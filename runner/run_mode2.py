#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_mode2.py']"/>
# 설계 검토 보고서를 짓는 흐름을 한 번에 돌리며 시간과 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# Mode 2 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: run_mode1 · 쓰이는 곳: 없음
"""Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

재는 코드는 `run_mode1.py` 의 것을 그대로 import 해 쓴다 — 여기에 사본이 없다.

## 네 단계 — LLM 은 그중 **하나**뿐이다

    init ──▶ agent ──▶ build ──▶ check
    기계      LLM 1개    기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `init`  | 뼈대 `data.ts` · `report.tsx` 를 만든다. 이미 있으면 스스로 건너뛴다 | `viz/init.mjs` |
| `agent` | **원고를 쓴다** — 설계 문서를 읽어 결정 표 · 서사 · 확신도 배지를 채운다 | `claude -p` 1회 |
| `build` | esbuild 트랜스파일 → React 정적 렌더 → 한 장짜리 HTML 조립 | `viz/build.mjs` |
| `check` | `<script>` 수 · `tsc --noEmit` · 링크 무결성 · 용어집 대조 · builderVersion | `viz/check.mjs` |

## 이 파이프라인의 LLM 자리는 **원고 쓰기** 하나다

`init` 은 스켈레톤만 만든다. 결정 표 · 서사 · 확신도 배지 · 옵션표를 채우는 절차의
정본은 `spec-review-dashboard` 스킬이다. **판정(수용/보류/번복)은 절대 모형이 하지
않는다** — `VerdictFooter` 는 비워서 낸다.

## 함정

- **명령마다 작업 디렉토리가 다르다.** `init` 은 `specs/` 가 있는 프로젝트 뿌리에서,
  `build` 와 `check` 는 보고서 폴더(`specs/<slug>/`)에서 돈다. 여기서 틀리면 오류 없이
  **조용히 엉뚱한 곳에 파일이 생긴다**(`stage_cwd`).
- **`claude` 는 막혀도 종료 코드 0 을 낼 수 있다.** `is_error` 와 `subtype` 을 봐야 한다.
  판정 코드는 `run_mode1.agent_verdict` 를 그대로 쓴다.
- **재는 코드를 새로 짜지 않는다.** 토큰 세기·합계·표 그리기는 `run_mode1` 에 있다.
  각자 세면 같은 이름의 숫자가 두 실행기에서 서로 다른 뜻을 갖는다.
- **Mode 1.5 의 `terms.json` 을 기계로 병합하지 않는다.** 있으면 프롬프트에 **알려 주기만**
  하고, 옮겨 적는 것은 모형의 일이다.

## 쓰는 법

    .venv/bin/python runner/run_mode2.py <프로젝트> <slug> [--model <모형 ID>]
                                            [--only init,build] [--skip agent]
                                            [--json 측정.json] [--dry-run]

`<프로젝트>` 는 **`specs/` 가 있는 폴더**다. 저장소 뿌리가 아닐 수 있다.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_mode1 as M  # noqa: E402

# 재는 코드(`hms` · `Heartbeat` · `normalize_usage` · `format_report` …)의 원본은
# `run_mode1.py` 하나뿐이다. 여기에는 사본이 없다.
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

# 설계 문서 파일명 규칙. `viz/init.mjs` 의 SPEC_FILENAME_RE 와 같은 규칙이다.
SPEC_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)-design\.md$")


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.report_dir']"/>
# 보고서 파일들이 들어 있는 폴더의 경로를 만들어 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode2.agent_prompt, runner.run_mode2.main, runner.test_run_mode2.test_report_dir_is_specs_slash_slug
# ── 1. 자리 잡기 — 어디에서 무엇을 도는가 ────────────────────────────────
def report_dir(project: str, slug: str) -> str:
    """보고서가 사는 폴더. 프로젝트 뿌리 아래 `specs/<slug>/` 다."""
    return os.path.join(project, "specs", slug)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.stage_cwd']"/>
# 네 단계(init/agent/build/check) 중 하나를 어느 작업 디렉토리에서 실행해야 하는지 정해 주는 함수다.
# 쓰는 것: runner.run_mode2.STAGES, runner.run_mode2.PROJECT_STAGES · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_build_and_check_run_inside_the_report_folder, runner.test_run_mode2.test_init_runs_at_the_project_root, runner.test_run_mode2.test_stage_cwd_rejects_an_unknown_stage, runner.test_run_mode2.test_the_agent_also_runs_at_the_project_root
def stage_cwd(stage: str, project: str, report_dir: str) -> str:
    """단계 하나를 어느 폴더에서 돌릴지 답한다. **여기서 틀리면 오류 없이 엉뚱한 곳에 쓴다.**

    `init.mjs` 는 `join(cwd, "specs")` 를 보므로 프로젝트 뿌리가 필요하고,
    `build.mjs`·`check.mjs` 는 `cwd` 에서 `data.ts`·`report.tsx` 를 읽으므로 보고서
    폴더가 필요하다. 모형(`agent`)은 둘 다 봐야 해서 뿌리에 세운다.
    """
    if stage not in STAGES:
        raise ValueError("모르는 단계: %s (있는 것: %s)" % (stage, ", ".join(STAGES)))
    return project if stage in PROJECT_STAGES else report_dir


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.is_agent_stage']"/>
# 이 단계가 LLM(큰 언어 모형)을 실제로 부르는 자리인지 참/거짓으로 답해 주는 함수다.
# 쓰는 것: runner.run_mode2.AGENT_STAGES · 쓰이는 곳: runner.test_run_mode2.test_only_one_stage_calls_the_model
def is_agent_stage(stage: str) -> bool:
    """이 단계가 큰 언어 모형을 부르는 자리인지 답한다. 토큰이 잡히는 자리는 여기뿐이다."""
    return stage in AGENT_STAGES


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.plan_stages']"/>
# init, agent, build, check 네 단계 중 이번에 실제로 돌릴 단계들만 골라 순서대로 나열해 주는 함수다. 파일이나 네트워크를 건드리지 않고 입력값만으로 답을 정한다.
# 쓰는 것: runner.run_mode2.STAGES · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode2.test_only_one_stage_calls_the_model, runner.test_run_mode2.test_plan_keeps_init_even_when_the_manuscript_exists, runner.test_run_mode2.test_plan_only_and_skip_are_honoured, runner.test_run_mode2.test_plan_rejects_an_unknown_stage (+2)
# ── 2. 단계 고르기 (파일 시스템을 보지 않는 순수 함수) ────────────────────
def plan_stages(has_manuscript: bool, only: Iterable[str] | None = None,
                skip: Iterable[str] | None = None) -> list[str]:
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다.

    `init` 은 늘 남긴다 — 이미 `data.ts` 가 있으면 건너뛸지를 `init.mjs` 자신이
    정한다(멱등 경로에서 exit 0). 여기서 미리 빼면 그 판단을 뺏는 것이다.

    `agent` 만은 **원고가 이미 채워졌을 때** 뺀다 — 사람이 쓴 글을 모형이 덮어쓰면
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
def find_spec(filenames: Iterable[str], slug: str) -> dict[str, str] | None:
    """설계 문서 파일 목록에서 이 slug 의 것을 찾는다. 없으면 `None`.

    **부분 문자열로 맞추지 않는다.** `load-reduction` 이 `llm-load-reduction` 을 물면
    엉뚱한 문서를 원본으로 삼아 결정 표 전체가 다른 계획의 것이 된다.
    """
    for name in filenames:
        m = SPEC_FILENAME_RE.match(name)
        if m and m.group(2) == slug:
            return {"file": name, "date": m.group(1), "slug": slug}
    return None


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.script_argv']"/>
# 기계 단계 하나(node 로 실행하는 viz/*.mjs 스크립트)를 부르기 위한 명령줄 인자 목록을 만들어 주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.run_mode2.main, runner.test_run_mode1.test_every_runner_script_path_actually_exists, runner.test_run_mode2.test_only_init_takes_the_slug_on_the_command_line, runner.test_run_mode2.test_script_argv_points_at_the_renderer_scripts
# ── 3. 기계 단계의 명령줄 ────────────────────────────────────────────────
def script_argv(root: str, stage: str, slug: str) -> list[str]:
    """`viz/<단계>.mjs` 하나를 부른다. node 는 PATH 에서 찾는다.

    **slug 를 받는 것은 `init` 뿐이다.** `build`·`check` 는 `cwd` 로 대상을 알기 때문에
    인자를 주면 오해한다.
    """
    argv = ["node", os.path.join(root, "viz", stage + ".mjs")]
    if stage == "init":
        argv.append(slug)
    return argv


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.agent_prompt']"/>
# 설계 검토 보고서를 쓰는 LLM 에이전트에게 줄 지시문 전체를 만드는 함수다.
# 쓰는 것: runner.run_mode2.report_dir · 쓰이는 곳: runner.run_mode2.run_agent, runner.test_run_mode2._prompt
# ── 4. 에이전트 프롬프트 — 검사가 잡아주지 않는 규율을 여기서 말한다 ──────
def agent_prompt(project: str, slug: str, spec_file: str, root: str,
                 terms_json: str | None = None) -> str:
    """원고를 쓰는 한 세션이 할 일 전부.

    **기계 검사가 잡는 것과 잡지 못하는 것을 나눠 적는다.** `<script>` 수와 링크
    무결성은 `check` 가 잡지만, 판정을 모형이 채웠는지 · D축 필드를 넣었는지는
    아무도 잡아주지 않는다.
    """
    folder = report_dir(project, slug)
    terms_block = ""
    if terms_json:
        terms_block = """
