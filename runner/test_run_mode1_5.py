# <include file="machine/comments.xml" path="//term[@id='test_run_mode1_5.py']"/>
# Mode 1.5 실행기의 회귀 시험 — 사람 관문·재개·문항 검사·QNum 규칙을 본다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 1.5 실행기의 회귀 시험.

여기서 보는 여섯 가지 — 사람 관문(답안이 없으면 멈추는가) · 재개(이미 만든 산출물을
다시 만들지 않는가) · 정답 미정 가르기 · 문항 검사(`quiz.py` 는 이것을 검사하지
않는다) · 기입란으로 이어짐(정답이 실리면 안 된다) · `QNum` 규칙(파이썬과 `quiz.py`
두 곳에서 매겨진다. 어긋나면 남의 답을 채점하고도 오류가 나지 않는다).

  .venv/bin/python -m pytest runner/test_run_mode1_5.py -q
"""
import os
import sys
from collections.abc import Sequence
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as M  # noqa: E402
import run_mode1_5 as R  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.one_question']"/>
# 검사를 통과하는 객관식 문항 하나를 만들어 주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.test_a_shuffled_sheet_passes, runner.test_run_mode1_5.test_an_unshuffled_sheet_is_caught, runner.test_run_mode1_5.test_the_answer_sheet_numbers_every_question_from_one
# ── 재료 ────────────────────────────────────────────────────────────────
def one_question(ask: str = "PageRank 는 무엇을 하는가?",
                 answer: int = 0) -> dict[str, Any]:
    """검사를 통과하는 문항 하나. 시험마다 한 군데씩만 망가뜨려 쓴다."""
    return {"ask": ask,
            "choices": ["그래프에서 중요한 점을 매긴다",
                        "파일을 줄 단위로 센다",
                        "주석을 소스에 심는다",
                        "선언을 훑어 목록으로 만든다",
                        "모르겠다"],
            "answer": answer}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.good_doc']"/>
# 테스트에서 쓸 정상적인 questions.json 문서 하나를 만들어 주는 도우미 함수다.
# 쓰는 것: runner.test_run_mode1_5.one_question · 쓰이는 곳: runner.test_run_mode1_5.filled_sheet, runner.test_run_mode1_5.test_a_blank_user_answer_is_caught, runner.test_run_mode1_5.test_a_fully_filled_sheet_has_no_complaints, runner.test_run_mode1_5.test_a_missing_answer_is_caught, runner.test_run_mode1_5.test_a_number_written_as_text_is_accepted (+28)
def good_doc() -> dict[str, Any]:
    """정상 `questions.json` 한 장. 용어 하나 · 문항 셋."""
    return {"plan": "/어느/plan.md",
            "terms": [{"term": "PageRank",
                       "means": "그래프에서 중요한 점을 매기는 방법",
                       "source": "/어느/plan.md:412",
                       "questions": [one_question(ask="문항 %d" % i, answer=i % 3)
                                     for i in range(3)]}],
            "excluded": []}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_fresh_run_stops_before_grading']"/>
# 아무 산출물도 없는 첫 실행에서는 채점 전 단계까지만 돈다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_stages · 쓰이는 곳: 없음
# ── 1. 단계 고르기 — 파일 시스템을 보지 않는 순수 함수 ──────────────────
def test_a_fresh_run_stops_before_grading():
    """아무것도 없으면 모으고 **거기서 끝난다.** 출제도 답안도 사람 쪽 일이다."""
    assert R.plan_stages(has_candidates=False, has_answers=False) == ["collect"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_grading_only_starts_once_a_human_answered']"/>
# 답안 파일이 이미 있을 때만 채점과 산출 단계가 계획에 들어간다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_stages · 쓰이는 곳: 없음
def test_grading_only_starts_once_a_human_answered():
    """답안이 생긴 뒤에야 채점과 산출이 붙는다."""
    assert R.plan_stages(has_candidates=True, has_answers=True) == ["grade", "emit"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_no_stage_calls_the_model']"/>
# Mode 1.5 실행기에 모형을 부르는 단계가 하나도 없음을 못박는 시험이다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def test_no_stage_calls_the_model():
    """**이 실행기는 모형을 부르지 않는다.** 출제는 term-benchmark 스킬의 일이다.

    CLI 칸으로 되돌리면 스킬과 두 곳에서 같은 일을 하게 되고, 헤드리스 세션은
    사람에게 되물을 수 없어 신규 개념의 뜻을 지어내게 된다.
    """
    for has_cand in (False, True):
        for has_ans in (False, True):
            stages = R.plan_stages(has_cand, has_ans)
            assert [s for s in stages if R.is_agent_stage(s)] == []
    assert R.AGENT_STAGES == set()


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_collect_is_skipped_when_candidates_already_exist']"/>
# 이미 후보 파일이 있으면 collect 단계를 다시 돌리지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_stages · 쓰이는 곳: 없음
def test_collect_is_skipped_when_candidates_already_exist():
    """다시 모으면 앞 실행이 쌓은 후보 파일을 덮어쓴다."""
    assert "collect" not in R.plan_stages(has_candidates=True, has_answers=False)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_nothing_runs_while_the_human_turn_is_open']"/>
# 사람 차례가 열려 있는 동안에는 돌릴 기계 단계가 없음을 못박는 시험이다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def test_nothing_runs_while_the_human_turn_is_open():
    """후보는 있고 답안은 없는 자리가 사람 차례다 — 돌릴 기계 단계가 없다."""
    assert R.plan_stages(has_candidates=True, has_answers=False) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_only_and_skip_are_honoured']"/>
# plan_stages 에 only 나 skip 옵션을 주면 그 지시가 실제로 반영되는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_stages · 쓰이는 곳: 없음
def test_only_and_skip_are_honoured():
    assert R.plan_stages(False, True, only=["grade"]) == ["grade"]
    assert "emit" not in R.plan_stages(False, True, skip=["emit"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_an_unknown_stage_is_rejected']"/>
# 존재하지 않는 단계 이름을 only 에 넣으면 오류가 나야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_stages · 쓰이는 곳: 없음
def test_an_unknown_stage_is_rejected():
    with pytest.raises(ValueError):
        R.plan_stages(False, False, only=["없는단계"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_gate_is_open_until_a_human_writes_answers']"/>
# 답안 파일이 없으면 사람 차례가 아직 열려 있다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.human_gate_open · 쓰이는 곳: 없음
# ── 2. 사람 관문 — 실행기가 멈추는 자리 ─────────────────────────────────
def test_the_gate_is_open_until_a_human_writes_answers():
    """`claude -p` 는 되물을 수 없다. 답안이 없으면 멈추는 것 말고 할 일이 없다."""
    assert R.human_gate_open(has_answers=False) is True
    assert R.human_gate_open(has_answers=True) is False


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_gate_notice_tells_the_human_exactly_which_files_to_touch']"/>
# 실행이 멈췄을 때 사람에게 보여주는 안내문이 무엇을 채워야 하는지 화면 텍스트만으로 알려주는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.gate_notice · 쓰이는 곳: 없음
def test_the_gate_notice_tells_the_human_exactly_which_files_to_touch():
    """멈췄을 때 사람이 무엇을 해야 하는지 화면만 보고 알 수 있어야 한다."""
    text = R.gate_notice(questions="/작업/questions.json",
                         sheet="/작업/answer-sheet.json",
                         answers="/작업/answers.json",
                         held=["E402", "mode1-nochange.json"],
                         answer_key="/작업/term-answer-key.json")
    assert "/작업/answer-sheet.json" in text
    assert "/작업/answers.json" in text
    assert "UserAns" in text                  # 무엇을 채우는지 이름으로 말한다
    assert "열지 않는다" in text               # 정답이 든 문항지는 열지 말라고 알린다
    # 출제에서 빠진 개념과 그것을 되살리는 방법을 함께 알린다
    assert "E402" in text and "/작업/term-answer-key.json" in text
    assert "term-benchmark" in text          # 묻는 절차는 스킬의 일이다
    assert "실패" not in text                 # 멈춘 것은 실패가 아니다


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_gate_notice_stays_quiet_when_nothing_was_held_back']"/>
# 출제에서 빠진 개념이 하나도 없을 때는 안내문이 그 이야기를 하지 않아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.gate_notice · 쓰이는 곳: 없음
def test_the_gate_notice_stays_quiet_when_nothing_was_held_back():
    text = R.gate_notice(questions="/작업/questions.json",
                         sheet="/작업/answer-sheet.json",
                         answers="/작업/answers.json",
                         held=[], answer_key="/작업/term-answer-key.json")
    assert "/작업/answers.json" in text
    assert "term-answer-key.json" not in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_new_concepts_without_a_meaning_are_held_back']"/>
# 정답(뜻)이 아직 정해지지 않은 새 개념은 출제 대상에서 빠져야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.split_new_concepts · 쓰이는 곳: 없음
# ── 3. 정답 미정 — 기계 규칙은 하나뿐이다 ───────────────────────────────
def test_new_concepts_without_a_meaning_are_held_back():
    """정답 문구가 없으면 출제하지 않는다. 채점할 수 없는 문항이 되기 때문이다."""
    ready, held = R.split_new_concepts(
        ["C-19", "E402", "mode1-nochange.json"],
        {"C-19": "인용 원점을 재는 결정 항목"})
    assert ready == ["C-19"]
    assert held == ["E402", "mode1-nochange.json"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_blank_meaning_counts_as_undefined']"/>
# 뜻 칸이 공백 문자로만 채워진 경우도 정답이 없는 것으로 취급해야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.split_new_concepts · 쓰이는 곳: 없음
def test_a_blank_meaning_counts_as_undefined():
    """빈 문자열이나 공백은 정답이 아니다 — `emit` 이 그대로 용어집으로 넘긴다."""
    ready, held = R.split_new_concepts(["C-19"], {"C-19": "   "})
    assert ready == [] and held == ["C-19"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_machine_never_judges_whether_a_concept_is_a_false_positive']"/>
# 이 함수가 개념이 진짜인지 오탐인지 판단하지 않고, 오직 뜻이 있는지만 본다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.split_new_concepts · 쓰이는 곳: 없음
def test_the_machine_never_judges_whether_a_concept_is_a_false_positive():
    """`E402`(린트 코드)든 진짜 개념이든 규칙은 같다 — 정답이 있으면 낸다."""
    ready, _ = R.split_new_concepts(["E402"], {"E402": "파이썬 린트가 내는 코드"})
    assert ready == ["E402"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_well_formed_question_sheet_has_no_complaints']"/>
# 정상 문항지에는 검사기가 불평을 하지 않는지 보는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
# ── 4. 문항 검사 — quiz.py 는 이것을 검사하지 않는다 ───────────────────
def test_a_well_formed_question_sheet_has_no_complaints():
    assert R.validate_questions(good_doc()) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_each_term_must_have_exactly_three_questions']"/>
# 용어마다 문항이 정확히 세 개여야 한다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_each_term_must_have_exactly_three_questions():
    """세 문항이 아니면 채점 구간(맞힌 수 2 이상 -> 확실)이 뜻을 잃는다."""
    doc = good_doc()
    doc["terms"][0]["questions"] = doc["terms"][0]["questions"][:2]
    assert any("3문항" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_dont_know_must_be_the_last_choice_and_always_the_same_words']"/>
# '모르겠다' 보기가 항상 마지막 자리와 같은 문구여야 한다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_dont_know_must_be_the_last_choice_and_always_the_same_words():
    """자리와 문구가 흔들리면 그것을 고르는 비용이 문항마다 달라진다."""
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = [
        "모르겠다", "그래프에서 중요한 점을 매긴다", "파일을 줄 단위로 센다",
        "주석을 소스에 심는다", "잘 모르겠는데요"]
    assert any("모르겠다" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_may_not_point_at_dont_know']"/>
# 정답 번호가 '모르겠다' 자리를 가리키면 안 된다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_may_not_point_at_dont_know():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 4     # 마지막 = "모르겠다"
    assert any("정답" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_an_answer_outside_the_choices_is_caught']"/>
# 정답 번호가 보기 범위를 벗어나면 잡힌다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_an_answer_outside_the_choices_is_caught():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 9
    assert R.validate_questions(doc) != []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_duplicate_choices_are_caught']"/>
# 같은 보기 문구가 두 번 나오면 잡힌다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_duplicate_choices_are_caught():
    """같은 보기가 둘이면 정답이 둘이 되거나 보기 수가 준다."""
    doc = good_doc()
    q = doc["terms"][0]["questions"][0]
    q["choices"] = ["같은 말", "같은 말", "다른 말", "또 다른 말", "모르겠다"]
    assert any("겹친" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_number_of_choices_is_fixed_at_five']"/>
# 보기 수가 항상 5개로 고정돼야 한다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_number_of_choices_is_fixed_at_five():
    """실제 뜻 4개 + "모르겠다" = 다섯 고정. 문항마다 개수가 다르면 찍어서 맞을 확률이
    달라져 정답률을 문항끼리 견줄 수 없다.
    """
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = ["그래프 어쩌고", "모르겠다"]
    assert any("보기" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_four_choices_are_no_longer_enough']"/>
# 보기가 4개(다섯 미만)여도 잡힌다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_four_choices_are_no_longer_enough():
    """보기가 넷이면 걸린다."""
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = [
        "그래프에서 중요한 점을 매긴다", "파일을 줄 단위로 센다",
        "주석을 소스에 심는다", "모르겠다"]
    assert any("보기" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_term_without_a_meaning_is_caught']"/>
# 용어의 뜻(means)이 비어 있으면 잡힌다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_a_term_without_a_meaning_is_caught():
    """`means` 가 비면 `emit` 이 뜻 없는 용어집을 낸다."""
    doc = good_doc()
    doc["terms"][0]["means"] = ""
    assert any("means" in c or "뜻" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_sheet_with_no_terms_is_caught']"/>
# 용어가 하나도 없는 문항지는 잘못된 문서로 잡혀야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.validate_questions · 쓰이는 곳: 없음
def test_a_sheet_with_no_terms_is_caught():
    assert R.validate_questions({"terms": []}) != []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.filled_sheet']"/>
# 사람이 답을 다 채운 기입란을 만들어 주는 재료 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: runner.test_run_mode1_5.test_a_blank_user_answer_is_caught, runner.test_run_mode1_5.test_a_fully_filled_sheet_has_no_complaints, runner.test_run_mode1_5.test_a_missing_answer_is_caught, runner.test_run_mode1_5.test_a_number_written_as_text_is_accepted, runner.test_run_mode1_5.test_a_sheet_whose_question_text_drifted_is_caught (+5)
# ── 5. questions.json 에서 기입란으로 바로 이어진다 ─────────────────────
def filled_sheet(doc: dict[str, Any] | None = None,
                 picks: Sequence[int | str] = (1, 2, 3)) -> dict[str, Any]:
    """기입란을 만들고 `UserAns` 를 채운 것. `picks` 는 문항 차례대로 고른 보기 번호.

    `good_doc()` 의 정답은 문항 차례대로 1 · 2 · 3번 보기다(`answer` 가 0부터라 하나 크다).
    그래서 `picks=(1, 2, 3)` 이면 세 문항 다 맞힌 답안이다.
    """
    sheet = R.answer_sheet(doc or good_doc())
    for rec, pick in zip(sheet["questions"], picks):
        rec["UserAns"] = pick
    return sheet


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_never_carries_the_answer']"/>
# 기입란에는 정답이 절대 실리면 안 된다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_never_carries_the_answer():
    """**이 시험이 기입란의 존재 이유다.** 풀기 전에 정답이 보이면 이해도가 아니라 눈을 잰다."""
    text = repr(R.answer_sheet(good_doc()))
    assert "answer" not in text.lower()


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_numbers_every_question_from_one']"/>
# 문항 번호(QNum)가 용어를 건너뛰며 1부터 죽 이어진다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.one_question, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_numbers_every_question_from_one():
    """`QNum` 은 용어를 건너뛰며 이어진다 — 용어마다 1로 되돌아가지 않는다."""
    doc = good_doc()
    doc["terms"].append({"term": "declmap.scan", "means": "선언을 훑는다",
                         "questions": [one_question(ask="둘째 %d" % i, answer=i % 3)
                                       for i in range(3)]})
    nums = [q["QNum"] for q in R.answer_sheet(doc)["questions"]]
    assert nums == [1, 2, 3, 4, 5, 6]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_carries_the_term_on_every_question']"/>
# 기입란의 모든 문항 레코드가 자기 용어 이름을 달고 있다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_carries_the_term_on_every_question():
    """채점 단위가 문항이 아니라 **용어**다. `Term` 이 없으면 되짚을 수가 없다."""
    for rec in R.answer_sheet(good_doc())["questions"]:
        assert rec["Term"] == "PageRank"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_numbers_the_choices_from_one_and_ends_with_dont_know']"/>
# 사람이 적는 보기 번호가 1부터 시작해 5번이 '모르겠다' 로 끝난다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_numbers_the_choices_from_one_and_ends_with_dont_know():
    """사람이 적는 번호는 1부터다. 문항지의 `answer` 는 0부터라 자리가 하나 어긋난다."""
    rec = R.answer_sheet(good_doc())["questions"][0]
    assert list(rec["AnsChoices"]) == ["1", "2", "3", "4", "5"]
    assert rec["AnsChoices"]["5"] == R.DONT_KNOW


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_leaves_the_user_column_empty']"/>
# 새로 만든 기입란은 사람이 채울 칸이 비어 있어야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_leaves_the_user_column_empty():
    """사람이 채울 자리는 비워서 낸다. 미리 채우면 안 푼 것이 답으로 실린다."""
    assert all(rec["UserAns"] == "" for rec in R.answer_sheet(good_doc())["questions"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_answer_sheet_matches_the_shape_quiz_py_reads']"/>
# 기입란 레코드의 모양이 quiz.mjs 가 기대하는 열쇠 집합과 똑같은지 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.answer_sheet, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_answer_sheet_matches_the_shape_quiz_py_reads():
    """`runner/term/quiz.py` 의 `tallySheet` 가 읽는 열쇠 그대로여야 한다."""
    for rec in R.answer_sheet(good_doc())["questions"]:
        assert set(rec) == {"QNum", "Term", "Question", "AnsChoices", "UserAns"}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_flatten_keeps_the_order_the_sheet_was_built_in']"/>
# 문항을 평평하게 펼치는 함수가 원래 순서를 그대로 지키는지 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.flatten_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_flatten_keeps_the_order_the_sheet_was_built_in():
    """번호 규칙이 파이썬과 `quiz.py` 두 곳에 산다. 여기서 한 번 못 박아 둔다."""
    flat = R.flatten_questions(good_doc())
    assert [q["QNum"] for q in flat] == [1, 2, 3]
    assert [q["Term"] for q in flat] == ["PageRank"] * 3
    assert [q["Raw"].get("ask") for q in flat] == ["문항 0", "문항 1", "문항 2"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_fully_filled_sheet_has_no_complaints']"/>
# 빈틈없이 다 채운 답안지가 정상이라고 확인하는 시험 하나.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
# ── 5-2. 채운 기입란 검사 — quiz.py 도 같은 대조를 한다 ────────────────
def test_a_fully_filled_sheet_has_no_complaints():
    assert R.validate_answers(filled_sheet(), good_doc()) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_choosing_dont_know_is_a_valid_answer']"/>
# "모르겠다"를 고르는 것도 정답을 안 고른 것과는 다른, 유효한 답이라고 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_choosing_dont_know_is_a_valid_answer():
    """"모르겠다" 는 답을 안 쓴 것이 아니라 고른 것이다."""
    assert R.validate_answers(filled_sheet(picks=(5, 5, 5)), good_doc()) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_blank_user_answer_is_caught']"/>
# 빈칸으로 남겨둔 답과 '모르겠다'를 고른 답은 다르다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_blank_user_answer_is_caught():
    """**안 푼 것과 모르는 것은 다르다.** 자동으로 "모르겠다" 로 메우지 않는다."""
    sheet = filled_sheet()
    sheet["questions"][1]["UserAns"] = ""
    assert any("UserAns" in c and "2번" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_user_answer_outside_the_choices_is_caught']"/>
# 존재하지 않는 보기 번호를 답으로 쓰면 걸러진다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_user_answer_outside_the_choices_is_caught():
    sheet = filled_sheet()
    sheet["questions"][0]["UserAns"] = 9
    assert any("보기 밖" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_number_written_as_text_is_accepted']"/>
# 사람이 손으로 채우는 칸이라 숫자와 숫자 모양 글자('1' 과 1)가 섞여도 똑같이 받아준다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_number_written_as_text_is_accepted():
    """사람이 손으로 채우는 칸이라 `3` 과 `"3"` 이 섞인다. 둘 다 받는다."""
    assert R.validate_answers(filled_sheet(picks=("1", "2", "3")), good_doc()) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_missing_answer_is_caught']"/>
# 문항 하나에 대한 답 레코드 자체가 통째로 빠지면 걸러진다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_missing_answer_is_caught():
    sheet = filled_sheet()
    del sheet["questions"][2]
    assert any("3번" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_an_answer_to_a_question_that_was_never_asked_is_caught']"/>
# 출제되지 않은 번호(99번)에 대한 답이 끼어들면 걸러진다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_an_answer_to_a_question_that_was_never_asked_is_caught():
    sheet = filled_sheet()
    sheet["questions"].append({"QNum": 99, "Term": "PageRank",
                               "Question": "없던 물음", "AnsChoices": {}, "UserAns": 1})
    assert any("99번" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_same_question_answered_twice_is_caught']"/>
# 같은 문항에 대한 답 레코드가 두 번 나오면 걸러진다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_the_same_question_answered_twice_is_caught():
    sheet = filled_sheet()
    sheet["questions"].append(dict(sheet["questions"][0]))
    assert any("둘 이상" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_sheet_whose_terms_drifted_is_caught']"/>
# 답안지의 용어 이름이 원래 문항지와 어긋나면 걸러진다는 것을 확인하는 시험. 번호만 믿고 채점하면 남의 답을 채점하고도 오류가 안 나기 때문에 필요한 검사다.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_sheet_whose_terms_drifted_is_caught():
    """**번호 규칙이 두 언어에 살아서 필요한 검사다.**

    순서가 어긋나면 남의 답을 채점하고도 오류가 나지 않는다. 그래서 번호만 믿지 않고
    용어와 물음 문구를 같이 대조한다.
    """
    sheet = filled_sheet()
    sheet["questions"][0]["Term"] = "declmap.scan"
    assert any("어긋난다" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_sheet_whose_question_text_drifted_is_caught']"/>
# 답안지의 물음 문구 자체가 원래 문항지와 어긋나면 걸러진다는 것을 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc, runner.test_run_mode1_5.filled_sheet · 쓰이는 곳: 없음
def test_a_sheet_whose_question_text_drifted_is_caught():
    sheet = filled_sheet()
    sheet["questions"][0]["Question"] = "다른 물음이 되어 버렸다"
    assert any("물음 문구" in c for c in R.validate_answers(sheet, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_old_count_shaped_answers_file_is_rejected']"/>
# 옛 꼴({용어: {correct, dontKnow}})의 답안 파일이 조용히 통과하지 않고 거부되는지 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_answers, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_old_count_shaped_answers_file_is_rejected():
    """옛 꼴(`{용어: {correct, dontKnow}}`)을 주면 조용히 0점이 아니라 거부한다."""
    old = {"PageRank": {"correct": 2, "dontKnow": 1, "means": "그래프 중요도"}}
    assert any("기입란" in c for c in R.validate_answers(old, good_doc()))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_collect_argv_names_the_plan_and_the_term_database']"/>
# collect 단계 명령줄이 계획서와 용어 DB 경로를 정확히 넘기는지 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.collect_argv · 쓰이는 곳: 없음
# ── 7. 기계 단계의 명령줄 — 경로를 박지 않는다 ──────────────────────────
def test_collect_argv_names_the_plan_and_the_term_database():
    argv = R.collect_argv(root="/도구/뿌리", plan="/계획/plan.md", terms_db="/어느/terms-db.json")
    assert argv[0] == "python3"
    assert argv[1].endswith(os.path.join("runner", "term", "collect.py"))
    assert argv[2] == "/계획/plan.md" and argv[3] == "/어느/terms-db.json"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_collect_argv_works_without_a_term_database']"/>
# 용어 DB 가 없어도 collect 명령줄이 만들어진다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.collect_argv · 쓰이는 곳: 없음
def test_collect_argv_works_without_a_term_database():
    """DB 가 없으면 코드베이스 용어는 0개다 — 그래도 신규 개념은 잡힌다."""
    assert R.collect_argv(root="/r", plan="/p.md", terms_db=None) == [
        "python3", os.path.join("/r", "runner", "term", "collect.py"), "/p.md"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_grade_and_emit_argv_point_at_the_right_scripts']"/>
# grade·emit 단계 명령줄이 각각 맞는 스크립트를 가리키는지 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.grade_argv, runner.run_mode1_5.emit_argv · 쓰이는 곳: 없음
def test_grade_and_emit_argv_point_at_the_right_scripts():
    argv = R.grade_argv("/r", "/작업/answers.json", "/작업/questions.json")
    assert argv[1].endswith("quiz.py")
    assert R.emit_argv("/r", "/작업/term-grades.json")[1].endswith("emit.py")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_grade_argv_hands_over_both_files']"/>
# 채점 명령줄이 답안 파일과 문항지 파일을 둘 다 넘긴다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.grade_argv · 쓰이는 곳: 없음
def test_grade_argv_hands_over_both_files():
    """채운 기입란에는 정답이 없다. 문항지가 같이 가야 채점이 된다."""
    argv = R.grade_argv("/r", "/작업/answers.json", "/작업/questions.json")
    assert argv[2:] == ["/작업/answers.json", "/작업/questions.json"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_report_reuses_the_mode_1_table']"/>
# Mode 1.5 의 실행 보고서가 Mode 1 과 같은 표 모양을 쓰는지 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.format_run · 쓰이는 곳: 없음
# ── 8. 보고 — 멈춘 것을 실패로 그리지 않는다 ────────────────────────────
def test_the_report_reuses_the_mode_1_table():
    rows: list[M.StageRow] = [{"stage": "collect", "seconds": 0.4, "ok": True,
                               "why": "", "usage": R.M.normalize_usage(None)}]
    text = R.format_run(rows, skipped=[], gate=None)
    assert "collect" in text and "합계" in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed']"/>
# 재개할 때 건너뛴 단계를 실패로 보이지 않고 '건너뜀' 으로 따로 표시하는지 확인하는 시험. 실패로 보이면 읽는 사람이 오해하기 때문이다.
# 쓰는 것: runner.run_mode1_5.format_run · 쓰이는 곳: 없음
def test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed():
    """재개해서 건너뛴 단계를 '실패' 로 그리면 읽는 사람이 오해한다."""
    text = R.format_run([{"stage": "grade", "seconds": 0.2, "ok": True, "why": "",
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[("collect", "term-candidates.json 이 이미 있다")],
                        gate=None)
    assert "건너뜀" in text and "collect" in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_gate_is_appended_to_the_report_and_is_not_a_failure']"/>
# 사람이 답안을 채워야 넘어가는 관문 문구가 보고서 끝에 붙되, 그것이 실패로 표시되지는 않는지 확인하는 시험.
# 쓰는 것: runner.run_mode1_5.format_run · 쓰이는 곳: 없음
def test_the_gate_is_appended_to_the_report_and_is_not_a_failure():
    text = R.format_run([{"stage": "collect", "seconds": 9.0, "ok": True, "why": "",
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[], gate="사람 차례 — answers.json 을 쓴다")
    assert "사람 차례" in text
    assert "실패" not in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_an_unshuffled_sheet_is_caught']"/>
# 여러 용어의 정답 자리가 전부 같은 위치에 몰려 있으면 잡힌다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.one_question, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
# ── 9. 문항지가 조용히 망가지는 두 자리 ─────────────────────────────────
def test_an_unshuffled_sheet_is_caught():
    """정답이 전부 같은 자리에 있으면 사람이 **위치로** 맞힌다. 보기의 좋고 나쁨은
    기계가 못 보지만 자리가 한곳에 몰린 것은 볼 수 있다.
    """
    doc = good_doc()
    doc["terms"].append({"term": "declmap.scan", "means": "선언을 훑는다",
                         "questions": [one_question(ask="문항 %d" % i, answer=0)
                                       for i in range(3)]})
    for q in doc["terms"][0]["questions"]:
        q["answer"] = 0
    assert any("자리" in c for c in R.validate_questions(doc))


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_a_shuffled_sheet_passes']"/>
# 정답 자리가 용어마다 다르게 섞여 있으면 통과한다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.one_question, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_a_shuffled_sheet_passes():
    doc = good_doc()
    doc["terms"].append({"term": "declmap.scan", "means": "선언을 훑는다",
                         "questions": [one_question(ask="문항 %d" % i, answer=(i + 1) % 3)
                                       for i in range(3)]})
    assert R.validate_questions(doc) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_shuffle_check_stays_quiet_on_a_tiny_sheet']"/>
# 문항이 3개뿐인 작은 표본에서는 정답이 몰려 있어도 자리 검사가 단정하지 않는다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.validate_questions, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_the_shuffle_check_stays_quiet_on_a_tiny_sheet():
    """문항이 셋뿐이면 우연히 몰릴 수 있다. 표본이 적을 때 단정하지 않는다."""
    doc = good_doc()
    for q in doc["terms"][0]["questions"]:
        q["answer"] = 0
    assert R.validate_questions(doc) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_known_terms_that_were_neither_asked_nor_excluded_are_reported']"/>
# 출제도 안 되고 제외 목록에도 없는 알려진 용어가 보고된다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.unasked_known, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_known_terms_that_were_neither_asked_nor_excluded_are_reported():
    """출제도 안 되고 `excluded` 에도 안 적힌 용어를 잡는다 — 무엇이 빠졌는지 보여야
    범위를 좁힌 것인지 잊은 것인지 사람이 구별할 수 있다.
    """
    cand: dict[str, Any] = {"known": {"PageRank": {}, "declmap.scan": {}, "warmup.save": {}}}
    doc = good_doc()                       # PageRank 만 출제됐다
    doc["excluded"] = [{"term": "declmap.scan", "why": "계획서에 정의가 없다"}]
    assert R.unasked_known(cand, doc) == ["warmup.save"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_nothing_is_reported_when_every_known_term_is_accounted_for']"/>
# 알려진 용어가 모두 출제됐으면 아무것도 보고되지 않는다는 것을 확인하는 시험 함수다.
# 쓰는 것: runner.run_mode1_5.unasked_known, runner.test_run_mode1_5.good_doc · 쓰이는 곳: 없음
def test_nothing_is_reported_when_every_known_term_is_accounted_for():
    cand: dict[str, Any] = {"known": {"PageRank": {}}}
    assert R.unasked_known(cand, good_doc()) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_the_gate_notice_lists_the_silently_dropped_terms']"/>
# 출제도 안 되고 제외 이유도 안 적힌 채 조용히 빠진 용어를 안내문이 사람에게 알려줘야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1_5.gate_notice · 쓰이는 곳: 없음
def test_the_gate_notice_lists_the_silently_dropped_terms():
    text = R.gate_notice(questions="/작업/questions.json", sheet="/작업/t.json",
                         answers="/작업/answers.json", held=[],
                         answer_key="/작업/key.json", unasked=["warmup.save"])
    assert "warmup.save" in text
    assert "실패" not in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_plan_slug_strips_the_date_prefix']"/>
# 날짜 접두사가 붙은 계획서 파일 이름에서 slug 가 날짜를 뗀 나머지인지 보는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_slug · 쓰이는 곳: 없음
# ── 7. 계획서별 작업 폴더 — 두 계획서가 같은 자리를 쓰면 한쪽이 죽는다 ──────
def test_plan_slug_strips_the_date_prefix():
    assert R.plan_slug("/a/b/2026-08-30-symbol-resolution-survey.md") == "symbol-resolution-survey"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_plan_slug_falls_back_to_the_bare_filename']"/>
# 날짜 접두사가 없는 계획서 파일 이름이면 slug 가 확장자만 뗀 파일 이름인지 보는 시험이다.
# 쓰는 것: runner.run_mode1_5.plan_slug · 쓰이는 곳: 없음
def test_plan_slug_falls_back_to_the_bare_filename():
    """날짜 접두사가 없으면 확장자만 뗀 파일 이름을 그대로 쓴다 — 빈 문자열을 내지 않는다."""
    assert R.plan_slug("/a/b/plan.md") == "plan"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1_5.test_two_plans_get_two_different_workdirs']"/>
# 계획서 둘의 기본 작업 폴더가 서로 다른지 확인하는 시험이다 — 겹치면 한쪽 산출물이 다른 쪽을 덮어쓴다.
# 쓰는 것: runner.run_mode1_5.default_workdir · 쓰이는 곳: 없음
def test_two_plans_get_two_different_workdirs():
    a = R.default_workdir("/repo", "/plans/2026-08-30-symbol-resolution-survey.md")
    b = R.default_workdir("/repo", "/plans/2026-08-30-llm-load-reduction.md")
    assert a != b
    assert a == "/repo/out/mode1_5/symbol-resolution-survey"
    assert b == "/repo/out/mode1_5/llm-load-reduction"
