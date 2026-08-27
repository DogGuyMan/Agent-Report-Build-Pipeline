# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 저장소의 현재 상태 (2026-08-27 실측)

파이프라인 `report init` → `report build` → `report check` 가 실제 스펙 디렉토리에서 end-to-end 로 동작한다.

| 항목 | 실측값 |
|---|---|
| 커밋 / 태그 | 22개 (`794b17a`~`ea33069`) / `v1` |
| 테스트 | `npm test` 44개 전부 통과 |
| `tsc --noEmit` | 통과 |
| 컴포넌트 export | 14개 (인계 문서가 지정한 11개 + `Page` + `Section` + `EvidenceNote`) |
| 빌드 산출물 `<script>` | **0개** |
| Node / TypeScript / Graphviz | v25.8.0 / 7.0.2 / 15.1.1 |

**아직 "검증됨"이 아닌 것 — 이렇게 쓰지 말 것:**
- **B1 육안 판정** — 다이어그램 가독성 복구 코드는 있으나 사람이 브라우저로 확인하지 않았다.
- **정본 재현(Phase 6)** — 기존 정본 HTML 2건을 새 파이프라인으로 재생성해 시각 대조하는 단계가 미실시다. **컴포넌트가 정본과 같은 마크업을 내는지는 미검증이다.**
- **B2 판정 시간 가설**, **D축 예측력(A1)** — 둘 다 미착수.

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

보고서 쪽 명령은 **보고서가 있는 저장소의 스펙 디렉토리에서** 실행한다 (`bin` 을 PATH 에 추가):

```bash
cd <프로젝트>                 # specs/ 가 있는 저장소
report init                   # 보고서가 없는 spec 을 날짜 내림차순으로 나열, exit 1
report init <slug>            # 대응 specs/YYYY-MM-DD-<slug>-design.md 가 있어야 스켈레톤 생성
cd specs/<slug> && report build   # → out/report.html
report check                      # script 수 · tsc · 링크 무결성 · builderVersion
```

## 아키텍처 — 두 저장소에 걸쳐 있다는 것이 전부다

이 저장소는 렌더러이고, **보고서는 다른 저장소의 `<프로젝트>/specs/<slug>/` 에 산다.** 여기서 나오는
비직관적 결정이 코드 곳곳에 박혀 있다.

```
~/report-builder                       <프로젝트>/specs/<slug>/
  bin/report        디스패치만            data.ts      결정 데이터만. builderVersion 포함
  src/components/   읽기 전용             report.tsx   서사·옵션표·판정 등 나머지 전부
  src/theme.css     정본 추출 + B1 패치    tsconfig.json  init 이 생성
  scripts/build.mjs esbuild→RTSM→조립     (out/report.html)  git 제외 — 재생성
  scripts/check.mjs 기계 검사 규칙
```

### 모듈 해결이 런타임과 타입 검사에서 서로 다른 경로를 탄다

보고서는 `report-builder` / `report-builder/types` / `report-builder/svg` 를 import 하지만 그 저장소의
`node_modules` 에는 아무것도 없다. 그래서 두 경로를 따로 뚫었다. **한쪽만 고치면 다른 쪽이 깨진다.**

| | 담당 | 가리키는 곳 |
|---|---|---|
| 런타임 | `scripts/build.mjs` 의 esbuild `alias` | `src/index.ts` · `src/types.ts` · **`scripts/svg.mjs`** |
| 타입 | `scripts/init.mjs` 가 생성하는 tsconfig 의 `paths` | 같음. 단 svg 는 **`scripts/svg.d.mts`** (선언 파일) |

`paths` 가 `.mjs` 를 직접 가리키면 TypeScript 가 형제 `.d.mts` 를 찾지 않아 `TS7016` 이 난다.
같은 이유로 생성 tsconfig 는 `typeRoots: [<ROOT>/node_modules/@types]` 를 명시한다 —
기본 `typeRoots` 는 tsconfig 파일 위치(외부 저장소) 기준이라 `@types/node` 를 못 찾고 `TS2688` 이 난다.

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

