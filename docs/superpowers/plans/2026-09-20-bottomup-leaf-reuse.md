# Bottom-Up 잎 레코드 완전 재사용 — 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> 실행 첫 걸음: 이 파일을 `docs/superpowers/plans/2026-09-20-bottomup-leaf-reuse.md` 로 복사해 저장소에 둔다(계획 모드에서는 이 파일만 쓸 수 있었다).

**Goal:** 파일 전략(`--strategy file`)에서 "아래(잎)에서 먼저 끝난 레코드의 뜻이 위 파일의 세션 프롬프트에 **항상** 실리고, 세션이 그것을 **레코드 키 그대로** `uses[].to` 에 적고, 세션이 틀리게 적은 것은 기계가 고치거나 떼어 내어 `verify-terms` 가 통과한다" 를 끝에서 끝까지 성립시킨다.

**Architecture:** 끊김 네 곳을 각각 한 Task 로 닫는다. ① 스케줄러는 **의존 파일이 전부 병합된 파일만** 풀에 넣고(준비 집합 · Kahn 식), 프롬프트는 **투입 순간** 조립한다 — 파일 간 순환이 있는 저장소에서만 남은 의존이 가장 적은 파일을 강제 투입해 기존 `shallow`/2패스 기구가 받는다. ② 프롬프트의 `의존 ->` 줄이 노드 id 대신 **이름**을 보이고, 레코드 계약이 "`uses[].to` 는 레코드 키, 외부 의존은 적지 않는다" 를 명시한다. ③ `pending_excerpt` 가 같은 배치의 심볼을 "열지 마라" 목록에서 뺀다. ④ 병합이 `uses[].to`·`shallow` 의 노드 id 를 이름으로 바꾸고, 어느 키도 아닌 것(stdlib·서드파티·짧은 이름)은 떼어 `dropped-uses.csv` 에 남긴다 — 층 전략과 파일 전략이 같은 함수를 쓴다.

**Tech Stack:** Python 3.14 · msgspec · networkx(계획) · `claude -p` 헤드리스 세션 · pytest · pyright strict.

---

## Context — 왜 이 변경인가

🔵 2026-09-19 파일 전략 전량 실행(R6, `evals/runs/2026-09-19-mode1-report-builder-cold-file-sonnet.json`)에서 실제 레코드 하나로 확인한 사슬 끊김:

| # | 어디 | 실물 |
|---|---|---|
| ① | `runner/mode1/survey_files.py:135-141` 이 78개 프롬프트를 **t0 에 전부 제출** | 병합 0개 시점에 조립돼 `dep_excerpt` 가 78개 전부 빈 채 시작. F03(`normalize.py`)이 7분에 끝나도 F75(`test_normalize.py`, 30분 뒤 시작)는 모른다 |
| ② | `survey.py` 심볼 줄 `의존 -> C218, C380` | 세션이 id 를 `uses.to`·`shallow` 에 그대로 베낀다 — 94건. 09-07 인계 문서(`HANDOFF-2026-09-07-codegraph-id-namespace.md`)의 "갈래 A" 미착수 |
| ③ | `survey.py` `pending_excerpt` | 자기 파일 안의 `_griffe_dump` 까지 "열지 마라" 목록에 넣었다 |
| ④ | `unresolved_rows` 이름표 · `verify-terms` | id 라서 `unknown` 94건 → 2패스 후보 탈락. `verify-terms` 실패 533건(id 94 · 짧은 이름 179 · 접두 틀림 79 · stdlib 181) → 파이프라인 정지 |

🔵 이 저장소의 파일 의존 그래프(오늘 `codegraph.json`): 파일 78 · 파일 간 간선 56 · **파일 간 순환 0** · 임계 경로 5 · 잎 파일 40. 준비 집합으로 기다려도 동시 8 기준 물결 10 → 11 — 벽시계 대가는 한 물결이다.

사용자 결정(2026-09-20): 의존 파일이 끝난 뒤 투입 · 외부 의존은 적지 않게 하고 적힌 것은 기계가 떼어 기록 · 이름 보정은 노드 id → 이름만.

## 지금 브랜치 상태

`survey-per-file-2pass`, `main` 에서 9커밋 앞. 미커밋: `runner/run_mode1_5.py`·`runner/test_run_mode1_5.py`·`.claude/skills/term-benchmark/SKILL.md`·`runner/README.md` (Mode 1.5 `--ask`, 별개 작업 — 이 계획 전에 따로 커밋한다). 게이트 빨강 둘은 이 계획과 무관: `machine/test_survey_plan.py::test_이_저장소_실측`(골든 상수가 오늘 `batches.json` 과 어긋남) · `test/test_wiki.py`(위키 표류).

## 파일 구조

| 파일 | 책임 |
|---|---|
| `runner/mode1/context.py` | `DroppedUse` 형 · `DROPPED` 산출물(`dropped-uses.csv`) |
| `runner/mode1/survey.py` | 공통: 프롬프트(이름 · 계약 문구) · `pending_excerpt` 자기 배치 제외 · `normalize_records` · `dropped_csv` · `refresh_merged`(병합→보정→쓰기) — 층 전략 `harvest` 가 쓴다 |
| `runner/mode1/survey_files.py` | 파일 전략: `dep_files` · 준비 집합 스케줄러(`ready`/`launch`/`refill`) · 투입 순간 프롬프트 조립 · `refresh_merged` 사용 |
| `runner/test_mode1.py` | 시험 전부 (기존 `_fake_agent` 에 프롬프트 갈무리 추가) |

