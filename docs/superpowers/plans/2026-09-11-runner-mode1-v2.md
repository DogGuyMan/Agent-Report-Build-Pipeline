# Mode 1 을 단계 기계 위로 (3단계 · 개정 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `runner/run_mode1.py`(1,147줄)의 `if/elif` 단계 루프를 없애고, Mode 1 을 `runner/pipeline.py` 의 단계 기계 위에 올린다. 그 과정에서 `detect-changes` 의 판정을 `changes.json` 으로 내보내고(D14), 증분·전량 그래프를 팩토리가 고르게 하고(D13), 재개 JSON 을 넣는다(D12).

**Architecture:** `runner/mode1/` 패키지(D7 안 A). **계산과 프롬프트는 자유 함수가 아니라 그것을 쓰는 단계 클래스의 메서드다** — 한 단계만 쓰면 그 단계의 `@staticmethod`, 둘 이상이 쓰면 믹스인(인터페이스 = 메서드 서명, 구현 한 벌). 파일 꼴(읽기·쓰기·검사)만 산출물 옆(`context.py` · `diff.py`)에 산다. 단계 12개는 산출물 사슬을 따라 모듈 여섯(`lang` · `scan` · `graph` · `survey` · `terms` · `wiki`)에 나뉘고, `edges.py` 가 전이표와 팩토리를, `run_mode1.py` 는 `main` 과 옛 이름 재수출만 갖는다.

**Tech Stack:** Python 3.14 · pytest · pyright strict(1.1.413) · `runner/pipeline.py`(2단계 산출물)

**사양:** `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` 의 D4 · D7 · D12 · D13 · D14(×2) · D15 · D16
**앞선 판:** [`2026-09-11-runner-mode1.md`](2026-09-11-runner-mode1.md) — Task 1 은 그 판으로 끝났다(🔵 `f88265a`). Task 2 착수 직전에 사용자가 아래 판정을 내려 이 판으로 갈아탄다.
**사람용 요약:** [`2026-09-11-runner-mode1-요약.md`](2026-09-11-runner-mode1-요약.md) 의 §1~§3 은 그대로 유효하다. 달라진 것은 이 문서의 "개정 이유" 절이 전부다.

---

## 개정 이유 — 2026-09-11 사용자 판정: 자유 함수를 단계에 종속시킨다

앞선 판은 `layers.py`(층 계산 · 샤드 병합) 와 `prompts.py`(프롬프트) 를 **단계와 무관한 자유 함수 모음**으로 두고 단계 클래스가 그것을 부르게 했다. 사용자가 이것을 물렸다 — *"free function 을 각 단계에 종속시키고자 한다. 한 단계만 쓰면 그 단계에, 둘이 쓰면 인터페이스로."* 단일 책임(SRP)을 단계 단위로 세우려는 뜻이다.

### 규칙 R4 — 무엇이 어디에 사는가

| 것 | 어디 | 왜 |
|---|---|---|
| **한 단계만 쓰는** 계산 · 프롬프트 | 그 단계 클래스의 `@staticmethod` | 소비자가 하나면 그 옆이 자리다 |
| **둘 이상의 단계가 쓰는** 계산 | **믹스인 클래스** — 두 단계가 상속한다 | 인터페이스는 메서드 서명이고 구현은 한 벌이다 (아래 [제안됨] ①) |
| 파일 꼴 — 읽기 · 쓰기 · 검사(`check_*`) | 산출물 선언 옆 (`context.py` · `diff.py`) | `Artifact.check` 와 `main --dry-run` 이 단계 밖에서 읽는다 |
| 형 (`Record` · `Records` · `WikiPage` · `WarmupDiff`) | 산출물 옆 (`context.py` · `diff.py`) | 형은 파일 꼴의 일부다 |
| 행 하나 만들기(`row`) · 저장소를 cwd 로 하는 기계 단계 | `measured.py` 믹스인 · `machine_stage.py` 베이스 | 여섯 단계가 쓴다 |

**[제안됨] ① — 둘이 쓰는 것은 믹스인 한 벌로 둔다.** 사용자의 말은 *"인터페이스를 구현해서 각각 클래스 내부에 각각 동일 로직 구현"* 이었다. 이것을 글자 그대로 하면 `scan_snapshot`(옛 지문과 지금 소스 대조, 10줄)이 `DetectChangesStage` 와 `SnapshotSourcesStage` 에 **두 벌** 생긴다. 이 계획은 대신 `SnapshotScan` 믹스인 한 벌을 두 단계가 상속하게 한다 — 인터페이스(메서드 이름·서명)는 사용자 뜻대로 클래스에 속하고, 본문은 하나다. **권하지 않는 쪽의 이유:** 결함 ③④ 와 D15 둘째 걸음이 바로 이 훑기를 고칠 예정이라 두 벌이면 두 곳을 같이 고쳐야 한다. 💭 판정은 사용자 몫이다 — "복제" 로 판정하면 Task 7 의 `SnapshotScan` 을 `ABC` 로 바꾸고 두 클래스에 본문을 각각 적는다(Task 7 끝에 대안 코드가 있다).

### 함수 → 소속 대조표

| 옛 자유 함수 (`run_mode1.py`) | 새 자리 | 소비자 |
|---|---|---|
| `Record` · `Records` · `WikiPage` | `context.py` (형) | 여럿 |
| `reading_path` | `context.py` — `READING.locate` 가 이것을 쓴다 | 산출물 + `annotate-symbols` 프롬프트 |
| `LANG_ALIAS` · `lang_of` | `scan.py` `SnapshotScan` 믹스인 | `detect-changes` · `snapshot-sources` |
| `changed_seed` | `scan.py` `DetectChangesStage.changed_seed` | `detect-changes` |
| `plan_summary` | `graph.py` `ScheduleBatchesStage.plan_summary` | `schedule-batches` · `main --dry-run` |
| `wiki_argv` | `machine_stage.py` `Mode1Machine.wiki_argv` | `collect-graph` · `publish-wiki` · `verify-wiki` |
| `terms_argv` | `terms.py` `VerifyTermsStage.terms_argv` | `verify-terms` |
| `warmup_section` · `dep_excerpt` · `survey_batch_prompt` · `nonnode_prompt` | `survey.py` `AnnotateSymbolsStage.*` | `annotate-symbols` |
| `merge_shards` · `_qualified` (→ `qualified`) | `survey.py` `AnnotateSymbolsStage.*` | `annotate-symbols` |
| (신설) `load_records` · `plan_files` · `compare_plan` | `survey.py` `AnnotateSymbolsStage.*` | `annotate-symbols` |
| `wiki_catalogue_prompt` | `wiki.py` `OutlineWikiStage.wiki_catalogue_prompt` | `outline-wiki` |
| `symbol_layers` · `page_layers` · `wiki_page_prompt` | `wiki.py` `WriteWikiStage.*` | `write-wiki` |
| `run_lang_select` 의 프롬프트 문자열 | `lang.py` `LangHintStage.hint_prompt` | `lang-hint` |
| (신설) `lang_for` · `scan_snapshot` | `scan.py` `SnapshotScan` 믹스인 | `detect-changes` · `snapshot-sources` |
| `write_diff` · `read_diff` · `check_diff` · `all_files` | `diff.py` (파일 꼴) | 산출물 · `detect-changes` · `annotate-symbols` · `main` |

`_qualified` 는 클래스 안에서 `qualified` 로 이름을 바꾼다 — pyright strict 가 파사드의 `AnnotateSymbolsStage._qualified` 참조를 `reportPrivateUsage` 로 잡는다. 파사드가 옛 이름 `_qualified` 로 다시 내보내므로 시험은 그대로다.

### 앞선 판에서 그대로인 것

- **설계 메모 ①** — 전량 그래프에는 `detect-changes` 가 없다. `snapshot-sources` 가 직접 훑어 지문을 찍는다. 전이표는 하나다.
- **설계 메모 ②** — D15 첫 걸음은 "다시 수집할지의 판정" 뿐이다 (`prep.py --diff` · `--force`). **사용자 확인이 아직 없다** — 요약 §4-②.
- **이름 12개** — `lang-hint ▶ lang-decide ▶ detect-changes ▶ collect-graph ▶ schedule-batches ▶ annotate-symbols ▶ snapshot-sources ▶ verify-terms ▶ outline-wiki ▶ write-wiki ▶ publish-wiki ▶ verify-wiki`. 옛 이름은 `ALIASES` 로 `--only` 에서만 산다.
- **범위 밖** — D17 claim 파일 · `삭제됨` 기계 삭제 · 결함 ③④ · `collect-graph` 쪼개기(Task 5 끝에 판정 요청만).
- **Task 1** — 끝났다. `runner/mode1/context.py` · `runner/test_mode1.py` 가 있고 4개 시험이 통과한다.

### 앞선 판이 못 잡았던 결함 둘 — 이 판에서 고친다

1. **`READING` 산출물의 자리가 자기호스팅을 몰랐다.** 앞선 판의 `READING.locate` 는 늘 `<repo>/docs/codegraph/terms-reading.json` 이었다. 그런데 `reading_path()` 는 저장소가 도구 자신이면 `machine/terms-reading.json` 을 낸다(🔵 `runner/CLAUDE.md` Gotcha). 자기 위키를 다시 구울 때 단계는 `machine/` 쪽을 읽고 산출물 검사는 `docs/codegraph/` 쪽을 봐서 어긋난다. → Task 2 에서 `READING.locate` 가 `reading_path(c.repo, c.root)` 를 쓴다.
2. **프롬프트가 옛 파일 이름을 말한다.** `wiki_catalogue_prompt` 는 LLM 에게 `wiki-plan.json` 을 쓰라고 하고 재료로 `survey-plan.json` 을 가리키는데, 산출물은 `outline.json` · `batches.json` 이다. → Task 9 에서 프롬프트의 이름을 바꾼다. **`runner/test_run_mode1.py:757` 의 `assert "wiki-plan.json" in p` 한 줄이 이것을 고정하고 있다** — [제안됨] ② 그 한 줄을 `"outline.json"` 으로 바꾼다. "시험 파일을 고치지 않는다" 규칙의 유일한 예외이고, 옮긴 것도 없앤 것도 아니라 **사용자가 이름을 바꾼 것**이라 파사드로 살릴 수 없다.

## 가드레일

- **브랜치 `refactor/runner-common-axis`.** `main` 에서 하지 않는다.
- **파이썬 본체 파일을 고치기 전에 diff 를 보이고 승인을 받는다** (2026-09-11 세션 규칙). 시험 파일(`test_*.py`)은 승인 없이 진행한다. 서브에이전트에 시킬 때는 "구현 전에 diff 를 보고하고 승인을 기다려라" 를 프롬프트에 넣는다.
- **커밋은 각 Task 끝에서.** `[tag] : subject` 소문자 한 줄 한국어, 빈 줄, `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. **`git add -A` 금지** — 경로를 좁힌다. 미추적 `runner/runner_presudo.md` · `docs/overturn/2026-07-05-…` 는 담지 않는다.
- **`# <include …/>` 블록은 손대지 않고 새로 심지 않는다.** 정의를 옮기면 그 위 세 줄 블록은 **함께 지운다.** `xmldoc check` 의 문제 수가 느는 것은 예상된 결과다(착수 전 🔵 **266**).
- **`Any` 금지.** `object` + `measure.as_map/as_list/as_str/as_int`. `test/test_no_any.py` 의 `COVERED` 에 새 파일 전부(Task 13).
- **코드 주석에는 현 상황만.** 날짜 · 수치 · 확신도 · 설계 철학 금지. 옮기는 함수의 독스트링은 그대로 따라간다.
- **`runner/test_run_mode1.py`(963줄)는 고치지 않는다** — [제안됨] ② 의 한 줄과 Task 12 의 "없앤 이름의 시험 삭제" 만 예외. 옮긴 이름은 전부 파사드로 살린다.
- **옮기는 Task(5~9)마다 `run_mode1.py` 의 원본을 지우고 파사드 한 줄을 넣는다.** 옛 `run_*` 함수는 파사드 이름으로 계속 돌다가 Task 12 에서 통째로 지운다.
- **실제 `annotate-symbols` 를 돌려 검증하지 마라.** 세션당 약 $0.5. `--dry-run` 과 순수 함수 시험까지만.
- 기준선 🔵 2026-09-11: `pytest` **566 통과 · 19 건너뜀**(562 + Task 1 의 4) · `test_run_mode1.py` **74 통과** · `xmldoc check` 문제 **266**.

## File Structure

| 파일 | 책임 | 상태 |
|---|---|---|
| `runner/mode1/__init__.py` | 빈 파일 | ✅ Task 1 |
| `runner/mode1/context.py` | `ROOT` · `Mode1Context` · 형 셋 · `reading_path` · 산출물 10개 · `check_*` | ✅ Task 1 → Task 2 보강 |
| `runner/mode1/measured.py` | `Measured` 믹스인 — 측정 표의 행 하나 | Task 2 |
| `runner/mode1/machine_stage.py` | `Mode1Machine` — 저장소가 cwd 인 자식 프로세스 단계 · `wiki_argv` | Task 2 |
| `runner/mode1/diff.py` | `WarmupDiff` 형 · `write_diff` · `read_diff` · `check_diff` · `all_files` | Task 3 |
| `runner/wiki/prep.py` | `--diff` · `--force` · `needs_collect` | Task 4 (D15 첫 걸음) |
| `runner/mode1/graph.py` | `CollectGraphStage` · `ScheduleBatchesStage`(+`plan_summary`) | Task 5 |
| `runner/mode1/terms.py` | `VerifyTermsStage`(+`terms_argv`) | Task 5 |
| `runner/mode1/wiki.py` | `PublishWikiStage` · `VerifyWikiStage` (Task 5) · `OutlineWikiStage` · `WriteWikiStage` (Task 9) | Task 5 · 9 |
| `runner/mode1/lang.py` | `LangHintStage`(+`hint_prompt`) · `LangDecideStage` | Task 6 |
| `runner/mode1/scan.py` | `SnapshotScan` 믹스인 · `DetectChangesStage`(+`changed_seed`) · `SnapshotSourcesStage` | Task 7 |
| `runner/mode1/survey.py` | `AnnotateSymbolsStage` — 프롬프트 넷 · 샤드 병합 · diff 대조 | Task 8 |
| `runner/mode1/edges.py` | `ORDER` · `WARM_ONLY` · `ALIASES` · `STAGES` · `EDGES` · `expand` · `plan_stages` · `build_mode1_graph` | Task 10 |
| `runner/mode1/resume.py` | `ResumeDoc` · `write_resume` · `read_resume` · `start_stage` | Task 11 |
| `runner/run_mode1.py` | `main` + argparse + 파사드. `_bootstrap_venv` 그대로 | Task 2·5~9 파사드 · Task 12 축소 |
| `runner/test_mode1.py` | 위 전부의 시험 | 매 Task |

