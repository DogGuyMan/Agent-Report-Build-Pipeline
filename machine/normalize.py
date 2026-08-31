#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='normalize.py']"/>
# 언어별 분석 도구의 원시 출력을 공통 형식 codegraph.json 으로 바꾸는 도구.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""normalize.py — 언어별 정적 분석 산출물을 codegraph.json(스키마 v2)으로 바꾼다.

  python3 normalize.py --clang-uml <full_class_all.json> --repo <저장소> -o codegraph.json

세 갈래 — C++(clang-uml + clang-doc) · C#(roslyn-dump) · Python(griffe + pycalls).
접기 규칙 R1~R7 과 kind enum 사상이 여기에만 있다. 언어 도구는 원시 사실만 내고
정책은 전부 이 파일이 쥔다.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any, Required, TypedDict, cast

from clang_doc import Symbol, load_clang_doc
from pycalls import PyCallsDump
# 산출물 `codegraph.json` 의 계약은 **여기 하나**다. 이 파일에 다시 적지 않는다.
from codegraph_types import CodeGraph, Edge, EdgeKind, Node

# ── 입력측 형(C++). codegraph.json 계약이 아니라 clang-uml 이 주는 원시 JSON 의 모양이라
#    codegraph_types.py 가 아니라 여기 산다. 실제로 읽는 열쇠만 적었다 —
#    clang-uml 은 이보다 훨씬 많은 열쇠를 내지만 안 읽는 것을 적어 봐야 어긋날 자리만 는다.


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.SourceLocation']"/>
# clang-uml 이 알려주는 '소스 코드 위치'(파일 경로와 줄 번호) 한 칸을 나타내는 타입 정의(TypedDict).
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.UmlIdentity, machine.normalize.UmlMember, machine.normalize._doc_element
class SourceLocation(TypedDict, total=False):
    """clang-uml 의 `source_location`. 남의 헤더가 아니라 이 저장소의 첫 사용 지점을
    가리키는 버릇이 있다. `is_first_party` 의 거름망 세 겹이 그것 때문이다."""

    file: str
    line: int


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.UmlMember']"/>
# clang-uml 이 클래스의 멤버 변수 하나를 표현하는 JSON 조각을 파이썬에서 다룰 때 쓰는 자료형(TypedDict)이다. 이 자료 자체는 아무 동작도 하지 않고, 필드 두 개(name, source_location)가 있다는 약속만 적어 둔 것이다.
# 쓰는 것: machine.normalize.SourceLocation · 쓰이는 곳: machine.normalize.UmlElement
class UmlMember(TypedDict, total=False):
    """`elements[].members[]` 한 칸. 소유 간선의 근거 위치가 여기서 나온다."""

    name: str
    source_location: SourceLocation


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.UmlTemplateParam']"/>
# clang-uml 요소의 템플릿 매개변수 한 칸을 나타내는 타입 정의(TypedDict).
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.UmlElement
class UmlTemplateParam(TypedDict, total=False):
    """`elements[].template_parameters[]` 한 칸. R5 투과가 `type` 을 따라 내려간다."""

    type: str


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.UmlIdentity']"/>
# clang-uml 이 낸 타입 정보와 clang-doc 이 낸 타입 정보 둘 다에 공통으로 있는 최소한의 항목(이름, 표시 이름, 네임스페이스, 소스 위치)만 모아 둔 자료형이다. 서로 다른 두 도구의 출력을 같은 잣대로 비교하려고 만든 '교집합' 모양이다.
# 쓰는 것: machine.normalize.SourceLocation · 쓰이는 곳: machine.normalize.UmlElement
class UmlIdentity(TypedDict, total=False):
    """1차 판정에 필요한 최소한 — clang-uml 의 element 와 clang-doc 심볼의 교집합이다.

    `_doc_element` 가 clang-doc 심볼을 이 꼴로 옮겨 `is_first_party` 에 그대로 태운다.
    `name` 만 필수다 — 이름 없이는 어느 판정도 못 하고, 두 수집기 모두 낸다.
    """

    name: Required[str]
    display_name: str
    namespace: str
    source_location: SourceLocation


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.UmlElement']"/>
# clang-uml이 낸 JSON의 elements[] 배열 한 칸을 표현하는 타입 정의(TypedDict)다. C++ 클래스 하나에 대응한다.
# 쓰는 것: machine.normalize.UmlIdentity, machine.normalize.UmlMember, machine.normalize.UmlTemplateParam · 쓰이는 곳: 없음
class UmlElement(UmlIdentity, total=False):
    """`elements[]` 한 칸. 위의 교집합에 clang-uml 만 갖는 열쇠를 더한 것이다."""

    id: Required[str]
    type: str
    is_abstract: bool
    members: list[UmlMember]
    template_parameters: list[UmlTemplateParam]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.UmlRelationship']"/>
# clang-uml 이 알려주는 두 타입 사이의 관계(관계선) 한 칸을 나타내는 타입 정의(TypedDict).
# 쓰는 것: 없음 · 쓰이는 곳: 없음
class UmlRelationship(TypedDict, total=False):
    """`relationships[]` 한 칸. `type` 은 clang-uml 의 낱말이라 `CLANG_UML_KIND` 를 거쳐야 한다."""

    type: Required[str]
    source: Required[str]
    destination: Required[str]
    label: str


# ── C++ 1차 코드로 볼 네임스페이스. 경로가 아니라 네임스페이스가 기준이다.
#    std:: 타입의 source_location 은 표준 헤더가 아니라 이 저장소의 첫 사용 지점을
#    가리킨다. 경로로 거르면 남의 타입을 1차로 오인한다.
CPP_FIRST_PARTY_NS = ("SJH", "TopdownShooter")

# ── clang-uml 의 낱말과 codegraph enum 의 낱말이 겹치지만 뜻이 다르다.
#    항등 매핑을 쓰면 간선이 조용히 틀린 칸에 들어가고 오류도 나지 않는다.
CLANG_UML_KIND: dict[str, EdgeKind] = {
    "aggregation": "composition",   # 값 멤버 (std::string detail)  -> UML 합성
    "association": "aggregation",   # 포인터·참조 멤버 (Actor* mOwner) -> UML 집약
    "dependency": "dependency",
    "instantiation": "instantiation",
    "friendship": "friendship",
    # "extension" 은 대상 노드의 is_abstract 를 봐야 갈린다 -> 아래 2-패스
    # "containment" 는 8종 enum 에 자리가 없어 버린다. 선언 위치 관계이고 방향이
    #   안쪽->바깥쪽이라 dependency 로 흡수하면 역방향 화살표가 생겨 오독을 부른다.
    #   버리되 수는 로그로 보고한다.
}

# ── R7. clang-uml 은 원시 타입을 element 로 승격하지 않아 C++ 에서는 걸리지 않는다.
#    다른 도구가 들어올 때를 위한 방어다.
CPP_PRIMITIVES = {
    "void", "bool", "char", "signed char", "unsigned char", "wchar_t", "char8_t",
    "char16_t", "char32_t", "short", "int", "long", "long long", "float", "double",
    "long double", "size_t", "ptrdiff_t", "nullptr_t",
    "unsigned", "unsigned int", "unsigned short", "unsigned long", "unsigned long long",
}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.git_commit']"/>
# 어떤 저장소 폴더가 지금 가리키는 git 커밋을 짧은 해시 문자열로 알려주는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize._assemble
def git_commit(repo: str) -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.module_of']"/>
# C++ 소스 파일 경로를 보고 그 파일이 속한 모듈(폴더 단위 묶음) 이름을 정하는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.merge_clang_doc, machine.normalize.merge_py_calls, machine.normalize.normalize_cpp, machine.normalize.normalize_python, machine.test_normalize.test_cpp_module_of (+1)
def module_of(path: str | None) -> str | None:
    """모듈 경계 = 폴더 트리. C# 쪽(`cs_module_of`)과 축이 같다.

    viz/src/render/renderer.h -> "render"      apps/TopdownShooter/main.cpp -> "apps/TopdownShooter"
    """
    if not path:
        return None
    parts = path.split("/")
    if parts[0] == "src" and len(parts) > 2:
        return parts[1]
    if parts[0] == "apps" and len(parts) > 2:
        return f"apps/{parts[1]}"
    return parts[0]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.load_clang_uml']"/>
# clang-uml 이라는 외부 분석 도구가 만든 JSON 결과 파일을 읽어서 세 부분으로 나눠주는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.main
def load_clang_uml(path: str) -> tuple[list[UmlElement], list[UmlRelationship], dict[str, Any]]:
    d: dict[str, Any] = json.load(open(path, encoding="utf-8"))
    return d["elements"], d["relationships"], d.get("metadata", {})


# ── 선언 위치가 저장소 안이어도 1차가 아닌 것들.
#    std 는 첫 사용 지점 함정 때문에 반드시 있어야 한다. 나머지는 빌드가 만든 파일이다.
GENERATED_MARKERS = ("/build/", "/vcpkg_installed/", "autogen", "/cmake-build", "/.venv/")
NEVER_FIRST_PARTY_NS = ("std", "__gnu_cxx", "__cxxabiv1")


