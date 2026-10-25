"""`annotate-symbols` 의 파일 전략. 파일 하나가 세션 하나, 가중치 순, 장벽 없는 풀.

`LlmStage.perform` 의 라운드 틀로는 "끝난 파일이 생길 때마다 2패스를 넣는" 흐름이 안 되므로
이 단계만 `perform` 을 갖는다. 세션 호출·측정(`P.run_agent_with`)·프롬프트·검문·병합은
전부 `AnnotateSymbolsStage` 것을 그대로 부른다.
"""
import json
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait

import measure as M
import pipeline as P
import survey_plan
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.survey import AnnotateSymbolsStage

AgentRun = tuple[float, int, M.ClaudeResult | None]


class AnnotateFilesStage(AnnotateSymbolsStage):
    """완료 콜백이 있는 풀. 끝난 세션마다 검문·병합·미해결 표·2패스 투입을 한다.

    2패스는 `shallow` 레코드가 있고, 그 심볼이 다른 파일에서 쓰이고(into > 0), 기다리던 의존 대상이
    전부 병합에 들어온 파일에만 건다 — into 큰 순. 아무도 안 쓰는 심볼은 얕은 채로 둔다.
    """

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.RECORD_SCHEMA, X.READING, X.UNRESOLVED]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.plan is None:
            ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
        plan = ctx.plan
        cg = P.load(X.CODEGRAPH.locate(ctx), X.CodeGraphDoc)
        nodes = {str(n.get("id")): n for n in cg["nodes"]}
        into = self.into_of(cg)
        name_of = self.name_of(plan)
        batches = {b["id"]: b for L in plan["layers"] for b in L.get("batches", [])}
        weight = {b["files"][0]: b.get("weight", 0.0) for b in batches.values() if b["files"]}
        d = self.shard_dir(ctx)
        os.makedirs(os.path.join(d, "_pass2"), exist_ok=True)
        self.write_schema(X.RECORD_SCHEMA.locate(ctx))
        ctx.baseline = self.load_records(X.READING.locate(ctx))
        ctx.merged = self.merge_shards(d, ctx.baseline)
        has_nonnode = any(L.get("kind") == "non-node" for L in plan["layers"])
        print("조사 세션 예상 %d개 (파일 %d + 비노드 %d · 2패스는 표가 정한다)"
              % (len(batches) + int(has_nonnode), len(batches), int(has_nonnode)), flush=True)

        rows: list[M.StageRow] = []
        queued: set[str] = set()          # 2패스를 넣은 배치 id
        failed = False
        pool = ThreadPoolExecutor(max_workers=max(1, ctx.concurrency))
        running: dict[Future[AgentRun], str] = {}

        def submit(label: str, prompt: str) -> None:
            fut = pool.submit(P.run_agent_with, self.model(ctx), ctx.repo, ctx.root, prompt, ctx.timeout, label)
            running[fut] = label

        def write_merged() -> None:
            ctx.merged = self.merge_shards(d, ctx.baseline)
            os.makedirs(os.path.dirname(X.READING.locate(ctx)), exist_ok=True)
            with open(X.READING.locate(ctx), "w", encoding="utf-8") as f:
                json.dump(ctx.merged, f, ensure_ascii=False, indent=1, sort_keys=True)
            table = self.unresolved_rows(ctx.merged, weight, into, known=set(ctx.merged), queued=queued)
            with open(X.UNRESOLVED.locate(ctx), "w", encoding="utf-8") as f:
                f.write(self.unresolved_csv(table))

        def hot_keys(bid: str) -> list[str]:
            """이 배치에서 다듬을 가치가 있는 얕은 레코드 — shallow 가 있고 into > 0."""
            return [k for k in (s["name"] or "" for s in batches[bid]["symbols"])
                    if k in ctx.merged and self.shallow_of(ctx.merged[k]) and into.get(k, 0) > 0]

        def pass2_candidates() -> list[str]:
            score: dict[str, int] = {}
            for bid in batches:
                if bid in queued or not os.path.exists(os.path.join(d, bid + ".json")):
                    continue
                hot = hot_keys(bid)
                if hot and all(dep in ctx.merged for k in hot for dep in self.shallow_of(ctx.merged[k])):
                    score[bid] = max(into[k] for k in hot)
            return sorted(score, key=lambda b: (-score[b], b))

        def submit_pass2(bid: str) -> None:
            queued.add(bid)
            shallow = {k: ctx.merged[k] for k in hot_keys(bid)}
            deps = {dep: ctx.merged[dep] for r in shallow.values() for dep in self.shallow_of(r) if dep in ctx.merged}
            submit(bid + "/p2", self.pass2_prompt(ctx.repo, ctx.root, bid, batches[bid]["files"][0], shallow, deps))

        def on_done(label: str, got: AgentRun) -> None:
            nonlocal failed
            seconds, rc, result = got
            ok, why = M.agent_verdict(rc, result)
            bid, is_p2 = (label[:-3], True) if label.endswith("/p2") else (label, False)
            if ok and is_p2:
                faults = self.apply_pass2(d, bid)
                if faults:
                    ok, why = False, "2패스가 틀렸다 — " + faults[0]["kind"]
                    for f in faults:
                        print("[%s] 2패스가 틀렸다 %s" % (label, self.fault_line(f)), file=sys.stderr)
            elif ok and bid in batches:
                one: survey_plan.SurveyPlan = {"target": 0, "totals": plan["totals"], "layers": [
                    {"level": 0, "symbol_count": None, "batches": [batches[bid]]}]}
                faults = self.check_shards(d, one).get(bid, [])
                if faults:
                    for f in faults:
                        print("[%s] 샤드가 틀렸다 %s" % (bid, self.fault_line(f)), file=sys.stderr)
                    self.quarantine(d, bid, faults)
                    ok, why = False, "샤드 격리 — " + faults[0]["kind"]
            failed = failed or not ok
            rows.append({"stage": "annotate-symbols/" + label, "seconds": seconds,
                         "usage": M.normalize_usage(result), "ok": ok, "why": why})
            write_merged()
            for cand in pass2_candidates():
                submit_pass2(cand)
            print("  [%s] %s — 레코드 %d개 · 돌고 있는 것 %d" % (label, "성공" if ok else "실패",
                                                             len(ctx.merged), len(running)), flush=True)

        def drain() -> None:
            while running:
                done, _ = wait(list(running), return_when=FIRST_COMPLETED)
                for fut in done:
                    label = running.pop(fut)
                    try:
                        got = fut.result()
                    except Exception as ex_:                       # noqa: BLE001 — 풀을 살린다
                        print("[%s] 세션이 터졌다: %s" % (label, ex_), file=sys.stderr)
                        got = (0.0, -1, None)
                    on_done(label, got)

        with M.Heartbeat(self.name):
            for bid, b in batches.items():          # 계획 순 = 가중치 순
                if os.path.exists(os.path.join(d, bid + ".json")):
                    continue
                prompt = self.survey_batch_prompt(
                    ctx.repo, ctx.root, b, self.dep_excerpt(ctx.merged, b, name_of),
                    pending=self.pending_excerpt(ctx.merged, b, nodes), name_of=name_of, **self.retry_inputs(d, bid))
                submit(bid, prompt)
            drain()
            if not failed and has_nonnode and not os.path.exists(os.path.join(d, "NONNODE.json")):
                submit("NONNODE", self.nonnode_prompt(ctx.repo, ctx.root))
                drain()
        pool.shutdown(wait=True)

        out = P.Outcome(P.FAIL if failed else P.OK, "세션이 실패했다" if failed else "", rows)
        if out.kind == P.OK:
            out = self.sweep(ctx, out)
        ctx.survey_ok = out.kind == P.OK
        print("  파일 조사 끝 — %s" % M.hms(time.monotonic() - t0), flush=True)
        return out
