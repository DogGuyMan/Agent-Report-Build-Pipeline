"""`verify-terms`. 읽기 레코드를 인용 검사하고 용어 DB 로 투영한다."""
import os
import sys

import pipeline as P
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine


class VerifyTermsStage(Mode1Machine):
    name = "verify-terms"

    @staticmethod
    def terms_argv(python: str, root: str, repo: str,
                   codegraph: str | None, reading: str | None) -> list[str]:
        """`terms_db.py` 명령줄.

        **정적 `codegraph.json` 을 위치 인자로 반드시 준다.** `--reading` 만 주면 읽기
        레코드의 투영이 그 파일을 **덮어써서** 정적 수집기가 찾은 노드가 조용히 사라진다.
        둘 다 주면 구조는 codegraph 가 이긴다.
        """
        argv = [python, os.path.join(root, "machine", "terms_db.py")]
        if codegraph:
            argv.append(codegraph)
        argv += ["--repo", repo]
        if reading:
            argv += ["--reading", reading]
        return argv

    def argv(self, ctx: Mode1Context) -> list[str]:
        cg, rd = X.CODEGRAPH.locate(ctx), X.READING.locate(ctx)
        return self.terms_argv(sys.executable, ctx.root, ctx.repo,
                               cg if os.path.exists(cg) else None,
                               rd if os.path.exists(rd) else None)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]
