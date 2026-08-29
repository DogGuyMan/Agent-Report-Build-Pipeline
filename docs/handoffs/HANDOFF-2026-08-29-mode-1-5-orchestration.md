# HANDOFF ① — Mode 1.5 계획의 위상 정렬과 실행 체계 (오케스트레이터용)

> 🟡 **부분 대체됨 (2026-08-29 03:20)** — TL;DR 과 §1 "세계의 상태" 는 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 가
> 최신이다. **재개는 그 문서부터 읽어라.** §0 슬롯 분배 · §3 위상 정렬 · §4 소유 매트릭스 · §5 하네스 · §7 규약은 여전히 여기가 정본이다.

> ~~**이 문서가 Mode 1.5 구현의 단일 진입점이다.**~~ 새 세션은 위 RESUME 문서부터 읽는다.
> 계획서 `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` 는 심화 자료이지 시작 전제가 아니다 —
> 각 Task 의 코드는 그 계획서에 있고, **이 문서는 그것을 어떤 순서로 누가 하는가**를 정한다.

---

## TL;DR + 바로 다음 한 걸음

**어디까지 왔나 (2026-08-29 갱신)** — 계획서 **10개 Task 전부 완료.** 6.1(스킬)은 슬롯 C 가 썼고 오케스트레이터가 검토·커밋했다(`1c22f65`).
**Mode 1.5 의 CLI 파이프라인 `collect → grade → emit` 이 end-to-end 로 완주**했고, Mode 2 쪽 연동(`Term.mental` · 이해도 컬럼 ·
init 스켈레톤의 `terms: []` 자리)도 끝났다.

**바로 다음 한 걸음** — ⚖ **사용자가 실제로 시험을 쳐 본다.** 그 전에 사용자 결정이 하나 필요하다: **시험 재료(`terms-db.json`)를
어디서 얻을 것인가.** 이 저장소는 Python 프로젝트라 `terms_db.py` 의 입력(`codegraph.json`)을 자기 자신에게서 만들 수 없다.
여러 세션을 열 거라면 아래 §0 의 슬롯 분배를 따르라.

**오케스트레이터의 역할** — 사용자가 명시했다: *"너의 역할은 Mode 2 마저 제작하면서 방금 제작한 Plan 의
오케스트레이터가 되어야 한다."* 즉 이 문서를 읽는 세션은 **직접 코드를 쓰는 것이 아니라** 서브에이전트에게
Task 를 배분하고, 결과를 검토하고, 사용자 판정이 필요한 지점에서 멈춰 묻는다.

---

## 0. 여러 세션을 열 때 — 슬롯 분배 (2026-08-29)

남은 Task(5.1 → 5.2 → 6.1)는 앞이 정한 필드명을 뒤가 참조하는 **직렬 사슬**이다. 여기서 병렬로 얻을 게 없다.
그래서 추가 세션의 가치는 **이 계획서 밖**에 있다. 네 슬롯으로 가른다.

| 슬롯 | 역할 | 읽을 것 | 소유 파일 | 착수 시점 |
|---|---|---|---|---|
| **A** | 오케스트레이터 | 이 문서 | `scripts/term/*` · `src/*` · `test/*` · `scripts/init.mjs` | 지금 (진행 중) |
| **B** | Mode 1 — 코드베이스 위키 | HANDOFF ③ Mode 1 절 + `RESUME-2026-08-28-track-c.md` | `codegraph/*.py` (**`terms_db.py` 제외**) | **지금** |
| **C** | Mode 1.5 스킬 저작 (Task 6.1) | HANDOFF ③ Mode 1.5 절 + 계획서 Task 6.1 | `~/.claude/skills/term-benchmark/SKILL.md` | **지금** — CLI 3개 명령이 확정됐다 |
| **D** | Mode 2 실사용 | HANDOFF ③ Mode 2 절 + `spec-review-dashboard` 스킬 | **다른 저장소**의 `docs/superpowers/specs/<slug>/` | **지금** |

### 파일 충돌 매트릭스

