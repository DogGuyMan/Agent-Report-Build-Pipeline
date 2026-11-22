#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트.

**`src/codewiki/python/machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다.

**`Any` 를 쓰지 않는다.** 바깥 프로그램이 꼴을 정하는 값은 `TypedDict` 로 선언하고
`msgspec` 이 검증한다. 안 맞으면 예외다 — 조용히 기본값으로 세지 않는다.
"""
import collections
import sys
import threading
import time
from collections.abc import Iterable, Sequence
from typing import NotRequired, TypedDict

import msgspec

class ClaudeUsage(TypedDict, total=False):
    """`claude -p --output-format json` 의 `usage`. 칸은 빠질 수 있고, 있으면 정수여야 한다."""
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


class ClaudeModelUsage(TypedDict, total=False):
    """`modelUsage` 의 Model 하나 — 세션이 그 Model 로 쓴 토큰의 누계. 칸은 빠질 수 있고, 있으면 정수여야 한다."""
    inputTokens: int
    outputTokens: int
    cacheReadInputTokens: int
    cacheCreationInputTokens: int


class ClaudeDenial(TypedDict, total=False):
    """허용 규칙 밖이라 CLI 가 막은 도구 호출 하나. 측정에는 개수만 쓴다."""
    tool_name: str
    tool_use_id: str
    tool_input: dict[str, object]


class ClaudeResult(TypedDict, total=False):
    """`claude -p --output-format json` 이 stdout 으로 내는 객체 하나.

    꼴을 정하는 것은 바깥 프로그램이라 칸은 전부 선택이고, 우리가 안 읽는 칸은 버린다.
    있는 칸의 형이 어긋나면 `msgspec.ValidationError` 다 — 조용히 0 으로 세지 않는다.
    """
    result: str
    usage: ClaudeUsage
    modelUsage: dict[str, ClaudeModelUsage]
    total_cost_usd: float
    num_turns: int
    duration_api_ms: int
    is_error: bool
    subtype: str
    permission_denials: list[ClaudeDenial]


# 옛 이름. 세 실행기와 시험이 이 이름으로 부른다.
AgentResult = ClaudeResult


def parse_result(text: str | bytes) -> ClaudeResult:
    """`claude` 의 stdout 을 형으로 읽는다. 깨졌으면 `DecodeError`, 꼴이 틀리면 `ValidationError`."""
    return msgspec.json.decode(text, type=ClaudeResult)

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


# ── 토큰 세기 ────────────────────────────────────────────────────────────


def normalize_usage(result: ClaudeResult | None) -> Usage:
    """`claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다.

    `total` 은 입력·출력·캐시읽기·캐시생성 넷을 더한 값이다. 캐시 둘을 빼고 "토큰 합" 이라
    부르면 일부만 센 것이다.

    `model_total` 은 `modelUsage` 의 Model 별 누계를 전부 더한 값이다. `usage` 는 호출 하나의 몫이라
    세션의 일부만 담아 올 수 있고, 이 값은 세션 전체다 — `usage_gap` 이 둘을 견준다.

    `denied` 는 CLI 가 막은 도구 호출의 수다(`permission_denials` 의 길이). 막힌 명령의 글은 싣지 않는다.

    기계 단계는 `None` 을 받아 전부 0 을 낸다 — `None` 을 그대로 두면 표를 더할 수 없다.
    """
    top: ClaudeResult = result or {}
    u = top.get("usage", {})
    got: Usage = {
        "input": u.get("input_tokens", 0),
        "output": u.get("output_tokens", 0),
        "cache_read": u.get("cache_read_input_tokens", 0),
        "cache_write": u.get("cache_creation_input_tokens", 0),
        "cost_usd": top.get("total_cost_usd", 0.0),
        "turns": top.get("num_turns", 0),
        "api_ms": top.get("duration_api_ms", 0),
        "denied": len(top.get("permission_denials", [])),
    }
    got["total"] = got["input"] + got["output"] + got["cache_read"] + got["cache_write"]
    got["model_total"] = sum(m.get("inputTokens", 0) + m.get("outputTokens", 0)
                             + m.get("cacheReadInputTokens", 0) + m.get("cacheCreationInputTokens", 0)
                             for m in top.get("modelUsage", {}).values())
    return got


def sum_usage(usages: Sequence[Usage]) -> Usage:
    """`normalize_usage` 가 낸 사전들을 열쇠별로 접는다. 표 맨 아래 '합계' 줄이 이것이다."""
    keys = ["input", "output", "cache_read", "cache_write", "total", "model_total", "turns", "api_ms", "denied"]
    # 정수 열쇠는 정수로 접고 `cost_usd` 만 실수로 따로 접는다.
    out: Usage = {k: sum(int(u.get(k) or 0) for u in usages) for k in keys}
    out["cost_usd"] = sum(float(u.get("cost_usd") or 0.0) for u in usages)
    return out


# `usage` 합계가 Model 별 누계보다 이 선을 넘게 작으면 덜 적힌 것으로 본다. 둘은 평소에도 보조 요청
# 몫만큼 다르므로 같은지로 견주면 모든 행이 걸린다 — `test_보조_요청_몫만큼의_차이는_덜_적힌_것이_아니다`.
USAGE_GAP_FLOOR = 20_000
USAGE_GAP_SHARE = 0.2


def usage_gap(usage: Usage) -> int:
    """`usage` 합계가 Model 별 누계보다 덜 적힌 토큰 수. 선을 넘지 않거나 누계가 없으면 0."""
    model_total = int(usage.get("model_total") or 0)
    gap = model_total - int(usage.get("total") or 0)
    return gap if gap > max(USAGE_GAP_FLOOR, USAGE_GAP_SHARE * model_total) else 0


# ── 실패 판정 ────────────────────────────────────────────────────────────


def result_text(result: ClaudeResult) -> str:
    """CLI 가 `result` 칸에 적은 글을 한 줄 · 200자까지로. 없으면 빈 글."""
    return " ".join(str(result.get("result") or "").split())[:200]


def agent_verdict(returncode: int, result: ClaudeResult | None) -> tuple[bool, str]:
    """에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다.

    종료 코드만 믿으면 안 된다. `claude` 는 최대 턴 수에 걸리거나 권한에 막혀도 0 을
    내면서 `is_error: true` 만 올릴 수 있다.

    실패면 CLI 가 `result` 칸에 적은 글을 사유 끝에 붙인다. `subtype` 만으로는 왜 실패했는지
    알 수 없는 실패가 있다 — `test_종료_코드가_0이_아니면_CLI_가_적은_글을_사유에_싣는다`.
    """
    if result is None:
        return False, "결과 JSON 을 읽지 못했다 (종료 코드 %d)" % returncode
    why = result.get("subtype") or "사유 없음"
    text = result_text(result)
    if text:
        why = "%s · %s" % (why, text)
    if returncode != 0:
        return False, "종료 코드 %d — %s" % (returncode, why)
    if result.get("is_error"):
        return False, "에이전트가 오류로 끝났다: %s" % why
    return True, ""


# ── 에이전트 호출 ────────────────────────────────────────────────────────


# 세션 인자의 기본값. 권한을 묻지 않고 모든 호출을 허용한다 — 단계가 `LlmStage.session_args` 를 재정의하지 않으면 이것이 실린다.
OPEN_SESSION: tuple[str, ...] = ("--permission-mode", "bypassPermissions")

# 세션이 시작할 때 싣는 것을 줄이는 인자 넷 — 내장 도구는 셋만 · 연결 서버 없음 · 스킬과 명령 없음 · 설정 파일 없음.
# 권한 인자 뒤에 이어 붙인다.
ISOLATED: tuple[str, ...] = ("--tools", "Bash,Read,Write", "--strict-mcp-config", "--disable-slash-commands",
                             "--setting-sources", "")


def claude_argv(model: str, repo: str, extra_dirs: Iterable[str],
                session_args: Sequence[str] = OPEN_SESSION) -> list[str]:
    """헤드리스 `claude` 명령줄. 프롬프트는 여기 싣지 않는다 — 표준 입력으로 준다.

    `session_args` 는 권한과 세션이 싣는 것을 정하는 인자다. 주지 않으면 `OPEN_SESSION` 이다.

    `--add-dir` 로 대상 저장소와 도구 저장소를 둘 다 열어 준다. 한쪽만 주면 에이전트가
    재료나 규약 중 하나를 못 본다.
    """
    argv = ["claude", "-p", "--output-format", "json", "--model", model, *session_args]
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
    for r in rows:
        gap = usage_gap(r["usage"])
        if gap:
            out.append("사용량 덜 적힘 — %s: 합계가 Model 별 누계보다 %s 토큰 작다"
                       % (r["stage"], "{:,}".format(gap)))
    for r in rows:
        denied = int(r["usage"].get("denied") or 0)
        if denied:
            out.append("거절된 호출 — %s: %d건" % (r["stage"], denied))
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
