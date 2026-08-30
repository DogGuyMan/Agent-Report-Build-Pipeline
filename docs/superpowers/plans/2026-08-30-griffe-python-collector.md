# griffe 기반 Python 정적 수집기 (`normalize_python`) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `machine/normalize.py` 에 세 번째 언어 갈래 `normalize_python()` 을 추가해, griffe 가 낸 Python 덤프를 기존 두 언어와 같은 `codegraph.json`(schema_version 2) 으로 정규화한다.

**Architecture:** C++(clang-uml)·C#(roslyn-dump) 이 이미 쓰는 모양을 그대로 따른다 — 0패스로 모듈·클래스를 평평하게 펴고, 1패스로 노드를 정하고, 2패스로 간선을 정한 뒤 공통 출구 `_assemble()` 로 수렴한다. `_assemble()` 은 재구현하지 않는다. 새 파일을 만들지 않고 `normalize.py` 한 곳에만 절을 더한다 — 언어별 플러그인 구조·파서 레지스트리·추상 Collector 인터페이스를 만들면 그 자체가 이 저장소가 잡으려는 실패다(거울 함정).

**Tech Stack:** Python 3.14 (`.venv/bin/python`) · griffe 2.2.0 · pytest · 표준 라이브러리만 추가 사용(`sys.stdlib_module_names`, `importlib.metadata`)

---

## ⚠ 저장소가 개편 중이다 — 시작 전에 반드시 읽을 것

**이 계획을 쓰는 도중에 다른 세션이 디렉토리를 갈아엎었다.** 🔵 2026-08-30 실측:

| 옛 이름 | 지금 |
|---|---|
| `codegraph/` | **`machine/`** (정적 분석) + **`runner/`** (실행기 `run_mode*.py`, `dispatch.mjs`) |
| `scripts/` | **`viz/`** |
| `src/` | **`viz/src/`** |
| `docs/codegraph/comments.xml` | **`machine/comments.xml`** |

이 계획의 모든 경로는 **새 이름 기준**으로 적혀 있다. 인계 문서
(`docs/handoffs/HANDOFF-2026-08-29-griffe-python-prototype.md`)는 **옛 이름으로 적혀 있으니**
그쪽 경로를 그대로 따르지 마라.

**개편은 끝났다.** 🔵 커밋 `671af75` 기준 `pytest machine/ runner/` **287 통과 · 19 건너뜀**,
`npm test` **177 통과**로 둘 다 초록이다. (계획을 쓰던 중간에는 11건이 실패했으나 해소됐다.)

착수 전에 `git log -3` 과 `ls` 로 위 표가 아직 맞는지 다시 확인하라 — 또 바뀌었을 수 있다.

---

## 이 계획을 쓰기 전에 실제로 확인한 것 (🔵 2026-08-30 세션 실측)

인계 문서 `docs/handoffs/HANDOFF-2026-08-29-griffe-python-prototype.md` 는 griffe 를 설치해 보지
못한 채 쓰였고, **그 문서의 두 전제가 실측으로 무너졌다.** 아래는 이 계획을 쓰는 세션이
실제로 설치하고 돌려서 눈으로 본 것이다.

### 1. griffe 2.2.0 이 실제로 내는 JSON 구조

```
.venv/bin/pip install griffe                       # → griffe 2.2.0
.venv/bin/python -m griffe dump machine -o /tmp/g.json
```

최상위는 `{"<패키지이름>": <모듈객체>}` 하나짜리 dict 다. 모듈 객체의 키:

| 키 | 값 | 비고 |
|---|---|---|
| `kind` | `"module"` | 아래 5종 중 하나 |
| `name` | 짧은 이름 | 완전 수식 이름은 **없다** — 순회하며 직접 이어 붙여야 한다 |
| `filepath` | 패키지는 **list**, 단일 모듈은 **str** | 둘 다 **절대 경로**. 저장소 상대경로로 바꿔야 한다 |
| `members` | **dict** (이름 → 객체) | 🔵 griffe 2.2.0 실측. 인계 문서가 경고한 "v1 부터 list→dict" 는 **이미 dict 다** |
| `imports` | dict (지역이름 → 완전 점 경로) | **이름 해소의 유일한 근거.** 예: `{"Node": "pyfx.base.Node", "json": "json"}` |
| `git_info` | 최상위 모듈에만 | `commit_hash`·`remote_url` 등. **쓰지 않는다** — 기존 `git_commit(repo)` 를 그대로 쓴다 |

`kind` 는 실측 5종이다 — `machine` 패키지 기준 `module`(22) · `class`(1) · `function`(265) ·
`attribute`(61) · `alias`(123).
`alias` 는 import 된 이름이고 `target_path` 에 완전 점 경로를 갖는다.

| 객체 kind | 갖는 키 |
|---|---|
| `class` | `bases`(식 리스트) · `lineno` · `endlineno` · `members` · `decorators` |
| `attribute` | `annotation`(식 또는 null) · `lineno` · `labels`(`["instance-attribute"]` 등) · `value` |
| `function` | `parameters`(각 원소에 `name`·`annotation`·`default`) · `returns`(식 또는 null) · `lineno` |
| `alias` | `target_path` · `lineno` |

### 2. 🔴 인계 문서의 R5 제외 근거는 사실이 아니다

인계 문서는 "griffe 는 타입힌트를 **문자열**로 준다(`List[Foo]` 를 파싱해야 함)" 를 근거로
R5(컨테이너 투과)를 범위 밖에 뒀다. **griffe 2.2.0 은 문자열이 아니라 구조화된 식 트리로 준다.**
문자열로 쓴 주석(`"list[dict[str, Node]]"`)조차 파싱해서 트리로 준다. 🔵 실측 출력:

```json
"dict[str, Node]" → {"cls":"ExprSubscript",
                     "left":  {"cls":"ExprName","name":"dict"},
                     "slice": {"cls":"ExprTuple","elements":[
                                 {"cls":"ExprName","name":"str"},
                                 {"cls":"ExprName","name":"Node"}]}}
"Node | None"     → {"cls":"ExprBinOp","left":{"cls":"ExprName","name":"Node"},
                     "operator":"|","right":"None"}
"Optional[Node]"  → {"cls":"ExprSubscript","left":{"cls":"ExprName","name":"Optional"},
                     "slice":{"cls":"ExprName","name":"Node"}}
"abc.Mapping[str, Node]" → left 가 {"cls":"ExprAttribute","values":[
                              {"cls":"ExprName","name":"abc"},
                              {"cls":"ExprName","name":"Mapping"}]}
"tuple[Node, ...]"→ slice 의 elements 에 문자열 `"..."` 가 그대로 섞여 온다
class Box(Generic[T], Node) → bases: [ExprSubscript(Generic[T]), ExprName(Node)]
```

이 모양은 C# 의 `generic_def` + `type_args` 와 **구조적으로 같다.** `normalize_csharp` 의
`resolve()` 가 이미 하는 일을 그대로 옮기면 된다. **사용자 결정(2026-08-30): R5 를 이번 범위에
포함한다.** 인계 문서의 "R5 제외" 지시는 근거가 사라졌으므로 따르지 않는다.

식 트리에서 만나는 `cls` 는 실측 6종이다 — `ExprName` · `ExprAttribute` · `ExprSubscript` ·
`ExprBinOp` · `ExprTuple`, 그리고 **식이 아닌 맨 문자열**(`"None"`, `"..."`).

### 3. 🔴 자기호스팅 골든 테스트는 사실상 빈 그래프를 검증한다

`machine/` 를 덤프한 결과 🔵 **클래스 1개 · 상속 0개 · 타입 주석 0개**다
(`machine.clangd_refs.Clangd` 하나뿐이다). codegraph.json 의 노드는 C++/C# 과 마찬가지로
**타입**이므로, `machine/` 를 정규화하면 노드 1개·간선 0개가 나온다. 인계 문서가 내세운
"자기호스팅 골든 테스트" 의 근거는 여기서 무너진다.