---

### Task 0: Mode 1.5 `--ask` 를 먼저 따로 커밋한다

**Files:** `runner/run_mode1_5.py` · `runner/test_run_mode1_5.py` · `.claude/skills/term-benchmark/SKILL.md` · `runner/README.md`

- [ ] **Step 1: 게이트**

Run: `.venv/bin/python -m pytest runner -q && npm run -s typecheck:py`
Expected: `336 passed` · `0 errors`

- [ ] **Step 2: 커밋**

```bash
git add runner/run_mode1_5.py runner/test_run_mode1_5.py .claude/skills/term-benchmark/SKILL.md runner/README.md
git commit -m "[feat] : mode 1.5 --ask - 대화형 claude 세션으로 term-benchmark 스킬을 띄우고 답안이 남으면 이어 채점"
```

- [ ] **Step 3: 이 계획을 저장소에 복사**

```bash
cp ~/.claude/plans/quizzical-stirring-otter.md docs/superpowers/plans/2026-09-20-bottomup-leaf-reuse.md
```

---

### Task 1: 프롬프트가 id 대신 이름을 보이고, `uses[].to` 계약을 못 박는다 (끊김 ②)

**Files:**
- Modify: `runner/mode1/survey.py` — `survey_batch_prompt`(심볼 줄 · 레코드 계약) · `pending_section` · `jobs`
- Modify: `runner/mode1/survey_files.py` — `survey_batch_prompt` 호출에 `name_of=`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** (`test_dep_excerpt_는_depends_on_의_id_를_이름으로_바꿔_찾는다` 아래에 붙인다)

```python
def test_배치_프롬프트의_의존_줄은_id_가_아니라_이름을_보인다():
    b: survey_plan.PlanBatch = {"id": "F00", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False,
         "depends_on": ["C1", "C9"]}]}
    p = SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "", name_of={"C1": "b.g"})
    assert "의존 -> b.g, C9" in p                 # 이름표에 없는 id 는 그대로 둔다 — 지어내지 않는다
    assert "의존 -> C1" not in p
    assert "uses[].to 는 이 저장소 안 심볼의 레코드 키" in p
    assert "subprocess.run" in p                  # 외부 의존은 적지 않는다는 예시가 계약에 있다
    assert '"shallow": ["위 목록의 이름 그대로"]' in SV.AnnotateSymbolsStage.pending_section("  - c.h (class) c.py:3")


def test_배치_프롬프트는_이름표_없이도_돈다():
    b = _one_batch_plan("L0-B00")["layers"][0]["batches"][0]
    assert "의존 -> 없음" in SV.AnnotateSymbolsStage.survey_batch_prompt("/repo", "/root", b, "")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "배치_프롬프트"`
Expected: `1 failed, 1 passed` — 첫 시험이 `TypeError: unexpected keyword 'name_of'`

- [ ] **Step 3: `survey_batch_prompt` — 서명과 심볼 줄**

`runner/mode1/survey.py` 의 `survey_batch_prompt` 서명과 `syms` 조립을 이렇게 바꾼다:

```python
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
        syms = "\n".join(
            "  - %s (%s) %s:%s   의존 -> %s"
            % (s["name"], s["kind"], s["file"], s["line"],
               ", ".join(names.get(d, d) for d in (s.get("depends_on") or [])) or "없음")
            for s in batch["symbols"])
```

- [ ] **Step 4: 레코드 계약 문구**

같은 함수의 프롬프트 본문에서

```
- uses[] = {{to, kind, label, where}}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
```

바로 아래에 두 줄을 더한다:

```
- **uses[].to 는 이 저장소 안 심볼의 레코드 키다** — 위 심볼 목록과 아래층 발췌에 적힌 이름 **그대로**.
  `C218` 같은 id 나 `GraphNode` 같은 짧은 이름을 쓰지 않는다. 표준 라이브러리·서드파티
  (`subprocess.run`, `networkx`)는 uses 에 넣지 않는다 — 기계가 떼어 내고 기록만 남긴다.
```

- [ ] **Step 5: `pending_section` 의 shallow 문구**

`"그렇게 쓴 레코드에는 `\"shallow\": [\"그 이름들\"]` 을 적는다"` → `"그렇게 쓴 레코드에는 `\"shallow\": [\"위 목록의 이름 그대로\"]` 을 적는다"`

- [ ] **Step 6: 호출자 둘**

`survey.py` `jobs()`:
```python
            names = self.name_of(ctx.plan)
            jobs = [(b["id"], self.survey_batch_prompt(ctx.repo, ctx.root, b,
                                                       self.dep_excerpt(ctx.merged, b, names),
                                                       ctx.targets, ctx.tracked_n, name_of=names))
                    for b in layer["batches"]]
