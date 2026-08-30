# codegraph/ — 파이썬 파이프라인

> 루트 나침반은 `../CLAUDE.md`. 이 문서는 **파이썬 쪽만** 다룬다.
> Node 배선은 `../scripts/CLAUDE.md`, 컴포넌트는 `../src/CLAUDE.md`.

이 저장소에서 가장 큰 모듈이다(파이썬 30파일). **정적 수집 · 인용 검증 · 측정**을 맡는다.
산문을 쓰지 않고 판정하지 않는다 — 기계가 아는 사실만 결정론으로 낸다.

## 무엇이 여기 있나

| 파일 | 하는 일 |
|---|---|
| `normalize.py` | 수집기 출력을 코드 지도(`codegraph.json`)로 정규화. **C++ 과 C# 두 경로가 한 파일에 있다** |
| `declmap.py` | 소스에서 선언 목록을 훑는다. 언어 넷(`cpp` `cs` `py` `ts`) |
| `clang_doc.py` | `clang-doc` 의 흩어진 JSON 을 평평한 심볼 목록으로 |
| `facts.py` · `render_modules.py` · `render_classes.py` | 사람이 읽는 사실 표 · 모듈 관계도 SVG |
| `terms_db.py` | 용어 사전 병합과 **인용 검사 L1/L2/L3**. 투영이 코드 지도를 덮는다 |
| `verify_citations.py` | 위키 산문의 `파일:줄` 인용을 3값으로 판정 |
| `xmldoc.py` | 주석 본문을 `comments.xml` 한 곳에 모으고 소스에는 레퍼런스만 남긴다 |
| `warmup.py` | 전수조사 증분 캐시 — 무엇을 다시 읽어야 하는지 가려낸다 |
| `survey_plan.py` | 코드 지도를 의존 위상 층과 배치로 나눈다. **판정하지 않는다** |
| `file_cache.py` | 층 경계에서 같은 파일을 다시 통독하지 않도록 개요를 디스크에 남긴다 |
| `run_mode1.py` · `run_mode1_5.py` · `run_mode2.py` | 세 mode 실행기. **단계마다 시간·토큰을 잰다** |
| `demermaid.py` | Mermaid 를 사전 렌더 SVG 로 |

## 세 실행기 — 재는 것이 목적이다

자동화는 수단이고, 목적은 **단계마다 벽시계 시간과 토큰을 붙들어 표로 내는 것**이다.

```
Mode 1    prep ─▶ warmup ─▶ survey-plan ─▶ survey ─▶ warmup-save ─▶ terms ─▶ wiki ─▶ build ─▶ check
#                              ↑ 기계(survey_plan.py)   ↑ LLM 층별
Mode 1.5  collect ─▶ author ─▶ [사람 차례] ─▶ grade ─▶ emit
Mode 2    init ─▶ agent ─▶ build ─▶ check
```

🔵 2026-08-30 실측 — **세 mode 모두 LLM 한 칸이 전체 시간의 99%** 를 쓴다.
Mode 1 냉시동은 27분 08초 중 에이전트가 26분 53초(99.1%) · 17,925,770 토큰 · $15.4991 · 84턴.
그중 **캐시읽기가 97.3%** 다 — `usage` 의 캐시 둘을 빼고 더하면 실제의 일부만 세게 된다.

**측정 코드는 `run_mode1.py` 한 곳에 있고 나머지 둘이 import 한다.** 재구현하지 마라.

## 전수조사 레코드 — 코드를 쓰면 레코드도 쓴다

절차의 정본은 **`codebase-terms-survey` 스킬**이다(저장소 사본 `.agents/skills/`).
여기서는 규약만 적는다:

- 원본은 `<repo>/docs/codegraph/terms-reading.json`. 꼴은 `{키: 레코드}`
- 레코드 계약 `{kind, module, where, means, does, uses[], confidence, source}`
- **`where` 는 실제 `파일:줄`** — `terms_db.py` 가 L1(파일) L2(줄) L3(근처에 그 이름) 로 검사한다
- `kind` 가 `file` `artifact` `key` `concept` `module` 이면 **이름이 그 줄에 글자 그대로** 있어야 한다
  (`terms_db.py` 의 `_stem` — `codegraph.json` 을 `.` 로 쪼개면 안 되기 때문)
- 새 함수를 만들면 그 자리에서 레코드를 쓰고 `xmldoc.py emit` → `inject` 로 주석 블록을 박는다
- 코드가 움직여 줄이 밀리면 `inject` 가 **마커 기준으로** `where` 를 다시 센다.
  `uses[].where` 는 마커가 없어 재계산되지 않는다(L3 경고로 남는다)

