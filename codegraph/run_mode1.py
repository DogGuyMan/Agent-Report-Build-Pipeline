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

## 다섯 단계 — LLM 은 그중 **하나**뿐이다

    prep ──▶ agent ──▶ terms ──▶ build ──▶ check
    기계      LLM 1개    기계      기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `prep`  | 정적 계층. clang-uml/clang-doc 또는 roslyn-dump 를 돌려 코드 지도를 만든다 | `scripts/wiki/prep.mjs` |
| `agent` | **전수조사와 위키 산문을 한 세션에서 이어 한다** | `claude -p` 1회 |
| `terms` | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `codegraph/terms_db.py` |
| `build` | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `scripts/wiki/build.mjs` |
| `check` | 산문의 인용을 저장소 실물과 대조한다 | `scripts/wiki/check.mjs` |

**에이전트를 하나로 묶은 것이 이 설계의 급소다.** 전수조사와 산문을 두 세션으로 쪼개면
두 번째 세션이 저장소를 처음부터 다시 읽는다 — 프롬프트 캐시가 새로 서서 토큰이 부풀고,
그러면 "Mode 1 한 바퀴에 얼마가 드는가" 라는 측정값의 뜻이 달라진다.

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

    .venv/bin/python codegraph/run_mode1.py <저장소> [--model opus] [--only prep,check]
                                            [--skip agent] [--json 측정.json] [--dry-run]
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time

# 이 파일은 <ROOT>/codegraph/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 단계는 다섯 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["prep", "agent", "terms", "build", "check"]

# LLM 을 부르는 단계. **하나뿐이라는 것이 이 실행기의 전제**다.
AGENT_STAGES = {"agent"}


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.is_agent_stage']"/>
# 이 단계가 큰 언어 모형을 부르는 자리인지 답한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# ── 1. 단계 고르기 ──────────────────────────────────────────────────────
def is_agent_stage(stage):
    """이 단계가 모형을 부르는가. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.plan_stages']"/>
# 다섯 단계 중 무엇을 실제로 돌릴지 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def plan_stages(has_codegraph, has_reading, has_prose, only=None, skip=None):
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 시험이 쉽다.

    `prep` 은 늘 남긴다 — 이미 코드 지도가 있으면 건너뛸지를 `prepPlan` 자신이 정한다
    (`scripts/wiki/prep.mjs` 의 `hasCodegraph`). 여기서 미리 빼면 그 판단을 뺏는 것이다.

    `agent` 만은 산출물이 **둘 다** 있을 때 뺀다. 한쪽만 있으면 여전히 부른다 —
    한 세션 안에서 남은 쪽만 하면 되고, 그 판단은 에이전트가 재료를 보고 한다.
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
        if s == "agent" and has_reading and has_prose:
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
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.format_report
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
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_agent
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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.agent_prompt']"/>
# 한 세션이 할 일 전부를 적은 글.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.run_agent
def agent_prompt(repo, root):
    """한 세션이 할 일 전부. **전수조사와 산문을 둘 다** 여기서 시킨다.

    쪼개지 않는 이유는 캐시다 — 두 세션으로 나누면 두 번째가 저장소를 처음부터
    다시 읽어 토큰이 부풀고, 그러면 측정값이 파이프라인의 비용이 아니라 세션 수의
    함수가 된다.
    """
    return """\
너는 report-builder 의 **Mode 1 에이전트**다. 대상 저장소 하나를 읽어 두 가지를 낸다.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 진행하지 말고
무엇이 없어서 막혔는지 적고 끝낸다.

대상 저장소   {repo}
도구 저장소   {root}   (report-builder. 규약과 스킬이 여기 있다)

## 이미 있는 재료 — 다시 만들지 마라

정적 계층은 이미 돌았다. 아래를 **먼저 읽고** 그 위에서 시작한다.

  {repo}/out/codegraph-raw/codegraph.json   코드 지도(점=타입·함수, 선=관계)
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 · hotspot 표
  {repo}/out/codegraph-raw/ranking.json     모듈 중요도(PageRank · hotspot)
  {repo}/out/codegraph-raw/modules.svg      모듈 관계도(큰 그림). .dot 와 .png 도 옆에 있다

## 할 일 1 — 용어 전수조사

`codebase-terms-survey` 스킬을 Skill 도구로 불러 그 절차대로 한다. 산출물은

  {repo}/docs/codegraph/terms-reading.json

레코드 계약은 `{{kind, module, where, means, does, uses[], confidence, source}}` 이고
**`where` 는 실제 `파일:줄` 이어야 한다** — 기계가 L1/L2/L3 로 검사한다. 지어내면 걸린다.
`confidence` 는 HIGH(읽었다) / MEDIUM(일부) / LOW(이름만) 중 하나로 반드시 적는다.

## 할 일 2 — 위키 산문

