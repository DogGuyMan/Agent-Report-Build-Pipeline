#!/usr/bin/env python3
"""verify_graph.py — codegraph.json 을 읽기 · 꼴 · 정합 · 근거 네 층으로 검사해 결함을 전부 모은다.

    python3 verify_graph.py <codegraph.json> --faults <graph-faults.json> --passed <graph-verified.json> [--repo <저장소>] [--manifest <collect-fingerprint.json>]

결함이 없으면 `--faults` 를 지우고 `--passed` 를 쓴다(종료 0). 결함이 있으면 `--passed` 를 지우고 `--faults` 를 쓴다(종료 1).
`--repo` 가 없으면 근거 층(V3)과 manifest 대조를 건너뛴다. `--manifest` 가 없거나 못 읽으면 최신성을 알 수 없다는 결함이다.
시각을 적지 않아 같은 입력이면 같은 바이트다.
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
from collect_manifest import CollectManifest, sources_digest
from jsonio import write_json_atomic

# 결함 코드 -> 층. 표와 코드가 1대1이다(test_verify_graph.py 가 고정한다).
LAYER: dict[str, str] = {
    "unreadable": "V0 읽기",
    "top-field": "V1 꼴", "schema-version": "V1 꼴", "language": "V1 꼴", "empty-graph": "V1 꼴",
    "node-shape": "V1 꼴", "edge-shape": "V1 꼴", "module-shape": "V1 꼴", "node-kind": "V1 꼴",
    "external-only": "V1 꼴", "occurrences-range": "V1 꼴",
    "duplicate-node": "V2 정합", "duplicate-edge": "V2 정합", "dangling-edge": "V2 정합",
    "external-node": "V2 정합", "external-source": "V2 정합", "external-constraint": "V2 정합",
    "first-party-location": "V2 정합", "module-list": "V2 정합", "module-dep": "V2 정합",
    "module-dep-mismatch": "V2 정합",
    "file-outside-repo": "V3 근거", "file-missing": "V3 근거", "line-out-of-range": "V3 근거",
    "freshness-unknown": "V3 근거", "generation-mismatch": "V3 근거", "source-drift": "V3 근거",
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


# 층 -> 결과 문서의 절.
SECTION_OF_LAYER: dict[str, str] = {"V0 읽기": "integrity", "V1 꼴": "integrity", "V2 정합": "integrity",
                                    "V3 근거": "freshness"}
# 기록에만 남고 통과를 막지 않는 코드.
REPORT_ONLY: frozenset[str] = frozenset()


class SectionDoc(TypedDict):
    """한 절의 결함 수와 코드별 수."""
    faults: int
    counts: dict[str, int]


class FreshnessDoc(SectionDoc):
    """최신성 절. `manifest` 는 수집 manifest 와의 대조 결과, `raw_provenance` 는 수집 원본이 prep 안에서 났는가."""
    manifest: Literal["ok", "missing", "mismatch"]
    sources_sha256: str | None
    raw_provenance: Literal["prep", "unknown"]


class CoverageDoc(SectionDoc):
    """범위 절. 소스 inventory 가 있을 때만 수가 채워진다."""
    inventory: Literal["ok", "missing"]
    files_total: int
    collected: int
    excluded: int
    unsupported: int
    failed: int
    no_symbols: int
    languages_not_collected: list[str]


class Capabilities(TypedDict):
    """이 수집기가 낼 수 있다고 주장하는 것."""
    methods: bool
    calls: bool
    resolution: Literal["compiler", "heuristic", "none"]


class Fit(TypedDict):
    """목적별 적합성. 지금 목적은 전수조사(annotate-symbols) 하나다."""
    survey: Literal["ready", "blocked"]
    blocked_by: list[str]


class VerifyDoc(TypedDict):
    """`graph-verified.json`(status passed) 과 `graph-faults.json`(status failed) 의 공통 꼴."""
    status: Literal["passed", "failed"]
    generation_id: str | None
    codegraph_sha256: str | None
    language: str | None
    source_tool: str | None
    repo_commit: str | None
    nodes: int
    edges: int
    modules: int
    checks_run: list[str]
    integrity: SectionDoc
    freshness: FreshnessDoc
    coverage: CoverageDoc
    capabilities: Capabilities
    fit: Fit
    total: int
    faults: list[Fault]


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
    """V1 꼴(원소) — 원소마다 따로 계약 형(`Node` · `Edge` · `Module`)으로 바꿔 본다. 첫 오류에서 멈추지 않고 전부 모은다.

    간선의 `occurrences` 가 1 이상인지, 1차 노드가 하나라도 있는지도 본다.
    """
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
    if el.nodes and all(n["kind"] == "external" for _, n in el.nodes):
        out.append(fault("external-only", "$.nodes", "1차 노드가 하나도 없다 — 외부 노드 %d개뿐이다" % len(el.nodes)))
    for i, raw in enumerate(_items(d, "edges")):
        try:
            edge = msgspec.convert(raw, Edge)
        except msgspec.ValidationError as e:
            out.append(fault("edge-shape", "$.edges[%d]" % i, str(e)))
            continue
        el.edges.append((i, edge))
        occ = edge.get("occurrences")
        if occ is not None and occ < 1:
            out.append(fault("occurrences-range", "$.edges[%d].occurrences" % i, "%d — 1 이상이어야 한다" % occ))
    for i, raw in enumerate(_items(d, "modules")):
        try:
            el.modules.append((i, msgspec.convert(raw, Module)))
        except msgspec.ValidationError as e:
            out.append(fault("module-shape", "$.modules[%d]" % i, str(e)))
            el.bad_module = True
    return el, out


def check_consistency(el: Elements) -> list[Fault]:
    """V2 정합 — id 가 겹치지 않고, 간선이 있는 노드를 잇고, 외부 노드 규칙(R4 · R6)과 모듈 목록이 맞는가.

    모듈의 `depends_on` 은 간선에서 다시 센 것(`normalize.py::_assemble` 의 유도와 같은 규칙)과 같아야 한다.

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
        module_of = {n["id"]: n["module"] for _, n in el.nodes}
        expected: dict[str, set[str]] = {m: set() for m in listed}
        for _, e in el.edges:
            a, b = module_of.get(e["from"]), module_of.get(e["to"])
            if kind_of.get(e["to"]) == "external" or not a or not b or a == b:
                continue
            expected.setdefault(a, set()).add(b)
        for i, m in el.modules:
            want, got = expected.get(m["id"], set()), set(m["depends_on"])
            if want != got:
                out.append(fault("module-dep-mismatch", "$.modules[%d].depends_on" % i,
                                 "간선으로 센 것과 다르다 — 빠짐 %s · 남음 %s"
                                 % (sorted(want - got) or "없음", sorted(got - want) or "없음")))
    ids = {m["id"] for _, m in el.modules}
    for i, m in el.modules:
        for dep in m["depends_on"]:
            if dep == m["id"]:
                out.append(fault("module-dep", "$.modules[%d].depends_on" % i, "%r 은 자기 자신이다" % dep))
            elif dep not in ids:
                out.append(fault("module-dep", "$.modules[%d].depends_on" % i, "%r 은 목록에 없는 모듈이다" % dep))
    return out


