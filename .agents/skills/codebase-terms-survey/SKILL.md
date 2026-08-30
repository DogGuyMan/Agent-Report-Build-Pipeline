---
name: codebase-terms-survey
description: Use when a repository needs a machine-checkable term dictionary (terms-reading.json → terms-db.json → codegraph.json projection) for report-builder Mode 1 — "전수조사", "코드베이스 용어 사전", "terms-reading.json 만들어", "terms-db 갱신", "codebase terms survey", or before Mode 1.5 (term-benchmark) / Mode 2 (spec-review-dashboard) can run on a Plan for that codebase. One LLM reading pass writes per-symbol records (meaning · behavior · relations · file:line) that terms_db.py verifies (L1/L2/L3) and projects into a code map. Borrows wiki-researcher's evidence discipline without its prose output.
---

# Codebase Terms Survey (Mode 1 — 전수조사)

## 한 줄 요약

코드베이스를 **한 번** 읽어 낱말마다 `{뜻, 동작, 관계, 위치}` 레코드를 쓴다. 뜻은 사람(LLM)이 쓰고, 위치는 기계가 검사하고, 코드 지도는 거기서 투영된다.
**"객관과 주관을 섞지 않는다"** — 읽은 것과 추론한 것을 레코드 단위로 가른다.

## When to use

- 어떤 저장소의 Plan/Spec 을 Mode 1.5(용어 시험)·Mode 2(설계 검토)로 돌리려는데 그 코드베이스의 `terms-db.json` 이 없을 때
- 코드가 많이 바뀌어 `terms-reading.json` 이 낡았을 때(증분 재조사)
- 정적 수집기(roslyn · clang-uml)가 없는 언어(Python · JS/TS 등)의 저장소 — 이 스킬만이 코드 지도를 만든다

**쓰지 않는 때** — 위키 산문이 필요할 때(그건 deep-wiki), 설계 판정이 필요할 때(그건 Mode 2). 이 스킬은 **판정하지 않는다** — 사실을 적고 인용을 붙인다.

## 전제 — 하나라도 없으면 착수하지 않는다

| 전제 | 확인 | 없을 때 |
|---|---|---|
| report-builder | `ls $REPO_ROOT/machine/terms_db.py` | 중단. 경로를 지어내지 않는다 |
| 대상 저장소 경로 `<repo>` | `git -C <repo> rev-parse --show-toplevel` | 사용자에게 묻는다 |
| **작업 트리가 조용한가** | `git -C <repo> status --porcelain` 에 소스 변경이 없어야 한다 | **중단.** 남이 파일을 고치는 중이면 `where`(줄 번호)가 움직이는 과녁이 된다 — 2026-08-29 실측: 병렬 세션의 주석 주입 중에 조사해 실패 7 · 근거 없음 121 |
| (선택) 정적 `codegraph.json` | `<repo>/out/codegraph-raw/codegraph.json` | 없으면 읽기 레코드만으로 만든다 — 정상 |

## 레코드 계약 — 이것이 산출물이다

`<repo>/docs/machine/terms-reading.json` (git 추적). 꼴은 `{ "키": 레코드 }`.

```json
{ "build_terms": {
    "kind": "function", "module": "codegraph", "where": "machine/terms_db.py:82",
    "means": "코드 지도에서 용어 사전을 만드는 함수.",
    "does": "노드와 모듈을 돌며 이름 · 종류 · 위치 · 관계를 뽑는다. 입력이 같으면 출력도 같다.",
    "uses": [ { "to": "_where", "kind": "dependency", "label": "calls", "where": "machine/terms_db.py:110" } ],
    "confidence": "HIGH",
    "source": "reading" } }
```

