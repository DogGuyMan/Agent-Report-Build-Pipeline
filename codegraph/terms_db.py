#!/usr/bin/env python3
"""terms_db.py — 코드베이스 용어 전수 수집.

**왜 필요한가.** Mode 1.5(용어 이해도 점검)가 사람에게 문제를 내려면 정답지가 있어야 한다.
그 정답지를 LLM 이 매번 새로 지어내면 세션마다 설명이 흔들린다. 여기서 한 번 뽑아 고정한다.

**이 파일은 판정하지 않는다.** 기계가 아는 사실(이름, 종류, 위치, 이웃)만 적는다.
사람이 읽을 설명은 Mode 1.5 가 LLM 으로 채우고 사용자가 검수한다.

입력은 normalize.py 가 낸 codegraph.json 이며 그 실제 키를 따른다.
  노드  id / name / kind / module / file / line
  간선  from / to / kind / label / file / line   (source/target 이 아니다)
  모듈  id / depends_on                          (name/files 가 아니다)

  terms_db.py [codegraph.json] --repo <저장소> [--reading terms-reading.json] [-o 출력디렉토리]

  codegraph.json 만       -> 정형문 terms-db.json. 투영이 입력의 상위집합인지 대조만 한다
  --reading 만            -> LLM 읽기 레코드로 terms-db.json 을 만들고 codegraph.json 을 투영해 쓴다
  둘 다                   -> 합친다. 구조는 codegraph 가 이긴다
  종료 코드 1 = 인용 실패(L1/L2) 또는 투영이 codegraph 를 다 담지 못함. 근거 없음(L3)은 0
"""
import argparse
import json
import os
import subprocess
import sys

from verify_citations import short


# 지도의 노드가 되지 않는 용어 종류. 사람이 부르는 이름(파일·산출물·JSON 키·개념)은 terms-db 에만 산다.
NON_NODE_KINDS = frozenset({"file", "module", "artifact", "key", "concept"})
# reading 레코드가 쓸 수 있는 kind 전부. codegraph 에서 온 kind 는 검사하지 않는다(정적 도구의 어휘).
KINDS = frozenset({"class", "struct", "enum", "interface", "delegate", "record", "external",
                   "function"}) | NON_NODE_KINDS
# LLM 이 쓸 수 있는 간선 종류. 새 종류를 만들지 않는다.
# ⚠ normalize.py 는 이보다 넓다 — instantiation · friendship 도 낸다(normalize.py:25-29).
#   정적 도구의 어휘는 check_terms 가 판정하지 않으므로 여기 넣지 않는다.
EDGE_KINDS = frozenset({"inheritance", "realization", "composition", "aggregation",
                        "association", "dependency"})
SOURCES = frozenset({"codegraph", "reading", "codegraph+reading"})


def _where(node):
    """`file:line` 위치 문자열. 파일이 없으면(외부 노드) 빈 문자열."""
    f = node.get("file") or ""
    ln = node.get("line")
    if not f:
        return ""
    return f"{f}:{ln}" if ln else f


def _split_where(where):
    """`file:line` -> (file, line). 빈 문자열이면 (None, None). 줄 번호가 없으면 (file, None)."""
    if not where:
        return None, None
    path, sep, ln = where.rpartition(":")
    if sep and ln.isdigit():
        return path, int(ln)
    return where, None


def _recompute_neighbors(db):
    """uses(방향 있음)에서 neighbors(방향 없음)를 다시 센다.

    모듈 레코드의 기존 이웃(depends_on)은 지킨다. 손으로 쓴 neighbors 는 여기서 덮인다 —
    neighbors 는 파생값이지 입력이 아니다.
    """
    near = {}
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


def build_terms(graph, facts, hotspot):
    """codegraph.json 에서 용어 사전을 만든다. 입력이 같으면 출력도 같다.

    facts 는 현재 쓰지 않는다(시그니처만 고정). hotspot 은 {"name": ...} 목록이며
    이름이 용어에 있으면 hotspot 표시만 붙인다.

    간선은 방향 · 종류 · 위치를 지켜 uses[] 에 담는다 — 이것이 있어야 project_codegraph 가
    codegraph.json 을 되돌릴 수 있다(codegraph ⊂ terms-db).
    """
    db = {}
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
    members = {}
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


def project_codegraph(db, language="unknown", repo_commit=""):
    """terms-db -> codegraph.json (schema_version 2). codegraph 는 terms-db 의 부분집합이다.

    노드 = NON_NODE_KINDS 가 아닌 레코드. 간선 = uses 중 양끝이 노드인 것.
    모듈 의존 = 서로 다른 모듈의 노드 간 간선 (normalize.py:268-276 과 같은 규칙).
    접기 키 (from, to, kind) 도 normalize.py:231 과 같다.
    """
    nodes, edges, node_id = {}, {}, {}
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
            kind = u.get("kind", "dependency")
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
    mod_dep = {}
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


