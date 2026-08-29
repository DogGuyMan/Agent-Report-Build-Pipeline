# HANDOFF — C++ 정적 수집기 둘을 합친다 (clang-doc + clang-uml)

> **작성** 2026-08-29 · **수신** 다른 Claude Code 에이전트
> **한 줄** — `clang-uml` 은 클래스 *관계*를 알고 `clang-doc` 은 심볼 *전량*을 안다.
> 둘을 합쳐 C++ 을 C#(roslyn-dump) 수준으로 올린다.
>
> 이 문서 하나만 읽고 착수할 수 있어야 한다. 다른 문서는 심화 자료이지 전제가 아니다.

---

## 1. 왜 이 일이 필요한가

report-builder 의 Mode 1(코드베이스 위키)은 정적 수집기가 낸 코드 지도 위에 LLM 전수조사를 얹는다.
C# 은 `roslyn-dump` 가 심볼 전량을 내주는데, **C++ 은 `clang-uml` 뿐이고 그것은 클래스 도구다.**

🔵 2026-08-29 실측 (대상: QtVisionEdit) — `clang-uml` 이 낸 1차 노드 30개는 **전부 타입**이다.
그런데 이 저장소의 핵심 로직(`ComputePanorama` · `GetGoodMatches` · `BroadcastChannels` …)은
네임스페이스 안 **자유 함수**라 하나도 안 잡혔다. 함수 층이 통째로 비어 있고,
그 구멍을 지금은 LLM 이 손으로 메우고 있다.

---

## 2. 두 도구 — 실측 대조

**둘 다 이미 설치돼 있다.** 새로 깔 것이 없다.

| | `clang-uml` | `clang-doc` |
|---|---|---|
| 정체 | C++ 전용 **UML 다이어그램 생성기** (서드파티) | **LLVM 공식 문서 생성기** (LLVM 번들) |
| 버전·위치 | 0.6.3 · `/opt/homebrew/bin/clang-uml` (**PATH 에 있음**) | Homebrew LLVM 22.1.8 · `/opt/homebrew/opt/llvm@22/bin/clang-doc` (**PATH 에 없다 — 절대경로로 부른다**) |
| 입력 | `compile_commands.json` + `.clang-uml` 설정 | `compile_commands.json` (`--executor=all-TUs`) |
| 출력 | `-g json` → 요소 + **관계** 배열 | `--format=json` → 네임스페이스 트리, 파일 여럿 |

### 실측 산출 (QtVisionEdit, 합친 compdb 46 TU 기준)

| 잡는 것 | clang-uml | clang-doc |
|---|---|---|
| 자유 함수 | **0** | **236** (전부 `파일:줄` 붙음) |
| 레코드(class/struct) | 30 (1차) | **64** |
| enum | 포함 | 4 |
| 저자 문서 주석 | **없음** | **63개 파싱됨** (`Description`) |
| 상속 (`Parents`/`Bases`) | 있음 | **있음** |
| 멤버·메서드 | 이름만 | **접근 수준별** (`PublicMethods` · `PrivateMembers`) |
| 시그니처 (반환형·인자) | 없음 | **있음** (`ReturnType` · `Params`) |
| **합성 / 집약 / 의존 구분** | **있음** ← 유일 | **없음** |

### 장단점 요약

**clang-uml 의 장점** — **관계의 종류를 분류한다.** 값 멤버는 합성, 포인터·참조 멤버는 집약,
그 밖은 의존으로 가른다. 우리 `normalize.py:27` 의 `CLANG_UML_KIND` 대응표가 이 분류를
codegraph 의 낱말로 옮기고, 그 위에서 소유 간선(C-13) 판정이 선다. **clang-doc 에는 이것이 없다.**

**clang-uml 의 단점** — ① 클래스만 본다(자유 함수 0) ② 문서 주석을 안 준다
③ 🔵 **글로브가 깊이 4 이상에서 죽는다** — `app/src/view/*.cpp` 로 주면
`ERROR: The complexity of an attempted match against a regular expression exceeded a pre-set level`.
같은 파일을 하나씩 열거하면 통과한다. `scripts/wiki/compdb.mjs` 의 `clangUmlConfig` 가
그래서 글로브를 쓰지 않는다.

**clang-doc 의 장점** — 심볼 전량 + 위치 + 시그니처 + **저자 문서 주석**.
`Location` 이 `{"Filename": "core/panorama/panorama.cpp", "LineNumber": 129}` 꼴로
**저장소 상대 경로**를 준다 — 우리 레코드의 `where` 에 그대로 들어간다.

**clang-doc 의 단점** — ① 관계의 종류를 안 나눈다 ② 출력이 **네임스페이스별 파일 여러 개**로
흩어진다(파일 91개). 모아 읽는 코드를 우리가 써야 한다 ③ 파일 이름이 맹글링된 심볼
(`_ZTVN3SJH6Server12SessionStoreE.json`)이라 경로로 찾지 말고 **내용을 훑어야** 한다.