## 용어집 재료가 이미 있다 — **옮겨 적되 기계로 붙여넣지 마라**

  {terms_json}

Mode 1.5(용어 이해도 점검)가 낸 파일이다. `{{ "용어": {{ TermMeans, UserMentalValue }} }}` 를
`data.ts` 의 `terms` 배열 꼴 `{{ id, label, short, kind, mental }}` 로 **손으로 옮긴다.**
옮기면서 뜻을 이 보고서의 문맥에 맞게 다듬는 것이 이 단계의 일이다. 통째로 복사하면
독자가 읽을 수 없는 정의가 그대로 실린다.
""".format(terms_json=terms_json)

    return """\
너는 report-builder 의 **Mode 2 에이전트**다. 설계 문서 하나를 읽어 **사용자가 수용 판정을
내리기 좋은 계기판**으로 압축한다. 사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는
순간 막힌다. 막히면 진행하지 말고 무엇이 없어서 막혔는지 적고 끝낸다.

프로젝트     {project}       (여기에 specs/ 가 있다)
설계 문서    {project}/specs/{spec_file}
보고서 폴더  {folder}        (여기의 data.ts 와 report.tsx **둘만** 고친다)
도구 저장소  {root}          (report-builder. 규약과 컴포넌트가 여기 있다)

