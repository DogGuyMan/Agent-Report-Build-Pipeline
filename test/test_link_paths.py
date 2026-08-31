import pytest
import os
import shutil
from viz.link_paths import makeResolver, buildIndex, linkPaths

def test_makeResolver_finds_file_in_bases(tmp_path):
    repo = tmp_path / "repo"
    base1 = repo / "b1"
    base1.mkdir(parents=True)
    (base1 / "a.cpp").touch()
    
    resolve = makeResolver([str(base1)], str(repo))
    assert resolve("a.cpp") == "b1/a.cpp"

def test_makeResolver_finds_via_index(tmp_path):
    repo = tmp_path / "repo"
    deep = repo / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "target.cpp").touch()
    
    idx = buildIndex(str(repo))
    resolve = makeResolver([], str(repo), idx)
    assert resolve("target.cpp") == "a/b/c/target.cpp"

def test_linkPaths_wraps_in_anchor():
    def dummy_resolve(p):
        return "repo/src/" + p
    
    html = "<p>See src/main.cpp for details</p>"
    out = linkPaths(html, dummy_resolve)
    assert '<a class="path-link" href="file://repo/src/src/main.cpp">src/main.cpp</a>' in out
