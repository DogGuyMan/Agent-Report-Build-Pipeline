# CLAUDE.md — 나침반

**이 문서는 지도가 아니라 나침반이다.** 어디를 봐야 하는지만 적는다.
자세한 것은 모듈 문서에 있고, 그것을 여기 다시 적지 않는다 — 두 군데 살면 어긋난다.

| 어디 | 무엇 |
|---|---|
| [`codegraph/CLAUDE.md`](codegraph/CLAUDE.md) | 파이썬 파이프라인 · 세 실행기 · 전수조사 레코드 · warmup |
| [`scripts/CLAUDE.md`](scripts/CLAUDE.md) | Node 배선 · 모듈 해결 · 직접 실행 가드 · 렌더 경로 |
| [`src/CLAUDE.md`](src/CLAUDE.md) | 컴포넌트 17개 · 테마 · 용어집과 관계 그래프 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 두 저장소에 걸친 구조 · 데이터 흐름 · 다이어그램 |
| [`docs/decisions/`](docs/decisions/README.md) | 기각·취소·보류된 것들. **같은 제안을 다시 하기 전에 읽는다** |

## ⚠ 방향 — 옛 산출물은 기준이 아니다 (2026-08-29 확정)

**이 도구는 옛 보고서를 재현하려고 만든 것이 아니다.** 2026-07-27 자 HTML 2건은 이 체계의 **출발점**
이지 도달점이 아니다. 그것을 "정본" 으로 삼아 새 출력을 맞추려는 시도는 **후퇴다.**

2026-08-28~29 세션에서 **세 Phase 가 같은 결함으로 정리됐다.** 우연이 아니라 한 가지 실수의 세 얼굴이었다.

| Phase | 하려던 것 | 공통 결함 |
|---|---|---|
| 2 (B2) — 기각 | 옛 저장소의 `mPasses` 사례로 파일럿 | 옛 프로젝트의 결정 이력에 의존 |
| 6 (B5) — 취소 | 옛 보고서 2건을 재생성해 **시각 동등** 확인 | 옛 출력을 목표로 삼음 |
| 3 (A1) — 취소 | 옛 저장소 설계 문서 60개로 소급 채점 | 옛 프로젝트의 이력에 의존 |

**앞으로는 이 저장소를 기반으로 새 정보를 쌓는다.** 도구를 완성해 실제 프로젝트에 써 보고, 거기서
실측과 보완점을 얻는다. 옛 저장소는 **CSS 의 출처**와 **장르 참고** 이상으로 쓰지 않는다.

**이 문서에 남은 "정본" 이라는 말은 두 가지 뜻이 섞여 있다.** 하나는 *표기 규약의 기준*(예: 상태 태그는
한국어가 정본) — 이건 유효하다. 다른 하나는 *옛 HTML 출력* — 이건 기준이 아니다. 뒤엣것은 아래에서
**"옛 출력"** 으로 고쳐 부른다.

## 이 저장소의 현재 상태 (2026-08-27 실측)

파이프라인 `report-spec init` → `report-spec build` → `report-spec check` 가 실제 스펙 디렉토리에서 end-to-end 로 동작한다. (옛 이름 `report` 도 위임으로 계속 동작한다.)

| 항목 | 실측값 |
|---|---|
| 커밋 / 태그 | 최신 `05869ac` / `v1` — API 는 추가만이라 태그 그대로 |
| 테스트 | `npm test` **145개** · `pytest codegraph/` **201 통과 · 19 건너뜀** (🔵 2026-08-30 실측) |
| `tsc --noEmit` | 통과 |
| 컴포넌트 export | 17개 (인계 문서가 지정한 11개 + `Page` `Section` `EvidenceNote` + 용어집 3종) |
| 빌드 산출물 `<script>` | 용어집 없으면 **0개**, 있으면 **1개**(용어 그래프 런타임 약 65KB) |
| Node / TypeScript / Graphviz | v25.8.0 / 7.0.2 / 15.1.1 |

**아직 "검증됨"이 아닌 것 — 이렇게 쓰지 말 것:**
- **D축 예측력(A1)** — **취소.** 아래 "Phase 3 취소" 절을 보라. D축은 평가 없이 보류 상태로 남는다.