## 절차 — 정본은 스킬이다

`spec-review-dashboard` 스킬을 Skill 도구로 불러 **그 절차대로** 한다. 블록 순서 ·
컴포넌트 17개의 props · 확신도 표기가 전부 거기 적혀 있다. 뼈대(`data.ts` · `report.tsx`)는
이미 만들어져 있다 — `report-spec init` 이 방금 돌았다. **다시 만들지 말고 채운다.**

기계 단계(`report-spec build` · `report-spec check`)는 **네가 돌리지 않는다.** 이 실행기가
네가 끝난 뒤에 돌리며 시간을 잰다. 너는 원고만 쓴다.

## 반드시 지킬 것 — 기계가 잡는 것

- **`<script>` 태그는 1개를 넘으면 안 된다.** 용어집(`terms`)이 없으면 0개, 있으면
  1개(용어 그래프 런타임)다. 산출물에 스크립트를 직접 쓰지 마라 — 예산이 이미 찼다.
- **결정 절 제목은 `<Section title="D0 …">` 처럼 `D<숫자>` 로 연다.** `data.ts` 의
  `id` 와 1:1 로 대조된다. 어긋나면 검사가 "절이 없는 결정" 으로 떨어뜨린다.
- **컴포넌트 17개 밖으로 나가지 마라.** 인라인 `style` · 신규 CSS 클래스 금지.
  반복 요소를 발견해도 그 자리에서 컴포넌트를 만들지 말고 보고서 끝에
  `## 컴포넌트 후보` 절로 **반복 횟수와 함께** 적기만 한다.

