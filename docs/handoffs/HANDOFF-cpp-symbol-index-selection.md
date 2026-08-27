# HandOff — C++ 심볼 인덱스 도구 선정 조사 (Track C 선행 결정)

> 작성일: 2026-08-27
> 인계 대상: **조사를 수행할 Claude Code Agent** (맥락 0 전제로 자기완결)
> 상위 문서: `HANDOFF-codebase-wiki.md` (Track C)
> 관계 문서: `HANDOFF-cpp-pattern-collection.md` (수집 완료) · `samples/cpp/OBSERVATION.md` (그 산출물)
> 대상 저장소: `$GRAPHICS_REPO` (`bfb72b4`)

---

## 0. 목적 — 이것부터 읽어라

> **후보 도구를 조사해 비교표를 채워 오는 것이 전부다. 도구를 고르는 것이 아니다.**

**선정 주체는 사용자다.** 이 작업의 산출물은 **채워진 비교표 + 실측 로그** 이고, "이걸 쓰자" 는
결론을 쓰지 않는다. 추천을 적어야 한다면 **비교표를 다 채운 뒤 맨 마지막에 근거와 함께 분리해서**
적고, 표 안에는 섞지 않는다.

### 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| 도구를 하나 골라 파이프라인에 편입하는 것 | 선정 주체는 사용자. 이 문서는 조사 의뢰다 |
| `normalize.py` 나 `codegraph.json` 을 건드리는 것 | 이번 범위 밖. Track C §7 확장 규율 |
| 검증 안 한 도구 성능을 표에 사실로 적는 것 | 아래 §4 의 라벨 규율. **미검증은 💭 로 적고 검증 열을 비운다** |
| 사용자의 기존 빌드 디렉토리를 건드리는 것 | `build_ninja` 는 사용자 정상 워크플로. `build_cc` 만 쓴다 |

---

## 1. 왜 이 조사가 생겼나 — 실측된 공백

C++ 코드베이스 분석 파이프라인(Track C)에 **질의 가능한 심볼 인덱스가 없다.**

🔵 **Track C §1 의 7번 행이 성립하지 않는다.**

> | 7 | 호출 관계 | clang-uml 시퀀스 | `SymbolFinder.FindCallersAsync` |

같은 칸에 놓여 있지만 같은 연산이 아니다. clang-uml 이 스스로 생성한 시퀀스 다이어그램 설정이
근거다 (`clang-uml --init --add-sequence-diagram`):

```yaml
seqprobe:
  type: sequence
  start_from:
    - function: main(int,const char **)     # <- 진입점을 시그니처로 미리 적어야 한다
```

| | C# (Roslyn) | C++ (clang-uml) |
|---|---|---|
| 연산 | `SymbolFinder.FindCallersAsync` | `start_from` 순방향 전개 |
| 질문 | **"누가 이걸 부르나"** (역방향 질의) | "이게 무엇을 부르나" (순방향, 시작점 기지정) |
| 형태 | 임의 질의 가능한 인덱스 | 다이어그램 1개당 설정 1개 |

**clang-uml 은 렌더러이지 인덱스가 아니다.** 따라서 "누가 이 심볼을 참조하나" 를 물으면
현재 파이프라인은 **grep 으로 떨어진다.**

### grep 이 C++ 에서 실제로 틀린 사례 (이 저장소, 이번 수집에서 발생)

🔵 수집 세션이 `src/fsm` 을 `std::function`·함수포인터·`Callback` grep 으로 판정해
**"해당 없음"** 이라는 틀린 결론을 냈다. 실제 기제는 `uint64_t` 비트마스크였다:

```
IFsmState::GetStateFlag()    -> 내가 누구 (비트 1개)      src/fsm/fsm_state.h:50
IFsmState::GetTransitFlag()  -> 갈 수 있는 곳들의 비트 OR  src/fsm/fsm_state.h:56
StateMachine::TryTransitImpl -> 둘의 AND 로 전이 허용 판단  src/fsm/state_machine.h:167
```