**시험 파일 머리(Task 1 에서 만든 것) 에 모듈 별명을 더해 간다.** 최종 모습:

```python
"""`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
import measure as M  # noqa: E402
import pipeline as P  # noqa: E402
from mode1 import context as X  # noqa: E402
from mode1 import diff as D  # noqa: E402
from mode1 import edges as E  # noqa: E402
from mode1 import graph as G  # noqa: E402
from mode1 import lang as LG  # noqa: E402
from mode1 import machine_stage as MC  # noqa: E402
from mode1 import measured as MS  # noqa: E402
from mode1 import resume as Z  # noqa: E402
from mode1 import scan as SC  # noqa: E402
from mode1 import survey as SV  # noqa: E402
from mode1 import terms as T  # noqa: E402
from mode1 import wiki as W  # noqa: E402
```

각 Task 의 Step 1 은 "이 Task 가 더하는 import 한 줄" 을 적는다. 아직 없는 모듈을 미리 import 하면 수집이 죽으므로 **그 Task 에서만** 더한다.

---

### Task 2: 형 · `reading_path` · `READING` 자리 고침 · `measured.py` · `machine_stage.py`

**Files:**
- Modify: `runner/mode1/context.py`
- Create: `runner/mode1/measured.py` · `runner/mode1/machine_stage.py`
- Modify: `runner/run_mode1.py` (원본 지우고 파사드)
- Test: `runner/test_mode1.py`

- [x] **Step 1: 실패하는 시험** — `test_mode1.py` 머리에 `import time` · `from mode1 import machine_stage as MC` · `from mode1 import measured as MS` 를 더하고 끝에:

```python
# ── 2. 형 · 읽기 레코드 자리 · 바닥 ──────────────────────────────────────


def test_읽기_레코드_자리는_자기호스팅만_다르다(tmp_path: Path):
    self_hosted = X.Mode1Context(root=str(tmp_path), model="m", repo=str(tmp_path))
    assert X.READING.locate(self_hosted) == os.path.join(str(tmp_path), "machine", "terms-reading.json")
    other = _ctx(tmp_path)   # root="/r" 는 저장소가 아니다
    assert X.READING.locate(other) == os.path.join(str(tmp_path), "docs", "codegraph", "terms-reading.json")


def test_측정_행은_단계_이름과_토큰_0_을_담는다():
    class T(MS.Measured):
        name = "t"
    r = T().row(time.monotonic(), True, "x")
    assert r["stage"] == "t" and r["ok"] is True and r["why"] == "x" and r["usage"]["total"] == 0


def test_기계_단계는_저장소를_cwd_로_한다(tmp_path: Path):
    class T(MC.Mode1Machine):
        name = "t"
        def argv(self, ctx: X.Mode1Context) -> list[str]:
            return ["true"]
    assert T().cwd(_ctx(tmp_path)) == str(tmp_path)
    assert MC.Mode1Machine.wiki_argv(
        "py", "/root", "prep.py", "/repo") == ["py", "/root/runner/wiki/prep.py", "/repo"]
    assert os.path.isdir(os.path.join(X.ROOT, "runner", "mode1"))   # 도구 뿌리는 셋 위다
```

- [x] **Step 2: 실패 확인** — `.venv/bin/python -m pytest runner/test_mode1.py -q` → `ImportError: cannot import name 'machine_stage' from 'mode1'`

- [x] **Step 3: `context.py` 보강** — 머리의 `Records = …` · `Pages = …` 를 아래로 바꾸고, `READING` 을 고친다:

```python
"""Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다."""
import os
from dataclasses import dataclass, field
from typing import NotRequired, TypedDict

import measure as M
import pipeline as P
import survey_plan
import warmup

# 레코드의 칸은 배치 세션이 채우므로 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
Record = dict[str, object]
Records = dict[str, Record]


class WikiPage(TypedDict):
    """`outline.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다."""

    file: str
    title: NotRequired[str]
    symbols: NotRequired[list[str]]


Pages = list[WikiPage]


def _no_records() -> Records:
    """`field(default_factory=dict)` 는 원소 형을 잃는다. 형이 붙은 빈 사전을 낸다."""
    return {}


def _no_pages() -> Pages:
    return []


def _no_ints() -> list[int]:
    return []


def _no_levels() -> dict[str, int]:
    return {}
```

`Mode1Context` 의 `wiki_pages: Pages` · `wiki_done: Pages` 는 그대로다(`Pages` 의 뜻이 `list[WikiPage]` 로 바뀐 것뿐). `check_reading` 아래, 산출물 선언 위에 `run_mode1.py` 의 `reading_path` 를 **본문 그대로** 옮긴다:

```python
def reading_path(repo: str, root: str) -> str:
    """전수조사 원본 `terms-reading.json` 의 자리.

    대상 저장소는 `<repo>/docs/codegraph/` 아래에 둔다. **이 저장소 자신만 다르다** —
    자기 것은 `machine/` 으로 옮겨져 있어 자기호스팅일 때 자리가 갈린다.
    """
    if os.path.abspath(repo) == os.path.abspath(root):
        return os.path.join(root, "machine", "terms-reading.json")
    return os.path.join(repo, "docs", "codegraph", "terms-reading.json")
```

`READING` 선언을 바꾼다:

```python
READING = P.Artifact[Mode1Context](
    "terms-reading.json", lambda c: reading_path(c.repo, c.root), check_reading)
```

- [x] **Step 4: `measured.py` · `machine_stage.py` 신설** — `ROOT` 는 `context.py` 로 간다(`import warmup` 아래, 경로 사실이 사는 자리)

`runner/mode1/measured.py`:

```python
"""측정 표의 행을 스스로 내는 단계의 믹스인."""
import time

import measure as M


class Measured:
    """측정 표의 행(`measure.StageRow`) 하나를 스스로 내는 단계 — 토큰 0, 자기 이름, 경과 초.

    기계 단계는 `MachineStage.perform` 이, LLM 단계는 `LlmStage.harvest` 가 행을 만든다.
    같은 프로세스의 파이썬 단계와, `perform` 을 앞에서 가로채 실패나 건너뜀을 내는
    LLM 단계는 스스로 만들어야 하므로 이것을 상속한다.
    """
    name: str = ""

    def row(self, t0: float, ok: bool, why: str = "") -> M.StageRow:
        return {"stage": self.name, "seconds": time.monotonic() - t0,
                "usage": M.normalize_usage(None), "ok": ok, "why": why}
```

`runner/mode1/machine_stage.py`:

```python
"""자식 프로세스 하나를 띄우는 Mode 1 단계의 베이스. 대상 저장소가 작업 폴더다."""
import os

import pipeline as P
from mode1.context import Mode1Context


class Mode1Machine(P.MachineStage[Mode1Context]):
    """자식 프로세스 하나. 대상 저장소가 작업 폴더다."""

    def cwd(self, ctx: Mode1Context) -> str:
        return ctx.repo

    @staticmethod
    def wiki_argv(python: str, root: str, script: str, repo: str) -> list[str]:
        """`runner/wiki/*.py` 하나를 부른다."""
        return [python, os.path.join(root, "runner", "wiki", script), repo]
```

`context.py` 의 `import warmup` 아래에:

```python
# 이 파일은 <ROOT>/runner/mode1/ 에 있다. 저장소 뿌리는 그 셋 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

`wiki_argv` 는 `run_mode1.py` 의 것을 본문 그대로 옮긴 것이다(`@staticmethod` 한 줄만 붙는다).

- [x] **Step 5: `run_mode1.py` 에서 원본을 지우고 파사드를 넣는다** — 지우는 것: `Record` · `Records` (그 위 주석 포함) · `WikiPage` · `reading_path` · `wiki_argv` 의 정의와 각각의 `# <include …/>` 세 줄 블록, `# ── 이 파일이 정하는 형 이름은 …` 주석 3줄, `# ── 2. 에이전트 호출` · `# ── 3. 기계 단계의 명령줄` 절 머리. `from measure import (…)` 블록 바로 아래에:

```python
# 형 · 자리 · 바닥의 원본은 `mode1/` 패키지다. 옛 이름으로 부르는 시험이 있어 그대로 다시 내보낸다.
from mode1.context import (  # noqa: E402,F401
    Record as Record, Records as Records, WikiPage as WikiPage, reading_path,
)
from mode1.machine_stage import Mode1Machine  # noqa: E402
wiki_argv = Mode1Machine.wiki_argv
```

`from typing import NotRequired, TypedDict, cast` 에서 `NotRequired` · `TypedDict` 가 안 쓰이게 되면 뺀다(pyright 가 `reportUnusedImport` 로 알려 준다).

- [x] **Step 6: 통과 확인** — `.venv/bin/python -m pytest runner/test_mode1.py runner/test_run_mode1.py -q` → `7 passed` + `74 passed`
- [x] **Step 7: 형 검사** — `npx --yes pyright@1.1.413 runner/mode1/ runner/run_mode1.py runner/test_mode1.py` → `0 errors`
- [ ] **Step 8: 커밋** — `git add runner/mode1/context.py runner/mode1/measured.py runner/mode1/machine_stage.py runner/run_mode1.py runner/test_mode1.py` · `[refactor] : mode1 형과 읽기 레코드 자리, 단계 바닥`

---

### Task 3: `changes.json` — 파일 꼴 (D14)

**Files:**
- Create: `runner/mode1/diff.py`
- Modify: `runner/mode1/context.py` (`CHANGES` 에 `check_diff`)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import diff as D`, 끝에:

```python
# ── 3. changes.json 의 꼴 ────────────────────────────────────────────────


