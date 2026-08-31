import pytest
import subprocess
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_ts_eval(script_body: str) -> str:
    # We compile the TS to JS on the fly using esbuild, then run it in Node
    script = f"""
    import {{ components, bounds, clampBox, rectOverlap }} from "./viz/src/runtime/graph-math.ts";
    {script_body}
    """
    tmp_path = os.path.join(ROOT, ".tmp-eval-math.ts")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(script)
    try:
        # bundle it to avoid module resolution issues
        esbuild = subprocess.run(["npx", "esbuild", tmp_path, "--bundle", "--format=esm", "--platform=node"], 
                                 capture_output=True, text=True, cwd=ROOT)
        if esbuild.returncode != 0:
            raise RuntimeError(esbuild.stderr)
            
        res = subprocess.run(["node", "--input-type=module", "-e", esbuild.stdout], capture_output=True, text=True, cwd=ROOT)
        if res.returncode != 0:
            raise RuntimeError(res.stderr)
        return res.stdout.strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_components_connected_nodes():
    script = """
    const comp = components(["a", "b", "c", "d", "e"], [["a", "b"], ["b", "c"], ["d", "e"]]);
    console.log(comp.get("a") === comp.get("b"));
    console.log(comp.get("b") === comp.get("c"));
    console.log(comp.get("d") === comp.get("e"));
    console.log(comp.get("a") !== comp.get("d"));
    """
    out = run_ts_eval(script).split('\n')
    assert out == ["true", "true", "true", "true"]

def test_components_isolated_nodes():
    script = """
    const comp = components(["x", "y"], []);
    console.log(comp.get("x") !== comp.get("y"));
    console.log(comp.size === 2);
    """
    out = run_ts_eval(script).split('\n')
    assert out == ["true", "true"]

def test_bounds():
    script = """
    const b1 = bounds(800, 400, 2);
    console.log(b1.minX === -400 && b1.maxX === 1200 && b1.minY === -200 && b1.maxY === 600);
    const b2 = bounds(800, 400, 1);
    console.log(b2.minX === 0 && b2.maxX === 800 && b2.minY === 0 && b2.maxY === 400);
    """
    assert run_ts_eval(script).split('\n') == ["true", "true"]

def test_clampBox():
    script = """
    console.log(clampBox(-999, -400, 1200) === -400);
    console.log(clampBox(5000, -400, 1200) === 1200);
    console.log(clampBox(10, -400, 1200) === 10);
    """
    assert run_ts_eval(script).split('\n') == ["true", "true", "true"]

def test_rectOverlap_overlaps():
    script = """
    const a = { minX: 0, maxX: 100, minY: 0, maxY: 40 };
    const b = { minX: 90, maxX: 200, minY: 0, maxY: 40 };
    const r = rectOverlap(a, b, 0);
    console.log(r.axis === "x" && r.amount === 10 && r.sign === -1);
    """
    assert run_ts_eval(script) == "true"

def test_rectOverlap_no_overlap_but_margin():
    script = """
    const a = { minX: 0, maxX: 100, minY: 0, maxY: 40 };
    const b = { minX: 120, maxX: 200, minY: 0, maxY: 40 };
    const r1 = rectOverlap(a, b, 0);
    const r2 = rectOverlap(a, b, 15);
    console.log(r1 === null);
    console.log(r2.axis === "x" && r2.amount === 10);
    """
    assert run_ts_eval(script).split('\n') == ["true", "true"]
