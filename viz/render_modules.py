#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='render_modules.py']"/>
# 모듈 사이의 의존 관계를 Graphviz 로 그리는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""render_modules.py — codegraph.json 의 모듈 의존 그래프를 Graphviz 로 그린다.

노드는 모듈 이름 + 클래스 수 + 대표 이름, 엣지는 뼈대 · 순환 · 외부 접촉 세 종류다.
splines=spline 을 쓴다 — 순환 간선이 constraint=false 라 같은 랭크에 놓이고, 직선으로 그으면
사이의 노드를 관통해 라벨을 지운다. constraint=true 는 뼈대에만 건다. 순환·외부 접촉까지 켜면
rankdir=BT 레이어가 흩어진다.

언어 무관하다. C++ · C# 의 codegraph.json 이 같은 스키마 v2 라 렌더러는 하나면 된다.

  python3 render_modules.py <codegraph.json> [-o 출력경로없는이름]
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from typing import NotRequired, TypedDict, cast

import networkx as nx


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.CodeNode']"/>
# codegraph.json 파일 안의 nodes 배열에 들어 있는 항목(클래스나 함수 같은 코드 조각) 하나가 어떤 모양인지를 미리 적어 둔 설계도다. 이것도 실제로 동작하는 클래스가 아니라 타입 검사용 표시다.
# 쓰는 것: 없음 · 쓰이는 곳: viz.render_modules.CodeGraph
# ── codegraph.json (스키마 v2) 의 모양. `machine/normalize.py` 의 `_assemble` 반환부와 같다.
#    이 선언이 없으면 pyright 가 이종(heterogeneous) dict 를 `int | list | str` 합집합으로 뭉개고,
#    그 dict 를 받은 쪽의 첨자 접근이 전부 Unknown 으로 오염된다.
#    ⚠ `render_classes.py` 에 같은 선언이 있다 — 스키마가 바뀌면 두 곳을 함께 고친다.
class CodeNode(TypedDict):
    """codegraph.json 의 nodes[] 한 칸."""
    id: str
    name: str
    kind: str
    module: str | None
    file: str | None
    line: int | None
    collapsed_from: NotRequired[list[str]]   # 외부 노드만 갖는다 — R2 로 접힌 원본 이름들
    signature: NotRequired[str]              # clang-doc 이 붙었을 때만
    doc: NotRequired[str]                    # clang-doc 이 붙었을 때만


# `from` 은 파이썬 예약어라 class 문법으로는 필드로 못 적는다. 함수형 TypedDict 를 쓴다.
CodeEdge = TypedDict("CodeEdge", {
    "from": str,
    "to": str,
    "kind": str,
    "label": NotRequired[str | None],
    "file": NotRequired[str | None],
    "line": NotRequired[int | None],
    "occurrences": NotRequired[int],         # 같은 쌍이 두 번 이상 나왔을 때만 붙는다
})


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.CodeModule']"/>
# codegraph.json 파일 안의 modules 배열에 들어 있는 항목 하나가 어떤 모양(어떤 필드를 가지는지)인지를 미리 적어 둔 설계도 같은 것이다. 실제로 동작하는 클래스가 아니라, 타입 검사 도구가 실수를 잡아내도록 도와주는 표시일 뿐이다.
# 쓰는 것: 없음 · 쓰이는 곳: viz.render_modules.CodeGraph
class CodeModule(TypedDict):
    """codegraph.json 의 modules[] 한 칸."""
    id: str
    depends_on: list[str]


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.CodeGraph']"/>
# codegraph.json 파일 전체가 어떤 모양인지 정해 놓은 타입 선언이다. render_classes.py 의 동명 클래스와 내용은 같지만 별개의 선언이다(파일마다 따로 정의).
# 쓰는 것: viz.render_modules.CodeModule, viz.render_modules.CodeNode · 쓰이는 곳: 없음
class CodeGraph(TypedDict):
    """codegraph.json 전체."""
    schema_version: int
    language: str
    platform: str
    source_tool: str
    repo_commit: str | None
    nodes: list[CodeNode]
    edges: list[CodeEdge]
    modules: list[CodeModule]


