# 결정 기록 — C# 중간 형식 (`roslyn-dump.json`)

> 작성일: 2026-08-27
> 상위 문서: `HANDOFF-codebase-wiki.md` (Track C)
> 근거 실측: `samples/csharp-unity/OBSERVATION.md` (특히 C·D·E·F·I절)
> 짝 문서: `HANDOFF-unity-pattern-collection.md` (수집 절차)
>
> **이 문서는 형식만 정한다. 도구를 만드는 것은 Track C Phase 7 이고 아직 착수하지 않았다.**

---

## 0. 한 줄 요약

**C# 쪽 도구는 `roslyn-dump.json` 하나를 낸다 — 접지 않은 원시 사실만.**
C-9 의 접기 규칙(R1~R7)·모듈 배정·중복 제거는 **전부 `normalize.py` 가 한다.**

---

## 1. 왜 이 결정이 필요한가

🔵 95 — 관찰 보고서 I절 1번이 이렇게 적었다.

> **C# 쪽에는 "파싱할 도구 출력" 이 존재하지 않는다. 이것이 C++ 쪽과의 가장 큰 구조적 차이다.**
> C++ 쪽은 `cmake --graphviz` 나 clang-uml JSON 처럼 **도구가 정한 출력 형식**을 파싱한다.
> Roslyn 에는 그런 것이 없다 — 라이브러리이고, `INamedTypeSymbol` 객체를 메모리에 줄 뿐이다.

Track C 는 `normalize.py` 를 "언어별 파서 함수 두 개" 로 그렸지만, **C# 쪽은 읽을 형식 자체가
없으므로 그것을 먼저 정하지 않으면 파서를 쓸 수 없다.** 그래서 Phase 5 보다 이것이 먼저다.

현재 존재하는 것은 **최소 시험(probe)이 임의로 정한 탭 구분 텍스트**뿐이다. 실측 원문:

```
kind=inherit	src=AddressableRenamer	dst=UnityEditor.EditorWindow	dstAsm=UnityEditor.CoreModule	at=Assets/@Editors/AddressableRenamer.cs:9
kind=assoc	src=Gamerecipe.StickRush.Data.ScriptableFoodCells	field=_foodCells	dst=System.Collections.Generic.List<Gamerecipe.StickRush.Data.SerialDataFood>	dstAsm=netstandard	attrs=[SerializeField]	at=.../ScriptableFoodCells.cs:11
```

**이 형식을 정본으로 삼지 않는다.** 이유는 §7 에 있다.

---

## 2. 확정 결정

| ID | 결정 | 근거 |
|---|---|---|
| **F1** | 형식은 **JSON 단일 파일 `roslyn-dump.json`** | §7 기각안 1 |
| **F2** | 도구는 **원시 사실만** 낸다. 접기·필터·모듈 배정은 전부 `normalize.py` | C-6(정규화는 Python). 정책을 두 언어로 두 번 구현하면 반드시 어긋난다 |
| **F3** | `types[]` 에 **외부 타입도 넣는다.** 관계는 전부 id → id | clang-uml 도 `std::` 83개를 `elements[]` 에 넣는다. 대칭을 맞춘다 |
| **F4** | 제네릭은 문자열이 아니라 **`type_args` 구조**로 낸다 | R5(컨테이너 투과)를 Python 이 **C# 제네릭 문법을 파싱하지 않고** 처리하게 하기 위해서다 |
| **F5** | `compilation.errors` · `unresolved_types` 는 **필수 필드**이고, 0 이 아니면 `normalize.py` 가 **거부**한다 | 🔵 모드 A 오류 1,055 / B 7,780 / C 0. 실패하면 간선의 `dst` 가 통째로 쓰레기가 된다 |
| **F6** | 모든 관계에 **`dst_assembly` 를 붙인다** | 🔵 경로 판별이 **양방향으로 샌다** (아래 §4) |
| **F7** | `attrs` 를 **버리지 않고 통과**시킨다 | 🔵 `[SerializeField]` 27건. 지금 쓰지 않아도 판단 여지를 남긴다 |
| **F8** | enum 멤버는 **버리지 않고 플래그로** 낸다 | 🔵 209건. 제외는 **정책**이므로 도구가 아니라 `normalize.py` 가 정한다 |
| **F9** | 도구와 `normalize.py` 를 **둘 다 `$REPO_ROOT/codegraph/` 에 둔다.** 대상 저장소 경로는 **인자로 받는다** | 2026-08-27 사용자 확정. 사용자 프로젝트에 도구를 심지 않는다 |
| **F10** | 덤프 범위는 **사용자 코드만 — `compilation` 은 하나다** | 2026-08-27 사용자 확정. 🔵 이미 오류 0건으로 검증된 경로(모드 C)다. 서드파티는 C-9 로 외부 노드 12개에 접힌다 |
| **F11** | **`dependency` 간선을 함께 뽑는다** — 메서드 파라미터·반환형·지역 변수 타입·`new` 표현식 | 2026-08-27 사용자 확정. C++ 쪽 `dependency` 206건과 층을 맞춘다 |

