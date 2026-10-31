"""Mode 1.5 실행기의 회귀 시험.

여기서 보는 여섯 가지 — 사람 관문(답안이 없으면 멈추는가) · 재개(이미 만든 산출물을
다시 만들지 않는가) · 정답 미정 가르기 · 문항 검사(`quiz.py` 는 이것을 검사하지
않는다) · 기입란으로 이어짐(정답이 실리면 안 된다) · `QNum` 규칙(파이썬과 `quiz.py`
두 곳에서 매겨진다. 어긋나면 남의 답을 채점하고도 오류가 나지 않는다).

  .venv/bin/python -m pytest test/term/test_run_mode1_5.py -q
"""
import json
import os
import sys
from pathlib import Path
from collections.abc import Sequence
from typing import Any

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "term", "python", "runner"), os.path.join(ROOT, "src", "codewiki", "python", "machine")]
from core import measure as M  # noqa: E402
from core import pipeline as P  # noqa: E402
import run_mode1_5 as R  # noqa: E402


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


def good_doc() -> dict[str, Any]:
    """정상 `questions.json` 한 장. 용어 하나 · 문항 셋."""
    return {"plan": "/어느/plan.md",
            "terms": [{"term": "PageRank",
                       "means": "그래프에서 중요한 점을 매기는 방법",
                       "source": "/어느/plan.md:412",
                       "questions": [one_question(ask="문항 %d" % i, answer=i % 3)
                                     for i in range(3)]}],
            "excluded": []}


# ── 1. 단계 고르기 — 파일 시스템을 보지 않는 순수 함수 ──────────────────
def test_a_fresh_run_stops_before_grading():
    """아무것도 없으면 모으고 **거기서 끝난다.** 출제도 답안도 사람 쪽 일이다."""
    assert R.plan_stages(has_candidates=False, has_answers=False) == ["collect"]


def test_grading_only_starts_once_a_human_answered():
    """답안이 생긴 뒤에야 채점과 산출이 붙는다."""
    assert R.plan_stages(has_candidates=True, has_answers=True) == ["grade", "emit"]


def test_no_stage_calls_the_model():
    """**`--ask` 없이는 이 실행기가 LLM Model을 부르지 않는다.** 출제는 term-benchmark 스킬의 일이다.

    헤드리스 출제 칸은 두지 않는다 — 사람에게 되물을 수 없어 신규 개념의 뜻을 지어내게 된다.
    `ask` 는 대화형 세션을 띄워 그 스킬을 부르는 자리이고, 기계 단계 셋(`STAGES`)에는 들지 않는다.
    """
    for has_cand in (False, True):
        for has_ans in (False, True):
            stages = R.plan_stages(has_cand, has_ans)
            assert [s for s in stages if R.is_agent_stage(s)] == []
    assert R.AGENT_STAGES == {R.ASK} and R.ASK not in R.STAGES


def test_collect_is_skipped_when_candidates_already_exist():
    """다시 모으면 앞 실행이 쌓은 후보 파일을 덮어쓴다."""
    assert "collect" not in R.plan_stages(has_candidates=True, has_answers=False)


def test_nothing_runs_while_the_human_turn_is_open():
    """후보는 있고 답안은 없는 자리가 사람 차례다 — 돌릴 기계 단계가 없다."""
    assert R.plan_stages(has_candidates=True, has_answers=False) == []


def test_only_and_skip_are_honoured():
    assert R.plan_stages(False, True, only=["grade"]) == ["grade"]
    assert "emit" not in R.plan_stages(False, True, skip=["emit"])


def test_an_unknown_stage_is_rejected():
    with pytest.raises(ValueError):
        R.plan_stages(False, False, only=["없는단계"])


# ── 2. 사람 관문 — 실행기가 멈추는 자리 ─────────────────────────────────
def test_the_gate_is_open_until_a_human_writes_answers():
    """`claude -p` 는 되물을 수 없다. 답안이 없으면 멈추는 것 말고 할 일이 없다."""
    assert R.human_gate_open(has_answers=False) is True
    assert R.human_gate_open(has_answers=True) is False


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


