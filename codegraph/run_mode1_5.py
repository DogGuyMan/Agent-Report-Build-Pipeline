#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/run_mode1_5.py']"/>
# 용어 이해도 점검 흐름을 돌리다 사람 차례에서 멈추는 실행기.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# Mode 1.5 파이프라인을 돌리다 사람 차례에서 멈추는 파일.
# 쓰는 것: run_mode1 · 쓰이는 곳: 없음
"""run_mode1_5.py — Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.**

**왜 이것이 있는가.** Mode 1.5 는 기계 단계(후보 모으기 · 채점 · 산출)와 큰 언어 모형
단계(용어 보충 · 출제) 사이에 **사람이 직접 답해야 하는 자리**가 끼어 있다. 손으로
돌리면 명령을 네 번 치는 동안 어디에서 시간이 갔고 토큰이 얼마나 흘렀는지가 남지
않는다. 이 파일의 목적은 자동화가 아니라 **단계마다 벽시계 시간과 토큰을 붙들어
표로 내는 것**이다 — Mode 1 실행기(`run_mode1.py`)와 같은 이유다.

## 네 단계와 그 사이의 사람 차례

    collect ──▶ author ──▶ [사람 차례] ──▶ grade ──▶ emit
     기계        모형 1개    실행기가 멈춘다   기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `collect` | Plan 본문과 코드베이스 용어 사전의 교차를 모은다 | `scripts/term/collect.mjs` |
| `author`  | **자연어 용어 보충과 출제를 한 세션에서 이어 한다** | `claude -p` 1회 |
| `grade`   | 사람이 쓴 답안을 채점한다(확실 / 모름) | `scripts/term/quiz.mjs` |
| `emit`    | 용어집과 학습 노트를 낸다 | `scripts/term/emit.mjs` |

**Mode 1 과 다른 점이 정확히 하나 있다 — 사람 자리다.** Mode 1 은 처음부터 끝까지
기계와 모형만으로 돈다. Mode 1.5 는 **사람이 아는지를 재는 것**이 목적이라 사람이
답하지 않으면 잴 것이 없다. 그런데 `claude -p` 는 헤드리스라 되물을 수 없다. 사람
자리에 모형을 넣으면 모형이 답을 지어내고, 그 순간 이 도구가 재는 것은 사람의 이해도가
아니라 모형의 상상이 된다. **그래서 실행기는 답안 파일이 없으면 멈춘다.**

## 사람 차례가 요구하는 것 둘

  1. `answers.json` — 실행기가 깔아 준 기입란(`answer-sheet.json`)의 `UserAns` 칸을
     전부 채워 이 이름으로 둔 것. **필수.** 맞고 틀림은 사람이 세지 않는다 —
     `quiz.mjs` 가 문항지와 대조해 센다.
  2. `term-answer-key.json` — Plan 이 새로 만든 개념의 **뜻**. 선택.
     뜻이 없는 개념은 출제되지 않는다(채점할 수 없으므로). 사람이 여기에 뜻을 적고
     실행기를 다시 돌리면 그때 출제된다.

## 재개 — 이미 있는 산출물을 보고 할 일을 정한다

멈췄다 다시 돌리는 것이 정상 흐름이라 **재개가 이 실행기의 기본 동작**이다.
후보 파일이 있으면 `collect` 를, 문항지가 있으면 `author` 를 건너뛴다. 특히 문항을
다시 내면 사람이 이미 푼 시험과 어긋나므로 건너뛰는 것이 **정확성** 문제다.

## `questions.json` — 이 실행기가 새로 정한 형식

지금까지 문항지는 스킬이 대화 안에서 만들고 버렸다. 헤드리스로 돌리려면 파일이
있어야 한다. `answers.json` 으로 곧장 이어지도록 뜻(`means`)을 함께 싣는다.

| 열쇠 | 꼴 | 뜻 |
|---|---|---|
| `plan` | 문자열 | 이 문항지가 나온 Plan 파일 경로 |
| `terms[]` | 배열 | 출제된 용어 하나당 한 칸 |
| `terms[].term` | 문자열 | 용어 이름. `answers.json` 의 열쇠가 된다 |
| `terms[].means` | 문자열 | **정답 문구.** `emit` 이 그대로 용어집으로 넘긴다 |
| `terms[].source` | 문자열 | 이 뜻의 출처(`파일:줄`). 지어낸 것과 구별하려고 적는다 |
| `terms[].questions[]` | 배열 | **정확히 3개.** `quiz.mjs` 의 채점 구간이 그 수를 전제한다 |
| `terms[].questions[].ask` | 문자열 | 물음 한 줄. 한 문항은 한 가지만 묻는다 |
| `terms[].questions[].choices[]` | 배열 | **정확히 5개.** 실제 뜻 4개 + **마지막에 항상 "모르겠다"** |
| `terms[].questions[].answer` | 정수 | 정답 보기의 자리(0부터). 마지막 칸을 가리키면 안 된다 |
| `excluded[]` | 배열 | 출제하지 못한 개념과 그 사유. 사람이 읽는 보고다 |

## `answer-sheet.json` — 사람이 채우는 기입란

**정답이 든 `questions.json` 을 사람에게 그대로 내밀 수 없다.** 그래서 실행기가 그것을
용어 순 · 문항 순으로 펴고 정답을 뺀 기입란을 따로 깐다. 사람은 `UserAns` 에 고른 보기
번호만 적는다 — 맞고 틀림을 세는 일은 기계가 한다.

    { "plan": "…/plan.md",
      "questions": [
        { "QNum": 1,
          "Term": "PageRank",
          "Question": "PageRank 가 하는 일은?",
          "AnsChoices": {"1": "…", "2": "…", "3": "…", "4": "…", "5": "모르겠다"},
          "UserAns": "" } ] }

`Term` 을 싣는 이유는 **채점 단위가 문항이 아니라 용어**이기 때문이다(3문항을 묶어
확실/모름을 매긴다). 없으면 채점할 때 되짚을 수가 없다.

**QNum 은 두 언어에 같은 규칙으로 산다** — 여기(`flatten_questions`)와 `scripts/term/quiz.mjs`
양쪽이 같은 순서로 펴야 번호가 맞는다. 그 규칙이 어긋나면 조용히 남의 답을 채점하게 되므로,
채점 직전에 `Term` 과 물음 문구를 문항지와 대조해 **다르면 멈춘다.**

## 쓰는 법

    .venv/bin/python codegraph/run_mode1_5.py <plan.md> --workdir <작업폴더> \
        [--terms-db <terms-db.json>] [--model haiku] [--dry-run]
"""
import argparse
import json
import os
import subprocess
import sys
import time