| 칸 | 값 | 규칙 |
|---|---|---|
| 키 | 파일은 파일명(`normalize.py`), 함수·클래스는 맨 이름, **다른 파일과 겹치면 겹친 전원** `<파일줄기>.<이름>`, 파일명이 겹치면 경로 전체 | Mode 1.5 가 이 키를 Plan 본문에서 낱말 경계로 찾는다 — Plan 의 표기와 글자까지 같아야 한다 |
| `kind` | `file module function class struct enum interface delegate record external artifact key concept` | `file module artifact key concept` 는 지도의 노드가 되지 않는다 |
| `module` | **디렉토리** (`codegraph`, `scripts/term`) | |
| `where` | `경로:줄`. 파일은 `:1`, 함수·클래스는 선언 줄, 산출물은 그 파일을 **쓰는** 줄, 키는 그 키를 **채우는** 줄, 개념은 그 낱말이 있는 줄 | `module` `external` 빼고 **필수.** 기계가 L1(파일) L2(줄) L3(근처에 이름) 로 검사 |
| `means` | 무엇인가 — 한 문장 | **객체지향을 갓 배운 대학 1학년 눈높이.** 다른 어려운 용어로 설명하지 않는다 |
| `does` | 무엇을 하는가 — 한두 문장. 선택 | 누가 언제 불러 무엇이 되는지까지 쓰면 좋다(아래 렌즈) |
| `uses[]` | 부르거나 · import 하거나 · 쓰는 대상. `kind` ∈ `dependency inheritance aggregation composition association realization`, `label` 에 이유(`calls` `imports` `writes`), `where` 는 그 자리 | `to` 는 사전에 있는 키여야 한다 |
| **`confidence`** | `HIGH` 코드를 읽고 썼다 / `MEDIUM` 일부 읽고 나머지는 추론 / `LOW` 이름·구조에서 추론 | **레코드마다 필수.** `wiki-researcher` 에서 이식. 검사기는 이 칸을 읽지 않는다 — 사람과 Mode 2 가 읽는다 |
| `source` | `reading` (LLM) · `codegraph` (정적) · `codegraph+reading` (합침) | 기계가 채운다 |
| `neighbors` | **쓰지 않는다** — 기계가 `uses` 양방향에서 다시 센다 | |

## 규율 — 객관과 주관을 섞지 않는다 (non-negotiable)

### 금지 표 — 이 말이 떠오르면 멈추고 읽는다 (`wiki-researcher` 이식)

| 떠오른 문장 | 해야 할 것 |
|---|---|
| "이건 아마 …를 처리할 것이다" | **금지.** 그 함수를 열어 실제로 무엇을 하는지 적는다 |
| "이름으로 보아 …" | **부족.** 이름은 거짓말한다. 구현을 확인한다 |
| "보통 이런 건 …와 비슷하다" | **금지.** 이 코드베이스를 읽는다. 관례에 대지 않는다 |
| "…에 연결될 것 같다" | **금지.** import 나 호출을 실제로 따라간다 |
| "읽지 않았지만 …" | `confidence: LOW` 로 적거나, 아예 쓰지 않는다. 확신에 찬 미지는 없다 |

### 증거 기준표 — 주장마다 요구되는 증거

| 주장 | 필요한 증거 (`where` 에 남긴다) |
|---|---|
| "X 가 Y 를 부른다" (`uses` dependency) | 호출 줄 `파일:줄` |
| "X 는 Y 를 상속한다" | 선언 줄의 `extends`/`:` |
| "이 파일이 Z 를 만든다" (artifact) | `json.dump` · `writeFileSync` 가 있는 줄 |
| "이 키를 채운다" (key) | 그 키에 값을 넣는 줄 |
| "이건 진입점이다" | 어디서 불리는지(`bin/*` · `main` 가드 · 등록 줄) |
| "이건 죽은 코드다" | 호출처가 0건임을 grep 으로 |

- **코드에 글자로 없는 것은 쓰지 않는다.** Plan 이 만든 결정 코드(`C-20`)나 개념(`무효화`)이 코드에 없으면 Mode 1.5 의 신규 개념으로 남긴다. 검사기 주석의 **예시 문자열**(`"C-19"`)을 개념으로 싣지 않는다 — 2026-08-29 첫 시험에서 그런 항목 3개는 전부 "모른다" 를 받았다.
- **LLM 추론은 한 번이다.** 위키·요약을 따로 쓰지 않는다. 필요하면 이 레코드에서 파생한다.
- **증분 재조사에서는 기존 레코드의 `means` `does` 를 바꾸지 않는다** — Mode 1.5 정답지로 이미 쓰였다. 고치는 것은 낡은 `where`, 새 레코드, 지워진 레코드.

## Workflow — 10단계

1. **전제 확인** (위 표). 트리가 조용한지 반드시 본다.
2. **대상 파일 고정** — 결과가 조사 범위다. 보고에 그대로 붙인다.
   ```bash
   cd <repo> && find <소스 디렉토리들> -type f \( -name "*.py" -o -name "*.mjs" -o -name "*.ts" -o -name "*.tsx" -o -name "*.cs" -o -name "*.cpp" -o -name "*.h" \) \
     -not -name "test_*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" | sort
   ```
