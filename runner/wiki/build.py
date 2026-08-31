#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='runner/wiki/build.py']"/>
# 산문을 사전 렌더 그림으로 바꾸고 정적 사이트를 짓는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
import sys
import shutil
import json
import subprocess
from typing import Any, cast

from runner.wiki.paths import wikiPaths as _wikiPaths
from tools.python import pythonPath as _pythonPath

wikiPaths = cast(Any, _wikiPaths)
pythonPath = cast(Any, _pythonPath)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def sidebarFrom(files: list[str]) -> list[dict[str, str]]:
    return sorted([{"text": f[:-3], "link": f"/{f[:-3]}"} for f in files if f.endswith(".md") and f != "index.md"], key=lambda x: x["text"])

def vitepressConfig(repoName: str, sidebar: list[dict[str, str]], outDir: str) -> str:
    items = [f'      {{ text: {json.dumps(s["text"], ensure_ascii=False)}, link: {json.dumps(s["link"], ensure_ascii=False)} }}' for s in sidebar]
    items_str = ",\n".join(items)
    return f"""// report-wiki build 가 생성한다. 손으로 고치지 말 것 — 다음 빌드에서 덮어쓴다.
// defineConfig 를 쓰지 않는 이유는 runner/wiki/build.mjs 의 주석을 보라.
export default ({{
  title: {json.dumps(repoName + ' 코드베이스 위키', ensure_ascii=False)},
  description: "codegraph 정적 계층 + deep-wiki 산문",
  srcDir: ".",
  outDir: {json.dumps(outDir, ensure_ascii=False)},
  themeConfig: {{
    sidebar: [
{items_str}
    ],
  }},
}});
"""

def run(cmd: str, args: list[str], cwd: str | None = None) -> None:
    r = subprocess.run([cmd] + args, cwd=cwd)
    if r.returncode != 0:
        print(f"실패 — {cmd} {' '.join(args)}", file=sys.stderr)
        sys.exit(r.returncode if r.returncode else 1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법 — report-wiki build <저장소 경로>", file=sys.stderr)
        sys.exit(1)
        
    repoArg = sys.argv[1]
    repo = os.path.abspath(os.path.expanduser(repoArg))
    
    P: dict[str, str] = wikiPaths(repo)
    
    if not os.path.exists(P["wiki"]):
        print(f"에러 — 산문이 없다: {P['wiki']}", file=sys.stderr)
        print("  deep-wiki 스킬이 먼저 여기에 마크다운을 써야 한다.", file=sys.stderr)
        sys.exit(1)
        
    shutil.rmtree(P["built"], ignore_errors=True)
    os.makedirs(P["built"], exist_ok=True)
    
    svgDir = ["--svg-dir", os.path.join(P["raw"], "diagrams")] if os.path.exists(os.path.join(P["raw"], "diagrams")) else []
    run(pythonPath(ROOT, sys.platform, cast(Any, os.environ)), [os.path.join(ROOT, "viz", "demermaid.py"), P["wiki"], "--out", P["built"]] + svgDir)
    
    stage = os.path.join(ROOT, ".tmp", "wiki", os.path.basename(repo))
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage, exist_ok=True)
    
    shutil.copytree(P["built"], stage, dirs_exist_ok=True)
    
    sidebar = sidebarFrom(os.listdir(stage))
    os.makedirs(os.path.join(stage, ".vitepress"), exist_ok=True)
    
    with open(os.path.join(stage, ".vitepress", "config.mts"), "w", encoding="utf-8") as f:
        f.write(vitepressConfig(os.path.basename(repo), sidebar, P["site"]))
        
    run(os.path.join(ROOT, "node_modules", ".bin", "vitepress"), ["build", stage], cwd=ROOT)
    
    print(f"\n사이트 {P['site']}")
    print(f"  페이지 {len(sidebar)}개 · 열기: open {os.path.join(P['site'], 'index.html')}")
