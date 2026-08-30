"""test_normalize.py — 정규화 계층의 회귀 시험."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import cast

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalize as N  # noqa: E402
from clang_doc import Symbol  # noqa: E402
from codegraph_types import CodeGraph  # noqa: E402

# 환경변수가 없으면 절대 존재할 수 없는 경로를 쓴다 — 빈 문자열이면 아래 os.path.join 이
# 상대경로가 되어 이 저장소의 산출물을 골든으로 착각해 읽는다.
CPP_REPO = os.path.expandvars(os.environ.get("GRAPHICS_REPO", "")) or "/골든저장소_미지정/GRAPHICS_REPO"
CS_REPO = os.path.expandvars(os.environ.get("CSHARP_REPO", "")) or "/골든저장소_미지정/CSHARP_REPO"


# ── 1. kind 대응표 — 낱말이 같아서 오히려 위험한 자리
def test_clang_uml_kind_is_not_identity() -> None:
    """clang-uml 의 낱말을 그대로 옮기면 안 된다. 값 멤버는 composition, 포인터는 aggregation."""
    assert N.CLANG_UML_KIND["aggregation"] == "composition"
    assert N.CLANG_UML_KIND["association"] == "aggregation"
    # 항등이 아니라는 것 자체를 고정한다
    assert N.CLANG_UML_KIND["aggregation"] != "aggregation"
    assert N.CLANG_UML_KIND["association"] != "association"


def test_clang_uml_kind_passthrough() -> None:
    """뜻이 같은 것은 그대로 간다."""
    for k in ("dependency", "instantiation", "friendship"):
        assert N.CLANG_UML_KIND[k] == k


def test_containment_is_not_mapped() -> None:
    """containment 는 8종 enum 에 자리가 없어 버린다. 대응표에 있으면 안 된다."""
    assert "containment" not in N.CLANG_UML_KIND
    assert "extension" not in N.CLANG_UML_KIND  # 2-패스로 갈린다(is_abstract)


def test_csharp_kind_map_is_total() -> None:
    """roslyn-dump 가 내는 4종이 전부 사상된다."""
    assert set(N.CS_KIND) == {"inherit", "realize", "assoc", "depend"}
    assert N.CS_KIND["assoc"] == "association"
    assert N.CS_KIND["depend"] == "dependency"


# ── 2. R5 투과 — 목록 기반이라는 것을 고정
# 이 절의 element 픽스처는 clang-uml 실제 출력 모양 그대로 둔다. `is_transparent_wrapper`
# 가 실제로 보는 것은 namespace 와 name 둘뿐이라 형을 맞추려 픽스처를 고치지 않는다.
def test_r5_cpp_is_list_based_not_all_std_templates() -> None:
    """basic_string 은 투과하지 않는다. 일반화하면 (STL) std 노드가 통째로 사라진다."""
    tmpl: dict[str, object] = {"namespace": "std", "is_template": True}
    assert N.is_transparent_wrapper(cast(N.UmlElement, {**tmpl, "name": "vector"}))
    assert N.is_transparent_wrapper(cast(N.UmlElement, {**tmpl, "name": "unique_ptr"}))
    assert not N.is_transparent_wrapper(cast(N.UmlElement, {**tmpl, "name": "basic_string"}))
    assert not N.is_transparent_wrapper(cast(N.UmlElement, {**tmpl, "name": "function"}))


def test_r5_cpp_requires_std_namespace() -> None:
    """이름이 같아도 std 가 아니면 투과 대상이 아니다."""
    assert not N.is_transparent_wrapper(
        cast(N.UmlElement, {"namespace": "SJH", "is_template": True, "name": "vector"}))


def test_r5_csharp_uses_generic_def_and_covers_array_and_tuple() -> None:
    """C# 은 generic_def 기준이고 배열("[]")과 튜플도 투과 목록에 든다."""
    assert "[]" in N.CS_TRANSPARENT_DEFS
    assert "System.Collections.Generic.List`1" in N.CS_TRANSPARENT_DEFS
    assert "System.ValueTuple`2" in N.CS_TRANSPARENT_DEFS
    # 인터페이스는 투과하지 않는다
    assert not any("IReadOnly" in d for d in N.CS_TRANSPARENT_DEFS)


def test_r7_csharp_uses_canonical_names_not_keywords() -> None:
    """roslyn-dump 는 System.String 으로 내므로 R7 도 정식 이름이어야 매칭된다."""
    assert "System.String" in N.CS_R7
    assert "System.Int32" in N.CS_R7
    assert "System.Object" in N.CS_R7          # 암묵 기반 타입
    assert "string" not in N.CS_R7             # 키워드로 두면 매칭이 안 된다


# ── 3. 모듈 경계 — 폴더 트리 규칙
@pytest.mark.parametrize("path,expected", [
    ("src/render/renderer.h", "render"),
    ("apps/_MyApp_/main.cpp", "apps/_MyApp_"),
])
def test_cpp_module_of(path: str, expected: str) -> None:
    """C++ 은 경로의 폴더가 곧 모듈이다."""
    assert N.module_of(path) == expected


@pytest.mark.parametrize("path,expected", [
    ("Assets/@Scripts/Controller/HomeScene/HomeScene.cs", "Controller"),
    ("Assets/@Scripts/Managers/Managers.cs", "Managers"),
    ("Assets/@Editors/AddressableRenamer.cs", "@Editors"),
])
def test_cs_module_of(path: str, expected: str) -> None:
    """C# 도 폴더 트리를 따르되 Assets/@Scripts 아래 한 겹을 모듈로 본다."""
    assert N.cs_module_of(path) == expected


