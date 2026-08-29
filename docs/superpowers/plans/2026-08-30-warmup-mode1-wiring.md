# WarmUp 을 Mode 1 파이프라인에 배선하기 — 실행 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `codegraph/warmup.py` 의 증분 판정을 `codegraph/run_mode1.py` 의 단계 흐름에 끼워, 국소 변경일 때 에이전트가 저장소 전량이 아니라 **바뀐 파일과 그 파급만** 읽게 한다.

**Architecture:** 새 단계를 둘 넣는다 — `agent` 앞의 `warmup`(판정만)과 `agent` 뒤의 `warmup-save`(매니페스트 확정). 판정과 확정을 갈라 놓는 것이 이 설계의 급소다. 에이전트가 실패했는데 매니페스트를 이미 "유효" 로 갱신했다면 다음 실행이 읽지 않은 파일을 읽은 것으로 쳐서 낡은 요약이 조용히 살아남는다. 판정 결과는 프롬프트의 **범위 지시문**으로 들어가고, 읽을 것이 하나도 없으면 에이전트를 **아예 부르지 않는다**.

**Tech Stack:** Python 3 (표준 라이브러리 + `pytest`). 새 의존성 없음. 새 파일 없음 — `codegraph/run_mode1.py` 와 그 시험 파일만 고친다.

---

## 왜 이 모양인가 — 착수 전에 읽을 것

### 실측 기준선 (🔵 2026-08-30, QtVisionEdit, 백지 상태)

```
단계   시간         합계 토큰     비용
prep   1.3초        0            $0
agent  26분 53.1초  17,925,770   $15.4991   ← 84턴
terms  0.1초        0            $0
build  13.6초       0            $0
check  0.2초        0            $0
합계   27분 08.1초  17,925,770   $15.4991
```

**시간의 99.1%, 토큰의 100%가 `agent` 한 칸에 있다.** 기계 네 단계를 합쳐 15.2초다. 그러므로 이 배선이 건드릴 곳은 `agent` 의 **입력 범위** 하나뿐이고, 기계 단계를 빠르게 만들 여지는 없다.

### 반드시 고쳐야 할 결함 — `위치만` 이 본문 변경을 삼킨다

🔵 2026-08-30 임시 저장소로 네 갈래를 전부 재현했다:

| 무엇을 고쳤나 | `warmup.py status` 판정 |
|---|---|
| 아무것도 안 고침 | 유효 2 · 재읽기 0 |
| 주석 한 줄 | 위치만 1 · **재읽기 0.0%** |
| **함수 본문** (`return x + 1` → `return x + 100`) | **위치만 1 · 재읽기 0** |
| 함수 추가 | 재읽기 1 (50.0%) |

`decl_hash` 는 `(kind, name)` 만 해싱한다(`codegraph/warmup.py:84`). 그래서 본문을 통째로 다시 써도 선언 이름이 같으면 `위치만` 이다. 전수조사 레코드의 `does`(동작)와 위키 산문의 행동 서술은 본문에 달려 있으므로, **`위치만` 을 에이전트에서 빼면 그 서술이 조용히 낡는다.**

**그래서 이 계획은 `재읽기` 가 아니라 `재읽기 ∪ 위치만` 을 씨앗으로 삼는다.** `warmup.py:244` 의 CLI 도 이미 그렇게 한다 — 도구는 옳고, 배선만 조심하면 된다.

### `hops` 기본값을 1 로 두는 근거 (임의값이 아니다)

🔵 2026-08-30 실측 — QtVisionEdit 의 추적 cpp 파일 77개 각각을 씨앗으로 두고 잰 파급:

| hops | 중앙값 | 평균 | 최대 | 전체 대비 평균 |
|---|---|---|---|---|
| 1 | 1 | 1.5 | 7 | 1.9% |
| 2 | 1 | 2.1 | 10 | 2.7% |
| 3 | 1 | 2.4 | 10 | 3.1% |

1홉에서 2홉으로 늘려도 평균 0.6파일이 더 붙을 뿐이다. **홉을 늘려 사는 안전은 거의 없고, 기본값 1 이면 충분하다.** `--hops` 로 바꿀 수 있게 두되 기본은 1 이다.

⚠ **파급은 이 저장소에서 약한 그물이다.** 간선이 닿는 파일이 77개 중 **16개**뿐이다(codegraph 가 클래스·자유함수 층만 담는다). 나머지 61개는 파급이 자기 자신뿐이다. 그러므로 안전은 파급이 아니라 **`위치만` 을 씨앗에 넣는 것**에서 나온다.

### 범위 밖 — 손대지 않는다

| 무엇 | 왜 이 계획에 없나 |
|---|---|
| `codegraph/warmup.py` 수정 | 도구는 옳다. 결함은 배선 쪽에 있다 |
| `codegraph/xmldoc.py` 를 저장소 무관하게 만들기 | 별개 하위체계다(`xmldoc.py:26-29` 가 report-builder 자신에 고정). `위치만` 을 에이전트에 보내므로 **정확성에는 필요 없고**, 나중의 순수 최적화다 |
| `bin/report-wiki` 에 명령 추가 | 실행기는 Python 이다. Node 진입점을 늘리면 같은 흐름이 두 곳에 생긴다 |
| `codegraph/normalize.py` 출력 키 | `terms_db.py` 가 간접 의존한다. 건드리면 조용히 깨진다 |
| 단계 등록기·플러그인 구조 | 거울 함정. 단계는 일곱 개 고정이고 `if/elif` 로 충분하다 |

### 파일 구조

새 파일을 만들지 않는다. `run_mode1.py` 는 지금 474줄이고 이 계획으로 약 570줄이 된다. 나누지 않는 이유는 **구현자 1 · 소비자 1** 이기 때문이다 — 한 CLI 실행기를 두 모듈로 쪼개는 것이 이 저장소가 경계하는 거울 함정이다.

| 파일 | 책임 | 이 계획에서 |
|---|---|---|
| `codegraph/run_mode1.py` | 단계 흐름 · 측정 · 보고 | **수정** (순수 함수 4개 추가 + `main` 배선) |
| `codegraph/test_run_mode1.py` | 위 파일의 회귀 시험 | **수정** (시험 14개 추가) |
| `codegraph/warmup.py` | 파일 지문과 무효화 판정 | 읽기만 (import) |
| `codegraph/declmap.py` | 추적 파일 목록과 선언 훑기 | 읽기만 (import) |

