# <include file="machine/comments.xml" path="//term[@id='test_terms_db.py']"/>
# terms-db 우선 파이프라인의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_terms_db.py — terms-db 우선 파이프라인의 회귀 시험."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terms_db as T  # noqa: E402
from codegraph_types import CodeGraph  # noqa: E402
from xmldoc import Terms  # noqa: E402

# 환경변수가 없으면 절대 존재할 수 없는 경로를 쓴다 — 빈 문자열이면 아래 os.path.join 이
# 상대경로가 되어 이 저장소의 산출물을 골든으로 착각해 읽는다.
CS_REPO = os.path.expandvars(os.environ.get("CSHARP_REPO", "")) or "/골든저장소_미지정/CSHARP_REPO"
CPP_REPO = os.path.expandvars(os.environ.get("GRAPHICS_REPO", "")) or "/골든저장소_미지정/GRAPHICS_REPO"


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db._graph']"/>
# terms_db 테스트에서 공통으로 쓰는 가짜 코드 지도 하나를 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_terms_db.test_build_terms_keeps_id_and_typed_uses, machine.test_terms_db.test_check_does_not_judge_edge_kinds_that_came_from_codegraph, machine.test_terms_db.test_check_skips_citations_of_codegraph_records, machine.test_terms_db.test_cli_still_accepts_codegraph_positional, machine.test_terms_db.test_merge_adds_new_reading_records_and_links_neighbors (+4)
def _graph() -> CodeGraph:
    """합성 codegraph — 클래스 2, 외부 1, 간선 2, 모듈 1. normalize.py 출력 키 그대로.

    ⚠ cast — `build_terms` 가 읽는 것은 `nodes` · `edges` · `modules` 뿐이라 `platform` 과
    `source_tool` 을 일부러 적지 않는다. 그 둘은 투영이 스스로 채우는 값이다.
    """
    return cast(CodeGraph, {
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
    })


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_build_terms_keeps_id_and_typed_uses']"/>
# codegraph 에서 만든 용어 사전에 id 와 간선 종류가 그대로 남는지 보는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.test_terms_db._graph · 쓰이는 곳: 없음
# ── 1. codegraph ⊂ terms-db — 간선을 잃지 않는다
def test_build_terms_keeps_id_and_typed_uses():
    """codegraph 의 id 와 종류 붙은 간선이 용어 레코드에 그대로 실린다."""
    db = T.build_terms(_graph(), facts={}, hotspot=[])
    # `id` 가 붙어 있다는 것이 이 시험이 보는 내용이라 `.get` 으로 무르게 하지 않는다.
    assert db["Renderer"]["id"] == "A.B.Renderer"  # pyright: ignore[reportTypedDictNotRequiredAccess]
    assert db["Renderer"]["uses"] == [
        {"to": "Mesh", "kind": "association", "label": "mMesh", "where": "src/render/renderer.cs:40"},
        {"to": "(BCL) netstandard", "kind": "dependency", "label": None, "where": ""},
    ]
    assert db["Mesh"]["uses"] == []
    assert db["Mesh"]["neighbors"] == ["Renderer"], "이웃은 uses 의 역방향에서도 나와야 한다"
    assert db["render"]["uses"] == [] and db["render"]["id"] == "render"  # pyright: ignore[reportTypedDictNotRequiredAccess]
    assert db["render"]["neighbors"] == [], "모듈 이웃은 depends_on 이다 — 여기선 비어 있다"


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db._triples']"/>
# 코드 지도의 간선들을 (출발, 도착, 종류) 세 값 묶음의 집합으로 바꿔주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_terms_db.test_project_golden_is_superset_of_real_codegraph, machine.test_terms_db.test_project_round_trips_synthetic_graph
# ── 2. 투영 — terms-db -> codegraph.json. codegraph 는 terms-db 의 부분집합이다
def _triples(g: CodeGraph) -> set[tuple[str, str, str]]:
    return {(e["from"], e["to"], e["kind"]) for e in g["edges"]}


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_project_round_trips_synthetic_graph']"/>
# 용어 사전을 다시 codegraph 로 투영했을 때 원래 codegraph 와 노드·간선·모듈이 같은지 보는 시험이다.
# 쓰는 것: machine.test_terms_db._graph, machine.terms_db.build_terms, machine.terms_db.project_codegraph, machine.test_terms_db._triples · 쓰이는 곳: 없음
def test_project_round_trips_synthetic_graph():
    """투영이 노드 · 간선 · 모듈을 그대로 되돌린다."""
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_project_drops_terms_that_are_not_code']"/>
# 코드가 아닌 용어(예: artifact)와 그 용어로 가는 간선은 투영된 codegraph 에 실리지 않는지 보는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.test_terms_db._graph, machine.terms_db.project_codegraph · 쓰이는 곳: 없음
def test_project_drops_terms_that_are_not_code():
    """코드가 아닌 용어와 그리로 가는 간선은 지도에 싣지 않는다."""
    db = T.build_terms(_graph(), facts={}, hotspot=[])
    db["codegraph.json"] = {"id": "codegraph.json", "kind": "artifact", "module": "codegraph",
                            "where": "machine/normalize.py:285", "means": "코드 지도 파일.",
                            "uses": [], "neighbors": [], "source": "reading"}
    db["Renderer"]["uses"].append({"to": "codegraph.json", "kind": "dependency", "label": "writes", "where": ""})
    p = T.project_codegraph(db)
    assert "codegraph.json" not in {n["id"] for n in p["nodes"]}
    assert all(e["to"] != "codegraph.json" for e in p["edges"]), "지도 밖 용어로 가는 간선은 지도에 싣지 않는다"


