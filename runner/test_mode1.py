"""`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON."""
import json
import os
import sys
import time
from pathlib import Path
from typing import cast

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
import measure as M  # noqa: E402
import pipeline as P  # noqa: E402
import survey_plan  # noqa: E402
from mode1 import context as X  # noqa: E402
from mode1 import diff as D  # noqa: E402
from mode1 import edges as E  # noqa: E402
from mode1 import graph as G  # noqa: E402
from mode1 import lang as LG  # noqa: E402
from mode1 import machine_stage as MC  # noqa: E402
from mode1 import measured as MS  # noqa: E402
from mode1 import resume as Z  # noqa: E402
from mode1 import scan as SC  # noqa: E402
from mode1 import survey as SV  # noqa: E402
from mode1 import terms as T  # noqa: E402
from mode1 import wiki as W  # noqa: E402


def _ctx(tmp_path: Path) -> X.Mode1Context:
    return X.Mode1Context(root="/r", model="m", repo=str(tmp_path))


# ── 1. 문맥과 산출물 ────────────────────────────────────────────────────


def test_문맥의_기본값은_전량이_아니다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert c.cold is False and c.targets is None and c.plan is None


def test_산출물은_저장소_아래_자리를_가리킨다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert X.CODEGRAPH.locate(c).endswith(os.path.join("out", "codegraph-raw", "codegraph.json"))
    assert X.CHANGES.locate(c).endswith("changes.json")
    assert X.BATCHES.locate(c).endswith("batches.json")


def test_코드지도_검사는_최상위_열쇠만_본다(tmp_path: Path):
    p = tmp_path / "cg.json"
    p.write_text('{"nodes": [{"file": null}], "edges": [], "language": "py"}')   # 기계축 실물처럼 null 이 있어도 통과
    assert P.check_file(str(p), X.CodeGraphDoc) == []
    p.write_text('{"nodes": "x"}')
    assert P.check_file(str(p), X.CodeGraphDoc) != []
    p.write_text('[]')
    assert P.check_file(str(p), X.CodeGraphDoc) != []


def test_층계획_검사는_실제_형으로_본다(tmp_path: Path):
    p = tmp_path / "b.json"
    p.write_text(json.dumps(_empty_plan()))
    assert X.BATCHES.schema is not None and P.check_file(str(p), X.BATCHES.schema) == []
    p.write_text('{"layers": {}}')
    assert P.check_file(str(p), X.BATCHES.schema) != []


# ── 2. 형 · 읽기 레코드 자리 · 바닥 ──────────────────────────────────────


def test_읽기_레코드_자리는_자기호스팅만_다르다(tmp_path: Path):
    self_hosted = X.Mode1Context(root=str(tmp_path), model="m", repo=str(tmp_path))
    assert X.READING.locate(self_hosted) == os.path.join(str(tmp_path), "machine", "terms-reading.json")
    other = _ctx(tmp_path)   # root="/r" 는 저장소가 아니다
    assert X.READING.locate(other) == os.path.join(str(tmp_path), "docs", "codegraph", "terms-reading.json")


def test_측정_행은_단계_이름과_토큰_0_을_담는다():
    class T(MS.Measured):
        name = "t"
    r = T().row(time.monotonic(), True, "x")
    assert r["stage"] == "t" and r["ok"] is True and r["why"] == "x" and r["usage"]["total"] == 0


def test_기계_단계는_저장소를_cwd_로_한다(tmp_path: Path):
    class T(MC.Mode1Machine):
        name = "t"

        def argv(self, ctx: X.Mode1Context) -> list[str]:
            return ["true"]
    assert T().cwd(_ctx(tmp_path)) == str(tmp_path)
    assert MC.Mode1Machine.wiki_argv("py", "/root", "prep.py", "/repo") == ["py", "/root/runner/wiki/prep.py", "/repo"]
    assert os.path.isdir(os.path.join(X.ROOT, "runner", "mode1"))   # 도구 뿌리는 셋 위다


# ── 3. changes.json 의 꼴 ────────────────────────────────────────────────


def _verdicts() -> dict[str, list[str]]:
    return {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": ["gone.py"]}


def test_diff_는_넷_갈래와_범위를_담는다(tmp_path: Path):
    p = str(tmp_path / "changes.json")
    D.write_diff(p, _verdicts(), targets=["b.py"], hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None
    assert got["targets"] == ["b.py"] and got["verdicts"]["삭제됨"] == ["gone.py"]


def test_전량이면_targets_가_None_이다(tmp_path: Path):
    p = str(tmp_path / "d.json")
    D.write_diff(p, _verdicts(), targets=None, hops=1, tracked=2)
    got = D.read_diff(p)
    assert got is not None and got["targets"] is None


def test_diff_검사는_형으로_보고_갈래_넷은_쓰는_쪽이_채운다(tmp_path: Path):
    assert X.CHANGES.schema is D.WarmupDiff
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}))
    assert P.check_file(str(p), D.WarmupDiff) == []
    p.write_text(json.dumps({"verdicts": {"유효": "x"}, "targets": None, "hops": 1, "tracked": 0}))
    assert P.check_file(str(p), D.WarmupDiff) != []          # 값이 배열이 아니다
    p.write_text(json.dumps({"verdicts": {}, "targets": "x", "hops": 1, "tracked": 0}))
    assert P.check_file(str(p), D.WarmupDiff) != []          # targets 가 null 도 배열도 아니다
    assert D.read_diff(str(tmp_path / "없음.json")) is None
    got = D.write_diff(str(p), {"재읽기": ["b.py"]}, None, 1, 1)   # 갈래를 덜 줘도 넷이 채워진다
    assert set(got["verdicts"]) == set(D.BUCKETS)


