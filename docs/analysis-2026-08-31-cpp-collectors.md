# 분석 — C++ 정적 수집기는 왜 여럿인가, 하나로 합칠 수 있는가

> 작성 2026-08-31 · 대상 `machine/` 의 정적 수집 계층
> 표기 — 🔵 이번 세션에서 직접 읽은 `파일:함수` 또는 직접 돌린 명령의 출력 · 🟡 저장소 문서에
> 기록된 실측(이번에 재측정하지 않음) · 💭 위 둘에서 끌어낸 판단(사실이 아니다)

---

## 0. 먼저 — 질문의 전제 하나가 실측과 어긋난다

**"C++ 이 세 모듈을 쓴다" 는 현재 배선과 다르다.** 파이프라인이 실제로 돌리는 것은 **둘**이다.

🔵 `runner/wiki/prep.mjs` 의 `prepPlan` — 수집기가 `clang-uml` 일 때 나오는 단계는
`["clang-uml", (clang-doc), "normalize", "facts", "render-modules"]` 다. `clangd` 는 이 목록에 없다.

🔵 저장소 전체를 훑어 `reverse_refs` · `clangd` 를 부르는 자리를 찾았다. `machine/clangd_refs.py` 와
`machine/reverse_refs.py` 를 **실행하는 코드는 저장소에 하나도 없다.** 나오는 것은 문서 참조뿐이다
(`ARCHITECTURE.md` 의 import 표 · `README.md` 의 선택 도구 표 · `docs/handoffs/` 여러 건).

🔵 `docs/handoffs/HANDOFF-clangd-reverse-refs.md` 머리에 **"보류 (사용자 확정)"** 배너가 붙어 있고,
사유가 그대로 적혀 있다 — *"현재 파이프라인 어느 단계도 이것을 입력으로 받지 않는다."*

| 도구 | 상태 | 근거 |
|---|---|---|
| `clang-uml` | **배선됨.** 반드시 돈다 | 🔵 `prep.mjs::prepPlan` |
| `clang-doc` | **배선됨.** 찾으면 돌고, 없으면 그 단계만 빠진다 | 🔵 `prep.mjs::prepPlan` — `hasClangDoc` 가 거짓이면 단계에서 빠질 뿐 막지 않는다 |
| `clangd` | **보류된 별개 갈래.** 코드는 남아 있으나 아무도 부르지 않는다 | 🔵 전수 grep · 🔵 보류 배너 |

💭 그러므로 "모듈이 3개로 나눠져 있다" 는 체감의 절반은 **죽은 코드가 살아 있는 것처럼 보이는 것**이
원인이다. 이것 자체가 실재하는 결함이고, 아래 §5 에서 다시 다룬다.

---

## 1. 각 모듈의 역할과 도입 동기

### 1-1. `clang-uml` — 관계의 *종류*를 아는 유일한 도구

🔵 `clang-uml --version` → `clang-uml 0.6.3` · `/opt/homebrew/bin/clang-uml`.
서드파티 UML 다이어그램 생성기이고, `-g json` 으로 요소 배열과 **관계 배열**을 낸다.

**도입 동기** — 이 저장소의 코드 지도(`codegraph.json`)는 간선에 8종 `kind` 를 요구한다
(🔵 `machine/codegraph_types.py::EdgeKind` — `composition` · `aggregation` · `dependency` ·
`instantiation` · `friendship` · `inheritance` · `realization` · `association`).
그 여덟 낱말을 **C++ 소스에서 판별해 주는 도구가 이것뿐이었다.**

🔵 `machine/normalize.py::CLANG_UML_KIND` 가 그 낱말을 옮기는데, 항등 사상이 아니다 —
`aggregation → composition`(값 멤버는 UML 합성), `association → aggregation`(포인터·참조 멤버는 집약).
🔵 `machine/test_normalize.py::test_clang_uml_kind_is_not_identity` 가 이 뒤집힘을 못박고 있다.

### 1-2. `clang-doc` — 심볼 *전량*을 아는 도구

🔵 `node runner/wiki/clang-doc.mjs` → `/opt/homebrew/opt/llvm@22/bin/clang-doc`.
LLVM 공식 문서 생성기이고 PATH 에 없어 따로 찾아야 한다 (🔵 `runner/wiki/clang-doc.mjs::clangDocPath`).