def _verdicts() -> dict[str, list[str]]:
    return {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": ["gone.py"]}


def test_diff_는_넷_갈래와_범위를_담는다(tmp_path: Path):
    p = str(tmp_path / "changes.json")
    D.write_diff(p, _verdicts(), targets=["b.py"], hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None
    assert got["targets"] == ["b.py"] and got["verdicts"]["삭제됨"] == ["gone.py"]


def test_전량이면_targets_가_None_이다(tmp_path: Path):
    p = str(tmp_path / "d.json")
    D.write_diff(p, _verdicts(), targets=None, hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None and got["targets"] is None


def test_diff_검사는_넷_갈래가_다_있어야_통과한다():
    assert D.check_diff({"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}) == []
    assert D.check_diff({"verdicts": {"유효": []}, "targets": None, "hops": 1, "tracked": 0}) != []
    assert X.CHANGES.check is D.check_diff


def test_전체_파일_집합은_삭제됨을_뺀_셋의_합이다():
    d: D.WarmupDiff = {"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}
    assert D.all_files(d) == {"a.py", "b.py"}
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.diff'`

- [ ] **Step 3: `diff.py` 신설**

```python
"""`changes.json` 의 꼴. 옛 판(지문)과 새 판(지금 소스)을 대조한 결과가 여기 남는다."""
import json
import os
from typing import TypedDict

import measure as M
import pipeline as P
import warmup

BUCKETS = ("유효", "재읽기", "위치만", "삭제됨")


class WarmupDiff(TypedDict):
    """`targets` 가 `None` 이면 판정 불가 = 전량이다."""
    verdicts: warmup.Verdicts
    targets: list[str] | None
    hops: int
    tracked: int


def write_diff(path: str, verdicts: warmup.Verdicts, targets: list[str] | None,
               hops: int, tracked: int) -> WarmupDiff:
    doc: WarmupDiff = {"verdicts": verdicts, "targets": targets, "hops": hops, "tracked": tracked}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    return doc


def _str_list(v: object) -> list[str] | None:
    if not isinstance(v, list):
        return None
    items = [x for x in M.as_list(v) if isinstance(x, str)]
    return items if len(items) == len(M.as_list(v)) else None


def check_diff(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["diff 가 객체가 아니다"]
    out: list[str] = []
    v = M.as_map(top.get("verdicts"))
    for b in BUCKETS:
        if _str_list(v.get(b)) is None:
            out.append("`verdicts.%s` 가 문자열 배열이 아니다" % b)
    t = top.get("targets")
    if t is not None and _str_list(t) is None:
        out.append("`targets` 가 `null` 도 문자열 배열도 아니다")
    if M.as_int(top.get("tracked")) < 0:
        out.append("`tracked` 가 정수가 아니다")
    return out


def read_diff(path: str) -> WarmupDiff | None:
    raw = P.read_json(path)
    if check_diff(raw):
        return None
    top = M.as_map(raw)
    v = M.as_map(top.get("verdicts"))
    verdicts: warmup.Verdicts = {b: _str_list(v.get(b)) or [] for b in BUCKETS}
    t = top.get("targets")
    return {"verdicts": verdicts, "targets": None if t is None else (_str_list(t) or []),
            "hops": M.as_int(top.get("hops")), "tracked": M.as_int(top.get("tracked"))}


def all_files(d: WarmupDiff) -> set[str]:
    """지금 존재하는 추적 파일 전체. `삭제됨` 은 뺀다."""
    v = d["verdicts"]
    return set(v["유효"]) | set(v["재읽기"]) | set(v["위치만"])
```

`context.py` 의 `CHANGES` 를 바꾼다 — `diff.py` 는 `context` 를 import 하지 않으므로 순환이 없다. import 는 `import warmup` 아래에:

```python
from mode1.diff import check_diff
```

```python
CHANGES = P.Artifact[Mode1Context](
    "changes.json", lambda c: os.path.join(raw_dir(c), "changes.json"), check_diff)
```

- [ ] **Step 4: 통과** `11 passed` · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/diff.py runner/mode1/context.py runner/test_mode1.py` · `[add] : warmup 판정을 changes.json 으로 내보내는 꼴과 검사`

---

### Task 4: `collect-graph` 가 diff 를 읽는다 (D15 첫 걸음)

**Files:**
- Modify: `runner/wiki/prep.py`
- Test: `runner/test_mode1.py`

앞선 판의 Task 4 와 같다. 사용자 확인(요약 §4-②)이 아직 없으므로 **착수 전에 한 번 더 묻는다.**

- [ ] **Step 1: 실패하는 시험**

```python
# ── 4. prep 이 diff 로 재수집 여부를 정한다 ─────────────────────────────


def test_prep_은_diff_에_바뀐_것이_있으면_다시_수집한다():
    sys.path.insert(0, os.path.join(ROOT, "runner", "wiki"))
    import prep
    fresh = {"유효": ["a.py"], "재읽기": [], "위치만": [], "삭제됨": []}
    stale = {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []}
    assert prep.needs_collect(has_codegraph=True, verdicts=fresh) is False
    assert prep.needs_collect(has_codegraph=True, verdicts=stale) is True
    assert prep.needs_collect(has_codegraph=False, verdicts=fresh) is True
    assert prep.needs_collect(has_codegraph=True, verdicts=None) is False
    assert prep.needs_collect(has_codegraph=True, verdicts=None, force=True) is True
```

- [ ] **Step 2: 실패 확인** — `AttributeError: module 'prep' has no attribute 'needs_collect'`

- [ ] **Step 3: 구현** — `runner/wiki/prep.py` 의 `prepPlan` 위에:

```python
def needs_collect(has_codegraph: bool, verdicts: dict[str, list[str]] | None,
                  force: bool = False) -> bool:
    """수집기를 다시 돌릴 것인가.

    `force` 면 무조건. diff 가 없으면 지금처럼 지도의 존재만 본다. diff 가 있으면
    `재읽기 · 위치만 · 삭제됨` 중 하나라도 있을 때 다시 수집한다 — 지도가 낡은 채 남는 것을 막는다.
    """
    if force or not has_codegraph:
        return True
    if verdicts is None:
        return False
    return bool(verdicts.get("재읽기") or verdicts.get("위치만") or verdicts.get("삭제됨"))
```

`prepPlan` 의 서명에 `verdicts: dict[str, list[str]] | None = None, force: bool = False` 를 더하고, 첫 분기 `if hasCodegraph:` 를 `if not needs_collect(hasCodegraph, verdicts, force):` 로 바꾼다. `main` 의 `sys.argv` 처리(`if len(sys.argv) < 2:` 부터 `repoArg = sys.argv[1]` 까지)를 대체한다:

```python
    ap = argparse.ArgumentParser(description="정적 수집 → 코드 지도 → 사실 파일 · 모듈 그림")
    ap.add_argument("repo")
    ap.add_argument("--diff", default=None, help="changes.json. 있으면 그 판정으로 재수집 여부를 정한다")
    ap.add_argument("--force", action="store_true", help="지도가 있어도 무조건 다시 수집한다 (전량)")
    a = ap.parse_args()
    repoArg = a.repo
    verdicts: dict[str, list[str]] | None = None
    if a.diff:
        with open(a.diff, encoding="utf-8") as f:
            raw: object = json.load(f)
        top = raw if isinstance(raw, dict) else {}
        v = top.get("verdicts") if isinstance(top, dict) else None
        if isinstance(v, dict):
            verdicts = {str(k): [x for x in val if isinstance(x, str)]
                        for k, val in v.items() if isinstance(val, list)}
```

`plan = prepPlan(...)` 호출에 `verdicts=verdicts, force=a.force` 를 넘긴다. `import argparse` · `import json` 을 머리에 더한다.

- [ ] **Step 4: 통과 확인** — `12 passed` · `test/test_wiki.py` 도 그대로
- [ ] **Step 5: 커밋** — `git add runner/wiki/prep.py runner/test_mode1.py` · `[feat] : prep 이 changes.json 을 받아 재수집 여부를 정한다`

**판정 요청 (Task 4 끝):** `collect-graph` 의 뒤 절반(`facts` · `render-modules`)은 위키 재료라 diff 와 무관하다. `collect-graph` 를 `collect` + `facts` 로 쪼갤지. **이 계획은 쪼개지 않는다.**

---

### Task 5: 기계 단계 다섯 + `schedule-batches` — `graph.py` · `terms.py` · `wiki.py`(절반)

**Files:**
- Create: `runner/mode1/graph.py` · `runner/mode1/terms.py` · `runner/mode1/wiki.py`
- Modify: `runner/run_mode1.py` (`plan_summary` · `terms_argv` 원본 지우고 파사드)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import graph as G` · `from mode1 import terms as T` · `from mode1 import wiki as W`, 끝에:

```python
# ── 5. 기계 단계와 층 계획 ──────────────────────────────────────────────


def _plan_with(files: list[str]) -> dict[str, object]:
    """배치 하나짜리 계획. ⚠ 이것으로 `annotate-symbols` 를 돌리면 세션이 실제로 뜬다 — 대조 시험에만 쓴다."""
    syms = [{"name": f + ".S", "file": f} for f in files]
    return {"target": 8, "layers": [{"level": 0, "symbol_count": len(syms), "file_count": len(files),
            "batches": [{"id": "L0-B00", "files": files, "symbols": syms}]}],
            "totals": {"symbols": len(syms), "edges": 0, "levels": 1, "cyclic_symbols": 0}}


def _empty_plan() -> dict[str, object]:
    """층 0개 계획. `annotate-symbols` 가 세션 없이 OK 로 끝나야 하는 시험에 쓴다."""
    return {"target": 8, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}


def test_기계_단계_다섯은_저장소를_cwd_로_한다(tmp_path: Path):
    c = _ctx(tmp_path)
    for st in (G.CollectGraphStage(), T.VerifyTermsStage(), W.PublishWikiStage(), W.VerifyWikiStage()):
        assert st.cwd(c) == c.repo


def test_prep_은_전량이면_force_증분이면_diff_를_넘긴다(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True
    assert "--force" in G.CollectGraphStage().argv(c) and "--diff" not in G.CollectGraphStage().argv(c)
    c.cold = False
    assert "--diff" in G.CollectGraphStage().argv(c) and "--force" not in G.CollectGraphStage().argv(c)


def test_terms_argv_는_정적_지도를_위치_인자로_준다():
    argv = T.VerifyTermsStage.terms_argv("py", "/root", "/repo", "/repo/out/codegraph-raw/codegraph.json", None)
    assert argv[2] == "/repo/out/codegraph-raw/codegraph.json" and "--reading" not in argv


def test_schedule_batches_는_diff_의_targets_로_좁힌다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"nodes": [], "edges": []}')
    seen: dict[str, object] = {}
    def fake_plan(cg: object, target: int = 8, only_files: list[str] | None = None) -> dict[str, object]:
        seen["only"] = only_files
        return _plan_with([])
    monkeypatch.setattr(G.survey_plan, "plan", fake_plan)
    c.targets = ["x.py"]
    out = G.ScheduleBatchesStage().perform(c)
    assert out.kind == P.OK and seen["only"] == ["x.py"] and c.plan is not None
    assert (raw / "batches.json").exists()


def test_계획_요약은_층과_합계를_낸다():
    plan = _plan_with(["a.py"])
    lines = G.ScheduleBatchesStage.plan_summary(plan)  # type: ignore[arg-type]
    assert lines[0].startswith("  층0") and "합계" in lines[-1]
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.graph'`

- [ ] **Step 3: `graph.py` 신설** — `plan_summary` 는 `run_mode1.py` 의 것을 본문 그대로(`@staticmethod` 만 붙는다):

```python
"""`collect-graph` · `schedule-batches`. 코드 지도를 만들고 층과 배치로 나눈다."""
import json
import os
import sys
import time
from typing import cast

import pipeline as P
import survey_plan
from mode1 import context as X
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured
from mode1.context import Mode1Context


class CollectGraphStage(Mode1Machine):
    """정적 수집 → 코드 지도. 전량이면 `--force`, 증분이면 `--diff changes.json`."""
    name = "collect-graph"

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = self.wiki_argv(sys.executable, ctx.root, "prep.py", ctx.repo)
        if ctx.cold:
            argv.append("--force")
        else:
            argv += ["--diff", X.CHANGES.locate(ctx)]
        return argv

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [] if ctx.cold else [X.CHANGES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]


class ScheduleBatchesStage(Measured, P.Stage[Mode1Context]):
    """코드 지도를 층과 배치로. 증분이면 diff 의 `targets` 로 좁힌다. LLM 을 부르지 않는다."""
    name = "schedule-batches"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH] + ([] if ctx.cold else [X.CHANGES])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.BATCHES]

    @staticmethod
    def plan_summary(plan: survey_plan.SurveyPlan) -> list[str]:
        """층·배치 수를 줄 목록으로. `--dry-run` 과 `schedule-batches` 단계가 같은 글을 쓴다."""
        out: list[str] = []
        for L in plan.get("layers", []):
            if L.get("kind") == "non-node":
                out.append("  층%d — 비노드 용어 (한 세션)" % L["level"])
            else:
                n = len(L.get("batches", []))
                # `file_count` 는 비노드 층만 갖지 않는 선택 항목이라 첨자하면 기계가 짚는다.
                # 이 가지는 `kind != "non-node"` 라 늘 있다.
                out.append("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                           % (L["level"], L["symbol_count"],
                              L["file_count"],  # pyright: ignore[reportTypedDictNotRequiredAccess]
                              n))
        총배치 = sum(len(L.get("batches", [])) for L in plan.get("layers", []))
        out.append("  합계 — 심볼 %d · 층 %d · 배치 %d (LLM 세션이 그만큼 뜬다)"
                   % (plan["totals"]["symbols"], plan["totals"]["levels"], 총배치))
        return out

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        raw = P.read_json(X.CODEGRAPH.locate(ctx))
        bad = X.check_codegraph(raw)
        if bad:
            return P.Outcome(P.FAIL, "; ".join(bad), [self.row(t0, False, "; ".join(bad))])
        cg = cast(survey_plan.CodeGraph, raw)   # check 뒤의 좁히기 cast
        only = None if ctx.cold else ctx.targets
        ctx.plan = survey_plan.plan(cg, ctx.target, only_files=only)
        out_path = X.BATCHES.locate(ctx)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ctx.plan, f, ensure_ascii=False, indent=1)
        print("%s%s" % (out_path, " (증분: %d파일)" % len(only) if only else ""))
        for line in self.plan_summary(ctx.plan):
            print(line)
        return P.Outcome(P.OK, "", [self.row(t0, True)])
```

- [ ] **Step 4: `terms.py` 신설** — `terms_argv` 는 `run_mode1.py` 의 것을 본문 그대로:

```python
"""`verify-terms`. 읽기 레코드를 인용 검사하고 용어 DB 로 투영한다."""
import os
import sys

import pipeline as P
from mode1 import context as X
from mode1.machine_stage import Mode1Machine
from mode1.context import Mode1Context


class VerifyTermsStage(Mode1Machine):
    name = "verify-terms"

    @staticmethod
    def terms_argv(python: str, root: str, repo: str,
                   codegraph: str | None, reading: str | None) -> list[str]:
        """`terms_db.py` 명령줄.

        **정적 `codegraph.json` 을 위치 인자로 반드시 준다.** `--reading` 만 주면 읽기
        레코드의 투영이 그 파일을 **덮어써서** 정적 수집기가 찾은 노드가 조용히 사라진다.
        둘 다 주면 구조는 codegraph 가 이긴다.
        """
        argv = [python, os.path.join(root, "machine", "terms_db.py")]
        if codegraph:
            argv.append(codegraph)
        argv += ["--repo", repo]
        if reading:
            argv += ["--reading", reading]
        return argv

    def argv(self, ctx: Mode1Context) -> list[str]:
        cg, rd = X.CODEGRAPH.locate(ctx), X.READING.locate(ctx)
        return self.terms_argv(sys.executable, ctx.root, ctx.repo,
                               cg if os.path.exists(cg) else None,
                               rd if os.path.exists(rd) else None)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]
```

- [ ] **Step 5: `wiki.py` 신설 (절반)** — Task 9 가 `OutlineWikiStage` · `WriteWikiStage` 를 이 파일에 더한다:

```python
"""`outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다."""
import sys

import pipeline as P
from mode1 import context as X
from mode1.machine_stage import Mode1Machine
from mode1.context import Mode1Context


class PublishWikiStage(Mode1Machine):
    name = "publish-wiki"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return self.wiki_argv(sys.executable, ctx.root, "build.py", ctx.repo)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]


class VerifyWikiStage(Mode1Machine):
    name = "verify-wiki"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return self.wiki_argv(sys.executable, ctx.root, "check.py", ctx.repo)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]
```

- [ ] **Step 6: `run_mode1.py` 원본 지우고 파사드** — `plan_summary` · `terms_argv` 정의와 include 블록, `# ── 4. 보고` 절 머리를 지운다. 파사드 블록에 더한다:

```python
from mode1.graph import ScheduleBatchesStage  # noqa: E402
from mode1.terms import VerifyTermsStage  # noqa: E402
plan_summary = ScheduleBatchesStage.plan_summary
terms_argv = VerifyTermsStage.terms_argv
```

- [ ] **Step 7: 통과** — `test_mode1.py` `17 passed` · `test_run_mode1.py` `74 passed` · **Step 8: 형 검사** `0 errors`
- [ ] **Step 9: 커밋** — `git add runner/mode1/graph.py runner/mode1/terms.py runner/mode1/wiki.py runner/run_mode1.py runner/test_mode1.py` · `[feat] : mode1 기계 단계 다섯과 층 계획 단계`

---

### Task 6: `lang-hint` + `lang-decide` — `lang.py` (D4)

**Files:**
- Create: `runner/mode1/lang.py`
- Test: `runner/test_mode1.py`

`run_lang_select` 는 이 Task 에서 지우지 않는다 — 옛 `main` 이 아직 부른다. Task 12 에서 통째로 지운다. 프롬프트 문자열만 여기로 **복사**해 오고, 원본은 그때 사라진다.

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import lang as LG`, 끝에:

```python
# ── 6. 언어 제안과 결정 ──────────────────────────────────────────────────


def test_lang_hint_는_싼_모형을_고정한다(tmp_path: Path):
    assert LG.LangHintStage().model(_ctx(tmp_path)) == LG.LANG_SELECT_MODEL


def test_lang_hint_는_낱말_하나만_받아들인다(tmp_path: Path):
    c = _ctx(tmp_path)
    st = LG.LangHintStage()
    out = st.harvest(c, [("lang-hint", 1.0, 0, {"result": " `Cpp`. "})], 0)
    assert c.proposed == "cpp" and out.kind == P.OK
    out = st.harvest(c, [("lang-hint", 1.0, 0, {"result": "rust"})], 0)
    assert c.proposed is None and out.kind == P.SKIP


def test_lang_hint_는_실패해도_SKIP_이지_FAIL_이_아니다(tmp_path: Path):
    out = LG.LangHintStage().harvest(_ctx(tmp_path), [("lang-hint", 1.0, 1, None)], 0)
    assert out.kind == P.SKIP and all(r["ok"] for r in out.rows)


def test_lang_hint_는_문서가_없으면_세션을_띄우지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    st = LG.LangHintStage()
    monkeypatch.setattr(st, "docs", lambda ctx: "   ")
    assert st.jobs(c, 0) == []
    out = st.harvest(c, [], 0)
    assert out.kind == P.SKIP and out.rows[0].get("skipped") is True


def test_lang_hint_프롬프트는_넷_중_하나를_낱말로_답하라고_한다():
    p = LG.LangHintStage.hint_prompt("# README\n이 저장소는 …")
    assert "cpp" in p and "unknown" in p and p.endswith("이 저장소는 …")


def test_lang_decide_는_제안이_있으면_넘긴다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert "--propose" not in LG.LangDecideStage().argv(c)
    c.proposed = "py"
    assert LG.LangDecideStage().argv(c)[-2:] == ["--propose", "py"]
    assert LG.LangDecideStage().writes(c) == [X.LANG_SELECT]
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.lang'`

- [ ] **Step 3: `lang.py` 신설** — `hint_prompt` 의 문자열은 `run_lang_select` 안의 것을 글자 그대로(`docs` 만 인자로):

```python
"""`lang-hint` · `lang-decide`. 언어 하나를 제안받고 결정론으로 채택한다."""
import os
import subprocess
import sys
import time
from collections.abc import Sequence

import measure as M
import pipeline as P
from mode1 import context as X
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured
from mode1.context import Mode1Context

# 언어 판별에 쓸 Model. 문서를 읽고 `cpp|cs|py|ts` 중 하나를 내는 것이 전부라 가장 싼 것을 쓴다.
# `--model` 은 annotate-symbols · write-wiki 몫이라 여기에 쓰지 않는다.
LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"
LANG_WORDS = ("cpp", "cs", "py", "ts")


class LangHintStage(Measured, P.LlmStage[Mode1Context]):
    """루트 문서를 읽혀 언어 하나를 제안받는다. 못 받아도 막지 않는다 — 관문이 아니다."""
    name = "lang-hint"
    emits = P.OK | P.SKIP

    def model(self, ctx: Mode1Context) -> str:
        return LANG_SELECT_MODEL

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    @staticmethod
    def hint_prompt(docs: str) -> str:
        return (
            "아래는 한 저장소의 최상위 문서다. 이 저장소에 **정적 분석기를 돌려 코드 지도를 만들려 한다.**\n"
            "어느 언어를 대상으로 삼아야 가장 쓸모 있는 지도가 나오겠는지 판단해라.\n\n"
            "고를 수 있는 것과 그 수집기:\n"
            "  cpp -> clang-uml    cs -> roslyn-dump    py -> griffe+pycalls    ts -> (수집기 없음)\n\n"
            "문서가 어떤 언어를 많이 이야기하는지가 아니라, **분석해서 얻을 것이 있는 코드**가\n"
            "어느 언어인지를 본다. 넷 중 하나를 **낱말 하나로만** 답해라. 설명하지 마라.\n"
            "판단이 안 서면 `unknown` 이라고 답해라.\n\n" + docs)

    def docs(self, ctx: Mode1Context) -> str:
        """루트 문서 묶음. `lang_select.py --print-docs` 가 고른다."""
        tool = os.path.join(ctx.root, "machine", "lang_select.py")
        return subprocess.run([sys.executable, tool, ctx.repo, "--print-docs"],
                              capture_output=True, text=True).stdout

    def prompt(self, ctx: Mode1Context) -> str:
        return self.hint_prompt(self.docs(ctx))

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        docs = self.docs(ctx)
        return [(self.name, self.hint_prompt(docs))] if docs.strip() else []

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        t0 = time.monotonic()
        ctx.proposed = None
        if not got:
            r = self.row(t0, True, "루트 문서 없음 — 파일 수로 고른다")
            r["skipped"] = True
            return P.Outcome(P.SKIP, r["why"], [r])
        base = super().harvest(ctx, got, rnd)
        for _, _, rc, result in got:
            word = M.as_str(M.as_map(result).get("result")).strip().strip("`.").lower()
            if rc == 0 and word in LANG_WORDS:
                ctx.proposed = word
        if base.kind != P.OK or ctx.proposed is None:
            for r in base.rows:
                r["ok"], r["why"], r["skipped"] = True, "제안 없음 — 파일 수로 고른다", True
            return P.Outcome(P.SKIP, "제안 없음", base.rows)
        return base


class LangDecideStage(Mode1Machine):
    """제안을 결정론으로 기각하거나 채택해 `lang-select.json` 을 쓴다."""
    name = "lang-decide"

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = [sys.executable, os.path.join(ctx.root, "machine", "lang_select.py"),
                ctx.repo, "-o", X.LANG_SELECT.locate(ctx)]
        if ctx.proposed:
            argv += ["--propose", ctx.proposed]
        return argv

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.LANG_SELECT]
```

**`lang-hint` 실패는 `SKIP` 이다** — 스펙 D4 의 폴백 간선 `('lang-propose', FAIL) -> 'lang-decide'` 대신, 관문이 아닌 단계의 실패를 `SKIP → NEXT` 로 잇는다. 같은 효과이고 갈래를 하나 더 안 만든다. Task 13 에서 스펙에 적는다.

- [ ] **Step 4: 통과** `23 passed` · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/lang.py runner/test_mode1.py` · `[feat] : lang-select 를 lang-hint 와 lang-decide 로 쪼갬`

---

### Task 7: `detect-changes` · `snapshot-sources` — `scan.py` (D14 쓰기 · 설계 메모 ①)

**Files:**
- Create: `runner/mode1/scan.py`
- Modify: `runner/run_mode1.py` (`LANG_ALIAS` · `lang_of` · `changed_seed` 원본 지우고 파사드)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import scan as SC`, 끝에:

```python
# ── 7. 옛 지문과 지금 소스의 대조 ────────────────────────────────────────


def _no_change() -> dict[str, list[str]]:
    return {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}


def test_lang_for_는_lang_select_을_먼저_보고_코드_지도로_폴백한다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    assert SC.SnapshotScan.lang_for(c) is None
    (raw / "codegraph.json").write_text('{"language": "csharp", "nodes": [], "edges": []}')
    assert SC.SnapshotScan.lang_for(c) == "cs"
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "griffe+pycalls"}')
    assert SC.SnapshotScan.lang_for(c) == "py"


def test_씨앗은_재읽기와_위치만의_합집합이다():
    v = {"유효": ["a.py"], "재읽기": ["c.py"], "위치만": ["b.py"], "삭제됨": ["z.py"]}
    assert SC.DetectChangesStage.changed_seed(v) == ["b.py", "c.py"]


def test_detect_changes_는_diff_파일을_쓴다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"language": "py", "nodes": [], "edges": []}')
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "griffe+pycalls"}')
    monkeypatch.setattr(SC.declmap, "tracked_files", lambda repo, lang, x: ["a.py"])
    monkeypatch.setattr(SC.declmap, "scan", lambda repo, lang, x, n: ({}, None))
    monkeypatch.setattr(SC.warmup, "status",
                        lambda cache, repo, files, decls: ({"유효": [], "재읽기": ["a.py"], "위치만": [], "삭제됨": []}, {}))
    out = SC.DetectChangesStage().perform(c)
    assert out.kind == P.OK
    got = D.read_diff(str(raw / "changes.json"))
    assert got is not None and got["targets"] == ["a.py"] and c.targets == ["a.py"]
    assert c.warmup_cache == str(raw / "snapshot.json")


def test_detect_changes_는_언어를_모르면_전량_diff_를_쓴다(tmp_path: Path):
    c = _ctx(tmp_path)
    out = SC.DetectChangesStage().perform(c)
    got = D.read_diff(X.CHANGES.locate(c))
    assert out.kind == P.OK and got is not None and got["targets"] is None and c.targets is None


def test_snapshot_sources_는_조사가_실패하면_쓰지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path); c.entries = {}; c.warmup_cache = str(tmp_path / "w.json"); c.cold = False
    wrote: list[str] = []
    monkeypatch.setattr(SC.warmup, "save", lambda p, e: wrote.append(p) or e)
    c.survey_ok = False
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == []
    c.survey_ok = True
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == [c.warmup_cache]


def test_snapshot_sources_는_전량이면_직접_훑어_찍는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path); c.cold = True; c.survey_ok = True
    monkeypatch.setattr(SC.SnapshotSourcesStage, "scan_snapshot",
                        staticmethod(lambda ctx: (_no_change(), {"a.py": {}}, str(tmp_path / "w.json"))))
    wrote: list[str] = []
    monkeypatch.setattr(SC.warmup, "save", lambda p, e: wrote.append(p) or e)
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == [str(tmp_path / "w.json")]


def test_지문은_옛_이름도_읽고_새_이름으로_쓴다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    assert X.snapshot_path(c).endswith("snapshot.json")
    (raw / "warmup.json").write_text("{}")
    assert X.snapshot_path(c).endswith("warmup.json")
    (raw / "snapshot.json").write_text("{}")
    assert X.snapshot_path(c).endswith("snapshot.json")
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.scan'`

- [ ] **Step 3: `scan.py` 신설** — `LANG_ALIAS` · `lang_of` · `changed_seed` 는 `run_mode1.py` 의 것을 본문 그대로(`LANG_ALIAS` 참조만 `SnapshotScan.LANG_ALIAS` 로):

```python
"""`detect-changes` · `snapshot-sources`. 옛 지문과 지금 소스를 대조하고, 조사가 해낸 뒤 지문을 찍는다."""
import json
import os
import sys
import time

import declmap
import measure as M
import pipeline as P
import warmup
from mode1 import context as X
from mode1 import diff as D
from mode1.measured import Measured
from mode1.context import Mode1Context


class SnapshotScan:
    """옛 지문과 지금 소스를 대조하는 한 벌. `detect-changes` 와 `snapshot-sources` 가 상속한다.

    훑는 코드가 한 벌인 이유 — 전량 그래프에는 `detect-changes` 가 없어 `snapshot-sources` 가
    스스로 훑어야 하고, 두 단계가 다른 방식으로 훑으면 다음 실행의 증분 판정이 어긋난다.
    """
    # 코드 지도가 적는 언어 이름과 declmap 이 아는 이름이 한 칸 다르다. 수집기 판별을 여기서
    # 다시 하지 않는다 — 판별 규칙이 두 곳에 생기면 조용히 어긋난다.
    LANG_ALIAS = {"csharp": "cs", "python": "py"}

    @staticmethod
    def lang_of(codegraph_path: str | None) -> str | None:
        """코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다.

        모르면 `None` 이다 — 예외가 아니다. 부르는 쪽이 증분 판정만 건너뛰고 나머지는 그대로 돈다.
        """
        if not codegraph_path:
            return None
        try:
            with open(codegraph_path, encoding="utf-8") as f:
                name = json.load(f).get("language")
        except (OSError, ValueError):
            return None
        name = SnapshotScan.LANG_ALIAS.get(name, name)
        return name if name in declmap.LANGS else None

    @staticmethod
    def lang_for(ctx: Mode1Context) -> str | None:
        """언어. `lang-select.json` 을 먼저, 없으면 코드 지도를 본다."""
        sel = M.as_map(P.read_json(X.LANG_SELECT.locate(ctx)))
        word = M.as_str(sel.get("language"))
        if word:
            name = SnapshotScan.LANG_ALIAS.get(word, word)
            return name if name in declmap.LANGS else None
        cg = X.CODEGRAPH.locate(ctx)
        return SnapshotScan.lang_of(cg if os.path.exists(cg) else None)

    @staticmethod
    def scan_snapshot(ctx: Mode1Context) -> tuple[warmup.Verdicts, warmup.Manifest, str] | None:
        """지금 소스를 훑어 옛 지문과 대조한다. `(판정, 새 지문, 지문 파일 경로)`.

        언어를 모르거나 git 이 아는 소스가 0개면 `None` — 전량으로 돈다.
        읽는 지문은 옛 이름(`warmup.json`)도 되고, 쓰는 경로는 늘 새 이름이다.
        """
        lang = SnapshotScan.lang_for(ctx)
        if lang is None:
            return None
        files = declmap.tracked_files(ctx.repo, lang, [])
        if not files:
            print("알림 — git 이 아는 %s 소스가 0개다. 전량 조사로 돈다." % lang, file=sys.stderr)
            return None
        decls, _ = declmap.scan(ctx.repo, lang, [], 0)
        판정, entries = warmup.status(X.snapshot_path(ctx), ctx.repo, files, decls)
        return 판정, entries, X.SNAPSHOT.locate(ctx)


class DetectChangesStage(SnapshotScan, Measured, P.Stage[Mode1Context]):
    """옛 지문과 지금 소스를 대조해 `changes.json` 을 쓴다. **증분 그래프에만 있다.**"""
    name = "detect-changes"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.LANG_SELECT]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CHANGES]

    @staticmethod
    def changed_seed(판정: warmup.Verdicts) -> list[str]:
        """다시 읽어야 할 파일의 씨앗. **`재읽기` 와 `위치만` 의 합집합이다.**

        `위치만` 을 반드시 포함한다 — `warmup.decl_hash` 는 선언의 이름만 해싱하므로 본문만
        바뀐 변경도 `위치만` 으로 판정된다. 레코드의 `does` 와 위키 산문의 행동 서술은 본문에
        달려 있어서, 이 갈래를 빼면 그 서술이 조용히 낡는다. `warmup.py` 의 CLI 도 같은 합집합을 쓴다.

        `유효` 는 읽을 것이 없고, `삭제됨` 은 읽을 파일 자체가 없다.
        """
        return sorted(set(판정.get("재읽기") or []) | set(판정.get("위치만") or []))

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        diff_path = X.CHANGES.locate(ctx)
        scanned = self.scan_snapshot(ctx)
        if scanned is None:
            empty: warmup.Verdicts = {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}
            print("알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다.", file=sys.stderr)
            D.write_diff(diff_path, empty, None, ctx.hops, 0)
            ctx.targets = None
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        판정, entries, cache = scanned
        files_n = sum(len(v) for k, v in 판정.items() if k != "삭제됨")
        seed = self.changed_seed(판정)
        cg = X.CODEGRAPH.locate(ctx)
        targets = warmup.blast_radius(cg, seed, ctx.hops) if seed and os.path.exists(cg) else seed
        D.write_diff(diff_path, 판정, targets, ctx.hops, files_n)
        ctx.targets, ctx.entries, ctx.warmup_cache, ctx.tracked_n = targets, entries, cache, files_n
        print("파일 %d개 — 유효 %d · 재읽기 %d · 위치만 %d · 삭제됨 %d"
              % (files_n, len(판정["유효"]), len(판정["재읽기"]), len(판정["위치만"]), len(판정["삭제됨"])))
        print("에이전트가 읽을 것 %d개 — 씨앗 %d개에서 %d홉 퍼뜨린 결과" % (len(targets), len(seed), ctx.hops))
        for p in targets[:15]:
            print("  " + p)
        if len(targets) > 15:
            print("  … 그 밖 %d개" % (len(targets) - 15))
        if 판정["삭제됨"]:
            print("사람이 볼 것 — 삭제된 파일 %d개의 레코드를 지울지 정해야 한다:" % len(판정["삭제됨"]),
                  file=sys.stderr)
            for p in 판정["삭제됨"][:10]:
                print("  " + p, file=sys.stderr)
        return P.Outcome(P.OK, "", [self.row(t0, True)])


class SnapshotSourcesStage(SnapshotScan, Measured, P.Stage[Mode1Context]):
    """전수조사가 해낸 뒤에만 지문을 찍는다.

    증분이면 `detect-changes` 가 넘긴 `entries` 를 찍고, 전량이면 **여기서 직접 훑어** 찍는다 —
    전량 그래프에는 `detect-changes` 가 없기 때문이다. 다음 실행이 이것을 옛 판으로 쓴다.
    """
    name = "snapshot-sources"

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.SNAPSHOT]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.entries is None:
            scanned = self.scan_snapshot(ctx)
            if scanned is None:
                print("알림 — 언어를 몰라 지문을 찍지 않는다.", file=sys.stderr)
                return P.Outcome(P.OK, "", [self.row(t0, True)])
            _, ctx.entries, ctx.warmup_cache = scanned
        if not ctx.warmup_cache:
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        if not ctx.survey_ok:
            print("지문을 갱신하지 않는다 — 전수조사가 실패했다. "
                  "지금 갱신하면 읽지 않은 파일이 '유효' 로 남는다.", file=sys.stderr)
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        warmup.save(ctx.warmup_cache, ctx.entries)
        print("지문 갱신 — %s (%d개 파일)" % (ctx.warmup_cache, len(ctx.entries)))
        return P.Outcome(P.OK, "", [self.row(t0, True)])
```

⚠ `snapshot-sources` 의 `writes = [SNAPSHOT]` 인데 세 갈래(언어 모름 · 지문 경로 없음 · 조사 실패)에서 파일을 안 쓰고 `OK` 를 낸다. `Pipeline.run` 의 `bad_writes` 가 `SNAPSHOT` 이 없으면 `FAIL` 로 바꾼다. **이것은 옛 동작과 다르다** — 옛 `save_warmup` 은 조용히 `True` 를 냈다. 조사 실패는 `annotate-symbols` 가 이미 `FAIL` 로 멈추므로 `snapshot-sources` 까지 오지 않는다. 언어를 모르는 경우만 실제로 `FAIL` 이 되는데, 언어를 모르면 `collect-graph` 가 먼저 죽는다. 그래도 **`writes` 를 조건부로** 한다 — `return [X.SNAPSHOT] if ctx.warmup_cache or ctx.entries is None else []` 는 시뮬레이터가 시작 전에 평가하므로 쓸 수 없다. 대신 `SNAPSHOT` 은 `check=None`(존재만) 이고, 세 갈래에서 옛 지문이 이미 있으면 존재는 참이다. **첫 전량 실행 + 언어 모름** 한 경우만 `FAIL` 이고 그것은 옳은 신호다. 이 판단을 스펙에 적는다(Task 13).

**[제안됨] ① 의 대안 — 사용자가 "복제" 로 판정하면:** `SnapshotScan` 을 `abc.ABC` 로 바꾸고 `lang_for` · `scan_snapshot` 을 `@staticmethod @abstractmethod` 로 선언만 남긴 뒤, 위 본문을 `DetectChangesStage` 와 `SnapshotSourcesStage` 에 각각 그대로 적는다. `LANG_ALIAS` · `lang_of` 는 `lang_for` 가 쓰므로 함께 두 벌이 된다. 파사드는 `DetectChangesStage.lang_of` 를 내보낸다.

- [ ] **Step 4: `run_mode1.py` 원본 지우고 파사드** — `LANG_ALIAS` · `lang_of` · `changed_seed` 정의와 include 블록, 그 위 주석을 지운다. 파사드 블록에:

```python
from mode1.scan import SnapshotScan, DetectChangesStage  # noqa: E402
LANG_ALIAS = SnapshotScan.LANG_ALIAS
lang_of = SnapshotScan.lang_of
changed_seed = DetectChangesStage.changed_seed
```

- [ ] **Step 5: 통과** — `test_mode1.py` `30 passed` · `test_run_mode1.py` `74 passed` · **Step 6: 형 검사** `0 errors`
- [ ] **Step 7: 커밋** — `git add runner/mode1/scan.py runner/run_mode1.py runner/test_mode1.py` · `[feat] : detect-changes 가 changes.json 을 쓰고 snapshot-sources 가 지문을 찍는다`

---

### Task 8: `annotate-symbols` — `survey.py` (D14 양방향 대조 · D2)

**Files:**
- Create: `runner/mode1/survey.py`
- Modify: `runner/run_mode1.py` (프롬프트 넷 · `merge_shards` · `_qualified` 원본 지우고 파사드)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import survey as SV`, 끝에:

```python
# ── 8. 전수조사 — 계획과 diff 의 대조 · 샤드 병합 · 층 돌기 ─────────────


def _diff(targets: list[str] | None) -> D.WarmupDiff:
    return {"verdicts": {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []},
            "targets": targets, "hops": 1, "tracked": 2}


def test_계획이_diff_보다_넓으면_잡는다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["a.py", "b.py"]), _diff(["b.py"])) != []


def test_계획이_diff_보다_좁으면_잡는다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["b.py"]), _diff(None)) != []


def test_계획과_diff_가_맞으면_통과한다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["b.py"]), _diff(["b.py"])) == []
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["a.py", "b.py"]), _diff(None)) == []


def test_annotate_symbols_는_어긋난_계획을_돌리지_않는다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _diff(["b.py"])["verdicts"], ["b.py"], 1, 2)
    (raw / "batches.json").write_text(json.dumps(_plan_with(["a.py", "b.py"])))
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.FAIL and "diff" in out.why


def test_annotate_symbols_는_바뀐_것이_없고_레코드가_있으면_SKIP(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _no_change(), [], 1, 0)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    reading = Path(X.READING.locate(c)); reading.parent.mkdir(parents=True)
    reading.write_text("{}")
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.SKIP and c.survey_ok is True


def test_annotate_symbols_는_레코드가_없으면_바뀐_것이_없어도_돈다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _no_change(), [], 1, 0)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    out = SV.AnnotateSymbolsStage().perform(c)     # 층이 0개라 세션 없이 OK 로 끝난다
    assert out.kind == P.OK and c.survey_ok is True


def test_샤드를_합치고_충돌은_전원을_개명한다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B00.json").write_text(json.dumps({"main": {"where": "app/gui.py:10"}}), encoding="utf-8")
    (d / "L0-B01.json").write_text(json.dumps({"main": {"where": "app/cli.py:3"}}), encoding="utf-8")
    got = SV.AnnotateSymbolsStage.merge_shards(str(d), {})
    assert sorted(got) == ["cli.main", "gui.main"]


def test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다():
    b = {"id": "L1-B00", "files": ["a.py"], "symbols": [{"name": "f", "kind": "function", "file": "a.py", "line": 1}]}
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", ["a.py"], 3)  # type: ignore[arg-type]
    assert "범위" in p and "_shards/L1-B00.json" in p
    assert "범위" not in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")  # type: ignore[arg-type]
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.survey'`

- [ ] **Step 3: `survey.py` 신설** — 프롬프트 넷과 `merge_shards` · `qualified` 는 `run_mode1.py` 의 것을 본문 그대로. 아래 코드에서 `…(본문 그대로)…` 로 표시한 자리는 `run_mode1.py` 의 해당 함수 본문을 한 글자도 바꾸지 않고 넣되, **들여쓰기를 한 단 더** 하고 함수 안의 다른 함수 호출을 `AnnotateSymbolsStage.<이름>(…)` 으로, `reading_path(repo, ROOT)` 를 `X.reading_path(repo, ROOT)` 로, `measure.as_str` 을 `M.as_str` 로, `_qualified` 를 `AnnotateSymbolsStage.qualified` 로 바꾼다:

```python
"""`annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다."""
import json
import os
import sys
import time
from collections.abc import Mapping, Sequence
from typing import cast

import measure as M
import pipeline as P
import survey_plan
from mode1 import context as X
from mode1 import diff as D
from mode1.context import ROOT
from mode1.measured import Measured
from mode1.context import Mode1Context, Record, Records


class AnnotateSymbolsStage(Measured, P.LlmStage[Mode1Context]):
    """배치 하나 = 세션 하나. 층 사이에 이어지는 값(`baseline` · `merged`)은 **문맥 칸**에 둔다."""
    name = "annotate-symbols"
    emits = P.OK | P.FAIL | P.SKIP

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""   # jobs 가 배치마다 만든다. 단일 프롬프트는 쓰이지 않는다

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.BATCHES] + ([] if ctx.cold else [X.CHANGES])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.READING]

    # ── 자리 ────────────────────────────────────────────────────────────

    @staticmethod
    def shard_dir(ctx: Mode1Context) -> str:
        return os.path.join(X.raw_dir(ctx), "_shards")

    # ── 프롬프트 넷 — run_mode1.py 에서 본문 그대로 ──────────────────────

    @staticmethod
    def warmup_section(targets: Sequence[str] | None, total: int, repo: str = "") -> str:
        …(본문 그대로 — `reading_path(repo, ROOT)` → `X.reading_path(repo, ROOT)`)…

    @staticmethod
    def dep_excerpt(merged: Mapping[str, Mapping[str, object]],
                    batch: survey_plan.PlanBatch) -> str:
        …(본문 그대로)…

    @staticmethod
    def survey_batch_prompt(repo: str, root: str, batch: survey_plan.PlanBatch,
                            dep_records: str, targets: Sequence[str] | None = None,
                            total: int = 0) -> str:
        …(본문 그대로 — 끝의 `+ warmup_section(...)` → `+ AnnotateSymbolsStage.warmup_section(...)`)…

    @staticmethod
    def nonnode_prompt(repo: str, root: str) -> str:
        …(본문 그대로 — `reading=reading_path(repo, ROOT)` → `reading=X.reading_path(repo, ROOT)`)…

    # ── 레코드 — run_mode1.py 에서 본문 그대로 + 신설 셋 ─────────────────

    @staticmethod
    def load_records(path: str) -> Records:
        """있으면 읽어 사전으로 좁혀 내고, 없거나 사전이 아니면 `{}`."""
        raw = P.read_json(path)
        return {k: M.as_map(v) for k, v in M.as_map(raw).items()}

    @staticmethod
    def merge_shards(shard_dir: str, existing: Records | None) -> Records:
        …(본문 그대로 — `_qualified(` → `AnnotateSymbolsStage.qualified(`)…

    @staticmethod
    def qualified(key: str, rec: Record | None) -> str:
        …(본문 그대로 — `measure.as_str` → `M.as_str`)…

    @staticmethod
    def plan_files(plan: object) -> set[str]:
        """계획에 든 배치들이 가리키는 파일 집합."""
        out: set[str] = set()
        for layer in M.as_list(M.as_map(plan).get("layers")):
            for batch in M.as_list(M.as_map(layer).get("batches")):
                for f in M.as_list(M.as_map(batch).get("files")):
                    if isinstance(f, str):
                        out.add(f)
        return out

    @staticmethod
    def compare_plan(plan: object, d: D.WarmupDiff) -> list[str]:
        """계획과 diff 가 같은 범위를 말하는지 양방향으로 본다. 불평 목록을 낸다.

        넓으면 전량 지시서에 부분 쪽지가 붙은 것이고, 좁으면 부분 지시서에 전량 쪽지가
        붙은 것이다. 두 번째가 더 위험하다 — 레코드가 조용히 빈다.
        `targets` 가 있을 때 "좁다" 는 잡지 않는다 — 좁힌 계획은 `targets` 의 부분집합일 수 있다.
        """
        have = AnnotateSymbolsStage.plan_files(plan)
        want = set(d["targets"]) if d["targets"] is not None else D.all_files(d)
        out: list[str] = []
        wider = have - want
        if wider:
            out.append("계획이 diff 보다 넓다 — diff 밖의 파일 %d개: %s" % (len(wider), sorted(wider)[:5]))
        if d["targets"] is None and want - have:
            out.append("계획이 diff 보다 좁다 — 전량인데 빠진 파일 %d개" % len(want - have))
        return out

    # ── 층 돌기 ─────────────────────────────────────────────────────────

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.plan is None:
            raw = P.read_json(X.BATCHES.locate(ctx))
            bad = X.check_batches(raw)
            if bad:
                return P.Outcome(P.FAIL, "; ".join(bad), [self.row(t0, False, "; ".join(bad))])
            ctx.plan = cast(survey_plan.SurveyPlan, raw)
            print("층 계획을 디스크에서 읽었다 — %s" % X.BATCHES.locate(ctx), flush=True)
        if not ctx.cold:
            d = D.read_diff(X.CHANGES.locate(ctx))
            if d is None:
                why = "changes.json 을 읽지 못했다"
                return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
            bad = self.compare_plan(ctx.plan, d)
            if bad:
                why = "계획이 diff 와 어긋난다: " + "; ".join(bad)
                return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
            ctx.targets, ctx.tracked_n = d["targets"], d["tracked"]
            if d["targets"] is not None and not d["targets"] and os.path.exists(X.READING.locate(ctx)):
                ctx.survey_ok = True    # 읽을 것이 없고 지난 레코드가 살아 있다 — 지문을 찍어도 된다
                row = self.row(t0, True, "바뀐 파일 0개 — 지난 조사 결과를 그대로 쓴다")
                row["skipped"] = True
                return P.Outcome(P.SKIP, row["why"], [row])
        n_sessions = sum(len(L.get("batches", [])) or 1 for L in ctx.plan["layers"])
        print("조사 세션 예상 %d개 (층 %d)" % (n_sessions, len(ctx.plan["layers"])), flush=True)
        os.makedirs(self.shard_dir(ctx), exist_ok=True)
        ctx.baseline = self.load_records(X.READING.locate(ctx))
        ctx.merged = dict(ctx.baseline)
        out = super().perform(ctx)
        ctx.survey_ok = out.kind == P.OK    # 층이 0개면 harvest 가 안 불리므로 여기서 정한다
        return out

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.plan["layers"]) if ctx.plan else 0

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        assert ctx.plan is not None
        layer = ctx.plan["layers"][rnd]
        if layer.get("kind") == "non-node":
            jobs = [("NONNODE", self.nonnode_prompt(ctx.repo, ctx.root))]
        else:
            jobs = [(b["id"], self.survey_batch_prompt(ctx.repo, ctx.root, b,
                                                       self.dep_excerpt(ctx.merged, b),
                                                       ctx.targets, ctx.tracked_n))
                    for b in layer["batches"]]
        # 샤드가 이미 있는 배치는 건너뛴다 — 다시 돌리면 실패한 배치만 돈다.
        return [(bid, pr) for bid, pr in jobs
                if not os.path.exists(os.path.join(self.shard_dir(ctx), bid + ".json"))]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "annotate-symbols/" + row["stage"]
        ctx.merged = self.merge_shards(self.shard_dir(ctx), ctx.baseline)
        path = X.READING.locate(ctx)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx.merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("  층 끝 — 레코드 %d개" % len(ctx.merged), flush=True)
        return out
```

`import sys` 는 `merge_shards` 가 `sys.stderr` 를 쓴다. 층 하나가 실패하면 `LlmStage.perform` 이 다음 층으로 가지 않는다 — 옛 `run_survey` 의 `break` 와 같다.

- [ ] **Step 4: `run_mode1.py` 원본 지우고 파사드** — `warmup_section` · `dep_excerpt` · `survey_batch_prompt` · `nonnode_prompt` · `merge_shards` · `_qualified` 정의와 include 블록을 지운다. 파사드 블록에:

```python
from mode1.survey import AnnotateSymbolsStage  # noqa: E402
warmup_section = AnnotateSymbolsStage.warmup_section
dep_excerpt = AnnotateSymbolsStage.dep_excerpt
survey_batch_prompt = AnnotateSymbolsStage.survey_batch_prompt
nonnode_prompt = AnnotateSymbolsStage.nonnode_prompt
merge_shards = AnnotateSymbolsStage.merge_shards
_qualified = AnnotateSymbolsStage.qualified
```

- [ ] **Step 5: 통과** — `test_mode1.py` `38 passed` · `test_run_mode1.py` `74 passed` · **Step 6: 형 검사** `0 errors`
- [ ] **Step 7: 커밋** — `git add runner/mode1/survey.py runner/run_mode1.py runner/test_mode1.py` · `[feat] : annotate-symbols 가 계획과 diff 를 대조하고 층을 돈다`

---

### Task 9: `outline-wiki` + `write-wiki` — `wiki.py` 나머지 (D16)

**Files:**
- Modify: `runner/mode1/wiki.py`
- Modify: `runner/run_mode1.py` (`wiki_catalogue_prompt` · `symbol_layers` · `page_layers` · `wiki_page_prompt` 원본 지우고 파사드)
- Modify: `runner/test_run_mode1.py:757` — **[제안됨] ② 한 줄** (`"wiki-plan.json"` → `"outline.json"`)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
# ── 9. 위키 목차와 장 ───────────────────────────────────────────────────


def test_outline_wiki_는_목차_파일을_쓴다고_선언하고_있으면_SKIP(tmp_path: Path):
    c = _ctx(tmp_path)
    assert W.OutlineWikiStage().writes(c) == [X.OUTLINE]
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "outline.json").write_text('{"pages": []}')
    assert W.OutlineWikiStage().perform(c).kind == P.SKIP


def test_목차_프롬프트는_새_이름의_파일을_말한다():
    p = W.OutlineWikiStage.wiki_catalogue_prompt("/repo", "/root")
    assert "outline.json" in p and "batches.json" in p
    assert "wiki-plan.json" not in p and "survey-plan.json" not in p


def test_write_wiki_는_이미_쓴_장을_건너뛴다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "outline.json").write_text(json.dumps({"pages": [{"file": "a.md", "symbols": []}, {"file": "b.md", "symbols": []}]}))
    (tmp_path / "docs" / "wiki").mkdir(parents=True)
    (tmp_path / "docs" / "wiki" / "a.md").write_text("x")
    c.plan = {"target": 8, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}
    st = W.WriteWikiStage()
    st.prepare(c)
    assert W.WriteWikiStage().reads(c) == [X.OUTLINE, X.BATCHES]
    assert [j[0] for j in st.jobs(c, 0)] == ["b.md"]


def test_페이지_층은_인용한_심볼의_최대():
    pages: list[X.WikiPage] = [{"file": "i.md", "symbols": []}, {"file": "p.md", "symbols": ["a", "b", "없음"]}]
    assert W.WriteWikiStage.page_layers(pages, {"a": 0, "b": 2}) == {"i.md": 0, "p.md": 2}
```

- [ ] **Step 2: 실패 확인** — `AttributeError: module 'mode1.wiki' has no attribute 'OutlineWikiStage'`

- [ ] **Step 3: `wiki.py` 에 더한다** — 머리 import 를 이렇게 바꾸고:

```python
import json
import os
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
from typing import cast

import measure as M
import pipeline as P
import survey_plan
from mode1 import context as X
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured
from mode1.context import Mode1Context, WikiPage
```

`PublishWikiStage` 위에 두 클래스를 넣는다. `wiki_catalogue_prompt` · `symbol_layers` · `page_layers` · `wiki_page_prompt` 는 `run_mode1.py` 의 것을 본문 그대로 — **단 `wiki_catalogue_prompt` 안의 파일 이름 셋을 바꾼다:** 재료 표의 `survey-plan.json` → `batches.json`, 낼 파일 `wiki-plan.json` → `outline.json`(두 곳).

```python
class OutlineWikiStage(Measured, P.LlmStage[Mode1Context]):
    """목차 한 세션. 이미 있으면 SKIP."""
    name = "outline-wiki"
    emits = P.OK | P.FAIL | P.SKIP

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return self.wiki_catalogue_prompt(ctx.repo, ctx.root)

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE]

    @staticmethod
    def wiki_catalogue_prompt(repo: str, root: str) -> str:
        …(본문 그대로 — 파일 이름 셋만 바꾼다)…

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if os.path.exists(X.OUTLINE.locate(ctx)):
            row = self.row(t0, True, "목차가 이미 있다")
            row["skipped"] = True
            return P.Outcome(P.SKIP, row["why"], [row])
        return super().perform(ctx)


class WriteWikiStage(Measured, P.LlmStage[Mode1Context]):
    """장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛴다."""
    name = "write-wiki"

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE, X.BATCHES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        # 장들은 LLM 자식 프로세스가 쓴다. "돌고 나면 있어야 한다" 는 선언이지 누가 쓰는가가 아니다 —
        # 이것이 없으면 시뮬레이터가 `publish-wiki` 의 읽기(`docs/wiki`)를 보장 못 해 그래프를 거부한다.
        return [X.WIKI_DIR]

    @staticmethod
    def symbol_layers(plan: survey_plan.SurveyPlan) -> dict[str, int]:
        …(본문 그대로 — 독스트링의 `survey-plan.json` → `batches.json`)…

    @staticmethod
    def page_layers(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]:
        …(본문 그대로)…

    @staticmethod
    def wiki_page_prompt(repo: str, root: str, page: WikiPage, lower_pages: str) -> str:
        …(본문 그대로)…

    def prepare(self, ctx: Mode1Context) -> None:
        raw = P.read_json(X.OUTLINE.locate(ctx))
        pages = [p for p in M.as_list(M.as_map(raw).get("pages")) if isinstance(M.as_map(p).get("file"), str)]
        ctx.wiki_pages = [cast(WikiPage, p) for p in pages]
        assert ctx.plan is not None
        lv = self.page_layers(ctx.wiki_pages, self.symbol_layers(ctx.plan))
        ctx.wiki_levels = sorted(set(lv.values()))
        ctx.wiki_level_of = lv
        ctx.wiki_done = []

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.plan is None:
            raw = P.read_json(X.BATCHES.locate(ctx))
            if X.check_batches(raw):
                return P.Outcome(P.FAIL, "층 계획을 읽지 못했다", [self.row(t0, False, "층 계획을 읽지 못했다")])
            ctx.plan = cast(survey_plan.SurveyPlan, raw)
        self.prepare(ctx)
        return super().perform(ctx)

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.wiki_levels)

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        k = ctx.wiki_levels[rnd]
        here = [pg for pg in ctx.wiki_pages if ctx.wiki_level_of[pg["file"]] == k
                and not os.path.exists(os.path.join(ctx.repo, "docs", "wiki", pg["file"]))]
        lower = "\n".join("  - %s — %s" % (pg["file"], pg.get("title") or pg["file"]) for pg in ctx.wiki_done)
        ctx.wiki_done = ctx.wiki_done + here
        return [(pg["file"], self.wiki_page_prompt(ctx.repo, ctx.root, pg, lower)) for pg in here]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "write-wiki/" + row["stage"]
        return out
```

⚠ `LlmStage.perform` 은 빈 `jobs` 를 그대로 `run_layer` 에 넘기고 `run_layer` 는 빈 목록에 빈 결과를 낸다 — 층에 쓸 장이 없어도 죽지 않는다. `runner/test_run_mode1.py` 의 `test_빈_층은_LLM_Model을_부르지_않는다` 가 그것을 고정한다.

- [ ] **Step 4: `run_mode1.py` 원본 지우고 파사드** — 네 정의와 include 블록을 지운다. 파사드 블록에:

```python
from mode1.wiki import OutlineWikiStage, WriteWikiStage  # noqa: E402
wiki_catalogue_prompt = OutlineWikiStage.wiki_catalogue_prompt
symbol_layers = WriteWikiStage.symbol_layers
page_layers = WriteWikiStage.page_layers
wiki_page_prompt = WriteWikiStage.wiki_page_prompt
```

- [ ] **Step 5: `runner/test_run_mode1.py:757`** — `assert "wiki-plan.json" in p` → `assert "outline.json" in p`. 그 위 include 블록의 설명 줄(`# 위키 카탈로그 단계의 프롬프트가 wiki-plan.json 을 …`)은 xmldoc 주입이라 손대지 않는다.

- [ ] **Step 6: 통과** — `test_mode1.py` `42 passed` · `test_run_mode1.py` `74 passed` · **Step 7: 형 검사** `0 errors`
- [ ] **Step 8: 커밋** — `git add runner/mode1/wiki.py runner/run_mode1.py runner/test_mode1.py runner/test_run_mode1.py` · `[feat] : wiki 를 outline-wiki 와 write-wiki 로 쪼갬`

---

### Task 10: 전이표 · 팩토리 · 별명 · `--cold` — `edges.py` (D13 · D9)

**Files:**
- Create: `runner/mode1/edges.py`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import edges as E`, 끝에:

```python
# ── 10. 흐름 — 순서 · 별명 · 전이표 · 팩토리 ────────────────────────────


def test_증분은_열둘_전량은_열하나():
    assert len(E.ORDER) == 12
    assert "detect-changes" not in E.plan_stages(None, None, cold=True)
    assert "detect-changes" in E.plan_stages(None, None, cold=False)
    assert "snapshot-sources" in E.plan_stages(None, None, cold=True)


def test_순서의_불변식_셋():
    i = E.ORDER.index
    assert i("detect-changes") < i("collect-graph") < i("schedule-batches") < i("annotate-symbols")
    assert i("annotate-symbols") + 1 == i("snapshot-sources") < i("verify-terms")   # 지문은 조사 바로 뒤
    assert i("verify-terms") < i("outline-wiki") < i("write-wiki") < i("publish-wiki") < i("verify-wiki")


def test_별명은_쪼갠_단계로_펴진다():
    assert E.expand(["lang-select", "publish-wiki"]) == ["lang-hint", "lang-decide", "publish-wiki"]
    assert E.expand(["wiki"]) == ["outline-wiki", "write-wiki"]
    assert E.expand(["warmup", "survey"]) == ["detect-changes", "annotate-symbols"]


def test_모르는_단계는_거부한다():
    with pytest.raises(ValueError):
        E.plan_stages(["없는-단계"], None)


def test_전량_그래프는_이름이_다르고_표는_같다(tmp_path: Path):
    cold = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    warm = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    assert E.build_mode1_graph(cold, None, None).name == "mode1-cold"
    assert E.build_mode1_graph(warm, None, None).name == "mode1-warm"
    assert E.EDGES.dest("annotate-symbols", P.SKIP) == P.NEXT


def test_전량에서는_annotate_symbols_가_SKIP_을_내지_않는다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    reading = Path(X.READING.locate(c)); reading.parent.mkdir(parents=True); reading.write_text("{}")
    assert SV.AnnotateSymbolsStage().perform(c).kind == P.OK      # 층이 0개라 세션 없이 OK. 전량은 diff 를 안 본다


def test_증분_그래프는_diff_를_읽는_단계가_둘이다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    g = E.build_mode1_graph(c, only=None, skip=None)
    readers = [n for n in g.order if X.CHANGES in g.stages[n].reads(c)]
    assert set(readers) == {"collect-graph", "schedule-batches", "annotate-symbols"}


def test_팩토리는_어긋난_그래프를_거부한다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path))
    with pytest.raises(P.GraphError):
        E.build_mode1_graph(c, only=["annotate-symbols"], skip=None)   # 계획도 diff 도 없다


def test_재개는_그_앞을_잘라_낸다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"nodes": [], "edges": []}')
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "x"}')
    g = E.build_mode1_graph(c, None, None, start_at="schedule-batches")
    assert g.order[0] == "schedule-batches"
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.edges'`

