import json
import pytest
from typing import Any, Dict
from runner.term.collect import pick_terms, find_new_concepts
import runner.term.quiz as Q
from runner.term.emit import to_terms_db, to_study_note

def test_pickterms_picks_only_terms_in_plan():
    db = {
      "Renderer": { "kind": "class", "means": "render 모듈의 class." },
      "Unused": { "kind": "class", "means": "안 쓰이는 것." },
    }
    plan = "이 계획은 Renderer 를 고친다."
    got = pick_terms(db, plan)
    assert list(got.keys()) == ["Renderer"]

def test_pickterms_keeps_word_boundaries():
    db = { "Ray": { "kind": "class", "means": "x" } }
    assert list(pick_terms(db, "Raycast 를 쓴다").keys()) == []
    assert list(pick_terms(db, "Ray 를 쓴다").keys()) == ["Ray"]

def test_pickterms_keeps_word_boundaries_with_korean_particles():
    """`pick_terms` 가 조사가 바로 붙은 용어를 잡는다 (re.ASCII 가 빠지면 깨짐)."""
    db = {"Renderer": {}}
    assert "Renderer" in pick_terms(db, "Renderer를 고친다")

def test_findnewconcepts_finds_new_identifiers():
    db = { "Renderer": { "kind": "class", "means": "x" } }
    plan = "C-19 결정에 따라 calls[] 를 roslyn-dump.json 에 넣는다. Renderer 는 그대로다."
    got = find_new_concepts(db, plan)
    assert sorted(got) == ["C-19", "calls[]", "roslyn-dump.json"]

def test_findnewconcepts_ignores_existing_terms():
    db = { "calls[]": { "kind": "field", "means": "x" } }
    assert find_new_concepts(db, "calls[] 를 쓴다") == []

def test_gradeone_assigns_certain_for_2_or_more_correct():
    assert Q.grade_one({ "correct": 3, "dontKnow": 0 })["mental"] == "확실"
    assert Q.grade_one({ "correct": 2, "dontKnow": 0 })["mental"] == "확실"

def test_gradeone_assigns_unknown_for_1_or_less_correct():
    assert Q.grade_one({ "correct": 1, "dontKnow": 0 })["mental"] == "모름"
    assert Q.grade_one({ "correct": 0, "dontKnow": 0 })["mental"] == "모름"

def test_gradeone_assigns_unknown_for_2_or_more_dontknow():
    assert Q.grade_one({ "correct": 1, "dontKnow": 2 })["mental"] == "모름"
    assert Q.grade_one({ "correct": 0, "dontKnow": 3 })["mental"] == "모름"

def test_gradeone_does_not_produce_ambiguous():
    for c in range(4):
        assert Q.grade_one({ "correct": c, "dontKnow": 0 })["mental"] != "애매"

def test_gradeone_returns_accuracy_rate():
    assert Q.grade_one({ "correct": 2, "dontKnow": 0 })["rate"] == 67
    assert Q.grade_one({ "correct": 1, "dontKnow": 0 })["rate"] == 33

def test_gradeone_rounds_half_up(monkeypatch: pytest.MonkeyPatch):
    """`grade_one` 의 백분율이 half-up 이다."""
    monkeypatch.setattr(Q, "QUESTIONS_PER_TERM", 2)
    # 1/2 = 50%
    assert Q.grade_one({ "correct": 1, "dontKnow": 0 })["rate"] == 50
    
    monkeypatch.setattr(Q, "QUESTIONS_PER_TERM", 8)
    # 1/8 = 12.5% -> rounds up to 13% with math.floor(x + 0.5)
    assert Q.grade_one({ "correct": 1, "dontKnow": 0 })["rate"] == 13

def test_totermsdb_includes_certain_terms():
    SAMPLE = {
      "calls[]": { "means": "누가 누구를 부르는지 모은 목록", "mental": "모름", "rate": 20 },
      "Renderer": { "means": "render 모듈의 class", "mental": "확실", "rate": 100 },
    }
    db = to_terms_db(SAMPLE)
    assert len(db) == 2, "확실로 판정된 것이 빠졌다"

