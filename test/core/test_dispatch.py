import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from core.dispatch import resolve_script  # noqa: E402

def test_resolveScript_maps_registered_command_to_path():
    table = {"init": "src/spec/python/viz/init.py", "build": "viz/build.mjs"}
    assert resolve_script(table, "init") == "src/spec/python/viz/init.py"

def test_resolveScript_returns_none_for_unknown():
    table = {"init": "src/spec/python/viz/init.py"}
    assert resolve_script(table, "nope") is None

def test_resolveScript_returns_none_for_empty():
    table = {"init": "x"}
    assert resolve_script(table, None) is None
    assert resolve_script(table, "") is None

def test_resolveScript_no_prototype_pollution():
    # In Python dicts, strings like "__class__" or "toString" are just normal keys unless defined
    table = {"init": "x"}
    assert resolve_script(table, "__class__") is None
    assert resolve_script(table, "update") is None
