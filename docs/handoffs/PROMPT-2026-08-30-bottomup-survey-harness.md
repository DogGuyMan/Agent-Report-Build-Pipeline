# Prompt — Mode 1 에이전트 단계 프롬프트 개조: Bottom-Up 층 병렬 (다른 Claude Code 에이전트용)

> 아래 ``` 블록을 새 세션에 **그대로** 붙여 넣는다. 자기완결적이다.
> 선택 참고(읽지 않아도 된다): `codegraph/CLAUDE.md` · `.agents/skills/codebase-terms-survey/SKILL.md`

```
[ROLE]
너는 report-builder(/Users/escatrgot/LLM-Tools/report-builder, branch main)의
**Mode 1 에이전트 단계 프롬프트 개조 담당**이다.

Mode 1 파이프라인은 다섯 칸이고 그중 LLM 이 도는 칸은 하나다:

    prep ──▶ agent ──▶ terms ──▶ build ──▶ check
    기계      LLM       기계      기계      기계

**너의 소관은 가운데 `agent` 칸 하나뿐이다.** 양옆의 기계 단계는 이미 결정론으로 돌고 있고
네가 건드릴 대상이 아니다. 네가 고치는 것은 **그 칸에 주입되는 프롬프트**다.

주입 지점은 문서가 아니라 코드다 — `codegraph/run_mode1.py:184` 의 `agent_prompt()` 가
헤드리스 `claude -p` 의 표준 입력으로 들어가는 글을 만든다(`run_mode1.py:362`).

목표: 그 한 세션 통짜 읽기를 **의존 위상 층 오름차순 + 층 안 병렬 배치**로 바꾼다.

[HARD RULES]
- **커밋 금지.** `git commit` · `git add` 하지 않는다. 구현 + 검증 + 보고까지만.
- 주석과 문서는 **한국어**. 영문 기술용어는 병기한다. 약어와 압축 표현을 쓰지 않는다.
- 새 `.py` 머리에는 이 저장소 규약대로 `# <include file="docs/codegraph/comments.xml" .../>` 마커와
  한 줄 뜻, `# 쓰는 것: … · 쓰이는 곳: …` 를 단다. `codegraph/facts.py:1-5` 를 그대로 본뜬다.
  다 만든 뒤 `.venv/bin/python codegraph/xmldoc.py emit && … inject && … check` 로 마커를 맞춘다.
- 확신도는 🔵(이번 세션에서 읽은 file:line 또는 실제 돌린 명령의 출력만) / 🟡 / 💭.
  **"검증됨" "입증" "증명" 을 쓰지 않는다.**
- **거울 함정 금지.** 단계는 여섯 고정이다. 레지스트리 · 플러그인 · 추상 스케줄러가 떠오르면
  그 자체가 이 도구가 잡으려는 실패다. 구현자 1 · 소비자 1이면 인터페이스를 만들지 않는다.
- **파이썬 의존성을 늘리지 않는다.** `networkx numpy scipy pytest` 넷이 전부다. 병렬은
  표준 라이브러리 `concurrent.futures.ThreadPoolExecutor` 로 한다(자식 프로세스를 기다리는 일이라
  스레드로 충분하다 — GIL 이 문제되지 않는다).

[IMPORTANT — BOUNDARIES]
prep 계층 전체가 네 것이 아니다. 이미 결정론으로 돌고 있고, 층 계산의 재료를 거기서 받는다.
- **건드리지 않는다** — `scripts/wiki/prep.mjs` · `scripts/wiki/paths.mjs` · `scripts/wiki/compdb.mjs` ·
  `scripts/wiki/clang-doc.mjs` · `codegraph/normalize.py` · `codegraph/facts.py` ·
  `codegraph/render_modules.py` · `codegraph/clang_doc.py`
- **건드리지 않는다** — `codegraph/terms_db.py` (Mode 1 에이전트 정의가 명시적으로 금지한다.
  오케스트레이터가 참조한다). 그 **출력을 읽기만** 한다.
- **건드리지 않는다** — `scripts/wiki/build.mjs` · `scripts/wiki/check.mjs` ·
  `codegraph/demermaid.py` · `codegraph/verify_citations.py` (뒤쪽 기계 단계)
- **건드리지 않는다** — `src/*` · `scripts/build.mjs` · `scripts/check.mjs` (Mode 2 소유)
- **건드리지 않는다** — `~/.claude/plugins/cache/skills/deep-wiki/**`.
  **플러그인 캐시라 업데이트에 덮인다.** deep-wiki 의 산문 규정을 바꾸고 싶으면 그 파일이 아니라
  **우리 프롬프트가 감싸서** 지시한다. 지금 `agent_prompt()` 가 이미 그렇게 하고 있다
  (`run_mode1.py:220` — "`/deep-wiki:page` 의 규정을 따르되 사이트 조립은 하지 마라").
- 지금 더러운 파일(아래 실측)을 정리하거나 되돌리지 않는다. 남의 작업이다.

네 작업 파일은 정확히 여섯이다:
  1. `codegraph/run_mode1.py`                          (개조 — **본체**)
  2. `codegraph/test_run_mode1.py`                     (개조 — 잠긴 결정이 바뀐다. 아래 참조)
  3. `codegraph/survey_plan.py`                        (신규 — 층·배치 계산)
  4. `codegraph/test_survey_plan.py`                   (신규)
  5. `codegraph/file_cache.py`                         (신규 — 층 경계 통독 캐시)
  6. `.agents/skills/codebase-terms-survey/SKILL.md`   (개조 — 절차의 정본)

