# HandOff — C++ 경계 규칙 선언과 진입점 식별 (Track C §1 17·18)

> 작성일: 2026-08-27
> 인계 대상: **C++ 저장소 안에서 실행되는 Claude Code Agent + 저장소 주인(사용자)**
> 대상 저장소: `$GRAPHICS_REPO`
> 상위 문서: `$REPO_ROOT/docs/handoffs/HANDOFF-codebase-wiki.md` (Track C)
> 짝 문서: `HANDOFF-unity-boundary-rules.md` (C# / Unity 쪽 같은 작업)
> 선행 산출물: `<저장소>/out/codegraph-raw/codegraph.json` (`normalize.py` 가 이미 만들어 뒀다)

---

## 0. 목적 — 이것부터 읽어라

> **에이전트가 아키텍처 위반을 판정하는 작업이 아니다.
> 사람이 "무엇이 허용인가" 를 선언하게 하고, 그 선언을 기계가 검사할 수 있는 파일로 남기는 것이다.**

Track C §1 이 이 항목을 **"규칙만 사람이 정하면 정적"** 으로 분류하고 이렇게 적었다.

> **18번이 값이 크다.** 지금은 "허용된 누수" 를 사람이 눈으로 표시하는데, `allow: render -> gl`
> 같은 규칙을 선언해두면 **위반 간선이 자동으로 빨강**이 되고, 새 위반이 생기면 검사에서 잡힌다.
> Graphviz P6 의 자동화다.

**즉 이 작업의 산출물은 분석이 아니라 선언 파일 하나다.**

### 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| 에이전트가 "이건 위반이다" 라고 **결론짓는 것** | 무엇이 허용된 누수인지는 **저장소 주인만 안다.** 도구는 계산·병치까지다 |
| 근거(`why`) 없이 `allow` 를 추가하는 것 | 근거 없는 예외는 규칙을 무의미하게 만든다. `why` 는 **필수 필드**다 |
| 순환을 없애려고 **코드를 고치는 것** | 이 작업은 선언이지 리팩터링이 아니다. 고칠지는 별개 판단이다 |
| `codegraph.json` 을 손으로 고치는 것 | 생성물이다. `normalize.py` 로 재생성한다 |

---

## 1. 재료 — 이미 측정돼 있다 🔵 (2026-08-27)

`normalize.py` 산출물 기준이다. **모듈 경계는 폴더 트리이고(C-15), 의존은 클래스 간선에서 유도한 것이다.**
⚠ **링크 의존(`target_link_libraries`)이 아니라 타입 의존이다.** 같은 것으로 읽지 말 것.

```
모듈 20개 / 모듈 간 의존 49개
```

### 1-1. 순환이 11개 있다 — 그중 2개가 상호 의존이다

```
material <-> render
material <-> resource_registry

render -> material -> render
resource_registry -> material -> resource_registry
sprite -> material -> resource_registry -> sprite
render -> object -> material -> render
resource_registry -> object -> material -> resource_registry
sprite -> object -> material -> resource_registry -> sprite
sprite -> render -> material -> resource_registry -> sprite
render -> scene -> object -> material -> render
sprite -> render -> object -> material -> resource_registry -> sprite
sprite -> playable -> scene -> object -> material -> resource_registry -> sprite
sprite -> render -> scene -> object -> material -> resource_registry -> sprite
```

🔵 ⭐️ **11개 순환 전부에 `material` 이 들어 있다.** 이것이 이 저장소에서 가장 큰 객관 신호다.
💭 **다만 "그래서 `material` 이 잘못됐다" 는 결론은 내지 않는다** — 순환이 의도된 것인지
(예: 재질이 렌더 상태를 알아야 하는 도메인 사정) 누수인지는 사용자 판정이다.

### 1-2. 순환을 뺀 위상 층 (근사 — 초안 재료일 뿐이다)

```
L0  apps/_MyApp_ · diagnostics · reflect
L1  fsm · input · material · object · playable · render · text · timer
L2  layout · resource_registry · scene · sprite
L3  buffer · program
L4  shader · texture
L5  common
```

⚠ **이 층은 기계가 뽑은 것이라 의미축이 아니다.** `diagnostics` 와 `reflect` 가 `apps` 와 같은
L0 에 온 것은 "아무도 안 쓴다" 는 뜻이지 "최상위 계층" 이라는 뜻이 아니다.
**§3 에서 사람이 다시 그린다.**

### 1-3. 잎 모듈 6개 (의존 0)

```
common · diagnostics · input · layout · reflect · shader
```

---

## 2. 산출물 — `codegraph-rules.toml`

**대상 저장소 루트에 둔다.** 경계 규칙은 도구가 아니라 **그 저장소에 관한 사실**이고,
아키텍처가 바뀌면 코드와 함께 바뀌어야 하므로 코드 옆에서 버전 관리되는 것이 맞다.
(C-12 는 *도구*를 사용자 프로젝트에 심지 말라는 규칙이고, 선언 파일은 도구가 아니다.
⚠ 그래도 이 판단은 §6 에 미결정으로 남긴다.)

**형식은 TOML 이다.** 이유 둘 — ① Python 3.11+ 의 `tomllib` 가 **표준 라이브러리**라 의존이 늘지 않는다.
② **주석을 쓸 수 있다.** 이 파일에서 가장 중요한 정보가 "왜 이 누수를 허용하는가" 이므로
주석이 안 되는 JSON 은 맞지 않는다.

```toml
[meta]
project      = "GlobalMedia-OpenGL-ComputerGraphics"
declared_at  = "2026-08-27"
declared_by  = "저장소 주인"
based_on     = "out/codegraph-raw/codegraph.json (commit bfb72b4, 모듈 20 / 의존 49)"

# ── 층. 위에 적힌 것이 아래를 쓴다. 아래에서 위로 가는 간선은 위반이다.
#    같은 층끼리는 기본 금지이고 필요하면 [[allow]] 로 연다.
[[layer]]
name    = "앱"
modules = ["apps/_MyApp_"]

[[layer]]
name    = "..."
modules = ["..."]

# ── 층 규칙의 예외. why 는 필수다.
[[allow]]
from = "material"
to   = "render"
why  = "여기에 근거를 적는다. 비워 두면 검사가 거부한다."

# ── 진입점 (Track C §1 17)
[[entrypoint]]
symbol = "main"
file   = "apps/_MyApp_/main.cpp"
why    = "실행 진입점"
```

**검사기는 이 파일과 `codegraph.json` 을 대조해 세 가지를 낸다** — 위반 간선 / 선언에 없는 새 간선 /
`why` 가 빈 `allow`. **판정은 하되 고치지 않는다.**

---

## 3. 절차

### 단계 1 — 순환 11개를 사람이 판정한다 (가장 중요)

§1-1 의 목록을 놓고 **각 상호 의존 쌍에 대해** 셋 중 하나를 고른다.

| 판정 | 뜻 | 파일에 쓰는 것 |
|---|---|---|
| **허용** | 도메인상 불가피하다 | `[[allow]]` + `why` |
| **위반** | 고쳐야 하지만 지금은 아니다 | `[[allow]]` 없이 두고 검사에서 빨강으로 뜨게 둔다 |
| **오탐** | 타입 의존일 뿐 실제 결합이 아니다 | `[[allow]]` + `why` 에 "오탐" 명시 |

⚠ **"위반" 을 고르면 검사가 계속 빨강을 낸다. 그것이 의도다** — 숨기지 말고 남겨 둔다.

**정지 조건:** `material <-> render` 와 `material <-> resource_registry` 두 쌍에 판정이 붙었으면 통과.

### 단계 2 — 층을 선언한다

§1-2 의 위상 층은 **재료일 뿐이다.** 사람이 의미로 다시 그린다.
`diagnostics`·`reflect` 처럼 "아무도 안 써서 L0 에 온 것" 을 그대로 두면 안 된다.

**정지 조건:** 20개 모듈이 전부 어느 층엔가 들어갔으면 통과. **빠진 모듈이 있으면 완료가 아니다.**

### 단계 3 — 층 규칙으로 설명 안 되는 간선을 `[[allow]]` 로 뺀다

층을 선언하면 49개 간선 중 위로 가는 것들이 남는다. 하나씩 `why` 를 붙인다.

⚠ **`why` 를 "필요해서" 로 채우지 말 것.** 6개월 뒤 그 문장이 판단 근거가 된다.

### 단계 4 — 진입점을 적는다

`main`/`WinMain` 은 패턴으로 찾는다. **예외가 이 저장소에 있는지 확인한다** —
🔵 §5 가 예고한 `src/reflect/` 의 자기등록(self-registration) 패턴이 있으면
**정적 초기화가 사실상 진입점**이므로 적어 둔다.

```bash
grep -rn "int main\|WinMain" apps/ src/ --include=*.cpp | head
```

### 단계 5 — 위생 정리 (작다)

🔵 `.clang-uml` 에 `probe` 라는 sequence 다이어그램이 있고 내용이 이 저장소와 무관하다
(`myproject` 2곳). `clang-uml --init` 이 찍은 도구 기본 예제다. **지우거나 실제 값으로 채운다.**

---

## 4. 별도 갈래 — 이 문서 범위 밖

**헤더 자기충족 타겟이 없다** 🔵 (2026-08-27 확인).
`cpp-index-friendly-conventions.md` §1 이 **최우선**으로 지목한 항목이고, 헤더마다 한 줄짜리
`.cpp` 를 만들어 한 타겟으로 묶는 CMake 작업이다. **저장소의 빌드를 고치는 일**이라 성격이 다르다.
**이 문서에서 하지 말 것.**

**Windows 산출물(Track C Phase 6)** 도 범위 밖이다 — Windows 머신이 필요하고
`toolchain/mingw-w64.cmake` 가 없어 크로스 폴백도 없다.

---

## 5. 미결정 — 혼자 정하지 않는다

- **`codegraph-rules.toml` 의 위치.** 대상 저장소 루트로 제안했으나, C-12("파이프라인 코드는
  report-builder")를 넓게 읽으면 `report-builder/codegraph/rules/<프로젝트>.toml` 이 될 수도 있다.
  💭 60 — 저장소 옆이 낫다고 보지만 확정은 사용자 몫이다.
- **순환을 실제로 고칠 것인가.** 이 문서는 선언까지만 한다.
- **`why` 없는 `allow` 를 검사 실패로 볼 것인가 경고로 볼 것인가.**

---

## 6. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만 인정한다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.**
- 커밋이 필요하면 `personal-commit-messages` 스킬을 따른다.
- **사용자 코드를 고치지 않는다.** 이 작업이 저장소에 남기는 것은 `codegraph-rules.toml` 하나와
  `.clang-uml` 위생 정리뿐이다.
- **거울 함정을 경계하라.** 규칙 파일은 층 목록·예외 목록·진입점 목록 셋이다.
  규칙 언어를 설계하거나 플러그인 구조가 나오면 그 자체가 Track C 가 잡으려는 실패다.
