"""Mode 2 와 Mode 1.5 를 import 하는 것만으로 해석기가 바뀌거나 networkx 가 실리면 안 된다.

자식 프로세스로 재는 이유는 이 시험 프로세스에 이미 networkx 가 실려 있을 수 있어서다.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = """
import sys, os, json
sys.path.insert(0, os.path.join({root!r}, "runner"))
import {mod}
print(json.dumps({{"prefix": sys.prefix, "networkx": "networkx" in sys.modules}}))
"""


def _probe(mod: str) -> dict[str, object]:
    r = subprocess.run([sys.executable, "-c", PROBE.format(root=ROOT, mod=mod)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    out: dict[str, object] = json.loads(r.stdout.strip().split("\n")[-1])
    return out


def test_mode2_는_networkx_를_끌어오지_않는다():
    assert _probe("run_mode2")["networkx"] is False


def test_mode1_5_는_networkx_를_끌어오지_않는다():
    assert _probe("run_mode1_5")["networkx"] is False


def test_mode2_import_는_해석기를_바꾸지_않는다():
    assert _probe("run_mode2")["prefix"] == sys.prefix


def test_mode1_5_import_는_해석기를_바꾸지_않는다():
    assert _probe("run_mode1_5")["prefix"] == sys.prefix
