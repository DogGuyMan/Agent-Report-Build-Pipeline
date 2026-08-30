# <include file="machine/comments.xml" path="//term[@id='test_warmup.py']"/>
# 증분 무효화 판정의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_warmup.py — 증분 무효화 판정의 회귀 시험."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warmup as W  # noqa: E402
from declmap import Decl, FileDecls  # noqa: E402
from warmup import Manifest  # noqa: E402


# ── 시험 재료 만들기 ─────────────────────────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup._git']"/>
# 테스트 안에서 git 명령을 대신 실행해주는 짧은 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_warmup._repo, machine.test_warmup.test_missing_file_is_deleted
def _git(repo: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup._repo']"/>
# 테스트용으로 진짜 git 저장소 하나를 만들어주는 도우미 함수다.
# 쓰는 것: machine.test_warmup._git · 쓰이는 곳: machine.test_warmup.test_comment_only_change_needs_no_llm, machine.test_warmup.test_declaration_change_forces_reread, machine.test_warmup.test_first_run_is_all_reread, machine.test_warmup.test_missing_file_is_deleted, machine.test_warmup.test_mtime_gate_skips_hashing (+3)
def _repo(tmp_path: Path, files: dict[str, str]) -> str:
    """진짜 git 저장소 하나를 만들고 files 를 커밋한다. files: {상대경로: 본문}

    가짜 경로로는 이 판정을 시험할 수 없다 — git 과 파일 시스템을 둘 다 실제로 물어본다.
    """
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    for rel, body in files.items():
        p = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "init")
    return repo


ONE = "class Alpha:\n    def run(self):\n        return 1\n"


# ── 1. 파일 해시 ─────────────────────────────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_file_hash_is_content_not_commit']"/>
# warmup.file_hash 가 커밋 여부가 아니라 파일 내용(바이트)만 보고 해시를 낸다는 것을 확인하는 시험이다.
# 쓰는 것: machine.warmup.file_hash · 쓰이는 곳: 없음
def test_file_hash_is_content_not_commit(tmp_path: Path):
    """커밋 여부와 무관하다 — 바이트 그대로의 sha256 이다."""
    p = tmp_path / "a.py"
    p.write_text(ONE, encoding="utf-8")
    first = W.file_hash(str(p))
    p.write_text(ONE + "# 한 줄 더\n", encoding="utf-8")
    assert W.file_hash(str(p)) != first
    p.write_text(ONE, encoding="utf-8")
    assert W.file_hash(str(p)) == first


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_file_hash_returns_none_for_missing']"/>
# 없는 파일을 해시하려 하면 에러가 나지 않고 None 이 나오는지 확인하는 시험이다.
# 쓰는 것: machine.warmup.file_hash · 쓰이는 곳: 없음
def test_file_hash_returns_none_for_missing(tmp_path: Path):
    """없는 파일이면 터지지 않고 None 이다."""
    assert W.file_hash(str(tmp_path / "없다.py")) is None


