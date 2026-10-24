"""단계 기계의 시험. 갈래 · 전이표 · 그래프 · 시뮬레이터 · 드라이버."""
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict

import msgspec
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M  # noqa: E402
import pipeline as P  # noqa: E402
from tools.template import TemplateError  # noqa: E402


class Terms(TypedDict):
    """시험용 산출물 꼴."""
    terms: list[str]


def test_갈래_넷은_서로_다른_비트다():
    assert len({P.OK, P.FAIL, P.SKIP, P.GATE}) == 4
    assert P.OK | P.FAIL | P.SKIP | P.GATE == 15


def test_Outcome_은_행_없이도_만들어진다():
    out = P.Outcome(P.OK)
    assert out.kind == P.OK
    assert out.why == ""
    assert out.rows == []


def test_Outcome_둘이_행_목록을_공유하지_않는다():
    a, b = P.Outcome(P.OK), P.Outcome(P.OK)
    a.rows.append({"stage": "x", "seconds": 0.0, "usage": {}, "ok": True, "why": ""})
    assert b.rows == []


def test_RunContext_는_네_칸을_갖는다():
    ctx = P.RunContext(root="/r", model="opus")
    assert (ctx.root, ctx.model, ctx.timeout, ctx.concurrency) == ("/r", "opus", None, 8)


def test_Artifact_는_ctx_로_자리를_정한다():
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    assert art.locate(P.RunContext(root="/r", model="opus")) == "/r/plan.md"
    assert art.schema is None


class 가짜단계(P.Stage[P.RunContext]):
    """시험용. 정해진 갈래를 그대로 낸다."""

    def __init__(self, name: str, kind: int = P.OK, emits: int = P.OK | P.FAIL,
                 reads: list[P.Artifact[P.RunContext]] | None = None,
                 writes: list[P.Artifact[P.RunContext]] | None = None) -> None:
        self.name = name
        self.emits = emits
        self._kind = kind
        self._reads = reads or []
        self._writes = writes or []
        self.돈횟수 = 0

    def reads(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
        return self._reads

    def writes(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
        return self._writes

    def perform(self, ctx: P.RunContext) -> P.Outcome:
        self.돈횟수 += 1
        return P.Outcome(self._kind, "", [{"stage": self.name, "seconds": 0.0,
                                           "usage": M.normalize_usage(None),
                                           "ok": self._kind == P.OK, "why": ""}])


def cast_가짜(st: "P.Stage[P.RunContext]") -> 가짜단계:
    assert isinstance(st, 가짜단계)
    return st


def test_읽을_것이_없으면_이름으로_말해_준다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    st = 가짜단계("collect", reads=[art])
    assert P.missing_reads(st, ctx) == ["읽을 것이 없다 — 계획"]


def test_읽을_것이_있으면_불평이_없다(tmp_path: Path):
    (tmp_path / "plan.md").write_text("x", encoding="utf-8")
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    assert P.missing_reads(가짜단계("collect", reads=[art]), ctx) == []


def test_꼴이_어긋난_산출물은_불평이_된다(tmp_path: Path):
    (tmp_path / "q.json").write_text('{"terms": [1]}', encoding="utf-8")
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("문항지", lambda c: os.path.join(c.root, "q.json"), Terms)
    bad = P.bad_writes(가짜단계("x", writes=[art]), ctx)
    assert len(bad) == 1 and bad[0].startswith("문항지 — ") and "$.terms[0]" in bad[0]


def test_load_는_형으로_읽고_틀리면_던진다(tmp_path: Path):
    p = tmp_path / "t.json"
    p.write_text('{"terms": ["a"]}', encoding="utf-8")
    assert P.load(str(p), Terms) == {"terms": ["a"]}
    p.write_text('{"terms": "a"}', encoding="utf-8")
    with pytest.raises(msgspec.ValidationError):
        P.load(str(p), Terms)


def test_단계_안의_꼴_예외는_FAIL_행이_된다(tmp_path: Path):
    class 던지는단계(P.Stage[P.RunContext]):
        name = "s"

        def perform(self, ctx: P.RunContext) -> P.Outcome:
            msgspec.convert({"terms": 1}, Terms)
            return P.Outcome(P.OK)
    ctx = P.RunContext(root=str(tmp_path), model="m")
    g = P.build_graph("g", ["s"], {"s": 던지는단계()},
                      P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), [], ctx)
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert rows[0]["ok"] is False and "$.terms" in rows[0]["why"]


def test_쓰지_못한_산출물은_없다고_말한다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("보고서", lambda c: os.path.join(c.root, "r.html"))
    assert P.bad_writes(가짜단계("build", writes=[art]), ctx) == ["보고서 — 나오지 않았다"]


def test_드라이버가_쓸_산출물의_폴더를_미리_만든다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="m")
    art = P.Artifact[P.RunContext]("지도", lambda c: os.path.join(c.root, "out", "raw", "g.json"))

    class 쓰는단계(P.Stage[P.RunContext]):
        name = "s"

        def writes(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]:
            return [art]

        def perform(self, ctx: P.RunContext) -> P.Outcome:
            with open(art.locate(ctx), "w", encoding="utf-8") as f:
                f.write("{}")
            return P.Outcome(P.OK, "", [{"stage": "s", "seconds": 0.0,
                                         "usage": M.normalize_usage(None), "ok": True, "why": ""}])
    g = P.build_graph("g", ["s"], {"s": 쓰는단계()},
                      P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), [], ctx)
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert rows[0]["ok"] is True and os.path.exists(art.locate(ctx))


