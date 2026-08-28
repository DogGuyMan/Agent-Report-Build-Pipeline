#!/usr/bin/env python3
"""fix_citation_paths.py — 인용의 맨 파일명을 저장소 기준 전체 경로로 보강한다.

**왜 필요한가.** 🔵 실측 — 위키를 쓰는 LLM 은 같은 파일을 여러 번 인용할 때 두 번째부터
경로를 줄여 `UI_StarRate.cs:50` 처럼 파일명만 남긴다. 사람이 읽기엔 자연스럽지만
**링크로는 죽고 인용 검증기 L1 실패로 잡힌다.** 프롬프트로 경고해도 반복 발생했다.

기계적으로 복구 가능한 경우에만 고친다:
  - 저장소 안에서 그 파일명이 **정확히 하나**일 때 → 전체 경로로 치환
  - 여러 개면 손대지 않고 보고한다 (어느 것인지 기계가 정할 수 없다)

⚠ 이미 경로가 붙은 인용(`Assets/...` / `src/...`)은 건드리지 않는다.

  fix_citation_paths.py <문서.md ...> --repo <저장소> [--dry-run]
"""
import argparse
import os
import re
import sys
from collections import defaultdict

# 경로 구분자 없이 파일명만 있는 인용. 앞에 / 나 단어문자가 오면 이미 경로가 붙은 것이다.
BARE = re.compile(r"(?<![/\w.])([A-Za-z_][A-Za-z0-9_]*\.(?:cs|h|hpp|cpp|cc|py|mjs|ts))(?=:\d)")

SKIP_DIRS = {".git", "Library", "Temp", "obj", "bin", "node_modules", "out"}


def index_repo(repo):
    """파일명 -> 저장소 기준 상대경로 목록."""
    idx = defaultdict(list)
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lstrip(".") in ("cs", "h", "hpp", "cpp", "cc", "py", "mjs", "ts"):
                idx[f].append(os.path.relpath(os.path.join(root, f), repo))
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(a.repo))
    idx = index_repo(repo)

    total_fixed = total_ambiguous = total_missing = 0
    for doc in a.docs:
        text = open(doc, encoding="utf-8").read()
        fixed, amb, miss = 0, [], []

        def sub(m):
            nonlocal fixed
            name = m.group(1)
            cands = idx.get(name, [])
            if len(cands) == 1:
                fixed += 1
                return cands[0]
            if len(cands) > 1:
                amb.append((name, len(cands)))
            else:
                miss.append(name)
            return name

        new = BARE.sub(sub, text)
        if fixed and not a.dry_run:
            open(doc, "w", encoding="utf-8").write(new)
        name = os.path.basename(doc)
        if fixed or amb or miss:
            print(f"  {name} — 보강 {fixed}"
                  + (f" · 모호 {len(amb)}" if amb else "")
                  + (f" · 미발견 {len(miss)}" if miss else ""))
            for n, c in dict(amb).items():
                print(f"      모호: {n} ({c}곳) — 손대지 않았다. 사람이 정해야 한다")
            for n in dict.fromkeys(miss):
                print(f"      미발견: {n} — 저장소에 없다. 인용 자체가 틀렸을 수 있다")
        total_fixed += fixed
        total_ambiguous += len(amb)
        total_missing += len(miss)

    print(f"\n{'(dry-run) ' if a.dry_run else ''}보강 {total_fixed} · 모호 {total_ambiguous} · 미발견 {total_missing}")
    return 1 if (total_ambiguous or total_missing) else 0


if __name__ == "__main__":
    sys.exit(main())