# ── 4. 외부 노드 명명 — 외부 하나 = 노드 하나
def test_cs_external_group_naming() -> None:
    """어셈블리 이름을 패키지·엔진·벤더링 무리로 접는다."""
    a2p = {"BakingSheet": "com.cathei.bakingsheet"}
    assert N.cs_external_group("netstandard", a2p) == "(BCL) netstandard"
    assert N.cs_external_group("UnityEditor.CoreModule", a2p) == "(엔진 에디터) UnityEditor"
    assert N.cs_external_group("UnityEngine.CoreModule", a2p) == "(엔진) UnityEngine.CoreModule"
    assert N.cs_external_group("UnityEngine.UIModule", a2p) == "com.unity.modules.ui"
    assert N.cs_external_group("BakingSheet", a2p) == "com.cathei.bakingsheet"
    # 접두 일치로 상위 패키지에 접힌다
    assert N.cs_external_group("BakingSheet.Google", a2p) == "com.cathei.bakingsheet"
    assert N.cs_external_group("DOTween", a2p) == "(벤더링) DOTween"


# ── 5. 골든 — 실제 저장소 산출물. 합성 데이터만으로 검증하지 않는다.
def _load(repo: str) -> CodeGraph:
    p = os.path.join(repo, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(p):
        pytest.skip(f"산출물 없음: {p}")
    return json.load(open(p, encoding="utf-8"))


@pytest.mark.parametrize("repo,lang,nodes,edges,mods", [
    (CPP_REPO, "cpp", 191, 417, 20),
    (CS_REPO, "csharp", 231, 540, 10),
])
def test_golden_counts(repo: str, lang: str, nodes: int, edges: int, mods: int) -> None:
    """노드 · 간선 · 모듈 수를 못박는다 — 의도한 변경이면 기대값을 함께 고친다."""
    g = _load(repo)
    assert g["schema_version"] == 2
    assert g["language"] == lang
    assert len(g["nodes"]) == nodes
    assert len(g["edges"]) == edges
    assert len(g["modules"]) == mods


def test_golden_cpp_association_is_zero() -> None:
    """C++ 에서 association 은 0이어야 한다 — 0이 아니면 대응표가 항등으로 되돌아간 것이다."""
    g = _load(CPP_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] == "association") == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "composition") > 0


def test_golden_csharp_has_no_ownership_kinds() -> None:
    """C# 은 언어에 소유 표지가 없어 composition/aggregation 이 0이다."""
    g = _load(CS_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] in ("composition", "aggregation")) == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "association") > 0


def test_golden_no_containment_leaked() -> None:
    """containment 는 버린다. 산출물에 남아 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        assert all(e["kind"] != "containment" for e in g["edges"])


def test_golden_external_nodes_have_no_location() -> None:
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        for n in g["nodes"]:
            if n["kind"] == "external":
                assert n["file"] is None and n["line"] is None
                assert n["module"] == "__external__"


def test_golden_r4_no_edges_out_of_island() -> None:
    """간선은 사용자 코드 → 외부 단방향만. 외부발 간선이 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
        assert not [e for e in g["edges"] if e["from"] in ext]


def test_golden_module_deps_exclude_external() -> None:
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 모든 모듈이 그리로 향해 노이즈가 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ids = {m["id"] for m in g["modules"]}
        assert "__external__" not in ids
        for m in g["modules"]:
            assert all(d in ids for d in m["depends_on"])


def test_golden_cpp_r5_recovered_first_party_ownership() -> None:
    """R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다 — 표본 하나가 살아 있는지 본다."""
    g = _load(CPP_REPO)
    nm = {n["id"]: n["name"] for n in g["nodes"]}
    owned = {(nm[e["from"]], e.get("label"), nm[e["to"]])
             for e in g["edges"] if e["kind"] == "composition"}
    assert ("SJH::RenderUnit", "mesh", "SJH::Mesh") in owned


def test_golden_ownership_edges_all_have_location() -> None:
    """소유 간선은 멤버 선언 줄을 가진다 — clang-uml 의 members[] 를 따로 뒤져 얻는다."""
    g = _load(CPP_REPO)
    own = [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]
    assert own and all(e.get("file") and e.get("line") for e in own)


