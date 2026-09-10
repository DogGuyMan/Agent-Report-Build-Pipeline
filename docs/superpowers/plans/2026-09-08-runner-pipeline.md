# 러너 단계 기계 2단계 — `pipeline.py` 신설과 Mode 2 · Mode 1.5 이주

> ## ✅ 완료 — 2026-09-09
>
> Task 13개를 전부 실행했다. 게이트 여섯이 초록이고 `xmldoc check` 하나는 **의도된 빨강**이다
> (3단계 뒤에 `emit`→`inject` 한 번으로 푼다).
>
> | 게이트 | 결과 |
> |---|---|
> | 파이썬 시험 | **562 통과 · 19 건너뜀 · 실패 0** (착수 전 511) |
> | JS 시험 | 8 통과 · 0 실패 |
> | TS 타입 · 파이썬 타입 | 통과 · **0 errors** |
> | README 표류 | 4개 일치 |
> | 환경 | 필수 전부 있다 |
> | 주석 주입 | 🔴 문제 266건 — **고치지 마라.** 3단계 뒤 한 번 |
>
> **⚠ 커밋하지 않았다.** 재개 문서의 가드레일(*"커밋은 사용자가 요청할 때만"*)에 따라
> 각 Task 의 커밋 단계를 건너뛰고 워킹 트리에 쌓아 두었다. 아래 체크박스의 커밋 단계도
> 그래서 완료 표시가 아니다.
>
> ### 계획과 달라진 것 일곱 — 구현이 드러낸 것
>
> | # | 무엇 | 왜 |
> |---|---|---|
> | 1 | **산출물 사슬은 `OK` 갈래에서만 `writes` 를 보장으로 센다** | `FAIL`·`SKIP` 으로 떨어진 단계는 자기 산출물을 내지 않는다. 계획서 본문과 Task 5 코드를 고쳤다 |
> | 2 | `measure.py` 에 **`as_list` 를 더했다** | `isinstance(v, list)` 하나로는 `list[Unknown]` 이 되어 `pyright strict` 가 원소마다 걸린다. `as_map` 과 같은 모양 |
> | 3 | Mode 1.5 에 **`_text` 지역 도우미**를 뒀다 | `as_str(123)` 은 `""` 인데 옛 코드의 `str(123 or "")` 은 `"123"` 이다. 좁히기 사다리를 그대로 갖다 쓰면 조용히 동작이 바뀐다 |
> | 4 | `SheetQuestion.UserAns` 를 **`str \| int`** 로 | 실행기가 내는 값은 늘 `""` 이지만 사람이 채우면 정수도 온다. 계획서는 `str` 이라 적었는데 시험이 정수를 넣는다 |
> | 5 | `StageRow` 의 토큰 칸은 `input_tokens` 가 아니라 **`total`** | 계획서의 시험이 없는 칸을 짚었다 |
> | 6 | `validate_answers` 의 목록 판정을 **`as_list` 뒤로** 옮겼다 | `isinstance` 로 먼저 좁히면 `list[Unknown]`. 목록 아닌 것과 빈 목록을 가르는 동작은 그대로 지켰다 |
> | 7 | `test_run_mode1_5.py` 를 **두 줄 고쳤다** | `filled_sheet` 의 반환형을 `R.AnswerSheet` 으로, `dict(...)` 를 `.copy()` 로. TypedDict 도입이 강제한 것이라 피할 수 없었다 |
>
> **스키마를 주장하는 `cast` 는 2단계 범위에서 0건이다.** `run_mode1.py:1093` 의
> `cast(survey_plan.SurveyPlan, …)` 하나가 남아 있으나 Mode 1 이라 3단계 소관이다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 세 실행기가 각자 갖고 있는 단계 루프를 `runner/pipeline.py` 하나로 모으고, 단계를 `Stage` 클래스로 올려 파이프라인 밖 전이표로 잇는다. 2단계에서는 Mode 2 와 Mode 1.5 만 이주시킨다 — Mode 1 은 3단계다.

**Architecture:** `Stage[C]` 는 상태를 갖지 않고 `Outcome`(갈래 · 사유 · 측정 행)을 반환한다. 흐름은 `StageDagGraph` 로 **진입점에서 미리 짓고**, `simulate()` 가 검사 다섯을 통과시킨 뒤에야 단계가 하나라도 돈다. 드라이버 `Pipeline.run` 은 `while cur:` 한 벌이고 모드는 데이터(단계 사전 · 전이표)만 넘긴다.

**Tech Stack:** Python 3.14 · `pyright` strict · `pytest`. `pipeline.py` 는 `measure.py` 처럼 **`machine/` 을 import 하지 않는다** — `runner/test_import_isolation.py` 가 그것을 잰다.

---

## 착수 전에 읽을 것

| 무엇 | 어디 |
|---|---|
| 사양 원본 (결정 17건 · 범위 밖 · 위험) | `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` |
| 재개 문서 (1단계 실측 · 가드레일 · 충돌 매트릭스) | `docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md` |
| 1단계 산출물의 공개 API | `runner/measure.py` |
| 러너축 모듈 문서 | `runner/CLAUDE.md` |

## 이 계획서가 확정한 것 — 2026-09-09 사용자 판정

재개 문서가 "2단계 착수 전에 사용자 판정을 받아라" 고 지목한 미결정 3건을 물었다.

| # | 결정 | 판정 | 이 계획서에서 |
|---|---|---|---|
| D2 | `Stage` 는 상태를 갖지 않는다. 갈래는 `Outcome` 반환값이다 | **`[승인됨]`** | Task 1 · 2 |
| D5 | 단계 사이의 값은 형이 붙은 `Context` dataclass 로 넘긴다 | **`[승인됨]`** | Task 1 · 11 · 12 |
| D6 | `pipeline.run` 은 가상 함수가 아니다 | **`[번복됨]`** — 사용자가 **재정의 허용**을 골랐다 | Task 7 |

### D6 번복의 처리 — 루프 3벌을 되살리지 않는 형태

사용자가 고른 것은 *재정의할 수 있게 두는 것*이지 *모드마다 루프를 다시 쓰는 것*이 아니다.
그래서 `Pipeline.run` 은 **동작하는 기본 구현을 가진 보통 메서드**로 둔다 —
`@final` 을 붙이지 않고, 추상으로도 만들지 않는다.

**2단계에서 실제로 재정의하는 모드는 없다.** Mode 2 와 Mode 1.5 의 루프가 같기 때문이다.
Mode 1.5 의 사람 관문은 재정의 대신 `GATE` 갈래를 내는 `gate` 단계로 들어간다 —
그래야 갈래 넷 중 `GATE` 가 죽은 어휘가 되지 않고 시뮬레이터의 검사 대상이 된다.
재정의 자리는 열려 있고, 3단계에서 Mode 1 이 필요하면 거기서 쓴다.

### 사양에서 하나 벗어나는 것 — `LlmStage.repo` 훅

D3 은 `llmstage` 의 훅을 다섯(`prompt` · `model` · `rounds` · `jobs` · `harvest`)으로 적었다.
여기에 **`repo(ctx)` 하나를 더한다** — 여섯이다.

**왜.** `claude_argv(model, repo, extra_dirs)` 와 `subprocess.run(..., cwd=repo)` 가 저장소
경로를 요구하는데, 그 경로가 모드마다 다른 칸에 있다(Mode 1 은 `ctx.repo`, Mode 2 는
`ctx.project`). `RunContext` 에 올리면 Mode 1.5 에는 뜻이 없는 칸이 생긴다.
`rulebasestage` 가 이미 같은 이유로 `cwd(ctx)` 훅을 갖고 있으므로 **대칭이다.**

## 파일 구조

| 파일 | 무엇 | 줄 수(예상) |
|---|---|---|
| **신설** `runner/pipeline.py` | 갈래 · `Outcome` · `Context` · `Artifact` · `Stage` · `Edges` · `StageDagGraph` · `simulate` · `Pipeline` · `MachineStage` · `LlmStage` · `run_layer` | ~430 |
| **신설** `runner/test_pipeline.py` | 위의 시험. 특히 팩토리가 망가진 그래프 다섯을 거부하는지 | ~420 |
| **수정** `runner/run_mode2.py` | 단계 4개를 `Stage` 로. `main` 은 그래프를 짓고 드라이버에 넘긴다 | 477 → ~430 |
| **수정** `runner/run_mode1_5.py` | 단계 3개 + `gate`. `Any` 20곳 제거 | 670 → ~640 |
| **수정** `runner/run_mode1.py` | `run_agent_with` · `run_layer` 를 `pipeline` 에서 재수출 | 1201 → ~1150 |
| **수정** `test/test_no_any.py` | `COVERED` 에 `runner/pipeline.py` · `runner/run_mode1_5.py` 추가 | |
| **수정** `runner/CLAUDE.md` · `runner/README.md` | 새 구조를 가리킨다 | |

**`run_mode1.py` 는 파사드를 지키지 않는다** — 시험 4개가 옛 이름을 약 200회 참조한다(D8).

## 2단계에 미치는 산출물 실측 (🔵 2026-09-09)

세 모드의 단계별 입출력을 코드에서 전수로 세어 사양의 대조표를 고쳤다. 그중 2단계에
직접 걸리는 것 넷이다.

**① Mode 2 는 매개가 JSON 이 아니다.** `data.ts`·`report.tsx` 는 TypeScript 소스이고
`out/report.html` 은 HTML 이다. **Mode 2 의 `Artifact` 셋은 전부 `check=None` 이고
존재 검사만 한다.**

**② 그러므로 2단계에서 `Artifact.check` 의 소비자는 하나뿐이다** — Mode 1.5 의
`grade` 가 읽는 `questions.json`·`answers.json`. 나머지는 전부 존재 검사다.
검사 기계 자체는 3줄이고 3단계에서 Mode 1 의 JSON 5종이 소비자가 되므로 유지한다.

**③ Mode 1.5 의 쓰는 쪽·읽는 쪽에 사양이 틀린 곳이 둘 있었다.** `term-candidates.json` 을
읽는 것은 `grade` 가 아니라 **관문**이고, `answer-sheet.json` 을 쓰는 것도 **관문**이다.
`grade` 는 `answers.json` 과 `questions.json` 만 본다. **Task 12 의 `GradeStage.reads` 와
`GateStage.perform` 은 이 정정과 이미 맞다** — 고칠 것이 없다.

### 이 실측 위에서 확정한 규칙 셋 — 2026-09-09 사용자 판정

| # | 규칙 | 근거 |
|---|---|---|
| R1 | **선택 입력은 `reads` 에 선언하지 않는다.** `reads` 는 *없으면 죽는 것*만 담는다 | 없어도 정상이라 시뮬레이터가 잡을 결함이 없다. 훅을 늘리지 않는다 |
| R2 | **`Artifact.check` 는 JSON 전용이다.** 서명은 `(raw: object) -> list[str]` 이고 드라이버가 `read_json` 으로 한 번 읽어 넘긴다 | 파일 읽기가 한 자리에 모이고, Mode 1.5 의 기존 검사기 둘이 껍데기 없이 들어맞는다 |
| R3 | **비 JSON 산출물은 `check=None` 으로 존재만 본다** | Mode 2 의 셋이 전부 여기 해당한다 |

