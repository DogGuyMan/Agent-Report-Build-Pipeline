"""test_manifest.py — 봉인(`manifest.py seal`)이 낸 꼴과 거부 조건의 시험."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402
import manifest as MF  # noqa: E402
import warmup  # noqa: E402


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def entry(path: str) -> warmup.Entry:
    return {"mtime": 0.0, "size": 0, "seen": 0.0, "file_hash": warmup.file_hash(path), "decl_hash": None}


def make_repo(tmp_path: Path) -> str:
    """조사가 끝난 직후의 대상 저장소 — 지문과 위키 상태가 지금 소스와 맞는다."""
    r = tmp_path / "대상"
    (r / "pkg").mkdir(parents=True)
    (r / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (r / "docs" / "wiki").mkdir(parents=True)
    (r / "docs" / "wiki" / "index.md").write_text("# 위키 pkg/a.py:1\n", encoding="utf-8")
    raw = r / "out" / "codegraph-raw"
    raw.mkdir(parents=True)
    (raw / "terms-db.json").write_text("{}", encoding="utf-8")
    (raw / "lang-select.json").write_text(json.dumps({"language": "py"}), encoding="utf-8")
    (r / ".gitignore").write_text("out/\n", encoding="utf-8")
    repo = str(r)
    warmup.save(str(raw / "snapshot.json"), {"pkg/a.py": entry(str(r / "pkg" / "a.py"))})
    with open(raw / "snapshot.json", "rb") as f:
        (raw / "wiki-state.json").write_text(
            json.dumps({"snapshot_sha256": hashlib.sha256(f.read()).hexdigest()}), encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def seal(repo: str, kinds: str = "terms-db,wiki") -> int:
    return MF.main(["seal", repo, "--kinds", kinds, "--producer-commit", "abc"])


def read_manifest(repo: str) -> MF.ArtifactManifest:
    with open(os.path.join(repo, "docs", "codegraph", "manifest.json"), "rb") as f:
        return msgspec.json.decode(f.read(), type=MF.ArtifactManifest)


def test_미추적_파일은_소스에_넣지_않는다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (tmp_path / "대상" / "pkg" / "b.py").write_text("y = 2\n", encoding="utf-8")
    assert seal(repo) == 0
    doc = read_manifest(repo)
    assert list(doc["inputs"]) == ["pkg/a.py"]                 # .md 는 확장자에 걸리지 않는다
    assert doc["source_exts"] == [".py"]
    assert doc["skip_dirs"] == sorted(declmap.SKIP_DIRS)


def test_blob_ids_는_git_hash_object_와_같다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    want = subprocess.run(["git", "-C", repo, "hash-object", "pkg/a.py"],
                          capture_output=True, text=True).stdout.strip()
    assert MF.blob_ids(repo, ["pkg/a.py"]) == {"pkg/a.py": want}


def test_seal_은_docs_codegraph_에_계약_꼴로_낸다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert seal(repo) == 0
    doc = read_manifest(repo)
    assert (doc["contract"], doc["version"]) == ("mode1-artifacts", 1)
    assert "superseded_by" not in doc                      # 성공 봉인은 실패 표식을 지운다
    assert [e["path"] for e in doc["artifacts"]["terms-db"]] == ["docs/codegraph/terms-db.json"]
    assert [e["path"] for e in doc["artifacts"]["wiki"]] == ["docs/wiki/index.md"]
    assert os.path.isfile(os.path.join(repo, "docs", "codegraph", "terms-db.json"))
    assert list(doc["inputs"]) == ["pkg/a.py"]


def test_seal_은_다시_읽지_않은_소스를_봉인하지_않는다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with open(os.path.join(repo, "pkg", "a.py"), "a", encoding="utf-8") as f:
        f.write("# 바꿈\n")
    assert seal(repo, "terms-db") == 3
    assert not os.path.exists(os.path.join(repo, "docs", "codegraph", "manifest.json"))


def test_seal_은_조사되지_않은_추적_파일도_거부한다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (tmp_path / "대상" / "pkg" / "b.py").write_text("y = 2\n", encoding="utf-8")
    git(repo, "add", "pkg/b.py")                           # 추적되어야 소스 집합에 든다
    assert seal(repo, "terms-db") == 3


def test_seal_은_작업_트리에서_지워진_추적_소스를_거부한다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    os.remove(os.path.join(repo, "pkg", "a.py"))           # 지웠고 아직 커밋하지 않았다
    assert seal(repo, "wiki") == 3                         # 지문 검사가 없는 종류도 막힌다
    assert not os.path.exists(os.path.join(repo, "docs", "codegraph", "manifest.json"))


def test_seal_은_지문을_따라잡지_못한_위키를_거부한다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = os.path.join(repo, "out", "codegraph-raw", "wiki-state.json")
    with open(state, "w", encoding="utf-8") as f:
        f.write(json.dumps({"snapshot_sha256": "옛것"}))
    assert seal(repo, "wiki") == 3
    assert seal(repo, "terms-db") == 0
    os.remove(os.path.join(repo, "out", "codegraph-raw", "snapshot.json"))    # 비교할 지문 자체가 없다
    assert seal(repo, "wiki") == 3


def test_seal_은_모르는_종류와_빈_종류를_거부한다(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert seal(repo, "foo") == 2
    assert seal(repo, "") == 2
