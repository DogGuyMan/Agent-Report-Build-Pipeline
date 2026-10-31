---
name: term-benchmark
description: Use before a Mode 2 design review whenever a Plan or Spec is about to be judged — "용어 이해도 점검", "이 Plan 에서 내가 모르는 용어", "용어 시험", "term benchmark", or when spec-review-dashboard is about to start and the reader's mental model of the Plan's vocabulary has not been measured. Runs a human-facing multiple-choice benchmark (3 questions per term, 5 choices each with "모르겠다" last), fills in the runner's answer sheet, grades it through report-term, and emits terms.json for the Mode 2 glossary. The CLI never asks anything — the asking is this skill's job.
---

# Term Benchmark (Mode 1.5 — 용어 이해도 점검)

## 한 줄 요약

인공지능 벤치마크를 사람 쪽으로 뒤집은 것이다. **정답지 → 객관식 → 정답률 → 확실/모름.** (3문항 규칙, 2026-08-29. 애매 는 5문항 시절의 산출물에만 남아 있다)

인공지능 벤치마크는 사람이 만든 정답지로 기계를 채점한다. 여기서는 기계가 만든 정답지로 사람을 채점한다.
목적은 성적이 아니라 **다음에 나올 설계 검토 보고서의 용어집에 무엇을 실어야 하는지를 실제로 재는 것**이다.
"이 독자는 `PageRank` 를 안다" 를 짐작으로 적으면 용어집이 장식이 된다. 그래서 물어본다.

## When to use

- **Mode 2(설계 검토) 직전.** `spec-review-dashboard` 를 부르기 전에 이것을 먼저 돈다.
  Mode 2 의 `data.ts` 에 있는 `terms` 배열은 이 스킬의 산출물로 채워진다
- 사용자가 **"이 Plan 에서 내가 모르는 용어가 뭔지"** 를 짐작이 아니라 실제 응답으로 알고 싶을 때
- 사용자가 "용어 이해도 점검", "용어 시험", "term benchmark" 라고 부를 때

**쓰지 않는 때:**

- **코드베이스 용어 DB(`terms-db.json`)가 없을 때.** 정답지가 없으면 시험을 낼 수 없다.
  Mode 1(코드베이스 위키)을 먼저 완료하라고 안내하고 **멈춘다.** 정답을 LLM 이 지어내서 채우지 않는다
- **봉인이 없을 때도 멈춘다.** `report-term collect` 가 `machine/evidence.py` 로 판정해 봉인(`<저장소>/docs/codegraph/manifest.json`)이
  없거나 깨졌으면, 또는 받은 용어 사전이 봉인 자리의 것이 아니면 exit 1 로 멈춘다. 에이전트는 Mode 1 을 대신 돌리지 않는다 —
  사용자에게 아래 생성 명령을 알리고 끝낸다. 봉인 뒤 소스가 움직였다는 경고는 시험을 막지 않는다. 대신 `term-candidates.json` 의
  `evidence.stale` 을 첫 줄로 사용자에게 알리고, `known` 중 `stale: true` 인 용어는 **출제하지 않거나** 문항 `source` 뒤에
  `(낡음 — 봉인 뒤 파일이 바뀜)` 을 붙인다. `evidence.uncommitted` 가 참이면 "이 정답지는 이 기계에만 있다" 도 알린다
- 단순히 낱말 뜻을 설명해 달라는 요청일 때. 그건 시험이 아니라 답변이다

## 전제 — 하나라도 없으면 착수하지 않는다

| 전제 | 확인 방법 | 없을 때 무엇을 하는가 |
|---|---|---|
| `report-term` CLI | `which report-term` | PATH 에 없다. 사용자에게 보고하고 **중단.** 경로를 지어내지 않는다 |
| 봉인된 코드베이스 용어 DB | `ls <저장소>/docs/codegraph/terms-db.json <저장소>/docs/codegraph/manifest.json` | Mode 1 을 먼저 돌리라고 안내하고 **중단.** 아래 생성 명령을 함께 알려 준다 |
| 검토할 Plan 파일 | `ls <plan.md>` | 어느 Plan 을 볼지 사용자에게 묻는다. 저장소를 뒤져 임의로 고르지 않는다 |
| Plan 저자가 답할 수 있는 상태 | 사용자가 지금 대화에 있는가 | **중단.** 이 스킬은 처음부터 끝까지 사람에게 묻는 절차다. 사람이 없으면 할 일이 없다 |

