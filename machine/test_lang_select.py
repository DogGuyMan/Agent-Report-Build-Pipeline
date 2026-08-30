# <include file="machine/comments.xml" path="//term[@id='test_lang_select.py']"/>
# 언어 판별의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_lang_select.py — 언어 판별의 회귀 시험."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lang_select as L  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select._repo']"/>
# 시험용 임시 git 저장소를 하나 만들어 주는 도우미 함수다.
# 쓰는 것: subprocess.run · 쓰이는 곳: machine.test_lang_select.test_counts_only_git_tracked_files, machine.test_lang_select.test_empty_repo_selects_nothing, machine.test_lang_select.test_no_proposal_falls_back_to_file_counts, machine.test_lang_select.test_proposal_can_override_the_count, machine.test_lang_select.test_proposal_with_no_sources_is_rejected (+3)
def _repo(tmp: Path, files: dict[str, str]) -> str:
    for rel, body in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    return str(tmp)


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_counts_only_git_tracked_files']"/>
# git 이 추적하는 파일만 언어별 소스 수로 세는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.count_sources · 쓰이는 곳: 없음
def test_counts_only_git_tracked_files(tmp_path: Path) -> None:
    """빌드 산출물과 vendored 를 세지 않기 위해 git 이 아는 파일만 센다."""
    r = _repo(tmp_path, {"a.py": "x = 1\n", "b.py": "y = 2\n"})
    (tmp_path / "untracked.py").write_text("z = 3\n", encoding="utf-8")
    assert L.count_sources(r)["py"] == 2


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_no_proposal_falls_back_to_file_counts']"/>
# select 함수가 아무 언어도 제안받지 않았을 때 파일 수로 언어를 고르는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_no_proposal_falls_back_to_file_counts(tmp_path: Path) -> None:
    """제안이 없으면 파일 수가 가장 많은 언어로 간다."""
    r = _repo(tmp_path, {"a.py": "", "b.py": "", "c.ts": ""})
    got = L.select(r)
    assert got["language"] == "py" and got["collector"] == "griffe+pycalls"


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_proposal_can_override_the_count']"/>
# 파일 수로는 소수파인 언어라도, 제안된 언어가 검사를 통과하면 그 언어가 선택되는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_proposal_can_override_the_count(tmp_path: Path) -> None:
    """세는 것으로는 '많은 쪽이 도구이고 주제는 적은 쪽' 을 알 수 없다.

    그게 모형이 문서를 읽는 이유다. 소수파 제안도 검사를 통과하면 따른다.
    """
    r = _repo(tmp_path, {"a.py": "", "b.py": "", "c.cs": ""})
    got = L.select(r, "cs")
    assert got["language"] == "cs"
    assert "파일 수 1위" in got["why"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_proposal_with_no_sources_is_rejected']"/>
# 제안된 언어의 소스 파일이 저장소에 한 개도 없으면 그 제안이 버려지고 파일 수 기준으로 되돌아가는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_proposal_with_no_sources_is_rejected(tmp_path: Path) -> None:
    """그 언어의 소스가 한 개도 없으면 헛소리다. 버리고 파일 수로 간다."""
    r = _repo(tmp_path, {"a.py": ""})
    got = L.select(r, "cpp")
    assert got["language"] == "py"
    assert "한 개도 없다" in got["why"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_proposal_without_a_collector_falls_back']"/>
# 수집기가 없는 언어가 제안되면 실제로 수집 가능한 다른 언어로 물러서는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_proposal_without_a_collector_falls_back(tmp_path: Path) -> None:
    """수집기가 없는 언어(ts)를 고르면 prep 이 막힌다 — 수집 가능한 쪽으로 물러선다.

    지도가 없는 것보다 부분 지도가 낫다.
    """
    r = _repo(tmp_path, {"a.ts": "", "b.ts": "", "c.py": ""})
    got = L.select(r, "ts")
    assert got["language"] == "py" and got["collector"] == "griffe+pycalls"
    assert "수집기가 없다" in got["why"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_unknown_word_is_rejected']"/>
# select 가 모르는 언어 이름이 제안되면 그 제안을 버리는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_unknown_word_is_rejected(tmp_path: Path) -> None:
    """모형이 아는 낱말 밖을 내면 버린다."""
    r = _repo(tmp_path, {"a.py": ""})
    got = L.select(r, "rust")
    assert got["language"] == "py" and "아는 언어가 아니다" in got["why"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_empty_repo_selects_nothing']"/>
# 소스 코드가 하나도 없는 저장소에서는 언어를 아무것도 고르지 않는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.select · 쓰이는 곳: 없음
def test_empty_repo_selects_nothing(tmp_path: Path) -> None:
    """소스가 하나도 없으면 고르지 않는다 — 지어내지 않는다."""
    r = _repo(tmp_path, {"README.md": "# 빈 저장소\n"})
    got = L.select(r)
    assert got["language"] is None and got["collector"] == "none"


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_collector_names_match_prep']"/>
# lang_select 모듈이 내놓는 수집기 이름이 prep 단계가 아는 이름과 똑같은지 확인하는 시험이다.
# 쓰는 것: machine.lang_select.COLLECTOR, machine.lang_select.LANG_EXTS · 쓰이는 곳: 없음
def test_collector_names_match_prep(tmp_path: Path) -> None:
    """여기서 내는 수집기 이름이 prep 이 아는 이름과 같아야 한다.

    어긋나면 prep 이 `collector` 를 못 알아보고 조용히 'none' 으로 떨어진다.
    """
    assert set(L.COLLECTOR.values()) == {"clang-uml", "roslyn-dump", "griffe+pycalls", "none"}
    assert set(L.LANG_EXTS) == set(L.COLLECTOR)


# <include file="machine/comments.xml" path="//term[@id='machine.test_lang_select.test_read_docs_picks_root_documents']"/>
# 저장소 루트에 있는 문서 파일만 읽어오는지 확인하는 시험 함수다.
# 쓰는 것: machine.test_lang_select._repo, machine.lang_select.read_docs · 쓰이는 곳: 없음
def test_read_docs_picks_root_documents(tmp_path: Path) -> None:
    """모형에게는 루트 문서만 준다. 없는 것은 조용히 건너뛴다."""
    r = _repo(tmp_path, {"README.md": "읽기\n", "CLAUDE.md": "규약\n"})
    text = L.read_docs(r)
    assert "README.md" in text and "CLAUDE.md" in text and "읽기" in text
