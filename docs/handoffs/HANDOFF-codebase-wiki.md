# HandOff — 코드베이스 이해 보고서 파이프라인 (Track C)

> 작성일: 2026-08-27
> 인계 대상: Claude Code Agent
> **관계 문서**: `HANDOFF-report-system.md` (Track A = D축, Track B = 설계 검토 렌더러). **이 문서는 그것과 별개의 작업 갈래다.** 두 문서를 섞지 말 것.

---

## 0. 목적 — 이것부터 읽어라

> **남의 코드베이스를 빠르게 이해하기 위한 다중 페이지 위키를 자동 생성한다.**
> 성공 지표는 **"이해에 걸린 시간"**이다. 독자는 사용자 본인 한 명이다.

핵심 설계 원칙은 하나다.

> **계산되는 것은 전부 정적 도구로 내리고, 판단되는 것만 LLM에 남긴다.**

이유는 정확도만이 아니다. **정적으로 뽑힌 사실은 사용자가 검토할 필요가 없다.** 검토 시간이 LLM이 쓴 부분에만 집중되고, 그것이 "빠르게 이해"의 실체다. 기능을 추가할지 망설여지면 **"이게 사람의 검토 시간을 줄이는가"**를 물어라.

### 이 작업이 왜 생겼나

이전 인계 문서(`HANDOFF-report-system.md`)가 이 갈래를 **통째로 빠뜨렸다.** 설계 보고서에서 "이 문서의 범위 밖"으로 표시한 것이 인계 시점에 "존재하지 않음"으로 바뀌었다. 실행 세션이 스스로 그 공백을 발견해 보고했고, 그 보고가 이 문서의 출발점이다.

---

## 1. 작업 분류 — 무엇이 어디에 속하나

코드베이스 분석 보고서를 만드는 작업 22개를 분류한 결과다. **16개가 완전 정적, 3개가 규칙만 정하면 정적, LLM에는 4개만 남는다.**

### 완전 정적 (LLM 관여 0)

| # | 작업 | C++ | C# |
|---|---|---|---|
| 1 | 파일 인벤토리 | `git ls-files` | 동일 |
| 2 | 모듈/프로젝트 경계 | CMake 타겟 | `.sln` / `.csproj` |
| 3 | 모듈 의존 방향 | `cmake --graphviz` | `ProjectReference` XML |
| 4 | 클래스·멤버 목록 | clang-uml | Roslyn |
| 5 | 상속·실현 | clang-uml | Roslyn |
| 6 | **합성·집약·의존** | **clang-uml** | **불가 — association 폴백** |
| 7a | **순방향 호출 전개** (이게 무엇을 부르나) | clang-uml `start_from` | Roslyn |
| 7b | **역방향 참조 질의** (누가 이걸 부르나) | **`libclang` 직접** (E5, 전수 1회 순회). clangd 는 폴백 | `SymbolFinder.FindCallersAsync` |
| 8 | 순환 의존 검출 | networkx | 동일 |
| 9 | 중요도 랭킹 | PageRank | 동일 |
| 10 | 변경 hotspot | `git log` 집계 | 동일 |
| 11 | file:line | `source_location` | `Location.GetLineSpan()` |
| 12 | 다이어그램 레이아웃 | Graphviz P4 + A1 | 동일 |
| 13 | 다이어그램 렌더 | `dot -Tsvg` | 동일 |
| 14 | **인용 검증 L3** | codegraph.json 대조 | Roslyn 덤프 대조 |
| 15 | 페이지 조립·검색 | VitePress | 동일 |
| 16 | 링크 무결성 | VitePress dead-link | 동일 |

### 규칙만 사람이 정하면 정적

| # | 작업 | 방법 |
|---|---|---|
| 17 | 진입점 식별 | `main`/`WinMain`/`Program.Main` 패턴 + 예외는 수동 |
| 18 | **아키텍처 경계 위반 판정** | 경계 규칙을 선언하면 기계 판정 |
| 19 | 목차 골격 | 모듈 트리에서 도출 (deep-wiki catalogue가 이미 함) |

⚠ **7번 행은 원래 하나였고, 그것이 틀렸다.** clang-uml 시퀀스와 `SymbolFinder.FindCallersAsync` 를
같은 칸에 넣었으나 **같은 연산이 아니다.** clang-uml 은 `start_from: - function: main(int,const char **)`
처럼 진입점을 시그니처로 미리 적어야 하는 **렌더러**이고, 역방향 질의를 못 한다.
그래서 "누가 이 심볼을 참조하나" 가 grep 으로 떨어졌고, 🔵 실제로 한 번 틀린 결론을 냈다
(`src/fsm` 을 `std::function` grep 으로 판정 → 실제 기제는 `uint64_t` 비트마스크).
역방향은 **`libclang` 직접**이 맡는다(E5) — **전수 역참조가 필요하다는 U2 판정**의 귀결이다.
결정 근거와 번복 이력은 `HANDOFF-clangd-reverse-refs.md` §7.
⚠ **대가**: 🔵 clangd 는 `-resource-dir`·`-isysroot` 를 자동 주입해 함정 1·2 를 통과했으나
(주입 0건, 두 clangd 모두 0 errors), **libclang 직접은 그것을 손으로 넣어야 한다.**
⚠ `DECISION-cpp-symbol-index.md`(scip-clang 선정)는 **번복됐다.** 따르지 말 것.

> 🔵 **2026-08-27 — 17·18 번의 인계 문서가 나왔다.**
> `HANDOFF-cpp-boundary-rules.md` · `HANDOFF-unity-boundary-rules.md`.
> 산출물은 대상 저장소의 `codegraph-rules.toml`(층 · 예외 · 진입점) 하나다.
> C++ 쪽은 재료가 준비됐다 — 🔵 모듈 20 / 의존 49 / **순환 11개, 전부에 `material` 이 들어 있다.**
> C# 쪽은 `roslyn-dump` 가 없어 **층 선언과 진입점까지만** 지금 할 수 있다.

18번이 값이 크다. 지금은 "허용된 누수"를 사람이 눈으로 표시하는데, `allow: render -> gl` 같은 규칙을 선언해두면 **위반 간선이 자동으로 빨강**이 되고, 새 위반이 생기면 검사에서 잡힌다. Graphviz P6의 자동화다.

### LLM에만 남는 것 — 넷

| # | 작업 | 왜 기계가 못 하나 |
|---|---|---|
| 20 | 무엇을 생략할지 | 300개 클래스 중 어느 33개를 그릴지. 랭킹이 후보를 주지만 최종 선택은 판단 |
| 21 | "왜" 서사 | 코드는 "무엇"만 말한다. 의도·역사·트레이드오프는 추론 |
| 22 | 미확인 영역 표시 | 모르는 것을 모른다고 쓰는 것 |
| — | 주장과 근거의 연결 | 사실 테이블의 어느 행이 이 문장을 뒷받침하는지 |

---

## 2. 확정된 결정 (사용자 확정 — 변경 금지)

| ID | 결정 | 근거 |
|---|---|---|
| C-1 | **위키 생성기는 microsoft/skills의 `deep-wiki` 플러그인을 쓴다** | 다중 페이지 VitePress + file:line 인용 + "미확인 영역" 강제를 이미 갖춤 |
| C-2 | **CodeWiki는 도입하지 않는다** | 계층 분해가 의미가 아니라 토큰/물리 크기 기반. 노드 폭발은 다른 방법으로 해결 |
| C-3 | **결합 방식은 "입력 주입"** | 정적 사실을 프롬프트/파일로 넣어 LLM이 그걸 근거로 서술. 다이어그램 교체나 사후 대조는 이번 범위 밖 |
| C-4 | **대상 언어는 C++(1순위) · C#(2순위)** | JS/TS·Python은 명시적으로 폐기 |
| C-5 | **산출물은 다중 페이지 위키** | 단일 HTML 보고서가 아님. Track B와 다른 형식 |
| C-6 | **정규화 스크립트는 Python** | networkx·pydot·lxml 생태계. 렌더러(Node)와는 파일로만 만나므로 언어가 달라도 무방 |
| C-7 | **인터페이스는 `codegraph.json`, 최소 스키마부터** | 노드 + 엣지 + 모듈. 확장은 나중 |
| C-8 | **다이어그램은 deep-wiki의 Mermaid가 아니라 Graphviz P1~P6** | deep-wiki Mermaid는 노드 상한이 없어 중형에서 깨진다 |
| C-9 | **외부 의존은 전이 확장 없이 단일 노드로 접고, 전부 하나의 외딴 섬에 모으고, 간선은 사용자 코드 → 외부 단방향만 그린다** | 2026-08-27 사용자 확정. 실측 근거는 아래 §2-1 |
| C-10 | **간선 `kind` enum 을 8종으로 확장한다** — 기존 6종 + `instantiation` + `friendship`. `schema_version` 을 2 로 올린다 | 2026-08-27 사용자 확정. C++ 실측에서 6종에 자리 없는 문자열이 나왔다(§7 참조) |
| ~~C-11~~ | 🔴 **2026-08-27 C-13 으로 번복됨.** ~~인용 검증 L3 의 판정 기준을 간선이 아니라 노드로 내린다.~~ 간선의 `file`/`line` 은 **선택 필드**로 남기고, 있으면 채우되 **L3 판정에는 쓰지 않는다** | 2026-08-27 사용자 확정. clang-uml 이 간선 411건 전량에 위치를 주지 않는다(§7 설계 근거 1) |
| C-12 | **파이프라인 코드는 전부 `$REPO_ROOT/codegraph/` 에 둔다.** `normalize.py` 도 `roslyn-dump` 도 여기 살고, **대상 저장소 경로는 인자로 받는다** | 2026-08-27 사용자 확정. 사용자 프로젝트(C++·Unity)에는 산출물만 남기고 도구를 심지 않는다 |
| C-13 *(C-16 으로 확장됨)* | **C-11 을 번복한다. 인용 검증 L3 의 판정 대상은 노드 + 소유 간선(`composition`·`aggregation`)이다.** 그 외 간선은 근거가 없으므로 검증기가 **"근거 없음"** 으로 낸다 — 판정은 통과/실패 2값이 아니라 **3값**이다 | 2026-08-27 사용자 확정. C-11 의 근거가 실측으로 뒤집혔다(아래 §7 설계 근거 1) |
| C-14 | **`containment` 는 버린다.** 8종 enum 에 자리가 없고 `dependency` 로 흡수하지 않는다 | 2026-08-27 사용자 확정. 방향이 안쪽→바깥쪽이라 흡수하면 P4 의미축에 역방향 화살표가 생겨 오독을 부른다. 🔵 이 저장소 7건 |
| C-15 | **`modules[].depends_on` 은 클래스 간선에서 유도한다.** `cmake --graphviz` 타겟 층과 조인하지 않는다 | 2026-08-27 사용자 확정. 입도가 다르고(폴더 20 vs 타겟 70), **C# 에는 CMake 대응물이 없어** 두 언어가 같은 방식을 쓸 수 있는 유일한 축이다 |
| C-16 | **C-13 을 확장한다. L3 판정 대상 = 노드 + `file/line` 이 null 이 아닌 간선 전부 + (--detail 시) 살 파일의 멤버·메서드 선언 줄** | 2026-08-27 사용자 확정. 🔵 C# 파일럿에서 간선 위치와 일치하는 인용 26건이 "소유 간선만" 제한으로 근거없음에 떨어졌다. C++ 은 소유 간선만 위치를 가져 실질 불변 |
| C-17 | **큰 모듈의 생략 규칙 — 간선 0(고아) 타입은 본문 서술에서 빼고 "전체 목록" 표에만 남긴다.** 생략하되 숨기지 않는다 | 2026-08-27 사용자 확정. Track C §1 20번(LLM 에만 남는 넷)의 첫 확정. 🔵 Controller 63→38 · UIs 50→24 · Data 53→36 |
| C-18 | **Mermaid 는 전면 치환한다(A안).** `mmdc` 로 사전 렌더하고 구조 다이어그램은 Graphviz SVG 로 교체. VitePress 의 클라이언트 Mermaid 렌더에 맡기지 않는다 | 2026-08-27 사용자 확정. C-8("Graphviz 가 정본")을 완화하지 않고 그대로 집행 |

