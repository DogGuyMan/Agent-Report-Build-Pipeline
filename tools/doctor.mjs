// <include file="machine/comments.xml" path="//term[@id='tools/doctor.mjs']"/>
// 이 컴퓨터에서 무엇이 되고 무엇이 안 되는지 한 화면으로 말하는 파일.
// 쓰는 것: pythonPath · 쓰이는 곳: 없음
// `npm run doctor` — 이 컴퓨터에서 무엇이 되고 무엇이 안 되는지 한 화면으로 말한다.
//
// **왜 있나.** 이 저장소는 Node 와 파이썬과 바깥 명령 여럿에 걸쳐 있다. 다른 컴퓨터로 옮기면
// 무엇이 빠졌는지가 **파이프라인 한복판에서 처음 드러난다.** 그때는 이미 절반쯤 진행한 뒤라
// 원인을 되짚기 어렵다. 이 명령은 그 실패를 앞으로 당긴다.
//
// 필수가 하나라도 없으면 exit 1. 선택은 없어도 통과시킨다 — 쓰는 갈래가 정해져 있어서다
// (C++ 만 clang-uml, C# 만 dotnet).
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { pythonPath } from "./python.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

// <include file="machine/comments.xml" path="//term[@id='probe']"/>
// 바깥 명령 하나를 돌려 첫 줄을 얻는다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** 명령 하나를 돌려 첫 줄을 돌려준다. 못 돌리면 null. */
export function probe(cmd, args) {
  try {
    const r = spawnSync(cmd, args, { encoding: "utf8", timeout: 20000 });
    if (r.error || r.status !== 0) return null;
    return `${r.stdout ?? ""}${r.stderr ?? ""}`.trim().split("\n")[0].slice(0, 70);
  } catch {
    return null;
  }
}

/** 결과 줄 하나를 글자로. 필수인데 없으면 ✗, 선택이면 -. */
export function line(name, version, required) {
  const mark = version ? "OK " : required ? "없음" : "선택";
  const pad = name.padEnd(22);
  return `  ${mark}  ${pad}${version ?? "(찾지 못했다)"}`;
}

if (process.argv[1] && process.argv[1].endsWith("doctor.mjs")) {
  const py = pythonPath(ROOT);
  const pyMods = py
    ? probe(py, ["-c",
        "import importlib.util as u;" +
        "m=[n for n in ('networkx','numpy','scipy','pytest') if u.find_spec(n) is None];" +
        "print('전부 있다' if not m else '빠짐: '+', '.join(m))"])
    : null;

  const checks = [
    ["필수", "Node", probe(process.execPath, ["--version"]), true],
    ["필수", "npm 의존성", existsSync(join(ROOT, "node_modules", "esbuild")) ? "node_modules 설치됨" : null, true],
    ["필수", "git", probe("git", ["--version"]), true],
    ["필수", "python", probe(py, ["--version"]), true],
    ["필수", "python 패키지", pyMods && pyMods.startsWith("전부") ? pyMods : null, true],
    ["필수", "Graphviz dot", probe("dot", ["-V"]), true],
    ["선택", "clang-uml (C++)", probe("clang-uml", ["--version"]), false],
    ["선택", "dotnet (C#)", probe("dotnet", ["--version"]), false],
    ["선택", "clangd", probe("clangd", ["--version"]), false],
    ["선택", "mmdc (Mermaid)", probe("npx", ["--no-install", "mmdc", "--version"]), false],
  ];

  console.log(`저장소 ${ROOT}`);
  console.log(`파이썬 ${py}\n`);
  let group = "";
  for (const [g, name, ver, required] of checks) {
    if (g !== group) { console.log(`── ${g} ──`); group = g; }
    console.log(line(name, ver, required));
  }

  console.log("\n── 골든 저장소 환경변수 (없으면 해당 테스트를 건너뛴다) ──");
  for (const v of ["GRAPHICS_REPO", "CSHARP_REPO", "CPP_REPO"]) {
    const val = process.env[v];
    console.log(`  ${val && existsSync(val) ? "OK " : "없음"}  ${v.padEnd(22)}${val ?? "(설정 안 됨)"}`);
  }

  const missing = checks.filter(([, , ver, required]) => required && !ver).map(([, name]) => name);
  if (missing.length) {
    console.error(`\n필수 ${missing.length}개가 없다: ${missing.join(", ")}`);
    console.error("설치 방법은 README.md 를 보라.");
    process.exit(1);
  }
  console.log("\n필수 항목이 전부 있다.");
}
