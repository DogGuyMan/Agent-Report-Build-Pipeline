# RESUME — 러너 단계 기계 리팩터링 (3단계 중 2단계 완료 · 3단계 계획 확정)

> 작성 2026-09-11 · 브랜치 `refactor/runner-common-axis` · 최신 커밋 `f30a6e7` · `main` 보다 27 커밋 앞
> 저장소 `$REPO_ROOT` (= `report-builder`)
> **이 문서가 이 작업의 단일 진입점이다.** 앞선 `RESUME-2026-09-08-…` 은 이 문서가 대체한다.

## TL;DR + 바로 다음 한 걸음

`runner/` 의 실행기 셋을 **공통 단계 기계**(`runner/pipeline.py`) 위로 올리는 3단계 작업이다.
**1·2단계는 끝났고 게이트가 초록이다.** 3단계(Mode 1)는 **계획서가 확정됐고 착수 전이다.**
2026-09-11 에 사용자가 3단계의 미결 셋을 판정했고, 단계·산출물 이름 12개를 전부 새로 정했다.

**바로 다음 할 일 — 개정 계획서(v2) Task 2 부터 실행한다.** Task 1 은 끝났다(🔵 `f88265a`).

    계획서(에이전트용)  docs/superpowers/plans/2026-09-11-runner-mode1-v2.md       Task 2~13, 전부 코드 포함
    앞선 판             docs/superpowers/plans/2026-09-11-runner-mode1.md          Task 1 만 유효. Task 2 앞에서 물렸다
    요약(사람용)        docs/superpowers/plans/2026-09-11-runner-mode1-요약.md      §1~§3 유효. 달라진 것은 v2 의 "개정 이유" 절
    실행 방식           이 세션에서는 executing-plans (파이썬 편집마다 사용자가 diff 를 보고 판단)

**2026-09-11 오후 판정 — 자유 함수를 단계에 종속시킨다.** `layers.py` · `prompts.py` 같은 자유 함수 모음을 두지 않는다.
한 단계만 쓰는 계산·프롬프트는 그 단계 클래스의 `@staticmethod`, 둘 이상이 쓰면 믹스인. 파일 꼴(읽기·쓰기·검사)만
산출물 옆(`context.py` · `diff.py`). v2 계획서의 "규칙 R4" 와 "함수 → 소속 대조표" 가 전부다.
**착수 전 사용자 판정 셋** — v2 끝의 표: ① 믹스인 vs 복제 · ② `test_run_mode1.py:757` 한 줄 · ③ D15 두 걸음.

**⚠ 착수 전 확인 둘**
1. 요약 §4-② (D15 를 두 걸음으로 나눔 — 이번엔 "다시 수집할지 판정"까지만) 에 사용자 이견이 없는지.
   §4-① 은 확정됐다(아래 "확정된 결정").
2. **이 세션의 사용자 규칙**: *"파이썬 파일을 고치기 전에 무엇을 왜 바꾸는지 보이고 확인을 받는다."*
   사용자가 2026-09-11 세션에 한해 걸었다. **새 세션은 다시 물어라** — 유지할지 말지.
   서브에이전트에 시킬 때는 "구현 전에 diff 를 보고하고 승인을 기다려라" 를 프롬프트에 넣는다.

## 지금 상태 — 다시 잰 것 (2026-09-11)

### 브랜치와 커밋

`refactor/runner-common-axis`. 워킹 트리는 **깨끗하다** — 미추적 둘만 있다(사용자 것, 건드리지 않는다):
`docs/overturn/2026-07-05-번복기록-분석보고서.md` · `runner/runner_presudo.md`.

| 커밋 | 무엇 |
|---|---|
| `f30a6e7` | 단계·산출물 이름 12개 확정 (계획 · 요약 · 스펙) |
| `4110b21` | 전량 그래프에서 `warmup` 을 빼고 `warmup-save` 가 직접 훑는 것으로 확정 |
| `bb7be52` | 3단계 계획서의 사람용 요약 |
| `a66a107` | 3단계 실행 계획 |
| `5974a73` | 번복 기록 0004 · 재개 문서에 D14 재번복 반영 |
| `d6efbb1` | D14 를 `warmup-diff.json` 으로 재번복 · D17(claim 파일) 신설 |
| `196df24` … `62c88e4` | 2단계 — `pipeline.py` 신설, Mode 2 · 1.5 이주, 문서 |

### 게이트 (2026-09-11 실측)

| 게이트 | 지금 | 비고 |
|---|---|---|
| `pytest -q` | **562 통과 · 19 건너뜀** | 3단계 기준선 |
| `npm run typecheck:py` | 0 errors | |
| `test/test_no_any.py` | 3 통과 · 7파일 덮음 | 3단계 Task 12 에서 `mode1/*` 추가 |
| `gen_readme --check` | 4개 일치 | |
| `xmldoc check` | **레퍼런스 579 · 문제 266** — 알려진 빨강 | 1·2단계가 심볼을 옮겨 마커가 어긋났다. **3단계 뒤 한 번에** 재주입. 지금 고치지 마라 |
| `npm test` · `typecheck` · `doctor` | 이번 세션에 안 돌림 | 2단계 완료 시점 초록 |

