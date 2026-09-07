# 러너 세 실행기의 공통 단계 기계 (Stage Machine) — 설계 검토

`runner/` 의 세 실행기(`run_mode1.py` · `run_mode1_5.py` · `run_mode2.py`)가 각자 갖고 있는
**단계 루프 · 단계 고르기 · 재는 코드**를 하나로 모으고, 단계를 `Stage` 클래스로 올려
파이프라인 밖 전이표(transition table)로 잇는다. `run_mode1.py`(1,391줄)는 그 과정에서
모듈로 쪼개진다.

동기는 사용자 문장 그대로다 — **"한 코드의 길이가 너무 길다"**, 그리고
**"확장에 열려있고 변경에 닫혀있는 구조"**(개방-폐쇄 원칙, Open-Closed Principle).

원본 pseudo code 는 `runner/runner_presudo.md` 에 있다. 이 문서는 그것을 실측과 대조해
고친 것이다.

## 배경 — 실측 (🔵 2026-09-08)

### 중복은 실재한다

| 중복 | 어디 | 벌 수 |
|---|---|---|
| `for stage in stages:` 단계 루프 | `run_mode1.main` · `run_mode1_5.main` · `run_mode2.main` | 3 |
| `plan_stages()` (only/skip 검증 + 재개 거르기) | 같은 셋 | 3 |
| `is_agent_stage()` + `AGENT_STAGES` 집합 | 같은 셋 | 3 |
| `normalize_usage(None)` 을 손으로 적기 (기계 단계의 토큰 0) | `run_mode1` 7 · 나머지 각 1 | 9 |

### 재는 코드를 얻으려고 `run_mode1` 을 import 하는 것이 부작용을 낳는다

`run_mode1_5.py` 와 `run_mode2.py` 는 `hms` · `format_report` · `Heartbeat` 같은
**재는 코드 9개**를 쓰려고 `import run_mode1 as M` 한다. 그런데 `run_mode1.py` 는
모듈 최상단에서 `_bootstrap_venv()` 를 호출하고 `machine/survey_plan.py` 를 import 한다.

    $ /opt/homebrew/bin/python3 probe.py      # 시스템 파이썬으로 run_mode2 를 import
    prefix: <저장소>/.venv                     ← os.execv 로 해석기가 통째로 바뀌었다
    networkx loaded: True                     ← Mode 2 는 networkx 를 쓰지 않는다
    survey_plan loaded: True

Mode 2 · Mode 1.5 는 `networkx` 도 `.venv` 재실행도 필요 없다. 재는 코드가 `run_mode1` 에
얹혀 있다는 이유 하나로 딸려 온다.

### 단계 사이를 건너다니는 값이 다섯 개 있다

`run_mode1.main` 이 지역 변수로 들고 다니는 것들이다. `warmup` 이 담아 `survey-plan` 과
`survey` 와 `warmup-save` 가 꺼내 쓴다.

    targets · entries · warmup_cache · tracked_n · plan_json

이 값들이 pseudo code 에는 없다. `perform()` 이 인자를 받지 않기 때문이다.

### LLM 단계 셋은 프롬프트만 다른 것이 아니다

| 단계 | LLM Model 호출 | 병렬 | 호출 뒤에 하는 일 |
|---|---|---|---|
| `lang-select` | 1회 | 없음 | 낱말 하나 파싱 → **`machine/lang_select.py` 를 자식 프로세스로** 돌려 제안을 기각/채택 |
| `survey` | 층마다 N회 | 동시 8 | 층이 끝날 때마다 `merge_shards` 로 샤드 병합 → 디스크 쓰기 |
| `wiki` | 목차 1회 + 장마다 N회 | 동시 8 | `wiki-plan.json` 을 읽어 층을 다시 계산 |

근거는 `run_mode1.py` 의 `run_lang_select` · `run_survey` · `run_wiki` · `run_layer` 다.
그래서 `getabstract_llm_prompt() -> string` 이라는 **단수 훅 하나**로는 셋을 못 덮는다.

### 한 단계가 측정 행을 여러 개 낸다

`run_survey` 와 `run_wiki` 의 반환형이 `list[StageRow]` 다 — 세션마다 한 행.
`perform()` 이 단수 결과를 내면 이 모양을 담지 못한다.

## §2.5 구조 신설 선언 — grep 으로 잰 것

| 항목 | 실측 |
|---|---|
| 구현자 수 (지금/예상) | 3 / 3. `run_grade.py` 는 단계 루프가 없어 제외 |
| 소비자 수 (지금/예상) | 3 실행기 + 시험 4개. 시험이 모듈 최상위 이름을 약 200회 참조한다 |
| 삭제 시험 | 이 구조를 지우면 위 표의 중복 3벌·9곳이 그대로 되살아난다. 지금이 바로 그 상태다 |
| 계획서 관계 | **계획 밖.** `docs/superpowers/plans/` 어디에도 이 항목이 없다 |

계획 밖이므로 대체불가 논거가 필요하다. 두 가지다 —
**① import 부작용**(위 실측)은 구조를 안 바꾸면 못 고친다.
**② 사용자가 요구한 개방-폐쇄**는 데이터로 표현되는 전이표 없이는 `if/elif` 수정으로만 확장된다.

## §2.7 축 선언 — 이 제안에 든 축 넷

1. **공통 추상의 두께** — D0 에서 결정 (사용자 선택)
2. **착지점을 정하는 자리** — D1 에서 결정 (사용자 선택)
3. **`lang-select` 의 혼합 성격 처리** — D4 에서 결정 (사용자 선택)
4. **모듈 경계** — D7 에서 결정 (사용자 선택)
5. **경계의 형 엄격도** — D10·D11 에서 결정 (사용자 요구)
6. **흐름을 언제 확정하는가** — D9·D12 에서 결정 (사용자 요구)
7. **증분과 전량의 의도 분리** — D13·D14·D15 (사용자 요구)
8. **LLM 단계의 훅 모양** — D3·D16 에서 재결정 (사용자 재검토 요구)

## Decision Log

| # | 결정 | 상태 | 신뢰도 |
|---|---|---|---|
| D0 | 공통축을 `Stage` 기반 클래스 + 교체 가능한 착지점으로 세운다 | `[승인됨]` | 🔵 90 |
| D1 | 전이표는 파이프라인 밖에 하나 둔다 | `[승인됨]` | 🔵 90 |
| D2 | `Stage` 는 상태를 갖지 않는다. 갈래는 `Outcome` 반환값이다 | `[제안됨]` | 🔵 85 |
| D3 | `llmstage` 의 훅은 **다섯이고 넷은 기본값이 있다.** 단일 호출은 하나만 구현한다 | `[번복됨]` | 🔵 88 |
| D4 | `lang-select` 를 `lang-propose` + `lang-decide` 로 쪼갠다 | `[승인됨]` | 🔵 88 |
| D5 | 단계 사이의 값은 `Context` 로 명시적으로 넘긴다 | `[제안됨]` | 🔵 88 |
| D6 | `pipeline.run` 은 가상 함수가 아니다 | `[제안됨]` | 🔵 90 |
| D7 | 모듈 경계 — 공통 2파일 + `mode1/` 패키지 (안 A) | `[승인됨]` | 🔵 85 |
| D8 | `run_mode1.py` 는 옛 이름을 재수출하는 파사드로 남는다 | `[제안됨]` | 🔵 85 |
| D9 | 흐름 전체를 `StageDagGraph` 로 **미리 짓는다.** 팩토리가 진입점에서 만들고 보장한다 | `[번복됨]` | 🔵 85 |
| D10 | 단계의 입력·출력은 `machine/` 의 기존 TypedDict 로 못 박고 경계에서 검증한다 | `[제안됨]` | 🔵 88 |
| D11 | `Any` 를 러너에서 **완전히 없애고** `object` + 좁히기로 바꾼다. 게이트로 강제한다 | `[제안됨]` | 🔵 92 |
| D12 | 그래프는 **비순환**이고, 재시도는 **재개 JSON** 으로 한다. 모든 중단이 그것을 남긴다 | `[번복됨]` | 🔵 88 |
| D13 | Mode 1 을 **증분 그래프와 전량 그래프 둘**로 나눈다. 팩토리가 고른다 | `[제안됨]` | 🔵 88 |
| D14 | `survey-plan.json` 이 **자기가 좁혀진 것인지 스스로 말한다** | `[제안됨]` | 🔵 90 |
| D15 | `prep` 의 건너뜀 판정을 **파일 존재에서 `targets` 로** 바꾼다 | `[승인됨]` | 🟡 72 |
| D16 | `wiki` 를 `wiki-catalogue` + `wiki-pages` 로 쪼갠다 | `[제안됨]` | 🔵 85 |

