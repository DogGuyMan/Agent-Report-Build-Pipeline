#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='verify_citations.py']"/>
# 문서에 적힌 file:line 인용이 진짜인지 기계로 판정하는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""verify_citations.py — 문서의 file:line 인용을 기계로 판정한다 (Track C §8, L1/L2/L3).

deep-wiki 가 쓴 위키(또는 facts/*.md, 관찰 보고서)의 인용이 진짜인지를 판정한다.
"경로 존재 확인" 수준의 기성 도구와 달리 L3 — 그 위치에 그 심볼이 실제로 있는가 — 를
codegraph.json 과 결정론적으로 대조한다. 이것이 이 파이프라인의 차별화다.

  L1  파일이 존재하나                 os.path.isfile
  L2  그 줄이 존재하나                줄 수 비교
  L3  그 위치에 그 심볼이 있나        codegraph 노드 + 위치 있는 간선 전부(C-16) + 살(--detail)

**판정은 3값이다 (C-13→C-16).** 통과 / 실패 / 근거 없음.
  C-16 (2026-08-27, C# 파일럿의 산출) — L3 대상은 "소유 간선만" 이 아니라 **file/line 이
  null 이 아닌 간선 전부**다. C++ 은 소유 간선만 위치를 가져 실질 불변이고, C# 은 assoc/depend
  간선 26건이 판정에 들어온다. `--detail`(살 파일)을 주면 멤버·메서드 선언 줄까지 잰다.
  - "근거 없음" = L1·L2 는 통과했으나 codegraph 에 그 위치의 선언이 등록돼 있지 않다.
    메서드 본문 줄, 함수 층(코드그래프 밖), dependency 간선의 위치가 여기 떨어진다.
  - 근거 없음을 통과로 세면 검증이 무의미해지고, 실패로 세면 정상 인용이 전부 실패한다.
    **그대로 3값으로 낸다.** 종료 코드는 실패(L1/L2)가 있을 때만 1 이다.

이름 대조 규칙 — C++ 관찰 보고서 F-2 의 교훈 둘을 그대로 쓴다:
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

# 인용 패턴 — 확장자 화이트리스트로 "3:4" 같은 오탐을 막는다.
# deep-wiki 로컬 규격 (path:line), 백틱/괄호/링크 감싸기 전부 허용, 범위 line-line 허용.
CITE = re.compile(
    r"([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot))"
    r":(\d+)(?:-(\d+))?")


# <include file="docs/codegraph/comments.xml" path="//term[@id='verify_citations.short']"/>
# 이름 대조용 마지막 조각을 남긴다. 중첩과 경로 구분자를 모두 벗긴다.
# 쓰는 것: 없음 · 쓰이는 곳: _stem, build_index
def short(name):
    """이름 대조용 마지막 조각. F-2 규칙 — ## 중첩, :: / . 경로 전부 마지막만."""
    for sep in ("##", "::", "."):
        name = name.split(sep)[-1]
    return name.split("<")[0]


# <include file="docs/codegraph/comments.xml" path="//term[@id='build_index']"/>
# 코드 지도에서 (파일, 줄) 로 찾는 판정 색인을 만든다.
# 쓰는 것: verify_citations.short · 쓰이는 곳: verify_citations.main
def build_index(codegraph):
    """codegraph -> (file,line) 판정 색인. L3 의 대상은 노드 + 소유 간선뿐이다(C-13)."""
    g = json.load(open(codegraph, encoding="utf-8"))
    # ⚠ (file,line) -> 이름은 1:1 이 아니다. 🔵 실측 — StageFSMState.h:42 에 그 줄의 실제
    #   선언(BaseStageFsmState)과 사용 지점을 위치로 갖는 템플릿 인스턴스(IFsmState<Actor>)가
    #   함께 등록돼 있다. C++ F-1 함정(사용 지점 위치)의 1차 코드판이다. 다중값 색인으로 담는다.
    nodes, owns = {}, {}
    for n in g["nodes"]:
        if n.get("file") and n.get("line"):
            nodes.setdefault((n["file"], n["line"]), []).append(n["name"])
    nm = {n["id"]: n["name"] for n in g["nodes"]}
    for e in g["edges"]:
        if e.get("file") and e.get("line"):          # C-16 — 위치 있는 간선 전부
            desc = f"{short(nm.get(e['from'], '?'))} --{e.get('label') or e['kind']}--> {short(nm.get(e['to'], '?'))}"
            owns.setdefault((e["file"], e["line"]), []).append(desc)
    return g, nodes, owns


# <include file="docs/codegraph/comments.xml" path="//term[@id='load_detail_index']"/>
# 원시 분석 파일에서 멤버와 메서드의 선언 줄 색인을 만든다.
# 쓰는 것: members[] · 쓰이는 곳: verify_citations.main
def load_detail_index(path):
    """살 파일의 멤버·메서드 선언 줄 색인. clang-uml(elements)과 roslyn-dump(types) 양쪽을 안다."""
    d = json.load(open(path, encoding="utf-8"))
    idx = {}
    if "elements" in d:                               # clang-uml (C++)
        for el in d["elements"]:
            for kind in ("members", "methods"):
                for m in el.get(kind) or []:
                    loc = m.get("source_location") or {}
                    if loc.get("file") and loc.get("line"):
                        idx.setdefault((loc["file"], loc["line"]), []).append(
                            f"{short(el.get('display_name') or '?')}.{m.get('name')}")
    else:                                             # roslyn-dump (C#)
        for t in d.get("types", []):
            for kind in ("members", "methods"):
                for m in t.get(kind) or []:
                    if m.get("file") and m.get("line"):
                        idx.setdefault((m["file"], m["line"]), []).append(
                            f"{short(t['name'])}.{m.get('name')}")
    return idx


# <include file="docs/codegraph/comments.xml" path="//term[@id='verify_citations.main']"/>
# 인용 검증 도구의 명령줄 진입점. 실패가 있을 때만 종료 코드 1 이다.
# 쓰는 것: build_index, load_detail_index · 쓰이는 곳: 없음
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docs", nargs="+", help="검사할 마크다운 문서")
    ap.add_argument("--repo", required=True, help="인용 경로의 기준 저장소")
    ap.add_argument("--codegraph", required=True)
    ap.add_argument("--detail", help="살 파일(clang-uml/roslyn-dump 원문) — 멤버·메서드 선언 줄까지 잰다")
    ap.add_argument("-v", "--verbose", action="store_true", help="인용 하나하나 출력")
    a = ap.parse_args()

    _, nodes, owns = build_index(a.codegraph)
    flesh = load_detail_index(a.detail) if a.detail else {}
    repo = os.path.abspath(os.path.expanduser(a.repo))

    total = Counter()
    fails, unfounded, name_warn = [], [], []
    line_cache = {}

    def lines_of(path):
        if path not in line_cache:
            try:
                line_cache[path] = open(path, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                line_cache[path] = None
        return line_cache[path]

    for doc in a.docs:
        text = open(doc, encoding="utf-8").read().splitlines()
        for lineno, raw in enumerate(text, 1):
            # ⚠ 이름 대조는 **인접 줄까지** 본다. 🔵 실측 — 산문이 줄바꿈되면 인용은 이 줄에,
            #   심볼 이름은 앞줄에 있다(data.md:29). 한 줄만 보면 정상 문서가 경고로 뜬다.
            ctx = "\n".join(text[max(0, lineno - 2):lineno + 1])
            # ⚠ `<!-- Sources: ... -->` 는 다이어그램 근거 **목록**이지 주장이 아니다.
            #   이름이 없는 것이 정상이므로 이름 대조에서 뺀다(오탐 방지).
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
