#!/usr/bin/env python3
"""Mode 1 산출물을 봉인한다 — `docs/codegraph/` 에 terms-db.json 사본과 manifest.json 을 낸다.

봉인은 그 실행에서 **검사기를 통과한** 산출물만 싣고, 그것이 **지금 소스를 다시 읽은 결과**일 때만 싣는다.
- terms-db : 소스 파일마다의 지문이 지난 전수조사의 지문(`out/codegraph-raw/snapshot.json`)과 같아야 한다
- wiki     : `write-wiki` 가 그 지문을 따라잡았다는 표(`out/codegraph-raw/wiki-state.json`)가 있어야 한다
소스 집합은 `declmap.tracked_files` 가 낸다 — git 이 아는 파일 중 언어의 확장자에 맞고 `declmap.SKIP_DIRS` 밖에 있는 것.
읽는 쪽(report-builder 의 `machine/evidence.py`)은 매니페스트 하나로 꼴과 신선도를 판정한다. 소스를 모으는
규칙(확장자 · 건너뛸 폴더)도 같이 적어, 읽는 쪽이 Mode 1 을 몰라도 같은 규칙을 다시 돌리게 한다.

    python machine/manifest.py seal <repo> --kinds terms-db,wiki --producer-commit <sha>
    exit 0 봉인 · 1 언어 모름 · 2 종류 틀림 · 3 다시 읽지 않은 것이 있다
"""
import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import NotRequired, TypedDict

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402
import warmup  # noqa: E402

CONTRACT = "mode1-artifacts"
VERSION = 1
KINDS = ("terms-db", "wiki")
PUBLISH = os.path.join("docs", "codegraph")


class ArtifactEntry(TypedDict):
    """봉인된 산출물 파일 하나. `path` 는 대상 저장소 뿌리 기준."""
    path: str
    sha256: str


class SupersededBy(TypedDict):
    """이 봉인 뒤의 Mode 1 실행이 실패했다는 표식. 봉인 자체는 그대로다 — 읽는 쪽이 경고로 본다."""
    stage: str
    at: str
    producer_commit: str


class ArtifactManifest(TypedDict):
    """`docs/codegraph/manifest.json` 의 꼴. `inputs` 는 봉인 시점 소스 파일마다의 git blob id 다."""
    contract: str
    version: int
    producer_commit: str
    source_commit: str
    source_exts: list[str]
    skip_dirs: list[str]
    artifacts: dict[str, list[ArtifactEntry]]
    inputs: dict[str, str]
    superseded_by: NotRequired[SupersededBy]


class LangPick(TypedDict):
    """`lang-select.json` 에서 봉인이 읽는 칸. 언어를 못 골랐으면 None 이다."""
    language: str | None


class WikiState(TypedDict):
    """`write-wiki` 가 따라잡은 지문(`snapshot.json` 바이트의 sha256)과 그때 쓴 장마다의 해시."""
    snapshot_sha256: str
    pages: NotRequired[dict[str, str]]


