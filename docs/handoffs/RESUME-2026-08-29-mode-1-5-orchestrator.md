# RESUME — Mode 1.5 오케스트레이터 세션 (2026-08-29)

> **이 문서가 재개의 단일 진입점이다.** 새 세션은 이것 하나만 읽고 이어갈 수 있어야 한다.
> 다른 문서는 심화 자료이지 시작 전제가 아니다.
>
> **이 문서가 대체하는 것** — `HANDOFF-2026-08-29-mode-1-5-orchestration.md` 의 "TL;DR" 과 "§1 세계의 상태" 절.
> 그 문서의 나머지(§0 슬롯 분배 · §3 위상 정렬 · §4 소유 매트릭스 · §5 하네스 · §7 규약)는 **여전히 유효**하고 여기서 반복하지 않는다.

---

## TL;DR + 바로 다음 한 걸음

**어디까지 왔나** — Mode 1.5(용어 이해도 벤치마크) 계획서 `2026-08-29-mode-1-5-term-benchmark.md` 의
**Task 10개 전부 완료·커밋**됐다. CLI `report-term collect → grade → emit` 이 end-to-end 로 돈다(스크래치패드 실측).
Mode 2 연동(`Term.mental` · 이해도 컬럼 · init 스켈레톤)도 끝났다. `term-benchmark` 스킬이 저장소 밖과 안에 있다.

**서브에이전트 정의 3개가 `.claude/agents/` 에 있다(미커밋).** ⚠ **이 문서의 최초 판이 "세 슬롯이 각자 만들었다"고 적은 것은
틀렸다** — 🔵 mtime 실측(03:17:24 · 03:18:02 · 03:18:39)과 그 세션의 첫 `ls` 결과(디렉토리 부재)로 확인했다.
**한 세션이 HANDOFF ③ 을 읽고 셋을 연달아 만들었다.** 아래 §4 를 보라.

**슬롯 B·C·D 의 실작업(외부 저장소)은 아직 착수 전**이다 — `terms-db.json` 도, 슬롯 D 의 새 보고서도 아직 없다(실측).

