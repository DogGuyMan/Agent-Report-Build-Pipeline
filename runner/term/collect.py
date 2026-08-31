# <include file="machine/comments.xml" path="//term[@id='collect.py']"/>
# 이 Plan 을 읽는 데 필요한 용어를 모으는 스크립트. Mode 1.5 의 1단계다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import re
import os
import sys
import json
from typing import Any, cast

def escape_re(s: str) -> str:
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\\g<0>', s)

# <include file="machine/comments.xml" path="//term[@id='runner.term.collect.pick_terms']"/>
# 코드베이스 용어 DB 중 Plan 본문에 실제로 등장하는 것만 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def pick_terms(db: dict[str, Any], plan_text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, rec in db.items():
        tail = r"\b" if re.search(r"[A-Za-z0-9_]$", name) else ""
        pattern = r"\b" + escape_re(name) + tail
        if re.search(pattern, plan_text, re.ASCII):
            out[name] = rec
    return out

# <include file="machine/comments.xml" path="//term[@id='runner.term.collect.find_new_concepts']"/>
# Plan 이 새로 만든 개념을 찾는다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def find_new_concepts(db: dict[str, Any], plan_text: str) -> list[str]:
    known = set(db.keys())
    found: set[str] = set()
    patterns = [
        r"\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b",
        r"\b[a-z][a-z0-9_-]*\.json\b",
        r"\b[a-z][A-Za-z0-9_]*\[\]",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, plan_text, re.ASCII):
            if m.group(0) not in known:
                found.add(m.group(0))
    return sorted(list(found))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collect":
        sys.argv.pop(1)
        
    if len(sys.argv) < 2:
        print("사용법 — report-term collect <plan.md> [terms-db.json]", file=sys.stderr)
        sys.exit(1)
        
    plan_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
        
    db: dict[str, Any] = {}
    if db_path and os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            # ⚠ cast — json.load 의 반환값(Any)을 우리가 아는 모양으로 강제한다.
            db = cast(dict[str, Any], json.load(f))
            
    known = pick_terms(db, plan_text)
    fresh = find_new_concepts(db, plan_text)
    
    out = {
        "plan": plan_path,
        "known": known,
        "newConcepts": fresh
    }
    path = os.path.join(os.getcwd(), "term-candidates.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
        
    print(path)
    print(f"  코드베이스 용어 {len(known)}개")
    print(f"  Plan 신규 개념 {len(fresh)}개 — 정답은 Plan 저자가 써야 한다")
    if fresh:
        print(f"    {', '.join(fresh)}")
