#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='verify_citations.py']"/>
# 문서에 적힌 file:line 인용이 진짜인지 기계로 판정하는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""verify_citations.py — 문서의 file:line 인용을 기계로 판정한다 (L1/L2/L3).

  L1  파일이 존재하나                 os.path.isfile
  L2  그 줄이 존재하나                줄 수 비교
  L3  그 위치에 그 심볼이 있나        codegraph 노드 + 위치 있는 간선 전부(C-16) + 살(--detail)

**판정은 3값이다** — 통과 / 실패 / 근거 없음.
  C-16 — L3 대상은 소유 간선만이 아니라 **file/line 이 null 이 아닌 간선 전부**다.
  `--detail`(살 파일)을 주면 멤버·메서드 선언 줄까지 잰다.
  - "근거 없음" = L1·L2 는 통과했으나 codegraph 에 그 위치의 선언이 등록돼 있지 않다.
    메서드 본문 줄, 함수 층(코드그래프 밖), dependency 간선의 위치가 여기 떨어진다.
  - 근거 없음을 통과로 세면 검증이 무의미해지고, 실패로 세면 정상 인용이 전부 실패한다.
    **그대로 3값으로 낸다.** 종료 코드는 실패(L1/L2)가 있을 때만 1 이다.

이름 대조 규칙 (F-2):
  - 중첩 타입은 마지막 조각으로 대조한다 (Program::UniformBlock -> UniformBlock)
  - canonical 이름 차이(basic_string 등)는 외부 노드 문제라 여기 안 온다 — 외부는 file 이 null

  verify_citations.py <문서.md ...> --repo <저장소> --codegraph <codegraph.json> [-v]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Mapping
from typing import Literal, NotRequired, TypedDict, cast

# ── 읽어 들이는 JSON 두 가지의 모양. 이 도구가 실제로 읽는 열쇠만 적는다.

# codegraph.json — 이 저장소가 내는 코드 지도.
# file/line 이 null 인 노드·간선이 있다(외부 심볼). 그래서 값이 Optional 이다.


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.Node']"/>
# codegraph.json 안에 있는 노드 하나(클래스나 함수 같은 심볼 하나)의 모양을 정의한 타입이다. 실제로 동작하는 코드가 아니라 타입 체커를 위한 설계도다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.verify_citations.CodeGraph
class Node(TypedDict):
    id: str
    name: str
    kind: str
    module: str
    file: str | None
    line: int | None


# `from` 은 파이썬 예약어라 class 문법으로는 못 적는다. 함수 문법이 유일한 길이다.
Edge = TypedDict("Edge", {
    "from": str,
    "to": str,
    "kind": str,
    "label": str | None,
    "file": str | None,
    "line": int | None,
})


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.CodeGraph']"/>
# 이 저장소가 만드는 '코드 지도' 파일(codegraph.json)이 어떤 모양인지 파이썬 타입으로 적어 둔 것이다. 실제 동작은 없고 데이터 모양만 정의한다.
# 쓰는 것: machine.verify_citations.Node · 쓰이는 곳: 없음
class CodeGraph(TypedDict):
    nodes: list[Node]
    edges: list[Edge]


# 살 파일 — clang-uml(C++) 과 roslyn-dump(C#) 두 외부 도구의 산출물이다.
# 이 저장소가 만든 스키마가 아니므로 만지는 자리만 적는다.


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations._ClangMember']"/>
# clang-uml(C++ 분석 도구)이 만든 '살 파일' 안에서 클래스의 멤버 변수나 메서드 하나를 나타내는 타입이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.verify_citations._ClangElement
class _ClangMember(TypedDict, total=False):
    name: str
    # 위치는 중첩 딕셔너리 안이고 키가 없을 수도 있다. 열쇠 유무를 보장 못 하므로 Mapping 이다.
    source_location: Mapping[str, object]


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations._ClangElement']"/>
# clang-uml(C++ 분석 도구) 이 내놓는 '살 파일' 안에서 클래스 하나에 해당하는 부분이 어떤 모양인지 적어 둔 타입이다.
# 쓰는 것: machine.verify_citations._ClangMember · 쓰이는 곳: machine.verify_citations._DetailFile
class _ClangElement(TypedDict, total=False):
    display_name: str
    members: list[_ClangMember] | None
    methods: list[_ClangMember] | None


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations._RoslynType']"/>
# roslyn-dump(C# 분석 도구)가 만든 '살 파일' 안에서 클래스나 타입 하나를 나타내는 타입이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.verify_citations._DetailFile
class _RoslynType(TypedDict):
    name: str
    members: NotRequired[list[Mapping[str, object]] | None]
    methods: NotRequired[list[Mapping[str, object]] | None]


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations._DetailFile']"/>
# 살 파일(멤버·메서드까지 담은 원시 분석 결과) 하나가 어떤 모양인지 적어 둔 타입 정의.
# 쓰는 것: machine.verify_citations._ClangElement, machine.verify_citations._RoslynType · 쓰이는 곳: 없음
class _DetailFile(TypedDict, total=False):
    elements: list[_ClangElement]      # clang-uml
    types: list[_RoslynType]           # roslyn-dump


