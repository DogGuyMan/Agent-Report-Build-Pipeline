# 관찰 보고서 — GlobalMedia-OpenGL-ComputerGraphics / C++

> 이 파일은 `docs/handoffs/templates/OBSERVATION-template.md` 의 사본이다.
> **절 번호와 제목을 바꾸지 말 것.** C++ 쪽 보고서와 C# 쪽 보고서가 같은 골격이어야
> `normalize.py` 의 파서 두 개를 나란히 놓고 설계할 수 있다.
> 채울 수 없는 칸은 **지우지 말고 `미확인` 또는 `해당 없음` 으로 남긴다.** 빈칸 자체가 정보다.

작성일: 2026-08-27
저장소 경로: `$GRAPHICS_REPO`
`repo_commit`: `bfb72b4`
작성자 세션: Claude Code Agent (C++ 저장소 내 실행), 핸드오프 `HANDOFF-cpp-pattern-collection.md` 수행

> ⚠ **상위 핸드오프 §1 의 환경 실측이 이번 세션 시점에는 틀렸다.** 핸드오프는
> "🔵 실측 — `build_ninja/compile_commands.json` 이 존재하며 132개 항목" 이라고 적었으나,
> 이번 세션 시작 시점에 이 저장소에는 **빌드 디렉토리가 하나도 없었다**(`ls -d build_*` → no matches).
> 따라서 Track C Phase 0·1 이 "이미 충족" 이라는 전제도 성립하지 않아, configure 를 새로 돌렸다.
> 자세한 것은 H절.

> ⚠ **이 수집의 측정 범위 — 선언만 읽었고 구현 로직은 읽지 않았다.**
> 🔵 이번 세션에서 연 소스는 전부 **선언(declaration)** 이다. 함수 본문(`.cpp` 구현부)은 **0건** 읽었다.
> 따라서 이 보고서가 근거를 가진 것은 **구조**(누가 누구를 소유·상속·의존하는가)뿐이고,
> **행위**(알고리즘이 무엇을 계산하는가, 어떤 순서 계약·불변식을 지키는가, 복잡도)에 대해서는
> 이 보고서에 근거가 **없다.** 그것은 Track C §1 이 LLM 계층(20~22번)에 배정한 몫이고,
> 정적 계층인 이 수집의 범위 밖이다. 범위를 적어 두지 않으면 독자가 행위까지 실측된 것으로 오해한다.

---

## A. 환경 실측

실제로 실행한 명령과 그 출력만 적는다. "설치돼 있을 것이다" 를 적지 않는다.

원문은 `out/codegraph-raw/00-env.txt`.

| 도구 | 확인 명령 | 출력 | 비고 |
|---|---|---|---|
| Graphviz | `dot -V` | `dot - graphviz version 15.1.1 (20260805.0921)` | 이미 설치돼 있었다 |
| CMake | `cmake --version \| head -1` | `cmake version 4.2.3` | `--fresh` 플래그 사용 가능 |
| Python | `python3 --version` | `Python 3.14.6` | |
| ninja | `ninja --version` | `1.13.2` | |
| clang-uml | `clang-uml --version` | `(eval):6: command not found: clang-uml` | **수집 시작 시점 미설치** |
| clang-uml (설치 후) | `clang-uml --version` | `clang-uml 0.6.3` / `Built against LLVM/Clang libraries version: 22.1.8` / `Using LLVM/Clang libraries version: Homebrew clang version 22.1.8` | |
| AppleClang | `/usr/bin/c++ -print-resource-dir` | `.../XcodeDefault.xctoolchain/usr/lib/clang/21` | clang-uml 의 22 와 **버전이 다르다**. H절 참조 |
| macOS SDK | `xcrun --show-sdk-path` | `/Applications/Xcode.app/.../MacOSX.sdk` | H절 참조 |

**설치가 필요했던 것:**

- `clang-uml` 0.6.3 — `brew install clang-uml` (의존 `llvm@22`, `yaml-cpp` 동반 설치). 핸드오프가 예고한 대로 이 작업의 유일한 신규 설치였다.

---

## B. 산출물 목록

`out/codegraph-raw/` 에 실제로 생긴 파일 전량이다. 디렉토리 총계 **2.4 MB**.

| 파일 | 크기(바이트) | 생성 명령 | 소요 시간 |
|---|---|---|---|
| `00-commit.txt` | 8 | `git rev-parse --short HEAD` | 즉시 |
| `00-env.txt` | 414 | A절 명령 묶음 | 즉시 |
| `01-cmake-graphviz-attempt1.log` | 1179 | 핸드오프 §3 단계 2 원문 명령 (**실패**) | 1.17s |
| `01-cmake-graphviz-attempt2.log` | 13771 | 위 명령 + vcpkg 툴체인 (**성공**) | 6.68s |
| `01-modules.dot` | 23281 | `cmake --fresh ... --graphviz=` | 위와 동일 |
| `01-modules.dot.<타겟>` / `.dependers` | 합계 약 1.5 MB | 같은 명령이 자동 생성 | 위와 동일 |
| `01-modules-nodelist.tsv` | 2852 | `.dot` 에서 노드 라벨 추출 | 즉시 |
| `01-modules-counts.txt` | 863 | `.dot` 노드·간선 계량 | 즉시 |
| `02-cc-ls.txt` | 148 | `ls -l ... compile_commands.json` | 즉시 |
| `02-cc-sample.txt` | 1435 | 핸드오프 §3 단계 3 파이썬 한 줄 | 즉시 |
| `03-clang-uml.log` | 10813 | `clang-uml -c .clang-uml -g json` | 42.58s |
| `full_class.json` | 834039 | 위와 동일 | 위와 동일 |
| `04-json-summary.txt` | 1348 | JSON 구조·관계 분포 요약 | 즉시 |
| `05-fileline-verify.txt` | 1673 | F절 검증 (전체 노드 앞 10건) | 즉시 |
| `05-fileline-verify-firstparty.txt` | 1445 | F절 검증 (1st-party 10건) | 즉시 |
| `06-counts.txt` | 1108 | E절 계량 | 즉시 |
| `07-composition-probe.yml` | 605 | D절 `composition` 단독 필터 프로브 설정 | — |
| `07-composition-probe.json` | 784871 | `clang-uml -c ... --allow-empty-diagrams --paths-relative-to-pwd` | 약 40s |

부속 `.dot` 파일 수: **119개**. 핸드오프 §3 이 예고한 대로 `cmake --graphviz` 는 타겟마다
`01-modules.dot.<타겟>` 과 `01-modules.dot.<타겟>.dependers` 를 함께 만든다. 전부 남겼다.

**생성에 실패한 것과 그 오류 메시지 원문:**

1. 핸드오프 §3 단계 2 의 **원문 명령이 실패**했다 (`01-cmake-graphviz-attempt1.log`):

```
CMake Error at cmake/DepsBase.cmake:9 (find_package):
  Could not find a package configuration file provided by "glm" with any of
  the following names:

    glmConfig.cmake
    glm-config.cmake

  Add the installation prefix of "glm" to CMAKE_PREFIX_PATH or set "glm_DIR"
  to a directory containing one of the above files.  If "glm" provides a
  separate development package or SDK, be sure it has been installed.
Call Stack (most recent call first):
  CMakeLists.txt:43 (include)


-- Configuring incomplete, errors occurred!
```

2. clang-uml 1차 실행 실패 — H절 참조.
3. clang-uml 2차 실행 실패 — H절 참조.

---

## C. 레코드 형태 표본

**도구가 낸 원문을 그대로 붙인다.** 요약·정리·이름 바꾸기 금지. `normalize.py` 의 파서는
이 표본을 보고 쓰이므로, 손댄 표본은 파서를 틀리게 만든다.

종류마다 **1건씩만** 붙인다. 길면 배열 원소 하나만 잘라 붙이고 잘랐다고 명시한다.

파일 표본은 `shapes/` 에 따로 두었다. 아래는 그 요지다.

### C-1. 노드에 해당하는 레코드

