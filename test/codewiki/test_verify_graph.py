"""`verify_graph.py` 의 층 — 읽기 · 꼴 · 정합 · 근거 · 장부 · 범위 · 수집 — 과 결과 파일."""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import cast

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "machine")]
import collect_manifest as CM  # noqa: E402
import verify_graph as V  # noqa: E402

Obj = dict[str, object]
EXT: Obj = {"id": "X:std", "name": "(표준) stdlib", "kind": "external", "module": "__external__",
            "file": None, "line": None}


def _node(nid: str, kind: str = "function", module: str | None = "pkg",
          file: str | None = "a.py", line: int | None = 1) -> Obj:
    return {"id": nid, "name": "pkg.a." + nid, "kind": kind, "module": module, "file": file, "line": line}


def _edge(src: str, dst: str, **extra: object) -> Obj:
    return {"from": src, "to": dst, "kind": "dependency", "label": None, "file": "a.py", "line": 2, **extra}


def _graph(nodes: list[Obj] | None = None, edges: list[Obj] | None = None,
           modules: list[Obj] | None = None, **top: object) -> Obj:
    g: Obj = {"schema_version": 2, "language": "python", "platform": "linux",
              "source_tool": "griffe 2.2.0", "repo_commit": None,
              "nodes": nodes if nodes is not None else [_node("C1"), _node("C2", line=3), EXT],
              "edges": edges if edges is not None else [_edge("C1", "C2"),
                                                        _edge("C2", "X:std", line=3, constraint=False)],
              "modules": modules if modules is not None else [{"id": "pkg", "depends_on": []}]}
    g.update(top)
    return g


def _codes(faults: list[V.Fault]) -> list[str]:
    return [f["code"] for f in faults]


def _check(g: Obj) -> list[V.Fault]:
    """V1 · V2 를 한 번에 — 근거 층 없이."""
    el, faults = V.check_elements(g)
    return V.check_top(g) + faults + V.check_consistency(el)


def test_온전한_지도는_결함이_없다() -> None:
    assert _check(_graph()) == []


def test_표는_일곱_층_서른네_코드고_층마다_절이_있다() -> None:
    assert len(V.LAYER) == 34
    assert sorted(set(V.LAYER.values())) == ["V0 읽기", "V1 꼴", "V2 정합", "V3 근거", "V4 장부", "범위", "수집"]
    assert set(V.LAYER.values()) <= set(V.SECTION_OF_LAYER)
    assert V.REPORT_ONLY == {"language-not-collected", "coverage-gap"} and V.REPORT_ONLY <= set(V.LAYER)
    with pytest.raises(KeyError):
        V.fault("없는-코드", "$", "")


def test_V0_없는_파일과_깨진_JSON_을_결함으로_낸다(tmp_path: Path) -> None:
    doc, _, faults = V.read_graph(str(tmp_path / "없음.json"))
    assert doc is None and _codes(faults) == ["unreadable"]
    p = tmp_path / "codegraph.json"
    p.write_text('{"nodes": [', encoding="utf-8")
    doc, sha, faults = V.read_graph(str(p))
    assert doc is None and _codes(faults) == ["unreadable"] and "1줄" in faults[0]["detail"]
    assert sha == hashlib.sha256(p.read_bytes()).hexdigest()


def test_V1_최상위의_열쇠_판_언어_빈_지도() -> None:
    g = _graph(nodes=[], schema_version=1, language="rust")
    del g["source_tool"]
    assert sorted(_codes(V.check_top(g))) == ["empty-graph", "language", "schema-version", "top-field"]
    assert _codes(V.check_top([])) == ["top-field"]


def test_V1_원소의_꼴은_첫_오류에서_멈추지_않고_전부_모은다() -> None:
    g = _graph(nodes=[_node("C1"), _node("C2", line=3), EXT, {"name": "id 없음"}, _node("C9", kind="macro")],
               edges=[_edge("C1", "C2"), _edge("C2", "X:std", line=3, constraint=False),
                      _edge("C1", "C2", kind="calls")],
               modules=[{"id": "pkg", "depends_on": []}, {"id": "m"}])
    _, faults = V.check_elements(g)
    assert _codes(faults) == ["node-shape", "node-kind", "edge-shape", "module-shape"]
    assert [f["at"] for f in faults] == ["$.nodes[3]", "$.nodes[4].kind", "$.edges[2]", "$.modules[1]"]


