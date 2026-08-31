# viz/ — 시각축. 보이는 것을 만든다

> 루트 나침반은 `../CLAUDE.md`. 이 문서는 **산출물을 그리는 코드만** 다룬다.
> 결정론 기계는 `../machine/CLAUDE.md`, 러너는 `../runner/CLAUDE.md`, 컴포넌트는 `src/CLAUDE.md`.

**이 폴더의 기준은 언어가 아니라 성격이다** (2026-08-30 축 분리). `.py` 든 `.py` 든
**사람이 볼 것을 만들면** 여기 산다. 그래서 Graphviz 를 부르는 파이썬 셋이 여기 함께 있다.

## 무엇이 여기 있나

| 자리 | 하는 일 |
|---|---|
| `src/` | React 컴포넌트 17개 · `theme.css` · 브라우저 런타임 |
| `init.py` · `build.py` · `check.py` | Mode 2 (`report-spec`) 의 세 단계 |
| `svg.py` · `wrap_terms.py` · `link_paths.py` | 빌드 후처리 세 통과 |
| `lib.py` | `src/` 를 `.tmp/lib.mjs` 로 번들 (테스트용) |
| `render_classes.py` · `render_modules.py` | DOT → `dot -Tsvg/-Tpng` 로 다이어그램 |
| `demermaid.py` | 위키 산문의 Mermaid 를 사전 렌더 SVG 로 치환 |
| `patch-legacy.py` | Phase 1 잔재. 옛 HTML 을 깁던 일회용 |

**Why — 파이썬 셋이 왜 기계축이 아닌가.** 셋 다 하는 일이 `subprocess` 로 `dot` 또는 `mmdc` 를
불러 **그림을 굽는 것**이다. 코드 지도를 계산하지 않고 이미 계산된 것을 그린다.

### `viz/*.py` 는 직접 실행 가드를 둔다 — 규약

```js
if (process.argv[1] && process.argv[1].endsWith("check.py")) { /* CLI 본체 */ }
```

import 시에는 순수 함수만 노출한다. 가드가 없으면 테스트가 import 하는 순간 `process.exit()` 가
호출돼 러너 자체가 죽는다(`init.py` 에서 실제로 발생). 새 스크립트도 이 패턴을 따른다.

### 모듈 해결이 런타임과 타입 검사에서 서로 다른 경로를 탄다

보고서는 `report-builder` / `report-builder/types` / `report-builder/svg` 를 import 하지만 그 저장소의
`node_modules` 에는 아무것도 없다. 그래서 두 경로를 따로 뚫었다. **한쪽만 고치면 다른 쪽이 깨진다.**

| | 담당 | 가리키는 곳 |
|---|---|---|
| 런타임 | `viz/build.py` 의 esbuild `alias` | `viz/src/index.ts` · `viz/src/types.ts` · **`viz/svg.py`** |
| 타입 | `viz/check.py` 가 **임시 생성**하는 tsconfig 의 `paths` | 같음. 단 svg 는 **`viz/svg.d.mts`** (선언 파일) |

`paths` 가 `.py` 를 직접 가리키면 TypeScript 가 형제 `.d.mts` 를 찾지 않아 `TS7016` 이 난다.
같은 이유로 임시 tsconfig 는 `typeRoots: [<ROOT>/node_modules/@types]` 를 명시한다 —
기본 `typeRoots` 는 tsconfig 파일 위치 기준이라 `@types/node` 를 못 찾고 `TS2688` 이 난다.

**타입 검사용 tsconfig 는 대상 저장소에 남기지 않는다 (2026-08-28 변경).** `check.py` 가 검사 직전에
`<ROOT>/.tmp-report-tsconfig.json` 을 만들고 끝나면 지운다. 이유는 성격 구분이다 — `data.ts` 와
`report.tsx` 는 결정 데이터와 본문, 즉 **원고**라서 `.md`/`.html` 과 같은 자격으로 대상 저장소에 산다.
반면 tsconfig 는 보고서 고유값이 **0건**인 순수 보일러플레이트라 남길 이유가 없다.
검사 대상은 `include` 글로브가 아니라 `files` 에 **절대경로로 열거**한다 — 글로브는 tsconfig 위치
기준으로 해석되는데 그 파일은 `ROOT` 에 있고 검사 대상은 `cwd` 라 서로 다르다.

**빌드 임시 번들(`.tmp-report.py`)은 `cwd` 가 아니라 `ROOT` 에 쓴다.** 동적 `import()` 는 파일 위치
기준으로 `react/jsx-runtime` 을 찾으므로, 외부 저장소에 두면 `ERR_MODULE_NOT_FOUND` 로 즉사한다.

