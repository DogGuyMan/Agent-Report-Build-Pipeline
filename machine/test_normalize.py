# <include file="machine/comments.xml" path="//term[@id='test_normalize.py']"/>
# 정규화 계층의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_uml_kind_is_not_identity']"/>
# clang-uml 이 낸 관계 이름을 우리 8종 관계 이름표로 바꾸는 대응표가 글자 그대로 옮기지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.CLANG_UML_KIND · 쓰이는 곳: 없음
# ── 1. kind 대응표 — 낱말이 같아서 오히려 위험한 자리
def test_clang_uml_kind_is_not_identity() -> None:
    """clang-uml 의 낱말을 그대로 옮기면 안 된다. 값 멤버는 composition, 포인터는 aggregation."""
    assert N.CLANG_UML_KIND["aggregation"] == "composition"
    assert N.CLANG_UML_KIND["association"] == "aggregation"
    # 항등이 아니라는 것 자체를 고정한다
    assert N.CLANG_UML_KIND["aggregation"] != "aggregation"
    assert N.CLANG_UML_KIND["association"] != "association"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_uml_kind_passthrough']"/>
# 이름이 같은 관계 종류(dependency, instantiation, friendship)는 대응표를 거쳐도 그대로 남는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.CLANG_UML_KIND · 쓰이는 곳: 없음
def test_clang_uml_kind_passthrough() -> None:
    """뜻이 같은 것은 그대로 간다."""
    for k in ("dependency", "instantiation", "friendship"):
        assert N.CLANG_UML_KIND[k] == k


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_containment_is_not_mapped']"/>
# containment 와 extension 이라는 관계 이름은 우리가 쓰는 8종 관계 목록에 자리가 없어서 대응표 자체에 들어있으면 안 된다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.CLANG_UML_KIND · 쓰이는 곳: 없음
def test_containment_is_not_mapped() -> None:
    """containment 는 8종 enum 에 자리가 없어 버린다. 대응표에 있으면 안 된다."""
    assert "containment" not in N.CLANG_UML_KIND
    assert "extension" not in N.CLANG_UML_KIND  # 2-패스로 갈린다(is_abstract)


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_csharp_kind_map_is_total']"/>
# C# 수집기(roslyn-dump)가 낼 수 있는 네 가지 관계 이름이 대응표에 빠짐없이 있는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.CS_KIND · 쓰이는 곳: 없음
def test_csharp_kind_map_is_total() -> None:
    """roslyn-dump 가 내는 4종이 전부 사상된다."""
    assert set(N.CS_KIND) == {"inherit", "realize", "assoc", "depend"}
    assert N.CS_KIND["assoc"] == "association"
    assert N.CS_KIND["depend"] == "dependency"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_r5_cpp_is_list_based_not_all_std_templates']"/>
# C++ 에서 std 컨테이너를 지도에서 지워도 되는지 판단하는 규칙이, 이름표만 보고 몽땅 지우는 게 아니라 미리 정한 목록에 있는 것만 지운다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.is_transparent_wrapper · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_r5_cpp_requires_std_namespace']"/>
# 이름이 vector 와 똑같아도 std 네임스페이스가 아니면 지도에서 지우면 안 된다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.is_transparent_wrapper · 쓰이는 곳: 없음
def test_r5_cpp_requires_std_namespace() -> None:
    """이름이 같아도 std 가 아니면 투과 대상이 아니다."""
    assert not N.is_transparent_wrapper(
        cast(N.UmlElement, {"namespace": "SJH", "is_template": True, "name": "vector"}))


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_r5_csharp_uses_generic_def_and_covers_array_and_tuple']"/>
# C# 에서 껍데기로 보고 투과시키는(속만 남기는) 제네릭 타입 목록에 배열("[]")과 튜플이 들어있는지, 반대로 인터페이스는 들어있지 않은지 확인하는 시험이다.
# 쓰는 것: machine.normalize.CS_TRANSPARENT_DEFS · 쓰이는 곳: 없음
def test_r5_csharp_uses_generic_def_and_covers_array_and_tuple() -> None:
    """C# 은 generic_def 기준이고 배열("[]")과 튜플도 투과 목록에 든다."""
    assert "[]" in N.CS_TRANSPARENT_DEFS
    assert "System.Collections.Generic.List`1" in N.CS_TRANSPARENT_DEFS
    assert "System.ValueTuple`2" in N.CS_TRANSPARENT_DEFS
    # 인터페이스는 투과하지 않는다
    assert not any("IReadOnly" in d for d in N.CS_TRANSPARENT_DEFS)


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_r7_csharp_uses_canonical_names_not_keywords']"/>
# roslyn-dump 가 타입 이름을 System.String 처럼 정식 이름으로 내보내므로, 원시 타입을 버리는 목록(R7)도 string 같은 키워드가 아니라 정식 이름으로 채워져야 매칭이 된다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.CS_R7 · 쓰이는 곳: 없음
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
# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cpp_module_of']"/>
# C++ 코드에서 어느 폴더에 있는 파일인지를 보고 그 파일이 속한 모듈 이름을 알아내는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.module_of · 쓰이는 곳: 없음
def test_cpp_module_of(path: str, expected: str) -> None:
    """C++ 은 경로의 폴더가 곧 모듈이다."""
    assert N.module_of(path) == expected


