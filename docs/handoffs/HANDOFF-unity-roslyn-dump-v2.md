# HandOff — `roslyn-dump` v2: 보고서가 요구하는 C# 사실 채우기

> 작성일: 2026-08-27
> 인계 대상: **`StickRushGame` 저장소를 대상으로 실행되는 Claude Code Agent**
> 대상 저장소: `$CSHARP_REPO` (Unity 6000.0.71f1, HEAD `bf54917`)
> 고칠 도구: `$REPO_ROOT/codegraph/roslyn-dump/Program.cs`
> 상위 문서: `$REPO_ROOT/docs/handoffs/HANDOFF-codebase-wiki.md` (Track C)
> 형식 명세: `DECISION-csharp-intermediate-format.md` (F1~F11 + §9 구현 노트)
> 짝 상황: C++ 은 이 정보를 clang-uml 이 공짜로 준다. **C# 만 우리가 채워야 한다**

> ⚠ **도구는 `report-builder` 에 있고 대상은 `StickRushGame` 이다.** C-12 가 "파이프라인 코드는
> 전부 report-builder, 대상 저장소 경로는 인자" 로 정했다. 이 작업은 **도구를 고치고
> StickRushGame 을 대상으로 돌려 검증**하는 것이다. 사용자 프로젝트에 코드를 심지 않는다.

---

## 0. 목적 — 이것부터 읽어라

> **`roslyn-dump` v1 은 "구조" 를 낸다. 보고서는 "구조 + 살" 을 요구한다. 그 살을 채우는 것이 전부다.**

파이프라인은 이미 끝까지 돈다 🔵 — `roslyn-dump` → `normalize_csharp()` → `codegraph.json` →
모듈 다이어그램. **막힌 것은 그 다음 계층이다.**

🔵 2026-08-27 실측 — C# 으로 클래스 층 다이어그램을 시도한 결과:

```
$ render_classes.py <C# codegraph.json> --module UIs
⚠ --detail 이 없다. 3분할 없이 이름 상자만 그린다 — P3 가 아니다.
  초점 'UIs' 클래스 50 / 표시 노드 80 / 간선 108
```

**간선은 다 나오는데 노드가 빈 상자다.** C++ 은 같은 명령이 UML 3분할(멤버 + 소유권 노트 +
메서드)을 그린다 — clang-uml 이 `members[]` 와 `methods[]` 를 주기 때문이다.

### ⚠ Track C §7 의 금지와 헷갈리지 말 것 — 이건 그 금지가 아니다

§7 은 이렇게 적었다.

> **나중에 붙일 자리 (지금 만들지 말 것)**: `nodes[].members`, `nodes[].methods`, `calls[]`

**그 금지의 대상은 `codegraph.json` 이다.** 이 작업이 채우는 것은 **`roslyn-dump.json`** 이고,
그것은 우리가 정한 중간 형식이다(F1). 대칭을 보면 분명하다:

| | 구조(노드·간선·kind) | 살(멤버·메서드) |
|---|---|---|
| C++ | `codegraph.json` | **`full_class_all.json`** (clang-uml 원문) |
| C# | `codegraph.json` | **`roslyn-dump.json`** ← 여기를 채운다 |

`render_classes.py` 는 이미 이 구조로 되어 있다 — 구조는 `codegraph.json` 에서, 살은
`--detail <원문>` 에서 읽는다. **`codegraph.json` 스키마는 건드리지 않는다.**

---

## 1. 지금 상태 — v1 이 내는 것 🔵 (2026-08-27 실측)

```
$ dotnet run --project codegraph/roslyn-dump -- $CSHARP_REPO
소스 112개 / HintPath 참조 378개 / ScriptAssemblies 치환 17개 / defines 137 / LangVersion CSharp9
  compilation — errors 0 / unresolved 0
  types 403 (소스 214 + 외부 189)
  relations 1586 — inherit 190 · assoc 494 · depend 832 · realize 70
  depend origin — return 165 · parameter 283 · local 216 · new 168
  enum 멤버 플래그 209 / [SerializeField] 27
```

**`types[]` 레코드가 가진 키 (전부):**