**R1 이 적용되는 세 곳** — `terms-db.json`(Mode 1.5 `collect`) · `terms.json`(Mode 2 `agent`) ·
`term-answer-key.json`(Mode 1.5 `gate`). 셋 다 `reads` 에 넣지 않고 단계 안에서 존재를 본다.
Task 12 의 `build_mode1_5_graph` 가 `given` 에 넣는 `questions.json`·`answers.json` 은
**선택이 아니라 필수인데 아무 단계도 쓰지 않는 것**이라 성격이 다르다 — 그 둘은 남는다.

**R2·R3 은 Task 1 의 `Artifact` 정의와 이미 맞다** — 고칠 것이 없다.

### 구현 중 잡은 결함 — `writes` 는 `OK` 갈래에서만 보장이다 (🔵 2026-09-09)

이 계획서의 첫 판은 산출물 사슬 검사에서 앞 단계의 `writes` 를 **갈래와 무관하게**
보장으로 셌다. **틀렸다.** 드라이버는 `out.kind == OK` 일 때만 `bad_writes` 를 보므로,
`FAIL` 이나 `SKIP` 으로 떨어진 단계는 자기 산출물을 내지 않았다.

Task 5 의 `test_산출물_어떤_경로에서만_없는_것을_잡는다` 가 이것을 잡았다 —
그 시험이 바로 "`a` 가 `FAIL` 로 `c` 에 떨어지는 경로" 를 재는 것인데, 앞선 판의
계산은 그 경로에서도 `a` 가 계획 파일을 썼다고 보아 불평을 내지 않았다.
아래 Task 5 의 코드가 고쳐진 판이다.

**④ `writes` 는 "이 단계의 파이썬 코드가 쓴다" 가 아니라 "이 단계가 돌고 나면 있어야
한다" 는 뜻이다.** Mode 1 의 `_shards/<배치>.json` 은 LLM 자식 프로세스가 쓰고 러너는
읽기만 하며, Mode 2 의 `agent` 도 `data.ts` 를 LLM 을 통해 채운다. 3단계에서 이 구분이
필요해지므로 `Stage.writes` 의 독스트링에 그 뜻을 적는다.

---

---

## Task 1: 갈래 넷 · `Outcome` · `RunContext` · `Artifact`

**Files:**
- Create: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

`runner/test_pipeline.py` 를 새로 만든다.

```python
"""단계 기계의 시험. 갈래 · 전이표 · 그래프 · 시뮬레이터 · 드라이버."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P  # noqa: E402


def test_갈래_넷은_서로_다른_비트다():
    assert len({P.OK, P.FAIL, P.SKIP, P.GATE}) == 4
    assert P.OK | P.FAIL | P.SKIP | P.GATE == 15


def test_Outcome_은_행_없이도_만들어진다():
    out = P.Outcome(P.OK)
    assert out.kind == P.OK
    assert out.why == ""
    assert out.rows == []


def test_Outcome_둘이_행_목록을_공유하지_않는다():
    a, b = P.Outcome(P.OK), P.Outcome(P.OK)
    a.rows.append({"stage": "x", "seconds": 0.0, "usage": {}, "ok": True, "why": ""})
    assert b.rows == []


def test_RunContext_는_세_칸을_갖는다():
    ctx = P.RunContext(root="/r", model="opus")
    assert (ctx.root, ctx.model, ctx.timeout, ctx.concurrency) == ("/r", "opus", None, 8)


def test_Artifact_는_ctx_로_자리를_정한다():
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    assert art.locate(P.RunContext(root="/r", model="opus")) == "/r/plan.md"
    assert art.check is None
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline'`

- [x] **Step 3: 최소 구현을 쓴다**

`runner/pipeline.py` 를 새로 만든다.

```python
#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 단계 기계. 갈래 · 단계 · 전이표 · 그래프 · 드라이버.

**`machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다 — `test_import_isolation.py` 가 그것을 잰다.

