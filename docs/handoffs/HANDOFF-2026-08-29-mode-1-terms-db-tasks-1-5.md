# HANDOFF ⑤ — Mode 1 terms-db 우선 파이프라인 Task 1~5 (mode-1-codebase-wiki 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 06:20). 이 프롬프트를 다시 실행하지 말 것.**
> `mode-1-codebase-wiki` 가 Task 1~5 를 TDD 로 마쳤고 오케스트레이터가 직접 재검증(pytest 51/51 · StickRush·Graphics CLI 실패 0)한 뒤
> `1ad879a` 로 커밋했다. **DONE_WITH_CONCERNS** — 계획서에 없던 결함 1건(정적 도구 간선 어휘 `instantiation`·`friendship` 재판정)을
> 서브에이전트가 Graphics 저장소 실측으로 잡아 고쳤다. 정정 주석은 계획서 Task 3 머리에 있다. 이 문서는 **기록용**이다.
> 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.
> 정본 참조(읽지 않아도 됨): `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md` Task 1~5 — 아래 `[STEP]` 이 그 절의 사본이다.

```
[ROLE]
당신은 $REPO_ROOT (브랜치 feat/report-builder) 의 Mode 1 에이전트 mode-1-codebase-wiki 다.
목표: codegraph/terms_db.py 를 "terms-db 우선" 구조로 확장한다 — 레코드가 간선을 잃지 않고(Task 1), terms-db 에서
codegraph.json 을 투영하고(Task 2), LLM 이 쓴 인용을 3값으로 판정하고(Task 3), LLM 읽기를 합치되 구조는 codegraph 가
이기고(Task 4), CLI 가 codegraph 없이도 돈다(Task 5). 다섯 Task 를 순서대로, 한 세션에서 한다.
Task 6(문서) · 7(전수조사 실행)은 이번 지시에 없다 — 하지 않는다.

[HARD RULES]
- 커밋하지 않는다. git add 도 하지 않는다. 각 Task 의 "Step 5: 커밋" 은 건너뛴다 — 오케스트레이터가 사용자 승인 후 한다.
- TDD 순서를 지킨다: 실패 테스트 작성 → 실패 확인 → 최소 구현 → 통과 확인. 실패를 실제로 보지 않고 구현으로 넘어가지 않는다.
- 주석 · docstring 은 한국어. "검증됨" "입증" "증명" 이라는 낱말을 쓰지 않는다.
- Python 3.14 표준 라이브러리만. 새 의존성을 넣지 않는다.
- 테스트 명령: .venv/bin/python -m pytest codegraph/ -q  (시스템 python 이 아니라 .venv 다)
- 골든 테스트 2개(StickRush · Graphics)는 이 머신에 산출물이 있으므로 skip 이 아니라 pass 여야 한다. skip 이 뜨면 경로 문제이니 멈추고 보고한다.

[BOUNDARIES]
- 당신이 소유하는 파일 = 정확히 2개: codegraph/terms_db.py (수정), codegraph/test_terms_db.py (신규).
- codegraph/normalize.py 를 건드리지 않는다 — 출력 키를 읽기만 한다.
- codegraph/test_normalize.py 를 건드리지 않는다 — §8 의 기존 terms_db 테스트 3개가 그대로 통과해야 한다.
- codegraph/verify_citations.py 는 import 만 한다 (from verify_citations import short).
- scripts/ · src/ · test/ · docs/ · CLAUDE.md · .claude/ 를 건드리지 않는다.

[VERIFIED FACTS — 2026-08-29 실측. 이 보고를 믿지 말고 시작 전에 재확인하라]
- HEAD 는 74c4268 이어야 한다 (git log --oneline -1). 작업 트리는 docs/prompt/checklist.yaml 하나만 미추적이다.
- Python 테스트 기준선: 31 passed (.venv/bin/python -m pytest codegraph/ -q).
- codegraph.json 출력 키 — normalize.py:280-288: schema_version · language · platform · source_tool · repo_commit · nodes[] · edges[] · modules[].
  노드 id/name/kind/module/file/line (normalize.py:160-174), 간선 from/to/kind/label/file/line (normalize.py:237-240), 모듈 id/depends_on (normalize.py:287).
  간선 접기 키 (from, to, kind) — normalize.py:231. 모듈 의존은 서로 다른 모듈의 노드 간 간선에서 파생 — normalize.py:268-276.
- verify_citations.short() 는 verify_citations.py:41-45 — "##" "::" "." 로 쪼개 마지막 조각, "<" 앞까지.
- 골든 재료: $CSHARP_REPO/out/codegraph-raw/codegraph.json (노드 231) ·
  $GRAPHICS_REPO/out/codegraph-raw/codegraph.json (노드 191). 둘 다 존재.
- 아래 STEP 의 코드는 오케스트레이터가 스크래치패드에서 조립해 돌려 봤다: 신규 19개 통과 · 기존 §8 3개 통과 ·
  StickRush 실물 CLI 출력 "용어 241개 / 실패 0 / 근거 없음 0" · "투영에 없는 것 0개". 그래도 당신이 TDD 순서로 다시 확인한다.

========================================================================
[STEP — 계획서 Task 1~5 를 그대로 옮김. 각 Task 의 Step 1~4 를 순서대로. Step 5(커밋)는 건너뛴다]

## Task 1: `build_terms` 가 간선을 잃지 않게 한다 — `id` 와 방향 있는 `uses[]`

codegraph ⊂ terms-db 가 성립하려면 레코드가 간선의 방향·종류·위치를 갖고 있어야 한다.

**Files:**
- Modify: `codegraph/terms_db.py:31-97` (`build_terms`), 헬퍼 2개 추가
- Create: `codegraph/test_terms_db.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다 — `codegraph/test_terms_db.py` 신규**

