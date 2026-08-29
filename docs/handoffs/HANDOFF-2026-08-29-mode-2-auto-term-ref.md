# HANDOFF ⑨ — Mode 2 용어 자동 참조 (mode-2-spec-report 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 15:40).** `mode-2-spec-report` DONE_WITH_CONCERNS — 내 테스트 단언 오류 1건(`tabindex` 속성 때문에 항상 0 이 되는 패턴)과 뒤쪽 경계 규칙 1건(`edges[]x`)을 잡아 고쳤다(하네스 6·7번째 사례). 오케스트레이터 재검증(npm test 78/78 · 두 보고서 check 5/5 · 누출 0 · term-ref 0→40 / 0→80) 뒤 `70e4f39`(feat) · `dbb4d0f`(수동 T 제거)로 커밋. 사용자 결정 — 제목·mono 는 건너뛴다(유지). 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**사용자 지시 (2026-08-29 15:20)** — "용어집에 포함된 용어가 계획 설명 본문에서 어떤 것은 term-ref 고 어떤 것은 아니다. 모든 계획 서술에서 term-ref 로 묶이게 하고,
컴포넌트화가 안 돼 있으면 컴포넌트화해 코드 작성을 줄여라." + "`?` 표시와 뜻 · 용례 카드가 나와야 한다."
🔵 실측 — `llm-load-reduction` 본문에 `M1` 5회 · `C-20` 3회 · `calls[]` 11회 등장, term-ref 는 0 · 0 · 1.

**설계 (오케스트레이터, 사용자 확인)** — React 트리 안에서는 산문이 props 로 들어가 닿지 않고 전역·컨텍스트는 금지이므로 **빌드 후 통과**:
`renderToStaticMarkup` 결과 문자열의 글자 부분에서 용어 id 의 **모든 등장**을, `TermRef` 컴포넌트를 실제로 렌더한 마크업으로 감싼다(마크업 출처 하나).
건너뛰는 곳 — 이미 term-ref/term-card 안 · `.mono` `<code>` `<pre>` · `h1~h3` `th` `summary` · 용어집·관계도·SVG · `<script>`.
긴 id 부터. ASCII 로 시작/끝나는 id 는 낱말 경계, 한글 id 는 경계 없음(`모듈을` 도 감싼다). 카드에 `body`(용례)와 이해도 배지 추가, 밑줄 낱말 끝에 작은 `?`.
두 보고서의 수동 `<T id>` 18곳은 지운다(자동으로 같은 결과). `defineTerms` 는 남긴다(추가만).

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — 7블록. 소유: `scripts/wrap-terms.mjs`(신규) · `test/wrap-terms.test.mjs`(신규) · `scripts/build.mjs` · `src/components/terms.tsx` 의 `defineTerms` · `src/theme.css`(추가만) · `test/components.test.mjs`(추가) · 두 보고서 `report.tsx`(수동 `<T>` 제거만).
