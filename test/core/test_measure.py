import json
import os
import sys

import msgspec
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from core import measure as M  # noqa: E402


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


def test_종료_코드가_0이_아니면_CLI_가_적은_글을_사유에_싣는다():
    ok, why = M.agent_verdict(1, {"subtype": "success", "is_error": True,
                                  "result": "You've hit your session limit · resets 9:50pm"})
    assert ok is False
    assert "종료 코드 1" in why and "session limit" in why


def test_사유에_싣는_글은_한_줄_200자까지다():
    _, why = M.agent_verdict(1, {"subtype": "success", "result": "첫 줄\n" + "가" * 500})
    assert "\n" not in why
    assert M.result_text({"result": "첫 줄\n" + "가" * 500}) == ("첫 줄 " + "가" * 500)[:200]


def test_CLI_가_글을_주지_않으면_사유는_subtype_뿐이다():
    assert M.agent_verdict(1, {"subtype": "error_max_turns"}) == (False, "종료 코드 1 — error_max_turns")


def test_성공한_세션의_글은_사유가_되지_않는다():
    assert M.agent_verdict(0, {"result": "샤드를 썼다", "subtype": "success"}) == (True, "")


def test_Model_별_누계를_model_total_로_적는다():
    """`usage` 는 호출 하나의 몫이고 `modelUsage` 는 세션의 누계다. 둘을 따로 적는다."""
    got = M.normalize_usage(M.parse_result(json.dumps({
        "usage": {"input_tokens": 4, "output_tokens": 207,
                  "cache_read_input_tokens": 109285, "cache_creation_input_tokens": 4709},
        "modelUsage": {
            "claude-sonnet-5-5": {"inputTokens": 30, "outputTokens": 11278, "cacheReadInputTokens": 1272778,
                                  "cacheCreationInputTokens": 89344, "costUSD": 0.598, "costBasis": "list"},
            "claude-haiku-5-5": {"inputTokens": 6787, "outputTokens": 25}},
        "total_cost_usd": 0.5981, "num_turns": 1})))
    assert got["total"] == 4 + 207 + 109285 + 4709
    assert got["model_total"] == 30 + 11278 + 1272778 + 89344 + 6787 + 25


def test_modelUsage_가_없으면_model_total_은_0이다():
    assert M.normalize_usage(M.parse_result('{"usage": {"input_tokens": 7}}'))["model_total"] == 0
    assert M.normalize_usage(None)["model_total"] == 0


def test_model_total_도_열쇠별로_접는다():
    a = M.normalize_usage({"modelUsage": {"m": {"inputTokens": 3}}})
    b = M.normalize_usage({"modelUsage": {"m": {"outputTokens": 4}}})
    assert M.sum_usage([a, b])["model_total"] == 7


def test_modelUsage_의_토큰_칸에_문자열이_오면_거부한다():
    with pytest.raises(msgspec.ValidationError):
        M.parse_result('{"modelUsage": {"m": {"inputTokens": "많이"}}}')


def _사용량(total: int, model_total: int) -> M.Usage:
    u = M.normalize_usage(None)
    u["total"], u["model_total"] = total, model_total
    return u


def test_보조_요청_몫만큼의_차이는_덜_적힌_것이_아니다():
    assert M.usage_gap(_사용량(94_873, 94_873 + 6_812)) == 0


def test_작은_세션의_보조_요청_몫도_걸리지_않는다():
    assert M.usage_gap(_사용량(10_000, 16_812)) == 0


def test_앞선_요청이_통째로_빠지면_덜_적힌_토큰_수를_낸다():
    assert M.usage_gap(_사용량(114_205, 1_373_430)) == 1_373_430 - 114_205


def test_누계가_없으면_견주지_않는다():
    assert M.usage_gap(_사용량(500_000, 0)) == 0