grep 은 C++ 의 오버로드 해소·매크로 전개·템플릿 실체화·ADL·`using` 별칭을 못 본다.
**이 조사의 존재 이유가 이 한 건이다.**

### 반대로, 외부 라이브러리 API DB 는 필요 없다

Track C §2-1 의 **C-9**(외부 의존 축약)가 그 요구를 제거했다. 외부 모듈은 depth 0 단일 노드이고
안으로 들어가지 않으므로, vcpkg 포트가 무슨 API 를 제공하는지 색인할 이유가 없다.
외부/1차 판별도 API 가 아니라 **네임스페이스와 CMake 타겟 이름**으로 한다.

> **따라서 이 조사의 대상은 1차 코드(`src/`, `apps/`)의 심볼 인덱스뿐이다.**
> **도구가 `vcpkg_installed/` 를 통째로 색인하려 든다면 그것은 감점 요인이다** (§3 기준 C3).

---

## 2. 명칭 — 다섯 갈래가 혼동되고 있다

사용자가 "C++ 문법·심볼 DB" 라고 부른 것은 단일 범주가 아니다. **성격이 다른 다섯 갈래**이고
서로 할 수 있는 일이 다르다. **조사할 때 이 구분을 유지하라.**

| # | 범주 명칭 | 무엇인가 | C++ 대표 |
|---|---|---|---|
| **A** | **컴파일러 프론트엔드 API / AST 질의** | 컴파일러가 만든 AST 에 직접 질의. 가장 정확 | `libclang`, `clang LibTooling`, `clang-query`(AST matcher) |
| **B** | **언어 서버 · 코드 인텔리전스 인덱스** | LSP 로 references / call hierarchy 질의. **데몬형** | `clangd`(+ background index) |
| **C** | **인덱스 교환 포맷** | **포맷이지 도구가 아니다.** 생산자가 따로 필요 | `SCIP`(+`scip-clang`), `LSIF`(+`lsif-clang`, deprecated), `Kythe` |
| **D** | **전통적 상호참조 DB (xref)** | 텍스트·휴리스틱 기반. 빠르지만 의미 해석 없음 | `cscope`, `GNU GLOBAL`(gtags), `universal-ctags` |
| **E** | **코드 프로퍼티 그래프 · 질의 언어** | 그래프 DB + 질의 언어. 보안 분석 계열 | `Joern`(CPG), `CodeQL` |
| (참고) | **문서 생성기 부산물** | 색인이 목적이 아니라 부산물 | `Doxygen XML`, `clang-doc` |

⚠ **C 범주를 "도구" 로 오해하지 말 것.** SCIP·LSIF 는 **포맷**이다. C++ 인덱스를 실제로
만들어 내는 생산자(`scip-clang` 등)가 별개로 있어야 하고, 그 생산자의 성숙도가 곧 실효 성능이다.

⚠ **Track C §9 의 기각 조항이 이 조사를 막지 않는다.** §9 는 `SCIP / Joern / tree-sitter 통합` 을
기각하며 부활 트리거를 **"지원 언어가 5개 이상으로 늘 때"** 로 걸었다. 그러나 지금 필요한 것은
다언어 지원이 아니라 **C++ 안에서의 질의 가능성**이다. **기각 사유가 이 요구를 커버하지 않으므로,
이건 "기각된 안" 이 아니라 아직 논의되지 않은 공백이다.** 조사 대상에서 빼지 말 것.

---

## 3. 선정 기준 체크리스트 — 이 표를 후보마다 채운다

기준은 **이번 수집 세션에서 실제로 부딪힌 것들**에서 나왔다. 추상적 좋음이 아니라
**이 저장소에서 걸린 문제를 푸는가**를 묻는다.

### C1~C4 — 기능 (없으면 탈락)

