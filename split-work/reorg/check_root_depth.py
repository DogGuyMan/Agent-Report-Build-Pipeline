#!/usr/bin/env python3
"""모든 .py 에서 `X = os.path.dirname(...os.path.abspath(__file__)...)` 사슬이 저장소 뿌리를 가리키는지 — 사슬 길이 == 깊이 + 1 — 를 본다.
자기 디렉토리(사슬 1)와 중간 디렉토리는 보고만 한다."""
import os
import re
import subprocess
import sys

from reorg_lib import ROOT

CHAIN = re.compile(r"^\s*(_?ROOT)\s*=\s*((?:os\.path\.dirname\()+)os\.path\.abspath\(__file__\)")


def main() -> int:
    bad: list[str] = []
    for rel in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "--", "*.py"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n"):
        if not rel or rel.startswith("split-work/"):
            continue
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                m = CHAIN.match(line)
                if m and m.group(2).count("os.path.dirname(") != rel.count("/") + 1:
                    bad.append(f"{rel}:{i}: {m.group(1)} 사슬 {m.group(2).count('os.path.dirname(')} ≠ 깊이+1 {rel.count('/') + 1}")
    print("\n".join(bad) or "ROOT 사슬 전부 맞다")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
