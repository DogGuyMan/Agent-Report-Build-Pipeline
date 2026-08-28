# HANDOFF ④ — `term-benchmark` 스킬 저작 (Task 6.1 · 슬롯 C 용 프롬프트)

> 🔴 **완료됨 (2026-08-29). 이 프롬프트를 다시 실행하지 말 것.**
> 슬롯 C 가 `~/.claude/skills/term-benchmark/SKILL.md` (223줄) 를 썼고, 오케스트레이터가 검토 후 저장소 사본
> `.claude/skills/term-benchmark/SKILL.md` 로 커밋했다(`1c22f65`). 절 구성·CLI 인자 순서·채점 구간·금지 단어 전부 실물과 대조했다.
> 이 문서는 **기록용**이다. 현재 진입점은 `HANDOFF-2026-08-29-mode-1-5-orchestration.md` 다.

> 아래 ``` 블록을 새 세션에 그대로 붙여넣는다. 자기완결이다.
> 정본 참조(읽지 않아도 됨): `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` Task 6.1,
> `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` Mode 1.5 절

```
[ROLE]
당신은 $REPO_ROOT (브랜치 feat/report-builder) 의 스킬 저작 에이전트다.
목표: Mode 1.5(용어 이해도 벤치마크)에서 **사람에게 묻는 절차**를 담은 스킬 문서
~/.claude/skills/term-benchmark/SKILL.md 를 쓴다.
CLI 는 결정론적인 부분(수집·채점·산출)만 하고 사람에게 묻지 않는다. 그 빈자리를 이 스킬이 채운다.
이 산출물은 코드가 아니라 **프롬프트**다.

[HARD RULES]
- 커밋하지 않는다. 스킬 파일은 저장소 밖(~/.claude/skills/)이라 git 과 무관하지만, 저장소 안 사본
  .claude/skills/term-benchmark/SKILL.md 도 만들지 않는다 — 오케스트레이터가 검토 후 복사·커밋한다.
- 한국어. 약어와 압축 표현을 피한다. 읽는 사람은 배경 지식이 없다고 가정한다.
- "검증됨" "입증" "증명" 이라는 단어를 쓰지 않는다.
- 스킬 형식: 첫 줄부터 YAML frontmatter (`---` / `name:` / `description:` / `---`). description 은 영어로,
  언제 이 스킬이 발동해야 하는지 트리거 문구를 담는다. 본문은 한국어 마크다운.
- 기존 스킬을 참고하되 복사하지 않는다: ~/.claude/skills/spec-review-dashboard/SKILL.md 가 같은 저장소의
  Mode 2 스킬이다. 그 문서의 절 구성(When to use / 전제 / Workflow / Style rules / Common pitfalls)을 따르면 일관된다.