@pytest.mark.parametrize("repo,lang", [(CS_REPO, "csharp"), (CPP_REPO, "cpp")])
# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_project_golden_is_superset_of_real_codegraph']"/>
# 실제 저장소에서 뽑은 codegraph.json 을 기준으로, 투영된 결과가 그 원본을 완전히 포함하는지(부분집합 관계) 확인하는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.terms_db.project_codegraph, machine.test_terms_db._triples · 쓰이는 곳: 없음
def test_project_golden_is_superset_of_real_codegraph(repo: str, lang: str):
    """실제 산출물로 확인한다 — codegraph 의 노드 · 간선 · 모듈이 투영에 전부 있다."""
    path = os.path.join(repo, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(path):
        pytest.skip(f"산출물 없음: {path}")
    g = json.load(open(path, encoding="utf-8"))
    p = T.project_codegraph(T.build_terms(g, facts={}, hotspot=[]), language=lang)
    assert {n["id"] for n in g["nodes"]} <= {n["id"] for n in p["nodes"]}
    assert _triples(g) <= _triples(p)
    assert {m["id"] for m in g["modules"]} == {m["id"] for m in p["modules"]}


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db._repo']"/>
# 인용 검사 테스트에서 쓸 가짜 저장소 하나를 임시 폴더에 만들어주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_terms_db._reading, machine.test_terms_db.test_cli_exits_1_when_a_citation_fails, machine.test_terms_db.test_cli_reading_only_writes_db_and_projection
# ── 3. 인용 3값 판정 — 실패(L1/L2) / 근거 없음(L3) / 통과
def _repo(tmp_path: Path) -> str:
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db._reading']"/>
# 인용 검사 테스트에서 쓸 고정된 reading 레코드 사전을 만들어주는 함수다.
# 쓰는 것: machine.test_terms_db._repo · 쓰이는 곳: machine.test_terms_db.test_check_flags_unknown_uses_target, machine.test_terms_db.test_check_l1_missing_file_is_failure, machine.test_terms_db.test_check_l2_line_past_eof_is_failure, machine.test_terms_db.test_check_l3_name_absent_is_unfounded_not_failure, machine.test_terms_db.test_check_passes_on_grounded_reading (+4)
def _reading() -> Terms:
    return {
        "build_terms": {"kind": "function", "module": "codegraph", "where": "codegraph/x.py:3",
                        "means": "용어 사전을 만든다.", "does": "노드를 돈다.",
                        "uses": [{"to": "_where", "kind": "dependency", "label": "calls",
                                  "where": "codegraph/x.py:4"}],
                        "source": "reading"},
        "_where": {"kind": "function", "module": "codegraph", "where": "codegraph/x.py:7",
                   "means": "위치 문자열을 만든다.", "uses": [], "source": "reading"},
    }


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_passes_on_grounded_reading']"/>
# 근거가 맞는 용어 기록은 지적받지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_passes_on_grounded_reading(tmp_path: Path):
    """근거가 맞는 reading 레코드는 아무 지적도 나오지 않는다."""
    db = T.merge_terms({}, _reading())
    assert T.check_terms(db, _repo(tmp_path)) == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_l1_missing_file_is_failure']"/>
# 존재하지 않는 파일을 가리키는 인용은 실패로 판정돼야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_l1_missing_file_is_failure(tmp_path: Path):
    """없는 파일을 가리키면 L1 실패다."""
    r = _reading(); r["_where"]["where"] = "codegraph/nope.py:1"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and term == "_where" and "L1" in why for lvl, term, why in out)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_l2_line_past_eof_is_failure']"/>
