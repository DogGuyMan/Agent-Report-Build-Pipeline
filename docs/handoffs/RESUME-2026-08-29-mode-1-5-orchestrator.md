# RESUME — Mode 1.5 오케스트레이터 세션 (2026-08-29)

> **이 문서가 재개의 단일 진입점이다.** 새 세션은 이것 하나만 읽고 이어갈 수 있어야 한다.
> 다른 문서는 심화 자료이지 시작 전제가 아니다.
>
> **이 문서가 대체하는 것** — `HANDOFF-2026-08-29-mode-1-5-orchestration.md` 의 "TL;DR" 과 "§1 세계의 상태" 절.
> 그 문서의 나머지(§0 슬롯 분배 · §3 위상 정렬 · §4 소유 매트릭스 · §5 하네스 · §7 규약)는 **여전히 유효**하고 여기서 반복하지 않는다.

---

## TL;DR + 바로 다음 한 걸음 (2026-08-29 18:15 갱신)

**어디까지 왔나** — 세 mode 가 **이 저장소 안에서 한 바퀴 돌았다.**
Mode 1(terms-db 우선 파이프라인, 자기 전수조사 191개) → Mode 1.5(첫 시험 20개: 확실 6 · 애매 3 · 모름 11, 이후 3문항 규칙) →
Mode 2(이해도가 실측된 `llm-load-reduction` 보고서). 그 위에 사용자 지시로 Mode 2 프론트가 다섯 번 진화했다 —
**용어집 아코디언 · 본문 용어 자동 참조 · 경로 `file://` 링크 · 관계도 물리(슬라이더로 확정) · 카드 위치/범례 수정.** 오늘 커밋 60건.

**서브에이전트 3개**(`.claude/agents/`)는 커밋됐고(`2aca41a`) 각각 실전에 1회 이상 투입돼 경계를 지켰다 — Mode 1 ⑤⑥, Mode 1.5 ⑦, Mode 2 ⑧⑨⑩⑪⑫.
하네스의 "이 보고를 믿지 말고 재검증하라" 한 줄이 오늘 내 오류 **7건**을 잡았다(§5).

**바로 다음 한 걸음** — 이 저장소 안에서 할 일은 **없다.** 남은 것은 전부 **사용자 결정**이다(§6):
> (가) 도구를 **다른 실제 프로젝트**에 써 본다 — CLAUDE.md `## ⚠ 방향`. StickRush 는 DB 는 있으나 Plan 이 없다.
> (나) 보류 항목 R3~R8 중 무엇을 열지.

---

## 1. 세계의 상태 — 2026-08-29 18:15 재측정

| 항목 | 값 |
|---|---|
| 저장소 | `$REPO_ROOT` (`~/report-builder` 는 **존재하지 않는다**) |
| 브랜치 | `feat/report-builder` |
| HEAD | `988d6ca [docs] : 재개 문서 이력 - 카드 위치와 범례 카드 결함 2건` |
| 커밋 | `95910ef` 이후 **48개**, 2026-08-29 하루 **60개** |
| 미커밋 | `docs/prompt/checklist.yaml` 하나 (사용자 메모, 의도적 미추적) |
| Node 테스트 | **95 통과** (`npm test` — 파일 8개: check · components · dispatch · init · svg · term · wrap-terms · link-paths · graph-math) |
| Python 테스트 | **51 통과** (`.venv/bin/python -m pytest codegraph/ -q`) |
| 타입 검사 | 통과 (`npm run typecheck`) |
| 보고서 2건 | `llm-load-reduction` · `mode-1-terms-db-first` — 둘 다 `report-spec check` **5/5**, `<script>` 1개, 용어집 경고 0 |
| 태그 | `v1` 그대로 — 컴포넌트 API 는 추가만 했다(`Term.mental` · `TermGraph.tune` · `ReportData.linkRoots`) |
| 런타임 번들 | 69.4KB (d3-force/zoom/drag/selection + 덩어리 물리 + 조정 슬라이더 + 카드 위치) |
| 스킬 | `spec-review-dashboard` · `term-benchmark` — `~/.claude/skills/` 원본과 `.claude/skills/` 사본 **동일**(`diff -q`) |
| 서브에이전트 정의 | `.claude/agents/mode-{1-codebase-wiki,1-5-term-benchmark,2-spec-report}.md` 커밋됨. 이 세션의 하네스가 셋 다 이름으로 부른다 |
| 외부 저장소 | 새 산출물 없음(재측정). StickRush `out/codegraph-raw/` 에 `codegraph.json` · `roslyn-dump.json` · `facts/` (Track C 산출) |