def test_전이표는_단계별_규칙을_먼저_본다():
    e = P.Edges({("lang-propose", P.FAIL): "lang-decide",
                 ("*", P.FAIL): P.HALT,
                 ("*", P.OK): P.NEXT})
    assert e.dest("lang-propose", P.FAIL) == "lang-decide"
    assert e.dest("prep", P.FAIL) == P.HALT
    assert e.dest("prep", P.OK) == P.NEXT


def test_전이표에_없는_갈래는_None_이다():
    e = P.Edges({("*", P.OK): P.NEXT})
    assert e.dest("prep", P.SKIP) is None


def test_전이표는_넘겨받은_사전을_복사한다():
    표 = {("*", P.OK): P.NEXT}
    e = P.Edges(표)
    표[("*", P.FAIL)] = P.HALT
    assert e.dest("prep", P.FAIL) is None


def 삼단_그래프(kinds: dict[str, int] | None = None) -> P.StageDagGraph[P.RunContext]:
    kinds = kinds or {}
    names = ["a", "b", "c"]
    stages: dict[str, P.Stage[P.RunContext]] = {
        n: 가짜단계(n, kinds.get(n, P.OK)) for n in names}
    return P.StageDagGraph(name="시험", order=names, stages=stages,
                           edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))


def test_첫_단계는_순서의_맨_앞이다():
    assert 삼단_그래프().first == "a"


def test_빈_그래프의_첫_단계는_None_이다():
    g: P.StageDagGraph[P.RunContext] = P.StageDagGraph(
        name="빈", order=[], stages={}, edges=P.Edges({}))
    assert g.first is None


def test_NEXT_는_순서상_다음_단계다():
    g = 삼단_그래프()
    assert g.next_of("a", P.OK) == "b"
    assert g.next_of("c", P.OK) is None


def test_HALT_는_흐름을_끝낸다():
    assert 삼단_그래프().next_of("b", P.FAIL) is None