- [ ] **Step 3: `edges.py` 신설**

```python
"""Mode 1 의 흐름 — 단계 순서 · 전이표 하나 · 팩토리. 단계는 자기 다음을 모른다."""
from collections.abc import Iterable

import pipeline as P
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.graph import CollectGraphStage, ScheduleBatchesStage
from mode1.lang import LangDecideStage, LangHintStage
from mode1.scan import DetectChangesStage, SnapshotSourcesStage
from mode1.survey import AnnotateSymbolsStage
from mode1.terms import VerifyTermsStage
from mode1.wiki import OutlineWikiStage, PublishWikiStage, VerifyWikiStage, WriteWikiStage

ORDER = ["lang-hint", "lang-decide", "detect-changes", "collect-graph", "schedule-batches",
         "annotate-symbols", "snapshot-sources", "verify-terms", "outline-wiki", "write-wiki",
         "publish-wiki", "verify-wiki"]

# 전량 그래프에는 없는 단계. 대조할 옛 지문이 없는데 대조 단계를 돌리지 않는다.
WARM_ONLY = {"detect-changes"}

# 옛 이름. `--only lang-select` 처럼 옛 명령줄이 그대로 돌게 한다.
ALIASES = {
    "lang-select": ["lang-hint", "lang-decide"], "warmup": ["detect-changes"],
    "prep": ["collect-graph"], "survey-plan": ["schedule-batches"],
    "survey": ["annotate-symbols"], "warmup-save": ["snapshot-sources"],
    "terms": ["verify-terms"], "wiki": ["outline-wiki", "write-wiki"],
    "wiki-catalogue": ["outline-wiki"], "wiki-pages": ["write-wiki"],
    "build": ["publish-wiki"], "check": ["verify-wiki"],
}

STAGES: dict[str, P.Stage[Mode1Context]] = {
    "lang-hint": LangHintStage(), "lang-decide": LangDecideStage(),
    "detect-changes": DetectChangesStage(), "collect-graph": CollectGraphStage(),
    "schedule-batches": ScheduleBatchesStage(), "annotate-symbols": AnnotateSymbolsStage(),
    "snapshot-sources": SnapshotSourcesStage(), "verify-terms": VerifyTermsStage(),
    "outline-wiki": OutlineWikiStage(), "write-wiki": WriteWikiStage(),
    "publish-wiki": PublishWikiStage(), "verify-wiki": VerifyWikiStage(),
}

# 전이표는 **하나**다. 전량과 증분의 차이는 단계 목록(`WARM_ONLY`)과 `ctx.cold` 가 만든다.
# 갈래 선언(`emits`)은 클래스에 있으므로 표가 하나여야 두 그래프 모두 완결성 검사를 통과한다.
EDGES = P.Edges({
    ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT,
    ("lang-hint", P.SKIP): P.NEXT,          # 제안 없이 파일 수로 고른다 (D4 의 폴백)
    ("outline-wiki", P.SKIP): P.NEXT,       # 목차가 이미 있다
    ("annotate-symbols", P.SKIP): P.NEXT,   # 바뀐 파일 0개 — 증분에서만 실제로 난다
})


def expand(names: Iterable[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        out += ALIASES.get(n, [n])
    return out


def plan_stages(only: Iterable[str] | None, skip: Iterable[str] | None,
                cold: bool = False) -> list[str]:
    """`--only` · `--skip` · 전량 여부만 본다. 재개 건너뛰기는 갈래(SKIP)와 재개 JSON 이 한다."""
    o = set(expand(only)) if only else None
    s = set(expand(skip or [])) | (WARM_ONLY if cold else set())
    for n in (o or set()) | s:
        if n not in ORDER:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (n, ", ".join(ORDER)))
    return [n for n in ORDER if (o is None or n in o) and n not in s]


def build_mode1_graph(ctx: Mode1Context, only: Iterable[str] | None,
                      skip: Iterable[str] | None,
                      start_at: str | None = None) -> P.StageDagGraph[Mode1Context]:
    """진입점에서 부른다. `start_at` 은 재개 JSON 이 준 단계다 — 그 앞을 잘라 낸다."""
    names = plan_stages(only, skip, cold=ctx.cold)
    if start_at is not None:
        if start_at not in names:
            raise ValueError("재개할 단계가 흐름에 없다: %s" % start_at)
        names = names[names.index(start_at):]
    name = "mode1-cold" if ctx.cold else "mode1-warm"
    return P.build_graph(name, names, {n: STAGES[n] for n in names},
                         EDGES, P.existing(X.ARTIFACTS, ctx), ctx)
```