**`Any` 를 쓰지 않는다.** 바깥이 꼴을 정하는 값은 `object` 로 받고 `measure.py` 의
좁히기 도우미로 하나씩 확인한다.
"""
import json
import os
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Generic, TypeVar, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M  # noqa: E402
from measure import AgentResult, StageRow  # noqa: E402

# ── 1. 갈래 넷 — 비트 하나씩. 늘리지 않는다 ─────────────────────────────
OK = 1
FAIL = 2
SKIP = 4
GATE = 8

KINDS = (OK, FAIL, SKIP, GATE)
KIND_NAME = {OK: "OK", FAIL: "FAIL", SKIP: "SKIP", GATE: "GATE"}

# 전이의 목적지 특수값. 단계 이름과 겹치지 않도록 널 문자로 시작한다.
HALT = "\x00halt"
NEXT = "\x00next"


@dataclass
class Outcome:
    """`perform()` 이 낸 것. 갈래는 정확히 하나이고, 세션 N개면 행도 N개다."""
    kind: int
    why: str = ""
    rows: list[StageRow] = field(default_factory=list)


@dataclass
class RunContext:
    """세 모드가 공유하는 칸만. 모드마다 이것을 상속해 자기 칸을 더한다."""
    root: str
    model: str
    timeout: float | None = None
    concurrency: int = 8


C = TypeVar("C", bound=RunContext)


@dataclass(frozen=True)
class Artifact(Generic[C]):
    """단계가 읽고 쓰는 파일 하나. 자리는 `ctx` 가 정하므로 경로를 박지 않는다.

    `check` 가 `None` 이면 있는지만 본다 — `data.ts` 처럼 JSON 이 아닌 것들이다.
    `check` 가 있으면 JSON 으로 읽어 넘기고, 불평 목록이 비어야 통과한다.
    """
    name: str
    locate: Callable[[C], str]
    check: Callable[[object], list[str]] | None = None


def read_json(path: str) -> object:
    """`json.load` 의 `Any` 를 `object` 로 좁히는 유일한 자리. 못 읽으면 `None`."""
    try:
        with open(path, encoding="utf-8") as f:
            return cast(object, json.load(f))
    except (OSError, ValueError):
        return None
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 5 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 단계 기계의 갈래 넷과 문맥 · 산출물 형

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `Stage[C]` 추상 기반과 산출물 검사

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

`runner/test_pipeline.py` 끝에 붙인다.

```python
class 가짜단계(P.Stage[P.RunContext]):
    """시험용. 정해진 갈래를 그대로 낸다."""

    def __init__(self, name: str, kind: int = P.OK, emits: int = P.OK | P.FAIL,
                 reads: list[P.Artifact[P.RunContext]] | None = None,
                 writes: list[P.Artifact[P.RunContext]] | None = None) -> None:
        self.name = name
        self.emits = emits
        self._kind = kind
        self._reads = reads or []
        self._writes = writes or []
        self.돈횟수 = 0

    def reads(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
        return self._reads

    def writes(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
        return self._writes

    def perform(self, ctx: P.RunContext) -> P.Outcome:
        self.돈횟수 += 1
        return P.Outcome(self._kind, "", [{"stage": self.name, "seconds": 0.0,
                                           "usage": M.normalize_usage(None),
                                           "ok": self._kind == P.OK, "why": ""}])


def test_읽을_것이_없으면_이름으로_말해_준다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    st = 가짜단계("collect", reads=[art])
    assert P.missing_reads(st, ctx) == ["읽을 것이 없다 — 계획"]


def test_읽을_것이_있으면_불평이_없다(tmp_path):
    (tmp_path / "plan.md").write_text("x", encoding="utf-8")
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    assert P.missing_reads(가짜단계("collect", reads=[art]), ctx) == []


def test_꼴이_어긋난_산출물은_불평이_된다(tmp_path):
    (tmp_path / "q.json").write_text('{"terms": []}', encoding="utf-8")
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext](
        "문항지", lambda c: os.path.join(c.root, "q.json"),
        check=lambda raw: [] if M.as_map(raw).get("terms") else ["용어가 없다"])
    assert P.bad_writes(가짜단계("x", writes=[art]), ctx) == ["문항지 — 용어가 없다"]


def test_쓰지_못한_산출물은_없다고_말한다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("보고서", lambda c: os.path.join(c.root, "r.html"))
    assert P.bad_writes(가짜단계("build", writes=[art]), ctx) == ["보고서 — 나오지 않았다"]
```

`runner/test_pipeline.py` 의 import 줄에 `measure` 를 더한다.

```python
import measure as M  # noqa: E402
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'Stage'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `read_json` 아래에 붙인다.

```python
# ── 2. 단계 — 상태를 갖지 않는다. 갈래는 반환값이다 ─────────────────────
class Stage(ABC, Generic[C]):
    """단계 하나. `emits` 는 **선언**이고 실제로 난 갈래는 `perform` 이 반환한다.

    `emits` 를 클래스에 두는 덕에 **시작 전에** 전이표 완결성을 검사할 수 있다.
    같은 단계를 층마다 다시 돌아도 인스턴스에 남는 것이 없다.
    """
    name: str = ""
    emits: int = OK | FAIL

    def reads(self, ctx: C) -> list[Artifact[C]]:
        """돌기 전에 있어야 하는 것. 없으면 단계를 돌리지 않는다."""
        return []

    def writes(self, ctx: C) -> list[Artifact[C]]:
        """**돌고 나면 있어야 하는 것.** 꼴이 어긋나면 `FAIL` 이 된다.

        이 단계의 파이썬 코드가 쓴다는 뜻이 아니다 — LLM 자식 프로세스가 쓰는 것도
        여기 선다. 누가 썼는지가 아니라 무엇이 있어야 하는지의 선언이다.
        """
        return []

    @abstractmethod
    def perform(self, ctx: C) -> Outcome:
        ...


def missing_reads(stage: Stage[C], ctx: C) -> list[str]:
    """읽을 산출물 중 없거나 꼴이 어긋난 것의 불평 목록."""
    out: list[str] = []
    for art in stage.reads(ctx):
        path = art.locate(ctx)
        if not os.path.exists(path):
            out.append("읽을 것이 없다 — %s" % art.name)
            continue
        if art.check is not None:
            out.extend("%s — %s" % (art.name, c) for c in art.check(read_json(path)))
    return out


def bad_writes(stage: Stage[C], ctx: C) -> list[str]:
    """쓴 산출물 중 안 나왔거나 꼴이 어긋난 것의 불평 목록."""
    out: list[str] = []
    for art in stage.writes(ctx):
        path = art.locate(ctx)
        if not os.path.exists(path):
            out.append("%s — 나오지 않았다" % art.name)
            continue
        if art.check is not None:
            out.extend("%s — %s" % (art.name, c) for c in art.check(read_json(path)))
    return out
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 9 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 단계 추상 기반과 읽기 쓰기 산출물 검사

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `Edges` — 파이프라인 밖 전이표

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
def test_전이표는_단계별_규칙을_먼저_본다():
    e = P.Edges({("lang-propose", P.FAIL): "lang-decide",
                 ("*", P.FAIL): P.HALT,
                 ("*", P.OK): P.NEXT})
    assert e.dest("lang-propose", P.FAIL) == "lang-decide"
    assert e.dest("prep", P.FAIL) == P.HALT
    assert e.dest("prep", P.OK) == P.NEXT


def test_전이표에_없는_갈래는_None_이다():
    e = P.Edges({("*", P.OK): P.NEXT})
    assert e.dest("prep", P.SKIP) is None


def test_전이표는_넘겨받은_사전을_복사한다():
    표 = {("*", P.OK): P.NEXT}
    e = P.Edges(표)
    표[("*", P.FAIL)] = P.HALT
    assert e.dest("prep", P.FAIL) is None
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k 전이표 -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'Edges'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `bad_writes` 아래에 붙인다.

```python
# ── 3. 전이표 — 파이프라인 밖에 하나. 단계는 자기 다음을 모른다 ──────────
class Edges:
    """`(단계 이름, 갈래) -> 목적지`. 목적지는 단계 이름이거나 `HALT` · `NEXT` 다.

    단계 이름 `"*"` 는 모든 단계에 걸리는 기본 규칙이다. 단계별 규칙이 먼저다.
    **기본값을 코드에 숨기지 않는다** — 규칙이 없으면 `None` 을 내고,
    그것을 `simulate` 가 완결성 위반으로 잡는다.
    """

    def __init__(self, table: Mapping[tuple[str, int], str]) -> None:
        self._table = dict(table)

    def dest(self, stage: str, kind: int) -> str | None:
        if (stage, kind) in self._table:
            return self._table[(stage, kind)]
        return self._table.get(("*", kind))
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 12 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 파이프라인 밖 전이표

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `StageDagGraph[C]` — 미리 지은 흐름

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
def 삼단_그래프(kinds: dict[str, int] | None = None) -> P.StageDagGraph[P.RunContext]:
    kinds = kinds or {}
    names = ["a", "b", "c"]
    stages = {n: 가짜단계(n, kinds.get(n, P.OK)) for n in names}
    return P.StageDagGraph(name="시험", order=names, stages=stages,
                           edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))


def test_첫_단계는_순서의_맨_앞이다():
    assert 삼단_그래프().first == "a"


def test_빈_그래프의_첫_단계는_None_이다():
    g = P.StageDagGraph(name="빈", order=[], stages={}, edges=P.Edges({}))
    assert g.first is None


def test_NEXT_는_순서상_다음_단계다():
    g = 삼단_그래프()
    assert g.next_of("a", P.OK) == "b"
    assert g.next_of("c", P.OK) is None


def test_HALT_는_흐름을_끝낸다():
    assert 삼단_그래프().next_of("b", P.FAIL) is None


def test_이름을_적은_간선은_그리로_점프한다():
    g = P.StageDagGraph(
        name="점프", order=["a", "b", "c"],
        stages={n: 가짜단계(n) for n in ["a", "b", "c"]},
        edges=P.Edges({("a", P.OK): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert g.next_of("a", P.OK) == "c"


def test_render_는_단계마다_갈래를_보인다():
    글 = 삼단_그래프().render()
    assert "a" in 글 and "OK→b" in 글 and "FAIL→(멈춤)" in 글
    assert "OK→(끝)" in 글
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k 그래프 -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'StageDagGraph'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `Edges` 아래에 붙인다.

```python
# ── 4. 그래프 — 팩토리가 미리 짓고 보장한 흐름 ──────────────────────────
@dataclass(frozen=True)
class StageDagGraph(Generic[C]):
    """실제로 돌 흐름. `order` 는 위상 순서이고 모든 간선이 앞으로만 간다.

    `given` 은 첫 단계가 돌기 전에 **이미 있는** 산출물이다 — 바깥에서 들어온 원본
    문서와, `--only` 로 앞칸을 뺐지만 디스크에 남아 있는 파일들이다.
    """
    name: str
    order: list[str]
    stages: dict[str, Stage[C]]
    edges: Edges
    given: list[Artifact[C]] = field(default_factory=list)

    @property
    def first(self) -> str | None:
        return self.order[0] if self.order else None

    def next_of(self, cur: str, kind: int) -> str | None:
        """이 갈래로 갈 다음 단계. 흐름이 끝나면 `None`."""
        d = self.edges.dest(cur, kind)
        if d is None or d == HALT:
            return None
        if d != NEXT:
            return d
        i = self.order.index(cur)
        return self.order[i + 1] if i + 1 < len(self.order) else None

    def render(self) -> str:
        """`--dry-run` 이 찍는 것. 폴백 간선까지 화면에 보인다."""
        lines = ["흐름 %s — 단계 %d" % (self.name, len(self.order))]
        for name in self.order:
            outs: list[str] = []
            for kind in KINDS:
                if not self.stages[name].emits & kind:
                    continue
                nxt = self.next_of(name, kind)
                if nxt is None:
                    # 순서상 다음이 없어 끝난 것과 HALT 로 멈춘 것을 갈라 적는다.
                    nxt = "(끝)" if self.edges.dest(name, kind) == NEXT else "(멈춤)"
                outs.append("%s→%s" % (KIND_NAME[kind], nxt))
            lines.append("  %-14s %s" % (name, " · ".join(outs)))
        return "\n".join(lines)
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 18 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 단계 흐름 그래프와 dry-run 이 찍을 그림

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `simulate` — 아무것도 실행하지 않고 검사 다섯

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

사양의 완료 조건 6 이 요구하는 것이다 — **망가진 그래프 다섯을 거부해야 한다.**

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
def test_어긋난_것이_없으면_불평이_없다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    assert P.simulate(삼단_그래프(), ctx) == []


def test_완결성_emits_비트에_간선이_없으면_잡는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="완결성", order=["a"],
        stages={"a": 가짜단계("a", emits=P.OK | P.SKIP)},
        edges=P.Edges({("*", P.OK): P.NEXT}))          # SKIP 규칙이 없다
    불평 = P.simulate(g, ctx)
    assert any("완결성" in c and "SKIP" in c for c in 불평), 불평


def test_매달림_없는_단계를_가리키면_잡는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="매달림", order=["a"], stages={"a": 가짜단계("a")},
        edges=P.Edges({("a", P.OK): "없는단계", ("*", P.FAIL): P.HALT}))
    assert any("매달림" in c for c in P.simulate(g, ctx))


def test_순환_뒤로_가는_간선을_잡는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="순환", order=["a", "b"],
        stages={"a": 가짜단계("a"), "b": 가짜단계("b")},
        edges=P.Edges({("b", P.FAIL): "a", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("순환" in c for c in P.simulate(g, ctx))


def test_도달성_아무도_가지_않는_단계를_잡는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="고아", order=["a", "b", "c"],
        stages={n: 가짜단계(n) for n in ["a", "b", "c"]},
        edges=P.Edges({("a", P.OK): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("도달성" in c and "b" in c for c in P.simulate(g, ctx))


def test_산출물_어떤_경로에서만_없는_것을_잡는다(tmp_path):
    """`a` 가 FAIL 로 `c` 에 떨어지면 `b` 가 쓸 파일이 없다. 한 줄 흐름이면 안 보인다."""
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    계획 = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.json"))
    g = P.StageDagGraph(
        name="사슬", order=["a", "b", "c"],
        stages={"a": 가짜단계("a", writes=[계획]),
                "b": 가짜단계("b"),
                "c": 가짜단계("c", reads=[계획])},
        edges=P.Edges({("a", P.FAIL): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("산출물" in c and "계획" in c for c in P.simulate(g, ctx))


def test_산출물_이미_있는_것은_given_으로_통과한다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    계획 = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.json"))
    g = P.StageDagGraph(
        name="given", order=["c"], stages={"c": 가짜단계("c", reads=[계획])},
        edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), given=[계획])
    assert P.simulate(g, ctx) == []


def test_팩토리는_어긋나면_단계를_하나도_돌리지_않고_죽는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    돌_단계 = 가짜단계("a", emits=P.OK | P.SKIP)
    with pytest.raises(P.GraphError) as e:
        P.build_graph("망가짐", ["a"], {"a": 돌_단계},
                      P.Edges({("*", P.OK): P.NEXT}), [], ctx)
    assert 돌_단계.돈횟수 == 0
    assert "완결성" in str(e.value)


def test_팩토리는_멀쩡하면_그래프를_낸다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.build_graph("멀쩡", ["a"], {"a": 가짜단계("a")},
                      P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), [], ctx)
    assert g.first == "a"
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k "simulate or 완결성 or 산출물 or 팩토리 or 순환 or 도달성 or 매달림 or 어긋난" -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'simulate'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `StageDagGraph` 아래에 붙인다.

```python
class GraphError(Exception):
    """팩토리가 지은 그래프가 검사를 통과하지 못했다. 단계는 하나도 돌지 않았다."""


def simulate(graph: StageDagGraph[C], ctx: C) -> list[str]:
    """아무것도 실행하지 않고 그래프만 걷는다. 불평 목록을 낸다(없으면 빈 목록).

    다섯을 본다 — 완결성 · 매달림 · 비순환 · 도달성 · 산출물 사슬.
    산출물 사슬은 **닿을 수 있는 모든 경로에서** 성립해야 한다. 가지가 생기면
    사람이 눈으로는 못 보는 자리라 이 검사가 손 검토보다 나은 유일한 이유다.
    """
    out: list[str] = []
    index = {n: i for i, n in enumerate(graph.order)}
    순환있음 = False

    # ① 완결성 · ② 매달림 · ③ 비순환
    for name in graph.order:
        stage = graph.stages[name]
        for kind in KINDS:
            if not stage.emits & kind:
                continue
            d = graph.edges.dest(name, kind)
            if d is None:
                out.append("완결성 — %s 의 %s 갈래에 간선이 없다" % (name, KIND_NAME[kind]))
                continue
            if d in (HALT, NEXT):
                continue
            if d not in graph.stages:
                out.append("매달림 — %s 의 %s 갈래가 없는 단계를 가리킨다: %s"
                           % (name, KIND_NAME[kind], d))
                continue
            if index[d] <= index[name]:
                out.append("순환 — %s 의 %s 갈래가 뒤로 간다: %s"
                           % (name, KIND_NAME[kind], d))
                순환있음 = True

    # ④ 도달성 — 첫 단계에서 어느 갈래로도 닿지 못하는 단계
    닿음: set[str] = set()
    if graph.first:
        더볼것 = [graph.first]
        while 더볼것:
            cur = 더볼것.pop()
            if cur in 닿음 or cur not in graph.stages:
                continue
            닿음.add(cur)
            for kind in KINDS:
                if not graph.stages[cur].emits & kind:
                    continue
                nxt = graph.next_of(cur, kind)
                if nxt:
                    더볼것.append(nxt)
    for name in graph.order:
        if name not in 닿음:
            out.append("도달성 — %s 로 가는 경로가 하나도 없다" % name)

    # ⑤ 산출물 사슬 — 순환이 있으면 앞 단계의 답이 아직 없어 셀 수 없다
    if 순환있음:
        return out
    # **갈래를 함께 담는다.** `OK` 로 나온 간선만 앞 단계의 `writes` 를 보장한다 —
    # `FAIL` 이나 `SKIP` 으로 떨어진 단계는 자기 산출물을 내지 않았다.
    앞선것: dict[str, list[tuple[str, int]]] = {n: [] for n in graph.order}
    for name in graph.order:
        for kind in KINDS:
            if not graph.stages[name].emits & kind:
                continue
            nxt = graph.next_of(name, kind)
            if nxt in 앞선것:
                앞선것[cast(str, nxt)].append((name, kind))
    보장됨: dict[str, set[str]] = {}
    처음부터 = {a.name for a in graph.given}
    for name in graph.order:
        ps = 앞선것[name]
        if ps:
            묶음 = [보장됨[p] | ({a.name for a in graph.stages[p].writes(ctx)}
                                if kind == OK else set())
                    for p, kind in ps]
            보장됨[name] = set.intersection(*묶음)
        else:
            보장됨[name] = set(처음부터)
        for art in graph.stages[name].reads(ctx):
            if art.name not in 보장됨[name]:
                out.append("산출물 — %s 가 읽는 %s 를 앞의 어떤 단계도 반드시 쓰지 않는다"
                           % (name, art.name))
    return out


def build_graph(name: str, order: Sequence[str], stages: Mapping[str, Stage[C]],
                edges: Edges, given: Sequence[Artifact[C]], ctx: C) -> StageDagGraph[C]:
    """흐름을 짓고 **그 자리에서 보장한다.** 어긋나면 단계를 하나도 돌리지 않고 죽는다.

    진입점에서 부른다 — 어떤 자식 프로세스도 띄우기 전에. 실패가 늦게 나면
    이미 파일을 쓴 뒤라 되돌리기 어렵다.
    """
    graph = StageDagGraph(name=name, order=list(order), stages=dict(stages),
                          edges=edges, given=list(given))
    complaints = simulate(graph, ctx)
    if complaints:
        raise GraphError("흐름 %s 가 어긋났다:\n  " % name + "\n  ".join(complaints))
    return graph


def existing(artifacts: Sequence[Artifact[C]], ctx: C) -> list[Artifact[C]]:
    """이미 디스크에 있는 산출물만 고른다. `build_graph` 의 `given` 에 넣는다.

    `--only build` 처럼 앞칸을 빼고 불러도 파일이 실제로 있으면 흐름이 성립한다.
    """
    return [a for a in artifacts if os.path.exists(a.locate(ctx))]
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 27 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 그래프 시뮬레이터와 진입점 팩토리

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `Pipeline[C].run` — 재정의 가능한 드라이버 (D6)

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
def test_드라이버는_전이표를_따라_끝까지_돈다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = 삼단_그래프()
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert [r["stage"] for r in rows] == ["a", "b", "c"]


def test_드라이버는_FAIL_에서_멈춘다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = 삼단_그래프({"b": P.FAIL})
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert [r["stage"] for r in rows] == ["a", "b"]
    assert g.stages["c"].돈횟수 == 0


def test_드라이버는_읽을_것이_없으면_단계를_돌리지_않는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    st = 가짜단계("a", reads=[art])
    g = P.StageDagGraph(name="빠짐", order=["a"], stages={"a": st},
                        edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert st.돈횟수 == 0
    assert rows[0]["ok"] is False
    assert "계획" in rows[0]["why"]


def test_드라이버는_재정의할_수_있다(tmp_path):
    """D6 — 사용자 판정. `run` 은 닫히지 않는다."""
    class 덧붙이는드라이버(P.Pipeline[P.RunContext]):
        def run(self, graph, ctx):
            rows = super().run(graph, ctx)
            rows.append({"stage": "덧붙임", "seconds": 0.0,
                         "usage": M.normalize_usage(None), "ok": True, "why": ""})
            return rows

    ctx = P.RunContext(root=str(tmp_path), model="opus")
    rows = 덧붙이는드라이버().run(삼단_그래프(), ctx)
    assert [r["stage"] for r in rows] == ["a", "b", "c", "덧붙임"]
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k 드라이버 -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'Pipeline'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `existing` 아래에 붙인다.

```python
# ── 5. 드라이버 — 한 벌. 모드는 데이터(그래프)만 넘긴다 ──────────────────
class Pipeline(Generic[C]):
    """그래프를 따라 도는 루프. 세 실행기가 이 한 벌을 쓴다.

    `run` 은 **재정의할 수 있다.** 다만 재정의가 루프를 다시 쓰는 자리는 아니다 —
    `super().run()` 을 부르고 앞뒤에 자기 일을 붙이는 자리다.
    """

    def run(self, graph: StageDagGraph[C], ctx: C) -> list[StageRow]:
        rows: list[StageRow] = []
        cur = graph.first
        while cur:
            stage = graph.stages[cur]
            print("\n── %s ──────────────────────────────" % cur, flush=True)
            t0 = time.monotonic()
            missing = missing_reads(stage, ctx)
            if missing:
                why = "; ".join(missing)
                out = Outcome(FAIL, why, [{"stage": cur, "seconds": time.monotonic() - t0,
                                           "usage": M.normalize_usage(None),
                                           "ok": False, "why": why}])
            else:
                out = stage.perform(ctx)
                bad = bad_writes(stage, ctx) if out.kind == OK else []
                if bad:
                    why = "; ".join(bad)
                    for row in out.rows:
                        row["ok"], row["why"] = False, why
                    out = Outcome(FAIL, why, out.rows)
            rows.extend(out.rows)
            nxt = graph.next_of(cur, out.kind)
            if out.kind == FAIL and nxt is None:
                print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            cur = nxt
        return rows
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 31 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 그래프를 따라 도는 드라이버 한 벌

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: `MachineStage` — 자식 프로세스 단계

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
class 참말단계(P.MachineStage[P.RunContext]):
    name = "참말"

    def argv(self, ctx: P.RunContext) -> list[str]:
        return [sys.executable, "-c", "pass"]

    def cwd(self, ctx: P.RunContext) -> str:
        return ctx.root


class 거짓말단계(참말단계):
    name = "거짓말"

    def argv(self, ctx: P.RunContext) -> list[str]:
        return [sys.executable, "-c", "raise SystemExit(3)"]


def test_기계_단계는_성공하면_OK_한_행이다(tmp_path):
    out = 참말단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.OK
    assert len(out.rows) == 1
    assert out.rows[0]["stage"] == "참말"
    assert out.rows[0]["usage"]["total"] == 0


def test_기계_단계는_종료코드를_사유로_적는다(tmp_path):
    out = 거짓말단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.FAIL
    assert "종료 코드 3" in out.why


def test_기계_단계는_작업_폴더가_없으면_돌지_않는다(tmp_path):
    ctx = P.RunContext(root=str(tmp_path / "없는곳"), model="opus")
    out = 참말단계().perform(ctx)
    assert out.kind == P.FAIL
    assert "작업 디렉토리가 없다" in out.why
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k 기계_단계 -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'MachineStage'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `Pipeline` 아래에 붙인다.

```python
# ── 6. 구체 단계의 두 갈래 — 기계와 LLM ─────────────────────────────────
class MachineStage(Stage[C]):
    """자식 프로세스 하나. LLM 을 부르지 않으므로 토큰은 늘 0이고 행도 하나다.

    `perform` 을 재정의하지 않는다 — 자식 프로세스를 띄우는 방식이 갈리면
    측정이 모드마다 달라진다.
    """
    emits = OK | FAIL

    @abstractmethod
    def argv(self, ctx: C) -> list[str]:
        ...

    @abstractmethod
    def cwd(self, ctx: C) -> str:
        ...

    def perform(self, ctx: C) -> Outcome:
        t0 = time.monotonic()
        cwd = self.cwd(ctx)
        if not os.path.isdir(cwd):
            ok, why = False, "작업 디렉토리가 없다: %s" % cwd
        else:
            with M.Heartbeat(self.name, every=60.0):
                rc = subprocess.run(self.argv(ctx), cwd=cwd).returncode
            ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
        seconds = time.monotonic() - t0
        print("%s — %s (%s)" % (self.name, "성공" if ok else "실패", M.hms(seconds)),
              flush=True)
        return Outcome(OK if ok else FAIL, why,
                       [{"stage": self.name, "seconds": seconds,
                         "usage": M.normalize_usage(None), "ok": ok, "why": why}])
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 34 passed

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : 자식 프로세스 단계

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: `run_agent_with` · `run_layer` 를 `pipeline.py` 로 옮긴다

**Files:**
- Modify: `runner/pipeline.py`
- Modify: `runner/run_mode1.py` (정의를 지우고 재수출로)
- Test: `runner/test_run_mode1.py` (한 줄도 고치지 않는다 — 파사드가 지킨다)

`LlmStage.perform` 이 팬아웃 호출을 쓴다. 그 코드는 지금 `run_mode1.py` 안에 있고
`machine/` 을 쓰지 않으므로 그대로 옮겨진다. **이름을 바꾸지 않는다** —
`runner/test_run_mode1.py` 가 `R.run_layer` 를 그대로 부른다.

- [x] **Step 1: 옮기기 전 시험이 초록인지 본다**

Run: `.venv/bin/python -m pytest runner/test_run_mode1.py -k "run_layer or run_agent_with" -q`
Expected: PASS — 옮긴 뒤에도 이 숫자가 같아야 한다. 숫자를 적어 둔다.

- [x] **Step 2: `pipeline.py` 에 옮겨 적는다**

`runner/pipeline.py` 의 `MachineStage` 아래에 붙인다. 본문은 `run_mode1.py` 의
`run_agent_with` · `run_layer` 를 **그대로** 옮긴 것이고, `AgentResult` 와
`claude_argv` 의 출처만 `measure` 로 바뀐다.

```python
# `claude -p` 한 번의 결과. `(걸린 초, 종료 코드, 결과 또는 None)`.
JobResult = tuple[str, float, int, AgentResult | None]


def run_agent_with(model: str, repo: str, root: str, prompt: str,
                   timeout: float | None = None,
                   label: str | None = None) -> tuple[float, int, AgentResult | None]:
    """`claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`.

    **배치별 시간을 여기서 잰다** — 부르는 쪽은 병렬이라 층 전체만 잴 수 있다.

    **하트비트를 여기 두지 않는다.** 동시에 도는 배치가 저마다 찍으면 화면을 못 읽는다.
    """
    argv = M.claude_argv(model=model, repo=repo, extra_dirs=[root])
    t0 = time.monotonic()
    p = subprocess.run(argv, input=prompt, cwd=repo,
                       capture_output=True, text=True, timeout=timeout)
    seconds = time.monotonic() - t0
    try:
        return seconds, p.returncode, cast(AgentResult, json.loads(p.stdout))
    except (ValueError, TypeError):
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print("[%s] %s" % (label or "?", tail), file=sys.stderr)
        return seconds, p.returncode, None


def run_layer(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]],
              concurrency: int = 8,
              timeout: float | None = None) -> list[JobResult]:
    """한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다.

    `jobs` 는 `[(라벨, 프롬프트), …]`. 낸 것은 `[(라벨, 초, 종료코드, 결과 또는 None), …]`
    이고 **라벨 순서로 정렬**해서 낸다 — 끝나는 순서는 실행마다 흔들린다.

    **한 배치가 터져도 층을 버리지 않는다.** 터진 배치는 종료 코드 -1 · 결과 None 인
    행으로 남고, 부르는 쪽이 실패로 센다.
    """
    if not jobs:
        return []
    rows: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
        futs = {ex.submit(run_agent_with, model, repo, root, prompt, timeout, label): label
                for label, prompt in jobs}
        for f in futs:
            label = futs[f]
            try:
                rows.append((label,) + f.result())
            except Exception as ex_:                      # noqa: BLE001 — 층을 살린다
                print("[%s] 배치가 터졌다: %s" % (label, ex_), file=sys.stderr)
                rows.append((label, 0.0, -1, None))
    return sorted(rows, key=lambda r: r[0])
```

- [x] **Step 3: `run_mode1.py` 의 정의를 지우고 재수출로 바꾼다**

`runner/run_mode1.py` 에서 `run_agent_with` 와 `run_layer` 의 **정의 두 개와 그 위의
`# <include …/>` 주석 블록**을 지운다. `import measure as M` 아래에 붙인다.

```python
import pipeline as P  # noqa: E402

# 팬아웃 호출의 원본은 `pipeline.py` 하나뿐이다. 여기에는 사본이 없다 —
# 시험 4개가 옛 이름을 참조하므로 이름 그대로 재수출한다.
run_agent_with = P.run_agent_with
run_layer = P.run_layer
```

`ThreadPoolExecutor` import 가 다른 데서 안 쓰이면 함께 지운다.

Run: `grep -n "ThreadPoolExecutor" runner/run_mode1.py`
없으면 `from concurrent.futures import ThreadPoolExecutor` 줄을 지운다.

- [x] **Step 4: 시험이 그대로 통과하는지 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode1.py -q && .venv/bin/python -m pytest runner/test_import_isolation.py -q`
Expected: PASS — Step 1 과 같은 수. import 격리 4개도 통과

Run: `npm run typecheck:py`
Expected: `0 errors`

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/run_mode1.py
git commit -m "$(cat <<'EOF'
[refactor] : 팬아웃 호출을 공통축으로 옮기고 옛 이름은 재수출

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: `LlmStage` — 훅 여섯, 필수는 둘

**Files:**
- Modify: `runner/pipeline.py`
- Test: `runner/test_pipeline.py`

D3 의 다섯에 `repo` 를 더한 여섯이다(위 "사양에서 하나 벗어나는 것"). 필수는
`prompt` 와 `repo` 둘이고 넷은 기본값이 있다.

- [x] **Step 1: 실패하는 시험을 쓴다**

```python
class 한번부르는단계(P.LlmStage[P.RunContext]):
    name = "한번"

    def prompt(self, ctx: P.RunContext) -> str:
        return "무엇을 하라"

    def repo(self, ctx: P.RunContext) -> str:
        return ctx.root


class 두층부르는단계(한번부르는단계):
    name = "두층"

    def rounds(self, ctx: P.RunContext) -> int:
        return 2

    def jobs(self, ctx: P.RunContext, rnd: int) -> list[tuple[str, str]]:
        return [("L%d-B0" % rnd, "p"), ("L%d-B1" % rnd, "p")]


def 가짜층(결과: dict[str, object] | None, rc: int = 0):
    def _fake(model, repo, root, jobs, concurrency=8, timeout=None):
        return [(label, 1.0, rc, 결과) for label, _ in jobs]
    return _fake


def test_LLM_단계는_기본으로_자기_이름의_세션_하나다(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "run_layer", 가짜층({"total_cost_usd": 0.5}))
    out = 한번부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.OK
    assert [r["stage"] for r in out.rows] == ["한번"]
    assert out.rows[0]["usage"]["cost_usd"] == 0.5


def test_LLM_단계는_기본_LLM_Model이_ctx_의_것이다(tmp_path, monkeypatch):
    본것: list[str] = []

    def _spy(model, repo, root, jobs, concurrency=8, timeout=None):
        본것.append(model)
        return [(label, 1.0, 0, {}) for label, _ in jobs]

    monkeypatch.setattr(P, "run_layer", _spy)
    한번부르는단계().perform(P.RunContext(root=str(tmp_path), model="haiku"))
    assert 본것 == ["haiku"]


def test_LLM_단계는_층마다_세션마다_행을_낸다(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "run_layer", 가짜층({}))
    out = 두층부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert [r["stage"] for r in out.rows] == ["L0-B0", "L0-B1", "L1-B0", "L1-B1"]


def test_LLM_단계는_층이_실패하면_다음_층을_돌지_않는다(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "run_layer", 가짜층(None, rc=1))
    out = 두층부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.FAIL
    assert [r["stage"] for r in out.rows] == ["L0-B0", "L0-B1"]
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -k LLM_단계 -q`
Expected: FAIL — `AttributeError: module 'pipeline' has no attribute 'LlmStage'`

- [x] **Step 3: 구현을 쓴다**

`runner/pipeline.py` 의 `run_layer` 아래에 붙인다.

```python
class LlmStage(Stage[C]):
    """LLM Model을 부르는 단계. 훅 여섯 중 `prompt` 와 `repo` 만 필수다.

    팬아웃은 단일 호출의 일반화다 — 세션 하나짜리 단계는 `jobs` 의 기본값이
    자기 이름 하나를 담은 목록을 내므로 훅을 하나도 더 구현하지 않는다.

    `perform` 을 재정의하지 않는다 — 층을 도는 방식과 측정이 갈리면 안 된다.
    """
    emits = OK | FAIL

    @abstractmethod
    def prompt(self, ctx: C) -> str:
        ...

    @abstractmethod
    def repo(self, ctx: C) -> str:
        """`claude -p` 가 열 저장소이자 자식 프로세스의 작업 폴더."""

    def model(self, ctx: C) -> str:
        return ctx.model

    def rounds(self, ctx: C) -> int:
        return 1

    def jobs(self, ctx: C, rnd: int) -> list[tuple[str, str]]:
        return [(self.name, self.prompt(ctx))]

    def harvest(self, ctx: C, got: Sequence[JobResult], rnd: int) -> Outcome:
        """세션마다 행 하나. 하나라도 실패하면 층이 실패다."""
        rows: list[StageRow] = []
        ok_all = True
        for label, seconds, rc, result in got:
            ok, why = M.agent_verdict(rc, result)
            ok_all = ok_all and ok
            rows.append({"stage": label, "seconds": seconds,
                         "usage": M.normalize_usage(result), "ok": ok, "why": why})
        return Outcome(OK if ok_all else FAIL,
                       "" if ok_all else "세션이 실패했다", rows)

    def perform(self, ctx: C) -> Outcome:
        rows: list[StageRow] = []
        for rnd in range(self.rounds(ctx)):
            jobs = self.jobs(ctx, rnd)
            with M.Heartbeat(self.name):
                got = run_layer(self.model(ctx), self.repo(ctx), ctx.root, jobs,
                                concurrency=ctx.concurrency, timeout=ctx.timeout)
            out = self.harvest(ctx, got, rnd)
            rows.extend(out.rows)
            if out.kind != OK:
                return Outcome(out.kind, out.why, rows)
        return Outcome(OK, "", rows)
```

- [x] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q`
Expected: PASS — 38 passed

Run: `npm run typecheck:py`
Expected: `0 errors`

- [x] **Step 5: 커밋**

```bash
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "$(cat <<'EOF'
[add] : LLM 단계와 훅 여섯

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Mode 2 이주

**Files:**
- Modify: `runner/run_mode2.py`
- Test: `runner/test_run_mode2.py` (**기존 시험을 고치지 않는다.** `plan_stages` 는 그대로 남는다)

`plan_stages` 는 사라지지 않고 팩토리의 ① 이 된다(D9).

- [x] **Step 1: 실패하는 시험을 쓴다**

`runner/test_run_mode2.py` 끝에 붙인다.

```python
def test_그래프는_고른_단계만_담는다(tmp_path):
    ctx = R.Mode2Context(root=str(tmp_path), model="opus",
                         project=str(tmp_path), slug="s", folder=str(tmp_path),
                         spec_file="spec.md")
    g = R.build_mode2_graph(ctx, has_manuscript=False, only=None, skip=["check"])
    assert g.order == ["init", "agent", "build"]


def test_원고가_있으면_그래프에_agent_가_없다(tmp_path):
    ctx = R.Mode2Context(root=str(tmp_path), model="opus",
                         project=str(tmp_path), slug="s", folder=str(tmp_path),
                         spec_file="spec.md")
    g = R.build_mode2_graph(ctx, has_manuscript=True, only=None, skip=None)
    assert "agent" not in g.order


def test_그래프의_실패는_전부_멈춤이다(tmp_path):
    ctx = R.Mode2Context(root=str(tmp_path), model="opus",
                         project=str(tmp_path), slug="s", folder=str(tmp_path),
                         spec_file="spec.md")
    g = R.build_mode2_graph(ctx, has_manuscript=False, only=None, skip=None)
    assert g.next_of("build", P.FAIL) is None
    assert g.next_of("build", P.OK) == "check"


def test_build_만_고르면_이미_있는_파일이_given_이_된다(tmp_path):
    (tmp_path / "data.ts").write_text("x", encoding="utf-8")
    (tmp_path / "report.tsx").write_text("x", encoding="utf-8")
    ctx = R.Mode2Context(root=str(tmp_path), model="opus",
                         project=str(tmp_path), slug="s", folder=str(tmp_path),
                         spec_file="spec.md")
    g = R.build_mode2_graph(ctx, has_manuscript=False, only=["build"], skip=None)
    assert g.order == ["build"]


def test_build_만_고르는데_파일이_없으면_팩토리가_죽는다(tmp_path):
    import pytest
    ctx = R.Mode2Context(root=str(tmp_path), model="opus",
                         project=str(tmp_path), slug="s", folder=str(tmp_path),
                         spec_file="spec.md")
    with pytest.raises(P.GraphError) as e:
        R.build_mode2_graph(ctx, has_manuscript=False, only=["build"], skip=None)
    assert "산출물" in str(e.value)
```

`runner/test_run_mode2.py` 의 import 줄에 `pipeline` 을 더한다.

```python
import pipeline as P  # noqa: E402
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -k 그래프 -q`
Expected: FAIL — `AttributeError: module 'run_mode2' has no attribute 'Mode2Context'`

- [x] **Step 3: 구현을 쓴다**

`runner/run_mode2.py` 에 `import pipeline as P` 를 `import measure as M` 아래에 더하고,
`run_machine` 아래에 붙인다.

```python
# ── 5. 단계 기계 — 문맥 · 산출물 · 단계 넷 · 전이표 ─────────────────────
@dataclass
class Mode2Context(P.RunContext):
    """Mode 2 의 단계 사이를 건너다니는 값. 칸마다 이름과 형이 있다."""
    project: str = ""
    slug: str = ""
    folder: str = ""
    spec_file: str = ""
    doc_dir: str = "specs"
    terms_json: str | None = None


DATA_TS = P.Artifact[Mode2Context](
    "data.ts", lambda c: os.path.join(c.folder, "data.ts"))
REPORT_TSX = P.Artifact[Mode2Context](
    "report.tsx", lambda c: os.path.join(c.folder, "report.tsx"))
REPORT_HTML = P.Artifact[Mode2Context](
    "out/report.html", lambda c: os.path.join(c.folder, "out", "report.html"))

ARTIFACTS = [DATA_TS, REPORT_TSX, REPORT_HTML]


class Mode2Machine(P.MachineStage[Mode2Context]):
    """`init` · `build` · `check` — 셋 다 `viz/` 의 스크립트를 자식 프로세스로 부른다."""

    def argv(self, ctx: Mode2Context) -> list[str]:
        return script_argv(ctx.root, self.name, ctx.slug)

    def cwd(self, ctx: Mode2Context) -> str:
        return stage_cwd(self.name, ctx.project, ctx.folder)


class InitStage(Mode2Machine):
    name = "init"

    def writes(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]:
        return [DATA_TS, REPORT_TSX]


class BuildStage(Mode2Machine):
    name = "build"

    def reads(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]:
        return [DATA_TS, REPORT_TSX]

    def writes(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]:
        return [REPORT_HTML]


class CheckStage(Mode2Machine):
    name = "check"

    def reads(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]:
        return [REPORT_HTML]


class AgentStage(P.LlmStage[Mode2Context]):
    """세션 하나. `--add-dir` 로 프로젝트와 도구 저장소를 둘 다 열어 준다."""
    name = "agent"

    def prompt(self, ctx: Mode2Context) -> str:
        return agent_prompt(ctx.project, ctx.slug, ctx.spec_file, ctx.root,
                            ctx.terms_json, ctx.doc_dir)

    def repo(self, ctx: Mode2Context) -> str:
        return ctx.project

    def harvest(self, ctx: Mode2Context, got: Sequence[P.JobResult],
                rnd: int) -> P.Outcome:
        """LLM Model이 낸 글을 화면에 흘린 뒤 기본 거두기를 그대로 쓴다."""
        for _, _, _, result in got:
            text = M.as_str(result.get("result")) if result else ""
            if text:
                print(text)
        return super().harvest(ctx, got, rnd)


MODE2_STAGES: dict[str, P.Stage[Mode2Context]] = {
    "init": InitStage(), "agent": AgentStage(),
    "build": BuildStage(), "check": CheckStage()}

# 갈래는 지금 동작과 1:1 이다 — 성공하면 다음, 실패하면 멈춤.
MODE2_EDGES = P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT})


def build_mode2_graph(ctx: Mode2Context, has_manuscript: bool,
                      only: Iterable[str] | None,
                      skip: Iterable[str] | None) -> P.StageDagGraph[Mode2Context]:
    """진입점에서 부른다. 어긋나면 단계를 하나도 돌리지 않고 죽는다."""
    names = plan_stages(has_manuscript=has_manuscript, only=only, skip=skip)
    return P.build_graph("mode2", names, {n: MODE2_STAGES[n] for n in names},
                         MODE2_EDGES, P.existing(ARTIFACTS, ctx), ctx)
```

`runner/run_mode2.py` 머리에 `from dataclasses import dataclass` 를 더한다.

- [x] **Step 4: `main` 을 그래프와 드라이버로 갈아 끼운다**

`runner/run_mode2.py` 의 `main` 에서 `try: stages = plan_stages(...)` 부터
`break` 로 끝나는 루프까지를 아래로 바꾼다. **바깥 출력은 그대로 둔다.**

```python
    ctx = Mode2Context(root=ROOT, model=a.model, timeout=a.timeout,
                       project=project, slug=a.slug, folder=folder,
                       spec_file=spec_file, doc_dir=doc_dir, terms_json=terms_json)
    try:
        graph = build_mode2_graph(
            ctx, has_manuscript=has_manuscript,
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None)
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    print("프로젝트 %s" % project)
    print("보고서   %s" % folder)
    print("설계문서 %s" % spec_file)
    print("LLM Model %s · 단계 %s" % (a.model, " -> ".join(graph.order) or "(없음)"))
    print("이미 있는 것 — 뼈대 %s · 채워진 원고 %s · 용어집 재료 %s"
          % (data_src is not None, has_manuscript, bool(terms_json)))
    if a.dry_run:
        for s in graph.order:
            print("  %-6s cwd=%s" % (s, stage_cwd(s, project, folder)))
        print(graph.render())
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode2Context]().run(graph, ctx)

    out_html = os.path.join(folder, "out", "report.html")
    if any(r["stage"] == "build" and r["ok"] for r in rows) and os.path.exists(out_html):
        print("out/report.html — {:,} 바이트".format(os.path.getsize(out_html)))
```

`main` 의 그 위에 있던 `print("프로젝트 …")` 다섯 줄과 옛 `rows: list[M.StageRow] = []`
· `t_all = …` 줄은 지운다 — 위 블록이 그것을 대신한다.

- [x] **Step 5: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -q`
Expected: PASS — 기존 시험 전부 + 새 시험 5개

Run: `.venv/bin/python -m pytest runner/test_import_isolation.py -q && npm run typecheck:py`
Expected: PASS · `0 errors`

`--dry-run` 을 실제 저장소에서 눈으로 본다.

Run: `.venv/bin/python runner/run_mode2.py docs/superpowers llm-load-reduction --dry-run`
Expected: 옛 `  init   cwd=…` 줄들이 그대로 있고 그 아래 `흐름 mode2 — 단계 N` 이 붙는다

- [x] **Step 6: 커밋**

```bash
git add runner/run_mode2.py runner/test_run_mode2.py
git commit -m "$(cat <<'EOF'
[refactor] : mode 2 를 단계 기계로 이주

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: `run_mode1_5.py` 의 `Any` 20곳을 없앤다

**Files:**
- Modify: `runner/run_mode1_5.py`
- Test: `runner/test_run_mode1_5.py` (**기존 시험을 고치지 않는다** — 호출부는 그대로 통한다)

**이 Task 는 Mode 1.5 이주(Task 12)보다 먼저 온다.** 이주 코드가 `P.read_json` 이 낸
`object` 를 `validate_answers` 와 `answer_sheet` 에 넘기는데, 서명이 아직
`dict[str, Any] | None` 이면 `pyright` 가 그 자리에서 깨진다.

D11 의 처방을 그대로 쓴다 — 읽어 온 JSON 은 `object` 로 받고 `measure.py` 의
좁히기 도우미로 하나씩 확인한다. **`dict[str, Any]` 를 `dict[str, object]` 로 바꾸는 것이
아니라 `object` 로 바꾼다** — 최상위가 사전인지도 못 믿는 자리이기 때문이다.

- [x] **Step 1: 게이트를 먼저 빨갛게 만든다**

`test/test_no_any.py` 의 `COVERED` 에 두 줄을 더한다.

```python
COVERED = [
    "runner/measure.py",
    "runner/pipeline.py",
    "runner/run_mode1.py",
    "runner/run_mode1_5.py",
    "runner/run_mode2.py",
    "runner/run_grade.py",
    "runner/dispatch.py",
]
```

Run: `.venv/bin/python -m pytest test/test_no_any.py -q`
Expected: FAIL — `형 자리에 Any 가 남았다:` 아래 `runner/run_mode1_5.py` 20줄

- [x] **Step 2: 여섯 함수의 서명을 `object` 로 바꾼다**

`runner/run_mode1_5.py` 에서 아래를 그대로 바꾼다. **본문의 `isinstance` 검사는
이미 다 있으므로 손대지 않는다** — 형 주석만 내려온다.

| 지금 | 바꿀 것 |
|---|---|
| `answer_key: dict[str, Any] \| None` | `answer_key: object` |
| `def validate_questions(doc: dict[str, Any] \| None)` | `def validate_questions(doc: object)` |
| `terms: list[dict[str, Any] \| None] \| None = (doc or {}).get("terms")` | `terms: object = M.as_map(doc).get("terms")` |
| `qs: list[dict[str, Any] \| None] \| None = (entry or {}).get("questions")` | `qs: object = M.as_map(entry).get("questions")` |
| `choices: list[Any] \| None = (q or {}).get("choices")` | `choices: object = M.as_map(q).get("choices")` |
| `def unasked_known(candidates: dict[str, Any] \| None, doc: dict[str, Any] \| None)` | `def unasked_known(candidates: object, doc: object)` |
| `def answer_sheet(doc: dict[str, Any] \| None) -> dict[str, Any]` | `def answer_sheet(doc: object) -> AnswerSheet` |
| `def validate_answers(sheet: dict[str, Any] \| None, doc: dict[str, Any] \| None)` | `def validate_answers(sheet: object, doc: object)` |
| `def _read_json(path: str) -> Any` | `def _read_json(path: str) -> object` |
| `cand: dict[str, Any] = _read_json(p_cand) or {}` | `cand = M.as_map(_read_json(p_cand))` |
| `concepts: list[str] = cand.get("newConcepts") or []` | `concepts = [M.as_str(t) for t in (cand.get("newConcepts") or []) if isinstance(t, str)]` |
| `_read_json(p_key) or {}` | `_read_json(p_key)` — `split_new_concepts` 가 `object` 를 받는다 |

`(doc or {}).get(...)` 꼴은 전부 `M.as_map(doc).get(...)` 으로 바꾼다 —
`as_map` 은 열쇠가 문자열인 사전이 아니면 `{}` 를 낸다.

`from typing import Any` 줄을 지운다.

- [x] **Step 3: 우리가 내는 것에는 형을 못 박는다**

`answer_sheet` 는 **우리가 쓰는** 파일이므로 `object` 가 아니라 TypedDict 다.
`runner/run_mode1_5.py` 의 `answer_sheet` 위에 붙인다.

```python
class SheetQuestion(TypedDict):
    """`answer-sheet.json` 의 한 칸. 사람은 `UserAns` 에만 적는다."""
    QNum: int
    Term: str
    Question: str
    AnsChoices: dict[str, str]
    UserAns: str


class AnswerSheet(TypedDict):
    """정답을 뺀 기입란 전체. **`answer` 를 싣지 않는 것이 요점이다.**"""
    plan: str
    questions: list[SheetQuestion]
```

`answer_sheet` 본문을 바꾼다.

```python
def answer_sheet(doc: object) -> AnswerSheet:
    """`questions.json` 에서 사람이 채울 `answer-sheet.json` 을 만든다.

    **정답(`answer`)을 싣지 않는 것이 이 함수의 요점이다.** 사람은 `UserAns` 에 고른
    보기 번호만 적고, 맞힌 수는 기계가 센다.
    """
    questions: list[SheetQuestion] = []
    for q_dict in flatten_questions(M.as_map(doc)):
        q = M.as_map(q_dict.get("Raw"))
        raw_choices = q.get("choices")
        choices = raw_choices if isinstance(raw_choices, list) else []
        questions.append({
            "QNum": M.as_int(q_dict.get("QNum")),
            "Term": M.as_str(q_dict.get("Term")),
            "Question": M.as_str(q.get("ask")),
            "AnsChoices": {str(i + 1): M.as_str(c) for i, c in enumerate(choices)},
            "UserAns": "",
        })
    return {"plan": M.as_str(M.as_map(doc).get("plan")), "questions": questions}
```

`from typing import TypedDict` 를 import 에 더한다.

- [x] **Step 4: 게이트와 시험이 함께 초록인지 확인한다**

Run: `.venv/bin/python -m pytest test/test_no_any.py runner/test_run_mode1_5.py -q`
Expected: PASS — `Any` 0건 · Mode 1.5 시험 전부

Run: `npm run typecheck:py`
Expected: `0 errors`

`0 errors` 가 아니면 **`cast` 로 덮지 마라** — `isinstance` 를 하나 더 두어 좁힌다.
스키마를 *주장하는* `cast` 는 완료 조건 4가 0건을 요구한다.

- [x] **Step 5: 커밋**

```bash
git add runner/run_mode1_5.py test/test_no_any.py
git commit -m "$(cat <<'EOF'
[refactor] : mode 1.5 의 Any 를 object 와 좁히기로

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Mode 1.5 이주 — `gate` 단계가 `GATE` 갈래를 낸다

**Files:**
- Modify: `runner/run_mode1_5.py`
- Test: `runner/test_run_mode1_5.py`

사람 관문은 지금 루프 **밖**에 있다. 단계로 올리면 `GATE` 갈래가 살아나고
시뮬레이터의 검사 대상이 된다.

- [x] **Step 1: 실패하는 시험을 쓴다**

`runner/test_run_mode1_5.py` 끝에 붙인다.

```python
def test_답안이_없으면_그래프_끝에_관문이_붙는다(tmp_path):
    ctx = R.Mode15Context(root=str(tmp_path), model="opus",
                          plan=str(tmp_path / "p.md"), workdir=str(tmp_path))
    g = R.build_mode1_5_graph(ctx, has_candidates=False, has_answers=False,
                              only=None, skip=None)
    assert g.order == ["collect", "gate"]


def test_답안이_있으면_관문이_없다(tmp_path):
    ctx = R.Mode15Context(root=str(tmp_path), model="opus",
                          plan=str(tmp_path / "p.md"), workdir=str(tmp_path))
    g = R.build_mode1_5_graph(ctx, has_candidates=True, has_answers=True,
                              only=None, skip=None)
    assert g.order == ["grade", "emit"]


def test_관문은_GATE_로_흐름을_끝낸다(tmp_path):
    ctx = R.Mode15Context(root=str(tmp_path), model="opus",
                          plan=str(tmp_path / "p.md"), workdir=str(tmp_path))
    g = R.build_mode1_5_graph(ctx, has_candidates=False, has_answers=False,
                              only=None, skip=None)
    assert g.stages["gate"].emits & P.GATE
    assert g.next_of("gate", P.GATE) is None


def test_문항지가_없으면_관문은_아무것도_하지_않는다(tmp_path):
    ctx = R.Mode15Context(root=str(tmp_path), model="opus",
                          plan=str(tmp_path / "p.md"), workdir=str(tmp_path))
    out = R.GateStage().perform(ctx)
    assert out.kind == P.OK
    assert out.rows == []
    assert ctx.gate is None


def test_문항지가_있으면_관문이_기입란을_깔고_안내를_남긴다(tmp_path):
    (tmp_path / R.QUESTIONS).write_text(
        json.dumps(good_doc(), ensure_ascii=False), encoding="utf-8")
    ctx = R.Mode15Context(root=str(tmp_path), model="opus",
                          plan=str(tmp_path / "p.md"), workdir=str(tmp_path))
    out = R.GateStage().perform(ctx)
    assert out.kind == P.GATE
    assert os.path.exists(tmp_path / R.SHEET)
    assert ctx.gate is not None and R.ANSWERS in ctx.gate
```

`good_doc()` 은 `runner/test_run_mode1_5.py:44` 에 이미 있는 헬퍼다 — 잘 만들어진
문항지 한 벌을 낸다. 픽스처가 아니라 그냥 함수라 인자 없이 부른다.

import 줄에 `pipeline` 과 `json` · `os` 가 있는지 본다. 없으면 더한다.

```python
import pipeline as P  # noqa: E402
```

- [x] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode1_5.py -k 관문 -q`
Expected: FAIL — `AttributeError: module 'run_mode1_5' has no attribute 'Mode15Context'`

- [x] **Step 3: 구현을 쓴다**

`runner/run_mode1_5.py` 에 `import pipeline as P` 를 `import measure as M` 아래에
더하고, `run_machine` 아래에 붙인다.

```python
# ── 7. 단계 기계 — 문맥 · 단계 셋 · 사람 관문 ───────────────────────────
@dataclass
class Mode15Context(P.RunContext):
    """Mode 1.5 의 단계 사이를 건너다니는 값. 산출 파일 자리는 `workdir` 이 정한다."""
    plan: str = ""
    workdir: str = ""
    terms_db: str | None = None
    # 사람 관문이 남긴 안내. `format_run` 이 표 밖에 찍는다.
    gate: str | None = None

    @property
    def p_cand(self) -> str:
        return os.path.join(self.workdir, CANDIDATES)

    @property
    def p_key(self) -> str:
        return os.path.join(self.workdir, ANSWER_KEY)

    @property
    def p_ques(self) -> str:
        return os.path.join(self.workdir, QUESTIONS)

    @property
    def p_sheet(self) -> str:
        return os.path.join(self.workdir, SHEET)

    @property
    def p_ans(self) -> str:
        return os.path.join(self.workdir, ANSWERS)

    @property
    def p_grades(self) -> str:
        return os.path.join(self.workdir, GRADES)


CANDIDATES_ART = P.Artifact[Mode15Context](CANDIDATES, lambda c: c.p_cand)
GRADES_ART = P.Artifact[Mode15Context](GRADES, lambda c: c.p_grades)


class Mode15Machine(P.MachineStage[Mode15Context]):
    """세 단계 모두 `runner/term/` 의 스크립트를 자식 프로세스로 부른다."""

    def cwd(self, ctx: Mode15Context) -> str:
        return ctx.workdir


class CollectStage(Mode15Machine):
    name = "collect"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return collect_argv(ctx.root, ctx.plan, ctx.terms_db)

    def writes(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [CANDIDATES_ART]


class GradeStage(Mode15Machine):
    name = "grade"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return grade_argv(ctx.root, ctx.p_ans, ctx.p_ques)

    def reads(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        """채운 기입란이 문항지와 아귀가 맞는지 채점 **전에** 본다."""
        doc = P.read_json(ctx.p_ques)
        return [P.Artifact[Mode15Context](QUESTIONS, lambda c: c.p_ques,
                                          check=validate_questions),
                P.Artifact[Mode15Context](ANSWERS, lambda c: c.p_ans,
                                          check=lambda raw: validate_answers(raw, doc))]

    def writes(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [GRADES_ART]


class EmitStage(Mode15Machine):
    name = "emit"

    def argv(self, ctx: Mode15Context) -> list[str]:
        return emit_argv(ctx.root, ctx.p_grades)

    def reads(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]:
        return [GRADES_ART]


class GateStage(P.Stage[Mode15Context]):
    """사람 차례. 기입란을 깔아 두고 흐름을 멈춘다 — **실패가 아니다.**

    문항지가 아직 없으면 깔 것이 없으므로 `OK` 로 지나간다.
    """
    name = "gate"
    emits = P.OK | P.GATE

    def perform(self, ctx: Mode15Context) -> P.Outcome:
        doc = P.read_json(ctx.p_ques)
        if not M.as_map(doc):
            return P.Outcome(P.OK, "문항지가 아직 없다")
        with open(ctx.p_sheet, "w", encoding="utf-8") as f:
            json.dump(answer_sheet(doc), f, ensure_ascii=False, indent=2)
            f.write("\n")
        cand = P.read_json(ctx.p_cand)
        concepts = [M.as_str(t) for t in (M.as_map(cand).get("newConcepts") or [])
                    if isinstance(t, str)]
        _, held = split_new_concepts(concepts, P.read_json(ctx.p_key))
        ctx.gate = gate_notice(ctx.p_ques, ctx.p_sheet, ctx.p_ans, held, ctx.p_key,
                               unasked=unasked_known(cand, doc))
        return P.Outcome(P.GATE, "사람 차례")


MODE1_5_STAGES: dict[str, P.Stage[Mode15Context]] = {
    "collect": CollectStage(), "grade": GradeStage(), "emit": EmitStage(),
    "gate": GateStage()}

# 갈래는 지금 동작과 1:1 이다. `gate` 의 `GATE` 만 새 줄이고, 이것도 지금 루프 밖에서
# 하던 일에 이름을 붙인 것이다.
MODE1_5_EDGES = P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT,
                         ("gate", P.GATE): P.HALT})


def build_mode1_5_graph(ctx: Mode15Context, has_candidates: bool, has_answers: bool,
                        only: Iterable[str] | None,
                        skip: Iterable[str] | None) -> P.StageDagGraph[Mode15Context]:
    """진입점에서 부른다. 사람 차례가 안 끝났으면 `gate` 를 맨 뒤에 붙인다."""
    names = plan_stages(has_candidates=has_candidates, has_answers=has_answers,
                        only=only, skip=skip)
    if human_gate_open(has_answers):
        names = names + ["gate"]
    given = P.existing([CANDIDATES_ART, GRADES_ART], ctx) + [
        P.Artifact[Mode15Context](QUESTIONS, lambda c: c.p_ques),
        P.Artifact[Mode15Context](ANSWERS, lambda c: c.p_ans)]
    return P.build_graph("mode1_5", names, {n: MODE1_5_STAGES[n] for n in names},
                         MODE1_5_EDGES, given, ctx)
```

`runner/run_mode1_5.py` 머리에 `from dataclasses import dataclass` 를 더한다.

**`QUESTIONS` 와 `ANSWERS` 를 늘 `given` 에 넣는 이유** — 그 둘은 사람과 스킬이 만드는
것이라 어떤 단계도 쓰지 않는다. 실제로 있는지는 드라이버가 `missing_reads` 로 본다.

- [x] **Step 4: `main` 을 그래프와 드라이버로 갈아 끼운다**

`runner/run_mode1_5.py` 의 `main` 에서 `p_cand = …` 여섯 줄부터 `gate = gate_notice(…)`
블록 끝까지를 아래로 바꾼다.

```python
    ctx = Mode15Context(root=ROOT, model="", plan=plan, workdir=workdir,
                        terms_db=terms_db)
    try:
        graph = build_mode1_5_graph(
            ctx,
            has_candidates=os.path.exists(ctx.p_cand),
            has_answers=os.path.exists(ctx.p_ans),
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None)
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    # 표 밖에 적을 것 — 건너뛴 단계. 재개가 정상 흐름이라 늘 있다.
    reasons = {"collect": "%s 이 이미 있다" % CANDIDATES,
               "grade": "답안이 아직 없다", "emit": "답안이 아직 없다"}
    skipped = [(s, reasons[s]) for s in STAGES if s not in graph.order] \
        if not a.only else []

    print("계획서 %s" % plan)
    print("작업 폴더 %s" % workdir)
    print("단계 %s" % (" -> ".join(s for s in graph.order if s != "gate") or "(없음)"))
    print("이미 있는 것 — 후보 %s · 문항지 %s · 답안 %s"
          % (os.path.exists(ctx.p_cand), os.path.exists(ctx.p_ques),
             os.path.exists(ctx.p_ans)))
    if a.dry_run:
        for s, why in skipped:
            print("건너뜀 — %s (%s)" % (s, why))
        if human_gate_open(os.path.exists(ctx.p_ans)):
            print("사람 차례에서 멈출 예정이다 — 답안 %s 이 없다." % ctx.p_ans)
        print(graph.render())
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode15Context]().run(graph, ctx)
    gate = ctx.gate
```

**문항지 사전 검사는 그대로 둔다** — `main` 이 `if os.path.exists(p_ques):` 로
`validate_questions` 를 부르는 블록은 `ctx.p_ques` 로 이름만 바꾸고 자리를 지킨다.
그 검사는 `--dry-run` 보다 먼저 죽어야 하기 때문이다.

옛 지역 변수 `p_cand` … `p_grades` 여섯을 쓰던 나머지 자리를 전부 `ctx.p_*` 로 바꾼다.

Run: `grep -n "\bp_cand\b\|\bp_key\b\|\bp_ques\b\|\bp_sheet\b\|\bp_ans\b\|\bp_grades\b" runner/run_mode1_5.py`
Expected: `ctx.` 가 앞에 붙지 않은 자리가 없어야 한다

- [x] **Step 5: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode1_5.py -q`
Expected: PASS — 기존 시험 전부 + 새 시험 5개

Run: `.venv/bin/python -m pytest runner/test_import_isolation.py -q && npm run typecheck:py`
Expected: PASS · `0 errors`

- [x] **Step 6: 커밋**

```bash
git add runner/run_mode1_5.py runner/test_run_mode1_5.py
git commit -m "$(cat <<'EOF'
[refactor] : mode 1.5 를 단계 기계로 이주하고 사람 관문을 갈래로

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: 문서와 게이트를 새 구조에 맞춘다

**Files:**
- Modify: `runner/CLAUDE.md`
- Modify: `runner/README.md` (생성물 — 손으로 고치지 않는다)
- Modify: `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md`
- Modify: `docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md`

- [x] **Step 1: `runner/README.md` 를 다시 굽는다**

Run: `.venv/bin/python tools/gen_readme.py machine runner viz tools`
Run: `.venv/bin/python tools/gen_readme.py --check machine runner viz tools`
Expected: `4개 일치`

- [x] **Step 2: `runner/CLAUDE.md` 의 "무엇이 여기 있나" 표에 한 줄을 더한다**

`measure.py` 줄 아래에 넣는다.

```markdown
| `pipeline.py` | 세 실행기가 함께 쓰는 **단계 기계** — 갈래 넷 · `Stage` · 전이표 · `StageDagGraph` · 시뮬레이터 · 드라이버 한 벌. `measure.py` 와 같이 **`machine/` 을 import 하지 않는다** |
```

같은 파일의 "Gotcha" 절 아래에 붙인다.

```markdown
## 흐름은 진입점에서 미리 짓고 보장한다

`main()` 이 인자를 읽자마자 `build_*_graph()` 를 부른다. **어떤 자식 프로세스도 띄우기
전이다.** 팩토리가 `simulate()` 로 다섯을 보고 하나라도 어긋나면 `GraphError` 로 죽는다 —
완결성 · 매달림 · 비순환 · 도달성 · 산출물 사슬.

`--dry-run` 은 그 그래프를 `render()` 로 찍는다. 단계 이름의 나열이 아니라 폴백 간선까지
포함한 실제 흐름이다.

**전이표는 파이프라인 밖에 하나다.** `Stage` 는 자기 다음이 어딘지 모른다 — 흐름을
알려면 `MODE*_EDGES` 를 함께 본다. 대가로 흐름 전체가 한 화면에 있고 통째로 교체된다.

**`Pipeline.run` 은 재정의할 수 있다.** 다만 재정의는 루프를 다시 쓰는 자리가 아니라
`super().run()` 앞뒤에 자기 일을 붙이는 자리다. 지금 재정의하는 모드는 없다.
```

- [x] **Step 3: 사양의 Decision Log 를 판정 결과로 갱신한다**

`docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` 의 Decision Log 표에서
세 줄의 상태를 바꾼다.

| # | 바꿀 것 |
|---|---|
| D2 | `[제안됨]` → `[승인됨]` — 사용자 판정 (2026-09-09) |
| D5 | `[제안됨]` → `[승인됨]` — 사용자 판정 (2026-09-09) |
| D6 | `[제안됨]` → `[번복됨]` — 사용자가 **재정의 허용**을 골랐다 (2026-09-09) |

D6 절의 본문 아래에 붙인다.

```markdown
**뒤집힌 것 (2026-09-09).** 사용자가 재정의 허용을 골랐다. `run` 은 `@final` 없이
동작하는 기본 구현을 가진 보통 메서드로 둔다 — 재정의를 막지 않되, 재정의가 루프를
다시 쓰는 자리는 아니다. 2단계에서 실제로 재정의하는 모드는 없다. Mode 1.5 의 사람
관문은 재정의 대신 `GATE` 를 내는 `gate` 단계로 들어가, 갈래 넷 중 `GATE` 가 죽은
어휘가 되지 않고 시뮬레이터의 검사 대상이 된다.
```

D3 절 아래에 붙인다.

```markdown
**구현에서 하나 늘었다 — `repo(ctx)`.** `claude_argv` 와 자식 프로세스의 `cwd` 가 요구하는
저장소 경로가 모드마다 다른 칸에 있다(Mode 1 은 `ctx.repo`, Mode 2 는 `ctx.project`).
`RunContext` 에 올리면 Mode 1.5 에 뜻 없는 칸이 생긴다. `rulebasestage` 가 같은 이유로
`cwd(ctx)` 를 갖고 있으므로 대칭이다. 훅은 여섯이고 필수는 `prompt` 와 `repo` 둘이다.
```

"구현 현황" 표의 2단계 줄을 `docs/superpowers/plans/2026-09-08-runner-pipeline.md` ·
**✅ 완료** 로 바꾸고, 그 아래에 2단계가 실제로 바꾼 것을 실측으로 적는다
(시험 수 · `Any` 수 · 줄 수 — **돌려서 나온 숫자만 적는다**).

- [x] **Step 4: 재개 문서를 3단계 진입점으로 갱신한다**

`docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md` 에서:

- TL;DR 을 "2단계 완료. 다음은 3단계" 로 바꾼다
- "단계 현황" 표의 2단계를 **✅ 완료** 로, 계획서 경로를 채운다
- "2단계가 딛고 설 것" 절을 **"3단계가 딛고 설 것 — `runner/pipeline.py` 의 공개 API"** 로
  바꾸고 `pipeline.py` 의 실제 서명을 옮겨 적는다
- "아직 판정 안 난 제안 5건" 을 **2건(D14 · D16)** 으로 줄이고, D2 · D5 · D6 을
  "확정된 결정" 표로 옮긴다 (D6 은 **번복**으로 표시)
- 게이트 표를 다시 재서 갱신한다

- [x] **Step 5: 게이트 일곱을 전부 돌린다**

```bash
.venv/bin/python -m pytest -q
npm test
npm run typecheck
npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
npm run doctor
```

Expected:
- pytest — 511 + 새 시험(약 50) 통과 · 19 건너뜀 · **실패 0**
- npm test — 8 통과
- typecheck · typecheck:py — 통과 · `0 errors`
- gen_readme — `4개 일치`
- doctor — 필수 전부 있다

**`.venv/bin/python machine/xmldoc.py check` 는 돌리지 않는다.** 알려진 빨강이고
3단계 뒤에 `emit` → `inject` 한 번으로 푼다 — 재개 문서의 "xmldoc 은 3단계 뒤에 한 번" 절.

- [x] **Step 6: import 부작용이 그대로인지 눈으로 본다**

```bash
/opt/homebrew/bin/python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), 'runner'))
import run_mode2, run_mode1_5
print('prefix=%s networkx=%s' % (os.path.basename(sys.prefix), 'networkx' in sys.modules))"
```

Expected: `prefix=3.14 networkx=False`

- [x] **Step 7: 커밋**

```bash
git add runner/CLAUDE.md runner/README.md \
        docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md \
        docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md \
        docs/superpowers/plans/2026-09-08-runner-pipeline.md
git commit -m "$(cat <<'EOF'
[docs] : 2단계 완료를 모듈 문서와 사양 결정란에 반영

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## 완료 조건

| # | 무엇 | 어떻게 본다 |
|---|---|---|
| 1 | 게이트 여섯이 초록 | Task 13 Step 5. `xmldoc` 은 3단계 뒤 |
| 2 | import 부작용이 없다 | Task 13 Step 6 |
| 3 | `--dry-run` 이 그래프를 찍는다 | `run_mode2.py … --dry-run` 에 `흐름 mode2` 가 보인다 |
| 4 | 팩토리가 망가진 그래프 다섯을 거부한다 | `test_pipeline.py` 의 완결성 · 매달림 · 순환 · 도달성 · 산출물 시험 |
| 5 | 단계를 하나도 돌리지 않고 죽는다 | `test_팩토리는_어긋나면_단계를_하나도_돌리지_않고_죽는다` |
| 6 | `Any` 가 0 | `test/test_no_any.py` 의 `COVERED` 7파일 |
| 7 | 스키마를 **주장하는** `cast` 가 0건 | `grep -n "cast(" runner/*.py` 로 눈으로 본다. `cast(object, …)` 와 `isinstance` 뒤의 좁히기만 남아야 한다 |
| 8 | 드라이버 루프가 한 벌 | `grep -c "for stage in stages" runner/run_mode*.py` → `run_mode1.py` 만 1 (3단계에서 0이 된다) |

## 범위 밖 — 이번에 하지 않는 것

- **Mode 1 이주.** 3단계다. `run_mode1.py` 는 Task 8 에서 `run_layer` 를 내보내는 것 말고는 손대지 않는다
- **`lang-select` 쪼개기(D4) · `wiki` 쪼개기(D16) · 증분/전량 그래프(D13) · `prep` 판정(D15).** 전부 Mode 1 의 것이라 3단계다
- **재개 JSON(D12).** 스키마는 사양에 적혀 있으나 소비자가 Mode 1 이다. 3단계에서 `halt-with-resume` 과 함께 넣는다. **2단계에서 빈 껍데기를 만들지 마라**
- **`runner/wiki/` 와 `runner/term/` 의 `Any`.** 얼갈이라 범위 밖이다
- **`machine/xmldoc.py` 의 레퍼런스 복구.** 3단계 직후 한 번
- **Mode 2 의 원고 채움 검사.** `agent` 가 종료 코드 0 으로 끝나도 원고가 비어 있을 수 있고 지금은 아무도 그것을 안 본다. **2026-09-09 사용자 판정으로 2단계에서 넣지 않는다** — 동작 변경이라 사양의 "1:1" 선을 넘고, 예외는 3단계의 D13 하나로 이미 잡혀 있다. 구멍은 사양의 "위험" 절에 기록했다
- **새 갈래.** 넷 고정. 좋은 아이디어가 나와도 기록만 하고 사용자에게 보고한다

## 함정 — 이 작업에서 실제로 밟기 쉬운 것

- **거울 함정.** 계층 상태 · 가드 함수 · 이벤트 큐 · 플러그인 등록기 · 스키마 언어를 만들지 않는다. 형 인자는 `C` 하나뿐이다
- **`cast` 로 형 오류를 덮는 것.** `pyright` 가 불평하면 `isinstance` 를 하나 더 둔다. 스키마를 주장하는 `cast` 는 완료 조건 7이 0건을 요구한다
- **동작 변경이 섞여 들어가는 것.** 2단계의 전이표는 지금 동작과 **1:1** 이다. `gate` 단계조차 루프 밖에서 하던 일에 이름을 붙인 것이다. 기존 시험이 하나라도 깨지면 리팩터링이 아니다
- **`xmldoc check` 를 고치려는 것.** 리팩터링이 줄 번호를 밀 때마다 다시 밀린다. 1단계에서 예측 +9 에 실측 +38 이었다 — **정의를 지우면 아래 마커의 줄 번호가 전부 밀린다**
- **`git add -A`.** 이 저장소는 여러 작업이 같은 워킹 트리를 쓴다. 경로를 좁혀 add 한다
- **미추적 `runner/runner_presudo.md`.** 사용자가 손으로 쓴 메모다. 커밋하지 말고 지우지도 마라
