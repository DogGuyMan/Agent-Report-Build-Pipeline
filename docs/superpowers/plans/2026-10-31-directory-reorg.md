# Directory Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the repository to the mode-first layout of `docs/superpowers/specs/2026-10-31-directory-reorg-design.md` (decision 0014) with no behaviour change, byte-identical outputs, and exact citation renumbering.

**Architecture:** Four one-off scripts under `split-work/reorg/` do the mechanical work — a path map (`pathmap.py`), a block stripper that records removed lines (`strip_blocks.py`), a mover (`apply_moves.py`), a path/import rewriter for code (`rewrite_paths.py`), and a citation remapper for documents and the survey record (`remap_citations.py`), sharing `reorg_lib.py`. Each task ends green and is one commit. Hand edits are limited to tuple-form path constants, gate lists, configuration files and the module `CLAUDE.md` restructure.

**Tech Stack:** Python 3.12+ (standard library only), git, the repository's existing gates (`pytest`, `pyright`, `tsc`, `node --test`, `tools/gen_readme.py`, `tools/doctor.py`), `split-work/capture.sh`.

**When to run:** after Phase M of the split plan rev.4 (R · A · K · M finished 2026-10-31, `main` merge `6c4009d`) and before Phase B (root `CLAUDE.md`, decision 0014). **Where:** the user's Mac, local session, on `main`. **Commits:** `[tag] : 한국어 제목` one line, ASCII punctuation only, no body (`personal-commit-messages`).

**This file** is the English original; `2026-10-31-directory-reorg.ko.md` is its Korean translation.

---

## File structure

| Path | Responsibility |
|---|---|
| `split-work/reorg/reorg_lib.py` | Shared: load the TSV map, the directory-prefix table, the dotted-name tables, the path regex |
| `split-work/reorg/pathmap.py` | Rules → `split-work/reorg/out/pathmap.tsv`; fails on unmapped files or target collisions |
| `split-work/reorg/strip_blocks.py` | Remove `# <include …/>` blocks; write `split-work/reorg/out/removed-lines.json` |
| `split-work/reorg/apply_moves.py` | `git mv` / `git rm` from the TSV; create package markers; delete empty directories |
| `split-work/reorg/rewrite_paths.py` | In code and configuration: path strings, directory prefixes, import statements, `ROOT` chains, `sys.path` directory names |
| `split-work/reorg/remap_citations.py` | In documents and `terms-reading.json`: paths **and** line numbers; record ids |
| `split-work/reorg/check_root_depth.py` | Verifier: every `ROOT`/`_ROOT` chain length equals path depth + 1 |
| `split-work/reorg/out/` | Git-ignored artifacts: TSV, removed-lines, baseline captures and gate logs |
| `codewiki/python/machine/reading_types.py` | New: the three TypedDicts `terms_db.py` used to import from `xmldoc.py` |

The scripts are temporary tooling like the rest of `split-work/` and are deleted with it after Phase B.

---

### Task 0: Preconditions and baseline

**Files:**
- Create: `split-work/reorg/out/` (git-ignored)
- Modify: `.gitignore`

- [ ] **Step 1: Confirm the starting point**

Run:
```bash
cd "$REPO_ROOT" && git switch main && git pull && git status --short && git log --oneline -3
grep -n 'K8' docs/handoffs/RESUME-2026-10-24-split-rev4-execution.md | head -3
```
Expected: clean tree; the resume document's §0 says K ✅ · M1 ✅ · M2 ✅ (🔵 2026-10-31) and Phase B has not started (no `codebase-wiki` repository, Mode 1 still in this tree). If Phase B has started, stop — this plan runs before it.

- [ ] **Step 2: Ignore the reorg artifacts**

Append to `.gitignore`:
```
# 디렉토리 정리(결정 0014) 일회용 스크립트의 산출물 — 경로 지도 · 지운 줄 기록 · 기준선 캡처
split-work/reorg/out/
```

- [ ] **Step 3: Record the gate baseline**

Run:
```bash
mkdir -p split-work/reorg/out
.venv/bin/python -m pytest -q 2>&1 | tail -3 | tee split-work/reorg/out/baseline-pytest.txt
npm test 2>&1 | tail -3 | tee split-work/reorg/out/baseline-npm-test.txt
npm run typecheck && npm run typecheck:py 2>&1 | tail -2 | tee split-work/reorg/out/baseline-pyright.txt
.venv/bin/python tools/gen_readme.py --check machine runner viz tools && npm run doctor | tail -3
```
Expected: the numbers of root `CLAUDE.md` "게이트 여섯" as updated by Phase K (two known reds: wiki drift, layer distribution). Write them down.

- [ ] **Step 4: Record the output baseline and the wiki check baseline**

Run:
```bash
.venv/bin/python bin/report-wiki prep .
split-work/capture.sh "$PWD" split-work/reorg/out/before && ls split-work/reorg/out/before | wc -l
.venv/bin/python bin/report-wiki check . > split-work/reorg/out/baseline-wiki-check.txt 2>&1; tail -3 split-work/reorg/out/baseline-wiki-check.txt
.venv/bin/python machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading machine/terms-reading.json > split-work/reorg/out/baseline-terms-db.txt 2>&1; tail -3 split-work/reorg/out/baseline-terms-db.txt
```
Expected: 31 captured files; the wiki check prints `L1 <n>/<f>` and `L2 <n>/<f>` lines — these two lines are the comparison target for Task 4.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "[update] : gitignore - split-work reorg 산출물"
```

---

### Task 1: Path map

**Files:**
- Create: `split-work/reorg/reorg_lib.py`, `split-work/reorg/pathmap.py`

- [ ] **Step 1: Write the shared library**

`split-work/reorg/reorg_lib.py`:
```python
"""디렉토리 정리(결정 0014) 스크립트들이 함께 쓰는 것 — 지도 읽기 · 디렉토리 접두사 표 · 점 표기 표 · 경로 토큰 정규식."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "split-work", "reorg", "out")
TSV = os.path.join(OUT, "pathmap.tsv")
REMOVED = os.path.join(OUT, "removed-lines.json")

# 디렉토리째 옮긴 것만 — 여러 자리로 갈라진 디렉토리(runner/ · viz/ · tools/ · test/ · config/ · runner/prompts/ · viz/templates/)는 없다.
# 긴 것이 먼저 맞아야 하므로 순서가 뜻을 갖는다.
DIRS = [
    ("runner/mode1/prompts/", "resource/codewiki/prompts/"),
    ("runner/mode1/", "codewiki/python/runner/mode1/"),
    ("runner/wiki/templates/", "resource/codewiki/templates/"),
    ("runner/wiki/", "codewiki/python/runner/wiki/"),
    ("runner/term/", "term/python/runner/term/"),
    ("machine/roslyn-dump/", "codewiki/csharp/roslyn-dump/"),
    ("machine/", "codewiki/python/machine/"),
    ("viz/src/", "spec/typescript/src/"),
    ("viz/templates/dot/", "resource/codewiki/templates/dot/"),
    ("viz/templates/report/", "resource/spec/templates/report/"),
    ("resources/samples/", "resource/codewiki/samples/"),
    ("resources/", "resource/codewiki/"),
    ("evals/runs/", "qa/evals/runs/"),
    ("evals/", "qa/evals/"),
    ("research_notes/", "docs/research/"),
    ("reports/", "docs/research/"),
]
# Task 3 이 손으로 먼저 옮기는 문서 다섯 — 지도(TSV)에는 "그대로" 로 적히므로 여기서 따로 안다.
EXTRA = {
    "docs/analysis-2026-08-31-cpp-collectors.md": "docs/notes/analysis-2026-08-31-cpp-collectors.md",
    "docs/2026-09-19-mode1-역대-실측과-패치-이력.md": "docs/notes/2026-09-19-mode1-역대-실측과-패치-이력.md",
    "docs/2패스개선.md": "docs/notes/2패스개선.md",
    "runner/runner_presudo.md": "docs/notes/runner_presudo.md",
    "remain-process-merged.md": "docs/handoffs/remain-process-merged.md",
}
# 점 표기 모듈 id 로도 쓰이는 디렉토리 — 파이썬 패키지인 것만.
DOTTED_DIRS = {a.rstrip("/").replace("/", "."): b.rstrip("/").replace("/", ".")
               for a, b in DIRS if a in ("runner/mode1/", "runner/wiki/", "runner/term/", "machine/")}

# 경로 토큰 — 빗금이 하나 이상 있는 낱말. 앞에 식별자 글자가 없어야 한다. 뒤에 `:줄` 또는 `:줄-줄` 이 붙을 수 있다.
TOKEN = re.compile(r"(?<![A-Za-z0-9_\-])(?P<path>(?:[A-Za-z0-9_.$\-]+/)+[A-Za-z0-9_.\-]*)"
                   r"(?P<ln>:(?P<a>\d+)(?:(?P<sep>[-~])(?P<b>\d+))?)?")


def load_map() -> tuple[dict[str, str], set[str]]:
    """TSV → ({옛 경로: 새 경로}(옮긴 것만), {지운 경로})."""
    moved: dict[str, str] = {}
    deleted: set[str] = set()
    with open(TSV, encoding="utf-8") as f:
        for line in f:
            old, new = line.rstrip("\n").split("\t")
            if new == "DELETE":
                deleted.add(old)
            elif new != old:
                moved[old] = new
    return moved, deleted


def map_rel(rel: str, moved: dict[str, str]) -> str:
    """저장소 상대 경로 하나 — 파일 지도가 먼저, 없으면 디렉토리 접두사(DIRS 순서). 못 옮기면 그대로."""
    if rel in moved:
        return moved[rel]
    if rel in EXTRA:
        return EXTRA[rel]
    for a, b in DIRS:
        if rel.startswith(a):
            return b + rel[len(a):]
        if rel == a.rstrip("/"):          # 빗금 없는 디렉토리 이름 — 레코드의 module 값 꼴
            return b.rstrip("/")
    return rel


def repo_key(tok: str) -> tuple[list[str], str]:
    """토큰을 (앞머리 조각들, 저장소 상대 경로) 로 가른다. 첫 조각이 `.` 이나 `$변수` 면 그 다음부터가 저장소 상대 경로다."""
    segs = tok.split("/")
    start = 1 if segs[0] == "." or segs[0].startswith("$") else 0
    return segs[:start], "/".join(segs[start:])


def map_token(tok: str, moved: dict[str, str], report: list[str], where: str) -> str:
    """경로 토큰 하나를 옮긴다. `..` 로 시작하는 상대 경로는 파일 자리에 따라 뜻이 달라지므로 옮기지 않고 보고한다."""
    segs = tok.split("/")
    if segs[0] == "..":
        core = "/".join(s for s in segs if s not in ("..", "."))
        if map_rel(core, moved) != core:
            report.append(f"{where}: 상대 경로 {tok} 는 손으로 고친다")
        return tok
    head, rest = repo_key(tok)
    tail = ""
    while rest.endswith("."):
        rest, tail = rest[:-1], tail + "."
    new = map_rel(rest, moved)
    if new == rest:
        return tok
    return "/".join(head + [new + tail])


def dotted(path: str) -> str | None:
    return path[:-3].replace("/", ".") if path.endswith(".py") else None


def dotted_map(moved: dict[str, str]) -> dict[str, str]:
    """{옛 점 표기 모듈: 새 점 표기 모듈} — 파일 단위 + 패키지 디렉토리."""
    out: dict[str, str] = {}
    for o, n in moved.items():
        do, dn = dotted(o), dotted(n)
        if do and dn:
            out[do] = dn
    out.update(DOTTED_DIRS)
    return out


def map_dotted(name: str, table: dict[str, str]) -> str:
    """점 표기 이름 하나를 옮긴다 — 정확히 같거나, `옛.` 으로 시작하면 그 머리만 바꾼다. 긴 열쇠가 먼저."""
    if name in table:
        return table[name]
    for k in sorted(table, key=len, reverse=True):
        if name.startswith(k + "."):
            return table[k] + name[len(k):]
    return name
```

- [ ] **Step 2: Write the path map script**

`split-work/reorg/pathmap.py`:
```python
#!/usr/bin/env python3
"""디렉토리 정리(결정 0014)의 경로 지도. `split-work/reorg/out/pathmap.tsv` 를 쓴다 — 추적 파일마다 `옛<TAB>새` 또는 `옛<TAB>DELETE`.

