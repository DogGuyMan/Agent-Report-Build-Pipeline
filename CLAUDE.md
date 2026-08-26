# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 저장소의 현재 상태 — 먼저 읽어라

**코드가 아직 하나도 없다.** 커밋 0개, `package.json` 없음, `node_modules` 없음.
존재하는 파일은 `.claude/CLAUDE.md`(행동 규율)와 `docs/handoffs/ReportSystem_HandOff.md`(설계 인계 문서) 둘뿐이다.

따라서 **빌드·린트·테스트 명령이 존재하지 않는다.** 아래 "명령" 절의 `report build` 등은 인계 문서가 정한 *구현 목표*이지 지금 실행 가능한 명령이 아니다. 없는 명령을 있는 것처럼 안내하지 말 것.

`docs/handoffs/ReportSystem_HandOff.md`가 이 저장소의 **유일한 사양 원본(single source of truth)** 이다. 작업 착수 전 반드시 통독한다.

## 무엇을 만드는 저장소인가

설계 검토 보고서(design review report)를 **단일 HTML 파일**로 렌더링하는 빌더다.

목적은 §0에 못박혀 있다 — **AI가 틀리지 않게 막는 것이 아니라, AI의 판단이 맞는지 틀린지를 사람이 시각적으로 빨리 판정하게 돕는 것.** 기능 추가를 망설일 때의 판단 기준은 "이게 사람의 판정 시간을 줄이는가" 하나다. 에이전트를 더 엄격하게 만드는 방향은 목적이 아니다.

## 두 트랙과 강제 순서

| | 내용 | 성격 |
|---|---|---|
| Track A | 확신도 체계에 **결정 불확실성(D축)** 추가 | 개념·규율 |
| Track B | 보고서 **렌더러 구축** | 인프라 |

```
B1 (다이어그램 가독성 수정) → B2 (Decision-gate mode 파일럿) → A1 (D축 소급 검증)
  → B3~B5 (렌더러 구축) → A2~A4 (스킬 패치, A1 통과 시에만)
```

이 순서에는 이유가 있다. 지키지 않으면 작업이 폐기된다.

- **B1이 1순위인 이유는 "짧아서"가 아니다.** 목적이 시각적 판정인데 현재 유일한 시각화(Before/After 다이어그램)가 글자 2.5px로 렌더돼 읽히지 않는다.
- **A1을 건너뛰고 A2로 가지 말 것.** D축 3지표가 과잉 설계를 예측하지 못하면 A2~A4는 전부 폐기 대상이다. **A1 완료 전에 D축 관련 코드를 쓰지 않는다.**
- A1의 산출물은 코드가 아니라 **문서**다. 사용자는 구현물보다 의사결정용 보고서를 먼저 받기를 선호한다.

## 확정된 스택 (변경 금지)

| 축 | 결정 |
|---|---|
| 위치 | `~/report-builder` 고정 경로. `bin`을 PATH에 추가 |
| 명령 | `report init <slug>` / `report build` / `report check` |
| 트랜스파일 | **esbuild** |
| 렌더 | **React `renderToStaticMarkup`** — 템플릿 엔진으로만 |
| 타입 | props 타입 정의만. `tsc --noEmit` |
| 단일 파일화 | **Node 문자열 조립 ~30줄** (번들러의 CSS 파이프라인조차 불필요) |
| pan/zoom | **CSS `transform` + 핸들러 30~50줄** |
| UI / 상태 | **없음. React 훅 한 개도 쓰지 않는다** |

React는 빌드 시점 Node에만 존재한다. `renderToStaticMarkup`은 HTML 문자열만 만들고, 산출물은 순수 HTML+CSS다.

### 산출물 불변식 (기계 검사 대상)

**빌드된 `report.html`에 `<script>` 태그가 pan/zoom 하나를 초과하면 잘못된 것이다.**
`grep -c '<script' out/report.html` 로 검사한다. 사람 판단이 필요 없다.

## 파일 구성 (목표 형태)