**도입 동기 — 이것이 이 보고서의 핵심이다.** 🔵 커밋 `022b89c` (2026-08-30,
`[feat] : cpp - clang-doc 심볼 전량 수집기와 clang-uml 병합`) 로 들어왔다.
사유는 🔵 `docs/handoffs/HANDOFF-2026-08-29-cpp-clang-doc-vs-clang-uml.md` 에 적혀 있다:

> 🟡 2026-08-29 QtVisionEdit 실측 — `clang-uml` 이 낸 1차 노드 30개는 **전부 타입**이다.
> 핵심 로직(`ComputePanorama` · `GetGoodMatches` · `BroadcastChannels`)은 네임스페이스 안
> **자유 함수**라 하나도 안 잡혔다.

같은 문서의 대조표(🟡): 자유 함수 **clang-uml 0개 대 clang-doc 236개**, 레코드 30 대 64,
저자 문서 주석 없음 대 63개 파싱됨, 시그니처 없음 대 있음.

**즉 clang-doc 은 "더 나은 도구로 갈아탄 것" 이 아니라 clang-uml 이 구조적으로 못 보는 층을
메우려고 들어온 것이다.** 🔵 `machine/normalize.py::merge_clang_doc` 의 독스트링이 병합 규칙을
그대로 적고 있다 — 노드는 합집합, 같은 이름이면 **위치는 clang-doc 이 이긴다**(clang-uml 의
`source_location` 은 첫 사용 지점을 가리키는 버릇이 있다), **간선은 손대지 않는다**(clang-doc 에
관계 분류가 없다).

### 1-3. `clangd` — 역방향 참조를 물어볼 수 있는 도구

🔵 `/usr/bin/clangd` · `Apple clangd version 21.0.0`.
🔵 `machine/clangd_refs.py::Clangd` 가 stdio JSON-RPC 로 언어 서버에 직접 말을 걸고,
🔵 `machine/reverse_refs.py` 가 1차 심볼 전량에 `textDocument/references` 를 돌린다.

**도입 동기** — 앞의 둘이 답하지 못하는 질문 하나가 있다. **"이 심볼을 누가 쓰는가."**
clang-uml 도 clang-doc 도 *선언*과 *타입 관계*만 낸다. 호출자 목록은 어느 쪽에도 없다.

🔵 `docs/handoffs/DECISION-cpp-symbol-index.md` 에 그 조사 기록이 남아 있다. 후보는 셋이었고
탈락 사유가 전부 **파이프라인 적합성**이었지 분석 능력이 아니었다 —
`scip-clang` 은 패키지 매니저 부재(GitHub 릴리스 수동 다운로드)와 star 91개,
`ccls` 는 데몬형이라 배치 소비 경로 불명확, `clangd` 는 `.idx` 가 내부 형식.

🔵 그 다음 문서(`HANDOFF-clangd-reverse-refs.md` §1)가 마지막 근거를 뒤집는다 —
*".idx 를 읽을 필요가 없다. clangd 를 띄워서 물어보면 된다."*
그렇게 `clangd` 로 갔다가, 사용자가 "전수 역참조" 를 확정하면서 최종 엔진을 `libclang` 직접으로
바꾸고(E5), `clangd` 는 **먼저 가는 중간 단계**(E7)로 남았다. 그리고 파이프라인이 이 산출물을
소비하지 않는다는 이유로 **갈래 전체가 보류됐다.**

---

## 2. 서로가 하지 못하는 것

🔵 `machine/codegraph_types.py::Node` · `Edge` 가 요구하는 칸을 기준으로, 누가 무엇을 채우는가.

