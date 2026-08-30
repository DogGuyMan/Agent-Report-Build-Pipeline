#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='survey_plan.py']"/>
# 전수조사를 어떤 순서로 어떻게 쪼개 돌릴지 계획하는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""survey_plan.py — 전수조사 배치 계획.

의존 대상이 없는 것부터 한 겹씩 올라가는 순서를 계산하고 층을 배치로 나눈다.
같은 층끼리는 서로 의존하지 않으므로 병렬로 읽어도 안전하다.

## ⚠ 간선의 방향 — 뒤집어 읽으면 정렬이 정반대가 된다

`codegraph.json` 의 간선 `{"from": A, "to": B}` 는 **"A 가 B 에 의존한다"** 는 뜻이다.
레코드의 `uses[].to`(A 가 부르는 대상)가 그대로 `to` 가 된다.

| 차수 | 뜻 | 층 |
|---|---|---|
| `out_deg` | **이것이 끌어오는 개수** (내가 남에게 의존) | 0이면 **층0** — 여기서 시작한다 |
| `in_deg`  | **이것을 끌어가는 개수** (남이 나에게 의존) | 0이면 진입점 — **맨 나중**에 읽는다 |

`in_deg` 가 0인 것부터 시작하면 top-down 이 되어, `main` 이 부르는 것들이 아직 안 읽힌 채로
`main` 의 뜻을 적게 된다.

입력은 `prep` 이 낸 `codegraph.json` 이다.

  survey_plan.py <codegraph.json> [--target 8] [--only-files a.py,b.py] [-o survey-plan.json]
