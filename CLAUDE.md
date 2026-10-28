# CLAUDE.md — 나침반

**이 문서는 지도가 아니라 나침반이다.** 어디를 봐야 하는지만 적는다.
자세한 것은 모듈 문서에 있고, 그것을 여기 다시 적지 않는다 — 두 군데 살면 어긋난다.

| 어디 | 무엇 |
|---|---|
| [`runner/CLAUDE.md`](runner/CLAUDE.md) | **러너축** — 세 실행기 · 명령 갈림길 · 얼갈이 단계 |
| [`machine/CLAUDE.md`](machine/CLAUDE.md) | **기계축** — 정적 수집 · 정규화 · 전수조사 레코드 · warmup |
| [`viz/CLAUDE.md`](viz/CLAUDE.md) | **시각축** — 렌더 경로 · 다이어그램 · 직접 실행 가드 |
| [`viz/src/CLAUDE.md`](viz/src/CLAUDE.md) | 컴포넌트 17개 · 테마 · 용어집과 관계 그래프 |
| [`tools/CLAUDE.md`](tools/CLAUDE.md) | 어느 축도 아닌 것 — 해석기 탐색 · 템플릿 채우기 · 환경 점검 · 경로 세척 · README 생성 |
| [`config/mode1.toml`](config/mode1.toml) · [`config/report.toml`](config/report.toml) | **설정값** — Mode 1 의 Model id · Mode 2 의 Model 별명(`opus`) · 원본 문서 자리 규칙 · 비용 어림(`[estimate]` — 형만 있고 읽는 운영 코드는 아직 없다). 코드는 읽기만 한다 |
| [`split-work/`](split-work/README.md) | **두 저장소 분리 작업 동안만** 쓰는 바이트 대조 도구. 제품 코드가 아니고 산출물은 git 밖이다. 분리가 끝나면 지운다 |
| [`test/CLAUDE.md`](test/CLAUDE.md) | 축을 가로지르는 시험 — 문서 게이트 · Node 렌더 시험 · 건너뜀 19 의 이유 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 두 저장소에 걸친 구조 · 데이터 흐름 · 다이어그램 |
| [`docs/wiki/`](docs/wiki/index.md) | **이 저장소의 RAG.** 자기 자신에게 Mode 1 을 돌려 구운 위키 21쪽. 코드를 뒤지기 전에 여기를 먼저 grep 한다 |
| [`docs/decisions/`](docs/decisions/README.md) | 기각·취소·보류된 것들. **같은 제안을 다시 하기 전에 읽는다** |
| [`docs/overturn/`](docs/overturn/README.md) | 뒤집힌 **판단**과 그 패턴. **무언가를 기각하려 하기 전에 검사표를 읽는다** |
| [`docs/CLAUDE.md`](docs/CLAUDE.md) | 보관소. **첨부되지 않은 인계·계획 문서는 스스로 열지 않는다** |

## ⚠ 방향 — 옛 산출물은 기준이 아니다

**이 도구는 옛 보고서를 재현하려고 만든 것이 아니다.** 2026-07-27 자 HTML 2건은 **출발점**이지
도달점이 아니고, 그것에 새 출력을 맞추려는 시도는 후퇴다. 새 정보는 이 저장소를 기반으로 쌓는다.
옛 저장소는 **CSS 의 출처**와 **장르 참고** 이상으로 쓰지 않는다. "정본" 은 *표기 규약의 기준*이라는
뜻으로만 남고 옛 HTML 은 **"옛 출력"** 이라 부른다. 세 Phase 가 이 한 결함으로 정리된 경위와
Track A/B 의 순서는 [`docs/decisions/0008`](docs/decisions/0008-old-output-is-origin-not-target.md) 에 있다.

## 이 저장소의 현재 상태 (🔵 2026-10-21 클라우드 실측 — 커밋 · 테스트 · 타입 · 버전 행. 나머지 행은 2026-09-13)

파이프라인 `report-spec init` → `report-spec build` → `report-spec check` 가 실제 스펙 디렉토리에서 end-to-end 로 동작한다. (옛 이름 `report` 도 위임으로 계속 동작한다.)