코드베이스 용어 DB 는 Mode 1 이 만들고 마지막 단계 `seal-artifacts` 가 봉인한다. 사람이 Mode 1 저장소의 뿌리에서 돌린다
(두 저장소로 갈리기 전에는 이 저장소, 갈린 뒤에는 codebase-wiki):

```bash
.venv/bin/python runner/run_mode1.py <저장소>
# → <저장소>/docs/codegraph/terms-db.json + manifest.json   (계약: docs/contract-mode1-artifacts.md)
#   끝나면 docs/codegraph/ 를 커밋한다
```

## Workflow — 7단계

**층이 둘이다 — CLI 와 실행기.** 아래 7단계는 이 스킬이 사람에게 물어 가며 손으로 도는 길이다.
그 위에 실행기가 따로 있어 기계 단계를 이어 돌린다:

```bash
.venv/bin/python runner/run_mode1_5.py <plan.md> --workdir <작업 디렉토리> --terms-db <저장소>/docs/codegraph/terms-db.json
```

`runner/run_mode1_5.py` 의 단계는 `collect → [사람 차례] → grade → emit` 이다. 실행기에는 출제 칸이 없다 —
문항지(`questions.json`)는 이 스킬이 쓰고, 실행기는 그것을 기계로 검사해 정답을 뺀 기입란(`answer-sheet.json`)을 깐다.
`--ask` 를 주면 실행기가 대화형 `claude` 세션을 띄워 이 스킬을 부른다(헤드리스 `-p` 가 아니다 — 사람에게 되묻는 자리라서).
`--only` / `--skip` 으로 단계를 고르고, `--dry-run` 은 무엇이 돌지만 보이고 끝낸다.

**답안(`answers.json`)이 없으면 실행기는 사람 차례에서 멈춘다.** 출제와, 사람에게 묻고 기입란을 채우는 일은
이 스킬의 몫이다.

### 1. 전제 확인

```bash
which report-term
ls <plan.md> <저장소>/docs/codegraph/terms-db.json
```

네 전제를 위 표대로 확인한다. 하나라도 없으면 **여기서 멈추고 보고한다.** 다음 단계로 넘어가지 않는다.

### 2. 후보를 모은다

```bash
cd <작업 디렉토리>          # 산출 파일이 여기 쌓인다
report-term collect <plan.md> <저장소>/docs/codegraph/terms-db.json
# → <작업 디렉토리>/term-candidates.json
```

산출 형태:

```json
{
  "plan": "<plan.md>",
  "known": { "용어": { "kind": …, "module": …, "where": …, "means": …, "neighbors": [] } },
  "newConcepts": ["C-19", "…"]
}
```

- `known` — 코드베이스 용어 DB 와 Plan 본문의 **교차**다. 정답(`means`)이 이미 있다
- `newConcepts` — Plan 이 새로 만든 개념이다. **정답이 없다.** 4단계에서 Plan 저자에게 묻는다

`collect` 가 잡는 것은 식별자 꼴 **세 가지뿐**이다 — 결정 코드(`C-19`·`U5`), 파일명(`*.json`),
배열 필드(`calls[]`). 그래서 3단계가 필요하다.

### 3. 자연어 용어를 사람이 보충한다

`WarmUp`·`PageRank`·`인용 원점` 같은 개념어는 기계가 가려낼 수 없다. **Plan 을 직접 읽고** 이해에
필요한 개념어를 골라 `known` 과 같은 형식으로 보탠다.

보탠 항목마다 **출처를 적는다** — `<plan.md>:412` 처럼 줄 번호까지. 출처 없이 보탠 용어는
"이 스킬이 지어낸 것" 과 구별되지 않는다.

뜻(`means`)을 이 단계에서 쓸 때는 **Plan 본문에 실제로 적힌 서술만** 옮긴다. Plan 이 그 용어를 정의하지
않았다면 그건 `known` 이 아니라 4단계로 보낼 **신규 개념**이다.

### 4. 신규 개념의 정답을 Plan 저자에게 묻는다

**LLM 이 지어내지 않는다.** `newConcepts` 와 3단계에서 정의를 찾지 못한 용어를 **한 개념씩**
`AskUserQuestion` 으로 묻는다.

