# Mode 1 을 단계 기계 위로 (3단계) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `runner/run_mode1.py`(1,147줄)의 `if/elif` 단계 루프를 없애고, Mode 1 을 2단계가 만든 `runner/pipeline.py` 의 단계 기계 위에 올린다. 그 과정에서 `warmup` 의 판정을 `warmup-diff.json` 파일로 내보내고(D14), 증분·전량 그래프를 팩토리가 고르게 하고(D13), 재개 JSON 을 넣는다(D12).

**Architecture:** `runner/mode1/` 패키지(D7 안 A) — `context.py`(문맥·산출물) · `prompts.py`(프롬프트, 그대로 이동) · `layers.py`(층·샤드 병합, 그대로 이동) · `stages.py`(단계 12개) · `edges.py`(전이표 둘 + 팩토리). `run_mode1.py` 는 `main` 과 옛 이름 재수출만 남는다. 단계는 전부 `pipeline.MachineStage` 또는 `pipeline.LlmStage` 의 서브클래스이고, 갈래는 `OK · FAIL · SKIP` 셋만 쓴다.

**Tech Stack:** Python 3.14 · pytest · pyright strict · `runner/pipeline.py`(2단계 산출물)

**사양:** `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` 의 D4 · D7 · D12 · D13 · D14(×2) · D15 · D16
**사람용 요약:** [`2026-09-11-runner-mode1-요약.md`](2026-09-11-runner-mode1-요약.md) — 판정은 그쪽에서 받는다

---

## 이 계획이 다루는 범위와 다루지 않는 범위

| 결정 | 이 계획 | 비고 |
|---|---|---|
| D4 `lang-select` 쪼개기 | **Task 6** | |
| D7 `mode1/` 패키지 | **Task 1·2** | |
| D12 재개 JSON | **Task 10** | 단계 수준만. 배치 수준은 결함 ③ 뒤 |
| D13 증분·전량 그래프 | **Task 9** | 스펙 그림과 다른 점 하나 — 아래 "설계 메모 ①" |
| D14 ×2 `warmup-diff.json` | **Task 3 · 7** | 쓰기는 3, 양방향 대조는 7 |
| D15 `prep` 이 `targets` 를 본다 | **Task 4** | **첫 걸음만** — 아래 "설계 메모 ②" |
| D16 `wiki` 쪼개기 | **Task 8** | |
| D17 claim 파일 | ✗ | **결함 ③ 뒤.** 배치 id 가 위치 기반이라 지금 넣으면 남의 배치를 막는다 |
| `삭제됨` 기계 삭제 (D14 부속) | ✗ | 레코드를 합치는 코드가 결함 ④ 의 수정 대상이라 **④ 와 같은 자리에서** 한다. 이 계획은 `삭제됨` 을 diff.json 에 **싣기만** 한다 |
| `prep` 을 `collect` + `facts` 로 쪼개기 | ✗ | 관찰만 있고 판정이 없다. Task 4 끝에 판정 요청을 남긴다 |
| 결함 ③④ (배치 id · `merge_shards` 개명) | ✗ | 인계 문서 `HANDOFF-2026-09-07-warmup-increment-unreachable.md` 소관. **이 계획 뒤** |

**증분 그래프는 만들되 이 계획 안에서는 "된다" 고 말하지 않는다.** ③④ 가 남아 있다.

### 설계 메모 ① — 🔴 확정 (2026-09-11): 전량 그래프에는 `warmup` 이 **없다.** `warmup-save` 가 직접 훑어 지문을 찍는다

`warmup.json` 은 **옛 판의 지문**(파일마다 바이트 해시 · 선언 해시)이고, `warmup-diff.json` 은 그 지문과 지금
소스를 대조한 결과다. 전량(`--cold` · 첫 실행)에는 대조할 옛 지문이 없거나 안 쓰기로 한 것이므로
**대조 단계(`warmup`)를 돌리지 않는다.** 대신 끝의 `warmup-save` 가 **스스로 훑어** 지금 판의 지문을 찍는다 —
다음 실행이 증분을 시작할 옛 판이 되도록.

| | 전량 | 증분 |
|---|---|---|
| 단계 | `warmup` 없음 · 11개 | `warmup` 있음 · 12개 |
| `warmup-diff.json` | **안 생긴다** | 생긴다 |
| `prep` | `--force` | `--diff` |
| `survey` | 대조 없음 | 양방향 대조 |
| `warmup-save` | `ctx.entries is None` → **직접 훑어서** 찍는다 | `warmup` 이 넘긴 `entries` 를 찍는다 |

**스펙 D13 의 그림이 그대로 맞다.** 앞선 판(전량에도 `warmup`)은 물렸다 — 번복 기록 0004 의 모양이었다(두 안만
놓고 셋째를 안 찾음). **전이표는 여전히 하나**다 — `survey` 의 `SKIP` 은 선언에 있으므로 표에 간선이 있어야
하고, 전량에서는 실제로 안 난다(Task 9 시험).

**두 안 모두에 `prep --force` 가 필요했다.** 전량이 diff 없이 `prep` 을 부르면 지금의 파일-존재 판정으로
떨어져 낡은 지도를 건너뛴다. 앞선 계획에서 빠져 있던 결함이다 — Task 4 에 `--force` 가 들어간다.

### 설계 메모 ② — D15 의 첫 걸음은 "부분 수집" 이 아니라 "다시 수집할지의 판정" 이다

D15 는 `prep` 이 `targets` 를 받는 것이고, 궁극에는 바뀐 파일만 다시 수집하는 것이다. 그런데 **수집기(clang-uml · roslyn-dump · griffe)가 파일 목록을 받는지 아직 재지 않았다.** 그래서 이 계획은 D15 를 **두 걸음**으로 나누고 첫 걸음만 한다.

- **첫 걸음 (이 계획)** — `prep.py` 가 `--diff warmup-diff.json` 을 받아, diff 에 `재읽기 · 위치만 · 삭제됨` 이 하나라도 있으면 **전량 재수집**하고, 전부 `유효` 면 수집기를 건너뛴다. 지금의 `hasCodegraph`(파일 존재) 판정을 **diff 판정으로 갈아 끼우는 것**이다. 결함 ⑤(낡은 지도)가 여기서 사라진다.
- **둘째 걸음 (범위 밖)** — 수집기별로 부분 수집 지원을 재고, 되는 것부터 `targets` 만 수집한다.

## 가드레일

- **브랜치 `refactor/runner-common-axis` 에서 한다.** `main` 에서 하지 않는다.
- **커밋은 각 Task 끝에서.** 메시지는 소문자 `[tag] : subject` 한 줄 한국어, 빈 줄, `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- **`git add -A` 금지.** 경로를 좁혀 add 한다. 워킹 트리에 다른 작업의 미커밋 파일이 있으면 담지 않는다.
- **`# <include …/>` 블록은 손대지 않고 새로 심지 않는다.** 정의를 옮기면 그 위 세 줄 블록은 **함께 지운다.** `xmldoc check` 의 문제 수가 **느는 것은 예상된 결과**다 — 재주입은 이 계획 뒤 한 번에 한다.
- **`Any` 금지.** `test/test_no_any.py` 의 `COVERED` 에 새 파일을 전부 넣는다(Task 12).
- **코드 주석에는 현 상황만.** 날짜 · 수치 · 확신도 · 설계 철학을 코드에 넣지 않는다.
- **`runner/test_run_mode1.py`(963줄)는 고치지 않는다.** 옛 이름을 `run_mode1.py` 가 재수출하므로 그대로 통과해야 한다. 통과하지 않으면 파사드가 틀린 것이다.
- **실제 `survey` 를 돌려 검증하지 마라.** 세션당 약 $0.5 다. `--dry-run` 과 순수 함수 시험까지만.
- 기준선 (🔵 2026-09-11): `pytest` **562 통과 · 19 건너뜀**. `xmldoc check` 는 착수 직전에 다시 재서 적어 둔다.

## File Structure

