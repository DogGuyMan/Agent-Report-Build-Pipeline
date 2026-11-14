"""적대적 검토(2026-11-09)의 반례 12개 — 고쳐진 뒤의 동작을 못박는다. 아직 못 고친 것은 xfail(strict) 로 두고 그 Task 가 표식을 뗀다."""
import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("src", "src/codewiki/python/runner", "src/codewiki/python/machine"):
    s = str(ROOT / p)
    if s not in sys.path:
        sys.path.insert(0, s)

import normalize  # noqa: E402
import survey_plan  # noqa: E402
import terms_db  # noqa: E402
import verify_graph as V  # noqa: E402
from codewiki.python.runner.wiki import compdb, prep  # noqa: E402
from core import pipeline as P  # noqa: E402
from mode1 import context as X, edges as E, graph as G  # noqa: E402


def node(id: str, name: str = "pkg.f", module: str = "pkg", file: str = "a.py") -> dict[str, object]:
    return {"id": id, "name": name, "kind": "function", "module": module, "file": file, "line": 1}


def graph() -> dict[str, object]:
    return {"schema_version": 2, "language": "python", "platform": "linux", "source_tool": "probe",
            "repo_commit": None, "nodes": [node("C1")], "edges": [], "modules": [{"id": "pkg", "depends_on": []}]}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "out" / "codegraph-raw").mkdir(parents=True)
    (tmp_path / "a.py").write_text("def f(): return 1\n", encoding="utf-8")
    return tmp_path


def raw(repo: Path, name: str) -> Path:
    return repo / "out" / "codegraph-raw" / name


def ctx_for(repo: Path) -> X.Mode1Context:
    return X.Mode1Context(root=str(ROOT), model="never-called", repo=str(repo), cold=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_깨진_JSON_은_파이프라인에서도_결함_파일과_핸드오프를_남긴다(repo: Path) -> None:
    raw(repo, "codegraph.json").write_text("{", encoding="utf-8")
    ctx = ctx_for(repo)
    pipeline = E.build_mode1_graph(ctx, only=["verify-graph"], skip=None)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rows = P.Pipeline().run(pipeline, ctx)
    assert rows[0]["ok"] is False
    doc = json.loads(raw(repo, "graph-faults.json").read_text(encoding="utf-8"))
    assert doc["total"] == 1 and doc["faults"][0]["code"] == "unreadable"   # Task 2 와 Task 4 의 꼴 양쪽에서 참
    assert raw(repo, "graph-handoff.md").exists()


def test_줄_수_같은_소스_교체는_source_drift_다(repo: Path) -> None:
    cg = raw(repo, "codegraph.json")
    cg.write_text(json.dumps(graph()), encoding="utf-8")
    manifest = raw(repo, "collect-fingerprint.json")
    manifest.write_text(json.dumps(prep.build_manifest("fp", {}, str(cg), str(repo), "griffe+pycalls")), encoding="utf-8")
    assert V.verify(str(cg), str(repo), manifest=str(manifest))["status"] == "passed"
    (repo / "a.py").write_text("def completely_different(): return 2\n", encoding="utf-8")
    doc = V.verify(str(cg), str(repo), manifest=str(manifest))
    assert doc["status"] == "failed" and doc["freshness"]["counts"] == {"source-drift": 1}


def test_V3_를_건너뛴_기록은_전수조사에_맞지_않는다(repo: Path) -> None:
    cg = raw(repo, "codegraph.json")
    cg.write_text(json.dumps(graph()), encoding="utf-8")
    (repo / "a.py").unlink()
    doc = V.verify(str(cg), None)
    assert doc["status"] == "passed"                       # 구조만 봤다 — 통과는 맞다
    assert "V3" not in doc["checks_run"] and doc["fit"]["survey"] == "blocked"
    raw(repo, "graph-verified.json").write_text(json.dumps(doc), encoding="utf-8")
    assert G.VerifiedGraph.gate(ctx_for(repo), need_batches=False)[0] != ""


def test_annotate_only_는_성공_기록_없이_돌지_않는다(repo: Path) -> None:
    raw(repo, "batches.json").write_text(json.dumps(survey_plan.plan(graph(), 8)), encoding="utf-8")
    raw(repo, "codegraph.json").write_text("{", encoding="utf-8")
    ctx = ctx_for(repo)
    # annotate-symbols 가 graph-verified.json 을 읽는다고 선언하면 시뮬레이터의 산출물 사슬 검사가 시작 전에 막는다
    with pytest.raises(P.GraphError, match="graph-verified.json"):
        E.build_mode1_graph(ctx, only=["annotate-symbols"], skip=None)


@pytest.mark.xfail(strict=True, reason="stage 4 — Task-level plan to come")
def test_고유_id_둘_같은_이름_은_용어_둘이다() -> None:
    g = graph()
    g["nodes"] = [node("cs:pkg.f(int)"), node("cs:pkg.f(float)")]
    terms = terms_db.build_terms(g, {}, [])
    assert len([r for r in terms.values() if r["kind"] != "module"]) == 2


def test_모듈_의존_누락과_음수_occurrences_는_결함이다(repo: Path) -> None:
    g = graph()
    g["nodes"].append(node("C2", "pkg2.g", "pkg2"))
    g["edges"] = [{"from": "C1", "to": "C2", "kind": "dependency", "label": "call", "file": "a.py", "line": 1,
                   "occurrences": -5}]
    g["modules"].append({"id": "pkg2", "depends_on": []})
    cg = raw(repo, "codegraph.json")
    cg.write_text(json.dumps(g), encoding="utf-8")
    doc = V.verify(str(cg), str(repo))
    assert doc["integrity"]["counts"] == {"module-dep-mismatch": 1, "occurrences-range": 1}


def test_외부_노드만_있는_지도는_결함이다(repo: Path) -> None:
    g = graph()
    g["nodes"] = [{"id": "X:std", "name": "std", "kind": "external", "module": "__external__", "file": None, "line": None}]
    g["modules"] = []
    cg = raw(repo, "codegraph.json")
    cg.write_text(json.dumps(g), encoding="utf-8")
    assert V.verify(str(cg), str(repo))["integrity"]["counts"] == {"external-only": 1}


def test_compdb_변경은_지문을_바꾼다(tmp_path: Path) -> None:
    for rel in prep.COLLECT_CODE:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / rel).read_bytes())
    helper = tmp_path / "src/codewiki/python/runner/wiki/compdb.py"
    helper.write_text("before\n", encoding="utf-8")
    before = prep.collect_fingerprint(str(tmp_path), {})
    helper.write_text("changed behavior\n", encoding="utf-8")
    assert before != prep.collect_fingerprint(str(tmp_path), {})