def test_전체_파일_집합은_삭제됨을_뺀_셋의_합이다():
    d: D.WarmupDiff = {"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}
    assert D.all_files(d) == {"a.py", "b.py"}


# ── 4. prep 이 diff 로 재수집 여부를 정한다 ─────────────────────────────


def test_prep_은_diff_에_바뀐_것이_있으면_다시_수집한다():
    sys.path.insert(0, ROOT)
    from runner.wiki import prep
    fresh = {"유효": ["a.py"], "재읽기": [], "위치만": [], "삭제됨": []}
    stale = {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []}
    assert prep.needs_collect(has_codegraph=True, verdicts=fresh) is False
    assert prep.needs_collect(has_codegraph=True, verdicts=stale) is True
    assert prep.needs_collect(has_codegraph=False, verdicts=fresh) is True
    assert prep.needs_collect(has_codegraph=True, verdicts=None) is False
    assert prep.needs_collect(has_codegraph=True, verdicts=None, force=True) is True
    assert prep.prepPlan("griffe+pycalls", True, False, False, False, verdicts=stale)["steps"][0] == "griffe"
    assert prep.prepPlan("griffe+pycalls", True, False, False, False, force=True)["steps"][0] == "griffe"
    assert prep.prepPlan("griffe+pycalls", True, False, False, False)["steps"] == ["facts", "render-modules"]


# ── 5. 기계 단계와 층 계획 ──────────────────────────────────────────────


def _plan_with(files: list[str]) -> survey_plan.SurveyPlan:
    """배치 하나짜리 계획 — 실제 `SurveyPlan` 꼴이라 msgspec 검증을 통과한다.
    ⚠ 이것으로 `annotate-symbols` 를 돌리면 세션이 실제로 뜬다 — 대조 시험에만 쓴다."""
    syms: list[survey_plan.PlanSymbol] = [
        {"id": f + ".S", "name": f + ".S", "file": f, "line": 1, "kind": "function", "in_cycle": False, "depends_on": []}
        for f in files]
    return {"target": 8, "layers": [{"level": 0, "symbol_count": len(syms), "file_count": len(files),
            "batches": [{"id": "L0-B00", "files": files, "symbols": syms}]}],
            "totals": {"symbols": len(syms), "edges": 0, "levels": 1, "cyclic_symbols": 0}}


def test_기계_단계_다섯은_저장소를_cwd_로_한다(tmp_path: Path):
    c = _ctx(tmp_path)
    for st in (G.CollectGraphStage(), T.VerifyTermsStage(), W.PublishWikiStage(), W.VerifyWikiStage()):
        assert st.cwd(c) == c.repo


def test_prep_은_전량이면_force_증분이면_diff_를_넘긴다(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True
    assert "--force" in G.CollectGraphStage().argv(c) and "--diff" not in G.CollectGraphStage().argv(c)
    c.cold = False
    assert "--diff" in G.CollectGraphStage().argv(c) and "--force" not in G.CollectGraphStage().argv(c)


def test_terms_argv_는_정적_지도를_위치_인자로_준다():
    argv = T.VerifyTermsStage.terms_argv("py", "/root", "/repo", "/repo/out/codegraph-raw/codegraph.json", None)
    assert argv[2] == "/repo/out/codegraph-raw/codegraph.json" and "--reading" not in argv


def test_schedule_batches_는_diff_의_targets_로_좁힌다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"nodes": [], "edges": []}')
    seen: dict[str, object] = {}

    def fake_plan(cg: object, target: int = 8, only_files: list[str] | None = None) -> survey_plan.SurveyPlan:
        seen["only"] = only_files
        return _plan_with([])
    monkeypatch.setattr(G.survey_plan, "plan", fake_plan)
    c.targets = ["x.py"]
    out = G.ScheduleBatchesStage().perform(c)
    assert out.kind == P.OK and seen["only"] == ["x.py"] and c.plan is not None
    assert (raw / "batches.json").exists()


def test_계획_요약은_층과_합계를_낸다():
    plan = _plan_with(["a.py"])
    lines = G.ScheduleBatchesStage.plan_summary(plan)
    assert lines[0].startswith("  층0") and "합계" in lines[-1]


# ── 6. 언어 제안과 결정 ──────────────────────────────────────────────────


def test_lang_hint_는_싼_모형을_고정한다(tmp_path: Path):
    assert LG.LangHintStage().model(_ctx(tmp_path)) == LG.LANG_SELECT_MODEL


def test_lang_hint_는_낱말_하나만_받아들인다(tmp_path: Path):
    c = _ctx(tmp_path)
    st = LG.LangHintStage()
    out = st.harvest(c, [("lang-hint", 1.0, 0, {"result": " `Cpp`. "})], 0)
    assert c.proposed == "cpp" and out.kind == P.OK
    out = st.harvest(c, [("lang-hint", 1.0, 0, {"result": "rust"})], 0)
    assert c.proposed is None and out.kind == P.SKIP


def test_lang_hint_는_실패해도_SKIP_이지_FAIL_이_아니다(tmp_path: Path):
    out = LG.LangHintStage().harvest(_ctx(tmp_path), [("lang-hint", 1.0, 1, None)], 0)
    assert out.kind == P.SKIP and all(r["ok"] for r in out.rows)


def test_lang_hint_는_문서가_없으면_세션을_띄우지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    st = LG.LangHintStage()
    def no_docs(ctx: X.Mode1Context) -> str:
        return "   "
    monkeypatch.setattr(st, "docs", no_docs)
    assert st.jobs(c, 0) == []
    out = st.harvest(c, [], 0)
    assert out.kind == P.SKIP and out.rows[0].get("skipped") is True


def test_lang_hint_프롬프트는_넷_중_하나를_낱말로_답하라고_한다():
    p = LG.LangHintStage.hint_prompt("# README\n이 저장소는 …")
    assert "cpp" in p and "unknown" in p and p.endswith("이 저장소는 …")


def test_lang_decide_는_제안이_있으면_넘긴다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert "--propose" not in LG.LangDecideStage().argv(c)
    c.proposed = "py"
    assert LG.LangDecideStage().argv(c)[-2:] == ["--propose", "py"]
    assert LG.LangDecideStage().writes(c) == [X.LANG_SELECT]


# ── 7. 옛 지문과 지금 소스의 대조 ────────────────────────────────────────


def _no_change() -> dict[str, list[str]]:
    return {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}


def test_lang_for_는_lang_select_을_먼저_보고_코드_지도로_폴백한다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    assert SC.SnapshotScan.lang_for(c) is None
    (raw / "codegraph.json").write_text('{"language": "csharp", "nodes": [], "edges": []}')
    assert SC.SnapshotScan.lang_for(c) == "cs"
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "griffe+pycalls"}')
    assert SC.SnapshotScan.lang_for(c) == "py"


def test_씨앗은_재읽기와_위치만의_합집합이다():
    v = {"유효": ["a.py"], "재읽기": ["c.py"], "위치만": ["b.py"], "삭제됨": ["z.py"]}
    assert SC.DetectChangesStage.changed_seed(v) == ["b.py", "c.py"]


def test_detect_changes_는_diff_파일을_쓴다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"language": "py", "nodes": [], "edges": []}')
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "griffe+pycalls"}')

    def tracked(repo: str, lang: str, includes: list[str]) -> list[str]:
        return ["a.py"]

    def scan(repo: str, lang: str, includes: list[str], n: int) -> tuple[dict[str, object], None]:
        return {}, None

    def status(cache: str, repo: str, files: list[str], decls: object) -> tuple[dict[str, list[str]], dict[str, object]]:
        return {"유효": [], "재읽기": ["a.py"], "위치만": [], "삭제됨": []}, {}
    monkeypatch.setattr(SC.declmap, "tracked_files", tracked)
    monkeypatch.setattr(SC.declmap, "scan", scan)
    monkeypatch.setattr(SC.warmup, "status", status)
    out = SC.DetectChangesStage().perform(c)
    assert out.kind == P.OK
    got = D.read_diff(str(raw / "changes.json"))
    assert got is not None and got["targets"] == ["a.py"] and c.targets == ["a.py"]
    assert c.warmup_cache == str(raw / "snapshot.json")


def test_detect_changes_는_언어를_모르면_전량_diff_를_쓴다(tmp_path: Path):
    c = _ctx(tmp_path)
    out = SC.DetectChangesStage().perform(c)
    got = D.read_diff(X.CHANGES.locate(c))
    assert out.kind == P.OK and got is not None and got["targets"] is None and c.targets is None