지도에 없는 추적 파일이 있거나 두 원본이 한 목적지로 겹치면 쓰지 않고 1 로 끝난다.
설계 커밋에 있던 파일은 접두사 규칙을 따르고, 그 뒤 생긴 파일은 EXACT 나 PHASE_K 에 이름이 있어야 한다(새 파일은 의식해서 둔다).
"""
import collections
import os
import subprocess
import sys

from reorg_lib import DIRS, OUT, ROOT, TSV

DESIGN_COMMIT = "b0bdb50"

DELETE = {
    "machine/xmldoc.py", "machine/test_xmldoc.py", "machine/comments.xml", "docs/prompt/checklist.yaml",
    "runner/README.md", "machine/README.md", "viz/README.md", "tools/README.md",   # gen_readme 가 새 자리에 다시 만든다
}
EXACT = {
    "runner/run_mode1.py": "codewiki/python/runner/run_mode1.py",
    "runner/check_shard.py": "codewiki/python/runner/check_shard.py",
    "runner/run_mode1_5.py": "term/python/runner/run_mode1_5.py",
    "runner/run_grade.py": "term/python/runner/run_grade.py",
    "runner/run_mode2.py": "spec/python/runner/run_mode2.py",
    "runner/pipeline.py": "core/pipeline.py",
    "runner/measure.py": "core/measure.py",
    "runner/dispatch.py": "core/dispatch.py",
    "runner/__init__.py": "core/__init__.py",
    "runner/prompts/ask.md": "resource/term/prompts/ask.md",
    "runner/prompts/agent.md": "resource/spec/prompts/agent.md",
    "runner/mode1/faults.toml": "resource/codewiki/faults.toml",
    "runner/CLAUDE.md": "core/CLAUDE.md",
    "runner/runner_presudo.md": "docs/notes/runner_presudo.md",
    "runner/test_mode1.py": "test/codewiki/test_mode1.py",
    "runner/test_run_mode1.py": "test/codewiki/test_run_mode1.py",
    "runner/test_run_mode1_5.py": "test/term/test_run_mode1_5.py",
    "runner/test_run_grade.py": "test/term/test_run_grade.py",
    "runner/test_run_mode2.py": "test/spec/test_run_mode2.py",
    "runner/test_pipeline.py": "test/core/test_pipeline.py",
    "runner/test_measure.py": "test/core/test_measure.py",
    "runner/test_import_isolation.py": "test/core/test_import_isolation.py",
    "machine/terms-reading.json": "resource/codewiki/terms-reading.json",
    "machine/CLAUDE.md": "codewiki/CLAUDE.md",
    "machine/reading_types.py": "codewiki/python/machine/reading_types.py",   # Task 2 가 만든다
    "viz/render_modules.py": "codewiki/python/viz/render_modules.py",
    "viz/render_classes.py": "codewiki/python/viz/render_classes.py",
    "viz/demermaid.py": "codewiki/python/viz/demermaid.py",
    "viz/__init__.py": "spec/python/viz/__init__.py",
    "viz/CLAUDE.md": "spec/CLAUDE.md",
    "viz/src/CLAUDE.md": "spec/typescript/CLAUDE.md",
    "viz/svg.mjs": "spec/typescript/svg.mjs",
    "viz/svg.d.mts": "spec/typescript/svg.d.mts",
    "viz/lib.mjs": "spec/typescript/lib.mjs",
    "tools/python.py": "common/python.py",
    "tools/template.py": "common/template.py",
    "tools/test_template.py": "test/common/test_template.py",
    "tools/test_gen_readme.py": "test/tools/test_gen_readme.py",
    "config/mode1.toml": "resource/codewiki/config.toml",
    "config/report.toml": "resource/spec/config.toml",
    "resources/templates/OBSERVATION-template.md": "resource/codewiki/samples/OBSERVATION-template.md",
    "evals/README.md": "qa/evals/README.md",
    "remain-process-merged.md": "docs/handoffs/remain-process-merged.md",
    "docs/analysis-2026-08-31-cpp-collectors.md": "docs/notes/analysis-2026-08-31-cpp-collectors.md",
    "docs/2026-09-19-mode1-역대-실측과-패치-이력.md": "docs/notes/2026-09-19-mode1-역대-실측과-패치-이력.md",
    "docs/2패스개선.md": "docs/notes/2패스개선.md",
    "test/test_term.py": "test/term/test_term.py",
    "test/test_check.py": "test/spec/test_check.py",
    "test/test_init.py": "test/spec/test_init.py",
    "test/test_link_paths.py": "test/spec/test_link_paths.py",
    "test/test_wrap_terms.py": "test/spec/test_wrap_terms.py",
    "test/test_components.py": "test/spec/test_components.py",
    "test/test_graph_math.py": "test/spec/test_graph_math.py",
    "test/test_config.py": "test/spec/test_config.py",
    "test/svg.test.mjs": "test/spec/svg.test.mjs",
    "test/test_templates.py": "test/common/test_templates.py",
    "test/test_dispatch.py": "test/core/test_dispatch.py",
    "test/test_portability.py": "test/tools/test_portability.py",
    "test/test_docs_citations.py": "qa/gates/test_docs_citations.py",
    "test/test_no_any.py": "qa/gates/test_no_any.py",
    "test/test_prompt_resources.py": "qa/gates/test_prompt_resources.py",
    "test/test_wiki.py": "qa/gates/test_wiki.py",
}
# 분리 계획 rev.4 의 Phase K 가 설계 커밋 뒤에 더한 파일(🔵 `6c4009d`). 봉인 쪽(manifest · seal)은 Mode 1, 계약 읽기(evidence · contract_types)는
# Mode 1.5 와 2 가 함께 읽으므로 common/. 없는 이름은 무시된다.
PHASE_K = {
    "machine/manifest.py": "codewiki/python/machine/manifest.py",
    "machine/test_manifest.py": "test/codewiki/test_manifest.py",
    "runner/mode1/seal.py": "codewiki/python/runner/mode1/seal.py",
    "machine/contract_types.py": "common/contract_types.py",
    "machine/evidence.py": "common/evidence.py",
    "machine/test_evidence.py": "test/common/test_evidence.py",
    "tools/gen_contract_types.py": "tools/gen_contract_types.py",
    "tools/test_gen_contract_types.py": "test/tools/test_gen_contract_types.py",
    "tools/gen_contract.py": "tools/gen_contract.py",
    "tools/test_gen_contract.py": "test/tools/test_gen_contract.py",
}
PREFIX = [("machine/test_", "test/codewiki/test_")] + DIRS + [("viz/", "spec/python/viz/")]
STAY_PREFIX = ("bin/", "tools/", "docs/", "split-work/", "contracts/", ".agents/", ".claude/", ".gemini/", ".github/")
STAY_EXACT = {"CLAUDE.md", "ARCHITECTURE.md", "README.md", "package.json", "package-lock.json", "pyrightconfig.json",
              "tsconfig.json", "requirements.txt", "skills-lock.json", ".gitignore", "test/CLAUDE.md"}


def git(*args: str) -> list[str]:
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return [l for l in r.stdout.split("\n") if l]


def target(path: str, existed: bool) -> str | None:
    if path in DELETE:
        return "DELETE"
    if path in EXACT:
        return EXACT[path]
    if path in PHASE_K:
        return PHASE_K[path]
    if existed:
        for a, b in PREFIX:
            if path.startswith(a):
                return b + path[len(a):]
    if path in STAY_EXACT or path.startswith(STAY_PREFIX):
        return path
    return None


def main() -> int:
    tracked = git("ls-files")
    existed = set(git("ls-tree", "-r", "--name-only", DESIGN_COMMIT))
    rows = [(f, target(f, f in existed)) for f in tracked]
    unmapped = [f for f, t in rows if t is None]
    counts = collections.Counter(t for _, t in rows if t not in (None, "DELETE"))
    collisions = sorted(t for t, c in counts.items() if c > 1)
    if unmapped or collisions:
        print("지도에 없는 파일(EXACT · PHASE_K · STAY 중 하나에 넣는다):", *unmapped, sep="\n  ")
        print("목적지가 겹치는 파일:", *collisions, sep="\n  ")
        return 1
    os.makedirs(OUT, exist_ok=True)
    with open(TSV, "w", encoding="utf-8") as f:
        for old, new in rows:
            f.write(f"{old}\t{new}\n")
    moved = sum(1 for o, n in rows if n not in ("DELETE", o))
    deleted = sum(1 for _, n in rows if n == "DELETE")
    print(f"추적 {len(rows)} · 이동 {moved} · 삭제 {deleted} · 그대로 {len(rows) - moved - deleted} → {TSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run it and classify every unmapped file**

Run: `cd split-work/reorg && ../../.venv/bin/python pathmap.py; cd ../..`
Expected on the design commit (🔵 2026-10-31): `추적 480 · 이동 192 · 삭제 8 · 그대로 280`; on `6c4009d` (after Phase K · M) the tracked count is 493 and the six Phase K files are mapped by `PHASE_K`. If the script lists unmapped files, add each to `EXACT` (or `PHASE_K` / `STAY_PREFIX`) with the placement rule of the spec §4, and show the user the additions before continuing.

- [ ] **Step 4: Commit**

```bash
git add split-work/reorg/reorg_lib.py split-work/reorg/pathmap.py
git commit -m "[add] : split-work reorg - 경로 지도 스크립트"
```

---

### Task 2: Delete the xmldoc remnants, recording removed lines

**Files:**
- Create: `split-work/reorg/strip_blocks.py`, `machine/reading_types.py`
- Modify: `machine/terms_db.py` (one import line), `machine/test_terms_db.py` (one import line), `machine/CLAUDE.md` (xmldoc row)
- Delete: `machine/xmldoc.py`, `machine/test_xmldoc.py`, `machine/comments.xml`

- [ ] **Step 1: Write the stripper**

`split-work/reorg/strip_blocks.py`:
```python
#!/usr/bin/env python3
"""폐지된 xmldoc 주입기가 남긴 `# <include …/>` 블록(표식 · 뜻 줄 · 선택적 의존 줄)을 전부 걷어내고,
파일마다 지운 1-based 줄 번호를 `split-work/reorg/out/removed-lines.json` 에 남긴다.
블록 경계는 machine/xmldoc.py 의 block_extent() 와 같다 — 의존 줄이 실제로 있는지 세어 더한다."""
import json
import os
import re
import subprocess
import sys

from reorg_lib import OUT, REMOVED, ROOT

INCLUDE_RE = re.compile(r'^\s*(#|//)\s*<include file="machine/comments\.xml"')
USES_LINE_RE = re.compile(r"^\s*(?:#|//)\s*(?:\S+ — )?쓰는 것: ")
CODE_ROOTS = ("runner/", "machine/", "viz/", "tools/", "bin/", "test/")


def block_extent(lines: list[str], i: int) -> int:
    c = 0
    while i + c < len(lines) and INCLUDE_RE.match(lines[i + c]):
        c += 1
    n = 2 * c
    u = 0
    while u < c and i + n + u < len(lines) and USES_LINE_RE.match(lines[i + n + u]):
        u += 1
    return n + u


def strip(lines: list[str]) -> tuple[list[str], list[int], int]:
    out: list[str] = []
    removed: list[int] = []
    markers = 0
    i = 0
    while i < len(lines):
        if INCLUDE_RE.match(lines[i]):
            n = block_extent(lines, i)
            markers += sum(1 for k in range(n) if INCLUDE_RE.match(lines[i + k]))
            removed.extend(range(i + 1, i + n + 1))
            i += n
            continue
        out.append(lines[i])
        i += 1
    return out, removed, markers


def main() -> int:
    tracked = [l for l in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n") if l]
    record: dict[str, list[int]] = {}
    files = markers = lines_removed = 0
    for rel in tracked:
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        if "<include file=" not in text:
            continue
        if not rel.startswith(CODE_ROOTS):
            print("코드 밖에 include 표식이 있다 — 손으로 본다:", rel)
            continue
        lines = text.splitlines(keepends=True)
        out, removed, m = strip(lines)
        if not removed:
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write("".join(out))
        record[rel] = removed
        files += 1
        markers += m
        lines_removed += len(removed)
    os.makedirs(OUT, exist_ok=True)
    with open(REMOVED, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    print(f"파일 {files} · 표식 {markers} · 지운 줄 {lines_removed} → {REMOVED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create `machine/reading_types.py` with the three types verbatim from `machine/xmldoc.py`**

```python
"""전수조사 원본 `terms-reading.json` 의 모양. `does` 와 `confidence` 만 선택이고 나머지는 모든 레코드에 있다."""
from typing import NotRequired, TypedDict


class Use(TypedDict):
    """`uses[]` 한 칸 — 이 용어가 무엇을 쓰는가."""
    to: str
    kind: str
    label: str
    where: str
    source: NotRequired[str]


class Term(TypedDict):
    """용어 하나. 열쇠 이름은 json 의 것 그대로다."""
    kind: str
    means: str
    module: str
    source: str
    where: str
    uses: list[Use]
    does: NotRequired[str]
    confidence: NotRequired[str]


# {용어 id: 레코드}. json 최상위가 이 모양이다.
Terms = dict[str, Term]
```
Before writing, diff the two class bodies against the current `machine/xmldoc.py` (`grep -n -A12 '^class Use\|^class Term' machine/xmldoc.py`) — Phase K may have added a field; copy what is there.

- [ ] **Step 3: Repoint the two imports (one line each)**

```bash
grep -n '^from xmldoc import Terms' machine/terms_db.py machine/test_terms_db.py
sed -i '' 's/^from xmldoc import Terms\(.*\)$/from reading_types import Terms\1/' machine/terms_db.py machine/test_terms_db.py
grep -rn 'xmldoc' machine/*.py runner tools viz test bin | grep -v '^machine/xmldoc.py\|^machine/test_xmldoc.py'
```
Expected after sed: only comment or docstring mentions remain (`machine/terms_db.py` "xmldoc.Term 이 정본" comment → change that comment to `reading_types.Term`; `machine/warmup.py` docstring mention stays — it describes the retired flow and is one word).

- [ ] **Step 4: Delete the three files, then strip the blocks**

The order matters — `xmldoc.py` and `test_xmldoc.py` contain markers themselves, and `git rm` refuses a file the stripper has just modified.

```bash
git rm -q machine/xmldoc.py machine/test_xmldoc.py machine/comments.xml
cd split-work/reorg && ../../.venv/bin/python strip_blocks.py; cd ../..
grep -rln '<include file=' --include='*.py' --include='*.mjs' --include='*.ts' --include='*.tsx' runner machine viz tools bin test | wc -l
```
Expected: `파일 71 · 표식 683 · 지운 줄 2049` on the design tree (🔵 2026-10-31 dry run; Phase K changes these only if it planted blocks, which root `CLAUDE.md` forbids); the final grep prints 0. The script also lists prose mentions of the marker outside code (`.gemini/PythonRule.md`, archive documents) — the archive stays as it is; `.gemini/PythonRule.md` is edited in Task 6.

- [ ] **Step 5: Edit the `machine/CLAUDE.md` row**

Replace the table row that begins `| \`xmldoc.py\` |` with:
```
| `reading_types.py` | `Use` · `Term` · `Terms` 형 — `terms-reading.json` 레코드의 모양. `terms_db.py` 가 import 한다. 주석 주입기 `xmldoc.py` 와 그 산출물 `comments.xml` 은 2026-10-31 에 지웠다(`docs/decisions/0010` · `0014`) |
```

- [ ] **Step 6: Gates**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -2        # baseline pass count minus the xmldoc tests; same two reds
npm run typecheck:py                                 # 0 errors
.venv/bin/python tools/gen_readme.py machine runner viz tools && .venv/bin/python tools/gen_readme.py --check machine runner viz tools
.venv/bin/python -m pytest test/test_docs_citations.py test/test_no_any.py test/test_prompt_resources.py -q
split-work/capture.sh "$PWD" split-work/reorg/out/after-strip && diff -r split-work/reorg/out/before split-work/reorg/out/after-strip && echo 같다
```
Expected: all green; `같다`. (README regeneration drops the `# <include>`-derived lines, which is why `gen_readme` runs before `--check`.)

- [ ] **Step 7: Commit**

```bash
git add -A machine runner viz tools bin test split-work/reorg/strip_blocks.py
git commit -m "[refactor] : xmldoc 잔재 삭제 - include 블록 686줄, xmldoc.py, comments.xml, 형은 reading_types.py 로"
```

---

### Task 3: Move documents (no code impact)

**Files:**
- Move: `reports/*`, `research_notes/**`, `remain-process-merged.md`, the three loose `docs/*.md`, `runner/runner_presudo.md`
- Delete: `docs/prompt/checklist.yaml`
- Modify: `docs/CLAUDE.md`

- [ ] **Step 1: Move with git**

```bash
mkdir -p docs/research docs/notes
git -c core.quotepath=off mv reports/* docs/research/ && git mv research_notes/* docs/research/
git mv remain-process-merged.md docs/handoffs/remain-process-merged.md
git -c core.quotepath=off mv docs/analysis-2026-08-31-cpp-collectors.md "docs/2026-09-19-mode1-역대-실측과-패치-이력.md" "docs/2패스개선.md" runner/runner_presudo.md docs/notes/
git rm -q docs/prompt/checklist.yaml
rmdir reports research_notes docs/prompt 2>/dev/null; git status --short | wc -l
```

- [ ] **Step 2: Update `docs/CLAUDE.md`**

In the table "무엇이 어디 있나", delete the row beginning `| \`prompt/\` |` and add after the `overturn/` row:
```
| `notes/` | 날짜 붙은 분석 · 실측 이력 · 러너 의사코드 — 한 세션의 관찰 기록 | ✗ |
| `research/` | ko-dev-terms 리서치 보고서와 조사 노트(루트의 `reports/` · `research_notes/` 를 2026-10-31 에 옮겼다) | ✗ |
```
In the "예외 넷" table delete the `prompt/` row and change the heading to `## 예외 셋 — 이건 열라고 있는 것이다`.

- [ ] **Step 3: Gates and commit**

```bash
.venv/bin/python -m pytest test/test_docs_citations.py -q && git add -A docs reports research_notes runner remain-process-merged.md
git commit -m "[docs] : 문서 폴더 정리 - reports, research_notes, 흩어진 분석을 docs 아래로"
```

---

### Task 4: Move code, resources and tests; rewrite paths and imports

**Files:**
- Create: `split-work/reorg/apply_moves.py`, `split-work/reorg/rewrite_paths.py`, `split-work/reorg/check_root_depth.py`, ten empty `__init__.py`
- Modify: everything the TSV moves; `pyrightconfig.json`, `tsconfig.json`, `package.json`, `.github/workflows/docs-gates.yml`, `tools/gen_readme.py`, `tools/setup.sh`, `bin/*`, the four gates, `split-work/capture.sh`

- [ ] **Step 1: Write the mover**

`split-work/reorg/apply_moves.py`:
```python
#!/usr/bin/env python3
"""pathmap.tsv 를 git mv / git rm 으로 적용하고, 패키지 표식을 만들고, 빈 디렉토리를 지운다."""
import os
import shutil
import subprocess
import sys

from reorg_lib import ROOT, TSV

INIT = ["codewiki/__init__.py", "codewiki/python/__init__.py", "codewiki/python/runner/__init__.py", "codewiki/python/viz/__init__.py",
        "term/__init__.py", "term/python/__init__.py", "term/python/runner/__init__.py",
        "spec/__init__.py", "spec/python/__init__.py", "spec/python/runner/__init__.py", "common/__init__.py"]
OLD_ROOTS = ["runner", "machine", "viz", "config", "evals", "resources", "reports", "research_notes", "docs/prompt"]


def git(*args: str) -> None:
    subprocess.run(["git", "-c", "core.quotepath=off", *args], check=True, cwd=ROOT)


def main() -> int:
    with open(TSV, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f if l.strip()]
    for old, new in rows:
        if new == "DELETE":
            if os.path.exists(os.path.join(ROOT, old)):
                git("rm", "-q", old)
        elif new != old:
            os.makedirs(os.path.dirname(os.path.join(ROOT, new)), exist_ok=True)
            git("mv", old, new)
    for rel in INIT:
        p = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            open(p, "w").close()
        git("add", rel)
    for top in OLD_ROOTS:
        for dirpath, dirnames, _ in os.walk(os.path.join(ROOT, top), topdown=False):
            for d in dirnames:
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
            if os.path.isdir(dirpath) and not os.listdir(dirpath):
                os.rmdir(dirpath)
    left = [t for t in OLD_ROOTS if os.path.exists(os.path.join(ROOT, t))]
    print("남은 옛 디렉토리:", left or "없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write the code rewriter**

`split-work/reorg/rewrite_paths.py`:
```python
#!/usr/bin/env python3
"""코드 · 설정 · 스크립트 안의 옛 경로를 새 경로로 — 경로 토큰, import 문, ROOT 사슬, sys.path 의 디렉토리 이름.
줄 수를 바꾸지 않는다. 문서와 terms-reading.json 은 remap_citations.py 의 몫이다(줄 번호까지 옮긴다)."""
import os
import re
import subprocess
import sys

from reorg_lib import ROOT, TOKEN, dotted_map, load_map, map_dotted, map_token

TARGET_PREFIXES = ("bin/", "codewiki/", "term/", "spec/", "core/", "common/", "tools/", "test/", "qa/",
                   ".github/workflows/", "split-work/")
TARGET_EXACT = {"package.json", "pyrightconfig.json", "tsconfig.json", ".gitignore",
                "resource/spec/config.toml", "resource/codewiki/samples/OBSERVATION-template.md"}
SKIP_SUFFIX = (".png", ".svg", ".pdf", ".json", ".lock", ".csproj", ".cs")   # 설정 JSON 셋은 TARGET_EXACT 로 들어온다
IMPORT_RE = re.compile(r"^(\s*)(from|import)\s+([A-Za-z_][\w.]*)(.*)$")
FLAT_CORE = [
    (re.compile(r"^(\s*)import pipeline(\s*(?:#.*)?)$"), r"\1from core import pipeline\2"),
    (re.compile(r"^(\s*)import pipeline as (\w+)(\s*(?:#.*)?)$"), r"\1from core import pipeline as \2\3"),
    (re.compile(r"^(\s*)from pipeline import "), r"\1from core.pipeline import "),
    (re.compile(r"^(\s*)import measure(\s*(?:#.*)?)$"), r"\1from core import measure\2"),
    (re.compile(r"^(\s*)import measure as (\w+)(\s*(?:#.*)?)$"), r"\1from core import measure as \2\3"),
    (re.compile(r"^(\s*)from measure import "), r"\1from core.measure import "),
    (re.compile(r"^(\s*)import pipeline, measure(\s*(?:#.*)?)$"), r"\1from core import pipeline, measure\2"),
]
ROOT_CHAIN = re.compile(r"^(?P<head>\s*\w+\s*=\s*)(?P<chain>(?:os\.path\.dirname\()+)os\.path\.abspath\(__file__\)(?P<tail>\)+)(?P<rest>.*)$")
SYSPATH_DIR = re.compile(r'os\.path\.join\((ROOT|root|_ROOT), "(runner|machine|viz)"\)')
# 파일의 새 최상위 폴더 → sys.path 에 적힌 옛 디렉토리 이름 → 그 모듈들이 이제 사는 자리
MODE_DIRS = {
    "codewiki": {"runner": '"codewiki", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"codewiki", "python", "viz"'},
    "term": {"runner": '"term", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "spec": {"runner": '"spec", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "core": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "common": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "tools": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
}


def mode_of(new_rel: str) -> str:
    parts = new_rel.split("/")
    if parts[0] in ("test", "qa") and len(parts) > 1 and parts[1] in MODE_DIRS:
        return parts[1]
    return parts[0] if parts[0] in MODE_DIRS else "core"


def rewrite(text: str, new_rel: str, old_rel: str | None, moved: dict[str, str], dot: dict[str, str], report: list[str]) -> str:
    out: list[str] = []
    is_code = new_rel.endswith(".py") or new_rel.startswith("bin/")
    for line in text.split("\n"):
        line = TOKEN.sub(lambda m: map_token(m.group("path"), moved, report, new_rel) + (m.group("ln") or ""), line)
        if is_code:
            m = IMPORT_RE.match(line)
            if m:
                line = m.group(1) + m.group(2) + " " + map_dotted(m.group(3), dot) + m.group(4)
            for pat, rep in FLAT_CORE:
                line = pat.sub(rep, line)
            if old_rel is not None and old_rel != new_rel:
                m = ROOT_CHAIN.match(line)
                if m:
                    n = m.group("chain").count("os.path.dirname(")
                    if n == old_rel.count("/") + 1:
                        k = new_rel.count("/") + 1
                        line = m.group("head") + "os.path.dirname(" * k + "os.path.abspath(__file__)" + ")" * k + m.group("rest")
            md = MODE_DIRS[mode_of(new_rel)]
            line = SYSPATH_DIR.sub(lambda mm: "os.path.join(%s, %s)" % (mm.group(1), md[mm.group(2)]), line)
        out.append(line)
    return "\n".join(out)


def main() -> int:
    moved, _ = load_map()
    back = {n: o for o, n in moved.items()}
    dot = dotted_map(moved)
    report: list[str] = []
    tracked = [l for l in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n") if l]
    changed = 0
    for rel in tracked:
        if rel in TARGET_EXACT:
            pass
        elif not rel.startswith(TARGET_PREFIXES) or rel.endswith(SKIP_SUFFIX) or rel.startswith("resource/"):
            continue
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        new = rewrite(text, rel, back.get(rel), moved, dot, report)
        if new != text:
            assert new.count("\n") == text.count("\n"), rel
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)
            changed += 1
    print("고친 파일:", changed)
    print("\n".join(sorted(set(report))) or "손으로 볼 상대 경로 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Write the depth checker**

`split-work/reorg/check_root_depth.py`:
```python
#!/usr/bin/env python3
"""모든 .py 에서 `X = os.path.dirname(...os.path.abspath(__file__)...)` 사슬이 저장소 뿌리를 가리키는지 — 사슬 길이 == 깊이 + 1 — 를 본다.
자기 디렉토리(사슬 1)와 중간 디렉토리는 보고만 한다."""
import os
import re
import subprocess
import sys

from reorg_lib import ROOT

CHAIN = re.compile(r"^\s*(_?ROOT)\s*=\s*((?:os\.path\.dirname\()+)os\.path\.abspath\(__file__\)")


def main() -> int:
    bad: list[str] = []
    for rel in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "--", "*.py"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n"):
        if not rel or rel.startswith("split-work/"):
            continue
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                m = CHAIN.match(line)
                if m and m.group(2).count("os.path.dirname(") != rel.count("/") + 1:
                    bad.append(f"{rel}:{i}: {m.group(1)} 사슬 {m.group(2).count('os.path.dirname(')} ≠ 깊이+1 {rel.count('/') + 1}")
    print("\n".join(bad) or "ROOT 사슬 전부 맞다")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Move and rewrite**

```bash
cd split-work/reorg && ../../.venv/bin/python pathmap.py && ../../.venv/bin/python apply_moves.py && ../../.venv/bin/python rewrite_paths.py && ../../.venv/bin/python check_root_depth.py; cd ../..
git status --short | grep -c '^R'
```
Expected: `남은 옛 디렉토리: 없음`, `고친 파일: <n>`, `ROOT 사슬 전부 맞다`, and about 190 renames.

- [ ] **Step 5: Hand-edit the tuple-form path constants (one line → one line each)**

Find them: `grep -rnE 'os\.path\.join\((ROOT|root|_ROOT), "(runner|machine|viz|config|resources|tools)"' codewiki term spec core common tools qa test bin`. Apply:

| File | Old | New |
|---|---|---|
| `codewiki/python/runner/mode1/context.py` | `os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")` | `os.path.join(ROOT, "resource", "codewiki", "prompts")` (move the line below the `ROOT =` line if `ROOT` is defined later) |
| same | `os.path.join(ROOT, "config", "mode1.toml")` | `os.path.join(ROOT, "resource", "codewiki", "config.toml")` |
| same | `os.path.join(os.path.dirname(os.path.abspath(__file__)), "faults.toml")` | `os.path.join(ROOT, "resource", "codewiki", "faults.toml")` |
| same (`reading_path`) | `os.path.join(root, "machine", "terms-reading.json")` | `os.path.join(root, "resource", "codewiki", "terms-reading.json")` |
| `codewiki/python/runner/mode1/terms.py` | `os.path.join(root, "machine", "terms_db.py")` | `os.path.join(root, "codewiki", "python", "machine", "terms_db.py")` |
| `codewiki/python/runner/mode1/lang.py` (two sites) | `os.path.join(ctx.root, "machine", "lang_select.py")` | `os.path.join(ctx.root, "codewiki", "python", "machine", "lang_select.py")` |
| `codewiki/python/runner/check_shard.py` · `run_mode1.py` (multi-line `sys.path.insert`) | `os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine"` | `os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "codewiki", "python", "machine"` |
| `codewiki/python/runner/mode1/survey.py` (example record literal near `"where": "codewiki/python/machine/terms_db.py:…"`) | `"module": "machine"` | `"module": "codewiki.python.machine"` — the line number in that example is illustrative; leave it |
| `codewiki/python/runner/mode1/machine_stage.py` | `os.path.join(root, "runner", "wiki", script)` | `os.path.join(root, "codewiki", "python", "runner", "wiki", script)` |
| `codewiki/python/runner/wiki/build.py` | `os.path.join(ROOT, "runner", "wiki", "templates")` | `os.path.join(ROOT, "resource", "codewiki", "templates")` |
| same | `os.path.join(ROOT, "viz", "demermaid.py")` | `os.path.join(ROOT, "codewiki", "python", "viz", "demermaid.py")` |
| `codewiki/python/runner/wiki/check.py` | `os.path.join(ROOT, "machine", "verify_citations.py")` | `os.path.join(ROOT, "codewiki", "python", "machine", "verify_citations.py")` |
| `codewiki/python/runner/wiki/prep.py` | `os.path.join(ROOT, "machine", "pycalls.py")` · `"normalize.py"` · `"facts.py"` | `os.path.join(ROOT, "codewiki", "python", "machine", "<same>")` |
| same | `os.path.join(ROOT, "viz", "render_modules.py")` | `os.path.join(ROOT, "codewiki", "python", "viz", "render_modules.py")` |
| `codewiki/python/viz/render_modules.py` · `render_classes.py` | `os.path.join(_ROOT, "viz", "templates", "dot")` | `os.path.join(_ROOT, "resource", "codewiki", "templates", "dot")` |
| `term/python/runner/run_mode1_5.py` | `os.path.join(root, "runner", "term", name)` | `os.path.join(root, "term", "python", "runner", "term", name)` |
| same | `os.path.join(root, "runner", "run_mode1_5.py")` | `os.path.join(root, "term", "python", "runner", "run_mode1_5.py")` |
| same | `os.path.join(ROOT, "runner", "prompts")` | `os.path.join(ROOT, "resource", "term", "prompts")` |
| same (generated child script) | `os.path.join({root!r}, "runner")` | `os.path.join({root!r}, "term", "python", "runner")` |
| `spec/python/runner/run_mode2.py` | `os.path.join(ROOT, "config", "report.toml")` | `os.path.join(ROOT, "resource", "spec", "config.toml")` |
| same | `os.path.join(root, "viz", stage + ".py")` | `os.path.join(root, "spec", "python", "viz", stage + ".py")` |
| same | `os.path.join(ROOT, "runner", "prompts")` | `os.path.join(ROOT, "resource", "spec", "prompts")` |
| `spec/python/viz/build.py` · `init.py` | `os.path.join(ROOT, "viz", "templates", "report")` | `os.path.join(ROOT, "resource", "spec", "templates", "report")` |
| `spec/python/viz/init.py` | `os.path.join(ROOT, "config", "report.toml")` | `os.path.join(ROOT, "resource", "spec", "config.toml")` |
| `tools/gen_readme.py` | `os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine")` | `os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "codewiki", "python", "machine")` |

Then: `grep -rnE '"(runner|machine|viz|config|resources|evals)"' codewiki term spec core common tools qa test bin` — expected empty except prose in docstrings. 🔵 On the design tree the rewriter leaves exactly the sites of this table (dry run 2026-10-31).

- [ ] **Step 6: Configuration files**

`pyrightconfig.json` (whole file):
```json
{
  "include": ["codewiki", "term", "spec", "core", "common", "tools", "test", "qa"],
  "exclude": [
    "**/__pycache__",
    "**/node_modules",
    ".venv",
    "codewiki/csharp",
    "spec/typescript"
  ],

  "venvPath": ".",
  "venv": ".venv",
  "extraPaths": [".", "codewiki/python/runner", "codewiki/python/machine", "codewiki/python/viz",
                 "term/python/runner", "spec/python/runner", "spec/python/viz"],

  "pythonVersion": "3.14",
  "pythonPlatform": "All",
  "typeCheckingMode": "strict"
}
```
`tsconfig.json`: `"include": ["spec/typescript/src/**/*.ts", "spec/typescript/src/**/*.tsx"]`.
`package.json`: `"pretest": "node spec/typescript/lib.mjs"`.
`spec/typescript/lib.mjs`: `entryPoints: ["spec/typescript/src/index.ts"],`.
`tools/setup.sh`: `node spec/typescript/lib.mjs` (the rewriter already did this; verify with `grep -n lib.mjs tools/setup.sh`).
`.github/workflows/docs-gates.yml`:
```yaml
      - name: citations and no-Any
        run: python -m pytest qa/gates/test_docs_citations.py qa/gates/test_no_any.py -q

      # 디렉토리별 README.md 가 소스 독스트링과 같은가
      - name: README drift
        run: python tools/gen_readme.py --check codewiki/python/runner codewiki/python/machine codewiki/python/viz term/python/runner spec/python/runner spec/python/viz core common tools
```

- [ ] **Step 7: `tools/gen_readme.py`**

Replace `DIR_ROLE` and `BANNER`:
```python
BANNER = ("> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —\n"
          "> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py codewiki/python/runner codewiki/python/machine "
          "codewiki/python/viz term/python/runner spec/python/runner spec/python/viz core common tools`\n")

# 디렉토리 한 줄. 여기만 사람이 쓴다 — 나머지는 전부 소스에서 온다.
DIR_ROLE = {
    "codewiki/python/runner": "Mode 1 실행기와 단계. 코드베이스를 읽어 위키를 만드는 순서를 잡고 자식 프로세스를 띄운다.",
    "codewiki/python/machine": "정적 수집 · 인용 검증 · 측정. 산문을 쓰지 않고 판정하지 않는다.",
    "codewiki/python/viz": "코드 지도와 위키의 그림을 Graphviz · Mermaid 로 굽는다.",
    "term/python/runner": "Mode 1.5 실행기. 용어를 모으고 채점하고 내보낸다. 사람에게 묻지 않는다.",
    "spec/python/runner": "Mode 2 실행기. 설계 검토 보고서를 짓는 흐름을 돌리며 잰다.",
    "spec/python/viz": "보고서 뼈대 · 빌드 · 검사. 원고를 하나짜리 HTML 로 굽는다.",
    "core": "세 실행기가 함께 타는 단계 기계 · 측정 · 명령 갈림길.",
    "common": "mode 를 가리지 않는 유틸 — 해석기 탐색 · 리소스 자리 채우기.",
    "tools": "저장소 관리용 잡도구.",
}
```
Check that the README title line uses the argument as given (`# \`codewiki/python/runner/\``): `grep -n '"# ' tools/gen_readme.py`.

- [ ] **Step 8: Entry points**

Each of `bin/report-wiki`, `bin/report-term`, `bin/report-spec` must now read (the rewriter changes the import and the table values; verify):
```python
from core.dispatch import run_dispatch
```
and the tables:
```python
    table={"prep": "codewiki/python/runner/wiki/prep.py", "build": "codewiki/python/runner/wiki/build.py", "check": "codewiki/python/runner/wiki/check.py"},
    table={"collect": "term/python/runner/term/collect.py", "grade": "term/python/runner/term/quiz.py", "emit": "term/python/runner/term/emit.py"},
    table={"init": "spec/python/viz/init.py", "build": "spec/python/viz/build.py", "check": "spec/python/viz/check.py"},
```

- [ ] **Step 9: Gates — `qa/gates/test_prompt_resources.py`**

Replace the header block (from `ROOT =` through `RUNNERS =`) with:
```python
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 실행기 셋은 평평한 이름으로 import 한다 — 세 runner 폴더와 machine 이 sys.path 에 있어야 한다.
sys.path[:0] = [ROOT, os.path.join(ROOT, "codewiki", "python", "runner"), os.path.join(ROOT, "term", "python", "runner"),
                os.path.join(ROOT, "spec", "python", "runner"), os.path.join(ROOT, "codewiki", "python", "machine")]

LONG_LINES = 6     # 줄바꿈이 이만큼 이상인 글(문자열 상수 · f-문자열)은 리소스로 뺀다
LONG_CHARS = 200   # 한 줄이라도 이 길이 이상이면 리소스로 뺀다
CODE_TOPS = ("codewiki", "term", "spec", "core", "common", "tools")   # 긴 글을 찾는 폴더 — 시험 파일은 뺀다
RESOURCE_TOPS = ("resource",)   # 프롬프트 · 결함 표 · 템플릿이 사는 폴더 — `resource/<mode>/…`
RUNNERS = {"run_mode1": "codewiki/python/runner", "run_mode1_5": "term/python/runner", "run_mode2": "spec/python/runner"}
```
Replace `template_files` and `prompt_files`:
```python
def template_files() -> list[str]:
    return sorted(t for top in RESOURCE_TOPS
                  for t in glob.glob(os.path.join(ROOT, top, "*", "templates", "**", "*"), recursive=True)
                  if os.path.isfile(t))


def prompt_files() -> list[str]:
    """Jinja2 로 렌더되는 리소스 파일 — 프롬프트 파일과 결함 표."""
    return sorted(glob.glob(os.path.join(ROOT, "resource", "*", "prompts", "*.md"))
                  + glob.glob(os.path.join(ROOT, "resource", "*", "faults.toml")))
```
In `test_프롬프트_선언과_파일_절이_1대1이다`, replace the runner loop and the glob:
```python
    for name, folder in RUNNERS.items():
        if os.path.exists(os.path.join(ROOT, folder, name + ".py")):
            importlib.import_module(name)
```
```python
    for p in prompt_files():
        if not p.endswith(".md"):
            continue
```
`import pipeline as P` (three places) → `from core import pipeline as P`; `from tools.template import TemplateError` → `from common.template import TemplateError` (the rewriter did these two; verify with `grep -n 'pipeline\|template' qa/gates/test_prompt_resources.py`).

- [ ] **Step 10: Gates — `qa/gates/test_docs_citations.py`, `test_no_any.py`, `test_wiki.py`**

`contextDocs()` list:
```python
    docs = ["CLAUDE.md", "README.md", "ARCHITECTURE.md",
            "codewiki/CLAUDE.md", "term/CLAUDE.md", "spec/CLAUDE.md", "spec/typescript/CLAUDE.md",
            "core/CLAUDE.md", "tools/CLAUDE.md", "test/CLAUDE.md", "qa/CLAUDE.md", "resource/CLAUDE.md",
            "docs/CLAUDE.md",
            ".claude/CLAUDE.md",
            ".claude/agents/mode-1-codebase-wiki.md",
            ".claude/agents/mode-1-5-term-benchmark.md",
            ".claude/agents/mode-2-spec-report.md",
            ".claude/skills/spec-review-dashboard/SKILL.md",
            ".claude/skills/term-benchmark/SKILL.md",
            ".agents/skills/codebase-terms-survey/SKILL.md"]
```
(`contextDocs` keeps only the ones that exist, so the new `CLAUDE.md` files of Task 6 may land later.) `test_no_any.py`: `COVERED` was rewritten by the script — verify every path exists: `.venv/bin/python -c "import qa.gates.test_no_any"` is not importable as a package; instead run the test. `test_wiki.py`: `ROOT` depth was fixed by the script; imports now read `from codewiki.python.runner.wiki…`.

- [ ] **Step 11: Test headers**

Every moved test file inserts its own directory and/or `ROOT` on `sys.path` and then imports flat names. Rule: `ROOT` chains are already fixed; for each test file add the folder(s) its flat imports now live in, using this table, and delete `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` lines that no longer serve an import.

| Test folder | Flat imports need | `sys.path` line to use |
|---|---|---|
| `test/codewiki/` | `codewiki/python/runner`, `codewiki/python/machine`, `codewiki/python/viz` | `sys.path[:0] = [ROOT, os.path.join(ROOT, "codewiki", "python", "runner"), os.path.join(ROOT, "codewiki", "python", "machine"), os.path.join(ROOT, "codewiki", "python", "viz")]` |
| `test/term/` | `term/python/runner`, `codewiki/python/machine` (declmap fixtures) | `sys.path[:0] = [ROOT, os.path.join(ROOT, "term", "python", "runner"), os.path.join(ROOT, "codewiki", "python", "machine")]` |
| `test/spec/` | `spec/python/runner`, `spec/python/viz` | `sys.path[:0] = [ROOT, os.path.join(ROOT, "spec", "python", "runner"), os.path.join(ROOT, "spec", "python", "viz")]` |
| `test/core/` | none (`from core import …`) | `sys.path.insert(0, ROOT)` |
| `test/common/` · `test/tools/` | none (`from common…` · `from tools…`) | `sys.path.insert(0, ROOT)` |

Find them: `grep -rn 'sys.path' test qa`. Run `.venv/bin/python -m pytest -q -x` and fix each `ModuleNotFoundError` by the table — test files are not cited, so their line counts may change.

- [ ] **Step 12: Relative imports, `split-work/capture.sh` and `capture.py`**

The rewriter refuses `../` paths and prints them. Fix each by hand from the file's new location — known today (🔵): `test/spec/svg.test.mjs` imports `../viz/svg.mjs` → `../../spec/typescript/svg.mjs`. Also run `grep -rnE "from ['\"]\.\./|import\(['\"]\.\./" test spec/typescript` and check every hit resolves (`node --check` for `.mjs`).

The rewriter changed the path strings; verify the three lines in `capture.sh` now read `codewiki/python/viz/render_modules.py`, `codewiki/python/viz/render_classes.py`, `bin/report-spec`; and `capture.py` line `sys.path[:0] = [ROOT, …]` now lists `codewiki/python/runner`, `codewiki/python/machine`, `term/python/runner`, `spec/python/runner`, `spec/python/viz` (its `from mode1.lang import …` needs the Mode 1 runner folder; `import run_mode1_5` · `run_mode2` need theirs).

- [ ] **Step 13: Regenerate READMEs and run every gate**

```bash
.venv/bin/python tools/gen_readme.py codewiki/python/runner codewiki/python/machine codewiki/python/viz term/python/runner spec/python/runner spec/python/viz core common tools
.venv/bin/python tools/gen_readme.py --check codewiki/python/runner codewiki/python/machine codewiki/python/viz term/python/runner spec/python/runner spec/python/viz core common tools
.venv/bin/python -m pytest -q 2>&1 | tail -3          # same pass count as Task 2; same two reds
npm test && npm run typecheck && npm run typecheck:py  # 8 · 0 · 0 (see spec §8 for the 16 newly checked test files)
npm run doctor
split-work/capture.sh "$PWD" split-work/reorg/out/after-move && diff -r split-work/reorg/out/before split-work/reorg/out/after-move && echo 같다
PATH="$PWD/bin:$PATH" report-wiki; report-term; report-spec     # three usage lines, exit 1 each
```
Expected: all as noted. If `pyright` reports errors only in files that came from the old `test/` (the 16 of spec §8), fix trivial ones; otherwise add the file to `exclude` and list it in the commit body of Task 7's report.

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "[refactor] : mode 1차 축으로 이동 - codewiki, term, spec, core, common, test, qa, resource"
```

---

### Task 5: Remap citations — wiki, survey record, context documents

**Files:**
- Create: `split-work/reorg/remap_citations.py`
- Modify: `docs/wiki/*.md`, `resource/codewiki/terms-reading.json`, `CLAUDE.md`, `ARCHITECTURE.md`, `README.md`, `docs/CLAUDE.md`, `codewiki/CLAUDE.md`, `core/CLAUDE.md`, `spec/CLAUDE.md`, `spec/typescript/CLAUDE.md`, `tools/CLAUDE.md`, `test/CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/agents/*.md`, three `SKILL.md`, `.gemini/*.md`, `docs/diagrams/*.dot`, `qa/evals/README.md`, `split-work/README.md`

- [ ] **Step 1: Write the remapper**

`split-work/reorg/remap_citations.py`:
```python
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
             ".agents/skills/codebase-terms-survey/SKILL.md", "qa/evals/README.md", "split-work/README.md"}
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
```

- [ ] **Step 2: Run it**

```bash
cd split-work/reorg && ../../.venv/bin/python remap_citations.py; cd ../..
git diff --stat | tail -1
```
Expected: `고친 문서: 32` and `지운 파일의 레코드(함께 지웠다): 42` on the design tree (🔵 dry run); a report of citations that pointed into a deleted block (🔵 ten in `docs/wiki/machine-*.md` — each moved to the declaration line below the block); the unchanged-id list contains only artifacts (`codegraph.json`, `terms-db.json`, …) and the split directory names (`runner`, `viz`).

- [ ] **Step 3: Verify against the baselines**

```bash
.venv/bin/python bin/report-wiki prep . && .venv/bin/python bin/report-wiki check . > split-work/reorg/out/after-wiki-check.txt 2>&1
grep -E '^L[12] ' split-work/reorg/out/baseline-wiki-check.txt split-work/reorg/out/after-wiki-check.txt
.venv/bin/python codewiki/python/machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading resource/codewiki/terms-reading.json > split-work/reorg/out/after-terms-db.txt 2>&1
tail -3 split-work/reorg/out/baseline-terms-db.txt split-work/reorg/out/after-terms-db.txt
.venv/bin/python -m pytest qa/gates/test_docs_citations.py -q
```
Expected: the `L1 n/f` and `L2 n/f` pairs are equal before and after; the terms-db failure count is equal; the citation gate is green. If a path the gate flags is a bare directory mention (`runner/`, `viz/`) in prose, fix it by hand in Task 6 — do not loosen the gate.

- [ ] **Step 4: Apply the same path rewrite to the two skill originals outside the repository**

```bash
for s in spec-review-dashboard term-benchmark; do cp ".claude/skills/$s/SKILL.md" "$HOME/.claude/skills/$s/SKILL.md"; done
diff -r .claude/skills/spec-review-dashboard "$HOME/.claude/skills/spec-review-dashboard" && echo 같다
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "[docs] : 인용 재계산 - 위키, 전수조사 레코드, 컨텍스트 문서의 경로와 줄"
```

---

### Task 6: Restructure the module documents

**Files:**
- Create: `term/CLAUDE.md`, `qa/CLAUDE.md`, `resource/CLAUDE.md`
- Modify: `CLAUDE.md`, `codewiki/CLAUDE.md`, `core/CLAUDE.md`, `spec/CLAUDE.md`, `spec/typescript/CLAUDE.md`, `tools/CLAUDE.md`, `test/CLAUDE.md`, `ARCHITECTURE.md`, `README.md`

- [ ] **Step 1: `term/CLAUDE.md`**

```markdown
# term/ — Mode 1.5. 용어 이해도 점검

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 단계 기계는 [`../core/CLAUDE.md`](../core/CLAUDE.md), 리소스는 [`../resource/CLAUDE.md`](../resource/CLAUDE.md).

Plan 하나를 놓고 돈다 — 필요한 용어를 모으고(collect), 사람이 푼 객관식 답안을 채점해(grade), 학습 노트와 용어집 DB 를 낸다(emit).
**실행기는 사람에게 묻지 않는다.** 묻는 절차는 `term-benchmark` 스킬이 맡는다.

## 무엇이 여기 있나

| 자리 | 무엇 |
|---|---|
| `python/runner/run_mode1_5.py` | Mode 1.5 파이프라인을 돌리다 사람 차례에서 멈추는 실행기 |
| `python/runner/run_grade.py` | 채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기 |
| `python/runner/term/` | `collect.py` · `quiz.py` · `emit.py` — `bin/report-term` 의 세 명령 |
| `../resource/term/prompts/ask.md` | 사람에게 묻는 세션의 프롬프트 글 |

전량 목록은 `python/runner/README.md` 에 있다(`tools/gen_readme.py` 가 생성).

## 이 모듈이 소유하는 것 (Owns)

`term/**` · `resource/term/**` · `test/term/**`. 소유하지 않는 것 — 용어 DB 의 꼴(`codewiki/python/machine/terms_db.py`)과 봉인(결정 0011).

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../core/` | `pipeline` · `measure` 를 import 한다 |
| 여기 → `../common/python.py` | 해석기 탐색 |
| 여기 → `../codewiki/` | **import 하지 않는다.** 봉인된 `terms-db.json` 을 읽을 뿐이다(결정 0011) — `test/core/test_import_isolation.py` 가 잰다 |
| `bin/report-term` → 여기 | 세 명령을 자식 프로세스로 띄운다 |
```

- [ ] **Step 2: `qa/CLAUDE.md`**

```markdown
# qa/ — 저장소가 규약을 지키는가. 코드가 맞는가는 test/ 의 몫

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 모듈 시험은 [`../test/CLAUDE.md`](../test/CLAUDE.md).

## gates/ — 규약 게이트 넷

| 파일 | 무엇을 고정하나 |
|---|---|
| `test_docs_citations.py` | 컨텍스트 문서(루트 · 모듈 `CLAUDE.md` · `README.md` · `ARCHITECTURE.md` · 에이전트 셋 · 스킬 셋)의 `파일:줄` 인용과 경로가 실재하는가. 목록은 `contextDocs()` |
| `test_no_any.py` | 형 자리의 `Any` 를 글자로 막는다. `COVERED` 의 파일은 `Any` 0 |
| `test_prompt_resources.py` | 리소스와 코드를 가르는 게이트 — 코드에 긴 글이 없다 · 단계의 `prompt_names` 와 `resource/<mode>/prompts/*.md` 의 파일 · 절이 1:1 · 템플릿마다 코드에 같은 값의 문자열 상수 · 프롬프트와 결함 표가 Jinja2 로 컴파일 · 줄 끝 공백과 `{#` 없음 |
| `test_wiki.py` | `report-wiki prep · build · check` 가 실제로 돈다. `check` 는 `docs/wiki/` 를 이 저장소 기준으로 검사한다 — 빨강이면 위키 재굽기가 답이다 |

CI(`.github/workflows/docs-gates.yml`)는 앞의 둘만 돈다 — 나머지는 Graphviz · Node · 골든 저장소가 필요해 로컬 몫이다.

## evals/ — 실행기가 잰 값

세 mode 실행기가 `--json` 으로 낸 단계별 시간 · 토큰 · 비용. 판정하지 않고 쌓아 둔다 — `evals/README.md`.

```bash
.venv/bin/python -m pytest qa/ -q                     # 게이트 넷
.venv/bin/python codewiki/python/runner/run_mode1.py <저장소> --model opus --json qa/evals/runs/$(date +%F)-mode1-<대상>-<조건>.json
```

## 이 모듈이 소유하는 것 (Owns)

`qa/**`. 소유하지 않는 것 — 검사 대상인 코드와 문서. 게이트가 빨개지면 대상을 고치지 게이트를 느슨하게 만들지 않는다.
```

- [ ] **Step 3: `resource/CLAUDE.md`**

```markdown
# resource/ — 코드가 읽기만 하는 것들. mode 별로 산다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 규칙의 출처는 결정 [`0012`](../docs/decisions/0012-prompt-dynamics-in-jinja2.md)(프롬프트는 Jinja2) 와 [`0014`](../docs/decisions/0014-mode-first-layout-and-resource-dir.md)(자리).

| 자리 | 무엇 | 읽는 코드 |
|---|---|---|
| `codewiki/prompts/<단계>.md` · `codewiki/faults.toml` | Mode 1 LLM 단계의 프롬프트(파일 이름 = 단계 이름, `<!-- section: 이름 -->` 절) · 결함 표 | `codewiki/python/runner/mode1/context.py` 의 `PROMPT_DIR` · `FAULTS_PATH` |
| `codewiki/templates/` | VitePress 설정 · 모듈 · 클래스 DOT 의 머리와 범례 | `runner/wiki/build.py` · `viz/render_*.py` 의 `TEMPLATES` |
| `codewiki/config.toml` | Mode 1 의 Model id 와 비용 어림 | `context.py` 의 `CONFIG_PATH` |
| `codewiki/samples/` | 수집기 출력의 골든 꼴(C++ · C# Unity)과 `OBSERVATION-template.md` | `codebase-terms-survey` 스킬 · 골든 시험 |
| `codewiki/terms-reading.json` | 이 저장소 자신의 전수조사 레코드(자기호스팅) | `context.py` 의 `reading_path()` · `terms_db.py --reading` |
| `term/prompts/ask.md` | Mode 1.5 가 사람에게 묻는 세션의 글 | `term/python/runner/run_mode1_5.py` |
| `spec/prompts/agent.md` · `spec/templates/report/` · `spec/config.toml` | Mode 2 에이전트 프롬프트 · 보고서 뼈대 다섯 · 원본 문서 자리 규칙과 Model 별명 | `run_mode2.py` · `viz/init.py` · `viz/build.py` |

**규칙.** 프롬프트는 단계당 한 파일, 글은 Jinja2 — 반복 · 빈 값 대체 · 조건부 절을 파일 안에 쓴다. **템플릿은 꼴만, 데이터 결정은 단계.** 파일 템플릿의 자리표시는 `{{이름}}` 하나(`common/template.py`). 파이썬은 여기 것을 읽기만 한다. `qa/gates/test_prompt_resources.py` 가 막는다.

두 mode 가 같은 리소스를 읽게 되면 `resource/common/` 을 더한다(0014 의 되살릴 조건).
```

- [ ] **Step 4: `test/CLAUDE.md` (whole file)**

```markdown
# test/ — 모듈 시험. mode 별로 모은다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 저장소 규약 게이트는 [`../qa/CLAUDE.md`](../qa/CLAUDE.md).

| 폴더 | 무엇을 | `sys.path` 에 넣는 것 |
|---|---|---|
| `codewiki/` | Mode 1 — 수집기 · 정규화 · 용어 DB · warmup · 층 계획 · 단계 기계 위의 Mode 1 실행기 | `codewiki/python/{runner,machine,viz}` |
| `term/` | Mode 1.5 — 실행기 · 채점 · collect/quiz/emit | `term/python/runner` · `codewiki/python/machine`(declmap 픽스처) |
| `spec/` | Mode 2 — `init` 의 slug · `check` 의 `<script>` 상한 · 경로 링크 · 용어 감싸기 · React 컴포넌트와 용어 그래프 수학(Node 자식 프로세스) · `config.toml` 대조 · **유일한 Node 시험** `svg.test.mjs` | `spec/python/{runner,viz}` |
| `core/` | 단계 기계 · 측정 · 명령 갈림길 · Mode 1.5 와 2 를 import 해도 networkx 가 실리지 않는가 | `ROOT` 만 |
| `common/` | 리소스 자리 채우기 · 템플릿에서 짓는 파일 꼴 | `ROOT` 만 |
| `tools/` | README 표류 · 해석기 탐색 · doctor 출력 | `ROOT` 만 |

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest -q                       # 전량 — test/ 와 qa/ 를 pytest 가 모은다
.venv/bin/python -m pytest test/spec -q             # 한 mode
.venv/bin/python -m pytest -k "링크" -q              # 이름으로 고르기
npm test                                            # pretest 가 spec/typescript/lib.mjs 로 .tmp/lib.mjs 를 굽고 node --test
GRAPHICS_REPO=… CSHARP_REPO=… .venv/bin/python -m pytest -q   # 골든 19개까지 돈다
```

## 비직관적인 것 (Gotchas)

- **건너뜀 19개는 실패가 아니다.** 골든 저장소 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO`)가 없어서다. 전부 `test/codewiki/` 쪽이다.
- **pytest 설정 파일이 없다.** 저장소 루트에서 `test_*.py` 를 전부 모은다. 루트 밖에서 돌리면 import 경로가 어긋난다.
- **`node --test test/` 는 Node v25 에서 죽는다.** 인자 없는 `node --test` 를 쓴다.
- **렌더 시험은 임시 파일을 `ROOT` 에 쓴다**(`.tmp-eval.mjs` · `.tmp-eval-math.ts`). 동적 `import()` 가 파일 위치 기준으로 `react` 를 찾는다.
- **`spec/typescript/src/` 를 고쳤는데 시험이 옛 동작을 보인다** — `.tmp/lib.mjs` 가 낡았다. `npm test` 로 다시 굽는다.
```

- [ ] **Step 5: `core/CLAUDE.md` (from `runner/CLAUDE.md`)**

Edit: title → `# core/ — 세 실행기가 함께 타는 단계 기계. 그리고 common/`; the "무엇이 여기 있나" table keeps only `pipeline.py` · `measure.py` · `dispatch.py` rows and adds:
```
| `../common/python.py` | 파이썬 해석기를 기계에 상관없이 찾는다 — `REPORT_PYTHON` → `.venv` → PATH |
| `../common/template.py` | 리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외 |
```
Move the "흔한 변경 패턴" block about adding a Mode 1 stage to `codewiki/CLAUDE.md` (Step 6) and replace it here with:
```bash
# bin 명령을 더한다 — 진입점의 table 한 줄 + 스크립트 파일 하나. dispatch.py 가 확장자로 해석기를 고른다
# 재는 코드가 필요하다 — 실행기가 아니라 measure.py 를 import 한다
# 단계를 더한다 — 그 mode 의 CLAUDE.md(codewiki · term · spec)를 본다. 단계 기계 자체는 바뀌지 않는다
```
Owns: `core/**` · `common/**` · `test/core/**` · `test/common/**`. Cross-module: `codewiki/` · `term/` · `spec/` → here; here → nothing (`measure.py` · `pipeline.py` import no mode — `test/core/test_import_isolation.py`).

- [ ] **Step 6: `codewiki/CLAUDE.md` (from `machine/CLAUDE.md`)**

Edit: title → `# codewiki/ — Mode 1. 코드베이스를 읽어 코드 지도와 위키를 만든다`; the blockquote → `> 루트 나침반은 [../CLAUDE.md](../CLAUDE.md). 단계 기계는 [../core/CLAUDE.md](../core/CLAUDE.md), 리소스는 [../resource/CLAUDE.md](../resource/CLAUDE.md). 분리 계획(결정 0011)의 Phase B 는 이 폴더를 통째로 codebase-wiki 저장소로 떼어낸다.`; the intro sentence "이 저장소에서 가장 큰 모듈이다(파이썬 27파일 — 본체 16 · 시험 11)" → "이 저장소에서 가장 큰 모듈이다 — `python/machine/`(정적 수집 · 인용 검증) · `python/runner/`(실행기와 단계) · `python/viz/`(그림) · `csharp/roslyn-dump/`(C# 수집기). 시험은 `test/codewiki/`". Add to the "무엇이 여기 있나" table the rows:
```
| `python/runner/run_mode1.py` | Mode 1 실행기 — 단계 기계 위에서 흐름을 짓고 단계마다 시간과 토큰을 잰다 |
| `python/runner/mode1/` | 단계 — `edges.py` 의 `ORDER` · `STAGES` · `EDGES`, `context.py` 의 산출물과 설정 · 프롬프트 자리 |
| `python/runner/wiki/` | `prep` · `build` · `check` — `bin/report-wiki` 의 세 명령 |
| `python/viz/render_modules.py` · `render_classes.py` | 코드 지도를 Graphviz DOT 로 적고 굽는다 |
| `python/viz/demermaid.py` | 위키의 Mermaid 를 빌드 전에 SVG 로 사전 렌더 |
```
Paste here the "Mode 1 에 단계를 더한다" block from the old `runner/CLAUDE.md` with its paths rewritten (`codewiki/python/runner/mode1/<모듈>.py` · `resource/codewiki/prompts/<단계>.md` · `context.py` · `edges.py`). Owns: `codewiki/**` · `resource/codewiki/**` · `test/codewiki/**` · `out/codegraph-raw/**`. Cross-module: here → `core/` (pipeline · measure), `common/` (python · template); `bin/report-wiki` → here; `term/` and `spec/` read the seal only (0011).

- [ ] **Step 7: `spec/CLAUDE.md` and `spec/typescript/CLAUDE.md`**

`spec/CLAUDE.md` (from `viz/CLAUDE.md`): title → `# spec/ — Mode 2. 설계 검토 보고서를 굽는다`; delete the section `### 위키 그림 사전 렌더 (viz/demermaid.py)` and every row about `render_modules` · `render_classes` · `demermaid` (they are in `codewiki/CLAUDE.md`); add a "무엇이 여기 있나" row `| python/runner/run_mode2.py | Mode 2 실행기 |`; Owns: `spec/**` · `resource/spec/**` · `test/spec/**`; Cross-module: here → `core/` · `common/`; `bin/report-spec` · `bin/report` → here; `codewiki/` → **not imported** (seal only, 0011). `spec/typescript/CLAUDE.md`: title → `# spec/typescript/ — 읽기 전용 React 컴포넌트`; paths were rewritten by Task 5; verify `grep -n 'viz/' spec/typescript/CLAUDE.md` prints nothing.

- [ ] **Step 8: `tools/CLAUDE.md` and `.gemini/PythonRule.md`**

`tools/CLAUDE.md`: delete the rows for `python.py` and `template.py`; add one line under the table: `해석기 탐색(python.py)과 리소스 자리 채우기(template.py)는 세 mode 가 함께 쓰므로 2026-10-31 에 common/ 으로 갔다.`
`.gemini/PythonRule.md`: `grep -n 'include' .gemini/PythonRule.md` — delete the paragraph that describes the `# <include …/>` comment block as a convention (the injector and every block were removed in Task 2) and, if the file lists the `requirements.txt` dependencies, make the list match the file.

- [ ] **Step 8b: Relative links the rewriter refused**

`rewrite_paths.py` and `remap_citations.py` print every `../` path whose target moved. 🔵 On the design tree they are the sibling links of the module documents (`codewiki/CLAUDE.md` → `../runner/CLAUDE.md` · `../viz/CLAUDE.md` · `../viz/src/CLAUDE.md`; `core/CLAUDE.md` → `../machine/…` · `../tools/python.py` · `../tools/template.py` · `../viz/CLAUDE.md`; `spec/CLAUDE.md` → `../config/report.toml` · `../machine/…` · `../runner/…` · `../tools/template.py`; `test/CLAUDE.md` · `tools/CLAUDE.md` likewise) plus two test literals (`qa/gates/test_docs_citations.py` · `qa/gates/test_wiki.py`). Rewrite each from the document's new location (`codewiki/CLAUDE.md` → `../core/CLAUDE.md` · `../spec/CLAUDE.md` · `../spec/typescript/CLAUDE.md`; `core/CLAUDE.md` → `../codewiki/…` · `../common/python.py` · `../common/template.py` · `../spec/CLAUDE.md`; `spec/CLAUDE.md` → `../resource/spec/config.toml` · `../codewiki/…` · `../core/dispatch.py` · `../common/template.py`; `tools/CLAUDE.md` → `../codewiki/python/machine/pycalls.py` · `../core/…` · `../term/python/runner/run_mode1_5.py` · `../codewiki/python/runner/wiki/…`); the test literals stay as they are (they are inputs to `pathRefsIn`, not citations) unless the citation gate flags them. Paths without `../` inside a module document are relative to the document's **old** directory and the gate flags them too (🔵 dry run: `spec/CLAUDE.md` → `src/CLAUDE.md` becomes `typescript/CLAUDE.md`; `spec/typescript/CLAUDE.md` → `runtime/term-graph.ts` becomes `src/runtime/term-graph.ts`; `core/CLAUDE.md` → `mode1/faults.toml` · `wiki/prep.py` · `wiki/check.py` · `mode1/terms.py` move with their sections to `codewiki/CLAUDE.md` as `../resource/codewiki/faults.toml` · `python/runner/wiki/prep.py` …; `docs/CLAUDE.md` → `../machine/CLAUDE.md` · `../viz/CLAUDE.md` · `../viz/src/CLAUDE.md` · `../test/test_docs_citations.py` become `../codewiki/CLAUDE.md` · `../spec/CLAUDE.md` · `../spec/typescript/CLAUDE.md` · `../qa/gates/test_docs_citations.py`). `.tmp/lib.mjs` is flagged only in a tree that has not run `npm test` yet.

- [ ] **Step 9: Root `CLAUDE.md`**

Replace these sections (the rest was path-rewritten by Task 5):

The compass table rows for `runner/CLAUDE.md` · `machine/CLAUDE.md` · `viz/CLAUDE.md` · `viz/src/CLAUDE.md` · `tools/CLAUDE.md` · `config/…` → 
```
| [`codewiki/CLAUDE.md`](codewiki/CLAUDE.md) | **Mode 1** — 정적 수집 · 정규화 · 전수조사 레코드 · warmup · 실행기와 단계 · 코드 지도 그림 |
| [`term/CLAUDE.md`](term/CLAUDE.md) | **Mode 1.5** — 용어 모으기 · 채점 · 내보내기 |
| [`spec/CLAUDE.md`](spec/CLAUDE.md) · [`spec/typescript/CLAUDE.md`](spec/typescript/CLAUDE.md) | **Mode 2** — 렌더 경로 · 직접 실행 가드 · 컴포넌트 17개 · 테마 · 용어집과 관계 그래프 |
| [`core/CLAUDE.md`](core/CLAUDE.md) | 세 실행기가 함께 타는 **단계 기계** · 측정 · 명령 갈림길. `common/` 의 유틸 둘도 여기서 설명한다 |
| [`tools/CLAUDE.md`](tools/CLAUDE.md) | 저장소 유지보수 — 환경 점검 · README 생성 · 설치 · 경로 세척 |
| [`resource/CLAUDE.md`](resource/CLAUDE.md) | **코드가 읽기만 하는 것** — 프롬프트 · 결함 표 · 템플릿 · `config.toml` · 골든 꼴 · 전수조사 레코드. mode 별로 |
| [`qa/CLAUDE.md`](qa/CLAUDE.md) | 저장소 규약 게이트 넷과 실행기 측정값 |
| [`test/CLAUDE.md`](test/CLAUDE.md) | 모듈 시험 — mode 별 폴더 |
```
The section `### 성격축 셋 — 언어가 아니라 하는 일로 가른다 (2026-08-30)` → `### 축 셋 — mode · 언어 · 성격 (2026-10-31, 결정 0014)` with the table:
```
| 축 | 자리 | 가르는 질문 |
|---|---|---|
| 1차 mode | `codewiki/` · `term/` · `spec/` | **어느 산출물의 것인가** — 코드베이스 위키 · 용어 이해도 · 설계 검토 보고서 |
| 2차 언어 | `python/` · `csharp/` · `typescript/` | **무엇으로 쓰였나** |
| 3차 성격 | `runner/` · `machine/` · `viz/` | **시키는가 · 계산하는가 · 그리는가** (2026-08-30 의 성격축을 그대로 둔다) |
| 축 밖 | `core/`(단계 기계) · `common/`(유틸) · `tools/`(유지보수) · `resource/`(읽기만) · `test/` · `qa/` | mode 를 가리지 않는 것 |
```
The architecture tree block under `## 아키텍처` → the tree of spec §3 (the `report-builder/` part). The "리소스와 코드를 가른다 (최우선)" bullet: `runner/**/prompts/<단계>.md` → `resource/<mode>/prompts/<단계>.md`; `runner/**/templates/ · viz/templates/` → `resource/<mode>/templates/`; `config/*.toml` → `resource/<mode>/config.toml`; `runner/mode1/faults.toml` → `resource/codewiki/faults.toml`; `test/test_prompt_resources.py` → `qa/gates/test_prompt_resources.py`. The "파이썬이 본체이고 JavaScript 는 경계에만" table rows: `viz/src/**` → `spec/typescript/src/**`, `viz/svg.mjs` → `spec/typescript/svg.mjs`, `viz/lib.mjs` → `spec/typescript/lib.mjs`. The gate table's README command → the nine directories. The entry-point table's script paths → `codewiki/python/runner/wiki/*.py` etc.

- [ ] **Step 10: `ARCHITECTURE.md` and `README.md`**

`ARCHITECTURE.md` §1 flowchart subgraph `RB` → nodes `BIN["bin/ 진입점 4개"]`, `CW["codewiki/ Mode 1<br/>python/{runner,machine,viz} · csharp/"]`, `TM["term/ Mode 1.5<br/>python/runner"]`, `SP["spec/ Mode 2<br/>python/{runner,viz} · typescript/"]`, `CORE["core/ 단계 기계 · common/ 유틸"]`, `RES["resource/ 프롬프트 · 템플릿 · config · 골든 꼴 · 레코드"]`; edges `BIN --> CW`, `BIN --> TM`, `BIN --> SP`, `CW --> CORE`, `TM --> CORE`, `SP --> CORE`, `CW -. 읽는다 .-> RES`, `TM -. 읽는다 .-> RES`, `SP -. 읽는다 .-> RES`. The paragraph "**축은 언어가 아니라 성격이다** (2026-08-30 분리)…" → "**1차 축은 mode, 2차는 언어, 3차는 성격이다** (2026-10-31, 결정 0014). 성격축(`runner/` · `machine/` · `viz/`)은 각 mode 의 언어 폴더 아래 그대로 산다." §4 layer diagram → `BIN --> DIS["core/dispatch.py"]`, `DIS --> SPEC["spec/python/viz/{init,build,check}.py"]`, `DIS --> TERM["term/python/runner/term/*.py"]`, `DIS --> WIKI["codewiki/python/runner/wiki/*.py"]`, `WIKI --> PY["codewiki/python/machine/*.py"]`, `RUN["<mode>/python/runner/run_mode*.py"] --> CORE["core/pipeline.py · measure.py"]`. `README.md`: the pytest line → `.venv/bin/python -m pytest -q`; the "필수 Python" row → `codewiki/`, `term/`, `spec/`, `core/` 등; the C# optional row → `codewiki/csharp/roslyn-dump`.

- [ ] **Step 11: Gates and commit**

```bash
.venv/bin/python -m pytest qa/gates/test_docs_citations.py -q     # green — fix every flagged path by hand, never the gate
.venv/bin/python -m pytest -q 2>&1 | tail -2
git add -A
git commit -m "[docs] : 모듈 CLAUDE.md 재구성 - mode 축, core, qa, resource, test 문서"
```

---

### Task 7: Close out

**Files:**
- Modify: `docs/handoffs/RESUME-2026-10-24-split-rev4-execution.md` (§10 row), `docs/decisions/0014-mode-first-layout-and-resource-dir.md` (이행 line), `docs/decisions/README.md` (0014 status), memory

- [ ] **Step 1: Full verification once more**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -2 && npm test && npm run typecheck && npm run typecheck:py && npm run doctor
.venv/bin/python tools/gen_readme.py --check codewiki/python/runner codewiki/python/machine codewiki/python/viz term/python/runner spec/python/runner spec/python/viz core common tools
split-work/capture.sh "$PWD" split-work/reorg/out/after-all && diff -r split-work/reorg/out/before split-work/reorg/out/after-all && echo 같다
git log --follow --oneline codewiki/python/machine/normalize.py | tail -1
```
Expected: gates as baseline (minus xmldoc tests), `같다`, and the oldest commit of `normalize.py`'s history visible.

- [ ] **Step 2: Record the execution**

In `docs/decisions/0014-…md` change `**이행** 아직 없다.` to `**이행** <날짜> · 커밋 <해시 범위>.` and in `docs/decisions/README.md` the 0014 status `확정 · 미이행` → `확정 · 이행`. Append to the resume document §10:
```
| <날짜> | 디렉토리 정리(결정 0014) 이행 — 커밋 <범위>. 분리 Phase B 는 `codewiki/` 를 통째로 떼어낸다. 다음은 B |
```
Update the memory file `directory-reorg-2026-10-31.md` ("아직 미이행" → 이행 날짜) and `resume-entry-point.md`.

- [ ] **Step 3: Commit**

```bash
git add docs/decisions docs/handoffs/RESUME-2026-10-24-split-rev4-execution.md
git commit -m "[docs] : 결정 0014 이행 기록 - 재개 문서와 결정 색인"
```

Then ask the user before `git push` (resume document §7: main 에 push 하기 전에는 묻는다).

---

## Self-review against the spec

| Spec section | Task |
|---|---|
| §3 target layout · §4 path map | Task 1 (`pathmap.py` = the map), Task 3 (documents), Task 4 (code) |
| §5 deletions | Task 2 (xmldoc), Task 3 (`checklist.yaml`), Task 1 DELETE set (four README) |
| §6 invariants | Task 2 Step 6 / Task 4 Step 13 / Task 7 Step 1 (capture diff), line-count assert in `rewrite_paths.py`, archive excluded from both rewriters |
| §7 citations and ids | Task 5 |
| §8 imports · `sys.path` · pyright | Task 4 Steps 2 (rewriter), 3 (checker), 6 (pyright), 11 (tests) |
| §9 meta files and gates | Task 4 Steps 5–12 |
| §10 verification | Task 0 (baseline), Task 4 Step 13, Task 5 Step 3, Task 7 Step 1 |
| §11 documentation | Task 6 |
| §12 open items | Task 1 Step 3 (`contracts/`), Task 4 Step 13 (16 test files), layer test untouched |

Placeholder scan: none. Type consistency: `load_map`, `map_rel`, `repo_key`, `map_token`, `dotted_map`, `map_dotted`, `TOKEN`, `REMOVED`, `TSV`, `OUT`, `ROOT` are defined in `reorg_lib.py` and used with the same names in the four scripts; `rewrite_paths.py` reports `../` tokens it refused to touch, and Task 4 Step 12 fixes those by hand.