**사용자 결정(2026-08-30): 합성 픽스처 + 빈약한 자기호스팅.** 실제 불변식은 tmp_path 에
쓴 픽스처 패키지를 **진짜 griffe 로 덤프**해서 검증하고, `machine/` 자기호스팅은
"파이프라인이 죽지 않는다" 는 연기 시험으로만 남긴다. 외부 저장소 의존은 두지 않는다.

### 3-2. 프로토타입으로 미리 밟은 지뢰 둘

이 계획을 쓴 세션이 아래 구현을 scratchpad 에서 **실제로 돌려 봤고**, 그 과정에서 두 가지가
나왔다. 둘 다 계획 본문에 이미 반영돼 있다.

1. **경로** — `os.path.relpath(griffe_filepath, repo)` 를 그냥 쓰면 안 된다. macOS 의 `/var` 는
   `/private/var` 로 가는 심볼릭 링크이고 griffe 는 **해소된** 절대 경로를 준다. `tmp_path` 를
   repo 로 준 테스트에서 상대경로가 `../../private/var/...` 가 되어 **모듈 이름이 `..` 로 나왔다.**
   양쪽에 `os.path.realpath()` 를 씌워 맞춘다.
2. **멤버 순서** — griffe 는 `members` 를 소스 순서가 아니라 **알파벳 순**으로 준다.
   같은 (from, to, kind) 로 접히는 간선에 남는 `label` 은 알파벳 첫 번째다. 실제 griffe 를
   태우는 테스트에서 label 을 주장하면 안 되는 이유다.

### 4. 기존 코드에서 그대로 쓸 것 / 손대지 말 것

| 이름 | 위치 | 이 계획에서 |
|---|---|---|
| `_assemble(nodes, edges, stats, *, language, source_tool, repo)` | `normalize.py` | **그대로 호출.** R1 제거·모듈 의존 유도·최종 dict 조립을 전부 여기서 한다 |
| `git_commit(repo)` | `normalize.py` | `_assemble` 이 부른다. 손대지 않는다 |
| `module_of(path)` | `normalize.py` | **Python 도 그대로 재사용한다**(Task 2 에서 근거와 함께 고정) |
| `build_parser()` | `normalize.py` | `--griffe-dump` 를 배타 그룹의 셋째로 추가 |
| `main()` | `normalize.py` | 2분기 → 3분기 |

**⚠ `<include file="machine/comments.xml" .../>` 주석 태그를 손으로 달지 말 것.**
그것은 `machine/xmldoc.py inject` 가 전수조사 결과로 자동으로 박는 것이다. 새 함수에는
태그 없는 평범한 한 줄 요약 주석만 남긴다.

---

## File Structure

| 파일 | 책임 | 상태 |
|---|---|---|
| `machine/normalize.py` | Python 절 신설 — 상수 4개, 함수 5개, `main()` 3분기 | 수정 (790줄 → 약 990줄) |
| `machine/test_normalize.py` | `── 12.` 절 신설 — 단위 11개 + 픽스처 골든 1개 + 자기호스팅 연기 1개 | 수정 (511줄 → 약 730줄) |
| `requirements.txt` | `griffe` 한 줄 추가 | 수정 |

**절대 건드리지 않는다:** `viz/src/` · `viz/` · `bin/` · `machine/comments.xml`·`machine/terms-reading.json` ·
`machine/terms_db.py` · `machine/comments.xml` · `machine/terms-reading.json`.

**커밋하지 않는다.** 이 저장소는 사용자가 명시적으로 요청할 때만 커밋한다. 아래 각 Task 의
마지막 단계는 커밋이 아니라 **검증 명령 실행**이다.

---

## Task 0: 시작 전 확인

**Files:** 없음 (읽기만)

- [ ] **Step 1: 다른 세션이 같은 파일을 건드리고 있지 않은지 확인**

```bash
cd $REPO_ROOT
git log -3 --oneline
git status --short -- machine/normalize.py machine/test_normalize.py requirements.txt
```

기대: `machine/normalize.py` 와 `machine/test_normalize.py` 가 `git status` 에 **나오지 않는다**.
나오면 다른 세션이 작업 중이다 — 멈추고 사용자에게 보고하라.

- [ ] **Step 2: griffe 설치 확인**

```bash
.venv/bin/pip show griffe | head -2
```

기대: `Name: griffe` / `Version: 2.2.0` (또는 그 이상).
`Package(s) not found` 가 나오면 `.venv/bin/pip install griffe` 로 설치한다.

- [ ] **Step 3: 기준선을 잰다 — "통과" 가 아니라 "지금 상태" 를 적는 것이다**

```bash
.venv/bin/python -m pytest machine/ runner/ -q 2>&1 | tail -15
npm test 2>&1 | tail -5
```

🔵 2026-08-30 실측(개편 완료 후, 커밋 `671af75`): **`287 passed, 19 skipped`** ·
`npm test` **177 통과**. 둘 다 초록이다. 이 숫자를 적어 두었다가 마지막에 비교한다.

계획을 쓰던 중간에는 개편이 진행 중이라 11건이 실패했으나 **지금은 해소됐다.** 그래도
착수 시점에 한 번 직접 재라 — 또 바뀌었을 수 있다.

---

## Task 1: `requirements.txt` 에 griffe 추가

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 의존성 한 줄 추가**

`requirements.txt` 의 마지막 줄(`pytest` 줄) 뒤에 아래를 덧붙인다. 기존 줄들의 주석 형식
(이름 + 공백 정렬 + `#` 한 줄 설명)을 그대로 따른다.

```
griffe          # normalize.py 의 Python 갈래 — griffe dump JSON 을 읽는다
```

- [ ] **Step 2: 파일이 그대로 읽히는지 확인**

```bash
cat requirements.txt
```

기대: `networkx` `numpy` `scipy` `pytest` `griffe` 다섯 줄이 보인다.

---

## Task 2: Python 절의 상수와 외부 그룹핑

**Files:**
- Modify: `machine/normalize.py` — `normalize_csharp()` 끝(`return _assemble(... language="csharp" ...)` 줄) **다음**, `build_parser()` **앞**
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 먼저 쓴다**

`machine/test_normalize.py` **맨 끝**에 아래를 통째로 덧붙인다.

```python
# ── 12. Python (griffe) — 식 트리 해석과 kind 사상 (2026-08-30 신설)
def test_py_kind_map_has_no_ownership():
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같은 이유로 소유 kind 를 쓰지 않는다."""
    assert set(N.PY_KIND.values()) == {"inheritance", "association", "dependency"}
    assert "composition" not in N.PY_KIND.values()
    assert "aggregation" not in N.PY_KIND.values()


def test_py_r7_covers_builtin_scalars_and_literals():
    """R7 — 원시 스칼라뿐 아니라 식 자리에 리터럴로 오는 None 과 ... 도 노드가 아니다."""
    for name in ("str", "int", "float", "bool", "bytes", "None", "NoneType", "object", "..."):
        assert name in N.PY_R7
    assert "Node" not in N.PY_R7


def test_py_transparent_is_concrete_containers_only():
    """R5 투과 목록은 구체 컨테이너와 typing 별칭까지다.

    추상 인터페이스(collections.abc.Mapping/Sequence)는 **넣지 않는다** — C# 이
    IReadOnlyDictionary 를 투과하지 않기로 한 것과 같은 축이다(CS_TRANSPARENT_DEFS 주석).
    """
    for name in ("list", "dict", "set", "tuple", "typing.Optional", "typing.Union"):
        assert name in N.PY_TRANSPARENT
    for name in ("collections.abc.Mapping", "collections.abc.Sequence", "typing.Mapping"):
        assert name not in N.PY_TRANSPARENT


def test_py_external_group_folds_stdlib_into_one():
    """R2 — 외부 하나 = 노드 하나. 표준 라이브러리는 C++ 의 "(STL) std" 와 같은 축으로 하나에 접는다."""
    assert N.py_external_group("json.JSONEncoder") == "(표준) stdlib"
    assert N.py_external_group("collections.abc.Mapping") == "(표준) stdlib"
    assert N.py_external_group("pytest") == "pytest"
    assert N.py_external_group("networkx.DiGraph") == "networkx"
    assert N.py_external_group("") == "(기타)"


@pytest.mark.parametrize("path,expected", [
    ("machine/normalize.py", "machine"),
    ("src/mypkg/core.py", "mypkg"),
    ("pyfx/base.py", "pyfx"),
    ("setup.py", "setup.py"),
])
def test_py_module_of_reuses_folder_tree(path, expected):
    """Python 도 모듈 경계는 폴더 트리다 — 그래서 module_of() 를 **그대로 재사용**한다.

    이 테스트가 있는 이유: module_of() 는 C++ 이 주인이다. C++ 쪽 사정으로 그 함수가
    바뀌면 Python 갈래가 조용히 따라 바뀐다. 그때 여기서 시끄럽게 깨지라고 박아 둔다.
    """
    assert N.module_of(path) == expected
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_kind or py_r7 or py_transparent or py_external or py_module_of" 2>&1 | tail -5
```