[⚠ 네가 잠긴 결정 하나를 뒤집는다 — 이걸 모르고 시작하면 안 된다]
`run_mode1.py:26-28` 과 `codegraph/CLAUDE.md` 는 **"에이전트를 하나로 묶은 것이 이 설계의 급소"**
라고 못 박고 있다. 이유는 캐시다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어
토큰이 부풀고, 측정값이 파이프라인의 비용이 아니라 세션 수의 함수가 된다.

**사용자가 이번에 그 결정을 뒤집었다.** 층 병렬은 세션을 여러 개로 쪼개는 것이 전제다.
그래서 다음 두 테스트가 지금의 결정을 지키고 있고, 네가 **의도적으로** 고쳐야 한다:
- `codegraph/test_run_mode1.py:34` `test_only_one_stage_calls_the_model`
  — `[s for s in stages if is_agent_stage(s)] == ["agent"]` 를 단언한다
- `codegraph/test_run_mode1.py:140` `test_the_prompt_names_both_halves_of_the_one_agent_job`
  — 한 프롬프트가 전수조사와 산문을 둘 다 지시함을 단언한다

**테스트를 조용히 지우지 마라.** 새 설계를 단언하는 테스트로 **갈아 끼우고**, 무엇이 왜 바뀌었는지
docstring 에 적는다. 그리고 `run_mode1.py` 의 모듈 docstring(`:26-28`)과 `codegraph/CLAUDE.md` 의
같은 주장도 함께 고친다 — 코드와 문서가 어긋난 채로 두지 않는다.

**비용은 열려 있다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 훨씬 적다. 어느 쪽이 큰지는
**모른다.** 다행히 `run_mode1.py` 자체가 재는 도구라 A/B 가 바로 된다. 냉시동 기준선은 아래에 있다.
**"더 싸졌다" 고 주장하지 마라 — 재고 숫자를 보고하라.**

[VERIFIED FACTS — 이번 세션 실측 2026-08-30]
- HEAD `05869ac [update] : gitignore`, branch `main`, `git status --porcelain` **39줄**.
  겹칠 수 있는 더러운 것: `codegraph/normalize.py` · `docs/codegraph/terms-reading.json`.
  `codegraph/run_mode1.py` 와 `codegraph/CLAUDE.md` 는 **untracked(`??`)** 다 — 아직 커밋 전이다.
- 파이썬은 `.venv/bin/python`. `networkx` 는 이미 쓰인다(`codegraph/facts.py:105` `nx.pagerank`).
- 🔵 **Mode 1 냉시동 기준선** (`codegraph/CLAUDE.md` 기록) — 전체 27분 08초 중
  에이전트가 26분 53초(**99.1%**) · 17,925,770 토큰 · **$15.4991** · **84턴**.
  그중 **캐시읽기가 97.3%**. 네 A/B 는 이 네 수와 비교한다.
- 🔵 이 저장소 자신의 코드 지도 `out/codegraph-raw/codegraph.json` — 노드 173 · 간선 105 · 모듈 7.
  1차 노드(external 제외) 167 · **순환 0개**(클래스층·모듈층 모두).
  ⚠ 이건 정적 수집기 산물이 아니라 이전 LLM 조사의 투영이다(Python·JS 라 수집기가 없다).
  **하네스 검증 표본으로만 쓴다.**
- 🔵 그 지도의 위상 깊이 분포 — **층0:110 · 층1:32 · 층2:16 · 층3:7 · 층4:2**.
  층0 의 110개 중 **42개는 in_deg·out_deg 가 모두 0인 고립 노드**다.
- 🔵 **out_deg 로 정렬하면 Bottom-Up 이 깨진다** — out_deg 1 무리(31개) 안에 위상 깊이 1·2·3·4 가
  섞여 있다. 그래서 정렬 축은 out_deg 값이 아니라 **위상 깊이**다.
- 🔵 **층 경계 중복 통독이 실재한다** — 유일 파일 41개인데 층별 파일 수를 합치면 84개, **중복 43회**.
  파일 25/41 이 여러 층에 걸친다. `codegraph/normalize.py` 는 심볼 21개가 층 0·1·2·3 에 흩어져 있다.
  **lock 으로는 못 막는다** — 서브에이전트는 컨텍스트가 분리돼 있어 lock 은 동시 쓰기를 막을 뿐
  이미 읽은 내용을 남에게 넘기지 못한다. 디스크에 남는 **통독 캐시**가 답이다.
- 🔵 `docs/codegraph/terms-reading.json` 318 레코드의 kind 분포 — function 200 · file 52 · key 14 ·
  artifact 14 · interface 11 · concept 9 · module 7 · external 6 · enum 4 · class 1.
  이 중 **96개(file·module·artifact·key·concept)는 코드 지도의 노드가 아니라 층 축이 없다.**
