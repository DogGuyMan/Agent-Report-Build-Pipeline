# <include file="machine/comments.xml" path="//term[@id='quiz.py']"/>
# 객관식 답안을 채점하는 스크립트. 사람에게 묻지 않는다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import math
import sys
import os
import json
import re
from typing import Any, cast

QUESTIONS_PER_TERM = 3
CHOICES_PER_QUESTION = 5

# <include file="machine/comments.xml" path="//term[@id='runner.term.quiz.flatten_questions']"/>
# 중첩된 문항지를 한 줄로 펴고 QNum 을 1부터 매긴다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def flatten_questions(doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    terms = doc.get("terms", [])
    if not isinstance(terms, list):
        terms = []
    for entry in terms:
        if not isinstance(entry, dict):
            entry = {}
        term = str(entry.get("term", "")).strip()
        means = str(entry.get("means", ""))
        questions = entry.get("questions", [])
        if not isinstance(questions, list):
            questions = []
        for q in questions:
            if not isinstance(q, dict):
                q = {}
            ans = q.get("answer")
            parsed_ans = ans + 1 if isinstance(ans, int) and not isinstance(ans, bool) else None
            out.append({
                "QNum": len(out) + 1,
                "Term": term,
                "Question": str(q.get("ask", "")),
                "Answer": parsed_ans,
                "Means": means,
                "Raw": q,
            })
    return out

# <include file="machine/comments.xml" path="//term[@id='runner.term.quiz.choice_number']"/>
# UserAns 를 보기 번호로 읽는다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def choice_number(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if re.fullmatch(r"^\d+$", text, re.ASCII):
        return int(text)
    return None

# <include file="machine/comments.xml" path="//term[@id='runner.term.quiz.tally_sheet']"/>
# 채운 기입란을 문항지와 대조해 용어마다 맞힌 수를 센다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def tally_sheet(sheet: dict[str, Any], doc: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    problems: list[str] = []
    counts: dict[str, dict[str, Any]] = {}
    terms = doc.get("terms", [])
    if not isinstance(terms, list):
        terms = []
    for entry in terms:
        if not isinstance(entry, dict):
            entry = {}
        term = str(entry.get("term", "")).strip()
        if term:
            counts[term] = {"correct": 0, "dontKnow": 0, "means": str(entry.get("means", ""))}
            
    got = sheet.get("questions")
    if not isinstance(got, list):
        return counts, ["기입란 파일이 아니다 — `questions` 배열이 없다"]
        
    byNum: dict[int, dict[str, Any]] = {}
    for i, rec in enumerate(got):
        if not isinstance(rec, dict):
            rec = {}
        num = rec.get("QNum")
        if not isinstance(num, int) or isinstance(num, bool):
            problems.append(f"{i + 1}번째 칸 — QNum 이 정수가 아니다: {json.dumps(num, ensure_ascii=False)}")
            continue
        if num in byNum:
            problems.append(f"{num}번 문항의 답안이 둘 이상이다")
        byNum[num] = rec
        
    for q in flatten_questions(doc):
        qnum = cast(int, q["QNum"])
        rec = byNum.get(qnum)
        if rec is not None:
            del byNum[qnum]
            
        if rec is None:
            problems.append(f"{qnum}번({q['Term']}) — 문항은 냈는데 답안이 없다")
            continue
            
        rec_term = str(rec.get("Term", ""))
        if rec_term != q["Term"]:
            problems.append(f"{qnum}번 — 용어가 어긋난다. 문항지는 {json.dumps(q['Term'], ensure_ascii=False)} 인데 답안은 {json.dumps(rec_term, ensure_ascii=False)} 이다")
            continue
            
        rec_question = str(rec.get("Question", ""))
        if rec_question != q["Question"]:
            problems.append(f"{qnum}번({q['Term']}) — 물음 문구가 문항지와 다르다")
            continue
            
        ans = choice_number(rec.get("UserAns"))
        if ans is None:
            problems.append(f"{qnum}번({q['Term']}) — UserAns 가 비었다. 안 푼 것을 \"모르겠다\" 로 세지 않는다")
            continue
            
        if ans < 1 or ans > CHOICES_PER_QUESTION:
            problems.append(f"{qnum}번({q['Term']}) — UserAns 가 보기 밖이다(1~{CHOICES_PER_QUESTION}): {ans}")
            continue
            
        bucket = counts.get(cast(str, q["Term"]))
        if not bucket:
            continue
            
        if ans == CHOICES_PER_QUESTION:
            bucket["dontKnow"] += 1
        elif ans == q["Answer"]:
            bucket["correct"] += 1
            
    for num in sorted(list(byNum.keys())):
        problems.append(f"{num}번 — 내지 않은 문항의 답안이 있다")
        
    return counts, problems

# <include file="machine/comments.xml" path="//term[@id='runner.term.quiz.grade_one']"/>
# 한 용어의 답안을 채점한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def grade_one(counts: dict[str, Any]) -> dict[str, Any]:
    correct = cast(int, counts.get("correct", 0))
    dont_know = cast(int, counts.get("dontKnow", 0))
    rate = math.floor((correct / QUESTIONS_PER_TERM) * 100 + 0.5)
    
    if dont_know >= 2:
        mental = "모름"
    elif correct >= 2:
        mental = "확실"
    else:
        mental = "모름"
        
    return {"rate": rate, "mental": mental}

# <include file="machine/comments.xml" path="//term[@id='runner.term.quiz.grade_all']"/>
# 답안 전체를 채점한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def grade_all(answers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for term, a in answers.items():
        res = grade_one(a)
        res["means"] = str(a.get("means", ""))
        out[term] = res
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith("quiz.py"):
        sys.argv.pop(1)
    
    args = sys.argv[1:]
    if args and args[0] == "grade":
        args.pop(0)
        
    if len(args) < 2:
        print("사용법 — report-term grade <answers.json> <questions.json>", file=sys.stderr)
        print("  answers.json  — 실행기가 깐 기입란(answer-sheet.json)의 UserAns 를 채운 것", file=sys.stderr)
        print("  questions.json — 정답이 든 문항지. 사람은 풀기 전에 열지 않는다", file=sys.stderr)
        print("  문항 작성과 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다.", file=sys.stderr)
        sys.exit(1)
        
    answers_file, questions_file = args[0], args[1]
    
    with open(answers_file, "r", encoding="utf-8") as f:
        # ⚠ cast — json.load 의 반환값(Any)을 우리가 아는 모양으로 강제한다.
        sheet = cast(dict[str, Any], json.load(f))
    with open(questions_file, "r", encoding="utf-8") as f:
        # ⚠ cast — json.load 의 반환값(Any)을 우리가 아는 모양으로 강제한다.
        doc = cast(dict[str, Any], json.load(f))
        
    counts, problems = tally_sheet(sheet, doc)
    if problems:
        print("채점하지 않는다 — 채운 기입란이 문항지와 맞지 않는다:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)
        
    graded = grade_all(counts)
    path = os.path.join(os.getcwd(), "term-grades.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(graded, ensure_ascii=False, indent=2) + "\n")
        
    tally = {"확실": 0, "애매": 0, "모름": 0}
    for g in graded.values():
        val = str(g["mental"])
        tally[val] = tally.get(val, 0) + 1
        
    print(path)
    print(f"  확실 {tally['확실']} · 애매 {tally['애매']} · 모름 {tally['모름']}")