| # | 기준 | 왜 이게 기준인가 | 판정 방법 |
|---|---|---|---|
| **C1** | **역방향 질의 — "누가 이 심볼을 참조하나"** | 이 조사가 생긴 이유 그 자체 (§1) | `SJH::Scene::Actor` 참조처를 전부 뽑아 보라 |
| **C2** | **템플릿 실체화를 보는가** | 🔵 `src/fsm` 은 헤더 2개뿐이고 `.cpp` 가 없어 `compile_commands.json` TU **0건**, clang-uml 노드 **0건** 이다. 헤더 전용 모듈이 통째로 안 보였다 | `StateMachine<TState,TOwner>` 가 잡히는지 확인 |
| **C3** | **외부 의존을 제외할 수 있는가** | C-9. `vcpkg_installed/` 와 `extern/` 을 색인에서 뺄 수 있어야 한다. 🔵 클래스 층 노드의 49.8%(101/203)가 외부였다 | 색인 대상 경로 필터 설정이 있는가 |
| **C4** | **`file:line` 이 정확한가 (인용 검증 L3 성립 조건)** | Track C §8 의 L3 가 여기 걸린다 | 아래 §5 의 **정답 10건**으로 대조 |

### C5~C8 — 파이프라인 적합성

| # | 기준 | 왜 이게 기준인가 |
|---|---|---|
| **C5** | **배치형인가 데몬형인가** | ⚠ **사용자 우선순위 #1 이 "결정론적 증거 수집" 이다.** 같은 입력에 같은 파일이 떨어지는 배치형이 상태를 들고 있는 데몬(LSP 세션)보다 유리하다. **B 범주(clangd)의 최대 약점이 여기다** |
| **C6** | **산출물이 파일로 떨어지는가, 형식이 안정적인가** | `normalize.py` 가 소비해야 한다. 버전 간 스키마가 흔들리면 감점 |
| **C7** | **`compile_commands.json` 을 그대로 먹는가** | 🔵 이미 `build_cc/compile_commands.json` 107건이 있다. 별도 빌드 설정을 또 요구하면 감점 |
| **C8** | **증분·재현** | 같은 커밋에서 두 번 돌려 **바이트 동일**한가. 우선순위 #1 |

### C9~C11 — 도입 비용

| # | 기준 | 비고 |
|---|---|---|
| **C9** | **macOS arm64 에서 도는가** | §5 의 환경 함정을 반드시 통과해야 한다 |
| **C10** | **설치 부담** | 🔵 이미 있는 것과 새로 받아야 하는 것을 구분해 적는다 (§5 설치 현황) |
| **C11** | **라이선스·비용** | ⚠ 이 저장소는 **개인 프로젝트**다(교수 제출용 아님). 상용 라이선스나 "오픈소스에만 무료" 조건은 **명시적으로 확인해 적을 것.** CodeQL·Understand 가 여기 걸린다 |

---

## 4. 라벨 규율 — 이 조사에서 가장 중요한 부분

사용자 우선순위가 명시돼 있다.

> **1순위: 반증 가능성 제거, 실측 데이터 수집, 결정론적 증거 수집**
> **2순위: LLM 부하 줄이기**

**순서를 뒤집지 말 것.** 구체적으로:

- 🔵 는 **이번 세션에서 실제로 돌린 명령의 출력만** 인정한다. 공식 문서를 읽은 것은 🟡 다.
- **표본이 아니라 전수로 재라.** 🔵 이번 수집 세션이 F절을 표본 10건으로 재서 "1st-party 10/10 완전 일치" 를 얻었는데, **전수 203건으로 다시 재니 97/102** 였다. 표본이 함정 하나를 통째로 숨겼다(§5 의 `##` 트랩). 전수가 몇 초면 표본을 쓸 이유가 없다.
- **모르면 `미확인` 으로 비워라.** 🔵 수집 세션의 유일한 틀린 주장이 grep 결과에서 판단을 채워 넣은 데서 나왔다(§1 의 `src/fsm`). **빈칸은 정보이고, 채운 추측은 오염이다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 약어와 압축 표현을 피한다. 한국어 + 영문 기술용어 병기.

