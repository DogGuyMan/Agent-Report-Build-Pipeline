#!/usr/bin/env python3
"""대상 저장소에 봉인된 Mode 1 산출물이 계약대로 있는지 판정하고, 봉인 뒤 소스가 움직였는지 알린다.

계약은 `contracts/mode1-artifacts.v1.json` 이고 형은 거기서 생성한 `contract_types.py` 다. **구조 문제**
(봉인 없음 · 계약 판 다름 · 종류 없음 · 해시 다름 · 꼴 아님)는 exit 1, **낡음**(봉인 뒤 소스가 바뀜 · 생김 ·
사라짐)은 경고만 하고 exit 0 이다. 무엇도 Mode 1 을 대신 돌리지 않는다 — 찍는 것은 사람이 칠 명령이다.

    python machine/evidence.py <repo> --need terms-db,wiki          # 구조 문제면 exit 1
    python machine/evidence.py <repo> --need wiki --list            # 통과하면 봉인된 경로와 낡음을 JSON 으로
    python machine/evidence.py <repo> --need terms-db,wiki --status # 한 줄 상태. 어느 경우든 exit 0
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contract_types import CONTRACT, VERSION, ArtifactManifest, TermsDb  # noqa: E402

KINDS = ("terms-db", "wiki")
MANIFEST = os.path.join("docs", "codegraph", "manifest.json")
TERMS_DB = os.path.join("docs", "codegraph", "terms-db.json")
FIX = ("사람이 Mode 1 을 돌린다 — cd $TOOLS_ROOT/codebase-wiki && .venv/bin/python runner/run_mode1.py <이 저장소>"
       " · 끝나면 docs/codegraph/ 를 커밋한다")


# ── 봉인 계산의 사본 — codebase-wiki 의 machine/manifest.py · declmap.tracked_files 와 같은 규칙 (결정 0011) ──
def git(repo: str, *args: str) -> str:
    """대상 저장소에서 git 을 부르고 stdout 을 낸다. 실패하면 CalledProcessError 다."""
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def sha256_of(path: str) -> str:
    """파일 바이트 그대로의 sha256."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def source_files(repo: str, exts: Sequence[str], skip: Sequence[str]) -> list[str]:
    """git 이 추적하는 파일 중 확장자가 맞고, 경로의 어느 성분(파일 이름 포함)도 `skip` 에 없는 것. 정렬해 낸다.

    git 이 실패하면(저장소가 아니거나 git 이 없으면) 빈 목록이다.
    """
    try:
        r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True)
    except OSError:
        return []
    if r.returncode != 0:
        return []
    out: list[str] = []
    for rel in r.stdout.split("\n"):
        if not rel or not rel.endswith(tuple(exts)):
            continue
        if any(part in skip for part in rel.split("/")):
            continue
        out.append(rel)
    return sorted(out)


def missing(repo: str, sources: Sequence[str]) -> list[str]:
    """git 이 추적하는데 작업 트리에 없는 소스. 지운 것을 아직 커밋하지 않은 상태다."""
    return [rel for rel in sources if not os.path.isfile(os.path.join(repo, rel))]


def blob_ids(repo: str, rels: Sequence[str]) -> dict[str, str]:
    """작업 트리 내용 그대로의 blob id. `git hash-object` 는 인자 순서대로 한 줄씩 낸다."""
    got: dict[str, str] = {}
    for i in range(0, len(rels), 500):
        chunk = list(rels[i:i + 500])
        got.update(zip(chunk, git(repo, "hash-object", "--", *chunk).split()))
    return got


# ── 판정 ──────────────────────────────────────────────────────────────────
def load_manifest(repo: str) -> tuple[ArtifactManifest | None, str]:
    """매니페스트와 빈 글, 또는 None 과 읽지 못한 이유."""
    path = os.path.join(repo, MANIFEST)
    if not os.path.isfile(path):
        return None, "manifest.json 이 없다 — 이 저장소에 봉인된 Mode 1 산출물이 없다: %s" % path
    try:
        with open(path, "rb") as f:
            return msgspec.json.decode(f.read(), type=ArtifactManifest), ""
    except msgspec.DecodeError as e:
        return None, "manifest.json 이 계약 꼴이 아니다 — %s" % e