```
~/report-builder/              (git 저장소. 컴포넌트 API 변경 시 태그 v1, v2…)
  bin/report                   init / build / check 진입점
  src/components/              읽기 전용 — 에이전트가 열지 않음
  src/theme.css                기존 6.6KB 이식
  scripts/build.mjs            esbuild → renderToStaticMarkup → 문자열 조립
  scripts/check.mjs            검사 규칙
  scripts/d-axis.mjs           (Track A A2 — A1 통과 후)

<프로젝트>/specs/<slug>/       작업 디렉토리
  data.ts                      결정 데이터만. builderVersion 포함
  report.tsx                   서사·옵션표·판정 등 나머지 전부
  (out/report.html)            git 제외 — 재생성
```

**`data.ts`에는 결정만. 나머지는 전부 `report.tsx`.** git에는 소스만 커밋한다.

`slug`는 `2026-07-27-geometry-winding-ownership-design.md`의 `geometry-winding-ownership` 부분이며,
`architecture-design-workflow` 스킬의 `specs/YYYY-MM-DD-<topic>-design.md`에서 `<topic>` 자리와 같다.

### 컴포넌트 11개와 그 상한선

`<ConfBadge>` `<StatusTag>` `<DecisionTable>`/`<Decision>` `<OptionTable>` `<BeforeAfter>` `<LockTable>` `<NewStructNote>` `<VerdictFooter>` `<Reversal>` `<Correction>` `<TriageBlock>`

전형은 이 수준이다. **이보다 복잡해지면 잘못 가고 있는 것이다.**

```tsx
export function ConfBadge({ tier, anchor }: { tier: "blue"|"amber"|"red"; anchor: number }) {
  return <span className={`conf-badge conf-${tier}`}>{anchor}</span>;
}
```

**보고서를 쓰다 반복 요소를 발견해도 그 자리에서 컴포넌트를 만들지 말 것.** 보고서 끝에 `## 컴포넌트 후보` 절로 **반복 횟수와 함께** 보고만 하고 사후 일괄 처리한다.

## 참조 원본의 실제 위치 (인계 문서는 "경로 미확인"이라 적혀 있다 — 아래가 확인된 값)

정본 출력 형태 2건과 그 입력, 그리고 이 체계가 나온 원천 보고서는 **다른 저장소**에 있다:

```
$GRAPHICS_REPO/doc/
  superpowers/specs/2026-07-27-geometry-winding-ownership-design-review.html   ← 정본
  superpowers/specs/2026-07-27-matrix-rain-parameterization-design-review.html ← 대조용
  superpowers/specs/*-design.md                                                 ← 입력 형태
  superpowers/specs/*-{before,after}.{dot,svg,png}                              ← Graphviz 원본
  번복기록/AI설계판단오류-분석보고서.md                                          ← 체계의 원천
```

스킬 원본은 `~/.claude/skills/<이름>/SKILL.md`. Track A 대상은 `confidence-and-sourcing`,
`design-decision-discipline`, `architecture-design-workflow`이고, Track B는 `graphviz-class-diagram`과
`spec-review-dashboard`를 참조한다.

## 환경 — 실측 확인됨 (2026-08-26)

인계 문서 §6이 확인하라고 요구한 항목들. 아래는 이 저장소에서 실제로 실행해 얻은 값이다.

| 항목 | 실측값 | 함의 |
|---|---|---|
| Graphviz | **15.1.1** | 10.0.1 이상 → `dot -Tsvg_inline` 사용 가능 |
| Node | **v25.8.0** | — |
| TypeScript | **미설치** | `npx tsc`가 `tsc@2.0.4`를 받으러 감. 설치 필요 |
| esbuild | **미설치** | 설치 필요 |
| `~/report-builder/node_modules` | **없음** | 인계 문서 §B-3의 "사전 설치 완료 전제"는 **거짓**이다 |
| `spec-review-dashboard` 스킬 | **존재** | §6의 미확인 항목 해소. B2는 이 스킬의 개정이 된다 |
| 정본 HTML CSS 동일성 | **바이트 단위 동일 (6,599자, diff 0줄)** | 추출 가능한 안정 레이어 확인됨 |
| 정본 HTML `<script>` 수 | **0개** | 현재 클라이언트 런타임 0 |
| 원본 저장소 `.gitignore`의 `*.html` | **없음** (`html/`, `doxygen/html/` 디렉토리 패턴만) | 보고서 HTML 제외 규칙을 별도로 추가해야 한다 |

