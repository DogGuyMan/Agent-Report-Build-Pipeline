# Mode 1 terms-db 우선 파이프라인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LLM 이 코드베이스를 **한 번** 전수조사해 `terms-db.json` 을 만들고, `codegraph.json` 은 그것의 **투영(look-up)** 으로 파생되게 한다. 첫 대상은 report-builder 자신이다.

**Architecture:** `terms-db.json` 이 원본 레코드다 — 용어마다 뜻(`means`) · 동작(`does`) · 위치(`where`) · 방향 있는 관계(`uses[]`) 를 갖는다. 정적 수집기(roslyn/clang-uml)가 있는 코드베이스는 `codegraph.json` 에서 레코드를 **먼저** 만들고 LLM 이 뜻만 보태며(구조 필드는 codegraph 가 이긴다), 수집기가 없는 코드베이스(Python/JS 인 이 저장소)는 LLM 의 읽기 레코드만으로 DB 를 만들고 `codegraph.json` 을 거기서 투영한다. LLM 이 쓴 모든 인용(`where`)은 `verify_citations.py` 와 같은 3값(실패 / 근거 없음 / 통과)으로 기계 검사한다.

**Tech Stack:** Python 3.14 표준 라이브러리만 (`codegraph/terms_db.py` 확장) · pytest · 기존 `verify_citations.short` 재사용. LLM 단계는 코드가 아니라 `mode-1-codebase-wiki` 에이전트의 절차다.

---

## 착수 전 실측 근거 (2026-08-29, HEAD `a49e285`)