clang-uml `full_class.json` → `elements[]`. 전량은 `shapes/node.json`
(`SJH::Scene::Component`, `methods`/`members` 배열만 앞 2건으로 잘랐고 그 사실을 파일 안에 고지했다).

```json
{
  "bases": [],
  "display_name": "SJH::Scene::Component",
  "id": "18032677677727336093",
  "is_abstract": false,
  "is_nested": false,
  "is_struct": false,
  "is_template": false,
  "is_union": false,
  "members": [ ... ],
  "methods": [ ... ],
  "name": "Component",
  "namespace": "SJH::Scene",
  "source_location": {
    "column": 11,
    "file": "src/input/mouse_input.h",
    "line": 42,
    "translation_unit": "src/input/mouse_input.cpp"
  },
  "template_parameters": [],
  "type": "class"
}
```

노드 키 조합은 4종뿐이다 (`04-json-summary.txt`):

| 건수 | 키 조합 |
|---|---|
| 118 | `bases, display_name, id, is_abstract, is_nested, is_struct, is_template, is_union, members, methods, name, namespace, source_location, template_parameters, type` |
| 77 | 위 + `comment` |
| 7 | `comment, constants, display_name, id, is_nested, name, namespace, source_location, type` (enum) |
| 1 | 위에서 `comment` 뺀 것 (enum) |

### C-2. 간선에 해당하는 레코드 — 종류별로 전부

`full_class.json` → 최상위 `relationships[]`. **`elements[].relationships` 는 존재하지 않는다**
(전 원소에서 0건). 7종 전량을 `shapes/edge-<type>.json` 에 1건씩 두었다.

```json
{"access": "private", "destination": "7546507215697875010", "label": "mOwner", "source": "18032677677727336093", "type": "association"}
{"access": "public",  "destination": "1543424174166016462", "label": "kind",   "source": "4821160019948448471", "type": "aggregation"}
{"access": "public",  "destination": "18032677677727336093", "source": "6258977476063918454", "type": "extension"}
{"access": "public",  "destination": "11730101602020562410", "source": "12706590146902731468", "type": "instantiation"}
{"access": "public",  "destination": "15408304036949544313", "source": "3728793175869902679", "type": "containment"}
{"access": "public",  "destination": "7546507215697875010", "label": "<<friend>>", "source": "18032677677727336093", "type": "friendship"}
{"access": "public",  "destination": "10174927757876140213", "source": "2871142539160479454", "type": "dependency"}
```

간선 키 조합은 3종뿐이다:

| 건수 | 키 조합 |
|---|---|
| 243 | `access, destination, source, type` |
| 166 | `access, destination, label, source, type` |
| 2 | `access, destination, label, multiplicity_destination, source, type` |

### C-3. 모듈·프로젝트 경계에 해당하는 레코드

`cmake --graphviz` 의 `01-modules.dot`. 발췌 원문은 `shapes/module.dot.txt`.

```
    "node0" [ label = "_MyApp_", shape = egg ];
    "node1" [ label = "engine_deps", shape = pentagon ];
    "node1" -> "node2" [ style = dashed ] // engine_deps -> -framework Cocoa
    "node0" -> "node1" [ style = dotted ] // _MyApp_ -> engine_deps
    "node34" -> "node36"  // sjhopengl_render -> sjhopengl_material
    "node33" [ label = "sjhopengl_diagnostics\n(SJH::diagnostics)", shape = octagon ];
```

읽는 법이 파일 안에 Legend 서브그래프로 박혀 있다. 그 원문도 `shapes/module.dot.txt` 에 전량 넣었다.

| `shape` | 뜻 | 이 저장소 출현 수 |
|---|---|---|
| `egg` | Executable | 2 |
| `octagon` | Static Library | 45 |
| `doubleoctagon` | Shared Library | 3 |
| `tripleoctagon` | Module Library | 1 |
| `pentagon` | Interface Library | 19 |
| `hexagon` | Object Library | 1 |
| `septagon` | Unknown Library | 6 |
| `box` | Custom Target | 1 |

(위 수치는 Legend 자체의 8개 예시 노드를 뺀 것이다.)

| `style` | Legend 가 붙인 라벨 | 이 저장소 간선 수 |
|---|---|---|
| (속성 없음) | Legend 상 `solid` = PUBLIC 링크 | 125 |
| `dashed` | `Interface` | 71 |
| `dotted` | `Private` | 50 |

### C-4. 위 셋 중 어디에도 안 들어가는데 실제로 나온 레코드

1. **노드 라벨 안에 개행과 별칭이 같이 들어 있다.** `.dot` 라벨은 타겟명 하나가 아니라
   `타겟명\n(별칭 네임스페이스)` 형태다 — 예: `"sjhopengl_render\n(SJH::render)"`.
   `_MyApp_` `sb7` `glfw3` 같은 일부에는 별칭 부분이 없다. 파서가 두 형태를 다 받아야 한다.

2. **경로가 타겟 이름 자리에 들어온 노드가 1건 있다.**

```
    "node6" [ label = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System/Library/Frameworks/OpenGL.framework", shape = septagon ];
```

   macOS 프레임워크 4건은 또 다른 형태다 — `-framework Cocoa` 처럼 **컴파일 플래그 원문**이 라벨이다.

3. **자기 자신을 가리키는 간선이 있다.**

```
    "node0" -> "node0"  // _MyApp_ -> _MyApp_
```

4. **부속 `.dot` 파일은 독립된 `digraph` 인데 노드 번호를 주 파일과 공유한다.**
   `01-modules.dot.base_deps` 안의 `"node8"` 은 주 파일의 `"node8"`(`glm::glm`) 과 같은 대상이다.
   부속 파일만 따로 파싱하면 번호가 충돌한다.

5. clang-uml JSON 최상위에 `metadata` 가 있다. `{"clang_uml_version": "0.6.3", "llvm_version": "Homebrew clang version 22.1.8", "schema_version": 3}` — **`schema_version: 3`** 이 파서가 붙잡을 버전 축이다.

---

## D. 간선 종류 대응표 — 이 보고서의 핵심

> ### 📌 2026-08-27 사용자 확정 — 이 절을 읽을 때의 전제가 바뀌었다
>
> 이 절은 `kind` 가 **6종 고정**이던 시점의 관찰이다. 그 뒤 아래가 확정됐다.
> **관찰 기록은 고치지 않는다. 결정만 여기 덧붙인다.**
>
> - **C-10 — `kind` enum 이 8종으로 확장됐다.** 6종 + `instantiation` + `friendship`.
>   `schema_version` 1 → 2. 아래 "대응시킬 수 없는 것" 표의 `instantiation`(C++ 11건)과
>   `friendship`(2건)은 **이제 자리가 생겼다.** `containment`(5건)는 여전히 자리가 없다.
> - **6종의 출처가 확인됐다** 🔵 88 — UML 의 관계 어휘다. Dependency · Association
>   (Aggregation/Composition 으로 더 특정됨) · Generalization(=`inheritance`) · Realization.
> - **`association` 0건 / `composition`·`aggregation` 0건은 대응표의 오류가 아니다** 🔵 90.
>   UML 에서 `composition`/`aggregation` 은 관계 종류가 아니라 association 끝(Property)의
>   `AggregationKind` 열거값(`none`/`shared`/`composite`, UML 2.5.1 사양 127쪽)이다.
>   이 enum 은 **관계 종류 축과 소유 강도 축을 한 줄로 평탄화**했고, 그래서
>   C++ 는 전부 `shared`/`composite` 로, C# 은 전부 `none` 으로 몰린다.
>   축을 분리하는 안(`kind` 4종 + `ownership` 필드)은 검토 후 **채택하지 않았다** —
>   `kind` 에서 값을 빼는 것이 §7 확장 규율("제거·의미 변경 금지")에 걸린다.
> - **R7 이 추가됐다** — 원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.
>   적용 순서: R5 → R7 → R2 → R1 → R4 → R3 → R6.

`codegraph.json` 의 `kind` 는 **6종 고정 enum** 이다:
`inheritance / realization / composition / aggregation / dependency / association`.