```python
"""test_terms_db.py — terms-db 우선 파이프라인의 회귀 테스트.

세 가지를 고정한다.
  1. codegraph.json ⊂ terms-db.json  — build_terms 가 간선을 잃지 않고, project_codegraph 가 되돌린다
  2. 인용 3값 판정              — 실패(L1/L2) / 근거 없음(L3) / 통과. reading 레코드는 where 가 필수
  3. 구조는 codegraph 가 이긴다  — merge_terms 가 LLM 레코드의 id/kind/module/where 로 덮어쓰지 않는다
골든(§2)은 실제 저장소 산출물을 쓴다 — 합성 데이터만으로 검증하지 않는다.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terms_db as T  # noqa: E402

CS_REPO = os.path.expanduser("$CSHARP_REPO")
CPP_REPO = os.path.expanduser("$GRAPHICS_REPO")


def _graph():
    """합성 codegraph — 클래스 2, 외부 1, 간선 2, 모듈 1. normalize.py 출력 키 그대로."""
    return {
        "schema_version": 2, "language": "csharp", "repo_commit": "abc",
        "nodes": [
            {"id": "A.B.Renderer", "name": "Renderer", "kind": "class", "module": "render",
             "file": "src/render/renderer.cs", "line": 12},
            {"id": "A.B.Mesh", "name": "Mesh", "kind": "class", "module": "render",
             "file": "src/render/mesh.cs", "line": 3},
            {"id": "(BCL) netstandard", "name": "(BCL) netstandard", "kind": "external",
             "module": "__external__", "file": None, "line": None},
        ],
        "edges": [
            {"from": "A.B.Renderer", "to": "A.B.Mesh", "kind": "association",
             "label": "mMesh", "file": "src/render/renderer.cs", "line": 40},
            {"from": "A.B.Renderer", "to": "(BCL) netstandard", "kind": "dependency",
             "label": None, "file": None, "line": None, "constraint": False},
        ],
        "modules": [{"id": "render", "depends_on": []}],
    }


# ── 1. codegraph ⊂ terms-db — 간선을 잃지 않는다
def test_build_terms_keeps_id_and_typed_uses():
    db = T.build_terms(_graph(), facts={}, hotspot=[])
    assert db["Renderer"]["id"] == "A.B.Renderer"
    assert db["Renderer"]["uses"] == [
        {"to": "Mesh", "kind": "association", "label": "mMesh", "where": "src/render/renderer.cs:40"},
        {"to": "(BCL) netstandard", "kind": "dependency", "label": None, "where": ""},
    ]
    assert db["Mesh"]["uses"] == []
    assert db["Mesh"]["neighbors"] == ["Renderer"], "이웃은 uses 의 역방향에서도 나와야 한다"
    assert db["render"]["uses"] == [] and db["render"]["id"] == "render"
    assert db["render"]["neighbors"] == [], "모듈 이웃은 depends_on 이다 — 여기선 비어 있다"
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q`
Expected: FAIL — `KeyError: 'id'` (또는 `'uses'`)

