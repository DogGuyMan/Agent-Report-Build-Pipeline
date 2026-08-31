import pytest
import os
from tools.python import pythonCandidates, pythonPath
from tools.doctor import line

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