def test_덜_적힌_행은_표_아래에_알린다():
    row = _행("annotate-symbols/L1-B14")
    row["usage"] = _사용량(114_205, 1_373_430)
    out = M.format_report([row, _행("verify-terms")])
    assert "사용량 덜 적힘 — annotate-symbols/L1-B14" in out and "1,259,225" in out
    assert "사용량 덜 적힘 — verify-terms" not in out


# ── 세션 인자 — 권한과 세션이 싣는 것을 정하는 명령줄 조각 ────────────────────

def test_세션_인자를_주지_않으면_명령줄은_묻지_않고_전부_허용한다():
    assert M.OPEN_SESSION == ("--permission-mode", "bypassPermissions")
    assert M.claude_argv("m", "/repo", ["/tool"]) == [
        "claude", "-p", "--output-format", "json", "--model", "m",
        "--permission-mode", "bypassPermissions", "--add-dir", "/repo", "--add-dir", "/tool"]


def test_세션_인자는_Model_뒤_폴더_앞에_그대로_실린다():
    argv = M.claude_argv("m", "/repo", ["/tool"], M.OPEN_SESSION + M.ISOLATED)
    assert argv == ["claude", "-p", "--output-format", "json", "--model", "m",
                    "--permission-mode", "bypassPermissions",
                    "--tools", "Bash,Read,Write", "--strict-mcp-config", "--disable-slash-commands",
                    "--setting-sources", "",
                    "--add-dir", "/repo", "--add-dir", "/tool"]


def test_세션_인자를_바꾸면_권한_인자도_그_값으로_바뀐다():
    argv = M.claude_argv("m", "/repo", [], ("--permission-mode", "dontAsk"))
    assert argv.count("--permission-mode") == 1 and "bypassPermissions" not in argv


# ── 거절된 호출 — 허용 규칙 밖이라 CLI 가 막은 도구 호출 ─────────────────────

_거절_둘 = ('{"result": "ok", "permission_denials": ['
          '{"tool_name": "Bash", "tool_use_id": "t1", "tool_input": {"command": "for f in a b; do cat $f; done"}},'
          '{"tool_name": "Write", "tool_use_id": "t2", "tool_input": {"file_path": "/elsewhere/x.json", "content": "{}"}}]}')


def test_거절된_호출_수를_denied_로_적는다():
    assert M.normalize_usage(M.parse_result(_거절_둘))["denied"] == 2


def test_거절이_없거나_결과가_없으면_denied_는_0이다():
    assert M.normalize_usage(M.parse_result('{"result": "ok", "permission_denials": []}'))["denied"] == 0
    assert M.normalize_usage(M.parse_result('{"result": "ok"}'))["denied"] == 0
    assert M.normalize_usage(None)["denied"] == 0


def test_denied_도_열쇠별로_접는다():
    a, b = M.normalize_usage(M.parse_result(_거절_둘)), M.normalize_usage(M.parse_result(_거절_둘))
    assert M.sum_usage([a, b])["denied"] == 4


def test_측정값에는_거절된_호출의_수만_남고_명령_글은_남지_않는다():
    got = M.normalize_usage(M.parse_result(_거절_둘))
    assert all(isinstance(v, (int, float)) for v in got.values())


def test_거절된_호출이_있는_행은_보고_끝에_한_줄씩_남는다():
    rows: list[M.StageRow] = [
        {"stage": "annotate-symbols/L2-B00", "seconds": 51.7, "ok": True, "why": "",
         "usage": M.normalize_usage(M.parse_result(_거절_둘))},
        {"stage": "annotate-symbols/L2-B01", "seconds": 45.1, "ok": True, "why": "",
         "usage": M.normalize_usage(M.parse_result('{"result": "ok"}'))}]
    out = M.format_report(rows)
    assert "거절된 호출 — annotate-symbols/L2-B00: 2건" in out
    assert "거절된 호출 — annotate-symbols/L2-B01" not in out


def test_permission_denials_가_목록이_아니면_거부한다():
    with pytest.raises(msgspec.ValidationError):
        M.parse_result('{"permission_denials": "없음"}')