def test_the_gate_notice_stays_quiet_when_nothing_was_held_back():
    text = R.gate_notice(questions="/작업/questions.json",
                         sheet="/작업/answer-sheet.json",
                         answers="/작업/answers.json",
                         held=[], answer_key="/작업/term-answer-key.json")
    assert "/작업/answers.json" in text
    assert "term-answer-key.json" not in text


# ── 3. 정답 미정 — 기계 규칙은 하나뿐이다 ───────────────────────────────
def test_new_concepts_without_a_meaning_are_held_back():
    """정답 문구가 없으면 출제하지 않는다. 채점할 수 없는 문항이 되기 때문이다."""
    ready, held = R.split_new_concepts(
        ["C-19", "E402", "mode1-nochange.json"],
        {"C-19": "인용 원점을 재는 결정 항목"})
    assert ready == ["C-19"]
    assert held == ["E402", "mode1-nochange.json"]


def test_a_blank_meaning_counts_as_undefined():
    """빈 문자열이나 공백은 정답이 아니다 — `emit` 이 그대로 용어집으로 넘긴다."""
    ready, held = R.split_new_concepts(["C-19"], {"C-19": "   "})
    assert ready == [] and held == ["C-19"]


def test_the_machine_never_judges_whether_a_concept_is_a_false_positive():
    """`E402`(린트 코드)든 진짜 개념이든 규칙은 같다 — 정답이 있으면 낸다."""
    ready, _ = R.split_new_concepts(["E402"], {"E402": "파이썬 린트가 내는 코드"})
    assert ready == ["E402"]


# ── 4. 문항 검사 — quiz.py 는 이것을 검사하지 않는다 ───────────────────
def test_a_well_formed_question_sheet_has_no_complaints():
    assert R.validate_questions(good_doc()) == []


def test_each_term_must_have_exactly_three_questions():
    """세 문항이 아니면 채점 구간(맞힌 수 2 이상 -> 확실)이 뜻을 잃는다."""
    doc = good_doc()
    doc["terms"][0]["questions"] = doc["terms"][0]["questions"][:2]
    assert any("3문항" in c for c in R.validate_questions(doc))


def test_dont_know_must_be_the_last_choice_and_always_the_same_words():
    """자리와 문구가 흔들리면 그것을 고르는 비용이 문항마다 달라진다."""
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = [
        "모르겠다", "그래프에서 중요한 점을 매긴다", "파일을 줄 단위로 센다",
        "주석을 소스에 심는다", "잘 모르겠는데요"]
    assert any("모르겠다" in c for c in R.validate_questions(doc))


def test_the_answer_may_not_point_at_dont_know():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 4     # 마지막 = "모르겠다"
    assert any("정답" in c for c in R.validate_questions(doc))


def test_an_answer_outside_the_choices_is_caught():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 9
    assert R.validate_questions(doc) != []


def test_duplicate_choices_are_caught():
    """같은 보기가 둘이면 정답이 둘이 되거나 보기 수가 준다."""
    doc = good_doc()
    q = doc["terms"][0]["questions"][0]
    q["choices"] = ["같은 말", "같은 말", "다른 말", "또 다른 말", "모르겠다"]
    assert any("겹친" in c for c in R.validate_questions(doc))


def test_the_number_of_choices_is_fixed_at_five():
    """실제 뜻 4개 + "모르겠다" = 다섯 고정. 문항마다 개수가 다르면 찍어서 맞을 확률이
    달라져 정답률을 문항끼리 견줄 수 없다.
    """
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = ["그래프 어쩌고", "모르겠다"]
    assert any("보기" in c for c in R.validate_questions(doc))


def test_four_choices_are_no_longer_enough():
    """보기가 넷이면 걸린다."""
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = [
        "그래프에서 중요한 점을 매긴다", "파일을 줄 단위로 센다",
        "주석을 소스에 심는다", "모르겠다"]
    assert any("보기" in c for c in R.validate_questions(doc))


