# 전수조사 심볼 해석(Symbol Resolution) 개선 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mode 1 `survey` 가 낸 `uses.to` 참조를 기계적으로 해석해 `terms` 단계에서 파이프라인이 멈추지 않게 한다.

**Architecture:** 두 갈래다. (1) **원인 제거** — `survey_plan.py` 가 `depends_on` 을 정적 도구의 내부 id(`C10`)가 아니라 사람이 읽는 이름으로 낸다. 이것이 `dep_excerpt` 가 아무것도 못 찾던 근본 원인이다. (2) **사후 해석** — `terms_db.py` 에 결정론적 해석 사다리(정확 조상 → 짧은 이름 → 외부/파일 합성 → 격하)를 넣어 남은 참조를 처리한다. LLM 프롬프트는 한 곳(external 안내)만 손댄다.

**Tech Stack:** Python 3.14 (표준 라이브러리만) · pytest · 기존 `codegraph/*.py`

---

## 배경 — 이 계획이 근거로 삼는 실측

🔵 2026-08-30 QtVisionEdit(C++) 백지 실행 1건. 근거 `evals/runs/2026-08-30-mode1-qtvisionedit-cold-sonnet.json`.

`survey` 층 6개는 전부 성공했으나 `terms` 가 종료 코드 1로 멈춰 `wiki`·`build`·`check` 가 돌지 못했다.
용어 166개 중 **실패 50건**, 그 실패가 가리키는 **서로 다른 대상 36개**다.

🔵 이 계획을 쓰며 실제 데이터로 확인한 두 결함:

**결함 1 — `dep_excerpt` 가 모든 배치에서 빈 문자열을 낸다.**
`survey-plan.json` 의 심볼 `depends_on` 은 노드 **id** 목록(`["C10"]`)인데
(`codegraph/survey_plan.py:142-143` 이 `edges` 의 id 쌍에서 만든다),
`dep_excerpt` 는 그것을 **이름으로 키가 잡힌** `terms-reading.json` 에서 찾는다
(`codegraph/run_mode1.py:392-394`). 교집합이 언제나 공집합이다.

```
batch L1-B00: depends_on=['C10', 'C21', 'C23'] -> dep_excerpt=EMPTY
batch L2-B00: depends_on=['C10', 'C11', 'C25', 'C29'] -> dep_excerpt=EMPTY
batch L3-B00: depends_on=['C10', 'C11', 'C12', 'C6'] -> dep_excerpt=EMPTY
batch L4-B00: depends_on=['C4', 'C5', 'C6', 'C7'] -> dep_excerpt=EMPTY
```

즉 배치 프롬프트의 **"너보다 아래층은 이미 끝났다 — 다시 조사하지 마라"** 절이 매 실행 비어 있었다.
Bottom-Up 층 설계(`codegraph/CLAUDE.md` 의 K1~K8)의 핵심 기제가 작동한 적이 없다.

**결함 2 — 프롬프트가 내부 id 를 그대로 노출한다.**
`codegraph/run_mode1.py:412-414` 가 `의존 -> C10` 을 렌더한다. 세션은 `C10` 이 무엇인지 풀 방법이
없고(결함 1로 발췌도 비어 있다) `uses.to` 에 `C10` 을 그대로 적었다 — 실패 6건이 이것이다.

**왜 시험이 못 잡았나.** `codegraph/test_survey_plan.py:15` 의 `_cg` 와
`codegraph/test_run_mode1.py:258-262` 의 `_배치` 가 **`id` 와 `name` 을 같은 값으로** 만든다.
합성 데이터에서는 두 결함이 보이지 않는다. 루트 `CLAUDE.md` 의 "합성 데이터만으로 검증하지 말 것" 이
가리키는 바로 그 사고다.

**해석 사다리 시뮬레이션** — 위 실측 36개 대상에 아래 Task 3~5 의 규칙을 적용한 결과:

| 판정 | 건수 | 예 |
|---|---:|---|
| 정확 조상으로 rollup | 2 | `SJH::Server::MessageRouter::AddHandler` → `SJH::Server::MessageRouter` |
| 짧은 이름으로 rollup | 15 | `MakeErrorMessage` → `SJH::Server::MakeErrorMessage` |
| external 합성 | 10 | `cv::warpPerspective` · `Ui::MainWindow` |
| file 합성 | 1 | `server/payloadlimits.h` |
| 남음(격하) | 8 | `C10`~`C30` 5개 + `kHeaderLengthFieldSize` 등 3개 |

Task 1 이 `C10` 계열 5개를 원천 제거하므로 **최종 격하 대상은 3개**로 좁혀진다.

---

## File Structure