def git(repo: str, *args: str) -> str:
    """대상 저장소에서 git 을 부르고 stdout 을 낸다. 실패하면 CalledProcessError 다."""
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def sha256_of(path: str) -> str:
    """파일 바이트 그대로의 sha256."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def blob_ids(repo: str, rels: Sequence[str]) -> dict[str, str]:
    """작업 트리 내용 그대로의 blob id. `git hash-object` 는 인자 순서대로 한 줄씩 낸다."""
    got: dict[str, str] = {}
    for i in range(0, len(rels), 500):
        chunk = list(rels[i:i + 500])
        got.update(zip(chunk, git(repo, "hash-object", "--", *chunk).split()))
    return got


def missing(repo: str, sources: Sequence[str]) -> list[str]:
    """git 이 추적하는데 작업 트리에 없는 소스. 지운 것을 아직 커밋하지 않은 상태다."""
    return [rel for rel in sources if not os.path.isfile(os.path.join(repo, rel))]


def unsurveyed(repo: str, sources: Sequence[str], snapshot: str) -> list[str]:
    """지난 전수조사의 지문과 다른 소스. 지문에 없는 새 파일도 넣는다."""
    snap = warmup.load(snapshot)
    out: list[str] = []
    for rel in sources:
        e = snap.get(rel)
        if e is None or e.get("file_hash") != warmup.file_hash(os.path.join(repo, rel)):
            out.append(rel)
    return out


def wiki_caught_up(raw: str) -> bool:
    """`wiki-state.json` 이 지금 `snapshot.json` 의 지문을 가리키는가. 둘 중 하나라도 읽지 못하면 아니다."""
    try:
        with open(os.path.join(raw, "wiki-state.json"), "rb") as f:
            state = msgspec.json.decode(f.read(), type=WikiState)
        return state["snapshot_sha256"] == sha256_of(os.path.join(raw, "snapshot.json"))
    except (OSError, msgspec.DecodeError):
        return False


def entries(repo: str, kind: str) -> list[ArtifactEntry]:
    """봉인한 종류의 파일 목록과 sha256. terms-db 는 `docs/codegraph/` 의 사본, wiki 는 `docs/wiki/*.md` 다."""
    if kind == "terms-db":
        rels = [os.path.join(PUBLISH, "terms-db.json")]
    else:
        rels = sorted(os.path.relpath(p, repo) for p in glob.glob(os.path.join(repo, "docs", "wiki", "*.md")))
    return [{"path": r, "sha256": sha256_of(os.path.join(repo, r))} for r in rels]


def refuse(head: str, rels: Sequence[str]) -> int:
    """봉인을 거부한 이유를 stderr 에 적고 종료 코드 3 을 낸다. 파일은 스무 개까지 보인다."""
    print("봉인하지 않는다 — " + head, file=sys.stderr)
    for rel in rels[:20]:
        print("  " + rel, file=sys.stderr)
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    """`seal` 명령. 거부 조건을 모두 지나야 `docs/codegraph/` 에 쓴다."""
    ap = argparse.ArgumentParser(description="Mode 1 산출물 봉인")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("repo")
    s.add_argument("--kinds", required=True, help="쉼표로. 이번 실행에서 검사를 통과한 것 — terms-db, wiki")
    s.add_argument("--producer-commit", required=True)
    a = ap.parse_args(argv)
    repo = os.path.abspath(str(a.repo))
    kinds = [k for k in str(a.kinds).split(",") if k]
    if not kinds or any(k not in KINDS for k in kinds):
        print("에러 — 봉인할 종류가 틀렸다: %r (있는 것: %s)" % (a.kinds, ", ".join(KINDS)), file=sys.stderr)
        return 2
    raw = os.path.join(repo, "out", "codegraph-raw")
    with open(os.path.join(raw, "lang-select.json"), "rb") as f:
        language = msgspec.json.decode(f.read(), type=LangPick)["language"]
    if language not in declmap.LANGS:
        print("에러 — 언어를 모른다: %r. lang-decide 가 먼저 돌아야 한다" % language, file=sys.stderr)
        return 1
    exts = list(declmap.LANGS[language]["exts"])
    skip = sorted(declmap.SKIP_DIRS)
    sources = declmap.tracked_files(repo, language, [])
    gone = missing(repo, sources)
    if gone:
        return refuse("추적되는데 작업 트리에 없는 소스 %d개:" % len(gone), gone)
    if "terms-db" in kinds:
        stale = unsurveyed(repo, sources, os.path.join(raw, "snapshot.json"))
        if stale:
            return refuse("지난 전수조사 뒤 바뀐 소스 %d개. Mode 1 을 증분으로 다시 돌린다:" % len(stale), stale)
    if "wiki" in kinds and not wiki_caught_up(raw):
        return refuse("write-wiki 가 지난 전수조사를 따라잡지 못했다", [])
    os.makedirs(os.path.join(repo, PUBLISH), exist_ok=True)
    if "terms-db" in kinds:
        shutil.copyfile(os.path.join(raw, "terms-db.json"), os.path.join(repo, PUBLISH, "terms-db.json"))
    doc: ArtifactManifest = {
        "contract": CONTRACT, "version": VERSION, "producer_commit": str(a.producer_commit),
        "source_commit": git(repo, "rev-parse", "HEAD").strip(),
        "source_exts": exts, "skip_dirs": skip,
        "artifacts": {k: entries(repo, k) for k in kinds},
        "inputs": blob_ids(repo, sources)}
    path = os.path.join(repo, PUBLISH, "manifest.json")
    with open(path, "wb") as f:
        f.write(msgspec.json.format(msgspec.json.encode(doc), indent=2))
    print("%s — 봉인 %s · 소스 %d개 (커밋은 사람이 한다)" % (path, ", ".join(kinds), len(sources)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
