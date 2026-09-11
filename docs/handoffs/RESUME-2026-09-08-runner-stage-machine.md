# RESUME — 러너 단계 기계 리팩터링 (3단계 중 1단계 완료)

> 작성 2026-09-08 · 브랜치 `refactor/runner-common-axis` · 최신 커밋 `2881370`
> 저장소 `$REPO_ROOT` (= `report-builder`)
> **이 문서가 이 작업의 단일 진입점이다.** 여기부터 읽는다.

## TL;DR + 바로 다음 한 걸음

`runner/` 의 실행기 셋(`run_mode1.py` · `run_mode1_5.py` · `run_mode2.py`)을 **공통 단계 기계**로
바꾸는 3단계 작업이다. **1단계(공통 재는 코드 추출)와 2단계(`pipeline.py` 신설 · Mode 2·1.5
이주)가 끝났고 게이트 여섯이 초록이다.**

**바로 다음 할 일 — 둘 중 하나를 사용자가 고른다:**

1. **3단계 계획서를 쓴다** — Mode 1 을 `mode1/` 패키지로 분해하고, 증분·전량 그래프를
   나누고(D13), `lang-select` 와 `wiki` 를 쪼개고(D4·D16), 재개 JSON 을 넣는다(D12).
   `superpowers:writing-plans` 스킬을 쓴다. 계획서 자리는
   `docs/superpowers/plans/2026-09-08-runner-mode1.md`.
2. **브랜치를 `main` 에 병합하고 멈춘다** — 1·2단계만으로도 독립적으로 값어치가 있다
   (import 부작용이 사라졌고, 드라이버 루프가 3벌에서 1벌로 줄었고, `Any` 가 0이 됐고,
   시작 전 그래프 검사가 생겼다).

**⚠ 3단계 착수 전에 사용자 판정을 받을 것 둘 — D14 · D16.**

**⚠ 2단계의 산출물은 아직 커밋되지 않았다.** 사용자가 요청할 때만 커밋한다는 가드레일에
따라 워킹 트리에 쌓여 있다.

## 지금 상태 — 다시 잰 것 (2026-09-08)

### 브랜치와 커밋

`main` 에서 갈라진 `refactor/runner-common-axis` 에 커밋 14건. **워킹 트리는 깨끗하다**
(미추적 `runner/runner_presudo.md` 하나만 있는데 이것은 사용자가 손으로 쓴 pseudo code 메모다).

```
2881370  [fix] : wiki - 위키 밖 링크 오탐과 check 종료 코드 반전 버그 수정   ← 다른 작업
194b780  [refactor] : runner - 시험 이름과 주석의 모형 표기를 LLM Model 로 통일 ← 다른 작업
f957179  [fix] : wiki - 스크립트로 띄우면 얼갈이 import 가 죽던 경로 문제 수정  ← 다른 작업
ccf95ef  [test] : machine - 전수조사 재실행으로 늘어난 심볼 수 반영          ← 다른 작업
5afbbd0  [chore] : xmldoc - 폐지 예정 배너와 모듈 설명 갱신                 ← 다른 작업
3882c67  [docs] : 1단계 완료를 계획서 체크리스트와 스펙 구현란에 반영
2f593cd  [docs] : 1단계 완료 실측 기록
62dbf8a  [docs] : 공통축 신설을 러너 문서에 반영
f4f20fd  [add] : 형 자리의 Any 를 막는 게이트
044af9a  [fix] : mode 2 와 1.5 가 재는 코드만 가져오도록
fef08b8  [refactor] : run_mode1 을 재는 코드의 파사드로
a857559  [add] : 측정 표와 하트비트를 공통축으로
0221270  [add] : 토큰 세기와 실패 판정을 공통축으로
ad994a3  [add] : 러너 공통 재는 코드의 형과 좁히기 도우미
```

아래 다섯(`5afbbd0`~`2881370`)은 **이 리팩터링이 아니라 다른 작업의 산물**이 이 브랜치에서
커밋된 것이다. 되돌리지 마라 — 게이트가 그 위에서 초록이다.

