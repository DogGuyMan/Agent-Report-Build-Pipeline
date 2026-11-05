#!/usr/bin/env python3
"""verify_graph.py — codegraph.json 을 읽기 · 꼴 · 정합 · 근거 네 층으로 검사해 결함을 전부 모은다.

    python3 verify_graph.py <codegraph.json> --faults <graph-faults.json> --passed <graph-verified.json> [--repo <저장소>]

결함이 없으면 `--faults` 를 지우고 `--passed` 를 쓴다(종료 0). 결함이 있으면 `--passed` 를 지우고 `--faults` 를 쓴다(종료 1).
`--repo` 가 없으면 근거 층(V3)을 건너뛴다. 시각을 적지 않아 같은 입력이면 같은 바이트다.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypedDict, cast, get_type_hints

import msgspec

from codegraph_types import CodeGraph, Edge, Module, Node

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
TOP = get_type_hints(CodeGraph)
ELEMENTS = ("nodes", "edges", "modules")


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


@dataclass
class Elements:
    """V1 을 지난 원소(원래 자리 번호와 함께)와, 꼴이 틀려 뒤 층이 빼야 하는 것의 흔적."""
    nodes: list[tuple[int, Node]]
    edges: list[tuple[int, Edge]]
    modules: list[tuple[int, Module]]
    bad_node_ids: set[str]
    bad_node_without_id: bool
    bad_module: bool


def check_top(doc: object) -> list[Fault]:
    """V1 꼴(최상위) — 계약 `CodeGraph` 의 열쇠가 다 있고 형이 맞는가 · 판이 2인가 · 아는 언어인가 · 노드가 있는가.

    `nodes` · `edges` · `modules` 는 목록인지만 본다. 원소는 `check_elements` 가 본다.
    """
    if not isinstance(doc, dict):
        return [fault("top-field", "$", "최상위가 객체가 아니라 %s 다" % type(doc).__name__)]
    d = cast(dict[str, object], doc)
    out: list[Fault] = []
    for key, t in TOP.items():
        if key not in d:
            out.append(fault("top-field", "$.%s" % key, "필수 열쇠가 없다"))
            continue
        try:
            msgspec.convert(d[key], list if key in ELEMENTS else t)
        except msgspec.ValidationError as e:
            out.append(fault("top-field", "$.%s" % key, str(e)))
    version, language, nodes = d.get("schema_version"), d.get("language"), d.get("nodes")
    if isinstance(version, int) and version != 2:
        out.append(fault("schema-version", "$.schema_version", "판이 %d 다 — 2 여야 한다" % version))
    if isinstance(language, str) and language not in LANGUAGES:
        out.append(fault("language", "$.language", "모르는 언어 %r" % language))
    if isinstance(nodes, list) and not nodes:
        out.append(fault("empty-graph", "$.nodes", "노드가 하나도 없다"))
    return out


def _items(d: dict[str, object], key: str) -> list[object]:
    """`d[key]` 가 목록이면 그것을, 아니면 빈 목록을 낸다 — 목록이 아닌 것은 `check_top` 이 이미 셌다."""
    v = d.get(key)
    return cast(list[object], v) if isinstance(v, list) else []


def check_elements(d: dict[str, object]) -> tuple[Elements, list[Fault]]:
    """V1 꼴(원소) — 원소마다 따로 계약 형(`Node` · `Edge` · `Module`)으로 바꿔 본다. 첫 오류에서 멈추지 않고 전부 모은다."""
    out: list[Fault] = []
    el = Elements([], [], [], set(), False, False)
    for i, raw in enumerate(_items(d, "nodes")):
        try:
            n = msgspec.convert(raw, Node)
        except msgspec.ValidationError as e:
            out.append(fault("node-shape", "$.nodes[%d]" % i, str(e)))
            nid = cast(dict[str, object], raw).get("id") if isinstance(raw, dict) else None
            if isinstance(nid, str):
                el.bad_node_ids.add(nid)
            else:
                el.bad_node_without_id = True
            continue
        if n["kind"] not in NODE_KINDS:
            out.append(fault("node-kind", "$.nodes[%d].kind" % i, "모르는 kind %r" % n["kind"]))
        el.nodes.append((i, n))
    for i, raw in enumerate(_items(d, "edges")):
        try:
            el.edges.append((i, msgspec.convert(raw, Edge)))
        except msgspec.ValidationError as e:
            out.append(fault("edge-shape", "$.edges[%d]" % i, str(e)))
    for i, raw in enumerate(_items(d, "modules")):
        try:
            el.modules.append((i, msgspec.convert(raw, Module)))
        except msgspec.ValidationError as e:
            out.append(fault("module-shape", "$.modules[%d]" % i, str(e)))
            el.bad_module = True
    return el, out


def check_consistency(el: Elements) -> list[Fault]:
    """V2 정합 — id 가 겹치지 않고, 간선이 있는 노드를 잇고, 외부 노드 규칙(R4 · R6)과 모듈 목록이 맞는가.

    V1 에서 꼴이 틀린 원소 때문에 생기는 끊김 · 목록 차이는 세지 않는다.
    """
    out: list[Fault] = []
    kind_of: dict[str, str] = {}
    for i, n in el.nodes:
        at = "$.nodes[%d]" % i
        if n["id"] in kind_of:
            out.append(fault("duplicate-node", at + ".id", "id %r 가 앞에도 있다" % n["id"]))
        kind_of[n["id"]] = n["kind"]
        external = n["kind"] == "external"
        if external != (n["module"] == EXTERNAL_MODULE) or (external and (n["file"] is not None or n["line"] is not None)):
            out.append(fault("external-node", at, "외부 노드는 kind external · module %s · 위치 없음이 함께여야 한다"
                             % EXTERNAL_MODULE))
        elif not external and (n["file"] is None or n["line"] is None):
            out.append(fault("first-party-location", at, "1차 노드 %r 에 file 이나 line 이 없다" % n["id"]))
    known = set(kind_of) | el.bad_node_ids
    seen: set[tuple[str, str, str]] = set()
    for i, e in el.edges:
        at = "$.edges[%d]" % i
        ends = [x for x in (e["from"], e["to"]) if x not in known]
        if ends and not el.bad_node_without_id:
            out.append(fault("dangling-edge", at, "없는 노드 %s 를 잇는다" % ", ".join(repr(x) for x in ends)))
        if kind_of.get(e["from"]) == "external":
            out.append(fault("external-source", at, "외부 노드 %r 에서 나가는 간선이다(R4)" % e["from"]))
        if kind_of.get(e["to"]) == "external" and e.get("constraint") is not False:
            out.append(fault("external-constraint", at, "외부로 가는 간선은 constraint false 여야 한다(R6)"))
        key = (e["from"], e["to"], e["kind"])
        if key in seen:
            out.append(fault("duplicate-edge", at, "같은 (from, to, kind) 가 앞에도 있다"))
        seen.add(key)
    if not (el.bad_node_ids or el.bad_node_without_id or el.bad_module):
        listed = [m["id"] for _, m in el.modules]
        used = {n["module"] for _, n in el.nodes if n["kind"] != "external" and n["module"]}
        for m in sorted(used - set(listed)):
            out.append(fault("module-list", "$.modules", "노드의 모듈 %r 이 목록에 없다" % m))
        for m in sorted(set(listed) - used):
            out.append(fault("module-list", "$.modules", "목록의 모듈 %r 을 쓰는 노드가 없다" % m))
        for m in sorted({x for x in listed if listed.count(x) > 1}):
            out.append(fault("module-list", "$.modules", "모듈 %r 이 두 번 있다" % m))
    ids = {m["id"] for _, m in el.modules}
    for i, m in el.modules:
        for dep in m["depends_on"]:
            if dep == m["id"]:
                out.append(fault("module-dep", "$.modules[%d].depends_on" % i, "%r 은 자기 자신이다" % dep))
            elif dep not in ids:
                out.append(fault("module-dep", "$.modules[%d].depends_on" % i, "%r 은 목록에 없는 모듈이다" % dep))
    return out


def _line_count(path: str) -> int | None:
    """파일의 줄 수. 일반 파일이 아니거나 못 열면 `None`."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


