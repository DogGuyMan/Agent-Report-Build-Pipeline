# Directory Reorganization — mode-first layout, `resource/`, `test/` and `qa/`

**Status** [제안됨] (proposed) · 2026-10-31 · design approved by the user through a nine-axis question round (four batches, fourteen questions). **Not executed.** Phases R · A · K · M of the two-repository split finished on 2026-10-31 (`main` merge `6c4009d`); execution is scheduled before Phase B — see "Scope and ordering".
**Decision record** `docs/decisions/0014-mode-first-layout-and-resource-dir.md`.
**Plan** `docs/superpowers/plans/2026-10-31-directory-reorg.md` (English original) · `docs/superpowers/plans/2026-10-31-directory-reorg.ko.md` (Korean translation).
**This file** is the English original; `2026-10-31-directory-reorg-design.ko.md` is its Korean translation.

> Until the plan runs, every path in `CLAUDE.md`, the module `CLAUDE.md` files, `ARCHITECTURE.md`, `README.md` and `docs/wiki/` describes the **current** layout. This document describes the **target**.

## 0. Summary

The repository's top level is regrouped by **mode** (`codewiki/` = Mode 1, `term/` = Mode 1.5, `spec/` = Mode 2), then by **language** (`python/`, `csharp/`, `typescript/`), then by the existing **nature axis** (`runner/`, `machine/`, `viz/`), which is kept so that file names and import paths survive. The five files all three modes share get their own homes (`core/` for the stage machine, `common/` for utilities). Every resource — prompts, fault table, file templates, configuration, collector golden shapes, this repository's own survey record — moves under `resource/<mode>/`. Module tests move under `test/<mode|core|common|tools>/`; the repository-convention gates and the runner measurements move under `qa/`. The retired xmldoc remnants are deleted in the same change. Citations in `docs/wiki/` and in `terms-reading.json` are rewritten mechanically (path substitution plus a deterministic line renumbering), the archive directories are left untouched, and Mode 1 is **not** re-run.

🔵 All counts in this document were measured on 2026-10-31 at commit `b0bdb50` with `git ls-files`, `grep` and the dry-run of the path map that the plan embeds: 480 tracked files → 192 move, 8 are deleted, 280 stay; no two sources map to one target.

## 1. Scope and ordering

| | |
|---|---|
| In scope | Moving and renaming tracked files; deleting the xmldoc remnants; rewriting paths, imports, `sys.path` lines, gate lists, configuration files, CI, entry points; rewriting citations in the wiki, the survey record and the context documents; restructuring the module `CLAUDE.md` files; regenerating the per-directory `README.md` files |
| Out of scope | Any behaviour change; renaming packages inside a mode (`runner/mode1/` stays `mode1`); re-running Mode 1; editing archive documents (`docs/handoffs/`, `docs/superpowers/`, `docs/my.self/`, `docs/decisions/`, `docs/overturn/`); the layer-distribution fixture in `test_survey_plan.py` (already red, cause unknown — root `CLAUDE.md` "게이트 여섯") |
| When | After Phase **M** of the two-repository split (decision 0011, plan rev.4 — R · A · K · M finished 2026-10-31, `6c4009d`) and before Phase **B**. Phase B then extracts `codewiki/` as a whole into the `codebase-wiki` repository |
| Where | Local session on the user's Mac (the user chose this over a cloud handoff) |
| Acceptance | The six gates are green at every commit, the 31 captured outputs of `split-work/capture.sh` are byte-identical before and after, and the `report-wiki check .` failure set is unchanged modulo path prefixes |

Relation to decision 0011: this is the **pre-step** of the split, not a replacement. The "common kernel" that 0011 says both repositories will duplicate is exactly `core/` + `common/`; giving it a directory makes the duplication boundary visible by name.

## 2. Decisions — nine axes