# 이 타입이 우리 코드인지 가른다. 네임스페이스 허용목록이 먼저, 없으면 선언 위치로 본다.
# 쓰는 것: 없음 · 쓰이는 곳: normalize_cpp
# 그 줄이 이 이름을 **정의**하는가. 전방 선언(`class QWidget;`)과 사용 줄은 아니다.
DEFINES_RE_CACHE: dict[str, re.Pattern[str]] = {}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.defines_at']"/>
# clang-uml 이 알려준 파일:줄이 실제로 그 타입을 정의하는 줄인지(전방 선언이나 그냥 사용하는 줄이 아니라) 확인하는 함수.
# 쓰는 것: machine.normalize.DEFINES_RE_CACHE · 쓰이는 곳: machine.normalize.is_first_party
def defines_at(repo: str, rel_file: str | None, line_no: int | None, name: str) -> bool:
    """`source_location` 이 가리키는 줄이 실제로 그 타입을 정의하는지 본다.

    clang-uml 이 주는 위치에는 정의 줄뿐 아니라 전방 선언(`class QWidget;`)과 사용 줄
    (`cv::Mat3b img;` · 매개변수 목록)이 섞인다. 정의만 1차로 인정한다.
    """
    if not (rel_file and line_no):
        return False
    # 중첩 타입의 구분자는 `::` 가 아니라 `##` 다(node_name 주석 참조). 둘 다 벗긴다.
    base = name.replace("##", "::").split("::")[-1].split("<")[0].strip()
    if not base:
        return False
    path = rel_file if os.path.isabs(rel_file) else os.path.join(repo, rel_file)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for i, ln in enumerate(fh, 1):
                if i == line_no:
                    src = ln.rstrip("\n")
                    break
            else:
                return False
    except OSError:
        return False
    stripped = src.strip()
    if stripped.endswith(";"):          # 전방 선언과 멤버 선언
        return False
    key = base
    rx = DEFINES_RE_CACHE.get(key)
    if rx is None:
        rx = re.compile(r"\b(?:class|struct|enum(?:\s+class)?|union)\s+(?:\w+\s+)*"
                        + re.escape(base) + r"\b")
        DEFINES_RE_CACHE[key] = rx
    return bool(rx.search(stripped))


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.tracked_set']"/>
# git 이 실제로 추적(관리)하고 있는 파일들의 절대경로 집합을 구하는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_cpp
def tracked_set(repo: str) -> set[str] | None:
    """git 이 추적하는 파일 집합. 1차 판정의 급소다 — 남의 헤더는 추적되지 않는다."""
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return {os.path.abspath(os.path.join(repo, f)) for f in r.stdout.split("\n") if f}

# <include file="machine/comments.xml" path="//term[@id='machine.normalize.is_first_party']"/>
# C++ 에서 찾아낸 타입(클래스 등) 하나가 '우리가 직접 쓴 코드'인지, 아니면 Qt·OpenCV·표준 라이브러리처럼 '남이 만든 코드'인지 참/거짓으로 가려내는 함수다.
# 쓰는 것: machine.normalize.defines_at · 쓰이는 곳: machine.normalize.merge_clang_doc, machine.normalize.normalize_cpp, machine.test_declmap.test_first_party_accepts_tracked_global_namespace_type, machine.test_declmap.test_first_party_rejects_qt_type_seen_inside_repo, machine.test_normalize.test_first_party_accepts_nested_type (+8)
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
def is_first_party(el: UmlIdentity, repo: str | None = None,
                   ns: tuple[str, ...] = CPP_FIRST_PARTY_NS,
                   tracked: set[str] | None = None) -> bool:
    """1차 코드 판정. 두 갈래다.

    ① 네임스페이스 허용목록 — 빠른 길. 저장소가 자기 네임스페이스를 쓰면 이것으로 끝난다.
    ② 선언 위치가 저장소 안 — 전역 네임스페이스를 쓰는 코드를 위한 길.

    ②에는 거름망이 세 겹 있어야 한다. clang-uml 의 `source_location` 은 남의 헤더가 아니라
    이 저장소의 첫 사용 지점을 가리키기 때문이다. 그래서
      · std 계열은 NEVER_FIRST_PARTY_NS 로 막고,
      · 빌드가 만든 파일(Qt autogen 의 Ui::*)은 GENERATED_MARKERS 로 막고,
      · 나머지는 git 추적 여부로 막는다 — Qt 의 QWidget, OpenCV 의 cv::Mat 이 여기 걸린다.
    """
    root = (el.get("namespace") or "").split("::")[0]
    if root in ns:
        return True
    if not repo:
        return False
    if root in NEVER_FIRST_PARTY_NS:
        return False
    loc: SourceLocation = el.get("source_location") or {}
    src = loc.get("file") or ""
    if not src:
        return False
    abs_src = src if os.path.isabs(src) else os.path.join(repo, src)
    abs_src = os.path.abspath(abs_src)
    if not abs_src.startswith(os.path.abspath(repo) + os.sep):
        return False
    if any(m in abs_src for m in GENERATED_MARKERS):
        return False
    # clang-uml 은 Qt·OpenCV 타입의 위치로도 이 저장소의 첫 사용 지점을 준다. 이 검사가
    # 없으면 남의 타입이 1차로 새어 PageRank 상위에 올라온다. git 이 추적하지 않는
    # 파일은 우리 코드가 아니다.
    if tracked is not None and abs_src not in tracked:
        return False
    # 마지막 겹 — 그 줄이 실제로 이 타입을 **정의**하는가. 전방 선언과 사용 줄은 뺀다.
    return defines_at(repo, src, loc.get("line"),
                      el.get("name") or el.get("display_name") or "")


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.external_group']"/>
# 저장소 바깥(외부 라이브러리)의 C++ 타입을 어떤 그룹 이름 하나로 뭉뚱그리는 함수 (R2 규칙: 외부 하나 = 노드 하나).
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_cpp
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
def external_group(el: UmlElement) -> str:
    """R2 — 외부 하나 = 노드 하나. 입도는 라이브러리·서브모듈 이름이다."""
    root = (el.get("namespace") or "").split("::")[0]
    if root == "std":
        return "(STL) std"
    if root:
        return root
    return "(기타) " + el.get("name", "?")


# ── R5 투과 대상. 목록으로 고정한다.
#    "std 네임스페이스의 템플릿 전부" 로 일반화하면 basic_string 까지 투과해
#    `(STL) std` 외부 노드가 통째로 사라지고 끝점 해소 실패가 크게 는다.
STD_TRANSPARENT = {
    "vector", "unordered_map", "unique_ptr", "array", "shared_ptr", "weak_ptr",
    "map", "set", "unordered_set", "list", "deque", "pair", "tuple",
    "optional", "initializer_list",
}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.is_transparent_wrapper']"/>
# vector 나 unique_ptr 처럼 '속에 다른 타입을 담기만 하는 그릇' 타입인지 판단하는 함수 (R5 규칙: 그릇은 노드로 만들지 않고 통과시킨다).
# 쓰는 것: machine.normalize.STD_TRANSPARENT · 쓰이는 곳: machine.normalize.normalize_cpp, machine.test_normalize.test_r5_cpp_is_list_based_not_all_std_templates, machine.test_normalize.test_r5_cpp_requires_std_namespace
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
def is_transparent_wrapper(el: UmlElement) -> bool:
    """R5 — 컨테이너·스마트포인터는 노드로 만들지 않고 투과시킨다.

    R5 를 빼면 사용자 코드끼리의 소유 간선이 unique_ptr/vector 를 2홉으로 거쳐야만 보인다.
    """
    return (el.get("namespace") or "").split("::")[0] == "std" and el.get("name") in STD_TRANSPARENT


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.member_location']"/>
# 두 타입 사이의 관계(간선)가 어느 멤버 변수 선언 때문에 생겼는지 그 위치(파일, 줄)를 찾는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_cpp
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
def member_location(src_el: UmlElement | None, label: str | None) -> tuple[str | None, int | None]:
    """간선의 근거 위치. label(멤버 이름)로 members[] 를 정확히 찾는다.

    문자열 탐색이 아니라 구조 조회다. 소유 간선만 멤버를 가리킬 수 있고, 나머지 종류
    (dependency/extension/instantiation/friendship)는 가리킬 멤버가 없어 위치가 null 이다.
    검증기는 그것을 "근거 없음" 으로 낸다 — 2값이 아니라 3값이다.
    """
    if not src_el or not label:
        return None, None
    members: list[UmlMember] = src_el.get("members") or []
    hits = [m for m in members if m.get("name") == label]
    if len(hits) != 1:
        return None, None
    loc: SourceLocation = hits[0].get("source_location") or {}
    return loc.get("file"), loc.get("line")

# <include file="machine/comments.xml" path="//term[@id='machine.normalize.node_name']"/>
# clang-uml 요소 하나에 붙일 노드 이름을 고르는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_cpp
# ! 이거 UmlElement에 넣어도 되는 함수 아니야? 왜 자유함수.
def node_name(el: UmlElement) -> str:
    """중첩 타입의 name 은 구분자가 :: 가 아니라 ## 이고 바깥 클래스가 namespace 에 없다."""
    return el.get("display_name") or el.get("name")

# <include file="machine/comments.xml" path="//term[@id='machine.normalize.doc_qualified_name']"/>
# clang-doc 이 찾아낸 심볼(함수·클래스 등)의 완전한 이름(네임스페이스 포함)을 만드는 함수.
# 쓰는 것: machine.clang_doc.Symbol · 쓰이는 곳: machine.normalize.merge_clang_doc
# ! 이거 clang_doc에 넣어도 되는 함수 아니야? 왜 자유함수.
def doc_qualified_name(sym: Symbol) -> str:
    """clang-doc 심볼의 완전 수식 이름. clang-uml 의 `display_name` 과 같은 축으로 맞춘다.

    두 수집기의 노드를 겹쳐 세지 않으려면 신원이 같은 낱말이어야 한다.
    """
    return f"{sym['namespace']}::{sym['name']}" if sym["namespace"] else sym["name"]