### 렌더 경로

`report.tsx` → esbuild 트랜스파일 → 동적 import → `renderToStaticMarkup` → `<style>` 에 `theme.css`
문자열 삽입 → `out/report.html`. **React 는 빌드 시점 Node 에만 존재하고 산출물은 순수 HTML+CSS 다.**

**용어 자동 참조 (2026-08-29 신설).** `data.ts` 에 `terms` 가 있으면 `renderToStaticMarkup` 결과에 `viz/wrap_terms.py` 를
한 번 더 통과시켜 본문 글자에 나오는 용어 id 의 **모든 등장**을 `TermRef` 마크업으로 감싼다(마크업은 그 컴포넌트를 실제로 렌더한
문자열 — 출처 하나). 건너뛰는 곳: 이미 감싼 곳 · 카드 안 · `.mono` `<code>` `<pre>` · `h1~h3` · `th` · `summary` · 용어집 · 관계도 · SVG.
긴 id 먼저, ASCII id 는 낱말 경계, 한글 id 는 조사까지. **저자는 `<T id>` 를 심지 않는다** — `defineTerms` 는 남아 있으나 선택이다.
왜 여기인가: 본문 산문 대부분이 props 로 들어가 React 트리 순회로는 닿지 않고, 전역·컨텍스트는 쓰지 않기 때문이다.

**경로 링크 (2026-08-29 신설).** 같은 자리에서 둘째 통과 `viz/link_paths.py` 가 본문(코드 글꼴 `.mono` **포함**)의 경로 꼴 낱말을
실제 로컬 파일·폴더의 `file://` 링크로 바꾼다(**새 탭**). 잡는 꼴 넷 — `docs/handoffs/` 아래 마크다운 이름,
`-design.md` 로 끝나는 이름, `HANDOFF-` 로 시작하는 이름, `facts/` 아래 글로브. 각각 뒤에 `:줄번호` 가 붙어도 된다.
(이 문단에 그 꼴을 **실물로 적지 않는다** — 적으면 인용 검사기가 진짜 인용으로 오인한다. `test/test_docs_citations.py` 참조.)
파일은 파일, 글로브는 폴더, 줄 번호는 글자로. 찾는 순서 — 보고서 폴더 → `specs/` → **`data.ts` 의 `linkRoots`**(저자가 명시한 외부 폴더, 저장소 기본보다 먼저) →
저장소 루트 → `out/codegraph-raw` → `git ls-files` 이름 유일. **없는 파일은 링크하지 않는다** — 계획에만 있는 파일이 링크되면 독자가 속는다.
용어(`term-ref`) 안은 건너뛴다 — 용어는 뜻 카드, 코드 글꼴은 파일 링크로 역할이 갈린다.

### Graphviz SVG 인라인 규칙 (`viz/svg.py`)

- `dot -Tsvg_inline` 사용 — `<?xml?>`·DOCTYPE 없이 나와 HTML 본문 삽입에 맞다.
- `width`/`height` 제거, `viewBox` 유지.
- **id 접두사를 붙인다.** 정의(`id="…"`)만이 아니라 `url(#…)` 과 `href`/`xlink:href` 참조까지 **세 곳을
  함께** 치환한다. 하나라도 빠지면 clipPath/marker 가 깨진다.
- **Mermaid/D3 로 대체하지 않는다.** `constraint=true/false` 분리가 Graphviz 에만 있고 그것이 의미축의 전제다.

## `report-spec init` 의 slug 검증

인계 문서에 없던 요구로, 사용자 지적에 의해 추가됐다. 초기 구현은 아무 문자열이나 받아 조용히 빈
디렉토리를 만들었다.

- 인자 없음 → 보고서 없는 문서 나열 후 exit 1. 줄 끝에 어느 자리인지를 함께 낸다
- 대응 문서 없음 → 거부 + 비슷한 slug 제시 후 exit 1
- 찾음 → `date`(파일명) · `specName`(문서 첫 `# ` 제목) · `branch`(git) 자동 채움
- **`data.ts` 가 이미 있으면 문서 존재를 따지지 않는다** — 작업 중인 보고서를 문서 이름 변경으로 막으면 안 된다

### 원본은 두 자리에 산다 (2026-08-31)