도구가 실제로 낸 문자열을 왼쪽에, 대응하는 enum 을 오른쪽에 적는다.

### D-1. clang-uml (`full_class.json` → `relationships[].type`)

출현 횟수는 `전체 / 양끝이 SJH 네임스페이스인 것` 두 수를 병기한다.

| 도구가 낸 문자열 | 출현 횟수 | 대응 enum | 판단 근거 |
|---|---|---|---|
| `extension` | 21 / 21 | `inheritance` 또는 `realization` | 🔵 `SJH::Scene::MeshRenderer -> SJH::Scene::Component`(구상 기반) 와 `SJH::Scene::MeshRenderer -> SJH::IRenderable`(순수 인터페이스) 가 **같은 문자열 `extension`** 으로 나온다. 둘을 가르려면 대상 노드의 `is_abstract` 를 봐야 한다. 간선만으로는 못 가른다 |
| `association` | 26 / 26 | `aggregation` | 🔵 포인터·참조 멤버다. 실측 대조: `label: "mOwner"` → `src/scene/actor.h:84` 의 `Actor* mOwner = nullptr;`. 소유하지 않는 참조 = UML 집약 |
| `aggregation` | 140 / 17 | `composition` | 🔵 **값 멤버다.** 실측 표본: `label:"detail"` → `std::string detail`, `label:"findings"` → `std::vector<DiagFinding> findings`, `label:"kind"` → enum 값 멤버. 값으로 품으면 수명이 묶이므로 UML 합성 |
| `dependency` | 206 / 68 | `dependency` | 🔵 그대로 대응 |
| `containment` | 5 / 5 | `dependency` 로 흡수하거나 버림 | 🔵 중첩 타입 관계다 — `SJH::Program::UniformBlock -> SJH::Program`. 소유가 아니라 **선언 위치**를 뜻한다. 방향도 안쪽→바깥쪽이다 |
| `instantiation` | 11 / 8 | 대응 자리 없음 (아래 표) | 🔵 `SJH::Reflect::TypeName<float> -> SJH::Reflect::TypeName<T>` — 템플릿 실체화 |
| `friendship` | 2 / 2 | 대응 자리 없음 (아래 표) | 🔵 `label` 이 `"<<friend>>"` 로 고정돼 온다 |

> ⚠ **가장 중요한 관찰.** clang-uml 이 쓰는 `aggregation` / `association` 이라는 낱말은
> `codegraph.json` enum 의 `aggregation` / `association` 과 **뜻이 겹치지 않는다.**
> 문자열을 그대로 옮기면 값 멤버 140건이 전부 틀린 칸에 들어간다.
> 🔵 이 판정은 세 표본을 원본 선언까지 열어 대조한 결과다(위 판단 근거 칸).
> 🔵 **위 대응표를 적용하면 `codegraph.json` 의 `association` 칸은 이 저장소에서 0건이 된다.**
> 추측이 아니라 대응표의 산술적 귀결이다 — clang-uml 의 `association` 26건은 `aggregation` 으로,
> `aggregation` 140건은 `composition` 으로 가고, `association` 으로 갈 문자열이 남지 않는다.
> 💭 60 — 이것이 대응표가 틀렸다는 신호인지 C++ 에 단순 연관이 실제로 드물다는 뜻인지는 판단이 갈린다. 확정은 사용자 몫이다.

**대응시킬 수 없는 것 (enum 6종에 자리가 없는 것):**

| 도구가 낸 문자열 | 출현 횟수 | 왜 안 들어가나 |
|---|---|---|
| `instantiation` | 11 (1st-party 8) | 템플릿 실체화는 타입 간 소유·의존이 아니라 **같은 타입의 다른 실체**다. 6종 어디에도 이 뜻이 없다. 이 저장소에서는 `SJH::Reflect::TypeName<T>` 특수화 때문에 몰려 나온다 |
| `friendship` | 2 | C++ 고유의 접근 권한 부여다. 의존 방향이 아니라 **캡슐화 예외**를 뜻한다. C# 쪽 보고서에는 대응물이 아예 없을 것이다 |
| `containment` | 5 | 중첩 타입 선언이다. 위 표에 `dependency` 흡수 후보로 적었으나, 뜻이 정확히 같지는 않아 여기에도 남긴다 |

**반대로 이 도구가 끝내 내지 못하는 enum:**

- **`composition` — 0건.** 🔵 411개 간선 전체에서 문자열 `composition` 이 한 번도 안 나온다.
  단, 이것은 "도구가 그 개념을 모른다" 는 뜻이 **아니다.** 두 가지를 따로 실측했다.
  - 🔵 `include.relationships: [composition]` 설정이 **스키마 검증을 통과한다**
    (`clang-uml --validate-only` → `Configuration file ... is valid.`). 즉 enum 값으로 존재한다.
  - 🔵 그 필터만 걸고 실제로 돌리면 `elements 203 / relationships 0` 이다
    (`07-composition-probe.json`). 즉 **이 저장소에서 실제로 0건 산출**이다.
  - 따라서 clang-uml 0.6.3 은 값 멤버를 `composition` 이 아니라 `aggregation` 으로 부르고 있다.
    핸드오프 §3 단계 4 의 정지 조건 표현("`composition` 과 `aggregation` 이 실제로 구분돼 있으면 통과")을
    문자 그대로 적용하면 **불통과**지만, 뜻으로 보면 값/포인터 구분 자체는 살아 있다
    (`aggregation` vs `association` 로 갈린다). **도구를 갈아타지 않고 그대로 보고한다.**
- **`realization` — 구분 불가.** 위 `extension` 항목대로 인터페이스 구현과 클래스 상속이 같은 문자열이다.
  가르려면 간선이 아니라 **대상 노드의 `is_abstract` 를 조회**해야 한다.
- **`inheritance` 의 가상/비가상, `public/private` 상속 구분** — `access` 필드가 오긴 하나
  이번 산출물의 `extension` 21건은 전부 `"access": "public"` 이었다.

### D-2. `cmake --graphviz` (`01-modules.dot`)

이쪽은 클래스가 아니라 **CMake 타겟 간 링크 관계**라 enum 6종과 층이 다르다.

| 도구가 낸 문자열 | 출현 횟수 | 대응 enum | 판단 근거 |
|---|---|---|---|
| 간선에 `style` 속성 없음 | 125 | `dependency` | 🔵 Legend 가 `solid` 를 일반 링크로 그린다. `target_link_libraries(... PUBLIC ...)` 에 해당 |
| `[ style = dashed ]` | 71 | `dependency` | 🔵 Legend 라벨이 `Interface` — `INTERFACE` 링크 |
| `[ style = dotted ]` | 50 | `dependency` | 🔵 Legend 라벨이 `Private` — `PRIVATE` 링크 |

**대응시킬 수 없는 것:**

| 도구가 낸 문자열 | 출현 횟수 | 왜 안 들어가나 |
|---|---|---|
| PUBLIC / INTERFACE / PRIVATE 링크 구분 | 246 전량 | 셋 다 `dependency` 로 뭉개진다. **링크 가시성은 6종 enum 에 자리가 없다.** 그런데 이 정보가 모듈 경계 그림에서는 가장 쓸모 있는 축이다 |

**반대로 이 도구가 끝내 내지 못하는 enum:**

- `inheritance` / `realization` / `composition` / `aggregation` / `association` **전부.**
  타겟 그래프에는 클래스 개념이 없다. 🔵 `.dot` 전체에서 상속·소유를 뜻하는 표기가 없다.

> ⚠ **enum 을 늘리는 제안을 여기에 쓰지 말 것.** 관찰만 적는다.
> 스키마 변경은 두 언어의 보고서가 모두 도착한 뒤 사용자가 결정한다.

---

## E. 계량

계량 원문은 `out/codegraph-raw/01-modules-counts.txt` 와 `06-counts.txt`, 탭 구분본은 `counts.tsv`.

### E-1. clang-uml (클래스 층)

