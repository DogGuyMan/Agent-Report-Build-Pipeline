---
name: spec-review-dashboard
description: Use when a Plan/Spec draft is ready and the user needs to make an acceptance call on it — spec review requests, "spec 검토 대시보드", "플랜 HTML로 보여줘", "설계 검토 보고서", "확신도 보고서 만들어줘", or as the natural companion artifact whenever architecture-design-workflow finishes a Decision Log. Also trigger whenever a design document needs to become a scannable HTML so a human can approve/hold/reverse (승인/보류/번복) it instead of reading prose end-to-end. Authors the report through the report-builder pipeline (report init → build → check) — never a hand-written HTML file, never a narrative summary.
---

# Spec Review Dashboard

Plan/Spec 을 **사용자가 수용 판정을 내리기 좋은 계기판**으로 압축한다. 산문 대신 표·배지·다이어그램.
판정 자체는 항상 사용자 몫.

**이 스킬은 HTML 을 손으로 쓰지 않는다.** `report-builder` 파이프라인에 `data.ts` + `report.tsx` 를
저작하고 `report build` 가 HTML 을 조립한다. 구판의 `assets/template.html` 복사·`{{PLACEHOLDER}}`
치환 방식은 **폐기됐다** — 컴포넌트와 `theme.css` 가 그 자리를 대신한다.

## When to use

- "spec 검토 대시보드 만들어줘", "플랜 HTML로 보여줘", "설계 검토 보고서", "확신도 보고서"
- `architecture-design-workflow` 가 Decision Log 를 산출한 직후 (동반 산출)
- 사용자가 승인/보류/번복 판정을 내려야 하는 국면

## 전제 — 하나라도 없으면 착수하지 않는다

| 전제 | 확인 방법 | 실패 시 |
|---|---|---|
| `report` CLI | `which report` | PATH 미등록. 사용자에게 보고하고 중단 |
| 대응 spec 문서 | `specs/YYYY-MM-DD-<slug>-design.md` | `report init` 이 거부한다. **slug 를 지어내지 말 것** |
| Before/After SVG | 아키텍처 변경 spec 인 경우 | **생성을 거부하고** 다이어그램을 먼저 만들라고 보고 |

렌더러 루트는 **`$REPO_ROOT`** 다
(`readlink -f "$(which report)"` 로 확인. `~/report-builder` 는 존재하지 않는다).
보고서는 **렌더러 저장소가 아니라 spec 이 있는 저장소**의 `specs/<slug>/` 에 산다.

## Workflow

1. **스켈레톤**
   ```bash
   cd <스펙 저장소>        # specs/ 가 있는 곳
   report init            # 인자 없이 → 보고서 없는 spec 을 날짜 내림차순 나열 후 exit 1
   report init <slug>     # data.ts · report.tsx · tsconfig.json 생성
   ```
   `date` · `specName`(spec 문서 첫 `# ` 제목) · `branch` 는 `init` 이 자동으로 채운다. 손대지 않는다.

2. **결정 데이터** — spec 의 Decision Log 에서 `D#` · 결정 문구 · Status · 확신도 앵커 · 옵션 수를
   뽑아 `data.ts` 의 `decisions[]` 에 옮긴다. **원문에서 읽은 값만 옮긴다.** 없는 결정을 지어내면
   대조가 무의미해진다.

3. **본문** — `report.tsx` 에 아래 블록을 **이 순서 그대로** 조립한다.

4. **다이어그램** — `inlineSvg` 로 SVG 를 읽어 `BeforeAfter` 에 넘긴다.
   ```tsx
   import { readFileSync } from "node:fs";
   import { inlineSvg } from "report-builder/svg";
   const before = inlineSvg(readFileSync("../<slug>-before.svg", "utf8"), "d1before");
   const after  = inlineSvg(readFileSync("../<slug>-after.svg",  "utf8"), "d1after");
   ```
   `idPrefix` 는 before/after 가 **서로 달라야 한다.** 같으면 clipPath·marker 가 충돌한다.