### 이 저장소의 규율 — 실행자가 어길 만한 것

- **커밋하지 마라.** 각 Task 의 마지막 단계는 `git add` 로 좁혀 담아 두고 **커밋 메시지를 제시한 뒤 사용자 승인을 기다린다.** `git add -A` 금지.
- **주석과 문서는 한국어.** 약어를 피하고 메커니즘(원리)을 먼저 쓴다.
- **경로를 코드에 박지 마라.** 파이썬은 `sys.executable`, 바깥 명령은 PATH 다.
- **확신도 표기** — 🔵 는 이번 세션에서 읽은 `file:line` 또는 실제로 돌린 명령의 출력만.
- **"검증됨" "입증" "증명" 이라고 쓰지 마라.**

### 검증 명령 (Task 마다 돈다)

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q     # 이 계획이 만지는 시험
.venv/bin/python -m pytest codegraph/ -q                       # 회귀 전량
```

착수 시점 기준선: 🔵 `codegraph/test_run_mode1.py` **20 passed**, `codegraph/` 전량 **125 passed, 19 skipped**.
(건너뜀 19개는 `$GRAPHICS_REPO`·`$CPP_REPO`·`$CSHARP_REPO` 가 없어서다. 실패가 아니다.)

---

## Task 1: 언어 이름 다리 — `lang_of`

코드 지도는 언어를 `"cpp"` / `"csharp"` 로 적고(`codegraph/normalize.py:460,725`), `declmap` 은 `"cpp"` / `"cs"` 로 안다(`codegraph/declmap.py:33`). 이 한 칸이 어긋나면 `warmup` 단계가 통째로 죽는다. 수집기를 다시 판별하지 않고 **코드 지도가 이미 적어 둔 값**을 읽는다 — 판별 규칙이 두 곳에 생기는 것을 막는다.

**Files:**
- Modify: `codegraph/run_mode1.py` (68번 줄 `AGENT_STAGES` 아래에 상수와 함수 추가)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`codegraph/test_run_mode1.py` 의 `# ── 4. 에이전트 호출` 절 **바로 앞**에 새 절을 넣는다:

```python
# ── 3.5 WarmUp — 언어 이름 다리
def test_lang_of_bridges_the_two_naming_schemes(tmp_path):
    """코드 지도는 'csharp' 이라 적고 declmap 은 'cs' 로 안다. 이 한 칸이 어긋나면 단계가 죽는다."""
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "csharp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cs"


def test_lang_of_passes_through_a_name_declmap_already_knows(tmp_path):
    p = tmp_path / "codegraph.json"
    p.write_text('{"language": "cpp"}', encoding="utf-8")
    assert R.lang_of(str(p)) == "cpp"


def test_lang_of_is_none_when_it_cannot_tell():
    """모르는 언어와 없는 파일은 둘 다 None 이다 — 부르는 쪽이 단계를 건너뛴다. 실패가 아니다."""
    assert R.lang_of("/없는/파일.json") is None
    assert R.lang_of(None) is None
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k lang_of
```

기대: `AttributeError: module 'run_mode1' has no attribute 'lang_of'` 로 3개 실패.

- [ ] **Step 3: 최소 구현을 쓴다**

`codegraph/run_mode1.py` 의 `AGENT_STAGES = {"agent"}` 줄 **바로 아래**에 넣는다:

```python

# 코드 지도가 적는 언어 이름과 declmap 이 아는 이름이 한 칸 다르다. 두 줄짜리 표다 —
# 수집기 판별을 여기서 다시 하지 않는다. 그러면 판별 규칙이 두 곳에 생겨 조용히 어긋난다.
LANG_ALIAS = {"csharp": "cs"}


def lang_of(codegraph_path):
    """코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다.

    모르면 `None` 이다 — 예외가 아니다. 부르는 쪽이 warmup 단계만 건너뛰고
    나머지는 그대로 돈다. 새 언어가 들어와도 파이프라인이 죽지 않아야 한다.
    """
    if not codegraph_path:
        return None
    try:
        with open(codegraph_path, encoding="utf-8") as f:
            name = json.load(f).get("language")
    except (OSError, ValueError):
        return None
    name = LANG_ALIAS.get(name, name)
    return name if name in declmap.LANGS else None
```

그리고 파일 머리의 `import` 무리 **바로 아래**(`ROOT = ...` 줄 위)에 넣는다:

```python
# warmup 과 declmap 은 같은 폴더에 있다. 이 파일이 CLI 로 돌 때는 sys.path[0] 이 그 폴더이고,
# 시험이 import 할 때는 시험 파일이 넣어 준다. 어느 쪽이든 확실하도록 여기서도 넣는다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402
import warmup  # noqa: E402
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k lang_of
```

기대: `3 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `128 passed, 19 skipped` (기준선 125 + 3).

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

제시할 커밋 메시지 (**직접 커밋하지 말 것**):

```
[feat] : 코드 지도의 언어 이름을 declmap 이름으로 옮기는 다리
```

---

## Task 2: `위치만` 을 씨앗에 넣는다 — `changed_seed`

**이 계획에서 가장 중요한 Task 다.** 위 "반드시 고쳐야 할 결함" 절에서 잰 것 — 함수 본문만 고친 변경이 `위치만` 으로 판정된다. 이것을 에이전트에서 빼면 레코드의 `does` 가 조용히 낡는다.

**Files:**
- Modify: `codegraph/run_mode1.py` (Task 1 에서 넣은 `lang_of` 아래)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

Task 1 의 시험들 **아래**에 이어 붙인다:

```python
def test_seed_includes_position_only_files():
    """급소 — 함수 본문만 바꾼 변경은 '위치만' 으로 온다.

    decl_hash 는 (kind, name) 만 해싱하므로(warmup.py:84) 본문을 통째로 다시 써도
    선언 이름이 같으면 '위치만' 이다. 이것을 빼면 레코드의 does 가 조용히 낡는다.
    """
    판정 = {"유효": ["a.cpp"], "재읽기": ["b.cpp"], "위치만": ["c.cpp"], "삭제됨": ["d.cpp"]}
    assert R.changed_seed(판정) == ["b.cpp", "c.cpp"]


def test_seed_excludes_valid_and_deleted():
    """유효는 읽을 것이 없고, 삭제됨은 읽을 파일 자체가 없다."""
    seed = R.changed_seed({"유효": ["a"], "재읽기": [], "위치만": [], "삭제됨": ["d"]})
    assert seed == []