## warmup 의 판정 네 갈래 — 그리고 알려진 구멍

| 파일 해시 | 선언 해시 | 판정 | 해야 할 일 |
|---|---|---|---|
| 같음 | — | `유효` | 아무것도 안 한다 |
| 다름 | 같음 | `위치만` | 좌표만 고친다 |
| 다름 | 다름 | `재읽기` | 그 파일만 다시 읽는다 |
| git 이 모름 | — | `삭제됨` | 사람이 정한다 |

⚠ **`위치만` 이 본문 재작성까지 삼킨다.** `decl_hash` 가 `(kind, name)` 만 해싱하므로
(`warmup.py` 의 `decl_hash`) 함수 본문을 통째로 다시 써도 선언 이름이 같으면 `위치만` 이다.
🔵 2026-08-30 실측으로 확인했다. **그래서 에이전트에 먹일 목록은 `재읽기` 가 아니라
`blast_radius(재읽기 ∪ 위치만)` 이어야 한다** — `warmup.py` 의 CLI 도 그렇게 한다.

**2026-08-30 에 배선됐다**(`1e5d766`). `run_mode1.py` 의 단계가 일곱이 되면서 `warmup`(판정만)과
`warmup-save`(확정)가 `agent` 앞뒤에 붙었다. **둘로 가른 것이 급소다** — 한 칸이면 에이전트가 실패해도
그 파일이 `유효` 로 기록되어 읽지 않은 파일이 읽은 것으로 남는다. 씨앗은 `changed_seed` 가 만들고
위 경고대로 `재읽기 ∪ 위치만` 이다. 판정을 못 하면 옛 동작인 전량 조사로 되돌아가고, 대조군은
`--skip warmup,warmup-save` 로 만든다.

계획서는 `../docs/superpowers/plans/2026-08-30-warmup-mode1-wiring.md` 다. **Task 9(실측 대조)만 미실행** —
국소 변경을 준 증분 실행의 절감폭은 아직 숫자가 없다.

## Bottom-Up 층 병렬 — 2026-08-30 에 뒤집힌 결정

이 문서의 이전 판과 `run_mode1.py` 는 **"에이전트를 하나로 묶은 것이 이 설계의 급소"** 라고
적고 있었다. 이유는 캐시였다. **사용자가 2026-08-30 에 그 결정을 뒤집었다.**
`agent` 한 칸이 `survey`(전수조사)와 `wiki`(산문) 둘로 갈리고, 각각 **층 오름차순으로 여러
세션**을 띄운다. `warmup-save` 는 **레코드를 만드는 `survey` 바로 뒤**에 있다 — `wiki` 뒤에
두면 산문 실패가 다음 실행의 전량 재조사를 부른다.

| # | 결정 |
|---|---|
**⚠ 간선 방향** — `codegraph.json` 의 `{from: A, to: B}` 는 **"A 가 B 에 의존"** 이다
(레코드의 `uses[].to` 가 그대로 `to` 다). 🔵 2026-08-30 실측 — 105건 전부 이 방향, 반대 0건.
그러므로 **`out_deg` = 내가 끌어오는 수**(0이면 층0, 여기서 시작), **`in_deg` = 남이 나를
끌어가는 수**(0이면 진입점, 맨 나중). 🔵 층0(110개) 평균 out_deg 0.00 · 층3(7개) 3.14.
**`in_deg` 0 부터 시작하면 top-down 이 되어 이 도구가 막으려는 사고가 그대로 난다** —
`main` 이 부르는 것들이 아직 안 읽힌 채로 `main` 의 뜻을 적게 된다.

| K1 | 정렬 축은 **위상 깊이**. 🔵 out_deg 로는 안 된다 — 이 저장소 실측에서 out_deg 1 무리(31개)와 2 무리(15개) 안에 깊이 1·2·3·4 가 전부 섞여 있었다. 의존 하나만 가져도 그 하나가 3층이면 4층이다 |
| — | 층 매기기는 **기계**다(`survey_plan.py`). `survey-plan` 이 `STAGES` 에서 자기 칸을 갖는 이유 — 한 칸에 묶으면 층 오름차순이 모형의 판단처럼 읽힌다 |
| K2 | 층 안은 병렬, 층 사이는 순차 |
| K3 · K4 | 배치는 8심볼, 한 층에 동시 8배치 |
| K5 | 비노드 용어(file · module · artifact · key · concept)는 맨 마지막 별도 층 |
| K6 | 위키도 같은 층 순서. 페이지의 층 = 인용하는 심볼의 최대 층 |
| K7 | 고립 노드는 층0 |
| K8 | 성공 판정은 **벽시계만.** 토큰·비용 증가는 허용하되 기록한다 |

