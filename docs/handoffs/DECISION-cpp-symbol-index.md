# 결정 기록 — C++ 심볼 인덱스 도구 선정

> # 🔴 SUPERSEDED — 이 문서를 따르지 말 것 (2026-08-27 번복)
>
> **D1(scip-clang 채택)이 사용자에 의해 번복됐다.** 사유는 인지도(GitHub star 91)와
> 패키지 매니저 부재(수동 바이너리 다운로드)다. **현재 정본은 `HANDOFF-clangd-reverse-refs.md`
> (역방향 = `clangd`)이다.**
>
> 이 문서를 지우지 않고 남기는 이유: **D2(고아 헤더 범위 밖)·D4(MSVC 전용 미지원)는 그대로 유효**하고,
> §3 의 한계 1~3 과 §7 기각안 목록이 후속 판단의 근거로 계속 쓰인다. scip-clang 은 **폴백으로 강등**
> (E2)됐을 뿐 폐기된 것이 아니다.
>
> **살아 있는 부분**: §3 한계 1~3 · §6 D5(고아 헤더를 "미확인 영역"으로 보고) · §7 기각안 표
> **죽은 부분**: §0 한 줄 요약 · §1 D1 · §2 · §4 · §5 첫 명령


> 작성일: 2026-08-27
> 상위 문서: `HANDOFF-codebase-wiki.md` (Track C)
> 이 문서가 답하는 것: `HANDOFF-cpp-symbol-index-selection.md` (조사 의뢰)
> 함께 볼 것: `cpp-index-friendly-conventions.md` — ⚠ 🔵 **이 문서는 아직 존재하지 않는다**(2026-08-27 확인). D2 의 완화 경로(자기 코드는 컨벤션으로)가 가리키는 대상이 비어 있다. §3 한계 1 도 이 문서를 참조한다.

---

## 0. 한 줄 요약

**역방향 질의 도구로 `scip-clang`을 채택한다. 헤더 전용 모듈 문제는 범위 밖으로 두고, Windows MSVC 전용 코드베이스는 미지원으로 명시한다.**

⚠ **이 문서의 모든 판정은 🟡(문서·저장소 확인)이다.** 원격 조사라 어떤 명령도 실행되지 않았다. 🔵(실행 검증)는 §5의 실측이 끝나야 붙는다.

---

## 1. 결정 로그

| # | 결정 | 상태 | 신뢰도 |
|---|---|---|---|
| **D1** | 역방향 질의 도구로 **`scip-clang`** 채택 | `[확정됨 2026-08-27 사용자]` | 🟡 80 |
| **D2** | **헤더 전용 모듈(고아 헤더)은 범위 밖.** 자기 코드는 컨벤션으로, 남의 코드는 미대응 | `[확정됨 2026-08-27 사용자]` | 🟡 75 |
| **D3** | Windows 네이티브 실행은 포기. **mingw 크로스 compdb로 macOS에서 Windows 경로 색인** | `[보류됨 2026-08-27 — 전제 실패]` 🔵 이 저장소에 `toolchain/` 디렉토리 자체가 없다. §4 참조 | 🔵 95 |
| **D4** | **MSVC 전용 코드베이스는 미지원**으로 문서에 명시 | `[확정됨 2026-08-27 사용자]` | 🟡 85 |
| **D5** | 고아 헤더는 분석 못 해도 **"미확인 영역"에 목록으로 보고**한다 | `[제안됨]` | 🟡 78 |

---

## 2. D1 — 왜 scip-clang인가

역방향 질의를 할 수 있는 도구는 셋이었으나, **파이프라인에 꽂히는 것은 하나뿐이다.**

| | 역방향 질의 | 배치 실행 | **Python이 읽을 수 있나** |
|---|---|---|---|
| **scip-clang** | ✅ | ✅ | ✅ `scip print --json` |
| clangd | ✅ | △ `clangd-indexer` | ❌ `.idx`는 내부 형식 |
| ccls | ✅ | ❌ 데몬 | ❌ |

**C6(산출물을 `normalize.py`가 소비)이 결정했다.** clangd는 역방향 질의 자체가 더 나을 수 있으나 인덱스 파일을 읽을 공개 경로가 없어 배치 파이프라인에 들어오지 못한다.

나머지 조건도 통과한다 — Apache-2.0(개인 프로젝트 무료), arm64 macOS 바이너리 제공, `compile_commands.json` 직접 소비, SCIP protobuf는 버전 관리되는 안정 스키마.

**부가 이점**: scip-clang은 Clang 21 기반이다. clang-uml이 두 번 실패한 원인이 AppleClang(리소스 디렉토리 `clang/21`) compdb를 Homebrew libclang 22로 읽은 것이었으므로, **버전이 맞아떨어져 함정 1이 아예 안 생길 수 있다.** 💭 60 — 첫 실행에서 판가름 난다.

---

## 3. 명시적 한계 — 이 절이 이 문서의 목적이다

### 한계 1 — 고아 헤더는 보이지 않는다

