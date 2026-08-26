// scripts/check.mjs
// 산출물 검사 규칙. 전부 기계 판정이며 사람 판단이 필요 없다.
import { readFileSync, existsSync } from "node:fs";
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

  // 보고서 디렉토리의 tsconfig 를 쓴다. ROOT 를 검사하면 report.tsx 가 빠진다.
  const tsc = spawnSync("npx", ["tsc", "--noEmit", "-p", cwd], { cwd: ROOT, stdio: "pipe" });
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
