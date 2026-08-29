import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { wikiPaths, collectorFor } from "../scripts/wiki/paths.mjs";
import { prepPlan } from "../scripts/wiki/prep.mjs";
import { sidebarFrom, vitepressConfig } from "../scripts/wiki/build.mjs";
import { checkArgs } from "../scripts/wiki/check.mjs";

// ── 경로 규약
test("wikiPaths 는 산문을 추적 경로에, 파생물을 out 아래에 둔다", () => {
  const p = wikiPaths("/tmp/repo");
  assert.equal(p.wiki, "/tmp/repo/docs/wiki");
  assert.equal(p.raw, "/tmp/repo/out/codegraph-raw");
  assert.equal(p.built, "/tmp/repo/out/codegraph-raw/wiki-built");
  assert.equal(p.site, "/tmp/repo/out/codegraph-raw/wiki-site");
  assert.equal(p.codegraph, "/tmp/repo/out/codegraph-raw/codegraph.json");
});

test("collectorFor 는 csproj 를 보면 roslyn-dump 를 고른다", () => {
  assert.equal(collectorFor(["Assembly-CSharp.csproj", "Assets"]), "roslyn-dump");
});

test("collectorFor 는 slnx 만 있어도 roslyn-dump 를 고른다", () => {
  assert.equal(collectorFor(["StickRushGame.slnx"]), "roslyn-dump");
});

test("collectorFor 는 CMakeLists.txt 를 보면 clang-uml 을 고른다", () => {
  assert.equal(collectorFor(["CMakeLists.txt", "core", "server"]), "clang-uml");
});

test("collectorFor 는 C# 이 C++ 보다 앞선다 — Unity 는 둘 다 가질 수 있다", () => {
  assert.equal(collectorFor(["CMakeLists.txt", "Assembly-CSharp.csproj"]), "roslyn-dump");
});

test("collectorFor 는 아무것도 못 찾으면 none 을 낸다", () => {
  assert.equal(collectorFor(["package.json", "src"]), "none");
});

// ── 준비 단계 계획
test("prepPlan 은 codegraph.json 이 있으면 수집기를 건너뛴다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: true, hasClangUmlConfig: true, hasRoslynDump: false });
  assert.deepEqual(p.steps, ["facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C++ 이고 설정이 있으면 clang-uml 부터 돈다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: true, hasRoslynDump: false });
  assert.deepEqual(p.steps, ["clang-uml", "normalize", "facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C++ 인데 .clang-uml 이 없으면 막힌다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /\.clang-uml/);
});

test("prepPlan 은 C# 이고 roslyn-dump.json 이 있으면 normalize 부터 돈다", () => {
  const p = prepPlan({ collector: "roslyn-dump", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: true });
  assert.deepEqual(p.steps, ["normalize", "facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C# 인데 roslyn-dump.json 이 없으면 막힌다 — dotnet 은 우리가 못 돌린다", () => {
  const p = prepPlan({ collector: "roslyn-dump", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /roslyn-dump\.json/);
});

test("prepPlan 은 수집기를 못 고르면 막힌다", () => {
  const p = prepPlan({ collector: "none", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /수집기/);
});

// ── 진입점 배선
test("report-wiki 는 세 명령을 디스패치 표에 갖는다", () => {
  const src = readFileSync(new URL("../bin/report-wiki", import.meta.url), "utf8");
  assert.match(src, /prep: "scripts\/wiki\/prep\.mjs"/);
  assert.match(src, /build: "scripts\/wiki\/build\.mjs"/);
  assert.match(src, /check: "scripts\/wiki\/check\.mjs"/);
  assert.match(src, /runDispatch/);
  assert.doesNotMatch(src, /아직 이 진입점은 비어 있다/);
});

// ── 빌드
test("sidebarFrom 은 마크다운 파일을 링크 항목으로 바꾼다", () => {
  assert.deepEqual(sidebarFrom(["managers.md", "data.md", "index.md"]), [
    { text: "data", link: "/data" },
    { text: "managers", link: "/managers" },
  ]);
});

test("sidebarFrom 은 index 를 사이드바에서 뺀다", () => {
  assert.deepEqual(sidebarFrom(["index.md"]), []);
});

test("sidebarFrom 은 마크다운이 아닌 것을 뺀다", () => {
  assert.deepEqual(sidebarFrom(["a.md", "assets", "b.svg"]), [{ text: "a", link: "/a" }]);
});

test("vitepressConfig 는 제목과 사이드바를 담고 srcDir 를 현재 폴더로 둔다", () => {
  const cfg = vitepressConfig("StickRushGame", [{ text: "data", link: "/data" }], "../wiki-site");
  assert.match(cfg, /title: "StickRushGame 코드베이스 위키"/);
  assert.match(cfg, /outDir: "\.\.\/wiki-site"/);
  assert.match(cfg, /\{ text: "data", link: "\/data" \}/);
  // 대상 저장소에는 node_modules 가 없다 — vitepress 를 import 하면 안 된다.
  assert.doesNotMatch(cfg, /from "vitepress"/);
  assert.match(cfg, /export default \(\{/);
});

test("vitepressConfig 는 제목의 따옴표를 이스케이프한다", () => {
  assert.match(vitepressConfig('Qt"Vision', [], "../wiki-site"), /title: "Qt\\"Vision 코드베이스 위키"/);
});

// ── 검사
test("checkArgs 는 산문 전량을 인자로 싣는다", () => {
  assert.deepEqual(checkArgs({
    repo: "/tmp/r", codegraph: "/tmp/r/cg.json", detail: null,
    docs: ["/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md"],
  }), ["--repo", "/tmp/r", "--codegraph", "/tmp/r/cg.json",
       "/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md"]);
});

test("checkArgs 는 살 파일이 있으면 --detail 을 끼운다", () => {
  assert.deepEqual(checkArgs({
    repo: "/tmp/r", codegraph: "/tmp/r/cg.json", detail: "/tmp/r/rd.json",
    docs: ["/tmp/r/docs/wiki/a.md"],
  }), ["--repo", "/tmp/r", "--codegraph", "/tmp/r/cg.json",
       "--detail", "/tmp/r/rd.json", "/tmp/r/docs/wiki/a.md"]);
});
