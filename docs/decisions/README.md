# 결정 기록

`CLAUDE.md` 에서 옮겨 온 것들이다. **같은 제안을 다시 하기 전에 해당 기록을 읽는다** —
전부 영구 금지가 아니라 *되살릴 조건*이 붙어 있다.

| # | 결정 | 상태 | 한 줄 |
|---|---|---|---|
| [0001](0001-phase-2-b2-rejected.md) | Phase 2 (B2) 소유권 미니 그래프 | 기각 | 파일럿 사례의 근거가 부식됐고 비교 대상 표가 없었다 |
| [0002](0002-phase-3-a1-cancelled.md) | Phase 3 (A1) D축 소급 검증 | 취소 | 채점할 재료가 없고, 재료를 구하는 방향이 후퇴다 |
| [0003](0003-phase-6-b5-cancelled.md) | Phase 6 (B5) 옛 출력 재현 | 취소 | 옛 출력은 열등판이라 따라갈 이유가 없다 |
| [0004](0004-d-axis-on-hold.md) | D축을 평가 없이 보류 | 보류 | 0002 가 게이트였다. `viz/src/types.ts` 에 필드를 넣지 않는다 |
| [0005](0005-rejected-proposals.md) | 기각안과 부활 트리거 | 유효 | Vite · panzoom · Tailwind 등. 조건부다 |
| [0006](0006-yellow-decisions-without-option-tables.md) | 🟡 결정의 빈 옵션표 | 확정 | 없는 대안을 지어내지 않고 보고만 한다 |
| [0007](0007-xmldoc-include-deprecated.md) | `# <include …/>` 주석 주입 | 폐지 예정 → **폐지 (0010)** | 표시 단계였다. 0010 이 확정했다 |
| [0008](0008-old-output-is-origin-not-target.md) | 옛 산출물은 출발점이지 기준이 아니다 | 확정 | 0001~0003 의 공통 원인. Track A/B 순서와 2026-08-28 해소 항목도 여기 |
| [0009](0009-second-report-genre-deferred.md) | 두 번째 보고서 장르(`번복기록`) mode | 보류 | 소비자 0 인 동안 mode 축을 파지 않는다. `plans/` 입력은 열렸다 |
| [0010](0010-xmldoc-retired.md) | `xmldoc` 주석 주입을 쓰지 않는다 | **폐지** | 게이트에서 뺐다. `emit`·`inject` 안 돌린다. 남은 블록은 잔재 — 지우는 건 별개 작업 |
| [0011](0011-split-mode1-and-report.md) | Mode 1 / Mode 1.5+2 두 저장소 · 데이터 계약 경계 | 확정 | Mode 1 은 사람이 부를 때만 · 1.5 는 봉인 필수 · 2 는 독립 · 리소스와 코드 분리 |
| [0012](0012-prompt-dynamics-in-jinja2.md) | 프롬프트의 동적 부분을 프롬프트 파일 안 Jinja2 로 | 확정 · 자리 조항은 0014 | 마크다운 · 절 표식 유지 · 엄격 검사 · 결함 문구는 TOML · 파일 템플릿은 그대로 · 템플릿은 꼴만 |
| [0013](0013-personal-language-graph-deferred.md) | 사용자 개인어를 공식 용어로 잇는 가중치 그래프(⑤) | 보류 | 공식 용어 쪽 끝이 ①② 실측이라 그것이 먼저다. 개인어 자료는 공개 저장소에 두지 않는다 |
| [0014](0014-mode-first-layout-and-resource-dir.md) | 1차 축은 mode(`codewiki` · `term` · `spec`) · `core` · `common` · `test`/`qa` · `resource/` 한 자리 | 확정 · 미이행 | 분리 계획 M 뒤 · B 앞에 실행(K · M 은 2026-10-31 끝). 0012 의 리소스 자리 조항을 고친다. xmldoc 잔재는 이때 지운다 |

## 새 기록을 더하는 법

번호를 이어 붙이고 위 표에 한 줄을 더한다. **기존 기록은 고치지 않는다** — 뒤집으려면
새 기록을 쓰고 옛 것의 상태를 한 줄로 갱신한다. 그래야 왜 뒤집혔는지가 남는다.

마지막 번호는 파일 이름에서 읽는다. 저장소 루트에서 돌린다.

```bash
ls docs/decisions/ | grep -E '^[0-9]{4}-[a-z]' | tail -n 1    # 지금 마지막 번호. 새 기록은 그다음
```