- 🔵 층 계산의 재료는 조사 **이전에** 있다. `report-wiki prep` 이 LLM 이 한 글자도 읽기 전에
  정적 수집기로 `codegraph.json` 을 낸다(`scripts/wiki/prep.mjs` 의 `prepPlan`). 수집기는 2종 고정 —
  `.csproj`/`.slnx`/`.sln` → roslyn-dump, `CMakeLists.txt` → clang-uml (`scripts/wiki/paths.mjs`
  의 `collectorFor`). Mode 1 대상 두 곳(StickRushGame C# · QtVisionEdit C++)이 전부 여기 해당한다.
- 🔵 deep-wiki 는 `~/.claude/plugins/cache/skills/deep-wiki/2.0.0/` 에 산다 — **버전 폴더가 있는
  플러그인 캐시**다. 페이지는 심볼도 모듈도 아닌 **주제 카탈로그**(Getting Started / Deep Dive,
  최대 4단, 절당 자식 ≤8장 — `commands/generate.md:44-51`). `wiki-writer`·`wiki-researcher` 는
  `model: sonnet` 이다.
- 🔵 `codegraph/warmup.py` 가 이미 있다. `blast_radius(재읽기 ∪ 위치만)` 이 다시 읽을 파일을 낸다.
  **증분 재조사에서는 층 계획을 이 목록으로 걸러야 한다** — 안 바뀐 심볼까지 다시 읽으면 warmup 이 무의미하다.
- 이 보고를 그대로 믿지 말고 **재검증하라.** 위 숫자는 지금 더러운 트리에서 잰 것이다.
  `[VERIFY]` 의 명령을 실제로 돌려 네 눈으로 확인한 뒤 진행한다.

[사용자가 확정한 결정 — 다시 논쟁하지 않는다]
| # | 결정 |
|---|---|
| K1 | 정렬 축은 **위상 깊이**. 남을 의존하지 않고 남에게 의존받기만 하는 것(out_deg 0)이 층0, 거기서 한 겹씩 벗긴다 |
| K2 | 층 안에서는 **병렬**, 층 사이는 **순차**. 층 k 는 층 <k 가 전부 끝난 뒤 시작 |
| K3 | 배치는 **고정 크기 N = 8 심볼** |
| K4 | 한 층에서 **동시에 8배치**까지 띄운다 |
| K5 | 그래프 노드가 아닌 용어(file·module·artifact·key·concept)는 **맨 마지막 별도 층** |
| K6 | 위키 산문도 같은 층 순서. **페이지의 층 = 그 페이지가 인용하는 심볼의 최대 층** |
| K7 | 고립 노드(간선 0개)는 의존 대상이 없으므로 **층0 에 함께 둔다** |

========================================================================
[STEP 1] codegraph/survey_plan.py (신규) — 층과 배치를 결정론으로 계산한다
========================================================================
```python
#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/survey_plan.py']"/>
# 전수조사를 어떤 순서로 어떻게 쪼개 돌릴지 계획하는 파일.
# 쓰는 것: survey-plan.json · 쓰이는 곳: run_mode1.main
"""survey_plan.py — 전수조사 배치 계획.

**왜 필요한가.** 심볼의 뜻은 그것이 의존하는 심볼의 뜻 위에 선다. 아무 순서로나 읽으면
아직 안 읽은 것을 가리키게 되고, 그 자리는 추론으로 메워진다. 그래서 **의존 대상이 없는 것부터**
한 겹씩 올라간다. 같은 층끼리는 서로 의존하지 않으므로 병렬로 읽어도 안전하다.

**이 파일은 판정하지 않는다.** 순서를 계산하고 배치를 나눌 뿐이다.

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
# 쓰는 것: 없음 · 쓰이는 곳: survey_plan.plan
def layer_of(first, edges):
    """의존 대상이 없으면 층0, 아니면 1 + 의존 대상들의 최대 층.

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
                 "files": b["files"],
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
    json.dump(p, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
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
```
- 🔵 이 저장소로 돌리면 층이 **0:110 · 1:32 · 2:16 · 3:7 · 4:2** 로 나와야 한다. 안 나오면 멈추고 보고하라.

========================================================================
[STEP 2] codegraph/file_cache.py (신규) — 층 경계 중복 통독을 없앤다
========================================================================
```python
#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/file_cache.py']"/>
# 파일을 한 번만 통독하도록 통독 결과를 디스크에 남기는 파일.
# 쓰는 것: _filecache/*.json · 쓰이는 곳: 없음
"""file_cache.py — 파일 통독 캐시.

층이 올라가면 같은 파일을 다시 열게 된다(🔵 이 저장소 실측 — 유일 파일 41개, 층별 합계 84개,
중복 43회). 배치 세션끼리는 컨텍스트를 공유하지 못하므로, 먼저 읽은 쪽이 **개요를 디스크에 남기고**
나중 쪽이 그것을 읽는다.

**lock 을 쓰지 않는다.** 임시 파일에 쓰고 `os.replace` 로 갈아 끼우면 POSIX 에서 원자적이라
반쯤 쓰인 파일을 남이 읽는 일이 없다. lock 은 동시 쓰기를 막을 뿐, 이미 읽은 내용을
남에게 넘겨주지는 못한다 — 그건 lock 이 풀 수 있는 문제가 아니다.

**캐시는 개요일 뿐 근거가 아니다.** 자기가 맡은 심볼은 반드시 실제 줄 범위를 열어 읽는다.
캐시만 보고 쓴 레코드는 `confidence` 가 HIGH 일 수 없다.

  file_cache.py get <repo> <파일경로>            → 캐시 출력. 없거나 낡았으면 종료 코드 1
  file_cache.py put <repo> <파일경로> <개요json> → 캐시 기록
"""
import hashlib
import json
import os
import sys


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache._paths']"/>
# 파일의 내용 해시와 그 캐시가 놓일 자리를 함께 낸다.
# 쓰는 것: 없음 · 쓰이는 곳: file_cache.get, file_cache.put
def _paths(repo, rel):
    """내용 해시로 캐시를 무효화한다. mtime 은 체크아웃으로 흔들려 못 믿는다."""
    h = hashlib.sha1(open(os.path.join(repo, rel), "rb").read()).hexdigest()
    key = hashlib.sha1(rel.encode("utf-8")).hexdigest()
    return h, os.path.join(repo, "out", "codegraph-raw", "_filecache", key + ".json")


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache.get']"/>
# 남이 남긴 통독 개요가 아직 쓸 만하면 돌려준다.
# 쓰는 것: file_cache._paths · 쓰이는 곳: 없음
def get(repo, rel):
    """캐시가 있고 내용 해시가 같으면 돌려준다. 아니면 None — 부르는 쪽이 통독한다."""
    try:
        h, path = _paths(repo, rel)
        d = json.load(open(path, encoding="utf-8"))
        return d if d.get("sha1") == h else None
    except Exception:
        return None


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache.put']"/>
# 통독 개요를 원자적으로 남긴다.
# 쓰는 것: file_cache._paths · 쓰이는 곳: 없음
def put(repo, rel, outline):
    """개요를 남긴다. 임시 파일 + os.replace 라 원자적이다."""
    h, path = _paths(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    json.dump({"path": rel, "sha1": h, "outline": outline},
              open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    cmd, repo, rel = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "get":
        d = get(repo, rel)
        if d is None:
            sys.exit(1)
        json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
    elif cmd == "put":
        print(put(repo, rel, json.load(open(sys.argv[4], encoding="utf-8"))))
    else:
        sys.exit("모르는 명령 %s" % cmd)
```
- `outline` 꼴은 배치 프롬프트가 정한다: 심볼마다
  `{name, kind, line, end_line, signature, one_line}` + 파일의 `imports` · `head_comment`.
- `out/codegraph-raw/` 는 gitignore 다. 캐시가 거기 사는 것이 맞다 — 재생성 가능한 파생물이다.

========================================================================
[STEP 3] codegraph/run_mode1.py (개조) — **본체.** agent 칸을 층 병렬로 바꾼다
========================================================================
지금 구조: `STAGES = ["prep","agent","terms","build","check"]`, `AGENT_STAGES = {"agent"}`,
`agent_prompt()` 하나가 전수조사와 산문을 **둘 다** 지시하고 `run_agent()` 가 **한 번** 부른다.

바꿀 구조 — 단계를 여섯으로 가르고 LLM 칸을 둘로 나눈다:

    prep ──▶ survey ──▶ terms ──▶ wiki ──▶ build ──▶ check
    기계     LLM 층별    기계     LLM 층별   기계     기계

`terms` 가 `survey` 와 `wiki` 사이로 온다. 이유: 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다. 지금은 산문이 검사 전 레코드를 본다.

3-1. 상단 상수:
```python
# 단계는 여섯 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["prep", "survey", "terms", "wiki", "build", "check"]

# 모형을 부르는 단계. **둘 다 층 오름차순으로 여러 번** 부른다 — 예전의 한 번이 아니다.
AGENT_STAGES = {"survey", "wiki"}
```

3-2. `plan_stages` 의 시그니처는 그대로 두고 `agent` 분기만 가른다:
```python
        if s == "survey" and has_reading:
            continue
        if s == "wiki" and has_prose:
            continue
```
(예전에는 `agent` 하나를 `has_reading and has_prose` 로 걸렀다. 이제 각자 자기 산출물로 걸린다 —
한쪽만 있으면 그쪽만 건너뛴다. 이건 **개선**이지 회귀가 아니다.)

3-3. `agent_prompt()` 를 **세 함수로 가른다.** 셋 다 순수 함수라 시험이 쉽다.

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.survey_batch_prompt']"/>
# 배치 하나를 맡을 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_layer
def survey_batch_prompt(repo, root, batch, dep_records):
    """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

    `dep_records` 는 **아래층에서 이미 완성된** 레코드 중 이 배치의 심볼이 의존하는 것만
    발췌한 것이다. 전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라진다.
    """
    syms = "\n".join(
        "  - %s (%s) %s:%s   의존 -> %s"
        % (s["name"], s["kind"], s["file"], s["line"], ", ".join(s["depends_on"]) or "없음")
        for s in batch["symbols"])
    return """\
너는 코드베이스 전수조사의 배치 {bid} 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 너보다 아래층은 이미 끝났다 — 다시 조사하지 마라

{deps}

## 네가 맡은 심볼 {n}개 — 이것만 한다

{syms}

## 읽는 법 — 순서를 지킨다

1. 담당 파일마다 통독 캐시를 먼저 본다:
     {root}/.venv/bin/python {root}/codegraph/file_cache.py get {repo} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 남긴다:
     … file_cache.py put {repo} <파일경로> <개요json>
     개요 꼴 — 심볼마다 {{name, kind, line, end_line, signature, one_line}} 에
     파일의 imports 와 head_comment 를 더한 객체.
2. **네 심볼은 캐시로 때우지 않는다.** 반드시 그 줄 범위를 실제로 읽는다.
   캐시는 남의 심볼을 uses[].to 로 가리킬 때만 쓴다.

## 레코드 계약

{{kind, module, where, means, does, uses[], confidence, source:"reading"}}
- where = `경로:줄` (필수. 기계가 L1 파일 / L2 줄 / L3 근처에 이름 으로 검사한다)
- means = 무엇인가, 한 문장. **객체지향을 갓 배운 대학 1학년 눈높이.** 어려운 용어로 설명하지 않는다
- does  = 무엇을 하는가, 한두 문장
- uses[] = {{to, kind, label, where}}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
- confidence = HIGH(코드를 읽고 썼다) / MEDIUM(일부 읽고 나머지는 추론) / LOW(이름·구조에서 추론)
  **전부 HIGH 로 적으면 그 칸이 장식이 된다.**

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 함수를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "…에 연결될 것 같다"    -> import 나 호출을 실제로 따라간다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 쓰는 곳 — 여기 말고 아무 데도 쓰지 않는다

  {repo}/docs/codegraph/_shards/{bid}.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 열지도 고치지도 않는다.** 지금 다른 배치들이 동시에 돌고 있다.
키가 다른 파일과 겹칠 것 같아도 **네가 고치지 않는다** — 층이 끝날 때 일괄 해소된다. 보고에 적기만 한다.
**커밋하지 않는다.**

## 끝내기 전에

- 심볼 {n}개에 레코드가 {n}개 있는가
- where 의 줄 번호를 실제로 열어 확인했는가
- confidence 가 전부 HIGH 는 아닌가
- 샤드 파일 하나만 만들었는가

보고: 레코드 수 · confidence 분포 · 통독한 파일과 캐시로 때운 파일 · 키 충돌 후보 · 읽지 못한 것과 이유.
""".format(repo=repo, root=root, bid=batch["id"], n=len(batch["symbols"]),
           syms=syms, deps=dep_records or "  (없음 — 너는 최하층이다)")


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.nonnode_prompt']"/>
# 지도에 없는 용어들을 맡을 마지막 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_layer
def nonnode_prompt(repo, root):
    """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

    이것들은 코드 지도의 노드가 아니라 층 축이 없다. 대신 **심볼 레코드가 재료**다 —
    파일 레코드는 그 파일 안 심볼들의 완성된 means/does 를 보고 쓴다.
    """
    ...   # survey_batch_prompt 와 같은 계약·금지표를 쓰되 대상만 다르다


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.wiki_page_prompt']"/>
# 위키 한 장을 맡을 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_layer
def wiki_page_prompt(repo, root, page, lower_pages):
    """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼의 최대 층.

    **왜 최대인가.** 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신 링크할 수
    있다. 가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다.

    **deep-wiki 플러그인을 고치지 않는다.** 그건 `~/.claude/plugins/cache/` 에 사는 캐시라
    업데이트에 덮인다. 대신 이 프롬프트가 감싸서 지시한다 — 지금 코드가 이미 쓰는 방식이다.
    `lower_pages` 는 이미 선 아래층 페이지의 파일명과 제목이다. 재설명 대신 그것을 링크하게 한다.
    """
    ...
```

3-4. 층을 도는 실행기. **`concurrent.futures` 만 쓴다**(새 의존성 없음):
```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_layer']"/>
# 한 층의 배치들을 동시에 돌리고 각각의 측정값을 모은다.
# 쓰는 것: run_mode1.run_agent · 쓰이는 곳: run_mode1.main
def run_layer(model, repo, root, prompts, concurrency=8, timeout=None):
    """한 층 = 동시에 최대 concurrency 개. 층 사이는 부르는 쪽이 순차로 돈다(K2).

    같은 층끼리는 서로 의존하지 않으므로 순서가 결과를 바꾸지 않는다 — 그래서 병렬이 안전하다.
    **자식 프로세스를 기다리는 일이라 스레드로 충분하다.** GIL 은 여기서 문제가 되지 않는다.
    각 배치의 usage 를 따로 모은다 — 어느 배치가 비쌌는지 알아야 다음에 target 을 조절한다.
    """
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(run_agent_with, model, repo, root, p, timeout): label
                for label, p in prompts}
        return [(futs[f],) + f.result() for f in futs]
