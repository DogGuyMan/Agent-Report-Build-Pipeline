# Mode 1 stage ③ — 위키 진입점 구현 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 비어 있는 `bin/report-wiki` 를 채워 코드베이스 위키 생성을 **재현 가능한 3개 명령**으로 만들고, 두 대상 저장소(StickRushGame C# · QtVisionEdit C++)에서 완주한다.

**Architecture:** `report-term`(Mode 1.5)과 **같은 꼴**이다 — CLI 는 묻지도 쓰지도 않는다. `prep` 이 정적 계층과 주입 재료를 만들고, 가운데 산문은 deep-wiki 스킬이 쓰고, `build` 가 후처리(사전 렌더 SVG 치환 + VitePress)를, `check` 가 인용 검증을 한다. 세 스크립트는 `scripts/dispatch.mjs` 의 `runDispatch` 를 공유하고 경로 규약 하나(`scripts/wiki/paths.mjs`)만 함께 본다.

**Tech Stack:** Node(진입점·디스패치) + Python `codegraph/*.py`(정적 계층) + Graphviz 15.1.1 + VitePress 1.6.4 + 외부 수집기 2종(`clang-uml` 0.6.3 · `roslyn-dump` 0.1)

---

## 이 계획이 서 있는 실측 (2026-08-29 18:20~18:35, 전부 이 세션에서 명령을 돌려 확인)

| 사실 | 값 |
|---|---|
| `npm test` / `pytest codegraph/` / `tsc --noEmit` | 95 통과 / 62 통과 / 통과 |
| `bin/report-wiki` | **자리 표시자.** 안내문만 출력하고 `process.exit(0)` |
| VitePress 설정 | 이 저장소·대상 저장소 **모두 `.vitepress` 0건** |
| `vitepress` / `vitepress-plugin-mermaid` | `node_modules` 에 **설치돼 있음** (1.6.4) |
| StickRushGame 기존 위키 | `out/codegraph-raw/wiki/` **10장 2,635줄** + `wiki-built/` SVG 33개. `.gitignore:82` 로 **추적 안 됨** |
| QtVisionEdit clang-uml 완주 | `full_class.json` 36,909바이트 → `codegraph.json` **노드 14 · 간선 10 · 모듈 3**(core·protocol·server) → `facts/` 5장 + `ranking.json` |
| QtVisionEdit `.clang-uml` 상대경로 | `compilation_database_dir: build/macos` · `relative_to: .` · `output_directory: out/codegraph-raw` 가 **설정 파일 위치 기준으로 정상 해석된다** (probe 로 확인 후 원복) |
| QtVisionEdit `.gitignore` | **`out/` 을 무시하지 않는다.** StickRush 는 `.gitignore:82` 에 있다 — W3 을 지키려면 QtVisionEdit 에 규칙을 더해야 한다 |
| QtVisionEdit `app/` | 루트 compdb 에 **없다.** `app/CMakeLists.txt:8` 이 의도적으로 `add_subdirectory` 를 안 한다. 별도 compdb 는 `app/build/Qt_6_11_1_for_macOS_Debug/compile_commands.json` 에 있다 |

### 확정된 결정 (다시 논쟁하지 않는다)

| # | 결정 | 근거 |
|---|---|---|
| **W1** | **위키 산문은 대상 저장소의 `docs/wiki/` 에 남긴다.** `out/` 이 아니다 | 사용자 확정 2026-08-29. Mode 2 의 선례 — 원고(`data.ts`·`report.tsx`)는 대상 저장소에 살고 산출물(`out/report.html`)만 제외했다 |
| **W2** | **StickRushGame 의 기존 위키 10장은 새 기준으로 다시 만든다** | 사용자 확정 2026-08-29. 08-28 산출물이라 terms-db 우선 역전(08-29) 이전 기준이고, 전량 1회 완주가 있어야 WarmUp 의 baseline 비용이 나온다 |
| **W3** | **파생물(`codegraph.json`·`facts/`·`wiki-built/`·`wiki-site/`)은 `out/codegraph-raw/` 에 둔다** | 결정론으로 재생성되므로 추적하지 않는다. W1 이 말하는 "원고" 는 사람·LLM 이 쓴 산문뿐이다 |
| **W4** | **WarmUp(증분 캐시)은 이 계획의 범위 밖** | 사용자 확정 2026-08-29 — 위키 1회 완주 → baseline 비용 측정 → WarmUp. 순서를 뒤집으면 이득을 숫자로 말할 수 없다 |

### 가드레일