| 파일 | 책임 | 이 계획에서 |
|---|---|---|
| `codegraph/survey_plan.py` | 코드 지도를 층·배치로 나눈다 | `depends_on` 을 이름으로 낸다 (Task 1) |
| `codegraph/test_survey_plan.py` | 위 회귀 | id≠name 시험 추가 (Task 1) |
| `codegraph/run_mode1.py` | 실행기·프롬프트 | `dep_excerpt` 회귀 시험 · external 안내 (Task 2, 6) |
| `codegraph/test_run_mode1.py` | 위 회귀 | id≠name 픽스처 (Task 2) |
| `codegraph/terms_db.py` | 사전 병합·인용 판정 | 해석 사다리 신설 (Task 3~5) |
| `codegraph/test_terms_db.py` | 위 회귀 | 해석 사다리 시험 (Task 3~5) |

새 파일은 만들지 않는다. 해석 사다리는 `terms_db.py` 안 순수 함수 두 개(`resolve_target` ·
`synthesize_record`)이며, 플러그인 구조나 레지스트리를 만들지 않는다 — 루트 `CLAUDE.md` 의
**거울 함정** 경고 대상이다. 구현자 1, 소비자 1 이면 인터페이스를 만들지 않는다.

---

### Task 1: `survey_plan.py` 가 `depends_on` 을 이름으로 낸다

**Files:**
- Modify: `codegraph/survey_plan.py:139-144`
- Test: `codegraph/test_survey_plan.py`

- [ ] **Step 1: id 와 name 이 다른 회귀 시험을 쓴다**

`codegraph/test_survey_plan.py` 의 `test_배치는_자기_심볼의_의존_대상을_들고_있다` 바로 아래에 더한다:

```python
def test_의존_대상은_id_가_아니라_이름이다():
    """실제 codegraph 는 id 가 `C10`, name 이 `AlignmentOptions` 로 서로 다르다.

    `dep_excerpt` 는 이름으로 키가 잡힌 terms-reading.json 에서 찾으므로,
    여기서 id 를 내면 교집합이 영원히 공집합이 된다(2026-08-30 실측으로 확인).
    """
    cg = {"nodes": [{"id": "C10", "name": "AlignmentOptions", "kind": "class",
                     "file": "app/opts.h", "line": 21},
                    {"id": "C11", "name": "PanoramaOptions", "kind": "class",
                     "file": "app/pano.h", "line": 9}],
          "edges": [{"from": "C11", "to": "C10"}]}
    top = [L for L in plan(cg)["layers"] if L.get("level") == 1][0]
    assert top["batches"][0]["symbols"][0]["depends_on"] == ["AlignmentOptions"]
```

- [ ] **Step 2: 실패를 확인한다**

Run: `cd /Users/escatrgot/LLM-Tools/report-builder && .venv/bin/python -m pytest codegraph/test_survey_plan.py -k 이름이다 -v`
Expected: FAIL — `assert ['C10'] == ['AlignmentOptions']`

- [ ] **Step 3: 최소 구현 — id 를 이름으로 바꿔 담는다**

`codegraph/survey_plan.py` 의 `plan()` 안, `layers = []` 바로 위에 이름 표를 만든다:

```python
    # 배치가 내는 depends_on 은 **이름**이다. `dep_excerpt` 가 이름으로 키가 잡힌
    # terms-reading.json 에서 찾기 때문이다 — id 를 내면 교집합이 언제나 공집합이 된다
    # (2026-08-30 QtVisionEdit 실측: 모든 배치에서 발췌가 비어 있었다).
    name_of = {i: (n.get("name") or i) for i, n in first.items()}

    layers = []
```

이어서 `"depends_on"` 줄을 고친다 (`codegraph/survey_plan.py:142-143`):

```python
                              "depends_on": sorted({name_of[d] for (o, d) in edges
                                                    if o == s and d in first and d != s})}
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_survey_plan.py -v`
Expected: 전부 PASS (기존 `test_배치는_자기_심볼의_의존_대상을_들고_있다` 는 `_cg` 가 id==name 이라 그대로 통과한다)

- [ ] **Step 5: 커밋**

```bash
git add codegraph/survey_plan.py codegraph/test_survey_plan.py
git commit -m "[fix] : 전수조사 계획의 의존 대상을 내부 id 가 아니라 이름으로 낸다"
```

---

### Task 2: `dep_excerpt` 가 실제로 발췌하는지 실데이터 꼴로 고정한다

Task 1 이 원인을 없앴다. 이 Task 는 **다시 깨지지 않게** 회귀를 박는다.

**Files:**
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: id≠name 픽스처로 실패 시험을 쓴다**

`codegraph/test_run_mode1.py` 의 `_배치()` 정의 아래에 더한다:

