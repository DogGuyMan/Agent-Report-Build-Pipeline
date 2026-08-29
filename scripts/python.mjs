// <include file="docs/codegraph/comments.xml" path="//term[@id='scripts/python.mjs']"/>
// scripts/python.mjs
// 파이썬 해석기를 **기계에 상관없이** 찾는다.
//
// **왜 필요한가.** 이 저장소의 파이프라인은 절반이 파이썬이다(`codegraph/*.py`).
// 그런데 `.venv/` 는 git 에서 제외되므로 다른 컴퓨터에는 없을 수도 있고, 있어도
// 자리가 다르다 — POSIX 는 `.venv/bin/python`, 윈도우는 `.venv/Scripts/python.exe` 다.
// 경로를 코드에 박으면 그 기계에서만 돈다.
//
// 찾는 순서 — 환경변수 `REPORT_PYTHON` → 저장소 안 `.venv` → PATH 의 `python3` → `python`.
import { existsSync } from "node:fs";
import { join } from "node:path";

/**
 * 후보 목록을 순서대로 만든다. 파일 시스템을 보지 않는 순수 함수라 테스트가 쉽다.
 * PATH 로 넘길 이름(`python3`)도 후보에 섞이므로, 존재 검사는 부르는 쪽이 한다.
 */
// <include file="docs/codegraph/comments.xml" path="//term[@id='pythonCandidates']"/>
export function pythonCandidates(root, platform = process.platform, env = process.env) {
  const out = [];
  if (env.REPORT_PYTHON) out.push(env.REPORT_PYTHON);
  if (platform === "win32") {
    out.push(join(root, ".venv", "Scripts", "python.exe"));
    out.push(join(root, ".venv", "Scripts", "python"));
  } else {
    out.push(join(root, ".venv", "bin", "python3"));
    out.push(join(root, ".venv", "bin", "python"));
  }
  out.push("python3", "python");
  return out;
}

/**
 * 실제로 쓸 해석기 하나를 고른다.
 * 절대경로 후보는 존재할 때만, 이름 후보(`python3`)는 그대로 돌려준다 — PATH 가 푼다.
 */
// <include file="docs/codegraph/comments.xml" path="//term[@id='pythonPath']"/>
export function pythonPath(root, platform = process.platform, env = process.env) {
  for (const c of pythonCandidates(root, platform, env)) {
    if (c.includes("/") || c.includes("\\")) {
      if (existsSync(c)) return c;
    } else {
      return c;
    }
  }
  return "python3";
}
