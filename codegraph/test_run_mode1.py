"""test_run_mode1.py — Mode 1 실행기의 회귀 테스트.

**왜 필요한가.** 이 실행기의 존재 이유는 **토큰과 시간을 정확히 재는 것**이다.
그래서 재는 자리가 틀리면 도구 전체가 무의미해진다. 그런데 그 다섯 자리는
**틀려도 오류가 나지 않는다** — 조용히 0이나 절반을 내고 표까지 잘 그려진다.

  1. 단계 고르기   이미 산출물이 있는 단계를 다시 돌면 시간이 부풀고, 없는 단계를
                   건너뛰면 그 뒤가 통째로 막힌다.
  2. 에이전트 하나 LLM 단계는 **하나**다. 둘로 쪼개면 캐시가 새로 서서 토큰이 부풀고
                   측정의 뜻이 달라진다.
  3. 토큰 합       `usage` 는 넷으로 쪼개져 온다(입력 · 출력 · 캐시 읽기 · 캐시 생성).
                   캐시를 빼고 더하면 실제 사용량의 일부만 세게 된다.
  4. 실패 판정     `claude -p` 는 막혀도 종료 코드 0 을 낼 수 있다. `is_error` 와
                   `subtype` 을 봐야 한다.
  5. 투영 덮어쓰기 `terms_db.py` 에 정적 `codegraph.json` 을 안 주면 투영이 그 파일을
                   **덮어쓴다**. 노드가 조용히 줄어든다.

  python -m pytest codegraph/test_run_mode1.py -q      # .venv 를 켠 뒤
"""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1 as R  # noqa: E402


# ── 1. 단계 고르기 — 순수 함수라 파일 시스템을 보지 않는다
def test_빈_저장소면_여덟_단계를_순서대로_돈다():
    """예전 이름은 `test_plan_runs_everything_on_an_empty_repo` 였다.

    warmup 배선까지는 일곱이었다(prep warmup agent warmup-save terms build check).
    2026-08-30 사용자 결정으로 `agent` 가 `survey` 와 `wiki` 로 갈렸고, `terms` 가 그 둘 사이로 왔다.
    `terms` 를 가운데 둔 이유는 산문 세션이 **인용 검사를 통과한** terms-db.json 을
    재료로 받게 하려는 것이다. 예전에는 산문이 검사 전 레코드를 봤다.
    """
    assert R.plan_stages(has_codegraph=False, has_reading=False, has_prose=False) == [
        "prep", "warmup", "survey", "warmup-save", "terms", "wiki", "build", "check"]


def test_warmup_관문이_survey_를_감싼다():
    """예전 이름은 `test_the_two_warmup_gates_straddle_the_agent` 였다.

    관문이 감싸야 하는 것은 **레코드를 만드는 단계**다. `survey` 가 레코드를 만들고
    `wiki` 는 산문을 쓴다. `wiki` 뒤에 확정을 두면 산문 실패가 다음 실행의 전량 재조사를
    부른다 — 레코드는 멀쩡한데 27분을 다시 쓰는 비용 회귀다 (J6).
    """
    p = R.plan_stages(False, False, False)
    assert p.index("warmup") < p.index("survey") < p.index("warmup-save")
    assert p.index("warmup-save") < p.index("wiki")


