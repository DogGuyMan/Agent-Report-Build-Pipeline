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
