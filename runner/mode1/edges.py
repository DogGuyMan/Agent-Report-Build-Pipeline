"""Mode 1 의 흐름 — 단계 순서 · 전이표 하나 · 팩토리. 단계는 자기 다음을 모른다."""
from collections.abc import Iterable

import pipeline as P
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.graph import CollectGraphStage, ScheduleBatchesStage
from mode1.lang import LangDecideStage, LangHintStage
from mode1.scan import DetectChangesStage, SnapshotSourcesStage
from mode1.seal import SealArtifactsStage
from mode1.survey import AnnotateSymbolsStage
from mode1.survey_files import AnnotateFilesStage
from mode1.terms import VerifyTermsStage
from mode1.wiki import OutlineWikiStage, PublishWikiStage, VerifyWikiStage, WriteWikiStage

ORDER = ["lang-hint", "lang-decide", "detect-changes", "collect-graph", "schedule-batches",
         "annotate-symbols", "snapshot-sources", "verify-terms", "outline-wiki", "write-wiki",
         "publish-wiki", "verify-wiki", "seal-artifacts"]

# 전량 그래프에는 없는 단계. 대조할 옛 지문이 없는데 대조 단계를 돌리지 않는다.
WARM_ONLY: set[str] = {"detect-changes"}

# 옛 이름. `--only lang-select` 처럼 옛 명령줄이 그대로 돌게 한다.
ALIASES = {
    "lang-select": ["lang-hint", "lang-decide"], "warmup": ["detect-changes"],
    "prep": ["collect-graph"], "survey-plan": ["schedule-batches"],
    "survey": ["annotate-symbols"], "warmup-save": ["snapshot-sources"],
    "terms": ["verify-terms"], "wiki": ["outline-wiki", "write-wiki"],
    "wiki-catalogue": ["outline-wiki"], "wiki-pages": ["write-wiki"],
    "build": ["publish-wiki"], "check": ["verify-wiki"],
}

STAGES: dict[str, P.Stage[Mode1Context]] = {
    "lang-hint": LangHintStage(), "lang-decide": LangDecideStage(),
    "detect-changes": DetectChangesStage(), "collect-graph": CollectGraphStage(),
    "schedule-batches": ScheduleBatchesStage(), "annotate-symbols": AnnotateSymbolsStage(),
    "snapshot-sources": SnapshotSourcesStage(), "verify-terms": VerifyTermsStage(),
    "outline-wiki": OutlineWikiStage(), "write-wiki": WriteWikiStage(),
    "publish-wiki": PublishWikiStage(), "verify-wiki": VerifyWikiStage(),
    "seal-artifacts": SealArtifactsStage(),
}

# 전이표는 **하나**다. 전량과 증분의 차이는 단계 목록(`WARM_ONLY`)과 `ctx.cold` 가 만든다.
# 갈래 선언(`emits`)은 클래스에 있으므로 표가 하나여야 두 그래프 모두 완결성 검사를 통과한다.
# `SKIP` 은 "산출물 없이 다음으로" 다 — 산출물이 이미 있어 안 만드는 것은 `OK` 다(`outline-wiki`).
EDGES = P.Edges({
    ("*", P.OK): P.NEXT, ("*", P.FAIL): P.HALT,
    ("lang-hint", P.SKIP): P.NEXT,          # 제안 없이 파일 수로 고른다 (D4 의 폴백)
    ("annotate-symbols", P.SKIP): P.NEXT,   # 바뀐 파일 0개 — 증분에서만 실제로 난다
})


def graph_name(ctx: Mode1Context) -> str:
    """전량/증분과 전략이 이름을 가른다 — `resume.json` 이 이 이름으로 자기 그래프를 알아본다."""
    base = "mode1-cold" if ctx.cold else "mode1-warm"
    return base + ("-file" if ctx.strategy == "file" else "")


def stages_for(ctx: Mode1Context) -> dict[str, P.Stage[Mode1Context]]:
    """전략이 고르는 단계는 하나뿐이다 — annotate-symbols."""
    got = dict(STAGES)
    if ctx.strategy == "file":
        got["annotate-symbols"] = AnnotateFilesStage()
    return got


def expand(names: Iterable[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        out += ALIASES.get(n, [n])
    return out


def plan_stages(only: Iterable[str] | None, skip: Iterable[str] | None,
                cold: bool = False) -> list[str]:
    """`--only` · `--skip` · 전량 여부만 본다. 재개 건너뛰기는 갈래(SKIP)와 재개 JSON 이 한다."""
    o = set(expand(only)) if only else None
    s: set[str] = set(expand(skip or []))
    if cold:
        s |= WARM_ONLY
    for n in (o or set()) | s:
        if n not in ORDER:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (n, ", ".join(ORDER)))
    return [n for n in ORDER if (o is None or n in o) and n not in s]


def build_mode1_graph(ctx: Mode1Context, only: Iterable[str] | None,
                      skip: Iterable[str] | None,
                      start_at: str | None = None) -> P.StageDagGraph[Mode1Context]:
    """진입점에서 부른다. `start_at` 은 재개 JSON 이 준 단계다 — 그 앞을 잘라 낸다."""
    names = plan_stages(only, skip, cold=ctx.cold)
    if start_at is not None:
        if start_at not in names:
            raise ValueError("재개할 단계가 흐름에 없다: %s" % start_at)
        names = names[names.index(start_at):]
    stages = stages_for(ctx)
    return P.build_graph(graph_name(ctx), names, {n: stages[n] for n in names},
                         EDGES, P.existing(X.ARTIFACTS, ctx), ctx)
