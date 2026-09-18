"""`collect-graph` · `schedule-batches`. 코드 지도를 만들고 층과 배치로 나눈다."""
import json
import os
import sys
import time
from typing import cast

import pipeline as P
import survey_plan
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured


class CollectGraphStage(Mode1Machine):
    """정적 수집 → 코드 지도. 전량이면 `--force`, 증분이면 `--diff changes.json`."""
    name = "collect-graph"

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = self.wiki_argv(sys.executable, ctx.root, "prep.py", ctx.repo)
        if ctx.cold:
            argv.append("--force")
        else:
            argv += ["--diff", X.CHANGES.locate(ctx)]
        return argv

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [] if ctx.cold else [X.CHANGES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH]


class ScheduleBatchesStage(Measured, P.Stage[Mode1Context]):
    """코드 지도를 배치로. 층 전략은 위상 층으로 나누고 증분이면 diff 의 `targets` 로 좁힌다.
    파일 전략은 파일 하나가 배치 하나이고 가중치 순이며 우선순위 CSV 를 함께 낸다. LLM 을 부르지 않는다."""
    name = "schedule-batches"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH] + ([] if ctx.cold else [X.CHANGES])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.BATCHES] + ([X.FILE_PRIORITY] if ctx.strategy == "file" else [])

    @staticmethod
    def plan_summary(plan: survey_plan.SurveyPlan) -> list[str]:
        """층·배치 수를 줄 목록으로. `--dry-run` 과 `schedule-batches` 단계가 같은 글을 쓴다."""
        out: list[str] = []
        for L in plan.get("layers", []):
            if L.get("kind") == "non-node":
                out.append("  층%d — 비노드 용어 (한 세션)" % L["level"])
            elif plan.get("target") == 0:      # 파일 계획 — 층이 하나고 배치가 곧 파일이다
                out.append("  파일 %d · 배치 %d · 심볼 %d (가중치 순, 장벽 없음)"
                           % (len(L["batches"]), len(L["batches"]), L["symbol_count"] or 0))
            else:
                n = len(L.get("batches", []))
                # `file_count` 는 비노드 층만 갖지 않는 선택 항목이라 첨자하면 기계가 짚는다.
                # 이 가지는 `kind != "non-node"` 라 늘 있다.
                out.append("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                           % (L["level"], L["symbol_count"],
                              L["file_count"],  # pyright: ignore[reportTypedDictNotRequiredAccess]
                              n))
        총배치 = sum(len(L.get("batches", [])) for L in plan.get("layers", []))
        out.append("  합계 — 심볼 %d · 층 %d · 배치 %d (LLM 세션이 그만큼 뜬다)"
                   % (plan["totals"]["symbols"], plan["totals"]["levels"], 총배치))
        return out

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        # 기계축 선언(`CodeGraph`)이 실물과 어긋나 최상위만 검증하고 넘길 때 `cast` 한다.
        cg = cast(survey_plan.CodeGraph, P.load(X.CODEGRAPH.locate(ctx), X.CodeGraphDoc))
        only = None if ctx.cold else ctx.targets
        if ctx.strategy == "file":
            ctx.plan = survey_plan.plan_by_file(cg)
            with open(X.FILE_PRIORITY.locate(ctx), "w", encoding="utf-8") as f:
                f.write(survey_plan.weights_csv(survey_plan.file_weights(cg)))
            print(X.FILE_PRIORITY.locate(ctx))
        else:
            ctx.plan = survey_plan.plan(cg, ctx.target, only_files=only)
        out_path = X.BATCHES.locate(ctx)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ctx.plan, f, ensure_ascii=False, indent=1)
        print("%s%s" % (out_path, " (증분: %d파일)" % len(only) if only else ""))
        for line in self.plan_summary(ctx.plan):
            print(line)
        return P.Outcome(P.OK, "", [self.row(t0, True)])