```
assembly · file · generic_def · id · kind · line · name · nested_in · partial_decls · type_args
```

**없는 것:** `members` · `methods` · `is_abstract` · `accessibility`

🔵 **이미 있는 것은 다시 만들지 말 것** — `kind` 가 `Class` 126 / `Enum` 62 / `Interface` 33 /
`Struct` 7 로 갈려 있으므로 **«interface» 스테레오타입은 지금도 가능**하다.

---

## 2. 격차 — 보고서의 어느 계층이 무엇 때문에 막혔나

Track C §3 파이프라인의 소비자별로 적는다.

| 소비자 | 필요한 것 | 지금 | 막힌 이유 |
|---|---|---|---|
| **클래스 다이어그램 (P3 3분할)** | 멤버명·타입·접근자, 메서드명·접근자·가상성 | ❌ | `members`/`methods` 부재 |
| **소유권 이중 인코딩** (스킬 규정) | 멤버 이름 ↔ 간선 `label` 매칭 | 🔸 | 간선의 `member` 는 있으나 노드 쪽 멤버 목록이 없어 대조 불가 |
| **«interface» / 추상 표시** | `kind` + `is_abstract` | 🔸 | 인터페이스는 되고 **추상 클래스는 안 된다** |
| **진입점 식별** (Track C §1 17) | `MonoBehaviour` 전이 파생 여부 | ❌ | 🔵 정규식 5 vs Roslyn 45 — 정규식은 **하한도 상한도 아니다**. 도구가 내야 한다 |
| **facts 표 / 위키 사실 주입** | 위와 같음 | ❌ | 같은 이유 |
| 모듈 다이어그램 | 노드·간선·모듈 | ✅ | 이미 됨 |
| 순환 검출 · 경계 검사 | 모듈 의존 | ✅ | 이미 됨 (순환 5개 측정) |
| 인용 검증 L1/L2/L3 | `file`/`line` | ✅ | 간선 540/540 전량에 위치 |

**즉 막힌 것은 넷이고 그 넷의 원인은 사실상 하나다 — 노드 안의 살.**

---

## 3. 해야 할 일

### D1 — `types[].members[]` 를 낸다

`INamedTypeSymbol.GetMembers()` 의 `IFieldSymbol` 과 `IPropertySymbol`.

```json
"members": [
  { "name": "_foodCells", "type": "System.Collections.Generic.List<...SerialDataFood>",
    "access": "private", "is_static": false, "attrs": ["SerializeField"],
    "file": "Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs", "line": 11 }
]
```

- **타입은 정식 이름으로** (`System.String`, `string` 아님). §9 구현 노트 2번과 같은 이유 —
  `normalize.py` 의 R7 매칭이 문자열이다.
- **프로퍼티도 넣되 `is_property: true` 로 구분한다.** C# 은 프로퍼티가 사실상 필드 역할을 하고
  Unity 코드에 흔하다. 구분해 두면 렌더러가 나중에 고를 수 있다.
- ⚠ **enum 멤버는 그대로 낸다.** `is_enum_member` 플래그만 붙인다 — 버리는 것은 정책이고
  정책은 `normalize.py` 몫이다(F2·F8).
- ⚠ **컴파일러 생성 멤버는 뺀다**(`IsImplicitlyDeclared`). 원시 사실이 아니라 파생물이다.

### D2 — `types[].methods[]` 를 낸다

`IMethodSymbol` 중 `Ordinary` 와 `Constructor`.

```json
"methods": [
  { "name": "LoadAll", "access": "public", "is_static": false,
    "is_abstract": false, "is_virtual": false, "is_override": false,
    "param_count": 2, "returns": "System.Threading.Tasks.Task",
    "file": "...", "line": 34 }
]
```

- **파라미터는 개수만.** 🔵 `render_classes.py` 는 `+ Name()` 형태로만 그리고, 인자 없는
  `Get*`/`Is*` 를 접근자로 걸러내는 데에만 개수를 쓴다. 전체 시그니처는 지금 쓰이지 않는다.
  **필요해지면 그때 추가한다**(확장 규율 "추가만").
