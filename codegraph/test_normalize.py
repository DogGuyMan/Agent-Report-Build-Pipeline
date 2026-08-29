"""test_normalize.py — 정규화 계층의 회귀 테스트.

**왜 필요한가.** `normalize.py` 의 세 자리는 **틀려도 오류가 나지 않는다** — 조용히 틀린
값을 내고 파이프라인 끝까지 통과한다. 그 셋을 고정하는 것이 이 파일의 전부다.

  1. kind 대응표   clang-uml 의 `aggregation` 은 codegraph 의 `composition` 이다.
                   항등 매핑을 쓰면 C++ 에서 166건이 조용히 틀린 칸에 들어간다(관찰 보고서 D절).
  2. R5 투과       목록 기반이다. "std 템플릿 전부" 로 일반화하면 basic_string 까지 투과해
                   `(STL) std` 노드가 사라지고 끝점 해소 실패가 47 -> 166 으로 는다(실측).
  3. 이름 규칙     중첩 타입은 `Outer##Inner` 다. `::` 로 쪼개면 L3 대조가 반드시 실패한다.

합성 데이터만으로 검증하지 않는다 — 아래 골든 테스트는 **실제 저장소 산출물**을 쓴다
(있을 때만 돌고, 없으면 skip).

  python -m pytest codegraph/test_normalize.py -q      # .venv 를 켠 뒤
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalize as N  # noqa: E402

# 환경변수가 없으면 절대 존재할 수 없는 경로를 쓴다 — 빈 문자열이면 아래 os.path.join 이
# 상대경로가 되어 **이 저장소의 산출물을 골든으로 착각해 읽는다**(실제로 겪었다).
CPP_REPO = os.path.expandvars(os.environ.get("GRAPHICS_REPO", "")) or "/골든저장소_미지정/GRAPHICS_REPO"
CS_REPO = os.path.expandvars(os.environ.get("CSHARP_REPO", "")) or "/골든저장소_미지정/CSHARP_REPO"


# ── 1. kind 대응표 — 낱말이 같아서 오히려 위험한 자리
def test_clang_uml_kind_is_not_identity():
    """clang-uml 의 낱말을 그대로 옮기면 안 된다. 값 멤버는 composition, 포인터는 aggregation."""
    assert N.CLANG_UML_KIND["aggregation"] == "composition"
    assert N.CLANG_UML_KIND["association"] == "aggregation"
    # 항등이 아니라는 것 자체를 고정한다
    assert N.CLANG_UML_KIND["aggregation"] != "aggregation"
    assert N.CLANG_UML_KIND["association"] != "association"


def test_clang_uml_kind_passthrough():
    """뜻이 같은 것은 그대로 간다."""
    for k in ("dependency", "instantiation", "friendship"):
        assert N.CLANG_UML_KIND[k] == k


def test_containment_is_not_mapped():
    """C-14 — containment 는 8종 enum 에 자리가 없어 버린다. 대응표에 있으면 안 된다."""
    assert "containment" not in N.CLANG_UML_KIND
    assert "extension" not in N.CLANG_UML_KIND  # 2-패스로 갈린다(is_abstract)


def test_csharp_kind_map_is_total():
    """roslyn-dump 가 내는 4종이 전부 사상된다."""
    assert set(N.CS_KIND) == {"inherit", "realize", "assoc", "depend"}
    assert N.CS_KIND["assoc"] == "association"
    assert N.CS_KIND["depend"] == "dependency"


# ── 2. R5 투과 — 목록 기반이라는 것을 고정
def test_r5_cpp_is_list_based_not_all_std_templates():
    """basic_string 은 투과하지 않는다. 일반화하면 (STL) std 노드가 통째로 사라진다."""
    tmpl = {"namespace": "std", "is_template": True}
    assert N.is_transparent_wrapper({**tmpl, "name": "vector"})
    assert N.is_transparent_wrapper({**tmpl, "name": "unique_ptr"})
    assert not N.is_transparent_wrapper({**tmpl, "name": "basic_string"})
    assert not N.is_transparent_wrapper({**tmpl, "name": "function"})


def test_r5_cpp_requires_std_namespace():
    """이름이 같아도 std 가 아니면 투과 대상이 아니다."""
    assert not N.is_transparent_wrapper({"namespace": "SJH", "is_template": True, "name": "vector"})


def test_r5_csharp_uses_generic_def_and_covers_array_and_tuple():
    """C# 은 generic_def 기준. 배열("[]")과 튜플이 포함돼야 한다 — 튜플은 실측으로 추가됐다."""
    assert "[]" in N.CS_TRANSPARENT_DEFS
    assert "System.Collections.Generic.List`1" in N.CS_TRANSPARENT_DEFS
    assert "System.ValueTuple`2" in N.CS_TRANSPARENT_DEFS
    # 인터페이스는 투과하지 않는다(probe 실측 — R7 후 IReadOnlyDictionary 가 남아 있었다)
    assert not any("IReadOnly" in d for d in N.CS_TRANSPARENT_DEFS)


