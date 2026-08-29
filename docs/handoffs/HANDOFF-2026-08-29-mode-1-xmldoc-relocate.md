# HANDOFF ⑭ — xmldoc where 마커 기준 재계산 + 의존 줄 + 증분 합치기 (mode-1-codebase-wiki 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 17:50).** `mode-1-codebase-wiki` DONE_WITH_CONCERNS(우려는 오케스트레이터가 같은 시각 고친 문서 3건 — 의도된 것). 재검증 전부 통과: pytest 62 · `xmldoc check` 0 · `terms_db` 용어 213 / 실패 0 / **근거 없음 0** · 코드 줄 무변경 0 · 멱등. **근본 원인 정정** — 셈 오류만이 아니라 `77b95de` 가 소스 블록만 커밋하고 `terms-reading.json` 을 빠뜨린 것(38파일 `strip == acf88e1`). 커밋은 RESUME §0.1. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**배경 (🔵 실측)** — `codegraph/xmldoc.py`(`acf88e1`, 주입 `77b95de`)는 뜻을 `docs/codegraph/comments.xml` 한 곳에 두고 코드에 `<include … @id='X'/>` 2줄 블록을 넣는다.
사용자 의도: **개발하면서 생각·기능 설명을 코드 옆에 미리 남겨 나중 LLM 의 재추론 부담을 줄인다.** 그런데 `plan_file` 이 `where` 를 "셈으로" 내면서 앞선 블록들의 누적 밀림을
빠뜨려 `terms-reading.json` 의 `where` 가 실제 선언 줄보다 2·3·4·6·8…32줄 위를 가리킨다(`terms_db.py` 검사 근거 없음 3 → 242, `xmldoc check` 문제 107건).

**사용자 결정 (19:10)** — (1) `where` 는 **마커 기준으로 재계산**한다(셈 제거). (2) 주입 블록에 **의존(uses) 줄**을 더한다 — 파일만 열어도 무엇을 부르고 무엇이 부르는지 보이게.
(3) 그 뒤 재조사 증분(`.tmp/terms-reading.addendum-2026-08-29.json`, 새 레코드 22 · uses 9)을 합치고 inject → 검사 → 커밋.

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — 7블록. 소유: `codegraph/xmldoc.py` · `codegraph/test_xmldoc.py`(신규) · `docs/codegraph/terms-reading.json` · `docs/codegraph/comments.xml` · inject 가 건드리는 소스 파일들의 **주석 블록만**.
