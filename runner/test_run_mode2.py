# <include file="machine/comments.xml" path="//term[@id='test_run_mode2.py']"/>
# Mode 2 실행기의 회귀 시험 — 작업 디렉토리·단계 고르기·원고 판별을 본다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 2 실행기의 회귀 시험.

여기서 보는 다섯 자리 — 작업 디렉토리(`init`·`agent` 는 프로젝트 뿌리, `build`·`check`
는 보고서 폴더. 틀려도 오류가 나지 않는다) · 단계 고르기 · 원고 판별(뼈대와 채워진
원고를 글자로 가른다) · 프롬프트 규율(판정은 언제나 사람 몫) · 재는 코드가 Mode 1
것을 그대로 쓰는가.

  .venv/bin/python -m pytest runner/test_run_mode2.py -q
"""
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M  # noqa: E402
import pipeline as P  # noqa: E402
import run_mode2 as R  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_init_runs_at_the_project_root']"/>
# init 단계가 프로젝트 뿌리 폴더에서 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
# ── 1. 작업 디렉토리 — Mode 2 의 가장 조용한 함정 ──────────────────────────
def test_init_runs_at_the_project_root():
    """`init` 은 `specs/` 가 있는 프로젝트 뿌리에서 돈다. `init.py` 가 `join(cwd, "specs")` 를 본다."""
    assert R.stage_cwd("init", project="/프로젝트", report_dir="/프로젝트/specs/붙임") == "/프로젝트"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_agent_also_runs_at_the_project_root']"/>
# 원고를 쓰는 LLM Model(에이전트) 단계도 프로젝트 뿌리에서 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
def test_the_agent_also_runs_at_the_project_root():
    """LLM Model은 설계 문서(`specs/*-design.md`)와 보고서 폴더를 **둘 다** 봐야 한다. 뿌리에 세운다."""
    assert R.stage_cwd("agent", project="/프로젝트", report_dir="/프로젝트/specs/붙임") == "/프로젝트"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_build_and_check_run_inside_the_report_folder']"/>
# build 와 check 단계는 보고서 폴더 안에서 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
def test_build_and_check_run_inside_the_report_folder():
    """`build`·`check` 는 보고서 폴더를 `cwd` 로 본다 — 거기서 data.ts 와 report.tsx 를 읽는다."""
    for stage in ("build", "check"):
        assert R.stage_cwd(stage, project="/프로젝트",
                           report_dir="/프로젝트/specs/붙임") == "/프로젝트/specs/붙임"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_stage_cwd_rejects_an_unknown_stage']"/>
# 존재하지 않는 단계 이름을 주면 오류가 나야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
def test_stage_cwd_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        R.stage_cwd("없는단계", project="/프로젝트", report_dir="/프로젝트/specs/붙임")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_report_dir_is_specs_slash_slug']"/>
# 보고서 폴더 경로가 "프로젝트/specs/슬러그" 꼴로 만들어지는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.report_dir · 쓰이는 곳: 없음
def test_report_dir_is_specs_slash_slug():
    assert R.report_dir("/프로젝트", "붙임") == os.path.join("/프로젝트", "specs", "붙임")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_runs_all_four_stages_on_an_empty_report']"/>
# 아직 아무것도 쓰이지 않은 보고서라면 네 단계를 전부 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
# ── 2. 단계 고르기 — 순수 함수라 파일 시스템을 보지 않는다 ────────────────
def test_plan_runs_all_four_stages_on_an_empty_report():
    assert R.plan_stages(has_manuscript=False) == ["init", "agent", "build", "check"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_only_one_stage_calls_the_model']"/>
# 네 단계 중 LLM Model(LLM)을 부르는 자리는 agent 하나뿐이라는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages, runner.run_mode2.is_agent_stage · 쓰이는 곳: 없음
def test_only_one_stage_calls_the_model():
    """LLM Model을 부르는 자리는 **원고 쓰기 하나**다. 나머지 셋은 기계다."""
    stages = R.plan_stages(has_manuscript=False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["agent"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_skips_the_agent_when_the_manuscript_is_already_written']"/>
# 사람이 이미 원고를 다 썼다면 LLM Model을 다시 부르지 않아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_skips_the_agent_when_the_manuscript_is_already_written():
    """사람이 쓴 원고를 LLM Model이 덮어쓰면 안 된다. 이미 채워졌으면 굽기만 한다."""
    p = R.plan_stages(has_manuscript=True)
    assert "agent" not in p
    assert p == ["init", "build", "check"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_keeps_init_even_when_the_manuscript_exists']"/>
# 원고가 이미 있어도 init 단계는 항상 목록의 맨 앞에 남아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_keeps_init_even_when_the_manuscript_exists():
    """`init` 은 늘 부른다 — 건너뛸지는 `init.py` 자신이 정한다(data.ts 가 있으면 exit 0)."""
    assert R.plan_stages(has_manuscript=True)[0] == "init"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_only_and_skip_are_honoured']"/>
# plan_stages 가 only(이것만 돈다)와 skip(이것은 뺀다) 옵션을 실제로 반영하는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_only_and_skip_are_honoured():
    assert R.plan_stages(False, only=["build", "check"]) == ["build", "check"]
    assert "agent" not in R.plan_stages(False, skip=["agent"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_rejects_an_unknown_stage']"/>
# only 옵션에 존재하지 않는 단계 이름을 넣으면 오류가 나야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        R.plan_stages(False, only=["없는단계"])


# ── 3. 원고 판별 — 뼈대와 채워진 글을 글자로 가른다 ───────────────────────
SKELETON_DATA = '''import type { ReportData } from "report-builder/types";
export const data: ReportData = {
  builderVersion: "v1",
  slug: "붙임",
  decisions: [],
  terms: [],
};
'''
SKELETON_REPORT = '''import { Page, Section, DecisionTable, VerdictFooter } from "report-builder";
export default function Report() {
  return (<Page data={data}><Section title="결정 요약" /></Page>);
}
'''
FILLED_DATA = '''export const data: ReportData = {
  decisions: [{ id: "D0", title: "무엇을 한다", status: "제안됨" }],
};
'''
FILLED_REPORT = '''export default function Report() {
  return (<Page data={data}><Section title="D0 무엇을 한다" /></Page>);
}
'''


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_a_fresh_skeleton_is_not_a_manuscript']"/>
# init 이 방금 만든 빈 뼈대(decisions가 빈 배열)는 아직 원고가 아니라는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.manuscript_is_written · 쓰이는 곳: 없음
def test_a_fresh_skeleton_is_not_a_manuscript():
    """`decisions: []` 는 `init` 이 방금 만든 뼈대다. LLM Model을 불러야 한다."""
    assert R.manuscript_is_written(SKELETON_DATA, SKELETON_REPORT) is False


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_a_filled_data_and_report_is_a_manuscript']"/>
# 결정 내용과 본문 절이 실제로 채워진 원고는 원고로 인정돼야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.manuscript_is_written · 쓰이는 곳: 없음
def test_a_filled_data_and_report_is_a_manuscript():
    assert R.manuscript_is_written(FILLED_DATA, FILLED_REPORT) is True


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_decisions_without_matching_sections_is_not_a_manuscript']"/>
# 결정 데이터는 채워졌지만 보고서 본문에 그에 대응하는 절이 없으면 아직 원고가 아니라는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.manuscript_is_written · 쓰이는 곳: 없음
def test_decisions_without_matching_sections_is_not_a_manuscript():
    """결정은 있는데 본문 절이 없으면 반쯤 쓰다 만 것이다. 이어 쓰게 다시 부른다."""
    assert R.manuscript_is_written(FILLED_DATA, SKELETON_REPORT) is False


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_missing_files_are_not_a_manuscript']"/>
# data.ts 나 report.tsx 파일 자체가 없는 경우(None)에는 원고가 아니라고 판정해야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.manuscript_is_written · 쓰이는 곳: 없음
def test_missing_files_are_not_a_manuscript():
    assert R.manuscript_is_written(None, None) is False
    assert R.manuscript_is_written(FILLED_DATA, None) is False


# ── 4. 설계 문서 찾기 — slug 를 지어내지 않는다 ──────────────────────────
SPEC_FILES = [
    "2026-08-28-llm-load-reduction-design.md",
    "2026-08-29-mode-1-terms-db-first-design.md",
    "메모.md",
]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_find_spec_returns_the_date_from_the_filename']"/>
# 파일 이름 안의 날짜와 슬러그로 맞는 설계 문서를 찾아내는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.find_spec · 쓰이는 곳: 없음
def test_find_spec_returns_the_date_from_the_filename():
    got = R.find_spec(SPEC_FILES, "llm-load-reduction")
    assert got is not None
    assert got["date"] == "2026-08-28"
    assert got["file"] == "2026-08-28-llm-load-reduction-design.md"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_find_spec_returns_nothing_for_an_unknown_slug']"/>
# 목록에 없는 슬러그를 찾으면 아무것도 나오지 않아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.find_spec · 쓰이는 곳: 없음
def test_find_spec_returns_nothing_for_an_unknown_slug():
    assert R.find_spec(SPEC_FILES, "없는-슬러그") is None


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_find_spec_does_not_match_a_partial_slug']"/>
# 슬러그의 일부만 같은 부분 문자열로는 엉뚱한 설계 문서를 찾아내면 안 된다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.find_spec · 쓰이는 곳: 없음
def test_find_spec_does_not_match_a_partial_slug():
    """부분 문자열로 걸리면 엉뚱한 문서를 원본으로 삼는다."""
    assert R.find_spec(SPEC_FILES, "load-reduction") is None


# ── 4-2. 원본은 두 자리에 산다 — specs/ 와 plans/ ────────────────────────
PLAN_FILES = [
    "2026-08-30-symbol-resolution-survey.md",
    "2026-08-26-report-builder.md",
    "README.md",
]


def test_find_spec_reads_plans_without_the_design_suffix():
    """plans/ 는 `-design` 접미사가 없다. 계획서만 사는 자리라 가드가 필요 없다."""
    got = R.find_spec(PLAN_FILES, "symbol-resolution-survey", "plans")
    assert got is not None
    assert got["date"] == "2026-08-30"
    assert got["file"] == "2026-08-30-symbol-resolution-survey.md"
    assert got["dir"] == "plans"


def test_find_spec_keeps_the_suffix_guard_for_specs():
    """specs/ 에서는 접미사가 없으면 안 잡힌다 — 같은 폴더에 다른 산출물이 함께 산다."""
    assert R.find_spec(PLAN_FILES, "symbol-resolution-survey", "specs") is None


def test_find_spec_defaults_to_specs():
    """자리를 안 주면 specs 다 — 옛 호출을 깨지 않는다."""
    got = R.find_spec(SPEC_FILES, "llm-load-reduction")
    assert got is not None and got["dir"] == "specs"


def test_report_dir_sits_next_to_its_source_document():
    """보고서는 원본 옆에 산다. plans 문서의 보고서는 plans/<slug>/ 다."""
    assert R.report_dir("/프로젝트", "붙임", "plans") == os.path.join("/프로젝트", "plans", "붙임")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_script_argv_points_at_the_renderer_scripts']"/>
# 각 단계를 실제로 실행할 명령줄(argv)이 올바른 node 스크립트를 가리키는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.script_argv · 쓰이는 곳: 없음
# ── 5. 명령줄 — init 만 slug 를 받는다 ───────────────────────────────────
def test_script_argv_points_at_the_renderer_scripts():
    argv = R.script_argv("/도구/뿌리", "build", slug="붙임")
    assert argv[0] == sys.executable
    assert argv[1] == os.path.join("/도구/뿌리", "viz", "build.py")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_only_init_takes_the_slug_on_the_command_line']"/>
# 명령줄 인자 중 슬러그 문자열은 init 단계에만 붙고, build·check 같은 단계에는 붙지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.script_argv · 쓰이는 곳: 없음
def test_only_init_takes_the_slug_on_the_command_line():
    """`build`·`check` 는 `cwd` 로 대상을 안다. slug 를 주면 인자를 오해한다."""
    assert R.script_argv("/도구/뿌리", "init", slug="붙임")[-1] == "붙임"
    assert R.script_argv("/도구/뿌리", "check", slug="붙임")[-1].endswith("check.py")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2._prompt']"/>
# 테스트 안에서 R.agent_prompt 를 기본값으로 대신 불러주는 작은 도우미 함수다.
# 쓰는 것: runner.run_mode2.agent_prompt · 쓰이는 곳: runner.test_run_mode2.test_the_prompt_forbids_committing, runner.test_run_mode2.test_the_prompt_forbids_the_d_axis, runner.test_run_mode2.test_the_prompt_forbids_the_model_from_filling_the_verdict, runner.test_run_mode2.test_the_prompt_mentions_the_glossary_source_only_when_it_exists, runner.test_run_mode2.test_the_prompt_names_the_canonical_procedure_skill (+3)
# ── 6. 프롬프트 규율 — 검사가 잡아주지 않는 것들 ──────────────────────────
def _prompt(project: str = "/프로젝트", slug: str = "붙임",
            spec_file: str = "2026-08-28-붙임-design.md",
            root: str = "/도구/뿌리", terms_json: str | None = None) -> str:
    """`agent_prompt` 를 기본값으로 부른다. 시험마다 바꾸는 칸만 이름 인자로 준다."""
    return R.agent_prompt(project=project, slug=slug, spec_file=spec_file,
                          root=root, terms_json=terms_json)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_forbids_the_model_from_filling_the_verdict']"/>
# agent_prompt 가 만든 문자열에 판정 금지 문구가 들어있는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_forbids_the_model_from_filling_the_verdict():
    """수용/보류/번복은 **언제나 사용자 몫**이다. 이 한 줄이 빠지면 LLM Model이 채운다."""
    p = _prompt()
    assert "VerdictFooter" in p
    assert "비워" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_states_the_single_script_invariant']"/>
# 프롬프트가 산출물에 <script> 태그는 1개까지만 허용한다는 규칙을 말하는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_states_the_single_script_invariant():
    p = _prompt()
    assert "<script>" in p and "1개" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_forbids_the_d_axis']"/>
# D축(보류 중인 평가 축)을 LLM Model이 함부로 채우지 못하게 프롬프트가 언급하는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_forbids_the_d_axis():
    """D축은 보류 상태다. 프롬프트가 말하지 않으면 LLM Model이 필드를 넣는다."""
    assert "D축" in _prompt()


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_names_the_canonical_procedure_skill']"/>
# 프롬프트가 따라야 할 정식 절차 스킬 이름을 밝히는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_names_the_canonical_procedure_skill():
    assert "spec-review-dashboard" in _prompt()


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_uses_korean_status_tags_only']"/>
# 결정 상태를 나타내는 한국어 태그 3종만 쓰도록 프롬프트가 요구하는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_uses_korean_status_tags_only():
    p = _prompt()
    assert "[제안됨]" in p and "[잠정됨]" in p and "[검증됨]" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_names_the_paths_the_model_must_touch']"/>
# LLM Model이 실제로 건드려야 할 프로젝트 경로와 파일명이 프롬프트 안에 다 적혀 있는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_names_the_paths_the_model_must_touch():
    p = _prompt()
    assert "/프로젝트" in p and "/도구/뿌리" in p
    assert "2026-08-28-붙임-design.md" in p
    assert "data.ts" in p and "report.tsx" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_forbids_committing']"/>
# 프롬프트가 LLM Model에게 커밋을 하지 말라고 명시하는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_forbids_committing():
    assert "커밋하지 마라" in _prompt()


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_mentions_the_glossary_source_only_when_it_exists']"/>
# Mode 1.5 가 만든 terms.json 용어집 경로는 실제로 있을 때만 프롬프트에 언급되고, 없으면 언급되지 않는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_mentions_the_glossary_source_only_when_it_exists():
    """Mode 1.5 의 terms.json 은 **알려 주기만** 한다. 기계로 병합하면 뜻을 다듬는 단계가 사라진다."""
    with_terms = _prompt(terms_json="/프로젝트/specs/붙임/terms.json")
    assert "terms.json" in with_terms
    assert "/프로젝트/specs/붙임/terms.json" in with_terms
    assert "terms.json" not in _prompt(terms_json=None)


@pytest.mark.parametrize("tj", ["/t/terms.json", "/t/terms.json\n"])
def test_용어집_절은_금지_목록과_규율_사이에_빈_줄을_두고_들어간다(tj: str):
    p = _prompt(terms_json=tj)
    assert '이라고 쓰지 마라.**\n\n## 용어집 재료가 이미 있다' in p
    assert '그대로 실린다.\n\n## 규율\n' in p
    assert '\n\n  ' + tj + '\n\nMode 1.5(' in p


def test_용어집이_없으면_금지_목록_뒤에_빈_줄_하나로_규율이_온다():
    p = _prompt()
    assert '이라고 쓰지 마라.**\n\n## 규율\n' in p and p.endswith('한 표로 보고한다.\n')
    assert "원본 문서    /프로젝트/specs/2026-08-28-붙임-design.md" in p
    assert "보고서 폴더  %s " % R.report_dir("/프로젝트", "붙임", "specs") in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_is_not_passed_on_the_command_line']"/>
# LLM Model에게 줄 프롬프트를 명령줄 인자로 싣지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.claude_argv · 쓰이는 곳: 없음
def test_the_prompt_is_not_passed_on_the_command_line():
    """프롬프트는 표준 입력으로 준다 — 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다."""
    argv = M.claude_argv(model="opus", repo="/프로젝트", extra_dirs=["/도구/뿌리"])
    assert not any(len(a) > 200 for a in argv)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_measuring_code_is_reused_not_reimplemented']"/>
# Mode 2 실행기가 시간·토큰을 재는 코드를 직접 다시 만들지 않고 Mode 1 것을 그대로 가져다 쓰는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.normalize_usage, runner.run_mode1.sum_usage, runner.run_mode1.agent_verdict, runner.run_mode1.format_report · 쓰이는 곳: 없음
# ── 7. 재는 코드는 Mode 1 것을 그대로 쓴다 ───────────────────────────────
def test_the_measuring_code_is_reused_not_reimplemented():
    """두 실행기가 각자 세면 같은 이름의 숫자가 서로 다른 뜻을 갖는다."""
    assert R.normalize_usage is M.normalize_usage
    assert R.sum_usage is M.sum_usage
    assert R.agent_verdict is M.agent_verdict
    assert R.format_report is M.format_report


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_a_machine_stage_row_is_all_zero_tokens']"/>
# LLM 을 부르지 않는 '기계 단계'는 토큰과 비용이 전부 0으로 나오는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_a_machine_stage_row_is_all_zero_tokens():
    z = R.normalize_usage(None)
    assert z["total"] == 0 and z["cost_usd"] == 0.0


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_report_table_has_a_row_per_stage_and_a_total']"/>
# 보고서 표에 단계마다 한 줄씩 나오고 합계 줄도 있는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.normalize_usage, runner.run_mode1.format_report · 쓰이는 곳: 없음
def test_the_report_table_has_a_row_per_stage_and_a_total():
    rows: list[M.StageRow] = [
        {"stage": "init", "seconds": 0.4, "usage": R.normalize_usage(None),
         "ok": True, "why": ""},
        {"stage": "agent", "seconds": 68.4, "ok": True, "why": "",
         "usage": R.normalize_usage({"usage": {"input_tokens": 10, "output_tokens": 20,
                                               "cache_read_input_tokens": 30,
                                               "cache_creation_input_tokens": 40},
                                     "total_cost_usd": 1.5, "num_turns": 7})},
    ]
    text = R.format_report(rows)
    assert "init" in text and "agent" in text and "합계" in text
    assert "1분 08.4초" in text


def _ctx(tmp_path: Path) -> R.Mode2Context:
    return R.Mode2Context(root=str(tmp_path), model="opus", project=str(tmp_path),
                          slug="s", folder=str(tmp_path), spec_file="spec.md")


def test_그래프는_고른_단계만_담는다(tmp_path: Path):
    g = R.build_mode2_graph(_ctx(tmp_path), has_manuscript=False,
                            only=None, skip=["check"])
    assert g.order == ["init", "agent", "build"]


def test_원고가_있으면_그래프에_agent_가_없다(tmp_path: Path):
    g = R.build_mode2_graph(_ctx(tmp_path), has_manuscript=True, only=None, skip=None)
    assert "agent" not in g.order


def test_그래프의_실패는_전부_멈춤이다(tmp_path: Path):
    g = R.build_mode2_graph(_ctx(tmp_path), has_manuscript=False, only=None, skip=None)
    assert g.next_of("build", P.FAIL) is None
    assert g.next_of("build", P.OK) == "check"


def test_build_만_고르면_이미_있는_파일이_given_이_된다(tmp_path: Path):
    (tmp_path / "data.ts").write_text("x", encoding="utf-8")
    (tmp_path / "report.tsx").write_text("x", encoding="utf-8")
    g = R.build_mode2_graph(_ctx(tmp_path), has_manuscript=False,
                            only=["build"], skip=None)
    assert g.order == ["build"]


def test_build_만_고르는데_파일이_없으면_팩토리가_죽는다(tmp_path: Path):
    with pytest.raises(P.GraphError) as e:
        R.build_mode2_graph(_ctx(tmp_path), has_manuscript=False,
                            only=["build"], skip=None)
    assert "산출물" in str(e.value)


def test_viz_script_paths_actually_exist() -> None:
    """Mode 2 가 부르는 viz 스크립트 셋이 디스크에 실재하는가."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for stage in ("init", "build", "check"):
        p = R.script_argv(root, stage, "슬러그")[1]
        assert os.path.isfile(p), f"Mode 2 가 없는 파일을 가리킨다: {p}"