def test_snapshot_sources_는_조사가_실패하면_쓰지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path); c.entries = {}; c.warmup_cache = str(tmp_path / "w.json"); c.cold = False
    wrote: list[str] = []

    def save(p: str, e: dict[str, object]) -> dict[str, object]:
        wrote.append(p)
        return e
    monkeypatch.setattr(SC.warmup, "save", save)
    c.survey_ok = False
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == []
    c.survey_ok = True
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == [c.warmup_cache]


def test_snapshot_sources_는_전량이면_직접_훑어_찍는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    c = _ctx(tmp_path); c.cold = True; c.survey_ok = True

    def scanned(ctx: X.Mode1Context) -> tuple[dict[str, list[str]], dict[str, object], str]:
        return _no_change(), {"a.py": {}}, str(tmp_path / "w.json")
    monkeypatch.setattr(SC.SnapshotSourcesStage, "scan_snapshot", staticmethod(scanned))
    wrote: list[str] = []

    def save(p: str, e: dict[str, object]) -> dict[str, object]:
        wrote.append(p)
        return e
    monkeypatch.setattr(SC.warmup, "save", save)
    SC.SnapshotSourcesStage().perform(c)
    assert wrote == [str(tmp_path / "w.json")]


def test_지문은_옛_이름도_읽고_새_이름으로_쓴다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    assert X.snapshot_path(c).endswith("snapshot.json")
    (raw / "warmup.json").write_text("{}")
    assert X.snapshot_path(c).endswith("warmup.json")
    (raw / "snapshot.json").write_text("{}")
    assert X.snapshot_path(c).endswith("snapshot.json")


# ── 8. 전수조사 — 계획과 diff 의 대조 · 샤드 병합 · 층 돌기 ─────────────


def _empty_plan() -> survey_plan.SurveyPlan:
    """층 0개 계획. `annotate-symbols` 가 세션 없이 OK 로 끝나야 하는 시험에 쓴다."""
    return {"target": 8, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}


def _diff(targets: list[str] | None) -> D.WarmupDiff:
    return {"verdicts": {"유효": ["a.py"], "재읽기": ["b.py"], "위치만": [], "삭제됨": []},
            "targets": targets, "hops": 1, "tracked": 2}


def test_계획이_diff_보다_넓으면_잡는다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["a.py", "b.py"]), _diff(["b.py"])) != []


def test_계획이_diff_보다_좁으면_잡는다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["b.py"]), _diff(None)) != []


def test_계획과_diff_가_맞으면_통과한다():
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["b.py"]), _diff(["b.py"])) == []
    assert SV.AnnotateSymbolsStage.compare_plan(_plan_with(["a.py", "b.py"]), _diff(None)) == []


def test_annotate_symbols_는_어긋난_계획을_돌리지_않는다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _diff(["b.py"])["verdicts"], ["b.py"], 1, 2)
    (raw / "batches.json").write_text(json.dumps(_plan_with(["a.py", "b.py"])))
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.FAIL and "diff" in out.why


def test_annotate_symbols_는_바뀐_것이_없고_레코드가_있으면_SKIP(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _no_change(), [], 1, 0)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    reading = Path(X.READING.locate(c)); reading.parent.mkdir(parents=True)
    reading.write_text("{}")
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.SKIP and c.survey_ok is True


def test_annotate_symbols_는_레코드가_없으면_바뀐_것이_없어도_돈다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    D.write_diff(str(raw / "changes.json"), _no_change(), [], 1, 0)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    out = SV.AnnotateSymbolsStage().perform(c)     # 층이 0개라 세션 없이 OK 로 끝난다
    assert out.kind == P.OK and c.survey_ok is True


def test_샤드를_합치고_충돌은_전원을_개명한다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B00.json").write_text(json.dumps({"main": {"where": "app/gui.py:10"}}), encoding="utf-8")
    (d / "L0-B01.json").write_text(json.dumps({"main": {"where": "app/cli.py:3"}}), encoding="utf-8")
    got = SV.AnnotateSymbolsStage.merge_shards(str(d), {})
    assert sorted(got) == ["cli.main", "gui.main"]


def test_같은_파일의_같은_키는_개명_없이_갈아_끼운다(tmp_path: Path):
    """증분 조사. 다시 읽은 카드는 옛 카드의 자리를 그대로 잇는다 — 코드 지도가 그 이름을 안다."""
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B00.json").write_text(json.dumps({"m.run": {"where": "m.py:51", "means": "새"}}), encoding="utf-8")
    got = SV.AnnotateSymbolsStage.merge_shards(str(d), {"m.run": {"where": "m.py:47", "means": "옛"}})
    assert got == {"m.run": {"where": "m.py:51", "means": "새"}}


def test_다른_파일의_같은_키는_여전히_양쪽_다_개명한다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B00.json").write_text(json.dumps({"main": {"where": "core/net.py:20"}}), encoding="utf-8")
    got = SV.AnnotateSymbolsStage.merge_shards(str(d), {"main": {"where": "app/gui.py:10"}})
    assert sorted(got) == ["gui.main", "net.main"]


def test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다():
    b: survey_plan.PlanBatch = {"id": "L1-B00", "files": ["a.py"], "symbols": [
        {"id": "f", "name": "f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False, "depends_on": []}]}
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", ["a.py"], 3)
    assert "## 범위" in p and "_shards/L1-B00.json" in p
    assert "## 범위" not in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")


# ── 9. 위키 목차와 장 ───────────────────────────────────────────────────


def test_outline_wiki_는_목차_파일을_쓴다고_선언하고_있으면_세션_없이_OK(tmp_path: Path):
    c = _ctx(tmp_path)
    assert W.OutlineWikiStage().writes(c) == [X.OUTLINE]
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "outline.json").write_text('{"pages": []}')
    out = W.OutlineWikiStage().perform(c)          # 이미 있으면 세션 없이 OK — SKIP 이 아니다
    assert out.kind == P.OK and out.rows[0].get("skipped") is True


def test_목차_프롬프트는_새_이름의_파일을_말한다():
    p = W.OutlineWikiStage.wiki_catalogue_prompt("/repo", "/root")
    assert "outline.json" in p and "batches.json" in p
    assert "wiki-plan.json" not in p and "survey-plan.json" not in p


def test_write_wiki_는_이미_쓴_장을_건너뛴다(tmp_path: Path):
    c = _ctx(tmp_path)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "outline.json").write_text(json.dumps({"pages": [{"file": "a.md", "symbols": []}, {"file": "b.md", "symbols": []}]}))
    (tmp_path / "docs" / "wiki").mkdir(parents=True)
    (tmp_path / "docs" / "wiki" / "a.md").write_text("x")
    c.plan = {"target": 8, "layers": [], "totals": {"symbols": 0, "edges": 0, "levels": 0, "cyclic_symbols": 0}}
    st = W.WriteWikiStage()
    st.prepare(c)
    assert W.WriteWikiStage().reads(c) == [X.OUTLINE, X.BATCHES]
    assert W.WriteWikiStage().writes(c) == [X.WIKI_DIR]
    assert [j[0] for j in st.jobs(c, 0)] == ["b.md"]


def test_페이지_층은_인용한_심볼의_최대():
    pages: list[X.WikiPage] = [{"file": "i.md", "symbols": []}, {"file": "p.md", "symbols": ["a", "b", "없음"]}]
    assert W.WriteWikiStage.page_layers(pages, {"a": 0, "b": 2}) == {"i.md": 0, "p.md": 2}


# ── 10. 흐름 — 순서 · 별명 · 전이표 · 팩토리 ────────────────────────────


def test_증분은_열둘_전량은_열하나():
    assert len(E.ORDER) == 12
    assert "detect-changes" not in E.plan_stages(None, None, cold=True)
    assert "detect-changes" in E.plan_stages(None, None, cold=False)
    assert "snapshot-sources" in E.plan_stages(None, None, cold=True)


def test_순서의_불변식_셋():
    i = E.ORDER.index
    assert i("detect-changes") < i("collect-graph") < i("schedule-batches") < i("annotate-symbols")
    assert i("annotate-symbols") + 1 == i("snapshot-sources") < i("verify-terms")   # 지문은 조사 바로 뒤
    assert i("verify-terms") < i("outline-wiki") < i("write-wiki") < i("publish-wiki") < i("verify-wiki")


def test_별명은_쪼갠_단계로_펴진다():
    assert E.expand(["lang-select", "publish-wiki"]) == ["lang-hint", "lang-decide", "publish-wiki"]
    assert E.expand(["wiki"]) == ["outline-wiki", "write-wiki"]
    assert E.expand(["warmup", "survey"]) == ["detect-changes", "annotate-symbols"]


def test_모르는_단계는_거부한다():
    with pytest.raises(ValueError):
        E.plan_stages(["없는-단계"], None)


def test_전량_그래프는_이름이_다르고_표는_같다(tmp_path: Path):
    cold = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    warm = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    assert E.build_mode1_graph(cold, None, None).name == "mode1-cold"
    assert E.build_mode1_graph(warm, None, None).name == "mode1-warm"
    assert E.EDGES.dest("annotate-symbols", P.SKIP) == P.NEXT


def test_전량에서는_annotate_symbols_가_SKIP_을_내지_않는다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_empty_plan()))
    reading = Path(X.READING.locate(c)); reading.parent.mkdir(parents=True); reading.write_text("{}")
    assert SV.AnnotateSymbolsStage().perform(c).kind == P.OK      # 층이 0개라 세션 없이 OK. 전량은 diff 를 안 본다


