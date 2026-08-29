# RESUME — Mode 1.5 오케스트레이터 세션 (2026-08-29)

> **이 문서가 재개의 단일 진입점이다.** 새 세션은 이것 하나만 읽고 이어갈 수 있어야 한다.
> 다른 문서는 심화 자료이지 시작 전제가 아니다.
>
> **이 문서가 대체하는 것** — `HANDOFF-2026-08-29-mode-1-5-orchestration.md` 의 "TL;DR" 과 "§1 세계의 상태" 절.
> 그 문서의 나머지(§0 슬롯 분배 · §3 위상 정렬 · §4 소유 매트릭스 · §5 하네스 · §7 규약)는 **여전히 유효**하고 여기서 반복하지 않는다.

---

## 🔴 최우선 — Mode 1 stage ③(위키)을 **두 저장소에서** 진행한다

> **2026-08-29 사용자 확정. 이것이 R9(다음 실사용 프로젝트)의 답이다.**
> **대상은 하나가 아니라 둘이고, 둘 다 해야 한다. 잊지 말 것.**

| # | 저장소 | 경로 | 실측 (2026-08-29 18:20) |
|---|---|---|---|
| **①** | **StickRushGame** (C#, Unity) | `$CSHARP_REPO` | 커밋 21 · HEAD `bf54917` · 사용자 `.cs` **110**(전체 1,713) · 수집기 `roslyn-dump` 0.1 |
| **②** | **QtVisionEdit** (C++, Qt/OpenCV) | `$CPP_REPO` | 커밋 **137** · HEAD `947cf50` · `.cpp` 46 + `.h` 31 = **10,300줄** · 수집기 `clang-uml` **0.6.3 설치 확인** |

**왜 이 둘인가** — ①은 `2026-08-28-llm-load-reduction.md` 계획서의 M1~M5 실측이 전부 나온 원래 표본이라 증분 이득을 숫자로 말할 수 있다.
②는 세 정적 수집기 갈래 중 **C++ 쪽을 실제로 태워** 언어 편향을 잡는다. 옛 Graphics 저장소가 아니라 QtVisionEdit 을 고른 것은
`CLAUDE.md` 의 `## ⚠ 방향` 절이 옛 프로젝트 이력 의존을 금지하기 때문이다.

### 각 저장소의 출발선 — 서로 다르다

| | ① StickRushGame | ② QtVisionEdit |
|---|---|---|
| `codegraph.json` · `facts/` · `ranking.json` | **이미 있다** (`out/codegraph-raw/`) | **없다 — 전부 처음부터** |
| 수집기 입력 | `.csproj` / `.slnx` | **`build/macos/compile_commands.json` 있다 (33 엔트리)** |
| 수집기 설정 | — | **`.clang-uml` 설정 파일 없다 → 만들어야 한다** |
| 위키 산문 | **10장 · 2,635줄 + 사전 렌더 SVG 33개 이미 있다** (2026-08-28) | 없다 |

### ⚠ 정정 — "위키가 한 번도 안 돌았다" 는 틀렸다

🔵 2026-08-29 18:20 실측 — ①에 `out/codegraph-raw/wiki/` 10장(2,635줄)과 `out/codegraph-raw/wiki-built/`(같은 10장 + SVG 33개,
`demermaid.py` 통과 완료)가 **이미 있다**. 위키 스스로 머리에 `deep-wiki 파일럿 (C# Data 스코프, 2026-08-28)` 이라 적어 뒀다 — **전량이 아니라 파일럿**이다.

**따라서 ③ 의 결손은 "산문을 못 만든다" 가 아니라 넷이다:**

| 결손 | 실측 근거 |
|---|---|
| **재현 불가** | `bin/report-wiki` 는 안내문만 출력하는 자리 표시자. 그 완주는 손으로 한 것이고 **명령이 남아 있지 않다** |
| **VitePress 사이트 없음** | 두 저장소 모두 `.vitepress` **0건**. `wiki-built` 는 마크다운 + SVG 폴더일 뿐 |
| **산출물이 사라진다** | StickRush `.gitignore:82` 의 `out/codegraph-raw/` — 다른 머신·다음 세션에 안 간다 |
| **기준이 낡았다** | 08-28 산출물인데 terms-db 우선 역전은 **08-29** 다 |

### 확정된 결정 2건 (2026-08-29 18:30, 사용자)

| # | 결정 | 근거 |
|---|---|---|
| **W1** | **위키 산문은 대상 저장소의 추적 경로에 남긴다** (`docs/wiki/` 등). `out/` 이 아니다 | Mode 2 의 선례 — 원고(`data.ts`·`report.tsx`)는 대상 저장소에 살고 산출물(`out/report.html`)만 제외했다. 위키 산문은 **LLM 이 쓴 원고**다. 부수 이득: WarmUp 의 blob 비교 대상이 된다 |
| **W2** | **StickRushGame 의 기존 위키 10장은 새 기준으로 다시 만든다** | 08-28 산출물이라 terms-db 우선 역전(08-29) 이전 기준이고, 스스로 "C# Data 스코프 파일럿" 이라 밝힌다. **전량 1회 완주가 있어야 WarmUp 의 baseline 비용이 나온다** |

### 순서 — WarmUp 은 나중이다

**위키 1회 완주 → baseline 비용 측정 → WarmUp.** 사용자 확정(2026-08-29).
증분 이득(재요약 비율)은 **전량 실행 1회가 있어야만** 계산되는 값이다 —
`2026-08-28-llm-load-reduction.md` Task 5 Step 5 가 그렇게 쓰여 있다. 순서를 뒤집으면 "얼마나 줄었나" 를 숫자로 말할 수 없다.

**WarmUp 은 설계만 있고 구현이 0이다.** 🔵 실측 — `codegraph/warmup.py` **부재**, 계획서 Task 1~8 실행 **0건**,
`terms-reading.json` 213 레코드에 **blob·commit·hash 계열 필드가 하나도 없다**. 지금 다시 돌리면 **매번 전량 재계산**이다.
설계된 보장은 **두 겹**임을 기억한다 — ① `git ls-tree` 의 blob SHA 3값 판정(유효/낡음/판정불가),
② `blast_radius()` 로 의존 간선 **양방향 1홉** 파급(“A 는 안 바뀌었는데 B 변경으로 A 서술이 틀려지는” 경우).
근거 M4 의 `1커밋당 2/114(1.8%)` 는 **변경 파일 비율**이지 재요약 비율이 아니다 — 1홉 파급을 태우면 커지고, **그 값은 미측정**이다.

---

## TL;DR + 바로 다음 한 걸음 (2026-08-29 17:40 갱신)

**어디까지 왔나** — 세 mode 가 이 저장소 안에서 한 바퀴 돌았다: Mode 1(전수조사 191개 → `terms-db.json` → `codegraph.json` 투영) →
Mode 1.5(첫 시험 20개, 이후 3문항 규칙) → Mode 2(이해도가 실측된 보고서 2건). 그 위에 Mode 2 프론트가 다섯 번,
Mode 1 이 두 번(terms-db 우선 전환 · xmldoc 주석 외부화) 진화했다. **오늘 커밋 68건.**

⚠️ **작업 트리에 41건이 미커밋이다 — ⑭ 가 방금 착지했고 커밋 승인 대기 중이다.** 재개하는 세션은 **§0 을 먼저 읽어라.**
38개는 `xmldoc inject` 가 넣은 **주석 블록만** 바뀐 것이다(코드 줄 변경 0, 재검증됨). 커밋 계획은 §0.1.

**바로 다음 한 걸음** — 순서가 정해져 있다:
> **1. 🔴 최우선 절**(바로 위)을 읽는다 — Mode 1 stage ③ 을 **StickRushGame(C#)과 QtVisionEdit(C++) 둘 다**에서 진행한다. R9 는 이것으로 닫혔다.
> **2. `bin/report-wiki` 진입점을 채운다** — `report-term` 과 같은 꼴(CLI 는 준비·후처리, 산문은 스킬).
> **3. R11 은 그다음** — `codegraph.json` 스키마에 `loc`(경로:줄 한 문자열) · `url`(원격 커밋 링크) 을 더할지. §6 참조.
>
> ~~§0.1 의 커밋 5건~~ → **완료** (`0428416` `e0af02d` `a0d87ce` `2124cf3` `29abc8f`, 2026-08-29 18:0x).

---

## 0. 방금 착지한 것 — 서브에이전트 ⑭ (2026-08-29 17:50, 미커밋)

**무엇** — `codegraph/xmldoc.py` 의 `where` 를 **마커 기준 재계산**으로 바꾸고, 주입 주석 블록에 **의존 줄**을 더하고,
보류됐던 재조사 증분(새 레코드 22 · uses 9)을 합쳤다. 프롬프트 전문: `HANDOFF-2026-08-29-mode-1-xmldoc-relocate.md`.

**사용자 의도(왜 이 파이프라인이 있나)** — *"개발하면서 내 생각과 기능 설명을 코드 옆에 미리 남겨, 나중 LLM 이 코드를 다시 추론하는 부담을 줄인다."*
뜻은 `terms-reading.json`(정본) → `comments.xml`(파생) 한 곳에 두고, 코드에는 **3줄 블록**만 박는다:
마커 `<include … @id='X'/>` · 한 줄 뜻 · **의존 줄** `// 쓰는 것: a, b · 쓰이는 곳: x`.

### 🔴 정정 — 근본 원인이 내 진단과 달랐다

내가 §0 초판에 적은 진단은 *"`plan_file` 이 `where` 를 셈으로 내며 누적 밀림을 빠뜨렸다"* 였다. **그건 절반이다.**
🔵 ⑭ 의 실측과 오케스트레이터 재검증: 주입 커밋 `77b95de` 는 **소스의 블록만 커밋하고 그때 다시 쓴 `terms-reading.json` 은 커밋하지 않았다.**
그래서 커밋된 json 은 *블록 없던 좌표*인데 파일에는 블록이 있었다. 근거 없음 242 중 대부분이 여기서 나왔다(블록을 걷어내면 26 으로 복귀).
검증: 38개 파일 전부 `strip_blocks(현재 소스) == acf88e1 의 소스` — 같음 38 · 다름 0.
**교훈 — 코드와 그 좌표를 적은 데이터는 같은 커밋에 들어가야 한다.** 따로 가면 검사기가 즉시 거짓말을 시작한다.

### 오케스트레이터가 직접 재검증한 결과 (전부 통과)

| 항목 | 값 |
|---|---|
| pytest | **62** (51 + `test_xmldoc.py` 11) |
| `npm test` · typecheck | **95** · 통과 |
| `xmldoc.py check` | **레퍼런스 166건 · 문제 0** |
| `terms_db.py --reading` | **용어 213 / 실패 0 / 근거 없음 0** · 투영 노드 134 간선 87 모듈 6 |
| 코드 줄 무변경 | **0** (주석 블록만 바뀌었다) |
| `means`/`does` 삭제 | **0** (Mode 1.5 정답지 보존) |
| 멱등 | 다시 `inject --dry-run` → 고칠 파일 0 · where 갱신 0 |
| 블록 | 3줄 · 마커 166 : 의존 줄 166 |
| `collect` 필수 8 | 8/8 · 두 보고서 `report-spec check` 5/5, `<script>` 1 |

근거 없음이 목표(원래 3건)보다 나은 **0** 인 이유 — 파일 레코드의 `:1` 이 이제 마커 줄이고 그 안에 파일명이 있어 L3 가 통과한다.

### ⑭ 가 계획서와 달리 한 것 (전부 타당, 재검증됨)

1. **`uses[].where` 도 옮겼다** — 계획서는 "안 다룬다" 였다. `carry_lines` 가 *이번에 민 만큼만* 따라 옮기고, 남은 어긋남 10건은 호출 자리를 직접 찾아 고쳤다. 그래서 `uses->` 근거 없음도 0 이다.
2. **낡은 `where` 20건을 고쳤다** — 조사 원본의 선언 레코드 11 · 증분 새 레코드 5 · 산출물·외부 4. 구조 칸만 손댔다.
3. **블록을 한 번 걷어내고 다시 넣었다** — 위 정정 때문이다. 코드 줄 결과 무변경 0 으로 확인.

### 미커밋 상태 — 커밋 계획은 아래 §0.1

⑭ 는 커밋하지 않았다(규약). `bin/report-wiki` 는 여전히 자리 표시자다. `xmldoc.py` 에 `strip` 명령은 만들지 않았다(이행기 1회용).

## 0.1 커밋 계획 — 사용자 승인 후, 경로를 좁혀 5건 (`-A` 금지)

| # | 메시지 | 경로 |
|---|---|---|
| 1 | `[fix] : xmldoc 의 where 를 마커 기준으로 재계산하고 의존 줄 추가` | `codegraph/xmldoc.py` `codegraph/test_xmldoc.py` |
| 2 | `[chore] : 주석 블록 재주입 - 마커 기준 where 와 의존 줄 반영` | 소스 38개 (`bin/*` `codegraph/*.py` `scripts/**` `src/**`, 주석만) |
| 3 | `[feat] : 전수조사 증분 합치기 - 새 레코드 22개와 낡은 인용 정정` | `docs/codegraph/terms-reading.json` `docs/codegraph/comments.xml` |
| 4 | `[docs] : 전수조사 스킬에 개발 규율과 xmldoc 산출물 반영` | `.agents/skills/codebase-terms-survey/SKILL.md` |
| 5 | `[docs] : 재개 문서 전면 갱신 - xmldoc 착지, R11 카토그래피, 인용 규율` | `docs/handoffs/RESUME-…` `HANDOFF-…-resurvey.md` `HANDOFF-…-xmldoc-relocate.md` |

## 1. 세계의 상태 — 2026-08-29 17:40 재측정

| 항목 | 값 |
|---|---|
| 저장소 | `$REPO_ROOT` (`~/report-builder` 는 **존재하지 않는다**) |
| 브랜치 | `feat/report-builder` |
| HEAD | `e1e0bfa [docs] : 전수조사 절차를 codebase-terms-survey 스킬로 - 정의 파일과 핸드오프는 포인터만` |
| 커밋 | `95910ef` 이후 **56개**, 2026-08-29 하루 **68개** |
| 미커밋 | **41건 — ⑭ 착지, 커밋 승인 대기(§0.1).** 그 밖에 `docs/prompt/checklist.yaml`(사용자 메모) · `HANDOFF-…-xmldoc-relocate.md`(이 세션의 기록) |
| Node 테스트 | **95 통과** (`npm test` — 인자 없이) |
| Python 테스트 | **62 통과** (⑭ 가 `test_xmldoc.py` 11개 추가. 착수 전 51) |
| 타입 검사 | 통과 |
| 보고서 2건 | `llm-load-reduction` · `mode-1-terms-db-first` — 둘 다 check **5/5**, `<script>` 1개 |
| 태그 | `v1` — 컴포넌트 API 는 추가만(`Term.mental` · `TermGraph.tune` · `ReportData.linkRoots`) |
| 런타임 번들 | 69.4KB (d3-force/zoom/drag/selection + 덩어리 물리 + 조정 슬라이더 + 카드 위치) |
| 스킬 3종 | `spec-review-dashboard` · `term-benchmark` (원본 `~/.claude/skills/`, 사본 `.claude/skills/`) · **`codebase-terms-survey`** (원본은 저장소 `.agents/skills/`, `.claude/skills/` 는 심볼릭 링크 — 사용자가 Antigravity 범용성 위해 이전 `c6aec64`) |
| 서브에이전트 정의 3종 | `.claude/agents/mode-{1-codebase-wiki,1-5-term-benchmark,2-spec-report}.md` — 커밋됨, 각각 실전 1회 이상 |
| 외부 저장소 | StickRush(C#) `out/codegraph-raw/codegraph.json` 노드 231 · Graphics(C++) 노드 191. 둘 다 Track C 산출, gitignore |

---

## 2. Task 상태 — Mode 1.5 계획 10/10 · terms-db 우선 계획 7/7

| Task | 내용 | 커밋 | 방식 |
|---|---|---|---|
| 0.1 | `scripts/dispatch.mjs` + 테스트 4 | `3c32fc6` | 서브에이전트 |
| 0.2 | `bin/report-{spec,term,wiki}`, `report` 위임 | `2316d6c` | 서브에이전트 |
| 0.3 | `CLAUDE.md` 명령 절 | `af03897` (+ 잔존 5곳 `2fff128`) | 서브에이전트 |
| 1.1 | `codegraph/terms_db.py` + pytest 3 | `8069517` | 서브에이전트 — **계획서 키 오류 2건 실측 정정** |
| 2.1 | `scripts/term/collect.mjs` + 테스트 4 | `1d31dc9` | 서브에이전트 |
| 3.1 | `scripts/term/quiz.mjs` + 테스트 6 | `6c0cca6` (+ `quiz` 명령 제거 `8b0141e`) | 서브에이전트 — **디스패처 인자 오류 실측 정정** |
| 4.1 | `scripts/term/emit.mjs` + 테스트 4 | `5d09bd9` | 서브에이전트 |
| 5.1 | `Term.mental` · 이해도 컬럼 · CSS + 테스트 2 | `506221a` | 서브에이전트 |
| 5.2 | init 스켈레톤 `terms: []` | `6e66190` | **오케스트레이터 직접** (위임 비용 > 작업) |
| 6.1 | `term-benchmark` 스킬 | `1c22f65` | **슬롯 C** 저작, 오케스트레이터 검토·커밋 |

**terms-db 우선 계획** (`2026-08-29-mode-1-terms-db-first.md`):

| Task | 내용 | 커밋 | 방식 |
|---|---|---|---|
| 1~5 | `terms_db.py` — `uses[]` 보존 · 투영 · 인용 3값 검사 · 합치기 · `--reading` CLI + 테스트 20 | `1ad879a` | `mode-1-codebase-wiki` — **계획서 결함 1건(C++ 간선 어휘) 실측 정정** |
| 6 | 전수조사 절차를 에이전트 정의 + HANDOFF ③ 에 | `b2e1c78` | `mode-1-codebase-wiki` |
| 7 | 이 저장소 전수조사 `terms-reading.json` 191개 | `a9b9080` | `mode-1-codebase-wiki` (LLM 읽기) |

**Mode 1 두 번째 진화(오후)** — `codebase-terms-survey` 스킬 신설 `259ad15` · `.agents/skills` 이전 `c6aec64`(사용자) · 절차를 스킬로 일원화 `e1e0bfa` ·
`xmldoc.py`+`comments.xml` 신설 `acf88e1` · 주석 주입 `77b95de` · **⑭ 진행 중**(§0).

**Mode 1.5 첫 시험과 규칙 변경** — 시험 `041d4be`(이해도 반영) · 3문항 규칙 `71a3386`. **Mode 2 프론트(사용자 지시)** — 아코디언 `596dec9` · 자동 참조 `70e4f39` · 경로 링크 `f92cb7d` · 관계도 물리 `6ef58b3` · 카드 위치 `a4d526c` · 범례 카드 `d42d3b3`.

**작업자 역할로 병행한 것(03:20 이전)** — `spec-review-dashboard` 스킬 용어집 반영 `d465df7` · 끊어진 심볼릭 링크 `33f4556` ·
용어 11개 추가로 경고 0 `245d160` · 핸드오프 4종 작성과 갱신(`3faa86e` `22d7c2b` `6e38375` `1666469` `c2d7015` `8b71c25`).

---

## 3. 확정된 결정 — 다시 논쟁하지 않는다

핸드오프 ① §1 의 표 11줄이 유효하다. **이 세션에서 추가로 확정된 것:**

| 결정 | 내용 | 근거 |
|---|---|---|
| `report-term quiz` 명령 없음 | 문항 출제는 CLI 가 아니라 스킬의 일. `collect` · `grade` · `emit` 셋뿐 | Task 3.1 실측 — 디스패처가 명령어를 소비해 `quiz` 와 `grade` 를 구분할 수 없었다 |
| 디스패처가 명령어 이름을 소비한다 | `scripts/dispatch.mjs:17` `[cmd, ...rest] = argv` → 스크립트는 파일 경로만 받는다 | `collect.mjs:51` · `quiz.mjs:38-40` · `emit.mjs` 가 같은 꼴 |
| `codegraph.json` 실제 키 | 간선 `from`/`to` · 모듈 `id`/`depends_on` (계획서의 `source`/`target` · `name`/`files` 는 **틀림**) | `normalize.py:237,287` |
| `terms.json` 필드명 | `TermMeans` · `UserMentalValue` — 사용자 확정, 바꾸지 말 것 | `emit.mjs:16-17` |
| Task 6.1 위임 가능 | "오케스트레이터 직접"은 CLI 미확정이 전제였고 그 전제가 사라졌다 | 핸드오프 ① 변경 이력 |
| 슬롯 B 가 지킬 간접 의존 | `normalize.py` 의 출력 키를 바꾸면 `terms_db.py` 가 깨진다 | `1666469` |
| **terms-db 우선** | `terms-db.json` 이 원본, `codegraph.json` 은 투영. LLM 전수조사 1회. LLM 레코드는 `where` 필수 + L1/L2/L3 기계 검사. 정적 수집기가 있으면 구조 필드는 codegraph 가 이긴다(D3). 원본 `docs/codegraph/`, 파생물 `out/`(D4). 키 규칙 맨 이름·충돌 시 `파일줄기.이름`(D5). `C-19` `M4` `U5` 는 사전에 그대로 | 계획서 D1~D7, 사용자 확정 05:50 · 06:45 |
| **3문항 규칙** | 용어당 3문항. 맞힌 수 2~3 확실 / 0~1 모름. "모른다" 2회 이상 모름. **애매 없음**(타입에만 남음) | 사용자 확정 14:40, `71a3386` |
| 용어 자동 참조 | 본문 모든 등장 감쌈. 제목(h2) · `.mono` · 표 머리 · summary · 용어집 · 관계도 · SVG 는 건너뜀 | 사용자 확정 15:20, `70e4f39` |
| 경로 링크 | 파일은 파일 · 글로브는 폴더 · `file://` · **새 탭** · `linkRoots` 가 저장소 기본 폴더보다 먼저 · 없는 파일은 링크 안 함 | 사용자 확정 16:00 · 16:30, `f92cb7d` |
| 관계도 물리 `KNOBS` | `REPEL_IN -200 · REPEL_OUT -200 · REPEL_MAX_DIST 410 · GRAVITY 0.035 · BOUNDS_SCALE 2.5 · LINK_DISTANCE 90 · LINK_STRENGTH 0.35 · COLLIDE_RADIUS 49 · GROUP_PAD 24 · GROUP_STRENGTH 0.6` | 사용자가 슬라이더로 확정 17:40, `6ef58b3` |
| 카드는 CSS 로 뜨고 위치만 런타임 | 표의 overflow 에 잘리지 않게 `position: fixed` 로 옮김 | `a4d526c` |

**정정된 것** (이전 문서가 틀렸던 것):
- 핸드오프 ② · ④ 는 작업 완료 후에도 "붙여넣어 실행하라"고 말하고 있었다 → 🔴 완료 배너를 달았다(`1c22f65` `8b71c25`).
  **원칙 5(발신 측 정리)를 늦게 한 것**이며, 사용자가 지적해 고쳤다.

---

## 4. 서브에이전트 소유 매트릭스 — 2026-08-29 17:40 실측

**슬롯(별도 세션) 구도는 끝났다.** 정의 파일 3개는 한 세션이 만들었고(03:1x, §9 정정), 실작업은 전부 **이 오케스트레이터 세션이 `Agent` 도구로**
띄운 서브에이전트가 했다. 각 정의의 `## 소유 파일과 경계` 절이 곧 매트릭스이고, 오늘 그 경계가 실전에서 지켜졌다(소유 밖 변경 0건, 전부 커밋 안 함).

| 파일 | 오케스트레이터 | `mode-1-codebase-wiki` | `mode-1-5-term-benchmark` | `mode-2-spec-report` |
|---|---|---|---|---|
| `codegraph/*` (`terms_db.py` 포함 — ⑤ 이후) | 검토·커밋 | **소유** (⑤⑥ 투입) | 읽기 | 읽기 |
| `docs/codegraph/terms-reading.json` · `comments.xml` | 검토 | **소유** (전수조사 원본과 파생 XML) | 읽기 | 읽기 |
| `codegraph/xmldoc.py` · `test_xmldoc.py` | 검토·커밋 | **소유** (⑭ 투입 중) | — | — |
| 소스의 **주석 블록**(`<include …/>`) | 검토 | `xmldoc inject` 로만 바꾼다 — 손으로 고치지 않는다 | — | — |
| `normalize.py` 출력 키 | — | **바꾸지 말 것** | — | — |
| `scripts/term/*` · `test/term.test.mjs` | 검토 | 읽기 | **소유** (⑦ 투입) | 읽기 |
| `scripts/dispatch.mjs` · `bin/*` | **소유** | 읽기 | 읽기 | 읽기 |
| `src/*` · `scripts/{build,check,init,svg,wrap-terms,link-paths}.mjs` · `test/{components,wrap-terms,link-paths,graph-math}.test.mjs` | 검토·커밋 | 읽기 | 읽기 | **소유** (⑧⑨⑩⑪⑫ 투입, 추가만) |
| `docs/superpowers/specs/*/{data.ts,report.tsx}` | 저작·커밋 | — | — | 소유(수동 `<T>` 제거 · `linkRoots` 한 줄) |
| `CLAUDE.md` · `docs/handoffs/*` · `.claude/skills/*` | **소유** | Track C 절만 | — | — |
| `.claude/agents/<자기 것>.md` | 검토 | 소유 | 소유 | 소유 |

**커밋은 오케스트레이터가 사용자 승인 후 경로를 좁혀 한다. `-A` 금지.** 서브에이전트는 구현 + 검증 + 보고까지.

---

## 5. 가드레일과 규약

핸드오프 ① §7 표가 그대로 유효하다. 요약:

| 항목 | 규약 |
|---|---|
| Node 테스트 | `npm test` — **인자 없이.** `node --test test/` 는 Node 25 에서 죽는다 |
| Python 테스트 | `.venv/bin/python -m pytest codegraph/ -q` |
| 커밋 | 사용자 승인 후. `[tag] : 한국어 한 줄`, 본문·트레일러 없음, `—`·`→`·`·` 금지 |
| 서브에이전트 | 커밋하지 않는다. 구현 + 검증 + 보고. 오케스트레이터가 **직접 재검증** 후 커밋 |
| 컴포넌트 | 추가만. props 제거·의미 변경 금지 |
| 금지 단어 | "검증됨" "입증" "증명" (보고 문장에서. 상태 태그 `[검증됨]` 은 별개) |
| 옛 산출물 | 기준이 아니다. `CLAUDE.md` `## ⚠ 방향` 절 |
| 도구는 판정하지 않는다 | CLI 는 사람에게 묻지 않는다. 묻는 건 스킬 |
| **`codegraph/*.py` 인용** | **줄 번호로 인용하지 않는다** — `xmldoc inject` 가 주석 블록을 넣고 빼며 줄을 민다. `normalize.py::normalize_cpp` 처럼 **함수 이름**으로 (2026-08-29 17:40 신설, 아래 실측) |
| 소스의 주석 블록 | 손으로 고치지 않는다. 뜻은 `terms-reading.json` 이 정본, `xmldoc emit`→`inject` 가 코드에 반영 |

**하네스 7블록** (서브에이전트 프롬프트에 빠뜨리지 않을 것) — `[ROLE]` `[HARD RULES]` `[BOUNDARIES]` `[VERIFIED FACTS]` `[STEP n]` `[SELF-REVIEW]` `[REPORT]`.
`[VERIFIED FACTS]` 에는 반드시 **"이 보고를 믿지 말고 재검증하라"** 를 넣는다. 오늘 그 한 줄이 내 오류 **8건**을 잡았다 — 계획서 키 2 · 테스트 절 번호 · 디스패처 인자 · C++ 간선 어휘(드라이런이 골든 하나만 돌림) ·
테스트 단언 패턴 · `edges[]` 뒤쪽 경계 · `xmldoc.py` 의 `uses[].where` 미갱신. **드라이런은 골든 재료 전부에 돌린다.**

**핸드오프를 쓸 때도 같은 규율이 걸린다** — 🔵 17:40: 이 문서에 적은 `normalize.py:178` 인용이 **쓰는 사이에** 어긋났다(⑭ 가 주석을 재주입 중이라 줄이 밀렸다).
원칙 2(믿지 말고 검증하라)로 문서의 인용을 하나씩 다시 돌려 보고 잡았다. **문서에 적은 검증 명령은 적은 자리에서 실제로 실행해 볼 것** — 이 문서 §0 의 두 명령은 그렇게 확인했다(둘 다 0).

---

## 6. 열린 결정 — 사용자 몫 (2026-08-29 17:40)

| # | 무엇 | 상태 | 막고 있는 것 |
|---|---|---|---|
| R1 · R2 | 시험 재료 · 에이전트 정의 커밋 | **해소** | — |
| R3 | C++ 용어 키가 네임스페이스 포함 (`SJH::Material`) | 보류 | Mode 1.5 를 C++ 저장소에 쓸 때 |
| R4 · R6 | `collect` 낱말 오탐 (`a.json` · `Data` `bin` `load` `report` `src`) | 보류 — "지금은 결정 안 한다" | 실사용 오탐 비율 |
| R5 | 외부 노드(`(STL) std`)를 용어 DB 에서 뺄지 | 보류 | R3 과 같은 시점 |
| R7 | C# 저장소에 읽기 단계를 얹어 **C1(오답 보기 품질)** 시험 | 보류 | StickRush 용 Plan 이 생길 때 |
| R8 | SVG 다이어그램 글자 안의 경로까지 링크할지 | 보류 | 필요가 생길 때 |
| R10 | 인용 부패 | **해소** — ⑭ 가 마커 기준 재계산 + `carry_lines`. 근거 없음 0 (§0). 남은 규율: 코드와 좌표 데이터를 **같은 커밋에** | — |
| **R11** | **`codegraph.json` 스키마 확장 — 카토그래피 여지** (사용자 17:35 제안) | **열림. ⑭ 착지 후 바로** | 아래 |
| **R9** | **도구를 써 볼 다음 실제 프로젝트** | **해소 (2026-08-29 18:20)** — **StickRushGame(C#)** 과 **QtVisionEdit(C++)** **둘 다.** 최우선 절 참조 | — |
| **R13** | Mode 1 stage ③ 진입점 `bin/report-wiki` 를 채우는 일 | **열림 — 지금 최우선.** 재현 불가 · VitePress 없음 · 산출물 소실 · 기준 낡음 | 착수 대기 |
| R12 | `wiki-architect` 의 부록 용어집(40+ terms)을 `terms-db.json` 에서 결정론으로 뽑을지 | 기록만 | Mode 1 안에서 두 LLM 이 같은 코드를 따로 읽는 자리 |

### R11 상세 — 사용자 제안과 조사 결과 (⑭ 착지 후 착수)

사용자 말: *"codegraph 의 스키마를 확장해서 정확히 어느 코드라인이며, 상대 경로를 넣는 URL 필드를 넣음으로 LLM 이 바로 추적할 수 있도록 카토그래피 여지를 만들고 싶다."*

🔵 **정적 수집기 실측 — 세 갈래, 산출 형식은 이미 같다** (`schema_version: 2`):

| 언어 | 수집기 | 실행 | 위치 출처 | 실물 |
|---|---|---|---|---|
| C++ | **clang-uml 0.6.3** (외부 도구) | `clang-uml -c .clang-uml -n full_class_all -g json --paths-relative-to-pwd` | `elements[].source_location {file,line}` → `normalize.py::normalize_cpp` | `SJH::MouseInput` → `src/input/mouse_input.h:42` |
| C# | **roslyn-dump 0.1** (**우리 도구**, `Microsoft.CodeAnalysis.CSharp 5.9.0`) | `dotnet run --project codegraph/roslyn-dump -- <저장소>` | `types[].{file,line}` → `normalize.py::normalize_csharp` | `AddressableRenamer` → `Assets/@Editors/AddressableRenamer.cs:9` |
| Python · JS/TS | **없음** — LLM 전수조사 → `terms_db.py::project_codegraph` 투영 | `codebase-terms-survey` 스킬 | 레코드 `where` 를 쪼갬 | `BeforeAfter` → `src/components/BeforeAfter.tsx:20`, `source_tool: "terms-db"` |

**이미 있는 것**: `nodes[]`/`edges[]` 의 `file`(저장소 루트 기준 **상대** 경로) + `line`. `verify_citations.py::build_index` 가 `(file,line)` 쌍을 색인 키로 쓴다.
**없는 것**: LLM 이 한 번에 붙여 넣어 뛸 수 있는 **한 문자열**.

| 안 | 값 | 평가 |
|---|---|---|
| ① `loc` | `"src/input/mouse_input.h:42"` | **권장.** 기계 독립 · git 안전 · `verify_citations` 인용 형식·`terms-reading.json` 의 `where` 와 **글자까지 같다** |
| ② `url` = `file:///…` 절대경로 | 클릭 가능 | **저장하지 않는다** — 기계 종속(다른 머신에서 죽은 링크). 보고서 빌드 때 `scripts/link-paths.mjs` 가 이미 만든다 |
| ③ `url` = `https://github.com/<org>/<repo>/blob/<commit>/…#L42` | 원격 + 줄 앵커 | **옵션으로.** `repo_commit` 이 이미 있어 커밋 고정 가능. 원격 없으면 생략. `wiki-researcher` 인용 형식과 같다 |

**손대는 곳**: `normalize.py::_assemble`(두 갈래 공통 출구) + `terms_db.py::project_codegraph`(투영) 두 군데, `schema_version: 2 → 3`.
소비자(`verify_citations.py` · `facts.py` · `render_*.py`)는 `file`/`line` 을 계속 읽으므로 **추가만** 이라 안 깨진다.
✅ **⑭ 가 착지했으므로 이제 착수할 수 있다** (커밋 5건 뒤).

💡 **이 문서가 `codegraph/*.py` 를 인용할 때 줄 번호를 쓰지 않는 이유** — `xmldoc inject` 가 주석 블록을 넣고 뺄 때마다 줄이 밀린다.
🔵 17:40 실측: 5분 전에 맞던 `normalize.py:178` 인용이 그 사이 어긋났다. **함수 이름으로 인용한다**(`normalize.py::normalize_cpp`).
이것이 R10 이 실재하는 증거이고, ⑭ 의 마커 기준 재계산이 필요한 이유다.

---

## 7. 포인터 (2026-08-29 17:40)

| 문서 | 역할 | 상태 |
|---|---|---|
| `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` | Mode 1.5 계획. 실측 정정 주석 4건 | 10/10 완료 |
| `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md` | Mode 1 terms-db 우선 계획. 결정 D1~D7 | 7/7 완료 |
| `docs/superpowers/specs/llm-load-reduction/` | Mode 2 보고서 — 이해도 실측(확실 6 · 애매 3 · 모름 11 · 미측정 4), `linkRoots` → StickRush | check 5/5 |
| `docs/superpowers/specs/mode-1-terms-db-first/` | terms-db 계획의 검토 보고서 — 결정 7건, 용어 30개 | check 5/5 |
| `docs/superpowers/specs/llm-load-reduction/term-quiz.md` (+ `out/quiz_to_answers.py` · `out/term-quiz.key.json`, gitignore) | 첫 시험지 100문항과 채점 헬퍼 | 기록 |
| `docs/codegraph/terms-reading.json` · `comments.xml` | 전수조사 원본(213)과 XML 파생물. `out/codegraph-raw/` 는 CLI 한 줄로 재생성 | 미커밋 — §0.1 |
| **`.agents/skills/codebase-terms-survey/SKILL.md`** | **Mode 1 전수조사 스킬** (신설 `259ad15`, 이전 `c6aec64`). `wiki-researcher` 의 증거 규율 이식 — 금지 표 · 증거 기준표 · `confidence` 3등급 · 탐색 안 한 것 목록. 개발 규율 절(코드 만들 때 레코드도 함께) 포함 | 활성 · `.claude/skills/` 는 심볼릭 링크 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-xmldoc-relocate.md` ⑭ | xmldoc 재계산 프롬프트 전문 | 🔴 완료(미커밋) |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-resurvey.md` ⑬ | 재조사 — ⑭ 안에서 소화된다 | 🟡 보류 |
| HANDOFF ① `…-mode-1-5-orchestration.md` | 위상 정렬 §3 · 하네스 §5 · 규약 §7 (Mode 1.5 계획의 기록) | 🟡 부분 대체 |
| HANDOFF ③ `…-mode-1-5-agents.md` | Mode 1/1.5/2 역할 서술 **원본** — `.claude/agents/` 가 실행본. 둘을 같이 고친다 | 🟢 활성 |
| HANDOFF ② ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ | 서브에이전트 프롬프트 기록 | 🔴 전부 완료 |
| `docs/handoffs/RESUME-2026-08-28-track-c.md` | Track C(Mode 1) 재개 — 별개 갈래 | 🟡 부분 대체 |
| `CLAUDE.md` | 저장소 규약. `## ⚠ 방향` 부터 | 갱신됨 |
| `docs/prompt/checklist.yaml` | 사용자 메모(작업 단계 의존 그래프) | 커밋됨 `6676827` |
| `docs/handoffs/HANDOFF-2026-08-29-griffe-python-prototype.md` | **R11/R9 관련 곁가지 — griffe 기반 Python 정적 수집기 프로토타입**(Option B, `normalize_python()` 추가). Artifact A(자기완결형 에이전트 프롬프트), 인계 대기 | 🟡 미착수 — 다른 세션에 인계용 |

**gitignore** — `out/`(보고서 산출물 · `out/codegraph-raw/` 파생물 · 시험 정답지) · `.tmp/`(**⑬ 의 addendum 이 여기 있다 — 다른 머신으로 안 간다**) · `__pycache__/`.

---

## 8. 재현 — 산출물이 사라졌을 때 (전부 결정론, 수 초)

> ⚠ 아래 기대값은 **⑭ 착지 전(HEAD `e1e0bfa`)** 기준이다. ⑭ 가 착지하면 용어 191 → **213**, pytest 51 → **61**,
> 근거 없음은 (원래 3건 + `uses[].where` 부패분)이 된다. **착지 후 이 절의 숫자를 한 번 고칠 것.**

```bash
cd $REPO_ROOT
npm test && .venv/bin/python -m pytest codegraph/ -q && npm run typecheck        # 95 · 51 · 통과

# Mode 1 — 이 저장소 자신의 terms-db.json 과 codegraph.json(투영). 원본은 docs/codegraph/terms-reading.json
.venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json
#   기대: 용어 191개 / 실패 0 · codegraph.json 노드 119 간선 76 모듈 6
.venv/bin/python codegraph/xmldoc.py check     # 코드 주석 블록이 json 과 맞는가 — 문제 0건 (R10 은 ⑭ 가 풀었다)
# 정적 수집기가 있는 저장소(StickRush)의 기존 호출 꼴 — 투영이 상위집합인지 대조
.venv/bin/python codegraph/terms_db.py $CSHARP_REPO/out/codegraph-raw/codegraph.json --repo $CSHARP_REPO -o /tmp/rb-cs
#   기대: 용어 241개 / 실패 0 · 투영에 없는 것 0개

# Mode 1.5 — 후보 수집 (known 26 / newConcepts 23) 과 채점 e2e
mkdir -p /tmp/rb-quiz && cd /tmp/rb-quiz && report-term collect $REPO_ROOT/docs/superpowers/plans/2026-08-28-llm-load-reduction.md $REPO_ROOT/out/codegraph-raw/terms-db.json
printf '{"A":{"correct":3,"dontKnow":0,"means":"a"},"B":{"correct":1,"dontKnow":2,"means":"b"}}\n' > answers.json
report-term grade answers.json && report-term emit term-grades.json      # 3문항 규칙: 확실 1 · 애매 0 · 모름 1

# Mode 2 — 두 보고서 빌드 · 검사
cd $REPO_ROOT/docs/superpowers/specs/llm-load-reduction && report-spec build && report-spec check   # 5/5, 자동 참조 40, 경로 링크 28
cd ../mode-1-terms-db-first && report-spec build && report-spec check                                                              # 5/5, 80, 36
```

---

## 9. 변경 이력 (추가만)

- 2026-08-29 03:20 — 최초 작성. 계획서 10/10 완료, 병렬 슬롯 3개 정의 파일 생성(미커밋), 실작업 미착수 시점.
- 2026-08-29 05:40 — R1 해소 방향 확정. 실측으로 "DB 가 없다" 가 아니라 "Plan 과 짝이 되는 코드베이스의 DB 가 없다" 로 문제를 다시 적었다(StickRush 는 DB 있음 · Plan 없음, 이 저장소는 그 반대). 사용자 결정 — Mode 1 을 **terms-db.json 원본 · codegraph.json 투영** 구조로 뒤집고 LLM 전수조사는 1회. 새 계획서 `2026-08-29-mode-1-terms-db-first.md` 와 그 검토 보고서(`specs/mode-1-terms-db-first/`, check 5/5, 용어 30개)를 만들었다. 계획서 코드는 스크래치패드 드라이런에서 19/19 통과(골든 2개 pass). 전부 **미커밋 · 착수 미승인**. 하네스 관측 — 이 세션은 `.claude/agents/` 셋 중 `mode-1-codebase-wiki` 만 이름으로 부를 수 있다(③ 문서 #2 와 같은 증상, 부분집합 다름).
- 2026-08-29 05:50 — 사용자가 검토 보고서의 옵션표를 놓고 **D3(정적 도구가 이긴다) · D4(원본 `docs/codegraph/` 추적, 파생물 `out/`) · D5(맨 이름, 겹치면 전원 한정)** 를 전부 1안으로 확정. 계획서 결정 목록과 보고서 `data.ts` 에 반영. 남은 사용자 결정 — **착수 승인**과 커밋 4건.
- 2026-08-29 (에이전트 정의 세션) — 🔴 **귀속 오류 정정.** 최초 판의 "세 슬롯이 각자 정의를 만들었다"(§4·TL;DR)와
  핸드오프 ① §9 의 "슬롯 B 가 만들었다" 는 틀렸다. mtime 3건과 그 세션의 `ls` 결과로 **한 세션이 셋을 다 만들었음**을
  확인했다. R2 의 "각 슬롯 소유" 사유도 함께 소멸. 아울러 핸드오프 ③·① 의 "CLI 4단계 / 4개 명령" 오기 4곳을 고쳤다
  (`report-term` 명령은 `collect` · `grade` · `emit` 셋).
  **미확인 관측 1건** — 정의 3개 중 `mode-2-spec-report` 가 하네스의 새 에이전트 알림 목록에 나오지 않았다.
  frontmatter 는 셋 다 같은 꼴이라 원인을 특정하지 못했다. `/agents` 로 확인할 것.
- 2026-08-29 06:20 — terms-db 우선 계획 **Task 1~5 완료** (`1ad879a`, 문서 `a41f286`). `mode-1-codebase-wiki` 첫 실전 투입 — 경계 준수, 커밋 안 함, DONE_WITH_CONCERNS 로 계획서 결함 1건(C++ 간선 어휘 `instantiation`·`friendship`) 실측 정정. 위 "미확인 관측" 은 해소 — 정의 파일 커밋(`2aca41a`) 뒤 하네스가 이 세션에 `mode-1-5-term-benchmark` · `mode-2-spec-report` 도 로드했다. 다음: Task 6·7 을 같은 에이전트에 연이어 위임(사용자 승인, 06:25 디스패치).
- 2026-08-29 06:50 — terms-db 우선 계획 **Task 6·7 완료** (`b2e1c78` 절차 문서, `a9b9080` 읽기 원본). **계획서 7/7.** 이 저장소의 `terms-reading.json` 191개 (file 35 · function 98 · interface 10 · artifact 13 · key 10 · concept 7 · module 7 · enum 4 · external 6 · class 1). 파생물은 `out/codegraph-raw/` (무시, CLI 한 줄로 재생성). 검사 실패 0 · 근거 없음 3(머리 주석에 파일명이 없는 파일 3개 — 규칙 유지, 정보성). `collect` known 26 / newConcepts 23. 사용자 결정 — `C-19` `M4` `U5`(코드엔 표기 예시로만 있음)를 **사전에 그대로 둔다**; Mode 1.5 에서 이 셋의 정답지는 '표기 예시' 가 된다. 파일명 충돌 규칙(경로 전체) 한 줄을 정의 파일에 보탬. R6 낱말 오탐 4건 더 관측(`bin` `load` `report` `src`) — R4 와 같이 보류. 서브에이전트가 잡은 내 오기 — `main` 은 5파일이 아니라 **9파일**. 다음: **Mode 1.5 — 사용자가 실제로 시험을 친다** (재료 확보됨).
- 2026-08-29 15:00 — **Mode 1.5 첫 시험.** 용어 20개 × 5문항(100문항)을 문제 파일로 치렀다(사용자 요청으로 대화식 출제 중단). 결과 확실 6 · 애매 3 · 모름 11 — 모름 11개가 전부 Plan 의 결정 코드·지표 표기. 사용자 판정 확정. `data.ts` 에 `mental` 20개 반영 → **이해도가 실측된 첫 보고서** (`041d4be`). 사용자 결정으로 채점 규칙을 **3문항 · 맞힌 수 2~3 확실 / 0~1 모름 · 모른다 2회 모름 · 애매 없음** 으로 변경 — 코드는 `mode-1-5-term-benchmark` 첫 실전 투입(`71a3386`), 문서 6곳은 오케스트레이터(`0447d9b`). C1 첫 관측 — 진짜 뜻이 있는 용어의 정답률이 60~100% 로 갈렸다(포화 아님). C2 실측 — 100문항은 많다. `C-19` `M4` `U5` 를 사전에 둔 결정은 무의미했다(전부 '모른다'). 그레이딩 헬퍼 `out/quiz_to_answers.py`(숫자 배열 → answers.json, gitignore).
- 2026-08-29 15:40 — **Mode 2 프론트 두 건 (사용자 지시).** ① 용어집을 이해도 그룹 **아코디언**으로(`596dec9`, `<details>` 스크립트 0줄, 모름만 열림) — `mode-2-spec-report` 첫 실전 투입. ② 본문 용어 **자동 참조** — 빌드 후 통과 `scripts/wrap-terms.mjs` 가 모든 등장을 `TermRef` 마크업으로 감싼다(`70e4f39`), 카드에 용례·이해도 배지, 밑줄 끝 `?`; 두 보고서의 수동 `<T>` 40곳 제거(`dbb4d0f`). 제목·`.mono` 는 건너뛴다(사용자 확정). 하네스가 내 오류 2건을 더 잡았다(테스트 단언 패턴 · 뒤쪽 경계). 서브에이전트 세션·네트워크 피드백 실측: 정상.
- 2026-08-29 16:35 — **Mode 2 경로 링크** (사용자 지시). 빌드 후 통과 둘째 `scripts/link-paths.mjs` — 본문(`.mono` 포함)의 경로 꼴을 실제 로컬 파일·폴더의 `file://` 링크(**새 탭**)로, 없는 파일은 그대로(`f92cb7d`). 해석 순서에서 **`linkRoots` 가 저장소 기본 폴더보다 앞**(사용자 확정) — llm 보고서의 `codegraph.json` 이 StickRush 로 간다. `ReportData.linkRoots?` 추가. llm 28개 · mode-1 36개 · 못 찾은 경로 4종(계획에만 있는 파일). `facts/*.md` 는 SVG 안에만 있어 링크 안 됨(의도). 테스트 86.
- 2026-08-29 17:45 — **관계도 물리 (사용자 지시 2건, `6ef58b3`).** `forceManyBody` → 덩어리를 아는 쌍 전수 척력 + 노드별 중력, 캔버스 상자 제한, **덩어리 경계 사각형(AABB) 충돌**(context7: d3-force 에 그룹 충돌 없음 → 커스텀 힘). 임시 슬라이더(`<TermGraph tune />`)로 사용자가 값 10개를 육안 확정 → `KNOBS` 에 박고 tune 을 뗌. 순수 계산 `src/runtime/graph-math.ts`(components · bounds · clampBox · rectOverlap) 테스트 9개. 런타임 68.5KB. 테스트 95.
- 2026-08-29 18:05 — **카드 결함 2건 (사용자 관측, 오케스트레이터 직접).** ① 표 안 카드가 `.table-wrap`(overflow-x)·`.card`(overflow hidden)에 잘림 → 런타임이 뜰 때 위치만 `position: fixed` 로(`a4d526c`, CLAUDE.md 의 'CSS 만으로' 문장 개정). ② 범례 안 카드가 항상 켜짐 — `.diagram-legend span` 이 자손 전체에 걸려 `.term-card` 의 display:none 을 이김 → 직계 자식 `>` 로(`d42d3b3`). 자동 참조가 새 자리에 term-ref 를 넣으면서 드러난 기존 CSS 의 함정. 같은 꼴의 자손 요소 선택자는 theme.css 에 더 없음(grep).
- 2026-08-29 18:15 — **핸드오프 전면 갱신(사용자 지시).** TL;DR · §1 · §4 · §6 · §7 · §8 을 재측정으로 다시 썼다. HANDOFF ① 배너에 §0 도 낡았음을 적고, ③ 의 '아직 안 된 것' 을 전부 완료로, Mode 2 절과 정의 파일에 오늘의 프론트 변경 5건을 반영, Track C RESUME 에 terms-db 우선 파이프라인 배너, CLAUDE.md 상태 표 수치 갱신.
- 2026-08-29 18:55 — R10 재조사(⑬) 서브에이전트 완료(증분 22+17)했으나 **보류** — 다른 세션의 `xmldoc.py inject` 와 `terms-reading.json` 을 놓고 충돌. 사용자 결정: xmldoc 먼저. 증분은 `.tmp/` addendum 으로 분리, 정본은 HEAD 로 복원. 작업 트리의 38개 소스 변경과 `codegraph/xmldoc.py` · `docs/codegraph/comments.xml` 은 **다른 세션 것 — 이 세션은 건드리지 않는다.**
- 2026-08-29 19:00 — **전수조사 절차를 스킬로 분리** (`codebase-terms-survey`, 사용자 결정 C 착수). `wiki-researcher` 는 통째로 부르지 않고 규율만 이식 — 금지 표 · 증거 기준표 · `confidence` 3등급 · 탐색 안 한 것 목록 · (선택) 모듈당 구조 렌즈 1회. "빠진 간선" 측정 도구는 스킬 안에 착수 조건으로 남김. 정의 파일 절차 절은 요약+포인터로. 사용자가 xmldoc(`acf88e1` `77b95de`)과 스킬을 커밋했다.
- 2026-08-29 17:40 — **/lossless-handoff 재실행.** ⑭(xmldoc where 마커 재계산 + 의존 줄 + 증분)이 **진행 중인 상태로** 문서화 — §0 신설(진척 · 재검증 명령 · 커밋 계획 · 실패 시 복구). `codebase-terms-survey` 스킬 신설과 `.agents/` 이전 반영. R11(codegraph 스키마 `loc`/`url` 확장) 신설 — 정적 수집기 3갈래 실측 표 포함. deep-wiki 조사: `wiki-researcher` 를 통째로 부르지 않고 규율만 이식(R12 로 기록).
- 2026-08-29 17:50 — ⑭ **착지.** 재검증 전부 통과(pytest 62 · xmldoc check 0 · terms_db 213/실패 0/**근거 없음 0** · 코드 줄 무변경 0 · 멱등). 🔴 **내 진단 정정** — 근본 원인은 셈 오류만이 아니라 `77b95de` 가 소스 블록만 커밋하고 `terms-reading.json` 을 빠뜨린 것이었다(38파일 `strip == acf88e1` 로 확인). R10 해소. §0 을 착지 기록으로, §0.1 에 커밋 5건.
