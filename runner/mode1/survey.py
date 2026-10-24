"""`annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다."""
import json
import os
import stat
import sys
import time
from collections.abc import Collection, Mapping, Sequence
from typing import ClassVar, Literal, cast

import msgspec

import pipeline as P
import survey_plan
from mode1 import context as X
from mode1 import diff as D
from mode1.context import (ROOT, FaultKind, Mode1Context, Record, Records, ShardFault, ShardRecords,
                           UnresolvedRow)
from mode1.measured import Measured


class AnnotateSymbolsStage(Measured, P.LlmStage[Mode1Context]):
    """배치 하나 = 세션 하나. 층 사이에 이어지는 값(`baseline` · `merged`)은 **문맥 칸**에 둔다."""
    name = "annotate-symbols"
    emits = P.OK | P.FAIL | P.SKIP
    prompt_dir = X.PROMPT_DIR
    prompt_names = ("annotate-symbols#batch", "annotate-symbols#batch-symbol",
                    "annotate-symbols#batch-symbol-no-deps", "annotate-symbols#batch-dep",
                    "annotate-symbols#batch-dep-no-means", "annotate-symbols#batch-no-deps",
                    "annotate-symbols#scope", "annotate-symbols#pending",
                    "annotate-symbols#retry", "annotate-symbols#nonnode",
                    "annotate-symbols#pass2", "annotate-symbols#pass2-dep", "annotate-symbols#pass2-no-deps")

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""   # jobs 가 배치마다 만든다. 단일 프롬프트는 쓰이지 않는다

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.BATCHES] + ([] if ctx.cold else [X.CHANGES])

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.RECORD_SCHEMA, X.READING, X.DROPPED]

    # ── 자리 ────────────────────────────────────────────────────────────

    @staticmethod
    def shard_dir(ctx: Mode1Context) -> str:
        return os.path.join(X.raw_dir(ctx), "_shards")

    # ── 프롬프트 넷 ─────────────────────────────────────────────────────

    @staticmethod
    def warmup_section(targets: Sequence[str] | None, total: int, repo: str = "") -> str:
        """프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다.

        붙는 곳은 **전수조사 배치 프롬프트뿐**이다. 위키 쪽 범위는 `wiki_page_prompt` 가
        페이지 목록으로 따로 준다.
        """
        if not targets:
            return ""
        목록 = "\n".join("  " + t for t in targets)
        return "\n" + AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#scope", reading=X.reading_path(repo, ROOT), count=str(len(targets)),
            total=str(total), targets=목록)

    @staticmethod
    def name_of(plan: survey_plan.SurveyPlan) -> dict[str, str]:
        """계획 전체의 `id -> name`. `depends_on` 은 노드 id 이고 레코드 키는 이름이라 이 표로 건넌다."""
        return {s["id"]: s["name"] or ""
                for L in plan["layers"] for b in L.get("batches", []) for s in b["symbols"]}

    @staticmethod
    def dep_excerpt(merged: Mapping[str, Mapping[str, object]],
                    batch: survey_plan.PlanBatch, name_of: Mapping[str, str]) -> str:
        """배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다.

        `depends_on` 은 노드 id 다. `name_of` 로 이름을 얻고 그 이름이 `merged` 에 있을 때만 싣는다.
        아직 레코드가 없는 이름은 아예 뺀다 — 없는 것을 가리키면 세션이 그 자리를 추론으로 메운다.

        읽기만 하므로 `Records` 가 아니라 `Mapping` 을 받는다 — `dict` 는 값 형이 고정이라
        `dict[str, dict[str, str]]` 같은 더 좁은 사전을 그대로 넘길 수 없다.
        """
        want = sorted({name_of.get(d, "") for s in batch.get("symbols", []) for d in s.get("depends_on", [])})
        no_means = AnnotateSymbolsStage.load_prompt("annotate-symbols#batch-dep-no-means").removesuffix("\n")
        return "\n".join(
            AnnotateSymbolsStage.load_prompt(
                "annotate-symbols#batch-dep", name=k,
                means=str((merged[k] or {}).get("means") or no_means)).removesuffix("\n")
            for k in want if k and k in merged)

    @staticmethod
    def survey_batch_prompt(repo: str, root: str, batch: survey_plan.PlanBatch,
                            dep_records: str, targets: Sequence[str] | None = None,
                            total: int = 0, pending: str = "",
                            name_of: Mapping[str, str] | None = None) -> str:
        """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

        `dep_records` 는 `dep_excerpt` 가 낸 아래층 발췌다. `pending` 은 `pending_excerpt` 가 낸
        **아직 조사되지 않은** 의존 대상이다 — 비지 않으면 열지 말고 얕게 쓰라는 절이 붙는다.
        `name_of` 는 계획의 `id -> name`. 심볼 줄의 `의존 ->` 를 이름으로 보인다 — 세션은 보이는 것을
        `uses[].to` 에 그대로 베끼므로, id 를 보이면 id 가 레코드에 박힌다.

        `targets` 는 warmup 이 판정한 다시 읽을 파일 목록이다. 있으면 **증분 조사**라는 뜻이라
        `warmup_section` 이 만든 범위 지시문을 뒤에 붙인다. `None` 이면 전량 조사다.
        """
        names = name_of or {}
        no_deps = AnnotateSymbolsStage.load_prompt("annotate-symbols#batch-symbol-no-deps").removesuffix("\n")
        syms = "\n".join(
            AnnotateSymbolsStage.load_prompt(
                "annotate-symbols#batch-symbol", name=str(s["name"]), kind=str(s["kind"]),
                file=str(s["file"]), line=str(s["line"]),
                deps=", ".join(names.get(d, d) for d in (s.get("depends_on") or [])) or no_deps
            ).removesuffix("\n")
            for s in batch["symbols"])
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#batch", repo=repo, root=root, bid=batch["id"], n=str(len(batch["symbols"])),
            syms=syms, deps=dep_records
            or AnnotateSymbolsStage.load_prompt("annotate-symbols#batch-no-deps").removesuffix("\n")) \
            + AnnotateSymbolsStage.pending_section(pending) \
            + AnnotateSymbolsStage.warmup_section(targets, total, repo)

    @staticmethod
    def pending_section(pending: str) -> str:
        """미조사 의존 대상이 있을 때만 붙는 절. 열지 말고 얕게 쓰고 `shallow` 를 표시하라고 시킨다."""
        if not pending:
            return ""
        return "\n" + AnnotateSymbolsStage.load_prompt("annotate-symbols#pending", pending=pending)

    @staticmethod
    def pending_excerpt(merged: Mapping[str, Mapping[str, object]], batch: survey_plan.PlanBatch,
                        nodes: Mapping[str, Mapping[str, object]]) -> str:
        """`depends_on` 중 **아직 레코드가 없는** 것을 `이름 (종류) 파일:줄` 로. 세션이 열지 않고 볼 최소 정보다.

        같은 배치의 심볼은 뺀다 — 세션이 지금 읽는 파일이라 "열지 마라" 가 성립하지 않는다.
        `nodes` 는 `codegraph.json` 의 노드를 id 로 키질한 것이다.
        """
        mine = {s["id"] for s in batch.get("symbols", [])}
        ids = sorted({d for s in batch.get("symbols", []) for d in s.get("depends_on", [])} - mine)
        lines: list[str] = []
        for i in ids:
            n = nodes.get(i)
            if n is None or str(n.get("name") or "") in merged:
                continue
            lines.append("  - %s (%s) %s:%s" % (n.get("name"), n.get("kind"), n.get("file"), n.get("line")))
        return "\n".join(lines)

    @staticmethod
    def nonnode_prompt(repo: str, root: str) -> str:
        """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

        이것들은 코드 지도의 노드가 아니라 층 축이 없다. 대신 심볼 레코드가 재료다 —
        **심볼 층이 하나라도 남아 있으면 이 세션을 띄우면 안 된다.**
        """
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#nonnode", repo=repo, root=root, reading=X.reading_path(repo, ROOT))

    # ── 샤드 검문 — 스키마 파일 · 기계 파서 · 전량 순회 ───────────────────

    WHERE_OPTIONAL = ("module", "external")
    # 결함 표 `faults.toml` — 결함 줄 꼴(`fault_line`) · 갈래마다 고치는 법(`FIX`) · 늘 같은 결함 설명(`fault_detail`).
    FAULTS: ClassVar[X.FaultTable] = X.load_fault_table()
    # 결함 갈래마다 고치는 법 한 줄 — 표의 `fix` 를 렌더한 글. 재조사 프롬프트와 check_shard 명령이 그대로 찍는다.
    FIX: ClassVar[Mapping[FaultKind, str]] = {k: P.PromptResource.render_text(t["fix"])
                                              for k, t in FAULTS["kind"].items()}
    SHARD_EXAMPLE: ShardRecords = {"build_terms": {
        "kind": "function", "module": "machine", "where": "machine/terms_db.py:82",
        "means": "코드 지도에서 용어 사전을 만드는 함수.",
        "does": "노드와 모듈을 돌며 이름 · 종류 · 위치 · 관계를 뽑는다.",
        "uses": [{"to": "_where", "kind": "dependency", "label": "calls", "where": "machine/terms_db.py:110"}],
        "confidence": "HIGH", "source": "reading"}}

    @staticmethod
    def write_schema(path: str) -> None:
        """`ShardRecords` 의 JSON Schema 를 읽기 전용으로 쓴다. 배치 세션이 읽는 견본이자 검문의 형이다.

        이미 있으면 잠시 풀고 다시 쓴다 — 실행마다 형과 같은 글이 있어야 한다.
        """
        doc = dict(msgspec.json.schema(ShardRecords))
        doc["examples"] = [AnnotateSymbolsStage.SHARD_EXAMPLE]
        if os.path.exists(path):
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    @staticmethod
    def fault(kind: FaultKind, batch: str, path: str, at: str, detail: str) -> ShardFault:
        return {"kind": kind, "batch": batch, "path": path, "at": at, "detail": detail,
                "fix": AnnotateSymbolsStage.FIX[kind]}

    @staticmethod
    def fault_detail(kind: FaultKind, name: str = "detail", /, **values: object) -> str:
        """결함 표의 결함 설명 `kind.<갈래>.<name>` 을 `values` 로 렌더한다. 인자가 위치 전용이라 값 이름이 `kind` 여도 된다."""
        return AnnotateSymbolsStage.render_text(AnnotateSymbolsStage.FAULTS["kind"][kind][name], **values)

    @staticmethod
    def check_shard(raw: bytes, batch: str = "", path: str = "") -> list[ShardFault]:
        """샤드 하나의 결함 목록. 문법 → 꼴 → `where` 규칙 순으로 보고, 앞이 틀리면 뒤는 보지 않는다.

        msgspec 은 꼴 오류(`ValidationError`)를 문법 오류(`DecodeError`)의 하위로 낸다 — 좁은 것을 먼저 잡는다.
        """
        F = AnnotateSymbolsStage.fault
        try:
            recs = msgspec.json.decode(raw, type=ShardRecords)
        except msgspec.ValidationError as e:
            detail, _, at = str(e).partition(" - at ")
            return [F("schema", batch, path, at.strip("`"), detail)]
        except msgspec.DecodeError as e:
            detail, _, at = str(e).rpartition(" (")
            return [F("malformed", batch, path, at.rstrip(")"), detail or str(e))]
        return [F("where", batch, path, k, AnnotateSymbolsStage.fault_detail("where", kind=r["kind"]))
                for k, r in recs.items()
                if "where" not in r and r["kind"] not in AnnotateSymbolsStage.WHERE_OPTIONAL]

    @staticmethod
    def fault_line(f: ShardFault) -> str:
        """결함 하나를 사람이 읽을 줄로 — 결함 표의 `line` 꼴. 재조사 절 · stderr · check_shard 명령이 이 줄을 찍는다."""
        return AnnotateSymbolsStage.render_text(AnnotateSymbolsStage.FAULTS["line"], f=f)

    @staticmethod
    def plan_ids(plan: survey_plan.SurveyPlan) -> list[str]:
        """계획이 띄우는 세션의 이름 전부 — 배치 id 들과, 비노드 층이 있으면 `NONNODE`."""
        ids = [b["id"] for L in plan["layers"] for b in L.get("batches", [])]
        return ids + (["NONNODE"] if any(L.get("kind") == "non-node" for L in plan["layers"]) else [])

    @staticmethod
    def check_coverage(raw: bytes, batch: survey_plan.PlanBatch, path: str) -> list[ShardFault]:
        """계획의 심볼 이름과 샤드의 키를 양방향으로 대조한다. 문법·꼴이 맞은 뒤에만 부른다."""
        keys = set(msgspec.json.decode(raw, type=ShardRecords))
        want = {s["name"] or "" for s in batch["symbols"]}
        F = AnnotateSymbolsStage.fault
        not_in_shard = AnnotateSymbolsStage.fault_detail("coverage", "detail-not-in-shard")
        not_in_plan = AnnotateSymbolsStage.fault_detail("coverage", "detail-not-in-plan")
        return ([F("coverage", batch["id"], path, n, not_in_shard) for n in sorted(want - keys)]
                + [F("coverage", batch["id"], path, k, not_in_plan) for k in sorted(keys - want)])

    @staticmethod
    def check_shards(shard_dir: str, plan: survey_plan.SurveyPlan) -> dict[str, list[ShardFault]]:
        """계획의 배치마다 샤드를 찾아 검문한다 — 문법·꼴·where 가 맞으면 coverage 까지. 틀린 것만 `{배치: 결함들}`."""
        bad: dict[str, list[ShardFault]] = {}
        batches = {b["id"]: b for L in plan["layers"] for b in L.get("batches", [])}
        for bid in AnnotateSymbolsStage.plan_ids(plan):
            path = os.path.join(shard_dir, bid + ".json")
            if not os.path.exists(path):
                bad[bid] = [AnnotateSymbolsStage.fault("missing", bid, path, "-",
                                                       AnnotateSymbolsStage.fault_detail("missing"))]
                continue
            with open(path, "rb") as f:
                raw = f.read()
            got = AnnotateSymbolsStage.check_shard(raw, bid, path)
            if not got and bid in batches:              # NONNODE 는 계획 심볼이 없어 대조하지 않는다
                got = AnnotateSymbolsStage.check_coverage(raw, batches[bid], path)
            if got:
                bad[bid] = got
        return bad

    @staticmethod
    def quarantine(shard_dir: str, bid: str, faults: Sequence[ShardFault] = ()) -> str:
        """틀린 샤드를 `.json.bad` 로 옮기고 결함들을 `.json.bad.why` 에 JSON 으로 남긴다.

        `.json` 이 아니라 병합이 안 읽고, `jobs` 가 그 배치를 다시 띄우며 결함을 프롬프트에 싣는다.
        """
        src = os.path.join(shard_dir, bid + ".json")
        dst = src + ".bad"
        if os.path.exists(src):
            os.replace(src, dst)
        if faults:
            with open(dst + ".why", "wb") as f:
                f.write(msgspec.json.format(msgspec.json.encode(list(faults)), indent=1))
        return dst

    @staticmethod
    def load_faults(shard_dir: str, bid: str) -> list[ShardFault]:
        """격리 사유. 없거나 꼴이 틀리면 빈 목록 — 낡은 사유로 재조사를 오도하지 않는다."""
        try:
            return P.load(os.path.join(shard_dir, bid + ".json.bad.why"), list[ShardFault])
        except (OSError, msgspec.DecodeError):
            return []

    @staticmethod
    def clear_quarantine(shard_dir: str, bid: str) -> None:
        """검문을 통과한 배치의 옛 격리 흔적을 치운다. 남기면 다음 재조사가 낡은 오류를 받는다."""
        for suffix in (".json.bad.why", ".json.bad"):
            path = os.path.join(shard_dir, bid + suffix)
            if os.path.exists(path):
                os.remove(path)

    @staticmethod
    def retry_section(shard_dir: str, bid: str) -> str:
        """지난 시도가 격리됐으면 그 결함들을 프롬프트 뒤에 붙일 절. 없으면 빈 글."""
        faults = AnnotateSymbolsStage.load_faults(shard_dir, bid)
        if not faults:
            return ""
        lines = "\n".join("  " + AnnotateSymbolsStage.fault_line(f).replace("\n", "\n  ") for f in faults)
        return "\n" + AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#retry", count=str(len(faults)), faults=lines,
            bad=os.path.join(shard_dir, bid + ".json.bad"))

    # ── 미해결 표 — 얕게 쓴 레코드가 기다리는 의존 대상 ───────────────────

    @staticmethod
    def shallow_of(rec: Mapping[str, object]) -> list[str]:
        """레코드의 `shallow` 를 이름 목록으로 좁힌다. 없거나 목록이 아니면 빈 목록."""
        got = rec.get("shallow")
        if not isinstance(got, list):
            return []
        items: list[object] = list(cast(list[object], got))
        return [str(x) for x in items]

    @staticmethod
    def into_of(cg: X.CodeGraphDoc) -> dict[str, int]:
        """심볼 이름마다 **다른 파일에서** 들어오는 간선 수 — 얕게 쓴 레코드를 다듬을 가치의 척도다."""
        nodes = {str(n.get("id")): n for n in cg["nodes"] if n.get("kind") != "external"}
        got = {str(n.get("name") or ""): 0 for n in nodes.values()}
        for e in cg.get("edges", []):
            s, d = nodes.get(str(e.get("from"))), nodes.get(str(e.get("to")))
            if s is not None and d is not None and s.get("file") != d.get("file"):
                got[str(d.get("name") or "")] += 1
        return got

    @staticmethod
    def unresolved_rows(merged: Mapping[str, Mapping[str, object]], weight: Mapping[str, float],
                        into: Mapping[str, int], known: Collection[str],
                        queued: Collection[str] = ()) -> list[UnresolvedRow]:
        """`shallow` 를 가진 레코드마다 의존 대상 한 줄. `into` 의 키 집합이 "계획에 있는 이름" 이다."""
        rows: list[UnresolvedRow] = []
        for key in sorted(merged):
            rec = merged[key]
            f = AnnotateSymbolsStage.file_of(dict(rec))
            for dep in AnnotateSymbolsStage.shallow_of(rec):
                status: Literal["shallow", "queued", "resolved", "unknown"]
                if dep in known:
                    status = "resolved"
                elif dep not in into:
                    status = "unknown"
                elif key in queued:
                    status = "queued"
                else:
                    status = "shallow"
                rows.append({"file": f, "key": key, "dep": dep, "priority": weight.get(f, 0.0),
                             "into": into.get(key, 0), "status": status})
        return rows

    @staticmethod
    def unresolved_csv(rows: Sequence[UnresolvedRow]) -> str:
        lines = ["file,key,dep,priority,into,status"]
        lines += ["%s,%s,%s,%.6f,%d,%s" % (r["file"], r["key"], r["dep"], r["priority"], r["into"], r["status"])
                  for r in rows]
        return "\n".join(lines) + "\n"

    # ── 2패스 — 파일을 열지 않고 shallow 레코드를 다듬는다 ────────────────

    @staticmethod
    def pass2_prompt(repo: str, root: str, bid: str, file: str,
                     shallow: Mapping[str, Mapping[str, object]],
                     deps: Mapping[str, Mapping[str, object]]) -> str:
        """2패스 — 파일을 다시 읽지 않는다. 얕게 쓴 레코드와, 이제 조사된 의존 대상의 뜻만 받아 다듬는다."""
        mine = json.dumps({k: dict(v) for k, v in shallow.items()}, ensure_ascii=False, indent=1)
        theirs = "\n".join(
            AnnotateSymbolsStage.load_prompt(
                "annotate-symbols#pass2-dep", name=k, means=str(r.get("means") or ""),
                does=str(r.get("does") or "")).removesuffix("\n")
            for k, r in sorted(deps.items()))
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#pass2", repo=repo, root=root, bid=bid, file=file, mine=mine,
            theirs=theirs
            or AnnotateSymbolsStage.load_prompt("annotate-symbols#pass2-no-deps").removesuffix("\n"))

    @staticmethod
    def apply_pass2(shard_dir: str, bid: str) -> list[ShardFault]:
        """2패스 샤드를 검문하고 원 샤드의 **같은 키만** 덮는다. 틀리면 원 샤드를 두고 결함을 낸다.

        덮은 레코드는 `shallow` 를 잃는다. 2패스 파일은 `<bid>.done.json` 으로 남긴다.
        """
        src = os.path.join(shard_dir, "_pass2", bid + ".json")
        dst = os.path.join(shard_dir, bid + ".json")
        with open(src, "rb") as f:
            raw = f.read()
        faults = AnnotateSymbolsStage.check_shard(raw, bid, src)
        if faults:
            return faults
        patch = msgspec.json.decode(raw, type=ShardRecords)
        with open(dst, "rb") as f:
            base = msgspec.json.decode(f.read(), type=ShardRecords)
        for k, rec in patch.items():
            if k in base:
                rec.pop("shallow", None)
                base[k] = rec
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(src, os.path.join(shard_dir, "_pass2", bid + ".done.json"))
        return []

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
    def normalize_records(got: Records, ids: Mapping[str, str]) -> tuple[Records, list[X.DroppedUse]]:
        """`uses[].to` 와 `shallow` 를 레코드 키로 맞춘다. 노드 id 는 이름으로 바꾸고, 어느 키도 아닌 것은 떼어 기록한다.

        `ids` 는 계획의 `id -> name`. 아는 이름 = 병합된 키 전부 ∪ 계획의 이름 전부 — 아직 조사되지
        않은 계획 심볼을 가리키는 간선은 살려 둔다(그 샤드가 오면 키가 생긴다). 비노드 키(file·artifact…)는
        병합된 키에 들어 있으므로 산다. 짧은 이름은 고치지 않는다 — 유일하지 않을 수 있어 떼어 기록만 한다.
        """
        known = set(got) | set(ids.values())
        dropped: list[X.DroppedUse] = []
        out: Records = {}
        for key, rec in got.items():
            f = AnnotateSymbolsStage.file_of(rec)
            new: Record = dict(rec)
            uses_raw = rec.get("uses")
            if isinstance(uses_raw, list):
                kept: list[object] = []
                for u in cast(list[object], uses_raw):
                    if not isinstance(u, dict):
                        continue
                    ud = cast(dict[str, object], u)
                    to = str(ud.get("to") or "")
                    to = ids.get(to, to)
                    if to in known:
                        kept.append({**ud, "to": to})
                    else:
                        dropped.append({"file": f, "key": key, "to": to, "label": str(ud.get("label") or ""),
                                        "where": str(ud.get("where") or ""), "why": "unknown-target"})
                new["uses"] = kept
            sh = AnnotateSymbolsStage.shallow_of(rec)
            if sh:
                fixed = [ids.get(s, s) for s in sh]
                new["shallow"] = [s for s in fixed if s in known]
                for s in fixed:
                    if s not in known:
                        dropped.append({"file": f, "key": key, "to": s, "label": "", "where": "",
                                        "why": "unknown-shallow"})
                if not new["shallow"]:
                    del new["shallow"]
            out[key] = new
        return out, dropped

    @staticmethod
    def dropped_csv(rows: Sequence[X.DroppedUse]) -> str:
        """`dropped-uses.csv` 본문. label 만 따옴표로 감싼다 — 세션이 쉼표를 쓰는 칸이 그것뿐이다."""
        lines = ["file,key,to,label,where,why"]
        lines += ['%s,%s,%s,"%s",%s,%s' % (r["file"], r["key"], r["to"], r["label"].replace('"', "'"),
                                           r["where"], r["why"]) for r in rows]
        return "\n".join(lines) + "\n"

    def refresh_merged(self, ctx: Mode1Context) -> list[X.DroppedUse]:
        """샤드를 다시 합치고 보정해 `terms-reading.json` 과 `dropped-uses.csv` 를 쓴다.

        층 끝(`harvest`)과 파일 끝(`AnnotateFilesStage`)이 같은 것을 부른다 — 병합의 정의는 한 곳이다.
        """
        assert ctx.plan is not None
        raw = self.merge_shards(self.shard_dir(ctx), ctx.baseline)
        ctx.merged, dropped = self.normalize_records(raw, self.name_of(ctx.plan))
        path = X.READING.locate(ctx)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx.merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        with open(X.DROPPED.locate(ctx), "w", encoding="utf-8") as f:
            f.write(self.dropped_csv(dropped))
        return dropped

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
        self.write_schema(X.RECORD_SCHEMA.locate(ctx))
        ctx.baseline = self.load_records(X.READING.locate(ctx))
        ctx.merged = dict(ctx.baseline)
        out = super().perform(ctx)
        if out.kind == P.OK:
            out = self.sweep(ctx, out)
        ctx.survey_ok = out.kind == P.OK    # 층이 0개면 harvest 가 안 불리므로 여기서 정한다
        return out

    def sweep(self, ctx: Mode1Context, out: P.Outcome) -> P.Outcome:
        """세션이 전부 끝난 뒤 샤드 전량을 검문한다. 틀린 샤드는 격리하고 단계를 실패로 세운다."""
        t0 = time.monotonic()
        assert ctx.plan is not None
        d = self.shard_dir(ctx)
        bad = self.check_shards(d, ctx.plan)
        for bid, faults in sorted(bad.items()):
            for f in faults:
                print("[%s] 샤드가 틀렸다 %s" % (bid, self.fault_line(f)), file=sys.stderr)
            self.quarantine(d, bid, faults)
        for bid in self.plan_ids(ctx.plan):
            if bid not in bad:
                self.clear_quarantine(d, bid)
        row = self.row(t0, not bad,
                       "" if not bad else "샤드 %d개가 틀려 격리했다 — --resume 이 그 배치만 다시 띄운다: %s"
                       % (len(bad), ", ".join(sorted(bad))))
        row["stage"] = "annotate-symbols/check-shards"
        n = sum(len(L.get("batches", [])) or 1 for L in ctx.plan["layers"])
        print("  샤드 검문 — 세션 %d개 중 틀린 것 %d개" % (n, len(bad)), flush=True)
        if bad:
            return P.Outcome(P.FAIL, row["why"], list(out.rows) + [row])
        return P.Outcome(P.OK, "", list(out.rows) + [row])

    def rounds(self, ctx: Mode1Context) -> int:
        return len(ctx.plan["layers"]) if ctx.plan else 0

    def jobs(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]:
        assert ctx.plan is not None
        layer = ctx.plan["layers"][rnd]
        if layer.get("kind") == "non-node":
            jobs = [("NONNODE", self.nonnode_prompt(ctx.repo, ctx.root))]
        else:
            names = self.name_of(ctx.plan)
            jobs = [(b["id"], self.survey_batch_prompt(ctx.repo, ctx.root, b,
                                                       self.dep_excerpt(ctx.merged, b, names),
                                                       ctx.targets, ctx.tracked_n, name_of=names))
                    for b in layer["batches"]]
        # 샤드가 이미 있는 배치는 건너뛴다 — 다시 돌리면 실패한 배치만 돌고, 격리된 사유를 받는다.
        d = self.shard_dir(ctx)
        return [(bid, pr + self.retry_section(d, bid)) for bid, pr in jobs
                if not os.path.exists(os.path.join(d, bid + ".json"))]

    def harvest(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome:
        out = super().harvest(ctx, got, rnd)
        for row in out.rows:
            row["stage"] = "annotate-symbols/" + row["stage"]
        dropped = self.refresh_merged(ctx)
        print("  층 끝 — 레코드 %d개 · 떼어 낸 간선 %d개" % (len(ctx.merged), len(dropped)), flush=True)
        return out
