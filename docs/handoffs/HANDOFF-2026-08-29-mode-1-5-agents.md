# HANDOFF ③ — Mode 1 / Mode 1.5 / Mode 2 에이전트 역할 정의

> 세 mode 각각을 맡는 Claude Code 에이전트가 **자기 역할과 경계**를 알기 위한 문서다.
> 구현 Task 의 코드는 계획서에, 실행 순서는 HANDOFF ① 에 있다. 이 문서는 **"나는 무엇이고 무엇이 아닌가"** 만 답한다.

> ## 🟢 상태 — 활성. 단 이 문서는 더 이상 **유일한** 사본이 아니다 (2026-08-29 갱신)
>
> 이 문서의 세 절이 **실행 가능한 서브에이전트 정의 3개로 옮겨졌다** — `.claude/agents/*.md`.
> 아래 `## 이 문서가 실체가 된 곳` 절을 먼저 읽어라.
>
> **역할을 고칠 때는 두 곳을 같이 고친다.** 이 문서가 서술 원본이고, `.claude/agents/` 가 실행본이다.
> 한쪽만 고치면 조용히 어긋난다 — 실제로 이번 갱신에서 "CLI 4단계" 오기가 그렇게 발견됐다.

---

## 전체 그림 — 세 mode 가 한 흐름이다

```
Mode 1 ─────────────▶ Mode 1.5 ─────────────▶ Mode 2
코드베이스 위키          용어 이해도 점검          설계 검토 보고서

산출: codegraph.json    산출: terms.json         산출: out/report.html
     facts/*.md              term-study-note.md       (용어집 + 관계도 포함)
     terms-db.json ◀─ 재료    ▲
                              │ Plan / Spec
                              │ (write-plan 등으로 만든 것)
```

**Mode 1.5 는 Mode 1 과 Mode 2 를 잇는 관문이다.** Mode 2 의 판정자가 Plan 의 용어를 모르면 그 판정은 무효이므로,
**판정 전에** 빈 칸을 찾아 메운다. 사후 점검이 아니라 사전 관문이다.

**세 mode 를 섞지 않는다.** `CLAUDE.md` 가 Track A/B(Mode 2)와 Track C(Mode 1)를 섞지 말라고 규정한다. Mode 1.5 는
둘을 **잇는** 것이지 섞는 것이 아니다 — 입력은 Mode 1 의 파일이고 출력은 Mode 2 의 파일이며, 자기 코드는 `scripts/term/` 에만 있다.

---

## Mode 1 에이전트 — 코드베이스 위키

### 나는 무엇인가
코드베이스를 읽어 **위키와 정적 사실 파일**을 만든다. 파이프라인은 Python(`codegraph/*.py`)과 deep-wiki 스킬이다.

### 산출물
| 파일 | 무엇 | 만드는 것 |
|---|---|---|
| `codegraph.json` | 코드 지도 — 점(클래스)과 선(관계) | `codegraph/normalize.py` |
| `facts/modules.md` `classes.md` `external.md` `entrypoints.md` `hotspot.md` | 사람이 읽는 사실 표 | `codegraph/facts.py` |
| `ranking.json` | 모듈 중요도(PageRank·hotspot) | `codegraph/facts.py` |
| **`terms-db.json`** | **코드베이스 용어 전수 — Mode 1.5 의 재료** | `codegraph/terms_db.py` (✅ 존재. Task 1.1, 커밋 `8069517`) |
| 위키 10장 | VitePress 다중 페이지 | deep-wiki 스킬 |

### 이 mode 에 새로 붙는 것
**`terms_db.py` 와 전수조사 절차.** 2026-08-29 부터 `terms-db.json` 이 **원본**이고 `codegraph.json` 은 그 **투영**이다
(계획서 `2026-08-29-mode-1-terms-db-first.md`). 정적 수집기가 있으면 codegraph 에서 레코드를 먼저 만들고 LLM 이
뜻 · 동작 · 새 관계를 보탠다(구조 필드는 codegraph 가 이긴다). 없으면(Python/JS) LLM 읽기 레코드만으로 DB 를 만들고
`codegraph.json` 을 투영한다. **LLM 이 쓴 모든 `where` 는 L1/L2/L3 로 기계 검사한다.** 절차는 에이전트 정의
`.claude/agents/mode-1-codebase-wiki.md` 의 `## 전수조사 절차` 절에 있다.