## 단계 현황

| 단계 | 무엇 | 계획서 | 상태 |
|---|---|---|---|
| 1 | `measure.py` 추출 · 파사드 · import 부작용 제거 · `Any` 게이트 | `plans/2026-09-08-runner-common-axis.md` | ✅ |
| 2 | `pipeline.py` 신설 · Mode 2 · 1.5 이주 | `plans/2026-09-08-runner-pipeline.md` | ✅ |
| **3** | Mode 1 을 `mode1/` 패키지로 · 증분/전량 그래프 · `changes.json` · 재개 JSON · 이름 12개 | `plans/2026-09-11-runner-mode1.md` | **계획 확정 · 착수 대기** |

## 2026-09-11 에 확정된 것 — 다시 논쟁하지 말 것

### ① 낱말 — "매니페스트" 는 옛 판의 지문이고 diff 가 아니다

| 파일 | 역할 |
|---|---|
| `snapshot.json` (← `warmup.json`) | **옛 판의 지문** — 지난 조사 때 파일마다 찍은 해시 둘(바이트 · 선언) |
| `changes.json` (새 파일) | 지문과 지금 소스를 **대조한 결과** — 유효 · 재읽기 · 위치만 · 삭제됨 + 파급 넓힌 `targets` |
| `codegraph.json` | 구조 지도. 바뀌었는지는 모른다 |

사용자가 인용한 우화("조수의 메모는 사라지고 지시서만 남았다")는 인계 문서 결함 ②를 다른 말로 쓴 것이다.
조수(`warmup.status()`)는 **이미 기계**다. 고칠 것은 메모가 파일이 아니었다는 것 하나.

### ② 전량 그래프에는 `detect-changes` 가 없다 (B안 · 요약 §4-①)

대조할 옛 지문이 없는데 대조 단계를 돌리지 않는다. 끝의 `snapshot-sources` 가 **직접 훑어** 지문을 찍는다.
스펙 D13 그림이 그대로 맞다. 두 안 모두 `collect-graph` 에 `--force` 가 필요했다(앞선 계획에서 빠졌던 것).
graphify 의 매니페스트 운용(늘 갱신되는 색인)이 참고가 됐다. **A안(전량에도 warmup)은 물렸다** — 번복 기록 0004 의 모양.

### ③ D14 ×2 — `detect-changes` 가 `changes.json` 을 쓰고 `annotate-symbols` 가 지시서와 양방향 대조

09-08 "계획에 싣기" → 09-10 "경고만"(소유 경계) → **09-11 "diff 를 러너 소유 파일로"**. 셋째 안이 앞의 두
제약(파일에 남긴다 / `machine/` 안 건드린다)을 둘 다 만족한다. 대조는 **양방향** — 넓으면 $50 사고, 좁으면 레코드 누락.
`삭제됨` 은 diff 에 싣기만 하고, 지우는 것은 결함 ④ 와 같은 자리에서.

### ④ D17 — 실행 둘이 겹칠 때 claim 파일. push 그대로. **결함 ③ 뒤**

한 실행 안에서는 `survey_plan.pack` 이 파일을 겹치지 않게 나눠 충돌이 없다. 메모리 락은 자식 프로세스·별개
실행 경계를 못 넘는다. 배치 id 가 위치 기반이라 지금 넣으면 남의 배치를 막는다.

### ⑤ 단계·산출물 이름 12개 (사용자가 하나씩 골랐다)

    증분:  lang-hint ▶ lang-decide ▶ detect-changes ▶ collect-graph ▶ schedule-batches ▶ annotate-symbols
           ▶ snapshot-sources ▶ verify-terms ▶ outline-wiki ▶ write-wiki ▶ publish-wiki ▶ verify-wiki
    전량:  같되 detect-changes 없음 (11개)

| 옛 → 새 | 파일 |
|---|---|
| `lang-select` → `lang-hint` + `lang-decide` | `lang-select.json` |
| `warmup` → `detect-changes` | `changes.json` |
| `prep` → `collect-graph` | `codegraph.json` |
| `survey-plan` → `schedule-batches` | `batches.json` (← `survey-plan.json`) |
| `survey` → `annotate-symbols` | `terms-reading.json` |
| `warmup-save` → `snapshot-sources` | `snapshot.json` (← `warmup.json`, **읽기만 이주**) |
| `terms` → `verify-terms` | `terms-db.json` |
| `wiki-catalogue` → `outline-wiki` | `outline.json` (← `wiki-plan.json`) |
| `wiki-pages` → `write-wiki` | `docs/wiki/*.md` |
| `build` → `publish-wiki` · `check` → `verify-wiki` | — |

옛 이름은 `ALIASES` 로 `--only` 에서만 산다. `machine/warmup.py` 의 `DEFAULT_CACHE` 는 손대지 않는다.
**스펙의 결정 본문은 옛 이름 그대로다** — 번복 이력이 그 이름으로 적혀 있어서. 스펙 머리의 "이름 확정" 절이 대응표다.