def test_이름을_적은_간선은_그리로_점프한다():
    stages: dict[str, P.Stage[P.RunContext]] = {n: 가짜단계(n) for n in ["a", "b", "c"]}
    g = P.StageDagGraph(
        name="점프", order=["a", "b", "c"], stages=stages,
        edges=P.Edges({("a", P.OK): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert g.next_of("a", P.OK) == "c"


def test_render_는_단계마다_갈래를_보인다():
    글 = 삼단_그래프().render()
    assert "a" in 글 and "OK→b" in 글 and "FAIL→(멈춤)" in 글
    assert "OK→(끝)" in 글


def test_어긋난_것이_없으면_불평이_없다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    assert P.simulate(삼단_그래프(), ctx) == []


def test_완결성_emits_비트에_간선이_없으면_잡는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="완결성", order=["a"],
        stages={"a": 가짜단계("a", emits=P.OK | P.SKIP)},
        edges=P.Edges({("*", P.OK): P.NEXT}))          # SKIP 규칙이 없다
    불평 = P.simulate(g, ctx)
    assert any("완결성" in c and "SKIP" in c for c in 불평), 불평


def test_매달림_없는_단계를_가리키면_잡는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.StageDagGraph(
        name="매달림", order=["a"], stages={"a": 가짜단계("a")},
        edges=P.Edges({("a", P.OK): "없는단계", ("*", P.FAIL): P.HALT}))
    assert any("매달림" in c for c in P.simulate(g, ctx))


def test_순환_뒤로_가는_간선을_잡는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    stages: dict[str, P.Stage[P.RunContext]] = {"a": 가짜단계("a"), "b": 가짜단계("b")}
    g = P.StageDagGraph(
        name="순환", order=["a", "b"], stages=stages,
        edges=P.Edges({("b", P.FAIL): "a", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("순환" in c for c in P.simulate(g, ctx))


def test_도달성_아무도_가지_않는_단계를_잡는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    stages: dict[str, P.Stage[P.RunContext]] = {n: 가짜단계(n) for n in ["a", "b", "c"]}
    g = P.StageDagGraph(
        name="고아", order=["a", "b", "c"], stages=stages,
        edges=P.Edges({("a", P.OK): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("도달성" in c and "b" in c for c in P.simulate(g, ctx))


def test_산출물_어떤_경로에서만_없는_것을_잡는다(tmp_path: Path):
    """`a` 가 FAIL 로 `c` 에 떨어지면 `b` 가 쓸 파일이 없다. 한 줄 흐름이면 안 보인다."""
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    계획 = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.json"))
    stages: dict[str, P.Stage[P.RunContext]] = {
        "a": 가짜단계("a", writes=[계획]),
        "b": 가짜단계("b"),
        "c": 가짜단계("c", reads=[계획])}
    g = P.StageDagGraph(
        name="사슬", order=["a", "b", "c"], stages=stages,
        edges=P.Edges({("a", P.FAIL): "c", ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    assert any("산출물" in c and "계획" in c for c in P.simulate(g, ctx))


def test_산출물_이미_있는_것은_given_으로_통과한다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    계획 = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.json"))
    g = P.StageDagGraph(
        name="given", order=["c"], stages={"c": 가짜단계("c", reads=[계획])},
        edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), given=[계획])
    assert P.simulate(g, ctx) == []


def test_팩토리는_어긋나면_단계를_하나도_돌리지_않고_죽는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    돌_단계 = 가짜단계("a", emits=P.OK | P.SKIP)
    with pytest.raises(P.GraphError) as e:
        P.build_graph("망가짐", ["a"], {"a": 돌_단계},
                      P.Edges({("*", P.OK): P.NEXT}), [], ctx)
    assert 돌_단계.돈횟수 == 0
    assert "완결성" in str(e.value)


def test_팩토리는_멀쩡하면_그래프를_낸다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = P.build_graph("멀쩡", ["a"], {"a": 가짜단계("a")},
                      P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}), [], ctx)
    assert g.first == "a"


def test_드라이버는_전이표를_따라_끝까지_돈다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = 삼단_그래프()
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert [r["stage"] for r in rows] == ["a", "b", "c"]


def test_드라이버는_FAIL_에서_멈춘다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    g = 삼단_그래프({"b": P.FAIL})
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert [r["stage"] for r in rows] == ["a", "b"]
    assert cast_가짜(g.stages["c"]).돈횟수 == 0


def test_드라이버는_읽을_것이_없으면_단계를_돌리지_않는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path), model="opus")
    art = P.Artifact[P.RunContext]("계획", lambda c: os.path.join(c.root, "plan.md"))
    st = 가짜단계("a", reads=[art])
    g = P.StageDagGraph(name="빠짐", order=["a"], stages={"a": st},
                        edges=P.Edges({("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT}))
    rows = P.Pipeline[P.RunContext]().run(g, ctx)
    assert st.돈횟수 == 0
    assert rows[0]["ok"] is False
    assert "계획" in rows[0]["why"]


def test_드라이버는_재정의할_수_있다(tmp_path: Path):
    """D6 — 사용자 판정. `run` 은 닫히지 않는다."""
    class 덧붙이는드라이버(P.Pipeline[P.RunContext]):
        def run(self, graph: P.StageDagGraph[P.RunContext],
                ctx: P.RunContext) -> list[M.StageRow]:
            rows = super().run(graph, ctx)
            rows.append({"stage": "덧붙임", "seconds": 0.0,
                         "usage": M.normalize_usage(None), "ok": True, "why": ""})
            return rows

    ctx = P.RunContext(root=str(tmp_path), model="opus")
    rows = 덧붙이는드라이버().run(삼단_그래프(), ctx)
    assert [r["stage"] for r in rows] == ["a", "b", "c", "덧붙임"]


class 참말단계(P.MachineStage[P.RunContext]):
    name = "참말"

    def argv(self, ctx: P.RunContext) -> list[str]:
        return [sys.executable, "-c", "pass"]

    def cwd(self, ctx: P.RunContext) -> str:
        return ctx.root


class 거짓말단계(참말단계):
    name = "거짓말"

    def argv(self, ctx: P.RunContext) -> list[str]:
        return [sys.executable, "-c", "raise SystemExit(3)"]


def test_기계_단계는_성공하면_OK_한_행이다(tmp_path: Path):
    out = 참말단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.OK
    assert len(out.rows) == 1
    assert out.rows[0]["stage"] == "참말"
    assert out.rows[0]["usage"]["total"] == 0


def test_기계_단계는_종료코드를_사유로_적는다(tmp_path: Path):
    out = 거짓말단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.FAIL
    assert "종료 코드 3" in out.why


def test_기계_단계는_작업_폴더가_없으면_돌지_않는다(tmp_path: Path):
    ctx = P.RunContext(root=str(tmp_path / "없는곳"), model="opus")
    out = 참말단계().perform(ctx)
    assert out.kind == P.FAIL
    assert "작업 디렉토리가 없다" in out.why


class 한번부르는단계(P.LlmStage[P.RunContext]):
    name = "한번"

    def prompt(self, ctx: P.RunContext) -> str:
        return "무엇을 하라"

    def repo(self, ctx: P.RunContext) -> str:
        return ctx.root


class 두층부르는단계(한번부르는단계):
    name = "두층"

    def rounds(self, ctx: P.RunContext) -> int:
        return 2

    def jobs(self, ctx: P.RunContext, rnd: int) -> list[tuple[str, str]]:
        return [("L%d-B0" % rnd, "p"), ("L%d-B1" % rnd, "p")]


def 가짜층(결과: P.AgentResult | None, rc: int = 0):
    def _fake(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]],
              concurrency: int = 8, timeout: float | None = None) -> list[P.JobResult]:
        return [(label, 1.0, rc, 결과) for label, _ in jobs]
    return _fake


def test_LLM_단계는_기본으로_자기_이름의_세션_하나다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(P, "run_layer", 가짜층({"total_cost_usd": 0.5}))
    out = 한번부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.OK
    assert [r["stage"] for r in out.rows] == ["한번"]
    assert out.rows[0]["usage"]["cost_usd"] == 0.5


def test_LLM_단계는_기본_LLM_Model이_ctx_의_것이다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    본것: list[str] = []

    def _spy(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]],
             concurrency: int = 8, timeout: float | None = None) -> list[P.JobResult]:
        본것.append(model)
        return [(label, 1.0, 0, {}) for label, _ in jobs]

    monkeypatch.setattr(P, "run_layer", _spy)
    한번부르는단계().perform(P.RunContext(root=str(tmp_path), model="haiku"))
    assert 본것 == ["haiku"]


def test_LLM_단계는_층마다_세션마다_행을_낸다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(P, "run_layer", 가짜층({}))
    out = 두층부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert [r["stage"] for r in out.rows] == ["L0-B0", "L0-B1", "L1-B0", "L1-B1"]


def test_LLM_단계는_층이_실패하면_다음_층을_돌지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(P, "run_layer", 가짜층(None, rc=1))
    out = 두층부르는단계().perform(P.RunContext(root=str(tmp_path), model="opus"))
    assert out.kind == P.FAIL
    assert [r["stage"] for r in out.rows] == ["L0-B0", "L0-B1"]


def test_prompt_resource_는_절_없는_파일을_통째로_읽는다(tmp_path: Path):
    (tmp_path / "hello.md").write_text("\n안녕 {{who}}\n\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("hello",)

    assert S.load_prompt("hello", who="세계") == "안녕 세계\n"


def test_prompt_resource_는_절을_이름으로_꺼낸다(tmp_path: Path):
    (tmp_path / "s.md").write_text(
        "<!-- section: a -->\n가 {{x}}\n\n<!-- section: b -->\n나\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("s#a", "s#b")

    assert S.load_prompt("s#a", x="1") == "가 1\n"
    assert S.load_prompt("s#b") == "나\n"


def test_prompt_resource_는_선언_밖의_이름을_거부한다(tmp_path: Path):
    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ()

    with pytest.raises(KeyError, match="hello"):
        S.load_prompt("hello")


def test_sections_는_첫_표식_앞의_글과_겹친_절을_거부한다():
    with pytest.raises(ValueError, match="앞에"):
        P.PromptResource.sections("머리\n<!-- section: a -->\n가\n")
    with pytest.raises(ValueError, match="두 번"):
        P.PromptResource.sections("<!-- section: a -->\n가\n<!-- section: a -->\n나\n")


def test_llm_stage_는_prompt_resource_다():
    assert issubclass(P.LlmStage, P.PromptResource)


@pytest.mark.parametrize("text", [
    "<!-- section: a -->\n가\n<!-- section: B -->\n나\n",
    "<!-- section: a -->\n가\n<!-- section: b_c -->\n나\n",
    "<!-- section: a -->\n가\n <!-- section: b -->\n나\n",
    "<!-- section: a -->\n가\n<!-- section: b --> \n나\n",
    "<!-- section: a -->\n가\n<!-- section: b -->",
    "<!-- section: a -->\n가\n<!--section: b-->\n나\n",
], ids=["upper", "underscore", "leading-space", "trailing-space", "no-final-newline", "no-space"])
def test_sections_는_꼴이_틀린_표식을_거부한다(text: str):
    with pytest.raises(ValueError, match="꼴이 틀렸다"):
        P.PromptResource.sections(text)


def test_sections_는_본문_속_낱말_section_을_통과시킨다():
    assert P.PromptResource.sections("<!-- section: a -->\n이 section 은 본문이다\n") == {"a": "이 section 은 본문이다\n"}


def test_load_prompt_는_name_과_cls_자리도_채운다(tmp_path: Path):
    (tmp_path / "f.md").write_text("{{name}} {{cls}}\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("f",)

    assert S.load_prompt("f", name="n", cls="c") == "n c\n"


def test_load_prompt_는_절대_경로가_아닌_prompt_dir_을_거부한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "hello.md").write_text("안녕\n", encoding="utf-8")
    (tmp_path / "hello.md").write_text("안녕\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Relative(P.PromptResource):
        prompt_dir = "prompts"
        prompt_names = ("hello",)

    class Undeclared(P.PromptResource):
        prompt_names = ("hello",)

    with pytest.raises(ValueError, match="절대 경로"):
        Relative.load_prompt("hello")
    with pytest.raises(ValueError, match="절대 경로"):
        Undeclared.load_prompt("hello")


def test_load_prompt_는_없는_절을_KeyError_로_낸다(tmp_path: Path):
    (tmp_path / "s.md").write_text("<!-- section: a -->\n가\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("s#z",)

    with pytest.raises(KeyError, match="절 'z'"):
        S.load_prompt("s#z")


def test_load_prompt_는_자리_어긋남을_TemplateError_로_낸다(tmp_path: Path):
    (tmp_path / "hello.md").write_text("안녕 {{who}}\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("hello",)

    with pytest.raises(TemplateError):
        S.load_prompt("hello")