### 나는 무엇이 아닌가
- **사람에게 묻지 않는다.** 이해도는 Mode 1.5 의 일이다
- **설계를 판정하지 않는다.** 그건 Mode 2 다
- **`means` 를 인용 없이 쓰지 않는다.** 뜻과 동작은 내가(LLM) 전수조사로 쓴다 — 단 **한 번**, 레코드마다
  `where`(file:line) 를 붙여서. `terms_db.py` 가 그 인용을 L1/L2/L3 로 기계 검사하고, 정적 수집기가 있는
  저장소에서는 구조 필드(`id kind module where`)를 codegraph 쪽으로 덮는다. 결정론은 codegraph 와 투영이
  지키고, 나는 인용으로 붙들린다

### 전제
Mode 1.5 가 시작되기 전에 **이 mode 가 완전히 WarmUp 되어 있어야 한다.** `terms-db.json` 이 없으면 Mode 1.5 는 중단하고 보고한다.

### 진입점
`bin/report-wiki` — 현재는 길잡이만 낸다. 실제 파이프라인은 Python 이라 Node 진입점이 비어 있다. 없는 기능을 있는 척하지 않는다.

---

## Mode 1.5 에이전트 — 용어 이해도 점검

### 나는 무엇인가
**인공지능 벤치마크를 사람 쪽으로 뒤집은 것.** 정답지를 만들고 → 객관식으로 묻고 → 정답률로 채점해 → 확실/애매/모름으로 가른다.

### 절차 (CLI 3단계 + Skill 1단계)

🔵 2026-08-29 실측 — `report-term` 을 인자 없이 실행하면 `사용법 — report-term <collect|grade|emit> [인자]` 가 나온다.
**명령은 셋이다.** 이 문서의 이전 판이 "CLI 4단계" 라고 적은 것은 `quiz` 명령이 있던 시절의 잔재다(Task 3.1 에서 제거됨).

```
report-term collect <plan.md> <terms-db.json>   → term-candidates.json
    코드베이스 용어 ∩ Plan 본문  +  Plan 신규 개념
        ↓
  [Skill] 신규 개념의 정답을 Plan 저자에게 묻는다. LLM 이 지어내지 않는다
  [Skill] 용어마다 객관식 3문항 + "모른다" 선택지를 만든다. 정답지는 TermMeans
  [Skill] AskUserQuestion 으로 한 용어씩 묻는다 → answers.json
        ↓
report-term grade answers.json                  → term-grades.json
    맞힌 수 2~3 확실 / 0~1 모름. "모른다" 2회 이상이면 모름 (2026-08-29 3문항 규칙. 애매 는 내지 않는다)
        ↓
report-term emit term-grades.json               → terms.json + term-study-note.md
```

### 산출물 두 갈래
| 파일 | 누가 읽나 | 무엇을 싣나 |
|---|---|---|
| `term-study-note.md` | **사람** | 모름·애매만. 이미 아는 것을 다시 싣지 않는다 |
| `terms.json` | **Mode 2** | **전부.** `{ "용어": { TermMeans, UserMentalValue } }` |

### 핵심 자료 구조 — 왜 이렇게 생겼나
```json
{ "calls[]": { "TermMeans": "누가 누구를 부르는지 모은 목록",
               "UserMentalValue": "모름" } }
```
`TermMeans` 는 **객관적 정답** — 코드베이스에서 기계로 뽑았거나 Plan 저자가 썼다. 정적·결정론적.
`UserMentalValue` 는 **주관적 이해도** — 사람마다·시점마다 다르다. 시험으로 실측했다.
둘을 한 레코드에 담되 **필드로 분리**한다. 이 저장소의 "객관 사실과 주관 판단을 한 문장에 섞지 않는다" 규율을 자료 구조에서 구현한 것이다.