def test_seed_is_sorted_and_deduplicated():
    """같은 파일이 두 갈래에 들어와도 한 번만 센다 — 프롬프트에 두 번 실리면 안 된다."""
    assert R.changed_seed({"재읽기": ["z", "a"], "위치만": ["a"]}) == ["a", "z"]


def test_seed_tolerates_missing_buckets():
    assert R.changed_seed({}) == []
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k seed
```

기대: `AttributeError: module 'run_mode1' has no attribute 'changed_seed'` 로 4개 실패.

- [ ] **Step 3: 최소 구현을 쓴다**

`lang_of` 아래에 넣는다:

```python
def changed_seed(판정):
    """다시 읽어야 할 파일의 씨앗. **`위치만` 을 반드시 포함한다.**

    `warmup.py` 의 문서는 `위치만` 을 "주석만 고치거나 줄만 밀린 변경" 이라 부르지만,
    구현은 그것과 **본문 재작성**을 구별하지 못한다 — `decl_hash` 가 선언의 이름만
    해싱하기 때문이다(`codegraph/warmup.py:84`). 🔵 2026-08-30 실측으로
    `return x + 1` → `return x + 100` 이 `위치만` 으로 판정되는 것을 확인했다.

    레코드의 `does`(동작)와 위키 산문의 행동 서술은 본문에 달려 있으므로 이 갈래를
    빼면 그 서술이 조용히 낡는다. `warmup.py:244` 의 CLI 도 같은 합집합을 쓴다.

    `유효` 는 읽을 것이 없고, `삭제됨` 은 읽을 파일 자체가 없다.
    """
    return sorted(set(판정.get("재읽기") or []) | set(판정.get("위치만") or []))
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k seed
```

기대: `4 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `132 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

제시할 커밋 메시지:

```
[fix] : 본문만 바뀐 파일이 에이전트를 건너뛰던 것 - 위치만을 씨앗에 넣는다
```

---

## Task 3: 읽을 것이 없으면 에이전트를 부르지 않는다 — `should_call_agent`

국소 변경의 실제 이득이 나오는 자리다. 아무것도 안 바뀌었으면 27분·$15.50 짜리 단계를 통째로 건너뛴다.

**Files:**
- Modify: `codegraph/run_mode1.py` (`changed_seed` 아래)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
def test_agent_is_skipped_when_nothing_changed_and_records_exist():
    """국소 변경의 이득이 여기서 나온다 — 27분짜리 단계를 통째로 건너뛴다."""
    assert R.should_call_agent(targets=[], has_reading=True) is False


def test_agent_still_runs_when_there_are_no_records_yet():
    """조사 결과가 아예 없으면 warmup 이 뭐라 하든 부른다 — 백지에서 시작하는 실행이다."""
    assert R.should_call_agent(targets=[], has_reading=False) is True


def test_agent_runs_when_something_changed():
    assert R.should_call_agent(targets=["a.cpp"], has_reading=True) is True


def test_agent_runs_when_warmup_could_not_judge():
    """targets 가 None 이면 warmup 이 못 돌았다는 뜻이다. 그때는 옛 동작(전량)으로 돌아간다."""
    assert R.should_call_agent(targets=None, has_reading=True) is True
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `AttributeError: module 'run_mode1' has no attribute 'should_call_agent'` 로 4개 실패,
나머지 27개 통과 (`4 failed, 27 passed`).

- [ ] **Step 3: 최소 구현을 쓴다**

```python
def should_call_agent(targets, has_reading):
    """에이전트를 부를 것인가.

    `targets` 가 `None` 이면 warmup 이 판정을 못 했다는 뜻이다(언어를 모르거나 코드
    지도가 없거나 단계를 건너뛴 경우). 그때는 **옛 동작인 전량 조사**로 돌아간다 —
    모르는 상태에서 건너뛰면 조용히 아무 일도 안 하게 된다.

    빈 목록(`[]`)은 "정말로 바뀐 것이 없다" 는 판정이다. 그때만, 그리고 지난 조사
    결과가 있을 때만 건너뛴다.
    """
    if targets is None:
        return True
    if not has_reading:
        return True
    return bool(targets)
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `31 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `136 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

```
[feat] : 바뀐 것이 없으면 에이전트 단계를 통째로 건너뛴다
```

---

## Task 4: 프롬프트의 범위 지시문 — `warmup_section`

판정 결과가 실제로 토큰을 줄이려면 **프롬프트 안으로** 들어가야 한다. 목록을 주는 것만으로는 부족하다 — "이 목록 밖은 읽지 마라" 를 함께 말해야 한다.

**Files:**
- Modify: `codegraph/run_mode1.py` (`agent_prompt` 위, 184번 줄 근처)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
def test_warmup_section_lists_every_target_and_the_ratio():
    """에이전트가 범위를 알려면 목록과 비율이 둘 다 있어야 한다."""
    s = R.warmup_section(["core/a.cpp", "server/b.h"], total=77)
    assert "core/a.cpp" in s and "server/b.h" in s
    assert "2" in s and "77" in s
    assert "읽지 마라" in s          # 목록 밖을 읽지 말라고 분명히 말한다


def test_warmup_section_is_empty_when_there_is_nothing_to_scope():
    """범위가 없으면 빈 글이다 — 부르는 쪽이 이 절을 통째로 뺀다."""
    assert R.warmup_section([], total=77) == ""
    assert R.warmup_section(None, total=77) == ""


def test_prompt_carries_the_scope_when_warmup_gave_one():
    p = R.agent_prompt(repo="/어느/저장소", root="/도구/뿌리",
                       targets=["core/a.cpp"], total=77)
    assert "core/a.cpp" in p
    assert "증분" in p


def test_prompt_without_a_scope_is_the_full_survey():
    """warmup 이 못 돌았거나 백지 실행이면 옛 프롬프트 그대로여야 한다."""
    p = R.agent_prompt(repo="/어느/저장소", root="/도구/뿌리")
    assert "증분" not in p
    assert "codebase-terms-survey" in p and "deep-wiki" in p
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `4 failed, 31 passed`. `warmup_section` 2개는 `AttributeError`,
프롬프트 2개는 `TypeError: agent_prompt() got an unexpected keyword argument 'targets'`.

- [ ] **Step 3: `warmup_section` 을 쓴다**

`def agent_prompt(...)` **바로 위**에 넣는다. 저장소 경로를 인자로 받는다 — 이 글은
`agent_prompt` 안에서 다시 `.format()` 을 타지 않으므로 중괄호 자리표시자를 쓸 수 없다.

