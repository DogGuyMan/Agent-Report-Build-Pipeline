#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_mode1.py']"/>
# Mode 1 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 1(코드베이스 위키) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

## 열 단계 — LLM 이 도는 칸은 **셋**이다

    lang-select ─▶ prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save ─▶ terms ─▶ wiki ─▶ build ─▶ check
    LLM 1회        기계     기계       기계            LLM 층별   기계           기계     LLM 층별  기계     기계

**층을 매기는 것은 기계다.** `survey-plan` 이 자기 칸을 갖는 이유가 그것이다.

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `lang-select` | 어떤 정적 수집기를 돌릴지 고른다. Model의 제안을 결정론 검사로 거른다 | `claude -p` 1회(가장 싼 Model) |
| `prep`  | 정적 계층. clang-uml/clang-doc 또는 roslyn-dump 를 돌려 코드 지도를 만든다 | `runner/wiki/prep.py` |
| `warmup` | 무엇을 다시 읽어야 하는지 **판정만** 한다. 매니페스트는 쓰지 않는다 | `machine/warmup.py` |
| `survey-plan` | **기계.** 코드 지도를 의존 위상 층과 배치로 나눈다. Model을 부르지 않는다 | `machine/survey_plan.py` |
| `survey` | 전수조사. 위 계획의 **층 오름차순 · 층 안 병렬**로 배치를 돌린다 | `claude -p` 배치마다 1회 |
| `warmup-save` | **전수조사가** 해낸 뒤에만 매니페스트를 **확정**한다 | `machine/warmup.py` |
| `terms` | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `machine/terms_db.py` |
| `wiki`  | 위키 산문. 목차 1회 + 장마다 1회, 같은 층 순서 | `claude -p` 장마다 1회 |
| `build` | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `runner/wiki/build.py` |
| `check` | 산문의 인용을 저장소 실물과 대조한다 | `runner/wiki/check.py` |

**층 축은 "의존을 몇 개 갖는가"(out_deg)가 아니라 "얼마나 깊은가"(위상 깊이)다(K1).**
의존 하나만 가진 심볼도 그 하나가 3층이면 4층이다. 같은 층은 서로 의존하지 않으므로
병렬로 읽는다(K2 · K4). 배치는 8심볼(K3), 비노드 용어는 맨 마지막 층(K5), 위키도 같은
층 순서(K6), 고립 노드는 층0(K7)이다.

**확정(`warmup-save`)은 `survey` 바로 뒤다.** 관문이 감싸야 하는 것은 레코드를 만드는
단계다. `wiki` 뒤에 두면 산문 실패가 다음 실행의 전량 재조사를 부른다.

`terms` 가 `survey` 와 `wiki` 사이에 있는 이유 — 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다.

## Model을 정하는 자리는 하나뿐이다

`main` 의 `--model` 기본값 하나가 `run_survey`/`run_wiki` -> `run_layer` ->
`run_agent_with` -> `claude_argv` 사슬을 그대로 타고 내려간다. **중간에서 Model을 바꾸지
않는다.** 별명이 아니라 정확한 ID 를 쓴다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.

이 파일 자신은 Model이 아니다. 층 순서 · 배치 묶기 · 샤드 병합 · 키 충돌 해소를 전부
결정론으로 하고, Model을 부르는 자리는 자식 세션뿐이다. 그래서 **이 스크립트를 실행하는
세션의 Model은 여기서 강제되지 않고, `--json` 이 남기는 `model` 칸에도 들어가지 않는다** —
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

    .venv/bin/python runner/run_mode1.py <저장소> [--model <Model ID>]
                                            [--only prep,check] [--skip wiki]
                                            [--concurrency 8] [--target 8]
                                            [--json 측정.json] [--dry-run] [--hops 1]

