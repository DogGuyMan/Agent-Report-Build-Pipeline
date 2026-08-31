# <include file="machine/comments.xml" path="//term[@id='emit.py']"/>
# 채점 결과를 학습 노트와 용어집 두 갈래로 내보내는 스크립트.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import os
import sys
import json
from typing import Any, cast

# <include file="machine/comments.xml" path="//term[@id='runner.term.emit.to_terms_db']"/>
# Mode 2 로 넘길 용어집 DB를 가공한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def to_terms_db(graded: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for term, rec in graded.items():
        out[term] = {
            "TermMeans": str(rec.get("means", "")),
            "UserMentalValue": str(rec.get("mental", "")),
        }
    return out

# <include file="machine/comments.xml" path="//term[@id='runner.term.emit.to_study_note']"/>
# 사람이 읽는 학습 노트를 생성한다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def to_study_note(graded: dict[str, dict[str, Any]]) -> str:
    rows: list[tuple[str, dict[str, Any]]] = []
    for term, r in graded.items():
        if r.get("mental") != "확실":
            rows.append((term, r))
            
    def get_rate(x: tuple[str, dict[str, Any]]) -> int:
        return cast(int, x[1].get("rate", 0))
        
    rows.sort(key=get_rate)
    
    head = "# 용어 학습 노트\n\n실측으로 가려낸, 아직 확실하지 않은 용어들이다.\n\n"
    if not rows:
        return head + "학습할 용어가 없다. 전부 확실로 판정됐다.\n"
        
    body = "\n".join(
        f"## {term}\n\n- 이해도 — **{r.get('mental')}** (정답률 {r.get('rate')}%)"
        f"\n- 뜻 — {r.get('means')}\n"
        for term, r in rows
    )
    return head + body

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith("emit.py"):
        sys.argv.pop(1)
        
    args = sys.argv[1:]
    if args and args[0] == "emit":
        args.pop(0)
        
    if not args:
        print("사용법 — report-term emit <term-grades.json>", file=sys.stderr)
        sys.exit(1)
        
    file = args[0]
    with open(file, "r", encoding="utf-8") as f:
        # ⚠ cast — json.load 의 반환값(Any)을 우리가 아는 모양으로 강제한다.
        graded = cast(dict[str, dict[str, Any]], json.load(f))
        
    db_path = os.path.join(os.getcwd(), "terms.json")
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(to_terms_db(graded), ensure_ascii=False, indent=2) + "\n")
        
    note_path = os.path.join(os.getcwd(), "term-study-note.md")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(to_study_note(graded))
        
    n = len(graded)
    study = sum(1 for r in graded.values() if r.get("mental") != "확실")
    
    print(f"{db_path} — 용어 {n}개 (전부 실림)")
    print(f"{note_path} — 학습 대상 {study}개")