기대: FAIL. `AttributeError: module 'normalize' has no attribute 'PY_KIND'`
(`test_py_module_of_reuses_folder_tree` 4건만 통과한다 — `module_of` 는 이미 있다).

- [ ] **Step 3: 상수와 함수를 구현한다**

`machine/normalize.py` 의 `normalize_csharp()` 마지막 줄
(`                     language="csharp", source_tool=dump.get("tool", "roslyn-dump ?"), repo=repo)`)
**바로 다음**, `def build_parser():` 위의 `# <include ...build_parser...>` 주석 **앞**에 삽입한다:

```python
# ═══════════════════════════════ Python (griffe) ═══════════════════════════════

# R7 — 파이썬 원시 타입과 암묵적 기반 타입. 노드로 승격하지 않는다.
#   "None" 은 `Foo | None` 의 오른쪽, "..." 는 `tuple[Foo, ...]` 의 Ellipsis 로 온다.
#   🔵 2026-08-30 실측 — griffe 는 이 둘을 식 객체가 아니라 맨 문자열로 준다.
PY_R7 = {
    "str", "int", "float", "bool", "bytes", "bytearray", "complex",
    "None", "NoneType", "object", "type", "...",
    "Any", "typing.Any",
}

# R5 — 투과 컨테이너. 껍데기를 벗기고 안의 타입으로 내려간다.
#   ⚠ 추상 인터페이스(collections.abc.Mapping 등)는 넣지 않는다 — C# 쪽이
#   IReadOnlyDictionary 를 투과하지 않기로 한 것과 같은 축이다(CS_TRANSPARENT_DEFS 참조).
#   typing 별칭은 import 표를 거치면 "typing.X" 로 펴지므로 그 꼴로 적는다.
PY_TRANSPARENT = {
    "list", "dict", "set", "frozenset", "tuple",
    "typing.List", "typing.Dict", "typing.Set", "typing.FrozenSet", "typing.Tuple",
    "typing.Optional", "typing.Union",
}

# kind 사상. C# 과 같은 이유로 소유 kind(composition/aggregation)가 없다 —
# 파이썬은 모든 바인딩이 참조라 값 멤버/포인터 멤버 구분 자체가 없다.
#   base = 상속 · attr = 클래스 속성 주석 · sig = 메서드 매개변수/반환 주석
PY_KIND = {"base": "inheritance", "attr": "association", "sig": "dependency"}


# 파이썬 외부 타입을 배포 이름 하나로 접는다.
# 쓰는 것: 없음 · 쓰이는 곳: normalize_python
def py_external_group(target):
    """R2 — 외부 하나 = 노드 하나. 입도는 import 루트 이름이다.

    표준 라이브러리는 C++ 의 "(STL) std" · C# 의 "(BCL) netstandard" 와 같은 축으로
    하나에 접는다. 낱낱이 세면 외부 섬이 json·os·re 같은 이름으로 뒤덮인다.
    """
    root = (target or "").split(".")[0]
    if not root:
        return "(기타)"
    if root in sys.stdlib_module_names:
        return "(표준) stdlib"
    return root
```

- [ ] **Step 4: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_kind or py_r7 or py_transparent or py_external or py_module_of" 2>&1 | tail -3
```

기대: `8 passed` (kind 1 + r7 1 + transparent 1 + external 1 + module_of 4).

---

## Task 3: 이름 해소 — `py_expr_name` 과 `py_resolve`

**Files:**
- Modify: `machine/normalize.py` — Task 2 가 넣은 `py_external_group()` 다음
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 먼저 쓴다**

`machine/test_normalize.py` 맨 끝에 덧붙인다:

```python
def test_py_expr_name_reads_name_and_dotted_attribute():
    """식 트리에서 '쓰인 그대로의 점 이름' 을 꺼낸다. 이름이 아닌 식이면 None 이다."""
    assert N.py_expr_name({"cls": "ExprName", "name": "Node"}) == "Node"
    assert N.py_expr_name({"cls": "ExprAttribute", "values": [
        {"cls": "ExprName", "name": "abc"}, {"cls": "ExprName", "name": "Mapping"}]}) == "abc.Mapping"
    assert N.py_expr_name("None") == "None"
    assert N.py_expr_name({"cls": "ExprSubscript", "left": {}, "slice": {}}) is None
    assert N.py_expr_name(None) is None


def test_py_resolve_prefers_import_table_then_same_module():
    """이름 해소 순서: import 표 -> 같은 모듈 -> 못 품(쓰인 그대로).

    griffe 는 식 안의 이름을 짧은 이름으로만 준다(bases 의 "Node"). 완전 수식 이름은
    모듈의 imports 표로만 복원할 수 있다 — 🔵 2026-08-30 실측.
    """
    imports = {"Node": "pyfx.base.Node", "json": "json"}
    fp = {"pyfx.core.Engine", "pyfx.core.Local"}
    assert N.py_resolve("Node", "pyfx.core", imports, fp) == "pyfx.base.Node"
    assert N.py_resolve("json.JSONEncoder", "pyfx.core", imports, fp) == "json.JSONEncoder"
    assert N.py_resolve("Local", "pyfx.core", imports, fp) == "pyfx.core.Local"
    # import 표에도 없고 같은 모듈 1차도 아니면 손대지 않는다 — 빌트인과 타입변수가 여기다.
    assert N.py_resolve("list", "pyfx.core", imports, fp) == "list"
    assert N.py_resolve("T", "pyfx.core", imports, fp) == "T"
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_expr_name or py_resolve" 2>&1 | tail -4
```

기대: FAIL. `AttributeError: module 'normalize' has no attribute 'py_expr_name'`

- [ ] **Step 3: 두 함수를 구현한다**

`machine/normalize.py` 의 `py_external_group()` 다음에 삽입한다:

```python
# 타입 식 트리에서 쓰인 그대로의 점 이름을 꺼낸다.
# 쓰는 것: 없음 · 쓰이는 곳: py_walk_expr
def py_expr_name(expr):
    """식이 단순 이름이면 그 이름을, 아니면 None.

    🔵 2026-08-30 실측 — griffe 는 `abc.Mapping` 을 ExprAttribute 의 values 리스트로,
    `None`·`...` 은 식 객체가 아니라 맨 문자열로 준다. 둘 다 여기서 받는다.
    """
    if isinstance(expr, str):
        return expr
    if not isinstance(expr, dict):
        return None
    if expr.get("cls") == "ExprName":
        return expr.get("name")
    if expr.get("cls") == "ExprAttribute":
        parts = [v.get("name") for v in expr.get("values", []) if isinstance(v, dict)]
        return ".".join(p for p in parts if p) or None
    return None


# 식 안의 짧은 이름을 완전 수식 이름으로 편다.
# 쓰는 것: 없음 · 쓰이는 곳: py_walk_expr
def py_resolve(name, mod_path, imports, first_party):
    """이름 해소 순서: 모듈의 import 표 -> 같은 모듈의 1차 클래스 -> 못 품.

    못 풀면 **쓰인 그대로** 돌려준다. 빌트인(`list`)과 타입변수(`T`)가 그 자리이고,
    호출자는 "점이 없는데 1차도 아니다" 로 그 둘을 걸러낸다.
    """
    head, _, rest = name.partition(".")
    if head in imports:
        return imports[head] + ("." + rest if rest else "")
    same = f"{mod_path}.{name}" if mod_path else name
    return same if same in first_party else name