def test_V2_열_규칙이_저마다_결함을_낸다() -> None:
    g = _graph(nodes=[_node("C1"), _node("C1"), EXT,
                      _node("X:bad", kind="external", module="pkg", file=None, line=None),
                      _node("C3", file=None)],
               edges=[_edge("C1", "C9"), _edge("X:std", "C1"), _edge("C1", "X:std"),
                      _edge("C1", "C3"), _edge("C1", "C3")],
               modules=[{"id": "pkg", "depends_on": ["pkg", "zzz"]}, {"id": "ghost", "depends_on": []}])
    assert sorted(set(_codes(_check(g)))) == sorted([
        "duplicate-node", "external-node", "first-party-location", "dangling-edge", "external-source",
        "external-constraint", "duplicate-edge", "module-list", "module-dep", "module-dep-mismatch"])


def test_V2_는_꼴이_틀린_노드_때문에_끊김을_만들지_않는다() -> None:
    with_id = _graph(nodes=[_node("C1"), {"id": "C2", "name": 1}, EXT])
    assert _codes(_check(with_id)) == ["node-shape"]
    without_id = _graph(nodes=[_node("C1"), {"name": 1}, EXT],
                        edges=[_edge("C1", "C7"), _edge("C1", "X:std", constraint=False)])
    assert _codes(_check(without_id)) == ["node-shape"]


