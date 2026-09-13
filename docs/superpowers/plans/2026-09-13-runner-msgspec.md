# 러너의 좁히기 도우미를 msgspec 으로 (안 맞으면 예외) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `runner/measure.py` 의 좁히기 도우미 다섯(`as_map` · `as_list` · `as_int` · `as_float` · `as_str`)을 없애고, 바깥 프로그램이 꼴을 정하는 JSON(LLM 결과 · 산출물 파일)을 **`msgspec` 이 `TypedDict` 로 검증**하게 한다. 꼴이 안 맞으면 조용히 기본값이 아니라 **예외**가 나고, 그 예외는 파이프라인 경계에서 잡혀 `FAIL` + 경로 있는 사유가 된다.

**Architecture:** 스키마는 이미 있는 `TypedDict` 들이다. 읽기는 `pipeline.load(path, T)` 한 함수(`msgspec.json.decode(type=T)`), 이미 파싱된 객체는 `msgspec.convert(obj, T)`. `Artifact.check`(불평 함수)는 `Artifact.schema`(형)로 바뀌고 `missing_reads` · `bad_writes` 가 그 형으로 검증한다. `Pipeline.run` 이 `stage.perform` 둘레에서 `msgspec.DecodeError` 를 받아 `FAIL` 로 바꾼다 — 예외를 잡는 자리는 **드라이버 하나**다. LLM 결과는 `run_agent_with` 가 `ClaudeResult` 형으로 디코드해 `AgentResult` 가 곧 `TypedDict` 가 된다.

**Tech Stack:** Python 3.14 · msgspec 0.21.1(🔵 설치됨) · pytest · pyright strict 1.1.413

---

## 실측 (🔵 2026-09-13) — 계획이 기대는 사실

- `as_*` 호출 **99곳 · 12파일**: `run_mode1_5.py` 24 · `test_measure.py` 19 · `measure.py` 16 · `mode1/diff.py` 7 · `mode1/survey.py` 5 · `mode1/resume.py` 4 · `mode1/context.py` 4 · `mode1/scan.py` 2 · `test_pipeline.py` 1 · `run_mode2.py` 1 · `mode1/wiki.py` 1 · `mode1/lang.py` 1.
- msgspec strict 동작: `bool`→`int` **거부** · `float`→`int` 거부 · `str`→`int` 거부 · `int`→`float` 허용 · `TypedDict(total=False)` 칸 없음 OK · 남는 칸 버림 · `None` 통째 거부 · `ValidationError ⊂ DecodeError`. 오류 문구에 경로가 붙는다(`at $.usage.input_tokens`).
- pyright strict 에서 `def load(path, t: type[T]) -> T` 에 `TypedDict` 를 넘기는 것 **0 errors**.
- **`machine/` 의 선언과 실물이 어긋난다.** `out/codegraph-raw/codegraph.json` 은 `survey_plan.CodeGraph` 로 검증 실패(`nodes[83].file` 이 `null`, 선언은 `NotRequired[str]`). `warmup.json` 은 `warmup.Manifest` 로 실패(`Entry.mtime` 없음). `survey-plan.json → SurveyPlan` · `changes.json → WarmupDiff` 는 통과. → 러너는 `codegraph.json` 을 **러너 소유의 느슨한 형**(최상위 `nodes` · `edges` 배열)으로만 검증한다 — 지금 `check_codegraph` 가 보던 만큼. 지문(`snapshot.json`)은 존재만 본다(지금과 같다). 기계축 어긋남은 **보고만** 한다(소유 밖).
- Mode 1.5 시험 62개는 `validate_questions` 등의 **의미 검사 문구**만 단정하고 꼴 오류 문구는 단정하지 않는다(🔵 grep 0건) — 꼴 검사를 msgspec 으로 바꿔도 시험이 안 깨진다.
- `requirements.txt:10` 에 `msgspec` 이 이미 있다(사용자가 넣음). `tools/doctor.py:45` 의 필수 모듈 목록에는 아직 없다.

## 실행 중 발견 (🔵 2026-09-13)