`.cpp`가 없어 번역 단위(translation unit)가 없는 헤더는 색인되지 않는다. **0건은 에러가 아니라 정상 종료라, 사라졌다는 사실조차 보이지 않는다.**

- **자기 코드**: 헤더 자기충족성 테스트(`cpp-index-friendly-conventions.md` §1)로 해결
- **남의 코드**: **해결 수단 없음.** 컨벤션을 강제할 수 없다

이 한계는 scip-clang만의 것이 아니다. libclang·clangd·ccls·clang-query·Kythe가 전부 번역 단위 기반이라 같은 한계를 갖는다. **도구를 바꿔서 푸는 문제가 아니다.**

### 한계 2 — Windows 네이티브 실행 불가

🟡 scip-clang 바이너리는 Linux와 macOS만 제공된다. 테스트 환경도 Ubuntu 18.04 / 22.04 / macOS 13이다. 소스 빌드는 Bazel 기반이고 Windows를 상정하지 않은 것으로 보인다.

**그러나 이것이 곧 "Windows 코드를 못 본다"는 뜻은 아니다.** 두 가지를 구분해야 한다.

| | |
|---|---|
| **실행 환경** | 도구가 어느 OS에서 도는가 |
| **색인 대상** | 도구가 어느 플랫폼의 코드를 보는가 |

**이 둘은 독립이다.** 무엇을 보는지는 OS가 아니라 `compile_commands.json`이 정한다. `_WIN32`가 정의된 compdb를 주면 macOS에서 돌아도 Windows 코드 경로를 본다. → D3

### 한계 3 — MSVC 전용 코드베이스 미지원

mingw 헤더와 MSVC 헤더는 다르다. MSVC 전용 확장(`__declspec`, MSVC STL 내부)을 쓰는 코드는 mingw로 파싱되지 않고, scip-clang은 Windows에서 돌지 않는다. **양쪽이 동시에 막힌다.**

**이 케이스는 현재 미지원으로 둔다.** 실제로 만났을 때가 재검토 시점이다.

---

## 4. D3 — mingw 크로스 compdb

macOS 한 곳에서 두 플랫폼을 모두 색인한다.

```bash
# macOS 경로
cmake -S . -B build-cc -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
scip-clang --compdb-path=build-cc/compile_commands.json
#   → codegraph.cpp.macos.json

# Windows 경로 — 같은 머신에서
cmake -S . -B build-cc-win -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=toolchain/mingw-w64.cmake \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
scip-clang --compdb-path=build-cc-win/compile_commands.json
#   → codegraph.cpp.windows.json
```

`codegraph.json`의 `platform` 필드가 여기서 값을 한다. **Windows 머신도 WSL도 필요 없다.**

🔵 **전제 확인 결과 — 실패했다 (2026-08-27, `bfb72b4`).**

```
$ ls toolchain/
ls: toolchain/: No such file or directory
$ find . -name 'mingw*' -not -path './build_cc/*'
(출력 없음)
```

**`toolchain/mingw-w64.cmake` 가 없고 `toolchain/` 디렉토리 자체가 없다.** mingw 이름을 가진 파일도
저장소 전체에 0건이다. 짐작대로 mingw 크로스빌드 환경은 이 프로젝트 것이 아니었다.
`HANDOFF-cpp-pattern-collection.md` §1 이 같은 사실을 이미 기록해 두었다.

**따라서 D3 은 이 저장소에서는 실행할 수 없다.** 위 명령 묶음은 mingw 툴체인이 있는 저장소에서만
유효하다. 이 저장소의 Windows 경로 색인은 **현재 수단이 없다** — 함정 9(MSVC 전용 미지원)와 합쳐
Windows 쪽은 통째로 미지원이다.

**D3 을 폐기하지는 않는다.** 논리(실행 환경과 색인 대상의 독립)는 그대로 유효하고, mingw 툴체인을
만들면 성립한다. 그것을 만들지는 별개 결정이다.

---

## 5. 실측이 필요한 항목 (🟡 → 🔵 전환 조건)

조사는 원격이라 전부 문서 근거다. 아래는 로컬에서 확인해야 한다.

| # | 확인할 것 | 방법 |
|---|---|---|
| 1 | ~~compdb 필드가 `command`인가 `arguments`인가~~ | 🔵 **해결됨 — `command` 다.** 키 4종: `command` · `directory` · `file` · `output` (107건, `build_cc`) |
| 2 | **플래그 주입 없이 도는가** | 먼저 그냥 실행. 함정 1이 안 생길 수 있다 |
| 3 | **중첩 타입 symbol 표기 규약** | `Program::UniformBlock`이 어떤 문자열로 나오나. clang-uml은 `Program##UniformBlock`이었다 |
| 4 | **역참조 정확도** | 정답 목록을 만들어 대조. 표본이 아니라 전수 |
| 5 | **재현성 정규화 범위** | 두 번 돌려 무엇이 달라지나 (절대경로·타임스탬프) |
| 6 | ~~mingw compdb가 파싱되는가~~ | 🔵 **확인 불가 — D3 전제가 실패했다.** `toolchain/` 없음. §4 참조 |

### ⚠ 설치 전에 — 이름 충돌 (🔵 2026-08-27 실측)

