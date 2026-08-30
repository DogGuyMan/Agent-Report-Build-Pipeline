// <include file="machine/comments.xml" path="//term[@id='runner/wiki/compdb.mjs']"/>
// C++ 저장소의 컴파일 명령 목록을 전부 찾아 합치는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// C++ 저장소의 compile_commands.json 을 **전부 찾아 하나로 합친다.**
//
// **왜 필요한가.** CMake 프로젝트는 타깃 트리가 여럿일 수 있다. QtVisionEdit 이 그렇다 —
// 루트가 core·protocol·server·test 를 짓고, GUI(app)는 Qt Creator 가 별도 트리에서 짓는다
// (app/CMakeLists.txt:8 이 의도적으로 add_subdirectory 를 하지 않는다).
// 루트 것만 쓰면 🔵 2026-08-29 실측으로 **1차 클래스 61개 중 37개(app)가 통째로 빠졌다.**
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

// 남의 코드와 빌드가 만든 파일. 여기 있는 것은 1차 코드가 아니다.
export const EXTERNAL_MARKERS = [
  "/vcpkg_installed/", "/_deps/", "/node_modules/", "/Qt/", "/homebrew/",
  "autogen", "/CMakeFiles/", "moc_", "qrc_", "ui_",
];

// 도구가 자기용으로 만든 축약본. 원본과 겹쳐 세면 중복이다.
const SIDECAR_DIRS = [".qtc_clangd", ".cache"];

// <include file="machine/comments.xml" path="//term[@id='findCompdbs']"/>
// 저장소 안의 컴파일 명령 파일을 전부 찾는다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** 저장소 안의 compile_commands.json 을 전부 찾는다. 외부 라이브러리 트리는 안 본다. */
export function findCompdbs(repo, readDir = readdirSync, isDir = (p) => statSync(p).isDirectory()) {
  const out = [];
  const walk = (dir, depth) => {
    if (depth > 6) return;
    let entries;
    try { entries = readDir(dir); } catch { return; }
    for (const name of entries) {
      const p = join(dir, name);
      if (name === "compile_commands.json") { out.push(p); continue; }
      if (name.startsWith(".") && !SIDECAR_DIRS.includes(name)) continue;
      if (["vcpkg_installed", "node_modules", ".git", "out"].includes(name)) continue;
      let d = false;
      try { d = isDir(p); } catch { d = false; }
      if (d) walk(p, depth + 1);
    }
  };
  walk(repo, 0);
  // 축약본은 원본이 있으면 버린다 — 같은 TU 를 두 번 세지 않는다.
  const primary = out.filter((p) => !SIDECAR_DIRS.some((s) => p.includes(`/${s}/`)));
  return (primary.length ? primary : out).sort();
}

// <include file="machine/comments.xml" path="//term[@id='mergeEntries']"/>
// 여러 목록을 합치고 중복과 남의 코드를 걷어 낸다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * 여러 compdb 의 엔트리를 합친다. 파일 경로로 중복을 지우고 외부·생성물을 뺀다.
 * 순수 함수라 테스트가 쉽다.
 */
export function mergeEntries(lists, repo) {
  const seen = new Set();
  const out = [];
  for (const list of lists) {
    for (const e of list) {
      const f = e?.file;
      if (typeof f !== "string" || seen.has(f)) continue;
      if (!f.startsWith(repo)) continue;                      // 저장소 밖은 남의 코드다
      if (EXTERNAL_MARKERS.some((m) => f.includes(m))) continue;
      seen.add(f);
      out.push(e);
    }
  }
  return out;
}

// <include file="machine/comments.xml" path="//term[@id='relativeFiles']"/>
// 합친 목록에서 저장소 기준 상대 경로만 뽑아 정렬한다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** 합친 엔트리에서 저장소 상대 경로 목록을 만든다. 정렬해 결정론을 지킨다. */
export function relativeFiles(entries, repo) {
  return [...new Set(entries.map((e) => e.file.slice(repo.length + 1)))].sort();
}

// <include file="machine/comments.xml" path="//term[@id='clangUmlConfig']"/>
// 정적 수집기 설정 글자를 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * clang-uml 설정 본문. **글로브를 쓰지 않고 파일을 열거한다.**
 *
 * 🔵 2026-08-29 실측 — clang-uml 0.6.3 은 깊이 4 이상의 글로브(`app/src/view/*.cpp`)에서
 * "regular expression complexity exceeded" 로 죽는다. 같은 파일들을 하나씩 적으면 통과한다.
 * 어차피 합친 compdb 가 대상 목록을 이미 알고 있으므로 열거가 더 정확하기도 하다.
 *
 * flags 와 paths 는 저자가 쓴 `.clang-uml` 에서 가져온다 — 기계마다 다른 값이라 박지 않는다.
 */
export function clangUmlConfig({ compdbDir, repo, outDir, files, flags, paths }) {
  const lines = [
    "# report-wiki prep 이 생성한다. 손으로 고치지 말 것 — 다음 실행에서 덮어쓴다.",
    "# 대상 파일은 합친 compile_commands.json 에서 열거한다(글로브는 깊이 4에서 죽는다).",
    `compilation_database_dir: ${compdbDir}`,
    `relative_to: ${repo}`,
    `output_directory: ${outDir}`,
  ];
  if (flags?.length) {
    lines.push("add_compile_flags:");
    for (const f of flags) lines.push(`  - ${f}`);
  }
  lines.push("diagrams:", "  full_class:", "    type: class", "    glob:");
  for (const f of files) lines.push(`      - ${f}`);
  if (paths?.length) {
    lines.push("    include:", `      paths: [${paths.join(", ")}]`);
  }
  return lines.join("\n") + "\n";
}

// <include file="machine/comments.xml" path="//term[@id='readAuthorConfig']"/>
// 저자가 쓴 설정에서 컴파일 깃발과 포함 경로만 읽어 온다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** 저자의 `.clang-uml` 에서 컴파일 플래그와 include 경로만 읽어 온다. */
export function readAuthorConfig(path) {
  if (!existsSync(path)) return { flags: [], paths: [] };
  const text = readFileSync(path, "utf8");
  const flags = [];
  const m = text.match(/^add_compile_flags:\s*\n((?:\s+-\s.*\n)+)/m);
  if (m) for (const l of m[1].split("\n")) {
    const t = l.replace(/^\s*-\s*/, "").trim();
    if (t) flags.push(t);
  }
  const inline = text.match(/^add_compile_flags:\s*\[([^\]]*)\]/m);
  if (inline) for (const t of inline[1].split(",")) {
    const s = t.trim();
    if (s) flags.push(s);
  }
  const p = text.match(/paths:\s*\[([^\]]*)\]/);
  const paths = p ? p[1].split(",").map((s) => s.trim()).filter(Boolean) : [];
  return { flags, paths };
}