5. **빌드·검사**
   ```bash
   cd <스펙 저장소>/specs/<slug>
   report build      # → out/report.html
   report check      # <script> 수 · tsc --noEmit · 링크 무결성 · builderVersion
   ```

6. `report check` 가 실패하면 **산출물을 사용자에게 내밀지 않는다.** 통과 출력을 근거로 붙인다.

## 블록 구성 — 이 순서 그대로

| 블록 | 컴포넌트 | 비고 |
|---|---|---|
| (a) 헤더 | `<Page data={data}>` | specName·date·branch·slug 를 `data.ts` 에서 자동 렌더 |
| (a′) 용어집 | `<Glossary terms={data.terms} />` | **결정 요약보다 앞에.** 배경 지식 없는 독자가 먼저 읽는다 |
| (a″) 용어 관계도 | `<TermGraph terms={data.terms} />` | 그물 그래프. 드래그·확대·hover 는 런타임이 한다 |
| (b) 결정 요약 표 | `<DecisionTable decisions={data.decisions} />` | 컬럼 `# · 결정 · 확신도 · 상태 · 옵션` |
| (c) 옵션 비교표 | `<OptionTable columns rows>` | 추천 행만 `recommended: true` |
| (d) Before/After | `<BeforeAfter id before after legend>` | `inlineSvg` 경유 필수 |
| (e) Lock 정합표 | `<LockTable rows>` | `consistent` 일치 / `unrelated` 무관 / `conflicting` 상충 |
| (f) 신규 구조물 신고 | `<NewStructNote …>` | 있을 때만 |
| (g) 수용 판정 푸터 | `<VerdictFooter />` | **비워서 산출한다** |

결정 상세 절은 `<Section title="D0 …">` 로 연다 — **`title` 이 `D<숫자>` 로 시작해야 한다.**
`check.mjs` 의 링크 무결성 검사가 `data.ts` 의 `id` 와 이 제목을 1:1 로 대조한다
(`viz/check.mjs:21`). 어긋나면 "절이 없는 결정" / "결정이 없는 절" 로 실패한다.

## 컴포넌트 전량 17개 — 이 밖의 것을 쓰지 않는다

`import { … } from "report-builder"`

| 컴포넌트 | props |
|---|---|
| `Page` | `data: ReportData`, `children` |
| `Section` | `title: string`, `children` |
| `ConfBadge` | `conf: Conf` |
| `StatusTag` | `variant: "proposed"\|"accepted"\|"superseded"`, `children` |
| `DecisionTable` | `decisions: Decision[]` |
| `OptionTable` | `columns: string[]`, `rows: { cells: ReactNode[]; recommended: boolean }[]` |
| `LockTable` | `rows: { lockId; claim; verdict; note }[]` |
| `NewStructNote` | `kind`, `implementers: number`, `consumers: number`, `deletionTest`, `grepEvidence` |
| `Reversal` | `rev`, `previous`, `now`, `reason` |
| `Correction` | `target`, `correction` |
| `TriageBlock` | `items: { id; title; why }[]` |
| `EvidenceNote` | `measured: ReactNode[]`, `judged?: ReactNode[]` |
| `BeforeAfter` | `id`, `before: DiagramPanel`, `after: DiagramPanel`, `legend: LegendItem[]` |
| `VerdictFooter` | `note?: string` |
| `defineTerms` | `(terms: Term[]) => 인라인 참조 컴포넌트`. **2026-08-29 부터 선택** — `report-spec build` 가 본문의 용어를 자동으로 감싼다(`viz/wrap-terms.mjs`). 손으로 `<T id>` 를 심지 않는다 |
| `Glossary` | `terms: Term[]` — 이해도 그룹 아코디언(모름 → 애매 → 확실 → 미측정, 모름만 열림) |
| `TermGraph` | `terms: Term[]`, `height?: number` |

