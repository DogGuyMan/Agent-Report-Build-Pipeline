#!/usr/bin/env python3
"""골든 저장소의 수집 원본과 코드 지도를 읽어 메서드 · 멤버 · 관계 수를 센다. 아무것도 고치지 않는다.

    GRAPHICS_REPO=<C++ 저장소> CSHARP_REPO=<C# 저장소> python3 raw_counts.py
"""
import collections
import json
import os


def load(repo: str, name: str) -> dict:
    with open(os.path.join(repo, "out", "codegraph-raw", name), encoding="utf-8") as f:
        return json.load(f)


def graph_summary(repo: str) -> None:
    g = load(repo, "codegraph.json")
    print("  지도", g["language"], g["repo_commit"], g["source_tool"])
    print("  노드 %d · 간선 %d" % (len(g["nodes"]), len(g["edges"])))
    print("  노드 종류", collections.Counter(n["kind"] for n in g["nodes"]).most_common())
    print("  간선 종류", collections.Counter(e["kind"] for e in g["edges"]).most_common())
    first = sum(1 for n in g["nodes"] if n["kind"] != "external")
    print("  1차 노드 %d" % first)


def cpp(repo: str) -> None:
    print("C++ full_class_all.json")   # 골든 지도의 원본이다. full_class.json 은 일부 요소만 담는다.
    d = load(repo, "full_class_all.json")
    elements = d["elements"]
    print("  요소 %d · 메서드 %d · 멤버 %d" % (len(elements),
                                         sum(len(e.get("methods") or []) for e in elements),
                                         sum(len(e.get("members") or []) for e in elements)))
    print("  관계 종류", collections.Counter(r.get("type") for r in d["relationships"]).most_common())
    graph_summary(repo)


def csharp(repo: str) -> None:
    print("C# roslyn-dump.json")
    d = load(repo, "roslyn-dump.json")
    types, relations = d["types"], d["relations"]
    print("  타입 %d · 소스 타입 %d · 메서드 %d · 멤버 %d" % (len(types), sum(1 for t in types if t.get("file")),
                                                     sum(len(t.get("methods") or []) for t in types),
                                                     sum(len(t.get("members") or []) for t in types)))
    print("  관계 종류", collections.Counter(r["kind"] for r in relations).most_common())
    print("  depend 출처", collections.Counter(r.get("origin") for r in relations if r["kind"] == "depend").most_common())
    graph_summary(repo)


if __name__ == "__main__":
    cpp(os.environ["GRAPHICS_REPO"])
    csharp(os.environ["CSHARP_REPO"])
