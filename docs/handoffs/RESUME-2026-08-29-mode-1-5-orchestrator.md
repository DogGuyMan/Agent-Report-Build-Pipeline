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

**병렬 슬롯 B·C·D 가 열려 있다.** 셋 다 `.claude/agents/` 에 서브에이전트 정의를 만들었고(미커밋), **실작업(외부 저장소)은
아직 착수 전**이다 — `terms-db.json` 도, 슬롯 D 의 새 보고서도 아직 없다(실측).

**바로 다음 한 걸음** — 두 갈래 중 하나. 둘 다 **사용자 결정이 먼저**다:

> **(가) 시험 재료를 정한다.** `terms-db.json` 없이 Plan 신규 개념만으로 스킬을 시험할지(가장 빠름, 코드베이스 용어 0개),
> 슬롯 B 가 Track C 를 돌려 외부 저장소에서 `terms-db.json` 을 만들 때까지 기다릴지, 슬롯 D 의 프로젝트에서 Mode 1 부터 갈지.
>
> **(나) 세 에이전트 정의(`.claude/agents/*.md`)를 커밋한다.** 각 슬롯 소유라 오케스트레이터가 대신 커밋하지 않았다.
> 사용자가 "커밋해도 된다"고 하면 `git add .claude/agents/` 로 좁혀 한 번에 커밋한다 — 셋이 한 묶음이다.

---

## 1. 세계의 상태 — 2026-08-29 03:20 재측정

| 항목 | 값 |
|---|---|
| 저장소 | `$REPO_ROOT` (`~/report-builder` 는 **존재하지 않는다**) |
| 브랜치 | `feat/report-builder` |
| HEAD | `8b71c25 [docs] : 스킬 저작 핸드오프 완료 배너` |
| 이 세션 커밋 | **21개** (`95910ef` 이후). 아래 §2 표 참조 |
| 미커밋 | `.claude/agents/mode-1-codebase-wiki.md` · `mode-1-5-term-benchmark.md` · `mode-2-spec-report.md` (**슬롯 B·C·D 소유**) · `docs/prompt/checklist.yaml` (사용자 메모, 의도적 미추적) |
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

세 슬롯이 각자 `.claude/agents/` 에 서브에이전트 정의를 만들었다. **소유 경계가 핸드오프 ① §0 과 정확히 일치**한다
(서로 다른 세션이 같은 문서를 읽고 만들었다). 그 정의 파일의 `## 소유 파일과 경계` 절이 곧 매트릭스다.

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
| **R1** | **시험 재료를 어디서 얻을지** | 이 저장소는 Python 이라 `terms_db.py` 입력을 자기에게서 못 만든다 | **스킬 실사용 전체** |
| R2 | `.claude/agents/*.md` 3개 커밋 | 각 슬롯 소유 | 없음 (미커밋 상태로도 동작) |
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
