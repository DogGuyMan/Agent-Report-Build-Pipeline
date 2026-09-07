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


def test_토큰_합계는_캐시_둘을_포함한다():
    got = M.normalize_usage({
        "usage": {"input_tokens": 10, "output_tokens": 20,
                  "cache_read_input_tokens": 30, "cache_creation_input_tokens": 40},
        "total_cost_usd": 1.5, "num_turns": 3, "duration_api_ms": 900,
    })
    assert got["total"] == 100
    assert got["cost_usd"] == 1.5
    assert got["turns"] == 3


def test_결과가_없으면_전부_0이다():
    got = M.normalize_usage(None)
    assert got["total"] == 0 and got["cost_usd"] == 0.0


def test_망가진_값은_예외가_아니라_0이다():
    got = M.normalize_usage({"usage": {"input_tokens": "많이"}, "num_turns": None})
    assert got["input"] == 0 and got["turns"] == 0


def test_사용량을_열쇠별로_접는다():
    a = M.normalize_usage({"usage": {"input_tokens": 1}, "total_cost_usd": 0.5})
    b = M.normalize_usage({"usage": {"input_tokens": 2}, "total_cost_usd": 0.25})
    assert M.sum_usage([a, b])["input"] == 3
    assert M.sum_usage([a, b])["cost_usd"] == 0.75


def test_종료_코드가_0이어도_is_error_면_실패다():
    ok, why = M.agent_verdict(0, {"is_error": True, "subtype": "max_turns"})
    assert ok is False and "max_turns" in why


def test_결과_JSON_이_없으면_실패다():
    ok, _ = M.agent_verdict(0, None)
    assert ok is False


def test_정상이면_성공이다():
    assert M.agent_verdict(0, {"result": "됐다"}) == (True, "")


def test_명령줄에_프롬프트를_싣지_않는다():
    argv = M.claude_argv("claude-sonnet-5", "/repo", ["/tool"])
    assert "-p" in argv and "--output-format" in argv
    assert argv[argv.index("--model") + 1] == "claude-sonnet-5"
    assert "--add-dir" in argv and "/repo" in argv and "/tool" in argv


def test_초를_사람이_읽는_꼴로():
    assert M.hms(9.25) == "9.2초"
    assert M.hms(61.5) == "1분 01.5초"
