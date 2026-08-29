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
