#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_mode2.py']"/>
# 설계 검토 보고서를 짓는 흐름을 한 번에 돌리며 시간과 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# Mode 2 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: run_mode1 · 쓰이는 곳: 없음
"""Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

재는 코드는 `measure.py` 의 것을 그대로 import 해 쓴다 — 여기에 사본이 없다.

## 네 단계 — LLM 은 그중 **하나**뿐이다

    init ──▶ agent ──▶ build ──▶ check
    기계      LLM 1개    기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `init`  | 뼈대 `data.ts` · `report.tsx` 를 만든다. 이미 있으면 스스로 건너뛴다 | `viz/init.py` |
| `agent` | **원고를 쓴다** — 설계 문서를 읽어 결정 표 · 서사 · 확신도 배지를 채운다 | `claude -p` 1회 |
| `build` | esbuild 트랜스파일 → React 정적 렌더 → 한 장짜리 HTML 조립 | `viz/build.py` |
| `check` | `<script>` 수 · `tsc --noEmit` · 링크 무결성 · 용어집 대조 · builderVersion | `viz/check.py` |

## 이 파이프라인의 LLM 자리는 **원고 쓰기** 하나다

`init` 은 스켈레톤만 만든다. 결정 표 · 서사 · 확신도 배지 · 옵션표를 채우는 절차의
정본은 `spec-review-dashboard` 스킬이다. **판정(수용/보류/번복)은 절대 LLM Model이 하지
않는다** — `VerdictFooter` 는 비워서 낸다.

## 함정

- **명령마다 작업 디렉토리가 다르다.** `init` 은 `specs/` 나 `plans/` 가 있는 프로젝트
  뿌리에서, `build` 와 `check` 는 보고서 폴더(`<자리>/<slug>/`)에서 돈다. 여기서 틀리면
  오류 없이 **조용히 엉뚱한 곳에 파일이 생긴다**(`stage_cwd`).
- **`claude` 는 막혀도 종료 코드 0 을 낼 수 있다.** `is_error` 와 `subtype` 을 봐야 한다.
  판정 코드는 `measure.agent_verdict` 를 그대로 쓴다.
- **재는 코드를 새로 짜지 않는다.** 토큰 세기·합계·표 그리기는 `measure` 에 있다.
  각자 세면 같은 이름의 숫자가 두 실행기에서 서로 다른 뜻을 갖는다.
- **Mode 1.5 의 `terms.json` 을 기계로 병합하지 않는다.** 있으면 프롬프트에 **알려 주기만**
  하고, 옮겨 적는 것은 LLM Model의 일이다.
- **Mode 1 봉인은 근거일 뿐 문이 아니다.** 있으면 프롬프트에 경로를 싣고, 없거나 깨졌어도 설계 문서만으로
  진행한다. 판정은 `machine/evidence.py` 가 하고 여기서는 읽기만 한다. `--dry-run` 은 그것도 부르지 않는다.

## 쓰는 법

    .venv/bin/python runner/run_mode2.py <프로젝트> <slug> [--model <LLM Model ID>]
                                            [--only init,build] [--skip agent]
                                            [--json 측정.json] [--dry-run]

`<프로젝트>` 는 **`specs/` 나 `plans/` 가 있는 폴더**다. 저장소 뿌리가 아닐 수 있다.
원본은 두 자리 중 어디든 되고, 보고서는 **그 원본 옆**에 생긴다.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypedDict

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import msgspec  # noqa: E402

import measure as M  # noqa: E402
import pipeline as P  # noqa: E402

# 재는 코드(`hms` · `Heartbeat` · `normalize_usage` · `format_report` …)의 원본은
# `measure.py` 하나뿐이다. 여기에는 사본이 없다.
normalize_usage = M.normalize_usage
sum_usage = M.sum_usage
agent_verdict = M.agent_verdict
claude_argv = M.claude_argv
format_report = M.format_report
hms = M.hms
Heartbeat = M.Heartbeat

# 단계는 넷 고정이다.
STAGES = ["init", "agent", "build", "check"]

# LLM 을 부르는 단계. 하나뿐이다 — 토큰이 잡히는 자리도 여기뿐이다.
AGENT_STAGES = {"agent"}

# 프로젝트 뿌리에서 도는 단계와 보고서 폴더에서 도는 단계. 틀리면 오류 없이
# 엉뚱한 곳에 파일이 생기므로 상수로 드러내 둔다.
PROJECT_STAGES = {"init", "agent"}


class DocDirConfig(TypedDict):
    """`[[doc_dirs]]` 하나 — 원본 문서가 사는 폴더와 그 파일명 꼴."""
    dir: str
    pattern: str


class ModelsConfig(TypedDict):
    """`[models]` — `agent` 세션의 Model."""
    mode2_agent: str


class ReportConfig(TypedDict):
    """`config/report.toml`. 원본 문서 자리 규칙은 `viz/init.py` 도 같은 파일에서 읽는다."""
    models: ModelsConfig
    doc_dirs: list[DocDirConfig]


with open(os.path.join(ROOT, "config", "report.toml"), "rb") as _f:
    CONFIG = msgspec.toml.decode(_f.read(), type=ReportConfig)

# 원본 문서가 사는 자리와 자리마다 다른 파일명 관례. 값은 `config/report.toml` 의 `doc_dirs` 다.
DOC_DIRS = [(d["dir"], re.compile(d["pattern"])) for d in CONFIG["doc_dirs"]]


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.report_dir']"/>
# 보고서 파일들이 들어 있는 폴더의 경로를 만들어 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode2.agent_prompt, runner.run_mode2.main, runner.test_run_mode2.test_report_dir_is_specs_slash_slug
# ── 1. 자리 잡기 — 어디에서 무엇을 도는가 ────────────────────────────────
def report_dir(project: str, slug: str, doc_dir: str = "specs") -> str:
    """보고서가 사는 폴더. **원본 문서 옆**이다 — `specs/<slug>/` 또는 `plans/<slug>/`.

    `doc_dir` 를 안 주면 `specs` 다 — 옛 호출을 깨지 않기 위해서다.
    """
    return os.path.join(project, doc_dir, slug)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.stage_cwd']"/>
# 네 단계(init/agent/build/check) 중 하나를 어느 작업 디렉토리에서 실행해야 하는지 정해 주는 함수다.
# 쓰는 것: runner.run_mode2.STAGES, runner.run_mode2.PROJECT_STAGES · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_build_and_check_run_inside_the_report_folder, runner.test_run_mode2.test_init_runs_at_the_project_root, runner.test_run_mode2.test_stage_cwd_rejects_an_unknown_stage, runner.test_run_mode2.test_the_agent_also_runs_at_the_project_root
def stage_cwd(stage: str, project: str, report_dir: str) -> str:
    """단계 하나를 어느 폴더에서 돌릴지 답한다. **여기서 틀리면 오류 없이 엉뚱한 곳에 쓴다.**

    `init.py` 는 `cwd` 아래 `specs/`·`plans/` 를 보므로 프로젝트 뿌리가 필요하고,
    `build.py`·`check.py` 는 `cwd` 에서 `data.ts`·`report.tsx` 를 읽으므로 보고서
    폴더가 필요하다. LLM Model(`agent`)은 둘 다 봐야 해서 뿌리에 세운다.
    """
    if stage not in STAGES:
        raise ValueError("모르는 단계: %s (있는 것: %s)" % (stage, ", ".join(STAGES)))
    return project if stage in PROJECT_STAGES else report_dir


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.is_agent_stage']"/>
# 이 단계가 LLM(큰 언어 LLM Model)을 실제로 부르는 자리인지 참/거짓으로 답해 주는 함수다.
# 쓰는 것: runner.run_mode2.AGENT_STAGES · 쓰이는 곳: runner.test_run_mode2.test_only_one_stage_calls_the_model
def is_agent_stage(stage: str) -> bool:
    """이 단계가 큰 언어 LLM Model을 부르는 자리인지 답한다. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.plan_stages']"/>
