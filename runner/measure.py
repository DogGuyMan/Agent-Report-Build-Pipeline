#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트.

**`machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다.

**`Any` 를 쓰지 않는다.** 바깥 프로그램이 꼴을 정하는 값은 `object` 로 받고 아래
좁히기 도우미로 하나씩 확인한다.
"""
from collections.abc import Iterable, Sequence
from typing import NotRequired, TypedDict, cast

# `claude -p --output-format json` 이 stdout 으로 내는 객체 하나. 꼴을 정하는 것은 바깥
# 프로그램이라 칸을 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
AgentResult = dict[str, object]

# 잰 값 한 묶음. 정수 여섯에 실수 하나(`cost_usd`)가 섞인 의도된 이종 사전이다.
# 값 타입을 `float` 으로 적는 것은 파이썬에서 정수가 실수의 부분형이라 둘 다 담기기 때문이다.
Usage = dict[str, float]


class StageRow(TypedDict):
    """측정 표의 한 줄. 세 실행기가 모두 이 꼴로 쌓고 `format_report` 가 읽는다.

    `skipped` 만 선택 항목이다 — 건너뛴 단계에만 붙는다.
    """

    stage: str
    seconds: float
    usage: Usage
    ok: bool
    why: str
    skipped: NotRequired[bool]


# ── 좁히기 도우미. `object` 를 쓸 수 있는 형으로 바꾸는 자리는 여기뿐이다 ──


def as_map(v: object) -> dict[str, object]:
    """열쇠가 문자열인 사전이면 그것을, 아니면 빈 사전을 낸다."""
    if not isinstance(v, dict):
        return {}
    items = cast(dict[object, object], v).items()
    return {k: x for k, x in items if isinstance(k, str)}


def as_int(v: object) -> int:
    """정수면 그것을, 아니면 0. `bool` 은 정수가 아니다 — 참/거짓이 수로 세어지면 안 된다."""
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


def as_float(v: object) -> float:
    """정수나 실수면 실수로, 아니면 0.0. `bool` 은 제외한다."""
    if isinstance(v, bool):
        return 0.0
    return float(v) if isinstance(v, (int, float)) else 0.0


def as_str(v: object) -> str:
    """문자열이면 그것을, 아니면 빈 문자열."""
    return v if isinstance(v, str) else ""


# ── 토큰 세기 ────────────────────────────────────────────────────────────


def normalize_usage(result: AgentResult | None) -> Usage:
    """`claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다.

    `total` 은 입력·출력·캐시읽기·캐시생성 넷을 더한 값이다. 캐시 둘을 빼고 "토큰 합" 이라
    부르면 일부만 센 것이다.

    기계 단계는 `None` 을 받아 전부 0 을 낸다 — `None` 을 그대로 두면 표를 더할 수 없다.
    """
    top = as_map(result)
    u = as_map(top.get("usage"))
    got: Usage = {
        "input": as_int(u.get("input_tokens")),
        "output": as_int(u.get("output_tokens")),
        "cache_read": as_int(u.get("cache_read_input_tokens")),
        "cache_write": as_int(u.get("cache_creation_input_tokens")),
        "cost_usd": as_float(top.get("total_cost_usd")),
        "turns": as_int(top.get("num_turns")),
        "api_ms": as_int(top.get("duration_api_ms")),
    }
    got["total"] = got["input"] + got["output"] + got["cache_read"] + got["cache_write"]
    return got


def sum_usage(usages: Sequence[Usage]) -> Usage:
    """`normalize_usage` 가 낸 사전들을 열쇠별로 접는다. 표 맨 아래 '합계' 줄이 이것이다."""
    keys = ["input", "output", "cache_read", "cache_write", "total", "turns", "api_ms"]
    # 정수 여섯은 정수로 접고 `cost_usd` 만 실수로 따로 접는다.
    out: Usage = {k: sum(int(u.get(k) or 0) for u in usages) for k in keys}
    out["cost_usd"] = sum(float(u.get("cost_usd") or 0.0) for u in usages)
    return out


# ── 실패 판정 ────────────────────────────────────────────────────────────


def agent_verdict(returncode: int, result: AgentResult | None) -> tuple[bool, str]:
    """에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다.

    종료 코드만 믿으면 안 된다. `claude` 는 최대 턴 수에 걸리거나 권한에 막혀도 0 을
    내면서 `is_error: true` 만 올릴 수 있다.
    """
    if result is None:
        return False, "결과 JSON 을 읽지 못했다 (종료 코드 %d)" % returncode
    top = as_map(result)
    why = as_str(top.get("subtype")) or "사유 없음"
    if returncode != 0:
        return False, "종료 코드 %d — %s" % (returncode, why)
    if top.get("is_error"):
        return False, "에이전트가 오류로 끝났다: %s" % why
    return True, ""


# ── 에이전트 호출 ────────────────────────────────────────────────────────


def claude_argv(model: str, repo: str, extra_dirs: Iterable[str]) -> list[str]:
    """헤드리스 `claude` 명령줄. 프롬프트는 여기 싣지 않는다 — 표준 입력으로 준다.

    `--add-dir` 로 대상 저장소와 도구 저장소를 둘 다 열어 준다. 한쪽만 주면 에이전트가
    재료나 규약 중 하나를 못 본다.
    """
    argv = ["claude", "-p", "--output-format", "json", "--model", model,
            "--permission-mode", "bypassPermissions"]
    for d in [repo] + list(extra_dirs):
        argv += ["--add-dir", d]
    return argv


# ── 보고 ─────────────────────────────────────────────────────────────────


def hms(seconds: float) -> str:
    """초를 사람이 읽는 꼴로. 재는 것이 목적이라 소수 첫째 자리까지 남긴다."""
    s = float(seconds)
    if s < 60:
        return "%.1f초" % s
    return "%d분 %04.1f초" % (int(s // 60), s % 60)