- 묻는 문장: "`C-19` 은 이 Plan 에서 무엇을 가리킵니까?"
- 선택지로 초안 두세 개를 내밀되 **"직접 쓰겠다"** 를 항상 남긴다.
  초안은 Plan 본문에서 읽은 문맥으로 만든다. 문맥이 없으면 선택지를 만들지 말고 그냥 묻는다
- 사용자가 준 답을 그 용어의 `means`(정답 문구)로 삼는다. 이 문구가 5단계 출제의 정답지가 된다

정답이 정해지지 않은 용어는 **출제하지 않는다.** 정답 없는 문항은 채점이 불가능하다.

### 5. 출제 — 한 용어씩, 3문항 × 5지선다

용어마다 객관식 **3문항**을 낸다. 정답은 그 용어의 `means` 다. (2026-08-29 사용자 변경 — 5문항은 첫 시험 100문항에서 피로가 실측됐다)

- `AskUserQuestion` 으로 **한 용어씩** 묻는다. 여러 용어를 한 질문에 몰아넣지 않는다
- 문항마다 보기는 **실제 뜻 4개 + 마지막에 "모르겠다"** 로 **정확히 5개**다.
  개수가 문항마다 다르면 찍어서 맞을 확률이 달라져 정답률을 문항끼리 견줄 수 없다

문항지를 파일로 낸다면 `questions.json` 꼴로 쓴다(`runner/run_mode1_5.py` 의 `validate_questions`
가 검사하는 꼴이다). 그 파일을 실행기에 주면 정답을 뺀 기입란 `answer-sheet.json` 이 나온다.

**응답을 세지 않는다.** 맞고 틀림은 `report-term grade` 가 문항지와 대조해 센다. 이 스킬이 할 일은
기입란의 `UserAns` 칸을 사용자의 응답으로 채우는 것뿐이다:

```json
{ "plan": "<plan.md>",
  "questions": [
    { "QNum": 1,
      "Term": "C-19",
      "Question": "C-19 은 무엇을 가리키는가?",
      "AnsChoices": {"1": "…", "2": "…", "3": "…", "4": "…", "5": "모르겠다"},
      "UserAns": 2 } ] }
```

- `UserAns` — 사용자가 고른 보기 번호(1부터). `5` 는 "모르겠다"
- **빈 칸을 남기지 않는다.** 채점기가 거부한다 — 안 푼 것과 모르는 것은 다르기 때문이다
- `QNum` · `Term` · `Question` 은 **손대지 않는다.** 채점기가 문항지와 대조하고, 다르면 멈춘다

채운 파일을 `answers.json` 이라는 이름으로 둔다.

출제 규율은 아래 별도 절에 있다. **그 절을 읽지 않고 출제하지 않는다.**

### 6. 채점

```bash
report-term grade answers.json questions.json
# → term-grades.json
#   확실 N · 애매 N · 모름 N
```

**인자가 둘이다.** 채운 기입란에는 정답이 없고 문항지에만 있어서, 둘이 만나야 채점이 된다.
아귀가 안 맞으면(빈 칸 · 보기 밖 번호 · 어긋난 용어) 채점하지 않고 무엇이 틀렸는지 적고 멈춘다.

채점 구간(사용자가 확정한 값이다. 임의로 바꾸지 않는다):

| 조건 | 판정 |
|---|---|
| "모르겠다" 2회 이상 | **모름** — 정답률과 무관하다. 찍어서 맞힌 것을 안다고 세지 않는다 |
| 맞힌 수 2~3 (정답률 67% 이상) | **확실** |
| 맞힌 수 0~1 | **모름** |

**애매 는 이 규칙이 내지 않는다.** 5문항 시절(2026-08-29 첫 시험까지)의 산출물과 `Term.mental` 타입에만 남아 있다.

집계를 사용자에게 보이고 **"이 판정이 맞습니까"** 를 한 번 묻는다. 사용자가 "이건 사실 아는데
문항이 이상했다" 고 하면 그 용어를 다시 출제하거나 판정을 사용자 말대로 고친다.
**기계의 판정보다 사용자의 자기 보고가 앞선다** — 재는 대상이 사용자 본인이기 때문이다.

### 7. 산출

```bash
report-term emit term-grades.json
# → terms.json          용어 전량. { "용어": { TermMeans, UserMentalValue } }
# → term-study-note.md  모름·애매만, 정답률 낮은 순
```

`terms.json` 을 Mode 2 로 옮기는 방법을 **사용자에게 안내한다**:

> `report-spec init <slug>` 이 만든 `data.ts` 의 `terms: []` 자리에 옮겨 적는다.
> 그 `data.ts` 는 **원본 문서 옆**에 산다 — 원본이 `specs/YYYY-MM-DD-<slug>-design.md` 면
> `specs/<slug>/`, `plans/YYYY-MM-DD-<slug>.md` 면 `plans/<slug>/` 다. 자리를 단정하지 말고
> `init` 이 알려 준 경로를 그대로 쓴다.
> `{ "용어": { TermMeans, UserMentalValue } }` 를
> `{ id, label, short, kind, mental }` 로 바꾼다 — `TermMeans` → `short`,
> `UserMentalValue` → `mental`(`"확실"|"애매"|"모름"`), `kind` 는
> `"decision"|"artifact"|"concept"|"tool"` 중 하나를 사람이 고른다.

**자동으로 import 하지 않는다.** `data.ts` 는 사람이 읽는 원고이고, 옮기면서 뜻을 다듬는 것이
이 단계의 일부다.

## 출제 규율 (non-negotiable)

- **오답 보기는 그럴듯해야 한다.** 명백히 틀린 보기만 넣으면 정답률이 100% 로 나오고 채점이 무의미해진다.
  가장 값싼 방법은 **같은 갈래의 다른 용어 정의를 오답으로 쓰는 것**이다 —
  `term-candidates.json` 의 `known` 에서 `kind` 나 `module` 이 같은 항목의 `means` 를 가져온다
- **보기 순서를 섞는다.** 정답이 늘 첫 번째나 늘 두 번째에 오면 사용자가 위치로 맞힌다
- **정답지에 없는 것을 묻지 않는다.** 이 시험은 사용자가 **아는지를 재는** 것이지 모르는 것을
  찾아내려고 괴롭히는 것이 아니다. `known` 과 `newConcepts` 밖으로 나가지 않는다
- **한 문항은 한 가지만 묻는다.** "A 이면서 B 인 것은?" 처럼 두 조건을 겹치면 어느 쪽을 몰라서
  틀렸는지 알 수 없다
- **"모르겠다" 선택지는 항상 마지막(5번)에, 항상 이 문구 그대로.** 위치나 문구가 흔들리면 사용자가
  그것을 고르는 비용이 문항마다 달라진다
- **보기는 정확히 5개다** — 실제 뜻 4개 + "모르겠다". 문항마다 개수가 다르면 찍어서 맞을 확률이
  달라지고, 그러면 정답률을 문항끼리 견줄 수 없다
- **문항 수는 3이다.** 2026-08-29 첫 시험(용어 20개 × 5문항 = 100문항)에서 사용자가 피로를 보고해 5 에서 3 으로 줄였다.
  맞힌 수 2~3 확실 / 0~1 모름. 이 수를 임의로 바꾸지 않는다 — 바꿀 때는 `runner/term/quiz.py` 의
  `QUESTIONS_PER_TERM` 을 고친다(`runner/run_mode1_5.py` 는 그것을 import 한다). 보기 수(`CHOICES_PER_QUESTION`)도 같은 자리다

## Style rules

- **읽는 사람은 배경 지식이 없다.** 객체지향을 갓 배운 대학 1학년 눈높이다. 문항 문구도 그 눈높이로 쓴다.
  용어를 설명하려고 다른 어려운 용어를 쓰지 않는다
- **문항을 스크립트로 자동 생성하지 않는다.** 보기의 그럴듯함은 기계가 만들 수 없다.
  자동 생성한 보기는 예외 없이 티가 나고, 티가 나는 순간 정답률이 실제 이해도와 무관해진다
- **한 번에 한 용어씩 묻는다.** 여러 용어를 한 질문에 몰아넣으면 사용자가 지치고, 지친 응답은
  이해도가 아니라 피로도를 잰다
- 용어가 20개를 넘으면 **먼저 사용자에게 목록을 보이고 우선순위를 확인한다.**
  전부 물으면 100문항이 된다

## Common pitfalls

- **LLM 이 사용자의 지식 상태를 안다고 가정한다** — 이 스킬의 존재 이유가 그 가정이 틀리기 때문이다.
  LLM 이 매긴 것은 초안이고, 사용자가 고친다. 6단계에서 판정을 보이고 한 번 더 묻는 절차를 건너뛰지 않는다