1. **msgspec 은 한글 열쇠 `TypedDict` 를 모듈 경계 너머에서 못 맞춘다.** `TypedDict("Buckets", {"유효": …})` 로 갈래 넷을 필수로 못 박으려던 것이 `json.loads` · `decode` 로 들어온 열쇠에 "missing required field `유효`" 로 죽었다. 같은 파일 리터럴(같은 인터닝 객체)일 때만 맞는다. ASCII 는 정상, `Struct` + `rename` 은 된다. → `WarmupDiff.verdicts` 는 `dict[str, list[str]]` 로 두고 넷이 다 있는 것은 `write_diff` 가 보장한다.
2. **`Artifact.check` 는 남긴다 — 뜻 검사용.** Mode 1.5 의 `validate_questions` · `validate_answers`(문항 수 · 정답 자리 · 빈 칸)는 형으로 못 적는다. `schema`(꼴) 를 먼저, 통과하면 `check`(뜻). `check_file(path, schema, check)`.
3. **시험 픽스처가 실제 형보다 성겼다.** `_plan_with` 의 심볼에 `id` · `line` · `kind` · `in_cycle` · `depends_on` 이 없어 `SurveyPlan` strict 검증에 걸렸다 → 실제 `PlanSymbol` 꼴로. `test_run_mode1.py` 의 LLM 결과 리터럴에 `"type"` · `"duration_ms"` 같은 안 읽는 칸이 있어 pyright 가 `TypedDict` 리터럴로 못 받았다 → 그 칸만 뺐다(4줄).
4. **옛 정책을 고정한 시험 하나를 뒤집었다** — `test_망가진_값은_예외가_아니라_0이다` → `…읽는_자리에서_거부된다`.

## 예외 정책 — 결정 하나

| 어디 | 안 맞으면 |
|---|---|
| 산출물 읽기·쓰기 검사(`missing_reads` · `bad_writes`) | `DecodeError` 를 잡아 불평 문자열 — 지금과 같은 자리, 문구만 경로가 붙는다 |
| 단계 본문 안(`P.load` · `msgspec.convert`) | **잡지 않는다.** `Pipeline.run` 이 `stage.perform` 둘레에서 잡아 `FAIL` 행으로 |
| LLM 결과(`run_agent_with`) | 디코드 실패는 지금처럼 `None`(→ "결과 JSON 을 읽지 못했다") + **stderr 에 경로 있는 사유** |
| 순수 함수(`validate_questions` 등 `object` 를 받는 것) | 안에서 `convert` 하고 `ValidationError` 를 불평 한 줄로 낸다 — 반환형이 `list[str]` 인 검사 함수라서 |

지금과 달라지는 것: LLM 이 `usage.input_tokens` 에 문자열을 내면 **지금은 0 토큰으로 표에 조용히 들어가고**, 뒤에는 세션 행이 실패로 남는다. 이것이 이 작업의 실익이다.

## 가드레일

- 본체 `.py` 는 고치기 전에 diff 를 보이고 사용자가 판단한다. 시험 파일은 그대로 진행.
- 커밋은 Task 마다. `[tag] : subject` · `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` · `git add -A` 금지.
- **`Any` 금지** 그대로 — `msgspec.convert` · `decode(type=T)` 는 `T` 를 낸다. `cast` 도 줄인다.
- `measure.py` · `pipeline.py` 는 `machine/` 을 import 하지 않는다(`test_import_isolation.py`). msgspec 은 C 확장 하나라 규약 안이다 — Task 1 에서 잰다.
- `machine/**` 은 소유 밖. `survey_plan.SurveyPlan` 처럼 실물이 통과하는 형만 빌려 쓴다.
- 공개 함수 이름·서명은 유지한다(`normalize_usage` · `agent_verdict` · `validate_questions` · `answer_sheet` · `validate_answers` · `unasked_known` · `split_new_concepts`). 파사드 `run_mode1.py` 의 재수출도 그대로.
- 기준선 🔵 2026-09-13: pytest 598 통과 · 실패 1(위키 인용, 기대됨) · 19 건너뜀 · pyright 0 · `xmldoc check` 339.

## File Structure