| 파일 | A | B | C | D |
|---|---|---|---|---|
| `scripts/term/*` · `src/*` · `test/*` | **소유** | — | — | 읽기만 |
| `codegraph/terms_db.py` | 읽기만 | **건드리지 말 것** (A 가 참조) | — | — |
| `codegraph/normalize.py` 의 **출력 키** | — | **바꾸지 말 것** — `terms_db.py` 가 `from`/`to`·`id`/`depends_on` 을 읽는다 (간접 의존) | — | — |
| `codegraph/` 나머지 | — | **소유** | — | — |
| `CLAUDE.md` | 소유 | Track C 절만 | — | — |
| `~/.claude/skills/term-benchmark/` | 검토 | — | **소유** | — |
| 다른 저장소 `specs/` | — | — | — | **소유** |

**커밋 충돌 방지** — 각 슬롯은 `git add <자기 경로>` 로 좁힌다. `git add -A` 금지. 인덱스에 남의 파일이 있으면
`git status --porcelain` 으로 확인하고 자기 것만 스테이징한다.

**슬롯 D 가 가장 가치가 크다.** 나머지는 이 저장소 안에서 도는 일이지만, D 만이 "도구가 실제 문제에 쓸모 있는가"를
답한다. 보완점은 보고서 끝 `## 컴포넌트 후보` 절로 **반복 횟수와 함께** 보고만 한다 — 그 자리에서 컴포넌트를 만들지 않는다.

**슬롯 C 가 알아야 할 CLI 실측** — `report-term` 의 명령은 `collect` · `grade` · `emit` 셋이다(`quiz` 는 제거됨 — 문항
출제는 스킬의 일). `grade` 의 입력 `answers.json` 은 `{ "용어": { correct, dontKnow, means } }` 꼴이고,
`emit` 이 내는 `terms.json` 은 `{ "용어": { TermMeans, UserMentalValue } }` 꼴이다. 디스패처가 명령어 이름을
소비하므로 스크립트는 파일 경로만 받는다.

---

## 1. 세계의 상태 — 2026-08-29 재측정

| 항목 | 값 |
|---|---|
| 저장소 | `$REPO_ROOT` (`~/report-builder` 는 **존재하지 않는다**) |
| 브랜치 | `feat/report-builder` |
| HEAD | `6e66190 [feat] : init 스켈레톤에 Mode 1.5 용어집 연결 자리 추가` |
| 미커밋 | `docs/prompt/checklist.yaml` 하나 (사용자 메모, 의도적 미추적) |
| Node 테스트 | 64개 통과 (`npm test`) |
| Python 테스트 | 31개 통과 (`.venv/bin/python -m pytest codegraph/ -q`) |
| 타입 검사 | 통과 (`npm run typecheck`) |

**직전 세션(2026-08-28~29)에서 확정된 것** — 이 문서를 읽는 세션은 다시 논쟁하지 않는다:

| 결정 | 내용 |
|---|---|
| 3-mode 구조 | Mode 1(코드베이스 위키) → **Mode 1.5(용어 이해도)** → Mode 2(설계 검토) |
| 세 갈래 | 사람의 이해 상태 — 확실 / 애매 / 모름 |
| 채점 | ~~한 용어당 5문항. 4~5 확실 / 2~3 애매 / 0~1 모름. "모른다" 3회~~ → **2026-08-29 14:40 변경: 3문항. 맞힌 수 2~3 확실 / 0~1 모름. "모른다" 2회 이상이면 모름.** 첫 시험 100문항의 피로 실측이 사유 |
| 판정 주체 | LLM 추정 → 사용자가 고친다 |
| 출제 범위 | Plan 을 이해하는 데 필요한 용어만 (코드베이스 DB ∩ Plan + Plan 신규 개념) |
| Plan 신규 개념의 정답 | **Plan 저자가 직접 쓴다** |
| 자료 구조 | `{ "용어": { TermMeans, UserMentalValue } }` — 객관 정답과 주관 이해도를 필드로 분리 |
| Mode 2 용어집 | **전부 싣되** 확실한 것은 흐리게 표시 |
| CLI | 바이너리 3개 — `report-wiki` · `report-term` · `report-spec`. **분리 완료.** `report-term` 은 `collect` · `grade` · `emit` |
| 산출물 `<script>` | **1개 예산이 이미 찼다** (용어 그래프 런타임). 새 런타임은 그 번들에 합친다 |

---

## 2. ⚠ 함정 — 재개 전에 반드시 읽을 것

### (가) ~~계획서의 섹션 번호 하나가 틀렸다~~ — Task 1.1 에서 `# ── 8.` 로 처리됨

