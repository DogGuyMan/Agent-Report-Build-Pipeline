"""test_run_mode1_5.py — Mode 1.5 실행기의 회귀 시험.

**왜 필요한가.** Mode 1.5 는 **사람의 이해도를 재는** 파이프라인이다. 그래서 다른
실행기라면 사소했을 실수가 여기서는 측정 자체를 무너뜨린다. 무너져도 오류가 나지
않고 그럴듯한 표가 나온다는 것이 더 나쁘다.

  1. 사람 관문   `claude -p` 는 되물을 수 없다. 사람 자리에 헤드리스 에이전트를 넣으면
                 답을 지어내고, 그러면 "사람이 아는가" 를 잰다는 목적이 죽는다.
                 실행기는 답안이 없으면 **반드시 멈춰야** 한다.
  2. 재개        멈춘 뒤 다시 돌릴 때 이미 만든 산출물을 다시 만들면 안 된다.
                 특히 문항을 다시 내면 사람이 이미 푼 시험과 어긋난다.
  3. 정답 미정   뜻이 정해지지 않은 개념을 출제하면 채점이 불가능하다.
                 기계 규칙은 하나뿐이다 — **정답 문구가 있느냐.**
  4. 문항 검사   "모른다" 가 마지막에 없거나 문항 수가 셋이 아니면 `quiz.mjs` 의
                 채점 구간(맞힌 수 2 이상 -> 확실)이 뜻을 잃는다. 그런데 `quiz.mjs` 는
                 그것을 검사하지 않고 조용히 채점한다.
  5. 이어짐      `questions.json` 에서 `answers.json` 으로 바로 이어지지 않으면
                 사람이 손으로 형식을 옮기다 틀린다.

  .venv/bin/python -m pytest codegraph/test_run_mode1_5.py -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1_5 as R  # noqa: E402


# ── 재료 ────────────────────────────────────────────────────────────────
def one_question(ask="PageRank 는 무엇을 하는가?", answer=0):
    """검사를 통과하는 문항 하나. 시험마다 한 군데씩만 망가뜨려 쓴다."""
    return {"ask": ask,
            "choices": ["그래프에서 중요한 점을 매긴다",
                        "파일을 줄 단위로 센다",
                        "주석을 소스에 심는다",
                        "모른다"],
            "answer": answer}


def good_doc():
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
    """아무것도 없으면 모으고 출제하고 **거기서 끝난다.** 답안은 사람이 쓴다."""
    assert R.plan_stages(has_candidates=False, has_questions=False,
                         has_answers=False) == ["collect", "author"]


def test_grading_only_starts_once_a_human_answered():
    """답안이 생긴 뒤에야 채점과 산출이 붙는다."""
    assert R.plan_stages(has_candidates=True, has_questions=True,
                         has_answers=True) == ["grade", "emit"]


def test_only_one_stage_calls_the_model():
    """모형을 부르는 자리는 `author` **하나**다. 보충과 출제를 한 세션에서 이어 한다."""
    stages = R.plan_stages(False, False, True)
    assert [s for s in stages if R.is_agent_stage(s)] == ["author"]


def test_collect_is_skipped_when_candidates_already_exist():
    """다시 모으면 앞 실행이 쌓은 후보 파일을 덮어쓴다."""
    assert "collect" not in R.plan_stages(has_candidates=True, has_questions=False,
                                          has_answers=False)


def test_authoring_is_skipped_when_questions_already_exist():
    """문항을 다시 내면 사람이 이미 푼 시험과 어긋난다. 돈도 두 번 든다."""
    assert R.plan_stages(has_candidates=True, has_questions=True,
                         has_answers=False) == []


def test_only_and_skip_are_honoured():
    assert R.plan_stages(False, False, True, only=["grade"]) == ["grade"]
    assert "emit" not in R.plan_stages(False, False, True, skip=["emit"])


def test_an_unknown_stage_is_rejected():
    with pytest.raises(ValueError):
        R.plan_stages(False, False, False, only=["없는단계"])


# ── 2. 사람 관문 — 실행기가 멈추는 자리 ─────────────────────────────────
def test_the_gate_is_open_until_a_human_writes_answers():
    """`claude -p` 는 되물을 수 없다. 답안이 없으면 멈추는 것 말고 할 일이 없다."""
    assert R.human_gate_open(has_answers=False) is True
    assert R.human_gate_open(has_answers=True) is False


def test_the_gate_notice_tells_the_human_exactly_which_files_to_touch():
    """멈췄을 때 사람이 무엇을 해야 하는지 화면만 보고 알 수 있어야 한다."""
    text = R.gate_notice(questions="/작업/questions.json",
                         template="/작업/answers-template.json",
                         answers="/작업/answers.json",
                         held=["E402", "mode1-nochange.json"],
                         answer_key="/작업/term-answer-key.json")
    assert "/작업/questions.json" in text
    assert "/작업/answers.json" in text
    assert "/작업/answers-template.json" in text
    # 출제에서 빠진 개념과 그것을 되살리는 방법을 함께 알린다
    assert "E402" in text and "/작업/term-answer-key.json" in text
    assert "term-benchmark" in text          # 묻는 절차는 스킬의 일이다
    assert "실패" not in text                 # 멈춘 것은 실패가 아니다


def test_the_gate_notice_stays_quiet_when_nothing_was_held_back():
    text = R.gate_notice(questions="/작업/questions.json",
                         template="/작업/answers-template.json",
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
    """`E402`(린트 코드)든 진짜 개념이든 규칙은 같다 — 정답이 있으면 낸다.

    오탐 여부를 기계가 판정하면 그 판정이 틀렸을 때 되돌릴 자리가 없다.
    """
    ready, _ = R.split_new_concepts(["E402"], {"E402": "파이썬 린트가 내는 코드"})
    assert ready == ["E402"]


# ── 4. 문항 검사 — quiz.mjs 는 이것을 검사하지 않는다 ───────────────────
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
        "모른다", "그래프에서 중요한 점을 매긴다", "파일을 줄 단위로 센다", "잘 모르겠다"]
    assert any("모른다" in c for c in R.validate_questions(doc))


def test_the_answer_may_not_point_at_dont_know():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 3     # 마지막 = "모른다"
    assert any("정답" in c for c in R.validate_questions(doc))


def test_an_answer_outside_the_choices_is_caught():
    doc = good_doc()
    doc["terms"][0]["questions"][0]["answer"] = 9
    assert R.validate_questions(doc) != []


def test_duplicate_choices_are_caught():
    """같은 보기가 둘이면 정답이 둘이 되거나 보기 수가 준다."""
    doc = good_doc()
    q = doc["terms"][0]["questions"][0]
    q["choices"] = ["같은 말", "같은 말", "다른 말", "모른다"]
    assert any("겹친" in c for c in R.validate_questions(doc))


def test_too_few_choices_are_caught():
    """보기 3~4개 + 모른다 = 넷에서 다섯. 둘뿐이면 찍어서 맞힐 확률이 절반이다."""
    doc = good_doc()
    doc["terms"][0]["questions"][0]["choices"] = ["그래프 어쩌고", "모른다"]
    assert any("보기" in c for c in R.validate_questions(doc))


def test_a_term_without_a_meaning_is_caught():
    """`means` 가 비면 `emit` 이 뜻 없는 용어집을 낸다."""
    doc = good_doc()
    doc["terms"][0]["means"] = ""
    assert any("means" in c or "뜻" in c for c in R.validate_questions(doc))


def test_a_sheet_with_no_terms_is_caught():
    assert R.validate_questions({"terms": []}) != []


# ── 5. questions.json 에서 answers.json 으로 바로 이어진다 ──────────────
def test_the_answer_template_keeps_the_meaning_and_zeroes_the_counts():
    """사람은 숫자 두 개만 채우면 된다. 뜻을 손으로 옮기다 틀리는 자리를 없앤다."""
    t = R.answers_template(good_doc())
    assert t == {"PageRank": {"correct": 0, "dontKnow": 0,
                              "means": "그래프에서 중요한 점을 매기는 방법"}}


def test_the_template_matches_the_shape_quiz_mjs_reads():
    """`scripts/term/quiz.mjs` 의 `gradeAll` 이 읽는 세 열쇠 그대로여야 한다."""
    for rec in R.answers_template(good_doc()).values():
        assert set(rec) == {"correct", "dontKnow", "means"}


def test_answers_may_not_count_more_responses_than_there_were_questions():
    """맞힌 수 + 모른다 가 3을 넘으면 사람이 세다 틀린 것이다. 채점 전에 잡는다."""
    bad = {"PageRank": {"correct": 3, "dontKnow": 2, "means": "뜻"}}
    assert any("3" in c for c in R.validate_answers(bad, good_doc()))


def test_answers_about_a_term_that_was_never_asked_are_caught():
    bad = {"없던용어": {"correct": 1, "dontKnow": 0, "means": "뜻"}}
    assert any("없던용어" in c for c in R.validate_answers(bad, good_doc()))


def test_a_missing_answer_is_caught():
    assert any("PageRank" in c for c in R.validate_answers({}, good_doc()))


def test_well_formed_answers_have_no_complaints():
    ok = {"PageRank": {"correct": 2, "dontKnow": 1, "means": "그래프 중요도"}}
    assert R.validate_answers(ok, good_doc()) == []


# ── 6. 에이전트 호출 — 한 번, 그리고 필요한 폴더를 다 열어 준다 ─────────
def test_author_argv_is_headless_json_and_opens_every_folder_it_reads():
    argv = R.author_argv(model="haiku", workdir="/작업",
                         root="/도구/뿌리", plan="/계획/plan.md")
    assert argv[0] == "claude" and "-p" in argv
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--model") + 1] == "haiku"
    dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
    # 작업 폴더(후보와 산출물) · 도구 뿌리(규약) · 계획서 폴더 셋을 다 봐야 한다
    assert "/작업" in dirs and "/도구/뿌리" in dirs and "/계획" in dirs


def test_author_argv_does_not_repeat_a_folder():
    """계획서가 작업 폴더 안에 있으면 같은 폴더가 두 번 열린다."""
    argv = R.author_argv(model="haiku", workdir="/작업",
                         root="/도구/뿌리", plan="/작업/plan.md")
    dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
    assert len(dirs) == len(set(dirs))


def test_the_prompt_carries_the_two_jobs_and_the_whole_question_discipline():
    """보충(3단계)과 출제(5단계)를 한 세션에서 이어 하고, 출제 규율을 다 싣는다."""
    p = R.author_prompt(workdir="/작업", root="/도구/뿌리", plan="/계획/plan.md")
    assert "/작업" in p and "/계획/plan.md" in p
    assert "term-candidates.json" in p and "questions.json" in p
    assert "3문항" in p and "모른다" in p
    assert "kind" in p and "module" in p        # 오답 보기를 어디서 가져오는가
    assert "섞" in p                             # 보기 순서를 섞는다
    assert "지어내" in p                          # 뜻을 지어내지 않는다
    assert "term-answer-key.json" in p           # 정답 미정은 사람에게 넘긴다


def test_the_prompt_forbids_asking_the_human():
    """헤드리스 세션은 되물을 수 없다. 되물으려 하면 그대로 막힌다."""
    p = R.author_prompt(workdir="/작업", root="/도구/뿌리", plan="/계획/plan.md")
    assert "묻지 않는다" in p


# ── 7. 기계 단계의 명령줄 — 경로를 박지 않는다 ──────────────────────────
def test_collect_argv_names_the_plan_and_the_term_database():
    argv = R.collect_argv(root="/도구/뿌리", plan="/계획/plan.md", terms_db="/어느/terms-db.json")
    assert argv[0] == "node"
    assert argv[1].endswith(os.path.join("scripts", "term", "collect.mjs"))
    assert argv[2] == "/계획/plan.md" and argv[3] == "/어느/terms-db.json"


def test_collect_argv_works_without_a_term_database():
    """DB 가 없으면 코드베이스 용어는 0개다 — 그래도 신규 개념은 잡힌다."""
    assert R.collect_argv(root="/r", plan="/p.md", terms_db=None) == [
        "node", os.path.join("/r", "scripts", "term", "collect.mjs"), "/p.md"]


def test_grade_and_emit_argv_point_at_the_right_scripts():
    assert R.grade_argv("/r", "/작업/answers.json")[1].endswith("quiz.mjs")
    assert R.emit_argv("/r", "/작업/term-grades.json")[1].endswith("emit.mjs")


# ── 8. 보고 — 멈춘 것을 실패로 그리지 않는다 ────────────────────────────
def test_the_report_reuses_the_mode_1_table():
    rows = [{"stage": "collect", "seconds": 0.4, "ok": True,
             "usage": R.M.normalize_usage(None)}]
    text = R.format_run(rows, skipped=[], gate=None)
    assert "collect" in text and "합계" in text


def test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed():
    """재개해서 건너뛴 단계를 '실패' 로 그리면 읽는 사람이 오해한다."""
    text = R.format_run([{"stage": "grade", "seconds": 0.2, "ok": True,
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[("collect", "term-candidates.json 이 이미 있다")],
                        gate=None)
    assert "건너뜀" in text and "collect" in text


def test_the_gate_is_appended_to_the_report_and_is_not_a_failure():
    text = R.format_run([{"stage": "author", "seconds": 9.0, "ok": True,
                          "usage": R.M.normalize_usage(None)}],
                        skipped=[], gate="사람 차례 — answers.json 을 쓴다")
    assert "사람 차례" in text
    assert "실패" not in text


# ── 9. 실측에서 드러난 두 가지 (2026-08-30, haiku 마른 실행) ────────────
def test_an_unshuffled_sheet_is_caught():
    """정답이 전부 같은 자리에 있으면 사람이 **위치로** 맞힌다 — 이해도가 아니라 눈치를 잰다.

    실측 — haiku 로 돌린 첫 문항지 24문항의 정답이 전부 0번 자리였다.
    보기의 좋고 나쁨은 기계가 못 보지만 **자리가 한곳에 몰린 것은 볼 수 있다.**
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
    """조용히 빠진 용어를 잡는다.

    실측 — haiku 가 `known` 20개 중 8개만 내고 12개를 `excluded` 에도 안 적고 버렸다.
    시험 범위를 좁히는 것 자체는 정당하다(용어 20개면 60문항이다). 다만 **무엇이
    빠졌는지 사람이 봐야** 범위를 좁힌 것인지 잊은 것인지 구별할 수 있다.
    """
    cand = {"known": {"PageRank": {}, "declmap.scan": {}, "warmup.save": {}}}
    doc = good_doc()                       # PageRank 만 출제됐다
    doc["excluded"] = [{"term": "declmap.scan", "why": "계획서에 정의가 없다"}]
    assert R.unasked_known(cand, doc) == ["warmup.save"]


def test_nothing_is_reported_when_every_known_term_is_accounted_for():
    cand = {"known": {"PageRank": {}}}
    assert R.unasked_known(cand, good_doc()) == []


def test_the_gate_notice_lists_the_silently_dropped_terms():
    text = R.gate_notice(questions="/작업/questions.json", template="/작업/t.json",
                         answers="/작업/answers.json", held=[],
                         answer_key="/작업/key.json", unasked=["warmup.save"])
    assert "warmup.save" in text
    assert "실패" not in text
