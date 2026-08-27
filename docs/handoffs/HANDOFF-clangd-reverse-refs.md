# HandOff — C++ 역방향 참조 도구 (clangd 경로)

> 작성일: 2026-08-27
> 인계 대상: Claude Code Agent
> 상위 문서: `HANDOFF-codebase-wiki.md` (Track C)
> 이 문서가 대체하는 것: `DECISION-cpp-symbol-index.md` (scip-clang 선정 — **번복됨**, §1 참조)


> ## ⚠ 2026-08-27 — 이 문서의 산출물은 낡았고, 갈래는 **보류** 상태다
>
> **보류 (사용자 확정)** — 역방향 참조는 Track C §1 의 7b 항목이고, 현재 파이프라인
> (`clang-uml` → `normalize.py` → `codegraph.json`) 어느 단계도 이것을 입력으로 받지 않는다.
>
> **산출물이 낡은 이유** 🔵 — `out/codegraph-raw/11-reverse-refs-cold.json` 의 역참조 1,767건은
> **1차 심볼 102개** 기준이다. 그 뒤 `apps/` 재수집으로 **1차 노드가 185개**가 됐다.
> 늘어난 83개에 대한 역참조가 이 파일에 없다.
>
> **재개할 때 할 일**: `full_class_all.json`(구본 `full_class.json` 아님)의 1차 노드를 입력으로
> 전수를 다시 돌린다. §6-1 의 `$/progress` 게이트는 그대로 유효하다.

---

## 0. 이 문서의 상태 — 먼저 읽어라

> **2026-08-27 갱신 — Task 1·2 와 어댑터 조사가 실행됐다. 이제 🔵 가 있다.**

작성 시점에는 🔵 가 하나도 없었으나, **Task 1·2 가 통과했고 §8 의 12개 중 5개가 🔵 로 닫혔다.**
갱신된 항목은 본문에 🔵 로 표시돼 있고, §8 표가 현재 상태의 정본이다.

**닫힌 것**: 1(star 600) · 2(**PyPI 릴리스는 C++ 불가 / git main 은 가능**) · 3(solidlsp PyPI 없음) ·
4(**clangd 환경 함정 자동 처리 — 통과**) · 11(compdb 필드 = `command`)
**남은 것**: 5 · 6 · 7 · 8 · 9 · 10 · 12 — 특히 **7 · 8 · 9(=U2)** 가 핵심이다.

나머지 판정은 여전히 **🟡** 또는 **💭** 다.

**빈칸을 추측으로 채우지 말 것.** 이 프로젝트의 이전 세션에서 grep 결과로 칸을 채운 것이 유일한 틀린 주장을 낳았다. 모르면 "미확인"으로 남기는 것이 정보다.

§8에 미확인 항목 전체 목록이 있다. **거기 있는 것을 확인하는 것이 이 인계의 첫 작업이다.**

---

## 1. 결정 이력 — 두 번 뒤집혔다

### 1차: scip-clang 선정 → 번복됨

조사 결과 `scip-clang`(Sourcegraph)이 유일하게 "역방향 질의 + 배치 실행 + Python 소비" 셋을 동시에 만족해 1순위로 선정됐다.

**사용자가 두 가지를 지적해 뒤집혔다.**

| 지적 | 실측 결과 |
|---|---|
| 인지도가 낮아 보인다 | 🟡 GitHub star **91개**. 문제가 생겼을 때 검색으로 해결책이 안 나온다 |
| 설치가 패키지 매니저에 의존하지 않는다 | 🟡 Homebrew·pip·cargo·apt 어디에도 없음. GitHub 릴리스 바이너리 수동 다운로드 |

사용자는 `~/report-builder`에 고정 도구 세트를 두고 버전을 관리하려 하므로, 수동 다운로드는 재현성 양쪽에서 감점이다.

### 2차: clangd로 전환 — 그런데 1차 탈락 근거가 틀렸었다

1차 조사에서 clangd를 탈락시킨 유일한 근거는 **"`.idx`가 내부 형식이라 Python이 못 읽는다"**였다.

**이 전제 자체가 잘못된 질문이었다.** `.idx`를 읽을 필요가 없다 — **clangd를 띄워서 물어보면 된다.** LSP `textDocument/references`가 바로 그 용도다.

> 💭 교훈: "산출 파일을 읽을 수 있는가"만 물었고 "질의할 수 있는가"를 묻지 않았다. 도구의 인터페이스 종류를 한 축으로만 봤다.

