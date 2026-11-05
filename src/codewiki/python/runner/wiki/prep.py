#!/usr/bin/env python3
import argparse
import hashlib
import os
import sys
import json
import subprocess

# 이 파일은 <ROOT>/src/codewiki/python/runner/wiki/ 에 있다. 스크립트로 띄우면 sys.path[0] 이 그 폴더라
# `codewiki` 도 `common` 도 보이지 않는다 — 패키지 import 보다 먼저 `src/` 를 넣는다.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if os.path.join(ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "src"))

from codewiki.python.runner.wiki.paths import wikiPaths, collectorFor, collectorFromSelect  # noqa: E402
from codewiki.python.runner.wiki.compdb import findCompdbs, mergeEntries, relativeFiles, clangUmlConfig, readAuthorConfig  # noqa: E402
from codewiki.python.runner.wiki.clang_doc import clangDocPath, clangDocArgs  # noqa: E402
from common.python import pythonPath  # noqa: E402

from typing import Any, Optional, cast

# 수집 결과를 바꾸는 이 저장소의 코드. normalize.py 가 평평하게 import 하는 모듈은 전부 여기 있어야 한다
# (test_prep_fingerprint.py 가 고정한다).
COLLECT_CODE = (
    "src/codewiki/python/machine/normalize.py",
    "src/codewiki/python/machine/codegraph_types.py",
    "src/codewiki/python/machine/clang_doc.py",
    "src/codewiki/python/machine/pycalls.py",
    "src/codewiki/python/runner/wiki/prep.py",
)


def tool_versions(collector: Optional[str], py: str, raw: str, clang_doc: Optional[str]) -> dict[str, str]:
    """바깥 수집기의 판. `--version` 첫 줄을 쓰고 못 얻으면 `?` 다. roslyn-dump 는 prep 밖에서 돌므로 산출물의 내용 해시를 쓴다."""
    def first_line(argv: list[str]) -> str:
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            return "?"
        out = (r.stdout or r.stderr).strip().splitlines()
        return out[0] if r.returncode == 0 and out else "?"
    got: dict[str, str] = {}
    if collector == "griffe+pycalls":
        got["griffe"] = first_line([py, "-m", "griffe", "--version"])
    elif collector == "clang-uml":
        got["clang-uml"] = first_line(["clang-uml", "--version"])
        if clang_doc:
            got["clang-doc"] = first_line([clang_doc, "--version"])
    elif collector == "roslyn-dump":
        dump = os.path.join(raw, "roslyn-dump.json")
        if os.path.exists(dump):
            with open(dump, "rb") as f:
                got["roslyn-dump.json"] = hashlib.sha256(f.read()).hexdigest()
        else:
            got["roslyn-dump.json"] = "?"
    return got


def collect_fingerprint(root: str, versions: dict[str, str]) -> str:
    """수집 코드의 내용과 바깥 수집기 판을 합친 sha256. 커밋 해시가 아니라 내용이라 커밋 전 수정도 잡는다."""
    h = hashlib.sha256()
    for rel in COLLECT_CODE:
        with open(os.path.join(root, rel), "rb") as f:
            h.update(f"{rel}\0".encode())
            h.update(hashlib.sha256(f.read()).digest())
    for name in sorted(versions):
        h.update(f"{name}={versions[name]}\0".encode())
    return h.hexdigest()


