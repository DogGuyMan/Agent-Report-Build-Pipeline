# <include file="machine/comments.xml" path="//term[@id='test_run_mode1.py']"/>
# Mode 1 실행기의 회귀 테스트 — 단계 고르기·토큰 합·실패 판정·투영을 본다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 1 실행기의 회귀 테스트.

재는 자리는 **틀려도 오류가 나지 않는다** — 조용히 0이나 절반을 내고 표까지 잘 그려진다.
그래서 여기서 본다: 단계 고르기 · 토큰 합(캐시 둘을 더하는가) · 실패 판정(종료 코드 0 인
실패를 잡는가) · 투영이 정적 `codegraph.json` 을 덮어쓰지 않는가 · 층 병렬과 샤드 병합.

  python -m pytest runner/test_run_mode1.py -q      # .venv 를 켠 뒤
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import cast

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as R  # noqa: E402
import warmup as W  # noqa: E402
from survey_plan import PlanBatch, SurveyPlan  # noqa: E402
from warmup import Manifest  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_빈_저장소면_열_단계를_순서대로_돈다']"/>
# 코드 지도도 읽기 레코드도 산문도 없는 백지 상태에서 Mode 1 이 어떤 순서로 단계를 도는지 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
# ── 1. 단계 고르기 — 순수 함수라 파일 시스템을 보지 않는다
def test_빈_저장소면_열_단계를_순서대로_돈다():
    """`terms` 가 `survey` 와 `wiki` 사이인 것은 산문 세션이 **인용 검사를 통과한**
    terms-db.json 을 재료로 받게 하려는 것이다.
    """
    assert R.plan_stages(has_codegraph=False, has_reading=False, has_prose=False) == [
        "lang-select", "prep", "warmup", "survey-plan", "survey", "warmup-save",
        "terms", "wiki", "build", "check"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_warmup_관문이_survey_를_감싼다']"/>
# warmup 이 survey 앞에, warmup-save 확정이 survey 뒤에 오는지 — 즉 조사가 판정과 확정 사이에 안전하게 감싸여 있는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_warmup_관문이_survey_를_감싼다():
    """관문이 감싸야 하는 것은 **레코드를 만드는 단계**다. `wiki` 뒤에 확정을 두면
    산문 실패가 다음 실행의 전량 재조사를 부른다 (J6).
    """
    p = R.plan_stages(False, False, False)
    assert p.index("warmup") < p.index("survey") < p.index("warmup-save")
    assert p.index("warmup-save") < p.index("wiki")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_세_단계가_모형을_부른다']"/>
# 열 단계 중 실제로 LLM 모형을 부르는 단계가 딱 셋(lang-select, survey, wiki)인지 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages, runner.run_mode1.is_agent_stage · 쓰이는 곳: 없음
def test_세_단계가_모형을_부른다():
    """모형을 부르는 칸은 `survey` 와 `wiki` 둘뿐이다. 토큰도 그 둘에서만 잡힌다."""
    stages = R.plan_stages(False, False, False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["lang-select", "survey", "wiki"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_산출물이_있는_LLM_단계만_각자_빠진다']"/>
# 조사(survey)와 산문(wiki)은 서로 다른 산출물로 각자 독립적으로 건너뛰어지는지, 즉 한쪽 산출물만 있어도 그 단계만 빠지는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_산출물이_있는_LLM_단계만_각자_빠진다():
    """LLM 단계 둘은 각자 자기 산출물로 걸린다 — 한쪽만 있으면 그쪽만 건너뛴다."""
    both = R.plan_stages(has_codegraph=True, has_reading=True, has_prose=True)
    assert "survey" not in both and "wiki" not in both
    # warmup 두 칸은 남는다 — 판정을 해 봐야 정말 건너뛰어도 되는지 알고,
    # 매니페스트는 갱신해 둬야 다음 실행이 옳게 판정한다(warmup 배선의 규칙 그대로).
    assert both == ["lang-select", "prep", "warmup", "survey-plan", "warmup-save",
                    "terms", "build", "check"]

    only_reading = R.plan_stages(True, True, False)
    assert "survey" not in only_reading and "wiki" in only_reading

    only_prose = R.plan_stages(True, False, True)
    assert "survey" in only_prose and "wiki" not in only_prose


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_the_save_gate_comes_before_terms']"/>
# 매니페스트를 확정하는 warmup-save 단계가 terms 단계보다 먼저 와야 terms 실패 시에도 판정이 남는다는 것을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_the_save_gate_comes_before_terms():
    """매니페스트 확정이 terms 뒤로 밀리면, terms 가 실패했을 때 판정이 사라진다."""
    p = R.plan_stages(False, False, False)
    assert p.index("warmup-save") < p.index("terms")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_skip_은_열_단계_흐름_기준으로_걸러낸다']"/>
# skip 인자로 특정 단계 이름을 주면 그 단계들이 전체 흐름에서 빠진 채 나머지 순서는 그대로 유지되는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_skip_은_열_단계_흐름_기준으로_걸러낸다():
    """`skip` 이 열 단계 목록에서 걸러내는 필터로 옳게 도는지만 본다."""
    p = R.plan_stages(False, False, False, skip=["warmup", "warmup-save"])
    assert p == ["lang-select", "prep", "survey-plan", "survey", "terms",
                 "wiki", "build", "check"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_plan_keeps_prep_even_when_codegraph_exists']"/>
# 코드 지도가 이미 있어도 prep 단계 자체는 항상 계획에 남아야 한다는 것을 보는 시험이다. 건너뛸지는 prep 내부(prepPlan)가 정한다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_plan_keeps_prep_even_when_codegraph_exists():
    """prep 은 늘 부른다 — 건너뛸지는 prep 자신이 정한다(prepPlan 의 hasCodegraph)."""
    stages = R.plan_stages(has_codegraph=True, has_reading=False, has_prose=False)
    assert stages[0] == "lang-select" and stages[1] == "prep"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_plan_only_and_skip_are_honoured']"/>
# only 인자를 주면 그 단계들만 남고, skip 인자를 주면 지정한 단계가 빠지는지 각각 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_plan_only_and_skip_are_honoured():
    assert R.plan_stages(False, False, False, only=["prep", "check"]) == ["prep", "check"]
    assert "build" not in R.plan_stages(False, False, False, skip=["build"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_plan_rejects_an_unknown_stage']"/>
# 존재하지 않는 단계 이름을 only 에 넣으면 조용히 무시하지 않고 오류를 내야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_plan_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        R.plan_stages(False, False, False, only=["없는단계"])


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_usage_totals_include_cache']"/>
# 토큰 사용량을 셀 때 캐시 읽기와 캐시 생성 토큰까지 더해야 실제로 흘러간 토큰 총합이 맞는다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
# ── 2. 토큰 합 — 캐시를 빼먹지 않는다
def test_usage_totals_include_cache():
    """캐시 읽기와 캐시 생성까지 더해야 실제로 흘러간 토큰이다."""
    got = R.normalize_usage({
        "usage": {"input_tokens": 9, "output_tokens": 52,
                  "cache_read_input_tokens": 13595, "cache_creation_input_tokens": 17213},
        "total_cost_usd": 0.036, "num_turns": 1, "duration_ms": 1977, "duration_api_ms": 1657,
    })
    assert got["input"] == 9
    assert got["output"] == 52
    assert got["cache_read"] == 13595
    assert got["cache_write"] == 17213
    assert got["total"] == 9 + 52 + 13595 + 17213
    assert got["cost_usd"] == 0.036
    assert got["turns"] == 1


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_usage_of_a_machine_stage_is_all_zero']"/>
# 토큰을 쓰지 않는 기계 단계는 사용량이 None 이 아니라 전부 0 으로 채워져야 보고 표를 더할 수 있다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_usage_of_a_machine_stage_is_all_zero():
    """기계 단계는 토큰을 쓰지 않는다. None 이 아니라 0 이어야 표가 더해진다."""
    z = R.normalize_usage(None)
    assert z["total"] == 0 and z["cost_usd"] == 0.0 and z["turns"] == 0


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_usage_tolerates_missing_fields']"/>
# usage 딕셔너리 안에 토큰 필드가 하나도 없는 빈 상태에서도 정규화가 죽지 않고 0 을 내는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_usage_tolerates_missing_fields():
    assert R.normalize_usage({"usage": {}})["total"] == 0


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_usage_sums_across_stages']"/>
# 여러 단계의 사용량을 하나로 합쳤을 때 토큰 총합과 비용 총합이 각 단계 값의 합과 같은지 보는 시험이다.
# 쓰는 것: runner.run_mode1.normalize_usage, runner.run_mode1.sum_usage · 쓰이는 곳: 없음
def test_usage_sums_across_stages():
    a = R.normalize_usage({"usage": {"input_tokens": 1, "output_tokens": 2}, "total_cost_usd": 0.5})
    b = R.normalize_usage({"usage": {"output_tokens": 3}, "total_cost_usd": 0.25})
    s = R.sum_usage([a, b])
    assert s["total"] == 6 and s["cost_usd"] == 0.75


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_result_is_a_failure_when_is_error_is_set']"/>
# 종료 코드가 0 이어도 결과 JSON 의 is_error 가 참이면 실패로 판정해야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.agent_verdict · 쓰이는 곳: 없음
# ── 3. 실패 판정 — 종료 코드만 믿지 않는다
def test_agent_result_is_a_failure_when_is_error_is_set():
    ok, why = R.agent_verdict(0, {"type": "result", "subtype": "success", "is_error": False})
    assert ok and why == ""
    bad, why = R.agent_verdict(0, {"type": "result", "subtype": "error_max_turns", "is_error": True})
    assert not bad and "error_max_turns" in why


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_result_is_a_failure_when_the_process_died']"/>
# 결과 JSON 자체는 성공을 말해도 프로세스 종료 코드가 0 이 아니면 전체 판정은 실패여야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.agent_verdict · 쓰이는 곳: 없음
def test_agent_result_is_a_failure_when_the_process_died():
    ok, why = R.agent_verdict(1, {"type": "result", "subtype": "success", "is_error": False})
    assert not ok and "종료 코드 1" in why


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_result_is_a_failure_when_json_is_unreadable']"/>
# 결과 JSON 자체를 읽지 못한 경우(None)에도 실패로 판정하고 그 이유를 알려야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.agent_verdict · 쓰이는 곳: 없음
def test_agent_result_is_a_failure_when_json_is_unreadable():
    ok, why = R.agent_verdict(0, None)
    assert not ok and "읽지" in why


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_lang_of_bridges_the_two_naming_schemes']"/>
# 코드 지도가 언어를 'csharp' 이라 적어도 declmap 은 'cs' 라는 이름으로 아므로, 이 둘을 다리처럼 이어주는 lang_of 를 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.lang_of · 쓰이는 곳: 없음
# ── 3.5 WarmUp — 언어 이름 다리
def test_lang_of_bridges_the_two_naming_schemes(tmp_path: Path):
    """코드 지도는 'csharp' 이라 적고 declmap 은 'cs' 로 안다. 이 한 칸이 어긋나면 단계가 죽는다."""
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "csharp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cs"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_lang_of_passes_through_a_name_declmap_already_knows']"/>
# 코드 지도의 언어 이름이 declmap 이 이미 아는 이름(예: 'cpp')이면 변환 없이 그대로 통과해야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.lang_of · 쓰이는 곳: 없음
def test_lang_of_passes_through_a_name_declmap_already_knows(tmp_path: Path):
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "cpp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cpp"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_lang_of_is_none_when_it_cannot_tell']"/>
# 파일이 없거나 경로 자체가 None 이면 lang_of 는 오류를 내는 대신 None 을 내야 부르는 쪽이 그 단계를 조용히 건너뛸 수 있다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.lang_of · 쓰이는 곳: 없음
def test_lang_of_is_none_when_it_cannot_tell():
    """모르는 언어와 없는 파일은 둘 다 None 이다 — 부르는 쪽이 단계를 건너뛴다. 실패가 아니다."""
    assert R.lang_of("/없는/파일.json") is None
    assert R.lang_of(None) is None


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_seed_includes_position_only_files']"/>
# 함수 본문만 바뀐 변경은 warmup 판정에서 '위치만' 갈래로 오는데, 이 갈래도 다시 읽어야 할 대상에 포함돼야 레코드의 does 가 낡지 않는다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.changed_seed · 쓰이는 곳: 없음
def test_seed_includes_position_only_files():
    """함수 본문만 바꾼 변경은 '위치만' 으로 온다 — `warmup.decl_hash` 가 (kind, name)
    만 해싱하기 때문이다. 이 갈래를 빼면 레코드의 does 가 조용히 낡는다.
    """
    판정 = {"유효": ["a.cpp"], "재읽기": ["b.cpp"], "위치만": ["c.cpp"], "삭제됨": ["d.cpp"]}
    assert R.changed_seed(판정) == ["b.cpp", "c.cpp"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_seed_excludes_valid_and_deleted']"/>
# 유효 갈래는 이미 맞는 레코드가 있어 다시 읽을 필요가 없고, 삭제됨 갈래는 읽을 파일 자체가 사라졌으므로 둘 다 시드에서 빠져야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.changed_seed · 쓰이는 곳: 없음
def test_seed_excludes_valid_and_deleted():
    """유효는 읽을 것이 없고, 삭제됨은 읽을 파일 자체가 없다."""
    seed = R.changed_seed({"유효": ["a"], "재읽기": [], "위치만": [], "삭제됨": ["d"]})
    assert seed == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_seed_is_sorted_and_deduplicated']"/>
# 같은 파일이 재읽기와 위치만 두 갈래에 동시에 들어와도 시드에는 한 번만 실려야 프롬프트에 중복이 안 생긴다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.changed_seed · 쓰이는 곳: 없음
def test_seed_is_sorted_and_deduplicated():
    """같은 파일이 두 갈래에 들어와도 한 번만 센다 — 프롬프트에 두 번 실리면 안 된다."""
    assert R.changed_seed({"재읽기": ["z", "a"], "위치만": ["a"]}) == ["a", "z"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_seed_tolerates_missing_buckets']"/>
# 판정 딕셔너리에 갈래 키가 아예 없는 빈 입력에도 changed_seed 가 죽지 않고 빈 목록을 내는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.changed_seed · 쓰이는 곳: 없음
def test_seed_tolerates_missing_buckets():
    assert R.changed_seed({}) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_is_skipped_when_nothing_changed_and_records_exist']"/>
# 국소 변경 최적화의 핵심 — 대상이 없고 이미 읽기 레코드가 있으면 조사 단계 전체를 통째로 건너뛰어야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.should_call_agent · 쓰이는 곳: 없음
def test_agent_is_skipped_when_nothing_changed_and_records_exist():
    """국소 변경의 이득이 여기서 나온다 — 조사 단계를 통째로 건너뛴다."""
    assert R.should_call_agent(targets=[], has_reading=True) is False


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_still_runs_when_there_are_no_records_yet']"/>
# 대상이 없어도 조사 결과 자체가 아예 없는 백지 상태라면 warmup 판정과 무관하게 에이전트를 불러야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.should_call_agent · 쓰이는 곳: 없음
def test_agent_still_runs_when_there_are_no_records_yet():
    """조사 결과가 아예 없으면 warmup 이 뭐라 하든 부른다 — 백지에서 시작하는 실행이다."""
    assert R.should_call_agent(targets=[], has_reading=False) is True


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_runs_when_something_changed']"/>
# 바뀐 파일이 하나라도 있으면 레코드가 이미 있더라도 에이전트를 불러야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.should_call_agent · 쓰이는 곳: 없음
def test_agent_runs_when_something_changed():
    assert R.should_call_agent(targets=["a.cpp"], has_reading=True) is True


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_agent_runs_when_warmup_could_not_judge']"/>
# targets 가 None 이면 warmup 이 판정 자체를 못 했다는 뜻이므로, 그럴 때는 예전처럼 무조건 전량 조사로 돌아가야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.should_call_agent · 쓰이는 곳: 없음
def test_agent_runs_when_warmup_could_not_judge():
    """targets 가 None 이면 warmup 이 못 돌았다는 뜻이다. 그때는 옛 동작(전량)으로 돌아간다."""
    assert R.should_call_agent(targets=None, has_reading=True) is True


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_warmup_section_lists_every_target_and_the_ratio']"/>
# 에이전트가 조사 범위를 알려면 프롬프트 절에 대상 파일 목록과 전체 대비 비율이 둘 다 있어야 하고, 목록 밖은 읽지 말라는 경고 문구도 있어야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.warmup_section · 쓰이는 곳: 없음
def test_warmup_section_lists_every_target_and_the_ratio():
    """에이전트가 범위를 알려면 목록과 비율이 둘 다 있어야 한다."""
    s = R.warmup_section(["core/a.cpp", "server/b.h"], total=77)
    assert "core/a.cpp" in s and "server/b.h" in s
    assert "2" in s and "77" in s
    assert "읽지 마라" in s          # 목록 밖을 읽지 말라고 분명히 말한다


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_warmup_section_is_empty_when_there_is_nothing_to_scope']"/>
# 범위를 좁힐 대상이 없으면(빈 목록이나 None) 절 자체가 빈 문자열이어야 부르는 쪽이 그 절을 통째로 뺄 수 있다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.warmup_section · 쓰이는 곳: 없음
def test_warmup_section_is_empty_when_there_is_nothing_to_scope():
    """범위가 없으면 빈 글이다 — 부르는 쪽이 이 절을 통째로 뺀다."""
    assert R.warmup_section([], total=77) == ""
    assert R.warmup_section(None, total=77) == ""


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1._배치']"/>
# 테스트에서 쓸 가짜 배치(batch) 데이터 하나를 만들어 주는 도우미 함수다.
# 쓰는 것: machine.survey_plan.PlanBatch · 쓰이는 곳: runner.test_run_mode1.test_배치_프롬프트는_범위가_없으면_전량_조사다, runner.test_run_mode1.test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다, runner.test_run_mode1.test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다
def _배치() -> PlanBatch:
    return {"id": "L1-B00", "files": ["core/net.py"],
            "symbols": [{"id": "send", "name": "send", "file": "core/net.py",
                         "line": 42, "kind": "function", "in_cycle": False,
                         "depends_on": ["encode"]}]}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다']"/>
# survey_batch_prompt 가 targets 를 받았을 때 결과 글에 증분 조사임을 알리는 문구가 들어가는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.survey_batch_prompt, runner.test_run_mode1._배치 · 쓰이는 곳: 없음
def test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다():
    """warmup 이 판정한 목록이 있으면 증분 조사다. 배치 세션이 그것을 알아야
    기존 레코드의 means/does 를 함부로 다시 쓰지 않는다.
    """
    p = R.survey_batch_prompt("/r", "/root", _배치(), "", targets=["core/a.cpp"], total=77)
    assert "core/a.cpp" in p
    assert "증분" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_배치_프롬프트는_범위가_없으면_전량_조사다']"/>
# targets 인자를 주지 않았을 때는(범위를 모를 때) 프롬프트가 전량 조사로 취급되어 "증분"이라는 말이 나오지 않아야 한다는 것을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.survey_batch_prompt, runner.test_run_mode1._배치 · 쓰이는 곳: 없음
def test_배치_프롬프트는_범위가_없으면_전량_조사다():
    """warmup 이 못 돌았거나 백지 실행이면 범위 지시문이 붙지 않는다."""
    p = R.survey_batch_prompt("/r", "/root", _배치(), "")
    assert "증분" not in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_claude_argv_is_headless_json_and_names_the_model']"/>
# claude CLI 를 헤드리스 JSON 모드로, 지정한 모형 이름으로, 대상 저장소와 도구 저장소 두 디렉토리를 모두 볼 수 있게 부르는 명령줄을 만드는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.claude_argv · 쓰이는 곳: 없음
# ── 4. 에이전트 호출 — 하나만, 그리고 대상 저장소를 볼 수 있게
def test_claude_argv_is_headless_json_and_names_the_model():
    argv = R.claude_argv(model="opus", repo="/어느/저장소", extra_dirs=["/도구/뿌리"])
    assert argv[0] == "claude"
    assert "-p" in argv
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--model") + 1] == "opus"
    # 대상 저장소와 도구 저장소를 둘 다 읽어야 한다 — 한쪽만 주면 재료를 못 본다
    dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
    assert "/어느/저장소" in dirs and "/도구/뿌리" in dirs


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_claude_argv_does_not_pass_the_prompt_on_the_command_line']"/>
# 프롬프트 본문은 명령줄 인자가 아니라 표준 입력으로 줘야 길이 한계와 따옴표 처리 문제를 피할 수 있다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.claude_argv · 쓰이는 곳: 없음
def test_claude_argv_does_not_pass_the_prompt_on_the_command_line():
    """프롬프트는 표준 입력으로 준다. 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다."""
    argv = R.claude_argv(model="opus", repo="/r", extra_dirs=[])
    assert not any(len(a) > 200 for a in argv)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다']"/>
# 배치 세션이 만드는 프롬프트가 자기 심볼·자기 샤드에만 쓰라고 말하고, 공유 파일인 terms-reading.json 을 건드리지 말라고 말하며, 통독 캐시를 먼저 보라고 말하고, 금지 표현을 담고 있는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.survey_batch_prompt, runner.test_run_mode1._배치 · 쓰이는 곳: 없음
def test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다():
    """배치 세션은 자기 심볼만 읽고 자기 샤드에만 쓴다 — terms-reading.json 을 직접
    고치면 동시에 도는 다른 배치가 서로를 지운다.
    """
    p = R.survey_batch_prompt(repo="/어느/저장소", root="/도구/뿌리",
                              batch=_배치(), dep_records="  - encode — 바이트로 바꾼다")
    assert "/어느/저장소" in p and "/도구/뿌리" in p
    assert "L1-B00" in p
    assert "core/net.py" in p and "42" in p
    assert "encode — 바이트로 바꾼다" in p           # 아래층 레코드를 발췌해 준다
    assert "_shards/L1-B00.json" in p               # 쓰는 곳은 자기 샤드뿐
    assert "terms-reading.json" in p                # 열지도 고치지도 말라고 적혀 있다
    assert "file_cache.py" in p                     # 통독 캐시를 먼저 본다
    assert "이름으로 보아" in p                       # 금지표
    assert "confidence" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_배치_프롬프트는_아래층이_없으면_최하층이라고_말한다']"/>
# 층0(가장 아래층) 배치를 조사할 때는 의존할 아래층이 없다는 뜻으로 프롬프트에 "최하층"이라는 말이 들어가야 한다는 것을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.survey_batch_prompt · 쓰이는 곳: 없음
def test_배치_프롬프트는_아래층이_없으면_최하층이라고_말한다():
    """층0 은 의존 대상이 없다. 빈 칸을 그냥 두면 세션이 무엇이 빠졌는지 헷갈린다."""
    batch: PlanBatch = {"id": "L0-B00", "files": ["a.py"],
                        "symbols": [{"id": "f", "name": "f", "file": "a.py", "line": 1,
                                     "kind": "function", "in_cycle": False,
                                     "depends_on": []}]}
    assert "최하층" in R.survey_batch_prompt("/r", "/root", batch, "")


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_비노드_프롬프트는_심볼이_아닌_종류만_말한다']"/>
# file·module·artifact·key·concept 는 층(layer) 축이 없는 비노드 종류이므로, 심볼 층 조사가 전부 끝난 뒤 별도 프롬프트로 다뤄져야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.nonnode_prompt · 쓰이는 곳: 없음
def test_비노드_프롬프트는_심볼이_아닌_종류만_말한다():
    """K5 — file · module · artifact · key · concept 는 층 축이 없다.
    심볼 레코드가 재료이므로 심볼 층이 전부 끝난 뒤에 돈다."""
    p = R.nonnode_prompt(repo="/어느/저장소", root="/도구/뿌리")
    for kind in ["file", "module", "artifact", "key", "concept"]:
        assert kind in p
    assert "_shards/" in p
    assert "이름으로 보아" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_의존_발췌는_아래층에_있는_것만_낸다']"/>
# 의존 레코드를 프롬프트에 전량 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라지므로, 자기 배치가 실제로 의존하는 것만 발췌해야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.dep_excerpt · 쓰이는 곳: 없음
def test_의존_발췌는_아래층에_있는_것만_낸다():
    """전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라진다."""
    merged = {"encode": {"means": "바이트로 바꾼다"}, "무관": {"means": "상관없다"}}
    # 일부러 모자란 배치다 — `dep_excerpt` 가 보는 열쇠(`symbols[].depends_on`)만 담았다.
    # `id` · `files` 와 나머지 심볼 칸을 채워 넣으면 이 시험이 무엇을 보는지가 흐려진다.
    batch = cast(PlanBatch, {"symbols": [{"id": "send", "depends_on": ["encode", "아직없음"]}]})
    got = R.dep_excerpt(merged, batch)
    assert "encode" in got and "바이트로 바꾼다" in got
    assert "무관" not in got
    assert "아직없음" not in got


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_의존_발췌는_아무것도_없으면_빈_문자열']"/>
# 의존 레코드도 없고 배치가 의존하는 것도 없으면 발췌 결과가 빈 문자열이어야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.dep_excerpt · 쓰이는 곳: 없음
def test_의존_발췌는_아무것도_없으면_빈_문자열():
    # 위와 같은 이유로 부분 배치다
    assert R.dep_excerpt({}, cast(PlanBatch, {"symbols": [{"id": "a", "depends_on": []}]})) == ""


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_terms_argv_passes_the_static_codegraph_positionally']"/>
# terms_db.py 를 부를 때 정적 codegraph.json 경로를 위치 인자로 넘기지 않으면 --reading 만으로도 그 파일을 덮어써 버리는 실제 사고가 있었기에, 이를 막는 명령줄 조립을 확인하는 시험이다.
# 쓰는 것: runner.run_mode1.terms_argv · 쓰이는 곳: 없음
# ── 5. 투영이 정적 codegraph 를 덮어쓰지 않게
def test_terms_argv_passes_the_static_codegraph_positionally():
    """`--reading` 만 주면 투영이 codegraph.json 을 **덮어쓴다**. 실제로 겪은 사고다.

    파일 시스템을 보지 않는 순수 함수다 — 없는 파일을 거르는 것은 부르는 쪽의 일이다.
    """
    argv = R.terms_argv(python="/py", root="/도구/뿌리", repo="/어느/저장소",
                        codegraph="/어느/저장소/out/codegraph-raw/codegraph.json",
                        reading="/어느/저장소/machine/terms-reading.json")
    assert argv[1].endswith("terms_db.py")
    assert "/어느/저장소/out/codegraph-raw/codegraph.json" in argv
    assert argv[argv.index("--reading") + 1].endswith("terms-reading.json")
    assert argv[argv.index("--repo") + 1] == "/어느/저장소"


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_report_has_a_row_per_stage_and_a_total']"/>
# format_report 가 여러 단계(prep, agent)의 실행 결과를 받아 각 단계 이름과 총 소요 시간, 토큰 합계, 비용, "합계" 줄까지 사람이 읽기 좋은 표 글로 만드는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.format_report, runner.run_mode1.normalize_usage, runner.run_mode1.StageRow · 쓰이는 곳: 없음
# ── 6. 보고 — 재는 것이 목적이므로 표에 네 값이 다 있어야 한다
def test_report_has_a_row_per_stage_and_a_total():
    rows: list[R.StageRow] = [
        {"stage": "prep", "seconds": 68.4, "usage": R.normalize_usage(None),
         "ok": True, "why": ""},
        {"stage": "agent", "seconds": 512.0, "ok": True, "why": "",
         "usage": R.normalize_usage({"usage": {"input_tokens": 10, "output_tokens": 20,
                                               "cache_read_input_tokens": 30,
                                               "cache_creation_input_tokens": 40},
                                     "total_cost_usd": 1.5, "num_turns": 7})},
    ]
    text = R.format_report(rows)
    assert "prep" in text and "agent" in text
    assert "1분 08.4초" in text        # 초가 아니라 사람이 읽는 꼴로 낸다
    assert "100" in text            # 10+20+30+40 = 합계 토큰
    assert "합계" in text
    assert "1.5" in text or "1.50" in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_report_marks_a_failed_stage']"/>
# 단계가 실패(ok: False)했을 때 format_report 가 "실패"라는 표시와 실패 이유 문구를 함께 보여주는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.format_report, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_report_marks_a_failed_stage():
    text = R.format_report([{"stage": "build", "seconds": 1.0, "ok": False,
                             "why": "산문이 없다", "usage": R.normalize_usage(None)}])
    assert "실패" in text and "산문이 없다" in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_report_marks_a_skipped_stage']"/>
# 건너뛴 단계(skipped: True)는 성공과 구분되게 "건너뜀"이라고 표시되어야 하고 "실패"라고 오해되면 안 된다는 것을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.format_report, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_report_marks_a_skipped_stage():
    """건너뜀을 '성공' 으로 그리면 시간이 확 준 이유를 읽는 사람이 알 수 없다."""
    text = R.format_report([{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
                             "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)}])
    assert "건너뜀" in text
    assert "바뀐 파일 0개" in text
    assert "실패" not in text


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_a_skipped_stage_does_not_break_the_total']"/>
# 건너뛴 단계가 행 목록에 섞여 있어도 format_report 가 여전히 "합계" 줄을 정상적으로 내는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.format_report, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_a_skipped_stage_does_not_break_the_total():
    rows: list[R.StageRow] = [{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
                               "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)},
                              {"stage": "build", "seconds": 2.0, "ok": True, "why": "",
                               "usage": R.normalize_usage(None)}]
    assert "합계" in R.format_report(rows)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_survey_가_실패하면_매니페스트를_갱신하지_않는다']"/>
# save_warmup 이 "survey/L0-B00"처럼 슬래시 뒤에 배치 이름이 붙은 행 라벨에서도 앞부분("survey")만 떼어 실패 여부를 올바르게 판단하는지 확인하는 테스트다. 문자열 전체를 통째로 비교하면 절대 실패로 안 잡혀 fail-open(위험하게 항상 통과) 이 되기 때문에 이를 막는 회귀 테스트다.
# 쓰는 것: runner.run_mode1.save_warmup, machine.warmup.save, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
# ── 11. warmup 확정 관문이 fail-open 이 되지 않는가
def test_survey_가_실패하면_매니페스트를_갱신하지_않는다(monkeypatch: pytest.MonkeyPatch):
    """행 라벨이 `survey/L0-B00` 꼴이므로 `r["stage"] == "survey"` 로 비교하면 영원히
    거짓이 되어 fail-open 이 된다. `save_warmup` 은 `/` 앞의 단계 이름만 떼어 본다.
    """
    saved: list[str] = []

    def 가짜_save(path: str, entries: Manifest) -> None:
        saved.append(path)

    monkeypatch.setattr(W, "save", 가짜_save)

    rows: list[R.StageRow] = [
        {"stage": "survey/L0-B00", "seconds": 0.0, "ok": True, "why": "",
         "usage": R.normalize_usage(None)},
        {"stage": "survey/L1-B00", "seconds": 0.0, "ok": False, "why": "터졌다",
         "usage": R.normalize_usage(None)}]
    # 일부러 모자란 매니페스트다 — `save_warmup` 은 `None` 인지와 개수만 보고
    # 나머지는 갈아 끼운 `save` 로 넘길 뿐이다. 다섯 칸을 채우면 소음만 는다.
    엔트리 = cast(Manifest, {"a.py": {}})
    R.save_warmup("/캐시/경로.json", 엔트리, rows)
    assert saved == [], "전수조사가 실패했는데 매니페스트를 갱신했다"

    rows[1]["ok"] = True
    R.save_warmup("/캐시/경로.json", 엔트리, rows)
    assert saved == ["/캐시/경로.json"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_판정을_못_했으면_아무것도_쓰지_않는다']"/>
# warmup 이 언어를 몰라 판정 자체를 건너뛴 경우(entries 가 None)와 저장 경로가 없는 경우(path 가 None)에는 save_warmup 이 아무 것도 저장하지 않아야 한다는 것을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.save_warmup, machine.warmup.save · 쓰이는 곳: 없음
def test_판정을_못_했으면_아무것도_쓰지_않는다(monkeypatch: pytest.MonkeyPatch):
    """`entries is None` 은 warmup 이 언어를 몰라 판정을 건너뛴 경우다.
    그때 쓰면 근거 없는 매니페스트가 생긴다."""
    saved: list[str] = []

    def 가짜_save(path: str, entries: Manifest) -> None:
        saved.append(path)

    monkeypatch.setattr(W, "save", 가짜_save)
    R.save_warmup("/캐시/경로.json", None, [])
    R.save_warmup(None, cast(Manifest, {"a.py": {}}), [])      # 위와 같은 이유로 부분 매니페스트다
    assert saved == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_run_layer_는_동시_한도를_넘지_않는다']"/>
# 한 층에서 동시에 뜨는 배치 수가 concurrency 한도를 넘으면 rate limit 에 걸려 층 전체가 무너지므로, run_layer 가 그 한도를 실제로 지키는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.run_layer · 쓰이는 곳: 없음
# ── 12. 층 병렬 — 동시에 몇 개까지 뜨는가
def test_run_layer_는_동시_한도를_넘지_않는다(monkeypatch: pytest.MonkeyPatch):
    """K4 — 한 층에서 동시에 8배치까지. 넘으면 rate limit 에 걸려 층 전체가 무너진다.

    실제로 `claude` 를 부르지 않는다. `run_agent_with` 를 바꿔 끼워 **동시에 몇 개가
    살아 있었는지**만 센다.
    """
    import threading
    lock, live, peak = threading.Lock(), [0], [0]

    def fake(model: str, repo: str, root: str, prompt: str,
             timeout: float | None = None,
             label: str | None = None) -> tuple[float, int, R.AgentResult | None]:
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.02)
        with lock:
            live[0] -= 1
        return 0.02, 0, {"usage": {"output_tokens": 1}, "num_turns": 1}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B%02d" % i, "글 %d" % i) for i in range(20)]
    got = R.run_layer("claude-sonnet-5", "/r", "/root", jobs, concurrency=3)
    assert peak[0] <= 3
    assert len(got) == 20


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_run_layer_는_라벨_순서로_돌려준다']"/>
# 배치들이 병렬로 도니 끝나는 순서는 흔들리지만, 결과 행은 실행마다 대조 가능하도록 라벨 순서로 정렬돼 나와야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.run_layer · 쓰이는 곳: 없음
def test_run_layer_는_라벨_순서로_돌려준다(monkeypatch: pytest.MonkeyPatch):
    """배치가 끝나는 순서는 흔들린다. 보고 표가 실행마다 달라지면 대조를 못 한다."""
    def fake(model: str, repo: str, root: str, prompt: str,
             timeout: float | None = None,
             label: str | None = None) -> tuple[float, int, R.AgentResult | None]:
        return 0.01, 0, {"usage": {}, "num_turns": 0}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B02", "다"), ("L0-B00", "가"), ("L0-B01", "나")]
    labels = [row[0] for row in R.run_layer("claude-sonnet-5", "/r", "/root", jobs)]
    assert labels == ["L0-B00", "L0-B01", "L0-B02"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_run_layer_는_한_배치가_죽어도_나머지를_돌린다']"/>
# 배치 하나가 예외로 죽었다고 층 전체 작업을 버리면 나머지 배치의 실행 시간이 통째로 날아가므로, 실패는 실패 행으로 남기고 나머지는 계속 돌아야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.run_layer · 쓰이는 곳: 없음
def test_run_layer_는_한_배치가_죽어도_나머지를_돌린다(monkeypatch: pytest.MonkeyPatch):
    """배치 하나가 터졌다고 층 전체를 버리면 20분이 날아간다. 실패는 행으로 남기고 계속 간다."""
    def fake(model: str, repo: str, root: str, prompt: str,
             timeout: float | None = None,
             label: str | None = None) -> tuple[float, int, R.AgentResult | None]:
        if label == "L0-B01":
            raise RuntimeError("자식이 죽었다")
        return 0.01, 0, {"usage": {}, "num_turns": 0}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B00", "가"), ("L0-B01", "나"), ("L0-B02", "다")]
    rows = R.run_layer("claude-sonnet-5", "/r", "/root", jobs)
    bad = [r for r in rows if r[0] == "L0-B01"][0]
    assert bad[2] != 0 and bad[3] is None      # (라벨, 초, 종료코드, 결과)
    assert len(rows) == 3


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_빈_층은_모형을_부르지_않는다']"/>
# 샤드가 이미 다 있어서 할 일이 없는 빈 층인데도 모형을 부르면 돈만 나가므로, 빈 작업 목록이면 아예 부르지 말아야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.run_layer · 쓰이는 곳: 없음
def test_빈_층은_모형을_부르지_않는다(monkeypatch: pytest.MonkeyPatch):
    """샤드가 이미 다 있으면 할 일이 없다. 그런데도 부르면 돈만 나간다(J4)."""
    def fake(model: str, repo: str, root: str, prompt: str,
             timeout: float | None = None,
             label: str | None = None) -> tuple[float, int, R.AgentResult | None]:
        pytest.fail("빈 층에서 모형을 불렀다")

    monkeypatch.setattr(R, "run_agent_with", fake)
    assert R.run_layer("claude-sonnet-5", "/r", "/root", []) == []


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1._shard']"/>
# 테스트용 임시 폴더 안에 샤드(shard) JSON 파일 하나를 만들어 주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: runner.test_run_mode1.test_같은_샤드를_두_번_합쳐도_개명하지_않는다, runner.test_run_mode1.test_망가진_샤드는_건너뛰고_나머지를_살린다, runner.test_run_mode1.test_샤드를_하나로_합친다, runner.test_run_mode1.test_아래층_레코드를_보존한다, runner.test_run_mode1.test_이미_있는_키와_겹쳐도_양쪽_다_개명한다 (+1)
# ── 13. 샤드 병합 — 키 충돌은 전역을 보는 쪽만 푼다
def _shard(tmp_path: Path, name: str, payload: R.Records) -> str:
    import json as _j
    d = tmp_path / "_shards"
    d.mkdir(exist_ok=True)
    (d / (name + ".json")).write_text(_j.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(d)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_샤드를_하나로_합친다']"/>
# merge_shards 가 여러 배치가 각각 낸 샤드 파일(JSON)들을 하나의 딕셔너리로 합치는 기본 동작을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_샤드를_하나로_합친다(tmp_path: Path):
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    _shard(tmp_path, "L0-B01", {"나": {"where": "b.py:1"}})
    got = R.merge_shards(d, {})
    assert sorted(got) == ["가", "나"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_키가_겹치면_양쪽_다_개명한다']"/>
# 서로 다른 두 샤드 파일이 같은 키("main")를 쓸 때, merge_shards 가 어느 한쪽만 남기지 않고 양쪽 다 새 이름으로 바꿔(개명) 둘 다 살리는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_키가_겹치면_양쪽_다_개명한다(tmp_path: Path):
    """한쪽만 한정하면 나중에 또 겹친다. `main` 이 9파일이면 9개 전부 개명이다."""
    d = _shard(tmp_path, "L0-B00", {"main": {"where": "app/gui.py:10"}})
    _shard(tmp_path, "L0-B01", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {})
    assert "main" not in got
    assert sorted(got) == ["gui.main", "net.main"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_아래층_레코드를_보존한다']"/>
# 위층(L1) 샤드를 합칠 때 이미 있던 아래층(L0 이하) 병합 결과가 지워지지 않고 그대로 남아있는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_아래층_레코드를_보존한다(tmp_path: Path):
    """층 k 의 병합이 층 <k 의 결과를 지우면 조사가 층마다 초기화된다."""
    d = _shard(tmp_path, "L1-B00", {"위": {"where": "b.py:1"}})
    got = R.merge_shards(d, {"아래": {"where": "a.py:1"}})
    assert sorted(got) == ["아래", "위"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_이미_있는_키와_겹쳐도_양쪽_다_개명한다']"/>
# 새로 합치려는 샤드의 키가 이미 기존(아래층) 결과에 있던 키와 겹칠 때도, 두 키가 겹칠 때와 마찬가지로 양쪽 다 개명해야 한다는 것을 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_이미_있는_키와_겹쳐도_양쪽_다_개명한다(tmp_path: Path):
    """아래층이 이미 쓴 이름과 겹치는 경우다. 새 것만 한정하면 옛 것이 계속 모호하다."""
    d = _shard(tmp_path, "L1-B00", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {"main": {"where": "app/gui.py:10"}})
    assert sorted(got) == ["gui.main", "net.main"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_망가진_샤드는_건너뛰고_나머지를_살린다']"/>
# 샤드 파일 하나가 JSON 파싱이 안 될 정도로 깨져 있어도, merge_shards 가 그 파일만 건너뛰고 나머지 정상 샤드는 그대로 합쳐내는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_망가진_샤드는_건너뛰고_나머지를_살린다(tmp_path: Path):
    """배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 20분을 버리지 않는다."""
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    (tmp_path / "_shards" / "L0-B01.json").write_text("{ 깨진", encoding="utf-8")
    assert sorted(R.merge_shards(d, {})) == ["가"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_샤드_폴더가_없으면_있던_것을_그대로']"/>
# 합칠 샤드 폴더 자체가 없을 때 merge_shards 가 에러를 내지 않고 기존에 넘겨받은 결과를 그대로 돌려주는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards · 쓰이는 곳: 없음
def test_샤드_폴더가_없으면_있던_것을_그대로(tmp_path: Path):
    assert R.merge_shards(str(tmp_path / "없다"), {"가": {}}) == {"가": {}}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_심볼_층_표를_계획에서_뽑는다']"/>
# 위키 페이지 층을 매기려면 먼저 심볼마다 몇 층인지 알아야 하므로, 조사 계획(SurveyPlan)에서 심볼별 층 번호 표를 뽑아내는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.symbol_layers · 쓰이는 곳: 없음
# ── 14. 위키도 같은 층 순서로 (K6)
def test_심볼_층_표를_계획에서_뽑는다():
    """페이지 층을 매기려면 심볼마다 층이 몇인지 알아야 한다."""
    # 일부러 모자란 계획이다 — `symbol_layers` 가 보는 것은 층 번호와 심볼 id 뿐이라
    # `totals` 와 나머지 심볼 칸을 채워 넣으면 이 시험이 무엇을 보는지가 흐려진다.
    plan = cast(SurveyPlan, {"layers": [
        {"level": 0, "batches": [{"id": "L0-B00", "symbols": [{"id": "encode"}]}]},
        {"level": 1, "batches": [{"id": "L1-B00", "symbols": [{"id": "send"}]}]},
        {"level": 2, "kind": "non-node", "batches": []},
    ]})
    assert R.symbol_layers(plan) == {"encode": 0, "send": 1}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_페이지_층은_인용한_심볼의_최대']"/>
# 위키 페이지가 인용하는 심볼 중 가장 위층의 심볼이 아직 안 다뤄졌으면 그 페이지도 아직 쓸 수 없으므로, 페이지 층은 인용 심볼 층의 최댓값이어야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.page_layers · 쓰이는 곳: 없음
def test_페이지_층은_인용한_심볼의_최대():
    """가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다."""
    sym = {"encode": 0, "send": 1, "retry": 3}
    pages: list[R.WikiPage] = [{"file": "protocol.md", "symbols": ["encode", "send"]},
                               {"file": "net.md", "symbols": ["retry", "encode"]}]
    assert R.page_layers(pages, sym) == {"protocol.md": 1, "net.md": 3}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_인용_심볼이_없는_페이지는_층0']"/>
# index.md 처럼 개괄만 있고 심볼을 인용하지 않는 페이지는 맨 먼저 써도 아무것도 앞지르지 않으므로 층0 으로 매겨야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.page_layers · 쓰이는 곳: 없음
def test_인용_심볼이_없는_페이지는_층0():
    """index.md 처럼 개괄만 있는 장이다. 맨 먼저 써도 아무것도 앞지르지 않는다."""
    assert R.page_layers([{"file": "index.md", "symbols": []}], {}) == {"index.md": 0}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_모르는_심볼은_층을_올리지_않는다']"/>
# 카탈로그가 지어낸 존재하지 않는 심볼 이름 하나 때문에 페이지가 엉뚱하게 맨 뒤 층으로 밀리면 안 된다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.page_layers · 쓰이는 곳: 없음
def test_모르는_심볼은_층을_올리지_않는다():
    """카탈로그가 지어낸 이름 하나로 페이지가 맨 뒤로 밀리면 안 된다."""
    assert R.page_layers([{"file": "a.md", "symbols": ["없는것"]}], {"x": 4}) == {"a.md": 0}


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_카탈로그_프롬프트는_계획_파일을_내라고_말한다']"/>
# 위키 카탈로그 단계의 프롬프트가 wiki-plan.json 을 산출물로 내라고 말하고, 인용 검사를 통과한 terms-db.json 을 재료로 보라고 말하며, 페이지마다 인용할 심볼 키를 적으라고 요구하는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.wiki_catalogue_prompt · 쓰이는 곳: 없음
def test_카탈로그_프롬프트는_계획_파일을_내라고_말한다():
    p = R.wiki_catalogue_prompt(repo="/어느/저장소", root="/도구/뿌리")
    assert "/어느/저장소" in p and "/도구/뿌리" in p
    assert "wiki-plan.json" in p
    assert "terms-db.json" in p          # 인용 검사를 통과한 재료를 본다
    assert "index.md" in p
    assert "symbols" in p                # 페이지마다 인용할 심볼 키를 적게 한다


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_페이지_프롬프트는_아래층_페이지를_링크하라고_말한다']"/>
# 위키 페이지 작성 프롬프트가 아래층 페이지 내용을 다시 설명하는 대신 링크로 연결하라고 지시하는지, 그리고 로컬 인용 규격과 서브에이전트 모델 계열을 명시하는지 보는 시험이다.
# 쓰는 것: runner.run_mode1.wiki_page_prompt · 쓰이는 곳: 없음
def test_페이지_프롬프트는_아래층_페이지를_링크하라고_말한다():
    """재설명 대신 링크하게 하는 것이 층 순서를 지키는 이유다."""
    page: R.WikiPage = {"file": "net.md", "title": "네트워크", "symbols": ["send"]}
    p = R.wiki_page_prompt(repo="/어느/저장소", root="/도구/뿌리", page=page,
                           lower_pages="  - protocol.md — 프로토콜")
    assert "net.md" in p and "네트워크" in p
    assert "protocol.md — 프로토콜" in p
    assert "deep-wiki" in p
    assert "사이트 조립은 하지" in p       # 그건 report-wiki build 의 일이다
    assert "(경로:줄)" in p               # 로컬 인용 규격
    assert "Sonnet 5" in p                # 서브에이전트를 띄운다면 같은 계열로


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_페이지_프롬프트는_아래층이_없으면_그렇게_말한다']"/>
# 가장 아래층인 index.md 처럼 링크할 아래층 페이지가 없으면, 프롬프트가 그 사실을 '첫 장' 이라고 명시적으로 알려줘야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.wiki_page_prompt · 쓰이는 곳: 없음
def test_페이지_프롬프트는_아래층이_없으면_그렇게_말한다():
    p = R.wiki_page_prompt("/r", "/root", {"file": "index.md", "title": "머리", "symbols": []}, "")
    assert "첫 장" in p


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_보고표는_진짜_벽시계를_따로_받는다']"/>
# 병렬로 여러 배치가 동시에 도는 경우 각 행의 초를 그냥 더하면 실제로 걸린 벽시계 시간과 다르기 때문에, format_report 가 wall_seconds 인자를 명시적으로 받으면 합계 줄에 그 값을 쓰고 안 주면 행들의 초를 그대로 더하는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.format_report, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
# ── 15. 병렬이면 행의 초 합계는 벽시계가 아니다
def test_보고표는_진짜_벽시계를_따로_받는다():
    """`wall_seconds` 를 주면 합계 줄이 그 값을 쓰고, 안 주면 행의 초를 더한다 —
    `run_mode2.py` 와 `run_mode1_5.py` 가 인자 없이 부르므로 기본값이 있어야 한다.
    """
    rows: list[R.StageRow] = [{"stage": "survey/L0-B00", "seconds": 100.0, "ok": True,
                               "why": "", "usage": R.normalize_usage(None)},
                              {"stage": "survey/L0-B01", "seconds": 100.0, "ok": True,
                               "why": "", "usage": R.normalize_usage(None)}]
    assert "3분 20.0초" in R.format_report(rows)              # 100+100, 예전 방식
    assert "1분 45.0초" in R.format_report(rows, wall_seconds=105.0)


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_단계별_소계를_낸다']"/>
# stage_totals 가 "survey/L0-B00"·"survey/L1-B00"처럼 슬래시로 배치가 붙은 행들을 "survey"라는 한 단계로 접어 시간과 턴 수를 소계로 합산하는지 확인하는 테스트다.
# 쓰는 것: runner.run_mode1.stage_totals, runner.run_mode1.normalize_usage · 쓰이는 곳: 없음
def test_단계별_소계를_낸다():
    """어느 단계가 비쌌는지 보려면 배치 행을 단계로 접어야 한다."""
    rows: list[R.StageRow] = [
        {"stage": "prep", "seconds": 1.0, "usage": R.normalize_usage(None),
         "ok": True, "why": ""},
        {"stage": "survey/L0-B00", "seconds": 10.0, "ok": True, "why": "",
         "usage": R.normalize_usage({"usage": {"output_tokens": 5}, "num_turns": 2})},
        {"stage": "survey/L1-B00", "seconds": 20.0, "ok": True, "why": "",
         "usage": R.normalize_usage({"usage": {"output_tokens": 7}, "num_turns": 3})},
    ]
    got = R.stage_totals(rows)
    assert got["survey"]["total"] == 12 and got["survey"]["turns"] == 5
    assert got["prep"]["total"] == 0


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_같은_샤드를_두_번_합쳐도_개명하지_않는다']"/>
# merge_shards 가 같은 입력으로 여러 번 불려도(예: 층마다 다시 부르는 상황) 매번 같은 결과를 내야 하고, 이전 병합 결과를 다시 입력으로 줘도 잘못 개명하지 않아야 한다(멱등성)는 것을 확인하는 테스트다. 새로 읽은 객체를 파이썬 `is not` 같은 정체성 비교로 "남"이라 착각해 잘못 개명하는 버그를 막기 위한 테스트다.
# 쓰는 것: runner.run_mode1.merge_shards, runner.test_run_mode1._shard · 쓰이는 곳: 없음
def test_같은_샤드를_두_번_합쳐도_개명하지_않는다(tmp_path: Path):
    """층마다 `merge_shards` 를 부르면 샤드를 매번 다시 읽는다. `is not` 으로 충돌을
    보면 다시 읽은 새 객체를 남으로 착각해 개명한다. 같은 입력이면 몇 번을 합쳐도
    같은 결과여야 한다(멱등).
    """
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1", "means": "뜻"}})
    한번 = R.merge_shards(d, {})
    두번 = R.merge_shards(d, {})
    assert 한번 == 두번 == {"가": {"where": "a.py:1", "means": "뜻"}}
    # 앞선 결과를 다시 넘겨도(잘못된 사용) 최소한 개명은 일어나지 않아야 한다
    assert R.merge_shards(d, 한번) == 한번


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_층_계획은_LLM_단계가_아니다']"/>
# 층을 오름차순으로 매기는 survey-plan 단계는 codegraph.json 하나로 결정론으로 계산하는 기계 단계이지 모형을 부르는 LLM 단계가 아니라는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages, runner.run_mode1.is_agent_stage · 쓰이는 곳: 없음
# ── 16. 층 계획은 기계다 — LLM 이 하는 일처럼 보이면 안 된다
def test_층_계획은_LLM_단계가_아니다():
    """`survey-plan` 은 `AGENT_STAGES` 에 없다.

    층 오름차순은 `survey_plan.py` 가 codegraph.json 하나로 **결정론**으로 낸다 —
    의존을 몇 개 갖는지(out_deg)가 아니라 **위상 깊이**다(K1). 이 사실이 표에서
    안 보이면 읽는 사람이 층 매기기까지 모형이 하는 줄 안다. 그래서 자기 칸을 준다.
    """
    stages = R.plan_stages(False, False, False)
    assert "survey-plan" in stages
    assert not R.is_agent_stage("survey-plan")
    assert [s for s in stages if R.is_agent_stage(s)] == ["lang-select", "survey", "wiki"]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_층_계획은_조사와_산문보다_먼저다']"/>
# 층 계획이 없으면 배치도 페이지 층도 만들 수 없으므로, survey-plan 이 survey 와 wiki 보다 먼저 오고 warmup 뒤에 와야 증분 목록을 받을 수 있다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_stages · 쓰이는 곳: 없음
def test_층_계획은_조사와_산문보다_먼저다():
    """계획이 없으면 배치도 페이지 층도 만들 수 없다."""
    p = R.plan_stages(False, False, False)
    assert p.index("survey-plan") < p.index("survey") < p.index("wiki")
    assert p.index("warmup") < p.index("survey-plan")      # 증분 목록을 받아야 한다


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_계획_요약은_층과_배치와_합계를_낸다']"/>
# 돈을 쓰기 전에 몇 세션이 뜨는지 사람이 한눈에 보도록, 층 계획 요약이 층별 심볼·파일·배치 수와 비노드 층, 전체 합계를 문자열 줄로 내야 한다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.plan_summary · 쓰이는 곳: 없음
def test_계획_요약은_층과_배치와_합계를_낸다():
    """돈을 쓰기 전에 몇 세션이 뜨는지 사람이 봐야 한다."""
    # 위와 같은 이유로 부분 계획이다 — `plan_summary` 가 읽는 열쇠만 담았다.
    plan = cast(SurveyPlan, {"layers": [
        {"level": 0, "symbol_count": 5, "file_count": 3,
         "batches": [{"id": "L0-B00"}, {"id": "L0-B01"}]},
        {"level": 1, "kind": "non-node", "batches": []},
    ], "totals": {"symbols": 5, "levels": 1}})
    lines = R.plan_summary(plan)
    assert "층0 — 심볼 5 · 파일 3 · 배치 2" in lines[0]
    assert "비노드" in lines[1]
    assert "배치 2" in lines[-1] and "심볼 5" in lines[-1]


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_lang_of_maps_every_collector_language_to_declmap']"/>
# 수집기가 codegraph.json 에 적는 언어 이름 셋(cpp, csharp, python) 모두가 declmap 이 아는 이름(cpp, cs, py)으로 정확히 풀려야, 새 수집기를 더할 때 이름을 빠뜨려도 여기서 잡힌다는 것을 보는 시험이다.
# 쓰는 것: runner.run_mode1.lang_of · 쓰이는 곳: 없음
def test_lang_of_maps_every_collector_language_to_declmap(tmp_path: Path) -> None:
    """코드 지도가 적는 언어 이름 셋이 전부 declmap 이 아는 이름으로 풀려야 한다.

    풀리지 않으면 lang_of 가 None 을 내고 warmup 단계가 **조용히 건너뛰어진다** — 죽지
    않으므로 알아채기 어렵다. 수집기를 더할 때 LANG_ALIAS 를 빠뜨리면 여기서 잡힌다.
    """
    for lang, want in (("cpp", "cpp"), ("csharp", "cs"), ("python", "py")):
        p = tmp_path / f"{lang}.json"
        p.write_text(json.dumps({"language": lang}), encoding="utf-8")
        assert R.lang_of(str(p)) == want, lang


# <include file="machine/comments.xml" path="//term[@id='runner.test_run_mode1.test_every_runner_script_path_actually_exists']"/>
# 세 실행기(Mode 1·1.5·2)가 부르는 node 스크립트 경로가 실제로 디스크에 존재하는지 확인해, 디렉토리 개편 후에도 옛 경로를 가리킨 채 시험만 통과하는 일을 막는 시험이다.
# 쓰는 것: runner.run_mode1.wiki_argv, runner.run_mode1_5._term_script, runner.run_mode2.script_argv · 쓰이는 곳: 없음
def test_every_runner_script_path_actually_exists() -> None:
    """세 실행기가 부르는 node 스크립트가 **디스크에 실재하는지** 본다.

    문자열만 대조하는 시험은 디렉토리가 개편돼도 초록으로 남는다 — 실제로
    `scripts/` 가 `runner/`·`viz/` 로 갈린 뒤에도 세 실행기가 옛 경로를 가리킨 채
    시험이 통과하고 있었다. 여기서는 파일 존재를 본다.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "runner"))
    import run_mode1_5 as R15
    import run_mode2 as R2

    for script in ("prep.py", "build.py", "check.py"):
        p = R.wiki_argv(sys.executable, root, script, "/대상")[1]
        assert os.path.isfile(p), f"Mode 1 이 없는 파일을 가리킨다: {p}"
    for name in ("collect.py", "emit.py", "quiz.py"):
        # 이 시험만 모듈 전용 헬퍼를 들여다본다 — 경로가 실재하는지 보는 것이 목적이고
        # 그 경로를 만드는 곳이 여기뿐이다. 공개로 올리면 계약에 없는 이름이 는다.
        p = R15._term_script(root, name)  # pyright: ignore[reportPrivateUsage]
        assert os.path.isfile(p), f"Mode 1.5 가 없는 파일을 가리킨다: {p}"
    for stage in ("init", "build", "check"):
        p = R2.script_argv(root, stage, "슬러그")[1]
        assert os.path.isfile(p), f"Mode 2 가 없는 파일을 가리킨다: {p}"


# ── 10. 전수조사 원본의 자리 — 자기호스팅만 다르다
def test_자기호스팅_읽기레코드_경로가_실재한다() -> None:
    """이 저장소 자신을 조사할 때 원본은 `machine/terms-reading.json` 이다.

    없는 자리를 가리키면 `has_reading` 이 거짓이 되어 전량 재조사가 돈다 — 실패하지
    않고 조용히 비싸진다. 그래서 문자열이 아니라 **파일 존재**를 본다.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = R.reading_path(root, root)
    assert os.path.isfile(p), f"자기호스팅 읽기 레코드가 없다: {p}"


def test_남의_저장소는_docs_codegraph_아래를_본다() -> None:
    assert R.reading_path("/어느/저장소", "/도구/뿌리") == os.path.join(
        "/어느/저장소", "docs", "codegraph", "terms-reading.json")


def test_배치_프롬프트의_범위_지시문이_같은_자리를_말한다() -> None:
    """프롬프트가 말하는 자리와 실행기가 읽고 쓰는 자리가 갈리면 세션이 없는 파일을 찾는다."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s = R.warmup_section(["machine/warmup.py"], total=39, repo=root)
    assert R.reading_path(root, root) in s
