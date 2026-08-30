#!/usr/bin/env python3
"""lang_select.py — 어떤 정적 수집기를 돌릴지 고른다.

    python3 lang_select.py <저장소> -o lang-select.json
    python3 lang_select.py <저장소> --propose py -o lang-select.json   # 모형의 제안을 받아

두 갈래를 합친다. **세는 것은 기계가, 읽는 것은 모형이 한다.**

  · `count_sources` — 확장자별 파일 수를 센다. 결정론이다.
  · `--propose` — 루트 문서(README·CLAUDE·ARCHITECTURE)를 읽은 모형이 낸 언어 하나.

모형의 제안은 **검사를 통과할 때만** 채택된다. 그 언어의 소스가 실제로 한 개도 없으면
버리고 파일 수가 가장 많은 언어로 간다. 모형은 근거를 대는 자리이지 결정하는 자리가 아니다.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Literal, TypedDict

Lang = Literal["cpp", "cs", "py", "ts"]

# 언어별 확장자와 그 언어를 맡는 수집기. `machine/declmap.py` 의 LANGS 와 같은 네 이름이다.
LANG_EXTS: dict[Lang, tuple[str, ...]] = {
    "cpp": (".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"),
    "cs": (".cs",),
    "py": (".py",),
    "ts": (".ts", ".tsx"),
}
COLLECTOR: dict[Lang, str] = {
    "cpp": "clang-uml",
    "cs": "roslyn-dump",
    "py": "griffe+pycalls",
    "ts": "none",            # 수집기가 아직 없다. 고르면 prep 이 막힌다
}

# 루트에서 모형에게 읽힐 문서. 없으면 건너뛴다.
DOC_NAMES = ("README.md", "CLAUDE.md", "ARCHITECTURE.md", "AGENTS.md")


class LangSelect(TypedDict):
    language: Lang | None
    collector: str
    counts: dict[str, int]
    proposed: str | None
    why: str


# git 이 아는 파일만 확장자별로 센다.
# 쓰는 것: 없음 · 쓰이는 곳: select
def count_sources(repo: str) -> dict[str, int]:
    """언어별 소스 파일 수. git 이 추적하는 것만 센다 — 빌드 산출물과 vendored 를 피한다."""
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True)
    files = r.stdout.split("\n") if r.returncode == 0 else []
    if not files:
        for dirpath, dirnames, filenames in os.walk(repo):
            dirnames[:] = [d for d in dirnames
                           if d not in {".git", "node_modules", "__pycache__", ".venv"}]
            files += [os.path.relpath(os.path.join(dirpath, f), repo) for f in filenames]
    out: dict[str, int] = {}
    for lang, exts in LANG_EXTS.items():
        out[lang] = sum(1 for f in files if f.endswith(exts))
    return out


# 모형에게 읽힐 루트 문서를 모은다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def read_docs(repo: str, limit: int = 6000) -> str:
    """루트 문서 몇 개를 앞부분만 잘라 잇는다. 없으면 빈 문자열이다."""
    parts: list[str] = []
    for name in DOC_NAMES:
        p = os.path.join(repo, name)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            parts.append(f"===== {name} =====\n{fh.read(limit)}")
    return "\n\n".join(parts)


# 세어 본 것과 모형의 제안을 합쳐 수집기를 고른다.
# 쓰는 것: count_sources · 쓰이는 곳: lang_select.main
def select(repo: str, proposed: str | None = None) -> LangSelect:
    """제안이 검사를 통과하면 그것을, 아니면 파일 수가 가장 많은 언어를 고른다.

    제안이 검사를 통과하지 못하는 경우는 둘이다 — 아는 언어가 아니거나, 그 언어의
    소스가 저장소에 한 개도 없거나. 둘 다 `why` 에 적어 남긴다.
    """
    counts = count_sources(repo)

    def top_of(langs: list[Lang]) -> Lang | None:
        """파일이 하나라도 있는 것 중 가장 많은 언어. 없으면 None."""
        # 선언이 없으면 리터럴이 str 로 넓혀져 Lang 을 잃는다.
        have: list[Lang] = [k for k in langs if counts.get(k)]
        return max(have, key=lambda k: counts[k]) if have else None

    all_langs: list[Lang] = ["cpp", "cs", "py", "ts"]
    best = top_of(all_langs)

    if proposed is None:
        why = f"제안 없음. 파일 수로 골랐다 ({counts})." if best else f"소스가 없다 ({counts})."
        return {"language": best, "collector": COLLECTOR.get(best, "none") if best else "none",
                "counts": counts, "proposed": None, "why": why}

    # `in` 은 형을 좁히지 못한다. 목록에서 같은 값을 찾아 Lang 으로 풀어 둔다.
    lang: Lang | None = next((k for k in all_langs if k == proposed), None)
    if lang is None:
        return {"language": best, "collector": COLLECTOR.get(best, "none") if best else "none",
                "counts": counts, "proposed": proposed,
                "why": f"제안 '{proposed}' 은 아는 언어가 아니다. 파일 수로 골랐다."}
    if not counts.get(lang):
        return {"language": best, "collector": COLLECTOR.get(best, "none") if best else "none",
                "counts": counts, "proposed": proposed,
                "why": f"제안 '{proposed}' 의 소스가 한 개도 없다. 파일 수로 골랐다."}
    if COLLECTOR[lang] == "none":
        # 수집기가 없는 언어를 고르면 prep 이 막힌다. 수집할 수 있는 언어로 물러서는 편이
        # 언제나 낫다 — 지도가 없는 것보다 부분 지도가 낫기 때문이다.
        alt = top_of([k for k in all_langs if COLLECTOR[k] != "none"])
        return {"language": alt, "collector": COLLECTOR.get(alt, "none") if alt else "none",
                "counts": counts, "proposed": proposed,
                "why": f"제안 '{proposed}' 은 수집기가 없다. 수집 가능한 '{alt}' 로 물러섰다."}

    note = "" if lang == best else f" (파일 수 1위는 '{best}' 이지만 제안을 따랐다)"
    return {"language": lang, "collector": COLLECTOR[lang], "counts": counts,
            "proposed": proposed, "why": f"제안 '{lang}' 이 검사를 통과했다{note}."}


# lang_select 도구의 명령줄 진입점.
# 쓰는 것: select, read_docs · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--propose", default=None, help="모형이 낸 언어 하나 (cpp|cs|py|ts)")
    ap.add_argument("--print-docs", action="store_true", help="모형에게 줄 문서만 찍고 끝낸다")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    if a.print_docs:
        sys.stdout.write(read_docs(a.repo))
        return 0

    got = select(a.repo, a.propose)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(got, fh, ensure_ascii=False, indent=2)
        print(f"{a.out} — 언어 {got['language']} · 수집기 {got['collector']}")
    else:
        print(json.dumps(got, ensure_ascii=False, indent=2))
    print(f"  {got['why']}")
    return 0 if got["language"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
