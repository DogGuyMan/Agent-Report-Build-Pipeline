# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
| 커밋 / 태그 | 22개 (`794b17a`~`ea33069`) / `v1` |
| 테스트 | `npm test` 44개 전부 통과 |
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
| `report-wiki` | 1 | (없음) | 코드베이스 위키. **아직 Node 파이프라인이 없어 길잡이만 낸다.** 실제 흐름은 `codegraph/*.py` + deep-wiki 스킬 |
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
#   (스킬이 객관식으로 묻고 answers.json 을 만든다)
report-term grade answers.json                  # → term-grades.json  확실/애매/모름
report-term emit term-grades.json               # → terms.json + term-study-note.md
```

## 아키텍처 — 두 저장소에 걸쳐 있다는 것이 전부다

이 저장소는 렌더러이고, **보고서는 다른 저장소의 `<프로젝트>/specs/<slug>/` 에 산다.** 여기서 나오는
비직관적 결정이 코드 곳곳에 박혀 있다.

**경로 실측 (2026-08-28).** 루트는 `$REPO_ROOT` 다. `~/report-builder` 는 **존재하지 않는다** —
이 문서의 이전 판이 그렇게 적어 두 세션이 헛짚었다. 근거: `~/.zshrc:211` 의
`export PATH="$HOME/LLM-Tools/report-builder/bin:$PATH"` (다른 셸 설정 파일에는 등록 없음),
`readlink -f "$(which report)"` → `$REPO_ROOT/bin/report`.

**자기호스팅은 예외가 아니라 의도다.** `report` 는 PATH 에 등록된 툴 바이너리이므로 어느 저장소에서든
부를 수 있고, 이 저장소 자신의 계획서도 검토 대상이 된다. 실제로 `specs/llm-load-reduction/` 이
여기 안에 있다 — Track C 계획을 Track A/B 도구로 검토하는 자기참조 구조다. 옮기지 말 것.

```
$REPO_ROOT             <프로젝트>/specs/<slug>/
  bin/report-spec   디스패치만            data.ts      결정 데이터만. builderVersion 포함
  src/components/   읽기 전용             report.tsx   서사·옵션표·판정 등 나머지 전부
  src/theme.css     옛 출력에서 추출+B1패치 (tsconfig.json)  check 가 ROOT 에 임시 생성
  scripts/build.mjs esbuild→RTSM→조립     (out/report.html)  git 제외 — 재생성
  scripts/check.mjs 기계 검사 규칙
