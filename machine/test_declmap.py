"""declmap.py 회귀. 정규식이 문법을 이해하지 못하므로 경계를 시험으로 못박는다.

  python -m pytest machine/test_declmap.py -q         # .venv 를 켠 뒤
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap as D  # noqa: E402


def _doc(lines, i, lang):
    return D.doc_above(lines, i, D.LANGS[lang])


# ── 1. 선언을 잡는가
def test_cs_decl_catches_modifiers_and_generics():
    m = D.LANGS["cs"]["decl"].match("    public static partial class Factory")
    assert m and m.group(1) == "class" and m.group(2).strip() == "Factory"


def test_cs_decl_catches_interface_with_constraint():
    m = D.LANGS["cs"]["decl"].match("public interface IStatableUI<T> where T : Enum")
    assert m and m.group(1) == "interface"


def test_cpp_decl_catches_enum_class():
    m = D.LANGS["cpp"]["decl"].match("\tenum class E_MOTION_MODEL : uint")
    assert m and m.group(1) == "enum class" and m.group(2) == "E_MOTION_MODEL"


def test_py_decl_catches_def_and_class():
    assert D.LANGS["py"]["decl"].match("def build_terms(x):").group(2) == "build_terms"
    assert D.LANGS["py"]["decl"].match("class Fact:").group(2) == "Fact"


def test_ts_decl_catches_export_function():
    m = D.LANGS["ts"]["decl"].match("export function wikiPaths(repo) {")
    assert m and m.group(1) == "function" and m.group(2) == "wikiPaths"


# ── 2. 문서 주석을 벗기는가
def test_cs_doc_strips_slashes_and_xml_tags():
    lines = ["/// <summary>", "/// 싱글톤", "/// </summary>", "public class Singleton"]
    assert _doc(lines, 3, "cs") == "싱글톤"


def test_cs_doc_skips_attribute_between_comment_and_decl():
    lines = ["/// 음식 데이터", "[System.Serializable]", "public struct SerialDataFood"]
    assert _doc(lines, 2, "cs") == "음식 데이터"


def test_cpp_doc_strips_comment_marker():
    lines = ["// 한 겹을 세 겹으로 편다", "cv::Mat3f BroadcastChannels("]
    assert _doc(lines, 1, "cpp") == "한 겹을 세 겹으로 편다"


def test_doc_stops_at_code():
    """주석이 아닌 코드 줄을 만나면 멈춘다 — 위쪽 딴 함수의 주석을 끌어오지 않는다."""
    lines = ["// 딴 함수 주석", "int other() { return 0; }", "", "void target()"]
    assert _doc(lines, 3, "cpp") == ""


def test_doc_has_a_ceiling():
    """아무리 긴 주석 더미라도 정해진 줄 수까지만 거슬러 올라간다."""
    lines = ["// 줄%d" % i for i in range(40)] + ["void target()"]
    got = _doc(lines, len(lines) - 1, "cpp")
    assert got and len(got.split()) <= D.DOC_MAX_LINES


# ── 3. 파일 거르기
def test_skip_dirs_covers_build_and_cache():
    for d in ("node_modules", "__pycache__", "vcpkg_installed", "out"):
        assert d in D.SKIP_DIRS


# ── 4. 1차 판정의 git 추적 거름망 (normalize.py, 2026-08-29)
import normalize as N  # noqa: E402


def test_first_party_rejects_qt_type_seen_inside_repo():
    """F-1 의 Qt 판. clang-uml 은 QWidget 의 위치로도 이 저장소의 첫 사용 지점을 준다.
    git 이 추적하지 않는 파일이므로 1차가 아니다."""
    el = {"namespace": "", "name": "QWidget",
          "source_location": {"file": "app/src/view/mainwindow.h"}}
    tracked = {os.path.abspath("/repo/app/src/view/mainwindow.cpp")}   # .h 는 없다
    assert N.is_first_party(el, "/repo", tracked=tracked) is False


def test_first_party_accepts_tracked_global_namespace_type(tmp_path):
    d = tmp_path / "app"
    d.mkdir()
    f = d / "mainwindow.h"
    f.write_text("#pragma once\nclass MainWindow : public QWidget\n{\n};\n", encoding="utf-8")
    el = {"namespace": "", "name": "MainWindow",
          "source_location": {"file": "app/mainwindow.h", "line": 2}}
    assert N.is_first_party(el, str(tmp_path), tracked={str(f)}) is True