## 확정된 스택 (변경 금지)

| 축 | 결정 |
|---|---|
| 위치 | `~/report-builder` 고정 경로. `bin` 을 PATH 에 추가 |
| 트랜스파일 | **esbuild** |
| 렌더 | **React `renderToStaticMarkup`** — 템플릿 엔진으로만 |
| 타입 | props 타입 정의만. `tsc --noEmit` |
| 단일 파일화 | **Node 문자열 조립** (번들러의 CSS 파이프라인조차 불필요) |
| 확대 UX | **CSS 체크박스 토글. JavaScript 0줄** (아래) |
| UI / 상태 | **없음. React 훅 한 개도 쓰지 않는다** |

### 산출물 불변식 (기계 검사 대상)

**빌드된 `report.html` 에 `<script>` 태그가 pan/zoom 하나를 초과하면 잘못된 것이다.**
`grep -c '<script' out/report.html` 로 검사한다. **현재 실측은 0개이므로 예산 1칸이 통째로 남아 있다.**

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

## 컴포넌트 — 정본이 인계 문서를 이긴다

인계 문서 §B-4 의 예시 코드는 정본 출력과 다르다. **정본 실측이 정본이다.**

```tsx
// 인계 문서 예시 (틀림) — 이모지가 빠지고 anchor: number 는 "실측" 을 표현 못 한다
<span className={`conf-badge conf-${tier}`}>{anchor}</span>

// 실제 — tier 는 green|amber|red, anchor 는 number|string
<span className="conf-badge conf-green">🔵 99</span>
<span className="conf-badge conf-green">🔵 실측</span>
```

- **정본에 tier 와 이모지가 어긋난 사례가 2건 있다**(`conf-green` 인데 🟡). 저작 실수로 보이나 확정할 수
  없어 임의로 고치지 않았다. `emoji` prop 으로 재정의를 허용해 두고 **사용자 결정 대기 중**이다.
  정본을 바꾸면 Phase 6 대조의 기준 자체가 흔들린다.
- `StatusTag` 는 상태값이 아니라 **색 계열(`variant`) + 자유 문구(`children`)** 다. 클래스는
  `status-badge` 가 아니라 `status-tag` (전자는 헤더 전용 별개 클래스).
- `<Decision>` 은 별도 컴포넌트로 만들지 않고 `DecisionTable` 내부 행 렌더로 접었다 — 구현자 1·소비자 1.

**보고서를 쓰다 반복 요소를 발견해도 그 자리에서 컴포넌트를 만들지 말 것.** 보고서 끝에
`## 컴포넌트 후보` 절로 **반복 횟수와 함께** 보고만 하고 사후 일괄 처리한다.

## `report init` 의 slug 검증

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
B1 (완료·육안 미판정) → B2 (미착수) → A1 (미착수, 생사 게이트)
  → B3~B5 (B3·B4 완료, B5 미완) → A2~A4 (A1 통과 시에만)