| 파일 | 바뀌는 것 |
|---|---|
| `tools/doctor.py` | 필수 모듈 목록에 `msgspec` |
| `runner/measure.py` | `ClaudeUsage` · `ClaudeResult` 형 · `parse_result` · `as_*` 5개 삭제 · `normalize_usage` · `agent_verdict` 형 위에서 |
| `runner/test_measure.py` | `as_*` 시험 7개 삭제 · `parse_result` 시험 4개 |
| `runner/pipeline.py` | `Artifact.check` → `schema` · `load` · `check_file` · `read_json` 삭제 · `run_agent_with` 형 디코드 · `Pipeline.run` 이 `DecodeError` 를 `FAIL` 로 |
| `runner/test_pipeline.py` | `check=` 람다 → `schema=` |
| `runner/mode1/context.py` | `check_*` 5개 → 형(`CodeGraphDoc` · `LangSelect` · `Outline`) · `Artifact(schema=…)` |
| `runner/mode1/diff.py` | `check_diff` · `read_diff` · `_str_list` 삭제 · `read_diff` 는 `P.load` 한 줄 |
| `runner/mode1/resume.py` | `read_resume` 를 `P.load` 로 |
| `runner/mode1/survey.py` · `scan.py` · `wiki.py` · `lang.py` · `graph.py` | `as_*` → 형 |
| `runner/test_mode1.py` | 바뀐 함수의 시험 |
| `runner/run_mode2.py` | `json.loads` → `M.parse_result` · `as_str` 한 곳 |
| `runner/run_mode1_5.py` | `QuestionsDoc` · `TermEntry` · `Question` · `Candidates` 형 · 24곳 · `_read_json` 삭제 |
| `runner/CLAUDE.md` · `docs/handoffs/RESUME-…` | 규약 갱신 · 기계축 어긋남 보고 |

---

### Task 1: 의존 — doctor · import 격리

**Files:** Modify `tools/doctor.py:45`

- [x] **Step 1:** `tools/doctor.py` 의 튜플 `('networkx','numpy','scipy','pytest')` 에 `'msgspec'` 을 더한다(한 줄).
- [x] **Step 2:** `npm run doctor` → "전부 있다". `.venv/bin/python -m pytest runner/test_import_isolation.py -q` 통과(아직 msgspec 을 import 하는 러너 코드는 없다 — 기준선).
- [x] **Step 3:** 커밋 — `git add requirements.txt tools/doctor.py` · `[chore] : msgspec 을 의존과 doctor 에 더한다` → 🔵 `89d7709`

---

### Task 2: `measure.py` — LLM 결과의 꼴을 선언하고 `as_*` 를 없앤다

**Files:** Modify `runner/measure.py` · `runner/test_measure.py`

- [x] **Step 1: 실패하는 시험** — `test_measure.py` 에서 `as_*` 를 쓰는 시험 7개(`test_문자열_열쇠_사전만_통과시킨다` · `test_정수가_아니면_0이다` · `test_수가_아니면_0점0이다` · `test_문자열이_아니면_빈_문자열이다` · `test_as_list_는_목록이_아니면_빈_목록이다` · `test_as_list_는_원소를_그대로_낸다` · `test_as_list_는_사본이라_원본을_건드리지_않는다`)를 지우고 더한다:

```python
import pytest
import msgspec


def test_결과_JSON_은_형으로_읽힌다():
    r = M.parse_result('{"result": "ok", "usage": {"input_tokens": 7}, "total_cost_usd": 1}')
    assert r["usage"]["input_tokens"] == 7 and r["total_cost_usd"] == 1.0   # int → float 는 허용


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
```

- [x] **Step 2: 실패 확인** — `AttributeError: module 'measure' has no attribute 'parse_result'`

- [x] **Step 3: 구현** — `measure.py` 머리 독스트링의 "`Any` 를 쓰지 않는다 … 좁히기 도우미로" 문장을 "바깥 프로그램이 꼴을 정하는 값은 `TypedDict` 로 선언하고 `msgspec` 이 검증한다. 안 맞으면 예외다." 로 바꾼다. `AgentResult = dict[str, object]` 를 아래로 바꾸고, `as_*` 5개와 그 절 머리를 지운다:

```python
import msgspec


class ClaudeUsage(TypedDict, total=False):
    """`claude -p --output-format json` 의 `usage`. 칸은 빠질 수 있고, 있으면 정수여야 한다."""
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


class ClaudeResult(TypedDict, total=False):
    """`claude -p --output-format json` 이 stdout 으로 내는 객체 하나.

    꼴을 정하는 것은 바깥 프로그램이라 칸은 전부 선택이고, 우리가 안 읽는 칸은 버린다.
    있는 칸의 형이 어긋나면 `msgspec.ValidationError` 다 — 조용히 0 으로 세지 않는다.
    """
    result: str
    usage: ClaudeUsage
    total_cost_usd: float
    num_turns: int
    duration_api_ms: int
    is_error: bool
    subtype: str


# 옛 이름. 세 실행기와 시험이 이 이름으로 부른다.
AgentResult = ClaudeResult


def parse_result(text: str | bytes) -> ClaudeResult:
    """`claude` 의 stdout 을 형으로 읽는다. 깨졌으면 `DecodeError`, 꼴이 틀리면 `ValidationError`."""
    return msgspec.json.decode(text, type=ClaudeResult)
```

```python
def normalize_usage(result: ClaudeResult | None) -> Usage:
    """…(독스트링 그대로)…"""
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
    }
    got["total"] = got["input"] + got["output"] + got["cache_read"] + got["cache_write"]
    return got
```

```python
def agent_verdict(returncode: int, result: ClaudeResult | None) -> tuple[bool, str]:
    """…(그대로)…"""
    if result is None:
        return False, "결과 JSON 을 읽지 못했다 (종료 코드 %d)" % returncode
    why = result.get("subtype") or "사유 없음"
    if returncode != 0:
        return False, "종료 코드 %d — %s" % (returncode, why)
    if result.get("is_error"):
        return False, "에이전트가 오류로 끝났다: %s" % why
    return True, ""
```

`from typing import … cast` 에서 `cast` 가 안 쓰이면 뺀다.

- [x] **Step 4:** `pytest runner/test_measure.py -q` → `18 passed`. **이 시점에 다른 파일은 아직 `M.as_*` 를 부르므로 전체 시험은 빨갛다** — Task 3~5 가 순서대로 푼다. 그래서 **Task 2 의 커밋은 Task 5 뒤에 한 번에** 한다(중간 커밋이 게이트를 깨지 않도록). pyright 는 `runner/measure.py runner/test_measure.py` 만 → `0 errors`.

---

### Task 3: `pipeline.py` — `Artifact.schema` · `load` · 드라이버가 예외를 받는다

**Files:** Modify `runner/pipeline.py` · `runner/test_pipeline.py`

- [x] **Step 1: 실패하는 시험** — `test_pipeline.py:93` 의 `check=lambda raw: …` 를 `schema=Terms` 로 바꾸고(`class Terms(TypedDict): terms: list[str]` 를 시험 파일에 둔다), 더한다:

```python
import msgspec


def test_load_는_형으로_읽고_틀리면_던진다(tmp_path: Path):
    p = tmp_path / "t.json"
    p.write_text('{"terms": ["a"]}', encoding="utf-8")
    assert P.load(str(p), Terms) == {"terms": ["a"]}
    p.write_text('{"terms": "a"}', encoding="utf-8")
    with pytest.raises(msgspec.ValidationError):
        P.load(str(p), Terms)


def test_쓴_산출물의_꼴이_틀리면_사유에_경로가_붙는다(tmp_path: Path):
    art = P.Artifact[P.RunContext]("t.json", lambda c: os.path.join(c.root, "t.json"), Terms)
    (tmp_path / "t.json").write_text('{"terms": [1]}', encoding="utf-8")
    class S(P.Stage[P.RunContext]):
        name = "s"
        def writes(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
            return [art]
        def perform(self, ctx: P.RunContext) -> P.Outcome:
            return P.Outcome(P.OK)
    bad = P.bad_writes(S(), P.RunContext(root=str(tmp_path), model="m"))
    assert len(bad) == 1 and "$.terms[0]" in bad[0]


def test_단계_안의_꼴_예외는_FAIL_행이_된다(tmp_path: Path):
    class S(P.Stage[P.RunContext]):
        name = "s"
        def perform(self, ctx: P.RunContext) -> P.Outcome:
            msgspec.convert({"terms": 1}, Terms)
            return P.Outcome(P.OK)
    g = P.build_graph("g", ["s"], {"s": S()}, P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), [], P.RunContext(root=str(tmp_path), model="m"))
    rows = P.Pipeline[P.RunContext]().run(g, P.RunContext(root=str(tmp_path), model="m"))
    assert rows[0]["ok"] is False and "$.terms" in rows[0]["why"]
```

