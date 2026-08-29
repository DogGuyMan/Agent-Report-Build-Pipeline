# scripts/ — Node 배선

> 루트 나침반은 `../CLAUDE.md`. 이 문서는 **Node 쪽 배선만** 다룬다.
> 파이썬 파이프라인은 `../codegraph/CLAUDE.md`, 컴포넌트는 `../src/CLAUDE.md`.

## 무엇이 여기 있나

| 자리 | 하는 일 |
|---|---|
| `dispatch.mjs` | `bin/` 진입점 넷이 공유하는 명령 갈림길 |
| `init.mjs` · `build.mjs` · `check.mjs` | Mode 2 (`report-spec`) |
| `wiki/` | Mode 1 (`report-wiki`) — `prep` · `build` · `check` · `compdb` · `clang-doc` · `paths` |
| `term/` | Mode 1.5 (`report-term`) — `collect` · `quiz` · `emit` |
| `svg.mjs` · `wrap-terms.mjs` · `link-paths.mjs` | 빌드 후처리 세 통과 |
| `python.mjs` · `doctor.mjs` · `lib.mjs` | 환경 탐색과 테스트 번들 |

### `scripts/*.mjs` 는 직접 실행 가드를 둔다 — 규약

```js
if (process.argv[1] && process.argv[1].endsWith("check.mjs")) { /* CLI 본체 */ }
```

import 시에는 순수 함수만 노출한다. 가드가 없으면 테스트가 import 하는 순간 `process.exit()` 가
호출돼 러너 자체가 죽는다(`init.mjs` 에서 실제로 발생). 새 스크립트도 이 패턴을 따른다.

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

### 렌더 경로

`report.tsx` → esbuild 트랜스파일 → 동적 import → `renderToStaticMarkup` → `<style>` 에 `theme.css`
문자열 삽입 → `out/report.html`. **React 는 빌드 시점 Node 에만 존재하고 산출물은 순수 HTML+CSS 다.**

**용어 자동 참조 (2026-08-29 신설).** `data.ts` 에 `terms` 가 있으면 `renderToStaticMarkup` 결과에 `scripts/wrap-terms.mjs` 를
한 번 더 통과시켜 본문 글자에 나오는 용어 id 의 **모든 등장**을 `TermRef` 마크업으로 감싼다(마크업은 그 컴포넌트를 실제로 렌더한
문자열 — 출처 하나). 건너뛰는 곳: 이미 감싼 곳 · 카드 안 · `.mono` `<code>` `<pre>` · `h1~h3` · `th` · `summary` · 용어집 · 관계도 · SVG.
긴 id 먼저, ASCII id 는 낱말 경계, 한글 id 는 조사까지. **저자는 `<T id>` 를 심지 않는다** — `defineTerms` 는 남아 있으나 선택이다.
왜 여기인가: 본문 산문 대부분이 props 로 들어가 React 트리 순회로는 닿지 않고, 전역·컨텍스트는 쓰지 않기 때문이다.

**경로 링크 (2026-08-29 신설).** 같은 자리에서 둘째 통과 `scripts/link-paths.mjs` 가 본문(코드 글꼴 `.mono` **포함**)의 경로 꼴 낱말을
실제 로컬 파일·폴더의 `file://` 링크로 바꾼다(**새 탭**). 잡는 꼴 넷 — `docs/handoffs/` 아래 마크다운 이름,
`-design.md` 로 끝나는 이름, `HANDOFF-` 로 시작하는 이름, `facts/` 아래 글로브. 각각 뒤에 `:줄번호` 가 붙어도 된다.
(이 문단에 그 꼴을 **실물로 적지 않는다** — 적으면 인용 검사기가 진짜 인용으로 오인한다. `test/docs-citations.test.mjs` 참조.)
파일은 파일, 글로브는 폴더, 줄 번호는 글자로. 찾는 순서 — 보고서 폴더 → `specs/` → **`data.ts` 의 `linkRoots`**(저자가 명시한 외부 폴더, 저장소 기본보다 먼저) →
저장소 루트 → `out/codegraph-raw` → `git ls-files` 이름 유일. **없는 파일은 링크하지 않는다** — 계획에만 있는 파일이 링크되면 독자가 속는다.
용어(`term-ref`) 안은 건너뛴다 — 용어는 뜻 카드, 코드 글꼴은 파일 링크로 역할이 갈린다.

