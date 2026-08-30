#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='runner/run_mode1.py']"/>
# Mode 1 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 1(코드베이스 위키) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

## 아홉 단계 — LLM 이 도는 칸은 **둘**뿐이다

    prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save ─▶ terms ─▶ wiki ─▶ build ─▶ check
    기계    기계       기계            LLM 층별   기계           기계     LLM 층별  기계     기계

**층을 매기는 것은 기계다.** `survey-plan` 이 자기 칸을 갖는 이유가 그것이다.

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `prep`  | 정적 계층. clang-uml/clang-doc 또는 roslyn-dump 를 돌려 코드 지도를 만든다 | `runner/wiki/prep.mjs` |
| `warmup` | 무엇을 다시 읽어야 하는지 **판정만** 한다. 매니페스트는 쓰지 않는다 | `machine/warmup.py` |
| `survey-plan` | **기계.** 코드 지도를 의존 위상 층과 배치로 나눈다. 모형을 부르지 않는다 | `machine/survey_plan.py` |
| `survey` | 전수조사. 위 계획의 **층 오름차순 · 층 안 병렬**로 배치를 돌린다 | `claude -p` 배치마다 1회 |
| `warmup-save` | **전수조사가** 해낸 뒤에만 매니페스트를 **확정**한다 | `machine/warmup.py` |
| `terms` | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `machine/terms_db.py` |
| `wiki`  | 위키 산문. 목차 1회 + 장마다 1회, 같은 층 순서 | `claude -p` 장마다 1회 |
| `build` | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `runner/wiki/build.mjs` |
| `check` | 산문의 인용을 저장소 실물과 대조한다 | `runner/wiki/check.mjs` |

**층 축은 "의존을 몇 개 갖는가"(out_deg)가 아니라 "얼마나 깊은가"(위상 깊이)다(K1).**
의존 하나만 가진 심볼도 그 하나가 3층이면 4층이다. 같은 층은 서로 의존하지 않으므로
병렬로 읽는다(K2 · K4). 배치는 8심볼(K3), 비노드 용어는 맨 마지막 층(K5), 위키도 같은
층 순서(K6), 고립 노드는 층0(K7)이다.

**확정(`warmup-save`)은 `survey` 바로 뒤다.** 관문이 감싸야 하는 것은 레코드를 만드는
단계다. `wiki` 뒤에 두면 산문 실패가 다음 실행의 전량 재조사를 부른다.

`terms` 가 `survey` 와 `wiki` 사이에 있는 이유 — 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다.

## 모형을 정하는 자리는 하나뿐이다

`main` 의 `--model` 기본값 하나가 `run_survey`/`run_wiki` -> `run_layer` ->
`run_agent_with` -> `claude_argv` 사슬을 그대로 타고 내려간다. **중간에서 모형을 바꾸지
않는다.** 별명이 아니라 정확한 ID 를 쓴다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.

이 파일 자신은 모형이 아니다. 층 순서 · 배치 묶기 · 샤드 병합 · 키 충돌 해소를 전부
결정론으로 하고, 모형을 부르는 자리는 자식 세션뿐이다. 그래서 **이 스크립트를 실행하는
세션의 모형은 여기서 강제되지 않고, `--json` 이 남기는 `model` 칸에도 들어가지 않는다** —
그 칸은 자식 세션의 값이다.

## 재는 자리 넷

  1. **벽시계 시간** — 단계마다 `time.monotonic()` 으로 감싼다. 파이썬이 재므로
     `claude` 가 무엇을 보고하든 상관없이 사람이 기다린 시간 그대로다.
  2. **토큰** — `claude -p --output-format json` 이 내는 `usage` 를 읽는다. 넷으로
     쪼개져 온다(입력 · 출력 · **캐시 읽기** · **캐시 생성**). **캐시 둘을 빼면 실제
     흘러간 양의 일부만 세게 된다.**
  3. **비용** — 같은 JSON 의 `total_cost_usd`.
  4. **턴 수** — `num_turns`. 에이전트가 몇 번 왕복했는지.

## 함정

- **`claude` 는 막혀도 종료 코드 0 을 낼 수 있다.** `is_error` 와 `subtype` 을 봐야 한다
  (`agent_verdict`).
- **`terms_db.py` 에 정적 `codegraph.json` 을 안 주면 투영이 그 파일을 덮어쓴다.**
  노드가 조용히 줄어든다(`terms_argv`).
- **경로를 박지 않는다.** 파이썬은 지금 도는 해석기(`sys.executable`), 나머지는 PATH 다.
  **예외 하나** — `_bootstrap_venv()` 는 `.venv` 밖 해석기로 불렸을 때 `.venv/bin/python3` 로
  재실행한다(파일 맨 위, `import survey_plan` 보다 먼저 — networkx 를 그 import 가 곧장 문다).
  경로 해석은 여기서 끝나고 그 아래 어떤 함수도 `.venv` 를 모른다.

## 쓰는 법

    .venv/bin/python runner/run_mode1.py <저장소> [--model <모형 ID>]
                                            [--only prep,check] [--skip wiki]
                                            [--concurrency 8] [--target 8]
                                            [--json 측정.json] [--dry-run] [--hops 1]

**증분 조사를 끄려면** `--skip warmup,warmup-save` 를 준다.
"""
import os
import sys


def _bootstrap_venv() -> None:
    """`.venv` 밖 해석기로 불렸으면 이 파일 안에서만 `.venv` 로 재실행한다.

    survey_plan.py 가 networkx 를 곧장 import 하므로, 그 import 가 일어나기 전에
    해석기 자체를 바꿔치기해야 한다. 재실행된 프로세스가 그대로 끝까지 돌고 끝나므로
    별도의 "해제" 코드는 없다 — 다른 코드는 여전히 `sys.executable` 만 본다.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_dir = os.path.join(repo_root, ".venv")
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if sys.platform == "win32" \
        else os.path.join(venv_dir, "bin", "python3")
    if not os.path.exists(venv_python):
        return
    # sys.executable 을 realpath 로 비교하면 안 된다 — .venv/bin/python3 는 시스템 파이썬
    # 바이너리로 가는 심볼릭 링크라, realpath 를 풀면 venv 밖의 실제 경로와 같아져 버려서
    # "이미 venv 안" 으로 오판하고 재실행을 건너뛴다. sys.prefix 는 pyvenv.cfg 로 정해지므로
    # 심볼릭 링크를 풀지 않은 채로도 정확히 venv 인지 아닌지를 가른다.
    if os.path.abspath(sys.prefix) == os.path.abspath(venv_dir):
        return
    os.execv(venv_python, [venv_python] + sys.argv)


_bootstrap_venv()

import argparse
import collections
import json
import subprocess
import threading
import time
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any, NotRequired, TypedDict, cast

# 러너는 `runner/`, 결정론 기계는 `machine/` 이다. 이 파일이 CLI 로 돌 때 sys.path[0] 은
# `runner/` 라 machine 을 못 찾는다 — 그래서 여기서 넣는다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine"
    ),
)
import declmap  # noqa: E402
import survey_plan  # noqa: E402
import warmup  # noqa: E402

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# warmup 이 **둘**이다. 앞(warmup)은 판정만 하고, 뒤(warmup-save)가 확정한다 —
# 에이전트가 실패했는데 확정하면 읽지 않은 파일이 '유효' 로 남는다. 확정은 레코드를
# 만드는 `survey` 바로 뒤다(J6).
# `survey-plan` 은 기계다 — 층은 `survey_plan.py` 가 codegraph.json 하나로 결정론으로 낸다.
# 단계는 열 고정이다.
STAGES = ["lang-select", "prep", "warmup", "survey-plan", "survey", "warmup-save",
          "terms", "wiki", "build", "check"]

# 모형을 부르는 단계. survey · wiki 는 **층 오름차순으로 여러 번** 부른다.
# lang-select 는 한 번만, 그리고 가장 싼 모형으로 부른다 — 문서 몇 쪽을 읽고 낱말 하나를 낸다.
AGENT_STAGES = {"lang-select", "survey", "wiki"}

