#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='prep.py']"/>
# 정적 계층을 돌려 위키가 읽을 재료를 만드는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
import sys
import json
import subprocess
from runner.wiki.paths import wikiPaths, collectorFor, collectorFromSelect
from runner.wiki.compdb import findCompdbs, mergeEntries, relativeFiles, clangUmlConfig, readAuthorConfig
from runner.wiki.clang_doc import clangDocPath, clangDocArgs
from tools.python import pythonPath

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Optional

def prepPlan(collector: Optional[str], hasCodegraph: bool, hasClangUmlConfig: bool, hasRoslynDump: bool, hasClangDoc: bool) -> dict[str, Any]:
    tail = ["facts", "render-modules"]
    if hasCodegraph:
        return {"steps": tail, "blocked": None}
    if collector == "clang-uml":
        if not hasClangUmlConfig:
            return {"steps": [], "blocked": "저장소 루트에 .clang-uml 설정이 없다."}
        doc = ["clang-doc"] if hasClangDoc else []
        return {"steps": ["clang-uml"] + doc + ["normalize"] + tail, "blocked": None}
    if collector == "griffe+pycalls":
        return {"steps": ["griffe", "pycalls", "normalize"] + tail, "blocked": None}
    if collector == "roslyn-dump":
        if not hasRoslynDump:
            return {
                "steps": [],
                "blocked": "out/codegraph-raw/roslyn-dump.json 이 없다. machine/roslyn-dump 를 dotnet 으로 먼저 돌려라.",
            }
        return {"steps": ["normalize"] + tail, "blocked": None}
    return {"steps": [], "blocked": "정적 수집기를 고르지 못했다. .csproj/.slnx 도 CMakeLists.txt 도 없다."}

def pyRoots(repo: str) -> list[str]:
    skip: set[str] = {"out", "node_modules", ".venv", "__pycache__", "docs", "test"}
    roots: list[str] = []
    try:
        entries = os.listdir(repo)
    except Exception:
        entries = []
    for name in entries:
        p = os.path.join(repo, name)
        if name.startswith(".") or name in skip:
            continue
        if os.path.isdir(p):
            try:
                if any(f.endswith(".py") for f in os.listdir(p)):
                    roots.append(name)
            except Exception:
                pass
    roots.sort()
    return roots if roots else ["."]

