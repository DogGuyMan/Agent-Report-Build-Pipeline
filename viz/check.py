# <include file="machine/comments.xml" path="//term[@id='viz/check.py']"/>
# 구운 보고서가 규칙을 지켰는지 보는 검사 스크립트.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# viz/check.py
# 산출물 검사 규칙. 전부 기계 판정이며 사람 판단이 필요 없다.
import json
import os
import re
import subprocess
import sys
from typing import TypedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ScriptCount(TypedDict):
    ok: bool
    count: int


class LinkResult(TypedDict):
    ok: bool
    missingSections: list[str]
    orphanSections: list[str]


class TermResult(TypedDict):
    ok: bool
    missing: list[str]


def countScripts(html: str) -> ScriptCount:
    """`<script>` 는 pan/zoom 하나까지만 허용된다(산출물 불변식)."""
    count = len(re.findall(r"<script", html))
    return {"ok": count <= 1, "count": count}


def linkIntegrity(decisionIds: list[str], reportSource: str) -> LinkResult:
    """`data.ts` 의 결정 id 와 `report.tsx` 의 절이 1:1 인지 본다."""
    sectionIds = re.findall(r'<Section\s+title="(D\d+)\b', reportSource)
    missingSections = [i for i in decisionIds if i not in sectionIds]
    orphanSections = [i for i in sectionIds if i not in decisionIds]
    return {"ok": not missingSections and not orphanSections,
            "missingSections": missingSections, "orphanSections": orphanSections}


# 본문에서 잡는 식별자 꼴 셋. `runner/term/collect.mjs` 의 findNewConcepts 와 같은 값이어야 한다.
TERM_PATTERNS = [
    re.compile(r"\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b"),
    re.compile(r"\b[a-z][a-z0-9_-]*\.json\b"),
    re.compile(r"\b[a-z][A-Za-z0-9_]*\[\]"),
]


def undefinedTerms(reportSource: str, termIds: list[str]) -> TermResult:
    """본문의 식별자 꼴 낱말 중 용어집에 정의가 없는 것을 찾는다.

    **경고이지 실패가 아니다** — 탐지 규칙이 오탐을 낼 수 있어 빌드를 막지 않는다.
    자연어 용어(WarmUp · PageRank)는 기계가 가릴 수 없어 저자가 직접 넣어야 한다.
    """
    known = set(termIds)
    found: set[str] = set()
    # JSX 속성값과 import 경로는 본문이 아니다. 거칠게 걷어낸다.
    # 절 제목의 D0·D1 은 링크 무결성 검사가 담당하므로 통째로 뺀다.
    body = re.sub(r"^import[^\n]*$", "", reportSource, flags=re.MULTILINE)
    body = re.sub(r'className="[^"]*"', "", body)
    body = re.sub(r'<Section\s+title="[^"]*"', "", body)
    for pat in TERM_PATTERNS:
        for m in pat.finditer(body):
            if m.group(0) not in known:
                found.add(m.group(0))
    return {"ok": not found, "missing": sorted(found)}


def versionMatch(dataVersion: str, currentVersion: str) -> dict[str, bool]:
    """`builderVersion` 불일치는 경고이지 실패가 아니다."""
    return {"ok": True, "warn": dataVersion != currentVersion}


def currentBuilderVersion() -> str:
    try:
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    except OSError:
        pass
    return "untagged"