```
`survey_files.py` 의 `survey_batch_prompt(...)` 호출에 `name_of=name_of` 를 더한다 (Task 4 에서 이 호출이 `launch()` 안으로 옮겨간다 — 그때도 유지).

- [ ] **Step 7: 통과 확인 + 커밋**

Run: `.venv/bin/python -m pytest runner -q && npm run -s typecheck:py`
Expected: 전부 통과 · 0 errors

```bash
git add runner/mode1/survey.py runner/mode1/survey_files.py runner/test_mode1.py
git commit -m "[fix] : 조사 프롬프트가 의존 대상을 id 아닌 이름으로 보이고 uses.to 는 레코드 키라고 못 박는다"
```

---

### Task 2: `pending_excerpt` 가 자기 배치의 심볼을 빼놓는다 (끊김 ③)

**Files:**
- Modify: `runner/mode1/survey.py` — `pending_excerpt`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** (`test_미조사_의존_절은_아직_없는_의존_대상을_이름_종류_자리로_적는다` 아래)

```python
def test_미조사_의존_절은_같은_배치의_심볼을_넣지_않는다():
    """자기 파일 안의 함수는 지금 읽고 있는 것이다 — "열지 마라" 목록에 들어가면 안 된다."""
    b: survey_plan.PlanBatch = {"id": "F03", "files": ["a.py"], "symbols": [
        {"id": "C2", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "in_cycle": False,
         "depends_on": ["C3", "C9"]},
        {"id": "C3", "name": "a.h", "kind": "function", "file": "a.py", "line": 5, "in_cycle": False,
         "depends_on": []}]}
    nodes = {"C3": {"id": "C3", "name": "a.h", "kind": "function", "file": "a.py", "line": 5, "module": "."},
             "C9": {"id": "C9", "name": "c.h", "kind": "class", "file": "c.py", "line": 3, "module": "."}}
    assert SV.AnnotateSymbolsStage.pending_excerpt({}, b, nodes) == "  - c.h (class) c.py:3"
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "같은_배치의_심볼"`
Expected: `1 failed` — `a.h` 줄이 함께 나온다

- [ ] **Step 3: 구현**

```python
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
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `.venv/bin/python -m pytest runner -q`
```bash
git add runner/mode1/survey.py runner/test_mode1.py
git commit -m "[fix] : 미조사 의존 절이 자기 배치의 심볼을 열지 마라 목록에 넣지 않는다"
```

---

### Task 3: 병합 보정 — id 는 이름으로, 모르는 대상은 떼어 `dropped-uses.csv` 에 (끊김 ④)

**Files:**
- Modify: `runner/mode1/context.py` — `DroppedUse` · `DROPPED` · `ARTIFACTS`
- Modify: `runner/mode1/survey.py` — `normalize_records` · `dropped_csv` · `refresh_merged` · `writes` · `harvest`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
def test_병합_보정은_id_를_이름으로_바꾸고_모르는_대상은_떼어_기록한다():
    got: X.Records = {
        "a.f": {**_good_record(), "where": "a.py:1", "uses": [
            {"to": "C1", "kind": "dependency", "label": "calls", "where": "a.py:2"},
            {"to": "subprocess.run", "kind": "dependency", "label": "runs", "where": "a.py:3"},
            {"to": "b.g", "kind": "dependency", "label": "ok", "where": "a.py:4"},
            {"to": "z.notyet", "kind": "dependency", "label": "later", "where": "a.py:5"}],
         "shallow": ["C1", "os.walk"]},
        "b.g": _good_record()}
    out, dropped = SV.AnnotateSymbolsStage.normalize_records(got, {"C1": "b.g", "C7": "z.notyet"})
    uses = cast(list[dict[str, object]], out["a.f"]["uses"])
    assert [u["to"] for u in uses] == ["b.g", "b.g", "z.notyet"]      # id 는 이름으로 · 계획에 있는 미조사 이름은 산다
    assert out["a.f"]["shallow"] == ["b.g"]
    assert [(d["to"], d["why"]) for d in dropped if d["key"] == "a.f"] == [("subprocess.run", "unknown-target"),
                                                                            ("os.walk", "unknown-shallow")]
    assert dropped[0]["file"] == "a.py" and dropped[0]["key"] == "a.f" and dropped[0]["where"] == "a.py:3"
    # _good_record() 의 uses.to 'g' 는 어느 키도 아니라 떼인다. 나머지 칸은 그대로다.
    assert out["b.g"]["uses"] == [] and out["b.g"]["means"] == got["b.g"]["means"]
    assert [(d["key"], d["to"]) for d in dropped if d["key"] == "b.g"] == [("b.g", "g")]


def test_병합_보정은_shallow_가_다_떨어지면_칸을_뗀다():
    got: X.Records = {"a.f": {**_good_record(), "uses": [], "shallow": ["os.walk"]}}
    out, dropped = SV.AnnotateSymbolsStage.normalize_records(got, {})
    assert "shallow" not in out["a.f"] and [d["why"] for d in dropped] == ["unknown-shallow"]


def test_dropped_csv_머리줄과_label_의_따옴표():
    text = SV.AnnotateSymbolsStage.dropped_csv([{"file": "a.py", "key": "a.f", "to": "subprocess.run",
                                                 "label": 'runs "x"', "where": "a.py:3", "why": "unknown-target"}])
    assert text.splitlines() == ["file,key,to,label,where,why",
                                 "a.py,a.f,subprocess.run,\"runs 'x'\",a.py:3,unknown-target"]


