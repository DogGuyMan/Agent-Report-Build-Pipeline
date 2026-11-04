import re
import os
import sys
import json
import subprocess
from typing import Any, TypedDict, cast

import msgspec

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
EVIDENCE = os.path.join(_ROOT, "src", "common", "evidence.py")
SEALED_DB = os.path.join("docs", "codegraph", "terms-db.json")

# 본문에서 잡는 식별자 꼴 셋 — 결정 코드 · 산출물 파일명 · 배열 필드. `src/spec/python/viz/check.py` 에 같은 사본이 있다(`qa/gates/test_rule_copies.py`).
TERM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b", re.ASCII),
    re.compile(r"\b[a-z][a-z0-9_-]*\.json\b", re.ASCII),
    re.compile(r"\b[a-z][A-Za-z0-9_]*\[\]", re.ASCII),
]


class EvidenceList(TypedDict):
    """`src/common/evidence.py --list` 가 stdout 에 내는 JSON. `stale_files` 는 봉인 뒤 움직인 소스 경로다."""
    manifest: str
    artifacts: list[str]
    stale: list[str]
    stale_files: list[str]
    uncommitted: bool
    superseded_by: dict[str, str] | None


def escape_re(s: str) -> str:
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\\g<0>', s)

def pick_terms(db: dict[str, Any], plan_text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, rec in db.items():
        tail = r"\b" if re.search(r"[A-Za-z0-9_]$", name) else ""
        pattern = r"\b" + escape_re(name) + tail
        if re.search(pattern, plan_text, re.ASCII):
            out[name] = rec
    return out

def find_new_concepts(db: dict[str, Any], plan_text: str) -> list[str]:
    known = set(db.keys())
    found: set[str] = set()
    for pat in TERM_PATTERNS:
        for m in pat.finditer(plan_text):
            if m.group(0) not in known:
                found.add(m.group(0))
    return sorted(list(found))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collect":
        sys.argv.pop(1)

    if len(sys.argv) < 3:
        print("사용법 — report-term collect <plan.md> <terms-db.json>", file=sys.stderr)
        print("  terms-db.json 은 Mode 1 이 대상 저장소 docs/codegraph/ 에 봉인해 낸다",
              file=sys.stderr)
        sys.exit(1)

    plan_path = sys.argv[1]
    db_path = os.path.abspath(sys.argv[2])
    real = os.path.realpath(db_path)
    if not real.endswith(os.sep + SEALED_DB):
        print("에러 — 봉인된 용어 사전이 아니다: %s — 봉인 자리는 %s"
              % (db_path, os.path.join("<대상>", SEALED_DB)), file=sys.stderr)
        sys.exit(1)
    # 봉인 자리는 대상 저장소 뿌리에서 세 단계 아래다 — 그 뿌리로 판정을 부른다.
    target = os.path.dirname(os.path.dirname(os.path.dirname(real)))
    # stderr 는 그대로 흘려 경고가 터미널에 보이게 하고, stdout 의 JSON 만 받는다.
    ev = subprocess.run([sys.executable, EVIDENCE, target, "--need", "terms-db", "--list"],
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
