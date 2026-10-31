"""test_evidence.py — 봉인 판정(`evidence.py`)의 구조 문제 · 낡음 · 한 줄 상태 시험."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evidence as E  # noqa: E402

RECORD: dict[str, object] = {"kind": "function", "module": "pkg", "where": "pkg/a.py:1", "means": "하나를 돌려준다.",
          "uses": [], "neighbors": [], "source": "reading"}
SKIP = (".git", "__pycache__", "node_modules", "out")


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def read_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, doc: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f)


def append(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def sha(path: str) -> str:
    """판정 쪽 함수를 쓰지 않고 잰 sha256 — 준비가 판정과 같은 구멍을 갖지 않게."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def blob(repo: str, rel: str) -> str:
    """판정 쪽 함수를 쓰지 않고 `git hash-object` 로 잰 blob id."""
    return subprocess.run(["git", "-C", repo, "hash-object", "--", rel],
                          capture_output=True, text=True, check=True).stdout.strip()


def sealed(tmp_path: Path, kinds: tuple[str, ...] = ("terms-db", "wiki"), files: dict[str, str] | None = None,
           exts: tuple[str, ...] = (".py",), skip: tuple[str, ...] = SKIP,
           inputs: tuple[str, ...] = ("pkg/a.py",)) -> str:
    """봉인까지 커밋한 대상 저장소. 매니페스트는 손으로 적은 기대값이다 — `inputs` 에 적은 파일만 소스다."""
    r = tmp_path / "대상"
    for rel, text in {"pkg/a.py": "def f():\n    return 1\n", **(files or {})}.items():
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(text, encoding="utf-8")
    (r / "docs" / "wiki").mkdir(parents=True)
    (r / "docs" / "wiki" / "index.md").write_text("# 위키\n", encoding="utf-8")
    pub = r / "docs" / "codegraph"
    pub.mkdir(parents=True)
    (pub / "terms-db.json").write_text(json.dumps({"f": RECORD}, ensure_ascii=False), encoding="utf-8")
    repo = str(r)
    git(repo, "init", "-q")
    git(repo, "add", "-A")                              # 소스 집합은 추적 파일이다 — 봉인 전에 추적시킨다
    arts: dict[str, list[dict[str, str]]] = {}
    if "terms-db" in kinds:
        arts["terms-db"] = [{"path": "docs/codegraph/terms-db.json", "sha256": sha(str(pub / "terms-db.json"))}]
    if "wiki" in kinds:
        arts["wiki"] = [{"path": "docs/wiki/index.md", "sha256": sha(str(r / "docs" / "wiki" / "index.md"))}]
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "abc", "source_commit": "def",
           "source_exts": list(exts), "skip_dirs": list(skip), "artifacts": arts,
           "inputs": {rel: blob(repo, rel) for rel in inputs}}
    (pub / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")                 # 봉인까지 커밋된 상태가 기본이다
    return repo


def test_봉인이_맞으면_문제도_낡음도_없다(tmp_path: Path):
    repo = sealed(tmp_path)
    assert E.problems(repo, ["terms-db", "wiki"]) == []
    assert E.staleness(repo) == []


def test_봉인이_없으면_문제다(tmp_path: Path):
    repo = sealed(tmp_path)
    os.remove(os.path.join(repo, E.MANIFEST))
    assert "manifest.json 이 없다" in E.problems(repo, ["terms-db"])[0]


def test_계약_판이_다르면_문제다(tmp_path: Path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.MANIFEST)
    doc = read_json(p)
    doc["version"] = 2
    write_json(p, doc)
    assert "계약이 다르다" in E.problems(repo, ["terms-db"])[0]


def test_필요한_종류가_봉인에_없으면_문제다(tmp_path: Path):
    repo = sealed(tmp_path, kinds=("terms-db",))
    assert E.problems(repo, ["terms-db"]) == []
    assert any("wiki 가 없다" in p for p in E.problems(repo, ["wiki"]))


def test_봉인_뒤_산출물을_고치거나_장을_더하면_문제다(tmp_path: Path):
    repo = sealed(tmp_path)
    append(os.path.join(repo, "docs", "wiki", "index.md"), "손으로 더함\n")
    append(os.path.join(repo, "docs", "wiki", "new.md"), "# 새 장\n")
    got = "\n".join(E.problems(repo, ["wiki"]))
    assert "봉인 뒤 바뀌었다 — docs/wiki/index.md" in got and "봉인 뒤 생긴 장 — docs/wiki/new.md" in got


def test_소스가_움직이면_낡음이지_문제가_아니다(tmp_path: Path):
    repo = sealed(tmp_path)
    append(os.path.join(repo, "pkg", "a.py"), "# 바꿈\n")
    append(os.path.join(repo, "pkg", "b.py"), "y = 2\n")
    git(repo, "add", "pkg/b.py")                        # 소스 집합은 추적 파일이다
    assert E.problems(repo, ["terms-db"]) == []
    got = "\n".join(E.staleness(repo))
    assert "바뀜 pkg/a.py" in got and "생김 pkg/b.py" in got


def test_미추적_파일은_낡음에_넣지_않는다(tmp_path: Path):
    repo = sealed(tmp_path)
    append(os.path.join(repo, "pkg", "c.py"), "z = 3\n")
    assert E.staleness(repo) == []


def test_추적되는데_지운_파일은_사라짐이다(tmp_path: Path):
    repo = sealed(tmp_path)
    os.remove(os.path.join(repo, "pkg", "a.py"))       # 지우고 아직 커밋하지 않았다 — git 은 여전히 추적한다
    assert E.staleness(repo) == ["사라짐 pkg/a.py"]


def test_hash_object_가_실패한_파일은_읽기실패다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = sealed(tmp_path)
    append(os.path.join(repo, "pkg", "b.py"), "y = 2\n")
    git(repo, "add", "pkg/b.py")
    real = E.git

    def flaky(where: str, *args: str) -> str:
        if args[0] == "hash-object" and "pkg/a.py" in args:
            raise subprocess.CalledProcessError(128, ["git", *args])
        return real(where, *args)

    monkeypatch.setattr(E, "git", flaky)
    assert E.staleness(repo) == ["생김 pkg/b.py", "읽기실패 pkg/a.py"]


def test_원고_커밋은_낡음이_아니다(tmp_path: Path):
    repo = sealed(tmp_path)
    os.makedirs(os.path.join(repo, "specs", "x"))
    append(os.path.join(repo, "specs", "x", "data.ts"), "export {};\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "원고")
    assert E.staleness(repo) == []


def test_terms_db_가_계약_꼴이_아니면_문제다(tmp_path: Path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.TERMS_DB)
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps({"f": {"kind": "function"}}))
    m = os.path.join(repo, E.MANIFEST)
    doc = read_json(m)
    doc["artifacts"]["terms-db"][0]["sha256"] = sha(p)
    write_json(m, doc)
    assert any("terms-db.json 이 계약 꼴이 아니다" in x for x in E.problems(repo, ["terms-db"]))


def test_main_은_낡음을_경고로만_찍고_목록에_싣는다(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    repo = sealed(tmp_path)
    append(os.path.join(repo, "pkg", "a.py"), "# 바꿈\n")
    assert E.main([repo, "--need", "wiki", "--list"]) == 0
    out = capsys.readouterr()
    got = json.loads(out.out)
    assert got["artifacts"] == [os.path.join(repo, "docs", "wiki", "index.md")]
    assert got["stale"] == ["바뀜 pkg/a.py"]
    assert "경고" in out.err


def test_main_은_구조_문제면_1_과_사람이_칠_명령을_낸다(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    repo = sealed(tmp_path, kinds=("terms-db",))
    assert E.main([repo, "--need", "terms-db,wiki"]) == 1
    assert "run_mode1.py" in capsys.readouterr().err


def test_미커밋_봉인은_경고다(tmp_path: Path):
    repo = sealed(tmp_path)
    append(os.path.join(repo, E.MANIFEST), "\n")       # 작업 트리에서만 바뀜 — 커밋 전 상태
    m, _ = E.load_manifest(repo)
    assert m is not None and E.problems(repo, ["terms-db"]) == []
    assert any("커밋되지 않았다" in w for w in E.warnings(repo, m))
    assert "미커밋" in E.status_line(repo, ["terms-db"])


def test_뒤_실행_실패_표식은_경고다(tmp_path: Path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.MANIFEST)
    doc = read_json(p)
    doc["superseded_by"] = {"stage": "write-wiki", "at": "2026-10-24T00:00:00+00:00", "producer_commit": "abc"}
    write_json(p, doc)
    git(repo, "commit", "-qam", "표식")
    assert E.problems(repo, ["terms-db"]) == []
    assert "뒤 실행 실패" in E.status_line(repo, ["terms-db"])


def test_status_는_있음_깨짐_없음을_한_줄로_내고_늘_0이다(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    repo = sealed(tmp_path)
    assert E.status_line(repo, ["terms-db", "wiki"]) == "Mode 1 봉인 — 있음"
    append(os.path.join(repo, "docs", "wiki", "index.md"), "x\n")
    assert E.status_line(repo, ["wiki"]).startswith("Mode 1 봉인 — 깨짐: 봉인 뒤 바뀌었다")
    os.remove(os.path.join(repo, E.MANIFEST))
    assert E.main([repo, "--need", "terms-db", "--status"]) == 0
    assert capsys.readouterr().out.strip() == "Mode 1 봉인 — 없음"


def test_status_는_꼴이_깨진_봉인을_없음이_아니라_깨짐으로_낸다(tmp_path: Path):
    repo = sealed(tmp_path)
    with open(os.path.join(repo, E.MANIFEST), "w", encoding="utf-8") as f:
        f.write("{broken")
    assert E.status_line(repo, ["terms-db"]).startswith("Mode 1 봉인 — 깨짐: manifest.json 이 계약 꼴이 아니다")


def test_status_는_git_밖이어도_한_줄을_내고_0이다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]):
    repo = sealed(tmp_path)
    shutil.rmtree(os.path.join(repo, ".git"))           # 봉인은 그대로 두고 git 저장소만 없앤다
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))     # 위쪽 저장소를 찾아 올라가지 않게
    assert E.main([repo, "--need", "terms-db", "--status"]) == 0
    out = capsys.readouterr()
    assert out.out.count("\n") == 1 and out.out.startswith("Mode 1 봉인 — 있음") and "미커밋" in out.out
    assert out.err == ""