## 반드시 지킬 것 — 기계가 **잡지 못하는** 것

- **판정은 절대 네가 하지 않는다.** `VerdictFooter` 는 **비워서** 낸다. 수용 · 보류 ·
  번복은 언제나 사용자 몫이다. 요약란에 "수용 권고" 같은 말도 쓰지 마라.
- **D축(결정 불확실성) 필드를 `data.ts` 에 넣지 마라.** D축은 평가 없이 보류 상태다.
  D 점수 · D 컬럼 · 결정 행 좌측 테두리색을 만들지 마라.
- **상태 태그는 한국어가 정본** — `[제안됨]` · `[잠정됨]` · `[검증됨]`.
  `proposed` · `accepted` 를 화면 문구로 쓰지 않는다.
- **결정 로그 표는 4컬럼이 정본** — `| # | 결정 | 상태 | 신뢰도 |`.
- **확신도는 🔵/🟡/💭 + 정수 또는 "실측"** 이고 `tier` 는 `green|amber|red` 다.
  🔵 는 **이번 세션에서 읽은 `파일:줄` 또는 실제로 돌린 명령의 출력**만 인정한다.
- **설계 문서에 없는 결정을 지어내지 마라.** 원문에서 읽은 것만 옮긴다. 네가 보탠
  항목이 있으면 행마다 `미검토 — 이 보고서가 추가` 처럼 출처를 박는다.
- **산문 문단 금지.** 설명은 설계 문서에 이미 있다. 계기판이지 축약본이 아니다.
- **객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.** 섞일 것 같으면 `EvidenceNote` 로 가른다.
- **"검증됨" · "입증" · "증명" 이라고 쓰지 마라.**
{terms_block}
## 규율

- **커밋하지 마라.** `git add` · `git commit` 금지.
- 쓰는 파일은 `{folder}/data.ts` 와 `{folder}/report.tsx` **둘뿐**이다.
  설계 문서와 소스는 읽기만 한다.
- 주석과 문서는 **한국어**. 약어를 피하고 메커니즘(원리)을 먼저 쓴다.
- 읽는 사람은 배경 지식이 없다고 가정한다(객체지향을 갓 배운 대학 1학년 눈높이).

