#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_grade.py']"/>
# 채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기.

`run_mode1_5.py` 의 `grade` 단계만 떼어 낸 것이다. 세 가지가 다르다.

  - **계획서가 아니라 작업 폴더를 받는다.** 이미 문답이 끝난 폴더를 곧장 가리킨다.
  - **채운 기입란을 두 이름에서 찾는다** — `answers.json` 이 있으면 그것, 없으면
    `answer-sheet.json`. 사람이 깔아 준 기입란에 그대로 답을 적는 일이 잦은데
    `run_mode1_5.py` 는 `answers.json` 만 보므로 그 경우 "답안이 아직 없다" 로 건너뛴다.
  - **채점만 한다.** `collect` 도 `emit` 도 돌리지 않는다.

채점 규칙과 명령줄은 `run_mode1_5.py` 의 것을 그대로 쓴다 — 여기에 사본을 두지 않는다.

쓰는 법:

    python runner/run_grade.py out/mode1_5/symbol-resolution-survey
    python runner/run_grade.py --plan docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md
    python runner/run_grade.py <폴더> --answers 내가-푼-것.json
"""
import argparse
import os
import sys
from collections.abc import Sequence

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# `run_mode1_5` 를 모듈 이름으로 부르려면 이 디렉토리가 sys.path 에 있어야 한다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_mode1_5 as Q  # noqa: E402


# 채운 기입란을 찾을 이름과 순서. 앞에 있는 것이 이긴다.
SHEET_NAMES = (Q.ANSWERS, Q.SHEET)


# <include file="machine/comments.xml" path="//term[@id='runner.run_grade.find_sheet']"/>
# 작업 폴더에서 채운 기입란 파일을 찾아 그 경로를 돌려주는 함수다.
# 쓰는 것: runner.run_grade.SHEET_NAMES · 쓰이는 곳: runner.run_grade.main
def find_sheet(workdir: str, names: Sequence[str] = SHEET_NAMES) -> str | None:
    """채운 기입란의 경로. 없으면 None.

    순서가 뜻을 갖는다 — `answers.json`(스킬이 따로 떠 놓은 것)이 있으면 그것이 이기고,
    없을 때만 `answer-sheet.json`(실행기가 깔아 준 것)을 본다.
    """
    for name in names:
        p = os.path.join(workdir, name)
        if os.path.isfile(p):
            return p
    return None


# <include file="machine/comments.xml" path="//term[@id='runner.run_grade.main']"/>
# 채점만 하는 실행기의 진입점.
# 쓰는 것: runner.run_grade.find_sheet, runner.run_mode1_5.grade_argv, runner.run_mode1_5.run_machine, runner.run_mode1_5.default_workdir, runner.run_mode1_5.validate_questions · 쓰이는 곳: 없음
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="채운 기입란을 문항지와 대조해 채점한다. 채점만 한다.")
    ap.add_argument("workdir", nargs="?", default=None,
                    help="문답이 끝난 작업 폴더. 생략하면 --plan 으로 찾는다")
    ap.add_argument("--plan", default=None,
                    help="계획서 경로. 주면 out/mode1_5/<slug>/ 을 작업 폴더로 잡는다")
    ap.add_argument("--answers", default=None,
                    help="채운 기입란 경로를 직접 지정한다. 기본은 %s 순으로 찾는다"
                         % " → ".join(SHEET_NAMES))
    a = ap.parse_args(argv)

    if a.workdir:
        workdir = os.path.abspath(os.path.expanduser(a.workdir))
    elif a.plan:
        plan = os.path.abspath(os.path.expanduser(a.plan))
        if not os.path.isfile(plan):
            print("에러 — 계획서가 없다: %s" % plan, file=sys.stderr)
            return 1
        workdir = Q.default_workdir(ROOT, plan)
    else:
        ap.error("작업 폴더나 --plan 중 하나는 줘야 한다")
        return 1

    if not os.path.isdir(workdir):
        print("에러 — 작업 폴더가 없다: %s" % workdir, file=sys.stderr)
        return 1

    questions = os.path.join(workdir, Q.QUESTIONS)
    if not os.path.isfile(questions):
        print("에러 — 문항지가 없다: %s" % questions, file=sys.stderr)
        return 1

    if a.answers:
        answers = os.path.abspath(os.path.expanduser(a.answers))
        if not os.path.isfile(answers):
            print("에러 — 기입란이 없다: %s" % answers, file=sys.stderr)
            return 1
    else:
        found = find_sheet(workdir)
        if found is None:
            print("에러 — 채운 기입란이 없다. %s 중 하나가 있어야 한다: %s"
                  % (" 또는 ".join(SHEET_NAMES), workdir), file=sys.stderr)
            return 1
        answers = found

    # 문항지가 채점 가능한 꼴인지 먼저 본다 — `quiz.py` 는 꼴을 보지 않는다.
    doc = Q._read_json(questions)  # pyright: ignore[reportPrivateUsage]
    complaints = Q.validate_questions(doc) if doc is not None \
        else ["%s 을 읽지 못했다" % questions]
    if complaints:
        for c in complaints:
            print("  문항지 — %s" % c, file=sys.stderr)
        print("에러 — 문항지가 채점 불가능한 꼴이다: %s" % questions, file=sys.stderr)
        return 1

    # flush — 자식 프로세스가 먼저 찍히면 어느 파일을 채점했는지가 결과 뒤로 밀린다.
    print("작업 폴더 %s" % workdir, flush=True)
    print("기입란   %s" % os.path.basename(answers), flush=True)
    print("문항지   %s" % os.path.basename(questions), flush=True)

    # `quiz.py` 는 산출물을 cwd 에 쓴다. 작업 폴더를 cwd 로 줘야 term-grades.json 이 제자리에 간다.
    rc = Q.run_machine(Q.grade_argv(ROOT, answers, questions), "grade", workdir)
    if rc != 0:
        print("실패 — 종료 코드 %d" % rc, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