```
- `run_agent()` 는 지금 `agent_prompt(repo, root)` 를 안에서 부른다(`run_mode1.py:362`).
  **프롬프트를 인자로 받는 `run_agent_with()` 로 가르고**, `run_agent()` 는 그것을 부르는
  얇은 껍질로 남긴다 — 기존 테스트가 덜 깨진다.
- **`--concurrency` 를 CLI 인자로 뺀다** (기본 8 = K4). 층별 배치 수는 `survey-plan.json` 이 정한다.
- `format_report` 의 행은 `survey/L0-B00` 처럼 **단계/배치** 로 적어 어느 배치가 비쌌는지 보이게 한다.
  층 소계 줄을 넣으면 더 좋다. 합계 계산은 `sum_usage` 를 그대로 쓴다.

3-5. 층이 끝날 때 **오케스트레이터(파이썬)가 샤드를 병합**한다:
```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.merge_shards']"/>
# 배치들이 따로 쓴 조각을 하나로 합치고 이름 충돌을 푼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def merge_shards(shard_dir, existing):
    """샤드를 합쳐 terms-reading.json 을 만든다. **키 충돌 해소는 여기서만 한다.**

    배치 세션은 자기 배치만 보므로 `main` 이 9파일에 있다는 것을 알 수 없다.
    전역을 보는 것은 이 함수뿐이다 — 겹치면 겹친 **전원**을 `<파일줄기>.<이름>` 으로 고친다.
    한쪽만 한정하면 나중에 또 겹친다.
    """