3. **(정적 수집기가 있으면) 먼저 codegraph 로 레코드를 만든다** — `terms_db.py <codegraph.json> --repo <repo>` 가 클래스·모듈 레코드를 정형문으로 낸다. 읽기 레코드는 그 위에 **뜻·동작·새 관계만** 보탠다. 구조 칸(`id kind module where`)은 codegraph 가 이긴다.
4. **선언과 문서 주석을 먼저 뽑는다** — `machine/declmap.py` 가 선언 한 줄과 **그 위에 붙은
   문서 주석**만 낸다. 저자가 쓴 의도라 이름 추론보다 근거가 낫고, 읽을 자리를 좁혀 준다.
   ```bash
   python machine/declmap.py <repo> --lang cs --include Assets/@Scripts    # cs · cpp · py · ts
   ```
   🔵 2026-08-29 실측 — 소스를 전량 정독하면 **1줄당 96토큰**, 이 방식으로 좁혀 읽으면
   **1줄당 33토큰**이었다(QtVisionEdit 2,982줄 vs StickRush 8,164줄). 약 3배.

   **그래도 정독을 없애지는 않는다.** 척추(진입점 · 상태 기계 · 뼈대 클래스 · 데이터 계약)는
   반드시 연다. 목록만 보고 쓴 레코드는 `confidence: LOW`, 문서 주석을 요약한 것은 `MEDIUM`,
   실제로 읽은 것만 `HIGH` 다. **싸진 만큼 확신도가 낮아진다는 사실을 칸으로 드러낸다.**

5. **배치 계획을 만든다** — `python machine/survey_plan.py <codegraph.json> --target 8`
   → `survey-plan.json`. 층0(의존 대상이 없는 것)부터 층이 오른다.
   재료는 조사 **이전에** 있다 — `report-wiki prep` 이 정적 수집기로 코드 지도를 먼저 낸다.
   수집기가 없는 저장소는 `prep` 이 막히므로 애초에 Mode 1 대상이 아니다. 그때는 함께 막고 보고한다.
   증분 재조사면 `warmup.py blast` 의 파일 목록을 `--only-files` 로 준다.
6. **레코드를 쓴다 — 층 오름차순, 층 안은 병렬.**
   - 층 사이는 **순차**. 층 k 는 층 <k 가 전부 끝나고 병합된 뒤 시작한다.
   - 층 안은 **배치 8개까지 동시**. 같은 층끼리는 서로 의존하지 않으므로 안전하다.
   - 배치는 자기 샤드 `<repo>/out/codegraph-raw/_shards/L{층}-B{번호}.json` 에만 쓴다.
     **terms-reading.json 을 직접 고치지 않는다** — 동시에 여러 배치가 돌기 때문이다.
   - 층이 끝나면 오케스트레이터(`run_mode1.py` 의 `merge_shards`)가 샤드를 병합한다.
     **키 충돌 해소는 거기서만 한다** — 배치는 자기 것만 보므로 `main` 이 9파일에 있다는 것을 모른다.
   - 층 k 배치에는 **자기 심볼이 의존하는 아래층 레코드만** 발췌해 준다. 전량 주입은 낭비다.
   - 같은 파일을 층마다 다시 열지 않도록 `file_cache.py` 를 쓴다. 다만 **자기 심볼은 캐시로
     때우지 않는다** — 캐시만 보고 쓰면 `confidence` 가 HIGH 일 근거가 없다.
   - 레코드마다 `confidence` 를 반드시 적는다. 위 계약과 규율대로.
7. **비노드 용어는 맨 마지막 층** — file · module · artifact · key · concept.
   심볼이 전부 읽힌 뒤라야 파일 레코드가 그 안 심볼들의 완성 레코드를 재료로 쓸 수 있다.
8. **(선택) 모듈당 구조 렌즈 1회** — `uses` 를 보강한다. 모듈 하나를 골라 **진입점에서 호출 사슬을 끝까지** 따라가며(A→B→C) 빠진 `uses` 를 채운다. 5렌즈 전부는 하지 않는다(산문이 필요한 게 아니다). 사슬을 따라가다 **읽지 않은 파일**이 나오면 아래 10 의 목록에 적는다.
9. **검사** — 실패 0 이 될 때까지 `where` 를 고친다. 근거 없음은 사유와 함께 남긴다.
   ```bash
   cd $REPO_ROOT && .venv/bin/python machine/terms_db.py --repo <repo> --reading <repo>/docs/machine/terms-reading.json
   #   -> <repo>/out/codegraph-raw/terms-db.json + codegraph.json.  마지막 줄 "실패 0"
   #   정적 codegraph 도 있으면:  terms_db.py <codegraph.json> --repo <repo> --reading <…json>  -> "투영에 없는 것 0개" 까지
   ```
