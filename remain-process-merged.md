# 통합 남은 작업 체크리스트

> `remain-process.md`와 `remain-process-2.md`를 기반으로, 현재 git 워킹 트리 상태(Unstaged changes)를 반영하여 카테고리별로 재구성한 남은 작업 목록입니다.

## 🚨 1. 최우선 대기 및 동기화 (Git 충돌 방지)

현재 `run_mode1.py`, `run_mode1_5.py`, `CLAUDE.md` 등에 **커밋되지 않은 타 세션의 작업**이 진행 중입니다. 이 작업들이 커밋된 후 충돌을 피하여 진행해야 할 항목들입니다.

- [ ] **스킬 문서 현행화 (커밋 대기 후 진행)**
  - `runner/run_mode1_5.py`에서 `author` 단계가 제거됨에 따라, `~/.claude/skills/term-benchmark/SKILL.md` 내용(머리말 두 층 설명, Common pitfalls의 층 구분 3줄) 수정 필요.
  - 이 문서의 Mode 1.5 실행 절차도 함께 확인.
- [ ] **Mode 1 Plan Task 1~2 (커밋 대기 후 진행)**
  - Task 1: `survey_plan.py`가 `depends_on`을 id가 아닌 이름으로 내도록 수정.
  - Task 2: `dep_excerpt` 회귀 시험(id≠name 픽스처) 추가.
  - *경고: 현재 수정 중인 `runner/run_mode1.py`와 강하게 충돌할 수 있으므로 착수 전 반드시 확인 필요.*

---

## 🏗️ 2. 심볼 파악 파이프라인 (Mode 1 & Plan Tasks)

`docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md` 기준 미완료 Task 및 병목 해결 과제입니다.

- [ ] **Task 3:** `resolve_target()` 조상 rollup 사다리 구현.
- [ ] **Task 4:** `synthesize_record()` 외부 심볼·파일 합성.
- [ ] **Task 5:** `resolve_uses()` 배선 (못 푼 것은 실패가 아니라 '근거 없음'으로 격하).
- [ ] **Task 6:** 배치 프롬프트에 `external` 탈출구 안내.
- [ ] **Task 7:** 실측 레코드 골든 대조.
- [ ] **Task 8:** 재실행 및 실측 갱신 (⚠️ **과금 발생 유의**).
- [ ] **성능 병목 해결 후속 조치**
  - `depends_on` 및 `uses.to`를 이름으로 통일한 후, 층 장벽 유지 여부 측정으로 결정.
  - 세션 고정비(82%) 절감을 위한 배치 크기(K3) 재검토 (재측정 후 진행).

---

## 🧪 3. Mode 1.5 & Mode 2 실행 및 연계

CLI 명령 실행 및 결과물을 산출하는 단계입니다.

- [ ] **Mode 1.5 잔여 실행 단계**
  - 문답 진행 후 `answers.json` 도출.
  - `grade` 단계 실행 → `term-grades.json`.
  - `emit` 단계 실행 → `terms.json` 및 `term-study-note.md` 생성.
- [ ] **Mode 2 연계 및 보고서 생성**
  - 대응 설계 문서(`docs/superpowers/specs/...symbol-resolution-survey-design.md`) 부재, 작성 필요.
  - `report-spec init` → `build` → `check` 완주.
  - Mode 1.5와 Mode 2 연결을 위해 `terms.json`의 결과를 `data.ts`에 수동으로 옮겨 적기 (`data.ts` 결정 표 및 `report.tsx` 서사 구성).

---

## 🤔 4. 사용자 판단 및 정책 결정 (보류 항목)

개발자/사용자의 명시적인 승인이나 결정이 필요한 항목입니다.

- [ ] **Mode 1.5 `questions.json` 처리 방향 결정**
  - 오케스트레이터가 작성한 수동 사본을 유지하여 문답을 이어갈지, 폐기하고 스킬 4단계부터 재돌릴지 결정.
- [ ] **스킬 심볼릭 링크 전환 여부**
  - `~/.claude/skills/`의 홈 사본을 저장소 심볼릭 링크로 대체할지 여부 결정 (현재는 내용만 동기화됨).
- [ ] **A-4 / A-5 Plan 승인 대기**
  - 중복 스키마 5곳 접기(A-4), 심볼 해석 플랜 실행(A-5) 착수 여부 승인.