# init, agent, build, check 네 단계 중 이번에 실제로 돌릴 단계들만 골라 순서대로 나열해 주는 함수다. 파일이나 네트워크를 건드리지 않고 입력값만으로 답을 정한다.
# 쓰는 것: runner.run_mode2.STAGES · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_only_one_stage_calls_the_model, runner.test_run_mode2.test_plan_keeps_init_even_when_the_manuscript_exists, runner.test_run_mode2.test_plan_only_and_skip_are_honoured, runner.test_run_mode2.test_plan_rejects_an_unknown_stage (+2)
# ── 2. 단계 고르기 (파일 시스템을 보지 않는 순수 함수) ────────────────────
def plan_stages(has_manuscript: bool, only: Iterable[str] | None = None,
                skip: Iterable[str] | None = None) -> list[str]:
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다.

    `init` 은 늘 남긴다 — 이미 `data.ts` 가 있으면 건너뛸지를 `init.py` 자신이
    정한다(멱등 경로에서 exit 0). 여기서 미리 빼면 그 판단을 뺏는 것이다.

    `agent` 만은 **원고가 이미 채워졌을 때** 뺀다 — 사람이 쓴 글을 LLM Model이 덮어쓰면
    되돌릴 수 없다.
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
        if s == "agent" and has_manuscript:
            continue
        out.append(s)
    return out


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.manuscript_is_written']"/>
# data.ts 와 report.tsx 두 파일의 글자 내용을 보고 원고(보고서 본문)가 이미 다 채워졌는지 판단하는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_a_filled_data_and_report_is_a_manuscript, runner.test_run_mode2.test_a_fresh_skeleton_is_not_a_manuscript, runner.test_run_mode2.test_decisions_without_matching_sections_is_not_a_manuscript, runner.test_run_mode2.test_missing_files_are_not_a_manuscript
def manuscript_is_written(data_source: str | None, report_source: str | None) -> bool:
    """원고가 이미 채워졌는가. 뼈대와 채워진 글을 **글자로** 가른다.

    **두 조건을 다 봐야 한다.** `init` 이 만든 뼈대는 `decisions: []` 이고 본문에
    `<Section title="D…">` 가 없다. 한쪽만 보면 반쯤 쓰다 만 원고를 완성으로 착각한다.
    """
    if not data_source or not report_source:
        return False
    if re.search(r"decisions:\s*\[\s*\]", data_source):
        return False
    return bool(re.search(r'<Section\s+title="D\d', report_source))


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.find_spec']"/>
# 여러 설계 문서 파일 이름 중에서 지금 다루는 slug 에 정확히 맞는 파일을 찾아 주는 함수다.
# 쓰는 것: runner.run_mode2.SPEC_FILENAME_RE · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_find_spec_does_not_match_a_partial_slug, runner.test_run_mode2.test_find_spec_returns_nothing_for_an_unknown_slug, runner.test_run_mode2.test_find_spec_returns_the_date_from_the_filename
def find_spec(filenames: Iterable[str], slug: str,
              doc_dir: str = "specs") -> dict[str, str] | None:
    """한 자리의 파일 목록에서 이 slug 의 원본 문서를 찾는다. 없으면 `None`.

    자리마다 파일명 관례가 다르므로 어느 자리인지를 받는다(`DOC_DIRS`).
    안 주면 `specs` 다 — 옛 호출을 깨지 않기 위해서다.

    **부분 문자열로 맞추지 않는다.** `load-reduction` 이 `llm-load-reduction` 을 물면
    엉뚱한 문서를 원본으로 삼아 결정 표 전체가 다른 계획의 것이 된다.
    """
    pattern = dict(DOC_DIRS).get(doc_dir)
    if pattern is None:
        return None
    for name in filenames:
        m = pattern.match(name)
        if m and m.group(2) == slug:
            return {"file": name, "date": m.group(1), "slug": slug, "dir": doc_dir}
    return None


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.script_argv']"/>
# 기계 단계 하나(node 로 실행하는 viz/*.mjs 스크립트)를 부르기 위한 명령줄 인자 목록을 만들어 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode1.test_every_runner_script_path_actually_exists, runner.test_run_mode2.test_only_init_takes_the_slug_on_the_command_line, runner.test_run_mode2.test_script_argv_points_at_the_renderer_scripts
# ── 3. 기계 단계의 명령줄 ────────────────────────────────────────────────
def script_argv(root: str, stage: str, slug: str) -> list[str]:
    """`viz/<단계>.py` 하나를 부른다.

    **slug 를 받는 것은 `init` 뿐이다.** `build`·`check` 는 `cwd` 로 대상을 알기 때문에
    인자를 주면 오해한다.
    """
    argv = [sys.executable, os.path.join(root, "viz", stage + ".py")]
    if stage == "init":
        argv.append(slug)
    return argv


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.agent_prompt']"/>
# 설계 검토 보고서를 쓰는 LLM 에이전트에게 줄 지시문 전체를 만드는 함수다.
# 쓰는 것: runner.run_mode2.report_dir · 쓰이는 곳: runner.run_mode2.run_agent, runner.test_run_mode2._prompt
# ── 4. 에이전트 프롬프트 — 검사가 잡아주지 않는 규율은 `runner/prompts/agent.md` 에 있다 ──
def agent_prompt(project: str, slug: str, spec_file: str, root: str,
                 terms_json: str | None = None, doc_dir: str = "specs",
                 evidence: Sequence[str] = (), manifest: str = "",
                 stale: Sequence[str] = (), uncommitted: bool = False) -> str:
    """원고를 쓰는 한 세션이 할 일 전부.

    글은 `runner/prompts/agent.md` 의 `main` 절이다. 용어집 재료 절은 `terms_json` 이 있을 때만 실린다(`{% if %}`).
    Mode 1 실측 자료 절은 `evidence`(봉인된 파일 경로) 가 비지 않았을 때만 실린다 — `manifest` 는 봉인 목록 파일의 경로,
    `stale` 은 봉인 뒤 움직인 소스(`바뀜 …` 꼴), `uncommitted` 는 봉인이 커밋되지 않았다는 뜻이고 둘은 그 절 안의 덧붙임이다.
    **그 글이 기계 검사가 잡는 것과 잡지 못하는 것을 나눠 적는다.** `<script>` 수와 링크
    무결성은 `check` 가 잡지만, 판정을 LLM Model이 채웠는지 · D축 필드를 넣었는지는
    아무도 잡아주지 않는다.

    `doc_dir` 는 원본이 사는 자리(`specs` 또는 `plans`)다. **프롬프트에 박으면 안 된다** —
    LLM Model이 없는 경로를 열어 보고 막힌다.
    """
    folder = report_dir(project, slug, doc_dir)
    return AgentStage.load_prompt("agent#main", project=project, spec_file=spec_file, folder=folder,
                                  root=root, terms_json=terms_json, doc_dir=doc_dir,
                                  evidence=list(evidence), manifest=manifest, stale=list(stale),
                                  uncommitted=uncommitted)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.run_agent']"/>