def test_증분_그래프는_diff_를_읽는_단계가_셋이다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=False)
    g = E.build_mode1_graph(c, only=None, skip=None)
    readers = [n for n in g.order if X.CHANGES in g.stages[n].reads(c)]
    assert set(readers) == {"collect-graph", "schedule-batches", "annotate-symbols"}


def test_팩토리는_어긋난_그래프를_거부한다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path))
    with pytest.raises(P.GraphError):
        E.build_mode1_graph(c, only=["annotate-symbols"], skip=None)   # 계획도 diff 도 없다


def test_재개는_그_앞을_잘라_낸다(tmp_path: Path):
    c = X.Mode1Context(root=ROOT, model="m", repo=str(tmp_path), cold=True)
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text('{"nodes": [], "edges": []}')
    (raw / "lang-select.json").write_text('{"language": "py", "collector": "x"}')
    g = E.build_mode1_graph(c, None, None, start_at="schedule-batches")
    assert g.order[0] == "schedule-batches"


# ── 11. 재개 JSON ───────────────────────────────────────────────────────


def test_재개_문서는_어디서_왜_멈췄는지를_담는다(tmp_path: Path):
    rows: list[M.StageRow] = [
        {"stage": "collect-graph", "seconds": 1.0, "usage": M.normalize_usage(None), "ok": True, "why": ""},
        {"stage": "annotate-symbols/L0-B00", "seconds": 2.0, "usage": M.normalize_usage(None), "ok": False, "why": "터짐"},
    ]
    p = str(tmp_path / "resume.json")
    Z.write_resume(p, graph="mode1-warm", rows=rows, order=["collect-graph", "annotate-symbols", "verify-terms"])
    got = Z.read_resume(p)
    assert got is not None
    assert got["failed_at"] == "annotate-symbols" and got["done"] == ["collect-graph"] and got["graph"] == "mode1-warm"


def test_실패가_없으면_재개_문서를_쓰지_않는다(tmp_path: Path):
    p = str(tmp_path / "r.json")
    assert Z.write_resume(p, graph="mode1-warm", rows=[], order=["collect-graph"]) is None
    assert not os.path.exists(p)


def test_다른_그래프의_재개_문서는_거부한다(tmp_path: Path):
    p = str(tmp_path / "r.json")
    rows: list[M.StageRow] = [{"stage": "collect-graph", "seconds": 0.0, "usage": M.normalize_usage(None), "ok": False, "why": "x"}]
    Z.write_resume(p, graph="mode1-cold", rows=rows, order=["collect-graph"])
    assert Z.start_stage(Z.read_resume(p), for_graph="mode1-warm") is None
    assert Z.start_stage(Z.read_resume(p), for_graph="mode1-cold") == "collect-graph"


# ── 샤드 검문 — 스키마 파일 · 기계 파서 · 전량 순회 ───────────────────────

def _good_record() -> dict[str, object]:
    return {"kind": "function", "module": "m", "where": "m.py:1", "means": "뜻", "does": "함",
            "uses": [{"to": "g", "kind": "dependency", "label": "calls", "where": "m.py:2"}],
            "confidence": "HIGH", "source": "reading"}


def _one_batch_plan(bid: str = "L0-B00") -> survey_plan.SurveyPlan:
    return {"target": 8, "totals": {"symbols": 1, "edges": 0, "levels": 1, "cyclic_symbols": 0},
            "layers": [{"level": 0, "symbol_count": 1, "file_count": 1, "batches": [
                {"id": bid, "files": ["m.py"], "symbols": [
                    {"id": "f", "name": "f", "kind": "function", "file": "m.py", "line": 1,
                     "in_cycle": False, "depends_on": []}]}]}]}


def test_샤드_형은_계약의_칸을_전부_요구한다():
    check = SV.AnnotateSymbolsStage.check_shard
    assert check(json.dumps({"f": _good_record()}).encode()) == []
    for gone in ("kind", "module", "means", "uses", "confidence", "source"):
        rec = {k: v for k, v in _good_record().items() if k != gone}
        assert check(json.dumps({"f": rec}).encode()), gone
    rec = _good_record(); del rec["does"]           # does 만 선택이다
    assert check(json.dumps({"f": rec}).encode()) == []


def test_샤드_형은_값의_어휘도_본다():
    check = SV.AnnotateSymbolsStage.check_shard
    for field, wrong in (("kind", "helper"), ("confidence", "SURE"), ("source", "codegraph")):
        rec = _good_record(); rec[field] = wrong
        assert check(json.dumps({"f": rec}).encode()), field
    rec = _good_record(); rec["kind"] = "method"    # 코드 지도가 내는 종류다
    assert check(json.dumps({"f": rec}).encode()) == []
    rec = _good_record(); rec["uses"] = [{"to": "g", "kind": "calls", "label": None, "where": "m.py:2"}]
    assert check(json.dumps({"f": rec}).encode())