```python
def _배치_실데이터꼴():
    """실제 survey-plan.json 의 꼴 — id 는 `C11`, name 은 사람이 읽는 이름이다.

    기존 `_배치()` 는 id 와 name 을 같게 두어 이 결함을 못 잡았다
    (2026-08-30: 모든 배치에서 dep_excerpt 가 빈 문자열이었다).
    """
    return {"id": "L1-B00", "files": ["app/pano.h"],
            "symbols": [{"id": "C11", "name": "PanoramaOptions", "file": "app/pano.h",
                         "line": 9, "kind": "class", "in_cycle": False,
                         "depends_on": ["AlignmentOptions"]}]}


def test_발췌는_이름으로_아래층_레코드를_찾는다():
    """depends_on 이 id 면 이름으로 키가 잡힌 사전에서 영원히 못 찾는다."""
    merged = {"AlignmentOptions": {"means": "정렬 옵션을 담는 값 객체."}}
    out = R.dep_excerpt(merged, _배치_실데이터꼴())
    assert "AlignmentOptions" in out
    assert "정렬 옵션을 담는 값 객체." in out


def test_프롬프트는_내부_id_를_노출하지_않는다():
    """세션이 `의존 -> C11` 을 보면 그 문자열을 uses.to 에 그대로 적는다 — 실제로 6건 났다."""
    p = R.survey_batch_prompt("/r", "/root", _배치_실데이터꼴(), "")
    assert "AlignmentOptions" in p
    assert "C11" not in p
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_run_mode1.py -k "발췌는_이름으로 or 노출하지" -v`
Expected: `test_발췌는_이름으로_아래층_레코드를_찾는다` PASS (Task 1 이 이미 고쳤다),
`test_프롬프트는_내부_id_를_노출하지_않는다` **FAIL** — 프롬프트가 심볼 자신의 `id` 를 쓰지는 않으나
`s["id"]` 가 아니라 `s["name"]` 을 쓰는지 확인이 필요하다.

- [ ] **Step 3: 프롬프트 렌더가 이름을 쓰는지 확인하고 필요하면 고친다**

`codegraph/run_mode1.py:411-415` 를 연다. 현재:

```python
    syms = "\n".join(
        "  - %s (%s) %s:%s   의존 -> %s"
        % (s["name"], s["kind"], s["file"], s["line"],
           ", ".join(s.get("depends_on") or []) or "없음")
        for s in batch["symbols"])
```

`s["name"]` 을 이미 쓰고 있고 `depends_on` 은 Task 1 이 이름으로 바꿨으므로 **코드 변경은 없다.**
시험이 통과하는지만 확인한다. 만약 FAIL 이면 위 코드가 `s["id"]` 를 쓰고 있다는 뜻이니
`s["name"]` 으로 바꾼다.

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_run_mode1.py -v`
Expected: 전부 PASS

- [ ] **Step 5: 커밋**

```bash
git add codegraph/test_run_mode1.py codegraph/run_mode1.py
git commit -m "[test] : 배치 발췌와 프롬프트가 내부 id 를 노출하지 않는지 실데이터 꼴로 고정"
```

---

### Task 3: 해석 사다리 — 조상 rollup

**Files:**
- Modify: `codegraph/terms_db.py` (`_stem` 아래에 추가)
- Test: `codegraph/test_terms_db.py`

- [ ] **Step 1: 실패 시험을 쓴다**

`codegraph/test_terms_db.py` 의 `test_check_flags_unknown_uses_target` 아래에 더한다:

```python
# ── 5. 심볼 해석 — 이름꼴이 달라도 같은 개체면 찾아낸다
def test_resolve_finds_exact_ancestor():
    """`A::B::C` 가 없고 `A::B` 가 있으면 `A::B` 로 되돌린다."""
    keys = {"SJH::Server::MessageRouter"}
    assert T.resolve_target("SJH::Server::MessageRouter::AddHandler", keys) \
        == "SJH::Server::MessageRouter"


def test_resolve_falls_back_to_unique_short_name():
    """네임스페이스 표기만 다른 경우 — 짧은 이름이 딱 하나면 그것으로 본다."""
    keys = {"SJH::Server::MakeErrorMessage"}
    assert T.resolve_target("MakeErrorMessage", keys) == "SJH::Server::MakeErrorMessage"


def test_resolve_strips_namespace_in_the_other_direction():
    """반대 방향도 된다 — 참조가 길고 사전 키가 짧은 경우."""
    keys = {"SessionStore"}
    assert T.resolve_target("SJH::Server::SessionStore::FindImage", keys) == "SessionStore"


def test_resolve_refuses_ambiguous_short_name():
    """짧은 이름이 둘 이상이면 찍지 않는다 — 틀린 간선을 만드느니 못 찾은 것이 낫다."""
    keys = {"A::Message", "B::Message"}
    assert T.resolve_target("Message", keys) is None