**바로 다음 한 걸음 (2026-08-29 15:00 갱신)** — 이 저장소 안에서 할 수 있는 일은 **다 했다.** Mode 1(전수조사 `terms-reading.json` 191개) →
Mode 1.5(첫 시험, 확실 6 · 애매 3 · 모름 11) → Mode 2(`llm-load-reduction` 보고서에 이해도 반영, check 5/5) 가 한 번 끝까지 돌았다.
다음은 **사용자 결정** — 도구를 **다른 실제 프로젝트**에 써 보는 것(CLAUDE.md `## ⚠ 방향`). StickRush 는 DB 는 있으나 Plan 이 없다.
열린 것: D7(C# 저장소에 읽기 단계 → C1 시험) · R3 · R4 · R5 · R6(낱말 오탐 `bin` `load` `report` `src` `Data` …).

---

## 1. 세계의 상태 — 2026-08-29 03:20 재측정

| 항목 | 값 |
|---|---|
| 저장소 | `$REPO_ROOT` (`~/report-builder` 는 **존재하지 않는다**) |
| 브랜치 | `feat/report-builder` |
| HEAD | `a49e285 [docs] : Mode 1.5 오케스트레이터 세션 재개 문서와 핸드오프 부분 대체 배너` (🔵 03:2x 재측정) |
| 이 세션 커밋 | **21개** (`95910ef` 이후). 아래 §2 표 참조 |
| 미커밋 | `.claude/agents/` 3개 (**한 세션이 만든 한 벌.** §4 정정 참조) · `docs/prompt/checklist.yaml` (사용자 메모, 의도적 미추적) |
| Node 테스트 | **64 통과** (`npm test`) |
| Python 테스트 | **31 통과** (`.venv/bin/python -m pytest codegraph/ -q`) |
| 타입 검사 | 통과 (`npm run typecheck`) |
| `report-spec check` (llm-load-reduction) | **5/5 통과**, 용어집 경고 0 (용어 24개) |
| 스킬 | `~/.claude/skills/term-benchmark/SKILL.md` 223줄 (슬롯 C 저작) · 저장소 사본 `.claude/skills/term-benchmark/` 커밋됨 |

**저장소 밖 자산** — `~/.claude/skills/spec-review-dashboard/SKILL.md` (174줄, 용어집 3종 반영) · `~/.claude/skills/term-benchmark/SKILL.md`.
둘 다 저장소 안 `.claude/skills/` 에 사본이 있다. **저장소 밖이 원본, 안은 사본**이다. 고치면 둘 다 갱신한다.

---

## 2. Task 상태 — 10/10

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

**작업자 역할로 병행한 것** — `spec-review-dashboard` 스킬 용어집 반영 `d465df7` · 끊어진 심볼릭 링크 `33f4556` ·
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

**정정된 것** (이전 문서가 틀렸던 것):
- 핸드오프 ② · ④ 는 작업 완료 후에도 "붙여넣어 실행하라"고 말하고 있었다 → 🔴 완료 배너를 달았다(`1c22f65` `8b71c25`).
  **원칙 5(발신 측 정리)를 늦게 한 것**이며, 사용자가 지적해 고쳤다.

---

## 4. 병렬 슬롯 충돌 매트릭스 — 2026-08-29 03:20 실측

**한 세션이** HANDOFF ③ 을 읽고 `.claude/agents/` 에 서브에이전트 정의 3개를 연달아 만들었다.
정의 파일의 `## 소유 파일과 경계` 절은 그 세션이 **핸드오프 ① §4·§0 에서 각 mode 의 행을 뽑아 넣은 것**이라
당연히 일치한다 — 서로 다른 세션이 독립으로 같은 결론에 도달한 것이 **아니다.**

🔴 **정정(실측).** 이 문서의 최초 판과 핸드오프 ① §9 는 "슬롯 B 가 `mode-1-codebase-wiki.md` 를 만들었다",
"세 슬롯이 각자 만들었다" 고 적었다. **둘 다 틀렸다.** 근거 — 세 파일 mtime 은 `03:17:24` · `03:18:02` · `03:18:39` 로
40초 안에 연달아 찍혔고, 그 세션이 착수 전 돌린 `ls` 는 `.claude/agents/` 와 `~/.claude/agents/` **둘 다 부재**로 나왔다.
커밋 `c2d7015`(03:18:18)가 그 사이에 끼어 첫 파일 하나만 보고 슬롯 B 로 귀속한 것이다.
**딸린 결과 — 정의 파일의 커밋 주체를 슬롯별로 나눌 필요가 없다.** 셋을 한 커밋으로 낸다.

| 파일 | A 오케스트레이터 | B `mode-1-codebase-wiki` | C `mode-1-5-term-benchmark` | D `mode-2-spec-report` |
|---|---|---|---|---|
| `scripts/term/*` · `test/term.test.mjs` | 검토 | 읽기 | **소유** | 읽기 |
| `scripts/dispatch.mjs` · `bin/*` | **소유** | 읽기 | 읽기 (명령표 변경은 A 승인) | 읽기 |
| `codegraph/*` (terms_db 제외) | 읽기 | **소유** | 읽기 | 읽기 |
| `codegraph/terms_db.py` | 참조 | **건드리지 말 것** | 읽기 | — |
| `normalize.py` 출력 키 | — | **바꾸지 말 것** | — | — |
| `src/*` · `scripts/{build,check,init,svg}.mjs` · `test/components.test.mjs` | 검토 | 읽기 | 읽기 | **소유** (추가만) |
| `CLAUDE.md` | 소유 | Track C 절만 | — | — |
| `~/.claude/skills/term-benchmark/` | 검토 | — | 읽기 전용 (고칠 일은 보고) | — |
| `.claude/agents/<자기 것>.md` | — | 소유 | 소유 | 소유 |
| 다른 저장소 `specs/<slug>/` | — | 접근 안 함 | — | **소유** |

**동시 진행 가능** — B · C · D 는 서로 파일이 안 겹친다. **커밋은 각자 `git add <경로>` 로 좁힌다. `-A` 금지.**
인덱스에 남의 파일이 있으면 `git status --porcelain` 으로 확인하고 자기 것만 스테이징한다.

**슬롯 B·D 실작업 착수 여부** — 03:20 실측: 외부 저장소(`$DEV_ROOT`)에 새 `terms-db.json` 도 새 `specs/*/data.ts` 도 없다.
**둘 다 정의 파일만 만들고 실작업은 아직이다.**

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
`[VERIFIED FACTS]` 에는 반드시 **"이 보고를 믿지 말고 재검증하라"** 를 넣는다. 이 세션에서 그 한 줄이 내 오류 4건을 잡았다.

---

## 6. 열린 결정 — 사용자 몫

| # | 무엇 | 왜 지금 안 정했나 | 막고 있는 것 |
|---|---|---|---|
| **R1** | ~~시험 재료를 어디서 얻을지~~ **→ 2026-08-29 05:40 방향 확정.** 사용자 결정: Mode 1 을 **terms-db 우선** 구조로 뒤집어 이 저장소 자신의 DB 를 만든다. 계획서 `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md` (Task 7개, 코드 드라이런 19/19 통과) + 검토 보고서 `docs/superpowers/specs/mode-1-terms-db-first/` (check 5/5). **착수 승인 대기** | — | 계획서 Task 1~7 실행 (`mode-1-codebase-wiki` 에 위임) |
| R2 | `.claude/agents/*.md` 3개 커밋 | 커밋은 사용자 승인 후. (소유가 갈린다는 이전 사유는 **위 §4 정정으로 소멸**) | 없음 (미커밋 상태로도 동작) |
| R3 | C++ 용어 키가 네임스페이스 포함 (`SJH::Material`) | 스킬의 자연어 보충 단계로 메우게 했으나 근본 해결 아님 | Mode 1.5 를 C++ 저장소에 쓸 때 |
| R4 | `collect.mjs` 코드 펜스 처리 | `a.json` 오탐. "지금은 결정 안 한다" 로 보류됨 | 오탐 비율이 실사용에서 드러날 때 |
| R5 | 외부 노드(`(STL) std`) 를 용어 DB 에서 뺄지 | `means` 가 어색 | R3 과 같은 시점 |

**R1 이 가장 급하다.** 세 선택지: ① `terms-db.json` 없이 Plan 신규 개념 34개만으로 스킬 시험 (가장 빠름) ② 슬롯 B 의 Track C 완료 대기
③ 슬롯 D 의 프로젝트에서 Mode 1 부터.

---

## 7. 포인터

| 문서 | 역할 | 상태 |
|---|---|---|
| `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` | Task 별 코드. **실측 정정 주석 3건** 포함 | 10/10 완료 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-orchestration.md` ① | 슬롯 분배 §0 · 위상 정렬 §3 · 하네스 §5 · 규약 §7 | **활성** — TL;DR·§1 은 이 문서가 대체 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-build-targets.md` ② | Task 0.1 프롬프트 | 🔴 완료 (기록용) |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` ③ | Mode 1/1.5/2 역할 정의 | **활성** — 슬롯 B·C·D 가 이것을 에이전트 정의로 옮겼다 |
| `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-skill.md` ④ | Task 6.1 프롬프트 | 🔴 완료 (기록용) |
| `docs/handoffs/RESUME-2026-08-28-track-c.md` | Track C(Mode 1) 재개 | 활성 — **별개 갈래**, 슬롯 B 가 읽는다 |
| `.claude/agents/mode-{1-codebase-wiki,1-5-term-benchmark,2-spec-report}.md` | 서브에이전트 정의 | 미커밋 (각 슬롯 소유) |
| `CLAUDE.md` | 저장소 규약. `## ⚠ 방향` 절부터 | 갱신됨 |

**gitignore 된 것** — `out/` · `.tmp/` · `.tmp-report-tsconfig.json` · `__pycache__/`. 스크래치패드(`/private/tmp/claude-501/.../scratchpad/`)의
`rb-quiz/`(answers.json · term-grades.json · terms.json · term-study-note.md) 는 **세션이 끝나면 사라진다** — 재개 시 §8 로 재현한다.

---

## 8. 재현 — 스크래치 자료가 사라졌을 때

Mode 1.5 CLI 의 end-to-end 를 30초에 다시 볼 수 있다:

```bash
mkdir -p /tmp/rb-quiz && cd /tmp/rb-quiz
printf '{"calls[]":{"correct":1,"dontKnow":0,"means":"호출 목록"},"Renderer":{"correct":5,"dontKnow":0,"means":"렌더러"},"WarmUp":{"correct":2,"dontKnow":3,"means":"캐시"}}\n' > answers.json
report-term grade answers.json      # 기대: 확실 1 · 애매 0 · 모름 2
report-term emit term-grades.json   # 기대: terms.json 용어 3개 (전부 실림) / 학습 노트 학습 대상 2개
cat terms.json                       # Renderer 가 UserMentalValue: "확실" 로 들어 있어야 한다
```

`collect` 실측 (DB 없이):
```bash
cd /tmp/rb-quiz && report-term collect $REPO_ROOT/docs/superpowers/plans/2026-08-28-llm-load-reduction.md
# 기대: 신규 개념 34개. a.json 은 알려진 오탐(R4)
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
