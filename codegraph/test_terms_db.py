"""test_terms_db.py — terms-db 우선 파이프라인의 회귀 테스트.

세 가지를 고정한다.
  1. codegraph.json ⊂ terms-db.json  — build_terms 가 간선을 잃지 않고, project_codegraph 가 되돌린다
  2. 인용 3값 판정              — 실패(L1/L2) / 근거 없음(L3) / 통과. reading 레코드는 where 가 필수
  3. 구조는 codegraph 가 이긴다  — merge_terms 가 LLM 레코드의 id/kind/module/where 로 덮어쓰지 않는다
골든(§2)은 실제 저장소 산출물을 쓴다 — 합성 데이터만으로 확인하지 않는다.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terms_db as T  # noqa: E402

# 환경변수가 없으면 절대 존재할 수 없는 경로를 쓴다 — 빈 문자열이면 아래 os.path.join 이
# 상대경로가 되어 **이 저장소의 산출물을 골든으로 착각해 읽는다**(실제로 겪었다).
CS_REPO = os.path.expandvars(os.environ.get("CSHARP_REPO", "")) or "/골든저장소_미지정/CSHARP_REPO"
CPP_REPO = os.path.expandvars(os.environ.get("GRAPHICS_REPO", "")) or "/골든저장소_미지정/GRAPHICS_REPO"


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


def test_check_does_not_judge_edge_kinds_that_came_from_codegraph(tmp_path):
    """정적 도구의 간선 어휘를 LLM 어휘로 재판정하지 않는다.

    normalize.py:25-29 는 instantiation · friendship 도 낸다. 이 둘을 실패로 세면
    C++ 저장소(GlobalMedia-OpenGL-ComputerGraphics)가 codegraph 만으로 16건 실패한다 —
    🔵 2026-08-29 실측. LLM 이 쓴 간선에는 여섯 어휘 제한이 그대로 살아 있어야 한다.
    """
    repo = _repo(tmp_path)
    g = _graph()
    g["edges"].append({"from": "A.B.Mesh", "to": "A.B.Renderer", "kind": "instantiation",
                       "label": None, "file": "src/render/mesh.cs", "line": 9})
    db = T.build_terms(g, facts={}, hotspot=[])
    assert T.check_terms(db, repo) == [], "codegraph 가 낸 간선 종류는 판정 대상이 아니다"

    merged = T.merge_terms(db, {"Renderer": {"means": "장면을 그린다.", "source": "reading",
                                             "uses": [{"to": "Mesh", "kind": "instantiation",
                                                       "label": None, "where": ""}]}})
    assert any(lvl == "실패" and "instantiation" in why
               for lvl, term, why in T.check_terms(merged, repo)), "LLM 이 쓴 간선은 여전히 판정한다"