- [ ] **Step 3: 구현 — `codegraph/terms_db.py` 의 `_where` 아래에 헬퍼 2개를 더하고 `build_terms` 를 통째로 바꾼다**

```python
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
```

- [ ] **Step 4: 통과를 확인한다 — 새 테스트와 기존 §8 셋 다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py codegraph/test_normalize.py -q -k "terms"`
Expected: `4 passed` (신규 1 + 기존 3). 기존 3개가 깨지면 `neighbors` 재계산 순서가 틀린 것이다.

- [ ] **Step 5: 커밋 — 오케스트레이터가 사용자 승인 후**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : terms-db 레코드가 간선의 방향, 종류, 위치를 uses 로 보존"
```

---

## Task 2: `project_codegraph` — terms-db 에서 codegraph.json 을 되돌린다

**Files:**
- Modify: `codegraph/terms_db.py` (함수 1개 + 상수 추가, `import sys`)
- Modify: `codegraph/test_terms_db.py` (append)

- [ ] **Step 1: 실패하는 테스트 — `test_terms_db.py` 끝에 append**

```python
# ── 2. 투영 — terms-db -> codegraph.json. codegraph 는 terms-db 의 부분집합이다
def _triples(g):
    return {(e["from"], e["to"], e["kind"]) for e in g["edges"]}


def test_project_round_trips_synthetic_graph():
    g = _graph()
    p = T.project_codegraph(T.build_terms(g, facts={}, hotspot=[]), language="csharp", repo_commit="abc")
    assert p["schema_version"] == 2 and p["language"] == "csharp" and p["source_tool"] == "terms-db"
    assert p["repo_commit"] == "abc"
    assert {n["id"] for n in p["nodes"]} == {n["id"] for n in g["nodes"]}
    assert _triples(p) == _triples(g)
    assert p["modules"] == [{"id": "render", "depends_on": []}]
    ext = next(e for e in p["edges"] if e["to"] == "(BCL) netstandard")
    assert ext.get("constraint") is False, "외부로 가는 간선은 R6 constraint=False 를 유지한다"
    mesh = next(n for n in p["nodes"] if n["id"] == "A.B.Mesh")
    assert (mesh["file"], mesh["line"], mesh["name"]) == ("src/render/mesh.cs", 3, "Mesh")


def test_project_drops_terms_that_are_not_code():
    db = T.build_terms(_graph(), facts={}, hotspot=[])
    db["codegraph.json"] = {"id": "codegraph.json", "kind": "artifact", "module": "codegraph",
                            "where": "codegraph/normalize.py:285", "means": "코드 지도 파일.",
                            "uses": [], "neighbors": [], "source": "reading"}
    db["Renderer"]["uses"].append({"to": "codegraph.json", "kind": "dependency", "label": "writes", "where": ""})
    p = T.project_codegraph(db)
    assert "codegraph.json" not in {n["id"] for n in p["nodes"]}
    assert all(e["to"] != "codegraph.json" for e in p["edges"]), "지도 밖 용어로 가는 간선은 지도에 싣지 않는다"


@pytest.mark.parametrize("repo,lang", [(CS_REPO, "csharp"), (CPP_REPO, "cpp")])
def test_project_golden_is_superset_of_real_codegraph(repo, lang):
    """실제 산출물로 확인한다 — codegraph 의 노드 · 간선 · 모듈이 투영에 전부 있다."""
    path = os.path.join(repo, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(path):
        pytest.skip(f"산출물 없음: {path}")
    g = json.load(open(path, encoding="utf-8"))
    p = T.project_codegraph(T.build_terms(g, facts={}, hotspot=[]), language=lang)
    assert {n["id"] for n in g["nodes"]} <= {n["id"] for n in p["nodes"]}
    assert _triples(g) <= _triples(p)
    assert {m["id"] for m in g["modules"]} == {m["id"] for m in p["modules"]}
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q`
Expected: 3~5개 FAIL — `AttributeError: module 'terms_db' has no attribute 'project_codegraph'`