`Conf` = `{ tier: "green"|"amber"|"red"; anchor: number|string; emoji?: string }`.
`anchor` 는 정수가 기본이나 `"실측"` 같은 문자열도 정본 사례가 있어 허용된다.
`emoji` 는 tier 가 함의하는 기본값(🔵/🟡/💭)을 덮어쓴다 — **정본 재현 목적으로만 쓴다.**

`Term` = `{ id; label; short; body?; kind: "decision"|"artifact"|"concept"|"tool"; links?: string[] }`.
**정의는 `data.ts` 의 `terms` 배열 한 곳에만 쓴다.** 본문 인라인 참조·용어집 표·관계 그래프가
전부 그 배열에서 나온다. **본문 인라인 참조는 자동이다** — 본문에 용어 id 를 그냥 쓰면 빌드가 모든 등장을 term-ref(밑줄 + `?` + 카드)로
감싼다. 제목(h2) · 표 머리 · `.mono` · 용어집 · 관계도 · SVG 안은 건너뛴다.
**경로도 자동이다** — 본문에 `docs/handoffs/x.md:12` 처럼 경로를 쓰면 빌드가 실제 파일·폴더로 가는 `file://` 링크(새 탭)로 만든다.
없는 파일은 그대로 글자로 남는다. 다른 저장소의 산출물을 가리키려면 `data.ts` 에 `linkRoots: ["<절대경로 폴더>"]` 를 적는다. `short` 는 커서를 올렸을 때 뜨는 한 줄이고 `body` 는 용어집 표에만 나온다.
`links` 는 방향 없는 그물 간선이다 — 양쪽 끝이 모두 정의된 용어일 때만 그려진다.

**읽는 사람은 배경 지식이 없다고 가정한다.** 객체지향을 갓 배운 대학 1학년 눈높이로 `short` 와 `body` 를 쓴다.
`C-19`·`calls[]`·`PageRank` 같은 낱말이 정의 없이 나오면 그 보고서는 읽히지 않는다.

`StatusTag` 는 상태값이 아니라 **색 계열 + 자유 문구**다. 문구는 한국어가 정본
(`[제안됨]`/`[잠정됨]`/`[검증됨]`). `proposed`/`accepted` 를 화면 문구로 쓰지 않는다.

## Style rules (non-negotiable)

파이프라인이 **기계로 강제**하는 것 — 어길 수 없다:

- `<script>` 는 **1개까지.** `terms` 가 있으면 용어 그래프 런타임(d3-force, 약 65KB)이 그 한 칸을 쓴다.
  없으면 0개. **예산이 찼으므로 새 런타임은 `viz/src/runtime/term-graph.ts` 번들에 합쳐야 한다** (`report build` 가 초과 시 exit 1)
- 외부 리소스 0건 — `theme.css` 가 `<style>` 로 통째 삽입된다. 폰트·CDN 로드 경로 자체가 없다
- 라이트 단일 테마 — `theme.css` 가 정본. **다크모드를 만들지 않는다**

**사람이 지켜야 하는 것** — 검사가 잡아주지 않는다:

- **산문 문단 금지.** 설명은 spec 본문에 이미 있다. 대시보드는 계기판이지 축약본이 아니다
- **전체 1~2 스크린.** 스크롤 몇 번으로 끝나야 판정이 가능하다
- **이모지는 확신도 앵커 3종(🔵🟡💭)만.** 장식 이모지 금지
- **인라인 `style` · 신규 클래스 금지.** `theme.css` 에 정의된 47개 클래스 밖으로 나가지 않는다.
  유일한 예외가 `BeforeAfter` 의 `--svg-w` 주입이고 그건 컴포넌트가 이미 한다
