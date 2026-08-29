# HANDOFF ⑦ — Mode 1.5 채점 규칙 3문항화 (mode-1-5-term-benchmark 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 15:00).** `mode-1-5-term-benchmark` 의 첫 실전 투입 — DONE, 경계 준수, 커밋 안 함. 오케스트레이터 재검증(npm test 64/64 · grade/emit 실전 꼴) 뒤 `71a3386` 로 커밋. 이 문서는 **기록용**이다.
> 코드(`scripts/term/quiz.mjs`)와 테스트(`test/term.test.mjs` quiz 절)만 맡긴다. 문서 6곳은 오케스트레이터가 같은 시각에 고쳤다.
> 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**사유** — 2026-08-29 첫 시험(용어 20개 × 5문항 = 100문항, 결과 확실 6 · 애매 3 · 모름 11)에서 사용자가 피로를 보고했다.
사용자 결정: **3문항. 맞힌 수 2~3 확실 / 0~1 모름. "모른다" 2회 이상이면 모름. 애매 는 내지 않는다.**

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — `[ROLE]` `[HARD RULES]` `[BOUNDARIES]` `[VERIFIED FACTS]` `[STEP]` `[SELF-REVIEW]` `[REPORT]`.
새 `gradeOne` 은 `dontKnow >= 2 → 모름`, `correct >= 2 → 확실`, 그 밖 `모름`. `QUESTIONS_PER_TERM = 3`. 테스트 6개를 새 규칙으로 바꾸되 개수는 유지(전체 64).
