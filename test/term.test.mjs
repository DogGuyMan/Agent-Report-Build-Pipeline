import { test } from "node:test";
import assert from "node:assert/strict";
import { pickTerms, findNewConcepts } from "../scripts/term/collect.mjs";

test("pickTerms 는 Plan 본문에 나오는 코드베이스 용어만 고른다", () => {
  const db = {
    Renderer: { kind: "class", means: "render 모듈의 class." },
    Unused: { kind: "class", means: "안 쓰이는 것." },
  };
  const plan = "이 계획은 Renderer 를 고친다.";
  const got = pickTerms(db, plan);
  assert.deepEqual(Object.keys(got), ["Renderer"]);
});

test("pickTerms 는 낱말 경계를 지킨다", () => {
  const db = { Ray: { kind: "class", means: "x" } };
  assert.deepEqual(Object.keys(pickTerms(db, "Raycast 를 쓴다")), []);
  assert.deepEqual(Object.keys(pickTerms(db, "Ray 를 쓴다")), ["Ray"]);
});

test("findNewConcepts 는 Plan 이 새로 만든 식별자를 찾는다", () => {
  const db = { Renderer: { kind: "class", means: "x" } };
  const plan = "C-19 결정에 따라 calls[] 를 roslyn-dump.json 에 넣는다. Renderer 는 그대로다.";
  const got = findNewConcepts(db, plan);
  assert.deepEqual(got.sort(), ["C-19", "calls[]", "roslyn-dump.json"]);
});

test("findNewConcepts 는 이미 DB 에 있는 것을 새 개념으로 세지 않는다", () => {
  const db = { "calls[]": { kind: "field", means: "x" } };
  assert.deepEqual(findNewConcepts(db, "calls[] 를 쓴다"), []);
});

import { gradeOne, QUESTIONS_PER_TERM } from "../scripts/term/quiz.mjs";

test("한 용어당 문항 수는 3개다", () => {
  assert.equal(QUESTIONS_PER_TERM, 3);
});

test("gradeOne 은 2개 이상 맞히면 확실로 매긴다", () => {
  assert.equal(gradeOne({ correct: 3, dontKnow: 0 }).mental, "확실");
  assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).mental, "확실");
});

test("gradeOne 은 1개 이하로 맞히면 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).mental, "모름");
  assert.equal(gradeOne({ correct: 0, dontKnow: 0 }).mental, "모름");
});

test("gradeOne 은 모른다를 2회 이상 고르면 정답률과 무관하게 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 1, dontKnow: 2 }).mental, "모름");
  assert.equal(gradeOne({ correct: 0, dontKnow: 3 }).mental, "모름");
});

test("gradeOne 은 애매를 내지 않는다 — 3문항 규칙은 확실 / 모름 두 갈래다", () => {
  for (let c = 0; c <= 3; c++) {
    assert.notEqual(gradeOne({ correct: c, dontKnow: 0 }).mental, "애매");
  }
});

test("gradeOne 은 정답률을 함께 돌려준다", () => {
  assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).rate, 67);
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).rate, 33);
});

import { toTermsDb, toStudyNote } from "../scripts/term/emit.mjs";

const SAMPLE = {
  "calls[]": { means: "누가 누구를 부르는지 모은 목록", mental: "모름", rate: 20 },
  Renderer: { means: "render 모듈의 class", mental: "확실", rate: 100 },
};

test("toTermsDb 는 확실한 것도 빠뜨리지 않는다", () => {
  const db = toTermsDb(SAMPLE);
  assert.equal(Object.keys(db).length, 2, "확실로 판정된 것이 빠졌다");
});

test("toTermsDb 는 정답과 이해도를 다른 필드에 담는다", () => {
  const db = toTermsDb(SAMPLE);
  assert.equal(db["calls[]"].TermMeans, "누가 누구를 부르는지 모은 목록");
  assert.equal(db["calls[]"].UserMentalValue, "모름");
});

test("toStudyNote 는 모름과 애매만 싣는다", () => {
  const md = toStudyNote(SAMPLE);
  assert.ok(md.includes("calls[]"), "모름인 용어가 학습 노트에 없다");
  assert.ok(!md.includes("Renderer"), "확실한 용어가 학습 노트에 들어갔다");
});

test("toStudyNote 는 학습할 것이 없으면 그 사실을 적는다", () => {
  const md = toStudyNote({ A: { means: "x", mental: "확실", rate: 100 } });
  assert.ok(md.includes("학습할 용어가 없다"));
});

// ── 기입란 채점 — 사람이 세던 자리를 기계가 가져간 곳 ────────────────────
import {
  flattenQuestions,
  choiceNumber,
  tallySheet,
  gradeAll,
  CHOICES_PER_QUESTION,
} from "../scripts/term/quiz.mjs";

/** 검사를 통과하는 문항 하나. `codegraph/test_run_mode1_5.py` 의 `one_question` 과 같은 꼴이다. */
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

/** 용어 하나 · 문항 셋. 정답은 차례대로 1 · 2 · 3번 보기다(`answer` 가 0부터라 하나 크다). */
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

