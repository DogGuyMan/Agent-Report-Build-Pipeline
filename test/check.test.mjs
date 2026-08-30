import { test } from "node:test";
import assert from "node:assert/strict";
import { countScripts, linkIntegrity, versionMatch } from "../viz/check.mjs";

test("countScripts 는 pan/zoom 하나까지 허용한다", () => {
  assert.equal(countScripts("<html></html>").ok, true);
  assert.equal(countScripts("<script>a</script>").ok, true);
  assert.equal(countScripts("<script>a</script><script>b</script>").ok, false);
});

test("countScripts 는 실제 개수를 함께 돌려준다", () => {
  assert.equal(countScripts("<script>a</script><script>b</script>").count, 2);
});

test("linkIntegrity 는 report.tsx 에 절이 없는 결정을 잡는다", () => {
  const r = linkIntegrity(["D0", "D1", "D2"], '<Section title="D0 — 가">\n<Section title="D1 — 나">');
  assert.equal(r.ok, false);
  assert.deepEqual(r.missingSections, ["D2"]);
});

test("linkIntegrity 는 data.ts 에 결정이 없는 절도 잡는다", () => {
  const r = linkIntegrity(["D0"], '<Section title="D0 — 가">\n<Section title="D9 — 유령">');
  assert.equal(r.ok, false);
  assert.deepEqual(r.orphanSections, ["D9"]);
});

test("linkIntegrity 는 양쪽이 맞으면 통과한다", () => {
  const r = linkIntegrity(["D0", "D1"], '<Section title="D0 — 가">\n<Section title="D1 — 나">');
  assert.equal(r.ok, true);
});

test("linkIntegrity 는 결정도 절도 없으면 통과한다", () => {
  assert.equal(linkIntegrity([], "").ok, true);
});

test("versionMatch 는 불일치를 경고로 분류한다 — 실패가 아니다", () => {
  const r = versionMatch("v1", "v2");
  assert.equal(r.ok, true, "버전 불일치는 빌드를 막지 않는다");
  assert.equal(r.warn, true);
});

test("versionMatch 는 일치하면 경고도 없다", () => {
  assert.deepEqual(versionMatch("v2", "v2"), { ok: true, warn: false });
});
