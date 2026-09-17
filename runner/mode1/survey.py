"""`annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다."""
import json
import os
import sys
import time
from collections.abc import Mapping, Sequence
import pipeline as P
import survey_plan
from mode1 import context as X
from mode1 import diff as D
from mode1.context import ROOT, Mode1Context, Record, Records
from mode1.measured import Measured


class AnnotateSymbolsStage(Measured, P.LlmStage[Mode1Context]):
    """배치 하나 = 세션 하나. 층 사이에 이어지는 값(`baseline` · `merged`)은 **문맥 칸**에 둔다."""
    name = "annotate-symbols"
    emits = P.OK | P.FAIL | P.SKIP

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""   # jobs 가 배치마다 만든다. 단일 프롬프트는 쓰이지 않는다

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.BATCHES] + ([] if ctx.cold else [X.CHANGES])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.READING]

    # ── 자리 ────────────────────────────────────────────────────────────

    @staticmethod
    def shard_dir(ctx: Mode1Context) -> str:
        return os.path.join(X.raw_dir(ctx), "_shards")

    # ── 프롬프트 넷 ─────────────────────────────────────────────────────

    @staticmethod
    def warmup_section(targets: Sequence[str] | None, total: int, repo: str = "") -> str:
        """프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다.

        ⚠ **이 글은 부르는 쪽이 `.format()` 을 돌린 뒤에 이어 붙는다.** 그래서 중괄호
        자리표시자를 남기면 안 되고, 저장소 경로를 `repo` 로 받아 여기서 박아 넣는다.

        붙는 곳은 **전수조사 배치 프롬프트뿐**이다. 위키 쪽 범위는 `wiki_page_prompt` 가
        페이지 목록으로 따로 준다.
        """
        if not targets:
            return ""
        목록 = "\n".join("  " + t for t in targets)
        return ("\n## 범위 — 증분 조사다. 저장소 전량을 읽지 마라\n"
                "\n"
                "지난 조사 결과가 %s 에 이미 있다. 그중\n"
                "**아래 %d개 파일에 걸린 레코드만** 다시 만든다. 추적 파일 %d개 중 %d개다.\n"
                "\n%s\n"
                "\n"
                "- **이 목록에 없는 파일은 읽지 마라.** 나머지 레코드는 그대로 살아 있고, 손대면 안 된다.\n"
                "- 목록 밖의 이름이 필요하면 소스가 아니라 **기존 terms-reading.json 과 codegraph.json**\n"
                "  을 근거로 쓴다.\n"
                "- 목록의 파일이 사라졌거나 읽을 수 없으면 **지어내지 말고** 보고에 적는다.\n"
                % (X.reading_path(repo, ROOT), len(targets), total, len(targets), 목록))

    @staticmethod
    def dep_excerpt(merged: Mapping[str, Mapping[str, object]],
                    batch: survey_plan.PlanBatch) -> str:
        """배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다.

        아직 레코드가 없는 이름은 아예 뺀다 — 없는 것을 가리키면 세션이 그 자리를 추론으로 메운다.

        읽기만 하므로 `Records` 가 아니라 `Mapping` 을 받는다 — `dict` 는 값 형이 고정이라
        `dict[str, dict[str, str]]` 같은 더 좁은 사전을 그대로 넘길 수 없다.
        """
        want = sorted({d for s in batch.get("symbols", []) for d in s.get("depends_on", [])})
        lines = ["  - %s — %s" % (k, (merged[k] or {}).get("means") or "(뜻 없음)")
                 for k in want if k in merged]
        return "\n".join(lines)

    @staticmethod
    def survey_batch_prompt(repo: str, root: str, batch: survey_plan.PlanBatch,
                            dep_records: str, targets: Sequence[str] | None = None,
                            total: int = 0) -> str:
        """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

        `dep_records` 는 `dep_excerpt` 가 낸 아래층 발췌다.

        `targets` 는 warmup 이 판정한 다시 읽을 파일 목록이다. 있으면 **증분 조사**라는 뜻이라
        `warmup_section` 이 만든 범위 지시문을 뒤에 붙인다. `None` 이면 전량 조사다.
        """
        syms = "\n".join(
            "  - %s (%s) %s:%s   의존 -> %s"
            % (s["name"], s["kind"], s["file"], s["line"],
               ", ".join(s.get("depends_on") or []) or "없음")
            for s in batch["symbols"])
        return """\
너는 코드베이스 전수조사의 배치 {bid} 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 너보다 아래층은 이미 끝났다 — 다시 조사하지 마라

{deps}

## 네가 맡은 심볼 {n}개 — 이것만 한다

{syms}

## 읽는 법 — 순서를 지킨다

1. 담당 파일마다 통독 캐시를 먼저 본다:
     {root}/.venv/bin/python {root}/machine/file_cache.py get {repo} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 남긴다:
     {root}/.venv/bin/python {root}/machine/file_cache.py put {repo} <파일경로> <개요json>
     개요 꼴 — 심볼마다 {{name, kind, line, end_line, signature, one_line}} 에
     파일의 imports 와 head_comment 를 더한 객체.
2. **네 심볼은 캐시로 때우지 않는다.** 반드시 그 줄 범위를 실제로 읽는다.
   캐시는 남의 심볼을 uses[].to 로 가리킬 때만 쓴다.

## 레코드 계약

{{kind, module, where, means, does, uses[], confidence, source:"reading"}}
- where = `경로:줄` (필수. 기계가 L1 파일 / L2 줄 / L3 근처에 이름 으로 검사한다)
- means = 무엇인가, 한 문장. **객체지향을 갓 배운 대학 1학년 눈높이.** 어려운 용어로 설명하지 않는다
- does  = 무엇을 하는가, 한두 문장
- uses[] = {{to, kind, label, where}}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
- confidence = HIGH(코드를 읽고 썼다) / MEDIUM(일부 읽고 나머지는 추론) / LOW(이름·구조에서 추론)
  **전부 HIGH 로 적으면 그 칸이 장식이 된다.**

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 함수를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "…에 연결될 것 같다"    -> import 나 호출을 실제로 따라간다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 쓰는 곳 — 여기 말고 아무 데도 쓰지 않는다

  {repo}/out/codegraph-raw/_shards/{bid}.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 열지도 고치지도 않는다.** 지금 다른 배치들이 동시에 돌고 있다.
키가 다른 파일과 겹칠 것 같아도 **네가 고치지 않는다** — 층이 끝날 때 일괄 해소된다. 보고에 적기만 한다.
**커밋하지 않는다.**

## 끝내기 전에

- 심볼 {n}개에 레코드가 {n}개 있는가
- where 의 줄 번호를 실제로 열어 확인했는가
- confidence 가 전부 HIGH 는 아닌가
- 샤드 파일 하나만 만들었는가

보고: 레코드 수 · confidence 분포 · 통독한 파일과 캐시로 때운 파일 · 키 충돌 후보 · 읽지 못한 것과 이유.
""".format(repo=repo, root=root, bid=batch["id"], n=len(batch["symbols"]),
               syms=syms, deps=dep_records or "  (없음 — 너는 최하층이다)") \
            + AnnotateSymbolsStage.warmup_section(targets, total, repo)

    @staticmethod
    def nonnode_prompt(repo: str, root: str) -> str:
        """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

        이것들은 코드 지도의 노드가 아니라 층 축이 없다. 대신 심볼 레코드가 재료다 —
        **심볼 층이 하나라도 남아 있으면 이 세션을 띄우면 안 된다.**
        """
        return """\
너는 코드베이스 전수조사의 **마지막 층** 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 심볼은 이미 전부 끝났다

  {reading}   앞선 층들이 합쳐 놓은 심볼 레코드

이 파일을 **읽기만** 한다. 고치지 않는다.

## 네가 맡은 것 — 코드 지도의 노드가 아닌 용어 다섯 종류

| kind | 무엇 | where 는 어디 |
|---|---|---|
| `file` | 소스 파일 하나 | `경로:1` |
| `module` | 디렉토리 하나 | 없어도 된다 |
| `artifact` | 이 저장소가 **만들어 내는** 파일 | 그 파일을 **쓰는** 줄 |
| `key` | 설정·JSON 의 이름난 칸 | 그 키를 **채우는** 줄 |
| `concept` | 코드에 글자로 있는 낱말 | 그 낱말이 있는 줄 |

**`file` `module` `artifact` `key` `concept` 는 이름이 그 줄에 글자 그대로 있어야 한다** —
기계가 L3(근처에 그 이름) 으로 검사한다.

`file` 레코드는 **그 파일 안 심볼들의 완성된 means/does 를 재료로** 쓴다. 다시 통독하지 않는다.
`concept` 은 **코드에 글자로 없는 것을 만들지 않는다** — 계획서에만 있는 개념은 여기 싣지 않는다.

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 자리를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 레코드 계약과 쓰는 곳

{{kind, module, where, means, does, uses[], confidence, source:"reading"}} 이고
쓰는 곳은 **여기 하나뿐**이다:

  {repo}/out/codegraph-raw/_shards/NONNODE.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 고치지 않는다. 커밋하지 않는다.**

보고: 종류별 레코드 수 · confidence 분포 · 근거를 못 찾아 뺀 것과 이유.
""".format(repo=repo, root=root, reading=X.reading_path(repo, ROOT))

    # ── 레코드 — 읽기 · 샤드 병합 · 계획과 diff 의 대조 ──────────────────

    @staticmethod
    def load_records(path: str) -> Records:
        """있으면 읽어 사전으로 좁혀 내고, 없거나 사전이 아니면 `{}`."""
        return P.load(path, Records) if os.path.exists(path) else {}

    @staticmethod
    def merge_shards(shard_dir: str, existing: Records | None) -> Records:
        """샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.**

        배치 세션은 자기 배치만 보므로 전역을 보는 것은 이 함수뿐이다 — 겹치면 겹친 **전원**을
        `<파일줄기>.<이름>` 으로 고친다. 한쪽만 한정하면 나중에 또 겹친다.

        **망가진 샤드는 건너뛴다.** 배치 하나가 반쯤 쓰고 죽어도 나머지 결과를 버리지 않는다.
        무엇을 건너뛰었는지는 stderr 에 적는다.

        ⚠ **`existing` 에는 누적본이 아니라 조사 이전의 원본을 준다.** 이 함수는 층마다 불리고
        그때마다 샤드 전부를 다시 읽는다. 누적본을 넘기면 이미 합쳐 둔 레코드를 **자기 자신과의
        충돌**로 보고 개명해 레코드 수가 줄어든다. 샤드가 원본이고 이 함수는 그 순수 함수다.

        충돌 판정에 `!=` 를 쓰는 것도 같은 이유다. `is not` 은 같은 샤드를 다시 읽은 새 객체를
        남으로 본다.
        """
        got = dict(existing or {})
        if not os.path.isdir(shard_dir):
            return got
        for fname in sorted(os.listdir(shard_dir)):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(shard_dir, fname), encoding="utf-8") as f:
                    shard: Records = json.load(f)
            except (ValueError, OSError) as ex:
                print("샤드를 건너뛴다 — %s: %s" % (fname, ex), file=sys.stderr)
                continue
            for key, rec in shard.items():
                # 자리 주인이 남(다른 파일)일 때만 충돌이다. 같은 파일이면 다시 읽은 새 판이라 갈아 끼운다.
                if key in got and got[key] != rec \
                        and AnnotateSymbolsStage.file_of(got[key]) != AnnotateSymbolsStage.file_of(rec):
                    # 겹친 전원을 개명한다. 이미 들어와 있던 쪽도 함께 고친다.
                    old = got.pop(key)
                    got[AnnotateSymbolsStage.qualified(key, old)] = old
                    got[AnnotateSymbolsStage.qualified(key, rec)] = rec
                else:
                    got[key] = rec
        return got

    @staticmethod
    def file_of(rec: Record | None) -> str:
        """`where` 의 파일 부분. 없으면 빈 글."""
        return str((rec or {}).get("where") or "").split(":")[0]

    @staticmethod
    def qualified(key: str, rec: Record | None) -> str:
        """`<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다."""
        stem = os.path.splitext(os.path.basename(AnnotateSymbolsStage.file_of(rec)))[0]
        return "%s.%s" % (stem, key) if stem else key

    @staticmethod
    def plan_files(plan: survey_plan.SurveyPlan) -> set[str]:
        """계획에 든 배치들이 가리키는 파일 집합."""
        return {f for layer in plan["layers"] for batch in layer["batches"] for f in batch["files"]}

    @staticmethod
    def compare_plan(plan: survey_plan.SurveyPlan, d: D.WarmupDiff) -> list[str]:
        """계획과 diff 가 같은 범위를 말하는지 양방향으로 본다. 불평 목록을 낸다.

        넓으면 전량 지시서에 부분 쪽지가 붙은 것이고, 좁으면 부분 지시서에 전량 쪽지가
        붙은 것이다. 두 번째가 더 위험하다 — 레코드가 조용히 빈다.
        `targets` 가 있을 때 "좁다" 는 잡지 않는다 — 좁힌 계획은 `targets` 의 부분집합일 수 있다.
        """
        have = AnnotateSymbolsStage.plan_files(plan)
        want = set(d["targets"]) if d["targets"] is not None else D.all_files(d)
        out: list[str] = []
        wider = have - want
        if wider:
            out.append("계획이 diff 보다 넓다 — diff 밖의 파일 %d개: %s" % (len(wider), sorted(wider)[:5]))
        if d["targets"] is None and want - have:
            out.append("계획이 diff 보다 좁다 — 전량인데 빠진 파일 %d개" % len(want - have))
        return out

    # ── 층 돌기 ─────────────────────────────────────────────────────────

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.plan is None:
            ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
            print("층 계획을 디스크에서 읽었다 — %s" % X.BATCHES.locate(ctx), flush=True)
        if not ctx.cold:
            d = D.read_diff(X.CHANGES.locate(ctx))
            if d is None:
                why = "changes.json 을 읽지 못했다"
                return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
            bad = self.compare_plan(ctx.plan, d)
            if bad:
                why = "계획이 diff 와 어긋난다: " + "; ".join(bad)
                return P.Outcome(P.FAIL, why, [self.row(t0, False, why)])
            ctx.targets, ctx.tracked_n = d["targets"], d["tracked"]
            if d["targets"] is not None and not d["targets"] and os.path.exists(X.READING.locate(ctx)):
                ctx.survey_ok = True    # 읽을 것이 없고 지난 레코드가 살아 있다 — 지문을 찍어도 된다
                row = self.row(t0, True, "바뀐 파일 0개 — 지난 조사 결과를 그대로 쓴다")
                row["skipped"] = True
                return P.Outcome(P.SKIP, row["why"], [row])
        n_sessions = sum(len(L.get("batches", [])) or 1 for L in ctx.plan["layers"])
        print("조사 세션 예상 %d개 (층 %d)" % (n_sessions, len(ctx.plan["layers"])), flush=True)
        os.makedirs(self.shard_dir(ctx), exist_ok=True)
        ctx.baseline = self.load_records(X.READING.locate(ctx))
        ctx.merged = dict(ctx.baseline)
        out = super().perform(ctx)
        ctx.survey_ok = out.kind == P.OK    # 층이 0개면 harvest 가 안 불리므로 여기서 정한다
        return out

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.plan["layers"]) if ctx.plan else 0

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        assert ctx.plan is not None
        layer = ctx.plan["layers"][rnd]
        if layer.get("kind") == "non-node":
            jobs = [("NONNODE", self.nonnode_prompt(ctx.repo, ctx.root))]
        else:
            jobs = [(b["id"], self.survey_batch_prompt(ctx.repo, ctx.root, b,
                                                       self.dep_excerpt(ctx.merged, b),
                                                       ctx.targets, ctx.tracked_n))
                    for b in layer["batches"]]
        # 샤드가 이미 있는 배치는 건너뛴다 — 다시 돌리면 실패한 배치만 돈다.
        return [(bid, pr) for bid, pr in jobs
                if not os.path.exists(os.path.join(self.shard_dir(ctx), bid + ".json"))]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "annotate-symbols/" + row["stage"]
        ctx.merged = self.merge_shards(self.shard_dir(ctx), ctx.baseline)
        path = X.READING.locate(ctx)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx.merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("  층 끝 — 레코드 %d개" % len(ctx.merged), flush=True)
        return out