# (파일, 줄) -> 그 자리에 등록된 이름들. L3 판정이 보는 색인은 전부 이 모양이다.
Index = dict[tuple[str, int], list[str]]


# 인용 패턴 — 확장자 화이트리스트로 "3:4" 같은 오탐을 막는다.
# deep-wiki 로컬 규격 (path:line), 백틱/괄호/링크 감싸기 전부 허용, 범위 line-line 허용.
CITE = re.compile(
    r"([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot))"
    r":(\d+)(?:-(\d+))?")


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.short']"/>
# 긴 심볼 이름을 이름 대조에 쓸 수 있는 짧은 마지막 조각으로 줄여주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db._stem, machine.test_normalize.test_nested_name_uses_double_hash, machine.verify_citations.build_index, machine.verify_citations.load_detail_index, machine.verify_citations.main
def short(name: str) -> str:
    """이름 대조용 마지막 조각. `##` · `::` · `.` 로 잘라 마지막만, `<` 뒤는 버린다 (F-2)."""
    for sep in ("##", "::", "."):
        name = name.split(sep)[-1]
    return name.split("<")[0]


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.build_index']"/>
# 인용 검증 도구가 codegraph.json 파일을 읽어서, '어느 파일 어느 줄에 무슨 이름이 있는지' 빠르게 찾을 수 있는 표(색인) 두 개를 만드는 함수다.
# 쓰는 것: machine.verify_citations.short · 쓰이는 곳: machine.verify_citations.main
def build_index(codegraph: str) -> tuple[CodeGraph, Index, Index]:
    """codegraph -> (노드 색인, 간선 색인). 둘 다 (file,line) 로 찾는다."""
    g: CodeGraph = json.load(open(codegraph, encoding="utf-8"))
    # ⚠ (file,line) -> 이름은 1:1 이 아니다. 한 줄에 실제 선언과, 사용 지점을 위치로 갖는
    #   템플릿 인스턴스가 함께 등록될 수 있다. 그래서 값이 목록인 다중값 색인이다.
    nodes: Index = {}
    owns: Index = {}
    for n in g["nodes"]:
        if n.get("file") and n.get("line"):
            # 위 참 판정이 null 을 걸렀지만 .get() 을 통해서는 좁혀지지 않는다.
            nodes.setdefault(cast("tuple[str, int]", (n["file"], n["line"])), []).append(n["name"])
    nm = {n["id"]: n["name"] for n in g["nodes"]}
    for e in g["edges"]:
        if e.get("file") and e.get("line"):          # C-16 — 위치 있는 간선 전부
            desc = f"{short(nm.get(e['from'], '?'))} --{e.get('label') or e['kind']}--> {short(nm.get(e['to'], '?'))}"
            owns.setdefault(cast("tuple[str, int]", (e["file"], e["line"])), []).append(desc)
    return g, nodes, owns


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.load_detail_index']"/>
# clang-uml(C++) 이나 roslyn-dump(C#) 가 만든 '살(detail) 파일'을 읽어서, 멤버 변수나 메서드가 정확히 몇 번째 줄에 선언됐는지 찾는 표를 만드는 함수다.
# 쓰는 것: machine.verify_citations.short · 쓰이는 곳: machine.verify_citations.main
def load_detail_index(path: str) -> Index:
    """살 파일의 멤버·메서드 선언 줄 색인. clang-uml(elements)과 roslyn-dump(types) 양쪽을 안다."""
    d: _DetailFile = json.load(open(path, encoding="utf-8"))
    idx: Index = {}
    # TypedDict 첨자는 열쇠가 문자열 리터럴이어야 풀리므로 목록에 Literal 형을 박는다.
    # `.get(합집합 열쇠)` 는 Any 로 떨어져 두 갈래 모두 cast 로 형을 되돌린다.
    member_kinds: tuple[Literal["members", "methods"], ...] = ("members", "methods")
    if "elements" in d:                               # clang-uml (C++)
        for el in d["elements"]:
            for kind in member_kinds:
                for m in cast("list[_ClangMember]", el.get(kind) or []):
                    loc: Mapping[str, object] = m.get("source_location") or {}
                    if loc.get("file") and loc.get("line"):
                        idx.setdefault(cast("tuple[str, int]", (loc["file"], loc["line"])), []).append(
                            f"{short(el.get('display_name') or '?')}.{m.get('name')}")
    else:                                             # roslyn-dump (C#)
        for t in d.get("types", []):
            for kind in member_kinds:
                for m in cast("list[Mapping[str, object]]", t.get(kind) or []):
                    if m.get("file") and m.get("line"):
                        idx.setdefault(cast("tuple[str, int]", (m["file"], m["line"])), []).append(
                            f"{short(t['name'])}.{m.get('name')}")
    return idx