def test_refresh_merged_는_보정본을_reading_과_dropped_csv_로_쓴다(tmp_path: Path):
    c = _ctx(tmp_path); c.plan = _one_batch_plan("L0-B00")
    d = Path(SV.AnnotateSymbolsStage.shard_dir(c)); d.mkdir(parents=True)
    (d / "L0-B00.json").write_text(json.dumps({"f": {**_good_record(), "uses": [
        {"to": "os.walk", "kind": "dependency", "label": "walks", "where": "m.py:2"}]}}), encoding="utf-8")
    os.makedirs(os.path.dirname(X.READING.locate(c)), exist_ok=True)
    dropped = SV.AnnotateSymbolsStage().refresh_merged(c)
    assert [x["to"] for x in dropped] == ["os.walk"]
    merged = json.loads(Path(X.READING.locate(c)).read_text(encoding="utf-8"))
    assert merged["f"]["uses"] == [] and c.merged == merged
    assert Path(X.DROPPED.locate(c)).read_text(encoding="utf-8").splitlines()[1].startswith("m.py,f,os.walk,")
```

`_good_record()` 의 `uses[0].to == "g"` 는 어느 키도 아니라 보정이 떼어 낸다. **기존 시험 중 `harvest` 나 `refresh_merged` 를 지난 뒤 `uses` 를 단언하는 것이 있으면** 그 `to` 를 계획에 있는 이름(예: `"f"`)으로 고친다 — 시험이 틀린 것이지 보정이 틀린 것이 아니다.

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "병합_보정 or dropped_csv or refresh_merged"`
Expected: `4 failed` — 속성 없음

- [ ] **Step 3: `context.py`**

`UnresolvedRow` 아래에:
```python
class DroppedUse(TypedDict):
    """`dropped-uses.csv` 의 한 줄 — 병합 보정이 레코드에서 떼어 낸 `uses[]` 하나 또는 `shallow` 이름 하나.

    `to` 는 떼어 낸 대상 이름(노드 id 였으면 이름으로 바꾼 뒤). `why` 는 unknown-target(어느 레코드 키도
    계획 이름도 아니다 — stdlib·서드파티·짧은 이름) · unknown-shallow(같은 사유, `shallow` 칸).
    """
    file: str
    key: str
    to: str
    label: str
    where: str
    why: Literal["unknown-target", "unknown-shallow"]
```
산출물 선언에 `UNRESOLVED` 다음:
```python
DROPPED = P.Artifact[Mode1Context](
    "dropped-uses.csv", lambda c: os.path.join(raw_dir(c), "dropped-uses.csv"))
```
`ARTIFACTS` 목록에 `UNRESOLVED` 뒤에 `DROPPED` 를 넣는다.

- [ ] **Step 4: `survey.py` — 보정 셋** (`merge_shards` 바로 아래)

```python
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
                dropped += [{"file": f, "key": key, "to": s, "label": "", "where": "", "why": "unknown-shallow"}
                            for s in fixed if s not in known]
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
```
`Record` 는 이미 `mode1.context` 에서 import 되어 있다(`from mode1.context import (ROOT, FaultKind, Mode1Context, Record, Records, …)`).

- [ ] **Step 5: `writes` 와 `harvest`**

```python
    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.RECORD_SCHEMA, X.READING, X.DROPPED]
```
`harvest` 의 병합·쓰기 여섯 줄(`ctx.merged = self.merge_shards(...)` 부터 `json.dump(...)` 까지)을 다음으로 바꾼다:
```python
        dropped = self.refresh_merged(ctx)
        print("  층 끝 — 레코드 %d개 · 떼어 낸 간선 %d개" % (len(ctx.merged), len(dropped)), flush=True)
```
(기존 `print("  층 끝 — 레코드 %d개" ...)` 줄은 지운다.)

- [ ] **Step 6: 통과 확인 + 커밋**

Run: `.venv/bin/python -m pytest runner -q && npm run -s typecheck:py`
```bash
git add runner/mode1/context.py runner/mode1/survey.py runner/test_mode1.py
git commit -m "[feat] : 병합 보정 - uses.to 의 노드 id 는 이름으로, 어느 키도 아닌 것은 떼어 dropped-uses.csv 에"
```

---

### Task 4: 준비 집합 스케줄러 — 의존 파일이 끝난 뒤 투입, 프롬프트는 투입 순간 조립 (끊김 ①)

**Files:**
- Modify: `runner/mode1/survey_files.py` — `dep_files` · `perform`(스케줄러) · `writes`
- Test: `runner/test_mode1.py` (`_fake_agent` 확장)

**동작 (한 문단):** 계획의 배치(= 파일)를 `pending` 목록(계획 순 = 가중치 순)에 둔다. `ready()` = 의존 파일이 전부 `done_files` 에 있는 것. `refill()` 은 빈 자리(`concurrency − 돌고 있는 것`)마다 준비된 것 중 첫째를 **그 순간의 `ctx.merged` 로 프롬프트를 조립해** 넣는다 — 그래서 `dep_excerpt` 가 늘 차 있다. 준비된 것이 없고 도는 것도 없으면(파일 간 순환) 남은 의존이 가장 적은 파일을 강제 투입하고 그 사실을 찍는다 — 그 세션만 `pending` 절을 받아 `shallow` 로 쓰고, 기존 2패스가 뒤에 다듬는다. 세션이 끝나면 성공·실패와 무관하게 그 파일을 `done_files` 에 넣는다(실패한 파일이 의존하는 쪽을 영원히 막지 않게) → 병합·보정 → 2패스 후보 → `refill()`.