# <include file="machine/comments.xml" path="//term[@id='machine.normalize._doc_element']"/>
# clang-doc 심볼 하나를 1차 코드 판정 함수(is_first_party)가 읽을 수 있는 모양으로 옮겨주는 함수.
# 쓰는 것: machine.clang_doc.Symbol, machine.normalize.SourceLocation · 쓰이는 곳: machine.normalize.merge_clang_doc
# ! 이거 Symbol에 넣어도 되는 함수 아니야? 왜 자유함수.
def _doc_element(sym: Symbol) -> UmlIdentity:
    """clang-doc 심볼을 `is_first_party` 가 읽는 꼴로 옮긴다.

    판정을 흉내 내지 않고 그대로 태운다. 세 겹 거름망(네임스페이스 허용목록 -> git 추적
    -> `defines_at`)을 우회하면 Qt 의 QWidget 과 OpenCV 의 cv::Mat 이 1차로 샌다.
    """
    return {"namespace": sym["namespace"], "name": sym["name"],
            "source_location": {"file": sym["file"], "line": sym["line"]}}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.merge_clang_doc']"/>
# clang-doc가 찾아낸 C++ 심볼들을 clang-uml이 이미 만들어 둔 노드 표에 합쳐 넣는 함수다.
# 쓰는 것: machine.normalize.module_of, machine.normalize.is_first_party, machine.normalize.doc_qualified_name, machine.normalize._doc_element · 쓰이는 곳: machine.normalize.normalize_cpp
def merge_clang_doc(nodes: dict[str, Node], doc_symbols: Sequence[Symbol] | None,
                    repo: str, tracked: set[str] | None, stats: Counter[str]) -> None:
    """clang-doc 의 심볼을 clang-uml 이 만든 노드 표에 합친다.

    clang-uml 은 관계의 종류(합성/집약/의존)를 알고 clang-doc 은 심볼 전량(자유 함수·
    시그니처·저자 주석)을 안다. 그래서

      · 노드는 합집합 — clang-uml 이 내지 않는 자유 함수가 여기서 들어온다.
      · 같은 이름이면 노드를 늘리지 않고 위치만 clang-doc 것으로 간다. clang-uml 의
        `source_location` 은 이 저장소의 첫 사용 지점을 가리키는 버릇이 있다.
      · 간선은 손대지 않는다. clang-doc 에는 관계 분류가 없다.

    1차가 아닌 심볼은 외부 노드로 접지 않고 버린다. clang-doc 이 간선을 만들지 않으므로
    접어 봐야 `_assemble` 의 R1(전이 확장 금지)이 곧바로 지우고, `collapsed_from` 만
    부풀어 facts/external.md 가 시끄러워진다.
    """
    by_name = {n["name"]: nid for nid, n in nodes.items() if n["kind"] != "external"}
    for sym in doc_symbols or ():
        if not is_first_party(_doc_element(sym), repo, tracked=tracked):
            stats["clang-doc 1차 아님(버림)"] += 1
            continue
        qname = doc_qualified_name(sym)
        hit = by_name.get(qname)
        node: Node
        if hit is not None:
            node = nodes[hit]
            node["file"], node["line"] = sym["file"], sym["line"]
            node["module"] = module_of(sym["file"])
            stats["clang-doc 로 위치 갱신"] += 1
        else:
            nid = "C%d" % (len(nodes) + 1)
            node = nodes[nid] = {
                "id": nid, "name": qname, "kind": sym["kind"],
                "module": module_of(sym["file"]),
                "file": sym["file"], "line": sym["line"],
            }
            by_name[qname] = nid
            stats["clang-doc 신규 노드 " + sym["kind"]] += 1
        # 빈 값은 키 자체를 만들지 않는다 — clang-doc 을 안 쓰는 저장소의 산출물이
        # 빈 문자열 두 개 때문에 통째로 달라지면 골든 대조가 무의미해진다.
        if sym["signature"]:
            node["signature"] = sym["signature"]
        if sym["doc"]:
            node["doc"] = sym["doc"]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.normalize_cpp']"/>
# clang-uml 이 뽑아낸 C++ 클래스와 관계 목록을 이 도구의 공통 코드 지도 형식으로 바꾸는 함수다.
# 쓰는 것: machine.normalize.module_of, machine.normalize.tracked_set, machine.normalize.is_first_party, machine.normalize.external_group, machine.normalize.is_transparent_wrapper (+4) · 쓰이는 곳: machine.normalize.main, machine.test_normalize.test_clang_doc_adds_function_nodes, machine.test_normalize.test_clang_doc_carries_signature_and_author_comment, machine.test_normalize.test_clang_doc_does_not_add_edges, machine.test_normalize.test_clang_doc_symbols_go_through_is_first_party (+2)
def normalize_cpp(elements: list[UmlElement], relationships: list[UmlRelationship],
                  repo: str, source_tool: str,
                  doc_symbols: Sequence[Symbol] = ()) -> tuple[CodeGraph, Counter[str]]:
    tracked = tracked_set(repo)
    by_id = {e["id"]: e for e in elements}
    by_display = {e.get("display_name"): e for e in elements}
    stats: Counter[str] = Counter()

    # ── 1패스: 노드를 정한다. 투과 래퍼는 노드가 되지 않는다(R5).
    #    외부는 R2 로 접는다. 접힌 원본은 추적을 위해 남긴다.
    node_id: dict[str, str] = {}          # element id -> codegraph node id
    nodes: dict[str, Node] = {}           # codegraph node id -> Node
    collapsed: defaultdict[str, list[str]] = defaultdict(list)
    wrappers: set[str] = set()

    for e in elements:
        if is_transparent_wrapper(e):
            wrappers.add(e["id"]); stats["R5 투과 래퍼"] += 1
            continue
        if node_name(e) in CPP_PRIMITIVES:
            stats["R7 원시 타입 제외"] += 1
            continue
        if is_first_party(e, repo, tracked=tracked):
            nid = "C%d" % (len(nodes) + 1)
            loc: SourceLocation = e.get("source_location") or {}
            nodes[nid] = {
                "id": nid, "name": node_name(e),
                "kind": "enum" if e.get("type") == "enum" else "class",
                "module": module_of(loc.get("file")),
                "file": loc.get("file"), "line": loc.get("line"),
            }
            node_id[e["id"]] = nid
            stats["1차 노드"] += 1
        else:
            g = external_group(e)
            nid = "X:" + g
            if nid not in nodes:
                nodes[nid] = {"id": nid, "name": g, "kind": "external",
                              "module": "__external__", "file": None, "line": None,
                              "collapsed_from": []}
            node_id[e["id"]] = nid
            collapsed[nid].append(node_name(e))
            stats["외부 원본 타입"] += 1

    # ── 1.5패스: clang-doc 합치기. 노드만 늘리고 간선은 손대지 않는다.
    #    간선 패스보다 먼저 와야 한다 — 뒤에 오면 위치 갱신이 `_assemble` 의 모듈 유도에
    #    반영되지 않아 모듈 목록이 옛 위치 기준으로 굳는다.
    merge_clang_doc(nodes, doc_symbols, repo, tracked, stats)

    # ── R5 투과 해소. 래퍼로 가는 간선은 래퍼의 템플릿 인자로 갈아탄다.
    def resolve(eid: str, depth: int = 0) -> list[str]:
        """element id -> codegraph node id 목록. 래퍼면 인자로 내려간다."""
        if depth > 4:
            return []
        if eid in node_id:
            return [node_id[eid]]
        el = by_id.get(eid)
        if not el or eid not in wrappers:
            return []
        out: list[str] = []
        params: list[UmlTemplateParam] = el.get("template_parameters") or []
        for tp in params:
            t = tp.get("type")
            tgt = by_display.get(t)
            if tgt is not None:
                out.extend(resolve(tgt["id"], depth + 1))
        return out

    # ── 2패스: 간선. extension 은 대상 노드의 is_abstract 를 봐야 갈리므로
    #    노드를 전량 적재한 뒤에 돌아야 한다(스트리밍 불가).
    edges: dict[tuple[str, str, str], Edge] = {}
    for r in relationships:
        t = r["type"]
        src_el = by_id.get(r["source"])
        dst_el = by_id.get(r["destination"])
        if t == "containment":
            stats["containment 버림(자리 없음)"] += 1
            continue
        if t == "extension":
            kind = "realization" if (dst_el is not None and dst_el.get("is_abstract")) else "inheritance"
        else:
            kind = CLANG_UML_KIND.get(t)
            if kind is None:
                stats[f"알 수 없는 type: {t}"] += 1
                continue

        srcs = resolve(r["source"])
        dsts = resolve(r["destination"])
        if not srcs or not dsts:
            stats["끝점 해소 실패"] += 1
            continue

        f, ln = member_location(src_el, r.get("label"))
        for s in srcs:
            for d in dsts:
                if s == d:
                    stats["자기참조 버림"] += 1
                    continue
                # R4 — 간선은 사용자 코드 -> 외부 단방향만.
                s_ext = nodes[s]["kind"] == "external"
                d_ext = nodes[d]["kind"] == "external"
                if s_ext:
                    stats["R4 외부발 간선 버림"] += 1
                    continue
                key = (s, d, kind)
                if key in edges:
                    edges[key]["occurrences"] = edges[key].get("occurrences", 1) + 1
                    stats["중복 간선 접음"] += 1
                    continue
                edges[key] = {"from": s, "to": d, "kind": kind,
                              "label": r.get("label"), "file": f, "line": ln}
                if d_ext:
                    edges[key]["constraint"] = False   # R6 — 섬으로 가는 간선

    for nid, names in collapsed.items():
        nodes[nid]["collapsed_from"] = sorted(set(names))

    return _assemble(nodes, edges, stats, language="cpp", source_tool=source_tool, repo=repo)


