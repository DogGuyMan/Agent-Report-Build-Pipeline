import os
import sys

import msgspec
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M  # noqa: E402


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


def test_망가진_값은_읽는_자리에서_거부된다():
    """옛 정책(조용히 0)을 뒤집었다 — 꼴이 틀린 결과는 `parse_result` 가 던지고 세션 행이 실패로 남는다."""
    with pytest.raises(msgspec.ValidationError):
        M.parse_result('{"usage": {"input_tokens": "많이"}, "num_turns": null}')


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
    argv = M.claude_argv("claude-sonnet-5-5", "/repo", ["/tool"])
    assert "-p" in argv and "--output-format" in argv
    assert argv[argv.index("--model") + 1] == "claude-sonnet-5-5"
    assert "--add-dir" in argv and "/repo" in argv and "/tool" in argv


def test_초를_사람이_읽는_꼴로():
    assert M.hms(9.25) == "9.2초"
    assert M.hms(61.5) == "1분 01.5초"


def _행(name: str, ok: bool = True, skipped: bool = False) -> M.StageRow:
    row: M.StageRow = {"stage": name, "seconds": 1.0,
                       "usage": M.normalize_usage(None), "ok": ok, "why": ""}
    if skipped:
        row["skipped"] = True
    return row


def test_표는_단계마다_한_줄과_합계를_낸다():
    out = M.format_report([_행("prep"), _행("check")])
    assert "prep" in out and "check" in out and "합계" in out


def test_벽시계를_주면_합계_시간이_그것이다():
    out = M.format_report([_행("a"), _행("b")], wall_seconds=1.0)
    assert "1.0초" in out


def test_건너뛴_단계는_실패가_아니다():
    out = M.format_report([_행("survey", skipped=True)])
    assert "건너뜀" in out and "실패" not in out


def test_배치_행을_단계_이름으로_접는다():
    rows = [_행("survey/L0-B00"), _행("survey/L0-B01"), _행("terms")]
    tot = M.stage_totals(rows)
    assert list(tot) == ["survey", "terms"]


def test_하트비트는_문맥_관리자다():
    with M.Heartbeat("시험", every=3600.0) as h:
        assert h.label == "시험"


# ── LLM 결과의 꼴 ────────────────────────────────────────────────────────


def test_결과_JSON_은_형으로_읽힌다():
    r = M.parse_result('{"result": "ok", "usage": {"input_tokens": 7}, "total_cost_usd": 1}')
    assert r.get("usage", {}).get("input_tokens") == 7
    assert r.get("total_cost_usd") == 1.0   # int → float 는 허용


def test_토큰_칸에_참거짓이나_문자열이_오면_거부한다():
    with pytest.raises(msgspec.ValidationError):
        M.parse_result('{"usage": {"input_tokens": true}}')
    with pytest.raises(msgspec.ValidationError):
        M.parse_result('{"usage": {"input_tokens": "7"}}')


def test_깨진_JSON_은_DecodeError_다():
    with pytest.raises(msgspec.DecodeError):
        M.parse_result("{ broken")


def test_없는_칸은_0으로_센다():
    u = M.normalize_usage(M.parse_result("{}"))
    assert u["input"] == 0 and u["cost_usd"] == 0.0 and u["total"] == 0
    assert M.normalize_usage(None)["turns"] == 0