# ── 2. 판정 네 갈래 ──────────────────────────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_unchanged_file_is_valid']"/>
# 안 바뀐 파일이 '유효'로 판정되는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_unchanged_file_is_valid(tmp_path: Path):
    """안 바뀐 파일은 유효다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py"])
    W.save(cache, entries)

    판정, _ = W.status(cache, repo, ["a.py"])
    assert 판정["유효"] == ["a.py"]
    assert 판정["재읽기"] == [] and 판정["위치만"] == [] and 판정["삭제됨"] == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_first_run_is_all_reread']"/>
# 캐시 파일이 아예 없을 때, 즉 첫 실행일 때는 모든 파일이 '재읽기'로 판정되는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status · 쓰이는 곳: 없음
def test_first_run_is_all_reread(tmp_path: Path):
    """매니페스트가 없으면 전부 재읽기다 — 첫 실행의 기준선."""
    repo = _repo(tmp_path, {"a.py": ONE, "b.py": ONE})
    판정, _ = W.status(str(tmp_path / "없다.json"), repo, ["a.py", "b.py"])
    assert 판정["재읽기"] == ["a.py", "b.py"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_uncommitted_change_is_stale']"/>
# 커밋하지 않고 작업 트리에서만 파일을 고쳐도 그 변경이 낡음으로 잡히는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_uncommitted_change_is_stale(tmp_path: Path):
    """커밋하지 않은 작업 트리 변경도 낡음이다 — blob SHA 로 판정하면 이것을 놓친다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py"])
    W.save(cache, entries)

    # 커밋하지 않는다. 작업 트리만 고친다 — 개발 중 가장 흔한 상태다.
    open(os.path.join(repo, "a.py"), "w", encoding="utf-8").write(
        ONE + "class Beta:\n    pass\n")

    판정, _ = W.status(cache, repo, ["a.py"])
    assert 판정["유효"] == []
    assert "a.py" in 판정["재읽기"] + 판정["위치만"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_missing_file_is_deleted']"/>
# 이번 훑기 목록에 없는 파일이 '삭제됨'으로 판정되는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save, machine.test_warmup._git · 쓰이는 곳: 없음
def test_missing_file_is_deleted(tmp_path: Path):
    """이번 훑기에 안 보인 항목은 삭제됨이다."""
    repo = _repo(tmp_path, {"a.py": ONE, "b.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py", "b.py"])
    W.save(cache, entries)

    os.remove(os.path.join(repo, "b.py"))
    _git(repo, "rm", "-q", "--cached", "b.py")

    판정, _ = W.status(cache, repo, ["a.py"])       # git 이 더는 b.py 를 모른다
    assert 판정["삭제됨"] == ["b.py"]
    assert 판정["유효"] == ["a.py"]


# ── 3. 두 겹 무효화 — 여기가 값어치의 전부다 ──────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_decl_hash_ignores_line_and_doc']"/>
# 선언 해시(decl_hash)가 줄 번호나 문서 주석이 달라도 선언 이름·종류만 같으면 같은 값을 낸다는 것을 확인하는 시험이다.
# 쓰는 것: machine.warmup.decl_hash · 쓰이는 곳: 없음
def test_decl_hash_ignores_line_and_doc(tmp_path: Path):
    """줄 번호와 문서 주석이 달라도 선언 목록이 같으면 같은 해시다."""
    a: FileDecls = {"lines": 3, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}
    b: FileDecls = {"lines": 9, "decls": [{"line": 7, "kind": "class", "name": "Alpha", "doc": "설명"}]}
    assert W.decl_hash(a) == W.decl_hash(b)


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_decl_hash_changes_when_declaration_added']"/>
# 선언이 하나 늘면 decl_hash 값이 달라진다는 것을 확인하는 시험이다.
# 쓰는 것: machine.warmup.decl_hash · 쓰이는 곳: 없음
def test_decl_hash_changes_when_declaration_added():
    """선언이 하나 늘면 선언 해시가 달라진다."""
    a: FileDecls = {"lines": 3, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}
    b: FileDecls = {"lines": 5, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""},
                                          {"line": 4, "kind": "class", "name": "Beta", "doc": ""}]}
    assert W.decl_hash(a) != W.decl_hash(b)


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_comment_only_change_needs_no_llm']"/>
# 주석만 바뀌고 선언 목록(클래스·함수 이름 등)이 그대로면 '위치만' 판정이 나와서 LLM 을 다시 부를 필요가 없는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_comment_only_change_needs_no_llm(tmp_path: Path):
    """선언이 같으면 위치만 — LLM 을 부르지 않는다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    before: dict[str, FileDecls] = {
        "a.py": {"lines": 3,
                 "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}}
    _, entries = W.status(cache, repo, ["a.py"], before)
    W.save(cache, entries)

    open(os.path.join(repo, "a.py"), "w", encoding="utf-8").write("# 주석\n" + ONE)
    after: dict[str, FileDecls] = {
        "a.py": {"lines": 4,
                 "decls": [{"line": 2, "kind": "class", "name": "Alpha", "doc": "주석"}]}}

    판정, _ = W.status(cache, repo, ["a.py"], after)
    assert 판정["위치만"] == ["a.py"]
    assert 판정["재읽기"] == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_declaration_change_forces_reread']"/>
# 파일 안의 선언(클래스·함수 목록)이 실제로 달라지면 그 파일만 '재읽기'로 판정되고 다른 파일은 영향받지 않는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_declaration_change_forces_reread(tmp_path: Path):
    """선언이 달라지면 그 파일만 재읽기다."""
    repo = _repo(tmp_path, {"a.py": ONE, "b.py": ONE})
    cache = str(tmp_path / "warmup.json")
    d: Decl = {"line": 1, "kind": "class", "name": "Alpha", "doc": ""}
    before: dict[str, FileDecls] = {"a.py": {"lines": 3, "decls": [d]},
                                    "b.py": {"lines": 3, "decls": [d]}}
    _, entries = W.status(cache, repo, ["a.py", "b.py"], before)
    W.save(cache, entries)

    open(os.path.join(repo, "a.py"), "a", encoding="utf-8").write("class Beta:\n    pass\n")
    after = dict(before)
    after["a.py"] = {"lines": 5, "decls": [d, {"line": 4, "kind": "class",
                                               "name": "Beta", "doc": ""}]}

    판정, _ = W.status(cache, repo, ["a.py", "b.py"], after)
    assert 판정["재읽기"] == ["a.py"]
    assert 판정["유효"] == ["b.py"]


# ── 4. mtime 1차 관문 ────────────────────────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_mtime_gate_skips_hashing']"/>
# 파일의 수정 시각과 크기가 이전과 똑같으면 굳이 파일 내용을 해싱하지 않는다는 1차 관문(mtime gate)을 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_mtime_gate_skips_hashing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """mtime 과 크기가 같으면 해싱하지 않는다 — stat 이 훨씬 싸다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py"])
    W.save(cache, entries)

    def 부른다(_: str) -> str | None:
        raise AssertionError("mtime 이 같은데 해싱했다")

    monkeypatch.setattr(W, "file_hash", 부른다)
    판정, _ = W.status(cache, repo, ["a.py"])
    assert 판정["유효"] == ["a.py"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_seen_is_refreshed_every_run']"/>
# 캐시 항목의 'seen'(마지막으로 본 시각/횟수) 값이 실행할 때마다 갱신되는지 확인하는 테스트다.
# 쓰는 것: machine.test_warmup._repo, machine.warmup.status, machine.warmup.save · 쓰이는 곳: 없음
def test_seen_is_refreshed_every_run(tmp_path: Path):
    """`seen` 은 매 실행마다 갱신된다 — 이번에 봤다는 표시다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, first = W.status(cache, repo, ["a.py"])
    W.save(cache, first)
    _, second = W.status(cache, repo, ["a.py"])
    assert second["a.py"]["seen"] >= first["a.py"]["seen"]


# ── 5. 저장과 적재 ───────────────────────────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_load_missing_cache_is_empty']"/>
# 저장된 캐시 파일이 없을 때 load 를 부르면 빈 사전이 나온다는 것을 확인하는 시험이다.
# 쓰는 것: machine.warmup.load · 쓰이는 곳: 없음
def test_load_missing_cache_is_empty(tmp_path: Path):
    """매니페스트가 없으면 빈 사전이다."""
    assert W.load(str(tmp_path / "없다.json")) == {}


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_save_then_load_roundtrip']"/>
# 매니페스트를 저장했다가 다시 읽으면 저장한 그대로 나온다는 것을 확인하는 시험이다. 저장 경로의 중간 디렉터리가 없어도 자동으로 만들어지는지도 함께 본다.
# 쓰는 것: machine.warmup.load, machine.warmup.save · 쓰이는 곳: 없음
def test_save_then_load_roundtrip(tmp_path: Path):
    """없는 중간 디렉토리를 만들어 저장하고 그대로 다시 읽는다."""
    cache = str(tmp_path / "깊은/자리/warmup.json")
    entries: Manifest = {"a.py": {"mtime": 1.0, "size": 3, "seen": 2.0,
                                  "file_hash": "x", "decl_hash": "y"}}
    W.save(cache, entries)
    assert W.load(cache) == entries


# ── 6. 파급 — 파일 단위 캐시가 못 잡는 것 ────────────────────────

# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_blast_radius_spreads_both_ways']"/>
# blast_radius(파급 범위 계산)가 코드 지도의 간선을 양방향으로 타고 퍼진다는 것을 확인하는 시험이다. 즉 B 를 쓰는 A 도, B 가 쓰는 C 도 둘 다 영향권에 든다.
# 쓰는 것: machine.warmup.blast_radius · 쓰이는 곳: 없음
def test_blast_radius_spreads_both_ways(tmp_path: Path):
    """간선을 양방향으로 탄다 — B 가 바뀌면 B 를 쓰는 A 의 서술도 틀려질 수 있다."""
    import json
    g = {"nodes": [{"id": "C1", "file": "a.py"}, {"id": "C2", "file": "b.py"},
                   {"id": "C3", "file": "c.py"}],
         "edges": [{"from": "C1", "to": "C2"}, {"from": "C2", "to": "C3"}]}
    p = tmp_path / "codegraph.json"
    p.write_text(json.dumps(g), encoding="utf-8")
    assert W.blast_radius(str(p), ["b.py"], hops=1) == ["a.py", "b.py", "c.py"]
    assert W.blast_radius(str(p), ["a.py"], hops=1) == ["a.py", "b.py"]
    assert W.blast_radius(str(p), ["a.py"], hops=2) == ["a.py", "b.py", "c.py"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_warmup.test_blast_radius_skips_nodes_without_file']"/>
# blast_radius 가 file 속성이 없는(외부 라이브러리 같은) 노드는 파급 대상에서 제외한다는 것을 확인하는 시험이다.
# 쓰는 것: machine.warmup.blast_radius · 쓰이는 곳: 없음
def test_blast_radius_skips_nodes_without_file(tmp_path: Path):
    """외부 노드는 file 이 null 이다 — 간선에서 빼야 한다."""
    import json
    g = {"nodes": [{"id": "C1", "file": "a.py"}, {"id": "X:(STL) std", "file": None}],
         "edges": [{"from": "C1", "to": "X:(STL) std"}]}
    p = tmp_path / "codegraph.json"
    p.write_text(json.dumps(g), encoding="utf-8")
    assert W.blast_radius(str(p), ["a.py"], hops=1) == ["a.py"]