def test_깨진_JSON_샤드는_결함_하나로_짚는다():
    got = SV.AnnotateSymbolsStage.check_shard(b'{"f": {"means": "a "b" c"}}', "L1-B30", "/s/L1-B30.json")
    assert len(got) == 1
    f = got[0]
    assert f["kind"] == "malformed" and f["batch"] == "L1-B30" and f["path"] == "/s/L1-B30.json"
    assert f["at"].startswith("byte ") and "malformed" in f["detail"] and f["fix"]


def test_결함은_네_갈래이고_갈래마다_고치는_법이_다르다():
    check = SV.AnnotateSymbolsStage.check_shard
    rec = _good_record(); rec["kind"] = "helper"
    schema = check(json.dumps({"f": rec}).encode())[0]
    assert schema["kind"] == "schema" and "kind" in schema["at"] and "helper" in schema["detail"]
    rec = _good_record(); del rec["where"]
    where = check(json.dumps({"f": rec}).encode())[0]
    assert where["kind"] == "where" and where["at"] == "f"
    fixes = {SV.AnnotateSymbolsStage.FIX[k] for k in ("missing", "malformed", "schema", "where")}
    assert len(fixes) == 4 and schema["fix"] == SV.AnnotateSymbolsStage.FIX["schema"]


def test_module_과_external_만_where_없이_통과한다():
    check = SV.AnnotateSymbolsStage.check_shard
    for kind in ("module", "external"):
        rec = _good_record(); rec["kind"] = kind; del rec["where"]
        assert check(json.dumps({"f": rec}).encode()) == [], kind
    rec = _good_record(); del rec["where"]
    assert [f["kind"] for f in check(json.dumps({"f": rec}).encode())] == ["where"]


def test_샤드_검문은_계획의_배치마다_파일을_찾는다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    plan = _one_batch_plan("L0-B00")
    plan["layers"][0]["batches"].append({"id": "L0-B01", "files": ["n.py"], "symbols": []})
    plan["layers"][0]["batches"].append({"id": "L0-B02", "files": ["o.py"], "symbols": []})
    plan["layers"].append({"level": 1, "symbol_count": None, "kind": "non-node", "note": "", "batches": []})
    (d / "L0-B00.json").write_text(json.dumps({"f": _good_record()}), encoding="utf-8")
    (d / "L0-B01.json").write_text('{"g": {"means": "a "b" c"}}', encoding="utf-8")
    (d / "NONNODE.json").write_text(json.dumps({"m.py": {**_good_record(), "kind": "file"}}), encoding="utf-8")
    bad = SV.AnnotateSymbolsStage.check_shards(str(d), plan)
    assert sorted(bad) == ["L0-B01", "L0-B02"]
    assert bad["L0-B01"][0]["kind"] == "malformed" and bad["L0-B02"][0]["kind"] == "missing"
    assert bad["L0-B01"][0]["path"] == str(d / "L0-B01.json")


def test_틀린_샤드는_격리되어_병합에서_빠지고_다음_실행에서_다시_뜬다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B01.json").write_text('{"g": {"means": "a "b" c"}}', encoding="utf-8")
    moved = SV.AnnotateSymbolsStage.quarantine(str(d), "L0-B01")
    assert not (d / "L0-B01.json").exists() and os.path.exists(moved) and not moved.endswith(".json")
    assert SV.AnnotateSymbolsStage.merge_shards(str(d), {}) == {}
    assert SV.AnnotateSymbolsStage.quarantine(str(d), "L0-B01") == moved   # 없으면 그대로 그 이름


def test_스키마_파일은_읽기_전용이고_다시_쓸_수_있다(tmp_path: Path):
    p = tmp_path / "record-schema.json"
    SV.AnnotateSymbolsStage.write_schema(str(p))
    assert os.stat(p).st_mode & 0o222 == 0
    doc = json.loads(p.read_text(encoding="utf-8"))
    assert doc["examples"] and SV.AnnotateSymbolsStage.check_shard(json.dumps(doc["examples"][0]).encode()) == []
    SV.AnnotateSymbolsStage.write_schema(str(p))                # 두 번째도 죽지 않는다
    assert os.stat(p).st_mode & 0o222 == 0


def test_프롬프트_둘은_스키마_파일을_가리킨다():
    b = _one_batch_plan()["layers"][0]["batches"][0]
    assert "record-schema.json" in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")
    assert "record-schema.json" in SV.AnnotateSymbolsStage.nonnode_prompt("/repo", "/root")


def test_annotate_symbols_는_끝에_샤드_전량을_검문하고_틀리면_FAIL(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_one_batch_plan("L0-B00")))
    shards = raw / "_shards"; shards.mkdir()
    (shards / "L0-B00.json").write_text('{"f": {"means": "a "b" c"}}', encoding="utf-8")   # 샤드가 있어 세션은 안 뜬다
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.FAIL and c.survey_ok is False
    assert not (shards / "L0-B00.json").exists() and (shards / "L0-B00.json.bad").exists()
    assert out.rows[-1]["stage"] == "annotate-symbols/check-shards" and out.rows[-1]["ok"] is False
    assert os.stat(X.RECORD_SCHEMA.locate(c)).st_mode & 0o222 == 0


def test_annotate_symbols_는_샤드가_전부_맞으면_검문_행을_남기고_OK(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_one_batch_plan("L0-B00")))
    shards = raw / "_shards"; shards.mkdir()
    (shards / "L0-B00.json").write_text(json.dumps({"f": _good_record()}), encoding="utf-8")
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.OK and c.survey_ok is True
    assert out.rows[-1]["stage"] == "annotate-symbols/check-shards" and out.rows[-1]["ok"] is True


# ── 오류 인계 — 격리 사유 저장 · 재조사 프롬프트 · 세션 안 자가검사 ────────

def _fault(kind: X.FaultKind = "malformed", at: str = "byte 7014") -> X.ShardFault:
    return {"kind": kind, "batch": "L1-B30", "path": "/s/L1-B30.json", "at": at,
            "detail": "JSON is malformed: expected ',' or '}'", "fix": SV.AnnotateSymbolsStage.FIX[kind]}


