"""`source_inventory.py` — 추적 파일을 언어별로 세고 파일마다 수집 상태를 적는다."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "machine")]
import lang_select as LS  # noqa: E402
import source_inventory as SI  # noqa: E402


def _git_repo(tmp_path: Path) -> Path:
    """`a.py` · `b.ts` · `c.cs` · `d.txt` 를 추적하는 저장소."""
    for name in ("a.py", "b.ts", "c.cs", "d.txt"):
        (tmp_path / name).write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_언어별로_세고_고른_언어의_파일만_수집된다(tmp_path: Path) -> None:
    inv = SI.build_inventory(str(_git_repo(tmp_path)), "py", {})
    assert inv["selected"] == "py"
    assert {lang: row["files"] for lang, row in inv["languages"].items()} == {"cs": 1, "py": 1, "ts": 1}
    assert [lang for lang, row in inv["languages"].items() if row["collected"]] == ["py"]
    assert inv["languages"]["ts"]["collector"] == "none"
    assert inv["files"]["a.py"] == {"language": "py", "status": "collected"}
    assert inv["files"]["b.ts"] == {"language": "ts", "status": "unsupported", "reason": "collector none"}
    assert "d.txt" not in inv["files"]


def test_제외_사유가_있는_파일은_제외로_적고_언어_수에는_든다(tmp_path: Path) -> None:
    inv = SI.build_inventory(str(_git_repo(tmp_path)), "py", {"a.py": "prep.pyRoots skip"})
    assert inv["files"]["a.py"] == {"language": "py", "status": "excluded", "reason": "prep.pyRoots skip"}
    assert inv["languages"]["py"]["files"] == 1


def test_고른_언어가_없으면_어느_것도_수집되지_않는다(tmp_path: Path) -> None:
    inv = SI.build_inventory(str(_git_repo(tmp_path)), None, {})
    assert not any(row["collected"] for row in inv["languages"].values())
    assert {e["status"] for e in inv["files"].values()} == {"unsupported"}


def test_인용되지_않은_수집_파일만_no_symbols_가_된다(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "e.py").write_text("y\n", encoding="utf-8")
    subprocess.run(["git", "add", "e.py"], cwd=repo, check=True)
    inv = SI.build_inventory(str(repo), "py", {})
    SI.mark_no_symbols(inv, {"a.py"})
    assert inv["files"]["a.py"]["status"] == "collected"
    assert inv["files"]["e.py"]["status"] == "no-symbols"
    assert inv["files"]["b.ts"]["status"] == "unsupported"


def test_git_저장소가_아니면_추적_파일이_없다(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x\n", encoding="utf-8")
    assert SI.tracked_files(str(tmp_path)) == []


def test_수집기_이름이_맡는_언어를_낸다() -> None:
    assert SI.language_for("griffe+pycalls") == "py"
    assert SI.language_for("clang-uml") == "cpp"
    assert SI.language_for("roslyn-dump") == "cs"
    assert SI.language_for("none") is None and SI.language_for(None) is None


def test_이_저장소의_언어별_파일_수는_추적_파일을_따로_센_것과_같다() -> None:
    inv = SI.build_inventory(ROOT, "py", {})
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    want = {lang: sum(1 for p in listed.split(b"\0") if p.endswith(tuple(e.encode() for e in exts)))
            for lang, exts in LS.LANG_EXTS.items()}
    assert {"cs", "py", "ts"} <= set(inv["languages"])
    assert {lang: row["files"] for lang, row in inv["languages"].items()} == {lang: n for lang, n in want.items() if n}
    assert len(inv["files"]) == sum(want.values())