| 파일 | 책임 | 어디서 오나 |
|---|---|---|
| `runner/mode1/__init__.py` | 빈 파일 | 신설 |
| `runner/mode1/context.py` | `Mode1Context` · 산출물 `Artifact` 10개 · 산출물 `check` 함수들 | 신설 |
| `runner/mode1/diff.py` | `WarmupDiff` 형 · 쓰기 · 읽기 · 검사 · 계획과의 양방향 대조 | 신설 (D14) |
| `runner/mode1/prompts.py` | `warmup_section` · `dep_excerpt` · `survey_batch_prompt` · `nonnode_prompt` · `wiki_catalogue_prompt` · `wiki_page_prompt` · `reading_path` | `run_mode1.py` 에서 **그대로 이동** |
| `runner/mode1/layers.py` | `symbol_layers` · `page_layers` · `merge_shards` · `_qualified` · `plan_summary` · `WikiPage` · `Record` · `Records` | 그대로 이동 |
| `runner/mode1/stages.py` | 단계 12개 클래스 + `MODE1_STAGES` | 신설. 본문은 `run_lang_select` · `run_warmup` · `save_warmup` · `run_survey` · `run_wiki` 에서 옮긴다 |
| `runner/mode1/edges.py` | `EDGES` · `ALIASES` · `expand` · `plan_stages` · `build_mode1_graph` | 신설 (D13 · D9) |
| `runner/mode1/resume.py` | `ResumeDoc` 형 · 쓰기 · 읽기 · 팩토리에 먹이기 | 신설 (D12) |
| `runner/run_mode1.py` | `main` + argparse + 재수출 파사드. `_bootstrap_venv` 는 그대로 | 축소 |
| `runner/wiki/prep.py` | `--diff` 인자 하나 추가 | 얼갈이 경계를 한 파일만큼 연다 (D15) |
| `runner/test_mode1.py` | 위 신설 모듈의 시험 | 신설 |

**단계 12개와 그 원본**

| 단계 | 기반 | 원본 (`run_mode1.py`) |
|---|---|---|
| `lang-propose` | `LlmStage` | `run_lang_select` 의 앞 절반 (모형 호출 · 낱말 파싱) |
| `lang-decide` | `MachineStage` | `run_lang_select` 의 뒤 절반 (`machine/lang_select.py` 호출) |
| `prep` | `MachineStage` | `main` 의 `wiki_argv(..., "prep.py")` 가지 |
| `warmup` | `Stage` (직접) | `run_warmup` + **diff 쓰기** |
| `survey-plan` | `Stage` (직접) | `main` 의 `survey-plan` 가지 |
| `survey` | `LlmStage` | `run_survey` + **diff 대조** |
| `warmup-save` | `Stage` (직접) | `save_warmup` |
| `terms` | `MachineStage` | `main` 의 `terms_argv` 가지 |
| `wiki-catalogue` | `LlmStage` | `run_wiki` 의 앞 절반 |
| `wiki-pages` | `LlmStage` | `run_wiki` 의 뒤 절반 |
| `build` · `check` | `MachineStage` | `main` 의 `wiki_argv` 가지 |

`warmup` · `survey-plan` · `warmup-save` 는 자식 프로세스도 LLM 도 아닌 **같은 프로세스의 파이썬**이라 `Stage` 를 직접 상속한다. 셋 다 행 하나에 토큰 0이다.

---

### Task 1: `mode1/` 패키지 뼈대 · `Mode1Context` · 산출물 선언

**Files:**
- Create: `runner/mode1/__init__.py` (빈 파일)
- Create: `runner/mode1/context.py`
- Create: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

`runner/test_mode1.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mode1 import context as X  # noqa: E402


def _ctx(tmp_path: object) -> X.Mode1Context:
    return X.Mode1Context(root="/r", model="m", repo=str(tmp_path))


def test_문맥의_기본값은_전량이_아니다(tmp_path):
    c = _ctx(tmp_path)
    assert c.cold is False and c.targets is None and c.plan is None


def test_산출물은_저장소_아래_자리를_가리킨다(tmp_path):
    c = _ctx(tmp_path)
    assert X.CODEGRAPH.locate(c).endswith(os.path.join("out", "codegraph-raw", "codegraph.json"))
    assert X.WARMUP_DIFF.locate(c).endswith("warmup-diff.json")
    assert X.SURVEY_PLAN.locate(c).endswith("survey-plan.json")


def test_코드지도_검사는_최상위_열쇠만_본다():
    assert X.check_codegraph({"nodes": [], "edges": []}) == []
    assert X.check_codegraph({"nodes": "x"}) != []
    assert X.check_codegraph([]) != []


def test_층계획_검사는_층과_합계를_본다():
    assert X.check_plan({"target": 8, "layers": [], "totals": {}}) == []
    assert X.check_plan({"layers": {}}) != []
```

- [ ] **Step 2: 실패 확인** — `.venv/bin/python -m pytest runner/test_mode1.py -q` → `ModuleNotFoundError: No module named 'mode1'`

- [ ] **Step 3: 구현**

`runner/mode1/__init__.py` 는 빈 파일. `runner/mode1/context.py`:

```python
"""Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다."""
import os
from dataclasses import dataclass, field

import measure as M
import pipeline as P
import survey_plan
import warmup


@dataclass
class Mode1Context(P.RunContext):
    """칸마다 이름과 형이 있다. 자루(dict)는 없다."""
    repo: str = ""
    target: int = 8
    hops: int = 1
    cold: bool = False
    # 단계 사이를 건너다니는 값. 채우는 단계 → 읽는 단계.
    proposed: str | None = None                      # lang-propose → lang-decide
    targets: list[str] | None = None                 # warmup → survey-plan · survey
    entries: warmup.Manifest | None = None           # warmup → warmup-save
    warmup_cache: str | None = None                  # warmup → warmup-save
    tracked_n: int = 0                               # warmup → survey (프롬프트 쪽지)
    plan: survey_plan.SurveyPlan | None = None       # survey-plan → survey · wiki-pages
    survey_ok: bool = False                          # survey → warmup-save
    baseline: dict[str, dict[str, object]] = field(default_factory=dict)   # survey 층 사이
    merged: dict[str, dict[str, object]] = field(default_factory=dict)     # survey 층 사이
    wiki_pages: list[dict[str, object]] = field(default_factory=list)      # wiki-pages 층 사이
    wiki_levels: list[int] = field(default_factory=list)
    wiki_level_of: dict[str, int] = field(default_factory=dict)
    wiki_done: list[dict[str, object]] = field(default_factory=list)


def raw_dir(c: Mode1Context) -> str:
    return os.path.join(c.repo, "out", "codegraph-raw")


# ── 산출물 검사. 최상위 열쇠와 성긴 형까지만 본다 ────────────────────────


def check_codegraph(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["코드 지도가 객체가 아니다"]
    out: list[str] = []
    for k in ("nodes", "edges"):
        if not isinstance(top.get(k), list):
            out.append("`%s` 가 배열이 아니다" % k)
    return out


def check_plan(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["층 계획이 객체가 아니다"]
    out: list[str] = []
    if not isinstance(top.get("layers"), list):
        out.append("`layers` 가 배열이 아니다")
    if not isinstance(top.get("totals"), dict):
        out.append("`totals` 가 객체가 아니다")
    return out


def check_lang_select(obj: object) -> list[str]:
    top = M.as_map(obj)
    return [] if "collector" in top else ["`collector` 가 없다"]


def check_wiki_plan(obj: object) -> list[str]:
    top = M.as_map(obj)
    return [] if isinstance(top.get("pages"), list) else ["`pages` 가 배열이 아니다"]


def check_reading(obj: object) -> list[str]:
    return [] if isinstance(obj, dict) else ["읽기 레코드가 객체가 아니다"]


# ── 산출물 선언. 자리는 ctx 가 정한다 ────────────────────────────────────

LANG_SELECT = P.Artifact[Mode1Context](
    "lang-select.json", lambda c: os.path.join(raw_dir(c), "lang-select.json"), check_lang_select)
CODEGRAPH = P.Artifact[Mode1Context](
    "codegraph.json", lambda c: os.path.join(raw_dir(c), "codegraph.json"), check_codegraph)
WARMUP_MANIFEST = P.Artifact[Mode1Context](
    "warmup.json", lambda c: os.path.join(c.repo, warmup.DEFAULT_CACHE))
WARMUP_DIFF = P.Artifact[Mode1Context](
    "warmup-diff.json", lambda c: os.path.join(raw_dir(c), "warmup-diff.json"))
SURVEY_PLAN = P.Artifact[Mode1Context](
    "survey-plan.json", lambda c: os.path.join(raw_dir(c), "survey-plan.json"), check_plan)
READING = P.Artifact[Mode1Context](
    "terms-reading.json",
    lambda c: os.path.join(c.repo, "docs", "codegraph", "terms-reading.json"), check_reading)
TERMS_DB = P.Artifact[Mode1Context](
    "terms-db.json", lambda c: os.path.join(raw_dir(c), "terms-db.json"))
WIKI_PLAN = P.Artifact[Mode1Context](
    "wiki-plan.json", lambda c: os.path.join(raw_dir(c), "wiki-plan.json"), check_wiki_plan)
WIKI_DIR = P.Artifact[Mode1Context](
    "docs/wiki", lambda c: os.path.join(c.repo, "docs", "wiki"))
RESUME = P.Artifact[Mode1Context](
    "resume.json", lambda c: os.path.join(raw_dir(c), "resume.json"))

ARTIFACTS = [LANG_SELECT, CODEGRAPH, WARMUP_MANIFEST, WARMUP_DIFF, SURVEY_PLAN,
             READING, TERMS_DB, WIKI_PLAN, WIKI_DIR, RESUME]
```

