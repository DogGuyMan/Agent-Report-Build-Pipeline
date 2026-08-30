#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/run_mode1.py']"/>
# Mode 1 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""run_mode1.py — Mode 1(코드베이스 위키) 파이프라인을 한 번에 돌리고 **재는** 실행기.

**왜 이것이 있는가.** Mode 1 은 기계 단계(정적 수집 · 투영 · 사이트 빌드 · 인용 검증)와
사람 자리(LLM 이 코드를 읽고 쓰는 곳)가 번갈아 나온다. 손으로 돌리면 명령을 여섯 번
치는 동안 **어디에서 시간이 갔고 토큰이 얼마나 흘렀는지가 남지 않는다.** 이 파일의
목적은 파이프라인을 자동화하는 것이 아니라 **단계마다 벽시계 시간과 토큰을 붙들어
표로 내는 것**이다. 자동화는 그것을 재기 위한 수단이다.

## 아홉 단계 — LLM 이 도는 칸은 **둘**뿐이다

    prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save ─▶ terms ─▶ wiki ─▶ build ─▶ check
    기계    기계       기계            LLM 층별   기계           기계     LLM 층별  기계     기계

**층을 매기는 것은 기계다.** `survey-plan` 이 자기 칸을 갖는 이유가 그것이다 —
한 칸에 묶어 두면 "의존 위상 층 오름차순" 이 모형의 판단처럼 읽힌다.

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `prep`  | 정적 계층. clang-uml/clang-doc 또는 roslyn-dump 를 돌려 코드 지도를 만든다 | `scripts/wiki/prep.mjs` |
| `warmup` | 무엇을 다시 읽어야 하는지 **판정만** 한다. 매니페스트는 쓰지 않는다 | `codegraph/warmup.py` |
| `survey-plan` | **기계.** 코드 지도를 의존 위상 층과 배치로 나눈다. 모형을 부르지 않는다 | `codegraph/survey_plan.py` |
| `survey` | 전수조사. 위 계획의 **층 오름차순 · 층 안 병렬**로 배치를 돌린다 | `claude -p` 배치마다 1회 |
| `warmup-save` | **전수조사가** 해낸 뒤에만 매니페스트를 **확정**한다 | `codegraph/warmup.py` |
| `terms` | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `codegraph/terms_db.py` |
| `wiki`  | 위키 산문. 목차 1회 + 장마다 1회, 같은 층 순서 | `claude -p` 장마다 1회 |
| `build` | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `scripts/wiki/build.mjs` |
| `check` | 산문의 인용을 저장소 실물과 대조한다 | `scripts/wiki/check.mjs` |

**⚠ 이 파일의 이전 판은 "에이전트를 하나로 묶은 것이 이 설계의 급소다" 라고 적었다.**
이유는 캐시였다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어 토큰이 부풀고,
측정값이 파이프라인 비용이 아니라 세션 수의 함수가 된다.

**2026-08-30 사용자가 그 결정을 뒤집었다.** 심볼의 뜻은 그것이 의존하는 심볼의 뜻 위에 서므로
아무 순서로나 읽으면 아직 안 읽은 것을 가리키게 되고 그 자리가 추론으로 메워진다.
그래서 **의존 대상이 없는 것부터** 한 겹씩 올라가고(K1), 같은 층은 서로 의존하지 않으므로
병렬로 읽는다(K2 · K4).

⚠ **축은 "의존을 몇 개 갖는가"(out_deg)가 아니라 "얼마나 깊은가"(위상 깊이)다.** 의존
하나만 가진 심볼도 그 하나가 3층이면 4층이다. 🔵 2026-08-30 이 저장소 실측 — out_deg 1
무리(31개) 안에 위상 깊이 1·2·3·4 가 전부 섞여 있었고, out_deg 2 무리(15개)도 같았다.
out_deg 로 정렬하면 아직 안 읽은 것을 가리키게 된다. 배치는 8심볼(K3), 비노드 용어는 맨 마지막 층(K5),
위키도 같은 층 순서(K6), 고립 노드는 층0(K7)이다.

**비용은 아직 재지 않았다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 훨씬 적다.
어느 쪽이 큰지는 **모른다.** 이 파일 자신이 재는 도구이므로 A/B 를 돌려 숫자로 답한다.
그 전에는 "더 싸졌다" "더 빨라졌다" 를 쓰지 않는다. 게다가 기준선은 **opus 한 세션**이고
지금은 **claude-sonnet-5 여러 세션**이라 변수가 둘이다 — 무엇 덕분인지 귀속할 수 없다.

**확정(`warmup-save`)이 `survey` 바로 뒤인 것이 중요하다.** 관문이 감싸야 하는 것은
레코드를 만드는 단계다. `wiki` 뒤에 두면 산문 실패가 다음 실행의 전량 재조사를 부른다.

`terms` 가 `survey` 와 `wiki` 사이에 있는 이유 — 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다. 예전에는 산문이 검사 전 레코드를 봤다.

## 모형은 두 계층이다 — 이 파일이 정하는 것은 아래 하나뿐이다

| 계층 | 누구 | 무슨 모형 | 이 파일이 정하나 |
|---|---|---|---|
| 위 — **오케스트레이터** | 이 스크립트를 실행하는 Claude Code 세션 | **opus** (사람이 그 세션에서 고른다) | **아니다.** 이 파일 밖이다 |
| 아래 — **서브에이전트** | 이 파일이 `claude -p` 로 띄우는 배치·장 세션 | **`claude-sonnet-5`** | **그렇다.** `--model` 기본값 |