def problems(repo: str, need: Sequence[str]) -> list[str]:
    """구조 문제. 비면 봉인을 근거로 쓸 수 있다."""
    m, why = load_manifest(repo)
    if m is None:
        return [why]
    if (m["contract"], m["version"]) != (CONTRACT, VERSION):
        return ["계약이 다르다 — %s v%d (이 저장소가 읽는 것: %s v%d)"
                % (m["contract"], m["version"], CONTRACT, VERSION)]
    out: list[str] = []
    for kind in need:
        entries = m["artifacts"].get(kind)
        if not entries:
            out.append("봉인에 %s 가 없다 — 그 실행에서 검사를 통과하지 못했다" % kind)
            continue
        for e in entries:
            p = os.path.join(repo, e["path"])
            if not os.path.isfile(p):
                out.append("봉인된 파일이 없다 — %s" % e["path"])
            elif sha256_of(p) != e["sha256"]:
                out.append("봉인 뒤 바뀌었다 — %s" % e["path"])
        if kind == "wiki":
            sealed_pages = {e["path"] for e in entries}
            for p in sorted(glob.glob(os.path.join(repo, "docs", "wiki", "*.md"))):
                rel = os.path.relpath(p, repo)
                if rel not in sealed_pages:
                    out.append("봉인 뒤 생긴 장 — %s" % rel)
    if "terms-db" in need and not out:
        try:
            with open(os.path.join(repo, TERMS_DB), "rb") as f:
                msgspec.json.decode(f.read(), type=TermsDb)
        except msgspec.DecodeError as e:
            out.append("terms-db.json 이 계약 꼴이 아니다 — %s" % e)
    return out


def staleness(repo: str) -> list[str]:
    """봉인 뒤 소스의 움직임. 매니페스트에 적힌 규칙으로 다시 모은다 — Mode 1 을 몰라도 된다.

    추적되는데 작업 트리에 없는 파일은 blob id 를 낼 수 없어 지금 목록에서 빠지고, 봉인에 있었으면 사라짐이다.
    `git hash-object` 가 실패하면 파일마다 다시 내고, 끝내 못 낸 파일은 읽기실패다. 어느 경우든 예외를 내지 않는다.
    """
    m, _ = load_manifest(repo)
    if m is None:
        return []
    files = source_files(repo, m["source_exts"], m["skip_dirs"])
    gone = set(missing(repo, files))
    present = [rel for rel in files if rel not in gone]
    unread: list[str] = []
    now: dict[str, str]
    try:
        now = blob_ids(repo, present)
    except (subprocess.CalledProcessError, OSError):
        now = {}
        for rel in present:
            try:
                now.update(blob_ids(repo, [rel]))
            except (subprocess.CalledProcessError, OSError):
                unread.append(rel)
    before = m["inputs"]
    return (["바뀜 %s" % p for p in sorted(before.keys() & now.keys()) if before[p] != now[p]]
            + ["생김 %s" % p for p in sorted(now.keys() - before.keys())]
            + ["사라짐 %s" % p for p in sorted(before.keys() - now.keys() - set(unread))]
            + ["읽기실패 %s" % p for p in unread])


def uncommitted(repo: str) -> list[str]:
    """봉인 파일 중 작업 트리에서 바뀌었거나 추적되지 않은 것. 비면 커밋된 봉인이다.

    git 이 실패하면(저장소 밖이거나 git 이 없으면) 커밋될 수 없으므로 봉인 파일 둘을 다 낸다.
    """
    try:
        out = git(repo, "status", "--porcelain", "--", MANIFEST, TERMS_DB)
    except (subprocess.CalledProcessError, OSError):
        return sorted([MANIFEST, TERMS_DB])
    return sorted(line[3:] for line in out.splitlines() if line.strip())