- **확실로 판정된 용어를 용어집에서 뺀다** — 빼지 않는다. `terms.json` 에는 **전부** 실린다.
  표시를 달리하는 것은 Mode 2 컴포넌트의 일이다. 학습 노트(`term-study-note.md`)에서만 빠진다
- **코드베이스 전체를 출제한다** — 이 Plan 이 요구하는 용어만 낸다.
  코드베이스 용어 DB 는 C++ 저장소 기준 200개 남짓이고, 그걸 다 물으면 1,000문항이 된다
- **CLI 에 묻는 기능을 넣으려 한다** — `report-term` 에 `quiz` 명령은 없다. 일부러 없다.
  도구는 결정론적인 부분(수집·채점·산출)만 하고 판정하지 않는다. 묻는 것은 이 스킬의 일이다.
  실행기(`runner/run_mode1_5.py`)도 출제하지 않는다 — `--ask` 일 때 대화형 세션을 띄워 이 스킬에
  넘길 뿐이고, 그렇지 않으면 사람 차례에서 멈춘다
- **C++ 용어를 짧은 이름으로 찾는다** — `terms-db.json` 의 C++ 키는 `SJH::Material` 처럼
  네임스페이스를 포함한다(C# 키는 단순 이름이다). Plan 본문이 `Material` 이라고만 쓰면
  `collect` 가 잡지 못한다. 그런 용어는 3단계에서 사람이 이어 붙인다
- **`means` 를 비운 채 문항지를 쓴다** — `emit` 이 그 문구를 그대로 용어집의 `TermMeans` 로
  넘긴다. 비어 있으면 뜻 없는 용어집이 나온다
- **맞힌 수를 손으로 센다** — 세지 않는다. 옛 `answers.json`(`{용어: {correct, dontKnow}}`)은
  더 이상 받지 않고 거부된다. 사람이 세던 자리를 없앤 것이 이번 변경의 요점이다
- **`UserAns` 를 빈 칸으로 남긴다** — 채점기가 멈춘다. 사용자가 답을 안 준 문항은 다시 묻는다.
  "모르겠다"(5번)로 대신 채우지 않는다 — 안 푼 것과 모르는 것은 다르다
- **작업 디렉토리를 옮겨 가며 명령을 돈다** — 세 명령 모두 산출 파일을 **현재 디렉토리**에 쓴다.
  중간에 `cd` 하면 다음 명령이 앞 단계의 파일을 찾지 못한다

## 산출물

| 파일 | 누가 만드나 | 누가 읽나 | 어디로 가나 |
|---|---|---|---|
| `term-candidates.json` | `report-term collect` | 이 스킬 (3~5단계) | 중간 산물. 남겨 두면 재출제에 쓴다 |
| `questions.json` | 출제자(이 스킬 또는 Mode 1.5 실행기) | `report-term grade` | 중간 산물. **정답이 들어 있다 — 사용자에게 보이지 않는다** |
| `answer-sheet.json` | 실행기(`run_mode1_5.py`) | 사람 | 정답을 뺀 기입란. 이것을 채워 `answers.json` 으로 둔다 |
| `answers.json` | **이 스킬** (사용자가 고른 보기 번호를 `UserAns` 에 적는다) | `report-term grade` | 중간 산물 |
| `term-grades.json` | `report-term grade` | 사용자(집계 확인) · `report-term emit` | 중간 산물 |
| `terms.json` | `report-term emit` | 사람이 읽고 옮긴다 | **Mode 2 `data.ts` 의 `terms` 배열** |
| `term-study-note.md` | `report-term emit` | 사용자 | 공부할 것. 모름·애매만, 정답률 낮은 순 |

## 아직 재어 보지 않은 것

- **이 시험이 실제 이해도와 얼마나 맞는지는 표본 1건뿐이다.** 2026-08-29 첫 시험(5문항 규칙, 용어 20개): 확실 6 · 애매 3 · 모름 11 —
  모름 11개가 전부 Plan 의 결정 코드·지표 표기였고, 사용자가 판정을 그대로 확정했다. 3문항·2/3 경계라는 값은 사용자가 정한 것이지 관측에서 나온 것이 아니다
- **"모르겠다" 2회 규칙이 너무 세거나 약한지도 아직 모른다.** 정답률이 높은데 모름으로 떨어지는
  사례가 반복되면 사용자에게 보고한다. 혼자 고치지 않는다
