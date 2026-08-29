"""test_run_mode2.py — Mode 2 실행기의 회귀 시험.

**왜 필요한가.** 이 실행기가 있는 이유는 Mode 2 한 바퀴가 **얼마나 걸리고 토큰을
얼마나 쓰는가** 를 붙드는 것이다. 그런데 재는 자리와 그 앞의 배선은 **틀려도 오류가
나지 않는다** — 조용히 엉뚱한 폴더에 파일을 만들거나, 0 을 세거나, 사람이 내려야 할
판정을 모형이 대신 채우고도 표는 멀쩡히 그려진다. 그 다섯 자리를 여기서 못박는다.

  1. 작업 디렉토리  Mode 2 는 명령마다 `cwd` 가 **다르다**. `init` 은 프로젝트 뿌리에서,
                    `build` 와 `check` 는 보고서 폴더(`specs/<slug>/`)에서 돈다.
                    여기서 틀리면 조용히 엉뚱한 곳에 스켈레톤이 생긴다.
  2. 단계 고르기    원고가 이미 채워졌는데 모형을 다시 부르면 사람이 쓴 글이 덮이고
                    돈이 든다. 반대로 뼈대뿐인데 건너뛰면 빈 보고서가 구워진다.
  3. 원고 판별      뼈대(`decisions: []` · 결정 절 0개)와 채워진 원고를 글자로 가른다.
  4. 프롬프트 규율  판정(`VerdictFooter`)은 **언제나 사람 몫**이다. `<script>` 1개
                    불변식과 D축 금지도 프롬프트가 말하지 않으면 모형이 어긴다.
  5. 재는 코드 재사용 토큰 세기와 실패 판정은 Mode 1 실행기에 이미 있다. 새로 짜면
                    두 실행기의 숫자가 서로 다른 뜻을 갖게 된다.

  .venv/bin/python -m pytest codegraph/test_run_mode2.py -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as M  # noqa: E402
import run_mode2 as R  # noqa: E402


# ── 1. 작업 디렉토리 — Mode 2 의 가장 조용한 함정 ──────────────────────────
def test_init_runs_at_the_project_root():
    """`init` 은 `specs/` 가 있는 프로젝트 뿌리에서 돈다. `init.mjs` 가 `join(cwd, "specs")` 를 본다."""
    assert R.stage_cwd("init", project="/프로젝트", report_dir="/프로젝트/specs/붙임") == "/프로젝트"


def test_the_agent_also_runs_at_the_project_root():
    """모형은 설계 문서(`specs/*-design.md`)와 보고서 폴더를 **둘 다** 봐야 한다. 뿌리에 세운다."""
    assert R.stage_cwd("agent", project="/프로젝트", report_dir="/프로젝트/specs/붙임") == "/프로젝트"


def test_build_and_check_run_inside_the_report_folder():
    """`build`·`check` 는 보고서 폴더를 `cwd` 로 본다 — 거기서 data.ts 와 report.tsx 를 읽는다."""
    for stage in ("build", "check"):
        assert R.stage_cwd(stage, project="/프로젝트",
                           report_dir="/프로젝트/specs/붙임") == "/프로젝트/specs/붙임"


def test_stage_cwd_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        R.stage_cwd("없는단계", project="/프로젝트", report_dir="/프로젝트/specs/붙임")


def test_report_dir_is_specs_slash_slug():
    assert R.report_dir("/프로젝트", "붙임") == os.path.join("/프로젝트", "specs", "붙임")


# ── 2. 단계 고르기 — 순수 함수라 파일 시스템을 보지 않는다 ────────────────
def test_plan_runs_all_four_stages_on_an_empty_report():
    assert R.plan_stages(has_manuscript=False) == ["init", "agent", "build", "check"]


def test_only_one_stage_calls_the_model():
    """모형을 부르는 자리는 **원고 쓰기 하나**다. 나머지 셋은 기계다."""
    stages = R.plan_stages(has_manuscript=False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["agent"]


def test_plan_skips_the_agent_when_the_manuscript_is_already_written():
    """사람이 쓴 원고를 모형이 덮어쓰면 안 된다. 이미 채워졌으면 굽기만 한다."""
    p = R.plan_stages(has_manuscript=True)
    assert "agent" not in p
    assert p == ["init", "build", "check"]


def test_plan_keeps_init_even_when_the_manuscript_exists():
    """`init` 은 늘 부른다 — 건너뛸지는 `init.mjs` 자신이 정한다(data.ts 가 있으면 exit 0)."""
    assert R.plan_stages(has_manuscript=True)[0] == "init"


def test_plan_only_and_skip_are_honoured():
    assert R.plan_stages(False, only=["build", "check"]) == ["build", "check"]
    assert "agent" not in R.plan_stages(False, skip=["agent"])


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


def test_a_fresh_skeleton_is_not_a_manuscript():
    """`decisions: []` 는 `init` 이 방금 만든 뼈대다. 모형을 불러야 한다."""
    assert R.manuscript_is_written(SKELETON_DATA, SKELETON_REPORT) is False


def test_a_filled_data_and_report_is_a_manuscript():
    assert R.manuscript_is_written(FILLED_DATA, FILLED_REPORT) is True


def test_decisions_without_matching_sections_is_not_a_manuscript():
    """결정은 있는데 본문 절이 없으면 반쯤 쓰다 만 것이다. 이어 쓰게 다시 부른다."""
    assert R.manuscript_is_written(FILLED_DATA, SKELETON_REPORT) is False


def test_missing_files_are_not_a_manuscript():
    assert R.manuscript_is_written(None, None) is False
    assert R.manuscript_is_written(FILLED_DATA, None) is False


# ── 4. 설계 문서 찾기 — slug 를 지어내지 않는다 ──────────────────────────
SPEC_FILES = [
    "2026-08-28-llm-load-reduction-design.md",
    "2026-08-29-mode-1-terms-db-first-design.md",
    "메모.md",
]


def test_find_spec_returns_the_date_from_the_filename():
    got = R.find_spec(SPEC_FILES, "llm-load-reduction")
    assert got["date"] == "2026-08-28"
    assert got["file"] == "2026-08-28-llm-load-reduction-design.md"


def test_find_spec_returns_nothing_for_an_unknown_slug():
    assert R.find_spec(SPEC_FILES, "없는-슬러그") is None


def test_find_spec_does_not_match_a_partial_slug():
    """부분 문자열로 걸리면 엉뚱한 문서를 원본으로 삼는다."""
    assert R.find_spec(SPEC_FILES, "load-reduction") is None


# ── 5. 명령줄 — init 만 slug 를 받는다 ───────────────────────────────────
def test_script_argv_points_at_the_renderer_scripts():
    argv = R.script_argv("/도구/뿌리", "build", slug="붙임")
    assert argv[0] == "node"
    assert argv[1] == os.path.join("/도구/뿌리", "scripts", "build.mjs")


def test_only_init_takes_the_slug_on_the_command_line():
    """`build`·`check` 는 `cwd` 로 대상을 안다. slug 를 주면 인자를 오해한다."""
    assert R.script_argv("/도구/뿌리", "init", slug="붙임")[-1] == "붙임"
    assert R.script_argv("/도구/뿌리", "check", slug="붙임")[-1].endswith("check.mjs")


# ── 6. 프롬프트 규율 — 검사가 잡아주지 않는 것들 ──────────────────────────
def _prompt(**kw):
    kw.setdefault("project", "/프로젝트")
    kw.setdefault("slug", "붙임")
    kw.setdefault("spec_file", "2026-08-28-붙임-design.md")
    kw.setdefault("root", "/도구/뿌리")
    kw.setdefault("terms_json", None)
    return R.agent_prompt(**kw)


def test_the_prompt_forbids_the_model_from_filling_the_verdict():
    """수용/보류/번복은 **언제나 사용자 몫**이다. 이 한 줄이 빠지면 모형이 채운다."""
    p = _prompt()
    assert "VerdictFooter" in p
    assert "비워" in p


def test_the_prompt_states_the_single_script_invariant():
    p = _prompt()
    assert "<script>" in p and "1개" in p


def test_the_prompt_forbids_the_d_axis():
    """D축은 평가 없이 보류 상태다(Phase 3 취소). 필드를 넣으면 tsc 가 아니라 규율이 깨진다."""
    assert "D축" in _prompt()


def test_the_prompt_names_the_canonical_procedure_skill():
    assert "spec-review-dashboard" in _prompt()


def test_the_prompt_uses_korean_status_tags_only():
    p = _prompt()
    assert "[제안됨]" in p and "[잠정됨]" in p and "[검증됨]" in p


def test_the_prompt_names_the_paths_the_model_must_touch():
    p = _prompt()
    assert "/프로젝트" in p and "/도구/뿌리" in p
    assert "2026-08-28-붙임-design.md" in p
    assert "data.ts" in p and "report.tsx" in p


def test_the_prompt_forbids_committing():
    assert "커밋하지 마라" in _prompt()


def test_the_prompt_mentions_the_glossary_source_only_when_it_exists():
    """Mode 1.5 의 terms.json 은 **알려 주기만** 한다. 기계로 병합하면 뜻을 다듬는 단계가 사라진다."""
    with_terms = _prompt(terms_json="/프로젝트/specs/붙임/terms.json")
    assert "terms.json" in with_terms
    assert "/프로젝트/specs/붙임/terms.json" in with_terms
    assert "terms.json" not in _prompt(terms_json=None)


def test_the_prompt_is_not_passed_on_the_command_line():
    """프롬프트는 표준 입력으로 준다 — 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다."""
    argv = M.claude_argv(model="opus", repo="/프로젝트", extra_dirs=["/도구/뿌리"])
    assert not any(len(a) > 200 for a in argv)


# ── 7. 재는 코드는 Mode 1 것을 그대로 쓴다 ───────────────────────────────
def test_the_measuring_code_is_reused_not_reimplemented():
    """두 실행기가 각자 세면 같은 이름의 숫자가 서로 다른 뜻을 갖는다."""
    assert R.normalize_usage is M.normalize_usage
    assert R.sum_usage is M.sum_usage
    assert R.agent_verdict is M.agent_verdict
    assert R.format_report is M.format_report


def test_a_machine_stage_row_is_all_zero_tokens():
    z = R.normalize_usage(None)
    assert z["total"] == 0 and z["cost_usd"] == 0.0


def test_the_report_table_has_a_row_per_stage_and_a_total():
    rows = [
        {"stage": "init", "seconds": 0.4, "usage": R.normalize_usage(None), "ok": True},
        {"stage": "agent", "seconds": 68.4, "ok": True,
         "usage": R.normalize_usage({"usage": {"input_tokens": 10, "output_tokens": 20,
                                               "cache_read_input_tokens": 30,
                                               "cache_creation_input_tokens": 40},
                                     "total_cost_usd": 1.5, "num_turns": 7})},
    ]
    text = R.format_report(rows)
    assert "init" in text and "agent" in text and "합계" in text
    assert "1분 08.4초" in text