```

3-6. **모듈 docstring 을 고친다.** `run_mode1.py:13-28` 의 다섯 단계 그림과
"에이전트를 하나로 묶은 것이 이 설계의 급소다" 문단을 새 설계로 바꾼다. 왜 바꿨는지
(사용자 결정 K1~K7)와 **비용은 아직 재지 않았다**는 것을 함께 적는다.

========================================================================
[STEP 4] codegraph/test_run_mode1.py (개조) — 잠긴 결정이 바뀐 것을 테스트로 드러낸다
========================================================================
- `test_only_one_stage_calls_the_model` (`:34`) → **갈아 끼운다**:
```python
def test_두_단계가_모형을_부른다():
    """예전에는 agent 한 칸이었다. 2026-08-30 사용자 결정으로 survey · wiki 로 갈렸다 —
    층 오름차순 병렬이 세션 분리를 전제하기 때문이다. 캐시 비용은 아직 재지 않았다."""
    stages = R.plan_stages(False, False, False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["survey", "wiki"]
```
- `test_the_prompt_names_both_halves_of_the_one_agent_job` (`:140`) → **둘로 가른다**:
  배치 프롬프트가 자기 심볼·샤드 경로·금지표를 담는지, 위키 프롬프트가 아래층 페이지를
  링크하라고 지시하는지 각각 단언한다.
- **새 테스트를 더한다**: `run_layer` 가 concurrency 를 넘지 않는지, `merge_shards` 가
  키 충돌을 **양쪽 다** 개명하는지, `plan_stages` 가 `has_reading` 만 있을 때 `survey` 만 건너뛰는지.

========================================================================
[STEP 5] codegraph/test_survey_plan.py (신규)
========================================================================
```python
#!/usr/bin/env python3
"""survey_plan.py 시험. 합성 그래프로 규칙을, 실제 지도로 규모를 본다."""
import json
import os

import pytest

from survey_plan import layer_of, pack, plan


def _cg(nodes, edges):
    return {"nodes": [{"id": i, "name": i, "kind": "function", "file": f, "line": 1}
                      for i, f in nodes],
            "edges": [{"from": s, "to": d} for s, d in edges]}


def test_층은_의존_대상이_없는_것부터():
    """a -> b -> c 면 c 가 층0, b 가 층1, a 가 층2."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "c")])
    assert (lv["c"], lv["b"], lv["a"]) == (0, 1, 2)


def test_고립_노드는_층0():
    """간선이 하나도 없어도 의존 대상이 없으므로 층0 이다 (K7)."""
    lv, _ = layer_of({"x": 1}, [])
    assert lv["x"] == 0


def test_순환은_한_덩어리로_접힌다():
    """a <-> b 는 위상 깊이가 정의되지 않는다. 같은 층으로 접고 표시한다."""
    lv, cyc = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "a"), ("a", "c")])
    assert lv["a"] == lv["b"] and cyc["a"] and cyc["b"] and not cyc["c"]


def test_out_deg_가_아니라_위상_깊이다():
    """a 는 out_deg 1, d 는 out_deg 2 지만 둘 다 층2 다 — out_deg 로 나누면 순서가 틀린다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1, "d": 1},
                     [("a", "b"), ("b", "c"), ("d", "b"), ("d", "c")])
    assert lv["a"] == 2 and lv["d"] == 2 and lv["b"] == 1 and lv["c"] == 0