# ── 부분 봉인 — `--optional`
@pytest.mark.parametrize("kind", ["terms-db", "wiki"])
def test_부분_봉인은_optional_이면_있는_종류만_판정한다(tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str):
    repo = sealed(tmp_path, kinds=(kind,))
    other = "wiki" if kind == "terms-db" else "terms-db"
    assert any("%s 가 없다" % other in p for p in E.problems(repo, ["terms-db", "wiki"]))
    assert E.problems(repo, ["terms-db", "wiki"], optional=True) == []
    assert E.status_line(repo, ["terms-db", "wiki"], optional=True) == "Mode 1 봉인 — 있음(%s 만)" % kind
    assert E.status_line(repo, ["terms-db", "wiki"]).startswith("Mode 1 봉인 — 깨짐: 봉인에 %s 가 없다" % other)
    assert E.main([repo, "--need", "terms-db,wiki", "--optional", "--list"]) == 0
    path = "docs/codegraph/terms-db.json" if kind == "terms-db" else "docs/wiki/index.md"
    assert json.loads(capsys.readouterr().out)["artifacts"] == [os.path.join(repo, path)]


def test_optional_이라도_봉인에_아무_종류도_없으면_문제다(tmp_path: Path):
    repo = sealed(tmp_path, kinds=())
    got = "\n".join(E.problems(repo, ["terms-db", "wiki"], optional=True))
    assert "terms-db 가 없다" in got and "wiki 가 없다" in got


