# HandOff — C# / Unity 저장소 패턴 수집 (Track C 선행 작업)

> 작성일: 2026-08-27
> 인계 대상: **Unity 프로젝트 저장소 안에서 실행되는 Claude Code Agent**
> 대상 저장소: **`StickRushGame`** — **2026-08-27 사용자 확정.**
> 후보 3종(`StickRushGame` / `Unity-Chess-main` / `MPB-StonAge`) 중 사용자가 고른 것이며 추정이 아니다.
> 상위 문서: `$REPO_ROOT/docs/handoffs/HANDOFF-codebase-wiki.md` (Track C)
> 짝 문서: `HANDOFF-cpp-pattern-collection.md` (C++ 쪽 같은 작업)
> 후속 문서: `DECISION-csharp-intermediate-format.md` — **이 수집 결과로 확정한 `roslyn-dump.json` 형식**

> ⚠ **같은 이름의 사본이 두 곳에 있고, 내용이 다르다. 어느 쪽인지부터 확정하라.**
>
> ~~두 사본이 커밋(`e681003`)과 미커밋 변경 수(1,001건)가 같다~~ — **이 서술은 틀렸다.**
> 🔵 2026-08-27 재측정:
>
> | | `$DEV_ROOT/StickRushGame` | `$CSHARP_REPO` |
> |---|---|---|
> | inode | 255288162 | 255626426 |
> | Unity | 2022.3.30f1 | **6000.0.71f1 (Unity 6)** |
> | HEAD | `e681003` | `bf54917` (관찰 보고서 작성 시점은 `c0a610f`) |
> | 미커밋 | 1,001건 | **0건** |
> | 추적 `.asset` | 211개 | **213개** |
>
> **수집 세션은 `UnityProjects/` 쪽 = Unity 6 에서 돌았고, 아래 §1 과 관찰 보고서의 모든 수치가
> 그 기준이다.** 다른 사본에서 실행하면 §1 부터 다시 재야 한다.
> `out/codegraph-raw/00-commit.txt` 옆에 `pwd` 출력을 함께 남겨 관찰 보고서 머리말의
> "저장소 경로" 에 적는다.

---

## 0. 목적 — 이것부터 읽어라

> **`normalize.py` 를 쓰기 위한 재료를 모아 오는 것이 전부다. `normalize.py` 를 쓰는 것도,
> Roslyn 덤프 도구를 만드는 것도 이 작업이 아니다.**

Track C §5 Phase 7 이 순서를 못박았다.

> "**C++ 로 파이프라인을 완성한 뒤에 시작할 것.** 인터페이스 형식이 먼저 굳어야 C# 도구가 무엇을
> 뱉어야 할지 알고 만들어진다. 반대로 하면 두 번 짜게 된다."

이 규정은 **덤프 도구 제작**에 걸린 것이지 관찰에 걸린 것이 아니다. 그래서 이 작업은
관찰까지만 하고, 아래 §3 단계 4는 **수십 줄짜리 최소 시험(probe)** 으로 제한한다.
본격 덤프 도구는 C++ 쪽이 끝난 뒤에 별도로 만든다.

### 이 작업이 끝났다고 말할 수 있는 조건

1. `out/codegraph-raw/` 에 원시 산출물이 있다.
2. `$REPO_ROOT/docs/handoffs/samples/csharp-unity/` 에 관찰 보고서와 표본이 복사돼 있다.
3. **§2 의 핵심 질문 세 개에 측정으로 답했다.** 답이 없으면 작업이 끝난 것이 아니다.

### 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| `normalize.py` 를 쓰는 것 | 두 언어 보고서가 모두 도착한 뒤에 쓴다 |
| 본격 Roslyn 덤프 도구를 만드는 것 | Track C Phase 7 의 순서 규정 위반. 최소 시험까지만 |
| `codegraph.json` 스키마를 고치거나 `kind` enum 을 늘리는 것 | **8종 고정**(C-10, 2026-08-27 확장: 6종 + `instantiation` + `friendship`). 관찰만 적고 판단은 사용자 |
| Unity 에디터로 프로젝트를 저장하거나 씬·프리팹을 여는 것 | 에디터가 메타파일·씬을 재직렬화해 사용자 작업물에 diff 를 만든다 |
| 외부 의존을 전이로 펼치는 것 (`packages-lock.json` 의 depth ≥ 1) | Track C §2-1 (C-9) 위반. 아래 §2-2 참조 |
| 외부 모듈을 어셈블리 단위로 쪼개 노드로 만드는 것 | 같은 이유. **패키지 이름 노드 하나**로 접는다 |
| 산출물을 요약·정리해서 보고하는 것 | 파서는 **원문 형태**를 보고 쓰인다 |

---

## 0-1. 진행 상황 (🔵 2026-08-27 — 이 절의 수치는 전부 실행한 명령의 출력)

> **수집은 끝났다.** §0 의 완료 조건 셋을 전부 만족한다.
> 관찰 보고서 `samples/csharp-unity/OBSERVATION.md` 가 A~I 채움 + G-1 추가 상태다.

### 단계별 결과

| 단계 | 결과 | 비고 |
|---|---|---|
| 1 환경·규모 | ✅ | 수집 도중 사용자가 `[update] : 6000` 을 커밋해 HEAD 가 바뀌었고, **단계 1 부터 재측정**했다 |
| 2 모듈 경계 3종 | ✅ | Q1 답: `.asmdef` 20(사용자 작성분 0) / `.csproj` 135(`.slnx` 등재 23) / 네임스페이스 7(사용자 4) / 폴더 9 |
| 2-1 패키지 노드 | ✅ | `packages-lock.json` 노드 85 · 패키지 간 간선 135. **R1 이 135 전부 버린다** |
| 3 `.csproj` 생성 | **건너뜀** | 작업 트리에 이미 `.csproj` 135개 · `Library/ScriptAssemblies/*.dll` 147개가 있다. Unity 배치 모드 미실행 |
| 4 Roslyn 최소 시험 | ✅ | **모드 C**(Unity 참조 395개만) 컴파일 오류 **0건** / 타입 해석 실패 **0건** |
| 5 Unity 고유 관찰 | ✅ | 정규식 계수가 양방향으로 틀린다는 것이 실측됨 → 단계 5-1 이 추가된 계기 |
| 5-1 Roslyn 질의 | ✅ | 호출식 1,295건 전수, 서로 다른 `(수신타입.메서드)` 507종 |
| 6 관찰 보고서 | ✅ | A~I 채움 + G-1 추가 |