# ── 색.
C_BACKBONE = "#2e75b6"   # 뼈대(비순환) 의존 — aggregate 계열 파랑
C_CYCLE = "#D50000"      # 순환. 여기 말고 빨강이 나오면 안 된다
C_EXTERNAL = "#777777"   # 외부 접촉 — depend 계열 회색
C_BORDER = "#1f4e79"


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.esc']"/>
# 아무 값이나 문자열로 바꿔서 DOT 언어 안에서 안전하게 쓸 수 있게 손질해 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: viz.render_modules.emit_dot
def esc(s: object) -> str:
    """DOT 문자열용."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.esch']"/>
# 아무 값이나 문자열로 바꿔서 Graphviz의 HTML 라벨 안에서 안전하게 쓸 수 있게 손질해 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: viz.render_modules.node_label
def esch(s: object) -> str:
    """HTML 라벨용. 클래스 이름에 제네릭/템플릿 꺾쇠가 실제로 들어온다
    (Action<TOwner>, UI_Base<T> 등) — DOT 이스케이프만으로는 dot 이 HTML 태그로 읽고 죽는다."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.load']"/>
# codegraph.json 파일을 열어서 파이썬이 다룰 수 있는 데이터로 읽어 오는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: viz.render_modules.main
def load(path: str) -> CodeGraph:
    # JSON 경계라 cast 가 불가피하다 — json.load 는 Any 를 준다. 실제 스키마 대조는
    # 바로 아래 schema_version 검사가 런타임에 맡는다.
    g = cast(CodeGraph, json.load(open(path, encoding="utf-8")))
    if g.get("schema_version") != 2:
        print(f"경고 — schema_version {g.get('schema_version')} (2 를 기대). 계속한다.", file=sys.stderr)
    return g


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.build']"/>
# codegraph 데이터를 가지고, 어느 모듈이 어느 모듈을 필요로 하는지를 나타내는 방향 그래프와 그 그래프를 그리는 데 필요한 여러 부가 정보를 만드는 함수다.
# 쓰는 것: networkx.DiGraph, networkx.simple_cycles · 쓰이는 곳: viz.render_modules.main
# ⚠ networkx 의 `DiGraph` 는 **런타임에 첨자를 받지 않는다**(`nx.DiGraph[str]` 은 TypeError).
#   타입 스텁에서만 제네릭이므로 주석은 반드시 따옴표로 감싼다.
def build(g: CodeGraph) -> tuple[
    "nx.DiGraph[str]", dict[str, list[str]], dict[tuple[str, str], int],
    dict[str, CodeNode], list[list[str]], set[tuple[str, str]],
]:
    """모듈 층 그래프와 노드별 부가 정보를 만든다."""
    nodes = {n["id"]: n for n in g["nodes"]}
    mods = {m["id"]: set(m["depends_on"]) for m in g["modules"]}

    members: defaultdict[str, list[str]] = defaultdict(list)   # 모듈 -> 그 안의 1차 클래스 이름
    for n in g["nodes"]:
        mod = n.get("module")
        if n["kind"] != "external" and mod is not None and mod in mods:
            members[mod].append(n["name"])

    # 모듈 -> 외부 노드 접촉 횟수. 외부 섬으로 가는 간선은 모듈 층에서도 따로 센다.
    ext_touch: defaultdict[tuple[str, str], int] = defaultdict(int)
    externals: dict[str, CodeNode] = {}
    for e in g["edges"]:
        a, b = nodes.get(e["from"]), nodes.get(e["to"])
        if not a or not b or b["kind"] != "external":
            continue
        amod = a.get("module")
        if amod is not None and amod in mods:
            ext_touch[(amod, b["id"])] += e.get("occurrences", 1)
            externals[b["id"]] = b

    G: "nx.DiGraph[str]" = nx.DiGraph()
    G.add_nodes_from(mods)
    for m, deps in mods.items():
        for d in deps:
            if d in mods:
                G.add_edge(m, d)

    # 순환에 참여하는 간선을 표시한다 — 빨강의 유일한 대상.
    cycles = list(nx.simple_cycles(G))
    cyc_edges: set[tuple[str, str]] = set()
    for c in cycles:
        for i in range(len(c)):
            cyc_edges.add((c[i], c[(i + 1) % len(c)]))
    return G, members, ext_touch, externals, cycles, cyc_edges


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.node_label']"/>
# 모듈 하나를 그림 상자로 그릴 때, 그 상자 안에 넣을 글자(모듈 이름, 클래스 개수, 대표 클래스 이름 몇 개)를 HTML 표 문자열로 만드는 함수다.
# 쓰는 것: viz.render_modules.esch · 쓰이는 곳: viz.render_modules.emit_dot
def node_label(mod: str, names: list[str]) -> str:
    """이름 + 클래스 수 + 대표 이름 3개."""
    short = sorted(names, key=lambda s: (len(s), s))
    head = [s.split(".")[-1].split("::")[-1] for s in short[:3]]
    rest = len(names) - len(head)
    body = ", ".join(head) + (f" 외 {rest}" if rest > 0 else "")
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
        f'<TR><TD><B>{esch(mod)}</B></TD></TR>'
        f'<TR><TD><FONT POINT-SIZE="9" COLOR="#555555">클래스 {len(names)}</FONT></TD></TR>'
        + (f'<TR><TD><FONT POINT-SIZE="8" COLOR="#888888">{esch(body)}</FONT></TD></TR>' if names else "")
        + "</TABLE>>"
    )


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.emit_dot']"/>
# 이미 계산된 모듈 의존 그래프를 실제 Graphviz DOT 문법 텍스트로 바꿔주는 함수다. 그림을 그리는 규칙(색, 순서, 범례)을 전부 이 함수 안에서 정한다.
# 쓰는 것: viz.render_modules.esc, viz.render_modules.node_label · 쓰이는 곳: viz.render_modules.main
def emit_dot(g: CodeGraph, path_in: str, G: "nx.DiGraph[str]",
             members: dict[str, list[str]], ext_touch: dict[tuple[str, str], int],
             externals: dict[str, CodeNode], cycles: list[list[str]],
             cyc_edges: set[tuple[str, str]], show_external: bool) -> str:
    lang = g.get("language", "?")
    ext_note = "" if show_external else "  [이번 렌더에서는 생략됨 — --external 로 켠다]"
    out: list[str] = []
    w = out.append

    # ── DOT 헤더 주석
    w(f"""/* 모듈 의존 그래프 — {lang} ({g.get('repo_commit', '?')})
 *
 * 목표 : 어느 모듈이 어느 모듈에 의존하는가, 그리고 순환이 어디 있는가.
 * 범위 : codegraph.json (schema v2) 의 modules[] + __external__ 접촉.
 *        출처 {path_in}
 *        도구 {g.get('source_tool', '?')}
 *
 * 엣지 3종
 *   파랑 실선  비순환 의존 — 레이아웃 뼈대 (constraint=true)
 *   빨강 굵게  순환에 참여하는 의존 — P6 게이트 (constraint=false)
 *   회색 점선  외부 패키지 접촉 — C-9 R3 섬으로 (constraint=false, R6){ext_note}
 *
 * ⚠ 이것은 링크 의존이 아니라 **타입 의존**이다 (C-15). 클래스 간선에서 유도했다.
 * ⚠ 순환 판정은 기계가 하지 않는다 — 빨강은 "사람이 볼 곳" 표시이고,
 *   허용/위반/오탐 판정은 codegraph-rules.toml 에 사람이 적는다.
 *
 * 렌더: dot -Tsvg X.dot -o X.svg && dot -Tpng -Gdpi=140 X.dot -o X.png
 */
digraph modules {{
  // P4 + P5 + A1 — 셋은 함께 다닌다
  rankdir=BT;
  splines=spline;
  ranksep=1.0;
  nodesep=0.55;
  bgcolor="white";
  node [shape=box, style="rounded,filled", fillcolor="#f7f9fc",
        color="{C_BORDER}", fontname="Helvetica", fontsize=11];
  edge [fontname="Helvetica", fontsize=9];
""")

    # ── 1차 모듈 밴드
    w('  subgraph cluster_first {')
    w(f'    label="1차 코드 — 모듈 {G.number_of_nodes()} / 의존 {G.number_of_edges()}";')
    w(f'    labeljust="l"; fontname="Helvetica"; fontsize=11; color="{C_BORDER}"; style="rounded";')
    for m in sorted(G.nodes()):
        w(f'    "{esc(m)}" [label={node_label(m, members.get(m, []))}];')
    w("  }\n")

    # ── __external__ 섬. **기본은 끈다** — 켜면 외부 노드가 세로로 늘어져 1차 밴드를 압도하고,
    #    constraint=false 점선이 캔버스를 가로질러 스파게티가 된다. 이 다이어그램의 논증은
    #    "1차 모듈 간 의존과 순환" 하나다. 외부 접촉 수치는 external-nodes.tsv 에 있다.
    if externals and show_external:
        w("  subgraph cluster_external {")
        w(f'    label="__external__ — 외부 {len(externals)}개 (C-9 R1~R3 적용 후)";')
        w('    labeljust="l"; fontname="Helvetica"; fontsize=11;')
        w('    color="#999999"; style="rounded,dashed"; bgcolor="#fafafa";')
        order = sorted(externals.values(), key=lambda n: -len(n.get("collapsed_from", [])))
        for n in order:
            cf = len(n.get("collapsed_from", []))
            w(f'    "{esc(n["id"])}" [shape=box, style="filled", fillcolor="#eeeeee", '
              f'color="#999999", fontsize=9, label="{esc(n["name"])}\\n({cf}종 접힘)"];')
        # 보이지 않는 constraint=true 사슬 — rank=same 은 BT+클러스터에서 못 믿는다.
        # 한 열로 쌓으면 세로로 늘어져 캔버스를 잡아먹으므로 3열로 나눈다.
        cols = 3
        for c in range(cols):
            col = order[c::cols]
            for a, b in zip(col, col[1:]):
                w(f'    "{esc(a["id"])}" -> "{esc(b["id"])}" [style=invis, constraint=true];')
        w("  }\n")

    # ── 뼈대는 constraint=true, 순환·외부는 false
    w("  // 뼈대 — 비순환 의존. 레이아웃 골격을 만든다.")
    w(f'  edge [color="{C_BACKBONE}", arrowhead=vee, style=solid, penwidth=1.2, constraint=true];')
    for a, b in sorted(G.edges()):
        if (a, b) not in cyc_edges:
            w(f'  "{esc(a)}" -> "{esc(b)}";')

    if cyc_edges:
        w("\n  // P6 — 순환 참여 간선. 여기 말고 빨강이 나오면 안 된다.")
        w(f'  edge [color="{C_CYCLE}", arrowhead=vee, style=solid, penwidth=2.6, constraint=false];')
        # 상호 의존(2-순환)은 화살표 둘이 아니라 dir=both 하나로 —
        # 같은 쌍에 선이 겹쳐 그려지는 것을 막는다.
        mutual = {tuple(sorted(e)) for e in cyc_edges if (e[1], e[0]) in cyc_edges}
        for a, b in sorted(mutual):
            w(f'  "{esc(a)}" -> "{esc(b)}" [dir=both, arrowtail=vee, label="상호"];')
        for a, b in sorted(cyc_edges):
            if tuple(sorted((a, b))) not in mutual:
                w(f'  "{esc(a)}" -> "{esc(b)}";')

    if ext_touch and show_external:
        w("\n  // 외부 접촉 — R6 대로 constraint=false. 섬은 레이어를 왜곡하지 않는다.")
        w(f'  edge [color="{C_EXTERNAL}", arrowhead=vee, style=dashed, penwidth=1.0, constraint=false];')
        for (m, x), cnt in sorted(ext_touch.items(), key=lambda kv: -kv[1]):
            lab = f' [label="{cnt}"]' if cnt > 1 else ""
            w(f'  "{esc(m)}" -> "{esc(x)}"{lab};')

    # ── 범례 — 실제로 그린 예시 엣지
    w("""
  subgraph cluster_legend {
    label="범례"; labeljust="l"; fontname="Helvetica"; fontsize=10;
    color="#cccccc"; style="rounded";
    node [shape=plaintext, style="", fillcolor="none", fontsize=9, height=0.2];
    La [label="A"]; Lb [label="B"];
    Lc [label="C"]; Ld [label="D"];
    Le [label="E"]; Lf [label="외부"];""")
    w(f'    La -> Lb [color="{C_BACKBONE}", arrowhead=vee, penwidth=1.2, '
      'label="의존 (비순환)", constraint=false];')
    w(f'    Lc -> Ld [color="{C_CYCLE}", arrowhead=vee, penwidth=2.6, '
      'label="순환 — 사람이 볼 곳", constraint=false];')
    w(f'    Le -> Lf [color="{C_EXTERNAL}", arrowhead=vee, style=dashed, '
      'label="외부 접촉", constraint=false];')
    # 범례 행을 수직으로 쌓는다 — 안 하면 캔버스 너비만큼 늘어난다
    w('    La -> Lc [style=invis, constraint=true];')
    w('    Lc -> Le [style=invis, constraint=true];')
    w("  }")

    # ── 사이클이 없다면 그 부재를 단언한다
    if not cycles:
        w('\n  note_nocycle [shape=note, fillcolor="#eefaee", color="#4a7",'
          ' label="순환 없음 — 모듈 의존이 단일 방향이다", fontsize=9];')

    w("}")
    return "\n".join(out)