계획서 Task 1.1 Step 1 이 `codegraph/test_normalize.py` 에 `# ── 12.` 섹션을 추가하라고 적었다.
🔵 실측 — 그 파일의 마지막 섹션은 **`# ── 7.`** 이다(`test_normalize.py:221`). **`# ── 8.` 로 붙여라.**
계획서 본문은 고치지 않았다. 이 문서가 우선한다.

### (나) `test/components.test.mjs` 의 import 에 `Glossary` 가 없다 — Task 5.1 프롬프트에 반영됨

계획서 Task 5.1 이 `Glossary` 렌더 테스트를 추가하라고 하는데, 🔵 실측 — 그 파일 5번째 줄의 import 목록에
`Glossary` 가 **없다.** Task 5.1 수행자는 import 에 `Glossary` 를 먼저 더해야 한다.

### (다) 옛 산출물은 기준이 아니다

`CLAUDE.md` 최상단 `## ⚠ 방향` 절을 반드시 읽어라. 2026-07-27 자 HTML 2건을 "정본"으로 삼아 새 출력을
맞추려는 시도는 **후퇴**다. 직전 세션에서 세 Phase 가 이 결함으로 취소됐다. **외부 저장소
`GlobalMedia-OpenGL-ComputerGraphics` 를 참조 자료로 삼는 Task 는 이 계획에 없다.**

### (라) 도구는 판정하지 않는다

`scripts/term/quiz.mjs` 는 **사람에게 묻지 않는다.** 채점만 한다. 묻는 절차는 Phase 6 의 Skill 이 맡는다.
이 경계를 코드에서 흐리면(예: `quiz.mjs` 가 `readline` 으로 직접 묻기 시작하면) 이 저장소의 핵심 규율이 깨진다.

### (마) 커밋 정책

**계획서의 각 Task 는 "Step N: 커밋" 을 포함한다. 그러나 서브에이전트는 커밋하지 않는다.** 서브에이전트는
구현 + 검증 + 보고까지만 하고, **오케스트레이터가 사용자 승인 후 커밋**한다. 메시지 형식은
`personal-commit-messages` 스킬 — 소문자 `[tag] : 한국어 한 줄`, 본문 없음, ASCII 구두점만, 트레일러 없음.

---

## 3. 위상 정렬 — Task 10개

### 의존 그래프

```
L0 ── 직렬. 다른 모든 것의 전제
│
│   Task 0.1  scripts/dispatch.mjs + test/dispatch.test.mjs
│             (bin 3개가 이것을 import 한다)
│
├──────────────┬──────────────┬──────────────┐
▼              ▼              ▼              │
L1 ── 병렬 3갈래. 파일이 겹치지 않는다        │
│              │              │              │
Task 0.2       Task 1.1       Task 2.1       │
bin/report-*   codegraph/     scripts/term/  │
bin/report     terms_db.py    collect.mjs    │
               test_normalize test/term      │
               .py            .test.mjs      │
│              │              │              │
▼              │              ▼              │
Task 0.3       │         Task 3.1 ═══════════╡ 파일 충돌
CLAUDE.md      │         scripts/term/       │ test/term.test.mjs 를
               │         quiz.mjs            │ 2.1 → 3.1 → 4.1 이
               │         test/term.test.mjs  │ 순서대로 append 한다
               │              │              │
               │              ▼              │
               │         Task 4.1 ═══════════╛
               │         scripts/term/emit.mjs
               │         test/term.test.mjs
               │              │
               └──────┬───────┘
                      ▼
L4 ── Task 5.1  src/types.ts · components/terms.tsx · theme.css · test/components.test.mjs
         │      (4.1 의 TermMeans/UserMentalValue 이름과 mental 값을 참조)
         ▼
      Task 5.2  scripts/init.mjs
         │
         ▼
L6 ── Task 6.1  ~/.claude/skills/term-benchmark/SKILL.md
                (CLI 3개 명령이 다 있어야 절차를 쓸 수 있다)
                ⚖ 사용자가 실제로 시험을 쳐 본다
```

### 레벨표