def test_a_term_without_a_meaning_is_caught():
    """`means` 가 비면 `emit` 이 뜻 없는 용어집을 낸다."""
    doc = good_doc()
    doc["terms"][0]["means"] = ""
    assert any("means" in c or "뜻" in c for c in R.validate_questions(doc))


def test_a_sheet_with_no_terms_is_caught():
    assert R.validate_questions({"terms": []}) != []


# ── 5. questions.json 에서 기입란으로 바로 이어진다 ─────────────────────
def filled_sheet(doc: dict[str, Any] | None = None,
                 picks: Sequence[int | str] = (1, 2, 3)) -> R.AnswerSheet:
    """기입란을 만들고 `UserAns` 를 채운 것. `picks` 는 문항 차례대로 고른 보기 번호.

    `good_doc()` 의 정답은 문항 차례대로 1 · 2 · 3번 보기다(`answer` 가 0부터라 하나 크다).
    그래서 `picks=(1, 2, 3)` 이면 세 문항 다 맞힌 답안이다.
    """
    sheet = R.answer_sheet(doc or good_doc())
    for rec, pick in zip(sheet["questions"], picks):
        rec["UserAns"] = pick
    return sheet


def test_the_answer_sheet_never_carries_the_answer():
    """**이 시험이 기입란의 존재 이유다.** 풀기 전에 정답이 보이면 이해도가 아니라 눈을 잰다."""
    text = repr(R.answer_sheet(good_doc()))
    assert "answer" not in text.lower()


def test_the_answer_sheet_numbers_every_question_from_one():
    """`QNum` 은 용어를 건너뛰며 이어진다 — 용어마다 1로 되돌아가지 않는다."""
    doc = good_doc()
    doc["terms"].append({"term": "declmap.scan", "means": "선언을 훑는다",
                         "questions": [one_question(ask="둘째 %d" % i, answer=i % 3)
                                       for i in range(3)]})
    nums = [q["QNum"] for q in R.answer_sheet(doc)["questions"]]
    assert nums == [1, 2, 3, 4, 5, 6]


def test_the_answer_sheet_carries_the_term_on_every_question():
    """채점 단위가 문항이 아니라 **용어**다. `Term` 이 없으면 되짚을 수가 없다."""
    for rec in R.answer_sheet(good_doc())["questions"]:
        assert rec["Term"] == "PageRank"


def test_the_answer_sheet_numbers_the_choices_from_one_and_ends_with_dont_know():
    """사람이 적는 번호는 1부터다. 문항지의 `answer` 는 0부터라 자리가 하나 어긋난다."""
    rec = R.answer_sheet(good_doc())["questions"][0]
    assert list(rec["AnsChoices"]) == ["1", "2", "3", "4", "5"]
    assert rec["AnsChoices"]["5"] == R.DONT_KNOW


def test_the_answer_sheet_leaves_the_user_column_empty():
    """사람이 채울 자리는 비워서 낸다. 미리 채우면 안 푼 것이 답으로 실린다."""
    assert all(rec["UserAns"] == "" for rec in R.answer_sheet(good_doc())["questions"])


def test_the_answer_sheet_matches_the_shape_quiz_py_reads():
    """`src/term/python/runner/term/quiz.py` 의 `tallySheet` 가 읽는 열쇠 그대로여야 한다."""
    for rec in R.answer_sheet(good_doc())["questions"]:
        assert set(rec) == {"QNum", "Term", "Question", "AnsChoices", "UserAns"}


def test_flatten_keeps_the_order_the_sheet_was_built_in():
    """번호 규칙이 파이썬과 `quiz.py` 두 곳에 산다. 여기서 한 번 못 박아 둔다."""
    flat = R.flatten_questions(good_doc())
    assert [q["QNum"] for q in flat] == [1, 2, 3]
    assert [q["Term"] for q in flat] == ["PageRank"] * 3
    assert [q["Raw"].get("ask") for q in flat] == ["문항 0", "문항 1", "문항 2"]


# ── 5-2. 채운 기입란 검사 — quiz.py 도 같은 대조를 한다 ────────────────
def test_a_fully_filled_sheet_has_no_complaints():
    assert R.validate_answers(filled_sheet(), good_doc()) == []