- [ ] **`check_terms` 잔여 실패 83건 대응**
  - LLM 오류가 아닌 수집기(`griffe/pycalls`) 공백에 의한 실패. 삭제 시 증거가 사라지므로 보존 중.
- [ ] **`pickTerms` 키 매칭 오탐 이슈**
  - FQN 매칭 도입 시 `get`, `git`, `main` 등 짧은 이름 매칭 오탐 발생 중 (구조 결정 문제로 일단 보류).

---

## 🧹 5. 문서 현행화 및 발견된 부채 (범위 밖 사항)

당장의 실행 차단 원인은 아니지만, 향후 유지보수를 위해 정리해야 할 문서 낡음 및 탐지된 결함들입니다.

- [x] **문서 내용 갱신** (2026-08-31 수행)
  - [x] `machine/CLAUDE.md`: 제목을 `# machine/ — 기계축` 으로. 죽은 경로 정정 —
        `pytest codegraph/`(3곳) → `pytest machine/`, Owns 의 `codegraph/**` → `machine/**`,
        `여기 → scripts/*` 행 삭제. 표에서 `render_modules.py` · `render_classes.py` ·
        `demermaid.py`(→ `viz/`)와 `run_mode*.py`(→ `runner/`)를 빼고 실재 파일로 교체.
        Mode 1.5 도표에서 `author` 제거, Mode 1 에 `lang-select` 추가.
        🔵 실측 재측정 — `pytest machine/` **188 통과 · 19 건너뜀**(201 → 188).
  - [x] `runner/CLAUDE.md`: Mode 1 을 아홉 → **열 단계**(`lang-select` 추가), LLM 칸 둘 → 셋.
        `report-wiki 제외` 는 **사실이 아니었다** — `bin/report-wiki:15` 가 `runDispatch` 를 쓴다.
        `runDispatch` 를 안 쓰는 것은 `report` 하나다.
  - [x] `runner/run_mode1.py` 독스트링: 아홉 → 열 단계, 단계표에 `lang-select` 행 추가.
        주입 주석의 "아홉 단계" 는 `machine/terms-reading.json` 을 고치고 `xmldoc.py emit`→`inject`
        로 다시 박았다(손으로 고치면 다음 주입에 덮인다).
  - [x] `ARCHITECTURE.md`: 첫 줄 `#` 복원, 백틱/볼드 교차 6곳 복구(134 · 189 · 201 · 212 ·
        223-224 · 355), `STAGES 가 일곱` → 현재 사실로, `여덟` → 열 보강.
  - [ ] **`CLAUDE.md` — 보류.** 아래 "동시 세션" 절을 보라.

- [x] **탐지된 결함 / 분석 대상 — 셋 다 실측으로 확인됨** (2026-08-31)
  - [x] **`findNewConcepts` 오탐 — 재현됨.** `runner/term/collect.mjs` 의 패턴
        `/\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b/g` 가 `C10` · `C11` 같은 **단순 인용 id** 를 신규 개념으로
        분류한다. `D\d` 만 예외로 빠져 있고 `C`·`K`·`B` 계열은 그대로 걸린다. 같은 세 꼴을
        `viz/check.mjs` 의 `undefinedTerms` 도 쓰므로 **한쪽만 고치면 어긋난다**(주석이 못박음).
  - [x] **Mode 1 층3 토큰 폭증 — 수치 확인됨.** 근거
        `evals/runs/2026-08-30-mode1-qtvisionedit-cold-sonnet.json` 을 층별로 합산:

        | 층 | 배치 | 토큰 | 초 합 | 비용 |
        |---|---:|---:|---:|---:|
        | L0 | 11 | 7,422,631 | 1177.7 | $5.1823 |
        | L1 | 1 | 902,177 | 136.3 | $0.5983 |
        | L2 | 1 | 783,411 | 103.7 | $0.5118 |
        | **L3** | **1** | **2,054,598** | **200.3** | **$1.0518** |
        | L4 | 1 | 784,959 | 88.6 | $0.4593 |
        | **L5** | **1** | **2,894,398** | **313.7** | **$1.4201** |

        L3 은 배치 하나인데 이웃 층(L2 783K · L4 785K)의 **약 2.6배**를 썼다. 체크리스트가
        적은 "심볼 4개(Controller)에 205만" 의 205만은 맞다. 원인은 아직 좁히지 못했다 —
        배치 안 심볼 목록과 통독 파일 크기를 봐야 한다.
  - [x] **Mode 1 층5 병렬화 — 병목 확인됨.** L5(비노드 용어, K5)는 **배치가 하나뿐**이라
        층 안 병렬(K2·K4)이 걸리지 않는다. 그런데 토큰은 전 층 최대(2,894,398)이고 벽시계도
        단일 배치 최장(313.7초)이다. 💭 K5 가 "맨 마지막 별도 층" 만 정하고 **쪼개지 않아서**
        생긴 구조적 병목으로 보인다 — 판단이지 사실이 아니다.

