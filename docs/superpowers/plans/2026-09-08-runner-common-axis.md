# 러너 공통축 추출 (1단계) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 세 실행기가 공유하는 재는 코드를 `runner/measure.py` 로 뽑아, `run_mode1_5.py` 와 `run_mode2.py` 가 `run_mode1.py` 를 import 하면서 겪는 해석기 재실행·networkx 적재 부작용을 없앤다.

**Architecture:** `runner/measure.py` 는 `machine/` 을 import 하지 않는 순수 모듈이다. 형(`Usage` · `StageRow` · `AgentResult`)과 순수 함수(`hms` · `normalize_usage` · `sum_usage` · `agent_verdict` · `claude_argv` · `format_report` · `stage_totals`)와 `Heartbeat` 만 담는다. `run_mode1.py` 는 옛 이름을 그대로 재수출하는 파사드로 남아 시험 네 파일을 한 줄도 고치지 않는다.

**Tech Stack:** Python 3.14 · pytest · pyright strict

**사양:** `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` 의 D5 · D8 · D10 · D11

---

## 이 계획이 다루는 범위

**이 계획은 3단계 중 1단계다.** 2·3단계는 1단계가 끝난 뒤에 쓴다 — 그 계획의 코드가 여기서 나온 API 모양에 달려 있어서, 지금 쓰면 추측이 된다.

| 단계 | 무엇 | 상태 |
|---|---|---|
| **1 (이 문서)** | `measure.py` 추출 · 파사드 · import 부작용 해소 · `Any` 게이트 | 착수 |
| 2 | `pipeline.py`(Outcome · Stage · Edges · StageDagGraph · 시뮬레이터) 신설, Mode 2 와 Mode 1.5 를 그 위로 이주 | 1단계 뒤 |
| 3 | Mode 1 을 `mode1/` 패키지로 분해, 증분·전량 그래프 분리 | 2단계 뒤 |

**동작을 바꾸지 않는다.** 세 실행기의 화면 출력과 종료 코드가 그대로여야 한다.

## 가드레일

- **커밋은 각 Task 끝에서 한다.** 메시지는 `personal-commit-messages` 규약 — 소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음.
- **`git add -A` 금지.** 워킹 트리에 다른 작업의 미커밋분이 있다: `machine/terms-reading.json` · `machine/test_survey_plan.py` · `runner/README.md` · `runner/run_mode1.py` · `runner/test_run_mode1.py` · `runner/wiki/{build,check,prep}.py` · `test/test_wiki.py`. **경로를 좁혀 add 한다.**
- **`runner/run_mode1.py` 는 이미 미커밋 변경이 있다**(주석의 `모형`→`Model` 이름 바꾸기). 그 변경을 되돌리지 말고 그 위에 얹는다.
- **`# <include …/>` 블록은 손대지 않는다.** `machine/xmldoc.py` 가 주입한다. 새 함수를 만들어도 이 계획에서는 주입을 돌리지 않는다 — `check` 가 94건에서 늘어나는 것은 예상된 결과이고, 재주입은 별개 작업이다.
- **코드 주석에는 현 상황만 적는다.** 날짜 · 측정 수치 · 확신도 표기 · 설계 철학 서사를 코드에 남기지 않는다.
- 주석과 문서는 **한국어**. 약어를 피한다.

## File Structure

| 파일 | 책임 |
|---|---|
| `runner/measure.py` (신설) | 형 셋 + 좁히기 도우미 + 재는 순수 함수 일곱 + `Heartbeat`. **`machine/` 을 import 하지 않는다** |
| `runner/test_measure.py` (신설) | 위의 시험 |
| `test/test_no_any.py` (신설) | 형 자리의 `Any` 를 0으로 막는 게이트. 단계마다 대상 파일이 는다 |
| `runner/run_mode1.py` (수정) | 옮긴 이름들을 `measure` 에서 재수출. 나머지는 그대로 |
| `runner/run_mode1_5.py` (수정) | `import run_mode1 as M` → `import measure as M` |
| `runner/run_mode2.py` (수정) | 같음 |
| `runner/test_import_isolation.py` (신설) | Mode 2·1.5 import 가 `.venv` 재실행과 networkx 적재를 부르지 않는지 |

---

### Task 1: `runner/measure.py` — 형과 좁히기 도우미

`Any` 를 쓰지 않는다. `pyright strict` 가 `object` 를 좁히지 않고 쓰면 잡는다.

