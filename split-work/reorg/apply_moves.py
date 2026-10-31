#!/usr/bin/env python3
"""pathmap.tsv 를 git mv / git rm 으로 적용하고, 패키지 표식을 만들고, 빈 디렉토리를 지운다."""
import os
import shutil
import subprocess
import sys

from reorg_lib import ROOT, TSV

INIT = ["codewiki/__init__.py", "codewiki/python/__init__.py", "codewiki/python/runner/__init__.py", "codewiki/python/viz/__init__.py",
        "term/__init__.py", "term/python/__init__.py", "term/python/runner/__init__.py",
        "spec/__init__.py", "spec/python/__init__.py", "spec/python/runner/__init__.py", "common/__init__.py"]
OLD_ROOTS = ["runner", "machine", "viz", "config", "evals", "resources", "reports", "research_notes", "docs/prompt"]


def git(*args: str) -> None:
    subprocess.run(["git", "-c", "core.quotepath=off", *args], check=True, cwd=ROOT)


def main() -> int:
    with open(TSV, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f if l.strip()]
    for old, new in rows:
        if new == "DELETE":
            if os.path.exists(os.path.join(ROOT, old)):
                git("rm", "-q", old)
        elif new != old:
            os.makedirs(os.path.dirname(os.path.join(ROOT, new)), exist_ok=True)
            git("mv", old, new)
    for rel in INIT:
        p = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            open(p, "w").close()
        git("add", rel)
    for top in OLD_ROOTS:
        for dirpath, dirnames, _ in os.walk(os.path.join(ROOT, top), topdown=False):
            for d in dirnames:
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
            if os.path.isdir(dirpath) and not os.listdir(dirpath):
                os.rmdir(dirpath)
    left = [t for t in OLD_ROOTS if os.path.exists(os.path.join(ROOT, t))]
    print("남은 옛 디렉토리:", left or "없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
