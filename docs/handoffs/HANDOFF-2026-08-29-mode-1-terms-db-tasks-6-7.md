# HANDOFF ⑥ — Mode 1 terms-db 우선 파이프라인 Task 6·7 (mode-1-codebase-wiki 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 06:50). 이 프롬프트를 다시 실행하지 말 것.**
> `mode-1-codebase-wiki` 가 Task 6(절차 문서, `b2e1c78`) 과 Task 7(전수조사, `a9b9080`) 을 마쳤고 오케스트레이터가 직접 재검증했다 —
> 검사 `용어 191개 / 실패 0 / 근거 없음 3` · 투영 노드 119 · `collect` known 26(필수 8 전부) · 인용 검증기 L3 탐침 통과.
> **DONE_WITH_CONCERNS** 4건은 RESUME 변경 이력 06:50 항목에. 사용자 결정 — `C-19` `M4` `U5` 레코드는 **그대로 둔다.**
> 이 문서는 **기록용**이다. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.
> Task 1~5 는 `HANDOFF-2026-08-29-mode-1-terms-db-tasks-1-5.md` (🔴 완료, `1ad879a`).

```
[ROLE]
당신은 $REPO_ROOT (브랜치 feat/report-builder) 의 Mode 1 에이전트 mode-1-codebase-wiki 다.
목표 둘, 순서대로: Task 6 — 전수조사 절차를 당신의 정의 파일과 역할 서술 원본에 같이 적는다.
Task 7 — 그 절차대로 이 저장소 35개 파일을 실제로 읽고 docs/codegraph/terms-reading.json 을 쓴 뒤,
terms_db.py 로 검사해 실패 0 을 만들고, Mode 1.5 의 collect 가 known 8개 이상을 잡는지 확인한다.
Task 7 은 코드가 아니라 데이터다 — LLM 추론 단계이며, 이 저장소에서 처음 하는 일이다.

[HARD RULES]
- 커밋하지 않는다. git add 도 하지 않는다. 계획서의 "Step 6: 커밋" 은 건너뛴다.
- codegraph/*.py 를 고치지 않는다. Task 1~5 는 끝났고 커밋됐다. Task 7 도중 terms_db.py 의 결함을 발견하면 고치지 말고 BLOCKED 로 보고한다.
- "검증됨" "입증" "증명" 이라는 낱말을 쓰지 않는다. 한국어. 읽는 사람은 객체지향을 갓 배운 대학 1학년이다.
- 코드에 글자로 없는 것은 사전에 쓰지 않는다. 인용 없는 뜻은 싣지 않는다.
- neighbors 는 쓰지 않는다 — 기계가 다시 센다.

[BOUNDARIES]
- 소유: .claude/agents/mode-1-codebase-wiki.md · docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md (Mode 1 절과 변경 이력만) ·
  docs/codegraph/terms-reading.json (디렉토리 신규) · out/codegraph-raw/ 의 생성물(gitignore).
- 건드리지 않음: codegraph/ · scripts/ · src/ · test/ · CLAUDE.md · 계획서 · 다른 핸드오프 · .claude/agents/ 의 다른 두 정의.

[VERIFIED FACTS — 2026-08-29 06:25 실측. 이 보고를 믿지 말고 시작 전에 재확인하라]
- HEAD 는 a41f286 이어야 한다. 작업 트리 미추적은 docs/prompt/ 뿐이다. pytest 는 51 passed.
- CLI: .venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json
  → 기본 출력 디렉토리는 <repo>/out/codegraph-raw/ (terms-db.json + codegraph.json). 마지막 줄에 "실패 N / 근거 없음 M". 실패>0 이면 exit 1.
- 레코드 검사 규칙(terms_db.py check_terms): source="reading" 레코드는 kind 가 KINDS 안이어야 하고, kind 가 module·external 이 아니면 where 필수.
  where 는 "경로:줄". L1 파일 없음·L2 줄 없음 = 실패. L3 = 그 줄 앞뒤 1줄 창에 이름 조각이 없으면 "근거 없음"(실패 아님).
  이름 조각: file·artifact·key·concept·module 은 키 글자 그대로("[]" 만 뗀다), 그 밖은 마지막 조각(terms_db.main → main).
  uses[].kind 는 inheritance realization composition aggregation association dependency 여섯뿐. uses[].to 는 사전에 있는 키여야 한다.
- KINDS = class struct enum interface delegate record external function file module artifact key concept.
- 전수조사 대상 35파일 (find 결과, 테스트·probe 제외):
  bin/report bin/report-spec bin/report-term bin/report-wiki
  codegraph/clangd_refs.py codegraph/demermaid.py codegraph/facts.py codegraph/fix_citation_paths.py codegraph/normalize.py
  codegraph/render_classes.py codegraph/render_modules.py codegraph/reverse_refs.py codegraph/terms_db.py codegraph/verify_citations.py
  scripts/build.mjs scripts/check.mjs scripts/dispatch.mjs scripts/init.mjs scripts/lib.mjs scripts/patch-legacy.mjs scripts/svg.mjs
  scripts/term/collect.mjs scripts/term/emit.mjs scripts/term/quiz.mjs
  src/components/badges.tsx src/components/BeforeAfter.tsx src/components/blocks.tsx src/components/index.ts src/components/tables.tsx
  src/components/terms.tsx src/components/VerdictFooter.tsx src/index.ts src/page.tsx src/runtime/term-graph.ts src/types.ts
  (def / class / export 104개. main 은 파이썬 5파일에 있어 키가 겹친다 → 겹친 전원 <파일줄기>.main)
- Plan llm-load-reduction 의 용어 중 이 저장소 코드에 글자로 있는 것 (grep -rlF 파일 수):
  codegraph.json 8 · roslyn-dump.json 4 · C-19 3 · calls[] 3 · PageRank 3 · hotspot 3 · WarmUp 2 · members[] 2 · edges[] 1 · M4 1 · U5 1.
  (C-20 C-21 M1 M2 U2 U3 U4 U6 무효화 calls.json methods[] 는 코드에 없다 → 쓰지 않는다)
- Mode 1.5 collect 는 PATH 의 report-term 으로 돈다: report-term collect <plan.md> <terms-db.json> → cwd 에 term-candidates.json.
  pickTerms 는 키를 Plan 본문에서 낱말 경계 정규식으로 찾는다 — 키가 Plan 의 표기와 글자까지 같아야 잡힌다(calls[] 는 calls[] 로).

========================================================================
[STEP — 계획서 Task 6·7 을 그대로 옮김. Step 의 "커밋" 은 건너뛴다]

## Task 6: 전수조사 절차 — 에이전트 정의와 역할 문서를 같이 고친다

코드가 아니라 **LLM 이 따를 절차**다. 두 문서를 같이 고친다 — "한쪽만 고치면 조용히 어긋난다"(HANDOFF ③ 머리말).

**Files:**
- Modify: `.claude/agents/mode-1-codebase-wiki.md` — `## 나는 무엇이 아닌가` 의 셋째 항목 교체, `## 소유 파일과 경계` 표에 두 행 추가, `## 전수조사 절차` 절 신설 (`## 전제` 앞에)
- Modify: `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` — `## Mode 1 에이전트` 절의 `### 이 mode 에 새로 붙는 것` 과 `### 나는 무엇이 아닌가` 셋째 항목을 같은 내용으로