# 언어 판별에 쓸 모형. 문서를 읽고 `cpp|cs|py|ts` 중 하나를 내는 것이 전부라 가장 싼 것을 쓴다.
# `--model` 은 survey·wiki 몫이라 여기에 쓰지 않는다.
LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"

# 코드 지도가 적는 언어 이름과 declmap 이 아는 이름이 한 칸 다르다. 수집기 판별을 여기서
# 다시 하지 않는다 — 판별 규칙이 두 곳에 생기면 조용히 어긋난다.
LANG_ALIAS = {"csharp": "cs", "python": "py"}

# ── 이 파일이 정하는 형 이름은 아래 다섯뿐이다. 코드 지도 · 층 계획 · 매니페스트 · 선언
#    훑기의 꼴은 `machine/` 의 `codegraph_types` · `survey_plan` · `warmup` · `declmap` 이
#    이미 적어 두었으므로 여기서 다시 적지 않는다.

# `claude -p --output-format json` 이 stdout 으로 내는 객체 하나. 꼴을 정하는 것은 바깥
# 프로그램이라 칸을 못 박지 않는다 — 읽는 자리마다 `.get` 으로 없을 수 있음을 받아들인다.
AgentResult = dict[str, Any]

# 잰 값 한 묶음. **정수 여섯에 실수 하나(`cost_usd`)가 섞인 의도된 이종 사전**이다.
# 값 타입을 `float` 으로 적는 것은 파이썬에서 정수가 실수의 부분형이라 둘 다 담기기
# 때문이다. 넣는 값을 실수로 바꾸지 않는다 — `normalize_usage` 는 그대로 정수를 넣는다.
Usage = dict[str, float]

# 전수조사 레코드 하나와 그 묶음. 레코드의 칸은 배치 세션이 채우므로 못 박지 않는다.
Record = dict[str, Any]
Records = dict[str, Record]


class StageRow(TypedDict):
    """측정 표의 한 줄. **세 실행기가 모두 이 꼴로 쌓고 `format_report` 가 읽는다.**

    `skipped` 만 선택 항목이다 — 건너뛴 단계에만 붙는다.
    """

    stage: str
    seconds: float
    usage: Usage
    ok: bool
    why: str
    skipped: NotRequired[bool]


class WikiPage(TypedDict):
    """`wiki-plan.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다."""

    file: str
    title: NotRequired[str]
    symbols: NotRequired[list[str]]


# <include file="machine/comments.xml" path="//term[@id='run_mode1.lang_of']"/>
# 코드 지도가 적어 둔 언어를 선언 훑기가 아는 이름으로 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_warmup
def lang_of(codegraph_path: str | None) -> str | None:
    """코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다.

    모르면 `None` 이다 — 예외가 아니다. 부르는 쪽이 warmup 단계만 건너뛰고 나머지는 그대로 돈다.
    """
    if not codegraph_path:
        return None
    try:
        with open(codegraph_path, encoding="utf-8") as f:
            name = json.load(f).get("language")
    except (OSError, ValueError):
        return None
    name = LANG_ALIAS.get(name, name)
    return name if name in declmap.LANGS else None


# <include file="machine/comments.xml" path="//term[@id='run_mode1.changed_seed']"/>
# 다시 읽어야 할 파일의 씨앗을 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_warmup
def changed_seed(판정: warmup.Verdicts) -> list[str]:
    """다시 읽어야 할 파일의 씨앗. **`재읽기` 와 `위치만` 의 합집합이다.**

    `위치만` 을 반드시 포함한다 — `warmup.decl_hash` 는 선언의 이름만 해싱하므로 본문만
    바뀐 변경도 `위치만` 으로 판정된다. 레코드의 `does` 와 위키 산문의 행동 서술은 본문에
    달려 있어서, 이 갈래를 빼면 그 서술이 조용히 낡는다. `warmup.py` 의 CLI 도 같은 합집합을 쓴다.

    `유효` 는 읽을 것이 없고, `삭제됨` 은 읽을 파일 자체가 없다.
    """
    return sorted(set(판정.get("재읽기") or []) | set(판정.get("위치만") or []))


# <include file="machine/comments.xml" path="//term[@id='run_mode1.should_call_agent']"/>
# 큰 언어 모형을 부를지 말지 정한다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def should_call_agent(targets: Sequence[str] | None, has_reading: bool) -> bool:
    """에이전트를 부를 것인가.

    `targets` 가 `None` 이면 warmup 이 판정을 못 했다는 뜻이다(언어를 모르거나 코드
    지도가 없거나 단계를 건너뛴 경우). 그때는 **전량 조사**로 돈다.

    빈 목록(`[]`)은 "정말로 바뀐 것이 없다" 는 판정이다. 그때만, 그리고 지난 조사
    결과가 있을 때만 건너뛴다.
    """
    if targets is None:
        return True
    if not has_reading:
        return True
    return bool(targets)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.is_agent_stage']"/>
# 이 단계가 큰 언어 모형을 부르는 자리인지 답한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 1. 단계 고르기 ──────────────────────────────────────────────────────
def is_agent_stage(stage: str) -> bool:
    """이 단계가 모형을 부르는가. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="machine/comments.xml" path="//term[@id='run_mode1.plan_stages']"/>
# 일곱 단계 중 무엇을 실제로 돌릴지 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def plan_stages(has_codegraph: bool, has_reading: bool, has_prose: bool,
                only: Iterable[str] | None = None,
                skip: Iterable[str] | None = None) -> list[str]:
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다.

    `prep` 은 늘 남긴다 — 이미 코드 지도가 있으면 건너뛸지를 `runner/wiki/prep.mjs` 가
    스스로 정한다. 여기서 미리 빼면 그 판단을 뺏는 것이다.

    LLM 단계 둘은 **각자 자기 산출물로 걸린다.** `survey` 는 읽기 레코드가 있으면,
    `wiki` 는 산문이 있으면 빠진다. 한쪽만 있으면 그쪽만 건너뛴다.
    """
    for name in list(only or []) + list(skip or []):
        if name not in STAGES:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (name, ", ".join(STAGES)))
    if only:
        return [s for s in STAGES if s in set(only)]
    out: list[str] = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        # warmup 두 칸은 빼지 않는다(warmup 배선의 규칙 그대로).
        if s == "survey" and has_reading:
            continue
        if s == "wiki" and has_prose:
            continue
        out.append(s)
    return out


# <include file="machine/comments.xml" path="//term[@id='run_mode1.normalize_usage']"/>
# 모형이 낸 사용량 보고에서 잴 값만 뽑아 평평하게 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 2. 토큰 세기 ────────────────────────────────────────────────────────
def normalize_usage(result: AgentResult | None) -> Usage:
    """`claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다.

    **정수 여섯과 실수 하나(`cost_usd`)를 한 사전에 담고, `total` 은 입력·출력·캐시읽기·
    캐시생성 넷을 더한 값이다.** 캐시 둘을 빼고 "토큰 합" 이라 부르면 일부만 센 것이다.
    `sum_usage` 가 이 사전을 키별로 접는다.

    기계 단계는 `None` 을 받아 전부 0 을 낸다 — `None` 을 그대로 두면 표를 더할 수 없다.
    """
    # `usage` 는 바깥 프로그램이 채우는 칸이라 값의 꼴을 못 박지 않는다.
    u: dict[str, Any] = (result or {}).get("usage") or {}
    got: Usage = {
        "input": int(u.get("input_tokens") or 0),
        "output": int(u.get("output_tokens") or 0),
        "cache_read": int(u.get("cache_read_input_tokens") or 0),
        "cache_write": int(u.get("cache_creation_input_tokens") or 0),
        "cost_usd": float((result or {}).get("total_cost_usd") or 0.0),
        "turns": int((result or {}).get("num_turns") or 0),
        "api_ms": int((result or {}).get("duration_api_ms") or 0),
    }
    got["total"] = got["input"] + got["output"] + got["cache_read"] + got["cache_write"]
    return got


