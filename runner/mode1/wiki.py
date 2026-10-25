"""`outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다."""
import os
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
import pipeline as P
import survey_plan
from mode1 import context as X
from mode1.context import Mode1Context, WikiPage
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured


class OutlineWikiStage(Measured, P.LlmStage[Mode1Context]):
    """목차 한 세션. 이미 있으면 세션 없이 OK — 산출물이 있으면 계약은 지켜진 것이다.

    `SKIP` 은 "산출물 없이 다음으로" 라는 뜻이라 여기에 맞지 않는다. `SKIP` 으로 내면
    시뮬레이터가 `write-wiki` 의 읽기(`outline.json`)를 보장하지 못해 그래프를 거부한다.
    """
    name = "outline-wiki"
    prompt_dir = X.PROMPT_DIR
    prompt_names = ("outline-wiki",)

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return self.wiki_catalogue_prompt(ctx.repo, ctx.root)

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE]

    @staticmethod
    def wiki_catalogue_prompt(repo: str, root: str) -> str:
        """페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다.

        K6 의 층을 매기려면 이 둘이 있어야 하는데, 위키 페이지는 심볼도 모듈도 아닌 **주제**
        단위라 기계가 결정론으로 못 만든다. 그래서 이 한 세션만 먼저 돈다.
        """
        return OutlineWikiStage.load_prompt("outline-wiki", repo=repo, root=root)

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if os.path.exists(X.OUTLINE.locate(ctx)):
            row = self.row(t0, True, "목차가 이미 있다")
            row["skipped"] = True
            return P.Outcome(P.OK, "", [row])
        return super().perform(ctx)


class WriteWikiStage(Measured, P.LlmStage[Mode1Context]):
    """장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛴다."""
    name = "write-wiki"
    prompt_dir = X.PROMPT_DIR
    prompt_names = ("write-wiki#main",)

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE, X.BATCHES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        # 장들은 LLM 자식 프로세스가 쓴다. "돌고 나면 있어야 한다" 는 선언이지 누가 쓰는가가 아니다 —
        # 이것이 없으면 시뮬레이터가 `publish-wiki` 의 읽기(`docs/wiki`)를 보장 못 해 그래프를 거부한다.
        return [X.WIKI_DIR]

    @staticmethod
    def symbol_layers(plan: survey_plan.SurveyPlan) -> dict[str, int]:
        """`batches.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다."""
        return {s["id"]: L["level"]
                for L in plan.get("layers", [])
                for b in L.get("batches", [])
                for s in b.get("symbols", [])}

    @staticmethod
    def page_layers(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]:
        """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층.

        아는 심볼이 하나도 없으면 층0 이다 — `index.md` 처럼 개괄만 있는 장이 여기 온다.
        `sym_layer` 에 없는 이름은 세지 않으므로, 카탈로그가 지어낸 이름 하나로 페이지가
        맨 뒤로 밀리지 않는다.
        """
        out: dict[str, int] = {}
        for p in pages:
            known = [sym_layer[s] for s in p.get("symbols", []) if s in sym_layer]
            out[p["file"]] = max(known) if known else 0
        return out

    @staticmethod
    def wiki_page_prompt(repo: str, root: str, page: WikiPage, lower_pages: Sequence[X.LowerPageRow]) -> str:
        """장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다."""
        return WriteWikiStage.load_prompt(
            "write-wiki#main", repo=repo, root=root, fname=page["file"],
            title=page.get("title") or page["file"], syms=page.get("symbols") or [], lower=lower_pages)

    def prepare(self, ctx: Mode1Context) -> None:
        ctx.wiki_pages = P.load(X.OUTLINE.locate(ctx), X.Outline)["pages"]
        assert ctx.plan is not None
        lv = self.page_layers(ctx.wiki_pages, self.symbol_layers(ctx.plan))
        ctx.wiki_levels = sorted(set(lv.values()))
        ctx.wiki_level_of = lv
        ctx.wiki_done = []

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if ctx.plan is None:
            ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
        self.prepare(ctx)
        return super().perform(ctx)

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.wiki_levels)

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        k = ctx.wiki_levels[rnd]
        here = [pg for pg in ctx.wiki_pages if ctx.wiki_level_of[pg["file"]] == k
                and not os.path.exists(os.path.join(ctx.repo, "docs", "wiki", pg["file"]))]
        lower: list[X.LowerPageRow] = [{"fname": pg["file"], "title": pg.get("title") or pg["file"]}
                                       for pg in ctx.wiki_done]
        ctx.wiki_done = ctx.wiki_done + here
        return [(pg["file"], self.wiki_page_prompt(ctx.repo, ctx.root, pg, lower)) for pg in here]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "write-wiki/" + row["stage"]
        return out


class PublishWikiStage(Mode1Machine):
    name = "publish-wiki"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return self.wiki_argv(sys.executable, ctx.root, "build.py", ctx.repo)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]


class VerifyWikiStage(Mode1Machine):
    name = "verify-wiki"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return self.wiki_argv(sys.executable, ctx.root, "check.py", ctx.repo)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.WIKI_DIR]