```

- [ ] **Step 4: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_expr_name or py_resolve" 2>&1 | tail -3
```

기대: `2 passed`.

---

## Task 4: R5 — 식 트리 순회기 `py_walk_expr`

이 계획의 핵심이다. 인계 문서가 "불가능하니 제외" 로 뒀던 자리이고, 실측으로 가능함이
확인된 자리다.

**Files:**
- Modify: `machine/normalize.py` — Task 3 이 넣은 `py_resolve()` 다음
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 먼저 쓴다**

`machine/test_normalize.py` 맨 끝에 덧붙인다. 식 트리 리터럴은 🔵 실제 griffe 2.2.0
출력에서 그대로 옮긴 것이다.

```python
# 이 절의 식 리터럴은 🔵 2026-08-30 griffe 2.2.0 실제 출력에서 그대로 옮겼다.
PYFX_IMPORTS = {"Node": "pyfx.base.Node", "Optional": "typing.Optional",
                "json": "json", "abc": "collections.abc", "Generic": "typing.Generic"}
PYFX_FIRST = {"pyfx.base.Node", "pyfx.core.Engine"}


def _walk(expr):
    """py_walk_expr 를 픽스처 문맥으로 감싼다. (결과, stats) 를 돌려준다."""
    st = Counter()
    got = N.py_walk_expr(expr, "pyfx.core", PYFX_IMPORTS, PYFX_FIRST, st)
    return got, st


def test_py_r5_unwraps_builtin_generic():
    """R5 — list[Node] 는 껍데기를 벗고 Node 로 내려간다. 이게 인계 문서가 못 한다고 본 자리다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprName", "name": "Node"}})
    assert got == ["pyfx.base.Node"]
    assert st["R5 투과 컨테이너 경유"] == 1


def test_py_r5_unwraps_dict_and_drops_key_by_r7():
    """dict[str, Node] — 속이 ExprTuple 이다. str 은 R7 로 죽고 Node 만 남는다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "dict"},
                     "slice": {"cls": "ExprTuple", "elements": [
                         {"cls": "ExprName", "name": "str"},
                         {"cls": "ExprName", "name": "Node"}]}})
    assert got == ["pyfx.base.Node"]
    assert st["R7 원시 타입 버림"] == 1


def test_py_r5_unwraps_optional_and_pep604_union():
    """Optional[Node] 와 Node | None 은 같은 뜻이고 griffe 는 다른 모양으로 준다."""
    got_a, _ = _walk({"cls": "ExprSubscript",
                      "left": {"cls": "ExprName", "name": "Optional"},
                      "slice": {"cls": "ExprName", "name": "Node"}})
    got_b, _ = _walk({"cls": "ExprBinOp",
                      "left": {"cls": "ExprName", "name": "Node"},
                      "operator": "|", "right": "None"})
    assert got_a == ["pyfx.base.Node"]
    assert got_b == ["pyfx.base.Node"]


def test_py_r5_nests_two_levels_deep():
    """list[dict[str, Node]] — 문자열로 쓴 주석도 griffe 가 트리로 파싱해 준다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "list"},
                     "slice": {"cls": "ExprSubscript",
                               "left": {"cls": "ExprName", "name": "dict"},
                               "slice": {"cls": "ExprTuple", "elements": [
                                   {"cls": "ExprName", "name": "str"},
                                   {"cls": "ExprName", "name": "Node"}]}}})
    assert got == ["pyfx.base.Node"]
    assert st["R5 투과 컨테이너 경유"] == 2


def test_py_r5_does_not_unwrap_abstract_interface():
    """abc.Mapping[str, Node] — 인터페이스는 투과하지 않는다. Mapping 자신이 남는다."""
    got, _ = _walk({"cls": "ExprSubscript",
                    "left": {"cls": "ExprAttribute", "values": [
                        {"cls": "ExprName", "name": "abc"},
                        {"cls": "ExprName", "name": "Mapping"}]},
                    "slice": {"cls": "ExprTuple", "elements": [
                        {"cls": "ExprName", "name": "str"},
                        {"cls": "ExprName", "name": "Node"}]}})
    assert got == ["collections.abc.Mapping"]


def test_py_walk_drops_ellipsis_and_type_variables():
    """tuple[Node, ...] 의 "..." 는 R7, Generic[T] 의 T 는 해소 실패로 각각 죽는다."""
    got, st = _walk({"cls": "ExprSubscript",
                     "left": {"cls": "ExprName", "name": "tuple"},
                     "slice": {"cls": "ExprTuple", "elements": [
                         {"cls": "ExprName", "name": "Node"}, "..."]}})
    assert got == ["pyfx.base.Node"]
    assert st["R7 원시 타입 버림"] == 1

    got2, st2 = _walk({"cls": "ExprSubscript",
                       "left": {"cls": "ExprName", "name": "Generic"},
                       "slice": {"cls": "ExprName", "name": "T"}})
    assert got2 == []
    assert st2["해소 실패(빌트인·타입변수)"] == 1


def test_py_walk_stops_at_depth_limit():
    """무한 중첩을 만나도 죽지 않는다 — C# resolve() 의 depth 가드와 같은 자리."""
    expr = {"cls": "ExprName", "name": "Node"}
    for _ in range(12):
        expr = {"cls": "ExprSubscript", "left": {"cls": "ExprName", "name": "list"}, "slice": expr}
    got, st = _walk(expr)
    assert got == []
    assert st["식 깊이 초과"] >= 1
```

파일 상단 import 절의 **표준 라이브러리 묶음**(`import json` / `import os` / `import sys`)
바로 아래, `import pytest` 앞의 빈 줄 **위**에 한 줄을 추가한다:

```python
from collections import Counter
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_r5 or py_walk" 2>&1 | tail -4
```

기대: FAIL. `AttributeError: module 'normalize' has no attribute 'py_walk_expr'` (7건).

- [ ] **Step 3: 순회기를 구현한다**

`machine/normalize.py` 의 `py_resolve()` 다음에 삽입한다:

```python
# 타입 식 하나에서 노드가 될 이름들을 뽑는다. R5 투과와 R7 거르기가 여기 있다.
# 쓰는 것: py_expr_name, py_resolve · 쓰이는 곳: normalize_python
def py_walk_expr(expr, mod_path, imports, first_party, stats, depth=0):
    """R5 — 컨테이너 껍데기를 벗기고 안의 타입 이름들을 모아 돌려준다.

    🔵 2026-08-30 실측 — griffe 2.2.0 은 타입 주석을 문자열이 아니라 식 트리로 준다.
    그래서 C++/C# 처럼 제네릭 문법을 손으로 파싱할 필요가 없고, C# 의 resolve() 가
    type_args 를 따라 내려가던 것과 같은 모양이 그대로 성립한다.

    돌려주는 것은 **완전 수식 이름의 리스트**다. 1차인지 외부인지는 호출자가 정한다.
    """
    if depth > 8:
        stats["식 깊이 초과"] += 1
        return []
    if expr is None:
        return []

    cls = expr.get("cls") if isinstance(expr, dict) else None

    if cls == "ExprBinOp":                    # `Node | None` — 합집합이므로 양쪽 다 본다
        return (py_walk_expr(expr.get("left"), mod_path, imports, first_party, stats, depth + 1)
                + py_walk_expr(expr.get("right"), mod_path, imports, first_party, stats, depth + 1))

    if cls == "ExprTuple":                    # `dict[str, Node]` 의 속
        out = []
        for e in expr.get("elements", []):
            out.extend(py_walk_expr(e, mod_path, imports, first_party, stats, depth + 1))
        return out

    if cls == "ExprSubscript":
        head = py_resolve(py_expr_name(expr.get("left")) or "", mod_path, imports, first_party)
        if head in PY_TRANSPARENT:            # R5 — 껍데기를 벗고 속으로 내려간다
            stats["R5 투과 컨테이너 경유"] += 1
            return py_walk_expr(expr.get("slice"), mod_path, imports, first_party, stats, depth + 1)
        # 투과 대상이 아니면 컨테이너 자신이 관계의 상대다 (인터페이스·사용자 제네릭).
        return py_walk_expr(expr.get("left"), mod_path, imports, first_party, stats, depth + 1)

    name = py_expr_name(expr)
    if not name:
        stats["이름이 아닌 식 버림"] += 1
        return []
    if name in PY_R7:                          # R7 — 쓰인 그대로가 이미 원시 타입
        stats["R7 원시 타입 버림"] += 1
        return []
    key = py_resolve(name, mod_path, imports, first_party)
    if key in PY_R7:                           # R7 — 펴 보니 원시 타입 (typing.Any 등)
        stats["R7 원시 타입 버림"] += 1
        return []
    if key not in first_party and "." not in key:
        # import 표에도 없고 1차도 아닌 맨 이름 — 빌트인이거나 타입변수다. 노드가 아니다.
        stats["해소 실패(빌트인·타입변수)"] += 1
        return []
    return [key]
```

