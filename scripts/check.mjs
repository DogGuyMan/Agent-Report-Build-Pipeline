// scripts/check.mjs
// 산출물 검사 규칙. 전부 기계 판정이며 사람 판단이 필요 없다.
import { readFileSync, existsSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

/** <script> 는 pan/zoom 하나까지만 허용된다(산출물 불변식). */
export function countScripts(html) {
  const count = (html.match(/<script/g) || []).length;
  return { ok: count <= 1, count };
}

/**
 * data.ts 의 결정 id 와 report.tsx 의 절이 1:1 인지 본다.
 * 지금은 표와 절이 어긋나도 아무도 모른다 — 이 검사가 그것을 잡는다.
 */
export function linkIntegrity(decisionIds, reportSource) {
  const sectionIds = [...reportSource.matchAll(/<Section\s+title="(D\d+)\b/g)].map((m) => m[1]);
  const missingSections = decisionIds.filter((id) => !sectionIds.includes(id));
  const orphanSections = sectionIds.filter((id) => !decisionIds.includes(id));
  return { ok: missingSections.length === 0 && orphanSections.length === 0, missingSections, orphanSections };
}

/** builderVersion 불일치는 경고이지 실패가 아니다. */
export function versionMatch(dataVersion, currentVersion) {
  return { ok: true, warn: dataVersion !== currentVersion };
}

function currentBuilderVersion() {
  try {
    return execFileSync("git", ["describe", "--tags", "--abbrev=0"], {
      cwd: ROOT, stdio: ["ignore", "pipe", "ignore"],
    }).toString().trim();
  } catch {
    return "untagged";
  }
}

// 직접 실행됐을 때만 검사를 수행한다. import 시에는 순수 함수만 노출한다.
if (process.argv[1] && process.argv[1].endsWith("check.mjs")) {
  const cwd = process.cwd();
  let failed = false;

  const outFile = join(cwd, "out/report.html");
  if (!existsSync(outFile)) {
    console.error("실패 — out/report.html 이 없다. 먼저 report build 를 실행한다.");
    process.exit(1);
  }
  const html = readFileSync(outFile, "utf8");

  const s = countScripts(html);
  console.log(`${s.ok ? "통과" : "실패"} — <script> ${s.count}개 (허용 1)`);
  if (!s.ok) failed = true;

  // 타입 검사용 tsconfig 는 검사 시점에 ROOT 에 임시로 만들고 지운다.
  // 보고서마다 내용이 동일한 보일러플레이트라 대상 저장소에 남길 이유가 없다
  // (build.mjs 가 .tmp-report.mjs 를 ROOT 에 두는 것과 같은 이유).
  //
  // paths 는 타입 해결 전용이라 선언 파일을 가리킨다. .mjs 를 직접 가리키면
  // TS 가 형제 .d.mts 를 찾지 않아 TS7016 이 난다 — 런타임 해결은 build.mjs 의 alias 가 따로 한다.
  // typeRoots 를 명시하는 이유: 기본값은 tsconfig 파일 위치 기준이라 @types/node 를 놓치고 TS2688 이 난다.
  //
  // include 글로브 대신 files 에 절대경로를 열거한다. 글로브는 tsconfig 위치 기준으로
  // 해석되는데 이 파일은 ROOT 에 있고 검사 대상은 cwd 라 서로 다르다.
  const tsconfigPath = join(ROOT, ".tmp-report-tsconfig.json");
  writeFileSync(tsconfigPath, JSON.stringify({
    extends: join(ROOT, "tsconfig.json"),
    compilerOptions: {
      typeRoots: [join(ROOT, "node_modules/@types")],
      paths: {
        "report-builder": [join(ROOT, "src/index.ts")],
        "report-builder/types": [join(ROOT, "src/types.ts")],
        "report-builder/svg": [join(ROOT, "scripts/svg.d.mts")],
      },
    },
    files: readdirSync(cwd).filter((f) => /\.tsx?$/.test(f)).map((f) => join(cwd, f)),
    include: [],
  }, null, 2) + "\n");

  let tsc;
  try {
    tsc = spawnSync("npx", ["tsc", "--noEmit", "-p", tsconfigPath], { cwd: ROOT, stdio: "pipe" });
  } finally {
    rmSync(tsconfigPath, { force: true });
  }
  console.log(`${tsc.status === 0 ? "통과" : "실패"} — tsc --noEmit`);
  if (tsc.status !== 0) {
    console.error(tsc.stdout.toString());
    failed = true;
  }

  const dataSrc = readFileSync(join(cwd, "data.ts"), "utf8");
  const reportSrc = readFileSync(join(cwd, "report.tsx"), "utf8");
  const ids = [...dataSrc.matchAll(/id:\s*"(D\d+)"/g)].map((m) => m[1]);
  const link = linkIntegrity(ids, reportSrc);
  console.log(`${link.ok ? "통과" : "실패"} — 링크 무결성 (결정 ${ids.length}건)`);
  if (!link.ok) {
    if (link.missingSections.length) console.error(`  절이 없는 결정: ${link.missingSections.join(", ")}`);
    if (link.orphanSections.length) console.error(`  결정이 없는 절: ${link.orphanSections.join(", ")}`);
    failed = true;
  }

  const dv = dataSrc.match(/builderVersion:\s*"([^"]+)"/)?.[1] ?? "?";
  const cv = currentBuilderVersion();
  const v = versionMatch(dv, cv);
  console.log(`${v.warn ? "경고" : "통과"} — builderVersion ${dv} vs ${cv}`);

  process.exit(failed ? 1 : 0);
}