- [ ] **Step 1: `_fake_agent` 가 프롬프트를 갈무리하도록 넓힌다** (기존 시험은 그대로 통과해야 한다)

```python
def _fake_agent(shards: dict[str, dict[str, object]], calls: list[str],
                prompts: dict[str, str] | None = None):
    """라벨을 보고 샤드를 써 주는 가짜 세션. 프롬프트의 '쓰는 곳' 줄에서 경로를 뽑는다.
    `prompts` 를 주면 라벨마다 받은 프롬프트를 남긴다 — 스케줄러가 무엇을 실었는지 보는 용도."""
    import re

    def run(model: str, repo: str, root: str, prompt: str, timeout: float | None,
            label: str = "") -> tuple[float, int, M.ClaudeResult | None]:
        calls.append(label)
        if prompts is not None:
            prompts[label] = prompt
        m = re.search(r"(\S+/_shards/\S+\.json)", prompt)
        assert m, label
        path = m.group(1)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(shards[label], f, ensure_ascii=False)
        return 0.01, 0, {"subtype": "success", "is_error": False, "num_turns": 2, "total_cost_usd": 0.01,
                         "usage": {"input_tokens": 1, "output_tokens": 1,
                                   "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}
    return run
```

- [ ] **Step 2: 실패하는 시험 셋**

```python
def test_dep_files_는_파일_간_간선의_목적_파일만_모은다():
    import mode1.survey_files as SF
    got = SF.AnnotateFilesStage.dep_files(_three_file_graph())
    assert got == {"a.py": {"b.py"}, "b.py": set(), "c.py": {"a.py"}}


def test_파일_스케줄러는_의존_파일이_끝난_뒤에야_투입하고_그_뜻을_프롬프트에_싣는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """동시 8 인데도 b → a → c 로 하나씩 간다 — 준비된 파일이 그때마다 하나뿐이라서. 프롬프트에는 앞선 뜻이 실린다."""
    import mode1.survey_files as SF
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"; c.concurrency = 8
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    cg = _three_file_graph()
    (raw / "codegraph.json").write_text(json.dumps(cg))
    plan = survey_plan.plan_by_file(cast(survey_plan.CodeGraph, cg))
    (raw / "batches.json").write_text(json.dumps(plan))
    ids = {b["files"][0]: b["id"] for b in plan["layers"][0]["batches"]}
    shards: dict[str, dict[str, object]] = {
        ids["b.py"]: {"b.g": _rec("b.py:1", means="지 뜻")},
        ids["a.py"]: {"a.f": _rec("a.py:1", means="에프 뜻", uses=[{"to": "b.g", "kind": "dependency", "label": "calls", "where": "a.py:1"}])},
        ids["c.py"]: {"c.k": _rec("c.py:1")},
        "NONNODE": {}}
    calls: list[str] = []; prompts: dict[str, str] = {}
    monkeypatch.setattr(SF.P, "run_agent_with", _fake_agent(shards, calls, prompts))
    out = SF.AnnotateFilesStage().perform(c)
    assert out.kind == P.OK, out.why
    assert calls == [ids["b.py"], ids["a.py"], ids["c.py"], "NONNODE"]
    assert "  - b.g — 지 뜻" in prompts[ids["a.py"]]                      # 아래층 발췌가 차 있다
    assert "  - a.f — 에프 뜻" in prompts[ids["c.py"]]
    assert "## 아직 조사되지 않은 의존 대상" not in prompts[ids["a.py"]]      # 기다렸으니 미조사가 없다
    assert "## 아직 조사되지 않은 의존 대상" not in prompts[ids["c.py"]]
    assert "의존 -> b.g" in prompts[ids["a.py"]]                        # id 'b' 가 아니라 이름 'b.g' (Task 1)
    assert not [r for r in out.rows if r["stage"].endswith("/p2")]        # 얕게 쓴 것이 없으니 2패스도 없다
    assert Path(X.DROPPED.locate(c)).read_text(encoding="utf-8").splitlines()[0] == "file,key,to,label,where,why"


def test_파일_스케줄러는_순환이면_남은_의존이_가장_적은_파일을_강제_투입한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """a.f ↔ b.g 가 서로 의존한다. 아무것도 준비되지 않으니 하나를 강제로 넣고, 그 세션만 미조사 절을 받는다."""
    import mode1.survey_files as SF
    c = _ctx(tmp_path); c.cold = True; c.strategy = "file"; c.concurrency = 2
    raw = tmp_path / "out" / "codegraph-raw"; raw.mkdir(parents=True)
    cg: X.CodeGraphDoc = {"nodes": [
        {"id": "a", "name": "a.f", "kind": "function", "file": "a.py", "line": 1, "module": "."},
        {"id": "b", "name": "b.g", "kind": "function", "file": "b.py", "line": 1, "module": "."}],
        "edges": [{"from": "a", "to": "b", "kind": "dependency", "label": None, "file": "a.py", "line": 1},
                  {"from": "b", "to": "a", "kind": "dependency", "label": None, "file": "b.py", "line": 1}]}
    (raw / "codegraph.json").write_text(json.dumps(cg))
    plan = survey_plan.plan_by_file(cast(survey_plan.CodeGraph, cg))
    (raw / "batches.json").write_text(json.dumps(plan))
    ids = {b["files"][0]: b["id"] for b in plan["layers"][0]["batches"]}
    first = plan["layers"][0]["batches"][0]["files"][0]                  # 가중치 순 첫째가 강제 투입된다
    other = "b.py" if first == "a.py" else "a.py"
    shards: dict[str, dict[str, object]] = {
        ids["a.py"]: {"a.f": _rec("a.py:1")}, ids["b.py"]: {"b.g": _rec("b.py:1")}, "NONNODE": {}}
    calls: list[str] = []; prompts: dict[str, str] = {}
    monkeypatch.setattr(SF.P, "run_agent_with", _fake_agent(shards, calls, prompts))
    out = SF.AnnotateFilesStage().perform(c)
    assert out.kind == P.OK, out.why
    assert calls[:2] == [ids[first], ids[other]]
    assert "## 아직 조사되지 않은 의존 대상" in prompts[ids[first]]           # 강제 투입 — 의존이 아직 없다
    assert "## 아직 조사되지 않은 의존 대상" not in prompts[ids[other]]      # 둘째는 첫째가 끝난 뒤 들어왔다
```
- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "dep_files or 의존_파일이_끝난 or 순환이면"`
Expected: `3 failed` — `dep_files` 없음 · 셋이 한 번에 투입돼 `a` 프롬프트의 발췌가 빔

- [ ] **Step 4: `dep_files`** (`AnnotateFilesStage` 안, `writes` 아래)

```python
    @staticmethod
    def dep_files(cg: X.CodeGraphDoc) -> dict[str, set[str]]:
        """파일마다 그 안의 심볼이 **다른 파일**의 심볼로 내는 간선의 목적 파일 집합. 외부 노드는 세지 않는다.

        준비 집합 스케줄러의 재료다 — 이 집합이 전부 끝난 파일만 투입한다.
        """
        nodes = {str(n.get("id")): n for n in cg["nodes"] if n.get("kind") != "external" and n.get("file")}
        got: dict[str, set[str]] = {str(n.get("file")): set() for n in nodes.values()}
        for e in cg.get("edges", []):
            s, t = nodes.get(str(e.get("from"))), nodes.get(str(e.get("to")))
            if s is not None and t is not None and s.get("file") != t.get("file"):
                got[str(s.get("file"))].add(str(t.get("file")))
        return got
