#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='render_modules.py']"/>
# 모듈 사이의 의존 관계를 Graphviz 로 그리는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""render_modules.py — codegraph.json 의 모듈 의존 그래프를 Graphviz 로 그린다.

사용자의 P1~P6 방법론을 **모듈 층**에 적용한 것이다. 클래스 층이 아니므로 P3(UML 3분할)는
노드 안에 "클래스 수 + 대표 이름" 으로 치환된다 — 모듈 하나가 무엇을 담는지 노드만 보고 알게.

  P1 클러스터   1차 모듈 밴드 / __external__ 섬 (C-9 R3)
  P2 엣지 구분  DAG 뼈대 · 순환 · 외부 접촉 셋을 색·굵기로 가른다
  P4 rankdir=BT 의존받는 쪽(잎)이 위, 오케스트레이터가 아래
  P5 splines=spline  ⚠ 스킬 기본은 line 이지만 여기서는 spline 이다. 순환 간선이
                     constraint=false 라 같은 랭크에 놓이고, 직선으로 그으면 사이의 노드를
                     **관통해 라벨을 지운다**(실측). P5 의 목적은 가독성이므로 spline 이 맞다
  P6 빨강 게이트 순환 간선만 굵은 빨강. 그 외에 빨강이 나오면 안 된다
  A1 constraint  뼈대만 true. 순환·외부 접촉은 false — 없으면 BT 레이어가 흩어진다

언어 무관하다. C++ · C# 의 codegraph.json 이 같은 스키마 v2 라 렌더러는 하나면 된다.

  python3 render_modules.py <codegraph.json> [-o 출력경로없는이름]
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict

import networkx as nx

# ── 색. 스킬 P2 의 5종 팔레트에서 이 다이어그램이 쓰는 것만 가져왔다.
C_BACKBONE = "#2e75b6"   # 뼈대(비순환) 의존 — aggregate 계열 파랑
C_CYCLE = "#D50000"      # P6 — 순환. 여기 말고 빨강이 나오면 안 된다
C_EXTERNAL = "#777777"   # 외부 접촉 — depend 계열 회색
C_BORDER = "#1f4e79"


# <include file="docs/codegraph/comments.xml" path="//term[@id='render_modules.esc']"/>
# DOT 문자열용 이스케이프.
# 쓰는 것: 없음 · 쓰이는 곳: emit_dot
def esc(s):
    """DOT 문자열용."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


# <include file="docs/codegraph/comments.xml" path="//term[@id='render_modules.esch']"/>
# HTML 라벨용 이스케이프. 클래스 이름에 제네릭 꺾쇠가 실제로 들어오기 때문에 필요하다.
# 쓰는 것: 없음 · 쓰이는 곳: node_label
def esch(s):
    """HTML 라벨용. 🔵 클래스 이름에 제네릭/템플릿 꺾쇠가 실제로 들어온다
    (Action<TOwner>, UI_Base<T> 등) — DOT 이스케이프만으로는 dot 이 HTML 태그로 읽고 죽는다."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# <include file="docs/codegraph/comments.xml" path="//term[@id='load']"/>
# codegraph.json 을 읽는다. 스키마 판이 다르면 경고만 하고 계속한다.
# 쓰는 것: 없음 · 쓰이는 곳: render_modules.main
def load(path):
    g = json.load(open(path, encoding="utf-8"))
    if g.get("schema_version") != 2:
        print(f"경고 — schema_version {g.get('schema_version')} (2 를 기대). 계속한다.", file=sys.stderr)
    return g


# <include file="docs/codegraph/comments.xml" path="//term[@id='render_modules.build']"/>
# 모듈 층 그래프와 노드마다 붙일 부가 정보를 만든다.
# 쓰는 것: modules[] · 쓰이는 곳: render_modules.main
def build(g):
    """모듈 층 그래프와 노드별 부가 정보를 만든다."""
    nodes = {n["id"]: n for n in g["nodes"]}
    mods = {m["id"]: set(m["depends_on"]) for m in g["modules"]}

    members = defaultdict(list)          # 모듈 -> 그 안의 1차 클래스 이름
    for n in g["nodes"]:
        if n["kind"] != "external" and n.get("module") in mods:
            members[n["module"]].append(n["name"])

    # 모듈 -> 외부 노드 접촉 횟수. R3 섬으로 가는 간선은 모듈 층에서도 따로 센다.
    ext_touch = defaultdict(int)
    externals = {}
    for e in g["edges"]:
        a, b = nodes.get(e["from"]), nodes.get(e["to"])
        if not a or not b or b["kind"] != "external":
            continue
        if a.get("module") in mods:
            ext_touch[(a["module"], b["id"])] += e.get("occurrences", 1)
            externals[b["id"]] = b

    G = nx.DiGraph()
    G.add_nodes_from(mods)
    for m, deps in mods.items():
        for d in deps:
            if d in mods:
                G.add_edge(m, d)

    # 순환에 참여하는 간선을 표시한다 — P6 빨강의 유일한 대상.
    cycles = list(nx.simple_cycles(G))
    cyc_edges = set()
    for c in cycles:
        for i in range(len(c)):
            cyc_edges.add((c[i], c[(i + 1) % len(c)]))
    return G, members, ext_touch, externals, cycles, cyc_edges