---

## 5. 이 저장소의 실측 사실 — 조사 착수 전에 알아야 할 것

전부 🔵 이번 수집 세션(2026-08-27, `bfb72b4`)의 명령 출력이다.
원시 산출물은 대상 저장소 `out/codegraph-raw/` (gitignore, 2.4 MB).

### 규모

| 항목 | 값 |
|---|---|
| 추적 `.cpp`/`.cc`/`.cxx` | 127 |
| 추적 `.h`/`.hpp` | 329 |
| `build_cc/compile_commands.json` 항목 | **107** (`apps/` 54 + `src/` 53) |
| clang-uml 클래스 노드 | 203 (1차 102 / 외부 101) |
| clang-uml 관계 | 411 |
| `cmake --graphviz` 타겟 노드 | 70 (1차 44 / 외부 26) |

### 빌드 — 이대로 재현하면 된다

```bash
cd $GRAPHICS_REPO
cmake --preset cc          # -> build_cc/, compile_commands.json 107건
```

`cc` 프리셋은 이 조사를 위해 추가된 것이다(`CMakePresets.json`). `ninja` 를 상속하고 이름만 `cc` 라
`build_${presetName}` 규칙에 따라 `build_cc` 로 떨어진다.
⚠ **`build_ninja-golden` · `build_ninja-release-golden` 은 골든 이미지 회귀 기준선이다. 읽기만 하라.**
⚠ `build_ninja` 는 사용자의 정상 개발 디렉토리다. 현재 이 워킹트리에 존재하지 않을 수 있다.

### 환경 함정 — 어떤 libclang 기반 도구든 이걸 밟는다

🔵 clang-uml 이 **두 번 연속 실패한 뒤** 세 번째에 성공했다. 원인이 둘 다 환경이다.

**함정 1 — 컴파일러 리소스 디렉토리 불일치**

```
[FATAL] include/GLFW/glfw3.h:137: 'stddef.h' file not found
```

`compile_commands.json` 은 AppleClang(`/usr/bin/c++`, resource dir `.../clang/21`) 기준인데
Homebrew libclang 은 22 다. 해결:

```
-resource-dir=/opt/homebrew/opt/llvm@22/lib/clang/22
```

**함정 2 — macOS SDK sysroot 부재**

```
[FATAL] include/GLFW/glfw3.h:147: 'OpenGL/gl.h' file not found
[NOTE]  did not find header 'gl.h' in framework 'OpenGL' (loaded from '/System/Library/Frameworks')
```

AppleClang 은 sysroot 를 암묵적으로 주지만 Homebrew clang 은 안 준다. 해결:

```
-isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk
```

> **후보 도구가 libclang 기반이면 위 두 플래그를 주입할 수단이 있는지부터 확인하라.**
> 없으면 C9 에서 탈락이다. 🔵 clang-uml 은 `add_compile_flags` 로 가능했다.

**함정 3 — glob 은 번역 단위에만 걸린다**

🔵 `glob: ["src/**/*.h"]` 만 주면 **매칭 0건**이다(`no translation units found`).
`compile_commands.json` 에는 `.cpp` 만 있고 헤더는 전이적으로 딸려 온다.

**함정 4 — 설정 파일 기준 상대경로**

🔵 설정을 저장소 밖에 두면 glob 이 설정 파일 위치 기준으로 풀린다.
clang-uml 은 `--paths-relative-to-pwd` 로 우회했다.

### `file:line` 정답 10건 — C4 판정용

🔵 전수 203건 대조를 이미 했다(`out/codegraph-raw/09-fileline-census-full.txt`).
후보 도구는 아래와 **같은 값**을 내야 한다.