def test_r7_csharp_uses_canonical_names_not_keywords():
    """roslyn-dump 는 System.String 으로 내므로 R7 도 정식 이름이어야 매칭된다."""
    assert "System.String" in N.CS_R7
    assert "System.Int32" in N.CS_R7
    assert "System.Object" in N.CS_R7          # 암묵 기반 타입
    assert "string" not in N.CS_R7             # 키워드로 두면 매칭이 안 된다


# ── 3. 모듈 경계 — 폴더 트리 규칙(C-15, C# 은 사용자 확정)
@pytest.mark.parametrize("path,expected", [
    ("src/render/renderer.h", "render"),
    ("apps/_MyApp_/main.cpp", "apps/_MyApp_"),
])
def test_cpp_module_of(path, expected):
    assert N.module_of(path) == expected


@pytest.mark.parametrize("path,expected", [
    ("Assets/@Scripts/Controller/HomeScene/HomeScene.cs", "Controller"),
    ("Assets/@Scripts/Managers/Managers.cs", "Managers"),
    ("Assets/@Editors/AddressableRenamer.cs", "@Editors"),
])
def test_cs_module_of(path, expected):
    assert N.cs_module_of(path) == expected


# ── 4. 외부 노드 명명 (C-9 R2)
def test_cs_external_group_naming():
    a2p = {"BakingSheet": "com.cathei.bakingsheet"}
    assert N.cs_external_group("netstandard", a2p) == "(BCL) netstandard"
    assert N.cs_external_group("UnityEditor.CoreModule", a2p) == "(엔진 에디터) UnityEditor"
    assert N.cs_external_group("UnityEngine.CoreModule", a2p) == "(엔진) UnityEngine.CoreModule"
    assert N.cs_external_group("UnityEngine.UIModule", a2p) == "com.unity.modules.ui"
    assert N.cs_external_group("BakingSheet", a2p) == "com.cathei.bakingsheet"
    # 접두 일치로 상위 패키지에 접힌다 (BakingSheet.Samples* 실측)
    assert N.cs_external_group("BakingSheet.Google", a2p) == "com.cathei.bakingsheet"
    assert N.cs_external_group("DOTween", a2p) == "(벤더링) DOTween"


# ── 5. 골든 — 실제 저장소 산출물. 합성 데이터만으로 검증하지 않는다.
def _load(repo):
    p = os.path.join(repo, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(p):
        pytest.skip(f"산출물 없음: {p}")
    return json.load(open(p, encoding="utf-8"))


@pytest.mark.parametrize("repo,lang,nodes,edges,mods", [
    (CPP_REPO, "cpp", 191, 417, 20),
    (CS_REPO, "csharp", 231, 540, 10),
])
def test_golden_counts(repo, lang, nodes, edges, mods):
    """수치가 바뀌면 무언가 변한 것이다 — 의도한 변경이면 이 기대값을 함께 고친다."""
    g = _load(repo)
    assert g["schema_version"] == 2
    assert g["language"] == lang
    assert len(g["nodes"]) == nodes
    assert len(g["edges"]) == edges
    assert len(g["modules"]) == mods


def test_golden_cpp_association_is_zero():
    """D절 대응표의 산술적 귀결 — C++ 에서 association 은 0이어야 한다.
    0이 아니면 대응표가 항등으로 되돌아간 것이다."""
    g = _load(CPP_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] == "association") == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "composition") > 0