- [ ] **Step 4: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "py_r5 or py_walk" 2>&1 | tail -3
```

기대: `7 passed`.

---

## Task 5: `normalize_python()` — 노드와 간선

**Files:**
- Modify: `machine/normalize.py` — Task 4 가 넣은 `py_walk_expr()` 다음
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 먼저 쓴다**

합성 dict 로 최소 덤프를 만들어 노드·간선의 모양을 고정한다.
`machine/test_normalize.py` 맨 끝에 덧붙인다:

```python
def _pyfx_dump(root):
    """🔵 griffe 2.2.0 출력 모양 그대로의 최소 덤프. 두 모듈 · 두 클래스."""
    return {"pyfx": {
        "kind": "module", "name": "pyfx", "filepath": [f"{root}/pyfx"], "imports": None,
        "members": {
            "base": {
                "kind": "module", "name": "base", "filepath": f"{root}/pyfx/base.py",
                "imports": {},
                "members": {"Node": {
                    "kind": "class", "name": "Node", "lineno": 1, "endlineno": 2, "bases": [],
                    "members": {"ident": {"kind": "attribute", "name": "ident", "lineno": 2,
                                          "annotation": {"cls": "ExprName", "name": "int"}}}}}},
            "core": {
                "kind": "module", "name": "core", "filepath": f"{root}/pyfx/core.py",
                "imports": {"Node": "pyfx.base.Node", "json": "json"},
                "members": {"Engine": {
                    "kind": "class", "name": "Engine", "lineno": 5, "endlineno": 12,
                    "bases": [{"cls": "ExprName", "name": "Node"}],
                    "members": {
                        "nodes": {"kind": "attribute", "name": "nodes", "lineno": 6,
                                  "annotation": {"cls": "ExprSubscript",
                                                 "left": {"cls": "ExprName", "name": "list"},
                                                 "slice": {"cls": "ExprName", "name": "Node"}}},
                        "enc": {"kind": "attribute", "name": "enc", "lineno": 7,
                                "annotation": {"cls": "ExprAttribute", "values": [
                                    {"cls": "ExprName", "name": "json"},
                                    {"cls": "ExprName", "name": "JSONEncoder"}]}},
                        "run": {"kind": "function", "name": "run", "lineno": 8, "endlineno": 9,
                                "parameters": [
                                    {"name": "self", "annotation": None},
                                    {"name": "n", "annotation": {"cls": "ExprName", "name": "Node"}}],
                                "returns": {"cls": "ExprName", "name": "Node"}},
                    }}}},
        }}}


def test_python_nodes_are_classes_with_qualified_names(tmp_path):
    """노드 이름은 완전 수식 점 이름이다 — griffe 가 짧은 이름만 주므로 순회하며 이어 붙인다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    first = {n["name"]: n for n in g["nodes"] if n["kind"] != "external"}
    assert set(first) == {"pyfx.base.Node", "pyfx.core.Engine"}
    assert first["pyfx.core.Engine"]["file"] == "pyfx/core.py"
    assert first["pyfx.core.Engine"]["line"] == 5
    assert first["pyfx.core.Engine"]["module"] == "pyfx"
    assert g["language"] == "python"
    assert g["schema_version"] == 2


def test_python_has_no_ownership_kinds(tmp_path):
    """파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같이 소유 간선이 0이어야 한다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    kinds = {e["kind"] for e in g["edges"]}
    assert "composition" not in kinds
    assert "aggregation" not in kinds
    assert kinds <= {"inheritance", "association", "dependency"}


def test_python_edge_kinds_and_labels(tmp_path):
    """상속 = inheritance · 속성 주석 = association · 시그니처 = dependency."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    by = {n["id"]: n["name"] for n in g["nodes"]}
    got = {(by[e["from"]], by[e["to"]], e["kind"]): e for e in g["edges"]}

    assert ("pyfx.core.Engine", "pyfx.base.Node", "inheritance") in got
    assoc = got[("pyfx.core.Engine", "pyfx.base.Node", "association")]
    assert assoc["label"] == "nodes" and assoc["line"] == 6      # R5 로 list[Node] 를 벗겼다
    dep = got[("pyfx.core.Engine", "pyfx.base.Node", "dependency")]
    assert dep["occurrences"] == 2                                # 매개변수 n + 반환 하나씩
    # Node.ident: int 는 R7 로 죽어 Node 에서 나가는 간선이 없다.
    assert not [e for e in g["edges"] if by[e["from"]] == "pyfx.base.Node"]


def test_python_external_is_folded_and_marked(tmp_path):
    """R2/R6 — json.JSONEncoder 는 "(표준) stdlib" 하나로 접히고 constraint=False 를 단다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ext = [n for n in g["nodes"] if n["kind"] == "external"]
    assert len(ext) == 1
    assert ext[0]["name"] == "(표준) stdlib"
    assert ext[0]["file"] is None and ext[0]["line"] is None
    assert ext[0]["module"] == "__external__"
    assert ext[0]["collapsed_from"] == ["json.JSONEncoder"]
    to_ext = [e for e in g["edges"] if e["to"] == ext[0]["id"]]
    assert len(to_ext) == 1 and to_ext[0]["constraint"] is False