def test_같은_파일은_한_배치에():
    """파일이 쪼개지면 두 세션이 같은 파일을 각각 통독하게 된다."""
    bs = pack(["a", "b", "c", "d", "e"],
              {"a": "f1.py", "b": "f1.py", "c": "f1.py", "d": "f2.py", "e": "f2.py"}, target=3)
    for f in ["f1.py", "f2.py"]:
        assert sum(1 for b in bs if f in b["files"]) == 1


def test_큰_파일은_초과를_허용한다():
    """심볼 5개짜리 파일은 target 3 이어도 쪼개지 않는다."""
    bs = pack(list("abcde"), {c: "big.py" for c in "abcde"}, target=3)
    assert len(bs) == 1 and len(bs[0]["symbols"]) == 5


def test_결정론():
    """같은 입력이면 같은 출력. 순서가 흔들리면 계획이 재현되지 않는다."""
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f2")], [("a", "b"), ("b", "c")])
    assert json.dumps(plan(cg), sort_keys=True) == json.dumps(plan(cg), sort_keys=True)


def test_external_은_제외():
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "ext", "name": "ext", "kind": "external"})
    assert plan(cg)["totals"]["symbols"] == 1


def test_마지막은_비노드_층():
    assert plan(_cg([("a", "f1")], []))["layers"][-1]["kind"] == "non-node"


def test_증분은_층_번호를_보존한다():
    """warmup 이 준 파일만 남기되 층은 **전체 그래프 기준**이어야 한다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다."""
    cg = _cg([("a", "f1"), ("b", "f2"), ("c", "f3")], [("a", "b"), ("b", "c")])
    p = plan(cg, only_files=["f1"])
    assert p["totals"]["symbols"] == 1 and p["layers"][0]["level"] == 2


REAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "out", "codegraph-raw", "codegraph.json")


