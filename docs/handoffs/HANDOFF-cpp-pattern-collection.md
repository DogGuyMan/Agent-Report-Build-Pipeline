# HandOff — C++ 저장소 패턴 수집 (Track C 선행 작업)

> 작성일: 2026-08-27
> 인계 대상: **C++ 저장소 안에서 실행되는 Claude Code Agent**
> 대상 저장소: `$GRAPHICS_REPO`
> 상위 문서: `$REPO_ROOT/docs/handoffs/HANDOFF-codebase-wiki.md` (Track C)
> 짝 문서: `HANDOFF-unity-pattern-collection.md` (C# / Unity 쪽 같은 작업)

---

## 0. 목적 — 이것부터 읽어라

> **`normalize.py` 를 쓰기 위한 재료를 모아 오는 것이 전부다. `normalize.py` 를 쓰는 것이 아니다.**

Track C §12 가 이 순서를 못박았다.

> "`.dot` 파일이 나오면 그 내용을 사용자에게 보여주고, 그것을 기준으로 `normalize.py` 의 첫 파서를
> 설계하라. **스키마를 추측으로 먼저 짜지 말 것** — 실제 산출물을 보고 맞추는 것이 순서다."

따라서 이 작업의 산출물은 **원시 도구 출력 + 고정 형식 관찰 보고서** 두 가지이고, 코드는 없다.

### 이 작업이 끝났다고 말할 수 있는 조건

1. `out/codegraph-raw/` 에 원시 산출물이 있다.
2. `$REPO_ROOT/docs/handoffs/samples/cpp/` 에 관찰 보고서와 표본이 복사돼 있다.
3. 관찰 보고서의 **D절(간선 종류 대응표)과 F절(file/line 실재 여부)이 채워져 있다.** 이 둘이 비면
   `normalize.py` 를 설계할 수 없으므로 작업이 끝난 것이 아니다.

### 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| 외부 의존을 전이로 펼치는 것 (`extern/` 안의 하위 의존) | Track C §2-1 (C-9) 위반. 아래 §2-3 참조 |
| 외부 라이브러리를 CMake 타겟 단위로 쪼개 노드로 만드는 것 | 같은 이유. **라이브러리 이름 노드 하나**로 접는다 |
| `normalize.py` 를 쓰는 것 | 이 작업의 산출물이 아니다. 두 언어 보고서가 모두 도착한 뒤에 쓴다 |
| `codegraph.json` 스키마를 고치거나 `kind` enum 을 늘리는 것 | **8종 고정**(C-10, 2026-08-27 확장: 6종 + `instantiation` + `friendship`). 관찰만 적고 판단은 사용자 |
| 주 빌드 구성을 바꾸는 것 | 아래 §2 안전 규칙 |
| 산출물을 요약·정리해서 보고하는 것 | 파서는 **원문 형태**를 보고 쓰인다. 손댄 표본은 파서를 틀리게 만든다 |

---

## 0-1. 진행 상황 (🔵 2026-08-27 — 이 절의 수치는 전부 실행한 명령의 출력)

> **수집은 끝났다.** §0 의 완료 조건 셋을 전부 만족한다.
> 원시 산출물 `out/codegraph-raw/`(2.4 MB), 관찰 보고서 `samples/cpp/OBSERVATION.md`(A~I 채움),
> D절·F절 모두 채워져 있다.

### 단계별 결과

| 단계 | 결과 | 비고 |
|---|---|---|
| 1 환경 | ✅ | `00-env.txt`. clang-uml 은 미설치였고 이 작업에서 `brew install clang-uml` → **0.6.3** |
| 2 `cmake --graphviz` | ✅ | `01-modules.dot` + **부속 파일 119개**. 노드 70 / 간선 246 |
| 3 `compile_commands.json` | ✅ | **107 항목** (apps 54 + src 53). 필드는 `command`·`directory`·`file`·`output` |
| 4 clang-uml | ✅ (3차 시도) | `full_class.json` 834 KB. 노드 **203** / 관계 **411**. 1·2차 실패 원인은 §H |
| 5 Doxygen | 실행 안 함 | 단계 4가 성공했으므로 조건("단계 4가 막혔을 때만") 불성립 |
| 6 관찰 보고서 | ✅ | A~I 채움 + E-3(C-9 축약) + F-2(전수 대조) 추가 |

### 산출물 (§4 목록 대비)

`samples/cpp/` 에 `OBSERVATION.md` · `shapes/node.json` · `shapes/edge-<kind>.json`(**7종**) ·
`shapes/module.dot.txt` · `external-nodes.tsv` · `counts.tsv` 전량 있다.
`out/codegraph-raw/` 에는 추가로 `07-external-touch.txt` · `08-external-collapse-simulation.txt` ·
`09-fileline-census-full.txt` · `10-dot-sidefile-subset-check.txt` · `12-r7-primitive-check.txt` 가 있다.

### ⏳ C++ 쪽 미완 — 나중에 완료해야 한다 (2026-08-27 사용자 명시)

C# 쪽은 `roslyn-dump` → `normalize_csharp()` 가 완주하며 **probe 실측과 6개 항목이 전부
대사됐다.** C++ 쪽은 그에 해당하는 마감이 아직 없다. **아래를 끝내야 "C++ 완료" 다.**

| # | 미완 항목 | 무엇이 문제인가 |
|---|---|---|
| 1 | **관찰 보고서가 구본과 신본이 섞여 있다** | D절(간선 대응표)·I절(파서 권고)이 **구본 `full_class.json`(203/411)** 기준으로 쓰였다. E-4·F-3 만 재수집본(318/671)으로 덧붙었다. **한 문서 안에서 두 기준이 공존한다** |
| 2 | **D절이 C-13 이전에 쓰였다** | `instantiation`·`friendship` 을 "대응시킬 수 없는 것" 으로 분류해 뒀으나 C-10 으로 자리가 생겼다. `containment` 는 C-14 로 버림 확정 |
| 3 | **I절의 간선 `file`/`line` 권고가 무효다** | C-11 → C-13 번복으로 `members[]` 구조 조회가 정본이 됐다. I절은 여전히 "label 휴리스틱" 을 논한다 |
| 4 | **재수집본 기준 대사(對査)가 없다** | C# 은 6개 항목이 probe 와 일치함을 확인했다. C++ 은 `codegraph.json`(191/417)이 `full_class_all.json`(318/671)에서 나온 경위를 수치로 대조한 적이 없다 |
| 5 | **`apps/_MyApp_` 모듈 이름과 `TopdownShooter` 네임스페이스의 불일치** | 모듈은 폴더(`apps/_MyApp_`), 네임스페이스는 `TopdownShooter` 다. 그래프를 읽는 사람이 헷갈린다 |

**우선순위는 1·3이다** — 다음 세션이 낡은 절을 정본으로 읽으면 파서를 틀리게 고친다.

---

### 이 핸드오프의 범위를 넘어 진행된 것

역방향 참조(Track C §1 7b)가 **별도 갈래로 진행 중**이다 — `HANDOFF-clangd-reverse-refs.md`.
엔진은 `clangd`(E6, stdio JSON-RPC 직접), 전수 확정, **E5(libclang)는 이 프로젝트에서 보류**.
🔵 1차 심볼 102개 전수 = 역참조 **1,767건**, 산출물 `out/codegraph-raw/11-reverse-refs-cold.json`.
**이 핸드오프의 수집 결과(clang-uml 의 `source_location`)가 그 입력이다** — 두 갈래가 위치로 조인된다.

---

## 1. 상위 문서의 환경 전제가 이 저장소와 다르다 — 실측 정정

Track C §4 는 다음을 전제했다. **전부 이 저장소에 없다.**

| Track C §4 의 전제 | 이 저장소의 실측 (2026-08-27) |
|---|---|
| `build-mac/` · `build-win/` 이 있다 | 없다. 실제는 `build_ninja` · `build_ninja-golden` · `build_ninja-release-golden` |
| `build-cc/` 를 새로 만들어야 한다 | **불필요할 수 있다.** 아래 §3 참조 |
| `toolchain/mingw-w64.cmake` 가 있다 | **없다.** mingw-w64 크로스빌드 환경 자체가 이 저장소에 없다 |
| Windows 는 MSVC 를 쓴다 | 맞다. `CMakePresets.json` 의 `base-msvc` 프리셋이 `hostSystemName == Windows` 조건부로 있다 |
| `CMAKE_EXPORT_COMPILE_COMMANDS` 를 켜야 한다 | **이미 켜져 있다.** `base` 프리셋의 `cacheVariables` 에 `"ON"` |

**따라서 Track C 의 Phase 0·1 은 이 저장소에서 이미 충족돼 있다.** 확인만 하고 넘어간다.

> ⚠ **아래 원문은 틀렸다. 취소선으로 남기고 실측을 옆에 적는다.**
>
> ~~🔵 실측 — `build_ninja/compile_commands.json` 이 존재하며 **132개 항목**을 담고 있다.~~

🔵 **2026-08-27 재측정 — 수집 세션 시작 시점에 이 저장소에는 빌드 디렉토리가 하나도 없었다.**

```
$ ls -d build_*
zsh: no matches found: build_*
$ ls -l build_ninja/compile_commands.json
ls: build_ninja/compile_commands.json: No such file or directory
```

따라서 "Track C 의 Phase 0·1 은 이미 충족돼 있다" 는 위 서술도 성립하지 않는다. 새로 configure 했고,
**§3 단계 2 의 원문 명령은 실패한다**(vcpkg 툴체인 누락 → `find_package(glm)` 에러).
폴백으로 제시된 `cmake -S . -B build_ninja --graphviz=...` 도 쓸 수 없었다 —
그 폴백은 `build_ninja` 에 툴체인이 이미 캐시돼 있다는 전제인데 디렉토리 자체가 없었다.

**실제로 통한 것**: `CMakePresets.json` 의 `base` 프리셋이 주는 두 값을 더한 것.

```bash
cmake --fresh -S . -B build_cc -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" \
  -DVCPKG_MANIFEST_INSTALL=ON \
  --graphviz=out/codegraph-raw/01-modules.dot
```

🔵 **이후 `cc` 프리셋이 저장소에 추가됐다.** 다음 세션부터는 이 한 줄이면 된다:

```bash
cmake --preset cc --graphviz=out/codegraph-raw/01-modules.dot
```

`ninja`(Debug)를 상속하고 이름만 `cc` 라서 `base` 의 `build_${presetName}` 규칙이 `build_cc` 를 만든다.
🔵 항목 수는 **132가 아니라 107** 이다. 첫 항목이 `src/texture/texture.cpp` 인 것은 맞다.

### 🔵 2026-08-27 3차 측정 — `build_ninja` 와 `build_cc` 가 둘 다 있는 상태에서 다시 쟀다

수집 세션 이후 저장소에 두 빌드 디렉토리가 모두 생겼다. **그 상태로 재측정한 결과다.**

| 항목 | 값 |
|---|---|
| 빌드 디렉토리 | `build_cc` · `build_ninja` **2개** (골든 2종은 **현재 없다**, 아래 §2 참조) |
| `build_cc/compile_commands.json` | **107 항목** (273,855 바이트) |
| `build_ninja/compile_commands.json` | **107 항목** (274,977 바이트) |
| 두 파일의 `file` 집합 | **동일.** 차이는 `directory`·`output` 경로뿐 |
| 두 캐시의 옵션 | **완전 동일** — `diff` 0줄 |
| 항목 분포 | `apps` 54 + `src` 53 |

**132 → 107 의 원인을 특정했다.** 🔵 현재 캐시는 이렇다:

```
ENABLE_TESTING:BOOL=OFF
SJH_BUILD_EDITOR:BOOL=OFF
SJH_GOLDEN_CAPTURE:BOOL=OFF

추적 .cpp:  test/ 23개 · editors/ 1개  =  24
차이:       132 - 107                  =  25
```

🟡 75 — **테스트·에디터가 켜져 있던 구성으로 보인다.** 24가 설명되고 1이 남는다.
확정하려면 `ENABLE_TESTING=ON` 으로 재configure 해야 하는데 **사용자 저장소 상태를 바꾸는 일이라
하지 않았다.** 다음 세션이 항목 수 불일치를 보면 **도구 결함이 아니라 옵션 차이부터 의심할 것.**

⚠ **§3 단계 2 의 폴백은 이제 쓸 수 있다.** `build_ninja` 에 vcpkg 툴체인이 캐시돼 있으므로
`cmake -S . -B build_ninja --graphviz=...` 가 성립한다. 위 "쓸 수 없었다" 는 **수집 세션 시점의
기록**이며, 그 시점에는 디렉토리 자체가 없었다.

**함정 2 의 폴백 경로가 이 저장소에는 없다.** Track C §6 함정 2 는 "MSVC 플래그 파싱이 막히면
mingw-w64 툴체인으로 우회하라"고 했으나 그 툴체인 파일이 없다. **Windows 산출물 수집(Track C
Phase 6)은 이 작업의 범위 밖이다.** macOS 산출물만 모은다.

