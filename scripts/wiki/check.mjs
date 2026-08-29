// <include file="docs/codegraph/comments.xml" path="//term[@id='scripts/wiki/check.mjs']"/>
// scripts/wiki/check.mjs
// report-wiki check <저장소> — 위키 산문의 인용을 검증한다.
// verify_citations.py 의 3값 판정을 그대로 쓴다:
//   L1 파일이 있나 · L2 그 줄이 있나 · L3 그 줄 근처에 그 이름이 있나
// L3 실패는 "근거 없음" 경고이지 실패가 아니다 — 탐지 규칙이 오탐을 낼 수 있어서다.
import { existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths } from "./paths.mjs";
import { pythonPath } from "../python.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));

/** verify_citations.py 에 넘길 인자를 만든다. 순수 함수라 테스트가 쉽다. */
// <include file="docs/codegraph/comments.xml" path="//term[@id='checkArgs']"/>
export function checkArgs({ repo, codegraph, detail, docs }) {
  const out = ["--repo", repo, "--codegraph", codegraph];
  if (detail) out.push("--detail", detail);
  return out.concat(docs);
}

if (process.argv[1] && process.argv[1].endsWith("check.mjs")) {
  const repoArg = process.argv[2];
  if (!repoArg) {
    console.error("사용법 — report-wiki check <저장소 경로>");
    process.exit(1);
  }
  const repo = resolve(repoArg.replace(/^~/, process.env.HOME ?? "~"));
  const P = wikiPaths(repo);

  if (!existsSync(P.codegraph)) {
    console.error(`에러 — codegraph.json 이 없다: ${P.codegraph}. report-wiki prep 을 먼저 돌려라.`);
    process.exit(1);
  }
  if (!existsSync(P.wiki)) {
    console.error(`에러 — 산문이 없다: ${P.wiki}`);
    process.exit(1);
  }
  const docs = readdirSync(P.wiki).filter((f) => f.endsWith(".md")).map((f) => join(P.wiki, f));
  if (docs.length === 0) {
    console.error(`에러 — ${P.wiki} 에 마크다운이 없다`);
    process.exit(1);
  }

  const detailPath = join(P.raw, "roslyn-dump.json");
  const args = checkArgs({
    repo,
    codegraph: P.codegraph,
    detail: existsSync(detailPath) ? detailPath : null,
    docs,
  });
  const r = spawnSync(pythonPath(ROOT), [join(ROOT, "codegraph", "verify_citations.py"), ...args], { stdio: "inherit" });
  process.exit(r.status ?? 1);
}