- [x] **Step 2: 실패 확인** — `AttributeError: … 'load'` / `TypeError: … unexpected keyword 'schema'`

- [x] **Step 3: 구현**

```python
import msgspec

T = TypeVar("T")


@dataclass(frozen=True)
class Artifact(Generic[C]):
    """단계가 읽고 쓰는 파일 하나. 자리는 `ctx` 가 정하므로 경로를 박지 않는다.

    `schema` 가 `None` 이면 있는지만 본다 — `data.ts` 처럼 JSON 이 아닌 것과, 선언이 실물과
    어긋나 형으로 못 보는 것(지문 `snapshot.json`)이다. 있으면 그 형으로 읽혀야 통과한다.
    """
    name: str
    locate: Callable[[C], str]
    schema: type[object] | None = None


def load(path: str, t: type[T]) -> T:
    """JSON 파일을 형 `t` 로 읽는다. 없거나 깨졌거나 꼴이 틀리면 예외다 — 여기서 잡지 않는다."""
    with open(path, "rb") as f:
        return msgspec.json.decode(f.read(), type=t)


def check_file(path: str, schema: type[object]) -> list[str]:
    """`load` 를 불평 목록으로 바꾼다. 산출물 경계에서만 쓴다."""
    try:
        load(path, schema)
    except msgspec.DecodeError as e:
        return [str(e)]
    return []
```

`missing_reads` · `bad_writes` 의 `if art.check is not None: out.extend(… art.check(read_json(path)))` 를 `if art.schema is not None: out.extend("%s — %s" % (art.name, c) for c in check_file(path, art.schema))` 로. `read_json` 은 **Task 5 끝에** 지운다(그때까지 `mode1_5` 가 쓴다).

`Pipeline.run` 의 `out = stage.perform(ctx)` 를:

```python
                try:
                    out = stage.perform(ctx)
                except msgspec.DecodeError as e:
                    why = "산출물 꼴이 어긋났다 — %s" % e
                    out = Outcome(FAIL, why, [{"stage": cur, "seconds": time.monotonic() - t0,
                                               "usage": M.normalize_usage(None),
                                               "ok": False, "why": why}])
```

`run_agent_with` 의 `return seconds, p.returncode, cast(AgentResult, json.loads(p.stdout))` / `except (ValueError, TypeError)` 를:

```python
    try:
        return seconds, p.returncode, M.parse_result(p.stdout)
    except msgspec.DecodeError as e:
        print("[%s] 결과 JSON 이 꼴에 안 맞는다 — %s" % (label or "?", e), file=sys.stderr)
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print("[%s] %s" % (label or "?", tail), file=sys.stderr)
        return seconds, p.returncode, None
```

`import json` 이 안 쓰이면 뺀다. `JobResult` 의 `AgentResult` 는 이름이 그대로라 손댈 것 없다.

- [x] **Step 4:** `pytest runner/test_pipeline.py runner/test_measure.py -q` 통과 · pyright `runner/pipeline.py runner/measure.py` 0.

---

### Task 4: `mode1/` — 검사 함수를 형으로

**Files:** Modify `runner/mode1/context.py` · `diff.py` · `resume.py` · `survey.py` · `scan.py` · `wiki.py` · `lang.py` · `graph.py` · `runner/test_mode1.py`

- [x] **Step 1: 시험 갱신** — `test_mode1.py` 에서 `check_codegraph` · `check_batches` · `check_diff` · `read_diff` · `all_files` · `read_resume` 를 쓰는 단정을 아래로 바꾼다:

```python
def test_코드지도_검사는_최상위_열쇠만_본다(tmp_path: Path):
    p = tmp_path / "cg.json"
    p.write_text('{"nodes": [{"file": null}], "edges": [], "language": "py"}')   # 기계축 실물처럼 null 이 있어도 통과
    assert P.check_file(str(p), X.CodeGraphDoc) == []
    p.write_text('{"nodes": "x"}')
    assert P.check_file(str(p), X.CodeGraphDoc) != []


def test_층계획_검사는_실제_형으로_본다(tmp_path: Path):
    p = tmp_path / "b.json"
    p.write_text(json.dumps(_empty_plan()))
    assert P.check_file(str(p), X.BATCHES.schema) == []    # type: ignore[arg-type]
    p.write_text('{"layers": {}}')
    assert P.check_file(str(p), X.BATCHES.schema) != []    # type: ignore[arg-type]
```

`test_diff_검사는_넷_갈래가_다_있어야_통과한다` → `X.CHANGES.schema is D.WarmupDiff` 와 `P.check_file(path, D.WarmupDiff)` 로. `test_diff_는_넷_갈래와_범위를_담는다` 의 `D.read_diff(p)` 는 그대로(서명 유지, 구현만 `P.load`). `test_전량이면_targets_가_None_이다` 그대로. `all_files` 그대로.

- [x] **Step 2: 구현**

`context.py` — `check_*` 5개를 지우고 형 셋을 둔다(`Record` · `Records` · `WikiPage` 옆):

```python
class CodeGraphDoc(TypedDict):
    """`codegraph.json` 의 최상위만. 노드 안은 기계축 선언(`survey_plan.CodeGraph`)이 실물과 어긋나
    `null` 이 오므로 러너는 열지 않는다 — `survey_plan.plan` 이 받을 때 `cast` 한다."""
    nodes: list[dict[str, object]]
    edges: list[dict[str, object]]


class LangSelect(TypedDict):
    """`lang-select.json`. `language` 는 못 골랐으면 `null` 이다."""
    language: str | None
    collector: str


class Outline(TypedDict):
    """`outline.json`."""
    pages: list[WikiPage]
```

산출물 선언: `LANG_SELECT(…, LangSelect)` · `CODEGRAPH(…, CodeGraphDoc)` · `CHANGES(…, check_diff)` → `(…, WarmupDiff)`(import `from mode1.diff import WarmupDiff`) · `BATCHES(…, survey_plan.SurveyPlan)` · `READING(…, Records)` · `OUTLINE(…, Outline)` · `RESUME(…)` 는 `resume.py` 가 `context` 를 import 하지 않으므로 `from mode1.resume import ResumeDoc` 를 붙여 `(…, ResumeDoc)`. `SNAPSHOT` · `TERMS_DB` · `WIKI_DIR` 는 `None` 그대로. `import measure as M` 이 안 쓰이면 뺀다.

`diff.py` — `_str_list` · `check_diff` 삭제. `read_diff`:

```python
def read_diff(path: str) -> WarmupDiff | None:
    """없으면 `None`. 있는데 꼴이 틀리면 예외다."""
    return P.load(path, WarmupDiff) if os.path.exists(path) else None
```

`resume.py` — `read_resume`:

```python
def read_resume(path: str) -> ResumeDoc | None:
    return P.load(path, ResumeDoc) if os.path.exists(path) else None
```

(`rows` 는 이제 복원된다 — `list[StageRow]` 형이 있어 공짜다. `M` import 는 `StageRow` 때문에 남는다.)

`survey.py` — `load_records`: `return P.load(path, Records) if os.path.exists(path) else {}`. `plan_files(plan: survey_plan.SurveyPlan)`: `{f for L in plan["layers"] for b in L["batches"] for f in b["files"]}`. `compare_plan(plan: survey_plan.SurveyPlan, d)`. `qualified`: `where = str(rec.get("where") or "") if rec else ""`. `perform` 의 `raw = P.read_json(X.BATCHES.locate(ctx)); bad = X.check_batches(raw); … cast(…)` 셋을 `ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)` 한 줄로(예외는 드라이버가 받는다).