- [ ] **Step 1: `.claude/agents/mode-1-codebase-wiki.md` 의 셋째 규율을 교체**

찾을 것:
```
- **`means` 를 풍부하게 쓰려고 하지 않는다.** 결정론이 목적이다 — 같은 입력이면 같은 출력.
  LLM 을 여기 끼우면 그게 깨진다
```
바꿀 것:
```
- **`means` 를 인용 없이 쓰지 않는다.** 뜻과 동작은 내가(LLM) 전수조사로 쓴다 — 단 **한 번**, 레코드마다
  `where`(file:line) 를 붙여서. `terms_db.py` 가 그 인용을 L1/L2/L3 로 기계 검사하고, 정적 수집기가 있는
  저장소에서는 구조 필드(`id kind module where`)를 codegraph 쪽으로 덮는다. 결정론은 codegraph 와 투영이
  지키고, 나는 인용으로 붙들린다
```

- [ ] **Step 2: 같은 파일 `## 소유 파일과 경계` 표에 두 행 추가 (`codegraph/terms_db.py` 행 아래)**

```
| `docs/codegraph/terms-reading.json` (이 저장소 자신을 조사할 때) | **소유** — 내 전수조사 원본 |
| `out/codegraph-raw/terms-db.json` · `codegraph.json` | 생성만. gitignore 다 — 원본에서 CLI 한 줄로 재생성 |
```