**저장소 밖 자산** — 스킬 원본 2종(위). **저장소 밖이 원본, 안은 사본**이다. 고치면 둘 다 갱신한다.

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

## 4. 서브에이전트 소유 매트릭스 — 2026-08-29 18:15 실측

**슬롯(별도 세션) 구도는 끝났다.** 정의 파일 3개는 한 세션이 만들었고(03:1x, §9 정정), 실작업은 전부 **이 오케스트레이터 세션이 `Agent` 도구로**
띄운 서브에이전트가 했다. 각 정의의 `## 소유 파일과 경계` 절이 곧 매트릭스이고, 오늘 그 경계가 실전에서 지켜졌다(소유 밖 변경 0건, 전부 커밋 안 함).

| 파일 | 오케스트레이터 | `mode-1-codebase-wiki` | `mode-1-5-term-benchmark` | `mode-2-spec-report` |
|---|---|---|---|---|
| `codegraph/*` (`terms_db.py` 포함 — ⑤ 이후) | 검토·커밋 | **소유** (⑤⑥ 투입) | 읽기 | 읽기 |
| `docs/codegraph/terms-reading.json` | 검토 | **소유** (전수조사 원본) | 읽기 | 읽기 |
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

**하네스 7블록** (서브에이전트 프롬프트에 빠뜨리지 않을 것) — `[ROLE]` `[HARD RULES]` `[BOUNDARIES]` `[VERIFIED FACTS]` `[STEP n]` `[SELF-REVIEW]` `[REPORT]`.
`[VERIFIED FACTS]` 에는 반드시 **"이 보고를 믿지 말고 재검증하라"** 를 넣는다. 오늘 그 한 줄이 내 오류 **7건**을 잡았다 — 계획서 키 2 · 테스트 절 번호 · 디스패처 인자 · C++ 간선 어휘(드라이런이 골든 하나만 돌림) · 테스트 단언 패턴 · `edges[]` 뒤쪽 경계. **드라이런은 골든 재료 전부에 돌린다.**

---

## 6. 열린 결정 — 사용자 몫 (2026-08-29 18:15)

| # | 무엇 | 상태 | 막고 있는 것 |
|---|---|---|---|
| R1 | 시험 재료 | **해소** — Mode 1 을 terms-db 우선으로 뒤집어 이 저장소 자신의 DB 를 만들었다(계획서 7/7) | — |
| R2 | `.claude/agents/*.md` 커밋 | **해소** `2aca41a` | — |
| R3 | C++ 용어 키가 네임스페이스 포함 (`SJH::Material`) | 보류 | Mode 1.5 를 C++ 저장소에 쓸 때 |
| R4 | `collect.mjs` 코드 펜스 처리 (`a.json` 오탐) | 보류 — "지금은 결정 안 한다" | 실사용 오탐 비율 |
| R5 | 외부 노드(`(STL) std`)를 용어 DB 에서 뺄지 | 보류 | R3 과 같은 시점 |
| R6 | `pickTerms` 낱말 오탐 — `Data` `Interface` `bin` `load` `report` `src` (짧은 영어 낱말이 Plan 본문 아무 데나 걸린다) | 보류 — R4 와 같은 갈래 | 실사용 오탐 비율 |
| R7 | C# 저장소(StickRush)에 읽기 단계를 얹어 **C1(오답 보기 품질)** 시험 (terms-db 계획 D7) | 보류 | StickRush 용 Plan 이 생길 때 |
| R8 | `facts/*.md` 처럼 **SVG 다이어그램 글자 안**의 경로까지 링크할지 | 보류 — 지금은 SVG 안을 건너뛴다 | 필요가 생길 때 |
| **R10** | **인용 부패** — `terms-reading.json` 의 `where`(file:line)는 코드가 바뀌면 낡는다. 🔵 18:15 실측: Task 7 직후 근거 없음 3 → 오늘 `term-graph.ts` `build.mjs` `terms.tsx` `quiz.mjs` 를 고친 뒤 **26**. 실패(L1/L2)는 아니라 파이프라인은 돌지만 L3 가 약해진다. 대책 후보 — (가) 이름 조각으로 줄을 다시 찾아 `where` 를 고치는 `--relocate` 옵션 (나) 커밋 훅으로 검사 (다) 그냥 재조사 | 보류 — 방식은 사용자 결정 | 다음 전수조사 때 |
| **R9** | **도구를 써 볼 다음 실제 프로젝트** | **열림 — 가장 급하다.** CLAUDE.md `## ⚠ 방향` 의 목적. StickRush 는 DB 있음 · Plan 없음 | 사용자 |