| # | 심볼 | 정답 위치 | 그 줄의 실제 내용 |
|---|---|---|---|
| 1 | `SJH::MouseInput` | `src/input/mouse_input.h:42` | `class MouseInput` |
| 2 | `SJH::VertexLayout` | `src/layout/vertex_layout.h:62` | `class VertexLayout` |
| 3 | `SJH::Diagnostics::GLObjectLog` | `src/diagnostics/gl_log.h:48` | `class GLObjectLog` |
| 4 | `SJH::Diagnostics::GLDebug` | `src/diagnostics/gl_log.h:107` | `class GLDebug` |
| 5 | `SJH::Diagnostics::GLValidate::IndexFindingKind` | `src/diagnostics/gl_validate.h:47` | `enum class IndexFindingKind` |
| 6 | `SJH::Diagnostics::GLValidate::DiagFinding` | `src/diagnostics/gl_validate.h:57` | `struct DiagFinding` |
| 7 | `SJH::Diagnostics::GLValidate::DiagResult` | `src/diagnostics/gl_validate.h:65` | `struct DiagResult` |
| 8 | `SJH::Diagnostics::UniformDiagnostics` | `src/diagnostics/uniform_diagnostics.h:40` | `class UniformDiagnostics` |
| 9 | `SJH::Scene::Component` | `src/scene/actor.h:58` | (중첩 아님, 클래스 선언) |
| 10 | `SJH::Program::UniformBlock` | `src/program/program.h:107` | `struct UniformBlock` — **중첩 타입** |

⚠ **10번이 함정이다.** 🔵 clang-uml 은 중첩 타입의 이름을 **`Program##UniformBlock`** 으로 낸다.
구분자가 `::` 가 아니라 **`##`** 이고, 바깥 클래스가 `namespace` 필드에 들어가지 않는다.
**표본 10건으로는 이 함정이 안 잡혔고 전수 203건으로 재고서야 5건이 드러났다.**
후보 도구가 중첩 타입 이름을 어떻게 내는지 **반드시 확인해 표에 적어라.**

### 도구 설치 현황 (🔵 이 머신, 2026-08-27)

| 도구 | 상태 |
|---|---|
| `clangd` | **설치됨** `/usr/bin/clangd` (Apple) + `llvm@22` 번들 |
| `clang-query` · `clang-doc` · `clang-check` · `clang-scan-deps` · `clang-refactor` | **llvm@22 번들에 있음** (`/opt/homebrew/opt/llvm@22/bin/`, PATH 에는 없음) |
| `ctags` | `/usr/bin/ctags` (BSD ctags — universal-ctags 아님) |
| `doxygen` | `/opt/homebrew/bin/doxygen` 1.16.1 (brew stable 1.18.0) |
| `clang-uml` | 0.6.3 설치됨 (libclang 22.1.8) |
| brew 포뮬러 존재 | `llvm` 22.1.8 · `cscope` 15.9 · `global` 6.7 · `universal-ctags` 6.2.1 · `rtags` 2.44 · `joern` 4.0.610 |
| brew 포뮬러 **없음** | `cquery` · `sourcetrail` · `codeql` — 별도 경로로 받아야 한다 |

이 저장소에는 `.clangd` 설정이 이미 있다(`CompilationDatabase: build_ninja`, `-std=c++17`, 경고 플래그).
⚠ **이건 설정 버그가 아니다.** `build_ninja` 는 사용자 정상 워크플로의 디렉토리이고, 지금 없을 뿐이다.

---

## 6. 조사할 후보 — 💭 미검증 목록

> ⚠ **아래는 전부 💭 미검증 후보다.** 작성자가 이름만 아는 것이고 능력·현황을 확인하지 않았다.
> **표의 서술을 사실로 옮기지 말고, 직접 확인해 §3 체크리스트를 채워라.**
> 목록에 없는 도구를 찾으면 추가하라. 반대로 이미 죽은 프로젝트면 그 사실을 적고 탈락시켜라.