# <include file="machine/comments.xml" path="//term[@id='machine.normalize._assemble']"/>
# C++·C#·Python 세 언어별 파서가 각자 다 만든 노드·간선 데이터를 마지막에 한 곳으로 모아 최종 codegraph.json 모양(딕셔너리)으로 포장하는 '마무리' 함수다. 세 파서 모두 마지막에는 이 함수를 거쳐 나간다.
# 쓰는 것: machine.normalize.git_commit · 쓰이는 곳: machine.normalize.normalize_cpp, machine.normalize.normalize_csharp, machine.normalize.normalize_python
def _assemble(nodes: dict[str, Node], edges: dict[tuple[str, str, str], Edge],
              stats: Counter[str], *, language: str, source_tool: str,
              repo: str) -> tuple[CodeGraph, Counter[str]]:
    """언어 공통 꼬리 — R1 제거, 모듈 의존 유도, 최종 dict 조립.

    세 언어 파서(normalize_cpp / normalize_csharp / normalize_python)가 여기로 수렴한다.

    `modules[].depends_on` 은 클래스 간선에서 유도한다. CMake 타겟 층(.dot)과는 입도가
    다르고 C# 에는 대응물이 없어 조인하지 않는다.
    이것은 링크 의존이 아니라 타입 의존이다. .dot 의 PUBLIC/INTERFACE/PRIVATE 축과는
    다른 것이므로 같은 것으로 읽지 말 것.
    """
    # R1 — 전이 확장 금지. 사용자 코드가 실제로 닿지 않는 외부 노드는 뺀다.
    touched = {e["to"] for e in edges.values()}
    dropped = [nid for nid, n in nodes.items() if n["kind"] == "external" and nid not in touched]
    for nid in dropped:
        stats["R1 로 제거된 외부 노드"] += 1
        del nodes[nid]

    modules = sorted({n["module"] for n in nodes.values() if n["module"] and n["kind"] != "external"})
    mod_dep: defaultdict[str, set[str]] = defaultdict(set)
    for e in edges.values():
        a, b = nodes[e["from"]], nodes[e["to"]]
        # 외부 섬은 모듈 그래프에 넣지 않는다(R3). 넣으면 모든 모듈이 __external__ 로 향해 노이즈가 된다.
        if b["kind"] == "external" or not a["module"] or not b["module"]:
            continue
        if a["module"] != b["module"]:
            mod_dep[a["module"]].add(b["module"])
            stats["모듈 간 의존"] += 1

    return {
        "schema_version": 2,
        "language": language,
        "platform": sys.platform,
        "source_tool": source_tool,
        "repo_commit": git_commit(repo),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "modules": [{"id": m, "depends_on": sorted(mod_dep.get(m, ()))} for m in modules],
    }, stats


# ═══════════════════════════════ C# (roslyn-dump.json) ═══════════════════════════════

# ── 입력측 형(C#). `machine/roslyn-dump/Program.cs` 의 레코드를 그대로 옮겼다.
#    C# 쪽이 `string?` 로 내는 자리는 여기서도 `str | None` 이다 — 다만 `name` 만은 str 로
#    적는다. 이름 없는 타입 레코드는 형식이 허용해도 실제로 나오지 않고, 노드 이름이 되는
#    자리라 None 을 받으면 codegraph.json 계약(`Node.name: str`)이 깨진다.


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.RoslynCompilation']"/>
# C# 분석 결과(roslyn-dump.json) 안의 '컴파일 요약 정보'를 나타내는 타입 정의(TypedDict). 참조 집합이 제대로 잡혔는지 확인하는 F5 게이트가 이걸 본다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.RoslynDump
class RoslynCompilation(TypedDict):
    """`compilation` — F5 게이트가 보는 곳."""

    assembly: str
    errors: int
    unresolved_types: int


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.RoslynType']"/>
# C# 타입(클래스·구조체·열거형 등) 하나를 나타내는 타입 정의(TypedDict). 1차 코드 판정은 file 유무가 아니라 assembly 값으로 한다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.RoslynDump
class RoslynType(TypedDict, total=False):
    """`types[]` 한 칸. 1차 판정은 file 유무가 아니라 `assembly` 다."""

    id: Required[str]
    name: Required[str]
    kind: Required[str | None]
    assembly: str | None
    file: Required[str | None]
    line: Required[int | None]
    generic_def: str | None
    type_args: list[str]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.RoslynRelation']"/>
# C# 두 타입 사이의 관계(상속·의존 등) 하나를 나타내는 타입 정의(TypedDict). 필드 origin 과 attrs 는 C# 만 갖는 정보다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.RoslynDump
class RoslynRelation(TypedDict, total=False):
    """`relations[]` 한 칸. `origin` 과 `attrs` 는 C# 만 갖는 비대칭 기록이다."""

    kind: Required[str]
    src: Required[str]
    dst: Required[str]
    member: str | None
    attrs: list[str] | None
    is_enum_member: Required[bool]
    origin: str | None
    file: str | None
    line: int | None


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.RoslynDump']"/>
# roslyn-dump.json 파일 전체의 모양을 나타내는 최상위 타입 정의(TypedDict).
# 쓰는 것: machine.normalize.RoslynCompilation, machine.normalize.RoslynType, machine.normalize.RoslynRelation · 쓰이는 곳: 없음
class RoslynDump(TypedDict, total=False):
    """`roslyn-dump.json` 통째. `tool` 은 없을 수 있어 `main` 이 기본값을 준다."""

    tool: str
    compilation: Required[RoslynCompilation]
    types: Required[list[RoslynType]]
    relations: Required[list[RoslynRelation]]


# R5 — C# 투과 래퍼. generic_def(정의 이름) 기준. "[]" 는 배열이다 — roslyn-dump 가
#   배열을 제네릭과 같은 자리로 표현한다.
#   인터페이스(IReadOnlyDictionary 등)는 넣지 않는다. 투과 대상은 구상 컨테이너뿐이다.
CS_TRANSPARENT_DEFS = {
    "System.Collections.Generic.List`1", "System.Collections.Generic.Dictionary`2",
    "System.Collections.Generic.HashSet`1", "System.Collections.Generic.Queue`1",
    "System.Collections.Generic.Stack`1", "System.Collections.Generic.LinkedList`1",
    "System.Nullable`1", "[]",
    # 튜플도 컨테이너다 — (float, float) 필드는 원소로 접힌다.
    "System.ValueTuple`1", "System.ValueTuple`2", "System.ValueTuple`3", "System.ValueTuple`4",
    "System.ValueTuple`5", "System.ValueTuple`6", "System.ValueTuple`7", "System.ValueTuple`8",
}

# R7 — 원시 타입과 암묵적 기반 타입. roslyn-dump 는 이름을 키워드("string")가 아니라
# 정식 이름("System.String")으로 내므로 여기서도 정식 이름으로 맞춘다.
CS_R7 = {
    "System.Object", "System.ValueType", "System.Enum", "System.Void",
    "System.String", "System.Boolean", "System.Char", "System.Decimal",
    "System.Single", "System.Double",
    "System.SByte", "System.Byte", "System.Int16", "System.UInt16",
    "System.Int32", "System.UInt32", "System.Int64", "System.UInt64",
    "System.IntPtr", "System.UIntPtr",
}

# kind 사상. C++ 쪽과 달리 낱말 어긋남이 없다 — roslyn-dump 형식을 우리가 정했기 때문이다.
CS_KIND: dict[str, EdgeKind] = {"inherit": "inheritance", "realize": "realization",
                                "assoc": "association", "depend": "dependency"}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.cs_module_of']"/>
# C# 소스 파일 경로에서 모듈(폴더 단위 묶음) 이름을 정하는 함수. module_of 의 C# 버전.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_csharp, machine.test_normalize.test_cs_module_of
def cs_module_of(path: str | None) -> str | None:
    """모듈 경계 = 폴더 트리. `module_of`(C++)와 축이 같다."""
    if not path:
        return None
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "Assets" and parts[1] == "@Scripts":
        return parts[2] if len(parts) > 3 else "@Scripts"
    if len(parts) >= 2 and parts[0] == "Assets" and parts[1] == "@Editors":
        return "@Editors"
    return parts[0]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.cs_asm2pkg']"/>