# <include file="machine/comments.xml" path="//term[@id='run_mode1.sum_usage']"/>
# 단계별 사용량을 하나로 합친다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.format_report, run_mode1.stage_totals
def sum_usage(usages: Sequence[Usage]) -> Usage:
    """`normalize_usage` 가 낸 사전들을 키별로 접는다. 표 맨 아래 '합계' 줄이 이것이다."""
    keys = ["input", "output", "cache_read", "cache_write", "total", "turns", "api_ms"]
    # 정수 여섯은 정수로 접고 `cost_usd` 만 실수로 따로 접는다.
    out: Usage = {k: sum(int(u.get(k) or 0) for u in usages) for k in keys}
    out["cost_usd"] = sum(float(u.get("cost_usd") or 0.0) for u in usages)
    return out


# <include file="machine/comments.xml" path="//term[@id='run_mode1.agent_verdict']"/>
# 큰 언어 모형 단계가 정말 해냈는지 판정한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 3. 실패 판정 ────────────────────────────────────────────────────────
def agent_verdict(returncode: int, result: AgentResult | None) -> tuple[bool, str]:
    """에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다.

    **종료 코드만 믿으면 안 된다.** `claude` 는 최대 턴 수에 걸리거나 권한에 막혀도
    0 을 내면서 `is_error: true` 만 올릴 수 있다.
    """
    if result is None:
        return False, "결과 JSON 을 읽지 못했다 (종료 코드 %d)" % returncode
    if returncode != 0:
        return False, "종료 코드 %d — %s" % (returncode, result.get("subtype") or "사유 없음")
    if result.get("is_error"):
        return False, "에이전트가 오류로 끝났다: %s" % (result.get("subtype") or "사유 없음")
    return True, ""


# <include file="machine/comments.xml" path="//term[@id='run_mode1.claude_argv']"/>
# 헤드리스 모형 호출의 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_agent_with
# ── 4. 에이전트 호출 ────────────────────────────────────────────────────
def claude_argv(model: str, repo: str, extra_dirs: Iterable[str]) -> list[str]:
    """헤드리스 `claude` 명령줄. **프롬프트는 여기 싣지 않는다** — 표준 입력으로 준다.

    `--add-dir` 로 대상 저장소와 도구 저장소를 둘 다 열어 준다. 한쪽만 주면
    에이전트가 재료(facts · codegraph.json)나 규약(스킬 · CLAUDE.md)을 못 본다.
    """
    argv = ["claude", "-p", "--output-format", "json", "--model", model,
            "--permission-mode", "bypassPermissions"]
    for d in [repo] + list(extra_dirs):
        argv += ["--add-dir", d]
    return argv


# <include file="machine/comments.xml" path="//term[@id='run_mode1.warmup_section']"/>
# 다시 읽을 범위를 알리는 지시문을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.survey_batch_prompt
def warmup_section(targets: Sequence[str] | None, total: int, repo: str = "") -> str:
    """프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다.

    ⚠ **이 글은 부르는 쪽이 `.format()` 을 돌린 뒤에 이어 붙는다.** 그래서 중괄호
    자리표시자를 남기면 안 되고, 저장소 경로를 `repo` 로 받아 여기서 박아 넣는다.

    붙는 곳은 **전수조사 배치 프롬프트뿐**이다. 위키 쪽 범위는 `wiki_page_prompt` 가
    페이지 목록으로 따로 준다.
    """
    if not targets:
        return ""
    목록 = "\n".join("  " + t for t in targets)
    return ("\n## 범위 — 증분 조사다. 저장소 전량을 읽지 마라\n"
            "\n"
            "지난 조사 결과가 %s/docs/codegraph/terms-reading.json 에 이미 있다. 그중\n"
            "**아래 %d개 파일에 걸린 레코드만** 다시 만든다. 추적 파일 %d개 중 %d개다.\n"
            "\n%s\n"
            "\n"
            "- **이 목록에 없는 파일은 읽지 마라.** 나머지 레코드는 그대로 살아 있고, 손대면 안 된다.\n"
            "- 목록 밖의 이름이 필요하면 소스가 아니라 **기존 terms-reading.json 과 codegraph.json**\n"
            "  을 근거로 쓴다.\n"
            "- 목록의 파일이 사라졌거나 읽을 수 없으면 **지어내지 말고** 보고에 적는다.\n"
            % (repo, len(targets), total, len(targets), 목록))


# <include file="machine/comments.xml" path="//term[@id='run_mode1.dep_excerpt']"/>
# 이 배치가 의존하는 아래층 레코드만 골라 짧은 글로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_survey
def dep_excerpt(merged: Records, batch: survey_plan.PlanBatch) -> str:
    """배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다.

    아직 레코드가 없는 이름은 아예 뺀다 — 없는 것을 가리키면 세션이 그 자리를 추론으로 메운다.
    """
    want = sorted({d for s in batch.get("symbols", []) for d in s.get("depends_on", [])})
    lines = ["  - %s — %s" % (k, (merged[k] or {}).get("means") or "(뜻 없음)")
             for k in want if k in merged]
    return "\n".join(lines)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.survey_batch_prompt']"/>
# 배치 하나를 맡을 세션에게 줄 글을 만드는 함수.
# 쓰는 것: run_mode1.warmup_section · 쓰이는 곳: run_mode1.run_survey
def survey_batch_prompt(repo: str, root: str, batch: survey_plan.PlanBatch,
                        dep_records: str, targets: Sequence[str] | None = None,
                        total: int = 0) -> str:
    """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

    `dep_records` 는 `dep_excerpt` 가 낸 아래층 발췌다.

    `targets` 는 warmup 이 판정한 다시 읽을 파일 목록이다. 있으면 **증분 조사**라는 뜻이라
    `warmup_section` 이 만든 범위 지시문을 뒤에 붙인다. `None` 이면 전량 조사다.
    """
    syms = "\n".join(
        "  - %s (%s) %s:%s   의존 -> %s"
        % (s["name"], s["kind"], s["file"], s["line"],
           ", ".join(s.get("depends_on") or []) or "없음")
        for s in batch["symbols"])
    return """\
너는 코드베이스 전수조사의 배치 {bid} 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 너보다 아래층은 이미 끝났다 — 다시 조사하지 마라

{deps}

## 네가 맡은 심볼 {n}개 — 이것만 한다

{syms}

## 읽는 법 — 순서를 지킨다

1. 담당 파일마다 통독 캐시를 먼저 본다:
     {root}/.venv/bin/python {root}/machine/file_cache.py get {repo} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 남긴다:
     {root}/.venv/bin/python {root}/machine/file_cache.py put {repo} <파일경로> <개요json>
     개요 꼴 — 심볼마다 {{name, kind, line, end_line, signature, one_line}} 에
     파일의 imports 와 head_comment 를 더한 객체.
2. **네 심볼은 캐시로 때우지 않는다.** 반드시 그 줄 범위를 실제로 읽는다.
   캐시는 남의 심볼을 uses[].to 로 가리킬 때만 쓴다.

## 레코드 계약

{{kind, module, where, means, does, uses[], confidence, source:"reading"}}
- where = `경로:줄` (필수. 기계가 L1 파일 / L2 줄 / L3 근처에 이름 으로 검사한다)
- means = 무엇인가, 한 문장. **객체지향을 갓 배운 대학 1학년 눈높이.** 어려운 용어로 설명하지 않는다
- does  = 무엇을 하는가, 한두 문장
- uses[] = {{to, kind, label, where}}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
- confidence = HIGH(코드를 읽고 썼다) / MEDIUM(일부 읽고 나머지는 추론) / LOW(이름·구조에서 추론)
  **전부 HIGH 로 적으면 그 칸이 장식이 된다.**

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 함수를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "…에 연결될 것 같다"    -> import 나 호출을 실제로 따라간다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 쓰는 곳 — 여기 말고 아무 데도 쓰지 않는다

  {repo}/out/codegraph-raw/_shards/{bid}.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 열지도 고치지도 않는다.** 지금 다른 배치들이 동시에 돌고 있다.
키가 다른 파일과 겹칠 것 같아도 **네가 고치지 않는다** — 층이 끝날 때 일괄 해소된다. 보고에 적기만 한다.
**커밋하지 않는다.**

## 끝내기 전에

- 심볼 {n}개에 레코드가 {n}개 있는가
- where 의 줄 번호를 실제로 열어 확인했는가
- confidence 가 전부 HIGH 는 아닌가
- 샤드 파일 하나만 만들었는가

보고: 레코드 수 · confidence 분포 · 통독한 파일과 캐시로 때운 파일 · 키 충돌 후보 · 읽지 못한 것과 이유.
""".format(repo=repo, root=root, bid=batch["id"], n=len(batch["symbols"]),
           syms=syms, deps=dep_records or "  (없음 — 너는 최하층이다)") \
        + warmup_section(targets, total, repo)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.nonnode_prompt']"/>
