#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='test_survey_plan.py']"/>
# 층 계획기의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_survey_plan.py — 층 계획기의 회귀 시험."""
import collections
import json
import os
import sys
from typing import cast

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from survey_plan import CodeGraph, layer_of, pack, plan  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan._cg']"/>
# 테스트에서 쓸 가짜 코드 지도(CodeGraph)를 간단히 만들어주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_survey_plan.test_external_은_제외, machine.test_survey_plan.test_결정론, machine.test_survey_plan.test_마지막은_비노드_층, machine.test_survey_plan.test_배치는_자기_심볼의_의존_대상을_들고_있다, machine.test_survey_plan.test_배치의_파일_목록에_빈_이름이_없다 (+3)
def _cg(nodes: list[tuple[str, str]], edges: list[tuple[str, str]]) -> CodeGraph:
    return {"nodes": [{"id": i, "name": i, "kind": "function", "file": f, "line": 1}
                      for i, f in nodes],
            "edges": [{"from": s, "to": d} for s, d in edges]}


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_층은_의존_대상이_없는_것부터']"/>
# 체인처럼 이어진 의존 관계에서 층이 제대로 매겨지는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_층은_의존_대상이_없는_것부터():
    """a -> b -> c 면 c 가 층0, b 가 층1, a 가 층2 다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "c")])
    assert (lv["c"], lv["b"], lv["a"]) == (0, 1, 2)


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_고립_노드는_층0']"/>
# 간선이 하나도 없는 외톨이 노드가 어느 층에 들어가는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_고립_노드는_층0():
    """간선이 하나도 없어도 의존 대상이 없으므로 층0 이다."""
    lv, _ = layer_of({"x": 1}, [])
    assert lv["x"] == 0


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_순환은_한_덩어리로_접힌다']"/>
# 서로 물고 도는(순환) 노드들이 같은 층으로 묶이고 순환 표시가 되는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_순환은_한_덩어리로_접힌다():
    """a <-> b 는 위상 깊이가 정의되지 않는다. 같은 층으로 접고 표시한다."""
    lv, cyc = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "a"), ("a", "c")])
    assert lv["a"] == lv["b"] and cyc["a"] and cyc["b"] and not cyc["c"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_out_deg_가_아니라_위상_깊이다']"/>
# 층을 매길 때 단순히 나가는 간선 개수(out_deg)가 아니라 실제 의존 깊이를 기준으로 삼는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_out_deg_가_아니라_위상_깊이다():
    """a 는 out_deg 1, d 는 out_deg 2 지만 둘 다 층2 다 — out_deg 로 나누면 순서가 틀린다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1, "d": 1},
                     [("a", "b"), ("b", "c"), ("d", "b"), ("d", "c")])
    assert lv["a"] == 2 and lv["d"] == 2 and lv["b"] == 1 and lv["c"] == 0


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_같은_파일은_한_배치에']"/>
# 같은 파일에 속한 심볼들이 서로 다른 배치로 쪼개지지 않고 한 배치에 모이는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.pack · 쓰이는 곳: 없음
def test_같은_파일은_한_배치에():
    """파일이 쪼개지면 두 세션이 같은 파일을 각각 통독하게 된다."""
    bs = pack(["a", "b", "c", "d", "e"],
              {"a": "f1.py", "b": "f1.py", "c": "f1.py", "d": "f2.py", "e": "f2.py"}, target=3)
    for f in ["f1.py", "f2.py"]:
        assert sum(1 for b in bs if f in b["files"]) == 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_큰_파일은_초과를_허용한다']"/>