### 결론 — 갈아타지 말고 **합친다**

```
clang-doc  ─→ 심볼 전량 (자유 함수 236 · 위치 · 시그니처 · 문서 주석)
clang-uml  ─→ 관계의 종류 (합성 / 집약 / 의존)
              ↓  둘을 normalize.py 에서 합침
        codegraph.json  (C# 수준)
```

---

## 3. 검증된 사실 — 착수 전 이 값들을 **직접 다시 확인하라**

> 저장소는 드리프트한다. 아래는 2026-08-29 기준이고, 그대로 믿지 말고 재측정한다.

| 사실 | 확인 명령 |
|---|---|
| report-builder 루트 | `readlink -f "$(which report-spec)"` → `<루트>/bin/report-spec` |
| `clang-doc` 위치 | `ls /opt/homebrew/opt/llvm@22/bin/clang-doc` |
| `normalize.py` CLI 는 `--clang-uml` / `--roslyn-dump` 배타 그룹 | `grep -n "add_argument" codegraph/normalize.py` (현재 647~650줄) |
| C++ 정규화 진입 | `normalize.py::normalize_cpp` (현재 264줄) |
| 관계 낱말 대응표 | `normalize.py::CLANG_UML_KIND` (현재 27줄) |
| 1차 판정 세 겹 | `normalize.py::is_first_party` — 네임스페이스 허용목록 → git 추적 → **그 줄이 정의하는가**(`defines_at`) |
| compdb 합치기 | `scripts/wiki/compdb.mjs` — `findCompdbs` · `mergeEntries` · `clangUmlConfig` |
| prep 배선 | `scripts/wiki/prep.mjs` 의 `"clang-uml"` 단계 |
| 시험 재료 | QtVisionEdit — `$CPP_REPO` 환경변수. 없으면 골든 테스트는 건너뛴다 |

**줄 번호를 인용할 때는 함수 이름을 함께 적어라.** 이 저장소는 `xmldoc.py inject` 가
주석 블록을 재주입하며 줄을 민다. 줄만 적은 인용은 하루면 낡는다.

---

## 4. 할 일

### STEP 1 — clang-doc 산출물을 읽는 함수를 만든다

**파일:** `codegraph/clang_doc.py` (신규)

`clang-doc --format=json` 은 네임스페이스마다 `index.json` 을 만들고, 그 안에
`Functions` · `Records` · `Enums` 배열을 둔다. 트리를 훑어 평평한 목록으로 만든다.

```python
def load_clang_doc(out_dir):
    """clang-doc 의 흩어진 index.json 을 모아 평평한 심볼 목록으로 만든다.

    파일 이름이 맹글링돼 있어 경로로 찾지 않는다 — index.json 만 훑는다.
    돌려주는 꼴: [{"name","kind","namespace","file","line","signature","doc"}]
    """
```

**요소 하나의 실제 모양** (🔵 실측):

```json
{"Name": "ComputePanorama",
 "Namespace": ["Panorama", "Core", "SJH"],          // ← 역순이다. 뒤집어 붙인다
 "Location": {"Filename": "core/panorama/panorama.cpp", "LineNumber": 129},
 "ReturnType": {"Name": "bool"},
 "Params": [{"Name": "images", "Type": {"Name": "const std::vector<cv::Mat3b> &"}}],
 "Description": {"ParagraphComments": [[{"TextComment": " images 를 순서대로 정합해 …"}]]}}
```

**함정 셋** — ① `Namespace` 는 **역순** 배열이다 ② `Location` 이 없는 요소가 있다(그 경우 버린다)
③ `Description` 은 중첩 리스트다. 글자만 뽑아 이어 붙인다.

### STEP 2 — 시험을 먼저 쓴다

**파일:** `codegraph/test_clang_doc.py` (신규). 합성 데이터로 위 세 함정을 못박는다.
**추가로 골든 시험 하나** — `$CPP_REPO` 가 있으면 실제 산출물에서 `ComputePanorama` 가
`core/panorama/panorama.cpp:129` 로 나오는지 본다(없으면 `pytest.skip`).

### STEP 3 — `normalize.py` 에 입력을 더한다

`--clang-doc <디렉토리>` 를 **선택 인자**로 더한다. `--clang-uml` 과 **배타가 아니라 함께** 쓴다.

```
normalize.py --clang-uml full_class.json --clang-doc clangdoc/json --repo <저장소> -o codegraph.json
```

합치는 규칙:

| | 이기는 쪽 | 이유 |
|---|---|---|
| 노드 목록 | **합집합** | clang-doc 이 함수를, clang-uml 이 관계 있는 타입을 낸다 |
| 같은 타입의 `where` | **clang-doc** | 시그니처까지 아는 쪽이 정확하다 |
| 간선의 `kind` | **clang-uml** | 관계 분류는 clang-doc 에 없다 |
| 1차 판정 | **기존 `is_first_party` 를 그대로 태운다** | 세 겹 거름망을 우회하지 마라 |