| 레벨 | Task | 병렬 | 성격 | 앞 의존 |
|---|---|---|---|---|
| **L0** | 0.1 ✅ `3c32fc6` | — | 직렬 | 없음 |
| **L1** | 0.2 ✅ `2316d6c` · 1.1 ✅ `8069517` · 2.1 ✅ `1d31dc9` | **3개 동시** | 서브에이전트 | 0.1 (0.2 만). 1.1·2.1 은 사실상 무의존 |
| **L2** | 0.3 ✅ `af03897` · 3.1 ✅ `6c0cca6` | 2개 동시 | 서브에이전트 | 0.3 ← 0.2 / 3.1 ← 2.1 (**파일 충돌**) |
| **L3** | 4.1 ✅ `5d09bd9` | — | 서브에이전트 | 3.1 (**파일 충돌**) |
| **L4** | 5.1 ✅ `506221a` | — | 서브에이전트 | 4.1 (이름 참조) |
| **L5** | 5.2 ✅ `6e66190` | — | 오케스트레이터 직접 (위임 비용 > 작업) | 5.1 |
| **L6** | 6.1 ✅ `1c22f65` | — | 슬롯 C 저작, 오케스트레이터 검토 | 0.2 · 2.1 · 3.1 · 4.1 전부 ✅ |

### 직렬이 **강제**되는 구간 — 두 종류뿐

| 구간 | 종류 | 이유 |
|---|---|---|
| `2.1 → 3.1 → 4.1` | **파일 충돌** | 셋 다 `test/term.test.mjs` 에 append 한다. 동시에 쓰면 서로 덮는다. 순서 자체는 무관하나 **한 번에 하나만** |
| `4.1 → 5.1` | **논리 의존** | 5.1 이 `TermMeans`/`UserMentalValue` 필드명과 `"확실"|"애매"|"모름"` 값을 참조한다. 4.1 이 정하기 전에 쓰면 이름이 어긋난다 |
| `0.1 → 0.2` | **논리 의존** | `bin/report-*` 가 `scripts/dispatch.mjs` 를 import 한다 |
| `5.1 → 5.2` | **논리 의존** | 5.2 의 `data.ts` 템플릿 주석이 5.1 의 `mental` 필드를 언급한다 |
| `전부 → 6.1` | **논리 의존** | Skill 이 CLI 3개 명령을 절차로 적는다 |

### 임계 경로

```
0.1 → 2.1 → 3.1 → 4.1 → 5.1 → 5.2 → 6.1     (7단계)
```

`0.2 → 0.3` 과 `1.1` 은 곁가지다. **임계 경로가 `test/term.test.mjs` 충돌 때문에 길어졌다.**
💭 이 충돌을 없애려면 세 Task 가 각자 테스트 파일을 갖게 하면 되지만(`test/term-collect.test.mjs` 등),
계획서가 이미 한 파일로 적었고 파일 셋이 한 흐름의 연속 단계라 붙여 두는 쪽이 읽기 좋다. **순서로 푼다.**

---

## 4. 파일 소유 매트릭스 (충돌 방지)

| 파일 | 소유 Task | 다른 Task 가 건드리면 |
|---|---|---|
| `scripts/dispatch.mjs` · `test/dispatch.test.mjs` | 0.1 | — |
| `bin/report` `bin/report-spec` `bin/report-term` `bin/report-wiki` | 0.2 | — |
| `CLAUDE.md` | 0.3 (명령 절만) | **오케스트레이터가 다른 절을 고칠 수 있다.** 0.3 은 `## 명령` 절 밖을 건드리지 않는다 |
| `codegraph/terms_db.py` | 1.1 | — |
| `codegraph/test_normalize.py` | 1.1 (append 만) | 기존 7개 섹션을 **건드리지 않는다** |
| `scripts/term/collect.mjs` | 2.1 | — |
| `scripts/term/quiz.mjs` | 3.1 | — |
| `scripts/term/emit.mjs` | 4.1 | — |
| **`test/term.test.mjs`** | **2.1 생성 → 3.1 append → 4.1 append** | **동시 편집 금지.** 앞 Task 가 끝난 뒤에만 |
| `src/types.ts` · `src/components/terms.tsx` · `src/theme.css` | 5.1 | **기존 필드·클래스 제거 금지** (컴포넌트는 추가만) |
| `test/components.test.mjs` | 5.1 (append + import 1줄) | 기존 테스트를 건드리지 않는다 |
| `scripts/init.mjs` | 5.2 | — |
| `~/.claude/skills/term-benchmark/SKILL.md` | 6.1 | 저장소 밖. 사본을 `.claude/skills/term-benchmark/` 에 |