def test_resolve_returns_none_when_nothing_matches():
    assert T.resolve_target("kHeaderLengthFieldSize", {"Other"}) is None
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k resolve -v`
Expected: FAIL — `AttributeError: module 'terms_db' has no attribute 'resolve_target'`

- [ ] **Step 3: 최소 구현**

`codegraph/terms_db.py` 의 `_stem` 함수 정의 바로 아래에 더한다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='resolve_target']"/>
# 사전에 없는 uses.to 를 아는 키로 되돌린다. 못 되돌리면 None.
# 쓰는 것: verify_citations.short · 쓰이는 곳: resolve_uses
def resolve_target(target, keys):
    """사전에 없는 `uses.to` 를 아는 키로 해석한다. 못 하면 `None`.

    링커의 심볼 해석과 같은 문제다 — 여러 표기가 한 개체를 가리킨다. 사다리는 둘이고
    **정확한 쪽을 먼저** 본다. 짧은 이름은 하나로 좁혀질 때만 쓴다 — 둘 이상이면
    찍지 않는다. 틀린 간선을 만드는 것이 못 찾은 것보다 나쁘다.

      1) 정확한 조상   `A::B::C` -> `A::B` -> `A`
      2) 조상의 짧은 이름이 사전에 딱 하나  `SJH::Server::SessionStore::FindImage` -> `SessionStore`
    """
    if target in keys:
        return target
    parts = target.split("::")
    for i in range(len(parts) - 1, 0, -1):
        cand = "::".join(parts[:i])
        if cand in keys:
            return cand
    by_short = {}
    for k in keys:
        by_short.setdefault(short(k), []).append(k)
    for i in range(len(parts), 0, -1):
        hits = by_short.get(short("::".join(parts[:i])), ())
        if len(hits) == 1:
            return hits[0]
    return None
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k resolve -v`
Expected: 5개 PASS

- [ ] **Step 5: 커밋**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : 사전에 없는 참조를 조상과 짧은 이름으로 되돌리는 해석 사다리"
```

---

### Task 4: 해석 사다리 — 외부 심볼과 파일 합성

rollup 으로 안 되는 것 중 **분류는 가능한** 것들이다. 원문을 고치지 않고 레코드를 만들어 준다.

**Files:**
- Modify: `codegraph/terms_db.py`
- Test: `codegraph/test_terms_db.py`

- [ ] **Step 1: 실패 시험을 쓴다**

Task 3 의 시험 아래에 더한다:

```python
def test_synthesize_makes_an_external_record_for_a_known_prefix(tmp_path):
    """OpenCV·Qt·표준 라이브러리 심볼은 `kind: external` 로 사전에 등록한다.

    스키마는 이미 external 을 지원한다(KINDS). 없던 것은 **그 자리를 채우는 절차**다.
    """
    rec = T.synthesize_record("cv::warpPerspective", str(tmp_path))
    assert rec is not None
    assert rec["kind"] == "external"
    assert rec["where"] == ""          # external 은 where 가 없어도 된다
    assert rec["source"] == "reading"


def test_synthesize_makes_a_file_record_for_a_real_path(tmp_path):
    """저장소에 실제로 있는 경로면 `kind: file` 로 만든다. where 는 `경로:1`."""
    (tmp_path / "server").mkdir()
    (tmp_path / "server" / "payloadlimits.h").write_text("// server/payloadlimits.h\n",
                                                        encoding="utf-8")
    rec = T.synthesize_record("server/payloadlimits.h", str(tmp_path))
    assert rec is not None
    assert rec["kind"] == "file"
    assert rec["where"] == "server/payloadlimits.h:1"


def test_synthesize_refuses_an_unknown_bare_name(tmp_path):
    """접두사도 아니고 실재하는 파일도 아니면 만들지 않는다 — 지어내지 않는다."""
    assert T.synthesize_record("kHeaderLengthFieldSize", str(tmp_path)) is None
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k synthesize -v`
Expected: FAIL — `AttributeError: module 'terms_db' has no attribute 'synthesize_record'`

- [ ] **Step 3: 최소 구현**

`codegraph/terms_db.py` 의 `resolve_target` 아래에 더한다:

```python
# 이 접두사로 시작하는 이름은 저장소 밖 라이브러리다. **목록을 늘리기 전에 멈춘다** —
# 늘어난다는 것은 그 저장소의 정적 수집기가 그 심볼을 놓쳤다는 뜻일 수도 있다.
EXTERNAL_PREFIXES = ("cv::", "std::", "Ui::", "Qt::", "boost::")


