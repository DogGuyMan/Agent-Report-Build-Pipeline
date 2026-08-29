"""warmup.py 회귀. 무효화가 틀리면 낡은 요약이 조용히 재사용되므로 경계를 못박는다.

**가짜 경로를 쓰지 않는다.** `tmp_path` 에 진짜 git 저장소와 진짜 파일을 만들어 시험한다 —
이 저장소에서 가짜 경로로 시험 둘이 잘못 통과한 적이 있다.

  python -m pytest codegraph/test_warmup.py -q         # .venv 를 켠 뒤
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warmup as W  # noqa: E402


# ── 시험 재료 만들기 ─────────────────────────────────────────────

def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


def _repo(tmp_path, files):
    """진짜 git 저장소 하나를 만들고 files 를 커밋한다. files: {상대경로: 본문}"""
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

def test_file_hash_is_content_not_commit(tmp_path):
    """커밋 여부와 무관하다 — 바이트 그대로의 sha256 이다."""
    p = tmp_path / "a.py"
    p.write_text(ONE, encoding="utf-8")
    first = W.file_hash(str(p))
    p.write_text(ONE + "# 한 줄 더\n", encoding="utf-8")
    assert W.file_hash(str(p)) != first
    p.write_text(ONE, encoding="utf-8")
    assert W.file_hash(str(p)) == first


def test_file_hash_returns_none_for_missing(tmp_path):
    assert W.file_hash(str(tmp_path / "없다.py")) is None


# ── 2. 판정 네 갈래 ──────────────────────────────────────────────

def test_unchanged_file_is_valid(tmp_path):
    """① 안 바뀐 파일은 유효다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py"])
    W.save(cache, entries)

    판정, _ = W.status(cache, repo, ["a.py"])
    assert 판정["유효"] == ["a.py"]
    assert 판정["재읽기"] == [] and 판정["위치만"] == [] and 판정["삭제됨"] == []


def test_first_run_is_all_reread(tmp_path):
    """매니페스트가 없으면 전부 재읽기다 — 첫 실행의 기준선."""
    repo = _repo(tmp_path, {"a.py": ONE, "b.py": ONE})
    판정, _ = W.status(str(tmp_path / "없다.json"), repo, ["a.py", "b.py"])
    assert 판정["재읽기"] == ["a.py", "b.py"]


def test_uncommitted_change_is_stale(tmp_path):
    """③ 커밋하지 않은 변경도 낡음이다 — 원안(blob SHA)의 결함을 못박는 시험."""
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


def test_missing_file_is_deleted(tmp_path):
    """④ 이번 훑기에 안 보인 항목은 삭제됨이다."""
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

def test_decl_hash_ignores_line_and_doc(tmp_path):
    """줄 번호와 문서 주석이 달라도 선언 목록이 같으면 같은 해시다."""
    a = {"lines": 3, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}
    b = {"lines": 9, "decls": [{"line": 7, "kind": "class", "name": "Alpha", "doc": "설명"}]}
    assert W.decl_hash(a) == W.decl_hash(b)


def test_decl_hash_changes_when_declaration_added():
    a = {"lines": 3, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}
    b = {"lines": 5, "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""},
                               {"line": 4, "kind": "class", "name": "Beta", "doc": ""}]}
    assert W.decl_hash(a) != W.decl_hash(b)


def test_comment_only_change_needs_no_llm(tmp_path):
    """⑤ 선언이 같으면 위치만 — LLM 을 부르지 않는다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    before = {"a.py": {"lines": 3,
                       "decls": [{"line": 1, "kind": "class", "name": "Alpha", "doc": ""}]}}
    _, entries = W.status(cache, repo, ["a.py"], before)
    W.save(cache, entries)

    open(os.path.join(repo, "a.py"), "w", encoding="utf-8").write("# 주석\n" + ONE)
    after = {"a.py": {"lines": 4,
                      "decls": [{"line": 2, "kind": "class", "name": "Alpha", "doc": "주석"}]}}

    판정, _ = W.status(cache, repo, ["a.py"], after)
    assert 판정["위치만"] == ["a.py"]
    assert 판정["재읽기"] == []


def test_declaration_change_forces_reread(tmp_path):
    """② 선언이 달라지면 그 파일만 재읽기다."""
    repo = _repo(tmp_path, {"a.py": ONE, "b.py": ONE})
    cache = str(tmp_path / "warmup.json")
    d = {"line": 1, "kind": "class", "name": "Alpha", "doc": ""}
    before = {"a.py": {"lines": 3, "decls": [d]}, "b.py": {"lines": 3, "decls": [d]}}
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

def test_mtime_gate_skips_hashing(tmp_path, monkeypatch):
    """mtime 과 크기가 같으면 해싱하지 않는다 — stat 이 훨씬 싸다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, entries = W.status(cache, repo, ["a.py"])
    W.save(cache, entries)

    def 부른다(_):
        raise AssertionError("mtime 이 같은데 해싱했다")

    monkeypatch.setattr(W, "file_hash", 부른다)
    판정, _ = W.status(cache, repo, ["a.py"])
    assert 판정["유효"] == ["a.py"]


def test_seen_is_refreshed_every_run(tmp_path):
    """`seen` 은 매 실행마다 갱신된다 — 이번에 봤다는 표시다."""
    repo = _repo(tmp_path, {"a.py": ONE})
    cache = str(tmp_path / "warmup.json")
    _, first = W.status(cache, repo, ["a.py"])
    W.save(cache, first)
    _, second = W.status(cache, repo, ["a.py"])
    assert second["a.py"]["seen"] >= first["a.py"]["seen"]


# ── 5. 저장과 적재 ───────────────────────────────────────────────

def test_load_missing_cache_is_empty(tmp_path):
    assert W.load(str(tmp_path / "없다.json")) == {}


def test_save_then_load_roundtrip(tmp_path):
    cache = str(tmp_path / "깊은/자리/warmup.json")
    entries = {"a.py": {"mtime": 1.0, "size": 3, "seen": 2.0,
                        "file_hash": "x", "decl_hash": "y"}}
    W.save(cache, entries)
    assert W.load(cache) == entries


# ── 6. 파급 — 파일 단위 캐시가 못 잡는 것 ────────────────────────

def test_blast_radius_spreads_both_ways(tmp_path):
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


def test_blast_radius_skips_nodes_without_file(tmp_path):
    """외부 노드는 file 이 null 이다 — 간선에서 빼야 한다."""
    import json
    g = {"nodes": [{"id": "C1", "file": "a.py"}, {"id": "X:(STL) std", "file": None}],
         "edges": [{"from": "C1", "to": "X:(STL) std"}]}
    p = tmp_path / "codegraph.json"
    p.write_text(json.dumps(g), encoding="utf-8")
    assert W.blast_radius(str(p), ["a.py"], hops=1) == ["a.py"]