### D0 · 공통축은 `Stage` 기반 클래스 + 교체 가능한 착지점 (Option A)

- Status: `[승인됨]` — 사용자 선택 (2026-09-08)
- 확신도: 🔵 90 — 중복 3벌이 실측이고, 소비자 3은 `design-decision-discipline` §4 의
  "두 번 이상 나타난 뒤에 추상화한다" 를 넘는다
- 옵션 4 (데이터 주도 드라이버 / 재는 코드만 분리 / 추상 기반 클래스 / State·Transition 그래프)
- 사용자 근거: *"추후 파이프라인 개발 후 확장에 열려있고 변경에 닫혀있는 구조를 원했다.
  Mode 1 에서 항상 고정적으로 흘러가는 게 아니라 손쉬운 Fall-Back 착지점, Cascade 분기
  착지점을 교체할 수 있을 것이라 보았다."*

**주의 — Fall-Back 과 Cascade 는 아직 코드에 없다.** 지금 세 루프의 실패는 전부 `break`
한 갈래로 흡수된다. 그러므로 이 결정은 §4 YAGNI 상 **미리 짓는 것**이고, 근거는 실측이
아니라 사용자의 확장 의도다. D4 가 그 첫 실사용처가 된다.

### D1 · 전이표는 파이프라인 밖에 하나

- Status: `[승인됨]` — 사용자 선택 (2026-09-08)
- 확신도: 🔵 90
- 옵션 3 (Stage 가 기본값·파이프라인이 덮어쓰기 / `Outcome` 이 착지점을 들고 오기 /
  파이프라인 밖 전이표 하나)
- 대가로 받아들이는 것: **Stage 만 읽어서는 다음이 어딘지 모른다.** 흐름을 알려면
  전이표를 함께 봐야 한다(두 곳 보기). 대신 흐름 전체가 한 화면에 있고 통째로 교체된다

### D2 · `Stage` 는 상태를 갖지 않는다

- Status: `[제안됨]`
- 확신도: 🔵 85 — `run_survey` 가 같은 단계를 **층마다 다시** 도는 것이 실측이다
- 옵션 2 (`curtransition` 을 멤버 변수로 / `Outcome` 반환값으로)
- pseudo code 의 `curtransition -> int` 를 멤버로 두면 재진입에서 앞 층의 값이 남는다.
  `emits`(낼 수 있는 갈래의 비트합)만 클래스에 남기고, 실제로 난 갈래는 반환한다
- `emits` 는 선언이므로 **시작 전에 전이표 완결성을 검사**할 수 있다 —
  비트가 섰는데 전이표에 대응 행이 없으면 그 자리에서 죽인다

### D3 · `llmstage` 의 훅은 다섯이고 넷은 기본값이 있다

- Status: `[번복됨]` — 앞선 판(훅 셋)을 실측 재조사로 뒤집는다 (2026-09-08)
- 확신도: 🔵 88 — 다섯 자리를 전부 폈다
- 옵션 4 (프롬프트 훅 하나 / 훅 셋 / 두 클래스로 가르기 / **훅 다섯 + 기본값 넷**)

**뒤집힌 것.** 앞선 판은 훅 셋(`rounds` · `jobs` · `harvest`)이었다. 근거로 "세 LLM 단계가
호출 횟수·병렬·거두기까지 다르다" 를 들었는데, **그 셋을 Mode 1 만 보고 셌다.**
Mode 2 와 Mode 1.5 를 함께 재니 그림이 달라졌다.

| 자리 | 모드 | 세션 수 | 병렬 | LLM Model | 호출 뒤 |
|---|---|---|---|---|---|
| `lang-propose` | 1 | **1** | — | **haiku 고정 상수** | 낱말 파싱 |
| `wiki` 목차 | 1 | **1** | — | `--model` | `wiki-plan.json` 이 나왔는지 확인 |
| `mode2-agent` | 2 | **1** | — | `--model` | `result` 출력 |
| `survey` | 1 | 층마다 N | 동시 8 | `--model` | `merge_shards` → 디스크 |
| `wiki` 장 | 1 | 층마다 N | 동시 8 | `--model` | 없음 |
| 기계 단계 13개 | 1 · 1.5 · 2 | 자식 1 | **0건** | — | — |

**축을 둘 뭉쳐 놨었다.** 실제로는 직교하는 축이 둘이다.

  - **LLM Model을 부르는가** — 토큰이 나오는 자리인가. LLM 5 · 기계 13
  - **세션을 몇 개 띄우는가** — LLM 중 단일 3 · 팬아웃 2. **기계 중 팬아웃은 0건이다**

두 축이 상관은 있지만(팬아웃은 전부 LLM) 같지 않다. 훅 셋은 두 번째 축만 보고 지은 것이라
**단일 호출 3개가 `rounds()->1` 과 목록 감싸기를 군더더기로 쓰게 된다.**

**팬아웃은 단일의 일반화이고, 그것이 이미 코드에 있다.** `run_wiki` 의 목차 호출:

    got = run_layer(model, repo, root, [("catalogue", wiki_catalogue_prompt(repo, root))], 1, timeout)

단일 호출을 팬아웃 함수에 job 하나로 넣어 부른다. 억지가 아니라 자연스럽게 읽힌다.

**재제안 — 훅 다섯, 필수는 하나.**

    llmstage[C]
        prompt(ctx)                  : virtual -> string              # ← 이것만 필수
        model(ctx)                   : virtual -> string  = ctx.model
        rounds(ctx)                  : virtual -> int     = 1
        jobs(ctx, round)             : virtual -> [(라벨, 프롬프트)]
                                                          = [(self.name, self.prompt(ctx))]
        harvest(ctx, results, round) : virtual -> Outcome = 갈래 판정 + 세션마다 행 하나
        perform(ctx)                 : 재정의 금지

| 구체 단계 | 구현하는 훅 |
|---|---|
| `mode2-agent` · `wiki-catalogue` | `prompt` |
| `lang-propose` | `prompt` · `model` |
| `wiki-pages` | `rounds` · `jobs` |
| `survey` | `rounds` · `jobs` · `harvest` |

**`model` 훅이 새로 생긴 이유** — `lang-propose` 만 `LANG_SELECT_MODEL`(haiku) 상수를 쓴다.
지금은 `run_lang_select` 안에 박힌 특수 경우인데, 훅으로 올리면 그것이 **선언**이 된다.
싼 LLM Model을 쓰는 단계가 늘어도 자리가 이미 있다.

**두 클래스로 가르지 않는 이유** — `abstractstage` → `llmstage` → `{Single, Fanout}` 로
3단이 된다. §3 이 경고한 "부모가 추상이 아니라 자식들의 합집합으로 부푼다" 가 정확히 그 꼴이고,
게다가 팬아웃이 단일의 일반화라 **가를 경계가 없다.** 기본값으로 같은 이득을 얻는다.