- [ ] **Step 3: 구현 — `terms_db.py` 상단 상수 + 함수. `import sys` 를 `import os` 아래에 더한다**

```python
# 지도의 노드가 되지 않는 용어 종류. 사람이 부르는 이름(파일·산출물·JSON 키·개념)은 terms-db 에만 산다.
NON_NODE_KINDS = frozenset({"file", "module", "artifact", "key", "concept"})
# reading 레코드가 쓸 수 있는 kind 전부. codegraph 에서 온 kind 는 검사하지 않는다(정적 도구의 어휘).
KINDS = frozenset({"class", "struct", "enum", "interface", "delegate", "record", "external",
                   "function"}) | NON_NODE_KINDS
# 간선 종류 — normalize.py 의 어휘 그대로. 새 종류를 만들지 않는다.
EDGE_KINDS = frozenset({"inheritance", "realization", "composition", "aggregation",
                        "association", "dependency"})
SOURCES = frozenset({"codegraph", "reading", "codegraph+reading"})


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
```

- [ ] **Step 4: 통과를 확인한다 — 골든 2개 포함**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q`
Expected: `5 passed` (골든 2개는 이 머신에 산출물이 있으므로 **skip 이 아니라 pass** 여야 한다. skip 이 뜨면 경로가 틀린 것)

- [ ] **Step 5: 커밋 — 오케스트레이터가 사용자 승인 후**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : terms-db 에서 codegraph.json 을 투영하는 project_codegraph"
```

---

## Task 3: `check_terms` — LLM 이 쓴 인용을 3값으로 판정한다

**Files:**
- Modify: `codegraph/terms_db.py` (함수 2개 추가, `from verify_citations import short`)
- Modify: `codegraph/test_terms_db.py` (append)

- [ ] **Step 1: 실패하는 테스트 — append**

