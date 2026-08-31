import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSpecFilename, findSimilar, DOC_DIRS } from "../viz/init.mjs";

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

// ── 원본 문서는 두 자리에 산다. 자리마다 파일명 관례가 다르다
test("DOC_DIRS 는 specs 와 plans 두 자리를 가진다", () => {
  assert.deepEqual(DOC_DIRS.map((d) => d.dir), ["specs", "plans"]);
});

test("plans 는 -design 접미사 없이 날짜와 slug 만으로 잡는다", () => {
  assert.deepEqual(
    parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "plans"),
    { date: "2026-08-30", slug: "symbol-resolution-survey" },
  );
});

test("plans 관례는 specs 에서 통하지 않는다 — 접미사 가드를 지킨다", () => {
  assert.equal(parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "specs"), null);
});

test("specs 관례는 plans 에서도 파일명이 맞으면 잡힌다", () => {
  // plans 의 정규식은 `.md` 앞을 전부 slug 로 본다. 관례 밖이지만 조용히 버리지는 않는다.
  assert.deepEqual(
    parseSpecFilename("2026-08-30-foo-design.md", "plans"),
    { date: "2026-08-30", slug: "foo-design" },
  );
});

test("parseSpecFilename 은 자리를 안 주면 specs 로 본다 — 옛 호출을 깨지 않는다", () => {
  assert.deepEqual(
    parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md"),
    { date: "2026-07-27", slug: "geometry-winding-ownership" },
  );
});

test("plans 도 날짜 형식이 아니면 null", () => {
  assert.equal(parseSpecFilename("README.md", "plans"), null);
  assert.equal(parseSpecFilename("not-a-date-topic.md", "plans"), null);
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
