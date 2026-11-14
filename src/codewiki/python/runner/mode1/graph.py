"""`collect-graph` · `verify-graph` · `derive-facts` · `schedule-batches`. 코드 지도를 만들고 검사한 뒤 파생물과 층 · 배치를 낸다."""
import hashlib
import os
import sys
import time
from collections import Counter
from typing import cast

import msgspec

from core import pipeline as P
import jsonio
import survey_plan
import verify_graph
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine
from mode1.measured import Measured


class GraphFaultReport(P.PromptResource):
    """결함 문서를 쓰고 핸드오프를 렌더하는 믹스인. `collect-graph` · `verify-graph` 가 쓴다. 템플릿 이름은 단계 이름이다."""
    prompt_dir = X.PROMPT_DIR
    EXAMPLES = 5
    name: str

    def write_faults(self, ctx: Mode1Context, doc: verify_graph.VerifyDoc) -> str:
        """결함 문서를 쓰고 성공 기록을 지운다 — 두 파일이 함께 남지 않는다."""
        verified = X.GRAPH_VERIFIED.locate(ctx)
        if os.path.exists(verified):
            os.remove(verified)
        path = X.GRAPH_FAULTS.locate(ctx)
        jsonio.write_json_atomic(path, doc, indent=1, trailing_newline=True)
        return path

    def write_handoff(self, ctx: Mode1Context, doc: verify_graph.VerifyDoc, **extra: object) -> str:
        """코드별로 묶어 많은 순, 예시는 `EXAMPLES` 개까지. 절 이름도 함께 — 어디를 볼지 말한다. `extra` 는 단계 템플릿이 더 받는 값이다."""
        counts = Counter(f["code"] for f in doc["faults"])
        groups: list[dict[str, object]] = []
        for code, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            layer = verify_graph.LAYER[code]
            groups.append({"code": code, "layer": layer, "section": verify_graph.SECTION_OF_LAYER[layer], "count": n,
                           "examples": [f for f in doc["faults"] if f["code"] == code][:self.EXAMPLES]})
        text = self.load_prompt(self.name, repo=ctx.repo, total=doc["total"], groups=groups,
                                checks_run=" · ".join(doc["checks_run"]) or "없음", fit=doc["fit"]["survey"], **extra)
        path = X.GRAPH_HANDOFF.locate(ctx)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


class CollectGraphStage(GraphFaultReport, Mode1Machine):
    """정적 수집 → 코드 지도. 전량이면 `--force`, 증분이면 `--diff changes.json`. 수집 · 정제만 한다(`--collect-only`).
    prep 이 죽으며 남긴 `collect-failure.json` 은 결함 문서와 핸드오프로 옮겨 멈춘다."""
    name = "collect-graph"
    prompt_names = ("collect-graph",)

    def argv(self, ctx: Mode1Context) -> list[str]:
        argv = self.wiki_argv(sys.executable, ctx.root, "prep.py", ctx.repo) + ["--collect-only"]
        if ctx.cold:
            argv.append("--force")
        else:
            argv += ["--diff", X.CHANGES.locate(ctx)]
        return argv

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [] if ctx.cold else [X.CHANGES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH, X.COLLECT_FINGERPRINT, X.NORMALIZE_REPORT, X.SOURCE_INVENTORY]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        out = super().perform(ctx)
        handoff = X.GRAPH_HANDOFF.locate(ctx)
        if out.kind == P.OK:
            if os.path.exists(handoff):
                os.remove(handoff)
            return out
        failure_path = X.COLLECT_FAILURE.locate(ctx)
        if not os.path.exists(failure_path):
            return out                         # prep 이 기록을 남기지 못하고 죽었다 — 종료 코드가 이유다
        failure = P.load(failure_path, verify_graph.FailureDoc)
        doc = verify_graph.failure_doc(failure)
        self.write_faults(ctx, doc)
        handoff = self.write_handoff(ctx, doc, step=failure["step"], returncode=failure["returncode"],
                                     stderr_tail=failure["stderr_tail"])
        why = "수집 실패 — %s (종료 %d) — %s" % (failure["step"], failure["returncode"], handoff)
        for row in out.rows:
            row["why"] = why
        return P.Outcome(P.FAIL, why, out.rows)