# 지도에 없는 용어들을 맡을 마지막 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_survey
def nonnode_prompt(repo: str, root: str) -> str:
    """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

    이것들은 코드 지도의 노드가 아니라 층 축이 없다. 대신 심볼 레코드가 재료다 —
    **심볼 층이 하나라도 남아 있으면 이 세션을 띄우면 안 된다.**
    """
    return """\
너는 코드베이스 전수조사의 **마지막 층** 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 심볼은 이미 전부 끝났다

  {repo}/docs/codegraph/terms-reading.json   앞선 층들이 합쳐 놓은 심볼 레코드

이 파일을 **읽기만** 한다. 고치지 않는다.

## 네가 맡은 것 — 코드 지도의 노드가 아닌 용어 다섯 종류

| kind | 무엇 | where 는 어디 |
|---|---|---|
| `file` | 소스 파일 하나 | `경로:1` |
| `module` | 디렉토리 하나 | 없어도 된다 |
| `artifact` | 이 저장소가 **만들어 내는** 파일 | 그 파일을 **쓰는** 줄 |
| `key` | 설정·JSON 의 이름난 칸 | 그 키를 **채우는** 줄 |
| `concept` | 코드에 글자로 있는 낱말 | 그 낱말이 있는 줄 |

**`file` `module` `artifact` `key` `concept` 는 이름이 그 줄에 글자 그대로 있어야 한다** —
기계가 L3(근처에 그 이름) 으로 검사한다.

`file` 레코드는 **그 파일 안 심볼들의 완성된 means/does 를 재료로** 쓴다. 다시 통독하지 않는다.
`concept` 은 **코드에 글자로 없는 것을 만들지 않는다** — 계획서에만 있는 개념은 여기 싣지 않는다.

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 자리를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 레코드 계약과 쓰는 곳

{{kind, module, where, means, does, uses[], confidence, source:"reading"}} 이고
쓰는 곳은 **여기 하나뿐**이다:

  {repo}/out/codegraph-raw/_shards/NONNODE.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 고치지 않는다. 커밋하지 않는다.**

보고: 종류별 레코드 수 · confidence 분포 · 근거를 못 찾아 뺀 것과 이유.
""".format(repo=repo, root=root)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.symbol_layers']"/>
# 배치 계획에서 심볼마다 몇 층인지만 뽑아 표로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def symbol_layers(plan: survey_plan.SurveyPlan) -> dict[str, int]:
    """`survey-plan.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다."""
    return {s["id"]: L["level"]
            for L in plan.get("layers", [])
            for b in L.get("batches", [])
            for s in b.get("symbols", [])}


# <include file="machine/comments.xml" path="//term[@id='run_mode1.page_layers']"/>
# 위키 페이지마다 몇 번째로 써야 하는지 층을 매기는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def page_layers(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]:
    """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층.

    아는 심볼이 하나도 없으면 층0 이다 — `index.md` 처럼 개괄만 있는 장이 여기 온다.
    `sym_layer` 에 없는 이름은 세지 않으므로, 카탈로그가 지어낸 이름 하나로 페이지가
    맨 뒤로 밀리지 않는다.
    """
    out: dict[str, int] = {}
    for p in pages:
        known = [sym_layer[s] for s in p.get("symbols", []) if s in sym_layer]
        out[p["file"]] = max(known) if known else 0
    return out


# <include file="machine/comments.xml" path="//term[@id='run_mode1.wiki_catalogue_prompt']"/>
# 위키에 어떤 장을 둘지 정하는 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def wiki_catalogue_prompt(repo: str, root: str) -> str:
    """페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다.

    K6 의 층을 매기려면 이 둘이 있어야 하는데, 위키 페이지는 심볼도 모듈도 아닌 **주제**
    단위라 기계가 결정론으로 못 만든다. 그래서 이 한 세션만 먼저 돈다.
    """
    return """\
너는 코드베이스 위키의 **목차 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

**산문을 쓰지 마라.** 이 세션이 낼 것은 목차 파일 하나뿐이다. 각 장은 다음 세션들이 쓴다.

## 재료 — 이미 다 있다. 다시 만들지 마라

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/ranking.json     모듈 중요도(PageRank · hotspot)
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/survey-plan.json 심볼의 의존 층

## 할 일

`/deep-wiki:catalogue` 의 규정을 따라 주제 카탈로그를 짠다 —
Getting Started / Deep Dive 계열, 최대 4단, 절당 자식 8장 이하.
장 수는 모듈 수에 맞춘다. `ranking.json` 상위 모듈부터.

낼 것은 이 파일 하나다:

  {repo}/out/codegraph-raw/wiki-plan.json

  {{"pages": [
    {{"file": "index.md", "title": "이 저장소는 무엇인가", "symbols": []}},
    {{"file": "protocol.md", "title": "프로토콜", "symbols": ["encode", "decode"]}}
  ]}}

- `file` 은 하위 폴더 없는 평평한 이름이다. **`index.md` 를 반드시 넣는다.**
- `symbols` 는 그 장이 **본문에서 다룰** 용어 키다. `terms-db.json` 에 **실제로 있는 키만** 적는다.
  지어낸 이름은 넣지 않는다 — 기계가 이 목록으로 장의 집필 순서를 정한다.
- 개괄만 하는 장은 `symbols` 를 빈 배열로 둔다. 그 장이 맨 먼저 쓰인다.

**마크다운 페이지를 만들지 마라. 커밋하지 마라.**

보고: 장 수 · 장마다 인용 심볼 수 · terms-db 에 없어서 뺀 이름.
""".format(repo=repo, root=root)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.wiki_page_prompt']"/>
# 위키 한 장을 맡을 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def wiki_page_prompt(repo: str, root: str, page: WikiPage, lower_pages: str) -> str:
    """장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다."""
    return """\
너는 코드베이스 위키의 **{fname} 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 네가 쓸 장 하나

  제목   {title}
  파일   {repo}/docs/wiki/{fname}
  다룰 것 {syms}

**이 한 장만 쓴다.** 다른 장을 만들지 않는다.

## 이미 선 장들 — 재설명하지 말고 링크한다

{lower}

## 재료

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/modules.svg      모듈 관계도(큰 그림)

## 규정

`/deep-wiki:page` 의 규정(3단계 절차 · Mermaid · 인용 규격 · 미확인 영역 표기)을 따르되
**사이트 조립은 하지 마라** — 그건 이 도구의 `report-wiki build` 가 한다. 평평한 마크다운만 쓴다.

- **인용은 로컬 규격 `(경로:줄)`** 로 쓴다. 저장소 뿌리 기준 상대 경로다. 기계가 대조한다
- Mermaid 는 소형만(노드 10개 이하). 큰 그림은 `out/codegraph-raw/modules.svg` 를 가리킨다
- 확인 못 한 것은 `(Unknown - verify in <파일>)` 로 남긴다. 지어내지 않는다
- 읽는 사람은 배경 지식이 없다고 가정한다(객체지향을 갓 배운 대학 1학년 눈높이)
- 한국어로 쓰고 영문 기술용어를 병기한다. 약어와 압축 표현을 피한다
- **네가 서브에이전트를 띄운다면 Sonnet 5 계열로 띄운다.** deep-wiki 의 것들은 이미 그렇게 돼 있다

**대상 저장소의 소스는 읽기만 한다. 쓰는 곳은 위 파일 하나뿐이다. 커밋하지 마라.**

보고: 줄 수 · 인용 수 · Mermaid 수 · Unknown 으로 남긴 자리.
""".format(repo=repo, root=root, fname=page["file"], title=page.get("title") or page["file"],
           syms=", ".join(page.get("symbols") or []) or "(개괄 — 특정 심볼 없음)",
           lower=lower_pages or "  (없음 — 네가 첫 장이다)")