`WARMUP_DIFF` 의 `check` 는 Task 3 에서 `diff.py` 가 정의한 뒤 붙인다(순환 import 를 피하려고 여기서 안 붙인다).

⚠ `import survey_plan` · `import warmup` 은 `machine/` 이 `sys.path` 에 있어야 한다. `run_mode1.py` 가 파일 머리에서 넣는다. **시험은 `run_mode1` 을 거치지 않으므로** `test_mode1.py` 머리에 `sys.path.insert(0, os.path.join(ROOT, "machine"))` 을 더한다 — Step 1 의 시험 파일 첫 줄들을 이렇게 고친다:

```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
```

- [ ] **Step 4: 통과 확인** — `4 passed`
- [ ] **Step 5: 형 검사** — `npx pyright@1.1.413 runner/mode1/context.py runner/test_mode1.py` → `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/__init__.py runner/mode1/context.py runner/test_mode1.py` · `[add] : mode1 패키지 뼈대와 문맥, 산출물 선언`

---

### Task 2: 프롬프트와 층 코드를 그대로 옮기고 파사드로 남긴다

**Files:**
- Create: `runner/mode1/prompts.py` · `runner/mode1/layers.py`
- Modify: `runner/run_mode1.py`

- [ ] **Step 1: 기준선** — `.venv/bin/python -m pytest runner/test_run_mode1.py -q` 통과 수를 적어 둔다.

- [ ] **Step 2: `layers.py` 로 옮긴다**

`run_mode1.py` 에서 아래를 **본문 그대로** `runner/mode1/layers.py` 로 옮기고 원본은 지운다(위의 `# <include …/>` 세 줄 블록도 함께):
`Record` · `Records` · `WikiPage` · `LANG_ALIAS` · `lang_of` · `changed_seed` · `symbol_layers` · `page_layers` · `merge_shards` · `_qualified` · `plan_summary`

`layers.py` 머리:

```python
"""층 계산과 샤드 병합. 코드 지도와 읽기 레코드를 다루는 결정론 코드다."""
import json
import os
import sys
from collections.abc import Iterable, Mapping
from typing import NotRequired, TypedDict

import declmap
import measure as M
import survey_plan
import warmup
```

- [ ] **Step 3: `prompts.py` 로 옮긴다**

같은 방식으로 `reading_path` · `warmup_section` · `dep_excerpt` · `survey_batch_prompt` · `nonnode_prompt` · `wiki_catalogue_prompt` · `wiki_page_prompt` 를 `runner/mode1/prompts.py` 로. `ROOT` 를 쓰는 곳은 `prompts.py` 안에서 다시 계산한다:

```python
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

`WikiPage` · `PlanBatch` 참조는 `from mode1.layers import WikiPage` · `import survey_plan` 으로.

- [ ] **Step 4: 파사드**

`run_mode1.py` 의 `import measure` 재수출 아래에 더한다:

```python
from mode1.layers import (  # noqa: E402,F401
    Record, Records, WikiPage, LANG_ALIAS, lang_of, changed_seed,
    symbol_layers, page_layers, merge_shards, _qualified, plan_summary,
)
from mode1.prompts import (  # noqa: E402,F401
    reading_path, warmup_section, dep_excerpt, survey_batch_prompt, nonnode_prompt,
    wiki_catalogue_prompt, wiki_page_prompt,
)
```

- [ ] **Step 5: 시험이 그대로 통과** — `runner/test_run_mode1.py` 통과 수가 Step 1 과 같다. **시험 파일을 고치지 않았다.**
- [ ] **Step 6: 형 검사** — `npx pyright@1.1.413 runner/run_mode1.py runner/mode1/` → `0 errors`
- [ ] **Step 7: 커밋** — `[refactor] : mode1 프롬프트와 층 코드를 패키지로 이동`

---

### Task 3: `warmup-diff.json` — 판정을 파일로 (D14)

**Files:**
- Create: `runner/mode1/diff.py`
- Modify: `runner/mode1/context.py` (`WARMUP_DIFF` 에 `check` 붙이기)
- Modify: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
from mode1 import diff as D  # noqa: E402


def _verdicts() -> dict[str, list[str]]:
    return {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": ["gone.py"]}


def test_diff_는_넷_갈래와_범위를_담는다(tmp_path):
    p = str(tmp_path / "warmup-diff.json")
    D.write_diff(p, _verdicts(), targets=["b.py"], hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None
    assert got["targets"] == ["b.py"] and got["verdicts"]["삭제됨"] == ["gone.py"]


def test_전량이면_targets_가_None_이다(tmp_path):
    p = str(tmp_path / "d.json")
    D.write_diff(p, _verdicts(), targets=None, hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None and got["targets"] is None


def test_diff_검사는_넷_갈래가_다_있어야_통과한다():
    assert D.check_diff({"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}) == []
    assert D.check_diff({"verdicts": {"유효": []}, "targets": None, "hops": 1, "tracked": 0}) != []


def test_전체_파일_집합은_삭제됨을_뺀_셋의_합이다():
    d: D.WarmupDiff = {"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}
    assert D.all_files(d) == {"a.py", "b.py"}
```

- [ ] **Step 2: 실패 확인** — `ModuleNotFoundError: No module named 'mode1.diff'`

- [ ] **Step 3: 구현** — `runner/mode1/diff.py`:

```python
"""`warmup` 의 판정을 파일로. 옛 판(매니페스트)과 새 판(지금 소스)의 차이가 여기 남는다."""
import json
import os
from typing import TypedDict

import measure as M
import pipeline as P
import warmup

BUCKETS = ("유효", "재읽기", "위치만", "삭제됨")


class WarmupDiff(TypedDict):
    """`warmup-diff.json` 의 꼴. `targets` 가 `None` 이면 판정 불가 = 전량이다."""
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

`measure.as_list` 가 없으면 `measure.py` 에 더한다(`as_map` 옆):

```python
def as_list(v: object) -> list[object]:
    """목록이면 그것을, 아니면 빈 목록."""
    return list(cast(list[object], v)) if isinstance(v, list) else []
```

`context.py` 의 `WARMUP_DIFF` 선언을 이렇게 바꾼다 — `diff.py` 가 `context` 를 import 하지 않으므로 순환이 없다:

```python
from mode1.diff import check_diff
WARMUP_DIFF = P.Artifact[Mode1Context](
    "warmup-diff.json", lambda c: os.path.join(raw_dir(c), "warmup-diff.json"), check_diff)
```

- [ ] **Step 4: 통과 확인** · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `git add runner/mode1/diff.py runner/mode1/context.py runner/measure.py runner/test_mode1.py runner/test_measure.py` · `[add] : warmup 판정을 warmup-diff.json 으로 내보내는 형과 검사`

---

### Task 4: `prep` 이 diff 를 읽는다 (D15 첫 걸음)

**Files:**
- Modify: `runner/wiki/prep.py` (`--diff` 인자 · `prepPlan` 의 판정 교체)
- Modify: `test/test_wiki.py` (prepPlan 시험이 있으면) 또는 `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — `runner/test_mode1.py` 에:

```python
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

`verdicts=None` 이고 `force` 가 없으면 지금 동작(파일 존재만 봄)을 유지한다 — 사람이 `prep.py` 를 직접
부를 때다. 전량 그래프는 **`--force`** 를 넘긴다.

- [ ] **Step 2: 실패 확인** — `AttributeError: module 'prep' has no attribute 'needs_collect'`

- [ ] **Step 3: 구현** — `runner/wiki/prep.py` 에 `prepPlan` 위에 더한다:

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

`prepPlan` 의 서명에 `verdicts: dict[str, list[str]] | None = None, force: bool = False` 를 더하고, 첫 분기 `if hasCodegraph:` 를 `if not needs_collect(hasCodegraph, verdicts, force):` 로 바꾼다.

`main` 의 `sys.argv` 처리를 이렇게 바꾼다 (`if len(sys.argv) < 2:` 부터 `repoArg = sys.argv[1]` 까지를 대체):

```python
    ap = argparse.ArgumentParser(description="정적 수집 → 코드 지도 → 사실 파일 · 모듈 그림")
    ap.add_argument("repo")
    ap.add_argument("--diff", default=None, help="warmup-diff.json. 있으면 그 판정으로 재수집 여부를 정한다")
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