def test_golden_csharp_has_no_ownership_kinds():
    """C# 은 언어에 소유 표지가 없어 composition/aggregation 이 0이다(함정 5)."""
    g = _load(CS_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] in ("composition", "aggregation")) == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "association") > 0


def test_golden_no_containment_leaked():
    """C-14 — containment 는 버린다. 산출물에 남아 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        assert all(e["kind"] != "containment" for e in g["edges"])


def test_golden_external_nodes_have_no_location():
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        for n in g["nodes"]:
            if n["kind"] == "external":
                assert n["file"] is None and n["line"] is None
                assert n["module"] == "__external__"


def test_golden_r4_no_edges_out_of_island():
    """C-9 R4 — 간선은 사용자 코드 → 외부 단방향만. 외부발 간선이 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
        assert not [e for e in g["edges"] if e["from"] in ext]


def test_golden_module_deps_exclude_external():
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 모든 모듈이 그리로 향해 노이즈가 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ids = {m["id"] for m in g["modules"]}
        assert "__external__" not in ids
        for m in g["modules"]:
            assert all(d in ids for d in m["depends_on"])


def test_golden_cpp_r5_recovered_first_party_ownership():
    """R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다 — 실측 표본이 살아 있는지 본다."""
    g = _load(CPP_REPO)
    nm = {n["id"]: n["name"] for n in g["nodes"]}
    owned = {(nm[e["from"]], e.get("label"), nm[e["to"]])
             for e in g["edges"] if e["kind"] == "composition"}
    assert ("SJH::RenderUnit", "mesh", "SJH::Mesh") in owned


def test_golden_ownership_edges_all_have_location():
    """C-16 의 전제 — 소유 간선은 멤버 선언 줄을 가진다(clang-uml members[] 구조 조회)."""
    g = _load(CPP_REPO)
    own = [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]
    assert own and all(e.get("file") and e.get("line") for e in own)