# ── 8. Mode 1 봉인 — 있으면 근거로 싣고, 없어도 진행한다 ───────────────────
SEALED = ["/프로젝트/docs/wiki/index.md", "/프로젝트/docs/codegraph/terms-db.json"]
MANIFEST = "/프로젝트/docs/codegraph/manifest.json"


def _sealed_prompt(terms_json: str | None = None, stale: Sequence[str] = (),
                   uncommitted: bool = False) -> str:
    """봉인이 있는 프롬프트. 시험마다 바꾸는 칸만 이름 인자로 준다."""
    return R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구", terms_json=terms_json,
                          evidence=SEALED, manifest=MANIFEST, stale=stale, uncommitted=uncommitted)


def test_prompt_names_mode1_evidence_when_sealed():
    got = R.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md", "/프로젝트/docs/codegraph/terms-db.json"],
                         manifest="/프로젝트/docs/codegraph/manifest.json")
    assert "## Mode 1 실측 자료" in got and "  /프로젝트/docs/wiki/index.md" in got
    assert "(/프로젝트/docs/codegraph/manifest.json)" in got
    assert "봉인 뒤 소스가 움직였다" not in got and "봉인이 커밋되지 않았다" not in got


def test_prompt_lists_stale_files_when_sources_moved():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md"], manifest="/m",
                         stale=["바뀜 pkg/a.py"])
    assert "봉인 뒤 소스가 움직였다" in got and "  바뀜 pkg/a.py" in got