def test_python_r4_no_edges_leave_the_external_island(tmp_path):
    """C-9 R4 — 간선은 1차 -> 외부 단방향만. 파이썬 갈래는 구조상 발생조차 하지 않는다."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ext = {n["id"] for n in g["nodes"] if n["kind"] == "external"}
    assert not [e for e in g["edges"] if e["from"] in ext]


def test_python_module_deps_exclude_external(tmp_path):
    """모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 안 된다(_assemble 의 R3)."""
    g, _ = N.normalize_python(_pyfx_dump(str(tmp_path)), str(tmp_path), "griffe test")
    ids = {m["id"] for m in g["modules"]}
    assert "__external__" not in ids
    for m in g["modules"]:
        assert all(d in ids for d in m["depends_on"])
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "test_python_" 2>&1 | tail -4
```

기대: FAIL. `AttributeError: module 'normalize' has no attribute 'normalize_python'` (6건).

- [ ] **Step 3: `normalize_python()` 을 구현한다**

`machine/normalize.py` 의 `py_walk_expr()` 다음에 삽입한다:

```python
# griffe 덤프를 공통 형식의 노드와 간선으로 바꾼다.
# 쓰는 것: module_of, py_external_group, py_walk_expr, _assemble · 쓰이는 곳: normalize.main
def normalize_python(dump, repo, source_tool):
    """griffe dump(JSON) -> codegraph.json. C++/C# 과 같은 모양(노드 -> 간선 -> _assemble)이다.

    1차/외부 판정에 별도 규칙이 없다 — griffe 는 **지정한 패키지만** 로드하므로 덤프에
    나온 클래스가 곧 1차이고, 주석·상속에서 참조되지만 덤프에 없는 이름이 외부다.
    C++ 의 네임스페이스 허용목록이나 C# 의 어셈블리 대조에 해당하는 것이 필요 없다.
    """
    stats = Counter()

    # ── 0패스: 모듈 나무를 평평하게 편다.
    #    griffe 는 완전 수식 이름을 주지 않고 members 를 이름으로 키질한 dict 로만 준다
    #    (🔵 2026-08-30 griffe 2.2.0 실측 — 조사 문서가 경고한 v1 의 list 가 아니다).
    #    그래서 이름은 여기서 직접 이어 붙인다.
    mods, classes = {}, {}

    def walk_module(obj, path):
        fp = obj.get("filepath")
        fp = fp[0] if isinstance(fp, list) else fp        # 패키지는 list, 단일 모듈은 str
        # ⚠ realpath 로 양쪽을 맞춘다. macOS 의 /var 는 /private/var 로 가는 심볼릭 링크라
        #   griffe(해소된 경로)와 repo(해소 안 된 경로)를 그냥 relpath 하면 "../.." 가 나오고
        #   모듈 이름이 ".." 가 된다. 🔵 2026-08-30 프로토타입에서 실제로 겪었다.
        rel = os.path.relpath(os.path.realpath(fp), os.path.realpath(repo)) if fp else None
        mods[path] = (obj, rel)
        for name, m in (obj.get("members") or {}).items():
            child = f"{path}.{name}"
            if m.get("kind") == "module":
                walk_module(m, child)
            elif m.get("kind") == "class":
                walk_class(m, child, path)

    def walk_class(cls, qname, mod_path):
        classes[qname] = (cls, mod_path)
        for name, m in (cls.get("members") or {}).items():
            if m.get("kind") == "class":                  # 중첩 클래스도 노드다
                stats["중첩 클래스"] += 1
                walk_class(m, f"{qname}.{name}", mod_path)

    for root, obj in dump.items():
        walk_module(obj, root)
    stats["모듈"] = len(mods)

    # ── 1패스: 1차 클래스 -> 노드. 이름은 완전 수식 점 이름이다.
    node_id, nodes = {}, {}
    for qname in sorted(classes):
        cls, mod_path = classes[qname]
        rel = mods[mod_path][1]
        nid = "C%d" % (len(nodes) + 1)
        nodes[nid] = {
            "id": nid, "name": qname, "kind": "class",
            "module": module_of(rel), "file": rel, "line": cls.get("lineno"),
        }
        node_id[qname] = nid
        stats["1차 노드"] += 1

    collapsed = defaultdict(list)

    def to_node(key):
        """R2 — 외부 이름을 배포 이름 하나로 접는다."""
        if key in node_id:
            return node_id[key]
        g = py_external_group(key)
        nid = "X:" + g
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": g, "kind": "external",
                          "module": "__external__", "file": None, "line": None,
                          "collapsed_from": []}
        node_id[key] = nid
        collapsed[nid].append(key)
        stats["외부 원본 타입"] += 1
        return nid

    # ── 2패스: 간선. 적용 순서 R5/R7(py_walk_expr) -> R2(to_node) -> R1/R3 은 _assemble.
    #    R4(외부발 간선)는 여기서 발생하지 않는다 — 간선의 출발은 언제나 1차 클래스다.
    edges = {}
    first_party = set(classes)

    def add(src_q, dst_key, kind, label, file, line):
        s, d = node_id[src_q], to_node(dst_key)
        if s == d:
            stats["자기참조 버림"] += 1
            return
        k = (s, d, kind)
        if k in edges:
            edges[k]["occurrences"] = edges[k].get("occurrences", 1) + 1
            stats["중복 간선 접음"] += 1
            return
        edges[k] = {"from": s, "to": d, "kind": kind, "label": label, "file": file, "line": line}
        if nodes[d]["kind"] == "external":
            edges[k]["constraint"] = False                # R6

    for qname in sorted(classes):
        cls, mod_path = classes[qname]
        imports = mods[mod_path][0].get("imports") or {}
        rel = mods[mod_path][1]

        def walk(expr):
            return py_walk_expr(expr, mod_path, imports, first_party, stats)

        for b in cls.get("bases") or []:
            for key in walk(b):
                add(qname, key, PY_KIND["base"], None, rel, cls.get("lineno"))

        for mname, m in (cls.get("members") or {}).items():
            kind = m.get("kind")
            if kind == "attribute" and m.get("annotation"):
                for key in walk(m["annotation"]):
                    add(qname, key, PY_KIND["attr"], mname, rel, m.get("lineno"))
            elif kind == "function":
                for p in m.get("parameters") or []:
                    if p.get("name") in ("self", "cls") or not p.get("annotation"):
                        continue
                    for key in walk(p["annotation"]):
                        add(qname, key, PY_KIND["sig"], f"{mname}({p['name']})", rel, m.get("lineno"))
                for key in walk(m.get("returns")):
                    add(qname, key, PY_KIND["sig"], f"{mname}()", rel, m.get("lineno"))

    for nid, names in collapsed.items():
        nodes[nid]["collapsed_from"] = sorted(set(names))

    return _assemble(nodes, edges, stats, language="python", source_tool=source_tool, repo=repo)
```

- [ ] **Step 4: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "test_python_" 2>&1 | tail -3
```

기대: `6 passed`.

---

## Task 6: CLI 배선 — `--griffe-dump`

**Files:**
- Modify: `machine/normalize.py:731-749` (`build_parser`) 와 `machine/normalize.py:751-` (`main`)
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 먼저 쓴다**

`machine/test_normalize.py` 맨 끝에 덧붙인다:

```python
def test_cli_griffe_dump_is_a_third_source():
    """수집기 셋은 고르는 관계다 — 배타 그룹의 셋째로 들어간다."""
    a = N.build_parser().parse_args(["--griffe-dump", "g.json", "--repo", "."])
    assert a.griffe_dump == "g.json"
    assert a.clang_uml is None and a.roslyn_dump is None


def test_cli_griffe_dump_conflicts_with_other_sources():
    """--clang-uml 과 함께 줄 수 없다. --clang-doc 과 달리 이건 합치는 관계가 아니다."""
    with pytest.raises(SystemExit):
        N.build_parser().parse_args(["--griffe-dump", "g.json", "--clang-uml", "u.json"])
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "griffe_dump" 2>&1 | tail -4
```

기대: FAIL — `test_cli_griffe_dump_is_a_third_source` 가
`SystemExit: 2` (`unrecognized arguments: --griffe-dump`) 로 죽는다.
(`test_cli_griffe_dump_conflicts_with_other_sources` 는 우연히 통과한다 — 인자를 몰라서 죽기 때문이다.
Step 4 이후에 올바른 이유로 통과하게 된다.)

- [ ] **Step 3-a: `build_parser()` 에 셋째 갈래를 추가한다**

`machine/normalize.py` 의 `build_parser()` 안,
`src.add_argument("--roslyn-dump", ...)` 줄 **바로 다음**에 한 줄을 넣는다:

```python
    src.add_argument("--griffe-dump", help="Python — griffe dump 산출물(JSON)")
```

- [ ] **Step 3-b: `main()` 을 3분기로 고친다**

`main()` 의 `else:` 절(`dump = json.load(open(a.roslyn_dump, ...))` 두 줄)을 아래로 **교체**한다:

```python
    elif a.roslyn_dump:
        dump = json.load(open(a.roslyn_dump, encoding="utf-8"))
        g, stats = normalize_csharp(dump, a.repo)
    else:
        dump = json.load(open(a.griffe_dump, encoding="utf-8"))
        try:
            from importlib.metadata import version as _pkg_version
            tool = "griffe " + _pkg_version("griffe")
        except Exception:
            tool = "griffe ?"
        g, stats = normalize_python(dump, a.repo, tool)
```

- [ ] **Step 3-c: 입력 요약 출력을 3분기로 고친다**

`main()` 의 아래 두 줄

```python
    else:
        print(f"입력: types {len(dump['types'])} / relations {len(dump['relations'])}")
```

을 아래로 **교체**한다:

```python
    elif a.roslyn_dump:
        print(f"입력: types {len(dump['types'])} / relations {len(dump['relations'])}")
    else:
        print(f"입력: 모듈 {stats['모듈']} / 1차 클래스 {stats['1차 노드']}")
```

- [ ] **Step 3-d: 소유 간선 0 안내문을 언어에 맞게 고친다**

`main()` 맨 끝의 아래 두 줄

```python
        # C# — 언어에 소유 표지가 없어 composition/aggregation 이 0이다. association 이 위치를 갖는다.
        assoc = [e for e in g["edges"] if e["kind"] == "association"]
        print(f"  소유 간선 0 (C# 정상 — 함정 5). association {sum(1 for e in assoc if e.get('line'))}/{len(assoc)} 에 위치")
```

을 아래로 **교체**한다:

```python
        # C# · Python — 언어에 소유 표지(값 멤버 vs 포인터 멤버)가 없어 composition/aggregation
        # 이 0이다. association 이 위치를 갖는다.
        assoc = [e for e in g["edges"] if e["kind"] == "association"]
        lang = {"csharp": "C#", "python": "Python"}.get(g["language"], g["language"])
        print(f"  소유 간선 0 ({lang} 정상 — 함정 5). association "
              f"{sum(1 for e in assoc if e.get('line'))}/{len(assoc)} 에 위치")
```

- [ ] **Step 4: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "griffe_dump" 2>&1 | tail -3
```

기대: `2 passed`.

---

## Task 7: 진짜 griffe 로 도는 픽스처 골든 테스트

합성 dict 만으로 검증하지 않는다 — griffe 가 실제로 내는 모양이 바뀌면 여기서 깨져야 한다.

**Files:**
- Test: `machine/test_normalize.py`

- [ ] **Step 1: 픽스처를 실제로 덤프해 검증하는 테스트를 쓴다**

이 절이 처음 쓰는 표준 라이브러리 셋을 파일 상단 import 묶음(`import json` / `import os` /
`import sys` 와 Task 4 가 넣은 `from collections import Counter` 가 있는 자리)에 알파벳 순으로
끼워 넣는다:

```python
import importlib.util
import subprocess
import tempfile
```

그리고 `machine/test_normalize.py` 맨 끝에 덧붙인다:

```python
# ── 13. Python 골든 — 합성 dict 가 아니라 **진짜 griffe** 를 태운다 (2026-08-30 신설)
#    machine/ 자기호스팅은 클래스 2개·상속 0개라 불변식을 못 세운다(🔵 2026-08-30 실측).
#    그래서 픽스처 패키지를 tmp_path 에 써서 돌린다. 저장소를 더럽히지 않는다 —
#    machine/ 안에 두면 자기호스팅 덤프에 그대로 섞여 들어간다(실제로 확인했다).
PYFX_FILES = {
    "pyfx/__init__.py": "",
    "pyfx/base.py": "class Node:\n    ident: int\n",
    "pyfx/core.py": (
        "import json\n"
        "from typing import Optional\n"
        "from .base import Node\n"
        "\n"
        "\n"
        "class Engine(Node):\n"
        "    nodes: list[Node]\n"
        "    table: dict[str, Node]\n"
        "    spare: Optional[Node]\n"
        "    later: Node | None\n"
        "    enc: json.JSONEncoder\n"
        "\n"
        "    def run(self, n: Node) -> list[Node]:\n"
        "        return []\n"
    ),
}


def _griffe_dump(tmp_path, files, pkg):
    """픽스처를 tmp_path 에 쓰고 실제 griffe 로 덤프해 dict 로 돌려준다.

    griffe 가 없으면 건너뛴다 — 기존 골든 테스트 관습(_load 의 pytest.skip)과 같다.
    """
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치 — .venv/bin/pip install -r requirements.txt")
    for rel, body in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    out = tmp_path / "griffe.json"
    r = subprocess.run([sys.executable, "-m", "griffe", "dump", pkg,
                        "-o", str(out), "-s", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_golden_python_fixture_counts(tmp_path):
    """수치가 바뀌면 무언가 변한 것이다 — griffe 의 출력 모양이 바뀌면 여기가 먼저 깨진다.

    노드 3 = Node · Engine · (표준) stdlib.
    간선 4 = 상속 1(Engine->Node) · association 1(Engine->Node, nodes/table/spare/later 가 접힘)
             · association 1(Engine->stdlib, enc) · dependency 1(Engine->Node, run 의 인자와 반환).
    """
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, stats = N.normalize_python(dump, str(tmp_path), "griffe test")
    assert g["schema_version"] == 2
    assert g["language"] == "python"
    assert len(g["nodes"]) == 3
    assert len(g["edges"]) == 4
    assert len(g["modules"]) == 1
    assert stats["R5 투과 컨테이너 경유"] >= 4      # list · dict · Optional · list(반환)


def test_golden_python_r5_recovered_first_party_through_containers(tmp_path):
    """R5 가 없으면 nodes/table/spare/later 네 속성이 통째로 사라진다 — 그게 안 일어나는지 본다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    by = {n["id"]: n["name"] for n in g["nodes"]}
    assoc = [e for e in g["edges"]
             if e["kind"] == "association" and by[e["to"]] == "pyfx.base.Node"]
    assert len(assoc) == 1
    assert assoc[0]["occurrences"] == 4          # nodes · table · spare · later 가 한 간선으로 접힘


