#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='terms_db.py']"/>
# 코드베이스의 용어를 한 곳에 모은 사전을 만드는 도구. Mode 1.5 의 재료가 여기서 나온다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""terms_db.py — 코드베이스 용어 전수 수집.

입력은 normalize.py 가 낸 codegraph.json 이며 그 실제 키를 따른다.
  노드  id / name / kind / module / file / line
  간선  from / to / kind / label / file / line   (source/target 이 아니다)
  모듈  id / depends_on                          (name/files 가 아니다)

  terms_db.py [codegraph.json] --repo <저장소> [--reading terms-reading.json] [-o 출력디렉토리]

  codegraph.json 만       -> 정형문 terms-db.json. 투영이 입력의 상위집합인지 대조만 한다
  --reading 만            -> LLM 읽기 레코드로 terms-db.json 을 만들고 codegraph.json 을 투영해 쓴다
  둘 다                   -> 합친다. 구조는 codegraph 가 이긴다
  종료 코드 1 = 인용 실패(L1/L2) 또는 투영이 codegraph 를 다 담지 못함. 근거 없음(L3)은 0

⚠ --reading 만 준 실행은 투영한 codegraph.json 을 출력 디렉토리에 **쓴다.** 기본 출력 자리가
<repo>/out/codegraph-raw 라 거기 있던 지도를 덮는다. 원본을 지키려면 -o 로 다른 자리를 준다.
"""
import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import Literal, NotRequired, TypedDict, cast

from codegraph_types import CodeGraph, Edge, EdgeKind, Node
from verify_citations import short
from xmldoc import Terms


# 지도의 노드가 되지 않는 용어 종류. 사람이 부르는 이름(파일·산출물·JSON 키·개념)은 terms-db 에만 산다.
NON_NODE_KINDS = frozenset({"file", "module", "artifact", "key", "concept"})
# reading 레코드가 쓸 수 있는 kind 전부. codegraph 에서 온 kind 는 검사하지 않는다(정적 도구의 어휘).
KINDS = frozenset({"class", "struct", "enum", "interface", "delegate", "record", "external",
                   "function"}) | NON_NODE_KINDS
# LLM 이 쓸 수 있는 간선 종류.
# ⚠ normalize.py 의 어휘는 이보다 넓다 — instantiation · friendship 도 낸다.
#   정적 도구가 낸 간선은 check_terms 가 어휘를 판정하지 않으므로 여기 넣지 않는다.
EDGE_KINDS = frozenset({"inheritance", "realization", "composition", "aggregation",
                        "association", "dependency"})
SOURCES = frozenset({"codegraph", "reading", "codegraph+reading"})

# LLM 이 덮어쓸 수 있는 필드. 열쇠에 Literal 형을 박아야 TypedDict 첨자가 풀린다.
READING_WINS: tuple[Literal["means", "does"], ...] = ("means", "does")


# ── terms-db.json 레코드의 모양. terms-reading.json 쪽은 `xmldoc.Term` 이 정본이고
#    `merge_terms` 가 그것을 그대로 받는다. 여기 두 자리는 그보다 넓다:
#      module   소속이 없는 노드가 있어 None 이 온다
#      label    상속처럼 멤버가 없는 간선은 None 이다
#    `Term`/`Use` 는 둘 다 `str` 이라 물려받을 수 없다(TypedDict 는 필드 형을 넓히지 못한다).

# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.DbUse']"/>
# 용어 사전 레코드 안의 uses 리스트에 들어가는 항목 하나가 어떤 모양이어야 하는지 정의하는 타입 틀(TypedDict)이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.TermRecord
class DbUse(TypedDict):
    """레코드의 `uses[]` 한 칸. `source` 는 merge_terms 가 LLM 이 보탠 간선에만 남긴다."""
    to: str
    kind: str
    label: str | None
    where: str
    source: NotRequired[str]


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.TermRecord']"/>
# 용어 사전(terms-db.json) 안에 들어가는 레코드 하나의 모양을 정해 놓은 타입 틀(TypedDict)이다.
# 쓰는 것: machine.terms_db.DbUse · 쓰이는 곳: machine.terms_db.merge_terms
class TermRecord(TypedDict):
    """용어 하나. `id` 는 codegraph 에서 온 레코드에만 있다 — reading 레코드는 키가 곧 이름이다."""
    kind: str
    module: str | None
    where: str
    means: str
    uses: list[DbUse]
    neighbors: list[str]
    source: str
    id: NotRequired[str]
    does: NotRequired[str]
    confidence: NotRequired[str]
    hotspot: NotRequired[bool]


# {용어 이름: 레코드}. terms-db.json 최상위가 이 모양이다.
TermsDb = dict[str, TermRecord]


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._where']"/>
# 코드 지도의 노드나 간선 하나가 파일의 어디에 있는지를 사람이 읽기 쉬운 문자열로 바꾸는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.build_terms
def _where(node: Node | Edge) -> str:
    """`file:line` 위치 문자열. 파일이 없으면(외부 노드) 빈 문자열."""
    f = node.get("file") or ""
    ln = node.get("line")
    if not f:
        return ""
    return f"{f}:{ln}" if ln else f


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._split_where']"/>
# "파일경로:줄번호" 꼴 문자열을 다시 파일 경로와 줄 번호 두 조각으로 나누는 함수다. _where 의 반대 방향이다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.check_terms, machine.terms_db.project_codegraph
def _split_where(where: str) -> tuple[str | None, int | None]:
    """`file:line` -> (file, line). 빈 문자열이면 (None, None). 줄 번호가 없으면 (file, None)."""
    if not where:
        return None, None
    path, sep, ln = where.rpartition(":")
    if sep and ln.isdigit():
        return path, int(ln)
    return where, None


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._recompute_neighbors']"/>
# 용어 사전 전체를 훑어서 각 용어가 누구와 이웃인지(서로 연결돼 있는지)를 다시 계산하는 함수다. uses 는 방향이 있는 관계이고 neighbors 는 방향이 없는 관계다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.build_terms, machine.terms_db.merge_terms
def _recompute_neighbors(db: TermsDb) -> None:
    """uses(방향 있음)에서 neighbors(방향 없음)를 다시 센다.

    모듈 레코드의 기존 이웃(depends_on)만 지킨다. 나머지 손으로 쓴 neighbors 는 여기서 덮인다.
    """
    near: dict[str, set[str]] = {}
    for key, rec in db.items():
        near[key] = set(rec.get("neighbors", [])) if rec.get("kind") == "module" else set()
    for key, rec in db.items():
        for u in rec.get("uses", []):
            t = u.get("to")
            if t in db and t != key:
                near[key].add(t)
                near[t].add(key)
    for key, rec in db.items():
        rec["neighbors"] = sorted(x for x in near[key] if x)


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.build_terms']"/>
# codegraph.json(정적 코드 지도)을 읽어서 용어 사전(딕셔너리) 하나로 만드는 함수다.
# 쓰는 것: machine.terms_db._where, machine.terms_db._recompute_neighbors · 쓰이는 곳: machine.terms_db.main, machine.test_normalize.test_terms_db_extracts_modules_and_classes, machine.test_normalize.test_terms_db_is_deterministic, machine.test_normalize.test_terms_db_means_is_never_empty, machine.test_terms_db.test_build_terms_keeps_id_and_typed_uses (+8)
def build_terms(graph: CodeGraph, facts: Mapping[str, object],
                hotspot: Sequence[Mapping[str, str]]) -> TermsDb:
    """codegraph.json 에서 용어 사전을 만든다. 입력이 같으면 출력도 같다.

    facts 는 쓰지 않는다(시그니처만 고정). hotspot 은 {"name": ...} 목록이며
    이름이 용어에 있으면 hotspot 표시만 붙인다.

    간선은 방향 · 종류 · 위치를 지켜 uses[] 에 담는다 — 이것이 있어야 project_codegraph 가
    codegraph.json 을 되돌릴 수 있다(codegraph ⊂ terms-db).
    """
    db: TermsDb = {}
    nodes = graph.get("nodes", [])
    by_id = {n.get("id"): n for n in nodes}

    for node in nodes:
        name = node.get("name")
        if not name:
            continue
        db[name] = {
            "id": node.get("id") or name,
            "kind": node.get("kind", "type"),
            "module": node.get("module", ""),
            "where": _where(node),
            "means": "",
            "uses": [],
            "neighbors": [],
            "source": "codegraph",
        }

    # 간선 -> uses. from/to 는 노드 id 이므로 이름으로 바꿔 담는다(용어 키는 이름이다).
    for e in graph.get("edges", []):
        s, t = by_id.get(e.get("from")), by_id.get(e.get("to"))
        if not s or not t:
            continue
        src, dst = db.get(s.get("name")), t.get("name")
        if src is None or not dst or dst not in db:
            continue
        src["uses"].append({
            "to": dst,
            "kind": e.get("kind", "dependency"),
            "label": e.get("label"),
            "where": _where(e),
        })

    # 모듈 — 소속 타입 수와 의존 모듈은 codegraph 가 이미 아는 사실이다.
    members: dict[str, int] = {}
    for node in nodes:
        m = node.get("module")
        if m:
            members[m] = members.get(m, 0) + 1

    for m in graph.get("modules", []):
        name = m.get("id")
        if not name or name in db:
            continue
        depends_on = sorted(m.get("depends_on", []))
        means = f"타입 {members.get(name, 0)}개를 묶은 모듈."
        if depends_on:
            means += " " + ", ".join(depends_on[:5]) + " 모듈에 의존한다."
        db[name] = {
            "id": name,
            "kind": "module",
            "module": name,
            "where": "",
            "means": means,
            "uses": [],
            "neighbors": depends_on,
            "source": "codegraph",
        }

    _recompute_neighbors(db)

    # 정형문 means — 이웃이 가장 값싼 설명 재료다. LLM 읽기가 붙으면 merge_terms 가 덮어쓴다.
    for name, rec in db.items():
        if rec["kind"] == "module":
            continue
        near = rec["neighbors"]
        means = f"{rec['module']} 모듈의 {rec['kind']}."
        if near:
            means += " " + ", ".join(near[:5]) + " 와(과) 이어져 있다."
        rec["means"] = means

    for h in hotspot:
        name = h.get("name") if isinstance(h, dict) else None
        if name and name in db:
            db[name]["hotspot"] = True

    return dict(sorted(db.items()))


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.project_codegraph']"/>
# 용어 사전을 거꾸로 codegraph.json 모양으로 되돌리는 함수다.
# 쓰는 것: machine.terms_db._split_where · 쓰이는 곳: machine.terms_db.main, machine.test_terms_db.test_project_drops_terms_that_are_not_code, machine.test_terms_db.test_project_golden_is_superset_of_real_codegraph, machine.test_terms_db.test_project_round_trips_synthetic_graph
def project_codegraph(db: TermsDb, language: str = "unknown",
                      repo_commit: str = "") -> CodeGraph:
    """terms-db -> codegraph.json (schema_version 2). codegraph 는 terms-db 의 부분집합이다.

    노드 = NON_NODE_KINDS 가 아닌 레코드. 간선 = uses 중 양끝이 노드인 것.
    모듈 의존 = 서로 다른 모듈의 노드 간 간선. 접기 키는 (from, to, kind) — 둘 다 normalize.py 와
    같은 규칙이라, 한쪽을 바꾸면 투영 대조가 깨진다.
    """
    nodes: dict[str, Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}
    node_id: dict[str, str] = {}
    for key, rec in db.items():
        if rec.get("kind") in NON_NODE_KINDS:
            continue
        nid = rec.get("id") or key
        f, ln = _split_where(rec.get("where", ""))
        nodes[nid] = {"id": nid, "name": key, "kind": rec.get("kind"),
                      "module": rec.get("module", ""), "file": f, "line": ln}
        node_id[key] = nid

    for key, rec in db.items():
        if key not in node_id:
            continue
        for u in rec.get("uses", []):
            t = u.get("to")
            if t not in node_id:
                continue          # artifact / key / concept 로 가는 간선은 지도에 없다
            # ⚠ cast — 사전의 uses[].kind 는 자유 문자열이고 지도의 간선 종류는 Literal
            #   (`EdgeKind`) 이다. 어휘 검사는 check_terms 가 EDGE_KINDS 로 따로 한다.
            kind = cast(EdgeKind, u.get("kind", "dependency"))
            k = (node_id[key], node_id[t], kind)
            if k in edges:
                edges[k]["occurrences"] = edges[k].get("occurrences", 1) + 1
                continue
            f, ln = _split_where(u.get("where", ""))
            edges[k] = {"from": node_id[key], "to": node_id[t], "kind": kind,
                        "label": u.get("label"), "file": f, "line": ln}
            if nodes[node_id[t]]["kind"] == "external":
                edges[k]["constraint"] = False   # R6 — 섬으로 가는 간선

    modules = sorted({n["module"] for n in nodes.values() if n["module"] and n["kind"] != "external"})
    mod_dep: dict[str, set[str]] = {}
    for e in edges.values():
        a, b = nodes[e["from"]], nodes[e["to"]]
        if b["kind"] == "external" or not a["module"] or not b["module"]:
            continue
        if a["module"] != b["module"]:
            mod_dep.setdefault(a["module"], set()).add(b["module"])

    return {
        "schema_version": 2,
        "language": language,
        "platform": sys.platform,
        "source_tool": "terms-db",
        "repo_commit": repo_commit,
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "modules": [{"id": m, "depends_on": sorted(mod_dep.get(m, ()))} for m in modules],
    }


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._stem']"/>
# 용어 이름에서 인용 대조에 쓸 짧은 조각을 뽑아내는 함수다.
# 쓰는 것: machine.verify_citations.short · 쓰이는 곳: machine.terms_db.check_terms
def _stem(key: str, kind: str) -> str:
    """L3 대조용 이름 조각. `calls[]` -> `calls`, `Outer::Inner` -> `Inner`, `terms_db.main` -> `main`.
    파일 · 산출물 · 키 · 개념 · 모듈은 글자 그대로 (`codegraph.json` 을 `.` 로 쪼개면 안 된다)."""
    k = key[:-2] if key.endswith("[]") else key
    if kind in NON_NODE_KINDS:
        return k
    return short(k)


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._written_by_llm']"/>
# 용어 사전의 한 uses 항목(간선)이 LLM(전수조사)이 쓴 것인지, 아니면 정적 분석 도구가 자동으로 만든 것인지를 가려내는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.check_terms
def _written_by_llm(rec_source: str, use: DbUse) -> bool:
    """이 간선을 LLM 이 썼는가. 표시가 없는 간선은 정적 도구가 낸 것이다.

    codegraph+reading 레코드의 uses 에는 두 출처가 섞여 있고, merge_terms 가 LLM 이 보탠
    간선에만 source="reading" 을 남긴다. 그 표시가 유일한 구분 근거다.
    """
    return rec_source == "reading" or use.get("source") == "reading"


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.check_terms']"/>
# 용어 사전(terms-db) 안에서 사람(LLM)이 직접 쓴 부분이 실제 코드 위치와 맞는지 검사하는 함수다. 기계가 자동으로 만든 부분은 다시 검사하지 않는다.
# 쓰는 것: machine.terms_db._split_where, machine.terms_db._stem, machine.terms_db._written_by_llm · 쓰이는 곳: machine.terms_db.main, machine.test_terms_db.test_check_does_not_judge_edge_kinds_that_came_from_codegraph, machine.test_terms_db.test_check_flags_unknown_uses_target, machine.test_terms_db.test_check_l1_missing_file_is_failure, machine.test_terms_db.test_check_l2_line_past_eof_is_failure (+4)
def check_terms(db: TermsDb, repo: str) -> list[tuple[str, str, str]]:
    """3값 판정 목록 [(등급, 용어, 사유)]. 등급은 "실패" | "근거 없음". 비어 있으면 전부 통과.

    검사 대상은 LLM 이 쓴 부분만이다 — source 가 reading 인 레코드의 where 와,
    reading 이 보탠 uses 의 where. codegraph 에서 온 위치는 여기서 재판정하지 않는다.
      L1 파일이 있나            -> 실패
      L2 그 줄이 있나           -> 실패
      L3 근처에 그 이름이 있나   -> 근거 없음 (앞 1줄 · 뒤 1줄까지 본다)
    """
    out: list[tuple[str, str, str]] = []
    cache: dict[str, list[str] | None] = {}

    def lines_of(rel: str) -> list[str] | None:
        if rel not in cache:
            try:
                cache[rel] = open(os.path.join(repo, rel), encoding="utf-8",
                                  errors="replace").read().splitlines()
            except OSError:
                cache[rel] = None
        return cache[rel]

    def cite(term: str, where: str, stem: str, what: str) -> None:
        f, ln = _split_where(where)
        if not f:
            return
        lines = lines_of(f)
        if lines is None:
            out.append(("실패", term, f"{what} L1 파일 없음: {f}"))
            return
        if not ln or ln > len(lines):
            out.append(("실패", term, f"{what} L2 줄 없음: {where} (파일은 {len(lines)}줄)"))
            return
        window = "\n".join(lines[max(0, ln - 2):ln + 1])
        if stem and stem not in window:
            out.append(("근거 없음", term, f"{what} L3 그 줄 근처에 '{stem}' 이 없다: {where}"))

    for key, rec in db.items():
        src = rec.get("source")
        if src not in SOURCES:
            out.append(("실패", key, f"source 값이 이상하다: {src!r}"))
            continue
        for fld in ("kind", "module", "where", "means", "neighbors"):
            if fld not in rec:
                out.append(("실패", key, f"필수 필드 없음: {fld}"))
        if not str(rec.get("means", "")).strip():
            out.append(("실패", key, "means 가 비었다"))
        for u in rec.get("uses", []):
            if not _written_by_llm(src, u):
                continue      # 정적 도구가 낸 간선 — 그 어휘와 대상은 여기서 재판정하지 않는다
            if u.get("to") not in db:
                out.append(("실패", key, f"uses.to 가 용어에 없다: {u.get('to')!r}"))
            if u.get("kind") not in EDGE_KINDS:
                out.append(("실패", key, f"uses.kind 값이 이상하다: {u.get('kind')!r}"))
        if src == "codegraph":
            continue
        if src == "reading":
            if rec.get("kind") not in KINDS:
                out.append(("실패", key, f"kind 값이 이상하다: {rec.get('kind')!r}"))
            if rec.get("kind") not in ("module", "external") and not rec.get("where"):
                out.append(("실패", key, "reading 레코드는 where 가 있어야 한다 — 인용 없는 뜻은 싣지 않는다"))
            cite(key, rec.get("where", ""), _stem(key, rec.get("kind")), "where")
        for u in rec.get("uses", []):
            if _written_by_llm(src, u):
                t = u.get("to")
                stem = _stem(t, db[t].get("kind")) if t in db else ""
                cite(key, u.get("where", ""), stem, f"uses->{t}")
    return out


# LLM 이 덮어쓸 수 없는 필드. 구조의 출처는 codegraph 하나다(D3).
STRUCTURE_FIELDS = ("id", "kind", "module", "where")


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.merge_terms']"/>
# LLM 이 읽고 쓴 용어 레코드(reading)를 codegraph 가 만든 기본 사전(base)에 합치는 함수다.
# 쓰는 것: machine.terms_db._recompute_neighbors, machine.terms_db.TermRecord · 쓰이는 곳: machine.terms_db.main, machine.test_terms_db.test_check_does_not_judge_edge_kinds_that_came_from_codegraph, machine.test_terms_db.test_check_flags_unknown_uses_target, machine.test_terms_db.test_check_l1_missing_file_is_failure, machine.test_terms_db.test_check_l2_line_past_eof_is_failure (+6)
def merge_terms(base: TermsDb, reading: Terms) -> TermsDb:
    """reading(LLM 이 쓴 것)을 base(codegraph 가 만든 것)에 합친다. 구조 필드는 codegraph 가 이긴다.

    - 같은 키가 base 에 있으면: means · does 를 덮고, (to, kind) 가 새로운 uses 만 더한다.
      더한 uses 에는 source="reading" 표시를 남긴다 — check_terms 가 그 인용만 본다.
    - 없으면: reading 레코드를 그대로 넣는다 (source="reading").
    - neighbors 는 마지막에 전부 다시 센다. 입력 dict 는 바꾸지 않는다.
    """
    db: TermsDb = {k: {**v, "uses": [{**u} for u in v.get("uses", [])]} for k, v in base.items()}
    for key, r in reading.items():
        if key in db:
            rec = db[key]
            for fld in READING_WINS:
                값 = r.get(fld)
                if 값:
                    rec[fld] = 값
            seen = {(u.get("to"), u.get("kind")) for u in rec["uses"]}
            for u in r.get("uses", []):
                sig = (u.get("to"), u.get("kind"))
                if sig not in seen:
                    rec["uses"].append({**u, "source": "reading"})
                    seen.add(sig)
            rec["source"] = "codegraph+reading"
        else:
            # ⚠ cast — reading 레코드에는 neighbors 가 없다. 아래 setdefault 가 자리를 채우고
            #   끝의 _recompute_neighbors 가 사전 전체를 다시 센다.
            rec = cast(TermRecord, dict(r))
            rec.setdefault("uses", [])
            rec.setdefault("neighbors", [])
            rec["source"] = "reading"
            db[key] = rec
    _recompute_neighbors(db)
    return dict(sorted(db.items()))


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db._git_commit']"/>
# 주어진 저장소 경로에서 현재 git 커밋 해시(HEAD)를 읽어오는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.terms_db.main
def _git_commit(repo: str) -> str:
    """저장소 HEAD. git 이 없거나 저장소가 아니면 빈 문자열 — 실패시키지 않는다."""
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


# <include file="machine/comments.xml" path="//term[@id='machine.terms_db.main']"/>
# terms_db.py 를 명령줄에서 실행했을 때 시작점이 되는 함수다.
# 쓰는 것: machine.terms_db.build_terms, machine.terms_db.project_codegraph, machine.terms_db.check_terms, machine.terms_db.merge_terms, machine.terms_db._git_commit · 쓰이는 곳: 없음
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codegraph", nargs="?", help="normalize.py 가 낸 codegraph.json. 없으면 --reading 만으로 만든다")
    ap.add_argument("--repo", required=True, help="인용 경로의 기준 저장소")
    ap.add_argument("--reading", help="LLM 전수조사 결과 terms-reading.json")
    ap.add_argument("-o", "--out", help="출력 디렉토리. 기본: codegraph.json 옆, 없으면 <repo>/out/codegraph-raw")
    a = ap.parse_args()
    if not a.codegraph and not a.reading:
        ap.error("codegraph.json 이나 --reading 중 하나는 있어야 한다")
    repo = os.path.abspath(os.path.expanduser(a.repo))

    g: CodeGraph | None = None
    db: TermsDb = {}
    if a.codegraph:
        # 한 칸 거쳐 담는다 — `g` 는 아래에서 없을 수도 있는 값이라 CodeGraph | None 이다.
        loaded: CodeGraph = json.load(open(a.codegraph, encoding="utf-8"))
        g = loaded
        db = build_terms(loaded, facts={}, hotspot=[])
    if a.reading:
        reading: Terms = json.load(open(a.reading, encoding="utf-8"))
        db = merge_terms(db, reading)

    if a.out:
        base = a.out
    elif a.codegraph:
        base = os.path.dirname(os.path.abspath(a.codegraph))
    else:
        base = os.path.join(repo, "out", "codegraph-raw")
    os.makedirs(base, exist_ok=True)

    problems = check_terms(db, repo)
    for lvl, term, why in problems:
        print(f"  {lvl}  {term}  {why}")
    fails = [p for p in problems if p[0] == "실패"]

    path = os.path.join(base, "terms-db.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"{path} — 용어 {len(db)}개 / 실패 {len(fails)} / 근거 없음 {len(problems) - len(fails)}")

    lang = g.get("language", "unknown") if g else "unknown"
    commit = (g.get("repo_commit") if g else None) or _git_commit(repo)
    proj = project_codegraph(db, language=lang, repo_commit=commit)
    if g is not None:
        missing = {n["id"] for n in g["nodes"]} - {n["id"] for n in proj["nodes"]}
        print(f"투영 대조 — codegraph 노드 {len(g['nodes'])}개 중 투영에 없는 것 {len(missing)}개"
              + (f": {sorted(missing)[:5]}" if missing else ""))
        if missing:
            fails.append(("실패", "(투영)", "codegraph 가 terms-db 의 부분집합이 아니다"))
    else:
        cg = os.path.join(base, "codegraph.json")
        with open(cg, "w", encoding="utf-8") as f:
            json.dump(proj, f, ensure_ascii=False, indent=2)
        print(f"{cg} — 노드 {len(proj['nodes'])} 간선 {len(proj['edges'])} 모듈 {len(proj['modules'])} (terms-db 의 투영)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
