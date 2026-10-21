# Regenerate Existing Skills from Latest SDK Sources

Use this workflow when an existing skill has stale examples, outdated API signatures,
or changed package guidance.

1. **Identify canonical source files first**

For Azure SDK language skills, use official upstream source docs and examples as the source of truth:

- Go: `https://github.com/Azure/azure-sdk-for-go/tree/main/sdk/<service>/<module>/README.md`
- Go examples: `https://github.com/Azure/azure-sdk-for-go/tree/main/sdk/<service>/<module>/`
- Rust: `https://github.com/Azure/azure-sdk-for-rust/tree/main/sdk/<service>/<crate>/README.md`
- Rust examples: `https://github.com/Azure/azure-sdk-for-rust/tree/main/sdk/<service>/<crate>/examples/`
- .NET/Java/Python/TS/Go: use current Microsoft Learn package docs + official SDK repos

2. **Refresh skill content surgically**

- Update code snippets to match current constructor/method signatures
- Keep crate/package names aligned with official publisher guidance
- Preserve skill structure/frontmatter unless intentionally changing behavior
- Update "Best Practices" and "Reference Links" when upstream recommendations change
- For Rust, if code uses `azure_core` types/imports directly, ensure `azure_core` is present in `Cargo.toml`; if only service-crate re-exports are used, direct `azure_core` dependency is optional

### API Surface Parity Gate (required for every regenerated skill)

Use the language-specific authoritative source as the contract for every snippet in the regenerated skill:

- **Python, .NET, Java, TypeScript, Go**: Treat the current Microsoft Learn API reference as the contract.
- **Rust**: Treat the official SDK repository (`https://github.com/Azure/azure-sdk-for-rust`) and crates.io documentation as the contract; Rust packages do not have Learn API-reference pages.

Before finalizing any regenerated skill:

1. Identify each SDK type/method shown in snippets (clients, operation groups, model constructors, enum members, long-running methods like `begin_*`).
2. Verify each symbol and signature against the authoritative source for that language/package (see above).
3. If the authoritative source shows a different shape (for example nested `properties=...` models, renamed methods, `begin_*` LRO methods), update the snippet to match.
4. Re-check imports so model/client modules match the authoritative source exactly.
5. Do not keep compatibility shortcuts that contradict authoritative examples in primary snippets.

### Scenario Coverage Gate (required for every regenerated skill, all languages)

Regeneration is not complete when snippets compile — it is complete when the skill demonstrates real usage breadth.

Before finalizing any regenerated skill:

1. Identify **hero scenarios** from the current authoritative docs/samples for that SDK (Microsoft Learn where available; otherwise the upstream SDK repo and package documentation).
2. Ensure each hero scenario is represented in the skill with copy-pastable snippets (or an explicit link to a bundled reference file when too large).
3. Add/refresh test scenarios so hero flows are validated by harness patterns.
4. Add at least **one important non-hero scenario** (for example: update/patch, delete/cleanup, export/import, advanced auth mode, paging/filtering, retries/error handling, or LRO monitoring) when supported by the SDK. For Python SDKs that support both sync and async clients, present both forms with equal priority; do not treat either as universally preferred.
5. For Azure SDK skills, structure `references/` as:
   - `references/capabilities.md` as a concise index that records each hero scenario and where it is covered (`SKILL.md` or a bundled reference), plus links to deeper non-hero references, with no historical/migration narration.
   - `references/non-hero-scenarios.md` for concrete non-hero examples that are intentionally kept out of the main `SKILL.md`.
   - Additional `references/*.md` files for specialized deep-dives (operation groups, tools, evaluator matrices, etc.).
6. If the SDK has broad operation-group coverage (common in management SDKs), include an operation-group table and explicitly call out which groups are covered in snippets vs. referenced only.
7. Never claim "full API surface" unless the skill genuinely demonstrates all major operation groups; otherwise state that the skill is optimized for hero workflows plus selected secondary scenarios.