**절대 건드리지 않는 파일** (어느 Task 도 소유하지 않음):
`scripts/build.mjs` · `scripts/check.mjs` · `src/runtime/term-graph.ts` · `src/components/{badges,tables,blocks,BeforeAfter,VerdictFooter}.tsx` ·
`docs/superpowers/specs/llm-load-reduction/*` — 이것들은 Mode 2 의 완성된 부분이다. 계획서 File Structure 가
`scripts/build.mjs [수정]` 이라고 적었으나 **실제 Task 중 build.mjs 를 고치는 것은 없다.** 계획서의 오기다.

---

## 5. 서브에이전트 하네스 — 프롬프트를 짤 때 반드시 넣을 것

각 Task 를 서브에이전트에 넘길 때 아래 여섯 블록을 빠뜨리지 않는다. HANDOFF ② 가 그 완성 예시다.

| 블록 | 내용 |
|---|---|
| `[ROLE]` | 저장소 절대경로 · 브랜치 · Task 하나의 목표 한 문장 |
| `[HARD RULES]` | **커밋 금지** · TDD(실패 테스트 → 실행 확인 → 구현 → 통과 확인) · 주석은 한국어 · `scripts/*.mjs` 직접 실행 가드 규약 · "검증됨"/"입증" 단어 금지 |
| `[BOUNDARIES]` | 위 §4 에서 그 Task 의 행만 뽑아 넣는다. **소유하지 않는 파일 목록을 명시** |
| `[VERIFIED FACTS]` | 이 문서 §1·§2 에서 그 Task 에 해당하는 실측 줄번호. "이 보고를 믿지 말고 재검증하라" 한 줄 |
| `[STEP n]` | 계획서에서 **그 Task 의 코드 블록을 통째로 복사**해 넣는다. 계획서를 읽으라고 시키지 않는다 |
| `[VERIFY]` + `[REPORT]` | 정확한 명령과 기대 출력. 보고 형식 `DONE / DONE_WITH_CONCERNS / BLOCKED` + 변경 파일 + 검증 출력 |

**서브에이전트가 돌아오면 오케스트레이터가 할 것** — 보고를 믿지 말고 `npm test` / `pytest` 를 **직접
다시 돌린다.** 통과하면 사용자에게 커밋 승인을 묻는다. 두 단계 검토(구현 검토 → 규약 검토)는
`superpowers:subagent-driven-development` 스킬 절차를 따른다.

---

## 6. 자동 Task Queue — 오케스트레이터의 실행 절차

```
1. L0  Task 0.1 을 서브에이전트에 넘긴다 (HANDOFF ② 가 그 프롬프트다)
   └ 돌아오면 npm test 직접 실행 → 44 → 48 확인 → 사용자에게 커밋 승인
2. L1  Task 0.2 · 1.1 · 2.1 을 **한 메시지에서 서브에이전트 3개로** 동시에 띄운다
   └ 셋 다 돌아오면 각각 검증 → 커밋 승인 (3개 커밋)
3. L2  Task 0.3 · 3.1 을 동시에
   └ 3.1 은 2.1 이 만든 test/term.test.mjs 가 있어야 시작 가능. 있는지 확인 후 띄운다
4. L3  Task 4.1
5. L4  Task 5.1
6. L5  Task 5.2
7. L6  Task 6.1 은 **오케스트레이터가 직접 쓴다** — 프롬프트를 쓰는 일이라 위임하면 한 겹이 더 생긴다
   └ 완성되면 ⚖ 사용자에게 실제 시험을 쳐 보라고 요청. 문항 난이도 판정은 사용자 몫
```

**멈춰서 물어야 하는 지점** (오케스트레이터가 혼자 정하지 않는다):
- 각 레벨의 커밋 승인
- Task 1.1 실행 후 `means` 가 정답지로 쓰기에 빈약하면 — LLM 보강 단계를 더할지
- Task 2.1 실행 후 `pickTerms` 오탐이 많으면 — 코드 블록 안 등장만 세도록 좁힐지
- Task 6.1 후 사용자 시험 결과 — 문항이 너무 쉽거나 어려운지

---

## 7. 가드레일과 규약 (Step 0 에서 확보)