# 이 파일은 <ROOT>/codegraph/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 재는 코드는 Mode 1 실행기에 이미 있고 시험으로 덮여 있다. 다시 짜지 않고 가져다 쓴다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as M  # noqa: E402

# 단계는 넷 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["collect", "author", "grade", "emit"]

# 모형을 부르는 단계. **하나뿐이라는 것이 이 실행기의 전제**다 — 쪼개면 프롬프트
# 캐시가 새로 서서 토큰이 부풀고, 측정값이 파이프라인의 비용이 아니라 세션 수의 함수가 된다.
AGENT_STAGES = {"author"}

# 한 용어당 문항 수. `scripts/term/quiz.mjs` 의 `QUESTIONS_PER_TERM` 과 **같은 값이어야 한다.**
# 한쪽만 고치면 채점 구간(맞힌 수 2 이상 -> 확실)이 조용히 뜻을 잃는다.
QUESTIONS_PER_TERM = 3

# "모르겠다" 는 자리도 문구도 고정이다. 흔들리면 그것을 고르는 비용이 문항마다 달라진다.
DONT_KNOW = "모르겠다"

# 한 문항의 보기 수. 실제 뜻 넷에 "모르겠다" 를 더해 다섯이다. 문항마다 다르면
# 찍어서 맞을 확률이 문항마다 달라지고, 그러면 정답률을 문항끼리 견줄 수 없다.
CHOICES_PER_QUESTION = 5

