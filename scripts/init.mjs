// scripts/init.mjs
// report init <slug> — 없으면 빈 스켈레톤 생성, 있으면 건드리지 않고 경고만.
import { existsSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const slug = process.argv[2];

if (!slug) {
  console.error("사용법 — report init <slug>");
  process.exit(1);
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

const version = currentBuilderVersion();
const dir = join(process.cwd(), "specs", slug);
const dataFile = join(dir, "data.ts");

if (existsSync(dataFile)) {
  const existing = readFileSync(dataFile, "utf8");
  const m = existing.match(/builderVersion:\s*"([^"]+)"/);
  console.log(`${slug} — 기존 작업 파일이 있다. 이어서 쓴다(rev.2 방식).`);
  if (m && m[1] !== version) {
    console.warn(`경고 — builderVersion "${m[1]}" 이 현재 "${version}" 과 다르다.`);
    console.warn(`  옛 버전으로 빌드하려면: git worktree add /tmp/rb-${m[1]} ${m[1]}`);
  }
  process.exit(0);
}

mkdirSync(dir, { recursive: true });

writeFileSync(dataFile, `import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: "${version}",
  slug: "${slug}",
  specName: "",
  date: "",
  branch: "",
  decisions: [],
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

writeFileSync(join(dir, "tsconfig.json"), JSON.stringify({
  extends: join(ROOT, "tsconfig.json"),
  compilerOptions: {
    // 기본 typeRoots 는 이 tsconfig 파일 위치(다른 저장소) 기준으로 잡혀
    // report-builder 의 node_modules/@types 를 못 찾는다. 명시적으로 지정한다.
    typeRoots: [join(ROOT, "node_modules/@types")],
    paths: {
      "report-builder": [join(ROOT, "src/index.ts")],
      "report-builder/types": [join(ROOT, "src/types.ts")],
      "report-builder/svg": [join(ROOT, "scripts/svg.mjs")],
    },
  },
  include: ["*.ts", "*.tsx"],
}, null, 2) + "\n");

console.log(`${slug} — 스켈레톤 생성: ${dir}`);