# <include file="docs/codegraph/comments.xml" path="//term[@id='synthesize_record']"/>
# 해석은 안 되지만 분류는 되는 참조에 레코드를 만들어 준다. 못 하면 None.
# 쓰는 것: 없음 · 쓰이는 곳: resolve_uses
def synthesize_record(target, repo):
    """해석 못 한 참조를 **분류할 수 있으면** 레코드로 만든다. 못 하면 `None`.

    원문을 고치는 rollup 과 달리 이쪽은 `uses.to` 를 그대로 두고 그 이름의 레코드를 만든다 —
    정밀도 손실이 없다. 대신 분류 규칙(접두사 목록·파일 존재)을 사람이 유지해야 한다.

    **지어내지 않는다.** 접두사에 맞거나 실제로 그 파일이 있을 때만 만든다.
    """
    if target.startswith(EXTERNAL_PREFIXES):
        return {"kind": "external", "module": "", "where": "",
                "means": f"저장소 밖 라이브러리의 {target}.",
                "uses": [], "neighbors": [], "confidence": "LOW", "source": "reading"}
    if "/" in target and os.path.isfile(os.path.join(repo, target)):
        return {"kind": "file", "module": os.path.dirname(target), "where": f"{target}:1",
                "means": f"소스 파일 {target}.",
                "uses": [], "neighbors": [], "confidence": "LOW", "source": "reading"}
    return None
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k synthesize -v`
Expected: 3개 PASS

- [ ] **Step 5: 커밋**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : 외부 라이브러리 심볼과 실재하는 파일에 레코드를 합성한다"
```

---

### Task 5: 사다리를 병합에 배선하고, 남은 것은 실패가 아니라 격하한다

**Files:**
- Modify: `codegraph/terms_db.py` (`merge_terms` 아래에 `resolve_uses` 신설 · `check_terms:321-322` 수정 · `main` 배선)
- Test: `codegraph/test_terms_db.py`

- [ ] **Step 1: 실패 시험을 쓴다**

```python
def test_resolve_uses_rewrites_rollup_targets(tmp_path):
    """rollup 된 참조는 uses.to 가 아는 키로 **바뀐다.**"""
    db = {"SessionStore": {"kind": "class", "module": "server", "where": "server/s.h:1",
                           "means": "세션을 담는다.", "uses": [], "neighbors": [],
                           "source": "reading"},
          "HandleFetch": {"kind": "function", "module": "server", "where": "server/f.cpp:3",
                          "means": "가져온다.", "neighbors": [], "source": "reading",
                          "uses": [{"to": "SJH::Server::SessionStore", "kind": "dependency",
                                    "label": "calls", "where": "server/f.cpp:5"}]}}
    out, left = T.resolve_uses(db, str(tmp_path))
    assert out["HandleFetch"]["uses"][0]["to"] == "SessionStore"
    assert left == []


def test_resolve_uses_synthesizes_and_keeps_the_original_name(tmp_path):
    """합성된 참조는 이름이 그대로 남고, 사전에 그 키가 생긴다."""
    db = {"Warp": {"kind": "function", "module": "core", "where": "core/w.cpp:2",
                   "means": "휜다.", "neighbors": [], "source": "reading",
                   "uses": [{"to": "cv::warpPerspective", "kind": "dependency",
                             "label": "calls", "where": "core/w.cpp:9"}]}}
    out, left = T.resolve_uses(db, str(tmp_path))
    assert out["Warp"]["uses"][0]["to"] == "cv::warpPerspective"
    assert out["cv::warpPerspective"]["kind"] == "external"
    assert left == []


def test_resolve_uses_reports_what_it_could_not_resolve(tmp_path):
    """못 푼 것은 조용히 지우지 않고 목록으로 돌려준다."""
    db = {"Decode": {"kind": "function", "module": "protocol", "where": "protocol/m.cpp:1",
                     "means": "푼다.", "neighbors": [], "source": "reading",
                     "uses": [{"to": "kHeaderLengthFieldSize", "kind": "dependency",
                               "label": "reads", "where": "protocol/m.cpp:4"}]}}
    out, left = T.resolve_uses(db, str(tmp_path))
    assert ("Decode", "kHeaderLengthFieldSize") in left


def test_unresolvable_target_is_unfounded_not_failure(tmp_path):
    """못 푼 참조는 파이프라인을 멈추지 않는다 — 3값의 '근거 없음' 이다."""
    r = _reading(); r["build_terms"]["uses"][0]["to"] = "ghost"
    out = T.check_terms(T.merge_terms({}, r), _repo(tmp_path))
    assert any(lvl == "근거 없음" and "ghost" in why for lvl, term, why in out)
    assert not any(lvl == "실패" for lvl, term, why in out)
```

