#!/usr/bin/env python3
"""verify_graph.py — codegraph.json 을 읽기 · 꼴 · 정합 · 근거 네 층으로 검사해 결함을 전부 모은다.

    python3 verify_graph.py <codegraph.json> --faults <graph-faults.json> --passed <graph-verified.json> [--repo <저장소>]

결함이 없으면 `--faults` 를 지우고 `--passed` 를 쓴다(종료 0). 결함이 있으면 `--passed` 를 지우고 `--faults` 를 쓴다(종료 1).
`--repo` 가 없으면 근거 층(V3)을 건너뛴다. 시각을 적지 않아 같은 입력이면 같은 바이트다.
"""
import hashlib
import json
from typing import Literal, TypedDict

# 결함 코드 -> 층. 표와 코드가 1대1이다(test_verify_graph.py 가 고정한다).
LAYER: dict[str, str] = {
    "unreadable": "V0 읽기",
    "top-field": "V1 꼴", "schema-version": "V1 꼴", "language": "V1 꼴", "empty-graph": "V1 꼴",
    "node-shape": "V1 꼴", "edge-shape": "V1 꼴", "module-shape": "V1 꼴", "node-kind": "V1 꼴",
    "duplicate-node": "V2 정합", "duplicate-edge": "V2 정합", "dangling-edge": "V2 정합",
    "external-node": "V2 정합", "external-source": "V2 정합", "external-constraint": "V2 정합",
    "first-party-location": "V2 정합", "module-list": "V2 정합", "module-dep": "V2 정합",
    "file-outside-repo": "V3 근거", "file-missing": "V3 근거", "line-out-of-range": "V3 근거",
}
# 노드의 kind. runner 의 RecordKind 안에 있어야 한다(test_mode1.py 가 대조한다).
NODE_KINDS = frozenset({"function", "method", "class", "struct", "enum", "interface", "delegate", "record", "external"})
LANGUAGES = frozenset({"cpp", "csharp", "python"})
EXTERNAL_MODULE = "__external__"


class Fault(TypedDict):
    """결함 하나. `at` 은 JSON 경로(`$.nodes[3].kind`)다."""
    code: str
    at: str
    detail: str


class FaultsDoc(TypedDict):
    """`graph-faults.json` — 결함이 있을 때만 있다."""
    status: Literal["failed"]
    language: str | None
    source_tool: str | None
    repo_commit: str | None
    total: int
    counts: dict[str, int]
    faults: list[Fault]


class PassedDoc(TypedDict):
    """`graph-verified.json` — 검사를 지난 지도의 기록. `codegraph_sha256` 이 그 지도 한 벌에만 묶는다."""
    status: Literal["passed"]
    language: str
    source_tool: str
    repo_commit: str | None
    nodes: int
    edges: int
    modules: int
    codegraph_sha256: str


def fault(code: str, at: str, detail: str) -> Fault:
    """결함 하나를 만든다. 표에 없는 코드는 `KeyError` 다."""
    if code not in LAYER:
        raise KeyError(code)
    return {"code": code, "at": at, "detail": detail}


def read_graph(path: str) -> tuple[object, str, list[Fault]]:
    """V0 읽기 — 파일을 열어 JSON 으로 푼다. (문서, 바이트의 sha256, 결함) 을 낸다. 못 열거나 못 풀면 문서는 `None` 이다."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        return None, "", [fault("unreadable", "$", "파일을 못 연다: %s" % (e.strerror or e))]
    sha = hashlib.sha256(raw).hexdigest()
    try:
        return json.loads(raw.decode("utf-8")), sha, []
    except UnicodeDecodeError as e:
        return None, sha, [fault("unreadable", "$", "UTF-8 이 아니다 — %d바이트째" % e.start)]
    except json.JSONDecodeError as e:
        return None, sha, [fault("unreadable", "$", "JSON 이 아니다 — %d줄 %d칸: %s" % (e.lineno, e.colno, e.msg))]
