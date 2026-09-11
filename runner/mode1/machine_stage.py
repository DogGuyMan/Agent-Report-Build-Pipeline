"""자식 프로세스 하나를 띄우는 Mode 1 단계의 베이스. 대상 저장소가 작업 폴더다."""
import os

import pipeline as P
from mode1.context import Mode1Context


class Mode1Machine(P.MachineStage[Mode1Context]):
    """자식 프로세스 하나. 대상 저장소가 작업 폴더다."""

    def cwd(self, ctx: Mode1Context) -> str:
        return ctx.repo

    @staticmethod
    def wiki_argv(python: str, root: str, script: str, repo: str) -> list[str]:
        """`runner/wiki/*.py` 하나를 부른다."""
        return [python, os.path.join(root, "runner", "wiki", script), repo]