## B1이 고칠 결함 — 다이어그램이 2.5px로 렌더된다

```
.page      max-width 1120px, padding 36px  →  내용 폭 1048px
.diagram-grid  1fr 1fr, gap 16px           →  패널당 516px
.svg-wrap  padding 14px + 테두리           →  실제 SVG 폭 486px
원본 SVG 1961pt = 2615px → 축소율 18.6% → 노드 글꼴 10pt(13.3px)이 화면상 2.5px
```

`.svg-wrap`의 `overflow-x: auto`를 `svg { max-width: 100% }`가 무력화해서, 넘치는 대신 줄어든다.
**착수 전 브라우저로 열어 육안 확인할 것.** 위 수치는 계산으로만 나온 결론이다.

### Graphviz SVG 인라인 규칙

- `dot -Tsvg_inline` 사용 — `<?xml?>`·DOCTYPE 없이 나와 HTML 본문 삽입에 맞다.
- `width`/`height` 속성 제거, `viewBox`만 남기고 컨테이너 div로 감싼다.
- **id에 접두사를 붙인다.** 한 페이지에 SVG가 2개 이상이면 `graph0`, clipPath/marker id가 충돌해 렌더가 깨진다.
- 다크 모드는 `fill="black"` → `fill="var(--fg)"` 치환. 인라인 SVG여야 CSS 변수를 상속한다.
- **Mermaid/D3로 대체하지 않는다.** `constraint=true/false` 분리가 Graphviz에만 있고 그것이 의미축의 전제다.

## D축 (Track A) — A1 통과 전까지는 개념일 뿐

확신도를 두 축으로 분리한다. E축의 기존 규정은 **전부 그대로 유지**된다.

| | E축 (증거 확신도) | D축 (결정 불확실성) |
|---|---|---|
| 묻는 것 | 내가 읽은 게 확실한가 (as-is) | 결론이 유일한가 (to-be) |
| 표기 | 🔵 / 🟡 / 💭 + 정수 배지 (기존) | **결정 행의 좌측 테두리 색** — 배지 아님 |
| 결속 행동 | 인용 첨부 / 도구 실행 | 옵션표 / 정렬 우선순위 |

두 축이 모두 3색이므로 **형태를 다르게 한다**(배지 vs 테두리). 이 분리로 `🔵 92 + D 높음`
= "근거는 확실하나 대안 검토는 필수"가 표현 가능해지며, 그 표현 불가능성이 정확히 누수 지점이었다.

D축 3지표(고정, 증식 금지): **D1** 구현자·소비자 수(grep, **now만**, expected 무시) /
**D2** `expected` 주장에 file:line 또는 계획문서 D# 인용이 붙었는가 / **D3** 채택 트리거 문장이 있는가.
총점 0–5 → 0–1 초록(단일안 가능) / 2–3 노랑(옵션표 필수) / 4–5 빨강(옵션표 + "먼저 볼 것" 노출).

- **도구는 판정하지 않는다.** D축은 계산·정렬·병치만 하고 결론을 내지 않는다. "D 4–5 → 제안 보류"는 폐기됐다.
- **본문 결정 표는 원래 순서를 유지한다.** D 내림차순 정렬은 논리 서사를 무너뜨린다. 상위 3개는 최상단 `<TriageBlock>`에만 뽑는다.
- 상태 태그는 **한국어가 정본**(`[제안됨]`/`[잠정됨]`/`[검증됨]`). `proposed`/`accepted` 영어 표기는 쓰지 않는다.
- 결정 로그 표는 **4컬럼이 정본**(`| # | 결정 | 상태 | 신뢰도 |`) + D축 컬럼 = 5컬럼. 스킬 템플릿의 6컬럼은 실사용 흔적이 없으므로 스킬 쪽을 고친다.