### D4 · `lang-select` 를 두 단계로 쪼갠다 (Option A)

- Status: `[승인됨]` — 사용자 선택 (2026-09-08)
- 확신도: 🔵 88
- 옵션 2 (두 단계로 쪼개기 / 한 단계로 두고 `harvest` 안에서 검사기 부르기)
- `lang-propose`(llmstage, LLM Model에게 언어를 묻는다) → `lang-decide`(rulebasestage,
  `machine/lang_select.py` 로 제안을 기각/채택)
- **이것이 D0 의 Fall-Back 착지점의 첫 실사용처다.** 지금은 LLM Model 호출 실패가
  `run_lang_select` 안의 `try/except` 에 숨어 있다. 쪼개면 전이표 한 줄이 된다:

      ('lang-propose', FAIL) -> 'lang-decide'    # 제안 없이 파일 수만으로 고른다

- **비호환 하나** — Mode 1 의 단계가 10개에서 11개가 된다. `--only lang-select` 를
  쓰던 명령줄이 깨진다. 별명 한 줄로 막는다: `lang-select` 는 두 단계로 펴진다

### D5 · 단계 사이의 값은 형이 붙은 `Context` 로 넘긴다 — 자루(bag)를 두지 않는다

- Status: `[제안됨]`
- 확신도: 🔵 88 — 건너다니는 값 다섯이 실측이고, `pyright strict` 가 게이트다
- 옵션 4 (Stage 멤버 / 모듈 전역 / `dict[str, Any]` 자루 / **칸마다 이름과 형이 있는 dataclass**)
- Stage 멤버에 담으면 Stage 끼리 서로를 알게 되고, 전역에 두면 시험이 격리되지 않는다
- **`dict[str, Any]` 자루는 거부한다.** `pyrightconfig.json` 이 `runner` 를 포함한
  `typeCheckingMode: strict` 라, 자루를 쓰면 꺼내 쓰는 자리마다 `cast` 가 붙는다.
  형 검사를 켜 둔 채로 형 검사를 끄는 셈이다
- 모드마다 자기 `Context` 를 갖고, 공통 부모는 얇게 둔다. `Stage` 와 `pipeline` 은
  형 인자 하나로 그것을 받는다(`Stage[C]` · `Pipeline[C]`). **형 인자는 하나뿐이다** —
  그 이상 일반화하지 않는다

      @dataclass
      class RunContext:                     # 세 모드가 공유하는 것만
          root: str
          model: str
          timeout: float | None

      @dataclass
      class Mode1Context(RunContext):
          repo: str
          concurrency: int
          target: int
          hops: int
          # 단계 사이를 건너다니는 값 — 전부 이름과 형이 있다
          targets:      list[str] | None            = None
          entries:      warmup.Manifest | None      = None
          warmup_cache: str | None                  = None
          tracked_n:    int                         = 0
          plan:         survey_plan.SurveyPlan | None = None

### D6 · `pipeline.run` 은 가상 함수가 아니다

- Status: `[제안됨]`
- 확신도: 🔵 90
- pseudo code 는 `run_mode1 : pipeline` 이 `run` 을 override 하게 두었다. 그러면
  드라이버 루프가 다시 3벌이 되어 이 작업이 없애려는 중복이 그대로 돌아온다
- 개방-폐쇄로 보면 방향이 반대다. **`run` 은 수정에 닫히는 쪽**이고, 열리는 것은
  단계 목록과 전이표라는 **데이터**다
- 같은 이유로 pseudo code 의 `stages.foreach.Run()` 도 고친다 — `foreach` 는
  `next_stage` 를 버린다. 전이가 뜻을 가지려면 `while cur:` 여야 한다

### D7 · 모듈 경계 — 공통 2파일 + `mode1/` 패키지 (안 A)

- Status: `[승인됨]` — 사용자 선택 (2026-09-08)
- 확신도: 🔵 85 — 셋 다 동작하므로 옳고 그름이 아니라 탐색 비용의 문제였다

| 안 | 모양 | 대가 |
|---|---|---|
| **A. 공통 2파일 + mode1 패키지** | `runner/measure.py` · `runner/pipeline.py` · `runner/mode1/{prompts,stages,layers,edges}.py` | 파일 9개. 모든 파일이 400줄 아래로 내려간다 |
| **B. 공통도 패키지로** | `runner/pipeline/{outcome,stage,transition,driver,measure}.py` + mode1 패키지 | 개념당 파일 하나로 찾기 쉽다. 소비자 3에 파일 5는 거울 함정 위험 |
| **C. 평면 — 패키지 없이** | `runner/` 아래 형제 모듈만 (`mode1_prompts.py` 등) | `sys.path` 장난이 지금과 똑같아 import 가 가장 덜 바뀐다. `runner/` 가 평평해진다 |

**A 채택.** B 는 파일 5개를 만들 만큼 개념이 무겁지 않고, C 는 `mode1_` 접두사가
패키지를 흉내 내는 이름 규약이 된다.

### D8 · `run_mode1.py` 는 파사드로 남는다

- Status: `[제안됨]`
- 확신도: 🔵 85 — 시험의 참조 횟수가 실측이다
- 시험 4개(2,011줄)가 `R.plan_stages`(29회) · `R.normalize_usage`(22회) 처럼 모듈
  최상위 이름을 약 200회 참조한다. 옛 이름을 재수출하면 **시험 파일을 한 줄도 안 고치고**
  분리할 수 있다
- 되돌릴 조건: 시험이 새 모듈을 직접 부르도록 옮겨지면 파사드를 지운다

### D9 · 흐름 전체를 `StageDagGraph` 로 미리 짓는다 — 팩토리가 진입점에서 보장한다

- Status: `[번복됨]` — 앞선 판(사전 거르기 유지)을 사용자 지시로 뒤집는다 (2026-09-08)
- 확신도: 🔵 85
- 옵션 2 (루프 전 사전 거르기로 유지 / **팩토리가 검증된 그래프를 미리 만든다**)
- 사용자 요구: *"`StageDagGraph` 가 미리 준비되어 있도록 보장하자. 스크립트단에서,
  즉 Cascade 된 흐름 · Fallback 시뮬레이터가 보장된 `StageDagGraph` 팩토리 생성해야 함."*

**뒤집힌 것.** 앞선 판은 `--only` · `--skip` · 재개 거르기를 루프 **전**의 사전 거르기로
두고 전이표는 실행 중에 생긴 갈래만 다루게 했다. 반대 근거는 *"돌지 않은 단계와 돌았는데
건너뛴 단계가 섞여 `--dry-run` 이 무엇을 보여줄지 모호해진다"* 였다.

**그 반대 근거가 오히려 팩토리를 요구한다.** 팩토리가 그래프를 미리 지으면 `--dry-run` 은
**그 그래프를 그대로 찍으면 된다.** 지금처럼 단계 이름을 한 줄로 나열하는 것이 아니라,
폴백 간선까지 포함한 실제 흐름을 보여 준다. 모호함은 사전 거르기를 유지해서가 아니라
**흐름을 자료로 만들어서** 없어진다.

    build_mode1_graph(ctx, only, skip) -> StageDagGraph
        │  ① 단계 집합을 정한다      (--only · --skip · 재개 판정)
        │  ② 전이 간선을 붙인다      (MODE1_EDGES 에서, 살아남은 단계만)
        │  ③ 보장한다               (아래 D9 검사 넷 + D12)
        └─ 하나라도 어긋나면 **여기서 죽는다.** 단계는 한 개도 돌지 않았다

**팩토리는 진입점에서 부른다.** `main()` 이 인자를 읽자마자, 어떤 자식 프로세스도 띄우기
전에. 실패가 늦게 나면 이미 파일을 쓴 뒤라 되돌리기 어렵다.