def warnings(repo: str, m: ArtifactManifest) -> list[str]:
    """낡음 — 멈추지 않는 것들. 소스 움직임 · 미커밋 · 뒤 실행 실패."""
    out = ["소스 " + s for s in staleness(repo)]
    if uncommitted(repo):
        out.append("봉인 파일이 커밋되지 않았다 — 이 기계에만 보인다. 다른 기계와 클라우드는 옛 봉인을 본다")
    sup = m.get("superseded_by")
    if sup:
        out.append("뒤 Mode 1 실행이 %s 에서 실패했다(%s) — 이 봉인은 그 전 것이다" % (sup["stage"], sup["at"]))
    return out


def status_line(repo: str, need: Sequence[str]) -> str:
    """`--status` 의 한 줄. 어느 경우든 예외 없이 글 하나를 돌려준다.

    없음 · 깨짐(첫 문제) · 있음(낡음 · 미커밋 · 뒤 실행 실패를 덧붙인다) · 판정 못 함(파일을 읽지 못했다) 넷 중 하나다.
    """
    try:
        m, why = load_manifest(repo)
        if m is None:
            return "Mode 1 봉인 — " + ("깨짐: " + why if os.path.isfile(os.path.join(repo, MANIFEST)) else "없음")
        got = problems(repo, need)
        if got:
            return "Mode 1 봉인 — 깨짐: " + got[0]
        parts = ["있음"]
        stale = staleness(repo)
        if stale:
            parts.append("낡음 %d건" % len(stale))
        if uncommitted(repo):
            parts.append("미커밋")
        if m.get("superseded_by"):
            parts.append("뒤 실행 실패")
        return "Mode 1 봉인 — " + " · ".join(parts)
    except (OSError, subprocess.CalledProcessError) as e:
        return "Mode 1 봉인 — 판정 못 함: %s" % e


def main(argv: Sequence[str] | None = None) -> int:
    """구조 문제면 1 과 사람이 칠 명령, 아니면 낡음을 경고로 찍고 0. `--status` 는 늘 0 이다."""
    ap = argparse.ArgumentParser(description="봉인된 Mode 1 산출물 판정")
    ap.add_argument("repo")
    ap.add_argument("--need", required=True, help="쉼표로 — terms-db, wiki")
    ap.add_argument("--list", action="store_true", help="통과하면 봉인된 경로와 낡음을 JSON 으로 낸다")
    ap.add_argument("--status", action="store_true", help="한 줄 상태만. 늘 exit 0")
    a = ap.parse_args(argv)
    repo = os.path.abspath(str(a.repo))
    need = [k for k in str(a.need).split(",") if k]
    if not need or any(k not in KINDS for k in need):
        print("에러 — 모르는 종류 %r (있는 것: %s)" % (a.need, ", ".join(KINDS)), file=sys.stderr)
        return 2
    if a.status:
        print(status_line(repo, need))
        return 0
    got = problems(repo, need)
    if got:
        for line in got:
            print(line, file=sys.stderr)
        print(FIX, file=sys.stderr)
        return 1
    m, _ = load_manifest(repo)
    assert m is not None
    warn = warnings(repo, m)
    if warn:
        print("경고 — %d건. 있는 자료로 진행한다" % len(warn), file=sys.stderr)
        for line in warn[:20]:
            print("  " + line, file=sys.stderr)
    if a.list:
        stale = staleness(repo)
        print(json.dumps({"manifest": os.path.join(repo, MANIFEST),
                          "artifacts": [os.path.join(repo, e["path"]) for k in need for e in m["artifacts"][k]],
                          "stale": stale,
                          "stale_files": sorted(s.split(" ", 1)[1] for s in stale),
                          "uncommitted": bool(uncommitted(repo)),
                          "superseded_by": m.get("superseded_by")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