### A1의 구현 함정 — D1은 "그때의 grep"이다

D1은 **결정 시점의 수**여야 한다. 지금 grep하면 그 이후 추가분이 섞여 결과가 오염된다.
`git show <결정_커밋>:<파일경로>`로 그날 스냅샷을 꺼내 세거나 `git log -S`로 도입 시점을 특정한다.
**이 함정을 놓치면 소급 검증 전체가 무효다.**

## 혼자 정하지 말 것 (미결정)

- N값(지연 승격 커밋 수) — 근거 없는 임의값 금지
- D 점수 구간 경계 — A1 결과에 따라 조정
- `[잠정됨]`이라는 이름과 그 적용 범위
- `data.ts`의 정확한 스키마 (D축 필드 포함 여부는 A1 결과에 달림)
- pan/zoom UX 형태 — 인라인 확대 / 모달 / 전체화면

## 기각안 — 다시 제안하기 전에 부활 트리거를 확인하라

영구 금지가 아니라 조건부다. 이유를 모르고 재제안하는 왕복을 막기 위한 목록이며, 전체 표는
인계 문서 §3에 있다.

| 기각안 | 부활 트리거 |
|---|---|
| Vite / vite-plugin-singlefile | 산출물이 진짜 클라이언트 상호작용(다중 위젯·상태·라우팅)을 가질 때 |
| `@hpcc-js/wasm` | graphviz 없는 환경에서 렌더해야 할 때 |
| svg-pan-zoom / panzoom | 핀치 줌·모바일 제스처가 필요할 때 (MIT인 anvaka/panzoom 우선) |
| React 훅 / 상태관리 | 산출물에 클라이언트 상태가 생길 때 |
| UI 라이브러리 / Tailwind | **없음.** LLM이 유틸리티 클래스를 길게 써서 토큰이 오히려 늚 |
| 인용 자동 검증 | 규율 미준수 사례가 관측될 때. 현재는 잡을 것이 없다 |

## 함정

- **거울 함정.** 과잉 설계를 잡는 도구를 만들면서 그 도구를 과잉 설계하는 것. `d-axis.mjs`는 지표 3개를 계산하는 스크립트다. 플러그인 구조·지표 레지스트리·추상 인터페이스가 나오면 그 자체가 이 작업이 잡으려는 실패다. 구현자 1, 소비자 1이면 인터페이스를 만들지 마라.
- **지표 증식 유혹.** D축은 3종 고정. 좋은 아이디어가 떠올라도 넣지 말고 **기록만 하고 사용자에게 보고**하라. 지표를 늘리면 검증 기준이 흔들려 검증 자체가 무의미해진다.
- **조기 성공 선언.** A1 표본은 5~10개일 것이고 그 정도로는 아무것도 증명되지 않는다. **"검증됨"이라고 쓰지 말 것.** 목표는 "명백한 반례가 없는가" 수준의 sanity check이다.

## 작업 규약

`.claude/CLAUDE.md`의 13개 체크포인트가 이 저장소에도 그대로 적용된다. 그 위에 추가되는 것:

- 확신도는 🔵/🟡/💭 + 정수. **🔵는 이번 세션에서 실제로 읽은 file:line만 인정.**
- 결정은 `[제안됨]`으로 먼저 기록하고 검증 후 승격.
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.
- 구조 신설 제안 시 `design-decision-discipline` §2.5의 4항목을 공개하고 §2.7의 축을 선언한다.
- 설명은 메커니즘 우선(원리 → API 세부), 한국어 + 영문 기술용어 병기.
- **약어와 압축 표현을 피할 것.** 인계 문서 초안이 그 이유로 한 번 반려됐다.
- 커밋 메시지는 `personal-commit-messages` 스킬을 따른다 (소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음).
