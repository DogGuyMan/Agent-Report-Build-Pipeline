"""test_gen_readme.py — README 가 소스와 어긋나지 않는지 본다."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_readme as G  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["machine", "runner", "viz", "tools"]


def test_readme_is_not_stale() -> None:
    """소스를 고치고 생성기를 안 돌리면 여기서 깨진다.

    README 를 손으로 고쳐도 같다. 주석과 달리 이 문서는 썩지 않고 빨개진다.
    """
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_readme.py"),
                        *DIRS, "--repo", ROOT, "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + "\n" + r.stdout


def test_every_directory_has_one() -> None:
    """네 디렉토리 전부 README 를 갖는다."""
    for d in DIRS:
        assert Path(ROOT, d, "README.md").is_file(), d


def test_signature_comes_from_pycalls_not_a_copy(tmp_path: Path) -> None:
    """시그니처는 pycalls.signature_of 하나에서만 온다. 두 곳에서 만들면 어긋난다."""
    src = "def f(a: int, *, b: str = 'x') -> bool:\n    '''한 줄.'''\n    return True\n"
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "m.py").write_text(src, encoding="utf-8")
    body = G.render_dir(str(tmp_path), "d")
    assert "(a: int, *, b: str = 'x') -> bool" in body
    assert "한 줄." in body


def test_pipe_in_signature_is_escaped(tmp_path: Path) -> None:
    """`str | None` 의 파이프가 마크다운 표 칸을 깨뜨리지 않는다."""
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "m.py").write_text(
        "def f(x: str | None) -> int | None:\n    return None\n", encoding="utf-8")
    body = G.render_dir(str(tmp_path), "d")
    assert "str \\| None" in body
    for line in body.splitlines():
        if line.startswith("| `f`"):
            assert line.count("|") - line.count("\\|") == 4   # 표 칸 경계 4개뿐