### 게이트 일곱 — 여섯 초록, 하나는 알려진 빨강

| 게이트 | 명령 | 지금 |
|---|---|---|
| 파이썬 시험 | `.venv/bin/python -m pytest -q` | **562 통과 · 19 건너뜀 · 실패 0** ✅ |
| JS 시험 | `npm test` | **8 통과 · 0 실패** ✅ |
| TS 타입 | `npm run typecheck` | **통과** ✅ |
| 파이썬 타입 | `npm run typecheck:py` | **0 errors** ✅ |
| README 표류 | `.venv/bin/python tools/gen_readme.py --check machine runner viz tools` | **4개 일치** ✅ |
| 환경 | `npm run doctor` | **필수 전부 있다** ✅ |
| 주석 주입 | `.venv/bin/python machine/xmldoc.py check` | **알려진 빨강** 🔴 (2단계로 더 밀렸다. 3단계 뒤 한 번) |

**⚠ `xmldoc check` 의 빨강은 고치지 마라. 알려진 것이고 지금 고치면 안 된다.**
사유는 아래 "xmldoc 은 3단계 뒤에 한 번" 절.

### 1단계가 실제로 바꾼 것

| 항목 | 착수 전 | 지금 |
|---|---|---|
| 파이썬 시험 | 486 통과 | 511 통과 |
| `run_mode2` 를 import 하면 | 해석기가 `.venv` 로 바뀌고 networkx 적재 | **해석기 그대로 · networkx 없음** |
| `run_mode1_5` 를 import 하면 | 같음 | **해석기 그대로 · networkx 없음** |
| `run_mode1.py` | 1,391줄 | **1,136줄** |
| 러너의 형 자리 `Any` | 24곳 | `run_mode1_5.py` 20곳만 남음 |

직접 재보는 법:

```bash
cd $REPO_ROOT
/opt/homebrew/bin/python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), 'runner'))
import run_mode2
print('prefix=%s networkx=%s' % (os.path.basename(sys.prefix), 'networkx' in sys.modules))"
# 기대: prefix=3.14 networkx=False   (기대가 아닌 값이면 1단계가 깨진 것이다)
```

## 단계 현황

| 단계 | 무엇 | 계획서 | 상태 |
|---|---|---|---|
| **1** | `measure.py` 추출 · 파사드 · import 부작용 제거 · `Any` 게이트 | `docs/superpowers/plans/2026-09-08-runner-common-axis.md` | **✅ 완료.** Task 7개 체크박스 전부 `[x]`, 커밋 SHA 박아 둠 |
| **2** | `pipeline.py` 신설(Outcome · Stage · Edges · StageDagGraph · 시뮬레이터), Mode 2·1.5 이주 | `docs/superpowers/plans/2026-09-08-runner-pipeline.md` | **✅ 완료.** Task 13개 |
| **3** | Mode 1 을 `mode1/` 패키지로 분해, 증분·전량 그래프 분리 | **미작성** | 다음 |

**계획서를 미리 쓰지 않은 것은 의도다.** 뒷 단계의 코드가 앞 단계에서 나올 실제 API 모양에
달려 있어서, 미리 쓰면 추측이 된다. 2단계 계획은 아래 `measure.py` 의 실제 서명 위에서 쓴다.

## 3단계가 딛고 설 것 — `runner/pipeline.py` 의 공개 API

**이것이 2단계의 산출물이다.** 드리프트 위험이 있으니 착수 시점에 `runner/pipeline.py` 를
직접 확인하라.

