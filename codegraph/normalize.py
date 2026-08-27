#!/usr/bin/env python3
"""normalize.py — 언어별 정적 분석 산출물을 codegraph.json(스키마 v2)으로 바꾼다.

Track C 의 정규화 계층이다. 접기 규칙(C-9 R1~R7)과 kind enum 사상이 **여기에만** 있다.
언어 도구는 원시 사실만 내고 정책은 전부 이 파일이 쥔다.

현재 구현: C++ (clang-uml JSON). C# (roslyn-dump.json)은 형식만 확정됐고 도구가 없다.

  python3 normalize.py --clang-uml <full_class_all.json> --repo <저장소> -o codegraph.json

거울 함정 경계 — 이 파일은 JSON 을 표로 바꾸는 스크립트다. 플러그인 구조·파서 레지스트리·
추상 인터페이스가 나오면 그 자체가 Track C 가 잡으려는 실패다.
"""
import argparse, json, os, subprocess, sys
from collections import Counter, defaultdict

# ── C++ 1차 코드로 볼 네임스페이스. 경로가 아니라 네임스페이스가 기준이다.
#    근거: std:: 타입 83건의 source_location 이 표준 헤더가 아니라 이 저장소의
#    첫 사용 지점을 가리킨다(관찰 보고서 F-1). 경로로 거르면 1st-party 로 오인한다.
CPP_FIRST_PARTY_NS = ("SJH", "TopdownShooter")

# ── D절 대응표. clang-uml 의 낱말과 codegraph enum 의 낱말이 겹치지만 뜻이 다르다.
#    항등 매핑을 쓰면 311건이 조용히 틀린 칸에 들어가고 오류도 나지 않는다.
CLANG_UML_KIND = {
    "aggregation": "composition",   # 값 멤버 (std::string detail)  -> UML 합성
    "association": "aggregation",   # 포인터·참조 멤버 (Actor* mOwner) -> UML 집약
    "dependency": "dependency",
    "instantiation": "instantiation",
    "friendship": "friendship",
    # "extension" 은 대상 노드의 is_abstract 를 봐야 갈린다 -> 아래 2-패스
    # "containment" 는 8종 enum 에 자리가 없다 -> **버린다** (2026-08-27 사용자 확정).
    #   선언 위치 관계이고 방향이 안쪽->바깥쪽이라 dependency 로 흡수하면 P4 의미축에서
    #   역방향 화살표 7개가 생겨 오독을 부른다. 버리되 수는 로그로 보고한다.
}

# ── R7. C++ 에서는 clang-uml 이 원시 타입을 element 로 승격하지 않아 실측상 해당 없음이지만,
#    다른 도구가 들어올 때를 위해 방어로 남긴다.
CPP_PRIMITIVES = {
    "void", "bool", "char", "signed char", "unsigned char", "wchar_t", "char8_t",
    "char16_t", "char32_t", "short", "int", "long", "long long", "float", "double",
    "long double", "size_t", "ptrdiff_t", "nullptr_t",
    "unsigned", "unsigned int", "unsigned short", "unsigned long", "unsigned long long",
}


def git_commit(repo):
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def module_of(path):
    """모듈 경계 = 폴더 트리. C# 쪽 결정(폴더 트리 9개)과 축을 맞춘다.

    src/render/renderer.h -> "render"      apps/TopdownShooter/main.cpp -> "apps/TopdownShooter"
    """
    if not path:
        return None
    parts = path.split("/")
    if parts[0] == "src" and len(parts) > 2:
        return parts[1]
    if parts[0] == "apps" and len(parts) > 2:
        return f"apps/{parts[1]}"
    return parts[0]