**이 파일 자신은 모형이 아니다.** 파이썬 프로세스이고, 층 순서 · 배치 묶기 · 샤드 병합 ·
키 충돌 해소를 전부 결정론으로 한다. 모형을 부르는 자리는 자식 세션뿐이다.

그러므로 **위 계층은 여기서 강제할 수 없다.** `opus` 로 돌든 무엇으로 돌든 이 스크립트는
똑같이 동작한다. 위 표의 `opus` 는 **규약이지 검사되는 값이 아니다** — 어긴다고 아무것도
막히지 않으니, 측정값을 비교할 때 오케스트레이터가 무엇이었는지 사람이 따로 기록해야 한다.

**아래 계층은 여기서 강제된다.** `main` 의 `--model` 기본값 하나가
`run_survey`/`run_wiki` -> `run_layer` -> `run_agent_with` -> `claude_argv` 사슬을 그대로
타고 내려간다. **중간에서 모형을 바꾸지 않는다.** 별명(`sonnet`)이 아니라 정확한 ID 를
쓰는 이유도 여기 있다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.

⚠ **`--json` 이 남기는 `model` 칸은 아래 계층의 값이다.** 위 계층은 거기 안 들어간다.

## 재는 자리 넷

  1. **벽시계 시간** — 단계마다 `time.monotonic()` 으로 감싼다. 파이썬이 재므로
     `claude` 가 무엇을 보고하든 상관없이 사람이 기다린 시간 그대로다.
  2. **토큰** — `claude -p --output-format json` 이 내는 `usage` 를 읽는다. 넷으로
     쪼개져 온다(입력 · 출력 · **캐시 읽기** · **캐시 생성**). 캐시 둘을 빼면 실제
     흘러간 양의 일부만 세게 된다 — 실측상 캐시가 전체의 99% 를 넘는 일이 흔하다.
  3. **비용** — 같은 JSON 의 `total_cost_usd`.
  4. **턴 수** — `num_turns`. 에이전트가 몇 번 왕복했는지.

## 함정

- **`claude` 는 막혀도 종료 코드 0 을 낼 수 있다.** `is_error` 와 `subtype` 을 봐야 한다
  (`agent_verdict`).
- **`terms_db.py` 에 정적 `codegraph.json` 을 안 주면 투영이 그 파일을 덮어쓴다.**
  노드가 조용히 줄어든다 — 이 저장소 자신에서 실제로 겪었다(`terms_argv`).
- **경로를 박지 않는다.** 파이썬은 지금 도는 해석기(`sys.executable`), 나머지는 PATH 다.

## 쓰는 법

    .venv/bin/python codegraph/run_mode1.py <저장소> [--model claude-sonnet-5]
                                            [--only prep,check] [--skip wiki]
                                            [--concurrency 8] [--target 8]
                                            [--json 측정.json] [--dry-run] [--hops 1]

**증분 조사를 끄려면** `--skip warmup,warmup-save` 를 준다. **다섯 단계 시절의 대조군은
이 옵션으로 만들 수 없다** — 그건 `git worktree add /tmp/rb-old 9223143` 으로 옛 커밋을
통째로 떼어 돌린다.
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# warmup 과 declmap 은 같은 폴더에 있다. 이 파일이 CLI 로 돌 때는 sys.path[0] 이 그 폴더이고,
# 시험이 import 할 때는 시험 파일이 넣어 준다. 어느 쪽이든 확실하도록 여기서도 넣는다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402
import survey_plan  # noqa: E402
import warmup  # noqa: E402

# 이 파일은 <ROOT>/codegraph/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# warmup 이 **둘**인 것이 이 흐름의 급소다. 앞(warmup)은 판정만 하고, 뒤(warmup-save)가
# 확정한다 — 에이전트가 실패했는데 확정하면 읽지 않은 파일이 '유효' 로 남는다.
# 확정은 **레코드를 만드는 `survey` 바로 뒤**다. `wiki` 뒤에 두면 산문 실패가
# 다음 실행의 전량 재조사를 부른다(J6).
# `survey-plan` 은 **기계**다. 층 오름차순이 LLM 의 판단처럼 보이지 않도록 자기 칸을 준다 —
# 층은 `survey_plan.py` 가 codegraph.json 하나로 결정론으로 낸다(모형을 부르지 않는다).
# 단계는 아홉 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["prep", "warmup", "survey-plan", "survey", "warmup-save",
          "terms", "wiki", "build", "check"]

# 모형을 부르는 단계. **둘 다 층 오름차순으로 여러 번** 부른다 — 예전의 한 번이 아니다.
AGENT_STAGES = {"survey", "wiki"}