def test_격리는_결함을_JSON_으로_옆에_남기고_그대로_읽어_낸다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L1-B30.json").write_text("{", encoding="utf-8")
    SV.AnnotateSymbolsStage.quarantine(str(d), "L1-B30", [_fault()])
    assert SV.AnnotateSymbolsStage.load_faults(str(d), "L1-B30") == [_fault()]
    assert json.loads((d / "L1-B30.json.bad.why").read_text(encoding="utf-8"))[0]["kind"] == "malformed"
    assert SV.AnnotateSymbolsStage.load_faults(str(d), "L1-B31") == []


def test_재조사_프롬프트는_지난_오류를_싣는다(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True; c.plan = _one_batch_plan("L1-B30")
    d = Path(SV.AnnotateSymbolsStage.shard_dir(c)); d.mkdir(parents=True)
    first = SV.AnnotateSymbolsStage().jobs(c, 0)[0][1]
    assert "지난 시도" not in first
    (d / "L1-B30.json.bad").write_text("{", encoding="utf-8")
    SV.AnnotateSymbolsStage.quarantine(str(d), "L1-B30", [_fault()])
    again = SV.AnnotateSymbolsStage().jobs(c, 0)[0][1]
    assert "## 지난 시도" in again and "byte 7014" in again and "L1-B30.json.bad" in again
    assert SV.AnnotateSymbolsStage.FIX["malformed"] in again      # 갈래별 고치는 법이 실린다
    assert again.startswith(first)          # 원래 지시는 그대로, 뒤에 붙는다


def test_프롬프트_둘은_자가검사_명령을_준다():
    b = _one_batch_plan("L0-B00")["layers"][0]["batches"][0]
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")
    assert "/root/runner/check_shard.py /repo/out/codegraph-raw/_shards/L0-B00.json" in p
    assert "check_shard.py /repo/out/codegraph-raw/_shards/NONNODE.json" in SV.AnnotateSymbolsStage.nonnode_prompt("/repo", "/root")


def test_검문이_통과한_배치의_옛_격리_흔적은_치운다(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_one_batch_plan("L0-B00")))
    shards = raw / "_shards"; shards.mkdir()
    (shards / "L0-B00.json").write_text(json.dumps({"f": _good_record()}), encoding="utf-8")
    (shards / "L0-B00.json.bad").write_text("{", encoding="utf-8")
    (shards / "L0-B00.json.bad.why").write_text("[]", encoding="utf-8")
    out = SV.AnnotateSymbolsStage().perform(c)
    assert out.kind == P.OK
    assert not (shards / "L0-B00.json.bad").exists() and not (shards / "L0-B00.json.bad.why").exists()


def test_check_shard_명령은_통과_0_불평_1(tmp_path: Path):
    import subprocess
    tool = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runner", "check_shard.py")
    good = tmp_path / "g.json"; good.write_text(json.dumps({"f": _good_record()}), encoding="utf-8")
    bad = tmp_path / "b.json"; bad.write_text('{"f": {"means": "a "b" c"}}', encoding="utf-8")
    ok = subprocess.run([sys.executable, tool, str(good)], capture_output=True, text=True)
    assert ok.returncode == 0 and "통과" in ok.stdout
    no = subprocess.run([sys.executable, tool, str(bad)], capture_output=True, text=True)
    assert no.returncode == 1 and "malformed" in no.stdout and SV.AnnotateSymbolsStage.FIX["malformed"] in no.stdout


# ── 전략 스위치 — schedule-batches 의 파일 계획 ─────────────────────────────

def test_전략_file_이면_schedule_batches_가_파일_계획과_우선순위_csv_를_낸다(tmp_path: Path):
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "codegraph.json").write_text(json.dumps({"language": "python", "nodes": [
        {"id": "a", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "module": "."},
        {"id": "b", "name": "b.f", "kind": "function", "file": "b.py", "line": 1, "module": "."}],
        "edges": [{"from": "a", "to": "b", "kind": "dependency", "label": None, "file": "a.py", "line": 1}]}))
    out = G.ScheduleBatchesStage().perform(c)
    assert out.kind == P.OK and c.plan is not None
    assert [b["id"] for b in c.plan["layers"][0]["batches"]] == ["F00", "F01"]
    assert c.plan["layers"][0]["batches"][0]["files"] == ["b.py"]
    csv = Path(X.FILE_PRIORITY.locate(c)).read_text(encoding="utf-8").splitlines()
    assert csv[0] == "file,out,into,interfaces,abstracts,weight" and csv[1].startswith("b.py,")


def test_계획_요약은_파일_계획도_읽는다():
    p = survey_plan.plan_by_file({"nodes": [{"id": "a", "name": "a.f", "kind": "function", "file": "a.py", "line": 1}], "edges": []})
    lines = G.ScheduleBatchesStage.plan_summary(p)
    assert any("파일 1" in ln and "배치 1" in ln for ln in lines)


def test_전략_기본값은_layer_이고_file_이면_writes_에_csv_가_있다(tmp_path: Path):
    c = _ctx(tmp_path)
    assert c.strategy == "layer"
    assert X.FILE_PRIORITY not in G.ScheduleBatchesStage().writes(c)
    c.strategy = "file"
    assert X.FILE_PRIORITY in G.ScheduleBatchesStage().writes(c)


# ── coverage 검문 — 주문한 심볼이 왔나 ───────────────────────────────────────

def test_coverage_검문은_빠진_심볼과_남의_심볼을_짚는다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    plan = _one_batch_plan("L0-B21")
    plan["layers"][0]["batches"][0]["symbols"].append(
        {"id": "g", "name": "m.WikiPage", "kind": "class", "file": "m.py", "line": 9, "in_cycle": False, "depends_on": []})
    (d / "L0-B21.json").write_text(json.dumps({"f": _good_record(), "m.other": _good_record()}), encoding="utf-8")
    bad = SV.AnnotateSymbolsStage.check_shards(str(d), plan)
    kinds = sorted((f["kind"], f["at"]) for f in bad["L0-B21"])
    assert kinds == [("coverage", "m.WikiPage"), ("coverage", "m.other")]
    assert "없다" in [f for f in bad["L0-B21"] if f["at"] == "m.WikiPage"][0]["detail"]
    assert SV.AnnotateSymbolsStage.FIX["coverage"] in bad["L0-B21"][0]["fix"]


def test_coverage_는_문법_꼴이_맞을_때만_본다(tmp_path: Path):
    d = tmp_path / "_shards"; d.mkdir()
    (d / "L0-B00.json").write_text("{", encoding="utf-8")
    bad = SV.AnnotateSymbolsStage.check_shards(str(d), _one_batch_plan("L0-B00"))
    assert [f["kind"] for f in bad["L0-B00"]] == ["malformed"]


def test_check_shard_명령은_옆의_batches_json_이_있으면_coverage_도_본다(tmp_path: Path):
    import subprocess
    tool = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runner", "check_shard.py")
    raw = tmp_path / "out" / "codegraph-raw"; (raw / "_shards").mkdir(parents=True)
    (raw / "batches.json").write_text(json.dumps(_one_batch_plan("L0-B00")))
    (raw / "_shards" / "L0-B00.json").write_text(json.dumps({"m.other": _good_record()}), encoding="utf-8")
    r = subprocess.run([sys.executable, tool, str(raw / "_shards" / "L0-B00.json")], capture_output=True, text=True)
    assert r.returncode == 1 and "[coverage]" in r.stdout and "f" in r.stdout


# ── dep_excerpt — depends_on 은 id, 레코드 키는 이름 ─────────────────────────

def test_dep_excerpt_는_depends_on_의_id_를_이름으로_바꿔_찾는다():
    b: survey_plan.PlanBatch = {"id": "L1-B00", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False, "depends_on": ["C1"]}]}
    merged = {"b.g": {"means": "지 뜻"}}
    assert SV.AnnotateSymbolsStage.dep_excerpt(merged, b, {"C1": "b.g"}) == "  - b.g — 지 뜻"
    assert SV.AnnotateSymbolsStage.dep_excerpt(merged, b, {}) == ""      # 이름을 모르면 못 찾는다