그리고 `plan = prepPlan(...)` 호출에 `verdicts=verdicts, force=a.force` 를 넘긴다(`prepPlan` 서명에도 `force: bool = False` 를 더한다). `import argparse` · `import json` 을 머리에 더한다.

- [ ] **Step 4: 통과 확인** · 기존 `test/test_wiki.py` 도 그대로 통과
- [ ] **Step 5: 커밋** — `[feat] : prep 이 warmup-diff 를 받아 재수집 여부를 정한다`

**판정 요청 (Task 4 끝에 사용자에게):** `prep` 의 뒤 절반(`facts` · `render-modules`)은 위키 재료라 diff 와 무관하다. `prep` 을 `collect` + `facts` 로 쪼갤지 판정을 받는다. **이 계획은 쪼개지 않는다** — 판정이 "쪼갠다" 면 Task 5 에 단계 하나가 는다.

---

### Task 5: 기계 단계 다섯 — `prep` · `survey-plan` · `warmup-save` · `terms` · `build` · `check`

**Files:**
- Create: `runner/mode1/stages.py`
- Modify: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
from mode1 import stages as S  # noqa: E402


def test_기계_단계는_저장소를_cwd_로_한다(tmp_path):
    c = _ctx(tmp_path)
    for st in (S.PrepStage(), S.TermsStage(), S.BuildStage(), S.CheckStage()):
        assert st.cwd(c) == c.repo


def test_prep_은_전량이면_force_증분이면_diff_를_넘긴다(tmp_path):
    c = _ctx(tmp_path); c.cold = True
    assert "--force" in S.PrepStage().argv(c) and "--diff" not in S.PrepStage().argv(c)
    c.cold = False
    assert "--diff" in S.PrepStage().argv(c) and "--force" not in S.PrepStage().argv(c)


def test_survey_plan_은_diff_의_targets_로_좁힌다(tmp_path, monkeypatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"nodes": [], "edges": []}')
    seen: dict[str, object] = {}
    def fake_plan(cg, target, only_files=None):
        seen["only"] = only_files
        return {"target": target, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}
    monkeypatch.setattr(S.survey_plan, "plan", fake_plan)
    c.targets = ["x.py"]
    out = S.SurveyPlanStage().perform(c)
    assert out.kind == S.P.OK and seen["only"] == ["x.py"] and c.plan is not None


def test_warmup_save_는_조사가_실패하면_쓰지_않는다(tmp_path, monkeypatch):
    c = _ctx(tmp_path); c.entries = {}; c.warmup_cache = str(tmp_path / "w.json")
    c.cold = False
    wrote: list[str] = []
    monkeypatch.setattr(S.warmup, "save", lambda p, e: wrote.append(p) or e)
    c.survey_ok = False
    S.WarmupSaveStage().perform(c)
    assert wrote == []
    c.survey_ok = True
    S.WarmupSaveStage().perform(c)
    assert wrote == [c.warmup_cache]


def test_warmup_save_는_전량이면_직접_훑어_찍는다(tmp_path, monkeypatch):
    c = _ctx(tmp_path); c.cold = True; c.survey_ok = True
    monkeypatch.setattr(S, "scan_fingerprints",
                        lambda ctx: ({"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}, {"a.py": {}}, str(tmp_path / "w.json")))
    wrote: list[str] = []
    monkeypatch.setattr(S.warmup, "save", lambda p, e: wrote.append(p) or e)
    S.WarmupSaveStage().perform(c)
    assert wrote == [str(tmp_path / "w.json")]
```

`survey_ok` 는 Task 1 에서 선언한 문맥 칸이다 — `save_warmup` 이 `rows` 를 뒤져 `survey/` 행을 찾던 것을 칸 하나로 바꾼다. `SurveyStage.harvest` 가 끝에서 세팅한다(Task 7).

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현** — `runner/mode1/stages.py`:

```python
"""Mode 1 의 단계 12개. 기계 여섯 · LLM 넷 · 같은 프로세스의 파이썬 셋."""
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from typing import cast

import declmap
import measure as M
import pipeline as P
import survey_plan
import warmup
from mode1 import context as X
from mode1 import diff as D
from mode1 import layers as L
from mode1 import prompts as R
from mode1.context import Mode1Context

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _row(name: str, t0: float, ok: bool, why: str = "") -> M.StageRow:
    return {"stage": name, "seconds": time.monotonic() - t0,
            "usage": M.normalize_usage(None), "ok": ok, "why": why}


# ── 기계 단계 — 자식 프로세스 하나 ───────────────────────────────────────


class Mode1Machine(P.MachineStage[Mode1Context]):
    def cwd(self, ctx: Mode1Context) -> str:
        return ctx.repo


class PrepStage(Mode1Machine):
    name = "prep"

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = [sys.executable, os.path.join(ctx.root, "runner", "wiki", "prep.py"), ctx.repo]
        if ctx.cold:
            argv.append("--force")
        else:
            argv += ["--diff", X.WARMUP_DIFF.locate(ctx)]
        return argv

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [] if ctx.cold else [X.WARMUP_DIFF]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]


class TermsStage(Mode1Machine):
    name = "terms"

    def argv(self, ctx: Mode1Context) -> list[str]:
        cg, rd = X.CODEGRAPH.locate(ctx), X.READING.locate(ctx)
        argv = [sys.executable, os.path.join(ctx.root, "machine", "terms_db.py")]
        if os.path.exists(cg):
            argv.append(cg)
        argv += ["--repo", ctx.repo]
        if os.path.exists(rd):
            argv += ["--reading", rd]
        return argv

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]


class BuildStage(Mode1Machine):
    name = "build"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return [sys.executable, os.path.join(ctx.root, "runner", "wiki", "build.py"), ctx.repo]

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]


class CheckStage(Mode1Machine):
    name = "check"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return [sys.executable, os.path.join(ctx.root, "runner", "wiki", "check.py"), ctx.repo]

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]


# ── 같은 프로세스의 파이썬 셋 — 자식 프로세스도 LLM 도 아니다 ────────────


class SurveyPlanStage(P.Stage[Mode1Context]):
    """코드 지도를 층과 배치로. 증분이면 diff 의 `targets` 로 좁힌다."""
    name = "survey-plan"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH] + ([] if ctx.cold else [X.WARMUP_DIFF])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.SURVEY_PLAN]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        raw = P.read_json(X.CODEGRAPH.locate(ctx))
        bad = X.check_codegraph(raw)
        if bad:
            return P.Outcome(P.FAIL, "; ".join(bad), [_row(self.name, t0, False, "; ".join(bad))])
        cg = cast(survey_plan.CodeGraph, raw)   # check 뒤의 좁히기 cast — D11 이 허용하는 꼴
        only = None if ctx.cold else ctx.targets
        ctx.plan = survey_plan.plan(cg, ctx.target, only_files=only)
        out_path = X.SURVEY_PLAN.locate(ctx)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ctx.plan, f, ensure_ascii=False, indent=1)
        print("%s%s" % (out_path, " (증분: %d파일)" % len(only) if only else ""))
        for line in L.plan_summary(ctx.plan):
            print(line)
        return P.Outcome(P.OK, "", [_row(self.name, t0, True)])


class WarmupSaveStage(P.Stage[Mode1Context]):
    """전수조사가 해낸 뒤에만 지문을 찍는다.

    증분이면 `warmup` 이 넘긴 `entries` 를 찍고, 전량이면 **여기서 직접 훑어** 찍는다 —
    전량 그래프에는 `warmup` 이 없기 때문이다. 다음 실행이 이것을 옛 판으로 쓴다.
    """
    name = "warmup-save"

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WARMUP_MANIFEST]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.entries is None:
            scanned = scan_fingerprints(ctx)
            if scanned is None:
                print("알림 — 언어를 몰라 지문을 찍지 않는다.", file=sys.stderr)
                return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
            _, ctx.entries, ctx.warmup_cache = scanned
        if not ctx.warmup_cache:
            return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
        if not ctx.survey_ok:
            print("매니페스트를 갱신하지 않는다 — 전수조사가 실패했다. "
                  "지금 갱신하면 읽지 않은 파일이 '유효' 로 남는다.", file=sys.stderr)
            return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
        warmup.save(ctx.warmup_cache, ctx.entries)
        print("매니페스트 갱신 — %s (%d개 파일)" % (ctx.warmup_cache, len(ctx.entries)))
        return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
