// <include file="machine/comments.xml" path="//term[@id='runner/wiki/prep.mjs']"/>
// 정적 계층을 돌려 위키가 읽을 재료를 만드는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// report-wiki prep <저장소> — 정적 계층을 돌려 deep-wiki 스킬이 읽을 재료를 만든다.
// 산문은 쓰지 않는다. 판정도 하지 않는다. 기계가 아는 사실만 결정론으로 낸다.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths, collectorFor, collectorFromSelect } from "./paths.mjs";
import { pythonPath } from "../../tools/python.mjs";
import { findCompdbs, mergeEntries, relativeFiles, clangUmlConfig, readAuthorConfig } from "./compdb.mjs";
import { clangDocPath, clangDocArgs } from "./clang-doc.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));

// <include file="machine/comments.xml" path="//term[@id='prepPlan']"/>
// 무엇을 어떤 순서로 돌릴지 정한다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * 무엇을 어떤 순서로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 테스트가 쉽다.
 * 막히면 steps 는 비고 blocked 에 사람이 읽을 사유가 담긴다.
 */
export function prepPlan({ collector, hasCodegraph, hasClangUmlConfig, hasRoslynDump, hasClangDoc }) {
  const tail = ["facts", "render-modules"];
  if (hasCodegraph) return { steps: tail, blocked: null };
  if (collector === "clang-uml") {
    if (!hasClangUmlConfig) {
      return { steps: [], blocked: "저장소 루트에 .clang-uml 설정이 없다." };
    }
    // clang-doc 은 **있으면 더 한다.** 없다고 막지 않는다 — 그 기계에서는 clang-uml 만으로
    // 옛 수준(타입만)의 결과가 나온다. 자유 함수 층이 비는 것은 손실이지 실패가 아니다.
    const doc = hasClangDoc ? ["clang-doc"] : [];
    return { steps: ["clang-uml", ...doc, "normalize", ...tail], blocked: null };
  }
  if (collector === "griffe+pycalls") {
    // 파이썬은 수집기 둘을 합친다 — griffe(클래스·상속·타입 주석)와 pycalls(함수·호출).
    // griffe 는 호출 관계를 내지 않으므로 pycalls 없이는 간선이 거의 없다.
    return { steps: ["griffe", "pycalls", "normalize", ...tail], blocked: null };
  }
  if (collector === "roslyn-dump") {
    if (!hasRoslynDump) {
      return {
        steps: [],
        blocked: "out/codegraph-raw/roslyn-dump.json 이 없다. machine/roslyn-dump 를 dotnet 으로 먼저 돌려라.",
      };
    }
    return { steps: ["normalize", ...tail], blocked: null };
  }
  return { steps: [], blocked: "정적 수집기를 고르지 못했다. .csproj/.slnx 도 CMakeLists.txt 도 없다." };
}

/**
 * `*.py` 를 가진 최상위 디렉토리 이름들. griffe 와 pycalls 가 같은 목록을 받아야
 * 두 수집기의 노드가 이름으로 맞물린다.
 *
 * 숨김 폴더와 재생성물(`out`·`node_modules`·`.venv`)은 뺀다. 하나도 없으면 `["."]` 다 —
 * 뿌리에 흩어진 스크립트뿐인 저장소가 그렇다.
 */