```

- [ ] **Step 5: `writes` 에 `DROPPED`**

```python
    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.RECORD_SCHEMA, X.READING, X.UNRESOLVED, X.DROPPED]
```

- [ ] **Step 6: `perform` — 스케줄러** (`rows: list[M.StageRow] = []` 부터 `pool.shutdown(wait=True)` 까지를 통째로 이것으로 바꾼다. 그 위의 준비 코드에서 `ctx.merged = self.merge_shards(d, ctx.baseline)` 한 줄은 `self.refresh_merged(ctx)` 로 바꾼다.)

```python
        rows: list[M.StageRow] = []
        queued: set[str] = set()          # 2패스를 넣은 배치 id
        failed = False
        pool = ThreadPoolExecutor(max_workers=max(1, ctx.concurrency))
        running: dict[Future[AgentRun], str] = {}
        deps = self.dep_files(cg)
        file_of_bid = {bid: b["files"][0] for bid, b in batches.items() if b["files"]}
        done_files: set[str] = {file_of_bid[bid] for bid in file_of_bid
                                if os.path.exists(os.path.join(d, bid + ".json"))}
        pending: list[str] = [bid for bid in file_of_bid if file_of_bid[bid] not in done_files]   # 계획 순 = 가중치 순

        def submit(label: str, prompt: str) -> None:
            fut = pool.submit(P.run_agent_with, self.model(ctx), ctx.repo, ctx.root, prompt, ctx.timeout, label)
            running[fut] = label

        def write_merged() -> None:
            self.refresh_merged(ctx)
            table = self.unresolved_rows(ctx.merged, weight, into, known=set(ctx.merged), queued=queued)
            with open(X.UNRESOLVED.locate(ctx), "w", encoding="utf-8") as f:
                f.write(self.unresolved_csv(table))

        def remaining(bid: str) -> set[str]:
            return deps.get(file_of_bid[bid], set()) - done_files

        def launch(bid: str) -> None:
            """투입 **순간**의 병합본으로 프롬프트를 만든다 — 그래서 앞서 끝난 파일의 뜻이 실린다."""
            pending.remove(bid)
            b = batches[bid]
            prompt = self.survey_batch_prompt(
                ctx.repo, ctx.root, b, self.dep_excerpt(ctx.merged, b, name_of),
                pending=self.pending_excerpt(ctx.merged, b, nodes), name_of=name_of) + self.retry_section(d, bid)
            submit(bid, prompt)

        def refill() -> None:
            """빈 자리마다 준비된(의존 파일이 전부 끝난) 파일을 넣는다.

            준비된 것이 없고 도는 것도 없으면 파일 간 순환이다 — 남은 의존이 가장 적은 파일을 강제 투입한다.
            그 세션만 미조사 절을 받아 shallow 로 쓰고, 2패스가 뒤에 다듬는다.
            """
            while pending and len(running) < max(1, ctx.concurrency):
                ready = [bid for bid in pending if not remaining(bid)]
                if ready:
                    launch(ready[0])
                    continue
                if running:
                    return
                bid = min(pending, key=lambda x: (len(remaining(x)), pending.index(x)))
                print("  [%s] 순환 — 의존 파일 %d개가 아직인데 강제 투입한다: %s"
                      % (bid, len(remaining(bid)), ", ".join(sorted(remaining(bid)))), flush=True)
                launch(bid)

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
            deps_recs = {dep: ctx.merged[dep] for r in shallow.values() for dep in self.shallow_of(r) if dep in ctx.merged}
            submit(bid + "/p2", self.pass2_prompt(ctx.repo, ctx.root, bid, batches[bid]["files"][0], shallow, deps_recs))

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
            if not is_p2 and bid in file_of_bid:
                done_files.add(file_of_bid[bid])      # 실패했어도 끝난 것이다 — 의존하는 쪽을 영원히 막지 않는다
            write_merged()
            for cand in pass2_candidates():
                submit_pass2(cand)
            print("  [%s] %s — 레코드 %d개 · 돌고 있는 것 %d · 대기 %d" % (label, "성공" if ok else "실패",
                                                                    len(ctx.merged), len(running), len(pending)), flush=True)
            refill()

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
            refill()
            drain()
            if not failed and has_nonnode and not os.path.exists(os.path.join(d, "NONNODE.json")):
                submit("NONNODE", self.nonnode_prompt(ctx.repo, ctx.root))
                drain()
        pool.shutdown(wait=True)
