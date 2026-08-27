# HandOff — C# / Unity 경계 규칙 선언과 진입점 식별 (Track C §1 17·18)

> 작성일: 2026-08-27
> 인계 대상: **Unity 저장소 안에서 실행되는 Claude Code Agent + 저장소 주인(사용자)**
> 대상 저장소: `$CSHARP_REPO` (Unity 6000.0.71f1, HEAD `bf54917`)
> 상위 문서: `$REPO_ROOT/docs/handoffs/HANDOFF-codebase-wiki.md` (Track C)
> 짝 문서: `HANDOFF-cpp-boundary-rules.md` (C++ 쪽 같은 작업)
> 근거 실측: `samples/csharp-unity/OBSERVATION.md`

---

## 0. 목적 — 이것부터 읽어라

> **에이전트가 아키텍처 위반을 판정하는 작업이 아니다.
> 사람이 "무엇이 허용인가" 를 선언하게 하고, 그 선언을 기계가 검사할 수 있는 파일로 남기는 것이다.**

C++ 쪽 짝 문서와 목적·산출물 형식이 같다. **다른 것은 두 가지다.**

### ⚠ 차이 1 — 이 저장소는 아직 `codegraph.json` 이 없다

C++ 쪽은 `normalize.py` 가 이미 돌아 모듈 20개 / 의존 49개 / 순환 11개가 **측정돼 있다.**
C# 쪽은 **`roslyn-dump` 도구가 아직 존재하지 않는다**(Track C Phase 7 미착수).
형식만 확정됐다 — `DECISION-csharp-intermediate-format.md`.

**따라서 이 작업은 둘로 갈린다.**

| | 지금 할 수 있다 | `roslyn-dump` 이후 |
|---|---|---|
| 층 선언 (§3 단계 1) | ✅ 폴더 트리는 실측됨 | |
| 진입점 식별 (§3 단계 2) | ✅ | |
| 위생 정리 (§3 단계 3) | ✅ | |
| **순환 판정 · 위반 검사** | ~~❌ 미측정~~ → 🔵 **가능해졌다** (§1-2 — 순환 5개 측정됨) | ✅ |

**지금 단계 1~3 을 해 두면 도구가 나온 날 바로 검사가 돌아간다.** 순서를 뒤집지 말 것 —
층을 먼저 선언해야 "무엇이 위반인가" 를 물을 수 있다.

### ⚠ 차이 2 — Unity 의 진입점은 코드에 호출자가 없다

`MonoBehaviour` 의 `Awake`/`Start`/`Update` 는 **엔진이 리플렉션으로 부른다.**
🔵 관찰 보고서 G절 — 호출 그래프에서 **입력 간선 0 인 고아**로 보이고 PageRank 중요도가 0 에 수렴한다.
**C++ 의 `main` 하나와 달리 진입점이 수십 개다.** §3 단계 2 가 이것을 다룬다.

### 절대 하지 말 것

| 금지 | 이유 |
|---|---|
| 에이전트가 "이건 위반이다" 라고 **결론짓는 것** | 무엇이 허용된 누수인지는 **저장소 주인만 안다** |
| 근거(`why`) 없이 `allow` 를 추가하는 것 | `why` 는 **필수 필드**다 |
| `.asmdef` 를 새로 만드는 것 | Unity 가 어셈블리를 다시 나누고 컴파일 순서가 바뀌어 프로젝트가 깨질 수 있다 |
| Unity 에디터로 씬·프리팹을 저장하는 것 | 재직렬화로 사용자 작업물에 diff 가 생긴다 |
| 모듈 경계를 `.asmdef` 로 잡는 것 | 🔵 **사용자 코드 114개 중 112개(98.2%)가 `Assembly-CSharp` 하나**에 들어간다. 폴더 트리로 확정됐다 |

---

## 1. 재료 — 실측된 것과 안 된 것

### 1-1. 모듈 경계 = 폴더 트리 🔵 (2026-08-27 사용자 확정)

`Assets/@Scripts/<폴더>` 와 `Assets/@Editors` 다.

```
Controller   31        UIs          24        Data          20
Utils        10        Interface     8        Managers       7
Test          2        Fixture       2        Exceptions     2
                                              ---------------------
                                              @Scripts 소계 106

@Editors      8   (SceneHelper 4 + 단일 파일 4)
                                              ---------------------
                                              사용자 코드 계 114
```

⚠ 🔵 **`@Editors/SceneHelper/ToolbarExtender/` 2파일은 서드파티다**(벤더링된 도구, 자체 `.asmdef` 보유).
모듈로 셀 때 빼야 한다. **경로가 `Assets/@` 로 시작해도 사용자 코드가 아닐 수 있다.**

### 1-2. 모듈 간 의존 — ~~미측정~~ → 🔵 **측정됨 (2026-08-27, roslyn-dump 완성)**