- **커밋은 사용자 승인 후에만.** 서브에이전트는 커밋하지 않는다. `git add -A` 금지 — 경로를 좁힌다.
- **`scripts/*.mjs` 는 직접 실행 가드를 둔다.** `if (process.argv[1] && process.argv[1].endsWith("prep.mjs")) { ... }`. 가드가 없으면 테스트가 import 하는 순간 `process.exit()` 이 러너를 죽인다.
- **거울 함정.** 플러그인 구조·수집기 레지스트리·추상 인터페이스를 만들지 않는다. 수집기는 2종 고정이고 소비자는 1개다.
- **대상 저장소는 남의 저장소다.** `docs/wiki/` 말고 다른 파일을 늘리지 않는다. `.clang-uml` 은 예외 — Task 6 에서 사용자 승인을 받는다.
- 커밋 메시지는 `personal-commit-messages` — 소문자 `[tag] : 제목` 한 줄, 한국어, 본문 없음.

---

## File Structure

| 파일 | 책임 | 신규/수정 |
|---|---|---|
| `scripts/wiki/paths.mjs` | 대상 저장소 하나의 **경로 규약**과 수집기 판별. 순수 함수만 | 신규 |
| `scripts/wiki/prep.mjs` | 정적 계층 실행 → `codegraph.json` · `facts/` · `ranking.json` · 모듈 다이어그램 | 신규 |
| `scripts/wiki/build.mjs` | `demermaid.py` 치환 → VitePress 설정 생성 → 정적 사이트 빌드 | 신규 |
| `scripts/wiki/check.mjs` | `verify_citations.py` 로 위키 산문의 인용을 3값 판정 | 신규 |
| `bin/report-wiki` | 자리 표시자 → `runDispatch` 배선 | 수정 |
| `test/wiki.test.mjs` | 위 순수 함수 전량의 회귀 | 신규 |
| `CLAUDE.md` | mode 진입점 표에서 `report-wiki` 행 갱신 | 수정 |

**분리 이유** — `paths.mjs` 는 소비자가 3개(`prep`·`build`·`check`)라 별도 파일이 정당하다. 나머지 셋은 `report-spec`(init/build/check)·`report-term`(collect/grade/emit)이 이미 쓰는 **명령 1개 = 스크립트 1개** 규약을 따른다.

---

## Task 1: 경로 규약 — `scripts/wiki/paths.mjs`

**Files:**
- Create: `scripts/wiki/paths.mjs`
- Test: `test/wiki.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/wiki.test.mjs` 를 새로 만든다:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { wikiPaths, collectorFor } from "../scripts/wiki/paths.mjs";

test("wikiPaths 는 산문을 추적 경로에, 파생물을 out 아래에 둔다", () => {
  const p = wikiPaths("/tmp/repo");
  assert.equal(p.wiki, "/tmp/repo/docs/wiki");
  assert.equal(p.raw, "/tmp/repo/out/codegraph-raw");
  assert.equal(p.built, "/tmp/repo/out/codegraph-raw/wiki-built");
  assert.equal(p.site, "/tmp/repo/out/codegraph-raw/wiki-site");
  assert.equal(p.codegraph, "/tmp/repo/out/codegraph-raw/codegraph.json");
});

test("collectorFor 는 csproj 를 보면 roslyn-dump 를 고른다", () => {
  assert.equal(collectorFor(["Assembly-CSharp.csproj", "Assets"]), "roslyn-dump");
});

test("collectorFor 는 slnx 만 있어도 roslyn-dump 를 고른다", () => {
  assert.equal(collectorFor(["StickRushGame.slnx"]), "roslyn-dump");
});

test("collectorFor 는 CMakeLists.txt 를 보면 clang-uml 을 고른다", () => {
  assert.equal(collectorFor(["CMakeLists.txt", "core", "server"]), "clang-uml");
});

test("collectorFor 는 C# 이 C++ 보다 앞선다 — Unity 는 둘 다 가질 수 있다", () => {
  assert.equal(collectorFor(["CMakeLists.txt", "Assembly-CSharp.csproj"]), "roslyn-dump");
});

