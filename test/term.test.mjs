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

test("한 용어당 문항 수는 5개다", () => {
  assert.equal(QUESTIONS_PER_TERM, 5);
});

test("gradeOne 은 4개 이상 맞히면 확실로 매긴다", () => {
  assert.equal(gradeOne({ correct: 5, dontKnow: 0 }).mental, "확실");
  assert.equal(gradeOne({ correct: 4, dontKnow: 0 }).mental, "확실");
});

test("gradeOne 은 2~3개 맞히면 애매로 매긴다", () => {
  assert.equal(gradeOne({ correct: 3, dontKnow: 0 }).mental, "애매");
  assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).mental, "애매");
});

test("gradeOne 은 거의 못 맞히면 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).mental, "모름");
  assert.equal(gradeOne({ correct: 0, dontKnow: 0 }).mental, "모름");
});

test("gradeOne 은 모른다를 3회 이상 고르면 정답률과 무관하게 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 2, dontKnow: 3 }).mental, "모름");
});

test("gradeOne 은 정답률을 함께 돌려준다", () => {
  assert.equal(gradeOne({ correct: 4, dontKnow: 0 }).rate, 80);
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).rate, 20);
});
