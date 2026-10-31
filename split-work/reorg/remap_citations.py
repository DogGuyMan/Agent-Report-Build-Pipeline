#!/usr/bin/env python3
"""문서와 terms-reading.json 의 경로 · `파일:줄` 인용 · 레코드 id 를 새 구조로 옮긴다.
줄 번호는 strip_blocks.py 가 남긴 지운 줄 기록으로 결정론으로 다시 센다. 아카이브(docs/handoffs · superpowers · my.self · decisions · overturn)는 건드리지 않는다."""
import json
import os
import re
import subprocess
import sys

from reorg_lib import REMOVED, ROOT, TOKEN, dotted_map, load_map, map_dotted, map_rel, map_token, repo_key

DOC_PREFIXES = ("docs/wiki/", "docs/diagrams/", ".claude/agents/", ".gemini/", ".agents/rules/")
DOC_EXACT = {"CLAUDE.md", "ARCHITECTURE.md", "README.md", "docs/CLAUDE.md", "codewiki/CLAUDE.md", "term/CLAUDE.md", "spec/CLAUDE.md",
             "spec/typescript/CLAUDE.md", "core/CLAUDE.md", "tools/CLAUDE.md", "test/CLAUDE.md", "qa/CLAUDE.md", "resource/CLAUDE.md",
             ".claude/CLAUDE.md", ".claude/skills/spec-review-dashboard/SKILL.md", ".claude/skills/term-benchmark/SKILL.md",
             ".agents/skills/codebase-terms-survey/SKILL.md", "qa/evals/README.md", "split-work/README.md",
             "docs/contract-mode1-artifacts.md", "requirements.txt"}
READING = "resource/codewiki/terms-reading.json"


def remap_line(old_tok: str, n: int, removed: dict[str, list[int]], report: list[str], where: str) -> int:
    """지운 줄 수만큼 올린다. 지운 줄 자체를 가리켰으면(선언 위의 include 블록을 인용한 경우) 그 아래 첫 남은 줄 — 선언 — 로 간다."""
    _, key = repo_key(old_tok)
    rm = removed.get(key, [])
    new = n - sum(1 for r in rm if r < n)
    if n in rm:
        report.append(f"{where}: {old_tok}:{n} 은 지운 블록 안이었다 → 그 아래 선언 줄 {new} 로")
    return new


def main() -> int:
    moved, deleted = load_map()
    dot = dotted_map(moved)
    with open(REMOVED, encoding="utf-8") as f:
        removed: dict[str, list[int]] = json.load(f)
    report: list[str] = []

    def sub(m: re.Match[str], where: str) -> str:
        old = m.group("path")
        new = map_token(old, moved, report, where)
        if m.group("ln") is None:
            return new
        a = remap_line(old, int(m.group("a")), removed, report, where)
        if m.group("b") is None:
            return f"{new}:{a}"
        b = remap_line(old, int(m.group("b")), removed, report, where)
        return f"{new}:{a}{m.group('sep')}{b}"

    tracked = [l for l in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n") if l]
    changed = 0
    for rel in tracked:
        if not (rel.startswith(DOC_PREFIXES) or rel in DOC_EXACT):
            continue
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:      # docs/diagrams 의 png
            continue
        new = TOKEN.sub(lambda m: sub(m, rel), text)
        if new != text:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)
            changed += 1

    # terms-reading.json — 같은 꼴로 다시 쓴다(indent=1 · 끝 줄바꿈 없음). 먼저 변경 없는 왕복이 바이트 동일한지 본다.
    rp = os.path.join(ROOT, READING)
    with open(rp, encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    assert json.dumps(data, ensure_ascii=False, indent=1) == raw, "terms-reading.json 의 꼴이 indent=1 이 아니다 — dump 인자를 맞춘다"

    def map_where(w: str) -> str:
        return TOKEN.sub(lambda m: sub(m, READING), w)

    def map_id(s: str) -> str:
        return map_rel(s, moved) if "/" in s else map_dotted(s, dot)

    out: dict[str, dict] = {}
    dropped: list[str] = []
    for tid, rec in data.items():
        if repo_key(rec["where"].split(":")[0])[1] in deleted:   # xmldoc.py · test_xmldoc.py · comments.xml 의 레코드 — 파일과 함께 지운다
            dropped.append(tid)
            continue
        rec = dict(rec)
        rec["where"] = map_where(rec["where"])
        rec["module"] = map_id(rec["module"])
        rec["uses"] = [{**u, "to": map_id(u["to"]), "where": map_where(u["where"])} for u in rec.get("uses", [])]
        out[map_id(tid)] = rec
    assert len(out) + len(dropped) == len(data), "id 가 겹쳤다"
    with open(rp, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1))
    unchanged_ids = sorted(t for t in data if map_id(t) == t and ("/" in t or "." in t) and not t.startswith(("bin", "docs/", "out/", "tools")))
    print("고친 문서:", changed)
    print("지운 파일의 레코드(함께 지웠다):", len(dropped))
    print("옮기지 못한 id(갈라진 디렉토리 이름 등):", unchanged_ids[:40])
    print("\n".join(sorted(set(report))) or "블록 안 인용 · 손볼 상대 경로 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
