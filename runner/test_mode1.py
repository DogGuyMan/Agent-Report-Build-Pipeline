"""`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON."""
import os
import sys
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
from mode1 import context as X  # noqa: E402
from mode1 import diff as D  # noqa: E402
from mode1 import machine_stage as MC  # noqa: E402
from mode1 import measured as MS  # noqa: E402


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


# ── 2. 형 · 읽기 레코드 자리 · 바닥 ──────────────────────────────────────


def test_읽기_레코드_자리는_자기호스팅만_다르다(tmp_path: Path):
    self_hosted = X.Mode1Context(root=str(tmp_path), model="m", repo=str(tmp_path))
    assert X.READING.locate(self_hosted) == os.path.join(str(tmp_path), "machine", "terms-reading.json")
    other = _ctx(tmp_path)   # root="/r" 는 저장소가 아니다
    assert X.READING.locate(other) == os.path.join(str(tmp_path), "docs", "codegraph", "terms-reading.json")


def test_측정_행은_단계_이름과_토큰_0_을_담는다():
    class T(MS.Measured):
        name = "t"
    r = T().row(time.monotonic(), True, "x")
    assert r["stage"] == "t" and r["ok"] is True and r["why"] == "x" and r["usage"]["total"] == 0


def test_기계_단계는_저장소를_cwd_로_한다(tmp_path: Path):
    class T(MC.Mode1Machine):
        name = "t"

        def argv(self, ctx: X.Mode1Context) -> list[str]:
            return ["true"]
    assert T().cwd(_ctx(tmp_path)) == str(tmp_path)
    assert MC.Mode1Machine.wiki_argv("py", "/root", "prep.py", "/repo") == ["py", "/root/runner/wiki/prep.py", "/repo"]
    assert os.path.isdir(os.path.join(X.ROOT, "runner", "mode1"))   # 도구 뿌리는 셋 위다


# ── 3. changes.json 의 꼴 ────────────────────────────────────────────────


def _verdicts() -> dict[str, list[str]]:
    return {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": ["gone.py"]}


def test_diff_는_넷_갈래와_범위를_담는다(tmp_path: Path):
    p = str(tmp_path / "changes.json")
    D.write_diff(p, _verdicts(), targets=["b.py"], hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None
    assert got["targets"] == ["b.py"] and got["verdicts"]["삭제됨"] == ["gone.py"]


def test_전량이면_targets_가_None_이다(tmp_path: Path):
    p = str(tmp_path / "d.json")
    D.write_diff(p, _verdicts(), targets=None, hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None and got["targets"] is None


def test_diff_검사는_넷_갈래가_다_있어야_통과한다():
    assert D.check_diff({"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}) == []
    assert D.check_diff({"verdicts": {"유효": []}, "targets": None, "hops": 1, "tracked": 0}) != []
    assert X.CHANGES.check is D.check_diff


def test_전체_파일_집합은_삭제됨을_뺀_셋의_합이다():
    d: D.WarmupDiff = {"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}
    assert D.all_files(d) == {"a.py", "b.py"}