def test_prompt_has_no_evidence_block_without_seal():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구")
    assert "## Mode 1 실측 자료" not in got


def test_prompt_notes_an_uncommitted_seal():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md"], manifest="/m", uncommitted=True)
    assert "봉인이 커밋되지 않았다" in got


def test_봉인이_없으면_낡음과_미커밋_값이_와도_글에_아무것도_더하지_않는다():
    base = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구")
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구",
                         manifest="/m", stale=["바뀜 pkg/a.py"], uncommitted=True)
    assert got == base


def test_봉인_글은_용어집_글을_쓰지_않는다():
    assert "terms.json" not in _sealed_prompt(stale=["바뀜 pkg/a.py"], uncommitted=True)


@pytest.mark.parametrize("tj", [None, "/t/terms.json"])
def test_근거_절은_용어집_뒤_규율_앞에_빈_줄_하나씩을_두고_들어간다(tj: str | None):
    p = _sealed_prompt(terms_json=tj)
    before = '그대로 실린다.\n\n' if tj else '이라고 쓰지 마라.**\n\n'
    assert before + '## Mode 1 실측 자료 — 이 저장소에 봉인돼 있다\n\n  ' + SEALED[0] + '\n  ' + SEALED[1] \
        + '\n\nMode 1(코드베이스 위키)이' in p
    assert '(' + MANIFEST + '). 코드의 뜻' in p
    assert '으로 적는다.\n\n## 규율\n' in p
    if tj:
        assert p.index('## 용어집 재료') < p.index('## Mode 1 실측 자료') < p.index('## 규율')
    else:
        assert '## 용어집 재료' not in p