### Regeneration Workflow Step 3: Validate Regenerated Skill Behavior

```bash
(cd tests && pnpm harness <skill-name> --mock --verbose)
```

If the skill has a Vally scenario, run that eval as well (locally or in CI) before finalizing.

**Rust regeneration gate (required for Rust skills):**

When regenerating any Rust skill, verify the generated `## Best Practices` section contains these exact first two rules:

1. `Use cargo add to manage dependencies, never edit Cargo.toml directly`
2. `Add azure_core only when importing azure_core types directly`

Use a content check before finalizing:

```bash
rg -n "Use `cargo add` to manage dependencies, never edit `Cargo.toml` directly|Add `azure_core` only when importing `azure_core` types directly" .github/plugins/azure-sdk-rust/skills/**/SKILL.md
```

The regeneration is not complete unless both lines are present in each affected Rust skill.

### Regeneration Workflow Step 4: Regenerate Docs Artifacts After Refresh

```bash
(cd docs-site && npx tsx scripts/extract-skills.ts && npm run build)
```

### Regeneration Workflow Step 5: Record What Changed

In the PR/commit notes, include:

- Which upstream docs/examples were used
- Which snippets/signatures were corrected
- Which tests/evals were run and their outcomes

#### Python plugin batch recipe: `azure-sdk-python`

Use this when the request is "regenerate all Python skills under azure-sdk-python."

1. **Scope the exact targets first**

```bash
# Canonical source of truth for Python plugin skills
ls .github/plugins/azure-sdk-python/skills/*/SKILL.md
```

- Treat `.github/plugins/azure-sdk-python/skills/` as canonical.
- Keep `.github/skills/<name>` links in sync after edits (symlink check/fix step below).

2. **For each skill, refresh from authoritative sources**

- Always use `microsoft-docs` MCP first for current Microsoft Learn API guidance.
- Verify the installed package version with `pip show <package>`, then inspect the installed package or official API reference to verify every symbol and signature used in snippets.
- For Azure SDK skills, prefer package overview + official SDK repo examples.
- For non-Azure Python skills in this plugin (for example `fastapi-router-py`, `pydantic-models-py`), keep language-specific best-practice variants and skip Azure-specific auth callouts when lifecycle/auth is not applicable.

3. **Apply Python enforcement rules consistently**

- Keep the standard section order for Azure SDK Python skills.
- Ensure `## Authentication & Lifecycle` starts with the required callout block (verbatim) when applicable.
- Ensure every client example uses `with` / `async with` lifecycle patterns.
- Ensure `## Best Practices` starts with the two required user-facing rules (or the documented variant for async-only/provider-pattern skills).
- Ensure each regenerated Azure SDK Python skill has `references/capabilities.md` (index) and `references/non-hero-scenarios.md` (concrete non-hero examples).
- Keep existing references/assets/scripts unless stale or incorrect.

4. **Validate all regenerated Python skills**

```bash
# Fast frontmatter/structure validation for every Python skill
python .github/skills/skill-creator/scripts/quick_validate.py .github/plugins/azure-sdk-python/skills/<skill-name>

# Run Python skill harness in mock mode (all *-py scenarios)
(cd tests && pwsh ./run-harness-by-language.ps1 -Language py -Mock)
```

5. **Sync skill links and docs artifacts**

```bash
# Ensure .github/skills links point at plugin canonical skills
python .github/scripts/sync_skill_links.py --plugin azure-sdk-python --check
python .github/scripts/sync_skill_links.py --plugin azure-sdk-python --apply

# Refresh docs site data after content changes
(cd docs-site && npx tsx scripts/extract-skills.ts && npm run build)
```

6. **Completion criteria for batch regeneration**

- Every targeted `.github/plugins/azure-sdk-python/skills/*/SKILL.md` is updated or explicitly confirmed current.
- Harness mock run for `-py` skills passes without regressions.
- Skill links are in sync for `azure-sdk-python`.
- PR notes include upstream docs used, signature corrections, and validation outcomes.