```python
def warmup_section(targets, total, repo=""):
    """프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다.

    **목록만 주면 부족하다.** 에이전트는 맥락이 모자라다고 느끼면 옆 파일을 더 읽는다.
    그것이 이 배선이 줄이려는 바로 그 비용이므로, 목록 밖을 읽지 말라고 분명히 쓴다.
    대신 이미 있는 레코드를 근거로 쓰라고 알려 준다 — 금지만 하면 막힌다.

    이 글은 `agent_prompt` 가 이미 `.format()` 을 돌린 **뒤에** 이어 붙는다. 그래서
    중괄호 자리표시자를 남기면 안 되고, 저장소 경로를 `repo` 로 받아 여기서 박아 넣는다.
    """
    if not targets:
        return ""
    목록 = "\n".join("  " + t for t in targets)
    return ("\n## 범위 — 증분 조사다. 저장소 전량을 읽지 마라\n"
            "\n"
            "지난 조사 결과가 %s/docs/codegraph/terms-reading.json 에 이미 있다. 그중\n"
            "**아래 %d개 파일에 걸린 레코드만** 다시 만든다. 추적 파일 %d개 중 %d개다.\n"
            "\n%s\n"
            "\n"
            "- **이 목록에 없는 파일은 읽지 마라.** 나머지 레코드는 그대로 살아 있고, 손대면 안 된다.\n"
            "- 목록 밖의 이름이 필요하면 소스가 아니라 **기존 terms-reading.json 과 codegraph.json**\n"
            "  을 근거로 쓴다.\n"
            "- 산문도 마찬가지다. 이 파일들을 다루는 페이지만 고치고 나머지 docs/wiki/*.md 는 둔다.\n"
            "- 목록의 파일이 사라졌거나 읽을 수 없으면 **지어내지 말고** 보고에 적는다.\n"
            % (repo, len(targets), total, len(targets), 목록))
```

- [ ] **Step 3-2: `agent_prompt` 가 그 절을 받게 고친다**

`codegraph/run_mode1.py:184` 의 서명을 바꾼다.

바꾸기 전:

```python
def agent_prompt(repo, root):
```

바꾼 뒤:

```python
def agent_prompt(repo, root, targets=None, total=0):
```

그리고 그 함수의 **마지막 줄**을 바꾼다.

바꾸기 전:

```python
""".format(repo=repo, root=root)
```

바꾼 뒤:

```python
""".format(repo=repo, root=root) + warmup_section(targets, total, repo)
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `35 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `140 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

```
[feat] : 증분 범위를 에이전트 프롬프트에 싣는다
```

---

## Task 5: 단계 둘을 흐름에 넣는다 — `plan_stages`

`warmup`(판정)과 `warmup-save`(확정)를 `agent` 앞뒤에 둔다. **둘을 한 단계로 합치지 않는 이유**는 그 사이에 실패할 수 있는 구간(`agent`)이 있기 때문이다.

**Files:**
- Modify: `codegraph/run_mode1.py:65` (`STAGES`), `codegraph/run_mode1.py:83` (`plan_stages`)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

기존 시험 `test_plan_runs_everything_on_an_empty_repo` 와
`test_plan_skips_the_agent_when_its_output_already_exists` 를 아래로 **교체**한다:

```python
def test_plan_runs_everything_on_an_empty_repo():
    """아무것도 없으면 일곱 단계를 순서대로 돈다. LLM 단계(agent)는 그중 하나뿐이다."""
    assert R.plan_stages(has_codegraph=False, has_reading=False, has_prose=False) == [
        "prep", "warmup", "agent", "warmup-save", "terms", "build", "check"]


def test_plan_skips_the_agent_when_its_output_already_exists():
    """조사 결과와 산문이 이미 있으면 에이전트를 부르지 않는다.

    **그래도 warmup 두 칸은 남는다.** 판정을 해 봐야 정말 건너뛰어도 되는지 알고,
    매니페스트는 갱신해 둬야 다음 실행이 옳게 판정한다.
    """
    p = R.plan_stages(has_codegraph=True, has_reading=True, has_prose=True)
    assert "agent" not in p
    assert p == ["prep", "warmup", "warmup-save", "terms", "build", "check"]
```

그리고 새 시험 셋을 그 아래에 더한다:

```python
def test_the_two_warmup_gates_straddle_the_agent():
    """판정은 앞, 확정은 뒤. 이 순서가 뒤집히면 실패한 에이전트가 '유효' 로 기록된다."""
    p = R.plan_stages(False, False, False)
    assert p.index("warmup") < p.index("agent") < p.index("warmup-save")


def test_the_save_gate_comes_before_terms():
    """매니페스트 확정이 terms 뒤로 밀리면, terms 가 실패했을 때 판정이 사라진다."""
    p = R.plan_stages(False, False, False)
    assert p.index("warmup-save") < p.index("terms")


def test_skipping_warmup_restores_the_old_five_stage_flow():
    """warmup 을 빼면 2026-08-30 에 실측한 그 흐름 그대로여야 한다 — 대조군을 만들 수 있게."""
    p = R.plan_stages(False, False, False, skip=["warmup", "warmup-save"])
    assert p == ["prep", "agent", "terms", "build", "check"]
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `5 failed, 33 passed`.
- `test_plan_runs_everything_on_an_empty_repo` — `AssertionError: assert ['prep','agent',...] == ['prep','warmup',...]`
- `test_plan_skips_the_agent_when_its_output_already_exists` — 같은 꼴
- `test_the_two_warmup_gates_straddle_the_agent` — `ValueError: 'warmup' is not in list`
- `test_the_save_gate_comes_before_terms` — 같은 꼴
- `test_skipping_warmup_restores_the_old_five_stage_flow` — `ValueError: 모르는 단계: warmup`

- [ ] **Step 3: 최소 구현을 쓴다**

`codegraph/run_mode1.py:65` 를 바꾼다.

바꾸기 전:

```python
# 단계는 다섯 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["prep", "agent", "terms", "build", "check"]
```

바꾼 뒤:

```python
# 단계는 일곱 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
#
# warmup 이 **둘**인 것이 이 흐름의 급소다. 앞(warmup)은 판정만 하고, 뒤(warmup-save)가
# 매니페스트를 갱신한다. 한 칸으로 합치면 에이전트가 실패했을 때도 그 파일이 "유효" 로
# 기록되어, 다음 실행이 읽지 않은 파일을 읽은 것으로 친다.
STAGES = ["prep", "warmup", "agent", "warmup-save", "terms", "build", "check"]
```