# ── 6. 중첩 타입 이름 규칙 — 검증기 쪽 규칙이지만 같은 뿌리라 여기서 고정
def test_nested_name_uses_double_hash():
    """F-2 실측 — 중첩 타입은 Outer##Inner 다. :: 로 쪼개면 L3 가 반드시 틀린다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verify_citations as V
    assert V.short("Program##UniformBlock") == "UniformBlock"
    assert V.short("SJH::Scene::Component") == "Component"
    assert V.short("Gamerecipe.StickRush.Managers") == "Managers"
    assert V.short("SJH::Reflect::TypeName<float>") == "TypeName"


# ── 7. 검증기 오염 시험 — 오탐을 고치면서 진탐지를 죽이지 않았는지 고정한다.
#    🔵 2026-08-28 실측 — Sources 주석 제외 + 인접 줄 대조로 오탐 24 -> 4 로 줄였다.
#    그 완화가 "위치는 맞는데 엉뚱한 심볼을 주장" 하는 진짜 오류까지 통과시키면 안 된다.
def _run_verifier(tmp_path, body, repo, codegraph, detail=None):
    import subprocess
    doc = tmp_path / "poison.md"
    doc.write_text(body, encoding="utf-8")
    cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "verify_citations.py"),
           str(doc), "--repo", repo, "--codegraph", codegraph]
    if detail:
        cmd += ["--detail", detail]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr


def test_verifier_catches_l1_l2_and_wrong_name(tmp_path):
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path, """
- 실재: Material 은 (src/material/material.h:73) 에 선언돼 있다
- L1 깨짐: 없는 파일 (src/material/ghost.h:10) 인용
- L2 깨짐: (src/material/material.h:99999) 줄 초과
- 엉뚱한 이름: RenderQueue 가 (src/material/material_property_block.h:55) 에 있다
""", CPP_REPO, cg)
    assert "L1  통과 3 / 실패 1" in out, out          # ghost.h 만 실패
    assert "L2  통과 2 / 실패 1" in out, out          # 99999 만 실패
    assert "이름 대조 경고 1건" in out, out            # RenderQueue != MaterialPropertyBlock


def test_verifier_does_not_warn_on_sources_comment(tmp_path):
    """`<!-- Sources: ... -->` 는 근거 목록이지 주장이 아니다 — 이름이 없어도 경고하면 안 된다."""
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path,
                        "<!-- Sources: src/material/material.h:73, src/material/pass.h:54 -->\n",
                        CPP_REPO, cg)
    assert "이름 대조 경고" not in out, out


def test_verifier_matches_name_on_adjacent_line(tmp_path):
    """산문이 줄바꿈되면 인용과 심볼 이름이 다른 줄에 있다 — 경고하면 안 된다(data.md:29 실측)."""
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path,
                        "핵심 타입은 Material 이고 그 선언은\n(src/material/material.h:73) 이다\n",
                        CPP_REPO, cg)
    assert "이름 대조 경고" not in out, out


# ── 8. 코드베이스 용어 DB (Mode 1.5 의 재료)
#   codegraph.json 의 실제 키를 따른다(normalize.py 출력부 실측): 노드 id/name/kind/module/file/line,
#   간선 from/to, 모듈 id/depends_on. source/target · name/files 는 존재하지 않는다.

def test_terms_db_extracts_modules_and_classes():
    """codegraph.json 의 노드와 모듈이 용어 항목이 돼야 한다. 이웃은 간선 from/to 에서 온다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {
        "language": "csharp",
        "nodes": [
            {"id": "A.B.Renderer", "name": "Renderer", "module": "render",
             "file": "src/render/renderer.cs", "line": 12, "kind": "class"},
            {"id": "A.B.Mesh", "name": "Mesh", "module": "render",
             "file": "src/render/mesh.cs", "line": 3, "kind": "class"},
        ],
        "edges": [{"from": "A.B.Renderer", "to": "A.B.Mesh", "kind": "association"}],
        "modules": [{"id": "render", "depends_on": []}],
    }
    db = T.build_terms(g, facts={}, hotspot=[])
    assert "Renderer" in db, "클래스 이름이 용어로 안 들어갔다"
    assert "render" in db, "모듈 이름이 용어로 안 들어갔다"
    assert db["Renderer"]["kind"] == "class"
    assert db["Renderer"]["where"] == "src/render/renderer.cs:12"
    assert db["Renderer"]["neighbors"] == ["Mesh"], "간선 from/to 가 이웃으로 안 들어갔다"
    assert db["Mesh"]["neighbors"] == ["Renderer"], "이웃은 양방향이어야 한다"
    assert db["render"]["kind"] == "module"


def test_terms_db_means_is_never_empty():
    """정답 칸이 비면 Mode 1.5 가 출제할 수 없다. 최소한 기계가 아는 사실로 채운다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {"language": "cpp",
         "nodes": [{"id": "N", "name": "Thing", "module": "core",
                    "file": "src/core/thing.h", "line": 4, "kind": "struct"}],
         "edges": [], "modules": [{"id": "core", "depends_on": []}]}
    db = T.build_terms(g, facts={}, hotspot=[])
    for name, rec in db.items():
        assert rec["means"].strip(), f"{name} 의 means 가 비었다"


def test_terms_db_is_deterministic():
    """같은 입력이면 같은 출력이어야 한다. LLM 혼선을 막는 것이 이 파일의 목적이다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {"language": "cpp",
         "nodes": [{"id": "N1", "name": "B", "module": "m", "file": "b.h", "line": 1, "kind": "class"},
                   {"id": "N2", "name": "A", "module": "m", "file": "a.h", "line": 2, "kind": "class"}],
         "edges": [], "modules": [{"id": "m", "depends_on": []}]}
    first = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    second = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    assert first == second


# ── 11. 1차 판정 — 네임스페이스가 없는 코드도 잡는다 (2026-08-29)
def test_first_party_by_namespace_allowlist():
    """허용목록에 있는 네임스페이스는 저장소 경로를 몰라도 1차다."""
    assert N.is_first_party({"namespace": "SJH::Core"}, None) is True