- **접근자(get/set)·컴파일러 생성은 뺀다** — §9 구현 노트 4번과 같은 기준.
- ⚠ **"사소한 메서드 걸러내기" 를 도구가 하지 말 것.** 그것은 렌더러의 표시 정책이다(F2).
  도구는 전부 내고 `render_classes.py` 의 `pick_methods()` 가 고른다.

### D3 — `types[].is_abstract` 를 낸다

`INamedTypeSymbol.IsAbstract`. 🔵 `kind == "Interface"` 는 이미 되므로 **추상 클래스만 남았다.**
`render_classes.py` 가 «interface» 스테레오타입을 붙이는 조건이 이것이다.

### D4 — Unity 진입점 재료: `MonoBehaviour` 전이 파생 표시

```json
"unity": { "is_monobehaviour": true, "is_scriptable_object": false }
```

**`BaseType` 을 타고 올라가며 판정한다.** 🔵 이것이 중요한 이유 —
정규식은 **5개**를 세고 Roslyn 은 **45개**를 센다. 중간 기반 클래스(`UI_Base` 26개 등)를
정규식이 못 따라가기 때문이다. `HANDOFF-unity-boundary-rules.md` §3 단계 2 가
"정확한 수가 필요하면 `roslyn-dump` 이후로 미룬다" 고 적은 그 항목이다.

⚠ **판정하지 말고 표시만 한다.** "이것이 진입점이다" 는 사람이 `codegraph-rules.toml` 에 적는다.

### D5 — 재실행하고 대사한다

```bash
cd $REPO_ROOT
dotnet build codegraph/roslyn-dump
dotnet run --project codegraph/roslyn-dump -- $CSHARP_REPO
.venv/bin/python codegraph/normalize.py \
  --roslyn-dump $CSHARP_REPO/out/codegraph-raw/roslyn-dump.json \
  --repo $CSHARP_REPO \
  -o $CSHARP_REPO/out/codegraph-raw/codegraph.json
```

---

## 4. 검증 — 세 가지를 통과해야 끝난 것이다

### 4-1. 회귀 — v1 수치가 하나도 바뀌면 안 된다 🔵

**살을 더하는 작업이므로 구조 수치는 그대로여야 한다.** 하나라도 어긋나면 D1~D4 중
무언가가 관계 추출을 건드린 것이다.

| 항목 | v1 실측 | v2 |
|---|---|---|
| compilation errors / unresolved | 0 / 0 | 0 / 0 이어야 한다 |
| types (소스 / 외부) | 403 (214 / 189) | 같아야 한다 |
| relations | 1,586 | 같아야 한다 |
| inherit / realize / assoc / depend | 190 / 70 / 494 / 832 | 같아야 한다 |
| enum 멤버 플래그 | 209 | 같아야 한다 |
| `[SerializeField]` (간선 쪽) | 27 | 같아야 한다 |
| `normalize` 후 노드 / 간선 / 모듈 | 231 / 540 / 10 | 같아야 한다 |
| 모듈 순환 | 5 | 같아야 한다 |

### 4-2. probe 대사 — 원래 기준과도 계속 맞아야 한다 🔵

| 항목 | probe 실측 |
|---|---|
| inherit (암묵 기반 `System.Object`/`ValueType`/`Enum` 제외) | **64** |
| assoc (enum 멤버 제외) | **285** |
| realize | **70** |
| 소스 타입 | **214** |

### 4-3. 새 필드의 L3 대조 — 표본이 아니라 전수로 🔵

**멤버·메서드의 `file`/`line` 이 실제 그 줄을 가리키는지 확인한다.**
⚠ **표본 10건으로 하지 말 것.** C++ 쪽에서 표본 10건은 100% 통과했는데 전수 203건으로 재니
중첩 타입 5건이 어긋났다(관찰 보고서 F-2). **같은 실수를 반복하지 않는다.**

```
멤버 N건 중 그 줄에 그 이름이 있는 것: ?/N
메서드 M건 중 그 줄에 그 이름이 있는 것: ?/M
```