**2026-08-28 에 해소된 것:**
- **B1 육안 판정 — 완료.** 사용자가 Chrome 으로 패치 전/후를 대조했다. 패치 전 옛 출력은 2615px SVG 가
  486px 패널로 눌려 "있기는 한데 너무너무 작다"(창 1200px · 배율 100%). 패치본은 토글이 보이고,
  누르면 1열로 펴지며 문구가 바뀌고 가로·세로 스크롤이 생긴다. **결함은 실재했고 체크박스 토글로 복구된다.**
- **옛 출력 재현(Phase 6) — 취소.** 아래 "Phase 6 취소" 절을 보라.

## 사양 원본과 인계 문서 3종

| 문서 | 역할 |
|---|---|
| `docs/handoffs/HANDOFF-report-system.md` | **Track A/B 의 사양 원본.** 착수 전 통독한다 |
| `docs/handoffs/ReportSystem_ReturnHandOff.md` | 위 문서의 **사실 오류와 실행 중 발견된 결함**을 되돌려 보낸 회신. 인계 문서와 충돌하면 이쪽이 실측이다 |
| `docs/handoffs/HANDOFF-codebase-wiki.md` | **Track C — 별개 갈래.** 코드베이스 위키(deep-wiki + VitePress 다중 페이지). Track A/B 와 섞지 말 것 |
| `docs/superpowers/plans/2026-08-26-report-builder.md` | 실행 계획. 발견된 결함이 해당 Phase 절에 반영돼 있다 |

`ReportSystem_HandOff.md` 는 `HANDOFF-report-system.md` 와 동일 계열의 구판이다.

## 명령

```bash
npm run doctor           # 이 컴퓨터에 무엇이 있고 무엇이 없는지. 필수가 없으면 exit 1
npm test                 # pretest 가 scripts/lib.mjs 로 src/ 를 .tmp/lib.mjs 로 번들한 뒤 node --test
npm run typecheck        # tsc --noEmit (이 저장소의 src/ 만)
node --test test/svg.test.mjs                                # 단일 파일
node --test --test-name-pattern="접두사" test/svg.test.mjs    # 단일 테스트
```

**함정 — `node --test test/` 는 Node v25.8.0 에서 죽는다.** 디렉토리 인자를 테스트 파일로 취급해
`Cannot find module '.../test'` 를 낸다. **인자 없는 `node --test`** 를 쓰면 Node 가 알아서 탐색한다.

**테스트가 `src/` 를 직접 import 하지 않는다.** `node --test` 는 JSX 를 해석하지 못하므로
`scripts/lib.mjs` 가 esbuild 로 `.tmp/lib.mjs` 를 만들고 `test/components.test.mjs` 가 그것을 import 한다.
`src/` 를 고치고 테스트가 옛 동작을 보이면 `.tmp/lib.mjs` 가 낡은 것이다 — `npm test` 로 다시 돌린다.

### mode 별 진입점 — 2026-08-29 분리

`bin/` 에 진입점이 네 개다. 전부 PATH 에 잡힌다 (`~/.zshrc:211`).

| 진입점 | Mode | 명령 | 하는 일 |
|---|---|---|---|
| `report-wiki` | 1 | `prep` · `build` · `check` | 코드베이스 위키. 세 명령이 **실제로 돈다**(`bin/report-wiki`). 사이의 LLM 자리는 `codebase-terms-survey` 스킬(전수조사)과 deep-wiki 스킬(산문)이 맡고, `codegraph/run_mode1.py` 가 그 전부를 한 번에 돌리며 잰다 |
| `report-term` | 1.5 | `collect` · `grade` · `emit` | 용어 이해도 점검. Plan 이 요구하는 용어를 모으고, 객관식 답안을 채점해, 학습 노트와 용어집 DB 를 낸다 |
| `report-spec` | 2 | `init` · `build` · `check` | 설계 검토 보고서 |
| `report` | — | (`report-spec` 과 같음) | **옛 이름.** `report-spec` 으로 위임하고 stderr 에 알림 한 줄을 낸다. stdout 은 동일 |

`report-spec` 과 `report-term` 은 `scripts/dispatch.mjs` 의 `runDispatch` 를 공유하고, 각자 자기 명령표만 갖는다.
`report-wiki` 는 자리 표시자라 `runDispatch` 를 쓰지 않고, `report` 는 `report-spec` 을 자식 프로세스로 실행한다(`spawnSync`).

보고서 쪽 명령은 **보고서가 있는 저장소의 스펙 디렉토리에서** 실행한다:

```bash
cd <프로젝트>                      # specs/ 가 있는 저장소
report-spec init                   # 보고서가 없는 spec 을 날짜 내림차순으로 나열, exit 1
report-spec init <slug>            # 대응 specs/YYYY-MM-DD-<slug>-design.md 가 있어야 스켈레톤 생성
cd specs/<slug> && report-spec build   # → out/report.html
report-spec check                      # script 수 · tsc · 링크 무결성 · 용어집 대조(경고) · builderVersion
```

용어 이해도 점검은 Plan 하나를 놓고 돈다. 사람에게 묻는 절차는 CLI 가 아니라 `term-benchmark` 스킬이 맡는다:

```bash
report-term collect <plan.md> [terms-db.json]   # → term-candidates.json
#   (LLM 이 questions.json 을 내고, 실행기가 정답을 뺀 기입란 answer-sheet.json 을 깐다)
#   (사람 또는 스킬이 칸마다 UserAns 에 보기 번호를 적어 answers.json 으로 둔다)
report-term grade answers.json questions.json   # → term-grades.json  확실/모름
report-term emit term-grades.json               # → terms.json + term-study-note.md
```

## 경로 변수 — 기계마다 다른 경로를 적지 않는다

**이 저장소는 공개된다.** 홈 아래 경로를 문서·코드·커밋에 그대로 적지 않고 변수 이름을 쓴다 —
`$REPO_ROOT` · `$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO` · `REPORT_PYTHON`.
**전체 표와 골든 상수의 함정은 [`codegraph/CLAUDE.md`](codegraph/CLAUDE.md) 의 "경로 변수" 절에 있다.**

`test/docs-citations.test.mjs` 가 컨텍스트 문서의 인용을 검사하며 `$` 로 시작하는 경로는
바깥 저장소로 보고 건너뛴다. 그 규약을 어기면 게이트에 걸린다.

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
$REPO_ROOT             <프로젝트>/specs/<slug>/
  bin/report-spec   디스패치만            data.ts      결정 데이터만. builderVersion 포함
  src/components/   읽기 전용             report.tsx   서사·옵션표·판정 등 나머지 전부
  src/theme.css     옛 출력에서 추출+B1패치 (tsconfig.json)  check 가 ROOT 에 임시 생성
  scripts/build.mjs esbuild→RTSM→조립     (out/report.html)  git 제외 — 재생성
  scripts/check.mjs 기계 검사 규칙
```

## 확정된 스택 (변경 금지)

| 축 | 결정 |
|---|---|
| 위치 | `$REPO_ROOT` 고정 경로. `bin` 을 PATH 에 추가 |
| 트랜스파일 | **esbuild** |
| 렌더 | **React `renderToStaticMarkup`** — 마크업은 템플릿 엔진으로만. **단 용어 그래프 런타임 1개는 산출물에 실린다**(아래) |
| 타입 | props 타입 정의만. `tsc --noEmit` |
| 단일 파일화 | **Node 문자열 조립** (번들러의 CSS 파이프라인조차 불필요) |
| 확대 UX | 다이어그램은 **CSS 체크박스 토글, JavaScript 0줄**. 용어 그래프는 런타임 스크립트 (아래) |
| UI / 상태 | **React 훅은 여전히 쓰지 않는다.** 클라이언트 상태는 용어 그래프 안에만 있다 |

### 산출물 불변식 (기계 검사 대상)

**빌드된 `report.html` 에 `<script>` 태그가 1개를 초과하면 잘못된 것이다.**
`grep -c '<script' out/report.html` 로 검사한다.

**예산 1칸은 2026-08-29 에 용어 그래프 런타임이 가져갔다.** `data.ts` 에 `terms` 가 있을 때만
`scripts/build.mjs` 가 `src/runtime/term-graph.ts` 를 번들해 넣는다. 용어집이 없는 보고서는
여전히 `<script>` 0개다. **예산이 다 찼으므로 새 런타임 코드를 넣으려면 이 번들 안에 합쳐야 한다.**

## 두 트랙과 강제 순서 (Track A/B)

```
B1 (완료·육안 판정됨) → B2 (기각) → A1 (취소)
  → B3~B5 (B3·B4 완료, B5 취소) → A2~A4 (A1 취소로 무기한 보류)
