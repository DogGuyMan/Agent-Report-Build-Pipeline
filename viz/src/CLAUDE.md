# viz/src/ — 읽기 전용 React 컴포넌트

> 루트 나침반은 `../CLAUDE.md`. 이 문서는 **보고서 컴포넌트와 테마만** 다룬다.
> 빌드 배선은 `../viz/CLAUDE.md`.

## 무엇이 여기 있나

컴포넌트 **17개** 를 내보낸다(인계 문서가 지정한 11개 + `Page` `Section` `EvidenceNote` + 용어집 3종).
`theme.css` 는 옛 출력에서 추출한 뒤 B1 패치를 얹은 것이다.
`runtime/term-graph.ts` 하나만 **산출물에 실리는 클라이언트 코드**다.

**React 훅을 쓰지 않는다.** 클라이언트 상태는 용어 그래프 안에만 있고 그것은 d3 + 바닐라다.

## 컴포넌트 — 인계 문서의 예시를 그대로 쓰지 말 것

인계 문서 §B-4 의 예시 코드는 실제로 필요한 것과 다르다. **인계 문서보다 실측이 앞선다** — 여기서
실측이란 옛 출력을 읽어 확인한 것이고, 그것이 컴포넌트 설계의 *출발점*이 됐다. 지금 기준은
`viz/src/components/` 의 현재 구현이다.

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

## B1 — 다이어그램 가독성은 CSS 만으로 고쳐졌다

인계 문서가 예측한 결함(`.svg-wrap svg { max-width: 100% }` 가 `overflow-x: auto` 를 무력화해 원본
1961pt SVG 의 10pt 글꼴이 화면상 2.5px 로 축소)은 실재했고, 해결은 **인계 문서가 예상한 pan/zoom
스크립트가 아니라 체크박스 토글**이었다.

- `.zoom-toggle:checked ~ .diagram-grid` — 형제 결합자만 쓴다. 기본은 병치, 켜면 1열 + 원본 픽셀 + 스크롤.
- **`--svg-w` 가 이 복구의 급소다.** `width`/`height` 를 제거한 인라인 SVG 는 고유 크기가 없어 브라우저가
  300×150px 로 렌더한다. `viz/svg.mjs` 가 속성 제거 **직전에** pt 를 읽어 px(× 4/3)로 환산해 돌려주고,
  `BeforeAfter` 가 `.svg-wrap` 의 인라인 style 로 주입한다. CSS 커스텀 속성은 상속되므로 자식 `svg` 가 읽는다.
- 이 연결고리 중 하나라도 끊으면 "실제 크기" 모드가 조용히 죽는다.

## 용어집과 관계 그래프 — 2026-08-29 신설

**읽는 사람은 배경 지식이 없다고 가정한다.** 대상은 객체지향을 갓 배운 대학 1학년 수준이다.
`C-19`·`calls[]`·`PageRank` 같은 낱말이 정의 없이 나오면 그 보고서는 읽히지 않는다.

**정의는 `data.ts` 의 `terms` 배열 한 곳에만 쓴다.** 본문 인라인 참조도, 용어집 표도, 관계 그래프도
전부 그 배열에서 나온다. 용어가 여기저기 흩어지는 것을 구조로 막는다.