def run(cmd: str, args: list[str], cwd: Optional[str] = None) -> None:
    r = subprocess.run([cmd] + args, cwd=cwd)
    if r.returncode != 0:
        print(f"실패 — {cmd} {' '.join(args)}", file=sys.stderr)
        sys.exit(r.returncode if r.returncode else 1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법 — report-wiki prep <저장소 경로>", file=sys.stderr)
        sys.exit(1)
    
    repoArg = sys.argv[1]
    repo = os.path.abspath(os.path.expanduser(repoArg))
    if not os.path.exists(repo):
        print(f"에러 — 저장소가 없다: {repo}", file=sys.stderr)
        sys.exit(1)
        
    P = wikiPaths(repo)
    PY = pythonPath(ROOT, sys.platform, dict(os.environ))
    
    selectPath = os.path.join(P["raw"], "lang-select.json")
    fromSelect = None
    if os.path.exists(selectPath):
        with open(selectPath, "r", encoding="utf-8") as f:
            fromSelect = collectorFromSelect(f.read())
            
    collector = fromSelect if fromSelect else collectorFor(os.listdir(repo))
    CLANG_DOC = clangDocPath() if collector == "clang-uml" else None
    
    plan = prepPlan(
        collector=collector,
        hasCodegraph=os.path.exists(P["codegraph"]),
        hasClangUmlConfig=os.path.exists(os.path.join(repo, ".clang-uml")),
        hasRoslynDump=os.path.exists(os.path.join(P["raw"], "roslyn-dump.json")),
        hasClangDoc=bool(CLANG_DOC),
    )
    
    print(f"대상 {repo}")
    print(f"수집기 {collector} · 단계 {' -> '.join(plan['steps']) if plan['steps'] else '(없음)'}")
    
    if collector == "clang-uml" and not CLANG_DOC:
        print("알림 — clang-doc 을 못 찾아 자유 함수 층이 빈다. CLANG_DOC 환경변수로 알려 주거나 brew install llvm 하라.")
        
    if plan["blocked"]:
        print(f"막힘 — {plan['blocked']}", file=sys.stderr)
        sys.exit(1)
        
    os.makedirs(P["raw"], exist_ok=True)
    compdbDir = os.path.join(P["raw"], "compdb")
    docOutDir = os.path.join(P["raw"], "clangdoc")
    authorFlags = []
    
    for step in plan["steps"]:
        if step == "clang-uml":
            dbs = findCompdbs(repo)
            lists: list[list[dict[str, Any]]] = []
            for f in dbs:
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        lists.append(json.load(file))
                except Exception:
                    lists.append([])
            entries = mergeEntries(lists, repo)
            files = relativeFiles(entries, repo)
            os.makedirs(compdbDir, exist_ok=True)
            with open(os.path.join(compdbDir, "compile_commands.json"), "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=1)
            print(f"compile_commands {len(dbs)}개 합침 -> 번역 단위 {len(entries)}개")
            
            authorCfg = readAuthorConfig(os.path.join(repo, ".clang-uml"))
            authorFlags = authorCfg["flags"]
            paths = authorCfg["paths"]
            cfg = os.path.join(P["raw"], ".clang-uml.generated")
            
            cfg_content = clangUmlConfig(
                compdbDir=compdbDir, repo=repo, outDir=P["raw"], files=files, flags=authorFlags,
                paths=paths if paths else list(set(f.split("/")[0] for f in files))
            )
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(cfg_content)
            run("clang-uml", ["-c", cfg, "-g", "json"], repo)
            
        elif step == "clang-doc":
            os.makedirs(docOutDir, exist_ok=True)
            if CLANG_DOC:
                run(CLANG_DOC, clangDocArgs(
                    outDir=docOutDir, repo=repo, flags=authorFlags,
                    compdbPath=os.path.join(compdbDir, "compile_commands.json")
                ), repo)
            
        elif step == "griffe":
            run(PY, ["-m", "griffe", "dump"] + pyRoots(repo) + ["-o", os.path.join(P["raw"], "griffe.json"), "-s", repo], repo)
            
        elif step == "pycalls":
            run(PY, [os.path.join(ROOT, "machine", "pycalls.py")] + pyRoots(repo) + ["--repo", repo, "-o", os.path.join(P["raw"], "pycalls.json")])
            
        elif step == "normalize":
            arg = []
            if collector == "clang-uml":
                arg = ["--clang-uml", os.path.join(P["raw"], "full_class.json")]
            elif collector == "griffe+pycalls":
                arg = ["--griffe-dump", os.path.join(P["raw"], "griffe.json"), "--py-calls", os.path.join(P["raw"], "pycalls.json")]
            else:
                arg = ["--roslyn-dump", os.path.join(P["raw"], "roslyn-dump.json")]
            
            if "clang-doc" in plan["steps"]:
                arg.extend(["--clang-doc", docOutDir])
                
            run(PY, [os.path.join(ROOT, "machine", "normalize.py")] + arg + ["--repo", repo, "-o", P["codegraph"]])
            
        elif step == "facts":
            detail = os.path.join(P["raw"], "roslyn-dump.json")
            extra = ["--detail", detail] if os.path.exists(detail) else []
            run(PY, [os.path.join(ROOT, "machine", "facts.py"), P["codegraph"], "--repo", repo] + extra + ["-o", P["raw"]])
            
        elif step == "render-modules":
            run(PY, [os.path.join(ROOT, "viz", "render_modules.py"), P["codegraph"], "-o", os.path.join(P["raw"], "modules")])

    print("\n준비 끝. 다음은 사람(스킬)의 차례다:")
    print(f"  재료  {P['raw']}/facts/ · {P['raw']}/ranking.json · {P['codegraph']}")
    print(f"  산문  {P['wiki']}/  <- deep-wiki 스킬이 여기에 쓴다 (추적 경로)")