| 항목 | 값 |
|---|---|
| 노드 수 (전체) | 203 |
| 노드 수 (서드파티·외부 의존 제외) | 102 |
| 간선 수 (전체) | 411 |
| 간선 수 (서드파티·외부 의존 제외) | 147 |
| 모듈·어셈블리 수 | 17 (노드의 `source_location.file` 을 `src/<모듈>` 로 접은 수) |
| 가장 노드가 많은 모듈과 그 수 | `src/reflect` — 37 |

노드 네임스페이스 분포: `SJH` 102 / `std` 83 / `glm` 7 / `nlohmann` 5 / `Effekseer` 2 / `FMOD` 2 / 무네임스페이스 2.
**`MyApp` 네임스페이스는 0건이다.** 이유는 아래 제외 기준 항목 참조.

모듈별 노드 수 (`source_location.file` 기준):
`src/reflect` 37 · `src/diagnostics` 26 · `src/render` 21 · `src/object` 19 · `src/resource_registry` 19 ·
`src/scene` 14 · `src/material` 14 · `src/program` 10 · `src/buffer` 7 · `src/sprite` 7 · `src/playable` 7 ·
`src/text` 5 · `src/common` 5 · `src/input` 4 · `src/texture` 4 · `src/layout` 2 · `src/shader` 2.

간선 종류별 전체/1st-party: `dependency` 206/68 · `aggregation` 140/17 · `association` 26/26 ·
`extension` 21/21 · `instantiation` 11/8 · `containment` 5/5 · `friendship` 2/2 · `composition` 0/0.

🔵 끝점이 `elements` 에 없는 간선(dangling)은 **0건**이다. 모든 `source`/`destination` id 가 노드로 실재한다.

### E-2. `cmake --graphviz` (모듈 층)

| 항목 | 값 |
|---|---|
| 노드 수 (전체) | 70 |
| 노드 수 (서드파티·외부 의존 제외) | 44 |
| 간선 수 (전체) | 246 |
| 간선 수 (서드파티·외부 의존 제외) | 204 |
| 모듈·어셈블리 수 | 70 (노드 = CMake 타겟이라 같다) |
| 가장 노드가 많은 모듈과 그 수 | 해당 없음 (이 층에서는 노드 자체가 모듈이다) |

1st → 3rd 간선 34건, 3rd → 3rd 간선 8건, 자기참조 1건.

**제외 기준으로 쓴 경로 패턴을 그대로 적는다:**

⚠ **핸드오프 §3 은 제외 기준으로 `extern/` 이라는 경로 패턴을 적으라고 했으나, 그렇게 할 수 없다.**
🔵 `01-modules.dot` 에는 **경로가 없다.** 노드는 CMake 타겟 이름뿐이고, 경로가 라벨로 들어온 것은
`OpenGL.framework` 단 1건이다. 그래서 실제로 쓴 기준은 **경로가 아니라 타겟 이름 정규식**이다:

```
^(_MyApp_|myapp_|sjh_|sjhopengl_|base_deps|engine_deps|game_deps|stb_extra)
```

이 기준으로 제외된 26개 노드 전량(도구가 낸 라벨 원문):

```
-framework Cocoa · -framework CoreFoundation · -framework CoreVideo · -framework IOKit
/Applications/Xcode.app/.../MacOSX.sdk/System/Library/Frameworks/OpenGL.framework
Boost::describe · Boost::mp11 · Boost::pfr · Threads::Threads
Effekseer · EffekseerRendererGL · assimp · assimp::assimp · box2d::box2d
fmod · fmodstudio · fmt::fmt · glfw3 · glm::glm · glm::glm-header-only
imgui::imgui · nlohmann_json::nlohmann_json · sb7 · spdlog · spdlog::spdlog · tweeny
```

clang-uml 쪽 제외 기준은 또 다르다 — 여기에는 경로가 있으므로 `source_location.file` 을 쓸 수 있지만,
실제로는 **네임스페이스**(`SJH::` / `MyApp::` 로 시작하는가)를 썼다. `std::` 83건이 경로로는
`src/...`(첫 사용 지점)를 가리켜서 경로 기준이 듣지 않기 때문이다. F절 참조.

⚠ **핸드오프 §3 이 예고한 `extern/Effekseer` 타겟 폭증은 일어나지 않았다.**
🔵 `.dot` 에 `TestCpp` `EffekseerSoundOSMixer` 류가 하나도 없다. `Effekseer` 와 `EffekseerRendererGL`
두 개만 있고 둘 다 `octagon`(Static Library) 로, 사전 빌드된 라이브러리를 링크만 하는 형태다.
따라서 "제외 전후 수의 차이로 `normalize.py` 의 절단 지점을 정한다" 는 §3 의 계획은
이 저장소에서는 다른 근거를 써야 한다.

### E-3. C-9 외부 축약 적용 시 — 접기 전후 (2026-08-27 추가)

> 이 절은 수집을 끝낸 뒤 상위 규칙 C-9(Track C §2-1, 이 문서 짝 핸드오프 §2-3)가 확정돼 덧붙인 것이다.
> **위 E-1·E-2 의 수치는 축약 전 원본이고, 아래가 축약 후다.** 원시 산출물은 손대지 않았다.
> 계산 원문은 `out/codegraph-raw/08-external-collapse-simulation.txt`, 노드 목록은 `external-nodes.tsv`.

적용 순서 R5 → R2 → R1 → R4 기준이다.

| 층 | 노드 (전 → 후) | 간선 (전 → 후) | 외딴 섬 크기 |
|---|---|---|---|
| 클래스 | 203 → **105** (사용자 102 + 섬 3) | 411 → **302** | 3 (`(STL) std` · `glm` · `Effekseer`) |
| 모듈 | 70 → **58** (사용자 44 + 섬 14) | 246 → **233** | 14 |

**서브모듈이 만드는 CMake 타겟 → 외부 노드 (핸드오프 §2-3 이 요구한 형식):**

```
extern/Effekseer 가 만드는 CMake 타겟   2개   ->  외부 노드 1개 (Effekseer)
                                              Effekseer ; EffekseerRendererGL
extern/sb7code   가 만드는 CMake 타겟   1개   ->  외부 노드 1개 (sb7)
                                              sb7
```

🔵 **핸드오프 §3 이 예고한 `TestCpp` · `EffekseerSoundOSMixer` 류는 나오지 않았다.** 이 저장소는
Effekseer 를 `add_subdirectory` 하지 않고 사전 빌드 라이브러리로 링크만 한다. 따라서 "접기 전후 수의
차이" 가 C++ 쪽에서는 크지 않다 — 폭증은 서브모듈이 아니라 **vcpkg 포트가 타겟 둘로 갈리는 것**과
**`std::` 템플릿 인자 증식**에서 온다.

**R1(전이 금지)이 지운 것 — 접촉 0회라 섬에도 못 들어간다:**

| 제거된 노드 | 누가 끌고 온 것인가 |
|---|---|
| `fmt::fmt` · `Threads::Threads` | `spdlog` |
| `Boost::mp11` | `boost-describe` |
| `glm::glm-header-only` | R2 가 이미 `glm` 으로 흡수 |

**R2 를 R1 보다 먼저 해야 하는 이유가 이 저장소에서 실제로 나온다.** 🔵 `Effekseer` 는 1st-party 가
직접 링크하지 않고 `EffekseerRendererGL` 을 거쳐야만 닿아 **depth 1** 이다. R1 을 먼저 적용하면
`Effekseer` 가 잘리고 부속 타겟 이름인 `EffekseerRendererGL` 이 섬에 남는다.

**R5(컨테이너 투과)가 없으면 사라질 뻔한 사용자 코드끼리의 소유 간선 8건** — 목록은 Track C §2-1.
R5 를 넣으면 사용자끼리 간선이 147 → **178** 로 늘고 그중 **27건이 `composition`** 으로 살아난다.
🔵 자기참조 `X → unique_ptr<X> → X` 10건은 접으면 자기 루프가 되어 자동 소멸하며, 전부 `XUPtr`
별칭과 `static Create()` 팩토리의 부산물이라 무손실이다.


---