**주의** — 마지막 시험은 기존 `test_check_flags_unknown_uses_target` 과 **정면으로 충돌한다.**
그 시험은 같은 상황을 "실패" 로 기대한다. 정책이 바뀌었으므로 기존 시험을 지우고 이것으로 대체한다.
`codegraph/test_terms_db.py` 에서 `test_check_flags_unknown_uses_target` 함수를 통째로 삭제한다.

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k "resolve_uses or unresolvable" -v`
Expected: FAIL — `AttributeError: module 'terms_db' has no attribute 'resolve_uses'`

- [ ] **Step 3: `resolve_uses` 를 만든다**

`codegraph/terms_db.py` 의 `merge_terms` 아래에 더한다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='resolve_uses']"/>
# 사전에 없는 uses.to 를 해석하거나 합성한다. 못 푼 것은 목록으로 돌려준다.
# 쓰는 것: resolve_target, synthesize_record, _recompute_neighbors · 쓰이는 곳: terms_db.main
def resolve_uses(db, repo):
    """`(고친 사전, 못 푼 [(용어, 대상), …])`. 입력 dict 는 바꾸지 않는다.

    사다리는 셋이고 순서가 정책이다.
      1) `resolve_target` 으로 되돌린다  -> `uses.to` 를 **고쳐 쓴다**(정밀도를 조금 잃는다)
      2) `synthesize_record` 로 만든다   -> `uses.to` 는 **그대로**, 사전에 키를 더한다
      3) 둘 다 안 되면 그대로 두고 보고한다 -> `check_terms` 가 '근거 없음' 으로 격하한다

    **1번을 2번보다 먼저 본다.** 아는 심볼로 되돌릴 수 있으면 그것이 언제나 낫다 —
    합성 레코드는 뜻이 비어 있어 Mode 1.5 의 재료가 되지 못한다.
    """
    out = {k: dict(v, uses=[dict(u) for u in v.get("uses", [])]) for k, v in db.items()}
    left = []
    for key in sorted(out):
        for u in out[key].get("uses", []):
            t = u.get("to")
            if not t or t in out:
                continue
            hit = resolve_target(t, set(out))
            if hit:
                u["to"] = hit
                continue
            made = synthesize_record(t, repo)
            if made:
                out[t] = made
                continue
            left.append((key, t))
    _recompute_neighbors(out)
    return dict(sorted(out.items())), left
```

- [ ] **Step 4: `check_terms` 가 격하하도록 고친다**

`codegraph/terms_db.py:321-322` 를 연다. 현재:

```python
            if u.get("to") not in db:
                out.append(("실패", key, f"uses.to 가 용어에 없다: {u.get('to')!r}"))
```

이렇게 바꾼다:

```python
            if u.get("to") not in db:
                # **실패가 아니라 근거 없음이다.** resolve_uses 가 사다리를 다 타고도 못 푼
                # 참조는 파이프라인을 멈출 근거가 못 된다 — 세션이 실제로 읽은 심볼인데
                # 정적 수집기가 노드로 뽑지 않은 경우가 섞여 있다(익명 네임스페이스 상수 등).
                # 2026-08-30 QtVisionEdit 실측: 이 한 줄이 파이프라인 전체를 막았다.
                out.append(("근거 없음", key, f"uses.to 가 용어에 없다: {u.get('to')!r}"))
```

- [ ] **Step 5: `main` 에 배선한다**

`codegraph/terms_db.py` 의 `main()` 에서 `problems = check_terms(db, repo)` **바로 위**에 더한다:

```python
    db, unresolved = resolve_uses(db, repo)
    if unresolved:
        print(f"해석 못 한 참조 {len(unresolved)}건 — 근거 없음으로 남긴다")
        for term, target in unresolved[:10]:
            print(f"  {term} -> {target!r}")

    problems = check_terms(db, repo)
```

- [ ] **Step 6: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -v`
Expected: 전부 PASS (`test_check_flags_unknown_uses_target` 은 Step 1 에서 지웠다)

- [ ] **Step 7: 전체 시험을 돌린다**

Run: `.venv/bin/python -m pytest codegraph/ -q`
Expected: 통과 수가 늘고 실패 0

- [ ] **Step 8: 커밋**

```bash
git add codegraph/terms_db.py codegraph/test_terms_db.py
git commit -m "[feat] : 참조 해석을 병합에 배선하고 못 푼 것은 실패가 아니라 근거 없음으로 둔다"
```

---

### Task 6: 배치 프롬프트에 `external` 탈출구를 적는다

스키마는 이미 `kind: external` 을 받는데(`KINDS`) 프롬프트가 그 존재를 알려 주지 않았다.
Task 4 가 사후 합성으로 메우지만, 세션이 처음부터 옳게 쓰면 합성이 필요 없다.

**Files:**
- Modify: `codegraph/run_mode1.py:440-449` (`survey_batch_prompt` 의 "레코드 계약" 절)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패 시험을 쓴다**

```python
def test_배치_프롬프트가_외부_심볼_적는_법을_알려_준다():
    """스키마는 external 을 받는데 프롬프트가 그 말을 안 해 실패 10건이 났다(2026-08-30)."""
    p = R.survey_batch_prompt("/r", "/root", _배치_실데이터꼴(), "")
    assert "external" in p
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_run_mode1.py -k 외부_심볼 -v`
Expected: FAIL — `assert 'external' in p`

- [ ] **Step 3: 프롬프트에 한 줄을 더한다**

`codegraph/run_mode1.py` 의 `survey_batch_prompt` 안, `- confidence = HIGH(...)` 줄 **아래**에 더한다:

```
- **저장소 밖 심볼**(`cv::` `std::` `Qt::` 같은 라이브러리)을 uses[].to 로 가리켜야 하면
  그 이름의 레코드도 함께 만든다 — `{{kind:"external", where:"", means:"...", confidence:"LOW"}}`.
  where 는 비운다. **사전에 없는 이름을 uses[].to 에 그냥 적으면 기계 검사에 걸린다.**
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_run_mode1.py -v`
Expected: 전부 PASS

- [ ] **Step 5: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[docs] : 배치 프롬프트에 저장소 밖 심볼을 external 로 적는 법을 넣는다"
```

