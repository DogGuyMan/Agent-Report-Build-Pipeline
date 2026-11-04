#!/usr/bin/env python3
"""test_survey_plan.py — 층 계획기의 회귀 시험."""
import collections
import json
import os
import sys
from typing import cast

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "runner"), os.path.join(ROOT, "src", "codewiki", "python", "machine"),
                os.path.join(ROOT, "src", "codewiki", "python", "viz")]
import survey_plan as SP  # noqa: E402
from survey_plan import CodeGraph, layer_of, pack, plan  # noqa: E402


def _cg(nodes: list[tuple[str, str]], edges: list[tuple[str, str]]) -> CodeGraph:
    return {"nodes": [{"id": i, "name": i, "kind": "function", "file": f, "line": 1}
                      for i, f in nodes],
            "edges": [{"from": s, "to": d} for s, d in edges]}


def test_층은_의존_대상이_없는_것부터():
    """a -> b -> c 면 c 가 층0, b 가 층1, a 가 층2 다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "c")])
    assert (lv["c"], lv["b"], lv["a"]) == (0, 1, 2)


def test_고립_노드는_층0():
    """간선이 하나도 없어도 의존 대상이 없으므로 층0 이다."""
    lv, _ = layer_of({"x": 1}, [])
    assert lv["x"] == 0


def test_순환은_한_덩어리로_접힌다():
    """a <-> b 는 위상 깊이가 정의되지 않는다. 같은 층으로 접고 표시한다."""
    lv, cyc = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "a"), ("a", "c")])
    assert lv["a"] == lv["b"] and cyc["a"] and cyc["b"] and not cyc["c"]


def test_out_deg_가_아니라_위상_깊이다():
    """a 는 out_deg 1, d 는 out_deg 2 지만 둘 다 층2 다 — out_deg 로 나누면 순서가 틀린다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1, "d": 1},
                     [("a", "b"), ("b", "c"), ("d", "b"), ("d", "c")])
    assert lv["a"] == 2 and lv["d"] == 2 and lv["b"] == 1 and lv["c"] == 0


def test_같은_파일은_한_배치에():
    """파일이 쪼개지면 두 세션이 같은 파일을 각각 통독하게 된다."""
    bs = pack(["a", "b", "c", "d", "e"],
              {"a": "f1.py", "b": "f1.py", "c": "f1.py", "d": "f2.py", "e": "f2.py"}, target=3)
    for f in ["f1.py", "f2.py"]:
        assert sum(1 for b in bs if f in b["files"]) == 1


def test_큰_파일은_초과를_허용한다():
    """심볼 5개짜리 파일은 target 3 이어도 쪼개지 않는다."""
    bs = pack(list("abcde"), {c: "big.py" for c in "abcde"}, target=3)
    assert len(bs) == 1 and len(bs[0]["symbols"]) == 5


def test_층_안에서_한_파일은_한_배치에만_있다():
    """lock 없는 설계의 전제다 — 깨지면 두 세션이 같은 파일을 동시에 연다.

    `pack` 을 직접 부르는 위 시험과 달리 `plan` 이 낸 실제 배치를 본다.
    층을 나누고 배치를 묶는 두 단계가 함께 성립해야 의미가 있다.
    """
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f1"), ("d", "f2"),
              ("e", "f3"), ("f", "f4"), ("g", "f5")], [])
    for L in plan(cg, target=2)["layers"]:
        seen = collections.Counter(f for b in L.get("batches", []) for f in b["files"])
        assert [f for f, n in seen.items() if n > 1] == []


def test_배치의_파일_목록에_빈_이름이_없다():
    """file 이 없는 노드는 빈 문자열로 묶인다. 그대로 두면 프롬프트가
    `file_cache.py get <repo> ` 를 빈 인자로 부르라고 시킨다."""
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "b", "name": "b", "kind": "function", "line": 1})  # file 없음
    for L in plan(cg)["layers"]:
        for b in L.get("batches", []):
            assert "" not in b["files"]


def test_결정론():
    """같은 입력이면 같은 출력. 순서가 흔들리면 계획이 재현되지 않는다."""
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f2")], [("a", "b"), ("b", "c")])
    assert json.dumps(plan(cg), sort_keys=True) == json.dumps(plan(cg), sort_keys=True)


def test_external_은_제외():
    """external 노드는 계획에 세지 않는다."""
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "ext", "name": "ext", "kind": "external"})
    assert plan(cg)["totals"]["symbols"] == 1


def test_마지막은_비노드_층():
    """file · module · artifact · key · concept 는 층 축이 없어 맨 뒤 별도 층이다."""
    # `kind` 가 있다는 것이 이 시험이 보는 내용이라 `.get` 으로 무르게 하지 않는다.
    assert plan(_cg([("a", "f1")], []))["layers"][-1]["kind"] == "non-node"  # pyright: ignore[reportTypedDictNotRequiredAccess]


