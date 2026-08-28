// scripts/build.mjs
// <프로젝트>/specs/<slug>/{data.ts, report.tsx} → out/report.html
// esbuild 로 트랜스파일 → renderToStaticMarkup → 문자열 조립. 클라이언트 런타임 0.
import { build } from "esbuild";
import { readFileSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const cwd = process.cwd();

/** ~/report-builder 의 현재 git 태그. 없으면 "untagged". */
function currentBuilderVersion() {
  try {
    return execFileSync("git", ["describe", "--tags", "--abbrev=0"], {
      cwd: ROOT, stdio: ["ignore", "pipe", "ignore"],
    }).toString().trim();
  } catch {
    return "untagged";
  }
}

const entry = join(cwd, "report.tsx");
// tmp 산출물은 report-builder 자신의 node_modules(react, react-dom)를 동적 import 로
// resolve 할 수 있도록 cwd(보고서가 있는 다른 저장소)가 아니라 ROOT 안에 둔다.
// cwd 에 두면 그 저장소에 react 가 설치돼 있지 않아 ERR_MODULE_NOT_FOUND 가 난다.
const tmp = join(ROOT, ".tmp-report.mjs");

await build({
  entryPoints: [entry],
  bundle: true,
  format: "esm",
  platform: "node",
  target: "node22",
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime", "react-dom/server"],
  // 보고서는 다른 저장소에 있으므로 node_modules 로는 report-builder 를 찾지 못한다.
  alias: {
    "report-builder": join(ROOT, "src/index.ts"),
    "report-builder/types": join(ROOT, "src/types.ts"),
    "report-builder/svg": join(ROOT, "scripts/svg.mjs"),
  },
  outfile: tmp,
  absWorkingDir: cwd,
  logLevel: "warning",
});

let mod;
try {
  mod = await import(pathToFileURL(tmp).href);
} finally {
  rmSync(tmp, { force: true });
}

const { renderToStaticMarkup } = await import("react-dom/server");
const body = renderToStaticMarkup(mod.default());
const data = mod.data;

const version = currentBuilderVersion();
if (data.builderVersion !== version) {
  console.warn(`경고 — data.ts 의 builderVersion "${data.builderVersion}" 이 현재 "${version}" 과 다르다. 빌드는 계속한다.`);
}

const css = readFileSync(join(ROOT, "src/theme.css"), "utf8");

// 용어 그래프 런타임. **terms 가 있을 때만** 번들해 넣는다 — 안 쓰는 보고서가 62KB 를 물지 않게.
// 산출물 불변식상 <script> 는 1개까지이므로 이 번들 하나로 끝낸다.
let runtime = "";
if (Array.isArray(data.terms) && data.terms.length > 0) {
  const r = await build({
    entryPoints: [join(ROOT, "src/runtime/term-graph.ts")],
    bundle: true,
    minify: true,
    format: "iife",
    platform: "browser",
    target: "es2020",
    write: false,
    logLevel: "warning",
  });
  const code = r.outputFiles[0].text;
  // </script> 가 코드 안에 있으면 HTML 파서가 스크립트를 조기 종료한다.
  runtime = `<script>${code.replace(/<\/script/gi, "<\\/script")}</script>`;
  console.log(`용어 그래프 런타임 ${code.length} 자 삽입 (용어 ${data.terms.length}개)`);
}

const html = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${data.specName} — 설계 검토</title>
<style>
${css}
</style>
</head>
<body>
${body}
${runtime}
</body>
</html>
`;

mkdirSync(join(cwd, "out"), { recursive: true });
writeFileSync(join(cwd, "out/report.html"), html);

const scripts = (html.match(/<script/g) || []).length;
console.log(`out/report.html — ${html.length} 자, <script> ${scripts}개`);
if (scripts > 1) {
  console.error(`불변식 위반 — <script> 가 ${scripts}개다. 허용은 pan/zoom 하나까지.`);
  process.exit(1);
}
