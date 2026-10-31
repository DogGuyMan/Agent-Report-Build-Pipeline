"""`seal-artifacts`. 이 실행에서 검사를 통과하고 지금 소스를 다시 읽은 산출물을 docs/codegraph 에 봉인한다."""
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import msgspec

import pipeline as P
from manifest import ArtifactManifest
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured


class SealArtifactsStage(Measured, Mode1Machine):
    """`machine/manifest.py seal` 을 부른다. 싣는 종류는 `ctx.verified` 이고, 비었으면 부르지 않고 실패 행 하나로 `FAIL` 이다."""
    name = "seal-artifacts"

    @staticmethod
    def producer_commit(root: str) -> str:
        """봉인한 도구의 판. git 밖이면 `unknown`."""
        r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else "unknown"

    @staticmethod
    def mark_superseded(repo: str, stage: str, producer_commit: str) -> bool:
        """실패한 실행 뒤 **이전 봉인**에 표식을 적는다. 봉인이 없거나 계약 꼴이 아니면 False. 봉인 자체는 새로 쓰지 않는다."""
        path = os.path.join(repo, "docs", "codegraph", "manifest.json")
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "rb") as f:
                doc = msgspec.json.decode(f.read(), type=ArtifactManifest)
        except msgspec.DecodeError:
            return False
        doc["superseded_by"] = {"stage": stage, "producer_commit": producer_commit,
                                "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with open(path, "wb") as f:
            f.write(msgspec.json.format(msgspec.json.encode(doc), indent=2))
        return True

    def argv(self, ctx: Mode1Context) -> list[str]:
        return [sys.executable, os.path.join(ctx.root, "machine", "manifest.py"), "seal", ctx.repo,
                "--kinds", ",".join(sorted(ctx.verified)),
                "--producer-commit", self.producer_commit(ctx.root)]

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.TERMS_DB, X.LANG_SELECT, X.SNAPSHOT]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.MANIFEST]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if not ctx.verified:
            why = "봉인할 것이 없다 — 이 실행에서 verify-terms 나 verify-wiki 가 통과하지 않았다"
            return P.Outcome(P.FAIL, why, [self.row(time.monotonic(), False, why)])
        return super().perform(ctx)