### 나는 무엇이 아닌가
- **CLI 는 사람에게 묻지 않는다.** `quiz.mjs` 는 채점만 한다. 묻는 것은 Skill 이다. 이 경계를 흐리면 "도구는 판정하지 않는다" 규율이 깨진다
- **LLM 이 사용자의 지식 상태를 안다고 가정하지 않는다.** 추정은 초안이고 사용자가 고친다
- **확실한 것을 버리지 않는다.** `terms.json` 에는 전부 싣는다. 표시만 달리한다
- **문항을 스크립트로 자동 생성하지 않는다.** 오답 보기의 그럴듯함은 기계가 못 만든다
- **코드베이스 전체를 출제하지 않는다.** 이 Plan 이 요구하는 용어만

### 진입점
`bin/report-term` — `collect` · `grade` · `emit`. (`quiz` 명령은 두지 않는다 — 문항 출제는 CLI 가 아니라 스킬의 일이다. 2026-08-29 Task 3.1 실측 후 제거.)

### Skill — ✅ 저작 완료 (2026-08-29, 커밋 `1c22f65`)

`~/.claude/skills/term-benchmark/SKILL.md` — 계획서 Task 6.1. **슬롯 C 가 썼다**(HANDOFF ④). 223줄.
저장소 사본은 `.claude/skills/term-benchmark/SKILL.md` 이고 🔵 실측 `diff -q` 결과 **원본과 동일**하다.
**저장소 밖이 원본, 안이 사본이다 — 고치면 둘 다 갱신한다.**

담기로 했던 7단계가 다 들어갔다(🔵 `grep -n` 으로 확인): 전제 확인 → collect → 저자에게 정답 요청 →
출제 규율 → `AskUserQuestion` 으로 한 용어씩 묻기 → grade → emit.

**남은 것은 저작이 아니라 시험이다.** ⚖ 사용자가 실제로 시험을 쳐 봐야 문항 난이도를 판정할 수 있고,
그 전에 **시험 재료를 정해야 한다**(RESUME 문서의 열린 결정 R1).

---

## Mode 2 에이전트 — 설계 검토 보고서

### 나는 무엇인가
Spec/Plan 을 **사용자가 수용 판정을 내리기 좋은 계기판**으로 압축한다. 산문 대신 표·배지·다이어그램. 판정은 항상 사용자 몫.

### 지금 완성된 것 (2026-08-29 실측)
| 항목 | 상태 |
|---|---|
| CLI | `report-spec init` → `build` → `check` (`report` 는 위임으로 호환) |
| 컴포넌트 | 17개 — 배지·표·블록·BeforeAfter·VerdictFooter·**Glossary·TermGraph·defineTerms** |
| 용어집 | `data.ts` 의 `terms` 배열 한 곳에만 정의. 본문 인라인 참조·용어집 표·관계 그래프가 전부 거기서 나온다. **2026-08-29** — 용어집은 이해도 아코디언, 본문 참조는 빌드가 자동으로 감싼다(`scripts/wrap-terms.mjs`) |
| 관계 그래프 | d3-force 런타임. 드래그·확대·hover. `<script>` 예산 1개를 이것이 쓴다 |
| 검사 | `<script>` ≤ 1 · `tsc --noEmit` · 링크 무결성 · **용어집 대조(경고)** · builderVersion |
| 실사용 보고서 | `docs/superpowers/specs/llm-load-reduction/` — 결정 6건, 용어 24개(전부 미측정), 관계도 |

### Mode 1.5 연동 — 2026-08-29 완료 (계획서 Phase 5)
- `Term` 에 `mental?: "확실" | "애매" | "모름"` 필드가 더해졌다. **기존 필드는 그대로**
- `<Glossary>` 에 이해도 컬럼이 생겼다. 확실은 흐리게, 없으면 "미측정"
- `report-spec init` 스켈레톤의 `data.ts` 에 `terms: []` 자리와 `terms.json` 을 옮겨 적으라는 주석이 생겼다
- **`terms.json` 을 자동 import 하지 않는다.** `data.ts` 는 사람이 읽는 파일이고 값이 눈에 보여야 한다