def test_first_party_by_declaration_path(tmp_path):
    """네임스페이스가 없어도 저장소 안에서 **정의**됐으면 1차다 — app/ 이 이 경우다."""
    d = tmp_path / "app" / "src" / "view"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\nclass MainWindow : public QWidget\n{\n};\n",
                                    encoding="utf-8")
    el = {"namespace": "", "name": "MainWindow",
          "source_location": {"file": "app/src/view/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


def test_first_party_rejects_forward_declaration(tmp_path):
    """`class QWidget;` 는 전방 선언이다 — 우리가 정의한 것이 아니다.
    🔵 이 검사가 없으면 QWidget 이 PageRank 상위에 올라온다(2026-08-29 실측)."""
    d = tmp_path / "app" / "src" / "feature"
    d.mkdir(parents=True)
    (d / "alignmentcontroller.h").write_text("#pragma once\nclass QWidget;\n", encoding="utf-8")
    el = {"namespace": "", "name": "QWidget",
          "source_location": {"file": "app/src/feature/alignmentcontroller.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


def test_first_party_rejects_use_site(tmp_path):
    """멤버 선언 줄은 정의가 아니다 — cv::Mat3b img; 가 이 경우다."""
    d = tmp_path / "core"
    d.mkdir(parents=True)
    (d / "panorama.h").write_text("#pragma once\n\tcv::Mat3b img;\n", encoding="utf-8")
    el = {"namespace": "cv", "name": "Mat_<uchar>",
          "source_location": {"file": "core/panorama.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


def test_first_party_accepts_nested_type(tmp_path):
    """중첩 타입은 이름 구분자가 ## 다. 벗기지 않으면 우리 enum 이 외부로 밀린다."""
    d = tmp_path / "app"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\n    enum class ServerState\n    {\n    };\n",
                                    encoding="utf-8")
    el = {"namespace": "", "name": "MainWindow##ServerState",
          "source_location": {"file": "app/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


def test_first_party_never_accepts_std_even_inside_repo():
    """F-1 — clang-uml 은 std 타입의 위치로 이 저장소의 첫 사용 지점을 준다.
    막지 않으면 std::vector 가 1차 코드가 된다."""
    el = {"namespace": "std", "name": "vector",
          "source_location": {"file": "core/panorama/panorama.h"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_rejects_generated_files():
    """Qt autogen 의 Ui::* 는 빌드 산출물이라 1차가 아니다."""
    el = {"namespace": "Ui", "name": "MainWindow",
          "source_location": {"file": "app/build/x/vedit_gui_autogen/include/ui_mainwindow.h"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_rejects_outside_repo():
    """저장소 밖에서 선언된 것은 1차가 아니다."""
    el = {"namespace": "cv", "name": "Mat",
          "source_location": {"file": "/opt/homebrew/include/opencv2/core.hpp"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_without_repo_keeps_old_behavior():
    """repo 를 안 주면 예전처럼 네임스페이스만 본다 — 기존 호출자가 안 깨진다."""
    el = {"namespace": "", "name": "MainWindow",
          "source_location": {"file": "app/src/view/mainwindow.h"}}
    assert N.is_first_party(el) is False


# ── 7. clang-doc 합치기 — 두 수집기의 역할 분담을 고정한다 (2026-08-29 신설)
#
# **왜 필요한가.** clang-uml 은 클래스 관계를 알고 clang-doc 은 심볼 전량을 안다.
# 합치는 규칙 넷이 전부 **틀려도 오류가 나지 않는** 자리다:
#   ① 노드는 합집합   ② 같은 타입의 where 는 clang-doc 이 이긴다
#   ③ 간선의 kind 는 clang-uml 만 낸다 (clang-doc 은 관계를 분류하지 않는다)
#   ④ 1차 판정은 기존 is_first_party 를 그대로 태운다 — 우회하면 Qt·OpenCV 가 샌다

_UML_SESSION = {
    "id": "u1", "name": "Session", "display_name": "SJH::Session",
    "namespace": "SJH", "type": "class",
    "source_location": {"file": "server/session.h", "line": 10},
}


def _doc(name, kind, namespace, file, line, signature="", doc=""):
    """clang_doc.load_clang_doc 이 내는 꼴 하나."""
    return {"name": name, "kind": kind, "namespace": namespace,
            "file": file, "line": line, "signature": signature, "doc": doc}


def test_clang_doc_adds_function_nodes(tmp_path):
    """①의 핵심 — clang-uml 이 0개를 내는 자유 함수가 여기서 들어온다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("ComputePanorama", "function", "SJH::Core::Panorama",
             "core/panorama/panorama.cpp", 129, signature="bool ComputePanorama()"),
    ])
    fns = [n for n in g["nodes"] if n["kind"] == "function"]
    assert len(fns) == 1
    # 이름은 clang-uml 의 display_name 과 같은 축이어야 한다 — 완전 수식 이름
    assert fns[0]["name"] == "SJH::Core::Panorama::ComputePanorama"
    assert (fns[0]["file"], fns[0]["line"]) == ("core/panorama/panorama.cpp", 129)
    assert fns[0]["module"] == "core"


def test_clang_doc_wins_on_where_for_a_shared_type(tmp_path):
    """② — 같은 타입이면 노드를 늘리지 않고 위치만 clang-doc 것으로 갈아 끼운다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t", doc_symbols=[
        _doc("Session", "class", "SJH", "server/session.h", 42),
    ])
    first = [n for n in g["nodes"] if n["kind"] != "external"]
    assert len(first) == 1                       # 중복 노드가 생기면 안 된다
    assert first[0]["line"] == 42                # clang-uml 의 10 이 아니다


def test_clang_doc_does_not_add_edges(tmp_path):
    """③ — clang-doc 은 관계를 분류하지 않는다. 간선 수가 늘면 안 된다."""
    els = [_UML_SESSION, {
        "id": "u2", "name": "Store", "display_name": "SJH::Store",
        "namespace": "SJH", "type": "class",
        "source_location": {"file": "server/store.h", "line": 5},
    }]
    rels = [{"type": "aggregation", "source": "u1", "destination": "u2", "label": "mStore"}]
    bare, _ = N.normalize_cpp(els, rels, str(tmp_path), "t")
    merged, _ = N.normalize_cpp(els, rels, str(tmp_path), "t", doc_symbols=[
        _doc("Session", "class", "SJH", "server/session.h", 42),
        _doc("Handle", "function", "SJH", "server/session.cpp", 88),
    ])
    assert len(merged["edges"]) == len(bare["edges"]) == 1
    assert merged["edges"][0]["kind"] == "composition"   # 대응표는 그대로다


def test_clang_doc_symbols_go_through_is_first_party(tmp_path):
    """④ — 세 겹 거름망을 우회하지 않는다. std 는 노드가 되지 않는다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("sort", "function", "std", "algorithm", 1),
        _doc("Mat", "class", "cv", "/밖/opencv/mat.hpp", 7),
    ])
    assert [n for n in g["nodes"] if n["kind"] != "external"] == []


def test_clang_doc_carries_signature_and_author_comment(tmp_path):
    """clang-uml 이 못 주던 둘 — 시그니처와 저자 문서 주석이 노드에 실린다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("BroadcastChannels", "function", "SJH::Core::Utils",
             "core/utils/channelutils.cpp", 8,
             signature="void BroadcastChannels(const cv::Mat & src)",
             doc="1채널을 3채널로 편다"),
    ])
    n = g["nodes"][0]
    assert n["signature"] == "void BroadcastChannels(const cv::Mat & src)"
    assert n["doc"] == "1채널을 3채널로 편다"


def test_uml_only_nodes_keep_their_shape(tmp_path):
    """골든 보호 — clang-doc 을 안 주면 노드의 키 구성이 예전 그대로여야 한다.
    빈 signature/doc 키가 생기기만 해도 골든 저장소의 산출물이 통째로 달라진다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t")
    n = [x for x in g["nodes"] if x["kind"] != "external"][0]
    assert set(n) == {"id", "name", "kind", "module", "file", "line"}


def test_cli_accepts_clang_uml_and_clang_doc_together():
    """--clang-doc 은 --clang-uml 과 **배타가 아니다**. 배타 그룹에 들어가면 합치기가 불가능해진다."""
    a = N.build_parser().parse_args(
        ["--clang-uml", "full_class.json", "--clang-doc", "clangdoc/json", "--repo", "."])
    assert a.clang_uml == "full_class.json"
    assert a.clang_doc == "clangdoc/json"


def test_cli_clang_doc_is_optional():
    """안 주면 None 이고 예전 동작 그대로다."""
    assert N.build_parser().parse_args(["--clang-uml", "f.json"]).clang_doc is None