```

- [ ] **Step 4: 통과 확인** · **Step 5: 형 검사** `0 errors`
- [ ] **Step 6: 커밋** — `[feat] : mode1 기계 단계 여섯을 단계 기계 위에`

---

### Task 6: `lang-propose` + `lang-decide` (D4)

**Files:** Modify `runner/mode1/stages.py` · `runner/mode1/prompts.py` · `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
def test_lang_propose_는_싼_모형을_고정한다(tmp_path):
    c = _ctx(tmp_path)
    assert S.LangProposeStage().model(c) == S.LANG_SELECT_MODEL


def test_lang_propose_는_낱말_하나만_받아들인다(tmp_path):
    c = _ctx(tmp_path)
    st = S.LangProposeStage()
    st.harvest(c, [("lang-propose", 1.0, 0, {"result": " `Cpp`. "})], 0)
    assert c.proposed == "cpp"
    st.harvest(c, [("lang-propose", 1.0, 0, {"result": "rust"})], 0)
    assert c.proposed is None


def test_lang_propose_는_실패해도_SKIP_이지_FAIL_이_아니다(tmp_path):
    c = _ctx(tmp_path)
    out = S.LangProposeStage().harvest(c, [("lang-propose", 1.0, 1, None)], 0)
    assert out.kind == S.P.SKIP


def test_lang_decide_는_제안이_있으면_넘긴다(tmp_path):
    c = _ctx(tmp_path)
    assert "--propose" not in S.LangDecideStage().argv(c)
    c.proposed = "py"
    assert S.LangDecideStage().argv(c)[-2:] == ["--propose", "py"]
```

**`lang-propose` 실패는 `SKIP` 이다** — 스펙 D4 의 폴백 간선 `('lang-propose', FAIL) -> 'lang-decide'` 대신, 이 단계는 **관문이 아니므로** 실패를 `SKIP` 으로 내고 전이표는 `SKIP → NEXT` 로 잇는다. 같은 효과이고 갈래를 하나 더 안 만든다. 스펙에 이 선택을 적는다(Task 12).

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현** — `stages.py` 에:

```python
LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"
LANG_WORDS = ("cpp", "cs", "py", "ts")


class LangProposeStage(P.LlmStage[Mode1Context]):
    """루트 문서를 읽혀 언어 하나를 제안받는다. 못 받아도 막지 않는다."""
    name = "lang-propose"
    emits = P.OK | P.SKIP

    def model(self, ctx: Mode1Context) -> str:
        return LANG_SELECT_MODEL

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        tool = os.path.join(ctx.root, "machine", "lang_select.py")
        docs = subprocess.run([sys.executable, tool, ctx.repo, "--print-docs"],
                              capture_output=True, text=True).stdout
        return R.lang_prompt(docs)

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        base = super().harvest(ctx, got, rnd)
        ctx.proposed = None
        for _, _, rc, result in got:
            word = M.as_str(M.as_map(result).get("result")).strip().strip("`.").lower()
            if rc == 0 and word in LANG_WORDS:
                ctx.proposed = word
        if base.kind != P.OK:
            for row in base.rows:
                row["ok"], row["why"] = True, "제안 없음 — 파일 수로 고른다"
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

`prompts.py` 에 `run_lang_select` 안에 박혀 있던 프롬프트 문자열을 `lang_prompt(docs: str) -> str` 함수로 옮긴다(본문 그대로, `docs` 만 인자로).

- [ ] **Step 4·5: 통과 · 형 검사** — **Step 6: 커밋** — `[feat] : lang-select 를 lang-propose 와 lang-decide 로 쪼갬`

---

### Task 7: `warmup` · `survey` — diff 쓰기와 양방향 대조 (D14)

**Files:** Modify `runner/mode1/stages.py` · `runner/mode1/diff.py` (`compare_plan`) · `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
def _plan_with(files: list[str]) -> dict[str, object]:
    syms = [{"name": f + ".S", "file": f} for f in files]
    return {"target": 8, "layers": [{"level": 0, "symbol_count": len(syms),
            "batches": [{"id": "L0-B00", "files": files, "symbols": syms}]}],
            "totals": {"symbols": len(syms), "edges": 0, "levels": 1, "cyclic_symbols": 0}}


def test_계획이_diff_보다_넓으면_잡는다():
    d: D.WarmupDiff = {"verdicts": {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []},
                       "targets": ["b.py"], "hops": 1, "tracked": 2}
    assert D.compare_plan(_plan_with(["a.py", "b.py"]), d) != []      # 전량 지시서 + 부분 쪽지


def test_계획이_diff_보다_좁으면_잡는다():
    d: D.WarmupDiff = {"verdicts": {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []},
                       "targets": None, "hops": 1, "tracked": 2}
    assert D.compare_plan(_plan_with(["b.py"]), d) != []               # 부분 지시서 + 전량 쪽지


def test_계획과_diff_가_맞으면_통과한다():
    d: D.WarmupDiff = {"verdicts": {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []},
                       "targets": ["b.py"], "hops": 1, "tracked": 2}
    assert D.compare_plan(_plan_with(["b.py"]), d) == []


def test_warmup_은_diff_파일을_쓴다(tmp_path, monkeypatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"language": "py", "nodes": [], "edges": []}')
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "griffe+pycalls"}')
    monkeypatch.setattr(S.declmap, "tracked_files", lambda repo, lang, x: ["a.py"])
    monkeypatch.setattr(S.declmap, "scan", lambda repo, lang, x, n: ({}, None))
    monkeypatch.setattr(S.warmup, "status",
                        lambda cache, repo, files, decls: ({"유효": [], "재읽기": ["a.py"], "위치만": [], "삭제됨": []}, {}))
    out = S.WarmupStage().perform(c)
    assert out.kind == S.P.OK
    got = D.read_diff(str(raw / "warmup-diff.json"))
    assert got is not None and got["targets"] == ["a.py"] and c.targets == ["a.py"]


def test_survey_는_어긋난_계획을_돌리지_않는다(tmp_path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "warmup-diff.json"),
                 {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []}, ["b.py"], 1, 2)
    (raw / "survey-plan.json").write_text(json.dumps(_plan_with(["a.py", "b.py"])))
    out = S.SurveyStage().perform(c)
    assert out.kind == S.P.FAIL and "diff" in out.why
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**

`diff.py` 에:

```python
def plan_files(plan: object) -> set[str]:
    """계획에 든 배치들이 가리키는 파일 집합."""
    out: set[str] = set()
    for layer in M.as_list(M.as_map(plan).get("layers")):
        for batch in M.as_list(M.as_map(layer).get("batches")):
            for f in M.as_list(M.as_map(batch).get("files")):
                if isinstance(f, str):
                    out.add(f)
    return out


def compare_plan(plan: object, d: WarmupDiff) -> list[str]:
    """계획과 diff 가 같은 범위를 말하는지 양방향으로 본다. 불평 목록을 낸다.

    넓으면 전량 지시서에 부분 쪽지가 붙은 것이고, 좁으면 부분 지시서에 전량 쪽지가
    붙은 것이다. 두 번째가 더 위험하다 — 레코드가 조용히 빈다.
    """
    have = plan_files(plan)
    want = set(d["targets"]) if d["targets"] is not None else all_files(d)
    out: list[str] = []
    wider = have - want
    if wider:
        out.append("계획이 diff 보다 넓다 — diff 밖의 파일 %d개: %s" % (len(wider), sorted(wider)[:5]))
    if d["targets"] is None and want - have:
        out.append("계획이 diff 보다 좁다 — 전량인데 빠진 파일 %d개" % len(want - have))
    return out
```

⚠ `targets` 가 있을 때 "좁다" 는 잡지 않는다 — 좁힌 계획은 `targets` 의 **부분집합**일 수 있다(그 파일에 심볼이 없을 수 있다). 전량일 때만 좁음을 본다.

`stages.py` 에:

```python
def lang_for(ctx: Mode1Context) -> str | None:
    """언어. `lang-select.json` 을 먼저, 없으면 코드 지도를 본다."""
    sel = M.as_map(P.read_json(X.LANG_SELECT.locate(ctx)))
    word = M.as_str(sel.get("language"))
    if word:
        return L.LANG_ALIAS.get(word, word)
    cg = X.CODEGRAPH.locate(ctx)
    return L.lang_of(cg if os.path.exists(cg) else None)