```
주의:
- `refill()` 은 `len(running) < concurrency` 까지만 넣는다 — 풀의 대기열에 프롬프트를 미리 쌓으면 다시 얼어 버린다. 투입 = 즉시 시작이어야 한다.
- 순환 판정은 `not ready and not running` 이다. 도는 것이 있으면 기다린다 — 그것이 끝나면 준비되는 파일이 생길 수 있다.
- 기존 `write_merged` 의 `json.dump(ctx.merged, …)` 는 `refresh_merged` 가 한다. 모듈 독스트링 첫 줄 "가중치 순, 장벽 없는 풀" 을 "의존 파일이 끝난 순, 준비 집합 풀" 로 고친다.

- [ ] **Step 7: 통과 확인** — 새 셋과 기존 스케줄러 시험 둘이 함께 통과해야 한다

Run: `.venv/bin/python -m pytest runner -q && npm run -s typecheck:py && .venv/bin/python -m pytest test/test_no_any.py -q`
Expected: 전부 통과 · 0 errors

- [ ] **Step 8: 커밋**

```bash
git add runner/mode1/survey_files.py runner/test_mode1.py
git commit -m "[feat] : 파일 스케줄러 - 의존 파일이 끝난 파일만 투입하고 프롬프트는 투입 순간 조립, 순환은 강제 투입"
```

---

### Task 5: 실데이터 검증 — 오늘 남은 1,318 레코드 위에서 보정이 무엇을 하는지 (읽기만)

**Files:** 없음 (검증 스크립트는 스크래치패드에)

- [ ] **Step 1: 보정 시뮬레이션**

```bash
.venv/bin/python - <<'EOF'
import json, sys
sys.path[:0] = ["runner", "machine"]
from mode1.survey import AnnotateSymbolsStage as S
plan = json.load(open("out/codegraph-raw/batches.json"))
got = json.load(open("machine/terms-reading.json"))
out, dropped = S.normalize_records(got, S.name_of(plan))
import collections
fixed = sum(1 for k in got for u in got[k].get("uses", []) if u["to"] in S.name_of(plan))
print("id→이름 고침", fixed, "· 떼어 냄", collections.Counter(d["why"] for d in dropped))
print("떼어 낸 대상 상위", collections.Counter(d["to"] for d in dropped).most_common(8))
keys = set(out)
print("남은 unknown to:", sum(1 for r in out.values() for u in r.get("uses", []) if u["to"] not in keys))
EOF
```
Expected (🔵 오늘 데이터 기준): `id→이름 고침 94` · `unknown-target` ≈ 439 · `unknown-shallow` ≈ 94 · **남은 unknown to: 0**.

- [ ] **Step 2: `verify-terms` 가 통과할지 미리 본다** — 보정본을 임시 파일로 쓰고 `terms_db.py` 를 돌린다 (원본은 건드리지 않는다)

```bash
.venv/bin/python - <<'EOF'
import json, sys
sys.path[:0] = ["runner", "machine"]
from mode1.survey import AnnotateSymbolsStage as S
plan = json.load(open("out/codegraph-raw/batches.json"))
out, _ = S.normalize_records(json.load(open("machine/terms-reading.json")), S.name_of(plan))
json.dump(out, open("/tmp/reading-normalized.json", "w"), ensure_ascii=False, indent=1)
EOF
.venv/bin/python machine/terms_db.py out/codegraph-raw/codegraph.json --repo . \
  --reading /tmp/reading-normalized.json -o /tmp/terms-check 2>&1 | grep -c "용어에 없다"