| 사실 | 근거 |
|---|---|
| `terms_db.py` 의 `means` 는 정형문이다 — `"{module} 모듈의 {kind}. A, B 와(과) 이어져 있다."` | 🔵 `codegraph/terms_db.py:56-58` |
| 간선의 방향·종류·위치를 **버린다** — `neighbors` 는 이름 집합뿐 | 🔵 `terms_db.py:41-47` (`from`/`to` 양방향을 집합에 넣음) |
| 그래서 지금의 terms-db 로는 codegraph 를 되돌릴 수 없다 — 부분집합 관계가 성립하지 않는다 | 위 두 줄의 귀결 |
| `codegraph.json` 출력 키 — `schema_version` `language` `platform` `source_tool` `repo_commit` `nodes[]` `edges[]` `modules[]` | 🔵 `normalize.py:280-288` |
| 노드 키 `id name kind module file line` · 간선 키 `from to kind label file line` (+ `occurrences` `constraint`) · 모듈 키 `id depends_on` | 🔵 `normalize.py:160-174, 237-240, 287` |
| 간선 접기 키는 `(from, to, kind)` | 🔵 `normalize.py:231` |
| 모듈 의존은 서로 다른 모듈의 노드 간 간선에서 파생한다. 외부 노드는 제외 | 🔵 `normalize.py:268-276` |
| 인용 3값 판정 — L1 파일 · L2 줄 · L3 그 위치에 그 심볼. **근거 없음은 실패가 아니다** | 🔵 `verify_citations.py:8-19` |
| 이름 대조는 **인접 줄까지** 본다 (앞 1줄 + 이 줄 + 뒤 1줄) | 🔵 `verify_citations.py:116-118` |
| 마지막 조각 대조 규칙 `short()` — `##` `::` `.` 로 쪼개 마지막만, `<` 앞까지 | 🔵 `verify_citations.py:41-45` |
| 이 저장소에는 `codegraph.json` 이 **없다** — Python/JS 라 roslyn/clang-uml 입력이 없다 | 🔵 `ls out/` 부재, RESUME §6 R1 |
| 외부 저장소 둘(StickRush C# · Graphics C++)에는 `codegraph.json` 이 있다 — 골든 테스트 재료 | 🔵 `find $DEV_ROOT -name codegraph.json` 2건 |
| `terms_db.py` 를 StickRush 에 돌리면 241개 (노드 231 + 모듈 10). 이름 충돌 0 | 🔵 실측 `--- 용어 241개` |
| Plan `llm-load-reduction` 의 용어 24개 중 이 저장소 **코드에 글자로 나타나는 것 13개** | 🔵 `grep -rlF` 전수 (`codegraph.json` 8파일, `PageRank` 3, `calls[]` 3, `WarmUp` 2 …) |
| Python 쪽 docstring 밀도 — `normalize.py` 19함수 중 17 · `facts.py` 5 중 4 | 🔵 `grep -c` |
| 전수조사 대상 파일 35개 · `def`/`class`/`export` 104개 (테스트·probe 제외) | 🔵 `find` + `grep -c` |
| `pickTerms` 는 낱말 경계 정규식으로 DB 키를 Plan 본문에서 찾는다 | 🔵 `scripts/term/collect.mjs:17-27` |
| Python 테스트 기준선 31개 통과 | 🔵 `.venv/bin/python -m pytest codegraph/ -q` |

---

## 결정 목록 (Mode 2 보고서의 행이 된다)

| # | 결정 | 상태 | 신뢰도 | 출처 |
|---|---|---|---|---|
| D1 | `terms-db.json` 이 원본, `codegraph.json` 은 그 투영. LLM 전수조사는 **1회** | `[제안됨]` — 사용자 확정 2026-08-29 | 🔵 실측 (부분집합 불성립 지점 `terms_db.py:41-47`) | 사용자 |
| D2 | LLM 이 쓴 레코드(`source: "reading"`)는 `where` 가 **필수**이고 L1/L2/L3 3값으로 기계 검사한다. 인용 없는 뜻은 싣지 않는다 | `[제안됨]` — 사용자 확정 | 🔵 `verify_citations.py` 규칙 재사용 | 사용자 |
| D3 | 정적 수집기가 있으면 **구조 필드(`id kind module where`)는 codegraph 가 이긴다.** LLM 은 `means` `does` 와 새 `uses` 만 보탠다 | `[제안됨]` — 사용자 확정 2026-08-29 (1안) | 🟡 75 — 결정론을 지키는 유일한 방법이라 봄. 반례 미관측 | 오케스트레이터 |
| D4 | 이 저장소의 읽기 원본은 **`docs/codegraph/terms-reading.json`(추적)**, 파생물 `terms-db.json` · `codegraph.json` 은 `out/codegraph-raw/`(무시, 원본에서 재생성) | `[제안됨]` — 사용자 확정 2026-08-29 (1안) | 🟡 70 — `out/` 이 gitignore 라 LLM 산출물을 거기 두면 사라진다. 위치 이름은 취향 | 오케스트레이터 |
| D5 | 키 규칙 — 소스 파일은 `kind: "file"` 로 파일명 키(`normalize.py`), 함수·클래스는 맨 이름, **충돌 시 전원 `<파일줄기>.<이름>`**(`terms_db.main`), `module` 은 디렉토리 | `[제안됨]` — 사용자 확정 2026-08-29 (1안) | 🟡 70 — Plan 이 파일명으로 부른다는 관찰에 근거. `main` 5건 충돌 실측 | 오케스트레이터 |
| D6 | 전수조사 주체는 `mode-1-codebase-wiki` 에이전트. 오케스트레이터는 검토·커밋만 | `[제안됨]` — 사용자 확정 | 🔵 | 사용자 |
| D7 | C#/C++ 저장소(StickRush)에 읽기 단계를 적용해 **C1(오답 보기 품질)** 을 시험하는 것은 이 계획 **밖** | `[제안됨]` — 기록만 | 💭 | 오케스트레이터 |

**D3 에 대한 우려 한 줄.** 사용자의 그림은 "LLM 이 한 번 훑어 구조까지 얻는다" 이다. 정적 수집기가 있는 저장소에서 LLM 추정이 정적 사실과 **어긋날 때** 어느 쪽을 믿을지가 D3 이다. 정적 쪽을 택했다 — 그래야 `verify_citations.py` 의 L3 가 계속 성립한다. 이 선택이 틀렸다고 보면 D3 만 뒤집으면 되고 나머지는 그대로다.

🔵 2026-08-29 05:50 — 검토 보고서의 옵션표를 놓고 사용자가 D3 · D4 · D5 를 **전부 1안**으로 확정했다.

---

## File Structure

| 파일 | 역할 | 변경 |
|---|---|---|
| `codegraph/terms_db.py` | 레코드 생성(`build_terms`) · 합치기(`merge_terms`) · 인용 검사(`check_terms`) · 투영(`project_codegraph`) · CLI | **수정** — 함수 4개 추가, CLI 인자 확장. 기존 호출 꼴 유지 |
| `codegraph/test_terms_db.py` | 위 네 함수와 CLI 의 회귀 테스트. 골든은 실제 저장소 산출물 | **신규** |
| `codegraph/test_normalize.py` §8 | 기존 terms_db 테스트 3개 | 건드리지 않는다 — 그대로 통과해야 한다 |
| `.claude/agents/mode-1-codebase-wiki.md` | 전수조사 절차 절 + "means 를 풍부하게 쓰지 않는다" 규율 개정 | **수정** (Mode 1 에이전트 소유) |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` Mode 1 절 | 위와 **같이** 고친다 (역할 서술 원본) | **수정** |
| `docs/codegraph/terms-reading.json` | 이 저장소의 LLM 전수조사 원본 | **신규** (Task 7, LLM 산출물) |
| `out/codegraph-raw/terms-db.json` · `codegraph.json` | 파생물 — gitignore. CLI 한 줄로 재생성 | 생성 |

**건드리지 않는 파일** — `codegraph/normalize.py`(출력 키 불변) · `codegraph/verify_citations.py`(import 만) · `scripts/term/*` · `src/*` · `CLAUDE.md`(오케스트레이터가 커밋 시 한 줄 보탠다).

**레코드 꼴 (schema 는 파일로 두지 않는다 — 여기와 docstring 이 정본)**

```json
{
  "build_terms": {
    "id": "build_terms",
    "kind": "function",
    "module": "codegraph",
    "where": "codegraph/terms_db.py:31",
    "means": "codegraph.json 에서 용어 사전을 만드는 함수.",
    "does": "노드와 모듈을 돌며 이름 · 종류 · 위치 · 관계를 뽑는다. 입력이 같으면 출력도 같다.",
    "uses": [
      { "to": "_where", "kind": "dependency", "label": "calls", "where": "codegraph/terms_db.py:62" }
    ],
    "neighbors": ["_where"],
    "source": "reading"
  }
}
```

| 필드 | 값 | 누가 채우나 |
|---|---|---|
| `id` | 투영 시 노드 id. 없으면 키 | codegraph 면 노드 id, reading 이면 키 |
| `kind` | `class struct enum interface delegate record external function` (지도의 노드가 됨) · `file module artifact key concept` (노드가 되지 **않음**) | |
| `module` | codegraph 면 노드의 `module`, reading 이면 **디렉토리** (`codegraph`, `scripts/term`) | |
| `where` | `file:line`. reading 은 `module`·`external` 빼고 **필수** | |
| `means` / `does` | 무엇인가 / 무엇을 하는가. `does` 는 선택 | reading 만 |
| `uses[]` | `{to: 용어 키, kind: 간선 종류, label, where}`. `kind` ∈ `inheritance realization composition aggregation association dependency` | 양쪽 |
| `neighbors` | `uses` 양방향에서 **재계산**. 손으로 쓰지 않는다 | 기계 |
| `source` | `codegraph` · `reading` · `codegraph+reading`(합쳐진 것) | 기계 |

---

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

## Task 6: 전수조사 절차 — 에이전트 정의와 역할 문서를 같이 고친다

코드가 아니라 **LLM 이 따를 절차**다. 두 문서를 같이 고친다 — "한쪽만 고치면 조용히 어긋난다"(HANDOFF ③ 머리말).

**Files:**
- Modify: `.claude/agents/mode-1-codebase-wiki.md` — `## 나는 무엇이 아닌가` 의 셋째 항목 교체, `## 소유 파일과 경계` 표에 두 행 추가, `## 전수조사 절차` 절 신설 (`## 전제` 앞에)
- Modify: `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` — `## Mode 1 에이전트` 절의 `### 이 mode 에 새로 붙는 것` 과 `### 나는 무엇이 아닌가` 셋째 항목을 같은 내용으로

- [ ] **Step 1: `.claude/agents/mode-1-codebase-wiki.md` 의 셋째 규율을 교체**

찾을 것:
```
- **`means` 를 풍부하게 쓰려고 하지 않는다.** 결정론이 목적이다 — 같은 입력이면 같은 출력.
  LLM 을 여기 끼우면 그게 깨진다
```
바꿀 것:
```
- **`means` 를 인용 없이 쓰지 않는다.** 뜻과 동작은 내가(LLM) 전수조사로 쓴다 — 단 **한 번**, 레코드마다
  `where`(file:line) 를 붙여서. `terms_db.py` 가 그 인용을 L1/L2/L3 로 기계 검사하고, 정적 수집기가 있는
  저장소에서는 구조 필드(`id kind module where`)를 codegraph 쪽으로 덮는다. 결정론은 codegraph 와 투영이
  지키고, 나는 인용으로 붙들린다
```

- [ ] **Step 2: 같은 파일 `## 소유 파일과 경계` 표에 두 행 추가 (`codegraph/terms_db.py` 행 아래)**

```
| `docs/codegraph/terms-reading.json` (이 저장소 자신을 조사할 때) | **소유** — 내 전수조사 원본 |
| `out/codegraph-raw/terms-db.json` · `codegraph.json` | 생성만. gitignore 다 — 원본에서 CLI 한 줄로 재생성 |
```

- [ ] **Step 3: 같은 파일에 `## 전수조사 절차` 절을 `## 전제` 바로 앞에 신설**

````markdown
## 전수조사 절차 — terms-reading.json 을 쓰는 법 (2026-08-29 신설)

LLM 추론은 **한 번**이다. 그 한 번에 뜻 · 동작 · 관계를 다 얻고, `codegraph.json` 은 거기서 투영한다.

1. **대상 파일을 고정한다.** 테스트 · probe · 캐시는 뺀다. 이 명령의 출력이 조사 범위다:
   ```bash
   find codegraph scripts src bin -type f \( -name "*.py" -o -name "*.mjs" -o -name "*.ts" -o -name "*.tsx" -o -path "bin/*" \) \
     -not -name "test_*" -not -name "probe_*" -not -path "*/__pycache__/*" | sort
   ```
2. **파일마다 레코드를 쓴다.** 순서는 위 목록 순서, 파일 안은 줄 번호 순서. 종류별 규칙:
   | 무엇 | `kind` | 키 | `where` |
   |---|---|---|---|
   | 소스 파일 | `file` | 파일명 (`normalize.py`, `collect.mjs`) | `경로:1` |
   | 함수 · 클래스 · 컴포넌트 | `function` / `class` | 맨 이름. **다른 파일과 충돌하면 충돌한 전원** `<파일줄기>.<이름>` (`terms_db.main`, `facts.main`) | 선언 줄 |
   | 산출 파일 (`codegraph.json` `terms-db.json` `report.html`) | `artifact` | 파일명 | 그 파일을 **쓰는** 줄 (`json.dump` · `writeFileSync`) |
   | 출력 JSON 의 키 (`nodes[]` `edges[]` `calls[]`) | `key` | `이름[]` (배열) 또는 `이름` | 그 키를 **채우는** 줄 |
   | 코드가 구현하는 개념 (`PageRank` `hotspot` `WarmUp`) | `concept` | 코드에 적힌 그대로 | 그 낱말이 있는 줄 |
   | 디렉토리 | `module` | 디렉토리 경로 (`codegraph`, `scripts/term`) | 비움 |
   `module` 필드는 항상 **디렉토리**다. `means` 는 한 문장, `does` 는 무엇을 하는지 한두 문장 — 둘 다 객체지향을 갓 배운 1학년 눈높이.
   `uses[]` 는 이 레코드가 **부르거나 · import 하거나 · 쓰는** 대상. `kind` 는 `dependency`(호출·import·쓰기) / `inheritance`(상속) / `aggregation`(멤버로 보유) 중 하나, `label` 에 `calls` `imports` `writes` 등 이유, `where` 는 그 자리.
   **`neighbors` 는 쓰지 않는다** — 기계가 다시 센다.
3. **코드에 없는 것은 쓰지 않는다.** Plan 이 만든 결정 코드(`C-20`, `U3`)나 개념(`무효화`)이 코드에 글자로 없으면
   그것은 Mode 1 의 것이 아니다 — Mode 1.5 의 `newConcepts` 로 남긴다. 인용 없는 뜻은 싣지 않는다.
4. **검사한다.** 실패 0 이 될 때까지 `where` 를 고친다. 근거 없음은 남겨도 되지만 이유를 보고한다.
   ```bash
   .venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json
   # -> out/codegraph-raw/terms-db.json + codegraph.json.  마지막 줄 "실패 0" 이어야 한다
   ```
5. **보고한다.** 레코드 수(종류별) · 실패 0 확인 출력 · 근거 없음 목록과 이유 · 키 충돌로 `<파일줄기>.<이름>` 이 된 것 목록.
````

- [ ] **Step 4: `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` 를 같이 고친다**

`### 이 mode 에 새로 붙는 것` 절을 이렇게 교체:
```markdown
### 이 mode 에 새로 붙는 것
**`terms_db.py` 와 전수조사 절차.** 2026-08-29 부터 `terms-db.json` 이 **원본**이고 `codegraph.json` 은 그 **투영**이다
(계획서 `2026-08-29-mode-1-terms-db-first.md`). 정적 수집기가 있으면 codegraph 에서 레코드를 먼저 만들고 LLM 이
뜻 · 동작 · 새 관계를 보탠다(구조 필드는 codegraph 가 이긴다). 없으면(Python/JS) LLM 읽기 레코드만으로 DB 를 만들고
`codegraph.json` 을 투영한다. **LLM 이 쓴 모든 `where` 는 L1/L2/L3 로 기계 검사한다.** 절차는 에이전트 정의
`.claude/agents/mode-1-codebase-wiki.md` 의 `## 전수조사 절차` 절에 있다.
```
`### 나는 무엇이 아닌가` 의 셋째 항목을 Step 1 과 **같은 문장**으로 교체.
`## 변경 이력` 에 한 줄 추가: `- 2026-08-29 — Mode 1 절: terms-db 우선 구조 반영. "means 를 풍부하게 쓰지 않는다" 를 "인용 없이 쓰지 않는다" 로 개정.`

- [ ] **Step 5: 두 문서가 같은 말을 하는지 확인**

Run: `grep -c "인용 없이 쓰지 않는다" .claude/agents/mode-1-codebase-wiki.md docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md`
Expected: 두 파일 다 `1` 이상

- [ ] **Step 6: 커밋 — 오케스트레이터가 사용자 승인 후. `.claude/agents/` 는 아직 미추적이라 이 커밋이 첫 추적이다 (RESUME R2 와 합친다)**

```bash
git add .claude/agents/mode-1-codebase-wiki.md docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md
git commit -m "[docs] : Mode 1 전수조사 절차와 terms-db 우선 규율을 에이전트 정의와 역할 문서에"
```

---

## Task 7: 전수조사 실행 — report-builder 자신 (LLM 단계, `mode-1-codebase-wiki` 가 한다)

이 Task 의 산출물은 코드가 아니라 **데이터**다. 결정론이 없으므로 TDD 대신 **인수 조건**으로 붙든다.

**Files:**
- Create: `docs/codegraph/terms-reading.json`
- Generate (gitignore): `out/codegraph-raw/terms-db.json` · `out/codegraph-raw/codegraph.json`

- [ ] **Step 1: 대상 파일 35개를 Task 6 §1 의 `find` 로 고정하고, 목록을 보고에 그대로 붙인다**

- [ ] **Step 2: Task 6 §2 규칙대로 레코드를 쓴다.** 예상 규모 — 파일 35 · 함수/클래스 104 · 산출물 약 12 · 키 약 10 · 개념 약 10 · 디렉토리 7 = **약 180개**. 반드시 들어가야 하는 키(Plan `llm-load-reduction` 이 쓰고 코드에 글자로 있는 것 — 🔵 실측):

| 키 | `kind` | 어디서 찾나 (시작점) |
|---|---|---|
| `codegraph.json` | `artifact` | `normalize.py` 의 `json.dump` 줄 |
| `roslyn-dump.json` | `artifact` | `normalize.py` C# 절 |
| `calls[]` `edges[]` `members[]` `nodes[]` `modules[]` | `key` | `normalize.py:285-287` 부근과 `verify_citations.py` |
| `PageRank` `hotspot` | `concept` | `facts.py` |
| `WarmUp` | `concept` | `grep -rn WarmUp codegraph scripts src` 로 2파일 |
| `normalize.py` `facts.py` `verify_citations.py` `terms_db.py` `collect.mjs` `quiz.mjs` `emit.mjs` | `file` | 각 파일 1줄 |
| `build_terms` `project_codegraph` `check_terms` `merge_terms` `pickTerms` `findNewConcepts` `gradeOne` `resolveScript` `runDispatch` | `function` | 선언 줄 |

- [ ] **Step 3: 검사가 실패 0 이 될 때까지 고친다**

Run: `.venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json`
Expected: 마지막 줄 `... — 용어 N개 / 실패 0 / 근거 없음 M` (M 은 보고에 목록과 이유를 붙인다) 그리고 `out/codegraph-raw/codegraph.json — 노드 …` 한 줄. 종료 코드 0.

- [ ] **Step 4: Mode 1.5 와 이어지는지 — 이 계획의 목적**

Run: `mkdir -p /tmp/rb-t7 && cd /tmp/rb-t7 && report-term collect $REPO_ROOT/docs/superpowers/plans/2026-08-28-llm-load-reduction.md $REPO_ROOT/out/codegraph-raw/terms-db.json && python3 -c "import json;d=json.load(open('term-candidates.json'));print(len(d['known']),sorted(d['known']));print(len(d['newConcepts']))"`
Expected: `known` 이 **8개 이상**이고 `codegraph.json` `roslyn-dump.json` `calls[]` `edges[]` `PageRank` `hotspot` `WarmUp` `members[]` 를 포함한다. `newConcepts` 는 34 미만으로 준다(`codegraph.json` `calls[]` 등이 known 으로 옮겨가므로).
`known` 에 `main` `check` 같은 낱말이 섞이면 그것은 R6(낱말 오탐)이지 이 Task 의 실패가 아니다 — 목록만 보고한다.

- [ ] **Step 5: 위키 인용 검증기가 투영을 읽는지 — 기존 도구와의 접점 한 번**

Run: `.venv/bin/python codegraph/verify_citations.py docs/superpowers/plans/2026-08-28-llm-load-reduction.md --repo . --codegraph out/codegraph-raw/codegraph.json | tail -3`
Expected: 오류 없이 3값 집계가 나온다 (숫자는 보고에 붙인다. 기대값 없음 — 첫 관측이다)

- [ ] **Step 6: 커밋 — 오케스트레이터가 사용자 승인 후. 원본만 추적한다**

```bash
git add docs/codegraph/terms-reading.json
git commit -m "[feat] : report-builder 자신의 전수조사 원본 terms-reading.json"
```

---

## 조사만 하고 구현하지 않는 것 — 기록만

| 항목 | 왜 안 하나 | 되살릴 조건 |
|---|---|---|
| StickRush(C#) 에 읽기 단계 적용 → C1(오답 보기 품질) 시험 (D7) | 이 계획의 목적은 이 저장소의 DB 다. C# 은 파일 241개 레코드를 LLM 이 다시 읽는 비용이 크다 | StickRush 용 Plan 이 생겼을 때 |
| `verify_citations.py` 가 `terms-db.json` 의 `where` 를 직접 읽게 통합 | `check_terms` 가 같은 규칙을 이미 쓴다. 도구 둘이 한 규칙을 공유하는 상태면 충분하다 — 합치면 거울 함정 | 규칙이 갈라지는 것이 관측될 때 |
| 스키마 파일(JSON Schema) | 소비자가 `check_terms` 하나다. 구현자 1 · 소비자 1 | 소비자가 둘 이상 될 때 |
| `pickTerms` 낱말 오탐(R6 — `Data` `Interface` `main`) | 별개 결정(RESUME R4 와 같은 갈래, "지금은 결정 안 한다") | 실사용에서 오탐 비율이 드러날 때 |
| `bin/report-wiki` 에 Node 파이프라인 | 실제 파이프라인은 Python 이다. 자리 표시자 유지 | 지시가 있을 때 |

## 순서와 배분

```
Task 1 → 2 → 3 → 4 → 5     직렬 (한 파일 terms_db.py · 한 테스트 파일 append 순서)   — mode-1-codebase-wiki
Task 6                     Task 5 와 병렬 가능 (문서만)                             — mode-1-codebase-wiki
Task 7                     Task 5 · 6 이후                                          — mode-1-codebase-wiki (LLM 읽기)
```

Task 1~5 는 서브에이전트 한 번에 맡겨도 된다 — 파일이 둘뿐이고 앞 Task 의 함수를 뒤가 부른다. 커밋은 Task 마다 오케스트레이터가 사용자 승인 후 경로를 좁혀 한다.

## Self-Review

- [x] 사용자 확정 3건(D1 · D2 · D6)이 Task 에 대응된다 — D1: Task 1·2·5, D2: Task 3, D6: 배분 절
- [x] 자리 표시자 없음 — 모든 코드 단계에 코드가 있다. Task 7 은 데이터라 코드 대신 인수 조건
- [x] 이름 일치 — `_split_where` `_recompute_neighbors` `project_codegraph` `check_terms` `merge_terms` `_stem` `_git_commit` `NON_NODE_KINDS` `KINDS` `EDGE_KINDS` `SOURCES` `STRUCTURE_FIELDS` 가 Task 간에 같다. `STRUCTURE_FIELDS` 는 선언만 하고 코드가 직접 쓰지 않는다 — `merge_terms` 가 그 필드를 **안 건드리는 것**으로 규칙을 구현하므로, 읽는 사람을 위한 문서 상수다
- [x] 금지 단어("검증됨" "입증" "증명") 없음 — `grep` 으로 확인할 것
- [x] `normalize.py` 출력 키를 바꾸지 않는다 — 읽기만 한다