def scan_fingerprints(ctx: Mode1Context) -> tuple[warmup.Verdicts, warmup.Manifest, str] | None:
    """지금 소스를 훑어 옛 지문과 대조한다. `(판정, 새 지문, 지문 파일 경로)`. 언어를 모르면 `None`.

    `warmup`(증분)과 `warmup-save`(전량) 둘이 부른다 — 훑는 코드는 한 벌이다.
    """
    lang = lang_for(ctx)
    if lang is None:
        return None
    files = declmap.tracked_files(ctx.repo, lang, [])
    decls, _ = declmap.scan(ctx.repo, lang, [], 0) if files else ({}, None)
    cache = os.path.join(ctx.repo, warmup.DEFAULT_CACHE)
    판정, entries = warmup.status(cache, ctx.repo, files, decls)
    return 판정, entries, cache


class WarmupStage(P.Stage[Mode1Context]):
    """옛 지문과 지금 소스를 대조해 `warmup-diff.json` 을 쓴다. **증분 그래프에만 있다.**"""
    name = "warmup"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.LANG_SELECT]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WARMUP_DIFF]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        diff_path = X.WARMUP_DIFF.locate(ctx)
        scanned = scan_fingerprints(ctx)
        if scanned is None:
            empty: warmup.Verdicts = {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}
            print("알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다.", file=sys.stderr)
            D.write_diff(diff_path, empty, None, ctx.hops, 0)
            ctx.targets = None
            return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
        판정, entries, cache = scanned
        files_n = sum(len(v) for k, v in 판정.items() if k != "삭제됨")
        seed = L.changed_seed(판정)
        cg = X.CODEGRAPH.locate(ctx)
        targets = warmup.blast_radius(cg, seed, ctx.hops) if seed and os.path.exists(cg) else seed
        D.write_diff(diff_path, 판정, targets, ctx.hops, files_n)
        ctx.targets, ctx.entries, ctx.warmup_cache, ctx.tracked_n = targets, entries, cache, files_n
        print("파일 %d개 — 유효 %d · 재읽기 %d · 위치만 %d · 삭제됨 %d"
              % (files_n, len(판정["유효"]), len(판정["재읽기"]), len(판정["위치만"]), len(판정["삭제됨"])))
        return P.Outcome(P.OK, "", [_row(self.name, t0, True)])
```

```python
def _shard_dir(ctx: Mode1Context) -> str:
    return os.path.join(X.raw_dir(ctx), "_shards")


class SurveyStage(P.LlmStage[Mode1Context]):
    """층 오름차순 · 층 안 병렬. 층마다 샤드를 합쳐 디스크에 쓴다.

    층 사이에 이어지는 값(`baseline` · `merged`)은 인스턴스가 아니라 **문맥 칸**에 둔다 —
    단계는 상태를 갖지 않는다.
    """
    name = "survey"
    emits = P.OK | P.FAIL | P.SKIP

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""   # jobs 가 배치마다 만든다. 단일 프롬프트는 쓰이지 않는다

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.SURVEY_PLAN] + ([] if ctx.cold else [X.WARMUP_DIFF])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.READING]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.plan is None:
            raw = P.read_json(X.SURVEY_PLAN.locate(ctx))
            bad = X.check_plan(raw)
            if bad:
                return P.Outcome(P.FAIL, "; ".join(bad), [_row(self.name, t0, False, "; ".join(bad))])
            ctx.plan = cast(survey_plan.SurveyPlan, raw)
            print("층 계획을 디스크에서 읽었다 — %s" % X.SURVEY_PLAN.locate(ctx), flush=True)
        if not ctx.cold:
            d = D.read_diff(X.WARMUP_DIFF.locate(ctx))
            if d is None:
                why = "warmup-diff.json 을 읽지 못했다"
                return P.Outcome(P.FAIL, why, [_row(self.name, t0, False, why)])
            bad = D.compare_plan(ctx.plan, d)
            if bad:
                why = "계획이 diff 와 어긋난다: " + "; ".join(bad)
                return P.Outcome(P.FAIL, why, [_row(self.name, t0, False, why)])
            ctx.targets = d["targets"]
            if d["targets"] is not None and not d["targets"] and os.path.exists(X.READING.locate(ctx)):
                row = _row(self.name, t0, True, "바뀐 파일 0개 — 지난 조사 결과를 그대로 쓴다")
                row["skipped"] = True
                return P.Outcome(P.SKIP, row["why"], [row])
        os.makedirs(_shard_dir(ctx), exist_ok=True)
        ctx.baseline = L.load_records(X.READING.locate(ctx))
        ctx.merged = dict(ctx.baseline)
        return super().perform(ctx)

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.plan["layers"]) if ctx.plan else 0

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        assert ctx.plan is not None
        layer = ctx.plan["layers"][rnd]
        if layer.get("kind") == "non-node":
            jobs = [("NONNODE", R.nonnode_prompt(ctx.repo, ctx.root))]
        else:
            jobs = [(b["id"], R.survey_batch_prompt(ctx.repo, ctx.root, b,
                                                    R.dep_excerpt(ctx.merged, b),
                                                    ctx.targets, ctx.tracked_n))
                    for b in layer["batches"]]
        return [(bid, pr) for bid, pr in jobs
                if not os.path.exists(os.path.join(_shard_dir(ctx), bid + ".json"))]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "survey/" + row["stage"]
        ctx.merged = L.merge_shards(_shard_dir(ctx), ctx.baseline)
        path = X.READING.locate(ctx)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx.merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        ctx.survey_ok = out.kind == P.OK
        return out
```

`layers.py` 에 `load_records(path) -> Records` 를 더한다 — 있으면 읽고 `isinstance(dict)` 로 좁혀 내고, 없으면 `{}`.

- [ ] **Step 4·5: 통과 · 형 검사** — **Step 6: 커밋** — `[feat] : warmup 이 diff 를 쓰고 survey 가 계획과 대조한다`

---

### Task 8: `wiki-catalogue` + `wiki-pages` (D16)

**Files:** Modify `runner/mode1/stages.py` · `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
def test_wiki_catalogue_는_목차_파일을_쓴다고_선언한다(tmp_path):
    c = _ctx(tmp_path)
    assert S.WikiCatalogueStage().writes(c) == [S.X.WIKI_PLAN]
    assert S.WikiPagesStage().reads(c) == [S.X.WIKI_PLAN, S.X.SURVEY_PLAN]


def test_wiki_pages_는_이미_쓴_장을_건너뛴다(tmp_path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "wiki-plan.json").write_text(json.dumps({"pages": [{"file": "a.md", "symbols": []}, {"file": "b.md", "symbols": []}]}))
    (tmp_path / "docs" / "wiki").mkdir(parents=True)
    (tmp_path / "docs" / "wiki" / "a.md").write_text("x")
    c.plan = {"target": 8, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}
    st = S.WikiPagesStage()
    st.prepare(c)
    assert [j[0] for j in st.jobs(c, 0)] == ["b.md"]
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현** — `run_wiki` 를 둘로 가른다:

```python
class WikiCatalogueStage(P.LlmStage[Mode1Context]):
    """목차 한 세션. 이미 있으면 SKIP."""
    name = "wiki-catalogue"
    emits = P.OK | P.FAIL | P.SKIP

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return R.wiki_catalogue_prompt(ctx.repo, ctx.root)

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_PLAN]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if os.path.exists(X.WIKI_PLAN.locate(ctx)):
            row = _row(self.name, t0, True, "목차가 이미 있다")
            row["skipped"] = True
            return P.Outcome(P.SKIP, row["why"], [row])
        return super().perform(ctx)


class WikiPagesStage(P.LlmStage[Mode1Context]):
    """장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛴다."""
    name = "wiki-pages"

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_PLAN, X.SURVEY_PLAN]

    def prepare(self, ctx: Mode1Context) -> None:
        raw = P.read_json(X.WIKI_PLAN.locate(ctx))
        pages = [p for p in M.as_list(M.as_map(raw).get("pages")) if isinstance(M.as_map(p).get("file"), str)]
        ctx.wiki_pages = [cast(L.WikiPage, p) for p in pages]
        assert ctx.plan is not None
        lv = L.page_layers(ctx.wiki_pages, L.symbol_layers(ctx.plan))
        ctx.wiki_levels = sorted(set(lv.values()))
        ctx.wiki_level_of = lv
        ctx.wiki_done = []

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if ctx.plan is None:
            raw = P.read_json(X.SURVEY_PLAN.locate(ctx))
            if X.check_plan(raw):
                return P.Outcome(P.FAIL, "층 계획을 읽지 못했다", [])
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
        return [(pg["file"], R.wiki_page_prompt(ctx.repo, ctx.root, pg, lower)) for pg in here]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "wiki/" + row["stage"]
        return out
```

