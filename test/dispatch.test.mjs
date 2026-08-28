import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveScript } from "../scripts/dispatch.mjs";

test("resolveScript 는 등록된 명령을 스크립트 경로로 바꾼다", () => {
  const table = { init: "scripts/init.mjs", build: "scripts/build.mjs" };
  assert.equal(resolveScript(table, "init"), "scripts/init.mjs");
});

test("resolveScript 는 없는 명령에 null 을 낸다", () => {
  const table = { init: "scripts/init.mjs" };
  assert.equal(resolveScript(table, "nope"), null);
});

test("resolveScript 는 명령이 없으면 null 을 낸다", () => {
  assert.equal(resolveScript({ init: "x" }, undefined), null);
});

test("resolveScript 는 프로토타입 오염을 통과시키지 않는다", () => {
  assert.equal(resolveScript({ init: "x" }, "toString"), null);
});