# 파일 이름은 한곳에 모은다. 스킬 문서와 어긋나면 사람이 엉뚱한 파일을 찾는다.
# `answers-template.json`(옛 이름)을 물려 쓰지 않는다 — 꼴이 통째로 달라져서, 이름을
# 물려 쓰면 지난 실행이 남긴 카운트 파일이 새 기입란인 척 조용히 섞인다.
CANDIDATES = "term-candidates.json"
ANSWER_KEY = "term-answer-key.json"
QUESTIONS = "questions.json"
SHEET = "answer-sheet.json"
ANSWERS = "answers.json"
GRADES = "term-grades.json"


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.is_agent_stage']"/>
# 이 단계가 큰 언어 모형을 부르는 자리인지 답한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 1. 단계 고르기 (파일 시스템을 보지 않는 순수 함수) ──────────────────
def is_agent_stage(stage):
    """이 단계가 큰 언어 모형을 부르는 자리인지 답한다. 토큰이 잡히는 곳은 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.plan_stages']"/>
# 네 단계 중 무엇을 실제로 돌릴지 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def plan_stages(has_candidates, has_questions, has_answers, only=None, skip=None):
    """무엇을 실제로 돌릴지 정한다. 파일 시스템을 보지 않으므로 시험이 쉽다.

    세 가지 규칙뿐이다.

      - 후보 파일이 있으면 `collect` 를 건너뛴다. 다시 모으면 덮어쓰기 때문이다.
      - 문항지가 있으면 `author` 를 건너뛴다. 다시 내면 **사람이 이미 푼 시험과
        어긋나고**, 모형을 한 번 더 부르니 돈도 두 번 든다.
      - 답안이 없으면 `grade` 와 `emit` 을 아예 넣지 않는다. 이것이 사람 차례다.
    """
    for name in list(only or []) + list(skip or []):
        if name not in STAGES:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (name, ", ".join(STAGES)))
    if only:
        return [s for s in STAGES if s in set(only)]
    out = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        if s == "collect" and has_candidates:
            continue
        if s == "author" and has_questions:
            continue
        if s in ("grade", "emit") and not has_answers:
            continue
        out.append(s)
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.human_gate_open']"/>
# 사람 차례가 아직 안 끝났는지 답한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def human_gate_open(has_answers):
    """사람 차례가 아직 안 끝났는가. 답안 파일 하나로 판정한다.

    답안이 없으면 뒤 단계는 잴 것이 없다 — 채점할 응답 자체가 없기 때문이다.
    """
    return not has_answers


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.split_new_concepts']"/>
# 새로 나온 개념을 출제할 것과 미룰 것으로 가른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 2. 정답 미정 가르기 — 기계 규칙은 하나뿐이다 ────────────────────────
def split_new_concepts(new_concepts, answer_key):
    """Plan 이 새로 만든 개념을 **출제할 것**과 **미룰 것**으로 가른다.

    규칙은 하나다 — **뜻(정답 문구)이 있느냐.** 뜻이 없으면 채점이 불가능하므로 낼 수 없다.

    **오탐인지 아닌지는 여기서 따지지 않는다.** `collect.mjs` 는 식별자 꼴 세 가지를
    글자로만 잡으므로 린트 코드(`E402`)나 임시 파일 이름이 섞여 들어온다. 그것을 기계가
    "오탐" 이라고 지워 버리면, 그 판정이 틀렸을 때 되돌릴 자리가 없다. 대신 뜻이 없으니
    자연히 출제에서 빠지고, 사람이 관문에서 목록을 보고 넘길지 뜻을 줄지 정한다.

    `(출제할 것, 미룰 것)` 두 목록을 원래 순서 그대로 낸다.
    """
    ready, held = [], []
    for t in new_concepts:
        if str((answer_key or {}).get(t) or "").strip():
            ready.append(t)
        else:
            held.append(t)
    return ready, held


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.validate_questions']"/>
# 문항지가 채점할 수 있는 꼴인지 본다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 3. 문항지 검사 — quiz.mjs 는 이것을 검사하지 않는다 ─────────────────
def validate_questions(doc):
    """`questions.json` 이 채점 가능한 꼴인지 본다. 불평 목록을 낸다(없으면 빈 목록).

    **왜 필요한가.** `quiz.mjs` 는 답안만 받아 세므로 문항지가 망가져도 모른다.
    문항이 둘뿐이거나 "모른다" 가 가운데 있어도 채점은 조용히 끝나고, 그 숫자가
    이해도라고 표에 실린다. 그 조용한 실패를 여기서 잡는다.

    검사는 판정이 아니다 — 형식이 맞는지만 본다. 문항의 **좋고 나쁨**은 기계가 볼 수 없다.
    """
    out, spots = [], []          # spots — 정답이 놓인 자리. 한곳에 몰렸는지 뒤에서 본다
    terms = (doc or {}).get("terms")
    if not isinstance(terms, list) or not terms:
        return ["문항지에 용어가 하나도 없다 — `terms` 배열이 비었거나 없다"]

    for i, entry in enumerate(terms):
        name = str((entry or {}).get("term") or "").strip()
        head = name or "(이름 없는 %d번째 용어)" % (i + 1)
        if not name:
            out.append("%s — `term` 이 비었다" % head)
        if not str((entry or {}).get("means") or "").strip():
            out.append("%s — `means`(뜻)가 비었다. 비면 용어집에 뜻 없는 항목이 실린다" % head)

        qs = (entry or {}).get("questions")
        if not isinstance(qs, list) or len(qs) != QUESTIONS_PER_TERM:
            out.append("%s — %d문항이어야 하는데 %s개다"
                       % (head, QUESTIONS_PER_TERM,
                          len(qs) if isinstance(qs, list) else "0"))
            qs = qs if isinstance(qs, list) else []

        for j, q in enumerate(qs):
            tag = "%s 문항 %d" % (head, j + 1)
            if not str((q or {}).get("ask") or "").strip():
                out.append("%s — 물음(`ask`)이 비었다" % tag)
            choices = (q or {}).get("choices")
            if not isinstance(choices, list) or len(choices) != CHOICES_PER_QUESTION:
                out.append("%s — 보기는 실제 뜻 %d개에 \"%s\" 를 더해 정확히 %d개여야 하는데 %s개다"
                           % (tag, CHOICES_PER_QUESTION - 1, DONT_KNOW,
                              CHOICES_PER_QUESTION,
                              len(choices) if isinstance(choices, list) else "0"))
                continue
            if choices[-1] != DONT_KNOW:
                out.append("%s — \"%s\" 가 **마지막** 보기가 아니다 (지금 마지막은 %r)"
                           % (tag, DONT_KNOW, choices[-1]))
            if len(set(choices)) != len(choices):
                out.append("%s — 보기가 서로 겹친다" % tag)
            ans = (q or {}).get("answer")
            if not isinstance(ans, int) or isinstance(ans, bool) \
                    or ans < 0 or ans >= len(choices):
                out.append("%s — 정답 자리(`answer`)가 보기 밖이다: %r" % (tag, ans))
            elif ans == len(choices) - 1:
                out.append("%s — 정답이 \"%s\" 를 가리킨다" % (tag, DONT_KNOW))
            else:
                spots.append(ans)

    # 정답 자리가 한곳에 몰렸는가. **보기의 좋고 나쁨은 기계가 못 보지만 자리는 볼 수 있다.**
    # 정답이 늘 첫 번째면 사람이 뜻이 아니라 위치로 맞히고, 그러면 이 시험은 이해도가
    # 아니라 눈치를 잰다. 문항이 적을 때는 우연히 몰릴 수 있으므로 여섯부터 본다.
    if len(spots) >= 6 and len(set(spots)) == 1:
        out.append("정답이 %d문항 모두 %d번 자리에 있다 — 보기 순서를 섞어야 한다"
                   % (len(spots), spots[0]))
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.unasked_known']"/>
# 출제도 안 되고 뺀 이유도 안 적힌 용어를 낸다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def unasked_known(candidates, doc):
    """후보의 `known` 중 **출제도 안 되고 뺀 이유도 안 적힌** 용어를 낸다.

    시험 범위를 좁히는 것 자체는 정당하다 — 용어 20개면 60문항이고 스킬도 그때는
    사람에게 우선순위를 먼저 물으라고 한다. 문제는 **조용히** 빠지는 것이다. 무엇이
    빠졌는지 보이지 않으면 좁힌 것인지 잊은 것인지 사람이 구별할 수 없다.

    실측 — haiku 로 돌린 첫 문항지가 `known` 20개 중 8개만 내고 나머지 12개를
    `excluded` 에도 적지 않았다(2026-08-30).

    판정하지 않고 **목록만** 낸다. 좁힐지 되살릴지는 사람이 정한다.
    """
    known = ((candidates or {}).get("known") or {}).keys()
    asked = {str((e or {}).get("term") or "") for e in (doc or {}).get("terms") or []}
    noted = {str((e or {}).get("term") or "") for e in (doc or {}).get("excluded") or []}
    return sorted(t for t in known if t not in asked and t not in noted)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.flatten_questions']"/>
# 문항지를 용어 순 · 문항 순으로 펴고 1부터 번호를 매긴다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1_5.answer_sheet
# ── 4. 문항지에서 기입란으로 곧장 잇기 ──────────────────────────────────
def flatten_questions(doc):
    """중첩된 문항지를 한 줄로 펴고 `QNum` 을 1부터 매긴다. `(번호, 용어, 문항)` 목록.

    **`scripts/term/quiz.mjs` 의 `flattenQuestions` 와 같은 순서여야 한다.** 번호 규칙이
    두 언어에 살고 있어서, 한쪽만 고치면 채점이 남의 답을 본다. 그래서 걸러 내지 않는다 —
    이름이 빈 용어도 자리를 차지한 채 그대로 센다. 걸러 내면 그 순간 양쪽 번호가 어긋난다.
    (이름이 비었다는 것 자체는 `validate_questions` 가 따로 잡는다.)
    """
    out = []
    for entry in (doc or {}).get("terms") or []:
        term = str((entry or {}).get("term") or "").strip()
        for q in (entry or {}).get("questions") or []:
            out.append((len(out) + 1, term, q or {}))
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.answer_sheet']"/>
# 문항지에서 정답을 빼고 사람이 채울 기입란을 만든다.
# 쓰는 것: run_mode1_5.flatten_questions · 쓰이는 곳: 없음
def answer_sheet(doc):
    """`questions.json` 에서 사람이 채울 `answer-sheet.json` 을 만든다.

    **정답(`answer`)을 싣지 않는 것이 이 함수의 요점이다.** 풀기 전에 정답이 보이면
    이 시험이 재는 것은 이해도가 아니라 눈이 된다.

    사람은 `UserAns` 에 고른 보기 번호만 적는다. 맞힌 수를 손으로 세던 자리를 없앤 것이라,
    "세다 틀려서 정답률 167%" 같은 것이 아예 생기지 않는다.
    """
    questions = []
    for qnum, term, q in flatten_questions(doc):
        choices = q.get("choices")
        choices = choices if isinstance(choices, list) else []
        questions.append({
            "QNum": qnum,
            "Term": term,
            "Question": str(q.get("ask") or ""),
            "AnsChoices": {str(i + 1): c for i, c in enumerate(choices)},
            "UserAns": "",
        })
    return {"plan": str((doc or {}).get("plan") or ""), "questions": questions}


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.choice_number']"/>
# 사람이 적은 UserAns 를 보기 번호로 읽는다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def choice_number(value):
    """`UserAns` 를 보기 번호로 읽는다. 못 읽으면 `None`.

    사람이 손으로 채우는 칸이라 `3` 과 `"3"` 이 섞인다. 둘 다 받는다.

    **빈 칸은 `None` 이고, "모르겠다" 로 대신 채우지 않는다.** 안 푼 것과 모르는 것은
    다르다. 자동으로 메우면 그 차이가 점수에 조용히 섞이고, 시험을 덜 푼 사람이
    "모르는 것이 많은 사람" 으로 기록된다.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value if value is not None else "").strip()
    return int(text) if text.isdigit() else None


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.validate_answers']"/>
# 채운 기입란이 문항지와 아귀가 맞는지 본다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def validate_answers(sheet, doc):
    """채운 기입란이 문항지와 아귀가 맞는지 본다. 불평 목록을 낸다(없으면 빈 목록).

    `quiz.mjs` 도 채점 직전에 같은 대조를 한다. 중복이 아니다 — 번호 규칙이 두 언어에
    살기 때문에, 한쪽에서만 보면 다른 쪽으로 들어온 파일이 그대로 채점된다.

    빈 칸을 오류로 잡는 것이 여기서 가장 중요한 일이다. 넘어가면 안 푼 문항이
    "틀린 문항" 으로 세어져 점수가 조용히 낮아진다.
    """
    out = []
    want = flatten_questions(doc)
    got = (sheet or {}).get("questions")
    if not isinstance(got, list):
        return ["기입란 파일이 아니다 — `questions` 배열이 없다"]

    seen = {}
    for i, rec in enumerate(got):
        rec = rec or {}
        num = rec.get("QNum")
        if not isinstance(num, int) or isinstance(num, bool):
            out.append("%d번째 칸 — `QNum` 이 정수가 아니다: %r" % (i + 1, rec.get("QNum")))
            continue
        if num in seen:
            out.append("%d번 문항의 답안이 둘 이상이다" % num)
        seen[num] = rec

    for num, term, q in want:
        rec = seen.pop(num, None)
        if rec is None:
            out.append("%d번(%s) — 문항은 냈는데 답안이 없다" % (num, term))
            continue
        if str(rec.get("Term") or "") != term:
            out.append("%d번 — 용어가 어긋난다. 문항지는 %r 인데 답안은 %r 이다"
                       % (num, term, rec.get("Term")))
        if str(rec.get("Question") or "") != str(q.get("ask") or ""):
            out.append("%d번(%s) — 물음 문구가 문항지와 다르다" % (num, term))
        ans = choice_number(rec.get("UserAns"))
        if ans is None:
            out.append("%d번(%s) — `UserAns` 가 비었다. 안 푼 것을 \"%s\" 로 세지 않는다: %r"
                       % (num, term, DONT_KNOW, rec.get("UserAns")))
        elif not 1 <= ans <= CHOICES_PER_QUESTION:
            out.append("%d번(%s) — `UserAns` 가 보기 밖이다(1~%d): %r"
                       % (num, term, CHOICES_PER_QUESTION, ans))

    for num in sorted(seen):
        out.append("%d번 — 내지 않은 문항의 답안이 있다" % num)
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5._term_script']"/>
# 용어 점검 스크립트의 절대 경로를 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 5. 명령줄 만들기 — 경로를 박지 않는다 ───────────────────────────────
def _term_script(root, name):
    """`scripts/term/<이름>` 의 절대 경로. 작업 폴더가 어디든 같은 파일을 부른다."""
    return os.path.join(root, "scripts", "term", name)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.collect_argv']"/>