# ── 6. 중첩 타입 이름 규칙 — 검증기 쪽 규칙이지만 같은 뿌리라 여기서 고정
def test_nested_name_uses_double_hash() -> None:
    """중첩 타입의 구분자는 Outer##Inner 다. :: 로 쪼개면 L3 대조가 반드시 틀린다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verify_citations as V
    assert V.short("Program##UniformBlock") == "UniformBlock"
    assert V.short("SJH::Scene::Component") == "Component"
    assert V.short("Gamerecipe.StickRush.Managers") == "Managers"
    assert V.short("SJH::Reflect::TypeName<float>") == "TypeName"


# ── 7. 검증기 오염 시험 — 오탐을 고치면서 진탐지를 죽이지 않았는지 고정한다.
#    Sources 주석 제외와 인접 줄 대조는 완화다. 그 완화가 "위치는 맞는데 엉뚱한 심볼을
#    주장" 하는 진짜 오류까지 통과시키면 안 된다.
def _run_verifier(tmp_path: Path, body: str, repo: str, codegraph: str,
                  detail: str | None = None) -> str:
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


def test_verifier_catches_l1_l2_and_wrong_name(tmp_path: Path) -> None:
    """없는 파일 · 줄 초과 · 엉뚱한 이름을 각각 제 갈래로 잡는다."""
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


def test_verifier_does_not_warn_on_sources_comment(tmp_path: Path) -> None:
    """`<!-- Sources: ... -->` 는 근거 목록이지 주장이 아니다 — 이름이 없어도 경고하면 안 된다."""
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path,
                        "<!-- Sources: src/material/material.h:73, src/material/pass.h:54 -->\n",
                        CPP_REPO, cg)
    assert "이름 대조 경고" not in out, out


def test_verifier_matches_name_on_adjacent_line(tmp_path: Path) -> None:
    """산문이 줄바꿈되면 인용과 심볼 이름이 다른 줄에 있다 — 경고하면 안 된다."""
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path,
                        "핵심 타입은 Material 이고 그 선언은\n(src/material/material.h:73) 이다\n",
                        CPP_REPO, cg)
    assert "이름 대조 경고" not in out, out


# ── 8. 코드베이스 용어 DB (Mode 1.5 의 재료)
#   codegraph.json 의 실제 키를 따른다: 노드 id/name/kind/module/file/line, 간선 from/to,
#   모듈 id/depends_on. source/target · name/files 는 존재하지 않는다.

def test_terms_db_extracts_modules_and_classes() -> None:
    """codegraph.json 의 노드와 모듈이 용어 항목이 돼야 한다. 이웃은 간선 from/to 에서 온다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    # 부분 지도다 — `build_terms` 가 읽는 열쇠만 담았다. `CodeGraph` 는 나머지도 필수라
    # 그대로는 붙지 않는다.
    g = cast(CodeGraph, {
        "language": "csharp",
        "nodes": [
            {"id": "A.B.Renderer", "name": "Renderer", "module": "render",
             "file": "src/render/renderer.cs", "line": 12, "kind": "class"},
            {"id": "A.B.Mesh", "name": "Mesh", "module": "render",
             "file": "src/render/mesh.cs", "line": 3, "kind": "class"},
        ],
        "edges": [{"from": "A.B.Renderer", "to": "A.B.Mesh", "kind": "association"}],
        "modules": [{"id": "render", "depends_on": []}],
    })
    db = T.build_terms(g, facts={}, hotspot=[])
    assert "Renderer" in db, "클래스 이름이 용어로 안 들어갔다"
    assert "render" in db, "모듈 이름이 용어로 안 들어갔다"
    assert db["Renderer"]["kind"] == "class"
    assert db["Renderer"]["where"] == "src/render/renderer.cs:12"
    assert db["Renderer"]["neighbors"] == ["Mesh"], "간선 from/to 가 이웃으로 안 들어갔다"
    assert db["Mesh"]["neighbors"] == ["Renderer"], "이웃은 양방향이어야 한다"
    assert db["render"]["kind"] == "module"


def test_terms_db_means_is_never_empty() -> None:
    """정답 칸이 비면 Mode 1.5 가 출제할 수 없다. 최소한 기계가 아는 사실로 채운다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = cast(CodeGraph, {"language": "cpp",     # 위와 같은 이유로 부분 지도다
                         "nodes": [{"id": "N", "name": "Thing", "module": "core",
                                    "file": "src/core/thing.h", "line": 4, "kind": "struct"}],
                         "edges": [], "modules": [{"id": "core", "depends_on": []}]})
    db = T.build_terms(g, facts={}, hotspot=[])
    for name, rec in db.items():
        assert rec["means"].strip(), f"{name} 의 means 가 비었다"


def test_terms_db_is_deterministic() -> None:
    """같은 입력이면 같은 출력이어야 한다. LLM 혼선을 막는 것이 이 파일의 목적이다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = cast(CodeGraph, {"language": "cpp",     # 위와 같은 이유로 부분 지도다
                         "nodes": [{"id": "N1", "name": "B", "module": "m", "file": "b.h",
                                    "line": 1, "kind": "class"},
                                   {"id": "N2", "name": "A", "module": "m", "file": "a.h",
                                    "line": 2, "kind": "class"}],
                         "edges": [], "modules": [{"id": "m", "depends_on": []}]})
    first = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    second = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    assert first == second


# ── 11. 1차 판정 — 네임스페이스가 없는 코드도 잡는다
def test_first_party_by_namespace_allowlist() -> None:
    """허용목록에 있는 네임스페이스는 저장소 경로를 몰라도 1차다."""
    # 일부러 name 을 뺀다 — 허용목록 경로가 이름을 보지 않고 끝난다는 것이 검사 내용이다.
    assert N.is_first_party(cast(N.UmlIdentity, {"namespace": "SJH::Core"}), None) is True