def _stem(key, kind):
    """L3 대조용 이름 조각. `calls[]` -> `calls`, `Outer::Inner` -> `Inner`, `terms_db.main` -> `main`.
    파일 · 산출물 · 키 · 개념 · 모듈은 글자 그대로 (`codegraph.json` 을 `.` 로 쪼개면 안 된다)."""
    k = key[:-2] if key.endswith("[]") else key
    if kind in NON_NODE_KINDS:
        return k
    return short(k)


def _written_by_llm(rec_source, use):
    """이 간선을 LLM 이 썼는가. 표시가 없는 간선은 정적 도구가 낸 것이다.

    합쳐진 레코드(codegraph+reading)의 uses 에는 두 출처가 섞여 있다. merge_terms 가
    LLM 이 보탠 것에만 source="reading" 을 남기므로 그것으로 가른다.
    """
    return rec_source == "reading" or use.get("source") == "reading"


def check_terms(db, repo):
    """3값 판정 목록 [(등급, 용어, 사유)]. 등급은 "실패" | "근거 없음". 비어 있으면 전부 통과.

    검사 대상은 **LLM 이 쓴 부분**만이다 — source 가 reading 인 레코드의 where 와,
    reading 이 보탠 uses 의 where. codegraph 에서 온 위치는 정적 도구의 사실이라 여기서
    재판정하지 않는다(verify_citations.py 가 위키 인용을 볼 때 함께 본다).
      L1 파일이 있나            -> 실패
      L2 그 줄이 있나           -> 실패
      L3 근처에 그 이름이 있나   -> 근거 없음 (verify_citations.py:116 과 같이 앞뒤 1줄까지)
    """
    out, cache = [], {}

    def lines_of(rel):
        if rel not in cache:
            try:
                cache[rel] = open(os.path.join(repo, rel), encoding="utf-8",
                                  errors="replace").read().splitlines()
            except OSError:
                cache[rel] = None
        return cache[rel]

    def cite(term, where, stem, what):
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


# LLM 이 덮어쓸 수 없는 필드. 정적 수집기가 있는 저장소에서 구조의 출처는 codegraph 하나다(D3).
STRUCTURE_FIELDS = ("id", "kind", "module", "where")


def merge_terms(base, reading):
    """reading(LLM 이 쓴 것)을 base(codegraph 가 만든 것)에 합친다. 구조 필드는 codegraph 가 이긴다.

    - 같은 키가 base 에 있으면: means · does 를 덮고, (to, kind) 가 새로운 uses 만 더한다.
      더한 uses 에는 source="reading" 표시를 남긴다 — check_terms 가 그 인용만 본다.
    - 없으면: reading 레코드를 그대로 넣는다 (source="reading").
    - neighbors 는 마지막에 전부 다시 센다. 입력 dict 는 바꾸지 않는다.
    """
    db = {k: dict(v, uses=[dict(u) for u in v.get("uses", [])]) for k, v in base.items()}
    for key, r in reading.items():
        if key in db:
            rec = db[key]
            for fld in ("means", "does"):
                if r.get(fld):
                    rec[fld] = r[fld]
            seen = {(u.get("to"), u.get("kind")) for u in rec["uses"]}
            for u in r.get("uses", []):
                sig = (u.get("to"), u.get("kind"))
                if sig not in seen:
                    rec["uses"].append(dict(u, source="reading"))
                    seen.add(sig)
            rec["source"] = "codegraph+reading"
        else:
            rec = dict(r)
            rec.setdefault("uses", [])
            rec.setdefault("neighbors", [])
            rec["source"] = "reading"
            db[key] = rec
    _recompute_neighbors(db)
    return dict(sorted(db.items()))


def _git_commit(repo):
    """저장소 HEAD. git 이 없거나 저장소가 아니면 빈 문자열 — 실패시키지 않는다."""
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


# 직접 실행됐을 때만 CLI 를 수행한다(scripts/*.mjs 와 같은 규약).
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codegraph", nargs="?", help="normalize.py 가 낸 codegraph.json. 없으면 --reading 만으로 만든다")
    ap.add_argument("--repo", required=True, help="인용 경로의 기준 저장소")
    ap.add_argument("--reading", help="LLM 전수조사 결과 terms-reading.json")
    ap.add_argument("-o", "--out", help="출력 디렉토리. 기본: codegraph.json 옆, 없으면 <repo>/out/codegraph-raw")
    a = ap.parse_args()
    if not a.codegraph and not a.reading:
        ap.error("codegraph.json 이나 --reading 중 하나는 있어야 한다")
    repo = os.path.abspath(os.path.expanduser(a.repo))

    g, db = None, {}
    if a.codegraph:
        g = json.load(open(a.codegraph, encoding="utf-8"))
        db = build_terms(g, facts={}, hotspot=[])
    if a.reading:
        db = merge_terms(db, json.load(open(a.reading, encoding="utf-8")))

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

    proj = project_codegraph(db, language=(g or {}).get("language", "unknown"),
                             repo_commit=(g or {}).get("repo_commit") or _git_commit(repo))
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
