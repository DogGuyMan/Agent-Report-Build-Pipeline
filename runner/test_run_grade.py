import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
import run_grade as G  # noqa: E402


def _questions() -> dict[str, Any]:
    return {"plan": "p.md", "terms": [{
        "term": "bin", "means": "진입점이 있는 곳.",
        "questions": [
            {"ask": "q1", "choices": ["a", "b", "c", "d", "모르겠다"], "answer": 0},
            {"ask": "q2", "choices": ["a", "b", "c", "d", "모르겠다"], "answer": 1},
            {"ask": "q3", "choices": ["a", "b", "c", "d", "모르겠다"], "answer": 2},
        ]}]}


def _sheet(answers: list[str]) -> dict[str, Any]:
    return {"plan": "p.md", "questions": [
        {"QNum": i + 1, "Term": "bin", "Question": "q%d" % (i + 1),
         "AnsChoices": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "모르겠다"},
         "UserAns": a}
        for i, a in enumerate(answers)]}


def _workdir(tmp_path: Path, sheet_name: str, answers: list[str]) -> Path:
    d = tmp_path / "wd"
    d.mkdir()
    (d / "questions.json").write_text(json.dumps(_questions(), ensure_ascii=False), encoding="utf-8")
    (d / sheet_name).write_text(json.dumps(_sheet(answers), ensure_ascii=False), encoding="utf-8")
    return d


def test_answers_json_wins_over_answer_sheet(tmp_path: Path):
    """둘 다 있으면 answers.json 이 이긴다 — 스킬이 따로 떠 놓은 것이 사람의 최종 답안이다."""
    d = tmp_path / "wd"
    d.mkdir()
    (d / "answers.json").touch()
    (d / "answer-sheet.json").touch()
    assert G.find_sheet(str(d)) == os.path.join(str(d), "answers.json")


def test_falls_back_to_answer_sheet(tmp_path: Path):
    """answers.json 이 없으면 실행기가 깔아 준 기입란을 그대로 본다.

    run_mode1_5.py 가 answers.json 만 보느라 건너뛰던 자리가 이것이다.
    """
    d = tmp_path / "wd"
    d.mkdir()
    (d / "answer-sheet.json").touch()
    assert G.find_sheet(str(d)) == os.path.join(str(d), "answer-sheet.json")


def test_returns_none_when_no_sheet(tmp_path: Path):
    d = tmp_path / "wd"
    d.mkdir()
    assert G.find_sheet(str(d)) is None


def test_grades_the_answer_sheet_in_place(tmp_path: Path):
    """answer-sheet.json 만 있어도 채점하고 term-grades.json 을 그 폴더에 낸다."""
    d = _workdir(tmp_path, "answer-sheet.json", ["1", "2", "3"])
    assert G.main([str(d)]) == 0
    got: dict[str, Any] = json.loads((d / "term-grades.json").read_text(encoding="utf-8"))
    assert got["bin"]["mental"] == "확실"
    assert got["bin"]["rate"] == 100


def test_dont_know_twice_is_모름(tmp_path: Path):
    d = _workdir(tmp_path, "answer-sheet.json", ["1", "5", "5"])
    assert G.main([str(d)]) == 0
    got: dict[str, Any] = json.loads((d / "term-grades.json").read_text(encoding="utf-8"))
    assert got["bin"]["mental"] == "모름"


def test_explicit_answers_path_overrides_lookup(tmp_path: Path):
    d = _workdir(tmp_path, "answer-sheet.json", ["5", "5", "5"])
    other = tmp_path / "내가-푼-것.json"
    other.write_text(json.dumps(_sheet(["1", "2", "3"]), ensure_ascii=False), encoding="utf-8")
    assert G.main([str(d), "--answers", str(other)]) == 0
    got: dict[str, Any] = json.loads((d / "term-grades.json").read_text(encoding="utf-8"))
    assert got["bin"]["mental"] == "확실"


def test_missing_workdir_fails(tmp_path: Path):
    assert G.main([str(tmp_path / "없다")]) == 1


def test_missing_questions_fails(tmp_path: Path):
    d = tmp_path / "wd"
    d.mkdir()
    (d / "answer-sheet.json").touch()
    assert G.main([str(d)]) == 1


def test_missing_sheet_fails(tmp_path: Path):
    d = tmp_path / "wd"
    d.mkdir()
    (d / "questions.json").write_text(json.dumps(_questions(), ensure_ascii=False), encoding="utf-8")
    assert G.main([str(d)]) == 1


def test_broken_questions_are_refused_before_grading(tmp_path: Path):
    """문항지가 채점 불가능한 꼴이면 quiz.py 를 부르지 않고 멈춘다."""
    d = tmp_path / "wd"
    d.mkdir()
    bad = _questions()
    bad["terms"][0]["questions"] = bad["terms"][0]["questions"][:2]  # 3문항이 아니다
    (d / "questions.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    (d / "answer-sheet.json").write_text(json.dumps(_sheet(["1", "2"]), ensure_ascii=False), encoding="utf-8")
    assert G.main([str(d)]) == 1
    assert not (d / "term-grades.json").exists()


def test_plan_flag_resolves_the_slug_workdir():
    """--plan 은 run_mode1_5 와 같은 자리를 잡는다 — 두 실행기가 어긋나면 안 된다."""
    import run_mode1_5 as Q  # pyright: ignore[reportMissingTypeStubs]
    plan = os.path.join(ROOT, "docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md")
    assert Q.default_workdir(ROOT, plan).endswith(os.path.join("out", "mode1_5", "symbol-resolution-survey"))


def test_needs_workdir_or_plan(tmp_path: Path):
    with pytest.raises(SystemExit):
        G.main([])
