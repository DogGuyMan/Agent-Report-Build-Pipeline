#!/usr/bin/env python3
"""file_cache.py 시험. 캐시가 **내용 해시로** 무효화되는지가 급소다.

mtime 으로 무효화하면 체크아웃 한 번에 멀쩡한 캐시가 통째로 죽고, 반대로
같은 mtime 으로 내용만 바뀌면 낡은 개요가 조용히 살아남는다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import file_cache as FC  # noqa: E402


def _repo(tmp_path, text="처음 내용\n"):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(text, encoding="utf-8")
    return str(tmp_path)


def test_없으면_None(tmp_path):
    """캐시가 없으면 None 이다 — 부르는 쪽이 통독하라는 뜻이다."""
    assert FC.get(_repo(tmp_path), "src/a.py") is None


def test_넣은_것을_그대로_돌려준다(tmp_path):
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"imports": ["os"], "symbols": []})
    got = FC.get(repo, "src/a.py")
    assert got["path"] == "src/a.py"
    assert got["outline"]["imports"] == ["os"]


def test_내용이_바뀌면_무효(tmp_path):
    """줄이 밀린 개요를 그대로 쓰면 where 가 거짓말을 한다."""
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"symbols": [{"name": "f", "line": 1}]})
    (tmp_path / "src" / "a.py").write_text("바뀐 내용\n", encoding="utf-8")
    assert FC.get(repo, "src/a.py") is None


def test_없는_파일이면_None(tmp_path):
    """지워진 파일에 해시를 낼 수 없다. 터지지 말고 None 이어야 한다."""
    assert FC.get(_repo(tmp_path), "src/없다.py") is None


def test_캐시는_out_아래에_산다(tmp_path):
    """out/ 은 gitignore 다. 재생성 가능한 파생물이 커밋에 섞이면 안 된다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    assert os.path.join("out", "codegraph-raw", "_filecache") in path


def test_파일마다_다른_자리(tmp_path):
    """경로 해시를 키로 쓰므로 두 파일이 서로를 덮지 않는다."""
    repo = _repo(tmp_path)
    (tmp_path / "src" / "b.py").write_text("다른 파일\n", encoding="utf-8")
    FC.put(repo, "src/a.py", {"who": "a"})
    FC.put(repo, "src/b.py", {"who": "b"})
    assert FC.get(repo, "src/a.py")["outline"]["who"] == "a"
    assert FC.get(repo, "src/b.py")["outline"]["who"] == "b"


def test_임시파일을_남기지_않는다(tmp_path):
    """os.replace 로 갈아 끼우므로 .tmp 가 남으면 안 된다 — 남으면 다음 읽기가 반쯤 쓰인 것을 본다."""
    repo = _repo(tmp_path)
    d = os.path.dirname(FC.put(repo, "src/a.py", {}))
    assert [f for f in os.listdir(d) if f.endswith(".tmp")] == []


def test_망가진_캐시는_None(tmp_path):
    """손으로 고쳐 깨졌거나 반쯤 쓰인 파일을 만나도 터지지 않는다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    open(path, "w", encoding="utf-8").write("{ 이건 json 이 아니다")
    assert FC.get(repo, "src/a.py") is None
