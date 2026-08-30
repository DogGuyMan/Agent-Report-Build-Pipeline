#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/survey_plan.py']"/>
# 전수조사를 어떤 순서로 어떻게 쪼개 돌릴지 계획하는 파일.
# 쓰는 것: survey-plan.json, networkx · 쓰이는 곳: run_mode1.main
"""survey_plan.py — 전수조사 배치 계획.

**왜 필요한가.** 심볼의 뜻은 그것이 의존하는 심볼의 뜻 위에 선다. 아무 순서로나 읽으면
아직 안 읽은 것을 가리키게 되고, 그 자리는 추론으로 메워진다. 그래서 **의존 대상이 없는 것부터**
한 겹씩 올라간다. 같은 층끼리는 서로 의존하지 않으므로 병렬로 읽어도 안전하다.

**이 파일은 판정하지 않는다.** 순서를 계산하고 배치를 나눌 뿐이다.

## ⚠ 간선의 방향 — 이것을 뒤집어 읽으면 정렬이 정반대가 된다

`codegraph.json` 의 간선 `{"from": A, "to": B}` 는 **"A 가 B 에 의존한다"** 는 뜻이다.
레코드의 `uses[].to`(A 가 부르는 대상)가 그대로 `to` 가 된다.
🔵 2026-08-30 이 저장소 실측 — 레코드 `uses` 105건이 **전부** `from=A, to=B` 로 들어 있었고
반대 방향은 0건이었다.

따라서:

| 차수 | 뜻 | 층 |
|---|---|---|
| `out_deg` | **이것이 끌어오는 개수** (내가 남에게 의존) | 0이면 **층0** — 여기서 시작한다 |
| `in_deg`  | **이것을 끌어가는 개수** (남이 나에게 의존) | 0이면 진입점 — **맨 나중**에 읽는다 |

🔵 실측 — 층0(110개)의 평균 `out_deg` 는 **0.00**, 층3(7개)은 **3.14** 다.
`in_deg` 가 0인 것들(`terms_db.main` · `normalize.main` 같은 진입점)은 층 3에 있다.

**`in_deg` 가 0인 것부터 시작하면 top-down 이 되어 정확히 이 도구가 막으려는 사고가 난다** —
`main` 이 부르는 것들이 아직 안 읽힌 채로 `main` 의 뜻을 적게 된다.

입력은 `prep` 이 이미 낸 `codegraph.json` 이다 — LLM 이 한 글자도 읽기 전에 존재한다.

  survey_plan.py <codegraph.json> [--target 8] [--only-files a.py,b.py] [-o survey-plan.json]
"""
import argparse
import collections
import json
import os
import sys

import networkx as nx


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.layer_of']"/>
# 노드마다 위상 깊이를 매긴다. 순환은 한 덩어리로 접는다.
# 쓰는 것: networkx · 쓰이는 곳: survey_plan.plan
def layer_of(first, edges):
    """의존 대상이 없으면 층0, 아니면 1 + 의존 대상들의 최대 층.

    `edges` 의 원소는 `(A, B)` = **"A 가 B 에 의존"** 이다(파일 머리말의 방향 표).
    그래서 `G.successors(n)` 이 "n 이 의존하는 것들" 이고, 그것이 비면 층0 이다.
    **의존을 몇 개 갖는지(out_deg)로 정렬하면 안 된다** — 의존 하나만 가져도 그 하나가
    3층이면 4층이다. 🔵 실측에서 out_deg 1 무리(31개) 안에 깊이 1·2·3·4 가 섞여 있었다.

    순환이 있으면 위상 깊이가 정의되지 않으므로 **강결합 성분(SCC)으로 접어** DAG 로 만든 뒤 센다.
    같은 순환에 든 심볼은 같은 층이 되어 같은 배치 후보가 된다 — 서로를 보며 함께 읽으라는 뜻이다.
    이 저장소 자신은 순환이 0개지만 C++ · C# 저장소에서는 흔하다.
    """
    G = nx.DiGraph()
    G.add_nodes_from(first)
    for s, d in edges:
        if s in first and d in first and s != d:
            G.add_edge(s, d)
    C = nx.condensation(G)                 # SCC 를 접은 DAG. C.graph["mapping"] 이 노드->성분
    lv = {}
    for c in reversed(list(nx.topological_sort(C))):   # 뒤에서부터 = 의존 대상이 먼저
        succ = list(C.successors(c))
        lv[c] = 0 if not succ else 1 + max(lv[s] for s in succ)
    m = C.graph["mapping"]
    size = collections.Counter(m.values())
    return {n: lv[m[n]] for n in G}, {n: size[m[n]] > 1 for n in G}


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.pack']"/>
# 한 층의 심볼을 파일이 쪼개지지 않게 목표 크기로 묶는다.
# 쓰는 것: 없음 · 쓰이는 곳: survey_plan.plan
def pack(members, file_of, target):
    """같은 파일의 같은 층 심볼은 **한 배치에** 몰아넣는다 — 층 안 중복 통독을 0으로 만든다.

    파일 하나가 target 을 넘으면 그 파일만으로 배치 하나가 된다(초과를 허용한다).
    쪼개면 그 파일을 두 세션이 각각 통독하게 되어 더 비싸기 때문이다.
    파일명 정렬 뒤 그리디라 같은 입력이면 같은 출력이다.
    """
    byfile = collections.defaultdict(list)
    for n in members:
        byfile[file_of.get(n) or ""].append(n)
    out, cur, curf = [], [], []
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.plan']"/>
# 코드 지도를 층과 배치로 나눈 계획을 만든다.
# 쓰는 것: survey_plan.layer_of, survey_plan.pack · 쓰이는 곳: run_mode1.main
def plan(cg, target=8, only_files=None):
    """코드 지도 -> 층 · 배치 계획.

    `only_files` 는 증분 재조사용이다 — `warmup.py` 의 `blast_radius` 가 낸 파일 목록을 주면
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

    bylv = collections.defaultdict(list)
    for n in keep:
        bylv[lv[n]].append(n)

    layers = []
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

    # K5 — 그래프 노드가 아닌 용어는 맨 마지막 별도 층. 심볼이 다 읽힌 뒤라야 정확해진다.
    last = (max(bylv) + 1) if bylv else 0
    layers.append({
        "level": last, "kind": "non-node", "symbol_count": None, "batches": [],
        "note": "file · module · artifact · key · concept. 심볼 층이 전부 끝난 뒤 한 세션으로 돈다. "
                "파일 레코드는 그 파일 안 심볼들의 완성 레코드를 재료로 쓴다.",
    })
    return {"target": target, "layers": layers,
            "totals": {"symbols": len(keep), "edges": len(edges), "levels": len(bylv),
                       "cyclic_symbols": sum(1 for n in keep if in_cycle.get(n))}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="전수조사를 층과 배치로 나눈다.")
    ap.add_argument("codegraph", help="prep 이 낸 codegraph.json")
    ap.add_argument("--target", type=int, default=8, help="배치당 목표 심볼 수 (기본 8)")
    ap.add_argument("--only-files", help="증분 재조사. 쉼표로 나눈 파일 목록(warmup blast 의 출력)")
    ap.add_argument("-o", "--out", help="출력 경로. 기본은 codegraph.json 옆 survey-plan.json")
    a = ap.parse_args(argv)
    try:
        cg = json.load(open(a.codegraph, encoding="utf-8"))
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
            print("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                  % (L["level"], L["symbol_count"], L["file_count"], len(L["batches"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