---

## 3. 형식 명세

```json
{
  "format_version": 1,
  "tool": "roslyn-dump 0.1 (Microsoft.CodeAnalysis.CSharp 5.9.0)",
  "repo_commit": "bf54917",
  "engine": { "unity": "6000.0.71f1", "lang_version": "9.0", "defines": 137 },

  "compilation": {
    "assembly": "Assembly-CSharp",
    "sources": 112,
    "references": 395,
    "errors": 0,
    "unresolved_types": 0
  },

  "types": [
    { "id": "T1",
      "name": "Gamerecipe.StickRush.Data.ScriptableFoodCells",
      "kind": "Class",
      "assembly": "Assembly-CSharp",
      "file": "Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs",
      "line": 11,
      "nested_in": null,
      "partial_decls": 1,
      "generic_def": null,
      "type_args": [] },

    { "id": "T42",
      "name": "System.Collections.Generic.List<Gamerecipe.StickRush.Data.SerialDataFood>",
      "kind": "Class",
      "assembly": "netstandard",
      "file": null, "line": null,
      "nested_in": null, "partial_decls": 0,
      "generic_def": "System.Collections.Generic.List`1",
      "type_args": ["T7"] }
  ],

  "relations": [
    { "kind": "inherit", "src": "T3", "dst": "T9",
      "member": null, "attrs": [], "is_enum_member": false,
      "file": "Assets/@Editors/AddressableRenamer.cs", "line": 9 },

    { "kind": "assoc", "src": "T1", "dst": "T42",
      "member": "_foodCells", "attrs": ["SerializeField"], "is_enum_member": false,
      "file": "Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs", "line": 11 },

    { "kind": "depend", "src": "T1", "dst": "T55",
      "member": "LoadAll", "attrs": [], "is_enum_member": false,
      "origin": "parameter",
      "file": "Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs", "line": 34 }
  ]
}
```

`relations[].kind` 는 **`inherit` · `realize` · `assoc` · `depend` 넷이다.**

앞의 셋은 🔵 Q3 의 실측이다 — 64 · 70 · 285.
넷째 `depend` 는 **F11 로 새로 추가**됐다. 최소 시험이 안 뽑았을 뿐 못 내는 것이 아니다(🟡 70).
`INamedTypeSymbol` 을 넘어 **메서드 시그니처와 본문 표현식**까지 훑어야 하므로 도구가 커진다.

| `depend` 의 출처 | Roslyn API |
|---|---|
| 메서드 파라미터 타입 | `IMethodSymbol.Parameters[].Type` |
| 반환형 | `IMethodSymbol.ReturnType` |
| 지역 변수 타입 | `SemanticModel` + `VariableDeclarationSyntax` |
| `new` 표현식 | `ObjectCreationExpressionSyntax` → `GetSymbolInfo` |

⚠ **`composition`/`aggregation` 은 넷에 없고 앞으로도 안 나온다** 🔵 92 —
C# 에 소유와 참조를 가르는 문법이 없다. Track C §6 함정 5 의 예측 (a) 가 그대로 확인됐다.

⚠ **`depend` 를 뽑아도 Unity 의 실제 배선은 절반만 담긴다.** 🔵 `UnityEvent` 의 `m_MethodName`
472건과 `[SerializeField]` 객체 참조의 실제 대상은 **프리팹·씬 YAML 에만** 있다. §6 참조.

⚠ **`new` 표현식은 `depend` 간선의 재료이지 `calls[]` 가 아니다.** Track C §7 이 "나중에 붙일
자리" 로 못박은 것은 `calls[]`(호출 관계)이고, `dependency` 는 **8종 enum 에 이미 있는 정식 kind** 다.
**둘을 섞지 말 것** — `new Foo()` 는 `depend` 로 내고, `foo.Bar()` 호출은 §6 대로 내지 않는다.

> ⚠ **`kind` 낱말을 `codegraph.json` 의 8종 enum 과 같게 쓰지 않는다.** 이 파일은 원시 사실이고,
> enum 으로의 사상(mapping)은 `normalize.py` 가 한다. C++ 쪽에서 clang-uml 의 `aggregation` 이
> `codegraph.json` 의 `composition` 을 뜻하는 어긋남이 실측됐으므로, **낱말이 같으면 오히려 위험하다.**

---

## 4. 필드별 근거 — 전부 실측에서 나왔다

**`compilation.errors` / `unresolved_types` (F5)** 🔵
참조 집합 구성에 따라 이렇게 갈린다.

| 모드 | 참조 구성 | 컴파일 error | 타입 해석 실패 |
|---|---|---|---|
| A | .NET 9 BCL 만 | 1,055 | 대량 (CS0246 675) |
| B | BCL + Unity 섞음 | **7,780** | 사실상 전부 |
| C | **Unity 참조 395개만** | **0** | **0** |

**B 가 A 보다 나쁘다.** `netstandard.dll` 과 .NET 9 BCL 에 같은 타입이 있어 전부 모호해진다
(CS0433 263건 · CS0518 7,094건). **덤프 도구는 `.csproj` 의 `<HintPath>` 전량 +
`<ProjectReference>` 대상 DLL 만 쓰고 호스트 런타임 어셈블리를 섞지 말아야 한다.**

**`dst_assembly` (F6)** 🔵 경로 규칙만 쓰면 양방향으로 샌다.

| 새는 방향 | 실측 |
|---|---|
| 사용자 경로 안에 서드파티 | `Assets/@Editors/SceneHelper/ToolbarExtender/` 2파일 |
| 사용자 어셈블리 안에 서드파티 | `Assembly-CSharp` 안의 `Assets/GPM/Shader/` 9파일 |

`ITypeSymbol.ContainingAssembly.Name` 은 경로 규칙보다 정확하다. **둘 다 받아서 교차 확인한다.**

**`type_args` (F4)** — R5 를 Python 이 문자열 파싱 없이 하기 위한 것이다.
probe 출력은 `dst=System.Collections.Generic.List<...SerialDataFood>` 처럼 **납작한 문자열**이라,
`normalize.py` 가 R5(컨테이너 투과)를 하려면 **C# 제네릭 문법 파서를 손으로 써야 한다.**
Roslyn 은 `INamedTypeSymbol.TypeArguments` 로 이미 구조를 갖고 있으므로 그대로 내면 된다.
🔵 R5 가 없으면 소유 간선이 사라지는 것은 C++ 쪽에서 8건으로 실측됐다.
배열(`string[]`)과 `Nullable<T>` 도 같은 자리로 표현한다.

**`origin` (F11)** — `depend` 간선에만 붙는다. 값은 `parameter` · `return` · `local` · `new` 넷.
어느 출처에서 나온 의존인지 구분하지 못하면 **지역 변수를 뺄지 말지(§8)를 나중에 판단할 수 없다.**
🔵 C++ 쪽 clang-uml 은 이 구분을 주지 않으므로 **C# 만 갖는 정보**다 — 그 비대칭을 기록해 둔다.

**`nested_in` · `partial_decls` (F3)** 🔵 노드 계량이 두 가지다 — 구문 231 / 의미 214.
차이 17 = `partial` 선언 30건 − 고유 이름 13개. **어느 쪽 수인지 명시하지 않으면 대조가 안 된다.**

**`file` / `line`** — C-11 로 **인용 검증 L3 의 판정 대상은 노드뿐이다.**
`types[]` 쪽이 판정에 쓰이고, `relations[]` 쪽은 **채우되 판정에 쓰지 않는다.**
🔵 Roslyn 은 `IFieldSymbol.Locations` 로 필드 선언 줄을 정확히 주므로(표본 4건 전부 일치)
낼 수 있는 값을 굳이 버리지 않는다. C++ 쪽(clang-uml)은 411건 전량에 이 값이 없다.

---

## 5. 경계 — 도구가 하는 일과 `normalize.py` 가 하는 일

| | `roslyn-dump` (C#) | `normalize.py` (Python) |
|---|---|---|
| 타입·관계 열거 | ✅ | |
| 어셈블리 귀속 | ✅ | |
| 위치(`file:line`) | ✅ | |
| 제네릭 인자 분해 | ✅ | |
| 컴파일 건전성 보고 | ✅ | |
| **사용자 / 서드파티 판별** | | ✅ (경로 + `assembly` 교차) |
| **R5 컨테이너 투과** | | ✅ (`type_args` 를 따라간다) |
| **R7 원시·암묵 기반 타입 제외** | | ✅ 🔵 274 → 9 |
| **R2 패키지 이름으로 접기** | | ✅ 🔵 어셈블리 13 → 패키지 12 |
| **R1 전이 확장 금지** | | ✅ 🔵 패키지 간 간선 135 전부 버림 |
| **R4 단방향 · R3 외딴 섬 · R6 `constraint=false`** | | ✅ |
| **모듈 배정 (폴더 트리 9개)** | | ✅ `file` 경로에서 도출 |
| **`kind` 8종 enum 사상** | | ✅ |
| **중복 간선 접기** | | ✅ |

**이 경계가 F2 의 전부다.** 접기 정책이 C# 도구 안으로 들어가면 C++ 쪽과 두 벌이 되고, 반드시 어긋난다.

⚠ **접기의 대가 하나** — 같은 `(from, to, kind)` 를 하나로 접으므로 **근거 위치가 하나만 남는다.**
🔵 `netstandard` 는 310회 접촉되는데 간선은 1개가 된다. 전부 보존해야 하면
`edges[].occurrences` 를 나중에 추가한다(Track C §7 확장 규율 "추가만"). **지금은 만들지 않는다.**

---

## 6. 범위 밖 — 기록만 한다

| 항목 | 실측 | 왜 지금 안 넣나 |
|---|---|---|
| 호출 관계 (`calls[]`) | 🔵 호출식 1,295건 · 서로 다른 `(수신타입.메서드)` 507종 | Track C §7 이 "나중에 붙일 자리 — 지금 만들지 말 것" 으로 못박음 |
| 프리팹·씬 YAML 배선 | 🔵 `m_MethodName` **472건**(사용자 자산 22건), `[SerializeField]` 객체 참조 | 근거가 `file:line` 이 아니라 `file:GUID` 다. **C-11 이후 L3 대상이 아니다** |
| `nodes[].members` · `methods` | — | 같은 이유 |
| 서드파티의 의미 수준 계량 | 미측정 | 135개 어셈블리를 각각 컴파일해야 한다 |

---

## 7. 기각안

**기각 1 — probe 의 탭 구분 `key=value` 형식을 정본으로 삼기.**
이미 존재하고 사람이 읽기 좋다는 장점이 있으나 셋이 걸린다.
① Python 쪽에 **손으로 쓴 파서가 필요**해진다 — JSON 이면 `json.load` 하나로 끝난다.
② `attrs=[SerializeField]` 같은 목록 인코딩이 임시변통이라 항목이 늘면 규칙을 또 정해야 한다.
③ 값에 `=` 가 들어가면 깨진다(기본값 있는 시그니처 등). **부활 트리거:** 없음.

**기각 2 — C# 도구가 `codegraph.json` 을 직접 내기.**
`normalize.py` 의 C# 경로가 비어 사라진다는 장점이 있으나, **C-9 접기 규칙과 모듈 배정이
C# 과 Python 두 곳에 생긴다.** 정책이 두 벌이 되면 반드시 어긋나고, C-6("정규화 스크립트는
Python")과도 충돌한다. **부활 트리거:** C++ 쪽이 파이프라인에서 빠져 언어가 C# 하나만 남을 때.

**기각 3 — 언어 공통 중간 형식 하나로 통일하기.**
C++ 은 **남이 정한 형식(clang-uml JSON · Graphviz `.dot`)을 읽는 일**이고 C# 은 **우리가 정할
형식을 쓰는 일**이다. 공통 형식을 만들면 C++ 쪽에 **변환 계층이 하나 더** 생긴다.
🔵 관찰 보고서 I절 1번이 지목한 비대칭이 실재하므로 대칭을 억지로 만들지 않는다.
**부활 트리거:** 언어가 3개 이상으로 늘 때.

---

## 8. 미결정 — 혼자 정하지 않는다

### ✅ 해소된 것 (2026-08-27 사용자 확정)

| 항목 | 결정 | 결과 |
|---|---|---|
| 도구의 위치 | **둘 다 `report-builder/codegraph/`** (F9) | 사용자 프로젝트에 도구를 심지 않는다. 대상 저장소 경로는 인자 |
| 어셈블리별 다중 컴파일 | **사용자 코드만, `compilation` 하나** (F10) | 형식이 지금 그대로다. `compilations[]` 배열 불필요 |
| `dependency` 간선 | **뽑는다** (F11) | `relations[].kind` 가 3종 → **4종** |

### 남은 것

- **`format_version` 을 `codegraph.json` 의 `schema_version` 과 함께 올릴 것인가** — 별개 축이다.
- 💭 **`depend` 가 얼마나 나올지 모른다.** C++ 은 206건이지만 C# 은 미측정이다.
  `assoc` 285건에 더해지므로 간선 수가 크게 늘 수 있다. **뽑아 본 뒤 R5/R7 적용 전후 수를
  반드시 함께 볼 것** — `(BCL) netstandard` 접촉이 R7 전 274 → 후 9 였던 것과 같은 일이
  `depend` 에서도 일어날 가능성이 높다.
- 💭 **지역 변수 타입까지 `depend` 로 낼 것인가.** F11 은 넷을 다 적었으나, 지역 변수는
  구현 세부라 구조 그림에 노이즈가 될 수 있다. **뽑아 보고 수를 본 뒤 판단한다.**

---

## 9. 구현 노트 (🔵 2026-08-27 — 도구 완성 후 기록)

`codegraph/roslyn-dump/Program.cs` 로 구현됐고 StickRushGame 에서 완주했다.
**probe 실측과의 대사가 전부 일치한다** — inherit 명시 64 · assoc 비열거 285 · realize 70 ·
enum 멤버 209 · `[SerializeField]` 27 · 소스 타입 214 · errors 0.

### 명세와 다르게 한 것 — 전부 기계적 사유다

| # | 구현 | 사유 |
|---|---|---|
| 1 | `void` 반환은 `depend` 로 내지 않는다 | 타입 참조가 아니라 값의 부재다. 정책이 아니라 기계적 제외 |
| 2 | 이름은 키워드가 아니라 정식 이름 (`string` → `System.String`) | normalize 의 R7 매칭이 문자열이라 정식 이름이 필요하다 |
| 3 | `dst_assembly` 필드를 관계에 따로 두지 않았다 | `types[dst].assembly` 로 정규화 — F6 의 취지(교차 확인 재료)는 그대로 충족된다 |
| 4 | 접근자(get/set)·컴파일러 생성 멤버 제외 | 원시 사실이 아니라 컴파일러 파생물이다 |
| 5 | 배열은 `generic_def: "[]"` + `type_args: [원소]` | F4 의 "같은 자리" 를 이렇게 구체화했다 |

### 구현 중 발견 — 명세가 예측하지 못한 것 둘

**(가) 🔵 튜플이 소스 위치를 달고 온다.** `(float, float)` 는 `netstandard` 의
`System.ValueTuple'2` 인데 Roslyn 이 **사용 지점의 소스 위치**를 붙인다.
clang-uml 에서 `std::` 타입의 `source_location` 이 첫 사용 지점을 가리키던 함정
(C++ 관찰 보고서 F절)의 **C# 판본**이다. 따라서 `normalize_csharp` 의 1차 판정은
`file` 유무가 아니라 **어셈블리**다. F6 이 경로·어셈블리 교차 확인을 요구한 이유가 재확인됐다.
`ValueTuple'1~8` 은 R5 투과 목록에 추가했다.

**(나) 🔵 소스 제네릭의 구성 인스턴스가 정의와 별도 심볼로 온다.** `UI_Base<UI_HomeButton>`
류 14건. 위치가 정의와 같으므로 `normalize_csharp` 가 (file, line) 으로 정의 노드에 접는다.
안 접으면 같은 클래스가 그래프에 중복된다.

### 정규화 결과 (StickRushGame, HEAD `bf54917`)

노드 231 (1차 214 + 외부 17) · 간선 540 · 모듈 10 · 모듈 간 의존 20 · **순환 5**
(`Managers ↔ Utils`, `UIs ↔ Controller` 포함). 간선 540/540 전량에 근거 위치.
외부 노드 17개 — probe 시점 12개보다 5개 많다. **`depend`(F11) 가 새로 닿게 한 어셈블리**
(`com.unity.localization` 7 · `com.cysharp.unitask` 2 · `(벤더링) ZString` 1 등)가 원인이며,
§8 이 예고한 "depend 를 뽑으면 R1 통과가 달라진다" 가 실측으로 확인된 것이다.