test("collectorFor 는 아무것도 못 찾으면 none 을 낸다", () => {
  assert.equal(collectorFor(["package.json", "src"]), "none");
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -A3 "wiki"`
Expected: FAIL — `Cannot find module '.../scripts/wiki/paths.mjs'`

- [ ] **Step 3: `scripts/wiki/paths.mjs` 를 만든다**

```js
// scripts/wiki/paths.mjs
// Mode 1 위키의 경로 규약 한 곳. prep · build · check 세 명령이 전부 이것만 본다.
// 순수 함수만 노출한다 — CLI 본체가 없으므로 직접 실행 가드도 없다.
import { join } from "node:path";

/**
 * 대상 저장소 하나에 대한 경로 규약.
 *
 * W1 — 산문(`wiki`)은 대상 저장소의 **추적 경로**에 산다. LLM 이 쓴 원고이기 때문이다.
 * W3 — 파생물(`raw`·`built`·`site`)은 `out/` 아래에 둔다. 결정론으로 재생성되므로 추적하지 않는다.
 */
export function wikiPaths(repo) {
  const raw = join(repo, "out", "codegraph-raw");
  return {
    repo,
    raw,
    wiki: join(repo, "docs", "wiki"),
    built: join(raw, "wiki-built"),
    site: join(raw, "wiki-site"),
    codegraph: join(raw, "codegraph.json"),
  };
}

/**
 * 저장소 최상위 항목 목록을 보고 정적 수집기를 고른다.
 *
 * 수집기는 2종 고정이다 — 레지스트리를 만들지 않는다(거울 함정).
 * C# 을 먼저 보는 이유: Unity 저장소는 네이티브 플러그인 때문에 `CMakeLists.txt` 를
 * 함께 가질 수 있으나, 사용자 코드는 `.cs` 다.
 */
export function collectorFor(entries) {
  const has = (suffix) => entries.some((f) => f.endsWith(suffix));
  if (has(".csproj") || has(".slnx") || has(".sln")) return "roslyn-dump";
  if (entries.includes("CMakeLists.txt")) return "clang-uml";
  return "none";
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `npm test 2>&1 | tail -8`
Expected: `pass 101` (기존 95 + 신규 6), `fail 0`

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add scripts/wiki/paths.mjs test/wiki.test.mjs
git commit -m "[feat] : 위키 경로 규약과 수집기 판별"
```

---

## Task 2: 준비 명령 — `scripts/wiki/prep.mjs`

정적 계층을 돌려 deep-wiki 스킬이 읽을 재료를 만든다. **산문은 쓰지 않는다.**

**Files:**
- Create: `scripts/wiki/prep.mjs`
- Modify: `test/wiki.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/wiki.test.mjs` 끝에 붙인다:

```js
import { prepPlan } from "../scripts/wiki/prep.mjs";

test("prepPlan 은 codegraph.json 이 있으면 수집기를 건너뛴다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: true, hasClangUmlConfig: true, hasRoslynDump: false });
  assert.deepEqual(p.steps, ["facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C++ 이고 설정이 있으면 clang-uml 부터 돈다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: true, hasRoslynDump: false });
  assert.deepEqual(p.steps, ["clang-uml", "normalize", "facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C++ 인데 .clang-uml 이 없으면 막힌다", () => {
  const p = prepPlan({ collector: "clang-uml", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /\.clang-uml/);
});

test("prepPlan 은 C# 이고 roslyn-dump.json 이 있으면 normalize 부터 돈다", () => {
  const p = prepPlan({ collector: "roslyn-dump", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: true });
  assert.deepEqual(p.steps, ["normalize", "facts", "render-modules"]);
  assert.equal(p.blocked, null);
});

test("prepPlan 은 C# 인데 roslyn-dump.json 이 없으면 막힌다 — dotnet 은 우리가 못 돌린다", () => {
  const p = prepPlan({ collector: "roslyn-dump", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /roslyn-dump\.json/);
});

test("prepPlan 은 수집기를 못 고르면 막힌다", () => {
  const p = prepPlan({ collector: "none", hasCodegraph: false, hasClangUmlConfig: false, hasRoslynDump: false });
  assert.deepEqual(p.steps, []);
  assert.match(p.blocked, /수집기/);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -c "prepPlan"`
Expected: FAIL — `Cannot find module '.../scripts/wiki/prep.mjs'`

- [ ] **Step 3: `scripts/wiki/prep.mjs` 를 만든다**

```js
// scripts/wiki/prep.mjs
// report-wiki prep <저장소> — 정적 계층을 돌려 deep-wiki 스킬이 읽을 재료를 만든다.
// 산문은 쓰지 않는다. 판정도 하지 않는다. 기계가 아는 사실만 결정론으로 낸다.
import { existsSync, mkdirSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths, collectorFor } from "./paths.mjs";
import { pythonPath } from "../python.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const PY = pythonPath(ROOT);   // 기계마다 다르다 — scripts/python.mjs 가 찾는다

/**
 * 무엇을 어떤 순서로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 테스트가 쉽다.
 * 막히면 steps 는 비고 blocked 에 사람이 읽을 사유가 담긴다.
 */
export function prepPlan({ collector, hasCodegraph, hasClangUmlConfig, hasRoslynDump }) {
  const tail = ["facts", "render-modules"];
  if (hasCodegraph) return { steps: tail, blocked: null };
  if (collector === "clang-uml") {
    if (!hasClangUmlConfig) {
      return { steps: [], blocked: "저장소 루트에 .clang-uml 설정이 없다. Task 6 을 보라." };
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
      run("clang-uml", ["-c", join(repo, ".clang-uml"), "-g", "json"], repo);
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
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `npm test 2>&1 | tail -8`
Expected: `pass 107` (Task 1 의 101 + 신규 6), `fail 0`

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add scripts/wiki/prep.mjs test/wiki.test.mjs
git commit -m "[feat] : 위키 준비 명령 - 정적 계층과 주입 재료"
```

---

## Task 3: 진입점 배선 — `bin/report-wiki`

**Files:**
- Modify: `bin/report-wiki` (전량 교체)
- Modify: `test/wiki.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/wiki.test.mjs` 끝에 붙인다:

```js
import { readFileSync } from "node:fs";

test("report-wiki 는 세 명령을 디스패치 표에 갖는다", () => {
  const src = readFileSync(new URL("../bin/report-wiki", import.meta.url), "utf8");
  assert.match(src, /prep: "scripts\/wiki\/prep\.mjs"/);
  assert.match(src, /build: "scripts\/wiki\/build\.mjs"/);
  assert.match(src, /check: "scripts\/wiki\/check\.mjs"/);
  assert.match(src, /runDispatch/);
  assert.doesNotMatch(src, /아직 이 진입점은 비어 있다/);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -A5 "report-wiki 는 세 명령"`
Expected: FAIL — `아직 이 진입점은 비어 있다` 가 아직 남아 있다

- [ ] **Step 3: `bin/report-wiki` 를 통째로 바꾼다**

```js
#!/usr/bin/env node
// <include file="docs/codegraph/comments.xml" path="//term[@id='report-wiki']"/>
// Mode 1 의 진입점. 코드베이스 위키를 만든다.
// 쓰는 것: runDispatch · 쓰이는 곳: 없음
// bin/report-wiki — Mode 1. 코드베이스 위키.
//   prep  : 정적 계층을 돌려 주입 재료(facts/*.md · ranking.json · codegraph.json)를 만든다
//   (산문 작성은 CLI 의 일이 아니다 — deep-wiki 스킬이 docs/wiki/ 에 쓴다)
//   build : Mermaid 를 사전 렌더 SVG 로 치환하고 VitePress 정적 사이트를 만든다
//   check : 위키 산문의 인용을 3값(있음/없음/근거없음)으로 판정한다
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runDispatch } from "../scripts/dispatch.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

runDispatch({
  root: ROOT,
  argv: process.argv.slice(2),
  table: {
    prep: "scripts/wiki/prep.mjs",
    build: "scripts/wiki/build.mjs",
    check: "scripts/wiki/check.mjs",
  },
  usage: "사용법 — report-wiki <prep|build|check> <저장소 경로>",
});
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `npm test 2>&1 | tail -8 && bin/report-wiki`
Expected: 테스트 `pass 108` · `fail 0`. `bin/report-wiki` 는 `사용법 — report-wiki <prep|build|check> <저장소 경로>` 를 내고 exit 1

> ⚠ **`build.mjs` 와 `check.mjs` 는 Task 4·5 에서 만든다.** 이 시점에 `report-wiki build` 를 부르면 Node 가 모듈을 못 찾아 죽는다. 정상이다 — Task 4 로 넘어간다.

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add bin/report-wiki test/wiki.test.mjs
git commit -m "[feat] : report-wiki 진입점 배선 - prep, build, check"
```

---

## Task 4: 빌드 명령 — `scripts/wiki/build.mjs`

`demermaid.py` 로 Mermaid 를 사전 렌더 SVG 로 바꾸고, VitePress 설정을 만들어 정적 사이트를 낸다.

**Files:**
- Create: `scripts/wiki/build.mjs`
- Modify: `test/wiki.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/wiki.test.mjs` 끝에 붙인다:

```js
import { vitepressConfig, sidebarFrom } from "../scripts/wiki/build.mjs";

test("sidebarFrom 은 마크다운 파일을 링크 항목으로 바꾼다", () => {
  const s = sidebarFrom(["managers.md", "data.md", "index.md"]);
  assert.deepEqual(s, [
    { text: "data", link: "/data" },
    { text: "managers", link: "/managers" },
  ]);
});

test("sidebarFrom 은 index 를 사이드바에서 뺀다", () => {
  assert.deepEqual(sidebarFrom(["index.md"]), []);
});

test("vitepressConfig 는 제목과 사이드바를 담고 srcDir 를 현재 폴더로 둔다", () => {
  const cfg = vitepressConfig("StickRushGame", [{ text: "data", link: "/data" }], "../wiki-site");
  assert.match(cfg, /title: "StickRushGame 코드베이스 위키"/);
  assert.match(cfg, /outDir: "\.\.\/wiki-site"/);
  assert.match(cfg, /\{ text: "data", link: "\/data" \}/);
  assert.match(cfg, /import \{ defineConfig \} from "vitepress"/);
});

test("vitepressConfig 는 제목의 따옴표를 이스케이프한다", () => {
  const cfg = vitepressConfig('Qt"Vision', [], "../wiki-site");
  assert.match(cfg, /title: "Qt\\"Vision 코드베이스 위키"/);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -c "sidebarFrom"`
Expected: FAIL — `Cannot find module '.../scripts/wiki/build.mjs'`

- [ ] **Step 3: `scripts/wiki/build.mjs` 를 만든다**

```js
// scripts/wiki/build.mjs
// report-wiki build <저장소> — 산문 후처리.
//   1) demermaid.py 가 Mermaid 를 사전 렌더 SVG 로 바꾼다 (결정 C-18)
//   2) 그 결과 폴더에 VitePress 설정을 만들고 정적 사이트를 낸다
// Mermaid 를 런타임에 그리지 않으므로 vitepress-plugin-mermaid 는 쓰지 않는다.
import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { wikiPaths } from "./paths.mjs";
import { pythonPath } from "../python.mjs";

const ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const PY = pythonPath(ROOT);   // 기계마다 다르다 — scripts/python.mjs 가 찾는다

/** 마크다운 파일 목록 -> VitePress 사이드바 항목. index 는 뺀다(홈이 따로 링크한다). */
export function sidebarFrom(files) {
  return files
    .filter((f) => f.endsWith(".md") && f !== "index.md")
    .map((f) => f.replace(/\.md$/, ""))
    .sort()
    .map((name) => ({ text: name, link: `/${name}` }));
}

/** VitePress 설정 파일 본문. 제목은 JSON.stringify 로 이스케이프한다. */
export function vitepressConfig(repoName, sidebar, outDir) {
  const items = sidebar.map((s) => `      { text: ${JSON.stringify(s.text)}, link: ${JSON.stringify(s.link)} }`);
  return `import { defineConfig } from "vitepress";

// report-wiki build 가 생성한다. 손으로 고치지 말 것 — 다음 빌드에서 덮어쓴다.
export default defineConfig({
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
  run(PY, [join(ROOT, "codegraph", "demermaid.py"), P.wiki, "--out", P.built, ...svgDir]);

  // 2) VitePress 설정 생성
  const files = readdirSync(P.built);
  const sidebar = sidebarFrom(files);
  const cfgDir = join(P.built, ".vitepress");
  mkdirSync(cfgDir, { recursive: true });
  writeFileSync(join(cfgDir, "config.mts"), vitepressConfig(repo.split("/").pop(), sidebar, P.site), "utf8");

  // 3) 정적 사이트 빌드 — vitepress 는 이 저장소의 node_modules 에 있다
  run(join(ROOT, "node_modules", ".bin", "vitepress"), ["build", P.built], ROOT);

  console.log(`\n사이트 ${P.site}`);
  console.log(`  페이지 ${sidebar.length}개 · 열기: open ${join(P.site, "index.html")}`);
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `npm test 2>&1 | tail -8`
Expected: `pass 112` · `fail 0`

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add scripts/wiki/build.mjs test/wiki.test.mjs
git commit -m "[feat] : 위키 빌드 명령 - svg 치환과 vitepress 사이트"
```

---

## Task 5: 검사 명령 — `scripts/wiki/check.mjs`

**Files:**
- Create: `scripts/wiki/check.mjs`
- Modify: `test/wiki.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/wiki.test.mjs` 끝에 붙인다:

```js
import { checkArgs } from "../scripts/wiki/check.mjs";

test("checkArgs 는 산문 전량을 인자로 싣는다", () => {
  const a = checkArgs({
    repo: "/tmp/r",
    codegraph: "/tmp/r/out/codegraph-raw/codegraph.json",
    detail: null,
    docs: ["/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md"],
  });
  assert.deepEqual(a, [
    "--repo", "/tmp/r",
    "--codegraph", "/tmp/r/out/codegraph-raw/codegraph.json",
    "/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md",
  ]);
});

test("checkArgs 는 살 파일이 있으면 --detail 을 끼운다", () => {
  const a = checkArgs({
    repo: "/tmp/r",
    codegraph: "/tmp/r/cg.json",
    detail: "/tmp/r/roslyn-dump.json",
    docs: ["/tmp/r/docs/wiki/a.md"],
  });
  assert.deepEqual(a, [
    "--repo", "/tmp/r", "--codegraph", "/tmp/r/cg.json",
    "--detail", "/tmp/r/roslyn-dump.json", "/tmp/r/docs/wiki/a.md",
  ]);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -c "checkArgs"`
Expected: FAIL — `Cannot find module '.../scripts/wiki/check.mjs'`

- [ ] **Step 3: `scripts/wiki/check.mjs` 를 만든다**

```js
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
const PY = pythonPath(ROOT);   // 기계마다 다르다 — scripts/python.mjs 가 찾는다

/** verify_citations.py 에 넘길 인자를 만든다. 순수 함수라 테스트가 쉽다. */
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
  const r = spawnSync(PY, [join(ROOT, "codegraph", "verify_citations.py"), ...args], { stdio: "inherit" });
  process.exit(r.status ?? 1);
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `npm test 2>&1 | tail -8`
Expected: `pass 114` · `fail 0`

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add scripts/wiki/check.mjs test/wiki.test.mjs
git commit -m "[feat] : 위키 검사 명령 - 인용 3값 판정"
```

---

## Task 6: QtVisionEdit 에 `.clang-uml` 설정을 심고 prep 을 완주한다

이 설정은 **남의 저장소에 파일을 늘리는 일**이다. 넣기 전에 사용자 승인을 받는다.

**Files:**
- Create: `$CPP_REPO/.clang-uml` (**대상 저장소**)

- [ ] **Step 1: 두 compdb 의 번역 단위를 센다**

```bash
Q=$CPP_REPO
python3 -c "
import json
for p in ['$Q/build/macos/compile_commands.json',
          '$Q/app/build/Qt_6_11_1_for_macOS_Debug/compile_commands.json']:
    try:
        d = json.load(open(p))
        print(len(d), p.replace('$Q/',''))
    except Exception as e:
        print('없음/오류', p.replace('$Q/',''), e)
"
```

Expected: 루트 compdb 는 **33**. app compdb 는 존재하며 0 보다 크다.
🔵 2026-08-29 실측 — 루트 33개이고 그중 `app/` 은 **0개**다(`app/CMakeLists.txt:8` 이 의도적으로 `add_subdirectory` 를 안 한다).

- [ ] **Step 2: `.clang-uml` 을 쓴다**

`$Q/.clang-uml` 에 그대로 넣는다. `compilation_database_dir` 와 `relative_to` 는 **설정 파일 위치 기준 상대경로**로 해석된다 — 설정이 저장소 루트에 있으므로 아래가 맞다.

**두 경로는 기계마다 다르다 — 물어서 넣는다. 박지 말 것.**

```bash
RESDIR=$(brew --prefix llvm@22 2>/dev/null)/lib/clang/22   # 또는: clang -print-resource-dir
SYSROOT=$(xcrun --show-sdk-path)
echo "$RESDIR"; echo "$SYSROOT"
```

Expected: 둘 다 존재하는 폴더. 리눅스라면 `add_compile_flags` 두 줄이 아예 필요 없을 수 있다 —
`clang-uml` 과 compdb 의 컴파일러가 같은 clang 이면 그렇다. 먼저 빼고 돌려 보고, 죽으면 넣는다.

```yaml
# report-wiki prep 이 읽는 clang-uml 설정.
# add_compile_flags 가 왜 필요한가 — compile_commands.json 의 컴파일러는 AppleClang 인데
# clang-uml 은 Homebrew libclang 으로 읽는다. resource-dir 를 명시하지 않으면 표준 헤더를
# 못 찾아 죽는다. 🔵 2026-08-29 macOS 에서 확인. 아래 두 경로는 위 명령의 출력으로 채운다.
compilation_database_dir: build/macos
relative_to: .
output_directory: out/codegraph-raw
add_compile_flags:
  - -resource-dir=<위 RESDIR>
  - -isysroot
  - <위 SYSROOT>
diagrams:
  full_class:
    type: class
    # test/ 는 뺀다 — 산문의 대상이 아니다. app/ 은 루트 compdb 에 없어 여기서 안 잡힌다.
    glob: [core/**/*.cpp, protocol/**/*.cpp, server/**/*.cpp]
    include:
      paths: [core, protocol, server, app]
```

- [ ] **Step 3: prep 을 돌린다**

```bash
Q=$CPP_REPO
report-wiki prep "$Q"
```

Expected: `수집기 clang-uml · 단계 clang-uml -> normalize -> facts -> render-modules` 로 시작해
`codegraph.json` **노드 14 · 간선 10 · 모듈 3**(core · protocol · server)과 `facts/` 5장이 나온다.
🔵 2026-08-29 스크래치패드에서 같은 사슬을 손으로 돌려 이 수치를 확인했다.

- [ ] **Step 4: `out/` 을 무시 규칙에 넣는다 (W3)**

🔵 2026-08-29 실측 — QtVisionEdit 의 `.gitignore` 는 `out/` 을 무시하지 **않는다**. 그대로 두면 `prep` 이 만든 파생물이 전부 미추적 파일로 뜬다. StickRush 는 이미 `.gitignore:82` 에 `out/codegraph-raw/` 가 있어 해당 없음.

```bash
Q=$CPP_REPO
printf '\n# report-wiki 파생물 - codegraph 에서 재생성한다\nout/codegraph-raw/\n' >> "$Q/.gitignore"
git -C "$Q" status --porcelain -uall
```

Expected: `.gitignore` 만 `M` 으로 뜨고 `out/` 아래 파일은 목록에 없다

- [ ] **Step 5: `app/` 을 넣을지 사용자에게 보고한다**

`app/src/view` 16파일이 위키에서 빠진다. `app/build/Qt_6_11_1_for_macOS_Debug/compile_commands.json` 을 두 번째 `.clang-uml` 다이어그램으로 붙이면 들어오지만, Qt Creator 가 만든 빌드 트리라 커밋된 프리셋으로 재현되지 않는다.
**혼자 정하지 말고 수치와 함께 보고한다** — "app 을 빼면 노드 14, 넣으면 몇 개" 를 실측해서 낸다.

- [ ] **Step 6: 커밋 (사용자 승인 후 — 대상 저장소에서)**

```bash
cd $CPP_REPO
git add .clang-uml .gitignore
git commit -m "[chore] : report-wiki 용 clang-uml 설정과 파생물 무시 규칙"
```

---

## Task 7: StickRushGame prep 을 새 기준으로 완주한다

W2 — 기존 위키 10장은 버리고 다시 만든다.

**Files:**
- Create: `$CSHARP_REPO/docs/wiki/` (**대상 저장소**, 다음 Task 에서 채워짐)

- [ ] **Step 1: 기존 위키를 백업 없이 지우지 않는다 — 옆으로 옮긴다**

```bash
CS=$CSHARP_REPO
mv "$CS/out/codegraph-raw/wiki" "$CS/out/codegraph-raw/wiki-2026-08-28-pilot"
```

Expected: 이동만 된다. 이 폴더는 `.gitignore:82` 로 추적되지 않으므로 git 은 아무 말도 하지 않는다.
**지우지 않는 이유** — 새 산문과 대조해 "terms-db 역전이 위키를 어떻게 바꿨나" 를 볼 재료다.

- [ ] **Step 2: prep 을 돌린다**

```bash
CS=$CSHARP_REPO
report-wiki prep "$CS"
```

Expected: `수집기 roslyn-dump` 로 시작한다. `out/codegraph-raw/roslyn-dump.json` 이 이미 있으므로 `단계 normalize -> facts -> render-modules` 로 간다. `facts/` 5장과 `ranking.json` 이 새로 쓰인다.

- [ ] **Step 3: `roslyn-dump.json` 이 없으면 막힘 메시지가 정확한지 확인한다**

```bash
CS=$CSHARP_REPO
mv "$CS/out/codegraph-raw/roslyn-dump.json" /tmp/rd.json
mv "$CS/out/codegraph-raw/codegraph.json" /tmp/cg.json
report-wiki prep "$CS"; echo "exit=$?"
mv /tmp/rd.json "$CS/out/codegraph-raw/roslyn-dump.json"
mv /tmp/cg.json "$CS/out/codegraph-raw/codegraph.json"
```

Expected: `막힘 — out/codegraph-raw/roslyn-dump.json 이 없다...` 와 `exit=1`

- [ ] **Step 4: 산문 폴더를 만든다**

```bash
mkdir -p $CSHARP_REPO/docs/wiki
```

- [ ] **Step 5: 커밋 없음**

이 Task 는 대상 저장소의 파생물만 건드린다(전부 `.gitignore` 대상). `docs/wiki/` 는 비어 있어 git 이 추적하지 않는다. 커밋은 Task 8 이 산문을 채운 뒤다.

---

## Task 8: 산문 — deep-wiki 스킬이 쓴다 (CLI 밖)

**이 Task 는 코드를 쓰지 않는다.** CLI 는 여기서 멈춘다. **두 저장소 각각에 대해 Step 1~5 를 돌린다** — 아래 `R` 자리에 저장소 경로를 넣는다.

```bash
# ① C#
R=$CSHARP_REPO
# ② C++
R=$CPP_REPO
```

- [ ] **Step 1: 재료를 확인한다**

```bash
ls "$R/out/codegraph-raw/facts/" && head -20 "$R/out/codegraph-raw/facts/modules.md"
```

Expected: `modules.md · classes.md · external.md · entrypoints.md · hotspot.md` 5장

- [ ] **Step 2: `codebase-terms-survey` 스킬로 전수조사를 돌린다**

산출물은 대상 저장소의 `docs/codegraph/terms-reading.json` 이다. 이 저장소에서 했던 것과 같은 규율을 따른다 — 레코드 계약은 `{id, kind, module, where, means, does?, uses[], confidence, source}`, `neighbors` 는 손으로 쓰지 않는다.

**C++(②)에서 주의할 것** — 용어 키에 네임스페이스가 붙는 문제(열린 결정 R3)가 여기서 처음 실제로 나타난다. 마주치면 **혼자 정하지 말고 사례와 함께 보고**한다.

- [ ] **Step 3: deep-wiki 스킬로 산문을 쓴다**

`wiki-architect` → `wiki-researcher` → `wiki-page-writer` 순. 출력 경로는 **`$R/docs/wiki/`** 다(W1). 페이지는 `facts/modules.md` 의 모듈 목록을 따른다.

- ① StickRushGame — 모듈 10개 안팎. **기존 파일럿 10장을 참고하지 않는다**(W2 — 낡은 기준이다). 대조는 Task 9 Step 3 에서 한다.
- ② QtVisionEdit — 🔵 실측 모듈 **3개**(`core` · `protocol` · `server`)에 클래스 11개. 작다 — 페이지도 3장 안팎이 정상이다.

- [ ] **Step 4: 산문이 자리에 있는지 확인한다**

```bash
mkdir -p "$R/docs/wiki" && ls "$R/docs/wiki/"*.md | wc -l
```

Expected: 1 이상

- [ ] **Step 5: 커밋 (사용자 승인 후 — 대상 저장소에서)**

```bash
cd "$R"
git add docs/wiki docs/codegraph
git commit -m "[docs] : 코드베이스 위키 산문과 용어 전수조사"
```

---

## Task 9: build · check 완주와 문서 갱신

- [ ] **Step 1: 두 저장소에서 build 를 돌린다**

```bash
report-wiki build $CSHARP_REPO
report-wiki build $CPP_REPO
```

Expected: 각각 `사이트 .../out/codegraph-raw/wiki-site` 와 `페이지 N개` 가 나오고 `index.html` 이 생긴다

- [ ] **Step 2: 두 저장소에서 check 를 돌린다**

```bash
report-wiki check $CSHARP_REPO
report-wiki check $CPP_REPO
```

Expected: `L1 통과 n / 실패 0`. **L3 의 "근거없음" 은 실패가 아니다** — 수치를 보고만 한다.

- [ ] **Step 3: baseline 비용을 기록한다 (W4 의 전제)**

```bash
CS=$CSHARP_REPO
echo "전량 1회 완주 — 페이지 $(ls $CS/docs/wiki/*.md | wc -l), 산문 $(cat $CS/docs/wiki/*.md | wc -l) 줄"
```

이 수치를 `docs/handoffs/RESUME-2026-08-29-mode-1-5-orchestrator.md` 의 🔴 최우선 절에 적는다. **WarmUp 의 이득은 이 값과 비교해서만 말할 수 있다.**

- [ ] **Step 4: `CLAUDE.md` 의 진입점 표를 고친다**

`## 명령` 절의 mode 표에서 `report-wiki` 행을 바꾼다:

```
| `report-wiki` | 1 | `prep` · `build` · `check` | 코드베이스 위키. `prep` 이 정적 계층과 주입 재료를, `build` 가 SVG 치환 + VitePress 를, `check` 가 인용 3값 판정을 한다. **산문은 CLI 밖** — `codebase-terms-survey` 와 deep-wiki 스킬이 `<저장소>/docs/wiki/` 에 쓴다 |
```

같은 절에 사용법을 더한다:

```bash
report-wiki prep  <저장소>   # → out/codegraph-raw/{codegraph.json, facts/, ranking.json}
#   (스킬이 <저장소>/docs/wiki/*.md 를 쓴다)
report-wiki build <저장소>   # → out/codegraph-raw/{wiki-built/, wiki-site/}
report-wiki check <저장소>   # 인용 L1/L2/L3
```

- [ ] **Step 5: 커밋 (사용자 승인 후)**

```bash
git add CLAUDE.md docs/handoffs/RESUME-2026-08-29-mode-1-5-orchestrator.md
git commit -m "[docs] : report-wiki 진입점 반영과 위키 완주 실측"
```

---

## 이 계획이 하지 않는 것

| 안 하는 것 | 왜 |
|---|---|
| **WarmUp 증분 캐시** | W4 — 전량 1회 완주가 있어야 이득을 잴 수 있다. `2026-08-28-llm-load-reduction.md` Task 5 가 그 계획이고 `codegraph/warmup.py` 는 아직 없다 |
| **`render_classes.py` 를 prep 에 넣기** | Graphviz 15.1.1 이 일부 모듈에서 `mincross.c:273` 어서션으로 죽는다(🔵 이 저장소 `codegraph` 모듈에서 재현). 상류 버그라 우리가 못 고친다. 모듈 다이어그램만 넣고 클래스 다이어그램은 손으로 부른다 |
| **수집기 자동 설치·빌드** | `dotnet` 과 `cmake` 는 대상 저장소마다 설정이 다르다. `prep` 은 재료가 없으면 **정확한 사유와 함께 exit 1** 을 낸다 |
| **VitePress 에 Mermaid 런타임 얹기** | 결정 C-18 — 다이어그램은 사전 렌더 SVG 다. `vitepress-plugin-mermaid` 는 설치돼 있지만 쓰지 않는다 |
