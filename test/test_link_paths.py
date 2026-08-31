import os
from pathlib import Path

from viz.link_paths import expandRoot, linkPaths, makeResolver, pathPattern


def fixture(tmp_path):
    root = tmp_path / "root"
    (root / "docs/handoffs").mkdir(parents=True)
    (root / "specs/slug").mkdir(parents=True)
    (root / "ext/facts").mkdir(parents=True)
    (root / "docs/handoffs/HANDOFF-x.md").write_text("x")
    (root / "specs/2026-01-01-slug-design.md").write_text("spec")
    (root / "ext/facts/modules.md").write_text("m")
    (root / "ext/codegraph.json").write_text("{}")
    cwd = root / "specs/slug"
    index = {"HANDOFF-x.md": ["docs/handoffs/HANDOFF-x.md"],
             "dup.md": ["a/dup.md", "b/dup.md"]}
    resolve = makeResolver([str(cwd), str(root / "specs"), str(root), str(root / "ext")],
                           str(root), index)
    return root, resolve


def href(p) -> str:
    return Path(p).as_uri()


def test_linkPaths_links_existing_file_and_keeps_line_number(tmp_path):
    root, resolve = fixture(tmp_path)
    out = linkPaths('<span class="mono">docs/handoffs/HANDOFF-x.md:900</span>', resolve)
    assert out == (
        '<span class="mono"><a class="path-link" target="_blank" rel="noopener" '
        'href="%s">docs/handoffs/HANDOFF-x.md:900</a></span>'
        % href(root / "docs/handoffs/HANDOFF-x.md"))


def test_linkPaths_finds_design_doc_in_parent_specs(tmp_path):
    root, resolve = fixture(tmp_path)
    out = linkPaths("<p>근거 2026-01-01-slug-design.md:311-312 참조</p>", resolve)
    assert ('href="%s">2026-01-01-slug-design.md:311-312</a>'
            % href(root / "specs/2026-01-01-slug-design.md")) in out


def test_linkPaths_uses_index_only_when_unique(tmp_path):
    root, resolve = fixture(tmp_path)
    out = linkPaths("<p>HANDOFF-x.md 와 dup.md</p>", resolve)
    assert ('href="%s">HANDOFF-x.md</a>' % href(root / "docs/handoffs/HANDOFF-x.md")) in out
    assert ">dup.md</a>" not in out


def test_linkPaths_links_glob_to_dir_and_leaves_missing_files(tmp_path):
    root, resolve = fixture(tmp_path)
    out = linkPaths("<p>facts/*.md 와 facts/calls.md 와 codegraph.json</p>", resolve)
    facts = href(root / "ext/facts")
    assert ('href="%s">facts/*.md</a>' % facts) in out or ('href="%s/">facts/*.md</a>' % facts) in out
    assert ">facts/calls.md</a>" not in out
    assert '">codegraph.json</a>' in out


def test_linkPaths_skips_term_ref_headings_and_graphs(tmp_path):
    _, resolve = fixture(tmp_path)
    html = "".join([
        '<span class="term-ref" tabindex="0">HANDOFF-x.md<span class="term-card">HANDOFF-x.md</span></span>',
        '<a href="#">HANDOFF-x.md</a>',
        "<h2>HANDOFF-x.md</h2>",
        "<th>HANDOFF-x.md</th>",
        "<summary>HANDOFF-x.md</summary>",
        "<script>HANDOFF-x.md</script>",
        "<svg><text>HANDOFF-x.md</text></svg>",
        '<div class="card term-groups"><td class="mono">HANDOFF-x.md</td></div>',
        '<div class="term-graph" data-terms="HANDOFF-x.md"></div>',
    ])
    assert linkPaths(html, resolve) == html


def test_linkPaths_is_idempotent(tmp_path):
    _, resolve = fixture(tmp_path)
    once = linkPaths('<span class="mono">docs/handoffs/HANDOFF-x.md</span>', resolve)
    assert linkPaths(once, resolve) == once


def test_pathPattern_matches_only_path_shapes():
    re_path = pathPattern()
    def hits(s):
        return [m.group(0) for m in re_path.finditer(s)]
    assert hits("a/b.md:3 c.json facts/*.md x.py") == ["a/b.md:3", "c.json", "facts/*.md", "x.py"]
    assert hits("버전 1.2 와 C-19 와 calls[] 와 http://x.com/a.md") == []


def test_makeResolver_honours_base_order(tmp_path):
    root = tmp_path / "order"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    (root / "a/x.json").write_text("a")
    (root / "b/x.json").write_text("b")
    r1 = makeResolver([str(root / "a"), str(root / "b")], str(root), {})
    r2 = makeResolver([str(root / "b"), str(root / "a")], str(root), {})
    assert r1("x.json")["href"] == href(root / "a/x.json")
    assert r2("x.json")["href"] == href(root / "b/x.json")


def test_expandRoot_expands_var_forms():
    os.environ["RB_TEST_ROOT"] = "/tmp/rb-test"
    try:
        assert expandRoot("$RB_TEST_ROOT/out") == "/tmp/rb-test/out"
        assert expandRoot("${RB_TEST_ROOT}/out") == "/tmp/rb-test/out"
    finally:
        del os.environ["RB_TEST_ROOT"]


def test_expandRoot_blanks_absent_var():
    os.environ.pop("RB_ABSENT_ROOT", None)
    assert expandRoot("$RB_ABSENT_ROOT/out") == "/out"


def test_expandRoot_expands_leading_tilde():
    assert expandRoot("~/x") == os.path.join(os.path.expanduser("~"), "x")
    assert expandRoot("/a/~/b") == "/a/~/b"