def test_first_party_by_declaration_path(tmp_path: Path) -> None:
    """네임스페이스가 없어도 저장소 안에서 **정의**됐으면 1차다 — app/ 이 이 경우다."""
    d = tmp_path / "app" / "src" / "view"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\nclass MainWindow : public QWidget\n{\n};\n",
                                    encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow",
                         "source_location": {"file": "app/src/view/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


def test_first_party_rejects_forward_declaration(tmp_path: Path) -> None:
    """전방 선언은 정의가 아니다 — 이 검사가 없으면 외부 타입이 중요도 상위에 올라온다."""
    d = tmp_path / "app" / "src" / "feature"
    d.mkdir(parents=True)
    (d / "alignmentcontroller.h").write_text("#pragma once\nclass QWidget;\n", encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "QWidget",
                         "source_location": {"file": "app/src/feature/alignmentcontroller.h",
                                             "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


def test_first_party_rejects_use_site(tmp_path: Path) -> None:
    """멤버 선언 줄은 정의가 아니다 — cv::Mat3b img; 가 이 경우다."""
    d = tmp_path / "core"
    d.mkdir(parents=True)
    (d / "panorama.h").write_text("#pragma once\n\tcv::Mat3b img;\n", encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "cv", "name": "Mat_<uchar>",
                         "source_location": {"file": "core/panorama.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


def test_first_party_accepts_nested_type(tmp_path: Path) -> None:
    """중첩 타입은 이름 구분자가 ## 다. 벗기지 않으면 우리 enum 이 외부로 밀린다."""
    d = tmp_path / "app"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\n    enum class ServerState\n    {\n    };\n",
                                    encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow##ServerState",
                         "source_location": {"file": "app/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


def test_first_party_never_accepts_std_even_inside_repo() -> None:
    """clang-uml 은 std 타입의 위치로도 이 저장소의 첫 사용 지점을 준다 — 막지 않으면 1차가 된다."""
    el: N.UmlIdentity = {"namespace": "std", "name": "vector",
                         "source_location": {"file": "core/panorama/panorama.h"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_rejects_generated_files() -> None:
    """Qt autogen 의 Ui::* 는 빌드 산출물이라 1차가 아니다."""
    el: N.UmlIdentity = {
        "namespace": "Ui", "name": "MainWindow",
        "source_location": {"file": "app/build/x/vedit_gui_autogen/include/ui_mainwindow.h"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_rejects_outside_repo() -> None:
    """저장소 밖에서 선언된 것은 1차가 아니다."""
    el: N.UmlIdentity = {"namespace": "cv", "name": "Mat",
                         "source_location": {"file": "/opt/homebrew/include/opencv2/core.hpp"}}
    assert N.is_first_party(el, "/repo") is False


def test_first_party_without_repo_keeps_old_behavior() -> None:
    """repo 를 안 주면 예전처럼 네임스페이스만 본다 — 기존 호출자가 안 깨진다."""
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow",
                         "source_location": {"file": "app/src/view/mainwindow.h"}}
    assert N.is_first_party(el) is False


# ── 7. clang-doc 합치기 — 두 수집기의 역할 분담을 고정한다.
#   clang-uml 은 클래스 관계를 알고 clang-doc 은 심볼 전량을 안다.

_UML_SESSION: N.UmlElement = {
    "id": "u1", "name": "Session", "display_name": "SJH::Session",
    "namespace": "SJH", "type": "class",
    "source_location": {"file": "server/session.h", "line": 10},
}


def _doc(name: str, kind: str, namespace: str, file: str, line: int,
         signature: str = "", doc: str = "") -> Symbol:
    """clang_doc.load_clang_doc 이 내는 꼴 하나."""
    return {"name": name, "kind": kind, "namespace": namespace,
            "file": file, "line": line, "signature": signature, "doc": doc}


def test_clang_doc_adds_function_nodes(tmp_path: Path) -> None:
    """clang-uml 이 내지 않는 자유 함수가 clang-doc 쪽에서 노드로 들어온다."""
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


def test_clang_doc_wins_on_where_for_a_shared_type(tmp_path: Path) -> None:
    """같은 타입이면 노드를 늘리지 않고 위치만 clang-doc 것으로 갈아 끼운다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t", doc_symbols=[
        _doc("Session", "class", "SJH", "server/session.h", 42),
    ])
    first = [n for n in g["nodes"] if n["kind"] != "external"]
    assert len(first) == 1                       # 중복 노드가 생기면 안 된다
    assert first[0]["line"] == 42                # clang-uml 의 10 이 아니다


def test_clang_doc_does_not_add_edges(tmp_path: Path) -> None:
    """clang-doc 은 관계를 분류하지 않는다. 간선 수가 늘면 안 된다."""
    els: list[N.UmlElement] = [_UML_SESSION, {
        "id": "u2", "name": "Store", "display_name": "SJH::Store",
        "namespace": "SJH", "type": "class",
        "source_location": {"file": "server/store.h", "line": 5},
    }]
    rels: list[N.UmlRelationship] = [
        {"type": "aggregation", "source": "u1", "destination": "u2", "label": "mStore"}]
    bare, _ = N.normalize_cpp(els, rels, str(tmp_path), "t")
    merged, _ = N.normalize_cpp(els, rels, str(tmp_path), "t", doc_symbols=[
        _doc("Session", "class", "SJH", "server/session.h", 42),
        _doc("Handle", "function", "SJH", "server/session.cpp", 88),
    ])
    assert len(merged["edges"]) == len(bare["edges"]) == 1
    assert merged["edges"][0]["kind"] == "composition"   # 대응표는 그대로다


def test_clang_doc_symbols_go_through_is_first_party(tmp_path: Path) -> None:
    """clang-doc 심볼도 1차 판정을 그대로 탄다 — 우회하면 외부 타입이 샌다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("sort", "function", "std", "algorithm", 1),
        _doc("Mat", "class", "cv", "/밖/opencv/mat.hpp", 7),
    ])
    assert [n for n in g["nodes"] if n["kind"] != "external"] == []


def test_clang_doc_carries_signature_and_author_comment(tmp_path: Path) -> None:
    """clang-uml 이 못 주던 둘 — 시그니처와 저자 문서 주석이 노드에 실린다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("BroadcastChannels", "function", "SJH::Core::Utils",
             "core/utils/channelutils.cpp", 8,
             signature="void BroadcastChannels(const cv::Mat & src)",
             doc="1채널을 3채널로 편다"),
    ])
    n = g["nodes"][0]
    # 선택 열쇠라 대괄호로는 못 읽는다. `.get` 이라도 없으면 None 이 되어 그대로 실패한다.
    assert n.get("signature") == "void BroadcastChannels(const cv::Mat & src)"
    assert n.get("doc") == "1채널을 3채널로 편다"


def test_uml_only_nodes_keep_their_shape(tmp_path: Path) -> None:
    """골든 보호 — clang-doc 을 안 주면 노드의 키 구성이 예전 그대로여야 한다.
    빈 signature/doc 키가 생기기만 해도 골든 저장소의 산출물이 통째로 달라진다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t")
    n = [x for x in g["nodes"] if x["kind"] != "external"][0]
    assert set(n) == {"id", "name", "kind", "module", "file", "line"}


def test_cli_accepts_clang_uml_and_clang_doc_together() -> None:
    """--clang-doc 은 --clang-uml 과 **배타가 아니다**. 배타 그룹에 들어가면 합치기가 불가능해진다."""
    a = N.build_parser().parse_args(
        ["--clang-uml", "full_class.json", "--clang-doc", "clangdoc/json", "--repo", "."])
    assert a.clang_uml == "full_class.json"
    assert a.clang_doc == "clangdoc/json"


def test_cli_clang_doc_is_optional() -> None:
    """안 주면 None 이고 예전 동작 그대로다."""
    assert N.build_parser().parse_args(["--clang-uml", "f.json"]).clang_doc is None


# ── 12. Python (griffe) — 식 트리 해석과 kind 사상
def test_py_kind_map_has_no_ownership() -> None:
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같은 이유로 소유 kind 를 쓰지 않는다."""
    assert set(N.PY_KIND.values()) == {"inheritance", "association", "dependency"}
    assert "composition" not in N.PY_KIND.values()
    assert "aggregation" not in N.PY_KIND.values()


def test_py_r7_covers_builtin_scalars_and_literals() -> None:
    """R7 — 원시 스칼라뿐 아니라 식 자리에 리터럴로 오는 None 과 ... 도 노드가 아니다."""
    for name in ("str", "int", "float", "bool", "bytes", "None", "NoneType", "object", "..."):
        assert name in N.PY_R7
    assert "Node" not in N.PY_R7


def test_py_transparent_is_concrete_containers_only() -> None:
    """R5 투과 목록은 구체 컨테이너와 typing 별칭까지다.

    추상 인터페이스(collections.abc.Mapping/Sequence)는 넣지 않는다 — C# 이
    IReadOnlyDictionary 를 투과하지 않기로 한 것과 같은 축이다.
    """
    for name in ("list", "dict", "set", "tuple", "typing.Optional", "typing.Union"):
        assert name in N.PY_TRANSPARENT
    for name in ("collections.abc.Mapping", "collections.abc.Sequence", "typing.Mapping"):
        assert name not in N.PY_TRANSPARENT


def test_py_external_group_folds_stdlib_into_one() -> None:
    """R2 — 외부 하나 = 노드 하나. 표준 라이브러리는 C++ 의 "(STL) std" 와 같은 축으로 하나에 접는다."""
    assert N.py_external_group("json.JSONEncoder") == "(표준) stdlib"
    assert N.py_external_group("collections.abc.Mapping") == "(표준) stdlib"
    assert N.py_external_group("pytest") == "pytest"
    assert N.py_external_group("networkx.DiGraph") == "networkx"
    assert N.py_external_group("") == "(기타)"


@pytest.mark.parametrize("path,expected", [
    ("machine/normalize.py", "machine"),
    ("src/mypkg/core.py", "mypkg"),
    ("pyfx/base.py", "pyfx"),
    ("setup.py", "setup.py"),
])
def test_py_module_of_reuses_folder_tree(path: str, expected: str) -> None:
    """Python 도 모듈 경계는 폴더 트리다 — 그래서 module_of() 를 **그대로 재사용**한다.

    이 테스트가 있는 이유: module_of() 는 C++ 이 주인이다. C++ 쪽 사정으로 그 함수가
    바뀌면 Python 갈래가 조용히 따라 바뀐다. 그때 여기서 시끄럽게 깨지라고 박아 둔다.
    """
    assert N.module_of(path) == expected


def test_py_expr_name_reads_name_and_dotted_attribute() -> None:
    """식 트리에서 '쓰인 그대로의 점 이름' 을 꺼낸다. 이름이 아닌 식이면 None 이다."""
    assert N.py_expr_name({"cls": "ExprName", "name": "Node"}) == "Node"
    assert N.py_expr_name({"cls": "ExprAttribute", "values": [
        {"cls": "ExprName", "name": "abc"}, {"cls": "ExprName", "name": "Mapping"}]}) == "abc.Mapping"
    assert N.py_expr_name("None") == "None"
    assert N.py_expr_name({"cls": "ExprSubscript", "left": {}, "slice": {}}) is None
    assert N.py_expr_name(None) is None


def test_py_resolve_prefers_import_table_then_same_module() -> None:
    """이름 해소 순서: import 표 -> 같은 모듈 -> 못 품(쓰인 그대로).

    griffe 는 식 안의 이름을 짧은 이름으로만 준다. 완전 수식 이름은 모듈의 imports 표로만
    복원할 수 있다.
    """
    imports = {"Node": "pyfx.base.Node", "json": "json"}
    fp = {"pyfx.core.Engine", "pyfx.core.Local"}
    assert N.py_resolve("Node", "pyfx.core", imports, fp) == "pyfx.base.Node"
    assert N.py_resolve("json.JSONEncoder", "pyfx.core", imports, fp) == "json.JSONEncoder"
    assert N.py_resolve("Local", "pyfx.core", imports, fp) == "pyfx.core.Local"
    # import 표에도 없고 같은 모듈 1차도 아니면 손대지 않는다 — 빌트인과 타입변수가 여기다.
    assert N.py_resolve("list", "pyfx.core", imports, fp) == "list"
    assert N.py_resolve("T", "pyfx.core", imports, fp) == "T"


# 이 절의 식 리터럴은 griffe 의 실제 출력 모양 그대로다.
PYFX_IMPORTS = {"Node": "pyfx.base.Node", "Optional": "typing.Optional",
                "json": "json", "abc": "collections.abc", "Generic": "typing.Generic"}
PYFX_FIRST = {"pyfx.base.Node", "pyfx.core.Engine"}


def _walk(expr: "N.GriffeExpr | None") -> tuple[list[str], Counter[str]]:
    """py_walk_expr 를 픽스처 문맥으로 감싼다. (결과, stats) 를 돌려준다."""
    st: Counter[str] = Counter()
    got = N.py_walk_expr(expr, "pyfx.core", PYFX_IMPORTS, PYFX_FIRST, st)
    return got, st


def test_py_r5_unwraps_builtin_generic() -> None:
    """R5 — list[Node] 는 껍데기를 벗고 Node 로 내려간다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprName", "name": "Node"}})
    assert got == ["pyfx.base.Node"]
    assert st["R5 투과 컨테이너 경유"] == 1


def test_py_r5_unwraps_dict_and_drops_key_by_r7() -> None:
    """dict[str, Node] — 속이 ExprTuple 이다. str 은 R7 로 죽고 Node 만 남는다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "dict"},
                     "slice": {"cls": "ExprTuple", "elements": [
                         {"cls": "ExprName", "name": "str"},
                         {"cls": "ExprName", "name": "Node"}]}})
    assert got == ["pyfx.base.Node"]
    assert st["R7 원시 타입 버림"] == 1


def test_py_r5_unwraps_optional_and_pep604_union() -> None:
    """Optional[Node] 와 Node | None 은 같은 뜻이고 griffe 는 다른 모양으로 준다."""
    got_a, _ = _walk({"cls": "ExprSubscript",
                      "left": {"cls": "ExprName", "name": "Optional"},
                      "slice": {"cls": "ExprName", "name": "Node"}})
    # `operator` 는 griffe 가 실제로 내지만 `GriffeExprNode` 에는 없다 — normalize 가
    # 읽지 않는 열쇠라서다. 픽스처를 실제 모양대로 두려고 여기만 좁게 뚫는다.
    got_b, _ = _walk(cast("N.GriffeExpr", {"cls": "ExprBinOp",
                                           "left": {"cls": "ExprName", "name": "Node"},
                                           "operator": "|", "right": "None"}))
    assert got_a == ["pyfx.base.Node"]
    assert got_b == ["pyfx.base.Node"]


def test_py_r5_nests_two_levels_deep() -> None:
    """list[dict[str, Node]] — 문자열로 쓴 주석도 griffe 가 트리로 파싱해 준다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprSubscript",
                               "left": {"cls": "ExprName", "name": "dict"},
                               "slice": {"cls": "ExprTuple", "elements": [
                                   {"cls": "ExprName", "name": "str"},
                                   {"cls": "ExprName", "name": "Node"}]}}})
    assert got == ["pyfx.base.Node"]
    assert st["R5 투과 컨테이너 경유"] == 2


def test_py_r5_does_not_unwrap_abstract_interface() -> None:
    """abc.Mapping[str, Node] — 인터페이스는 투과하지 않는다. Mapping 자신이 남는다."""
    got, _ = _walk({"cls": "ExprSubscript",
                    "left": {"cls": "ExprAttribute", "values": [
                        {"cls": "ExprName", "name": "abc"},
                        {"cls": "ExprName", "name": "Mapping"}]},
                    "slice": {"cls": "ExprTuple", "elements": [
                        {"cls": "ExprName", "name": "str"},
                        {"cls": "ExprName", "name": "Node"}]}})
    assert got == ["collections.abc.Mapping"]


def test_py_walk_drops_ellipsis_and_typing_plumbing() -> None:
    """tuple[Node, ...] 의 "..." 도, Generic[T] 의 Generic 도 R7 로 죽는다.

    Generic 은 **투과하지 않는다** — abc.Mapping 과 같은 규칙이라 컨테이너 자신이 남는다.
    그래서 typing 배관을 R7 에 넣어 거른다. 안 그러면 제네릭 클래스마다
    (표준) stdlib 로 향하는 가짜 상속 간선이 하나씩 생긴다.
    """
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "tuple"},
                     "slice": {"cls": "ExprTuple", "elements": [
                         {"cls": "ExprName", "name": "Node"}, "..."]}})
    assert got == ["pyfx.base.Node"]
    assert st["R7 원시 타입 버림"] == 1

    got2, st2 = _walk({"cls": "ExprSubscript",
                       "left": {"cls": "ExprName", "name": "Generic"},
                       "slice": {"cls": "ExprName", "name": "T"}})
    assert got2 == []
    assert st2["R7 원시 타입 버림"] == 1


def test_py_walk_drops_unresolvable_type_variable() -> None:
    """투과 컨테이너를 지나 도달한 타입변수 T 는 해소 실패로 죽는다 — 노드가 아니다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprName", "name": "T"}})
    assert got == []
    assert st["해소 실패(빌트인·타입변수)"] == 1


def test_py_walk_stops_at_depth_limit() -> None:
    """무한 중첩을 만나도 죽지 않는다 — C# resolve() 의 depth 가드와 같은 자리."""
    expr: N.GriffeExpr = {"cls": "ExprName", "name": "Node"}
    for _ in range(12):
        expr = {"cls": "ExprSubscript", "left": {"cls": "ExprName", "name": "list"}, "slice": expr}
    got, st = _walk(expr)
    assert got == []
    assert st["식 깊이 초과"] >= 1


def _pyfx_dump(root: str) -> N.GriffeDump:
    """griffe 출력 모양 그대로의 최소 덤프. 두 모듈 · 두 클래스.

    `pyfx` 는 `__init__.py` 를 가진 보통 패키지라 `filepath` 가 그 파일을 가리키는 str 이다.
    `filepath` 가 list 로 오는 것은 `__init__.py` 가 없는 네임스페이스 패키지뿐이고, 그
    갈래는 `test_pyfx_namespace_package_filepath_is_a_list` 가 따로 고정한다.

    ⚠ cast 인 이유 둘. ① 실제 덤프에는 normalize 가 읽지 않는 열쇠가 더 섞인다.
    ② 패키지의 `imports` 는 실제로 `null` 로 오는데 형은 `dict[str, str]` 로 적혀 있다.
    픽스처를 형에 맞추지 않고 실제 모양대로 둔다.
    """
    return cast(N.GriffeDump, {"pyfx": {
        "kind": "module", "name": "pyfx",
        "filepath": f"{root}/pyfx/__init__.py", "imports": None,
        "members": {
            "base": {
                "kind": "module", "name": "base", "filepath": f"{root}/pyfx/base.py",
                "imports": {},
                "members": {"Node": {
                    "kind": "class", "name": "Node", "lineno": 1, "endlineno": 2, "bases": [],
                    "members": {"ident": {"kind": "attribute", "name": "ident", "lineno": 2,
                                          "annotation": {"cls": "ExprName", "name": "int"}}}}}},
            "core": {
                "kind": "module", "name": "core", "filepath": f"{root}/pyfx/core.py",
                "imports": {"Node": "pyfx.base.Node", "json": "json"},
                "members": {"Engine": {
                    "kind": "class", "name": "Engine", "lineno": 5, "endlineno": 12,
                    "bases": [{"cls": "ExprName", "name": "Node"}],
                    "members": {
                        "nodes": {"kind": "attribute", "name": "nodes", "lineno": 6,
                                  "annotation": {"cls": "ExprSubscript",
                                                 "left": {"cls": "ExprName", "name": "list"},
                                                 "slice": {"cls": "ExprName", "name": "Node"}}},
                        "enc": {"kind": "attribute", "name": "enc", "lineno": 7,
                                "annotation": {"cls": "ExprAttribute", "values": [
                                    {"cls": "ExprName", "name": "json"},
                                    {"cls": "ExprName", "name": "JSONEncoder"}]}},
                        "run": {"kind": "function", "name": "run", "lineno": 8, "endlineno": 9,
                                "parameters": [
                                    {"name": "self", "annotation": None},
                                    {"name": "n", "annotation": {"cls": "ExprName", "name": "Node"}}],
                                "returns": {"cls": "ExprName", "name": "Node"}},
                    }}}},
        }}})


def test_python_nodes_are_classes_with_qualified_names(tmp_path: Path) -> None:
    """노드 이름은 완전 수식 점 이름이다 — griffe 가 짧은 이름만 주므로 순회하며 이어 붙인다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    first = {n["name"]: n for n in g["nodes"] if n["kind"] != "external"}
    assert set(first) == {"pyfx.base.Node", "pyfx.core.Engine"}
    assert first["pyfx.core.Engine"]["file"] == "pyfx/core.py"
    assert first["pyfx.core.Engine"]["line"] == 5
    assert first["pyfx.core.Engine"]["module"] == "pyfx"
    assert g["language"] == "python"
    assert g["schema_version"] == 2


def test_python_has_no_ownership_kinds(tmp_path: Path) -> None:
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같이 소유 간선이 0이어야 한다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    kinds = {e["kind"] for e in g["edges"]}
    assert "composition" not in kinds
    assert "aggregation" not in kinds
    assert kinds <= {"inheritance", "association", "dependency"}


def test_python_edge_kinds_and_labels(tmp_path: Path) -> None:
    """상속 = inheritance · 속성 주석 = association · 시그니처 = dependency."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    by = {n["id"]: n["name"] for n in g["nodes"]}
    got = {(by[e["from"]], by[e["to"]], e["kind"]): e for e in g["edges"]}

    assert ("pyfx.core.Engine", "pyfx.base.Node", "inheritance") in got
    assoc = got[("pyfx.core.Engine", "pyfx.base.Node", "association")]
    assert assoc["label"] == "nodes" and assoc["line"] == 6      # R5 로 list[Node] 를 벗겼다
    dep = got[("pyfx.core.Engine", "pyfx.base.Node", "dependency")]
    assert dep.get("occurrences") == 2                            # 매개변수 n + 반환 하나씩
    # Node.ident: int 는 R7 로 죽어 Node 에서 나가는 간선이 없다.
    assert not [e for e in g["edges"] if by[e["from"]] == "pyfx.base.Node"]


def test_python_external_is_folded_and_marked(tmp_path: Path) -> None:
    """R2/R6 — json.JSONEncoder 는 "(표준) stdlib" 하나로 접히고 constraint=False 를 단다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ext = [n for n in g["nodes"] if n["kind"] == "external"]
    assert len(ext) == 1
    assert ext[0]["name"] == "(표준) stdlib"
    assert ext[0]["file"] is None and ext[0]["line"] is None
    assert ext[0]["module"] == "__external__"
    assert ext[0].get("collapsed_from") == ["json.JSONEncoder"]   # 선택 열쇠 — 위와 같다
    to_ext = [e for e in g["edges"] if e["to"] == ext[0]["id"]]
    assert len(to_ext) == 1 and to_ext[0].get("constraint") is False


def test_python_r4_no_edges_leave_the_external_island(tmp_path: Path) -> None:
    """간선은 1차 -> 외부 단방향만. 파이썬 갈래는 구조상 발생조차 하지 않는다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
    assert not [e for e in g["edges"] if e["from"] in ext]


def test_python_module_deps_exclude_external(tmp_path: Path) -> None:
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 안 된다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ids = {m["id"] for m in g["modules"]}
    assert "__external__" not in ids
    for m in g["modules"]:
        assert all(d in ids for d in m["depends_on"])


def test_cli_griffe_dump_is_a_third_source() -> None:
    """수집기 셋은 고르는 관계다 — 배타 그룹의 셋째로 들어간다."""
    a = N.build_parser().parse_args(["--griffe-dump", "g.json", "--repo", "."])
    assert a.griffe_dump == "g.json"
    assert a.clang_uml is None and a.roslyn_dump is None


def test_cli_griffe_dump_conflicts_with_other_sources() -> None:
    """--clang-uml 과 함께 줄 수 없다. --clang-doc 과 달리 이건 합치는 관계가 아니다."""
    with pytest.raises(SystemExit):
        N.build_parser().parse_args(["--griffe-dump", "g.json", "--clang-uml", "u.json"])


# ── 13. Python 골든 — 합성 dict 가 아니라 진짜 griffe 를 태운다.
#    machine/ 자기호스팅은 클래스와 상속이 거의 없어 불변식을 못 세운다. 그래서 픽스처
#    패키지를 tmp_path 에 써서 돌린다 — machine/ 안에 두면 자기호스팅 덤프에 섞여 들어간다.
PYFX_FILES = {
    "pyfx/__init__.py": "",
    "pyfx/base.py": "class Node:\n    ident: int\n",
    "pyfx/core.py": (
        "import json\n"
        "from typing import Optional\n"
        "from .base import Node\n"
        "\n"
        "\n"
        "class Engine(Node):\n"
        "    nodes: list[Node]\n"
        "    table: dict[str, Node]\n"
        "    spare: Optional[Node]\n"
        "    later: Node | None\n"
        "    enc: json.JSONEncoder\n"
        "\n"
        "    def run(self, n: Node) -> list[Node]:\n"
        "        return []\n"
    ),
}


def _griffe_dump(tmp_path: Path, files: dict[str, str], pkg: str) -> N.GriffeDump:
    """픽스처를 tmp_path 에 쓰고 실제 griffe 로 덤프해 dict 로 돌려준다.

    griffe 가 없으면 건너뛴다 — 기존 골든 테스트 관습(_load 의 pytest.skip)과 같다.
    """
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치 — .venv/bin/pip install -r requirements.txt")
    for rel, body in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    out = tmp_path / "griffe.json"
    r = subprocess.run([sys.executable, "-m", "griffe", "dump", pkg,
                        "-o", str(out), "-s", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_golden_python_fixture_counts(tmp_path: Path) -> None:
    """griffe 의 출력 모양이 바뀌면 여기가 먼저 깨진다 — 의도한 변경이면 기대값을 함께 고친다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, stats = N.normalize_python(dump, str(tmp_path), "griffe test")
    assert g["schema_version"] == 2
    assert g["language"] == "python"
    assert len(g["nodes"]) == 3
    assert len(g["edges"]) == 4
    assert len(g["modules"]) == 1
    assert stats["R5 투과 컨테이너 경유"] >= 4      # list · dict · Optional · list(반환)


def test_golden_python_r5_recovered_first_party_through_containers(tmp_path: Path) -> None:
    """R5 가 없으면 nodes/table/spare/later 네 속성이 통째로 사라진다 — 그게 안 일어나는지 본다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    by = {n["id"]: n["name"] for n in g["nodes"]}
    assoc = [e for e in g["edges"]
             if e["kind"] == "association" and by[e["to"]] == "pyfx.base.Node"]
    assert len(assoc) == 1
    assert assoc[0].get("occurrences") == 4      # nodes · table · spare · later 가 한 간선으로 접힘


def test_golden_python_external_nodes_have_no_location(tmp_path: Path) -> None:
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    for n in g["nodes"]:
        if n["kind"] == "external":
            assert n["file"] is None and n["line"] is None
            assert n["module"] == "__external__"


def test_golden_python_ownership_edges_are_absent(tmp_path: Path) -> None:
    """C# 과 같은 자리 — 파이썬은 모든 바인딩이 참조라 소유 kind 가 나올 수 없다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    assert not [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]


def test_selfhost_python_smoke() -> None:
    """실제 저장소를 태워도 파이프라인이 죽지 않는지만 본다 — 불변식 검증이 아니다.

    machine/ 은 클래스와 상속이 거의 없어 여기서는 간선 수 따위를 주장하지 않는다.
    진짜 불변식은 위 픽스처 골든이 본다.
    """
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치")
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "g.json")
        r = subprocess.run([sys.executable, "-m", "griffe", "dump", "machine",
                            "-o", out, "-s", repo], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        dump = json.load(open(out, encoding="utf-8"))
    g, stats = N.normalize_python(dump, repo, "griffe selfhost")
    assert g["language"] == "python"
    assert g["schema_version"] == 2
    assert stats["모듈"] > 15
    assert all(n["module"] == "machine" for n in g["nodes"] if n["kind"] != "external")
    ids = {m["id"] for m in g["modules"]}
    assert "__external__" not in ids


def test_pyfx_namespace_package_filepath_is_a_list(tmp_path: Path) -> None:
    """네임스페이스 패키지(= __init__.py 없음)는 filepath 가 디렉토리 목록(list)으로 온다.

    갈림은 "패키지냐 모듈이냐" 가 아니라 __init__.py 유무다. 이 저장소의 machine/ 에는
    __init__.py 가 없어 운영 경로가 바로 이 갈래이고, walk_module 의
    `fp[0] if isinstance(fp, list)` 가 죽은 가지가 아니다.
    """
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치")
    pkg = tmp_path / "nspkg"
    pkg.mkdir()
    (pkg / "m.py").write_text("class A:\n    pass\n", encoding="utf-8")   # __init__.py 를 두지 않는다
    out = tmp_path / "g.json"
    r = subprocess.run([sys.executable, "-m", "griffe", "dump", "nspkg",
                        "-o", str(out), "-s", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    dump = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(dump["nspkg"]["filepath"], list)      # ← 고정하려는 사실

    g, _ = N.normalize_python(cast(N.GriffeDump, dump), str(tmp_path), "griffe test")
    first = [n for n in g["nodes"] if n["kind"] != "external"]
    assert [n["name"] for n in first] == ["nspkg.m.A"]
    assert first[0]["file"] == "nspkg/m.py"                 # list 를 풀어 상대경로가 제대로 났다
    assert first[0]["module"] == "nspkg"
