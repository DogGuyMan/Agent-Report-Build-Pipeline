# <include file="machine/comments.xml" path="//term[@id='collect.py']"/>
# 이 Plan 을 읽는 데 필요한 용어를 모으는 스크립트. Mode 1.5 의 1단계다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import re
import os
import sys
import json
import subprocess
from typing import Any, TypedDict, cast

import msgspec

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE = os.path.join(_ROOT, "machine", "evidence.py")
SEALED_DB = os.path.join("docs", "codegraph", "terms-db.json")


class EvidenceList(TypedDict):
    """`machine/evidence.py --list` 가 stdout 에 내는 JSON. `stale_files` 는 봉인 뒤 움직인 소스 경로다."""
    manifest: str
    artifacts: list[str]
    stale: list[str]
    stale_files: list[str]
    uncommitted: bool
    superseded_by: dict[str, str] | None


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

    if len(sys.argv) < 3:
        print("사용법 — report-term collect <plan.md> <terms-db.json>", file=sys.stderr)
        print("  terms-db.json 은 codebase-wiki 의 Mode 1 이 대상 저장소 docs/codegraph/ 에 봉인해 낸다",
              file=sys.stderr)
        sys.exit(1)

    plan_path = sys.argv[1]
    db_path = os.path.abspath(sys.argv[2])
    top = subprocess.run(["git", "-C", os.path.dirname(db_path), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip() or os.path.dirname(db_path)
    sealed_db = os.path.join(top, SEALED_DB)
    if os.path.realpath(db_path) != os.path.realpath(sealed_db):
        print("에러 — 봉인된 용어 사전이 아니다: %s — 봉인 자리는 %s" % (db_path, sealed_db), file=sys.stderr)
        sys.exit(1)
    # stderr 는 그대로 흘려 경고가 터미널에 보이게 하고, stdout 의 JSON 만 받는다.
    ev = subprocess.run([sys.executable, EVIDENCE, top, "--need", "terms-db", "--list"],
                        stdout=subprocess.PIPE, text=True)
    if ev.returncode != 0:
        print("에러 — 봉인된 Mode 1 결과가 없다. 정답지 없이는 시험을 낼 수 없다.", file=sys.stderr)
        sys.exit(1)
    listed = msgspec.json.decode(ev.stdout, type=EvidenceList)
    stale_files = set(listed["stale_files"])

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
    with open(db_path, "r", encoding="utf-8") as f:
        # ⚠ cast — json.load 의 반환값(Any)을 우리가 아는 모양으로 강제한다.
        db = cast(dict[str, Any], json.load(f))

    known = pick_terms(db, plan_text)
    for rec in known.values():
        if str(rec.get("where", "")).split(":")[0] in stale_files:
            rec["stale"] = True          # 봉인 뒤 바뀐 파일의 용어 — 출제자가 피하거나 표시한다
    fresh = find_new_concepts(db, plan_text)

    out = {
        "plan": plan_path,
        "known": known,
        "newConcepts": fresh,
        "evidence": {"manifest": listed["manifest"], "stale": listed["stale"],
                     "uncommitted": listed["uncommitted"],
                     "superseded_by": listed["superseded_by"]},
    }
    path = os.path.join(os.getcwd(), "term-candidates.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(path)
    print(f"  코드베이스 용어 {len(known)}개")
    print(f"  Plan 신규 개념 {len(fresh)}개 — 정답은 Plan 저자가 써야 한다")
    if fresh:
        print(f"    {', '.join(fresh)}")
