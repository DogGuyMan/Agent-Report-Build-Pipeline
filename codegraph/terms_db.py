#!/usr/bin/env python3
"""terms_db.py — 코드베이스 용어 전수 수집.

**왜 필요한가.** Mode 1.5(용어 이해도 점검)가 사람에게 문제를 내려면 정답지가 있어야 한다.
그 정답지를 LLM 이 매번 새로 지어내면 세션마다 설명이 흔들린다. 여기서 한 번 뽑아 고정한다.

**이 파일은 판정하지 않는다.** 기계가 아는 사실(이름, 종류, 위치, 이웃)만 적는다.
사람이 읽을 설명은 Mode 1.5 가 LLM 으로 채우고 사용자가 검수한다.

입력은 normalize.py 가 낸 codegraph.json 이며 그 실제 키를 따른다.
  노드  id / name / kind / module / file / line
  간선  from / to               (source/target 이 아니다)
  모듈  id / depends_on         (name/files 가 아니다)

  terms_db.py <codegraph.json> --repo <저장소> [-o 출력디렉토리]
"""
import argparse
import json
import os


def _where(node):
    """`file:line` 위치 문자열. 파일이 없으면(외부 노드) 빈 문자열."""
    f = node.get("file") or ""
    ln = node.get("line")
    if not f:
        return ""
    return f"{f}:{ln}" if ln else f


def build_terms(graph, facts, hotspot):
    """codegraph.json 에서 용어 사전을 만든다. 입력이 같으면 출력도 같다.

    facts 는 현재 쓰지 않는다(시그니처만 고정). hotspot 은 {"name": ...} 목록이며
    이름이 용어에 있으면 hotspot 표시만 붙인다.
    """
    db = {}
    nodes = graph.get("nodes", [])
    by_id = {n.get("id"): n for n in nodes}

    # 이웃 — 무엇과 이어져 있는지가 용어를 설명하는 가장 값싼 재료다. 방향은 무시한다.
    neighbors = {}
    for e in graph.get("edges", []):
        s, t = e.get("from"), e.get("to")
        for a, b in ((s, t), (t, s)):
            if a in by_id and b in by_id:
                neighbors.setdefault(a, set()).add(by_id[b].get("name", ""))

    for node in nodes:
        name = node.get("name")
        if not name:
            continue
        kind = node.get("kind", "type")
        module = node.get("module", "")
        near = sorted(x for x in neighbors.get(node.get("id"), set()) if x)
        means = f"{module} 모듈의 {kind}."
        if near:
            means += " " + ", ".join(near[:5]) + " 와(과) 이어져 있다."
        db[name] = {
            "kind": kind,
            "module": module,
            "where": _where(node),
            "means": means,
            "neighbors": near,
            "source": "codegraph",
        }

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
            "kind": "module",
            "module": name,
            "where": "",
            "means": means,
            "neighbors": depends_on,
            "source": "codegraph",
        }

    for h in hotspot:
        name = h.get("name") if isinstance(h, dict) else None
        if name and name in db:
            db[name]["hotspot"] = True

    return dict(sorted(db.items()))


# 직접 실행됐을 때만 CLI 를 수행한다(scripts/*.mjs 와 같은 규약).
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph")
    ap.add_argument("--repo", required=True)
    ap.add_argument("-o", "--out", help="출력 디렉토리. 기본: codegraph.json 옆")
    a = ap.parse_args()

    g = json.load(open(a.codegraph, encoding="utf-8"))
    base = a.out or os.path.dirname(os.path.abspath(a.codegraph))
    os.makedirs(base, exist_ok=True)

    db = build_terms(g, facts={}, hotspot=[])
    path = os.path.join(base, "terms-db.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"{path} — 용어 {len(db)}개")


if __name__ == "__main__":
    main()
