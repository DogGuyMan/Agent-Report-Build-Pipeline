"""`prep.py` 의 수집 지문 — 계산 · 읽기 · 재수집 · 실패한 수집 뒤의 정리."""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from codewiki.python.runner.wiki import prep  # noqa: E402

PREP = os.path.join(ROOT, "src", "codewiki", "python", "runner", "wiki", "prep.py")
MACHINE = Path(ROOT, "src", "codewiki", "python", "machine")


def test_지문은_normalize_가_import_하는_이_저장소_모듈을_전부_담는다() -> None:
    tree = ast.parse((MACHINE / "normalize.py").read_text(encoding="utf-8"))
    local: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and (MACHINE / f"{n.module}.py").exists():
            local.add(n.module)
        elif isinstance(n, ast.Import):
            local |= {a.name for a in n.names if (MACHINE / f"{a.name}.py").exists()}
    want = {f"src/codewiki/python/machine/{m}.py" for m in local | {"normalize"}}
    assert want <= set(prep.COLLECT_CODE)


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
    sha = hashlib.sha256(cg.read_bytes()).hexdigest()
    fp.write_text(json.dumps({"fingerprint": "f1", "codegraph_sha256": sha}), encoding="utf-8")
    assert prep.recorded_fingerprint(str(fp), str(cg)) == "f1"
    cg.write_text('{"nodes": [1]}', encoding="utf-8")
    assert prep.recorded_fingerprint(str(fp), str(cg)) is None
    fp.write_text("{깨짐", encoding="utf-8")
    assert prep.recorded_fingerprint(str(fp), str(cg)) is None
    assert prep.recorded_fingerprint(str(tmp_path / "없음.json"), str(cg)) is None


def _run(repo: Path, *extra: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run([sys.executable, PREP, str(repo), *extra], capture_output=True, text=True, timeout=300)


def _cs_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "대상"
    (repo / "out" / "codegraph-raw").mkdir(parents=True)
    (repo / "App.csproj").write_text("<Project/>", encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "codegraph.json").write_text('{"nodes": [], "edges": []}', encoding="utf-8")
    (repo / "out" / "codegraph-raw" / "collect-fingerprint.json").write_text("{}", encoding="utf-8")
    return repo


def test_정제가_실패하면_옛_지도와_옛_지문이_남지_않는다(tmp_path: Path) -> None:
    repo = _cs_repo(tmp_path)
    raw = repo / "out" / "codegraph-raw"
    (raw / "roslyn-dump.json").write_text("{", encoding="utf-8")
    got = _run(repo, "--force")
    assert got.returncode != 0
    assert not (raw / "codegraph.json").exists()
    assert not (raw / "collect-fingerprint.json").exists()


def test_수집이_막혀도_옛_지도가_남지_않는다(tmp_path: Path) -> None:
    repo = _cs_repo(tmp_path)
    got = _run(repo, "--force")
    assert got.returncode == 1 and "막힘" in got.stderr
    assert not (repo / "out" / "codegraph-raw" / "codegraph.json").exists()


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

    again = _run(repo)
    assert "단계 facts -> render-modules" in again.stdout

    rec["fingerprint"] = "옛 수집기"
    (raw / "collect-fingerprint.json").write_text(json.dumps(rec), encoding="utf-8")
    third = _run(repo)
    assert "단계 griffe -> pycalls -> normalize" in third.stdout