그리고 `plan_stages` 의 반복문을 바꾼다.

바꾸기 전:

```python
    out = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        if s == "agent" and has_reading and has_prose:
            continue
        out.append(s)
    return out
```

바꾼 뒤:

```python
    out = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        # warmup 두 칸은 빼지 않는다. 에이전트를 건너뛸 때도 판정은 해 봐야 하고
        # (정말 건너뛰어도 되는지 아는 유일한 방법이다), 매니페스트는 갱신해 둬야
        # 다음 실행이 옳게 판정한다.
        if s == "agent" and has_reading and has_prose:
            continue
        out.append(s)
    return out
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: `38 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `143 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

```
[feat] : warmup 판정과 확정 두 칸을 에이전트 앞뒤에 넣는다
```

---

## Task 6: 표에 "건너뜀" 을 그린다 — `format_report`

에이전트를 건너뛴 실행이 표에서 "성공" 으로 보이면, 27분이 15초로 줄어든 이유를 읽는 사람이 알 수 없다. **재는 것이 이 도구의 목적이므로 건너뜀은 보여야 한다.**

**Files:**
- Modify: `codegraph/run_mode1.py:275` 근처 (`format_report`)
- Test: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`# ── 6. 보고` 절 끝에 더한다:

```python
def test_report_marks_a_skipped_stage():
    """건너뜀을 '성공' 으로 그리면 27분이 15초가 된 이유를 읽는 사람이 알 수 없다."""
    text = R.format_report([{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
                             "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)}])
    assert "건너뜀" in text
    assert "바뀐 파일 0개" in text
    assert "실패" not in text


def test_a_skipped_stage_does_not_break_the_total():
    rows = [{"stage": "agent", "seconds": 0.0, "ok": True, "skipped": True,
             "why": "바뀐 파일 0개", "usage": R.normalize_usage(None)},
            {"stage": "build", "seconds": 2.0, "ok": True,
             "usage": R.normalize_usage(None)}]
    assert "합계" in R.format_report(rows)
```

- [ ] **Step 2: 실패를 눈으로 본다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k skipped
```

기대: `AssertionError: assert '건너뜀' in '단계 상태 ...'` — 지금은 "성공" 으로 그린다.

- [ ] **Step 3: 최소 구현을 쓴다**

`format_report` 안의 상태 칸을 바꾼다.

바꾸기 전:

```python
            "성공" if r.get("ok") else "실패",
```

바꾼 뒤:

```python
            "건너뜀" if r.get("skipped") else ("성공" if r.get("ok") else "실패"),