def check_sources(el: Elements, repo: str) -> list[Fault]:
    """V3 근거 — 노드와 간선의 `file` 이 저장소 안의 실제 파일이고 `line` 이 1 이상 그 파일 끝 이하인가."""
    out: list[Fault] = []
    root = os.path.realpath(repo)
    count: dict[str, int | None] = {}
    places = ([("$.nodes[%d]" % i, n["file"], n["line"]) for i, n in el.nodes]
              + [("$.edges[%d]" % i, e["file"], e["line"]) for i, e in el.edges])
    for at, file, line in places:
        if file is None:
            continue
        full = os.path.realpath(os.path.join(root, file))
        if os.path.isabs(file) or os.path.commonpath([root, full]) != root:
            out.append(fault("file-outside-repo", at + ".file", "저장소 밖 경로 %r" % file))
            continue
        if file not in count:
            count[file] = _line_count(full)
        n = count[file]
        if n is None:
            out.append(fault("file-missing", at + ".file", "파일이 없다: %s" % file))
        elif line is not None and not 1 <= line <= n:
            out.append(fault("line-out-of-range", at + ".line", "%d줄 — %s 는 %d줄이다" % (line, file, n)))
    return out


def _text(d: dict[str, object] | None, key: str) -> str | None:
    """`d[key]` 가 문자열이면 그것을, 아니면 `None`."""
    v = d.get(key) if d is not None else None
    return v if isinstance(v, str) else None


