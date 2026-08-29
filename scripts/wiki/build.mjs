// scripts/wiki/build.mjs
// report-wiki build <저장소> — 산문 후처리.
//   1) demermaid.py 가 Mermaid 를 사전 렌더 SVG 로 바꾼다 (결정 C-18)
//   2) 그 결과 폴더에 VitePress 설정을 만들고 정적 사이트를 낸다
// Mermaid 를 런타임에 그리지 않으므로 vitepress-plugin-mermaid 는 쓰지 않는다.
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths } from "./paths.mjs";
import { pythonPath } from "../python.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));

/** 마크다운 파일 목록 -> VitePress 사이드바 항목. index 는 뺀다(홈이 따로 링크한다). */
export function sidebarFrom(files) {
  return files
    .filter((f) => f.endsWith(".md") && f !== "index.md")
    .map((f) => f.replace(/\.md$/, ""))
    .sort()
    .map((name) => ({ text: name, link: `/${name}` }));
}

/**
 * VitePress 설정 파일 본문. 제목은 JSON.stringify 로 이스케이프한다.
 *
 * **`defineConfig` 를 import 하지 않는다.** 이 파일은 **대상 저장소** 안에 쓰이는데
 * 그 저장소에는 node_modules 가 없다. Node 는 import 를 파일 위치 기준으로 풀기 때문에
 * `Cannot find package 'vitepress'` 로 즉사한다(🔵 2026-08-29 QtVisionEdit 에서 겪었다).
 * `defineConfig` 는 타입만 붙여 주는 항등 함수라 평범한 객체를 내보내면 동작이 같다.
 */
export function vitepressConfig(repoName, sidebar, outDir) {
  const items = sidebar.map((s) => `      { text: ${JSON.stringify(s.text)}, link: ${JSON.stringify(s.link)} }`);
  return `// report-wiki build 가 생성한다. 손으로 고치지 말 것 — 다음 빌드에서 덮어쓴다.
// defineConfig 를 쓰지 않는 이유는 scripts/wiki/build.mjs 의 주석을 보라.
export default ({
  title: ${JSON.stringify(`${repoName} 코드베이스 위키`)},
  description: "codegraph 정적 계층 + deep-wiki 산문",
  srcDir: ".",
  outDir: ${JSON.stringify(outDir)},
  themeConfig: {
    sidebar: [
${items.join(",\n")}
    ],
  },
});
`;
}

function run(cmd, args, cwd) {
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd });
  if (r.status !== 0) {
    console.error(`실패 — ${cmd} ${args.join(" ")}`);
    process.exit(r.status ?? 1);
  }
}

if (process.argv[1] && process.argv[1].endsWith("build.mjs")) {
  const repoArg = process.argv[2];
  if (!repoArg) {
    console.error("사용법 — report-wiki build <저장소 경로>");
    process.exit(1);
  }
  const repo = resolve(repoArg.replace(/^~/, process.env.HOME ?? "~"));
  const P = wikiPaths(repo);

  if (!existsSync(P.wiki)) {
    console.error(`에러 — 산문이 없다: ${P.wiki}`);
    console.error("  deep-wiki 스킬이 먼저 여기에 마크다운을 써야 한다.");
    process.exit(1);
  }

  // 1) Mermaid -> 사전 렌더 SVG
  mkdirSync(P.built, { recursive: true });
  const svgDir = existsSync(join(P.raw, "diagrams")) ? ["--svg-dir", join(P.raw, "diagrams")] : [];
  run(pythonPath(ROOT), [join(ROOT, "codegraph", "demermaid.py"), P.wiki, "--out", P.built, ...svgDir]);

  // 2) 이 저장소 안으로 옮겨 놓고 짓는다.
  //
  // **왜 대상 저장소에서 바로 짓지 않나.** 대상 저장소에는 node_modules 가 없다.
  // Vite 도 Node 도 import 를 **파일 위치 기준**으로 풀기 때문에 거기서 지으면
  // `Cannot find package 'vitepress'` 와 `vue/server-renderer` 를 못 찾는다
  // (🔵 2026-08-29 QtVisionEdit 에서 둘 다 겪었다). scripts/build.mjs 가
  // .tmp-report.mjs 를 cwd 가 아니라 ROOT 에 두는 것과 같은 이유다.
  const stage = join(ROOT, ".tmp", "wiki", basename(repo));
  rmSync(stage, { recursive: true, force: true });
  mkdirSync(stage, { recursive: true });
  cpSync(P.built, stage, { recursive: true });

  const sidebar = sidebarFrom(readdirSync(stage));
  mkdirSync(join(stage, ".vitepress"), { recursive: true });
  writeFileSync(join(stage, ".vitepress", "config.mts"),
    vitepressConfig(basename(repo), sidebar, P.site), "utf8");

  // 3) 정적 사이트 빌드 — 산출물만 대상 저장소로 되돌아간다(outDir 이 절대경로다)
  run(join(ROOT, "node_modules", ".bin", "vitepress"), ["build", stage], ROOT);

  console.log(`\n사이트 ${P.site}`);
  console.log(`  페이지 ${sidebar.length}개 · 열기: open ${join(P.site, "index.html")}`);
}