### 핵심 질문 셋의 답

| # | 답 |
|---|---|
| **Q1** 모듈 경계 | **`.asmdef` 는 쓸 수 없다.** 사용자 코드 114개 중 **112개(98.2%)가 `Assembly-CSharp` 하나**에 들어가고 **사용자 코드 사이 모듈 간선이 0개**다. **2026-08-27 사용자 확정 — 폴더 트리 9개**(`Controller` 31 · `UIs` 24 · `Data` 20 · `Utils` 10 · `Interface` 8 · `Managers` 7 · …). 네임스페이스(4)는 기각 |
| **Q2** `file:line` | **성립한다.** 노드·간선 모두 위치가 붙고 표본 10 + 간선 4 전부 일치. 단 **참조 집합을 섞으면 안 된다**(모드 A 오류 1,055 / B 7,780 / C 0) |

> ⚠ **2026-08-27 C-11 → C-13 으로 번복. 아래 C-11 서술은 무효다.**
>
> **C-13 (최종): L3 판정 대상 = 노드 + 소유 간선.** C# 은 `IFieldSymbol.Locations` 로
> `assoc` 간선 전량에 위치가 붙으므로 **C++ 보다 L3 대상이 넓다** — C++ 은 소유 간선
> 205/205 에만 붙고 `dependency`·`extension` 에는 없다. **이 비대칭은 숨기지 않고 적는다.**
>
> <details><summary>(무효가 된 C-11 시점 서술)</summary>
>
> ⚠ **2026-08-27 C-11 — Q2 의 답은 유효하지만 쓰임이 바뀌었다.**
> 인용 검증 L3 의 **판정 기준이 노드로 내려갔다.** C++ 쪽 도구(clang-uml)가 간선 411건 전량에
> 위치를 주지 않아 언어 간 기준이 갈리기 때문이다(Track C §7 설계 근거 1).
>
> **C# 쪽이 하던 일은 그대로 한다** — Roslyn 은 `IFieldSymbol.Locations` 로 필드 선언 줄을
> 정확히 주므로 `edges[].file`/`line` 을 **계속 채운다.** 필드도 스키마에 남는다.
> 다만 **검증기는 그 값을 판정에 쓰지 않는다.** C# 만 간선까지 검증하면 검증 기준이 언어에 따라
> 달라지기 때문이다. **이 저장소가 스키마보다 정확한 정보를 갖는 쪽이라는 사실은 기록해 둔다.**
>
> </details>
| **Q3** 간선 종류 | **3종만 나온다** — `inheritance` 64 · `realization` 70 · `association` 285. `composition`/`aggregation` 은 **도구를 바꿔도 안 나온다**(C# 문법에 소유/참조 구분이 없다). `dependency` 는 못 내는 게 아니라 **이번에 안 뽑았다** |

### 산출물

`samples/csharp-unity/` 에 `OBSERVATION.md` · `shapes/`(symbol · relation 3종 + `_header` · asmdef · prefab ·
packages-lock-entry) · `external-nodes.tsv` · `counts.tsv` 전량 있다.

### 규약 이탈 1건 — 밝혀 둔다

probe 의 `Program.cs` 가 **152줄**로 §3 단계 4 의 "수십 줄" 상한을 넘었다. 세 모드 비교(A/B/C),
중첩 타입 순회, enum 멤버 분리, 구문 수준 전체 계수, `MonoBehaviour` 전이 상속 판정을 넣다가 늘었다.
🔵 다만 스키마·직렬화·플러그인 구조·CLI 는 **하나도 만들지 않았다** — 출력은 전부 탭 구분 텍스트다.

---

## 1. 실측 — Unity 는 C# 프로젝트가 아니라 별개의 문제다

🔵 아래는 **`$CSHARP_REPO`(Unity 6, HEAD `bf54917`)** 에서
2026-08-27 에 실제로 측정한 값이다. 다른 사본에서 실행하면 **전부 다시 재야 한다**(머리말 표 참조).

| 항목 | 값 |
|---|---|
| Unity 버전 | ~~2022.3.30f1~~ → 🔵 **6000.0.71f1** (`ProjectSettings/ProjectVersion.txt`) |
| `dotnet` SDK | 9.0.200 (설치된 SDK 4종 — 6.0.420 · 8.0.202 · 9.0.100 · 9.0.200) |
| Roslyn | `Microsoft.CodeAnalysis.CSharp` **5.9.0** (NuGet, 이 작업의 유일한 신규 설치) |
| 추적 중인 `.cs` | 1,713개 |
| **그중 사용자 코드** | **114개 (6.7%)** — `Assets/@Scripts` 106 + `Assets/@Editors` 8 |
| 서드파티 | 1,599개 — `Feel` 866 · `GPM` 653 · `Plugins` 69 · `PlayerPrefsEditor` 11 |
| `.asmdef` | 20개 |
| **`.asmdef` 중 사용자가 작성한 코드에 붙은 것** | **0개.** 🔵 단 `Assets/@` 아래에 **1개 있다** — `Assets/@Editors/SceneHelper/ToolbarExtender/ToolbarExtender.Editor.asmdef`. **벤더링된 서드파티 도구**의 것이다 |
| 추적 중인 `.unity` (씬) | 66개 |
| 추적 중인 `.prefab` | 266개 |
| 추적 중인 `.asset` | ~~211개~~ → 🔵 **213개** |
| 추적 중인 `.csproj` / `.sln` | **0개** — `.gitignore:35` 의 `*.csproj` 로 제외돼 있다 |
| 추적 중인 **`.slnx`** | 🔵 **1개 — 추적된다.** `.gitignore` 의 `*.sln` 이 `.slnx` 를 **걸러내지 못한다** |
| 작업 트리의 `.csproj` | 🔵 **135개 실재** (git 에는 없고 Unity 가 만든 것) |
| `Library/ScriptAssemblies/*.dll` | 🔵 **147개 실재** |
| `Library/` | `.gitignore:5` 로 제외돼 있다 |

### 여기서 나오는 결론 셋 — 전부 C++ 쪽에는 없는 문제다

**(가) 깨끗한 클론에는 Roslyn 이 열 것이 거의 없다 — 단 `.slnx` 는 예외다.**
`.sln` 도 `.csproj` 도 `Library/ScriptAssemblies/*.dll` 도 git 에서 제외돼 있다.
이 파일들은 **Unity 에디터가 생성하는 파생물**이지 소스가 아니기 때문이다.
Track C §11 의 확인 항목 "C# 프로젝트가 실제로 있는지, 솔루션 파일 위치" 는
**"있다가 아니라, 생성해야 있다"** 가 답이다.

> 🔵 **2026-08-27 정정 — 이 결론이 절반 뒤집혔다.** 사용자가 Unity 6 로 올리면서
> **`StickRushGame.slnx` 가 추적되기 시작했다.** `.gitignore` 의 `*.sln` 패턴이
> `.slnx` 를 걸러내지 못한다. 또 이 작업 트리에는 `.csproj` 135개와
> `Library/ScriptAssemblies/*.dll` 147개가 **이미 실재**해서, 수집 세션은
> **단계 3(Unity 배치 모드)을 실행하지 않고 건너뛰었다.**
>
> ⚠ 그러나 **깨끗한 클론에서는 여전히 성립한다** — `.slnx` 하나만 오고 그것이 가리키는
> `.csproj` 는 오지 않는다. `.slnx` 는 프로젝트 목록일 뿐 컴파일 정보가 없다.
> **단계 3 을 삭제하지 말 것.**

**(나) 사용자 코드의 모듈 경계가 `.asmdef` 에 없다.**
`.asmdef`(Assembly Definition)는 Unity 에서 CMake 타겟에 해당하는 모듈 경계다. 그런데
20개 전부가 서드파티 플러그인에 붙어 있고, **사용자 코드 114개 파일에는 하나도 없다.**
`.asmdef` 가 없는 코드는 전부 기본 어셈블리 `Assembly-CSharp` 하나로 뭉친다.

> 즉 `codegraph.json` 의 `modules[]` 를 `.asmdef` 로 채우면 **정작 보고 싶은 사용자 코드가
> 모듈 하나로 뭉개진다.** 이것이 C# 쪽의 가장 큰 설계 질문이고, 추측이 아니라 측정으로 답해야 한다.

**(다) 서드파티가 93%다.** 필터링은 선택이 아니라 이 언어 쪽의 1순위 제약이다.
C++ 쪽은 `extern/` 서브모듈 2개만 빼면 됐지만, 여기서는 제외 규칙이 틀리면 그래프 전체가 남의 코드가 된다.

---

## 2. 이 작업이 답해야 할 핵심 질문 셋

관찰 보고서의 어느 절에 답이 들어가는지를 함께 적는다.

| # | 질문 | 답이 들어갈 절 |
|---|---|---|
| Q1 | **사용자 코드의 모듈 경계를 무엇으로 잡을 것인가** — `.asmdef` / 폴더 트리 / 네임스페이스 중 무엇이 실제로 의미 있는 경계인가 | C-3, E |
| Q2 | **Roslyn 이 `file:line` 을 실제로 주는가, 그 위치가 맞는가** — 인용 검증 L3 의 성립 조건 | F |
| Q3 | **간선 8종 중 C# / Unity 에서 실제로 나오는 것은 몇 종인가** | D |

Q3 에 대해 Track C §6 함정 5 가 이미 예측을 내놨다. **확인하되 그대로 믿지 말 것.**

> "C# 으로 가면 두 가지를 잃는다. (a) 합성/집약 구분 — 언어에서 소유와 참조가 구분되지 않아
> 도구를 바꿔도 안 된다. (b) 인용 검증 L3 … **C# 보고서는 5종 간선이 아니라 3종(상속·실현·연관)으로
> 그려야 한다.**"

---

## 2-2. 외부 의존 처리 — Track C §2-1 (C-9) 의 C# 적용

> **2026-08-27 사용자 확정.** 상위 규칙은 `HANDOFF-codebase-wiki.md` §2-1 에 있다.
> 여기에는 **C# / Unity 에서 그 규칙이 무엇을 뜻하는지**만 적는다. 규칙 자체를 바꾸지 말 것.

### 규칙 넷 (재게)

| # | 규칙 |
|---|---|
| **R1** | 전이 확장을 하지 않는다. 사용자 코드가 **직접 닿는** 외부 모듈만 노드가 된다 |
| **R2** | 외부 모듈 하나 = 노드 하나. 입도는 **패키지 이름** |
| **R3** | 모든 외부 노드를 `__external__` 그룹 하나에 모아 **외딴 섬**으로 둔다 |
| **R4** | 간선은 **사용자 코드 → 외부 단방향만**. 외부→외부, 외부→사용자는 만들지 않는다 |


### 규칙 둘 추가 (Track C §2-1 "규칙 둘 추가" 와 동일)

| # | 규칙 |
|---|---|
| **R5** | **컨테이너·스마트포인터 투과.** `List<T>` `Dictionary<K,V>` `Nullable<T>` `T[]` 등은 노드로 만들지 않고 `A -> Wrapper<T>` + `Wrapper<T> -> T` 를 `A -> T` 로 접는다 |
| **R6** | 섬으로 들어가는 간선에 `constraint=false`. 섬은 시각 구분 |
| **R7** | **원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.** `string` `int` `float` `bool` 등과 `object`/`System.Enum`/`System.ValueType` 은 대상이 `(BCL) netstandard` 라도 간선을 만들지 않는다 |

**적용 순서 고정: R5 -> R7 -> R2 -> R1 -> R4 -> R3 -> R6.**

🔵 이 저장소 실측 — `(BCL) netstandard` 접촉이 **R7 전 274건 / R7 후 9건**:

```
(a) R5 적용 후 전체                          274
(b) 암묵적 기반(object/Enum/ValueType) 제외   145
(c) R7 = 원시 타입까지 제외                     9   <- 채택 (2026-08-27 사용자 확정)

남는 9건: System.Action 3 / System.Type 2 / System.Exception 2
          / IReadOnlyDictionary 1 / System.Random 1
```

⚠ **R7 은 노드를 지우지 않는다.** 9건이 남으므로 `(BCL) netstandard` 는 여전히 외부 노드다.
나머지 11개 외부 노드의 접촉 합이 72건이므로, R7 없이는 표준 라이브러리 하나가 전체의 4배가 된다.

> ⚠ **이 문서에 "적용 순서 고정" 이 두 번 적혀 있었고 내용이 달랐다**(R7 포함본과 미포함본).
> R7 이 나중에 추가된 규칙이므로 **R7 포함본(위)이 정본**이고, 미포함본은 2026-08-27 에 삭제했다.
> 짝 문서인 `HANDOFF-cpp-pattern-collection.md` §2-3 이 같은 정정을 이미 했다.

⚠ **C# 은 §6 함정 5 대로 `composition`/`aggregation` 구분이 없으므로, R5 가 접은 뒤의
`kind` 는 전부 `association` 이다.** C++ 쪽 실측 근거는 Track C §2-1.

### 이 저장소에서 그 결과가 어떤 모양인가 — 실측 🔵

참조로 넘긴 DLL 은 **395개**인데, 사용자 코드 112개 파일이 상속·인터페이스 실현·필드 타입으로
**실제로 닿는 어셈블리는 13개**뿐이다. 그것을 패키지 이름으로 접으면 **12개 노드**가 된다:

```
  310  (BCL) netstandard
   34  (엔진) UnityEngine.CoreModule
   12  com.unity.ugui
   12  com.cathei.bakingsheet        <- BakingSheet(11) + BakingSheet.Google(1) 이 접힌 것
    4  (엔진 에디터) UnityEditor
    3  com.unity.modules.ui
    2  (벤더링) DOTween
    1  com.unity.inputsystem
    1  com.unity.addressables
    1  com.unity.modules.audio
    1  com.unity.modules.animation
    1  com.unity.modules.imgui
```

**반면 전이를 펼치면** `packages-lock.json` 기준 노드 85개(depth 0=57, 1=19, 2=9)에
패키지 간 간선 135개가 붙는다. **R1 이 그 135개를 전부 버린다** — 사용자 코드가 닿지 않기 때문이다.

### 노드 이름을 무엇으로 쓰나

| 외부의 종류 | 노드 이름 | 예 |
|---|---|---|
| `Packages/manifest.json` 의 패키지 | 패키지 id 그대로 | `com.cathei.bakingsheet`, `com.unity.ugui` |
| 엔진 내장 모듈 (`com.unity.modules.*` 에 있는 것) | 패키지 id | `com.unity.modules.ui` |
| 엔진 어셈블리인데 패키지가 없는 것 | `(엔진) <어셈블리>` | `(엔진) UnityEngine.CoreModule` |
| 에디터 어셈블리 | `(엔진 에디터) UnityEditor` | — |
| 표준 라이브러리 | `(BCL) netstandard` | — |
| `Assets/` 아래 벤더링된 서드파티 | `(벤더링) <이름>` | `(벤더링) DOTween` |

### 어셈블리 → 패키지 매핑을 어떻게 얻나

`Library/PackageCache/<패키지>@<해시>/**/*.asmdef` 의 `name` 필드가 어셈블리 이름이고,
경로의 `@` 앞부분이 패키지 이름이다. 이 둘로 사전을 만든다. 실측 축약비:

```
PackageCache 안 .asmdef(어셈블리) 259개  ->  패키지 46개
.slnx 밖 csproj              112개  ->  패키지 41개 (매핑 106, 실패 6)
```

매핑 실패 6개는 전부 `BakingSheet.Samples*` 로, `PackageCache` 안에 대응하는 `.asmdef` 이 없다.
**그런 것은 `(벤더링)` 이 아니라 상위 패키지(`com.cathei.bakingsheet`)로 접는다.**

### 판별에 쓸 재료 — 이미 수집 절차 안에 있다

- `Packages/manifest.json` · `Packages/packages-lock.json` — **git 에 추적된다.** `Library/` 와 달리
  제외되지 않으므로 깨끗한 클론에도 있다. 아래 단계 2-1 에서 뜬다.
- Roslyn 심볼의 `ITypeSymbol.ContainingAssembly.Name` — 어느 어셈블리에 사는 타입인지를 준다.
  경로 규칙보다 정확하다.

⚠ **경로만으로 판별하면 새어 나간다.** 실측 증거 둘: `Assets/@Editors/` 안에 서드파티가 있고
(`ToolbarExtender` 2파일), `Assembly-CSharp` 어셈블리 안에도 서드파티가 있다
(`Assets/GPM/Shader/` 9파일). **경로 규칙과 `ContainingAssembly` 를 둘 다 써서 교차 확인한다.**

---

## 3. 수집 절차

각 단계에 **정지 조건**이 있다. 막히면 다음으로 가지 말고 오류 원문 그대로 관찰 보고서 H절에 적는다.

### 준비

```bash
cd <Unity 저장소>
mkdir -p out/codegraph-raw
printf 'out/codegraph-raw/\n' >> .gitignore
git rev-parse --short HEAD > out/codegraph-raw/00-commit.txt
```

### 단계 1 — 환경과 규모 실측 (설치 0, 도구 0)

```bash
{
  cat ProjectSettings/ProjectVersion.txt
  dotnet --version
  echo "--- cs by top dir under Assets ---"
  git ls-files 'Assets/*.cs' | awk -F/ '{print $2}' | sort | uniq -c | sort -rn
  echo "--- counts ---"
  echo "asmdef: $(git ls-files '*.asmdef' | wc -l)"
  echo "scene:  $(git ls-files '*.unity'  | wc -l)"
  echo "prefab: $(git ls-files '*.prefab' | wc -l)"
  echo "asset:  $(git ls-files '*.asset'  | wc -l)"
  echo "csproj tracked: $(git ls-files '*.csproj' | wc -l)"
} > out/codegraph-raw/00-env.txt 2>&1
```

**정지 조건:** 파일에 실제 수치가 있으면 통과. 관찰 보고서 A·E절에 옮긴다.

**여기서 서드파티 제외 규칙을 정한다.** 위 `uniq -c` 출력을 보고 사용자 코드 디렉토리를 고른 뒤,
**그 경로 패턴을 관찰 보고서 E절에 그대로 적는다.** 이후 모든 계량은 제외 전후 두 수를 함께 낸다.

### 단계 2 — 모듈 경계 후보 3종을 전부 측정한다 (Q1)

`.asmdef` 는 JSON 이다. **도구가 필요 없다.**

```bash
# (가) asmdef 경계와 그 참조 관계
for f in $(git ls-files '*.asmdef'); do
  echo "=== $f"; cat "$f"
done > out/codegraph-raw/01-asmdef.txt

# (나) 폴더 트리 경계 — 사용자 코드 디렉토리의 2단계까지
git ls-files 'Assets/@Scripts/*.cs' | awk -F/ '{print $3}' | sort | uniq -c | sort -rn \
  > out/codegraph-raw/01-folders.txt

# (다) 네임스페이스 경계
git ls-files 'Assets/@Scripts/*.cs' 'Assets/@Editors/*.cs' \
  | xargs grep -h '^ *namespace ' | sort | uniq -c | sort -rn \
  > out/codegraph-raw/01-namespaces.txt
```

`.asmdef` 의 `references` 배열이 어셈블리 간 의존 방향을 준다. 이것이 C++ 의
`cmake --graphviz` 에 해당하는 산출물이다.

**정지 조건:** 세 파일이 모두 비어 있지 않으면 통과. **셋 중 어느 것이 의미 있는 경계인지를
관찰 보고서 C-3 절에 근거와 함께 적는다.** 혼자 정하지 말고 세 후보의 수치를 나란히 제시한다.

⚠ 사용자 코드에 `.asmdef` 가 하나도 없다는 것은 **결함이 아니라 관찰**이다. 새로 만들지 말 것.
`.asmdef` 를 추가하면 Unity 가 어셈블리를 다시 나누고 컴파일 순서가 바뀌어 사용자 프로젝트가 깨질 수 있다.

### 단계 2-1 — 외부 의존을 패키지 노드로 접는다 (C-9 / §2-2)

**`Packages/manifest.json` 과 `Packages/packages-lock.json` 은 git 에 추적된다.** `Library/` 와
달리 제외되지 않으므로, `.csproj` 도 `Library/` 도 없는 깨끗한 클론에서 **서드파티 의존 그래프를
얻을 수 있는 유일한 파일**이다. 도구가 필요 없다 — JSON 이다.

```bash
cp Packages/manifest.json      out/codegraph-raw/06-manifest.json
cp Packages/packages-lock.json out/codegraph-raw/06-packages-lock.json

python3 - <<'EOF' > out/codegraph-raw/06-packages.txt
import json, glob, collections
lock = json.load(open('Packages/packages-lock.json'))['dependencies']
man  = json.load(open('Packages/manifest.json'))
print(f"manifest 직접 의존: {len(man['dependencies'])}")
print(f"lock 패키지 노드:   {len(lock)}")
print("  depth 별:", dict(sorted(collections.Counter(v['depth'] for v in lock.values()).items())))
print("  source 별:", dict(collections.Counter(v['source'] for v in lock.values())))
print(f"패키지 간 간선:     {sum(len(v.get('dependencies', {})) for v in lock.values())}  <- R1 이 전부 버린다")
print()
print("# 어셈블리 -> 패키지 매핑 사전 (노드 접기의 근거)")
asm2pkg = {}
for a in glob.glob('Library/PackageCache/*/**/*.asmdef', recursive=True):
    pkg = a.split('/')[2].split('@')[0]
    try: asm2pkg[json.load(open(a, encoding='utf-8-sig'))['name']] = pkg
    except Exception: pass
print(f"어셈블리 {len(asm2pkg)}개 -> 패키지 {len(set(asm2pkg.values()))}개")
for k, v in sorted(asm2pkg.items()): print(f"  {k}\t{v}")
EOF
```

**정지 조건:** `06-packages.txt` 에 패키지 수와 어셈블리→패키지 사전이 있으면 통과.

⚠ **여기서 나온 패키지 전량이 노드가 되는 것이 아니다.** R1 에 따라 **사용자 코드가 실제로 닿는
것만** 노드가 된다. 무엇이 닿는지는 단계 4 에서 Roslyn 이 알려준다. 이 단계는 **이름 사전을
만드는 것**이 목적이다.

### 단계 3 — `.csproj` 를 생성한다 (Roslyn 의 전제)

git 에 없으므로 만들어야 한다. **작업 트리에 이미 있으면 그것을 쓰고 이 단계를 건너뛴다.**

```bash
ls *.csproj *.sln 2>/dev/null | head
```

없다면 Unity 에디터가 생성해야 한다. 에디터를 GUI 로 열지 말고 배치 모드로 돌린다:

```bash
/Applications/Unity/Hub/Editor/<버전>/Unity.app/Contents/MacOS/Unity \
  -batchmode -quit -nographics \
  -projectPath "$(pwd)" \
  -executeMethod UnityEditor.SyncVS.SyncSolution \
  -logFile out/codegraph-raw/02-unity-sync.log
```

**정지 조건:** `Assembly-CSharp.csproj` 가 생기면 통과.

**막히는 경우가 흔하다.** Unity 에디터가 설치돼 있지 않거나, 버전이 안 맞거나, 라이선스가 없으면
이 단계는 실패한다. **그때는 우회하지 말고 H절에 적고 단계 4로 간다** — 단계 4의 최소 시험은
`.csproj` 없이도 할 수 있다(아래).

생성된 `.csproj` 하나를 골라 원문을 남긴다. `ProjectReference` 와 `Reference` 항목이
모듈 경계의 네 번째 후보다.

```bash
cp Assembly-CSharp.csproj out/codegraph-raw/02-Assembly-CSharp.csproj.txt
```

### 단계 4 — Roslyn 최소 시험 (Q2·Q3) — **수십 줄 넘기지 말 것**

목적은 **덤프 도구를 만드는 것이 아니라 세 가지만 확인하는 것**이다.

1. Roslyn 이 이 코드베이스의 심볼을 실제로 해석하는가
2. `Location.GetLineSpan()` 이 주는 `file:line` 이 실제 파일의 그 줄과 맞는가 (Q2)
3. 어떤 관계 종류가 실제로 나오는가 (Q3)

```bash
dotnet new console -o out/codegraph-raw/probe
cd out/codegraph-raw/probe
dotnet add package Microsoft.CodeAnalysis.CSharp
```

**`Microsoft.Build.Locator` 와 `MSBuildWorkspace` 를 이 단계에서 쓰지 말 것.**
Track C §6 함정 4 가 지적한 대로 Roslyn 은 라이브러리이고 MSBuild 연동은 별개의 난관인데,
Unity 가 만든 `.csproj` 는 대상 프레임워크가 `netstandard2.1` 이라 설치된 dotnet 9 SDK 와
충돌할 수 있다. **최소 시험은 `.csproj` 를 아예 우회한다** — 사용자 코드 `.cs` 파일 목록을 직접 읽어
`CSharpCompilation.Create` 로 컴파일하고 심볼을 훑는다.

참조 어셈블리(`UnityEngine.dll` 등)가 없으면 타입 해석이 부분적으로 실패한다.
**그것 자체가 답이다** — 얼마나 실패하는지를 세어 관찰 보고서에 적는다.
`Library/ScriptAssemblies/` 나 Unity 설치 경로의 관리 DLL 을 참조로 넣으면 얼마나 나아지는지도
함께 측정하면 좋다.

시험이 내야 할 것:

| 출력 | 파일 |
|---|---|
| 심볼 20개의 `이름 / kind / file:line` | `03-symbols.txt` |
| 관계 표본 — 상속·인터페이스 실현·필드 타입 각 1건씩 원문 | `03-relations.txt` |
| 타입 해석 실패 건수와 그 진단 메시지 원문 | `03-diagnostics.txt` |
| **사용자 코드가 실제로 닿는 외부 어셈블리와 접촉 횟수** (C-9 R1) | `07-external-touch.txt` |
| 호출 전수 집계 / 지정 질의 답 (단계 5-1) | `08-invocations.txt` · `08-query-answers.txt` |

**`07-external-touch.txt` 를 내는 법.** 상속(`BaseType`) · 인터페이스 실현(`Interfaces`) ·
필드 타입(`IFieldSymbol.Type`, 제네릭 인자 포함)을 훑으면서 `ContainingAssembly.Name` 을 세면 된다.
자기 컴파일(사용자 코드)에 사는 것은 제외한다. **이것이 R1 의 "직접 닿는" 을 측정으로 정의한 것이다.**

그다음 단계 2-1 의 사전으로 어셈블리를 패키지 이름에 매핑해 `07-external-collapse.txt` 를 낸다.
**접기 전후 두 수를 반드시 함께 적는다** (예: 어셈블리 13개 → 패키지 노드 12개).

**정지 조건:** `03-symbols.txt` 의 `file:line` 표본 10건을 **실제 `.cs` 파일과 육안 대조**해
관찰 보고서 F절 표를 채웠고, `07-external-touch.txt` 에 접촉 어셈블리 목록이 있으면 통과.

### 단계 5 — Unity 고유 관찰 (기록만, 스키마 변경 금지)

정적 분석이 구조적으로 놓치는 것들이다. **세기만 하고 판단하지 않는다.**

```bash
{
  echo "MonoBehaviour 상속:  $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -l ': *MonoBehaviour' | wc -l)"
  echo "ScriptableObject:    $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -l ': *ScriptableObject' | wc -l)"
  echo "SerializeField:      $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -c 'SerializeField' | awk -F: '{s+=$2} END {print s}')"
  echo "GetComponent<:       $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -c 'GetComponent<'  | awk -F: '{s+=$2} END {print s}')"
  echo "Resources.Load:      $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -c 'Resources.Load' | awk -F: '{s+=$2} END {print s}')"
  echo "SendMessage:         $(git ls-files 'Assets/@Scripts/*.cs' | xargs grep -c 'SendMessage'    | awk -F: '{s+=$2} END {print s}')"
} > out/codegraph-raw/04-unity-dynamic.txt 2>&1
```

⚠ **위 수치는 하한이 아니다. 그냥 틀린 수다.** 2026-08-27 실측으로 양방향 오차가 확인됐다.

| 항목 | 정규식 | Roslyn 정확 | 방향 |
|---|---|---|---|
| `MonoBehaviour` 파생 타입 | 5 | **45** | 정규식이 **9배 적게** — 중간 기반 클래스(`UI_Base` 26개 등)를 못 따라간다 |
| `Instantiate(` | 1 | **5** | 적게 |
| `FindObjectOfType` 계열 | 4 | **9** | 적게 |
| `StartCoroutine(` | 5 | **1** | **정규식이 많게** — 5건 중 4건이 주석이다 |

**`StartCoroutine` 이 결정적이다.** 정규식은 주석과 문자열을 세고 Roslyn 은 안 센다.
따라서 정규식 수치는 **하한(lower bound)도 상한도 아니고, 경계가 아예 없는 다른 수**다.
"하한 N개" 라고 적는 것조차 틀렸다.

**그러므로 단계 5 의 정규식 계수는 "정확한 수" 로 쓰지 않는다.** 용도는 하나뿐이다 —
**정적 분석이 놓치는 자리가 어디인지 표시하는 것.** 정확한 수가 필요하면 아래 단계 5-1 로 간다.

각 수치가 뜻하는 것을 관찰 보고서 G절에 적는다.

| 관찰 | 왜 정적 분석이 놓치나 |
|---|---|
| `MonoBehaviour` 생명주기 메서드 (`Awake`/`Start`/`Update`) | 코드 어디서도 호출하지 않는다. 엔진이 리플렉션으로 부른다. **호출 그래프에서 입력 간선 0 인 고아로 보이고 PageRank 중요도가 0에 수렴한다** |
| `[SerializeField]` 필드 | 값을 **에디터에서 프리팹·씬 YAML 에 넣는다.** 코드에는 대입이 없다. 실제로는 소유(composition)에 가까운데 Roslyn 은 타입 참조로만 본다 |
| `GetComponent<T>()` | 런타임 조회. 컴파일 시점 의존이 **약하게만** 잡힌다 |
| `Resources.Load` / Addressables | 문자열 경로로 자산을 찾는다. 간선이 아예 없다 |
| `UnityEvent` 인스펙터 연결 | 호출 관계가 코드가 아니라 씬·프리팹 YAML 에 있다 |

**프리팹 YAML 표본 1건을 반드시 남긴다.** 실제 배선이 어디에 어떤 형태로 있는지를 보여주는 것이
이 절의 핵심이다. GUID 참조 형태를 원문 그대로 붙인다.

```bash
git ls-files 'Assets/@*/*.prefab' | head -1 | xargs head -60 > out/codegraph-raw/04-prefab-sample.yaml
```

⚠ **여기서 "Unity 전용 간선 종류를 추가하자" 는 제안을 하지 말 것.** `kind` 는 8종 고정이고
(그중 `instantiation`·`friendship` 은 C++ 전용이라 C# 에서는 항상 0건이다),
Track C §7 이 `nodes[].members` · `calls[]` 를 "나중에 붙일 자리 — 지금 만들지 말 것" 으로
명시했다. **횟수와 함께 기록만 하고 사용자에게 보고한다.**

### 단계 5-1 — Roslyn 질의 파이프라인 (정규식을 대체한다)

> **2026-08-27 사용자 지시로 추가.** 단계 5 의 정규식 계수가 하한조차 아니라는 것이
> 실측으로 밝혀졌기 때문이다. 정확한 수가 필요한 항목은 전부 여기서 답한다.

**설계 원칙 — 어휘 목록(API DB)을 만들지 않는다.** 무엇을 grep 할지 미리 정하는 순간
그 목록을 누가 정하느냐는 판단 문제가 정적 계층으로 되돌아오고, Unity 버전마다 드리프트한다.
Track C §6 함정 6(거울 함정)이 금지하는 방향이다. 대신 **두 단**으로 짠다.

**(A) 전수 열거 — 목록 없이 센다.**
단계 4 의 모드 C 컴파일(오류 0건)에서 `SemanticModel` 을 얻고, 모든 `InvocationExpressionSyntax`
를 `IMethodSymbol` 로 해석해 `수신타입.메서드` 로 집계한다. **미리 정한 어휘가 없다** —
코드가 실제로 부른 것만 나온다.

```
# 08-invocations.txt 머리 (StickRushGame 실측)
# 호출식 1295건 중 심볼 해석 성공 1288, 실패 7
# 서로 다른 (수신타입.메서드) 507종
64	Gamerecipe.StickRush.UI_Base.Get	Probe
51	Gamerecipe.StickRush.GameLogger.LogDebug	Probe
31	UnityEngine.Component.GetComponent	UnityEngine.CoreModule
19	UnityEngine.Events.UnityEvent.AddListener	UnityEngine.CoreModule
```

대상 어셈블리를 함께 낸다. `Probe` 는 사용자 코드 자신이고 그 외는 외부다 — C-9 의 재료와 같다.

**(B) 지정 질의 — (A) 위에서 고른다.**
단계 5 체크리스트 항목에만 정확한 수를 답하고, **정규식 수치와 나란히 적는다.**
질의 목록은 **이 핸드오프가 소유한다.** 코드 안에서 늘리지 말 것.

```
# 08-query-answers.txt (StickRushGame 실측, 발췌)
# 질의                              Roslyn 정확  정규식  근거 file:line
UnityEvent.AddListener                    19      미측정  UI_ButtonAnimation.cs:32 ; ...
GetComponent 계열                         40          39  UI_StageStateView.cs:58 ; ...
Instantiate                                5           1  UI_FoodStickView.cs:43 ; ...
StartCoroutine/StopCoroutine               1           5  CoroutineRunner.cs:22
MonoBehaviour.Invoke(문자열)               4  48 과 섞임  UI_CustomerSpaceView.cs:72 ; ...
그 외 .Invoke() (델리게이트/UnityEvent)   43  48 과 섞임  UI_RerollButton.cs:46 ; ...
```

**정규식이 못 하던 분해가 여기서 된다.** `Invoke(` 48건은 정규식으로는
`MonoBehaviour.Invoke(string, float)`(정적 분석이 놓치는 것)와 델리게이트·`UnityEvent` 의
`Invoke()`(놓치지 않는 것)를 구분할 수 없었다. Roslyn 은 수신 타입으로 4 / 43 으로 가른다.

**근거 `file:line` 을 함께 낸다** — 질의당 최대 3건. 이것이 없으면 인용 검증 L3 가 안 된다.

**정지 조건:** `08-invocations.txt` 에 (A) 전수 집계가 있고, `08-query-answers.txt` 의 모든
질의에 Roslyn 수치와 근거 위치가 채워졌으면 통과.

⚠ **(A) 를 반드시 남긴다.** (B) 의 질의 목록이 무엇을 빠뜨렸는지는 (A) 를 봐야 드러난다.
목록이 스스로를 검증하지 못하게 하는 장치다.

⚠ **`new` 표현식도 함께 집계해 두되 지금은 쓰지 않는다.** `dependency` 간선의 재료지만
Track C §7 이 `calls[]` 를 "나중에 붙일 자리" 로 못박았다. **횟수만 기록하고 간선으로 만들지 말 것.**

---

### 단계 6 — 관찰 보고서 작성

```bash
mkdir -p $REPO_ROOT/docs/handoffs/samples/csharp-unity
cp $REPO_ROOT/docs/handoffs/templates/OBSERVATION-template.md \
   $REPO_ROOT/docs/handoffs/samples/csharp-unity/OBSERVATION.md
```

**절 번호와 제목을 바꾸지 않는다** — C++ 쪽 보고서와 나란히 놓고 읽어야 한다.

---

## 4. 무엇을 복사해 오고 무엇을 남기나

```
<Unity 저장소>/out/codegraph-raw/          ← gitignore. 원시 산출물 전량. 여기 남긴다
$REPO_ROOT/docs/handoffs/samples/csharp-unity/
  OBSERVATION.md                            ← 양식 A~I 를 채운 것
  shapes/symbol.txt                          ← 심볼 레코드 원문 1건
  shapes/relation-<kind>.txt                 ← 관계 레코드 원문, 종류마다 1건씩
  shapes/asmdef.json                         ← .asmdef 원문 1건
  shapes/prefab.yaml                         ← 프리팹 YAML 발췌 (GUID 참조가 보이는 부분)
  shapes/packages-lock-entry.json            ← packages-lock.json 레코드 원문 1건
  external-nodes.tsv                         ← C-9 로 접은 외부 노드 목록 (이름 / 접촉횟수 / 접힌 어셈블리)
  counts.tsv                                 ← E절 계량표를 탭 구분으로 다시 낸 것
```

**표본 파일 하나가 200줄을 넘으면 자르고 잘랐다고 명시한다.**

---

## 5. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만 인정한다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.**
- 커밋이 필요하면 `personal-commit-messages` 스킬을 따른다 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).
- **사용자 프로젝트를 바꾸지 않는다.** `.asmdef` 신설 금지, 씬·프리팹 저장 금지,
  `.gitignore` 에 한 줄 추가하는 것 외에 추적 파일을 건드리지 않는다.
- **거울 함정을 경계하라.** 이 작업은 파일을 모아 표로 정리하는 일이다. 수집 스크립트에
  플러그인 구조나 추상 인터페이스가 나오면 그 자체가 Track C 가 잡으려는 실패다.

---

## ✅ 실행 완료 (2026-08-27) — 오케스트레이터 보고용

**산출물** — `samples/csharp-unity/` (`OBSERVATION.md` A~I 전 절 · `shapes/` 6개 · `counts.tsv`
· `external-nodes.tsv`) + 대상 저장소 `out/codegraph-raw/` 원시 산출물 23개.

### §0 완료 조건 셋 — 전부 충족

| 조건 | 결과 |
|---|---|
| `out/codegraph-raw/` 에 원시 산출물 | ✅ 23개 파일 |
| `samples/csharp-unity/` 에 보고서·표본 | ✅ |
| **§2 핵심 질문 셋에 측정으로 답함** | ✅ 아래 |

- **Q1 (모듈 경계)** — 네 후보를 전부 쟀다. `.asmdef` 는 사용자 코드를 **1개**, `.csproj` 는 **2개**
  경계로만 나누고 **사용자 코드 사이의 모듈 간선이 0개**다. 사용자 코드 114개 중 112개(98.2%)가
  `Assembly-CSharp` 하나에 들어간다. 네임스페이스는 4개, 폴더는 9개로 나뉘고 이 저장소에서는 둘이 거의 겹친다.
- **Q2 (`file:line`)** — **성립한다.** 심볼 10건 + 간선 4건 육안 대조 전부 일치.
  단 전제가 하나 — **참조 집합을 섞으면 안 된다**: 모드 A(BCL만) 오류 1,055 / 모드 B(섞음) **7,780** /
  모드 C(csproj 목록만) **0**. 원인은 SDK 버전이 아니라 `netstandard2.1` 참조에 호스트 BCL 을 더한 것이다.
- **Q3 (간선 종류)** — 6종 중 **3종**(inheritance 64 · realization 70 · association 285).
  `composition`/`aggregation` 은 언어에 근거가 없어 도구를 바꿔도 안 나온다. §6 함정 5 의 예측이 맞았다.

### 핸드오프 §1 실측과 달랐던 것 셋 — 전부 보고서 머리말에 기록

1. **사본 둘의 Unity 버전이 다르다** — `$DEV_ROOT/StickRushGame` 는 2022.3.30f1,
   정본(`UnityProjects/`)은 **6000.0.71f1**. 핸드오프 §1 표는 다른 사본의 값이었다.
2. **수집 도중 HEAD 가 바뀌었다** — 사용자가 `c0a610f [update] : 6000`(1,043 files)을 커밋했다.
   단계 1 부터 재측정했다.
3. **§1 결론 (가)가 뒤집혔다** — `.csproj` 135개와 `StickRushGame.slnx`(추적됨,
   `.gitignore` 의 `*.sln` 이 `.slnx` 를 못 거른다)가 실재해 **단계 3(Unity 배치 모드)을 건너뛰었다.**
   §1 (나)도 정확히는 `.asmdef` 가 **1개 있고 그것이 덮는 파일은 2개**(벤더링된 ToolbarExtender)다.

### 이 세션이 추가로 밝힌 것

- **정규식 계수는 하한조차 아니다** — `MonoBehaviour` 정규식 5 vs Roslyn **45**(중간 기반 클래스
  `UI_Base` 26개 등), `StartCoroutine` 정규식 5 vs Roslyn **1**(5건 중 4건이 주석).
  이 발견으로 §3 단계 5 의 "전부 하한" 경고와 **단계 5-1(Roslyn 질의 파이프라인)** 이 추가됐다.
- **호출 간선 471개가 코드가 아니라 자산에 있다** — `.prefab`/`.unity` 의 `m_MethodName` 472건 중
  471건에 실제 메서드명이 들어 있다.
- **`AddListener` 19건** — C-4 (3)에 근거 없이 쓴 문장을 측정으로 검증하고 보고서에 철회·정정으로 남겼다.

⚠ **미수정** — 이 문서 14행에 오타가 있다: `HANDOFF-cpp-pattern-col각lection.md`.
짝 문서 상호참조가 깨지므로 고쳐야 한다. **에이전트가 건드리지 않고 남겼다.**