- **에이전트가 채운 항목에는 출처를 박는다.** 옵션표에 spec 원문에 없는 안을 넣었다면 판정·출처 열로
  `기각(정본 §N)` / `채택(D#)` / `미검토 — 이 보고서가 추가` 처럼 **행마다 구분한다.** 출처 열 없이
  병기하면 독자가 무엇이 원문이고 무엇이 에이전트 것인지 구별할 수 없다
- **객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다.** 섞일 것 같으면 `EvidenceNote` 로 행을 가른다

## Common pitfalls

- **용어를 본문 여기저기서 즉석 정의** — 금지. `terms` 배열에만 쓴다. 본문에는 id 를 그대로 쓰면 빌드가 감싼다 — `<T id=…/>` 를 손으로 심지 않는다
- **`report check` 의 용어집 경고를 무시** — 본문에 식별자 꼴 낱말(`C-19`·`*.json`·`calls[]`)이 있는데
  `terms` 에 없으면 경고가 뜬다. 실패는 아니지만 **그 목록이 곧 빠진 정의 목록**이다. 자연어 용어(`WarmUp`)는
  기계가 못 잡으므로 저자가 직접 넣는다
- **판정 푸터를 AI 가 채움** — 절대 금지. `VerdictFooter` 는 항상 빈 채로 산출한다
- **다이어그램 없이 생성** — 아키텍처 변경 spec 인데 Before/After 가 없으면 생성을 거부하고 보고
- **Lock 정합표 생략** — 정본 spec 이 있는데 대조표 없이 산출 금지
  (`architecture-design-workflow` 의 lock-conformance table 을 그대로 옮겨온다)
- **확신도 등급을 여기서 재정의** — 정본은 `confidence-and-sourcing` §1.5 (🔵≥90 / 🟡60–89 / 💭<60).
  🔵 는 **이번 세션에서 읽은 file:line 또는 실제로 돌린 명령의 출력**만 인정한다
- **`--svg-w` 를 끊음** — `inlineSvg` 를 거치지 않고 SVG 문자열을 직접 넣으면 `width`/`height` 가
  제거된 SVG 가 고유 크기를 잃어 브라우저가 300×150px 로 렌더한다. "실제 크기" 토글이 조용히 죽는다
- **`Section title` 과 `data.ts` 의 `id` 불일치** — `report check` 가 잡지만, 잡히고 나서 고치면
  이미 사용자에게 잘못된 표를 보인 뒤다
- **보고서를 쓰다 컴포넌트를 즉석 신설** — 금지. 보고서 끝에 `## 컴포넌트 후보` 절로
  **반복 횟수와 함께** 보고만 하고 사후 일괄 처리한다. 컴포넌트는 **추가만** 한다(props 제거·의미 변경 금지)
- **거울 함정** — 과잉 설계를 잡는 보고서를 과잉 설계하는 것. 결정 3건짜리 spec 에 7블록을 다 채우지 않는다

## 아직 검증되지 않은 것 — "검증됨" 이라고 쓰지 말 것

- **옛 산출물(2026-07-27 자 HTML 2건)은 기준이 아니다.** 출발점일 뿐이다. 새 출력을 거기에 맞추려는
  시도는 후퇴다 — 2026-08-28 에 그 방향의 Phase 셋이 취소됐다. 현재 컴포넌트 출력이 기준이다
- **용어집이 실제 독자에게 읽히는지는 미검증이다.** Mode 1.5(용어 이해도 벤치마크)가 붙으면 `Term.mental`
  필드로 실측이 들어온다. 그전까지 용어 선정은 저자의 감이다
- **D축(결정 불확실성)은 도입 전이다.** `viz/src/types.ts` 에 필드가 없다. 소급 검증(A1)을 통과하기
  전까지 D축 컬럼·테두리색을 **만들지 않는다**
- `.status-badge` / `.status-dot` 은 `theme.css:25-27` 에 정의돼 있으나 **쓰는 컴포넌트가 없다**
  (헤더 전체 상태 배지 자리). 필요하면 컴포넌트 후보로 보고할 것 — 인라인으로 직접 쓰지 않는다