**서브에이전트 모형은 `claude-sonnet-5` 다.** `main` 의 `--model` 기본값 하나가
`run_survey`/`run_wiki` → `run_layer` → `run_agent_with` → `claude_argv` 사슬을 타고 내려간다.
별명(`sonnet`)이 아니라 정확한 ID 를 쓴다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.

**파일 lock 은 걸지 않는다. 필요가 없다.** 배타성이 lock 이 아니라 `survey_plan.pack()` 에서
나온다 — 같은 파일의 심볼을 한 배치에 몰아넣으므로 한 층 안에서 두 배치가 같은 파일을
가리키지 않는다. 층 사이는 순차라 시간상 겹치지도 않는다. 🔵 2026-08-30 두 저장소에서
층 안 파일 중복 0건을 확인했다.

**비용은 아직 재지 않았다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다.
어느 쪽이 큰지 **모른다** — `--json` 으로 A/B 를 돌려 `evals/runs/` 에 쌓고 대조한다.
기준선은 **opus 한 세션**이라 모형까지 다르다. **"층 병렬 덕분" 이라고 귀속할 수 없다.**

🔵 2026-08-30 이 저장소 실측 — 1차 노드 167개의 층 분포는 **0:110 · 1:32 · 2:16 · 3:7 · 4:2**,
순환 0개, 고립 노드 42개. 층 경계 중복 통독은 유일 파일 41개에 층별 합계 84개(**중복 43회**)다.

⚠ **`merge_shards` 에는 누적본이 아니라 조사 이전의 원본을 준다.** 층마다 불리며 샤드를
전부 다시 읽으므로, 누적본을 주면 이미 합친 레코드를 자기 자신과의 충돌로 보고 개명한다 —
🔵 연기 시험에서 레코드 수가 38 → 27 로 줄어드는 것으로 드러났다.

## 경로 변수 — 문서와 테스트가 쓰는 이름

**이 저장소는 공개된다. 기계마다 다른 경로를 문서·코드·커밋에 그대로 적지 않는다.**
어느 머신에서 읽어도 뜻이 통하도록 변수 이름을 쓴다.

| 변수 | 가리키는 곳 | 값이 없으면 |
|---|---|---|
| `REPORT_PYTHON` | 쓸 파이썬 해석기 | 저장소 안 `.venv` → PATH 의 `python3` 순으로 찾는다 (`scripts/python.mjs`) |
| `$REPO_ROOT` | 이 저장소 | 문서 표기 전용 — 동작에 영향 없음 |
| `$TOOLS_ROOT` · `$DEV_ROOT` | 개인 작업 폴더 두 곳 | 같음 |
| `$GRAPHICS_REPO` | C++ 골든 저장소 (clang-uml 표본) | **골든 테스트 15개가 건너뛴다.** 실패가 아니다 |
| `$CSHARP_REPO` | C# 골든 저장소 (StickRushGame) | 같음 |
| `$CPP_REPO` | C++ 위키 대상 (QtVisionEdit) | 문서 표기 전용 |

```bash
# 각자 자기 경로로. ~/.zshrc 에 넣으면 골든 테스트까지 돈다.
export GRAPHICS_REPO="$HOME/<...>/GlobalMedia-OpenGL-ComputerGraphics"
export CSHARP_REPO="$HOME/<...>/StickRushGame"
```

🔵 2026-08-30 실측 — 변수 없이 `pytest codegraph/` 는 **201 통과 · 19 건너뜀**,
`$GRAPHICS_REPO` 와 `$CSHARP_REPO` 를 주면 **205 통과 · 15 건너뜀**이다.
남는 15개는 `$CPP_REPO` 쪽 골든이라 그 저장소가 있어야 돈다. **건너뜀은 실패가 아니다.**

**함정.** 골든 경로 상수는 값이 없을 때 빈 문자열이 되면 안 된다. `os.path.join("", "out/…")` 이
**상대경로**가 되어 이 저장소의 산출물을 골든으로 착각해 읽는다(실제로 겪었다). 그래서
`… or "/골든저장소_미지정/<변수>"` 로 절대 존재할 수 없는 경로를 준다.

`data.ts` 의 `linkRoots` 도 같은 규약을 쓴다 — `scripts/link-paths.mjs` 의 `expandRoot()` 가
`$VAR` 와 `~` 를 편다. 변수가 없는 독자에게는 그 링크만 조용히 안 걸린다.