# 파일은 있지만 파일 끝을 넘는 줄 번호를 가리키는 인용은 실패로 판정돼야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_l2_line_past_eof_is_failure(tmp_path: Path):
    """파일 끝을 넘는 줄을 가리키면 L2 실패다."""
    r = _reading(); r["_where"]["where"] = "codegraph/x.py:99"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and "L2" in why for lvl, _term, why in out)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_l3_name_absent_is_unfounded_not_failure']"/>
# 파일과 줄 번호는 맞지만 그 근처에 심볼 이름 글자가 없을 때는 '실패' 가 아니라 '근거 없음' 으로 약하게 판정돼야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_l3_name_absent_is_unfounded_not_failure(tmp_path: Path):
    """근처에 이름이 없으면 실패가 아니라 "근거 없음" 이다."""
    r = _reading(); r["_where"]["where"] = "codegraph/x.py:1"   # 파일·줄은 있으나 근처에 _where 가 없다
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "근거 없음" and term == "_where" for lvl, term, _why in out)
    assert not any(lvl == "실패" for lvl, _term, _why in out)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_reading_record_requires_where']"/>
# 사람(또는 LLM)이 쓴 reading 레코드에 위치(where) 를 아예 안 적으면 그 자체로 실패라는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_reading_record_requires_where(tmp_path: Path):
    """reading 레코드에 where 가 비면 실패다."""
    r = _reading(); r["_where"]["where"] = ""
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and term == "_where" and "where" in why for lvl, term, why in out)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_flags_unknown_uses_target']"/>
# 한 레코드의 uses 가 사전에 아예 없는 용어를 가리키면 실패라는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.merge_terms, machine.terms_db.check_terms, machine.test_terms_db._reading, _repo · 쓰이는 곳: 없음
def test_check_flags_unknown_uses_target(tmp_path: Path):
    """사전에 없는 용어를 가리키는 uses 는 실패다."""
    r = _reading(); r["build_terms"]["uses"][0]["to"] = "ghost"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "실패" and "ghost" in why for lvl, _term, why in out)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_skips_citations_of_codegraph_records']"/>
# 정적 수집 도구(clang-doc 등)가 만든 레코드는 이 검사기가 인용 위치를 재검증하지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.terms_db.check_terms, machine.test_terms_db._graph, _repo · 쓰이는 곳: 없음
def test_check_skips_citations_of_codegraph_records(tmp_path: Path):
    """정적 도구가 낸 레코드의 위치는 여기서 재판정하지 않는다 — verify_citations.py 의 영역."""
    db = T.build_terms(_graph(), facts={}, hotspot=[])      # src/render/*.cs 는 가짜 저장소에 없다
    assert T.check_terms(db, _repo(tmp_path)) == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_merge_reading_overrides_means_but_not_structure']"/>