# 코드 지도가 적는 언어 이름과 declmap 이 아는 이름이 한 칸 다르다. 두 줄짜리 표다 —
# 수집기 판별을 여기서 다시 하지 않는다. 그러면 판별 규칙이 두 곳에 생겨 조용히 어긋난다.
LANG_ALIAS = {"csharp": "cs"}


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.lang_of']"/>
# 코드 지도가 적어 둔 언어를 선언 훑기가 아는 이름으로 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_warmup
def lang_of(codegraph_path):
    """코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다.

    모르면 `None` 이다 — 예외가 아니다. 부르는 쪽이 warmup 단계만 건너뛰고
    나머지는 그대로 돈다. 새 언어가 들어와도 파이프라인이 죽지 않아야 한다.
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.changed_seed']"/>
# 다시 읽어야 할 파일의 씨앗을 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_warmup
def changed_seed(판정):
    """다시 읽어야 할 파일의 씨앗. **`위치만` 을 반드시 포함한다.**

    `warmup.py` 의 문서는 `위치만` 을 "주석만 고치거나 줄만 밀린 변경" 이라 부르지만,
    구현은 그것과 **본문 재작성**을 구별하지 못한다 — `decl_hash` 가 선언의 이름만
    해싱하기 때문이다(`codegraph/warmup.py` 의 `decl_hash`). 🔵 2026-08-30 실측으로
    `return x + 1` → `return x + 100` 이 `위치만` 으로 판정되는 것을 확인했다.

    레코드의 `does`(동작)와 위키 산문의 행동 서술은 본문에 달려 있으므로 이 갈래를
    빼면 그 서술이 조용히 낡는다. `warmup.py` 의 CLI 도 같은 합집합을 쓴다.

    `유효` 는 읽을 것이 없고, `삭제됨` 은 읽을 파일 자체가 없다.
    """
    return sorted(set(판정.get("재읽기") or []) | set(판정.get("위치만") or []))


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.should_call_agent']"/>
# 큰 언어 모형을 부를지 말지 정한다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def should_call_agent(targets, has_reading):
    """에이전트를 부를 것인가.

    `targets` 가 `None` 이면 warmup 이 판정을 못 했다는 뜻이다(언어를 모르거나 코드
    지도가 없거나 단계를 건너뛴 경우). 그때는 **옛 동작인 전량 조사**로 돌아간다 —
    모르는 상태에서 건너뛰면 조용히 아무 일도 안 하게 된다.

    빈 목록(`[]`)은 "정말로 바뀐 것이 없다" 는 판정이다. 그때만, 그리고 지난 조사
    결과가 있을 때만 건너뛴다.
    """
    if targets is None:
        return True
    if not has_reading:
        return True
    return bool(targets)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.is_agent_stage']"/>
# 이 단계가 큰 언어 모형을 부르는 자리인지 답한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 1. 단계 고르기 ──────────────────────────────────────────────────────
def is_agent_stage(stage):
    """이 단계가 모형을 부르는가. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.plan_stages']"/>