### 규모 실측 (2026-08-27)

| 항목 | 값 |
|---|---|
| 추적 중인 `.cpp`/`.cc`/`.cxx` | 127개 |
| 추적 중인 `.h`/`.hpp` | 329개 |
| `compile_commands.json` 항목 | ~~132개~~ → 🔵 **107개** (apps 54 + src 53) |
| `src/` 하위 디렉토리 | ~~21개~~ → 🔵 **19개** (`buffer` `common` `diagnostics` `fsm` `input` `layout` `material` `object` `playable` `program` `reflect` `render` `resource_registry` `scene` `shader` `sprite` `text` `texture` `timer`) |
| `extern/` | 서브모듈 2개 — `Effekseer`, `sb7code` |
| Graphviz / CMake / Python | 15.1.1 / 4.2.3 / 3.14.6 |
| `ninja` / `doxygen` | 설치됨 |
| **`clang-uml`** | ~~미설치~~ → 🔵 **0.6.3 설치 완료** (libclang 22.1.8). 이 작업의 유일한 신규 설치였다 |
| `toolchain/mingw-w64.cmake` | 🔵 **없다. `toolchain/` 디렉토리 자체가 없다** (`find . -name 'mingw*'` 0건) |
| `clangd` | 🔵 `/usr/bin/clangd` **21.0.0**(Apple) + llvm@22 번들 **22.1.8**. 역방향 갈래가 쓴다 |