# reading(LLM이 읽은 내용)과 codegraph(정적 도구가 뽑은 구조)를 합칠 때, 뜻 설명은 reading 이 이기고 id·kind·module·where 같은 구조 정보는 codegraph 가 이기는지 보는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.test_terms_db._graph, machine.terms_db.merge_terms · 쓰이는 곳: 없음
# ── 4. 합치기 — 구조 필드는 codegraph 가 이긴다
def test_merge_reading_overrides_means_but_not_structure():
    """뜻은 reading 이 덮고 구조(id · kind · module · where)는 codegraph 가 이긴다."""
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    reading: Terms = {"Renderer": {"kind": "function", "module": "elsewhere", "where": "x.cs:1",
                                   "means": "장면을 그리는 클래스.",
                                   "does": "매 프레임 Mesh 를 그린다.",
                                   "uses": [{"to": "Mesh", "kind": "dependency",
                                             "label": "calls Draw",
                                             "where": "src/render/renderer.cs:50"}],
                                   "source": "reading"}}
    db = T.merge_terms(base, reading)
    r = db["Renderer"]
    # `does` 와 `id` 가 둘 다 있어야 한다는 것이 이 시험의 내용이라 첨자 그대로 둔다.
    assert r["means"] == "장면을 그리는 클래스." and r["does"] == "매 프레임 Mesh 를 그린다."  # pyright: ignore[reportTypedDictNotRequiredAccess]
    assert (r["id"], r["kind"], r["module"], r["where"]) == (  # pyright: ignore[reportTypedDictNotRequiredAccess]
        "A.B.Renderer", "class", "render", "src/render/renderer.cs:12"), "구조는 codegraph 가 이긴다"
    assert r["source"] == "codegraph+reading"
    kinds = {(u["to"], u["kind"]) for u in r["uses"]}
    assert ("Mesh", "association") in kinds and ("Mesh", "dependency") in kinds, "새 종류의 간선은 더해진다"
    added = next(u for u in r["uses"] if u["kind"] == "dependency" and u["to"] == "Mesh")
    assert added.get("source") == "reading", "reading 이 보탠 간선은 표시가 남아야 check 가 인용을 본다"
    assert base["Renderer"]["source"] == "codegraph", "입력을 제자리에서 바꾸지 않는다"


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_merge_adds_new_reading_records_and_links_neighbors']"/>
# codegraph 에는 없고 reading 에만 있는 새 레코드가 합치기 후 사전에 들어가고, 그 레코드가 가리키는 대상과 서로 이웃으로 연결되는지 보는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.test_terms_db._graph, machine.terms_db.merge_terms · 쓰이는 곳: 없음
def test_merge_adds_new_reading_records_and_links_neighbors():
    """codegraph 에 없던 reading 레코드가 들어오고 이웃이 양쪽에 걸린다."""
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    reading: Terms = {"codegraph.json": {"kind": "artifact", "module": "codegraph",
                                         "where": "machine/normalize.py:285",
                                         "means": "코드 지도 파일.",
                                         "uses": [{"to": "Renderer", "kind": "dependency",
                                                   "label": "lists", "where": ""}],
                                         "source": "reading"}}
    db = T.merge_terms(base, reading)
    assert db["codegraph.json"]["source"] == "reading"
    assert "codegraph.json" in db["Renderer"]["neighbors"], "reading 레코드의 uses 도 이웃에 반영된다"
    assert db["codegraph.json"]["neighbors"] == ["Renderer"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_merge_is_deterministic']"/>
# 같은 입력으로 `merge_terms` 를 두 번 돌리면 항상 같은 결과가 나오는지(결정론) 보는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.test_terms_db._graph, machine.terms_db.merge_terms, machine.test_terms_db._reading · 쓰이는 곳: 없음
def test_merge_is_deterministic():
    """같은 입력이면 같은 출력이다."""
    base = T.build_terms(_graph(), facts={}, hotspot=[])
    a = json.dumps(T.merge_terms(base, _reading()), ensure_ascii=False, sort_keys=True)
    b = json.dumps(T.merge_terms(base, _reading()), ensure_ascii=False, sort_keys=True)
    assert a == b


# ── 5. CLI — reading 만으로 terms-db.json + codegraph.json(투영) 을 낸다. 기존 호출 꼴은 그대로
HERE = os.path.dirname(os.path.abspath(__file__))


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db._run']"/>
# terms_db.py 를 명령줄 프로그램으로 실제로 실행시켜주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_terms_db.test_cli_exits_1_when_a_citation_fails, machine.test_terms_db.test_cli_needs_at_least_one_input, machine.test_terms_db.test_cli_reading_only_writes_db_and_projection, machine.test_terms_db.test_cli_still_accepts_codegraph_positional
def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, os.path.join(HERE, "terms_db.py"), *args],
                          capture_output=True, text=True)


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_cli_reading_only_writes_db_and_projection']"/>
# terms_db.py 를 커맨드라인 도구처럼 실행했을 때, reading 파일 하나만 줘도 제대로 동작하는지 확인하는 시험이다.
# 쓰는 것: machine.test_terms_db._repo, machine.test_terms_db._reading, machine.test_terms_db._run · 쓰이는 곳: 없음
def test_cli_reading_only_writes_db_and_projection(tmp_path: Path):
    """reading 만 줘도 terms-db.json 과 투영 codegraph.json 을 낸다."""
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_cli_exits_1_when_a_citation_fails']"/>
# reading 레코드 안의 인용(where)이 존재하지 않는 파일을 가리키면 CLI 가 실패로 끝나야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.test_terms_db._repo, machine.test_terms_db._reading, machine.test_terms_db._run · 쓰이는 곳: 없음
def test_cli_exits_1_when_a_citation_fails(tmp_path: Path):
    """인용이 하나라도 실패하면 종료 코드가 1 이다."""
    repo = _repo(tmp_path)
    bad = _reading(); bad["_where"]["where"] = "codegraph/nope.py:1"
    reading = tmp_path / "terms-reading.json"
    reading.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    r = _run(["--repo", repo, "--reading", str(reading), "-o", str(tmp_path / "out")])
    assert r.returncode == 1
    assert "L1" in r.stdout


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_cli_still_accepts_codegraph_positional']"/>
# 옛날 방식대로 codegraph.json 파일 경로를 위치 인자로 줘도 CLI 가 여전히 동작하는지 확인하는 시험이다.
# 쓰는 것: machine.test_terms_db._graph, machine.test_terms_db._run · 쓰이는 곳: 없음
def test_cli_still_accepts_codegraph_positional(tmp_path: Path):
    """기존 호출 꼴 `terms_db.py <codegraph.json> --repo` 가 그대로 돈다."""
    g = tmp_path / "codegraph.json"
    g.write_text(json.dumps(_graph()), encoding="utf-8")
    r = _run([str(g), "--repo", str(tmp_path), "-o", str(tmp_path / "out")])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "투영 대조" in r.stdout and "없는 것 0개" in r.stdout
    assert not (tmp_path / "out" / "codegraph.json").exists(), "codegraph 가 입력이면 투영을 파일로 쓰지 않는다"


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_cli_needs_at_least_one_input']"/>
# codegraph 위치 인자도, --reading 옵션도 아무것도 주지 않으면 CLI 가 사용법 오류로 끝나야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.test_terms_db._run · 쓰이는 곳: 없음
def test_cli_needs_at_least_one_input(tmp_path: Path):
    """입력을 하나도 안 주면 사용법 오류로 끝난다."""
    r = _run(["--repo", str(tmp_path)])
    assert r.returncode == 2 and "--reading" in r.stderr