⚠ `LlmStage.perform` 은 빈 `jobs` 를 그대로 `run_layer` 에 넘기고 `run_layer` 는 빈 목록에 빈 결과를 낸다 — 층에 쓸 장이 없어도 죽지 않는다. `runner/test_run_mode1.py` 의 `test_빈_층은_LLM_Model을_부르지_않는다` 가 그것을 고정한다.

- [ ] **Step 4·5·6** — 커밋 `[feat] : wiki 를 wiki-catalogue 와 wiki-pages 로 쪼갬`

---

### Task 9: 전이표 둘 · 팩토리 · 별명 · `--cold` (D13 · D9)

**Files:** Create `runner/mode1/edges.py` · Modify `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
from mode1 import edges as E  # noqa: E402


def test_증분은_열둘_전량은_열하나():
    assert len(E.ORDER) == 12
    assert E.ORDER.index("warmup") < E.ORDER.index("prep") < E.ORDER.index("survey-plan")
    assert "warmup" not in E.plan_stages(None, None, cold=True)
    assert "warmup" in E.plan_stages(None, None, cold=False)
    assert "warmup-save" in E.plan_stages(None, None, cold=True)


def test_별명은_쪼갠_단계로_펴진다():
    assert E.expand(["lang-select", "build"]) == ["lang-propose", "lang-decide", "build"]
    assert E.expand(["wiki"]) == ["wiki-catalogue", "wiki-pages"]


def test_전량_그래프는_이름이_다르고_표는_같다(tmp_path):
    cold = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    warm = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    assert E.build_mode1_graph(cold, None, None).name == "mode1-cold"
    assert E.build_mode1_graph(warm, None, None).name == "mode1-warm"
    assert E.EDGES.dest("survey", S.P.SKIP) == S.P.NEXT


def test_전량에서는_survey_가_SKIP_을_내지_않는다(tmp_path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "survey-plan.json").write_text(json.dumps(_plan_with([])))
    (tmp_path / "docs" / "codegraph").mkdir(parents=True)
    (tmp_path / "docs" / "codegraph" / "terms-reading.json").write_text("{}")
    out = S.SurveyStage().perform(c)          # 층이 0개라 세션 없이 OK 로 끝난다
    assert out.kind == S.P.OK


def test_증분_그래프는_diff_를_읽는_단계가_셋이다(tmp_path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    g = E.build_mode1_graph(c, only=None, skip=None)
    readers = [n for n in g.order if X.WARMUP_DIFF in g.stages[n].reads(c)]
    assert set(readers) == {"survey-plan", "survey"}   # prep 은 argv 로 받는다


def test_팩토리는_어긋난_그래프를_거부한다(tmp_path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path))
    with pytest.raises(S.P.GraphError):
        E.build_mode1_graph(c, only=["survey"], skip=None)   # 계획도 diff 도 없다
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현** — `runner/mode1/edges.py`:

```python
"""Mode 1 의 흐름 — 단계 순서 · 전이표 둘 · 팩토리. 단계는 자기 다음을 모른다."""
from collections.abc import Iterable

import pipeline as P
from mode1 import context as X
from mode1 import stages as S
from mode1.context import Mode1Context

ORDER = ["lang-propose", "lang-decide", "warmup", "prep", "survey-plan", "survey",
         "warmup-save", "terms", "wiki-catalogue", "wiki-pages", "build", "check"]

# 전량 그래프에는 없는 단계. 대조할 옛 지문이 없는데 대조 단계를 돌리지 않는다.
WARM_ONLY = {"warmup"}

# 옛 명령줄 `--only lang-select` · `--only wiki` 가 그대로 돌게 한다.
ALIASES = {"lang-select": ["lang-propose", "lang-decide"],
           "wiki": ["wiki-catalogue", "wiki-pages"]}

STAGES: dict[str, P.Stage[Mode1Context]] = {
    "lang-propose": S.LangProposeStage(), "lang-decide": S.LangDecideStage(),
    "warmup": S.WarmupStage(), "prep": S.PrepStage(),
    "survey-plan": S.SurveyPlanStage(), "survey": S.SurveyStage(),
    "warmup-save": S.WarmupSaveStage(), "terms": S.TermsStage(),
    "wiki-catalogue": S.WikiCatalogueStage(), "wiki-pages": S.WikiPagesStage(),
    "build": S.BuildStage(), "check": S.CheckStage(),
}

# 전이표는 **하나**다. 전량과 증분의 차이는 단계 목록(`WARM_ONLY`)과 `ctx.cold` 가 만든다 —
# 전량에는 `warmup` 이 없고, `survey` 는 diff 를 읽지 않으며 `SKIP` 을 내지 않는다.
# 갈래 선언(`emits`)은 클래스에 있으므로 두 표가 같아야 시뮬레이터가 통과한다.
EDGES = P.Edges({
    ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT,
    ("lang-propose", P.SKIP): P.NEXT,      # 제안 없이 파일 수로 고른다 (D4 의 폴백)
    ("wiki-catalogue", P.SKIP): P.NEXT,    # 목차가 이미 있다
    ("survey", P.SKIP): P.NEXT,            # 바뀐 파일 0개 — 증분에서만 실제로 난다
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

**두 그래프가 표 하나를 공유하는 이유.** `emits` 는 클래스 선언이라 전량에서도 `SurveyStage` 는 `SKIP` 을 *낼 수 있다고* 선언한다. 표가 둘이면 전량 표에서 완결성 검사가 실패한다. 그래서 표는 하나이고, **전량이 `SKIP` 을 실제로 안 낸다는 것은 단계 시험으로 고정한다**(아래 시험 교체).

- [ ] **Step 4·5·6** — 커밋 `[feat] : mode1 전이표와 팩토리, 증분과 전량 그래프`

설계 메모 ① 은 확정됐다(전량에는 `warmup` 없음). Task 9 끝에 판정 요청은 없다.

---

### Task 10: 재개 JSON (D12)

**Files:** Create `runner/mode1/resume.py` · Modify `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
from mode1 import resume as Z  # noqa: E402


def test_재개_문서는_어디서_왜_멈췄는지를_담는다(tmp_path):
    rows: list[M.StageRow] = [
        {"stage": "prep", "seconds": 1.0, "usage": M.normalize_usage(None), "ok": True, "why": ""},
        {"stage": "survey/L0-B00", "seconds": 2.0, "usage": M.normalize_usage(None), "ok": False, "why": "터짐"},
    ]
    p = str(tmp_path / "resume.json")
    Z.write_resume(p, graph="mode1-warm", rows=rows, order=["prep", "survey", "terms"])
    got = Z.read_resume(p)
    assert got is not None
    assert got["failed_at"] == "survey" and got["done"] == ["prep"] and got["graph"] == "mode1-warm"


def test_다른_그래프의_재개_문서는_거부한다(tmp_path):
    p = str(tmp_path / "r.json")
    Z.write_resume(p, graph="mode1-cold", rows=[], order=["prep"])
    assert Z.start_stage(Z.read_resume(p), for_graph="mode1-warm") is None
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현** — `runner/mode1/resume.py`:

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

`rows` 는 읽을 때 복원하지 않는다 — 측정을 이어 붙이는 것은 화면 표시용이라 이번 범위에서 뺀다. 형에는 남겨 둔다.

- [ ] **Step 4·5·6** — 커밋 `[feat] : 재개 json 쓰기와 읽기`

---

### Task 11: `main` 을 그래프 위로

**Files:** Modify `runner/run_mode1.py`

- [ ] **Step 1: 기준선** — 세 명령의 출력을 파일로 남겨 둔다:

```bash
.venv/bin/python runner/run_mode1.py . --dry-run > /tmp/m1-dry-before.txt 2>&1
.venv/bin/python runner/run_mode1.py . --only prep --dry-run > /tmp/m1-prep-before.txt 2>&1
```

- [ ] **Step 2: `main` 을 다시 쓴다** — `run_mode2.main` 과 같은 모양으로. `run_mode1.py` 의 파사드 재수출 아래에 이 import 를 둔다:

```python
import pipeline as P  # noqa: E402
from mode1 import context as X, diff, resume  # noqa: E402
from mode1.context import Mode1Context  # noqa: E402
from mode1.edges import build_mode1_graph, plan_stages, expand, ORDER as STAGES  # noqa: E402,F401
```

```python
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--target", type=int, default=8)
    ap.add_argument("--hops", type=int, default=1)
    ap.add_argument("--only"); ap.add_argument("--skip")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=float, default=None)
    ap.add_argument("--cold", action="store_true", help="전량. 매니페스트로 좁히지 않는다")
    ap.add_argument("--resume", action="store_true", help="resume.json 이 있으면 멈춘 자리부터")
    a = ap.parse_args(argv)

    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(repo):
        print("에러 — 저장소가 없다: %s" % repo, file=sys.stderr); return 1
    ctx = Mode1Context(root=ROOT, model=a.model, timeout=a.timeout, concurrency=a.concurrency,
                       repo=repo, target=a.target, hops=a.hops, cold=a.cold)
    start = None
    if a.resume:
        start = resume.start_stage(resume.read_resume(X.RESUME.locate(ctx)),
                                   "mode1-cold" if a.cold else "mode1-warm")
        if start is None:
            print("에러 — 이 그래프용 resume.json 이 없다", file=sys.stderr); return 1
    try:
        graph = build_mode1_graph(ctx, only=a.only.split(",") if a.only else None,
                                  skip=a.skip.split(",") if a.skip else None, start_at=start)
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr); return 1

    print("대상 %s" % repo)
    print("LLM Model %s · 흐름 %s · 단계 %s" % (a.model, graph.name, " -> ".join(graph.order)))
    if a.dry_run:
        print(graph.render())
        d = diff.read_diff(X.WARMUP_DIFF.locate(ctx))
        cg = X.CODEGRAPH.locate(ctx)
        if "survey-plan" in graph.order and os.path.exists(cg):
            raw = P.read_json(cg)
            if not X.check_codegraph(raw):
                only = None if a.cold else (d["targets"] if d else None)
                미리 = survey_plan.plan(cast(survey_plan.CodeGraph, raw), a.target, only_files=only)
                print("\n층 계획 (기계가 결정론으로 낸다)%s" % (" — diff 로 좁힘" if only else ""))
                for line in plan_summary(미리):
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

    print("\n" + "=" * 72); print("Mode 1 측정 — 전체 %s" % hms(wall)); print("=" * 72)
    print(format_report(rows, wall_seconds=wall))
    print("\n단계 소계 — 병렬이라 행의 초 합계는 벽시계가 아니다")
    for name, u in stage_totals(rows).items():
        print("  %-12s 토큰 %12s · 턴 %3d · 비용 $%.4f" % (name, "{:,}".format(u["total"]), u["turns"], u["cost_usd"]))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": a.model, "graph": graph.name, "stages": rows,
                       "stage_totals": stage_totals(rows), "concurrency": a.concurrency,
                       "target": a.target, "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": wall}, f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)
    return 0 if all(r["ok"] or r.get("skipped") for r in rows) else 1