`/deep-wiki:page` 의 규정(3단계 절차 · Mermaid · 인용 규격 · 미확인 영역 표기)을 따르되
**사이트 조립은 하지 마라** — 그건 이 도구의 `report-wiki build` 가 한다. 너는 평평한
마크다운만 쓴다.

  {repo}/docs/wiki/*.md      (하위 폴더 없이. `index.md` 를 반드시 포함)

- 페이지 수는 모듈 수에 맞춘다. `ranking.json` 상위 모듈부터.
- **인용은 로컬 규격 `(경로:줄)`** 로 쓴다. 저장소 뿌리 기준 상대 경로다.
- Mermaid 는 소형만(노드 10개 이하). 큰 그림은 `out/codegraph-raw/modules.svg` 를 가리킨다.
- 확인 못 한 것은 `(Unknown - verify in <파일>)` 로 남긴다. 지어내지 않는다.

## 규율

- **커밋하지 마라.** `git add` · `git commit` 금지.
- 대상 저장소의 **소스는 읽기만** 한다. 쓰는 곳은 `docs/codegraph/` 와 `docs/wiki/` 둘뿐이다.
- 주석과 문서는 **한국어**. 약어를 피하고 메커니즘을 먼저 쓴다.
- 읽는 사람은 배경 지식이 없다고 가정한다(객체지향을 갓 배운 대학 1학년 눈높이).
- 코드에 글자로 없는 것은 쓰지 않는다. "~일 것이다" 대신 읽고 말한다.

끝나면 만든 파일 목록과 각 파일의 레코드 수 / 페이지 줄 수를 한 표로 보고한다.
""".format(repo=repo, root=root)


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
def format_report(rows):
    """단계별 표 + 합계 줄. 이 실행기의 **산출물 본체**다."""
    head = ["단계", "상태", "시간", "입력", "출력", "캐시읽기", "캐시생성", "합계", "턴", "비용($)"]
    body = []
    for r in rows:
        u = r["usage"]
        body.append([
            r["stage"],
            "성공" if r.get("ok") else "실패",
            _hms(r["seconds"]),
            "{:,}".format(u["input"]), "{:,}".format(u["output"]),
            "{:,}".format(u["cache_read"]), "{:,}".format(u["cache_write"]),
            "{:,}".format(u["total"]), str(u["turns"]), "%.4f" % u["cost_usd"],
        ])
    tot = sum_usage([r["usage"] for r in rows])
    body.append([
        "합계", "", _hms(sum(float(r["seconds"]) for r in rows)),
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
        if not r.get("ok"):
            out.append("실패 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
    return "\n".join(out)


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


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_agent']"/>
# 모형을 한 번 부르고 그 결과 기록을 돌려준다.
# 쓰는 것: run_mode1.claude_argv, run_mode1.agent_prompt · 쓰이는 곳: run_mode1.main
def run_agent(model, repo, root, timeout=None):
    """`claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`."""
    argv = claude_argv(model=model, repo=repo, extra_dirs=[root])
    with _Heartbeat("agent"):
        p = subprocess.run(argv, input=agent_prompt(repo, root), cwd=repo,
                           capture_output=True, text=True, timeout=timeout)
    try:
        return p.returncode, json.loads(p.stdout)
    except (ValueError, TypeError):
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print(tail, file=sys.stderr)
        return p.returncode, None


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_machine']"/>
# 기계 단계 하나를 부른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def run_machine(argv, label):
    """기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다."""
    with _Heartbeat(label, every=60.0):
        p = subprocess.run(argv)
    return p.returncode


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.main']"/>
# 명령줄을 읽고 단계를 차례로 돌린 뒤 측정 표를 낸다.
# 쓰는 것: run_mode1.plan_stages, run_mode1.run_agent, run_mode1.terms_argv, run_mode1.format_report · 쓰이는 곳: 없음
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    ap.add_argument("--model", default="opus", help="에이전트가 쓸 모형 (기본: opus)")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
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
        return 0

    rows, t_all = [], time.monotonic()
    for stage in stages:
        print("\n── %s ──────────────────────────────" % stage, flush=True)
        t0 = time.monotonic()
        if stage == "agent":
            rc, result = run_agent(a.model, repo, ROOT, timeout=a.timeout)
            ok, why = agent_verdict(rc, result)
            usage = normalize_usage(result)
            if result and result.get("result"):
                print(result["result"])
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
            usage = normalize_usage(None)
        seconds = time.monotonic() - t0
        rows.append({"stage": stage, "seconds": seconds, "usage": usage,
                     "ok": ok, "why": why})
        print("%s — %s (%s)" % (stage, "성공" if ok else "실패", _hms(seconds)), flush=True)
        if not ok:
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % _hms(time.monotonic() - t_all))
    print("=" * 72)
    print(format_report(rows))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": a.model, "stages": rows,
                       "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": time.monotonic() - t_all},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
