import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSpecFilename, findSimilar } from "../scripts/init.mjs";

test("parseSpecFilename 은 날짜와 slug 를 분리한다", () => {
  assert.deepEqual(
    parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md"),
    { date: "2026-07-27", slug: "geometry-winding-ownership" },
  );
});

test("parseSpecFilename 은 slug 에 하이픈이 많아도 정확히 자른다", () => {
  assert.deepEqual(
    parseSpecFilename("2026-05-20-sp1-shader-program-resource-consolidation-design.md"),
    { date: "2026-05-20", slug: "sp1-shader-program-resource-consolidation" },
  );
});

test("parseSpecFilename 은 -design.md 로 안 끝나면 null", () => {
  assert.equal(parseSpecFilename("2026-07-27-geometry-winding-ownership-before.svg"), null);
  assert.equal(parseSpecFilename("2026-07-27-geometry-winding-ownership-design-review.html"), null);
});

test("parseSpecFilename 은 날짜 형식이 아니면 null", () => {
  assert.equal(parseSpecFilename("26-7-27-my-topic-design.md"), null);
  assert.equal(parseSpecFilename("not-a-date-my-topic-design.md"), null);
});

test("parseSpecFilename 은 무관한 파일명에 null", () => {
  assert.equal(parseSpecFilename("README.md"), null);
  assert.equal(parseSpecFilename("data.ts"), null);
});

test("findSimilar 는 오타에 대해 원본을 후보로 낸다", () => {
  const candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"];
  const result = findSimilar("geometry-winding-ownershp", candidates);
  assert.deepEqual(result, ["geometry-winding-ownership"]);
});

test("findSimilar 는 부분 문자열 포함도 잡는다", () => {
  const candidates = ["geometry-winding-ownership"];
  assert.deepEqual(findSimilar("geometry-winding", candidates), ["geometry-winding-ownership"]);
});

test("findSimilar 는 전혀 무관한 문자열에 대해 빈 배열을 낸다", () => {
  const candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"];
  assert.deepEqual(findSimilar("totally-unrelated-topic", candidates), []);
});
