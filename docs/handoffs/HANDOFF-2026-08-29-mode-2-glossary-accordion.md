# HANDOFF ⑧ — Mode 2 용어집 아코디언 (mode-2-spec-report 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 15:30).** `mode-2-spec-report` 의 첫 실전 투입 — DONE, 경계 준수, theme.css 추가만(14/0), 커밋 안 함. 오케스트레이터 재검증(npm test 68/68 · 두 보고서 check 5/5 · 모름만 열림) 뒤 `596dec9` 로 커밋. 사용자 육안 판정: 초기 상태(모름만 펼침) 확인. 이 문서는 **기록용**이다. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**사용자 지시 (2026-08-29 15:05)** — "용어집 — 먼저 읽을 것: (1) 모름 · 애매 · 확실 · 미측정 순으로 정렬 (2) 이해도 그룹별로 묶어 아코디언 UI 컴포넌트로."
**사용자 확정 기본값** — 그룹 순서 모름 → 애매 → 확실 → 미측정 · 브라우저 기본 `<details>/<summary>` (스크립트 0줄) · 모름 그룹만 펼쳐진 채 시작 ·
제목 줄에 개수("모름 (11)") · 빈 그룹은 안 그린다 · 그룹 안 순서는 `data.ts` 순서 그대로 · props(`terms`)는 그대로, 마크업만 바뀐다.

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — `[ROLE]` `[HARD RULES]` `[BOUNDARIES]` `[VERIFIED FACTS]` `[STEP]` `[SELF-REVIEW]` `[REPORT]`.
소유: `src/components/terms.tsx`(Glossary 만) · `src/theme.css`(추가만) · `test/components.test.mjs`(Glossary 테스트). 두 보고서 재빌드 + check 5/5 가 인수 조건.
