// <include file="machine/comments.xml" path="//term[@id='check.mjs']"/>
// 구운 보고서가 규칙을 지켰는지 보는 검사 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/check.mjs
// 산출물 검사 규칙. 전부 기계 판정이며 사람 판단이 필요 없다.
import { readFileSync, existsSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

// <include file="machine/comments.xml" path="//term[@id='countScripts']"/>
// 산출물 HTML 의 <script> 개수를 센다. 1개까지만 허용된다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** <script> 는 pan/zoom 하나까지만 허용된다(산출물 불변식). */
export function countScripts(html) {
  const count = (html.match(/<script/g) || []).length;
  return { ok: count <= 1, count };
}

// <include file="machine/comments.xml" path="//term[@id='linkIntegrity']"/>
// 결정 표의 항목과 본문 절이 1:1 인지 본다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
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


// <include file="machine/comments.xml" path="//term[@id='undefinedTerms']"/>
// 본문에 쓰였는데 용어집에 정의가 없는 식별자를 찾는다.
// 쓰는 것: C-19, calls[] · 쓰이는 곳: 없음
/**
 * 본문에 쓰인 식별자 꼴 낱말 중 용어집에 정의가 없는 것을 찾는다.
 * **경고이지 실패가 아니다** — 탐지 규칙이 오탐을 낼 수 있어 빌드를 막지 않는다.
 *
 * 잡는 꼴은 셋뿐이다. 자연어 용어(WarmUp, PageRank 같은 것)는 기계가 가릴 수 없어 빼고,
 * 저자가 용어집에 직접 넣어야 한다.
 *   - 결정 코드      C-19 · D-1 · U5 · R-13 · M4
 *   - 산출물 파일명   codegraph.json · roslyn-dump.json
 *   - 배열 필드      calls[] · edges[]
 */
export function undefinedTerms(reportSource, termIds) {
  const known = new Set(termIds);
  const found = new Set();
  const patterns = [
    /\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b/g,
    /\b[a-z][a-z0-9_-]*\.json\b/g,
    /\b[a-z][A-Za-z0-9_]*\[\]/g,
  ];
  // JSX 속성값과 import 경로는 본문이 아니다. 거칠게 걷어낸다.
  const body = reportSource
    .replace(/^import[^\n]*$/gm, "")
    .replace(/className="[^"]*"/g, "")
    // 절 제목의 D0·D1 은 결정 번호이고 링크 무결성 검사가 따로 담당한다. 통째로 뺀다.
    .replace(/<Section\s+title="[^"]*"/g, "");
  for (const re of patterns) {
    for (const m of body.matchAll(re)) {
      if (!known.has(m[0])) found.add(m[0]);
    }
  }
  return { ok: found.size === 0, missing: [...found].sort() };
}

// <include file="machine/comments.xml" path="//term[@id='versionMatch']"/>
// data.ts 의 builderVersion 이 지금 버전과 같은지 본다. 달라도 경고까지다.
// 쓰는 것: builderVersion · 쓰이는 곳: 없음
/** builderVersion 불일치는 경고이지 실패가 아니다. */
export function versionMatch(dataVersion, currentVersion) {
  return { ok: true, warn: dataVersion !== currentVersion };
}

// <include file="machine/comments.xml" path="//term[@id='check.currentBuilderVersion']"/>
// 검사 시점의 report-builder git 태그를 읽는다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
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
        "report-builder": [join(ROOT, "viz/src/index.ts")],
        "report-builder/types": [join(ROOT, "viz/src/types.ts")],
        "report-builder/svg": [join(ROOT, "viz/svg.d.mts")],
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


  // 용어집 대조 — 경고만 낸다.
  // 용어는 { id: "C-19", ... } 처럼 줄 중간에 오므로 줄머리에 고정하지 않는다.
  // 결정 id(D0·D1…)는 링크 무결성 검사가 담당하므로 여기서 뺀다.
  const termIds = [...dataSrc.matchAll(/\bid:\s*"([^"]+)"/g)].map((m) => m[1]);
  const glossaryIds = termIds.filter((t) => !/^D\d+$/.test(t));
  const ut = undefinedTerms(reportSrc, glossaryIds);
  if (ut.ok) {
    console.log(`통과 — 용어집 대조 (정의 ${glossaryIds.length}개)`);
  } else {
    console.log(`경고 — 용어집에 없는 식별자 ${ut.missing.length}개`);
    console.log(`  ${ut.missing.join(", ")}`);
  }

  const dv = dataSrc.match(/builderVersion:\s*"([^"]+)"/)?.[1] ?? "?";
  const cv = currentBuilderVersion();
  const v = versionMatch(dv, cv);
  console.log(`${v.warn ? "경고" : "통과"} — builderVersion ${dv} vs ${cv}`);

  process.exit(failed ? 1 : 0);
}