def test_totermsdb_separates_answer_and_understanding():
    SAMPLE = {
      "calls[]": { "means": "누가 누구를 부르는지 모은 목록", "mental": "모름", "rate": 20 },
      "Renderer": { "means": "render 모듈의 class", "mental": "확실", "rate": 100 },
    }
    db = to_terms_db(SAMPLE)
    assert db["calls[]"]["TermMeans"] == "누가 누구를 부르는지 모은 목록"
    assert db["calls[]"]["UserMentalValue"] == "모름"

def test_tostudynote_includes_only_unknown_and_ambiguous():
    SAMPLE = {
      "calls[]": { "means": "누가 누구를 부르는지 모은 목록", "mental": "모름", "rate": 20 },
      "Renderer": { "means": "render 모듈의 class", "mental": "확실", "rate": 100 },
    }
    md = to_study_note(SAMPLE)
    assert "calls[]" in md, "모름인 용어가 학습 노트에 없다"
    assert "Renderer" not in md, "확실한 용어가 학습 노트에 들어갔다"

def test_tostudynote_indicates_when_nothing_to_study():
    md = to_study_note({ "A": { "means": "x", "mental": "확실", "rate": 100 } })
    assert "학습할 용어가 없다" in md

def one_question(ask: str, answer: int) -> Dict[str, Any]:
    return {
        "ask": ask,
        "choices": [
            "그래프에서 중요한 점을 매긴다",
            "파일을 줄 단위로 센다",
            "주석을 소스에 심는다",
            "선언을 훑어 목록으로 만든다",
            "모르겠다",
        ],
        "answer": answer,
    }

def good_doc() -> Dict[str, Any]:
    return {
        "plan": "/어느/plan.md",
        "terms": [
            {
                "term": "PageRank",
                "means": "그래프에서 중요한 점을 매기는 방법",
                "questions": [one_question(f"문항 {i}", i) for i in [0, 1, 2]],
            },
        ],
    }

def filled_sheet(doc: Dict[str, Any], picks: list[Any]) -> Dict[str, Any]:
    questions = []
    for i, q in enumerate(Q.flatten_questions(doc)):
        questions.append({
            "QNum": q["QNum"],
            "Term": q["Term"],
            "Question": q["Question"],
            "AnsChoices": {},
            "UserAns": picks[i],
        })
    return {
        "plan": doc.get("plan"),
        "questions": questions,
    }

def test_choices_per_question():
    assert Q.CHOICES_PER_QUESTION == 5

def test_flattenquestions_numbers_sequentially_across_terms():
    doc = good_doc()
    doc["terms"].append({
        "term": "declmap.scan",
        "means": "선언을 훑는다",
        "questions": [one_question(f"둘째 {i}", i) for i in [0, 1, 2]],
    })
    flat = Q.flatten_questions(doc)
    assert [q["QNum"] for q in flat] == [1, 2, 3, 4, 5, 6]
    assert [q["Term"] for q in flat] == ["PageRank", "PageRank", "PageRank", "declmap.scan", "declmap.scan", "declmap.scan"]

def test_flattenquestions_shifts_answer_to_1_based_index():
    assert [q["Answer"] for q in Q.flatten_questions(good_doc())] == [1, 2, 3]

def test_choicenumber_accepts_numbers_and_strings():
    assert Q.choice_number(3) == 3
    assert Q.choice_number("3") == 3
    assert Q.choice_number(" 3 ") == 3

def test_choicenumber_rejects_bool():
    """`choice_number` 가 `True` 를 보기 번호로 받지 않는다."""
    assert Q.choice_number(True) is None

def test_choicenumber_does_not_fill_blanks_with_dontknow():
    assert Q.choice_number("") is None
    assert Q.choice_number(None) is None
    assert Q.choice_number("셋") is None

def test_tallysheet_counts_correct_answers():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [1, 2, 3]), doc)
    assert problems == []
    assert counts["PageRank"] == {
        "correct": 3,
        "dontKnow": 0,
        "means": "그래프에서 중요한 점을 매기는 방법",
    }

def test_tallysheet_counts_last_choice_as_dontknow():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [5, 5, 3]), doc)
    assert counts["PageRank"]["dontKnow"] == 2
    assert counts["PageRank"]["correct"] == 1

