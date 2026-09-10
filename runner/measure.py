#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트.

**`machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다.

**`Any` 를 쓰지 않는다.** 바깥 프로그램이 꼴을 정하는 값은 `object` 로 받고 아래
좁히기 도우미로 하나씩 확인한다.
"""
import collections
import sys
import threading
import time
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


def as_list(v: object) -> list[object]:
    """목록이면 원소를 `object` 로 본 사본을, 아니면 빈 목록을 낸다.

    `isinstance(v, list)` 하나로 좁히면 `list[Unknown]` 이 되어 원소를 쓰는 자리마다
    검사기가 걸린다. 원소 형까지 못 박아야 좁히기가 끝난다.
    """
    if not isinstance(v, list):
        return []
    return list(cast(list[object], v))


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


def format_report(rows: Sequence[StageRow], wall_seconds: float | None = None) -> str:
    """단계별 표 + 합계 줄. 실행기의 산출물 본체다.

    `wall_seconds` 를 주면 합계 줄의 시간이 그 값이 되고, 안 주면 행의 초를 더한다.
    층 안에서 배치가 동시에 돌면 행의 합이 사람이 기다린 시간보다 커지므로, 병렬로 도는
    쪽이 진짜 벽시계를 재서 넘긴다.
    """
    head = ["단계", "상태", "시간", "입력", "출력", "캐시읽기", "캐시생성", "합계", "턴", "비용($)"]
    body: list[list[str]] = []
    for r in rows:
        u = r["usage"]
        body.append([
            r["stage"],
            "건너뜀" if r.get("skipped") else ("성공" if r.get("ok") else "실패"),
            hms(r["seconds"]),
            "{:,}".format(u["input"]), "{:,}".format(u["output"]),
            "{:,}".format(u["cache_read"]), "{:,}".format(u["cache_write"]),
            "{:,}".format(u["total"]), str(u["turns"]), "%.4f" % u["cost_usd"],
        ])
    tot = sum_usage([r["usage"] for r in rows])
    total_seconds = (sum(float(r["seconds"]) for r in rows)
                     if wall_seconds is None else float(wall_seconds))
    body.append([
        "합계", "", hms(total_seconds),
        "{:,}".format(tot["input"]), "{:,}".format(tot["output"]),
        "{:,}".format(tot["cache_read"]), "{:,}".format(tot["cache_write"]),
        "{:,}".format(tot["total"]), str(tot["turns"]), "%.4f" % tot["cost_usd"],
    ])

    # 한글은 폭이 두 칸이라 len() 으로는 안 맞는다. 표시 폭을 따로 센다.
    def w(s: object) -> int:
        return sum(2 if ord(c) > 0x2E80 else 1 for c in str(s))
    cols = [max(w(head[i]), max(w(row[i]) for row in body)) for i in range(len(head))]

    def line(cells: Sequence[str]) -> str:
        return "  ".join(str(c) + " " * (cols[i] - w(c)) for i, c in enumerate(cells)).rstrip()

    out = [line(head), "  ".join("-" * c for c in cols)]
    out += [line(r) for r in body[:-1]]
    out += ["  ".join("-" * c for c in cols), line(body[-1])]
    for r in rows:
        if r.get("skipped"):
            out.append("건너뜀 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
        elif not r.get("ok"):
            out.append("실패 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
    return "\n".join(out)


def stage_totals(rows: Sequence[StageRow]) -> collections.OrderedDict[str, Usage]:
    """`survey/L0-B00` 같은 행을 `/` 앞까지로 접는다. `{단계: 합친 usage}`."""
    byname: collections.OrderedDict[str, list[Usage]] = collections.OrderedDict()
    for r in rows:
        name = r["stage"].split("/")[0]
        byname.setdefault(name, []).append(r["usage"])
    return collections.OrderedDict((k, sum_usage(v)) for k, v in byname.items())


# ── 오래 도는 단계 옆에서 경과를 알린다 ──────────────────────────────────


class Heartbeat:
    """오래 도는 단계 옆에서 경과 시간을 stderr 로 알린다.

    `--output-format json` 은 끝나야 한 덩이로 나오므로 그 사이 아무것도 찍히지 않는다.
    """

    def __init__(self, label: str, every: float = 30.0) -> None:
        self.label, self.every = label, every
        self._stop = threading.Event()
        self._t0 = time.monotonic()
        self._th = threading.Thread(target=self._tick, daemon=True)

    def _tick(self) -> None:
        while not self._stop.wait(self.every):
            print("    … %s 진행 중 (%s)" % (self.label, hms(time.monotonic() - self._t0)),
                  file=sys.stderr, flush=True)

    def __enter__(self) -> "Heartbeat":
        self._th.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