```python
# ── 3. 인용 3값 판정 — 실패(L1/L2) / 근거 없음(L3) / 통과
def _repo(tmp_path):
    """가짜 저장소 — codegraph/x.py 8줄."""
    src = tmp_path / "codegraph"
    src.mkdir()
    (src / "x.py").write_text(
        '"""x.py"""\n'
        '\n'
        'def build_terms(graph):\n'
        '    return _where(graph)\n'
        '\n'
        '\n'
        'def _where(node):\n'
        '    return ""\n', encoding="utf-8")
    return str(tmp_path)


def _reading():
    return {
        "build_terms": {"kind": "function", "module": "codegraph", "where": "codegraph/x.py:3",
                        "means": "용어 사전을 만든다.", "does": "노드를 돈다.",
                        "uses": [{"to": "_where", "kind": "dependency", "label": "calls",
                                  "where": "codegraph/x.py:4"}],
                        "source": "reading"},
        "_where": {"kind": "function", "module": "codegraph", "where": "codegraph/x.py:7",
                   "means": "위치 문자열을 만든다.", "uses": [], "source": "reading"},
    }


def test_check_passes_on_grounded_reading(tmp_path):
    db = T.merge_terms({}, _reading())
    assert T.check_terms(db, _repo(tmp_path)) == []


def test_check_l1_missing_file_is_failure(tmp_path):
    r = _reading(); r["_where"]["where"] = "codegraph/nope.py:1"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and term == "_where" and "L1" in why for lvl, term, why in out)


def test_check_l2_line_past_eof_is_failure(tmp_path):
    r = _reading(); r["_where"]["where"] = "codegraph/x.py:99"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and "L2" in why for lvl, term, why in out)


def test_check_l3_name_absent_is_unfounded_not_failure(tmp_path):
    r = _reading(); r["_where"]["where"] = "codegraph/x.py:1"   # 파일·줄은 있으나 근처에 _where 가 없다
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "근거 없음" and term == "_where" for lvl, term, why in out)
    assert not any(lvl == "실패" for lvl, term, why in out)


def test_check_reading_record_requires_where(tmp_path):
    r = _reading(); r["_where"]["where"] = ""
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and term == "_where" and "where" in why for lvl, term, why in out)


def test_check_flags_unknown_uses_target(tmp_path):
    r = _reading(); r["build_terms"]["uses"][0]["to"] = "ghost"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and "ghost" in why for lvl, term, why in out)


def test_check_skips_citations_of_codegraph_records(tmp_path):
    """정적 도구가 낸 레코드의 위치는 여기서 재판정하지 않는다 — verify_citations.py 의 영역."""
    db = T.build_terms(_graph(), facts={}, hotspot=[])      # src/render/*.cs 는 가짜 저장소에 없다
    assert T.check_terms(db, _repo(tmp_path)) == []
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q -k check`
Expected: 7개 FAIL — `AttributeError: ... 'merge_terms'` (Task 4 의 함수를 먼저 부른다. Step 3 에서 **둘 다** 최소 구현한다 — merge 는 Task 4 에서 완성)

- [ ] **Step 3: 구현 — `terms_db.py`. import 에 `from verify_citations import short` 추가 (같은 디렉토리, 표준 라이브러리만 씀)**

```python
def _stem(key, kind):
    """L3 대조용 이름 조각. `calls[]` -> `calls`, `Outer::Inner` -> `Inner`, `terms_db.main` -> `main`.
    파일 · 산출물 · 키 · 개념 · 모듈은 글자 그대로 (`codegraph.json` 을 `.` 로 쪼개면 안 된다)."""
    k = key[:-2] if key.endswith("[]") else key
    if kind in NON_NODE_KINDS:
        return k
    return short(k)


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
            if src == "reading" or u.get("source") == "reading":
                t = u.get("to")
                stem = _stem(t, db[t].get("kind")) if t in db else ""
                cite(key, u.get("where", ""), stem, f"uses->{t}")
    return out


def merge_terms(base, reading):
    """(Task 4 에서 완성) reading 을 base 에 합친다. 여기서는 최소 — 새 레코드만 넣는다."""
    db = {k: dict(v, uses=[dict(u) for u in v.get("uses", [])]) for k, v in base.items()}
    for key, r in reading.items():
        if key not in db:
            rec = dict(r)
            rec.setdefault("uses", [])
            rec.setdefault("neighbors", [])
            rec["source"] = "reading"
            db[key] = rec
    _recompute_neighbors(db)
    return dict(sorted(db.items()))
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q`
Expected: `12 passed`