| 후보 | 범주 | 확인할 것 |
|---|---|---|
| `clang-query` (LibTooling AST matcher) | A | 배치 실행 가능한가. 출력이 기계 판독 가능한가. 역방향 질의를 matcher 로 표현할 수 있는가 |
| `libclang` Python 바인딩 | A | 직접 스크립트를 짜는 선택지. **거울 함정 주의** — 직접 짜면 유지보수가 우리 몫이 된다 |
| `clangd` background index | B | 인덱스 파일 형식이 문서화·안정적인가. **데몬 없이 인덱스만 배치로 뽑을 수 있는가** (C5 핵심) |
| `clangd-indexer` | B/C | 존재 여부부터 확인. 배포에 포함되는가 |
| `scip-clang` (Sourcegraph) | C | 성숙도·유지 상태. macOS arm64 바이너리 제공 여부 |
| `lsif-clang` | C | 💭 SCIP 로 대체되며 deprecated 된 것으로 안다 — **확인할 것** |
| `Kythe` | C | 도입 비용이 큰 것으로 안다 — 확인 |
| `CodeQL` | E | **C11 라이선스가 관건.** 개인 프로젝트에서 쓸 수 있는 조건인지 명확히 적을 것 |
| `Joern` | E | brew 에 있음(4.0.610). C/C++ 프론트엔드 정확도가 관건 |
| `GNU GLOBAL` (gtags) | D | 의미 해석 없이 휴리스틱이라 C1·C2 에서 약할 것으로 봄 — 확인 |
| `cscope` | D | 위와 같음. 오래됐지만 배치형이라 C5·C8 에는 강할 수 있음 |
| `universal-ctags` | D | 위와 같음 |
| `rtags` | B | 💭 유지보수가 멈춘 것으로 안다 — 확인 |
| `Sourcetrail` | B/E | 💭 2021 년 개발 중단 후 오픈소스화된 것으로 안다 — 확인 |
| `Understand` (SciTools) | E | 상용. C11 |
| `Doxygen XML` | 참고 | 이미 설치돼 있고 Track C Phase 3 에 대타로 등장한다. **합성/집약 구분을 잃는다**는 것이 §5 에 기록돼 있음 |
| `clang-doc` | 참고 | llvm@22 번들에 있음. 출력 형식 확인 |

---

## 7. 산출물

```
$REPO_ROOT/docs/handoffs/samples/cpp-index/
  COMPARISON.md          <- §3 체크리스트 C1~C11 을 후보마다 채운 표. 이 작업의 본체
  probe-logs/<도구>.txt   <- 실제로 돌린 명령과 출력 원문. 🔵 의 근거
  fileline-check.tsv     <- §5 정답 10건 대조 결과 (도구 x 심볼)
```

`COMPARISON.md` 는 후보마다 한 절이고, 각 절에 §3 의 C1~C11 표 + 실제로 돌린 명령을 적는다.
**돌려 보지 못한 후보는 "미실행" 으로 남기고 이유를 적는다.** 지우지 않는다.

### 이 작업이 끝났다고 말할 수 있는 조건

1. 후보마다 C1~C11 이 채워졌거나 `미확인`/`미실행` 로 명시돼 있다.
2. **최소 2개 후보는 실제로 이 저장소에 돌려 봤다** — §5 정답 10건 대조까지.
3. C5(배치 vs 데몬)와 C11(라이선스)이 후보마다 채워져 있다. **이 둘이 비면 사용자가 저울질할 수 없다.**

---

## 8. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만.**
- 표본이 아니라 전수. 전수가 비싸면 그 사실과 표본 크기를 적는다.
- 모르면 `미확인`. 추측으로 칸을 채우지 않는다.
- 커밋이 필요하면 `personal-commit-messages` 스킬 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).
- ⚠ **사용자가 같은 워킹트리에서 병렬로 작업한다.** 커밋은 반드시 경로 지정 partial 커밋으로.
  인덱스 전체 커밋은 사용자의 staged 작업을 휩쓴다.
- ⚠ **거울 함정.** 이 작업은 도구를 조사해 표로 정리하는 일이다. 조사 스크립트에 플러그인 구조나
  추상 인터페이스가 나오면 그 자체가 Track C §6 함정 6 이 잡으려는 실패다.