def test_배치는_자기_심볼의_의존_대상을_들고_있다():
    """배치 프롬프트가 아래층 레코드를 발췌하려면 depends_on 이 계획 안에 있어야 한다."""
    cg = _cg([("a", "f1"), ("b", "f2")], [("a", "b")])
    top = [L for L in plan(cg)["layers"] if L.get("level") == 1][0]
    assert top["batches"][0]["symbols"][0]["depends_on"] == ["b"]


def test_증분은_층_번호를_보존한다():
    """warmup 이 준 파일만 남기되 층은 **전체 그래프 기준**이어야 한다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다."""
    cg = _cg([("a", "f1"), ("b", "f2"), ("c", "f3")], [("a", "b"), ("b", "c")])
    p = plan(cg, only_files=["f1"])
    assert p["totals"]["symbols"] == 1 and p["layers"][0]["level"] == 2


SNAPSHOT = os.path.join(ROOT, "test", "codewiki", "fixtures", "codegraph-self.json")
REAL = os.path.join(ROOT, "out", "codegraph-raw", "codegraph.json")


def _layer_files_overlap(p: SP.SurveyPlan) -> list[str]:
    """한 층 안에서 두 배치 이상에 나오는 파일. lock 없는 설계의 전제라 비어 있어야 한다."""
    return [f for L in p["layers"]
            for f, n in collections.Counter(f for b in L.get("batches", []) for f in b["files"]).items()
            if n > 1]


def test_실제_지도_스냅샷의_층_분포():
    """이 저장소의 실제 지도를 얼린 스냅샷으로 층 분포를 못박는다 — 계획기가 바뀔 때만 깨진다.

    스냅샷은 `report-wiki prep .` 의 `codegraph.json` 에서 `plan` 이 읽는 열쇠
    (id · name · kind · file · line · from · to)만 남긴 것이다. 코드가 바뀌어도 스냅샷은 그대로다.
    """
    p = plan(json.load(open(SNAPSHOT, encoding="utf-8")))
    sizes = [L["symbol_count"] for L in p["layers"] if L.get("kind") != "non-node"]
    assert sizes == [497, 107, 54, 22, 14, 6]
    # ⚠ cast — `symbol_count` 가 None 인 것은 비노드 층뿐이고 그것은 바로 위 조건이 걸렀다.
    assert sum(cast(list[int], sizes)) == p["totals"]["symbols"] == 700
    assert _layer_files_overlap(p) == []


@pytest.mark.skipif(not os.path.exists(REAL), reason="out/codegraph-raw/codegraph.json 이 없다")
def test_이_기계의_지도도_층_안_파일이_배타적이다():
    """지금 이 기계의 지도에서도 층 안 배치끼리 파일이 겹치지 않는다. 분포는 코드와 함께 움직여 보지 않는다."""
    p = plan(json.load(open(REAL, encoding="utf-8")))
    sizes = [L["symbol_count"] for L in p["layers"] if L.get("kind") != "non-node"]
    assert sum(cast(list[int], sizes)) == p["totals"]["symbols"]
    assert _layer_files_overlap(p) == []


def test_간선은_from_이_의존하는_쪽이다():
    """`{from: A, to: B}` 는 "A 가 B 에 의존" 이다 — 뒤집어 읽으면 정렬이 정반대가 된다.

    out_deg 0(아무것도 안 끌어옴)이 층0 이고, in_deg 0(아무도 안 씀 = 진입점)이 맨 위층이다.
    """
    # main 이 util 을 부른다  ->  (main, util)
    lv, _ = layer_of({"main": 1, "util": 1}, [("main", "util")])
    assert lv["util"] == 0, "의존받기만 하는 util 이 층0 이어야 한다"
    assert lv["main"] == 1, "남을 부르는 main 은 위층이어야 한다"


def test_진입점은_맨_위층이다():
    """in_deg 0 은 아무도 안 쓰는 것 = 진입점이다. 거기서 시작하면 top-down 이 된다."""
    lv, _ = layer_of({"main": 1, "mid": 1, "leaf": 1},
                     [("main", "mid"), ("mid", "leaf")])
    진입점 = [n for n in ("main", "mid", "leaf")
              if not any(d == n for _, d in [("main", "mid"), ("mid", "leaf")])]
    assert 진입점 == ["main"]
    assert lv["main"] == max(lv.values())      # 진입점이 맨 위
    assert lv["leaf"] == 0                     # 잎이 맨 아래


# ── 파일 가중치와 파일 단위 계획 ──────────────────────────────────────────

def _cg2(nodes: list[tuple[str, str, str]], edges: list[tuple[str, str]],
         abstraction: dict[str, str] | None = None) -> CodeGraph:
    """(id, 이름, 파일). 이름의 마지막 마디가 `_` 로 시작하면 비공개다."""
    out: CodeGraph = {"nodes": [{"id": i, "name": n, "kind": "function", "file": f, "line": 1}
                                for i, n, f in nodes],
                      "edges": [{"from": s, "to": d} for s, d in edges]}
    for i, a in (abstraction or {}).items():
        node = next(x for x in out["nodes"] if x["id"] == i)
        node["kind"] = "class"; node["abstraction"] = a   # pyright: ignore[reportGeneralTypeIssues]
    return out


