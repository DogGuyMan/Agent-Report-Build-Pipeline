#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='runner/wiki/check.py']"/>
# 위키 산문의 인용을 검증하는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
import sys
import subprocess
from typing import Any, cast

# 이 파일은 <ROOT>/runner/wiki/ 에 있다. 스크립트로 띄우면 sys.path[0] 이 그 폴더라
# `runner` 도 `tools` 도 보이지 않는다 — 패키지 import 보다 먼저 뿌리를 넣는다.
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from runner.wiki.paths import wikiPaths as _wikiPaths  # noqa: E402
from tools.python import pythonPath as _pythonPath  # noqa: E402

wikiPaths = cast(Any, _wikiPaths)
pythonPath = cast(Any, _pythonPath)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def checkArgs(repo: str, codegraph: str, detail: str | None, docs: list[str]) -> list[str]:
    out = ["--repo", repo, "--codegraph", codegraph]
    if detail:
        out.extend(["--detail", detail])
    out.extend(docs)
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법 — report-wiki check <저장소 경로>", file=sys.stderr)
        sys.exit(1)
        
    repoArg = sys.argv[1]
    repo = os.path.abspath(os.path.expanduser(repoArg))
    
    P: dict[str, str] = wikiPaths(repo)
    
    if not os.path.exists(P["codegraph"]):
        print(f"에러 — codegraph.json 이 없다: {P['codegraph']}. report-wiki prep 을 먼저 돌려라.", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(P["wiki"]):
        print(f"에러 — 산문이 없다: {P['wiki']}", file=sys.stderr)
        sys.exit(1)
        
    docs = [os.path.join(P["wiki"], f) for f in os.listdir(P["wiki"]) if f.endswith(".md")]
    if not docs:
        print(f"에러 — {P['wiki']} 에 마크다운이 없다", file=sys.stderr)
        sys.exit(1)
        
    detailPath = os.path.join(P["raw"], "roslyn-dump.json")
    args = checkArgs(
        repo=repo,
        codegraph=P["codegraph"],
        detail=detailPath if os.path.exists(detailPath) else None,
        docs=docs
    )
    
    r = subprocess.run([pythonPath(ROOT, sys.platform, cast(Any, os.environ)), os.path.join(ROOT, "machine", "verify_citations.py")] + args)
    sys.exit(r.returncode if r.returncode else 1)