class VerifyGraphStage(GraphFaultReport, Mode1Machine):
    """코드 지도를 LLM 단계 앞에서 검사한다. 결함이 있으면 결함 JSON 옆에 핸드오프를 남기고 멈춘다."""
    name = "verify-graph"
    prompt_names = ("verify-graph",)

    def argv(self, ctx: Mode1Context) -> list[str]:
        return [sys.executable, os.path.join(ctx.root, "src", "codewiki", "python", "machine", "verify_graph.py"),
                X.CODEGRAPH.locate(ctx), "--repo", ctx.repo, "--manifest", X.COLLECT_FINGERPRINT.locate(ctx),
                "--report", X.NORMALIZE_REPORT.locate(ctx), "--inventory", X.SOURCE_INVENTORY.locate(ctx),
                "--failure", X.COLLECT_FAILURE.locate(ctx),
                "--faults", X.GRAPH_FAULTS.locate(ctx), "--passed", X.GRAPH_VERIFIED.locate(ctx)]

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return []          # 없는 지도도 이 단계가 unreadable 로 보고한다

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.GRAPH_VERIFIED]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        out = super().perform(ctx)
        handoff = X.GRAPH_HANDOFF.locate(ctx)
        if out.kind == P.OK:
            if os.path.exists(handoff):
                os.remove(handoff)
            return out
        faults = X.GRAPH_FAULTS.locate(ctx)
        if not os.path.exists(faults):
            return out                         # 검사기 자체가 죽었다 — 종료 코드가 이유다
        doc = P.load(faults, verify_graph.VerifyDoc)
        handoff = self.write_handoff(ctx, doc, codegraph=X.CODEGRAPH.locate(ctx), language=doc["language"] or "?",
                                     source_tool=doc["source_tool"] or "?", repo_commit=doc["repo_commit"] or "?")
        why = "코드 지도 결함 %d건 — %s" % (doc["total"], handoff)
        for row in out.rows:
            row["why"] = why
        return P.Outcome(P.FAIL, why, out.rows)


class VerifiedGraph:
    """검사를 지난 지도만 읽는 단계의 믹스인. 지도 바이트를 한 번 읽어 성공 기록과 파생물에 대조하고 그 바이트를 돌려준다."""

    @staticmethod
    def gate(ctx: Mode1Context, need_batches: bool, need_ranking: bool = False) -> tuple[str, bytes]:
        """막힐 이유(빈 문자열이면 통과)와 지금 지도의 바이트. 해시를 낸 바이트를 그대로 파싱해야 바꿔 끼우기 경쟁이 없다.

        `need_batches` 면 `batches.json` 이 지금 지도의 지문과 성공 기록의 generation 을 갖는지도 본다.
        `need_ranking` 이면 `ranking.json` 이 성공 기록의 generation 을 갖는지도 본다.
        """
        verified = X.GRAPH_VERIFIED.locate(ctx)
        if not os.path.exists(verified):
            return "성공 기록이 없다 — verify-graph 부터 돌린다", b""
        doc = P.load(verified, X.GraphVerifiedDoc)
        fit = doc["fit"]
        if fit.get("survey") != "ready":
            blocked = fit.get("blocked_by")
            names = [str(x) for x in cast(list[object], blocked)] if isinstance(blocked, list) else []
            return "성공 기록이 전수조사에 맞지 않는다 — %s" % ", ".join(names), b""
        with open(X.CODEGRAPH.locate(ctx), "rb") as f:
            raw = f.read()
        now = hashlib.sha256(raw).hexdigest()
        if doc["codegraph_sha256"] != now:
            return "검사 뒤에 코드 지도가 바뀌었다 — verify-graph 부터 다시 돌린다", raw
        if need_batches:
            batches = X.BATCHES.locate(ctx)
            if not os.path.exists(batches):
                return "배치가 없다 — schedule-batches 부터 돌린다", raw
            plan = P.load(batches, survey_plan.SurveyPlan)
            if plan.get("codegraph_sha256") != now:
                return "배치가 지금 지도의 것이 아니다 — schedule-batches 부터 다시 돌린다", raw
            if plan.get("generation_id") != doc["generation_id"]:
                return "배치의 generation 이 성공 기록과 다르다 — schedule-batches 부터 다시 돌린다", raw
        if need_ranking:
            ranking = X.RANKING.locate(ctx)
            if not os.path.exists(ranking):
                return "ranking.json 이 없다 — derive-facts 부터 돌린다", raw
            if P.load(ranking, X.RankingDoc)["generation_id"] != (doc["generation_id"] or ""):
                return "ranking.json 의 generation 이 성공 기록과 다르다 — derive-facts 부터 다시 돌린다", raw
        return "", raw