**Files:**
- Create: `runner/measure.py`
- Create: `runner/test_measure.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`runner/test_measure.py` 를 만든다:

```python
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
```

`as_int(True)` 가 0인 것은 의도다 — 파이썬에서 `bool` 은 `int` 의 부분형이라 걸러 내지 않으면 참/거짓이 토큰 수로 세어진다.

- [ ] **Step 2: 시험이 실패하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'measure'`

- [ ] **Step 3: 최소 구현**

`runner/measure.py` 를 만든다:

```python
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
```

- [ ] **Step 4: 시험이 통과하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: PASS — 4 passed

- [ ] **Step 5: 형 검사**

Run: `.venv/bin/python -m pyright runner/measure.py` (또는 `npm run typecheck:py`)
Expected: `0 errors`

- [ ] **Step 6: 커밋**

```bash
git add runner/measure.py runner/test_measure.py
git commit -m "[add] : 러너 공통 재는 코드의 형과 좁히기 도우미"
```

---

### Task 2: 재는 순수 함수 다섯을 옮긴다

**Files:**
- Modify: `runner/measure.py`
- Modify: `runner/test_measure.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`runner/test_measure.py` 끝에 붙인다:

```python
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
    ok, why = M.agent_verdict(0, None)
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
```

`test_망가진_값은_예외가_아니라_0이다` 는 **의도한 차이**다. 옛 코드는 `int("많이")` 로 `ValueError` 를 던졌다. 좁히기를 쓰면 0이 된다. 정상 입력에서는 동작이 같다.

- [ ] **Step 2: 시험이 실패하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: FAIL — `AttributeError: module 'measure' has no attribute 'normalize_usage'`

- [ ] **Step 3: 구현**

`runner/measure.py` 의 좁히기 도우미 아래에 붙인다:

```python
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
```

- [ ] **Step 4: 시험이 통과하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: PASS — 13 passed

- [ ] **Step 5: 커밋**

```bash
git add runner/measure.py runner/test_measure.py
git commit -m "[add] : 토큰 세기와 실패 판정을 공통축으로"
```

---

### Task 3: 표 그리기와 하트비트를 옮긴다

**Files:**
- Modify: `runner/measure.py`
- Modify: `runner/test_measure.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`runner/test_measure.py` 끝에 붙인다:

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: FAIL — `AttributeError: module 'measure' has no attribute 'format_report'`

- [ ] **Step 3: 구현**

`runner/measure.py` 의 `hms` 아래에 붙인다. **본문은 `runner/run_mode1.py` 의 것을 그대로 옮긴다** — 옮기면서 고치지 않는다:

```python
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
```

- [ ] **Step 4: 시험이 통과하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_measure.py -q`
Expected: PASS — 18 passed

- [ ] **Step 5: 형 검사**

Run: `npm run typecheck:py`
Expected: `0 errors`

- [ ] **Step 6: 커밋**

```bash
git add runner/measure.py runner/test_measure.py
git commit -m "[add] : 측정 표와 하트비트를 공통축으로"
```

---

### Task 4: `run_mode1.py` 를 파사드로 바꾼다

시험 네 파일이 `R.normalize_usage` 처럼 최상위 이름을 약 200회 참조한다. 재수출하면 그 파일들을 한 줄도 고치지 않는다.

**Files:**
- Modify: `runner/run_mode1.py`

- [ ] **Step 1: 기존 시험이 지금 통과하는지 먼저 확인한다 (기준선)**

Run: `.venv/bin/python -m pytest runner/test_run_mode1.py -q`
Expected: PASS. 통과 개수를 적어 둔다 — Step 4 에서 같아야 한다.

- [ ] **Step 2: 옮긴 정의를 지우고 재수출로 바꾼다**

`runner/run_mode1.py` 에서 아래 정의를 **지운다**:
`AgentResult` · `Usage` · `StageRow` · `normalize_usage` · `sum_usage` · `agent_verdict` · `claude_argv` · `hms` · `format_report` · `stage_totals` · `Heartbeat`
(각 정의 바로 위의 `# <include …/>` 세 줄 블록도 함께 지운다 — 정의가 없어졌으므로 남으면 `check` 가 어긋난다.)

`import declmap` 줄들 **아래**에 재수출을 넣는다:

```python
# 재는 코드의 원본은 `runner/measure.py` 하나다. 여기에 사본이 없다.
# 옛 이름으로 부르는 곳이 있어 그대로 다시 내보낸다.
import measure  # noqa: E402
from measure import (  # noqa: E402,F401
    AgentResult, Usage, StageRow, Heartbeat,
    normalize_usage, sum_usage, agent_verdict, claude_argv,
    hms, format_report, stage_totals,
)
```

`Record` 와 `Records` 는 Mode 1 만 쓰므로 **옮기지 않는다.** 다만 `Any` 를 없앤다:

```python
# 레코드의 칸은 배치 세션이 채우므로 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
Record = dict[str, object]
Records = dict[str, Record]
```

`from typing import Any, NotRequired, TypedDict, cast` 에서 더 이상 쓰지 않는 이름을 뺀다.

- [ ] **Step 3: 좁히기가 필요해진 한 자리를 고친다**

`Record` 의 값이 `object` 가 되면 `_qualified` 의 `where.split(...)` 이 형 오류가 난다
(`object` 에는 `.split` 이 없다). `runner/run_mode1.py` 의 `_qualified` 를 이렇게 바꾼다:

```python
def _qualified(key: str, rec: Record | None) -> str:
    """`<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다."""
    where = measure.as_str((rec or {}).get("where"))
    stem = os.path.splitext(os.path.basename(where.split(":")[0]))[0]
    return "%s.%s" % (stem, key) if stem else key
```

옛 코드는 `(rec or {}).get("where") or ""` 였다. `as_str` 이 같은 일을 하면서 문자열이
아닌 값도 빈 문자열로 만든다 — `where` 가 숫자로 들어오면 옛 코드는 `.split` 에서 터졌다.

`merge_shards` 는 고칠 것이 없다. `Records = dict[str, Record]` 이므로 `shard.items()` 의
`rec` 이 `Record` 로 잡히고 `_qualified` 에 그대로 들어간다.

**다른 오류가 나오면 형만 맞춘다.** 새 동작을 넣지 않는다.

- [ ] **Step 4: 기존 시험이 그대로 통과하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_run_mode1.py runner/test_measure.py -q`
Expected: PASS — Step 1 의 개수 + 18

- [ ] **Step 5: 형 검사**

Run: `npm run typecheck:py`
Expected: `0 errors`

- [ ] **Step 6: 커밋**

```bash
git add runner/run_mode1.py
git commit -m "[refactor] : run_mode1 을 재는 코드의 파사드로"
```

---

### Task 5: Mode 2 와 Mode 1.5 의 import 부작용을 없앤다

**Files:**
- Create: `runner/test_import_isolation.py`
- Modify: `runner/run_mode1_5.py`
- Modify: `runner/run_mode2.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`runner/test_import_isolation.py` 를 만든다:

```python
"""Mode 2 와 Mode 1.5 를 import 하는 것만으로 해석기가 바뀌거나 networkx 가 실리면 안 된다.

자식 프로세스로 재는 이유는 이 시험 프로세스에 이미 networkx 가 실려 있을 수 있어서다.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = """
import sys, os, json
sys.path.insert(0, os.path.join({root!r}, "runner"))
import {mod}
print(json.dumps({{"prefix": sys.prefix, "networkx": "networkx" in sys.modules}}))
"""


