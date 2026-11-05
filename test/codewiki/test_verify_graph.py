"""`verify_graph.py` 의 네 층 — 읽기 · 꼴 · 정합 · 근거 — 와 결과 파일."""
import hashlib
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "machine")]
import verify_graph as V  # noqa: E402

Obj = dict[str, object]
EXT: Obj = {"id": "X:std", "name": "(표준) stdlib", "kind": "external", "module": "__external__",
            "file": None, "line": None}


def _codes(faults: list[V.Fault]) -> list[str]:
    return [f["code"] for f in faults]


def test_표는_네_층_스물한_코드다() -> None:
    assert len(V.LAYER) == 21
    assert sorted(set(V.LAYER.values())) == ["V0 읽기", "V1 꼴", "V2 정합", "V3 근거"]
    with pytest.raises(KeyError):
        V.fault("없는-코드", "$", "")


def test_V0_없는_파일과_깨진_JSON_을_결함으로_낸다(tmp_path: Path) -> None:
    doc, _, faults = V.read_graph(str(tmp_path / "없음.json"))
    assert doc is None and _codes(faults) == ["unreadable"]
    p = tmp_path / "codegraph.json"
    p.write_text('{"nodes": [', encoding="utf-8")
    doc, sha, faults = V.read_graph(str(p))
    assert doc is None and _codes(faults) == ["unreadable"] and "1줄" in faults[0]["detail"]
    assert sha == hashlib.sha256(p.read_bytes()).hexdigest()
