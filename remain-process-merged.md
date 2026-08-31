# 남은 작업 — 안 된 것과 불확실한 것만

> 수행이 끝난 항목은 이 문서에 남기지 않는다. 여기 있는 것은 **아직 안 했거나, 확인만 했고
> 안 고쳤거나, 사용자 결정을 기다리는 것**이다. 마지막 정리 2026-08-31.

---

## 🏗️ 1. 심볼 파악 파이프라인 — Plan Task 미완

`docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md` 기준.

- [ ] **Task 1:** `survey_plan.py` 가 `depends_on` 을 id 가 아니라 **이름**으로 내도록 수정.
      🔵 아직 id 다 — `machine/survey_plan.py` 의 `layers[].batches[].symbols[].depends_on` 이
      `edges` 의 목적지 **심볼 id** 를 그대로 담는다.
- [ ] **Task 2:** `dep_excerpt` 회귀 시험 추가 (id ≠ name 픽스처).
      `dep_excerpt` 는 `runner/run_mode1.py` 에 있고 시험은 `runner/test_run_mode1.py` 에 있다.
- [ ] **Task 3:** `resolve_target()` 조상 rollup 사다리 구현.
- [ ] **Task 4:** `synthesize_record()` 외부 심볼 · 파일 합성.
- [ ] **Task 5:** `resolve_uses()` 배선 — 못 푼 것은 실패가 아니라 "근거 없음" 으로 격하.
- [ ] **Task 6:** 배치 프롬프트에 `external` 탈출구 안내.
- [ ] **Task 7:** 실측 레코드 골든 대조.
- [ ] **Task 8:** 재실행 및 실측 갱신 — ⚠️ **과금 발생.**
- [ ] **성능 병목 후속** (Task 1 이 끝난 뒤에만 의미 있다)
  - `depends_on` 과 `uses.to` 를 이름으로 통일한 뒤, 층 장벽을 유지할지 **측정으로** 정한다.
  - 세션 고정비(82%) 절감을 위한 배치 크기(K3) 재검토 — 재측정 후.

---

## 🧪 2. Mode 1.5 · Mode 2 실행 — 사람 칸에서 멈춰 있다

- [ ] **Mode 1.5 잔여 단계.** `out/mode1_5/symbol-resolution/` 에 `questions.json` 과
      `term-candidates.json` 은 있고 **`answers.json` 이 없다.** 문답이 안 끝났다.
  - 문답 진행 → `answers.json`
  - `report-term grade` → `term-grades.json`
  - `report-term emit` → `terms.json` · `term-study-note.md`
- [ ] **Mode 2 연계.** 대응 설계 문서가 **없다** — 🔵 `docs/superpowers/specs/` 에
      `*-symbol-resolution-survey-design.md` 가 없다. 먼저 써야 `report-spec init` 이 잡는다.
  - `report-spec init` → `build` → `check` 완주
  - `terms.json` 을 `data.ts` 로 **손으로** 옮겨 적기(자동 병합하지 않는 것이 의도다).
    `data.ts` 결정 표와 `report.tsx` 서사 구성.

---

## 🤔 3. 사용자 판단 대기

- [ ] **Mode 1.5 `questions.json` 처리 방향.** 오케스트레이터가 만든 수동 사본을 그대로 두고
      문답을 이어갈지, 폐기하고 `term-benchmark` 스킬 4단계부터 다시 돌릴지.
- [ ] **홈 스킬 사본을 심볼릭 링크로 바꿀지.** 🔵 `<repo>/.claude/skills/` 는 `../../.agents/skills/`
      로 가는 링크지만 `~/.claude/skills/` 는 **여전히 독립 디렉토리**다. 내용만 맞춰 놨을 뿐이라
      다시 표류한다.
- [ ] **A-4 / A-5 착수 승인.** 중복 스키마 5곳 접기(A-4), 심볼 해석 플랜 실행(A-5).
- [ ] **`check_terms` 잔여 실패 83건.** LLM 오류가 아니라 수집기(`griffe` · `pycalls`) 공백에서
      온 것이다. 지우면 증거가 사라지므로 보존 중.
- [ ] **`pickTerms` 키 매칭 오탐.** FQN 매칭을 넣으면 `get` · `git` · `main` 같은 짧은 이름이
      마구 걸린다. 구조 결정이 필요해 보류.

---

## 🐞 4. 확인은 됐고 **안 고친** 결함 셋

셋 다 2026-08-31 에 실측으로 재현·확인만 했다. **고치지 않았다.**

