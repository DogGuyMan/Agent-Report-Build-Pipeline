"""`outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다."""
import hashlib
import json
import os
import shutil
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
import msgspec
import pipeline as P
import survey_plan
import warmup
from manifest import WikiState
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
    """장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛰고, 따라잡은 기준 뒤 바뀐 파일을 인용하는 장만 다시 쓴다. 사람이 고친 장은 .bak 에 남기고 덮는다.

    기준은 `wiki-state.json` 의 `sources` 다 — 전량 · 증분이 같다. 기준이 없으면 기존 장의 신선도를 모르므로
    건너뛰고, 그런 장이 하나라도 있으면 끝나도 따라잡았다고 적지 않는다. 장의 해시는 층마다 바로 적고,
    기존 장이 없는 처음 굽기면 그때 지문을 기준으로 함께 적는다. `snapshot_sha256` 은 끝에서만 적는다.
    """
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

    @staticmethod
    def page_hash(path: str) -> str:
        """파일 바이트 그대로의 sha256."""
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    @staticmethod
    def stale_pages(wiki_dir: str, pages: Iterable[str], changed: set[str]) -> set[str]:
        """이미 쓴 장 중 바뀐 파일의 경로를 글자 그대로 담은 것. 그 장은 다시 쓴다."""
        out: set[str] = set()
        for name in pages:
            path = os.path.join(wiki_dir, name)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                if any(c in text for c in changed):
                    out.add(name)
        return out

    @staticmethod
    def edited_pages(wiki_dir: str, pages: Iterable[str], recorded: Mapping[str, str]) -> set[str]:
        """지난 write-wiki 가 적어 둔 해시와 지금 해시가 다른 장 — 사람이 고친 것이다."""
        out: set[str] = set()
        for name in pages:
            path = os.path.join(wiki_dir, name)
            if name in recorded and os.path.exists(path) and WriteWikiStage.page_hash(path) != recorded[name]:
                out.add(name)
        return out

    @staticmethod
    def back_up_edited(wiki_dir: str, edited: Iterable[str]) -> list[str]:
        """손댄 장을 `docs/wiki/.bak/<장>` 으로 옮긴다. 옮긴 뒤에는 없는 장이라 `jobs` 가 다시 쓴다."""
        moved: list[str] = []
        bak = os.path.join(wiki_dir, ".bak")
        for name in sorted(edited):
            os.makedirs(bak, exist_ok=True)
            shutil.move(os.path.join(wiki_dir, name), os.path.join(bak, name))
            moved.append(name)
        return moved

    @staticmethod
    def read_state(path: str) -> WikiState | None:
        """지난 write-wiki 의 상태. 없거나 꼴이 틀리면 None — 그러면 기준도 손댐도 판정하지 않는다."""
        try:
            return P.load(path, WikiState)
        except (OSError, msgspec.DecodeError):
            return None

    @staticmethod
    def write_state(path: str, state: WikiState) -> None:
        """`wiki-state.json` 을 쓴다. 다른 산출물과 같은 꼴(들여쓰기 1, 한글 그대로)이다."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)

    @staticmethod
    def source_hashes(snapshot: str) -> dict[str, str] | None:
        """지문 파일의 `{경로: file_hash}`. 지문이 없으면 None. 못 읽은 파일(`file_hash` 가 None)은 뺀다."""
        if not os.path.exists(snapshot):
            return None
        return {rel: h for rel, e in warmup.load(snapshot).items() if (h := e.get("file_hash"))}

    @staticmethod
    def changed_sources(prev: Mapping[str, str], cur: Mapping[str, str]) -> set[str]:
        """기준 소스 지도와 지금 지문의 해시가 다른 경로 — 바뀐 것 · 새로 생긴 것 · 지운 것."""
        return {p for p in prev.keys() | cur.keys() if prev.get(p) != cur.get(p)}

    @staticmethod
    def record_pages(state_path: str, wiki_dir: str, names: Iterable[str],
                     sources: Mapping[str, str] | None = None) -> None:
        """방금 쓴 장들의 해시를 `pages` 에 적는다. `sources` 를 주면 기준도 바꿔 적는다. `snapshot_sha256` 은 건드리지 않는다."""
        state: WikiState = WriteWikiStage.read_state(state_path) or {}
        pages = dict(state.get("pages", {}))
        for name in names:
            pages[name] = WriteWikiStage.page_hash(os.path.join(wiki_dir, name))
        state["pages"] = pages
        if sources is not None:
            state["sources"] = dict(sources)
        WriteWikiStage.write_state(state_path, state)

    @staticmethod
    def mark_caught_up(state_path: str, snapshot: str, sources: Mapping[str, str]) -> None:
        """위키가 이 지문을 따라잡았다고 적는다 — `sources` 와 `snapshot_sha256`. `pages` 는 그대로 둔다."""
        state: WikiState = WriteWikiStage.read_state(state_path) or {}
        state["snapshot_sha256"] = WriteWikiStage.page_hash(snapshot)
        state["sources"] = dict(sources)
        state["pages"] = dict(state.get("pages", {}))
        WriteWikiStage.write_state(state_path, state)

    def prepare(self, ctx: Mode1Context) -> None:
        ctx.wiki_pages = P.load(X.OUTLINE.locate(ctx), X.Outline)["pages"]
        assert ctx.plan is not None
        lv = self.page_layers(ctx.wiki_pages, self.symbol_layers(ctx.plan))
        ctx.wiki_levels = sorted(set(lv.values()))
        ctx.wiki_level_of = lv
        ctx.wiki_done = []
        wiki_dir = os.path.join(ctx.repo, "docs", "wiki")
        state = self.read_state(X.WIKI_STATE.locate(ctx))
        prev = state.get("sources") if state is not None else None
        cur = self.source_hashes(X.SNAPSHOT.locate(ctx))
        existing = [pg["file"] for pg in ctx.wiki_pages if os.path.exists(os.path.join(wiki_dir, pg["file"]))]
        if prev is None or cur is None:
            ctx.wiki_stale, ctx.wiki_unknown = set(), existing
        else:
            ctx.wiki_stale, ctx.wiki_unknown = self.stale_pages(wiki_dir, existing, self.changed_sources(prev, cur)), []
        ctx.wiki_first_bake = prev is None and cur is not None and not existing
        recorded = state.get("pages", {}) if state is not None else {}
        ctx.wiki_backed_up = self.back_up_edited(wiki_dir, self.edited_pages(wiki_dir, ctx.wiki_stale, recorded))

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if ctx.plan is None:
            ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
        self.prepare(ctx)
        out = super().perform(ctx)
        if ctx.wiki_backed_up:
            print("손으로 고친 장 %d개를 덮었다 — 원본은 docs/wiki/.bak/ 에 있다:" % len(ctx.wiki_backed_up))
            for name in ctx.wiki_backed_up:
                print("  " + name)
        if out.kind != P.OK:
            return out
        snap = X.SNAPSHOT.locate(ctx)
        cur = self.source_hashes(snap)
        if ctx.wiki_unknown:
            print("위키는 따라잡았다고 적지 않는다 — 지난 기준이 없어 기존 장 %d개의 신선도를 모른다. "
                  "그 장들을 지우고 다시 돌리면 새로 굽는다" % len(ctx.wiki_unknown))
        elif cur is not None:
            self.mark_caught_up(X.WIKI_STATE.locate(ctx), snap, cur)
        return out

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.wiki_levels)

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        k = ctx.wiki_levels[rnd]
        here = [pg for pg in ctx.wiki_pages if ctx.wiki_level_of[pg["file"]] == k
                and (pg["file"] in ctx.wiki_stale
                     or not os.path.exists(os.path.join(ctx.repo, "docs", "wiki", pg["file"])))]
        lower: list[X.LowerPageRow] = [{"fname": pg["file"], "title": pg.get("title") or pg["file"]}
                                       for pg in ctx.wiki_done]
        ctx.wiki_done = ctx.wiki_done + here
        return [(pg["file"], self.wiki_page_prompt(ctx.repo, ctx.root, pg, lower)) for pg in here]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        """층이 끝날 때마다 성공한 장의 해시를 바로 적는다 — 뒤 층이 실패해도 그 장은 LLM 이 쓴 것으로 남는다.

        처음 굽기면 지금 지문을 기준(`sources`)으로 함께 적는다 — 있는 장이 전부 이 지문으로 쓴 것이라서다.
        기준이 있던 실행은 기준을 옮기지 않는다 — 옮기면 아직 다시 쓰지 않은 낡은 장이 낡음 판정에서 빠진다.
        """
        out = super().harvest(ctx, got, rnd)
        wiki_dir = os.path.join(ctx.repo, "docs", "wiki")
        written = [row["stage"] for row in out.rows
                   if row["ok"] and os.path.exists(os.path.join(wiki_dir, row["stage"]))]
        if written:
            cur = self.source_hashes(X.SNAPSHOT.locate(ctx)) if ctx.wiki_first_bake else None
            self.record_pages(X.WIKI_STATE.locate(ctx), wiki_dir, written, cur)
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

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        out = super().perform(ctx)
        if out.kind == P.OK:
            ctx.verified.add("wiki")
        return out