# <include file="machine/comments.xml" path="//term[@id='machine.test_terms_db.test_check_does_not_judge_edge_kinds_that_came_from_codegraph']"/>
# 간선 종류(kind)가 정해진 6종 어휘 안에 있어야 한다는 규칙은 사람이나 LLM이 적은 간선에만 적용되고, 정적 도구(normalize.py)가 낸 instantiation·friendship 같은 간선에는 적용되지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.terms_db.build_terms, machine.terms_db.check_terms, machine.terms_db.merge_terms, machine.test_terms_db._graph, _repo · 쓰이는 곳: 없음
def test_check_does_not_judge_edge_kinds_that_came_from_codegraph(tmp_path: Path):
    """정적 도구의 간선 어휘는 재판정하지 않는다 — 여섯 어휘 제한은 LLM 이 쓴 간선에만 산다.

    normalize 는 instantiation · friendship 도 낸다. 그것을 실패로 세면 codegraph 만으로
    실패가 쏟아진다.
    """
    repo = _repo(tmp_path)
    g = _graph()
    g["edges"].append({"from": "A.B.Mesh", "to": "A.B.Renderer", "kind": "instantiation",
                       "label": None, "file": "src/render/mesh.cs", "line": 9})
    db = T.build_terms(g, facts={}, hotspot=[])
    assert T.check_terms(db, repo) == [], "codegraph 가 낸 간선 종류는 판정 대상이 아니다"

    # ⚠ cast — 일부러 모자란 reading 레코드를 준다. 보려는 것이 LLM 이 쓴 간선의 어휘
    #   하나뿐이라 kind · module · where 를 적지 않는다. 채워 넣으면 무엇을 보는지 흐려진다.
    merged = T.merge_terms(db, cast(Terms, {
        "Renderer": {"means": "장면을 그린다.", "source": "reading",
                     "uses": [{"to": "Mesh", "kind": "instantiation",
                               "label": None, "where": ""}]}}))
    assert any(lvl == "실패" and "instantiation" in why
               for lvl, _term, why in T.check_terms(merged, repo)), "LLM 이 쓴 간선은 여전히 판정한다"
