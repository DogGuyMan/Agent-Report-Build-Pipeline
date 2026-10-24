"""`lang-hint` · `lang-decide`. 언어 하나를 제안받고 결정론으로 채택한다."""
import os
import subprocess
import sys
import time
from collections.abc import Sequence

import pipeline as P
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured

# 언어 판별에 쓸 Model. 문서를 읽고 `cpp|cs|py|ts` 중 하나를 내는 것이 전부라 가장 싼 것을 쓴다.
# `--model` 은 annotate-symbols · write-wiki 몫이라 여기에 쓰지 않는다.
LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"
LANG_WORDS = ("cpp", "cs", "py", "ts")


class LangHintStage(Measured, P.LlmStage[Mode1Context]):
    """루트 문서를 읽혀 언어 하나를 제안받는다. 못 받아도 막지 않는다 — 관문이 아니다."""
    name = "lang-hint"
    emits = P.OK | P.SKIP
    prompt_dir = X.PROMPT_DIR
    prompt_names = ("lang-hint",)

    def model(self, ctx: Mode1Context) -> str:
        return LANG_SELECT_MODEL

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    @staticmethod
    def hint_prompt(docs: str) -> str:
        # 절은 줄바꿈 하나로 끝난다 — docs 뒤에 붙은 그 하나를 뗀다.
        return LangHintStage.load_prompt("lang-hint", docs=docs)[:-1]

    def docs(self, ctx: Mode1Context) -> str:
        """루트 문서 묶음. `lang_select.py --print-docs` 가 고른다."""
        tool = os.path.join(ctx.root, "machine", "lang_select.py")
        return subprocess.run([sys.executable, tool, ctx.repo, "--print-docs"],
                              capture_output=True, text=True).stdout

    def prompt(self, ctx: Mode1Context) -> str:
        return self.hint_prompt(self.docs(ctx))

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        docs = self.docs(ctx)
        return [(self.name, self.hint_prompt(docs))] if docs.strip() else []

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        t0 = time.monotonic()
        ctx.proposed = None
        if not got:
            r = self.row(t0, True, "루트 문서 없음 — 파일 수로 고른다")
            r["skipped"] = True
            return P.Outcome(P.SKIP, r["why"], [r])
        base = super().harvest(ctx, got, rnd)
        for _, _, rc, result in got:
            word = (result.get("result", "") if result else "").strip().strip("`.").lower()
            if rc == 0 and word in LANG_WORDS:
                ctx.proposed = word
        if base.kind != P.OK or ctx.proposed is None:
            for r in base.rows:
                r["ok"], r["why"], r["skipped"] = True, "제안 없음 — 파일 수로 고른다", True
            return P.Outcome(P.SKIP, "제안 없음", base.rows)
        return base


class LangDecideStage(Mode1Machine):
    """제안을 결정론으로 기각하거나 채택해 `lang-select.json` 을 쓴다."""
    name = "lang-decide"

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = [sys.executable, os.path.join(ctx.root, "machine", "lang_select.py"),
                ctx.repo, "-o", X.LANG_SELECT.locate(ctx)]
        if ctx.proposed:
            argv += ["--propose", ctx.proposed]
        return argv

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.LANG_SELECT]