- [ ] **`findNewConcepts` 오탐.** `runner/term/collect.mjs` 의
      `/\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b/g` 가 `C10` · `C11` 같은 **단순 인용 id** 를 신규 개념으로
      분류한다. `D\d` 만 예외라 `C` · `K` · `B` 계열은 그대로 걸린다.
      ⚠ **쌍이 이제 언어가 다르다** — 같은 세 꼴을 `viz/check.py` 의 `undefinedTerms`
      (`TERM_PATTERNS`) 도 쓴다. 한쪽만 고치면 조용히 어긋난다. **둘 다 고쳐야 한다.**

- [ ] **Mode 1 층3 토큰 폭증 — 원인 미상.**
      근거 `evals/runs/2026-08-30-mode1-qtvisionedit-cold-sonnet.json` 층별 합산:

      | 층 | 배치 | 토큰 | 초 합 | 비용 |
      |---|---:|---:|---:|---:|
      | L0 | 11 | 7,422,631 | 1177.7 | $5.1823 |
      | L1 | 1 | 902,177 | 136.3 | $0.5983 |
      | L2 | 1 | 783,411 | 103.7 | $0.5118 |
      | **L3** | **1** | **2,054,598** | **200.3** | **$1.0518** |
      | L4 | 1 | 784,959 | 88.6 | $0.4593 |
      | **L5** | **1** | **2,894,398** | **313.7** | **$1.4201** |

      L3 은 배치 하나인데 이웃 층(L2 783K · L4 785K)의 **약 2.6배**를 썼다.
      다음에 볼 것 — 그 배치의 심볼 목록과 통독 파일 크기.

- [ ] **Mode 1 층5 병렬화 병목.** L5(비노드 용어, K5)는 **배치가 하나뿐**이라 층 안 병렬(K2 · K4)이
      걸리지 않는다. 그런데 토큰은 전 층 최대(2,894,398)이고 벽시계도 단일 배치 최장(313.7초)이다.
      💭 K5 가 "맨 마지막 별도 층" 만 정하고 **쪼개지 않아서** 생긴 구조적 병목으로 보인다 —
      판단이지 사실이 아니다.

---

## ⚠ 5. Node → Python 포팅이 남긴 것

게이트는 전부 초록이지만 아래 셋은 **안 됐다.**

- [ ] **시험 커버리지 48건 소실.** 포팅이 옮기지 않은 시험이다. 그물이 성글어졌다.

      | 시험 | 옛 | 새 | 잃은 것 |
      |---|---:|---:|---|
      | components | 29 | 2 | **-27** — 17개 컴포넌트의 마크업 계약 |
      | wiki | 32 | 8 | **-24** |
      | graph-math | 8 | 6 | -2 |
      | (그 외 9종) | 97 | 102 | 되찾음 · 늘어남 |
      | **합계** | **166** | **118** | **-48** |

      `components` 는 `.tmp/lib.mjs` 를 node 자식 프로세스로 렌더해 확인하는 꼴이 이미 있어
      되살릴 수 있다. **되살릴지, 어느 것부터 할지는 사용자 결정이다.**

- [ ] **`runner/term/*.mjs` 셋이 아직 JS 다.** `collect.mjs` · `quiz.mjs` · `emit.mjs`.
      `runner/dispatch.py` 가 확장자를 보고 node 로 띄우는 갈림이 **이것 때문에** 필요하다.
      옮기면 그 갈림도 지울 수 있다.

- [ ] **`DOC_DIRS` 중복이 남을 이유가 사라졌다.** `viz/init.py` 와 `runner/run_mode2.py` 두 곳에
      사는 근거는 **"언어가 달라 한 곳에 못 모은다"** 였는데 이제 둘 다 파이썬이다.
      합칠 수 있게 됐지만 합치지 않았다 — 구조 변경이라 사용자 결정 대상이다.
      문서(`viz/CLAUDE.md`)에는 사실만 고쳐 적어 뒀다.

---

## 📄 6. 문서 현행화 잔여

- [ ] **`~/.claude/skills/term-benchmark/SKILL.md` 가 없어진 `author` 단계를 설명한다.**
      🔵 두 곳 — 54줄 "단계는 `collect → author → grade → emit` 넷이고", 235줄
      "`run_mode1_5.py` 가 `author` 단계에서 모형을 부르는 것은…".
      실제 단계는 `collect → [사람] → grade → emit` 셋이다(2026-08-31 `927684f` 에서 제거).
      머리말의 두 층 설명과 Common pitfalls 의 층 구분 3줄도 함께 봐야 한다.
      ⚠ 위 §3 의 "심볼릭 링크로 바꿀지" 와 얽힌다 — 홈 사본을 고쳐도 저장소 원본과 다시 갈린다.
