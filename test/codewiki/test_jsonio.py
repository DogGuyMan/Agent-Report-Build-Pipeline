"""jsonio — 원자적 JSON 쓰기."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/codewiki/python/machine"))
import jsonio  # noqa: E402


def test_같은_입력은_같은_바이트고_임시_파일이_남지_않는다(tmp_path: Path) -> None:
    p = tmp_path / "a.json"
    jsonio.write_json_atomic(str(p), {"b": 1, "a": [1, 2]}, indent=1, trailing_newline=True)
    first = p.read_bytes()
    jsonio.write_json_atomic(str(p), {"b": 1, "a": [1, 2]}, indent=1, trailing_newline=True)
    assert p.read_bytes() == first and first.endswith(b"\n")
    assert os.listdir(tmp_path) == ["a.json"]


def test_바꿔_끼우기가_실패하면_옛_파일이_그대로_남는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "a.json"
    p.write_text("old", encoding="utf-8")

    def boom(src: str, dst: str) -> None:
        raise OSError("disk")
    monkeypatch.setattr(jsonio.os, "replace", boom)
    with pytest.raises(OSError):
        jsonio.write_json_atomic(str(p), {"new": True})
    assert p.read_text(encoding="utf-8") == "old" and os.listdir(tmp_path) == ["a.json"]


def test_sort_keys_면_안쪽_사전까지_열쇠를_정렬해_쓴다(tmp_path: Path) -> None:
    p = tmp_path / "a.json"
    doc = {"나": 1, "가": {"z": 1, "a": 2}}
    jsonio.write_json_atomic(str(p), doc, indent=1, sort_keys=True)
    assert p.read_text(encoding="utf-8") == json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True)