def test_tallysheet_does_not_count_wrong_answers_as_correct():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [2, 1, 3]), doc)
    assert counts["PageRank"]["correct"] == 1
    assert counts["PageRank"]["dontKnow"] == 0

def test_tallysheet_catches_blanks_and_blocks_grading():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [1, "", 3]), doc)
    assert len(problems) == 1
    assert "UserAns" in problems[0]

def test_tallysheet_catches_out_of_bounds_numbers():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [1, 2, 9]), doc)
    assert "보기 밖" in " ".join(problems)

def test_tallysheet_does_not_grade_answers_with_mismatched_terms():
    doc = good_doc()
    sheet = filled_sheet(doc, [1, 2, 3])
    sheet["questions"][0]["Term"] = "declmap.scan"
    counts, problems = Q.tally_sheet(sheet, doc)
    assert "어긋난다" in " ".join(problems)

def test_tallysheet_does_not_grade_answers_with_mismatched_question_text():
    doc = good_doc()
    sheet = filled_sheet(doc, [1, 2, 3])
    sheet["questions"][0]["Question"] = "다른 물음이 되어 버렸다"
    counts, problems = Q.tally_sheet(sheet, doc)
    assert "물음 문구" in " ".join(problems)

def test_tallysheet_catches_missing_and_extra_answers():
    doc = good_doc()
    sheet = filled_sheet(doc, [1, 2, 3])
    sheet["questions"].pop()
    sheet["questions"].append({ "QNum": 99, "Term": "PageRank", "Question": "없던 물음", "UserAns": 1 })
    problems = Q.tally_sheet(sheet, doc)[1]
    joined = " ".join(problems)
    assert "3번" in joined
    assert "99번" in joined

def test_tallysheet_rejects_old_count_format_files():
    doc = good_doc()
    old = { "PageRank": { "correct": 2, "dontKnow": 1, "means": "그래프 중요도" } }
    problems = Q.tally_sheet(old, doc)[1]
    assert "기입란" in " ".join(problems)

def test_tallysheet_output_matches_gradeall_input():
    doc = good_doc()
    counts, problems = Q.tally_sheet(filled_sheet(doc, [1, 2, 5]), doc)
    assert Q.grade_all(counts) == {
      "PageRank": { "rate": 67, "mental": "확실", "means": "그래프에서 중요한 점을 매기는 방법" },
    }


def test_collect_은_용어_사전_없이_돌지_않는다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nRenderer 를 고친다.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"), str(plan)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "terms-db.json" in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def test_collect_은_봉인_없는_용어_사전을_거부한다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo = tmp_path / "대상"
    (repo / "docs" / "codegraph").mkdir(parents=True)
    db = repo / "docs" / "codegraph" / "terms-db.json"
    db.write_text("{}", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"), str(plan), str(db)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "manifest.json 이 없다" in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def _sealed_target(tmp_path, under=""):
    """`pkg/a.py` 하나와 그 용어 사전을 봉인해 커밋한 대상 저장소. `(대상, docs/codegraph)` 를 돌려준다.

    `under` 를 주면 그 폴더가 git 뿌리이고 대상은 그 아래 `대상/` 이다.
    """
    import hashlib, subprocess
    top = tmp_path / under if under else tmp_path / "대상"
    repo = top / "대상" if under else top
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    pub = repo / "docs" / "codegraph"
    pub.mkdir(parents=True)
    rec = {"kind": "function", "module": "pkg", "where": "pkg/a.py:1", "means": "하나를 돌려준다.",
           "uses": [], "neighbors": [], "source": "reading"}
    (pub / "terms-db.json").write_text(json.dumps({"f": rec}, ensure_ascii=False), encoding="utf-8")

    def git(*a: str) -> None:
        subprocess.run(["git", "-C", str(top), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                       check=True, capture_output=True)

    git("init", "-q")
    blob = subprocess.run(["git", "-C", str(repo), "hash-object", "pkg/a.py"],
                          capture_output=True, text=True).stdout.strip()
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "p", "source_commit": "s",
           "source_exts": [".py"], "skip_dirs": [".git", "__pycache__", "node_modules", "out"],
           "artifacts": {"terms-db": [{"path": "docs/codegraph/terms-db.json",
                                       "sha256": hashlib.sha256((pub / "terms-db.json").read_bytes()).hexdigest()}]},
           "inputs": {"pkg/a.py": blob}}
    (pub / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "init")
    return repo, pub


def _collect(tmp_path, db):
    """`collect.py <plan> <db>` 를 tmp_path 에서 돌린다. 계획서는 용어 `f` 를 부른다."""
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nf 를 고친다.\n", encoding="utf-8")
    return subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"), str(plan), str(db)],
                          capture_output=True, text=True, cwd=tmp_path)