# 일곱 단계 중 무엇을 실제로 돌릴지 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def plan_stages(has_codegraph, has_reading, has_prose, only=None, skip=None):
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 시험이 쉽다.

    `prep` 은 늘 남긴다 — 이미 코드 지도가 있으면 건너뛸지를 `prepPlan` 자신이 정한다
    (`scripts/wiki/prep.mjs` 의 `hasCodegraph`). 여기서 미리 빼면 그 판단을 뺏는 것이다.

    LLM 단계 둘은 **각자 자기 산출물로 걸린다.** `survey` 는 읽기 레코드가 있으면,
    `wiki` 는 산문이 있으면 빠진다. 한쪽만 있으면 그쪽만 건너뛴다.
    """
    for name in list(only or []) + list(skip or []):
        if name not in STAGES:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (name, ", ".join(STAGES)))
    if only:
        return [s for s in STAGES if s in set(only)]
    out = []
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.normalize_usage']"/>
# 모형이 낸 사용량 보고에서 잴 값만 뽑아 평평하게 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 2. 토큰 세기 ────────────────────────────────────────────────────────
def normalize_usage(result):
    """`claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다.

    **캐시 둘을 반드시 더한다.** `usage` 는 넷으로 쪼개져 오는데 캐시 읽기와 캐시 생성이
    보통 전체의 대부분이다. 그 둘을 빼고 "토큰 합" 이라 부르면 한 자릿수 백분율만 센 것이다.

    기계 단계는 `None` 을 받아 전부 0 을 낸다 — `None` 을 그대로 두면 표를 더할 수 없다.
    """
    u = (result or {}).get("usage") or {}
    got = {
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.sum_usage']"/>
# 단계별 사용량을 하나로 합친다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.format_report, run_mode1.stage_totals
def sum_usage(usages):
    """단계별 사용량을 하나로 합친다. 표 맨 아래 '합계' 줄이 이것이다."""
    keys = ["input", "output", "cache_read", "cache_write", "total", "turns", "api_ms"]
    out = {k: sum(int(u.get(k) or 0) for u in usages) for k in keys}
    out["cost_usd"] = sum(float(u.get("cost_usd") or 0.0) for u in usages)
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.agent_verdict']"/>
# 큰 언어 모형 단계가 정말 해냈는지 판정한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 3. 실패 판정 ────────────────────────────────────────────────────────
def agent_verdict(returncode, result):
    """에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다.

    **종료 코드만 믿으면 안 된다.** `claude` 는 최대 턴 수에 걸리거나 권한에 막혀도
    0 을 내면서 `is_error: true` 만 올릴 수 있다. 그걸 성공으로 세면 다음 단계가
    빈 재료를 읽고 엉뚱한 곳에서 죽는다.
    """
    if result is None:
        return False, "결과 JSON 을 읽지 못했다 (종료 코드 %d)" % returncode
    if returncode != 0:
        return False, "종료 코드 %d — %s" % (returncode, result.get("subtype") or "사유 없음")
    if result.get("is_error"):
        return False, "에이전트가 오류로 끝났다: %s" % (result.get("subtype") or "사유 없음")
    return True, ""


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.claude_argv']"/>
# 헤드리스 모형 호출의 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_agent_with
# ── 4. 에이전트 호출 ────────────────────────────────────────────────────
def claude_argv(model, repo, extra_dirs):
    """헤드리스 `claude` 명령줄. **프롬프트는 여기 싣지 않는다** — 표준 입력으로 준다.

    `--add-dir` 로 대상 저장소와 도구 저장소를 둘 다 열어 준다. 한쪽만 주면
    에이전트가 재료(facts · codegraph.json)나 규약(스킬 · CLAUDE.md)을 못 본다.
    """
    argv = ["claude", "-p", "--output-format", "json", "--model", model,
            "--permission-mode", "bypassPermissions"]
    for d in [repo] + list(extra_dirs):
        argv += ["--add-dir", d]
    return argv


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.warmup_section']"/>
# 다시 읽을 범위를 알리는 지시문을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.survey_batch_prompt
def warmup_section(targets, total, repo=""):
    """프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다.

    **목록만 주면 부족하다.** 에이전트는 맥락이 모자라다고 느끼면 옆 파일을 더 읽는다.
    그것이 이 배선이 줄이려는 바로 그 비용이므로, 목록 밖을 읽지 말라고 분명히 쓴다.
    대신 이미 있는 레코드를 근거로 쓰라고 알려 준다 — 금지만 하면 막힌다.

    이 글은 부르는 쪽이 이미 `.format()` 을 돌린 **뒤에** 이어 붙는다. 그래서
    중괄호 자리표시자를 남기면 안 되고, 저장소 경로를 `repo` 로 받아 여기서 박아 넣는다.

    ⚠ 2026-08-30 — 산문 범위를 말하던 줄을 뺐다. 이 글은 이제 **전수조사 배치 프롬프트**에만
    붙는데, 그 프롬프트는 "쓰는 곳은 자기 샤드 하나뿐" 이라고 못 박는다. 한 글 안에서
    `docs/wiki/*.md` 를 고치라는 지시와 어긋나면 세션이 어느 쪽을 따를지 알 수 없다.
    위키 쪽 범위는 `wiki_page_prompt` 가 페이지 목록으로 따로 준다.
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.dep_excerpt']"/>
# 이 배치가 의존하는 아래층 레코드만 골라 짧은 글로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_survey
def dep_excerpt(merged, batch):
    """배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다.

    전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 쪼갠 이점이 사라진다.
    아직 레코드가 없는 이름은 아예 뺀다 — 없는 것을 가리키면 세션이 그 자리를 추론으로 메운다.
    """
    want = sorted({d for s in batch.get("symbols", []) for d in s.get("depends_on", [])})
    lines = ["  - %s — %s" % (k, (merged[k] or {}).get("means") or "(뜻 없음)")
             for k in want if k in merged]
    return "\n".join(lines)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.survey_batch_prompt']"/>
# 배치 하나를 맡을 세션에게 줄 글을 만드는 함수.
# 쓰는 것: run_mode1.warmup_section · 쓰이는 곳: run_mode1.run_survey
def survey_batch_prompt(repo, root, batch, dep_records, targets=None, total=0):
    """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

    `dep_records` 는 **아래층에서 이미 완성된** 레코드 중 이 배치의 심볼이 의존하는 것만
    발췌한 것이다(`dep_excerpt`). 전량을 주입하면 층이 올라갈수록 프롬프트가 부푼다.

    `targets` 는 warmup 이 판정한 다시 읽을 파일 목록이다. 있으면 **증분 조사**라는 뜻이라
    `warmup_section` 이 만든 범위 지시문을 뒤에 붙인다 — 배치 세션이 그것을 알아야
    기존 레코드의 `means` `does` 를 함부로 다시 쓰지 않는다. `None` 이면 전량 조사다.
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
     {root}/.venv/bin/python {root}/codegraph/file_cache.py get {repo} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 남긴다:
     {root}/.venv/bin/python {root}/codegraph/file_cache.py put {repo} <파일경로> <개요json>
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.nonnode_prompt']"/>
# 지도에 없는 용어들을 맡을 마지막 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_survey
def nonnode_prompt(repo, root):
    """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

    이것들은 코드 지도의 노드가 아니라 **층 축이 없다.** 대신 심볼 레코드가 재료다 —
    파일 레코드는 그 파일 안 심볼들의 완성된 means/does 를 보고 쓴다.
    그래서 심볼 층이 하나라도 남아 있으면 이 세션을 띄우면 안 된다.
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.symbol_layers']"/>
# 배치 계획에서 심볼마다 몇 층인지만 뽑아 표로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def symbol_layers(plan):
    """`survey-plan.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다."""
    return {s["id"]: L["level"]
            for L in plan.get("layers", [])
            for b in L.get("batches", [])
            for s in b.get("symbols", [])}


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.page_layers']"/>
# 위키 페이지마다 몇 번째로 써야 하는지 층을 매기는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def page_layers(pages, sym_layer):
    """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층.

    **왜 최대인가.** 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신
    링크할 수 있다. 가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다.

    아는 심볼이 하나도 없으면 층0 이다 — `index.md` 처럼 개괄만 있는 장이 여기 온다.
    카탈로그가 지어낸 이름 하나로 페이지가 맨 뒤로 밀리는 일도 이 규칙이 막는다.
    """
    out = {}
    for p in pages:
        known = [sym_layer[s] for s in p.get("symbols", []) if s in sym_layer]
        out[p["file"]] = max(known) if known else 0
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.wiki_catalogue_prompt']"/>
# 위키에 어떤 장을 둘지 정하는 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def wiki_catalogue_prompt(repo, root):
    """페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다.

    K6 의 층을 매기려면 이 둘이 있어야 하는데, deep-wiki 의 페이지는 심볼도 모듈도 아닌
    **주제** 단위라 기계가 결정론으로 못 만든다. 그래서 이 한 세션만 먼저 돈다.
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.wiki_page_prompt']"/>
# 위키 한 장을 맡을 세션에게 줄 글을 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_wiki
def wiki_page_prompt(repo, root, page, lower_pages):
    """장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다.

    **deep-wiki 플러그인을 고치지 않는다.** 그건 `~/.claude/plugins/cache/` 에 사는 캐시라
    업데이트에 덮인다. 대신 이 프롬프트가 감싸서 지시한다 — 지금 코드가 이미 쓰는 방식이다.
    """
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.node_argv']"/>
# 위키 기계 단계 하나를 부르는 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 5. 기계 단계의 명령줄 ────────────────────────────────────────────────
def node_argv(root, script, repo):
    """`scripts/wiki/*.mjs` 하나를 부른다. node 는 PATH 에서 찾는다."""
    return ["node", os.path.join(root, "scripts", "wiki", script), repo]


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.terms_argv']"/>
# 용어 사전을 만드는 단계의 명령줄을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def terms_argv(python, root, repo, codegraph, reading):
    """`terms_db.py` 명령줄.

    **정적 `codegraph.json` 을 위치 인자로 반드시 준다.** `--reading` 만 주면
    읽기 레코드의 투영이 그 파일을 **덮어쓴다** — 정적 수집기가 찾은 노드가
    조용히 사라진다(이 저장소 자신에서 노드 95 가 투영본 때문에 뒤바뀐 적이 있다).
    둘 다 주면 구조는 codegraph 가 이긴다.
    """
    argv = [python, os.path.join(root, "codegraph", "terms_db.py")]
    if codegraph:
        argv.append(codegraph)
    argv += ["--repo", repo]
    if reading:
        argv += ["--reading", reading]
    return argv


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1._hms']"/>
# 초를 사람이 읽는 시간 꼴로 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.format_report
# ── 6. 보고 ─────────────────────────────────────────────────────────────
def _hms(seconds):
    """초를 사람이 읽는 꼴로. 재는 것이 목적이라 소수 첫째 자리까지 남긴다."""
    s = float(seconds)
    if s < 60:
        return "%.1f초" % s
    return "%d분 %04.1f초" % (int(s // 60), s % 60)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.format_report']"/>
# 단계별 측정값을 표 한 장으로 만든다.
# 쓰는 것: run_mode1.sum_usage, run_mode1._hms · 쓰이는 곳: run_mode1.main
def format_report(rows, wall_seconds=None):
    """단계별 표 + 합계 줄. 이 실행기의 **산출물 본체**다.

    `wall_seconds` 는 **병렬 때문에** 생겼다. 층 안에서 배치 8개가 동시에 돌면
    행의 초를 더한 값이 사람이 기다린 시간의 8배까지 부푼다. 진짜 벽시계를 부르는 쪽이
    재서 넘긴다. 안 넘기면 예전처럼 행을 더한다 — Mode 1.5 와 Mode 2 는 병렬이 아니라 그게 맞다.
    """
    head = ["단계", "상태", "시간", "입력", "출력", "캐시읽기", "캐시생성", "합계", "턴", "비용($)"]
    body = []
    for r in rows:
        u = r["usage"]
        body.append([
            r["stage"],
            "건너뜀" if r.get("skipped") else ("성공" if r.get("ok") else "실패"),
            _hms(r["seconds"]),
            "{:,}".format(u["input"]), "{:,}".format(u["output"]),
            "{:,}".format(u["cache_read"]), "{:,}".format(u["cache_write"]),
            "{:,}".format(u["total"]), str(u["turns"]), "%.4f" % u["cost_usd"],
        ])
    tot = sum_usage([r["usage"] for r in rows])
    total_seconds = (sum(float(r["seconds"]) for r in rows)
                     if wall_seconds is None else float(wall_seconds))
    body.append([
        "합계", "", _hms(total_seconds),
        "{:,}".format(tot["input"]), "{:,}".format(tot["output"]),
        "{:,}".format(tot["cache_read"]), "{:,}".format(tot["cache_write"]),
        "{:,}".format(tot["total"]), str(tot["turns"]), "%.4f" % tot["cost_usd"],
    ])

    # 한글은 폭이 두 칸이라 len() 으로는 안 맞는다. 표시 폭을 따로 센다.
    def w(s):
        return sum(2 if ord(c) > 0x2E80 else 1 for c in str(s))
    cols = [max(w(head[i]), max(w(row[i]) for row in body)) for i in range(len(head))]
    def line(cells):
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.plan_summary']"/>
# 층 계획을 사람이 읽는 줄들로 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def plan_summary(plan):
    """층·배치·동시 물결 수를 줄 목록으로. **돈을 쓰기 전에** 몇 세션이 뜨는지 보여 주려는 것이다.

    `--dry-run` 과 `survey-plan` 단계가 같은 글을 쓴다. 순수 함수라 시험이 쉽다.
    """
    out = []
    for L in plan.get("layers", []):
        if L.get("kind") == "non-node":
            out.append("  층%d — 비노드 용어 (한 세션)" % L["level"])
        else:
            n = len(L.get("batches", []))
            out.append("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                       % (L["level"], L["symbol_count"], L["file_count"], n))
    총배치 = sum(len(L.get("batches", [])) for L in plan.get("layers", []))
    out.append("  합계 — 심볼 %d · 층 %d · 배치 %d (LLM 세션이 그만큼 뜬다)"
               % (plan["totals"]["symbols"], plan["totals"]["levels"], 총배치))
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.stage_totals']"/>
# 배치 행들을 단계 단위로 접어 소계를 내는 함수.
# 쓰는 것: run_mode1.sum_usage · 쓰이는 곳: run_mode1.main
def stage_totals(rows):
    """`survey/L0-B00` 같은 행을 `survey` 로 접는다. `{단계: 합친 usage}`.

    배치가 스물이 넘으면 표를 눈으로 훑어 "어느 단계가 비쌌나" 를 못 본다.
    `ARCHITECTURE.md` 의 여덟 줄짜리 표와 대조할 수 있는 모양이 이것이다.
    """
    byname = collections.OrderedDict()
    for r in rows:
        name = r["stage"].split("/")[0]
        byname.setdefault(name, []).append(r["usage"])
    return collections.OrderedDict((k, sum_usage(v)) for k, v in byname.items())


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1._Heartbeat']"/>
# 오래 도는 단계 옆에서 경과 시간을 알리는 조각.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 7. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
class _Heartbeat:
    """오래 도는 단계 옆에서 경과 시간을 알린다.

    에이전트 단계는 수 분에서 십수 분이 걸리는데 `--output-format json` 은 끝나야
    한 덩이로 나온다. 아무것도 안 찍히면 사람이 멈춘 줄 안다.
    """

    def __init__(self, label, every=30.0):
        self.label, self.every = label, every
        self._stop = threading.Event()
        self._t0 = time.monotonic()
        self._th = threading.Thread(target=self._tick, daemon=True)

    def _tick(self):
        while not self._stop.wait(self.every):
            print("    … %s 진행 중 (%s)" % (self.label, _hms(time.monotonic() - self._t0)),
                  file=sys.stderr, flush=True)

    def __enter__(self):
        self._th.start()
        return self

    def __exit__(self, *_):
        self._stop.set()


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_agent_with']"/>
# 주어진 글로 모형을 한 번 부르고 걸린 시간과 결과를 함께 내는 함수.
# 쓰는 것: run_mode1.claude_argv · 쓰이는 곳: run_mode1.run_layer
def run_agent_with(model, repo, root, prompt, timeout=None, label=None):
    """`claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`.

    **시간을 여기서 잰다.** 배치들이 동시에 도는 동안 부르는 쪽은 층 전체만 잴 수 있어
    어느 배치가 비쌌는지 모른다. 다음에 `--target` 을 조절하려면 배치별 값이 있어야 한다.

    **하트비트를 여기 두지 않는다.** 8개가 동시에 찍으면 화면이 못 읽는 글이 된다 —
    층 하나를 감싸는 하트비트 하나면 충분하다(`run_layer` 를 부르는 쪽이 건다).
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_layer']"/>
# 한 층의 배치들을 동시에 돌리고 각각의 측정값을 모으는 함수.
# 쓰는 것: run_mode1.run_agent_with · 쓰이는 곳: run_mode1.run_survey, run_mode1.run_wiki
def run_layer(model, repo, root, jobs, concurrency=8, timeout=None):
    """한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다(K2).

    같은 층끼리는 서로 의존하지 않으므로 순서가 결과를 바꾸지 않는다 — 그래서 병렬이 안전하다.
    같은 층의 배치는 **같은 파일을 가리키지 않는다**(`survey_plan.pack` 이 보장한다).
    그래서 파일 lock 이 필요 없다.

    **자식 프로세스를 기다리는 일이라 스레드로 충분하다.** GIL 은 여기서 문제가 되지 않는다.

    `jobs` 는 `[(라벨, 프롬프트), …]`. 낸 것은 `[(라벨, 초, 종료코드, 결과 또는 None), …]` 이고
    **라벨 순서로 정렬**해서 낸다 — 끝나는 순서는 실행마다 흔들려 보고 표를 대조할 수 없게 된다.

    **한 배치가 터져도 층을 버리지 않는다.** 20분짜리 층이 예외 하나로 날아가면 안 된다.
    터진 배치는 종료 코드 -1 · 결과 None 인 행으로 남고, 부르는 쪽이 실패로 센다.
    """
    if not jobs:
        return []
    rows = []
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.merge_shards']"/>
# 배치들이 따로 쓴 조각을 하나로 합치고 이름 충돌을 푸는 함수.
# 쓰는 것: run_mode1._qualified · 쓰이는 곳: run_mode1.run_survey
def merge_shards(shard_dir, existing):
    """샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.**

    배치 세션은 자기 배치만 보므로 `main` 이 9파일에 있다는 것을 알 수 없다.
    전역을 보는 것은 이 함수뿐이다 — 겹치면 겹친 **전원**을 `<파일줄기>.<이름>` 으로 고친다.
    한쪽만 한정하면 나중에 또 겹친다(`codebase-terms-survey` 스킬의 키 규칙).

    **망가진 샤드는 건너뛴다.** 배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 결과를 버리지 않는다.
    무엇을 건너뛰었는지는 stderr 에 적어 사람이 다시 돌릴 수 있게 한다.

    ⚠ **`existing` 에는 누적본이 아니라 조사 이전의 원본을 준다.** 이 함수는 층마다 불리고
    그때마다 샤드 전부를 다시 읽는다. 누적본을 넘기면 이미 합쳐 둔 레코드를 **자기 자신과의
    충돌**로 보고 개명해 버린다 — 🔵 2026-08-30 연기 시험에서 레코드 수가 38 -> 27 로
    줄어드는 것으로 드러났다. 샤드가 진실의 원본이고 이 함수는 그 순수 함수다.

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
                shard = json.load(f)
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1._qualified']"/>
# 겹친 이름 앞에 파일 줄기를 붙여 서로 구별되게 만드는 함수.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.merge_shards
def _qualified(key, rec):
    """`<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다."""
    where = (rec or {}).get("where") or ""
    stem = os.path.splitext(os.path.basename(where.split(":")[0]))[0]
    return "%s.%s" % (stem, key) if stem else key


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_machine']"/>
# 기계 단계 하나를 부른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def run_machine(argv, label):
    """기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다."""
    with _Heartbeat(label, every=60.0):
        p = subprocess.run(argv)
    return p.returncode


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_warmup']"/>
# 무엇을 다시 읽어야 하는지 판정하는 앞 관문.
# 쓰는 것: run_mode1.lang_of, run_mode1.changed_seed · 쓰이는 곳: run_mode1.main
def run_warmup(repo, codegraph, hops):
    """관문 ① — 무엇을 다시 읽어야 하는지 판정한다. **매니페스트를 쓰지는 않는다.**

    쓰기를 여기서 하면 에이전트가 실패했을 때도 "유효" 로 기록되어, 다음 실행이
    읽지 않은 파일을 읽은 것으로 친다. 그래서 갱신은 `save_warmup` 이 따로 한다.

    판정할 수 없으면 `targets` 를 `None` 으로 낸다 — 실패가 아니다. 그러면
    `should_call_agent` 가 옛 동작(전량 조사)으로 돌아간다.

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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.save_warmup']"/>
# 판정 기록을 확정하는 뒤 관문.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def save_warmup(cache_path, entries, rows):
    """관문 ② — **전수조사가 실제로 해낸 뒤에만** 매니페스트를 갱신한다.

    앞칸이 판정을 못 했거나(`entries is None`) 전수조사가 실패했으면 **쓰지 않는다.**
    쓰지 않는 것이 안전한 쪽이다 — 다음 실행이 전량을 다시 읽을 뿐 틀리지는 않는다.

    ⚠ **단계 이름만 떼어 본다.** 층 병렬이 되면서 행 라벨이 `survey/L0-B00` 꼴이 됐다.
    예전처럼 `r["stage"] == "survey"` 로 비교하면 **영원히 거짓**이 되어 관문이
    fail-open 이 된다 — 조사가 실패해도 매니페스트가 '유효' 로 남는 바로 그 사고다.
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_survey']"/>
# 전수조사를 층 오름차순으로 돌리고 층마다 샤드를 합치는 함수.
# 쓰는 것: run_mode1.run_layer, run_mode1.merge_shards, run_mode1.survey_batch_prompt, run_mode1.nonnode_prompt, run_mode1.dep_excerpt · 쓰이는 곳: run_mode1.main
def run_survey(model, repo, root, plan, concurrency, timeout, reading_path,
               targets=None, total=0):
    """층 사이는 순차, 층 안은 병렬(K2). `[행, …]` 을 낸다.

    **층이 끝날 때마다 병합해서 디스크에 쓴다.** 다음 층의 배치가 아래층 레코드를 발췌해
    받아야 하고, 중간에 죽어도 거기까지는 남아야 한다.

    **샤드가 이미 있는 배치는 건너뛴다(J4).** 재시도 구조를 만들지 않고도 `--only survey` 로
    다시 돌리면 실패한 배치만 다시 돈다.
    """
    shard_dir = os.path.join(repo, "out", "codegraph-raw", "_shards")
    os.makedirs(shard_dir, exist_ok=True)
    # **조사 이전의 원본**을 따로 붙들어 둔다. 층마다 `merge_shards` 에 이것을 준다 —
    # 누적본을 주면 이미 합친 레코드를 자기 자신과의 충돌로 보고 개명한다(위 경고).
    baseline = {}
    if os.path.exists(reading_path):
        with open(reading_path, encoding="utf-8") as f:
            baseline = json.load(f)
    merged = dict(baseline)

    rows = []
    for L in plan["layers"]:
        if L.get("kind") == "non-node":
            jobs = [("NONNODE", nonnode_prompt(repo, root))]
            label_of = {"NONNODE": "survey/L%d-비노드" % L["level"]}
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
        with _Heartbeat("survey 층%d" % L["level"]):
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_wiki']"/>
# 위키 목차를 받고 장들을 층 오름차순으로 쓰게 하는 함수.
# 쓰는 것: run_mode1.run_layer, run_mode1.wiki_catalogue_prompt, run_mode1.wiki_page_prompt, run_mode1.page_layers, run_mode1.symbol_layers · 쓰이는 곳: run_mode1.main
def run_wiki(model, repo, root, plan, concurrency, timeout):
    """카탈로그 한 세션(J3) -> 장들을 층 오름차순 병렬(K6).

    목차를 기계가 못 만드는 이유는 deep-wiki 의 장이 심볼도 모듈도 아닌 **주제** 단위라서다.
    그래서 이 한 세션만 먼저 돈다.
    """
    raw = os.path.join(repo, "out", "codegraph-raw")
    wiki_plan_path = os.path.join(raw, "wiki-plan.json")
    rows = []

    if not os.path.exists(wiki_plan_path):
        with _Heartbeat("wiki 목차"):
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
        pages = json.load(f)["pages"]
    lv = page_layers(pages, symbol_layers(plan))
    done = []
    for k in sorted(set(lv.values())):
        here = [pg for pg in pages if lv[pg["file"]] == k
                and not os.path.exists(os.path.join(repo, "docs", "wiki", pg["file"]))]
        if not here:
            continue
        lower = "\n".join("  - %s — %s" % (pg["file"], pg.get("title") or pg["file"])
                          for pg in done)
        jobs = [(pg["file"], wiki_page_prompt(repo, root, pg, lower)) for pg in here]
        print("  층%d — 장 %d개를 동시 %d 로 쓴다" % (k, len(jobs), concurrency), flush=True)
        with _Heartbeat("wiki 층%d" % k):
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.main']"/>
# 명령줄을 읽고 단계를 차례로 돌린 뒤 측정 표를 낸다.
# 쓰는 것: run_mode1.plan_stages, run_mode1.terms_argv, run_mode1.format_report, run_mode1.run_warmup, run_mode1.save_warmup (+4) · 쓰이는 곳: 없음
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    # 🔴 서브에이전트 모델은 Claude Sonnet 5 다. 별명(`sonnet`)이 아니라 정확한 ID 를 적는다 —
    #    별명은 최신판을 따라 움직여 측정이 흔들린다. 예전 기본값은 `opus` 였다.
    #    이 값이 main -> run_survey/run_wiki -> run_layer -> run_agent_with -> claude_argv
    #    사슬을 그대로 타고 내려간다. **중간에서 모형을 바꾸지 않는다.**
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
        # 돈을 쓰기 전에 **몇 세션이 뜨는지** 보여 준다. 층 계산은 결정론이라 지금 해도 같다.
        if "survey-plan" in stages and os.path.exists(codegraph):
            with open(codegraph, encoding="utf-8") as f:
                미리 = survey_plan.plan(json.load(f), a.target)
            print("\n층 계획 (기계가 결정론으로 낸다 — 모형을 부르지 않는다)")
            for L in plan_summary(미리):
                print(L)
        return 0

    # warmup 이 앞칸에서 담아 두고 뒤칸이 꺼내 쓴다. 같은 프로세스 안이라 파일로 넘길 이유가 없다.
    #   targets  에이전트가 읽을 파일 목록. None 이면 판정을 못 했다는 뜻이다(= 전량 조사)
    #   entries  갱신될 매니페스트. 에이전트가 성공한 뒤에만 쓴다
    targets, entries, warmup_cache, tracked_n = None, None, None, 0
    survey_plan_path = os.path.join(raw, "survey-plan.json")
    plan_json = None
    rows, t_all = [], time.monotonic()
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
        elif stage == "survey-plan":
            # **기계 단계다. 모형을 부르지 않는다.** 층은 codegraph.json 하나로 결정론이다 —
            # 의존을 몇 개 갖는지(out_deg)가 아니라 **위상 깊이**로 매긴다. 🔵 실측에서
            # out_deg 1 무리 안에 깊이 1·2·3·4 가 섞여 있었다(K1).
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
                for L in plan_summary(plan_json):
                    print(L)
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
                    plan_json = json.load(f)
                print("층 계획을 디스크에서 읽었다 — %s" % survey_plan_path, flush=True)
            if stage == "survey":
                got = run_survey(a.model, repo, ROOT, plan_json, a.concurrency,
                                 a.timeout, reading, targets, tracked_n)
            else:
                got = run_wiki(a.model, repo, ROOT, plan_json, a.concurrency, a.timeout)
            rows += got
            ok = bool(got) and all(r["ok"] for r in got)
            print("%s — %s (%s · 세션 %d개)"
                  % (stage, "성공" if ok else "실패", _hms(time.monotonic() - t0), len(got)),
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
            print("%s — %s (%s)" % (stage, "성공" if ok else "실패", _hms(seconds)), flush=True)
        if not all(r["ok"] for r in rows):
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

    wall = time.monotonic() - t_all
    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % _hms(wall))
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