```python
OK, FAIL, SKIP, GATE = 1, 2, 4, 8        # 갈래 넷. 늘리지 않는다
KINDS = (OK, FAIL, SKIP, GATE)
HALT = "\x00halt"                        # 전이 목적지 특수값
NEXT = "\x00next"

@dataclass
class Outcome:                            # perform() 의 반환. Stage 는 무상태다
    kind: int; why: str = ""; rows: list[StageRow] = ...

@dataclass
class RunContext:                         # 세 모드가 공유하는 칸만
    root: str; model: str
    timeout: float | None = None; concurrency: int = 8

C = TypeVar("C", bound=RunContext)        # 형 인자는 이것 하나뿐이다

@dataclass(frozen=True)
class Artifact(Generic[C]):               # 단계가 읽고 쓰는 파일 하나
    name: str
    locate: Callable[[C], str]
    check: Callable[[object], list[str]] | None = None   # JSON 전용. None 이면 존재만

read_json(path: str) -> object            # json.load 의 Any 를 막는 유일한 자리

class Stage(ABC, Generic[C]):
    name: str; emits: int                 # emits 는 선언이지 상태가 아니다
    reads(ctx: C)  -> list[Artifact[C]]   # 없으면 죽는 것만. 선택 입력은 넣지 않는다
    writes(ctx: C) -> list[Artifact[C]]   # 돌고 나면 있어야 하는 것 (누가 쓰는지가 아니다)
    perform(ctx: C) -> Outcome            # 추상

missing_reads(stage, ctx) -> list[str]
bad_writes(stage, ctx)    -> list[str]

class Edges:                              # 파이프라인 밖에 하나. "*" 는 기본 규칙
    dest(stage: str, kind: int) -> str | None

@dataclass(frozen=True)
class StageDagGraph(Generic[C]):
    name: str; order: list[str]; stages: dict[str, Stage[C]]
    edges: Edges; given: list[Artifact[C]]
    first -> str | None
    next_of(cur: str, kind: int) -> str | None
    render() -> str                       # --dry-run 이 찍는다

class GraphError(Exception): ...
simulate(graph, ctx)   -> list[str]       # 완결성·매달림·비순환·도달성·산출물 사슬
build_graph(name, order, stages, edges, given, ctx) -> StageDagGraph[C]
existing(artifacts, ctx) -> list[Artifact[C]]      # given 에 넣을 것

class Pipeline(Generic[C]):
    run(graph, ctx: C) -> list[StageRow]  # **재정의 가능하다** (D6). 지금 쓰는 모드는 없다

class MachineStage(Stage[C]):             # 자식 프로세스 하나. 토큰 0 · 행 1
    argv(ctx) -> list[str]                # 추상
    cwd(ctx)  -> str                      # 추상
    perform  : 재정의 금지

JobResult = tuple[str, float, int, AgentResult | None]
run_agent_with(model, repo, root, prompt, timeout=None, label=None)
run_layer(model, repo, root, jobs, concurrency=8, timeout=None) -> list[JobResult]

class LlmStage(Stage[C]):                 # 훅 여섯. 필수는 prompt · repo 둘
    prompt(ctx) -> str                    # 추상
    repo(ctx)   -> str                    # 추상 — claude 가 열 저장소이자 cwd
    model(ctx)  -> str  = ctx.model
    rounds(ctx) -> int  = 1
    jobs(ctx, rnd)             = [(self.name, self.prompt(ctx))]
    harvest(ctx, got, rnd)     = 세션마다 행 하나
    perform  : 재정의 금지
```

**`run_mode1.py` 는 `run_agent_with` 와 `run_layer` 를 `pipeline` 에서 재수출한다.**
시험 넷이 옛 이름을 참조하므로 **파사드를 지우지 마라.** `measure.py` 재수출도 그대로다.

**`measure.py` 에 `as_list` 가 늘었다** — `as_map` 과 같은 모양이고, `isinstance` 하나로는
`list[Unknown]` 이 되는 문제를 막는다.

⚠ **`as_str` 은 `str(v or "")` 와 다르다.** 숫자가 오면 앞엣것은 `""`, 뒤엣것은 `"123"`.
Mode 1.5 는 옛 동작을 지키려고 `_text` 라는 지역 도우미를 쓴다. **3단계에서 Mode 1 의
`Any` 를 없앨 때 같은 함정을 밟지 마라.**

## 2단계가 만든 이주 본보기 둘

3단계의 Mode 1 이주가 그대로 따라 할 모양이다.