@pytest.mark.parametrize("path,expected", [
    ("Assets/@Scripts/Controller/HomeScene/HomeScene.cs", "Controller"),
    ("Assets/@Scripts/Managers/Managers.cs", "Managers"),
    ("Assets/@Editors/AddressableRenamer.cs", "@Editors"),
])
# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cs_module_of']"/>
# C# 코드에서 Assets/@Scripts 아래 한 겹의 폴더를 모듈로 본다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.cs_module_of · 쓰이는 곳: 없음
def test_cs_module_of(path: str, expected: str) -> None:
    """C# 도 폴더 트리를 따르되 Assets/@Scripts 아래 한 겹을 모듈로 본다."""
    assert N.cs_module_of(path) == expected


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cs_external_group_naming']"/>
# C# 에서 어셈블리 이름을 보고 그것이 표준 라이브러리인지, 유니티 엔진인지, 서드파티 패키지인지를 판단해 하나의 외부 이름으로 접는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.cs_external_group · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._load']"/>
# 골든 시험(실제 저장소 산출물로 하는 시험)들이 공통으로 쓰는 도우미 함수로, 주어진 저장소 경로 아래의 codegraph.json 파일을 읽어온다.
# 쓰는 것: machine.codegraph_types.CodeGraph · 쓰이는 곳: machine.test_normalize.test_golden_counts, machine.test_normalize.test_golden_cpp_association_is_zero, machine.test_normalize.test_golden_cpp_r5_recovered_first_party_ownership, machine.test_normalize.test_golden_csharp_has_no_ownership_kinds, machine.test_normalize.test_golden_external_nodes_have_no_location (+4)
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
# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_counts']"/>
# 실제 저장소를 정규화한 결과물의 노드·간선·모듈 개수가 정해진 숫자와 정확히 같은지 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_counts(repo: str, lang: str, nodes: int, edges: int, mods: int) -> None:
    """노드 · 간선 · 모듈 수를 못박는다 — 의도한 변경이면 기대값을 함께 고친다."""
    g = _load(repo)
    assert g["schema_version"] == 2
    assert g["language"] == lang
    assert len(g["nodes"]) == nodes
    assert len(g["edges"]) == edges
    assert len(g["modules"]) == mods


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_cpp_association_is_zero']"/>
# C++ 산출물에는 association 간선이 하나도 없어야 한다는 규칙을 확인하는 시험 함수다. 있으면 이름 대응표가 잘못 되돌아간 것이다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_cpp_association_is_zero() -> None:
    """C++ 에서 association 은 0이어야 한다 — 0이 아니면 대응표가 항등으로 되돌아간 것이다."""
    g = _load(CPP_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] == "association") == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "composition") > 0


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_csharp_has_no_ownership_kinds']"/>
# C# 은 언어 자체에 값 멤버/포인터 멤버 구분이 없어서 소유를 뜻하는 composition·aggregation 간선이 하나도 없어야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_csharp_has_no_ownership_kinds() -> None:
    """C# 은 언어에 소유 표지가 없어 composition/aggregation 이 0이다."""
    g = _load(CS_REPO)
    assert sum(1 for e in g["edges"] if e["kind"] in ("composition", "aggregation")) == 0
    assert sum(1 for e in g["edges"] if e["kind"] == "association") > 0


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_no_containment_leaked']"/>
# containment(포함) 관계는 8가지 간선 종류에 자리가 없어서 버려야 하는데, 산출물에 실수로 남아있지 않은지 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_no_containment_leaked() -> None:
    """containment 는 버린다. 산출물에 남아 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        assert all(e["kind"] != "containment" for e in g["edges"])


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_external_nodes_have_no_location']"/>
# 외부 노드(우리 저장소 밖의 라이브러리 등)는 소스 코드가 우리 손에 없으니 파일과 줄 번호가 비어있어야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_external_nodes_have_no_location() -> None:
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        for n in g["nodes"]:
            if n["kind"] == "external":
                assert n["file"] is None and n["line"] is None
                assert n["module"] == "__external__"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_r4_no_edges_out_of_island']"/>
# 간선은 항상 우리 코드에서 외부 라이브러리로만 향해야 하고, 외부 라이브러리에서 우리 코드로 되돌아오는 간선이 있으면 안 된다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_r4_no_edges_out_of_island() -> None:
    """간선은 사용자 코드 → 외부 단방향만. 외부발 간선이 있으면 안 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
        assert not [e for e in g["edges"] if e["from"] in ext]


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_module_deps_exclude_external']"/>
# 모듈끼리의 의존 관계는 실제 모듈끼리만 있어야 하고 __external__ 이라는 가짜 모듈이 끼면 안 된다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_module_deps_exclude_external() -> None:
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 모든 모듈이 그리로 향해 노이즈가 된다."""
    for repo in (CPP_REPO, CS_REPO):
        g = _load(repo)
        ids = {m["id"] for m in g["modules"]}
        assert "__external__" not in ids
        for m in g["modules"]:
            assert all(d in ids for d in m["depends_on"])


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_cpp_r5_recovered_first_party_ownership']"/>
# std 컨테이너를 지도에서 지워도, 우리 코드끼리의 소유 관계(예: 렌더 유닛이 메시를 가짐)는 여전히 남아있어야 한다는 것을 표본 하나로 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_cpp_r5_recovered_first_party_ownership() -> None:
    """R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다 — 표본 하나가 살아 있는지 본다."""
    g = _load(CPP_REPO)
    nm = {n["id"]: n["name"] for n in g["nodes"]}
    owned = {(nm[e["from"]], e.get("label"), nm[e["to"]])
             for e in g["edges"] if e["kind"] == "composition"}
    assert ("SJH::RenderUnit", "mesh", "SJH::Mesh") in owned


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_ownership_edges_all_have_location']"/>
# 소유를 뜻하는 간선(composition, aggregation)은 그 멤버가 어느 파일 몇 번째 줄에 선언됐는지 위치 정보를 반드시 가지고 있어야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._load · 쓰이는 곳: 없음
def test_golden_ownership_edges_all_have_location() -> None:
    """소유 간선은 멤버 선언 줄을 가진다 — clang-uml 의 members[] 를 따로 뒤져 얻는다."""
    g = _load(CPP_REPO)
    own = [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]
    assert own and all(e.get("file") and e.get("line") for e in own)


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_nested_name_uses_double_hash']"/>
# 클래스 안에 또 클래스가 있는 경우(중첩 타입) 이름을 Outer##Inner 처럼 이중 샵으로 구분해야 하고, ::로 나누면 인용 대조가 반드시 틀린다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.verify_citations.short · 쓰이는 곳: 없음
# ── 6. 중첩 타입 이름 규칙 — 검증기 쪽 규칙이지만 같은 뿌리라 여기서 고정
def test_nested_name_uses_double_hash() -> None:
    """중첩 타입의 구분자는 Outer##Inner 다. :: 로 쪼개면 L3 대조가 반드시 틀린다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verify_citations as V
    assert V.short("Program##UniformBlock") == "UniformBlock"
    assert V.short("SJH::Scene::Component") == "Component"
    assert V.short("Gamerecipe.StickRush.Managers") == "Managers"
    assert V.short("SJH::Reflect::TypeName<float>") == "TypeName"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._run_verifier']"/>