"""
import argparse
import collections
import json
import os
import sys
from collections.abc import Collection, Iterable, Mapping
from typing import NotRequired, TypedDict, cast

import networkx as nx

# ── 이 파일이 읽고 쓰는 사전의 모양.
#    `from` 이 파이썬 예약어라 간선만 함수 꼴 TypedDict 문법을 쓴다.
GraphNode = TypedDict("GraphNode", {
    "id": str,
    "name": NotRequired[str],
    "kind": NotRequired[str],
    "file": NotRequired[str],
    "line": NotRequired[int],
})
GraphEdge = TypedDict("GraphEdge", {"from": str, "to": str})


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.CodeGraph']"/>
# prep 단계가 만든 codegraph.json 파일의 내용 중 이 파일이 실제로 쓰는 부분(nodes, edges)만 담는 타입 정의다. 데이터를 담는 상자일 뿐 동작하는 코드는 없다.
# 쓰는 것: machine.survey_plan.GraphNode, machine.survey_plan.GraphEdge · 쓰이는 곳: 없음
class CodeGraph(TypedDict):
    """`prep` 이 낸 codegraph.json 중 이 파일이 실제로 읽는 부분만."""
    nodes: list[GraphNode]
    edges: NotRequired[list[GraphEdge]]


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.PackedBatch']"/>
# pack 함수가 만들어내는, 아직 배치 번호나 상세 심볼 정보가 붙지 않은 중간 단계의 묶음을 나타내는 타입이다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
class PackedBatch(TypedDict):
    """`pack` 이 내는 중간 묶음. 아직 배치 id 도 심볼 레코드도 붙지 않았다."""
    files: list[str]
    symbols: list[str]


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.PlanSymbol']"/>
# 최종 계획(survey-plan.json)에 들어가는 심볼 하나의 정보를 담는 타입이다. 이 심볼이 무엇이고, 어디에 있고, 무엇에 의존하는지를 담는다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.survey_plan.PlanBatch
class PlanSymbol(TypedDict):
    id: str
    name: str | None
    file: str | None
    line: int | None
    kind: str | None
    in_cycle: bool
    depends_on: list[str]


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.PlanBatch']"/>
# 전수조사 계획서 안에서 배치(한 세션이 맡을 몫) 하나의 모양을 정해 둔 타입 사전이다.
# 쓰는 것: machine.survey_plan.PlanSymbol · 쓰이는 곳: machine.survey_plan.PlanLayer, runner.run_mode1.dep_excerpt, runner.test_run_mode1._배치
class PlanBatch(TypedDict):
    id: str
    files: list[str]
    symbols: list[PlanSymbol]


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.PlanLayer']"/>
# 전수조사 계획에서 층(layer) 하나를 나타내는 자료 모양이다. 딕셔너리 안에 어떤 값들이 들어가야 하는지 정하는 타입 틀(TypedDict)일 뿐, 실제로 동작하는 코드는 아니다.
# 쓰는 것: machine.survey_plan.PlanBatch · 쓰이는 곳: machine.survey_plan.SurveyPlan
class PlanLayer(TypedDict):
    """심볼 층과 맨 끝 비노드 층이 한 목록에 섞여 있다.

    비노드 층만 `kind` 와 `note` 를 갖고 `file_count` 는 갖지 않는다 — 그래서 셋이 선택 항목이다.
    """
    level: int
    symbol_count: int | None
    batches: list[PlanBatch]
    file_count: NotRequired[int]
    kind: NotRequired[str]
    note: NotRequired[str]


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.PlanTotals']"/>
# 계획 전체를 요약하는 합계 숫자들을 담는 타입이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.survey_plan.SurveyPlan
class PlanTotals(TypedDict):
    symbols: int
    edges: int
    levels: int
    cyclic_symbols: int


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.SurveyPlan']"/>
# 전수조사를 어떻게 나눠 돌릴지 계획한 결과 전체를 담는 자료형이다.
# 쓰는 것: machine.survey_plan.PlanLayer, machine.survey_plan.PlanTotals · 쓰이는 곳: runner.run_mode1.plan_summary, runner.run_mode1.symbol_layers
class SurveyPlan(TypedDict):
    target: int
    layers: list[PlanLayer]
    totals: PlanTotals


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.layer_of']"/>
# 각 심볼이 그래프에서 몇 번째 층에 있는지 계산하는 함수다. 아무것도 의존하지 않으면 층0, 의존하는 것이 있으면 그중 가장 깊은 층보다 1 더 깊은 층이다.
# 쓰는 것: networkx · 쓰이는 곳: machine.survey_plan.plan, machine.test_survey_plan.test_out_deg_가_아니라_위상_깊이다, machine.test_survey_plan.test_간선은_from_이_의존하는_쪽이다, machine.test_survey_plan.test_고립_노드는_층0, machine.test_survey_plan.test_순환은_한_덩어리로_접힌다 (+2)
def layer_of(first: Collection[str],
             edges: Iterable[tuple[str, str]]) -> tuple[dict[str, int], dict[str, bool]]:
    """의존 대상이 없으면 층0, 아니면 1 + 의존 대상들의 최대 층.

    `edges` 의 원소는 `(A, B)` = **"A 가 B 에 의존"** 이다(파일 머리말의 방향 표).
    그래서 `G.successors(n)` 이 "n 이 의존하는 것들" 이고, 그것이 비면 층0 이다.
    의존을 몇 개 갖는지(out_deg)로 정렬하면 안 된다 — 의존 하나만 가져도 그 하나가 3층이면 4층이다.

    순환이 있으면 위상 깊이가 정의되지 않으므로 **강결합 성분(SCC)으로 접어** DAG 로 만든 뒤 센다.
    같은 순환에 든 심볼은 같은 층이 되어 같은 배치 후보가 된다.
    """
    G: nx.DiGraph[str] = nx.DiGraph()
    G.add_nodes_from(first)
    for s, d in edges:
        if s in first and d in first and s != d:
            G.add_edge(s, d)
    C = nx.condensation(G)                 # SCC 를 접은 DAG. C.graph["mapping"] 이 노드->성분
    lv: dict[int, int] = {}
    for c in reversed(list(nx.topological_sort(C))):   # 뒤에서부터 = 의존 대상이 먼저
        succ = list(C.successors(c))
        lv[c] = 0 if not succ else 1 + max(lv[s] for s in succ)
    # networkx 는 성분 표를 타입이 없는 `graph` 사전(dict[str, Any])에 담아 돌려준다 — 여기서만 좁힌다.
    m = cast(dict[str, int], C.graph["mapping"])
    size = collections.Counter(m.values())
    return {n: lv[m[n]] for n in G}, {n: size[m[n]] > 1 for n in G}


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.pack']"/>
# 같은 층에 속한 심볼들을 파일 단위로 묶어서, 너무 많지 않은 크기의 묶음(배치) 여러 개로 나누는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.survey_plan.plan, machine.test_survey_plan.test_같은_파일은_한_배치에, machine.test_survey_plan.test_큰_파일은_초과를_허용한다
def pack(members: Iterable[str], file_of: Mapping[str, str | None],
         target: int) -> list[PackedBatch]:
    """같은 파일의 같은 층 심볼은 **한 배치에** 몰아넣는다 — 층 안 중복 통독을 0으로 만든다.

    파일 하나가 target 을 넘으면 그 파일만으로 배치 하나가 된다 — target 은 상한이 아니다.
    파일명 정렬 뒤 그리디라 같은 입력이면 같은 출력이다.
    """
    byfile: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for n in members:
        byfile[file_of.get(n) or ""].append(n)
    out: list[PackedBatch] = []
    cur: list[str] = []
    curf: list[str] = []
    for f in sorted(byfile):
        syms = sorted(byfile[f])
        if cur and len(cur) + len(syms) > target:
            out.append({"files": curf, "symbols": cur})
            cur, curf = [], []
        cur += syms
        curf.append(f)
    if cur:
        out.append({"files": curf, "symbols": cur})
    return out


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.plan']"/>
# 코드 지도(codegraph.json) 전체를 받아서, 어떤 순서(층)로 어떻게 묶어(배치) 조사할지 계획표를 만드는 함수다.
# 쓰는 것: machine.survey_plan.layer_of, machine.survey_plan.pack · 쓰이는 곳: machine.survey_plan.main, machine.test_survey_plan.test_external_은_제외, machine.test_survey_plan.test_결정론, machine.test_survey_plan.test_마지막은_비노드_층, machine.test_survey_plan.test_배치는_자기_심볼의_의존_대상을_들고_있다 (+5)
def plan(cg: CodeGraph, target: int = 8,
         only_files: Iterable[str] | None = None) -> SurveyPlan:
    """코드 지도 -> 층 · 배치 계획.

    `only_files` 는 증분 재조사용이다 — `warmup.blast_radius` 가 낸 파일 목록을 주면
    그 파일의 심볼만 남긴다. 층 번호는 **전체 그래프 기준으로 매긴 뒤** 거른다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다.
    """
    nodes = {n["id"]: n for n in cg["nodes"]}
    first = {i: n for i, n in nodes.items() if n.get("kind") != "external"}
    edges = [(e["from"], e["to"]) for e in cg.get("edges", [])]
    lv, in_cycle = layer_of(first, edges)
    file_of = {i: n.get("file") for i, n in first.items()}

    keep = set(first)
    if only_files is not None:
        want = set(only_files)
        keep = {i for i in first if file_of.get(i) in want}

    bylv: collections.defaultdict[int, list[str]] = collections.defaultdict(list)
    for n in keep:
        bylv[lv[n]].append(n)

    layers: list[PlanLayer] = []
    for k in sorted(bylv):
        bs = pack(bylv[k], file_of, target)
        layers.append({
            "level": k,
            "symbol_count": len(bylv[k]),
            "file_count": len({file_of.get(n) for n in bylv[k] if file_of.get(n)}),
            "batches": [
                {"id": "L%d-B%02d" % (k, i),
                 # 빈 이름을 거른다 — file 이 없는 노드가 "" 로 묶여 들어온다.
                 # 그대로 두면 배치 프롬프트가 빈 경로로 통독 캐시를 부르라고 시킨다.
                 "files": [f for f in b["files"] if f],
                 "symbols": [{"id": s, "name": first[s].get("name"), "file": file_of.get(s),
                              "line": first[s].get("line"), "kind": first[s].get("kind"),
                              "in_cycle": in_cycle.get(s, False),
                              "depends_on": sorted({d for (o, d) in edges
                                                    if o == s and d in first and d != s})}
                             for s in b["symbols"]]}
                for i, b in enumerate(bs)],
        })

    # K5 — 그래프 노드가 아닌 용어는 맨 마지막 별도 층. `symbol_count` 가 None 인 층이 이것이다.
    last = (max(bylv) + 1) if bylv else 0
    layers.append({
        "level": last, "kind": "non-node", "symbol_count": None, "batches": [],
        "note": "file · module · artifact · key · concept. 심볼 층이 전부 끝난 뒤 한 세션으로 돈다. "
                "파일 레코드는 그 파일 안 심볼들의 완성 레코드를 재료로 쓴다.",
    })
    return {"target": target, "layers": layers,
            "totals": {"symbols": len(keep), "edges": len(edges), "levels": len(bylv),
                       "cyclic_symbols": sum(1 for n in keep if in_cycle.get(n))}}


# <include file="machine/comments.xml" path="//term[@id='machine.survey_plan.main']"/>
# 전수조사 계획을 만드는 명령줄 도구의 시작점이다.
# 쓰는 것: machine.survey_plan.plan · 쓰이는 곳: 없음
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="전수조사를 층과 배치로 나눈다.")
    ap.add_argument("codegraph", help="prep 이 낸 codegraph.json")
    ap.add_argument("--target", type=int, default=8, help="배치당 목표 심볼 수 (기본 8)")
    ap.add_argument("--only-files", help="증분 재조사. 쉼표로 나눈 파일 목록(warmup blast 의 출력)")
    ap.add_argument("-o", "--out", help="출력 경로. 기본은 codegraph.json 옆 survey-plan.json")
    a = ap.parse_args(argv)
    try:
        cg: CodeGraph = json.load(open(a.codegraph, encoding="utf-8"))
    except Exception as ex:
        print("에러 — codegraph.json 을 읽지 못했다: %s" % ex, file=sys.stderr)
        return 1
    p = plan(cg, a.target, a.only_files.split(",") if a.only_files else None)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.codegraph)), "survey-plan.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=1)
    print(out)
    print("  심볼 %d · 간선 %d · 층 %d · 순환에 든 심볼 %d"
          % (p["totals"]["symbols"], p["totals"]["edges"],
             p["totals"]["levels"], p["totals"]["cyclic_symbols"]))
    for L in p["layers"]:
        if L.get("kind") == "non-node":
            print("  층%d — 비노드 용어 (한 세션)" % L["level"])
        else:
            # 심볼 층은 위에서 file_count 를 반드시 넣지만 형 검사기가 그것을 볼 방법이 없다.
            print("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                  % (L["level"], L["symbol_count"], L["file_count"], len(L["batches"])))  # pyright: ignore[reportTypedDictNotRequiredAccess]
    return 0


if __name__ == "__main__":
    sys.exit(main())
