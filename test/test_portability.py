import pytest
import os
from pathlib import Path
from tools.python import pythonCandidates, pythonPath
from tools.doctor import line, meets, requirement_names, version_of

def test_pythonCandidates_prefers_env():
    c = pythonCandidates("/r", "darwin", {"REPORT_PYTHON": "/opt/py"})
    assert c[0] == "/opt/py"

def test_pythonCandidates_posix_venv():
    c = pythonCandidates("/r", "linux", {})
    assert c[:2] == [os.path.join("/r", ".venv/bin/python3"), os.path.join("/r", ".venv/bin/python")]

def test_pythonCandidates_win32_venv():
    c = pythonCandidates("/r", "win32", {})
    assert c[:2] == [os.path.join("/r", ".venv/Scripts/python.exe"), os.path.join("/r", ".venv/Scripts/python")]

def test_pythonCandidates_fallback():
    c = pythonCandidates("/r", "linux", {})
    assert c[-2:] == ["python3", "python"]

def test_pythonPath_skips_missing_venv():
    assert pythonPath("/절대로/없는/저장소", "linux", {}) == "python3"

def test_line():
    assert "없음" in line("dot", None, True)
    assert "선택" in line("dot", None, False)
    assert "OK" in line("dot", "graphviz 15", True)

def test_line_은_하한보다_낮은_판을_낮음으로_적는다():
    assert "낮음" in line("dot", "dot - graphviz version 2.43.0 (0)", True, (10, 0, 1))
    assert "OK" in line("dot", "dot - graphviz version 15.1.1 (20260805.0921)", True, (10, 0, 1))

def test_version_of_는_도구가_찍는_판_글을_읽는다():
    assert version_of("dot - graphviz version 2.43.0 (0)") == (2, 43, 0)
    assert version_of("dot - graphviz version 15.1.1 (20260805.0921)") == (15, 1, 1)
    assert version_of("v25.8.0") == (25, 8, 0)
    assert version_of("Python 3.14.6") == (3, 14, 6)
    assert version_of(">=22.13.0") == (22, 13, 0)
    assert version_of("판 없음") is None

def test_meets_는_없는_것을_통과시키지_않는다():
    assert not meets(None, None)
    assert meets("git version 2.53.0", None)
    assert not meets("Python 3.11.9", (3, 12))
    assert meets("Python 3.12.0", (3, 12))

def test_requirement_names_는_주석과_판_조건을_뗀다(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text(
        "# 머리 주석\nnumpy==2.5.2   # 꼬리 주석\n\npytest>=9\nmsgspec\n", encoding="utf-8")
    assert requirement_names(str(tmp_path)) == ["numpy", "pytest", "msgspec"]

def test_requirement_names_는_이_저장소의_목록을_읽는다():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert "griffe" in requirement_names(root)
