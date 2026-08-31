import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runner.wiki.paths import wikiPaths, collectorFor, collectorFromSelect
from runner.wiki.prep import prepPlan
from runner.wiki.build import sidebarFrom, vitepressConfig
from runner.wiki.check import checkArgs
from runner.wiki.compdb import mergeEntries, relativeFiles, clangUmlConfig, EXTERNAL_MARKERS
from runner.wiki.clang_doc import clangDocCandidates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_wiki_paths():
    p = wikiPaths("/tmp/repo")
    assert p["wiki"] == "/tmp/repo/docs/wiki"
    assert p["raw"] == "/tmp/repo/out/codegraph-raw"
    assert p["built"] == "/tmp/repo/out/codegraph-raw/wiki-built"
    assert p["site"] == "/tmp/repo/out/codegraph-raw/wiki-site"
    assert p["codegraph"] == "/tmp/repo/out/codegraph-raw/codegraph.json"

def test_collector_for():
    assert collectorFor(["Assembly-CSharp.csproj", "Assets"]) == "roslyn-dump"
    assert collectorFor(["StickRushGame.slnx"]) == "roslyn-dump"
    assert collectorFor(["CMakeLists.txt", "core", "server"]) == "clang-uml"
    assert collectorFor(["CMakeLists.txt", "Assembly-CSharp.csproj"]) == "roslyn-dump"
    assert collectorFor(["package.json", "src"]) == "none"

def test_prep_plan():
    out0 = prepPlan("clang-uml", True, True, False, False)
    assert out0["steps"] == ["facts", "render-modules"]
    assert out0["blocked"] is None

    out1 = prepPlan("clang-uml", False, True, False, False)
    assert out1["steps"] == ["clang-uml", "normalize", "facts", "render-modules"]
    assert out1["blocked"] is None

    out2 = prepPlan("clang-uml", False, False, False, False)
    assert out2["steps"] == []
    assert ".clang-uml" in out2["blocked"]

    out3 = prepPlan("roslyn-dump", False, False, True, False)
    assert out3["steps"] == ["normalize", "facts", "render-modules"]
    assert out3["blocked"] is None

    out4 = prepPlan("roslyn-dump", False, False, False, False)
    assert out4["steps"] == []
    assert "roslyn-dump.json" in out4["blocked"]

    out5 = prepPlan("none", False, False, False, False)
    assert out5["steps"] == []
    assert "수집기" in out5["blocked"]

    out6 = prepPlan("clang-uml", False, True, False, True)
    assert out6["steps"] == ["clang-uml", "clang-doc", "normalize", "facts", "render-modules"]

    out7 = prepPlan("clang-uml", False, True, False, False)
    assert out7["steps"] == ["clang-uml", "normalize", "facts", "render-modules"]
    assert out7["blocked"] is None

    out8 = prepPlan("roslyn-dump", False, False, True, True)
    assert "clang-doc" not in out8["steps"]

def test_report_wiki_dispatch():
    with open(os.path.join(ROOT, "bin", "report-wiki"), "r", encoding="utf-8") as f:
        src = f.read()
    assert 'prep": "runner/wiki/prep.py"' in src or 'prep: "runner/wiki/prep.py"' in src or 'runner/wiki/prep.py' in src
    assert 'build": "runner/wiki/build.py"' in src or 'build: "runner/wiki/build.py"' in src or 'runner/wiki/build.py' in src
    assert 'check": "runner/wiki/check.py"' in src or 'check: "runner/wiki/check.py"' in src or 'runner/wiki/check.py' in src
    assert "runDispatch" in src or "runner/wiki" in src
    assert "아직 이 진입점은 비어 있다" not in src