# C# 어셈블리(assembly) 이름을 유니티 패키지 이름으로 바꿔주는 사전(dict)을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_csharp
def cs_asm2pkg(repo: str) -> dict[str, str]:
    """어셈블리 이름 -> 패키지 id. `Library/PackageCache/<pkg>@<hash>/**/*.asmdef` 의
    name 이 어셈블리이고, 경로의 `@` 앞이 패키지다."""
    import glob as _glob
    out: dict[str, str] = {}
    base = os.path.join(repo, "Library/PackageCache")
    for a in _glob.glob(os.path.join(base, "*", "**", "*.asmdef"), recursive=True):
        pkg = os.path.relpath(a, base).split("/")[0].split("@")[0]
        try:
            asmdef: dict[str, Any] = json.load(open(a, encoding="utf-8-sig"))
            out[asmdef["name"]] = pkg
        except Exception:
            pass
    # precompiled DLL(Newtonsoft.Json 등)은 .asmdef 가 없다 — 파일명으로 보충한다.
    # .asmdef 가 이미 준 이름은 덮어쓰지 않는다.
    for d in _glob.glob(os.path.join(base, "*", "**", "*.dll"), recursive=True):
        pkg = os.path.relpath(d, base).split("/")[0].split("@")[0]
        out.setdefault(os.path.splitext(os.path.basename(d))[0], pkg)
    return out


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.cs_external_group']"/>
# C# 외부(우리 코드가 아닌) 타입을 패키지 이름 하나로 묶는 함수. external_group 의 C# 버전 (R2 규칙).
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_csharp, machine.test_normalize.test_cs_external_group_naming
def cs_external_group(asm: str | None, asm2pkg: dict[str, str]) -> str:
    """R2 — 외부 하나 = 노드 하나. 입도는 패키지 이름."""
    import re as _re
    if not asm:
        return "(기타)"
    if asm in asm2pkg:
        return asm2pkg[asm]
    if asm.startswith("UnityEditor"):
        return "(엔진 에디터) UnityEditor"
    m = _re.fullmatch(r"UnityEngine\.(\w+)Module", asm)
    if m and m.group(1) != "Core":
        return "com.unity.modules." + m.group(1).lower()
    if asm.startswith("UnityEngine") or asm == "UnityEngine":
        return f"(엔진) {asm}"
    if asm in ("netstandard", "mscorlib") or asm.startswith("System"):
        return "(BCL) netstandard"
    for known, pkg in asm2pkg.items():                       # BakingSheet.Samples* -> 상위 패키지
        if asm.startswith(known + "."):
            return pkg
    return f"(벤더링) {asm}"


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.normalize_csharp']"/>
# roslyn-dump가 뽑아낸 C# 타입·관계 정보를 이 프로젝트 공통의 코드 지도(노드+간선) 형태로 바꾸는 함수다.
# 쓰는 것: machine.normalize._assemble, machine.normalize.cs_module_of, machine.normalize.cs_asm2pkg, machine.normalize.cs_external_group · 쓰이는 곳: machine.normalize.main
def normalize_csharp(dump: RoslynDump, repo: str) -> tuple[CodeGraph, Counter[str]]:
    # F5 게이트 — 참조 집합이 틀리면 dst 가 통째로 쓰레기가 된다.
    comp = dump["compilation"]
    if comp["errors"] or comp["unresolved_types"]:
        print(f"거부(F5) — errors {comp['errors']} / unresolved_types {comp['unresolved_types']}. "
              f"참조 집합을 확인하라 (모드 C: csproj 목록만, 호스트 BCL 금지).", file=sys.stderr)
        sys.exit(2)

    ty = {t["id"]: t for t in dump["types"]}
    asm2pkg = cs_asm2pkg(repo)
    src_asm = dump["compilation"]["assembly"]
    stats: Counter[str] = Counter()
    stats["asm->pkg 사전"] = len(asm2pkg)

    # 1차 판정은 file 유무가 아니라 어셈블리다. (float, float) 튜플은 netstandard 소속인데
    #   사용 지점의 소스 위치를 달고 온다 — C++ 에서 std:: 타입의 source_location 이 첫 사용
    #   지점을 가리키는 것과 같은 함정이다.
    def is_first(t: RoslynType) -> bool:
        return t.get("assembly") == src_asm

    def resolve(tid: str, depth: int = 0) -> list[str]:
        """R5 — 투과 래퍼는 type_args 를 따라 내려간다. roslyn-dump 가 제네릭 인자를
        구조로 주므로 문법 파싱이 필요 없다.
        투과 체크가 1차 판정보다 먼저다 — 튜플처럼 소스 위치를 단 외부 컨테이너가 있다."""
        if depth > 4:
            return []
        t = ty[tid]
        if t.get("generic_def") in CS_TRANSPARENT_DEFS:
            stats["R5 투과 래퍼 경유"] += 1
            out: list[str] = []
            for a in t.get("type_args", []):
                out.extend(resolve(a, depth + 1))
            return out
        if is_first(t):
            return [tid]                          # 소스(1차) 타입
        if t["kind"] in ("TypeParameter", "Error"):
            stats[f"dst {t['kind']} 버림"] += 1
            return []
        return [tid]                              # 외부 타입

    # ── 1패스: 소스 타입 -> 1차 노드.
    #    소스 제네릭의 구성 인스턴스(UI_Base<UI_HomeButton> 등)는 file 이 있어도
    #    별도 노드로 만들지 않는다 — Roslyn 이 정의와 다른 심볼로 주지만 위치는 정의와
    #    같으므로 (file, line) 으로 정의 노드에 접는다. 안 접으면 같은 클래스가 중복된다.
    node_id: dict[str, str] = {}
    nodes: dict[str, Node] = {}
    by_loc: dict[tuple[str | None, int | None], str] = {}
    for t in dump["types"]:
        if not is_first(t) or t.get("type_args"):
            continue
        nid = "C%d" % (len(nodes) + 1)
        nodes[nid] = {
            "id": nid, "name": t["name"], "kind": (t["kind"] or "class").lower(),
            "module": cs_module_of(t["file"]), "file": t["file"], "line": t["line"],
        }
        node_id[t["id"]] = nid
        by_loc[(t["file"], t["line"])] = nid
        stats["1차 노드"] += 1
    for t in dump["types"]:
        if is_first(t) and t.get("type_args"):
            hit = by_loc.get((t["file"], t["line"]))
            if hit:
                node_id[t["id"]] = hit
                stats["소스 제네릭 인스턴스 접음"] += 1

    collapsed: defaultdict[str, list[str]] = defaultdict(list)

    def to_node(tid: str) -> str:
        if tid in node_id:
            return node_id[tid]
        t = ty[tid]
        g = cs_external_group(t.get("assembly"), asm2pkg)
        nid = "X:" + g
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": g, "kind": "external",
                          "module": "__external__", "file": None, "line": None,
                          "collapsed_from": []}
        node_id[tid] = nid
        collapsed[nid].append(t["name"])
        stats["외부 원본 타입"] += 1
        return nid

    # ── 2패스: 간선. 적용 순서 R5 -> R7 -> R2(to_node) -> (R1/R4/R3/R6 은 _assemble).
    edges: dict[tuple[str, str, str], Edge] = {}
    for r in dump["relations"]:
        if r["is_enum_member"]:
            stats["enum 멤버 버림(플래그)"] += 1
            continue
        kind = CS_KIND[r["kind"]]
        srcs = resolve(r["src"])
        for d_tid in resolve(r["dst"]):
            if ty[d_tid]["name"] in CS_R7:                     # R7
                stats["R7 원시·암묵 기반 버림"] += 1
                continue
            for s_tid in srcs:
                s, d = to_node(s_tid), to_node(d_tid)
                if s == d:
                    stats["자기참조 버림"] += 1
                    continue
                if nodes[s]["kind"] == "external":             # R4
                    stats["R4 외부발 간선 버림"] += 1
                    continue
                key = (s, d, kind)
                if key in edges:
                    edges[key]["occurrences"] = edges[key].get("occurrences", 1) + 1
                    stats["중복 간선 접음"] += 1
                    continue
                edges[key] = {"from": s, "to": d, "kind": kind,
                              "label": r.get("member"), "file": r.get("file"), "line": r.get("line")}
                origin, attrs = r.get("origin"), r.get("attrs")
                if origin:
                    edges[key]["origin"] = origin              # C# 만 갖는 정보 — 비대칭 기록
                if attrs:
                    edges[key]["attrs"] = attrs                # [SerializeField] 등이 그대로 실린다
                if nodes[d]["kind"] == "external":
                    edges[key]["constraint"] = False           # R6

    for nid, names in collapsed.items():
        nodes[nid]["collapsed_from"] = sorted(set(names))

    return _assemble(nodes, edges, stats,
                     language="csharp", source_tool=dump.get("tool", "roslyn-dump ?"), repo=repo)


# ═══════════════════════════════ Python (griffe) ═══════════════════════════════

# ── 입력측 형(Python). griffe 의 `dump` JSON 이다. 타입 주석은 문자열이 아니라 식 트리로
#    오고 그 트리는 재귀적이다 (`Node | None` 은 ExprBinOp, `dict[str, Node]` 는
#    ExprSubscript + ExprTuple). 그래서 식의 형도 재귀적으로 적는다. `None` 과 `...` 만은
#    식 객체가 아니라 맨 문자열로 오므로 `GriffeExpr` 가 `str` 과의 합집합이다.


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.GriffeExprNode']"/>
# griffe 가 파이썬 타입 주석을 트리(재귀 구조)로 표현할 때 쓰는 '식 노드' 한 칸의 모양을 설명하는 타입 정의(TypedDict). 실행되는 코드가 아니라 데이터 모양 약속이다.
# 쓰는 것: machine.normalize.GriffeExpr · 쓰이는 곳: 없음
class GriffeExprNode(TypedDict, total=False):
    """식 트리 한 마디. `cls` 가 어느 마디인지 말하고, 나머지 열쇠는 마디마다 다르다."""

    cls: str
    name: str                       # ExprName
    values: list["GriffeExpr"]      # ExprAttribute — `abc.Mapping` 의 마디들
    left: "GriffeExpr"              # ExprBinOp / ExprSubscript
    right: "GriffeExpr"             # ExprBinOp
    slice: "GriffeExpr"             # ExprSubscript — `[...]` 의 속
    elements: list["GriffeExpr"]    # ExprTuple


