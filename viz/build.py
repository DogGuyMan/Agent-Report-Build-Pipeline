# <include file="machine/comments.xml" path="//term[@id='viz/build.py']"/>
# 보고서 원고를 하나짜리 HTML 파일로 굽는 스크립트.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
import sys
import subprocess
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from viz.wrap_terms import wrapTerms
from viz.link_paths import makeResolver, buildIndex, linkPaths

def currentBuilderVersion() -> str:
    try:
        res = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], cwd=ROOT, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "untagged"

def main() -> None:
    cwd = os.getcwd()
    tmp_mjs = os.path.join(ROOT, ".tmp-report.mjs")
    
    # 1. Run esbuild
    esbuild_res = subprocess.run([
        "npx", "esbuild",
        "--bundle", "--format=esm", "--platform=node", "--target=node22",
        "--jsx=automatic",
        "--external:react", "--external:react-dom", "--external:react/jsx-runtime", "--external:react-dom/server",
        f"--alias:report-builder={os.path.join(ROOT, 'viz/src/index.ts')}",
        f"--alias:report-builder/types={os.path.join(ROOT, 'viz/src/types.ts')}",
        # report.tsx 가 import 하는 자리라 esbuild 가 번들 시점에 읽는다.
        # 파이썬으로 옮기면 esbuild 가 파싱하지 못한다 — 여기는 JavaScript 로 남는다.
        f"--alias:report-builder/svg={os.path.join(ROOT, 'viz/svg.mjs')}",
        f"--outfile={tmp_mjs}",
    ], cwd=cwd, input='export { default, data } from "./report.tsx";\nexport { defineTerms } from "report-builder";', text=True)
    
    if esbuild_res.returncode != 0:
        print("esbuild failed", file=sys.stderr)
        sys.exit(esbuild_res.returncode)
        
    # 2. Run Node to render to static markup
    render_script = f"""
    import * as mod from 'file://{tmp_mjs}';
    import {{ renderToStaticMarkup }} from 'react-dom/server';
    import {{ createElement }} from 'react';
    
    const html = renderToStaticMarkup(mod.default());
    let refs = {{}};
    if (Array.isArray(mod.data.terms) && mod.data.terms.length > 0 && typeof mod.defineTerms === 'function') {{
        const T = mod.defineTerms(mod.data.terms);
        for (const t of mod.data.terms) {{
            refs[t.id] = renderToStaticMarkup(createElement(T, {{ id: t.id }}, t.id));
        }}
    }}
    console.log(JSON.stringify({{ body: html, data: mod.data, refs }}));
    """
    tmp_render = os.path.join(ROOT, ".tmp-render.mjs")
    with open(tmp_render, "w", encoding="utf-8") as f:
        f.write(render_script)
        
    try:
        # 렌더 프로세스의 cwd 는 **보고서 폴더**여야 한다 — report.tsx 가 before.svg 같은
        # 곁 파일을 상대 경로로 읽는다. 임시 파일 자체는 ROOT 안에 있어 react 는 그대로 풀린다.
        res = subprocess.run(["node", tmp_render], cwd=cwd, capture_output=True, text=True)
        if res.returncode != 0:
            print("Render failed:", res.stderr, file=sys.stderr)
            sys.exit(res.returncode)
        rendered = json.loads(res.stdout)
    finally:
        if os.path.exists(tmp_mjs): os.remove(tmp_mjs)
        if os.path.exists(tmp_render): os.remove(tmp_render)
        
    body = rendered["body"]
    data = rendered["data"]
    refs = rendered["refs"]
    
    # 3. wrapTerms
    if data.get("terms") and refs:
        before = body.count('class="term-ref"')
        body = wrapTerms(body, refs)
        after = body.count('class="term-ref"')
        print(f"용어 자동 참조 — term-ref {before} → {after} (용어 {len(data['terms'])}개)")
        
    # 4. linkPaths
    repoRoot = cwd
    try:
        res = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if res.returncode == 0:
            repoRoot = res.stdout.strip()
    except Exception:
        pass
        
    bases = [cwd, os.path.dirname(cwd)]
    if isinstance(data.get("linkRoots"), list):
        bases.extend(data["linkRoots"])
    bases.extend([repoRoot, os.path.join(repoRoot, "out/codegraph-raw")])
    
    missed: set[str] = set()

    def on_miss(p: str) -> None:
        missed.add(p)
    resolve = makeResolver(bases, repoRoot, buildIndex(repoRoot))
    body = linkPaths(body, resolve, on_miss)
    
    n = body.count('class="path-link"')
    miss_msg = f" (못 찾은 경로 {len(missed)}종: {', '.join(list(missed)[:6])}{' …' if len(missed) > 6 else ''})" if missed else ""
    print(f"경로 링크 — {n}개{miss_msg}")
    
    # 5. Check version
    version = currentBuilderVersion()
    if data.get("builderVersion") != version:
        print(f"경고 — data.ts 의 builderVersion \"{data.get('builderVersion')}\" 이 현재 \"{version}\" 과 다르다. 빌드는 계속한다.")
        
    # 6. Read CSS
    with open(os.path.join(ROOT, "viz/src/theme.css"), "r", encoding="utf-8") as f:
        css = f.read()
        
    # 7. Term Graph runtime
    runtime = ""
    if data.get("terms"):
        r = subprocess.run([
            "npx", "esbuild", os.path.join(ROOT, "viz/src/runtime/term-graph.ts"),
            "--bundle", "--minify", "--format=iife", "--platform=browser", "--target=es2020"
        ], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            code = r.stdout.replace("</script", "<\\/script")
            runtime = f"<script>{code}</script>"
            print(f"용어 그래프 런타임 {len(code)} 자 삽입 (용어 {len(data['terms'])}개)")
            
    # 8. HTML output
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{data.get("specName", "")} — 설계 검토</title>
<style>
{css}
</style>
</head>
<body>
{body}
{runtime}
</body>
</html>
"""
    out_dir = os.path.join(cwd, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "report.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    scripts = html.count("<script")
    print(f"out/report.html — {len(html)} 자, <script> {scripts}개")
    if scripts > 1:
        print(f"불변식 위반 — <script> 가 {scripts}개다. 허용은 pan/zoom 하나까지.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