| 자리 | 파일명 관례 | 보고서가 생기는 곳 |
|---|---|---|
| `specs/` | `YYYY-MM-DD-<slug>-design.md` | `specs/<slug>/` |
| `plans/` | `YYYY-MM-DD-<slug>.md` | `plans/<slug>/` |

**보고서는 원본 문서 옆에 생긴다.** `specs/` 만 접미사를 요구하는 이유는 그 폴더에
`-before.svg` · `-design-review.html` 이 함께 살아 접미사가 오타 가드 노릇을 하기 때문이다.
`plans/` 는 계획서만 있어 가드가 필요 없다.

⚠ **관례가 `viz/init.py` 의 `DOC_DIRS` 와 `../runner/run_mode2.py` 의 `DOC_DIRS` 두 곳에 산다.**
언어가 달라 한 곳에 모을 수 없다 — 한쪽만 고치면 `init` 은 찾는데 러너는 못 찾는
어긋남이 조용히 생긴다. 고칠 때 반드시 둘 다 본다.

**주입하는 네 값은 전부 `JSON.stringify` 로 이스케이프한다.** 실제 spec 제목에 백틱이 있어
(`` # `back_face` → `flip_faces` ``) 템플릿 리터럴에 그대로 꽂으면 `data.ts` 가 문법 오류가 된다.

### `report-spec check` 의 용어 대조 — 경고이지 실패가 아니다

본문에 식별자 꼴 낱말이 있는데 `terms` 에 없으면 목록을 띄운다. 잡는 꼴은 셋뿐이다 —
결정 코드(`C-19`·`U5`·`M4`), 산출물 파일명(`*.json`), 배열 필드(`calls[]`).
자연어 용어(`WarmUp`·`PageRank`)는 기계가 가릴 수 없어 **저자가 직접 넣어야 한다.**
실패시키지 않는 이유는 탐지 규칙이 오탐을 낼 수 있어서다.

## 이 모듈이 소유하는 것 (Owns)

`viz/**` 전부 — `src/` 포함. **소유하지 않는 것** — `../machine/*.py` 는 결과만 읽고 고치지 않는다.
`bin/**` 은 러너축의 것이다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `../runner/*` → 여기 | `runner/wiki/build.py` 가 `demermaid.py` 를, `runner/wiki/prep.py` 가 `render_modules.py` 를 자식 프로세스로 부른다 |
| `../runner/dispatch.py` → 여기 | `report-spec` 의 명령표가 `viz/init.py` · `viz/build.py` · `viz/check.py` 를 가리킨다 |
| 여기 → `src/` | `build.py` 의 esbuild `alias`, `check.py` 의 임시 tsconfig `paths` |
| 여기 → 바깥 명령 | `dot`(Graphviz) · `npx mmdc`(Mermaid) 를 PATH 로 부른다 |

**여기서 나가는 화살표는 없다시피 하다** — 시각축은 잎이다. 부르는 쪽은 언제나 러너다.

## 흔한 변경 패턴 (Common modification patterns)

```bash
# 새 .py 를 더했다 — 직접 실행 가드부터 넣는다
node --test test/<해당>.py      # 가드가 없으면 import 순간 process.exit 로 러너가 죽는다

# viz/src/ 를 고쳤는데 테스트가 옛 동작을 보인다 — .tmp/lib.mjs 가 낡았다
npm test                              # pretest 가 다시 번들한다

# 새 mode 명령을 더한다 — bin 의 table 한 줄과 scripts 파일 하나
$EDITOR bin/report-<mode>             # table: { <명령>: "scripts/…mjs" }
```

**함정 — `node --test test/` 는 Node v25.8.0 에서 죽는다.** 디렉토리를 테스트 파일로 취급한다.
**인자 없는 `node --test`** 를 쓰면 Node 가 알아서 찾는다.

## 비직관적인 것 (Gotchas)

- **Why — 임시 번들은 `cwd` 가 아니라 `ROOT` 에 쓴다.** 동적 `import()` 가 파일 위치 기준으로
  `react/jsx-runtime` 을 찾으므로 외부 저장소에 두면 즉사한다.
- **Gotcha — 타입 검사용 tsconfig 는 `include` 글로브가 아니라 `files` 에 절대경로로 열거한다.**
  글로브는 tsconfig 위치 기준인데 그 파일은 `ROOT` 에 있고 검사 대상은 `cwd` 다.
- **Note — 위키 사이트는 대상 저장소가 아니라 이 저장소 안에서 짓는다.** 대상에는
  `node_modules` 가 없어 `Cannot find package 'vitepress'` 로 죽는다. 산출물만 되돌아간다.
