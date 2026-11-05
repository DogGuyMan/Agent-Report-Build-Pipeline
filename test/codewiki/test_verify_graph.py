"""`verify_graph.py` 의 네 층 — 읽기 · 꼴 · 정합 · 근거 — 와 결과 파일."""
import hashlib
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "machine")]
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


def test_표는_네_층_스물한_코드다() -> None:
    assert len(V.LAYER) == 21
    assert sorted(set(V.LAYER.values())) == ["V0 읽기", "V1 꼴", "V2 정합", "V3 근거"]
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