# 한 파일에 심볼이 많으면 목표 배치 크기를 넘더라도 그 파일을 쪼개지 않는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.pack · 쓰이는 곳: 없음
def test_큰_파일은_초과를_허용한다():
    """심볼 5개짜리 파일은 target 3 이어도 쪼개지 않는다."""
    bs = pack(list("abcde"), {c: "big.py" for c in "abcde"}, target=3)
    assert len(bs) == 1 and len(bs[0]["symbols"]) == 5


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_층_안에서_한_파일은_한_배치에만_있다']"/>
# 층 계획을 실제로 짰을 때 한 층 안에서 파일이 여러 배치에 나뉘어 들어가지 않는지 확인하는 시험이다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
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


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_배치의_파일_목록에_빈_이름이_없다']"/>
# file 필드가 없는 노드가 있어도 배치의 files 목록에 빈 문자열이 섞여 들어가지 않는지 확인하는 시험이다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_배치의_파일_목록에_빈_이름이_없다():
    """file 이 없는 노드는 빈 문자열로 묶인다. 그대로 두면 프롬프트가
    `file_cache.py get <repo> ` 를 빈 인자로 부르라고 시킨다."""
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "b", "name": "b", "kind": "function", "line": 1})  # file 없음
    for L in plan(cg)["layers"]:
        for b in L.get("batches", []):
            assert "" not in b["files"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_결정론']"/>
# 같은 입력을 두 번 넣었을 때 plan() 이 항상 같은 결과를 내는지(순서가 흔들리지 않는지) 확인하는 시험이다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_결정론():
    """같은 입력이면 같은 출력. 순서가 흔들리면 계획이 재현되지 않는다."""
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f2")], [("a", "b"), ("b", "c")])
    assert json.dumps(plan(cg), sort_keys=True) == json.dumps(plan(cg), sort_keys=True)


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_external_은_제외']"/>
# kind 가 external 인 노드는 층 계획을 세울 때 심볼 수에 포함되지 않는지 확인하는 시험이다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_external_은_제외():
    """external 노드는 계획에 세지 않는다."""
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "ext", "name": "ext", "kind": "external"})
    assert plan(cg)["totals"]["symbols"] == 1


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_마지막은_비노드_층']"/>
# file · module · artifact · key · concept 같은, 코드 노드가 아닌 것들이 계획의 맨 마지막 층으로 따로 빠지는지 확인하는 시험이다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_마지막은_비노드_층():
    """file · module · artifact · key · concept 는 층 축이 없어 맨 뒤 별도 층이다."""
    # `kind` 가 있다는 것이 이 시험이 보는 내용이라 `.get` 으로 무르게 하지 않는다.
    assert plan(_cg([("a", "f1")], []))["layers"][-1]["kind"] == "non-node"  # pyright: ignore[reportTypedDictNotRequiredAccess]


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_배치는_자기_심볼의_의존_대상을_들고_있다']"/>
# 계획 안의 각 심볼 레코드가 자신이 의존하는 대상 목록(depends_on)을 함께 갖고 있는지 확인하는 시험이다. 이후 배치 프롬프트가 아래층 레코드를 발췌할 때 이 정보가 필요하다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_배치는_자기_심볼의_의존_대상을_들고_있다():
    """배치 프롬프트가 아래층 레코드를 발췌하려면 depends_on 이 계획 안에 있어야 한다."""
    cg = _cg([("a", "f1"), ("b", "f2")], [("a", "b")])
    top = [L for L in plan(cg)["layers"] if L.get("level") == 1][0]
    assert top["batches"][0]["symbols"][0]["depends_on"] == ["b"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_증분은_층_번호를_보존한다']"/>
# warmup 이 준 파일 목록만으로 계획을 걸러도(only_files), 층 번호는 걸러내기 전 전체 그래프 기준으로 매겨져야 한다는 것을 확인하는 시험이다. 거른 뒤에 다시 매기면 사라진 의존 대상 때문에 층이 실제보다 낮게 나온다.
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_증분은_층_번호를_보존한다():
    """warmup 이 준 파일만 남기되 층은 **전체 그래프 기준**이어야 한다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다."""
    cg = _cg([("a", "f1"), ("b", "f2"), ("c", "f3")], [("a", "b"), ("b", "c")])
    p = plan(cg, only_files=["f1"])
    assert p["totals"]["symbols"] == 1 and p["layers"][0]["level"] == 2


REAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "out", "codegraph-raw", "codegraph.json")


@pytest.mark.skipif(not os.path.exists(REAL), reason="out/codegraph-raw/codegraph.json 이 없다")
# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_이_저장소_실측']"/>
# 가짜 데이터가 아니라 이 저장소가 실제로 만든 codegraph.json 파일을 넣어, 층별 심볼 개수 분포가 예상한 숫자와 정확히 같은지 못박아 두는 회귀 시험이다. out/codegraph-raw/codegraph.json 이 없으면 pytest.mark.skipif 로 건너뛴다(machine/test_survey_plan.py:121).
# 쓰는 것: machine.survey_plan.plan, machine.test_survey_plan._cg · 쓰이는 곳: 없음
def test_이_저장소_실측():
    """이 저장소의 실제 지도로 층 분포를 못박는다 — 코드가 바뀌면 기대값을 함께 고친다."""
    p = plan(json.load(open(REAL, encoding="utf-8")))
    sizes = [L["symbol_count"] for L in p["layers"] if L.get("kind") != "non-node"]
    assert sizes == [232, 217, 145, 87, 12, 4]
    # ⚠ cast — `symbol_count` 가 None 인 것은 비노드 층뿐이고 그것은 바로 위 조건이 걸렀다.
    assert sum(cast(list[int], sizes)) == p["totals"]["symbols"] == 697
    # lock 없는 설계의 전제 — 실제 지도에서도 층 안 파일이 배타적이어야 한다
    for L in p["layers"]:
        seen = collections.Counter(f for b in L.get("batches", []) for f in b["files"])
        assert [f for f, n in seen.items() if n > 1] == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_간선은_from_이_의존하는_쪽이다']"/>
# 간선 {from, to} 에서 from 이 to 에 의존한다는 방향을 layer_of 가 올바르게 해석하는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_간선은_from_이_의존하는_쪽이다():
    """`{from: A, to: B}` 는 "A 가 B 에 의존" 이다 — 뒤집어 읽으면 정렬이 정반대가 된다.

    out_deg 0(아무것도 안 끌어옴)이 층0 이고, in_deg 0(아무도 안 씀 = 진입점)이 맨 위층이다.
    """
    # main 이 util 을 부른다  ->  (main, util)
    lv, _ = layer_of({"main": 1, "util": 1}, [("main", "util")])
    assert lv["util"] == 0, "의존받기만 하는 util 이 층0 이어야 한다"
    assert lv["main"] == 1, "남을 부르는 main 은 위층이어야 한다"


# <include file="machine/comments.xml" path="//term[@id='machine.test_survey_plan.test_진입점은_맨_위층이다']"/>
# 아무도 쓰지 않는 진입점(in_deg 0)이 가장 위층에 오고, 맨 끝 잎(leaf)이 가장 아래층에 오는지 확인하는 시험 함수다.
# 쓰는 것: machine.survey_plan.layer_of · 쓰이는 곳: 없음
def test_진입점은_맨_위층이다():
    """in_deg 0 은 아무도 안 쓰는 것 = 진입점이다. 거기서 시작하면 top-down 이 된다."""
    lv, _ = layer_of({"main": 1, "mid": 1, "leaf": 1},
                     [("main", "mid"), ("mid", "leaf")])
    진입점 = [n for n in ("main", "mid", "leaf")
              if not any(d == n for _, d in [("main", "mid"), ("mid", "leaf")])]
    assert 진입점 == ["main"]
    assert lv["main"] == max(lv.values())      # 진입점이 맨 위
    assert lv["leaf"] == 0                     # 잎이 맨 아래
