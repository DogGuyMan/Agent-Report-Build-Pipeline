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

## Notes (오케스트레이터용 — 펜스 밖)

- 돌아오면 파일을 **직접 열어 읽는다.** frontmatter 형식, 7단계 명령의 정확성(특히 인자 순서), 금지 단어를 본다.
- 통과하면 `.claude/skills/term-benchmark/SKILL.md` 로 복사하고 커밋한다:
  `[docs] : term-benchmark 스킬 - 사람에게 묻는 절차`
- 그다음 ⚖ **사용자에게 실제 시험을 요청한다.** 재료: `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` + 아직 없는
  `terms-db.json` — 이 Plan 은 Track C 계획이고 그 저장소의 codegraph.json 은 외부에 있다. **이 저장소 자체를 대상으로
  terms_db.py 를 돌릴 수는 없다** (Python 프로젝트라 roslyn/clang-uml 입력이 없다). 시험 재료를 어디서 얻을지는 사용자 결정이다.
