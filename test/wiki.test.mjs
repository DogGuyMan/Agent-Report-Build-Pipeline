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

// ── compdb 합치기 (2026-08-29)
import { mergeEntries, relativeFiles, clangUmlConfig, EXTERNAL_MARKERS } from "../scripts/wiki/compdb.mjs";

test("mergeEntries 는 파일 경로로 중복을 지운다 — 트리 둘이 같은 TU 를 가질 수 있다", () => {
  const e = (f) => ({ file: `/r/${f}`, directory: "/r/b" });
  const out = mergeEntries([[e("a.cpp"), e("b.cpp")], [e("b.cpp"), e("c.cpp")]], "/r");
  assert.deepEqual(out.map((x) => x.file), ["/r/a.cpp", "/r/b.cpp", "/r/c.cpp"]);
});

test("mergeEntries 는 저장소 밖 파일을 뺀다", () => {
  const out = mergeEntries([[{ file: "/other/x.cpp" }, { file: "/r/y.cpp" }]], "/r");
  assert.deepEqual(out.map((x) => x.file), ["/r/y.cpp"]);
});

test("mergeEntries 는 외부 라이브러리와 빌드 산출물을 뺀다", () => {
  const files = ["/r/src/a.cpp", "/r/vcpkg_installed/x.cpp", "/r/b/vedit_autogen/moc_x.cpp",
                 "/r/build/CMakeFiles/y.cpp"];
  const out = mergeEntries([files.map((f) => ({ file: f }))], "/r");
  assert.deepEqual(out.map((x) => x.file), ["/r/src/a.cpp"]);
});

test("EXTERNAL_MARKERS 는 Qt autogen 과 vcpkg 를 덮는다", () => {
  for (const m of ["autogen", "/vcpkg_installed/", "moc_"]) assert.ok(EXTERNAL_MARKERS.includes(m));
});

test("relativeFiles 는 저장소 상대경로를 정렬해 낸다 — 결정론", () => {
  const out = relativeFiles([{ file: "/r/b.cpp" }, { file: "/r/a.cpp" }, { file: "/r/b.cpp" }], "/r");
  assert.deepEqual(out, ["a.cpp", "b.cpp"]);
});

test("clangUmlConfig 는 글로브를 쓰지 않고 파일을 열거한다 — 깊이 4 정규식 함정", () => {
  const cfg = clangUmlConfig({
    compdbDir: "/r/out/compdb", repo: "/r", outDir: "/r/out",
    files: ["app/src/view/mainwindow.cpp", "core/panorama/warp.cpp"],
    flags: ["-resource-dir=/x"], paths: ["app", "core"],
  });
  assert.doesNotMatch(cfg, /\*/);
  assert.match(cfg, /- app\/src\/view\/mainwindow\.cpp/);
  assert.match(cfg, /- core\/panorama\/warp\.cpp/);
  assert.match(cfg, /- -resource-dir=\/x/);
  assert.match(cfg, /paths: \[app, core\]/);
});

// ── clang-doc 배선 (2026-08-29)
//
// **왜 필요한가.** clang-uml 은 클래스만 보고 자유 함수를 0개 낸다. clang-doc 이 그 층을
// 채우지만 **PATH 에 없다** — LLVM 번들이라 Homebrew 의 keg 안에 숨어 있다.
// 경로를 코드에 박으면 그 기계에서만 돈다. 못 찾았을 때 **막히지 않고 건너뛰는 것**도
// 규칙이다 — clang-doc 이 없는 기계에서도 clang-uml 만으로 옛 수준의 결과는 나와야 한다.
import { clangDocCandidates } from "../scripts/wiki/clang-doc.mjs";

test("clangDocCandidates 는 환경변수를 맨 앞에 둔다 — 사용자가 고른 것이 이긴다", () => {
  const c = clangDocCandidates({ CLANG_DOC: "/내가/고른/clang-doc", PATH: "" }, []);
  assert.equal(c[0], "/내가/고른/clang-doc");
});

test("clangDocCandidates 는 brew 접두사 다음에 PATH 를 훑는다", () => {
  const c = clangDocCandidates({ PATH: "/usr/bin:/bin" }, ["/opt/llvm"]);
  assert.deepEqual(c, ["/opt/llvm/bin/clang-doc", "/usr/bin/clang-doc", "/bin/clang-doc"]);
});

test("clangDocCandidates 는 경로를 박지 않는다 — 접두사가 없으면 PATH 만 본다", () => {
  const c = clangDocCandidates({ PATH: "/usr/bin" }, []);
  assert.deepEqual(c, ["/usr/bin/clang-doc"]);
  assert.ok(!c.some((p) => p.includes("homebrew")));
});

test("prepPlan 은 clang-doc 이 있으면 clang-uml 바로 다음에 돈다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: true,
                       hasRoslynDump: false, hasClangDoc: true });
  assert.deepEqual(p.steps, ["clang-uml", "clang-doc", "normalize", "facts", "render-modules"]);
});

test("prepPlan 은 clang-doc 이 없으면 그 단계만 빼고 계속 간다 — 막히지 않는다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: true,
                       hasRoslynDump: false, hasClangDoc: false });
  assert.deepEqual(p.steps, ["clang-uml", "normalize", "facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C# 경로에 clang-doc 을 끼우지 않는다", () => {
  const p = prepPlan({ collector: "roslyn-dump", hasCodegraph: false, hasClangUmlConfig: false,
                       hasRoslynDump: true, hasClangDoc: true });
  assert.ok(!p.steps.includes("clang-doc"));
});
