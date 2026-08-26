# ReturnHandOff — 설계 검토 보고서 시스템 실행 보고

> 작성일: 2026-08-26
> 수신: `ReportSystem_HandOff.md`를 작성한 오케스트레이터
> 발신: 그 문서를 받아 실행한 세션
> 대상 저장소: `~/report-builder` (브랜치 `feat/report-builder`, 태그 `v1`)

---

## 0. 이 문서의 목적

인계 문서 §0은 이 시스템의 목적을 **"AI의 판단이 맞는지 틀린지를 사람이 빠르게 판정하도록 돕는 것"**으로 정의했다. 이 보고서는 같은 원리를 인계 문서 자신에게 적용한다 — **인계 문서의 어떤 판단이 실행 결과 맞았고 어떤 것이 틀렸는지를 판정 가능한 형태로 되돌려 보낸다.**

따라서 이 문서의 중심은 "무엇을 만들었다"가 아니라 **"문서가 예측한 것과 실제가 어디서 갈렸는가"**다.

확신도 표기는 인계 문서 §5 규약을 따른다. 🔵는 **이번 실행 세션에서 직접 명령을 돌려 얻은 값**만 붙였다.

---

## 1. 실행 요약

| Phase | 인계 문서 | 상태 | 비고 |
|---|---|---|---|
| 0 | (전제) | 완료 | 인계 문서가 "전제"라 한 것이 실제로는 미충족이었다 (§3-1) |
| 1 | B1 다이어그램 가독성 | **코드 완료 · 육안 판정 미완** | 사용자 판정 대기 |
| 2 | B2 Decision-gate 파일럿 | **미착수** | §2 참조 |
| 3 | A1 소급 검증 | **미착수** | §2 참조 |
| 4 | B3 렌더러 + CLI | 완료 | |
| 5 | B4 check.mjs | 완료 | |
| 6 | B5 골든 재생성 | **6.1(v1 태그)만 완료** | 사용자 결정 대기 (§8-2) |
| 7 | A2~A4 | 미착수 | A1 게이트 미통과 |

**🔵 계량 실측 (2026-08-26)**

| 항목 | 값 |
|---|---|
| 커밋 | 21개 (`794b17a` ~ `e449e84`) |
| 태그 | `v1` |
| 테스트 | **40개 전부 통과** (svg 8 · components 16 · check 8 · init 8) |
| `tsc --noEmit` | 통과 |
| 추적 소스 | 1,391줄 (`src/` 476 · `scripts/` 475 · `test/` 354 · `bin/` 22 · 설정 64) |
| 컴포넌트 export | 13개 (인계 문서가 지정한 11개 + `Page` + `Section`) |
| 빌드 산출물 `<script>` | **0개** |

**동작이 확인된 것:** `report init` → `report build` → `report check` 가 실제 스펙 디렉토리에서 end-to-end로 돌고, 산출물에 `<script>`와 React 런타임이 각각 0개다. 링크 무결성 검사는 **음성 대조까지 통과**했다 — `data.ts`에 `D0`을 추가하면 `절이 없는 결정: D0` + 종료코드 1을 내고, `report.tsx`에 절을 추가하면 통과한다.

**동작이 확인되지 않은 것 (인계 문서 §4 "조기 성공 선언" 경계):**
- **B1이 실제로 읽히는지** — 계산과 코드만 있고 육안 확인이 없다
- **정본을 재현하는지** — Phase 6 시각 대조 미실시. **컴포넌트가 정본과 같은 마크업을 내는지는 아직 미검증이다**
- B2의 판정 시간 가설
- D축의 예측력

---

## 2. 순서 이탈 — 밝혀 둔다

인계 문서 권장 순서는 `B1 → B2 → A1 → B3~B5`였다. 실제로는 **`B1 → B3~B5`로 진행하고 B2와 A1을 건너뛰었다.**

**이유:** B2의 완료 조건은 "사용자가 표로 읽을 때와 그림으로 볼 때의 판정 시간 비교"이고, A1의 게이트 판정도 사용자 몫이다. 둘 다 렌더러 구축을 막지 않으며, 인계 문서 자신이 "B3~B5는 A1 결과와 무관하게 진행 가능"이라고 적었다. 사용자 응답을 기다리는 동안 코드 경로를 뚫는 쪽을 택했다.