# <include file="docs/codegraph/comments.xml" path="//term[@id='node_label']"/>
# 모듈 상자 안에 넣을 이름 · 클래스 수 · 대표 이름 세 줄을 만든다.
# 쓰는 것: render_modules.esch · 쓰이는 곳: emit_dot
def node_label(mod, names):
    """P3 의 모듈 층 대응 — 이름 + 클래스 수 + 대표 이름 3개."""
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='emit_dot']"/>
# 모듈 그래프를 Graphviz DOT 문자열로 찍어 낸다.
# 쓰는 것: node_label, render_modules.esc · 쓰이는 곳: render_modules.main
def emit_dot(g, path_in, G, members, ext_touch, externals, cycles, cyc_edges, show_external):
    lang = g.get("language", "?")
    ext_note = "" if show_external else "  [이번 렌더에서는 생략됨 — --external 로 켠다]"
    out = []
    w = out.append

    # ── 헤더 주석 (스킬: 제목·범위·엣지 종류·출처·렌더 명령)
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

    # ── P1 — 1차 모듈 밴드
    w('  subgraph cluster_first {')
    w(f'    label="1차 코드 — 모듈 {G.number_of_nodes()} / 의존 {G.number_of_edges()}";')
    w(f'    labeljust="l"; fontname="Helvetica"; fontsize=11; color="{C_BORDER}"; style="rounded";')
    for m in sorted(G.nodes()):
        w(f'    "{esc(m)}" [label={node_label(m, members.get(m, []))}];')
    w("  }\n")

    # ── P1 — __external__ 섬 (C-9 R3). **기본은 끈다.**
    #    🔵 켜고 렌더해 보니 외부 17개가 세로로 늘어져 1차 밴드를 압도했고, constraint=false
    #    점선이 캔버스를 가로질러 스파게티가 됐다. 이 다이어그램의 논증은 "1차 모듈 간 의존과
    #    순환" 하나다 — 외부 접촉은 **다른 논증**이라 같은 장에 넣으면 둘 다 죽는다.
    #    스킬 Phase 2 의 "생략이 가치다" 를 그대로 적용한다. 수치는 external-nodes.tsv 에 있다.
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
        # 한 열로 쌓으면 세로로 늘어져 캔버스를 잡아먹으므로 3열로 나눈다(스킬 anti-sprawl).
        cols = 3
        for c in range(cols):
            col = order[c::cols]
            for a, b in zip(col, col[1:]):
                w(f'    "{esc(a["id"])}" -> "{esc(b["id"])}" [style=invis, constraint=true];')
        w("  }\n")

    # ── P2 + A1 — 뼈대는 constraint=true, 순환·외부는 false
    w("  // 뼈대 — 비순환 의존. 레이아웃 골격을 만든다.")
    w(f'  edge [color="{C_BACKBONE}", arrowhead=vee, style=solid, penwidth=1.2, constraint=true];')
    for a, b in sorted(G.edges()):
        if (a, b) not in cyc_edges:
            w(f'  "{esc(a)}" -> "{esc(b)}";')

    if cyc_edges:
        w("\n  // P6 — 순환 참여 간선. 여기 말고 빨강이 나오면 안 된다.")
        w(f'  edge [color="{C_CYCLE}", arrowhead=vee, style=solid, penwidth=2.6, constraint=false];')
        # 상호 의존(2-순환)은 화살표 둘이 아니라 dir=both 하나로 — 스킬 Phase 3 규정이고,
        # 같은 쌍에 선이 겹쳐 그려지는 것도 막는다.
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

    # ── 범례 — 텍스트 표가 아니라 실제로 그린 예시 엣지
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

    # ── 사이클이 없다면 그 부재를 단언한다 (스킬 Phase 1 체크리스트)
    if not cycles:
        w('\n  note_nocycle [shape=note, fillcolor="#eefaee", color="#4a7",'
          ' label="순환 없음 — 모듈 의존이 단일 방향이다", fontsize=9];')

    w("}")
    return "\n".join(out)


# <include file="docs/codegraph/comments.xml" path="//term[@id='render_modules.main']"/>
# 모듈 다이어그램 도구의 명령줄 진입점.
# 쓰는 것: load, render_modules.build, emit_dot · 쓰이는 곳: 없음
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph", help="codegraph.json")
    ap.add_argument("-o", "--out", help="출력 경로(확장자 없이). 기본은 입력 옆 <lang>-modules")
    ap.add_argument("--external", action="store_true",
                    help="__external__ 섬을 함께 그린다. 기본은 끔 — 켜면 1차 밴드를 압도한다")
    a = ap.parse_args()

    g = load(a.codegraph)
    G, members, ext_touch, externals, cycles, cyc_edges = build(g)
    dot = emit_dot(g, a.codegraph, G, members, ext_touch, externals, cycles, cyc_edges, a.external)

    base = a.out or os.path.join(os.path.dirname(os.path.abspath(a.codegraph)),
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