def recorded_fingerprint(path: str, codegraph: str) -> Optional[str]:
    """기록된 지문. 기록이 없거나 깨졌거나 지금 지도가 기록할 때의 지도가 아니면 `None` 이다 — 셋 다 다시 수집하라는 뜻이다."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = cast(object, json.load(f))
        with open(codegraph, "rb") as f:
            now = hashlib.sha256(f.read()).hexdigest()
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    d = cast(dict[str, object], raw)
    fp, sha = d.get("fingerprint"), d.get("codegraph_sha256")
    return fp if isinstance(fp, str) and sha == now else None


def needs_collect(has_codegraph: bool, verdicts: dict[str, list[str]] | None,
                  force: bool = False, tool_changed: bool = False) -> bool:
    """수집기를 다시 돌릴 것인가.

    `force` 거나 수집 코드 · 수집기 판이 지도를 만들 때와 다르면(`tool_changed`) 무조건. diff 가 없으면 지도의 존재만 본다. diff 가 있으면
    `재읽기 · 위치만 · 삭제됨` 중 하나라도 있을 때 다시 수집한다 — 지도가 낡은 채 남는 것을 막는다.
    """
    if force or tool_changed or not has_codegraph:
        return True
    if verdicts is None:
        return False
    return bool(verdicts.get("재읽기") or verdicts.get("위치만") or verdicts.get("삭제됨"))

def prepPlan(collector: Optional[str], hasCodegraph: bool, hasClangUmlConfig: bool, hasRoslynDump: bool, hasClangDoc: bool,
             verdicts: dict[str, list[str]] | None = None, force: bool = False,
             toolChanged: bool = False) -> dict[str, Any]:
    tail = ["facts", "render-modules"]
    if not needs_collect(hasCodegraph, verdicts, force, toolChanged):
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
                "blocked": "out/codegraph-raw/roslyn-dump.json 이 없다. src/codewiki/csharp/roslyn-dump 를 dotnet 으로 먼저 돌려라.",
            }
        return {"steps": ["normalize"] + tail, "blocked": None}
    return {"steps": [], "blocked": "정적 수집기를 고르지 못했다. .csproj/.slnx 도 CMakeLists.txt 도 없다."}

def pyRoots(repo: str) -> list[str]:
    skip: set[str] = {"out", "node_modules", ".venv", "__pycache__", "docs", "test"}
    roots: list[str] = []
    try:
        entries = os.listdir(repo) + [os.path.join("src", e) for e in os.listdir(os.path.join(repo, "src"))] if os.path.isdir(os.path.join(repo, "src")) else os.listdir(repo)
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
    ap = argparse.ArgumentParser(description="정적 수집 → 코드 지도 → 사실 파일 · 모듈 그림")
    ap.add_argument("repo", help="저장소 경로")
    ap.add_argument("--diff", default=None, help="changes.json. 있으면 그 판정으로 재수집 여부를 정한다")
    ap.add_argument("--force", action="store_true", help="지도가 있어도 무조건 다시 수집한다 (전량)")
    a = ap.parse_args()
    repoArg = cast(str, a.repo)
    diffPath = cast(Optional[str], a.diff)
    force = bool(a.force)
    verdicts: dict[str, list[str]] | None = None
    if diffPath:
        with open(diffPath, encoding="utf-8") as f:
            raw = cast(object, json.load(f))
        top = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
        v = top.get("verdicts")
        if isinstance(v, dict):
            verdicts = {}
            for k, val in cast(dict[str, object], v).items():
                if isinstance(val, list):
                    verdicts[k] = [x for x in cast(list[object], val) if isinstance(x, str)]
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
    fingerprint = collect_fingerprint(ROOT, tool_versions(collector, PY, P["raw"], CLANG_DOC))
    recorded = recorded_fingerprint(P["fingerprint"], P["codegraph"])

    plan = prepPlan(
        collector=collector,
        hasCodegraph=os.path.exists(P["codegraph"]),
        hasClangUmlConfig=os.path.exists(os.path.join(repo, ".clang-uml")),
        hasRoslynDump=os.path.exists(os.path.join(P["raw"], "roslyn-dump.json")),
        hasClangDoc=bool(CLANG_DOC),
        verdicts=verdicts,
        force=force,
        toolChanged=recorded != fingerprint,
    )
    
    print(f"대상 {repo}")
    print(f"수집기 {collector} · 단계 {' -> '.join(plan['steps']) if plan['steps'] else '(없음)'}")
    
    if collector == "clang-uml" and not CLANG_DOC:
        print("알림 — clang-doc 을 못 찾아 자유 함수 층이 빈다. CLANG_DOC 환경변수로 알려 주거나 brew install llvm 하라.")
        
    # 다시 수집하기로 정했으면 막혔든 아니든 옛 지도와 옛 지문부터 지운다. 수집이 실패해도 낡은 지도가 뒤 단계로 가지 않는다.
    if plan["blocked"] is not None or "normalize" in plan["steps"]:
        for stale in (P["codegraph"], P["fingerprint"]):
            if os.path.exists(stale):
                os.remove(stale)

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
            run(PY, ["-m", "griffe", "dump"] + [r.removeprefix("src/") for r in pyRoots(repo)] + ["-o", os.path.join(P["raw"], "griffe.json"), "-s", repo, "-s", os.path.join(repo, "src")], repo)
            
        elif step == "pycalls":
            run(PY, [os.path.join(ROOT, "src", "codewiki", "python", "machine", "pycalls.py")] + pyRoots(repo) + ["--repo", repo, "-o", os.path.join(P["raw"], "pycalls.json")])
            
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
                
            run(PY, [os.path.join(ROOT, "src", "codewiki", "python", "machine", "normalize.py")] + arg + ["--repo", repo, "-o", P["codegraph"]])
            # 끊겨 깨진 지문 파일은 recorded_fingerprint 가 None 으로 읽어 다음에 다시 수집한다.
            with open(P["codegraph"], "rb") as g:
                sha = hashlib.sha256(g.read()).hexdigest()
            with open(P["fingerprint"], "w", encoding="utf-8") as f:
                json.dump({"fingerprint": fingerprint, "codegraph_sha256": sha}, f, indent=1)
            
        elif step == "facts":
            detail = os.path.join(P["raw"], "roslyn-dump.json")
            extra = ["--detail", detail] if os.path.exists(detail) else []
            run(PY, [os.path.join(ROOT, "src", "codewiki", "python", "machine", "facts.py"), P["codegraph"], "--repo", repo] + extra + ["-o", P["raw"]])
            
        elif step == "render-modules":
            run(PY, [os.path.join(ROOT, "src", "codewiki", "python", "viz", "render_modules.py"), P["codegraph"], "-o", os.path.join(P["raw"], "modules")])

    print("\n준비 끝. 다음은 사람(스킬)의 차례다:")
    print(f"  재료  {P['raw']}/facts/ · {P['raw']}/ranking.json · {P['codegraph']}")
    print(f"  산문  {P['wiki']}/  <- deep-wiki 스킬이 여기에 쓴다 (추적 경로)")