| 모드 | 어디 | 무엇을 보나 |
|---|---|---|
| Mode 2 | `run_mode2.py` 의 `Mode2Context` · `Mode2Machine` · `AgentStage` · `build_mode2_graph` | `LlmStage` 를 세션 하나로 쓰는 법 · `harvest` 재정의로 출력 흘리기 · `plan_stages` 를 팩토리의 ①로 남기기 |
| Mode 1.5 | `run_mode1_5.py` 의 `Mode15Context` · `GateStage` · `build_mode1_5_graph` | `GATE` 갈래를 내는 단계 · `ctx` 에 값을 남겨 `main` 이 꺼내 쓰기 · 닫힌 함수를 `Artifact.check` 로 걸기 |

## 확정된 결정 — 다시 논쟁하지 말 것

사양 원본은 `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` (결정 17건).
**아래 12건은 사용자가 직접 정했다.** 재검토 요청 없이 뒤집지 마라.

| # | 결정 | 사용자 근거 |
|---|---|---|
| D0 | 공통축은 `Stage` 상속 + 교체 가능한 착지점 | *"확장에 열려있고 변경에 닫혀있는 구조… Fall-Back 착지점, Cascade 분기 착지점을 교체"* |
| D1 | 전이표는 **파이프라인 밖에 하나**. Stage 는 자기 다음을 모른다 | 사용자 선택 |
| D3 | `llmstage` 훅 다섯, **필수는 `prompt` 하나** (`model`·`rounds`·`jobs`·`harvest` 는 기본값) | 재검토 요구 → 실측 재조사로 번복 |
| D4 | `lang-select` 를 `lang-propose` + `lang-decide` 로 쪼갠다 | 사용자 선택 (안 A) |
| D7 | 모듈 경계 = 공통 2파일 + `mode1/` 패키지 | 사용자 선택 (안 A) |
| D9 | 흐름 전체를 `StageDagGraph` 로 **미리 짓는다.** 팩토리가 진입점에서 보장 | *"Fallback 시뮬레이터가 보장된 StageDagGraph 팩토리"* |
| D10 | 입출력을 `machine/` 의 **기존 TypedDict** 로 못 박고 경계에서 검증 | *"Stage 경계마다 인풋·리턴 JSON 스키마가 엄격하게 달라야"* |
| D11 | `Any` 를 **완전히 없애고** `object` + 좁히기. 게이트로 강제 | *"Any 를 일절 쓰지 않도록… 파이썬 컴파일러를 통해서도 잡을 수 있도록"* |
| D12 | 그래프는 **비순환**, 재시도는 **재개 JSON** 으로. 모든 중단이 그것을 남긴다 | *"어디서 실패했는지를 Fall-Back 하면서 JSON 값을 리턴… 이전 실패했던 지점에서만 다시 시작"* |
| D13 | Mode 1 을 **증분 그래프와 전량 그래프 둘**로. 팩토리가 고른다 | *"증분용 stage, 완전 처음부터 시작하는 파이프라인 두가지로 명시적으로 분리"* |
| D14 (×2) | **`warmup` 이 `warmup-diff.json` 을 쓴다.** `survey` 가 로딩 시 계획과 양방향 대조. `삭제됨` 은 기계가 지운다 | *"Diff 작업을 기계적으로 만드는 파이프라인을 한 번 두기만 하면 된다"* (2026-09-11) |
| D17 | 실행 둘이 겹칠 때 **claim 파일**. push 그대로. **결함 ③ 뒤** | *"push 그대로. 실행 둘이 겹치는 것만 막으면 된다"* (2026-09-11) |
| D15 | `prep` 의 건너뜀 판정을 파일 존재 → `targets` 로 | *"동의"* |
| D2 | `Stage` 는 무상태. 갈래는 `Outcome` 반환값 | 사용자 선택 (2026-09-09) |
| D5 | 단계 사이의 값은 형이 붙은 `Context` dataclass | 사용자 선택 (2026-09-09) |
| D6 | **`pipeline.run` 은 재정의 가능하다** — 앞선 판(비가상)의 번복 | 사용자 선택 (2026-09-09). 다만 2단계에서 재정의하는 모드는 없다 |
| R1 | 선택 입력은 `reads` 에 선언하지 않는다 | 사용자 선택 (2026-09-09) |
| R2 | `Artifact.check` 는 JSON 전용 | 사용자 선택 (2026-09-09) |
| D14 | **경고만.** 계획 파일에 범위를 싣지 않는다 | 사용자 선택 (2026-09-10). `machine/` 소유 경계를 열지 않는다 |
| D16 | `wiki` 를 `wiki-catalogue` + `wiki-pages` 로 쪼갠다 | 사용자 선택 (2026-09-10) |
| 순서 | **리팩터링이 먼저, warmup 결함 ③④는 후속** | *"일단 리팩토링 먼저… 리펙토링 끝난 후 후속 작업"* |