C-8이 중요하다. deep-wiki에는 **"다이어그램은 외부 SVG를 참조하라"고만 지시**하고, 실제 그림은 clang-uml 필터로 모듈별 작게 잘라 Graphviz로 렌더한다.

---

## 2-1. C-9 상세 — 외부 의존을 다루는 규칙 (사용자 확정, 변경 금지)

**적용 범위: C++ · C# 양쪽 동일하다.** 두 언어의 `codegraph.json` 이 같은 모양이어야
`normalize.py` 가 한 가지 그래프만 다루면 된다.

### 규칙 넷

| # | 규칙 |
|---|---|
| **R1** | **전이 확장을 하지 않는다.** 사용자 코드가 **직접 닿는** 외부 모듈만 노드가 된다. 그 모듈이 다시 의존하는 것(depth ≥ 1)은 **그래프에 넣지 않는다.** |
| **R2** | **외부 모듈 하나 = 노드 하나.** 입도는 **패키지·라이브러리 이름**이다. 한 패키지가 어셈블리나 CMake 타겟을 여럿 만들어도 **접어서 하나로 센다.** |
| **R3** | **모든 외부 노드는 하나의 그룹에 모아 외딴 섬으로 둔다.** 그룹 id 는 `__external__` 로 고정한다. |
| **R4** | **간선은 단방향만 그린다 — 사용자 코드 → 외부.** 외부 → 외부 간선과 외부 → 사용자 간선은 **만들지 않는다.** |

### 규칙 둘 추가 — C++ 실측에서 나온 것 (2026-08-27)

위 R1~R4 는 C# 실측에서 나왔다. C++ 산출물(clang-uml)에 적용해 보니 **R1~R4 만으로는 부족한 지점이 둘** 나왔다. 문구를 고치지 않고 규칙을 덧붙인다.

| # | 규칙 |
|---|---|
| **R5** | **컨테이너·스마트포인터는 투과시킨다.** `std::vector<T>` `std::unique_ptr<T>` `std::shared_ptr<T>` `std::array<T,N>` `std::map<K,V>` `std::optional<T>` 같은 **투명 래퍼는 노드로 만들지 않고**, `A -> Wrapper<T>` 와 `Wrapper<T> -> T` 두 간선을 `A -> T` 하나로 접는다. C# 은 `List<T>` `Dictionary<K,V>` `Nullable<T>` 가 같은 자리다. |
| **R6** | **섬으로 들어가는 간선에 `constraint=false` 를 준다.** P4 의 `rankdir=BT` 의미축이 외부 노드 때문에 뒤틀리는 것을 막는다(§10 A1 규율). 섬은 회색 배경 등으로 시각 구분해 **"여기부터 남의 코드"** 를 한눈에 보이게 한다. |