| 코드 지도가 요구하는 것 | clang-uml | clang-doc | clangd(보류) | roslyn-dump(C#) |
|---|---|---|---|---|
| 클래스·구조체 노드 | ✅ | ✅ | — | ✅ |
| **네임스페이스 자유 함수 노드** | ❌ 0개 | ✅ | — | (해당 없음, §3) |
| 노드의 `file` · `line` | △ 첫 사용 지점 편향 | ✅ 정확 | ✅ | ✅ |
| 노드의 `signature` · `doc` | ❌ | ✅ | ❌ | ✅ |
| **간선 8종 `kind` 분류** | ✅ **유일** | ❌ | ❌ | ✅ |
| 상속·실현 | ✅ | ✅(관계 분류 없이) | ❌ | ✅ |
| **역방향 참조(누가 쓰는가)** | ❌ | ❌ | ✅ **유일** | ❌ |
| **호출 관계 `calls[]`** | △ §4-2 | ❌ | △ 역참조로 근사 | ❌ 명시적 미구현 |

몇 칸은 근거를 따로 적는다.

- **clang-uml 의 자유 함수 0개** — 🟡 문서 기록. 원인은 도구 성격이다. 클래스 다이어그램
  생성기이므로 타입에 매달리지 않은 함수는 애초에 모델에 들어오지 않는다.
- **clang-uml 의 위치 편향** — 🔵 `machine/normalize.py::SourceLocation` 독스트링:
  *"남의 헤더가 아니라 이 저장소의 첫 사용 지점을 가리키는 버릇이 있다."*
  그래서 `is_first_party` 가 거름망 세 겹을 갖는다.
- **clang-uml 의 글로브 붕괴** — 🟡 깊이 4 이상 글로브에서 정규식 복잡도 오류로 죽는다.
  그래서 🔵 `runner/wiki/compdb.mjs::clangUmlConfig` 가 글로브를 쓰지 않고 파일을 열거한다.
- **clang-doc 의 출력 흩어짐** — 🔵 `machine/clang_doc.py` 머리 주석이 "형식의 급소 다섯" 으로
  적어 뒀다. 네임스페이스 배열이 **안쪽부터** 오고, `Location` 없는 요소가 섞이고,
  `Description` 이 리스트의 리스트이고, `index.json` 은 얕은 참조뿐이며, 전역 네임스페이스에
  `GlobalNamespace` 라는 가짜 이름이 붙는다. **다섯 개 전부 틀려도 오류가 나지 않는 자리다.**
- **C# 도 호출 관계가 없다** — 🔵 `machine/roslyn-dump/Program.cs` 주석:
  *"foo.Bar() 호출은 내지 않는다 — 그것은 calls[] 이고 Track C §7 이 '나중에 붙일 자리' 로 못박았다."*
  이 구멍은 C++ 만의 문제가 아니다.

**한 줄 요약** — clang-uml 은 *관계를 분류할 수 있으나 함수를 못 본다*, clang-doc 은
*함수를 전부 보지만 관계를 분류하지 못한다*. 겹치는 부분이 아니라 **서로의 사각을 메운다.**

---

## 3. 그러면 C# 은 왜 하나로 되는가 — 도구 성숙도가 아니라 **언어 구조**다

여기가 가장 오해하기 쉬운 자리다. "C++ 이 더 오래됐으니 도구가 더 좋을 것" 은 성립하지 않는다.
차이의 원인은 셋이고, 전부 도구 품질과 무관하다.

**(가) C# 에는 자유 함수가 없다.** 모든 메서드는 타입의 멤버다. 그래서
🔵 `machine/roslyn-dump/Program.cs` 의 `TypeRec` 이 `Members` 와 `Methods` 를 **타입 안에** 담는
것만으로 심볼 공간이 전부 덮인다. C++ 은 네임스페이스 스코프에 함수가 산다 — 타입 중심 모델이
구조적으로 놓치는 층이 존재한다. **clang-doc 이 필요한 이유가 정확히 이것이다.**

**(나) C# 에는 공개된 의미 분석 API 가 하나 있다.** Roslyn 의 `CSharpCompilation` +
`SemanticModel` 이 심볼·타입·위치·상속·제네릭 인자를 **한 객체 모델로** 준다.
🔵 `Program.cs` 는 527줄짜리 우리 프로그램이고, 그 안에서 타입 등록·상속·실현·필드 연관·
메서드 의존을 한 번에 뽑는다. C++ 진영의 대응물은 libclang / LibTooling 인데, **거기에는
"저장소 전체를 JSON 으로 덤프해 주는 공식 프론트엔드" 가 없다.** clang-doc 은 문서 생성기,
clang-uml 은 다이어그램 생성기, clangd 는 에디터 서버다 — 셋 다 *다른 목적으로 만들어진 것을
빌려 쓰는* 중이다.

**(다) C# 쪽이 더 자동화돼 있지도 않다.** 🔵 `prep.mjs::prepPlan` 의 C# 갈래는 수집기를 **아예
돌리지 않는다** — `out/codegraph-raw/roslyn-dump.json` 이 이미 있어야 하고, 없으면 막힌다:
*"machine/roslyn-dump 를 dotnet 으로 먼저 돌려라."* 즉 C# 은 "도구 1개" 가 아니라
**"사람이 손으로 미리 돌려 둔 도구 1개 + Unity 가 생성해 준 `Assembly-CSharp.csproj`"** 다
(🔵 `Program.cs` 가 그 파일이 없으면 즉시 종료한다).

💭 그러므로 비대칭의 정직한 서술은 이렇다 — **C++ 이 도구 셋을 쓰는 게 아니라, C# 이
"우리가 직접 짠 수집기 하나" 로 되는 언어인 것이다.** C++ 에 대해 같은 것을 하려면
libclang 위에 우리가 프로그램을 하나 짜야 하고, 그것이 §4 의 선택지 D 다.

---

## 4. 하나의 모듈로 만든다면 무엇이 구현돼야 하는가

### 4-1. 대체 도구가 반드시 채워야 하는 칸 — 현 파이프라인이 실제로 읽는 것만

새 도구를 판단하는 기준은 "C++ 을 잘 분석하는가" 가 아니라 **"아래 칸을 전부 채우는가"** 다.
근거는 🔵 `machine/codegraph_types.py` 와 🔵 `machine/normalize.py::merge_clang_doc` ·
`normalize_cpp` 가 실제로 읽는 열쇠들이다.

| # | 요구 | 왜 필수인가 | 지금 채우는 것 |
|---|---|---|---|
| R1 | 타입 노드 + `파일:줄` | 인용 검증 L1/L2/L3 의 대상 (🔵 `machine/verify_citations.py`) | clang-uml + clang-doc |
| R2 | **자유 함수 노드** + `파일:줄` | C++ 로직의 다수가 여기 산다 | **clang-doc 만** |
| R3 | **간선 8종 분류** (합성/집약/의존/인스턴스화/우정/상속/실현/연관) | `EdgeKind` 계약. 소유 판정이 이 위에 선다 | **clang-uml 만** |
| R4 | 간선의 근거 위치(멤버 이름 + `파일:줄`) | 🔵 `test_normalize.py::test_golden_ownership_edges_all_have_location` 이 못박음 | clang-uml `members[]` |
| R5 | 시그니처 · 저자 문서 주석 | 🔵 `codegraph_types.py::Node` 의 `signature` · `doc` | **clang-doc 만** |
| R6 | 1차/외부 판정에 쓸 네임스페이스 | 🔵 `normalize.py::is_first_party` 세 겹 거름망의 첫 겹 | 둘 다 |
| R7 | `compile_commands.json` 배치 소비 | 데몬·에디터 전제면 파이프라인에 못 들어온다 | 둘 다 |
| R8 | 파이썬이 읽을 수 있는 안정 출력 형식 | 🔵 `DECISION-cpp-symbol-index.md` 의 C6 — 이 조건이 과거 후보 셋 중 둘을 탈락시켰다 | 둘 다 JSON |
| R9 | 패키지 매니저 설치 | 🔵 같은 문서 — scip-clang 탈락의 절반이 이 조건 | brew 둘 다 |
| — | (역방향 참조) | **현재 소비자가 없다.** 보류 사유 그 자체 | 아무도 |

**R3 과 R2 를 동시에 만족하는 기성 도구가 없다는 것이 지금 둘을 쓰는 이유다.** 이 표에서
한 칸만 비어도 `normalize.py` 를 고쳐야 하고, 골든 시험(🔵 C++ 191노드/417간선 ·
C# 231노드/540간선, `test_normalize.py::test_golden_counts`)이 깨진다.

### 4-2. 선택지

| | 방식 | R2(함수) | R3(관계 분류) | 대가 |
|---|---|---|---|---|
| **A** | **지금 그대로** — clang-uml + clang-doc, clangd 는 정리 | ✅ | ✅ | 외부 도구 2개 의존. 병합 규칙 유지 비용 |
| B | clang-doc 만 | ✅ | ❌ **8종이 무너진다** | `EdgeKind` 계약 파기 → `codegraph.json` 스키마 v3 |
| C | clang-uml 만 (+ 시퀀스 다이어그램) | △ 4-3 참조 | ✅ | 전수 덤프가 아니라 시작점 지정형 |
| D | libclang 직접 — C# 의 `roslyn-dump` 대응물을 우리가 짠다 | ✅ | ✅ (우리가 판별) | 🔵 `DECISION-cpp-symbol-index.md` §3 한계 1 — 번역 단위 기반이라 **고아 헤더는 여전히 안 보인다.** 환경 함정(`-resource-dir` · `-isysroot`)을 손으로 주입해야 한다 |

🔵 선택지 C 의 근거 — `clang-uml --help` 에 `--add-sequence-diagram` 이 있다. 시퀀스 다이어그램은
호출 사슬을 담으므로 자유 함수가 모델에 들어온다. 🟡 다만 같은 도움말에 `--print-from` /
`--print-to` 가 함께 있다 — **시작점을 지정해야 하는 다이어그램**이지 저장소 전량 심볼 덤프가
아니다. 💭 70 — 전수조사 입력으로 쓰려면 "모든 함수를 시작점으로 N번 돌린다" 가 되어
비용과 중복 관리가 clang-doc 한 번보다 나빠 보인다. **재보고 없이 확정하지 말 것.**

### 4-3. 권고

**선택지 A 를 유지하고, 대신 §5 의 정리 작업을 한다.** 근거 셋:

1. 🔵 병합 지점이 **함수 하나**다 (`normalize.py::merge_clang_doc`, 45줄). 도구가 둘이라는
   사실이 코드 전체에 번지지 않는다. `prep` 단계 하나와 병합 함수 하나가 전부다.
2. 🔵 `prepPlan` 이 clang-doc 없는 기계에서 **막지 않고 단계만 뺀다.** 결합이 이미 느슨하다.
3. 💭 85 — 선택지 D 는 C# 이 하나로 되는 이유를 C++ 에서 재현하려는 시도인데, 그 대가로
   **우리가 유지보수해야 할 컴파일러 프론트엔드 프로그램이 하나 늘어난다.** 🔵 `roslyn-dump` 가
   527줄인데 그것은 Roslyn 이 의미 모델을 통째로 주기 때문이고, libclang 은 그만큼 주지 않는다.
   구현자 1 · 소비자 1 인 도구에서 이 교환은 `CLAUDE.md` 가 경고하는 **거울 함정**에 가깝다.

**선택지 D 를 되살릴 조건** — ① `calls[]`(호출 관계)가 실제로 필요해졌을 때. 🔵 그 자리는 C# 쪽에도
비어 있으므로 두 언어를 한 번에 결정해야 한다. ② clang-uml 또는 clang-doc 이 상류에서 깨져
우회가 필요할 때.

---

## 5. 지금 당장 해소할 수 있는 것 — "셋으로 보이는" 착시

이 조사의 실질적 발견은 도구 개수가 아니라 **문서와 코드가 배선되지 않은 갈래를 살아 있는 것처럼
보여 준다**는 점이다. 🔵 근거:

| 자리 | 지금 적힌 것 | 실제 |
|---|---|---|
| `README.md` 필요한 것 표 | `선택 · clangd · C++ 역참조를 뽑을 때만` | 어떤 명령도 clangd 를 부르지 않는다 |
| `ARCHITECTURE.md` §4 import 표 | `reverse_refs.py → clangd_refs` 를 살아 있는 의존으로 나열 | 그 위를 부르는 진입점이 없다 |
| `ARCHITECTURE.md` §7 "새 정적 수집기" | *"지금은 **둘 고정**"* · C++/C# 만 | 🔵 실제로는 **셋**이다 — `paths.mjs::collectorFor` 가 `griffe+pycalls`(Python)를 낸다 |
| `machine/` | `clangd_refs.py` · `reverse_refs.py` 가 다른 생산 파일과 나란히 산다 | 보류 갈래 |

제안(사용자 판정 필요, 착수하지 않았다):

1. `README.md` · `ARCHITECTURE.md` 의 clangd 항목에 **"보류 갈래 — 현재 파이프라인이 부르지 않는다"**
   한 줄을 붙인다. 코드는 지우지 않는다 — 되살릴 조건이 문서에 남아 있다.
2. `ARCHITECTURE.md` §7 의 "수집기 둘 고정" 을 **셋**으로 고친다. 🔵 Python 갈래가 2026-08-30 에
   들어왔는데 그 절만 낡았다.
3. 💭 60 — `machine/` 안에 보류 갈래를 담을 자리를 따로 둘지는 **미결정**이다. 파일 둘 때문에
   디렉토리를 새로 파는 것은 그 자체가 과잉일 수 있다. 주석 한 줄이 더 싸다.

---

## 6. 확신할 수 없는 것

- **clang-doc 병합 이후의 QtVisionEdit 실측 노드·간선 수**를 이번에 재측정하지 않았다.
  §1-2 의 236 · 30 · 64 는 전부 2026-08-29 문서 기록(🟡)이다.
- **선택지 C(clang-uml 시퀀스 다이어그램)의 실효성**은 도움말 플래그만 보고 판단했다.
  실제로 돌려 보지 않았다.
- **선택지 D 의 구현 규모**를 추정하지 않았다. `roslyn-dump` 527줄은 Roslyn 기준이고
  libclang 기준의 대응 규모는 모른다.
