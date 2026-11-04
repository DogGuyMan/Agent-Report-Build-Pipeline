# src/codewiki/ — Mode 1. 코드베이스를 읽어 코드 지도와 위키를 만든다

> 루트 나침반은 [`../../CLAUDE.md`](../../CLAUDE.md). 단계 기계는 [`../core/CLAUDE.md`](../core/CLAUDE.md), 리소스는 [`../../resource/CLAUDE.md`](../../resource/CLAUDE.md).
> 분리 계획(결정 0011)의 Phase B 는 이 폴더를 통째로 codebase-wiki 저장소로 떼어낸다.

이 저장소에서 가장 큰 모듈이다 — `python/machine/`(정적 수집 · 인용 검증) · `python/runner/`(실행기와 단계) ·
`python/viz/`(그림) · `csharp/roslyn-dump/`(C# 수집기). 시험은 `test/codewiki/`.
기계 쪽은 산문을 쓰지 않고 판정하지 않는다 — 기계가 아는 사실만 결정론으로 낸다.

## 무엇이 여기 있나

**전량 목록은 `python/machine/README.md` · `python/runner/README.md` · `python/viz/README.md` 에 있다** —
`tools/gen_readme.py` 가 소스에서 생성하고 `test/tools/test_gen_readme.py` 가 드리프트를 막는다. 아래는 급소만 고른 것이다.

| 자리 | 하는 일 |
|---|---|
| `python/runner/run_mode1.py` | Mode 1 실행기 — 단계 기계 위에서 흐름을 짓고 단계마다 시간과 토큰을 잰다. 열세 단계 `lang-hint→lang-decide→detect-changes→collect-graph→schedule-batches→annotate-symbols→snapshot-sources→verify-terms→outline-wiki→write-wiki→publish-wiki→verify-wiki→seal-artifacts`. LLM 칸은 넷(`lang-hint` · `annotate-symbols` · `outline-wiki` · `write-wiki`). `--cold` 는 전량(`detect-changes` 없음), `--resume` 은 `resume.json` 의 단계부터 |
| `python/runner/mode1/` | 단계 — `context`(문맥 · 형 · 산출물 16개 `ARTIFACTS` · 설정 · 프롬프트 자리) · `measured` · `machine_stage`(믹스인 · 베이스) · `diff` · `resume` · 단계 모듈 여덟 `lang` · `scan` · `graph` · `survey` · `survey_files`(`--strategy file`) · `terms` · `wiki` · `seal`(`seal-artifacts` — 이 실행에서 검사를 통과한 것만 `docs/codegraph/` 에 봉인) · `edges`(`ORDER` · `STAGES` · `EDGES` · `ALIASES`). **계산은 그것을 쓰는 단계 클래스의 `@staticmethod`** 이고 둘이 쓰면 믹스인이다. 프롬프트 글은 `../../resource/codewiki/prompts/*.md`, 샤드 검문의 결함 문구는 결함 표 `../../resource/codewiki/faults.toml` |
| `python/runner/wiki/` | `prep` · `build` · `check` — `bin/report-wiki` 의 세 명령. 그 밖에 `compdb` · `clang_doc` · `paths` |
| `python/runner/check_shard.py` | 전수조사 에이전트가 샤드를 쓴 뒤 스스로 돌리는 검문 |
| `python/viz/render_modules.py` · `render_classes.py` | 코드 지도를 Graphviz DOT 로 적고 굽는다 |
| `python/viz/demermaid.py` | 위키의 Mermaid 를 빌드 전에 SVG 로 사전 렌더 |
| `csharp/roslyn-dump/` | C# 수집기(dotnet). 출력은 `out/codegraph-raw/roslyn-dump.json` |

`python/machine/` 의 급소:

| 파일 | 하는 일 |
|---|---|
| `normalize.py` | 수집기 출력을 코드 지도(`codegraph.json`)로 정규화. **C++ · C# · Python 세 경로가 한 파일에 있다** |
| `pycalls.py` | 파이썬 소스에서 심볼과 **호출 관계**를 뽑는다(`ast` 만 씀). griffe 가 못 내는 것을 채운다 |
| `codegraph_types.py` | `codegraph.json` 계약 한 곳. 생산자와 소비자가 전부 여기를 본다 |
| `declmap.py` | 소스에서 선언 목록을 훑는다. 언어 넷(`cpp` `cs` `py` `ts`) |
| `clang_doc.py` | `clang-doc` 의 흩어진 JSON 을 평평한 심볼 목록으로 |
| `facts.py` | 코드 지도에서 사람이 읽는 사실 표(`facts/*.md`)와 `ranking.json` 을 만든다 |
| `lang_select.py` | 어떤 정적 수집기를 돌릴지 고른다. LLM Model의 제안을 결정론 검사로 거른다 |
| `clangd_refs.py` · `reverse_refs.py` | clangd 에 직접 말해 역방향 참조를 받는다 |
| `terms_db.py` | 용어 사전 병합과 **인용 검사 L1/L2/L3**. 투영이 코드 지도를 덮는다 |
| `verify_citations.py` | 위키 산문의 `파일:줄` 인용을 3값으로 판정 |
| `reading_types.py` | `Use` · `Term` · `Terms` 형 — `terms-reading.json` 레코드의 모양. `terms_db.py` 가 import 한다. 주석 주입기 `xmldoc.py` 와 그 산출물 `comments.xml` 은 2026-10-31 에 지웠다(`docs/decisions/0010` · `0014`) |
| `warmup.py` | 전수조사 증분 캐시 — 무엇을 다시 읽어야 하는지 가려낸다 |
| `survey_plan.py` | 코드 지도를 의존 위상 층과 배치로 나눈다. **판정하지 않는다** |
| `file_cache.py` | 층 경계에서 같은 파일을 다시 통독하지 않도록 개요를 디스크에 남긴다 |
| `manifest.py` | 봉인 매니페스트 — `seal` 이 산출물과 소스 지문을 대상 저장소의 `<저장소>/docs/codegraph/manifest.json` 에 적는다. 계약은 `../../contracts/` — 설명 문서 `contract-mode1-artifacts.md` 는 git 밖 `docs/` |

## Python 수집기 — 왜 둘인가 (2026-08-30 신설)

파이썬은 **수집기 둘을 합쳐야** 쓸 만한 지도가 나온다. C++ 이 clang-uml(관계)과
clang-doc(심볼 전량)을 합치는 것과 같은 구조다.

| 수집기 | 내는 것 | 못 내는 것 |
|---|---|---|
| `griffe`(외부) | 클래스 · 상속 · 타입 주석 | **호출 관계를 아예 안 낸다** — 시그니처 추출기다 |
| `pycalls.py`(우리 것) | 함수 · 메서드 · 호출 | 타입 주석에서 오는 관계 |

```bash
# 이 저장소를 훑을 때 — report-wiki prep 이 고르는 뿌리(파이썬 파일이 바로 든 최상위 폴더와 src/ 아래의 그런 폴더, test 제외)와 같다.
# src/ 꼴이면 griffe 는 -s src 로 그 안을 뿌리로 보고, pycalls 는 경로의 src/ 를 떼어 이름을 맞춘다 — id 에 src. 가 붙지 않는다
.venv/bin/python -m griffe dump codewiki term spec core common tools -o g.json -s . -s src
.venv/bin/python src/codewiki/python/machine/pycalls.py src/codewiki src/term src/spec src/core src/common tools --repo . -o pycalls.json
.venv/bin/python src/codewiki/python/machine/normalize.py --griffe-dump g.json --py-calls pycalls.json --repo . -o codegraph.json
```

`--py-calls` 는 **`--clang-doc` 과 같은 자리**다 — 배타 그룹이 아니라 합치는 인자이고,
안 주면 옛 동작 그대로다(🔵 바이트 대조로 확인).

🔵 2026-08-30 이 저장소 실측 — 무엇이 달라지는지:

| | 노드 | 간선 |
|---|---:|---:|
| griffe 만 | 67 | 122 |
| griffe + pycalls | **613** | **840** |
| (strict 전환 이전, griffe 만) | 2 | 0 |

**함정 — 이름 해소가 이 수집기의 급소다.** 틀려도 오류가 나지 않고 간선이 조용히 사라진다.
이 저장소의 import 는 세 꼴이 섞여 있다 — `sys.path` 에 형제 디렉토리를 넣고 부르는 평평한 이름(**`import warmup`**),
그렇게 넣은 디렉토리 아래의 패키지(**`from mode1.context import …`**), `src/` 뿌리부터 쓴 패키지
(**`from core import pipeline`** · `from common.python import pythonPath`). 그래서 `import_table` 은 import 에 쓰인
**점 경로를 통째로** 모듈 · 패키지 점 경로의 **꼬리**(끝 조각 하나 · 둘 · … · 전체)와 맞춰 찾고, 한 꼬리가 둘 이상과
맞으면 조용히 고르지 않고 **버린다**(`test/codewiki/test_pycalls.py` 가 고정한다). 파일 이름 하나는 그 꼬리의 가장 짧은 경우다.
개발 중 디렉토리 뿌리로 걸렀더니 모듈을 넘는 호출이 **338개에서 1개로** 떨어졌다. 🔵 2026-11-04 — 파일 이름(stem) 하나만
열쇠로 잡던 판은 `src/` 로 옮긴 뒤의 이 저장소에서 모듈을 넘는 호출을 **61개**만 잡았고, 점 경로 꼬리로 바꾼 뒤 **171개**다.

**호출의 kind 는 `dependency` 다.** 8종 enum 안에 있고 "부른다" 의 UML 대응이다.
소유(composition/aggregation)로 올리지 않는다 — 부른다고 갖는 것이 아니다.

## 위키 그림 사전 렌더 (`python/viz/demermaid.py`)

- **사전 렌더가 핵심이다.** VitePress 의 mermaid 플러그인은 브라우저에서 그린다.
  `demermaid.py` 가 빌드 전에 전면 치환해 **산출물에 JS 의존이 남지 않게** 한다.
  ⚠ 원본 위키는 고치지 않는다 — 인용 검증기의 대상으로 그대로 남아야 해서 치환본만 따로 낸다.
- **Mermaid 블록 앞줄의 `<!-- graphviz: <이름> -->` 표식**이 있으면 mmdc 대신 `--svg-dir` 의 미리 구운
  SVG 로 바꾼다. 산문을 손대지 않고 그림만 갈아 끼우는 자리다.
- 손으로 쓴 DOT 는 `docs/diagrams/<날짜>-<이름>.dot` 에 `.svg`·`.png` 와 함께 둔다.
- Mermaid 와 Graphviz 는 서로의 대체재가 아니다 — 산문 안의 그림은 LLM 이 쓰기 쉬운 Mermaid 로 들어오고,
  코드 지도에서 **계산해서** 그리는 그림은 Graphviz 다(`../spec/CLAUDE.md` 의 "Graphviz SVG 인라인 규칙").

## 세 mode 의 흐름 — Mode 1 만 여기 산다

**Mode 1 의 실행기는 `python/runner/` 에 있다.** Mode 1.5 · 2 의 실행기는 `../term/` · `../spec/` 에 있고
이 폴더를 import 하지 않는다 — 봉인된 산출물만 읽는다(결정 0011). 단계 기계 자체는 `../core/CLAUDE.md`.

```
Mode 1    lang-hint ─▶ lang-decide ─▶ detect-changes ─▶ collect-graph ─▶ schedule-batches ─▶ annotate-symbols
#            LLM        lang_select.py   warmup.py        normalize.py 등    survey_plan.py        LLM 층별
          ─▶ snapshot-sources ─▶ verify-terms ─▶ outline-wiki ─▶ write-wiki ─▶ publish-wiki ─▶ verify-wiki ─▶ seal-artifacts
#            warmup.py           terms_db.py     LLM             LLM                            verify_citations.py   manifest.py
Mode 1.5  collect ─▶ gate ─▶ [사람 차례] ─▶ grade ─▶ emit
Mode 2    init ─▶ [LLM] ─▶ build ─▶ check
```

옛 단계 이름(`prep` · `survey` · `warmup-save` …)은 `src/codewiki/python/runner/mode1/edges.py` 의 `ALIASES` 로 명령줄에서만 산다.

🔵 2026-08-30 실측 — **세 mode 모두 LLM 한 칸이 전체 시간의 99%** 를 쓴다.
Mode 1 냉시동은 27분 08초 중 에이전트가 26분 53초(99.1%) · 17,925,770 토큰 · $15.4991 · 84턴.
그중 **캐시읽기가 97.3%** 다 — `usage` 의 캐시 둘을 빼고 더하면 실제의 일부만 세게 된다.

**측정 코드는 `src/core/measure.py` 한 곳에 있고 세 실행기가 import 한다.** 재구현하지 마라.

## 전수조사 레코드 — 코드를 쓰면 레코드도 쓴다

절차의 정본은 **`codebase-terms-survey` 스킬**이다(저장소 사본 `.agents/skills/`).
여기서는 규약만 적는다:

- 원본은 대상 저장소의 `<저장소>/docs/codegraph/terms-reading.json`, 이 저장소 자신만 `../../resource/codewiki/terms-reading.json`. 꼴은 `{키: 레코드}`
- 레코드 계약 `{kind, module, where, means, does, uses[], confidence, source}`
- **`where` 는 실제 `파일:줄`** — `terms_db.py` 가 L1(파일) L2(줄) L3(근처에 그 이름) 로 검사한다
- `kind` 가 `file` `artifact` `key` `concept` `module` 이면 **이름이 그 줄에 글자 그대로** 있어야 한다
  (`terms_db.py` 의 `_stem` — `codegraph.json` 을 `.` 로 쪼개면 안 되기 때문)
- 새 함수를 만들면 그 자리에서 레코드를 쓴다. **주석 블록은 박지 않는다** — 주입은 폐지됐다(`docs/decisions/0010`)
- 코드가 움직여 줄이 밀리면 `where` 는 낡는다. 자동 재계산은 없다 — `terms_db.py` 의 L2 가 잡고, Mode 1 증분(`detect-changes`)이
  그 파일을 다시 읽거나 손으로 고친다. `uses[].where` 도 같다(L3 경고)

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

**배선돼 있다.** `warmup`(판정만)과 `warmup-save`(확정)가 `survey` 앞뒤에 각각 자기 칸으로
붙어 있다. **둘로 가른 것이 급소다** — 한 칸이면 에이전트가 실패해도
그 파일이 `유효` 로 기록되어 읽지 않은 파일이 읽은 것으로 남는다. 씨앗은 `changed_seed` 가 만들고
위 경고대로 `재읽기 ∪ 위치만` 이다. 판정을 못 하면 옛 동작인 전량 조사로 되돌아가고, 대조군은
`--skip warmup,warmup-save` 로 만든다.

계획서는 git 밖 `2026-08-30-warmup-mode1-wiring.md` 다. **Task 9(실측 대조)만 미실행** —
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
| — | 층 매기기는 **기계**다(`survey_plan.py`). `survey-plan` 이 `STAGES` 에서 자기 칸을 갖는 이유 — 한 칸에 묶으면 층 오름차순이 LLM Model의 판단처럼 읽힌다 |
| K2 | 층 안은 병렬, 층 사이는 순차 |
| K3 · K4 | 배치는 8심볼, 한 층에 동시 8배치 |
| K5 | 비노드 용어(file · module · artifact · key · concept)는 맨 마지막 별도 층 |
| K6 | 위키도 같은 층 순서. 페이지의 층 = 인용하는 심볼의 최대 층 |
| K7 | 고립 노드는 층0 |
| K8 | 성공 판정은 **벽시계만.** 토큰·비용 증가는 허용하되 기록한다 |

**서브에이전트 LLM Model은 `claude-sonnet-5-5` 다.** 값은 `resource/codewiki/config.toml` 의 `[models] sessions` 한 곳에 있고
(`lang-hint` 만 같은 표의 `lang_hint`), `src/codewiki/python/runner/mode1/context.py` 의 `load_config` 가 읽어 `run_mode1.py` 의 `--model` 기본값이 된다. 그 값이
단계(`src/codewiki/python/runner/mode1/survey.py` · `wiki.py` 의 `outline-wiki` · `write-wiki`) → `pipeline.run_layer` → `run_agent_with` → `measure.claude_argv` 사슬을 타고 내려간다.
`--strategy file` 의 `AnnotateFilesStage`(`src/codewiki/python/runner/mode1/survey_files.py`)는 `run_layer` 를 건너뛰고 `run_agent_with` 를 직접 부른다.
별명(`sonnet`)이 아니라 정확한 ID 를 쓴다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.

**파일 lock 은 걸지 않는다. 필요가 없다.** 배타성이 lock 이 아니라 `survey_plan.pack()` 에서
나온다 — 같은 파일의 심볼을 한 배치에 몰아넣으므로 한 층 안에서 두 배치가 같은 파일을
가리키지 않는다. 층 사이는 순차라 시간상 겹치지도 않는다. 🔵 2026-08-30 두 저장소에서
층 안 파일 중복 0건을 확인했다.

**비용은 아직 재지 않았다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다.
어느 쪽이 큰지 **모른다** — `--json` 으로 A/B 를 돌려 `qa/evals/runs/` 에 쌓고 대조한다.
기준선은 **opus 한 세션**이라 LLM Model까지 다르다. **"층 병렬 덕분" 이라고 귀속할 수 없다.**

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
| `REPORT_PYTHON` | 쓸 파이썬 해석기 | 저장소 안 `.venv` → PATH 의 `python3` 순으로 찾는다 (`src/common/python.py`) |
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

🔵 2026-08-31 실측 — 변수 없이 (그때 `machine/` 에 있던) 기계 시험은 **188 통과 · 19 건너뜀**이다.
건너뛰는 19개는 `$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO` 쪽 골든이라
그 저장소가 있어야 돈다. **건너뜀은 실패가 아니다.**

**함정.** 골든 경로 상수는 값이 없을 때 빈 문자열이 되면 안 된다. `os.path.join("", "out/…")` 이
**상대경로**가 되어 이 저장소의 산출물을 골든으로 착각해 읽는다(실제로 겪었다). 그래서
`… or "/골든저장소_미지정/<변수>"` 로 절대 존재할 수 없는 경로를 준다.

`data.ts` 의 `linkRoots` 도 같은 규약을 쓴다 — `src/spec/python/viz/link_paths.py` 의 `expandRoot()` 가
`$VAR` 와 `~` 를 편다. 변수가 없는 독자에게는 그 링크만 조용히 안 걸린다.

**새 문서에도 이 규약을 쓴다** — 홈 아래 경로를 적을 일이 생기면 위 변수 중 하나로 적는다.

**코드에도 경로를 박지 않는다.** 파이썬 해석기는 `src/common/python.py` 의 `pythonPath()` 로 찾고,
바깥 명령(`git` · `dot` · `clang-uml` · `dotnet` · `clangd` · `mmdc`)은 PATH 로 부른다.
새 기계에서 무엇이 빠졌는지는 **`npm run doctor`** 가 한 화면으로 말한다 — 필수가 없으면 exit 1.
파이썬 의존성은 `requirements.txt` 에 있다 — `networkx` `numpy` `scipy` `pytest` `griffe` `msgspec` 여섯이면 전량이 돈다.
설치 절차는 `README.md` 에 있다.

## 검증

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest test/codewiki -q          # 골든 변수가 없으면 일부 건너뛴다
.venv/bin/python src/codewiki/python/machine/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading resource/codewiki/terms-reading.json
#   기대: 실패 0. "근거 없음" 은 경고이지 실패가 아니다
.venv/bin/python src/codewiki/python/runner/run_mode1.py <저장소> --dry-run   # 자식 프로세스 0개. 시뮬레이터의 다섯 검사가 돈다
```

**파이썬 의존성은 여섯이면 전량이 돈다** — `networkx` `numpy` `scipy` `pytest` `griffe` `msgspec`
(`requirements.txt`). 표준 라이브러리로 풀 수 있으면 새 의존성을 더하지 마라.

## 이 모듈이 소유하는 것 (Owns)

`src/codewiki/**` · `resource/codewiki/**`(프롬프트 · 결함 표 · 템플릿 · 설정 · 골든 꼴 · 전수조사 원본) · `test/codewiki/**`,
그리고 `out/codegraph-raw/**`(재생성 대상이라 판 관리 밖). **소유하지 않는 것** — 단계 기계(`../core/`)와
Mode 2 의 것(`src/spec/typescript/src/*` · `src/spec/python/viz/build.py` · `src/spec/python/viz/check.py`)은 읽기만 한다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../core/` | `pipeline` · `measure` 를 import 한다 |
| 여기 → `../common/` | `python.py`(해석기 탐색) · `template.py`(`{{이름}}` 자리 채우기) |
| `bin/report-wiki` → 여기 | `prep` · `build` · `check` 를 자식 프로세스로 띄운다 |
| `../term/` · `../spec/` → 여기 | **import 하지 않는다.** 이 폴더가 대상 저장소에 봉인한 산출물을 `../common/evidence.py` 로 판정해 읽을 뿐이다(결정 0011) |

안에서의 화살표:

| 방향 | 무엇 |
|---|---|
| `python/runner/wiki/prep.py` → `python/machine/` · `python/viz/` | `pycalls.py` · `normalize.py` · `facts.py` · `render_modules.py` 를 자식 프로세스로 부른다 |
| `python/runner/wiki/build.py` → `python/viz/demermaid.py` | 자식 프로세스 |
| `python/runner/wiki/check.py` → `python/machine/verify_citations.py` | 자식 프로세스 |
| `python/runner/run_mode1.py` · `python/runner/mode1/*` → `python/machine/` | `survey_plan`(`run_mode1` · `graph` · `survey` · `context` · `wiki`) · `warmup`(`scan` · `diff` · `context` · `wiki`) · `declmap`(`scan`) · `manifest`(`context` · `wiki` · `seal`) 을 import 하고, `python/runner/mode1/terms.py` 가 `terms_db.py` 를, `python/runner/mode1/seal.py` 가 `manifest.py seal` 을 자식 프로세스로 부른다 |

⚠ **`normalize.py` 의 출력 키는 간접 의존이다.** `terms_db.py` 가 `from`/`to` · `id`/`depends_on`
를 읽는다. 코드에 명시돼 있지 않아 바꾸면 조용히 깨진다. 키를 바꾸는 변경이면 멈추고 보고한다.

## 흔한 변경 패턴 (Common modification patterns)

```bash
# Mode 1 에 단계를 더한다 — 넷을 한꺼번에 고친다. 하나라도 빠지면 시작 전에 GraphError 로 죽는다(프롬프트는 qa/gates/test_prompt_resources.py 가 잡는다)
#   src/codewiki/python/runner/mode1/<모듈>.py   Stage 하위 클래스 — name · emits · reads · writes · perform. 계산은 @staticmethod
#   resource/codewiki/prompts/<단계>.md  LLM 단계면 프롬프트 리소스(파일 이름 = 단계 이름) · 클래스에 prompt_names 선언("<파일>#<절>", 절이 없으면 "<파일>")
#   src/codewiki/python/runner/mode1/context.py  새 산출물이면 Artifact(schema · check) 를 만들고 ARTIFACTS 에 넣는다
#   src/codewiki/python/runner/mode1/edges.py    ORDER 에 자리 · STAGES 에 인스턴스 · SKIP 을 내면 EDGES 에 그 갈래 · 옛 이름은 ALIASES
.venv/bin/python src/codewiki/python/runner/run_mode1.py <저장소> --dry-run    # 시뮬레이터의 다섯 검사가 여기서 돈다

# 새 함수를 더했다 — 레코드도 그 자리에서 쓴다. 주석 블록은 박지 않는다 (0010)
$EDITOR resource/codewiki/terms-reading.json     # {kind, module, where, means, does, uses[], confidence}
.venv/bin/python src/codewiki/python/machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading resource/codewiki/terms-reading.json

# 코드를 옮겨 줄이 밀렸다 — L2 실패 목록을 보고 where 를 고치거나 Mode 1 증분으로 다시 읽는다
.venv/bin/python src/codewiki/python/machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading resource/codewiki/terms-reading.json

# 수집기 출력이 바뀌었다 — 골든 시험부터 본다
GRAPHICS_REPO=... CSHARP_REPO=... .venv/bin/python -m pytest test/codewiki -q
```

## 비직관적인 것 (Gotchas)

- **Note — `terms_db.py` 에 정적 `codegraph.json` 을 위치 인자로 반드시 준다.** `--reading` 만 주면
  투영이 그 파일을 **덮어써서** 노드가 조용히 줄어든다. 🔵 실제로 두 번 겪었다.
- **Gotcha — 골든 경로 상수가 빈 문자열이 되면 안 된다.** `os.path.join("", "out/…")` 이 상대경로가
  되어 이 저장소의 산출물을 골든으로 착각해 읽는다. 그래서 `… or "/골든저장소_미지정/<변수>"` 를 쓴다.
- **Why — `src/core/measure.py` 만 측정 코드를 갖는다.** 세 실행기가 import 한다. 세 곳에 같은 토큰 셈이
  살면 하나만 고쳐도 표가 어긋난다.
- **Note — `declmap` 의 정규식은 ASCII 경로만 문다.** 한글 파일명은 인용으로 잡히지 않는다.
- **Note — 위키 정적 사이트는 대상 저장소가 아니라 이 저장소 안에서 짓는다.** 대상에는
  `node_modules` 가 없어 `Cannot find package 'vitepress'` 로 죽는다. 산출물만 되돌아간다.
- **주의 — 대상 저장소의 전수조사 원본은 `<repo>/docs/codegraph/terms-reading.json` 이다.**
  이 저장소 자신의 것만 `../../resource/codewiki/terms-reading.json` 이라 두 경로가 다르다.
  `annotate-symbols.md` 의 `{{reading}}` 자리는 `context.reading_path` 가 채우며, 산출물 `READING` 의 자리도
  그 함수가 둘을 가른다 — 고칠 때 헷갈리지 말 것.
- **Gotcha — `run_mode1.py` 와 `mode1/` 만 `python/machine/` 을 import 한다.** `declmap` · `survey_plan` · `warmup` · `manifest` 넷이다.
  같은 폴더가 아니라 파일 머리에서 `sys.path` 에 자기 폴더 · `src/`(`core` · `common` 이 그 아래) · `python/machine/` 을 직접 넣는다.
- **Gotcha — 증분 그래프의 `--only prep` 은 거부된다.** `collect-graph` 가 `changes.json` 을 읽는다고 선언해서다.
  `--only warmup,prep` 이나 `--only prep --cold` 로 간다. 옛 단계 이름은 `mode1.edges.ALIASES` 로 `--only` · `--skip` 에서 산다.
- **Gotcha — 기계축 선언이 실물과 어긋난다.** `codegraph.json` 은 `survey_plan.CodeGraph` 로 strict 검증에
  실패하고(`GraphNode.file` 에 `null`), `warmup.json` 은 `warmup.Manifest` 로 실패한다(`Entry.mtime` 없음).
  러너는 `CodeGraphDoc`(최상위만)으로 보고 `cast` 로 넘긴다. 지문은 존재만 본다.
- **Note — 자기호스팅 코드 지도에는 시험이 없다.** `report-wiki prep` 은 최상위 `test/` 를 건너뛴다. 시험이
  `test/` 로 모인 2026-10-31 부터 `resource/codewiki/terms-reading.json` 의 시험 기호 레코드(약 600)는 지도에 노드가 없어
  "근거 없음" 으로 나온다 — 실패가 아니다.