- [ ] **Step 5: 커밋 — 오케스트레이터가 사용자 승인 후**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : LLM 이 쓴 용어 인용을 L1, L2, L3 3값으로 판정하는 check_terms"
```

---

## Task 4: `merge_terms` — LLM 읽기를 합치되 구조는 codegraph 가 이긴다 (D3)

**Files:**
- Modify: `codegraph/terms_db.py` (`merge_terms` 완성)
- Modify: `codegraph/test_terms_db.py` (append)

- [ ] **Step 1: 실패하는 테스트 — append**

```python
# ── 4. 합치기 — 구조 필드는 codegraph 가 이긴다 (D3)
def test_merge_reading_overrides_means_but_not_structure():
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    reading = {"Renderer": {"kind": "function", "module": "elsewhere", "where": "x.cs:1",
                            "means": "장면을 그리는 클래스.", "does": "매 프레임 Mesh 를 그린다.",
                            "uses": [{"to": "Mesh", "kind": "dependency", "label": "calls Draw",
                                      "where": "src/render/renderer.cs:50"}],
                            "source": "reading"}}
    db = T.merge_terms(base, reading)
    r = db["Renderer"]
    assert r["means"] == "장면을 그리는 클래스." and r["does"] == "매 프레임 Mesh 를 그린다."
    assert (r["id"], r["kind"], r["module"], r["where"]) == \
        ("A.B.Renderer", "class", "render", "src/render/renderer.cs:12"), "구조는 codegraph 가 이긴다"
    assert r["source"] == "codegraph+reading"
    kinds = {(u["to"], u["kind"]) for u in r["uses"]}
    assert ("Mesh", "association") in kinds and ("Mesh", "dependency") in kinds, "새 종류의 간선은 더해진다"
    added = next(u for u in r["uses"] if u["kind"] == "dependency" and u["to"] == "Mesh")
    assert added.get("source") == "reading", "reading 이 보탠 간선은 표시가 남아야 check 가 인용을 본다"
    assert base["Renderer"]["source"] == "codegraph", "입력을 제자리에서 바꾸지 않는다"


def test_merge_adds_new_reading_records_and_links_neighbors():
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    reading = {"codegraph.json": {"kind": "artifact", "module": "codegraph",
                                  "where": "codegraph/normalize.py:285", "means": "코드 지도 파일.",
                                  "uses": [{"to": "Renderer", "kind": "dependency", "label": "lists", "where": ""}],
                                  "source": "reading"}}
    db = T.merge_terms(base, reading)
    assert db["codegraph.json"]["source"] == "reading"
    assert "codegraph.json" in db["Renderer"]["neighbors"], "reading 레코드의 uses 도 이웃에 반영된다"
    assert db["codegraph.json"]["neighbors"] == ["Renderer"]


def test_merge_is_deterministic():
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    a = json.dumps(T.merge_terms(base, _reading()), ensure_ascii=False, sort_keys=True)
    b = json.dumps(T.merge_terms(base, _reading()), ensure_ascii=False, sort_keys=True)
    assert a == b
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q -k merge`
Expected: 첫 테스트 FAIL — `assert r["means"] == ...` (기존 레코드는 아직 안 덮는다)

- [ ] **Step 3: 구현 — `merge_terms` 를 이것으로 교체**

```python
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
```

- [ ] **Step 4: 통과를 확인한다 — 전체**

Run: `.venv/bin/python -m pytest codegraph/ -q`
Expected: `46 passed` (기존 31 + 신규 15). 골든 2개는 pass.

- [ ] **Step 5: 커밋 — 오케스트레이터가 사용자 승인 후**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : LLM 읽기를 합치되 구조 필드는 codegraph 가 이기는 merge_terms"
```

---

## Task 5: CLI — codegraph 없이도 돌고, 있으면 부분집합을 대조한다

**Files:**
- Modify: `codegraph/terms_db.py` (docstring · `main`, `import subprocess`)
- Modify: `codegraph/test_terms_db.py` (append)

- [ ] **Step 1: 실패하는 테스트 — append**