- [ ] **Step 3: 같은 파일에 `## 전수조사 절차` 절을 `## 전제` 바로 앞에 신설**

````markdown
## 전수조사 절차 — terms-reading.json 을 쓰는 법 (2026-08-29 신설)

LLM 추론은 **한 번**이다. 그 한 번에 뜻 · 동작 · 관계를 다 얻고, `codegraph.json` 은 거기서 투영한다.

1. **대상 파일을 고정한다.** 테스트 · probe · 캐시는 뺀다. 이 명령의 출력이 조사 범위다:
   ```bash
   find codegraph scripts src bin -type f \( -name "*.py" -o -name "*.mjs" -o -name "*.ts" -o -name "*.tsx" -o -path "bin/*" \) \
     -not -name "test_*" -not -name "probe_*" -not -path "*/__pycache__/*" | sort
   ```
2. **파일마다 레코드를 쓴다.** 순서는 위 목록 순서, 파일 안은 줄 번호 순서. 종류별 규칙:
   | 무엇 | `kind` | 키 | `where` |
   |---|---|---|---|
   | 소스 파일 | `file` | 파일명 (`normalize.py`, `collect.mjs`) | `경로:1` |
   | 함수 · 클래스 · 컴포넌트 | `function` / `class` | 맨 이름. **다른 파일과 충돌하면 충돌한 전원** `<파일줄기>.<이름>` (`terms_db.main`, `facts.main`) | 선언 줄 |
   | 산출 파일 (`codegraph.json` `terms-db.json` `report.html`) | `artifact` | 파일명 | 그 파일을 **쓰는** 줄 (`json.dump` · `writeFileSync`) |
   | 출력 JSON 의 키 (`nodes[]` `edges[]` `calls[]`) | `key` | `이름[]` (배열) 또는 `이름` | 그 키를 **채우는** 줄 |
   | 코드가 구현하는 개념 (`PageRank` `hotspot` `WarmUp`) | `concept` | 코드에 적힌 그대로 | 그 낱말이 있는 줄 |
   | 디렉토리 | `module` | 디렉토리 경로 (`codegraph`, `scripts/term`) | 비움 |
   `module` 필드는 항상 **디렉토리**다. `means` 는 한 문장, `does` 는 무엇을 하는지 한두 문장 — 둘 다 객체지향을 갓 배운 1학년 눈높이.
   `uses[]` 는 이 레코드가 **부르거나 · import 하거나 · 쓰는** 대상. `kind` 는 `dependency`(호출·import·쓰기) / `inheritance`(상속) / `aggregation`(멤버로 보유) 중 하나, `label` 에 `calls` `imports` `writes` 등 이유, `where` 는 그 자리.
   **`neighbors` 는 쓰지 않는다** — 기계가 다시 센다.
3. **코드에 없는 것은 쓰지 않는다.** Plan 이 만든 결정 코드(`C-20`, `U3`)나 개념(`무효화`)이 코드에 글자로 없으면
   그것은 Mode 1 의 것이 아니다 — Mode 1.5 의 `newConcepts` 로 남긴다. 인용 없는 뜻은 싣지 않는다.
4. **검사한다.** 실패 0 이 될 때까지 `where` 를 고친다. 근거 없음은 남겨도 되지만 이유를 보고한다.
   ```bash
   .venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json
   # -> out/codegraph-raw/terms-db.json + codegraph.json.  마지막 줄 "실패 0" 이어야 한다
   ```
