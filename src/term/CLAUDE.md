# src/term/ — Mode 1.5. 용어 이해도 점검

> 루트 나침반은 [`../../CLAUDE.md`](../../CLAUDE.md). 단계 기계는 [`../core/CLAUDE.md`](../core/CLAUDE.md), 리소스는 [`../../resource/CLAUDE.md`](../../resource/CLAUDE.md).

Plan 하나를 놓고 돈다 — 필요한 용어를 모으고(collect), 사람이 푼 객관식 답안을 채점해(grade), 학습 노트와 용어집 DB 를 낸다(emit).
**실행기는 사람에게 묻지 않는다.** 묻는 절차는 `term-benchmark` 스킬이 맡는다.

## 무엇이 여기 있나

| 자리 | 무엇 |
|---|---|
| `python/runner/run_mode1_5.py` | Mode 1.5 파이프라인을 돌리다 사람 차례에서 멈추는 실행기 |
| `python/runner/run_grade.py` | 채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기 |
| `python/runner/term/` | `collect.py` · `quiz.py` · `emit.py` — `bin/report-term` 의 세 명령 |
| `../../resource/term/prompts/ask.md` | 사람에게 묻는 세션의 프롬프트 글 |

전량 목록은 `python/runner/README.md` 에 있다(`tools/gen_readme.py` 가 생성).

## 이 모듈이 소유하는 것 (Owns)

`src/term/**` · `resource/term/**` · `test/term/**`. 소유하지 않는 것 — 용어 DB 의 꼴(`src/codewiki/python/machine/terms_db.py`)과 봉인.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../core/` | `pipeline` · `measure` 를 import 한다 |
| 여기 → `../common/python.py` | 해석기 탐색 |
| 여기 → `../common/evidence.py` | `collect.py` 가 자식 프로세스로 불러 봉인된 Mode 1 산출물을 판정한다 |
| 여기 → `../codewiki/` | **import 하지 않는다.** 봉인된 `terms-db.json` 을 읽을 뿐이다 — `test/core/test_import_isolation.py` 가 잰다 |
| `bin/report-term` → 여기 | 세 명령을 자식 프로세스로 띄운다 |