`scan.py` — `lang_for`: `sel = P.load(p, X.LangSelect) if os.path.exists(p := X.LANG_SELECT.locate(ctx)) else None; word = sel["language"] if sel else None` 꼴로. `lang_of` 의 `json.load(f).get("language")` 는 `msgspec.json.decode(f.read(), type=dict[str, object]).get("language")` 로(`Any` 가 아니라 `object` 가 나온다 — `isinstance(name, str)` 로 좁힌다).

`wiki.py` — `prepare`: `ctx.wiki_pages = P.load(X.OUTLINE.locate(ctx), X.Outline)["pages"]`; `perform` 의 `read_json + check_batches + cast` → `P.load(…, survey_plan.SurveyPlan)`. `M` import 를 뺀다.

`lang.py` — `harvest`: `word = ((result or {}).get("result") or "").strip().strip("\`.").lower()`.

`graph.py` — `perform`: `raw = P.read_json(…); bad = X.check_codegraph(raw); …; cg = cast(survey_plan.CodeGraph, raw)` → `cg = cast(survey_plan.CodeGraph, P.load(X.CODEGRAPH.locate(ctx), X.CodeGraphDoc))`. 이 `cast` 는 남는다 — 기계축 선언이 실물과 어긋나 있어서(위 실측).

- [x] **Step 3:** `pytest runner/test_mode1.py runner/test_run_mode1.py runner/test_pipeline.py runner/test_measure.py -q` 통과 · pyright `runner/mode1/ runner/pipeline.py runner/measure.py runner/run_mode1.py` 0.
- [x] **Step 4:** 실측 — `.venv/bin/python runner/run_mode1.py . --dry-run` 이 전과 같은 층 계획을 찍고, `--only warmup` 이 `changes.json` 을 낸다(LLM 0).

---

### Task 5: `run_mode2.py` · `run_mode1_5.py` — 남은 25곳 · `read_json` 삭제

**Files:** Modify `runner/run_mode2.py` · `runner/run_mode1_5.py` · `runner/pipeline.py`(`read_json` 삭제) · `runner/test_run_mode1_5.py`(필요할 때만)

- [x] **Step 1:** `run_mode2.py:327` `json.loads(p.stdout)` → `M.parse_result(p.stdout)`, `except (ValueError, TypeError)` → `except msgspec.DecodeError`. `:434` `M.as_str(result.get("result")) if result else ""` → `(result or {}).get("result", "")`.

- [x] **Step 2:** `run_mode1_5.py` — 형 넷을 `SheetQuestion` 위에 둔다:

```python
class Question(TypedDict, total=False):
    """`questions.json` 의 문항 하나. LLM 이 쓰고 사람이 손댈 수 있어 칸은 전부 선택이다 —
    있는 칸의 형만 msgspec 이 보고, 개수·자리·빈 문구는 `validate_questions` 가 본다."""
    ask: str
    choices: list[str]
    answer: int


class TermEntry(TypedDict, total=False):
    term: str
    means: str
    questions: list[Question]


class QuestionsDoc(TypedDict, total=False):
    plan: str
    terms: list[TermEntry]
    excluded: list[TermEntry]


class Candidates(TypedDict, total=False):
    """`term-candidates.json`."""
    known: dict[str, object]
    newConcepts: list[str]
```

`validate_questions(doc: object)`:

```python
    try:
        d = msgspec.convert(doc, QuestionsDoc)
    except msgspec.ValidationError as e:
        return ["문항지의 꼴이 틀리다 — %s" % e]
    terms = d.get("terms", [])
    if not terms:
        return ["문항지에 용어가 하나도 없다 — `terms` 배열이 비었거나 없다"]
    for i, 칸 in enumerate(terms):
        name = 칸.get("term", "").strip()
        …
        qs = 칸.get("questions", [])
        …
            choices = 물음.get("choices", [])
            …
            ans = 물음.get("answer")
            if ans is None or ans < 0 or ans >= len(choices):
```

(`isinstance(ans, int) or isinstance(ans, bool)` 는 msgspec 이 대신 한다 — `answer: int` 에 `bool` 이 오면 위에서 거부된다.) `_text` 는 `str(v or "")` 가 필요한 자리(`answer_sheet` 의 `Term` 등)에 남긴다.