# ── 소스 집합은 매니페스트의 규칙 그대로다
def test_건너뛸_폴더_안의_추적_파일은_소스가_아니다(tmp_path: Path):
    """경로 중간의 폴더 성분과 파일 이름 성분 둘 다 `skip_dirs` 에 걸린다."""
    repo = sealed(tmp_path, files={"pkg/build/x.py": "x = 1\n", "pkg/skipme.py": "s = 1\n"},
                  skip=(".git", "build", "skipme.py"))
    assert E.staleness(repo) == []


def test_매니페스트의_source_exts_를_그대로_따른다(tmp_path: Path):
    repo = sealed(tmp_path, files={"src/a.ts": "export const a = 1;\n", "pkg/notes.txt": "메모\n"},
                  exts=(".ts",), inputs=("src/a.ts",))
    assert E.staleness(repo) == []
    append(os.path.join(repo, "pkg", "a.py"), "# 바꿈 — .ts 저장소에서는 소스가 아니다\n")
    append(os.path.join(repo, "src", "a.ts"), "export const b = 2;\n")
    assert E.staleness(repo) == ["바뀜 src/a.ts"]


def test_비ASCII_이름의_소스도_소스_집합에_든다(tmp_path: Path):
    repo = sealed(tmp_path, files={"pkg/한글.py": "h = 1\n"}, inputs=("pkg/a.py", "pkg/한글.py"))
    git(repo, "config", "core.quotePath", "true")       # 기계 설정과 무관하게 따옴표가 붙는 기본값으로
    assert "pkg/한글.py" in E.source_files(repo, [".py"], list(SKIP))
    assert E.staleness(repo) == []
    append(os.path.join(repo, "pkg", "한글.py"), "# 바꿈\n")
    assert E.staleness(repo) == ["바뀜 pkg/한글.py"]