- [ ] **Step 4: 통과** `51 passed` · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/edges.py runner/test_mode1.py` · `[feat] : mode1 전이표와 팩토리, 증분과 전량 그래프`

---

### Task 11: 재개 JSON — `resume.py` (D12)

**Files:**
- Create: `runner/mode1/resume.py`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — 머리에 `from mode1 import resume as Z`, 끝에:

```python
# ── 11. 재개 JSON ───────────────────────────────────────────────────────


def test_재개_문서는_어디서_왜_멈췄는지를_담는다(tmp_path: Path):
    rows: list[M.StageRow] = [
        {"stage": "collect-graph", "seconds": 1.0, "usage": M.normalize_usage(None), "ok": True, "why": ""},
        {"stage": "annotate-symbols/L0-B00", "seconds": 2.0, "usage": M.normalize_usage(None), "ok": False, "why": "터짐"},
    ]
    p = str(tmp_path / "resume.json")
    Z.write_resume(p, graph="mode1-warm", rows=rows, order=["collect-graph", "annotate-symbols", "verify-terms"])
    got = Z.read_resume(p)
    assert got is not None
    assert got["failed_at"] == "annotate-symbols" and got["done"] == ["collect-graph"] and got["graph"] == "mode1-warm"


def test_실패가_없으면_재개_문서를_쓰지_않는다(tmp_path: Path):
    p = str(tmp_path / "r.json")
    assert Z.write_resume(p, graph="mode1-warm", rows=[], order=["collect-graph"]) is None
    assert not os.path.exists(p)


