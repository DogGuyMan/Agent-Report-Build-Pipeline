// <include file="machine/comments.xml" path="//term[@id='runner/wiki/clang-doc.mjs']"/>
// clang-doc 실행 파일을 기계에 상관없이 찾는 파일.
// 쓰는 것: clangDocPath · 쓰이는 곳: 없음
// `clang-doc` 실행 파일을 **기계에 상관없이** 찾는다.
//
// **왜 필요한가.** C++ 정적 수집기는 둘이다 — `clang-uml` 은 클래스 관계를 알고
// `clang-doc` 은 심볼 전량을 안다. 🔵 2026-08-29 QtVisionEdit 실측 — clang-uml 이 낸
// 1차 노드 30개가 전부 타입이고 자유 함수는 0개였다. 그 저장소의 핵심 로직이
// 네임스페이스 안 자유 함수라 함수 층이 통째로 비어 있었다.
//
// **그런데 `clang-doc` 은 PATH 에 없다.** LLVM 번들이라 Homebrew 의 keg 안에 숨어 있고
// (`/opt/homebrew/opt/llvm@22/bin/clang-doc`), 리눅스에서는 또 다른 자리다.
// `tools/python.mjs` 가 파이썬을 찾는 것과 같은 꼴로 **찾아서** 쓴다 — 박지 않는다.
//
// 찾는 순서 — 환경변수 `CLANG_DOC` → `brew --prefix` 가 아는 LLVM keg → PATH.
//
// **못 찾아도 막지 않는다.** clang-doc 이 없는 기계에서는 clang-uml 만으로 옛 수준의
// 결과가 나와야 한다. 그래서 `clangDocPath()` 는 실패를 예외가 아니라 `null` 로 낸다.
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { delimiter, join } from "node:path";

// 어느 formula 에 들어 있는지가 기계마다 다르다. 버전 붙은 쪽을 먼저 본다.
const BREW_FORMULAE = ["llvm@22", "llvm"];

// <include file="machine/comments.xml" path="//term[@id='clangDocCandidates']"/>
// clang-doc 이 있을 만한 자리를 순서대로 늘어놓는다.
// 쓰는 것: 없음 · 쓰이는 곳: clangDocPath
/**
 * 후보 경로를 순서대로 만든다. 파일 시스템도 bash 도 보지 않는 순수 함수라 테스트가 쉽다.
 * `prefixes` 는 부르는 쪽이 구해서 넘긴다(`brewPrefixes`).
 */
export function clangDocCandidates(env = process.env, prefixes = []) {
  const out = [];
  if (env.CLANG_DOC) out.push(env.CLANG_DOC);
  for (const p of prefixes) out.push(join(p, "bin", "clang-doc"));
  for (const dir of (env.PATH || "").split(delimiter)) {
    if (dir) out.push(join(dir, "clang-doc"));
  }
  return out;
}

// <include file="machine/comments.xml" path="//term[@id='brewPrefixes']"/>
// 꾸러미 관리자가 아는 LLVM 설치 자리를 묻는다.
// 쓰는 것: 없음 · 쓰이는 곳: clangDocPath
/** Homebrew 가 아는 LLVM keg 의 접두사들. brew 가 없으면 빈 배열이다. */
export function brewPrefixes(run = spawnSync) {
  const out = [];
  for (const formula of BREW_FORMULAE) {
    const r = run("brew", ["--prefix", formula], { encoding: "utf8" });
    if (r.status === 0 && r.stdout) out.push(r.stdout.trim());
  }
  return out;
}

// <include file="machine/comments.xml" path="//term[@id='clangDocPath']"/>
// 실제로 쓸 clang-doc 실행 파일 하나를 고른다.
// 쓰는 것: clangDocCandidates, brewPrefixes · 쓰이는 곳: runner/wiki/clang-doc.mjs
/** 실제로 쓸 실행 파일 하나. 없으면 `null` 이다 — 부르는 쪽이 단계를 건너뛴다. */
export function clangDocPath(env = process.env, exists = existsSync, prefixes = null) {
  for (const c of clangDocCandidates(env, prefixes ?? brewPrefixes())) {
    if (exists(c)) return c;
  }
  return null;
}

// <include file="machine/comments.xml" path="//term[@id='clangDocArgs']"/>
// clang-doc 에 넘길 명령줄 인자를 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * `clang-doc` 에 넘길 인자를 만든다. 순수 함수라 테스트가 쉽다.
 *
 * `--executor=all-TUs` 가 급소다 — 기본 실행기는 번역 단위 하나만 본다.
 * `--ignore-map-errors` 가 없으면 한 TU 라도 못 읽는 순간 전량이 죽는다.
 * `--source-root` 를 주어야 `Location.Filename` 이 저장소 상대 경로로 나온다 —
 * 그 값이 우리 레코드의 `where` 에 그대로 들어간다.
 */
export function clangDocArgs({ outDir, repo, compdbPath, flags = [] }) {
  return [
    "--executor=all-TUs", "--format=json",
    "--output", outDir,
    "--source-root", repo,
    "--ignore-map-errors",
    ...flags.flatMap((f) => ["--extra-arg", f]),
    compdbPath,
  ];
}

if (process.argv[1] && process.argv[1].endsWith("clang-doc.mjs")) {
  const found = clangDocPath();
  console.log(found ?? "clang-doc 을 못 찾았다. CLANG_DOC 환경변수로 알려 주거나 brew install llvm 하라.");
  process.exit(found ? 0 : 1);
}