# 설계 검토 보고서를 실제로 작성하는 LLM 세션(claude -p)을 한 번 불러오는 함수다.
# 쓰는 것: runner.run_mode2.agent_prompt · 쓰이는 곳: runner.run_mode2.main
# ── 5. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
def run_agent(model: str, project: str, slug: str, spec_file: str, root: str,
              terms_json: str | None = None,
              timeout: float | None = None,
              doc_dir: str = "specs",
              evidence: Sequence[str] = (), manifest: str = "",
              stale: Sequence[str] = (), uncommitted: bool = False) -> tuple[int, M.AgentResult | None]:
    """`claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`.

    `--add-dir` 로 프로젝트와 도구 저장소를 둘 다 열어 준다 — 한쪽만 주면 LLM Model이
    설계 문서나 컴포넌트 규약 중 하나를 못 본다.
    """
    argv = claude_argv(model=model, repo=project, extra_dirs=[root])
    prompt = agent_prompt(project, slug, spec_file, root, terms_json, doc_dir,
                          evidence=evidence, manifest=manifest, stale=stale, uncommitted=uncommitted)
    with Heartbeat("agent"):
        p = subprocess.run(argv, input=prompt, cwd=project,
                           capture_output=True, text=True, timeout=timeout)
    try:
        return p.returncode, M.parse_result(p.stdout)
    except msgspec.DecodeError as e:
        print("결과 JSON 이 꼴에 안 맞는다 — %s" % e, file=sys.stderr)
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print(tail, file=sys.stderr)
        return p.returncode, None


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.run_machine']"/>
# init 을 제외한 기계 단계(build, check) 하나를 정해진 작업 폴더에서 실제로 실행하는 함수다.
# 쓰는 것: runner.run_mode1.Heartbeat · 쓰이는 곳: 없음
def run_machine(argv: Sequence[str], label: str, cwd: str) -> int:
    """기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다."""
    with Heartbeat(label, every=60.0):
        p = subprocess.run(argv, cwd=cwd)
    return p.returncode


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2._read']"/>
# 파일 하나를 열어 그 안의 글자를 통째로 읽어 오는 작은 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def _read(path: str) -> str | None:
    """파일을 읽어 문자열로. 없으면 `None` — 순수 함수에 존재 여부를 떠넘기지 않는다."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


EVIDENCE = os.path.join(ROOT, "machine", "evidence.py")
EVIDENCE_NEED = "terms-db,wiki"


class SealedEvidence(TypedDict):
    """`machine/evidence.py --list` 가 stdout 에 내는 JSON 중 여기서 읽는 칸. 나머지 칸은 버린다."""
    manifest: str
    artifacts: list[str]
    stale: list[str]
    uncommitted: bool


def no_seal() -> SealedEvidence:
    """봉인을 쓰지 않는 값. 근거 절이 프롬프트에 실리지 않는다."""
    return {"manifest": "", "artifacts": [], "stale": [], "uncommitted": False}


def read_seal(project: str) -> SealedEvidence:
    """프로젝트가 든 저장소에 봉인된 Mode 1 산출물을 읽는다. 상태 한 줄을 찍고, 못 읽으면 `no_seal()` 이다.

    `machine/evidence.py` 를 자식 프로세스로 두 번 부른다 — `--status`(한 줄) 와 `--list`(JSON). 봉인이 없거나 깨졌거나
    꼴이 안 맞아도 멈추지 않는다. 구조 문제의 이유는 `--list` 의 stderr 가 그대로 터미널에 흘러 보인다.
    """
    try:
        top = subprocess.run(["git", "-C", project, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True).stdout.strip() or project
    except OSError:
        top = project
    got = subprocess.run([sys.executable, EVIDENCE, top, "--need", EVIDENCE_NEED, "--status"],
                         stdout=subprocess.PIPE, text=True)
    print(got.stdout.strip() or "Mode 1 봉인 — 상태를 알 수 없다")
    listed = subprocess.run([sys.executable, EVIDENCE, top, "--need", EVIDENCE_NEED, "--list"],
                            stdout=subprocess.PIPE, text=True)
    if listed.returncode != 0:
        return no_seal()
    try:
        return msgspec.json.decode(listed.stdout, type=SealedEvidence)
    except msgspec.DecodeError as e:
        print("Mode 1 봉인 목록이 꼴에 안 맞는다 — %s" % e, file=sys.stderr)
        return no_seal()


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.main']"/>
# Mode 2(설계 검토 보고서) 파이프라인의 진입점. 스펙 문서를 찾아서 보고서를 만드는 네 단계(init→agent→build→check)를 순서대로 돌린다.
# 쓰는 것: runner.run_mode2.find_spec, runner.run_mode2.report_dir, runner.run_mode2.manuscript_is_written, runner.run_mode2.plan_stages, runner.run_mode2.stage_cwd (+7) · 쓰이는 곳: 없음

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
    evidence: tuple[str, ...] = ()
    manifest: str = ""
    stale: tuple[str, ...] = ()
    uncommitted: bool = False


# Mode 2 의 산출물은 셋 다 JSON 이 아니다 — TypeScript 소스와 HTML 이다.
# 그래서 `check` 가 없고 존재만 본다.
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
    prompt_dir = os.path.join(ROOT, "runner", "prompts")
    prompt_names = ("agent#main",)

    def prompt(self, ctx: Mode2Context) -> str:
        return agent_prompt(ctx.project, ctx.slug, ctx.spec_file, ctx.root,
                            ctx.terms_json, ctx.doc_dir, evidence=ctx.evidence, manifest=ctx.manifest,
                            stale=ctx.stale, uncommitted=ctx.uncommitted)

    def repo(self, ctx: Mode2Context) -> str:
        return ctx.project

    def harvest(self, ctx: Mode2Context, got: Sequence[P.JobResult],
                rnd: int) -> P.Outcome:
        """LLM Model이 낸 글을 화면에 흘린 뒤 기본 거두기를 그대로 쓴다."""
        for _, _, _, result in got:
            text = result.get("result", "") if result else ""
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


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mode 2 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="specs/ 나 plans/ 가 있는 폴더 (저장소 뿌리가 아닐 수 있다)")
    ap.add_argument("slug",
                    help="보고서 slug. specs/YYYY-MM-DD-<slug>-design.md 또는 "
                         "plans/YYYY-MM-DD-<slug>.md 가 있어야 한다")
    ap.add_argument("--model", default=CONFIG["models"]["mode2_agent"],
                    help="에이전트가 쓸 LLM Model (기본: %(default)s)")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
    a = ap.parse_args(argv)

    project = os.path.abspath(os.path.expanduser(a.project))
    present = [d for d, _ in DOC_DIRS if os.path.isdir(os.path.join(project, d))]
    if not present:
        print("에러 — specs/ 도 plans/ 도 없다: %s" % project, file=sys.stderr)
        print("  <프로젝트> 는 저장소 뿌리가 아니라 그 둘 중 하나가 있는 폴더다.", file=sys.stderr)
        return 1

    # 두 자리를 순서대로 뒤진다. 먼저 원본 문서를, 못 찾으면 이미 작업 중인 원고를 찾는다 —
    # 문서 이름이 바뀌어도 진행 중인 보고서를 막지 않기 위해서다.
    spec = None
    for d in present:
        spec = find_spec(sorted(os.listdir(os.path.join(project, d))), a.slug, d)
        if spec:
            break
    doc_dir = spec["dir"] if spec else next(
        (d for d in present if os.path.exists(os.path.join(project, d, a.slug, "data.ts"))),
        present[0])

    folder = report_dir(project, a.slug, doc_dir)
    data_src = _read(os.path.join(folder, "data.ts"))
    report_src = _read(os.path.join(folder, "report.tsx"))
    has_manuscript = manuscript_is_written(data_src, report_src)

    # 원본 문서가 없어도 이미 작업 중인 원고가 있으면 막지 않는다.
    if spec is None and data_src is None:
        print("에러 — 원본 문서를 찾지 못했다: %s/specs/*-%s-design.md 또는 %s/plans/*-%s.md"
              % (project, a.slug, project, a.slug), file=sys.stderr)
        return 1
    spec_file = spec["file"] if spec else "(없음 — 작업 중인 원고를 이어 쓴다)"

    terms_json: str | None = os.path.join(folder, "terms.json")
    terms_json = terms_json if os.path.exists(terms_json) else None

    # `--dry-run` 은 자식 프로세스를 띄우지 않는다 — 봉인 판정도 부르지 않는다.
    sealed = no_seal() if a.dry_run else read_seal(project)

    ctx = Mode2Context(root=ROOT, model=a.model, timeout=a.timeout,
                       project=project, slug=a.slug, folder=folder,
                       spec_file=spec_file, doc_dir=doc_dir, terms_json=terms_json,
                       evidence=tuple(sealed["artifacts"]), manifest=sealed["manifest"],
                       stale=tuple(sealed["stale"]), uncommitted=sealed["uncommitted"])
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
    if a.dry_run:
        seal_note = "확인 안 함 — --dry-run"
    elif sealed["artifacts"]:
        seal_note = "%d건 (낡음 %d)" % (len(sealed["artifacts"]), len(sealed["stale"]))
    else:
        seal_note = "없음 — 근거 자리 없이 진행"
    print("이미 있는 것 — 뼈대 %s · 채워진 원고 %s · 용어집 재료 %s · Mode 1 자료 %s"
          % (data_src is not None, has_manuscript, bool(terms_json), seal_note))
    if a.dry_run:
        for s_name in graph.order:
            print("  %-6s cwd=%s" % (s_name, stage_cwd(s_name, project, folder)))
        print(graph.render())
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode2Context]().run(graph, ctx)

    out_html = os.path.join(folder, "out", "report.html")
    if any(r["stage"] == "build" and r["ok"] for r in rows) and os.path.exists(out_html):
        print("out/report.html — {:,} 바이트".format(os.path.getsize(out_html)))

    print("\n" + "=" * 72)
    print("Mode 2 측정 — 전체 %s" % hms(time.monotonic() - t_all))
    print("=" * 72)
    print(format_report(rows))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"project": project, "slug": a.slug, "model": a.model,
                       "stages": rows, "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": time.monotonic() - t_all},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