```

그리고 그 함수 끝의 사유 출력을 바꾼다.

바꾸기 전:

```python
    for r in rows:
        if not r.get("ok"):
            out.append("실패 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
    return "\n".join(out)
```

바꾼 뒤:

```python
    for r in rows:
        if r.get("skipped"):
            out.append("건너뜀 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
        elif not r.get("ok"):
            out.append("실패 — %s: %s" % (r["stage"], r.get("why") or "사유 없음"))
    return "\n".join(out)
```

- [ ] **Step 4: 통과를 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k skipped
```

기대: `2 passed`.

- [ ] **Step 5: 회귀 전량**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `145 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
```

```
[feat] : 측정 표에 건너뛴 단계를 따로 그린다
```

---

## Task 7: 실행기에 배선한다 — `main`

여기까지의 순수 함수를 실제 흐름에 잇는다. **부수효과는 이 Task 에만 있다.**

**Files:**
- Modify: `codegraph/run_mode1.py:386` 이후 (`main`)

- [ ] **Step 1: `--hops` 를 인자로 더한다**

`ap.add_argument("--timeout", ...)` 줄 **바로 아래**에 넣는다:

```python
    ap.add_argument("--hops", type=int, default=1,
                    help="바뀐 파일에서 파급을 몇 홉 퍼뜨릴지 (기본: 1). "
                         "🔵 2026-08-30 QtVisionEdit 실측 — 1홉 평균 1.5파일, 2홉 2.1파일로 "
                         "차이가 거의 없다")
```

- [ ] **Step 2: 판정 상태를 담을 변수를 만든다**

`rows, t_all = [], time.monotonic()` 줄을 아래로 **교체**한다:

```python
    # warmup 이 앞칸에서 담아 두고 뒤칸이 꺼내 쓴다. 같은 프로세스 안이라 파일로 넘길 이유가 없다.
    #   targets  에이전트가 읽을 파일 목록. None 이면 판정을 못 했다는 뜻이다(= 전량 조사)
    #   entries  갱신될 매니페스트. 에이전트가 성공한 뒤에만 쓴다
    targets, entries, warmup_cache, tracked_n = None, None, None, 0
    rows, t_all = [], time.monotonic()
```

- [ ] **Step 3: 단계 갈림길에 두 칸을 더한다**

`main` 의 `for stage in stages:` 안, `if stage == "agent":` **바로 앞**에 두 갈래를 넣는다.

바꾸기 전:

```python
        if stage == "agent":
            rc, result = run_agent(a.model, repo, ROOT, timeout=a.timeout)
            ok, why = agent_verdict(rc, result)
            usage = normalize_usage(result)
            if result and result.get("result"):
                print(result["result"])
```

바꾼 뒤:

```python
        if stage == "warmup":
            targets, entries, warmup_cache, tracked_n, ok, why = run_warmup(repo, codegraph, a.hops)
            usage = normalize_usage(None)
        elif stage == "warmup-save":
            ok, why = save_warmup(warmup_cache, entries, rows)
            usage = normalize_usage(None)
        elif stage == "agent":
            if not should_call_agent(targets, os.path.exists(reading)):
                ok, why, usage = True, "바뀐 파일 0개 — 지난 조사 결과를 그대로 쓴다", normalize_usage(None)
                rows.append({"stage": stage, "seconds": time.monotonic() - t0,
                             "usage": usage, "ok": ok, "why": why, "skipped": True})
                print("%s — 건너뜀 (%s)" % (stage, why), flush=True)
                continue
            rc, result = run_agent(a.model, repo, ROOT, targets=targets,
                                   total=tracked_n, timeout=a.timeout)
            ok, why = agent_verdict(rc, result)
            usage = normalize_usage(result)
            if result and result.get("result"):
                print(result["result"])
```

- [ ] **Step 4: 두 부수효과 함수를 쓴다**

`def main(argv=None):` **바로 위**에 넣는다:

```python
def run_warmup(repo, codegraph, hops):
    """관문 ① — 무엇을 다시 읽어야 하는지 판정한다. **매니페스트를 쓰지는 않는다.**

    쓰기를 여기서 하면 에이전트가 실패했을 때도 "유효" 로 기록되어, 다음 실행이
    읽지 않은 파일을 읽은 것으로 친다. 그래서 갱신은 `save_warmup` 이 따로 한다.

    판정할 수 없으면 `targets` 를 `None` 으로 낸다 — 실패가 아니다. 그러면
    `should_call_agent` 가 옛 동작(전량 조사)으로 돌아간다.

    반환 (targets, entries, cache_path, 추적파일수, 성공인가, 사유)
    """
    lang = lang_of(codegraph if os.path.exists(codegraph) else None)
    if lang is None:
        print("알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다.", file=sys.stderr)
        return None, None, None, 0, True, ""

    cache = os.path.join(repo, warmup.DEFAULT_CACHE)
    files = declmap.tracked_files(repo, lang, [])
    if not files:
        print("알림 — git 이 아는 %s 소스가 0개다. 전량 조사로 돈다." % lang, file=sys.stderr)
        return None, None, None, 0, True, ""

    decls, _ = declmap.scan(repo, lang, [], 0)
    판정, entries = warmup.status(cache, repo, files, decls)
    seed = changed_seed(판정)

    # 파급까지 넓힌다. 코드 지도가 없으면 씨앗 그대로다 — 파급은 안전망이지 필수가 아니다.
    if seed and os.path.exists(codegraph):
        targets = warmup.blast_radius(codegraph, seed, hops)
    else:
        targets = seed

    print("%s 파일 %d개 — 유효 %d · 재읽기 %d · 위치만 %d · 삭제됨 %d"
          % (lang, len(files), len(판정["유효"]), len(판정["재읽기"]),
             len(판정["위치만"]), len(판정["삭제됨"])))
    print("에이전트가 읽을 것 %d개 (%.1f%%) — 씨앗 %d개에서 %d홉 퍼뜨린 결과"
          % (len(targets), len(targets) / len(files) * 100, len(seed), hops))
    for p in targets[:15]:
        print("  " + p)
    if len(targets) > 15:
        print("  … 그 밖 %d개" % (len(targets) - 15))
    if 판정["삭제됨"]:
        print("사람이 볼 것 — 삭제된 파일 %d개의 레코드를 지울지 정해야 한다:"
              % len(판정["삭제됨"]), file=sys.stderr)
        for p in 판정["삭제됨"][:10]:
            print("  " + p, file=sys.stderr)
    return targets, entries, cache, len(files), True, ""


def save_warmup(cache_path, entries, rows):
    """관문 ② — 에이전트가 실제로 해낸 뒤에만 매니페스트를 갱신한다.

    앞칸이 판정을 못 했거나(`entries is None`) 에이전트가 실패했으면 **쓰지 않는다.**
    쓰지 않는 것이 안전한 쪽이다 — 다음 실행이 전량을 다시 읽을 뿐 틀리지는 않는다.
    """
    if entries is None or not cache_path:
        return True, ""
    실패한_에이전트 = [r for r in rows if r["stage"] == "agent" and not r.get("ok")]
    if 실패한_에이전트:
        print("매니페스트를 갱신하지 않는다 — 에이전트가 실패했다. "
              "지금 갱신하면 읽지 않은 파일이 '유효' 로 남는다.", file=sys.stderr)
        return True, ""
    warmup.save(cache_path, entries)
    print("매니페스트 갱신 — %s (%d개 파일)" % (cache_path, len(entries)))
    return True, ""
```

- [ ] **Step 5: `run_agent` 가 범위를 넘기게 고친다**

`codegraph/run_mode1.py` 의 `run_agent` 를 바꾼다.

바꾸기 전:

```python
def run_agent(model, repo, root, timeout=None):
    """`claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`."""
    argv = claude_argv(model=model, repo=repo, extra_dirs=[root])
    with _Heartbeat("agent"):
        p = subprocess.run(argv, input=agent_prompt(repo, root), cwd=repo,
                           capture_output=True, text=True, timeout=timeout)
```

바꾼 뒤:

```python
def run_agent(model, repo, root, targets=None, total=0, timeout=None):
    """`claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`.

    `targets` 가 있으면 프롬프트에 범위 지시문이 붙어 증분 조사가 된다.
    `None` 이면 옛 동작 그대로 전량 조사다.
    """
    argv = claude_argv(model=model, repo=repo, extra_dirs=[root])
    prompt = agent_prompt(repo, root, targets=targets, total=total)
    with _Heartbeat("agent"):
        p = subprocess.run(argv, input=prompt, cwd=repo,
                           capture_output=True, text=True, timeout=timeout)
```

- [ ] **Step 6: 회귀 전량이 그대로인지 본다**

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python -m pytest codegraph/ -q
```

기대: `145 passed, 19 skipped` (Task 6 과 같다 — 이 Task 는 시험을 더하지 않는다).

- [ ] **Step 7: 마른 실행으로 흐름을 눈으로 본다**

```bash
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" --dry-run
```

기대 출력 (산문과 조사 결과가 이미 있으므로 `agent` 가 빠진다):

```
모형 opus · 단계 prep -> warmup -> warmup-save -> terms -> build -> check
이미 있는 것 — 코드지도 True · 읽기레코드 True · 산문 True
```

- [ ] **Step 8: warmup 단계만 실제로 돌려 판정을 본다 (토큰 0)**

```bash
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" \
  --only warmup
```

기대: 매니페스트가 아직 없으므로 냉시동이다.

```
cpp 파일 77개 — 유효 0 · 재읽기 77 · 위치만 0 · 삭제됨 0
에이전트가 읽을 것 77개 (100.0%) — 씨앗 77개에서 1홉 퍼뜨린 결과
```

⚠ `--only warmup` 은 `warmup-save` 를 빼므로 매니페스트가 **안 써진다.** 의도한 동작이다.

- [ ] **Step 9: 매니페스트를 세우고 아무것도 안 고친 채 다시 본다**

```bash
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" \
  --only warmup,warmup-save
```

첫 줄은 Step 8 과 같고 끝에 `매니페스트 갱신 — .../out/codegraph-raw/warmup.json (77개 파일)` 이 붙는다.
바로 한 번 더 같은 명령을 돌린다. 기대:

```
cpp 파일 77개 — 유효 77 · 재읽기 0 · 위치만 0 · 삭제됨 0
에이전트가 읽을 것 0개 (0.0%) — 씨앗 0개에서 1홉 퍼뜨린 결과
```

- [ ] **Step 10: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py
```

```
[feat] : mode 1 실행기에 warmup 두 관문을 배선한다
```

---

## Task 8: 새 함수들의 전수조사 레코드를 넣는다

이 저장소의 규약이다 — 새 심볼은 `docs/codegraph/terms-reading.json` 에 레코드를 갖고, 그 레코드가 소스의 주석 블록으로 주입된다. 빠뜨리면 `xmldoc.py check` 가 잡는다.

**Files:**
- Modify: `docs/codegraph/terms-reading.json`
- Modify: `docs/codegraph/comments.xml` (도구가 생성한다 — 손으로 고치지 말 것)
- Modify: `codegraph/run_mode1.py` (도구가 주석 블록을 주입한다)

- [ ] **Step 1: 레코드를 더한다**

줄 번호를 손으로 옮겨 적지 않는다 — 앞 Task 들이 줄을 밀어 놓았고, 손으로 옮기면 반드시
어긋난다. 아래 스크립트가 소스에서 `def` 줄을 직접 찾아 `where` 에 넣는다.
`LANG_ALIAS` 는 모듈 상수라 레코드를 만들지 않는다 — 용어 사전의 항목이 아니다.

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python - <<'PY'
import collections, json, re

F = "codegraph/run_mode1.py"
소스 = open(F, encoding="utf-8").read().split("\n")

def 줄(이름):
    """`def 이름(` 이 나오는 첫 줄 번호(1부터). 못 찾으면 멈춘다 — 조용히 틀리면 안 된다."""
    패턴 = re.compile(r"^def %s\(" % re.escape(이름))
    for i, ln in enumerate(소스, 1):
        if 패턴.match(ln):
            return i
    raise SystemExit("못 찾음: def %s( — 앞 Task 를 먼저 끝내라" % 이름)

설명 = {
    "lang_of": (
        "코드 지도가 적어 둔 언어를 선언 훑기가 아는 이름으로 바꾼다.",
        "수집기를 다시 판별하지 않는다. 판별 규칙이 두 곳에 생기면 조용히 어긋난다. "
        "모르는 언어는 없음으로 답해 그 단계만 빠지게 한다."),
    "changed_seed": (
        "다시 읽어야 할 파일의 씨앗을 고른다.",
        "내용은 달라졌으나 선언은 같은 갈래를 반드시 포함한다. 선언 지문이 이름만 보기 "
        "때문에 본문을 통째로 다시 쓴 변경이 그 갈래로 오고, 빼면 동작 서술이 조용히 낡는다."),
    "should_call_agent": (
        "큰 언어 모형을 부를지 말지 정한다.",
        "읽을 것이 없고 지난 조사 결과가 있을 때만 건너뛴다. 판정을 못 한 경우는 "
        "건너뛰지 않는다 - 모르는 채로 건너뛰면 아무 일도 안 하게 된다."),
    "warmup_section": (
        "다시 읽을 범위를 알리는 지시문을 만든다.",
        "목록만 주지 않고 목록 밖을 읽지 말라고 함께 적는다. 맥락이 모자라면 옆 파일을 "
        "더 읽는데 그것이 줄이려는 비용이다."),
    "run_warmup": (
        "무엇을 다시 읽어야 하는지 판정하는 앞 관문.",
        "판정만 하고 기록을 갱신하지는 않는다. 판정할 수 없으면 없음으로 답해 "
        "전량 조사로 돌아가게 한다."),
    "save_warmup": (
        "판정 기록을 확정하는 뒤 관문.",
        "큰 언어 모형이 실제로 해낸 뒤에만 쓴다. 실패했는데 갱신하면 읽지 않은 파일이 "
        "유효로 남아 낡은 요약이 살아남는다."),
}

p = "docs/codegraph/terms-reading.json"
d = json.load(open(p, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
for 이름, (means, does) in 설명.items():
    d["run_mode1." + 이름] = collections.OrderedDict([
        ("kind", "function"), ("module", "codegraph"),
        ("where", "%s:%d" % (F, 줄(이름))),
        ("means", means), ("does", does),
        ("uses", []), ("confidence", "HIGH"), ("source", "reading"),
    ])
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("레코드 %d개 — run_mode1 새 함수 6개 반영" % len(d))
PY
```

기대 출력: `레코드 285개 — run_mode1 새 함수 6개 반영` (착수 시점 279 + 6).

- [ ] **Step 2: 넣은 좌표가 실제 `def` 줄인지 눈으로 확인한다**

```bash
.venv/bin/python - <<'PY'
import json
d = json.load(open("docs/codegraph/terms-reading.json", encoding="utf-8"))
소스 = open("codegraph/run_mode1.py", encoding="utf-8").read().split("\n")
for k in sorted(d):
    if not k.startswith("run_mode1.") or d[k]["kind"] != "function":
        continue
    파일, 줄 = d[k]["where"].rsplit(":", 1)
    print("%-34s %s | %s" % (k, d[k]["where"], 소스[int(줄) - 1][:60]))
PY
```

기대: 모든 줄이 `def <그 이름>(` 로 시작한다. 하나라도 어긋나면 Step 1 을 다시 돌린다.

- [ ] **Step 3: 주석 블록을 만들고 주입한다**

```bash
.venv/bin/python codegraph/xmldoc.py emit
.venv/bin/python codegraph/xmldoc.py inject
.venv/bin/python codegraph/xmldoc.py check
```

기대: `check` 가 `문제 0건`.

- [ ] **Step 4: 인용을 기계로 검사한다**

```bash
.venv/bin/python codegraph/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading docs/codegraph/terms-reading.json
```

기대: `실패 0`. `근거 없음` 은 **1** 이어야 한다 — `normalize.main` 의 구조적 1건이 기준선이고, 그보다 늘면 새로 넣은 레코드의 `where` 가 틀린 것이다.

- [ ] **Step 5: 주입으로 줄이 밀렸으니 시험을 다시 돌린다**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: `145 passed, 19 skipped`.

- [ ] **Step 6: 담아 두고 승인을 기다린다**

```bash
git add codegraph/run_mode1.py docs/codegraph/terms-reading.json docs/codegraph/comments.xml
```

```
[chore] : warmup 배선 함수 6개의 전수조사 레코드와 주석 블록
```

---

## Task 9: 실측 대조 — 이 배선이 값을 하는가

**코드가 아니라 측정이다.** 이 Task 없이는 배선이 정당화되지 않는다.

**Files:** 없음 (측정만)

- [ ] **Step 1: 대조군 — 아무것도 안 바뀐 상태에서 돌린다**

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" \
  --model opus --json /tmp/mode1-nochange.json   # 대조군: 아무것도 안 바뀐 실행
```

기대: `agent` 가 **건너뜀**으로 그려지고 합계 토큰이 0 이다. 전체 시간은 30초 미만이어야 한다
(기계 단계 15.2초 + warmup 의 `declmap.scan`).

- [ ] **Step 2: 소스 한 파일에 국소 변경을 준다**

대상 저장소의 파일 하나를 고른다. **되돌릴 수 있게 먼저 확인한다:**

```bash
cd "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit"
git status --short          # 깨끗한지 본다
git diff --stat core/panorama/panorama.cpp
```

`core/panorama/panorama.cpp` 안의 함수 하나에 주석 한 줄을 더한다(내용은 바꾸지 않는다).
`report-builder` 로 돌아와 판정만 본다:

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" --only warmup
```

기대: `위치만 1` 로 판정되고 `에이전트가 읽을 것` 이 **한 자릿수**여야 한다
(🔵 2026-08-30 실측 — 1홉 파급 평균 1.5파일).

- [ ] **Step 3: 증분 실행을 돌린다**

```bash
.venv/bin/python codegraph/run_mode1.py \
  "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit" \
  --model opus --json /tmp/mode1-incremental.json
```

- [ ] **Step 4: 두 실행을 대조한다**

냉시동 기준선은 이 계획 머리에 **숫자로 박아 두었다** — 그 측정의 JSON 은 한 세션에만
있던 파일이라 다른 기계에서는 없다. 그래서 기준선을 글자로 넣고 증분만 읽는다.

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python - <<'PY'
import json

# 🔵 2026-08-30 QtVisionEdit 냉시동 실측 (이 계획 머리의 표와 같은 값)
기준 = {"total": 17925770, "cache_read": 17437842, "cost_usd": 15.4991,
        "turns": 84, "wall": 1628.1, "읽은파일": 77}

증분 = json.load(open("/tmp/mode1-incremental.json", encoding="utf-8"))
t = 증분["total"]

print("%-12s %14s %14s" % ("", "냉시동", "증분"))
print("%-12s %14s %14s" % ("합계 토큰", "{:,}".format(기준["total"]), "{:,}".format(t["total"])))
print("%-12s %14s %14s" % ("캐시읽기", "{:,}".format(기준["cache_read"]), "{:,}".format(t["cache_read"])))
print("%-12s %14.4f %14.4f" % ("비용($)", 기준["cost_usd"], t["cost_usd"]))
print("%-12s %14d %14d" % ("턴", 기준["turns"], t["turns"]))
print("%-12s %14.1f %14.1f" % ("벽시계(초)", 기준["wall"], 증분["wall_seconds"]))

if 기준["total"]:
    print("\n토큰 %.1f%% 줄었다 · 비용 $%.2f 줄었다"
          % ((1 - t["total"] / 기준["total"]) * 100, 기준["cost_usd"] - t["cost_usd"]))
PY
```

- [ ] **Step 5: 소스 변경을 되돌린다**

```bash
cd "$HOME/DevelopProjects/QT/QTEngineExample/pureimage/opencv/QtVisionEdit"
git diff core/panorama/panorama.cpp        # 무엇을 되돌리는지 먼저 본다
git checkout -- core/panorama/panorama.cpp
git status --short
```

⚠ **`git checkout -- .` 을 쓰지 마라.** 그 저장소에는 이번 실행이 만든
`docs/codegraph/terms-reading.json` 과 `docs/wiki/*.md` 가 커밋되지 않은 채 있다.
경로를 하나만 좁혀서 되돌린다.

- [ ] **Step 6: 결과를 보고한다**

아래 표의 오른쪽 칸을 **Step 4 가 실제로 찍은 숫자로 채워** 사용자에게 낸다.
왼쪽은 이미 잰 값이므로 그대로 둔다.

| | 냉시동 (🔵 2026-08-30) | 증분 (Step 4 출력) |
|---|---|---|
| 벽시계 | 27분 08.1초 | |
| 합계 토큰 | 17,925,770 | |
| 캐시읽기 | 17,437,842 | |
| 비용 | $15.4991 | |
| 턴 | 84 | |
| 에이전트가 읽은 파일 | 77 / 77 | |

그리고 Step 1 의 대조군(아무것도 안 바뀐 실행)이 `agent` 를 **건너뜀**으로 그렸는지,
그때 합계 토큰이 **0** 이었는지 함께 적는다.

**"검증됨" 이라고 쓰지 마라.** 표본이 하나이므로 쓸 수 있는 말은 "명백한 반례가 없다" 까지다.

---

## 남는 것 — 이 계획이 닫지 않는 구멍

착수 전에 알고 있어야 하고, **끝난 뒤 사용자에게 보고한다.**

| 구멍 | 무슨 일이 나나 | 언제 닫나 |
|---|---|---|
| 선언이 하나도 없는 파일 | `declmap.scan` 이 그런 파일을 결과에 안 넣어(`declmap.py:135` 의 `if hits:`) `decl_hash` 가 양쪽 다 `None` 이 된다 → 내용이 바뀌어도 `위치만` 이다. **이 계획이 `위치만` 을 씨앗에 넣으므로 새지는 않는다.** 다만 절약도 없다 | 절약이 모자란 것이 관측될 때 |
| 파급이 얇은 그물 | 🔵 간선이 닿는 파일이 77개 중 16개뿐이다. 나머지는 파급이 자기 자신뿐이라 전이 오염을 못 잡는다 | codegraph 가 멤버·메서드 층을 담게 될 때 |
| `xmldoc.py` 가 저장소 고정 | 대상 저장소의 `where` 좌표를 기계로 못 고친다. 그래서 `위치만` 을 에이전트에 보낸다 | `--repo` 를 받게 고칠 때. 별개 계획이다 |
| 대상 저장소 소스가 조용해야 한다 | 남이 파일을 고치는 중이면 `mtime`·`file_hash` 가 움직이는 과녁이다 | 닫히지 않는다. 실행 전에 `git status` 로 확인한다 |
