import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M  # noqa: E402


def test_문자열_열쇠_사전만_통과시킨다():
    assert M.as_map({"a": 1}) == {"a": 1}
    assert M.as_map([1, 2]) == {}
    assert M.as_map(None) == {}


def test_정수가_아니면_0이다():
    assert M.as_int(5) == 5
    assert M.as_int("5") == 0
    assert M.as_int(True) == 0
    assert M.as_int(None) == 0


def test_수가_아니면_0점0이다():
    assert M.as_float(1.5) == 1.5
    assert M.as_float(2) == 2.0
    assert M.as_float(True) == 0.0
    assert M.as_float("x") == 0.0


def test_문자열이_아니면_빈_문자열이다():
    assert M.as_str("ok") == "ok"
    assert M.as_str(3) == ""
    assert M.as_str(None) == ""