def test_C샵_강제_수집은_원본_출처를_unknown_으로_적는다(repo: Path) -> None:
    cg = raw(repo, "codegraph.json")
    cg.write_text(json.dumps(graph()), encoding="utf-8")
    assert prep.prepPlan("roslyn-dump", True, False, True, False, force=True)["steps"][0] == "normalize"
    doc = prep.build_manifest("fp", {"roslyn-dump.json": "abc"}, str(cg), str(repo), "roslyn-dump")
    assert doc["raw_provenance"] == "unknown"
    assert prep.build_manifest("fp", {}, str(cg), str(repo), "griffe+pycalls")["raw_provenance"] == "prep"


def test_같은_파일의_두_컴파일_명령은_하나만_남고_장부에_남는다(tmp_path: Path) -> None:
    d = str(tmp_path)
    entries = [{"file": d + "/a.cpp", "directory": d, "command": "clang++ -DMODE=1 a.cpp"},
               {"file": "a.cpp", "directory": d, "command": "clang++ -DMODE=2 a.cpp"}]   # 두 번째는 상대경로다
    dropped: list[dict[str, object]] = []
    kept = compdb.mergeEntries([entries], d, dropped)
    assert len(kept) == 1 and kept[0]["command"].endswith("-DMODE=1 a.cpp")
    assert len(dropped) == 1 and dropped[0]["reason"] == "duplicate-config"


def test_자기_재귀_호출은_해소_실패가_아니다() -> None:
    nodes = {"C1": node("C1")}
    ids = {"pkg.f": "C1"}
    edges: dict[tuple[str, str, str], dict[str, object]] = {}
    stats = normalize.Ledger()
    normalize.merge_py_calls(nodes, ids, edges, {"symbols": [], "calls": [
        {"caller": "pkg.f", "callee": "pkg.f", "file": "a.py", "line": 1}]}, stats)
    assert edges == {} and stats["자기참조 버림"] == 1 and stats["호출 양끝 해소 실패"] == 0


@pytest.mark.xfail(strict=True, reason="stage 4 — Task-level plan to come")
def test_호출이_타입_간선에_접혀도_호출_위치가_남는다() -> None:
    nodes = {"C1": node("C1"), "C2": node("C2", "pkg.g")}
    ids = {"pkg.f": "C1", "pkg.g": "C2"}
    edges = {("C1", "C2", "dependency"): {"from": "C1", "to": "C2", "kind": "dependency",
                                           "label": "type annotation", "file": "a.py", "line": 1}}
    normalize.merge_py_calls(nodes, ids, edges, {"symbols": [], "calls": [
        {"caller": "pkg.f", "callee": "pkg.g", "file": "a.py", "line": 9}]}, normalize.Ledger())
    e = edges[("C1", "C2", "dependency")]
    assert e["occurrences"] == 2 and {"file": "a.py", "line": 9, "label": "호출"} in e["sites"]