⚠ **함수 노드의 `kind`** 는 `function` 이다. `codegraph.json` 스키마의 `kind` 가 이 값을 받는지
먼저 확인하라 — C# 쪽(`normalize_csharp`)이 이미 어떻게 하는지 보면 된다.

### STEP 4 — `prep` 이 clang-doc 도 돌리게 한다

`scripts/wiki/prep.mjs` 의 `"clang-uml"` 단계 뒤에 `"clang-doc"` 단계를 더한다.
설정 생성은 `compdb.mjs` 가 이미 만든 **합친 compdb** 를 그대로 쓴다.

```js
run(CLANG_DOC, ["--executor=all-TUs", "--format=json", "--output", docOut,
                "--source-root", repo, "--ignore-map-errors",
                ...flags.flatMap((f) => ["--extra-arg", f]),
                join(compdbDir, "compile_commands.json")], repo);
```

**`clang-doc` 은 PATH 에 없다.** `scripts/python.mjs` 가 파이썬을 찾는 것과 같은 꼴로
`scripts/wiki/clang-doc.mjs` 에 `clangDocPath()` 를 두어 찾아라 —
환경변수 `CLANG_DOC` → `brew --prefix llvm@22`/bin → PATH 순. **경로를 박지 마라.**

### STEP 5 — 실측하고 보고한다

```bash
report-wiki prep "$CPP_REPO"
python3 -c "import json;d=json.load(open('$CPP_REPO/out/codegraph-raw/codegraph.json'));
print('노드',len(d['nodes']),'간선',len(d['edges']))"
```

**기대** — 노드가 39에서 크게 는다(clang-doc 이 함수 236을 낸다. 1차 거름망 통과분은 그보다 적다).
**정확한 수를 예언하지 마라. 나온 값을 그대로 보고한다.**

---

## 5. 경계 — 건드리지 말 것

| 파일 | 왜 |
|---|---|
| `codegraph/normalize.py` 의 `normalize_csharp` 와 그 아래 | C# 경로다. 이 작업과 무관하고 골든 시험이 231노드/540간선을 못박고 있다 |
| `codegraph/terms_db.py` | 사전 병합. 다른 작업(WarmUp)이 만질 수 있다 |
| `CPP_FIRST_PARTY_NS` · `defines_at` · `tracked_set` | 1차 판정 세 겹. **우회하지 말고 그대로 태워라.** 우회하면 Qt·OpenCV 타입이 1차로 샌다 |
| 대상 저장소의 소스 | 읽기만 한다 |

---

## 6. 검증

```bash
cd <report-builder 루트>
npm test                                            # 기대: fail 0
export GRAPHICS_REPO=... CSHARP_REPO=... CPP_REPO=...
.venv/bin/python -m pytest codegraph/ -q            # 기대: 골든 포함 전부 통과
npm run typecheck                                   # 기대: exit 0
.venv/bin/python codegraph/xmldoc.py check          # 기대: 문제 0건
report-wiki prep "$CPP_REPO" && report-wiki check "$CPP_REPO"   # 기대: exit 0
```

**골든 회귀가 급소다.** `pytest` 는 Graphics(C++ 191노드/417간선)와 StickRush(C# 231/540)를
못박고 있다. **이 둘이 깨지면 합치기 규칙이 틀린 것이다.**

---

## 7. 이 저장소의 규약 (반드시 지킬 것)

- **커밋하지 마라.** 사용자 승인 후 오케스트레이터가 한다. `git add -A` 금지, 경로를 좁혀라.
- **새 코드를 쓰면 그 자리에서 전수조사 레코드도 쓴다.** `docs/codegraph/terms-reading.json` 에
  `{kind, module, where, means, does?, uses[], confidence, source:"reading"}`. 그다음
  `xmldoc.py emit` → `inject` 로 주석 블록을 박는다. **코드와 좌표는 같은 커밋에.**
- `scripts/*.mjs` 는 **직접 실행 가드**를 둔다 — `if (process.argv[1]?.endsWith("x.mjs")) { … }`.
  없으면 시험이 import 하는 순간 `process.exit()` 이 러너를 죽인다.
- **경로를 코드에 박지 마라.** 환경변수와 탐색으로 찾는다(`scripts/python.mjs` 가 본보기).
- 주석과 문서는 **한국어**. 약어를 피하고 메커니즘을 먼저 쓴다.
- **거울 함정** — 수집기는 둘 고정이다. 플러그인 구조·레지스트리를 만들지 마라.

---

## 8. 보고

`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` 중 하나로 시작하고 아래를 담아라.

- 바뀐 파일 목록
- §6 검증 명령의 **실제 출력** (요약하지 말고 숫자를 그대로)
- 합치기 전후 노드·간선 수
- **판단이 갈렸던 자리**와 무엇을 골랐는지
- 미룬 것과 그 이유

**이 문서의 수치를 그대로 믿지 말고 시작 전에 재확인하라.** 틀린 것을 찾으면 보고에 적어라.