def _file_facts(path: str) -> tuple[int, str] | None:
    """파일의 (줄 수, 바이트의 sha256). 일반 파일이 아니거나 못 열면 `None`."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    return raw.count(b"\n") + (1 if raw and not raw.endswith(b"\n") else 0), hashlib.sha256(raw).hexdigest()


def check_sources(el: Elements, repo: str) -> tuple[list[Fault], dict[str, str]]:
    """V3 근거 — 노드와 간선의 `file` 이 저장소 안의 실제 파일이고 `line` 이 1 이상 그 파일 끝 이하인가.

    결함과 함께, 연 파일마다 지금 바이트의 sha256(`{상대 경로: sha}`)을 낸다. 없는 파일은 들어 있지 않다.
    """
    out: list[Fault] = []
    root = os.path.realpath(repo)
    facts: dict[str, tuple[int, str] | None] = {}
    places = ([("$.nodes[%d]" % i, n["file"], n["line"]) for i, n in el.nodes]
              + [("$.edges[%d]" % i, e["file"], e["line"]) for i, e in el.edges])
    for at, file, line in places:
        if file is None:
            continue
        full = os.path.realpath(os.path.join(root, file))
        if os.path.isabs(file) or os.path.commonpath([root, full]) != root:
            out.append(fault("file-outside-repo", at + ".file", "저장소 밖 경로 %r" % file))
            continue
        if file not in facts:
            facts[file] = _file_facts(full)
        got = facts[file]
        if got is None:
            out.append(fault("file-missing", at + ".file", "파일이 없다: %s" % file))
        elif line is not None and not 1 <= line <= got[0]:
            out.append(fault("line-out-of-range", at + ".line", "%d줄 — %s 는 %d줄이다" % (line, file, got[0])))
    return out, {rel: got[1] for rel, got in facts.items() if got is not None}


def check_manifest(manifest_path: str | None, sha: str, now: dict[str, str]
                   ) -> tuple[list[Fault], Literal["ok", "missing", "mismatch"], CollectManifest | None]:
    """최신성 — 수집 manifest 가 이 지도의 것이고, 인용 파일의 지금 바이트가 수집 시점과 같은가."""
    if manifest_path is None or not os.path.exists(manifest_path):
        return [fault("freshness-unknown", "$", "수집 manifest 가 없다 — prep 이 지도를 만들었는지 알 수 없다")], "missing", None
    try:
        with open(manifest_path, "rb") as f:
            m = msgspec.json.decode(f.read(), type=CollectManifest)
    except (OSError, msgspec.DecodeError) as e:
        return [fault("freshness-unknown", "$", "수집 manifest 를 읽을 수 없다: %s" % e)], "missing", None
    if m["codegraph_sha256"] != sha:
        return [fault("generation-mismatch", "$", "manifest 는 다른 지도(%s…)의 것이다" % m["codegraph_sha256"][:12])], "mismatch", m
    out: list[Fault] = []
    for rel in sorted(set(now) | set(m["sources"])):
        then, cur = m["sources"].get(rel), now.get(rel, "missing")
        if then is None:
            out.append(fault("source-drift", "$.sources[%r]" % rel, "manifest 에 없는 파일을 인용한다"))
        elif then != cur:
            out.append(fault("source-drift", "$.sources[%r]" % rel, "수집 때 %s… 지금 %s…" % (then[:12], cur[:12])))
    return out, "ok", m


def _text(d: dict[str, object] | None, key: str) -> str | None:
    """`d[key]` 가 문자열이면 그것을, 아니면 `None`."""
    v = d.get(key) if d is not None else None
    return v if isinstance(v, str) else None


def capabilities_of(language: str | None) -> Capabilities:
    """언어(수집기)별로 지도가 주장할 수 있는 것."""
    if language == "python":
        return {"methods": True, "calls": True, "resolution": "heuristic"}
    if language in ("cpp", "csharp"):
        return {"methods": False, "calls": False, "resolution": "compiler"}
    return {"methods": False, "calls": False, "resolution": "none"}


def section(faults: list[Fault], name: str) -> SectionDoc:
    """결함 중 이 절에 속한 것의 수와 코드별 수."""
    mine = [f for f in faults if SECTION_OF_LAYER[LAYER[f["code"]]] == name]
    return {"faults": len(mine), "counts": dict(sorted(Counter(f["code"] for f in mine).items()))}


def fit_of(status: str, checks_run: list[str], freshness: FreshnessDoc, blocking: list[Fault]) -> Fit:
    """전수조사에 들어갈 수 있는가. 구조만 본 기록(V3 없음)과 수집 manifest 와 맞지 않는 기록은 맞지 않는다."""
    why: list[str] = sorted({f["code"] for f in blocking})
    if "V3" not in checks_run:
        why.append("V3 를 돌리지 않았다 (--repo 없음)")
    if freshness["manifest"] != "ok":
        why.append("수집 manifest 와 맞지 않는다 (%s)" % freshness["manifest"])
    return {"survey": "ready" if status == "passed" and not why else "blocked", "blocked_by": why}


def verify(path: str, repo: str | None, manifest: str | None = None) -> VerifyDoc:
    """층을 차례로 돌려 결과 문서 하나를 낸다. 앞 층이 열지 못한 것은 뒤 층이 보지 않는다.

    `repo` 가 있으면 근거 층 뒤에 수집 manifest 를 대조한다. `repo` 가 없으면 manifest 는 보지 않는다.
    """
    doc, sha, faults = read_graph(path)
    checks = ["V0"]
    d = cast(dict[str, object], doc) if isinstance(doc, dict) else None
    el: Elements | None = None
    now: dict[str, str] = {}
    state: Literal["ok", "missing", "mismatch"] = "missing"
    found: CollectManifest | None = None
    if not faults:
        faults = check_top(doc)
        checks.append("V1")
    if d is not None:
        el, more = check_elements(d)
        faults = faults + more + check_consistency(el)
        checks.append("V2")
        if repo is not None:
            cited, now = check_sources(el, repo)
            faults = faults + cited
            checks.append("V3")
            drift, state, found = check_manifest(manifest, sha, now)
            faults = faults + drift
            if manifest is not None and os.path.exists(manifest):
                checks.append("manifest")
    blocking = [f for f in faults if f["code"] not in REPORT_ONLY]
    status: Literal["passed", "failed"] = "failed" if blocking or d is None or el is None else "passed"
    fresh, cover = section(faults, "freshness"), section(faults, "coverage")
    freshness: FreshnessDoc = {"faults": fresh["faults"], "counts": fresh["counts"], "manifest": state,
                               "sources_sha256": sources_digest(now) if now else None,
                               "raw_provenance": found["raw_provenance"] if found else "unknown"}
    coverage: CoverageDoc = {"faults": cover["faults"], "counts": cover["counts"], "inventory": "missing",
                             "files_total": 0, "collected": 0, "excluded": 0, "unsupported": 0, "failed": 0,
                             "no_symbols": 0, "languages_not_collected": []}
    language = _text(d, "language")
    return {"status": status, "generation_id": found["generation_id"] if found and state == "ok" else None,
            "codegraph_sha256": sha or None,
            "language": language, "source_tool": _text(d, "source_tool"), "repo_commit": _text(d, "repo_commit"),
            "nodes": len(el.nodes) if el else 0, "edges": len(el.edges) if el else 0,
            "modules": len(el.modules) if el else 0, "checks_run": checks,
            "integrity": section(faults, "integrity"), "freshness": freshness, "coverage": coverage,
            "capabilities": capabilities_of(language), "fit": fit_of(status, checks, freshness, blocking),
            "total": len(faults), "faults": faults}


def _replace(keep: str, drop: str, doc: VerifyDoc) -> None:
    """다른 쪽 결과 파일을 먼저 지우고 이쪽을 쓴다 — 도중에 끊겨도 두 파일이 함께 남지 않는다."""
    if os.path.exists(drop):
        os.remove(drop)
    write_json_atomic(keep, doc, indent=1, trailing_newline=True)


def main(argv: Sequence[str] | None = None) -> int:
    """`verify` 를 돌려 결과 파일 하나를 쓰고 다른 하나를 지운다. 통과면 0, 결함이면 1."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("codegraph", help="검사할 codegraph.json")
    ap.add_argument("--repo", default=None, help="근거 층(V3)의 기준 저장소. 없으면 V3 와 manifest 대조를 건너뛴다")
    ap.add_argument("--manifest", default=None, help="prep 이 쓴 collect-fingerprint.json. 없으면 freshness-unknown")
    ap.add_argument("--faults", required=True, help="결함이 있으면 쓰는 graph-faults.json")
    ap.add_argument("--passed", required=True, help="통과하면 쓰는 graph-verified.json")
    a = ap.parse_args(argv)
    got = verify(a.codegraph, a.repo, a.manifest)
    if got["status"] == "passed":
        _replace(a.passed, a.faults, got)
        print("%s — 통과 · 노드 %d · 간선 %d · 모듈 %d" % (a.passed, got["nodes"], got["edges"], got["modules"]))
        return 0
    _replace(a.faults, a.passed, got)
    counts = sorted(Counter(f["code"] for f in got["faults"]).items())
    print("%s — 결함 %d건 · %s" % (a.faults, got["total"], " · ".join("%s %d" % kv for kv in counts)), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