def _probe(mod: str) -> dict[str, object]:
    r = subprocess.run([sys.executable, "-c", PROBE.format(root=ROOT, mod=mod)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    import json
    return json.loads(r.stdout.strip().split("\\n")[-1])


def test_mode2_는_networkx_를_끌어오지_않는다():
    assert _probe("run_mode2")["networkx"] is False


def test_mode1_5_는_networkx_를_끌어오지_않는다():
    assert _probe("run_mode1_5")["networkx"] is False


def test_mode2_import_는_해석기를_바꾸지_않는다():
    assert _probe("run_mode2")["prefix"] == sys.prefix
```

- [ ] **Step 2: 시험이 실패하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_import_isolation.py -q`
Expected: FAIL — `networkx` 가 `True` 다 (세 시험 중 둘 이상 실패)

- [ ] **Step 3: 구현**

`runner/run_mode2.py` 에서:

```python
import run_mode1 as M  # noqa: E402
```
를
```python
import measure as M  # noqa: E402
```
로 바꾼다. 아래의 `normalize_usage = M.normalize_usage` 같은 별칭 줄은 그대로 둔다.

`runner/run_mode1_5.py` 에서 같은 줄을 같은 방식으로 바꾸고, 그 위의
`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 는 그대로 둔다.

`run_mode1_5.py` 의 `run_machine` 이 쓰는 `M.Heartbeat` 와 `format_run` 이 쓰는
`M.StageRow` · `M.format_report` 는 이름이 같아 그대로 동작한다.

- [ ] **Step 4: 시험이 통과하는지 본다**

Run: `.venv/bin/python -m pytest runner/test_import_isolation.py -q`
Expected: PASS — 3 passed

- [ ] **Step 5: 세 실행기의 `--dry-run` 이 그대로인지 본다**

Run:
```bash
.venv/bin/python runner/run_mode2.py docs/superpowers . --dry-run 2>&1 | tail -5
```
Expected: 에러 없이 단계 목록이 나온다 (`specs/` 가 있는 폴더라 통과한다).

- [ ] **Step 6: 커밋**

```bash
git add runner/run_mode2.py runner/run_mode1_5.py runner/test_import_isolation.py
git commit -m "[fix] : mode 2 와 1.5 가 재는 코드만 가져오도록"
```

---

### Task 6: `Any` 금지 게이트

`pyright strict` 는 명시적 `Any` 를 잡지 못한다. grep 게이트로 막는다.

**Files:**
- Create: `test/test_no_any.py`

- [ ] **Step 1: 시험을 쓴다 (지금 통과해야 한다)**

`test/test_no_any.py` 를 만든다:

```python
"""형 자리의 `Any` 를 0으로 막는 게이트.

`pyright` 의 strict 모드는 `Unknown` 의 전파는 잡지만 저자가 손으로 적은 `Any` 는
그냥 통과시킨다. 그래서 글자로 막는다.

`COVERED` 는 단계마다 는다. 아직 안 옮긴 파일을 여기 넣으면 게이트가 빨개진다.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# `Any` 를 0으로 지켜야 하는 파일. 리팩터링이 진행되면 여기에 줄이 는다.
COVERED = [
    "runner/measure.py",
]

# 낱말 경계로 본다 — `Anything` 같은 이름을 잘못 잡지 않는다.
ANY = re.compile(r"\bAny\b")


def _code_lines(path: str) -> list[tuple[int, str]]:
    """주석과 독스트링 줄을 뺀 나머지. 글자 검사라 완벽하지 않고 그럴 필요도 없다."""
    out: list[tuple[int, str]] = []
    in_doc = False
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.count('"""') % 2 == 1:
                in_doc = not in_doc
                continue
            if in_doc or stripped.startswith("#"):
                continue
            out.append((i, line))
    return out


def test_공통축에_Any_가_없다():
    hits: list[str] = []
    for path in COVERED:
        for lineno, line in _code_lines(path):
            if ANY.search(line):
                hits.append("%s:%d %s" % (path, lineno, line.strip()))
    assert hits == [], "형 자리에 Any 가 남았다:\n" + "\n".join(hits)


def test_덮는_파일이_실제로_있다():
    for path in COVERED:
        assert os.path.exists(os.path.join(ROOT, path)), path
```

- [ ] **Step 2: 시험을 돌린다**

Run: `.venv/bin/python -m pytest test/test_no_any.py -q`
Expected: PASS — 2 passed

- [ ] **Step 3: 게이트가 실제로 잡는지 확인한다**

`runner/measure.py` 맨 아래에 임시로 `_시험용: object = None  # type: Any` 가 아니라
진짜 형 자리에 넣어 본다: `def _버릴것(x: "Any") -> None: ...` 를 넣고 시험을 돌린다.

Run: `.venv/bin/python -m pytest test/test_no_any.py -q`
Expected: FAIL — "형 자리에 Any 가 남았다"

**넣었던 줄을 지운다.** 다시 돌려 PASS 인지 확인한다.

- [ ] **Step 4: 커밋**

```bash
git add test/test_no_any.py
git commit -m "[add] : 형 자리의 Any 를 막는 게이트"
```

---

### Task 7: 게이트 전체를 돌리고 문서를 맞춘다

**Files:**
- Modify: `runner/README.md` (자동 생성)
- Modify: `runner/CLAUDE.md`

- [ ] **Step 1: 게이트 일곱을 전부 돌린다**

```bash
.venv/bin/python -m pytest -q
npm test
npm run typecheck
npm run typecheck:py
.venv/bin/python machine/xmldoc.py check ; echo "종료 코드 $?"
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
npm run doctor
```

Expected:

| 게이트 | 기대 |
|---|---|
| `pytest` | **483 + 새 시험 개수** 통과 · 19 건너뜀. 483 보다 줄면 회귀다 |
| `npm test` | 8 통과 |
| `typecheck` | 통과 |
| `typecheck:py` | `0 errors` |
| `xmldoc check` | 종료 코드 1. **문제가 94건보다 는다** — 아래 설명을 읽을 것 |
| `gen_readme --check` | 불일치가 난다 → Step 2 로 |
| `doctor` | 필수 전부 있다 |

**⚠ `xmldoc check` 의 문제 건수는 늘어난다. 정상이다.**

`run_check` 는 `terms-reading.json` 의 용어마다 소스에 마커가 있는지 본다. Task 4 에서
옮긴 정의와 그 `# <include …/>` 블록을 지웠으므로, 그 용어들은 **마커를 잃는다** —
`레퍼런스가 없다` 로 세어진다. 지운 마커 수만큼(약 9건) 늘어 **94 → 약 103** 이 된다.

**고치는 방법은 `xmldoc.py emit` → `inject` 뿐이고, 그것은 이 계획의 범위 밖이다**
(사용자 판단 대기 중). 착수 전에 정확한 숫자를 적어 두고, 끝난 뒤 **그 수 + 지운 마커 수**
와 같은지 본다. 그보다 더 늘었으면 의도치 않게 다른 마커를 건드린 것이다.

```bash
# 착수 전에 재 둔다
.venv/bin/python machine/xmldoc.py check 2>&1 | tail -1
```

- [ ] **Step 2: 자동 생성 README 를 맞춘다**

Run: `.venv/bin/python tools/gen_readme.py machine runner viz tools`
그다음 Run: `.venv/bin/python tools/gen_readme.py --check machine runner viz tools`
Expected: `README 4개 — 소스와 일치`

- [ ] **Step 3: `runner/CLAUDE.md` 의 표에 새 파일을 더한다**

"무엇이 여기 있나" 표에 두 줄을 더한다:

```markdown
| `measure.py` | 세 실행기가 함께 쓰는 재는 코드 — 형 · 좁히기 도우미 · 표 · 하트비트. **`machine/` 을 import 하지 않는다** |
```

"비직관적인 것 (Gotchas)" 절에 한 줄을 더한다:

```markdown
- **Gotcha — `run_mode1.py` 를 import 하면 해석기가 바뀐다.** 파일 머리의 `_bootstrap_venv()` 가
  `.venv` 밖 해석기를 `os.execv` 로 갈아치우고, `import survey_plan` 이 networkx 를 문다.
  재는 코드가 필요할 뿐이면 `measure.py` 를 import 한다. `runner/test_import_isolation.py` 가 고정한다.
```

- [ ] **Step 4: 커밋**

```bash
git add runner/README.md runner/CLAUDE.md
git commit -m "[docs] : 공통축 신설을 러너 문서에 반영"
```

---

## 완료 조건

- [ ] `pytest` 가 483 이상 통과하고 줄어든 시험이 없다
- [ ] `npm run typecheck:py` 가 `0 errors`
- [ ] `runner/test_import_isolation.py` 3건 통과 — Mode 2·1.5 가 networkx 를 안 끌어온다
- [ ] `test/test_no_any.py` 통과 — `runner/measure.py` 에 형 자리 `Any` 0개
- [ ] `xmldoc check` 의 문제 건수가 **착수 전 수 + 지운 마커 수** 와 같다 (그보다 더 늘지 않았다)
- [ ] `gen_readme --check` 가 4개 일치
- [ ] 세 실행기의 `--dry-run` 출력이 이전과 같다

## 다음 단계

1단계가 끝나면 **2단계 계획을 쓴다** — `runner/pipeline.py`(Outcome · Stage · Edges · StageDagGraph · 시뮬레이터) 신설과 Mode 2 · Mode 1.5 이주. 2단계 계획의 코드는 여기서 나온 `measure.py` 의 실제 서명에 달려 있으므로 지금 쓰지 않는다.

**인계 문서 `HANDOFF-2026-09-07-warmup-increment-unreachable.md` 의 결함 ③④는 3단계가 끝난 뒤에 착수한다.** 고칠 자리(`run_layer` · `merge_shards`)가 3단계에서 옮겨가기 때문이다.

## 이 리팩터링이 xmldoc 결정에 미치는 영향

**리팩터링은 `# <include …/>` 레퍼런스를 대량으로 깨뜨린다.** 1단계에서 약 9건, 3단계에서
`run_mode1.py` 의 심볼 대부분이 `mode1/` 패키지로 옮겨가면 그 파일의 레퍼런스가 통째로
어긋난다. `terms-reading.json` 의 `where` 는 `runner/run_mode1.py:NNN` 을 가리키고 있다.

그래서 계류 중이던 질문이 바뀐다. **"큰 diff 를 낼 것인가" 가 아니라 "언제 낼 것인가" 다** —
리팩터링을 하는 이상 재주입은 피할 수 없다. 가장 싼 시점은 **3단계가 끝난 직후 한 번**이다.
중간에 여러 번 돌리면 그때마다 4,000줄 넘는 diff 가 난다.

`docs/decisions/0007`(폐지 예정)과도 이어진다 — 재주입을 어차피 한 번 해야 한다면, 그
시점이 폐지 표시를 `emit_xml()` 에 넣기에도 가장 좋은 자리다.