---

## ⚠ 6. 동시 세션 경고 — 2026-08-31 19:35~ 관측

**다른 세션이 같은 작업 트리에서 Node → Python 포팅을 진행 중이다.** 내가 한 일이 아니고,
되돌리지 않았다. 관측된 것:

- `viz/*.mjs` 와 `tools/*.mjs` 가 **전부 사라졌다** — `viz/check.mjs` · `viz/init.mjs` ·
  `viz/svg.mjs` · `viz/link-paths.mjs` · `tools/python.mjs` · `tools/doctor.mjs` 가 HEAD 에는
  있고 워킹 트리에는 없다. 자리에 `viz/check.py` · `viz/svg.py` · `viz/link_paths.py` ·
  `viz/wrap_terms.py` 가 새로 생겼다.
- `test/*.test.mjs` 8개가 `test/test_*.py` 로 바뀌었다.
- `bin/report-spec` · `bin/report-term` · `bin/report-wiki` 가 **`#!/usr/bin/env python3` 인데
  본문에 `//` 주석이 남은 혼종 상태**다.

**그래서 지금 두 시험 관문이 다 빨갛다:**

| 관문 | 지금 |
|---|---|
| `npm test` | `test/wiki.test.mjs` 실패 |
| `pytest`(전체) | `test/test_init.py` 수집 단계에서 ERROR |
| `pytest machine/` | 188 통과 · 19 건너뜀 — **여기만 초록** |
| `runner/test_run_mode1.py::test_every_runner_script_path_actually_exists` | 실패(`viz/init.mjs` 없음) |

**`CLAUDE.md` 갱신을 보류한 이유가 이것이다.** 그 항목이 요구하는 것(테스트 수치 · 실제 게이트 ·
확정된 스택)이 지금 이 순간 다른 세션에 의해 바뀌고 있다. 포팅이 커밋된 뒤에 재측정해서 적는다.

**포팅 완료 후 CLAUDE.md 에 적을 것 (측정만 다시 하면 됨):**

| 항목 | 문서의 낡은 값 | 2026-08-31 19:30 실측(포팅 전) |
|---|---|---|
| 커밋 | `05869ac` | `927684f` / 태그 `v1` |
| `npm test` | 160개 | 184개 |
| pytest | `pytest codegraph/` 235 통과 | `pytest machine/ runner/ tools/ viz/` 356 통과 · 19 건너뜀 |
| 실측 날짜 | 2026-08-27 | — |
| 컴포넌트 export | 17개 | **17개 — 그대로 맞다**(`.tmp/lib.mjs` 실측) |
| Node / TS / Graphviz | v25.8.0 / 7.0.2 / 15.1.1 | **그대로 맞다** |

**게이트는 4가지가 아니라 여섯이다**(포팅 전 기준, 전부 초록이었다):

```bash
npm test                                                        # 184 통과
npm run typecheck                                               # tsc --noEmit
npm run typecheck:py                                            # pyright strict — 0 errors
.venv/bin/python -m pytest                                      # 356 통과 · 19 건너뜀
.venv/bin/python machine/xmldoc.py check                        # 레퍼런스 738건 · 문제 0건
.venv/bin/python tools/gen_readme.py --check machine runner viz tools   # README 4개 일치
```

`plans/` 지원 설명은 **이미 CLAUDE.md 에 있다**(`report-spec init <slug>` 주석과
"참조 원본의 실제 위치" 절의 2026-08-31 단락). 추가할 것이 없다.