**💭 45 — 이 판단이 옳았는지는 확신할 수 없다.** 인계 문서가 B2를 "판정 시간의 최대 미사용 자산"이라 부른 것은 우선순위 신호였는데, 그것을 뒤로 미뤘다. 되돌릴 수 있는 이탈이지만 문서의 명시적 순서를 거스른 것은 사실이다.

---

## 3. 인계 문서의 사실 오류 — 실측으로 반증됨

### 3-1. "node_modules 사전 설치 완료 전제"는 거짓이었다 🔵

§B-3의 파일 구성도에 `node_modules/  사전 설치 완료 전제`라고 적혀 있었다. **실제로는 `package.json`조차 없었고 커밋이 0개인 빈 저장소였다.**

영향: 계획에 Phase 0(환경 구축)을 새로 만들어야 했다. 설치한 것 — typescript 7.0.2 · esbuild 0.28.2 · react/react-dom 19.2.8 · @types/{node 26.3.0, react 19.2.18, react-dom 19.2.5}.

**§B-2의 "typescript@7의 tsc" 결정은 유효했다** 🔵 — `npm view typescript version` = 7.0.2, 설치 후 `npx tsc -v` = `Version 7.0.2`.

**함정 하나:** 로컬 설치 전에 `npx tsc -v`를 치면 npm이 이름만 보고 **2016년의 무관한 패키지 `tsc@2.0.4`**를 받으러 간다. 이걸 "설치됐다"고 오독하기 쉽다.

### 3-2. "CSS 6,599자"는 맞았지만 측정 대상이 달랐다 🔵

§B-1의 "CSS 6,599자가 두 파일에서 바이트 단위로 동일하다(diff 0줄)"는 **사실이다.** 두 정본의 `<style>` 블록은 실제로 완전히 동일하다.

다만 6,599는 `<style>`·`</style>` 태그 줄과 HTML 내부 6칸 들여쓰기를 **포함한** 값이다. 그것을 떼고 `src/theme.css`로 추출하면 **6,064바이트**가 된다. 실행 중인 서브에이전트가 이 차이를 결함으로 의심했으므로, 다음 세션이 같은 혼란을 겪지 않게 기록한다.

현재 `src/theme.css`는 B1 패치와 블록 컴포넌트 CSS가 더해져 **132줄 / 8,497바이트**다.

### 3-3. §B-4의 `<ConfBadge>` 예시가 정본 출력과 다르다 🔵 — 가장 중요한 오류

인계 문서 §B-4의 예시는 이렇다:

```tsx
return <span className={`conf-badge conf-${tier}`}>{anchor}</span>;
```

**정본 실측은 이렇다:**

```html
<span class="conf-badge conf-green">🔵 99</span>
<span class="conf-badge conf-amber">🟡 75</span>
<span class="conf-badge conf-red">💭 65</span>
<span class="conf-badge conf-green">🔵 실측</span>     ← 앵커가 숫자가 아닌 사례
```

예시대로 만들면 **B5 골든 대조가 전부 실패한다.** 이모지가 빠지고, `anchor: number` 타입은 `"실측"`을 표현하지 못한다. 정본을 따라 `이모지 + 앵커`를 렌더하고 `anchor: number | string`으로 구현했다.

### 3-4. 정본에 tier와 이모지가 어긋난 사례가 2건 있다 🔵

```html
<span class="conf-badge conf-green">🟡 80</span>
```

🟡(amber)인데 클래스가 `conf-green`이다. 저작 시 실수로 보이나 **확정할 수 없다.**

**임의로 고치지 않았다.** 정본을 바꾸면 B5 대조의 기준 자체가 흔들린다. 대신 `emoji` prop으로 재정의를 허용해 두 경우를 모두 표현할 수 있게 하고 사용자 결정 대기 중이다(§8-2).

### 3-5. `<StatusTag>`는 상태값이 아니라 자유 문자열이다 🔵

§B-4는 `status-badge`, `status-proposed/accepted` 상태값으로 적었으나 정본은 이렇다:

```html
<span class="status-tag status-accepted">검증됨 · 기록 완료</span>
<span class="status-tag status-accepted">확정 사용자 · rev.1 번복</span>
<span class="status-tag status-proposed">비-목표 (남은 갭)</span>
```

**상태 + 부연**이 자유 문구로 들어간다. 색 계열(`variant`)과 문구(`children`)를 분리해 구현했다.