def load_clang_uml(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["elements"], d["relationships"], d.get("metadata", {})


def is_first_party(el):
    return (el.get("namespace") or "").split("::")[0] in CPP_FIRST_PARTY_NS


def external_group(el):
    """R2 — 외부 하나 = 노드 하나. 입도는 라이브러리·서브모듈 이름이다."""
    root = (el.get("namespace") or "").split("::")[0]
    if root == "std":
        return "(STL) std"
    if root:
        return root
    return "(기타) " + el.get("name", "?")


# ── R5 투과 대상. 규칙 문면이 명시한 것(vector/unique_ptr/shared_ptr/array/map)에
#    실측으로 확인된 같은 성격의 것만 더했다. 임의 확장이 아니다.
#
#    🔵 이 저장소의 std 노드 107개 분포 (2026-08-27):
#      투과함  vector 28 · unordered_map 27 · unique_ptr 25 · array 5 · shared_ptr 3
#              map 2 · pair 1 · optional 1 · set 1 · initializer_list 1        = 94
#      안 함   function 9 · basic_string 2 · time_point 1 · basic_string_view 1 = 13
#
#    ⚠ "std 네임스페이스의 템플릿 전부" 로 일반화하면 basic_string 까지 투과해
#    `(STL) std` 외부 노드가 통째로 사라지고 끝점 해소 실패가 47 -> 166 으로 는다.
#    목록을 쓰는 편이 규칙 문면에도 가깝고 손실도 적다(실측 대조).
STD_TRANSPARENT = {
    "vector", "unordered_map", "unique_ptr", "array", "shared_ptr", "weak_ptr",
    "map", "set", "unordered_set", "list", "deque", "pair", "tuple",
    "optional", "initializer_list",
}


def is_transparent_wrapper(el):
    """R5 — 컨테이너·스마트포인터는 노드로 만들지 않고 투과시킨다.

    ⚠ R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다. 🔵 실측 8건 —
    RenderUnit --mesh--> Mesh 등이 unique_ptr/vector 를 2홉으로 거쳐야만 보인다.
    """
    return (el.get("namespace") or "").split("::")[0] == "std" and el.get("name") in STD_TRANSPARENT


def member_location(src_el, label):
    """간선의 근거 위치. label(멤버 이름)로 members[] 를 정확히 찾는다.

    문자열 탐색이 아니라 구조 조회다. 🔵 실측 — 소유 간선 311건 전량이 유일 매칭되고
    모호한 것이 0건이다. **C-13 으로 소유 간선은 인용 검증 L3 의 판정 대상이 됐다.**
    나머지 종류(dependency/extension/instantiation/friendship)는 가리킬 멤버가 없어
    위치가 null 이고, 검증기는 그것을 "근거 없음" 으로 낸다(2값이 아니라 3값).
    """
    if not src_el or not label:
        return None, None
    hits = [m for m in (src_el.get("members") or []) if m.get("name") == label]
    if len(hits) != 1:
        return None, None
    loc = hits[0].get("source_location") or {}
    return loc.get("file"), loc.get("line")


def node_name(el):
    """중첩 타입의 name 은 구분자가 :: 가 아니라 ## 이고 바깥 클래스가 namespace 에 없다."""
    return el.get("display_name") or el.get("name")


def normalize_cpp(elements, relationships, repo, source_tool):
    by_id = {e["id"]: e for e in elements}
    by_display = {e.get("display_name"): e for e in elements}
    stats = Counter()

    # ── 1패스: 노드를 정한다. 투과 래퍼는 노드가 되지 않는다(R5).
    #    외부는 R2 로 접는다. 접힌 원본은 추적을 위해 남긴다.
    node_id = {}          # element id -> codegraph node id
    nodes = {}            # codegraph node id -> dict
    collapsed = defaultdict(list)
    wrappers = set()

    for e in elements:
        if is_transparent_wrapper(e):
            wrappers.add(e["id"]); stats["R5 투과 래퍼"] += 1
            continue
        if node_name(e) in CPP_PRIMITIVES:
            stats["R7 원시 타입 제외"] += 1
            continue
        if is_first_party(e):
            nid = "C%d" % (len(nodes) + 1)
            loc = e.get("source_location") or {}
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

    # ── R5 투과 해소. 래퍼로 가는 간선은 래퍼의 템플릿 인자로 갈아탄다.
    def resolve(eid, depth=0):
        """element id -> codegraph node id 목록. 래퍼면 인자로 내려간다."""
        if depth > 4:
            return []
        if eid in node_id:
            return [node_id[eid]]
        el = by_id.get(eid)
        if not el or eid not in wrappers:
            return []
        out = []
        for tp in el.get("template_parameters") or []:
            t = tp.get("type")
            tgt = by_display.get(t)
            if tgt is not None:
                out.extend(resolve(tgt["id"], depth + 1))
        return out

    # ── 2패스: 간선. extension 은 대상 노드의 is_abstract 를 봐야 갈리므로
    #    노드를 전량 적재한 뒤에 돌아야 한다(스트리밍 불가).
    edges = {}
    for r in relationships:
        t = r["type"]
        src_el = by_id.get(r["source"])
        dst_el = by_id.get(r["destination"])
        if t == "containment":
            stats["containment 버림(자리 없음)"] += 1
            continue
        if t == "extension":
            kind = "realization" if (dst_el or {}).get("is_abstract") else "inheritance"
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


def _assemble(nodes, edges, stats, *, language, source_tool, repo):
    """언어 공통 꼬리 — R1 제거, 모듈 의존 유도(C-15), 최종 dict 조립.

    두 언어 파서(normalize_cpp / normalize_csharp)가 여기로 수렴한다.

    modules[].depends_on 은 클래스 간선에서 유도한다 (2026-08-27 사용자 확정, C-15).
    CMake 타겟 층(.dot)과 조인하지 않는 이유 둘:
      1. 입도가 다르다 — 폴더 모듈 20개 vs CMake 타겟 70개. 1:1 이 아니다.
      2. C# 에는 CMake 대응물이 없다(.asmdef 는 사용자 코드를 0개로 나눈다).
         클래스 간선 유도는 두 언어가 같은 방식을 쓸 수 있는 유일한 축이다.
    ⚠ 이것은 링크 의존이 아니라 타입 의존이다. .dot 의 PUBLIC/INTERFACE/PRIVATE
    축과는 다른 것이므로 같은 것으로 읽지 말 것.
    """
    # R1 — 전이 확장 금지. 사용자 코드가 실제로 닿지 않는 외부 노드는 뺀다.
    touched = {e["to"] for e in edges.values()}
    dropped = [nid for nid, n in nodes.items() if n["kind"] == "external" and nid not in touched]
    for nid in dropped:
        stats["R1 로 제거된 외부 노드"] += 1
        del nodes[nid]

    modules = sorted({n["module"] for n in nodes.values() if n["module"] and n["kind"] != "external"})
    mod_dep = defaultdict(set)
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

# R5 — C# 투과 래퍼. generic_def(정의 이름) 기준. "[]" 는 배열(F4 가 제네릭과 같은 자리로 표현).
#   ⚠ 인터페이스(IReadOnlyDictionary 등)는 넣지 않는다 — 🔵 probe 실측에서 R7 후 잔존 9건에
#   IReadOnlyDictionary 가 남아 있었다. 즉 그때의 접기도 인터페이스를 투과하지 않았다.
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
CS_KIND = {"inherit": "inheritance", "realize": "realization",
           "assoc": "association", "depend": "dependency"}


def cs_module_of(path):
    """모듈 경계 = 폴더 트리 (2026-08-27 사용자 확정 — .asmdef 기각, 네임스페이스 기각)."""
    if not path:
        return None
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "Assets" and parts[1] == "@Scripts":
        return parts[2] if len(parts) > 3 else "@Scripts"
    if len(parts) >= 2 and parts[0] == "Assets" and parts[1] == "@Editors":
        return "@Editors"
    return parts[0]


def cs_asm2pkg(repo):
    """어셈블리 이름 -> 패키지 id. Library/PackageCache/<pkg>@<hash>/**/*.asmdef 의
    name 이 어셈블리, 경로의 @ 앞이 패키지다 (HANDOFF-unity-pattern-collection.md §2-2)."""
    import glob as _glob
    out = {}
    base = os.path.join(repo, "Library/PackageCache")
    for a in _glob.glob(os.path.join(base, "*", "**", "*.asmdef"), recursive=True):
        pkg = os.path.relpath(a, base).split("/")[0].split("@")[0]
        try:
            out[json.load(open(a, encoding="utf-8-sig"))["name"]] = pkg
        except Exception:
            pass
    # precompiled DLL(Newtonsoft.Json 등)은 .asmdef 가 없다 — 파일명으로 보충한다.
    # .asmdef 가 이미 준 이름은 덮어쓰지 않는다.
    for d in _glob.glob(os.path.join(base, "*", "**", "*.dll"), recursive=True):
        pkg = os.path.relpath(d, base).split("/")[0].split("@")[0]
        out.setdefault(os.path.splitext(os.path.basename(d))[0], pkg)
    return out


def cs_external_group(asm, asm2pkg):
    """C-9 R2 — 외부 하나 = 노드 하나. 입도는 패키지 이름. 명명 규칙은 §2-2 표."""
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


def normalize_csharp(dump, repo):
    # F5 게이트 — 참조 집합이 틀리면 dst 가 통째로 쓰레기가 된다(모드 A 1,055 / B 7,780 실측).
    comp = dump["compilation"]
    if comp["errors"] or comp["unresolved_types"]:
        print(f"거부(F5) — errors {comp['errors']} / unresolved_types {comp['unresolved_types']}. "
              f"참조 집합을 확인하라 (모드 C: csproj 목록만, 호스트 BCL 금지).", file=sys.stderr)
        sys.exit(2)

    ty = {t["id"]: t for t in dump["types"]}
    asm2pkg = cs_asm2pkg(repo)
    src_asm = dump["compilation"]["assembly"]
    stats = Counter()
    stats["asm->pkg 사전"] = len(asm2pkg)

    # ⚠ 1차 판정은 file 유무가 아니라 어셈블리다. 🔵 (float, float) 튜플이 netstandard 소속인데
    #   사용 지점의 소스 위치를 달고 온다 — clang-uml 에서 std:: 타입의 source_location 이
    #   첫 사용 지점을 가리키던 함정(관찰 보고서 F절)의 C# 판본이다. F6 이 경로와 어셈블리를
    #   둘 다 받아 교차 확인하라고 한 이유가 정확히 이것이다.
    def is_first(t):
        return t.get("assembly") == src_asm

    def resolve(tid, depth=0):
        """R5 — 투과 래퍼는 type_args 를 따라 내려간다. F4 덕에 제네릭 문법 파싱이 필요 없다.
        투과 체크가 1차 판정보다 먼저다 — 튜플처럼 소스 위치를 단 외부 컨테이너가 있다."""
        if depth > 4:
            return []
        t = ty[tid]
        if t.get("generic_def") in CS_TRANSPARENT_DEFS:
            stats["R5 투과 래퍼 경유"] += 1
            out = []
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
    #    ⚠ 소스 제네릭의 구성 인스턴스(UI_Base<UI_HomeButton> 등)는 file 이 있어도
    #    별도 노드로 만들지 않는다 — Roslyn 이 정의와 다른 심볼로 주지만 위치는 정의와
    #    같으므로 (file, line) 으로 정의 노드에 접는다. 안 접으면 같은 클래스가 중복된다.
    node_id, nodes = {}, {}
    by_loc = {}
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

    collapsed = defaultdict(list)

    def to_node(tid):
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
    edges = {}
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
                if r.get("origin"):
                    edges[key]["origin"] = r["origin"]         # C# 만 갖는 정보 — 비대칭 기록
                if r.get("attrs"):
                    edges[key]["attrs"] = r["attrs"]           # F7 — [SerializeField] 통과
                if nodes[d]["kind"] == "external":
                    edges[key]["constraint"] = False           # R6

    for nid, names in collapsed.items():
        nodes[nid]["collapsed_from"] = sorted(set(names))

    return _assemble(nodes, edges, stats,
                     language="csharp", source_tool=dump.get("tool", "roslyn-dump ?"), repo=repo)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--clang-uml", help="C++ — clang-uml -g json 산출물")
    src.add_argument("--roslyn-dump", help="C# — roslyn-dump.json (codegraph/roslyn-dump 가 만든 것)")
    ap.add_argument("--repo", default=".", help="대상 저장소 (repo_commit, asm->pkg 사전용)")
    ap.add_argument("-o", "--out", default="codegraph.json")
    a = ap.parse_args()

    if a.clang_uml:
        els, rels, meta = load_clang_uml(a.clang_uml)
        tool = "clang-uml " + str(meta.get("clang_uml_version", "?"))
        g, stats = normalize_cpp(els, rels, a.repo, tool)
    else:
        dump = json.load(open(a.roslyn_dump, encoding="utf-8"))
        g, stats = normalize_csharp(dump, a.repo)
    json.dump(g, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"{a.out} — 노드 {len(g['nodes'])} / 간선 {len(g['edges'])} / 모듈 {len(g['modules'])}")
    if a.clang_uml:
        print(f"입력: elements {len(els)} / relationships {len(rels)}")
    else:
        print(f"입력: types {len(dump['types'])} / relations {len(dump['relations'])}")
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
        # C# — 언어에 소유 표지가 없어 composition/aggregation 이 0이다. association 이 위치를 갖는다.
        assoc = [e for e in g["edges"] if e["kind"] == "association"]
        print(f"  소유 간선 0 (C# 정상 — 함정 5). association {sum(1 for e in assoc if e.get('line'))}/{len(assoc)} 에 위치")


if __name__ == "__main__":
    main()
