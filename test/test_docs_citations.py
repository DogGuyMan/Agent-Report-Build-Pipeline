import pytest
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITE = re.compile(
    r'([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot)):(\d+)(?:-(\d+))?'
)

PATH_REF = re.compile(
    r'(?<![A-Za-z0-9_$/@~.-])((?:\.\./)*(?:\.?[A-Za-z0-9_@+~-]+/)+[A-Za-z0-9_@.+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot|html|css|xml))(?![A-Za-z0-9])'
)

def contextDocs(root=ROOT, exists=os.path.exists):
    docs = ["CLAUDE.md", "README.md", "ARCHITECTURE.md",
            "machine/CLAUDE.md", "viz/CLAUDE.md", "viz/src/CLAUDE.md",
            "runner/CLAUDE.md", "tools/CLAUDE.md",
            "docs/CLAUDE.md"]
    return [d for d in docs if exists(os.path.join(root, d))]

def isExempt(p):
    return p.startswith("out/") or "<" in p or ">" in p

def stripExternalTrees(text):
    def repl(m):
        block = m.group(1)
        lines = block.split('\n')
        first_line = next((l for l in lines if l.strip()), "")
        if re.match(r'^\s*\$[A-Za-z_][A-Za-z0-9_]*/', first_line):
            return ""
        return m.group(0)
    return re.sub(r'```[^\n]*\n([\s\S]*?)```', repl, text)

def pathRefsIn(text):
    body = stripExternalTrees(text)
    refs = []
    for m in PATH_REF.finditer(body):
        p = m.group(1)
        if not isExempt(p):
            refs.append(p)
    # maintain insertion order while removing duplicates
    return list(dict.fromkeys(refs))

def brokenPathRefs(text, docRel=".", root=ROOT, exists=os.path.exists):
    base = os.path.dirname(os.path.join(root, docRel))
    broken = []
    for p in pathRefsIn(text):
        if not exists(os.path.join(root, p)) and not exists(os.path.join(base, p)):
            broken.append(p)
    return broken

def citationsIn(text):
    out = []
    for m in CITE.finditer(text):
        if m.start() > 0 and text[m.start() - 1] == "$":
            continue
        out.append({"path": m.group(1), "line": int(m.group(2)), "index": m.start()})
    return out

def brokenCitations(text, root=ROOT, exists=os.path.exists):
    return [c for c in citationsIn(text) if not exists(os.path.join(root, c["path"]))]

def test_citations_env_var():
    assert len(citationsIn("보라 `$GRAPHICS_REPO/src/a.h:67` 을")) == 0
    assert len(citationsIn("보라 `viz/src/a.h:67` 을")) == 1

def test_citations_extension():
    assert len(citationsIn("3:4 로 나뉜다")) == 0
    assert len(citationsIn("`viz/build.mjs:152`")) == 1

def test_context_docs_finds_at_least_one():
    docs = contextDocs()
    assert "CLAUDE.md" in docs

def test_path_refs_skips_env_and_placeholders():
    assert len(pathRefsIn("`$GRAPHICS_REPO/doc/a.html` 를 보라")) == 0
    assert len(pathRefsIn("`specs/<slug>/data.ts` 가 생긴다")) == 0
    assert len(pathRefsIn("`out/report.html` 이 나온다")) == 0
    assert pathRefsIn("`viz/build.mjs` 가 짓는다") == ["viz/build.mjs"]

def test_path_refs_skips_bare_filenames():
    assert len(pathRefsIn("저자는 `data.ts` 를 고친다")) == 0

def test_path_refs_catches_dotted_folders():
    assert pathRefsIn("`.claude/CLAUDE.md` 의 13개") == [".claude/CLAUDE.md"]

def test_path_refs_catches_sibling_modules():
    assert pathRefsIn("컴포넌트는 `../viz/src/CLAUDE.md`") == ["../viz/src/CLAUDE.md"]
    assert pathRefsIn("나침반은 `../CLAUDE.md`") == []

def test_path_refs_strips_external_trees_but_keeps_repo_blocks():
    external = "```\n$GRAPHICS_REPO/doc/\n  superpowers/specs/a.html\n```"
    assert len(pathRefsIn(external)) == 0
    internal = "```bash\ncd $REPO_ROOT\n.venv/bin/python machine/facts.py\n```"
    assert "machine/facts.py" in pathRefsIn(internal)

def test_path_refs_does_not_truncate_extensions():
    assert pathRefsIn("`viz/src/theme.css`") == ["viz/src/theme.css"]
    assert pathRefsIn("`a/terms.json`") == ["a/terms.json"]
    assert pathRefsIn("`a/b.html`") == ["a/b.html"]
    assert pathRefsIn("`viz/src/components/x.tsx`") == ["viz/src/components/x.tsx"]

def test_real_docs_have_no_broken_links():
    for rel in contextDocs():
        with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as f:
            text = f.read()
        broken = brokenCitations(text)
        assert len(broken) == 0, f"{rel} has broken citations"
        broken_paths = brokenPathRefs(text, rel)
        assert len(broken_paths) == 0, f"{rel} has broken paths"
