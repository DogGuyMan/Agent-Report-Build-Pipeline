#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='gen_readme.py']"/>
# 소스에서 디렉토리별 README.md 를 생성하는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""gen_readme.py — 소스에서 디렉토리별 README.md 를 생성한다.

    python3 tools/gen_readme.py machine runner viz tools        # 쓴다
    python3 tools/gen_readme.py machine runner viz tools --check  # 낡았으면 exit 1

모듈 한 줄은 모듈 독스트링 첫 줄, 심볼 한 줄은 그 심볼 독스트링 첫 줄에서 온다.
시그니처는 `machine/pycalls.py` 의 `signature_of` 를 그대로 쓴다 — 두 곳에서 만들면 어긋난다.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine"))
from pycalls import signature_of  # noqa: E402

BANNER = ("> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —\n"
          "> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py "
          "machine runner viz tools`\n")

# 디렉토리 한 줄. 여기만 사람이 쓴다 — 나머지는 전부 소스에서 온다.
DIR_ROLE = {
    "machine": "정적 수집 · 인용 검증 · 측정. 산문을 쓰지 않고 판정하지 않는다.",
    "runner": "세 mode 실행기. 단계마다 벽시계 시간과 토큰을 잰다.",
    "viz": "코드 지도와 위키를 사람이 보는 그림으로 만든다.",
    "tools": "저장소 관리용 잡도구.",
}


# <include file="machine/comments.xml" path="//term[@id='tools.gen_readme.first_line']"/>
# 파이썬 코드의 독스트링(설명 문구) 중 첫 줄만 뽑아내는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: tools.gen_readme.render_dir
# 독스트링 첫 줄만 꺼낸다. 없으면 빈 문자열.
# 쓰는 것: 없음 · 쓰이는 곳: render_dir
def first_line(node: ast.AST) -> str:
    if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ""
    doc = ast.get_docstring(node)
    if not doc:
        return ""
    line = doc.splitlines()[0].strip()
    # 모듈 독스트링은 "파일이름.py — 설명" 꼴이라 앞머리를 뗀다.
    for sep in (" — ", " - "):
        if isinstance(node, ast.Module) and sep in line and line.split(sep)[0].endswith(".py"):
            return line.split(sep, 1)[1]
    return line


# <include file="machine/comments.xml" path="//term[@id='tools.gen_readme.cell']"/>
# 마크다운 표 칸 안에 안전하게 넣을 수 있도록 글자를 다듬는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: tools.gen_readme.render_dir
# 마크다운 표 칸에 넣을 수 있게 파이프를 막는다.
# 쓰는 것: 없음 · 쓰이는 곳: render_dir
def cell(text: str) -> str:
    return text.replace("|", "\\|")


# <include file="machine/comments.xml" path="//term[@id='tools.gen_readme.render_dir']"/>
# 디렉토리 하나 안의 파이썬 파일들을 훑어서 그 디렉토리의 README.md 에 들어갈 글 내용을 만드는 함수다.
# 쓰는 것: tools.gen_readme.first_line, tools.gen_readme.cell, machine.pycalls.signature_of · 쓰이는 곳: tools.gen_readme.main, tools.test_gen_readme.test_pipe_in_signature_is_escaped, tools.test_gen_readme.test_signature_comes_from_pycalls_not_a_copy
# 디렉토리 하나의 README 본문을 만든다.
# 쓰는 것: first_line, cell, signature_of · 쓰이는 곳: gen_readme.main
def render_dir(repo: str, d: str) -> str:
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(repo, d)):
        dirnames[:] = [x for x in dirnames if x != "__pycache__"]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(os.path.relpath(os.path.join(dirpath, fn), repo))
    files.sort()

    trees: dict[str, ast.Module] = {}
    for rel in files:
        with open(os.path.join(repo, rel), encoding="utf-8") as fh:
            trees[rel] = ast.parse(fh.read())

    out = [f"# `{d}/` — {DIR_ROLE.get(d, '')}", "", BANNER, "## 파일", "",
           "| 파일 | 하는 일 |", "|---|---|"]
    for rel in files:
        out.append(f"| [`{os.path.basename(rel)}`]({os.path.basename(rel)}) "
                   f"| {cell(first_line(trees[rel])) or '—'} |")
    out.append("")

    for rel in files:
        tree = trees[rel]
        rows: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                rows.append(f"| `{node.name}` | `{cell(signature_of(node))}` "
                            f"| {cell(first_line(node))} |")
            elif isinstance(node, ast.ClassDef):
                rows.append(f"| **`{node.name}`** | *class* | {cell(first_line(node))} |")
                for m in node.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        rows.append(f"| `{node.name}.{m.name}` | `{cell(signature_of(m))}` "
                                    f"| {cell(first_line(m))} |")
        if not rows:
            continue
        out += ["---", "", f"## `{os.path.basename(rel)}`", "",
                first_line(tree), "", "| 심볼 | 시그니처 | 하는 일 |", "|---|---|---|"]
        out += rows
        out.append("")
    return "\n".join(out) + "\n"


# <include file="machine/comments.xml" path="//term[@id='tools.gen_readme.main']"/>
# gen_readme 도구를 터미널에서 실행했을 때 맨 처음 불리는 함수다.
# 쓰는 것: tools.gen_readme.render_dir · 쓰이는 곳: 없음
# gen_readme 도구의 명령줄 진입점.
# 쓰는 것: render_dir · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--check", action="store_true", help="쓰지 않고 낡았는지만 본다")
    a = ap.parse_args()

    stale: list[str] = []
    for d in a.dirs:
        body = render_dir(a.repo, d)
        path = os.path.join(a.repo, d, "README.md")
        old = ""
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
        if a.check:
            if old != body:
                stale.append(f"{d}/README.md")
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"{path} — {body.count(chr(10))}줄")

    if a.check:
        if stale:
            print("낡았다: " + ", ".join(stale) + "\n  갱신: "
                  "python3 tools/gen_readme.py " + " ".join(a.dirs), file=sys.stderr)
            return 1
        print(f"README {len(a.dirs)}개 — 소스와 일치")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