def test_배치_프롬프트의_의존_줄은_id_가_아니라_이름을_보인다():
    b: survey_plan.PlanBatch = {"id": "F00", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False,
         "depends_on": ["C1", "C9"]}]}
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", name_of={"C1": "b.g"})
    assert "의존 -> b.g, C9" in p                 # 이름표에 없는 id 는 그대로 둔다 — 지어내지 않는다
    assert "의존 -> C1" not in p
    assert "uses[].to 는 이 저장소 안 심볼의 레코드 키" in p
    assert "subprocess.run" in p                  # 외부 의존은 적지 않는다는 예시가 계약에 있다
    assert '"shallow": ["위 목록의 이름 그대로"]' in SV.AnnotateSymbolsStage.pending_section("  - c.h (class) c.py:3")


def test_배치_프롬프트는_이름표_없이도_돈다():
    b = _one_batch_plan("L0-B00")["layers"][0]["batches"][0]
    assert "의존 -> 없음" in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")


def test_name_of_는_계획_전체의_id_이름_표다():
    plan = _one_batch_plan("L0-B00")
    assert SV.AnnotateSymbolsStage.name_of(plan) == {"f": "f"}


# ── shallow 표시와 미조사 의존 절 ────────────────────────────────────────────

def test_샤드_형은_shallow_를_선택_칸으로_받는다():
    rec = {**_good_record(), "shallow": ["b.g", "c.h"]}
    assert SV.AnnotateSymbolsStage.check_shard(json.dumps({"f": rec}).encode()) == []
    rec["shallow"] = "b.g"                                   # 목록이어야 한다
    assert SV.AnnotateSymbolsStage.check_shard(json.dumps({"f": rec}).encode())[0]["kind"] == "schema"


def test_미조사_의존_절은_아직_없는_의존_대상을_이름_종류_자리로_적는다():
    b: survey_plan.PlanBatch = {"id": "F03", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False, "depends_on": ["C1", "C9"]}]}
    nodes = {"C1": {"id": "C1", "name": "b.g", "kind": "function", "file": "b.py", "line": 7, "module": "."},
             "C9": {"id": "C9", "name": "c.h", "kind": "class", "file": "c.py", "line": 3, "module": "."}}
    got = SV.AnnotateSymbolsStage.pending_excerpt({"b.g": {"means": "있다"}}, b, nodes)
    assert got == "  - c.h (class) c.py:3"                    # b.g 는 이미 있으니 빠진다


def test_미조사_의존_절은_같은_배치의_심볼을_넣지_않는다():
    """자기 파일 안의 함수는 지금 읽고 있는 것이다 — "열지 마라" 목록에 들어가면 안 된다."""
    b: survey_plan.PlanBatch = {"id": "F03", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False,
         "depends_on": ["C3", "C9"]},
        {"id": "C3", "name": "a.h", "kind": "function", "file": "a.py", "line": 5, "in_cycle": False,
         "depends_on": []}]}
    nodes = {"C3": {"id": "C3", "name": "a.h", "kind": "function", "file": "a.py", "line": 5, "module": "."},
             "C9": {"id": "C9", "name": "c.h", "kind": "class", "file": "c.py", "line": 3, "module": "."}}
    assert SV.AnnotateSymbolsStage.pending_excerpt({}, b, nodes) == "  - c.h (class) c.py:3"


def test_파일_전략_프롬프트는_미조사_절과_shallow_지시를_싣는다():
    b = _one_batch_plan("F00")["layers"][0]["batches"][0]
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", pending="  - c.h (class) c.py:3")
    assert "## 아직 조사되지 않은 의존 대상" in p and "c.h (class)" in p and "shallow" in p
    assert "## 아직 조사되지 않은 의존 대상" not in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")


# ── 미해결 표 unresolved.csv ─────────────────────────────────────────────────

def test_into_of_는_다른_파일에서_들어오는_간선_수를_이름으로_센다():
    cg: X.CodeGraphDoc = {"nodes": [{"id": "a", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "module": "."},
                                    {"id": "b", "name": "b.g", "kind": "function", "file": "b.py", "line": 1, "module": "."},
                                    {"id": "b2", "name": "b.h", "kind": "function", "file": "b.py", "line": 2, "module": "."}],
                          "edges": [{"from": "a", "to": "b", "kind": "dependency", "label": None, "file": "a.py", "line": 1},
                                    {"from": "b2", "to": "b", "kind": "dependency", "label": None, "file": "b.py", "line": 2}]}
    assert SV.AnnotateSymbolsStage.into_of(cg) == {"a.f": 0, "b.g": 1, "b.h": 0}   # 같은 파일 b2→b 는 안 센다


def test_미해결_표는_shallow_레코드마다_의존_대상_한_줄이고_상태를_가른다():
    merged = {"a.f": {**_good_record(), "shallow": ["b.g", "z.none"]}, "b.g": _good_record()}
    weight = {"m.py": 1.25}; into = {"a.f": 2, "b.g": 0}
    rows = SV.AnnotateSymbolsStage.unresolved_rows(merged, weight, into, known={"b.g"})
    assert rows == [
        {"file": "m.py", "key": "a.f", "dep": "b.g", "priority": 1.25, "into": 2, "status": "resolved"},
        {"file": "m.py", "key": "a.f", "dep": "z.none", "priority": 1.25, "into": 2, "status": "unknown"}]
    rows = SV.AnnotateSymbolsStage.unresolved_rows({"a.f": {**_good_record(), "shallow": ["c.k"]}}, weight,
                                                   {"a.f": 1, "c.k": 0}, known=set(), queued={"a.f"})
    assert [r["status"] for r in rows] == ["queued"]


def test_미해결_csv_머리줄():
    text = SV.AnnotateSymbolsStage.unresolved_csv([
        {"file": "m.py", "key": "a.f", "dep": "b.g", "priority": 1.25, "into": 2, "status": "shallow"}])
    assert text.splitlines() == ["file,key,dep,priority,into,status", "m.py,a.f,b.g,1.250000,2,shallow"]


# ── 2패스 — 파일을 열지 않고 shallow 레코드를 다듬어 원 샤드에 덧씌운다 ─────────

def test_2패스_프롬프트는_파일을_열지_말라_하고_얕은_레코드와_의존_뜻을_준다():
    shallow = {"a.f": {**_good_record(), "shallow": ["b.g"]}}
    deps = {"b.g": {**_good_record(), "means": "지 뜻", "does": "지 일"}}
    p = SV.AnnotateSymbolsStage.pass2_prompt("/repo", "/root", "F03", "a.py", shallow, deps)
    assert "열지" in p and "a.f" in p and "지 뜻" in p and "_shards/_pass2/F03.json" in p and "shallow" in p


def test_2패스_결과는_원_샤드의_같은_키만_덮고_shallow_를_뗀다(tmp_path: Path):
    d = tmp_path / "_shards"; (d / "_pass2").mkdir(parents=True)
    (d / "F03.json").write_text(json.dumps({"a.f": {**_good_record(), "shallow": ["b.g"]}, "a.h": _good_record()}), encoding="utf-8")
    (d / "_pass2" / "F03.json").write_text(json.dumps({"a.f": {**_good_record(), "does": "다듬음"}, "a.zzz": _good_record()}), encoding="utf-8")
    faults = SV.AnnotateSymbolsStage.apply_pass2(str(d), "F03")
    assert faults == []
    got = json.loads((d / "F03.json").read_text(encoding="utf-8"))
    assert got["a.f"]["does"] == "다듬음" and "shallow" not in got["a.f"] and got["a.h"] == _good_record()
    assert "a.zzz" not in got                                   # 계획 밖 키는 버린다
    assert (d / "_pass2" / "F03.done.json").exists()            # 감사용으로 남긴다