---

## 2. 안전 규칙 — 어기면 사용자의 테스트 기준선이 깨진다

**`build_ninja-golden` 과 `build_ninja-release-golden` 을 건드리지 말 것.**
이름이 말하듯 골든 이미지 대조용 빌드 디렉토리다. 여기에 `cmake` 를 다시 돌리면 사용자의
회귀 검증 기준선이 바뀔 수 있다. **읽기만 한다.**

> 🔵 **2026-08-27 3차 측정 — 이 두 디렉토리는 현재 존재하지 않는다.**
> 그러나 `CMakePresets.json` 에 `ninja-golden` · `ninja-release-golden` · `msvc-golden` ·
> `msvc-2022-golden` 프리셋이 남아 있어 **언제든 다시 생긴다.** 규칙은 그대로 유지한다.

- 새 빌드 디렉토리를 만들 때는 `build_cc` 라는 이름을 쓴다. 기존 어느 이름과도 겹치지 않는다.
- `.gitignore` 에 `out/codegraph-raw/` 와 `.clang-uml` 을 추가한다. 안 하면 생성물이 커밋된다.
  🔵 **`build_cc/` 는 추가할 필요가 없다** — `.gitignore:46` 에 이미 `build_*/` 가 있다.
  수집 세션이 넣은 `build_cc/` 한 줄(192행)은 **중복이며 지워도 된다.**
- 이 저장소는 vcpkg 매니페스트 모드를 쓴다(`base` 프리셋이 `VCPKG_MANIFEST_INSTALL: ON`).
  **새 빌드 디렉토리를 configure 하면 vcpkg 가 의존성 설치를 다시 확인한다.** 바이너리 캐시가
  있으면 빠르지만 처음이면 오래 걸릴 수 있다. 시간이 걸려도 정상이니 중단하지 말 것.

---

## 2-3. 외부 의존 처리 — Track C §2-1 (C-9) 의 C++ 적용

> **2026-08-27 사용자 확정.** 상위 규칙은 `HANDOFF-codebase-wiki.md` §2-1 에 있다.
> 여기에는 **C++ 에서 그 규칙이 무엇을 뜻하는지**만 적는다. 규칙 자체를 바꾸지 말 것.
> 짝 문서인 `HANDOFF-unity-pattern-collection.md` §2-2 가 같은 규칙의 C# 적용이다.

### 규칙 넷 (재게)

| # | 규칙 |
|---|---|
| **R1** | 전이 확장을 하지 않는다. 사용자 코드가 **직접 닿는** 외부 라이브러리만 노드가 된다 |
| **R2** | 외부 라이브러리 하나 = 노드 하나. 입도는 **라이브러리·서브모듈 이름** |
| **R3** | 모든 외부 노드를 `__external__` 그룹 하나에 모아 **외딴 섬**으로 둔다 |
| **R4** | 간선은 **사용자 코드 → 외부 단방향만**. 외부→외부, 외부→사용자는 만들지 않는다 |


### 규칙 둘 추가 (Track C §2-1 "규칙 둘 추가" 와 동일)

| # | 규칙 |
|---|---|
| **R5** | **컨테이너·스마트포인터 투과.** `std::vector<T>` `std::unique_ptr<T>` `std::shared_ptr<T>` `std::array<T,N>` `std::map<K,V>` 등은 노드로 만들지 않고 `A -> Wrapper<T>` + `Wrapper<T> -> T` 를 `A -> T` 로 접는다 |
| **R6** | 섬으로 들어가는 간선에 `constraint=false`. 섬은 시각 구분 |
| **R7** | **원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.** `int` `float` `bool` `char` 등 내장 타입은 대상이 `(STL) std` 라도 간선을 만들지 않는다 |

**적용 순서 고정: R5 -> R7 -> R2 -> R1 -> R4 -> R3 -> R6.**

> ⚠ **이 문서에 "적용 순서 고정" 이 두 번 적혀 있었고 내용이 달랐다**(R7 포함본과 미포함본).
> R7 이 나중에 추가된 규칙이므로 **R7 포함본이 정본**이고, 미포함본은 삭제했다.

### 🔵 R7 의 C++ 판정 — 해당 없음 (2026-08-27 실측)

문서가 예상한 대로 **"해당 없음" 이 답이다.** 근거는 `out/codegraph-raw/12-r7-primitive-check.txt`.

```
element type 분포: {'class': 195, 'enum': 8}
원시/내장 타입 이름을 가진 노드: 없음 (0건)
끝점이 elements 에 없는 간선: 0
```

🔵 **clang-uml 은 원시 타입을 element 로 승격하지 않는다.** `int` `float` `bool` `GLuint` 등이
노드로 존재하지 않으므로 **간선도 애초에 생기지 않는다.** 따라서 `(STL) std` 접촉은
**R7 전후가 동일**하고, C# 의 274 → 9 같은 감소가 C++ 에는 없다.

💭 70 — C# 의 `object`/`System.Enum` 같은 **보편 기반 타입이 C++ 에 없다**는 것이 근본 이유로 보인다.
C++ 에는 모든 타입이 상속하는 루트가 없고, 원시 타입은 클래스가 아니다.
**이 비대칭 자체가 두 언어 보고서를 나란히 놓을 때 드러나는 관찰이다.**