### E-4. 🔵 apps/ 재수집 (2026-08-27) — 위 E-1~E-3 은 `src/` 만 보던 반쪽이다

H절의 미해결 항목 "`apps/` 가 통째로 빠졌다" 를 사용자 승인으로 닫았다.
`glob` 에 `apps/*/*.cpp` 를 더해 다시 수집했다. **구본은 지우지 않았다** —
`full_class.json`(구본)과 `full_class_all.json`(신본)이 둘 다 있다.
대조 원문은 `out/codegraph-raw/13-apps-recollect-census.txt`.

| 항목 | 구본 (src) | 신본 (src+apps) | 증감 |
|---|---|---|---|
| elements | 203 | **318** | +115 |
| relationships | 411 | **671** | +260 |

**네임스페이스별 노드**

| 네임스페이스 | 구본 | 신본 | 증감 |
|---|---|---|---|
| `SJH` | 102 | 111 | **+9** |
| `std` | 83 | 107 | +24 |
| **`TopdownShooter`** | **0** | **74** | +74 |
| `glm` | 7 | 7 | 0 |
| `FMOD` | 2 | 6 | +4 |
| `nlohmann` | 5 | 5 | 0 |
| `Effekseer` | 2 | 3 | +1 |
| `tweeny` | 0 | 1 | +1 |
| (무네임스페이스) | 2 | 4 | +2 |

🔵 **앱 네임스페이스 이름이 `MyApp` 이 아니라 `TopdownShooter` 다.** `MyApp` 은 CMake 타겟
이름(`_MyApp_`)이었지 C++ 네임스페이스가 아니었다. **H절과 I절의 "`MyApp::` 0건" 서술은
이름이 틀렸던 것이고, 현상(앱 코드 부재) 자체는 맞았다.**

🔵 **`SJH` 가 9개 는 것이 중요하다.** 엔진 쪽인데 **앱에서만 쓰이던 타입**이라 `src/` 만 보면
안 잡혔다. 즉 재수집은 앱 코드를 더한 것만이 아니라 **엔진 그래프의 구멍도 메웠다.**

**간선 종류**

| 종류 | 구본 | 신본 | 증감 |
|---|---|---|---|
| `dependency` | 206 | 282 | +76 |
| `aggregation` | 140 | 215 | +75 |
| `association` | 26 | 96 | **+70** |
| `extension` | 21 | 52 | +31 |
| `instantiation` | 11 | 16 | +5 |
| `containment` | 5 | 7 | +2 |
| `friendship` | 2 | 3 | +1 |
| `composition` | 0 | **0** | 0 |

🔵 **`composition` 은 신본에서도 0건이다.** D절의 대응표(값 멤버 = `aggregation`,
포인터 멤버 = `association`)는 **앱 코드를 넣어도 그대로 유효하다.**
🔵 `association`(포인터 멤버)이 26 → 96 으로 **3.7배**가 됐다 — 앱 코드가 엔진 객체를
포인터로 들고 있는 구조로 보인다.

**R1 외부 접촉 — 외부 노드가 3개에서 5개로 늘었다**

| 외부 노드 | 구본 접촉 | 신본 접촉 | 타입 종수(신본) |
|---|---|---|---|
| `(STL) std` | 122 | 168 | 99 |
| `glm` | 48 | 69 | 4 |
| `FMOD` | **0 (R1 로 제거됐었다)** | **5** | 4 |
| `Effekseer` | 2 | 4 | 3 |
| `tweeny` | **0 (없었다)** | **1** | 1 |

🔵 ⭐️ **`FMOD` 가 R1 을 통과하기 시작했다.** E-3 은 "`nlohmann-json` 과 `FMOD` 는 외부를
거쳐야만 닿아서 R1(전이 금지)이 제거한다" 고 적었다. **그것은 `src/` 만 봤을 때의 사실이었다** —
앱 코드가 FMOD 를 **직접** 쓴다. `tweeny` 도 앱에서만 나온다.
**"무엇이 R1 을 통과하는가" 가 수집 범위에 따라 달라진다는 실증이다.**
🔵 `nlohmann` 은 신본에서도 여전히 R1 이 제거한다(접촉 0회).

---

## F. `file` / `line` 실재 여부 — 인용 검증 L3 의 성립 조건

`codegraph.json` 스키마는 **노드가 아니라 간선에** `file`/`line` 을 요구한다.
"A 가 B 를 소유한다" 의 근거는 클래스 선언 줄이 아니라 **멤버 선언 줄** 이기 때문이다.

| 질문 | 답 | 근거 |
|---|---|---|
| 노드에 file/line 이 붙는가 | **예. 203/203 전량.** | 🔵 `source_location` 객체로 온다. 키는 `file` `line` `column` `translation_unit` 4개 |
| **간선에 file/line 이 붙는가** | **아니오. 411건 전량에 없다.** | 🔵 간선 키 조합 3종(C-2)에 `file`·`line`·`source_location` 이 하나도 없다. 프로그램으로 전수 확인했다 |
| 경로가 절대경로인가 상대경로인가 | **저장소 루트 기준 상대경로.** `src/input/mouse_input.h` 형태 | 🔵 표본 5건 전량이 `src/` 로 시작한다. 단 `translation_unit` 도 같은 상대 형식이다 |
| 그 경로가 실제로 존재하는가 (표본 10건 확인) | **10/10 존재** | 🔵 `os.path.exists` 로 확인 |
| 그 줄에 실제로 그 심볼이 있는가 (표본 10건 육안 대조) | **1st-party 10/10 일치. 단 `std::` 타입은 0/여러 건 불일치** | 아래 표 |

> ⚠ **이 절이 이 보고서에서 D절 다음으로 중요하다.**
> 🔵 **간선에 file/line 이 없다.** `codegraph.json` 스키마가 간선에 요구하는 바로 그 필드를
> clang-uml 은 주지 않는다. 인용 검증 L3 를 간선 단위로 세우려면 이 간극을 메워야 한다.
> 다만 간선의 **`label` 이 멤버 이름**(`mOwner`, `findings`, `kind`)으로 오고,
> 출발 노드의 `source_location` 이 그 멤버가 선언된 **파일**을 가리키므로,
> 파일은 알고 **줄만 모르는** 상태다. I절에 이어 적는다.

### F-2. 전수 대조 (2026-08-27 추가 — 표본이 놓친 것이 있어 전 노드로 다시 쟀다)

> 아래 F-1 의 표본 10건은 **양식이 요구한 최소치**였고, 그 결과는 1st-party 10/10 완전 일치였다.
> **전수로 다시 재니 결과가 다르다.** 전수 검사가 프로그램으로 수 초이므로 표본을 쓸 이유가 없었다.
> 원문은 `out/codegraph-raw/09-fileline-census-full.txt`.

🔵 **노드 203건 전수** (표본 아님):

| 검사 | 결과 |
|---|---|
| L1 파일이 존재하나 | **203 / 203** |
| L2 그 줄이 존재하나 | **203 / 203** |
| L3 그 줄에 그 심볼이 있나 — 1st-party | **97 / 102** |
| L3 그 줄에 그 심볼이 있나 — 외부 | **77 / 101** |

**1st-party 불일치 5건은 전부 중첩 타입(nested type)이고, 원인이 하나다.**

| 노드 | 위치 | 그 줄의 실제 내용 |
|---|---|---|
| `SJH::Diagnostics::CaptureVariant::Target` | `src/diagnostics/pass_capture.h:34` | `enum Target` |
| `SJH::Program::UniformBlock` | `src/program/program.h:107` | `struct UniformBlock` |
| `SJH::Program::UniformMember` | `src/program/program.h:189` | `struct UniformMember` |
| `SJH::MaterialPropertyBlock::TextureBinding` | `src/material/material_property_block.h:63` | `struct TextureBinding` |
| `SJH::RenderableProcessor::WorldEntry` | `src/render/renderable_processor.h:88` | `struct WorldEntry` |

🔵 **중첩 타입의 `name` 필드는 구분자로 `##` 를 쓴다.**