# 후보 모으기 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def collect_argv(root, plan, terms_db):
    """`collect.mjs` 명령줄. node 는 PATH 에서 찾는다.

    `bin/report-term` 대신 스크립트를 곧장 부른다 — PATH 등록에 기대지 않으려는 것이고,
    `run_mode1.py` 의 `node_argv` 와 같은 방식이다.

    **용어 사전이 없으면 빼고 부른다.** 빈 문자열을 넘기면 `collect.mjs` 가 그것을
    파일 경로로 알고 찾다 실패한다.
    """
    argv = ["node", _term_script(root, "collect.mjs"), plan]
    if terms_db:
        argv.append(terms_db)
    return argv


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.grade_argv']"/>
# 채점 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def grade_argv(root, answers, questions):
    """`quiz.mjs` 명령줄. 산출물은 **부르는 쪽의 작업 폴더**에 떨어진다.

    **두 파일을 다 넘긴다.** 채운 기입란에는 정답이 없고 문항지에만 있어서, 둘이 만나야
    채점이 된다. 정답을 기입란에 실었다면 인자가 하나로 줄었겠지만 그러면 사람이
    풀기 전에 정답을 본다.
    """
    return ["node", _term_script(root, "quiz.mjs"), answers, questions]


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.emit_argv']"/>
# 산출 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def emit_argv(root, grades):
    """`emit.mjs` 명령줄. `terms.json` 과 `term-study-note.md` 를 작업 폴더에 쓴다."""
    return ["node", _term_script(root, "emit.mjs"), grades]


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.author_argv']"/>
# 출제 세션의 헤드리스 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def author_argv(model, workdir, root, plan):
    """출제 세션의 헤드리스 명령줄. **프롬프트는 여기 싣지 않는다** — 표준 입력으로 준다.

    폴더 셋을 다 열어 준다. 작업 폴더(후보와 산출물) · 도구 뿌리(규약과 스킬) ·
    계획서 폴더. 하나라도 빠지면 모형이 재료나 규약을 못 본다. 셋이 겹칠 수 있으므로
    같은 폴더를 두 번 열지 않게 순서를 지키며 걸러 낸다.
    """
    dirs, seen = [], set()
    for d in [workdir, root, os.path.dirname(os.path.abspath(plan))]:
        if d and d not in seen:
            seen.add(d)
            dirs.append(d)
    return M.claude_argv(model=model, repo=dirs[0], extra_dirs=dirs[1:])


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.author_prompt']"/>
# 한 세션이 할 일 전부를 적은 글.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def author_prompt(workdir, root, plan):
    """한 세션이 할 일 전부. **용어 보충과 출제를 둘 다** 여기서 시킨다.

    쪼개지 않는 이유는 캐시다 — 두 세션으로 나누면 두 번째가 Plan 과 후보를 처음부터
    다시 읽어 토큰이 부푼다(Mode 1 실측에서 전체 토큰의 97% 가 캐시 읽기였다).

    출제 규율은 `term-benchmark` 스킬의 `## 출제 규율` 절에서 옮겨 온 것이다.
    프롬프트에 실어야 하는 이유는 헤드리스 세션이 스킬을 안 열 수 있기 때문이다.
    """
    return """\
너는 report-builder 의 **Mode 1.5 출제자**다. 용어 시험 문항지 한 장을 만든다.
사람에게 **묻지 않는다** — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 진행하지 말고
무엇이 없어서 막혔는지 적고 끝낸다.

계획서     {plan}
작업 폴더  {workdir}   (여기에 파일을 쓴다)
도구 저장소 {root}      (report-builder. 규약과 스킬이 여기 있다)

## 이미 있는 재료 — 다시 만들지 마라

  {workdir}/{candidates}   후보. 두 갈래다
      known        코드베이스 용어 사전과 계획서 본문의 교차. **정답(means)이 이미 있다**
      newConcepts  계획서가 새로 만든 개념. 정답이 없다
  {workdir}/{answer_key}   있으면 읽는다. 사람이 적어 준 신규 개념의 뜻이다

## 할 일 1 — 자연어 용어를 보충한다

`collect` 가 잡는 것은 식별자 꼴 **세 가지뿐**이다(결정 코드 · 파일명 · 배열 필드).
`WarmUp`·`PageRank`·`인용 원점` 같은 개념어는 기계가 가려낼 수 없다. **계획서를 직접
읽고** 이해에 필요한 개념어를 골라 보탠다.

- 보탠 항목마다 **출처를 `파일:줄` 로 적는다.** 출처 없이 보탠 것은 지어낸 것과 구별되지 않는다.
- 뜻은 **계획서 본문에 실제로 적힌 서술만** 옮긴다. **지어내지 마라.**
- 계획서가 그 용어를 정의하지 않았다면 보태지 말고 `excluded` 에 넣는다.

## 할 일 2 — 출제

용어마다 객관식 **3문항**을 낸다. 정답은 그 용어의 뜻(`means`)이다.

**출제 규율 — 이것을 어기면 문항지가 채점 불가능해진다.**

- **오답 보기는 그럴듯해야 한다.** 명백히 틀린 보기만 넣으면 정답률이 100% 로 몰려
  채점이 무의미해진다. 가장 값싼 방법은 **같은 갈래의 다른 용어 뜻을 오답으로 쓰는 것**이다 —
  후보 파일 `known` 에서 `kind` 나 `module` 이 같은 항목의 `means` 를 가져온다.
- **보기 순서를 섞는다.** 정답이 늘 첫 번째에 오면 사람이 위치로 맞힌다.
- **정답지에 없는 것을 묻지 않는다.** `known` 과 **뜻이 정해진** 신규 개념 밖으로 나가지 않는다.
- **한 문항은 한 가지만 묻는다.** 두 조건을 겹치면 어느 쪽을 몰라서 틀렸는지 알 수 없다.
- **"{dont_know}" 는 항상 마지막 보기로, 항상 이 문구 그대로.** 보기는 실제 뜻 {real_choices}개에
  그것을 더해 **정확히 {choices}개**다. 문항마다 개수가 다르면 찍어서 맞을 확률이 달라져
  정답률을 문항끼리 견줄 수 없다.
- 읽는 사람은 배경 지식이 없다(객체지향을 갓 배운 대학 1학년 눈높이). 용어를 설명하려고
  다른 어려운 용어를 쓰지 않는다.

**뜻이 정해지지 않은 신규 개념은 출제하지 마라.** 정답 없는 문항은 채점이 불가능하다.
그런 개념은 `excluded` 에 `{{term, why}}` 로 남긴다 — 사람이 {answer_key} 에 뜻을 적고
실행기를 다시 돌리면 그때 출제된다. 네가 뜻을 지어내 채우면 이 시험이 재는 것이
사람의 이해도가 아니라 네 상상이 된다.

## 산출물 — 파일 하나

  {workdir}/{questions}

```json
{{ "plan": "{plan}",
   "terms": [
     {{ "term": "PageRank",
        "means": "그래프에서 중요한 점을 매기는 방법",
        "source": "{plan}:412",
        "questions": [
          {{ "ask": "PageRank 가 하는 일은?",
             "choices": ["보기 가", "보기 나", "보기 다", "보기 라", "{dont_know}"],
             "answer": 0 }}
        ] }}
   ],
   "excluded": [ {{ "term": "E402", "why": "계획서에 정의가 없다 — 사람이 뜻을 줘야 한다" }} ] }}
```

- `terms[].questions` 는 **정확히 3개**이고 `choices` 는 **정확히 {choices}개**다.
  `answer` 는 정답 보기의 자리(0부터)이고 **마지막 칸("{dont_know}")을 가리키면 안 된다.**
- `excluded` 에는 뜻을 못 구한 것을 전부 남긴다. 조용히 버리지 마라.

## 규율

- **커밋하지 마라.** `git add` · `git commit` 금지.
- 쓰는 파일은 `{workdir}/{questions}` **하나뿐**이다. 다른 파일을 고치지 마라.
- 문항 문구는 **한국어**. 약어를 피한다.
- 계획서에 글자로 없는 것은 쓰지 않는다.

끝나면 출제한 용어 수 · 문항 수 · 출제에서 뺀 개념 목록을 한 표로 보고한다.
""".format(plan=plan, workdir=workdir, root=root, candidates=CANDIDATES,
           answer_key=ANSWER_KEY, questions=QUESTIONS, dont_know=DONT_KNOW,
           choices=CHOICES_PER_QUESTION, real_choices=CHOICES_PER_QUESTION - 1)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.gate_notice']"/>