**Fallback 시뮬레이터 — 아무것도 실행하지 않고 그래프만 걷는다.** 각 단계가 낼 수 있는
갈래(`emits`)의 모든 조합을 따라가며 넷을 본다.

| 검사 | 무엇이 어긋나면 | 왜 실행 중에 못 잡나 |
|---|---|---|
| 완결성 | `emits` 비트가 섰는데 그 갈래의 간선이 없다 | 그 갈래가 실제로 나야만 터진다 |
| 도달성 | 어떤 단계로 가는 경로가 하나도 없다 | 조용히 안 돌고 끝난다 |
| 산출물 사슬 | **어떤 경로에서는** 읽을 파일을 앞의 누구도 쓰지 않는다 | 그 경로를 타야만 터진다 |
| 종료 | 어떤 경로가 `HALT` 에도 마지막 단계에도 닿지 않는다 | 매달린 채 끝난다 |

**산출물 사슬 검사가 가지 때문에 어려워진다.** 흐름이 한 줄일 때는 "앞선 단계가 썼나" 만
보면 됐다. 가지가 생기면 **그 단계에 닿는 모든 경로에서** 성립해야 한다.
`lang-propose` 가 실패해 `lang-decide` 로 떨어지는 경로에서도 `prep` 이 읽을
`lang-select.json` 이 있어야 한다 — 그 경로를 실제로 타 보기 전에는 사람이 놓친다.
**이것이 시뮬레이터가 손 검토보다 나은 유일한 이유다.**

**`plan_stages` 는 사라지지 않고 팩토리의 ① 이 된다.** 세 벌이 한 벌로 합쳐지는 것은 그대로다.

### D12 · 그래프는 비순환이고, 재시도는 재개 JSON 으로 한다

- Status: `[번복됨]` — 앞선 판(재시도를 아예 포기)을 사용자 지시로 뒤집는다 (2026-09-08)
- 확신도: 🔵 88
- 옵션 3 (비순환 고정 + 재시도 포기 / 순환 허용 + 방문 횟수 상한 / **비순환 + 재개 JSON**)
- 사용자 요구: *"종료조건이 완벽하게 통제되어야 한다. 어디서 실패했는지를 Fall-Back 하면서
  JSON 값을 리턴하도록 하고, DAG-Graph-Factory 에 이 Fallback 에서 나온 JSON 을 입력받으면
  이전 실패했던 지점에서만 다시 시작하도록 구성하자."*

**뒤집힌 것.** 앞선 판은 "비순환이므로 재시도를 못 만든다" 를 대가로 받아들였다.
재시도가 **프로세스 안의 순환**이어야 한다고 전제했기 때문이다. 그 전제가 틀렸다.

**재시도는 순환이 아니라 새 그래프다.**

    1회차:  … ▶ survey ──FAIL──▶ halt-with-resume  ─────▶  resume.json 을 쓴다
                                                              │
    2회차:  build_mode1_graph(ctx, resume=resume.json) ◀──────┘
            └─ survey 부터 시작하는 **더 작은 비순환 그래프**를 짓는다

그래프는 여전히 비순환이다. 되돌아가는 간선이 하나도 없다. 재시도는 **프로세스 경계 밖**에서
일어나고, 그 경계를 넘는 것이 재개 JSON 이다. D14 가 계획의 범위를 파일에 실어 프로세스
경계를 넘긴 것과 같은 수법이다.

**불변식 — 모든 중단은 재개 JSON 을 남긴다.** 이것이 사용자가 말한 "종료조건의 완벽한 통제"다.
시뮬레이터의 종료 검사가 이렇게 완결된다.

    모든 경로는 둘 중 하나에 닿는다
      ⑴ 마지막 단계 (정상 종료)
      ⑵ 재개 JSON 을 남기는 중단 (halt-with-resume)
    어느 쪽에도 안 닿는 경로가 있으면 팩토리가 죽는다

**`resume.json` 이 담는 것.** 새 스키마이므로 D10 의 규율을 그대로 받는다(`machine/` 에
없는 것이라 러너가 선언한다. `Any` 없음, 경계에서 검증).

| 칸 | 무엇 | 왜 필요한가 |
|---|---|---|
| `graph` | 어느 그래프였나 (`mode1-cold` · `mode1-warm` · `mode2` …) | 다른 그래프의 재개 JSON 을 잘못 먹이는 것을 막는다 |
| `failed_at` | 실패한 단계 이름 | 여기부터 다시 시작한다 |
| `why` | 갈래와 사유 | 사람이 읽는다. 프롬프트 결함인지 환경 문제인지 가른다 |
| `done` | 성공으로 끝난 단계 이름들 | 팩토리가 그만큼 그래프를 줄인다 |
| `rows` | 그때까지의 측정 행 | 재개해도 전체 비용이 이어져 보인다 |
| `scope` | 증분 범위 (`only_files`) | D14 의 칸과 같은 것. 재개가 범위를 잃지 않는다 |

**사용자가 짚은 것 하나를 그대로 옮겨 둔다** — *"실패한 것이 애초에 설계와 프롬프트에 잘못된
부분이 있다고 생각한다."* 그래서 `why` 는 사람이 읽으라고 있는 칸이다. 재개가 자동 재시도로
읽히면 안 된다 — **같은 프롬프트로 다시 돌리면 같은 자리에서 또 실패한다.**
재개 JSON 은 *다시 하기*가 아니라 *고치고 나서 거기부터*를 위한 것이다.

**⚠ 배치 수준 재개는 아직 신뢰할 수 없다.** 인계 문서 결함 ③ — 배치 id 가 위치 기반이라
계획이 바뀌면 남은 샤드가 남의 배치를 대신한다. `resume.json` 은 **단계 수준**만 담고,
배치 수준 재개는 ③이 고쳐진 뒤에 얹는다.

### D16 · `wiki` 를 `wiki-catalogue` + `wiki-pages` 로 쪼갠다

- Status: `[제안됨]`
- 확신도: 🔵 85 — `run_wiki` 안에 손으로 쓴 산출물 검사가 실재한다
- 옵션 2 (한 단계로 두기 / 두 단계로 쪼개기)
- D4(`lang-select` 쪼개기)와 같은 패턴이다. 훅 때문이 아니라 두 가지 때문이다.

**⑴ D10 의 `writes` 가 손코딩 검사를 대신한다.** 지금 `run_wiki` 에는 이런 코드가 있다.

    if not os.path.exists(wiki_plan_path):
        rows.append({... "ok": False, "why": "wiki-plan.json 이 나오지 않았다"})
        return rows

`wiki-catalogue.writes = [wiki_plan_artifact]` 이면 드라이버가 공통으로 한다.

**⑵ 그래프가 실제 의존을 보인다.** 목차가 낸 파일을 장들이 읽는다는 사실이 지금은 함수
안에 숨어 있다. 쪼개면 산출물 사슬 검사(D9)의 대상이 된다.

**⚠ 단계 수가 는다.** Mode 1 은 D4 로 11개, D16 으로 **12개**가 된다.
`--only wiki` 를 쓰던 명령줄은 D4 와 같은 별명 규칙으로 막는다.

### D10 · 입력·출력을 `machine/` 의 기존 TypedDict 로 못 박고 경계에서 검증한다

- Status: `[제안됨]`
- 확신도: 🔵 88 — 스키마가 이미 있다는 것과 검증 선례가 있다는 것 둘 다 실측이다
- 옵션 3 (지금처럼 `dict[str, Any]` + `.get()` / `cast` 만 붙이기 / **경계에서 검증**)

**스키마를 새로 만들지 않는다.** `machine/` 이 이미 JSON 산출물마다 TypedDict 를 선언해
두었다 — `codegraph_types.CodeGraph` · `survey_plan.SurveyPlan` · `warmup.Manifest` ·
`warmup.Entry` · `lang_select.LangSelect` · `declmap.FileDecls` 등. 러너는 **가져다 쓴다.**
러너가 새로 선언할 것은 러너만 아는 두 개뿐이다(`StageRow` · `WikiPage`, 지금도 그렇다).