```

### 모듈 해결이 런타임과 타입 검사에서 서로 다른 경로를 탄다

보고서는 `report-builder` / `report-builder/types` / `report-builder/svg` 를 import 하지만 그 저장소의
`node_modules` 에는 아무것도 없다. 그래서 두 경로를 따로 뚫었다. **한쪽만 고치면 다른 쪽이 깨진다.**

| | 담당 | 가리키는 곳 |
|---|---|---|
| 런타임 | `scripts/build.mjs` 의 esbuild `alias` | `src/index.ts` · `src/types.ts` · **`scripts/svg.mjs`** |
| 타입 | `scripts/check.mjs` 가 **임시 생성**하는 tsconfig 의 `paths` | 같음. 단 svg 는 **`scripts/svg.d.mts`** (선언 파일) |

`paths` 가 `.mjs` 를 직접 가리키면 TypeScript 가 형제 `.d.mts` 를 찾지 않아 `TS7016` 이 난다.
같은 이유로 임시 tsconfig 는 `typeRoots: [<ROOT>/node_modules/@types]` 를 명시한다 —
기본 `typeRoots` 는 tsconfig 파일 위치 기준이라 `@types/node` 를 못 찾고 `TS2688` 이 난다.

**타입 검사용 tsconfig 는 대상 저장소에 남기지 않는다 (2026-08-28 변경).** `check.mjs` 가 검사 직전에
`<ROOT>/.tmp-report-tsconfig.json` 을 만들고 끝나면 지운다. 이유는 성격 구분이다 — `data.ts` 와
`report.tsx` 는 결정 데이터와 본문, 즉 **원고**라서 `.md`/`.html` 과 같은 자격으로 대상 저장소에 산다.
반면 tsconfig 는 보고서 고유값이 **0건**인 순수 보일러플레이트라 남길 이유가 없다.
검사 대상은 `include` 글로브가 아니라 `files` 에 **절대경로로 열거**한다 — 글로브는 tsconfig 위치
기준으로 해석되는데 그 파일은 `ROOT` 에 있고 검사 대상은 `cwd` 라 서로 다르다.

**빌드 임시 번들(`.tmp-report.mjs`)은 `cwd` 가 아니라 `ROOT` 에 쓴다.** 동적 `import()` 는 파일 위치
기준으로 `react/jsx-runtime` 을 찾으므로, 외부 저장소에 두면 `ERR_MODULE_NOT_FOUND` 로 즉사한다.

### `scripts/*.mjs` 는 직접 실행 가드를 둔다 — 규약

```js
if (process.argv[1] && process.argv[1].endsWith("check.mjs")) { /* CLI 본체 */ }
```

import 시에는 순수 함수만 노출한다. 가드가 없으면 테스트가 import 하는 순간 `process.exit()` 가
호출돼 러너 자체가 죽는다(`init.mjs` 에서 실제로 발생). 새 스크립트도 이 패턴을 따른다.

### 렌더 경로

`report.tsx` → esbuild 트랜스파일 → 동적 import → `renderToStaticMarkup` → `<style>` 에 `theme.css`
문자열 삽입 → `out/report.html`. **React 는 빌드 시점 Node 에만 존재하고 산출물은 순수 HTML+CSS 다.**

**용어 자동 참조 (2026-08-29 신설).** `data.ts` 에 `terms` 가 있으면 `renderToStaticMarkup` 결과에 `scripts/wrap-terms.mjs` 를
한 번 더 통과시켜 본문 글자에 나오는 용어 id 의 **모든 등장**을 `TermRef` 마크업으로 감싼다(마크업은 그 컴포넌트를 실제로 렌더한
문자열 — 출처 하나). 건너뛰는 곳: 이미 감싼 곳 · 카드 안 · `.mono` `<code>` `<pre>` · `h1~h3` · `th` · `summary` · 용어집 · 관계도 · SVG.
긴 id 먼저, ASCII id 는 낱말 경계, 한글 id 는 조사까지. **저자는 `<T id>` 를 심지 않는다** — `defineTerms` 는 남아 있으나 선택이다.
왜 여기인가: 본문 산문 대부분이 props 로 들어가 React 트리 순회로는 닿지 않고, 전역·컨텍스트는 쓰지 않기 때문이다.

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

## B1 — 다이어그램 가독성은 CSS 만으로 고쳐졌다

인계 문서가 예측한 결함(`.svg-wrap svg { max-width: 100% }` 가 `overflow-x: auto` 를 무력화해 원본
1961pt SVG 의 10pt 글꼴이 화면상 2.5px 로 축소)은 실재했고, 해결은 **인계 문서가 예상한 pan/zoom
스크립트가 아니라 체크박스 토글**이었다.

- `.zoom-toggle:checked ~ .diagram-grid` — 형제 결합자만 쓴다. 기본은 병치, 켜면 1열 + 원본 픽셀 + 스크롤.
- **`--svg-w` 가 이 복구의 급소다.** `width`/`height` 를 제거한 인라인 SVG 는 고유 크기가 없어 브라우저가
  300×150px 로 렌더한다. `scripts/svg.mjs` 가 속성 제거 **직전에** pt 를 읽어 px(× 4/3)로 환산해 돌려주고,
  `BeforeAfter` 가 `.svg-wrap` 의 인라인 style 로 주입한다. CSS 커스텀 속성은 상속되므로 자식 `svg` 가 읽는다.
- 이 연결고리 중 하나라도 끊으면 "실제 크기" 모드가 조용히 죽는다.

### Graphviz SVG 인라인 규칙 (`scripts/svg.mjs`)

- `dot -Tsvg_inline` 사용 — `<?xml?>`·DOCTYPE 없이 나와 HTML 본문 삽입에 맞다.
- `width`/`height` 제거, `viewBox` 유지.
- **id 접두사를 붙인다.** 정의(`id="…"`)만이 아니라 `url(#…)` 과 `href`/`xlink:href` 참조까지 **세 곳을
  함께** 치환한다. 하나라도 빠지면 clipPath/marker 가 깨진다.
- **Mermaid/D3 로 대체하지 않는다.** `constraint=true/false` 분리가 Graphviz 에만 있고 그것이 의미축의 전제다.

## 컴포넌트 — 인계 문서의 예시를 그대로 쓰지 말 것

인계 문서 §B-4 의 예시 코드는 실제로 필요한 것과 다르다. **인계 문서보다 실측이 앞선다** — 여기서
실측이란 옛 출력을 읽어 확인한 것이고, 그것이 컴포넌트 설계의 *출발점*이 됐다. 지금 기준은
`src/components/` 의 현재 구현이다.

```tsx
// 인계 문서 예시 (틀림) — 이모지가 빠지고 anchor: number 는 "실측" 을 표현 못 한다
<span className={`conf-badge conf-${tier}`}>{anchor}</span>

// 실제 — tier 는 green|amber|red, anchor 는 number|string
<span className="conf-badge conf-green">🔵 99</span>
<span className="conf-badge conf-green">🔵 실측</span>
```

- **옛 출력에 tier 와 이모지가 어긋난 사례는 1건이다**(`conf-green` 인데 🟡 80).
  🔵 2026-08-28 실측 — 옛 출력 2개 파일의 `conf-badge` 24개를 전수 검사했다. 유일한 불일치는
  `2026-07-27-geometry-winding-ownership-design-review.html` 143번째 줄 하나이고,
  `matrix-rain-parameterization` 쪽은 0건이다. **이 문서와 계획서가 적어 둔 "2건" 은 틀린 수치였다.**
  사용자 결정: **저작 실수로 보고 `tier` 를 amber 로 정정한다.** 다만 옛 출력 파일 자체는 건드리지 않는다.
  `emoji` prop 은 그대로 남는다 — 옛 출력을 재현할 일이 생길 때를 위한 여지다.
- `StatusTag` 는 상태값이 아니라 **색 계열(`variant`) + 자유 문구(`children`)** 다. 클래스는
  `status-badge` 가 아니라 `status-tag` (전자는 헤더 전용 별개 클래스).
- `<Decision>` 은 별도 컴포넌트로 만들지 않고 `DecisionTable` 내부 행 렌더로 접었다 — 구현자 1·소비자 1.

**보고서를 쓰다 반복 요소를 발견해도 그 자리에서 컴포넌트를 만들지 말 것.** 보고서 끝에
`## 컴포넌트 후보` 절로 **반복 횟수와 함께** 보고만 하고 사후 일괄 처리한다.

## `report-spec init` 의 slug 검증

인계 문서에 없던 요구로, 사용자 지적에 의해 추가됐다. 초기 구현은 아무 문자열이나 받아 조용히 빈
디렉토리를 만들었다.

- 인자 없음 → 보고서 없는 spec 나열 후 exit 1
- 대응 `specs/*-<slug>-design.md` 없음 → 거부 + 비슷한 slug 제시 후 exit 1
- 찾음 → `date`(파일명) · `specName`(문서 첫 `# ` 제목) · `branch`(git) 자동 채움
- **`data.ts` 가 이미 있으면 spec 존재를 따지지 않는다** — 작업 중인 보고서를 spec 이름 변경으로 막으면 안 된다

**주입하는 네 값은 전부 `JSON.stringify` 로 이스케이프한다.** 실제 spec 제목에 백틱이 있어
(`` # `back_face` → `flip_faces` ``) 템플릿 리터럴에 그대로 꽂으면 `data.ts` 가 문법 오류가 된다.

## 두 트랙과 강제 순서 (Track A/B)

```
B1 (완료·육안 판정됨) → B2 (기각) → A1 (취소)
  → B3~B5 (B3·B4 완료, B5 취소) → A2~A4 (A1 취소로 무기한 보류)
```

실행 세션은 B2·A1 을 건너뛰고 B3~B5 로 갔다(B2 는 이후 기각). 둘 다 완료 조건이 **사용자 판정**이라 코드 경로를 막지
않았기 때문이다. 되돌릴 수 있는 이탈이지만 문서의 명시적 순서를 거스른 것은 사실이다.

### Phase 3 (A1 소급 검증) 취소 — 2026-08-29

**착수하지 말 것.** 계획서 `# Phase 3` 절의 체크박스 15개는 유효하지 않다.

A1 은 "D축 3지표가 과잉 설계를 실제로 예측하는가" 를 과거 결정들로 채점해 확인하려던 것이다.
**두 겹의 이유로 취소한다.**

1. **재료가 없다.** 소급 검증은 "결정" 과 "그 뒤의 결과(번복/존속)" 를 짝지어야 성립한다.
   이 저장소는 커밋 38개에 최초 커밋이 3일 전이고, 유일한 보고서(`llm-load-reduction`)의
   결정 6건은 전부 `[제안됨]` 이며 그 계획의 Task 1~8 중 **실행된 것이 0개**다
   (🔵 2026-08-29 실측 — `codegraph/measure_citation_origin.py`·`warmup.py` 부재 확인).
   번복된 것도 살아남은 것도 없어 채점표의 세로축이 통째로 비어 있다.
2. **재료를 구하는 방향이 후퇴다.** 계획서는 외부 Graphics 저장소의 설계 문서 60개를 표본으로
   지목한다. 그건 이 도구를 옛 프로젝트 이력에 다시 묶는 것이다 — 위 "방향" 절이 금지한 바로 그것.

**되살릴 조건.** **report-builder 로 쌓은 결정들**이 실제로 번복되거나 살아남은 이력이 충분히
생겼을 때. 그때는 외부 저장소를 볼 필요가 없다.

**딸린 결과 — D축은 평가 없이 보류된다.** A1 이 게이트였으므로 Phase 7(A2~A4)도 함께 잠긴다.
`src/types.ts` 에 D축 필드를 넣지 않는다는 규율은 그대로 유효하다.

### Phase 2 (B2) 기각 — 2026-08-28

**착수하지 말 것.** 계획서 `# Phase 2` 절의 체크박스 10개는 유효하지 않다.

B2 는 "설계 후보 비교를 표 대신 **소유권 미니 그래프**로 보여주면 판정이 빨라지는가" 를 한 사례로
시험하려던 것이다. 사용자 판단으로 **기각**했다.

조사에서 드러난 것 (🔵 2026-08-28 실측):

- **문제의식 자체는 살아 있었다.** 결정 *전* 후보 비교가 여전히 표뿐이라는 지적은 옛 출력 2건에서
  재확인됐고, **오늘 만든 `llm-load-reduction` 보고서의 D2 옵션표가 새 사례로 하나 더 늘었다.**
- **그러나 파일럿 사례의 근거 절반이 부식됐다.** 계획서는 `mPasses` 사례를 "정답이 `Material` 로
  확정돼 검증이 명확하다" 는 이유로 골랐는데, 그 정답이 가리킨 코드가 대상 저장소에 없다 —
  `src/material.h` 파일 부재, `ITechnique` 는 소스 히트 0건이며 git 이력에서도 소스에 들어온 적이 없다.
  패스 목록의 현재 소유자는 `PassIterator` 다(`src/render/pass_iterator.h:67`).
- **비교 대상 표가 아예 없었다.** Task 2.3 은 "같은 결정을 표로 읽었을 때와 비교" 하라는데,
  `Model` 대 `Material` 을 A/B 옵션표로 담은 문서가 어디에도 없다. 원본 보고서의 표는
  `항목/내용` 2열짜리 반박 근거 표이고, 옛 대시보드의 옵션표들은 **다른 결정 사안**이다.
  즉 계획서에 없는 추가 작업이 선행돼야 했다.

**되살릴 조건.** 결정 *전* 후보 비교를 그림으로 하고 싶은 요구가 다시 생기고, **정답이 이미 확정됐으며
그 결정의 옵션표가 이미 존재하는** 사례가 나타날 때. 그때는 표를 새로 만들 필요가 없어 비용이 다르다.

### Phase 6 (B5) 취소 — 2026-08-28

**착수하지 말 것.** 계획서 `# Phase 6` 절의 체크박스 17개는 유효하지 않다.

- **사유(사용자 판단)** — 대상이던 두 spec 은 **이미 종료된 작업**이라 보고서를 다시 만들 실익이 없다.
- **원래 목적 자체를 폐기했다.** Phase 6 이 답하려던 질문은 "컴포넌트가 옛 출력과 같은 마크업을 내는가"
  였다. 그 질문이 틀렸다 — **옛 출력은 열등판이고 새 컴포넌트가 그것을 따라갈 이유가 없다.**
  2026-08-28 에 이 대조를 테스트로 만들었다가 같은 날 폐기했다(`test/golden.test.mjs`, 삭제됨).
- **폐기 전에 관측된 차이는 기록해 둔다** — 결정 표 헤더 3곳(옛 `D#`/`Status`/`옵션 수` vs
  현재 `#`/`상태`/`옵션`)과 판정 푸터의 사유란·안내문이 다르다. **현재 컴포넌트가 기준이다.**
  옛 것은 헤더에 영어가 섞이고 `&nbsp;` 이스케이프 잔재가 있다.

- **A1 이 취소됐으므로 A2~A4 도 잠긴다.** D축 3지표의 예측력이 평가되지 않은 채로 남았다.
  **D축 관련 코드를 쓰지 않는다** — 이 규율은 A1 취소와 무관하게 유효하다.
- **사용자는 구현물보다 의사결정용 보고서를 먼저 받기를 선호한다.** 이 선호는 A1 밖에서도 유효하다.

### D축 (Track A) — 평가 없이 보류. `src/types.ts` 에 필드가 없다

| | E축 (증거 확신도) | D축 (결정 불확실성) |
|---|---|---|
| 묻는 것 | 내가 읽은 게 확실한가 (as-is) | 결론이 유일한가 (to-be) |
| 표기 | 🔵 / 🟡 / 💭 + 정수 배지 (기존) | **결정 행의 좌측 테두리 색** — 배지 아님 |
| 결속 행동 | 인용 첨부 / 도구 실행 | 옵션표 / 정렬 우선순위 |

두 축이 모두 3색이므로 **형태를 다르게 한다**(배지 vs 테두리). 이 분리로 `🔵 92 + D 높음`
= "근거는 확실하나 대안 검토는 필수" 가 표현 가능해지며, 그 표현 불가능성이 정확히 누수 지점이었다.

D축 3지표(고정, 증식 금지): **D1** 구현자·소비자 수(grep, **now만**, expected 무시) /
**D2** `expected` 주장에 file:line 또는 계획문서 D# 인용이 붙었는가 / **D3** 채택 트리거 문장이 있는가.
총점 0–5 → 0–1 초록(단일안 가능) / 2–3 노랑(옵션표 필수) / 4–5 빨강(옵션표 + "먼저 볼 것" 노출).

- **도구는 판정하지 않는다.** D축은 계산·정렬·병치만 한다. "D 4–5 → 제안 보류" 는 폐기됐다.
- **본문 결정 표는 원래 순서를 유지한다.** D 내림차순 정렬은 논리 서사를 무너뜨린다.
  상위 3개는 최상단 `<TriageBlock>` 에만 뽑는다.
- 상태 태그는 **한국어가 정본**(`[제안됨]`/`[잠정됨]`/`[검증됨]`). `proposed`/`accepted` 는 쓰지 않는다.
- 결정 로그 표는 **4컬럼이 정본**(`| # | 결정 | 상태 | 신뢰도 |`) + D축 컬럼 = 5컬럼.

**언젠가 A1 을 되살린다면 — D1 은 "그때의 grep" 이다.** 지금 grep 하면 결정 이후 추가분이 섞여 오염된다.
`git show <결정_커밋>:<파일경로>` 로 그날 스냅샷을 꺼내 세거나 `git log -S` 로 도입 시점을 특정한다.
**이 함정을 놓치면 소급 검증 전체가 무효다.**

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

스킬 원본은 `~/.claude/skills/<이름>/SKILL.md`. Track A 대상은 `confidence-and-sourcing`,
`design-decision-discipline`, `architecture-design-workflow` 이고, Track B 는 `graphviz-class-diagram` 과
`spec-review-dashboard` 를 참조한다. ~~B2 는 `spec-review-dashboard` 의 개정이 된다.~~ **B2 기각으로 이 개정 계획도 함께 소멸했다** — 다만 그 스킬은 2026-08-28 에 report-builder 파이프라인 기준으로 따로 포팅됐다.

## 혼자 정하지 말 것 (미결정)

- N값(지연 승격 커밋 수) — 근거 없는 임의값 금지
- D 점수 구간 경계 — A1 취소로 판단 근거가 사라졌다. D축을 되살릴 때 함께 정한다
- `[잠정됨]` 이라는 이름과 그 적용 범위
- `data.ts` 의 D축 필드 포함 여부 (D축 자체가 보류라 함께 잠겨 있다)

**해소됨:** "콘솔 에러 0건" 검사는 넣지 않기로 확정(2026-08-28) — `<script>` 0개라 잡을 것이 없다.

### 상시 예외 — 🟡 결정에 옵션표가 없는 경우

`confidence-and-sourcing` §1.5 는 🟡(60–89)에 옵션표를 **필수**로 규정한다. 그런데
`llm-load-reduction` 보고서의 D3(72)·D4(62)·D6(70) 세 건이 `optionCount: 0` 이다.
🔵 실측 — 그 설계 문서 1,063줄에 **기각된 대안의 서술이 없다**(`옵션`·`대안`·`기각` 검색 결과 무관한 1건뿐).

**방침(2026-08-28 확정): 채우지 말고 보고만 한다.** 없는 대안을 지어내면 옵션표가 장식이 된다.
보고서 안에 `## 이 보고서가 보유하지 못한 것` 절로 명시돼 있다.

**이건 저작 규율의 문제이지 도구의 결함이 아니다.** 닫는 방법은 하나 — spec 을 쓸 때 기각한 대안을
그 자리에서 적는 것. 앞으로 쌓을 관측 항목의 첫 번째로 기록해 둔다: **🟡 결정 중 옵션표를 가진 비율.**

## 기각안 — 다시 제안하기 전에 부활 트리거를 확인하라

영구 금지가 아니라 조건부다. 전체 표는 인계 문서 §3 에 있다.

| 기각안 | 부활 트리거 |
|---|---|
| Vite / vite-plugin-singlefile | 산출물이 진짜 클라이언트 상호작용(다중 위젯·상태·라우팅)을 가질 때 |
| `@hpcc-js/wasm` | graphviz 없는 환경에서 렌더해야 할 때 |
| svg-pan-zoom / panzoom | 핀치 줌·모바일 제스처가 필요할 때 (MIT 인 anvaka/panzoom 우선) |
| ~~React 훅 / 상태관리~~ | **2026-08-29 부활** — 용어 그래프가 클라이언트 상태를 갖는다. 단 **React 훅은 여전히 안 쓴다**. 런타임은 d3 + 바닐라다 |
| UI 라이브러리 / Tailwind | **없음.** LLM 이 유틸리티 클래스를 길게 써서 토큰이 오히려 늚 |
| 인용 자동 검증 | 규율 미준수 사례가 관측될 때. 현재는 잡을 것이 없다 |

## 용어집과 관계 그래프 — 2026-08-29 신설

**읽는 사람은 배경 지식이 없다고 가정한다.** 대상은 객체지향을 갓 배운 대학 1학년 수준이다.
`C-19`·`calls[]`·`PageRank` 같은 낱말이 정의 없이 나오면 그 보고서는 읽히지 않는다.

**정의는 `data.ts` 의 `terms` 배열 한 곳에만 쓴다.** 본문 인라인 참조도, 용어집 표도, 관계 그래프도
전부 그 배열에서 나온다. 용어가 여기저기 흩어지는 것을 구조로 막는다.

| 컴포넌트 | 하는 일 |
|---|---|
| `defineTerms(terms)` | 용어 목록을 묶어 인라인 참조 컴포넌트를 돌려준다. **전역 변수도 React 컨텍스트도 쓰지 않는다.** 2026-08-29 부터 빌드가 본문 용어를 **자동으로** 감싸므로 저자가 직접 쓸 일은 드물다 (`scripts/wrap-terms.mjs`) |
| `<Glossary terms>` | 정의 전량을 **이해도 그룹 아코디언**(`<details>`, 모름 → 애매 → 확실 → 미측정, 모름만 열림)으로 보인다. 보고서 맨 앞에 놓는다 |
| `<TermGraph terms>` | 용어 관계를 그물로 그린다. 좌표 계산·드래그·확대·hover 는 런타임이 한다 |

### 왜 d3-force + SVG 인가 — 다른 것을 다시 제안하기 전에 읽을 것

조사 문서(`docs/handoffs/compass_artifact_*.md`)가 **자기 임계값**을 이렇게 적어 뒀다 —
"노드 **2천 미만이면 d3+SVG/Canvas 로 충분**; 2천~2만이면 WebGL; 2만 이상이면 GPU 시뮬레이션".

**용어집은 노드 수십 개다.** 임계값보다 두 자릿수 아래다. 🔵 실측 번들 크기(esbuild `--minify`):

| 조합 | 최소화 후 |
|---|---|
| `d3-force` 만 | 13,796 바이트 |
| `d3-force`+`d3-zoom`+`d3-drag`+`d3-selection` (**채택**) | 62,232 바이트 |
| `pixi.js` · `cytoscape` · `@cosmos.gl/graph` (패키지) | 74MB · 5.7MB · 4.7MB |

**PixiJS·WebGL·GPU 를 여기 들이는 것은 거울 함정이다** — 용어를 설명하려고 물리 엔진을 얹는 것이 된다.
조사 문서가 PixiJS 를 권하는 대목은 "Obsidian 룩앤필 재현" 과 "그래픽스 포트폴리오" 목적이고,
이 도구의 목적이 아니다.

### 구현상 급소

- **데이터는 `data-terms` 속성으로 넘긴다.** `<script type="application/json">` 을 쓰면
  `countScripts` 가 2로 세어 불변식이 깨진다
- **런타임은 `terms` 가 있을 때만 번들된다.** 안 쓰는 보고서가 65KB 를 물지 않게
- **`</script>` 문자열을 이스케이프한다.** 번들 코드 안에 그 문자열이 있으면 HTML 파서가 조기 종료한다
- 본문 인라인 참조의 hover 카드는 **CSS 만으로** 뜬다(갈래 · id · 이해도 배지 / 뜻 / 용례 `body`, 밑줄 끝 `?`). 아코디언도 `<details>` 라 스크립트 0. 스크립트는 그래프에만 쓰인다

### `report-spec check` 의 용어 대조 — 경고이지 실패가 아니다

본문에 식별자 꼴 낱말이 있는데 `terms` 에 없으면 목록을 띄운다. 잡는 꼴은 셋뿐이다 —
결정 코드(`C-19`·`U5`·`M4`), 산출물 파일명(`*.json`), 배열 필드(`calls[]`).
자연어 용어(`WarmUp`·`PageRank`)는 기계가 가릴 수 없어 **저자가 직접 넣어야 한다.**
실패시키지 않는 이유는 탐지 규칙이 오탐을 낼 수 있어서다.

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
