// <include file="docs/codegraph/comments.xml" path="//term[@id='scripts/wiki/prep.mjs']"/>
// scripts/wiki/prep.mjs
// report-wiki prep <저장소> — 정적 계층을 돌려 deep-wiki 스킬이 읽을 재료를 만든다.
// 산문은 쓰지 않는다. 판정도 하지 않는다. 기계가 아는 사실만 결정론으로 낸다.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths, collectorFor } from "./paths.mjs";
import { pythonPath } from "../python.mjs";
import { findCompdbs, mergeEntries, relativeFiles, clangUmlConfig, readAuthorConfig } from "./compdb.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));

/**
 * 무엇을 어떤 순서로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 테스트가 쉽다.
 * 막히면 steps 는 비고 blocked 에 사람이 읽을 사유가 담긴다.
 */
// <include file="docs/codegraph/comments.xml" path="//term[@id='prepPlan']"/>
export function prepPlan({ collector, hasCodegraph, hasClangUmlConfig, hasRoslynDump }) {
  const tail = ["facts", "render-modules"];
  if (hasCodegraph) return { steps: tail, blocked: null };
  if (collector === "clang-uml") {
    if (!hasClangUmlConfig) {
      return { steps: [], blocked: "저장소 루트에 .clang-uml 설정이 없다." };
    }
    return { steps: ["clang-uml", "normalize", ...tail], blocked: null };
  }
  if (collector === "roslyn-dump") {
    if (!hasRoslynDump) {
      return {
        steps: [],
        blocked: "out/codegraph-raw/roslyn-dump.json 이 없다. codegraph/roslyn-dump 를 dotnet 으로 먼저 돌려라.",
      };
    }
    return { steps: ["normalize", ...tail], blocked: null };
  }
  return { steps: [], blocked: "정적 수집기를 고르지 못했다. .csproj/.slnx 도 CMakeLists.txt 도 없다." };
}

function run(cmd, args, cwd) {
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd });
  if (r.status !== 0) {
    console.error(`실패 — ${cmd} ${args.join(" ")}`);
    process.exit(r.status ?? 1);
  }
}

if (process.argv[1] && process.argv[1].endsWith("prep.mjs")) {
  const repoArg = process.argv[2];
  if (!repoArg) {
    console.error("사용법 — report-wiki prep <저장소 경로>");
    process.exit(1);
  }
  const repo = resolve(repoArg.replace(/^~/, process.env.HOME ?? "~"));
  if (!existsSync(repo)) {
    console.error(`에러 — 저장소가 없다: ${repo}`);
    process.exit(1);
  }
  const P = wikiPaths(repo);
  const PY = pythonPath(ROOT);
  const collector = collectorFor(readdirSync(repo));
  const plan = prepPlan({
    collector,
    hasCodegraph: existsSync(P.codegraph),
    hasClangUmlConfig: existsSync(join(repo, ".clang-uml")),
    hasRoslynDump: existsSync(join(P.raw, "roslyn-dump.json")),
  });

  console.log(`대상 ${repo}`);
  console.log(`수집기 ${collector} · 단계 ${plan.steps.join(" -> ") || "(없음)"}`);
  if (plan.blocked) {
    console.error(`막힘 — ${plan.blocked}`);
    process.exit(1);
  }
  mkdirSync(P.raw, { recursive: true });

  for (const step of plan.steps) {
    if (step === "clang-uml") {
      // 저장소 안의 compile_commands.json 을 **전부** 합친다 — CMake 타깃 트리가 여럿이다.
      const dbs = findCompdbs(repo);
      const lists = dbs.map((f) => { try { return JSON.parse(readFileSync(f, "utf8")); } catch { return []; } });
      const entries = mergeEntries(lists, repo);
      const files = relativeFiles(entries, repo);
      const compdbDir = join(P.raw, "compdb");
      mkdirSync(compdbDir, { recursive: true });
      writeFileSync(join(compdbDir, "compile_commands.json"), JSON.stringify(entries, null, 1), "utf8");
      console.log(`compile_commands ${dbs.length}개 합침 -> 번역 단위 ${entries.length}개`);

      // 설정은 생성한다. 저자의 .clang-uml 에서는 플래그와 include 경로만 가져온다.
      const { flags, paths } = readAuthorConfig(join(repo, ".clang-uml"));
      const cfg = join(P.raw, ".clang-uml.generated");
      writeFileSync(cfg, clangUmlConfig({
        compdbDir, repo, outDir: P.raw, files, flags,
        paths: paths.length ? paths : [...new Set(files.map((f) => f.split("/")[0]))],
      }), "utf8");
      run("clang-uml", ["-c", cfg, "-g", "json"], repo);
    } else if (step === "normalize") {
      const arg = collector === "clang-uml"
        ? ["--clang-uml", join(P.raw, "full_class.json")]
        : ["--roslyn-dump", join(P.raw, "roslyn-dump.json")];
      run(PY, [join(ROOT, "codegraph", "normalize.py"), ...arg, "--repo", repo, "-o", P.codegraph]);
    } else if (step === "facts") {
      const detail = join(P.raw, "roslyn-dump.json");
      const extra = existsSync(detail) ? ["--detail", detail] : [];
      run(PY, [join(ROOT, "codegraph", "facts.py"), P.codegraph, "--repo", repo, ...extra, "-o", P.raw]);
    } else if (step === "render-modules") {
      run(PY, [join(ROOT, "codegraph", "render_modules.py"), P.codegraph, "-o", join(P.raw, "modules")]);
    }
  }

  console.log(`\n준비 끝. 다음은 사람(스킬)의 차례다:`);
  console.log(`  재료  ${P.raw}/facts/ · ${P.raw}/ranking.json · ${P.codegraph}`);
  console.log(`  산문  ${P.wiki}/  <- deep-wiki 스킬이 여기에 쓴다 (추적 경로)`);
}