`roslyn-dump` → `normalize_csharp()` 가 완주해 이 절의 전제가 바뀌었다.
`out/codegraph-raw/codegraph.json` 기준 — 모듈 10 / 모듈 간 의존 20 / **순환 5개**:

```
Managers <-> Utils                    (상호 의존)
UIs <-> Controller                    (상호 의존)
Managers -> UIs -> Controller
Managers -> UIs -> Utils
Managers -> UIs -> Controller -> Utils
```

| 모듈 | 의존 대상 |
|---|---|
| Controller | Data, Interface, Managers, UIs, Utils |
| Managers | Data, Exceptions, Interface, UIs, Utils |
| UIs | Controller, Data, Interface, Utils |
| Test | Data, Managers, Utils |
| Utils | Interface, Managers |
| Fixture | Data |
| @Editors · Data · Exceptions · Interface | (의존 없음 — 잎) |

**따라서 §3 단계 4(순환 판정)를 이제 할 수 있다.** C++ 쪽과 같은 판정 절차를 따른다 —
상호 의존 쌍 `Managers <-> Utils` 와 `UIs <-> Controller` 에 허용/위반/오탐 판정을 붙인다.

#### (원문 — 측정 전 기록)

`roslyn-dump` 가 없어서다. 🔵 관찰 보고서 기준으로 **타입 간** 간선은 419개
(`inherit` 64 · `realize` 70 · `assoc` 285)가 측정됐으나, **그것을 모듈로 집계한 적이 없다.**

💭 **추측으로 채우지 말 것.** `Controller → Data` 같은 것이 있을 법하다고 적는 순간
그것이 나중에 실측인 것처럼 읽힌다. §3 단계 1 은 **의존이 아니라 층만** 선언한다.

### 1-3. 외부 노드는 이미 접혀 있다 🔵

C-9 적용 결과 **12개**다(`external-nodes.tsv`). 참조 DLL 395 → 접촉 어셈블리 13 → 패키지 12.

```
(BCL) netstandard 310 · (엔진) UnityEngine.CoreModule 34 · com.unity.ugui 12
com.cathei.bakingsheet 12 · (엔진 에디터) UnityEditor 4 · com.unity.modules.ui 3
(벤더링) DOTween 2 · com.unity.inputsystem / addressables / modules.audio /
modules.animation / modules.imgui 각 1
```

**경계 규칙에서 외부는 다루지 않는다** — R3 으로 외딴 섬이고 R4 로 단방향이라 위반이 성립하지 않는다.

---

## 2. 산출물 — `codegraph-rules.toml`

**형식과 위치는 C++ 쪽과 동일하다.** 대상 저장소 루트, TOML(Python `tomllib` 가 표준 라이브러리이고
주석을 쓸 수 있다). 상세는 `HANDOFF-cpp-boundary-rules.md` §2 를 볼 것. 여기서는 차이만 적는다.

```toml
[meta]
project      = "StickRushGame"
declared_at  = "2026-08-27"
based_on     = "Assets/@Scripts 폴더 트리 (commit bf54917). 모듈 간 의존은 미측정"

[[layer]]
name    = "씬 진입"
modules = ["Controller"]

# ...

# ── Unity 진입점. C++ 과 달리 여러 개이고, 코드에 호출자가 없다.
[[entrypoint]]
kind   = "unity_lifecycle"        # 엔진이 리플렉션으로 부른다
symbol = "HomeScene.Start"
file   = "Assets/@Scripts/Controller/HomeScene/HomeScene.cs"
why    = "홈 씬 진입"

[[entrypoint]]
kind   = "unity_asset"            # 프리팹·씬 YAML 이 GUID 로 물고 있다
symbol = "UI_OpenSettingButton"
file   = "Assets/@Scripts/UIs/Buttons/UI_OpenSettingButton.cs"
why    = "UI_SettingButton.prefab 이 m_Script 로 참조"
```

🔵 **`kind` 필드가 C++ 쪽에는 없다.** Unity 는 진입 경로가 두 종류이고(엔진 생명주기 / 자산 배선)
둘 다 **코드에 호출자가 없어** 정적 분석이 고아로 본다. 구분해 두지 않으면 나중에
"왜 이게 진입점인가" 를 다시 조사하게 된다.

---

## 3. 절차

### 단계 1 — 층을 선언한다 (지금 가능)

§1-1 의 폴더 10개(`@Editors` 포함)를 층으로 배열한다. **의존을 적는 것이 아니라 순서를 적는 것이다.**

💭 참고로 이름만 보면 `Controller`(씬) → `UIs`/`Managers` → `Data`/`Interface` → `Utils` 같은
모양이 예상되지만, **이것은 이름에서 온 추측이지 측정이 아니다.** 사용자가 실제 구조로 다시 그린다.

⚠ **`Test`·`Fixture`·`Exceptions` 를 빠뜨리지 말 것.** 각 2개뿐이라 눈에 안 띈다.
**10개 폴더가 전부 어느 층엔가 들어가야 완료다.**