**미결정 0건.** 사양의 결정 17건이 전부 판정됐다. 3단계는 판정을 다시 받을 필요 없이 착수한다.

⚠ **D14 는 절반만 막는다.** 경고로 안 막히는 것 셋이 사양의 `[개선 대상]` **M1-1** 에 적혀 있다 —
⑴ `--only` 로 쪼개면 여전히 전량 계획이 쓰인다 ⑵ `--dry-run` 이 좁히기를 못 보인다
⑶ **시뮬레이터가 D13 의 두 그래프를 대조할 수 없다.** ⑶ 은 D13 과 직접 얽히지만
순서 제약(증분 그래프는 ③④ 뒤)이 눌러 둔다. **증분 그래프를 실제로 쓰기 시작할 때
소유 경계를 여는 판정을 다시 받아라.**

### 정정된 주장 하나

**1단계 계획서는 `xmldoc` 문제가 +9 늘 것이라 적었는데 실제로는 +38 이었다**(117 → 155).
`run_mode1.py` 만 떼어 재 보니 마커 없음 4→13(+9, 예측대로)이고 **줄 밀림 0→29** 였다.
**정의를 지우면 그 아래 마커의 줄 번호가 전부 밀린다** — 지운 마커 수만 세면 안 된다.
2·3단계에서 같은 실수를 반복하지 마라.

## xmldoc 은 3단계 뒤에 한 번 — 지금 고치지 마라

`machine/xmldoc.py` 는 소스에 `# <include …/>` 주석 블록을 주입하고, `check` 는
`machine/terms-reading.json` 의 `where` 줄 번호와 파일의 마커 위치가 **같은지** 본다.
리팩터링이 코드를 옮길 때마다 그 줄 번호가 밀린다.

- **지금 돌리면 3단계에서 또 밀린다.** 가장 싼 시점은 **3단계 직후 한 번**이다.
- 고치는 명령은 `.venv/bin/python machine/xmldoc.py emit` → `inject` 다. **지금 돌리지 마라.**
- `machine/comments.xml` 은 `emit_xml()` 의 산출물이고 지금 `terms-reading.json` 과
  **약 5,700줄 어긋나 있다.** 손으로 고치지 마라.
- 이 체계 자체가 **폐지 예정**이다 — `docs/decisions/0007-xmldoc-include-deprecated.md`.
  **새 코드에 `# <include …/>` 를 새로 심지 마라.** 대체 마크업은 미정이다(사용자 결정 대기).

## 병렬 작업 충돌 매트릭스

| 파일 / 영역 | 누가 소유 | 비고 |
|---|---|---|
| `runner/measure.py` · `runner/test_measure.py` | **이 작업** | 1단계 산출물. 2단계가 딛고 선다 |
| `runner/run_mode1.py` · `run_mode1_5.py` · `run_mode2.py` | **이 작업** | 2·3단계에서 크게 바뀐다 |
| `runner/test_import_isolation.py` · `test/test_no_any.py` | **이 작업** | 게이트. 약화시키지 마라 |
| `runner/wiki/**` | 다른 작업 | 1단계 범위 밖. **3단계에서 `prep.py` 만** D15 때문에 열린다 |
| `runner/term/**` | 다른 작업 | 얼갈이. 이 리팩터링이 손대지 않는다 |
| `machine/**` | 다른 작업 | 부르기만 하고 고치지 않는다 (`runner/CLAUDE.md` 의 Owns 절) |
| `machine/terms-reading.json` | 다른 작업 | 재조사 산출물($50.73). 손대지 마라 |

