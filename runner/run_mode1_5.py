#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_mode1_5.py']"/>
# 용어 이해도 점검 흐름을 돌리다 사람 차례에서 멈추는 실행기.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# Mode 1.5 파이프라인을 돌리다 사람 차례에서 멈추는 파일.
# 쓰는 것: run_mode1 · 쓰이는 곳: 없음
"""Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.**

재는 코드는 `run_mode1.py` 의 것을 그대로 import 해 쓴다 — 여기에 사본이 없다.

## 네 단계와 그 사이의 사람 차례

    collect ──▶ [스킬 차례] ──▶ grade ──▶ emit
     기계        실행기가 멈춘다   기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `collect` | Plan 본문과 코드베이스 용어 사전의 교차를 모은다 | `runner/term/collect.py` |
| `grade`   | 사람이 쓴 답안을 채점한다(확실 / 모름) | `runner/term/quiz.py` |
| `emit`    | 용어집과 학습 노트를 낸다 | `runner/term/emit.py` |

**`--ask` 를 주면 스킬 차례를 실행기가 연다** — 대화형 `claude` 세션을 띄워 첫 프롬프트로
`/term-benchmark` 를 넘기고, 세션이 `answers.json` 을 남기면 그대로 `grade` `emit` 으로 이어간다.
남기지 않으면 관문처럼 기입란을 깔고 멈춘다. 터미널에서만 된다.

**`--ask` 없이는 이 실행기에 LLM Model을 부르는 칸이 없다.** 출제는 `term-benchmark` 스킬의 일이다 —
스킬이 `questions.json` 을 쓰고, 실행기는 그것을 **기계로 검사**해 정답을 뺀 기입란을 깐다.
오답 보기의 그럴듯함은 기계가 만들 수 없고, 묻는 자리에는 사람이 있어야 한다.

**Mode 1 과 다른 점은 사람 자리 하나다.** 재는 것이 사람의 이해도라 사람이 답하지 않으면
잴 것이 없고, `claude -p` 는 헤드리스라 되물을 수 없다. **그래서 실행기는 답안 파일이
없으면 멈춘다.**

## 사람 차례가 요구하는 것 둘

  1. `answers.json` — 실행기가 깔아 준 기입란(`answer-sheet.json`)의 `UserAns` 칸을
     전부 채워 이 이름으로 둔 것. **필수.** 맞고 틀림은 사람이 세지 않는다 —
     `quiz.py` 가 문항지와 대조해 센다.
  2. `term-answer-key.json` — Plan 이 새로 만든 개념의 **뜻**. 선택.
     뜻이 없는 개념은 출제되지 않는다(채점할 수 없으므로). 사람이 여기에 뜻을 적고
     실행기를 다시 돌리면 그때 출제된다.

## 재개 — 이미 있는 산출물을 보고 할 일을 정한다

멈췄다 다시 돌리는 것이 정상 흐름이라 **재개가 이 실행기의 기본 동작**이다.
후보 파일이 있으면 `collect` 를 건너뛴다. 문항지가 있으면 채점 가능한 꼴인지 먼저 검사하고,
어긋나면 아무 단계도 돌리지 않는다 — `quiz.py` 는 문항지를 검사하지 않는다.

## `questions.json` — 문항지의 형식

| 열쇠 | 꼴 | 뜻 |
|---|---|---|
| `plan` | 문자열 | 이 문항지가 나온 Plan 파일 경로 |
| `terms[]` | 배열 | 출제된 용어 하나당 한 칸 |
| `terms[].term` | 문자열 | 용어 이름. `answers.json` 의 열쇠가 된다 |
| `terms[].means` | 문자열 | **정답 문구.** `emit` 이 그대로 용어집으로 넘긴다 |
| `terms[].source` | 문자열 | 이 뜻의 출처(`파일:줄`). 지어낸 것과 구별하려고 적는다 |
| `terms[].questions[]` | 배열 | **정확히 3개.** `quiz.py` 의 채점 구간이 그 수를 전제한다 |
| `terms[].questions[].ask` | 문자열 | 물음 한 줄. 한 문항은 한 가지만 묻는다 |
| `terms[].questions[].choices[]` | 배열 | **정확히 5개.** 실제 뜻 4개 + **마지막에 항상 "모르겠다"** |
| `terms[].questions[].answer` | 정수 | 정답 보기의 자리(0부터). 마지막 칸을 가리키면 안 된다 |
| `excluded[]` | 배열 | 출제하지 못한 개념과 그 사유. 사람이 읽는 보고다 |

## `answer-sheet.json` — 사람이 채우는 기입란

**정답이 든 `questions.json` 을 사람에게 그대로 내밀 수 없다.** 실행기가 그것을 용어 순 ·
문항 순으로 펴고 정답을 뺀 기입란을 따로 깐다. 사람은 `UserAns` 에 고른 보기 번호만
적는다 — 맞고 틀림을 세는 일은 기계가 한다.

    { "plan": "…/plan.md",
      "questions": [
        { "QNum": 1,
          "Term": "PageRank",
          "Question": "PageRank 가 하는 일은?",
          "AnsChoices": {"1": "…", "2": "…", "3": "…", "4": "…", "5": "모르겠다"},
          "UserAns": "" } ] }

`Term` 을 싣는 것은 **채점 단위가 문항이 아니라 용어**이기 때문이다(3문항을 묶어
확실/모름을 매긴다). 없으면 채점할 때 되짚을 수가 없다.

**QNum 은 두 언어에 같은 규칙으로 산다** — 여기(`flatten_questions`)와 `runner/term/quiz.py`
양쪽이 같은 순서로 펴야 번호가 맞는다. 어긋나면 조용히 남의 답을 채점하게 되므로,
채점 직전에 `Term` 과 물음 문구를 문항지와 대조해 **다르면 멈춘다.**

## 쓰는 법

    .venv/bin/python runner/run_mode1_5.py <plan.md> \
        [--workdir <작업폴더>] [--terms-db <terms-db.json>] [--dry-run]

**`--workdir` 는 이제 선택이다.** 안 주면 계획서 이름에서 slug 를 뽑아
`out/mode1_5/<slug>/` 를 만들어 쓴다(`default_workdir`). **계획서를 둘 이상 동시에
점검할 때 `--workdir` 를 생략하고 `out/mode1_5/` 를 공유하지 마라** — `questions.json`
같은 산출 파일 이름이 하나뿐이라 서로 덮어써 한쪽이 죽는다(2026-08-31 실측). slug 로
나뉜 기본값을 쓰면 계획서마다 자기 폴더를 갖는다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypedDict, cast

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# `tools.python` 과 `runner.term.quiz` 는 절대 경로 패키지 import 라 ROOT 가 sys.path 에
# 있어야 한다. "쓰는 법" 대로 `python runner/run_mode1_5.py` 로 직접 부르면 sys.path[0] 이
# `runner/` 라 ROOT 가 없다 — 이 줄보다 먼저 두 import 를 하면 ModuleNotFoundError 로 죽는다.
sys.path.insert(0, ROOT)
from tools.python import pythonPath  # noqa: E402
from runner.term.quiz import QUESTIONS_PER_TERM, CHOICES_PER_QUESTION, flatten_questions, choice_number  # noqa: E402

# 재는 코드(`hms` · `Heartbeat` · `normalize_usage` · `format_report` …)의 원본은
# `measure.py` 하나뿐이다. 여기에는 사본이 없다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msgspec  # noqa: E402

import measure as M  # noqa: E402
import pipeline as P  # noqa: E402

# 기계 단계는 셋 고정이다. 사이의 출제·문답은 `term-benchmark` 스킬이 맡는다.
STAGES = ["collect", "grade", "emit"]

# 사람 차례 자리에 `--ask` 로 끼우는 단계. 헤드리스가 아니라 **대화형** `claude` 세션을 띄워
# 스킬이 사용자에게 직접 묻게 한다 — 출제는 여전히 스킬의 일이고 실행기는 자리만 내준다.
ASK = "ask"
SKILL = "term-benchmark"

# LLM Model을 부르는 단계. `ask` 하나뿐이고 `--ask` 를 줄 때만 그래프에 들어간다.
# 헤드리스 출제 칸은 두지 않는다 — 사람에게 되물을 수 없어 신규 개념의 뜻을 지어내게 된다.
AGENT_STAGES: set[str] = {ASK}


# "모르겠다" 는 자리도 문구도 고정이다. 흔들리면 그것을 고르는 비용이 문항마다 달라진다.
DONT_KNOW = "모르겠다"

# 한 문항의 보기 수. 실제 뜻 넷에 "모르겠다" 를 더해 다섯이다. 문항마다 다르면
# 찍어서 맞을 확률이 문항마다 달라지고, 그러면 정답률을 문항끼리 견줄 수 없다.

# 파일 이름은 한곳에 모은다. 스킬 문서와 어긋나면 사람이 엉뚱한 파일을 찾는다.
CANDIDATES = "term-candidates.json"
ANSWER_KEY = "term-answer-key.json"
QUESTIONS = "questions.json"
SHEET = "answer-sheet.json"
ANSWERS = "answers.json"
GRADES = "term-grades.json"


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.is_agent_stage']"/>
# 어떤 단계 이름을 주면 그 단계가 LLM(에이전트)을 부르는 단계인지 참/거짓으로 답해주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 1. 단계 고르기 (파일 시스템을 보지 않는 순수 함수) ──────────────────
def is_agent_stage(stage: str) -> bool:
    """이 단계가 큰 언어 LLM Model을 부르는 자리인지 답한다. 토큰이 잡히는 곳은 여기뿐이다."""
    return stage in AGENT_STAGES


def plan_stages(has_candidates: bool, has_answers: bool,
                only: Iterable[str] | None = None,
                skip: Iterable[str] | None = None,
                ask: bool = False) -> list[str]:
    """무엇을 실제로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다.

    세 가지 규칙뿐이다.

      - 후보 파일이 있으면 `collect` 를 건너뛴다. 다시 모으면 덮어쓴다.
      - 답안이 없으면 `grade` 와 `emit` 을 아예 넣지 않는다. 이것이 사람 차례다.
      - `ask` 면 그 사람 차례 자리에 `ask` 를 세우고 `grade` `emit` 을 뒤에 붙인다 —
        세션이 답안을 남기면 그대로 이어 채점한다. 답안이 이미 있으면 물을 것이 없다.
    """
    for name in list(only or []) + list(skip or []):
        if name not in STAGES:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (name, ", ".join(STAGES)))
    if only:
        return [s for s in STAGES if s in set(only)]
    out: list[str] = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        if s == "collect" and has_candidates:
            continue
        if s in ("grade", "emit") and not has_answers:
            if ask and s == "grade":
                out.append(ASK)
            if not ask:
                continue
        out.append(s)
    return out


def human_gate_open(has_answers: bool) -> bool:
    """사람 차례가 아직 안 끝났는가. 답안 파일 하나로 판정한다."""
    return not has_answers


# ── 2. 정답 미정 가르기 — 기계 규칙은 하나뿐이다 ────────────────────────
def _text(v: object) -> str:
    """`str(v or "")` 와 같다. 숫자가 와도 글자로 본다."""
    return str(v) if v else ""


class Question(TypedDict, total=False):
    """`questions.json` 의 문항 하나. LLM 이 쓰고 사람이 손댈 수 있어 칸은 전부 선택이다 —
    있는 칸의 형만 msgspec 이 보고, 개수 · 자리 · 빈 문구는 `validate_questions` 가 본다."""
    ask: str
    choices: list[str]
    answer: int


class TermEntry(TypedDict, total=False):
    term: str
    means: str
    questions: list[Question]


class QuestionsDoc(TypedDict, total=False):
    plan: str
    terms: list[TermEntry]
    excluded: list[TermEntry]


class Candidates(TypedDict, total=False):
    """`term-candidates.json`."""
    known: dict[str, object]
    newConcepts: list[str]


class SheetDoc(TypedDict, total=False):
    """사람이 채운 `answers.json`. 칸 안은 무엇이든 올 수 있어 `validate_answers` 가 하나씩 본다."""
    plan: str
    questions: list[dict[str, object]]


def split_new_concepts(new_concepts: Iterable[str],
                       answer_key: object) -> tuple[list[str], list[str]]:
    """Plan 이 새로 만든 개념을 **출제할 것**과 **미룰 것**으로 가른다.

    규칙은 하나다 — **뜻(정답 문구)이 있느냐.** 뜻이 없으면 채점이 불가능하므로 낼 수 없다.

    **오탐인지 아닌지는 여기서 따지지 않는다.** `collect.py` 가 식별자 꼴을 글자로만 잡아
    린트 코드나 임시 파일 이름을 섞어 보내지만, 뜻이 없으면 자연히 출제에서 빠진다.

    `(출제할 것, 미룰 것)` 두 목록을 원래 순서 그대로 낸다.
    """
    key = msgspec.convert(answer_key, dict[str, object]) if answer_key is not None else {}
    ready: list[str] = []
    held: list[str] = []
    for t in new_concepts:
        if _text(key.get(t)).strip():
            ready.append(t)
        else:
            held.append(t)
    return ready, held


# ── 3. 문항지 검사 — quiz.py 는 이것을 검사하지 않는다 ─────────────────
def validate_questions(doc: object) -> list[str]:
    """`questions.json` 이 채점 가능한 꼴인지 본다. 불평 목록을 낸다(없으면 빈 목록).

    **`quiz.py` 는 이것을 검사하지 않는다.** 답안만 받아 세므로 문항이 둘뿐이거나
    "모르겠다" 가 가운데 있어도 채점은 조용히 끝난다. 그 조용한 실패를 여기서 잡는다.

    형식이 맞는지만 본다. 문항의 좋고 나쁨은 기계가 볼 수 없다.
    """
    out: list[str] = []
    spots: list[int] = []        # spots — 정답이 놓인 자리. 한곳에 몰렸는지 뒤에서 본다
    # 꼴은 msgspec 이 본다(있는 칸의 형). 개수 · 자리 · 빈 문구는 아래가 본다 —
    # 문항지는 LLM Model이 쓰고 사람이 손댈 수 있는 JSON 이라 그 둘을 갈라 잡는다.
    try:
        d = msgspec.convert(doc, QuestionsDoc)
    except msgspec.ValidationError as e:
        return ["문항지의 꼴이 틀리다 — %s" % e]
    terms = d.get("terms", [])
    if not terms:
        return ["문항지에 용어가 하나도 없다 — `terms` 배열이 비었거나 없다"]

    for i, 칸 in enumerate(terms):
        name = 칸.get("term", "").strip()
        head = name or "(이름 없는 %d번째 용어)" % (i + 1)
        if not name:
            out.append("%s — `term` 이 비었다" % head)
        if not 칸.get("means", "").strip():
            out.append("%s — `means`(뜻)가 비었다. 비면 용어집에 뜻 없는 항목이 실린다" % head)

        qs = 칸.get("questions", [])
        if len(qs) != QUESTIONS_PER_TERM:
            out.append("%s — %d문항이어야 하는데 %d개다"
                       % (head, QUESTIONS_PER_TERM, len(qs)))

        for j, 물음 in enumerate(qs):
            tag = "%s 문항 %d" % (head, j + 1)
            if not 물음.get("ask", "").strip():
                out.append("%s — 물음(`ask`)이 비었다" % tag)
            choices = 물음.get("choices", [])
            if len(choices) != CHOICES_PER_QUESTION:
                out.append("%s — 보기는 실제 뜻 %d개에 \"%s\" 를 더해 정확히 %d개여야 하는데 %d개다"
                           % (tag, CHOICES_PER_QUESTION - 1, DONT_KNOW,
                              CHOICES_PER_QUESTION, len(choices)))
                continue
            if choices[-1] != DONT_KNOW:
                out.append("%s — \"%s\" 가 **마지막** 보기가 아니다 (지금 마지막은 %r)"
                           % (tag, DONT_KNOW, choices[-1]))
            if len(set(choices)) != len(choices):
                out.append("%s — 보기가 서로 겹친다" % tag)
            ans = 물음.get("answer")
            if ans is None or ans < 0 or ans >= len(choices):   # bool · 문자열은 msgspec 이 위에서 거부했다
                out.append("%s — 정답 자리(`answer`)가 보기 밖이다: %r" % (tag, ans))
            elif ans == len(choices) - 1:
                out.append("%s — 정답이 \"%s\" 를 가리킨다" % (tag, DONT_KNOW))
            else:
                spots.append(ans)

    # 정답 자리가 한곳에 몰렸는가. 정답이 늘 같은 자리면 사람이 뜻이 아니라 위치로 맞힌다.
    # 문항이 적을 때는 우연히 몰릴 수 있으므로 여섯부터 본다.
    if len(spots) >= 6 and len(set(spots)) == 1:
        out.append("정답이 %d문항 모두 %d번 자리에 있다 — 보기 순서를 섞어야 한다"
                   % (len(spots), spots[0]))
    return out


def unasked_known(candidates: object, doc: object) -> list[str]:
    """후보의 `known` 중 **출제도 안 되고 뺀 이유도 안 적힌** 용어를 낸다.

    판정하지 않고 **목록만** 낸다. 좁힐지 되살릴지는 사람이 정한다.
    """
    known = msgspec.convert(candidates, Candidates).get("known", {})
    d = msgspec.convert(doc, QuestionsDoc)
    asked = {e.get("term", "") for e in d.get("terms", [])}
    noted = {e.get("term", "") for e in d.get("excluded", [])}
    return sorted(t for t in known if t not in asked and t not in noted)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.answer_sheet']"/>
# questions.json 에서 정답을 뺀, 사람이 풀 답안지를 만드는 함수다.
# 쓰는 것: runner.run_mode1_5.flatten_questions · 쓰이는 곳: runner.run_mode1_5.flatten_questions, runner.run_mode1_5.main, runner.test_run_mode1_5.filled_sheet, runner.test_run_mode1_5.test_the_answer_sheet_carries_the_term_on_every_question, runner.test_run_mode1_5.test_the_answer_sheet_leaves_the_user_column_empty (+4)
# ── 4. 문항지에서 기입란으로 곧장 잇기 ──────────────────────────────────
class SheetQuestion(TypedDict):
    """`answer-sheet.json` 의 한 칸. 사람은 `UserAns` 에만 적는다."""
    QNum: int
    Term: str
    Question: str
    AnsChoices: dict[str, str]
    # 실행기가 내는 값은 늘 `""` 이지만, 사람이 채우면 정수도 온다 —
    # `choice_number` 가 둘 다 받는다.
    UserAns: str | int


class AnswerSheet(TypedDict):
    """정답을 뺀 기입란 전체. **`answer` 를 싣지 않는 것이 요점이다.**"""
    plan: str
    questions: list[SheetQuestion]


def answer_sheet(doc: object) -> AnswerSheet:
    """`questions.json` 에서 사람이 채울 `answer-sheet.json` 을 만든다.

    **정답(`answer`)을 싣지 않는 것이 이 함수의 요점이다.** 사람은 `UserAns` 에 고른
    보기 번호만 적고, 맞힌 수는 기계가 센다.
    """
    d = msgspec.convert(doc, QuestionsDoc)
    questions: list[SheetQuestion] = []
    for q_dict in flatten_questions(cast(dict[str, object], d)):
        q = msgspec.convert(q_dict.get("Raw"), Question)
        choices = q.get("choices", [])
        questions.append({
            "QNum": msgspec.convert(q_dict.get("QNum"), int),
            "Term": _text(q_dict.get("Term")),
            "Question": q.get("ask", ""),
            "AnsChoices": {str(i + 1): c for i, c in enumerate(choices)},
            "UserAns": "",
        })
    return {"plan": d.get("plan", ""), "questions": questions}


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.validate_answers']"/>
# 사람이 채운 답안지 파일이 원래 문항지와 내용이 맞는지 검사하는 함수다.
# 쓰는 것: runner.run_mode1_5.flatten_questions, runner.run_mode1_5.choice_number · 쓰이는 곳: runner.run_mode1_5.main, runner.test_run_mode1_5.test_a_blank_user_answer_is_caught, runner.test_run_mode1_5.test_a_fully_filled_sheet_has_no_complaints, runner.test_run_mode1_5.test_a_missing_answer_is_caught, runner.test_run_mode1_5.test_a_number_written_as_text_is_accepted (+7)
def validate_answers(sheet: object, doc: object) -> list[str]:
    """채운 기입란이 문항지와 아귀가 맞는지 본다. 불평 목록을 낸다(없으면 빈 목록).

    `quiz.py` 도 채점 직전에 같은 대조를 한다. 중복이 아니다 — 번호 규칙이 두 언어에
    살기 때문에, 한쪽에서만 보면 다른 쪽으로 들어온 파일이 그대로 채점된다.

    **빈 칸은 오류다.** 넘어가면 안 푼 문항이 틀린 문항으로 세어진다.
    """
    out: list[str] = []
    try:
        d = msgspec.convert(doc, QuestionsDoc)
        s = msgspec.convert(sheet, SheetDoc)
    except msgspec.ValidationError as e:
        return ["기입란 파일이 아니다 — %s" % e]
    want = flatten_questions(cast(dict[str, object], d))
    if "questions" not in s:
        return ["기입란 파일이 아니다 — `questions` 배열이 없다"]

    seen: dict[int, dict[str, object]] = {}
    for i, 칸 in enumerate(s["questions"]):
        num = 칸.get("QNum")
        if not isinstance(num, int) or isinstance(num, bool):
            out.append("%d번째 칸 — `QNum` 이 정수가 아니다: %r" % (i + 1, 칸.get("QNum")))
            continue
        if num in seen:
            out.append("%d번 문항의 답안이 둘 이상이다" % num)
        seen[num] = 칸

    for q_dict in want:
        num = msgspec.convert(q_dict.get("QNum"), int)
        term = _text(q_dict.get("Term"))
        q = msgspec.convert(q_dict.get("Raw"), Question)
        rec = seen.pop(num, None)
        if rec is None:
            out.append("%d번(%s) — 문항은 냈는데 답안이 없다" % (num, term))
            continue
        if _text(rec.get("Term")) != term:
            out.append("%d번 — 용어가 어긋난다. 문항지는 %r 인데 답안은 %r 이다"
                       % (num, term, rec.get("Term")))
        if _text(rec.get("Question")) != q.get("ask", ""):
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


# 같은 규칙을 쓴다 — 두 Mode 가 같은 계획서를 다른 이름으로 부르면 사람이 헷갈린다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode1_5.default_workdir
_PLAN_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")


def plan_slug(plan: str) -> str:
    """계획서 경로에서 작업 폴더 이름으로 쓸 slug 를 뽑는다.

    `YYYY-MM-DD-<slug>.md` 꼴이면 날짜를 뗀 나머지가 slug 다(`run_mode2.DOC_DIRS`의
    `plans` 규칙과 같다). 그 꼴이 아니면(날짜 접두사가 없는 파일) 확장자만 뗀 파일 이름을
    그대로 쓴다 — **빈 문자열을 내지 않는다.** 빈 문자열이면 `default_workdir` 가
    `out/mode1_5/` 바로 아래를 가리켜 여러 계획서가 다시 겹친다.
    """
    name = os.path.basename(plan)
    m = _PLAN_FILENAME_RE.match(name)
    return m.group(2) if m else os.path.splitext(name)[0]


def default_workdir(root: str, plan: str) -> str:
    """`--workdir` 를 안 주면 여기로 떨어진다 — `<root>/out/mode1_5/<slug>/`.

    **`out/mode1_5/` 를 그대로 작업 폴더로 쓰지 않는다.** 계획서 둘을 동시에 점검하면
    `questions.json` 같은 산출 파일이 이름 하나뿐이라 서로 덮어써 한쪽이 죽는다
    (2026-08-31 실측 — 같은 저장소를 쓰는 세션 둘이 `out/mode1_5/` 를 공유해 실제로 겹쳤다).
    slug 로 나누면 계획서마다 자기 폴더를 갖는다.
    """
    return os.path.join(root, "out", "mode1_5", plan_slug(plan))


# ── 5. 명령줄 만들기 — 경로를 박지 않는다 ───────────────────────────────
def _term_script(root: str, name: str) -> str:
    """`runner/term/<이름>` 의 절대 경로. 작업 폴더가 어디든 같은 파일을 부른다."""
    return os.path.join(root, "runner", "term", name)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.collect_argv']"/>
# 용어 후보를 모으는 collect.mjs 를 실행할 명령줄(문자열 목록)을 만드는 함수다.
# 쓰는 것: runner.run_mode1_5._term_script · 쓰이는 곳: runner.run_mode1_5.main, runner.test_run_mode1_5.test_collect_argv_names_the_plan_and_the_term_database, runner.test_run_mode1_5.test_collect_argv_works_without_a_term_database
def collect_argv(root: str, plan: str, terms_db: str | None) -> list[str]:
    """`collect.py` 명령줄. node 는 PATH 에서 찾는다.

    **용어 사전이 없으면 인자를 빼고 부른다.** 빈 문자열을 넘기면 `collect.py` 가
    그것을 파일 경로로 알고 찾다 실패한다.
    """
    argv = [pythonPath(root, sys.platform, dict(os.environ)), _term_script(root, "collect.py"), plan]
    if terms_db:
        argv.append(terms_db)
    return argv


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.grade_argv']"/>
# 채점 스크립트 quiz.mjs 를 실행할 명령줄을 만드는 함수다.
# 쓰는 것: runner.run_mode1_5._term_script · 쓰이는 곳: runner.run_grade.main, runner.run_mode1_5.main, runner.test_run_mode1_5.test_grade_and_emit_argv_point_at_the_right_scripts, runner.test_run_mode1_5.test_grade_argv_hands_over_both_files
def grade_argv(root: str, answers: str, questions: str) -> list[str]:
    """`quiz.py` 명령줄. 산출물은 **부르는 쪽의 작업 폴더**에 떨어진다.

    **두 파일을 다 넘긴다.** 채운 기입란에는 정답이 없고 문항지에만 있어서, 둘이
    만나야 채점이 된다.
    """
    return [pythonPath(root, sys.platform, dict(os.environ)), _term_script(root, "quiz.py"), answers, questions]


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.emit_argv']"/>
# 결과물을 만드는 emit.mjs 를 실행할 명령줄을 만드는 함수다.
# 쓰는 것: runner.run_mode1_5._term_script · 쓰이는 곳: runner.run_mode1_5.main, runner.test_run_mode1_5.test_grade_and_emit_argv_point_at_the_right_scripts
def emit_argv(root: str, grades: str) -> list[str]:
    """`emit.py` 명령줄. `terms.json` 과 `term-study-note.md` 를 작업 폴더에 쓴다."""
    return [pythonPath(root, sys.platform, dict(os.environ)), _term_script(root, "emit.py"), grades]


def ask_argv(root: str, plan: str, workdir: str, python: str) -> list[str]:
    """대화형 `claude` 명령줄. 첫 프롬프트가 `/term-benchmark …` 라 세션이 뜨자마자 스킬이 돈다.

    `-p` 를 쓰지 않는다 — 스킬은 `AskUserQuestion` 으로 사람에게 묻고, 헤드리스는 되물을 수 없다.
    작업 폴더가 저장소 밖일 수 있어 `--add-dir` 로 열어 준다. 채점은 세션이 끝난 뒤 실행기 몫이라
    프롬프트에 "하지 마라" 를 박는다.
    """
    prompt = AskStage.load_prompt(
        "ask", skill=SKILL, plan=plan, workdir=workdir,
        candidates=os.path.join(workdir, CANDIDATES), questions=os.path.join(workdir, QUESTIONS),
        python=python, runner=os.path.join(root, "runner", "run_mode1_5.py"),
        sheet=os.path.join(workdir, SHEET), answers=os.path.join(workdir, ANSWERS)).rstrip("\n")
    return ["claude", "--add-dir", workdir, prompt]


def run_interactive(argv: Sequence[str], cwd: str) -> int:
    """터미널을 그대로 넘겨 자식을 띄우고 끝날 때까지 기다린다. 출력을 가로채지 않는다."""
    return subprocess.run(list(argv), cwd=cwd).returncode


# ── 6. 보고 — 멈춘 것을 실패로 그리지 않는다 ────────────────────────────
def gate_notice(questions: str, sheet: str, answers: str, held: Sequence[str],
                answer_key: str, unasked: Sequence[str] = ()) -> str:
    """사람 차례에서 화면에 낼 안내문."""
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
        "맞고 틀림은 세지 않아도 된다. `quiz.py` 가 문항지와 대조해 센다.",
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.format_run']"/>
# Mode 1.5 실행 결과를 사람이 읽을 보고 문자열로 만드는 함수다.
# 쓰는 것: runner.run_mode1.format_report · 쓰이는 곳: runner.run_mode1_5.main, runner.test_run_mode1_5.test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed, runner.test_run_mode1_5.test_the_gate_is_appended_to_the_report_and_is_not_a_failure, runner.test_run_mode1_5.test_the_report_reuses_the_mode_1_table
def format_run(rows: Sequence[M.StageRow], skipped: Sequence[tuple[str, str]] | None,
               gate: str | None) -> str:
    """`run_mode1.format_report` 의 표를 쓰고, 그 표가 말하지 못하는 둘을 덧붙인다.

    그 표는 단계를 **성공/실패** 둘로만 그린다. 건너뛴 단계와 사람 차례는 실패가 아니므로
    표에는 **실제로 돌린 단계만** 담고, 나머지는 표 밖에 글로 적는다.
    """
    out: list[str] = []
    for stage, why in skipped or []:
        out.append("건너뜀 — %s (%s)" % (stage, why))
    if skipped:
        out.append("")
    out.append(M.format_report(rows) if rows else "돌린 단계가 없다.")
    if gate:
        out.append(gate)
    return "\n".join(out)


# ── 7. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.run_machine']"/>
# 기계 단계 하나(collect/grade/emit 등)를 실제로 실행시키는 함수다.
# 쓰는 것: runner.run_mode1.Heartbeat · 쓰이는 곳: runner.run_grade.main
def run_machine(argv: Sequence[str], label: str, cwd: str) -> int:
    """기계 단계 하나. 출력은 그대로 흘려보낸다.

    **`cwd` 를 반드시 준다.** `runner/term/*.mjs` 는 산출 파일을 전부 `process.cwd()` 에
    쓴다 — 작업 폴더를 정해 주지 않으면 파일이 흩어진다.
    """
    with M.Heartbeat(label, every=60.0):
        p = subprocess.run(argv, cwd=cwd)
    return p.returncode


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1_5.main']"/>
# Mode 1.5(용어 이해도 점검) 파이프라인의 진입점. 문제를 만들고 사람이 풀 때까지 멈췄다가 채점하고 결과를 낸다.
# 쓰는 것: runner.run_mode1_5.plan_stages, runner.run_mode1.agent_verdict, runner.run_mode1.normalize_usage, runner.run_mode1_5.validate_questions, runner.run_mode1_5.collect_argv (+12) · 쓰이는 곳: 없음

# ── 8. 단계 기계 — 문맥 · 단계 셋 · 사람 관문 ───────────────────────────
@dataclass
class Mode15Context(P.RunContext):
    """Mode 1.5 의 단계 사이를 건너다니는 값. 산출 파일 자리는 `workdir` 이 정한다."""
    plan: str = ""
    workdir: str = ""
    terms_db: str | None = None
    # 사람 관문이 남긴 안내. `format_run` 이 표 밖에 찍는다.
    gate: str | None = None

    @property
    def p_cand(self) -> str:
        return os.path.join(self.workdir, CANDIDATES)

    @property
    def p_key(self) -> str:
        return os.path.join(self.workdir, ANSWER_KEY)

    @property
    def p_ques(self) -> str:
        return os.path.join(self.workdir, QUESTIONS)

    @property
    def p_sheet(self) -> str:
        return os.path.join(self.workdir, SHEET)

    @property
    def p_ans(self) -> str:
        return os.path.join(self.workdir, ANSWERS)

    @property
    def p_grades(self) -> str:
        return os.path.join(self.workdir, GRADES)


CANDIDATES_ART = P.Artifact[Mode15Context](CANDIDATES, lambda c: c.p_cand)
GRADES_ART = P.Artifact[Mode15Context](GRADES, lambda c: c.p_grades)


class Mode15Machine(P.MachineStage[Mode15Context]):
    """세 단계 모두 `runner/term/` 의 스크립트를 자식 프로세스로 부른다."""

    def cwd(self, ctx: Mode15Context) -> str:
        return ctx.workdir


class CollectStage(Mode15Machine):
    name = "collect"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return collect_argv(ctx.root, ctx.plan, ctx.terms_db)

    def writes(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [CANDIDATES_ART]


class GradeStage(Mode15Machine):
    name = "grade"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return grade_argv(ctx.root, ctx.p_ans, ctx.p_ques)

    def reads(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        """채운 기입란이 문항지와 아귀가 맞는지 채점 **전에** 본다."""
        doc = P.load(ctx.p_ques, QuestionsDoc) if os.path.exists(ctx.p_ques) else None
        return [P.Artifact[Mode15Context](QUESTIONS, lambda c: c.p_ques,
                                          QuestionsDoc, validate_questions),
                P.Artifact[Mode15Context](ANSWERS, lambda c: c.p_ans,
                                          SheetDoc, lambda raw: validate_answers(raw, doc))]

    def writes(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [GRADES_ART]


class EmitStage(Mode15Machine):
    name = "emit"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return emit_argv(ctx.root, ctx.p_grades)

    def reads(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [GRADES_ART]


class GateStage(P.Stage[Mode15Context]):
    """사람 차례. 기입란을 깔아 두고 흐름을 멈춘다 — **실패가 아니다.**

    문항지가 아직 없으면 깔 것이 없으므로 `OK` 로 지나간다.
    """
    name = "gate"
    emits = P.OK | P.GATE

    def perform(self, ctx: Mode15Context) -> P.Outcome:
        if not os.path.exists(ctx.p_ques):
            return P.Outcome(P.OK, "문항지가 아직 없다")
        doc = P.load(ctx.p_ques, QuestionsDoc)
        with open(ctx.p_sheet, "w", encoding="utf-8") as f:
            json.dump(answer_sheet(doc), f, ensure_ascii=False, indent=2)
            f.write("\n")
        cand = P.load(ctx.p_cand, Candidates) if os.path.exists(ctx.p_cand) else Candidates()
        concepts = cand.get("newConcepts", [])
        key = P.load(ctx.p_key, dict[str, object]) if os.path.exists(ctx.p_key) else None
        _, held = split_new_concepts(concepts, key)
        ctx.gate = gate_notice(ctx.p_ques, ctx.p_sheet, ctx.p_ans, held, ctx.p_key,
                               unasked=unasked_known(cand, doc))
        return P.Outcome(P.GATE, "사람 차례")


class AskStage(P.PromptResource, P.Stage[Mode15Context]):
    """`--ask` 의 사람 차례. 대화형 `claude` 세션을 띄워 `term-benchmark` 스킬이 출제하고 묻게 한다.

    세션이 답안을 남기면 `OK` 로 채점에 넘기고, 남기지 않았으면 관문과 같은 일(기입란 · 안내)을
    하고 `GATE` 로 멈춘다. 터미널이 아니거나 `claude` 가 없으면 세션을 띄우지 않고 `FAIL`.
    토큰·비용은 대화형 세션이라 여기서 잡히지 않는다 — 행의 usage 는 0 이다.
    """
    name = ASK
    emits = P.OK | P.FAIL | P.GATE
    prompt_dir = os.path.join(ROOT, "runner", "prompts")
    prompt_names = ("ask",)

    def perform(self, ctx: Mode15Context) -> P.Outcome:
        t0 = time.monotonic()
        row: M.StageRow = {"stage": self.name, "seconds": 0.0, "usage": M.normalize_usage(None),
                           "ok": False, "why": ""}
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            row["why"] = "대화형 터미널이 아니다 — --ask 는 터미널에서만 돈다"
            return P.Outcome(P.FAIL, row["why"], [row])
        if shutil.which("claude") is None:
            row["why"] = "PATH 에 claude 가 없다"
            return P.Outcome(P.FAIL, row["why"], [row])
        python = pythonPath(ctx.root, sys.platform, dict(os.environ))
        rc = run_interactive(ask_argv(ctx.root, ctx.plan, ctx.workdir, python), cwd=ctx.root)
        row["seconds"] = time.monotonic() - t0
        if rc != 0:
            row["why"] = "claude 세션 종료 코드 %d" % rc
            return P.Outcome(P.FAIL, row["why"], [row])
        row["ok"] = True
        if os.path.exists(ctx.p_ans):
            print("%s — 답안이 남았다. 이어서 채점한다 (%s)" % (self.name, M.hms(row["seconds"])), flush=True)
            return P.Outcome(P.OK, "", [row])
        gate = GateStage().perform(ctx)      # 기입란과 안내는 관문과 같은 것을 깐다
        return P.Outcome(P.GATE, gate.why or "답안이 남지 않았다", [row])


MODE1_5_STAGES: dict[str, P.Stage[Mode15Context]] = {
    "collect": CollectStage(), "grade": GradeStage(), "emit": EmitStage(),
    "gate": GateStage(), ASK: AskStage()}

# 갈래는 지금 동작과 1:1 이다. `gate` 의 `GATE` 만 새 줄이고, 이것도 지금 루프 밖에서
# 하던 일에 이름을 붙인 것이다. `ask` 는 답안이 안 남으면 관문처럼 `GATE` 로 멈춘다.
MODE1_5_EDGES = P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT,
                         ("gate", P.GATE): P.HALT, (ASK, P.GATE): P.HALT})


def build_mode1_5_graph(ctx: Mode15Context, has_candidates: bool, has_answers: bool,
                        only: Iterable[str] | None,
                        skip: Iterable[str] | None,
                        ask: bool = False) -> P.StageDagGraph[Mode15Context]:
    """진입점에서 부른다. 사람 차례가 안 끝났으면 `gate` 를 맨 뒤에 붙인다 — `ask` 면
    그 자리를 `ask` 가 대신하므로 `gate` 를 붙이지 않는다.

    `questions.json` 과 `answers.json` 은 사람과 스킬이 만드는 것이라 어떤 단계도
    쓰지 않는다 — 늘 `given` 에 넣고 실제 존재는 드라이버가 본다.
    """
    names = plan_stages(has_candidates=has_candidates, has_answers=has_answers,
                        only=only, skip=skip, ask=ask)
    if human_gate_open(has_answers) and ASK not in names:
        names = names + ["gate"]
    given = P.existing([CANDIDATES_ART, GRADES_ART], ctx) + [
        P.Artifact[Mode15Context](QUESTIONS, lambda c: c.p_ques),
        P.Artifact[Mode15Context](ANSWERS, lambda c: c.p_ans)]
    return P.build_graph("mode1_5", names, {n: MODE1_5_STAGES[n] for n in names},
                         MODE1_5_EDGES, given, ctx)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mode 1.5 파이프라인을 돌리고 단계별 시간·토큰을 잰다. 사람 차례에서 멈춘다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="점검할 계획서 경로 (plan.md)")
    ap.add_argument("--workdir", default=None,
                    help="산출 파일이 쌓일 폴더 (기본: out/mode1_5/<계획서 slug>/, 없으면 만든다). "
                         "스크립트가 cwd 에 쓰기 때문에 필요하다")
    ap.add_argument("--terms-db", dest="terms_db", default=None,
                    help="코드베이스 용어 사전 terms-db.json. 없으면 신규 개념만 잡힌다")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--ask", action="store_true",
                    help="사람 차례를 여기서 연다 — 대화형 claude 세션을 띄워 %s 스킬이 출제·문답하고, "
                         "답안이 남으면 이어서 채점한다. 터미널에서만 된다" % SKILL)
    a = ap.parse_args(argv)

    plan = os.path.abspath(os.path.expanduser(a.plan))
    if not os.path.isfile(plan):
        print("에러 — 계획서가 없다: %s" % plan, file=sys.stderr)
        return 1
    if a.workdir:
        # 사람이 자리를 직접 골랐다 — 있어야 한다. 만들어 주지 않는다.
        workdir = os.path.abspath(os.path.expanduser(a.workdir))
        if not os.path.isdir(workdir):
            print("에러 — 작업 폴더가 없다: %s" % workdir, file=sys.stderr)
            return 1
    else:
        # 계획서 slug 로 자기 폴더를 만든다. **`out/mode1_5/` 를 그대로 쓰지 않는다** —
        # 계획서 둘을 동시에 점검하면 산출 파일이 서로 덮어써 한쪽이 죽는다.
        workdir = default_workdir(ROOT, plan)
        os.makedirs(workdir, exist_ok=True)
    terms_db = os.path.abspath(os.path.expanduser(a.terms_db)) if a.terms_db else None
    if terms_db and not os.path.isfile(terms_db):
        print("에러 — 용어 사전이 없다: %s" % terms_db, file=sys.stderr)
        return 1

    ctx = Mode15Context(root=ROOT, model="", plan=plan, workdir=workdir,
                        terms_db=terms_db)
    try:
        graph = build_mode1_5_graph(
            ctx,
            has_candidates=os.path.exists(ctx.p_cand),
            has_answers=os.path.exists(ctx.p_ans),
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None,
            ask=bool(a.ask))
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    # 표 밖에 적을 것 — 건너뛴 단계. 재개가 정상 흐름이라 늘 있다.
    reasons = {"collect": "%s 이 이미 있다" % CANDIDATES,
               "grade": "답안이 아직 없다", "emit": "답안이 아직 없다"}
    skipped = [(s_name, reasons[s_name]) for s_name in STAGES
               if s_name not in graph.order] if not a.only else []

    # 문항지가 있으면 **무엇을 돌리기 전에** 채점 가능한 꼴인지 본다.
    # 출제는 스킬이 하고 검사는 여기가 한다 — `quiz.py` 는 꼴을 보지 않는다.
    if os.path.exists(ctx.p_ques):
        try:
            complaints = validate_questions(P.load(ctx.p_ques, object))
        except msgspec.DecodeError as e:
            complaints = ["%s 을 읽지 못했다 — %s" % (ctx.p_ques, e)]
        if complaints:
            for c in complaints:
                print("  문항지 — %s" % c, file=sys.stderr)
            print("에러 — 문항지가 채점 불가능한 꼴이다: %s" % ctx.p_ques, file=sys.stderr)
            return 1

    print("계획서 %s" % plan)
    print("작업 폴더 %s" % workdir)
    print("단계 %s" % (" -> ".join(n for n in graph.order if n != "gate") or "(없음)"))
    print("이미 있는 것 — 후보 %s · 문항지 %s · 답안 %s"
          % (os.path.exists(ctx.p_cand), os.path.exists(ctx.p_ques),
             os.path.exists(ctx.p_ans)))
    if a.dry_run:
        for s_name, why in skipped:
            print("건너뜀 — %s (%s)" % (s_name, why))
        if human_gate_open(os.path.exists(ctx.p_ans)):
            print("사람 차례를 %s 세션이 연다 — 답안 %s 이 남으면 이어 채점한다." % (SKILL, ctx.p_ans)
                  if a.ask else "사람 차례에서 멈출 예정이다 — 답안 %s 이 없다." % ctx.p_ans)
        print(graph.render())
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode15Context]().run(graph, ctx)
    gate = ctx.gate

    print("\n" + "=" * 72)
    print("Mode 1.5 측정 — 전체 %s" % M.hms(time.monotonic() - t_all))
    print("=" * 72)
    print(format_run(rows, skipped, gate))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"plan": plan, "workdir": workdir,
                       "stages": rows, "skipped": skipped,
                       "total": M.sum_usage([r["usage"] for r in rows]) if rows else {},
                       "human_gate_open": bool(gate),
                       "wall_seconds": time.monotonic() - t_all},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