@pytest.mark.skipif(not os.path.exists(REAL), reason="out/codegraph-raw/codegraph.json 이 없다")
def test_이_저장소_실측():
    """🔵 2026-08-30 기준 층 분포. 코드가 바뀌면 숫자도 바뀐다 — 그때는 값을 갱신한다."""
    p = plan(json.load(open(REAL, encoding="utf-8")))
    sizes = [L["symbol_count"] for L in p["layers"] if L.get("kind") != "non-node"]
    assert sum(sizes) == p["totals"]["symbols"]
    assert sizes[0] > sizes[-1]          # 아래층이 가장 넓다
```

========================================================================
[STEP 6] .agents/skills/codebase-terms-survey/SKILL.md (개조) — 절차의 정본
========================================================================
`.claude/skills/codebase-terms-survey` 는 이 파일로 가는 **심볼릭 링크**다. 원본만 고친다.

6-1. Workflow 5단계 `"레코드를 쓴다 — 파일 순서, 파일 안은 줄 순서"` 를 갈아 끼운다:
```
5. **배치 계획을 만든다** — `python codegraph/survey_plan.py <codegraph.json> --target 8`
   → `survey-plan.json`. 층0(의존 대상이 없는 것)부터 층이 오른다.
   재료는 조사 **이전에** 있다 — `report-wiki prep` 이 정적 수집기로 코드 지도를 먼저 낸다.
   수집기가 없는 저장소는 `prep` 이 막히므로 애초에 Mode 1 대상이 아니다. 그때는 함께 막고 보고한다.
   증분 재조사면 `warmup.py blast` 의 파일 목록을 `--only-files` 로 준다.
6. **레코드를 쓴다 — 층 오름차순, 층 안은 병렬.**
   - 층 사이는 **순차**. 층 k 는 층 <k 가 전부 끝나고 병합된 뒤 시작한다.
   - 층 안은 **배치 8개까지 동시**. 같은 층끼리는 서로 의존하지 않으므로 안전하다.
   - 배치는 자기 샤드 `<repo>/docs/codegraph/_shards/L{층}-B{번호}.json` 에만 쓴다.
     **terms-reading.json 을 직접 고치지 않는다** — 동시에 여러 배치가 돌기 때문이다.
   - 층이 끝나면 오케스트레이터(`run_mode1.py` 의 `merge_shards`)가 샤드를 병합한다.
     **키 충돌 해소는 거기서만 한다** — 배치는 자기 것만 보므로 `main` 이 9파일에 있다는 것을 모른다.
   - 층 k 배치에는 **자기 심볼이 의존하는 아래층 레코드만** 발췌해 준다. 전량 주입은 낭비다.
   - 같은 파일을 층마다 다시 열지 않도록 `file_cache.py` 를 쓴다. 다만 **자기 심볼은 캐시로
     때우지 않는다** — 캐시만 보고 쓰면 `confidence` 가 HIGH 일 근거가 없다.
7. **비노드 용어는 맨 마지막 층** — file · module · artifact · key · concept.
   심볼이 전부 읽힌 뒤라야 파일 레코드가 그 안 심볼들의 완성 레코드를 재료로 쓸 수 있다.
```
아래 기존 6·7·8 단계는 번호만 8·9·10 으로 민다.

6-2. `## 산출물` 표에 두 줄을 보탠다:
```
| `<repo>/out/codegraph-raw/survey-plan.json` | `survey_plan.py` | 층·배치 계획. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/_filecache/*.json` | 배치 세션 | 통독 캐시. gitignore, 재생성 |
```

6-3. `## Common pitfalls` 에 세 줄을 보탠다:
```
- **out_deg 로 정렬** — 그건 위상 깊이가 아니다. 🔵 실측에서 out_deg 1 무리 안에 깊이 1·2·3·4 가
  섞여 있었다. out_deg 로 나누면 아직 안 읽은 것을 가리키게 된다
- **층 경계에서 같은 파일을 다시 통독** — 🔵 유일 파일 41개인데 층별 합계 84개다. `file_cache.py` 를 쓴다
- **배치가 terms-reading.json 을 직접 고침** — 동시 쓰기로 서로를 지운다. 샤드에만 쓴다
```

6-4. 새 절 `## deep-wiki 산문도 같은 층 순서로 (K6)` 를 붙인다:
```
위키 페이지는 심볼도 모듈도 아닌 **주제** 단위다(Getting Started / Deep Dive, 최대 4단, 절당 ≤8장).
그래서 **페이지의 층 = 그 페이지가 인용하는 심볼들의 최대 층**으로 매긴다.
왜 최대인가 — 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신 링크할 수 있다.

**deep-wiki 플러그인 파일을 고치지 않는다.** `~/.claude/plugins/cache/` 에 사는 캐시라 업데이트에
덮인다. 우리 프롬프트(`run_mode1.py` 의 `wiki_page_prompt`)가 감싸서 지시한다.
```

[VERIFY] — 실제로 돌리고 출력을 보고에 붙인다
- `cd /Users/escatrgot/LLM-Tools/report-builder`
- `.venv/bin/python -m pytest codegraph/ -q`
  → 🔵 기준선은 골든 변수 없이 **201 통과 · 19 건너뜀**이다. 실패 0이어야 하고,
    통과 수는 네가 더한 만큼 늘어야 한다. **줄어들면 무언가를 조용히 깬 것이다.**