def test_공개는_마지막_마디가_밑줄로_시작하지_않는_것():
    assert SP.is_public("m.run") and SP.is_public("m.Cls.run")
    assert not SP.is_public("m._helper") and not SP.is_public("m.Cls.__init__") and not SP.is_public("m.Cls._x")


def test_파일_가중치_out_은_모든_심볼_in_은_공개_심볼만_센다():
    # a.py: pub 가 b.py 의 pub 을, _priv 가 c.py 의 pub 을 쓴다. c.py 의 _hidden 이 a.py 의 pub 을 쓴다(비공개 → 안 셈)
    cg = _cg2([("a1", "a.pub", "a.py"), ("a2", "a._priv", "a.py"),
               ("b1", "b.pub", "b.py"), ("c1", "c.pub", "c.py"), ("c2", "c._hidden", "c.py"),
               ("c3", "c.other", "c.py")],
              [("a1", "b1"), ("a2", "c1"), ("c2", "a1"), ("c3", "a2"), ("a1", "a2")])
    w = {r["file"]: r for r in SP.file_weights(cg)}
    assert (w["a.py"]["out"], w["a.py"]["into"]) == (2, 1)     # c._hidden → a.pub: 받는 쪽이 공개라 센다. c.other → a._priv: 받는 쪽 비공개라 안 센다. 같은 파일 간선도 안 센다
    assert (w["b.py"]["out"], w["b.py"]["into"]) == (0, 1)
    assert (w["c.py"]["out"], w["c.py"]["into"]) == (2, 1)


def test_파일_가중치_수식은_세_항의_합이고_큰_순으로_난다():
    cg = _cg2([("a", "a.f", "a.py"), ("b", "b.f", "b.py"), ("c", "c.I", "c.py"), ("d", "d.A", "d.py")],
              [("a", "b"), ("a", "c"), ("d", "b")], {"c": "interface", "d": "abstract"})
    rows = SP.file_weights(cg)
    w = {r["file"]: r for r in rows}
    # out_max = 2(a) · into_max = 2(b) · 추상 점수 최대 = 5(c: 인터페이스)
    assert w["a.py"]["weight"] == pytest.approx((1 - 2 / 2) + 0 / 2 + 0)
    assert w["b.py"]["weight"] == pytest.approx((1 - 0 / 2) + 2 / 2 + 0)
    assert w["c.py"]["weight"] == pytest.approx((1 - 0 / 2) + 1 / 2 + 5 / 5)
    assert w["d.py"]["weight"] == pytest.approx((1 - 1 / 2) + 0 / 2 + 3 / 5)
    assert [r["file"] for r in rows] == ["c.py", "b.py", "d.py", "a.py"]
    assert (w["c.py"]["interfaces"], w["d.py"]["abstracts"]) == (1, 1)


def test_파일_가중치_최대값이_0이면_그_항은_0이_아니라_정의대로():
    cg = _cg2([("a", "a.f", "a.py"), ("b", "b.f", "b.py")], [])
    w = {r["file"]: r for r in SP.file_weights(cg)}
    assert w["a.py"]["weight"] == pytest.approx(1.0)      # out 항은 의존이 하나도 없으면 1, 나머지는 0


def test_파일_계획은_파일_하나가_배치_하나이고_가중치_내림차순():
    cg = _cg2([("a", "a.f", "a.py"), ("a2", "a.g", "a.py"), ("b", "b.f", "b.py")], [("a", "b")])
    p = SP.plan_by_file(cg)
    assert p["layers"][0]["batches"][0]["files"] == ["b.py"]     # b 가 피의존 1, 의존 0 → 앞
    assert [b["id"] for b in p["layers"][0]["batches"]] == ["F00", "F01"]
    assert sorted(s["name"] or "" for s in p["layers"][0]["batches"][1]["symbols"]) == ["a.f", "a.g"]
    assert p["layers"][0]["batches"][0].get("weight", 0.0) > p["layers"][0]["batches"][1].get("weight", 0.0)
    assert p["layers"][-1].get("kind") == "non-node" and p["totals"]["symbols"] == 3
    assert p["layers"][0]["batches"][1]["symbols"][0]["depends_on"] == ["b"]


def test_파일_계획은_결정론():
    cg = _cg2([("a", "a.f", "a.py"), ("b", "b.f", "b.py")], [("a", "b")])
    assert json.dumps(SP.plan_by_file(cg), sort_keys=True) == json.dumps(SP.plan_by_file(cg), sort_keys=True)


def test_가중치_csv_는_원값과_가중치를_함께_적는다():
    cg = _cg2([("a", "a.f", "a.py"), ("b", "b.f", "b.py")], [("a", "b")])
    text = SP.weights_csv(SP.file_weights(cg))
    lines = text.splitlines()
    assert lines[0] == "file,out,into,interfaces,abstracts,weight"
    assert lines[1].startswith("b.py,0,1,0,0,") and lines[2].startswith("a.py,1,0,0,0,")