def test_근거_절_안의_순서는_목록_낡음_미커밋이고_빈_줄_하나로_갈린다():
    p = _sealed_prompt(stale=["바뀜 pkg/a.py", "생김 pkg/b.py"], uncommitted=True)
    assert '적는다.\n\n**봉인 뒤 소스가 움직였다**' in p
    assert '확인한다.\n\n  바뀜 pkg/a.py\n  생김 pkg/b.py\n\n**봉인이 커밋되지 않았다**' in p
    assert '달라질 수 있다.\n\n## 규율\n' in p
    assert (p.index('## Mode 1 실측 자료') < p.index('봉인 뒤 소스가 움직였다')
            < p.index('봉인이 커밋되지 않았다') < p.index('## 규율'))


def test_낡음이_없고_미커밋만_있으면_낡음_문단은_없다():
    p = _sealed_prompt(uncommitted=True)
    assert '적는다.\n\n**봉인이 커밋되지 않았다**' in p
    assert "봉인 뒤 소스가 움직였다" not in p


def test_AgentStage_는_문맥의_봉인_칸을_프롬프트로_넘긴다():
    ctx = R.Mode2Context(root="/도구", model="opus", project="/프로젝트", slug="슬러그",
                         folder="/프로젝트/specs/슬러그", spec_file="x-design.md",
                         evidence=("/프로젝트/docs/wiki/index.md",), manifest="/m",
                         stale=("바뀜 pkg/a.py",), uncommitted=True)
    got = R.AgentStage().prompt(ctx)
    assert "  /프로젝트/docs/wiki/index.md" in got and "  바뀜 pkg/a.py" in got
    assert "봉인이 커밋되지 않았다" in got