| **R7** | **원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.** `string` `int` `float` `bool` 등 언어 내장 타입, 그리고 컴파일러가 암묵적으로 붙이는 기반 타입(C# 의 `object`/`System.Enum`/`System.ValueType`, C++ 의 해당물)은 대상이 표준 라이브러리 노드라도 간선을 만들지 않는다. `Foo -> netstandard(왜냐하면 int 필드가 있어서)` 는 그림에서 정보가 0 이다. |

**적용 순서가 고정이다: R5 → R7 → R2 → R1 → R4 → R3 → R6.**

- **R7 을 R2 보다 먼저** — 원시 타입을 먼저 걷어내지 않으면 표준 라이브러리 노드가 접촉 수로 다른 모든 외부 노드를 압도한다. 🔵 C# 실측: `(BCL) netstandard` 접촉이 R7 전 274건 / R7 후 **9건**. 나머지 11개 외부 노드의 접촉 합이 72건이므로, R7 없이는 표준 라이브러리 하나가 전체의 4배가 된다.
- 🔵 C# 실측 내역 — 274건 중 원시 타입 265건(그중 암묵적 기반 `object` 60 · `System.Enum` 62 · `System.ValueType` 7 = 129건), 실질 접촉 9건(`System.Action` 3 · `System.Type` 2 · `System.Exception` 2 · `IReadOnlyDictionary` 1 · `System.Random` 1).
- ⚠ **R7 은 노드를 지우지 않는다.** 위 9건이 남으므로 `(BCL) netstandard` 는 여전히 외부 노드다. 지배적이지 않게 될 뿐이다.

- **R5 를 R2 보다 먼저** — 래퍼를 먼저 걷어내지 않으면 `std::vector<Foo>` 가 통째로 외부 노드에 접혀 `Foo` 와의 관계가 사라진다.
- **R2 를 R1 보다 먼저** — 🔵 순서를 뒤집으면 섬에 **부속 타겟 이름**이 남는다. C++ 저장소에서 `Effekseer` 는 `EffekseerRendererGL` 을 거쳐야만 닿아 depth 1 이다. R1(전이 금지)을 먼저 적용하면 `Effekseer` 가 잘리고 `EffekseerRendererGL` 이 섬에 남는다. R2(패키지 단위 접기)를 먼저 하면 둘이 `Effekseer` 하나로 접혀 depth 0 이 된다.

#### R5 를 빼면 가장 값진 간선이 조용히 사라진다

🔵 C++ 실측 — **사용자 코드끼리의 소유 관계 8건이 오직 래퍼를 2홉으로 거쳐야만 보였다.**

```
전  RenderUnit --aggregation(mesh)--> std::unique_ptr<Mesh> ,  std::unique_ptr<Mesh> --dependency--> Mesh
후  RenderUnit --composition(mesh)--> Mesh
```

R5 없이 R1·R4 를 적용하면 `std::unique_ptr<Mesh>` 가 `std` 노드에 접히고 역방향 간선이 잘려 **`RenderUnit -> Mesh` 가 복구 불가능하게 소멸한다.** 같은 방식으로 사라질 뻔한 것들:

| 사용자 클래스 | 멤버 | 대상 | 래퍼 |
|---|---|---|---|
| `SJH::RenderUnit` | `mesh` | `SJH::Mesh` | `std::unique_ptr` |
| `SJH::Reflect::ComponentDesc` | `Fields` | `SJH::Reflect::FieldDesc` | `std::vector` |
| `SJH::Text::TextRenderer` | `mGlyphs` | `SJH::Scene::Actor` | `std::vector` |
| `SJH::Diagnostics::GLValidate::DiagResult` | `findings` | `...::DiagFinding` | `std::vector` |
| `SJH::MeshData` | `vertices` | `SJH::Vertex` | `std::vector` |
| `SJH::Program::UniformBlock` | `ubo` | `SJH::UniformBuffer` | `std::unique_ptr` |
| `SJH::LightUboUploader` | `mLightBlockUbo` | `SJH::UniformBuffer` | `std::unique_ptr` |
| `SJH::Diagnostics::GLStateFields` | `attribute_layouts` | `...::VertexAttribInfo` | `std::array` |

R5 를 넣으면 사용자끼리 간선이 **147 -> 178** 로 늘고 그중 **27건이 `composition`** 으로 살아난다.

접은 뒤의 `kind` 는 **래퍼가 정한다** — 값·컨테이너·`unique_ptr` = `composition`(수명이 묶인다) / 생포인터·참조·`weak_ptr` = `aggregation`(안 묶인다). **C# 은 §6 함정 5 대로 이 구분이 없으므로 전부 `association` 이다.**

**투명이 아닌 것**: `std::function<...>` `std::string` `std::string_view` `std::chrono::*`. `T` 를 담는 그릇이 아니라 그 자체가 값이므로 R2 로 접힌다.

🔵 **자기참조는 접은 뒤 버린다.** `X -> unique_ptr<X> -> X` 는 접으면 자기 루프가 된다. C++ 저장소에 10건 있었고 전부 `XUPtr` 별칭과 `static Create()` 팩토리의 부산물이라 버려도 무손실이다.

#### C++ 쪽 실측 근거 (GlobalMedia-OpenGL-ComputerGraphics, `bfb72b4`, 2026-08-27)

🔵 이 세션에서 실제로 돌린 명령의 출력이다. 원문은 대상 저장소 `out/codegraph-raw/08-external-collapse-simulation.txt`.

| 측정 | 값 |
|---|---|
| 클래스 층 노드 중 외부 | **101 / 203 = 49.8%** (`std::` 만 83) |
| 모듈 층 노드 중 외부 | **26 / 70 = 37.1%** |
| `vcpkg.json` 선언 포트 12개가 `.dot` 노드로는 | **26개** (`glm` 하나가 `glm::glm` + `glm::glm-header-only` 둘로 갈림) |
| R1(전이 금지)이 지운 depth 1 이상 | `Boost::mp11` `Threads::Threads` `fmt::fmt` `glm::glm-header-only` — `vcpkg.json` 에 이름조차 없는 것들 |

**R5 → R2 → R1 → R4 적용 결과:**

| 층 | 노드 (전 → 후) | 간선 (전 → 후) | 외딴 섬 구성 |
|---|---|---|---|
| 클래스 | 203 → **105** (사용자 102 + 섬 3) | 411 → **302** | `std` `glm` `Effekseer` |
| 모듈 | 70 → **58** (사용자 44 + 섬 14) | 246 → **233** | `glm` `spdlog` `assimp` `box2d` `imgui` `tweeny` `nlohmann_json` `boost-describe` `boost-pfr` `sb7` `glfw3` `Effekseer` `fmod` `macOS SDK` |

클래스 층 섬이 3개뿐인 것은 R1 의 효과다 — `nlohmann-json` 과 `FMOD` 는 사용자 클래스가 직접 참조하지 않고 `std::function` 같은 래퍼를 거쳐서만 닿아 depth 1 이 되어 빠진다.

#### C++ 에서 "사용자 코드" 판별 — 경로로 하면 틀린다

🔵 층마다 기준이 다르다.

| 층 | 판정 |
|---|---|
| 모듈 | 저장소 `CMakeLists.txt` 가 `add_library`/`add_executable` 로 **선언한** 타겟 |
| 클래스 | **네임스페이스**가 프로젝트 루트로 시작 (`SJH::` / `MyApp::`) |

**경로 기준 필터는 실패한다.** `std::` 타입 83건의 `source_location.file` 이 표준 헤더가 아니라 **이 저장소의 첫 사용 지점**(`src/reflect/meta.h:27` 등)을 가리키기 때문이다. 경로로 거르면 이것들이 사용자 코드로 오인된다. C# 쪽에서 관찰된 누수(`Assets/@Editors/` 안의 서드파티)와 같은 계열의 함정이고, **양쪽 다 경로 아닌 축을 하나 더 써서 교차 확인해야 한다.**

⚠ **한 가지 판단이 들어갔다.** C++ 저장소의 `stb_extra` 는 `add_library(stb_extra INTERFACE)` 로 저장소가 직접 선언한 타겟이지만 실질은 vcpkg `stb` 포트의 래퍼다. 위 계량은 이것을 **사용자 코드로 분류**했다("저장소가 선언한 타겟" 기준). 외부로 옮기면 사용자 44 → 43, 섬 14 → 15 가 된다. 💭 60 — 선언 기준이 `normalize.py` 에 더 쓸모 있다고 보지만 확정은 사용자 몫이다.

### 왜 이렇게 정했나 — 실측 근거 (StickRushGame, 2026-08-27)

🔵 이 세션에서 실제로 돌린 명령의 출력이다.

| 측정 | 값 |
|---|---|
| Roslyn 에 참조로 넘긴 DLL | **395개** |
| 그중 사용자 코드(112 파일)가 상속·실현·필드 타입으로 **실제로 닿는** 어셈블리 | **13개** |
| 그 13개를 **패키지 이름으로 접으면** | **12개 노드** |
| `packages-lock.json` 의 패키지 노드 (전이 포함) | 85개 (depth 0 = 57, depth 1 = 19, depth 2 = 9) |
| `packages-lock.json` 의 패키지 간 의존 간선 | 135개 |
| 서드파티 비율 (추적 `.cs` 기준) | 1,599 / 1,713 = **93.3%** |

**전이를 펼치면 그래프의 거의 전부가 남의 코드가 된다.** 반대로 R1~R4 를 적용하면
사용자 코드 214개 노드 옆에 외부 노드 12개가 붙는 형태가 된다.

접히는 실례 — 어셈블리 두 개가 패키지 하나가 된다:

```
BakingSheet           11회 접촉  ┐
BakingSheet.Google     1회 접촉  ┴->  com.cathei.bakingsheet   (노드 1개)
```

### `codegraph.json` 에서의 표현

**외부 노드** — `file`/`line` 이 **없다.** 이 저장소에 소스가 없기 때문이다:

```json
{ "id": "X1", "name": "com.cathei.bakingsheet", "kind": "external",
  "module": "__external__" }
```

**외딴 섬 모듈** — `depends_on` 은 **항상 빈 배열**이다. R4 가 외부→외부를 금지하므로:

```json
{ "id": "__external__", "depends_on": [] }
```

**간선** — `from` 은 반드시 사용자 노드, `to` 는 외부 노드다. **`file`/`line` 은 사용자 쪽
멤버 선언 줄이므로 인용 검증 L3 은 그대로 성립한다** (§8):

```json
{ "from": "C7", "to": "X1", "kind": "association",
  "label": "_foodCells", "file": "Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs", "line": 11 }
```

### 중복 간선을 접는다

한 사용자 클래스가 같은 외부 모듈을 여러 번 참조하는 일이 흔하다. 실측에서
`netstandard` 는 **310회** 접촉된다. 310개 간선을 그대로 그리면 그림이 못 쓰게 된다.

**같은 `(from, to, kind)` 쌍은 하나로 접는다.** 남길 `file`/`line` 은 **첫 출현**의 것으로 한다.

> ⚠ **이 접기는 L3 의 근거를 하나만 남긴다.** 접힌 나머지 접촉 지점의 `file:line` 은 버려진다.
> 지금은 그림이 읽히는 쪽을 택한 것이고, 근거를 전부 보존해야 할 일이 생기면
> `edges[].occurrences` 같은 필드를 **나중에 추가**한다(§7 확장 규율: 필드는 추가만).

### 무엇이 "외부" 인가 — 언어별 판별

| 언어 | 외부로 치는 것 | 노드 이름으로 쓸 것 |
|---|---|---|
| C# / Unity | `Packages/manifest.json` 의 패키지, `Library/PackageCache/` 의 패키지, 엔진 어셈블리, `Assets/` 아래 벤더링된 서드파티 | 패키지 이름 (`com.cathei.bakingsheet`). 패키지가 없는 것은 그룹 라벨 (`(BCL) netstandard`, `(엔진) UnityEngine.CoreModule`, `(벤더링) DOTween`) |
| C++ | `extern/` 서브모듈, 시스템·vcpkg 라이브러리 | 서브모듈·라이브러리 이름 (`Effekseer`, `sb7code`). 그 안의 CMake 타겟이 여럿이어도 접는다 |

⚠ **"사용자 코드" 의 판별은 언어별 핸드오프의 E절 제외 규칙을 따른다.** 경로만으로는
새어 나간다는 것이 실측으로 확인됐다 — C# 쪽에서 `Assets/@Editors/` 안에 서드파티가 있었고
(`ToolbarExtender` 2파일), `Assembly-CSharp` 어셈블리 안에도 서드파티가 있었다
(`Assets/GPM/Shader/` 9파일). **경로 규칙과 어셈블리·타겟 판별을 둘 다 써서 교차 확인한다.**

---

## 3. 파이프라인

```
[정적 계층 — 검토 불필요]

C++ ─ clang-uml ──────────── .json ─┐
    ─ cmake --graphviz ────── .dot ─┤
    ─ Doxygen (빌드 실패 시) ─ .xml ─┤
C#  ─ Roslyn 덤프 도구 ────── .json ─┤──→ normalize.py
    ─ csproj 파싱 ─────────── .xml ─┤
공통 ─ git log ────────────── .json ─┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              facts/*.md          ranking.json        diagrams/*.svg
            (사실 테이블)      (중요도 + hotspot)    (Graphviz P1~P6)
                    │                   │                   │
                    └─── 입력 주입 ─────┘                   │
                              │                             │
[LLM 계층 — 여기만 검토]      ▼                             │
                    microsoft deep-wiki                     │
                    · 무엇을 생략할지                        │
                    · "왜" 서사                              │
                    · 미확인 영역 표시                       │
                              │ .md                         │
                              ▼                             ▼
[검증 계층 — 기계]      검증·가공 스크립트 ←─────────────────┘
                    · Mermaid 블록을 SVG 참조로 치환
                    · 인용 검증 L1 / L2 / L3
                    · 경계 규칙 자동 판정
                    · dead-link
                              │
                              ▼
                    VitePress 다중 페이지 위키
```

`.svg`만 LLM을 우회한다. 그림은 프롬프트에 못 넣으므로 deep-wiki를 건너뛰어 검증 단계로 직행하고, LLM은 "참조하라"는 지시만 받는다. 이것이 Mermaid 노드 폭발을 피하는 경로다.

---

## 4. 사용자 개발 환경 (전제)

기존 프로젝트 구조를 그대로 따른다.

```
build-mac/     기존 — macOS 개발용 (clang++). 건드리지 말 것
build-win/     기존 — mingw-w64 크로스빌드. 건드리지 말 것
build-cc/      신규 — Ninja, compile_commands.json 전용
```

- macOS: Ninja / Makefile / Xcode 사용 중
- Windows: MSVC 사용 중. 별도로 mingw-w64 + Wine 크로스빌드 환경 보유
- 툴체인 파일: `toolchain/mingw-w64.cmake`
- 코드에 `#ifdef __APPLE__` / `#ifdef _WIN32` 분기가 있음 (§6 함정 3 참조)

**주 빌드 구성을 바꾸지 말 것.** `build-cc/`를 추가할 뿐이다. 실패해도 개발에 영향이 0이어야 한다. `.gitignore`에 `build-cc/` 추가.

---

## 5. Phase별 설치·실행 순서

각 Phase에 정지 조건이 있다. 통과하지 못하면 다음으로 가지 말 것.

### Phase 0 — 이미 있는 것 확인 + 첫 산출물 (설치 0)

```bash
dot -V && cmake --version && python3 --version
cmake -S . -B build-cc --graphviz=out/modules.dot
```

`cmake --graphviz`는 CMake 내장이라 추가 설치가 없다. **configure만 하면 되고 컴파일이 필요 없어서 빌드가 깨진 코드베이스에서도 나온다.**

**정지 조건**: `out/modules.dot`이 생기고 안에 실제 타겟 이름이 있으면 통과.

### Phase 1 — compile_commands.json

clang-uml의 전제다. **`CMAKE_EXPORT_COMPILE_COMMANDS`는 Makefile과 Ninja generator에서만 동작한다.** Xcode와 Visual Studio generator에서는 무시된다.

**Ninja Multi-Config는 쓰지 말 것** — 모든 구성이 한 파일에 섞여 나와 쓸 수 없다.

```bash
# 1a. macOS — 여기부터
brew install ninja
cmake -S . -B build-cc -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# 1b. Windows — 반드시 Developer Command Prompt에서 (cl.exe가 PATH에 있어야 함)
cmake -S . -B build-cc -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

**1a를 먼저 하고 통과한 뒤에 1b로 갈 것.** 양쪽을 동시에 붙들면 실패 원인이 섞인다.

**정지 조건**: `build-cc/compile_commands.json`이 생기고 안에 실제 소스 경로가 있으면 통과.

### Phase 2 — clang-uml

```bash
brew install clang-uml          # macOS
# Windows는 릴리스 바이너리 또는 소스 빌드 (LLVM 의존)

clang-uml -c .clang-uml -g json
```

`.clang-uml` 설정 파일에 다이어그램 정의가 필요하다. **처음엔 필터 없이 전체를 뽑을 것** — 노드가 몇 개 나오는지가 이후 필터 설계의 기준이 된다.

**정지 조건**: JSON이 나오고 `relationships` 배열에 `composition`/`aggregation`이 실제로 구분돼 있으면 통과.

### Phase 3 — Doxygen (Phase 1이 양쪽 다 막혔을 때만)

```bash
brew install doxygen
```

```
GENERATE_XML = YES
EXTRACT_ALL  = YES
HAVE_DOT     = NO
```

**빌드 없이 헤더만 파싱**하므로 clang-uml의 대타가 된다. 대신 **합성/집약 구분을 잃는다.** `HAVE_DOT=NO`인 이유는 그림을 Doxygen이 아니라 우리가 그리기 때문이다.

### Phase 4 — Python 환경

```bash
cd $REPO_ROOT          # C-12 — 파이프라인 코드가 사는 곳
python3 -m venv .venv
.venv/bin/pip install networkx pydot lxml
```

> ⚠ **🔵 2026-08-27 — `pip install networkx pydot lxml` 을 그냥 치면 실패한다.**
>
> ```
> error: externally-managed-environment
> × This environment is externally managed
> ```
>
> Homebrew Python 3.14.6 은 전역 설치를 거부한다(PEP 668). **venv 를 만들어야 한다.**
>
> 🔵 **2026-08-27 — `numpy` 와 `scipy` 도 필요하다.** 원래 목록(networkx·pydot·lxml)에 없었으나
> `networkx.pagerank` 가 scipy 구현만 갖고 있어 `ModuleNotFoundError: numpy` 로 죽는다(실측).
> `.venv/bin/pip install networkx pydot lxml numpy scipy` 가 완전한 목록이다.
> 실측 — 이 머신의 Python 5종(homebrew 3.14 · python.org 3.13 · macports 3.12 ·
> 시스템 3.9) 어디에도 `networkx` 가 없었다.

- `networkx` — PageRank, 순환 검출
- `pydot` — Phase 0의 `.dot` 파싱
- `lxml` — Phase 3의 Doxygen XML

clang-uml JSON은 표준 `json` 모듈로 충분하다.

### Phase 5 — `normalize.py` 제작 (macOS 산출물 기준)

Phase 0·2의 산출물을 §7의 `codegraph.json`으로 변환한다.

> 🔵 **2026-08-27 — C++ 경로 착수·동작 확인.** `codegraph/normalize.py` (C-12).
>
> ```
> .venv/bin/python codegraph/normalize.py \
>   --clang-uml <저장소>/out/codegraph-raw/full_class_all.json \
>   --repo <저장소> -o <저장소>/out/codegraph-raw/codegraph.json
> ```
>
> 🔵 실측 산출 — 입력 elements 318 / relationships 671 →
> **노드 191 · 간선 417 · 모듈 20**, `schema_version` 2.
>
> | 적용된 규칙 | 실측 |
> |---|---|
> | R5 투과 래퍼 | 94 |
> | R1 로 제거된 외부 노드 | 4 |
> | R4 외부발 간선 버림 | 26 |
> | 중복 간선 접음 | 98 (`occurrences` 로 보존) |
> | `containment` 버림(자리 없음) | 7 |
> | 끝점 해소 실패 | 48 |
>
> `kind` 분포 — `dependency` 144 · `composition` 123 · `aggregation` 82 ·
> `realization` 44 · `instantiation` 13 · `inheritance` 8 · `friendship` 3.
> 🔵 **`association` 0건** — D절 대응표의 산술적 귀결이며 예측대로다.
>
> 🔵 **`modules[].depends_on` 구현됨 (C-15)** — 클래스 간선에서 유도한다.
> 모듈 20개 / 모듈 간 간선 **49개**. `apps/_MyApp_` 이 13개 모듈에 의존하고,
> 의존이 없는 잎 모듈이 6개다(`common` `diagnostics` `input` `layout` `reflect` `shader`).
> ⚠ **이것은 링크 의존이 아니라 타입 의존이다.** `.dot` 의 PUBLIC/INTERFACE/PRIVATE 축과
> 다른 것이므로 같은 것으로 읽지 말 것.
>
> 🔵 **C# 경로 구현·완주 (2026-08-27).** `roslyn-dump`(C#, `codegraph/roslyn-dump/`) →
> `normalize_csharp()` → `codegraph.json`. 입력 types 403 / relations 1,586 →
> **노드 231 (1차 214 + 외부 17) · 간선 540 · 모듈 10 · 모듈 간 의존 20 · 순환 5**.
> **간선 540/540 전량에 근거 위치** — C++ (소유 간선만 205/417) 보다 넓다는 비대칭이 예측대로다.
> probe 실측과의 대사: inherit 명시 64 · assoc 비열거 285 · realize 70 · enum 209 ·
> `[SerializeField]` 27 — **전부 일치.** F5 게이트(errors 0 / unresolved 0) 통과.
>
> **미구현**: 회귀 테스트.
>
> ⏳ **C++ 쪽은 아직 마감되지 않았다** — 관찰 보고서에 구본(203/411)과 재수집본(318/671)
> 기준이 섞여 있고, D절·I절이 C-11→C-13 번복 이전에 쓰였다. 목록은
> `HANDOFF-cpp-pattern-collection.md` §0-1 "⏳ C++ 쪽 미완" 에 있다.


### Phase 5-1 — 모듈 다이어그램 렌더러 🔵 완료 (2026-08-27)

`codegraph/render_modules.py` — `codegraph.json` → `.dot` + `.svg` + `.png`.
**언어 무관이다.** 스키마 v2 가 같으므로 렌더러는 하나이고 두 언어에 그대로 돈다.

```bash
.venv/bin/python codegraph/render_modules.py <codegraph.json> -o out/diagrams/<이름>
```

| | C++ | C# |
|---|---|---|
| 모듈 / 의존 | 20 / 49 | 10 / 20 |
| 순환 | 11 (참여 간선 15) | 5 (참여 간선 8) |

**P1~P6 적용과 두 곳의 의도적 이탈:**

| | 스킬 기본 | 이 렌더러 | 사유 |
|---|---|---|---|
| P3 UML 3분할 | 클래스의 멤버·메서드 | **모듈의 클래스 수 + 대표 이름 3개** | 모듈 층이라 클래스 3분할이 성립하지 않는다. 노드만 보고 그 모듈이 뭘 담는지 알게 하는 취지는 유지 |
| P5 `splines=line` | 직선 | **`splines=spline`** | 🔵 직선으로 그으니 순환 간선(constraint=false, 같은 랭크)이 **사이 노드를 관통해 라벨을 지웠다.** P5 의 목적이 가독성이므로 spline 이 맞다 |

**P6 는 순환에만 쓴다** — 빨강이 다른 데 나오면 안 되도록. 상호 의존(2-순환)은 화살표 둘이
아니라 `dir=both` + "상호" 라벨 하나다(스킬 Phase 3).

⚠ **`__external__` 섬은 기본으로 그리지 않는다(`--external` 로 켠다).**
🔵 켜고 렌더해 보니 외부 17개가 세로로 늘어져 1차 밴드를 압도했고 점선이 캔버스를 가로질렀다.
이 그림의 논증은 "1차 모듈 간 의존과 순환" 하나이고 외부 접촉은 다른 논증이다 —
같은 장에 넣으면 둘 다 죽는다(스킬 Phase 2 "생략이 가치다"). 수치는 `external-nodes.tsv` 에 있다.

### Phase 7-1 — `roslyn-dump` v2 (보고서가 요구하는 살) 🔵 완료 (2026-08-27)

인계 문서 — `HANDOFF-unity-roslyn-dump-v2.md`. **F12~F14 로 형식이 확장됐다**
(`DECISION-csharp-intermediate-format.md` §10 에 구현 노트).

```
v2 살 — members 695 · methods 532 · is_abstract=true 25
        · MonoBehaviour 45 · ScriptableObject 6
```

- **회귀 12개 항목 전부 동일** — 살을 더하는 작업이라 구조 수치가 안 바뀌어야 하고, 안 바뀌었다.
  `errors 0 / unresolved 0 · types 403 · relations 1586 · normalize 후 노드 231 / 간선 540 / 모듈 10 / 순환 5`
- **새 필드 L3 전수 대조 — 위치 1,227/1,227 (100%)**. 표본이 아니라 전수로 쟀다.
  불일치로 잡힌 1건은 위치 오류가 아니라 인덱서(`IPropertySymbol.Name` 이 `this[]`)다.
  ⚠ **`partial` 은 어긋나지 않았다** — 명세가 예측한 위험처였으나 `partial_decls ≥ 2` 인 타입 10개가 전부 통과했다.
- **P3 3분할이 실제로 그려진다.** `render_classes.py` 의 `--detail` 리더에 `roslyn-dump.json`
  갈래를 태웠다(clang-uml 은 `elements[].display_name`, C# 은 `types[].name`).
  `Exceptions 2/4/3` · `Fixture 1/9/8` · `Interface 13/46/57`(«interface» 11) · `Utils 14/29/42`(멤버 31행 · 메서드 34행).

⚠ **남은 결함 둘** — 둘 다 이 작업이 만든 것이 아니다.
1. `Managers` 모듈은 Graphviz 15.1.1 이 죽는다 (`fixLabelOrder`, mincross.c:273).
   `--detail` 없이도 재현되므로 v1 부터 있던 것이다. 💭 55 원인 미확정. **별도 과제.**
2. **큰 모듈 생략 규칙이 없다.** `Utils`(클래스 14)가 렌더 결과 가로 **6,771px** 이다.
   `UIs` 50 · `Data` 53 · `Controller` 63 은 더 크다. §1 20번(LLM 에만 남는 넷)에 걸린 항목.

| 소비자 | 막힌 이유 |
|---|---|
| 클래스 다이어그램 P3 3분할 | `types[].members`/`methods` 부재 |
| 추상 클래스 «interface» 표시 | `is_abstract` 부재 (`kind` 로 인터페이스는 이미 구분됨) |
| 진입점 식별 | `MonoBehaviour` 전이 파생 표시 부재 — 🔵 정규식 5 vs Roslyn 45 |

⚠ **Track C §7 의 "`nodes[].members` 지금 만들지 말 것" 과 헷갈리지 말 것.** 그 금지는
`codegraph.json` 이고, 채우는 것은 `roslyn-dump.json` 이다. C++ 이 clang-uml 원문에서
살을 읽는 것과 **대칭**이다.

### Phase 5-2 — facts + ranking 생성기 🔵 완료 (2026-08-27)

`codegraph/facts.py` — `codegraph.json` (+ C# 은 `--detail roslyn-dump.json`) →
**`ranking.json` + `facts/*.md` 5종** (modules · classes · external · entrypoints · hotspot).
언어 무관, 전량 기계 덤프 — **생략하지 않는다**(생략 판단은 LLM 계층 §1 20번의 몫).

```bash
.venv/bin/python codegraph/facts.py <codegraph.json> --repo <저장소> [--detail <roslyn-dump.json>]
```

| | C++ | C# |
|---|---|---|
| 클래스 (전량) | 185 | 214 |
| hotspot 코드파일 | 106 | 107 |
| PageRank 상위 | `Actor` · `Component` · `Layer` · `Transform` | `InitBase` · `UI_Base` · `IDataCustomerAccessor` |

- **PageRank 는 1차 클래스 그래프에서만** 잰다 — 외부 노드를 넣으면 R3 섬의 단방향 간선이
  rank 를 전부 흡수한다(`netstandard` 1위가 되어 목적이 죽는다). 가중치는 `occurrences`.
- **hotspot 은 codegraph 밖의 피더다** — `git log --numstat` 전 이력. 이름변경은 새 경로 귀속.
- **인용을 deep-wiki 로컬 규격 `(path:line)` 그대로 낸다** — 위키가 표의 인용을 옮겨 적으면
  검증기 L3 가 잴 수 있다. C-3 주입 재료가 이것으로 완성됐다.
- 🔵 교차 신호 — C++ 에서 순환의 중심 `material` 의 `material.h` 가 hotspot 4위(17커밋)다.
  구조 신호(순환)와 변경 신호(hotspot)가 같은 곳을 가리킨다.
- ⚠ C# `entrypoints.md` 는 `--detail` 없이는 비어 있다 — unity 플래그가 `codegraph.json` 에
  없고 `roslyn-dump.json` 에만 있다(구조/살 분리, render_classes 와 같은 이유).

### Phase 8 — deep-wiki 파일럿 🔵 1건 완료 (2026-08-27, C# Managers 스코프)

`/deep-wiki:page` 규정(3단계 절차·Mermaid 3종·인용 규격·Unknown 표기)대로
**`Managers` 모듈 페이지를 생성**했다 — `<Unity저장소>/out/codegraph-raw/wiki/managers.md`.
C-3 주입: facts 5종을 근거 정본으로 사용. C-8: 대형 그림은 `csharp-modules.svg` 참조로
지시하고 페이지 내 Mermaid 는 소형(≤10노드, 부활 트리거 범위 안)만 넣었다.

**생성 직후 검증기로 쟀다 — 파이프라인이 처음으로 끝까지 한 바퀴 돌았다:**

```
인용 56건 — L1 56/56 · L2 56/56 (실패 0)
L3  노드 14 · 소유간선 0 · 근거없음 42
```

🔵 **근거없음 42건을 해부하니 검증 정책의 결함 둘이 나왔다.** 파일럿의 최대 수확이다.

| 42건의 실제 분포 | 건수 | 정체 |
|---|---|---|
| **assoc/depend 간선 위치와 정확히 일치** | **26** | `Managers.cs:38`(`_resource` 필드) 등 — codegraph 에 간선 위치로 실재하는데 **C-13 이 "소유 간선만" 으로 제한해 판정에서 빠진다.** C# 은 소유 간선이 언어상 0 이라 이 제한이 판정력을 죽인다 |
| 메서드 선언·본문 줄 | 16 | `Awake`(:55)·`Start`(:68)·`AsyncInitialize` 등 — codegraph 에 메서드 층이 없다. 단 **'살' 파일(roslyn-dump `methods[].file/line`, clang-uml `methods[].source_location`)에는 있다** |

**✅ 둘 다 확정·구현됐다 (같은 날, C-16):**
1. L3 대상 = 위치 있는 간선 전부 → C# 26건 회복
2. 검증기 `--detail` → 멤버·메서드 층 9건 회복

🔵 **재검 결과 — 근거없음 42 → 7.** 남은 7건은 메서드 본문·주석·partial 재선언 줄로,
선언이 아닌 위치를 인용한 것 — **3값 설계가 의도한 정당한 "근거 없음"** 이다.
회귀: facts 자기 일관성 C++ 185/185 · C# 265/265 그대로.

```
최종:  L1 56/56 · L2 56/56 · L3 = 노드 14 + 간선 26 + 멤버·메서드 9 + 근거없음 7
```

### Phase 9 — 검증 계층 도구 조사와 C-18 집행 🔵 (2026-08-27)

**기성 도구 조사 — 자체 제작이 필요한 것은 하나뿐이었다.**

| 필요 | 기성 도구 | 판정 |
|---|---|---|
| Mermaid→SVG | `@mermaid-js/mermaid-cli`(`mmdc` 11.16.0, MIT) — `.md` 입력을 직접 받아 블록을 추출·렌더 | ✅ 채택. 설치함 |
| dead-link | VitePress **내장** `ignoreDeadLinks: false` 가 빌드 시 전수 검사·실패 처리. 외부는 `lychee`/`markdown-link-check` | ✅ 내장으로 충분 — 별도 도구 불요 |
| VitePress 조립 | deep-wiki `wiki-vitepress` 스킬이 스캐폴딩·다크테마 3층·click-to-zoom 까지 규정 | ✅ 기성 사용 |
| 회귀 테스트 | `pytest` / stdlib `unittest` | ✅ 기성 사용 |
| **Mermaid 정책 집행** | **없음** | ❌ **자체 제작** — `codegraph/demermaid.py` |

⚠ **기성 경로가 C-8 과 충돌했다.** `wiki-vitepress` 는 `vitepress-plugin-mermaid` 로
**클라이언트에서 Mermaid 를 그린다.** 그대로 쓰면 "Graphviz 가 정본" 이 무력화된다.
→ **C-18 (A안, 전면 치환)** 으로 확정하고 `demermaid.py` 를 만들었다.

**`demermaid.py` — 두 단 치환. 원본은 고치지 않는다**(인용 검증기 대상으로 보존):

1. `<!-- graphviz: <이름> -->` 표식이 앞에 있으면 **우리 Graphviz SVG 로 교체** — C-8 의 본뜻
2. 표식 없는 나머지는 `mmdc` 로 사전 렌더 — 문법은 살리되 클라이언트 JS 의존 제거

🔵 C# 위키 실측 — **Graphviz 교체 1 · mmdc 렌더 2 · 실패 0 · 남은 클라이언트 Mermaid 의존 0.**

### Phase 6 — Windows 산출물로 검증

두 플랫폼 그래프를 비교한다. **차이 자체가 값진 정보다** — "어느 클래스가 플랫폼 전용인가"가 자동으로 드러난다. 원래 사람이 `#ifdef`를 뒤져야 알던 것이고, deep-wiki도 못 주는 정보다.

### Phase 7 — C# Roslyn 덤프 도구 제작

> 🔵 **2026-08-27 — Phase 7 착수 (사용자 승인).** 순서 규정("C++ 로 파이프라인을 완성한 뒤에
> 시작할 것")에서 이탈하지만, 그 규정이 지키려던 전제 — **인터페이스 형식이 먼저 굳는 것** — 가
> 이미 충족됐다(`roslyn-dump.json` F1~F11 · `codegraph.json` v2 · C-9~C-15). F2(도구는 원시
> 사실만, 정책은 normalize.py)가 "두 번 짜는" 위험을 구조적으로 격리했으므로 규정의 취지를
> 어기지 않는다. 마일스톤이 C+++C# 이므로 임계 경로인 이 도구를 먼저 끝낸다.

> 🔵 **2026-08-27 — 도구 완성.** `codegraph/roslyn-dump/`(C# 콘솔, Roslyn 5.9). 모드 C 재현 —
> 소스 112 / 참조 378+17 / **errors 0 / unresolved 0**, 2.5초. `depend` 832건
> (parameter 283 · local 216 · new 168 · return 165). 구현이 명세와 다르게 한 것은
> `DECISION-csharp-intermediate-format.md` §9 구현 노트에 있다.

> 🔵 **이 도구가 낼 형식은 이미 확정됐다: `DECISION-csharp-intermediate-format.md`.**
> `roslyn-dump.json` 하나를 내고, **접기 규칙(R1~R7)·모듈 배정·`kind` enum 사상은 전부
> `normalize.py` 가 한다**(F2). 도구는 원시 사실만 낸다.
> 형식 확정을 Phase 5 보다 먼저 한 이유는 **C# 쪽에 파싱할 도구 출력이 존재하지 않기 때문**이다 —
> 읽을 형식을 먼저 정하지 않으면 파서를 쓸 수 없다.


**Roslyn은 CLI가 아니라 라이브러리다.** 콘솔 앱을 만들어야 한다(§6 함정 4).

```bash
dotnet new console -o tools/roslyn-dump
cd tools/roslyn-dump
dotnet add package Microsoft.CodeAnalysis.CSharp.Workspaces
dotnet add package Microsoft.Build.Locator
```

**C++로 파이프라인을 완성한 뒤에 시작할 것.** 인터페이스 형식이 먼저 굳어야 C# 도구가 무엇을 뱉어야 할지 알고 만들어진다. 반대로 하면 두 번 짜게 된다.

---

## 6. 알려진 함정

**함정 1 — generator 제약.** `CMAKE_EXPORT_COMPILE_COMMANDS`는 Makefile과 Ninja에서만 동작한다. Xcode·Visual Studio generator에서는 조용히 무시된다. 파일이 안 생기는데 에러도 안 나므로 원인을 못 찾기 쉽다.

**함정 2 — MSVC 플래그 파싱.** Windows에서 Ninja + MSVC로 뽑으면 `compile_commands.json`이 `cl.exe` 호출과 MSVC 플래그로 채워진다. clang-uml은 libclang 기반이라 clang-cl 드라이버 모드로 읽어야 하고, MSVC 전용 확장이나 헤더에서 파싱 에러가 날 수 있다. (신뢰도: 중간 — 실제로 얼마나 걸리는지는 돌려봐야 안다.)

**폴백**: 이미 `build-win/`에서 mingw-w64를 쓰고 있으므로, MSVC 대신 mingw 툴체인으로 `build-cc`를 만들면 GCC 플래그가 나와 clang이 훨씬 잘 읽는다. 그리고 macOS에서 크로스로 뽑을 수 있어 Windows 머신이 아예 필요 없어진다.

```bash
cmake -S . -B build-cc-win -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=toolchain/mingw-w64.cmake \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

**함정 3 — 두 플랫폼의 그래프가 다르다.** clang-uml은 전처리 후를 보므로, macOS에서 뽑은 그래프에는 Windows 전용 클래스·멤버가 **아예 없다.** 반대도 같다. 따라서 `codegraph.json`은 **플랫폼별로 따로 나오고 하나로 합칠 수 없다.** 스키마에 `platform` 필드가 필수인 이유다.

**함정 4 — Roslyn은 설치가 아니라 제작이다.** C++는 CLI를 깔면 끝이지만 C#은 콘솔 앱을 만들어야 한다. `Microsoft.Build.Locator`가 필요한 이유는 MSBuild 위치를 런타임에 찾아야 하기 때문이고, 이걸 빼면 흔히 실패한다.

**함정 5 — 언어 교체는 도구 교체가 아니다.** C#으로 가면 두 가지를 잃는다. (a) 합성/집약 구분 — 언어에서 소유와 참조가 구분되지 않아 도구를 바꿔도 안 된다. (b) 인용 검증 L3 — C++는 clang-uml JSON이 공짜로 주지만 C#은 Roslyn 덤프를 따로 만들어야 한다. **C# 보고서는 5종 간선이 아니라 3종(상속·실현·연관)으로 그려야 한다.**

**함정 6 — 거울 함정.** `normalize.py`는 JSON을 표로 바꾸는 스크립트다. 플러그인 구조, 파서 레지스트리, 추상 인터페이스가 나오면 과잉이다. 언어가 둘뿐이면 함수 두 개면 된다.


**함정 7 — 고아 헤더는 조용히 사라진다 (D2, 범위 밖으로 확정).** `.cpp` 가 없어 번역 단위가 없는
헤더는 색인되지 않는다. **0건이 에러가 아니라 정상 종료라, 사라졌다는 사실조차 안 보인다.**
🔵 이 저장소에서 실제로 발생했다 — `src/fsm` 은 헤더 2개뿐이고 `src/fsm/*.cpp` 가 없어
`compile_commands.json` 번역 단위 **0건**, clang-uml 노드 **0건** 이었다. `StateMachine<TState,TOwner>` 가
`Scene::Component` 를 상속하는데도 그래프에 없다.
**도구를 바꿔서 푸는 문제가 아니다** — libclang · clangd · ccls · clang-query · Kythe · scip-clang 이
전부 번역 단위 기반이라 같은 한계를 갖는다. 자기 코드는 헤더 자기충족성 컨벤션으로 줄이고,
남의 코드는 **해결 수단이 없다.** 대신 D5 대로 **"미확인 영역" 에 고아 헤더 목록을 실어 신호는 살린다.**

**함정 8 — 실행 환경과 색인 대상은 독립이다.** 🟡 `scip-clang` 바이너리는 Linux · macOS 만 제공된다.
그러나 "Windows 코드를 못 본다" 는 뜻이 아니다. **무엇을 보는지는 OS 가 아니라
`compile_commands.json` 이 정한다.** `_WIN32` 가 정의된 compdb 를 주면 macOS 에서 돌아도
Windows 코드 경로를 본다. 이때 `codegraph.json` 의 `platform` 필드가 값을 한다(함정 3 과 짝).

**함정 9 — MSVC 전용 코드베이스는 미지원 (D4).** mingw 헤더와 MSVC 헤더는 다르다.
MSVC 전용 확장(`__declspec`, MSVC STL 내부)을 쓰는 코드는 mingw 로 파싱되지 않고,
`scip-clang` 은 Windows 에서 돌지 않는다. **양쪽이 동시에 막힌다.** 실제로 만났을 때가 재검토 시점이다.

**함정 10 — `scip` 이라는 이름이 충돌한다 (scip-clang 은 폴백으로 강등됐으나 되살릴 때를 위해 남긴다).** 🔵 `brew install scip` 은 Sourcegraph 의 코드 인텔리전스
도구가 아니라 **혼합정수계획 솔버**(SCIP Optimization Suite, scipopt.org, 현재 10.0.3)를 설치한다.
🔵 `scip-clang` 은 Homebrew 포뮬러가 **없다**(`No available formula`). 공식 릴리스 바이너리를 직접
받아야 한다. **이름만 보고 `brew install scip` 을 실행하면 전혀 다른 소프트웨어가 깔린다.**

**함정 11 — `pip install multilspy` 는 C++ 를 못 한다.** 🔵 PyPI 최신 릴리스는 **0.0.15 (2025-04-03)**
이고, 설치해서 열어 보면 `language_servers/` 에 `clangd_language_server` 가 **없으며**
`Language` enum 이 `csharp python rust java kotlin typescript javascript go ruby dart` 뿐이다 —
**`cpp` 가 없다.** 저장소 main 은 살아 있고(최근 커밋 2026-08-20) 거기에는 `cpp` 가 있지만,
**릴리스된 적이 없다.** C++ 를 쓰려면 `pip install git+https://github.com/microsoft/multilspy` 로
움직이는 브랜치를 받아야 한다. README 의 지원 언어표(`cpp | clangd`)는 main 기준이라
**PyPI 설치본과 다르다.** 🔵 `solidlsp`(Serena 내장)도 PyPI 독립 패키지가 없다
(`No matching distribution found`).

---

## 7. `codegraph.json` 스키마 v1

```json
{
  "schema_version": 2,
  "language": "cpp",
  "platform": "macos",
  "source_tool": "clang-uml 0.5.3",
  "repo_commit": "a1b2c3d",

  "nodes": [
    { "id": "C1", "name": "Renderer", "kind": "class",
      "module": "render", "file": "src/render/renderer.h", "line": 42 },
    { "id": "X1", "name": "std", "kind": "external",
      "module": "__external__", "file": null, "line": null,
      "collapsed_from": ["std::vector<...>", "std::function<...>", "..."] }
  ],
  "edges": [
    { "from": "C1", "to": "C2", "kind": "composition",
      "label": "mFrameBuffer", "file": "src/render/renderer.h", "line": 51 }
  ],
  "modules": [
    { "id": "render", "depends_on": ["core", "gl"] }
  ]
}
```

**설계 근거 셋:**

1. ~~**`edges[]`에 `file`/`line`이 붙는다** — 노드가 아니라 엣지에. "Renderer가 FrameBuffer를 소유한다"는 주장의 근거는 클래스 선언이 아니라 **멤버 선언 줄**이다. 인용 검증 L3가 여기서 성립한다.~~

   ⚠ **2026-08-27 — 두 번 뒤집혔다. C-11 로 취소됐다가 C-13 으로 되살아났다.**
   **원문(위 취소선)의 취지가 결국 옳았다.** 다만 적용 범위가 좁아졌다.

   ### 최종 (C-13)

   **L3 의 판정 대상 = 노드 + 소유 간선(`composition`·`aggregation`).** 나머지 간선은 근거가 없다.

   🔵 **실측이 C-11 의 근거를 뒤집었다.** C-11 은 "clang-uml 이 간선에 위치를 주지 않는다" 를
   전제로 했는데, **노드의 `members[]` 에 멤버별 `source_location` 이 전부 들어 있다.**

   ```
   멤버 561건 전부에 source_location.line 있음
   간선 label -> members[] 유일 매칭 : 311건,  모호 0건,  실패 3건(friendship 의 "<<friend>>")
     aggregation 215/215  ·  association 96/96   = 소유 간선 100%
   ```

   **문자열 탐색이 아니라 구조 조회다.** C-11 을 정할 때 "파일 안에서 label 을 찾는 휴리스틱,
   같은 이름이 여러 번 나오면 틀림" 으로 설명했던 것은 **메커니즘을 잘못 안 것이다.**
   🔵 산출된 `codegraph.json` 에서 소유 간선 **205/205 전량**에 정확한 멤버 선언 줄이 붙는다.

   | 간선 종류 | 근거 위치 | L3 판정 |
   |---|---|---|
   | `composition` · `aggregation` | **멤버 선언 줄** (`members[].source_location`) | **한다** |
   | `dependency` · `inheritance` · `realization` · `instantiation` · `friendship` | 없음 — 가리킬 멤버가 없다 | **근거 없음** |

   **대가: 검증기가 3값이 된다** — 통과 / 실패 / **근거 없음**. 2값으로 만들려고 "근거 없음" 을
   통과로 세면 검증이 무의미해지고, 실패로 세면 정상 간선이 전부 실패한다. **3값을 그대로 낸다.**

   **C# 은 더 넓다** 🔵 — Roslyn 의 `IFieldSymbol.Locations` 는 필드 선언 줄을 주고 표본 4건이
   전부 일치했다. `assoc` 간선 전량에 위치가 붙으므로 **C# 은 L3 대상이 C++ 보다 넓다.**
   그 비대칭은 숨기지 않고 언어별 보고서에 적는다.

   근거는 실측이다 🔵 — clang-uml 0.6.3 은 **간선 411건 전량에 위치를 주지 않는다.** 간선 키
   조합 3종 어디에도 `file`·`line`·`source_location` 이 없다(전수 확인). 위 설계 근거가 요구하는
   바로 그 필드를 C++ 쪽 주 도구가 산출하지 않는다.

   복구안 둘을 검토하고 **둘 다 채택하지 않았다:**

   | 안 | 왜 안 썼나 |
   |---|---|
   | 간선 `label`(멤버 이름)로 파일 안에서 줄을 역추적 | `label` 이 있는 간선이 **166/411** 뿐이다. 나머지 245건은 근거를 만들 방법이 아예 없고, 같은 이름 멤버가 여러 번 나오면 틀린 줄을 짚는다. **인용 검증이 통과/실패 2값이 아니라 통과/실패/모름 3값이 된다** |
   | `clangd` 역방향 참조 갈래와 조인 | 전수 복구는 가능해 보이나 별개 갈래(`HANDOFF-clangd-reverse-refs.md`)와 결합되고 범위가 커진다 |

   **바뀌는 것과 안 바뀌는 것을 분명히 한다.**

   - **필드는 남는다.** `edges[].file`/`line` 을 스키마에서 빼지 않는다 — 아래 확장 규율("제거 금지")에
     걸리고, **C# 쪽은 이 값을 정확하게 낸다.** 🔵 Roslyn 의 `IFieldSymbol.Locations` 는 필드 선언
     줄을 그대로 주며 간선 표본 4건이 전부 일치했다. 낼 수 있는 도구는 계속 낸다.
   - **판정만 노드로 내린다.** 검증기는 인용된 `file:line` 을 `nodes[]` 의 위치와 대조한다.
     간선에 값이 있어도 **판정에 쓰지 않는다** — 언어마다 있고 없고가 갈리면 검증 기준 자체가
     언어에 따라 달라지기 때문이다.
   - **잃는 것을 적어 둔다.** "A 가 B 를 소유한다" 의 근거로 제시되는 줄이 **멤버 선언 줄이 아니라
     타입 선언 줄**이 된다. 독자가 그 줄에 가면 `class Renderer {` 만 있고 소유 관계는 안 보인다.
     💭 **이 손실을 문서 쪽에서 어떻게 보완할지는 아직 정하지 않았다.**
2. **`kind`는 8종 고정 enum** (C-10, 2026-08-27 확장):
   `inheritance / realization / composition / aggregation / dependency / association / instantiation / friendship`.

   앞의 6종은 **UML 의 관계 어휘**다 🔵 88 — UML 은 Dependency · Association(Aggregation/Composition 으로 더 특정됨) · Generalization(=`inheritance`) · Realization 을 관계 종류로 둔다.
   뒤의 2종은 **C++ 고유**로, C++ 실측에서 6종에 자리가 없어 추가했다: `instantiation`(템플릿 실체화, 11건) · `friendship`(`friend` 선언, 2건).
   **C# 은 이 둘이 영원히 0건이다** — 언어에 대응 개념이 없다.

   ⚠ **UML 원본과 이 enum 은 구조가 다르다** 🔵 90. UML 에서 `composition`/`aggregation` 은 관계의 종류가 아니라 **association 끝(Property)에 붙는 `AggregationKind` 열거값**이다 — `none` / `shared` / `composite` 셋 (UML 2.5.1 사양 127쪽). 즉 이 enum 은 **관계 종류 축과 소유 강도 축을 한 줄로 평탄화한 것**이다.

   그 평탄화가 실측에서 이렇게 드러난다:
   - **C++ 는 `association` 이 0건**이다. clang-uml 이 소유 강도를 보고하므로 값 멤버 140건은 `composite`, 포인터 26건은 `shared` 로 가고 `none` 에 남는 것이 없다.
   - **C# 은 `composition`/`aggregation` 이 0건**이다. 언어에 소유 표지가 없어 전부 `none` 으로 떨어져 `association` 285건이 된다.

   **둘 다 대응표가 틀린 것이 아니라 축이 그렇게 생긴 결과다.** 축을 분리하는 안(`kind` 4종 + `ownership` 필드)은 2026-08-27 에 검토했고 **채택하지 않았다** — `kind` 에서 값을 빼는 것이 아래 확장 규율("제거·의미 변경 금지")에 걸리기 때문이다.
3. **`source_tool`을 기록한다** — 나중에 "이 사실이 어느 도구에서 왔나"를 추적할 수 있다. 도구가 틀렸을 때 범위를 좁힌다.
4. **외부 의존은 §2-1 (C-9) 의 규칙을 따른다** — 전이 확장 없음, 패키지 이름 노드 하나, `module: "__external__"` 외딴 섬, 사용자→외부 단방향 간선. 외부 노드에는 `file`/`line` 이 붙지 않는다(이 저장소에 소스가 없으므로). ~~간선 쪽 `file`/`line` 은 사용자 쪽 멤버 선언 줄이라 L3 는 유지된다.~~ → **C-11 이후 무의미하다.** L3 는 노드 기준이고 외부 노드는 애초에 L3 대상이 아니므로, 외부로 가는 간선은 **인용 검증의 대상에서 통째로 빠진다.**

**확장 규율**: 필드는 **추가만** 한다. 제거·의미 변경 금지. `schema_version`은 깨는 변경에만 올린다.

**나중에 붙일 자리 (지금 만들지 말 것)**: `nodes[].members`, `nodes[].methods`, `calls[]`.

`kind: "external"` 과 `collapsed_from[]` 은 §2-1(C-9) 규칙이 요구하는 두 필드다. **확장 규율("추가만")을 지킨 추가다.** 노드의 `kind`("class"/"external")와 간선의 `kind`(8종 enum)는 **서로 다른 필드**이니 혼동하지 말 것. 외부 노드는 `file`/`line` 이 `null` 이다 — 저장소 안에 선언 위치가 없기 때문이고, 그래서 **인용 검증 L3의 대상이 아니다.**

---

## 8. 인용 검증 L1 / L2 / L3

기성 도구가 못 하는 지점이고, 이 파이프라인의 차별화가 여기다. 조사 결과 **file:line을 코드와 결정론적으로 대조하는 도구는 존재하지 않는다** — 전부 "경로 존재 확인" 수준이다.

| | 검사 | 방법 |
|---|---|---|
| L1 | 파일이 존재하나 | `os.path.isfile` |
| L2 | 그 라인이 존재하나 | 줄 수 비교 |
| **L3** | **그 위치에 그 심볼이 실제로 있나** | **`codegraph.json` 의 `nodes[].file`/`line` 과 대조** (C-11) |

**L3가 값의 전부다.** deep-wiki가 "Renderer는 `renderer.h:42`에 있다"고 쓰면 `codegraph.json`과 맞춰 참/거짓을 기계적으로 판정할 수 있다.

> 🔵 **2026-08-27 — 검증기 구현 완료: `codegraph/verify_citations.py`.**
>
> ```bash
> .venv/bin/python codegraph/verify_citations.py <문서.md ...> --repo <저장소> --codegraph <codegraph.json>
> ```
>
> - **판정 3값** — 통과 / 실패(L1·L2, 종료코드 1) / 근거 없음(L3). 인용 패턴은 확장자
>   화이트리스트 정규식 — deep-wiki 로컬 규격 `(path:line)` 과 백틱·링크·범위 전부 잡는다.
> - **자기 일관성 시험 통과** — facts/*.md 의 인용 C++ 185/185 · C# 265/265 가 전부
>   L3 노드 일치. facts 는 codegraph 에서 생성됐으므로 100% 가 나와야 정상이고, 나왔다.
> - **오염 시험 통과** — 없는 파일(L1)·줄 초과(L2)·**위치는 유효한 선언인데 문서가 다른
>   심볼을 주장하는 경우(이름 대조 경고)** 를 전부 잡는다.
> - **실전 표본** — 손으로 쓴 관찰 보고서(OBSERVATION.md) 28건: 노드 16 · 소유간선 3 ·
>   근거없음 9. 3값의 분포가 실제 문서에서 이렇게 나온다.
> - 🔵 **구현 중 발견 — (file,line) → 심볼은 1:1 이 아니다.** StageFSMState.h:42 에
>   그 줄의 실제 선언(`BaseStageFsmState`)과 사용 지점을 위치로 갖는 템플릿 인스턴스
>   (`IFsmState<Actor>`)가 함께 등록돼 있다(F-1 함정의 1차 코드판). 색인은 다중값이다.

> **2026-08-27 C-13 — L3 의 대상은 노드 + 소유 간선이다.** 근거는 §7 설계 근거 1.
> 검증기가 판정하는 주장은 둘이다:
>
> | 주장 형태 | 대조 대상 |
> |---|---|
> | "X 는 `파일:줄` 에 선언돼 있다" | `nodes[].file`/`line` |
> | **"X 가 Y 를 소유한다 (`파일:줄`)"** | **`edges[].file`/`line` — `kind` 가 `composition`/`aggregation` 인 것만** |
>
> 그 외 간선(`dependency`·`inheritance`·`realization`·`instantiation`·`friendship`)은
> `file`/`line` 이 `null` 이다. **검증기는 이것을 "근거 없음" 으로 내고 통과로도 실패로도 세지 않는다.**
>
> ⚠ **두 가지 실무 함정이 딸려 온다** 🔵 C++ 실측:
>
> 1. **노드 `name` 이 canonical 이라 소스 텍스트와 다르다.** `basic_string` vs `std::string`,
>    `unique_ptr` vs 프로젝트 별칭 `VertexLayoutUPtr`. 문자열 대조로 L3 를 하면
>    1st-party 는 97/102 통과하지만 외부는 77/101 로 떨어진다.
> 2. **중첩 타입의 `name` 구분자가 `::` 가 아니라 `##` 다.** `Program##UniformBlock`.
>    `is_nested == true` 이면 `##` 로 쪼개 **마지막 조각**으로 대조해야 한다.
>    🔵 이 함정은 **표본 10건으로는 안 잡히고 전수 203건으로 재야 드러났다.**
>    **L3 검증기의 자체 검증은 표본이 아니라 전수로 할 것.**

---

## 9. 기각안 + 부활 트리거

**"영구 금지"가 아니다.** 각각 부활 조건이 있다. 다음 세션이 이유를 모르고 다시 제안하는 왕복을 막기 위한 목록이다.

| 기각안 | 부활 트리거 |
|---|---|
| **CodeWiki 전체 도입** | deep-wiki catalogue가 자식≤8 제약으로도 못 쪼갤 만큼 대상이 커질 때 (~1M 줄 다국어 모노레포) |
| **CodeWiki 계층 분해만 발췌** | 독립 CLI가 없고 물리 크기 기반이라 수동 의미 경계보다 열등 |
| **deepwiki-by-cc** | 스타 1·포크 0의 미검증 1인 프로젝트. 성숙해지면 재검토 |
| **호스팅 DeepWiki를 파이프라인 부품으로** | 불가능. MCP 도구가 셋뿐이고 이미 만들어진 위키에 질문하는 창구다 |
| **JS/TS · Python 분석기** | 그 언어 코드베이스를 실제로 문서화할 때 |
| **SCIP / Joern / tree-sitter 통합** | 지원 언어가 5개 이상으로 늘 때 |
| **deep-wiki의 Mermaid 다이어그램 사용** | 노드 상한이 없어 중형에서 깨진다. 대상이 아주 작을 때만 |
| **다이어그램 단계 교체 · 사후 대조 검증** | 사용자가 범위 밖으로 명시. 입력 주입만으로 목표 달성 가능 |
| **벡터 DB / 임베딩 RAG** | 사실 테이블이 결정론적이고 작으므로 불필요 |
| **`normalize.py`의 플러그인 구조** | 언어가 4개 이상으로 늘 때 |

---

## 10. 작업 규약

- 사용자의 기존 스킬을 전부 준수한다. 특히 `confidence-and-sourcing` §1.5(티어→행동 결속), `code-design-review-lenses`의 Self-review gate.
- 확신도는 🔵/🟡/💭 + 정수. 🔵는 **이번 세션에서 읽은** file:line만 인정.
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 사용자는 **구현물보다 의사결정용 보고서를 먼저** 받기를 선호한다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.** 이전 인계 초안이 그 이유로 한 번 반려됐다.
- Graphviz 다이어그램은 사용자의 P1~P6 방법론을 따른다. 특히 **P4(rankdir=BT 의미축)는 A1(constraint=true/false 분리) 없이는 작동하지 않는다.**

---

## 11. 저장소에서 직접 확인할 것

| 항목 | 왜 |
|---|---|
| `dot -V`, `cmake --version`, `python3 --version` | Phase 0 전제 |
| 현재 CMake generator | Xcode/VS면 Phase 1에서 Ninja 빌드 디렉토리를 새로 만들어야 함 |
| `.gitignore`에 `build-cc/` 추가했는지 | 안 하면 생성물이 커밋된다 |
| `toolchain/mingw-w64.cmake` 존재 여부 | 함정 2의 폴백 경로 |
| C# 프로젝트가 실제로 있는지, 솔루션 파일 위치 | Phase 7 전제 |
| microsoft/skills `deep-wiki` 플러그인 설치 여부 | ✅ 🔵 **2.0.0 설치 완료 (2026-08-27, `deep-wiki@skills`).** C-1 근거 3개 실물 대조 통과 — VitePress(`wiki-vitepress`) · file:line 인용 강제(Step 0 + Mermaid `<!-- Sources -->` + 페이지당 최소 5파일) · 미확인 영역(`(Unknown – verify in ...)` 규칙). **C-3 주입 지점 = `/deep-wiki:generate` Step 1(Repository Scan)** · C-8 치환 대상(Mermaid 11회 내장) 확인. | `/plugin marketplace add microsoft/skills` → `/plugin install deep-wiki`. ⚠ 🔵 **`npx skills add microsoft/skills` 로는 안 된다** — 그 명령은 레포의 `.github/skills/`(스킬 13개, Azure/KQL 등)만 가져오고, deep-wiki 는 `.github/plugins/deep-wiki/` 의 **플러그인**이라 빠진다. 2026-08-27 실제로 그렇게 헛설치됐다. 제공 명령: `/deep-wiki:generate` · `page` · `research` |

---

## 12. 첫 작업

**Phase 0을 지금 실행하라.** 5분이고 설치가 없다.

```bash
cmake -S . -B build-cc --graphviz=out/modules.dot
```

`.dot` 파일이 나오면 그 내용을 사용자에게 보여주고, **그것을 기준으로 `normalize.py`의 첫 파서를 설계하라.** 스키마를 추측으로 먼저 짜지 말 것 — 실제 산출물을 보고 맞추는 것이 순서다.

---

## 13. 2026-08-27 세션 변경 이력 — 오케스트레이터 보고용

**이 문서와 하위 문서에 이번 세션이 가한 변경 전량이다.** 무엇이 사용자 확정이고
무엇이 에이전트 실측인지 구분해 적는다.

### 확정 결정이 둘 늘었다 (§2)

| ID | 결정 | 확정 근거 |
|---|---|---|
| **C-9** | 외부 의존은 전이 확장 없이 단일 노드로 접고, 하나의 외딴 섬에 모으고, 간선은 사용자→외부 단방향만 | 2026-08-27 사용자 확정. 상세 §2-1 |
| **C-10** | 간선 `kind` enum 을 **8종**으로 확장 (6종 + `instantiation` + `friendship`), `schema_version` 1 → 2 | 2026-08-27 사용자 확정. C++ 실측에서 6종에 자리 없는 문자열이 나왔다 |

### §2-1 규칙이 R1~R7 로 자랐다

- **R1~R4** (C# 실측에서) — 전이 금지 / 패키지 이름 노드 하나 / `__external__` 외딴 섬 / 단방향
- **R5~R6** (C++ 실측에서, 사용자 추가) — 컨테이너·스마트포인터 투과 / 섬 간선 `constraint=false`
- **R7** (이번 세션 추가) — **원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.**
  🔵 근거: `(BCL) netstandard` 접촉이 **274 → 9**. 나머지 11개 외부 노드 접촉 합이 72 이므로
  R7 없이는 표준 라이브러리 하나가 전체의 4배가 된다. ⚠ 노드는 사라지지 않는다(9건이 남는다).

**적용 순서 고정: R5 → R7 → R2 → R1 → R4 → R3 → R6.**
⚠ C++ 쪽 R7 은 **규칙만 넣었고 실측이 없다.** `(STL) std` 가 R7 전후로 어떻게 변하는지,
C++ 에 "암묵적 기반 타입" 이 있기는 한지는 재봐야 한다(`HANDOFF-cpp-pattern-collection.md` §2-3).

### §7 스키마 갱신

`schema_version` 2. `kind` 8종. **UML 근거를 실측으로 확인해 적었다** 🔵 —
UML 은 Dependency · Association(Aggregation/Composition 으로 더 특정됨) · Generalization · Realization 을
관계 종류로 두고, `AggregationKind` 는 `none`/`shared`/`composite` 로 **association 끝(Property)에 붙는
열거값**이다(UML 2.5.1 사양 127쪽).

**이것이 두 언어의 0건을 설명한다** — 이 enum 은 관계 종류 축과 소유 강도 축을 한 줄로 평탄화했다.
C++ 는 전부 `shared`/`composite` 로 몰려 `association` 0건, C# 은 전부 `none` 으로 몰려
`composition`·`aggregation` 0건이다. **대응표의 오류가 아니다.**
축 분리안(`kind` 4종 + `ownership` 필드)은 검토 후 **채택하지 않았다** — `kind` 에서 값을 빼는 것이
§7 확장 규율("제거·의미 변경 금지")에 걸린다.

### 하위 문서 변경

| 문서 | 변경 |
|---|---|
| `HANDOFF-unity-pattern-collection.md` | §2-2(C-9 의 C# 적용) · 단계 2-1(패키지 노드) · **단계 5-1(Roslyn 질의 파이프라인)** 신설. §3 단계 5 의 "정규식은 전부 하한" 경고를 **실측으로 정정** |
| `HANDOFF-cpp-pattern-collection.md` | §2-3(C-9 의 C++ 적용) 신설 + R7 |
| `templates/OBSERVATION-template.md` | D절 enum 6종 → 8종 |
| `DECISION-csharp-intermediate-format.md` | **F12~F14** 추가 + **§10 v2 구현 노트** 신설 |
| `samples/{cpp,csharp-unity}/OBSERVATION.md` | D절에 결정 반영 주석. **관찰 기록 자체는 고치지 않았다** — 6종 시점의 관찰이라는 사실이 정보이므로 |

### 이번 세션이 실측으로 뒤집은 것 셋 🔵

1. **정규식 계수는 하한조차 아니다.** `MonoBehaviour` 정규식 5 vs Roslyn 45,
   `StartCoroutine` 정규식 5 vs Roslyn 1(5건 중 **4건이 주석**). 하한도 상한도 아니다.
   → 단계 5-1(Roslyn 질의 파이프라인)이 이 때문에 생겼다.
2. **모듈 간 의존은 `roslyn-dump` 없이도 잴 수 있었다.** 상속·실현·필드만 보면 7모듈/101건인데
   `dependency` 를 넣으면 **10모듈/1,484건**(14배)이 된다.
3. **`(BCL) netstandard` 접촉 274건의 실질은 9건이다.** 265건이 원시 타입이고 그중 129건은
   암묵적 기반 타입(`object` 60 · `System.Enum` 62 · `System.ValueType` 7)이었다. → R7.

### 열려 있는 게이트 — 사용자 판정 대기

| # | 항목 | 막는 것 |
|---|---|---|
| 1 | **큰 모듈 생략 규칙** | 🔵 `Utils`(클래스 14) 렌더가 가로 6,771px. §1 20번(LLM 에만 남는 넷) |
| 2 | **`codegraph-rules.toml` 의 `[[layer]]` 확정 + 순환 판정** | C# 은 초안 있음, C++ 은 파일 자체가 없음 |
| 3 | R5 `TRANSPARENT` 에 `IReadOnlyDictionary` 추가 여부 | (A) 전수 census 가 잡아낸 누락 1건 |

### 다음 세션이 할 일 — 제안

**정적 계층은 이제 전부 끝났다.** `codegraph.json` 아래로는 아무것도 없다 —
`facts/*.md` · `ranking.json` · 검증 계층(L1/L2/L3 · Mermaid 치환 · 경계 판정 · dead-link) ·
deep-wiki 결합 · VitePress 가 전부 미착수다.

💭 65 — **인용 검증기(L1/L2/L3)를 먼저 만드는 것**을 제안한다. 재료가 100% 갖춰져 있고
(간선 540/540 · 멤버·메서드 1,227/1,227 에 위치), 위 게이트를 기다리지 않으며,
§8 이 "L3 가 값의 전부" 라고 못박은 것이기 때문이다. 반면 `facts`·`ranking`·deep-wiki 는
게이트 1번(무엇을 생략할지)에 걸린다.