### 나는 무엇이 아닌가
- **옛 산출물을 재현하지 않는다.** `CLAUDE.md` `## ⚠ 방향` 절. 2026-07-27 자 HTML 은 출발점이지 기준이 아니다
- **판정 푸터를 채우지 않는다.** `VerdictFooter` 는 항상 비워서 낸다
- **용어를 감으로 고르지 않는다.** Mode 1.5 가 붙은 뒤로는 `terms` 가 `terms.json` 에서 온다
- **D축(결정 불확실성)을 만들지 않는다.** A1 취소로 무기한 보류. `src/types.ts` 에 필드가 없다
- **새 런타임 스크립트를 추가하지 않는다.** 예산 1개가 찼다. 필요하면 `src/runtime/term-graph.ts` 번들에 합친다

### 진입점
`bin/report-spec` (Task 0.2 후). Skill 은 `~/.claude/skills/spec-review-dashboard/SKILL.md` — 2026-08-28 에 이 파이프라인 기준으로 포팅됐다.

---

## 이 문서가 실체가 된 곳 — `.claude/agents/` (2026-08-29)

이 문서는 **서술**이지 실행되는 것이 아니었다. 2026-08-29 에 세 절을 각각 **Claude Code 서브에이전트 정의**로 옮겼다.
그 전까지 `.claude/agents/` 도 `~/.claude/agents/` 도 **존재하지 않았다**(🔵 `ls` 로 확인 — 둘 다 `No such file or directory`).

| 정의 파일 | `name` | 옮겨 담은 절 |
|---|---|---|
| `.claude/agents/mode-1-codebase-wiki.md` | `mode-1-codebase-wiki` | `## Mode 1 에이전트` |
| `.claude/agents/mode-1-5-term-benchmark.md` | `mode-1-5-term-benchmark` | `## Mode 1.5 에이전트` |
| `.claude/agents/mode-2-spec-report.md` | `mode-2-spec-report` | `## Mode 2 에이전트` |

### 이 문서에 없던 것 중 정의 파일이 추가로 담은 것

서술만으로는 서브에이전트가 사고를 낼 수 있어 **경계와 검증을 붙였다.** 출처는 이 문서가 아니라 다른 문서다:

| 더한 것 | 어디서 왔나 |
|---|---|
| `## 소유 파일과 경계` 표 | HANDOFF ① §4 파일 소유 매트릭스 + §0 슬롯 충돌 매트릭스에서 그 mode 의 행만 |
| `## 지켜야 할 규율` 표 | HANDOFF ① §7 가드레일 + 이 문서 `## 세 에이전트가 공유하는 규율` |
| 검증 명령 (`npm test` · `pytest` · `typecheck`) | HANDOFF ① §7. **`node --test test/` 는 Node 25 에서 죽는다**는 함정 포함 |
| **커밋 금지** 를 규율표에 명시 | HANDOFF ① §2(마) — 서브에이전트는 구현 + 검증 + 보고까지만 |
| 보고 형식 `DONE / DONE_WITH_CONCERNS / BLOCKED` | HANDOFF ① §5 하네스 |
| frontmatter `tools` 목록 | Mode 1.5 만 `AskUserQuestion` 을 갖는다 — **묻는 것은 Mode 1.5 뿐**이라는 이 문서의 규정을 도구 권한으로 구현한 것 |

### 아직 안 된 것 — 이어서 할 일

| # | 할 일 | 왜 아직인가 |
|---|---|---|
| **1** | **세 정의 파일 커밋** | 미추적 상태(`?? .claude/agents/`). 커밋은 사용자 승인 후. `git add .claude/agents/` 로 좁혀 **한 묶음으로** — 셋이 한 벌이다 |
| **2** | **`mode-2-spec-report` 가 실제로 로드되는지 확인** | 아래 참조 |
| 3 | 세 에이전트에 실제 작업을 태워 보기 | 정의만 있고 **한 번도 실행되지 않았다.** 경계가 실전에서 맞는지는 아직 모른다 |