**새 문서에도 이 규약을 쓴다** — 홈 아래 경로를 적을 일이 생기면 위 변수 중 하나로 적는다.

**코드에도 경로를 박지 않는다.** 파이썬 해석기는 `scripts/python.mjs` 의 `pythonPath()` 로 찾고,
바깥 명령(`git` · `dot` · `clang-uml` · `dotnet` · `clangd` · `mmdc`)은 PATH 로 부른다.
새 기계에서 무엇이 빠졌는지는 **`npm run doctor`** 가 한 화면으로 말한다 — 필수가 없으면 exit 1.
파이썬 의존성은 `requirements.txt` 에 있다(🔵 실측 — `networkx` `numpy` `scipy` `pytest` 넷이면 전량이 돈다).
설치 절차는 `README.md` 에 있다.

## 검증

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest codegraph/ -q          # 골든 변수가 없으면 일부 건너뛴다
.venv/bin/python codegraph/xmldoc.py check        # 마커와 json 이 맞는가
.venv/bin/python codegraph/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading docs/codegraph/terms-reading.json
#   기대: 실패 0. "근거 없음" 은 경고이지 실패가 아니다
```

**파이썬 의존성은 넷이면 전량이 돈다** — `networkx` `numpy` `scipy` `pytest`
(`requirements.txt`). 표준 라이브러리로 풀 수 있으면 새 의존성을 더하지 마라.

## 이 모듈이 소유하는 것 (Owns)

`codegraph/**` 전부와 `docs/codegraph/terms-reading.json`(전수조사 원본), 그리고
`out/codegraph-raw/**`(재생성 대상이라 판 관리 밖). **소유하지 않는 것** — `src/*` ·
`scripts/build.mjs` · `scripts/check.mjs` 는 Mode 2 의 것이라 읽기만 한다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `scripts/wiki/*.mjs` → 여기 | `prep` 이 `normalize.py` · `facts.py` · `render_modules.py` 를 자식 프로세스로 부른다 |
| `scripts/wiki/check.mjs` → 여기 | `verify_citations.py` 를 부른다 |
| `scripts/wiki/build.mjs` → 여기 | `demermaid.py` 를 부른다 |
| 여기 → `scripts/*` | `run_mode*.py` 가 `node scripts/…mjs` 를 부른다 (**되돌아오는 방향**) |
| 여기 → `src/*` | **없다.** 파이썬은 컴포넌트를 모른다 |

⚠ **`normalize.py` 의 출력 키는 간접 의존이다.** `terms_db.py` 가 `from`/`to` · `id`/`depends_on`
를 읽는다. 코드에 명시돼 있지 않아 바꾸면 조용히 깨진다. 키를 바꾸는 변경이면 멈추고 보고한다.

## 흔한 변경 패턴 (Common modification patterns)

```bash
# 새 함수를 더했다 — 레코드도 그 자리에서 쓴다
$EDITOR docs/codegraph/terms-reading.json     # {kind, module, where, means, does, uses[], confidence}
.venv/bin/python codegraph/xmldoc.py emit && .venv/bin/python codegraph/xmldoc.py inject
.venv/bin/python codegraph/xmldoc.py check    # 기대: 문제 0건

# 코드를 옮겨 줄이 밀렸다 — inject 가 마커 기준으로 다시 센다
.venv/bin/python codegraph/xmldoc.py inject

# 수집기 출력이 바뀌었다 — 골든 시험부터 본다
GRAPHICS_REPO=... CSHARP_REPO=... .venv/bin/python -m pytest codegraph/ -q
```

## 비직관적인 것 (Gotchas)

- **Note — `terms_db.py` 에 정적 `codegraph.json` 을 위치 인자로 반드시 준다.** `--reading` 만 주면
  투영이 그 파일을 **덮어써서** 노드가 조용히 줄어든다. 🔵 실제로 두 번 겪었다.
- **Gotcha — 골든 경로 상수가 빈 문자열이 되면 안 된다.** `os.path.join("", "out/…")` 이 상대경로가
  되어 이 저장소의 산출물을 골든으로 착각해 읽는다. 그래서 `… or "/골든저장소_미지정/<변수>"` 를 쓴다.
- **Why — `run_mode1.py` 만 측정 코드를 갖는다.** 나머지 둘이 import 한다. 세 곳에 같은 토큰 셈이
  살면 하나만 고쳐도 표가 어긋난다.
- **Note — `declmap` 의 정규식은 ASCII 경로만 문다.** 한글 파일명은 인용으로 잡히지 않는다.
