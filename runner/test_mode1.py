"""`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON."""
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
from mode1 import context as X  # noqa: E402


def _ctx(tmp_path: Path) -> X.Mode1Context:
    return X.Mode1Context(root="/r", model="m", repo=str(tmp_path))


# ── 1. 문맥과 산출물 ────────────────────────────────────────────────────


def test_문맥의_기본값은_전량이_아니다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert c.cold is False and c.targets is None and c.plan is None


def test_산출물은_저장소_아래_자리를_가리킨다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert X.CODEGRAPH.locate(c).endswith(os.path.join("out", "codegraph-raw", "codegraph.json"))
    assert X.CHANGES.locate(c).endswith("changes.json")
    assert X.BATCHES.locate(c).endswith("batches.json")


def test_코드지도_검사는_최상위_열쇠만_본다():
    assert X.check_codegraph({"nodes": [], "edges": []}) == []
    assert X.check_codegraph({"nodes": "x"}) != []
    assert X.check_codegraph([]) != []


def test_층계획_검사는_층과_합계를_본다():
    assert X.check_batches({"target": 8, "layers": [], "totals": {}}) == []
    assert X.check_batches({"layers": {}}) != []