### Graphviz SVG 인라인 규칙 (`scripts/svg.mjs`)

- `dot -Tsvg_inline` 사용 — `<?xml?>`·DOCTYPE 없이 나와 HTML 본문 삽입에 맞다.
- `width`/`height` 제거, `viewBox` 유지.
- **id 접두사를 붙인다.** 정의(`id="…"`)만이 아니라 `url(#…)` 과 `href`/`xlink:href` 참조까지 **세 곳을
  함께** 치환한다. 하나라도 빠지면 clipPath/marker 가 깨진다.
- **Mermaid/D3 로 대체하지 않는다.** `constraint=true/false` 분리가 Graphviz 에만 있고 그것이 의미축의 전제다.

## `report-spec init` 의 slug 검증

인계 문서에 없던 요구로, 사용자 지적에 의해 추가됐다. 초기 구현은 아무 문자열이나 받아 조용히 빈
디렉토리를 만들었다.

- 인자 없음 → 보고서 없는 spec 나열 후 exit 1
- 대응 `specs/*-<slug>-design.md` 없음 → 거부 + 비슷한 slug 제시 후 exit 1
- 찾음 → `date`(파일명) · `specName`(문서 첫 `# ` 제목) · `branch`(git) 자동 채움
- **`data.ts` 가 이미 있으면 spec 존재를 따지지 않는다** — 작업 중인 보고서를 spec 이름 변경으로 막으면 안 된다

**주입하는 네 값은 전부 `JSON.stringify` 로 이스케이프한다.** 실제 spec 제목에 백틱이 있어
(`` # `back_face` → `flip_faces` ``) 템플릿 리터럴에 그대로 꽂으면 `data.ts` 가 문법 오류가 된다.

### `report-spec check` 의 용어 대조 — 경고이지 실패가 아니다

본문에 식별자 꼴 낱말이 있는데 `terms` 에 없으면 목록을 띄운다. 잡는 꼴은 셋뿐이다 —
결정 코드(`C-19`·`U5`·`M4`), 산출물 파일명(`*.json`), 배열 필드(`calls[]`).
자연어 용어(`WarmUp`·`PageRank`)는 기계가 가릴 수 없어 **저자가 직접 넣어야 한다.**
실패시키지 않는 이유는 탐지 규칙이 오탐을 낼 수 있어서다.

## 이 모듈이 소유하는 것 (Owns)

`scripts/**` 와 `bin/**`. **소유하지 않는 것** — `codegraph/*.py` 는 부르기만 하고 고치지 않는다.
`src/*` 는 esbuild 로 번들할 뿐 내용을 모른다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `bin/*` → 여기 | 진입점 넷이 전부 `dispatch.mjs` 의 `runDispatch` 를 쓴다 (`report-wiki` 제외) |
| 여기 → `codegraph/*.py` | `wiki/prep.mjs` · `wiki/check.mjs` · `wiki/build.mjs` 가 자식 프로세스로 부른다 |
| 여기 → `src/*` | `build.mjs` 의 esbuild `alias`, `check.mjs` 의 임시 tsconfig `paths` |
| `codegraph/run_mode*.py` → 여기 | 세 실행기가 `node scripts/…mjs` 를 부른다 (**되돌아오는 방향**) |

**순환처럼 보이지만 아니다** — 파이썬 실행기는 최상위 오케스트레이터이고, `scripts/` 는 그 아래
단계다. 같은 프로세스 안에서 서로 부르는 것이 아니라 자식 프로세스 경계로 갈려 있다.

## 흔한 변경 패턴 (Common modification patterns)

```bash
# 새 .mjs 를 더했다 — 직접 실행 가드부터 넣는다
node --test test/<해당>.test.mjs      # 가드가 없으면 import 순간 process.exit 로 러너가 죽는다

# src/ 를 고쳤는데 테스트가 옛 동작을 보인다 — .tmp/lib.mjs 가 낡았다
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