def test_문맥의_봉인_칸은_비어_있는_것이_기본이다():
    ctx = R.Mode2Context(root="/도구", model="opus", project="/프로젝트", slug="슬러그",
                         folder="/f", spec_file="x-design.md")
    assert (ctx.evidence, ctx.manifest, ctx.stale, ctx.uncommitted) == ((), "", (), False)
    assert "## Mode 1 실측 자료" not in R.AgentStage().prompt(ctx)


class _FakeRun:
    """`subprocess.run` 자리에 끼우는 가짜. `evidence.py` 호출만 답하고 부른 명령줄을 모은다."""

    def __init__(self, status: str, list_code: int, listed: str) -> None:
        self.status, self.list_code, self.listed = status, list_code, listed
        self.argvs: list[list[str]] = []

    def __call__(self, argv: list[str], **kw: object) -> "subprocess.CompletedProcess[str]":
        self.argvs.append(list(argv))
        if argv[0] == "git":
            return subprocess.CompletedProcess(argv, 0, stdout="/저장소\n", stderr="")
        if "--status" in argv:
            return subprocess.CompletedProcess(argv, 0, stdout=self.status, stderr="")
        return subprocess.CompletedProcess(argv, self.list_code, stdout=self.listed, stderr="")


def test_봉인을_읽으면_상태_한_줄을_찍고_목록을_받는다(monkeypatch: pytest.MonkeyPatch,
                                  capsys: pytest.CaptureFixture[str]):
    fake = _FakeRun("Mode 1 봉인 — 있음 · 낡음 1건\n", 0,
                    '{"manifest": "/저장소/docs/codegraph/manifest.json", "artifacts": ["/저장소/docs/wiki/index.md"],'
                    ' "stale": ["바뀜 a.py"], "stale_files": ["a.py"], "uncommitted": true, "superseded_by": null}')
    monkeypatch.setattr(R.subprocess, "run", fake)
    got = R.read_seal("/프로젝트")
    assert got == {"manifest": "/저장소/docs/codegraph/manifest.json", "artifacts": ["/저장소/docs/wiki/index.md"],
                   "stale": ["바뀜 a.py"], "uncommitted": True}
    assert capsys.readouterr().out == "Mode 1 봉인 — 있음 · 낡음 1건\n"
    evidence_calls = [a for a in fake.argvs if a[0] != "git"]
    assert [a[-1] for a in evidence_calls] == ["--status", "--list"]
    assert all(a[1] == R.EVIDENCE and a[2] == "/저장소" and a[3:6] == ["--need", "terms-db,wiki", "--optional"]
               for a in evidence_calls)