**증분 조사를 끄려면** `--skip warmup,warmup-save` 를 준다.
"""
import os
import sys


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1._bootstrap_venv']"/>
# 이 스크립트를 돌리는 파이썬이 .venv 안의 것인지 확인하고, 아니면 .venv 파이썬으로 바꿔서 다시 실행하는 함수다.
# 쓰는 것: os, sys · 쓰이는 곳: 없음
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
import json
import subprocess
import time
from collections.abc import Iterable, Sequence
from typing import cast

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

# 재는 코드의 원본은 `runner/measure.py` 하나다. 여기에 사본이 없다.
# 옛 이름으로 부르는 곳이 있어 그대로 다시 내보낸다.
import pipeline as P  # noqa: E402
from measure import (  # noqa: E402,F401
    AgentResult as AgentResult, Usage as Usage, StageRow as StageRow,
    Heartbeat as Heartbeat,
    normalize_usage, sum_usage, agent_verdict, claude_argv,
    hms, format_report, stage_totals,
)

# 형 · 자리 · 단계 바닥의 원본은 `mode1/` 패키지다. 옛 이름으로 부르는 시험이 있어 그대로 다시 내보낸다.
from mode1.context import (  # noqa: E402,F401
    Record as Record, Records as Records, WikiPage as WikiPage, reading_path,
)
from mode1.machine_stage import Mode1Machine  # noqa: E402
from mode1.graph import ScheduleBatchesStage  # noqa: E402
from mode1.terms import VerifyTermsStage  # noqa: E402
wiki_argv = Mode1Machine.wiki_argv
plan_summary = ScheduleBatchesStage.plan_summary
terms_argv = VerifyTermsStage.terms_argv
from mode1.scan import SnapshotScan, DetectChangesStage  # noqa: E402
LANG_ALIAS = SnapshotScan.LANG_ALIAS
lang_of = SnapshotScan.lang_of
changed_seed = DetectChangesStage.changed_seed
from mode1.survey import AnnotateSymbolsStage  # noqa: E402
warmup_section = AnnotateSymbolsStage.warmup_section
dep_excerpt = AnnotateSymbolsStage.dep_excerpt
survey_batch_prompt = AnnotateSymbolsStage.survey_batch_prompt
nonnode_prompt = AnnotateSymbolsStage.nonnode_prompt
merge_shards = AnnotateSymbolsStage.merge_shards
_qualified = AnnotateSymbolsStage.qualified
from mode1.wiki import OutlineWikiStage, WriteWikiStage  # noqa: E402
wiki_catalogue_prompt = OutlineWikiStage.wiki_catalogue_prompt
symbol_layers = WriteWikiStage.symbol_layers
page_layers = WriteWikiStage.page_layers
wiki_page_prompt = WriteWikiStage.wiki_page_prompt

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# warmup 이 **둘**이다. 앞(warmup)은 판정만 하고, 뒤(warmup-save)가 확정한다 —
# 에이전트가 실패했는데 확정하면 읽지 않은 파일이 '유효' 로 남는다. 확정은 레코드를
# 만드는 `survey` 바로 뒤다(J6).
# `survey-plan` 은 기계다 — 층은 `survey_plan.py` 가 codegraph.json 하나로 결정론으로 낸다.
# 단계는 열 고정이다.
STAGES = ["lang-select", "prep", "warmup", "survey-plan", "survey", "warmup-save",
          "terms", "wiki", "build", "check"]

# Model을 부르는 단계. survey · wiki 는 **층 오름차순으로 여러 번** 부른다.
# lang-select 는 한 번만, 그리고 가장 싼 Model으로 부른다 — 문서 몇 쪽을 읽고 낱말 하나를 낸다.
AGENT_STAGES = {"lang-select", "survey", "wiki"}

# 언어 판별에 쓸 Model. 문서를 읽고 `cpp|cs|py|ts` 중 하나를 내는 것이 전부라 가장 싼 것을 쓴다.
# `--model` 은 survey·wiki 몫이라 여기에 쓰지 않는다.
LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"

# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.should_call_agent']"/>
# 전수조사 단계에서 큰 언어 Model(에이전트)을 실제로 부를지 말지를 정하는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.test_run_mode1.test_agent_is_skipped_when_nothing_changed_and_records_exist, runner.test_run_mode1.test_agent_runs_when_something_changed, runner.test_run_mode1.test_agent_runs_when_warmup_could_not_judge, runner.test_run_mode1.test_agent_still_runs_when_there_are_no_records_yet
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.is_agent_stage']"/>
# 주어진 단계 이름이 Model(LLM)을 부르는 단계인지 검사하는 함수다.
# 쓰는 것: runner.run_mode1.AGENT_STAGES · 쓰이는 곳: runner.test_run_mode1.test_세_단계가_Model을_부른다, runner.test_run_mode1.test_층_계획은_LLM_단계가_아니다
# ── 1. 단계 고르기 ──────────────────────────────────────────────────────
def is_agent_stage(stage: str) -> bool:
    """이 단계가 Model을 부르는가. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.plan_stages']"/>