| 항목 | 실측값 |
|---|---|
| 측정 기준 커밋 / 태그 | `1d54b69` / `v1` — API 는 추가만이라 태그 그대로 |
| 테스트 | `pytest` **660 통과 · 2 실패 · 19 건너뜀** · `npm test` **8개**(JS 경계 `viz/svg.mjs` 만). 실패 2건은 아래 "게이트 여섯" 의 위키 표류와 층 분포 고정값이다 |
| 타입 | `tsc --noEmit` 통과 · `pyright` strict **0 errors** |
| 컴포넌트 export | 17개 (인계 문서가 지정한 11개 + `Page` `Section` `EvidenceNote` + 용어집 3종) |
| 빌드 산출물 `<script>` | 용어집 없으면 **0개**, 있으면 **1개**(용어 그래프 런타임 약 65KB) |
| Node / TypeScript / Graphviz | Mac v25.8.0 / 7.0.2 / 15.1.1 (2026-09-13) · 클라우드 v22.22.0 / 7.0.2 / 15.1.1 (2026-10-22). 클라우드 Ubuntu 의 apt 판(2.43)은 `-Tsvg_inline` 을 모르므로(`Format: "svg_inline" not recognized`) 환경 설정 스크립트 `tools/cloud_env.sh` 가 공식 `.deb` 를 깐다. `doctor` 는 10.0.1 미만을 낮음으로 막는다 |

**"검증됨" 이라고 쓰지 말 것 — D축 예측력.** 평가 없이 보류다([`0004`](docs/decisions/0004-d-axis-on-hold.md)).

## 위키는 아카이브가 아니라 RAG 다 (🔵 2026-09-08 실측)

`docs/wiki/` 는 이 저장소가 **자기 자신에게 Mode 1 을 돌려 만든** 코드베이스 위키다.
`docs/` 아래 있지만 성격이 정반대다 — **검색해서 읽으라고 있는 코퍼스**이므로
[`docs/CLAUDE.md`](docs/CLAUDE.md) 의 "첨부되지 않으면 열지 않는다" 규칙은 여기에 적용되지 않는다.

| 실측 | 값 |
|---|---|
| 페이지 | 21개 · 4067줄. 하위 폴더 없는 평평한 이름이라 파일명이 곧 주제다 |
| 코드 인용 | `파일:줄` 꼴 304건 (그중 줄 번호까지 붙은 것 92건) |
| 그림 | Mermaid 블록 30개. graphviz 치환 표식은 아직 0건 |
| 미검증 | `Unknown - verify` 29건 |

**쓰는 법 — 코드를 grep 하기 전에 위키를 먼저 grep 한다.** 인용이 `파일:줄` 이라 거기서
바로 코드로 내려갈 수 있다. 다만 셋을 지킨다:

- **`Unknown - verify` 가 붙은 문장은 근거가 없다.** 그대로 인용하지 말고 코드로 확인한다.
- **위키는 스냅샷이다.** 코드가 그 뒤로 움직였으면 조용히 표류한다 — 줄 번호부터 낡는다.
  🔵 2026-09-13 실제로 낡았다 — `report-wiki check .` 의 L2 실패 43건이 전부 `runner/run_mode1.py` 옛 줄 번호다(위 "게이트 여섯").
- **충돌하면 코드와 모듈 CLAUDE.md 가 맞다.** 위키는 그것들에서 파생된 2차 산출물이다.

다시 굽는 것은 Mode 1 이다 — [`runner/CLAUDE.md`](runner/CLAUDE.md) 를 보라.

### 그림은 두 도구가 굽고, 정적 사이트에 JS 를 남기지 않는다

| 도구 | 부르는 곳 | 무엇 | `doctor` |
|---|---|---|---|
| Graphviz `dot` | `viz/render_modules.py` · `viz/render_classes.py` | networkx 로 짠 그래프를 DOT 로 적고 `-Tsvg`/`-Tpng` 로 굽는다 | **필수** |
| Graphviz `dot -Tsvg_inline` | `viz/svg.mjs` | 보고서 HTML 본문에 그대로 삽입 | **필수** |
| Mermaid `npx mmdc` | `viz/demermaid.py` | 위키 산문의 Mermaid 를 **빌드 전에** SVG 로 사전 렌더 | 선택 |

**둘은 서로의 대체재가 아니다.** 산문 안의 그림은 LLM 이 쓰기 쉬운 Mermaid 로 들어오고,
코드 지도에서 **계산해서** 그리는 그림은 Graphviz 다 — `constraint=true/false` 분리가
Graphviz 에만 있고 그것이 의미축의 전제다(`viz/CLAUDE.md`).

사전 렌더 규칙 · `<!-- graphviz: <이름> -->` 표식 · 손으로 쓴 DOT 의 자리는 [`viz/CLAUDE.md`](viz/CLAUDE.md) 의
"위키 그림 사전 렌더" 절, 보고서 쪽은 같은 문서의 "렌더 경로" 와 "Graphviz SVG 인라인 규칙" 절에 있다.