또 클래스 이름이 `status-badge`가 아니라 `status-tag`다. `status-badge`는 헤더에 1회만 쓰이는 별개 클래스다.

---

## 4. 인계 문서가 정하지 않아 실행 중 정한 것

### 4-1. B1 복구 방식 — 옵션표를 만들어 사용자가 선택 (옵션 B 채택)

§B-7이 pan/zoom UX 형태를 미결정으로 남겼으므로, B1은 그 결정을 대신하지 않는 최소 복구만 하도록 옵션표를 냈다.

| | 방식 | `<script>` | 판정 |
|---|---|---|---|
| A | 1열 세로 스택 고정 | 0 | 폭이 1048px로 늘어도 축소율 40% → **여전히 안 읽힘** |
| **B** | **체크박스 토글 (기본 병치 / 켜면 1열 + 원본 픽셀 + 스크롤)** | **0** | **사용자 채택** |
| C | pan/zoom 스크립트 | 1 | §B-7 미결정 UX를 지금 확정해야 해서 보류 |

**B는 JavaScript 0줄이다.** `.zoom-toggle:checked ~ .diagram-grid` 형제 결합자만 쓴다. 산출물 불변식 예산(`<script>` 1개)을 **소모하지 않고** 결함을 고쳤다.

### 4-2. `--svg-w` — §B-5 규칙의 부작용을 메우는 장치 🔵

§B-5는 "`width`/`height` 속성을 제거하고 `viewBox`만 남긴다"고 정했다. **그 규칙만 따르면 "실제 크기" 복원이 불가능하다.**

`width`/`height` 없는 인라인 SVG는 고유 크기(intrinsic size)가 없어서, CSS `width: auto`를 주면 브라우저가 **기본값 300×150px**로 렌더한다. 원본 크기를 알 방법이 사라진다.

해결: `scripts/svg.mjs`가 속성 제거 **직전에** pt 값을 읽어 px(× 4/3)로 환산해 돌려주고, `BeforeAfter`가 그것을 `.svg-wrap`의 인라인 style로 `--svg-w`에 주입한다. CSS 커스텀 속성은 상속되므로 자식 `svg`가 읽는다.

🔵 실제 정본 SVG로 검증: `1961pt → 2615px`. 인계 문서 §B-1이 계산으로 낸 수치와 정확히 일치한다.

### 4-3. `report init`의 slug 검증 — 인계 문서에 없던 요구

§B-3은 slug을 `2026-07-27-geometry-winding-ownership-design.md`의 `geometry-winding-ownership` 부분으로 정의했다. 그런데 **`report init` 동작 규정에는 그 대응 관계를 검증하라는 말이 없다.**

초기 구현은 규정대로 만들어서 **아무 문자열이나 받아 조용히 빈 디렉토리를 만들었다.** 사용자가 이를 지적해 고쳤다.

현재 동작:
- **인자 없음** → `specs/`를 훑어 아직 보고서가 없는 spec을 날짜 내림차순으로 나열, exit 1 (🔵 실제 저장소에서 59건)
- **대응 `*-design.md` 없음** → 거부 + 비슷한 slug 제시, exit 1
- **찾음** → `date`(파일명) · `specName`(문서 첫 `# ` 제목) · `branch`(git) 자동 채움
- **`data.ts` 이미 있음** → 기존 멱등 동작 유지. **이 경로에서는 spec 존재를 따지지 않는다** (작업 중인 보고서를 spec 이름 변경으로 막으면 안 된다)

**다음 세션에 대한 권고:** §B-3의 `report init` 동작 규정에 이 검증을 명문화할 것.

### 4-4. "콘솔 에러 0건" 검사를 넣지 않았다 — 상태 `[제안됨]`

§B-6 표에 있는 5개 검사 중 이것만 뺐다. 산출물에 `<script>`가 0~1개뿐이고 상태도 없어 **실행할 클라이언트 코드가 사실상 없다.** 헤드리스 브라우저 의존성을 들이는 것은 잡을 것이 없는 검사를 위해 무거운 도구를 들이는 것이고, 이는 §4 거울 함정에 해당한다고 판단했다.

pan/zoom 스크립트가 실제로 도입될 때 추가하는 것으로 미뤘다. **사용자 확인 대기 중.**

### 4-5. `<Decision>` 컴포넌트를 별도로 만들지 않았다