---

### Task 7: 실측 레코드로 사다리를 대조한다 (골든)

합성 데이터만으로 검증하지 않는다 — 이 결함 자체가 합성 시험을 통과했었다.

**Files:**
- Test: `codegraph/test_terms_db.py`

- [ ] **Step 1: 골든 시험을 쓴다**

`codegraph/test_terms_db.py` 맨 아래에 더한다:

```python
# ── 6. 골든 — 실제 저장소의 전수조사 레코드로 사다리를 대조한다
@pytest.mark.skipif(not os.path.isdir(CPP_REPO), reason="GRAPHICS_REPO 가 없다")
def test_resolve_uses_leaves_few_unresolved_on_a_real_reading(tmp_path):
    """실측 레코드에서 못 푸는 참조가 소수로 남는지 본다.

    2026-08-30 QtVisionEdit 실측 기준 — 서로 다른 대상 36개 중 rollup 17 · 합성 11 ·
    남는 것 8(그중 5개는 survey_plan 의 id 결함이 낸 것이라 이제 나오지 않는다).
    숫자를 못 박지 않는다. **대부분이 풀리는가**만 본다.
    """
    reading = os.path.join(CPP_REPO, "docs", "codegraph", "terms-reading.json")
    if not os.path.isfile(reading):
        pytest.skip("전수조사 레코드가 아직 없다")
    db = T.merge_terms({}, json.load(open(reading, encoding="utf-8")))
    before = sum(1 for r in db.values() for u in r.get("uses", [])
                 if u.get("to") not in db)
    _, left = T.resolve_uses(db, CPP_REPO)
    assert before > 0, "이 골든은 못 푼 참조가 있는 레코드라야 뜻이 있다"
    assert len(left) < before / 2, f"사다리가 절반도 못 풀었다: {before} -> {len(left)}"
```

- [ ] **Step 2: 시험을 돌린다**

Run: `.venv/bin/python -m pytest codegraph/test_terms_db.py -k real_reading -v`
Expected: `GRAPHICS_REPO` 가 없으면 SKIP (실패가 아니다). 있으면 PASS

- [ ] **Step 3: 실측 저장소로 직접 확인한다**

Run:
```bash
.venv/bin/python codegraph/terms_db.py \
  /Users/escatrgot/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit/out/codegraph-raw/codegraph.json \
  --repo /Users/escatrgot/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit \
  --reading /Users/escatrgot/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit/docs/codegraph/terms-reading.json
echo "종료 코드: $?"
```
Expected: 종료 코드 **0**. "실패" 건수가 0 이고 "근거 없음" 이 소수로 남는다

- [ ] **Step 4: 커밋**

```bash
git add codegraph/test_terms_db.py
git commit -m "[test] : 실제 전수조사 레코드로 해석 사다리를 대조하는 골든"
```

---

### Task 8: 파이프라인을 다시 돌려 실측을 갱신한다

**Files:**
- Create: `evals/runs/2026-08-30-mode1-qtvisionedit-resolved.json`
- Modify: `ARCHITECTURE.md` §3 · `codegraph/CLAUDE.md`

- [ ] **Step 1: 산출물을 지우고 백지에서 다시 돌린다**

이전 실행의 샤드가 남아 있으면 `survey` 를 건너뛴다(J4). **의도적으로 지운다:**

```bash
TGT=/Users/escatrgot/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit
git -C "$TGT" status --short          # 먼저 본다. 커밋 안 된 것이 있으면 멈춘다
rm -rf "$TGT/out/codegraph-raw/_shards"
```

- [ ] **Step 2: 돌린다**