def verify(path: str, repo: str | None) -> FaultsDoc | PassedDoc:
    """네 층을 차례로 돌려 결과 문서 하나를 낸다. 앞 층이 열지 못한 것은 뒤 층이 보지 않는다."""
    doc, sha, faults = read_graph(path)
    if not faults:
        faults = check_top(doc)
    d = cast(dict[str, object], doc) if isinstance(doc, dict) else None
    el: Elements | None = None
    if d is not None:
        el, more = check_elements(d)
        faults = faults + more + check_consistency(el)
        if repo is not None:
            faults = faults + check_sources(el, repo)
    if faults or d is None or el is None:
        counts = Counter(f["code"] for f in faults)
        return {"status": "failed", "language": _text(d, "language"), "source_tool": _text(d, "source_tool"),
                "repo_commit": _text(d, "repo_commit"), "total": len(faults),
                "counts": dict(sorted(counts.items())), "faults": faults}
    return {"status": "passed", "language": cast(str, d["language"]), "source_tool": cast(str, d["source_tool"]),
            "repo_commit": _text(d, "repo_commit"), "nodes": len(el.nodes), "edges": len(el.edges),
            "modules": len(el.modules), "codegraph_sha256": sha}


def _replace(keep: str, drop: str, doc: FaultsDoc | PassedDoc) -> None:
    """다른 쪽 결과 파일을 먼저 지우고 이쪽을 쓴다 — 도중에 끊겨도 두 파일이 함께 남지 않는다."""
    if os.path.exists(drop):
        os.remove(drop)
    os.makedirs(os.path.dirname(os.path.abspath(keep)), exist_ok=True)
    with open(keep, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    """`verify` 를 돌려 결과 파일 하나를 쓰고 다른 하나를 지운다. 통과면 0, 결함이면 1."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("codegraph", help="검사할 codegraph.json")
    ap.add_argument("--repo", default=None, help="근거 층(V3)의 기준 저장소. 없으면 V3 를 건너뛴다")
    ap.add_argument("--faults", required=True, help="결함이 있으면 쓰는 graph-faults.json")
    ap.add_argument("--passed", required=True, help="통과하면 쓰는 graph-verified.json")
    a = ap.parse_args(argv)
    got = verify(a.codegraph, a.repo)
    if got["status"] == "passed":
        _replace(a.passed, a.faults, got)
        print("%s — 통과 · 노드 %d · 간선 %d · 모듈 %d" % (a.passed, got["nodes"], got["edges"], got["modules"]))
        return 0
    _replace(a.faults, a.passed, got)
    print("%s — 결함 %d건 · %s" % (a.faults, got["total"], " · ".join("%s %d" % kv for kv in got["counts"].items())),
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