**#2 — 확인이 필요한 관측.** 정의 파일 3개를 만든 뒤 하네스가 새 에이전트를 알렸는데 그 목록에
`mode-1-codebase-wiki` 와 `mode-1-5-term-benchmark` **둘만 있었고 `mode-2-spec-report` 가 없었다.**
🔵 실측으로는 세 파일 모두 frontmatter 4줄이 같은 꼴이고 YAML 로 깨질 만한 문자(값 안의 `: `, ` #`, 들여쓰기)가 없다.
**원인을 특정하지 못했다** — 목록이 잘렸을 수도, 스캔 시점 문제일 수도 있다.
확인 방법: `/agents` 로 세 개가 다 보이는지 본다. 안 보이면 그때 원인을 판다. **정의 파일에 결함이 있다고 단정하지 말 것.**

### 역할을 고칠 때의 규약

**이 문서와 `.claude/agents/*.md` 는 같이 고친다.** 한쪽만 고치면 어긋난다.
정의 파일은 **각 슬롯 소유**다(HANDOFF ① §0) — 오케스트레이터는 검토하고, 슬롯 밖에서 남의 정의를 고치지 않는다.

---

## 세 에이전트가 공유하는 규율

| 규율 | 내용 |
|---|---|
| 도구는 판정하지 않는다 | 계산·정렬·병치만. 판정은 사람 |
| 객관과 주관을 섞지 않는다 | 문장에서도, 자료 구조에서도 |
| 결정론 | 같은 입력이면 같은 출력. LLM 은 결정론이 깨져도 되는 자리에만 |
| 거울 함정 | 과잉 설계를 잡는 도구를 과잉 설계하지 않는다. 구현자 1·소비자 1이면 인터페이스를 만들지 않는다 |
| 읽는 사람은 배경 지식이 없다 | 객체지향을 갓 배운 대학 1학년 눈높이 |
| 옛 산출물은 기준이 아니다 | 출발점일 뿐. 새 출력을 거기에 맞추지 않는다 |
| 커밋은 사용자 승인 후 | 서브에이전트는 커밋하지 않는다 |

---

## 다음 세션이 이 문서를 열었을 때 — 한 문단 요약

세 mode 의 역할 서술은 **완결됐고**, 그것이 `.claude/agents/` 의 실행 가능한 정의 3개로 옮겨졌다(미커밋).
Mode 1.5 쪽은 계획서 Task 10개가 전부 끝났고 `term-benchmark` 스킬까지 있다 — **코드는 더 쓸 것이 없다.**
막혀 있는 것은 하나다: **시험 재료를 어디서 얻을 것인가**(RESUME 문서 R1). `terms-db.json` 을 만들려면
Mode 1(Track C)이 외부 저장소에서 돌아야 하는데 아직 안 돌았다. 그래서 다음 걸음은 코드가 아니라
**사용자 결정**이다. 결정이 나면 그때 세 에이전트에 실작업을 태운다.

---

## 변경 이력 (추가만)

- 2026-08-29 03:10 — 최초 작성. 세 mode 의 역할·경계 서술. 이 시점에 `.claude/agents/` 는 없었다.
- 2026-08-29 (같은 날 늦게) — 세 절을 `.claude/agents/*.md` 3개로 옮김. 그 과정에서 실측으로 잡은 것:
  - **"CLI 4단계" 는 오기.** `report-term` 명령은 `collect` · `grade` · `emit` 셋이다. `quiz` 가 있던 시절의 잔재.
    같은 오기가 HANDOFF ① 세 곳(§0 슬롯표 · §3 의존 그래프 · §3 직렬 강제 표)에도 있어 함께 고쳤다.
  - **Task 6.1 스킬은 이미 완료돼 있었다** — 이 문서가 "슬롯 C 가 쓴다"(미래형)로 적고 있었으나
    `~/.claude/skills/term-benchmark/SKILL.md` 223줄이 커밋 `1c22f65` 로 들어와 있다.
  - `mode-2-spec-report` 가 하네스 에이전트 목록에 안 보인 관측 1건 — **원인 미특정.** `/agents` 로 확인할 것.
- 2026-08-29 — Mode 1 절: terms-db 우선 구조 반영. "means 를 풍부하게 쓰지 않는다" 를 "인용 없이 쓰지 않는다" 로 개정.