⚠ **R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다.** 🔵 이 저장소 실측 8건 —
`RenderUnit --mesh--> Mesh`, `ComponentDesc --Fields--> FieldDesc`,
`TextRenderer --mGlyphs--> Actor` 등이 전부 `std::unique_ptr` / `std::vector` 래퍼를
2홉으로 거쳐야만 보인다. 근거와 전체 목록은 Track C §2-1.

### C++ 에서 "외부" 는 무엇인가

| 종류 | 노드 이름 | 이 저장소의 예 |
|---|---|---|
| `extern/` 서브모듈 | 서브모듈 디렉토리 이름 | `Effekseer`, `sb7code` |
| vcpkg · 시스템 라이브러리 | 라이브러리 이름 | 단계 2·4 에서 실측해 채운다 |
| 표준 라이브러리 | `(STL) std` 하나로 접는다 | — |
| Qt | `(Qt) <모듈>` 또는 `Qt` 하나 | `apps/_MyApp_` · `editors/` 가 `qt_add_executable` 을 쓴다 |

⚠ **C# 쪽과 대칭이 깨지는 지점이 여기다.** C# 은 `packages-lock.json` 이라는 **선언된 목록**이
있지만 C++ 에는 그런 것이 없다. 대신 **CMake 타겟**과 **소스 경로**가 그 역할을 한다.
따라서 C++ 쪽은 "패키지 이름" 이 아니라 **"서브모듈·라이브러리 이름"** 이 노드 이름이 된다.
**이 차이 자체를 관찰 보고서 C-3 절에 적는다.**

### 단계 2 (`cmake --graphviz`) 의 지시가 이 규칙으로 바뀐다

기존 지시 — "`extern/Effekseer` 가 만드는 타겟(`TestCpp`, `EffekseerSoundOSMixer` 등)이
`.dot` 에 전부 나올 것이다. **지우지 말고 그대로 둔다**" — 는 **유지된다.**
원시 산출물에는 손대지 않는다. 바뀌는 것은 **관찰 보고서에 무엇을 적느냐**다.

관찰 보고서 C-3 · E절에 **접기 전후 두 수를 함께 적는다**:

```
extern/Effekseer 가 만드는 CMake 타겟   N개   ->  외부 노드 1개 (Effekseer)
extern/sb7code   가 만드는 CMake 타겟   M개   ->  외부 노드 1개 (sb7code)
```

`.dot` 의 타겟 이름을 서브모듈로 되돌리는 근거는 **그 타겟의 소스 경로**다.
`compile_commands.json` 의 `file` 필드가 `extern/Effekseer/...` 로 시작하면 그 타겟은
`Effekseer` 로 접힌다.

### 단계 4 (clang-uml) 가 내야 할 것이 하나 늘었다

**사용자 코드가 실제로 닿는 외부 타입의 목록과 접촉 횟수**를 `07-external-touch.txt` 로 낸다.
clang-uml 이 낸 관계에서 `to` 쪽이 `src/` 밖(`extern/`, 시스템 include, Qt)인 것을 세면 된다.
**접기 전후 두 수를 반드시 함께 적는다** (예: 외부 타입 N개 → 외부 노드 4개).

### 🔵 `07-external-touch.txt` 생성 완료 (2026-08-27)

**접기 전후:**

| 항목 | 값 |
|---|---|
| 외부 타입 (접기 전, 실제로 닿는 것만) | **81종** |
| 외부 노드 (접기 후) | **3개** |
| 총 접촉 | **172회** |

| 외부 노드 | 접촉 | 타입 종수 | 간선 종류별 |
|---|---|---|---|
| `(STL) std` | 122 | 75 | aggregation 81 · dependency 41 |
| `glm` | 48 | 4 | aggregation 41 · dependency 7 |
| `Effekseer` | 2 | 2 | dependency 1 · aggregation 1 |

⚠ **clang-uml 산출물의 외부 element 는 101개인데 실제로 닿는 것은 81종이다.**
나머지 20종은 **외부를 거쳐야만 닿는 것**이라 R1(전이 금지)이 제거한다.
`nlohmann-json` 과 `FMOD` 가 여기 해당해 **외부 노드에서 통째로 빠진다** —
`std::function<json(void*)>` 같은 래퍼를 거쳐야만 닿기 때문이다.

**R1 의 "직접 닿는" 을 이 저장소에서 쓴 정의(파일 머리에도 적어 뒀다):**

> clang-uml `relationships` 중 `source` 가 `SJH::`/`MyApp::` 네임스페이스이고
> `destination` 이 그 밖인 간선을 1회 접촉으로 센다. 상속(`extension`)·멤버(`aggregation`/
> `association`)·의존(`dependency`)·중첩(`containment`)·실체화(`instantiation`)·`friendship` 전부 포함.