§B-4는 `<DecisionTable> / <Decision>`을 한 행으로 묶어 적었다. `Decision`을 별도 컴포넌트로 분리할 이유를 찾지 못해 `DecisionTable` 내부의 행 렌더로 접었다. 구현자 1 · 소비자 1이면 인터페이스를 만들지 않는다는 §2.5 원칙을 적용했다.

---

## 5. 이론과 달랐던 것 — 실행해야만 나온 결함 5건

**이 절이 이 보고서의 핵심이다.** 아래는 전부 "코드를 옮겨 적으면 될 것"처럼 보였으나 **실제로 돌려보니 실패한 것들**이다. 설계 문서만으로는 예측 불가능했다.

### 5-1. `node --test test/`가 Node v25.8.0에서 실패한다 🔵

```
Error: Cannot find module '$HOME/report-builder/test'
```

디렉토리 인자를 테스트 파일로 취급한다. **인자 없는 `node --test`**를 쓰면 Node가 알아서 탐색해 정상 동작한다. 글로브(`'test/*.test.mjs'`)도 된다.

### 5-2. 빌드 임시 번들을 `cwd`에 두면 외부 저장소에서 죽는다 🔵

보고서는 `~/report-builder` **밖**에 있다. 트랜스파일한 `.tmp-report.mjs`를 그 위치에 쓰고 동적 `import()`하면, Node가 **그 파일 위치 기준으로** `react/jsx-runtime`을 찾는다. 외부 저장소에는 react가 없으므로 `ERR_MODULE_NOT_FOUND`로 즉사한다.

해결: 임시 번들을 `ROOT`(report-builder 자신)에 둔다. 그러면 `ROOT/node_modules`에서 해결된다.

### 5-3. 스펙 디렉토리 tsconfig가 `@types/node`를 못 찾는다 🔵

`report init`이 만드는 tsconfig는 `~/report-builder/tsconfig.json`을 `extends`한다. base가 `"types": ["node"]`를 요구하는데, **TypeScript의 기본 `typeRoots`는 확장하는 tsconfig 파일 위치 기준으로 계산된다.** 외부 저장소에는 `@types/node`가 없으므로 `TS2688`로 실패한다.

해결: 생성되는 tsconfig에 `typeRoots: [<ROOT>/node_modules/@types]`를 명시.

### 5-4. `report-builder/svg`에 타입 선언이 없어 `tsc`가 막힌다 🔵

```
error TS7016: Could not find a declaration file for module 'report-builder/svg'.
'.../scripts/svg.mjs' implicitly has an 'any' type.
```

`svg.mjs`는 순수 JavaScript라 strict 모드에서 implicit any가 된다. `scripts/svg.d.mts`를 만들었으나 **그것만으로는 안 됐다** — tsconfig `paths`가 `.mjs`를 직접 가리키면 TypeScript가 형제 `.d.mts`를 찾지 않는다.

해결: `paths`가 **선언 파일**을 가리키게 한다. `paths`는 타입 해결 전용이고, 런타임 해결은 esbuild `alias`가 `.mjs`로 따로 하므로 충돌하지 않는다.

**모듈 해결이 빌드와 타입 검사에서 서로 다른 경로를 타야 한다**는 것이 §B-2 스택 결정에서 예측되지 않았던 부분이다.

### 5-5. spec 제목의 백틱이 생성 코드 문법을 깨뜨린다 🔵

`report init`이 spec 문서의 첫 `# ` 제목을 `data.ts`에 주입하는데, 실제 저장소의 spec 중에 제목이 이런 것이 있다:

```
# `back_face` → `flip_faces` ...
```

템플릿 리터럴에 그대로 꽂으면 `data.ts`가 문법 오류가 된다. 주입하는 네 값 전부 `JSON.stringify`로 이스케이프하도록 고쳤다.

**서브에이전트가 실제 저장소 데이터를 확인하다 발견했다.** 합성 테스트 데이터만 썼으면 안 나왔을 결함이다.

### 부수 — `init.mjs`에 직접 실행 가드가 없었다

`check.mjs`는 `if (process.argv[1]?.endsWith("check.mjs"))` 가드로 순수 함수만 노출한다. `init.mjs`는 그 패턴을 안 따라서, 테스트가 import하는 순간 `process.exit(1)`이 호출돼 러너 자체가 죽었다. 같은 패턴으로 감쌌다.

