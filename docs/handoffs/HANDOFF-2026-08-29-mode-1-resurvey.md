# HANDOFF ⑬ — Mode 1 증분 재조사 (R10 인용 부패, mode-1-codebase-wiki 용 프롬프트)

> 🔴 **완료 (2026-08-29 17:50) — ⑭ 안에서 소화됐다.** 증분 22+9 가 `terms-reading.json` 에 들어갔고 용어 213 · 근거 없음 0. 아래는 보류 당시 기록.
>
> 🟡 ~~보류 → ⑭ 로 이관 (2026-08-29 17:20).~~ 이 증분은 `HANDOFF-2026-08-29-mode-1-xmldoc-relocate.md`(⑭)의 STEP 4 에서 소화된다 — 그쪽이 착지하면 이 문서는 🔴 다.
> (아래는 보류 당시 기록)
>
> 🟡 **보류 (2026-08-29 16:55).** 서브에이전트는 DONE_WITH_CONCERNS 로 끝났으나 **커밋하지 않았다** — 같은 시각 다른 세션이 `codegraph/xmldoc.py inject` 로 38개 파일에 주석 블록을 넣으며 `terms-reading.json` 의 `where` 를 재계산하고 있어, 재조사가 계산한 `where` 가 HEAD 에도 현재 트리에도 맞지 않았다(깨끗한 HEAD 워크트리에서 실패 7 · 근거 없음 121). **사용자 결정 — xmldoc 세션이 먼저 착지, 재조사는 그 뒤.** 재조사의 증분(새 레코드 22 · uses 17, means/does 무변경)은 `.tmp/terms-reading.addendum-2026-08-29.json` 에 떼어 두었고 `terms-reading.json` 은 HEAD 로 되돌렸다. xmldoc 착지 후: addendum 을 키로 합치고 `xmldoc.py inject` 로 `where` 재계산 → 검사 → 커밋. 서브에이전트가 잡은 `xmldoc.py:194` 결함(`uses[].where` 미갱신)은 그 세션에 전달. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**배경 (🔵 18:15 실측)** — 전수조사 커밋 `a9b9080` 뒤 오늘 코드가 많이 바뀌어 `docs/codegraph/terms-reading.json` 의 `where` 가 낡았다: 근거 없음 3 → **26**
(`quiz.mjs` 7 · `types.ts` 4 · `term-graph.ts` 4 · `terms.tsx` 4 · `build.mjs` 4 + 원래 3). 또 새 파일 3개(`scripts/wrap-terms.mjs` `scripts/link-paths.mjs` `src/runtime/graph-math.ts`)와
새 함수들(`wrapTerms` `linkPaths` `makeResolver` `buildIndex` `rectOverlap` `componentCollide` `mountTune` `mountTermCards` …)이 사전에 없다.
**사용자 결정** — 지금 재조사한다(`--relocate` 옵션은 만들지 않는다).

**설계** — **증분**: (1) 근거 없음 26건의 `where` 를 이름 조각으로 다시 찾아 고친다(뜻 `means` 는 그대로 — Mode 1.5 정답지로 이미 쓰였다) (2) 새 파일·새 함수 레코드를 절차대로 추가
(3) 오늘 지워진 함수가 있으면 레코드 제거 (4) 검사 실패 0, 근거 없음 ≤ 3(머리 주석에 파일명 없는 파일 3개) (5) `collect` 필수 8개 유지.

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — 7블록. 소유: `docs/codegraph/terms-reading.json` 만.
