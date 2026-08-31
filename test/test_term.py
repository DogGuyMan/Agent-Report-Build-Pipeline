import pytest
import subprocess
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_js_eval(script_body: str) -> str:
    script = f"""
    import assert from "node:assert/strict";
    import {{ pickTerms, findNewConcepts }} from "./runner/term/collect.mjs";
    import {{ gradeOne, QUESTIONS_PER_TERM, flattenQuestions, choiceNumber, tallySheet, gradeAll, CHOICES_PER_QUESTION }} from "./runner/term/quiz.mjs";
    import {{ toTermsDb, toStudyNote }} from "./runner/term/emit.mjs";

    {script_body}
    """
    tmp_path = os.path.join(ROOT, ".tmp-term-eval.mjs")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(script)
    try:
        res = subprocess.run(["node", tmp_path], capture_output=True, text=True, cwd=ROOT)
        if res.returncode != 0:
            raise AssertionError(f"JS Error: {res.stderr}\n{res.stdout}")
        return res.stdout.strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_pickterms_picks_only_terms_in_plan():
    run_js_eval("""
    const db = {
      Renderer: { kind: "class", means: "render 모듈의 class." },
      Unused: { kind: "class", means: "안 쓰이는 것." },
    };
    const plan = "이 계획은 Renderer 를 고친다.";
    const got = pickTerms(db, plan);
    assert.deepEqual(Object.keys(got), ["Renderer"]);
    """)

def test_pickterms_keeps_word_boundaries():
    run_js_eval("""
    const db = { Ray: { kind: "class", means: "x" } };
    assert.deepEqual(Object.keys(pickTerms(db, "Raycast 를 쓴다")), []);
    assert.deepEqual(Object.keys(pickTerms(db, "Ray 를 쓴다")), ["Ray"]);
    """)

def test_findnewconcepts_finds_new_identifiers():
    run_js_eval("""
    const db = { Renderer: { kind: "class", means: "x" } };
    const plan = "C-19 결정에 따라 calls[] 를 roslyn-dump.json 에 넣는다. Renderer 는 그대로다.";
    const got = findNewConcepts(db, plan);
    assert.deepEqual(got.sort(), ["C-19", "calls[]", "roslyn-dump.json"]);
    """)

def test_findnewconcepts_ignores_existing_terms():
    run_js_eval("""
    const db = { "calls[]": { kind: "field", means: "x" } };
    assert.deepEqual(findNewConcepts(db, "calls[] 를 쓴다"), []);
    """)

def test_questions_per_term():
    run_js_eval("""
    assert.equal(QUESTIONS_PER_TERM, 3);
    """)

def test_gradeone_assigns_certain_for_2_or_more_correct():
    run_js_eval("""
    assert.equal(gradeOne({ correct: 3, dontKnow: 0 }).mental, "확실");
    assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).mental, "확실");
    """)

def test_gradeone_assigns_unknown_for_1_or_less_correct():
    run_js_eval("""
    assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).mental, "모름");
    assert.equal(gradeOne({ correct: 0, dontKnow: 0 }).mental, "모름");
    """)

def test_gradeone_assigns_unknown_for_2_or_more_dontknow():
    run_js_eval("""
    assert.equal(gradeOne({ correct: 1, dontKnow: 2 }).mental, "모름");
    assert.equal(gradeOne({ correct: 0, dontKnow: 3 }).mental, "모름");
    """)

def test_gradeone_does_not_produce_ambiguous():
    run_js_eval("""
    for (let c = 0; c <= 3; c++) {
      assert.notEqual(gradeOne({ correct: c, dontKnow: 0 }).mental, "애매");
    }
    """)

def test_gradeone_returns_accuracy_rate():
    run_js_eval("""
    assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).rate, 67);
    assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).rate, 33);
    """)


def test_totermsdb_includes_certain_terms():
    run_js_eval("""
    const SAMPLE = {
      "calls[]": { means: "누가 누구를 부르는지 모은 목록", mental: "모름", rate: 20 },
      Renderer: { means: "render 모듈의 class", mental: "확실", rate: 100 },
    };
    const db = toTermsDb(SAMPLE);
    assert.equal(Object.keys(db).length, 2, "확실로 판정된 것이 빠졌다");
    """)

def test_totermsdb_separates_answer_and_understanding():
    run_js_eval("""
    const SAMPLE = {
      "calls[]": { means: "누가 누구를 부르는지 모은 목록", mental: "모름", rate: 20 },
      Renderer: { means: "render 모듈의 class", mental: "확실", rate: 100 },
    };
    const db = toTermsDb(SAMPLE);
    assert.equal(db["calls[]"].TermMeans, "누가 누구를 부르는지 모은 목록");
    assert.equal(db["calls[]"].UserMentalValue, "모름");
    """)

def test_tostudynote_includes_only_unknown_and_ambiguous():
    run_js_eval("""
    const SAMPLE = {
      "calls[]": { means: "누가 누구를 부르는지 모은 목록", mental: "모름", rate: 20 },
      Renderer: { means: "render 모듈의 class", mental: "확실", rate: 100 },
    };
    const md = toStudyNote(SAMPLE);
    assert.ok(md.includes("calls[]"), "모름인 용어가 학습 노트에 없다");
    assert.ok(!md.includes("Renderer"), "확실한 용어가 학습 노트에 들어갔다");
    """)

def test_tostudynote_indicates_when_nothing_to_study():
    run_js_eval("""
    const md = toStudyNote({ A: { means: "x", mental: "확실", rate: 100 } });
    assert.ok(md.includes("학습할 용어가 없다"));
    """)

# quiz sheet processing