def test_choosing_dont_know_is_a_valid_answer():
    """"모르겠다" 는 답을 안 쓴 것이 아니라 고른 것이다."""
    assert R.validate_answers(filled_sheet(picks=(5, 5, 5)), good_doc()) == []


def test_a_blank_user_answer_is_caught():
    """**안 푼 것과 모르는 것은 다르다.** 자동으로 "모르겠다" 로 메우지 않는다."""
    sheet = filled_sheet()
    sheet["questions"][1]["UserAns"] = ""
    assert any("UserAns" in c and "2번" in c for c in R.validate_answers(sheet, good_doc()))


def test_a_user_answer_outside_the_choices_is_caught():
    sheet = filled_sheet()
    sheet["questions"][0]["UserAns"] = 9
    assert any("보기 밖" in c for c in R.validate_answers(sheet, good_doc()))


def test_a_number_written_as_text_is_accepted():
    """사람이 손으로 채우는 칸이라 `3` 과 `"3"` 이 섞인다. 둘 다 받는다."""
    assert R.validate_answers(filled_sheet(picks=("1", "2", "3")), good_doc()) == []


def test_a_missing_answer_is_caught():
    sheet = filled_sheet()
    del sheet["questions"][2]
    assert any("3번" in c for c in R.validate_answers(sheet, good_doc()))


def test_an_answer_to_a_question_that_was_never_asked_is_caught():
    sheet = filled_sheet()
    sheet["questions"].append({"QNum": 99, "Term": "PageRank",
                               "Question": "없던 물음", "AnsChoices": {}, "UserAns": 1})
    assert any("99번" in c for c in R.validate_answers(sheet, good_doc()))


def test_the_same_question_answered_twice_is_caught():
    sheet = filled_sheet()
    sheet["questions"].append(sheet["questions"][0].copy())
    assert any("둘 이상" in c for c in R.validate_answers(sheet, good_doc()))


def test_a_sheet_whose_terms_drifted_is_caught():
    """**번호 규칙이 두 언어에 살아서 필요한 검사다.**

    순서가 어긋나면 남의 답을 채점하고도 오류가 나지 않는다. 그래서 번호만 믿지 않고
    용어와 물음 문구를 같이 대조한다.
    """
    sheet = filled_sheet()
    sheet["questions"][0]["Term"] = "declmap.scan"
    assert any("어긋난다" in c for c in R.validate_answers(sheet, good_doc()))


def test_a_sheet_whose_question_text_drifted_is_caught():
    sheet = filled_sheet()
    sheet["questions"][0]["Question"] = "다른 물음이 되어 버렸다"
    assert any("물음 문구" in c for c in R.validate_answers(sheet, good_doc()))


def test_the_old_count_shaped_answers_file_is_rejected():
    """옛 꼴(`{용어: {correct, dontKnow}}`)을 주면 조용히 0점이 아니라 거부한다."""
    old = {"PageRank": {"correct": 2, "dontKnow": 1, "means": "그래프 중요도"}}
    assert any("기입란" in c for c in R.validate_answers(old, good_doc()))


# ── 7. 기계 단계의 명령줄 — 경로를 박지 않는다 ──────────────────────────
def test_collect_argv_names_the_plan_and_the_term_database():
    argv = R.collect_argv(root="/도구/뿌리", plan="/계획/plan.md", terms_db="/어느/terms-db.json")
    assert argv[0] == "python3"
    assert argv[1].endswith(os.path.join("runner", "term", "collect.py"))
    assert argv[2] == "/계획/plan.md" and argv[3] == "/어느/terms-db.json"


def test_collect_argv_always_names_the_term_database():
    """용어 사전은 필수다 — Mode 1.5 는 Mode 1 결과 없이 돌지 않는다."""
    argv = R.collect_argv(root="/r", plan="/p.md", terms_db="/db.json")
    assert argv[-2:] == ["/p.md", "/db.json"]


