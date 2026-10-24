"""파일 템플릿이 제자리에서 렌더되는지 — 보고서 뼈대 data.ts 와 모듈 DOT 의 머리 · 범례."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from viz.init import writeSkeleton  # noqa: E402
from viz.render_modules import CodeGraph, build, emit_dot  # noqa: E402

DATA_TS = '''import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: "v1",
  slug: "s",
  specName: "T `x` \\"q\\" {{b}}",
  date: "2026-01-01",
  branch: "main",
  decisions: [],
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮겨 적는다.
  //   report-term collect <plan.md> <terms-db.json>  →  (스킬이 묻는다)  →  report-term grade  →  report-term emit
  // terms.json 의 { "용어": { TermMeans, UserMentalValue } } 를
  // { id, label, short, kind, mental } 로 옮긴다. 자동 import 하지 않는다 — 이 파일은 사람이 읽는 파일이다.
  terms: [],
};
'''


def test_뼈대_data_ts_는_값만_바뀌고_나머지는_글자_그대로다(tmp_path: Path):
    writeSkeleton(str(tmp_path), "s", "2026-01-01", 'T `x` "q" {{b}}', "main", "v1")
    assert (tmp_path / "data.ts").read_text(encoding="utf-8") == DATA_TS


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
