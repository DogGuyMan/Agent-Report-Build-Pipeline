"""계약에서 낸 소비자 형이 계약과 같은지, 모르는 꼴을 거부하는지, 형의 스키마가 계약으로 돌아오는지 본다."""
import hashlib
import importlib
import json
import os
import subprocess
import sys
from typing import cast

import msgspec

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "machine")]
import gen_contract_types as G  # noqa: E402

CONTRACT = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")


def strip_names(node: object) -> object:
    """생산자 `tools/gen_contract.py` 와 같은 규칙 — 칸 이름은 남기고 스키마의 title · description 만 뗀다."""
    if isinstance(node, list):
        return [strip_names(v) for v in cast(list[object], node)]
    if not isinstance(node, dict):
        return node
    out: dict[str, object] = {}
    for k, v in cast(dict[str, object], node).items():
        if k in ("title", "description"):
            continue
        out[k] = ({n: strip_names(s) for n, s in cast(dict[str, object], v).items()}
                  if k in ("properties", "$defs") and isinstance(v, dict) else strip_names(v))
    return out


def test_py_type_은_계약이_쓰는_꼴을_옮긴다():
    assert G.py_type({"anyOf": [{"type": "string"}, {"type": "null"}]}) == "str | None"
    assert G.py_type({"type": "array", "items": {"$ref": "#/$defs/DbUse"}}) == "list[DbUse]"
    assert G.py_type({"type": "object", "additionalProperties": {"type": "string"}}) == "dict[str, str]"


def test_py_type_은_모르는_꼴을_거부한다():
    try:
        G.py_type({"type": "number"})
    except ValueError:
        return
    raise AssertionError("number 를 받아들였다")


def test_생성물이_계약과_같고_형의_스키마가_계약으로_돌아온다():
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen_contract_types.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    T = importlib.import_module("contract_types")
    with open(CONTRACT, encoding="utf-8") as f:
        doc = cast(dict[str, object], json.load(f))
    schemas = cast(dict[str, object], doc["schemas"])
    for fname, tname in cast(dict[str, str], doc["types"]).items():
        assert strip_names(msgspec.json.schema(cast(type, getattr(T, tname)))) == schemas[fname], fname


def test_계약_리소스가_지문과_같다():
    with open(CONTRACT, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with open(CONTRACT[:-len(".json")] + ".sha256", encoding="utf-8") as f:
        assert f.read().split()[0] == digest