def test_golden_python_external_nodes_have_no_location(tmp_path):
    """외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    for n in g["nodes"]:
        if n["kind"] == "external":
            assert n["file"] is None and n["line"] is None
            assert n["module"] == "__external__"


def test_golden_python_ownership_edges_are_absent(tmp_path):
    """C# 과 같은 자리 — 파이썬은 모든 바인딩이 참조라 소유 kind 가 나올 수 없다."""
    dump = _griffe_dump(tmp_path, PYFX_FILES, "pyfx")
    g, _ = N.normalize_python(dump, str(tmp_path), "griffe test")
    assert not [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]


def test_selfhost_python_smoke():
    """machine/ 자기호스팅 — 연기 시험이다. 불변식 검증이 아니다.

    🔵 2026-08-30 실측 — machine/ 는 클래스 2개·상속 0개·타입 주석 0개다. 그래서 이
    시험이 확인하는 것은 "실제 저장소를 태워도 파이프라인이 죽지 않는다" 하나뿐이고,
    간선 개수 같은 것은 여기서 주장하지 않는다. 진짜 불변식은 위 픽스처 골든이 본다.
    """
    if importlib.util.find_spec("griffe") is None:
        pytest.skip("griffe 미설치")
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "g.json")
        r = subprocess.run([sys.executable, "-m", "griffe", "dump", "machine",
                            "-o", out, "-s", repo], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        dump = json.load(open(out, encoding="utf-8"))
    g, stats = N.normalize_python(dump, repo, "griffe selfhost")
    assert g["language"] == "python"
    assert g["schema_version"] == 2
    assert stats["모듈"] > 15                       # 🔵 실측 22개
    assert all(n["module"] == "machine" for n in g["nodes"] if n["kind"] != "external")
    ids = {m["id"] for m in g["modules"]}
    assert "__external__" not in ids
```

- [ ] **Step 2: 테스트를 돌려 통과를 확인한다**

```bash
.venv/bin/python -m pytest machine/test_normalize.py -q -k "golden_python or selfhost_python" 2>&1 | tail -20
```

기대: `5 passed`.

**실패하면 추측으로 기대값을 고치지 마라.** 실제 덤프를 눈으로 보고 원인을 찾는다:

```bash
.venv/bin/python -m griffe dump pyfx -o /tmp/pyfx.json -s <픽스처를_쓴_디렉토리>
.venv/bin/python -c "import json;print(json.dumps(json.load(open('/tmp/pyfx.json')),indent=2,ensure_ascii=False))" | head -80
```

- [ ] **Step 3: 픽스처 골든의 기대값이 실측과 맞는지 눈으로 한 번 확인한다**

```bash
cd $REPO_ROOT && .venv/bin/python - <<'PY'
import json, os, subprocess, sys, tempfile
sys.path.insert(0, "machine")
import normalize as N
FILES = {
    "pyfx/__init__.py": "",
    "pyfx/base.py": "class Node:\n    ident: int\n",
    "pyfx/core.py": ("import json\nfrom typing import Optional\nfrom .base import Node\n\n\n"
                     "class Engine(Node):\n    nodes: list[Node]\n    table: dict[str, Node]\n"
                     "    spare: Optional[Node]\n    later: Node | None\n    enc: json.JSONEncoder\n\n"
                     "    def run(self, n: Node) -> list[Node]:\n        return []\n"),
}
with tempfile.TemporaryDirectory() as td:
    for rel, body in FILES.items():
        p = os.path.join(td, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(body)
    out = os.path.join(td, "g.json")
    subprocess.run([sys.executable, "-m", "griffe", "dump", "pyfx", "-o", out, "-s", td], check=True)
    g, st = N.normalize_python(json.load(open(out)), td, "griffe probe")
print("노드:", [(n["name"], n["kind"]) for n in g["nodes"]])
print("간선:", [(n["kind"], n["label"], n.get("occurrences", 1)) for n in g["edges"]])
print("모듈:", g["modules"])
print("stats:", dict(st))
PY
```

기대 출력 — 🔵 **이 계획을 쓴 세션이 프로토타입으로 실제로 찍어 본 값이다**(예측이 아니다):

```
노드: [('pyfx.base.Node', 'class'), ('pyfx.core.Engine', 'class'), ('(표준) stdlib', 'external')]
간선: [('inheritance', None, 1), ('association', 'enc', 1), ('association', 'later', 4), ('dependency', 'run(n)', 2)]
모듈: [{'id': 'pyfx', 'depends_on': []}]
stats: {'모듈': 3, '1차 노드': 2, 'R7 원시 타입 버림': 3, '외부 원본 타입': 1,
        'R5 투과 컨테이너 경유': 4, '중복 간선 접음': 4}
```

**⚠ label 이 `nodes` 가 아니라 `later` 인 것에 주의하라.** griffe 는 members 를 소스 순서가
아니라 **알파벳 순**으로 준다(`enc` → `later` → `nodes` → `spare` → `table`). 접힌 간선에
남는 label 은 그중 **첫 번째**다. 그래서 실제 griffe 를 태우는 Task 7 의 테스트는 label 을
주장하지 않고 `occurrences` 만 본다. 반대로 Task 5 는 합성 dict 라 순서를 직접 정하므로
label 을 주장해도 된다 — 두 테스트가 다르게 생긴 이유가 이것이다.

---

## Task 8: 전체 검증

**Files:** 없음 (검증만)

- [ ] **Step 1: pytest 전량**

```bash
cd $REPO_ROOT && .venv/bin/python -m pytest machine/ runner/ -q 2>&1 | tail -5
```

기대: Task 0 Step 3 의 기준선에 **새 테스트 30건이 더해진다**
(🔵 실측 기준선 `287 passed, 19 skipped` → `317 passed, 19 skipped`).
**실패가 하나라도 생기면 멈추고 원인을 찾는다.**

- [ ] **Step 2: CLI 가 실제로 도는지 end-to-end 로 확인**

```bash
cd $REPO_ROOT && .venv/bin/python -m griffe dump machine -o /tmp/g-selfhost.json -s . \
  && .venv/bin/python machine/normalize.py --griffe-dump /tmp/g-selfhost.json --repo . -o /tmp/codegraph-py.json
```

기대: 아래 꼴의 출력. **노드 1개는 정상이다** — machine/ 에 클래스가 하나뿐이기 때문이다.

```
/tmp/codegraph-py.json — 노드 1 / 간선 0 / 모듈 1
입력: 모듈 22 / 1차 클래스 1
  ...
외부 노드: 없음
근거 위치가 붙은 간선: 0/0
```

- [ ] **Step 3: JS 쪽 회귀 확인 (영향받으면 범위를 벗어났다는 신호다)**

```bash
cd $REPO_ROOT && npm test 2>&1 | tail -5 && npm run typecheck 2>&1 | tail -3
```

기대: `npm test` **177 통과**, `typecheck` 무출력 통과 (🔵 2026-08-30 실측).
달라지면 `viz/src/`·`viz/` 를 건드렸다는 신호다 — diff 를 다시 보라.

- [ ] **Step 4: xmldoc 주석 파이프라인이 깨지지 않았는지 확인**

```bash
cd $REPO_ROOT && .venv/bin/python machine/xmldoc.py check 2>&1 | tail -10
```

기대: 이 변경 **전과 같은** 결과. 새 함수에 `<include>` 태그를 손으로 달지 않았으므로
새 문제가 늘어나면 안 된다. 늘었으면 태그를 손으로 단 것이다 — 지워라.

- [ ] **Step 5: diff 를 통째로 눈으로 읽는다**

```bash
cd $REPO_ROOT && git diff --stat -- machine/normalize.py machine/test_normalize.py requirements.txt
git diff -- machine/normalize.py | head -250
```

기대: 세 파일만 바뀌어 있다. `viz/src/`·`viz/`·`bin/`·`docs/` 가 나오면 잘못된 것이다.

- [ ] **Step 6: 커밋하지 않는다**

이 저장소는 사용자가 명시적으로 요청할 때만 커밋한다. **`git commit` 을 실행하지 마라.**
사용자가 나중에 커밋을 요청하면 `personal-commit-messages` 스킬로 메시지를 짓는다
(소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음, 트레일러 없음).

---

## Self-review 체크리스트 (Task 8 이후)

- [ ] `composition`/`aggregation` kind 를 Python 갈래에서 만들지 않았는가?
- [ ] R5 를 **실제로 구현**했는가? (`stats["R5 투과 컨테이너 경유"]` 가 0이 아닌가)
- [ ] `<include>` xmldoc 태그를 손으로 달지 않았는가?
- [ ] `_assemble()` 을 재구현하지 않고 그대로 호출했는가?
- [ ] 언어별 플러그인 구조·파서 레지스트리·추상 Collector 인터페이스를 만들지 않았는가?
- [ ] `viz/src/`·`viz/`·`bin/`·`machine/comments.xml`·`machine/terms-reading.json`·`terms_db.py` 를 건드리지 않았는가?
- [ ] 커밋하지 않았는가?

---

## 이 계획이 의도적으로 남긴 구멍 — 보고서에 반드시 적을 것

기능이 아니라 **모르는 것**이다. 조용히 빠뜨리지 말고 최종 보고에 그대로 옮긴다.

| 구멍 | 내용 | 왜 남겼나 |
|---|---|---|
| 모듈 수준 함수의 참조 | 노드가 클래스뿐이라 `def f(x: Foo)` 같은 모듈 수준 함수의 주석은 간선을 만들지 못한다. machine/ 의 함수 519개가 전부 여기 해당한다 | C++ 은 `clang-doc` 이 **함수 노드**를 따로 만든다(`merge_clang_doc`). Python 도 같은 길이 열려 있지만 이번 프로토타입의 범위 밖이다 |
| 중첩 클래스 이름 규약 | Python 갈래는 `Outer.Inner` 로 점을 쓴다. C++ 검증기는 `##` 를 쓴다(`test_nested_name_uses_double_hash`) | 두 규약이 다르다. Python 의 L3 검증 경로는 이 계획에서 **시험되지 않았다** |
| 중첩 클래스 안에서의 이름 해소 | `Outer` 안에서 `Inner` 를 짧은 이름으로 참조하면 `py_resolve` 가 `모듈.Inner` 를 찾아 실패한다 | 드물고, 실패해도 조용히 죽지 않고 `해소 실패` 카운터에 남는다 |
| 타입 주석이 없는 코드 | 주석이 없으면 간선이 0이다. 자기호스팅이 정확히 그 경우다 | 정적 수집기의 원리적 한계다. griffe 의 잘못도 이 계획의 잘못도 아니다 |
| `griffe` 버전 고정 | `requirements.txt` 에 하한/상한을 걸지 않았다 | `members` 가 list→dict 로 바뀐 전례가 있다. 실사용에 들어가기 전에 핀을 박을지 사용자가 정한다 |
| R11 (`schema_version` 3, `loc`/`url`) | 손대지 않았다 | 별도 열린 결정이고 사용자 승인 전이다 |

## 변경 이력

- 2026-08-30 — 최초 작성. 인계 문서의 R5 제외 근거와 자기호스팅 골든 근거가 실측으로
  무너진 것을 반영하고, 사용자 결정(R5 포함 · 합성 픽스처 + 빈약한 자기호스팅)을 계획에 넣었다.