5. **보고한다.** 레코드 수(종류별) · 실패 0 확인 출력 · 근거 없음 목록과 이유 · 키 충돌로 `<파일줄기>.<이름>` 이 된 것 목록.
````

- [ ] **Step 4: `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` 를 같이 고친다**

`### 이 mode 에 새로 붙는 것` 절을 이렇게 교체:
```markdown
### 이 mode 에 새로 붙는 것
**`terms_db.py` 와 전수조사 절차.** 2026-08-29 부터 `terms-db.json` 이 **원본**이고 `codegraph.json` 은 그 **투영**이다
(계획서 `2026-08-29-mode-1-terms-db-first.md`). 정적 수집기가 있으면 codegraph 에서 레코드를 먼저 만들고 LLM 이
뜻 · 동작 · 새 관계를 보탠다(구조 필드는 codegraph 가 이긴다). 없으면(Python/JS) LLM 읽기 레코드만으로 DB 를 만들고
`codegraph.json` 을 투영한다. **LLM 이 쓴 모든 `where` 는 L1/L2/L3 로 기계 검사한다.** 절차는 에이전트 정의
`.claude/agents/mode-1-codebase-wiki.md` 의 `## 전수조사 절차` 절에 있다.
```
`### 나는 무엇이 아닌가` 의 셋째 항목을 Step 1 과 **같은 문장**으로 교체.
`## 변경 이력` 에 한 줄 추가: `- 2026-08-29 — Mode 1 절: terms-db 우선 구조 반영. "means 를 풍부하게 쓰지 않는다" 를 "인용 없이 쓰지 않는다" 로 개정.`

- [ ] **Step 5: 두 문서가 같은 말을 하는지 확인**

Run: `grep -c "인용 없이 쓰지 않는다" .claude/agents/mode-1-codebase-wiki.md docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md`
Expected: 두 파일 다 `1` 이상

- [ ] **Step 6: 커밋 — 오케스트레이터가 사용자 승인 후. `.claude/agents/` 는 아직 미추적이라 이 커밋이 첫 추적이다 (RESUME R2 와 합친다)**

```bash
git add .claude/agents/mode-1-codebase-wiki.md docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md
git commit -m "[docs] : Mode 1 전수조사 절차와 terms-db 우선 규율을 에이전트 정의와 역할 문서에"
```

---

## Task 7: 전수조사 실행 — report-builder 자신 (LLM 단계, `mode-1-codebase-wiki` 가 한다)

이 Task 의 산출물은 코드가 아니라 **데이터**다. 결정론이 없으므로 TDD 대신 **인수 조건**으로 붙든다.

**Files:**
- Create: `docs/codegraph/terms-reading.json`
- Generate (gitignore): `out/codegraph-raw/terms-db.json` · `out/codegraph-raw/codegraph.json`

- [ ] **Step 1: 대상 파일 35개를 Task 6 §1 의 `find` 로 고정하고, 목록을 보고에 그대로 붙인다**

- [ ] **Step 2: Task 6 §2 규칙대로 레코드를 쓴다.** 예상 규모 — 파일 35 · 함수/클래스 104 · 산출물 약 12 · 키 약 10 · 개념 약 10 · 디렉토리 7 = **약 180개**. 반드시 들어가야 하는 키(Plan `llm-load-reduction` 이 쓰고 코드에 글자로 있는 것 — 🔵 실측):

| 키 | `kind` | 어디서 찾나 (시작점) |
|---|---|---|
| `codegraph.json` | `artifact` | `normalize.py` 의 `json.dump` 줄 |
| `roslyn-dump.json` | `artifact` | `normalize.py` C# 절 |
| `calls[]` `edges[]` `members[]` `nodes[]` `modules[]` | `key` | `normalize.py:285-287` 부근과 `verify_citations.py` |
| `PageRank` `hotspot` | `concept` | `facts.py` |
| `WarmUp` | `concept` | `grep -rn WarmUp codegraph scripts src` 로 2파일 |
| `normalize.py` `facts.py` `verify_citations.py` `terms_db.py` `collect.mjs` `quiz.mjs` `emit.mjs` | `file` | 각 파일 1줄 |
| `build_terms` `project_codegraph` `check_terms` `merge_terms` `pickTerms` `findNewConcepts` `gradeOne` `resolveScript` `runDispatch` | `function` | 선언 줄 |