| 항목 | 규약 | 출처 |
|---|---|---|
| Node 테스트 | `npm test` (pretest 가 `.tmp/lib.mjs` 를 번들). **`node --test test/` 는 Node 25 에서 죽는다** — 인자 없이 | `CLAUDE.md` 명령 절 |
| Python 테스트 | `.venv/bin/python -m pytest codegraph/ -q` | 실측 |
| 타입 검사 | `npm run typecheck` | `package.json` |
| 직접 실행 가드 | `if (process.argv[1] && process.argv[1].endsWith("파일명.mjs")) { CLI 본체 }` — import 시 순수 함수만 | `CLAUDE.md` 규약 절 |
| 커밋 메시지 | `[tag] : 한국어 한 줄`. 본문·트레일러 없음. `—` `→` `·` 금지, `-` `->` `,` 로 | `personal-commit-messages` |
| 컴포넌트 | **추가만.** props 제거·의미 변경 금지 | `CLAUDE.md` 작업 규약 |
| 확신도 표기 | 🔵 는 이번 세션에서 읽은 `file:line` 또는 실제 돌린 명령의 출력만 | `CLAUDE.md` 작업 규약 |
| 금지 단어 | "검증됨" "입증" "증명" | 계획서 Self-Review |
| 거울 함정 | 지표 레지스트리·플러그인 구조·추상 인터페이스가 나오면 그 자체가 실패 | `CLAUDE.md` 함정 절 |

---

## 8. 포인터

| 문서 | 역할 |
|---|---|
| `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` | **Task 별 코드의 출처.** 서브에이전트 프롬프트는 여기서 코드를 복사한다 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-build-targets.md` | **HANDOFF ②** — Task 0.1 의 붙여넣기용 프롬프트 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` | **HANDOFF ③** — Mode 1 / 1.5 / 2 각 에이전트의 역할 정의 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-skill.md` | **HANDOFF ④** — Task 6.1 `term-benchmark` 스킬 저작 프롬프트 (슬롯 C 용) |
| `CLAUDE.md` | 저장소 규약. `## ⚠ 방향` 절부터 |
| `docs/handoffs/RESUME-2026-08-28-track-c.md` | Track C(Mode 1) 재개 문서. 이 문서와 **별개 갈래** |

**이 문서가 대체하는 것** — 없음. Mode 1.5 는 신규다.

---

## 9. 변경 이력 (추가만)

- 2026-08-29 — 최초 작성. 계획서 완성 직후, 구현 0줄 시점.
- 2026-08-29 (같은 날 늦게) — L0~L3 완료 반영. §0 슬롯 분배 신설. 서브에이전트가 실측으로 잡은 계획서 오류 3건
  (간선 키 `from/to`, 모듈 키 `id/depends_on`, 디스패처가 명령어 소비)은 계획서 본문에 정정 주석으로 들어갔다.
  `report-term quiz` 명령은 제거됐다.
- 2026-08-29 (더 늦게) — 5.1 · 5.2 완료. 9/10. 6.1 을 슬롯 C 로 넘기고 HANDOFF ④ 작성. 원래 "오케스트레이터 직접"
  이었던 6.1 규정은 CLI 미확정이 전제였고 그 전제가 사라져 위임 가능해졌다.
- 2026-08-29 (마지막) — 6.1 완료. **10/10.** 슬롯 B 가 `.claude/agents/mode-1-codebase-wiki.md` (Claude Code 서브에이전트
  정의)를 만들었다 — 계획서에 없던 산출물이나 HANDOFF ③ Mode 1 절을 에이전트 형식으로 옮긴 것이라 방향에 맞는다.
  핸드오프 ② 에 완료 배너를 달았다(원칙 5 — 발신 측 정리를 늦게 한 것).
- 2026-08-29 (더 늦게, 에이전트 정의 세션) — HANDOFF ③ 을 `.claude/agents/*.md` 3개로 옮기던 중 실측으로
  **"CLI 4단계 / CLI 4개 명령" 오기 3곳을 정정**했다(§0 슬롯 C 행 · §3 의존 그래프 L6 · §3 직렬 강제 표).
  `report-term` 명령은 `collect` · `grade` · `emit` **셋**이다 - `quiz` 제거(Task 3.1) 가 이 문서에 반영되지 않았다.
  §6 실행 절차 7번의 "Task 6.1 은 오케스트레이터가 직접 쓴다" 는 이미 §9 앞 항목이 뒤집었으므로 그대로 둔다.