```
display_name = "SJH::Program::UniformBlock"
name         = "Program##UniformBlock"      <- :: 가 아니라 ##
namespace    = "SJH"                        <- 바깥 클래스가 namespace 에 안 들어간다
is_nested    = true
```

선언 줄에는 `struct UniformBlock` 만 있으므로 `name` 을 그대로 문자열 대조하면 **반드시 실패한다.**
`is_nested == true` 이면 `name` 을 `##` 로 쪼개 **마지막 조각**으로 대조해야 한다.
🔵 이 저장소의 중첩 타입은 5건이고 전부 이 규칙으로 일치한다.

외부 불일치 24건은 아래 F-1 이 이미 적은 canonical 이름 문제(`basic_string` vs `string`)와 같은 원인이다.

### F-3. 🔵 재수집본 L3 전수 대조 (2026-08-27) — 중첩 타입 규칙이 검증됐다

C-11 로 **L3 의 판정 대상은 노드뿐**이 됐으므로, 노드 318건 전수로 다시 쟀다.
**F-2 가 발견한 중첩 타입 규칙(`is_nested` 이면 `name` 을 `##` 로 쪼개 마지막 조각으로 대조)을
적용한 상태다.**

| 검사 | 구본 (203) | 신본 (318) |
|---|---|---|
| L1 파일이 존재하나 | 203/203 | **318/318** |
| L2 그 줄이 존재하나 | 203/203 | **318/318** |
| **L3 — 1st-party** | **102/102** | **185/185** |
| L3 — 외부 | 77/101 | 107/133 |

🔵 ⭐️ **1st-party 가 100% 다.** F-2 는 같은 구본에서 **97/102** 였다 — 중첩 타입 5건이
불일치했다. 그 5건을 `##` 규칙으로 처리하니 **102/102 가 됐고, 신본 185건에서도 불일치가 0이다.**
**F-2 가 제안한 규칙이 3.6배 큰 표본에서 반증되지 않았다.**

🔵 **외부는 여전히 80% 언저리다**(107/133). 원인은 F-1 이 적은 canonical 이름 문제
(`basic_string` vs `std::string`)로 그대로다. **C-9 로 외부는 노드 하나로 접히고
`file`/`line` 이 `null` 이 되므로 L3 대상에서 빠진다** — 실무상 문제가 되지 않는다.

**F-1. 표본 10건 대조 결과 (양식이 요구한 최소치 — 위 F-2 가 이것을 대체한다):**

1st-party(`SJH::`) 노드 10건 — 원문은 `05-fileline-verify-firstparty.txt`.

| # | 도구가 말한 위치 | 그 줄의 실제 내용 | 일치 |
|---|---|---|---|
| 1 | `src/input/mouse_input.h:42` | `class MouseInput` | 예 |
| 2 | `src/layout/vertex_layout.h:62` | `class VertexLayout` | 예 |
| 3 | `src/diagnostics/gl_log.h:48` | `class GLObjectLog` | 예 |
| 4 | `src/diagnostics/gl_log.h:107` | `class GLDebug` | 예 |
| 5 | `src/diagnostics/gl_validate.h:47` | `enum class IndexFindingKind` | 예 |
| 6 | `src/diagnostics/gl_validate.h:57` | `struct DiagFinding` | 예 |
| 7 | `src/diagnostics/gl_validate.h:65` | `struct DiagResult` | 예 |
| 8 | `src/diagnostics/gl_validate.h:77` | `enum class InfoLogSeverity` | 예 |
| 9 | `src/diagnostics/gl_validate.h:86` | `struct LinkReport` | 예 |
| 10 | `src/diagnostics/uniform_diagnostics.h:40` | `class UniformDiagnostics` | 예 |

**그러나 필터 없이 앞 10건을 뽑으면 결과가 딴판이다** — 원문은 `05-fileline-verify.txt`.
`elements` 배열 앞머리는 대부분 `std::` 타입이고, 그 `source_location` 은 선언 위치가 아니라
**이 저장소에서 처음 쓰인 지점**을 가리킨다.

| # | 도구가 말한 위치 | 그 줄의 실제 내용 | 일치 |
|---|---|---|---|
| 1 | `src/reflect/file_watch.h:32` | `std::filesystem::file_time_type mLastWrite{};` | 아니오 (노드 이름은 `time_point`) |
| 2 | `src/input/mouse_input.h:48` | `void BindLookHandler(std::function<void(double dx, double dy)> handler` | 예 (`function`) |
| 5 | `src/layout/vertex_layout.h:71` | `static VertexLayoutUPtr Create();` | 아니오 (노드 이름은 `unique_ptr`) |
| 6 | `src/diagnostics/gl_log.h:56` | `static bool CheckShaderCompile(GLuint shader, std::string_view tag = {` | 아니오 (노드 이름은 `basic_string_view`) |
| 9 | `src/reflect/meta.h:27` | `std::string Text;` | 아니오 (노드 이름은 `basic_string`) |
| 10 | `src/reflect/type_id.h:74` | `struct TypeName<std::string>` | 아니오 (노드 이름은 `basic_string`) |

🔵 불일치의 원인은 두 가지이고 둘 다 재현된다.
① 노드 `name` 이 **정규화된 canonical 이름**이라 소스에 쓰인 별칭과 다르다 (`basic_string` vs `string`,
`unique_ptr` vs `VertexLayoutUPtr`).
② `std::` 타입의 `source_location` 은 표준 헤더가 아니라 **이 저장소의 첫 사용 지점**이다.
따라서 **경로만 보고 1st-party 를 가르면 안 된다.** E절에서 네임스페이스를 기준으로 쓴 이유다.

---

## G. 스키마에 안 들어가는 관찰 — 기록만

이 언어·엔진에서만 나오는 구조로, 지금 스키마에 자리가 없는 것들이다.
**여기에 적힌 것을 근거로 필드를 추가하지 않는다.** 나중에 사용자가 판단한다.

핸드오프 §5 가 세운 💭 예상 4건을 하나씩 확인했다. **2건은 빗나갔고 2건은 맞았다.**