---

## 7. 포인터 (2026-08-29 18:15)

| 문서 | 역할 | 상태 |
|---|---|---|
| `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` | Mode 1.5 계획. 실측 정정 주석 4건(키 2 · 디스패처 · 3문항) | 10/10 완료 |
| `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md` | Mode 1 terms-db 우선 계획. 결정 D1~D7, 정정 주석 1건(간선 어휘) | 7/7 완료 |
| `docs/superpowers/specs/llm-load-reduction/` | Mode 2 보고서 — **이해도 실측 반영**(확실 6 · 애매 3 · 모름 11 · 미측정 4), `linkRoots` → StickRush | check 5/5 |
| `docs/superpowers/specs/mode-1-terms-db-first/` | terms-db 계획의 검토 보고서 — 결정 7건, 용어 30개(미측정) | check 5/5 |
| `docs/superpowers/specs/llm-load-reduction/term-quiz.md` (+ `out/quiz_to_answers.py` · `out/term-quiz.key.json`, gitignore) | 첫 시험지 100문항과 채점 헬퍼 | 기록 |
| `docs/codegraph/terms-reading.json` | 이 저장소의 LLM 전수조사 원본(191). 파생물은 `out/codegraph-raw/` — `terms_db.py --reading` 한 줄로 재생성 | 커밋됨 |
| HANDOFF ① `…-mode-1-5-orchestration.md` | Mode 1.5 위상 정렬 §3 · 하네스 §5 · 규약 §7 | 🟡 부분 대체 — §0 슬롯 분배도 낡음(아래 배너) |
| HANDOFF ③ `…-mode-1-5-agents.md` | Mode 1/1.5/2 역할 서술 **원본** — `.claude/agents/` 가 실행본. 둘을 같이 고친다 | 활성 |
| HANDOFF ② ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ | 서브에이전트 프롬프트 기록(빌드 타깃 · 스킬 · terms-db 1~5 · 6~7 · 3문항 · 아코디언 · 자동 참조 · 경로 링크 · 물리 · 슬라이더) | 🔴 전부 완료 |
| `docs/handoffs/RESUME-2026-08-28-track-c.md` | Track C(Mode 1) 재개 — **별개 갈래**. terms-db 우선 파이프라인 반영 배너 있음 | 🟡 부분 대체 |
| `CLAUDE.md` | 저장소 규약. `## ⚠ 방향` 부터. 렌더 경로(자동 참조 · 경로 링크) · 용어집 절(아코디언 · `KNOBS` · 카드 위치) 갱신됨 | 갱신됨 |
| `~/.claude/skills/{spec-review-dashboard,term-benchmark}/SKILL.md` | 스킬 원본(사본 `.claude/skills/`) — 3문항 · 자동 참조 · 경로 링크 반영 | 동일 |

**gitignore 된 것** — `out/` (보고서 산출물 · `out/codegraph-raw/` 파생물 · 시험 정답지/답안) · `.tmp/` · `.tmp-report-tsconfig.json` · `__pycache__/`.

---

## 8. 재현 — 산출물이 사라졌을 때 (전부 결정론, 수 초)

```bash
cd $REPO_ROOT
npm test && .venv/bin/python -m pytest codegraph/ -q && npm run typecheck        # 95 · 51 · 통과

# Mode 1 — 이 저장소 자신의 terms-db.json 과 codegraph.json(투영). 원본은 docs/codegraph/terms-reading.json
.venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json
#   기대: 용어 191개 / 실패 0 · codegraph.json 노드 119 간선 76 모듈 6.  근거 없음은 3 → 26(18:15 실측) — 코드 편집으로 줄 번호가 밀린 것(R10)
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