**💭 60 — 다음 세션 권고:** `scripts/*.mjs`에 이 가드를 규약으로 명문화할 것. CLI 스크립트를 테스트 가능하게 만드는 유일한 조건이다.

---

## 6. §6 "저장소에서 직접 확인할 것" — 전부 답함 🔵

인계 문서가 미확인으로 남긴 7개 항목이다.

| 항목 | 실측 결과 |
|---|---|
| 다이어그램이 실제로 안 읽히는지 육안 확인 | **미완.** 원인 CSS 규칙(`.svg-wrap svg { width:100%; max-width:100% }`)은 확인했고 SVG 원본 1961pt·글꼴 10pt도 확인했으나, **육안 판정은 사용자 몫이라 열려 있다** |
| `spec-review-dashboard` 스킬의 존재 여부 | **존재.** `~/.claude/skills/spec-review-dashboard/{SKILL.md, assets}`. 산출물을 "spec 옆에 `<spec-name>-review.html`"로 규정하며 블록 구성 (a)~(g)를 정의한다. **B2는 이 스킬의 개정이 된다** |
| `.gitignore`에 `*.html`이 있는지 | **없다.** 원본 저장소에는 `html/`·`doxygen/html/` 디렉토리 패턴만 있다. `~/report-builder/.gitignore`에 `out/`·`**/specs/*/out/`을 새로 만들었다 |
| Graphviz 버전 | **15.1.1** (20260805.0921). 10.0.1 이상이므로 `-Tsvg_inline` 사용 가능. 실행해 확인함 — `<?xml?>` 선언과 DOCTYPE 없이 나오고 `width`/`height`/`viewBox`를 갖는다 |
| TypeScript 버전 | **7.0.2** (설치 후). 인계 문서의 "7.x여야 Go 네이티브" 전제 충족 |
| `node_modules` 설치 상태 | **미설치였다** → §3-1 |
| `worked-example.dot`의 3종 세트 불일치 | **미확인.** 파일 위치는 `~/.claude/skills/graphviz-class-diagram/references/worked-example.dot`로 확인했으나 내용 대조는 하지 않았다. **다음 세션 과제로 남긴다** |

---

## 7. 새로 발견된 설계 공백 — 두 번째 보고서 장르

**인계 문서는 보고서 종류를 하나만 정의한다** — 설계 검토 보고서. "mode"는 `Decision-gate mode`(graphviz 스킬 기능)와 `다크 모드`(CSS)로만 등장하며, 보고서 종류 축은 없다.

그런데 🔵 원본 저장소 `doc/번복기록/`에 **다른 장르가 실재한다:**

```
2026-07-05-번복기록-분석보고서.md
2026-07-10-쟁점별-비교분석-및-파이프라인개선안.md
2026-07-27-RT베이크기각-분석보고서.md
AI설계판단오류-분석보고서.md          ← 인계 문서 §2가 "이 체계의 원천"이라 부른 그 문서
engine-migration-class.svg           ← before/after 쌍이 아닌 단일 의존 그래프
refrender-class-dependency.svg
```

이 장르는 spec에 딸리지 않고, 수용 판정란이 없고, before/after 쌍이 아니라 현황 그래프 한 장을 쓴다. **현재 시스템은 이것을 구조적으로 배제한다** — `report init`이 대응 `*-design.md`를 요구하기 때문이다(§4-3).

**주목할 점: Phase 3(A1)의 산출물이 정확히 이 두 번째 장르다.** 인계 문서 §A-2가 "A1의 산출물은 코드가 아니라 문서"라고 정했고, 소급 검증 보고서는 spec에 딸리지 않는다. 즉 **인계 문서 자신이 요구한 산출물이 인계 문서가 설계한 렌더러로는 만들어지지 않는다.**

**💭 70 — 지금 두 번째 mode를 추가하지 말 것을 권한다.** 세 가지 이유다.

1. **첫 번째 모드가 아직 검증 안 됐다.** Phase 6 시각 대조 미실시. 정본을 재현하지도 못한 컴포넌트 위에 두 번째 축을 얹으면 실패 원인이 섞인다.
2. **거울 함정이다**(§4 첫 항목). "mode"라는 축을 도입하면 컴포넌트마다 분기가 생긴다.
3. **인계 문서의 인접 장르 처리 패턴이 일관되게 "분리"다.** `dp-trace-simulator`는 별개 스킬 확정, Three.js는 "별도 트랙" 기각.