⚠ **C# 과 기준이 다르다 — 숨기지 않고 적는다.** C# 은 "상속 · 인터페이스 실현 · 필드 타입" 셋을
셌고 **어셈블리** 단위로 귀속시켰다. C++ 은 **네임스페이스** 단위이고 간선 종류가 더 넓다
(`dependency` 41+7건이 C# 기준에는 없다). 🔵 **경로 기준을 쓸 수 없었던 이유**는 관찰 보고서 F절에 있다 —
`std::` 타입 83건의 `source_location.file` 이 표준 헤더가 아니라 **이 저장소의 첫 사용 지점**을 가리킨다.

⚠ **R1 의 "직접 닿는" 을 측정으로 정의하고, 무엇을 썼는지 D절에 적어라.**
C# 쪽은 이렇게 정의했다 — 상속 · 인터페이스 실현 · 필드 타입(제네릭 인자 포함)에서
대상이 사는 어셈블리를 세는 것. C++ 에서는 상속 · 멤버 타입 · (clang-uml 이 준다면)
의존 간선의 대상 헤더 경로가 그에 해당한다.
**두 언어가 다른 기준을 쓰게 되면 그것 자체가 관찰이니 숨기지 말고 적는다.**

---

## 3. 수집 절차

각 단계에 **정지 조건**이 있다. 통과하지 못하면 다음으로 가지 말고, 막힌 내용을 관찰 보고서
H절에 오류 원문 그대로 적는다. **추측으로 우회하지 않는다.**

### 준비

```bash
cd $GRAPHICS_REPO
mkdir -p out/codegraph-raw
printf 'build_cc/\nout/codegraph-raw/\n' >> .gitignore
git rev-parse --short HEAD > out/codegraph-raw/00-commit.txt
```

### 단계 1 — 환경 실측을 파일로 남긴다

```bash
{
  dot -V
  cmake --version | head -1
  python3 --version
  ninja --version
  clang-uml --version || echo "clang-uml: 미설치"
} > out/codegraph-raw/00-env.txt 2>&1
```

**정지 조건:** `00-env.txt` 에 실제 버전 문자열이 있으면 통과. 관찰 보고서 A절에 그대로 옮긴다.

### 단계 2 — 모듈 경계 (`cmake --graphviz`)

CMake 내장 기능이라 추가 설치가 없고, **configure 만 하면 되므로 컴파일이 필요 없다.**
빌드가 깨진 상태에서도 나온다.

```bash
cmake -S . -B build_cc -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  --graphviz=out/codegraph-raw/01-modules.dot
```

vcpkg 때문에 `build_cc` configure 가 실패하면, **기존 `build_ninja` 에 대해 다시 configure** 한다
(골든 디렉토리가 아니므로 허용된다). 🔵 2026-08-27 기준 `build_ninja` 가 실재하고 툴체인이
캐시돼 있으므로 **이 폴백은 지금 쓸 수 있다**:

```bash
cmake -S . -B build_ninja --graphviz=out/codegraph-raw/01-modules.dot
```

**정지 조건:** `01-modules.dot` 이 생기고 안에 실제 타겟 이름이 있으면 통과.

⚠ 이 저장소는 `extern/Effekseer` 가 자체 CMake 타겟을 다수 만든다(`TestCpp`,
`EffekseerSoundOSMixer` 등). `.dot` 에 그것들이 전부 나올 것이다. **지우지 말고 그대로 둔다.**
대신 관찰 보고서 E절에 "제외 기준으로 쓴 경로 패턴" 으로 `extern/` 을 적고, 제외 전후 수를 둘 다 센다.
`normalize.py` 가 어디서 잘라야 하는지가 그 두 수의 차이로 정해진다.

`cmake --graphviz` 는 `.dot` 하나가 아니라 **타겟별 부속 파일도 함께** 만든다
(`01-modules.dot.EditorCommon` 같은 것). 전부 `out/codegraph-raw/` 안에 남긴다.

### 단계 3 — `compile_commands.json` 확인

```bash
ls -l build_cc/compile_commands.json build_ninja/compile_commands.json 2>&1
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d),'entries'); print(d[0])" \
  build_ninja/compile_commands.json > out/codegraph-raw/02-cc-sample.txt
```

**정지 조건:** 항목 수가 0이 아니고 `file` 값이 실제 소스 경로면 통과.

**Ninja Multi-Config 를 쓰지 말 것** — 모든 구성이 한 파일에 섞여 나와 쓸 수 없다.
이 저장소의 프리셋은 단일 구성 Ninja 이므로 그대로 두면 문제없다.

### 단계 4 — clang-uml

```bash
brew install clang-uml
```

`.clang-uml` 설정 파일이 필요하다. **처음에는 필터를 걸지 말 것** — 노드가 몇 개 나오는지가
이후 필터 설계의 기준이 된다. 최소 설정은 이 정도다:

```yaml
compilation_database_dir: build_ninja
output_directory: out/codegraph-raw
diagrams:
  full_class:
    type: class
    glob: ["src/**/*.cpp", "src/**/*.h"]
    include:
      paths: ["src", "apps"]
```

```bash
clang-uml -c .clang-uml -g json
```

> 🔵 **2026-08-27 3차 측정 — 저장소에 실재하는 `.clang-uml` 은 위 최소 설정과 다르다.**
> 수집 세션이 §5-1 문제 1·2 를 풀면서 `add_compile_flags` 두 줄을 더했고
> (`-resource-dir=/opt/homebrew/opt/llvm@22/lib/clang/22`, `-isysroot <MacOSX.sdk>`),
> `compilation_database_dir` 이 `build_ninja` 가 아니라 **`build_cc`** 로 되어 있다.
> **다음 세션은 그 파일을 먼저 읽을 것.** 위 최소 설정을 그대로 덮어쓰면 1·2차 실패가 재현된다.
>
> ⚠ **그 파일에 `probe` 라는 sequence 다이어그램이 하나 더 붙어 있는데, 내용이 이 저장소와
> 무관한 예제 값이다.** 🔵 출처를 확인했다 — `clang-uml --add-sequence-diagram probe` 또는
> `--init` 이 찍어 넣는 **도구 기본 예제**다(`--init` 산출물도 같은 `myproject` 값을 쓴다) — `using_namespace: [myproject]`, `exclude.namespaces: [myproject::detail]`,
> `start_from: main(int,const char **)`. `-g json` 으로 class 만 뽑았기 때문에 산출물에는
> 영향이 없었다. **실제 설정으로 오해하지 말 것.** 제거하거나 실제 값으로 채우는 것은 사용자 판단이다.
>
> 🔵 **`glob` 은 여전히 `[src/**/*.cpp, src/**/*.h]` 라서 `apps/` 갭(§5-1 문제 3)은 그대로다.**

**정지 조건 (Track C Phase 2 와 동일):** JSON 이 나오고 `relationships` 배열에
**`composition` 과 `aggregation` 이 실제로 구분돼 있으면** 통과.

구분이 안 되어 있으면 그 자체가 중대한 발견이다. 관찰 보고서 D절의 "이 도구가 끝내 내지 못하는
enum" 에 적는다. C++ 에서 이 둘을 구분하는 것이 Track C 가 clang-uml 을 고른 이유이므로,
구분이 없으면 도구 선택 자체가 재검토 대상이 된다. **혼자 다른 도구로 갈아타지 말고 보고한다.**

### 단계 5 — Doxygen (단계 4가 막혔을 때만)

clang-uml 이 끝내 안 되면 대타로 쓴다. **빌드 없이 헤더만 파싱**한다.

```
GENERATE_XML = YES
EXTRACT_ALL  = YES
HAVE_DOT     = NO
```

`HAVE_DOT=NO` 인 이유는 그림을 Doxygen 이 아니라 Graphviz P1~P6 로 우리가 그리기 때문이다.
**대신 합성/집약 구분을 잃는다.** 그 손실을 관찰 보고서 D절에 명시한다.

이 저장소에는 이미 `doxygen/` 디렉토리와 `cmake/Doxygen.cmake` 가 있다. **기존 설정을 덮어쓰지 말고**
별도 설정 파일을 만들어 쓴다.

### 단계 6 — 관찰 보고서 작성

```bash
mkdir -p $REPO_ROOT/docs/handoffs/samples/cpp
cp $REPO_ROOT/docs/handoffs/templates/OBSERVATION-template.md \
   $REPO_ROOT/docs/handoffs/samples/cpp/OBSERVATION.md
```

양식의 A~I 절을 채운다. **절 번호와 제목을 바꾸지 않는다** — C# 쪽 보고서와 나란히 놓고 읽어야 한다.

---

## 4. 무엇을 복사해 오고 무엇을 남기나

원시 산출물 전량은 **대상 저장소에 남긴다.** clang-uml JSON 은 클 수 있고, `normalize.py` 설계에는
전량이 필요하지 않다.

```
<C++ 저장소>/out/codegraph-raw/          ← gitignore. 원시 산출물 전량. 여기 남긴다
$REPO_ROOT/docs/handoffs/samples/cpp/
  OBSERVATION.md                          ← 양식 A~I 를 채운 것
  shapes/node.json                        ← 노드 레코드 원문 1건
  shapes/edge-<kind>.json                  ← 간선 레코드 원문, kind 마다 1건씩
  shapes/module.dot.txt                    ← .dot 의 노드·간선 선언 원문 발췌
  external-nodes.tsv                       ← C-9 로 접은 외부 노드 목록 (이름 / 접촉횟수 / 접힌 타겟)
  counts.tsv                               ← E절 계량표를 탭 구분으로 다시 낸 것
```

**표본 파일 하나가 200줄을 넘으면 자르고 잘랐다고 명시한다.** 형태를 보여주는 것이 목적이지
전량 전달이 목적이 아니다.

---

## 5. 이 저장소에서만 나올 것으로 예상되는 것 — 관찰 보고서 G절 후보

💭 55 — 아래는 이 세션에서 파일 목록만 보고 세운 예상이며 **확인된 것이 아니다.**
실제로 나오는지 확인하고, 나오지 않으면 "해당 없음" 으로 적는다.

- `src/reflect/` 가 있다. 최근 커밋이 `리플렉션 레지스트리 SJH::reflect 신설` 이다.
  런타임 등록 기반 구조는 **정적 분석이 간선을 못 본다** — 등록 매크로나 자기등록(self-registration)
  패턴이면 clang-uml 에 의존 간선이 안 잡힌다. 실제로 그런지 확인해 G절에 적는다.
- `src/fsm/` — 상태 전이가 테이블이나 함수 포인터로 되어 있으면 같은 문제가 생긴다.
- `resources/` 와 `src/shader/` — 셰이더 파일은 C++ 심볼이 아니므로 그래프에 아예 없다.
- `apps/_MyApp_` 과 `editors/` 의 Qt 타겟(`qt_add_executable`) — moc 생성 코드가
  `compile_commands.json` 에 섞여 들어오면 노드 수가 부풀 수 있다.

---

## 5-1. 새로 생긴 문제·의문 (🔵 2026-08-27)

수집을 마치고 나서 드러난 것들이다. **해결하지 않고 기록만 한다** — 판단은 사용자 몫이다.

### 문제 1 — `kind` enum 이 8종으로 늘면서 관찰 보고서 D절이 부분적으로 낡았다

§0 금지 표가 이제 **8종 고정**(C-10: 6종 + `instantiation` + `friendship`)이라고 적고 있다.
관찰 보고서 D절은 그 확장 **이전**에 쓰였고, `instantiation`(11건)과 `friendship`(2건)을
**"대응시킬 수 없는 것"** 으로 분류해 뒀다. **이제 자리가 생겼으므로 그 두 행은 재분류 대상이다.**

🔵 그러나 **`containment`(5건)는 여전히 자리가 없다.** 중첩 타입 선언을 뜻하고
(`SJH::Program::UniformBlock -> SJH::Program`), 방향이 안쪽→바깥쪽이며 소유가 아니라 **선언 위치**다.
8종 중 어디에도 그 뜻이 없다. **D절의 "대응시킬 수 없는 것" 표에 이것만 남는다.**

### 문제 2 — §3 단계 4 의 정지 조건이 실측과 어긋난다

문서는 이렇게 적고 있다.

> **정지 조건:** JSON 이 나오고 `relationships` 배열에 **`composition` 과 `aggregation` 이
> 실제로 구분돼 있으면** 통과.

🔵 **문자 그대로 적용하면 불통과다.** clang-uml 0.6.3 은 `composition` 을 **0건** 낸다
(411 간선 전체). 그런데 값/포인터 구분 자체는 살아 있다 — 낱말이 다를 뿐이다:

| clang-uml 이 내는 것 | 실제 의미 | `codegraph.json` enum |
|---|---|---|
| `aggregation` 140건 | **값 멤버** (`std::string detail`) | `composition` |
| `association` 26건 | **포인터·참조 멤버** (`Actor* mOwner`) | `aggregation` |

🔵 `composition` 이 스키마상 존재하지 않는 것은 아니다 — `include.relationships: [composition]` 이
`--validate-only` 를 통과하고, 실제로 돌리면 `elements 203 / relationships 0` 이 나온다.
**다음 세션이 이 정지 조건만 보고 "도구 선택 재검토" 로 가지 않도록 D절을 먼저 읽어야 한다.**

### ✅ 문제 3 — `apps/` 누락 — **2026-08-27 재수집으로 해소됨**

> 🔵 **사용자 승인으로 재수집했다.** `.clang-uml` 에 `full_class_all` 다이어그램을 추가하고
> (`glob: [src/**/*.cpp, apps/*/*.cpp]`) 돌렸다. **구본 `full_class.json` 은 지우지 않았다.**
> 결과 — elements **203 → 318**, relationships **411 → 671**, `TopdownShooter` **74개** 등장.
> 대조 원문 `out/codegraph-raw/13-apps-recollect-census.txt`, 상세는 관찰 보고서 **E-4·F-3**.
>
> **재수집으로 드러난 것 셋:**
> 1. 🔵 앱 네임스페이스는 `MyApp` 이 아니라 **`TopdownShooter`** 다. `MyApp` 은 CMake 타겟 이름이었다.
> 2. 🔵 **`SJH` 가 9개 늘었다** — 앱에서만 쓰이던 엔진 타입. 재수집이 **엔진 그래프의 구멍도 메웠다.**
> 3. 🔵 ⭐️ **`FMOD` 가 R1 을 통과하기 시작했다**(접촉 0 → 5). E-3 이 "R1 이 제거한다" 고 적은 것은
>    `src/` 만 봤을 때의 사실이었다. **R1 통과 여부가 수집 범위에 따라 달라진다.**
>
> 아래 원문은 기록으로 남긴다.

#### (원문 — 재수집 전)

🔵 `MyApp::` 네임스페이스 노드 **0건**이다. 원인은 도구가 아니라 **§3 단계 4 의 최소 설정**이다 —
`glob: ["src/**/*.cpp", "src/**/*.h"]` 이 `apps/` 를 안 잡고, `include.paths` 에 `"apps"` 가 있어도
**glob 이 먼저 잘라낸다.** 🔵 `apps/` 는 `compile_commands.json` 에 **54건** 들어와 있으므로
configure 문제가 아니다.

**핸드오프가 "처음에는 필터를 걸지 말 것" 이라 해서 준 설정을 그대로 썼고, 임의로 넓히지 않았다.**
`.dot` 기준 MyApp 계열 타겟이 **19개** 있으므로, 넓히면 노드 수가 크게 는다.
**계량 수치를 최종본으로 쓰려면 이것부터 결정해야 한다.**

### 🔵 문제 3 의 해결 경로 — 실제로 돌려서 확인했다 (2026-08-27)

**`clang-uml` 은 디렉토리별 깊이를 설정으로 제어할 수 있다. CLI 인자가 아니라 설정 파일이다.**
아래는 전부 이 저장소에서 실행한 결과다.

**(1) `apps/` 를 넓히면 이렇게 는다.**

| 설정 | elements | relationships |
|---|---|---|
| `glob: [src/**/*.cpp]` (현재) | 203 | 411 |
| `glob: [src/**/*.cpp, apps/*/*.cpp]` | **318** | **671** |

🔵 **네임스페이스 이름이 문서의 예상과 다르다.** `MyApp::` 이 아니라 **`TopdownShooter`(74개)** 다.
`MyApp` 은 CMake 타겟 이름(`_MyApp_`)이지 C++ 네임스페이스가 아니었다.
넓히면 `SJH` 도 102 → 111 로 9개 는다(앱에서만 쓰이던 엔진 타입).

⚠ **`apps/**/*.cpp` 는 죽는다.**

```
ERROR: The complexity of an attempted match against a regular expression exceeded a pre-set level.
```

🔵 `apps/*/*.cpp` 로 쓰면 정상 동작한다. clang-uml 0.6.3 의 glob 이 `**` 를 정규식으로 펴다가
복잡도 상한에 걸리는 것으로 보인다. **`src/**/*.cpp` 는 멀쩡한데 `apps/**/*.cpp` 만 걸린다.**

**(2) 깊이 제어는 `include.context` 의 `radius` 다.** 씨앗(seed)을 정하고 **그래프 홉 수**로 자른다.

```yaml
include:
  context:
    - match:
        radius: 1
        pattern: '(SJH|TopdownShooter)::.*'
```

🔵 좁은 씨앗 하나(`SJH::Scene::Actor`)로 반경만 바꿔 재본 결과 — **radius 가 실제로 듣는다:**

| 설정 | elements | relationships |
|---|---|---|
| `context: [SJH::Scene::Actor]` (축약형) | 13 | 23 |
| `radius: 1` | 13 | 23 |
| `radius: 2` | **74** | **172** |

축약형의 기본 반경은 **1** 이다. 🔵 `radius: 0` 은 이 시험에서 1 과 같은 결과를 냈다 — **0 의 의미는
확인하지 못했다.**

> ⭐️ **이것이 C-9 R1(전이 확장 금지)과 정확히 같은 뜻이다.** 내 코드를 씨앗으로 두고 `radius: 1`
> 이면 "내 코드 전부 + 내 코드가 직접 닿는 것까지" 가 되고, 외부의 외부는 들어오지 않는다.
> **R1 을 파서에서 사후에 거르는 대신 수집 단계에서 강제할 수 있다.**

🔵 다만 씨앗을 `(SJH|TopdownShooter)::.*` 로 넓게 잡으면 `radius: 1` 이 **326 elements** 를 낸다 —
경로 필터(318)보다 **오히려 많다.** `include.paths` 가 잘라내던 `std::` 이웃을 context 가 끌어오기
때문이다. **둘은 다른 축이므로 섞어 쓸 때 결과를 반드시 재확인할 것.**

**(3) `--validate-only` 로 확인한 `include` 하위 키 (0.6.3):**
`paths` · `namespaces` · `elements` · `context` · `subclasses` · `parents` · `dependants` ·
`dependencies` · `relationships` · `access`, 그리고 `filter_mode: basic|advanced`.
⚠ **스키마 통과가 동작을 뜻하지 않는다** — 위 (2)가 그 예다. 반드시 돌려서 수를 볼 것.

---

> 🔵 **2026-08-27 3차 측정 — 재수집 전 현재 산출물은 여전히 반쪽이다.** `full_class.json` 을 다시 읽어 확인했다:
> `elements` 203개 중 `MyApp` 네임스페이스 **0개** (SJH 102 · std 83 · glm 7 · nlohmann 5 ·
> Effekseer 2 · FMOD 2 · 무네임스페이스 2), `relationships` 411개.
> **관찰 보고서의 모든 계량 수치와 완전히 일치**하므로 산출물은 그대로 유효하지만,
> `apps/` 가 빠진 반쪽이라는 사실도 그대로다.

### 문제 4 — `glob` 은 번역 단위에만 걸린다 (함정)

🔵 `glob: ["src/**/*.h"]` 만 주면 매칭 **0건**이다 (`no translation units found`).
`compile_commands.json` 에는 `.cpp` 만 있고 헤더는 전이적으로 딸려 온다.
🔵 설정 파일을 저장소 밖에 두면 glob 이 **설정 파일 위치 기준**으로 풀린다 —
`--paths-relative-to-pwd` 로 우회했다.

### 문제 5 — 역방향 갈래에서 나온 것: 정적 도구가 조용히 부분 결과를 준다

이 핸드오프의 범위 밖이지만 **파이프라인 전체에 걸린다.**
🔵 `clangd` 는 색인이 덜 찬 상태에서 참조 질의에 **부분 결과를 에러 없이** 돌려준다:

```
경과(s)  참조수
   0.6      7
  10.7     15      <- 두 번 연속 같은 값인데도 오답
  15.7     45      <- 정답
```

🔵 **디스크 색인이 이미 있어도** 즉시 질의하면 샤드 로딩 중이라 덜 나온다 — 전수 결과가
게이트 없이 **1,747건**, 게이트 후 **1,767건**이었다. 20건이 조용히 빠졌다.
해결은 `$/progress` 의 `end` 를 기다리는 게이트이고 이미 구현·검증했다
(3회 실행 바이트 동일). 상세는 `HANDOFF-clangd-reverse-refs.md` §6-1.

> ⚠ **교훈이 이 문서에도 적용된다.** 정적 도구가 "성공" 을 반환했다고 완전한 것이 아니다.
> clang-uml 도 같은 성질이 있는지는 **미확인** 이다.

### ✅ 해소됨 — 간선 `file`/`line` (2026-08-27 C-11 → **C-13 으로 번복**)

> 🔴 **아래 C-11 기록은 번복됐다. 먼저 이것을 읽을 것.**
>
> C-11 은 "clang-uml 이 간선에 위치를 주지 않는다" 를 전제로 L3 를 노드로 내렸다.
> 🔵 **그 전제가 틀렸다** — 노드의 `members[]` 에 **멤버별 `source_location`** 이 전부 있다.
> 간선의 `label` 로 `members[]` 를 조회하면 된다. **문자열 탐색이 아니라 구조 조회다.**
>
> ```
> 멤버 561건 전부에 source_location.line 있음
> label -> members[] 유일 매칭 311건 / 모호 0건
>   aggregation 215/215 · association 96/96  = 소유 간선 100%
> ```
>
> **C-13 (최종)** — L3 판정 대상 = **노드 + 소유 간선(`composition`·`aggregation`)**.
> 🔵 산출된 `codegraph.json` 에서 소유 간선 **205/205 전량**에 정확한 멤버 선언 줄이 붙는다.
> 나머지 종류는 가리킬 멤버가 없어 `null` 이고, 검증기가 **"근거 없음"** 으로 낸다(3값).
>
> ⚠ **`label` 휴리스틱을 채택하지 않았다는 아래 서술도 함께 무효다** — 채택 안 한 것은
> *파일 안 문자열 탐색* 이고, 실제로 쓰는 것은 *`members[]` 구조 조회* 다. 다른 방법이다.

#### (원문 — C-11 시점 기록)

관찰 보고서 F절과 I절이 **이 핸드오프 최대의 미해결 항목**으로 올려 둔 것이다:
🔵 clang-uml 이 간선 411건 전량에 위치를 주지 않는다.

**사용자가 "노드 단위로 내린다" 를 택했다.** Track C **C-11** 로 확정됐고 §7 설계 근거 1 과
§8 이 그에 맞춰 고쳐졌다.

| | 결정 |
|---|---|
| 인용 검증 L3 의 판정 대상 | **노드뿐.** 간선은 판정하지 않는다 |
| `edges[].file`/`line` 필드 | **남긴다.** 낼 수 있는 도구는 계속 채운다(C# 은 정확히 낸다). 다만 판정에 쓰지 않는다 |
| `label` 휴리스틱 (166/411 복구) | **채택 안 함** |
| `clangd` 역참조 갈래와 조인 | **채택 안 함** (범위 확대) |

**파서에 미치는 영향 — 줄어든다.**

- 🔵 I절의 "간선에 `file`/`line` 이 없다" 항목은 **더 이상 결함이 아니다.** 예상된 상태다.
- `label` 로 줄을 역추적하는 경로가 사라지므로 파서가 단순해지고, **245건의 "근거 없음" 문제도 소멸**한다.
- 대신 **F절의 노드 쪽 두 함정이 전면에 온다** — canonical 이름(`basic_string`)과
  중첩 타입 구분자(`Program##UniformBlock`). L3 가 노드에만 걸리므로 이 둘이 곧 L3 의 정확도다.
  🔵 전수 203건 기준 1st-party 97/102 · 외부 77/101.

💭 **남는 손실 하나** — "A 가 B 를 소유한다" 의 근거 줄이 멤버 선언 줄이 아니라 타입 선언 줄이 된다.
문서 쪽에서 이것을 어떻게 보완할지는 **아직 정해지지 않았다.**

### 의문 1 — `stb_extra` 를 1차로 볼 것인가 외부로 볼 것인가

🔵 `cmake/DepsEngine.cmake:133` 이 `add_library(stb_extra INTERFACE)` 로 **저장소가 직접 선언**한
타겟이지만, 실질은 vcpkg `stb` 포트의 래퍼다(vcpkg 가 타겟이 아니라 `Stb_INCLUDE_DIR` 변수만 주기 때문).
계량은 **"저장소가 선언한 타겟" 기준으로 1차 분류**했다. 외부로 옮기면 1차 44 → 43, 섬 14 → 15.
💭 60 — 선언 기준이 `normalize.py` 에 더 쓸모 있다고 보지만 **확정은 사용자 몫이다.**

### 의문 2 — vcpkg 포트와 `.dot` 노드가 1:1 이 아니다

🔵 `vcpkg.json` 선언 포트 **12개**가 `.dot` 서드파티 노드 **26개**로 갈라진다. 네 갈래다.

| 갈래 | 예 |
|---|---|
| 한 포트가 타겟 둘로 export | `glm` → `glm::glm` + `glm::glm-header-only` (spdlog·assimp 동일) |
| 전이 의존이 독립 노드로 | `fmt::fmt`·`Threads::Threads`(spdlog), `Boost::mp11`(boost-describe) |
| 선언했는데 `.dot` 에 없음 | `stb`(→`stb_extra` 흡수) · `catch2`(테스트 OFF) · `opencv4`(golden feature OFF) |
| vcpkg 무관 | `sb7` `glfw3` `Effekseer` `fmod` + macOS 프레임워크 5개 |

**파서가 "`vcpkg.json` 을 읽어 외부를 거르면 된다" 고 가정하면 정확히 이 네 갈래에서 틀린다.**

### 의문 3 — 예상이 빗나간 것 둘

🔵 §3 단계 2 가 예고한 **`extern/Effekseer` 타겟 폭증이 일어나지 않았다.** `TestCpp`·
`EffekseerSoundOSMixer` 류가 `.dot` 에 0건이고, `Effekseer`·`EffekseerRendererGL` 둘뿐이다 —
이 저장소는 Effekseer 를 `add_subdirectory` 하지 않고 **사전 빌드 라이브러리로 링크만 한다.**
따라서 "제외 전후 수의 차이로 절단 지점을 정한다" 는 §3 의 계획은 다른 근거를 써야 한다.
🔵 실제 폭증은 **vcpkg 포트가 타겟 둘로 갈리는 것**과 **`std::` 템플릿 인자 증식**에서 온다.

🔵 §5 가 예고한 **Qt/moc 오염도 없었다.** `SJH_BUILD_EDITOR` 가 기본 `OFF` 라 `editors/` 가
configure 되지 않고, `compile_commands.json` 107건에 moc 생성 파일이 없다.
**따라서 §2-3 의 "Qt → `(Qt) <모듈>`" 행은 이 저장소에서 아직 검증되지 않았다.**

---

## 6. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만 인정한다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.**
- 커밋이 필요하면 `personal-commit-messages` 스킬을 따른다 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).
- **거울 함정을 경계하라.** 이 작업은 파일을 모아 표로 정리하는 일이다. 수집 스크립트에
  플러그인 구조나 추상 인터페이스가 나오면 그 자체가 Track C 가 잡으려는 실패다.
