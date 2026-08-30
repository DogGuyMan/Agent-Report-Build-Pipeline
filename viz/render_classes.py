#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='render_classes.py']"/>
# 모듈 하나를 골라 그 안의 클래스 관계도를 Graphviz 로 그리는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""render_classes.py — 모듈 하나를 골라 클래스 층 다이어그램을 그린다 (P1~P6 전체).

모듈 층(`render_modules.py`)이 "어디를 볼지" 를 알려준다면, 이 그림은 "그 안에서 무엇이
그렇게 만드는지" 를 보여준다. 순환의 중심 모듈을 골라 돌리는 것이 가장 값이 크다.

**입력이 둘인 이유.** `codegraph.json` 에는 멤버·메서드가 없다 — Track C §7 이
`nodes[].members` / `methods` 를 "나중에 붙일 자리, 지금 만들지 말 것" 으로 못박았기 때문이다.
그래서 P3(UML 3분할)의 살은 원시 산출물에서 따로 읽는다.

  구조(노드·간선·kind)  <- codegraph.json   ← 정본. 낱말 어긋남이 이미 교정돼 있다
  살(멤버·메서드)        <- clang-uml json    ← 표시용

⚠ **원시에서 간선을 읽지 않는다.** clang-uml 의 `aggregation` 은 codegraph 의 `composition`
을 뜻한다(D절). 원시를 직접 그리면 그 함정에 다시 빠진다.

⚠ **C# 은 아직 이 그림을 그릴 수 없다** — `roslyn-dump.json` 에 members/methods 가 없다.
`--detail` 없이 돌리면 3분할이 이름만 남은 상자가 되고, 그것은 P3 가 아니다.

  python3 render_classes.py <codegraph.json> --module material --detail <clang-uml.json>
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict

import networkx as nx

# ── P2 5종 팔레트 (스킬 Phase 3 표 그대로)
STYLE = {
    "inheritance":  ('color="#1f4e79", arrowhead=onormal, style=solid',            "상속"),
    "realization":  ('color="#333333", arrowhead=onormal, style=dashed',           "실현"),
    "composition":  ('color="#7030a0", dir=both, arrowtail=diamond, arrowhead=vee', "합성(소유)"),
    "aggregation":  ('color="#2e75b6", dir=both, arrowtail=odiamond, arrowhead=vee', "집약(참조)"),
    "dependency":   ('color="#777777", arrowhead=vee, style=dashed',               "의존(사용)"),
    "instantiation": ('color="#999999", arrowhead=onormal, style=dotted',          "템플릿 실체화"),
    "friendship":   ('color="#b58900", arrowhead=vee, style=dotted',               "friend"),
}
# A1 — 구조 엣지만 랭크를 잡는다. 의존 계열은 레이어를 가로지르되 왜곡하지 않는다.
BACKBONE = {"inheritance", "realization", "composition", "aggregation"}
C_CYCLE = "#D50000"