JS_HELPERS = """
function oneQuestion(ask, answer) {
  return {
    ask,
    choices: [
      "그래프에서 중요한 점을 매긴다",
      "파일을 줄 단위로 센다",
      "주석을 소스에 심는다",
      "선언을 훑어 목록으로 만든다",
      "모르겠다",
    ],
    answer,
  };
}

function goodDoc() {
  return {
    plan: "/어느/plan.md",
    terms: [
      {
        term: "PageRank",
        means: "그래프에서 중요한 점을 매기는 방법",
        questions: [0, 1, 2].map((i) => oneQuestion(`문항 ${i}`, i)),
      },
    ],
  };
}

function filledSheet(doc, picks) {
  return {
    plan: doc.plan,
    questions: flattenQuestions(doc).map((q, i) => ({
      QNum: q.QNum,
      Term: q.Term,
      Question: q.Question,
      AnsChoices: {},
      UserAns: picks[i],
    })),
  };
}
"""

def run_js_quiz_eval(script_body: str) -> str:
    return run_js_eval(JS_HELPERS + script_body)

def test_choices_per_question():
    run_js_quiz_eval("""
    assert.equal(CHOICES_PER_QUESTION, 5);
    """)

def test_flattenquestions_numbers_sequentially_across_terms():
    run_js_quiz_eval("""
    const doc = goodDoc();
    doc.terms.push({
      term: "declmap.scan",
      means: "선언을 훑는다",
      questions: [0, 1, 2].map((i) => oneQuestion(`둘째 ${i}`, i)),
    });
    assert.deepEqual(
      flattenQuestions(doc).map((q) => q.QNum),
      [1, 2, 3, 4, 5, 6],
    );
    assert.deepEqual(
      flattenQuestions(doc).map((q) => q.Term),
      ["PageRank", "PageRank", "PageRank", "declmap.scan", "declmap.scan", "declmap.scan"],
    );
    """)

def test_flattenquestions_shifts_answer_to_1_based_index():
    run_js_quiz_eval("""
    assert.deepEqual(
      flattenQuestions(goodDoc()).map((q) => q.Answer),
      [1, 2, 3],
    );
    """)

def test_choicenumber_accepts_numbers_and_strings():
    run_js_quiz_eval("""
    assert.equal(choiceNumber(3), 3);
    assert.equal(choiceNumber("3"), 3);
    assert.equal(choiceNumber(" 3 "), 3);
    """)

def test_choicenumber_does_not_fill_blanks_with_dontknow():
    run_js_quiz_eval("""
    assert.equal(choiceNumber(""), null);
    assert.equal(choiceNumber(null), null);
    assert.equal(choiceNumber(undefined), null);
    assert.equal(choiceNumber("셋"), null);
    """)

def test_tallysheet_counts_correct_answers():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { counts, problems } = tallySheet(filledSheet(doc, [1, 2, 3]), doc);
    assert.deepEqual(problems, []);
    assert.deepEqual(counts.PageRank, {
      correct: 3,
      dontKnow: 0,
      means: "그래프에서 중요한 점을 매기는 방법",
    });
    """)

def test_tallysheet_counts_last_choice_as_dontknow():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { counts } = tallySheet(filledSheet(doc, [5, 5, 3]), doc);
    assert.equal(counts.PageRank.dontKnow, 2);
    assert.equal(counts.PageRank.correct, 1);
    """)

def test_tallysheet_does_not_count_wrong_answers_as_correct():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { counts } = tallySheet(filledSheet(doc, [2, 1, 3]), doc);
    assert.equal(counts.PageRank.correct, 1);
    assert.equal(counts.PageRank.dontKnow, 0);
    """)

def test_tallysheet_catches_blanks_and_blocks_grading():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { problems } = tallySheet(filledSheet(doc, [1, "", 3]), doc);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /UserAns/);
    """)

def test_tallysheet_catches_out_of_bounds_numbers():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { problems } = tallySheet(filledSheet(doc, [1, 2, 9]), doc);
    assert.match(problems.join(" "), /보기 밖/);
    """)

def test_tallysheet_does_not_grade_answers_with_mismatched_terms():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const sheet = filledSheet(doc, [1, 2, 3]);
    sheet.questions[0].Term = "declmap.scan";
    const { problems } = tallySheet(sheet, doc);
    assert.match(problems.join(" "), /어긋난다/);
    """)

def test_tallysheet_does_not_grade_answers_with_mismatched_question_text():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const sheet = filledSheet(doc, [1, 2, 3]);
    sheet.questions[0].Question = "다른 물음이 되어 버렸다";
    assert.match(tallySheet(sheet, doc).problems.join(" "), /물음 문구/);
    """)

def test_tallysheet_catches_missing_and_extra_answers():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const sheet = filledSheet(doc, [1, 2, 3]);
    sheet.questions.pop();
    sheet.questions.push({ QNum: 99, Term: "PageRank", Question: "없던 물음", UserAns: 1 });
    const joined = tallySheet(sheet, doc).problems.join(" ");
    assert.match(joined, /3번/);
    assert.match(joined, /99번/);
    """)

def test_tallysheet_rejects_old_count_format_files():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const old = { PageRank: { correct: 2, dontKnow: 1, means: "그래프 중요도" } };
    assert.match(tallySheet(old, doc).problems.join(" "), /기입란/);
    """)

def test_tallysheet_output_matches_gradeall_input():
    run_js_quiz_eval("""
    const doc = goodDoc();
    const { counts } = tallySheet(filledSheet(doc, [1, 2, 5]), doc);
    assert.deepEqual(gradeAll(counts), {
      PageRank: { rate: 67, mental: "확실", means: "그래프에서 중요한 점을 매기는 방법" },
    });
    """)