```

**세션 수 표시(D13 안전장치)** — `SurveyStage.perform` 의 대조 통과 직후, 첫 세션이 뜨기 전에 한 줄을 찍는다: `"조사 세션 예상 %d개 (층 %d)"`. 확인을 **묻지는 않는다** — 문턱값(N)을 혼자 정하지 않기로 한 규약 때문이다. `--dry-run` 이 같은 수를 미리 보인다.

`run_lang_select` · `run_warmup` · `save_warmup` · `run_survey` · `run_wiki` · `run_machine` · `is_agent_stage` · `should_call_agent` · `STAGES` · `AGENT_STAGES` 는 **지운다**(include 블록과 함께). `runner/test_run_mode1.py` 가 이 이름들을 참조하는 시험이 있으면 **그 시험만 지운다** — 옮긴 것이 아니라 없앤 것이라 파사드로 살릴 수 없다. 지운 시험 이름을 보고에 적는다. 나머지(`plan_stages` 등 옮긴 이름)는 파사드로 살린다: `from mode1.edges import plan_stages, expand, ORDER as STAGES`.

- [ ] **Step 3: 시험** — `.venv/bin/python -m pytest -q` → **562 이상 통과, 실패 0** (지운 시험만큼 줄 수 있다. 지운 것을 보고에 적는다)
- [ ] **Step 4: `--dry-run` 대조** — Step 1 의 두 파일과 새 출력을 비교한다. **단계 이름이 `lang-select`→`lang-propose,lang-decide` · `wiki`→둘로 바뀐 것과 `graph.render()` 가 추가된 것 외에는 같아야 한다.**
- [ ] **Step 5: 형 검사** — `npm run typecheck:py` → `0 errors`
- [ ] **Step 6: 커밋** — `[refactor] : run_mode1 이 단계 기계 위에서 돈다`

---

### Task 12: 게이트 · 문서 · `Any` 게이트 확장 · 인계 문서 표시

**Files:** Modify `test/test_no_any.py` · `runner/README.md`(도구) · `runner/CLAUDE.md` · `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` · `docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md`

- [ ] **Step 1: `Any` 게이트** — `COVERED` 에 `runner/mode1/context.py` · `diff.py` · `prompts.py` · `layers.py` · `stages.py` · `edges.py` · `resume.py` · `runner/run_mode1.py` 를 더한다. 통과해야 한다.
- [ ] **Step 2: 게이트 일곱**

```bash
.venv/bin/python -m pytest -q          # 562 이상 · 실패 0
npm test                               # 8
npm run typecheck && npm run typecheck:py
.venv/bin/python machine/xmldoc.py check ; echo $?    # 1. 문제 수 = 착수 전 + 지운 include 블록 수
.venv/bin/python tools/gen_readme.py machine runner viz tools && .venv/bin/python tools/gen_readme.py --check machine runner viz tools
npm run doctor
```

- [ ] **Step 3: `runner/CLAUDE.md`** — "무엇이 여기 있나" 표의 `run_mode1.py` 행을 12단계 · `mode1/` 패키지로 고친다. `--cold` · `--resume` · `warmup-diff.json` 을 한 줄씩.
- [ ] **Step 4: 스펙에 되돌려 적을 것 셋** — D4 의 폴백이 `FAIL→lang-decide` 가 아니라 `SKIP→NEXT` 로 구현된 것 · 전량 그래프에 `warmup` 이 없고 `warmup-save` 가 직접 훑는다는 것(D13 그림은 그대로) · D2 가 `SurveyStage` 에서 문맥 칸으로 지켜졌다는 것.
- [ ] **Step 5: 인계 문서 배너 갱신** — `HANDOFF-2026-09-07-warmup-increment-unreachable.md` 의 🔴 배너를 "리팩터링 끝. ③④ 착수 가능. 고칠 자리: `runner/mode1/stages.py` 의 `SurveyStage.harvest` 와 `runner/mode1/layers.py` 의 `merge_shards`, `machine/survey_plan.py` 의 배치 id" 로 고친다.
- [ ] **Step 6: 커밋** — `[docs] : mode1 단계 기계 완료를 문서와 게이트에 반영`

---

## 완료 조건

- [ ] `runner/run_mode1.py` 에 `for stage in` 루프가 없다 — `grep -c "for stage in" runner/run_mode1.py` = 0
- [ ] `pytest` 562 이상 통과 · 실패 0 (지운 시험은 보고에 이름이 적혀 있다)
- [ ] `test/test_no_any.py` 가 `mode1/` 전체와 `run_mode1.py` 를 덮고 통과한다
- [ ] `--dry-run` 이 `graph.render()` 로 폴백 간선을 보이고, diff 가 있으면 좁힌 층 계획을 찍는다
- [ ] `warmup-diff.json` 이 실제로 생긴다 — 자기 저장소에 `--only warmup` 으로 확인 (LLM 0)
- [ ] `--only survey` 를 diff 없이 부르면 **팩토리가 거부**한다 (`GraphError`)
- [ ] 낡은 전량 계획 + 좁힌 diff 를 두고 `--only survey` 를 부르면 **`SurveyStage` 가 FAIL** 로 멈춘다 — 인계 문서 재현 ② 가 더는 재현되지 않는다
- [ ] 스펙과 인계 문서가 Task 12 대로 갱신됐다

## 이 계획 뒤

1. **`xmldoc emit` → `inject` 를 한 번** — 1·2·3단계가 옮긴 심볼의 마커를 재주입한다. `docs/decisions/0007` 의 `emit_xml()` 폐지 속성을 이때 함께 넣는다.
2. **결함 ③④** — 인계 문서대로. 그 뒤에 **D17 claim 파일**과 **`삭제됨` 기계 삭제**.
3. **D15 둘째 걸음** — 수집기별 부분 수집 지원을 재고 되는 것부터.
4. 증분 그래프를 실제로 쓰기 시작한다 — 그때까지 "증분이 된다" 고 말하지 않는다.
