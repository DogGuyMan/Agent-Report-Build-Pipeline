#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='test_file_cache.py']"/>
# 파일 캐시의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_file_cache.py — 파일 캐시의 회귀 시험."""
import os
import sys
from pathlib import Path
from typing import cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import file_cache as FC  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache._repo']"/>
# 시험용으로 쓸 가짜 저장소 폴더를 임시 디렉토리 안에 만들어주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_file_cache.test_내용이_바뀌면_무효, machine.test_file_cache.test_넣은_것을_그대로_돌려준다, machine.test_file_cache.test_망가진_캐시는_None, machine.test_file_cache.test_없는_파일이면_None, machine.test_file_cache.test_없으면_None (+3)
def _repo(tmp_path: Path, text: str = "처음 내용\n") -> str:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(text, encoding="utf-8")
    return str(tmp_path)


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache._outline']"/>
# FC.get 이 돌려준 캐시 한 건에서 개요(outline) 부분만 꺼내는 도우미 함수다.
# 쓰는 것: typing.cast · 쓰이는 곳: machine.test_file_cache.test_넣은_것을_그대로_돌려준다, machine.test_file_cache.test_파일마다_다른_자리
def _outline(got: dict[str, object] | None) -> dict[str, object]:
    """캐시 한 건에서 개요만 꺼낸다. json 에서 온 사전이라 값이 `object` 다 — 한 번 좁힌다."""
    assert got is not None
    return cast(dict[str, object], got["outline"])


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_없으면_None']"/>
# 파일 캐시에 아무것도 넣지 않았을 때 조회가 어떻게 되는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_없으면_None(tmp_path: Path):
    """캐시가 없으면 None 이다 — 부르는 쪽이 통독하라는 뜻이다."""
    assert FC.get(_repo(tmp_path), "src/a.py") is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_넣은_것을_그대로_돌려준다']"/>
# 캐시에 저장한 개요를 다시 꺼내면 저장한 그대로 나오는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.file_cache.put, machine.test_file_cache._repo, machine.test_file_cache._outline · 쓰이는 곳: 없음
def test_넣은_것을_그대로_돌려준다(tmp_path: Path):
    """넣은 개요가 경로와 함께 그대로 돌아온다."""
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"imports": ["os"], "symbols": []})
    got = FC.get(repo, "src/a.py")
    assert got is not None
    assert got["path"] == "src/a.py"
    assert _outline(got)["imports"] == ["os"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_내용이_바뀌면_무효']"/>
# 캐시를 만든 뒤 원본 파일 내용을 바꾸면 그 캐시가 더 이상 쓰이지 않는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.file_cache.put, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_내용이_바뀌면_무효(tmp_path: Path):
    """줄이 밀린 개요를 그대로 쓰면 where 가 거짓말을 한다."""
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"symbols": [{"name": "f", "line": 1}]})
    (tmp_path / "src" / "a.py").write_text("바뀐 내용\n", encoding="utf-8")
    assert FC.get(repo, "src/a.py") is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_없는_파일이면_None']"/>
# 저장소에 존재하지 않는 파일 경로로 캐시를 조회했을 때 터지지 않고 None 이 오는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_없는_파일이면_None(tmp_path: Path):
    """지워진 파일에 해시를 낼 수 없다. 터지지 말고 None 이어야 한다."""
    assert FC.get(_repo(tmp_path), "src/없다.py") is None


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_캐시는_out_아래에_산다']"/>
# 캐시 파일이 저장되는 경로가 out/codegraph-raw/_filecache 아래인지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.put, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_캐시는_out_아래에_산다(tmp_path: Path):
    """out/ 은 gitignore 다. 재생성 가능한 파생물이 커밋에 섞이면 안 된다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    assert os.path.join("out", "codegraph-raw", "_filecache") in path


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_파일마다_다른_자리']"/>
# 서로 다른 두 파일의 캐시가 같은 자리에 저장되어 서로를 덮어쓰지 않는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.file_cache.put, machine.test_file_cache._repo, machine.test_file_cache._outline · 쓰이는 곳: 없음
def test_파일마다_다른_자리(tmp_path: Path):
    """경로 해시를 키로 쓰므로 두 파일이 서로를 덮지 않는다."""
    repo = _repo(tmp_path)
    (tmp_path / "src" / "b.py").write_text("다른 파일\n", encoding="utf-8")
    FC.put(repo, "src/a.py", {"who": "a"})
    FC.put(repo, "src/b.py", {"who": "b"})
    assert _outline(FC.get(repo, "src/a.py"))["who"] == "a"
    assert _outline(FC.get(repo, "src/b.py"))["who"] == "b"


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_임시파일을_남기지_않는다']"/>
# 캐시를 저장한 뒤 .tmp 로 끝나는 임시 파일이 디렉터리에 남지 않는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.put, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_임시파일을_남기지_않는다(tmp_path: Path):
    """os.replace 로 갈아 끼우므로 .tmp 가 남으면 안 된다 — 남으면 다음 읽기가 반쯤 쓰인 것을 본다."""
    repo = _repo(tmp_path)
    d = os.path.dirname(FC.put(repo, "src/a.py", {}))
    assert [f for f in os.listdir(d) if f.endswith(".tmp")] == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_file_cache.test_망가진_캐시는_None']"/>
# 캐시 파일 내용이 올바른 JSON 이 아니게 손상됐을 때 조회가 터지지 않고 None 이 오는지 확인하는 시험 함수다.
# 쓰는 것: machine.file_cache.get, machine.file_cache.put, machine.test_file_cache._repo · 쓰이는 곳: 없음
def test_망가진_캐시는_None(tmp_path: Path):
    """손으로 고쳐 깨졌거나 반쯤 쓰인 파일을 만나도 터지지 않는다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    open(path, "w", encoding="utf-8").write("{ 이건 json 이 아니다")
    assert FC.get(repo, "src/a.py") is None