### ⑥ D4 표현 — `lang-hint` 실패는 `SKIP → 다음`

`FAIL → lang-decide` 간선이 아니다. 같은 효과이고 관문 아닌 단계의 실패를 "실패"라 부르지 않는다.

### 앞선 재개 문서에서 그대로 유효한 것

D0·D1·D2·D5·D6·D7·D8·D9·D10·D11·D12·D13·D15·D16 은 `RESUME-2026-09-08` 의 "확정된 결정" 절 그대로다.
`pipeline.py` 의 공개 API 와 Mode 2 이주 본보기도 그 문서에 있다 — **3단계 코드는 그것을 그대로 따른다.**

## 3단계에서 판정이 남은 것

| 어디 | 무엇 | 언제 |
|---|---|---|
| 요약 §4-② | D15 두 걸음 (이번엔 "다시 수집할지 판정"만) | 착수 전 |
| Task 4 끝 | `collect-graph` 를 `collect` + `facts` 로 쪼갤지 | Task 4 뒤 |

## 병렬 작업 충돌 매트릭스

| 파일·자리 | 누가 | 이 작업 |
|---|---|---|
| `runner/**` (`mode1/` 신설 포함) | **이 작업** | 소유 |
| `runner/wiki/prep.py` | 이 작업 — **한 파일만** (`--diff` · `--force`) | D15 로 열린 경계 |
| `machine/**` · `viz/**` | 다른 작업 | 읽기만. `DEFAULT_CACHE` 도 안 건드린다 |
| `machine/comments.xml` · `# <include …/>` 751곳 | xmldoc 재주입 작업 | **3단계 뒤 한 번에.** 건드리지 마라 |
| `docs/overturn/2026-07-05-…` · `runner/runner_presudo.md` | 사용자 (미추적) | 담지 마라 |
| 결함 ③④ (`merge_shards` · 배치 id) | `HANDOFF-2026-09-07-warmup-increment-unreachable.md` | **이 작업 뒤.** 고칠 자리가 3단계로 옮겨간다 |

## 가드레일 · 규약

- 브랜치 `refactor/runner-common-axis`. `main` 에서 하지 않는다.
- **커밋은 Task 마다.** `[tag] : subject` 소문자 한 줄 한국어, 빈 줄, `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. **`git add -A` 금지** — 경로를 좁힌다.
- **TDD.** 시험 먼저, 실패 확인, 구현, 통과. 계획서가 시험 코드를 전부 담고 있다.
- **`Any` 금지.** `object` + 좁히기(`measure.as_map` 등). `test/test_no_any.py` 가 게이트.
- **`# <include …/>` 블록** — 새로 심지 않는다. 정의를 옮기면 위 세 줄 블록을 함께 지운다. `xmldoc check` 가 느는 것은 정상.
- **코드 주석에는 현 상황만.** 날짜 · 수치 · 확신도 · 설계 철학 금지.
- **`runner/test_run_mode1.py`(963줄)를 고치지 않는다.** 파사드 재수출로 그대로 통과해야 한다. 옮긴 게 아니라 없앤 이름의 시험만 지우고 이름을 보고한다.
- **실제 `annotate-symbols` 를 돌려 검증하지 마라.** 세션당 약 $0.5. `--dry-run` 과 순수 함수 시험까지만.
- **파이썬 편집 전 확인** — 위 TL;DR 의 세션 규칙. 새 세션은 유지 여부를 먼저 묻는다.

## 포인터

| 문서 | 무엇 |
|---|---|
| `docs/superpowers/plans/2026-09-11-runner-mode1.md` | **3단계 계획 (에이전트용).** Task 12개 |
| `docs/superpowers/plans/2026-09-11-runner-mode1-요약.md` | 사람용 요약. 판정은 여기서 |
| `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` | 스펙. 결정 18건. 머리에 "이름 확정" 절 |
| `docs/superpowers/specs/runner-stage-machine/out/report.html` | Mode 2 보고서 (재생성 가능) |
| `docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md` | 앞선 재개 문서. `pipeline.py` API · Mode 2 본보기 · 1·2단계 상세는 여기 |
| `docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md` | 결함 ③④. 🔴 리팩터링 후속 |
| `docs/overturn/README.md` | 번복 기록 4건 · 검사표 5항목. **남의 안을 물리치기 전에 읽는다** |
| `docs/decisions/0007-xmldoc-include-deprecated.md` | xmldoc 폐지 예정. 재주입 때 `emit_xml()` 속성 함께 |

## 변경 이력

- 2026-09-11 — 최초 작성. `RESUME-2026-09-08` 을 대체. 3단계 계획서 확정, 미결 셋 판정(B안 · D15 두 걸음은 미확인 · prep 쪼개기는 Task 4 뒤), 이름 12개 확정, 번복 기록 0004, 세션 규칙(파이썬 편집 전 확인) 기록.