**`cast` 는 검증이 아니다.** 지금 `run_mode1.main` 은 디스크에서 읽은 층 계획을
`cast(survey_plan.SurveyPlan, json.load(f))` 로 받으며 주석에 *"디스크에서 읽은 것이라
기계가 꼴을 확인할 수 없다"* 고 적어 두었다. `cast` 는 검사기에게 거짓말을 하는 것이라
꼴이 어긋나면 **엉뚱한 자리에서** 터진다.

**Mode 1.5 에 이미 선례가 있다.** `run_mode1_5.validate_questions` 와 `validate_answers`
가 바로 이 일을 한다 — 읽은 JSON 이 채점 가능한 꼴인지 보고 불평 목록을 낸다.
D10 은 그것을 세 모드로 넓히는 것이다.

각 Stage 는 자기가 읽고 쓰는 산출물을 **선언**한다. `emits` 가 갈래의 계약인 것과 같은 자리다.

    class Artifact(Generic[T]):
        path(ctx)  -> string          # 자리는 ctx 가 정한다. 경로를 박지 않는다
        schema     -> type[T]         # machine/ 의 TypedDict
        check(obj) -> [string]        # 불평 목록. 비면 통과

    abstractstage
        reads  -> [Artifact]          # 없으면 단계를 돌리기 전에 죽는다
        writes -> [Artifact]          # 돌린 뒤 꼴을 보고 어긋나면 FAIL

    load(artifact, ctx) -> T | None   # cast 를 쓰지 않는다. check 를 통과해야 낸다
    dump(artifact, ctx, obj: T)       # 쓰기 전에 check

**검증의 깊이는 얕게 못 박는다 — 거울 함정 경계.** 최상위 필수 열쇠가 있는지와 그 열쇠의
성긴 형(list 인가 dict 인가 int 인가)까지만 본다. 안쪽 원소는 믿는다. 스키마 언어·검증
데코레이터·JSON Schema 파일을 도입하지 않는다. `validate_questions` 가 지금 하는 깊이가
그 기준선이다.

**이것이 주는 것 둘.**

1. `--only survey` 처럼 앞칸을 건너뛰고 불러 층 계획이 없을 때, 지금은 `main` 안의
   `if not os.path.exists(...)` 특례로 막는다. `reads` 선언이 있으면 **드라이버가 공통으로**
   막고 어느 산출물이 없어서 못 도는지 이름으로 말해 준다
2. 전이표 완결성 검사(D2)와 같은 자리에서 **산출물 사슬 검사**가 공짜로 생긴다 —
   어떤 단계의 `reads` 를 앞선 어떤 단계도 `writes` 하지 않으면 시작 전에 죽는다

### D11 · `Any` 를 러너에서 완전히 없앤다 — `object` + 좁히기 사다리

- Status: `[제안됨]`
- 확신도: 🔵 92 — 이번 세션에 탐침을 짜서 `pyright` 로 실제로 돌려 봤다
- 옵션 3 (지금대로 `Any` 허용 / `Any` 를 줄이되 경계에만 남기기 / **완전히 없애고 게이트로 막기**)
- 사용자 요구: *"Stage 경계마다도 인풋, 리턴 JSON 스키마가 엄격하게 달라야 한다. 똑같은
  JSON 문자열을 주고받더라도 직렬화·역직렬화에서는 반드시 엄격한 타입을 가지고 `Any` 를
  일절 쓰지 않도록. 파이썬 컴파일러를 통해서도 잡을 수 있도록."*

**실측 ① — `pyright strict` 는 명시적 `Any` 를 잡지 못한다.**

    def read_any(path: str) -> Any: ...
    def use_any(path: str) -> int:
        d = read_any(path)
        return d["layers"][0].nope     # ← 오류 0건. 조용히 통과한다

`pyrightconfig.json` 에 `reportExplicitAny` 와 `reportAny` 를 넣어도 pyright 1.1.413 은
**그 설정을 무시한다**(오류 수가 5로 그대로였다). 그 둘은 basedpyright 의 규칙이다.
`strict` 가 잡는 것은 `Unknown` 의 **전파**이지 저자가 손으로 적은 `Any` 가 아니다.

**실측 ② — `object` 로 받으면 검사기가 실제로 잡는다.**

    def read_obj(path: str) -> object: ...
    def use_obj(path: str) -> int:
        d = read_obj(path)
        return d["layers"]             # ← error: "__getitem__" 이 "object" 에 없다

**실측 ③ — `isinstance(v, dict)` 하나로는 부족하다.** 그렇게 좁히면 `dict[Unknown, Unknown]`
이 되어 `.get()` 이 다시 `reportUnknownMemberType` 으로 걸린다. 열쇠와 값의 형까지 좁혀야 한다.

**실측 ④ — `Any` 0개로 `pyright strict` 0 오류가 실제로 가능하다.** 아래 모양을 짜서 통과시켰다.

    def is_map(v: object) -> TypeIs[dict[str, object]]:
        if not isinstance(v, dict):
            return False
        keys = cast(dict[object, object], v).keys()
        return all(isinstance(k, str) for k in keys)

    def read_json(path: str) -> object:
        with open(path, encoding="utf-8") as f:
            return cast(object, json.load(f))     # json.load 의 Any 를 막는 유일한 자리

    def parse_plan(raw: object) -> tuple[Plan | None, list[str]]:
        if not is_map(raw):
            return None, ["최상위가 객체가 아니다"]
        target = raw.get("target")                # target: object
        ...                                       # isinstance 로 하나씩 좁힌다

**`cast` 두 종류를 갈라야 한다.** D10 이 거부한 `cast` 와 여기 쓰는 `cast` 는 다른 것이다.

| 쓰는 `cast` | 무엇을 주장하나 | 판정 |
|---|---|---|
| `cast(SurveyPlan, json.load(f))` | 안 본 값이 깊은 스키마와 같다고 **주장한다** | 거부 (D10) |
| `cast(dict[object, object], v)` | `isinstance` 가 이미 증명한 것에 "값은 object" 를 더한다 | 허용 — 항상 참인 문장이다 |
| `cast(object, json.load(f))` | `Any` 를 `object` 로 **좁힌다**. 넓히지 않는다 | 허용 — `Any` 를 막는 자리다 |

**`Any` 를 정말 못 쓰는 자리는 어떻게 하나.** 바깥 프로그램이 꼴을 정하는 둘(`AgentResult`
— `claude -p` 가 내는 JSON, `Records` — 배치 세션이 칸을 채우는 레코드)도 예외가 아니다.
`dict[str, Any]` 대신 **`dict[str, object]`** 로 적고 꺼내 쓰는 자리에서 `isinstance` 로
좁힌다. 모양을 못 박지 못하는 것과 `Any` 를 쓰는 것은 다른 문제다 —
전자는 스키마의 문제이고 후자는 검사를 끄는 것이다.