대신 §B-4가 정한 절차가 있다 — **컴포넌트 후보로 횟수와 함께 기록만 하고 사후 일괄 처리.** A1을 실제로 쓰면서 어떤 요소가 몇 번 반복되는지 관측한 뒤 정하는 것이 지금 추측으로 축을 세우는 것보다 낫다.

---

## 8. 열려 있는 게이트 — 사용자 판정 대기

### 8-1. B1 육안 확인 (최우선)

`.b1.html` 검증본 2건을 생성했다 🔵 (88,624 / 93,460바이트, `<script>` 각 0개). "⤢ 실제 크기로 보기"를 눌렀을 때 노드 글자가 읽히는지 사용자가 판정해야 한다.

**읽히지 않으면 옵션 A/C 재검토가 필요하고 `theme.css`를 다시 손대야 한다.**

### 8-2. 정본의 tier/이모지 불일치 2건 (§3-4)

Phase 6 착수의 선결 조건이다. 정본 그대로 재현할지, 저작 실수로 보고 정정할지. 정정하면 대조 결과에 "의도적 차이 1건"으로 기록된다.

### 8-3. §4-4의 "콘솔 에러 0건" 검사 생략에 동의하는지

### 8-4. 그 외 인계 문서 §A-4의 미결정 사항 전부 미해결

N값 · D 점수 구간 경계 · `[잠정됨]` 이름과 적용 범위 · `data.ts`의 D축 필드 — 전부 A1 결과에 달려 있고 A1이 미착수다.

---

## 9. 다음 세션이 할 일

권장 순서다.

1. **B1 육안 판정** (§8-1) — 실패하면 여기서 다시 시작
2. **§8-2 결정 후 Phase 6** — 기존 정본 2건 재생성 후 시각 대조. **이것이 통과하기 전까지 이 시스템은 "정본을 재현한다"고 주장할 수 없다**
3. **B2 파일럿** — 건너뛴 것. `mPasses` 배치 결정으로 소유권 그래프 2장을 만들고 판정 시간을 비교
4. **A1 소급 검증** — Track A 전체의 생사 게이트. `git show <결정_커밋>:<파일>` 또는 `git log -S`로 **"그때의 grep"**을 지킬 것. 이 함정을 놓치면 전체가 무효다
5. A1 통과 시에만 A2~A4

**인계 문서 §B-3에 명문화할 것:** `report init`의 slug 검증(§4-3), `scripts/*.mjs`의 직접 실행 가드 규약(§5 부수).

---

## 10. 넘겨받을 상태

```
~/report-builder  (브랜치 feat/report-builder, 태그 v1)
  bin/report                    init/build/check 디스패치
  src/
    types.ts        56줄        props 타입. D축 필드는 아직 없다 (A1 대기)
    theme.css      132줄        정본 추출 + B1 패치 + 블록 CSS
    page.tsx        33줄        Page, Section
    components/    251줄        11개 컴포넌트 (badges/tables/blocks/BeforeAfter/VerdictFooter)
  scripts/
    svg.mjs         37줄        inlineSvg — 헤더 제거·width/height→px 환산·id 접두사
    svg.d.mts        7줄        타입 선언 (§5-4)
    build.mjs       91줄        esbuild → renderToStaticMarkup → 문자열 조립
    check.mjs       83줄        script 수·타입·링크 무결성·builderVersion
    init.mjs       201줄        slug 검증 + 스켈레톤 생성 (§4-3)
    lib.mjs         18줄        테스트용 번들
    patch-legacy.mjs 38줄       B1 검증 전용. Phase 6 완료 후 제거 후보
  test/            354줄        40개
  docs/
    handoffs/ReportSystem_HandOff.md          원본 인계 문서
    handoffs/ReportSystem_ReturnHandOff.md    이 문서
    superpowers/plans/2026-08-26-report-builder.md   실행 계획 (결함 발견분 반영됨)
```

**계획 문서는 실행 중 발견된 결함이 전부 반영돼 있다.** §5의 5건과 §4-3의 변경이 해당 태스크 절에 실측 근거와 함께 기록돼 있으므로, 재실행 시 같은 함정을 다시 밟지 않는다.

**미해결 상태로 남긴 것을 다시 명시한다** — 정본 재현 여부(Phase 6), B1 육안 판정, B2 가설, D축 예측력. **이 중 어느 것도 "검증됨"이라고 쓰지 않았다.**
