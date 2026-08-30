"""test_declmap.py — 선언·문서주석 추출기의 회귀 시험."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap as D  # noqa: E402


def _doc(lines: list[str], i: int, lang: str) -> str:
    return D.doc_above(lines, i, D.LANGS[lang])


# ── 1. 선언을 잡는가
def test_cs_decl_catches_modifiers_and_generics() -> None:
    """수식어가 여러 개 붙고 들여쓰여 있어도 종류와 이름을 뽑는다."""
    m = D.LANGS["cs"]["decl"].match("    public static partial class Factory")
    assert m and m.group(1) == "class" and m.group(2).strip() == "Factory"


def test_cs_decl_catches_interface_with_constraint() -> None:
    """제네릭 제약절이 뒤에 붙은 인터페이스 선언도 잡는다."""
    m = D.LANGS["cs"]["decl"].match("public interface IStatableUI<T> where T : Enum")
    assert m and m.group(1) == "interface"


def test_cpp_decl_catches_enum_class() -> None:
    """`enum class` 는 두 낱말이 한 종류다."""
    m = D.LANGS["cpp"]["decl"].match("\tenum class E_MOTION_MODEL : uint")
    assert m and m.group(1) == "enum class" and m.group(2) == "E_MOTION_MODEL"


def test_py_decl_catches_def_and_class() -> None:
    """def 와 class 를 모두 잡고 이름을 두 번째 그룹에 둔다."""
    fn = D.LANGS["py"]["decl"].match("def build_terms(x):")
    assert fn and fn.group(2) == "build_terms"
    cls = D.LANGS["py"]["decl"].match("class Fact:")
    assert cls and cls.group(2) == "Fact"


def test_ts_decl_catches_export_function() -> None:
    """export 가 앞에 붙은 함수 선언을 잡는다."""
    m = D.LANGS["ts"]["decl"].match("export function wikiPaths(repo) {")
    assert m and m.group(1) == "function" and m.group(2) == "wikiPaths"


# ── 2. 문서 주석을 벗기는가
def test_cs_doc_strips_slashes_and_xml_tags() -> None:
    """`///` 와 XML 태그를 벗기고 본문만 남긴다."""
    lines = ["/// <summary>", "/// 싱글톤", "/// </summary>", "public class Singleton"]
    assert _doc(lines, 3, "cs") == "싱글톤"


def test_cs_doc_skips_attribute_between_comment_and_decl() -> None:
    """주석과 선언 사이에 낀 속성 줄을 건너뛴다."""
    lines = ["/// 음식 데이터", "[System.Serializable]", "public struct SerialDataFood"]
    assert _doc(lines, 2, "cs") == "음식 데이터"


def test_cpp_doc_strips_comment_marker() -> None:
    """`//` 표시를 벗기고 본문만 남긴다."""
    lines = ["// 한 겹을 세 겹으로 편다", "cv::Mat3f BroadcastChannels("]
    assert _doc(lines, 1, "cpp") == "한 겹을 세 겹으로 편다"


def test_doc_stops_at_code() -> None:
    """주석이 아닌 코드 줄을 만나면 멈춘다 — 위쪽 딴 함수의 주석을 끌어오지 않는다."""
    lines = ["// 딴 함수 주석", "int other() { return 0; }", "", "void target()"]
    assert _doc(lines, 3, "cpp") == ""


def test_doc_has_a_ceiling() -> None:
    """아무리 긴 주석 더미라도 정해진 줄 수까지만 거슬러 올라간다."""
    lines = ["// 줄%d" % i for i in range(40)] + ["void target()"]
    got = _doc(lines, len(lines) - 1, "cpp")
    assert got and len(got.split()) <= D.DOC_MAX_LINES


# ── 3. 파일 거르기
def test_skip_dirs_covers_build_and_cache() -> None:
    """빌드 산출물과 캐시 디렉토리가 거름망에 들어 있다."""
    for d in ("node_modules", "__pycache__", "vcpkg_installed", "out"):
        assert d in D.SKIP_DIRS


# ── 4. 1차 판정의 git 추적 거름망 (normalize.py)
import normalize as N  # noqa: E402


def test_first_party_rejects_qt_type_seen_inside_repo() -> None:
    """저장소 안에서 보였어도 git 이 추적하지 않는 파일의 타입은 1차가 아니다."""
    el: N.UmlIdentity = {"namespace": "", "name": "QWidget",
                         "source_location": {"file": "app/src/view/mainwindow.h"}}
    tracked = {os.path.abspath("/repo/app/src/view/mainwindow.cpp")}   # 픽스처는 .h 를 일부러 뺀다
    assert N.is_first_party(el, "/repo", tracked=tracked) is False


def test_first_party_accepts_tracked_global_namespace_type(tmp_path: Path) -> None:
    """git 이 추적하는 파일에서 정의된 전역 네임스페이스 타입은 1차다."""
    d = tmp_path / "app"
    d.mkdir()
    f = d / "mainwindow.h"
    f.write_text("#pragma once\nclass MainWindow : public QWidget\n{\n};\n", encoding="utf-8")
    el: N.UmlIdentity = {"namespace": "", "name": "MainWindow",
                         "source_location": {"file": "app/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path), tracked={str(f)}) is True
