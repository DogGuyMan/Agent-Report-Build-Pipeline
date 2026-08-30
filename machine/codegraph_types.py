# <include file="machine/comments.xml" path="//term[@id='codegraph_types.py']"/>
# codegraph.json(스키마 v2)의 모양을 적어 둔 파일. 실행되는 코드가 없다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# codegraph.json(스키마 v2)의 모양을 적어 둔 파일. 실행되는 코드가 없다.
# 쓰는 것: 없음 · 쓰이는 곳: normalize, facts, survey_plan, verify_citations, render_modules, render_classes
"""codegraph_types.py — `codegraph.json`(schema_version 2) 의 계약을 적어 둔 한 곳.

생산자(`normalize.py::_assemble`)와 소비자 전부가 여기 하나를 본다.

이 파일에 로직을 넣지 마라. 여기는 `viz/src/types.ts` 의 파이썬 짝이다 — 모양만 적는다.
정책(접기 규칙 R1~R7 · kind 사상)은 `normalize.py` 에만 있다.
"""
from typing import Literal, NotRequired, TypedDict

__all__ = ["EdgeKind", "Node", "Edge", "Module", "CodeGraph"]

# 8종 고정. 새 값을 만들지 않는다 — `normalize.py` 의 대응표 주석을 보라.
EdgeKind = Literal[
    "composition", "aggregation", "dependency", "instantiation",
    "friendship", "inheritance", "realization", "association",
]


# <include file="machine/comments.xml" path="//term[@id='machine.codegraph_types.Node']"/>
# 코드 지도(codegraph.json)에 찍히는 점 하나의 모양이다. 실제 타입 하나이거나, 접혀서 뭉친 외부 타입들의 섬 하나를 나타낸다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.codegraph_types.CodeGraph
class Node(TypedDict):
    """코드 지도의 점. 1차 타입 하나 또는 접힌 외부 섬 하나."""

    id: str
    name: str
    kind: str
    # 외부 노드는 `"__external__"`, 위치가 없는 노드는 file/line 이 None 이다.
    module: str | None
    file: str | None
    line: int | None
    # 외부 노드에만 — 이 섬으로 접힌 원본 타입 이름들 (R2).
    collapsed_from: NotRequired[list[str]]
    # C++ clang-doc 갈래가 함수 노드에 붙인다.
    signature: NotRequired[str]
    doc: NotRequired[str]


# `from` 이 파이썬 예약어라 class 문법으로는 필드로 적을 수 없다. 함수 꼴이 유일한 길이다.
Edge = TypedDict("Edge", {
    "from": str,
    "to": str,
    "kind": EdgeKind,
    # 근거가 되는 멤버 이름과 그 위치. 상속처럼 멤버가 없는 간선은 label 이 None 이다.
    "label": str | None,
    "file": str | None,
    "line": int | None,
    # 같은 (from, to, kind) 로 접힌 횟수. 1이면 아예 붙지 않는다.
    "occurrences": NotRequired[int],
    # R6 — 외부 섬으로 가는 간선은 배치를 끌지 않는다.
    "constraint": NotRequired[bool],
    # C# 갈래만 갖는다 — 비대칭 기록.
    "origin": NotRequired[str],
    "attrs": NotRequired[list[str]],
})


# <include file="machine/comments.xml" path="//term[@id='machine.codegraph_types.Module']"/>
# 폴더 트리 한 칸을 나타내는 자료 모양이다. 클래스라기보다 '이 모양대로 딕셔너리를 채워라'는 설계도에 가깝다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.codegraph_types.CodeGraph
class Module(TypedDict):
    """폴더 트리 한 칸. `depends_on` 은 클래스 간선에서 유도된 타입 의존이다.

    링크 의존이 아니다. CMake 의 PUBLIC/INTERFACE/PRIVATE 축과 같은 것으로 읽지 마라.
    """

    id: str
    depends_on: list[str]


# <include file="machine/comments.xml" path="//term[@id='machine.codegraph_types.CodeGraph']"/>
# normalize.py 가 마지막에 만들어 내는 codegraph.json 파일 전체의 모양을 정의하는 틀이다. 실제로 실행되는 코드는 없고, 타입 검사기가 이 모양을 지키는지 확인하는 데만 쓰인다.
# 쓰는 것: machine.codegraph_types.Node, machine.codegraph_types.Edge, machine.codegraph_types.Module · 쓰이는 곳: machine.test_normalize._load
class CodeGraph(TypedDict):
    """`normalize.py::_assemble` 이 내는 최종 모양."""

    schema_version: int
    language: str
    platform: str
    source_tool: str
    repo_commit: str | None
    nodes: list[Node]
    edges: list[Edge]
    modules: list[Module]