## 사양 원본과 인계 문서

| 문서 | 역할 |
|---|---|
| `docs/handoffs/RESUME-2026-09-11-runner-stage-machine.md` | **지금의 재개 진입점.** 러너 단계 기계 3단계 완료 · 2026-09-13 msgspec 도입까지 반영. 빨간 게이트 둘을 푸는 순서가 여기 있다 |
| `docs/handoffs/HANDOFF-report-system.md` | **Track A/B 의 사양 원본.** 착수 전 통독한다 |
| `docs/handoffs/ReportSystem_ReturnHandOff.md` | 위 문서의 **사실 오류와 실행 중 발견된 결함**을 되돌려 보낸 회신. 인계 문서와 충돌하면 이쪽이 실측이다 |
| `docs/handoffs/HANDOFF-codebase-wiki.md` | **Track C — 별개 갈래.** 코드베이스 위키(deep-wiki + VitePress 다중 페이지). Track A/B 와 섞지 말 것 |
| `docs/superpowers/plans/2026-08-26-report-builder.md` | 실행 계획. 발견된 결함이 해당 Phase 절에 반영돼 있다 |
| `docs/handoffs/RESUME-2026-10-28-official-term-grounding.md` | **Mode 1.5 강화 갈래 — 공식 용어 근거 스킬(① 권위 출처 · ② 사용 빈도 말뭉치).** 0단계 확인까지 했고 사용자 결정을 기다린다. Track A/B/C 와 섞지 말 것. 개인어 그래프(⑤)는 [`0013`](docs/decisions/0013-personal-language-graph-deferred.md) 으로 보류 |

`ReportSystem_HandOff.md` 는 `HANDOFF-report-system.md` 와 동일 계열의 구판이다.

## 명령

```bash
npm run setup            # 새 기계에서 먼저 — .venv · node_modules 를 고정된 판으로 깔고 doctor 까지 (tools/setup.sh)
npm run doctor           # 이 컴퓨터에 무엇이 있고 무엇이 없는지. 필수가 없거나 판이 낮으면 exit 1
.venv/bin/python -m pytest -q                        # 파이썬 시험 전량
.venv/bin/python -m pytest test/test_check.py -q     # 단일 파일
.venv/bin/python -m pytest -k "링크" -q               # 이름으로 고르기
npm test                 # JS 경계만 — pretest 가 viz/lib.mjs 로 .tmp/lib.mjs 를 만든 뒤 node --test
npm run typecheck        # tsc --noEmit (이 저장소의 viz/src/ 만)
npm run typecheck:py     # pyright strict
```

### 게이트 여섯 — 전부 초록이어야 한다 (🔵 2026-10-21 실측 — 지금 둘이 빨강)

| 게이트 | 명령 | 지금 |
|---|---|---|
| 파이썬 시험 | `.venv/bin/python -m pytest -q` | 🔴 660 통과 · **2 실패** · 19 건너뜀 |
| JS 시험 | `npm test` | 8 통과 |
| TS 타입 | `npm run typecheck` | 통과 |
| 파이썬 타입 | `npm run typecheck:py` | 0 errors |
| README 표류 | `.venv/bin/python tools/gen_readme.py --check machine runner viz tools` | 4개 일치 |
| 환경 | `npm run doctor` | 필수 전부 있다 |

