#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/declmap.py']"/>
# 선언과 그 위의 문서 주석만 뽑아 한 장으로 만드는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""declmap.py — 선언과 그 위의 문서 주석을 뽑아 한 장으로 만든다.

**왜 있나.** 전수조사(Mode 1)에서 LLM 이 소스를 전부 정독하면 비싸다.
🔵 2026-08-29 실측 — QtVisionEdit 30파일 2,982줄을 전량 정독했을 때 소스 1줄당 96토큰,
StickRush 110파일 8,164줄을 이 방식(선언 + 문서 주석)으로 읽었을 때 **1줄당 33토큰**이었다.
약 3배 차이다. 그 손 작업을 도구로 굳힌 것이 이 파일이다.

**무엇을 뽑나.** 선언 한 줄과, 그 **바로 위에 붙은 문서 주석**이다. 저자가 직접 쓴 의도라
이름에서 추론하는 것보다 근거가 낫다. 본문은 뽑지 않는다 — 본문이 필요하면 사람이 연다.

**한계를 분명히 한다.** 정규식이라 문법을 이해하지 못한다. 문자열 안의 `class` 같은 낱말에
속을 수 있고, 여러 줄에 걸친 선언은 첫 줄만 본다. 그래서 이 산출물은 **읽을 자리를 좁혀 주는
목록**이지 코드 지도가 아니다. 지도는 정적 수집기(clang-uml · roslyn-dump)가 만든다.

  python3 declmap.py <저장소> --lang cs --include Assets/@Scripts -o declmap.json
  python3 declmap.py <저장소> --lang cpp --include core --include app
"""
import argparse
import json
import os
import re
import subprocess
import sys

# ── 언어별 규칙. 넷 고정이다 — 레지스트리를 만들지 않는다.
#    doc:  선언 위에 붙는 문서 주석의 시작 표시
#    lead: 주석 표시 자체를 벗기는 꼴 (줄 앞의 /// · # · * 따위)
#    strip: 벗긴 뒤 남은 마크업을 걷어 내는 꼴 (C# 의 <summary> 등). 없으면 생략
LANGS = {
    "cs": dict(
        exts=(".cs",),
        decl=re.compile(r'^\s*(?:\[[^\]]*\]\s*)?(?:public|internal|protected|private)?\s*'
                        r'(?:static\s+|abstract\s+|sealed\s+|partial\s+|readonly\s+)*'
                        r'(class|interface|struct|enum|record)\s+([A-Za-z_][\w<>,\s]*)'),
        doc=("///",), lead=re.compile(r'^\s*///+\s?'), strip=re.compile(r'<[^>]+>'),
    ),
    "cpp": dict(
        exts=(".h", ".hpp", ".cpp", ".cc"),
        decl=re.compile(r'^\s*(?:template\s*<[^>]*>\s*)?'
                        r'(class|struct|enum class|enum|namespace)\s+([A-Za-z_]\w*)'),
        doc=("///", "//!", "//"), lead=re.compile(r'^\s*//[/!]*\s?'), strip=None,
    ),
    "py": dict(
        exts=(".py",),
        decl=re.compile(r'^\s*(?:@\w+\s*)?(class|def)\s+([A-Za-z_]\w*)'),
        doc=("#",), lead=re.compile(r'^\s*#+\s?'), strip=None,
    ),
    "ts": dict(
        exts=(".ts", ".tsx", ".mjs", ".js", ".jsx"),
        decl=re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?'
                        r'(class|interface|type|enum|function|const)\s+([A-Za-z_$][\w$]*)'),
        doc=("///", "//", "*"), lead=re.compile(r'^\s*(?://+|\*+)\s?'), strip=None,
    ),
}

SKIP_DIRS = {"node_modules", "__pycache__", ".git", "build", "obj", "bin",
             "vcpkg_installed", ".venv", "Library", "Temp", "out", ".tmp"}
DOC_MAX_LINES = 14   # 선언 위로 이만큼만 거슬러 올라간다


# <include file="docs/codegraph/comments.xml" path="//term[@id='declmap.tracked_files']"/>
# 조사 대상 파일 목록을 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: declmap.scan, warmup.main
def tracked_files(repo, lang, includes):
    """git 이 아는 파일만 본다 — 빌드 산출물과 캐시를 걸러 내는 가장 싼 방법이다."""
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    exts = LANGS[lang]["exts"]
    out = []
    for rel in r.stdout.split("\n"):
        if not rel or not rel.endswith(exts):
            continue
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if includes and not any(rel.startswith(p) for p in includes):
            continue
        out.append(rel)
    return sorted(out)


# <include file="docs/codegraph/comments.xml" path="//term[@id='doc_above']"/>
# 선언 바로 위에 붙은 문서 주석을 모은다.
# 쓰는 것: 없음 · 쓰이는 곳: declmap.scan
def doc_above(lines, i, rule):
    """선언 위에 붙은 문서 주석을 모은다. 빈 줄과 특성(attribute) 줄은 건너뛴다."""
    got, j = [], i - 1
    while j >= 0 and (i - j) <= DOC_MAX_LINES:
        s = lines[j].strip()
        if s.startswith(rule["doc"]):
            body = rule["lead"].sub("", s)
            if rule["strip"]:
                body = rule["strip"].sub("", body)
            got.insert(0, body.strip())
        elif s == "" or s.startswith("[") or s.startswith("@"):
            pass                      # 빈 줄과 특성은 주석과 선언 사이에 흔히 낀다
        else:
            break
        j -= 1
    return " ".join(x for x in got if x).strip()


# <include file="docs/codegraph/comments.xml" path="//term[@id='declmap.scan']"/>
# 파일을 돌며 선언과 문서 주석을 모은다.
# 쓰는 것: doc_above, declmap.tracked_files · 쓰이는 곳: warmup.decl_hash, warmup.main
def scan(repo, lang, includes, doc_chars):
    rule = LANGS[lang]
    result, counts = {}, {"파일": 0, "선언": 0, "문서 주석 있음": 0}
    for rel in tracked_files(repo, lang, includes):
        path = os.path.join(repo, rel)
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
        except OSError:
            continue
        hits = []
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


def render(result):
    """사람과 LLM 이 그대로 읽을 수 있는 글자로. JSON 보다 짧다."""
    out = []
    for rel, v in result.items():
        out.append(f"══ {rel}  ({v['lines']}줄)")
        for d in v["decls"]:
            out.append(f"  {d['line']:5} {d['kind']:12} {d['name']}")
            if d["doc"]:
                out.append(f"        ㄴ {d['doc']}")
    return "\n".join(out)


def main():
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
