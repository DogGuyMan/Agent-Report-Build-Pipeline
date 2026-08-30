#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='declmap.py']"/>
# 선언과 그 위의 문서 주석만 뽑아 한 장으로 만드는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""declmap.py — 선언과 그 위의 문서 주석을 뽑아 한 장으로 만든다.

뽑는 것은 선언 한 줄과 그 **바로 위에 붙은 문서 주석**이다. 본문은 뽑지 않는다.

⚠ 정규식이라 문법을 이해하지 못한다. 문자열 안의 `class` 같은 낱말에 속을 수 있고,
여러 줄에 걸친 선언은 첫 줄만 본다. 산출물은 읽을 자리를 좁혀 주는 목록이지 코드 지도가
아니다 — 지도는 정적 수집기(clang-uml · roslyn-dump)가 만든다.

  python3 declmap.py <저장소> --lang cs --include Assets/@Scripts -o declmap.json
  python3 declmap.py <저장소> --lang cpp --include core --include app
"""
import argparse
import json
import os
import re
import subprocess
import sys
from typing import TypedDict


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.LangRule']"/>
# 언어 하나(cs/cpp/py/ts)마다 선언과 문서 주석을 정규식으로 잡는 규칙 한 세트의 모양이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.declmap.doc_above
# 언어 규칙 한 칸의 생김새를 적어 둔 표.
# 쓰는 것: 없음 · 쓰이는 곳: declmap.LANGS, doc_above, declmap.scan
class LangRule(TypedDict):
    """LANGS 한 칸의 생김새. 다섯 칸 중 None 이 될 수 있는 것은 `strip` 하나뿐이다."""
    exts: tuple[str, ...]
    decl: re.Pattern[str]
    doc: tuple[str, ...]
    lead: re.Pattern[str]
    strip: re.Pattern[str] | None


# ── 언어별 규칙. 넷 고정이다.
#    doc:  선언 위에 붙는 문서 주석의 시작 표시
#    lead: 주석 표시 자체를 벗기는 꼴 (줄 앞의 /// · # · * 따위)
#    strip: 벗긴 뒤 남은 마크업을 걷어 내는 꼴 (C# 의 <summary> 등). 없으면 None
LANGS: dict[str, LangRule] = {
    "cs": {
        "exts": (".cs",),
        "decl": re.compile(r'^\s*(?:\[[^\]]*\]\s*)?(?:public|internal|protected|private)?\s*'
                           r'(?:static\s+|abstract\s+|sealed\s+|partial\s+|readonly\s+)*'
                           r'(class|interface|struct|enum|record)\s+([A-Za-z_][\w<>,\s]*)'),
        "doc": ("///",), "lead": re.compile(r'^\s*///+\s?'), "strip": re.compile(r'<[^>]+>'),
    },
    "cpp": {
        "exts": (".h", ".hpp", ".cpp", ".cc"),
        "decl": re.compile(r'^\s*(?:template\s*<[^>]*>\s*)?'
                           r'(class|struct|enum class|enum|namespace)\s+([A-Za-z_]\w*)'),
        "doc": ("///", "//!", "//"), "lead": re.compile(r'^\s*//[/!]*\s?'), "strip": None,
    },
    "py": {
        "exts": (".py",),
        "decl": re.compile(r'^\s*(?:@\w+\s*)?(class|def)\s+([A-Za-z_]\w*)'),
        "doc": ("#",), "lead": re.compile(r'^\s*#+\s?'), "strip": None,
    },
    "ts": {
        "exts": (".ts", ".tsx", ".mjs", ".js", ".jsx"),
        "decl": re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?'
                           r'(class|interface|type|enum|function|const)\s+([A-Za-z_$][\w$]*)'),
        "doc": ("///", "//", "*"), "lead": re.compile(r'^\s*(?://+|\*+)\s?'), "strip": None,
    },
}


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.Decl']"/>
# 뽑아낸 선언 하나를 담는 자료 모양이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.declmap.FileDecls
# 뽑아낸 선언 한 줄의 생김새.
# 쓰는 것: 없음 · 쓰이는 곳: declmap.FileDecls, declmap.scan
class Decl(TypedDict):
    """선언 하나. `line` 은 1-based 다. `scan` 이 내고 `render` · warmup · run_mode1 이 읽는다."""
    line: int
    kind: str
    name: str
    doc: str


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.FileDecls']"/>
# 소스 파일 한 개에서 뽑아낸 결과(총 줄 수와 선언 목록)를 담는 딕셔너리 틀이다.
# 쓰는 것: machine.declmap.Decl · 쓰이는 곳: machine.declmap.render
# 파일 한 개 몫의 선언 묶음.
# 쓰는 것: Decl · 쓰이는 곳: declmap.scan, render
class FileDecls(TypedDict):
    """파일 한 개 몫. `warmup.decl_hash` 가 받는 것이 이 꼴이다."""
    lines: int
    decls: list[Decl]


SKIP_DIRS = {"node_modules", "__pycache__", ".git", "build", "obj", "bin",
             "vcpkg_installed", ".venv", "Library", "Temp", "out", ".tmp"}
DOC_MAX_LINES = 14   # 선언 위로 이만큼만 거슬러 올라간다


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.tracked_files']"/>
# 훑어볼 소스 파일 목록을 골라내는 함수다.
# 쓰는 것: machine.declmap.LANGS · 쓰이는 곳: machine.declmap.scan, machine.warmup.main, runner.run_mode1.run_warmup
def tracked_files(repo: str, lang: str, includes: list[str]) -> list[str]:
    """git 이 아는 파일만 본다 — 빌드 산출물과 캐시를 걸러 내는 가장 싼 방법이다."""
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    exts = LANGS[lang]["exts"]
    out: list[str] = []
    for rel in r.stdout.split("\n"):
        if not rel or not rel.endswith(exts):
            continue
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if includes and not any(rel.startswith(p) for p in includes):
            continue
        out.append(rel)
    return sorted(out)


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.doc_above']"/>
# 선언 한 줄 바로 위에 붙어 있는 문서 주석을 모으는 함수다.
# 쓰는 것: machine.declmap.LangRule · 쓰이는 곳: machine.declmap.scan, machine.test_declmap._doc
def doc_above(lines: list[str], i: int, rule: LangRule) -> str:
    """선언 위에 붙은 문서 주석을 모은다. 빈 줄과 특성(attribute) 줄은 건너뛴다."""
    got: list[str] = []
    j = i - 1
    while j >= 0 and (i - j) <= DOC_MAX_LINES:
        s = lines[j].strip()
        if s.startswith(rule["doc"]):
            body = rule["lead"].sub("", s)
            strip = rule["strip"]      # 지역 변수로 받아야 None 검사가 아래까지 이어진다
            if strip:
                body = strip.sub("", body)
            got.insert(0, body.strip())
        elif s == "" or s.startswith("[") or s.startswith("@"):
            pass                      # 빈 줄과 특성은 주석과 선언 사이에 흔히 낀다
        else:
            break
        j -= 1
    return " ".join(x for x in got if x).strip()


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.scan']"/>
# 저장소 안 소스 파일들을 하나씩 열어서, 그 안에 있는 선언(클래스·함수 등)과 그 위에 붙은 문서 주석을 뽑아 모으는 함수다.
# 쓰는 것: machine.declmap.tracked_files, machine.declmap.doc_above · 쓰이는 곳: machine.declmap.main, machine.warmup.main, runner.run_mode1.run_warmup
def scan(repo: str, lang: str, includes: list[str],
         doc_chars: int) -> tuple[dict[str, FileDecls], dict[str, int]]:
    rule = LANGS[lang]
    result: dict[str, FileDecls] = {}
    counts = {"파일": 0, "선언": 0, "문서 주석 있음": 0}
    for rel in tracked_files(repo, lang, includes):
        path = os.path.join(repo, rel)
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
        except OSError:
            continue
        hits: list[Decl] = []
        for i, ln in enumerate(lines):
            m = rule["decl"].match(ln)
            if not m:
                continue
            name = m.group(2).split(":")[0].split("{")[0].split("(")[0].split("=")[0].strip()
            if not name:
                continue
            doc = doc_above(lines, i, rule)[:doc_chars]
            hits.append({"line": i + 1, "kind": m.group(1), "name": name, "doc": doc})
            counts["선언"] += 1
            if doc:
                counts["문서 주석 있음"] += 1
        if hits:
            result[rel] = {"lines": len(lines), "decls": hits}
            counts["파일"] += 1
    return result, counts


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.render']"/>
# scan()이 만든 결과를 사람이 읽기 좋은 텍스트로 바꾸는 함수다.
# 쓰는 것: machine.declmap.FileDecls · 쓰이는 곳: machine.declmap.main
def render(result: dict[str, FileDecls]) -> str:
    """사람과 LLM 이 그대로 읽을 수 있는 글자로. JSON 보다 짧다."""
    out: list[str] = []
    for rel, v in result.items():
        out.append(f"══ {rel}  ({v['lines']}줄)")
        for d in v["decls"]:
            out.append(f"  {d['line']:5} {d['kind']:12} {d['name']}")
            if d["doc"]:
                out.append(f"        ㄴ {d['doc']}")
    return "\n".join(out)


# <include file="machine/comments.xml" path="//term[@id='machine.declmap.main']"/>
# declmap.py 도구를 터미널에서 실행할 때 제일 먼저 불리는 진입점 함수다.
# 쓰는 것: machine.declmap.scan, machine.declmap.render · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--lang", required=True, choices=sorted(LANGS))
    ap.add_argument("--include", action="append", default=[],
                    help="이 접두사로 시작하는 경로만 본다. 여러 번 쓸 수 있다")
    ap.add_argument("--doc-chars", type=int, default=220, help="문서 주석 최대 글자 수")
    ap.add_argument("-o", "--out", help="JSON 출력 경로. 없으면 글자만 낸다")
    a = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"에러 — git 저장소가 아니다: {repo}", file=sys.stderr)
        return 1

    result, counts = scan(repo, a.lang, a.include, a.doc_chars)
    print(render(result))
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(result, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n{a.out}", file=sys.stderr)
    ratio = counts["문서 주석 있음"] / counts["선언"] * 100 if counts["선언"] else 0
    print(f"\n파일 {counts['파일']} · 선언 {counts['선언']} · "
          f"문서 주석 {counts['문서 주석 있음']} ({ratio:.0f}%)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