# 사람 차례에서 화면에 낼 안내문.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 6. 보고 — 멈춘 것을 실패로 그리지 않는다 ────────────────────────────
def gate_notice(questions, sheet, answers, held, answer_key, unasked=()):
    """사람 차례에서 화면에 낼 안내문.

    **이 글이 이 실행기의 산출물 절반이다.** 멈춘 화면만 보고 무엇을 해야 하는지
    알 수 없으면, 사람은 파이프라인을 처음부터 다시 뒤진다.
    """
    lines = [
        "",
        "사람 차례 — 여기서 멈춘다. 아래는 기계가 대신할 수 없는 일이다.",
        "",
        "  1. 기입란을 연다              %s" % sheet,
        "  2. 칸마다 고른 보기 번호를 `UserAns` 에 적는다 (1~%d. %d 는 \"%s\")"
        % (CHOICES_PER_QUESTION, CHOICES_PER_QUESTION, DONT_KNOW),
        "     빈 칸이 하나라도 남으면 채점하지 않고 멈춘다 — 안 푼 것과 모르는 것은 다르다.",
        "  3. 채운 파일을 이 이름으로 둔다 %s" % answers,
        "  4. 이 실행기를 **같은 인자로 다시** 돌린다 — 채점부터 이어서 한다",
        "",
        "%s 에는 정답이 들어 있다 — 풀기 전에 열지 않는다." % os.path.basename(questions),
        "맞고 틀림은 세지 않아도 된다. `quiz.mjs` 가 문항지와 대조해 센다.",
        "",
        "묻고 답을 받는 절차 자체는 `term-benchmark` 스킬이 맡는다.",
        "그 스킬은 사람에게 한 용어씩 물어 기입란을 대신 채워 준다.",
    ]
    if held:
        lines += [
            "",
            "출제에서 빠진 개념 %d개 — 뜻이 정해지지 않아 채점할 수 없다:" % len(held),
            "  " + ", ".join(held),
            "되살리려면 아래 파일에 `{\"개념\": \"뜻\"}` 으로 적고 다시 돌린다.",
            "  %s" % answer_key,
            "(계획서와 무관한 것이 섞여 있으면 그냥 두면 된다 — 뜻이 없으면 출제되지 않는다)",
        ]
    if unasked:
        lines += [
            "",
            "출제도 안 되고 뺀 이유도 안 적힌 용어 %d개 — 조용히 빠졌다:" % len(unasked),
            "  " + ", ".join(unasked),
            "범위를 좁힌 것이면 그냥 두면 된다. 잊은 것이면 %s 를 지우고 다시 돌린다."
            % os.path.basename(questions),
        ]
    return "\n".join(lines)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.format_run']"/>
