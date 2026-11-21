"""`prep.py` 의 수집 지문 — 계산 · 읽기 · 재수집 · 실패한 수집 뒤의 정리."""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from codewiki.python.runner.wiki import compdb, derive, prep  # noqa: E402

PREP = os.path.join(ROOT, "src", "codewiki", "python", "runner", "wiki", "prep.py")
MACHINE = Path(ROOT, "src", "codewiki", "python", "machine")


def _local_imports(path: Path) -> set[str]:
    """파일이 import 하는 이 저장소 모듈의 상대 경로."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for n in ast.walk(tree):
        names = ([n.module] if isinstance(n, ast.ImportFrom) and n.module else
                 [a.name for a in n.names] if isinstance(n, ast.Import) else [])
        for name in names:
            if name.startswith("codewiki.python."):
                out.add("src/" + name.replace(".", "/") + ".py")
            elif (MACHINE / f"{name}.py").exists():
                out.add(f"src/codewiki/python/machine/{name}.py")
    return {p for p in out if Path(ROOT, p).exists()}


def test_지문은_prep_와_normalize_가_import_하는_이_저장소_모듈을_전부_담는다() -> None:
    want = (_local_imports(MACHINE / "normalize.py") | _local_imports(Path(PREP)) | _local_imports(MACHINE / "source_inventory.py")
            | _local_imports(MACHINE / "collect_manifest.py"))
    want |= {"src/codewiki/python/machine/normalize.py", "src/codewiki/python/runner/wiki/prep.py"}
    assert want <= set(prep.COLLECT_CODE), sorted(want - set(prep.COLLECT_CODE))


def test_설정_입력이_바뀌면_지문이_바뀐다(tmp_path: Path) -> None:
    (tmp_path / ".clang-uml").write_text("add_compile_flags: [-std=c++20]\n", encoding="utf-8")
    a = prep.config_inputs(str(tmp_path), "clang-uml")
    (tmp_path / ".clang-uml").write_text("add_compile_flags: [-std=c++23]\n", encoding="utf-8")
    b = prep.config_inputs(str(tmp_path), "clang-uml")
    assert set(a) == {".clang-uml"} and a != b
    assert prep.config_inputs(str(tmp_path), "griffe+pycalls") == {}


def test_지문은_같은_입력이면_같고_수집기_판이_바뀌면_바뀐다() -> None:
    a = prep.collect_fingerprint(ROOT, {"griffe": "griffe 2.2.0"})
    assert a == prep.collect_fingerprint(ROOT, {"griffe": "griffe 2.2.0"})
    assert a != prep.collect_fingerprint(ROOT, {"griffe": "griffe 2.3.0"})


def test_지문은_커밋하지_않은_코드_수정도_잡는다(tmp_path: Path) -> None:
    for rel in prep.COLLECT_CODE:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(Path(ROOT, rel).read_bytes())
    before = prep.collect_fingerprint(str(tmp_path), {})
    p = tmp_path / prep.COLLECT_CODE[0]
    p.write_bytes(p.read_bytes() + b"\n# x\n")
    assert prep.collect_fingerprint(str(tmp_path), {}) != before


def test_수집기_판은_griffe_면_판을_roslyn_이면_산출물_해시를_쓴다(tmp_path: Path) -> None:
    assert prep.tool_versions("griffe+pycalls", sys.executable, str(tmp_path), None)["griffe"].startswith("griffe ")
    assert prep.tool_versions("roslyn-dump", sys.executable, str(tmp_path), None) == {"roslyn-dump.json": "?"}
    (tmp_path / "roslyn-dump.json").write_bytes(b"{}")
    got = prep.tool_versions("roslyn-dump", sys.executable, str(tmp_path), None)
    assert got == {"roslyn-dump.json": hashlib.sha256(b"{}").hexdigest()}
    assert prep.tool_versions("clang-uml", sys.executable, str(tmp_path), None)["clang-uml"]


def test_기록된_지문은_지도가_그때의_지도일_때만_읽힌다(tmp_path: Path) -> None:
    cg, fp = tmp_path / "codegraph.json", tmp_path / "collect-fingerprint.json"
    cg.write_text('{"nodes": []}', encoding="utf-8")
    fp.write_text(json.dumps(prep.build_manifest("f1", {}, str(cg), str(tmp_path), "griffe+pycalls")), encoding="utf-8")
    got = prep.read_manifest(str(fp), str(cg))
    assert got is not None and got["fingerprint"] == "f1"
    cg.write_text('{"nodes": [1]}', encoding="utf-8")
    assert prep.read_manifest(str(fp), str(cg)) is None
    fp.write_text("{깨짐", encoding="utf-8")
    assert prep.read_manifest(str(fp), str(cg)) is None
    assert prep.read_manifest(str(tmp_path / "없음.json"), str(cg)) is None


def _tracked(repo: Path, files: dict[str, str]) -> str:
    """`files` 를 써서 git 이 추적하게 하고 저장소 경로를 낸다."""
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    return str(repo)


def test_파이썬은_pyRoots_밖의_추적_파일을_제외로_적는다(tmp_path: Path) -> None:
    repo = _tracked(tmp_path, {"pkg/a.py": "x\n", "pkg/sub/b.py": "x\n", "test/t.py": "x\n", "setup.py": "x\n", "pkg/c.ts": "x\n"})
    assert prep.excluded_files(repo, "griffe+pycalls", [], []) == {"test/t.py": "prep.pyRoots skip", "setup.py": "prep.pyRoots skip"}
    assert prep.excluded_files(repo, "roslyn-dump", [], []) == {}


def test_C플러스플러스는_compile_commands_가_버렸거나_싣지_않은_파일을_제외로_적는다(tmp_path: Path) -> None:
    repo = _tracked(tmp_path, {"a.cpp": "x\n", "b.cpp": "x\n", "c.h": "x\n", "d.py": "x\n"})
    dropped: list[dict[str, Any]] = [{"file": repo + "/b.cpp", "reason": "external"},
                                     {"file": repo + "/a.cpp", "reason": "duplicate-config"}]
    got = prep.excluded_files(repo, "clang-uml", dropped, ["a.cpp"])
    assert got == {"b.cpp": "compdb: external", "c.h": "not-in-compdb"}   # a.cpp 는 첫 명령이 남았으니 수집된다


def test_compile_commands_합치기는_저장소_밖과_외부_파일을_사유와_함께_버린다() -> None:
    repo = "/work/repo"
    entries: list[dict[str, Any]] = [
        {"file": repo + "/a.cpp", "directory": repo}, {"file": "/elsewhere/x.cpp", "directory": "/elsewhere"},
        {"file": repo + "/_deps/y.cpp", "directory": repo}, {"file": "sub/z.cpp", "directory": repo + "/build/.."}, {"file": 3}]
    dropped: list[dict[str, Any]] = []
    kept = compdb.mergeEntries([entries], repo, dropped)
    assert [e["file"] for e in kept] == [repo + "/a.cpp", repo + "/sub/z.cpp"]
    assert [(e["file"], e["reason"]) for e in dropped] == [("/elsewhere/x.cpp", "outside-repo"), (repo + "/_deps/y.cpp", "external")]
    assert compdb.mergeEntries([entries], repo) == kept


def _run(repo: Path, *extra: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run([sys.executable, PREP, str(repo), *extra], capture_output=True, text=True, timeout=300)


def _cs_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "대상"
    (repo / "out" / "codegraph-raw").mkdir(parents=True)
    (repo / "App.csproj").write_text("<Project/>", encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "codegraph.json").write_text('{"nodes": [], "edges": []}', encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "collect-fingerprint.json").write_text("{}", encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "normalize-report.json").write_text("{}", encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "source-inventory.json").write_text("{}", encoding="utf-8")
    return repo


def test_정제가_실패하면_옛_지도와_옛_지문이_남지_않는다(tmp_path: Path) -> None:
    repo = _cs_repo(tmp_path)
    raw = repo / "out" / "codegraph-raw"
    (raw / "roslyn-dump.json").write_text("{", encoding="utf-8")
    got = _run(repo, "--force")
    assert got.returncode != 0
    assert not (raw / "codegraph.json").exists()
    assert not (raw / "collect-fingerprint.json").exists()
    assert not (raw / "normalize-report.json").exists()
    assert json.loads((raw / "source-inventory.json").read_text(encoding="utf-8"))["selected"] == "cs"   # 옛 것은 지워지고 수집 전에 쓴 새 것이 남는다
    failure = json.loads((raw / "collect-failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "failed" and failure["step"] == "normalize" and failure["returncode"] != 0
    assert failure["stderr_tail"]


def test_수집이_막혀도_옛_지도가_남지_않는다(tmp_path: Path) -> None:
    repo = _cs_repo(tmp_path)
    got = _run(repo, "--force")
    assert got.returncode == 1 and "막힘" in got.stderr
    failure = json.loads((repo / "out" / "codegraph-raw" / "collect-failure.json").read_text(encoding="utf-8"))
    assert failure["step"] == "plan" and failure["returncode"] == 1 and "roslyn-dump.json" in failure["stderr_tail"][0]
    assert not (repo / "out" / "codegraph-raw" / "codegraph.json").exists()
    assert not (repo / "out" / "codegraph-raw" / "normalize-report.json").exists()
    assert not (repo / "out" / "codegraph-raw" / "source-inventory.json").exists()


def test_수집에_성공하면_지문을_남기고_지문이_다르면_다시_수집한다(tmp_path: Path) -> None:
    repo = tmp_path / "대상"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "requirements.txt").write_text("", encoding="utf-8")
    (repo / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "pkg" / "a.py").write_text("def f():\n    return g()\n\n\ndef g():\n    return 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    raw = repo / "out" / "codegraph-raw"

    first = _run(repo)
    assert first.returncode == 0, first.stderr
    rec = json.loads((raw / "collect-fingerprint.json").read_text(encoding="utf-8"))
    assert rec["codegraph_sha256"] == hashlib.sha256((raw / "codegraph.json").read_bytes()).hexdigest()
    assert set(rec) >= {"sources", "generation_id"} and len(rec["generation_id"]) == 64
    ledger = json.loads((raw / "normalize-report.json").read_text(encoding="utf-8"))
    assert ledger["codegraph_sha256"] == rec["codegraph_sha256"] and ledger["language"] == "python"
    inv_path = raw / "source-inventory.json"
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    assert inventory["selected"] == "py" and inventory["languages"]["py"]["collected"] is True
    assert rec["inventory_sha256"] == hashlib.sha256(inv_path.read_bytes()).hexdigest()
    assert json.loads((raw / "ranking.json").read_text(encoding="utf-8"))["generation_id"] == rec["generation_id"]
    assert not (raw / "collect-failure.json").exists()

    kept = inv_path.read_bytes()
    again = _run(repo)
    assert "단계 facts -> render-modules" in again.stdout
    assert inv_path.read_bytes() == kept

    rec["fingerprint"] = "옛 수집기"
    (raw / "collect-fingerprint.json").write_text(json.dumps(rec), encoding="utf-8")
    third = _run(repo)
    assert "단계 griffe -> pycalls -> normalize" in third.stdout
    rec = json.loads((raw / "collect-fingerprint.json").read_text(encoding="utf-8"))
    assert rec["inventory_sha256"] == hashlib.sha256(inv_path.read_bytes()).hexdigest()
    assert json.loads((raw / "ranking.json").read_text(encoding="utf-8"))["generation_id"] == rec["generation_id"]


def test_collect_only_는_꼬리를_빼고_prep_은_넣는다() -> None:
    full = prep.prepPlan("griffe+pycalls", True, False, False, False, force=True)
    only = prep.prepPlan("griffe+pycalls", True, False, False, False, force=True, collectOnly=True)
    assert full["steps"] == ["griffe", "pycalls", "normalize", "facts", "render-modules"]
    assert only["steps"] == ["griffe", "pycalls", "normalize"]
    assert prep.prepPlan("clang-uml", False, True, False, True, collectOnly=True)["steps"] == ["clang-uml", "clang-doc", "normalize"]
    assert prep.prepPlan("roslyn-dump", False, False, True, False, collectOnly=True)["steps"] == ["normalize"]
    assert prep.prepPlan("griffe+pycalls", True, False, False, False)["steps"] == ["facts", "render-modules"]
    assert prep.prepPlan("griffe+pycalls", True, False, False, False, collectOnly=True)["steps"] == []   # 다시 수집할 것이 없으면 꼬리 없이 아무것도 하지 않는다


def test_소스_내용이_바뀌면_diff_없이도_다시_수집한다(tmp_path: Path) -> None:
    """직접 report-wiki prep 을 부르는 경로 — --diff 가 없어도 manifest 의 소스 해시가 재수집을 정한다."""
    repo = tmp_path / "r"
    (repo / "pkg").mkdir(parents=True)
    (repo / "requirements.txt").write_text("", encoding="utf-8")
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True, env=env)
    first = _run(repo)
    assert first.returncode == 0, first.stderr
    second = _run(repo)
    assert "normalize" not in second.stdout.split("단계")[1].splitlines()[0]
    (repo / "pkg" / "a.py").write_text("def f():\n    return 2\n", encoding="utf-8")   # 같은 줄 수, 다른 내용
    third = _run(repo)
    assert "normalize" in third.stdout.split("단계")[1].splitlines()[0]
    doc = json.loads((repo / "out/codegraph-raw/collect-fingerprint.json").read_text(encoding="utf-8"))
    assert doc["sources"]["pkg/a.py"] == hashlib.sha256((repo / "pkg" / "a.py").read_bytes()).hexdigest()
    assert doc["raw_provenance"] == "prep" and len(doc["generation_id"]) == 64


def test_파생_산출물_단계가_죽어도_수집_실패_기록을_쓰지_않는다(tmp_path: Path) -> None:
    paths = prep.wikiPaths(str(tmp_path))
    os.makedirs(paths["raw"])
    with pytest.raises(SystemExit) as stop:
        derive.derive_steps(str(tmp_path), paths, sys.executable, "g1")
    assert stop.value.code == 1
    assert not os.path.exists(paths["failure"])