def test_다른_그래프의_재개_문서는_거부한다(tmp_path: Path):
    p = str(tmp_path / "r.json")
    rows: list[M.StageRow] = [{"stage": "collect-graph", "seconds": 0.0, "usage": M.normalize_usage(None), "ok": False, "why": "x"}]
    Z.write_resume(p, graph="mode1-cold", rows=rows, order=["collect-graph"])
    assert Z.start_stage(Z.read_resume(p), for_graph="mode1-warm") is None
    assert Z.start_stage(Z.read_resume(p), for_graph="mode1-cold") == "collect-graph"
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.resume'`

- [ ] **Step 3: `resume.py` 신설**

```python
"""재개 JSON. 모든 중단이 이것을 남기고, 팩토리가 이것을 읽어 멈춘 자리부터 짓는다."""
import json
import os
from typing import TypedDict

import measure as M
import pipeline as P


class ResumeDoc(TypedDict):
    graph: str
    failed_at: str
    why: str
    done: list[str]
    rows: list[M.StageRow]


def write_resume(path: str, graph: str, rows: list[M.StageRow], order: list[str]) -> ResumeDoc | None:
    """실패한 행이 없으면 아무것도 쓰지 않고 `None`. 있으면 쓴다."""
    failed = [r for r in rows if not r.get("ok") and not r.get("skipped")]
    if not failed:
        return None
    failed_at = failed[0]["stage"].split("/")[0]
    done = [n for n in order if n != failed_at and order.index(n) < order.index(failed_at)]
    doc: ResumeDoc = {"graph": graph, "failed_at": failed_at,
                      "why": failed[0].get("why") or "", "done": done, "rows": rows}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return doc


def read_resume(path: str) -> ResumeDoc | None:
    top = M.as_map(P.read_json(path))
    graph, at = M.as_str(top.get("graph")), M.as_str(top.get("failed_at"))
    if not graph or not at:
        return None
    done = [x for x in M.as_list(top.get("done")) if isinstance(x, str)]
    return {"graph": graph, "failed_at": at, "why": M.as_str(top.get("why")),
            "done": done, "rows": []}


def start_stage(doc: ResumeDoc | None, for_graph: str) -> str | None:
    """이 그래프용 재개 문서면 시작할 단계를, 아니면 `None`."""
    if doc is None or doc["graph"] != for_graph:
        return None
    return doc["failed_at"]
```