| 컴포넌트 | 하는 일 |
|---|---|
| `defineTerms(terms)` | 용어 목록을 묶어 인라인 참조 컴포넌트를 돌려준다. **전역 변수도 React 컨텍스트도 쓰지 않는다.** 2026-08-29 부터 빌드가 본문 용어를 **자동으로** 감싸므로 저자가 직접 쓸 일은 드물다 (`viz/wrap-terms.mjs`) |
| `<Glossary terms>` | 정의 전량을 **이해도 그룹 아코디언**(`<details>`, 모름 → 애매 → 확실 → 미측정, 모름만 열림)으로 보인다. 보고서 맨 앞에 놓는다 |
| `<TermGraph terms>` | 용어 관계를 그물로 그린다. 좌표 계산·드래그·확대·hover 는 런타임이 한다. **물리 상수는 `viz/src/runtime/term-graph.ts` 머리의 `KNOBS`** — 2026-08-29 사용자가 슬라이더로 육안 확정한 값(덩어리 사이 척력은 `REPEL_MAX_DIST` 밖 0, 덩어리 경계 사각형 충돌 `GROUP_PAD`, 상자 `BOUNDS_SCALE` 2.5). 다시 조정하려면 `<TermGraph terms tune />` 로 슬라이더 패널을 켠다(임시용, 산출물에 남기지 않는다) |

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
- 본문 인라인 참조의 hover 카드는 CSS(`:hover`/`:focus`)로 **뜨고**, **위치만** 런타임이 화면 기준(`position: fixed`)으로 옮긴다 — 표의 `.table-wrap`(overflow-x) · `.card`(overflow hidden)에 잘리던 것을 2026-08-29 에 고쳤다. 카드 내용: 갈래 · id · 이해도 배지 / 뜻 / 용례 `body`, 밑줄 끝 `?`. 아코디언은 `<details>` 라 스크립트 0. 런타임 번들 하나가 그래프와 카드 위치를 맡는다

## 이 모듈이 소유하는 것 (Owns)

`viz/src/**` — 컴포넌트 · `types.ts` · `theme.css` · `runtime/term-graph.ts`.
**소유하지 않는 것** — 대상 저장소의 `data.ts` 와 `report.tsx` 는 사람이 쓴 **원고**다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `viz/build.mjs` → 여기 | esbuild `alias` 로 `report-builder` · `/types` · `/svg` 를 푼다 |
| `viz/check.mjs` → 여기 | 임시 tsconfig 의 `paths` 로 같은 곳을 가리킨다 |
| 여기 → 다른 모듈 | **없다.** 컴포넌트는 아무것도 부르지 않는다 |

⚠ **런타임과 타입 검사가 서로 다른 경로를 탄다.** 한쪽만 고치면 다른 쪽이 깨진다 —
자세한 것은 [`../viz/CLAUDE.md`](../viz/CLAUDE.md) 의 "모듈 해결" 절.

## 흔한 변경 패턴 (Common modification patterns)

```bash
# 컴포넌트를 더한다 — 추가만 한다. props 제거·의미 변경 금지
$EDITOR viz/src/components/<이름>.tsx && $EDITOR viz/src/index.ts   # export 를 더한다
npm test && npm run typecheck

# 산출물 불변식을 확인한다
cd <프로젝트>/specs/<slug> && report-spec build
grep -c '<script' out/report.html     # 용어집 없으면 0, 있으면 1. 2 이상이면 잘못됐다
```

**보고서를 쓰다 반복 요소를 발견해도 그 자리에서 컴포넌트를 만들지 마라.**
보고서 끝에 `## 컴포넌트 후보` 절로 **반복 횟수와 함께** 보고만 하고 사후 일괄 처리한다.

## 비직관적인 것 (Gotchas)

- **Why — `--svg-w` 가 "실제 크기" 보기의 급소다.** `width`/`height` 를 제거한 인라인 SVG 는 고유
  크기가 없어 브라우저가 300×150px 로 렌더한다. 연결고리 하나만 끊겨도 조용히 죽는다.
- **Gotcha — 용어 데이터는 `data-terms` 속성으로 넘긴다.** `<script type="application/json">` 을
  쓰면 `countScripts` 가 2로 세어 불변식이 깨진다.
- **Note — 번들 코드 안의 `</script>` 문자열을 이스케이프한다.** 안 하면 HTML 파서가 조기 종료한다.
- **Why — D축 필드를 `types.ts` 에 넣지 않는다.** 평가 없이 보류된 상태다
  ([`../docs/decisions/0004-d-axis-on-hold.md`](../docs/decisions/0004-d-axis-on-hold.md)).