끝나면 결정 몇 건 · 옵션표 몇 개 · 용어 몇 개를 넣었는지 한 표로 보고한다.
""".format(project=project, slug=slug, spec_file=spec_file, folder=folder,
           root=root, terms_block=terms_block)


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.run_agent']"/>
# 설계 검토 보고서를 실제로 작성하는 LLM 세션(claude -p)을 한 번 불러오는 함수다.
# 쓰는 것: runner.run_mode2.agent_prompt · 쓰이는 곳: runner.run_mode2.main
# ── 5. 실제로 돌리기 (부수효과는 이 아래에만 있다) ──────────────────────
def run_agent(model: str, project: str, slug: str, spec_file: str, root: str,
              terms_json: str | None = None,
              timeout: float | None = None) -> tuple[int, M.AgentResult | None]:
    """`claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`.

    `--add-dir` 로 프로젝트와 도구 저장소를 둘 다 열어 준다 — 한쪽만 주면 모형이
    설계 문서나 컴포넌트 규약 중 하나를 못 본다.
    """
    argv = claude_argv(model=model, repo=project, extra_dirs=[root])
    prompt = agent_prompt(project, slug, spec_file, root, terms_json)
    with Heartbeat("agent"):
        p = subprocess.run(argv, input=prompt, cwd=project,
                           capture_output=True, text=True, timeout=timeout)
    try:
        return p.returncode, json.loads(p.stdout)
    except (ValueError, TypeError):
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


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode2.main']"/>
# Mode 2(설계 검토 보고서) 파이프라인의 진입점. 스펙 문서를 찾아서 보고서를 만드는 네 단계(init→agent→build→check)를 순서대로 돌린다.
# 쓰는 것: runner.run_mode2.find_spec, runner.run_mode2.report_dir, runner.run_mode2.manuscript_is_written, runner.run_mode2.plan_stages, runner.run_mode2.stage_cwd (+7) · 쓰이는 곳: 없음
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mode 2 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="specs/ 가 있는 폴더 (저장소 뿌리가 아닐 수 있다)")
    ap.add_argument("slug", help="보고서 slug. specs/YYYY-MM-DD-<slug>-design.md 가 있어야 한다")
    ap.add_argument("--model", default="opus", help="에이전트가 쓸 모형 (기본: opus)")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
    a = ap.parse_args(argv)

    project = os.path.abspath(os.path.expanduser(a.project))
    specs_dir = os.path.join(project, "specs")
    if not os.path.isdir(specs_dir):
        print("에러 — specs/ 가 없다: %s" % specs_dir, file=sys.stderr)
        print("  <프로젝트> 는 저장소 뿌리가 아니라 specs/ 가 있는 폴더다.", file=sys.stderr)
        return 1

    spec = find_spec(sorted(os.listdir(specs_dir)), a.slug)
    folder = report_dir(project, a.slug)
    data_src = _read(os.path.join(folder, "data.ts"))
    report_src = _read(os.path.join(folder, "report.tsx"))
    has_manuscript = manuscript_is_written(data_src, report_src)

    # 설계 문서가 없어도 이미 작업 중인 원고가 있으면 막지 않는다.
    if spec is None and data_src is None:
        print("에러 — 설계 문서를 찾지 못했다: %s/*-%s-design.md" % (specs_dir, a.slug),
              file=sys.stderr)
        return 1
    spec_file = spec["file"] if spec else "(없음 — 작업 중인 원고를 이어 쓴다)"

    terms_json: str | None = os.path.join(folder, "terms.json")
    terms_json = terms_json if os.path.exists(terms_json) else None

    try:
        stages = plan_stages(
            has_manuscript=has_manuscript,
            only=a.only.split(",") if a.only else None,
            skip=a.skip.split(",") if a.skip else None)
    except ValueError as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    print("프로젝트 %s" % project)
    print("보고서   %s" % folder)
    print("설계문서 %s" % spec_file)
    print("모형 %s · 단계 %s" % (a.model, " -> ".join(stages) or "(없음)"))
    print("이미 있는 것 — 뼈대 %s · 채워진 원고 %s · 용어집 재료 %s"
          % (data_src is not None, has_manuscript, bool(terms_json)))
    if a.dry_run:
        for s in stages:
            print("  %-6s cwd=%s" % (s, stage_cwd(s, project, folder)))
        return 0

    rows: list[M.StageRow] = []
    t_all = time.monotonic()
    for stage in stages:
        print("\n── %s ──────────────────────────────" % stage, flush=True)
        cwd = stage_cwd(stage, project, folder)
        t0 = time.monotonic()
        if stage == "agent":
            rc, result = run_agent(a.model, project, a.slug, spec_file, ROOT,
                                   terms_json=terms_json, timeout=a.timeout)
            ok, why = agent_verdict(rc, result)
            usage = normalize_usage(result)
            if result and result.get("result"):
                print(result["result"])
        else:
            if not os.path.isdir(cwd):
                rc, ok, why = 1, False, "작업 디렉토리가 없다: %s" % cwd
            else:
                rc = run_machine(script_argv(ROOT, stage, a.slug), stage, cwd)
                ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
            usage = normalize_usage(None)
        seconds = time.monotonic() - t0
        rows.append({"stage": stage, "seconds": seconds, "usage": usage,
                     "ok": ok, "why": why})
        print("%s — %s (%s)" % (stage, "성공" if ok else "실패", hms(seconds)), flush=True)
        if stage == "build" and ok:
            out_html = os.path.join(folder, "out", "report.html")
            if os.path.exists(out_html):
                print("out/report.html — {:,} 바이트".format(os.path.getsize(out_html)))
        if not ok:
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

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