# <include file="machine/comments.xml" path="//term[@id='machine.verify_citations.main']"/>
# 위키 문서에 적힌 `파일:줄` 인용이 진짜인지 확인하는 명령줄 도구의 시작점.
# 쓰는 것: machine.verify_citations.short, machine.verify_citations.build_index, machine.verify_citations.load_detail_index · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docs", nargs="+", help="검사할 마크다운 문서")
    ap.add_argument("--repo", required=True, help="인용 경로의 기준 저장소")
    ap.add_argument("--codegraph", required=True)
    ap.add_argument("--detail", help="살 파일(clang-uml/roslyn-dump 원문) — 멤버·메서드 선언 줄까지 잰다")
    ap.add_argument("-v", "--verbose", action="store_true", help="인용 하나하나 출력")
    a = ap.parse_args()

    _, nodes, owns = build_index(a.codegraph)
    flesh: Index = load_detail_index(a.detail) if a.detail else {}
    repo = os.path.abspath(os.path.expanduser(a.repo))

    total: Counter[str] = Counter()
    fails: list[str] = []
    unfounded: list[str] = []
    name_warn: list[str] = []
    line_cache: dict[str, list[str] | None] = {}

    def lines_of(path: str) -> list[str] | None:
        if path not in line_cache:
            try:
                line_cache[path] = open(path, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                line_cache[path] = None
        return line_cache[path]

    for doc in a.docs:
        text = open(doc, encoding="utf-8").read().splitlines()
        for lineno, raw in enumerate(text, 1):
            # ⚠ 이름 대조는 앞뒤 1줄까지 본다. 산문이 줄바꿈되면 인용은 이 줄에, 심볼 이름은
            #   앞줄에 있어 한 줄만 보면 정상 문서가 경고로 뜬다.
            ctx = "\n".join(text[max(0, lineno - 2):lineno + 1])
            # ⚠ `<!-- Sources: ... -->` 는 다이어그램 근거 목록이지 주장이 아니다.
            #   이름이 없는 것이 정상이므로 이름 대조에서 뺀다.
            is_src_list = raw.lstrip().startswith("<!-- Sources:")
            for m in CITE.finditer(raw):
                f, ln = m.group(1), int(m.group(2))
                total["인용"] += 1
                where = f"{os.path.basename(doc)}:{lineno}"

                # L1
                ap_ = os.path.join(repo, f)
                content = lines_of(ap_)
                if content is None:
                    total["L1 실패"] += 1
                    fails.append(f"[L1] {where}  {f}:{ln} — 파일 없음")
                    continue
                total["L1 통과"] += 1
                # L2
                if ln > len(content):
                    total["L2 실패"] += 1
                    fails.append(f"[L2] {where}  {f}:{ln} — 파일이 {len(content)}줄뿐")
                    continue
                total["L2 통과"] += 1
                # L3 — 노드 / 소유 간선 / 근거 없음 (C-13)
                if (f, ln) in nodes:
                    names = nodes[(f, ln)]
                    total["L3 통과(노드)"] += 1
                    # 그 위치의 이름 중 하나라도 인접 줄에 있으면 통과. 전부 없으면 경고.
                    if not is_src_list and not any(short(nm) in ctx for nm in names):
                        cand = " / ".join(short(nm) for nm in names)
                        name_warn.append(f"[이름?] {where}  {f}:{ln} 의 심볼은 {cand} 인데 "
                                         f"문서 줄에 어느 것도 없다")
                    if a.verbose:
                        print(f"  통과(노드)   {f}:{ln} = {' / '.join(names)}")
                elif (f, ln) in owns:
                    total["L3 통과(간선)"] += 1
                    if a.verbose:
                        print(f"  통과(간선)   {f}:{ln} = {owns[(f, ln)][0]}")
                elif (f, ln) in flesh:
                    total["L3 통과(멤버·메서드)"] += 1
                    if a.verbose:
                        print(f"  통과(살)     {f}:{ln} = {' / '.join(flesh[(f, ln)][:2])}")
                else:
                    total["L3 근거없음"] += 1
                    unfounded.append(f"[없음] {where}  {f}:{ln} — 소스 줄: {content[ln-1].strip()[:60]}")

    # ── 보고
    print(f"인용 {total['인용']}건 — 문서 {len(a.docs)}개, 기준 저장소 {repo}")
    print(f"  L1  통과 {total['L1 통과']} / 실패 {total['L1 실패']}")
    print(f"  L2  통과 {total['L2 통과']} / 실패 {total['L2 실패']}")
    print(f"  L3  노드 {total['L3 통과(노드)']} · 간선 {total['L3 통과(간선)']}"
          f" · 멤버·메서드 {total['L3 통과(멤버·메서드)']} · 근거없음 {total['L3 근거없음']}")
    if name_warn:
        print(f"  ⚠ 이름 대조 경고 {len(name_warn)}건 (위치는 선언인데 문서 줄에 그 이름이 없음)")
    for x in fails[:10]:
        print("  " + x)
    if len(fails) > 10:
        print(f"  ... 실패 외 {len(fails)-10}건")
    if a.verbose:
        for x in unfounded[:10]:
            print("  " + x)
        for x in name_warn[:5]:
            print("  " + x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