10. **보고** — 레코드 수(종류별) · 검사 출력 · 근거 없음 목록과 이유 · 키 충돌 목록 · **`confidence` 분포(HIGH/MEDIUM/LOW 수)** · **탐색 안 한 것**(Explored ✅ / Partial 🔶 / Unexplored ❓ — 범위 안인데 안 읽은 파일, 사슬이 끊긴 자리) · (있으면) Mode 1.5 `collect` 의 known 수.

## 착수 조건으로 남긴 측정 — "빠진 간선이 몇인가" (아직 도구 없음)

`uses` 가 얼마나 빠졌는지 **재는 도구가 없다.** 정적 codegraph 가 있는 저장소(StickRush)에서 **LLM 이 적은 `uses` ∩ 정적 간선** 을 세면 recall(정적 간선 중 LLM 이 잡은 비율)·precision(LLM 간선 중 정적에 있는 비율)이 숫자로 나온다.
구현 자리는 `terms_db.py` 의 codegraph+reading 경로(지금은 노드 상위집합만 대조한다) — **작업 트리가 깨끗해지면** 넣는다(2026-08-29 현재 다른 세션이 `codegraph/*.py` 를 고치는 중). 그 숫자가 나오기 전에는 "렌즈 1회로 `uses` 가 좋아졌다" 고 **주장하지 않는다.**

## C++ 저장소의 함정 — 2026-08-29 실측

| 함정 | 무엇이 일어나나 | 막는 법 |
|---|---|---|
| **CMake 타깃 트리가 여럿** | 루트 compdb 만 쓰면 별도로 짓는 타깃이 통째로 빠진다. QtVisionEdit 은 1차 클래스 61개 중 **37개(app)** 가 이렇게 빠졌다 | `report-wiki prep` 이 저장소 안 `compile_commands.json` 을 **전부 찾아 합친다**(`runner/wiki/compdb.mjs`) |
| **clang-uml 글로브가 깊이 4에서 죽는다** | `app/src/view/*.cpp` 에서 `regular expression complexity exceeded`. 같은 파일을 하나씩 적으면 통과한다 | 생성 설정이 **파일을 열거**한다. 글로브를 쓰지 않는다 |
| **남의 타입이 1차로 샌다** | `source_location` 이 남의 헤더가 아니라 **이 저장소의 첫 사용 지점**을 가리킨다(F-1). `QWidget` 이 PageRank 1위로 올라온 적이 있다 | `normalize.py` 가 세 겹으로 막는다 — std 계열 이름 · 빌드 산출물 경로 · **그 줄이 실제로 정의하는가**(전방 선언 `class QWidget;` 과 사용 줄을 뺀다) |
| **네임스페이스 없는 코드** | `CPP_FIRST_PARTY_NS` 만 보면 전역 네임스페이스를 쓰는 모듈이 통째로 외부가 된다 | 허용목록에 없으면 **선언 위치**로 판정한다(위 세 겹을 통과할 때만) |

## Common pitfalls

- **움직이는 트리에서 조사** — 병렬 세션이 파일을 고치면 줄 번호가 밀린다. 전제 3 을 건너뛰지 않는다
- **인용 부패** — 코드가 바뀌면 `where` 는 낡는다(L3 근거 없음이 는다). `xmldoc.py inject` 가 마커 기준으로 재계산한다 — 셈으로 추정하는 방식은 앞선 블록의 누적 밀림을 놓친다(2026-08-29 실측: 근거 없음 3 → 242). `uses[].where` 는 재계산되지 않는다
- **키 충돌을 한쪽만 한정** — `main` 이 9파일이면 9개 전부 `<파일줄기>.main`
- **파일 레코드의 `where`** 는 `경로:1` — 머리 주석에 파일명이 없으면 근거 없음이 뜬다. 정보성이다. 파일에 머리 주석을 다는 것이 정답이지 규칙을 바꾸는 것이 아니다
- **범위 밖 파일을 `does` 에서 언급** — 그 파일의 레코드가 없으면 독자가 따라갈 수 없다. 범위에 넣거나 언급을 뺀다
- **`confidence` 를 전부 HIGH 로** — 그러면 칸이 장식이다. 이름만 보고 쓴 것은 LOW 다
- **out_deg 로 정렬** — 그건 위상 깊이가 아니다. 🔵 실측에서 out_deg 1 무리 안에 깊이 1·2·3·4 가
  섞여 있었다. out_deg 로 나누면 아직 안 읽은 것을 가리키게 된다