GriffeExpr = str | GriffeExprNode


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.GriffeParam']"/>
# griffe 덤프에서 함수 매개변수 하나를 나타내는 타입 정의(TypedDict).
# 쓰는 것: machine.normalize.GriffeExpr · 쓰이는 곳: 없음
class GriffeParam(TypedDict, total=False):
    """`parameters[]` 한 칸. `self`·`cls` 와 주석 없는 매개변수는 호출부가 거른다."""

    name: Required[str]
    annotation: "GriffeExpr | None"


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.GriffeObject']"/>
# 파이썬 코드를 훑는 외부 도구 griffe 가 모듈·클래스·속성·함수를 전부 하나의 같은 JSON 모양으로 내보내기 때문에, 그 하나의 모양을 파이썬 자료형(TypedDict)으로 옮겨 적은 것이다. 실제로 무엇인지는 안에 있는 kind 필드 값(예: "module", "class", "function")으로 나중에 구분한다.
# 쓰는 것: machine.normalize.GriffeExpr · 쓰이는 곳: 없음
class GriffeObject(TypedDict, total=False):
    """모듈·클래스·속성·함수를 한 형으로 받는다 — griffe 가 `kind` 로만 가르기 때문이다.

    `filepath` 는 `__init__.py` 가 있으면 그 파일 경로(str), 없으면 디렉토리 목록(list)이다.
    `members` 는 list 가 아니라 이름으로 키질한 dict 다.
    """

    kind: str
    filepath: str | list[str]
    lineno: int
    members: dict[str, "GriffeObject"]
    imports: dict[str, str]
    bases: list["GriffeExpr"]
    annotation: "GriffeExpr | None"
    parameters: list[GriffeParam]
    returns: "GriffeExpr | None"


# griffe dump 의 뿌리 — 최상위 패키지 이름 -> 모듈 나무.
GriffeDump = dict[str, GriffeObject]


# R7 — 파이썬 원시 타입과 암묵적 기반 타입. 노드로 승격하지 않는다.
#   "None" 은 `Foo | None` 의 오른쪽, "..." 는 `tuple[Foo, ...]` 의 Ellipsis 로 온다.
#   griffe 는 이 둘을 식 객체가 아니라 맨 문자열로 준다.
PY_R7 = {
    "str", "int", "float", "bool", "bytes", "bytearray", "complex",
    "None", "NoneType", "object", "type", "...",
    # 타입 시스템 배관 — 의존이 아니라 표기 장치다. Generic[T]/Protocol 을 노드로 만들면
    # 모든 제네릭 클래스가 (표준) stdlib 로 향하는 가짜 간선을 하나씩 얻는다.
    "Any", "typing.Any", "typing.Generic", "typing.Protocol",
}

# R5 — 투과 컨테이너. 껍데기를 벗기고 안의 타입으로 내려간다.
#   추상 인터페이스(collections.abc.Mapping 등)는 넣지 않는다 — `CS_TRANSPARENT_DEFS` 와
#   같은 축이다. typing 별칭은 import 표를 거치면 "typing.X" 로 펴지므로 그 꼴로 적는다.
PY_TRANSPARENT = {
    "list", "dict", "set", "frozenset", "tuple",
    "typing.List", "typing.Dict", "typing.Set", "typing.FrozenSet", "typing.Tuple",
    "typing.Optional", "typing.Union",
}

