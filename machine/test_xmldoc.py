"""test_xmldoc.py — 주석 블록 주입기의 회귀 시험."""
import json
import os
import sys
from pathlib import Path
from typing import cast

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xmldoc as X  # noqa: E402
from xmldoc import Terms  # noqa: E402


def marker(tid: str, prefix: str = "#") -> str:
    return f"{prefix} <include file=\"{X.XML_REL}\" path=\"//term[@id='{tid}']\"/>"


# ⚠ 아래 픽스처들이 `cast(Terms, …)` 를 쓰는 이유. 각 시험이 보는 자리(`means` ·
#   `uses[].to` · `where`)만 적고 나머지는 일부러 비운다. 채워 넣으면 흐려진다.


def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, terms: Terms) -> None:
    """tmp_path 를 저장소 뿌리로 삼는다. 상수 세 개만 갈아 끼우면 된다."""
    monkeypatch.setattr(X, "ROOT", str(tmp_path))
    monkeypatch.setattr(X, "READING", str(tmp_path / "terms-reading.json"))
    monkeypatch.setattr(X, "XML_ABS", str(tmp_path / "comments.xml"))
    (tmp_path / "terms-reading.json").write_text(
        json.dumps(terms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ── 1. 줄 번호는 마커에서 다시 센다 — 셈으로 내지 않는다

def test_relocate_reads_markers_not_arithmetic():
    """블록이 앞에 몇 개 있든 각 용어의 자리는 '그 마커 줄 + 3' 이다."""
    lines: list[str] = []
    expect: dict[str, int] = {}
    for name in ("alpha", "beta", "gamma"):
        lines.append("")                       # 블록 사이 빈 줄 — 자리가 제각각이 되게
        lines.append("x = 1")
        expect[name] = len(lines) + 1 + 3      # 마커 줄(1-based) + 블록 세 줄
        lines.append(marker(name))
        lines.append(f"# {name} 의 뜻.")
        lines.append("# 쓰는 것: 없음 · 쓰이는 곳: 없음")
        lines.append(f"def {name}():")
        lines.append("    pass")
    assert X.relocate(lines) == expect


def test_relocate_skips_comment_chunk_below_block():
    """블록은 원래 있던 주석 덩어리보다 위에 놓인다. 선언은 그 덩어리 아래다."""
    lines = [
        marker("f"),
        "# f 의 뜻.",
        "# 쓰는 것: 없음 · 쓰이는 곳: 없음",
        "# 원래 있던 설명 한 줄",
        "# 두 줄째",
        "def f():",
    ]
    assert X.relocate(lines) == {"f": 6}


# ── 2. 블록은 항상 세 줄이고 셋째 줄이 의존이다

def test_block_is_three_lines_with_uses():
    """블록은 마커 · 뜻 · 의존 세 줄이고 셋째 줄에 쓰는 것과 쓰이는 곳이 든다."""
    terms = cast(Terms, {
        "me": {"kind": "function", "means": "내가 하는 일.",
               "uses": [{"to": "a"}, {"to": "b"}]},
        "x": {"kind": "function", "means": "나를 쓰는 쪽.",
              "uses": [{"to": "me"}]},
        "a": {"kind": "function", "means": "a."},
        "b": {"kind": "function", "means": "b."},
    })
    blk = X.block_lines(["me"], terms, "#", "")
    assert len(blk) == 3
    assert blk[0].startswith("# <include")
    assert blk[1] == "# 내가 하는 일."
    assert "쓰는 것: a, b" in blk[2]
    assert "쓰이는 곳: x" in blk[2]


def test_block_says_none_when_no_uses():
    """의존이 없어도 "없음" 으로 세 줄을 채운다."""
    terms = cast(Terms, {"lonely": {"kind": "function", "means": "혼자다."}})
    blk = X.block_lines(["lonely"], terms, "//", "  ")
    assert len(blk) == 3
    assert blk[2] == "  // 쓰는 것: 없음 · 쓰이는 곳: 없음"


def test_block_caps_at_five_and_counts_the_rest():
    """의존은 다섯 개까지 적고 나머지는 개수로 접는다."""
    terms = cast(Terms, {"many": {"kind": "function", "means": "많이 쓴다.",
                                  "uses": [{"to": f"t{i}"} for i in range(8)]}})
    blk = X.block_lines(["many"], terms, "#", "")
    assert "쓰는 것: t0, t1, t2, t3, t4 (+3)" in blk[2]


# ── 3. 걷어내기 — 블록은 통째로 걷힌다

def test_strip_removes_whole_block():
    """블록은 통째로 걷힌다."""
    lines = [
        marker("f"), "# 뜻.", "# 쓰는 것: 없음 · 쓰이는 곳: 없음",
        "def f():", "    pass",
    ]
    out, _ = X.strip_blocks(lines)
    assert out == ["def f():", "    pass"]


def test_strip_removes_legacy_two_line_block():
    """이행기 — 옛 두 줄 블록도 남기지 않는다."""
    lines = [marker("f"), "# 뜻.", "def f():", "    pass"]
    out, _ = X.strip_blocks(lines)
    assert out == ["def f():", "    pass"]


# ── 4. 다시 돌려도 같다

def test_inject_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """두 번 돌린 결과가 한 번과 같다 — 덧붙지 않고 갈린다."""
    src = "def alpha():\n    return beta()\n\n\ndef beta():\n    return 1\n"
    (tmp_path / "m.py").write_text(src, encoding="utf-8")
    terms = cast(Terms, {
        "alpha": {"kind": "function", "module": ".", "where": "m.py:1",
                  "means": "알파.", "uses": [{"to": "beta"}]},
        "beta": {"kind": "function", "module": ".", "where": "m.py:5",
                 "means": "베타.", "uses": []},
    })
    fake_repo(tmp_path, monkeypatch, terms)

    X.run_inject(False)
    first = (tmp_path / "m.py").read_text(encoding="utf-8")
    read1: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    where1 = {k: v["where"] for k, v in read1.items()}

    X.run_inject(False)
    second = (tmp_path / "m.py").read_text(encoding="utf-8")
    read2: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    where2 = {k: v["where"] for k, v in read2.items()}

    assert first == second
    assert where1 == where2
    # 선언 줄을 가리켜야 한다 — 마커 줄이 아니라
    body = first.split("\n")
    assert "def alpha" in body[int(where1["alpha"].split(":")[1]) - 1]
    assert "def beta" in body[int(where1["beta"].split(":")[1]) - 1]
    assert X.run_check() == 0


def test_inject_finds_anchor_from_marker_even_if_where_is_stale(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """json 의 where 가 낡아도 파일에 마커가 있으면 그 자리를 믿는다."""
    src = "def alpha():\n    return 1\n"
    (tmp_path / "m.py").write_text(src, encoding="utf-8")
    terms = cast(Terms, {"alpha": {"kind": "function", "module": ".", "where": "m.py:1",
                                   "means": "알파.", "uses": []}})
    fake_repo(tmp_path, monkeypatch, terms)
    X.run_inject(False)

    # where 를 손으로 망가뜨린다 — 마커 줄을 가리키게
    t: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    good = t["alpha"]["where"]
    t["alpha"]["where"] = "m.py:1"
    (tmp_path / "terms-reading.json").write_text(json.dumps(t, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
    X.run_inject(False)
    t2: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    assert t2["alpha"]["where"] == good


# ── 5. 검사 — 어긋난 where 를 잡는다

def test_check_flags_where_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                    capsys: pytest.CaptureFixture[str]):
    """어긋난 where 를 찾아 이름과 함께 알리고 1 로 끝난다."""
    src = "def alpha():\n    return 1\n"
    (tmp_path / "m.py").write_text(src, encoding="utf-8")
    terms = cast(Terms, {"alpha": {"kind": "function", "module": ".", "where": "m.py:1",
                                   "means": "알파.", "uses": []}})
    fake_repo(tmp_path, monkeypatch, terms)
    X.run_inject(False)
    assert X.run_check() == 0

    t: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    t["alpha"]["where"] = "m.py:1"
    (tmp_path / "terms-reading.json").write_text(json.dumps(t, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
    (tmp_path / "comments.xml").write_text(X.emit_xml(t), encoding="utf-8")
    capsys.readouterr()
    assert X.run_check() == 1
    assert "alpha" in capsys.readouterr().out


# ── 6. 밀린 줄을 따라 옮긴다 — 마커를 못 박는 용어도 제자리를 지킨다

def test_inject_carries_unmarked_where_and_uses(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch):
    """마커를 못 박는 용어의 where 와 uses[].where 도 밀린 줄만큼 따라 내려간다."""
    src = "def alpha():\n    out = {}\n    out['nodes'] = []\n    return out\n"
    (tmp_path / "m.py").write_text(src, encoding="utf-8")
    terms = cast(Terms, {
        "alpha": {"kind": "function", "module": ".", "where": "m.py:1", "means": "알파.",
                  "uses": [{"to": "nodes[]", "where": "m.py:3"}]},
        "nodes[]": {"kind": "key", "module": ".", "where": "m.py:3", "means": "점 목록."},
    })
    fake_repo(tmp_path, monkeypatch, terms)
    X.run_inject(False)

    t: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    body = (tmp_path / "m.py").read_text(encoding="utf-8").split("\n")
    # key 는 마커를 안 박지만 블록 세 줄만큼 아래로 따라와야 한다
    assert t["nodes[]"]["where"] == "m.py:6"
    assert "nodes" in body[5]
    assert t["alpha"]["uses"][0]["where"] == "m.py:6"

    # 두 번 돌려도 더 밀리지 않는다
    X.run_inject(False)
    t2: Terms = json.loads((tmp_path / "terms-reading.json").read_text(encoding="utf-8"))
    assert t2["nodes[]"]["where"] == "m.py:6"
    assert t2["alpha"]["uses"][0]["where"] == "m.py:6"