# 인용 검증기(verify_citations.py)를 임시 markdown 문서에 대해 실제로 실행해보고 그 출력을 문자열로 돌려주는 시험용 도우미 함수다.
# 쓰는 것: machine.verify_citations · 쓰이는 곳: machine.test_normalize.test_verifier_catches_l1_l2_and_wrong_name, machine.test_normalize.test_verifier_does_not_warn_on_sources_comment, machine.test_normalize.test_verifier_matches_name_on_adjacent_line
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_verifier_catches_l1_l2_and_wrong_name']"/>
# 위키 산문에 적힌 파일:줄 인용이 실제로 존재하는 파일인지(L1), 그 줄 번호가 파일 범위 안인지(L2), 거기 적힌 이름이 그 위치에 실제로 있는 이름인지(이름 대조)를 각각 따로 잡아내는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._run_verifier · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_verifier_does_not_warn_on_sources_comment']"/>
# <!-- Sources: ... --> 라는 주석은 근거 목록을 나열한 것이지 이름을 주장하는 문장이 아니므로, 그 안에 이름이 없어도 경고를 내면 안 된다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._run_verifier · 쓰이는 곳: 없음
def test_verifier_does_not_warn_on_sources_comment(tmp_path: Path) -> None:
    """`<!-- Sources: ... -->` 는 근거 목록이지 주장이 아니다 — 이름이 없어도 경고하면 안 된다."""
    cg = os.path.join(CPP_REPO, "out/codegraph-raw/codegraph.json")
    if not os.path.isfile(cg):
        pytest.skip("C++ 산출물 없음")
    out = _run_verifier(tmp_path,
                        "<!-- Sources: src/material/material.h:73, src/material/pass.h:54 -->\n",
                        CPP_REPO, cg)
    assert "이름 대조 경고" not in out, out


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_verifier_matches_name_on_adjacent_line']"/>
# 글이 줄바꿈되어 이름과 인용이 서로 다른 줄에 놓이더라도, 검증기가 그것을 이어서 읽고 잘못된 경고를 내지 않아야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.test_normalize._run_verifier · 쓰이는 곳: 없음
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

# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_terms_db_extracts_modules_and_classes']"/>
# codegraph.json 의 노드와 모듈이 용어 사전(terms_db)의 항목으로 잘 바뀌는지 확인하는 테스트다.
# 쓰는 것: machine.terms_db.build_terms · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_terms_db_means_is_never_empty']"/>
# 용어 사전의 모든 항목이 설명(means)을 반드시 갖는지 확인하는 테스트다.
# 쓰는 것: machine.terms_db.build_terms · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_terms_db_is_deterministic']"/>
# 같은 입력을 두 번 넣으면 항상 같은 결과가 나오는지(재현성) 확인하는 테스트다.
# 쓰는 것: machine.terms_db.build_terms · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_by_namespace_allowlist']"/>
# 허용목록에 있는 네임스페이스면 소스 파일 경로 없이도 1차(자체) 코드로 판정되는지 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
# ── 11. 1차 판정 — 네임스페이스가 없는 코드도 잡는다
def test_first_party_by_namespace_allowlist() -> None:
    """허용목록에 있는 네임스페이스는 저장소 경로를 몰라도 1차다."""
    # 일부러 name 을 뺀다 — 허용목록 경로가 이름을 보지 않고 끝난다는 것이 검사 내용이다.
    assert N.is_first_party(cast(N.UmlIdentity, {"namespace": "SJH::Core"}), None) is True


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_by_declaration_path']"/>
# 네임스페이스가 없어도 저장소 안 경로에서 클래스가 실제로 정의(선언)돼 있으면 1차로 판정되는지 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_by_declaration_path(tmp_path: Path) -> None:
    """네임스페이스가 없어도 저장소 안에서 **정의**됐으면 1차다 — app/ 이 이 경우다."""
    d = tmp_path / "app" / "src" / "view"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\nclass MainWindow : public QWidget\n{\n};\n",
                                    encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow",
                         "source_location": {"file": "app/src/view/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_rejects_forward_declaration']"/>
# 전방 선언(class QWidget;)만 있는 경우는 진짜 정의가 아니므로 1차로 판정하면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_rejects_forward_declaration(tmp_path: Path) -> None:
    """전방 선언은 정의가 아니다 — 이 검사가 없으면 외부 타입이 중요도 상위에 올라온다."""
    d = tmp_path / "app" / "src" / "feature"
    d.mkdir(parents=True)
    (d / "alignmentcontroller.h").write_text("#pragma once\nclass QWidget;\n", encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "QWidget",
                         "source_location": {"file": "app/src/feature/alignmentcontroller.h",
                                             "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_rejects_use_site']"/>
# 멤버 변수 선언처럼 타입을 그냥 '사용'만 하는 줄은 그 타입의 정의가 아니므로 1차로 판정하면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_rejects_use_site(tmp_path: Path) -> None:
    """멤버 선언 줄은 정의가 아니다 — cv::Mat3b img; 가 이 경우다."""
    d = tmp_path / "core"
    d.mkdir(parents=True)
    (d / "panorama.h").write_text("#pragma once\n\tcv::Mat3b img;\n", encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "cv", "name": "Mat_<uchar>",
                         "source_location": {"file": "core/panorama.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is False


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_accepts_nested_type']"/>
# 클래스 안에 중첩된 타입(예: MainWindow 안의 ServerState)도 이름 구분자 ##를 벗겨내면 정의 위치를 찾아 1차로 판정된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_accepts_nested_type(tmp_path: Path) -> None:
    """중첩 타입은 이름 구분자가 ## 다. 벗기지 않으면 우리 enum 이 외부로 밀린다."""
    d = tmp_path / "app"
    d.mkdir(parents=True)
    (d / "mainwindow.h").write_text("#pragma once\n    enum class ServerState\n    {\n    };\n",
                                    encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow##ServerState",
                         "source_location": {"file": "app/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path)) is True


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_never_accepts_std_even_inside_repo']"/>
# std::vector처럼 표준 라이브러리 타입은 저장소 안 파일 경로를 가리키더라도 절대 1차로 판정되면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_never_accepts_std_even_inside_repo() -> None:
    """clang-uml 은 std 타입의 위치로도 이 저장소의 첫 사용 지점을 준다 — 막지 않으면 1차가 된다."""
    el: N.UmlIdentity = {"namespace": "std", "name": "vector",
                         "source_location": {"file": "core/panorama/panorama.h"}}
    assert N.is_first_party(el, "/repo") is False


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_rejects_generated_files']"/>
# Qt의 자동 생성 코드(autogen) 안에 있는 타입은 빌드 산출물이지 직접 짠 코드가 아니므로 1차로 판정되면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_rejects_generated_files() -> None:
    """Qt autogen 의 Ui::* 는 빌드 산출물이라 1차가 아니다."""
    el: N.UmlIdentity = {
        "namespace": "Ui", "name": "MainWindow",
        "source_location": {"file": "app/build/x/vedit_gui_autogen/include/ui_mainwindow.h"}}
    assert N.is_first_party(el, "/repo") is False


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_rejects_outside_repo']"/>
# 저장소 바깥 경로(예: 시스템에 설치된 OpenCV 헤더)에서 선언된 타입은 1차로 판정되면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
def test_first_party_rejects_outside_repo() -> None:
    """저장소 밖에서 선언된 것은 1차가 아니다."""
    el: N.UmlIdentity = {"namespace": "cv", "name": "Mat",
                         "source_location": {"file": "/opt/homebrew/include/opencv2/core.hpp"}}
    assert N.is_first_party(el, "/repo") is False


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_first_party_without_repo_keeps_old_behavior']"/>
# repo 경로 인자를 안 주면 예전처럼 네임스페이스만 보고 판정하는 옛 동작이 그대로 유지되는지 확인하는 하위호환 테스트다.
# 쓰는 것: machine.normalize.is_first_party · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._doc']"/>
# clang_doc.load_clang_doc 이 실제로 내보내는 심볼 하나의 모양을 흉내 내어 만들어주는 시험용 픽스처 생성 함수다.
# 쓰는 것: machine.clang_doc.Symbol · 쓰이는 곳: machine.test_normalize.test_clang_doc_adds_function_nodes, machine.test_normalize.test_clang_doc_carries_signature_and_author_comment, machine.test_normalize.test_clang_doc_does_not_add_edges, machine.test_normalize.test_clang_doc_symbols_go_through_is_first_party, machine.test_normalize.test_clang_doc_wins_on_where_for_a_shared_type
def _doc(name: str, kind: str, namespace: str, file: str, line: int,
         signature: str = "", doc: str = "") -> Symbol:
    """clang_doc.load_clang_doc 이 내는 꼴 하나."""
    return {"name": name, "kind": kind, "namespace": namespace,
            "file": file, "line": line, "signature": signature, "doc": doc}


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_doc_adds_function_nodes']"/>
# clang-uml 이 놓친 자유 함수도 clang-doc 자료를 합치면 코드 지도에 노드로 나타나는지 확인하는 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp, machine.test_normalize._doc · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_doc_wins_on_where_for_a_shared_type']"/>
# clang-uml 과 clang-doc 이 같은 타입을 각자 다른 위치로 알고 있을 때, 노드를 두 개로 늘리지 않고 위치만 clang-doc 쪽으로 바꿔치기하는지 확인하는 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp, machine.test_normalize._doc · 쓰이는 곳: 없음
def test_clang_doc_wins_on_where_for_a_shared_type(tmp_path: Path) -> None:
    """같은 타입이면 노드를 늘리지 않고 위치만 clang-doc 것으로 갈아 끼운다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t", doc_symbols=[
        _doc("Session", "class", "SJH", "server/session.h", 42),
    ])
    first = [n for n in g["nodes"] if n["kind"] != "external"]
    assert len(first) == 1                       # 중복 노드가 생기면 안 된다
    assert first[0]["line"] == 42                # clang-uml 의 10 이 아니다


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_doc_does_not_add_edges']"/>
# clang-doc 은 심볼만 주지 관계(간선)는 분류하지 않으므로, clang-doc 자료를 더 넣어도 간선 수가 늘지 않아야 한다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp, machine.test_normalize._doc · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_doc_symbols_go_through_is_first_party']"/>
# clang-doc 으로 들어온 심볼도 우리 코드인지 남의 코드(외부 라이브러리)인지 가리는 판정을 그대로 통과해야 한다는 것을 확인하는 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp, machine.test_normalize._doc · 쓰이는 곳: 없음
def test_clang_doc_symbols_go_through_is_first_party(tmp_path: Path) -> None:
    """clang-doc 심볼도 1차 판정을 그대로 탄다 — 우회하면 외부 타입이 샌다."""
    g, _ = N.normalize_cpp([], [], str(tmp_path), "t", doc_symbols=[
        _doc("sort", "function", "std", "algorithm", 1),
        _doc("Mat", "class", "cv", "/밖/opencv/mat.hpp", 7),
    ])
    assert [n for n in g["nodes"] if n["kind"] != "external"] == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_clang_doc_carries_signature_and_author_comment']"/>
# clang-uml 은 주지 못하지만 clang-doc 은 주는 두 가지 정보 — 함수 시그니처와 저자가 단 문서 주석 — 이 노드에 그대로 실리는지 확인하는 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp, machine.test_normalize._doc · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_uml_only_nodes_keep_their_shape']"/>
# clang-doc 자료를 아예 안 주면 노드가 예전과 똑같은 모양으로 나와야 한다는 골든 보호 테스트다.
# 쓰는 것: machine.normalize.normalize_cpp · 쓰이는 곳: 없음
def test_uml_only_nodes_keep_their_shape(tmp_path: Path) -> None:
    """골든 보호 — clang-doc 을 안 주면 노드의 키 구성이 예전 그대로여야 한다.
    빈 signature/doc 키가 생기기만 해도 골든 저장소의 산출물이 통째로 달라진다."""
    g, _ = N.normalize_cpp([_UML_SESSION], [], str(tmp_path), "t")
    n = [x for x in g["nodes"] if x["kind"] != "external"][0]
    assert set(n) == {"id", "name", "kind", "module", "file", "line"}


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cli_accepts_clang_uml_and_clang_doc_together']"/>
# --clang-doc 옵션과 --clang-uml 옵션은 둘 중 하나만 고르는 게 아니라 같이 줄 수 있어야 한다는 것을 확인하는 시험 함수다. 서로 배타적이면 두 수집기 결과를 합칠 수 없게 된다.
# 쓰는 것: machine.normalize.build_parser · 쓰이는 곳: 없음
def test_cli_accepts_clang_uml_and_clang_doc_together() -> None:
    """--clang-doc 은 --clang-uml 과 **배타가 아니다**. 배타 그룹에 들어가면 합치기가 불가능해진다."""
    a = N.build_parser().parse_args(
        ["--clang-uml", "full_class.json", "--clang-doc", "clangdoc/json", "--repo", "."])
    assert a.clang_uml == "full_class.json"
    assert a.clang_doc == "clangdoc/json"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cli_clang_doc_is_optional']"/>
# --clang-doc 옵션을 안 주면 그냥 없는 채로(None) 넘어가고 예전과 똑같이 동작해야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.build_parser · 쓰이는 곳: 없음
def test_cli_clang_doc_is_optional() -> None:
    """안 주면 None 이고 예전 동작 그대로다."""
    assert N.build_parser().parse_args(["--clang-uml", "f.json"]).clang_doc is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_kind_map_has_no_ownership']"/>
# 파이썬 언어에는 C++ 처럼 값으로 갖는 멤버와 포인터로 갖는 멤버의 구분이 없어서, 파이썬용 관계 대응표에는 소유를 뜻하는 composition/aggregation 이 없어야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.PY_KIND · 쓰이는 곳: 없음
# ── 12. Python (griffe) — 식 트리 해석과 kind 사상
def test_py_kind_map_has_no_ownership() -> None:
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같은 이유로 소유 kind 를 쓰지 않는다."""
    assert set(N.PY_KIND.values()) == {"inheritance", "association", "dependency"}
    assert "composition" not in N.PY_KIND.values()
    assert "aggregation" not in N.PY_KIND.values()


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r7_covers_builtin_scalars_and_literals']"/>
# 파이썬 R7(원시 타입 버림) 목록에 str, int 같은 원시 스칼라 타입뿐 아니라 None, ... (Ellipsis) 같은 리터럴도 들어있어야 한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.PY_R7 · 쓰이는 곳: 없음
def test_py_r7_covers_builtin_scalars_and_literals() -> None:
    """R7 — 원시 스칼라뿐 아니라 식 자리에 리터럴로 오는 None 과 ... 도 노드가 아니다."""
    for name in ("str", "int", "float", "bool", "bytes", "None", "NoneType", "object", "..."):
        assert name in N.PY_R7
    assert "Node" not in N.PY_R7


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_transparent_is_concrete_containers_only']"/>
# 파이썬에서 속을 들여다보고 투과시키는(껍데기로 보는) 목록은 list·dict·set·tuple 같은 구체 컨테이너와 typing 별칭까지만이고, collections.abc.Mapping 같은 추상 인터페이스는 투과하지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.PY_TRANSPARENT · 쓰이는 곳: 없음
def test_py_transparent_is_concrete_containers_only() -> None:
    """R5 투과 목록은 구체 컨테이너와 typing 별칭까지다.

    추상 인터페이스(collections.abc.Mapping/Sequence)는 넣지 않는다 — C# 이
    IReadOnlyDictionary 를 투과하지 않기로 한 것과 같은 축이다.
    """
    for name in ("list", "dict", "set", "tuple", "typing.Optional", "typing.Union"):
        assert name in N.PY_TRANSPARENT
    for name in ("collections.abc.Mapping", "collections.abc.Sequence", "typing.Mapping"):
        assert name not in N.PY_TRANSPARENT


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_external_group_folds_stdlib_into_one']"/>
# 파이썬 표준 라이브러리 모듈들은 C++ 의 (STL) std 처럼 전부 하나의 외부 이름으로 접어야 한다는 규칙을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.py_external_group · 쓰이는 곳: 없음
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
# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_module_of_reuses_folder_tree']"/>
# 파이썬도 C++ 과 마찬가지로 폴더 구조가 곧 모듈 경계이므로, 파이썬 전용 함수를 새로 만들지 않고 C++ 이 쓰는 module_of 함수를 그대로 재사용한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.module_of · 쓰이는 곳: 없음
def test_py_module_of_reuses_folder_tree(path: str, expected: str) -> None:
    """Python 도 모듈 경계는 폴더 트리다 — 그래서 module_of() 를 **그대로 재사용**한다.

    이 테스트가 있는 이유: module_of() 는 C++ 이 주인이다. C++ 쪽 사정으로 그 함수가
    바뀌면 Python 갈래가 조용히 따라 바뀐다. 그때 여기서 시끄럽게 깨지라고 박아 둔다.
    """
    assert N.module_of(path) == expected


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_expr_name_reads_name_and_dotted_attribute']"/>
# 파이썬 코드의 식(표현) 나무에서 '쓰여진 그대로의 점으로 이어진 이름'을 꺼내는 함수를 확인하는 시험 함수다. 이름이 아닌 다른 종류의 식이면 아무것도 못 꺼내고 None 이 나와야 한다.
# 쓰는 것: machine.normalize.py_expr_name · 쓰이는 곳: 없음
def test_py_expr_name_reads_name_and_dotted_attribute() -> None:
    """식 트리에서 '쓰인 그대로의 점 이름' 을 꺼낸다. 이름이 아닌 식이면 None 이다."""
    assert N.py_expr_name({"cls": "ExprName", "name": "Node"}) == "Node"
    assert N.py_expr_name({"cls": "ExprAttribute", "values": [
        {"cls": "ExprName", "name": "abc"}, {"cls": "ExprName", "name": "Mapping"}]}) == "abc.Mapping"
    assert N.py_expr_name("None") == "None"
    assert N.py_expr_name({"cls": "ExprSubscript", "left": {}, "slice": {}}) is None
    assert N.py_expr_name(None) is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_resolve_prefers_import_table_then_same_module']"/>
# 파이썬에서 짧게 쓰인 이름(예: Node)을 완전한 전체 경로 이름(예: pyfx.base.Node)으로 복원할 때 어떤 순서로 찾는지를 확인하는 시험 함수다. 순서는 import 표를 먼저 보고, 그다음 같은 모듈 안을 보고, 둘 다 없으면 원래 쓰인 그대로 둔다.
# 쓰는 것: machine.normalize.py_resolve · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._walk']"/>
# 파이썬 타입 표현식(griffe expr)을 걸어 들어가며 실제로 참조하는 타입 이름들을 뽑아내는 py_walk_expr 함수를, 매번 같은 고정 픽스처 값들을 채워 호출해 주는 테스트 헬퍼 함수다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
def _walk(expr: "N.GriffeExpr | None") -> tuple[list[str], Counter[str]]:
    """py_walk_expr 를 픽스처 문맥으로 감싼다. (결과, stats) 를 돌려준다."""
    st: Counter[str] = Counter()
    got = N.py_walk_expr(expr, "pyfx.core", PYFX_IMPORTS, PYFX_FIRST, st)
    return got, st


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r5_unwraps_builtin_generic']"/>
# list[Node] 처럼 파이썬 내장 컨테이너 타입 안에 담긴 클래스 이름을 껍데기를 벗기고 찾아낼 수 있는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
def test_py_r5_unwraps_builtin_generic() -> None:
    """R5 — list[Node] 는 껍데기를 벗고 Node 로 내려간다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprName", "name": "Node"}})
    assert got == ["pyfx.base.Node"]
    assert st["R5 투과 컨테이너 경유"] == 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r5_unwraps_dict_and_drops_key_by_r7']"/>
# dict[str, Node] 처럼 키와 값이 있는 컨테이너에서 값(Node)만 남고 원시 타입인 키(str)는 버려지는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
def test_py_r5_unwraps_dict_and_drops_key_by_r7() -> None:
    """dict[str, Node] — 속이 ExprTuple 이다. str 은 R7 로 죽고 Node 만 남는다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "dict"},
                     "slice": {"cls": "ExprTuple", "elements": [
                         {"cls": "ExprName", "name": "str"},
                         {"cls": "ExprName", "name": "Node"}]}})
    assert got == ["pyfx.base.Node"]
    assert st["R7 원시 타입 버림"] == 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r5_unwraps_optional_and_pep604_union']"/>
# Optional[Node] 와 Node | None 처럼 같은 뜻이지만 griffe 가 서로 다른 모양으로 주는 두 표현이 둘 다 Node 로 정리되는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r5_nests_two_levels_deep']"/>
# list[dict[str, Node]] 처럼 컨테이너 안에 컨테이너가 두 겹으로 중첩된 경우에도 안쪽의 Node 까지 파고들어 찾아내는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_r5_does_not_unwrap_abstract_interface']"/>
# abc.Mapping[str, Node] 처럼 인터페이스 성격의 컨테이너는 list나 dict와 달리 속을 파고들지 않고 그 컨테이너 자신이 결과로 남는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_walk_drops_ellipsis_and_typing_plumbing']"/>
# tuple[Node, ...] 의 "..." 표시나 Generic[T] 의 Generic 처럼 실제 타입이 아닌 타이핑 배관 부분이 결과에서 걸러지는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_walk_drops_unresolvable_type_variable']"/>
# list[T] 처럼 컨테이너를 벗겨도 그 안이 실제 클래스가 아니라 이름만 있는 타입변수 T 라면, 그 T 는 노드가 아니므로 버려지는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
def test_py_walk_drops_unresolvable_type_variable() -> None:
    """투과 컨테이너를 지나 도달한 타입변수 T 는 해소 실패로 죽는다 — 노드가 아니다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprName", "name": "T"}})
    assert got == []
    assert st["해소 실패(빌트인·타입변수)"] == 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_py_walk_stops_at_depth_limit']"/>
# list[list[list[...Node...]]] 처럼 컨테이너를 아주 깊게(12겹) 중첩해도 순회 함수가 무한히 파고들다 죽지 않고 깊이 제한에서 멈추는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.py_walk_expr · 쓰이는 곳: 없음
def test_py_walk_stops_at_depth_limit() -> None:
    """무한 중첩을 만나도 죽지 않는다 — C# resolve() 의 depth 가드와 같은 자리."""
    expr: N.GriffeExpr = {"cls": "ExprName", "name": "Node"}
    for _ in range(12):
        expr = {"cls": "ExprSubscript", "left": {"cls": "ExprName", "name": "list"}, "slice": expr}
    got, st = _walk(expr)
    assert got == []
    assert st["식 깊이 초과"] >= 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._pyfx_dump']"/>
# griffe(파이썬 정적 분석 도구)가 실제로 내보내는 출력 모양을 손으로 흉내 낸, pyfx 라는 가짜 패키지(모듈 둘 · 클래스 둘)의 최소 덤프 딕셔너리를 만들어주는 시험용 픽스처 함수다.
# 쓰는 것: machine.normalize.GriffeDump · 쓰이는 곳: machine.test_normalize.test_python_edge_kinds_and_labels, machine.test_normalize.test_python_external_is_folded_and_marked, machine.test_normalize.test_python_has_no_ownership_kinds, machine.test_normalize.test_python_module_deps_exclude_external, machine.test_normalize.test_python_nodes_are_classes_with_qualified_names (+1)
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_nodes_are_classes_with_qualified_names']"/>
# griffe 가 클래스 이름을 짧게(Node, Engine)만 주기 때문에, 정규화 함수가 패키지 경로까지 붙여 완전한 점(.) 이름(pyfx.base.Node)으로 만들어 주는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_has_no_ownership_kinds']"/>
# 파이썬에는 C# 처럼 값으로 갖는 멤버와 포인터로 갖는 멤버의 구분이 없으므로, 정규화 결과에 소유 관계(composition/aggregation) 간선이 하나도 없어야 함을 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
def test_python_has_no_ownership_kinds(tmp_path: Path) -> None:
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같이 소유 간선이 0이어야 한다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    kinds = {e["kind"] for e in g["edges"]}
    assert "composition" not in kinds
    assert "aggregation" not in kinds
    assert kinds <= {"inheritance", "association", "dependency"}


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_edge_kinds_and_labels']"/>
# 상속은 inheritance 간선으로, 속성에 붙은 타입 주석은 association 간선으로, 함수 시그니처에 나오는 타입은 dependency 간선으로 각각 올바르게 분류되는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_external_is_folded_and_marked']"/>
# json.JSONEncoder 처럼 이 저장소 바깥(표준 라이브러리)에서 온 타입은 하나의 "(표준) stdlib" 노드로 뭉뚱그려지고, 그 사실이 표시(constraint=False)되는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_r4_no_edges_leave_the_external_island']"/>
# 외부 노드에서 다시 우리 코드 쪽으로 나가는 간선이 있으면 안 된다는 규칙(R4)이 파이썬에서도 지켜지는지 확인하는 시험이다. 파이썬은 구조상 애초에 이런 간선이 생기지 않는다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
def test_python_r4_no_edges_leave_the_external_island(tmp_path: Path) -> None:
    """간선은 1차 -> 외부 단방향만. 파이썬 갈래는 구조상 발생조차 하지 않는다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
    assert not [e for e in g["edges"] if e["from"] in ext]


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_python_module_deps_exclude_external']"/>
# 모듈끼리의 의존 관계 목록에는 우리 저장소 안 모듈만 있어야 하고 __external__ 이라는 가짜 모듈이 섞이면 안 된다는 것을 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python, machine.test_normalize._pyfx_dump · 쓰이는 곳: 없음
def test_python_module_deps_exclude_external(tmp_path: Path) -> None:
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 안 된다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ids = {m["id"] for m in g["modules"]}
    assert "__external__" not in ids
    for m in g["modules"]:
        assert all(d in ids for d in m["depends_on"])


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cli_griffe_dump_is_a_third_source']"/>
# griffe 덤프는 clang-uml, roslyn-dump 와 마찬가지로 셋 중 하나를 고르는 관계라서, --griffe-dump 를 주면 다른 둘은 자동으로 비어(None) 있어야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.build_parser · 쓰이는 곳: 없음
def test_cli_griffe_dump_is_a_third_source() -> None:
    """수집기 셋은 고르는 관계다 — 배타 그룹의 셋째로 들어간다."""
    a = N.build_parser().parse_args(["--griffe-dump", "g.json", "--repo", "."])
    assert a.griffe_dump == "g.json"
    assert a.clang_uml is None and a.roslyn_dump is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_cli_griffe_dump_conflicts_with_other_sources']"/>
# griffe 덤프는 --clang-doc 과 달리 다른 수집기와 합쳐 쓸 수 있는 관계가 아니라서, --clang-uml 과 함께 주면 프로그램이 오류로 종료돼야 한다는 것을 확인하는 시험 함수다.
# 쓰는 것: machine.normalize.build_parser · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize._griffe_dump']"/>
# 가짜 픽스처가 아니라 진짜 griffe 도구를 실행해서 실제 출력을 얻어오는 시험용 도우미 함수다. griffe 가 설치돼 있지 않으면 시험을 건너뛴다.
# 쓰는 것: griffe · 쓰이는 곳: machine.test_normalize.test_golden_python_external_nodes_have_no_location, machine.test_normalize.test_golden_python_fixture_counts, machine.test_normalize.test_golden_python_ownership_edges_are_absent, machine.test_normalize.test_golden_python_r5_recovered_first_party_through_containers
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_python_fixture_counts']"/>
# 합성 dict가 아니라 진짜 griffe 도구를 pyfx 라는 작은 픽스처 패키지에 돌려서 나온 결과의 노드/간선/모듈 개수가 기대한 값과 맞는지 고정해 두는 시험이다. griffe 출력 모양이 바뀌면 여기가 먼저 깨진다.
# 쓰는 것: machine.test_normalize._griffe_dump, machine.normalize.normalize_python · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_python_r5_recovered_first_party_through_containers']"/>
# R5 규칙(컨테이너 투과)이 없으면 nodes/table/spare/later 네 속성이 전부 사라져버릴 텐데, 실제로는 이 네 개가 하나의 association 간선으로 잘 합쳐져 남는지 진짜 griffe로 확인하는 시험이다.
# 쓰는 것: machine.test_normalize._griffe_dump, machine.normalize.normalize_python · 쓰이는 곳: 없음
def test_golden_python_r5_recovered_first_party_through_containers(tmp_path: Path) -> None:
    """R5 가 없으면 nodes/table/spare/later 네 속성이 통째로 사라진다 — 그게 안 일어나는지 본다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    by = {n["id"]: n["name"] for n in g["nodes"]}
    assoc = [e for e in g["edges"]
             if e["kind"] == "association" and by[e["to"]] == "pyfx.base.Node"]
    assert len(assoc) == 1
    assert assoc[0].get("occurrences") == 4      # nodes · table · spare · later 가 한 간선으로 접힘


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_python_external_nodes_have_no_location']"/>
# 외부(우리 저장소 바깥) 노드는 이 저장소에 소스 파일이 없으므로 file과 line이 항상 null이어야 함을 진짜 griffe로 확인하는 시험이다.
# 쓰는 것: machine.test_normalize._griffe_dump, machine.normalize.normalize_python · 쓰이는 곳: 없음
def test_golden_python_external_nodes_have_no_location(tmp_path: Path) -> None:
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    for n in g["nodes"]:
        if n["kind"] == "external":
            assert n["file"] is None and n["line"] is None
            assert n["module"] == "__external__"


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_golden_python_ownership_edges_are_absent']"/>
# C#과 같은 자리의 파이썬 판 확인 — 파이썬에서는 모든 변수 바인딩이 참조라서 소유(composition/aggregation) 간선이 절대 나올 수 없음을 진짜 griffe로 확인하는 시험이다.
# 쓰는 것: machine.test_normalize._griffe_dump, machine.normalize.normalize_python · 쓰이는 곳: 없음
def test_golden_python_ownership_edges_are_absent(tmp_path: Path) -> None:
    """C# 과 같은 자리 — 파이썬은 모든 바인딩이 참조라 소유 kind 가 나올 수 없다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    assert not [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_selfhost_python_smoke']"/>
# 합성 픽스처가 아니라 이 저장소 자신(machine/ 폴더)을 실제로 griffe에 돌려도 정규화 파이프라인이 죽지 않고 끝까지 도는지만 확인하는 연기 시험(smoke test)이다. machine/ 은 클래스와 상속이 거의 없어 구체적인 개수는 주장하지 않는다.
# 쓰는 것: machine.normalize.normalize_python · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_normalize.test_pyfx_namespace_package_filepath_is_a_list']"/>
# __init__.py 가 없는 파이썬 패키지(네임스페이스 패키지)는 griffe가 filepath를 문자열이 아니라 디렉토리 목록(list)으로 준다는 사실과, 정규화 함수가 그 경우를 제대로 처리해 첫 항목을 골라 상대경로를 만드는지 확인하는 시험이다.
# 쓰는 것: machine.normalize.normalize_python · 쓰이는 곳: 없음
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
