"""`outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다."""
import sys

import pipeline as P
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine


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