def test_build():
    assert sidebarFrom(["managers.md", "data.md", "index.md"]) == [{"text": "data", "link": "/data"}, {"text": "managers", "link": "/managers"}]
    assert sidebarFrom(["index.md"]) == []
    assert sidebarFrom(["a.md", "assets", "b.svg"]) == [{"text": "a", "link": "/a"}]
    
    cfg1 = vitepressConfig("StickRushGame", [{"text": "data", "link": "/data"}], "../wiki-site")
    assert 'title: "StickRushGame 코드베이스 위키"' in cfg1
    assert 'outDir: "../wiki-site"' in cfg1
    assert '{ text: "data", link: "/data" }' in cfg1
    assert 'from "vitepress"' not in cfg1
    assert 'export default ({' in cfg1

    cfg2 = vitepressConfig('Qt"Vision', [], "../wiki-site")
    assert 'title: "Qt\\"Vision 코드베이스 위키"' in cfg2

def test_check_args():
    assert checkArgs("/tmp/r", "/tmp/r/cg.json", None, ["/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md"]) == ["--repo", "/tmp/r", "--codegraph", "/tmp/r/cg.json", "/tmp/r/docs/wiki/a.md", "/tmp/r/docs/wiki/b.md"]
    assert checkArgs("/tmp/r", "/tmp/r/cg.json", "/tmp/r/rd.json", ["/tmp/r/docs/wiki/a.md"]) == ["--repo", "/tmp/r", "--codegraph", "/tmp/r/cg.json", "--detail", "/tmp/r/rd.json", "/tmp/r/docs/wiki/a.md"]

def test_compdb():
    e = lambda f: {"file": f"/r/{f}", "directory": "/r/b"}
    out0 = mergeEntries([[e("a.cpp"), e("b.cpp")], [e("b.cpp"), e("c.cpp")]], "/r")
    assert [x["file"] for x in out0] == ["/r/a.cpp", "/r/b.cpp", "/r/c.cpp"]

    out1 = mergeEntries([[{"file": "/other/x.cpp"}, {"file": "/r/y.cpp"}]], "/r")
    assert [x["file"] for x in out1] == ["/r/y.cpp"]

    out2 = mergeEntries([[{"file": "/r/src/a.cpp"}, {"file": "/r/vcpkg_installed/x.cpp"}, {"file": "/r/b/vedit_autogen/moc_x.cpp"}, {"file": "/r/build/CMakeFiles/y.cpp"}]], "/r")
    assert [x["file"] for x in out2] == ["/r/src/a.cpp"]
    
    for m in ["autogen", "/vcpkg_installed/", "moc_"]:
        assert m in EXTERNAL_MARKERS

    out4 = relativeFiles([{"file": "/r/b.cpp"}, {"file": "/r/a.cpp"}, {"file": "/r/b.cpp"}], "/r")
    assert out4 == ["a.cpp", "b.cpp"]

    cfg = clangUmlConfig(
        compdbDir="/r/out/compdb", repo="/r", outDir="/r/out",
        files=["app/src/view/mainwindow.cpp", "core/panorama/warp.cpp"],
        flags=["-resource-dir=/x"], paths=["app", "core"]
    )
    assert "*" not in cfg
    assert "- app/src/view/mainwindow.cpp" in cfg
    assert "- core/panorama/warp.cpp" in cfg
    assert "- -resource-dir=/x" in cfg
    assert "paths: [app, core]" in cfg

def test_clang_doc():
    out0 = clangDocCandidates({"CLANG_DOC": "/내가/고른/clang-doc", "PATH": ""}, [])
    assert out0[0] == "/내가/고른/clang-doc"
    
    out1 = clangDocCandidates({"PATH": "/usr/bin:/bin"}, ["/opt/llvm"])
    assert out1 == ["/opt/llvm/bin/clang-doc", "/usr/bin/clang-doc", "/bin/clang-doc"]
    
    out2 = clangDocCandidates({"PATH": "/usr/bin"}, [])
    assert out2 == ["/usr/bin/clang-doc"]
    assert not any("homebrew" in p for p in out2)
