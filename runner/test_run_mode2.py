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
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as M  # noqa: E402
import run_mode2 as R  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_init_runs_at_the_project_root']"/>
# init 단계가 프로젝트 뿌리 폴더에서 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
# ── 1. 작업 디렉토리 — Mode 2 의 가장 조용한 함정 ──────────────────────────
def test_init_runs_at_the_project_root():
    """`init` 은 `specs/` 가 있는 프로젝트 뿌리에서 돈다. `init.mjs` 가 `join(cwd, "specs")` 를 본다."""
    assert R.stage_cwd("init", project="/프로젝트", report_dir="/프로젝트/specs/붙임") == "/프로젝트"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_agent_also_runs_at_the_project_root']"/>
# 원고를 쓰는 모형(에이전트) 단계도 프로젝트 뿌리에서 돌아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.stage_cwd · 쓰이는 곳: 없음
def test_the_agent_also_runs_at_the_project_root():
    """모형은 설계 문서(`specs/*-design.md`)와 보고서 폴더를 **둘 다** 봐야 한다. 뿌리에 세운다."""
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
# 네 단계 중 모형(LLM)을 부르는 자리는 agent 하나뿐이라는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages, runner.run_mode2.is_agent_stage · 쓰이는 곳: 없음
def test_only_one_stage_calls_the_model():
    """모형을 부르는 자리는 **원고 쓰기 하나**다. 나머지 셋은 기계다."""
    stages = R.plan_stages(has_manuscript=False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["agent"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_skips_the_agent_when_the_manuscript_is_already_written']"/>
# 사람이 이미 원고를 다 썼다면 모형을 다시 부르지 않아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_skips_the_agent_when_the_manuscript_is_already_written():
    """사람이 쓴 원고를 모형이 덮어쓰면 안 된다. 이미 채워졌으면 굽기만 한다."""
    p = R.plan_stages(has_manuscript=True)
    assert "agent" not in p
    assert p == ["init", "build", "check"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_plan_keeps_init_even_when_the_manuscript_exists']"/>
# 원고가 이미 있어도 init 단계는 항상 목록의 맨 앞에 남아야 한다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.plan_stages · 쓰이는 곳: 없음
def test_plan_keeps_init_even_when_the_manuscript_exists():
    """`init` 은 늘 부른다 — 건너뛸지는 `init.mjs` 자신이 정한다(data.ts 가 있으면 exit 0)."""
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
    """`decisions: []` 는 `init` 이 방금 만든 뼈대다. 모형을 불러야 한다."""
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


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_script_argv_points_at_the_renderer_scripts']"/>
# 각 단계를 실제로 실행할 명령줄(argv)이 올바른 node 스크립트를 가리키는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.script_argv · 쓰이는 곳: 없음
# ── 5. 명령줄 — init 만 slug 를 받는다 ───────────────────────────────────
def test_script_argv_points_at_the_renderer_scripts():
    argv = R.script_argv("/도구/뿌리", "build", slug="붙임")
    assert argv[0] == "node"
    assert argv[1] == os.path.join("/도구/뿌리", "viz", "build.mjs")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_only_init_takes_the_slug_on_the_command_line']"/>
# 명령줄 인자 중 슬러그 문자열은 init 단계에만 붙고, build·check 같은 단계에는 붙지 않는다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode2.script_argv · 쓰이는 곳: 없음
def test_only_init_takes_the_slug_on_the_command_line():
    """`build`·`check` 는 `cwd` 로 대상을 안다. slug 를 주면 인자를 오해한다."""
    assert R.script_argv("/도구/뿌리", "init", slug="붙임")[-1] == "붙임"
    assert R.script_argv("/도구/뿌리", "check", slug="붙임")[-1].endswith("check.mjs")


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
    """수용/보류/번복은 **언제나 사용자 몫**이다. 이 한 줄이 빠지면 모형이 채운다."""
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
# D축(보류 중인 평가 축)을 모형이 함부로 채우지 못하게 프롬프트가 언급하는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_forbids_the_d_axis():
    """D축은 보류 상태다. 프롬프트가 말하지 않으면 모형이 필드를 넣는다."""
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
# 모형이 실제로 건드려야 할 프로젝트 경로와 파일명이 프롬프트 안에 다 적혀 있는지 확인하는 테스트 함수다.
# 쓰는 것: runner.test_run_mode2._prompt · 쓰이는 곳: 없음
def test_the_prompt_names_the_paths_the_model_must_touch():
    p = _prompt()
    assert "/프로젝트" in p and "/도구/뿌리" in p
    assert "2026-08-28-붙임-design.md" in p
    assert "data.ts" in p and "report.tsx" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_forbids_committing']"/>
# 프롬프트가 모형에게 커밋을 하지 말라고 명시하는지 확인하는 테스트 함수다.
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


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode2.test_the_prompt_is_not_passed_on_the_command_line']"/>
# 모형에게 줄 프롬프트를 명령줄 인자로 싣지 않는다는 것을 확인하는 시험이다.
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