```python
# ── 5. CLI — reading 만으로 terms-db.json + codegraph.json(투영) 을 낸다. 기존 호출 꼴은 그대로
HERE = os.path.dirname(os.path.abspath(__file__))


def _run(args):
    return subprocess.run([sys.executable, os.path.join(HERE, "terms_db.py"), *args],
                          capture_output=True, text=True)


def test_cli_reading_only_writes_db_and_projection(tmp_path):
    repo = _repo(tmp_path)
    reading = tmp_path / "terms-reading.json"
    reading.write_text(json.dumps(_reading(), ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    r = _run(["--repo", repo, "--reading", str(reading), "-o", str(out)])
    assert r.returncode == 0, r.stdout + r.stderr
    db = json.load(open(out / "terms-db.json", encoding="utf-8"))
    cg = json.load(open(out / "codegraph.json", encoding="utf-8"))
    assert set(db) == {"build_terms", "_where"}
    assert {n["id"] for n in cg["nodes"]} == {"build_terms", "_where"} and cg["source_tool"] == "terms-db"
    assert "실패 0" in r.stdout


def test_cli_exits_1_when_a_citation_fails(tmp_path):
    repo = _repo(tmp_path)
    bad = _reading(); bad["_where"]["where"] = "codegraph/nope.py:1"
    reading = tmp_path / "terms-reading.json"
    reading.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    r = _run(["--repo", repo, "--reading", str(reading), "-o", str(tmp_path / "out")])
    assert r.returncode == 1
    assert "L1" in r.stdout


def test_cli_still_accepts_codegraph_positional(tmp_path):
    """기존 호출 꼴 `terms_db.py <codegraph.json> --repo` 가 그대로 돈다 (StickRush · Graphics 용)."""
    g = tmp_path / "codegraph.json"
    g.write_text(json.dumps(_graph()), encoding="utf-8")
    r = _run([str(g), "--repo", str(tmp_path), "-o", str(tmp_path / "out")])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "투영 대조" in r.stdout and "없는 것 0개" in r.stdout
    assert not (tmp_path / "out" / "codegraph.json").exists(), "codegraph 가 입력이면 투영을 파일로 쓰지 않는다"


def test_cli_needs_at_least_one_input(tmp_path):
    r = _run(["--repo", str(tmp_path)])
    assert r.returncode == 2 and "--reading" in r.stderr
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -q -k cli`
Expected: 4개 중 3개 FAIL (`--reading` 인자를 모른다 / positional 필수라 exit 2)

- [ ] **Step 3: 구현 — 모듈 docstring 의 사용법 줄과 `main` 을 교체. `import subprocess` 추가**

docstring 의 마지막 두 줄을 이렇게 바꾼다:

```python
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
```

`main` 은 이것으로 교체:

```python
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
```

- [ ] **Step 4: 통과를 확인한다 — 전체 + 기존 호출 꼴을 StickRush 실물에**

Run: `.venv/bin/python -m pytest codegraph/ -q`
Expected: `50 passed`

Run: `.venv/bin/python codegraph/terms_db.py $CSHARP_REPO/out/codegraph-raw/codegraph.json --repo $CSHARP_REPO -o /tmp/rb-t5`
Expected: 마지막 두 줄이 `... 용어 241개 / 실패 0 / 근거 없음 0` 과 `투영 대조 — codegraph 노드 231개 중 투영에 없는 것 0개`. 종료 코드 0.

- [ ] **Step 5: 커밋 — 오케스트레이터가 사용자 승인 후**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : terms_db CLI 가 codegraph 없이 --reading 만으로 DB 와 투영을 낸다"
```

---

========================================================================
[SELF-REVIEW — 보고 전에 확인]
- [ ] 다섯 Task 모두 실패 테스트를 먼저 썼고 실패를 실제로 봤는가
- [ ] .venv/bin/python -m pytest codegraph/ -q 가 50 passed 인가 (기존 31 + 신규 19). skip 0
- [ ] StickRush 실물에 기존 호출 꼴을 돌려 "용어 241개 / 실패 0 / 근거 없음 0" 과 "투영에 없는 것 0개" 가 나오는가
- [ ] git status --porcelain 에 codegraph/terms_db.py · codegraph/test_terms_db.py 외에 당신이 만든 변경이 없는가
- [ ] "검증됨" "입증" "증명" 이 두 파일에 없는가 (grep)
- [ ] 커밋하지 않았는가

[REPORT — 이 형식으로, 한국어]
상태: DONE | DONE_WITH_CONCERNS | BLOCKED
변경 파일: (경로 나열)
검증 출력: (pytest 마지막 3줄 · StickRush CLI 마지막 2줄 · git status --porcelain 전체)
계획서와 달리 한 것: (있으면 무엇을 왜. 없으면 "없음")
미룬 것 / 우려: (없으면 "없음")
커밋: 하지 않았다 (확인)
```