```
Expected: `0`. (`where L2 줄 없음` 5건과 `L1 파일 없음` 3건은 남는다 — 세션이 줄을 틀리게 쓴 것이라 이 계획 밖. 그 8건이 exit 1 을 내면 그것이 다음 결함이다 — 기록만 한다.)

---

### Task 6: 문서 · 게이트 · 커밋

**Files:**
- Regenerate: `runner/README.md`
- Modify: `runner/CLAUDE.md` — 파일 전략 설명이 "가중치 순, 장벽 없음" 이면 "의존 파일이 끝난 순, 준비 집합 풀 · 순환만 shallow/2패스" 로 한 줄 고친다 (있을 때만)

- [ ] **Step 1: README 재생성 · 게이트**

```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools
.venv/bin/python -m pytest -q          # 빨강은 test_wiki 와 test_이_저장소_실측 둘만 (이 계획 전부터)
npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
```

- [ ] **Step 2: 커밋**

```bash
git add runner/README.md runner/CLAUDE.md docs/superpowers/plans/2026-09-20-bottomup-leaf-reuse.md
git commit -m "[docs] : 파일 전략은 준비 집합 풀 - 잎 레코드 재사용 계획과 readme 갱신"
```

---

### Task 7: 실행 절차 (사용자 "돌려" 로만)

코드가 아니라 절차다. 비용 ≈ $57 (R6 와 같은 규모, 세션 수 79 + 2패스 소수).

- [ ] **Step 1: 깨끗한 시작**

```bash
cp evals/runs/2026-09-19-mode1-report-builder-cold-file-sonnet.json <scratchpad>/r6-before-fix.json
rm -rf out machine/terms-reading.json && test ! -e out && echo clean
```

- [ ] **Step 2: 실행**

```bash
nohup caffeinate -i .venv/bin/python runner/run_mode1.py . --cold --strategy file \
  --json evals/runs/$(date +%F)-mode1-report-builder-cold-file-sonnet-ready.json > <scratchpad>/mode1-ready.log 2>&1 &
```

- [ ] **Step 3: 잴 것과 기대**

| 항목 | 어디서 | R6 (고치기 전) | 기대 |
|---|---|---|---|
| 첫 물결 투입 수 | 로그 첫 줄들 | 78 동시 제출 | 잎 파일 40개 중 8 |
| "순환 — 강제 투입" 줄 | 로그 | — | **0** (이 저장소는 순환 0) |
| `shallow` 레코드 | `terms-reading.json` | 376 | ≈ 0 |
| 2패스 세션 | `/p2` 행 | 2 | 0 |
| `uses.to` 가 노드 id | `terms-reading.json` | 94 | 0 |
| `dropped-uses.csv` 행 | 새 산출물 | — | 외부 의존 수(🟡 100~200) |
| `verify-terms` `용어에 없다` | 로그 | 533 | **0** → 처음으로 `outline-wiki` 이후 단계가 돈다 |
| `annotate-symbols` 벽시계 | JSON | 34분 44초 | 🟡 +1 물결 ≈ 36~38분 (비노드 8.5분 포함) |
| 비용 | JSON | $57.15 | 🟡 ±10% — 프롬프트에 발췌가 실려 첫 턴이 조금 무겁다 |

- [ ] **Step 4: 기록** — `evals/README.md` 표에 한 줄, `docs/2026-09-19-mode1-역대-실측과-패치-이력.md` §1 표에 R7 행과 §3 결함 표의 ①②③④ 를 "닫힘" 으로.

---

## 검증 — 끝에서 끝까지

1. `.venv/bin/python -m pytest runner -q` — 새 시험 12개(프롬프트 2 · pending 1 · 보정 4 · 스케줄러 3 · dep_files 1 · 기존 스케줄러 2 유지) 포함 전부 통과.
2. `npm run typecheck:py` 0 errors · `test/test_no_any.py` 통과.
3. Task 5 의 실데이터 시뮬레이션: `남은 unknown to: 0` · `용어에 없다` 0건.
4. Task 4 의 세 파일 시험이 고정하는 것: 동시 8 인데 b→a→c 직렬 · a 프롬프트에 `b.g — 지 뜻` · 미조사 절 없음 · 2패스 없음.
5. 실제 실행은 Task 7 — 사용자 지시로만.

## 열어 둔 것 (계획 밖, 기록만)

- `where L2 줄 없음` 5건 · `L1 파일 없음` 3건 — 세션이 줄 번호를 틀린 것. `verify-terms` 의 다음 걸림돌.
- 파일 전략에서 `file_cache` 지시(프롬프트 "읽는 법" 1번)는 읽을 둘째 세션이 없어 낭비 턴이다(R6 에서 55회 put). 전략이 `file` 이면 그 절을 빼는 것 — 별개 판단.
- NONNODE 가 파일 세션 뒤 혼자 8.5분 도는 것 — `file` 레코드를 파일 세션이 쓰게 하는 안, 별개.
- 짧은 이름·접두 틀림(258건)은 프롬프트 계약으로 줄기를 기대하고, 남으면 `dropped-uses.csv` 에서 본다. 유일 접미 보정은 사용자 결정으로 하지 않았다.
- 파일 전략의 증분(`--cold` 전용 해제) — Diff 실측을 위해 필요하나 이 계획 밖.
- `runner/mode1/prompt/survey_prompt.md` 는 손으로 쓴 스냅샷이라 이미 낡았다(옛 `dep_excerpt` 서명). 프롬프트를 바꾼 뒤 갱신하거나 생성물로 바꾸는 것 — 별개.