```

실행 세션은 B2·A1 을 건너뛰고 B3~B5 로 갔다. 둘 다 완료 조건이 **사용자 판정**이라 코드 경로를 막지
않았기 때문이다. 되돌릴 수 있는 이탈이지만 문서의 명시적 순서를 거스른 것은 사실이다.

- **A1 을 건너뛰고 A2 로 가지 말 것.** D축 3지표가 과잉 설계를 예측하지 못하면 A2~A4 는 전부 폐기 대상이다.
  **A1 완료 전에 D축 관련 코드를 쓰지 않는다.**
- **A1 의 산출물은 코드가 아니라 문서다.** 사용자는 구현물보다 의사결정용 보고서를 먼저 받기를 선호한다.

### D축 (Track A) — A1 통과 전까지는 개념일 뿐. `src/types.ts` 에 필드가 없다

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

**A1 의 구현 함정 — D1 은 "그때의 grep" 이다.** 지금 grep 하면 결정 이후 추가분이 섞여 오염된다.
`git show <결정_커밋>:<파일경로>` 로 그날 스냅샷을 꺼내 세거나 `git log -S` 로 도입 시점을 특정한다.
**이 함정을 놓치면 소급 검증 전체가 무효다.**

## 참조 원본의 실제 위치

정본 출력 2건과 그 입력, 이 체계의 원천 보고서는 **다른 저장소**에 있다:

```
$GRAPHICS_REPO/doc/
  superpowers/specs/2026-07-27-geometry-winding-ownership-design-review.html   ← 정본
  superpowers/specs/2026-07-27-matrix-rain-parameterization-design-review.html ← 대조용
  superpowers/specs/*-design.md                                                 ← 입력 형태
  superpowers/specs/*-{before,after}.{dot,svg,png}                              ← Graphviz 원본
  번복기록/                                    ← 체계의 원천 + **두 번째 보고서 장르**
```

`번복기록/` 의 분석 보고서들은 spec 에 딸리지 않고, 수용 판정란이 없고, before/after 쌍이 아니라
현황 그래프 한 장을 쓴다. **현재 `report init` 은 대응 `*-design.md` 를 요구하므로 이 장르를 구조적으로
배제한다.** A1 의 산출물이 정확히 이 장르다. 그래도 **지금 두 번째 mode 를 추가하지 말 것** — 첫 모드가
Phase 6 미검증이고, mode 축 도입은 거울 함정이다. 컴포넌트 후보로 횟수와 함께 기록만 한다.

스킬 원본은 `~/.claude/skills/<이름>/SKILL.md`. Track A 대상은 `confidence-and-sourcing`,
`design-decision-discipline`, `architecture-design-workflow` 이고, Track B 는 `graphviz-class-diagram` 과
`spec-review-dashboard` 를 참조한다. B2 는 `spec-review-dashboard` 의 개정이 된다.

## 혼자 정하지 말 것 (미결정)

- 정본의 tier/이모지 불일치 2건 — 재현할지 정정할지. **Phase 6 착수의 선결 조건**
- "콘솔 에러 0건" 검사 생략에 동의하는지 (`<script>` 0개라 잡을 것이 없다고 판단해 뺐다)
- N값(지연 승격 커밋 수) — 근거 없는 임의값 금지
- D 점수 구간 경계 — A1 결과에 따라 조정
- `[잠정됨]` 이라는 이름과 그 적용 범위
- `data.ts` 의 D축 필드 포함 여부

## 기각안 — 다시 제안하기 전에 부활 트리거를 확인하라

영구 금지가 아니라 조건부다. 전체 표는 인계 문서 §3 에 있다.

| 기각안 | 부활 트리거 |
|---|---|
| Vite / vite-plugin-singlefile | 산출물이 진짜 클라이언트 상호작용(다중 위젯·상태·라우팅)을 가질 때 |
| `@hpcc-js/wasm` | graphviz 없는 환경에서 렌더해야 할 때 |
| svg-pan-zoom / panzoom | 핀치 줌·모바일 제스처가 필요할 때 (MIT 인 anvaka/panzoom 우선) |
| React 훅 / 상태관리 | 산출물에 클라이언트 상태가 생길 때 |
| UI 라이브러리 / Tailwind | **없음.** LLM 이 유틸리티 클래스를 길게 써서 토큰이 오히려 늚 |
| 인용 자동 검증 | 규율 미준수 사례가 관측될 때. 현재는 잡을 것이 없다 |

## 함정

- **거울 함정.** 과잉 설계를 잡는 도구를 만들면서 그 도구를 과잉 설계하는 것. `d-axis.mjs` 는 지표 3개를
  계산하는 스크립트다. 플러그인 구조·지표 레지스트리·추상 인터페이스가 나오면 그 자체가 이 작업이 잡으려는
  실패다. 구현자 1, 소비자 1이면 인터페이스를 만들지 마라.
- **지표 증식 유혹.** D축은 3종 고정. 좋은 아이디어가 떠올라도 넣지 말고 **기록만 하고 사용자에게 보고**하라.
- **조기 성공 선언.** A1 표본은 5~10개일 것이고 그 정도로는 아무것도 증명되지 않는다.
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