def test_목록이_실패하면_멈추지_않고_빈_값이다(monkeypatch: pytest.MonkeyPatch,
                           capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(R.subprocess, "run", _FakeRun("Mode 1 봉인 — 없음\n", 1, ""))
    assert R.read_seal("/프로젝트") == R.no_seal()
    assert capsys.readouterr().out == "Mode 1 봉인 — 없음\n"


def test_목록이_꼴에_안_맞아도_멈추지_않고_빈_값이다(monkeypatch: pytest.MonkeyPatch,
                              capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(R.subprocess, "run", _FakeRun("Mode 1 봉인 — 있음\n", 0, '{"manifest": 1}'))
    assert R.read_seal("/프로젝트") == R.no_seal()
    assert "꼴에 안 맞는다" in capsys.readouterr().err


def test_상태_줄이_비면_알_수_없다고_찍는다(monkeypatch: pytest.MonkeyPatch,
                         capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(R.subprocess, "run", _FakeRun("", 1, ""))
    R.read_seal("/프로젝트")
    assert capsys.readouterr().out == "Mode 1 봉인 — 상태를 알 수 없다\n"


def test_봉인이_없는_저장소에서_진짜_evidence_py_가_빈_값을_낸다(tmp_path: Path,
                                           capsys: pytest.CaptureFixture[str]):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert R.read_seal(str(tmp_path)) == R.no_seal()
    assert capsys.readouterr().out == "Mode 1 봉인 — 없음\n"


def test_위키_없이_봉인된_저장소에서_terms_db_를_싣는다(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """생산자는 위키가 따라잡지 못하면 terms-db 만 봉인한다 — 그 봉인을 깨짐으로 버리지 않는다."""
    import hashlib
    import json

    def git(*a: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                       check=True, capture_output=True)

    pub = tmp_path / "docs" / "codegraph"
    pub.mkdir(parents=True)
    rec: dict[str, object] = {"kind": "function", "module": "pkg", "where": "pkg/a.py:1", "means": "뜻", "uses": [],
           "neighbors": [], "source": "reading"}
    (pub / "terms-db.json").write_text(json.dumps({"f": rec}, ensure_ascii=False), encoding="utf-8")
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "p", "source_commit": "s",
           "source_exts": [".py"], "skip_dirs": ["out"], "inputs": {},
           "artifacts": {"terms-db": [{"path": "docs/codegraph/terms-db.json",
                                       "sha256": hashlib.sha256((pub / "terms-db.json").read_bytes()).hexdigest()}]}}
    (pub / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "봉인")
    got = R.read_seal(str(tmp_path))
    assert got["artifacts"] == [str(pub / "terms-db.json")]
    assert capsys.readouterr().out == "Mode 1 봉인 — 있음(terms-db 만)\n"


def test_dry_run_은_자식_프로세스를_하나도_띄우지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                  capsys: pytest.CaptureFixture[str]):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "2026-01-01-슬러그-design.md").write_text("# 설계\n", encoding="utf-8")

    def boom(*a: object, **kw: object) -> None:
        raise AssertionError("--dry-run 이 자식 프로세스를 띄웠다: %r" % (a,))

    monkeypatch.setattr(R.subprocess, "run", boom)
    assert R.main([str(tmp_path), "슬러그", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "Mode 1 자료 확인 안 함 — --dry-run" in out
    assert "Mode 1 봉인 —" not in out