def test_V3_저장소_밖_없는_파일_줄_넘침(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")
    g = _graph(nodes=[_node("C1"), _node("C2", line=9), _node("C3", file="없음.py"),
                      _node("C4", file="../밖.py"), _node("C5", file="/etc/passwd")],
               edges=[_edge("C1", "C2", line=0)], modules=[{"id": "pkg", "depends_on": []}])
    el, _ = V.check_elements(g)
    faults, shas = V.check_sources(el, str(tmp_path))
    assert _codes(faults) == [
        "line-out-of-range", "file-missing", "file-outside-repo", "file-outside-repo", "line-out-of-range"]
    assert shas == {"a.py": hashlib.sha256((tmp_path / "a.py").read_bytes()).hexdigest()}   # 연 파일만 든다


def test_결과_파일은_한쪽만_남고_통과는_같은_바이트다(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def f():\n    return g()\ndef g():\n    return 1\n", encoding="utf-8")
    cg, faults, passed = tmp_path / "codegraph.json", tmp_path / "graph-faults.json", tmp_path / "graph-verified.json"
    cg.write_text(json.dumps(_graph()), encoding="utf-8")
    manifest = tmp_path / "collect-fingerprint.json"
    manifest.write_text(json.dumps(CM.build_manifest("fp", {}, str(cg), str(tmp_path), "griffe+pycalls")), encoding="utf-8")
    argv = [str(cg), "--repo", str(tmp_path), "--manifest", str(manifest), "--faults", str(faults), "--passed", str(passed)]
    assert V.main(argv) == 0
    first = passed.read_bytes()
    assert json.loads(first)["status"] == "passed" and json.loads(first)["integrity"]["faults"] == 0
    assert V.main(argv) == 0 and passed.read_bytes() == first and not faults.exists()
    assert json.loads(first)["codegraph_sha256"] == hashlib.sha256(cg.read_bytes()).hexdigest()
    cg.write_text("{", encoding="utf-8")
    assert V.main(argv) == 1 and not passed.exists()
    assert json.loads(faults.read_text(encoding="utf-8"))["integrity"]["counts"] == {"unreadable": 1}


def test_결과_문서는_네_절과_수행_검사와_적합을_갖는다(tmp_path: Path) -> None:
    p = tmp_path / "g.json"
    p.write_text(json.dumps(_graph()), encoding="utf-8")
    doc = V.verify(str(p), None)
    assert doc["checks_run"] == ["V0", "V1", "V2"] and doc["fit"]["survey"] == "blocked"
    assert set(doc) >= {"integrity", "freshness", "coverage", "capabilities", "fit", "generation_id"}
    assert doc["capabilities"] == {"methods": True, "calls": True, "resolution": "heuristic"}


def _mapped(tmp_path: Path) -> Path:
    """`a.py` 와 그것을 인용하는 지도를 쓰고 지도의 자리를 낸다."""
    (tmp_path / "a.py").write_text("def f():\n    return g()\ndef g():\n    return 1\n", encoding="utf-8")
    cg = tmp_path / "codegraph.json"
    cg.write_text(json.dumps(_graph()), encoding="utf-8")
    return cg


def _manifest(tmp_path: Path, cg: Path, inventory: Path | None = None) -> Path:
    """지금 지도와 소스로 수집 manifest 를 쓰고 그 자리를 낸다. `inventory` 가 있으면 그 해시를 적는다."""
    m = tmp_path / "collect-fingerprint.json"
    sha = (CM.file_sha256(str(inventory)) or "") if inventory is not None else ""
    m.write_text(json.dumps(CM.build_manifest("fp", {}, str(cg), str(tmp_path), "griffe+pycalls", inventory_sha256=sha)),
                 encoding="utf-8")
    return m


def test_manifest_없음은_freshness_unknown_이고_적합하지_않다(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    for manifest in (None, str(tmp_path / "없음.json")):
        doc = V.verify(str(cg), str(tmp_path), manifest=manifest)
        assert doc["status"] == "failed" and doc["freshness"]["counts"] == {"freshness-unknown": 1}
        assert doc["freshness"]["manifest"] == "missing" and doc["generation_id"] is None
        assert "manifest" not in doc["checks_run"]
        assert doc["fit"]["survey"] == "blocked" and "freshness-unknown" in doc["fit"]["blocked_by"]


def test_옛_꼴의_manifest_는_읽을_수_없어_freshness_unknown(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    old = tmp_path / "collect-fingerprint.json"
    old.write_text(json.dumps({"fingerprint": "f", "codegraph_sha256": hashlib.sha256(cg.read_bytes()).hexdigest()}),
                   encoding="utf-8")
    doc = V.verify(str(cg), str(tmp_path), manifest=str(old))
    assert doc["freshness"]["counts"] == {"freshness-unknown": 1} and doc["freshness"]["manifest"] == "missing"


def test_다른_지도의_manifest_는_generation_mismatch(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    m = _manifest(tmp_path, cg)
    cg.write_text(json.dumps(_graph(), indent=1), encoding="utf-8")   # 내용은 같고 바이트가 다르다
    doc = V.verify(str(cg), str(tmp_path), manifest=str(m))
    assert doc["status"] == "failed" and doc["freshness"]["counts"] == {"generation-mismatch": 1}
    assert doc["freshness"]["manifest"] == "mismatch" and doc["generation_id"] is None


def test_같은_줄_수의_다른_내용은_source_drift(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    m = _manifest(tmp_path, cg)
    want = json.loads(m.read_text(encoding="utf-8"))["generation_id"]
    ok = V.verify(str(cg), str(tmp_path), manifest=str(m))
    assert ok["status"] == "passed" and ok["generation_id"] == want and ok["freshness"]["manifest"] == "ok"
    assert ok["checks_run"] == ["V0", "V1", "V2", "V3", "manifest"] and ok["fit"]["survey"] == "ready"
    (tmp_path / "a.py").write_text("def f():\n    return 2\ndef g():\n    return 3\n", encoding="utf-8")
    doc = V.verify(str(cg), str(tmp_path), manifest=str(m))
    assert doc["status"] == "failed" and doc["freshness"]["counts"] == {"source-drift": 1}
    assert doc["generation_id"] == want


REAL = os.path.join(ROOT, "out", "codegraph-raw", "codegraph.json")


@pytest.mark.skipif(not os.path.exists(REAL), reason="out/codegraph-raw/codegraph.json 이 없다")
def test_이_저장소_지도는_V0_부터_V2_까지_지난다() -> None:
    got = V.verify(REAL, None)
    assert got["status"] == "passed", got


PY_ROW: Obj = {"files": 1, "collector": "griffe+pycalls", "collected": True}
TS_ROW: Obj = {"files": 2, "collector": "none", "collected": False}
COLLECTED: Obj = {"language": "py", "status": "collected"}


def _ledger(tmp_path: Path, cg: Path, reasons: list[Obj] | None = None, over: Obj | None = None) -> Path:
    """지도의 바이트에 묶인 버림 장부를 쓰고 그 자리를 낸다. `over` 는 열쇠를 덮는다."""
    doc: Obj = {"codegraph_sha256": hashlib.sha256(cg.read_bytes()).hexdigest(), "language": "python",
                "source_tool": "griffe 2.2.0", "reasons": reasons or [], **(over or {})}
    p = tmp_path / "normalize-report.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _inventory(tmp_path: Path, languages: dict[str, Obj] | None = None, files: dict[str, Obj] | None = None) -> Path:
    """소스 inventory 를 쓰고 그 자리를 낸다. 기본은 파이썬만 있고 `a.py` 하나가 수집된 꼴이다."""
    doc: Obj = {"selected": "py", "languages": languages or {"py": PY_ROW}, "files": files or {"a.py": COLLECTED}}
    p = tmp_path / "source-inventory.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _covered(tmp_path: Path, reasons: list[Obj] | None = None, languages: dict[str, Obj] | None = None,
             files: dict[str, Obj] | None = None, failure: Path | None = None) -> V.VerifyDoc:
    """지도 · 장부 · inventory · manifest 를 한 벌로 쓰고 범위 절까지 검사한 결과를 낸다."""
    cg = _mapped(tmp_path)
    ledger = _ledger(tmp_path, cg, reasons)
    inv = _inventory(tmp_path, languages, files)
    manifest = _manifest(tmp_path, cg, inv)
    return V.verify(str(cg), str(tmp_path), manifest=str(manifest), report=str(ledger), inventory=str(inv),
                    failure=str(failure) if failure is not None else None)


def test_장부와_inventory_가_맞으면_범위_절이_채워지고_통과한다(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    ledger = _ledger(tmp_path, cg, [{"reason": "자기참조 버림", "class": "policy", "count": 2, "samples": []}])
    inv = _inventory(tmp_path)
    manifest = _manifest(tmp_path, cg, inv)
    faults, passed = tmp_path / "graph-faults.json", tmp_path / "graph-verified.json"
    argv = [str(cg), "--repo", str(tmp_path), "--manifest", str(manifest), "--report", str(ledger), "--inventory", str(inv),
            "--failure", str(tmp_path / "collect-failure.json"), "--faults", str(faults), "--passed", str(passed)]
    assert V.main(argv) == 0
    doc = json.loads(passed.read_text(encoding="utf-8"))
    assert doc["checks_run"] == ["V0", "V1", "V2", "V3", "manifest", "V4", "coverage"] and doc["fit"]["survey"] == "ready"
    assert doc["coverage"] == {"faults": 0, "counts": {}, "inventory": "ok", "files_total": 1, "collected": 1, "excluded": 0,
                               "unsupported": 0, "failed": 0, "no_symbols": 0, "languages_not_collected": []}


@pytest.mark.parametrize("row, code", [
    ({"reason": "모르는 관계 종류", "class": "fault", "count": 3, "samples": ["x"]}, "unknown-kind"),
    ({"reason": "끝점 해소 실패", "class": "unresolved", "count": 48, "samples": ["a -> b"]}, "unresolved-drop"),
])
def test_장부의_결함과_미해결_사유는_통과를_막는다(tmp_path: Path, row: Obj, code: str) -> None:
    doc = _covered(tmp_path, [row])
    assert doc["status"] == "failed" and doc["coverage"]["counts"] == {code: 1}
    assert doc["fit"]["survey"] == "blocked" and code in doc["fit"]["blocked_by"]
    assert doc["faults"][0]["at"] == "$.reasons[%r]" % row["reason"] and "%d건" % cast(int, row["count"]) in doc["faults"][0]["detail"]


def test_장부가_없거나_다른_지도의_것이면_report_stale(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    inv = _inventory(tmp_path)
    manifest = _manifest(tmp_path, cg, inv)

    def run(ledger: Path) -> V.VerifyDoc:
        return V.verify(str(cg), str(tmp_path), manifest=str(manifest), report=str(ledger), inventory=str(inv))

    others: list[Obj] = [{"codegraph_sha256": "0" * 64}, {"language": "cpp"}]
    stale = [run(tmp_path / "없음.json")]
    stale += [run(_ledger(tmp_path, cg, None, over)) for over in others]
    (tmp_path / "normalize-report.json").write_text("{깨짐", encoding="utf-8")
    stale.append(run(tmp_path / "normalize-report.json"))
    for doc in stale:
        assert doc["status"] == "failed" and doc["coverage"]["counts"] == {"report-stale": 1}, doc["faults"]
    assert stale[0]["faults"][0]["detail"].startswith("장부가 없거나 읽을 수 없다")


def test_inventory_가_없거나_manifest_의_것이_아니면_inventory_stale(tmp_path: Path) -> None:
    cg = _mapped(tmp_path)
    ledger = _ledger(tmp_path, cg)
    inv = _inventory(tmp_path)
    manifest = _manifest(tmp_path, cg, inv)
    doc = V.verify(str(cg), str(tmp_path), manifest=str(manifest), report=str(ledger), inventory=str(tmp_path / "없음.json"))
    assert doc["status"] == "failed" and doc["coverage"]["counts"] == {"inventory-stale": 1}
    assert doc["coverage"]["inventory"] == "missing"
    inv.write_text(inv.read_text(encoding="utf-8") + "\n", encoding="utf-8")        # manifest 가 적은 해시와 달라진다
    doc = V.verify(str(cg), str(tmp_path), manifest=str(manifest), report=str(ledger), inventory=str(inv))
    assert doc["status"] == "failed" and doc["coverage"]["counts"] == {"inventory-stale": 1}
    assert doc["faults"][0]["detail"] == "inventory 가 manifest 의 것이 아니다"


def test_수집하지_않은_언어는_기록만_하고_막지_않는다(tmp_path: Path) -> None:
    ts: Obj = {"language": "ts", "status": "unsupported", "reason": "collector none"}
    doc = _covered(tmp_path, languages={"py": PY_ROW, "ts": TS_ROW}, files={"a.py": COLLECTED, "x.ts": ts, "y.ts": ts})
    assert doc["status"] == "passed" and doc["fit"] == {"survey": "ready", "blocked_by": []}
    assert doc["coverage"]["counts"] == {"language-not-collected": 1} and doc["total"] == 1
    assert doc["coverage"]["languages_not_collected"] == ["ts"] and doc["coverage"]["unsupported"] == 2
    assert doc["faults"][0]["detail"] == "2개 파일 — 수집기 none"


def test_고른_언어인데_인용되지_않는_파일은_기록만_하고_막지_않는다(tmp_path: Path) -> None:
    gap: Obj = {"language": "py", "status": "no-symbols"}
    doc = _covered(tmp_path, files={"a.py": COLLECTED, "e.py": gap})
    assert doc["status"] == "passed" and doc["fit"]["survey"] == "ready"
    assert doc["coverage"]["counts"] == {"coverage-gap": 1} and doc["coverage"]["no_symbols"] == 1
    assert doc["faults"][0]["at"] == "$.files['e.py']"


def test_수집_실패_기록이_있으면_collect_failed_로_막는다(tmp_path: Path) -> None:
    failure = tmp_path / "collect-failure.json"
    failure.write_text(json.dumps({"status": "failed", "step": "normalize", "argv": ["x"], "returncode": 2,
                                   "stderr_tail": ["앞", "죽음"]}), encoding="utf-8")
    doc = _covered(tmp_path, failure=failure)
    assert doc["status"] == "failed" and doc["coverage"]["counts"] == {"collect-failed": 1}
    assert "normalize" in doc["faults"][0]["detail"] and "죽음" in doc["faults"][0]["detail"] and "앞" not in doc["faults"][0]["detail"]
    failure.write_text("{깨짐", encoding="utf-8")
    doc = _covered(tmp_path, failure=failure)
    assert doc["status"] == "failed" and doc["coverage"]["counts"] == {"collect-failed": 1}


def test_지도를_못_읽으면_장부와_inventory_는_보지_않고_실패_기록은_본다(tmp_path: Path) -> None:
    cg = tmp_path / "codegraph.json"
    cg.write_text("{", encoding="utf-8")
    failure = tmp_path / "collect-failure.json"
    failure.write_text(json.dumps({"status": "failed", "step": "plan", "argv": [], "returncode": 1, "stderr_tail": []}),
                       encoding="utf-8")
    missing = str(tmp_path / "없음.json")
    doc = V.verify(str(cg), str(tmp_path), report=missing, inventory=missing, failure=str(failure))
    assert doc["checks_run"] == ["V0"]
    assert doc["integrity"]["counts"] == {"unreadable": 1} and doc["coverage"]["counts"] == {"collect-failed": 1}


def test_수집이_죽어_지도가_없을_때의_결함_문서는_실패이고_적합하지_않다() -> None:
    doc = V.failure_doc({"status": "failed", "step": "clang-uml", "argv": ["clang-uml"], "returncode": 2, "stderr_tail": ["x"]})
    assert doc["status"] == "failed" and doc["total"] == 1 and doc["checks_run"] == []
    assert doc["fit"] == {"survey": "blocked", "blocked_by": ["collect-failed"]}
    assert doc["coverage"]["counts"] == {"collect-failed": 1} and doc["coverage"]["inventory"] == "missing"
    assert doc["faults"][0]["detail"] == "clang-uml 가 종료 코드 2 로 죽었다"