[BOUNDARIES]
- 소유 파일 = 정확히 1개: ~/.claude/skills/term-benchmark/SKILL.md (신규, 디렉토리도 신규).
- 저장소 안의 어떤 파일도 만들거나 고치지 않는다. scripts/term/* 를 읽되 고치지 않는다.
- 다른 세션(슬롯 A·B·D)이 저장소 안에서 동시에 작업 중이다. git 명령은 읽기(log/status/show)만.

[VERIFIED FACTS — 2026-08-29 실측. 이 보고를 믿지 말고 파일을 열어 재확인하라]
- CLI 진입점 bin/report-term 의 명령은 collect · grade · emit 셋이다. quiz 명령은 없다 — 문항 출제는 CLI 의 일이 아니라 이 스킬의 일이다.
- 디스패처(scripts/dispatch.mjs)가 명령어 이름을 소비하므로 각 스크립트는 파일 경로 인자만 받는다.
- report-term collect <plan.md> [terms-db.json] → cwd 에 term-candidates.json
    형태: { plan, known: { "용어": { kind, module, where, means, neighbors } }, newConcepts: ["C-19", ...] }
    known = 코드베이스 용어 DB 와 Plan 본문의 교차 (정답이 이미 있다)
    newConcepts = Plan 이 새로 만든 개념 (정답이 없다 — **Plan 저자가 직접 써야 한다**)
    구현: scripts/term/collect.mjs. 식별자 꼴 세 가지만 잡는다(결정 코드 C-19·U5, 파일명 *.json, 배열 필드 calls[]).
    자연어 용어(WarmUp·PageRank)는 기계가 못 잡으므로 이 스킬이 사람 판단으로 보탠다.
- report-term grade <answers.json> → cwd 에 term-grades.json
    answers.json 형태: { "용어": { correct: 맞힌 수, dontKnow: "모른다" 고른 수, means: 정답 문구 } }
    채점(사용자 확정, scripts/term/quiz.mjs:18-21): 한 용어당 5문항. 맞힌 수 4~5 → 확실 / 2~3 → 애매 / 0~1 → 모름.
    "모른다" 3회 이상이면 정답률과 무관하게 모름.
- report-term emit <term-grades.json> → cwd 에 terms.json + term-study-note.md
    terms.json: { "용어": { TermMeans, UserMentalValue } } — 전부 실린다(확실 포함)
    term-study-note.md: 모름·애매만, 정답률 낮은 순
- 코드베이스 용어 DB 는 Mode 1 이 만든다: .venv/bin/python codegraph/terms_db.py <codegraph.json> --repo <저장소> -o <출력디렉토리> → terms-db.json
    실측: C++ 저장소 211개, C# 저장소 241개. **C++ 키는 네임스페이스를 포함한다** (SJH::Material). C# 은 단순 이름.
    이 DB 가 없으면 Mode 1.5 는 시작할 수 없다 — 전제 확인 단계에서 잡아야 한다.
- Mode 2 쪽: report-spec init 이 만드는 data.ts 에 terms: [] 자리와 옮겨 적는 법 주석이 있다. terms.json 을 자동 import 하지 않는다.
- Mode 2 의 Term 타입: { id, label, short, body?, kind: "decision"|"artifact"|"concept"|"tool", links?, mental?: "확실"|"애매"|"모름" }

========================================================================
[STEP 1] 디렉토리와 파일을 만든다
  mkdir -p ~/.claude/skills/term-benchmark

[STEP 2] SKILL.md 를 쓴다. 아래 절을 이 순서로 담는다.

frontmatter
  name: term-benchmark
  description: (영어) Use before a Mode 2 design review whenever a Plan/Spec is about to be judged — "용어 이해도 점검",
    "이 Plan 에서 내가 모르는 용어", "용어 시험", "term benchmark", or when spec-review-dashboard is about to start and
    the reader's mental model of the Plan's vocabulary has not been measured. Runs a human-facing multiple-choice
    benchmark (5 questions per term + "I don't know"), grades via report-term, and emits terms.json for the Mode 2 glossary.
    Never asks from the CLI — the asking is this skill's job.

## 한 줄 요약
  인공지능 벤치마크를 사람 쪽으로 뒤집은 것. 정답지 → 객관식 → 정답률 → 확실/애매/모름.

## When to use
  - Mode 2(설계 검토) 직전. spec-review-dashboard 를 부르기 전에 이것을 먼저 돈다
  - "이 Plan 에서 내가 모르는 용어가 뭔지" 를 실측하고 싶을 때
  - 쓰지 않는 때: 코드베이스 용어 DB(terms-db.json)가 없을 때 — 그때는 Mode 1 을 먼저 완료하라고 안내하고 멈춘다

## 전제 — 하나라도 없으면 착수하지 않는다
  표로: report-term CLI(which report-term) / terms-db.json 존재 / 검토할 Plan 파일 / Plan 저자가 답할 수 있는 상태
  각 행에 "실패 시 무엇을 하는가"

## Workflow — 7단계. 각 단계에 실행 명령과 산출 파일
  1. 전제 확인
  2. report-term collect <plan.md> <terms-db.json> — 후보를 모은다
  3. **자연어 용어 보충** — collect 는 식별자 꼴만 잡는다. Plan 을 읽고 WarmUp·PageRank 같은 개념어를 known 과 같은 형식으로 보탠다.
     보탠 것은 출처(Plan 의 줄번호)를 적는다
  4. **신규 개념의 정답을 Plan 저자에게 묻는다.** LLM 이 지어내지 않는다. AskUserQuestion 으로 한 개념씩. 답을 means 로 삼는다
  5. **출제** — 용어마다 객관식 5문항 + "모른다" 선택지. 정답지는 means. AskUserQuestion 으로 **한 용어씩** 묻는다.
     응답을 세어 answers.json 에 { correct, dontKnow, means } 로 적는다
  6. report-term grade answers.json → term-grades.json. 집계(확실/애매/모름 수)를 사용자에게 보인다
  7. report-term emit term-grades.json → terms.json + term-study-note.md.
     terms.json 을 Mode 2 의 data.ts terms 배열로 옮기는 법을 안내한다 (자동 import 하지 않는다 — 사람이 읽는 파일이다)

## 출제 규율 (non-negotiable)
  - 오답 보기는 **그럴듯해야** 한다. 명백히 틀린 보기만 넣으면 채점이 무의미하다. 같은 갈래의 다른 용어 정의를 오답으로 쓰면 그럴듯해진다
  - 보기 순서를 섞는다. 정답 위치가 한 곳에 몰리면 안 된다
  - **정답지에 없는 것을 묻지 않는다.** 모르는 것을 묻는 시험이 아니라 아는지를 재는 시험이다
  - 한 문항은 한 가지만 묻는다. "A 이고 B 인 것은?" 처럼 두 조건을 겹치지 않는다
  - "모른다" 선택지는 항상 마지막에, 같은 문구로

## Style rules
  - 읽는 사람은 배경 지식이 없다. 객체지향을 갓 배운 대학 1학년 눈높이. 문항 문구도 그 눈높이
  - 문항을 스크립트로 자동 생성하지 않는다. 보기의 그럴듯함은 기계가 못 만든다
  - 한 번에 한 용어씩 묻는다. 여러 용어를 한 질문에 몰아넣지 않는다

## Common pitfalls
  - **LLM 이 사용자의 지식 상태를 안다고 가정** — 추정은 초안이고 사용자가 고친다. 채점 결과를 보이고 "이 판정이 맞는가" 를 한 번 더 묻는다
  - **확실로 판정된 것을 용어집에서 뺌** — 전부 싣는다. 표시만 달리한다 (Mode 2 컴포넌트가 한다)
  - **코드베이스 전체를 출제** — 이 Plan 이 요구하는 용어만. collect 의 known 과 newConcepts 밖으로 나가지 않는다
  - **CLI 에 묻는 기능을 넣으려 함** — 도구는 판정하지 않는다. 묻는 것은 이 스킬이다
  - **C++ 용어를 짧은 이름으로 찾음** — terms-db.json 의 C++ 키는 SJH::Material 처럼 네임스페이스를 포함한다. Plan 본문이 Material 이라고만 쓰면 collect 가 못 잡는다. 그런 경우 자연어 보충 단계(3)에서 사람이 잇는다
  - **문항 수를 줄임** — 5문항이어야 정답률이 80% 임계에 딱 떨어진다. 4문항이면 0/25/50/75/100 이라 경계가 무의미하다

## 산출물
  표로: term-candidates.json / answers.json / term-grades.json / terms.json / term-study-note.md — 누가 읽나, 어디로 가나

[STEP 3] 자기 점검
  - frontmatter 가 파일 첫 줄에서 시작하는가
  - Workflow 7단계마다 실행 명령이 있는가
  - "검증됨" "입증" "증명" 이 없는가 (grep)
  - 저장소 안에 아무것도 만들지 않았는가 (cd $REPO_ROOT && git status --porcelain 에 내 것이 없는가)

[REPORT — 한국어로]
상태: DONE | DONE_WITH_CONCERNS | BLOCKED
만든 파일: ~/.claude/skills/term-benchmark/SKILL.md (줄 수)
절 목록:
미룬 것 / 우려: (특히 — 출제 규율 중 실제로 지키기 어려워 보이는 것)
저장소 변경: 없음 (확인)
```

---

## 슬롯 C 회신 — 실행 결과 (2026-08-29)

**상태: DONE.** 위 프롬프트의 STEP 1~3 을 전부 수행했다.

| 항목 | 결과 |
|---|---|
| 만든 파일 | `~/.claude/skills/term-benchmark/SKILL.md` — 223줄 / 13,098 바이트 |
| frontmatter | 첫 줄부터 시작. `name` + `description`(영어) 598자 — 1,024자 제한 이내 |
| 금지 단어 | `검증됨` `입증` `증명` **0건** (`grep` 확인) |
| 저장소 변경 | 없음. 슬롯 C 는 저장소 안에 아무것도 만들지 않았다 |
| 저장소 사본 | 오케스트레이터가 `.claude/skills/term-benchmark/SKILL.md` 로 복사·커밋 (`1c22f65`). `diff` 결과 두 사본 동일 |

### 절 구성 (9개 + frontmatter)

| 줄 | 절 | 비고 |
|---|---|---|
| 1 | frontmatter | 영어 트리거 문구. `spec-review-dashboard` 직전 발동을 명시 |
| 8 | 한 줄 요약 | 정답지 → 객관식 → 정답률 → 확실/애매/모름 |
| 16 | When to use | `terms-db.json` 없을 때 **멈춘다** 를 여기와 전제 표 양쪽에 |
| 29 | 전제 — 하나라도 없으면 착수하지 않는다 | 4행 표 + "없을 때 무엇을 하는가" 열 + `terms_db.py` 생성 명령 |
| 45 | Workflow — 7단계 | 단계마다 실행 명령과 산출 파일 |
| 164 | 출제 규율 (non-negotiable) | 6항 |
| 179 | Style rules | 3항 + 용어 20개 초과 시 우선순위 확인 |
| 190 | Common pitfalls | 7항 |
| 208 | 산출물 | 5행 표 — 누가 만드나 / 누가 읽나 / 어디로 가나 |
| 218 | 아직 재어 보지 않은 것 | 5문항·80%·40% 는 관측이 아니라 사용자 결정값임을 명시 |

### 프롬프트의 `[VERIFIED FACTS]` 재확인 — 전부 일치, 다만 두 가지 보탬

프롬프트가 지시한 대로 보고를 믿지 않고 파일을 직접 열었다. 🔵 2026-08-29 실측:

| 확인한 것 | 근거 | 결과 |
|---|---|---|
| 명령 셋 · `quiz` 부재 | `bin/report-term:16-20` | 일치. `grade` 는 `scripts/term/quiz.mjs` 로 간다 |
| 채점 구간 | `scripts/term/quiz.mjs:15-23` | 일치. `dontKnow >= 3` 이 정답률보다 앞선다 |
| 인자 순서 | `scripts/dispatch.mjs:16-24` | 일치. 명령 이름을 소비하고 나머지만 넘긴다 |
| `data.ts` 옮겨 적기 매핑 | `scripts/init.mjs:95-99` | 일치. 스킬 7단계 문구를 이 주석과 같은 매핑으로 맞췄다 |

**프롬프트에 없던 두 가지 (스킬에 반영함):**

1. **`known` 레코드에 필드가 2개 더 있다.** 프롬프트는 `{ kind, module, where, means, neighbors }` 5개로 적었으나
   실제로는 `source: "codegraph"` 가 항상, `hotspot: true` 가 조건부로 붙는다(`codegraph/terms_db.py:60-66`).
   출제에 쓰이지 않아 스킬 본문의 형태 예시에서는 생략했다.
2. **세 명령 모두 산출 파일을 `process.cwd()` 에 쓴다**(`collect.mjs:63` · `quiz.mjs:44` · `emit.mjs:51,54`).
   중간에 `cd` 하면 다음 명령이 앞 단계 파일을 찾지 못한다. 프롬프트에 없던 pitfall 로 추가했다.

### ⚠ 미해소 — 우려 3건

프롬프트가 명시적으로 물은 "출제 규율 중 실제로 지키기 어려워 보이는 것" 에 대한 답이다.
**셋 다 스킬 문서만으로는 닫히지 않는다.** 실제 시험 1회가 필요하다.

| # | 우려 | 왜 문제인가 | 언제 판가름 나나 |
|---|---|---|---|
| **C1** | **"오답 보기는 그럴듯해야 한다" 가 가장 약한 고리** | 스킬은 "같은 `kind`/`module` 의 다른 용어 `means` 를 오답으로 쓰라"는 수단을 준다. 그런데 `terms-db.json` 의 `means` 는 `"<모듈> 모듈의 <kind>. A, B, C 와(과) 이어져 있다."` 라는 **기계 생성 정형문**이다(`terms_db.py:57-59`). 같은 모듈의 두 용어는 앞부분이 글자까지 똑같아 오답이 정답과 구별 불가능하거나, 반대로 이웃 이름만 다르면 사용자가 **뜻이 아니라 이웃 목록으로 정답을 역추적**한다. 어느 쪽이든 정답률이 이해도가 아니라 **문항 품질**을 재게 된다 | 사용자 시험 1회. 정답률이 100% 또는 0% 로 몰리면 이 우려가 현실화된 것 |
| **C2** | **"용어 20개 초과 시 우선순위 확인" 의 경계값 20에 근거가 없다** | 100문항이면 과하다는 판단일 뿐 관측이 아니다. CLAUDE.md 의 "N값 — 근거 없는 임의값 금지" 와 같은 성격의 미결정 사안이다 | 첫 시험의 실제 용어 개수와 사용자 피로도 |
| **C3** | **`newConcepts` 정규식이 `D\d` 를 제외한다** (`collect.mjs:37`) | Mode 2 의 결정 ID(`D1`·`D2`)와 충돌을 피하려는 의도로 보이나 코드에 그 이유가 적혀 있지 않다. Plan 이 `D3` 를 **개념어**로 쓰면 `collect` 가 놓치고 3단계 사람 보충에만 의존하게 된다 | 코드 의도를 확인하지 못해 스킬에 적지 않았다. **오케스트레이터(슬롯 A)가 판단할 사안** |

### 이어서 할 일

| 순서 | 할 일 | 누가 | 상태 |
|---|---|---|---|
| 1 | 파일 검토 — frontmatter · 7단계 인자 순서 · 금지 단어 | 오케스트레이터 | ✅ 완료 |
| 2 | `.claude/skills/term-benchmark/SKILL.md` 사본 커밋 | 오케스트레이터 | ✅ `1c22f65` |
| 3 | **⚖ 시험 재료를 어디서 얻을지 결정** | **사용자** | ⏸ 대기 (아래) |
| 4 | 사용자가 실제로 시험을 쳐 본다 | 사용자 + 스킬 | ⏸ 3번 이후 |
| 5 | 시험 결과로 **C1** 판정 — 오답 보기가 실제로 기능하는가 | 오케스트레이터 | ⏸ 4번 이후 |
| 6 | **C2** 경계값 20, **C3** `D\d` 제외 의도 — 사용자에게 물어 확정 | 오케스트레이터 | ⏸ 미착수 |

**3번이 전체를 막고 있다.** ⚖ 사용자 결정 필요:

이 저장소는 Python 프로젝트라 `terms_db.py` 의 입력(`codegraph.json`)을 **자기 자신에게서 만들 수 없다**
(roslyn/clang-uml 입력이 없다). 시험 재료를 얻는 길은 셋이다:

| 길 | 재료 | 대가 |
|---|---|---|
| (가) `terms-db.json` 없이 | Plan 의 `newConcepts` 만으로 시험 | 가장 빠르다. 코드베이스 용어 0개라 **C1(오답 보기)을 시험하지 못한다** — 정답을 전부 사용자가 4단계에서 직접 쓰기 때문 |
| (나) 외부 C++/C# 저장소 | Mode 1 파이프라인을 그 저장소에 돌려 `terms-db.json` 생성 | Mode 1 완주가 선행. **C1 을 제대로 시험할 수 있는 유일한 길** |
| (다) 손으로 만든 소형 DB | 용어 10개 남짓을 직접 적어 넣음 | 중간. C1 은 시험되나 정형문 문제(진짜 원인)는 재현되지 않는다 |

**시험할 Plan 후보** — `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` (이 저장소 안. Track C 계획).

### 이 문서의 위상

**기록용이다.** 위 펜스 안 프롬프트를 다시 실행하지 말 것. 현재 진입점은
`RESUME-2026-08-29-mode-1-5-orchestrator.md` 이고, 그 다음이 `HANDOFF-2026-08-29-mode-1-5-orchestration.md` 다.
스킬 자체를 고칠 일이 생기면 `~/.claude/skills/term-benchmark/SKILL.md` 와 저장소 사본 **양쪽을 함께** 고친다 —
지금은 `diff` 가 비어 있고, 그 상태를 유지하는 것이 이 스킬의 유일한 정합성 조건이다.