**`brew install scip` 을 실행하지 말 것.** 전혀 다른 소프트웨어가 깔린다.

```
$ brew info --formula scip
==> scip: stable 10.0.3 (bottled)
Solver for mixed integer programming and mixed integer nonlinear programming
https://scipopt.org
```

혼합정수계획 **최적화 솔버**다. Sourcegraph 의 코드 인텔리전스와 무관하고, 라이선스가 Apache-2.0
으로 같아서 확인 없이 보면 더 헷갈린다.

🔵 **`scip-clang` 은 Homebrew 포뮬러가 없다** (`No available formula with the name "scip-clang"`).
공식 릴리스 바이너리를 직접 받아야 한다. `scip` CLI(`scip print --json`) 도 같은 이유로
brew 로 받으면 안 된다 — Sourcegraph 배포본을 받아야 한다.

🔵 현재 이 머신에 `scip-clang` · `scip` 둘 다 **미설치**다.

### 첫 명령 — 이 순서로

```bash
# 0. compdb 형식 확인
jq -r '.[0] | keys' build_cc/compile_commands.json

# 1. 외부 의존 제외
jq '[.[] | select(.file | test("vcpkg_installed|/extern/") | not)]' \
  build_cc/compile_commands.json > cc.filtered.json

# 2. 플래그 주입 없이 먼저 실행 ← 중요
scip-clang --compdb-path=cc.filtered.json --show-compiler-diagnostics

# 3. JSON 변환 후 중첩 타입 표기 확인
scip print --json index.scip > index.json
```

**2번을 플래그 없이 먼저 돌리는 것이 핵심이다.** 통과하면 함정 대응이 통째로 불필요해지고, 실패하면 에러 메시지를 보고 무엇을 주입할지 정하면 된다. 미리 넣으면 정말 필요한지 모른 채로 간다.

⚠ `scip-clang`은 **프로젝트 루트에서 실행**해야 한다(빌드 디렉토리 아님).

---

## 6. D5 — 고아 헤더를 "미확인 영역"으로 보고

분석은 포기하되 **신호는 살린다.** 도구를 추가하지 않고 `normalize.py`에 다섯 줄이면 된다.

```python
tracked = set(git_ls_files("*.h", "*.hpp"))
indexed = set(paths_appearing_in(index_json))
orphans = tracked - indexed        # 이 목록을 보고서에 싣는다
```

Track C가 요구하는 **"미확인 영역" 섹션이 정확히 이 자리**다. 빈칸을 정직하게 남기는 것이 조용히 사라지는 것보다 낫다.

---

## 7. 기각안 + 부활 트리거

| 기각안 | 사유 | 부활 트리거 |
|---|---|---|
| **clangd / clangd-indexer** | `.idx`가 내부 형식이라 Python 소비 불가 | scip-clang이 환경 함정을 못 넘길 때. 또는 MSVC 전용 코드베이스를 만났을 때 |
| **ccls** | 데몬형이고 배치 소비 경로 불명확 | clangd도 막힐 때 |
| **CodeQL** | 라이선스 — 비오픈소스 개인 프로젝트 사용 불가 | 프로젝트를 오픈소스로 공개할 때 |
| **Understand (SciTools)** | 상용 구독 | 없음 |
| **Sourcetrail / NumbatUI** | 2021 개발 중단. 포크는 스스로 "Unstable/WIP" 표기 | 없음 |
| **lsif-clang** | 유지보수 모드. scip-clang이 계승 | 없음 |
| **rtags** | Emacs 중심, 활동성 낮음 | 없음 |
| **Kythe** | Google 유지보수 축소, Bazel 기반 무거운 설정 | 없음 |
| **clang-query** | 대화형 탐색 도구, 지속형 인덱스 아님 | 일회성 정밀 확인이 필요할 때 (보조 용도로는 유효) |
| **GNU GLOBAL (gtags)** | 고아 헤더 안전망으로 검토했으나 D2로 범위 밖 | 고아 헤더 대응이 다시 필요해질 때 |
| **universal-ctags / cscope** | C++ 오버로드·템플릿 해석 불가 | 없음 |
| **WSL 경유 실행** | MSVC compdb의 경로·플래그 불일치가 그대로 남음 | Linux 전용 코드베이스를 Windows 머신에서 볼 때 |

---

## 8. 상위 문서에 반영할 것

`HANDOFF-codebase-wiki.md` (Track C)를 고쳐야 한다.

**§1 표의 7번 행이 틀렸다.** clang-uml 시퀀스와 `SymbolFinder.FindCallersAsync`를 같은 칸에 넣었으나 같은 연산이 아니다. 이렇게 나눠야 한다.

| # | 작업 | C++ | C# |
|---|---|---|---|
| 7a | **순방향 호출 전개** (이게 무엇을 부르나) | clang-uml `start_from` | Roslyn |
| 7b | **역방향 참조 질의** (누가 이걸 부르나) | **scip-clang** | `SymbolFinder.FindCallersAsync` |

그리고 §6 함정 목록에 **한계 1~3**을 추가한다.