`unasked_known(candidates: object, doc: object)` · `answer_sheet(doc: object)` · `validate_answers(sheet: object, doc: object)` · `split_new_concepts(…, answer_key: object)` · `flatten_questions(doc)` — 각각 첫 줄에서 `msgspec.convert(doc, QuestionsDoc)` / `convert(candidates, Candidates)` / `convert(answer_key, dict[str, object])` / `convert(sheet, AnswerSheet)` 를 하고 그 형으로 읽는다. `validate_answers` 는 `sheet` 의 꼴 오류를 `["기입란 파일이 아니다 — %s" % e]` 로 낸다(사람이 채우는 파일이라 예외가 아니라 불평이 맞다). `GateStage.perform` · `GradeStage` 등 `P.read_json(ctx.p_ques)` 는 `P.load(ctx.p_ques, QuestionsDoc)` (없으면 `os.path.exists` 로 먼저 본다 — 지금 "문항지가 아직 없다" 갈래). `_read_json` (517줄) 삭제.

- [x] **Step 3:** `pipeline.py` 의 `read_json` 을 지운다. `grep -rn "read_json\|as_map\|as_list\|as_int\|as_float\|as_str" runner/` → 0.
- [x] **Step 4:** `pytest -q` → 기준선과 같은 통과 수(위키 인용 1건만 빨강) · `npx pyright` 0 · `test_no_any` 통과.
- [x] **Step 5:** 커밋 둘 — `git add runner/measure.py runner/test_measure.py runner/pipeline.py runner/test_pipeline.py` · `[refactor] : llm 결과와 산출물을 msgspec 형으로 검증하고 좁히기 도우미를 뺀다` → 🔵 `bab8e6b` 그리고 `git add runner/mode1 runner/test_mode1.py runner/run_mode2.py runner/run_mode1_5.py runner/test_run_mode1_5.py` · `[refactor] : mode1 · 1.5 · 2 의 json 읽기를 형으로` → 🔵 `70e1e4a`. (Task 2~5 는 한 덩이로만 초록이 되므로 여기서 함께 커밋한다.)

---

### Task 6: 게이트 · 문서

- [x] **Step 1:** 게이트 일곱 — pytest · `npm test` · tsc · pyright · `xmldoc check`(수 적어 둠) · `gen_readme` 재생성 · doctor.
- [x] **Step 2:** `runner/CLAUDE.md` — `measure.py` 행의 "좁히기 도우미" → "LLM 결과 형(`ClaudeResult`)"; Gotcha "형 자리의 `Any` 는 pyright 가 안 잡는다" 절에 "바깥 JSON 은 `TypedDict` + `msgspec` 으로 읽는다. `as_*` 도우미는 없다. 안 맞으면 예외이고 `Pipeline.run` 이 `FAIL` 로 바꾼다" 한 줄. `pipeline.py` 행에 "`Artifact.schema`".
- [x] **Step 3:** `docs/handoffs/RESUME-2026-09-11-runner-stage-machine.md` 에 절 하나 — "기계축 선언이 실물과 어긋난다(🔵 2026-09-13)": `codegraph.json` ↔ `survey_plan.CodeGraph`(`GraphNode.file` 이 `null`), `warmup.json` ↔ `warmup.Manifest`(`mtime` 없음). 러너는 느슨한 형으로만 본다. 기계축 소유자 몫.
- [x] **Step 4:** 커밋 — `[docs] : msgspec 도입을 문서와 게이트에 반영`

## 완료 조건

- [x] `grep -rnE "\bas_(map|list|int|float|str)\(" runner/` → 0 · `read_json` 0 · `cast(` 는 `graph.py` 의 `CodeGraph` 한 곳 등 기계축 어긋남 때문인 것만
- [x] pytest — 🔵 597 통과 · 실패 1(위키 인용) 통과 수 ≥ 기준선 − 7(지운 `as_*` 시험) + 새 시험 · 실패는 위키 인용 1건뿐
- [x] `usage.input_tokens` 에 문자열이 오는 결과를 `parse_result` 에 넣으면 `ValidationError` 이고, 그 세션 행은 표에 "실패" 로 남는다(시험으로 고정)
- [x] `--dry-run` · `--only warmup` 실측이 Task 4 전과 같다