def main() -> int:
    cwd = os.getcwd()
    failed = False

    out_file = os.path.join(cwd, "out/report.html")
    if not os.path.exists(out_file):
        print("실패 — out/report.html 이 없다. 먼저 report build 를 실행한다.", file=sys.stderr)
        return 1
    with open(out_file, encoding="utf-8") as f:
        html = f.read()

    s = countScripts(html)
    print("%s — <script> %s개 (허용 1)" % ("통과" if s["ok"] else "실패", s["count"]))
    if not s["ok"]:
        failed = True

    # 타입 검사용 tsconfig 는 검사 시점에 ROOT 에 임시로 만들고 지운다.
    # 보고서마다 내용이 같은 보일러플레이트라 대상 저장소에 남길 이유가 없다.
    #
    # paths 는 타입 해결 전용이라 선언 파일을 가리킨다. `.mjs` 를 직접 가리키면
    # TS 가 형제 `.d.mts` 를 찾지 않아 TS7016 이 난다 — 런타임 해결은 build.py 의 alias 가 한다.
    # typeRoots 를 명시하는 이유: 기본값은 tsconfig 위치 기준이라 @types/node 를 놓치고 TS2688 이 난다.
    # include 글로브 대신 files 에 절대경로를 열거한다. 글로브는 tsconfig 위치 기준으로
    # 해석되는데 이 파일은 ROOT 에 있고 검사 대상은 cwd 라 서로 다르다.
    tsconfig_path = os.path.join(ROOT, ".tmp-report-tsconfig.json")
    with open(tsconfig_path, "w", encoding="utf-8") as f:
        json.dump({
            "extends": os.path.join(ROOT, "tsconfig.json"),
            "compilerOptions": {
                "typeRoots": [os.path.join(ROOT, "node_modules/@types")],
                "paths": {
                    "report-builder": [os.path.join(ROOT, "viz/src/index.ts")],
                    "report-builder/types": [os.path.join(ROOT, "viz/src/types.ts")],
                    "report-builder/svg": [os.path.join(ROOT, "viz/svg.d.mts")],
                },
            },
            "files": [os.path.join(cwd, n) for n in sorted(os.listdir(cwd))
                      if re.search(r"\.tsx?$", n)],
            "include": [],
        }, f, indent=2)
        f.write("\n")

    try:
        tsc = subprocess.run(["npx", "tsc", "--noEmit", "-p", tsconfig_path],
                             cwd=ROOT, capture_output=True, text=True)
    finally:
        os.remove(tsconfig_path)
    print("%s — tsc --noEmit" % ("통과" if tsc.returncode == 0 else "실패"))
    if tsc.returncode != 0:
        print(tsc.stdout, file=sys.stderr)
        failed = True

    with open(os.path.join(cwd, "data.ts"), encoding="utf-8") as f:
        data_src = f.read()
    with open(os.path.join(cwd, "report.tsx"), encoding="utf-8") as f:
        report_src = f.read()

    ids = re.findall(r'id:\s*"(D\d+)"', data_src)
    link = linkIntegrity(ids, report_src)
    print("%s — 링크 무결성 (결정 %d건)" % ("통과" if link["ok"] else "실패", len(ids)))
    if not link["ok"]:
        if link["missingSections"]:
            print("  절이 없는 결정: %s" % ", ".join(link["missingSections"]), file=sys.stderr)
        if link["orphanSections"]:
            print("  결정이 없는 절: %s" % ", ".join(link["orphanSections"]), file=sys.stderr)
        failed = True

    # 용어집 대조 — 경고만 낸다. 결정 id(D0·D1…)는 링크 무결성 검사가 담당하므로 뺀다.
    term_ids = re.findall(r'\bid:\s*"([^"]+)"', data_src)
    glossary_ids = [t for t in term_ids if not re.fullmatch(r"D\d+", t)]
    ut = undefinedTerms(report_src, glossary_ids)
    if ut["ok"]:
        print("통과 — 용어집 대조 (정의 %d개)" % len(glossary_ids))
    else:
        print("경고 — 용어집에 없는 식별자 %d개" % len(ut["missing"]))
        print("  %s" % ", ".join(ut["missing"]))

    m = re.search(r'builderVersion:\s*"([^"]+)"', data_src)
    dv = m.group(1) if m else "?"
    cv = currentBuilderVersion()
    v = versionMatch(dv, cv)
    print("%s — builderVersion %s vs %s" % ("경고" if v["warn"] else "통과", dv, cv))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
