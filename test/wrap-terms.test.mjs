import { test } from "node:test";
import assert from "node:assert/strict";
import { wrapTerms, termPattern } from "../viz/wrap-terms.mjs";

// 빌드가 TermRef 를 렌더해 넘기는 꼴을 흉내 낸 마크업. 글자(id)를 담은 term-ref 여야 한다.
const ref = (id) => `<span class="term-ref" tabindex="0">${id}<span class="term-card">뜻</span></span>`;
const refs = (...ids) => new Map(ids.map((id) => [id, ref(id)]));

test("wrapTerms 는 글자에 나오는 용어를 전부 감싼다", () => {
  const out = wrapTerms("<p>M1 은 M1 이다. calls[] 도.</p>", refs("M1", "calls[]"));
  assert.equal((out.match(/class="term-ref"/g) ?? []).length, 3);
  assert.ok(out.includes(ref("calls[]")));
});

test("wrapTerms 는 이미 term-ref 안이거나 카드 안이면 건드리지 않는다", () => {
  const html = `<p>${ref("M1")} 과 <span class="term-card">M1</span></p>`;
  assert.equal(wrapTerms(html, refs("M1")), html);
});

test("wrapTerms 는 mono · code · pre · 제목 · th · summary · svg · script 안을 건드리지 않는다", () => {
  const html = [
    '<span class="mono">M1</span>', "<code>M1</code>", "<pre>M1</pre>",
    "<h2>M1</h2>", "<th>M1</th>", "<summary>M1</summary>",
    '<svg><text>M1</text></svg>', "<script>var M1=1</script>",
  ].join("");
  assert.equal(wrapTerms(html, refs("M1")), html);
});

test("wrapTerms 는 용어집 · 관계도 · 다이어그램 블록 안을 건드리지 않는다", () => {
  const html = '<div class="card term-groups"><td class="mono">M1</td><td>M1 뜻</td></div><div class="term-graph" data-terms="[M1]"></div><div class="svg-wrap">M1</div>';
  assert.equal(wrapTerms(html, refs("M1")), html);
});

test("wrapTerms 는 긴 id 를 먼저 맞춘다", () => {
  const out = wrapTerms("<p>git blob SHA 와 git</p>", refs("git", "git blob SHA"));
  assert.ok(out.includes(ref("git blob SHA")), "긴 것이 통째로");
  assert.equal((out.match(/class="term-ref"/g) ?? []).length, 2);
});

// 주의 — ref() 가 내는 여는 태그는 `class="term-ref" tabindex="0">` 다.
// `class="term-ref">` 로 세면 어떤 경우에도 0이 나와 시험이 헛돈다.
const opens = (out, id) => (out.match(new RegExp(`class="term-ref" tabindex="0">${id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}<`, "g")) ?? []).length;

test("wrapTerms 는 ASCII 앞뒤에 낱말 경계를 요구하고 한글 조사에는 요구하지 않는다", () => {
  const out = wrapTerms("<p>M10 M1x edges[]x 모듈을 모듈</p>", refs("M1", "edges[]", "모듈"));
  assert.equal(opens(out, "M1"), 0, "M10 · M1x 는 M1 이 아니다");
  assert.equal(opens(out, "edges[]"), 0, "edges[]x 는 다르다");
  assert.equal(opens(out, "모듈"), 2, "모듈을 도 감싼다");
});

test("wrapTerms 는 속성값을 건드리지 않고, 두 번 돌려도 같다", () => {
  const html = '<a title="M1" data-x="M1">M1</a>';
  const once = wrapTerms(html, refs("M1"));
  assert.ok(once.startsWith('<a title="M1" data-x="M1">'), "속성 그대로");
  assert.equal(wrapTerms(once, refs("M1")), once, "멱등");
});

test("termPattern 은 id 가 없으면 null", () => {
  assert.equal(termPattern([]), null);
});