# ── 산출물
def test_봉인된_terms_db_의_내용만_고쳐도_문제다(tmp_path: Path):
    """계약 꼴은 지키고 뜻만 바꾼 용어 사전 — 해시가 잡는다."""
    repo = sealed(tmp_path)
    changed = dict(RECORD, means="둘을 돌려준다.")
    write_json(os.path.join(repo, E.TERMS_DB), {"f": changed})
    assert "봉인 뒤 바뀌었다 — docs/codegraph/terms-db.json" in E.problems(repo, ["terms-db"])


def test_봉인_항목_경로가_종류와_맞지_않으면_문제다(tmp_path: Path):
    repo = sealed(tmp_path)
    m = os.path.join(repo, E.MANIFEST)
    doc = read_json(m)
    page = os.path.join(repo, "docs", "wiki", "index.md")
    doc["artifacts"]["terms-db"] = [{"path": "docs/wiki/index.md", "sha256": sha(page)}]
    write_json(m, doc)
    assert any("봉인 항목 경로가 종류와 맞지 않는다 — terms-db: docs/wiki/index.md" in p
               for p in E.problems(repo, ["terms-db"]))
    assert not E.entry_fits("wiki", "docs/wiki/../x.md") and not E.entry_fits("wiki", "docs/wiki/sub/x.md")
    assert not E.entry_fits("wiki", "/docs/wiki/x.md") and E.entry_fits("wiki", "docs/wiki/x.md")


# ── 미커밋 — 매니페스트와 거기 적힌 산출물 전부
def test_위키_장만_커밋되지_않아도_미커밋이다(tmp_path: Path):
    repo = sealed(tmp_path)
    git(repo, "rm", "-q", "--cached", "docs/wiki/index.md")
    git(repo, "commit", "-qm", "위키 장을 추적에서 뺀다")
    assert E.problems(repo, ["terms-db", "wiki"]) == []
    assert "미커밋" in E.status_line(repo, ["terms-db", "wiki"])


def test_gitignore_로_무시된_봉인은_미커밋이다(tmp_path: Path):
    repo = sealed(tmp_path)
    with open(os.path.join(repo, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("docs/codegraph/\n")
    git(repo, "rm", "-q", "-r", "--cached", "docs/codegraph")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "봉인 폴더를 무시한다")
    assert E.problems(repo, ["terms-db", "wiki"]) == []
    assert "미커밋" in E.status_line(repo, ["terms-db", "wiki"])