**정지 조건:** 폴더 10개가 전부 배치됐으면 통과.

### 단계 2 — 진입점을 적는다 (지금 가능, 이 저장소의 핵심 난점)

**세 경로를 각각 훑는다.**

**(가) 씬 컨트롤러.** 🔵 `Controller/` 아래에 `*Scene.cs` 가 실재한다 —
`HomeScene` · `SplashScene` · `InGameScene` · `ResourceClearenceScene`.

```bash
git ls-files 'Assets/@Scripts/*.cs' | xargs grep -ln "class .*Scene" 
```

**(나) `MonoBehaviour` 생명주기.** ⚠ **정규식으로 세지 말 것.**
🔵 실측 — 정규식 5 vs Roslyn **45**(중간 기반 클래스 `UI_Base` 26개 등을 못 따라간다).
**정확한 수가 필요하면 `roslyn-dump` 이후로 미룬다.** 지금은 **씬 컨트롤러만** 적고
나머지는 "미완" 으로 남긴다.

**(다) 자산 배선.** 🔵 프리팹·씬 YAML 이 `m_Script: {guid: ...}` 로 스크립트를 직접 물고 있다.
사용자 자산 쪽만 **프리팹 16개 + 씬 6개**다. 이것들이 실질 진입점이다.

```bash
# GUID -> .cs 역인덱스를 만들어 대조한다 (.meta 파일에 guid 가 있다)
git ls-files 'Assets/@Scripts/*.cs.meta' | head -3 | xargs grep -h guid
```

⚠ **`UnityEvent` 의 `m_PersistentCalls` 는 이 단계에서 다루지 않는다.**
🔵 저장소 전체 472건이고 사용자 자산 쪽 22건인데, `m_Target` 의 `fileID` 를 같은 파일 안에서
역참조해야 대상이 확정된다. **±8줄 휴리스틱으로는 부족하다는 것이 이미 실측됐다.** 별도 과제다.

**정지 조건:** 씬 컨트롤러 전부와 자산 배선 프리팹 16개·씬 6개가 `[[entrypoint]]` 로 적혔으면 통과.
`MonoBehaviour` 생명주기는 **"미완" 으로 명시하고 넘어간다.**

### 단계 3 — 위생 정리 (지금 가능)

🔵 **낡은 사본이 있다.** `$DEV_ROOT/StickRushGame` 은 Unity **2022.3.30f1**, HEAD `e681003`,
**미커밋 1,001건**이다. 정본은 `$CSHARP_REPO`
(Unity 6000.0.71f1, HEAD `bf54917`, 미커밋 0).

⚠ **에이전트가 지우지 말 것.** 미커밋 변경 1,001건이 무엇인지 확인되지 않았다.
**사용자에게 보고만 한다.**

### 단계 4 — 순환 판정과 위반 검사 (`roslyn-dump` 이후)

도구가 나오면 `normalize.py` 가 `modules[].depends_on` 을 클래스 간선에서 유도한다(C-15).
그때 C++ 쪽 §3 단계 1 과 같은 판정을 한다. **지금은 하지 않는다.**

---

## 4. 미결정 — 혼자 정하지 않는다

- **`codegraph-rules.toml` 의 위치** — C++ 쪽 §5 와 같은 항목이다. 두 저장소가 같은 선택을 해야 한다.
- **`Test`·`Fixture` 를 모듈로 볼 것인가** — 각 2파일이다. 프로덕션 코드와 같은 층에 두면
  의존 그래프가 지저분해지고, 빼면 그래프가 실제와 달라진다.
- **`@Editors` 를 하나의 모듈로 볼 것인가 쪼갤 것인가** — 8파일 중 4가 `SceneHelper` 이고
  그중 2는 서드파티다.
- **`UnityEvent` 배선을 진입점으로 볼 것인가** — 472건 중 사용자 쪽 22건. 별도 과제로 미뤘다.

---

## 5. 작업 규약

- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만 인정한다.**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- **정규식 계수를 "정확한 수" 로 쓰지 말 것.** 🔵 이 저장소에서 양방향 오차가 실측됐다 —
  `MonoBehaviour` 정규식 5 / Roslyn 45, `StartCoroutine` 정규식 5 / Roslyn 1(주석 4건을 셌다).
  **하한도 상한도 아니다.**
- 설명은 메커니즘 우선, 한국어 + 영문 기술용어 병기. **약어와 압축 표현을 피할 것.**
- 커밋이 필요하면 `personal-commit-messages` 스킬을 따른다.
- **사용자 프로젝트를 바꾸지 않는다.** 이 작업이 남기는 것은 `codegraph-rules.toml` 하나뿐이다.
- **거울 함정을 경계하라.** 규칙 파일은 층·예외·진입점 목록 셋이다. 규칙 언어를 설계하지 말 것.