| # | Axis | Decision | Alternatives not chosen | Why |
|---|---|---|---|---|
| ① | Relation to 0011 | Pre-step of the split; after M, before B | Replace the split (new decision overturning 0011); apply after the split to each repository | User's choice; keeps 0011 intact and makes Phase B a directory extraction |
| ② | Primary axis and names | mode → language → nature. Names `codewiki` · `term` · `spec` | `mode1 · mode1_5 · mode2` (awkward 1.5); `wiki · term · spec` (chosen first, then `wiki` was found to collide three deep: top-level, `docs/wiki/`, `runner/wiki/`) | User's choice; `codewiki` is also close to 0011's repository name `codebase-wiki` |
| ② | Inside a mode | Keep the nature axis under the language folder | Flat under language (≈40 Python files in one folder; `clang_doc.py` ×2 and `wiki.py`/`wiki/` collide); Python without a language folder | Import paths and file names survive; zero collisions |
| ③ | `core` vs `common` | `core/` = stage machine (`pipeline.py` 16 consumers, `measure.py` 7, `dispatch.py` 3 entry points); `common/` = utilities (`python.py` 5, `template.py` 6); `tools/` keeps only repository maintenance | `core` = the whole machine axis; one `common` only | User's choice; consumer counts measured by grep |
| ④ | `test` vs `qa` | `test/` = every module test, grouped by mode; `qa/gates/` = repository-convention gates (citations · `Any` · resource separation · wiki drift); `qa/evals/` = runner measurements | Tests stay beside code and `qa` = cross-cutting tests; `qa` = measurements only | User's choice |
| ⑤ | `resource/` scope | Everything: prompts, fault table, file templates, `config/*.toml`, collector golden shapes, `terms-reading.json` | Measured data only; measured data + config | User's choice; amends the location clause of decision 0012 |
| ⑥ | `docs/` | Keep `docs/superpowers/{plans,specs}`; add `docs/notes/` (loose analyses) and `docs/research/` (absorbs root `reports/` and `research_notes/`); `remain-process-merged.md` → `docs/handoffs/` | Flatten to `docs/plans` · `docs/specs` (changes the superpowers skills' default path); leave root folders alone | User's choice |
| ⑦ | Citations and archive | Mechanical path substitution plus deterministic line renumbering; archive untouched; no re-bake | Rewrite archives too; leave wiki and record red until the next Mode 1 run | A pure move keeps line numbers; the 2026-08-30 axis move (`c1e4496`) also left archives alone; a re-bake measured $57 on 2026-09-19 |
| ⑧ | xmldoc remnants | Delete all: `machine/xmldoc.py`, `machine/test_xmldoc.py`, `machine/comments.xml`, the `# <include …/>` blocks (686 marker lines in 62 files) | Move only; delete files but keep blocks | User's choice; the removed line numbers are recorded, so renumbering stays exact |
| ⑨ | Procedure | The per-file Python edit-approval rule is retired (user, 2026-10-31); this session writes documents only | — | User's choice |

Routine calls made without asking (listed in the approval question): `bin/` stays at the root because `~/.zshrc` registers it on `PATH`; `config/report.toml` becomes `resource/spec/config.toml` because only Mode 2 reads it (`viz/init.py`, `runner/run_mode2.py`); `test_wiki.py` is a gate (it checks `docs/wiki/` drift); the empty `docs/prompt/checklist.yaml` is deleted; `OBSERVATION-template.md` sits next to the samples it templates; `resources/` is renamed `resource/` as the user wrote it; `split-work/` stays until Phase B.

## 3. Target layout

```
report-builder/
  bin/                     report · report-spec · report-term · report-wiki        (unchanged; on PATH)
  codewiki/                Mode 1
    CLAUDE.md
    python/
      runner/              run_mode1.py · check_shard.py · mode1/ (stages) · wiki/ (prep · build · check · clang_doc · compdb · paths)
      machine/             normalize · facts · terms_db · verify_citations · survey_plan · warmup · declmap · pycalls ·
                           clang_doc · clangd_refs · reverse_refs · lang_select · file_cache · fix_citation_paths ·
                           codegraph_types · reading_types (new: the Term/Terms types that xmldoc.py used to hold)
      viz/                 render_modules · render_classes · demermaid
    csharp/
      roslyn-dump/         Program.cs · roslyn-dump.csproj · .gitignore
  term/                    Mode 1.5
    CLAUDE.md
    python/runner/         run_mode1_5.py · run_grade.py · term/ (collect · quiz · emit)
  spec/                    Mode 2
    CLAUDE.md
    python/
      runner/              run_mode2.py
      viz/                 init · build · check · link_paths · wrap_terms
    typescript/            CLAUDE.md · src/ (components · runtime · page.tsx · index.ts · types.ts · theme.css) · svg.mjs · svg.d.mts · lib.mjs
  core/                    CLAUDE.md · pipeline.py · measure.py · dispatch.py
  common/                  python.py · template.py
  tools/                   CLAUDE.md · doctor.py · doctor_packages.py · gen_readme.py · setup.sh · cloud_env.sh (· scrub_local_paths.py, git-ignored)
  test/
    CLAUDE.md
    codewiki/              10 machine tests + test_mode1 · test_run_mode1
    term/                  test_run_mode1_5 · test_run_grade · test_term
    spec/                  test_run_mode2 · test_check · test_init · test_link_paths · test_wrap_terms · test_components · test_graph_math · test_config · svg.test.mjs
    core/                  test_pipeline · test_measure · test_import_isolation · test_dispatch
    common/                test_template · test_templates
    tools/                 test_gen_readme · test_portability
  qa/
    CLAUDE.md
    gates/                 test_docs_citations · test_no_any · test_prompt_resources · test_wiki
    evals/                 README.md · runs/*.json
  resource/
    CLAUDE.md
    codewiki/              prompts/ (annotate-symbols · lang-hint · outline-wiki · write-wiki) · faults.toml ·
                           templates/ (vitepress.config.mts.tmpl · dot/ ×3) · config.toml · samples/ (cpp · csharp-unity · OBSERVATION-template.md) ·
                           terms-reading.json
    term/                  prompts/ask.md
    spec/                  prompts/agent.md · templates/report/ (data.ts.tmpl · entry.ts · page.html.tmpl · render.mjs.tmpl · report.tsx.tmpl) · config.toml
  docs/
    superpowers/{plans,specs}   handoffs/ (+ remain-process-merged.md)   my.self/   decisions/   overturn/   wiki/   diagrams/
    notes/                 analysis-2026-08-31-cpp-collectors · 2026-09-19-mode1-역대-실측과-패치-이력 · 2패스개선 · runner_presudo
    research/              ← reports/* · research_notes/*
    CLAUDE.md · ai-readiness-map.html · ai-readiness-score.json · (png · pdf)
  split-work/              unchanged (deleted after Phase B); gains reorg/ (the one-off scripts of this plan)
  out/                     git-ignored, unchanged
  CLAUDE.md · ARCHITECTURE.md · README.md · package.json · package-lock.json · pyrightconfig.json · tsconfig.json · requirements.txt · skills-lock.json · .gitignore
  .agents/ · .claude/ · .gemini/ · .github/                                     (unchanged)

Gone: config/ · evals/ · resources/ · reports/ · research_notes/ · docs/prompt/ · runner/ · machine/ · viz/ ·
      machine/xmldoc.py · machine/test_xmldoc.py · machine/comments.xml · every `# <include …/>` block · the four generated README.md (regenerated in place)
```

## 4. Path map

The plan embeds `split-work/reorg/pathmap.py`, which turns these rules into a TSV and refuses to run if any tracked file is unmapped or two sources collide. Rules, in the order they apply: exact entries first, then directory prefixes (longest first), then "stays" (root files, `bin/`, `tools/`, `docs/`, `split-work/`, dot-directories).

| Current | Target | Note |
|---|---|---|
| `runner/run_mode1.py` · `runner/check_shard.py` · `runner/mode1/*.py` · `runner/wiki/*.py` | `codewiki/python/runner/…` | `mode1/` keeps its name |
| `runner/mode1/prompts/*.md` · `runner/mode1/faults.toml` · `runner/wiki/templates/*` | `resource/codewiki/prompts/` · `resource/codewiki/faults.toml` · `resource/codewiki/templates/` | |
| `machine/*.py` (not tests, not xmldoc) · `machine/roslyn-dump/` · `machine/terms-reading.json` | `codewiki/python/machine/` · `codewiki/csharp/roslyn-dump/` · `resource/codewiki/terms-reading.json` | |
| `viz/render_modules.py` · `viz/render_classes.py` · `viz/demermaid.py` · `viz/templates/dot/*` | `codewiki/python/viz/` · `resource/codewiki/templates/dot/` | Mode 1 drawings |
| `config/mode1.toml` · `resources/samples/**` · `resources/templates/OBSERVATION-template.md` | `resource/codewiki/config.toml` · `resource/codewiki/samples/` · `resource/codewiki/samples/OBSERVATION-template.md` | |
| `runner/run_mode1_5.py` · `runner/run_grade.py` · `runner/term/*` · `runner/prompts/ask.md` | `term/python/runner/…` · `resource/term/prompts/ask.md` | |
| `runner/run_mode2.py` · `runner/prompts/agent.md` | `spec/python/runner/run_mode2.py` · `resource/spec/prompts/agent.md` | |
| `viz/{__init__,init,build,check,link_paths,wrap_terms}.py` · `viz/src/**` · `viz/svg.mjs` · `viz/svg.d.mts` · `viz/lib.mjs` · `viz/templates/report/*` · `config/report.toml` | `spec/python/viz/` · `spec/typescript/src/` · `spec/typescript/` · `resource/spec/templates/report/` · `resource/spec/config.toml` | |
| `runner/pipeline.py` · `runner/measure.py` · `runner/dispatch.py` · `runner/__init__.py` | `core/` | |
| `tools/python.py` · `tools/template.py` | `common/` | `tools/` keeps doctor · doctor_packages · gen_readme · setup.sh · cloud_env.sh |
| `machine/test_*.py` (10) · `runner/test_mode1.py` · `runner/test_run_mode1.py` | `test/codewiki/` | |
| `runner/test_run_mode1_5.py` · `runner/test_run_grade.py` · `test/test_term.py` | `test/term/` | |
| `runner/test_run_mode2.py` · `test/test_{check,init,link_paths,wrap_terms,components,graph_math,config}.py` · `test/svg.test.mjs` | `test/spec/` | |
| `runner/test_{pipeline,measure,import_isolation}.py` · `test/test_dispatch.py` | `test/core/` | |
| `tools/test_template.py` · `test/test_templates.py` | `test/common/` | `test_templates` exercises `common/template.py` against both resource sets |
| `tools/test_gen_readme.py` · `test/test_portability.py` | `test/tools/` | |
| `test/test_docs_citations.py` · `test/test_no_any.py` · `test/test_prompt_resources.py` · `test/test_wiki.py` | `qa/gates/` | |
| `evals/README.md` · `evals/runs/*.json` | `qa/evals/` | |
| `reports/*.md` · `research_notes/**` | `docs/research/` | sub-folder names kept |
| `docs/analysis-2026-08-31-cpp-collectors.md` · `docs/2026-09-19-mode1-역대-실측과-패치-이력.md` · `docs/2패스개선.md` · `runner/runner_presudo.md` | `docs/notes/` | |
| `remain-process-merged.md` | `docs/handoffs/remain-process-merged.md` | stale 2026-08-31 todo; archive |
| `runner/CLAUDE.md` · `machine/CLAUDE.md` · `viz/CLAUDE.md` · `viz/src/CLAUDE.md` | `core/CLAUDE.md` · `codewiki/CLAUDE.md` · `spec/CLAUDE.md` · `spec/typescript/CLAUDE.md` | then restructured (§11) |
| `runner/README.md` · `machine/README.md` · `viz/README.md` · `tools/README.md` | deleted, regenerated for the nine Python directories | `tools/gen_readme.py` |
| `machine/xmldoc.py` · `machine/test_xmldoc.py` · `machine/comments.xml` · `docs/prompt/checklist.yaml` | deleted | |

Files Phase K added after the design commit (🔵 `6c4009d`): `machine/manifest.py` and `runner/mode1/seal.py` (Mode 1 seal) → `codewiki/python/machine/` · `codewiki/python/runner/mode1/`; `machine/evidence.py` and `machine/contract_types.py` (read by Mode 1.5 and Mode 2) → `common/`; their tests → `test/codewiki/` · `test/common/`; `tools/gen_contract*.py` stay in `tools/` with their tests in `test/tools/`; `contracts/` and `docs/contract-mode1-artifacts.md` stay (0011 names the contract path literally, in both repositories). The plan's path map lists these by name and fails on any other file added later, so each new file is placed consciously.

## 5. Deletions

| What | Count (🔵 2026-10-31) | Consequence |
|---|---|---|
| `# <include file="machine/comments.xml" …/>` blocks (marker + meaning line + optional uses line) | 686 markers in 62 files | Line numbers below each block shift up; the removed line numbers are recorded per file so citations can be renumbered exactly |
| `machine/xmldoc.py` | 1 | `terms_db.py` and `test_terms_db.py` import `Terms` from it → the three TypedDicts `Use` · `Term` · `Terms` move verbatim to a new `machine/reading_types.py` and the two import lines change (one line → one line) |
| `machine/test_xmldoc.py` · `machine/comments.xml` | 2 | Test count drops by the xmldoc tests |
| `docs/prompt/checklist.yaml` | 1 (0 bytes) | `docs/CLAUDE.md` row removed |
| `runner/README.md` · `machine/README.md` · `viz/README.md` · `tools/README.md` | 4 | Regenerated by `tools/gen_readme.py` at the new locations |

## 6. Invariants while executing

1. **Line count preservation.** In every moved file that existed before and is not a test file, the only content edits are one-line-for-one-line substitutions (`sys.path` depth, path strings, import renames) and the recorded block deletions. No insertions. This is what makes the citation renumbering a function, not an estimate.
2. **Archive untouched.** `docs/handoffs/`, `docs/superpowers/`, `docs/my.self/`, `docs/decisions/`, `docs/overturn/` keep their old paths (except the two rows this design itself adds to the resume document's change log and to the compass).
3. **Byte-identical outputs.** The 31 outputs of `split-work/capture.sh` (prompts, skeleton, VitePress config, DOT, `report.html`) are equal before and after.
4. **Green at every commit.** Each task ends with the six gates in the same state as the baseline (the two known reds stay red for their known reasons and nothing else goes red).
5. **No behaviour change.** No function body changes except the import lines named in §5 and the path constants named in §9.

## 7. Citation and identifier rewriting

| Target | What is rewritten | How |
|---|---|---|
| `docs/wiki/*.md` (203 `file:line` citations, 🔵) | Paths through the map; line numbers through the per-file removed-lines record | `split-work/reorg/remap_citations.py` |
| `resource/codewiki/terms-reading.json` (3,053 `where` fields, 1,318 ids, 1,735 `uses`, 🔵) | `where` and `uses[].where` (path:line); `module` (dotted or slashed directory); record ids, `uses[].to`, `depends_on` (dotted module ids derived from the Python file map; slashed file ids through the file map) | Same script; JSON re-serialised with the file's existing format (`indent=1`, `ensure_ascii=False`) after asserting that a no-op round trip is byte-identical |
| Context documents in `contextDocs()` (root and module `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, `.claude/CLAUDE.md`, three agents, three skills) | Paths and `file:line` citations | Same script; then the hand edits of §11 |
| `docs/diagrams/*.dot`, `qa/evals/README.md`, `split-work/README.md`, `split-work/*.py`, `split-work/*.sh`, `.gemini/PythonRule.md` | Paths | Same script |
| Code and configuration | Path strings, import statements, `sys.path` entries | §9 |

Ids that name a directory that splits across modes (`runner`, `viz`, `tools`, `test`) are left as they are and listed in the script's report; the L1/L2/L3 checks read `where`, not ids. Wiki page file names (`machine-*.md`, `runner-*.md`, `viz-*.md`) keep their old names until the next Mode 1 run.

A citation whose line was itself deleted (it pointed at an include marker) is reported, not silently moved. 🔵 None is expected: `where` points at declaration lines, which sit below the blocks.

## 8. Import and `sys.path` policy

Top-level packages after the move: `codewiki`, `term`, `spec`, `core`, `common`, `tools` (plus `test` and `qa`, which are not imported).

| Today | After | Where it appears |
|---|---|---|
| `from tools.template import …` · `from tools.python import …` | `from common.template import …` · `from common.python import …` | 11 statements |
| `from runner.dispatch import …` | `from core.dispatch import …` | `bin/*` ×3, `test_dispatch` |
| `import pipeline` · `import pipeline as P` · `from pipeline import …` · `import measure` · `from measure import …` | `from core import pipeline` · `from core import pipeline as P` · `from core.pipeline import …` · `from core import measure` · `from core.measure import …` | runners, `check_shard.py`, `mode1/lang.py`, tests, gates |
| `from runner.wiki.X import …` · `from runner.wiki import prep` | `from codewiki.python.runner.wiki.X import …` | 13 statements |
| `from runner.term.X import …` · `import runner.term.quiz` | `from term.python.runner.term.X import …` · `import term.python.runner.term.quiz` | 4 statements |
| `from viz.{init,check,link_paths,wrap_terms} import …` | `from spec.python.viz.… import …` | tests, `run_mode2.py` |
| `from viz.render_modules import …` | `from codewiki.python.viz.render_modules import …` | `render_classes.py`, `test_templates.py` |
| `from xmldoc import Terms` | `from reading_types import Terms` | `terms_db.py`, `test_terms_db.py` |
| flat sibling imports inside `machine/` (`import normalize`, `from codegraph_types import …`, …) and inside a `runner/` folder (`import run_mode1_5` from `run_grade.py`) | unchanged | they rely on the file's own directory being on `sys.path`, which stays true |

`ROOT` computation: files derive the repository root with a chain of `os.path.dirname(…)` calls; the chain grows by the file's depth change (+2 for `runner/x.py` → `codewiki/python/runner/x.py`, +2 for `runner/mode1/x.py`, +2 for `machine/x.py` and `viz/x.py`, 0 for `core/` and `common/`, +1 for tests and gates). The plan ships a checker that compares the chain length with the path depth for every `.py` file.

`sys.path` entries that named a directory (`os.path.join(ROOT, "runner")`, `"machine"`) are rewritten to the directory that now holds the modules the file imports: Mode 1 files → `codewiki/python/runner` and `codewiki/python/machine`; Mode 1.5 → `term/python/runner`; Mode 2 → `spec/python/runner` and `spec/python/viz`; the child script that `run_mode1_5.py` generates → `term/python/runner`; `tools/gen_readme.py` → `codewiki/python/machine`.

`pyrightconfig.json`: `include` = the six code roots plus `test` and `qa`; `exclude` adds `codewiki/csharp` and `spec/typescript`; `extraPaths` = `.`, the three `runner/` folders, `codewiki/python/machine`, `codewiki/python/viz`, `spec/python/viz`. 🔵 Today `test/` is not in `include`; its 16 files become type-checked for the first time — errors found there are fixed if trivial, otherwise the file is excluded by name and listed in the plan's final report.

## 9. Meta files and gates

| File | Change |
|---|---|
| `pyrightconfig.json` | §8 |
| `tsconfig.json` | `include` → `spec/typescript/src/**/*.ts`, `spec/typescript/src/**/*.tsx` |
| `package.json` | `pretest` → `node spec/typescript/lib.mjs` |
| `spec/typescript/lib.mjs` | `entryPoints: ["spec/typescript/src/index.ts"]` (outfile `.tmp/lib.mjs` unchanged) |
| `spec/python/viz/build.py` · `check.py` | esbuild aliases and the generated tsconfig `paths` → `spec/typescript/src/index.ts` · `types.ts` · `spec/typescript/svg.mjs`; `theme.css`; `runtime/term-graph.ts`; `TEMPLATES` → `resource/spec/templates/report` |
| `spec/python/viz/init.py` · `spec/python/runner/run_mode2.py` | `resource/spec/config.toml`; `resource/spec/prompts`; stage scripts under `spec/python/viz/` |
| `term/python/runner/run_mode1_5.py` | `term/python/runner/term/<name>`, `term/python/runner/run_mode1_5.py`, `resource/term/prompts`, child-script `sys.path` |
| `codewiki/python/runner/mode1/context.py` | `PROMPT_DIR` → `resource/codewiki/prompts`; `CONFIG_PATH` → `resource/codewiki/config.toml`; `FAULTS_PATH` → `resource/codewiki/faults.toml`; `reading_path()` → `resource/codewiki/terms-reading.json` for self-hosting (the target-repository branch `docs/codegraph/` is unchanged) |
| `codewiki/python/runner/mode1/terms.py` · `machine_stage.py` · `wiki/{build,check,prep}.py` | child-process targets → `codewiki/python/machine/*.py`, `codewiki/python/viz/*.py`, `codewiki/python/runner/wiki/*.py`; `TEMPLATES` → `resource/codewiki/templates` |
| `codewiki/python/viz/render_modules.py` · `render_classes.py` | `TEMPLATES` → `resource/codewiki/templates/dot` |
| `bin/report-wiki` · `report-term` · `report-spec` | `from core.dispatch import run_dispatch`; command tables → new script paths |
| `tools/gen_readme.py` | `DIR_ROLE` keyed by the nine Python directories; `BANNER` command; `machine` on `sys.path` → `codewiki/python/machine` |
| `tools/setup.sh` | `node spec/typescript/lib.mjs` |
| `.github/workflows/docs-gates.yml` | `qa/gates/test_docs_citations.py qa/gates/test_no_any.py`; `gen_readme.py --check` with the nine directories |
| `.gitignore` | add `split-work/reorg/out/` |
| `qa/gates/test_prompt_resources.py` | `CODE_TOPS = ("codewiki", "term", "spec", "core", "common", "tools")`; templates glob `resource/*/templates/**`; prompts glob `resource/*/prompts/*.md` and `resource/*/faults.toml`; runner lookup table by mode; `from core import pipeline as P` |
| `qa/gates/test_no_any.py` | `COVERED` paths through the map |
| `qa/gates/test_docs_citations.py` | `contextDocs()` → the new module `CLAUDE.md` set (§11) |
| `split-work/capture.sh` · `capture.py` · `split_reading.py` | paths through the map |
| `~/.claude/skills/spec-review-dashboard/SKILL.md` · `term-benchmark/SKILL.md` (outside the repository) | same path rewrite as their in-repository copies, so the copies do not drift from the originals |

## 10. Verification

```bash
# baseline (Task 0) and after every task
.venv/bin/python -m pytest -q                    # pass count = baseline − xmldoc tests; the two known reds only
npm test                                         # 8
npm run typecheck                                # 0 errors
npm run typecheck:py                             # 0 errors
.venv/bin/python tools/gen_readme.py --check codewiki/python/runner codewiki/python/machine codewiki/python/viz \
    term/python/runner spec/python/runner spec/python/viz core common tools
npm run doctor
split-work/capture.sh "$PWD" split-work/after-reorg && diff -r split-work/before-reorg split-work/after-reorg   # empty
.venv/bin/python bin/report-wiki prep . && .venv/bin/python bin/report-wiki check .   # L1/L2 counts equal to baseline
```

Plus: `report-spec`, `report-term`, `report-wiki` with no arguments print their usage lines from `PATH`; `git log --follow codewiki/python/machine/normalize.py` shows the pre-move history.

## 11. Documentation restructure

| Target | Source | Content change beyond path substitution |
|---|---|---|
| root `CLAUDE.md` | itself | The compass table (module docs), the "성격축 셋" section becomes "축 셋 — mode · 언어 · 성격", the architecture tree, the "리소스와 코드를 가른다" rule (locations → `resource/<mode>/`), the command block, the gate table commands, the entry-point table paths, the "파이썬이 본체" table, the skills note |
| `codewiki/CLAUDE.md` | `machine/CLAUDE.md` | Title and intro say Mode 1; the "무엇이 여기 있나" table gains the runner and viz rows that `runner/CLAUDE.md` and `viz/CLAUDE.md` held for Mode 1; the xmldoc row is removed; Owns/Cross-module tables name `core/` and `resource/codewiki/` |
| `core/CLAUDE.md` | `runner/CLAUDE.md` | Keeps the stage machine, the two-direction child-process section, the flow-building section; the Mode 1 stage-adding pattern moves to `codewiki/CLAUDE.md`; the Mode 1.5 lines move to `term/CLAUDE.md`; a short "common/" section |
| `spec/CLAUDE.md` | `viz/CLAUDE.md` | Drops the Mode 1 drawing sections (render · demermaid → `codewiki/CLAUDE.md`); keeps render path, SVG inline rule, init slug check, check's term comparison |
| `spec/typescript/CLAUDE.md` | `viz/src/CLAUDE.md` | Paths only |
| `term/CLAUDE.md` · `qa/CLAUDE.md` · `resource/CLAUDE.md` | new, short | What lives here, who reads it, the gate list / resource rules (0012 + 0014) |
| `test/CLAUDE.md` | itself | Rewritten: tests by mode, gates moved to `qa/`, commands |
| `tools/CLAUDE.md` | itself | `python.py` and `template.py` rows removed |
| `docs/CLAUDE.md` | itself | `prompt/` row removed; `notes/` and `research/` rows added |
| `ARCHITECTURE.md` · `README.md` | themselves | §1 flowchart and §4 layer diagram node labels; command blocks; the "무엇이 어디에 사는가" table |
| nine `README.md` | generated | `tools/gen_readme.py` |

## 12. Open items (not decided by this design)

- Any top-level directory created after `6c4009d` — classified when the plan runs (default: stays at the root).
- `machine/test_survey_plan.py::test_이_저장소_실측` — the layer distribution changes again after the move; the root `CLAUDE.md` rule ("find out why machines differ before touching the expected value") stands.
- The 16 formerly type-unchecked test files (§8).
- Renaming `runner/mode1/` inside `codewiki/` — deferred; separate commit if ever.

## 13. New-structure declaration (design-decision-discipline §2.5, 🔵 2026-10-31)

1. Implementers — `core/` 3 files, `common/` 2 files, `qa/gates/` 4 files, `resource/` 43 files (6 prompts, 1 fault table, 9 templates, 2 configs, 24 golden-shape files, 1 record).
2. Consumers — `pipeline.py` 16 files, `measure.py` 7, `dispatch.py` 3 entry points, `python.py` 5, `template.py` 6; resource consumers are the stage classes (`prompt_names`) and the `render_file` call sites.
3. Deletion test — without `core/` and `common/` the five shared files have no mode to belong to and stay mixed into `runner/` and `tools/`, as today; 0011's Phase B must copy exactly these five into the second repository.
4. Relation to the plan documents — inside 0011 (pre-step, between M and B).
