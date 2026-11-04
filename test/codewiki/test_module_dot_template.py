"""모듈 DOT 템플릿이 제자리에서 렌더되는지 — 머리 · 범례."""
import os
import shutil
import subprocess
import sys
from typing import cast

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from codewiki.python.viz.render_modules import CodeGraph, build, emit_dot  # noqa: E402


def _graph(language: object) -> CodeGraph:
    return cast(CodeGraph, {"schema_version": 2, "language": language, "platform": "x", "source_tool": "t", "repo_commit": "abc",
            "nodes": [{"id": "a.A", "name": "A", "kind": "class", "module": "a"},
                      {"id": "b.B", "name": "B", "kind": "class", "module": "b"}],
            "edges": [{"from": "a.A", "to": "b.B", "kind": "dependency"}],
            "modules": [{"id": "a", "depends_on": ["b"]}, {"id": "b", "depends_on": []}]})


def _dot(g: CodeGraph) -> str:
    G_, members, ext_touch, externals, cycles, cyc_edges = build(g)
    return emit_dot(g, "cg.json", G_, members, ext_touch, externals, cycles, cyc_edges, False)


def test_모듈_DOT_의_머리와_범례는_제자리에서_이어진다():
    dot = _dot(_graph("python"))
    assert dot.startswith("/* 모듈 의존 그래프 — python (abc)\n")
    assert '  edge [fontname="Helvetica", fontsize=9];\n\n  subgraph cluster_first {\n' in dot
    assert '\n\n  subgraph cluster_legend {\n' in dot
    assert '    Le [label="E"]; Lf [label="외부"];\n    La -> Lb [' in dot
    if shutil.which("dot"):
        r = subprocess.run(["dot", "-Tcanon"], input=dot, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


def test_모듈_DOT_머리는_언어가_문자열이_아니어도_글자로_찍는다():
    assert _dot(_graph(None)).startswith("/* 모듈 의존 그래프 — None (abc)\n")
    assert _dot(_graph(3)).startswith("/* 모듈 의존 그래프 — 3 (abc)\n")