# <include file="machine/comments.xml" path="//term[@id='run_mode1.node_argv']"/>
# 위키 기계 단계 하나를 부르는 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 5. 기계 단계의 명령줄 ────────────────────────────────────────────────
def node_argv(root: str, script: str, repo: str) -> list[str]:
    """`runner/wiki/*.mjs` 하나를 부른다. node 는 PATH 에서 찾는다."""
    return ["node", os.path.join(root, "runner", "wiki", script), repo]


# <include file="machine/comments.xml" path="//term[@id='run_mode1.terms_argv']"/>
# 용어 사전을 만드는 단계의 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
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


# <include file="machine/comments.xml" path="//term[@id='run_mode1.hms']"/>
# 초를 사람이 읽는 시간 꼴로 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.format_report
# ── 6. 보고 ─────────────────────────────────────────────────────────────
def hms(seconds: float) -> str:
    """초를 사람이 읽는 꼴로. 재는 것이 목적이라 소수 첫째 자리까지 남긴다."""
    s = float(seconds)
    if s < 60:
        return "%.1f초" % s
    return "%d분 %04.1f초" % (int(s // 60), s % 60)


# <include file="machine/comments.xml" path="//term[@id='run_mode1.format_report']"/>
# 단계별 측정값을 표 한 장으로 만든다.
# 쓰는 것: run_mode1.sum_usage, run_mode1.hms · 쓰이는 곳: run_mode1.main
def format_report(rows: Sequence[StageRow], wall_seconds: float | None = None) -> str:
    """단계별 표 + 합계 줄. 이 실행기의 **산출물 본체**다.

    **`wall_seconds` 를 주면 합계 줄의 시간이 그 값이 되고, 안 주면 행의 초를 더한다.**
    층 안에서 배치가 동시에 돌면 행의 합이 사람이 기다린 시간보다 훨씬 커지므로 병렬로
    도는 쪽이 진짜 벽시계를 재서 넘긴다. Mode 1.5 와 Mode 2 는 병렬이 아니라 안 넘긴다.
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


# <include file="machine/comments.xml" path="//term[@id='run_mode1.plan_summary']"/>
# 층 계획을 사람이 읽는 줄들로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def plan_summary(plan: survey_plan.SurveyPlan) -> list[str]:
    """층·배치 수를 줄 목록으로. `--dry-run` 과 `survey-plan` 단계가 같은 글을 쓴다."""
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


# <include file="machine/comments.xml" path="//term[@id='run_mode1.stage_totals']"/>
# 배치 행들을 단계 단위로 접어 소계를 내는 함수.
# 쓰는 것: run_mode1.sum_usage · 쓰이는 곳: run_mode1.main
def stage_totals(rows: Sequence[StageRow]) -> collections.OrderedDict[str, Usage]:
    """`survey/L0-B00` 같은 행을 `/` 앞까지로 접는다. `{단계: 합친 usage}`."""
    byname: collections.OrderedDict[str, list[Usage]] = collections.OrderedDict()
    for r in rows:
        name = r["stage"].split("/")[0]
        byname.setdefault(name, []).append(r["usage"])
    return collections.OrderedDict((k, sum_usage(v)) for k, v in byname.items())


# <include file="machine/comments.xml" path="//term[@id='run_mode1.Heartbeat']"/>
# 오래 도는 단계 옆에서 경과 시간을 알리는 조각.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 7. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
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


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_agent_with']"/>
# 주어진 글로 모형을 한 번 부르고 걸린 시간과 결과를 함께 내는 함수.
# 쓰는 것: run_mode1.claude_argv · 쓰이는 곳: run_mode1.run_layer
def run_agent_with(model: str, repo: str, root: str, prompt: str,
                   timeout: float | None = None,
                   label: str | None = None) -> tuple[float, int, AgentResult | None]:
    """`claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`.

    **배치별 시간을 여기서 잰다** — 부르는 쪽은 병렬이라 층 전체만 잴 수 있다.

    **하트비트를 여기 두지 않는다.** 동시에 도는 배치가 저마다 찍으면 화면을 못 읽는다 —
    층 하나를 감싸는 하트비트 하나를 `run_layer` 를 부르는 쪽이 건다.
    """
    argv = claude_argv(model=model, repo=repo, extra_dirs=[root])
    t0 = time.monotonic()
    p = subprocess.run(argv, input=prompt, cwd=repo,
                       capture_output=True, text=True, timeout=timeout)
    seconds = time.monotonic() - t0
    try:
        return seconds, p.returncode, json.loads(p.stdout)
    except (ValueError, TypeError):
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print("[%s] %s" % (label or "?", tail), file=sys.stderr)
        return seconds, p.returncode, None


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_layer']"/>
# 한 층의 배치들을 동시에 돌리고 각각의 측정값을 모으는 함수.
# 쓰는 것: run_mode1.run_agent_with · 쓰이는 곳: run_mode1.run_survey, run_mode1.run_wiki
def run_layer(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]],
              concurrency: int = 8,
              timeout: float | None = None) -> list[tuple[str, float, int, AgentResult | None]]:
    """한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다(K2).

    같은 층의 배치는 **같은 파일을 가리키지 않는다**(`survey_plan.pack` 이 보장한다).
    그래서 파일 lock 이 필요 없다. 자식 프로세스를 기다리는 일이라 스레드로 충분하다.

    `jobs` 는 `[(라벨, 프롬프트), …]`. 낸 것은 `[(라벨, 초, 종료코드, 결과 또는 None), …]` 이고
    **라벨 순서로 정렬**해서 낸다 — 끝나는 순서는 실행마다 흔들린다.

    **한 배치가 터져도 층을 버리지 않는다.** 터진 배치는 종료 코드 -1 · 결과 None 인
    행으로 남고, 부르는 쪽이 실패로 센다.
    """
    if not jobs:
        return []
    rows: list[tuple[str, float, int, AgentResult | None]] = []
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


# <include file="machine/comments.xml" path="//term[@id='run_mode1.merge_shards']"/>
# 배치들이 따로 쓴 조각을 하나로 합치고 이름 충돌을 푸는 함수.
# 쓰는 것: run_mode1._qualified · 쓰이는 곳: run_mode1.run_survey
def merge_shards(shard_dir: str, existing: Records | None) -> Records:
    """샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.**

    배치 세션은 자기 배치만 보므로 전역을 보는 것은 이 함수뿐이다 — 겹치면 겹친 **전원**을
    `<파일줄기>.<이름>` 으로 고친다. 한쪽만 한정하면 나중에 또 겹친다.

    **망가진 샤드는 건너뛴다.** 배치 하나가 반쯤 쓰고 죽어도 나머지 결과를 버리지 않는다.
    무엇을 건너뛰었는지는 stderr 에 적는다.

    ⚠ **`existing` 에는 누적본이 아니라 조사 이전의 원본을 준다.** 이 함수는 층마다 불리고
    그때마다 샤드 전부를 다시 읽는다. 누적본을 넘기면 이미 합쳐 둔 레코드를 **자기 자신과의
    충돌**로 보고 개명해 레코드 수가 줄어든다. 샤드가 원본이고 이 함수는 그 순수 함수다.

    충돌 판정에 `!=` 를 쓰는 것도 같은 이유다. `is not` 은 같은 샤드를 다시 읽은 새 객체를
    남으로 본다.
    """
    got = dict(existing or {})
    if not os.path.isdir(shard_dir):
        return got
    for fname in sorted(os.listdir(shard_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(shard_dir, fname), encoding="utf-8") as f:
                shard: Records = json.load(f)
        except (ValueError, OSError) as ex:
            print("샤드를 건너뛴다 — %s: %s" % (fname, ex), file=sys.stderr)
            continue
        for key, rec in shard.items():
            if key in got and got[key] != rec:
                # 겹친 전원을 개명한다. 이미 들어와 있던 쪽도 함께 고친다.
                old = got.pop(key)
                got[_qualified(key, old)] = old
                got[_qualified(key, rec)] = rec
            else:
                got[key] = rec
    return got


# <include file="machine/comments.xml" path="//term[@id='run_mode1._qualified']"/>
# 겹친 이름 앞에 파일 줄기를 붙여 서로 구별되게 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.merge_shards
def _qualified(key: str, rec: Record | None) -> str:
    """`<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다."""
    where = (rec or {}).get("where") or ""
    stem = os.path.splitext(os.path.basename(where.split(":")[0]))[0]
    return "%s.%s" % (stem, key) if stem else key


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_machine']"/>
# 기계 단계 하나를 부른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def run_machine(argv: Sequence[str], label: str) -> int:
    """기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다."""
    with Heartbeat(label, every=60.0):
        p = subprocess.run(argv)
    return p.returncode


# 어떤 정적 수집기를 돌릴지 정한다. 모형의 제안을 결정론 검사로 거른다.
# 쓰는 것: claude_argv, lang_select · 쓰이는 곳: run_mode1.main
def run_lang_select(repo: str, root: str, timeout: float | None) -> tuple[bool, str, Usage]:
    """루트 문서를 모형에게 읽히고 언어 하나를 받아 `lang-select.json` 을 쓴다.

    **모형은 제안만 한다.** 채택 여부는 `machine/lang_select.py` 가 결정론으로 판정한다 —
    제안한 언어의 소스가 한 개도 없으면 버리고 파일 수가 가장 많은 언어로 간다.

    모형을 못 부르거나 문서가 없으면 제안 없이 파일 수만으로 고른다. **막지 않는다** —
    이 단계는 뒤 단계를 돕는 것이지 관문이 아니다.
    """
    raw = os.path.join(repo, "out", "codegraph-raw")
    os.makedirs(raw, exist_ok=True)
    out = os.path.join(raw, "lang-select.json")
    tool = os.path.join(root, "machine", "lang_select.py")

    docs = subprocess.run([sys.executable, tool, repo, "--print-docs"],
                          capture_output=True, text=True).stdout
    proposed: str | None = None
    usage: Usage = normalize_usage(None)
    if docs.strip():
        prompt = (
            "아래는 한 저장소의 최상위 문서다. 이 저장소에 **정적 분석기를 돌려 코드 지도를 만들려 한다.**\n"
            "어느 언어를 대상으로 삼아야 가장 쓸모 있는 지도가 나오겠는지 판단해라.\n\n"
            "고를 수 있는 것과 그 수집기:\n"
            "  cpp -> clang-uml    cs -> roslyn-dump    py -> griffe+pycalls    ts -> (수집기 없음)\n\n"
            "문서가 어떤 언어를 많이 이야기하는지가 아니라, **분석해서 얻을 것이 있는 코드**가\n"
            "어느 언어인지를 본다. 넷 중 하나를 **낱말 하나로만** 답해라. 설명하지 마라.\n"
            "판단이 안 서면 `unknown` 이라고 답해라.\n\n" + docs)
        try:
            r = subprocess.run(claude_argv(model=LANG_SELECT_MODEL, repo=repo, extra_dirs=[root]),
                               input=prompt, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0:
                got = json.loads(r.stdout)
                usage = normalize_usage(got)
                word = str(got.get("result", "")).strip().strip("`.").lower()
                if word in ("cpp", "cs", "py", "ts"):
                    proposed = word
        except (OSError, ValueError, subprocess.SubprocessError):
            proposed = None

    argv = [sys.executable, tool, repo, "-o", out]
    if proposed:
        argv += ["--propose", proposed]
    r2 = subprocess.run(argv, capture_output=True, text=True)
    sys.stdout.write(r2.stdout)
    if r2.returncode != 0:
        return False, (r2.stdout + r2.stderr).strip().splitlines()[-1][:120], usage
    return True, f"제안 {proposed or '없음'}", usage


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_warmup']"/>
# 무엇을 다시 읽어야 하는지 판정하는 앞 관문.
# 쓰는 것: run_mode1.lang_of, run_mode1.changed_seed · 쓰이는 곳: run_mode1.main
def run_warmup(repo: str, codegraph: str, hops: int) -> tuple[
        list[str] | None, warmup.Manifest | None, str | None, int, bool, str]:
    """관문 ① — 무엇을 다시 읽어야 하는지 판정한다. **매니페스트를 쓰지는 않는다.**

    쓰기를 여기서 하면 에이전트가 실패했을 때도 "유효" 로 기록되어, 다음 실행이
    읽지 않은 파일을 읽은 것으로 친다. 갱신은 `save_warmup` 이 따로 한다.

    판정할 수 없으면 `targets` 를 `None` 으로 낸다 — 실패가 아니다. 그러면
    `should_call_agent` 가 전량 조사로 돌아간다.

    반환 (targets, entries, cache_path, 추적파일수, 성공인가, 사유)
    """
    lang = lang_of(codegraph if os.path.exists(codegraph) else None)
    if lang is None:
        print("알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다.", file=sys.stderr)
        return None, None, None, 0, True, ""

    cache = os.path.join(repo, warmup.DEFAULT_CACHE)
    files = declmap.tracked_files(repo, lang, [])
    if not files:
        print("알림 — git 이 아는 %s 소스가 0개다. 전량 조사로 돈다." % lang, file=sys.stderr)
        return None, None, None, 0, True, ""

    decls, _ = declmap.scan(repo, lang, [], 0)
    판정, entries = warmup.status(cache, repo, files, decls)
    seed = changed_seed(판정)

    # 파급까지 넓힌다. 코드 지도가 없으면 씨앗 그대로다 — 파급은 안전망이지 필수가 아니다.
    if seed and os.path.exists(codegraph):
        targets = warmup.blast_radius(codegraph, seed, hops)
    else:
        targets = seed

    print("%s 파일 %d개 — 유효 %d · 재읽기 %d · 위치만 %d · 삭제됨 %d"
          % (lang, len(files), len(판정["유효"]), len(판정["재읽기"]),
             len(판정["위치만"]), len(판정["삭제됨"])))
    print("에이전트가 읽을 것 %d개 (%.1f%%) — 씨앗 %d개에서 %d홉 퍼뜨린 결과"
          % (len(targets), len(targets) / len(files) * 100, len(seed), hops))
    for p in targets[:15]:
        print("  " + p)
    if len(targets) > 15:
        print("  … 그 밖 %d개" % (len(targets) - 15))
    if 판정["삭제됨"]:
        print("사람이 볼 것 — 삭제된 파일 %d개의 레코드를 지울지 정해야 한다:"
              % len(판정["삭제됨"]), file=sys.stderr)
        for p in 판정["삭제됨"][:10]:
            print("  " + p, file=sys.stderr)
    return targets, entries, cache, len(files), True, ""


# <include file="machine/comments.xml" path="//term[@id='run_mode1.save_warmup']"/>
# 판정 기록을 확정하는 뒤 관문.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def save_warmup(cache_path: str | None, entries: warmup.Manifest | None,
                rows: Sequence[StageRow]) -> tuple[bool, str]:
    """관문 ② — **전수조사가 실제로 해낸 뒤에만** 매니페스트를 갱신한다.

    앞칸이 판정을 못 했거나(`entries is None`) 전수조사가 실패했으면 **쓰지 않는다.**
    쓰지 않는 쪽이 안전하다 — 다음 실행이 전량을 다시 읽을 뿐 틀리지는 않는다.

    ⚠ **행 라벨에서 `/` 앞의 단계 이름만 떼어 본다.** 라벨은 `survey/L0-B00` 꼴이라
    `r["stage"] == "survey"` 로 비교하면 영원히 거짓이 되어 관문이 fail-open 이 된다.
    """
    if entries is None or not cache_path:
        return True, ""
    실패한_조사 = [r for r in rows
                   if r["stage"].split("/")[0] == "survey" and not r.get("ok")]
    if 실패한_조사:
        print("매니페스트를 갱신하지 않는다 — 전수조사가 실패했다. "
              "지금 갱신하면 읽지 않은 파일이 '유효' 로 남는다.", file=sys.stderr)
        return True, ""
    warmup.save(cache_path, entries)
    print("매니페스트 갱신 — %s (%d개 파일)" % (cache_path, len(entries)))
    return True, ""


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_survey']"/>
# 전수조사를 층 오름차순으로 돌리고 층마다 샤드를 합치는 함수.
# 쓰는 것: run_mode1.run_layer, run_mode1.merge_shards, run_mode1.survey_batch_prompt, run_mode1.nonnode_prompt, run_mode1.dep_excerpt · 쓰이는 곳: run_mode1.main
def run_survey(model: str, repo: str, root: str, plan: survey_plan.SurveyPlan,
               concurrency: int, timeout: float | None, reading_path: str,
               targets: Sequence[str] | None = None, total: int = 0) -> list[StageRow]:
    """층 사이는 순차, 층 안은 병렬(K2). `[행, …]` 을 낸다.

    **층이 끝날 때마다 병합해서 디스크에 쓴다.** 다음 층의 배치가 아래층 레코드를 발췌해
    받아야 하고, 중간에 죽어도 거기까지는 남아야 한다.

    **샤드가 이미 있는 배치는 건너뛴다(J4).** `--only survey` 로 다시 돌리면 실패한
    배치만 다시 돈다.
    """
    shard_dir = os.path.join(repo, "out", "codegraph-raw", "_shards")
    os.makedirs(shard_dir, exist_ok=True)
    # **조사 이전의 원본**을 따로 붙들어 둔다. 층마다 `merge_shards` 에 이것을 준다 —
    # 누적본을 주면 이미 합친 레코드를 자기 자신과의 충돌로 보고 개명한다.
    baseline: Records = {}
    if os.path.exists(reading_path):
        with open(reading_path, encoding="utf-8") as f:
            baseline = json.load(f)
    merged = dict(baseline)

    rows: list[StageRow] = []
    for L in plan["layers"]:
        if L.get("kind") == "non-node":
            jobs: list[tuple[str, str]] = [("NONNODE", nonnode_prompt(repo, root))]
            label_of: dict[str, str] = {"NONNODE": "survey/L%d-비노드" % L["level"]}
        else:
            jobs, label_of = [], {}
            for b in L["batches"]:
                jobs.append((b["id"], survey_batch_prompt(
                    repo, root, b, dep_excerpt(merged, b), targets, total)))
                label_of[b["id"]] = "survey/" + b["id"]
        jobs = [(bid, pr) for bid, pr in jobs
                if not os.path.exists(os.path.join(shard_dir, bid + ".json"))]
        if not jobs:
            print("  층%d — 샤드가 이미 다 있다. 건너뛴다." % L["level"], flush=True)
            continue

        print("  층%d — 배치 %d개를 동시 %d 로 돌린다"
              % (L["level"], len(jobs), concurrency), flush=True)
        with Heartbeat("survey 층%d" % L["level"]):
            got = run_layer(model, repo, root, jobs, concurrency, timeout)
        for bid, seconds, rc, result in got:
            ok, why = agent_verdict(rc, result)
            rows.append({"stage": label_of[bid], "seconds": seconds,
                         "usage": normalize_usage(result), "ok": ok, "why": why})

        merged = merge_shards(shard_dir, baseline)
        os.makedirs(os.path.dirname(reading_path), exist_ok=True)
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("  층%d 끝 — 레코드 %d개" % (L["level"], len(merged)), flush=True)
        if not all(r["ok"] for r in rows):
            print("층%d 에 실패한 배치가 있다. 다음 층으로 가지 않는다 — "
                  "아래층이 비면 위층이 추론으로 메운다." % L["level"], file=sys.stderr)
            break
    return rows


# <include file="machine/comments.xml" path="//term[@id='run_mode1.run_wiki']"/>
# 위키 목차를 받고 장들을 층 오름차순으로 쓰게 하는 함수.
# 쓰는 것: run_mode1.run_layer, run_mode1.wiki_catalogue_prompt, run_mode1.wiki_page_prompt, run_mode1.page_layers, run_mode1.symbol_layers · 쓰이는 곳: run_mode1.main
def run_wiki(model: str, repo: str, root: str, plan: survey_plan.SurveyPlan,
             concurrency: int, timeout: float | None) -> list[StageRow]:
    """카탈로그 한 세션(J3) -> 장들을 층 오름차순 병렬(K6)."""
    raw = os.path.join(repo, "out", "codegraph-raw")
    wiki_plan_path = os.path.join(raw, "wiki-plan.json")
    rows: list[StageRow] = []

    if not os.path.exists(wiki_plan_path):
        with Heartbeat("wiki 목차"):
            got = run_layer(model, repo, root,
                            [("catalogue", wiki_catalogue_prompt(repo, root))], 1, timeout)
        _, seconds, rc, result = got[0]
        ok, why = agent_verdict(rc, result)
        rows.append({"stage": "wiki/목차", "seconds": seconds,
                     "usage": normalize_usage(result), "ok": ok, "why": why})
        if not ok:
            return rows
    if not os.path.exists(wiki_plan_path):
        rows.append({"stage": "wiki/목차", "seconds": 0.0, "usage": normalize_usage(None),
                     "ok": False, "why": "wiki-plan.json 이 나오지 않았다"})
        return rows

    with open(wiki_plan_path, encoding="utf-8") as f:
        pages: list[WikiPage] = json.load(f)["pages"]
    lv = page_layers(pages, symbol_layers(plan))
    done: list[WikiPage] = []
    for k in sorted(set(lv.values())):
        here = [pg for pg in pages if lv[pg["file"]] == k
                and not os.path.exists(os.path.join(repo, "docs", "wiki", pg["file"]))]
        if not here:
            continue
        lower = "\n".join("  - %s — %s" % (pg["file"], pg.get("title") or pg["file"])
                          for pg in done)
        jobs = [(pg["file"], wiki_page_prompt(repo, root, pg, lower)) for pg in here]
        print("  층%d — 장 %d개를 동시 %d 로 쓴다" % (k, len(jobs), concurrency), flush=True)
        with Heartbeat("wiki 층%d" % k):
            got = run_layer(model, repo, root, jobs, concurrency, timeout)
        for fname, seconds, rc, result in got:
            ok, why = agent_verdict(rc, result)
            rows.append({"stage": "wiki/" + fname, "seconds": seconds,
                         "usage": normalize_usage(result), "ok": ok, "why": why})
        done += here
        if not all(r["ok"] for r in rows):
            print("층%d 에 실패한 장이 있다. 다음 층으로 가지 않는다." % k, file=sys.stderr)
            break
    return rows


# <include file="machine/comments.xml" path="//term[@id='run_mode1.main']"/>
# 명령줄을 읽고 단계를 차례로 돌린 뒤 측정 표를 낸다.
# 쓰는 것: run_mode1.plan_stages, run_mode1.terms_argv, run_mode1.format_report, run_mode1.run_warmup, run_mode1.save_warmup (+4) · 쓰이는 곳: 없음
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    # 별명이 아니라 정확한 ID 를 적는다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.
    # 이 값이 main -> run_survey/run_wiki -> run_layer -> run_agent_with -> claude_argv
    # 사슬을 그대로 타고 내려간다. **중간에서 모형을 바꾸지 않는다.**
    ap.add_argument("--model", default="claude-sonnet-5",
                    help="배치·장 세션이 쓸 모형 (기본: claude-sonnet-5)")
    ap.add_argument("--concurrency", type=int, default=8,
                    help="한 층에서 동시에 띄울 세션 수 (기본 8 = K4)")
    ap.add_argument("--target", type=int, default=8,
                    help="배치당 목표 심볼 수 (기본 8 = K3)")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
    ap.add_argument("--hops", type=int, default=1,
                    help="바뀐 파일에서 파급을 몇 홉 퍼뜨릴지 (기본: 1). "
                         "🔵 2026-08-30 QtVisionEdit 실측 — 1홉 평균 1.5파일, 2홉 2.1파일로 "
                         "차이가 거의 없다")
    a = ap.parse_args(argv)

    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(repo):
        print("에러 — 저장소가 없다: %s" % repo, file=sys.stderr)
        return 1

    raw = os.path.join(repo, "out", "codegraph-raw")
    codegraph = os.path.join(raw, "codegraph.json")
    reading = os.path.join(repo, "docs", "codegraph", "terms-reading.json")
    wiki = os.path.join(repo, "docs", "wiki")
    has_prose = os.path.isdir(wiki) and any(f.endswith(".md") for f in os.listdir(wiki))

    try:
        stages = plan_stages(
            has_codegraph=os.path.exists(codegraph),
            has_reading=os.path.exists(reading),
            has_prose=has_prose,
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None)
    except ValueError as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    print("대상 %s" % repo)
    print("모형 %s · 단계 %s" % (a.model, " -> ".join(stages) or "(없음)"))
    print("이미 있는 것 — 코드지도 %s · 읽기레코드 %s · 산문 %s"
          % (os.path.exists(codegraph), os.path.exists(reading), has_prose))
    if a.dry_run:
        # 층 계산은 결정론이라 지금 해도 같다.
        if "survey-plan" in stages and os.path.exists(codegraph):
            with open(codegraph, encoding="utf-8") as f:
                미리 = survey_plan.plan(json.load(f), a.target)
            print("\n층 계획 (기계가 결정론으로 낸다 — 모형을 부르지 않는다)")
            for lines in plan_summary(미리):
                print(lines)
        return 0

    # warmup 이 앞칸에서 담아 두고 뒤칸이 꺼내 쓴다. 같은 프로세스 안이라 파일로 넘길 이유가 없다.
    #   targets  에이전트가 읽을 파일 목록. None 이면 판정을 못 했다는 뜻이다(= 전량 조사)
    #   entries  갱신될 매니페스트. 에이전트가 성공한 뒤에만 쓴다
    targets: list[str] | None = None
    entries: warmup.Manifest | None = None
    warmup_cache: str | None = None
    tracked_n = 0
    survey_plan_path = os.path.join(raw, "survey-plan.json")
    plan_json: survey_plan.SurveyPlan | None = None
    rows: list[StageRow] = []
    t_all = time.monotonic()
    for stage in stages:
        print("\n── %s ──────────────────────────────" % stage, flush=True)
        t0 = time.monotonic()
        if stage == "warmup":
            targets, entries, warmup_cache, tracked_n, ok, why = run_warmup(repo, codegraph, a.hops)
            rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                         "usage": normalize_usage(None), "ok": ok, "why": why})
        elif stage == "warmup-save":
            ok, why = save_warmup(warmup_cache, entries, rows)
            rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                         "usage": normalize_usage(None), "ok": ok, "why": why})
        elif stage == "lang-select":
            ok, why, usage = run_lang_select(repo, ROOT, a.timeout)
            rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                         "usage": usage, "ok": ok, "why": why})
        elif stage == "survey-plan":
            # **기계 단계다. 모형을 부르지 않는다.** 층은 codegraph.json 하나로 결정론이고,
            # 의존을 몇 개 갖는지(out_deg)가 아니라 **위상 깊이**로 매긴다(K1).
            if not os.path.exists(codegraph):
                ok, why = False, "코드 지도가 없다 — prep 이 먼저다: %s" % codegraph
            else:
                with open(codegraph, encoding="utf-8") as f:
                    # warmup 이 판정한 목록이 있으면 그 파일의 심볼만 남긴다(증분 조사).
                    # 층 번호는 **전체 그래프 기준으로 매긴 뒤** 걸러진다 —
                    # 거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다.
                    plan_json = survey_plan.plan(json.load(f), a.target, only_files=targets)
                with open(survey_plan_path, "w", encoding="utf-8") as f:
                    json.dump(plan_json, f, ensure_ascii=False, indent=1)
                print("%s%s" % (survey_plan_path,
                                " (증분: warmup 이 준 %d파일)" % len(targets) if targets else ""))
                for lines in plan_summary(plan_json):
                    print(lines)
                ok, why = True, ""
            rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                         "usage": normalize_usage(None), "ok": ok, "why": why})
        elif stage in AGENT_STAGES:
            if stage == "survey" and not should_call_agent(targets, os.path.exists(reading)):
                rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                             "usage": normalize_usage(None), "ok": True, "skipped": True,
                             "why": "바뀐 파일 0개 — 지난 조사 결과를 그대로 쓴다"})
                print("%s — 건너뜀 (바뀐 파일 0개)" % stage, flush=True)
                continue
            if plan_json is None:
                # `--only survey` 처럼 앞칸을 건너뛰고 불렀을 때다. 디스크에 있으면 그것을 쓴다.
                if not os.path.exists(survey_plan_path):
                    print("에러 — 층 계획이 없다: %s (survey-plan 이 먼저다)" % survey_plan_path,
                          file=sys.stderr)
                    return 1
                with open(survey_plan_path, encoding="utf-8") as f:
                    # 디스크에서 읽은 것이라 기계가 꼴을 확인할 수 없다. `survey-plan` 칸이
                    # `survey_plan.plan` 의 결과를 그대로 쓴 파일이라 꼴은 같다.
                    plan_json = cast(survey_plan.SurveyPlan, json.load(f))
                print("층 계획을 디스크에서 읽었다 — %s" % survey_plan_path, flush=True)
            if stage == "survey":
                got = run_survey(a.model, repo, ROOT, plan_json, a.concurrency,
                                 a.timeout, reading, targets, tracked_n)
            else:
                got = run_wiki(a.model, repo, ROOT, plan_json, a.concurrency, a.timeout)
            rows += got
            ok = bool(got) and all(r["ok"] for r in got)
            print("%s — %s (%s · 세션 %d개)"
                  % (stage, "성공" if ok else "실패", hms(time.monotonic() - t0), len(got)),
                  flush=True)
        else:
            if stage == "terms":
                # 없는 파일은 넘기지 않는다 — terms_argv 는 순수 함수라 존재를 모른다
                cmd = terms_argv(sys.executable, ROOT, repo,
                                 codegraph if os.path.exists(codegraph) else None,
                                 reading if os.path.exists(reading) else None)
            else:
                cmd = node_argv(ROOT, stage + ".mjs", repo)
            rc = run_machine(cmd, stage)
            ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
            seconds = time.monotonic() - t0
            rows.append({"stage": stage, "seconds": seconds, "usage": normalize_usage(None),
                         "ok": ok, "why": why})
            print("%s — %s (%s)" % (stage, "성공" if ok else "실패", hms(seconds)), flush=True)
        if not all(r["ok"] for r in rows):
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

    wall = time.monotonic() - t_all
    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % hms(wall))
    print("=" * 72)
    print(format_report(rows, wall_seconds=wall))
    print("\n단계 소계 — 병렬이라 행의 초 합계는 벽시계가 아니다")
    for name, u in stage_totals(rows).items():
        print("  %-12s 토큰 %12s · 턴 %3d · 비용 $%.4f"
              % (name, "{:,}".format(u["total"]), u["turns"], u["cost_usd"]))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": a.model, "stages": rows,
                       "stage_totals": stage_totals(rows),
                       "concurrency": a.concurrency, "target": a.target,
                       "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": wall},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