def test_두_단계가_모형을_부른다():
    """예전 이름은 `test_only_one_stage_calls_the_model` 였다. 예전에는 `agent` 한 칸이었고
    그것이 **이 설계의 급소**라고 적혀 있었다.

    이유는 캐시였다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어 토큰이 부풀고,
    측정값이 파이프라인 비용이 아니라 세션 수의 함수가 된다.
    **2026-08-30 사용자가 그 결정을 뒤집었다.** 층 오름차순 병렬이 세션 분리를 전제하기 때문이다.
    캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다 — 어느 쪽이 큰지는 **아직 재지 않았다.**
    """
    stages = R.plan_stages(False, False, False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["survey", "wiki"]


def test_산출물이_있는_LLM_단계만_각자_빠진다():
    """예전 이름은 `test_plan_skips_the_agent_when_its_output_already_exists` 와
    `test_plan_keeps_the_agent_when_only_half_its_work_is_done` 둘이었다.
    둘을 하나로 합쳤다 — 둘 다 "산출물 유무로 각 LLM 단계가 걸리는가" 라는 같은 성질을 본다.

    예전에는 `agent` 하나를 `has_reading and has_prose` 로 걸렀다.
    이제 각자 자기 산출물로 걸린다 — 한쪽만 있으면 그쪽만 건너뛴다. 이건 **개선**이지 회귀가 아니다.
    """
    both = R.plan_stages(has_codegraph=True, has_reading=True, has_prose=True)
    assert "survey" not in both and "wiki" not in both
    # warmup 두 칸은 남는다 — 판정을 해 봐야 정말 건너뛰어도 되는지 알고,
    # 매니페스트는 갱신해 둬야 다음 실행이 옳게 판정한다(warmup 배선의 규칙 그대로).
    assert both == ["prep", "warmup", "warmup-save", "terms", "build", "check"]

    only_reading = R.plan_stages(True, True, False)
    assert "survey" not in only_reading and "wiki" in only_reading

    only_prose = R.plan_stages(True, False, True)
    assert "survey" in only_prose and "wiki" not in only_prose


def test_the_save_gate_comes_before_terms():
    """매니페스트 확정이 terms 뒤로 밀리면, terms 가 실패했을 때 판정이 사라진다."""
    p = R.plan_stages(False, False, False)
    assert p.index("warmup-save") < p.index("terms")


def test_skip_은_새_여덟_흐름_기준으로_걸러낸다():
    """예전 이름은 `test_skipping_warmup_restores_the_old_five_stage_flow` 였다.

    옛 시험은 `skip=["warmup", "warmup-save"]` 가 **다섯 단계 시절의 대조군**
    (`["prep", "agent", "terms", "build", "check"]`)을 되살린다고 단언했다. 이 계획이
    `agent` 를 지웠으므로 그 값 자체가 더는 나올 수 없다 — `STAGES` 에 `agent` 가 없다.

    **다섯 단계 대조군은 이 코드로 만드는 것이 아니다.** 계획 맨 위 "🔴🔴 서브에이전트 모델"
    절이 이미 정한 대로, 옛 코드가 필요한 대조군은 `git worktree add /tmp/rb-old 9223143`
    로 커밋 `9223143` 을 통째로 떼어 돌린다. `--skip warmup,warmup-save` 는 그 대조군을
    만드는 경로가 **아니다** — 이 시험은 그저 `skip` 이 새 여덟 단계 목록에서도 여전히
    걸러내는 필터로 옳게 동작하는지만 본다.
    """
    p = R.plan_stages(False, False, False, skip=["warmup", "warmup-save"])
    assert p == ["prep", "survey", "terms", "wiki", "build", "check"]


def test_plan_keeps_prep_even_when_codegraph_exists():
    """prep 은 늘 부른다 — 건너뛸지는 prep 자신이 정한다(prepPlan 의 hasCodegraph)."""
    assert R.plan_stages(has_codegraph=True, has_reading=False, has_prose=False)[0] == "prep"


def test_plan_only_and_skip_are_honoured():
    assert R.plan_stages(False, False, False, only=["prep", "check"]) == ["prep", "check"]
    assert "build" not in R.plan_stages(False, False, False, skip=["build"])


def test_plan_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        R.plan_stages(False, False, False, only=["없는단계"])


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


def test_usage_of_a_machine_stage_is_all_zero():
    """기계 단계는 토큰을 쓰지 않는다. None 이 아니라 0 이어야 표가 더해진다."""
    z = R.normalize_usage(None)
    assert z["total"] == 0 and z["cost_usd"] == 0.0 and z["turns"] == 0


def test_usage_tolerates_missing_fields():
    assert R.normalize_usage({"usage": {}})["total"] == 0


def test_usage_sums_across_stages():
    a = R.normalize_usage({"usage": {"input_tokens": 1, "output_tokens": 2}, "total_cost_usd": 0.5})
    b = R.normalize_usage({"usage": {"output_tokens": 3}, "total_cost_usd": 0.25})
    s = R.sum_usage([a, b])
    assert s["total"] == 6 and s["cost_usd"] == 0.75


# ── 3. 실패 판정 — 종료 코드만 믿지 않는다
def test_agent_result_is_a_failure_when_is_error_is_set():
    ok, why = R.agent_verdict(0, {"type": "result", "subtype": "success", "is_error": False})
    assert ok and why == ""
    bad, why = R.agent_verdict(0, {"type": "result", "subtype": "error_max_turns", "is_error": True})
    assert not bad and "error_max_turns" in why


def test_agent_result_is_a_failure_when_the_process_died():
    ok, why = R.agent_verdict(1, {"type": "result", "subtype": "success", "is_error": False})
    assert not ok and "종료 코드 1" in why


def test_agent_result_is_a_failure_when_json_is_unreadable():
    ok, why = R.agent_verdict(0, None)
    assert not ok and "읽지" in why


# ── 3.5 WarmUp — 언어 이름 다리
def test_lang_of_bridges_the_two_naming_schemes(tmp_path):
    """코드 지도는 'csharp' 이라 적고 declmap 은 'cs' 로 안다. 이 한 칸이 어긋나면 단계가 죽는다."""
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "csharp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cs"


def test_lang_of_passes_through_a_name_declmap_already_knows(tmp_path):
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "cpp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cpp"


def test_lang_of_is_none_when_it_cannot_tell():
    """모르는 언어와 없는 파일은 둘 다 None 이다 — 부르는 쪽이 단계를 건너뛴다. 실패가 아니다."""
    assert R.lang_of("/없는/파일.json") is None
    assert R.lang_of(None) is None


def test_seed_includes_position_only_files():
    """급소 — 함수 본문만 바꾼 변경은 '위치만' 으로 온다.

    decl_hash 는 (kind, name) 만 해싱하므로(warmup.py:84) 본문을 통째로 다시 써도
    선언 이름이 같으면 '위치만' 이다. 이것을 빼면 레코드의 does 가 조용히 낡는다.
    """
    판정 = {"유효": ["a.cpp"], "재읽기": ["b.cpp"], "위치만": ["c.cpp"], "삭제됨": ["d.cpp"]}
    assert R.changed_seed(판정) == ["b.cpp", "c.cpp"]


def test_seed_excludes_valid_and_deleted():
    """유효는 읽을 것이 없고, 삭제됨은 읽을 파일 자체가 없다."""
    seed = R.changed_seed({"유효": ["a"], "재읽기": [], "위치만": [], "삭제됨": ["d"]})
    assert seed == []


def test_seed_is_sorted_and_deduplicated():
    """같은 파일이 두 갈래에 들어와도 한 번만 센다 — 프롬프트에 두 번 실리면 안 된다."""
    assert R.changed_seed({"재읽기": ["z", "a"], "위치만": ["a"]}) == ["a", "z"]


def test_seed_tolerates_missing_buckets():
    assert R.changed_seed({}) == []


def test_agent_is_skipped_when_nothing_changed_and_records_exist():
    """국소 변경의 이득이 여기서 나온다 — 27분짜리 단계를 통째로 건너뛴다."""
    assert R.should_call_agent(targets=[], has_reading=True) is False


def test_agent_still_runs_when_there_are_no_records_yet():
    """조사 결과가 아예 없으면 warmup 이 뭐라 하든 부른다 — 백지에서 시작하는 실행이다."""
    assert R.should_call_agent(targets=[], has_reading=False) is True


def test_agent_runs_when_something_changed():
    assert R.should_call_agent(targets=["a.cpp"], has_reading=True) is True


def test_agent_runs_when_warmup_could_not_judge():
    """targets 가 None 이면 warmup 이 못 돌았다는 뜻이다. 그때는 옛 동작(전량)으로 돌아간다."""
    assert R.should_call_agent(targets=None, has_reading=True) is True


def test_warmup_section_lists_every_target_and_the_ratio():
    """에이전트가 범위를 알려면 목록과 비율이 둘 다 있어야 한다."""
    s = R.warmup_section(["core/a.cpp", "server/b.h"], total=77)
    assert "core/a.cpp" in s and "server/b.h" in s
    assert "2" in s and "77" in s
    assert "읽지 마라" in s          # 목록 밖을 읽지 말라고 분명히 말한다


def test_warmup_section_is_empty_when_there_is_nothing_to_scope():
    """범위가 없으면 빈 글이다 — 부르는 쪽이 이 절을 통째로 뺀다."""
    assert R.warmup_section([], total=77) == ""
    assert R.warmup_section(None, total=77) == ""


def _배치():
    return {"id": "L1-B00", "files": ["core/net.py"],
            "symbols": [{"id": "send", "name": "send", "file": "core/net.py",
                         "line": 42, "kind": "function", "in_cycle": False,
                         "depends_on": ["encode"]}]}


def test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다():
    """예전 이름은 `test_prompt_carries_the_scope_when_warmup_gave_one` 였다.

    warmup 이 판정한 목록이 있으면 증분 조사다. 배치 세션이 그것을 알아야
    기존 레코드의 means/does 를 함부로 다시 쓰지 않는다.
    """
    p = R.survey_batch_prompt("/r", "/root", _배치(), "", targets=["core/a.cpp"], total=77)
    assert "core/a.cpp" in p
    assert "증분" in p


def test_배치_프롬프트는_범위가_없으면_전량_조사다():
    """예전 이름은 `test_prompt_without_a_scope_is_the_full_survey` 였다.
    warmup 이 못 돌았거나 백지 실행이면 범위 지시문이 붙지 않는다."""
    p = R.survey_batch_prompt("/r", "/root", _배치(), "")
    assert "증분" not in p


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


def test_claude_argv_does_not_pass_the_prompt_on_the_command_line():
    """프롬프트는 표준 입력으로 준다. 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다."""
    argv = R.claude_argv(model="opus", repo="/r", extra_dirs=[])
    assert not any(len(a) > 200 for a in argv)


def test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다():
    """예전에는 한 프롬프트가 전수조사와 산문을 **둘 다** 지시했다
    (`test_the_prompt_names_both_halves_of_the_one_agent_job`).

    2026-08-30 사용자 결정으로 갈렸다. 배치 세션은 자기 심볼만 읽고 자기 샤드에만 쓴다 —
    terms-reading.json 을 직접 고치면 동시에 도는 다른 배치가 서로를 지운다.
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


def test_배치_프롬프트는_아래층이_없으면_최하층이라고_말한다():
    """층0 은 의존 대상이 없다. 빈 칸을 그냥 두면 세션이 무엇이 빠졌는지 헷갈린다."""
    batch = {"id": "L0-B00", "files": ["a.py"],
             "symbols": [{"id": "f", "name": "f", "file": "a.py", "line": 1,
                          "kind": "function", "in_cycle": False, "depends_on": []}]}
    assert "최하층" in R.survey_batch_prompt("/r", "/root", batch, "")


def test_비노드_프롬프트는_심볼이_아닌_종류만_말한다():
    """K5 — file · module · artifact · key · concept 는 층 축이 없다.
    심볼 레코드가 재료이므로 심볼 층이 전부 끝난 뒤에 돈다."""
    p = R.nonnode_prompt(repo="/어느/저장소", root="/도구/뿌리")
    for kind in ["file", "module", "artifact", "key", "concept"]:
        assert kind in p
    assert "_shards/" in p
    assert "이름으로 보아" in p


def test_의존_발췌는_아래층에_있는_것만_낸다():
    """전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라진다."""
    merged = {"encode": {"means": "바이트로 바꾼다"}, "무관": {"means": "상관없다"}}
    batch = {"symbols": [{"id": "send", "depends_on": ["encode", "아직없음"]}]}
    got = R.dep_excerpt(merged, batch)
    assert "encode" in got and "바이트로 바꾼다" in got
    assert "무관" not in got
    assert "아직없음" not in got


def test_의존_발췌는_아무것도_없으면_빈_문자열():
    assert R.dep_excerpt({}, {"symbols": [{"id": "a", "depends_on": []}]}) == ""


# ── 5. 투영이 정적 codegraph 를 덮어쓰지 않게
def test_terms_argv_passes_the_static_codegraph_positionally():
    """`--reading` 만 주면 투영이 codegraph.json 을 **덮어쓴다**. 실제로 겪은 사고다.

    파일 시스템을 보지 않는 순수 함수다 — 없는 파일을 거르는 것은 부르는 쪽의 일이다.
    """
    argv = R.terms_argv(python="/py", root="/도구/뿌리", repo="/어느/저장소",
                        codegraph="/어느/저장소/out/codegraph-raw/codegraph.json",
                        reading="/어느/저장소/docs/codegraph/terms-reading.json")
    assert argv[1].endswith("terms_db.py")
    assert "/어느/저장소/out/codegraph-raw/codegraph.json" in argv
    assert argv[argv.index("--reading") + 1].endswith("terms-reading.json")
    assert argv[argv.index("--repo") + 1] == "/어느/저장소"


# ── 6. 보고 — 재는 것이 목적이므로 표에 네 값이 다 있어야 한다
def test_report_has_a_row_per_stage_and_a_total():
    rows = [
        {"stage": "prep", "seconds": 68.4, "usage": R.normalize_usage(None), "ok": True},
        {"stage": "agent", "seconds": 512.0, "ok": True,
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


def test_report_marks_a_failed_stage():
    text = R.format_report([{"stage": "build", "seconds": 1.0, "ok": False,
                             "why": "산문이 없다", "usage": R.normalize_usage(None)}])
    assert "실패" in text and "산문이 없다" in text


def test_report_marks_a_skipped_stage():
    """건너뜀을 '성공' 으로 그리면 27분이 15초가 된 이유를 읽는 사람이 알 수 없다."""
    text = R.format_report([{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
                             "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)}])
    assert "건너뜀" in text
    assert "바뀐 파일 0개" in text
    assert "실패" not in text


def test_a_skipped_stage_does_not_break_the_total():
    rows = [{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
             "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)},
            {"stage": "build", "seconds": 2.0, "ok": True,
             "usage": R.normalize_usage(None)}]
    assert "합계" in R.format_report(rows)


# ── 11. warmup 확정 관문이 fail-open 이 되지 않는가 (2026-08-30 신설)
def test_survey_가_실패하면_매니페스트를_갱신하지_않는다(monkeypatch):
    """🔴 층 병렬이 만드는 조용한 버그를 막는 시험이다.

    warmup 배선의 `save_warmup` 은 `r["stage"] == "agent"` 로 실패를 찾았다.
    단계가 `survey` 로 갈리고 행 라벨이 `survey/L0-B00` 꼴이 되면서 그 비교가
    **영원히 거짓**이 됐다 — 조사가 실패해도 매니페스트가 갱신되는 fail-open 이다.
    그래서 단계 이름만 떼어 비교한다.
    """
    import warmup as W
    saved = []
    monkeypatch.setattr(W, "save", lambda path, entries: saved.append(path))

    rows = [{"stage": "survey/L0-B00", "ok": True, "usage": R.normalize_usage(None)},
            {"stage": "survey/L1-B00", "ok": False, "why": "터졌다",
             "usage": R.normalize_usage(None)}]
    R.save_warmup("/캐시/경로.json", {"a.py": {}}, rows)
    assert saved == [], "전수조사가 실패했는데 매니페스트를 갱신했다"

    rows[1]["ok"] = True
    R.save_warmup("/캐시/경로.json", {"a.py": {}}, rows)
    assert saved == ["/캐시/경로.json"]


def test_판정을_못_했으면_아무것도_쓰지_않는다(monkeypatch):
    """`entries is None` 은 warmup 이 언어를 몰라 판정을 건너뛴 경우다.
    그때 쓰면 근거 없는 매니페스트가 생긴다."""
    import warmup as W
    saved = []
    monkeypatch.setattr(W, "save", lambda path, entries: saved.append(path))
    R.save_warmup("/캐시/경로.json", None, [])
    R.save_warmup(None, {"a.py": {}}, [])
    assert saved == []


# ── 12. 층 병렬 — 동시에 몇 개까지 뜨는가 (2026-08-30 신설)
def test_run_layer_는_동시_한도를_넘지_않는다(monkeypatch):
    """K4 — 한 층에서 동시에 8배치까지. 넘으면 rate limit 에 걸려 층 전체가 무너진다.

    실제로 `claude` 를 부르지 않는다. `run_agent_with` 를 바꿔 끼워 **동시에 몇 개가
    살아 있었는지**만 센다.
    """
    import threading
    lock, live, peak = threading.Lock(), [0], [0]

    def fake(model, repo, root, prompt, timeout=None, label=None):
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


def test_run_layer_는_라벨_순서로_돌려준다(monkeypatch):
    """배치가 끝나는 순서는 흔들린다. 보고 표가 실행마다 달라지면 대조를 못 한다."""
    monkeypatch.setattr(R, "run_agent_with",
                        lambda *a, **k: (0.01, 0, {"usage": {}, "num_turns": 0}))
    jobs = [("L0-B02", "다"), ("L0-B00", "가"), ("L0-B01", "나")]
    labels = [row[0] for row in R.run_layer("claude-sonnet-5", "/r", "/root", jobs)]
    assert labels == ["L0-B00", "L0-B01", "L0-B02"]


def test_run_layer_는_한_배치가_죽어도_나머지를_돌린다(monkeypatch):
    """배치 하나가 터졌다고 층 전체를 버리면 20분이 날아간다. 실패는 행으로 남기고 계속 간다."""
    def fake(model, repo, root, prompt, timeout=None, label=None):
        if label == "L0-B01":
            raise RuntimeError("자식이 죽었다")
        return 0.01, 0, {"usage": {}, "num_turns": 0}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B00", "가"), ("L0-B01", "나"), ("L0-B02", "다")]
    rows = R.run_layer("claude-sonnet-5", "/r", "/root", jobs)
    bad = [r for r in rows if r[0] == "L0-B01"][0]
    assert bad[2] != 0 and bad[3] is None      # (라벨, 초, 종료코드, 결과)
    assert len(rows) == 3


def test_빈_층은_모형을_부르지_않는다(monkeypatch):
    """샤드가 이미 다 있으면 할 일이 없다. 그런데도 부르면 돈만 나간다(J4)."""
    monkeypatch.setattr(R, "run_agent_with",
                        lambda *a, **k: pytest.fail("빈 층에서 모형을 불렀다"))
    assert R.run_layer("claude-sonnet-5", "/r", "/root", []) == []


# ── 13. 샤드 병합 — 키 충돌은 전역을 보는 쪽만 푼다 (2026-08-30 신설)
def _shard(tmp_path, name, payload):
    import json as _j
    d = tmp_path / "_shards"
    d.mkdir(exist_ok=True)
    (d / (name + ".json")).write_text(_j.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(d)


def test_샤드를_하나로_합친다(tmp_path):
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    _shard(tmp_path, "L0-B01", {"나": {"where": "b.py:1"}})
    got = R.merge_shards(d, {})
    assert sorted(got) == ["가", "나"]


def test_키가_겹치면_양쪽_다_개명한다(tmp_path):
    """한쪽만 한정하면 나중에 또 겹친다. `main` 이 9파일이면 9개 전부 개명이다."""
    d = _shard(tmp_path, "L0-B00", {"main": {"where": "app/gui.py:10"}})
    _shard(tmp_path, "L0-B01", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {})
    assert "main" not in got
    assert sorted(got) == ["gui.main", "net.main"]


def test_아래층_레코드를_보존한다(tmp_path):
    """층 k 의 병합이 층 <k 의 결과를 지우면 조사가 층마다 초기화된다."""
    d = _shard(tmp_path, "L1-B00", {"위": {"where": "b.py:1"}})
    got = R.merge_shards(d, {"아래": {"where": "a.py:1"}})
    assert sorted(got) == ["아래", "위"]


def test_이미_있는_키와_겹쳐도_양쪽_다_개명한다(tmp_path):
    """아래층이 이미 쓴 이름과 겹치는 경우다. 새 것만 한정하면 옛 것이 계속 모호하다."""
    d = _shard(tmp_path, "L1-B00", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {"main": {"where": "app/gui.py:10"}})
    assert sorted(got) == ["gui.main", "net.main"]


def test_망가진_샤드는_건너뛰고_나머지를_살린다(tmp_path):
    """배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 20분을 버리지 않는다."""
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    (tmp_path / "_shards" / "L0-B01.json").write_text("{ 깨진", encoding="utf-8")
    assert sorted(R.merge_shards(d, {})) == ["가"]


def test_샤드_폴더가_없으면_있던_것을_그대로(tmp_path):
    assert R.merge_shards(str(tmp_path / "없다"), {"가": {}}) == {"가": {}}