---

## 2. 확정된 것과 미확정인 것

### 확정 (사용자 확정)

| ID | 결정 | 신뢰도 |
|---|---|---|
| ~~E1~~ | ~~**엔진은 clangd**~~ | 🔴 **번복됨 2026-08-27 — U2 가 '전수' 로 결정되면서 §7 규칙에 따라 `libclang` 직접으로 전환.** 아래 E5 |
| **E5** | **엔진은 `libclang` 직접.** 전수 역참조를 1회 순회로 뽑는다 | `[확정됨 2026-08-27 사용자]` 🔵 |
| **E6** | 어댑터는 **stdio JSON-RPC 직접**. multilspy·solidlsp 는 배포 사유로 탈락 | `[확정됨 2026-08-27 사용자]` 🔵 |
| **E7** | **단계 전략 — E6(clangd)로 먼저 진행하고, E5(libclang)를 최종으로 둔다** | `[확정됨 2026-08-27 사용자]` 🔵 |

### E7 — 왜 두 단계인가, 그리고 그것이 만드는 제약

**지금 E6 로 가는 이유**: 🔵 clangd 는 환경 함정을 자동 처리해 **오늘 당장 0 errors 로 돈다**(§3-6).
그 사이에 **엔진과 무관한 것들** — 정답 목록(#17) · 역참조 정확도(#7) · 중첩 타입 표기(#8) ·
`codegraph.json` 결합 — 을 먼저 확정할 수 있다. libclang 의 환경 함정 수동 주입을
**먼저 풀지 않아도 파이프라인 계약을 증명할 수 있다.**

**E5 를 최종으로 두는 이유**: U2(전수 역참조)가 확정돼 있고, 전수는 libclang 1회 순회가 자연스럽다.

> ⚠ **이 단계 전략이 강제하는 설계 제약 하나 — 이것을 어기면 두 번 만들게 된다.**
> **엔진과 `normalize.py` 사이의 경계를 엔진 중립으로 둘 것.** 즉 산출물은
> `{심볼 식별자 -> [참조 위치…]}` 형태의 파일 하나이고, 그 파일을 만드는 것이 clangd 인지
> libclang 인지가 소비자에게 보이면 안 된다. clangd 의 LSP 응답 형태(`uri`/`range`)가
> 그대로 새어 나가면 E5 전환 때 소비자까지 고쳐야 한다.
>
> 💭 80 — **심볼 식별자를 USR 로 통일하는 것이 가장 안전해 보인다.** 핸드오프 §5 가 libclang 쪽에
> 이미 "이름이 아니라 USR" 을 못박았고, clangd 도 내부적으로 USR 기반이다. 다만 clangd 의
> LSP 응답에 USR 이 실려 오는지는 **미확인** 이고, 안 실려 오면 위치(file:line:col)를 조인 키로
> 써야 한다. **이것이 E6 착수 시 가장 먼저 확인할 것이다.**

> 💭 65 — **전수의 비용이 생각보다 작을 수 있다.** 🔵 이 저장소의 1차 클래스 노드는 102개다.
> clangd 로 전수를 돌려도 수백~수천 왕복 수준이지 "수천 번이라 불가능" 은 아닐 수 있다.
> 사실이면 E5 의 시급성이 낮아진다. **E6 진행 중에 실측으로 확인할 것** (구 Task 5 의 일부가 부활).
| E2 | **scip-clang은 폴백으로 강등.** SCIP 생태계가 필요할 때만 | 🟡 85 |
| E3 | 헤더 전용 모듈(고아 헤더)은 **범위 밖** | 🟡 75 |
| E4 | Windows MSVC 전용 코드베이스는 **미지원**으로 명시 | 🟡 85 |

### 미확정 — 이 인계가 답해야 할 것

| ID | 질문 | 현재 |
|---|---|---|
| ~~U1~~ | ~~Python 어댑터~~ | 🔵 **닫힘 — 주 경로에서는 무효(libclang 에 어댑터 없음). 조건부 답은 E6** |
| ~~U2~~ | ~~선별 질의로 충분한가~~ | 🔵 **닫힘 — 전수 역참조가 필요하다(사용자 확정). → libclang** |
| ~~U3~~ | ~~clangd 가 libclang 보다 나은가~~ | 🔵 **닫힘 — 환경 함정 축은 clangd 우세였으나 U2(전수)가 이겼다.** §7 대로 다른 기준으로 정하지 않았다 |

**U2가 U3를 결정한다.** §7 참조.

---

## 3. clangd 경로 설계

### 3-1. 두 도구의 역할이 다르다

| | 역할 | 인지도 |
|---|---|---|
| **clangd** | 실제 엔진. LSP 서버 | 🟡 최상급 (LLVM 재단, VS Code C++ 확장의 기반) |
| **multilspy 등** | Python에서 clangd를 부르는 어댑터 | 💭 미확인 |

⚠ **어댑터에도 같은 기준을 적용해야 한다.** 🔵 **2026-08-27 실측으로 이 문단의 원래 서술이 틀렸음이
확인됐고, 동시에 더 큰 문제가 드러났다.**

원래 서술("C++를 공식 지원 언어로 광고하지 않는다")은 **틀렸다.** 🔵 multilspy 는 star **600개**이고
README 지원 언어표에 **`cpp | clangd` 가 명시**돼 있다.

**그러나 그 표는 저장소 main 기준이고, PyPI 설치본과 다르다.**

| | `pip install multilspy` (0.0.15) | `pip install git+…` (main) |
|---|---|---|
| `language_servers/clangd_language_server` | 🔵 **없음** | 🔵 있음 |
| `Language` enum | 🔵 `csharp python rust java kotlin typescript javascript go ruby dart` — **`cpp` 없음** | 🔵 `… cpp php elixir` **포함** |

🔵 PyPI 최신 릴리스는 **0.0.15, 2025-04-03** 으로 1년 이상 묵었다. 저장소는 살아 있으나
(최근 커밋 2026-08-20) **C++ 지원이 릴리스된 적이 없다.** 패키지 설명문에도
`Python, Rust, Java, Go, JavaScript, Ruby, C# and Dart` 로 박혀 있다.

> ⚠ **이것이 scip-clang 탈락 사유를 그대로 재현한다.** scip-clang 을 뺀 이유가 "패키지 매니저에 없고
> 수동 다운로드라 재현성이 나쁘다" 였는데, multilspy 로 C++ 를 하려면 **릴리스 태그가 아니라
> 움직이는 브랜치**를 받아야 한다. 커밋 해시로 핀하면 재현은 되지만
> "패키지 매니저로 관리된다" 는 명분이 사라진다.

### 3-2. 근본적 차이 — 파일이 안 남는다

```
[파일 방식]  scip-clang / libclang
  1회 실행 → index.json (전체 역참조) → normalize.py가 읽음 → 끝

[질의 방식]  clangd
  서버 띄움 → 심볼마다 물어봄 → 응답 모아서 저장 → 서버 종료
```

clangd는 **"이 심볼 하나의 참조처"**를 묻는 도구지 **"전체 역참조 인덱스"**를 뱉는 도구가 아니다. 파일을 만들려면 **무엇을 물을지 목록이 먼저 있어야** 하고, 심볼 수만큼 왕복해야 한다.

### 3-3. 위치 목록은 이미 있다

`textDocument/references`는 심볼 이름이 아니라 **파일:줄:열**을 요구한다(🟡). 보통은 `workspace/symbol`로 위치를 먼저 찾는 2단계가 필요하다.

**그런데 clang-uml JSON이 이미 모든 클래스의 `source_location{file, line, column}`을 갖고 있다.** 2단계가 1단계로 줄고 두 도구의 역할이 깔끔하게 갈린다.

```
clang-uml  →  "무엇이 어디에 있나"  (노드 + 위치)
clangd     →  "누가 그걸 부르나"    (엣지)
```

### 3-4. 전수로 물을 필요가 없다 — 이것이 이 경로를 실용적으로 만든다

전체 심볼을 다 물으면 수천 번 왕복이라 느리다. 그런데 **보고서에 실리는 것은 상위 30~50개뿐**이다. PageRank로 중요도를 매긴 뒤 그것만 질의하면 **수십 번**으로 끝난다.

```python
for cls in top_classes[:40]:
    refs = query_references(cls.file, cls.line, cls.column)
    graph.add_reverse_edges(cls.id, refs)
```

**어차피 나머지는 안 그릴 것이므로 안 물어도 된다.** 💭 70 — 이 전제가 맞는지가 U2이고, 이 인계의 핵심 검증 대상이다.

### 3-5. 전체 형태

```
compile_commands.json
    ├→ clang-uml -g json  →  노드 + 위치 + 5종 관계
    │                              │
    │                         ranking.json (PageRank 상위 N개)
    │                              │
    └→ clangd (배치 1회)  ←────────┘  위치로 질의
              │
              └→ 역참조 결과 수집  →  codegraph.json
```

```bash
brew install llvm     # clangd 포함. 설치는 이게 전부
clangd --compile-commands-dir=build_cc --background-index
```

### 3-6. 환경 함정을 clangd가 자동 처리한다 (검증 필요)

clang-uml이 두 번 걸렸던 함정을 clangd는 알아서 처리한다고 문서에 나와 있다(🟡).

> macOS에서 `-isysroot`는 `xcrun`으로 기본 SDK를 조회해 설정되고, `-resource-dir`도 clangd가 자기 것으로 맞춘다.

🔵 **2026-08-27 Task 2 실행 결과 — 사실로 확인됐다. 그것도 예상보다 강하게.**

```
$ /usr/bin/clangd --compile-commands-dir=build_cc --check=src/render/mesh_renderer.cpp
   -> All checks completed, 0 errors
$ /opt/homebrew/opt/llvm@22/bin/clangd --compile-commands-dir=build_cc --check=src/render/mesh_renderer.cpp
   -> All checks completed, 0 errors
```

**플래그 주입 0건.** clangd 가 cc1 인자에 스스로 넣은 것:

| clangd | 자동 주입한 `-resource-dir` | `-isysroot` |
|---|---|---|
| Apple 21.0.0 | `/Applications/Xcode.app/.../clang/21` | `.../MacOSX.sdk` |
| Homebrew 22.1.8 | `/opt/homebrew/Cellar/llvm@22/22.1.8/lib/clang/22` | `.../MacOSX.sdk` |

⚠ **가장 중요한 부분**: compdb 는 AppleClang(`/usr/bin/c++`, resource dir `clang/21`) 기준인데
**Homebrew clangd 22 도 통과했다.** clang-uml 을 두 번 죽인 21/22 불일치가 clangd 에서는
발생하지 않는다 — clangd 가 compdb 의 컴파일러 경로를 신뢰하지 않고 **자기 리소스 디렉토리로
덮어쓰기** 때문이다.

**§5(libclang 직접)의 유일한 비교 열세였던 "환경 함정 직접 처리" 가 clangd 쪽에서 소멸했다.**

---

## 4. 3단 폴백 — Python 어댑터 (U1)

```
1) multilspy 시도       pip install multilspy
   ↓ C++에서 막히면
2) solidlsp 시도        oraios/serena 내장. C++ 명시 지원(🟡)
   ↓ 그것도 막히면
3) stdio JSON-RPC 직접   ~100줄. 의존성이 clangd 하나로 줄어듦
```

**3번이 폴백이 아니라 오히려 더 깨끗한 최종 형태일 수 있다.** 💭 65 — LSP는 stdio로 주고받는 JSON-RPC라 직접 말하는 것이 어렵지 않고, 그러면 인지도 기준을 100% 만족한다(의존성이 LLVM 하나).

### 🔵 2026-08-27 갱신 — 위 순서가 뒤집혔다

**1번과 2번이 둘 다 같은 사유(배포 경로 부재)로 걸렸다.**

| 후보 | 배포 상태 (🔵 실측) | 판정 |
|---|---|---|
| multilspy | PyPI 0.0.15 에 **`cpp` 없음**. C++ 는 `git+` 로 움직이는 브랜치를 받아야 함 | scip-clang 탈락 사유와 동일 |
| solidlsp | 🔵 **PyPI 독립 패키지 없음** (`No matching distribution found`). Serena(28.5k stars, MIT) 내장 모듈이라 통째로 끌어와야 함 | "어댑터 하나만 받는다" 가 안 됨 |
| stdio JSON-RPC 직접 | 의존성이 `brew install llvm` 하나. 움직이는 브랜치 핀 불필요 | **유일하게 배포 사유에서 자유로움** |

💭 75 — **3번을 1순위로 올리는 것이 맞다고 본다.** 다만 🔵 인 것은 "1·2번이 배포 기준에서 걸린다"
까지이고, "그러므로 3번" 은 판단이다. **선정은 사용자가 한다**(§10).

**어댑터를 고르느라 시간을 쓰는 것이 이 작업의 목적이 아니다.** 무엇을 고르든 §8 의 7·8·9 는
그대로 남으므로, 어댑터 결정을 U2 판정보다 앞세우지 말 것.

---

## 5. 살아 있는 대안 — libclang 직접

**clangd 경로가 확정된 것이 아니다.** libclang 직접이 여전히 유효한 후보다.

| | clangd + LSP | libclang 직접 |
|---|---|---|
| 인지도 | 🟡 최상급 (LLVM) | 🟡 최상급 (LLVM) |
| 설치 | `brew install llvm` | `pip install libclang` |
| 의존성 수 | clangd + 어댑터(또는 직접 구현) | 1개 |
| 산출 | 질의 결과를 모아 저장 | 순회 결과를 바로 저장 |
| **전수 역참조** | 비쌈 → 선별 질의로 회피 | **자연스러움 (1회 순회)** |
| 구현 분량 | 💭 LSP 오케스트레이션 ~100줄 | 💭 AST 순회 ~60~120줄 |
| 초기 대기 | 💭 background index 완료까지 수 분 | 없음 |
| **환경 함정** | 🔵 **자동 주입 — 실측 확인 (0 errors, 주입 0건)** | ❌ **직접 처리** |

### libclang 직접의 골격

```python
import json, clang.cindex as cx
cx.Config.set_library_file("/opt/homebrew/opt/llvm/lib/libclang.dylib")
cdb = cx.CompilationDatabase.fromDirectory("build_cc")
index = cx.Index.create()
refs = {}
for cmd in cdb.getAllCompileCommands():
    args = list(cmd.arguments)[1:]           # 첫 인자(컴파일러 경로) 제거
    tu = index.parse(cmd.filename, args=args)
    for c in tu.cursor.walk_preorder():
        if c.kind.is_reference() or c.kind == cx.CursorKind.DECL_REF_EXPR:
            d = c.referenced
            if d is None:
                continue
            refs.setdefault(d.get_usr(), []).append(
                f"{c.location.file}:{c.location.line}:{c.location.column}")
json.dump(refs, open("reverse_refs.json", "w"), indent=1)
```

**⚠ 반드시 지킬 것: 심볼 식별은 이름이 아니라 USR(Unified Symbol Resolution)로 한다.** 이름으로 잡으면 오버로드와 중첩 타입이 뭉개진다.

**알려진 함정** (💭 — 전부 미검증):
- 템플릿 인스턴스화·매크로 전개를 libclang이 부분적으로만 노출
- 107개 번역 단위에서 헤더가 반복 파싱돼 느릴 수 있음
- AppleClang용 compdb의 `/usr/bin/c++` 플래그를 libclang이 먹을 때 시스템 헤더 경로 보정 필요
- Homebrew LLVM 22의 `libclang.dylib` 경로를 `Config.set_library_file()`로 지정해야 함

---

## 6. 검증 순서 (Task)

각 Task에 정지 조건이 있다. 통과하지 못하면 다음으로 가지 말 것.

### Task 1 — 환경 확인 (설치 0)

```bash
which clangd && clangd --version
ls /opt/homebrew/opt/llvm/lib/libclang.dylib
jq -r '.[0] | keys' build_cc/compile_commands.json    # command인가 arguments인가
```

**정지 조건**: clangd 바이너리가 있고 compdb 필드 형태가 확인되면 통과.

### Task 2 — clangd가 환경 함정을 실제로 통과하는가 (가장 중요)

§3-6의 🟡 주장을 실측으로 바꾼다. 파일 하나만 열어 심볼 하나를 조회한다.

```bash
clangd --compile-commands-dir=build_cc --check=src/render/renderer.cpp
```

**정지 조건**: `'stddef.h' file not found`나 `'OpenGL/gl.h' file not found`가 **안 나오면** 통과. 나오면 clangd도 플래그 주입이 필요하다는 뜻이고, libclang 직접 대비 장점이 사라진다 → §5로 전환 검토.

### Task 3 — 어댑터 선정 (U1)

§4의 3단 폴백을 순서대로. **각 단계 30분 상한.**

**정지 조건**: 심볼 하나에 대해 `textDocument/references`가 응답을 돌려주면 통과.

### Task 4 — 정확도 측정 (전수, 표본 아님)

⚠ **이전 세션의 교훈: 표본 10건은 100% 통과했으나 전수 203건에서 5건의 함정이 드러났다.** 표본으로 판정하지 말 것.

정답 목록을 만들어 대조한다. 참조가 5~10건쯤인 작은 심볼을 고를 것 — 많이 쓰이는 것은 수동 정답을 만들기 어렵다.

**측정할 것:**
- 정답 대비 누락(false negative)
- 정답에 없는 것이 나옴(false positive) — 주석·문자열 리터럴을 긁는지
- `uint64_t` 비트마스크 사례가 잡히는가 ← grep이 틀렸던 그 케이스

**정지 조건**: 누락이 없고 오검출이 이해 가능한 수준이면 통과.

### Task 5 — U2 판정: 선별 질의로 충분한가

상위 40개만 질의했을 때 보고서를 쓸 수 있는지 확인한다.

**측정할 것:**
- 40개 질의에 걸린 시간
- background index 완료까지 걸린 시간
- 40개 밖의 심볼이 보고서에 필요해지는 빈도

**정지 조건**: 충분하면 clangd 확정. 부족하면 §7로.

---

## 6-1. E6 실행 결과 (🔵 2026-08-27 — 전부 이 세션에서 돌린 명령의 출력)

구현물: `$REPO_ROOT/codegraph/clangd_refs.py` (stdio JSON-RPC 클라이언트, E6).
프로브: 같은 디렉토리의 `probe_task3.py` · `probe_index_completeness.py` · `probe_cold.py` · `probe_fullscan.py`.

### Task 3 통과 — `textDocument/references` 가 응답한다

`SJH::Scene::Component`(`src/scene/actor.h:58:11`, 위치는 clang-uml 이 준 것) 질의 결과
**참조 45건**, 소요 0.01s(웜). `apps/_MyApp_/...` 의 크로스파일 참조까지 잡힌다.

### 조인 키 — USR 은 안 실려 온다 (E7 이 최우선으로 지정한 확인 항목)

응답 레코드 원문:

```json
{"range": {"end": {"character": 19, "line": 57}, "start": {"character": 10, "line": 57}},
 "uri": "file:///.../src/scene/actor.h"}
```

🔵 **키가 `range` 와 `uri` 뿐이다. USR 이 없다.** 따라서 **조인 키는 위치(파일:줄:열)** 여야 한다.
E7 의 💭 80("USR 로 통일하는 것이 안전해 보인다")은 **clangd 쪽에서 성립하지 않는다.**
LSP 는 0-based, clang-uml 은 1-based 이므로 변환이 필요하다(클라이언트가 흡수했다).

⚠ **E5(libclang)로 갈아끼울 때 여기가 접합점이다.** libclang 은 USR 을 준다. 두 엔진의 산출물을
같은 모양으로 두려면 **위치를 정본 키로 쓰고 USR 은 부가 필드**로 두는 편이 안전하다.

### 인덱스는 compdb 디렉토리 옆에 디스크로 남는다

🔵 위치 = **`<compdb-dir>/.cache/clangd/index/`** — 프로젝트 루트가 아니다.
이 저장소에서는 `build_cc/.cache/clangd/`, **샤드 1602개 / 15 MB**.
`.gitignore` 의 `build_cc/` 에 이미 걸려 커밋되지 않는다(🔵 `git check-ignore` 확인).

### ⚠ 가장 중요한 발견 — 콜드 인덱스는 부분 결과를 조용히 돌려준다

인덱스가 없는 상태에서 같은 질의를 반복하면:

```
경과(s)  참조수
   0.6      7
   5.6     15
  10.7     15
  15.7     45   <- 웜 상태의 정답에 도달
```

🔵 **에러도, 미완성 표시도, 경고도 없다.** 7건을 받은 쪽은 그것이 전부인 줄 안다.
웜 상태에서는 120초 내내 45로 고정이므로, **"안정됐다" 는 것만으로는 완성을 보장하지 못한다** —
위 표에서 10.7s 지점의 15건도 두 번 연속 같은 값이었다.

> **이것이 사용자 우선순위 #1(반증 가능성 제거·결정론적 증거)을 정면으로 위협한다.**
> 같은 명령이 실행 시점에 따라 다른 답을 내고, 틀린 답이 틀렸다고 말하지 않는다.
> **파이프라인은 인덱스 완성을 확인한 뒤에만 질의해야 하고, 그 확인 수단이 아직 없다.**
> 💭 70 — clangd 의 `$/progress` 알림(indexing)을 받아 완료를 기다리는 것이 정공법으로 보이나
> **미검증** 이다. 값이 안정될 때까지 폴링하는 것은 위 15건 사례처럼 오답을 낼 수 있다.

### 전수 비용 — E7 의 💭 65 가 확인됐다

🔵 1차 심볼 **102개 전수 질의**(웜 인덱스, 선언 제외):

| 측정 | 값 |
|---|---|
| 총 소요 | **24.9초** |
| 질의당 평균 | 244ms (p50 238 / p95 602 / max 780) |
| 연 파일 | 63개 |
| 수집한 역참조 | **1,747건** |
| 실패 | **0건** |

> ⚠ **E5 의 근거가 이 규모에서는 약해진다.** §7 이 "전수는 clangd 로 심볼 수만큼 왕복이라 비싸다"
> 를 전제로 libclang 을 지목했는데, 🔵 실측은 **25초**다. 콜드 인덱스 구축까지 더해도 1분 안쪽이다.
> 💭 75 — 이 저장소 규모에서는 **clangd 로 전수를 돌리는 것이 실용적**이며, E5 의 시급성이 낮다.
> **다만 위의 부분 결과 문제가 해결되지 않으면 전수의 신뢰도 자체가 성립하지 않는다.**
> 판단은 사용자 몫이다.

---

## 7. 판단을 가르는 단 하나의 질문

> **선별 질의(상위 40개)로 충분한가, 전수 역참조가 필요한가.**

| 답 | 선택 |
|---|---|
| 선별로 충분 | **clangd** — 환경 함정 자동 처리가 이득 |
| 전수가 필요 | **libclang 직접** — 1회 순회가 자연스러움 |

**다른 기준으로 정하지 말 것.** 인지도는 둘 다 LLVM이라 동률이고, 설치도 `brew install llvm` vs `pip install libclang`으로 동률이다. **이 질문 하나만 갈린다.**

### 🔵 판정 결과 (2026-08-27 사용자 확정)

> **답 = 전수가 필요하다. 따라서 `libclang` 직접.**

⚠ **이 선택이 무엇을 버리는지 명시해 둔다.** 이번 세션에서 🔵 로 증명한 clangd 의 유일한 우위가
**환경 함정 자동 처리**(§3-6 — 두 clangd 모두 주입 0건으로 통과)였는데, libclang 직접은 그것을
**직접 처리해야 한다.** `-resource-dir` 과 `-isysroot` 를 손으로 넣어야 하고,
clang-uml 이 두 번 실패한 그 지점을 다시 밟는다.

**그럼에도 §7 의 규칙대로 U2 가 이겼다.** 전수 역참조는 clangd 로는 심볼 수만큼 왕복이라
비싸고, libclang 은 1회 순회로 자연스럽다. 다른 기준으로 뒤집지 않는다.

**clangd 는 폐기가 아니라 폴백이다.** libclang 이 환경 함정을 못 넘기면 §9 의 부활 트리거대로
되돌아온다. 그때의 어댑터는 E6(stdio JSON-RPC 직접)로 이미 정해져 있다.

---

## 8. 미확인 항목 전체 목록

이 인계의 첫 작업은 이것들을 확인하는 것이다.

| # | 항목 | 현재 | 확인 방법 |
|---|---|---|---|
| 1 | multilspy GitHub star 수 | 🔵 **600** | 완료 |
| 2 | multilspy가 C++에서 실제로 도는가 | 🔵 **PyPI 0.0.15 = 불가(`cpp` enum 없음) / git main = 가능** | 완료 (§3-1) |
| 3 | solidlsp 성숙도·star 수 | 🔵 **Serena 28.5k stars, MIT. 단 PyPI 독립 패키지 없음** | 완료 |
| 4 | clangd가 환경 함정을 자동 처리하는가 | 🔵 **통과. Apple 21 · Homebrew 22 둘 다 0 errors, 주입 0건** | 완료 (§3-6) |
| 5 | background index 완료 시간 | 💭 미측정 | Task 5 |
| 6 | 40회 질의 소요 시간 | 💭 미측정 | Task 5 |
| 7 | `textDocument/references` 정확도 | 💭 미측정 | **Task 4** |
| 8 | 중첩 타입(`Program::UniformBlock`) 표기 | 💭 미확인 | Task 4 |
| 9 | 선별 40개로 충분한가 | 💭 미검증 | **Task 5 = U2** |
| 10 | libclang 직접의 실제 구현 분량 | 💭 60~120줄 추정 | 만들어봐야 앎 |
| 11 | compdb 필드가 `command`인가 `arguments`인가 | 🔵 **`command`** (키 4종: command·directory·file·output) | 완료 |
| 12 | scip-clang v0.4.0 릴리스 날짜 | 💭 미확인 | (폴백이라 우선순위 낮음) |

### 🔵 갱신 후 새로 생긴 항목

| # | 항목 | 현재 |
|---|---|---|
| 13 | **어댑터 순서 재선정** | 🔵 1·2번이 배포 기준에서 걸렸다(§4 갱신). 순서를 다시 정해야 한다 |
| 14 | multilspy 를 쓴다면 **git 커밋 해시 핀 정책** | 💭 미정 |
| 15 | ~~경로 표기 불일치~~ | 🔵 **해결됨 2026-08-27.** 이 문서가 `build-cc`(하이픈)로 쓰던 것을 대상 저장소의 실제 이름 **`build_cc`(언더스코어)** 로 일괄 교정했다. 그 전에는 §6 명령을 그대로 붙여넣으면 전부 실패했다 |
| 16 | 저장소 `.clangd` 의 compdb 경로 | 🔵 `CompilationDatabase: build_ninja` 를 가리킨다. 설정 버그는 아니지만(사용자 정상 워크플로) 파이프라인은 `--compile-commands-dir` 로 매번 덮어써야 한다 |
| 17 | **Task 4 정답 목록** | 🔵 **아직 하나도 없다.** 참조 5~10건짜리 작은 심볼을 골라 손으로 만들어야 한다 |

**이제 7·8·9가 핵심이다.** 4는 닫혔다. 나머지는 이 셋을 확인하는 과정에서 딸려 나온다.
**9(U2)가 §7의 "판단을 가르는 단 하나의 질문" 이고 아직 안 닫혔다.**

---

## 9. 기각안 + 부활 트리거

| 기각안 | 사유 | 부활 트리거 |
|---|---|---|
| **scip-clang** | 🟡 star 91개, 패키지 매니저 없음 | SCIP 인덱스를 Sourcegraph에 올리거나 크로스레포 네비게이션이 필요할 때 |
| **clangd `.idx` 직접 파싱** | 🟡 서드파티 파서 부재. `clangd-indexer`·`dexp`는 Homebrew llvm에 미포함 | 없음. `.idx`를 읽는 대신 질의하면 된다 |
| **Doxygen `<referencedby>`** | 🟡 공식 문서가 오버로드·매크로에서 부정확할 수 있다고 명시 | Doxygen을 이미 돌리고 있어 부수적으로 얻을 수 있을 때 |
| **GNU GLOBAL (gtags)** | 🟡 내장 C++ 파서가 6.6.5부터 deprecated | 없음 |
| **universal-ctags / cscope** | 🟡 C++ 오버로드·템플릿 해석 불가. grep과 같은 실패를 반복 | 없음 |
| **ccls / rtags** | 💭 활동성 미확인, 데몬형 | clangd가 막힐 때 |
| **CodeQL** | 🟡 비오픈소스 개인 프로젝트 사용 불가 | 프로젝트를 오픈소스로 공개할 때 |
| **Understand (SciTools)** | 🟡 상용 구독 ($100~120/월) | 없음 |
| **고아 헤더 대응 도구 전반** | E3으로 범위 밖 | 남의 코드베이스에서 고아 헤더 누락이 실제 문제가 될 때 |

---

## 10. 작업 규약

- **확신도는 🔵/🟡/💭 + 정수.** 🔵는 **이번 세션에서 실제로 돌린 명령의 출력**만 인정한다. 문서를 읽은 것은 🟡다.
- **모르면 비워라.** 표의 칸을 추측으로 채우지 말 것. 빈칸은 정보다.
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- **표본이 아니라 전수로 재라.** 표본 10건이 100% 통과하고 전수 203건에서 함정이 드러난 전례가 있다.
- 사용자는 **구현물보다 의사결정용 보고서를 먼저** 받기를 선호한다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.** 이전 인계 초안이 그 이유로 반려된 적이 있다.
- **도구를 고르는 것이 이 작업의 목적이 아니다.** §7의 질문에 답할 데이터를 모으는 것이 목적이고, 선정은 사용자가 한다.

---

## 11. 첫 작업

**Task 1과 Task 2를 지금 실행하라.** 설치가 필요 없거나 `brew install llvm` 하나면 되고, Task 2 결과 하나가 §5(libclang 전환) 여부를 크게 가른다.

```bash
which clangd && clangd --version
clangd --compile-commands-dir=build_cc --check=src/render/renderer.cpp
```

에러가 나면 **그 에러 메시지 전문을 사용자에게 보여줄 것.** 무엇을 주입해야 하는지가 거기 적혀 있다. 미리 플래그를 넣지 말 것 — 정말 필요한지 모른 채로 가게 된다.