불일치가 나오면 **원인을 적는다** — C# 은 `partial` 과 프로퍼티 접근자에서 어긋날 소지가 있다.

### 4-4. 그림이 실제로 나오는지

```bash
.venv/bin/python codegraph/render_classes.py \
  $CSHARP_REPO/out/codegraph-raw/codegraph.json \
  --module Data --detail $CSHARP_REPO/out/codegraph-raw/roslyn-dump.json \
  -o out/diagrams/csharp-data-classes
```

⚠ **`render_classes.py` 의 `--detail` 리더는 지금 clang-uml 형식만 안다.**
`load_detail()` 이 `elements[].display_name` 을 키로 쓴다. **`roslyn-dump.json` 은
`types[].name` 이므로 리더를 한 갈래 더 태워야 한다.** 이것도 이 작업의 범위다.

⚠ **초점 모듈을 `UIs` 로 고르지 말 것** — 🔵 클래스 50 / 표시 80 / 간선 108 로 너무 크다.
`Data`(53)도 크다. **작은 것부터**(`Exceptions` 2 · `Fixture` 1 · `Interface` 13)
확인하고 큰 모듈은 생략 규칙을 따로 정한다(§6).

---

## 5. 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| `codegraph.json` 스키마에 `members`/`methods` 를 넣는 것 | Track C §7 이 금지한 것이 **이것**이다. `roslyn-dump.json` 에만 넣는다 |
| 도구가 "사소한 메서드" 를 걸러내는 것 | 표시 정책은 렌더러 몫이다(F2). 도구는 원시 사실만 |
| 도구가 "이것이 진입점이다" 라고 판정하는 것 | 사람이 `codegraph-rules.toml` 에 적는다 |
| 관계 추출 로직을 건드리는 것 | §4-1 회귀가 깨진다. 이 작업은 **더하기만** 한다 |
| 참조 집합을 바꾸는 것 | 🔵 모드 C(csproj 목록만)가 오류 0건의 유일한 구성이다. BCL 을 섞으면 7,780건 난다 |
| `calls[]` (호출 관계)를 내는 것 | Track C §7 이 "나중에 붙일 자리" 로 못박았다. `depend` 와 다르다 |
| Unity 에디터로 씬·프리팹을 저장하는 것 | 재직렬화로 사용자 작업물에 diff 가 생긴다 |

---

## 6. 미결정 — 혼자 정하지 않는다

- **큰 모듈의 생략 규칙.** 🔵 `UIs` 는 클래스 50 / 간선 108 이라 한 장에 안 들어간다.
  중요도 상위 N개만 그릴지, 서브폴더로 더 쪼갤지, 아니면 클래스 층은 작은 모듈에만 쓸지.
  **Track C §1 20번("무엇을 생략할지")이 LLM 에만 남는 넷 중 하나로 분류한 항목이다.**
- **프로퍼티를 멤버로 볼 것인가 메서드로 볼 것인가.** D1 은 멤버로 두되 `is_property` 로
  구분하도록 했다. 렌더러가 어느 칸에 그릴지는 그림을 보고 정한다.
- **`param_count` 만으로 충분한가.** 지금 소비자는 그것만 쓴다. 전체 시그니처가 필요해지는
  시점이 오면 추가한다.

---

## 7. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만 인정한다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- **정규식 계수를 "정확한 수" 로 쓰지 말 것.** 🔵 이 저장소에서 양방향 오차가 실측됐다 —
  `MonoBehaviour` 정규식 5 / Roslyn 45, `StartCoroutine` 정규식 5 / Roslyn 1(주석 4건을 셌다).
- 설명은 메커니즘 우선, 한국어 + 영문 기술용어 병기. **약어와 압축 표현을 피할 것.**
- 커밋이 필요하면 `personal-commit-messages` 스킬을 따른다.
- **사용자 프로젝트를 바꾸지 않는다.** 이 작업이 StickRushGame 에 남기는 것은
  `out/codegraph-raw/` 의 재생성된 산출물뿐이다.