def test_2패스_결과가_깨졌으면_원_샤드를_건드리지_않는다(tmp_path: Path):
    d = tmp_path / "_shards"; (d / "_pass2").mkdir(parents=True)
    before = json.dumps({"a.f": {**_good_record(), "shallow": ["b.g"]}})
    (d / "F03.json").write_text(before, encoding="utf-8")
    (d / "_pass2" / "F03.json").write_text("{", encoding="utf-8")
    faults = SV.AnnotateSymbolsStage.apply_pass2(str(d), "F03")
    assert faults and faults[0]["kind"] == "malformed"
    assert (d / "F03.json").read_text(encoding="utf-8") == before


# ── AnnotateFilesStage — 완료 콜백이 있는 풀 ──────────────────────────────────

def _fake_agent(shards: dict[str, dict[str, object]], calls: list[str]):
    """라벨을 보고 샤드를 써 주는 가짜 세션. 프롬프트의 '쓰는 곳' 줄에서 경로를 뽑는다."""
    import re

    def run(model: str, repo: str, root: str, prompt: str, timeout: float | None,
            label: str = "") -> tuple[float, int, M.ClaudeResult | None]:
        calls.append(label)
        m = re.search(r"(\S+/_shards/\S+\.json)", prompt)
        assert m, label
        path = m.group(1)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(shards[label], f, ensure_ascii=False)
        return 0.01, 0, {"subtype": "success", "is_error": False, "num_turns": 2, "total_cost_usd": 0.01,
                         "usage": {"input_tokens": 1, "output_tokens": 1,
                                   "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}
    return run


def _three_file_graph() -> X.CodeGraphDoc:
    """b.py 는 의존 없음(먼저) · a.f 가 b.g 에 의존 · c.k 가 a.f 에 의존."""
    return {"nodes": [
        {"id": "a", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "module": "."},
        {"id": "b", "name": "b.g", "kind": "function", "file": "b.py", "line": 1, "module": "."},
        {"id": "c", "name": "c.k", "kind": "function", "file": "c.py", "line": 1, "module": "."}],
        "edges": [{"from": "a", "to": "b", "kind": "dependency", "label": None, "file": "a.py", "line": 1},
                  {"from": "c", "to": "a", "kind": "dependency", "label": None, "file": "c.py", "line": 1}]}


def _rec(where: str, **more: object) -> dict[str, object]:
    return {**_good_record(), "where": where, "uses": [], **more}


def test_파일_스케줄러는_가중치_순으로_돌고_shallow_가_풀리면_2패스를_넣는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import mode1.survey_files as SF
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"; c.concurrency = 1
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    cg = _three_file_graph()
    (raw / "codegraph.json").write_text(json.dumps(cg))
    plan = survey_plan.plan_by_file(cast(survey_plan.CodeGraph, cg))
    (raw / "batches.json").write_text(json.dumps(plan))
    ids = {b["files"][0]: b["id"] for b in plan["layers"][0]["batches"]}
    shards: dict[str, dict[str, object]] = {
        ids["b.py"]: {"b.g": _rec("b.py:1")},
        ids["a.py"]: {"a.f": _rec("a.py:1", shallow=["b.g"])},      # 세션이 b.g 를 얕게 썼다고 치자
        ids["c.py"]: {"c.k": _rec("c.py:1", shallow=["a.f"])},
        ids["a.py"] + "/p2": {"a.f": _rec("a.py:1", does="다듬음")},
        "NONNODE": {"a.py": {**_rec("a.py:1"), "kind": "file"}},
    }
    calls: list[str] = []
    monkeypatch.setattr(SF.P, "run_agent_with", _fake_agent(shards, calls))
    out = SF.AnnotateFilesStage().perform(c)
    assert out.kind == P.OK, out.why
    assert calls[:3] == [ids["b.py"], ids["a.py"], ids["c.py"]]            # 가중치 순
    assert ids["a.py"] + "/p2" in calls                                   # a.f: into=1(c→a) · b.g 가 있다 → 2패스
    assert ids["c.py"] + "/p2" not in calls                               # c.k: into=0 → 다듬지 않는다
    assert calls[-1] == "NONNODE"
    merged = json.loads(Path(X.READING.locate(c)).read_text(encoding="utf-8"))
    assert merged["a.f"]["does"] == "다듬음" and "shallow" not in merged["a.f"]
    assert merged["c.k"].get("shallow") == ["a.f"]                         # 남은 shallow 는 그대로
    csv = Path(X.UNRESOLVED.locate(c)).read_text(encoding="utf-8").splitlines()
    assert csv[0] == "file,key,dep,priority,into,status"
    assert any(",c.k,a.f," in ln and ln.endswith(",resolved") for ln in csv)
    stages = [r["stage"] for r in out.rows]
    assert "annotate-symbols/%s/p2" % ids["a.py"] in stages and stages[-1] == "annotate-symbols/check-shards"
    assert c.survey_ok is True


def test_파일_스케줄러는_틀린_샤드를_격리하고_FAIL_로_끝낸다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import mode1.survey_files as SF
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"; c.concurrency = 2
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    cg = _three_file_graph()
    (raw / "codegraph.json").write_text(json.dumps(cg))
    plan = survey_plan.plan_by_file(cast(survey_plan.CodeGraph, cg))
    (raw / "batches.json").write_text(json.dumps(plan))
    ids = {b["files"][0]: b["id"] for b in plan["layers"][0]["batches"]}
    shards: dict[str, dict[str, object]] = {
        ids["b.py"]: {"b.g": _rec("b.py:1")}, ids["a.py"]: {"a.f": _rec("a.py:1")},
        ids["c.py"]: {"wrong.key": _rec("c.py:1")}, "NONNODE": {}}
    monkeypatch.setattr(SF.P, "run_agent_with", _fake_agent(shards, []))
    out = SF.AnnotateFilesStage().perform(c)
    assert out.kind == P.FAIL and c.survey_ok is False
    assert (raw / "_shards" / (ids["c.py"] + ".json.bad")).exists()
    faults = SV.AnnotateSymbolsStage.load_faults(str(raw / "_shards"), ids["c.py"])
    assert faults and faults[0]["kind"] == "coverage"
    assert "NONNODE" not in [r["stage"].split("/")[-1] for r in out.rows]      # 실패했으면 비노드 세션을 안 띄운다


def test_전략_file_이면_annotate_symbols_가_파일_단계이고_그래프_이름이_갈린다(tmp_path: Path):
    import mode1.survey_files as SF
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"
    g = E.build_mode1_graph(c, only=None, skip=None)
    assert isinstance(g.stages["annotate-symbols"], SF.AnnotateFilesStage) and g.name == "mode1-cold-file"
    c.strategy = "layer"
    g = E.build_mode1_graph(c, only=None, skip=None)
    assert type(g.stages["annotate-symbols"]) is SV.AnnotateSymbolsStage and g.name == "mode1-cold"