| 관찰 | 출현 횟수 | 왜 정적 분석이 놓치나 |
|---|---|---|
| **`src/reflect` 자기등록 예상은 빗나갔다.** 🔵 `src/reflect/registry.h` 주석이 명시한다 — "등록은 명시적 함수 호출이다(P-1a). 정적 초기화 self-registration 을 쓰지 않는다 - STATIC 아카이브에서 오브젝트가 탈락해 조용히 빈 스키마를 낳기 때문이다." 등록 매크로도 `__attribute__((constructor))` 도 없다 (grep 결과 헤더가드만 걸림) | 0 | 해당 없음 — 이 저장소는 그 함정을 의도적으로 피했다 |
| **다만 리플렉션의 진짜 간극은 다른 데 있다.** 🔵 `src/reflect/field_desc.h:28-29` 가 `std::function<nlohmann::json(const void *)> Get;` / `std::function<void(void *, const nlohmann::json &)> Set;` 를 들고 있다 | 2 (필드), 영향은 `ComponentDesc` 전량 | **`void *` 로 타입이 지워진다.** "이 `ComponentDesc` 가 어떤 C++ 타입을 기술하는가" 라는 간선이 타입 수준에 존재하지 않는다. 정적 분석이 볼 수 있는 것은 `void*` 뿐이다 |
| **`ComponentDesc` 는 문자열 키로 조회된다.** 🔵 `Registry::Find(const std::string &key)`, `ComponentDesc::Name` 이 `"TopdownShooter::Entity::EnemyTuning"` 같은 문자열이다 | `mDescs` / `mAliasToName` 2개 맵 | 타입 참조가 아니라 **문자열 리터럴**이 결합을 만든다. 게다가 `Aliases` 로 옛 이름 리다이렉트까지 한다. 어느 정적 분석기도 이 간선을 못 본다 |
| **`src/fsm` — 전이 그래프가 런타임 비트마스크라 정적 분석이 못 본다.** 🔵 측정: 파일은 `fsm_state.h` `state_machine.h` 2개뿐, `src/fsm/*.cpp` **없음**, `compile_commands.json` 의 `src/fsm` 번역단위 **0건**, clang-uml 노드 **0건**. 🔵 선언 확인: `IFsmState::GetStateFlag()` / `GetTransitFlag()` 가 `uint64_t` 비트를 반환하고 `StateMachine::TryTransitImpl` 이 둘의 AND 로 전이 허용을 판단한다(`src/fsm/fsm_state.h:50-56`, `src/fsm/state_machine.h:167`) | 노드 0 / 간선 0 | **상태 전이 간선 `A -> B` 가 그래프에 존재하지 않는다.** 전이 가능 여부가 타입 관계가 아니라 **런타임 정수 비트 연산**이기 때문이다. 핸드오프 §5 가 예상한 부류가 맞다 — 다만 함수 포인터가 아니라 비트마스크다. 추가로 `StateMachine<TState,TOwner>` 는 `Scene::Component` 를 상속하는데도 노드가 0건이다: TU 가 없어 템플릿 실체화 지점이 스캔에 안 들어온 것으로 보이나 **미확인** |
| **셰이더 예상은 맞았다.** `resources/` 와 `src/shader` 의 셰이더 파일은 C++ 심볼이 아니다 | `src/shader` 노드 2건뿐 (`Shader` 클래스 등) | 셰이더 소스(`.slang`/`.vs`/`.fs`)는 그래프에 아예 없다. 셰이더 uniform 이름 ↔ C++ 문자열 결합도 전부 문자열이다 |
| **Qt / moc 오염 예상은 빗나갔다.** 🔵 `compile_commands.json` 107건에 moc 생성 파일이 없고, `editors/` 타겟이 아예 configure 되지 않았다 | 0 | 해당 없음. `.dot` 에도 Qt 타겟이 없다. 기본 configure 로는 에디터가 꺼져 있다 |
| **`apps/` 가 통째로 빠졌다.** 🔵 `MyApp` 네임스페이스 노드 0건. 핸드오프가 준 최소 설정의 `glob: ["src/**/*.cpp", "src/**/*.h"]` 이 `apps/` 를 안 잡는다. `include.paths` 에 `"apps"` 가 있어도 **glob 이 먼저 잘라낸다** | 노드 0 / `.dot` 기준 MyApp 타겟은 19개 존재 | 도구 한계가 아니라 **설정 문제**다. 핸드오프가 "처음에는 필터를 걸지 말 것" 이라 해서 원문 그대로 썼다. H절에 남긴다 |
| **`instantiation` 11건 중 8건이 `SJH::Reflect::TypeName<T>` 특수화다** | 11 | 템플릿 특수화가 노드를 불린다. `src/reflect` 가 37노드로 최다인 이유의 상당 부분이다 |
| **`std::` 타입 83건이 노드로 섞여 있다** | 83 / 203 (40.9%) | 표준 라이브러리 타입이 1급 노드로 올라온다. `std::function<void(double,double)>` 처럼 **템플릿 인자까지 박힌 이름**이라 같은 `std::function` 도 시그니처마다 다른 노드가 된다 |

---

## H. 막힌 것

해결하지 못한 채 남긴 것. **추측으로 우회하지 말고 여기에 적는다.**

| 막힌 지점 | 오류 원문 | 시도한 것 | 다음에 해볼 것 |
|---|---|---|---|
| **핸드오프 §1 의 환경 전제가 사실과 달랐다.** 빌드 디렉토리가 하나도 없었다 | `(eval):1: no matches found: build_*` / `ls: build_ninja/compile_commands.json: No such file or directory` | `ls -la` 로 저장소 루트 전량 확인. `build_ninja` · `build_ninja-golden` · `build_ninja-release-golden` 전부 부재 | 해결됨 — `build_cc` 를 새로 configure 했다. 핸드오프 §1 표의 "132개 항목" 은 이번 세션에 재현되지 않는다 |
| **§3 단계 2 의 원문 명령이 실패했다.** vcpkg 툴체인이 빠져 있다 | `CMake Error at cmake/DepsBase.cmake:9 (find_package): Could not find a package configuration file provided by "glm"` (전문은 B절) | 핸드오프가 준 폴백(`cmake -S . -B build_ninja --graphviz=...`)은 **쓸 수 없었다.** 그 폴백은 `build_ninja` 에 이미 툴체인이 캐시돼 있다는 전제인데 디렉토리 자체가 없었다 | 해결됨 — `CMakePresets.json` 의 `base` 프리셋이 주는 두 값만 더해 `build_cc` 로 돌렸다: `-DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake` 와 `-DVCPKG_MANIFEST_INSTALL=ON`. 골든 디렉토리는 건드리지 않았다 |
| `rm -rf build_cc` 가 거부됐다 | `Permission to use Bash with command ... has been denied.` | 대신 `cmake --fresh` 로 캐시를 무효화했다 (CMake 4.2.3 지원) | 해결됨 |
| **clang-uml 1차 실행 실패 — 컴파일러 빌트인 헤더 부재** | `ERROR: Failed to generate class diagram 'full_class' due to following issues:` / ` - [FATAL] include/GLFW/glfw3.h:137: 'stddef.h' file not found` | 원인 실측: `compile_commands.json` 은 AppleClang(`/usr/bin/c++`, resource dir `.../clang/21`) 기준인데 clang-uml 은 Homebrew libclang 22 로 파싱한다 | 해결됨 — `.clang-uml` 의 `add_compile_flags` 에 `-resource-dir=/opt/homebrew/opt/llvm@22/lib/clang/22` 추가 |
| **clang-uml 2차 실행 실패 — macOS SDK 프레임워크 부재** | ` - [FATAL] include/GLFW/glfw3.h:147: 'OpenGL/gl.h' file not found` / ` - [NOTE] ... did not find header 'gl.h' in framework 'OpenGL' (loaded from '/System/Library/Frameworks')` | AppleClang 은 sysroot 를 암묵적으로 주지만 Homebrew clang 은 안 준다 | 해결됨 — `add_compile_flags` 에 `-isysroot /Applications/Xcode.app/.../MacOSX.sdk` 추가. 3차 실행 성공(42.58s, exit 0) |
| **`apps/` 가 수집되지 않았다 (미해결)** | 오류 없음. 조용히 0건 | 핸드오프 §3 단계 4 가 준 최소 설정을 **원문 그대로** 썼다. `glob` 이 `src/**` 만 잡아 `apps/**` TU 가 후보에 안 든다. 설정을 임의로 넓히는 것은 "처음에는 필터를 걸지 말 것" 과 별개로 핸드오프가 준 설정을 바꾸는 일이라 **하지 않았다** | `glob` 에 `apps/**/*.cpp` 를 더해 재수집. 그러면 `MyApp::` 19개 타겟 상당의 클래스가 들어와 노드 수가 크게 는다. **사용자 판단 대기** |
| **`src/fsm` 노드가 0건이다 (미해결)** | 오류 없음 | `src/fsm` 은 헤더 2개뿐이고 `compile_commands.json` 에 대응 `.cpp` TU 가 없다 | 💭 60 — 순수 템플릿 헤더가 실체화 없이는 안 잡히는 현상으로 보이나 **확인하지 못했다** |
| **Windows 산출물 (범위 밖)** | 해당 없음 | 핸드오프 §1 이 범위 밖으로 못박았다. mingw-w64 툴체인 파일이 저장소에 없고 호스트가 macOS 다 | Track C Phase 6 을 별도로 진행할 때 |
| **Doxygen 대타 (단계 5)** | 해당 없음 | **실행하지 않았다.** 단계 4 가 최종적으로 성공했으므로 조건("단계 4가 막혔을 때만")이 성립하지 않는다 | 필요 없음 |

**작업 중 저장소에 생긴 변경 (전부 gitignore 처리, 커밋하지 않음):**

- `.gitignore` 에 3줄 추가: `build_cc/`, `out/codegraph-raw/`, `.clang-uml`
- 새 파일 `.clang-uml` (저장소 루트, 미추적)
- 새 디렉토리 `build_cc/`, `out/codegraph-raw/` (미추적)
- 🔵 골든 디렉토리는 애초에 존재하지 않았고, 어떤 기존 빌드 디렉토리도 건드리지 않았다.