# <include file="machine/comments.xml" path="//term[@id='render_classes.esch']"/>
# HTML 라벨에 넣을 문자열의 꺾쇠와 앰퍼샌드를 안전하게 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: node_html
def esch(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# <include file="machine/comments.xml" path="//term[@id='render_classes.esc']"/>
# DOT 문자열에 넣을 따옴표와 역슬래시를 안전하게 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


# <include file="machine/comments.xml" path="//term[@id='render_classes.short']"/>
# 긴 이름에서 마지막 조각만 남긴다. 클러스터가 이미 맥락을 주기 때문이다.
# 쓰는 것: 없음 · 쓰이는 곳: node_html
def short(name):
    """SJH::Scene::Component -> Component. 모듈 클러스터가 이미 맥락을 준다."""
    return name.split("::")[-1].split(".")[-1]


ACCESS = {"public": "+", "protected": "#", "private": "-"}


# <include file="machine/comments.xml" path="//term[@id='load_detail']"/>
# 원시 분석 파일에서 이름마다 멤버 · 메서드 · 추상 여부를 뽑는다.
# 쓰는 것: 없음 · 쓰이는 곳: render_classes.main
def load_detail(path):
    """원문에서 이름 -> (members, methods, is_abstract) 를 뽑는다.

    두 갈래를 안다 — C++ 은 clang-uml(`elements[].display_name`),
    C# 은 roslyn-dump(`types[].name`). 키가 다를 뿐 소비하는 모양은 같게 맞춘다.
    ⚠ 여기서 걸러내기를 하지 않는다. 표시 정책은 node_html/pick_methods 몫이다.
    """
    d = json.load(open(path, encoding="utf-8"))
    out = {}

    if "elements" in d:                                  # clang-uml (C++)
        for e in d["elements"]:
            out[e.get("display_name")] = {
                "members": e.get("members") or [],
                "methods": e.get("methods") or [],
                "abstract": bool(e.get("is_abstract")),
            }
        return out

    for t in d.get("types", []):                         # roslyn-dump (C#)
        if t.get("members") is None and t.get("methods") is None:
            continue                                     # 외부 타입 — 살이 없다
        out[t.get("name")] = {
            "members": t.get("members") or [],           # name/type/access 는 키가 같다
            "methods": [{
                "name": m.get("name"),
                "access": m.get("access"),
                "is_constructor": bool(m.get("is_ctor")),
                "is_operator": False,
                "is_deleted": False,
                "is_defaulted": False,
                "is_pure_virtual": bool(m.get("is_abstract")),
                # pick_methods 는 인자 유무만 본다(인자 없는 Get*/Is* 걸러내기).
                "parameters": [None] * int(m.get("param_count") or 0),
            } for m in (t.get("methods") or [])],
            "abstract": bool(t.get("is_abstract")),
        }
    return out


# <include file="machine/comments.xml" path="//term[@id='pick_methods']"/>
# 그림에 실을 만한 메서드만 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: node_html
def pick_methods(methods, limit=6):
    """책임을 전달하는 메서드만. 사소한 getter/setter·연산자·특수멤버는 뺀다(스킬 Phase 2)."""
    out = []
    for m in methods:
        if m.get("is_constructor") or m.get("is_operator") or m.get("is_deleted"):
            continue
        n = m.get("name", "")
        if n.startswith("~") or m.get("is_defaulted"):
            continue
        # 인자 없는 Get*/Is* 는 단순 접근자로 본다 — 구조를 말해주지 않는다
        if not m.get("parameters") and (n.startswith("Get") or n.startswith("Is")):
            continue
        out.append(m)
    return out[:limit], max(0, len(out) - limit)


# <include file="machine/comments.xml" path="//term[@id='node_html']"/>
# 클래스 하나를 이름 · 멤버 · 메서드 3분할 상자로 그린다.
# 쓰는 것: render_classes.esch, render_classes.short, pick_methods · 쓰이는 곳: render_classes.main
def node_html(name, det, own_note):
    """P3 — UML 3분할. 이름(+스테레오타입) / 멤버(+소유권 노트) / 메서드."""
    rows = []
    stereo = ""
    if det and det["abstract"]:
        stereo = '<BR/><FONT POINT-SIZE="8" COLOR="#666666">&#171;interface&#187;</FONT>'
    rows.append(f'<TR><TD ALIGN="CENTER" BGCOLOR="#eef3fa"><B>{esch(short(name))}</B>{stereo}</TD></TR>')

    if det:
        mem = det["members"][:6]
        extra = len(det["members"]) - len(mem)
        if mem:
            lines = []
            for m in mem:
                note = own_note.get(m.get("name"), "")
                nt = f' <FONT COLOR="#7030a0">{note}</FONT>' if note else ""
                lines.append(
                    f'{ACCESS.get(m.get("access"), " ")} {esch(m.get("name"))}'
                    f' : <FONT COLOR="#666666">{esch(m.get("type"))}</FONT>{nt}')
            if extra:
                lines.append(f'<FONT COLOR="#999999">… 외 {extra}</FONT>')
            rows.append('<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="8">'
                        + "<BR/>".join(lines) + "</FONT></TD></TR>")

        meth, more = pick_methods(det["methods"])
        if meth:
            lines = []
            for m in meth:
                virt = ' <FONT COLOR="#1f4e79">v</FONT>' if m.get("is_pure_virtual") else ""
                lines.append(f'{ACCESS.get(m.get("access"), " ")} {esch(m.get("name"))}(){virt}')
            if more:
                lines.append(f'<FONT COLOR="#999999">… 외 {more}</FONT>')
            rows.append('<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="8">'
                        + "<BR/>".join(lines) + "</FONT></TD></TR>")

    return ('<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            + "".join(rows) + "</TABLE>>")


# <include file="machine/comments.xml" path="//term[@id='render_classes.main']"/>
# 클래스 다이어그램 도구의 명령줄 진입점.
# 쓰는 것: load_detail, node_html · 쓰이는 곳: 없음
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph")
    ap.add_argument("--module", required=True, help="초점 모듈 (예: material)")
    ap.add_argument("--detail", help="원문 — P3 3분할의 살. clang-uml(-g json) 또는 roslyn-dump.json")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    g = json.load(open(a.codegraph, encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    detail = load_detail(a.detail) if a.detail else {}
    if not detail:
        print("⚠ --detail 이 없다. 3분할 없이 이름 상자만 그린다 — P3 가 아니다.", file=sys.stderr)

    focus = a.module
    inside = {i for i, n in nodes.items() if n.get("module") == focus}
    if not inside:
        print(f"모듈 '{focus}' 에 노드가 없다. 있는 것: "
              f"{sorted({n.get('module') for n in nodes.values() if n.get('module')})}", file=sys.stderr)
        return 1

    # ── Phase 1 그라운딩 — 범위는 "초점 모듈 + 그와 직접 연결된 것" 이다. 전이 확장은 없다.
    edges = [e for e in g["edges"] if e["from"] in inside or e["to"] in inside]
    shown = set(inside) | {e["from"] for e in edges} | {e["to"] for e in edges}

    # 모듈 층 순환쌍 — 클래스 간선 중 그 쌍을 잇는 것이 P6 빨강 대상이다.
    MG = nx.DiGraph()
    for m in g["modules"]:
        for d in m["depends_on"]:
            MG.add_edge(m["id"], d)
    cyc_pairs = set()
    for c in nx.simple_cycles(MG):
        for i in range(len(c)):
            cyc_pairs.add((c[i], c[(i + 1) % len(c)]))

    # 소유권 노트 — 멤버 이름 -> (owns)/(observes). 스킬의 "이중 인코딩".
    own_note = defaultdict(dict)
    for e in edges:
        if e.get("label") and e["kind"] in ("composition", "aggregation"):
            own_note[e["from"]][e["label"]] = "(owns)" if e["kind"] == "composition" else "(observes)"

    by_mod = defaultdict(list)
    for i in shown:
        by_mod[nodes[i].get("module") or "?"].append(i)

    out, w = [], None
    w = out.append
    w(f"""/* 클래스 층 — 모듈 '{focus}' ↔ 그 이웃  ({g.get('language')}, {g.get('repo_commit')})
 *
 * 목표 : 모듈 층에서 빨갛게 뜬 순환이 **어느 클래스 때문인지** 를 본다.
 * 범위 : '{focus}' 의 클래스 전부 + 그와 직접 연결된 클래스만. 전이 확장 없음(C-9 R1 과 같은 정신).
 *        구조 {a.codegraph}
 *        살   {a.detail or '(없음 — 3분할 미적용)'}
 * 엣지 : 상속 남색 / 실현 검정점선 / 합성 보라다이아 / 집약 파랑빈다이아 / 의존 회색점선
 *        + 모듈 순환에 기여하는 간선은 굵은 빨강(P6)
 * 제외 : 초점 모듈과 연결되지 않은 클래스, 접근자 계열 메서드, 특수멤버.
 * 렌더 : dot -Tsvg X.dot -o X.svg
 */
digraph classes {{
  rankdir=BT;
  splines=spline;
  ranksep=0.9;
  nodesep=0.4;
  compound=true;
  bgcolor="white";
  node [shape=plaintext, fontname="Helvetica"];
  edge [fontname="Helvetica", fontsize=8];
""")

    for mod in sorted(by_mod, key=lambda m: (m != focus, m)):
        is_focus = mod == focus
        w(f'  subgraph "cluster_{esc(mod)}" {{')
        w(f'    label="{esch(mod)}"; labeljust="l"; fontname="Helvetica"; fontsize=10;')
        w('    style="rounded"; color="%s"; bgcolor="%s";'
          % (("#1f4e79", "#ffffff") if is_focus else ("#bbbbbb", "#fafafa")))
        for i in sorted(by_mod[mod], key=lambda x: nodes[x]["name"]):
            n = nodes[i]
            if is_focus:
                w(f'    "{esc(i)}" [label={node_html(n["name"], detail.get(n["name"]), own_note.get(i, {}))}];')
            else:
                # 스킬 Phase 2 — 범위 밖은 박스 + 이름만
                w(f'    "{esc(i)}" [shape=box, style="rounded,filled", fillcolor="#f0f0f0",'
                  f' color="#aaaaaa", fontsize=9, label="{esc(short(n["name"]))}"];')
        w("  }\n")

    # ── P2 + A1
    for kind, (style, _) in STYLE.items():
        group = [e for e in edges if e["kind"] == kind]
        if not group:
            continue
        constraint = "true" if kind in BACKBONE else "false"
        w(f'  // {kind}')
        w(f'  edge [{style}, penwidth=1.1, constraint={constraint}];')
        for e in sorted(group, key=lambda x: (x["from"], x["to"])):
            ma, mb = nodes[e["from"]].get("module"), nodes[e["to"]].get("module")
            red = (ma, mb) in cyc_pairs
            lab = e.get("label") or ""
            occ = e.get("occurrences", 1)
            if occ > 1:
                lab = f"{lab} ×{occ}" if lab else f"×{occ}"
            attrs = []
            if lab:
                attrs.append(f'label="{esc(lab)}"')
            if red:
                attrs.append(f'color="{C_CYCLE}", penwidth=2.6')
            s = f' [{", ".join(attrs)}]' if attrs else ""
            w(f'  "{esc(e["from"])}" -> "{esc(e["to"])}"{s};')
        w("")

    # ── 범례 — 실제로 그린 엣지 (스킬 규정)
    w('  subgraph cluster_legend {')
    w('    label="범례"; labeljust="l"; fontsize=10; color="#cccccc"; style="rounded";')
    w('    node [shape=plaintext, fontsize=8, height=0.18];')
    # ⚠ 범례 엣지는 constraint=true 다. 🔵 false 로 두면 랭크 제약이 없어 dot 이 B 를
    #   캔버스 끝까지 밀어 범례가 그래프보다 넓어진다(실측). 범례 노드는 본 그래프와
    #   연결되지 않으므로 여기서 constraint 를 켜도 레이아웃을 왜곡하지 않는다.
    keys = [k for k in STYLE if any(e["kind"] == k for e in edges)] + ["__cycle__"]
    for idx, k in enumerate(keys):
        w(f'    "lg{idx}a" [label="A"]; "lg{idx}b" [label="B"];')
    for idx, k in enumerate(keys):
        if k == "__cycle__":
            w(f'    "lg{idx}a" -> "lg{idx}b" [color="{C_CYCLE}", arrowhead=vee, penwidth=2.6,'
              ' label="모듈 순환에 기여", constraint=true];')
        else:
            w(f'    "lg{idx}a" -> "lg{idx}b" [{STYLE[k][0]}, label="{STYLE[k][1]}", constraint=true];')
    # ⚠ 행끼리는 쌓지 않는다. 🔵 스킬은 "수직으로 쌓아라" 고 하지만 그것은 rankdir 이
    #   가로일 때의 조언이다. 여기는 BT 라 각 행이 이미 세로 쌍(A 위 B)이고, 행까지 쌓으면
    #   범례가 7행 x 2랭크 = 14랭크가 되어 **캔버스 높이를 그래프보다 크게 만든다**(실측).
    #   행을 나란히 두면 2랭크로 끝난다.
    w("  }")
    w("}")

    base = a.out or os.path.join(os.path.dirname(os.path.abspath(a.codegraph)), f"{focus}-classes")
    os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
    open(base + ".dot", "w", encoding="utf-8").write("\n".join(out))
    for fmt, extra in (("svg", []), ("png", ["-Gdpi=140"])):
        r = subprocess.run(["dot", f"-T{fmt}"] + extra + [base + ".dot", "-o", f"{base}.{fmt}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"dot -T{fmt} 실패:\n{r.stderr}", file=sys.stderr)
            return 1

    red = sum(1 for e in edges
              if (nodes[e["from"]].get("module"), nodes[e["to"]].get("module")) in cyc_pairs)
    print(f"{base}.svg / .png / .dot")
    print(f"  초점 '{focus}' 클래스 {len(inside)} / 표시 노드 {len(shown)} / 간선 {len(edges)}")
    print(f"  이웃 모듈 {len(by_mod) - 1}개 — " + ", ".join(sorted(m for m in by_mod if m != focus)))
    print(f"  모듈 순환에 기여하는 클래스 간선(빨강) {red}개")
    kc = defaultdict(int)
    for e in edges:
        kc[e["kind"]] += 1
    print("  간선 종류 — " + " · ".join(f"{k} {v}" for k, v in sorted(kc.items(), key=lambda x: -x[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
