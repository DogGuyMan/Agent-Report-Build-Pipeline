# <include file="machine/comments.xml" path="//term[@id='test_external_contracts.py']"/>
# 바깥 도구(griffe·clang-doc·Graphviz·networkx)의 동작에 기대는 주장을 고정하는 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_external_contracts.py — 바깥 도구의 동작에 기대는 주장을 고정한다.

이 저장소의 코드는 griffe · clang-doc · Graphviz · networkx 의 동작을 전제로 짜여 있다.
그 전제를 주석에만 적어 두면 도구가 바뀔 때 조용히 낡는다. 여기 적으면 깨진다.
"""
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import declmap as D  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_networkx_digraph_is_not_subscriptable_at_runtime']"/>
# networkx 의 DiGraph 가 실행 중에는 대괄호로 타입을 못 받는다는 것을 확인하는 시험 함수다.
# 쓰는 것: networkx.DiGraph · 쓰이는 곳: 없음
# ── 1. networkx — 실행 시각에 DiGraph 는 첨자를 못 받는다
def test_networkx_digraph_is_not_subscriptable_at_runtime() -> None:
    """`nx.DiGraph[str]` 은 TypeError 다. 그래서 서명의 주석을 따옴표에 넣는다.

    이 시험이 깨지면 `viz/render_*.py` 와 `machine/facts.py` 의 따옴표를 벗겨도 된다.
    """
    with pytest.raises(TypeError):
        nx.DiGraph[str]                                          # type: ignore[misc]


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts._svg_size']"/>
# Graphviz dot 명령으로 그림을 그려서 그 SVG 의 가로세로 크기(pt 단위)를 숫자로 꺼내주는 도우미 함수다.
# 쓰는 것: subprocess.run, re.search · 쓰이는 곳: machine.test_external_contracts.test_graphviz_legend_edge_without_constraint_widens_the_canvas
# ── 2. Graphviz — 범례 간선의 constraint 가 캔버스 너비를 정한다
def _svg_size(dot_src: str, tmp: Path) -> tuple[float, float]:
    src = tmp / "g.dot"
    src.write_text(dot_src, encoding="utf-8")
    out = subprocess.run(["dot", "-Tsvg", str(src)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    m = re.search(r'width="([\d.]+)pt" height="([\d.]+)pt"', out.stdout)
    assert m, out.stdout[:300]
    return float(m.group(1)), float(m.group(2))


_LEGEND = """digraph g {{
  rankdir=BT;
  a -> b; b -> c;
  la [label="범례A"]; lb [label="범례B"];
  la -> lb [constraint={c}];
}}"""


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_graphviz_legend_edge_without_constraint_widens_the_canvas']"/>
# Graphviz(그림을 그려주는 외부 프로그램)의 동작 하나가 여전히 사실인지 확인하는 시험 함수다.
# 쓰는 것: machine.test_external_contracts._svg_size · 쓰이는 곳: 없음
def test_graphviz_legend_edge_without_constraint_widens_the_canvas(tmp_path: Path) -> None:
    """범례 간선을 `constraint=false` 로 두면 랭크 제약이 없어 캔버스가 옆으로 넓어진다.

    `viz/render_modules.py` · `render_classes.py` 가 범례 간선만 `constraint=true` 로
    두는 근거다. 이 시험이 깨지면 그 주석과 코드를 함께 다시 봐야 한다.
    """
    if shutil.which("dot") is None:
        pytest.skip("graphviz 없음")
    w_on, _ = _svg_size(_LEGEND.format(c="true"), tmp_path)
    w_off, _ = _svg_size(_LEGEND.format(c="false"), tmp_path)
    assert w_off > w_on


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_langs_table_shape_is_uniform']"/>
# declmap.py 의 LANGS 표에서 cpp·cs·py·ts 네 언어가 전부 같은 다섯 칸(exts, decl, doc, lead, strip)을 갖고, 각 칸의 값 타입이 정해진 대로인지 확인하는 시험이다.
# 쓰는 것: declmap.LANGS · 쓰이는 곳: 없음
# ── 3. declmap 의 LANGS 표 — 다섯 칸의 형이 실제로 고정돼 있는가
def test_langs_table_shape_is_uniform() -> None:
    """네 언어 전부 같은 다섯 칸을 갖고, 칸마다 형이 고정돼 있다.

    `exts`·`doc` 는 튜플, `decl`·`lead` 는 컴파일된 정규식, `strip` 만 None 이 될 수 있다.
    `LangRule` TypedDict 가 이 사실 위에 서 있다 — 새 언어를 더하며 한 칸을 빠뜨리거나
    형을 바꾸면 여기가 먼저 잡는다.
    """
    assert set(D.LANGS) == {"cpp", "cs", "py", "ts"}
    for lang, rule in D.LANGS.items():
        assert set(rule) == {"exts", "decl", "doc", "lead", "strip"}, lang
        assert isinstance(rule["exts"], tuple) and rule["exts"], lang
        assert all(isinstance(e, str) and e.startswith(".") for e in rule["exts"]), lang
        assert isinstance(rule["doc"], tuple) and rule["doc"], lang
        assert isinstance(rule["decl"], re.Pattern), lang
        assert isinstance(rule["lead"], re.Pattern), lang
        assert rule["strip"] is None or isinstance(rule["strip"], re.Pattern), lang
    # None 이 되는 칸이 strip 뿐이라는 것도 함께 못박는다 — 실제로 cs 만 값을 갖는다.
    assert [k for k, r in D.LANGS.items() if r["strip"] is not None] == ["cs"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_declmap_regex_is_line_based_and_syntax_blind']"/>
# declmap.py 의 선언 탐지 정규식이 프로그래밍 언어 문법을 전혀 모르고 그냥 한 줄씩 문자열 패턴만 본다는 한계를 확인하는 시험이다.
# 쓰는 것: declmap.LANGS · 쓰이는 곳: 없음
def test_declmap_regex_is_line_based_and_syntax_blind() -> None:
    """정규식이라 문법을 모른다 — 문자열 안의 `class` 에도 걸리고, 한 줄만 본다.

    산출물이 코드 지도가 아니라는 것의 근거다. 이 한계가 사라지면(= 이 시험이 깨지면)
    `declmap.py` 의 "코드 지도가 아니다" 주석을 다시 봐야 한다.
    `scan()` 이 아니라 정규식을 직접 겨눈다 — `scan` 은 `git ls-files` 를 타므로
    이 한계와 무관한 것(git 추적 여부)까지 함께 시험하게 된다.
    """
    decl = D.LANGS["py"]["decl"]
    assert decl.match("class Real:")                       # 진짜 선언
    assert decl.match('class Fake:  # 주석 안이 아니어도')
    # 한 줄만 본다 — 여는 괄호에서 끊긴 선언의 둘째 줄은 아무것도 아니다.
    assert not decl.match("    x,")
    # C++ 은 문자열 리터럴 안의 class 에 실제로 속는다.
    assert D.LANGS["cpp"]["decl"].match('class Fake;')


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_griffe_gives_expression_trees_not_strings']"/>
# 외부 도구 griffe 가 타입 주석을 평범한 문자열이 아니라 구조화된 식(expression) 트리로 내놓는다는 것을 확인하는 시험이다.
# 쓰는 것: subprocess.run · 쓰이는 곳: 없음
# ── 4. griffe — 이 저장소가 기대는 출력 모양
def test_griffe_gives_expression_trees_not_strings(tmp_path: Path) -> None:
    """타입 주석은 문자열이 아니라 구조화된 식 트리로 온다.

    R5(컨테이너 투과)가 이 사실 위에 서 있다. 문자열로 돌아가면 `py_walk_expr` 이
    통째로 못 쓰게 된다.
    """
    import importlib.util
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치")
    import json
    (tmp_path / "gx").mkdir()
    (tmp_path / "gx" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "gx" / "m.py").write_text(
        "class A:\n    xs: list[int]\n", encoding="utf-8")
    out = tmp_path / "g.json"
    r = subprocess.run([sys.executable, "-m", "griffe", "dump", "gx",
                        "-o", str(out), "-s", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    ann = json.loads(out.read_text(encoding="utf-8"))["gx"]["members"]["m"] \
        ["members"]["A"]["members"]["xs"]["annotation"]
    assert isinstance(ann, dict), "문자열로 돌아왔다 — R5 의 전제가 깨졌다"
    assert ann["cls"] == "ExprSubscript"
    assert ann["left"]["name"] == "list"


# <include file="machine/comments.xml" path="//term[@id='machine.test_external_contracts.test_python_ast_unparse_round_trips_annotations']"/>
# 파이썬 표준 라이브러리 ast.unparse 가 함수 시그니처를 원문 그대로 되살리는지 확인하는 시험 함수다.
# 쓰는 것: machine.pycalls.signature_of · 쓰이는 곳: 없음
def test_python_ast_unparse_round_trips_annotations() -> None:
    """`pycalls.signature_of` 는 `ast.unparse` 로 주석을 되살린다. 원문 그대로여야 한다."""
    src = "def f(a: dict[str, int] = {}, *, b: str | None = None) -> bool: ...\n"
    fn = ast.parse(src).body[0]
    assert isinstance(fn, ast.FunctionDef)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pycalls import signature_of
    assert signature_of(fn) == "(a: dict[str, int] = {}, *, b: str | None = None) -> bool"