def test_collect_은_낡은_파일의_용어에_stale_을_표시하고_evidence_를_싣는다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo, pub = _sealed_target(tmp_path)
    (repo / "pkg" / "a.py").write_text("def f():\n    return 2\n", encoding="utf-8")     # 봉인 뒤 바뀜
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nf 를 고친다.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"),
                        str(plan), str(pub / "terms-db.json")], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0 and "경고" in r.stderr
    got = json.loads((tmp_path / "term-candidates.json").read_text(encoding="utf-8"))
    assert got["known"]["f"]["stale"] is True
    assert got["evidence"]["stale"] == ["바뀜 pkg/a.py"] and got["evidence"]["uncommitted"] is False


def test_collect_은_봉인_자리가_아닌_용어_사전을_거부한다(tmp_path):
    """봉인은 멀쩡해도 받은 파일이 봉인된 그 파일이 아니면 시험을 내지 않는다."""
    import os, shutil, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo, pub = _sealed_target(tmp_path)
    raw = repo / "out" / "codegraph-raw"
    raw.mkdir(parents=True)
    shutil.copyfile(pub / "terms-db.json", raw / "terms-db.json")
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nf 를 고친다.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"),
                        str(plan), str(raw / "terms-db.json")], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "봉인된 용어 사전이 아니다" in r.stderr
    assert "봉인 자리는" in r.stderr and os.path.join("docs", "codegraph", "terms-db.json") in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def test_collect_은_내용만_고친_용어_사전을_거부한다(tmp_path):
    """계약 꼴은 지키고 뜻만 바꾼 봉인 — 정답지가 봉인과 다르면 시험을 내지 않는다."""
    repo, pub = _sealed_target(tmp_path)
    rec = json.loads((pub / "terms-db.json").read_text(encoding="utf-8"))
    rec["f"]["means"] = "둘을 돌려준다."
    (pub / "terms-db.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    r = _collect(tmp_path, pub / "terms-db.json")
    assert r.returncode == 1 and "봉인 뒤 바뀌었다 — docs/codegraph/terms-db.json" in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def test_collect_은_git_하위_폴더의_대상도_받는다(tmp_path):
    """봉인 자리는 git 뿌리가 아니라 받은 파일의 세 단계 위 폴더(대상 저장소)를 기준으로 본다."""
    repo, pub = _sealed_target(tmp_path, under="모노")
    r = _collect(tmp_path, pub / "terms-db.json")
    assert r.returncode == 0, r.stderr
    got = json.loads((tmp_path / "term-candidates.json").read_text(encoding="utf-8"))
    assert "f" in got["known"] and got["evidence"]["stale"] == []


def test_collect_은_git_밖에서_봉인_자리를_엉뚱하게_안내하지_않는다(tmp_path):
    import os
    outside = tmp_path / "밖"
    (outside / "docs" / "codegraph").mkdir(parents=True)
    db = outside / "docs" / "codegraph" / "terms-db.json"
    db.write_text("{}", encoding="utf-8")
    r = _collect(tmp_path, db)                          # 자리는 맞고 봉인이 없다
    assert r.returncode == 1 and "manifest.json 이 없다" in r.stderr
    assert str(outside / "docs" / "codegraph" / "manifest.json") in r.stderr
    assert os.path.join("docs", "codegraph", "docs", "codegraph") not in r.stderr
    other = tmp_path / "다른" / "terms-db.json"         # 자리가 틀렸다
    other.parent.mkdir()
    other.write_text("{}", encoding="utf-8")
    r = _collect(tmp_path, other)
    assert r.returncode == 1 and "봉인된 용어 사전이 아니다" in r.stderr
    assert "봉인 자리는 " + os.path.join("<대상>", "docs", "codegraph", "terms-db.json") in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()
