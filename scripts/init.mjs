// scripts/init.mjs
// report init [slug]
//  - 인자 없으면: specs/*-design.md 중 아직 보고서가 없는 것을 날짜 내림차순으로 나열.
//  - 인자 있으면: 대응하는 specs/YYYY-MM-DD-<slug>-design.md 가 있어야 스켈레톤을 만든다.
//    없으면 거부(exit 1) — 오타를 조용히 통과시키지 않는다.
//  - data.ts 가 이미 있으면(멱등) 스펙 문서 존재 여부와 무관하게 이어서 쓴다.
//  - tsconfig.json 은 만들지 않는다. 보고서마다 내용이 동일한 보일러플레이트라
//    대상 저장소에 남길 이유가 없다. check.mjs 가 검사 시점에 ROOT 에 임시 생성한다.
import { existsSync, mkdirSync, writeFileSync, readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

const SPEC_FILENAME_RE = /^(\d{4}-\d{2}-\d{2})-(.+)-design\.md$/;

/**
 * spec 파일명에서 날짜와 slug 를 뽑는다.
 * 규칙: YYYY-MM-DD-<slug>-design.md
 * 안 맞으면 null.
 */
export function parseSpecFilename(basename) {
  const m = basename.match(SPEC_FILENAME_RE);
  if (!m) return null;
  return { date: m[1], slug: m[2] };
}

/**
 * slug 오타에 대한 비슷한 후보를 단순 규칙으로 찾는다.
 * 규칙: 부분 문자열 포함(양방향) 또는 앞 4글자 공유.
 * 편집 거리 등 정교한 알고리즘은 쓰지 않는다.
 */
export function findSimilar(slug, candidates) {
  return candidates.filter((c) => {
    if (c === slug) return false;
    if (c.includes(slug) || slug.includes(c)) return true;
    return slug.length >= 4 && c.length >= 4 && c.slice(0, 4) === slug.slice(0, 4);
  });
}

// 직접 실행됐을 때만 CLI 를 수행한다. import 시에는 순수 함수만 노출한다.
if (process.argv[1] && process.argv[1].endsWith("init.mjs")) {
  const slug = process.argv[2];
  const cwd = process.cwd();
  const specsDir = join(cwd, "specs");

  function currentBuilderVersion() {
    try {
      return execFileSync("git", ["describe", "--tags", "--abbrev=0"], {
        cwd: ROOT, stdio: ["ignore", "pipe", "ignore"],
      }).toString().trim();
    } catch {
      return "untagged";
    }
  }

  /** specs/ 아래 spec 문서 목록. { file, date, slug }[] */
  function listSpecs() {
    if (!existsSync(specsDir)) return [];
    return readdirSync(specsDir)
      .map((file) => {
        const parsed = parseSpecFilename(file);
        return parsed && { file, ...parsed };
      })
      .filter(Boolean);
  }

  function hasReport(slug) {
    return existsSync(join(specsDir, slug, "data.ts"));
  }

  function currentBranch() {
    try {
      return execFileSync("git", ["rev-parse", "--abbrev-ref", "HEAD"], {
        cwd, stdio: ["ignore", "pipe", "ignore"],
      }).toString().trim();
    } catch {
      return "";
    }
  }

  function writeSkeleton(dir, { slug, date, specName, branch, version }) {
    mkdirSync(dir, { recursive: true });

    writeFileSync(join(dir, "data.ts"), `import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: ${JSON.stringify(version)},
  slug: ${JSON.stringify(slug)},
  specName: ${JSON.stringify(specName)},
  date: ${JSON.stringify(date)},
  branch: ${JSON.stringify(branch)},
  decisions: [],
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮겨 적는다.
  //   report-term collect <plan.md> <terms-db.json>  →  (스킬이 묻는다)  →  report-term grade  →  report-term emit
  // terms.json 의 { "용어": { TermMeans, UserMentalValue } } 를
  // { id, label, short, kind, mental } 로 옮긴다. 자동 import 하지 않는다 — 이 파일은 사람이 읽는 파일이다.
  terms: [],
};
`);

    writeFileSync(join(dir, "report.tsx"), `import { Page, Section, DecisionTable, VerdictFooter } from "report-builder";
import { data } from "./data.js";

export { data };

export default function Report() {
  return (
    <Page data={data}>
      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>
      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
`);

  }

  if (!slug) {
    const specs = listSpecs();
    const missing = specs
      .filter((s) => !hasReport(s.slug))
      .sort((a, b) => b.date.localeCompare(a.date));

    if (missing.length === 0) {
      console.log("모든 spec 에 보고서가 있다.");
      process.exit(0);
    }

    const width = Math.max(...missing.map((s) => s.slug.length)) + 3;
    console.log("보고서가 없는 spec:");
    for (const s of missing) {
      console.log(`  ${s.slug.padEnd(width)}${s.date}`);
    }
    console.log("");
    console.log("사용법 — report init <slug>");
    process.exit(1);
  }

  const version = currentBuilderVersion();
  const dir = join(specsDir, slug);
  const dataFile = join(dir, "data.ts");

  if (existsSync(dataFile)) {
    // 멱등 경로 — spec 문서 존재 여부는 따지지 않는다. 이미 작업 중인
    // 보고서를 spec 이름이 바뀌었다는 이유로 막으면 안 된다.
    const existing = readFileSync(dataFile, "utf8");
    const m = existing.match(/builderVersion:\s*"([^"]+)"/);
    console.log(`${slug} — 기존 작업 파일이 있다. 이어서 쓴다(rev.2 방식).`);
    if (m && m[1] !== version) {
      console.warn(`경고 — builderVersion "${m[1]}" 이 현재 "${version}" 과 다르다.`);
      console.warn(`  옛 버전으로 빌드하려면: git worktree add /tmp/rb-${m[1]} ${m[1]}`);
    }
    process.exit(0);
  }

  const specs = listSpecs();
  const match = specs.find((s) => s.slug === slug);

  if (!match) {
    console.error("에러 — 대응하는 spec 문서를 찾지 못했다:");
    console.error(`  specs/*-${slug}-design.md`);

    const candidates = findSimilar(slug, specs.map((s) => s.slug));
    if (candidates.length > 0) {
      const width = Math.max(...candidates.map((c) => c.length)) + 3;
      console.error("");
      console.error("비슷한 slug:");
      for (const c of candidates) {
        const s = specs.find((s) => s.slug === c);
        console.error(`  ${c.padEnd(width)}${s.date}`);
      }
    }
    process.exit(1);
  }

  const specSource = readFileSync(join(specsDir, match.file), "utf8");
  const titleMatch = specSource.match(/^#\s+(.+)$/m);
  const specName = titleMatch ? titleMatch[1].trim() : "";
  const branch = currentBranch();

  writeSkeleton(dir, { slug, date: match.date, specName, branch, version });

  console.log(`${slug} — 스켈레톤 생성: ${dir}`);
  console.log(`  근거 spec: specs/${match.file}`);
}