```

실행 세션은 B2·A1 을 건너뛰고 B3~B5 로 갔다(B2 는 이후 기각). 둘 다 완료 조건이 **사용자 판정**이라 코드 경로를 막지
않았기 때문이다. 되돌릴 수 있는 이탈이지만 문서의 명시적 순서를 거스른 것은 사실이다.

**기각·취소된 것에 착수하지 마라.** 사유와 되살릴 조건은 전부
[`docs/decisions/`](docs/decisions/README.md) 에 있다 — Phase 2·3·6 과 D축 보류.
계획서의 해당 절 체크박스는 유효하지 않다.

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

`번복기록/` 의 분석 보고서들은 spec 에 딸리지 않고, 수용 판정란이 없고, before/after 쌍이 아니라
현황 그래프 한 장을 쓴다. **현재 `report-spec init` 은 대응 `*-design.md` 를 요구하므로 이 장르를 구조적으로
배제한다.** 그래도 **지금 두 번째 mode 를 추가하지 말 것** — 실제로 그 장르의 보고서를 쓸 일이
생기기 전에는 소비자가 0이고, mode 축 도입은 거울 함정이다. 컴포넌트 후보로 횟수와 함께 기록만 한다.

스킬 원본은 `~/.claude/skills/<이름>/SKILL.md`(단 `codebase-terms-survey` 는 저장소 `.agents/skills/` 가 원본이고 `.claude/skills/` 가 심볼릭 링크 — 2026-08-29 사용자 이전). Track A 대상은 `confidence-and-sourcing`,
`design-decision-discipline`, `architecture-design-workflow` 이고, Track B 는 `graphviz-class-diagram` 과
`spec-review-dashboard` 를 참조한다. ~~B2 는 `spec-review-dashboard` 의 개정이 된다.~~ **B2 기각으로 이 개정 계획도 함께 소멸했다** — 다만 그 스킬은 2026-08-28 에 report-builder 파이프라인 기준으로 따로 포팅됐다.

## 혼자 정하지 말 것 (미결정)

- N값(지연 승격 커밋 수) — 근거 없는 임의값 금지
- D 점수 구간 경계 — A1 취소로 판단 근거가 사라졌다. D축을 되살릴 때 함께 정한다
- `[잠정됨]` 이라는 이름과 그 적용 범위
- `data.ts` 의 D축 필드 포함 여부 (D축 자체가 보류라 함께 잠겨 있다)

**해소됨:** "콘솔 에러 0건" 검사는 넣지 않기로 확정(2026-08-28) — `<script>` 0개라 잡을 것이 없다.

## 함정

- **거울 함정.** 과잉 설계를 잡는 도구를 만들면서 그 도구를 과잉 설계하는 것. `d-axis.mjs` 는 지표 3개를
  계산하는 스크립트다. 플러그인 구조·지표 레지스트리·추상 인터페이스가 나오면 그 자체가 이 작업이 잡으려는
  실패다. 구현자 1, 소비자 1이면 인터페이스를 만들지 마라.
- **지표 증식 유혹.** D축은 3종 고정. 좋은 아이디어가 떠올라도 넣지 말고 **기록만 하고 사용자에게 보고**하라.
- **조기 성공 선언.** 표본이 5~10개면 그 정도로는 아무것도 증명되지 않는다.
  **"검증됨" 이라고 쓰지 말 것.** 목표는 "명백한 반례가 없는가" 수준의 sanity check 이다.
- **합성 데이터만으로 검증하지 말 것.** 백틱 제목 결함(위)은 서브에이전트가 실제 저장소 데이터를 확인하다
  발견했다. 합성 테스트만 썼으면 안 나왔다.

## 작업 규약

`.claude/CLAUDE.md` 의 13개 체크포인트가 이 저장소에도 그대로 적용된다. 그 위에 추가되는 것:

- 확신도는 🔵/🟡/💭 + 정수. **🔵는 이번 세션에서 실제로 읽은 file:line 또는 실제로 돌린 명령의 출력만 인정.**
- 결정은 `[제안됨]` 으로 먼저 기록하고 검증 후 승격.
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 구조 신설 제안 시 `design-decision-discipline` §2.5 의 4항목을 공개하고 §2.7 의 축을 선언한다.
- **컴포넌트는 추가만 한다.** props 제거·의미 변경 금지. 컴포넌트 API 가 바뀌는 갱신마다 태그(`v1`, `v2`).
  옛 버전 빌드가 필요하면 `git worktree add /tmp/rb-v1 v1`.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.** 인계 문서 초안이 그 이유로 한 번 반려됐다.
- 커밋 메시지는 `personal-commit-messages` 스킬을 따른다 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).