```bash
.venv/bin/python codegraph/run_mode1.py \
  /Users/escatrgot/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit \
  --json evals/runs/2026-08-30-mode1-qtvisionedit-resolved.json
```
Expected: `terms` 가 통과하고 `wiki` · `build` · `check` 가 처음으로 돈다.
비용은 이전 실행 기준 `survey` 만 $9.22 였으므로 **`wiki` 를 더하면 그 이상**이다 —
돌리기 전에 사용자에게 알린다.

- [ ] **Step 3: 실측을 문서에 옮긴다**

`ARCHITECTURE.md` §3 의 "새 구조 실측" 표를 이번 실행 값으로 갱신한다. 이전 표(멈춘 실행)는
지우지 말고 "🔵 2026-08-30 1차 — `terms` 에서 멈춤" 으로 남긴다. 무엇이 왜 바뀌었는지가 근거다.

`codegraph/CLAUDE.md` 의 "Bottom-Up 층 병렬" 절에 한 줄을 더한다:

```markdown
⚠ **2026-08-30 — `dep_excerpt` 는 배선된 날부터 빈 문자열만 냈다.** `survey-plan.json` 의
`depends_on` 이 노드 **id** 였는데 `terms-reading.json` 은 **이름**으로 키가 잡혀 교집합이
언제나 공집합이었다. 시험이 못 잡은 이유는 픽스처가 id 와 name 을 같게 두었기 때문이다.
`survey_plan.plan` 이 이름을 내도록 고쳤다.
```

- [ ] **Step 4: 인용 검사를 돌린다**

Run: `node --test test/docs-citations.test.mjs`
Expected: 전부 PASS — 문서에 적은 `파일:줄` 이 실재하는지 본다

- [ ] **Step 5: 커밋**

```bash
git add evals/runs/2026-08-30-mode1-qtvisionedit-resolved.json ARCHITECTURE.md codegraph/CLAUDE.md
git commit -m "[chore] : 심볼 해석 배선 뒤 mode 1 완주 실측과 dep_excerpt 결함 기록"
```

---

## 이 계획이 **하지 않는** 것

의도적으로 뺀 것들이다. 하고 싶어지면 먼저 사용자에게 보고한다.

| 안 하는 것 | 왜 |
|---|---|
| 임베딩·코사인 유사도로 참조를 맞추기 | 이 문제는 `::` 로 구조화된 정확 문자열 문제다. 확률적 매칭은 틀린 간선을 만든다 |
| 해석 규칙을 플러그인·레지스트리로 빼기 | **거울 함정.** 함수 둘이면 충분하다. 구현자 1, 소비자 1 |
| `EXTERNAL_PREFIXES` 를 자동으로 늘리기 | 목록이 늘어난다는 건 정적 수집기가 그 심볼을 놓쳤다는 신호일 수 있다. 사람이 본다 |
| 층3 이 왜 비쌌는지(심볼당 51.4만 토큰) 파기 | 별개 조사다. 이 계획은 완주를 막은 결함만 다룬다 |
| 층5(비노드) 를 쪼개 병렬화하기 | 가장 오래 걸린 단일 단계(5분 13초)이지만, 쪼개려면 K5(비노드는 심볼이 다 읽힌 뒤)를 건드려야 한다. 별도 결정 |

---

## Self-Review

**1. 결함 대응 — 실측 50건이 전부 덮이는가**

| 실측 결함 | 담당 Task |
|---|---|
| 내부 id 를 `uses.to` 에 씀 (6건) | Task 1 (원인 제거) + Task 2 (회귀) |
| `dep_excerpt` 가 언제나 빈 문자열 | Task 1 + Task 2 |
| 외부 라이브러리 심볼 미등록 (11건) | Task 4 (사후 합성) + Task 6 (원인 제거) |
| 이름꼴 불일치 (17건) | Task 3 (rollup) |
| 실재하는 파일 참조 (1건) | Task 4 (file 합성) |
| 남는 것 (3건) | Task 5 (근거 없음으로 격하) |

**2. 자리표시자 — 없다.** 모든 단계에 실제 코드와 실제 명령이 있다.

**3. 이름 일관성** — `resolve_target(target, keys) -> str|None` · `synthesize_record(target, repo) -> dict|None` ·
`resolve_uses(db, repo) -> (dict, list)` 셋뿐이고 Task 3·4·5 에서 같은 이름·같은 시그니처로 쓰인다.
`EXTERNAL_PREFIXES` 는 Task 4 에서 정의하고 같은 곳에서만 쓴다.

**4. 알려진 충돌 하나** — Task 5 가 기존 `test_check_flags_unknown_uses_target` 을 지운다.
정책이 "실패" 에서 "근거 없음" 으로 바뀌기 때문이며, Task 5 Step 1 에 명시했다.