`rows` 는 읽을 때 복원하지 않는다 — 측정을 이어 붙이는 것은 화면 표시용이라 이번 범위에서 뺀다.

- [ ] **Step 4: 통과** `54 passed` · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/resume.py runner/test_mode1.py` · `[feat] : 재개 json 쓰기와 읽기`

---

### Task 12: `main` 을 그래프 위로 · 옛 `run_*` 삭제 · 없앤 이름의 시험 삭제

**Files:**
- Modify: `runner/run_mode1.py`
- Modify: `runner/test_run_mode1.py` (없앤 이름의 시험 **17개** 삭제 — 아래 목록)

- [ ] **Step 1: 기준선** — 두 명령의 출력을 파일로 남겨 둔다:

```bash
.venv/bin/python runner/run_mode1.py . --dry-run > /tmp/m1-dry-before.txt 2>&1
.venv/bin/python runner/run_mode1.py . --only prep --dry-run > /tmp/m1-prep-before.txt 2>&1
```

- [ ] **Step 2: `main` 을 다시 쓴다** — 파사드 블록 아래에 이 import 를 두고:

```python
from mode1 import context as X  # noqa: E402
from mode1 import diff, resume  # noqa: E402
from mode1.context import Mode1Context  # noqa: E402
from mode1.edges import ORDER as STAGES, build_mode1_graph, expand, plan_stages  # noqa: E402,F401
```

`main` 전체를 이것으로 바꾼다:

```python
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    # 별명이 아니라 정확한 ID 를 적는다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.
    ap.add_argument("--model", default="claude-sonnet-5", help="배치·장 세션이 쓸 Model")
    ap.add_argument("--concurrency", type=int, default=8, help="한 층에서 동시에 띄울 세션 수")
    ap.add_argument("--target", type=int, default=8, help="배치당 목표 심볼 수")
    ap.add_argument("--hops", type=int, default=1, help="바뀐 파일에서 파급을 몇 홉 퍼뜨릴지")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
    ap.add_argument("--cold", action="store_true", help="전량. 옛 지문으로 좁히지 않는다")
    ap.add_argument("--resume", action="store_true", help="resume.json 이 있으면 멈춘 자리부터")
    a = ap.parse_args(argv)

    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(repo):
        print("에러 — 저장소가 없다: %s" % repo, file=sys.stderr)
        return 1
    ctx = Mode1Context(root=ROOT, model=a.model, timeout=a.timeout, concurrency=a.concurrency,
                       repo=repo, target=a.target, hops=a.hops, cold=a.cold)
    start = None
    if a.resume:
        start = resume.start_stage(resume.read_resume(X.RESUME.locate(ctx)),
                                   "mode1-cold" if a.cold else "mode1-warm")
        if start is None:
            print("에러 — 이 그래프용 resume.json 이 없다", file=sys.stderr)
            return 1
    try:
        graph = build_mode1_graph(ctx, only=a.only.split(",") if a.only else None,
                                  skip=a.skip.split(",") if a.skip else None, start_at=start)
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    print("대상 %s" % repo)
    print("LLM Model %s · 흐름 %s · 단계 %s" % (a.model, graph.name, " -> ".join(graph.order)))
    if a.dry_run:
        print(graph.render())
        d = diff.read_diff(X.CHANGES.locate(ctx))
        cg = X.CODEGRAPH.locate(ctx)
        if "schedule-batches" in graph.order and os.path.exists(cg):
            raw = P.read_json(cg)
            if not X.check_codegraph(raw):
                only = None if a.cold else (d["targets"] if d else None)
                미리 = survey_plan.plan(cast(survey_plan.CodeGraph, raw), a.target, only_files=only)
                print("\n층 계획 (기계가 결정론으로 낸다)%s" % (" — diff 로 좁힘" if only else ""))
                for line in ScheduleBatchesStage.plan_summary(미리):
                    print(line)
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode1Context]().run(graph, ctx)
    wall = time.monotonic() - t_all
    doc = resume.write_resume(X.RESUME.locate(ctx), graph.name, rows, graph.order)
    if doc:
        print("멈춤 — %s 에서. 재개: --resume  (%s)" % (doc["failed_at"], X.RESUME.locate(ctx)),
              file=sys.stderr)
    elif os.path.exists(X.RESUME.locate(ctx)):
        os.remove(X.RESUME.locate(ctx))

    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % hms(wall))
    print("=" * 72)
    print(format_report(rows, wall_seconds=wall))
    print("\n단계 소계 — 병렬이라 행의 초 합계는 벽시계가 아니다")
    for name, u in stage_totals(rows).items():
        print("  %-16s 토큰 %12s · 턴 %3d · 비용 $%.4f"
              % (name, "{:,}".format(u["total"]), u["turns"], u["cost_usd"]))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": a.model, "graph": graph.name, "stages": rows,
                       "stage_totals": stage_totals(rows), "concurrency": a.concurrency,
                       "target": a.target, "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": wall}, f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)
    return 0 if all(r["ok"] or r.get("skipped") for r in rows) else 1