- **거울 함정을 경계하라.** 이 작업은 Roslyn 심볼에서 필드 몇 개를 더 읽어 JSON 에 넣는 것이다.
  추상 계층·플러그인 구조·설정 파일이 나오면 그 자체가 Track C 가 잡으려는 실패다.
- 끝나면 `DECISION-csharp-intermediate-format.md` 에 **F12~F14 로 형식 확장을 기록**하고,
  §9 구현 노트에 발견한 것을 덧붙인다.

---

## ✅ 실행 완료 (2026-08-27) — 오케스트레이터 보고용

**고친 것** — `codegraph/roslyn-dump/Program.cs` 416 → 527줄, `codegraph/render_classes.py` 의
`load_detail()`. **사용자 프로젝트에 남긴 것은 `out/codegraph-raw/` 재생성분뿐이다**(§7 규약 준수).

### D1~D5 — 전부 구현

```
v2 살 — members 695 · methods 532 · is_abstract=true 25
        · MonoBehaviour 45 · ScriptableObject 6
```

`types[]` 에 붙은 키: `is_abstract` · `accessibility` · `unity` · `members` · `methods`.
**소스 선언 타입 214개에만 채웠다.** 외부 189개는 `null` — C-9 로 외딴 섬에 접히므로 살이 쓰이지 않는다.

### §4 검증 — 넷 전부 통과

**4-1 회귀 — 12개 항목 전부 동일** 🔵 (`codegraph.json` 에 `members`/`methods` 가 새지 않았음도 확인 — §5 금지 준수)

**4-2 probe 대사 — 4개 전부 일치** (inherit 64 · assoc 285 · realize 70 · 소스 타입 214)

**4-3 새 필드 L3 — 표본이 아니라 전수** 🔵

```
멤버   694/695        메서드 532/532        → 위치 정확도 1,227/1,227 (100%)
```

불일치 1건은 **위치 오류가 아니라 인덱서**다 — `IPropertySymbol.Name` 이 `this[]` 를 주는데
소스는 `public List<int> this[int i] {` 다. 줄은 정확하다.
⚠ **`partial` 은 어긋나지 않았다** — 명세가 예측한 위험처였으나 `partial_decls ≥ 2` 인 타입 10개
(`InGameController` 5분할 등)가 전부 통과했다. `SrcLoc` 이 파일·줄 순 정렬로 첫 선언을 고르기 때문이다.

**4-4 그림** — `⚠ --detail 이 없다` 경고가 사라졌다.
`Exceptions 2/4/3` · `Fixture 1/9/8` · `Interface 13/46/57`(«interface» 11) · `Utils 14/29/42`(멤버 31행 · 메서드 34행).
`load_detail()` 은 입력에 `elements` 가 있으면 clang-uml, 없으면 `types` 를 읽는다. **형식 어댑터일 뿐 표시 정책은 넣지 않았다**(F2).

### 형식 확장 기록

`DECISION-csharp-intermediate-format.md` 에 **F12~F14** 를 확정 결정으로 추가하고
**§10 v2 구현 노트**를 새로 썼다.

### §6 미결정 갱신

- ⏳ **큰 모듈의 생략 규칙** — 여전히 미결정이고 **이제 급하다.** 🔵 `Utils`(클래스 14)의
  렌더 결과가 가로 **6,771px** 이다. `UIs` 50 · `Data` 53 · `Controller` 63 은 더 크다.
- ⏳ **프로퍼티를 멤버로 볼 것인가** — `is_property: true` 로 내고 렌더러가 멤버 칸에 그린다. 그림을 보고 정할 일.
- ✅ **`param_count` 만으로 충분한가** — 지금 소비자는 그것만 쓴다. 충분했다.

### 새로 발견된 결함 — 이 작업이 만든 것이 아니다

**`Managers` 모듈은 Graphviz 15.1.1 이 죽는다.**

```
Assertion failed: (LIST_SIZE(&arr) == agnnodes_z(sg)), function fixLabelOrder, file mincross.c, line 273.
```

`--detail` **없이도 똑같이 죽는다** — v1 과 같은 조건에서 재현되므로 D1~D4 가 원인이 아니다.
💭 55 원인 미확정. **별도 과제다.**