export function pyRoots(repo) {
  const skip = new Set(["out", "node_modules", ".venv", "__pycache__", "docs", "test"]);
  const roots = readdirSync(repo, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith(".") && !skip.has(e.name))
    .map((e) => e.name)
    .filter((name) => {
      try {
        return readdirSync(join(repo, name)).some((f) => f.endsWith(".py"));
      } catch {
        return false;
      }
    })
    .sort();
  return roots.length ? roots : ["."];
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
  // lang-select 단계가 낸 판정이 있으면 그것을 쓴다. 없으면 예전처럼 루트를 보고 고른다.
  const selectPath = join(P.raw, "lang-select.json");
  const fromSelect = existsSync(selectPath)
    ? collectorFromSelect(readFileSync(selectPath, "utf8"))
    : null;
  const collector = fromSelect ?? collectorFor(readdirSync(repo));
  // PATH 에 없는 도구라 찾아 둔다. 못 찾으면 null 이고 그 단계만 빠진다.
  const CLANG_DOC = collector === "clang-uml" ? clangDocPath() : null;
  const plan = prepPlan({
    collector,
    hasCodegraph: existsSync(P.codegraph),
    hasClangUmlConfig: existsSync(join(repo, ".clang-uml")),
    hasRoslynDump: existsSync(join(P.raw, "roslyn-dump.json")),
    hasClangDoc: Boolean(CLANG_DOC),
  });

  console.log(`대상 ${repo}`);
  console.log(`수집기 ${collector} · 단계 ${plan.steps.join(" -> ") || "(없음)"}`);
  if (collector === "clang-uml" && !CLANG_DOC) {
    console.warn("알림 — clang-doc 을 못 찾아 자유 함수 층이 빈다. "
      + "CLANG_DOC 환경변수로 알려 주거나 brew install llvm 하라.");
  }
  if (plan.blocked) {
    console.error(`막힘 — ${plan.blocked}`);
    process.exit(1);
  }
  mkdirSync(P.raw, { recursive: true });

  // clang-uml 단계가 만든 것을 clang-doc 단계가 그대로 쓴다 — 합친 compdb 를 두 번 만들지 않는다.
  const compdbDir = join(P.raw, "compdb");
  const docOutDir = join(P.raw, "clangdoc");
  let authorFlags = [];

  for (const step of plan.steps) {
    if (step === "clang-uml") {
      // 저장소 안의 compile_commands.json 을 **전부** 합친다 — CMake 타깃 트리가 여럿이다.
      const dbs = findCompdbs(repo);
      const lists = dbs.map((f) => { try { return JSON.parse(readFileSync(f, "utf8")); } catch { return []; } });
      const entries = mergeEntries(lists, repo);
      const files = relativeFiles(entries, repo);
      mkdirSync(compdbDir, { recursive: true });
      writeFileSync(join(compdbDir, "compile_commands.json"), JSON.stringify(entries, null, 1), "utf8");
      console.log(`compile_commands ${dbs.length}개 합침 -> 번역 단위 ${entries.length}개`);

      // 설정은 생성한다. 저자의 .clang-uml 에서는 플래그와 include 경로만 가져온다.
      const { flags, paths } = readAuthorConfig(join(repo, ".clang-uml"));
      authorFlags = flags;                     // clang-doc 단계도 같은 플래그를 쓴다
      const cfg = join(P.raw, ".clang-uml.generated");
      writeFileSync(cfg, clangUmlConfig({
        compdbDir, repo, outDir: P.raw, files, flags,
        paths: paths.length ? paths : [...new Set(files.map((f) => f.split("/")[0]))],
      }), "utf8");
      run("clang-uml", ["-c", cfg, "-g", "json"], repo);
    } else if (step === "clang-doc") {
      // 합친 compdb 를 그대로 먹인다. 저자 플래그(resource-dir · isysroot)가 없으면
      // Homebrew libclang 이 표준 헤더를 못 찾아 전량이 죽는다 — clang-uml 과 같은 사정이다.
      mkdirSync(docOutDir, { recursive: true });
      run(CLANG_DOC, clangDocArgs({
        outDir: docOutDir, repo, flags: authorFlags,
        compdbPath: join(compdbDir, "compile_commands.json"),
      }), repo);
    } else if (step === "griffe") {
      run(PY, ["-m", "griffe", "dump", ...pyRoots(repo),
               "-o", join(P.raw, "griffe.json"), "-s", repo], repo);
    } else if (step === "pycalls") {
      run(PY, [join(ROOT, "machine", "pycalls.py"), ...pyRoots(repo),
               "--repo", repo, "-o", join(P.raw, "pycalls.json")]);
    } else if (step === "normalize") {
      let arg;
      if (collector === "clang-uml") arg = ["--clang-uml", join(P.raw, "full_class.json")];
      else if (collector === "griffe+pycalls") {
        arg = ["--griffe-dump", join(P.raw, "griffe.json"),
               "--py-calls", join(P.raw, "pycalls.json")];
      } else arg = ["--roslyn-dump", join(P.raw, "roslyn-dump.json")];
      // clang-doc 이 돌았을 때만 얹는다. 안 돌았으면 옛 동작 그대로다.
      if (plan.steps.includes("clang-doc")) arg.push("--clang-doc", docOutDir);
      run(PY, [join(ROOT, "machine", "normalize.py"), ...arg, "--repo", repo, "-o", P.codegraph]);
    } else if (step === "facts") {
      const detail = join(P.raw, "roslyn-dump.json");
      const extra = existsSync(detail) ? ["--detail", detail] : [];
      run(PY, [join(ROOT, "machine", "facts.py"), P.codegraph, "--repo", repo, ...extra, "-o", P.raw]);
    } else if (step === "render-modules") {
      run(PY, [join(ROOT, "viz", "render_modules.py"), P.codegraph, "-o", join(P.raw, "modules")]);
    }
  }

  console.log(`\n준비 끝. 다음은 사람(스킬)의 차례다:`);
  console.log(`  재료  ${P.raw}/facts/ · ${P.raw}/ranking.json · ${P.codegraph}`);
  console.log(`  산문  ${P.wiki}/  <- deep-wiki 스킬이 여기에 쓴다 (추적 경로)`);
}