```

`ScheduleBatchesStage` 는 Task 5 의 파사드 import 로 이미 들어와 있다.

- [ ] **Step 3: 옛 것을 지운다** — `run_machine` · `run_lang_select` · `run_warmup` · `save_warmup` · `run_survey` · `run_wiki` · `is_agent_stage` · `should_call_agent` · 옛 `plan_stages` · `STAGES` · `AGENT_STAGES` · `LANG_SELECT_MODEL` 의 정의와 include 블록, `# ── 1. 단계 고르기` 절 머리, 그리고 파일 머리 독스트링의 "열 단계" 표를 12단계 표로 바꾼다(단계 이름 · 기반 · 부르는 것 세 칸). `Heartbeat` · `Iterable` · `Mapping` · `declmap` · `warmup` · `subprocess` 등 안 쓰이게 된 import 를 pyright 가 짚는 대로 뺀다. `_bootstrap_venv` 와 `sys.path` 삽입은 그대로다. **`grep -c "for stage in" runner/run_mode1.py` 가 0 이어야 한다.**

- [ ] **Step 4: `runner/test_run_mode1.py` 에서 없앤 이름의 시험 17개를 지운다** — 옮긴 것이 아니라 없앤 것이라 파사드로 살릴 수 없다. 각 시험 위의 include 블록 3줄도 함께.

옛 `plan_stages(has_codegraph, has_reading, has_prose, …)` (11개 — 새 `plan_stages(only, skip, cold)` 와 서명이 다르다):
`test_빈_저장소면_열_단계를_순서대로_돈다` · `test_산출물이_있는_LLM_단계만_각자_빠진다` · `test_plan_keeps_prep_even_when_codegraph_exists` · `test_plan_only_and_skip_are_honoured` · `test_plan_rejects_an_unknown_stage` · `test_skip_은_열_단계_흐름_기준으로_걸러낸다` · `test_the_save_gate_comes_before_terms` · `test_warmup_관문이_survey_를_감싼다` · `test_층_계획은_조사와_산문보다_먼저다` · `test_세_단계가_LLM_Model을_부른다` · `test_층_계획은_LLM_단계가_아니다`
`should_call_agent` (4개): `test_agent_is_skipped_when_nothing_changed_and_records_exist` · `test_agent_runs_when_something_changed` · `test_agent_runs_when_warmup_could_not_judge` · `test_agent_still_runs_when_there_are_no_records_yet`
`save_warmup` (2개): `test_survey_가_실패하면_매니페스트를_갱신하지_않는다` · `test_판정을_못_했으면_아무것도_쓰지_않는다`

이들이 지키던 불변식은 `test_mode1.py` 가 다시 지킨다 — 순서 셋(Task 10 `test_순서의_불변식_셋`) · `--only/--skip` · 모르는 단계 거부(Task 10) · 바뀐 것 없음 + 레코드 있음 → SKIP / 레코드 없음 → 돈다(Task 8) · 조사 실패 → 지문 안 찍음(Task 7). **`wiki_argv` · `terms_argv` 의 시험 3개는 남긴다** — 파사드가 살린다.

- [ ] **Step 5: 시험** — `.venv/bin/python -m pytest -q` → **실패 0.** 기대 수: 566 − 17 + (Task 2~11 이 더한 50) = **599 통과 · 19 건너뜀** 근처. 지운 시험 이름 17개를 보고에 적는다.
- [ ] **Step 6: `--dry-run` 대조** — Step 1 의 두 파일과 새 출력을 비교한다. 단계 이름이 새 이름 12개로 바뀐 것과 `graph.render()` 가 추가된 것 외에는 같아야 한다. `--only prep` 은 `ALIASES` 로 `collect-graph` 가 된다.
- [ ] **Step 7: 형 검사** — `npm run typecheck:py` → `0 errors`
- [ ] **Step 8: 커밋** — `git add runner/run_mode1.py runner/test_run_mode1.py` · `[refactor] : run_mode1 이 단계 기계 위에서 돈다`

---

### Task 13: 게이트 · 문서 · `Any` 게이트 확장 · 인계 문서 표시

**Files:** Modify `test/test_no_any.py` · `runner/README.md`(도구가 낸다) · `runner/CLAUDE.md` · `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` · `docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md` · `docs/handoffs/RESUME-2026-09-11-runner-stage-machine.md`

- [ ] **Step 1: `Any` 게이트** — `COVERED` 에 `runner/mode1/context.py` · `measured.py` · `machine_stage.py` · `diff.py` · `lang.py` · `scan.py` · `graph.py` · `survey.py` · `terms.py` · `wiki.py` · `edges.py` · `resume.py` 를 더한다(`runner/run_mode1.py` 는 이미 있다). 통과해야 한다.
- [ ] **Step 2: 게이트 일곱**

```bash
.venv/bin/python -m pytest -q          # 실패 0
npm test                               # 8
npm run typecheck && npm run typecheck:py
.venv/bin/python machine/xmldoc.py check ; echo $?    # 문제 수 = 266 + 지운 include 블록 수. 적어 둔다
.venv/bin/python tools/gen_readme.py machine runner viz tools && .venv/bin/python tools/gen_readme.py --check machine runner viz tools
npm run doctor
```

- [ ] **Step 3: `runner/CLAUDE.md`** — "무엇이 여기 있나" 표의 `run_mode1.py` 행을 12단계 · `mode1/` 패키지(모듈 여섯 + `context` · `measured` · `machine_stage` · `diff` · `edges` · `resume`)로 고친다. `--cold` · `--resume` · `changes.json` 을 한 줄씩. "Gotcha — `run_mode1.py` 만 `machine/` 을 import 한다" 를 "`mode1/` 패키지가" 로.
- [ ] **Step 4: 스펙에 되돌려 적을 것 넷** — ① D4 의 폴백이 `FAIL→lang-decide` 가 아니라 `SKIP→NEXT` 로 구현된 것 · ② 전량 그래프에 `detect-changes` 가 없고 `snapshot-sources` 가 직접 훑는다는 것(D13 그림은 그대로) · ③ D2 가 `AnnotateSymbolsStage` 에서 문맥 칸으로 지켜졌다는 것 · ④ **D7 의 모양이 바뀐 것** — 자유 함수 모음(`layers` · `prompts`)이 아니라 단계에 종속된 메서드와 믹스인(규칙 R4). `snapshot-sources` 의 `writes` 가 첫 전량 + 언어 모름에서 `FAIL` 이 되는 것도 한 줄.
- [ ] **Step 5: 인계 문서 배너 갱신** — `HANDOFF-2026-09-07-warmup-increment-unreachable.md` 의 🔴 배너를 "리팩터링 끝. ③④ 착수 가능. 고칠 자리: `runner/mode1/survey.py` 의 `AnnotateSymbolsStage.harvest` 와 `merge_shards`, `machine/survey_plan.py` 의 배치 id" 로. `RESUME-2026-09-11-runner-stage-machine.md` 의 TL;DR 을 "3단계 완료" 로.
- [ ] **Step 6: 커밋** — `[docs] : mode1 단계 기계 완료를 문서와 게이트에 반영`

---

## 완료 조건

- [ ] `runner/run_mode1.py` 에 `for stage in` 루프가 없다 — `grep -c "for stage in" runner/run_mode1.py` = 0
- [ ] `runner/mode1/` 에 `def ` 로 시작하는 최상위 자유 함수는 `context.py`(`raw_dir` · `check_*` · `reading_path` · `snapshot_path` · `_no_*`) · `diff.py`(파일 꼴) · `edges.py`(`expand` · `plan_stages` · `build_mode1_graph`) · `resume.py`(파일 꼴) 에만 있다 — `grep -n "^def " runner/mode1/lang.py runner/mode1/scan.py runner/mode1/graph.py runner/mode1/survey.py runner/mode1/terms.py runner/mode1/wiki.py` 가 비어 있다
- [ ] `pytest` 실패 0 (지운 시험 17개는 보고에 이름이 적혀 있다)
- [ ] `test/test_no_any.py` 가 `mode1/` 전체와 `run_mode1.py` 를 덮고 통과한다
- [ ] `--dry-run` 이 `graph.render()` 로 폴백 간선을 보이고, diff 가 있으면 좁힌 층 계획을 찍는다
- [ ] `changes.json` 이 실제로 생긴다 — 자기 저장소에 `--only warmup` 으로 확인 (LLM 0)
- [ ] `--only survey` 를 diff 없이 부르면 **팩토리가 거부**한다 (`GraphError`)
- [ ] 낡은 전량 계획 + 좁힌 diff 를 두고 `--only survey` 를 부르면 **`AnnotateSymbolsStage` 가 FAIL** 로 멈춘다 — 인계 문서 재현 ② 가 더는 재현되지 않는다
- [ ] 스펙과 인계 문서가 Task 13 대로 갱신됐다

## 착수 전 사용자 판정 셋

| # | 무엇 | 어디 | 이 계획의 기본값 |
|---|---|---|---|
| ① | 둘이 쓰는 훑기 — 믹스인 한 벌 vs 두 클래스에 복제 | Task 7 | 믹스인 |
| ② | `test_run_mode1.py:757` 한 줄(`wiki-plan.json` → `outline.json`) | Task 9 | 바꾼다 |
| ③ | D15 두 걸음 (이번엔 "다시 수집할지 판정" 만) — 요약 §4-② | Task 4 | 첫 걸음만 |

## 이 계획 뒤

1. **`xmldoc emit` → `inject` 를 한 번** — 1·2·3단계가 옮긴 심볼의 마커를 재주입한다. `docs/decisions/0007` 의 `emit_xml()` 폐지 속성을 이때 함께 넣는다.
2. **결함 ③④** — 인계 문서대로. 그 뒤에 **D17 claim 파일**과 **`삭제됨` 기계 삭제**.
3. **D15 둘째 걸음** — 수집기별 부분 수집 지원을 재고 되는 것부터.
4. 증분 그래프를 실제로 쓰기 시작한다 — 그때까지 "증분이 된다" 고 말하지 않는다.