# kind 사상. C# 과 같은 이유로 소유 kind(composition/aggregation)가 없다 —
# 파이썬은 모든 바인딩이 참조라 값 멤버/포인터 멤버 구분 자체가 없다.
#   base = 상속 · attr = 클래스 속성 주석 · sig = 메서드 매개변수/반환 주석
PY_KIND: dict[str, EdgeKind] = {"base": "inheritance", "attr": "association", "sig": "dependency"}


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.py_external_group']"/>
# 파이썬 외부(표준 라이브러리 포함) 타입을 배포 이름 하나로 묶는 함수. external_group 의 파이썬 버전 (R2 규칙).
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.normalize_python, machine.test_normalize.test_py_external_group_folds_stdlib_into_one
# 파이썬 외부 타입을 배포 이름 하나로 접는다.
# 쓰는 것: 없음 · 쓰이는 곳: normalize_python
def py_external_group(target: str) -> str:
    """R2 — 외부 하나 = 노드 하나. 입도는 import 루트 이름이다.

    표준 라이브러리는 C++ 의 "(STL) std" · C# 의 "(BCL) netstandard" 와 같은 축으로
    하나에 접는다. 낱낱이 세면 외부 섬이 json·os·re 같은 이름으로 뒤덮인다.
    """
    root = (target or "").split(".")[0]
    if not root:
        return "(기타)"
    if root in sys.stdlib_module_names:
        return "(표준) stdlib"
    return root


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.py_expr_name']"/>
# griffe 가 만든 타입 표현식 트리에서 '점으로 이어진 단순한 이름'을 문자열로 뽑아내는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.py_walk_expr, machine.test_normalize.test_py_expr_name_reads_name_and_dotted_attribute
# 타입 식 트리에서 쓰인 그대로의 점 이름을 꺼낸다.
# 쓰는 것: 없음 · 쓰이는 곳: py_walk_expr
def py_expr_name(expr: GriffeExpr | None) -> str | None:
    """식이 단순 이름이면 그 이름을, 아니면 None.

    griffe 는 `abc.Mapping` 을 ExprAttribute 의 values 리스트로, `None`·`...` 은 식 객체가
    아니라 맨 문자열로 준다. 둘 다 여기서 받는다.
    """
    if isinstance(expr, str):
        return expr
    if not isinstance(expr, dict):
        return None
    if expr.get("cls") == "ExprName":
        return expr.get("name")
    if expr.get("cls") == "ExprAttribute":
        parts = [v.get("name") for v in expr.get("values", []) if isinstance(v, dict)]
        return ".".join(p for p in parts if p) or None
    return None


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.py_resolve']"/>
# 파이썬 코드에서 짧게(예: import 로 줄여) 쓰인 타입 이름을 완전한(모듈 경로 포함) 이름으로 풀어내는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.py_walk_expr, machine.test_normalize.test_py_resolve_prefers_import_table_then_same_module
# 식 안의 짧은 이름을 완전 수식 이름으로 편다.
# 쓰는 것: 없음 · 쓰이는 곳: py_walk_expr
def py_resolve(name: str, mod_path: str, imports: dict[str, str], first_party: set[str]) -> str:
    """이름 해소 순서: 모듈의 import 표 -> 같은 모듈의 1차 클래스 -> 못 품.

    못 풀면 **쓰인 그대로** 돌려준다. 빌트인(`list`)과 타입변수(`T`)가 그 자리이고,
    호출자는 "점이 없는데 1차도 아니다" 로 그 둘을 걸러낸다.
    """
    head, _, rest = name.partition(".")
    if head in imports:
        return imports[head] + ("." + rest if rest else "")
    same = f"{mod_path}.{name}" if mod_path else name
    return same if same in first_party else name


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.py_walk_expr']"/>
# 파이썬 타입 주석 하나(예: `dict[str, Node] | None`)를 griffe 가 준 트리 구조에서 재귀적으로 파고들어, 실제로 '관계'로 쳐줄 만한 타입 이름들만 뽑아내는 함수다. 사람이 정규식으로 문자열을 파싱하는 대신, griffe 가 이미 만들어 준 트리를 타고 내려간다.
# 쓰는 것: machine.normalize.py_expr_name, machine.normalize.py_resolve · 쓰이는 곳: machine.normalize.normalize_python, machine.test_normalize._walk, machine.test_normalize.test_py_r5_does_not_unwrap_abstract_interface, machine.test_normalize.test_py_r5_nests_two_levels_deep, machine.test_normalize.test_py_r5_unwraps_builtin_generic (+5)
# 타입 식 하나에서 노드가 될 이름들을 뽑는다. R5 투과와 R7 거르기가 여기 있다.
# 쓰는 것: py_expr_name, py_resolve · 쓰이는 곳: normalize_python
def py_walk_expr(expr: GriffeExpr | None, mod_path: str, imports: dict[str, str],
                 first_party: set[str], stats: Counter[str], depth: int = 0) -> list[str]:
    """R5 — 컨테이너 껍데기를 벗기고 안의 타입 이름들을 모아 돌려준다.

    griffe 가 타입 주석을 식 트리로 주므로 제네릭 문법을 손으로 파싱할 필요가 없다.
    돌려주는 것은 완전 수식 이름의 리스트다. 1차인지 외부인지는 호출자가 정한다.
    """
    if depth > 8:
        stats["식 깊이 초과"] += 1
        return []
    if expr is None:
        return []

    # 마디 세 종류는 식 객체(dict)에만 있다. 맨 문자열(`None`·`...`)은 여기를 그냥 지나
    # 아래 py_expr_name 으로 간다 — 검사기에 그 사실을 보이려고 한 겹 감쌌을 뿐, 갈래는 같다.
    if isinstance(expr, dict):
        cls = expr.get("cls")

        if cls == "ExprBinOp":                # `Node | None` — 합집합이므로 양쪽 다 본다
            return (py_walk_expr(expr.get("left"), mod_path, imports, first_party, stats, depth + 1)
                    + py_walk_expr(expr.get("right"), mod_path, imports, first_party, stats, depth + 1))

        if cls == "ExprTuple":                # `dict[str, Node]` 의 속
            out: list[str] = []
            for e in expr.get("elements", []):
                out.extend(py_walk_expr(e, mod_path, imports, first_party, stats, depth + 1))
            return out

        if cls == "ExprSubscript":
            head = py_resolve(py_expr_name(expr.get("left")) or "", mod_path, imports, first_party)
            if head in PY_TRANSPARENT:        # R5 — 껍데기를 벗고 속으로 내려간다
                stats["R5 투과 컨테이너 경유"] += 1
                return py_walk_expr(expr.get("slice"), mod_path, imports, first_party, stats, depth + 1)
            # 투과 대상이 아니면 컨테이너 자신이 관계의 상대다 (인터페이스·사용자 제네릭).
            return py_walk_expr(expr.get("left"), mod_path, imports, first_party, stats, depth + 1)

    name = py_expr_name(expr)
    if not name:
        stats["이름이 아닌 식 버림"] += 1
        return []
    if name in PY_R7:                          # R7 — 쓰인 그대로가 이미 원시 타입
        stats["R7 원시 타입 버림"] += 1
        return []
    key = py_resolve(name, mod_path, imports, first_party)
    if key in PY_R7:                           # R7 — 펴 보니 원시 타입 (typing.Any 등)
        stats["R7 원시 타입 버림"] += 1
        return []
    if key not in first_party and "." not in key:
        # import 표에도 없고 1차도 아닌 맨 이름 — 빌트인이거나 타입변수다. 노드가 아니다.
        stats["해소 실패(빌트인·타입변수)"] += 1
        return []
    return [key]


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.normalize_python']"/>
# griffe가 뽑아낸 파이썬 클래스 정보(와 선택적으로 pycalls가 뽑아낸 호출 정보)를 이 프로젝트 공통의 코드 지도로 바꾸는 함수다.
# 쓰는 것: machine.normalize.module_of, machine.normalize._assemble, machine.normalize.py_external_group, machine.normalize.py_walk_expr, machine.normalize.merge_py_calls · 쓰이는 곳: machine.normalize.main, machine.test_normalize.test_golden_python_external_nodes_have_no_location, machine.test_normalize.test_golden_python_fixture_counts, machine.test_normalize.test_golden_python_ownership_edges_are_absent, machine.test_normalize.test_golden_python_r5_recovered_first_party_through_containers (+11)
# griffe 덤프를 공통 형식의 노드와 간선으로 바꾼다.
# 쓰는 것: module_of, py_external_group, py_walk_expr, _assemble · 쓰이는 곳: normalize.main
def normalize_python(dump: GriffeDump, repo: str, source_tool: str,
                     calls: PyCallsDump | None = None) -> tuple[CodeGraph, Counter[str]]:
    """griffe dump(JSON) -> codegraph.json. C++/C# 과 같은 모양(노드 -> 간선 -> _assemble)이다.

    1차/외부 판정에 별도 규칙이 없다 — griffe 는 지정한 패키지만 로드하므로 덤프에 나온
    클래스가 곧 1차이고, 주석·상속에서 참조되지만 덤프에 없는 이름이 외부다.

    `calls` 를 주면 `pycalls.py` 의 심볼과 호출을 합친다. 주지 않으면 그 병합만 건너뛴다.
    """
    stats: Counter[str] = Counter()

    # ── 0패스: 모듈 나무를 평평하게 편다.
    #    griffe 는 완전 수식 이름을 주지 않고 members 를 이름으로 키질한 dict 로만 준다.
    #    그래서 이름은 여기서 직접 이어 붙인다.
    mods: dict[str, tuple[GriffeObject, str | None]] = {}
    classes: dict[str, tuple[GriffeObject, str]] = {}

    def walk_module(obj: GriffeObject, path: str) -> None:
        fp = obj.get("filepath")
        # 갈림은 "패키지냐 모듈이냐" 가 아니라 네임스페이스 패키지냐다. __init__.py 가
        #   있으면 그 파일 경로(str), 없으면 디렉토리 목록(list)이 온다. 이 저장소의
        #   machine/ 에는 __init__.py 가 없어 list 갈래를 탄다.
        fp = fp[0] if isinstance(fp, list) else fp
        # realpath 로 양쪽을 맞춘다. macOS 의 /var 는 /private/var 로 가는 심볼릭 링크라
        #   griffe(해소된 경로)와 repo(해소 안 된 경로)를 그냥 relpath 하면 "../.." 가 나오고
        #   모듈 이름이 ".." 가 된다.
        rel = os.path.relpath(os.path.realpath(fp), os.path.realpath(repo)) if fp else None
        mods[path] = (obj, rel)
        members: dict[str, GriffeObject] = obj.get("members") or {}
        for name, m in members.items():
            child = f"{path}.{name}"
            if m.get("kind") == "module":
                walk_module(m, child)
            elif m.get("kind") == "class":
                walk_class(m, child, path)

    def walk_class(cls: GriffeObject, qname: str, mod_path: str) -> None:
        classes[qname] = (cls, mod_path)
        members: dict[str, GriffeObject] = cls.get("members") or {}
        for name, m in members.items():
            if m.get("kind") == "class":                  # 중첩 클래스도 노드다
                stats["중첩 클래스"] += 1
                walk_class(m, f"{qname}.{name}", mod_path)

    for root, obj in dump.items():
        walk_module(obj, root)
    stats["모듈"] = len(mods)

    # ── 1패스: 1차 클래스 -> 노드. 이름은 완전 수식 점 이름이다.
    node_id: dict[str, str] = {}
    nodes: dict[str, Node] = {}
    for qname in sorted(classes):
        cls, mod_path = classes[qname]
        rel = mods[mod_path][1]
        nid = "C%d" % (len(nodes) + 1)
        nodes[nid] = {
            "id": nid, "name": qname, "kind": "class",
            "module": module_of(rel), "file": rel, "line": cls.get("lineno"),
        }
        node_id[qname] = nid
        stats["1차 노드"] += 1

    collapsed: defaultdict[str, list[str]] = defaultdict(list)

    def to_node(key: str) -> str:
        """R2 — 외부 이름을 배포 이름 하나로 접는다."""
        if key in node_id:
            return node_id[key]
        g = py_external_group(key)
        nid = "X:" + g
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": g, "kind": "external",
                          "module": "__external__", "file": None, "line": None,
                          "collapsed_from": []}
        node_id[key] = nid
        collapsed[nid].append(key)
        stats["외부 원본 타입"] += 1
        return nid

    # ── 2패스: 간선. 적용 순서 R5/R7(py_walk_expr) -> R2(to_node) -> R1/R3 은 _assemble.
    #    R4(외부발 간선)는 여기서 발생하지 않는다 — 간선의 출발은 언제나 1차 클래스다.
    edges: dict[tuple[str, str, str], Edge] = {}
    first_party = set(classes)

    def add(src_q: str, dst_key: str, kind: EdgeKind, label: str | None,
            file: str | None, line: int | None) -> None:
        s, d = node_id[src_q], to_node(dst_key)
        if s == d:
            stats["자기참조 버림"] += 1
            return
        k = (s, d, kind)
        if k in edges:
            edges[k]["occurrences"] = edges[k].get("occurrences", 1) + 1
            stats["중복 간선 접음"] += 1
            return
        edges[k] = {"from": s, "to": d, "kind": kind, "label": label, "file": file, "line": line}
        if nodes[d]["kind"] == "external":
            edges[k]["constraint"] = False                # R6

    for qname in sorted(classes):
        cls, mod_path = classes[qname]
        imports: dict[str, str] = mods[mod_path][0].get("imports") or {}
        rel = mods[mod_path][1]

        def walk(expr: GriffeExpr | None, _mp: str = mod_path,
                 _im: dict[str, str] = imports) -> list[str]:
            return py_walk_expr(expr, _mp, _im, first_party, stats)

        bases: list[GriffeExpr] = cls.get("bases") or []
        for b in bases:
            for key in walk(b):
                add(qname, key, PY_KIND["base"], None, rel, cls.get("lineno"))

        cls_members: dict[str, GriffeObject] = cls.get("members") or {}
        for mname, m in cls_members.items():
            kind = m.get("kind")
            if kind == "attribute" and (ann := m.get("annotation")):
                for key in walk(ann):
                    add(qname, key, PY_KIND["attr"], mname, rel, m.get("lineno"))
            elif kind == "function":
                params: list[GriffeParam] = m.get("parameters") or []
                for p in params:
                    p_ann = p.get("annotation")
                    if p.get("name") in ("self", "cls") or not p_ann:
                        continue
                    for key in walk(p_ann):
                        add(qname, key, PY_KIND["sig"], f"{mname}({p['name']})", rel, m.get("lineno"))
                for key in walk(m.get("returns")):
                    add(qname, key, PY_KIND["sig"], f"{mname}()", rel, m.get("lineno"))

    if calls is not None:
        merge_py_calls(nodes, node_id, edges, calls, stats)

    for nid, names in collapsed.items():
        nodes[nid]["collapsed_from"] = sorted(set(names))

    return _assemble(nodes, edges, stats, language="python", source_tool=source_tool, repo=repo)


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.merge_py_calls']"/>
# griffe 는 파이썬의 클래스·상속·타입주석은 알지만 '어느 함수가 어느 함수를 호출하는지'는 전혀 모른다. 그 빈틈을, 저장소가 직접 만든 도구 pycalls.py 가 뽑아낸 함수·메서드 목록과 호출 관계를 받아서 griffe 가 만든 노드 표에 합쳐 넣는 함수다.
# 쓰는 것: machine.normalize.module_of · 쓰이는 곳: machine.normalize.normalize_python
# pycalls 의 심볼과 호출을 griffe 가 만든 노드 표에 합친다.
# 쓰는 것: module_of · 쓰이는 곳: normalize_python
def merge_py_calls(nodes: dict[str, Node], node_id: dict[str, str],
                   edges: dict[tuple[str, str, str], Edge],
                   calls: PyCallsDump, stats: Counter[str]) -> None:
    """`pycalls.py` 가 뽑은 함수·메서드와 호출을 합친다.

    griffe 는 클래스·상속·타입 주석을 알고, pycalls 는 함수 전량과 호출을 안다. 그래서

      · 노드는 합집합 — griffe 가 내지 않는 모듈 수준 함수가 여기서 들어온다.
        같은 이름이면 노드를 늘리지 않고 시그니처만 채운다.
      · 간선도 낸다. 여기가 `merge_clang_doc` 과 갈리는 자리다 — clang-doc 에는 관계
        분류가 없어 간선을 안 만들지만, 호출은 그 자체가 관계다.
      · 호출의 kind 는 `dependency` 다. 8종 enum 안에 있고 "부른다" 의 UML 대응이다.
        소유(composition/aggregation)로 올리지 않는다 — 부른다고 갖는 것이 아니다.

    `pycalls` 는 양끝이 모두 저장소 안 정의인 호출만 낸다. 그래서 여기서 외부 노드를
    만들 일이 없고, `_assemble` 의 R4(외부발 간선 금지)도 구조상 위반될 수 없다.
    """
    kinds = {"function": "function", "method": "method", "class": "class"}
    for sym in calls["symbols"]:
        hit = node_id.get(sym["name"])
        sig = sym.get("signature")                # NotRequired 라 첨자로 읽지 않는다
        if hit is not None:
            node = nodes[hit]
            if "signature" not in node and sig:
                node["signature"] = sig
            stats["pycalls 로 시그니처 보강"] += 1
            continue
        nid = "C%d" % (len(nodes) + 1)
        nodes[nid] = {
            "id": nid, "name": sym["name"], "kind": kinds[sym["kind"]],
            "module": module_of(sym["file"]), "file": sym["file"], "line": sym["line"],
        }
        if sig:
            nodes[nid]["signature"] = sig
        node_id[sym["name"]] = nid
        stats["pycalls 신규 노드 " + sym["kind"]] += 1

    for c in calls["calls"]:
        s, d = node_id.get(c["caller"]), node_id.get(c["callee"])
        if s is None or d is None or s == d:
            stats["호출 양끝 해소 실패"] += 1
            continue
        key = (s, d, PY_KIND["sig"])
        if key in edges:
            edges[key]["occurrences"] = edges[key].get("occurrences", 1) + 1
            stats["호출이 기존 간선에 접힘"] += 1
            continue
        edges[key] = {"from": s, "to": d, "kind": PY_KIND["sig"],
                      "label": "호출", "file": c["file"], "line": c["line"]}
        stats["호출 간선"] += 1


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.build_parser']"/>
# normalize.py 명령줄 도구가 받는 옵션들을 정의하는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: machine.normalize.main, machine.test_normalize.test_cli_accepts_clang_uml_and_clang_doc_together, machine.test_normalize.test_cli_clang_doc_is_optional, machine.test_normalize.test_cli_griffe_dump_conflicts_with_other_sources, machine.test_normalize.test_cli_griffe_dump_is_a_third_source
def build_parser() -> argparse.ArgumentParser:
    """명령줄 규약. `--clang-doc` 과 `--py-calls` 는 배타 그룹에 넣지 않는다.

    보조 수집기는 고르는 관계가 아니라 합치는 관계다. 배타 그룹에 넣으면 주 수집기와
    함께 줄 수 없어 합치기 자체가 불가능해진다.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--clang-uml", help="C++ — clang-uml -g json 산출물")
    src.add_argument("--roslyn-dump", help="C# — roslyn-dump.json (machine/roslyn-dump 가 만든 것)")
    src.add_argument("--griffe-dump", help="Python — griffe dump 산출물(JSON)")
    ap.add_argument("--py-calls",
                    help="Python — pycalls.py 산출물(JSON). --griffe-dump 와 **함께** 쓴다")
    ap.add_argument("--clang-doc",
                    help="C++ — clang-doc --format=json 출력 디렉토리. --clang-uml 과 **함께** 쓴다")
    ap.add_argument("--repo", default=".", help="대상 저장소 (repo_commit, asm->pkg 사전용)")
    ap.add_argument("-o", "--out", default="codegraph.json")
    return ap


# <include file="machine/comments.xml" path="//term[@id='machine.normalize.main']"/>
# 이 파일을 명령줄에서 직접 실행했을 때 맨 처음 불리는 함수다. C++/C#/Python 세 갈래 중 사용자가 어느 것을 돌리라고 했는지 보고 그 갈래대로 코드 지도를 만든다.
# 쓰는 것: machine.normalize.build_parser, machine.normalize.load_clang_uml, machine.clang_doc.load_clang_doc, machine.normalize.normalize_cpp, machine.normalize.normalize_csharp (+1) · 쓰이는 곳: 없음
def main() -> None:
    a = build_parser().parse_args()
    syms: list[Symbol] = []
    # 아래 세 갈래 중 하나만 채워진다. 마지막 요약 출력이 갈래마다 다른 것을 세므로
    # 여기서 빈 값으로 열어 둔다 — 갈래를 타지 않은 쪽은 그 요약을 찍지 않는다.
    els: list[UmlElement] = []
    rels: list[UmlRelationship] = []
    cs_dump: RoslynDump | None = None

    # 참/거짓이 아니라 None 여부로 가른다. argparse 의 배타 그룹이 보장하는 것은
    #   "셋 중 정확히 하나가 None 이 아니다" 이지 "참이다" 가 아니다 — `--clang-uml ""` 를
    #   주면 참/거짓 판정은 세 갈래를 모두 빠져나가 open(None) 으로 죽는다.
    if a.clang_uml is not None:
        els, rels, meta = load_clang_uml(a.clang_uml)
        tool = "clang-uml " + str(meta.get("clang_uml_version", "?"))
        if a.clang_doc:
            syms = load_clang_doc(a.clang_doc)
            tool += f" + clang-doc({len(syms)} 심볼)"
        g, stats = normalize_cpp(els, rels, a.repo, tool, doc_symbols=syms)
    elif a.roslyn_dump is not None:
        dump: RoslynDump = json.load(open(a.roslyn_dump, encoding="utf-8"))
        cs_dump = dump
        g, stats = normalize_csharp(dump, a.repo)
    else:
        py_dump: GriffeDump = json.load(open(a.griffe_dump, encoding="utf-8"))
        try:
            from importlib.metadata import version as _pkg_version
            tool = "griffe " + _pkg_version("griffe")
        except Exception:
            tool = "griffe ?"
        py_calls: PyCallsDump | None = None
        if a.py_calls:
            # json.load 는 Any 다. 파일 경계 한 자리에서만 형을 세운다 — 아래 len() 두 번이
            # 그 자리에서 바로 실패하므로 모양이 틀리면 조용히 넘어가지 않는다.
            py_calls = cast(PyCallsDump, json.load(open(a.py_calls, encoding="utf-8")))
            tool += (f" + pycalls({len(py_calls['symbols'])} 심볼"
                     f" / {len(py_calls['calls'])} 호출)")
        g, stats = normalize_python(py_dump, a.repo, tool, calls=py_calls)
    json.dump(g, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"{a.out} — 노드 {len(g['nodes'])} / 간선 {len(g['edges'])} / 모듈 {len(g['modules'])}")
    if a.clang_uml is not None:
        print(f"입력: elements {len(els)} / relationships {len(rels)}"
              + (f" / clang-doc 심볼 {len(syms)}" if a.clang_doc else ""))
    elif cs_dump is not None:                 # == a.roslyn_dump is not None. 검사기에 보이는 꼴
        print(f"입력: types {len(cs_dump['types'])} / relations {len(cs_dump['relations'])}")
    else:
        print(f"입력: 모듈 {stats['모듈']} / 1차 클래스 {stats['1차 노드']}")
    for k, v in stats.most_common():
        print(f"  {k:28s} {v}")
    ext = [n for n in g["nodes"] if n["kind"] == "external"]
    print("외부 노드:", ", ".join(f"{n['name']}({len(n.get('collapsed_from', []))})" for n in ext) or "없음")
    with_loc = sum(1 for e in g["edges"] if e.get("line"))
    own = [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]
    own_loc = sum(1 for e in own if e.get("line"))
    print(f"근거 위치가 붙은 간선: {with_loc}/{len(g['edges'])}")
    if own:
        print(f"  그중 소유 간선(C-13 L3 판정 대상): {own_loc}/{len(own)}")
    else:
        # C# · Python — 언어에 소유 표지(값 멤버 vs 포인터 멤버)가 없어 composition/aggregation
        # 이 0이다. association 이 위치를 갖는다.
        assoc = [e for e in g["edges"] if e["kind"] == "association"]
        lang = {"csharp": "C#", "python": "Python"}.get(g["language"], g["language"])
        print(f"  소유 간선 0 ({lang} 정상 — 함정 5). association "
              f"{sum(1 for e in assoc if e.get('line'))}/{len(assoc)} 에 위치")


if __name__ == "__main__":
    main()