- [ ] **Step 3: 검사가 실패 0 이 될 때까지 고친다**

Run: `.venv/bin/python codegraph/terms_db.py --repo . --reading docs/codegraph/terms-reading.json`
Expected: 마지막 줄 `... — 용어 N개 / 실패 0 / 근거 없음 M` (M 은 보고에 목록과 이유를 붙인다) 그리고 `out/codegraph-raw/codegraph.json — 노드 …` 한 줄. 종료 코드 0.

- [ ] **Step 4: Mode 1.5 와 이어지는지 — 이 계획의 목적**

Run: `mkdir -p /tmp/rb-t7 && cd /tmp/rb-t7 && report-term collect $REPO_ROOT/docs/superpowers/plans/2026-08-28-llm-load-reduction.md $REPO_ROOT/out/codegraph-raw/terms-db.json && python3 -c "import json;d=json.load(open('term-candidates.json'));print(len(d['known']),sorted(d['known']));print(len(d['newConcepts']))"`
Expected: `known` 이 **8개 이상**이고 `codegraph.json` `roslyn-dump.json` `calls[]` `edges[]` `PageRank` `hotspot` `WarmUp` `members[]` 를 포함한다. `newConcepts` 는 34 미만으로 준다(`codegraph.json` `calls[]` 등이 known 으로 옮겨가므로).
`known` 에 `main` `check` 같은 낱말이 섞이면 그것은 R6(낱말 오탐)이지 이 Task 의 실패가 아니다 — 목록만 보고한다.

- [ ] **Step 5: 위키 인용 검증기가 투영을 읽는지 — 기존 도구와의 접점 한 번**

Run: `.venv/bin/python codegraph/verify_citations.py docs/superpowers/plans/2026-08-28-llm-load-reduction.md --repo . --codegraph out/codegraph-raw/codegraph.json | tail -3`
Expected: 오류 없이 3값 집계가 나온다 (숫자는 보고에 붙인다. 기대값 없음 — 첫 관측이다)

- [ ] **Step 6: 커밋 — 오케스트레이터가 사용자 승인 후. 원본만 추적한다**

```bash
git add docs/codegraph/terms-reading.json
git commit -m "[feat] : report-builder 자신의 전수조사 원본 terms-reading.json"
```

---

========================================================================
[SELF-REVIEW — 보고 전에 확인]
- [ ] 두 문서가 같은 문장을 갖는가: grep -c "인용 없이 쓰지 않는다" 가 두 파일 다 1 이상
- [ ] terms_db.py 검사 마지막 줄이 "실패 0" 인가. exit 0 인가
- [ ] must-have 키(codegraph.json roslyn-dump.json calls[] edges[] members[] PageRank hotspot WarmUp + 파일 7 + 함수 9)가 전부 사전에 있는가
- [ ] collect 의 known 이 8개 이상이고 위 8개 산출물·키·개념을 포함하는가
- [ ] git status --porcelain 에 소유 파일 밖의 변경이 없는가 (out/ 은 무시되므로 안 보인다)
- [ ] "검증됨" "입증" "증명" 이 terms-reading.json 과 두 문서에 없는가
- [ ] 커밋하지 않았는가

[REPORT — 이 형식으로, 한국어]
상태: DONE | DONE_WITH_CONCERNS | BLOCKED
변경 파일: (경로 나열)
레코드 수: 종류별 (file / function / class / artifact / key / concept / module) 과 합계
검사 출력: terms_db.py 마지막 2줄 · 근거 없음 목록 전체와 각각의 이유
키 충돌 목록: <파일줄기>.<이름> 이 된 것 전부
collect 결과: known 개수와 목록 · newConcepts 개수
verify_citations 출력: 마지막 3줄
계획서와 달리 한 것: (있으면 무엇을 왜. 없으면 "없음")
미룬 것 / 우려: (없으면 "없음")
커밋: 하지 않았다 (확인)
```
