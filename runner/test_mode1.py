"""`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "machine"))
import pipeline as P  # noqa: E402
from mode1 import context as X  # noqa: E402
from mode1 import diff as D  # noqa: E402
from mode1 import graph as G  # noqa: E402
from mode1 import lang as LG  # noqa: E402
from mode1 import machine_stage as MC  # noqa: E402
from mode1 import measured as MS  # noqa: E402
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


def test_코드지도_검사는_최상위_열쇠만_본다():
    assert X.check_codegraph({"nodes": [], "edges": []}) == []
    assert X.check_codegraph({"nodes": "x"}) != []
    assert X.check_codegraph([]) != []


def test_층계획_검사는_층과_합계를_본다():
    assert X.check_batches({"target": 8, "layers": [], "totals": {}}) == []
    assert X.check_batches({"layers": {}}) != []


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


def test_diff_검사는_넷_갈래가_다_있어야_통과한다():
    assert D.check_diff({"verdicts": _verdicts(), "targets": None, "hops": 1, "tracked": 2}) == []
    assert D.check_diff({"verdicts": {"유효": []}, "targets": None, "hops": 1, "tracked": 0}) != []
    assert X.CHANGES.check is D.check_diff


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


def _plan_with(files: list[str]) -> dict[str, object]:
    """배치 하나짜리 계획. ⚠ 이것으로 `annotate-symbols` 를 돌리면 세션이 실제로 뜬다 — 대조 시험에만 쓴다."""
    syms = [{"name": f + ".S", "file": f} for f in files]
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

    def fake_plan(cg: object, target: int = 8, only_files: list[str] | None = None) -> dict[str, object]:
        seen["only"] = only_files
        return _plan_with([])
    monkeypatch.setattr(G.survey_plan, "plan", fake_plan)
    c.targets = ["x.py"]
    out = G.ScheduleBatchesStage().perform(c)
    assert out.kind == P.OK and seen["only"] == ["x.py"] and c.plan is not None
    assert (raw / "batches.json").exists()


def test_계획_요약은_층과_합계를_낸다():
    plan = _plan_with(["a.py"])
    lines = G.ScheduleBatchesStage.plan_summary(plan)  # type: ignore[arg-type]
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


def _empty_plan() -> dict[str, object]:
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


def test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다():
    b = {"id": "L1-B00", "files": ["a.py"], "symbols": [{"name": "f", "kind": "function", "file": "a.py", "line": 1}]}
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", ["a.py"], 3)  # type: ignore[arg-type]
    assert "## 범위" in p and "_shards/L1-B00.json" in p
    assert "## 범위" not in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")  # type: ignore[arg-type]


# ── 9. 위키 목차와 장 ───────────────────────────────────────────────────


def test_outline_wiki_는_목차_파일을_쓴다고_선언하고_있으면_SKIP(tmp_path: Path):
    c = _ctx(tmp_path)
    assert W.OutlineWikiStage().writes(c) == [X.OUTLINE]
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    (raw / "outline.json").write_text('{"pages": []}')
    assert W.OutlineWikiStage().perform(c).kind == P.SKIP


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
