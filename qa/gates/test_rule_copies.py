"""두 mode 에 사본으로 사는 규칙이 같은가 — 용어 찾기 규칙(Mode 1.5 · Mode 2)과 봉인 소스 집합(Mode 1 · 봉인 판정)."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "machine"),
                os.path.join(ROOT, "src", "common")]
import declmap  # noqa: E402
import evidence  # noqa: E402
import manifest  # noqa: E402
from spec.python.viz import check  # noqa: E402
from term.python.runner.term import collect  # noqa: E402


def test_용어_찾기_규칙은_Mode_1_5_와_Mode_2_가_같다() -> None:
    assert [(p.pattern, p.flags) for p in collect.TERM_PATTERNS] == [(p.pattern, p.flags) for p in check.TERM_PATTERNS]


def _repo(tmp: Path) -> str:
    tracked = {"pkg/a.py": "x = 1\n", "pkg/한글.py": "y = 2\n", "pkg/notes.txt": "t\n",
               "node_modules/dep.py": "s\n", "out/gen.py": "s\n"}
    for rel, body in {**tracked, "pkg/old_copy.py": "z = 3\n"}.items():
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-f", *tracked], cwd=tmp, check=True)
    (tmp / "pkg/a.py").write_text("x = 9\n", encoding="utf-8")  # blob_ids 는 스테이징이 아니라 작업 트리를 잰다
    return str(tmp)


def test_봉인_소스_집합은_생산자와_판정이_같다(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    produced = declmap.tracked_files(repo, "py", [])
    judged = evidence.source_files(repo, list(declmap.LANGS["py"]["exts"]), sorted(declmap.SKIP_DIRS))
    assert produced == judged == ["pkg/a.py", "pkg/한글.py"]
    assert manifest.blob_ids(repo, produced) == evidence.blob_ids(repo, judged)