def test_grade_and_emit_argv_point_at_the_right_scripts():
    argv = R.grade_argv("/r", "/작업/answers.json", "/작업/questions.json")
    assert argv[1].endswith("quiz.py")
    assert R.emit_argv("/r", "/작업/term-grades.json")[1].endswith("emit.py")


def test_grade_argv_hands_over_both_files():
    """채운 기입란에는 정답이 없다. 문항지가 같이 가야 채점이 된다."""
    argv = R.grade_argv("/r", "/작업/answers.json", "/작업/questions.json")
    assert argv[2:] == ["/작업/answers.json", "/작업/questions.json"]


# ── 8. 보고 — 멈춘 것을 실패로 그리지 않는다 ────────────────────────────
def test_the_report_reuses_the_mode_1_table():
    rows: list[M.StageRow] = [{"stage": "collect", "seconds": 0.4, "ok": True,
                               "why": "", "usage": R.M.normalize_usage(None)}]
    text = R.format_run(rows, skipped=[], gate=None)
    assert "collect" in text and "합계" in text


def test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed():
    """재개해서 건너뛴 단계를 '실패' 로 그리면 읽는 사람이 오해한다."""
    text = R.format_run([{"stage": "grade", "seconds": 0.2, "ok": True, "why": "",
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[("collect", "term-candidates.json 이 이미 있다")],
                        gate=None)
    assert "건너뜀" in text and "collect" in text


def test_the_gate_is_appended_to_the_report_and_is_not_a_failure():
    text = R.format_run([{"stage": "collect", "seconds": 9.0, "ok": True, "why": "",
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[], gate="사람 차례 — answers.json 을 쓴다")
    assert "사람 차례" in text
    assert "실패" not in text


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


def test_a_shuffled_sheet_passes():
    doc = good_doc()
    doc["terms"].append({"term": "declmap.scan", "means": "선언을 훑는다",
                         "questions": [one_question(ask="문항 %d" % i, answer=(i + 1) % 3)
                                       for i in range(3)]})
    assert R.validate_questions(doc) == []


def test_the_shuffle_check_stays_quiet_on_a_tiny_sheet():
    """문항이 셋뿐이면 우연히 몰릴 수 있다. 표본이 적을 때 단정하지 않는다."""
    doc = good_doc()
    for q in doc["terms"][0]["questions"]:
        q["answer"] = 0
    assert R.validate_questions(doc) == []


def test_known_terms_that_were_neither_asked_nor_excluded_are_reported():
    """출제도 안 되고 `excluded` 에도 안 적힌 용어를 잡는다 — 무엇이 빠졌는지 보여야
    범위를 좁힌 것인지 잊은 것인지 사람이 구별할 수 있다.
    """
    cand: dict[str, Any] = {"known": {"PageRank": {}, "declmap.scan": {}, "warmup.save": {}}}
    doc = good_doc()                       # PageRank 만 출제됐다
    doc["excluded"] = [{"term": "declmap.scan", "why": "계획서에 정의가 없다"}]
    assert R.unasked_known(cand, doc) == ["warmup.save"]


def test_nothing_is_reported_when_every_known_term_is_accounted_for():
    cand: dict[str, Any] = {"known": {"PageRank": {}}}
    assert R.unasked_known(cand, good_doc()) == []


def test_the_gate_notice_lists_the_silently_dropped_terms():
    text = R.gate_notice(questions="/작업/questions.json", sheet="/작업/t.json",
                         answers="/작업/answers.json", held=[],
                         answer_key="/작업/key.json", unasked=["warmup.save"])
    assert "warmup.save" in text
    assert "실패" not in text


# ── 7. 계획서별 작업 폴더 — 두 계획서가 같은 자리를 쓰면 한쪽이 죽는다 ──────
def test_plan_slug_strips_the_date_prefix():
    assert R.plan_slug("/a/b/2026-08-30-symbol-resolution-survey.md") == "symbol-resolution-survey"


def test_plan_slug_falls_back_to_the_bare_filename():
    """날짜 접두사가 없으면 확장자만 뗀 파일 이름을 그대로 쓴다 — 빈 문자열을 내지 않는다."""
    assert R.plan_slug("/a/b/plan.md") == "plan"


def test_two_plans_get_two_different_workdirs():
    a = R.default_workdir("/repo", "/plans/2026-08-30-symbol-resolution-survey.md")
    b = R.default_workdir("/repo", "/plans/2026-08-30-llm-load-reduction.md")
    assert a != b
    assert a == "/repo/out/mode1_5/symbol-resolution-survey"
    assert b == "/repo/out/mode1_5/llm-load-reduction"


def _m15(tmp_path: Path) -> R.Mode15Context:
    return R.Mode15Context(root=str(tmp_path), model="",
                           plan=str(tmp_path / "p.md"), workdir=str(tmp_path))


def test_답안이_없으면_그래프_끝에_관문이_붙는다(tmp_path: Path):
    g = R.build_mode1_5_graph(_m15(tmp_path), has_candidates=False,
                              has_answers=False, only=None, skip=None)
    assert g.order == ["collect", "gate"]


def test_답안이_있으면_관문이_없다(tmp_path: Path):
    g = R.build_mode1_5_graph(_m15(tmp_path), has_candidates=True,
                              has_answers=True, only=None, skip=None)
    assert g.order == ["grade", "emit"]


def test_관문은_GATE_로_흐름을_끝낸다(tmp_path: Path):
    g = R.build_mode1_5_graph(_m15(tmp_path), has_candidates=False,
                              has_answers=False, only=None, skip=None)
    assert g.stages["gate"].emits & P.GATE
    assert g.next_of("gate", P.GATE) is None


def test_문항지가_없으면_관문은_아무것도_하지_않는다(tmp_path: Path):
    ctx = _m15(tmp_path)
    out = R.GateStage().perform(ctx)
    assert out.kind == P.OK
    assert out.rows == []
    assert ctx.gate is None


def test_문항지가_있으면_관문이_기입란을_깔고_안내를_남긴다(tmp_path: Path):
    (tmp_path / R.QUESTIONS).write_text(
        json.dumps(good_doc(), ensure_ascii=False), encoding="utf-8")
    ctx = _m15(tmp_path)
    out = R.GateStage().perform(ctx)
    assert out.kind == P.GATE
    assert os.path.exists(tmp_path / R.SHEET)
    assert ctx.gate is not None and R.ANSWERS in ctx.gate


# ── --ask — CLI 가 대화형 세션을 띄워 term-benchmark 스킬이 출제·문답한다 ─────────
def _claude_found(name: str) -> str | None:
    return "/usr/local/bin/claude"


def _claude_missing(name: str) -> str | None:
    return None


def _session_left_nothing(argv: Sequence[str], cwd: str) -> int:
    return 0


def test_ask_를_주면_사람_차례_자리에_ask_가_서고_채점이_뒤따른다():
    """답안이 없을 때만 `ask` 가 들어가고, 그 뒤에 `grade` `emit` 이 이어진다."""
    assert R.plan_stages(has_candidates=False, has_answers=False, ask=True) == ["collect", "ask", "grade", "emit"]
    assert R.plan_stages(has_candidates=True, has_answers=False, ask=True) == ["ask", "grade", "emit"]
    assert R.plan_stages(has_candidates=True, has_answers=True, ask=True) == ["grade", "emit"]     # 답안이 있으면 물을 것이 없다


def test_ask_는_LLM_을_부르는_유일한_단계다():
    assert R.is_agent_stage("ask") and R.AGENT_STAGES == {"ask"}
    assert [s for s in R.plan_stages(True, False) if R.is_agent_stage(s)] == []          # --ask 없이는 여전히 0


def test_ask_명령줄은_대화형_claude_에_스킬_호출을_첫_프롬프트로_준다(tmp_path: Path):
    argv = R.ask_argv("/root", "/plans/p.md", str(tmp_path), "/root/.venv/bin/python", "/대상/docs/codegraph/terms-db.json")
    assert argv[0] == "claude" and "-p" not in argv and "--print" not in argv
    prompt = argv[-1]
    assert prompt.startswith("/term-benchmark ") and "/plans/p.md" in prompt and str(tmp_path) in prompt
    assert R.ANSWERS in prompt and R.QUESTIONS in prompt and "run_mode1_5.py" in prompt
    assert "--terms-db" in prompt
    assert "--add-dir" in argv and str(tmp_path) in argv


def test_ask_첫_프롬프트는_한_줄이고_기입란_명령과_산출물_자리를_그대로_싣는다(tmp_path: Path):
    w = str(tmp_path)
    prompt = R.ask_argv("/root", "/plans/p.md", w, "/py", "/db.json")[-1]
    assert "\n" not in prompt
    assert "`/py /root/src/term/python/runner/run_mode1_5.py /plans/p.md --workdir %s --terms-db /db.json` 를 돌려 %s 로 깔고" % (w, os.path.join(w, R.SHEET)) in prompt
    assert "후보는 %s 에 이미 있다" % os.path.join(w, R.CANDIDATES) in prompt
    assert "채운 것을 %s 으로 둔 뒤" % os.path.join(w, R.ANSWERS) in prompt


def test_ask_그래프는_답안이_남지_않으면_GATE_로_끝나고_남으면_채점으로_간다(tmp_path: Path):
    g = R.build_mode1_5_graph(_m15(tmp_path), has_candidates=True, has_answers=False,
                              only=None, skip=None, ask=True)
    assert g.order == ["ask", "grade", "emit"]
    assert g.stages["ask"].emits & P.GATE
    assert g.next_of("ask", P.GATE) is None and g.next_of("ask", P.OK) == "grade"


def test_ask_는_터미널이_아니면_세션을_띄우지_않고_실패한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(R.sys.stdin, "isatty", lambda: False)
    launched: list[Sequence[str]] = []
    def spy(argv: Sequence[str], cwd: str) -> int:
        launched.append(argv)
        return 0
    monkeypatch.setattr(R, "run_interactive", spy)
    out = R.AskStage().perform(_m15(tmp_path))
    assert out.kind == P.FAIL and "터미널" in out.why and launched == []


def test_ask_뒤에_답안이_없으면_기입란을_깔고_GATE_로_멈춘다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(R.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(R.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(R.shutil, "which", _claude_found)
    (tmp_path / R.QUESTIONS).write_text(json.dumps(good_doc(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(R, "run_interactive", _session_left_nothing)      # 세션은 문항지만 남기고 끝났다고 치자
    ctx = _m15(tmp_path)
    out = R.AskStage().perform(ctx)
    assert out.kind == P.GATE and os.path.exists(tmp_path / R.SHEET) and ctx.gate is not None
    assert len(out.rows) == 1 and out.rows[0]["stage"] == "ask" and out.rows[0]["ok"]


def test_ask_뒤에_답안이_있으면_OK_로_채점에_넘긴다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(R.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(R.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(R.shutil, "which", _claude_found)
    def fake(argv: Sequence[str], cwd: str) -> int:
        (tmp_path / R.ANSWERS).write_text("{}", encoding="utf-8")
        return 0
    monkeypatch.setattr(R, "run_interactive", fake)
    out = R.AskStage().perform(_m15(tmp_path))
    assert out.kind == P.OK and out.rows[0]["ok"]


def test_ask_는_claude_가_없으면_실패한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(R.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(R.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(R.shutil, "which", _claude_missing)
    out = R.AskStage().perform(_m15(tmp_path))
    assert out.kind == P.FAIL and "claude" in out.why


def test_term_script_paths_actually_exist() -> None:
    """Mode 1.5 가 부르는 얼갈이 스크립트가 디스크에 실재하는가. 문자열 대조는 디렉토리 개편을 못 잡는다."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for name in ("collect.py", "emit.py", "quiz.py"):
        # 경로를 만드는 곳이 모듈 전용 헬퍼뿐이라 그것을 들여다본다. 공개로 올리면 계약에 없는 이름이 는다.
        p = R._term_script(root, name)  # pyright: ignore[reportPrivateUsage]
        assert os.path.isfile(p), f"Mode 1.5 가 없는 파일을 가리킨다: {p}"
