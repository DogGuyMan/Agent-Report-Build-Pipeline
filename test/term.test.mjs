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