# 열 단계 중 이번 실행에서 실제로 돌릴 단계 목록을 정하는 함수다.
# 쓰는 것: runner.run_mode1.STAGES · 쓰이는 곳: runner.run_mode1.main, runner.test_run_mode1.test_plan_keeps_prep_even_when_codegraph_exists, runner.test_run_mode1.test_plan_only_and_skip_are_honoured, runner.test_run_mode1.test_plan_rejects_an_unknown_stage, runner.test_run_mode1.test_skip_은_열_단계_흐름_기준으로_걸러낸다 (+7)
def plan_stages(has_codegraph: bool, has_reading: bool, has_prose: bool,
                only: Iterable[str] | None = None,
                skip: Iterable[str] | None = None) -> list[str]:
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다.

    `prep` 은 늘 남긴다 — 이미 코드 지도가 있으면 건너뛸지를 `runner/wiki/prep.py` 가
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


# 팬아웃 호출의 원본은 `pipeline.py` 하나뿐이다. 여기에는 사본이 없다 —
# 시험 넷이 옛 이름을 참조하므로 이름 그대로 재수출한다.
run_agent_with = P.run_agent_with
run_layer = P.run_layer


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.run_machine']"/>
# 기계(파이썬·노드) 단계 하나를 자식 프로세스로 실행하는 함수다.
# 쓰는 것: runner.run_mode1.Heartbeat · 쓰이는 곳: runner.run_mode1.main, runner.run_mode1_5.main, runner.run_mode2.main
def run_machine(argv: Sequence[str], label: str) -> int:
    """기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다."""
    with Heartbeat(label, every=60.0):
        p = subprocess.run(argv)
    return p.returncode


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.run_lang_select']"/>
# 저장소가 어느 언어인지 판별하기 위해 Model에게 문서를 읽혀 언어 하나를 제안받는 함수다.
# 쓰는 것: runner.run_mode1.claude_argv, runner.run_mode1.normalize_usage · 쓰이는 곳: runner.run_mode1.main
# 어떤 정적 수집기를 돌릴지 정한다. Model의 제안을 결정론 검사로 거른다.
# 쓰는 것: claude_argv, lang_select · 쓰이는 곳: run_mode1.main
def run_lang_select(repo: str, root: str, timeout: float | None) -> tuple[bool, str, Usage]:
    """루트 문서를 Model에게 읽히고 언어 하나를 받아 `lang-select.json` 을 쓴다.

    **Model은 제안만 한다.** 채택 여부는 `machine/lang_select.py` 가 결정론으로 판정한다 —
    제안한 언어의 소스가 한 개도 없으면 버리고 파일 수가 가장 많은 언어로 간다.

    Model을 못 부르거나 문서가 없으면 제안 없이 파일 수만으로 고른다. **막지 않는다** —
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.run_warmup']"/>
# 전수조사 전에 '어느 파일을 다시 읽어야 하는지' 만 미리 판정하는 함수다. 아직 아무것도 저장하지는 않는다.
# 쓰는 것: runner.run_mode1.lang_of, machine.declmap.tracked_files, machine.declmap.scan, machine.warmup.status, runner.run_mode1.changed_seed (+1) · 쓰이는 곳: runner.run_mode1.main
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.save_warmup']"/>
# 전수조사가 실제로 끝난 뒤에만 "무엇을 다시 읽었는지" 기록(매니페스트)을 확정해서 저장하는 함수다.
# 쓰는 것: machine.warmup.save · 쓰이는 곳: runner.run_mode1.main, runner.test_run_mode1.test_survey_가_실패하면_매니페스트를_갱신하지_않는다, runner.test_run_mode1.test_판정을_못_했으면_아무것도_쓰지_않는다
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.run_survey']"/>
# 전수조사(코드베이스 용어 레코드 작성)를 층 낮은 것부터 순서대로 돌리고, 층이 끝날 때마다 결과를 합쳐 파일에 저장하는 함수다.
# 쓰는 것: runner.run_mode1.nonnode_prompt, runner.run_mode1.survey_batch_prompt, runner.run_mode1.dep_excerpt, runner.run_mode1.Heartbeat, runner.run_mode1.run_layer (+3) · 쓰이는 곳: runner.run_mode1.main
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.run_wiki']"/>
# 위키 문서의 목차를 먼저 받고, 그 목차를 바탕으로 장(챕터)들을 의존 층 순서대로 병렬로 쓰게 만드는 함수다.
# 쓰는 것: runner.run_mode1.run_layer, runner.run_mode1.wiki_catalogue_prompt, runner.run_mode1.wiki_page_prompt, runner.run_mode1.page_layers, runner.run_mode1.symbol_layers (+1) · 쓰이는 곳: runner.run_mode1.main
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.main']"/>
# Mode 1(코드베이스 위키) 파이프라인 전체를 순서대로 돌리는 진입점 함수. 명령줄 인자를 읽고 어떤 단계를 돌릴지 정한 뒤 하나씩 실행하며 시간과 토큰을 잰다.
# 쓰는 것: runner.run_mode1.plan_stages, runner.run_mode1.run_warmup, runner.run_mode1.save_warmup, runner.run_mode1.run_lang_select, runner.run_mode1.run_survey (+8) · 쓰이는 곳: 없음
def main(argv: Sequence[str] | None = None) -> int:
    # 
    ap = argparse.ArgumentParser(
        description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    # 별명이 아니라 정확한 ID 를 적는다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.
    # 이 값이 main -> run_survey/run_wiki -> run_layer -> run_agent_with -> claude_argv
    # 사슬을 그대로 타고 내려간다. **중간에서 Model을 바꾸지 않는다.**
    ap.add_argument("--model", default="claude-sonnet-5",
                    help="배치·장 세션이 쓸 Model (기본: claude-sonnet-5)")
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
    reading = reading_path(repo, ROOT)
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
    print("Model %s · 단계 %s" % (a.model, " -> ".join(stages) or "(없음)"))
    print("이미 있는 것 — 코드지도 %s · 읽기레코드 %s · 산문 %s"
          % (os.path.exists(codegraph), os.path.exists(reading), has_prose))
    if a.dry_run:
        # 층 계산은 결정론이라 지금 해도 같다.
        if "survey-plan" in stages and os.path.exists(codegraph):
            with open(codegraph, encoding="utf-8") as f:
                미리 = survey_plan.plan(json.load(f), a.target)
            print("\n층 계획 (기계가 결정론으로 낸다 — Model을 부르지 않는다)")
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
            # **기계 단계다. Model을 부르지 않는다.** 층은 codegraph.json 하나로 결정론이고,
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
                cmd = wiki_argv(sys.executable, ROOT, stage + ".py", repo)
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
