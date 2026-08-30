import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir, homedir } from "node:os";
import { pathToFileURL } from "node:url";
import { linkPaths, makeResolver, pathPattern, expandRoot } from "../viz/link-paths.mjs";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "rb-links-"));
  mkdirSync(join(root, "docs/handoffs"), { recursive: true });
  mkdirSync(join(root, "specs/slug"), { recursive: true });
  mkdirSync(join(root, "ext/facts"), { recursive: true });
  writeFileSync(join(root, "docs/handoffs/HANDOFF-x.md"), "x");
  writeFileSync(join(root, "specs/2026-01-01-slug-design.md"), "spec");
  writeFileSync(join(root, "ext/facts/modules.md"), "m");
  writeFileSync(join(root, "ext/codegraph.json"), "{}");
  const cwd = join(root, "specs/slug");
  const index = new Map([
    ["HANDOFF-x.md", ["docs/handoffs/HANDOFF-x.md"]],
    ["dup.md", ["a/dup.md", "b/dup.md"]],
  ]);
  const resolve = makeResolver({ bases: [cwd, join(root, "specs"), root, join(root, "ext")], repoRoot: root, index });
  return { root, cwd, resolve };
}
const href = (p) => pathToFileURL(p).href;

test("linkPaths 는 있는 파일을 file:// 로 잇고 줄 번호는 글자로 남긴다", () => {
  const { root, resolve } = fixture();
  const out = linkPaths('<span class="mono">docs/handoffs/HANDOFF-x.md:900</span>', resolve);
  assert.equal(
    out,
    `<span class="mono"><a class="path-link" target="_blank" rel="noopener" href="${href(join(root, "docs/handoffs/HANDOFF-x.md"))}">docs/handoffs/HANDOFF-x.md:900</a></span>`,
  );
});

test("linkPaths 는 보고서 폴더의 부모(specs/)에서 설계 문서를 찾는다", () => {
  const { root, resolve } = fixture();
  const out = linkPaths("<p>근거 2026-01-01-slug-design.md:311-312 참조</p>", resolve);
  assert.ok(out.includes(`href="${href(join(root, "specs/2026-01-01-slug-design.md"))}">2026-01-01-slug-design.md:311-312</a>`));
});

test("linkPaths 는 이름만 있는 파일을 색인에서 유일할 때만 잇는다", () => {
  const { root, resolve } = fixture();
  const out = linkPaths("<p>HANDOFF-x.md 와 dup.md</p>", resolve);
  assert.ok(out.includes(`href="${href(join(root, "docs/handoffs/HANDOFF-x.md"))}">HANDOFF-x.md</a>`), "유일하면 링크");
  assert.ok(!out.includes(">dup.md</a>"), "둘 이상이면 링크하지 않는다");
});

test("linkPaths 는 글로브를 폴더로 잇고, 없는 파일은 건드리지 않는다", () => {
  const { root, resolve } = fixture();
  const out = linkPaths("<p>facts/*.md 와 facts/calls.md 와 codegraph.json</p>", resolve);
  const factsDir = href(join(root, "ext/facts"));
  assert.ok(
    out.includes(`href="${factsDir}/">facts/*.md</a>`) || out.includes(`href="${factsDir}">facts/*.md</a>`),
    "폴더 링크",
  );
  assert.ok(!/<a[^>]*>facts\/calls\.md<\/a>/.test(out), "없는 파일은 글자 그대로");
  assert.ok(out.includes(`">codegraph.json</a>`), "linkRoots(ext) 에서 찾는다");
});

test("linkPaths 는 term-ref · a · 제목 · th · summary · script · svg · 용어집 · 관계도 안을 건드리지 않는다", () => {
  const { resolve } = fixture();
  const html = [
    '<span class="term-ref" tabindex="0">HANDOFF-x.md<span class="term-card">HANDOFF-x.md</span></span>',
    '<a href="#">HANDOFF-x.md</a>',
    "<h2>HANDOFF-x.md</h2>",
    "<th>HANDOFF-x.md</th>",
    "<summary>HANDOFF-x.md</summary>",
    "<script>HANDOFF-x.md</script>",
    "<svg><text>HANDOFF-x.md</text></svg>",
    '<div class="card term-groups"><td class="mono">HANDOFF-x.md</td></div>',
    '<div class="term-graph" data-terms="HANDOFF-x.md"></div>',
  ].join("");
  assert.equal(linkPaths(html, resolve), html);
});

test("linkPaths 는 두 번 돌려도 같다", () => {
  const { resolve } = fixture();
  const once = linkPaths('<span class="mono">docs/handoffs/HANDOFF-x.md</span>', resolve);
  assert.equal(linkPaths(once, resolve), once);
});

test("pathPattern 은 경로 꼴만 잡는다", () => {
  const re = pathPattern();
  const hits = (s) => [...s.matchAll(re)].map((m) => m[0]);
  assert.deepEqual(hits("a/b.md:3 c.json facts/*.md x.py"), ["a/b.md:3", "c.json", "facts/*.md", "x.py"]);
  assert.deepEqual(hits("버전 1.2 와 C-19 와 calls[] 와 http://x.com/a.md"), [], "숫자 · 결정 코드 · 배열 필드 · URL 은 아니다");
});

test("makeResolver 는 bases 순서대로 먼저 찾은 것을 쓴다 — linkRoots 를 앞에 두면 외부 폴더가 이긴다", () => {
  const root = mkdtempSync(join(tmpdir(), "rb-order-"));
  mkdirSync(join(root, "a")); mkdirSync(join(root, "b"));
  writeFileSync(join(root, "a/x.json"), "a"); writeFileSync(join(root, "b/x.json"), "b");
  const r1 = makeResolver({ bases: [join(root, "a"), join(root, "b")], repoRoot: root, index: new Map() });
  const r2 = makeResolver({ bases: [join(root, "b"), join(root, "a")], repoRoot: root, index: new Map() });
  assert.equal(r1("x.json").href, pathToFileURL(join(root, "a/x.json")).href);
  assert.equal(r2("x.json").href, pathToFileURL(join(root, "b/x.json")).href);
});

test("expandRoot 는 $VAR 와 ${VAR} 를 편다", () => {
  process.env.RB_TEST_ROOT = "/tmp/rb-test";
  assert.equal(expandRoot("$RB_TEST_ROOT/out"), "/tmp/rb-test/out");
  assert.equal(expandRoot("${RB_TEST_ROOT}/out"), "/tmp/rb-test/out");
  delete process.env.RB_TEST_ROOT;
});

test("expandRoot 는 값이 없는 변수를 빈 문자열로 만든다 — 그러면 isDir 이 걸러 낸다", () => {
  delete process.env.RB_ABSENT_ROOT;
  assert.equal(expandRoot("$RB_ABSENT_ROOT/out"), "/out");
});

test("expandRoot 는 앞머리 ~ 를 홈으로 편다", () => {
  assert.equal(expandRoot("~/x"), join(homedir(), "/x"));
  assert.equal(expandRoot("/a/~/b"), "/a/~/b");
});