# <include file="machine/comments.xml" path="//term[@id='viz.render_modules.main']"/>
# codegraph.json 하나를 읽어 모듈 의존 관계 다이어그램(svg/png/dot)을 파일로 만들어내는, 이 파일을 명령줄에서 실행했을 때 맨 처음 호출되는 함수다.
# 쓰는 것: viz.render_modules.load, viz.render_modules.build, viz.render_modules.emit_dot · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph", help="codegraph.json")
    ap.add_argument("-o", "--out", help="출력 경로(확장자 없이). 기본은 입력 옆 <lang>-modules")
    ap.add_argument("--external", action="store_true",
                    help="__external__ 섬을 함께 그린다. 기본은 끔 — 켜면 1차 밴드를 압도한다")
    a = ap.parse_args()
    # argparse.Namespace 의 속성은 Any 다. 타입 있는 지역 변수로 한 번 받아
    # 아래 경로 계산까지 Unknown 이 번지지 않게 한다.
    cg_path: str = a.codegraph
    out_base: str | None = a.out
    show_external: bool = a.external

    g = load(cg_path)
    G, members, ext_touch, externals, cycles, cyc_edges = build(g)
    dot = emit_dot(g, cg_path, G, members, ext_touch, externals, cycles, cyc_edges, show_external)

    base = out_base or os.path.join(os.path.dirname(os.path.abspath(cg_path)),
                                    f"{g.get('language', 'x')}-modules")
    os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
    open(base + ".dot", "w", encoding="utf-8").write(dot)

    for fmt, extra in (("svg", []), ("png", ["-Gdpi=140"])):
        r = subprocess.run(["dot", f"-T{fmt}"] + extra + [base + ".dot", "-o", f"{base}.{fmt}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"dot -T{fmt} 실패:\n{r.stderr}", file=sys.stderr)
            return 1

    print(f"{base}.svg / .png / .dot")
    print(f"  언어 {g.get('language')} — 모듈 {G.number_of_nodes()} / 의존 {G.number_of_edges()}"
          f" / 외부 {len(externals)}")
    print(f"  순환 {len(cycles)}개, 순환 참여 간선 {len(cyc_edges)}개")
    for c in sorted(cycles, key=len)[:6]:
        print("    " + " -> ".join(c) + " -> " + c[0])
    if len(cycles) > 6:
        print(f"    ... 외 {len(cycles) - 6}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