class DeriveFactsStage(VerifiedGraph, Measured, Mode1Machine):
    """검사를 지난 지도에서 facts/*.md · ranking.json · 모듈 그림을 만든다. 지도가 성공 기록과 다르면 돌지 않는다."""
    name = "derive-facts"

    def argv(self, ctx: Mode1Context) -> list[str]:
        return self.wiki_argv(sys.executable, ctx.root, "derive.py", ctx.repo)

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH, X.GRAPH_VERIFIED]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.RANKING]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        why, _ = self.gate(ctx, need_batches=False)
        if why:
            return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
        return super().perform(ctx)


class ScheduleBatchesStage(VerifiedGraph, Measured, P.Stage[Mode1Context]):
    """코드 지도를 배치로. 층 전략은 위상 층으로 나누고 증분이면 diff 의 `targets` 로 좁힌다.
    파일 전략은 파일 하나가 배치 하나이고 가중치 순이며 우선순위 CSV 를 함께 낸다. LLM 을 부르지 않는다."""
    name = "schedule-batches"
    # 진입 알림 한 줄의 꼬리. 멈추는 것은 사람의 Ctrl-C 뿐이고 실행기는 묻지 않는다.
    STOP_TAIL = "  (Ctrl-C 로 멈춤)"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CODEGRAPH, X.GRAPH_VERIFIED] + ([] if ctx.cold else [X.CHANGES])

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
        out.append("  합계 — 심볼 %d · 층 %d · 배치 %d · 전수조사 세션 %d"
                   % (plan["totals"]["symbols"], plan["totals"]["levels"], 총배치,
                      ScheduleBatchesStage.session_count(plan)))
        return out

    @staticmethod
    def session_count(plan: survey_plan.SurveyPlan) -> int:
        """계획이 띄울 전수조사(`annotate-symbols`) 세션 수. 배치가 없는 층(비노드 층)은 한 세션이다. 위키 · 목차 세션은 세지 않는다."""
        return sum(len(L.get("batches", [])) or 1 for L in plan.get("layers", []))

    @staticmethod
    def estimate_line(n_sessions: int, cfg: X.EstimateConfig, full: bool) -> str:
        """`전수조사 세션 N개 · 예상 $lo~hi · 증분|전량`. 범위는 resource/codewiki/config.toml 의 [estimate].

        `full` 은 계획이 diff 로 좁혀지지 않았다는 뜻이다.
        """
        lo = round(n_sessions * cfg["usd_per_batch_min"])
        hi = round(n_sessions * cfg["usd_per_batch_max"])
        return "전수조사 세션 %d개 · 예상 $%d~%d · %s" % (n_sessions, lo, hi, "전량" if full else "증분")

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        why, raw = self.gate(ctx, need_batches=False)
        if why:
            return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
        cg = msgspec.json.decode(raw, type=survey_plan.CodeGraph)
        only = None if ctx.cold else ctx.targets
        if ctx.strategy == "file":
            ctx.plan = survey_plan.plan_by_file(cg)
            with open(X.FILE_PRIORITY.locate(ctx), "w", encoding="utf-8") as f:
                f.write(survey_plan.weights_csv(survey_plan.file_weights(cg)))
            print(X.FILE_PRIORITY.locate(ctx))
        else:
            ctx.plan = survey_plan.plan(cg, ctx.target, only_files=only)
        ctx.plan["codegraph_sha256"] = hashlib.sha256(raw).hexdigest()
        ctx.plan["generation_id"] = P.load(X.GRAPH_VERIFIED.locate(ctx), X.GraphVerifiedDoc)["generation_id"] or ""
        out_path = X.BATCHES.locate(ctx)
        jsonio.write_json_atomic(out_path, ctx.plan, indent=1)
        print("%s%s" % (out_path, " (증분: %d파일)" % len(only) if only else ""))
        for line in self.plan_summary(ctx.plan):
            print(line)
        print(self.estimate_line(self.session_count(ctx.plan), X.load_config()["estimate"], only is None)
              + self.STOP_TAIL)
        return P.Outcome(P.OK, "", [self.row(t0, True)])