**강제는 게이트로 한다.** pyright 가 못 잡으므로 시험 하나를 더한다.

    # test/test_no_any.py
    grep -rn "\bAny\b" runner/**.py   →  형 자리에 나오면 실패

**지금 얼마나 있나 (🔵 실측).** 러너의 `Any` 는 **24곳**이다 —
`run_mode1_5.py` 20 · `run_mode1.py` 4. 여기에 `runner/term/quiz.py` 와
`runner/wiki/check.py` 가 더 있으나 그 둘은 범위 밖이다(얼갈이 단계).
`run_mode2.py` 와 `run_grade.py` 는 이미 0이다.

**각 구체 단계가 자기 직렬화 모듈을 갖는다.** 단계 A 와 단계 B 가 같은 JSON 문자열을
주고받더라도, A 의 `writes` 스키마와 B 의 `reads` 스키마는 **각각 따로 선언한다.**
한쪽을 고치면 다른 쪽이 검사기에서 깨져야 하기 때문이다. 공용 "만능 파서" 를 두면
그 깨짐이 사라진다.

### 산출물과 스키마 대조표

| 산출물 | 쓰는 단계 | 읽는 단계 | 스키마 |
|---|---|---|---|
| `out/codegraph-raw/lang-select.json` | `lang-decide` | `prep` | `machine/lang_select.py` 의 `LangSelect` |
| `out/codegraph-raw/codegraph.json` | `prep` | `warmup` · `survey-plan` · `terms` | `machine/codegraph_types.py` 의 `CodeGraph` |
| `out/codegraph-raw/survey-plan.json` | `survey-plan` | `survey` · `wiki` | `machine/survey_plan.py` 의 `SurveyPlan` |
| warmup 매니페스트 | `warmup-save` | `warmup` | `machine/warmup.py` 의 `Manifest` |
| `docs/codegraph/terms-reading.json` | `survey` | `terms` | 러너의 `Records` (레코드 칸은 배치 세션이 정하므로 못 박지 않는다) |
| `out/codegraph-raw/wiki-plan.json` | `wiki`(목차) | `wiki`(장) | 러너의 `WikiPage` 목록 |
| `term-candidates.json` | `collect` | `grade` | Mode 1.5 — 러너가 선언 |
| `questions.json` · `answer-sheet.json` · `answers.json` | 스킬 / `collect` | `grade` | **이미 `validate_questions` · `validate_answers` 가 있다** |
| `term-grades.json` | `grade` | `emit` | Mode 1.5 — 러너가 선언 |

`Records` 의 **안쪽 칸**은 못 박지 않는다 — 배치 세션이 채우므로 러너가 정하지 않는다.
`AgentResult`(`claude -p` 의 출력)도 같다. **그러나 그것이 `Any` 를 쓸 이유는 아니다** —
둘 다 `dict[str, object]` 로 적고 꺼내 쓰는 자리에서 좁힌다 (D11).

### 배경 추가 — 증분이 도달 불가였다 (인계 문서 실측, 2026-09-07)

`docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md` 가 원인 넷을 실측해 두었다.
사용자 허락을 받고 열었다.

| # | 무엇 | 실측 |
|---|---|---|
| ① | `plan_stages` 의 `if s == "survey" and has_reading: continue` — 레코드가 한 번 생기면 `survey` 가 영구히 빠진다 | `plan_stages(True, True, False)` 에 `survey` 가 없다. `should_call_agent` 는 `True` 를 내는데 불릴 자리가 없다 |
| ② | `targets` 가 프로세스 지역 변수라 단계를 쪼개면 조용히 전량으로 돌아간다 | 한 프로세스면 배치 17개, 쪼개면 88개. **경고가 없다.** 2026-07 에 $50.73 이 이렇게 나갔다 |
| ③ | 배치 id 가 위치 기반(`L0-B00`)이라 계획이 바뀌면 남은 샤드가 남의 배치를 대신한다 | 전량 88 · 좁힘 9 · id 겹침 9 → **같은 묶음 0 · 다른 묶음 9** |
| ④ | `merge_shards` 가 같은 심볼의 갱신을 충돌로 오인해 키를 개명한다 | 813키 중 675개 개명. `xmldoc check` 0 → 737건 |

**⑤ 는 그 문서에 없다** — 이 세션에서 따로 찾았다. `runner/wiki/prep.py` 의 `prepPlan` 은
`hasCodegraph`(**파일이 있는가**) 하나로 수집기와 `normalize` 를 통째로 건너뛴다.
`prep.py` 에 강제 재수집 플래그가 없고 `codegraph.json` 을 무효화하는 코드도 저장소에 없다 —
**다시 수집하려면 손으로 파일을 지우는 수밖에 없다.**

그래서 Mode 1 안에 **서로 말하지 않는 낡음 판정이 둘** 있다.

| 판정자 | 무엇을 보나 | 입도 | 낡았는지 아나 |
|---|---|---|---|
| `prepPlan` 의 `hasCodegraph` | 파일이 **있는가** | 저장소 전체, 전부 아니면 전무 | **모른다** |
| `warmup.status` | 선언 해시가 **바뀌었는가** | 파일별 | 안다 |

**⑤ 의 귀결 (🟡 85 — 코드 경로를 읽어 추적했고 재현하지는 않았다).** `run_warmup` 은
`declmap.scan` 으로 실제 소스를 읽으므로 신선하다. 그러나 지도는 낡은 채로 남아
`warmup.blast_radius` 와 `survey_plan.plan` 으로 흘러간다. `plan` 의 배치는 `cg["nodes"]`
에서만 나오므로 **지도에 없는 새 심볼은 warmup 이 지목해도 어떤 배치에도 들어가지 못한다.**

### D13 · Mode 1 을 증분 그래프와 전량 그래프 둘로 나눈다 — 팩토리가 고른다

- Status: `[제안됨]`
- 확신도: 🔵 88 — ①이 인계 문서에 실측으로 남아 있다
- 옵션 3 (지금처럼 한 흐름에 정적·동적 건너뜀을 겹치기 / **그래프 둘로 나누기** / mode 를 하나 더 만들기)
- 사용자 요구: *"증분용 stage, 완전 처음부터 시작하는 파이프라인 두 가지로 명시적으로 분리"*

**mode 를 더 만들지 않는다.** 루트 `CLAUDE.md` 가 mode 축 도입을 거울 함정으로 지목했고,
D9 의 팩토리가 이미 고르는 자리다.

    build_mode1_graph(ctx, only, skip, *, cold: bool) -> StageDagGraph
        cold=True   전량   lang-propose ▶ lang-decide ▶ prep(전량) ▶ survey-plan(전량) ▶ survey ▶ …
        cold=False  증분   lang-propose ▶ lang-decide ▶ warmup ▶ prep(증분) ▶ survey-plan(좁힘)
                                                        ▶ survey ▶ warmup-save ▶ …

**①이 구조로 사라진다.** `plan_stages` 의 `if s == "survey" and has_reading: continue` 를
지운다. 증분 그래프에서 `survey` 는 **언제나 그래프에 있고**, 바뀐 것이 없으면 `SKIP` 갈래를
내서 전이표가 다음 칸으로 보낸다. 정적 건너뜀과 동적 건너뜀이 겹쳐 있던 것이 갈린다 —
**정적인 것은 그래프 선택으로 올라가고, 동적인 것만 갈래로 남는다.**

**증분 그래프에서는 `warmup` 이 `prep` 보다 앞이다.** 어느 파일이 바뀌었는지를 알아야
`prep` 이 그 파일만 다시 수집할지 정할 수 있다. 지금은 `prep → warmup` 이라 순서가 거꾸로다.

**⚠ 이것은 동작 변경이다.** 이 문서의 "범위 밖" 이 *"전이표는 지금 동작과 1:1로 같은 값을
적는다"* 고 했는데, D13 은 그 예외다. ①을 고치는 것이 곧 두 그래프로 나누는 것이라 분리할 수 없다.
**예외는 이 하나뿐이고 나머지 전이는 1:1을 지킨다.**

**⚠ 안전장치가 함께 가야 한다.** 인계 문서가 경고한 대로, `survey` 를 기본 경로에 되살리면
**실수로 비싼 실행이 시작될 수 있다**(배치 88개 ≈ $50). 팩토리가 그래프를 지은 뒤
**예상 세션 수를 먼저 보이고 확인받는** 관문을 D13 과 한 묶음으로 넣는다.

### D14 · `survey-plan.json` 이 자기가 좁혀진 것인지 스스로 말한다

- Status: `[제안됨]`
- 확신도: 🔵 90 — ②가 실측이고 금액까지 붙어 있다
- 옵션 3 (지금대로 프로세스 지역 변수 / 디스크에서 읽을 때 **경고만** / **계획 파일에 범위를 싣는다**)
- `survey-plan.json` 스키마에 `only_files` 칸을 더한다. 없으면 전량, 있으면 그 목록이 범위다

**②가 D10 의 Artifact 로 자연히 해소된다.** 지금은 `targets` 가 프로세스 메모리에만 있어
`--only warmup,survey-plan` 과 `--only survey` 로 쪼개면 조용히 전량 계획이 쓰인다.
계획 파일이 자기 범위를 실으면 **프로세스 경계를 넘는다.**

그리고 D9 의 시뮬레이터가 이것을 검사할 수 있게 된다 —
**전량 그래프의 `survey` 가 좁혀진 계획을 읽거나 그 반대면 산출물 사슬 검사가 잡는다.**
지금은 사람이 화면을 보고도 구분할 수 없다.

**인계 문서의 갈래 D(경고만)보다 C(계획에 싣기)를 고른 이유** — 경고는 사람이 읽어야 하고,
`--dry-run` 이 좁히기를 반영하지 않는다는 별개 결함(인계 문서 "가드레일" 절)이 남는다.
계획에 실으면 `--dry-run` 도 그 파일을 읽어 그대로 보일 수 있다.

### D15 · `prep` 의 건너뜀 판정을 파일 존재에서 `targets` 로 바꾼다

- Status: `[승인됨]` — 사용자 선택 (2026-09-08). 세 번째 안(`targets` 를 받는다)
- 확신도: 🟡 72 — ⑤의 코드 경로는 읽었으나 귀결을 재현하지는 않았다
- 옵션 3 (지금대로 `hasCodegraph` / `--force` 플래그만 더하기 / **`targets` 를 받는다**)
- **범위를 넘는다.** `runner/wiki/prep.py` 는 이 문서가 "손대지 않는다" 고 적은 얼갈이다.
  D15 를 채택하면 그 경계를 한 파일만큼 연다

| 안 | 무엇 | 대가 |
|---|---|---|
| 지금대로 | `codegraph.json` 이 있으면 수집기를 건너뛴다 | 지도가 낡은 채 남고, 다시 수집하려면 **손으로 파일을 지워야 한다** |
| `--force` 플래그 | 전량 그래프가 `prep --force` 를 부른다 | 싸다. 두 판정자가 여전히 둘로 남는다 |
| `targets` 를 받는다 | 증분 그래프가 바뀐 파일 목록을 넘긴다 | 판정이 하나로 합쳐진다. 얼갈이를 고쳐야 하고 수집기별 부분 수집이 되는지 확인이 필요하다 |

**사용자가 세 번째를 골랐다.** 다만 **수집기가 부분 수집을 지원하는지 아직 재지 않았다** —
clang-uml 과 roslyn-dump 가 파일 목록을 받는지 확인하는 것이 구현의 첫 걸음이다.
받지 않으면 그 수집기에 한해 전량 재수집으로 물러선다. 그 물러섬은 결정 번복이 아니라
**수집기 능력에 따른 갈래**이므로 구현자가 정해도 된다.

### 순서 제약 — ③④가 먼저다

**증분 그래프는 ③④가 고쳐지기 전에는 신뢰할 수 없다.** ③은 남은 샤드가 남의 배치를
대신하게 하고, ④는 재조사할 때마다 레코드 키를 갈아 버린다. 둘 다 이 문서의 범위 밖이고
인계 문서가 이미 갈래를 적어 두었다(③ → E/F, ④ → G/H).

    ③④ 수정 (인계 문서 소관)  ─▶  D13·D14 (이 문서)  ─▶  증분 그래프를 실제로 쓴다

D13·D14 를 먼저 넣어도 해롭지는 않다 — 전량 그래프는 그대로 돌고, 증분 그래프는 ③④가
고쳐질 때까지 **쓰지 않으면 된다.** 다만 "증분이 된다" 고 말하지 않는다.

## 설계

### 형과 클래스

    Outcome                       # perform() 의 반환. Stage 는 상태를 갖지 않는다 (D2)
        kind   -> int             # OK | FAIL | SKIP | GATE  (정확히 하나)
        why    -> string
        rows   -> [StageRow]      # 세션 N개면 N행. 기계 단계는 1행

    RunContext                    # 드라이버가 소유한다 (D5). 자루(bag)를 두지 않는다
        root, model, timeout
    Mode1Context : RunContext     # 모드마다 자기 것. 칸마다 이름과 형이 있다
        repo, concurrency, target, hops
        targets      -> [string] | None
        entries      -> warmup.Manifest | None
        warmup_cache -> string | None
        tracked_n    -> int
        plan         -> survey_plan.SurveyPlan | None

    Artifact[T]                   # 단계가 읽고 쓰는 JSON 하나 (D10)
        path(ctx)  -> string
        schema     -> type[T]     # machine/ 의 기존 TypedDict
        check(obj) -> [string]    # 얕은 검증. 불평 목록

    abstractstage[C]              # C = 그 모드의 Context 형. 형 인자는 하나뿐이다
        name             -> string
        emits            -> int   # 낼 수 있는 갈래의 비트합. 선언이지 상태가 아니다
        reads            -> [Artifact]   # 없으면 돌리기 전에 죽는다 (D10)
        writes           -> [Artifact]   # 돌린 뒤 꼴이 어긋나면 FAIL
        perform(ctx: C)  -> Outcome

    rulebasestage : abstractstage
        argv(ctx)        : virtual -> [string]
        cwd(ctx)         : virtual -> string          # Mode 2 는 단계마다 다르다
        perform(ctx)     : 재정의 금지                 # 자식 프로세스 + 토큰 0 + 1행

    llmstage : abstractstage                          # (D3)
        rounds(ctx)                  : virtual -> int  # 1 또는 층 수
        jobs(ctx, round)             : virtual -> [(라벨, 프롬프트)]
        harvest(ctx, results, round) : virtual -> Outcome
        perform(ctx)     : 재정의 금지                 # round 마다 run_layer + harvest

    Edges                         # 파이프라인 밖 (D1). Stage 는 자기 다음을 모른다
        (stage_name, kind) -> dest_name | HALT | NEXT

    StageDagGraph[C]              # 팩토리가 미리 짓고 보장한 흐름 (D9)
        stages -> {name: abstractstage[C]}    # 이름으로 점프하므로 사전이다
        edges  -> Edges
        first  -> string
        render() -> string        # --dry-run 이 이것을 찍는다

    build_graph(ctx, only, skip) -> StageDagGraph[C]        # 진입점에서 부른다
        ① 단계 집합을 정한다   (--only · --skip · 재개 판정 — 옛 plan_stages)
        ② 살아남은 단계에 전이 간선을 붙인다
        ③ simulate(graph) 로 보장한다 — 어긋나면 여기서 죽는다

    simulate(graph) -> [string]   # 아무것도 실행하지 않는다. 그래프만 걷는다
        완결성    emits 비트마다 간선이 있는가
        도달성    닿을 수 없는 단계가 있는가
        산출물    **모든 경로에서** reads 를 앞의 누가 writes 하는가 (D10)
        종료      모든 경로가 HALT 또는 마지막 단계에 닿는가
        비순환    되돌아가는 간선이 있는가 (D12)

    pipeline[C]                   # 가상 함수 아님 (D6). mode 는 데이터만 넘긴다
        run(graph, ctx: C) -> [StageRow]
            cur = graph.first
            while cur:
                out = graph.stages[cur].perform(ctx)
                rows += out.rows
                cur = graph.edges.resolve(cur, out.kind)

### Before / After — Mode 1 의 흐름

**Before** — 단계 10개. 실패는 전부 한 갈래(`break`)로 흡수되고, 언어 선택의 폴백은
`run_lang_select` 안의 `try/except` 에 숨어 있다.

    lang-select ─▶ prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save
      └ (내부 try/except 폴백)                                    │
                                                          terms ─▶ wiki ─▶ build ─▶ check

    실패하면: break — 어느 단계든 같다

**After** — 단계 11개. 언어 선택의 폴백이 전이표의 한 줄로 드러난다.

    lang-propose ─▶ lang-decide ─▶ prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save
         │              ▲                                                          │
         └── FAIL ──────┘  (전이표 한 줄)                                            │
                                                          terms ─▶ wiki ─▶ build ─▶ check

    MODE1_EDGES = {
        ('lang-propose', FAIL): 'lang-decide',    # 제안 없이 파일 수만으로 고른다
        ('survey',       SKIP): 'warmup-save',    # 바뀐 파일 0개
        ('*',            FAIL): HALT,             # 나머지는 지금과 같다
    }

이 표는 팩토리의 재료일 뿐이고, **실제로 도는 흐름은 팩토리가 낸 `StageDagGraph` 다**(D9).
`--only` 로 단계를 빼면 그래프도 그만큼 작아지고, 그 작아진 그래프가 다시 보장을 통과해야 한다.

Graphviz 판(`docs/diagrams/`)은 구현 단계에서 그린다 — 지금은 흐름이 확정되지 않았다.

### 갈래 넷이 어디서 왔는지

새 어휘를 지어내지 않았다. 넷 다 지금 코드에 있는 것에 이름만 붙였다.

| 갈래 | 지금 코드 | 어디 |
|---|---|---|
| `OK` | `rows.append(ok=True)` 뒤 계속 | 세 실행기 전부 |
| `FAIL` | `break` + `"막힘 —"` | 세 실행기 전부 |
| `SKIP` | `continue` + `skipped: True` | `run_mode1.main` 의 `survey` (바뀐 파일 0개) |
| `GATE` | 루프 밖 `gate` — 실패가 아닌데 멈춘다 | `run_mode1_5.main` 의 사람 관문 |

## 범위 밖 — 이번에 하지 않는 것

- **`runner/wiki/` 와 `runner/term/` 은 손대지 않는다.** 자식 프로세스로 불리는 얼갈이
  단계이고, 이 작업은 부르는 쪽만 바꾼다
- **새 갈래를 만들지 않는다.** 위 표의 넷 고정. 좋은 아이디어가 나와도 기록만 하고 보고한다
- **Cascade 분기를 실제로 배선하지 않는다.** D4 의 Fall-Back 한 줄만 넣는다.
  나머지 전이표는 지금 동작과 1:1로 같은 값을 적는다 — 구조 변경과 동작 변경을 섞지 않는다.
  **예외는 D13 하나다**(`survey` 정적 건너뜀 제거). ①을 고치는 것이 곧 그래프를 나누는 것이라
  분리할 수 없다
- **인계 문서의 결함 ③(배치 id)과 ④(레코드 키 개명)는 고치지 않는다.** `machine/survey_plan.py`
  와 `merge_shards` 의 충돌 판정이라 별개 작업이고, 인계 문서가 이미 갈래를 적어 두었다.
  다만 **그 둘이 고쳐지기 전에는 증분 그래프를 쓰지 않는다**(순서 제약 절)
- **`machine/` 과 `viz/` 는 소유하지 않는다** (`runner/CLAUDE.md` 의 Owns 절).
  스키마도 새로 선언하지 않고 거기 있는 TypedDict 를 가져다 쓴다
- **스키마 언어를 도입하지 않는다.** JSON Schema 파일 · pydantic · 검증 데코레이터 ·
  스키마 등록기를 만들지 않는다. `check` 는 손으로 쓴 얕은 함수다 (D10)
- **형 인자를 하나 넘게 만들지 않는다.** `Stage[C]` 의 `C` 하나뿐이다. `Outcome` 이나
  `Artifact` 의 반환형까지 파이프라인 서명에 끌어올리지 않는다
- **`runner/term/` 과 `runner/wiki/` 의 `Any` 는 이번에 없애지 않는다** (D11). 얼갈이
  단계라 범위 밖이다. 세 실행기와 공통축만 0으로 만든다
- **basedpyright 로 갈아타지 않는다.** 검사기를 바꾸는 것은 이 작업의 범위가 아니다.
  `Any` 금지는 grep 게이트로 막는다 (D11)

## 위험

- **거울 함정.** 과잉 설계를 잡는 도구를 만들며 그 도구를 과잉 설계하는 것.
  경계선을 미리 긋는다 — 갈래는 넷 고정, 계층 상태(hierarchical state)·가드 함수·
  이벤트 큐·플러그인 등록기를 만들지 않는다. 그런 것이 나오면 그 자체가 이 작업이
  잡으려던 실패다
- **동작 변경이 섞여 들어가는 것.** 전이표의 값이 지금 동작과 다르면 리팩터링이 아니다.
  게이트가 이것을 잡는다 — 시험 483개가 그대로 통과해야 한다
- **D0 이 실측이 아니라 의도에 기반한다.** Fall-Back·Cascade 는 아직 소비자가 D4 하나다.
  D4 를 넣고도 두 번째 소비자가 오래 안 생기면 전이표는 `if/elif` 보다 무거운 채로 남는다

## 완료 조건 — 게이트 일곱이 전부 초록

리팩터링이므로 **숫자가 그대로여야 한다.**

| 게이트 | 명령 | 지금 |
|---|---|---|
| 파이썬 시험 | `.venv/bin/python -m pytest -q` | 483 통과 · 19 건너뜀 |
| JS 시험 | `npm test` | 8 통과 |
| TS 타입 | `npm run typecheck` | 통과 |
| 파이썬 타입 | `npm run typecheck:py` | 0 errors |
| 주석 주입 | `.venv/bin/python machine/xmldoc.py check` | 문제 0건 |
| README 표류 | `.venv/bin/python tools/gen_readme.py --check machine runner viz tools` | 4개 일치 |
| 환경 | `npm run doctor` | 필수 전부 있다 |

추가로 세 가지를 눈으로 확인한다.

1. **import 부작용이 사라졌는지** — 시스템 파이썬으로 `run_mode2` 를 import 했을 때
   `sys.prefix` 가 안 바뀌고 `networkx` 가 안 실린다
2. **`--dry-run` 출력이 세 모드 모두 이전과 같은지**
3. **`runner/CLAUDE.md` 와 `runner/README.md` 가 새 구조를 가리키는지** —
   `gen_readme.py` 게이트가 README 는 잡지만 `CLAUDE.md` 는 안 잡는다. 손으로 고친다
4. **`cast` 가 줄었는지** — 스키마를 **주장하는** `cast` 가 0건이어야 한다.
   `isinstance` 뒤에 붙는 좁히기 `cast` 는 남는다 (D11 의 표)
5. **`Any` 가 0인지** — 새 게이트 `test/test_no_any.py` 가 세 실행기와 공통축에서
   형 자리의 `Any` 를 0으로 확인한다. 지금 24곳이다
6. **팩토리가 어긋난 그래프를 실제로 거부하는지** — 시험에서 일부러 망가뜨린 그래프
   다섯(간선 빠짐 · 고아 단계 · 어떤 경로에서만 없는 산출물 · 매달린 경로 · 순환)을
   넣어 `build_graph` 가 **단계를 하나도 돌리지 않고** 죽는지 본다
7. **`--dry-run` 이 그래프를 찍는지** — 폴백 간선이 화면에 보여야 한다. 앞선 판의
   반대 근거가 여기서 해소된다 (D9)