---

## I. `normalize.py` 파서 설계에 대한 권고

**코드를 쓰지 않는다.** 위 A~H 에서 관찰된 것만 근거로, 파서가 마주칠 것을 문장으로 적는다.
확신도는 🔵/🟡/💭 + 정수를 붙이고, 🔵 는 이 세션에서 실제로 돌린 명령의 출력만 인정한다.

- 🔵 **파서는 두 개가 아니라 두 층이다.** `cmake --graphviz` 는 CMake 타겟 층, clang-uml 은 C++ 클래스 층이고, 둘 사이에 공통 식별자가 없다. `.dot` 노드는 타겟 이름(`sjhopengl_render`), clang-uml 노드는 네임스페이스 이름(`SJH::Scene::Component`) 이다. 두 층을 잇는 유일한 실측 가능한 다리는 **파일 경로**다 — clang-uml 노드의 `source_location.file` 이 `src/render/...` 이면 `sjhopengl_render` 타겟 소속이라고 볼 수 있다. 다만 `.dot` 쪽에 경로가 없으므로 (E절) 그 대응표는 `compile_commands.json` 의 `output` 필드(`src/render/CMakeFiles/sjhopengl_render.dir/...`)에서 따로 만들어야 한다. 🔵 그 필드가 실제로 있음을 `02-cc-sample.txt` 에서 확인했다.

- 🔵 **`type` 문자열을 그대로 enum 에 옮기면 안 된다.** D절이 핵심이다. clang-uml 의 `aggregation`(140건)은 값 멤버라 `composition` 쪽 뜻이고, `association`(26건)은 포인터 멤버라 `aggregation` 쪽 뜻이다. 낱말이 같아서 오히려 위험하다 — 무심코 항등 매핑을 쓰면 166건이 조용히 틀린 칸에 들어가고, 오류가 나지 않아 발견되지도 않는다.

- 🔵 **상속과 인터페이스 구현을 간선만으로 가를 수 없다.** `extension` 21건이 둘을 합쳐 놓았다. `inheritance` 와 `realization` 을 나누려면 파서가 **대상 노드를 조회해 `is_abstract` 를 읽어야** 한다. 즉 간선 변환이 노드 테이블에 의존한다 — 간선을 스트리밍으로 처리하는 설계는 못 쓴다. 노드를 먼저 전량 적재한 뒤 간선을 도는 2-패스가 필요하다.

- 🔵 **간선에 `file`/`line` 이 없다 (F절).** `codegraph.json` 이 간선에 요구하는 필드를 clang-uml 은 주지 않는다. 다만 절반은 복구할 수 있다: 간선의 `label` 이 멤버 이름이고(166/411건에 `label` 이 있다), 출발 노드의 `source_location.file` 이 그 멤버가 선언된 파일이다. 🟡 70 — 파일 안에서 `label` 문자열을 찾아 줄을 특정하는 방식은 대체로 통하겠지만, 같은 이름 멤버가 여러 번 나오거나 `label` 이 없는 243건에는 안 통한다. `label` 없는 간선(`extension`/`instantiation`/`containment`, `dependency` 다수)은 **줄 근거를 만들 방법이 아예 없다.**

- 🔵 **경로로 서드파티를 거르면 안 된다 (F절).** `std::` 타입 83건의 `source_location.file` 이 표준 헤더가 아니라 이 저장소의 첫 사용 지점(`src/reflect/meta.h:27` 등)을 가리킨다. 경로 기준 필터는 이것들을 1st-party 로 오인한다. **`namespace` 필드를 기준으로 써야 한다.** 이번 계량은 그렇게 했다.

- 🔵 **중첩 타입은 `name` 이 `Outer##Inner` 다.** 구분자가 `::` 가 아니라 `##` 이고, 바깥 클래스가 `namespace` 필드에 들어가지 않는다. `is_nested == true` 이면 `##` 로 쪼개 마지막 조각으로 대조해야 L3 가 성립한다. **표본 10건으로는 이 함정이 안 잡혔다** — 전수(203건)로 재고서야 5건이 드러났다. 파서 검증은 표본이 아니라 전수로 할 것.

- 🔵 **노드 이름은 canonical 이라 소스 텍스트와 다르다.** `basic_string` vs `std::string`, `unique_ptr` vs 프로젝트 별칭 `VertexLayoutUPtr`. 인용 검증이 "그 줄에 그 이름이 있는가" 로 문자열 대조를 하면 1st-party 는 10/10 통과하지만 `std::` 타입은 대부분 실패한다. 대조 규칙을 노드 종류별로 나눠야 한다.

- 🔵 **`.dot` 라벨은 한 줄이 아니다.** `"sjhopengl_render\n(SJH::render)"` 처럼 `\n` 과 별칭이 박혀 온다. 별칭이 없는 타겟(`_MyApp_`, `sb7`, `glfw3`)도 섞여 있으므로 두 형태를 모두 받아야 한다. 또한 라벨 자리에 컴파일 플래그(`-framework Cocoa`)나 절대경로(`.../OpenGL.framework`)가 그대로 들어온 노드가 5건 있다.

- 🔵 **`.dot` 부속 파일 119개는 노드 번호를 주 파일과 공유한다.** 부속 파일을 독립 파싱하면 `node8` 이 충돌한다. 🔵 **전수 대조했다 — 주 파일 하나만 읽으면 충분하다.** 부속 파일 119개 전량을 검사해, 주 파일에 없는 간선 **0건** · 노드번호와 라벨이 어긋난 것 **0건** 이었다. 부속 파일은 주 파일의 완전한 부분집합이다. 원문은 `out/codegraph-raw/10-dot-sidefile-subset-check.txt`.

- 🔵 **링크 가시성(PUBLIC/INTERFACE/PRIVATE)이 `style` 로만 구분된다.** 속성 없음 125 / `dashed` 71 / `dotted` 50. 6종 enum 에는 이 축이 없어 세 개가 전부 `dependency` 로 뭉개진다. 💭 65 — 모듈 경계 그림에서는 이 축이 실제로 가장 쓸모 있어 보이는데, 스키마에 자리가 없다는 사실만 적어 둔다. 판단은 사용자 몫이다.

- 🔵 **`instantiation`(11) · `friendship`(2) · `containment`(5) 는 갈 곳이 없다.** 합계 18건이다. 버릴지 `dependency` 로 접을지는 사용자 결정이다. 🟡 85 — `friendship` 은 C# 쪽에 대응물이 **없다.** 짝 보고서 `samples/csharp-unity/OBSERVATION.md` D절을 이번 세션에서 읽어 확인했다: C# 도구는 `inherit`(64) · `realize`(70) · `assoc`(285) **3종만** 낸다. `instantiation` · `containment` 도 대응물이 없다. 🟡 인 것은 그 측정을 내가 돌린 것이 아니라 짝 보고서를 인용했기 때문이다. **반대 방향의 비대칭도 있다** — C# 쪽에는 C++ 에 없는 미대응 항목이 셋 더 있다(프리팹 GUID 간선, `UnityEvent` 메서드명 472건, `[SerializeField]` 27건).

- 🔵 **이번 산출물은 `apps/` 가 빠진 반쪽이다 (H절).** `MyApp::` 노드 0건이고, `.dot` 기준으로 MyApp 계열 타겟이 19개 있다. 파서 설계는 이 상태로 진행해도 형태 파악에는 지장이 없지만, **계량 수치를 최종본으로 쓰면 안 된다.** `glob` 을 넓혀 재수집할지가 사용자에게 남은 결정이다.

- 💭 55 — 리플렉션·문자열 키 결합(G절)은 파서 문제가 아니라 **그래프 자체의 구멍**이다. `normalize.py` 가 아무리 정확해도 `ComponentDesc` 문자열 키가 만드는 결합은 산출물에 없으므로 복구할 수 없다. 이 저장소의 그래프를 읽는 사람이 그 구멍의 존재를 알아야 한다는 것만 적어 둔다.
