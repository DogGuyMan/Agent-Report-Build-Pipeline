#!/usr/bin/env python3
"""폐지된 xmldoc 주입기가 남긴 `# <include …/>` 블록(표식 · 뜻 줄 · 선택적 의존 줄)을 전부 걷어내고,
파일마다 지운 1-based 줄 번호를 `split-work/reorg/out/removed-lines.json` 에 남긴다.
블록 경계는 machine/xmldoc.py 의 block_extent() 와 같다 — 의존 줄이 실제로 있는지 세어 더한다."""
import json
import os
import re
import subprocess
import sys

from reorg_lib import OUT, REMOVED, ROOT

INCLUDE_RE = re.compile(r'^\s*(#|//)\s*<include file="machine/comments\.xml"')
USES_LINE_RE = re.compile(r"^\s*(?:#|//)\s*(?:\S+ — )?쓰는 것: ")
CODE_ROOTS = ("runner/", "machine/", "viz/", "tools/", "bin/", "test/")


def block_extent(lines: list[str], i: int) -> int:
    c = 0
    while i + c < len(lines) and INCLUDE_RE.match(lines[i + c]):
        c += 1
    n = 2 * c
    u = 0
    while u < c and i + n + u < len(lines) and USES_LINE_RE.match(lines[i + n + u]):
        u += 1
    return n + u


def strip(lines: list[str]) -> tuple[list[str], list[int], int]:
    out: list[str] = []
    removed: list[int] = []
    markers = 0
    i = 0
    while i < len(lines):
        if INCLUDE_RE.match(lines[i]):
            n = block_extent(lines, i)
            markers += sum(1 for k in range(n) if INCLUDE_RE.match(lines[i + k]))
            removed.extend(range(i + 1, i + n + 1))
            i += n
            continue
        out.append(lines[i])
        i += 1
    return out, removed, markers


def main() -> int:
    tracked = [l for l in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n") if l]
    record: dict[str, list[int]] = {}
    files = markers = lines_removed = 0
    for rel in tracked:
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        if "<include file=" not in text:
            continue
        if not rel.startswith(CODE_ROOTS):
            print("코드 밖에 include 표식이 있다 — 손으로 본다:", rel)
            continue
        lines = text.splitlines(keepends=True)
        out, removed, m = strip(lines)
        if not removed:
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write("".join(out))
        record[rel] = removed
        files += 1
        markers += m
        lines_removed += len(removed)
    os.makedirs(OUT, exist_ok=True)
    with open(REMOVED, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    print(f"파일 {files} · 표식 {markers} · 지운 줄 {lines_removed} → {REMOVED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