**건너뛰는 19개는 골든 저장소 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO`)가
없어서다. 실패가 아니다.**

**빨강 하나 — 위키 표류.** 2026-09-08~11 의 러너 단계 기계 리팩터링이 `runner/run_mode1.py` 의 심볼을
`runner/mode1/` 로 옮겼는데(파일이 281줄로 줄었다) 위키를 다시 굽지 않았다.
`test/test_wiki.py::test_check_는_통과를_통과로_보고한다` — 위키가 `runner/run_mode1.py:414~1075` 를 인용하고
`report-wiki check .` 가 L1 561/0 · **L2 518/43** 으로 exit 1. 푸는 것은 **위키 재굽기(Mode 1 자기 실행)** 이고
손으로 고치지 않는다. 🔵 2026-10-21 클라우드에서도 L2 실패는 같은 43건이고, 그 위에 L1 실패 18건이 더 나온다 —
전부 `tools/` 의 `scrub_local_paths.py` 인용인데 이 파일은 git 밖(`.gitignore:28`)이라 그 파일이 없는 클론에서만 난다.
`out/` 이 없는 새 클론에서는 `report-wiki prep .` 을 먼저 돌려야 이 실패가 보인다 — 안 돌리면 `codegraph.json` 이
없다는 다른 이유로 실패한다. `docs/handoffs/RESUME-2026-09-11-runner-stage-machine.md` 의 "바로 다음 할 일" 중
1번(xmldoc 재주입)은 [`0010`](docs/decisions/0010-xmldoc-retired.md) 으로 **무효**, 2번(위키)부터다.

**빨강 둘 — 층 분포 고정값.** `machine/test_survey_plan.py::test_이_저장소_실측` 이 이 저장소 코드 지도의 층 분포를
`[514, 323, 161, 96, 23, 14]`(합 1131, `943f3fc` 2026-09-19)로 못박는다. 🔵 2026-10-21 클라우드에서 `report-wiki prep .` 을
새로 돌리면 `[544, 347, 167, 104, 23, 15]`(합 1200)이다. 같은 날 사용자 Mac 에서도 실패하는데 값이 `[538, 342, …]` 로 또 다르다.
기계마다 다른 이유는 확인하지 못했다 — 기대값을 고치기 전에 그것부터 본다. `out/codegraph-raw/codegraph.json` 이 없으면
이 시험은 건너뛴다.

**`xmldoc check` 는 게이트가 아니다 (2026-09-13).** 주석 주입은 폐지됐다 — [`0010`](docs/decisions/0010-xmldoc-retired.md).

### 파이썬이 본체이고 JavaScript 는 경계에만 남는다 (2026-08-31 포팅)

세 CLI 와 러너 · 기계 · 렌더 파이프라인은 전부 **파이썬**이다. JavaScript 가 남는 자리는
**esbuild 와 React 가 실제로 읽는 곳** 넷뿐이다 — 옮기면 번들러가 파싱하지 못한다.

| 남는 JS | 왜 |
|---|---|
| `viz/src/**` (`.ts` · `.tsx`) | React 컴포넌트 원본. 확정된 스택 |
| `viz/svg.mjs` + `viz/svg.d.mts` | `report.tsx` 가 `report-builder/svg` 로 **import** 한다. 번들 시점에 esbuild 가 읽는다 |
| `viz/lib.mjs` | `viz/src/` 를 `.tmp/lib.mjs` 로 굽는 esbuild 호출 |

**`test/test_components.py` 는 node 를 자식 프로세스로 띄워 `.tmp/lib.mjs` 를 렌더한다.**
`viz/src/` 를 고치고 시험이 옛 동작을 보이면 `.tmp/lib.mjs` 가 낡은 것이다 — `npm test` 로 다시 굽는다.

### mode 별 진입점 — 2026-08-29 분리

`bin/` 에 진입점이 네 개다. 전부 PATH 에 잡힌다 (`~/.zshrc:211`).

| 진입점 | Mode | 명령 | 하는 일 |
|---|---|---|---|
| `report-wiki` | 1 | `prep` · `build` · `check` | 코드베이스 위키. 세 명령이 **실제로 돈다**(`bin/report-wiki`). 사이의 LLM 자리는 `codebase-terms-survey` 스킬(전수조사)과 deep-wiki 스킬(산문)이 맡고, `runner/run_mode1.py` 가 그 전부를 한 번에 돌리며 잰다 |
| `report-term` | 1.5 | `collect` · `grade` · `emit` | 용어 이해도 점검. Plan 이 요구하는 용어를 모으고, 객관식 답안을 채점해, 학습 노트와 용어집 DB 를 낸다 |
| `report-spec` | 2 | `init` · `build` · `check` | 설계 검토 보고서 |
| `report` | — | (`report-spec` 과 같음) | **옛 이름.** `report-spec` 으로 위임하고 stderr 에 알림 한 줄을 낸다. stdout 은 동일 |

`report-wiki` · `report-spec` · `report-term` 셋이 `runner/dispatch.py` 의 `run_dispatch` 를 공유하고,
각자 자기 명령표만 갖는다. `report` 만 `report-spec` 을 자식 프로세스로 실행한다(`subprocess.run`).

보고서 쪽 명령은 **보고서가 있는 저장소의 스펙 디렉토리에서** 실행한다:

```bash
cd <프로젝트>                      # specs/ 나 plans/ 가 있는 저장소
report-spec init                   # 보고서가 없는 문서를 날짜 내림차순으로 나열, exit 1
report-spec init <slug>            # specs/YYYY-MM-DD-<slug>-design.md 또는 plans/YYYY-MM-DD-<slug>.md
cd <자리>/<slug> && report-spec build  # → out/report.html. <자리> 는 원본이 있던 곳
report-spec check                      # script 수 · tsc · 링크 무결성 · 용어집 대조(경고) · builderVersion
```

용어 이해도 점검은 Plan 하나를 놓고 돈다. 사람에게 묻는 절차는 CLI 가 아니라 `term-benchmark` 스킬이 맡는다:

```bash
report-term collect <plan.md> [terms-db.json]   # → term-candidates.json
#   (`term-benchmark` 스킬이 questions.json 을 내고, 실행기는 그것을 기계로 검사해
#    정답을 뺀 기입란 answer-sheet.json 을 깐다. 실행기에는 LLM Model을 부르는 칸이 없다)
#   (사람 또는 스킬이 칸마다 UserAns 에 보기 번호를 적어 answers.json 으로 둔다)
report-term grade answers.json questions.json   # → term-grades.json  확실/모름
report-term emit term-grades.json               # → terms.json + term-study-note.md
```

## 경로 변수 — 기계마다 다른 경로를 적지 않는다

**이 저장소는 공개된다.** 홈 아래 경로를 문서·코드·커밋에 그대로 적지 않고 변수 이름을 쓴다 —
`$REPO_ROOT` · `$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO` · `REPORT_PYTHON`.
**전체 표와 골든 상수의 함정은 [`machine/CLAUDE.md`](machine/CLAUDE.md) 의 "경로 변수" 절에 있다.**

`test/test_docs_citations.py` 가 컨텍스트 문서(서브에이전트 · 이 저장소의 스킬 포함)의 인용을 검사하며
`$` · `~` 로 시작하는 경로는 바깥으로 보고 건너뛴다. 그 규약을 어기면 게이트에 걸린다.

## 아키텍처 — 두 저장소에 걸쳐 있다는 것이 전부다

이 저장소는 렌더러이고, **보고서는 다른 저장소의 `<프로젝트>/specs/<slug>/` 에 산다.** 여기서 나오는
비직관적 결정이 코드 곳곳에 박혀 있다.

**경로 실측 (2026-08-28).** 루트는 `$REPO_ROOT` 다. `~/report-builder` 는 **존재하지 않는다** —
이 문서의 이전 판이 그렇게 적어 두 세션이 헛짚었다. 근거: `~/.zshrc:211` 의
`export PATH="$HOME/LLM-Tools/report-builder/bin:$PATH"` (다른 셸 설정 파일에는 등록 없음),
`readlink -f "$(which report)"` → `$REPO_ROOT/bin/report`.

**자기호스팅은 예외가 아니라 의도다.** `report` 는 PATH 에 등록된 툴 바이너리이므로 어느 저장소에서든
부를 수 있고, 이 저장소 자신의 계획서도 검토 대상이 된다. 실제로 `docs/superpowers/specs/llm-load-reduction/` 이
여기 안에 있다 — Track C 계획을 Track A/B 도구로 검토하는 자기참조 구조다. 옮기지 말 것.

```
$REPO_ROOT                  <프로젝트>/specs/<slug>/
  bin/report-spec        디스패치만       data.ts      결정 데이터만. builderVersion 포함
  runner/dispatch.py     명령 갈림길      report.tsx   서사·옵션표·판정 등 나머지 전부
  viz/src/components/    읽기 전용        (tsconfig.json)  check 가 ROOT 에 임시 생성
  viz/src/theme.css      옛 출력에서 추출  (out/report.html)  git 제외 — 재생성
  viz/build.py           esbuild→RTSM→조립
  viz/check.py           기계 검사 규칙
  viz/svg.mjs            report.tsx 가 import 하는 자리라 JS 로 남는다
```

### 성격축 셋 — 언어가 아니라 하는 일로 가른다 (2026-08-30)

| 축 | 자리 | 가르는 질문 |
|---|---|---|
| 러너 | `runner/` + `bin/` | **시키는가** — 순서를 잡고 자식 프로세스를 띄운다 |
| 기계 | `machine/` | **계산하는가** — 정적 수집·정규화·용어 DB. 그림을 그리지 않는다 |
| 시각 | `viz/` | **그리는가** — HTML·SVG·다이어그램. 계산된 것을 받아 굽는다 |

**옛 경계(`scripts/`=Node · `codegraph/`=Python)는 성격과 어긋나 있었다.** Graphviz 를 부르는
파이썬 셋이 기계축에, 결정론적 채점 `.mjs` 가 Node 축에 섞여 있었다. `tools/` 는 셋 어디에도
속하지 않는 것만 받는다. `config/` 는 축이 아니라 설정값이 사는 자리이고, 코드는 읽기만 한다.

## 확정된 스택 (변경 금지)

| 축 | 결정 |
|---|---|
| 위치 | `$REPO_ROOT` 고정 경로. `bin` 을 PATH 에 추가 |
| 트랜스파일 | **esbuild** — `viz/build.py` 가 `npx esbuild` 를 자식 프로세스로 부른다 |
| 렌더 | **React `renderToStaticMarkup`** — 마크업은 템플릿 엔진으로만. **단 용어 그래프 런타임 1개는 산출물에 실린다**(아래) |
| 타입 | props 타입 정의만. `tsc --noEmit` |
| 단일 파일화 | **파이썬 문자열 조립**(`viz/build.py`). 번들러의 CSS 파이프라인은 쓰지 않는다 |
| 확대 UX | 다이어그램은 **CSS 체크박스 토글, JavaScript 0줄**. 용어 그래프는 런타임 스크립트 (아래) |
| UI / 상태 | **React 훅은 여전히 쓰지 않는다.** 클라이언트 상태는 용어 그래프 안에만 있다 |

### 산출물 불변식 (기계 검사 대상)

**빌드된 `report.html` 에 `<script>` 태그가 1개를 초과하면 잘못된 것이다.**
`grep -c '<script' out/report.html` 로 검사한다.

**예산 1칸은 2026-08-29 에 용어 그래프 런타임이 가져갔다.** `data.ts` 에 `terms` 가 있을 때만
`viz/build.py` 가 `viz/src/runtime/term-graph.ts` 를 번들해 넣는다. 용어집이 없는 보고서는
여전히 `<script>` 0개다. **예산이 다 찼으므로 새 런타임 코드를 넣으려면 이 번들 안에 합쳐야 한다.**

## 기각·취소된 것에 착수하지 마라

Phase 2·3·6 과 D축 보류의 사유와 되살릴 조건은 전부 [`docs/decisions/`](docs/decisions/README.md) 에 있다.
계획서의 해당 절 체크박스는 유효하지 않다. Track A/B 의 강제 순서와 이탈 기록은 [`0008`](docs/decisions/0008-old-output-is-origin-not-target.md).

## 참조 원본의 실제 위치 — 출처이지 기준이 아니다

이 체계가 **출발한** 자료는 다른 저장소에 있다. **읽을 일이 생길 때만 열고, 새 출력을 여기에
맞추지 않는다**(위 "방향" 절):

```
$GRAPHICS_REPO/doc/
  superpowers/specs/2026-07-27-geometry-winding-ownership-design-review.html   ← theme.css 의 출처
  superpowers/specs/2026-07-27-matrix-rain-parameterization-design-review.html ← 같은 계열 1건
  superpowers/specs/*-design.md                                                 ← 입력 형태
  superpowers/specs/*-{before,after}.{dot,svg,png}                              ← Graphviz 원본
  번복기록/                                    ← 체계의 원천 + **두 번째 보고서 장르**
```

`번복기록/` 은 두 번째 보고서 장르다 — **지금 mode 를 추가하지 말 것.** 사유와 되살릴 조건은
[`docs/decisions/0009`](docs/decisions/0009-second-report-genre-deferred.md).

스킬 원본은 `~/.claude/skills/<이름>/SKILL.md`(단 `codebase-terms-survey` 는 저장소 `.agents/skills/` 가 원본이고 저장소 안 `.claude/skills/` 가 심볼릭 링크 — 2026-08-29 사용자 이전).

⚠ **`.claude/skills/` 는 두 자리에 있다. 헷갈리지 말 것**(🔵 2026-08-31 실측 — 한 세션이 실제로 헛짚었다).

| 자리 | 무엇 | git |
|---|---|---|
| `<repo>/.claude/skills/` | 항목 20개 — **심볼릭 링크 13개**(`../../.agents/skills/<이름>`) + 실제 디렉토리 7개 — 홈 원본을 깊은 복사로 맞춰 넣은 사본: `spec-review-dashboard` · `term-benchmark` 와, 클라우드 세션(저장소 하나를 여는 claude.ai/code 세션 — 프로젝트 스레드는 저장소 스킬을 안 읽는다)에도 있게 넣은 `personal-commit-messages` · `design-decision-discipline` · `lossless-handoff` · `confidence-and-sourcing` · `response-quality-calibration`. 링크 자체가 추적된다 | 추적됨(🔵 2026-10-24) |
| `~/.claude/skills/` | 위 실제 디렉토리 7개의 **원본**, 그리고 `codebase-terms-survey` 의 사본(원본은 저장소 `.agents/skills/`). 저장소 밖이라 어느 저장소도 추적하지 않는다 | 밖 |

`.gitignore` 에 `.claude` 는 없다 — 저장소 안 것이 git 밖인 이유는 무시라서가 아니라
**홈 경로가 애초에 워킹 트리 밖**이기 때문이다. 사본은 어느 쪽이든 조용히 표류한다 — 원본을 고치면 같은 변경에서 사본도 맞춘다(🔵 2026-08-31 —
워크플로 7단계 시절 구판으로 남아 층 병렬 배치 절이 통째로 없었다. 원본으로 맞췄다).

Track 별 참조 스킬 목록은 [`0008`](docs/decisions/0008-old-output-is-origin-not-target.md) 끝에 있다.

## 혼자 정하지 말 것 (미결정)

- N값(지연 승격 커밋 수) — 근거 없는 임의값 금지
- D 점수 구간 경계 — A1 취소로 판단 근거가 사라졌다. D축을 되살릴 때 함께 정한다
- `[잠정됨]` 이라는 이름과 그 적용 범위
- `data.ts` 의 D축 필드 포함 여부 (D축 자체가 보류라 함께 잠겨 있다)


## 함정

- **거울 함정.** 과잉 설계를 잡는 도구를 만들면서 그 도구를 과잉 설계하는 것. `d-axis` 는 지표 3개를
  계산하는 스크립트다. 플러그인 구조·지표 레지스트리·추상 인터페이스가 나오면 그 자체가 이 작업이 잡으려는
  실패다. 구현자 1, 소비자 1이면 인터페이스를 만들지 마라.
- **지표 증식 유혹.** D축은 3종 고정. 좋은 아이디어가 떠올라도 넣지 말고 **기록만 하고 사용자에게 보고**하라.
- **조기 성공 선언.** 표본이 5~10개면 그 정도로는 아무것도 증명되지 않는다.
  **"검증됨" 이라고 쓰지 말 것.** 목표는 "명백한 반례가 없는가" 수준의 sanity check 이다.
- **합성 데이터만으로 검증하지 말 것.** 백틱 제목 결함(`viz/CLAUDE.md` 의 `json.dumps` 이스케이프 절)은 서브에이전트가 실제 저장소 데이터를 확인하다
  발견했다. 합성 테스트만 썼으면 안 나왔다.

## 작업 규약

`.claude/CLAUDE.md` 의 13개 체크포인트가 이 저장소에도 그대로 적용된다. 그 위에 추가되는 것:

- **리소스와 코드를 가른다 (최우선).** LLM 프롬프트는 단계당 한 파일 `runner/**/prompts/<단계>.md`(파일 이름이
  단계 이름이고, 안은 `<!-- section: 이름 -->` 으로 가른다), 코드가 쓰는 파일 템플릿은 `runner/**/templates/` ·
  `viz/templates/`, 설정값은 `config/*.toml`, 샤드 검문의 결함 문구는 결함 표 `runner/mode1/faults.toml`. 파이썬은 읽기만
  한다 — 프롬프트는 단계가 `prompt_names` 에 선언한 이름으로 `PromptResource.load_prompt("<파일>#<절>")`(절이 없는 파일은
  `"<파일>"`), 템플릿은 `tools.template.render_file`.
  **프롬프트 글은 Jinja2 다**(`requirements.txt` 의 명시 의존) — 반복 · 빈 값 대체 · 조건부 절을 파일 안에 쓰고, 글이 쓰는
  이름과 넘긴 값이 같아야 한다. **템플릿은 꼴만, 데이터 결정은 단계** — 무엇을 싣는가는 파이썬이 정해 행으로 넘긴다
  ([`0012`](docs/decisions/0012-prompt-dynamics-in-jinja2.md)). 파일 템플릿의 자리표시는 `{{이름}}` 하나다.
  `test/test_prompt_resources.py` 가 막는다 — 긴 글(문자열 상수 · f-문자열)은 `runner` · `viz` · `machine` · `tools` 의
  파이썬(시험 파일 제외)에서 찾고, 프롬프트 글은 전부 Jinja2 로 컴파일되어야 하며 줄 끝 공백과 `{#` 를 두지 않는다.
- 확신도는 🔵/🟡/💭 + 정수. **🔵는 이번 세션에서 실제로 읽은 file:line 또는 실제로 돌린 명령의 출력만 인정.**
- 결정은 `[제안됨]` 으로 먼저 기록하고 검증 후 승격.
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 구조 신설 제안 시 `design-decision-discipline` §2.5 의 4항목을 공개하고 §2.7 의 축을 선언한다.
- **남의 제안을 기각할 때는 `docs/overturn/README.md` 의 검사표를 먼저 지난다.** 제안에는
  §2.5·§2.7 의 의무가 붙지만 기각에는 없어서, 지금까지 뒤집힌 판단은 전부 기각·포기 쪽이었다(표본 수는 그 README 가 센다).
- **컴포넌트는 추가만 한다.** props 제거·의미 변경 금지. 컴포넌트 API 가 바뀌는 갱신마다 태그(`v1`, `v2`).
  옛 버전 빌드가 필요하면 `git worktree add /tmp/rb-v1 v1`.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.** 인계 문서 초안이 그 이유로 한 번 반려됐다.

### 코드 주석 — 현 상황만 적는다 (2026-08-30 확정)

**주석과 독스트링에는 "지금 이 코드가 무엇인가" 만 쓴다.** 확신도 표기·날짜·측정 수치·번복
기록·설계 철학·존재 이유 서사를 코드에 남기지 않는다. 그런 것은 대화와 `docs/` 의 몫이다.

| 쓴다 | 쓰지 않는다 |
|---|---|
| 함수·클래스마다 한 줄 요약 | `**왜 필요한가.**` 절 |
| 코드가 의존하는 형식·동작 사실 | `🔵 2026-08-29 <저장소> 실측 — …` 날짜 붙은 관찰 |
| 비직관적 제약과 그 즉각적 귀결 | `~에 뒤집힌 결정` · `이전 판은 ~라고 적었다` |
| | `거울 함정 경계 — …` 같은 설계 철학 |
| | 관찰 보고서·계획서·핸드오프 참조 |

**형식·동작 사실은 남긴다** — 지우면 다음 사람이 버그를 만든다.
예: `clang-doc 의 Namespace 는 안쪽부터 온다. 뒤집어야 한다.` 날짜와 수치만 뺀다.

**주장이 아니라 시험으로 적는다.** 외부 도구의 동작에 기대는 사실은 주석 대신 그것을 고정하는
시험을 두고 주석은 그 이름을 가리킨다. 주석은 썩지만 시험은 깨진다.

모듈·클래스·함수의 목록과 역할은 각 디렉토리의 `README.md` 에 둔다.

⚠ **소스에 남은 `# <include …/>` 블록은 폐지된 주석 주입의 잔재다**([`0010`](docs/decisions/0010-xmldoc-retired.md)).
**새 코드에 심지 않고, 있는 것을 고치지도 않는다.** `emit` · `inject` · `check` 어느 것도 돌리지 않는다.
지우는 것은 별개의 코드 작업이라 사용자가 시점을 정한다. 대체 마크업은 없다 — 의존 그래프는 `terms-db.json` 에 산다.
- 커밋 메시지는 `personal-commit-messages` 스킬을 따른다 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).

## 문서 정본

- 정본 `.agents/rules/react-best-practices.md` · 같은 내용의 사본 `.gemini/ReactRule.md` (내용을 고칠 때는 정본만 고친다)
- 정본 `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md` · 같은 내용의 사본 `docs/handoffs/HANDOFF-2026-08-29-mode-1-terms-db-tasks-1-5.md`, `docs/superpowers/specs/2026-08-29-mode-1-terms-db-first-design.md` (내용을 고칠 때는 정본만 고친다)
- 정본 `docs/handoffs/HANDOFF-report-system.md` · 같은 내용의 사본 `docs/handoffs/ReportSystem_HandOff.md` (내용을 고칠 때는 정본만 고친다)
- 정본 `docs/superpowers/specs/2026-08-28-llm-load-reduction-design.md` · 같은 내용의 사본 `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` (내용을 고칠 때는 정본만 고친다)

## 용어

- LlmStage · 같은 뜻의 다른 표기 llmstage (새로 쓸 때는 LlmStage)
- codegraph · 같은 뜻의 다른 표기 code graph (새로 쓸 때는 codegraph)
- deep-wiki · 같은 뜻의 다른 표기 DeepWiki (새로 쓸 때는 deep-wiki)
- run_dispatch · 같은 뜻의 다른 표기 runDispatch (새로 쓸 때는 run_dispatch)