# 측정 표에 건너뜀과 사람 차례를 덧붙인다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def format_run(rows, skipped, gate):
    """Mode 1 의 측정 표를 그대로 쓰고, 그 표가 말하지 못하는 둘을 덧붙인다.

    `run_mode1.format_report` 는 단계를 **성공/실패** 둘로만 그린다. 그런데 Mode 1.5 는
    재개가 정상 흐름이라 **건너뛴 단계**가 늘 있고, 사람 차례에서 **멈춘다.** 둘 다
    실패가 아니다 — 실패로 그리면 읽는 사람이 파이프라인이 깨진 줄 안다.
    그래서 표는 실제로 **돌린 단계만** 담고, 나머지는 표 밖에 글로 적는다.
    """
    out = []
    for stage, why in skipped or []:
        out.append("건너뜀 — %s (%s)" % (stage, why))
    if skipped:
        out.append("")
    out.append(M.format_report(rows) if rows else "돌린 단계가 없다.")
    if gate:
        out.append(gate)
    return "\n".join(out)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5._read_json']"/>
# 있으면 읽고 없거나 깨졌으면 아무것도 아닌 값을 낸다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 7. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
def _read_json(path):
    """있으면 읽고 없거나 깨졌으면 `None`. 재개 판단은 파일 존재만으로 하지 않는다."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.run_machine']"/>
# 기계 단계 하나를 작업 폴더에서 부른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def run_machine(argv, label, cwd):
    """기계 단계 하나. 출력은 그대로 흘려보낸다.

    **`cwd` 를 반드시 준다.** `scripts/term/*.mjs` 는 산출 파일을 전부
    `process.cwd()` 에 쓴다 — 작업 폴더를 정해 주지 않으면 파일이 흩어진다.
    """
    with M._Heartbeat(label, every=60.0):
        p = subprocess.run(argv, cwd=cwd)
    return p.returncode


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.run_author']"/>
# 출제 세션을 한 번 부른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def run_author(model, workdir, root, plan, timeout=None):
    """출제 세션을 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`."""
    argv = author_argv(model=model, workdir=workdir, root=root, plan=plan)
    with M._Heartbeat("author"):
        p = subprocess.run(argv, input=author_prompt(workdir, root, plan), cwd=workdir,
                           capture_output=True, text=True, timeout=timeout)
    try:
        return p.returncode, json.loads(p.stdout)
    except (ValueError, TypeError):
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print(tail, file=sys.stderr)
        return p.returncode, None


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1_5.main']"/>
# 명령줄을 읽고 단계를 돌린 뒤 측정 표와 사람 차례 안내를 낸다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Mode 1.5 파이프라인을 돌리고 단계별 시간·토큰을 잰다. 사람 차례에서 멈춘다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="점검할 계획서 경로 (plan.md)")
    ap.add_argument("--workdir", default=None,
                    help="산출 파일이 쌓일 폴더 (기본: 지금 폴더). 스크립트가 cwd 에 쓰기 때문에 필요하다")
    ap.add_argument("--terms-db", dest="terms_db", default=None,
                    help="코드베이스 용어 사전 terms-db.json. 없으면 신규 개념만 잡힌다")
    ap.add_argument("--model", default="opus", help="출제에 쓸 모형 (기본: opus)")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="출제 단계의 제한 시간(초)")
    a = ap.parse_args(argv)

    plan = os.path.abspath(os.path.expanduser(a.plan))
    if not os.path.isfile(plan):
        print("에러 — 계획서가 없다: %s" % plan, file=sys.stderr)
        return 1
    workdir = os.path.abspath(os.path.expanduser(a.workdir or os.getcwd()))
    if not os.path.isdir(workdir):
        print("에러 — 작업 폴더가 없다: %s" % workdir, file=sys.stderr)
        return 1
    terms_db = os.path.abspath(os.path.expanduser(a.terms_db)) if a.terms_db else None
    if terms_db and not os.path.isfile(terms_db):
        print("에러 — 용어 사전이 없다: %s" % terms_db, file=sys.stderr)
        return 1

    p_cand = os.path.join(workdir, CANDIDATES)
    p_key = os.path.join(workdir, ANSWER_KEY)
    p_ques = os.path.join(workdir, QUESTIONS)
    p_sheet = os.path.join(workdir, SHEET)
    p_ans = os.path.join(workdir, ANSWERS)
    p_grades = os.path.join(workdir, GRADES)

    try:
        stages = plan_stages(
            has_candidates=os.path.exists(p_cand),
            has_questions=os.path.exists(p_ques),
            has_answers=os.path.exists(p_ans),
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None)
    except ValueError as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    # 표 밖에 적을 것 — 건너뛴 단계. 재개가 정상 흐름이라 늘 있다.
    reasons = {"collect": "%s 이 이미 있다" % CANDIDATES,
               "author": "%s 이 이미 있다 — 다시 내면 이미 푼 시험과 어긋난다" % QUESTIONS,
               "grade": "답안이 아직 없다", "emit": "답안이 아직 없다"}
    skipped = [(s, reasons[s]) for s in STAGES if s not in stages] if not a.only else []

    print("계획서 %s" % plan)
    print("작업 폴더 %s" % workdir)
    print("모형 %s · 단계 %s" % (a.model, " -> ".join(stages) or "(없음)"))
    print("이미 있는 것 — 후보 %s · 문항지 %s · 답안 %s"
          % (os.path.exists(p_cand), os.path.exists(p_ques), os.path.exists(p_ans)))
    if a.dry_run:
        for s, why in skipped:
            print("건너뜀 — %s (%s)" % (s, why))
        if human_gate_open(os.path.exists(p_ans)):
            print("사람 차례에서 멈출 예정이다 — 답안 %s 이 없다." % p_ans)
        return 0

    rows, t_all = [], time.monotonic()
    for stage in stages:
        print("\n── %s ──────────────────────────────" % stage, flush=True)
        t0 = time.monotonic()
        if stage == "author":
            rc, result = run_author(a.model, workdir, ROOT, plan, timeout=a.timeout)
            ok, why = M.agent_verdict(rc, result)
            usage = M.normalize_usage(result)
            if result and result.get("result"):
                print(result["result"])
            if ok:
                # 문항지가 채점 가능한 꼴인지 여기서 본다 — quiz.mjs 는 검사하지 않는다
                doc = _read_json(p_ques)
                complaints = validate_questions(doc) if doc is not None \
                    else ["%s 을 읽지 못했다" % p_ques]
                if complaints:
                    ok, why = False, "문항지가 채점 불가능한 꼴이다"
                    for c in complaints:
                        print("  문항지 — %s" % c, file=sys.stderr)
        else:
            usage = M.normalize_usage(None)
            if stage == "collect":
                cmd = collect_argv(ROOT, plan, terms_db)
            elif stage == "grade":
                # 채운 기입란이 문항지와 아귀가 맞는지 채점 **전에** 본다
                doc, ans = _read_json(p_ques), _read_json(p_ans)
                complaints = validate_answers(ans or {}, doc or {}) if doc else []
                if complaints:
                    for c in complaints:
                        print("  답안 — %s" % c, file=sys.stderr)
                    rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                                 "usage": usage, "ok": False, "why": "답안이 문항지와 맞지 않는다"})
                    break
                cmd = grade_argv(ROOT, p_ans, p_ques)
            else:
                cmd = emit_argv(ROOT, p_grades)
            rc = run_machine(cmd, stage, cwd=workdir)
            ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
        seconds = time.monotonic() - t0
        rows.append({"stage": stage, "seconds": seconds, "usage": usage, "ok": ok, "why": why})
        print("%s — %s (%s)" % (stage, "성공" if ok else "실패", M._hms(seconds)), flush=True)
        if not ok:
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

    # 사람 차례 — 답안이 없고 문항지가 생겼으면 기입란을 깔아 두고 안내한다
    gate = None
    if human_gate_open(os.path.exists(p_ans)) and all(r["ok"] for r in rows):
        doc = _read_json(p_ques)
        if doc:
            with open(p_sheet, "w", encoding="utf-8") as f:
                json.dump(answer_sheet(doc), f, ensure_ascii=False, indent=2)
                f.write("\n")
            cand = _read_json(p_cand) or {}
            _, held = split_new_concepts(cand.get("newConcepts") or [],
                                         _read_json(p_key) or {})
            gate = gate_notice(p_ques, p_sheet, p_ans, held, p_key,
                               unasked=unasked_known(cand, doc))

    print("\n" + "=" * 72)
    print("Mode 1.5 측정 — 전체 %s" % M._hms(time.monotonic() - t_all))
    print("=" * 72)
    print(format_run(rows, skipped, gate))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"plan": plan, "workdir": workdir, "model": a.model,
                       "stages": rows, "skipped": skipped,
                       "total": M.sum_usage([r["usage"] for r in rows]) if rows else {},
                       "human_gate_open": bool(gate),
                       "wall_seconds": time.monotonic() - t_all},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
