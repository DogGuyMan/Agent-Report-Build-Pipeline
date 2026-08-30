#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='facts.py']"/>
# 코드 지도에서 사람이 읽는 사실 표와 중요도 순위를 뽑는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""facts.py — codegraph.json 에서 deep-wiki 주입물(facts/*.md + ranking.json)을 만든다.

  ranking.json   중요도(PageRank) + 변경 hotspot(git log)
  facts/*.md     모듈·클래스·외부·진입점 사실 표

표는 전량을 낸다. 상한을 두는 곳은 표에 명시하고 총량을 함께 적는다.
인용 형식은 deep-wiki 로컬 규격 `(path:line)` 이다 — 위키가 그대로 옮겨 적어야 L3 가 잴 수 있다.

  facts.py <codegraph.json> --repo <저장소> [--detail <roslyn-dump.json>] [-o <출력디렉토리>]

--detail 은 C# 전용이다. 진입점 재료(unity.is_monobehaviour 등)는 codegraph.json 에 없고
roslyn-dump.json 에만 있다.
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from typing import NotRequired, TypedDict

import networkx as nx

HOTSPOT_TOP = 30   # hotspot 표의 표시 상한. 전체 수는 함께 적는다(no silent caps).


# ── 이 파일이 읽고 쓰는 사전의 모양.
#    `from` 이 파이썬 예약어라 간선만 함수 꼴 TypedDict 문법을 쓴다.
#    ⚠ networkx 의 `DiGraph` 는 실행 시각에 첨자를 받지 못한다 — 서명에서는 따옴표로 감싼다.
GraphNode = TypedDict("GraphNode", {
    "id": str,
    "name": str,
    "kind": str,
    "module": NotRequired[str],
    "file": NotRequired[str],
    "line": NotRequired[int],
    "collapsed_from": NotRequired[list[str]],
})
GraphEdge = TypedDict("GraphEdge", {"from": str, "to": str, "occurrences": NotRequired[int]})


# <include file="machine/comments.xml" path="//term[@id='machine.facts.GraphModule']"/>
# codegraph.json 안에서 모듈 하나가 어떤 모양인지 정의하는 타입. 모듈 이름과 그 모듈이 의존하는 다른 모듈들의 이름 목록을 담는다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.CodeGraph
class GraphModule(TypedDict):
    id: str
    depends_on: list[str]


# <include file="machine/comments.xml" path="//term[@id='machine.facts.CodeGraph']"/>
# normalize.py 가 만든 codegraph.json 중에서 facts.py 가 실제로 읽어 쓰는 부분만 골라 정의한 딕셔너리 틀이다.
# 쓰는 것: machine.facts.GraphNode, machine.facts.GraphEdge, machine.facts.GraphModule · 쓰이는 곳: 없음
class CodeGraph(TypedDict):
    """`normalize.py` 가 낸 codegraph.json 중 이 파일이 실제로 읽는 부분만."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    modules: list[GraphModule]
    language: NotRequired[str]
    repo_commit: NotRequired[str]


# <include file="machine/comments.xml" path="//term[@id='machine.facts.HotspotStat']"/>
# git 이력에서 파일 하나가 얼마나 자주, 얼마나 많이 바뀌었는지를 담는 자료 모양.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.HotspotRow
class HotspotStat(TypedDict):
    """git log 에서 센 파일 하나의 변경량."""
    commits: int
    added: int
    deleted: int


# <include file="machine/comments.xml" path="//term[@id='machine.facts.HotspotRow']"/>
# HotspotStat(커밋 수·증감 줄수)에 그 값이 어느 파일·어느 모듈 것인지를 더한 딕셔너리 틀이다. ranking.json 에 그대로 실린다.
# 쓰는 것: machine.facts.HotspotStat · 쓰이는 곳: 없음
class HotspotRow(HotspotStat):
    """변경량에 "어느 파일 · 어느 모듈" 을 더한 것. ranking.json 에 실린다."""
    file: str
    module: str | None


# <include file="machine/comments.xml" path="//term[@id='machine.facts.ClassRow']"/>
# 1차 클래스 하나에 대한 사실 행 하나의 모양. build 함수가 만들고 classes.md 등 표 여러 개가 이걸 읽어서 쓴다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.Ranking
class ClassRow(TypedDict):
    """1차 클래스 하나의 사실 행. `build` 가 내고 표 넷이 쓴다."""
    name: str
    kind: str
    module: str | None
    file: str | None
    line: int | None
    pagerank: float
    in_deg: int
    out_deg: int
    ext_touch: int


# <include file="machine/comments.xml" path="//term[@id='machine.facts.ModuleRow']"/>
# ranking.json 에 실리는 모듈 하나의 요약 정보 모양.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.Ranking
class ModuleRow(TypedDict):
    id: str
    classes: int
    pagerank_sum: float
    in_cycle: bool


# <include file="machine/comments.xml" path="//term[@id='machine.facts.HotspotBlock']"/>
# ranking.json 안에 들어갈 hotspot(변경 많은 파일) 정보 한 뭉치의 모양을 정의하는 딕셔너리 틀이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.Ranking
class HotspotBlock(TypedDict):
    note: str
    available: bool
    code_files: list[HotspotRow]
    total_tracked_in_log: int


# <include file="machine/comments.xml" path="//term[@id='machine.facts.Ranking']"/>
# ranking.json 파일 전체의 모양을 정의하는 자료형이다.
# 쓰는 것: machine.facts.HotspotBlock, machine.facts.ModuleRow, machine.facts.ClassRow · 쓰이는 곳: 없음
class Ranking(TypedDict):
    """ranking.json 전체."""
    language: str
    repo_commit: str
    generated_from: str
    pagerank_note: str
    classes: list[ClassRow]
    modules: list[ModuleRow]
    hotspot: HotspotBlock


# <include file="machine/comments.xml" path="//term[@id='machine.facts.RoslynType']"/>
# C# 전용 --detail 옵션으로 받는 roslyn-dump.json 안에서 타입(클래스) 하나가 어떤 모양인지 정의하는 타입.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.RoslynDump
class RoslynType(TypedDict):
    """`--detail` 로 받는 roslyn-dump.json 의 타입 하나 (C# 전용)."""
    name: str
    file: str
    line: int
    unity: NotRequired[dict[str, bool]]


# <include file="machine/comments.xml" path="//term[@id='machine.facts.RoslynDump']"/>
# --detail 옵션으로 받는 roslyn-dump.json(C# 전용) 파일 전체의 모양을 정의하는 딕셔너리 틀이다.
# 쓰는 것: machine.facts.RoslynType · 쓰이는 곳: 없음
class RoslynDump(TypedDict):
    types: list[RoslynType]


# <include file="machine/comments.xml" path="//term[@id='machine.facts.sh']"/>
# 바깥 셸 명령을 실행하고 성공했을 때만 결과를 돌려주는 도우미 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.collect_hotspot
def sh(cmd: list[str], cwd: str) -> str | None:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


# <include file="machine/comments.xml" path="//term[@id='machine.facts.collect_hotspot']"/>
# 파일마다 git 이력에서 커밋 몇 번 건드려졌는지, 줄이 얼마나 늘고 줄었는지를 세는 함수다. codegraph.json 이 아니라 git log 자체에서 정보를 얻는다.
# 쓰는 것: machine.facts.sh · 쓰이는 곳: machine.facts.main
# ── hotspot 은 codegraph 가 아니라 git log 에서 온다.
def collect_hotspot(repo: str) -> dict[str, HotspotStat] | None:
    """파일별 커밋 수·증감 줄수. 이름변경(old => new)은 새 경로로 귀속시킨다(단순 규칙)."""
    raw = sh(["git", "log", "--numstat", "--format=%H"], repo)
    if raw is None:
        return None
    files: defaultdict[str, HotspotStat] = defaultdict(
        lambda: {"commits": 0, "added": 0, "deleted": 0})
    seen_in_commit: set[str] = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:                      # 커밋 해시 줄
            seen_in_commit = set()
            continue
        a, d, path = parts
        if "=>" in path:                          # rename: "old => new" 또는 "dir/{old => new}/f"
            if "{" in path:
                pre, rest = path.split("{", 1)
                inside, post = rest.split("}", 1)
                path = pre + inside.split(" => ")[-1] + post
                path = path.replace("//", "/")
            else:
                path = path.split(" => ")[-1]
        rec = files[path]
        if path not in seen_in_commit:
            rec["commits"] += 1
            seen_in_commit.add(path)
        if a.isdigit():
            rec["added"] += int(a)
        if d.isdigit():
            rec["deleted"] += int(d)
    return dict(files)


# <include file="machine/comments.xml" path="//term[@id='machine.facts.build']"/>
# 코드 지도를 읽어서 각 클래스가 얼마나 중요한지(PageRank)와 모듈 사이에 순환 의존이 있는지를 계산하는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.facts.main
def build(g: CodeGraph) -> tuple[list[ClassRow], "nx.DiGraph[str]", list[list[str]], set[str]]:
    nodes = {n["id"]: n for n in g["nodes"]}
    first = {i: n for i, n in nodes.items() if n["kind"] != "external"}

    # ── PageRank — 1차 클래스 그래프에서만 잰다. 외부 노드를 넣으면 R3 섬의 단방향 간선이
    #    rank 를 전부 빨아들인다. 가중치는 occurrences 다.
    G: nx.DiGraph[str] = nx.DiGraph()
    G.add_nodes_from(first)
    ext_touch: Counter[str] = Counter()
    for e in g["edges"]:
        s, d = e["from"], e["to"]
        if s in first and d in first:
            w = e.get("occurrences", 1)
            if G.has_edge(s, d):
                G[s][d]["weight"] += w
            else:
                G.add_edge(s, d, weight=w)
        elif s in first:
            ext_touch[s] += e.get("occurrences", 1)
    pr: dict[str, float] = nx.pagerank(G, weight="weight") if G.number_of_nodes() else {}

    # ── 모듈 층 — 렌더러와 같은 계산(순환 포함)
    MG: nx.DiGraph[str] = nx.DiGraph()
    for m in g["modules"]:
        MG.add_node(m["id"])
        for d in m["depends_on"]:
            MG.add_edge(m["id"], d)
    cycles = list(nx.simple_cycles(MG))
    cyc_mods = {x for c in cycles for x in c}

    rows: list[ClassRow] = []
    for i, n in first.items():
        rows.append({
            "name": n["name"], "kind": n["kind"], "module": n.get("module"),
            "file": n.get("file"), "line": n.get("line"),
            "pagerank": round(pr.get(i, 0.0), 6),
            "in_deg": G.in_degree(i) if i in G else 0,
            "out_deg": G.out_degree(i) if i in G else 0,
            "ext_touch": ext_touch.get(i, 0),
        })
    rows.sort(key=lambda r: -r["pagerank"])
    return rows, MG, cycles, cyc_mods


# <include file="machine/comments.xml" path="//term[@id='machine.facts.cite']"/>
# 클래스 사실 행 하나를 사람이 읽는 '(파일:줄)' 인용 문자열로 바꾸는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def cite(r: ClassRow) -> str:
    return f"({r['file']}:{r['line']})" if r.get("file") else "(위치 없음)"


HEAD_NOTE = """> **기계 생성 — 손으로 고치지 말 것.** `machine/facts.py` 가 `codegraph.json` 에서 만들었다.
> 인용은 deep-wiki 로컬 규격 `(path:line)` 이다 — 위키가 그대로 옮겨 적으면 검증기 L3 가 잰다.
"""


# <include file="machine/comments.xml" path="//term[@id='machine.facts.main']"/>
# facts 도구를 터미널에서 실행할 때 제일 먼저 불리는 진입점 함수다.
# 쓰는 것: machine.facts.build, machine.facts.collect_hotspot · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--detail", help="C# 전용 — roslyn-dump.json (unity 진입점 재료)")
    ap.add_argument("-o", "--out", help="출력 디렉토리. 기본: codegraph.json 옆")
    a = ap.parse_args()

    g: CodeGraph = json.load(open(a.codegraph, encoding="utf-8"))
    lang = g.get("language", "?")
    commit = g.get("repo_commit", "?")
    base = a.out or os.path.dirname(os.path.abspath(a.codegraph))
    fdir = os.path.join(base, "facts")
    os.makedirs(fdir, exist_ok=True)

    rows, MG, cycles, cyc_mods = build(g)
    hotspot = collect_hotspot(a.repo)

    node_files = {r["file"] for r in rows if r["file"]}
    file_mod = {r["file"]: r["module"] for r in rows if r["file"]}

    # ── ranking.json
    mod_pr: defaultdict[str, float] = defaultdict(float)
    mod_cnt: Counter[str] = Counter()
    for r in rows:
        if r["module"]:
            mod_pr[r["module"]] += r["pagerank"]
            mod_cnt[r["module"]] += 1
    hs_code: list[HotspotRow] = []
    if hotspot:
        for f, v in hotspot.items():
            if f in node_files:
                hs_code.append({"file": f, "module": file_mod.get(f), **v})
        hs_code.sort(key=lambda x: -x["commits"])
    ranking: Ranking = {
        "language": lang, "repo_commit": commit,
        "generated_from": os.path.basename(a.codegraph),
        "pagerank_note": "1차 클래스 그래프만. 외부 노드는 제외 — 넣으면 R3 섬이 rank 를 흡수한다",
        "classes": rows,
        "modules": sorted(
            [{"id": m, "classes": mod_cnt[m], "pagerank_sum": round(mod_pr[m], 6),
              "in_cycle": m in cyc_mods} for m in mod_cnt],
            key=lambda x: -x["pagerank_sum"]),
        "hotspot": {
            "note": "git log --numstat 전 이력. 이름변경은 새 경로 귀속(단순 규칙)",
            "available": hotspot is not None,
            "code_files": hs_code,                     # codegraph 노드가 있는 파일만
            "total_tracked_in_log": len(hotspot) if hotspot else 0,
        },
    }
    rpath = os.path.join(base, "ranking.json")
    json.dump(ranking, open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ── facts/modules.md
    lines = [f"# 모듈 사실 표 — {lang} ({commit})", "", HEAD_NOTE]
    lines.append(f"모듈 {MG.number_of_nodes()}개 / 모듈 간 의존 {MG.number_of_edges()}개 / 순환 {len(cycles)}개")
    lines.append("")
    lines.append("| 모듈 | 클래스 | PageRank 합 | 의존 대상 | 순환 참여 |")
    lines.append("|---|---|---|---|---|")
    for m in ranking["modules"]:
        deps = ", ".join(sorted(MG.successors(m["id"]))) or "—"
        lines.append(f"| {m['id']} | {m['classes']} | {m['pagerank_sum']} | {deps} | "
                 f"{'⚠ 예' if m['in_cycle'] else '아니오'} |")
    lines.append("")
    lines.append("## 순환 — 전량")
    lines.append("")
    if cycles:
        for c in sorted(cycles, key=len):
            lines.append("- `" + " -> ".join(c) + " -> " + c[0] + "`")
        lines.append("")
        lines.append("⚠ 순환의 허용/위반 판정은 기계가 하지 않는다 — `codegraph-rules.toml` 에 사람이 적는다.")
    else:
        lines.append("- 없음 (모듈 의존이 단일 방향)")
    open(os.path.join(fdir, "modules.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ── facts/classes.md — 전량, PageRank 내림차순
    lines = [f"# 클래스 사실 표 — {lang} ({commit})", "", HEAD_NOTE]
    lines.append(f"1차 클래스 {len(rows)}개 전량. PageRank 내림차순 — 위쪽이 \"많이 의존받는(기반)\" 쪽이다.")
    lines.append("")
    lines.append("**서술 열(C-17)** — `본문` 은 위키 본문에서 서술할 대상, `목록` 은 간선이 0이라")
    lines.append("본문에서 빼고 이 표에만 남기는 대상이다. **생략하되 숨기지 않는다.**")
    narr = sum(1 for r in rows if r["in_deg"] or r["out_deg"])
    lines.append(f"본문 {narr} / 목록 {len(rows) - narr}")
    lines.append("")
    lines.append("| # | 서술 | 클래스 | 종류 | 모듈 | PageRank | 받는← | 주는→ | 외부접촉 | 선언 위치 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        tag = "본문" if (r["in_deg"] or r["out_deg"]) else "목록"
        lines.append(f"| {i} | {tag} | {r['name']} | {r['kind']} | {r['module']} | {r['pagerank']} "
                 f"| {r['in_deg']} | {r['out_deg']} | {r['ext_touch']} | {cite(r)} |")
    open(os.path.join(fdir, "classes.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ── facts/external.md — C-9 접힘표
    lines = [f"# 외부 의존 사실 표 — {lang} ({commit})", "", HEAD_NOTE]
    lines.append("C-9 적용 후의 외부 노드다 — 전이 확장 없음(R1), 패키지/라이브러리 하나 = 노드 하나(R2).")
    lines.append("")
    lines.append("| 외부 노드 | 접촉 간선 | 접힌 타입 수 | 대표 |")
    lines.append("|---|---|---|---|")
    nodes = {n["id"]: n for n in g["nodes"]}
    ext_edge: Counter[str] = Counter()
    for e in g["edges"]:
        if nodes[e["to"]]["kind"] == "external":
            ext_edge[e["to"]] += e.get("occurrences", 1)
    for nid, cnt in ext_edge.most_common():
        n = nodes[nid]
        cf = n.get("collapsed_from", [])
        head = ", ".join(sorted(cf, key=len)[:3]) + (f" 외 {len(cf)-3}" if len(cf) > 3 else "")
        lines.append(f"| {n['name']} | {cnt} | {len(cf)} | {head} |")
    open(os.path.join(fdir, "external.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ── facts/entrypoints.md — 언어별. 판정 없이 표시만.
    lines = [f"# 진입점 재료 — {lang} ({commit})", "", HEAD_NOTE]
    lines.append("⚠ **이 표는 후보이지 판정이 아니다.** \"이것이 진입점\" 확정은 `codegraph-rules.toml` 에 사람이 적는다.")
    lines.append("")
    if lang == "csharp" and a.detail:
        dump: RoslynDump = json.load(open(a.detail, encoding="utf-8"))
        mono: list[RoslynType] = []
        so: list[RoslynType] = []
        for t in dump["types"]:
            u: dict[str, bool] = t.get("unity") or {}
            if u.get("is_monobehaviour"):
                mono.append(t)
            if u.get("is_scriptable_object"):
                so.append(t)
        lines.append(f"## MonoBehaviour 전이 파생 — {len(mono)}개 (Roslyn 판정. 정규식 계수 5는 오답이었다)")
        lines.append("")
        lines.append("엔진이 리플렉션으로 부르므로 **코드에 호출자가 없다** — 호출 그래프에서 고아로 보인다.")
        lines.append("")
        lines.append("| 타입 | 선언 위치 |")
        lines.append("|---|---|")
        for t in sorted(mono, key=lambda x: x["name"]):
            lines.append(f"| {t['name']} | ({t['file']}:{t['line']}) |")
        lines.append("")
        lines.append(f"## ScriptableObject 파생 — {len(so)}개 (에디터에서 자산으로 생성된다)")
        lines.append("")
        lines.append("| 타입 | 선언 위치 |")
        lines.append("|---|---|")
        for t in sorted(so, key=lambda x: x["name"]):
            lines.append(f"| {t['name']} | ({t['file']}:{t['line']}) |")
        lines.append("")
        lines.append("⚠ 프리팹·씬 YAML 의 `m_Script` GUID 배선(사용자 자산 프리팹 16 + 씬 6)은 이 표 밖이다 —")
        lines.append("근거가 `file:line` 이 아니라 `file:GUID` 라 L3 대상이 아니다(관찰 보고서 D절).")
    elif lang == "cpp":
        apps = sorted({r["module"] for r in rows if r["module"] and r["module"].startswith("apps/")})
        lines.append("## 응용 모듈 (main 이 사는 곳)")
        lines.append("")
        for m in apps:
            lines.append(f"- `{m}`")
        lines.append("")
        lines.append("⚠ `main` 함수 자체는 codegraph 에 없다 — clang-uml 은 클래스 층만 낸다.")
        lines.append("함수 층 진입점 식별은 Track C §1 17(패턴 + 수동)이고 `codegraph-rules.toml` 몫이다.")
    else:
        lines.append("(이 언어의 진입점 재료 없음 — C# 은 --detail 로 roslyn-dump.json 을 줘야 한다)")
    open(os.path.join(fdir, "entrypoints.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ── facts/hotspot.md
    lines = [f"# 변경 hotspot — {lang} ({commit})", "", HEAD_NOTE]
    if hotspot is None:
        lines.append("⚠ git log 를 읽지 못했다 — hotspot 미확인.")
    else:
        lines.append(f"git 전 이력 기준. 추적 파일 {len(hotspot)}개 중 **codegraph 노드가 있는 코드 파일 "
                 f"{len(hs_code)}개**만 표에 올린다. 표시는 상위 {HOTSPOT_TOP}개, 전량은 `ranking.json`.")
        lines.append("")
        lines.append("| # | 파일 | 모듈 | 커밋 수 | +줄 | -줄 |")
        lines.append("|---|---|---|---|---|---|")
        for i, h in enumerate(hs_code[:HOTSPOT_TOP], 1):
            lines.append(f"| {i} | {h['file']} | {h['module']} | {h['commits']} | {h['added']} | {h['deleted']} |")
    open(os.path.join(fdir, "hotspot.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"{rpath}")
    print(f"{fdir}/ — modules.md · classes.md · external.md · entrypoints.md · hotspot.md")
    print(f"  클래스 {len(rows)} / 모듈 {MG.number_of_nodes()} / 순환 {len(cycles)}"
          f" / hotspot 코드파일 {len(hs_code) if hotspot else '미확인'}")
    top = rows[:5]
    print("  PageRank 상위:", " · ".join(f"{r['name'].split('::')[-1].split('.')[-1]}({r['pagerank']})" for r in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