/** 기입란을 만들고 `UserAns` 를 채운 것. `picks` 는 문항 차례대로 고른 보기 번호. */
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

test("보기 수는 다섯이다 — 실제 뜻 넷에 모르겠다 하나", () => {
  assert.equal(CHOICES_PER_QUESTION, 5);
});

test("flattenQuestions 는 용어를 건너뛰며 1부터 번호를 잇는다", () => {
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
});

test("flattenQuestions 는 0부터인 정답 자리를 1부터인 보기 번호로 옮긴다", () => {
  // 기입란의 UserAns 가 1부터라, 여기서 자릿수를 맞춰 두고 뒤에서는 그냥 견준다.
  assert.deepEqual(
    flattenQuestions(goodDoc()).map((q) => q.Answer),
    [1, 2, 3],
  );
});

test("choiceNumber 는 숫자와 숫자 문자열을 둘 다 받는다", () => {
  assert.equal(choiceNumber(3), 3);
  assert.equal(choiceNumber("3"), 3);
  assert.equal(choiceNumber(" 3 "), 3);
});

test("choiceNumber 는 빈 칸을 모르겠다로 메우지 않는다", () => {
  // 안 푼 것과 모르는 것은 다르다. 메우면 그 차이가 점수에 조용히 섞인다.
  assert.equal(choiceNumber(""), null);
  assert.equal(choiceNumber(null), null);
  assert.equal(choiceNumber(undefined), null);
  assert.equal(choiceNumber("셋"), null);
});

test("tallySheet 는 맞힌 수를 사람 대신 센다", () => {
  const doc = goodDoc();
  const { counts, problems } = tallySheet(filledSheet(doc, [1, 2, 3]), doc);
  assert.deepEqual(problems, []);
  assert.deepEqual(counts.PageRank, {
    correct: 3,
    dontKnow: 0,
    means: "그래프에서 중요한 점을 매기는 방법",
  });
});

test("tallySheet 는 마지막 보기를 고른 것을 모르겠다로 센다", () => {
  const doc = goodDoc();
  const { counts } = tallySheet(filledSheet(doc, [5, 5, 3]), doc);
  assert.equal(counts.PageRank.dontKnow, 2);
  assert.equal(counts.PageRank.correct, 1);
});

test("tallySheet 는 틀린 답을 맞힌 것으로 세지 않는다", () => {
  const doc = goodDoc();
  const { counts } = tallySheet(filledSheet(doc, [2, 1, 3]), doc);
  assert.equal(counts.PageRank.correct, 1);
  assert.equal(counts.PageRank.dontKnow, 0);
});

test("tallySheet 는 빈 칸을 잡아내고 채점을 막는다", () => {
  const doc = goodDoc();
  const { problems } = tallySheet(filledSheet(doc, [1, "", 3]), doc);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /UserAns/);
});

test("tallySheet 는 보기 밖 번호를 잡아낸다", () => {
  const doc = goodDoc();
  const { problems } = tallySheet(filledSheet(doc, [1, 2, 9]), doc);
  assert.match(problems.join(" "), /보기 밖/);
});

test("tallySheet 는 용어가 어긋난 답안을 채점하지 않는다", () => {
  // 번호 규칙이 파이썬과 여기 두 곳에 산다. 어긋나면 남의 답을 채점하고도 조용하다.
  const doc = goodDoc();
  const sheet = filledSheet(doc, [1, 2, 3]);
  sheet.questions[0].Term = "declmap.scan";
  const { problems } = tallySheet(sheet, doc);
  assert.match(problems.join(" "), /어긋난다/);
});

test("tallySheet 는 물음 문구가 다른 답안을 채점하지 않는다", () => {
  const doc = goodDoc();
  const sheet = filledSheet(doc, [1, 2, 3]);
  sheet.questions[0].Question = "다른 물음이 되어 버렸다";
  assert.match(tallySheet(sheet, doc).problems.join(" "), /물음 문구/);
});

test("tallySheet 는 빠진 답안과 남는 답안을 둘 다 잡는다", () => {
  const doc = goodDoc();
  const sheet = filledSheet(doc, [1, 2, 3]);
  sheet.questions.pop();
  sheet.questions.push({ QNum: 99, Term: "PageRank", Question: "없던 물음", UserAns: 1 });
  const joined = tallySheet(sheet, doc).problems.join(" ");
  assert.match(joined, /3번/);
  assert.match(joined, /99번/);
});

test("tallySheet 는 옛 카운트 꼴 답안 파일을 거부한다", () => {
  const doc = goodDoc();
  const old = { PageRank: { correct: 2, dontKnow: 1, means: "그래프 중요도" } };
  assert.match(tallySheet(old, doc).problems.join(" "), /기입란/);
});

test("tallySheet 의 산출물은 gradeAll 이 그대로 받는 꼴이다", () => {
  const doc = goodDoc();
  const { counts } = tallySheet(filledSheet(doc, [1, 2, 5]), doc);
  assert.deepEqual(gradeAll(counts), {
    PageRank: { rate: 67, mental: "확실", means: "그래프에서 중요한 점을 매기는 방법" },
  });
});
