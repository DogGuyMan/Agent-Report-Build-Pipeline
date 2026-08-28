# HANDOFF ③ — Mode 1 / Mode 1.5 / Mode 2 에이전트 역할 정의

> 세 mode 각각을 맡는 Claude Code 에이전트가 **자기 역할과 경계**를 알기 위한 문서다.
> 구현 Task 의 코드는 계획서에, 실행 순서는 HANDOFF ① 에 있다. 이 문서는 **"나는 무엇이고 무엇이 아닌가"** 만 답한다.

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
| **`terms-db.json`** | **코드베이스 용어 전수 — Mode 1.5 의 재료** | `codegraph/terms_db.py` (**신설 예정**, 계획서 Task 1.1) |
| 위키 10장 | VitePress 다중 페이지 | deep-wiki 스킬 |

### 이 mode 에 새로 붙는 것
**`terms_db.py` 하나.** `codegraph.json` 에서 이름·종류·위치·이웃을 뽑아 `{ "용어": { kind, module, where, means, neighbors } }` 를 만든다.
**기계가 아는 사실만 적는다.** 사람이 읽을 설명은 Mode 1.5 가 LLM 으로 채우고 사용자가 검수한다.

### 나는 무엇이 아닌가
- **사람에게 묻지 않는다.** 이해도는 Mode 1.5 의 일이다
- **설계를 판정하지 않는다.** 그건 Mode 2 다
- **`means` 를 풍부하게 쓰려고 하지 않는다.** 결정론이 목적이다 — 같은 입력이면 같은 출력. LLM 을 여기 끼우면 그게 깨진다

### 전제
Mode 1.5 가 시작되기 전에 **이 mode 가 완전히 WarmUp 되어 있어야 한다.** `terms-db.json` 이 없으면 Mode 1.5 는 중단하고 보고한다.

### 진입점
`bin/report-wiki` — 현재는 길잡이만 낸다. 실제 파이프라인은 Python 이라 Node 진입점이 비어 있다. 없는 기능을 있는 척하지 않는다.

---

## Mode 1.5 에이전트 — 용어 이해도 점검

### 나는 무엇인가
**인공지능 벤치마크를 사람 쪽으로 뒤집은 것.** 정답지를 만들고 → 객관식으로 묻고 → 정답률로 채점해 → 확실/애매/모름으로 가른다.

### 절차 (CLI 4단계 + Skill 1단계)
```
report-term collect <plan.md> <terms-db.json>   → term-candidates.json
    코드베이스 용어 ∩ Plan 본문  +  Plan 신규 개념
        ↓
  [Skill] 신규 개념의 정답을 Plan 저자에게 묻는다. LLM 이 지어내지 않는다
  [Skill] 용어마다 객관식 5문항 + "모른다" 선택지를 만든다. 정답지는 TermMeans
  [Skill] AskUserQuestion 으로 한 용어씩 묻는다 → answers.json
        ↓
report-term grade answers.json                  → term-grades.json
    맞힌 수 4~5 확실 / 2~3 애매 / 0~1 모름. "모른다" 3회 이상이면 모름
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
`bin/report-term` — `collect` · `grade` · `emit`. (`quiz` 는 `grade` 의 별칭으로 남겨 두되 사람에게 묻는 기능은 넣지 않는다.)

### Skill
`~/.claude/skills/term-benchmark/SKILL.md` — 계획서 Task 6.1. **오케스트레이터가 직접 쓴다.** 담을 것: 전제 확인 → collect → 저자에게 정답 요청 → 출제 규율 → 한 용어씩 묻기 → grade → emit.

---

## Mode 2 에이전트 — 설계 검토 보고서

### 나는 무엇인가
Spec/Plan 을 **사용자가 수용 판정을 내리기 좋은 계기판**으로 압축한다. 산문 대신 표·배지·다이어그램. 판정은 항상 사용자 몫.

### 지금 완성된 것 (2026-08-29 실측)
| 항목 | 상태 |
|---|---|
| CLI | `report init` → `build` → `check` (곧 `report-spec` 으로 개명, `report` 는 위임으로 호환) |
| 컴포넌트 | 17개 — 배지·표·블록·BeforeAfter·VerdictFooter·**Glossary·TermGraph·defineTerms** |
| 용어집 | `data.ts` 의 `terms` 배열 한 곳에만 정의. 본문 인라인 참조·용어집 표·관계 그래프가 전부 거기서 나온다 |
| 관계 그래프 | d3-force 런타임. 드래그·확대·hover. `<script>` 예산 1개를 이것이 쓴다 |
| 검사 | `<script>` ≤ 1 · `tsc --noEmit` · 링크 무결성 · **용어집 대조(경고)** · builderVersion |
| 실사용 보고서 | `docs/superpowers/specs/llm-load-reduction/` — 결정 6건, 용어 13개, 관계도 |

### Mode 1.5 가 붙으면 바뀌는 것 (계획서 Phase 5)
- `Term` 에 `mental?: "확실" | "애매" | "모름"` 필드가 더해진다. **기존 필드는 그대로**
- `<Glossary>` 에 이해도 컬럼이 생긴다. 확실한 것은 흐리게
- `report-spec init` 스켈레톤의 `data.ts` 에 `terms: []` 자리와 `terms.json` 을 옮겨 적으라는 주석이 생긴다
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