- `.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json`
  → **층 분포가 0:110 · 1:32 · 2:16 · 3:7 · 4:2** 여야 한다.
- 결정론:
  ```
  .venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p1.json
  .venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p2.json
  diff /tmp/p1.json /tmp/p2.json && echo "결정론 OK"
  ```
- 층 안 파일 중복 0:
  ```
  .venv/bin/python -c "
  import json,collections
  p=json.load(open('/tmp/p1.json'))
  for L in p['layers']:
      c=collections.Counter(f for b in L.get('batches',[]) for f in b['files'])
      print(L['level'], '중복', [f for f,n in c.items() if n>1] or '없음')"
  ```
- `.venv/bin/python codegraph/run_mode1.py . --dry-run`
  → 단계가 `prep -> survey -> terms -> wiki -> build -> check` 로 나와야 한다.
- 마커: `.venv/bin/python codegraph/xmldoc.py emit && … inject && … check` → 문제 0건.
- `npm test` → 기존 통과 수 유지(네 변경은 Node 쪽을 안 건드리므로 숫자가 그대로여야 한다).
- 심볼릭 링크: `ls -la .claude/skills/codebase-terms-survey` → 여전히 링크여야 한다.

[Self-review]
- prep 계층(`prep.mjs` · `normalize.py` · `facts.py` · `compdb.mjs` · `paths.mjs`)과
  `terms_db.py` · `build.mjs` · `check.mjs` · `src/*` 를 안 건드렸는가? (`git status --short`)
- `~/.claude/plugins/` 아래를 안 건드렸는가?
- 처음부터 더러웠던 39개 파일을 건드리거나 되돌리지 않았는가?
- **잠긴 결정을 뒤집은 것을 코드·테스트·문서 세 곳에 모두 적었는가?**
  (`run_mode1.py` docstring · 갈아 낀 테스트의 docstring · `codegraph/CLAUDE.md`)
- 새 `.py` 두 개에 `# <include .../>` 마커와 `# 쓰는 것: … · 쓰이는 곳: …` 줄이 있는가?
- 문서에 "검증됨" "입증" "증명" 이 없는가? 재지 않은 것을 "더 싸졌다" 고 주장하지 않았는가?
- 새 파이썬 의존성을 더하지 않았는가? (`concurrent.futures` 는 표준 라이브러리다)
- 레지스트리·플러그인·추상 스케줄러를 만들지 않았는가? (거울 함정)
- **실제 전수조사를 돌리지 않았는가?** 너는 하네스만 만든다.

[REPORT]
DONE / DONE_WITH_CONCERNS / BLOCKED
+ 파일별 변경 요약 (6개만이어야 한다)
+ `pytest codegraph/ -q` 마지막 줄 그대로 (기준선 201 통과 · 19 건너뜀과 비교해서)
+ `survey_plan.py` 실행 출력 그대로 (층 분포가 보이게)
+ 결정론 diff · 층 안 파일 중복 · `run_mode1.py --dry-run` 단계 목록
+ **뒤집은 잠긴 결정과 그것을 적은 자리 세 곳**
+ 미룬 것 / 조율이 필요한 것
+ `git status --short`
**커밋하지 않는다.**
```

---

## Notes (오케스트레이터/사용자용 — 붙여 넣는 블록 바깥)

- **이 작업은 하네스만 만든다. 전수조사 실행은 포함되지 않는다.** 작업 트리가 39개 파일 더럽고,
  전수조사는 "트리가 조용할 때만" 이 전제다(줄 번호가 움직이는 과녁이 된다). 실행은 정리 후 별도로.
- **비용은 열린 질문이다.** 한 세션 통짜(🔵 냉시동 27분 08초 · 17.9M 토큰 · $15.4991 · 84턴 ·
  캐시읽기 97.3%)를 층 병렬로 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다.
  어느 쪽이 큰지는 **모른다.** `run_mode1.py --json` 이 이미 재므로 A/B 는 저렴하다 —
  하네스가 서면 StickRushGame 이나 QtVisionEdit 한 곳에서 한 번씩 돌려 비교하면 된다.
- **함께 뒤집히는 문서 두 곳** — `codegraph/run_mode1.py:26-28` 과 `codegraph/CLAUDE.md` 의
  "에이전트를 하나로 묶은 것이 이 설계의 급소다". 둘 다 untracked 라 커밋 전에 고치면 이력이 깨끗하다.
- **`terms` 가 `survey` 와 `wiki` 사이로 옮겨간다.** 산문 세션이 인용 검사를 통과한 `terms-db.json` 을
  재료로 받게 하려는 것이다. 부수 효과로 산문의 인용 품질이 올라갈 수 있는데, **이것도 재지 않은
  기대**다. `check` 단계의 3값 판정이 그 지표가 된다.
- 결과(DONE + diff)를 받으면 층 분포 110/32/16/7/2 와 결정론 diff, pytest 201→증가를 직접 확인한다.
- 커밋 메시지(권장), 셋으로 나눈다:
  - `[feat] : 전수조사 층 계획과 통독 캐시     codegraph/{survey_plan,file_cache}.py + 시험`
  - `[feat] : mode 1 에이전트 칸을 층 병렬로     codegraph/run_mode1.py  codegraph/test_run_mode1.py`
  - `[docs] : 전수조사 스킬에 층 순서와 병렬 배치     .agents/skills/codebase-terms-survey/SKILL.md`