- **층 경계에서 같은 파일을 다시 통독** — 🔵 유일 파일 41개인데 층별 합계 84개다. `file_cache.py` 를 쓴다
- **배치가 terms-reading.json 을 직접 고침** — 동시 쓰기로 서로를 지운다. 샤드에만 쓴다

## 개발 규율 — 코드를 만들 때 레코드도 함께 (사용자 의도, 2026-08-29)

이 사전의 목적은 **나중 LLM 이 코드를 다시 추론하는 부담을 줄이는 것**이다. 그래서 전수조사는 한 번이고, 그 뒤로는 **개발하면서** 채운다:

- 새 함수·파일·산출물·키를 만들면 **그 자리에서 레코드를 쓴다** — 뜻 · 동작 · `uses` · `confidence`. 생각한 것(왜 이렇게 했는가)은 `does` 에 한 문장.
- `machine/xmldoc.py emit` → `inject` 로 코드 옆에 **주석 블록**(마커 · 한 줄 뜻 · 의존 줄 "쓰는 것 / 쓰이는 곳")을 박는다. 코드에는 레퍼런스만, 본문은 `comments.xml` 한 곳 — 두 군데 살면 어긋난다.
- 코드가 움직여 줄 번호가 밀리면 `inject` 가 **마커 기준으로 `where` 를 재계산**한다(2026-08-29 ⑭ 이후). `uses[].where` 는 마커가 없어 L3 경고로만 남는다.
- 검사 둘을 같이 본다 — `terms_db.py --reading`(L1/L2/L3) · `xmldoc.py check`(마커와 json 이 맞는가).

## deep-wiki 산문도 같은 층 순서로 (K6)

위키 페이지는 심볼도 모듈도 아닌 **주제** 단위다(Getting Started / Deep Dive, 최대 4단, 절당 ≤8장).
그래서 **페이지의 층 = 그 페이지가 인용하는 심볼들의 최대 층**으로 매긴다.
왜 최대인가 — 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신 링크할 수 있다.

목차는 기계가 만들지 못한다(주제 단위라서). 그래서 `wiki` 단계는 **목차 세션 1개**로 시작해
`wiki-plan.json` 을 받고, 거기 적힌 페이지별 인용 심볼로 층을 매긴 뒤 장을 층 순서로 쓴다.

**deep-wiki 플러그인 파일을 고치지 않는다.** `~/.claude/plugins/cache/` 에 사는 캐시라 업데이트에
덮인다. 우리 프롬프트(`run_mode1.py` 의 `wiki_page_prompt`)가 감싸서 지시한다.

**서브에이전트 모형은 `claude-sonnet-5` 다.** 오케스트레이터가 `--model` 로 박아 넣는다.

## 산출물

| 파일 | 누가 | 어디로 |
|---|---|---|
| `<repo>/docs/machine/terms-reading.json` | 이 스킬(LLM) | git 추적 — 원본 |
| `<repo>/docs/machine/comments.xml` · 소스의 주석 블록 | `xmldoc.py emit` / `inject` | git 추적 — 파생물. 손으로 고치지 않는다 |
| `<repo>/out/codegraph-raw/terms-db.json` | `terms_db.py` | Mode 1.5 `report-term collect` 의 재료. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/codegraph.json` | `terms_db.py` (투영) | `verify_citations.py` · 다이어그램 · Mode 2. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/survey-plan.json` | `survey_plan.py` | 층·배치 계획. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/_shards/*.json` | 배치 세션 | 배치별 레코드 조각. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/_filecache/*.json` | 배치 세션 | 통독 캐시. gitignore, 재생성 |

## 아직 재어 보지 않은 것

- `uses` 누락률 — 위 측정 도구가 없다. 첫 숫자가 나오면 이 절을 고친다
- `confidence` 분포가 실제 뜻의 정확도와 맞는지 — Mode 1.5 시험(C1: 오답 보기가 헐거우면 정답률이 100% 로 몰린다)이 간접 지표다
- 렌즈 1회의 비용 대비 이득 — 표본 0