### 살아 있는 다른 인계 문서 둘

| 문서 | 상태 |
|---|---|
| `docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md` | 🔴 **리팩터링 후속.** 배너가 붙어 있다. 결함 ①②는 D13·D14 가 흡수했고 **③④만 남았다.** 3단계가 끝난 뒤 착수 — 고칠 자리(`run_layer` · `merge_shards`)가 리팩터링으로 옮겨간다 |
| `docs/handoffs/HANDOFF-2026-09-08-xmldoc-deprecation-marker.md` | ✅ **완료됨** (커밋 `5afbbd0`). 다시 실행하지 마라 |
| `docs/handoffs/HANDOFF-2026-09-07-codegraph-id-namespace.md` | 안 읽음. warmup 문서의 짝. 결함 ④의 갈래 H 와 한 묶음이라고 지목돼 있다 |

## 가드레일 · 규약

- **커밋은 사용자가 요청할 때만.** 형식은 `personal-commit-messages` — 소문자
  `[tag] : subject` 한 줄, **한국어**, 본문 없음. 세션 지침이 요구하면 그 뒤에
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` 트레일러 한 줄.
- **`git add -A` 금지.** 이 저장소는 여러 작업이 같은 워킹 트리를 쓴다. 경로를 좁혀 add 한다.
- **TDD.** 시험을 먼저 쓰고 실패를 확인한 뒤 구현한다. 1단계가 그렇게 돌았다.
- **주석과 문서는 한국어.** 약어를 피하고 메커니즘을 먼저 쓴다.
- **코드 주석에는 "지금 이 코드가 무엇인가" 만 쓴다** — 날짜 · 측정 수치 · 확신도 표기 ·
  설계 철학 서사를 코드에 남기지 않는다. 그런 것은 `docs/` 의 몫이다.
- **구조 신설 제안 시** `design-decision-discipline` §2.5 의 4항목을 공개하고 §2.7 의 축을 선언한다.
- **남의 제안을 기각하기 전에** `docs/overturn/README.md` 의 판단 직전 검사표를 지난다.
  이 작업에서 뒤집힌 판단 3건이 **전부 기각 쪽**이었다.
- **거울 함정.** 과잉 설계를 잡는 도구를 과잉 설계하지 마라. 사양의 "범위 밖" 절이
  경계선을 미리 그어 두었다 — 갈래는 넷 고정, 계층 상태·가드 함수·이벤트 큐·플러그인
  등록기·스키마 언어를 만들지 않는다. 형 인자는 `Stage[C]` 의 `C` 하나뿐이다.

## 포인터

| 무엇 | 어디 |
|---|---|
| **사양 원본** (결정 17건 · 설계 · 범위 밖 · 위험) | `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` |
| 그 사양의 Mode 2 보고서 (계기판) | `docs/superpowers/specs/runner-stage-machine/out/report.html` — git 제외. `report-spec build` 로 재생성 |
| **1단계 계획서** (체크박스 전부 완료 · Task 별 커밋 SHA) | `docs/superpowers/plans/2026-09-08-runner-common-axis.md` |
| 사용자가 쓴 원본 pseudo code | `runner/runner_presudo.md` — **미추적.** 이 저장소가 추적하지 않는다 |
| 번복 기록과 판단 검사표 | `docs/overturn/README.md` |
| 러너축 모듈 문서 (Gotcha 갱신됨) | `runner/CLAUDE.md` |

## 변경 이력

- 2026-09-11 — D14 를 두 번째로 뒤집었다(경고만 → `warmup-diff.json`). D17(claim 파일) 신설.
  둘 다 3단계 계획서에 들어가야 한다. 번복 기록 0004 추가.

- **2026-09-08** — 최초 작성. 1단계(공통축 추출) 완료 시점에서 씀. 커밋 14건 중 이 작업의
  것은 9건이고 나머지 5건은 다른 작업이 같은 브랜치에 넣은 것이다. 게이트 여섯 초록,
  `xmldoc` 하나는 의도된 빨강.
