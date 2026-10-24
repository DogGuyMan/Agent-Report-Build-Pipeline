# Mode 1 / Mode 1.5+2 두 저장소 분리 — 실행 계획 (rev.4 · 2026-10-24)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **실행 세션은 먼저 묻는다** — 본체 `.py` 편집을 사용자가 diff 로 직접 승인하는 규칙(메모리 `python-edit-approval-rule`)을 이번에도 유지하는가. 유지하면 자동 모드를 켜지 않는다.

**Goal:** 한 저장소의 세 mode 를 **두 git 저장소**로 가른다. Mode 1(코드베이스 위키 · 정적 분석)은 사람이 부를 때만 돌고, 검사를 통과한 산출물을 대상 저장소에 **봉인**해 둔다. Mode 1.5(용어 점검)는 그 봉인이 없으면 돌지 않는다. Mode 2(설계 검토 보고서)는 Mode 1 과 독립으로 돌고, 봉인이 있으면 그것을 근거로 쓴다. 그 전에 프롬프트와 파일 템플릿을 코드에서 리소스 파일로 뺀다.

**Architecture:** 경계는 **데이터 계약(A3)** 이다. 스키마 리소스 `contracts/mode1-artifacts.v1.json` 을 두 저장소가 같은 사본으로 갖는다. Mode 1 은 `docs/codegraph/manifest.json` · `docs/codegraph/terms-db.json` 을 git 추적 자리에 낸다(봉인). report-builder 는 계약에서 **생성한** 형으로 봉인을 읽어 꼴과 신선도를 판정한다. 두 저장소는 코드 import · 자식 프로세스 · 시험 어느 층에서도 서로를 부르지 않는다. 공통 커널(`runner/pipeline.py` · `measure.py` · `dispatch.py` · `tools/*`)은 양쪽에 복제한다. 리소스 분리(Phase R)와 계약(Phase K)은 분리 전에 단일 저장소에서 끝낸다.

**Tech Stack:** Python 3.12+ · msgspec 0.21.1(JSON · TOML 디코드, JSON Schema 생성) · pytest · `git filter-repo`(🔵 `/opt/homebrew/bin/git-filter-repo`) · `gh`(🔵 DogGuyMan 로그인) · Node 22+ (Mode 2: esbuild · React · tsc / Mode 1: VitePress · mmdc)

표기 — 🔵 이번 세션에서 읽은 `파일:줄` 또는 돌린 명령의 출력 · 🟡 추론 · 💭 주관.

---

## 0. 결정

### 0.1 설계 원칙 (2026-10-24 사용자)

| 축 | 결정 | 이 계획에서의 모양 |
|---|---|---|
| **최우선 — 리소스와 코드** | 단계별 프롬프트는 파일로, 파이썬은 로드만 | Phase R. 프롬프트는 **단계당 한 파일**(`runner/**/prompts/<단계>.md`, 안에서 `<!-- section: 이름 -->` 으로 절을 가른다), 파일 템플릿은 `**/templates/*`, 설정값은 `config/*.toml`. 자리표시는 `{{이름}}` 하나 |
| 결합 | 양방향 0 · 느슨하게 | 두 저장소 사이에 코드 · 도구 의존 0. 선은 대상 저장소 안의 파일뿐 |
| 추상화를 통한 의존 | 경계 = A3 데이터 계약 | 두 저장소가 같은 계약 리소스에 의존한다. 소비자 형은 그 리소스에서 생성한다 |
| 확장에 열림 · 변경에 닫힘 | 기반은 닫고 확장은 파일로 | 새 LLM 단계 = 단계 클래스 + `.md` 하나. `PromptResource` · `tools/template.py` 는 고치지 않는다 |
| 책임 · 관심사 분리 | 한 파일 한 책임 | 봉인(`machine/manifest.py`) · 판정(`machine/evidence.py`) · 형 생성(`tools/gen_contract_types.py`) · 렌더(`tools/template.py`) · 리소스 자리(`PromptResource`) |
| 커널 | 양쪽 복제 | 표류는 자동 감시하지 않는다(결정 0011) |

### 0.2 사용 규칙 — 유스케이스 시험 결과 (2026-10-24 사용자)

| # | 시나리오 | 결정 | 계획의 자리 |
|---|---|---|---|
| U0 | 재질의 — Mode 사이의 실행 관계 | **Mode 1 은 사람이 부를 때만 돈다. 무엇도 대신 돌리지 않는다.** Mode 1.5 는 Mode 1 결과가 없으면 돌지 않고, 낡았으면 있는 JSON 으로 돈다. **Mode 2 와 Mode 1 은 독립이다** | §3.4 · K6 · K8 |
| U1 | 처음 보는 저장소에 첫 보고서 | Mode 2 는 봉인 없이 진행한다(U0 이 시나리오 1 의 "init 이 대신 돌려라" 를 대체) | K8 |
| U2 | 코드 수정 뒤 | Mode 2 는 진행한다(U0). **Mode 1 은 바뀐 파일을 다시 읽어야만 봉인한다** — 다시 읽지 않고 봉인만 고치는 길은 없다 | K2 |
| U2b | 위키 장 | 바뀐 파일을 인용하는 장만 다시 쓴다(Mode 1 의 새 동작) | K3 |
| U3 | 클라우드 세션 | 봉인과 `terms-db.json` 을 대상 저장소 git 에 커밋한다 — `docs/codegraph/` | K1 |
| U4 | 스킬 경유 | 에이전트는 Mode 1 을 돌리지 않는다. 용어 시험 스킬은 봉인이 없으면 멈추고 알린다 | K9 |
| U5 | 프롬프트 고침 | 단계당 한 파일, 절로 가른다 | R2 · R4 · R5 |
| U6 | 계약 변경 | 소비자 형을 계약 JSON 에서 생성한다 | K5 |
| U8 | Mode 1 만 쓸 때 | 봉인은 늘 `docs/codegraph/` 에 낸다 | K1 |
| U9 | 용어 시험 | 봉인 없으면 멈추고, 낡았으면 경고하고 진행 | K6 |
| U10 | 자기호스팅 | 예외 없이 같은 규칙. U0 으로 Mode 2 는 막히지 않는다 | — |
| U11 | Mode 1 진입 — 비용 · 전량 폴백 | **묻지 않는다.** `schedule-batches` 뒤 배치 수와 예상 비용 범위를 한 줄 찍는다. 지문이 없거나 언어를 몰라 **증분으로 불렸는데 전량**이 되면 그 사실을 굵게 찍고 돈다 | R7 · K2b |
| U12 | 사람이 고친 위키 장 | 덮어쓴다. 덮기 전 `docs/wiki/.bak/<장>.md` 로 남기고 보고에 적는다. 손댐은 `write-wiki` 가 적어 둔 장 해시와 다른 것으로 안다 | K3 |
| U13 | Mode 1 부분 성공 | 전부 아니면 전무 — HALT, 봉인 없음. 이전 봉인은 남되 `manifest.json` 에 "뒤 실행이 실패했다" 표식을 적어 Mode 1.5·2 가 경고를 본다 | K1 · K2 · K6 |
| U14 | Mode 2 진입 — 봉인 가시성 | `report-spec init` 이 `evidence.py --status` 로 **한 줄** 찍는다(있음 · 낡음 N건 · 없음 · 깨짐). 막지 않는다 — 스킬 경로에도 닿는다 | K6 · K7 · K7b |
| U15 | 봉인 커밋을 잊으면 | `evidence.py` 가 봉인 파일이 미커밋이면 "이 기계에만 보인다" 경고. Mode 2 프롬프트에도 한 줄 | K6 · K7 |
| U16 | 1.5 낡음 경고의 흔적 | `term-candidates.json` 에 `evidence: {manifest, stale, uncommitted}` 를 싣고, 낡은 파일에 `where` 가 걸린 용어에 `stale: true` 를 표시한다. 스킬이 그것을 피하거나 표시한다 | K6 · K8 |

**대체된 답 — 기록으로 남긴다.** 시나리오 1(init 이 대신 돌린다) · 7(y/N 한 번 묻는다) · 1↔4(터미널이면 돌린다)는 U0 이 "Mode 1 은 사람이 부를 때만" 으로 대체했다. 그래서 자동 실행 · 비용 어림 · `y/N` 은 계획에 없다. 첫 요청의 "1.5 & 2 는 반드시 Mode 1 실측 기반" 은 U0 으로 **1.5 는 필수, 2 는 있으면 근거로** 가 됐다. 시나리오 2 의 "막는다" 는 Mode 2 에서는 U0 이 대체했고, Mode 1 의 봉인 규칙으로만 남았다.

**U2 를 어떻게 지키나.** 봉인 단계는 소스 파일마다의 지문을 **지난 전수조사의 지문**(`out/codegraph-raw/snapshot.json`, 🔵 `warmup.Entry.file_hash`)과 대조한다. 하나라도 다르면 `terms-db` 를 봉인하지 않는다. 위키는 `write-wiki` 가 그 지문을 따라잡았다는 표(`wiki-state.json`)가 있어야 봉인한다. 신선도는 커밋이 아니라 파일 지문이다 — 보고서 원고 커밋은 낡음이 아니다.

### 0.3 그대로 둔 기본값 — 다르면 알려 달라

| # | 기본값 | 바뀌는 곳 |
|---|---|---|
| Q1 | "별개의 Skill" = 별개 프로젝트. 스킬은 각 저장소의 `.claude/skills/` · `.agents/skills/` 에 둔다 | B9 · C5 |
| Q2 | 새 저장소 `codebase-wiki` · `$TOOLS_ROOT/codebase-wiki` · GitHub `DogGuyMan/codebase-wiki` **private** | B1 · B2 |
| Q3 | Mode 1 은 `filter-repo` 로 경로 이력 보존, report-builder 는 삭제 커밋. 가르기 전에 이 브랜치를 `main` 에 fast-forward | M2 · B1 |
| Q6 | 문서는 주제별 라우팅(§2.3) | B1 · C1 |
| Q7 | 벤더 스킬 14개와 `skills-lock.json` 은 report-builder 에만 | B9 · C1 |
| Q8 | 재굽기(LLM 과금)는 Phase E. 실행 시점은 사용자가 정한다 | Phase E |
| Q9 | `# <include file="machine/comments.xml" …/>` 잔재는 그대로 둔다 | — |
| Q10 | `terms-db.json` 은 그대로 커밋한다. 🔵 디스크 1.38 MB · git blob(zlib) 237 KB · 칸을 `kind means does where module` 로 줄인 slim 투영도 176 KB 라 이득이 작다. 실행마다 한 판이 쌓인다 | K1 |

### 0.4 이 규칙이 부르는 것

- **Phase K 이후 `report-term collect` 는 봉인 없는 저장소에서 멈춘다.** 이 저장소 자신도 Phase E 전까지 멈춘다 — 위키가 이미 낡았고(🔵 루트 CLAUDE.md "빨강 하나" L2 43건) Phase R 이 프롬프트를 옮기며 줄을 민다.
- **Mode 2 는 언제나 돈다.** 봉인이 없으면 에이전트 프롬프트에 근거 자리가 없을 뿐이다.
- **Mode 1 을 사람이 다시 돌리면 `docs/codegraph/` 가 바뀐다.** 커밋은 사람이 한다. 잊으면 `evidence.py` 가 "이 기계에만 보인다" 고 경고한다.
- **Mode 1 은 묻지 않는다.** 예상 비용을 찍지만 멈추지 않는다 — 멈추는 것은 Ctrl-C 다.
- **위키 장을 손으로 고치면 다음 증분이 덮는다.** 덮기 전 `docs/wiki/.bak/` 에 남으니 거기서 되살린다.
- **실패한 Mode 1 실행은 봉인하지 않는다.** 이전 봉인이 남고 그 위에 "뒤 실행 실패" 표식이 붙는다 — 1.5·2 는 경고를 보고 옛 자료로 돈다.

---

## 1. 실측 (🔵 2026-10-22~24)

### 1.1 두 mode 사이의 결합 — 일곱 곳

| 부르는 쪽 | 불리는 쪽 | 줄 | Task |
|---|---|---|---|
| `runner/test_run_mode1_5.py` | `run_mode1` (import) | `:23` | A2 |
| `runner/test_run_mode2.py` | `run_mode1` (import) | `:20` | A2 |
| `runner/test_run_mode1.py` | `run_mode1_5` · `run_mode2` (import) | `:703-704` | A3 |
| `tools/gen_readme.py` | `machine/pycalls.signature_of` (import) | `:21-22` | C2 |
| `runner/wiki/build.py` | `viz/demermaid.py` (자식 프로세스) | `:76` | 둘 다 Mode 1 몫이라 함께 간다 |
| `runner/wiki/prep.py` | `viz/render_modules.py` (자식 프로세스) | `:210` | 같음 |
| `viz/build.py` | 자리 문자열 `out/codegraph-raw` | `:101` | 링크 뿌리로만 남는다(§3.1) |

### 1.2 코드 안의 리소스 — 열여덟 곳

긴 글 상수 검사(독스트링 제외 · 줄바꿈 6개 이상 또는 200자 이상)를 `runner/` · `viz/` 에 돌린 결과다. 오탐 0건이었고, 이 검사가 R9 의 게이트가 된다.

| 자리 | 무엇 | 갈 곳 (파일 · 절) |
|---|---|---|
| `runner/mode1/lang.py:34` | `lang-hint` 프롬프트 | `runner/mode1/prompts/lang-hint.md` |
| `runner/mode1/survey.py:113` | 배치 프롬프트 | `…/prompts/annotate-symbols.md` · `batch` |
| `runner/mode1/survey.py:59` | 증분 범위 절 | 같은 파일 · `scope` |
| `runner/mode1/survey.py:191` | 미조사 의존 절 | 같은 파일 · `pending` |
| `runner/mode1/survey.py:407` | 재조사 절 | 같은 파일 · `retry` |
| `runner/mode1/survey.py:224` | 비노드 층 프롬프트 | 같은 파일 · `nonnode` |
| `runner/mode1/survey.py:478` | 2패스 프롬프트 | 같은 파일 · `pass2` |
| `runner/mode1/wiki.py:38` | 목차 프롬프트 | `…/prompts/outline-wiki.md` |
| `runner/mode1/wiki.py:128` | 장 프롬프트 | `…/prompts/write-wiki.md` |
| `runner/run_mode2.py:251` | Mode 2 에이전트 프롬프트 | `runner/prompts/agent.md` · `main` |
| `runner/run_mode2.py:240` | 용어집 절 | 같은 파일 · `terms` |
| `runner/run_mode1_5.py:515` | `--ask` 첫 프롬프트(한 줄 % 서식) | `runner/prompts/ask.md` |
| `runner/wiki/build.py:38` | VitePress 설정 | `runner/wiki/templates/vitepress.config.mts.tmpl` |
| `viz/render_classes.py:384` | 클래스 DOT 머리 | `viz/templates/dot/classes-head.dot.tmpl` |
| `viz/render_modules.py:207` | 모듈 DOT 머리 | `viz/templates/dot/modules-head.dot.tmpl` |
| `viz/render_modules.py:284` | 모듈 DOT 범례 | `viz/templates/dot/modules-legend.dot.tmpl` |
| `viz/build.py:48` (+ `:40` 진입 모듈) | 정적 렌더 스크립트 | `viz/templates/report/render.mjs.tmpl` · `entry.ts` |
| `viz/init.py:94` · `:106` | `data.ts` · `report.tsx` 뼈대 | `viz/templates/report/data.ts.tmpl` · `report.tsx.tmpl` |

**죽은 리소스 넷.** `runner/mode1/prompt/*.md` 는 아무도 로드하지 않는다(🔵 `grep` 0건). 내용도 파이썬 소스 발췌다. R4 가 지운다.

### 1.3 코드 안의 설정값

| 자리 | 값 | 갈 곳 |
|---|---|---|
| `runner/run_mode1.py:201` | `--model` 기본 `claude-sonnet-5-5` | `config/mode1.toml` `[models] sessions` |
| `runner/mode1/lang.py:16` | `LANG_SELECT_MODEL = "claude-haiku-4-5-20251001"` | `config/mode1.toml` `[models] lang_hint` |
| `runner/run_mode2.py:468` | `--model` 기본 `opus` | `config/report.toml` `[models] mode2_agent` |
| `runner/run_mode2.py:97` **와** `viz/init.py:11` | `DOC_DIRS` — 같은 규칙 두 곳 | `config/report.toml` `[[doc_dirs]]` 한 곳 |

`runner/term/quiz.py:12-13` 의 `QUESTIONS_PER_TERM = 3` · `CHOICES_PER_QUESTION = 5` 는 코드에 남긴다 — 채점 구간이 전제하는 불변식이다. 💭

### 1.4 실측 비용 — Mode 1 을 사람이 부를 때 기다리는 것

| 실행 | 벽시계 | 비용 | 근거 |
|---|---:|---:|---|
| QtVisionEdit 냉시동, 전수조사만(sonnet) | 18분 | $9.22 | 🔵 `evals/runs/2026-08-30-mode1-qtvisionedit-cold-sonnet.json` |
| 이 저장소 증분 한 번(sonnet) | 9분 | $31.35 | 🔵 `evals/runs/2026-09-17-mode1-report-builder-warm-sonnet.json` |
| 이 저장소 냉시동 전량(sonnet) | 35분 | $57.15 | 🔵 `evals/runs/2026-09-19-mode1-report-builder-cold-file-sonnet.json` |

### 1.5 전수조사 레코드와 위키

`machine/terms-reading.json` 1,318 레코드 — `where` 접두사로 가른다(A4). `docs/wiki/` 21쪽 — Mode 2 주제 6 · Mode 1 주제 11 · 공통 4. `terms-db.json` 의 실제 형은 🔵 `machine/terms_db.py:60-88` 의 `DbUse` · `TermRecord` 다. 계약 스키마는 이 형에서 생성한다(K4).

---

## 2. 분리 뒤의 모양

### 2.1 `codebase-wiki`

```
codebase-wiki/
  bin/report-wiki
  config/mode1.toml
  contracts/mode1-artifacts.v1.json · .sha256    계약 (정본은 이쪽, 형에서 생성)
  runner/   dispatch · measure · pipeline(+PromptResource) · run_mode1 · check_shard · runner_presudo.md
            mode1/**  (+ prompts/{lang-hint,annotate-symbols,outline-wiki,write-wiki}.md · seal.py)
            wiki/**   (+ templates/vitepress.config.mts.tmpl)
            test_measure · test_mode1 · test_pipeline · test_run_mode1
  machine/  전부 (+ manifest.py · test_manifest.py)
  viz/      render_classes · render_modules · demermaid · templates/dot/*.tmpl
  tools/    gen_contract_types 를 뺀 전부 (+ template.py · gen_contract.py)
  test/     test_docs_citations · test_no_any · test_dispatch · test_portability · test_wiki · test_prompt_resources
  evals/**  resources/**  docs/{decisions,overturn,wiki,diagrams,prompt,codegraph,CLAUDE.md,contract-mode1-artifacts.md, 라우팅 문서}
  .claude/{CLAUDE.md, settings.json, agents/mode-1-codebase-wiki.md, skills/codebase-terms-survey}
  .agents/skills/codebase-terms-survey/  .gemini/PythonRule.md  .github/**
```

### 2.2 `report-builder`

```
report-builder/
  bin/report · report-spec · report-term
  config/report.toml
  contracts/mode1-artifacts.v1.json · .sha256    계약 사본 (codebase-wiki 에서 복사만 한다)
  runner/   dispatch · measure · pipeline(+PromptResource) · run_mode1_5 · run_mode2 · run_grade · term/**
            prompts/{agent,ask}.md
            test_measure · test_pipeline · test_run_mode1_5 · test_run_mode2 · test_run_grade
  machine/  evidence.py · contract_types.py(생성물) · test_evidence.py · CLAUDE.md · README.md
  viz/      init · build · check · wrap_terms · link_paths · svg.mjs · svg.d.mts · lib.mjs · src/** · templates/report/*
  tools/    gen_contract 를 뺀 전부 (+ template.py · gen_contract_types.py)
  test/     test_docs_citations · test_no_any · test_dispatch · test_portability · test_prompt_resources · test_config
            test_check · test_components · test_graph_math · test_init · test_link_paths · test_term · test_wrap_terms · svg.test.mjs
  docs/codegraph/{terms-reading.json, terms-db.json, manifest.json}   이 저장소를 대상으로 한 Mode 1 산출물 (봉인은 Phase E 뒤)
  docs/{decisions,overturn,wiki,diagrams,prompt,CLAUDE.md,contract-mode1-artifacts.md, 남는 문서, my.self, ai-readiness-*}
  .claude/{CLAUDE.md, settings*.json, agents/mode-1-5-*.md · mode-2-*.md, skills/{spec-review-dashboard,term-benchmark,벤더 13}}
  .agents/{rules, skills/벤더 14}  .gemini/**  .github/**  skills-lock.json
```

### 2.3 문서 라우팅 (Q6)

**codebase-wiki 로 가는 것** — B1 의 경로 목록에 들어가고 C1 이 여기서 지운다.

| 묶음 | 파일 |
|---|---|
| `docs/handoffs/` | `DECISION-cpp-symbol-index.md` · `DECISION-csharp-intermediate-format.md` · `HANDOFF-2026-08-29-cpp-clang-doc-vs-clang-uml.md` · `HANDOFF-2026-08-29-griffe-python-prototype.md` · `HANDOFF-2026-08-29-mode-1-resurvey.md` · `HANDOFF-2026-08-29-mode-1-terms-db-tasks-1-5.md` · `HANDOFF-2026-08-29-mode-1-terms-db-tasks-6-7.md` · `HANDOFF-2026-08-29-mode-1-xmldoc-relocate.md` · `HANDOFF-2026-08-29-warmup-incremental-cache.md` · `HANDOFF-2026-09-07-codegraph-id-namespace.md` · `HANDOFF-2026-09-07-warmup-increment-unreachable.md` · `HANDOFF-2026-09-08-xmldoc-deprecation-marker.md` · `HANDOFF-clangd-reverse-refs.md` · `HANDOFF-codebase-wiki.md` · `HANDOFF-cpp-boundary-rules.md` · `HANDOFF-cpp-pattern-collection.md` · `HANDOFF-cpp-symbol-index-selection.md` · `HANDOFF-unity-boundary-rules.md` · `HANDOFF-unity-pattern-collection.md` · `HANDOFF-unity-roslyn-dump-v2.md` · `PROMPT-2026-08-30-bottomup-survey-harness.md` · `RESUME-2026-08-28-track-c.md` · `RESUME-2026-08-30-python-strict-and-collector.md` · `RESUME-2026-09-08-runner-stage-machine.md` · `RESUME-2026-09-11-runner-stage-machine.md` · `cpp-index-friendly-conventions.md` |
| `docs/superpowers/plans/` | `2026-08-28-llm-load-reduction.md` · `2026-08-29-mode-1-terms-db-first.md` · `2026-08-29-mode-1-wiki-entrypoint.md` · `2026-08-30-bottomup-survey-harness.md` · `2026-08-30-griffe-python-collector.md` · `2026-08-30-symbol-resolution-survey.md` + `symbol-resolution-survey/` · `2026-08-30-warmup-mode1-wiring.md` · `2026-09-11-runner-mode1-v2.md` · `2026-09-11-runner-mode1-요약.md` · `2026-09-11-runner-mode1.md` · `2026-09-20-bottomup-leaf-reuse.md` + `bottomup-leaf-reuse/` |
| `docs/superpowers/specs/` | `2026-08-30-griffe-python-collector-design.md` + `griffe-python-collector/` · `2026-09-08-runner-stage-machine-design.md` + `runner-stage-machine/` · 링크 `2026-08-28-llm-load-reduction-design.md` + `llm-load-reduction/` · 링크 `2026-08-29-mode-1-terms-db-first-design.md` + `mode-1-terms-db-first/` |
| `docs/` 직속 | `2026-09-19-mode1-역대-실측과-패치-이력.md` · `2패스개선.md` · `analysis-2026-08-31-cpp-collectors.md` · `코드베이스 분석 보고서 파이프라인.png` · `코드베이스_분석_보고서_파이프라인.pdf` |
| 전체 | `evals/**` · `resources/**` |

**양쪽에 두는 것** — `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md` · `docs/superpowers/plans/2026-09-08-runner-common-axis.md` · `2026-09-08-runner-pipeline.md` · `2026-09-13-runner-msgspec.md` · 이 계획서 · `docs/{decisions,overturn,diagrams,prompt}/**` · `docs/CLAUDE.md` · `docs/contract-mode1-artifacts.md` · `contracts/**`.

**report-builder 에 남는 것** — 위에 없는 전부. 주제를 모르는 둘(`compass_artifact_…md` · `plans/2026-08-31-plan-citation-precheck.md` + 폴더)도 남긴다. 🟡

---

## 3. 계약 A3

### 3.1 파일 (자리는 전부 대상 저장소 기준)

| 자리 | 쓰는 것 (codebase-wiki) | 읽는 것 (report-builder) |
|---|---|---|
| `docs/codegraph/manifest.json` (git 추적) | `machine/manifest.py` (단계 `seal-artifacts`) | `machine/evidence.py` — 모든 판정의 출발점 |
| `docs/codegraph/terms-db.json` (git 추적) | 봉인이 `out/codegraph-raw/terms-db.json` 을 복사해 낸다 | `runner/term/collect.py` · `term-benchmark` 스킬 |
| `docs/wiki/*.md` (git 추적) | `write-wiki` 단계 | Mode 2 에이전트 프롬프트의 근거 자리(있을 때만) |
| `out/codegraph-raw/**` (git 밖) | Mode 1 의 작업 파일 | `viz/build.py` · `link_paths.py` 의 링크 뿌리로만. 봉인 대상이 아니다 |

`out/` 은 Mode 1 의 작업대이고 `docs/codegraph/` 는 **내보낸 실측**이다. 읽는 쪽은 `docs/codegraph/` 만 본다.

### 3.2 계약 리소스

```json
{ "contract": "mode1-artifacts", "version": 1,
  "types":   { "terms-db.json": "TermsDb", "manifest.json": "ArtifactManifest" },
  "schemas": { "terms-db.json": <JSON Schema>, "manifest.json": <JSON Schema> } }
```

- **codebase-wiki 가 형에서 생성한다** — `tools/gen_contract.py` 가 `terms_db.TermsDb` · `manifest.ArtifactManifest` 에서 `msgspec.json.schema` 로 뽑는다. `title` · `description` 은 뗀다. `$defs` 열쇠는 클래스 이름이다.
- **report-builder 는 복사만 하고 형을 생성한다** — `tools/gen_contract_types.py` 가 이 파일에서 `machine/contract_types.py` 를 낸다(U6). 생성된 형의 스키마가 계약과 같은지 시험이 왕복으로 본다. 새 의존성은 없다.
- 지문 파일 `mode1-artifacts.v1.sha256`(`shasum -a 256 -c` 꼴)을 같이 둔다.
- **판 올림** — 열쇠를 빼거나 뜻을 바꾸면 `v2` 파일. 더하는 것은 같은 판이다(msgspec 은 모르는 열쇠를 버린다 🔵 탐침).

### 3.3 봉인 규칙 (codebase-wiki) — U2 · U2b · U3 · U8

- `seal-artifacts` 는 Mode 1 그래프의 마지막 단계다. **그 실행에서 검사기를 통과한 것만** 싣는다 — `verify-terms` → `terms-db`, `verify-wiki` → `wiki`.
- **`terms-db` 는 다시 읽은 소스에만 봉인한다.** 지금 소스 파일마다의 지문이 `out/codegraph-raw/snapshot.json`(지난 전수조사가 성공한 뒤 `snapshot-sources` 가 찍은 것)과 같아야 한다. 하나라도 다르거나 새 파일이면 거부한다. 해결은 Mode 1 증분 실행 하나다(바뀐 파일만 LLM 이 다시 읽는다).
- **`wiki` 는 `write-wiki` 가 그 지문을 따라잡았을 때만 봉인한다.** `write-wiki` 는 증분에서 바뀐 파일을 글자로 인용하는 장을 다시 쓰고, 끝나면 `out/codegraph-raw/wiki-state.json` 에 그때의 `snapshot.json` 해시를 적는다. 봉인은 그 해시가 지금 지문과 같을 때만 위키를 싣는다.
- 봉인은 `docs/codegraph/terms-db.json`(복사) · `docs/codegraph/manifest.json` 을 쓴다. `manifest.json` 의 `inputs` 는 소스 파일마다의 git blob id, `source_exts` · `skip_dirs` 는 그것을 모은 규칙이다 — 읽는 쪽이 Mode 1 을 몰라도 같은 규칙을 다시 돌린다.
- **진입 알림(U11).** `schedule-batches` 가 끝나면 `배치 N개 · 예상 $lo~hi · 증분|전량` 한 줄을 찍는다. 배치당 비용 범위는 `config/mode1.toml` 의 `[estimate]` 다. 증분으로 불렸는데 지문이 없거나 언어를 몰라 전량이 되면 `⚠ 증분으로 불렸지만 전량이다` 를 stderr 에 찍고 **그대로 돈다.** 묻지 않는다.
- **손댄 장(U12).** `write-wiki` 는 쓴 장마다 해시를 `wiki-state.json` 의 `pages` 에 적는다. 다음 증분에서 다시 쓸 장의 지금 해시가 그것과 다르면 사람이 고친 것이다 — `docs/wiki/.bak/<장>.md` 로 옮긴 뒤 다시 쓰고, 끝에 "손으로 고친 장 N개를 덮었다(.bak)" 목록을 찍는다. `.bak/` 은 VitePress 빌드와 봉인에서 제외한다.
- **실패한 실행(U13).** 어느 단계든 FAIL 로 HALT 하면 `run_mode1.py` 가 **이전 봉인**(`docs/codegraph/manifest.json`)이 있을 때 `superseded_by: {stage, at, producer_commit}` 를 적어 둔다. 봉인 자체는 새로 쓰지 않는다. 다음 성공 봉인이 이 칸을 없앤다.

### 3.4 판정 규칙 (report-builder) — U0 · U9 · U13 · U14 · U15 · U16

`machine/evidence.py <repo> --need terms-db[,wiki] [--list | --status]` 는 **구조 문제**가 있으면 찍고 exit 1, **낡음**은 경고로만 찍고 exit 0 이다. `--status` 는 어느 경우든 exit 0 이고 한 줄만 찍는다.

| 구조 문제 (exit 1) | 낡음 (경고 · exit 0) |
|---|---|
| `manifest.json` 없음 · 꼴 아님 · 계약 판 다름 | 봉인 뒤 소스가 바뀜 · 생김 · 사라짐 |
| 필요한 종류가 봉인에 없음 | 봉인 파일이 **커밋되지 않았다** — 이 기계에만 보인다 (U15) |
| 봉인된 파일이 없거나 해시가 다름 · 봉인 뒤 생긴 위키 장 | 이전 봉인에 `superseded_by` — 뒤 Mode 1 실행이 실패했다 (U13) |
| `terms-db.json` 이 계약 꼴이 아님 | |

`--status` 한 줄의 꼴 — `Mode 1 봉인 — 있음 · 낡음 3건 · 미커밋` / `Mode 1 봉인 — 없음` / `Mode 1 봉인 — 깨짐: terms-db.json 해시가 다르다`.

| 부르는 곳 | 모양 | exit 1 이면 | 낡음이면 |
|---|---|---|---|
| `report-term collect` (Mode 1.5) | `--need terms-db --list` | **멈춘다** | 경고하고 진행. `term-candidates.json` 에 `evidence` 와 용어별 `stale: true` 를 싣는다 (U16) |
| `runner/run_mode2.py` (Mode 2) | `--status` 한 줄 + `--need terms-db,wiki --list` | 상태 한 줄 찍고 근거 자리 없이 진행 | 근거 자리 + 낡은 파일 목록 + 미커밋 한 줄을 프롬프트에 싣고 진행 |
| `report-spec init` (Mode 2) | `--need terms-db,wiki --status` | 상태 한 줄 찍고 진행 (U14) | 같은 줄에 `낡음 N건` |

무엇도 Mode 1 을 대신 돌리지 않는다. 멈출 때 찍는 안내는 사람이 칠 명령 하나다.

---

## 4. Tasks

**순서** — R(리소스 분리) → A(경계 끊기) → K(계약 — 생산자와 소비자) → M(병합) → B(codebase-wiki 추출) → C(report-builder 줄이기) → E(재굽기). R · A · K 는 단일 저장소에서 돈다.

**커밋 메시지** — `personal-commit-messages` 규약. 아래 `git commit` 줄을 그대로 쓴다.

**작업 폴더** — 두 저장소 밖 `$TOOLS_ROOT/split-work/`. 커밋하지 않는다.

```bash
mkdir -p "$TOOLS_ROOT/split-work"
```

### Phase R — 리소스와 코드를 가른다 (최우선 · 단일 저장소)

> 동작은 바이트 단위로 같아야 한다. R3 이 옮기기 전의 글을 찍고 R8 이 옮긴 뒤와 `diff` 한다.

#### Task R1: `{{이름}}` 렌더러 — `tools/template.py`

**Files:**
- Create: `tools/template.py` · `tools/test_template.py`
- Modify: `test/test_no_any.py` (COVERED 에 한 줄)

자리표시를 `{{이름}}` 로 정한 이유 — 프롬프트와 템플릿에 JSON 중괄호와 `$REPO_ROOT` 가 흔하다. `str.format` 은 중괄호를, `string.Template` 은 `$` 를 이스케이프해야 한다. 🔵 지금 인라인 프롬프트가 `{{ }}` 이스케이프를 쓴다(`runner/run_mode2.py:245`).

- [ ] **Step 1: 실패하는 시험** — `tools/test_template.py`:

```python
import pytest

from tools.template import TemplateError, render, render_file


def test_자리를_값으로_바꾼다():
    assert render("대상 {{repo}} · 도구 {{ root }}", {"repo": "/a", "root": "/b"}) == "대상 /a · 도구 /b"


def test_값이_없는_자리는_예외다():
    with pytest.raises(TemplateError, match="repo"):
        render("{{repo}}", {})


def test_자리가_없는_값도_예외다():
    with pytest.raises(TemplateError, match="slug"):
        render("{{repo}}", {"repo": "/a", "slug": "x"})


def test_한겹_중괄호와_달러는_건드리지_않는다():
    text = '꼴은 {"키": 레코드} · { "용어": { TermMeans } } · $REPO_ROOT/bin · {{ "따옴표" }}'
    assert render(text, {}) == text


def test_값_안의_자리는_다시_펴지_않는다():
    assert render("{{a}}", {"a": "{{b}}"}) == "{{b}}"


def test_render_file_은_UTF8_파일을_읽어_채운다(tmp_path):
    p = tmp_path / "t.md"
    p.write_text("안녕 {{who}}\n", encoding="utf-8")
    assert render_file(str(p), {"who": "세계"}) == "안녕 세계\n"
```
Run: `.venv/bin/python -m pytest tools/test_template.py -q` → Expected: `ModuleNotFoundError: No module named 'tools.template'`.

- [ ] **Step 2: 구현** — `tools/template.py`:

```python
"""리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외다.

이름은 영문자 · 숫자 · 밑줄이다. 한 겹 중괄호와 `$` 는 글자 그대로 둔다 — 프롬프트와 템플릿에
JSON 과 환경변수 표기가 흔하다. 바꾼 값 안의 `{{…}}` 는 다시 펴지 않는다.
"""
import re
from collections.abc import Mapping

SLOT = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(ValueError):
    """템플릿의 자리와 넘긴 값이 맞지 않는다."""


def render(text: str, values: Mapping[str, str]) -> str:
    """`{{이름}}` 을 값으로 바꾼다. 값이 없는 자리 · 자리가 없는 값은 둘 다 `TemplateError`."""
    slots = set(SLOT.findall(text))
    missing = sorted(slots - set(values))
    unused = sorted(set(values) - slots)
    if missing or unused:
        raise TemplateError("값이 없는 자리 %s · 자리가 없는 값 %s" % (missing, unused))
    return SLOT.sub(lambda m: values[m.group(1)], text)


def render_file(path: str, values: Mapping[str, str]) -> str:
    """파일 하나를 UTF-8 로 읽어 `render` 한다."""
    with open(path, encoding="utf-8") as f:
        return render(f.read(), values)
```
`test/test_no_any.py` 의 `COVERED` 끝에 `"tools/template.py",`.

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest tools/test_template.py test/test_no_any.py -q && npm run typecheck:py
git add tools/template.py tools/test_template.py test/test_no_any.py
git commit -m "[update] : tools/template - 리소스 파일의 {{이름}} 자리를 채운다"
```

#### Task R2: 단계가 리소스를 읽는 자리 — `PromptResource` (단계당 한 파일 · 절)

**Files:**
- Modify: `runner/pipeline.py` (머리 import · `LlmStage` 위 믹스인 · `LlmStage` 기반)
- Test: `runner/test_pipeline.py` (끝에 다섯)

쓰는 쪽은 LLM 단계 전부와 대화형 `AskStage`(LLM 단계가 아니다 🔵 `runner/run_mode1_5.py:718`)라서 믹스인이다(메모리 `stage-owned-functions` — 둘 이상이 쓰면 믹스인). 이름 꼴은 `"<파일>"` 또는 `"<파일>#<절>"` 이다(U5).

- [ ] **Step 1: 실패하는 시험** — `runner/test_pipeline.py` 끝에(`import pytest` 가 없으면 머리에):

```python
def test_prompt_resource_는_절_없는_파일을_통째로_읽는다(tmp_path):
    (tmp_path / "hello.md").write_text("\n안녕 {{who}}\n\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("hello",)

    assert S.load_prompt("hello", who="세계") == "안녕 세계\n"


def test_prompt_resource_는_절을_이름으로_꺼낸다(tmp_path):
    (tmp_path / "s.md").write_text(
        "<!-- section: a -->\n가 {{x}}\n\n<!-- section: b -->\n나\n", encoding="utf-8")

    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ("s#a", "s#b")

    assert S.load_prompt("s#a", x="1") == "가 1\n"
    assert S.load_prompt("s#b") == "나\n"


def test_prompt_resource_는_선언_밖의_이름을_거부한다(tmp_path):
    class S(P.PromptResource):
        prompt_dir = str(tmp_path)
        prompt_names = ()

    with pytest.raises(KeyError, match="hello"):
        S.load_prompt("hello")


def test_sections_는_첫_표식_앞의_글과_겹친_절을_거부한다():
    with pytest.raises(ValueError, match="앞에"):
        P.PromptResource.sections("머리\n<!-- section: a -->\n가\n")
    with pytest.raises(ValueError, match="두 번"):
        P.PromptResource.sections("<!-- section: a -->\n가\n<!-- section: a -->\n나\n")


def test_llm_stage_는_prompt_resource_다():
    assert issubclass(P.LlmStage, P.PromptResource)
```
Run: `.venv/bin/python -m pytest runner/test_pipeline.py -q -k "prompt_resource or sections or llm_stage_는"` → Expected: `AttributeError: … 'PromptResource'`.

- [ ] **Step 2: 구현**

`runner/pipeline.py:22` 의 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 아래에:
```python
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from tools.template import render  # noqa: E402
```
머리 import 에 `import re`, `from typing import ClassVar, Generic, TypeVar`.

`class LlmStage(Stage[C]):` 바로 위에:
```python
SECTION = re.compile(r"^<!-- section: ([a-z0-9-]+) -->\n", re.MULTILINE)


class PromptResource:
    """프롬프트 글을 리소스 파일에서 읽는 단계의 믹스인. 단계당 파일 하나 `<prompt_dir>/<파일>.md`.

    파일 안은 `<!-- section: 이름 -->` 줄로 절을 가를 수 있다. 단계는 읽는 이름을 `prompt_names` 에
    `"<파일>"` 또는 `"<파일>#<절>"` 로 선언한다. 선언 밖은 읽지 않는다 — `test/test_prompt_resources.py` 가
    선언과 디스크의 파일 · 절을 1:1 로 대조한다.
    """
    prompt_dir: ClassVar[str] = ""
    prompt_names: ClassVar[tuple[str, ...]] = ()

    @staticmethod
    def sections(text: str) -> dict[str, str]:
        """절 이름 → 글. 표식이 없으면 `{"": 본문}`. 글은 앞뒤 줄바꿈을 떼고 줄바꿈 하나로 끝낸다."""
        marks = list(SECTION.finditer(text))
        if not marks:
            return {"": text.strip("\n") + "\n"}
        if text[:marks[0].start()].strip():
            raise ValueError("첫 절 표식 앞에 글이 있다")
        out: dict[str, str] = {}
        for i, m in enumerate(marks):
            if m.group(1) in out:
                raise ValueError("절 %r 이 두 번 나온다" % m.group(1))
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            out[m.group(1)] = text[m.end():end].strip("\n") + "\n"
        return out

    @classmethod
    def load_prompt(cls, name: str, **values: str) -> str:
        """`"<파일>"` 또는 `"<파일>#<절>"` 을 읽어 `{{이름}}` 자리를 채운다. 어긋나면 `TemplateError`."""
        if name not in cls.prompt_names:
            raise KeyError("%s 는 프롬프트 %r 를 선언하지 않았다 (선언: %s)"
                           % (cls.__name__, name, ", ".join(cls.prompt_names) or "없음"))
        file, _, section = name.partition("#")
        with open(os.path.join(cls.prompt_dir, file + ".md"), encoding="utf-8") as f:
            parts = cls.sections(f.read())
        if section not in parts:
            raise KeyError("%s.md 에 절 %r 이 없다" % (file, section))
        return render(parts[section], values)
```
`class LlmStage(Stage[C]):` → `class LlmStage(PromptResource, Stage[C]):`.

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest runner/ -q && npm run typecheck:py
git add runner/pipeline.py runner/test_pipeline.py
git commit -m "[update] : pipeline - PromptResource 믹스인, 단계당 한 파일과 절"
```
Expected: 실패 0 · `runner/test_import_isolation.py` 초록(표준 라이브러리만 문다).

#### Task R3: 옮기기 전의 글을 찍는다

**Files:**
- Create: `$TOOLS_ROOT/split-work/capture.py` · `capture.sh` · `extract.py` (저장소 밖)

- [ ] **Step 1: `capture.py`**

```python
#!/usr/bin/env python3
"""리소스로 옮기기 전후의 글을 고정 입력으로 찍는다 — `capture.py <저장소> <출력폴더> <샤드폴더>`.

이름마다 `<출력폴더>/<이름>.txt` 하나. 끝 줄바꿈은 하나로 맞춘다(리소스 절은 줄바꿈 하나로 끝난다).
샤드폴더는 전후 두 번 다 같은 경로여야 한다 — 재조사 절이 그 경로를 글에 싣는다.
"""
import os
import sys
import tempfile

ROOT, OUT, SHARDS = (os.path.abspath(p) for p in sys.argv[1:4])
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner"), os.path.join(ROOT, "machine")]
os.makedirs(OUT, exist_ok=True)
os.makedirs(SHARDS, exist_ok=True)

from mode1.lang import LangHintStage  # noqa: E402
from mode1.survey import AnnotateSymbolsStage as S  # noqa: E402
from mode1.wiki import OutlineWikiStage, WriteWikiStage  # noqa: E402
from runner.wiki.build import sidebarFrom, vitepressConfig  # noqa: E402
import run_mode1_5  # noqa: E402
import run_mode2  # noqa: E402
from viz.init import writeSkeleton  # noqa: E402


def put(name: str, text: str) -> None:
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(text.rstrip("\n") + "\n")


batch = {"id": "L0-B1", "files": ["a.py"],
         "symbols": [{"id": "n1", "name": "f", "kind": "function", "file": "a.py", "line": 1,
                      "depends_on": ["n2"]}]}
put("lang-hint", LangHintStage.hint_prompt("# README\n본문\n"))
put("annotate-batch.full", S.survey_batch_prompt(
    "/대상", "/도구", batch, "  - g — 뜻", targets=["a.py"], total=3,
    pending="  - h (function) b.py:2", name_of={"n2": "g"}))
put("annotate-batch.bare", S.survey_batch_prompt("/대상", "/도구", batch, ""))
put("annotate-nonnode", S.nonnode_prompt("/대상", "/도구"))
put("annotate-pass2", S.pass2_prompt("/대상", "/도구", "L0-B1", "a.py", {"f": {"kind": "function"}},
                                     {"g": {"means": "뜻", "does": "함"}}))
S.quarantine(SHARDS, "L0-B1", S.check_shard(b"{", "L0-B1", "/x.json"))
put("annotate-retry", S.retry_section(SHARDS, "L0-B1"))
put("outline-wiki", OutlineWikiStage.wiki_catalogue_prompt("/대상", "/도구"))
put("write-wiki", WriteWikiStage.wiki_page_prompt(
    "/대상", "/도구", {"file": "index.md", "title": "개요", "symbols": ["f"]}, "  - a.md — A"))
put("mode2-agent.bare", run_mode2.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구"))
put("mode2-agent.terms", run_mode2.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구",
                                                terms_json="/프로젝트/specs/슬러그/terms.json"))
put("mode1_5-ask", run_mode1_5.ask_argv("/도구", "/계획.md", "/작업", "/py")[-1])
put("vitepress-config", vitepressConfig("대상", sidebarFrom(["index.md", "a.md"]), "/out"))
with tempfile.TemporaryDirectory() as d:
    writeSkeleton(d, "슬러그", "2026-01-01", "제목 `백틱`", "main", "v1")
    for name in ("data.ts", "report.tsx"):
        with open(os.path.join(d, name), encoding="utf-8") as f:
            put("skeleton-" + name, f.read())
print(OUT)
```

- [ ] **Step 2: `capture.sh`**

```bash
#!/bin/bash
# capture.sh <저장소> <출력폴더> — 파이썬 글 + DOT 둘 + 보고서 HTML 하나
set -e
REPO="$1"; OUT="$2"
"$REPO/.venv/bin/python" "$TOOLS_ROOT/split-work/capture.py" "$REPO" "$OUT" "$TOOLS_ROOT/split-work/fixture-shards"
"$REPO/.venv/bin/python" "$REPO/viz/render_modules.py" "$REPO/out/codegraph-raw/codegraph.json" -o "$OUT/modules" >/dev/null
"$REPO/.venv/bin/python" "$REPO/viz/render_classes.py" "$REPO/out/codegraph-raw/codegraph.json" --module machine -o "$OUT/classes" >/dev/null
rm -f "$OUT"/modules.svg "$OUT"/modules.png "$OUT"/classes.svg "$OUT"/classes.png
( cd "$REPO/docs/superpowers/specs/runner-stage-machine" && "$REPO/bin/report-spec" build >/dev/null && cp out/report.html "$OUT/report.html" )
```
(`--module machine` 은 🔵 `ARCHITECTURE.md` §8 이 적은 모듈 이름이다. 없다고 나오면 오류에 보이는 모듈 하나로 바꾸고 전후 같은 것을 쓴다.)

- [ ] **Step 3: `extract.py`** — 파이썬 문자열 하나를 리소스 글로 옮기는 기계

```python
#!/usr/bin/env python3
"""파이썬 안의 문자열 하나를 `{{이름}}` 리소스 글로 옮긴다 — `extract.py <파일.py> <줄> <출력>`.

`<줄>` 이 걸치는 가장 바깥 문자열(`.format()` 용 상수 또는 f-문자열)을 고른다.
- `.format()` 자리 `{x}` → `{{x}}`. 이스케이프 `{{ }}` 는 한 겹 `{ }` 로 풀린다.
- f-문자열 식 `{식}` → `{{slotN}}`. 대응을 찍는다 — 리소스에서 slotN 을 뜻 있는 이름으로 바꾸고,
  부르는 쪽에서 `이름=str(식)` 으로 넘긴다.
- 앞뒤 줄바꿈은 뗀다. 앞에서 뗀 수를 찍는다 — 부르는 쪽이 그만큼 `"\n"` 을 앞에 붙인다.
"""
import ast
import string
import sys

path, line, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(path, encoding="utf-8") as f:
    tree = ast.parse(f.read())
spans = [n for n in ast.walk(tree)
         if (isinstance(n, ast.JoinedStr) or (isinstance(n, ast.Constant) and isinstance(n.value, str)))
         and n.end_lineno is not None and n.lineno <= line <= n.end_lineno]
node = min(spans, key=lambda n: n.lineno)     # 같은 줄에서 시작하면 ast.walk 가 바깥을 먼저 낸다
parts: list[str] = []
slots: list[str] = []
if isinstance(node, ast.Constant):
    for literal, field, spec, conv in string.Formatter().parse(node.value):
        parts.append(literal)
        if field is not None:
            assert not spec and not conv, "서식 지정자가 있다: %s" % field
            parts.append("{{%s}}" % field)
            slots.append(field)
else:
    for v in node.values:
        if isinstance(v, ast.Constant):
            parts.append(str(v.value))
        else:
            assert isinstance(v, ast.FormattedValue) and v.format_spec is None and v.conversion == -1, ast.unparse(v)
            name = "slot%d" % (len(slots) + 1)
            parts.append("{{%s}}" % name)
            slots.append("%s = %s" % (name, ast.unparse(v.value)))
text = "".join(parts)
lead = len(text) - len(text.lstrip("\n"))
with open(out, "w", encoding="utf-8") as f:
    f.write(text.strip("\n") + "\n")
print(out)
print("  앞 줄바꿈 %d개를 뗐다" % lead)
for s in sorted(set(slots)):
    print("  자리", s)
```

- [ ] **Step 4: 옮기기 전을 찍는다**

```bash
chmod +x "$TOOLS_ROOT/split-work/capture.sh"
"$TOOLS_ROOT/split-work/capture.sh" "$PWD" "$TOOLS_ROOT/split-work/before"
ls "$TOOLS_ROOT/split-work/before"
```
Expected: `.txt` 열넷 · `modules.dot` · `classes.dot` · `report.html`. `out/codegraph-raw/codegraph.json` 이 없으면 먼저 `.venv/bin/python bin/report-wiki prep .`. 커밋 없음.

#### Task R4: Mode 1 프롬프트 → 단계당 한 파일

**Files:**
- Create: `runner/mode1/prompts/{lang-hint,annotate-symbols,outline-wiki,write-wiki}.md`
- Modify: `runner/mode1/context.py` · `lang.py` · `survey.py` · `wiki.py`
- Delete: `runner/mode1/prompt/` (죽은 사본 넷)

- [ ] **Step 1: 큰 다섯을 기계로 뽑는다** — 한 파일에서 뽑기를 모두 끝낸 뒤 그 파일을 고친다(고치면 줄이 밀린다)

```bash
X="$TOOLS_ROOT/split-work/extract.py"; T="$TOOLS_ROOT/split-work/frag"; mkdir -p "$T" runner/mode1/prompts
.venv/bin/python $X runner/mode1/survey.py 113 "$T/batch.md"
.venv/bin/python $X runner/mode1/survey.py 224 "$T/nonnode.md"
.venv/bin/python $X runner/mode1/survey.py 478 "$T/pass2.md"
.venv/bin/python $X runner/mode1/wiki.py 38 runner/mode1/prompts/outline-wiki.md
.venv/bin/python $X runner/mode1/wiki.py 128 runner/mode1/prompts/write-wiki.md
```
Expected 자리:

| 글 | 자리 |
|---|---|
| `batch` | `bid` `deps` `n` `repo` `root` `syms` |
| `nonnode` | `reading` `repo` `root` |
| `pass2` | `bid` `file` `mine` `repo` `root` `theirs` |
| `outline-wiki.md` | `repo` `root` |
| `write-wiki.md` | `fname` `lower` `repo` `root` `syms` `title` |

다섯 다 "앞 줄바꿈 0개". 옛 `.format(...)` 이 넘기는데 글에 없는 이름은 Step 3 에서 빼고 넘긴다.

- [ ] **Step 2: 작은 넷은 손으로**

`"$T/scope.md"`:
```
## 범위 — 증분 조사다. 저장소 전량을 읽지 마라

지난 조사 결과가 {{reading}} 에 이미 있다. 그중
**아래 {{count}}개 파일에 걸린 레코드만** 다시 만든다. 추적 파일 {{total}}개 중 {{count}}개다.

{{targets}}

- **이 목록에 없는 파일은 읽지 마라.** 나머지 레코드는 그대로 살아 있고, 손대면 안 된다.
- 목록 밖의 이름이 필요하면 소스가 아니라 **기존 terms-reading.json 과 codegraph.json**
  을 근거로 쓴다.
- 목록의 파일이 사라졌거나 읽을 수 없으면 **지어내지 말고** 보고에 적는다.
```

`"$T/pending.md"`:
```
## 아직 조사되지 않은 의존 대상 — 열지 마라

{{pending}}

이것들의 모듈을 **열지 않는다.** 이름·종류·시그니처(호출 자리에서 보이는 것)만으로 **얕게** 쓴다.
그렇게 쓴 레코드에는 `"shallow": ["위 목록의 이름 그대로"]` 을 적는다 — 기계가 모아 두었다가, 그 대상이 조사된 뒤
**너 대신 다른 세션이** does 와 uses[].label 을 다듬는다. means 와 where 는 네 코드만 보면 되니 지금 정확히 쓴다.
뜻을 지어내지 마라 — does 에는 코드에서 보이는 사실만.
```

`"$T/retry.md"`:
```
## 지난 시도가 되돌려졌다 — 같은 실수를 하지 마라

이 배치는 한 번 돌았고, 기계 검문이 그 샤드에서 결함 {{count}}개를 찾아 되돌렸다:

{{faults}}

- 되돌린 샤드는 {{bad}} 에 그대로 있다. **결함의 자리를 열어 무엇이 깨졌는지 먼저 본다.**
- 읽은 내용을 다시 쓰되, **끝내기 전에 검문 명령을 반드시 돌려 `통과` 를 본다.**
```

`runner/mode1/prompts/lang-hint.md`:
```
아래는 한 저장소의 최상위 문서다. 이 저장소에 **정적 분석기를 돌려 코드 지도를 만들려 한다.**
어느 언어를 대상으로 삼아야 가장 쓸모 있는 지도가 나오겠는지 판단해라.

고를 수 있는 것과 그 수집기:
  cpp -> clang-uml    cs -> roslyn-dump    py -> griffe+pycalls    ts -> (수집기 없음)

문서가 어떤 언어를 많이 이야기하는지가 아니라, **분석해서 얻을 것이 있는 코드**가
어느 언어인지를 본다. 넷 중 하나를 **낱말 하나로만** 답해라. 설명하지 마라.
판단이 안 서면 `unknown` 이라고 답해라.

{{docs}}
```

`annotate-symbols.md` 로 묶는다:
```bash
{ for s in batch scope pending retry nonnode pass2; do
    printf '<!-- section: %s -->\n' "$s"; cat "$T/$s.md"; printf '\n'
  done; } > runner/mode1/prompts/annotate-symbols.md
```

- [ ] **Step 3: 단계가 리소스를 읽게 고친다**

`runner/mode1/context.py` — `ROOT` 근처에:
```python
# Mode 1 LLM 단계의 프롬프트 리소스. 단계마다 `prompt_names` 로 자기 것을 선언한다.
PROMPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
```

`runner/mode1/lang.py` — `LangHintStage` 머리(`emits` 아래)에 `prompt_dir = X.PROMPT_DIR` · `prompt_names = ("lang-hint",)`, 그리고:
```python
    @staticmethod
    def hint_prompt(docs: str) -> str:
        return LangHintStage.load_prompt("lang-hint", docs=docs)
```

`runner/mode1/survey.py` — `AnnotateSymbolsStage` 머리에:
```python
    prompt_dir = X.PROMPT_DIR
    prompt_names = ("annotate-symbols#batch", "annotate-symbols#scope", "annotate-symbols#pending",
                    "annotate-symbols#retry", "annotate-symbols#nonnode", "annotate-symbols#pass2")
```
여섯 함수의 `return` 을 바꾼다(앞의 계산은 그대로):
```python
    # warmup_section
        if not targets:
            return ""
        목록 = "\n".join("  " + t for t in targets)
        return "\n" + AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#scope", reading=X.reading_path(repo, ROOT), count=str(len(targets)),
            total=str(total), targets=목록)

    # survey_batch_prompt — syms 계산 뒤
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#batch", repo=repo, root=root, bid=batch["id"], n=str(len(batch["symbols"])),
            syms=syms, deps=dep_records or "  (없음 — 너는 최하층이다)") \
            + AnnotateSymbolsStage.pending_section(pending) \
            + AnnotateSymbolsStage.warmup_section(targets, total, repo)

    # pending_section
        if not pending:
            return ""
        return "\n" + AnnotateSymbolsStage.load_prompt("annotate-symbols#pending", pending=pending)

    # nonnode_prompt
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#nonnode", repo=repo, root=root, reading=X.reading_path(repo, ROOT))

    # retry_section
        faults = AnnotateSymbolsStage.load_faults(shard_dir, bid)
        if not faults:
            return ""
        lines = "\n".join("  " + AnnotateSymbolsStage.fault_line(f).replace("\n", "\n  ") for f in faults)
        return "\n" + AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#retry", count=str(len(faults)), faults=lines,
            bad=os.path.join(shard_dir, bid + ".json.bad"))

    # pass2_prompt — mine · theirs 계산 뒤
        return AnnotateSymbolsStage.load_prompt(
            "annotate-symbols#pass2", repo=repo, root=root, bid=bid, file=file, mine=mine,
            theirs=theirs or "  (없음)")
```
`warmup_section` 독스트링의 "⚠ 이 글은 부르는 쪽이 `.format()` 을 돌린 뒤에 이어 붙는다…" 두 줄은 지운다.

`runner/mode1/wiki.py` — `OutlineWikiStage` 에 `prompt_dir = X.PROMPT_DIR` · `prompt_names = ("outline-wiki",)`, `WriteWikiStage` 에 `prompt_dir = X.PROMPT_DIR` · `prompt_names = ("write-wiki",)`:
```python
    # wiki_catalogue_prompt
        return OutlineWikiStage.load_prompt("outline-wiki", repo=repo, root=root)

    # wiki_page_prompt
        return WriteWikiStage.load_prompt(
            "write-wiki", repo=repo, root=root, fname=page["file"],
            title=page.get("title") or page["file"],
            syms=", ".join(page.get("symbols") or []) or "(개괄 — 특정 심볼 없음)",
            lower=lower_pages or "  (없음 — 네가 첫 장이다)")
```

- [ ] **Step 4:**
```bash
git rm -q -r runner/mode1/prompt
.venv/bin/python -m pytest runner/ -q && npm run typecheck:py
git add runner/mode1/prompts runner/mode1/context.py runner/mode1/lang.py runner/mode1/survey.py runner/mode1/wiki.py
git commit -m "[refactor] : mode 1 프롬프트를 단계당 한 파일 리소스로 - 죽은 사본 넷 삭제"
```

#### Task R5: Mode 1.5 · Mode 2 프롬프트 → `runner/prompts/`

**Files:**
- Create: `runner/prompts/{agent,ask}.md`
- Modify: `runner/run_mode2.py:226-307,422-428` · `runner/run_mode1_5.py:507-520,718`

- [ ] **Step 1:**
```bash
X="$TOOLS_ROOT/split-work/extract.py"; T="$TOOLS_ROOT/split-work/frag"; mkdir -p runner/prompts
.venv/bin/python $X runner/run_mode2.py 251 "$T/agent-main.md"
.venv/bin/python $X runner/run_mode2.py 240 "$T/agent-terms.md"
{ printf '<!-- section: main -->\n'; cat "$T/agent-main.md"; printf '\n<!-- section: terms -->\n'; cat "$T/agent-terms.md"; } \
  > runner/prompts/agent.md
```
Expected — `main` 자리 `doc_dir folder project root spec_file terms_block`(앞 줄바꿈 0), `terms` 자리 `terms_json`(**앞 줄바꿈 1개**). 🔵 옛 코드는 `slug` 도 넘기지만 글에 `{slug}` 가 없다 — 새 호출에서 뺀다.

`runner/prompts/ask.md` (한 줄):
```
/{{skill}} 계획서 {{plan}} · 작업 폴더 {{workdir}} · 후보는 {{candidates}} 에 이미 있다. 문항지는 {{questions}} 에 쓰고, 기입란은 `{{python}} {{runner}} {{plan}} --workdir {{workdir}}` 를 돌려 {{sheet}} 로 깔고, 사용자에게 한 용어씩 물어 UserAns 를 채운 것을 {{answers}} 으로 둔 뒤 세션을 끝낸다. 채점(grade · emit)은 이 세션이 끝나면 실행기가 이어서 한다 — 여기서 하지 마라.
```

- [ ] **Step 2: Mode 2** — `AgentStage` 머리에 `prompt_dir = os.path.join(ROOT, "runner", "prompts")` · `prompt_names = ("agent#main", "agent#terms")`. `agent_prompt` 의 몸을:
```python
    folder = report_dir(project, slug, doc_dir)
    terms_block = ""
    if terms_json:
        terms_block = "\n" + AgentStage.load_prompt("agent#terms", terms_json=terms_json)
    return AgentStage.load_prompt("agent#main", project=project, spec_file=spec_file, folder=folder,
                                  root=root, terms_block=terms_block, doc_dir=doc_dir)
```

- [ ] **Step 3: Mode 1.5** — `class AskStage(P.Stage[Mode15Context]):` → `class AskStage(P.PromptResource, P.Stage[Mode15Context]):`, 머리에 `prompt_dir = os.path.join(ROOT, "runner", "prompts")` · `prompt_names = ("ask",)`. `ask_argv` 의 `prompt = (…)` 를:
```python
    prompt = AskStage.load_prompt(
        "ask", skill=SKILL, plan=plan, workdir=workdir,
        candidates=os.path.join(workdir, CANDIDATES), questions=os.path.join(workdir, QUESTIONS),
        python=python, runner=os.path.join(root, "runner", "run_mode1_5.py"),
        sheet=os.path.join(workdir, SHEET), answers=os.path.join(workdir, ANSWERS)).rstrip("\n")
```

- [ ] **Step 4:**
```bash
.venv/bin/python -m pytest runner/ -q && npm run typecheck:py
git add runner/prompts runner/run_mode2.py runner/run_mode1_5.py
git commit -m "[refactor] : mode 1.5 와 2 프롬프트를 runner/prompts 리소스로"
```

#### Task R6: 파일 템플릿 일곱 → `templates/`

**Files:**
- Create: `viz/templates/report/{data.ts.tmpl,report.tsx.tmpl,render.mjs.tmpl,entry.ts}` · `viz/templates/dot/{classes-head,modules-head,modules-legend}.dot.tmpl` · `runner/wiki/templates/vitepress.config.mts.tmpl`
- Modify: `viz/init.py` · `viz/build.py` · `viz/render_classes.py` · `viz/render_modules.py` · `runner/wiki/build.py`

`viz/templates/` 를 `report/`(Mode 2) 와 `dot/`(Mode 1) 둘로 가른다 — B1 의 경로 목록이 폴더 하나로 끝난다.

- [ ] **Step 1: 보고서 템플릿 넷**

`viz/templates/report/data.ts.tmpl`:
```
import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: {{version}},
  slug: {{slug}},
  specName: {{specName}},
  date: {{date}},
  branch: {{branch}},
  decisions: [],
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮겨 적는다.
  //   report-term collect <plan.md> <terms-db.json>  →  (스킬이 묻는다)  →  report-term grade  →  report-term emit
  // terms.json 의 { "용어": { TermMeans, UserMentalValue } } 를
  // { id, label, short, kind, mental } 로 옮긴다. 자동 import 하지 않는다 — 이 파일은 사람이 읽는 파일이다.
  terms: [],
};
```

`viz/templates/report/report.tsx.tmpl`:
```
import { Page, Section, DecisionTable, VerdictFooter } from "report-builder";
import { data } from "./data.js";

export { data };

export default function Report() {
  return (
    <Page data={data}>
      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>
      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
```

`viz/templates/report/render.mjs.tmpl`:
```
import * as mod from 'file://{{bundle}}';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';

const html = renderToStaticMarkup(mod.default());
let refs = {};
if (Array.isArray(mod.data.terms) && mod.data.terms.length > 0 && typeof mod.defineTerms === 'function') {
    const T = mod.defineTerms(mod.data.terms);
    for (const t of mod.data.terms) {
        refs[t.id] = renderToStaticMarkup(createElement(T, { id: t.id }, t.id));
    }
}
console.log(JSON.stringify({ body: html, data: mod.data, refs }));
```

`viz/templates/report/entry.ts`:
```
export { default, data } from "./report.tsx";
export { defineTerms } from "report-builder";
```

- [ ] **Step 2: DOT 셋은 기계로**

```bash
X="$TOOLS_ROOT/split-work/extract.py"; mkdir -p viz/templates/dot
.venv/bin/python $X viz/render_classes.py 384 viz/templates/dot/classes-head.dot.tmpl
.venv/bin/python $X viz/render_modules.py 207 viz/templates/dot/modules-head.dot.tmpl
.venv/bin/python $X viz/render_modules.py 284 viz/templates/dot/modules-legend.dot.tmpl
```
찍힌 `slotN = <식>` 마다 템플릿의 `{{slotN}}` 을 식의 마지막 이름으로 바꾸고(`g.get('language')` → `{{language}}` · `detail_path or '(없음 — 3분할 미적용)'` → `{{detail_path}}` · `C_BORDER` → `{{C_BORDER}}`), 옛 `w(f"""…""")` 는 `w(render_file(os.path.join(TEMPLATES, "<파일>"), {"<이름>": str(<식>), …}))` 로. 앞 줄바꿈을 뗐다고 찍히면 `"\n" + render_file(…)`.

- [ ] **Step 3: VitePress 설정** — `runner/wiki/templates/vitepress.config.mts.tmpl`:

```
// report-wiki build 가 생성한다. 손으로 고치지 말 것 — 다음 빌드에서 덮어쓴다.
// defineConfig 를 쓰지 않는 이유는 runner/wiki/build.mjs 의 주석을 보라.
export default ({
  title: {{title}},
  description: "codegraph 정적 계층 + deep-wiki 산문",
  srcDir: ".",
  outDir: {{out_dir}},
  // 위키 페이지는 하위 폴더 없는 평평한 이름이라 `../` 가 있는 링크는 위키 밖이다.
  // 죽은 링크 검사는 그 바깥을 확인할 수 없어 전부 죽은 것으로 본다. 위키 안의 깨진
  // 링크는 계속 잡아야 하므로 검사를 통째로 끄지 않고 이 꼴만 뺀다.
  ignoreDeadLinks: [/\.\.\//],
  themeConfig: {
    sidebar: [
{{items}}
    ],
  },
});
```
(둘째 줄의 낡은 `build.mjs` 언급은 바이트 대조를 위해 그대로 옮긴다. 고치는 것은 별건이다.)

- [ ] **Step 4: 부르는 쪽**

`viz/init.py` 머리(`import subprocess` 아래):
```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.template import render_file  # noqa: E402

TEMPLATES = os.path.join(ROOT, "viz", "templates", "report")
```
`writeSkeleton` 의 두 글을:
```python
    data_ts = render_file(os.path.join(TEMPLATES, "data.ts.tmpl"), {
        "version": q(version), "slug": q(slug), "specName": q(specName),
        "date": q(date), "branch": q(branch)})
    …
    report_tsx = render_file(os.path.join(TEMPLATES, "report.tsx.tmpl"), {})
```
`main()` 안의 지역 `ROOT = …` 줄은 지운다.

`viz/build.py` 머리에 `from tools.template import render_file` · `TEMPLATES = os.path.join(ROOT, "viz", "templates", "report")`. esbuild `input=` → `render_file(os.path.join(TEMPLATES, "entry.ts"), {})`, `render_script = f"""…"""` → `render_file(os.path.join(TEMPLATES, "render.mjs.tmpl"), {"bundle": tmp_mjs})`.

`viz/render_classes.py` · `viz/render_modules.py` 머리에:
```python
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from tools.template import render_file  # noqa: E402

TEMPLATES = os.path.join(_ROOT, "viz", "templates", "dot")
```

`runner/wiki/build.py` 머리에 `from tools.template import render_file  # noqa: E402` · `TEMPLATES = os.path.join(ROOT, "runner", "wiki", "templates")`. `vitepressConfig` 의 `return f"""…"""` 를(`items_str` 줄 삭제):
```python
    return render_file(os.path.join(TEMPLATES, "vitepress.config.mts.tmpl"), {
        "title": json.dumps(repoName + ' 코드베이스 위키', ensure_ascii=False),
        "out_dir": json.dumps(outDir, ensure_ascii=False),
        "items": ",\n".join(items)})
```

- [ ] **Step 5:**
```bash
.venv/bin/python -m pytest -q && npm test && npm run typecheck:py
git add viz/templates runner/wiki/templates viz/init.py viz/build.py viz/render_classes.py viz/render_modules.py runner/wiki/build.py
git commit -m "[refactor] : 파일 템플릿 일곱을 templates 리소스로"
```
Expected: 실패는 알려진 빨강 둘(`test_wiki.py::test_check_는_통과를_통과로_보고한다` · `test_survey_plan.py::test_이_저장소_실측`)뿐.

#### Task R7: 설정값 → `config/*.toml`

**Files:**
- Create: `config/mode1.toml` · `config/report.toml` · `test/test_config.py`
- Modify: `runner/mode1/context.py` · `runner/mode1/lang.py:14-16` · `runner/run_mode1.py:201` · `runner/run_mode2.py:89-100,468` · `viz/init.py:11-14` · `runner/test_mode1.py` · `runner/CLAUDE.md` · `viz/CLAUDE.md`

- [ ] **Step 1: 리소스 둘**

`config/mode1.toml`:
```toml
# Mode 1 이 부르는 Model. 별명이 아니라 정확한 ID 를 쓴다 — 별명은 최신판을 따라 움직여 측정이 흔들린다.
[models]
sessions = "claude-sonnet-5-5"           # annotate-symbols · outline-wiki · write-wiki 의 세션. --model 의 기본값
lang_hint = "claude-haiku-4-5-20251001"  # lang-hint. 낱말 하나를 내는 것이 전부라 가장 싼 것

# 진입 알림의 어림 — 배치 수 × 배치당 비용(USD). evals/runs 의 실측 범위. 찍기만 하고 묻지 않는다.
[estimate]
usd_per_batch_min = 0.4
usd_per_batch_max = 1.4
```

`config/report.toml`:
```toml
# Mode 1.5 · Mode 2 의 설정.
[models]
mode2_agent = "opus"   # run_mode2.py --model 의 기본값

# 원본 문서가 사는 자리와 파일명 관례. viz/init.py 와 runner/run_mode2.py 가 같이 읽는다.
# specs/ 만 -design.md 를 요구한다 — 같은 폴더에 -before.svg · -design-review.html 이 함께 살아 오타 가드가 된다.
[[doc_dirs]]
dir = "specs"
pattern = '^(\d{4}-\d{2}-\d{2})-(.+)-design\.md$'

[[doc_dirs]]
dir = "plans"
pattern = '^(\d{4}-\d{2}-\d{2})-(.+)\.md$'
```

- [ ] **Step 2: 실패하는 시험** — `runner/test_mode1.py` 끝에:
```python
def test_설정이_정확한_모델_ID_를_준다() -> None:
    cfg = X.load_config()
    assert cfg["models"]["sessions"].startswith("claude-")
    assert cfg["models"]["lang_hint"].startswith("claude-")
    assert LG.LANG_SELECT_MODEL == cfg["models"]["lang_hint"]
    assert 0 < cfg["estimate"]["usd_per_batch_min"] < cfg["estimate"]["usd_per_batch_max"]
```
`test/test_config.py`:
```python
"""원본 문서 자리 규칙은 config/report.toml 한 곳에서 온다 — 두 읽는 쪽이 같은 것을 본다."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner")]

import run_mode2  # noqa: E402
from viz.init import DOC_DIRS as VIZ_DOC_DIRS  # noqa: E402


def test_원본_문서_자리_규칙은_한_곳에서_온다():
    assert [(d, p.pattern) for d, p in run_mode2.DOC_DIRS] == \
        [(d["dir"], d["re"].pattern) for d in VIZ_DOC_DIRS]
    assert [d for d, _ in run_mode2.DOC_DIRS] == ["specs", "plans"]


def test_mode2_모델_기본값은_설정에서_온다():
    assert run_mode2.CONFIG["models"]["mode2_agent"] == "opus"
```
Run: `.venv/bin/python -m pytest runner/test_mode1.py test/test_config.py -q -k "설정 or 한_곳 or 기본값"` → Expected: `AttributeError`.

- [ ] **Step 3: 구현**

`runner/mode1/context.py` (`import msgspec` 가 없으면 더한다):
```python
class ModelsConfig(TypedDict):
    sessions: str
    lang_hint: str


class EstimateConfig(TypedDict):
    usd_per_batch_min: float
    usd_per_batch_max: float


class Mode1Config(TypedDict):
    """`config/mode1.toml`."""
    models: ModelsConfig
    estimate: EstimateConfig


CONFIG_PATH = os.path.join(ROOT, "config", "mode1.toml")


def load_config(path: str = CONFIG_PATH) -> Mode1Config:
    """설정 파일을 형으로 읽는다. 꼴이 안 맞으면 msgspec 예외 — 조용히 기본값으로 가지 않는다."""
    with open(path, "rb") as f:
        return msgspec.toml.decode(f.read(), type=Mode1Config)
```
`runner/mode1/lang.py:14-16` → `LANG_SELECT_MODEL = X.load_config()["models"]["lang_hint"]`. `runner/run_mode1.py:201` 의 `default="claude-sonnet-5-5"` → `default=X.load_config()["models"]["sessions"]`.

`runner/run_mode2.py:89-100` 의 주석과 `DOC_DIRS = [...]` 를(`from typing import TypedDict` 추가):
```python
class DocDirConfig(TypedDict):
    dir: str
    pattern: str


class ModelsConfig(TypedDict):
    mode2_agent: str


class ReportConfig(TypedDict):
    """`config/report.toml`. 원본 문서 자리 규칙은 `viz/init.py` 도 같은 파일에서 읽는다."""
    models: ModelsConfig
    doc_dirs: list[DocDirConfig]


with open(os.path.join(ROOT, "config", "report.toml"), "rb") as _f:
    CONFIG = msgspec.toml.decode(_f.read(), type=ReportConfig)

DOC_DIRS = [(d["dir"], re.compile(d["pattern"])) for d in CONFIG["doc_dirs"]]
```
`:468` → `default=CONFIG["models"]["mode2_agent"], help="에이전트가 쓸 LLM Model (기본: config/report.toml)"`.

`viz/init.py:11-14` 의 `DOC_DIRS` 를(머리에 `import tomllib`):
```python
with open(os.path.join(ROOT, "config", "report.toml"), "rb") as _f:
    _CONFIG = tomllib.load(_f)

DOC_DIRS: list[dict[str, Any]] = [{"dir": str(d["dir"]), "re": re.compile(str(d["pattern"]))}
                                  for d in _CONFIG["doc_dirs"]]
```

`runner/CLAUDE.md` 의 마지막 Gotcha("원본 문서 자리 규칙이 두 곳에 중복돼 산다")와 `viz/CLAUDE.md` 의 "⚠ 관례가 … 두 곳에 산다" 문단을 각각 한 줄로: "원본 문서 자리 규칙은 `config/report.toml` 한 곳이다. `test/test_config.py` 가 두 읽는 쪽이 같은 것을 보는지 고정한다."

- [ ] **Step 4:**
```bash
.venv/bin/python -m pytest -q && npm run typecheck:py
git add config runner/mode1/context.py runner/mode1/lang.py runner/run_mode1.py runner/run_mode2.py viz/init.py runner/test_mode1.py test/test_config.py runner/CLAUDE.md viz/CLAUDE.md
git commit -m "[refactor] : 모델 id 와 원본 문서 자리 규칙을 config toml 로 - DOC_DIRS 중복 해소"
```

#### Task R8: 옮긴 뒤를 찍어 대조한다

```bash
"$TOOLS_ROOT/split-work/capture.sh" "$PWD" "$TOOLS_ROOT/split-work/after"
diff -r "$TOOLS_ROOT/split-work/before" "$TOOLS_ROOT/split-work/after" && echo "같다"
```
Expected: `같다`. 다르면 diff 가 어느 리소스의 어느 줄인지 말한다 — 리소스를 고친다. 커밋 없음.

#### Task R9: 다시 들어오지 못하게 막는다

**Files:**
- Create: `test/test_prompt_resources.py`
- Modify: 루트 `CLAUDE.md` · `runner/CLAUDE.md` · `viz/CLAUDE.md` · `tools/CLAUDE.md` · `test/CLAUDE.md`

- [ ] **Step 1: 게이트 시험**

```python
"""리소스와 코드를 가르는 게이트 — 긴 글은 리소스 파일에 살고, 프롬프트 선언과 파일 · 절은 1:1 이다."""
import ast
import glob
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner"), os.path.join(ROOT, "machine")]

LONG_LINES = 6     # 줄바꿈이 이만큼 이상인 글 상수는 리소스로 뺀다
LONG_CHARS = 200   # 한 줄이라도 이 길이 이상이면 리소스로 뺀다
RUNNERS = ("run_mode1", "run_mode1_5", "run_mode2")   # 이 저장소에 있는 것만 import 해 단계 클래스를 모은다


def code_files() -> list[str]:
    out: list[str] = []
    for top in ("runner", "viz"):
        for p in glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True):
            if not os.path.basename(p).startswith("test_") and "__pycache__" not in p:
                out.append(p)
    return sorted(out)


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                ids.add(id(b.value))
    return ids


def all_subclasses(cls: type) -> set[type]:
    out: set[type] = set()
    for c in cls.__subclasses__():
        out |= {c} | all_subclasses(c)
    return out


def test_파이썬에_리소스로_뺄_긴_글이_없다() -> None:
    hits: list[str] = []
    for p in code_files():
        with open(p, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        docs = docstring_nodes(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                if n.value.count("\n") >= LONG_LINES or len(n.value) >= LONG_CHARS:
                    hits.append("%s:%d" % (os.path.relpath(p, ROOT), n.lineno))
    assert hits == [], "리소스 파일로 옮길 글이 코드에 있다:\n" + "\n".join(hits)


def test_프롬프트_선언과_파일_절이_1대1이다() -> None:
    for name in RUNNERS:
        if os.path.exists(os.path.join(ROOT, "runner", name + ".py")):
            importlib.import_module(name)
    import pipeline as P
    declared = {os.path.normpath(os.path.join(c.prompt_dir, n))
                for c in all_subclasses(P.PromptResource) for n in getattr(c, "prompt_names", ())}
    on_disk: set[str] = set()
    for p in glob.glob(os.path.join(ROOT, "runner", "**", "prompts", "*.md"), recursive=True):
        base = os.path.normpath(p[:-len(".md")])
        with open(p, encoding="utf-8") as f:
            for sec in P.PromptResource.sections(f.read()):
                on_disk.add(base + ("#" + sec if sec else ""))
    assert sorted(on_disk - declared) == [], "아무 단계도 읽지 않는 프롬프트 파일 · 절이 있다"
    assert sorted(declared - on_disk) == [], "선언했는데 없는 프롬프트 파일 · 절이 있다"


def test_템플릿_파일은_모두_코드가_부른다() -> None:
    sources = ""
    for p in code_files():
        with open(p, encoding="utf-8") as f:
            sources += f.read()
    templates = [t for top in ("runner", "viz")
                 for t in glob.glob(os.path.join(ROOT, top, "**", "templates", "**", "*"), recursive=True)
                 if os.path.isfile(t)]
    orphans = sorted(os.path.relpath(t, ROOT) for t in templates if os.path.basename(t) not in sources)
    assert orphans == [], "아무도 부르지 않는 템플릿이 있다:\n" + "\n".join(orphans)
```
Run: `.venv/bin/python -m pytest test/test_prompt_resources.py -q` → Expected: `3 passed`. 첫 시험이 걸리면 그 글을 R4~R6 처럼 옮긴다. 기준을 올려 통과시키지 않는다.

- [ ] **Step 2: 일부러 깨 본다** — 게이트가 실제로 잡는지(검사표 □4)

```bash
printf '\nX = """1\n2\n3\n4\n5\n6\n7"""\n' >> runner/measure.py
.venv/bin/python -m pytest test/test_prompt_resources.py -q -k 긴_글    # 기대: 실패, runner/measure.py
git checkout -- runner/measure.py
printf '\n<!-- section: orphan -->\n고아\n' >> runner/prompts/ask.md
.venv/bin/python -m pytest test/test_prompt_resources.py -q -k 1대1     # 기대: 실패 — ask.md 가 절을 갖게 되어 선언 "ask" 와 어긋난다
git checkout -- runner/prompts/ask.md
```

- [ ] **Step 3: 규약을 문서에**

루트 `CLAUDE.md` "작업 규약" 맨 앞에:
```markdown
- **리소스와 코드를 가른다 (최우선).** LLM 프롬프트는 단계당 한 파일 `runner/**/prompts/<단계>.md`(안은
  `<!-- section: 이름 -->` 으로 가른다), 파일 템플릿은 `**/templates/*`, 설정값은 `config/*.toml`. 파이썬은 읽기만
  한다 — 프롬프트는 단계의 `PromptResource.load_prompt("<파일>#<절>")`, 템플릿은 `tools.template.render_file`.
  자리표시는 `{{이름}}` 하나다. `test/test_prompt_resources.py` 가 막는다.
```
`runner/CLAUDE.md` — "흔한 변경 패턴" Mode 1 묶음에 `#   runner/mode1/prompts/<단계>.md  LLM 단계면 프롬프트 리소스 · 클래스에 prompt_names 선언("<파일>#<절>")` 한 줄, 표의 `mode1/` 행 "계산과 프롬프트는 … `@staticmethod`" → "계산은 단계 클래스의 `@staticmethod`, 프롬프트 글은 `mode1/prompts/*.md`", `pipeline.py` 행에 `PromptResource`. `tools/CLAUDE.md` 표에 `| template.py | 리소스 파일의 {{이름}} 자리를 채운다. 자리와 값이 어긋나면 예외 | runner/pipeline.py · viz/*.py · runner/wiki/build.py |`. `viz/CLAUDE.md` 표에 `| templates/report/ · templates/dot/ | 보고서 뼈대 · 렌더 스크립트 / DOT 머리 · 범례 |`. `test/CLAUDE.md` 표에 `test_prompt_resources.py` · `test_config.py` 두 행.

- [ ] **Step 4:**
```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools
.venv/bin/python -m pytest test/test_docs_citations.py test/test_prompt_resources.py -q
git add test/test_prompt_resources.py CLAUDE.md runner/CLAUDE.md tools/CLAUDE.md viz/CLAUDE.md test/CLAUDE.md */README.md
git commit -m "[test] : 리소스 게이트 - 코드 안의 긴 글, 프롬프트 선언과 파일 절 1대1, 템플릿 고아"
```

### Phase A — 두 mode 사이의 시험·코드 결합을 끊는다

#### Task A1: 결정 기록 0011

**Files:** Create `docs/decisions/0011-split-mode1-and-report.md` · Modify `docs/decisions/README.md`

- [ ] **Step 1**

```markdown
# 결정 0011 — Mode 1 과 Mode 1.5+2 를 두 저장소로 가르고, 경계를 데이터 계약으로 둔다

**상태** 확정 · 2026-10-24 · 사용자 판단 (유스케이스 시험 열 장면과 재질의 하나를 거쳤다)

**무엇을.** `report-builder` 는 Mode 1.5 + Mode 2 만 남고 Mode 1 은 `codebase-wiki` 로 나간다. 둘은 코드 import ·
자식 프로세스 · 시험 어느 층에서도 서로를 부르지 않는다. 경계는 데이터 계약이다 — 스키마 리소스
`contracts/mode1-artifacts.v1.json` 의 같은 사본 둘과, Mode 1 이 대상 저장소 `docs/codegraph/` 에 내는 봉인.

**사용 규칙.**
- Mode 1 은 사람이 부를 때만 돈다. 무엇도 대신 돌리지 않는다. **묻지도 않는다** — 예상 비용을 한 줄 찍고 돈다. 증분으로 불렸는데 전량이 되면 그 사실을 굵게 알린다.
- Mode 1 은 바뀐 소스를 다시 읽어야만 봉인한다 — 지난 전수조사의 지문과 지금 소스가 같아야 한다.
- 사람이 고친 위키 장은 `docs/wiki/.bak/` 에 남기고 덮는다.
- 실패한 실행은 봉인하지 않되 이전 봉인에 "뒤 실행 실패" 표식을 남긴다. 1.5·2 는 그것을 경고로 본다.
- Mode 1.5 는 봉인이 없으면 돌지 않는다. 봉인 뒤 소스가 바뀌었으면 경고하고 있는 자료로 돈다 — 그 경고는 `term-candidates.json` 까지 간다.
- Mode 2 는 Mode 1 과 독립이다. 봉인이 있으면 에이전트의 근거로 쓰고, 없어도 돈다. `report-spec init` 과 `run_mode2.py` 가 봉인 상태를 한 줄로 보인다 — 깨진 봉인도 막지 않는다.
- 미커밋 봉인은 경고다. 봉인 파일은 사람이 커밋한다.

**같이 정한 것 — 리소스와 코드를 가른다(최우선).** 프롬프트는 단계당 한 파일, 파일 템플릿은 `**/templates/*`,
설정값은 `config/*.toml`. 파이썬은 읽기만 한다. report-builder 의 계약 형은 계약 JSON 에서 생성한다.

**고르지 않은 것.** 도구 실행면(CLI · 설치형 스킬)에 기대는 안, 코드 인터페이스(Protocol · 발행 패키지)에 기대는 안,
report-spec init 이 Mode 1 을 대신 돌리는 안(재질의에서 "Mode 1 은 사람이 부를 때만" 으로 정리됐다).

**대가로 받아들인 것.** 공통 커널과 봉인 계산(`source_files` · `blob_ids`)을 양쪽에 복제한다. 표류를 막는 자동 검사는
두지 않는다. 계약 파일만은 지문(`.sha256`)으로 양쪽이 같은지를 각자의 시험이 본다. 형 생성기는 구현자 1 · 소비자 1
이지만 사용자가 거울 함정 경계를 알고 골랐다.

**되살릴 조건.** 복제한 커널이 세 번 이상 어긋나 사고를 내면 셋째 저장소(패키지)를 다시 검토한다.

계획서: `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`
```
색인에: `| [0011](0011-split-mode1-and-report.md) | Mode 1 / Mode 1.5+2 두 저장소 · 데이터 계약 경계 | 확정 | Mode 1 은 사람이 부를 때만 · 1.5 는 봉인 필수 · 2 는 독립 · 리소스와 코드 분리 |`

- [ ] **Step 2:**
```bash
git add docs/decisions/0011-split-mode1-and-report.md docs/decisions/README.md
git commit -m "[docs] : 결정 0011 - 두 저장소 분리, 데이터 계약, mode 사이 실행 규칙"
```

#### Task A2: Mode 2 시험이 `run_mode1` 을 import 하지 않게 한다

**Files:** Modify `runner/test_run_mode1_5.py:23` · `runner/test_run_mode2.py:20` · `runner/run_mode1_5.py:6,9` · `runner/run_mode2.py:6,9`

- [ ] **Step 1:** 두 시험의 `import run_mode1 as M  # noqa: E402` → `import measure as M  # noqa: E402`(쓰는 이름은 전부 `measure` 가 정본 🔵 `run_mode2.py:71-77`). 두 실행기의 `# 쓰는 것: run_mode1 · 쓰이는 곳: 없음` → `# 쓰는 것: measure, pipeline · 쓰이는 곳: 없음`, 독스트링 "재는 코드는 `run_mode1.py` 의 것을" → "`measure.py` 의 것을".
- [ ] **Step 2:**
```bash
.venv/bin/python -m pytest runner/test_run_mode1_5.py runner/test_run_mode2.py -q
grep -rn 'run_mode1\b' runner/run_mode1_5.py runner/run_mode2.py runner/run_grade.py runner/term/ runner/test_run_mode1_5.py runner/test_run_mode2.py runner/test_run_grade.py viz/ test/ tools/
git add runner/test_run_mode1_5.py runner/test_run_mode2.py runner/run_mode1_5.py runner/run_mode2.py
git commit -m "[test] : mode 1.5 와 2 시험이 run_mode1 대신 measure 를 import 한다"
```
Expected: 실패 0 · `grep` 출력 없음.

#### Task A3: 세 실행기를 한 번에 보는 시험을 셋으로

**Files:** Modify `runner/test_run_mode1.py:693-717` · `runner/test_run_mode1_5.py`(끝) · `runner/test_run_mode2.py`(끝)

- [ ] **Step 1:** `runner/test_run_mode1_5.py` 끝에:
```python
def test_term_script_paths_actually_exist() -> None:
    """Mode 1.5 가 부르는 얼갈이 스크립트가 디스크에 실재하는가. 문자열 대조는 디렉토리 개편을 못 잡는다."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("collect.py", "emit.py", "quiz.py"):
        p = R._term_script(root, name)  # pyright: ignore[reportPrivateUsage]
        assert os.path.isfile(p), f"Mode 1.5 가 없는 파일을 가리킨다: {p}"
```
`runner/test_run_mode2.py` 끝에:
```python
def test_viz_script_paths_actually_exist() -> None:
    """Mode 2 가 부르는 viz 스크립트 셋이 디스크에 실재하는가."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for stage in ("init", "build", "check"):
        p = R.script_argv(root, stage, "슬러그")[1]
        assert os.path.isfile(p), f"Mode 2 가 없는 파일을 가리킨다: {p}"
```
- [ ] **Step 2:** `runner/test_run_mode1.py` 의 `test_every_runner_script_path_actually_exists` 를:
```python
def test_every_runner_script_path_actually_exists() -> None:
    """Mode 1 이 부르는 얼갈이 스크립트 셋이 **디스크에 실재하는지** 본다.

    문자열만 대조하는 시험은 디렉토리가 개편돼도 초록으로 남는다 — 실제로
    `scripts/` 가 `runner/`·`viz/` 로 갈린 뒤에도 실행기가 옛 경로를 가리킨 채
    시험이 통과하고 있었다. 여기서는 파일 존재를 본다.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for script in ("prep.py", "build.py", "check.py"):
        p = R.wiki_argv(sys.executable, root, script, "/대상")[1]
        assert os.path.isfile(p), f"Mode 1 이 없는 파일을 가리킨다: {p}"
```
- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest runner/ -q
git add runner/test_run_mode1.py runner/test_run_mode1_5.py runner/test_run_mode2.py
git commit -m "[test] : 실행기 스크립트 실재 시험을 mode 별로 가른다"
```

#### Task A4: 전수조사 레코드를 두 몫으로 가르는 스크립트

**Files:** Create `$TOOLS_ROOT/split-work/split_reading.py` (저장소 밖)

- [ ] **Step 1**

```python
#!/usr/bin/env python3
"""terms-reading.json 을 두 저장소 몫으로 가른다 — `split_reading.py <원본> <mode1 출력> <mode2 출력>`.

판정은 `where` 의 경로 접두사다. 디렉토리는 `/` 로 끝나는 접두사, 파일은 글자 그대로.
FIRST(report-builder 몫인 machine/ 파일) → MODE1 → MODE2 → DROP 순으로 보고, 어디에도 없으면 공통 커널로
보아 둘 다 받는다. 반대편으로 건너가는 `uses[].to` 는 끊고 센다.
"""
import collections
import json
import sys

FIRST = ("machine/evidence.py", "machine/test_evidence.py", "machine/contract_types.py",
         "tools/gen_contract_types.py", "tools/test_gen_contract_types.py")
MODE1 = ("machine/", "runner/mode1/", "runner/wiki/", "runner/run_mode1.py", "runner/check_shard.py",
         "runner/test_mode1.py", "runner/test_run_mode1.py", "viz/render_classes.py",
         "viz/render_modules.py", "viz/demermaid.py", "viz/templates/dot/", "test/test_wiki.py",
         "bin/report-wiki", "config/mode1.toml", "tools/gen_contract.py", "tools/test_gen_contract.py",
         "evals/", "resources/")
MODE2 = ("runner/run_mode1_5.py", "runner/run_mode2.py", "runner/run_grade.py", "runner/term/",
         "runner/prompts/", "runner/test_run_mode1_5.py", "runner/test_run_mode2.py", "runner/test_run_grade.py",
         "viz/", "bin/report", "bin/report-spec", "bin/report-term", "tsconfig.json", "config/report.toml",
         "test/test_check.py", "test/test_components.py", "test/test_graph_math.py", "test/test_config.py",
         "test/test_init.py", "test/test_link_paths.py", "test/test_term.py",
         "test/test_wrap_terms.py", "test/svg.test.mjs", ".gemini/ReactRule.md")
DROP = ("runner/test_import_isolation.py",)


def hit(path: str, rules: tuple[str, ...]) -> bool:
    return any(path == r or (r.endswith("/") and path.startswith(r)) for r in rules)


def side(where: str) -> set[str]:
    path = where.split(":")[0]
    if hit(path, FIRST):
        return {"mode2"}
    if hit(path, MODE1):
        return {"mode1"}
    if hit(path, MODE2):
        return {"mode2"}
    if hit(path, DROP):
        return set()
    return {"mode1", "mode2"}


def main(src: str, out1: str, out2: str) -> int:
    with open(src, encoding="utf-8") as f:
        db = json.load(f)
    sides = {k: side(r["where"]) for k, r in db.items()}
    out: dict[str, dict[str, object]] = {"mode1": {}, "mode2": {}}
    cut: collections.Counter[str] = collections.Counter()
    for key, rec in db.items():
        for s in sides[key]:
            copy = dict(rec)
            kept = [u for u in rec.get("uses", []) if u["to"] in db and s in sides[u["to"]]]
            cut[s] += len(rec.get("uses", [])) - len(kept)
            copy["uses"] = kept
            out[s][key] = copy
    for s, path in (("mode1", out1), ("mode2", out2)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out[s], f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"{s}: 레코드 {len(out[s])} · 끊은 uses {cut[s]} → {path}")
    print(f"둘 다 받은 레코드 {sum(1 for v in sides.values() if len(v) == 2)} · "
          f"버린 레코드 {sum(1 for v in sides.values() if not v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
```
- [ ] **Step 2:**
```bash
.venv/bin/python "$TOOLS_ROOT/split-work/split_reading.py" machine/terms-reading.json \
  "$TOOLS_ROOT/split-work/reading-mode1.json" "$TOOLS_ROOT/split-work/reading-mode2.json"
```
Expected: **mode1 + mode2 − 둘 다 받은 수 + 버린 수 = 1,318**. 🟡 어림 mode1 ≈ 960 · mode2 ≈ 500, ±20 은 정상. 커밋 없음.

### Phase K — 계약 A3 (단일 저장소에서 생산자와 소비자를 함께 세운다)

#### Task K1: 생산자 — 봉인 `machine/manifest.py` (U2 · U3 · U8)

**Files:** Create `machine/manifest.py` · `machine/test_manifest.py`

- [ ] **Step 1: 실패하는 시험** — `machine/test_manifest.py`:

```python
import hashlib
import json
import os
import subprocess
import sys

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest as MF  # noqa: E402
import warmup  # noqa: E402


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def entry(path: str) -> warmup.Entry:
    return {"mtime": 0.0, "size": 0, "seen": 0.0, "file_hash": warmup.file_hash(path), "decl_hash": None}


def make_repo(tmp_path) -> str:
    """조사가 끝난 직후의 대상 저장소 — 지문과 위키 상태가 지금 소스와 맞는다."""
    r = tmp_path / "대상"
    (r / "pkg").mkdir(parents=True)
    (r / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (r / "docs" / "wiki").mkdir(parents=True)
    (r / "docs" / "wiki" / "index.md").write_text("# 위키 pkg/a.py:1\n", encoding="utf-8")
    raw = r / "out" / "codegraph-raw"
    raw.mkdir(parents=True)
    (raw / "terms-db.json").write_text("{}", encoding="utf-8")
    (raw / "lang-select.json").write_text(json.dumps({"language": "py"}), encoding="utf-8")
    (r / ".gitignore").write_text("out/\n", encoding="utf-8")
    repo = str(r)
    warmup.save(str(raw / "snapshot.json"), {"pkg/a.py": entry(str(r / "pkg" / "a.py"))})
    with open(raw / "snapshot.json", "rb") as f:
        (raw / "wiki-state.json").write_text(
            json.dumps({"snapshot_sha256": hashlib.sha256(f.read()).hexdigest()}), encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def seal(repo: str, kinds: str = "terms-db,wiki") -> int:
    return MF.main(["seal", repo, "--kinds", kinds, "--producer-commit", "abc"])


def test_source_files_는_확장자와_건너뛸_폴더로_거르고_새_파일도_넣는다(tmp_path):
    repo = make_repo(tmp_path)
    (tmp_path / "대상" / "pkg" / "b.py").write_text("y = 2\n", encoding="utf-8")
    assert MF.source_files(repo, [".py"], ["docs", "out"]) == ["pkg/a.py", "pkg/b.py"]


def test_blob_ids_는_git_hash_object_와_같다(tmp_path):
    repo = make_repo(tmp_path)
    want = subprocess.run(["git", "-C", repo, "hash-object", "pkg/a.py"],
                          capture_output=True, text=True).stdout.strip()
    assert MF.blob_ids(repo, ["pkg/a.py"]) == {"pkg/a.py": want}


def test_seal_은_docs_codegraph_에_계약_꼴로_낸다(tmp_path):
    repo = make_repo(tmp_path)
    assert seal(repo) == 0
    with open(os.path.join(repo, "docs", "codegraph", "manifest.json"), "rb") as f:
        doc = msgspec.json.decode(f.read(), type=MF.ArtifactManifest)
    assert (doc["contract"], doc["version"]) == ("mode1-artifacts", 1)
    assert "superseded_by" not in doc                      # 성공 봉인은 실패 표식을 지운다
    assert [e["path"] for e in doc["artifacts"]["terms-db"]] == ["docs/codegraph/terms-db.json"]
    assert [e["path"] for e in doc["artifacts"]["wiki"]] == ["docs/wiki/index.md"]
    assert os.path.isfile(os.path.join(repo, "docs", "codegraph", "terms-db.json"))
    assert list(doc["inputs"]) == ["pkg/a.py"]


def test_seal_은_다시_읽지_않은_소스를_봉인하지_않는다(tmp_path):
    repo = make_repo(tmp_path)
    open(os.path.join(repo, "pkg", "a.py"), "a", encoding="utf-8").write("# 바꿈\n")
    assert seal(repo, "terms-db") == 3
    assert not os.path.exists(os.path.join(repo, "docs", "codegraph", "manifest.json"))


def test_seal_은_조사되지_않은_새_파일도_거부한다(tmp_path):
    repo = make_repo(tmp_path)
    open(os.path.join(repo, "pkg", "b.py"), "w", encoding="utf-8").write("y = 2\n")
    assert seal(repo, "terms-db") == 3


def test_seal_은_지문을_따라잡지_못한_위키를_거부한다(tmp_path):
    repo = make_repo(tmp_path)
    open(os.path.join(repo, "out", "codegraph-raw", "wiki-state.json"), "w", encoding="utf-8").write(
        json.dumps({"snapshot_sha256": "옛것"}))
    assert seal(repo, "wiki") == 3
    assert seal(repo, "terms-db") == 0


def test_seal_은_모르는_종류와_빈_종류를_거부한다(tmp_path):
    repo = make_repo(tmp_path)
    assert seal(repo, "foo") == 2
    assert seal(repo, "") == 2
```
Run: `.venv/bin/python -m pytest machine/test_manifest.py -q` → Expected: `ModuleNotFoundError: No module named 'manifest'`. (`warmup.save` 와 `warmup.Entry` 칸은 🔵 `machine/warmup.py:48-54,117`.)

- [ ] **Step 2: 구현** — `machine/manifest.py`:

```python
#!/usr/bin/env python3
"""Mode 1 산출물을 봉인한다 — `docs/codegraph/` 에 terms-db.json 사본과 manifest.json 을 낸다.

봉인은 그 실행에서 **검사기를 통과한** 산출물만 싣고, 그것이 **지금 소스를 다시 읽은 결과**일 때만 싣는다.
- terms-db : 소스 파일마다의 지문이 지난 전수조사의 지문(`out/codegraph-raw/snapshot.json`)과 같아야 한다
- wiki     : `write-wiki` 가 그 지문을 따라잡았다는 표(`out/codegraph-raw/wiki-state.json`)가 있어야 한다
읽는 쪽(report-builder 의 `machine/evidence.py`)은 매니페스트 하나로 꼴과 신선도를 판정한다. 소스를 모으는
규칙(확장자 · 건너뛸 폴더)도 같이 적어, 읽는 쪽이 Mode 1 을 몰라도 같은 규칙을 다시 돌리게 한다.

    python machine/manifest.py seal <repo> --kinds terms-db,wiki --producer-commit <sha>
    exit 0 봉인 · 1 언어 모름 · 2 종류 틀림 · 3 다시 읽지 않은 것이 있다
"""
import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import NotRequired, TypedDict

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402
import warmup  # noqa: E402

CONTRACT = "mode1-artifacts"
VERSION = 1
KINDS = ("terms-db", "wiki")
PUBLISH = os.path.join("docs", "codegraph")


class ArtifactEntry(TypedDict):
    """봉인된 산출물 파일 하나. `path` 는 대상 저장소 뿌리 기준."""
    path: str
    sha256: str


class SupersededBy(TypedDict):
    """이 봉인 뒤의 Mode 1 실행이 실패했다는 표식. 봉인 자체는 그대로다 — 읽는 쪽이 경고로 본다."""
    stage: str
    at: str
    producer_commit: str


class ArtifactManifest(TypedDict):
    """`docs/codegraph/manifest.json` 의 꼴. `inputs` 는 봉인 시점 소스 파일마다의 git blob id 다."""
    contract: str
    version: int
    producer_commit: str
    source_commit: str
    source_exts: list[str]
    skip_dirs: list[str]
    artifacts: dict[str, list[ArtifactEntry]]
    inputs: dict[str, str]
    superseded_by: NotRequired[SupersededBy]


class LangPick(TypedDict):
    language: str | None


class WikiState(TypedDict):
    """`write-wiki` 가 따라잡은 지문(`snapshot.json` 바이트의 sha256)과 그때 쓴 장마다의 해시."""
    snapshot_sha256: str
    pages: NotRequired[dict[str, str]]


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def sha256_of(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def source_files(repo: str, exts: Sequence[str], skip: Sequence[str]) -> list[str]:
    """추적 파일과 무시되지 않은 새 파일 중 확장자가 맞고 건너뛸 폴더 밖에 있는 것. 정렬해 낸다."""
    out: set[str] = set()
    for rel in git(repo, "ls-files", "-co", "--exclude-standard").splitlines():
        parts = rel.split("/")
        if rel.endswith(tuple(exts)) and not any(p in skip for p in parts[:-1]) \
                and os.path.isfile(os.path.join(repo, rel)):
            out.add(rel)
    return sorted(out)


def blob_ids(repo: str, rels: Sequence[str]) -> dict[str, str]:
    """작업 트리 내용 그대로의 blob id. `git hash-object` 는 인자 순서대로 한 줄씩 낸다."""
    got: dict[str, str] = {}
    for i in range(0, len(rels), 500):
        chunk = list(rels[i:i + 500])
        got.update(zip(chunk, git(repo, "hash-object", "--", *chunk).split()))
    return got


def unsurveyed(repo: str, sources: Sequence[str], snapshot: str) -> list[str]:
    """지난 전수조사의 지문과 다른 소스. 지문에 없는 새 파일도 넣는다."""
    snap = warmup.load(snapshot)
    out: list[str] = []
    for rel in sources:
        e = snap.get(rel)
        if e is None or e.get("file_hash") != warmup.file_hash(os.path.join(repo, rel)):
            out.append(rel)
    return out


def wiki_caught_up(raw: str) -> bool:
    try:
        with open(os.path.join(raw, "wiki-state.json"), "rb") as f:
            state = msgspec.json.decode(f.read(), type=WikiState)
    except (OSError, msgspec.DecodeError):
        return False
    return state["snapshot_sha256"] == sha256_of(os.path.join(raw, "snapshot.json"))


def entries(repo: str, kind: str) -> list[ArtifactEntry]:
    if kind == "terms-db":
        rels = [os.path.join(PUBLISH, "terms-db.json")]
    else:
        rels = sorted(os.path.relpath(p, repo) for p in glob.glob(os.path.join(repo, "docs", "wiki", "*.md")))
    return [{"path": r, "sha256": sha256_of(os.path.join(repo, r))} for r in rels]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mode 1 산출물 봉인")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("repo")
    s.add_argument("--kinds", required=True, help="쉼표로. 이번 실행에서 검사를 통과한 것 — terms-db, wiki")
    s.add_argument("--producer-commit", required=True)
    a = ap.parse_args(argv)
    repo = os.path.abspath(str(a.repo))
    kinds = [k for k in str(a.kinds).split(",") if k]
    if not kinds or any(k not in KINDS for k in kinds):
        print("에러 — 봉인할 종류가 틀렸다: %r (있는 것: %s)" % (a.kinds, ", ".join(KINDS)), file=sys.stderr)
        return 2
    raw = os.path.join(repo, "out", "codegraph-raw")
    with open(os.path.join(raw, "lang-select.json"), "rb") as f:
        language = msgspec.json.decode(f.read(), type=LangPick)["language"]
    if language not in declmap.LANGS:
        print("에러 — 언어를 모른다: %r. lang-decide 가 먼저 돌아야 한다" % language, file=sys.stderr)
        return 1
    exts = list(declmap.LANGS[language]["exts"])
    skip = sorted(set(declmap.SKIP_DIRS) | {"out", "docs"})
    sources = source_files(repo, exts, skip)
    if "terms-db" in kinds:
        stale = unsurveyed(repo, sources, os.path.join(raw, "snapshot.json"))
        if stale:
            print("봉인하지 않는다 — 지난 전수조사 뒤 바뀐 소스 %d개. Mode 1 을 증분으로 다시 돌린다:" % len(stale),
                  file=sys.stderr)
            for rel in stale[:20]:
                print("  " + rel, file=sys.stderr)
            return 3
    if "wiki" in kinds and not wiki_caught_up(raw):
        print("봉인하지 않는다 — write-wiki 가 지난 전수조사를 따라잡지 못했다", file=sys.stderr)
        return 3
    os.makedirs(os.path.join(repo, PUBLISH), exist_ok=True)
    if "terms-db" in kinds:
        shutil.copyfile(os.path.join(raw, "terms-db.json"), os.path.join(repo, PUBLISH, "terms-db.json"))
    doc: ArtifactManifest = {
        "contract": CONTRACT, "version": VERSION, "producer_commit": str(a.producer_commit),
        "source_commit": git(repo, "rev-parse", "HEAD").strip(),
        "source_exts": exts, "skip_dirs": skip,
        "artifacts": {k: entries(repo, k) for k in kinds},
        "inputs": blob_ids(repo, sources)}
    path = os.path.join(repo, PUBLISH, "manifest.json")
    with open(path, "wb") as f:
        f.write(msgspec.json.format(msgspec.json.encode(doc), indent=2))
    print("%s — 봉인 %s · 소스 %d개 (커밋은 사람이 한다)" % (path, ", ".join(kinds), len(sources)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest machine/test_manifest.py -q && npm run typecheck:py
git add machine/manifest.py machine/test_manifest.py
git commit -m "[update] : machine/manifest - 다시 읽은 산출물만 docs/codegraph 에 봉인"
```
Expected: `7 passed` · `0 errors`.

#### Task K2: 생산자 — 마지막 단계 `seal-artifacts`

**Files:**
- Create: `runner/mode1/seal.py`
- Modify: `runner/mode1/context.py`(`verified` · `MANIFEST`) · `runner/mode1/terms.py` · `runner/mode1/wiki.py`(`VerifyWikiStage`) · `runner/mode1/edges.py` · `runner/run_mode1.py`(독스트링 표) · `runner/CLAUDE.md`
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험** — `runner/test_mode1.py` 끝에(`_ctx` 도우미 🔵 `:213`):

```python
def test_seal_은_검사를_통과한_것만_싣는다(tmp_path) -> None:
    from mode1 import seal as SL
    ctx = _ctx(tmp_path)
    ctx.verified = {"wiki", "terms-db"}
    argv = SL.SealArtifactsStage().argv(ctx)
    assert argv[argv.index("--kinds") + 1] == "terms-db,wiki"


def test_seal_은_통과한_검사가_없으면_실패한다(tmp_path) -> None:
    from mode1 import seal as SL
    out = SL.SealArtifactsStage().perform(_ctx(tmp_path))
    assert out.kind == P.FAIL and "봉인할 것이 없다" in out.why


def test_seal_artifacts_는_그래프의_마지막이다() -> None:
    assert E.ORDER[-1] == "seal-artifacts"


def test_verify_terms_는_통과하면_verified_에_적는다(tmp_path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    monkeypatch.setattr(P.MachineStage, "perform", lambda self, c: P.Outcome(P.OK, "", []))
    assert T.VerifyTermsStage().perform(ctx).kind == P.OK
    assert ctx.verified == {"terms-db"}


def test_mark_superseded_는_이전_봉인에_표식을_적고_없으면_False(tmp_path) -> None:
    from mode1 import seal as SL
    repo = tmp_path / "대상"
    (repo / "docs" / "codegraph").mkdir(parents=True)
    assert SL.SealArtifactsStage.mark_superseded(str(repo), "write-wiki", "abc") is False
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "p", "source_commit": "s",
           "source_exts": [".py"], "skip_dirs": [], "artifacts": {}, "inputs": {}}
    (repo / "docs" / "codegraph" / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    assert SL.SealArtifactsStage.mark_superseded(str(repo), "write-wiki", "abc") is True
    got = json.load(open(repo / "docs" / "codegraph" / "manifest.json", encoding="utf-8"))
    assert got["superseded_by"]["stage"] == "write-wiki" and got["superseded_by"]["producer_commit"] == "abc"
```
(파일 머리에 `import json` 이 없으면 더한다.)
Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "seal or verified"` → Expected: `ModuleNotFoundError: No module named 'mode1.seal'`.

- [ ] **Step 2: 구현**

`runner/mode1/context.py` — `Mode1Context` 칸 끝에 `verified: set[str] = field(default_factory=set)   # 이 실행에서 검사를 통과한 산출물 → seal-artifacts`(`dataclasses.field`). 산출물:
```python
from manifest import ArtifactManifest  # noqa: E402  (machine/ 은 이미 sys.path 에 있다)
MANIFEST = P.Artifact[Mode1Context](
    "manifest.json", lambda c: os.path.join(c.repo, "docs", "codegraph", "manifest.json"), ArtifactManifest)
WIKI_STATE = P.Artifact[Mode1Context](
    "wiki-state.json", lambda c: os.path.join(raw_dir(c), "wiki-state.json"))
```
`ARTIFACTS` 끝에 `MANIFEST, WIKI_STATE`.

`runner/mode1/seal.py`:
```python
"""`seal-artifacts`. 이 실행에서 검사를 통과하고 지금 소스를 다시 읽은 산출물을 docs/codegraph 에 봉인한다."""
import os
import subprocess
import sys
from datetime import datetime, timezone

import msgspec

import pipeline as P
from manifest import ArtifactManifest
from mode1 import context as X
from mode1.context import Mode1Context
from mode1.machine_stage import Mode1Machine


class SealArtifactsStage(Mode1Machine):
    name = "seal-artifacts"

    @staticmethod
    def producer_commit(root: str) -> str:
        """봉인한 도구의 판. git 밖이면 `unknown`."""
        r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else "unknown"

    @staticmethod
    def mark_superseded(repo: str, stage: str, producer_commit: str) -> bool:
        """실패한 실행 뒤 **이전 봉인**에 표식을 적는다. 봉인이 없으면 False. 봉인 자체는 새로 쓰지 않는다."""
        path = os.path.join(repo, "docs", "codegraph", "manifest.json")
        if not os.path.isfile(path):
            return False
        with open(path, "rb") as f:
            doc = msgspec.json.decode(f.read(), type=ArtifactManifest)
        doc["superseded_by"] = {"stage": stage, "producer_commit": producer_commit,
                               "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with open(path, "wb") as f:
            f.write(msgspec.json.format(msgspec.json.encode(doc), indent=2))
        return True

    def argv(self, ctx: Mode1Context) -> list[str]:
        return [sys.executable, os.path.join(ctx.root, "machine", "manifest.py"), "seal", ctx.repo,
                "--kinds", ",".join(sorted(ctx.verified)),
                "--producer-commit", self.producer_commit(ctx.root)]

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.TERMS_DB, X.LANG_SELECT, X.SNAPSHOT]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.MANIFEST]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if not ctx.verified:
            return P.Outcome(P.FAIL, "봉인할 것이 없다 — 이 실행에서 verify-terms 나 verify-wiki 가 통과하지 않았다", [])
        return super().perform(ctx)
```

`runner/mode1/terms.py` 의 `VerifyTermsStage` 와 `runner/mode1/wiki.py` 의 `VerifyWikiStage` 에 각각:
```python
    def perform(self, ctx: Mode1Context) -> P.Outcome:
        out = super().perform(ctx)
        if out.kind == P.OK:
            ctx.verified.add("terms-db")          # VerifyWikiStage 는 "wiki"
        return out
```

`runner/mode1/edges.py` — `from mode1.seal import SealArtifactsStage`, `ORDER` 끝에 `"seal-artifacts"`, `STAGES` 에 `"seal-artifacts": SealArtifactsStage()`. 간선은 기본으로 충분하다.

`runner/run_mode1.py` 독스트링 — "열두 단계" → "열세 단계", 흐름 줄 끝에 `─▶ seal-artifacts`, 표 끝에 `| \`seal-artifacts\` | 기계 | 이 실행에서 검사를 통과하고 다시 읽은 산출물을 \`docs/codegraph/\` 에 봉인 | \`machine/manifest.py\` |`. `runner/CLAUDE.md` 표의 단계 나열도 열셋으로.

`runner/run_mode1.py` `main` — `return 0 if all(r["ok"] or r.get("skipped") for r in rows) else 1` 바로 앞에(U13 — 실패한 실행은 이전 봉인에 표식만 남긴다):
```python
    failed = [r["stage"] for r in rows if not (r["ok"] or r.get("skipped"))]
    if failed and SealArtifactsStage.mark_superseded(ctx.repo, failed[0], SealArtifactsStage.producer_commit(ctx.root)):
        print("이전 봉인에 표식을 적었다 — 이 실행이 %s 에서 실패했다. Mode 1.5·2 는 경고를 보고 옛 자료로 돈다"
              % failed[0], file=sys.stderr)
```
(`from mode1.seal import SealArtifactsStage` 를 import 묶음에.)

- [ ] **Step 3: 시험 · 흐름 · 실물 대조**

```bash
.venv/bin/python -m pytest runner/ machine/test_manifest.py -q && npm run typecheck:py
.venv/bin/python runner/run_mode1.py . --dry-run | tail -n 5
```
Expected: 실패 0 · `GraphError` 없이 `seal-artifacts` 가 끝에 찍힌다.

**지문 범위를 실물로 본다** — `snapshot-sources` 가 찍는 파일 범위가 봉인의 소스 범위와 같은지(다르면 봉인이 늘 거부한다):
```bash
.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "machine")
import declmap, manifest as MF, warmup
src = MF.source_files(".", list(declmap.LANGS["py"]["exts"]), sorted(set(declmap.SKIP_DIRS) | {"out", "docs"}))
snap = warmup.load("out/codegraph-raw/snapshot.json")
missing = [p for p in src if p not in snap]
print("소스", len(src), "· 지문에 없는 소스", len(missing), missing[:10])
EOF
```
Expected: 지문에 없는 소스가 **이번 세션에 새로 만든 파일뿐**(Phase R · K 의 새 `.py`)이다. 폴더째 빠진다면(예: `test/` 전부) `source_files` 의 건너뛸 폴더를 `runner/mode1/scan.py` 의 `SnapshotSourcesStage` 가 쓰는 목록에 맞춘다.

- [ ] **Step 4:**
```bash
git add runner/mode1 runner/run_mode1.py runner/test_mode1.py runner/CLAUDE.md
git commit -m "[update] : mode 1 마지막 단계 seal-artifacts - 검사를 통과한 산출물만 봉인"
```

#### Task K2b: 진입 알림 — 예상 비용과 전량 폴백 (U11)

**Files:**
- Modify: `runner/mode1/graph.py`(`ScheduleBatchesStage`) · `runner/mode1/scan.py`(`DetectChangesStage.perform` · `SnapshotScan.scan_snapshot`)
- Test: `runner/test_mode1.py`

묻지 않는다. 찍기만 한다 — 멈추는 것은 Ctrl-C 다.

- [ ] **Step 1: 실패하는 시험** — `runner/test_mode1.py` 끝에(`G` · `SC` 는 머리에서 이미 import 돼 있다 🔵 `:20,25`):

```python
def test_estimate_line_은_배치_수와_비용_범위를_적는다() -> None:
    cfg = {"usd_per_batch_min": 0.4, "usd_per_batch_max": 1.4}
    assert G.ScheduleBatchesStage.estimate_line(78, cfg, cold=False) == "배치 78개 · 예상 $31~109 · 증분"
    assert G.ScheduleBatchesStage.estimate_line(0, cfg, cold=True) == "배치 0개 · 예상 $0~0 · 전량"


def test_detect_changes_는_지문이_없으면_전량이라고_굵게_알린다(tmp_path, capsys, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    monkeypatch.setattr(SC.SnapshotScan, "scan_snapshot", staticmethod(lambda c: None))
    SC.DetectChangesStage().perform(ctx)
    assert "증분으로 불렸지만 전량이다" in capsys.readouterr().err
```
Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "estimate or 전량이라고"` → Expected: `AttributeError: … 'estimate_line'`.

- [ ] **Step 2: 구현**

`runner/mode1/graph.py` 의 `ScheduleBatchesStage` 에:
```python
    @staticmethod
    def estimate_line(n_batches: int, cfg: X.EstimateConfig, cold: bool) -> str:
        """`배치 N개 · 예상 $lo~hi · 증분|전량`. 범위는 config/mode1.toml 의 [estimate]."""
        lo = round(n_batches * cfg["usd_per_batch_min"])
        hi = round(n_batches * cfg["usd_per_batch_max"])
        return "배치 %d개 · 예상 $%d~%d · %s" % (n_batches, lo, hi, "전량" if cold else "증분")
```
그리고 `perform` 이 OK 로 끝나는 자리 끝에(이미 `perform` 을 재정의하고 있으면 그 끝에):
```python
            plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
            n = sum(len(L.get("batches", [])) for L in plan.get("layers", []))
            print(self.estimate_line(n, X.load_config()["estimate"], ctx.cold) + "  (Ctrl-C 로 멈춤)")
```

`runner/mode1/scan.py` — `DetectChangesStage.perform` 의 알림 `"알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다."` 를 `"⚠ 증분으로 불렸지만 전량이다 — 언어를 몰라 증분 판정을 건너뛴다. 비용은 전량과 같다"` 로. `SnapshotScan.scan_snapshot` 에서 지문 파일(`X.SNAPSHOT.locate(ctx)`)이 없을 때(`warmup.load` 가 빈 사전을 돌려 전 파일이 `재읽기` 가 되는 길) 같은 꼴로 한 줄: `"⚠ 증분으로 불렸지만 전량이다 — 지난 지문(snapshot.json)이 없다"`. 둘 다 stderr. 멈추지 않는다.

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest runner/test_mode1.py -q -k "estimate or 전량이라고" && npm run typecheck:py
git add runner/mode1/graph.py runner/mode1/scan.py runner/test_mode1.py
git commit -m "[update] : mode 1 진입 알림 - 예상 비용 한 줄, 전량 폴백은 굵게. 묻지 않는다"
```

#### Task K3: 생산자 — 바뀐 파일을 인용하는 위키 장만 다시 쓰고, 손댄 장은 .bak 에 남긴다 (U2b · U12)

**Files:**
- Modify: `runner/mode1/context.py`(`wiki_stale` · `wiki_backed_up` 칸) · `runner/mode1/wiki.py`(`WriteWikiStage`) · `runner/wiki/build.py`(`.bak` 제외) · `machine/manifest.py`(`WikiState.pages` — K1 에서 했으면 확인만)
- Test: `runner/test_mode1.py`

- [ ] **Step 1: 실패하는 시험**

```python
def test_stale_pages_는_바뀐_파일을_글자로_인용하는_장이다(tmp_path) -> None:
    wiki = tmp_path / "docs" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "a.md").write_text("근거 `pkg/a.py:3`\n", encoding="utf-8")
    (wiki / "b.md").write_text("근거 `pkg/b.py:1`\n", encoding="utf-8")
    got = W.WriteWikiStage.stale_pages(str(wiki), ["a.md", "b.md", "c.md"], {"pkg/a.py"})
    assert got == {"a.md"}


def test_write_wiki_는_끝나면_지문을_따라잡았다고_적는다(tmp_path, monkeypatch) -> None:
    import hashlib
    ctx = _ctx(tmp_path)
    snap = X.SNAPSHOT.locate(ctx)
    os.makedirs(os.path.dirname(snap), exist_ok=True)
    open(snap, "w", encoding="utf-8").write('{"files": {}}')
    monkeypatch.setattr(P.LlmStage, "perform", lambda self, c: P.Outcome(P.OK, "", []))
    monkeypatch.setattr(W.WriteWikiStage, "prepare", lambda self, c: None)
    ctx.plan = cast(Any, {"layers": []})
    assert W.WriteWikiStage().perform(ctx).kind == P.OK
    state = json.load(open(X.WIKI_STATE.locate(ctx), encoding="utf-8"))
    assert state["snapshot_sha256"] == hashlib.sha256(open(snap, "rb").read()).hexdigest()
    assert "pages" in state


def test_edited_pages_는_적어_둔_해시와_다른_장이다(tmp_path) -> None:
    import hashlib
    wiki = tmp_path / "docs" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "a.md").write_text("원본\n", encoding="utf-8")
    (wiki / "b.md").write_text("원본\n", encoding="utf-8")
    h = hashlib.sha256("원본\n".encode()).hexdigest()
    (wiki / "a.md").write_text("사람이 고침\n", encoding="utf-8")
    assert W.WriteWikiStage.edited_pages(str(wiki), ["a.md", "b.md", "c.md"], {"a.md": h, "b.md": h}) == {"a.md"}


def test_back_up_edited_는_bak_로_옮기고_목록을_돌려준다(tmp_path) -> None:
    wiki = tmp_path / "docs" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "a.md").write_text("사람이 고침\n", encoding="utf-8")
    assert W.WriteWikiStage.back_up_edited(str(wiki), {"a.md"}) == ["a.md"]
    assert not (wiki / "a.md").exists()
    assert (wiki / ".bak" / "a.md").read_text(encoding="utf-8") == "사람이 고침\n"
```
(파일 머리에 `json` · `cast` 가 없으면 import 한다. `Any` 는 시험 파일이라 `test_no_any` 대상이 아니다.)

Run: `.venv/bin/python -m pytest runner/test_mode1.py -q -k "stale_pages or 따라잡"` → Expected: `AttributeError: … 'stale_pages'`.

- [ ] **Step 2: 구현**

`runner/mode1/context.py` — `Mode1Context` 에 두 칸: `wiki_stale: set[str] = field(default_factory=set)   # 증분에서 다시 쓸 장` · `wiki_backed_up: list[str] = field(default_factory=list)   # 손으로 고쳐서 .bak 에 남긴 장`.

`runner/mode1/wiki.py` 의 `WriteWikiStage` 에(머리에 `import glob` · `import hashlib` · `import json` · `import shutil` · `import msgspec` · `from mode1 import diff as D` · `from mode1.scan import DetectChangesStage` · `from manifest import WikiState`):
```python
    @staticmethod
    def page_hash(path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    @staticmethod
    def stale_pages(wiki_dir: str, pages: Iterable[str], changed: set[str]) -> set[str]:
        """이미 쓴 장 중 바뀐 파일의 경로를 글자 그대로 담은 것. 그 장은 다시 쓴다."""
        out: set[str] = set()
        for name in pages:
            path = os.path.join(wiki_dir, name)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                if any(c in text for c in changed):
                    out.add(name)
        return out

    @staticmethod
    def edited_pages(wiki_dir: str, pages: Iterable[str], recorded: Mapping[str, str]) -> set[str]:
        """지난 write-wiki 가 적어 둔 해시와 지금 해시가 다른 장 — 사람이 고친 것이다."""
        out: set[str] = set()
        for name in pages:
            path = os.path.join(wiki_dir, name)
            if name in recorded and os.path.exists(path) and WriteWikiStage.page_hash(path) != recorded[name]:
                out.add(name)
        return out

    @staticmethod
    def back_up_edited(wiki_dir: str, edited: Iterable[str]) -> list[str]:
        """손댄 장을 `docs/wiki/.bak/<장>` 으로 옮긴다. 옮긴 뒤에는 없는 장이라 `jobs` 가 다시 쓴다."""
        moved: list[str] = []
        bak = os.path.join(wiki_dir, ".bak")
        for name in sorted(edited):
            os.makedirs(bak, exist_ok=True)
            shutil.move(os.path.join(wiki_dir, name), os.path.join(bak, name))
            moved.append(name)
        return moved

    @staticmethod
    def read_state(path: str) -> WikiState | None:
        """지난 write-wiki 의 상태. 없거나 꼴이 틀리면 None — 그러면 손댐을 판정하지 않는다."""
        try:
            return P.load(path, WikiState)
        except (OSError, msgspec.DecodeError):
            return None
```
`prepare` 끝에:
```python
        wiki_dir = os.path.join(ctx.repo, "docs", "wiki")
        d = D.read_diff(X.CHANGES.locate(ctx)) if not ctx.cold else None
        changed = set(DetectChangesStage.changed_seed(d["verdicts"])) | set(d["verdicts"].get("삭제됨", [])) if d else set()
        ctx.wiki_stale = self.stale_pages(wiki_dir, [pg["file"] for pg in ctx.wiki_pages], changed)
        state = self.read_state(X.WIKI_STATE.locate(ctx))
        recorded = state.get("pages", {}) if state else {}
        ctx.wiki_backed_up = self.back_up_edited(wiki_dir, self.edited_pages(wiki_dir, ctx.wiki_stale, recorded))
```
(`ctx.cold` 는 🔵 `runner/mode1/edges.py:41` · `run_mode1.py:228` 에 이미 있다.)
`jobs` 의 거름 조건을:
```python
        here = [pg for pg in ctx.wiki_pages if ctx.wiki_level_of[pg["file"]] == k
                and (pg["file"] in ctx.wiki_stale
                     or not os.path.exists(os.path.join(ctx.repo, "docs", "wiki", pg["file"])))]
```
`perform` 을:
```python
    def perform(self, ctx: Mode1Context) -> P.Outcome:
        if ctx.plan is None:
            ctx.plan = P.load(X.BATCHES.locate(ctx), survey_plan.SurveyPlan)
        self.prepare(ctx)
        out = super().perform(ctx)
        if out.kind == P.OK and os.path.exists(X.SNAPSHOT.locate(ctx)):
            wiki_dir = os.path.join(ctx.repo, "docs", "wiki")
            pages = {os.path.basename(p): self.page_hash(p) for p in glob.glob(os.path.join(wiki_dir, "*.md"))}
            with open(X.WIKI_STATE.locate(ctx), "w", encoding="utf-8") as f:
                json.dump({"snapshot_sha256": self.page_hash(X.SNAPSHOT.locate(ctx)), "pages": pages}, f, indent=1)
        if ctx.wiki_backed_up:
            print("손으로 고친 장 %d개를 덮었다 — 원본은 docs/wiki/.bak/ 에 있다:" % len(ctx.wiki_backed_up))
            for name in ctx.wiki_backed_up:
                print("  " + name)
        return out
```
클래스 독스트링 "이미 쓴 장은 건너뛴다" → "이미 쓴 장은 건너뛰고, 증분에서는 바뀐 파일을 인용하는 장만 다시 쓴다. 사람이 고친 장은 .bak 에 남기고 덮는다".

`runner/wiki/build.py` — 위키를 `.tmp/wiki/<저장소>/` 로 복사하는 자리(🔵 `:78-85` 근처)에서 `.bak` 을 뺀다: `shutil.copytree(src, stage, ignore=shutil.ignore_patterns(".bak"))` 꼴(파일 순회면 `.bak` 폴더를 건너뛴다). `machine/verify_citations.py` 가 `docs/wiki` 를 재귀로 모으면 거기서도 `.bak` 을 뺀다 — 최상위 `*.md` 만 보면 손댈 것 없다(실행 때 확인). 봉인(`manifest.entries`)과 `evidence.py` 의 "봉인 뒤 생긴 장" 은 최상위 `*.md` 만 본다 🔵.

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest runner/ -q && npm run typecheck:py
git add runner/mode1/context.py runner/mode1/wiki.py runner/wiki/build.py machine/manifest.py runner/test_mode1.py
git commit -m "[update] : write-wiki 가 증분에서 바뀐 파일을 인용하는 장만 다시 쓰고, 손댄 장은 .bak 에 남긴다"
```

#### Task K4: 생산자 — 계약 리소스 `tools/gen_contract.py`

**Files:** Create `tools/gen_contract.py` · `tools/test_gen_contract.py` · `contracts/mode1-artifacts.v1.json` · `.sha256`

- [ ] **Step 1: 실패하는 시험** — `tools/test_gen_contract.py`:

```python
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_contract as G  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_계약_파일이_형과_같다():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_contract.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_strip_names_는_스키마의_title_description_만_뗀다():
    got = G.strip_names({"title": "A", "description": "d", "type": "object",
                         "properties": {"title": {"type": "string", "description": "칸"}}})
    assert got == {"type": "object", "properties": {"title": {"type": "string"}}}
```
Run: `.venv/bin/python -m pytest tools/test_gen_contract.py -q` → Expected: `ModuleNotFoundError`.

- [ ] **Step 2: 구현** — `tools/gen_contract.py`:

```python
#!/usr/bin/env python3
"""계약 리소스 `contracts/mode1-artifacts.v1.json` 과 지문 `.sha256` 을 Mode 1 의 형에서 낸다.

두 저장소에 같은 사본으로 산다. report-builder 는 이 파일에서 자기 형을 생성한다(`tools/gen_contract_types.py`).
`title` · `description`(클래스 이름 · 독스트링)은 뗀다. `types` 가 파일마다의 최상위 형 이름을 알려 준다.

    python tools/gen_contract.py            # 쓴다
    python tools/gen_contract.py --check    # 낡았으면 exit 1
"""
import argparse
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from typing import cast

import msgspec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "machine"))
import manifest as MF  # noqa: E402
import terms_db  # noqa: E402

JSON_PATH = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")
SHA_PATH = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.sha256")


def strip_names(node: object) -> object:
    """스키마 객체에서 `title` · `description` 을 뗀다. `properties` · `$defs` 안의 칸 이름은 남긴다."""
    if isinstance(node, list):
        return [strip_names(v) for v in cast(list[object], node)]
    if not isinstance(node, dict):
        return node
    out: dict[str, object] = {}
    for k, v in cast(dict[str, object], node).items():
        if k in ("title", "description"):
            continue
        if k in ("properties", "$defs") and isinstance(v, dict):
            out[k] = {name: strip_names(sub) for name, sub in cast(dict[str, object], v).items()}
        else:
            out[k] = strip_names(v)
    return out


def contract_text() -> str:
    doc = {"contract": MF.CONTRACT, "version": MF.VERSION,
           "types": {"terms-db.json": "TermsDb", "manifest.json": "ArtifactManifest"},
           "schemas": {"terms-db.json": strip_names(msgspec.json.schema(terms_db.TermsDb)),
                       "manifest.json": strip_names(msgspec.json.schema(MF.ArtifactManifest))}}
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() + "  " + os.path.basename(JSON_PATH) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="계약 리소스를 형에서 낸다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = contract_text()
    if a.check:
        try:
            with open(JSON_PATH, encoding="utf-8") as f1, open(SHA_PATH, encoding="utf-8") as f2:
                same = f1.read() == text and f2.read() == sha_text(text)
        except OSError:
            same = False
        if not same:
            print("계약 리소스가 형과 다르다 — python tools/gen_contract.py 로 다시 낸다. "
                  "열쇠를 빼거나 뜻을 바꿨다면 v2 로 판을 올린다", file=sys.stderr)
            return 1
        return 0
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    with open(SHA_PATH, "w", encoding="utf-8") as f:
        f.write(sha_text(text))
    print(JSON_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3:**
```bash
.venv/bin/python tools/gen_contract.py
.venv/bin/python -m pytest tools/test_gen_contract.py -q
( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 )
git add tools/gen_contract.py tools/test_gen_contract.py contracts
git commit -m "[update] : 계약 리소스 contracts/mode1-artifacts.v1 - 형에서 생성하고 지문으로 고정"
```
Expected: `2 passed` · `OK`. `$defs` 에 `DbUse` · `TermRecord` · `ArtifactEntry` · `ArtifactManifest`.

#### Task K5: 소비자 — 계약에서 형을 생성한다 (U6)

**Files:** Create `tools/gen_contract_types.py` · `tools/test_gen_contract_types.py` · `machine/contract_types.py`(생성물) · Modify `test/test_no_any.py`

report-builder 몫이다. 분리 전에는 이 저장소에 나란히 놓이고, B1 이 codebase-wiki 이력에서 빼낸다. 💭 구현자 1 · 소비자 1 생성기라 거울 함정 경계다 — 사용자가 알고 골랐다(U6). 생성기는 계약이 실제로 쓰는 꼴만 다루고, 모르는 꼴이면 예외를 낸다.

- [ ] **Step 1: 실패하는 시험** — `tools/test_gen_contract_types.py`:

```python
import importlib
import json
import os
import subprocess
import sys
from typing import cast

import msgspec

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "machine")]
import gen_contract_types as G  # noqa: E402

CONTRACT = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")


def strip_names(node: object) -> object:
    """생산자 `tools/gen_contract.py` 와 같은 규칙 — 칸 이름은 남기고 스키마의 title · description 만 뗀다."""
    if isinstance(node, list):
        return [strip_names(v) for v in cast(list[object], node)]
    if not isinstance(node, dict):
        return node
    out: dict[str, object] = {}
    for k, v in cast(dict[str, object], node).items():
        if k in ("title", "description"):
            continue
        out[k] = ({n: strip_names(s) for n, s in cast(dict[str, object], v).items()}
                  if k in ("properties", "$defs") and isinstance(v, dict) else strip_names(v))
    return out


def test_py_type_은_계약이_쓰는_꼴을_옮긴다():
    assert G.py_type({"anyOf": [{"type": "string"}, {"type": "null"}]}) == "str | None"
    assert G.py_type({"type": "array", "items": {"$ref": "#/$defs/DbUse"}}) == "list[DbUse]"
    assert G.py_type({"type": "object", "additionalProperties": {"type": "string"}}) == "dict[str, str]"


def test_py_type_은_모르는_꼴을_거부한다():
    try:
        G.py_type({"type": "number"})
    except ValueError:
        return
    raise AssertionError("number 를 받아들였다")


def test_생성물이_계약과_같고_형의_스키마가_계약으로_돌아온다():
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen_contract_types.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    T = importlib.import_module("contract_types")
    with open(CONTRACT, encoding="utf-8") as f:
        doc = json.load(f)
    for fname, tname in doc["types"].items():
        assert strip_names(msgspec.json.schema(getattr(T, tname))) == doc["schemas"][fname], fname


def test_계약_리소스가_지문과_같다():
    import hashlib
    with open(CONTRACT, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with open(CONTRACT[:-len(".json")] + ".sha256", encoding="utf-8") as f:
        assert f.read().split()[0] == digest
```
Run: `.venv/bin/python -m pytest tools/test_gen_contract_types.py -q` → Expected: `ModuleNotFoundError: No module named 'gen_contract_types'`.

- [ ] **Step 2: 구현** — `tools/gen_contract_types.py`:

```python
#!/usr/bin/env python3
"""계약 리소스(JSON Schema)에서 소비자 형을 낸다 — 생성물 `machine/contract_types.py`. `--check` 면 낡았을 때 exit 1.

계약 `contracts/mode1-artifacts.v1.json` 은 codebase-wiki 가 형에서 생성해 보낸 사본이다. 여기서 그 스키마를
TypedDict 로 되돌린다 — 소비자 형을 손으로 쓰지 않는다. 다루는 꼴은 계약이 실제로 쓰는 것뿐이다:
object(properties · required) · dict[str, T](additionalProperties) · array · string · integer · boolean · null · anyOf · $ref.
"""
import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from typing import cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")
OUT = os.path.join(ROOT, "machine", "contract_types.py")
SCALARS = {"string": "str", "integer": "int", "boolean": "bool", "null": "None"}

Schema = Mapping[str, object]


def py_type(s: Schema) -> str:
    """스키마 하나를 파이썬 형 표기로. 모르는 꼴이면 ValueError."""
    if "$ref" in s:
        return str(s["$ref"]).rsplit("/", 1)[-1]
    if "anyOf" in s:
        return " | ".join(py_type(cast(Schema, x)) for x in cast(list[object], s["anyOf"]))
    t = s.get("type")
    if isinstance(t, str) and t in SCALARS:
        return SCALARS[t]
    if t == "array":
        return "list[%s]" % py_type(cast(Schema, s["items"]))
    if t == "object" and "additionalProperties" in s and "properties" not in s:
        return "dict[str, %s]" % py_type(cast(Schema, s["additionalProperties"]))
    raise ValueError("이 생성기가 모르는 꼴: %s" % json.dumps(s, ensure_ascii=False))


def refs(node: object) -> set[str]:
    """스키마 안의 `$ref` 가 가리키는 이름 전부."""
    if isinstance(node, dict):
        d = cast(dict[str, object], node)
        here = {str(d["$ref"]).rsplit("/", 1)[-1]} if "$ref" in d else set()
        return here.union(*(refs(v) for v in d.values()))
    if isinstance(node, list):
        return set().union(*(refs(v) for v in cast(list[object], node)))
    return set()


def class_text(name: str, s: Schema) -> str:
    props = cast(Mapping[str, Schema], s.get("properties", {}))
    required = set(cast(list[str], s.get("required", [])))
    lines = ["class %s(TypedDict):" % name]
    for p in sorted(props):
        t = py_type(props[p])
        lines.append("    %s: %s" % (p, t if p in required else "NotRequired[%s]" % t))
    return "\n".join(lines)


def module_text(doc: Mapping[str, object]) -> str:
    defs: dict[str, Schema] = {}
    schemas = cast(Mapping[str, Schema], doc["schemas"])
    for sch in schemas.values():
        defs.update(cast(Mapping[str, Schema], sch.get("$defs", {})))
    order: list[str] = []

    def visit(n: str) -> None:
        if n in order:
            return
        for r in sorted(refs(defs[n]) - {n}):
            visit(r)
        order.append(n)

    for n in sorted(defs):
        visit(n)
    aliases = ["%s = %s" % (tname, py_type(schemas[fname]))
               for fname, tname in sorted(cast(Mapping[str, str], doc["types"]).items())
               if py_type(schemas[fname]) != tname]
    head = ('"""생성물 — tools/gen_contract_types.py 가 contracts/mode1-artifacts.v1.json 에서 낸다. 손대지 마라."""\n'
            "from typing import NotRequired, TypedDict\n\n"
            "CONTRACT = %s\nVERSION = %d\n" % (json.dumps(doc["contract"]), cast(int, doc["version"])))
    return head + "\n\n" + "\n\n\n".join(class_text(n, defs[n]) for n in order) + "\n\n\n" + "\n".join(aliases) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="계약에서 소비자 형을 낸다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    with open(CONTRACT, encoding="utf-8") as f:
        text = module_text(cast(Mapping[str, object], json.load(f)))
    if a.check:
        try:
            with open(OUT, encoding="utf-8") as f:
                same = f.read() == text
        except OSError:
            same = False
        if not same:
            print("machine/contract_types.py 가 계약과 다르다 — python tools/gen_contract_types.py", file=sys.stderr)
            return 1
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 낸다 · 시험 · 타입**

```bash
.venv/bin/python tools/gen_contract_types.py
.venv/bin/python -m pytest tools/test_gen_contract_types.py -q && npm run typecheck:py
```
Expected: `4 passed` · `0 errors`. `machine/contract_types.py` 에 `DbUse` · `TermRecord` · `ArtifactEntry` · `ArtifactManifest` 클래스와 `TermsDb = dict[str, TermRecord]` 한 줄. `test/test_no_any.py` 의 `COVERED` 에 `"machine/contract_types.py",`.

- [ ] **Step 4:**
```bash
git add tools/gen_contract_types.py tools/test_gen_contract_types.py machine/contract_types.py test/test_no_any.py
git commit -m "[update] : 계약 json 에서 소비자 형을 생성한다 - machine/contract_types"
```

#### Task K6: 소비자 — 판정 `machine/evidence.py` 와 `report-term collect` 관문 (U0 · U9 · U13 · U15 · U16)

**Files:**
- Create: `machine/evidence.py` · `machine/test_evidence.py`
- Modify: `runner/term/collect.py` · `runner/run_mode1_5.py:475-483,616,791-792` · `runner/test_run_mode1_5.py:499-503` · `test/test_term.py` · `test/test_no_any.py`

봉인 계산(`git` · `sha256_of` · `source_files` · `blob_ids`)은 `manifest.py` 와 같은 사본이다 — 결정 0011 의 복제. import 하지 않는다.

- [ ] **Step 1: 실패하는 시험** — `machine/test_evidence.py`:

```python
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evidence as E  # noqa: E402

RECORD = {"kind": "function", "module": "pkg", "where": "pkg/a.py:1", "means": "하나를 돌려준다.",
          "uses": [], "neighbors": [], "source": "reading"}


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def sealed(tmp_path, kinds=("terms-db", "wiki")) -> str:
    r = tmp_path / "대상"
    (r / "pkg").mkdir(parents=True)
    (r / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (r / "docs" / "wiki").mkdir(parents=True)
    (r / "docs" / "wiki" / "index.md").write_text("# 위키\n", encoding="utf-8")
    pub = r / "docs" / "codegraph"
    pub.mkdir(parents=True)
    (pub / "terms-db.json").write_text(json.dumps({"f": RECORD}, ensure_ascii=False), encoding="utf-8")
    repo = str(r)
    git(repo, "init", "-q")
    exts, skip = [".py"], ["docs", "out"]
    arts: dict[str, list[dict[str, str]]] = {}
    if "terms-db" in kinds:
        arts["terms-db"] = [{"path": "docs/codegraph/terms-db.json", "sha256": E.sha256_of(str(pub / "terms-db.json"))}]
    if "wiki" in kinds:
        arts["wiki"] = [{"path": "docs/wiki/index.md", "sha256": E.sha256_of(str(r / "docs" / "wiki" / "index.md"))}]
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "abc", "source_commit": "def",
           "source_exts": exts, "skip_dirs": skip, "artifacts": arts,
           "inputs": E.blob_ids(repo, E.source_files(repo, exts, skip))}
    (pub / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")                 # 봉인까지 커밋된 상태가 기본이다
    return repo


def test_봉인이_맞으면_문제도_낡음도_없다(tmp_path):
    repo = sealed(tmp_path)
    assert E.problems(repo, ["terms-db", "wiki"]) == []
    assert E.staleness(repo) == []


def test_봉인이_없으면_문제다(tmp_path):
    repo = sealed(tmp_path)
    os.remove(os.path.join(repo, E.MANIFEST))
    assert "manifest.json 이 없다" in E.problems(repo, ["terms-db"])[0]


def test_계약_판이_다르면_문제다(tmp_path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.MANIFEST)
    doc = json.load(open(p, encoding="utf-8"))
    doc["version"] = 2
    json.dump(doc, open(p, "w", encoding="utf-8"))
    assert "계약이 다르다" in E.problems(repo, ["terms-db"])[0]


def test_필요한_종류가_봉인에_없으면_문제다(tmp_path):
    repo = sealed(tmp_path, kinds=("terms-db",))
    assert E.problems(repo, ["terms-db"]) == []
    assert any("wiki 가 없다" in p for p in E.problems(repo, ["wiki"]))


def test_봉인_뒤_산출물을_고치거나_장을_더하면_문제다(tmp_path):
    repo = sealed(tmp_path)
    open(os.path.join(repo, "docs", "wiki", "index.md"), "a", encoding="utf-8").write("손으로 더함\n")
    open(os.path.join(repo, "docs", "wiki", "new.md"), "w", encoding="utf-8").write("# 새 장\n")
    got = "\n".join(E.problems(repo, ["wiki"]))
    assert "봉인 뒤 바뀌었다 — docs/wiki/index.md" in got and "봉인 뒤 생긴 장 — docs/wiki/new.md" in got


def test_소스가_움직이면_낡음이지_문제가_아니다(tmp_path):
    repo = sealed(tmp_path)
    open(os.path.join(repo, "pkg", "a.py"), "a", encoding="utf-8").write("# 바꿈\n")
    open(os.path.join(repo, "pkg", "b.py"), "w", encoding="utf-8").write("y = 2\n")
    assert E.problems(repo, ["terms-db"]) == []
    got = "\n".join(E.staleness(repo))
    assert "바뀜 pkg/a.py" in got and "생김 pkg/b.py" in got


def test_원고_커밋은_낡음이_아니다(tmp_path):
    repo = sealed(tmp_path)
    os.makedirs(os.path.join(repo, "specs", "x"))
    open(os.path.join(repo, "specs", "x", "data.ts"), "w", encoding="utf-8").write("export {};\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "원고")
    assert E.staleness(repo) == []


def test_terms_db_가_계약_꼴이_아니면_문제다(tmp_path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.TERMS_DB)
    open(p, "w", encoding="utf-8").write(json.dumps({"f": {"kind": "function"}}))
    m = os.path.join(repo, E.MANIFEST)
    doc = json.load(open(m, encoding="utf-8"))
    doc["artifacts"]["terms-db"][0]["sha256"] = E.sha256_of(p)
    json.dump(doc, open(m, "w", encoding="utf-8"))
    assert any("terms-db.json 이 계약 꼴이 아니다" in x for x in E.problems(repo, ["terms-db"]))


def test_main_은_낡음을_경고로만_찍고_목록에_싣는다(tmp_path, capsys):
    repo = sealed(tmp_path)
    open(os.path.join(repo, "pkg", "a.py"), "a", encoding="utf-8").write("# 바꿈\n")
    assert E.main([repo, "--need", "wiki", "--list"]) == 0
    out = capsys.readouterr()
    got = json.loads(out.out)
    assert got["artifacts"] == [os.path.join(repo, "docs", "wiki", "index.md")]
    assert got["stale"] == ["바뀜 pkg/a.py"]
    assert "경고" in out.err


def test_main_은_구조_문제면_1_과_사람이_칠_명령을_낸다(tmp_path, capsys):
    repo = sealed(tmp_path, kinds=("terms-db",))
    assert E.main([repo, "--need", "terms-db,wiki"]) == 1
    assert "run_mode1.py" in capsys.readouterr().err


def test_미커밋_봉인은_경고다(tmp_path):
    repo = sealed(tmp_path)
    with open(os.path.join(repo, E.MANIFEST), "a", encoding="utf-8") as f:
        f.write("\n")                                   # 작업 트리에서만 바뀜 — 커밋 전 상태
    m, _ = E.load_manifest(repo)
    assert m is not None and E.problems(repo, ["terms-db"]) == []
    assert any("커밋되지 않았다" in w for w in E.warnings(repo, m))
    assert "미커밋" in E.status_line(repo, ["terms-db"])


def test_뒤_실행_실패_표식은_경고다(tmp_path):
    repo = sealed(tmp_path)
    p = os.path.join(repo, E.MANIFEST)
    doc = json.load(open(p, encoding="utf-8"))
    doc["superseded_by"] = {"stage": "write-wiki", "at": "2026-10-24T00:00:00+00:00", "producer_commit": "abc"}
    json.dump(doc, open(p, "w", encoding="utf-8"))
    git(repo, "commit", "-qam", "표식")
    assert E.problems(repo, ["terms-db"]) == []
    assert "뒤 실행 실패" in E.status_line(repo, ["terms-db"])


def test_status_는_있음_깨짐_없음을_한_줄로_내고_늘_0이다(tmp_path, capsys):
    repo = sealed(tmp_path)
    assert E.status_line(repo, ["terms-db", "wiki"]) == "Mode 1 봉인 — 있음"
    open(os.path.join(repo, "docs", "wiki", "index.md"), "a", encoding="utf-8").write("x\n")
    assert E.status_line(repo, ["wiki"]).startswith("Mode 1 봉인 — 깨짐: 봉인 뒤 바뀌었다")
    os.remove(os.path.join(repo, E.MANIFEST))
    assert E.main([repo, "--need", "terms-db", "--status"]) == 0
    assert capsys.readouterr().out.strip() == "Mode 1 봉인 — 없음"
```
Run: `.venv/bin/python -m pytest machine/test_evidence.py -q` → Expected: `ModuleNotFoundError: No module named 'evidence'`.

- [ ] **Step 2: 구현** — `machine/evidence.py`:

```python
#!/usr/bin/env python3
"""대상 저장소에 봉인된 Mode 1 산출물이 계약대로 있는지 판정하고, 봉인 뒤 소스가 움직였는지 알린다.

계약은 `contracts/mode1-artifacts.v1.json` 이고 형은 거기서 생성한 `contract_types.py` 다. **구조 문제**
(봉인 없음 · 계약 판 다름 · 종류 없음 · 해시 다름 · 꼴 아님)는 exit 1, **낡음**(봉인 뒤 소스가 바뀜 · 생김 ·
사라짐)은 경고만 하고 exit 0 이다. 무엇도 Mode 1 을 대신 돌리지 않는다 — 찍는 것은 사람이 칠 명령이다.

    python machine/evidence.py <repo> --need terms-db,wiki          # 구조 문제면 exit 1
    python machine/evidence.py <repo> --need wiki --list            # 통과하면 봉인된 경로와 낡음을 JSON 으로
    python machine/evidence.py <repo> --need terms-db,wiki --status # 한 줄 상태. 어느 경우든 exit 0
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence

import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contract_types import CONTRACT, VERSION, ArtifactManifest, TermsDb  # noqa: E402

KINDS = ("terms-db", "wiki")
MANIFEST = os.path.join("docs", "codegraph", "manifest.json")
TERMS_DB = os.path.join("docs", "codegraph", "terms-db.json")
FIX = ("사람이 Mode 1 을 돌린다 — cd $TOOLS_ROOT/codebase-wiki && .venv/bin/python runner/run_mode1.py <이 저장소>"
       " · 끝나면 docs/codegraph/ 를 커밋한다")


# ── 봉인 계산의 사본 — codebase-wiki 의 machine/manifest.py 와 같은 규칙 (결정 0011) ──
def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def sha256_of(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def source_files(repo: str, exts: Sequence[str], skip: Sequence[str]) -> list[str]:
    out: set[str] = set()
    for rel in git(repo, "ls-files", "-co", "--exclude-standard").splitlines():
        parts = rel.split("/")
        if rel.endswith(tuple(exts)) and not any(p in skip for p in parts[:-1]) \
                and os.path.isfile(os.path.join(repo, rel)):
            out.add(rel)
    return sorted(out)


def blob_ids(repo: str, rels: Sequence[str]) -> dict[str, str]:
    got: dict[str, str] = {}
    for i in range(0, len(rels), 500):
        chunk = list(rels[i:i + 500])
        got.update(zip(chunk, git(repo, "hash-object", "--", *chunk).split()))
    return got


# ── 판정 ──────────────────────────────────────────────────────────────────
def load_manifest(repo: str) -> tuple[ArtifactManifest | None, str]:
    path = os.path.join(repo, MANIFEST)
    if not os.path.isfile(path):
        return None, "manifest.json 이 없다 — 이 저장소에 봉인된 Mode 1 산출물이 없다: %s" % path
    try:
        with open(path, "rb") as f:
            return msgspec.json.decode(f.read(), type=ArtifactManifest), ""
    except msgspec.DecodeError as e:
        return None, "manifest.json 이 계약 꼴이 아니다 — %s" % e


def problems(repo: str, need: Sequence[str]) -> list[str]:
    """구조 문제. 비면 봉인을 근거로 쓸 수 있다."""
    m, why = load_manifest(repo)
    if m is None:
        return [why]
    if (m["contract"], m["version"]) != (CONTRACT, VERSION):
        return ["계약이 다르다 — %s v%d (이 저장소가 읽는 것: %s v%d)"
                % (m["contract"], m["version"], CONTRACT, VERSION)]
    out: list[str] = []
    for kind in need:
        entries = m["artifacts"].get(kind)
        if not entries:
            out.append("봉인에 %s 가 없다 — 그 실행에서 검사를 통과하지 못했다" % kind)
            continue
        for e in entries:
            p = os.path.join(repo, e["path"])
            if not os.path.isfile(p):
                out.append("봉인된 파일이 없다 — %s" % e["path"])
            elif sha256_of(p) != e["sha256"]:
                out.append("봉인 뒤 바뀌었다 — %s" % e["path"])
        if kind == "wiki":
            sealed_pages = {e["path"] for e in entries}
            for p in sorted(glob.glob(os.path.join(repo, "docs", "wiki", "*.md"))):
                rel = os.path.relpath(p, repo)
                if rel not in sealed_pages:
                    out.append("봉인 뒤 생긴 장 — %s" % rel)
    if "terms-db" in need and not out:
        try:
            with open(os.path.join(repo, TERMS_DB), "rb") as f:
                msgspec.json.decode(f.read(), type=TermsDb)
        except msgspec.DecodeError as e:
            out.append("terms-db.json 이 계약 꼴이 아니다 — %s" % e)
    return out


def staleness(repo: str) -> list[str]:
    """봉인 뒤 소스의 움직임. 매니페스트에 적힌 규칙으로 다시 모은다 — Mode 1 을 몰라도 된다."""
    m, _ = load_manifest(repo)
    if m is None:
        return []
    now = blob_ids(repo, source_files(repo, m["source_exts"], m["skip_dirs"]))
    before = m["inputs"]
    return (["바뀜 %s" % p for p in sorted(before.keys() & now.keys()) if before[p] != now[p]]
            + ["생김 %s" % p for p in sorted(now.keys() - before.keys())]
            + ["사라짐 %s" % p for p in sorted(before.keys() - now.keys())])


def uncommitted(repo: str) -> list[str]:
    """봉인 파일 중 작업 트리에서 바뀌었거나 추적되지 않은 것. 비면 커밋된 봉인이다."""
    out = git(repo, "status", "--porcelain", "--", MANIFEST, TERMS_DB)
    return sorted(line[3:] for line in out.splitlines() if line.strip())


def warnings(repo: str, m: ArtifactManifest) -> list[str]:
    """낡음 — 멈추지 않는 것들. 소스 움직임 · 미커밋 · 뒤 실행 실패."""
    out = ["소스 " + s for s in staleness(repo)]
    if uncommitted(repo):
        out.append("봉인 파일이 커밋되지 않았다 — 이 기계에만 보인다. 다른 기계와 클라우드는 옛 봉인을 본다")
    sup = m.get("superseded_by")
    if sup:
        out.append("뒤 Mode 1 실행이 %s 에서 실패했다(%s) — 이 봉인은 그 전 것이다" % (sup["stage"], sup["at"]))
    return out


def status_line(repo: str, need: Sequence[str]) -> str:
    """`--status` 의 한 줄. 어느 경우든 예외 없이 글 하나를 돌려준다."""
    m, _ = load_manifest(repo)
    if m is None:
        return "Mode 1 봉인 — 없음"
    got = problems(repo, need)
    if got:
        return "Mode 1 봉인 — 깨짐: " + got[0]
    parts = ["있음"]
    stale = staleness(repo)
    if stale:
        parts.append("낡음 %d건" % len(stale))
    if uncommitted(repo):
        parts.append("미커밋")
    if m.get("superseded_by"):
        parts.append("뒤 실행 실패")
    return "Mode 1 봉인 — " + " · ".join(parts)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="봉인된 Mode 1 산출물 판정")
    ap.add_argument("repo")
    ap.add_argument("--need", required=True, help="쉼표로 — terms-db, wiki")
    ap.add_argument("--list", action="store_true", help="통과하면 봉인된 경로와 낡음을 JSON 으로 낸다")
    ap.add_argument("--status", action="store_true", help="한 줄 상태만. 늘 exit 0")
    a = ap.parse_args(argv)
    repo = os.path.abspath(str(a.repo))
    need = [k for k in str(a.need).split(",") if k]
    if not need or any(k not in KINDS for k in need):
        print("에러 — 모르는 종류 %r (있는 것: %s)" % (a.need, ", ".join(KINDS)), file=sys.stderr)
        return 2
    if a.status:
        print(status_line(repo, need))
        return 0
    got = problems(repo, need)
    if got:
        for line in got:
            print(line, file=sys.stderr)
        print(FIX, file=sys.stderr)
        return 1
    m, _ = load_manifest(repo)
    assert m is not None
    warn = warnings(repo, m)
    if warn:
        print("경고 — %d건. 있는 자료로 진행한다" % len(warn), file=sys.stderr)
        for line in warn[:20]:
            print("  " + line, file=sys.stderr)
    if a.list:
        stale = staleness(repo)
        print(json.dumps({"manifest": os.path.join(repo, MANIFEST),
                          "artifacts": [os.path.join(repo, e["path"]) for k in need for e in m["artifacts"][k]],
                          "stale": stale,
                          "stale_files": sorted(s.split(" ", 1)[1] for s in stale),
                          "uncommitted": bool(uncommitted(repo)),
                          "superseded_by": m.get("superseded_by")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
`test/test_no_any.py` 의 `COVERED` 에 `"machine/evidence.py",`.

Run: `.venv/bin/python -m pytest machine/test_evidence.py -q && npm run typecheck:py` → Expected: `13 passed` · `0 errors`.

- [ ] **Step 3: `collect` 관문 시험** — `test/test_term.py` 끝에:

```python
def test_collect_은_용어_사전_없이_돌지_않는다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nRenderer 를 고친다.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"), str(plan)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "terms-db.json" in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def test_collect_은_봉인_없는_용어_사전을_거부한다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo = tmp_path / "대상"
    (repo / "docs" / "codegraph").mkdir(parents=True)
    db = repo / "docs" / "codegraph" / "terms-db.json"
    db.write_text("{}", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"), str(plan), str(db)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "manifest.json 이 없다" in r.stderr
    assert not (tmp_path / "term-candidates.json").exists()


def test_collect_은_낡은_파일의_용어에_stale_을_표시하고_evidence_를_싣는다(tmp_path):
    import hashlib, os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo = tmp_path / "대상"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    pub = repo / "docs" / "codegraph"
    pub.mkdir(parents=True)
    rec = {"kind": "function", "module": "pkg", "where": "pkg/a.py:1", "means": "하나를 돌려준다.",
           "uses": [], "neighbors": [], "source": "reading"}
    (pub / "terms-db.json").write_text(json.dumps({"f": rec}, ensure_ascii=False), encoding="utf-8")

    def git(*a: str) -> None:
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                       check=True, capture_output=True)

    git("init", "-q")
    blob = subprocess.run(["git", "-C", str(repo), "hash-object", "pkg/a.py"],
                          capture_output=True, text=True).stdout.strip()
    doc = {"contract": "mode1-artifacts", "version": 1, "producer_commit": "p", "source_commit": "s",
           "source_exts": [".py"], "skip_dirs": ["docs", "out"],
           "artifacts": {"terms-db": [{"path": "docs/codegraph/terms-db.json",
                                       "sha256": hashlib.sha256((pub / "terms-db.json").read_bytes()).hexdigest()}]},
           "inputs": {"pkg/a.py": blob}}
    (pub / "manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "init")
    (repo / "pkg" / "a.py").write_text("def f():\n    return 2\n", encoding="utf-8")     # 봉인 뒤 바뀜
    plan = tmp_path / "plan.md"
    plan.write_text("# 계획\nf 를 고친다.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(root, "runner", "term", "collect.py"),
                        str(plan), str(pub / "terms-db.json")], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0 and "경고" in r.stderr
    got = json.loads((tmp_path / "term-candidates.json").read_text(encoding="utf-8"))
    assert got["known"]["f"]["stale"] is True
    assert got["evidence"]["stale"] == ["바뀜 pkg/a.py"] and got["evidence"]["uncommitted"] is False
```
(파일 머리에 `import json` 이 없으면 더한다.)

Run: `.venv/bin/python -m pytest test/test_term.py -q -k collect_은` → Expected: 셋 다 실패(지금은 용어 사전이 선택이고 봉인을 보지 않는다).

- [ ] **Step 4: `collect.py`** — 머리 import 네 줄 아래에 `import subprocess` 와:
```python
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE = os.path.join(_ROOT, "machine", "evidence.py")
```
`if __name__ == "__main__":` 아래 전체를:
```python
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collect":
        sys.argv.pop(1)

    if len(sys.argv) < 3:
        print("사용법 — report-term collect <plan.md> <terms-db.json>", file=sys.stderr)
        print("  terms-db.json 은 codebase-wiki 의 Mode 1 이 대상 저장소 docs/codegraph/ 에 봉인해 낸다",
              file=sys.stderr)
        sys.exit(1)

    plan_path = sys.argv[1]
    db_path = os.path.abspath(sys.argv[2])
    top = subprocess.run(["git", "-C", os.path.dirname(db_path), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip() or os.path.dirname(db_path)
    # stderr 는 그대로 흘려 경고가 터미널에 보이게 하고, stdout 의 JSON 만 받는다.
    ev = subprocess.run([sys.executable, EVIDENCE, top, "--need", "terms-db", "--list"],
                        stdout=subprocess.PIPE, text=True)
    if ev.returncode != 0:
        print("에러 — 봉인된 Mode 1 결과가 없다. 정답지 없이는 시험을 낼 수 없다.", file=sys.stderr)
        sys.exit(1)
    listed = cast(dict[str, Any], json.loads(ev.stdout))
    stale_files = set(cast(list[str], listed.get("stale_files", [])))

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
    with open(db_path, "r", encoding="utf-8") as f:
        db = cast(dict[str, Any], json.load(f))

    known = pick_terms(db, plan_text)
    for rec in known.values():
        if str(rec.get("where", "")).split(":")[0] in stale_files:
            rec["stale"] = True          # 봉인 뒤 바뀐 파일의 용어 — 출제자가 피하거나 표시한다 (U16)
    fresh = find_new_concepts(db, plan_text)

    out = {
        "plan": plan_path,
        "known": known,
        "newConcepts": fresh,
        "evidence": {"manifest": listed.get("manifest"), "stale": listed.get("stale", []),
                     "uncommitted": listed.get("uncommitted", False),
                     "superseded_by": listed.get("superseded_by")},
    }
    path = os.path.join(os.getcwd(), "term-candidates.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(path)
    print(f"  코드베이스 용어 {len(known)}개")
    print(f"  Plan 신규 개념 {len(fresh)}개 — 정답은 Plan 저자가 써야 한다")
    if fresh:
        print(f"    {', '.join(fresh)}")
```
(낡음 경고는 `evidence.py` 가 stderr 로 찍고 exit 0 이라 그대로 진행한다 — U9.)

- [ ] **Step 5: 실행기 — `--terms-db` 필수**

`runner/run_mode1_5.py:791-792` → `required=True, help="코드베이스 용어 사전. 대상 저장소 docs/codegraph/terms-db.json (codebase-wiki 가 봉인한다)"`. `collect_argv` 의 `terms_db: str | None` → `terms_db: str`, `if terms_db:` 분기를 없애고 늘 붙인다. `Mode15Context.terms_db` → `str = ""`. `runner/test_run_mode1_5.py` 의 `test_collect_argv_works_without_a_term_database` 를 지우고:
```python
def test_collect_argv_always_names_the_term_database():
    """용어 사전은 필수다 — Mode 1.5 는 Mode 1 결과 없이 돌지 않는다."""
    argv = R.collect_argv(root="/r", plan="/p.md", terms_db="/db.json")
    assert argv[-2:] == ["/p.md", "/db.json"]
```
`--terms-db` 없이 `main` 을 부르는 시험이 `SystemExit(2)` 로 떨어지면 그 시험 인자에 `"--terms-db", "/어느/terms-db.json"` 을 더한다.

- [ ] **Step 6:**
```bash
.venv/bin/python -m pytest machine/test_evidence.py test/test_term.py runner/test_run_mode1_5.py test/test_no_any.py -q && npm run typecheck:py
git add machine/evidence.py machine/test_evidence.py test/test_no_any.py runner/term/collect.py runner/run_mode1_5.py runner/test_run_mode1_5.py test/test_term.py
git commit -m "[update] : machine/evidence 판정과 report-term collect 관문 - 봉인 필수, 낡음은 경고"
```

#### Task K7: Mode 2 — 봉인이 있으면 근거로, 없어도 진행 (U0 · U1 · U14 · U15)

**Files:**
- Modify: `runner/prompts/agent.md`(절 둘과 자리 하나) · `runner/run_mode2.py` · `runner/test_run_mode2.py`

`report-spec init` 은 봉인을 보지 않는다 — 고칠 것 없다. 근거를 쓰는 곳은 에이전트 프롬프트뿐이다.

- [ ] **Step 1: 리소스** — `runner/prompts/agent.md` 의 `main` 절에서 `{{terms_block}}` 한 줄 바로 아래에 `{{evidence_block}}` 한 줄. 파일 끝에:
```
<!-- section: evidence -->
## Mode 1 실측 자료 — 이 저장소에 봉인돼 있다

{{listed}}

형제 저장소 `codebase-wiki` 가 이 저장소를 읽어 만들고 봉인한 것이다({{manifest}}). 코드의 뜻 · 동작 ·
관계는 **설계 문서와 이 자료를 근거로** 적는다. 위키는 `docs/wiki/index.md` 에서 장을 고르고, 용어 뜻은
`terms-db.json` 의 `means` 를 쓴다. 둘에 없는 사실은 지어내지 말고 `EvidenceNote` 에 "Mode 1 자료에 없음" 으로 적는다.

<!-- section: evidence-stale -->
**봉인 뒤 소스가 움직였다** — 아래 파일에 대한 서술은 자료를 믿지 말고 코드를 직접 읽어 확인한다.

{{stale}}

<!-- section: evidence-uncommitted -->
**봉인이 커밋되지 않았다** — 이 자료는 이 기계에만 있다. 다른 기계에서 보고서를 다시 지으면 근거가 달라질 수 있다.
```

- [ ] **Step 2: 실패하는 시험** — `runner/test_run_mode2.py` 끝에:
```python
def test_prompt_names_mode1_evidence_when_sealed():
    got = R.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md", "/프로젝트/docs/codegraph/terms-db.json"],
                         manifest="/프로젝트/docs/codegraph/manifest.json")
    assert "## Mode 1 실측 자료" in got and "  /프로젝트/docs/wiki/index.md" in got
    assert "봉인 뒤 소스가 움직였다" not in got


def test_prompt_lists_stale_files_when_sources_moved():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md"], manifest="/m",
                         stale=["바뀜 pkg/a.py"])
    assert "봉인 뒤 소스가 움직였다" in got and "  바뀜 pkg/a.py" in got


def test_prompt_has_no_evidence_block_without_seal():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구")
    assert "## Mode 1 실측 자료" not in got


def test_prompt_notes_an_uncommitted_seal():
    got = R.agent_prompt("/프로젝트", "슬러그", "x-design.md", "/도구",
                         evidence=["/프로젝트/docs/wiki/index.md"], manifest="/m", uncommitted=True)
    assert "봉인이 커밋되지 않았다" in got
```
Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -q -k "evidence or stale"` → Expected: `TypeError: … unexpected keyword argument 'evidence'`.

- [ ] **Step 3: 구현**

`AgentStage.prompt_names` → `("agent#main", "agent#terms", "agent#evidence", "agent#evidence-stale", "agent#evidence-uncommitted")`.
`agent_prompt` 시그니처에 `evidence: Sequence[str] = (), manifest: str = "", stale: Sequence[str] = (), uncommitted: bool = False`, 몸을:
```python
    folder = report_dir(project, slug, doc_dir)
    terms_block = ""
    if terms_json:
        terms_block = "\n" + AgentStage.load_prompt("agent#terms", terms_json=terms_json)
    evidence_block = ""
    if evidence:
        evidence_block = "\n" + AgentStage.load_prompt(
            "agent#evidence", listed="\n".join("  " + p for p in evidence), manifest=manifest)
        if stale:
            evidence_block += "\n" + AgentStage.load_prompt(
                "agent#evidence-stale", stale="\n".join("  " + s for s in stale))
        if uncommitted:
            evidence_block += "\n" + AgentStage.load_prompt("agent#evidence-uncommitted")
    return AgentStage.load_prompt("agent#main", project=project, spec_file=spec_file, folder=folder, root=root,
                                  terms_block=terms_block, evidence_block=evidence_block, doc_dir=doc_dir)
```
`Mode2Context` 끝에 `evidence: tuple[str, ...] = ()` · `manifest: str = ""` · `stale: tuple[str, ...] = ()` · `uncommitted: bool = False`. `AgentStage.prompt` 와 `run_agent` 가 넷을 그대로 넘긴다.

`main` 에서 `terms_json` 을 정한 바로 뒤에 — 상태 한 줄(U14)을 먼저 찍고, 목록을 받는다:
```python
    top = subprocess.run(["git", "-C", project, "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip() or project
    evidence_py = os.path.join(ROOT, "machine", "evidence.py")
    status = subprocess.run([sys.executable, evidence_py, top, "--need", "terms-db,wiki", "--status"],
                            capture_output=True, text=True).stdout.strip()
    print(status or "Mode 1 봉인 — 상태를 알 수 없다")
    ev = subprocess.run([sys.executable, evidence_py, top, "--need", "terms-db,wiki", "--list"],
                        capture_output=True, text=True)
    sealed = (json.loads(ev.stdout) if ev.returncode == 0
              else {"manifest": "", "artifacts": [], "stale": [], "uncommitted": False})
    if ev.stderr:
        print(ev.stderr, end="", file=sys.stderr)
```
`Mode2Context(…, evidence=tuple(sealed["artifacts"]), manifest=sealed["manifest"], stale=tuple(sealed["stale"]), uncommitted=bool(sealed["uncommitted"]))`. "이미 있는 것 — …" 줄에 `· Mode 1 자료 %s` 를 더하고 `"%d건 (낡음 %d)" % (len(sealed["artifacts"]), len(sealed["stale"])) if sealed["artifacts"] else "없음 — 근거 자리 없이 진행"` 을 넣는다. 봉인이 없어도, 깨져도 멈추지 않는다 — 상태 줄이 그것을 말한다.

- [ ] **Step 4:**
```bash
.venv/bin/python -m pytest runner/ test/test_prompt_resources.py -q && npm run typecheck:py
git add runner/prompts runner/run_mode2.py runner/test_run_mode2.py
git commit -m "[update] : mode 2 는 봉인이 있으면 근거로 싣고 없어도 진행한다"
```

#### Task K7b: `report-spec init` 이 봉인 상태 한 줄을 찍는다 (U14)

**Files:**
- Modify: `viz/init.py` (`main` 앞 함수 둘 · `main` 첫머리) · `viz/CLAUDE.md`
- Test: `test/test_init.py`

판정만 한다. 막지 않는다 — Mode 2 는 Mode 1 과 독립이다. 스킬 경로(`init → build → check`)에 봉인 상태가 닿는 유일한 자리다.

- [ ] **Step 1: 실패하는 시험** — `test/test_init.py` 끝에:

```python
def test_mode_one_status_는_한_줄을_돌려준다(tmp_path):
    import subprocess, sys
    from viz.init import modeOneStatus
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    assert modeOneStatus(sys.executable, str(tmp_path)) == "Mode 1 봉인 — 없음"


def test_init_은_상태를_찍고_막지_않는다(tmp_path):
    import os, subprocess, sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "2026-01-01-x-design.md").write_text("# X\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    r = subprocess.run([sys.executable, os.path.join(root, "viz", "init.py"), "x"],
                       cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0 and "Mode 1 봉인 — 없음" in r.stdout
    assert (tmp_path / "specs" / "x" / "data.ts").exists()
```
Run: `.venv/bin/python -m pytest test/test_init.py -q -k "status or 막지"` → Expected: `ImportError: cannot import name 'modeOneStatus'`.

- [ ] **Step 2: 구현** — `viz/init.py` 의 `main` 위에:

```python
EVIDENCE = os.path.join(ROOT, "machine", "evidence.py")


def repoTopLevel(cwd: str) -> str:
    """git 최상위. git 밖이면 cwd 그대로 — build.py 가 링크 뿌리를 찾는 것과 같은 규칙."""
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd


def modeOneStatus(python: str, repo: str) -> str:
    """봉인 상태 한 줄. 판정만 하고 막지 않는다 — Mode 2 는 Mode 1 과 독립이다."""
    r = subprocess.run([python, EVIDENCE, repo, "--need", "terms-db,wiki", "--status"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "Mode 1 봉인 — 상태를 알 수 없다 (evidence.py 가 답하지 않았다)"
```
`main` 에서 `docs = listDocs(cwd)` 바로 뒤에 `print(modeOneStatus(sys.executable, repoTopLevel(cwd)))`. `viz/CLAUDE.md` 의 "`report-spec init` 의 slug 검증" 목록에 `- **봉인 상태 한 줄** — init 이 machine/evidence.py --status 를 불러 찍는다. 막지 않는다 — Mode 2 는 Mode 1 과 독립이다`.

- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest test/test_init.py -q && npm run typecheck:py
git add viz/init.py viz/CLAUDE.md test/test_init.py
git commit -m "[update] : report-spec init 이 mode 1 봉인 상태를 한 줄 찍는다 - 막지 않는다"
```

#### Task K8: 계약 문서와 스킬 둘 (U4 · U16)

**Files:**
- Create: `docs/contract-mode1-artifacts.md`
- Modify: `~/.claude/skills/term-benchmark/SKILL.md` · `~/.claude/skills/spec-review-dashboard/SKILL.md` (**원본**) → 사본 `.claude/skills/*/SKILL.md` · `test/test_docs_citations.py`

- [ ] **Step 1: 계약 문서**

```markdown
# Mode 1 산출물 계약 v1 — codebase-wiki 가 봉인하고 report-builder 가 판정한다

**정본은 `contracts/mode1-artifacts.v1.json` 이다.** 이 문서는 그것을 사람이 읽게 푼 것이다. 두 저장소에 같은 사본으로 산다.
코드는 서로를 부르지 않는다 — 결정 0011.

| 대상 저장소 안의 자리 (git 추적) | 만드는 것 (codebase-wiki) | 읽는 것 (report-builder) |
|---|---|---|
| `docs/codegraph/manifest.json` | `machine/manifest.py` · 단계 `seal-artifacts` | `machine/evidence.py` |
| `docs/codegraph/terms-db.json` | 봉인이 작업 파일을 복사해 낸다 | `report-term collect` · `term-benchmark` 스킬 |
| `docs/wiki/*.md` | `write-wiki` 단계 | Mode 2 에이전트 프롬프트(있을 때만) |

## 실행 규칙

- **Mode 1 은 사람이 부를 때만 돈다.** 무엇도 대신 돌리지 않는다. 다시 돌린 뒤 `docs/codegraph/` 를 커밋하는 것도 사람이다.
- **Mode 1.5 는 봉인이 없으면 돌지 않는다.** 봉인 뒤 소스가 움직였으면 경고하고 있는 자료로 돈다.
- **Mode 2 는 Mode 1 과 독립이다.** 봉인이 있으면 근거로 쓰고, 없어도 돈다.

## 봉인 — 무엇을 싣나

그 실행에서 검사기를 통과하고 **지금 소스를 다시 읽은** 것만. `terms-db` 는 소스 파일마다의 지문이 지난 전수조사와
같아야 하고, `wiki` 는 `write-wiki` 가 그 지문을 따라잡았어야 한다(증분에서는 바뀐 파일을 인용하는 장을 다시 쓴다).
코드가 바뀌었으면 해결은 Mode 1 증분 실행 하나다 — 다시 읽지 않고 봉인만 고치는 길은 없다.

## 판정 — 구조 문제와 낡음

구조 문제(exit 1): 봉인 없음 · 계약 판 다름 · 필요한 종류 없음 · 봉인 뒤 산출물이 바뀜 · 봉인 뒤 위키 장이 생김 ·
`terms-db.json` 이 계약 꼴이 아님. 낡음(경고, exit 0): 봉인 뒤 소스가 바뀜 · 생김 · 사라짐. 보고서 원고 커밋은 낡음이 아니다.

## 판 올림

열쇠를 더하는 것은 같은 판이다. 빼거나 뜻을 바꾸면 `v2` 파일을 새로 만든다. codebase-wiki 에서 `tools/gen_contract.py` 로
내고 `contracts/` 둘을 report-builder 로 복사한 뒤 `tools/gen_contract_types.py` 로 형을 다시 낸다.
```

- [ ] **Step 2: `term-benchmark` 원본** — "코드베이스 용어 DB(`terms-db.json`)가 없을 때 … **멈춘다**" 문단 뒤에 한 줄: "**봉인이 없어도 멈춘다** — `report-term collect` 가 `machine/evidence.py` 로 판정한다. 에이전트는 Mode 1 을 대신 돌리지 않는다. 사용자에게 아래 명령을 알리고 끝낸다. 봉인 뒤 소스가 움직였다는 경고는 시험을 막지 않는다 — 대신 `term-candidates.json` 의 `evidence.stale` 을 첫 줄로 사용자에게 알리고, `known` 중 `stale: true` 인 용어는 **출제하지 않거나** 문항 `source` 뒤에 `(낡음 — 봉인 뒤 파일이 바뀜)` 을 붙인다. `evidence.uncommitted` 가 참이면 '이 정답지는 이 기계에만 있다' 도 알린다." 생성 명령 블록을:
```bash
# 코드베이스 용어 DB 는 codebase-wiki 의 Mode 1 이 만들고 봉인한다. 사람이 돌린다:
cd $TOOLS_ROOT/codebase-wiki && .venv/bin/python runner/run_mode1.py <저장소>
# → <저장소>/docs/codegraph/terms-db.json + manifest.json   (계약: docs/contract-mode1-artifacts.md)
```
`--terms-db <terms-db.json>` 예시의 경로를 `<저장소>/docs/codegraph/terms-db.json` 으로.

- [ ] **Step 3: `spec-review-dashboard` 원본** — 절차 절 앞에:
```markdown
## 근거 — 봉인된 Mode 1 실측이 있으면 그것을

Mode 2 는 Mode 1 과 독립이다. 대상 저장소에 봉인(`docs/codegraph/manifest.json`)이 있으면 실행기가 위키와 용어 DB 를
근거 자리로 프롬프트에 싣고, 봉인 뒤 바뀐 파일은 코드를 직접 읽어 확인하라고 덧붙인다. 봉인이 없어도 보고서는 만든다.
**에이전트는 Mode 1 을 대신 돌리지 않는다.** 계약은 `docs/contract-mode1-artifacts.md`.
```

- [ ] **Step 4:**
`test/test_docs_citations.py` 의 `contextDocs` 에 `"docs/contract-mode1-artifacts.md",`.
```bash
cp ~/.claude/skills/term-benchmark/SKILL.md .claude/skills/term-benchmark/SKILL.md
cp ~/.claude/skills/spec-review-dashboard/SKILL.md .claude/skills/spec-review-dashboard/SKILL.md
.venv/bin/python -m pytest test/test_docs_citations.py -q
git add docs/contract-mode1-artifacts.md .claude/skills/term-benchmark/SKILL.md .claude/skills/spec-review-dashboard/SKILL.md test/test_docs_citations.py
git commit -m "[docs] : mode 1 산출물 계약 v1 과 두 스킬의 실행 규칙"
```

### Phase M — 게이트 · 병합 · 가를 지점 고정

#### Task M1: 게이트

```bash
.venv/bin/python -m pytest -q
npm test && npm run typecheck && npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
.venv/bin/python tools/gen_contract.py --check && .venv/bin/python tools/gen_contract_types.py --check
npm run doctor
.venv/bin/python machine/evidence.py . --need terms-db; echo "exit $?"
```
Expected: pytest 실패는 알려진 빨강 둘만. 나머지 초록. README 가 낡았으면 다시 내고 `[docs] : readme 재생성` 으로 커밋한다. 마지막 줄은 `manifest.json 이 없다` · `exit 1` — Phase E 까지 이 저장소의 정상이다(§0.4).

#### Task M2: `main` 에 올린다 (Q3)

```bash
git checkout main
git merge --ff-only survey-per-file-2pass
git push origin main
git tag split-base-2026-10-24
git push origin split-base-2026-10-24
```
Expected: `Fast-forward`. 거부되면 `main` 에 새 커밋이 생긴 것이다 — 사용자에게 알린다.

### Phase B — `codebase-wiki` 를 뽑는다

#### Task B1: 경로 목록 · 새 clone · 두 번 거르기

**Files:** Create `$TOOLS_ROOT/split-work/mode1-paths.txt`

- [ ] **Step 1: 경로 목록** (디렉토리는 그 아래 전부. 옛 자리 `codegraph` 는 2026-08-30 이전 기계축 이력)

```
bin/report-wiki
config/mode1.toml
contracts
runner/__init__.py
runner/CLAUDE.md
runner/README.md
runner/check_shard.py
runner/dispatch.py
runner/measure.py
runner/pipeline.py
runner/run_mode1.py
runner/runner_presudo.md
runner/mode1
runner/wiki
runner/test_measure.py
runner/test_mode1.py
runner/test_pipeline.py
runner/test_run_mode1.py
machine
codegraph
viz/__init__.py
viz/CLAUDE.md
viz/README.md
viz/render_classes.py
viz/render_modules.py
viz/demermaid.py
viz/templates/dot
tools
test/CLAUDE.md
test/test_docs_citations.py
test/test_no_any.py
test/test_dispatch.py
test/test_portability.py
test/test_wiki.py
test/test_prompt_resources.py
evals
resources
docs/CLAUDE.md
docs/contract-mode1-artifacts.md
docs/decisions
docs/overturn
docs/wiki
docs/diagrams
docs/prompt
docs/2026-09-19-mode1-역대-실측과-패치-이력.md
docs/2패스개선.md
docs/analysis-2026-08-31-cpp-collectors.md
docs/코드베이스 분석 보고서 파이프라인.png
docs/코드베이스_분석_보고서_파이프라인.pdf
docs/handoffs/DECISION-cpp-symbol-index.md
docs/handoffs/DECISION-csharp-intermediate-format.md
docs/handoffs/HANDOFF-2026-08-29-cpp-clang-doc-vs-clang-uml.md
docs/handoffs/HANDOFF-2026-08-29-griffe-python-prototype.md
docs/handoffs/HANDOFF-2026-08-29-mode-1-5-agents.md
docs/handoffs/HANDOFF-2026-08-29-mode-1-resurvey.md
docs/handoffs/HANDOFF-2026-08-29-mode-1-terms-db-tasks-1-5.md
docs/handoffs/HANDOFF-2026-08-29-mode-1-terms-db-tasks-6-7.md
docs/handoffs/HANDOFF-2026-08-29-mode-1-xmldoc-relocate.md
docs/handoffs/HANDOFF-2026-08-29-warmup-incremental-cache.md
docs/handoffs/HANDOFF-2026-09-07-codegraph-id-namespace.md
docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md
docs/handoffs/HANDOFF-2026-09-08-xmldoc-deprecation-marker.md
docs/handoffs/HANDOFF-clangd-reverse-refs.md
docs/handoffs/HANDOFF-codebase-wiki.md
docs/handoffs/HANDOFF-cpp-boundary-rules.md
docs/handoffs/HANDOFF-cpp-pattern-collection.md
docs/handoffs/HANDOFF-cpp-symbol-index-selection.md
docs/handoffs/HANDOFF-unity-boundary-rules.md
docs/handoffs/HANDOFF-unity-pattern-collection.md
docs/handoffs/HANDOFF-unity-roslyn-dump-v2.md
docs/handoffs/PROMPT-2026-08-30-bottomup-survey-harness.md
docs/handoffs/RESUME-2026-08-28-track-c.md
docs/handoffs/RESUME-2026-08-30-python-strict-and-collector.md
docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md
docs/handoffs/RESUME-2026-09-11-runner-stage-machine.md
docs/handoffs/cpp-index-friendly-conventions.md
docs/superpowers/plans/2026-08-28-llm-load-reduction.md
docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md
docs/superpowers/plans/2026-08-29-mode-1-wiki-entrypoint.md
docs/superpowers/plans/2026-08-30-bottomup-survey-harness.md
docs/superpowers/plans/2026-08-30-griffe-python-collector.md
docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md
docs/superpowers/plans/symbol-resolution-survey
docs/superpowers/plans/2026-08-30-warmup-mode1-wiring.md
docs/superpowers/plans/2026-09-08-runner-common-axis.md
docs/superpowers/plans/2026-09-08-runner-pipeline.md
docs/superpowers/plans/2026-09-11-runner-mode1-v2.md
docs/superpowers/plans/2026-09-11-runner-mode1-요약.md
docs/superpowers/plans/2026-09-11-runner-mode1.md
docs/superpowers/plans/2026-09-13-runner-msgspec.md
docs/superpowers/plans/2026-09-20-bottomup-leaf-reuse.md
docs/superpowers/plans/bottomup-leaf-reuse
docs/superpowers/plans/2026-10-22-split-mode1-and-report.md
docs/superpowers/specs/2026-08-28-llm-load-reduction-design.md
docs/superpowers/specs/llm-load-reduction
docs/superpowers/specs/2026-08-29-mode-1-terms-db-first-design.md
docs/superpowers/specs/mode-1-terms-db-first
docs/superpowers/specs/2026-08-30-griffe-python-collector-design.md
docs/superpowers/specs/griffe-python-collector
docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md
docs/superpowers/specs/runner-stage-machine
.claude/CLAUDE.md
.claude/settings.json
.claude/agents/mode-1-codebase-wiki.md
.claude/skills/codebase-terms-survey
.agents/skills/codebase-terms-survey
.gemini/PythonRule.md
.github
CLAUDE.md
ARCHITECTURE.md
README.md
.gitignore
package.json
package-lock.json
requirements.txt
pyrightconfig.json
```

- [ ] **Step 2: clone · 거르기 둘** — 둘째가 report-builder 몫 다섯을 이력째 뺀다

```bash
cd "$TOOLS_ROOT"
git clone --no-local --branch main "$TOOLS_ROOT/report-builder" codebase-wiki
cd codebase-wiki
git filter-repo --paths-from-file "$TOOLS_ROOT/split-work/mode1-paths.txt"
git filter-repo --force --invert-paths \
  --path machine/evidence.py --path machine/test_evidence.py --path machine/contract_types.py \
  --path tools/gen_contract_types.py --path tools/test_gen_contract_types.py
```
- [ ] **Step 3:**
```bash
git ls-files | awk -F/ '{print $1}' | sort | uniq -c | sort -rn
git ls-files machine tools | grep -cE 'evidence|contract_types'    # 기대: 0
ls runner/prompts viz/templates/report 2>&1                         # 기대: 둘 다 없다
```

#### Task B2: 원격 (Q2)

```bash
gh repo create DogGuyMan/codebase-wiki --private --description "Mode 1 — 코드베이스 위키와 정적 분석. 사람이 부르면 돌고, 검사를 통과한 실측을 대상 저장소에 봉인한다"
git remote add origin https://github.com/DogGuyMan/codebase-wiki.git
```

#### Task B3: 루트 설정

- [ ] **Step 1: `package.json`**
```json
{
  "name": "codebase-wiki",
  "version": "0.1.0",
  "description": "Mode 1 — 코드베이스를 읽어 코드 지도 · 용어 DB · VitePress 위키를 만들고 봉인한다",
  "scripts": {
    "typecheck:py": "npx --yes pyright@1.1.413",
    "doctor": "python3 tools/doctor.py",
    "setup": "bash tools/setup.sh"
  },
  "engines": {
    "node": ">=22.13.0"
  },
  "license": "ISC",
  "type": "module",
  "private": true,
  "devDependencies": {
    "@mermaid-js/mermaid-cli": "^11.16.0",
    "@types/node": "^26.3.0",
    "vitepress": "^1.6.4",
    "vitepress-plugin-mermaid": "^2.0.17"
  }
}
```
```bash
rm -rf node_modules package-lock.json && npx --yes npm@11.11.0 install --no-audit --no-fund
```
- [ ] **Step 2:** `tools/setup.sh` 의 `node viz/lib.mjs` 줄과 그 위 주석 삭제. `tools/doctor.py:109` 의 `"esbuild"` → `"vitepress"`.
- [ ] **Step 3:**
```bash
npm run setup     # 기대: "필수 항목이 전부 있다."
git add -A package.json package-lock.json tools/setup.sh tools/doctor.py
git commit -m "[chore] : codebase-wiki - mode 1 만 남긴 npm 의존성과 setup"
```

#### Task B4: 시험 목록

`test/test_no_any.py` COVERED 에서 `runner/run_mode1_5.py` · `runner/run_mode2.py` · `runner/run_grade.py` · `machine/evidence.py` · `machine/contract_types.py` 삭제, `runner/mode1/seal.py` 추가. `test/test_docs_citations.py` contextDocs 에서 `viz/src/CLAUDE.md` · `.claude/agents/mode-1-5-term-benchmark.md` · `.claude/agents/mode-2-spec-report.md` · `.claude/skills/spec-review-dashboard/SKILL.md` · `.claude/skills/term-benchmark/SKILL.md` 삭제.
```bash
.venv/bin/python -m pytest test/test_no_any.py test/test_prompt_resources.py -q
git add test/test_no_any.py test/test_docs_citations.py
git commit -m "[test] : codebase-wiki - 게이트 목록에서 mode 1.5 와 2 를 뺀다"
```
문서 인용 시험은 B6 전까지 빨강이 정상이다.

#### Task B5: 전수조사 레코드와 위키

```bash
cp "$TOOLS_ROOT/split-work/reading-mode1.json" machine/terms-reading.json
git rm -q docs/wiki/runner-mode1-5-term.md docs/wiki/runner-mode2-spec.md docs/wiki/runner-run-grade.md \
          docs/wiki/viz-build-pipeline.md docs/wiki/viz-components.md docs/wiki/viz-term-graph-runtime.md
grep -n 'runner-mode1-5-term\|runner-mode2-spec\|runner-run-grade\|viz-build-pipeline\|viz-components\|viz-term-graph-runtime' docs/wiki/*.md
```
보이는 **링크 줄만** 지운다.
```bash
.venv/bin/python machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading machine/terms-reading.json
git add machine/terms-reading.json docs/wiki/
git commit -m "[chore] : codebase-wiki - 전수조사 레코드와 위키를 mode 1 몫만 남긴다"
```
Expected: `terms_db.py` 실패는 Phase R 이 줄을 민 파일의 L2 에서만 나온다. Phase E 가 푼다.

#### Task B6: 컨텍스트 문서

- [ ] **Step 1: 루트 `CLAUDE.md`**

```markdown
# CLAUDE.md — 나침반 (codebase-wiki)

**이 문서는 지도가 아니라 나침반이다.** 어디를 봐야 하는지만 적는다.

| 어디 | 무엇 |
|---|---|
| [`runner/CLAUDE.md`](runner/CLAUDE.md) | **러너축** — Mode 1 실행기 · 명령 갈림길 · 얼갈이 단계 · 프롬프트 리소스 |
| [`machine/CLAUDE.md`](machine/CLAUDE.md) | **기계축** — 정적 수집 · 정규화 · 전수조사 레코드 · warmup · 봉인 |
| [`viz/CLAUDE.md`](viz/CLAUDE.md) | **시각축** — 모듈·클래스 다이어그램 · 위키 그림 사전 렌더 |
| [`tools/CLAUDE.md`](tools/CLAUDE.md) | 어느 축도 아닌 것 — 해석기 탐색 · 환경 점검 · README · 계약 리소스 · 템플릿 렌더 |
| [`test/CLAUDE.md`](test/CLAUDE.md) | 축을 가로지르는 시험 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 구조 · 데이터 흐름 |
| [`docs/contract-mode1-artifacts.md`](docs/contract-mode1-artifacts.md) | **이 저장소가 봉인하고 `report-builder` 가 판정하는 것.** 정본은 `contracts/mode1-artifacts.v1.json` |
| [`docs/wiki/`](docs/wiki/index.md) | **이 저장소의 RAG.** 코드를 뒤지기 전에 먼저 grep 한다 |
| [`docs/decisions/`](docs/decisions/README.md) | 기각·취소·보류된 것들. 같은 제안을 다시 하기 전에 읽는다 |
| [`docs/overturn/`](docs/overturn/README.md) | 뒤집힌 판단과 그 패턴. 기각하려 하기 전에 검사표를 읽는다 |
| [`docs/CLAUDE.md`](docs/CLAUDE.md) | 보관소. 첨부되지 않은 인계·계획 문서는 스스로 열지 않는다 |

## 이 저장소는 무엇인가

**Mode 1 — 코드베이스 위키.** 대상 저장소를 읽어 코드 지도 · 사실 파일 · 용어 전수 DB · VitePress 위키를 만들고,
검사를 통과하고 지금 소스를 다시 읽은 것을 대상 저장소 `docs/codegraph/` 에 **봉인**한다. 진입점 `bin/report-wiki`,
실행기 `runner/run_mode1.py`(열세 단계, 마지막이 `seal-artifacts`).

**사람이 부를 때만 돈다.** 형제 저장소 `report-builder` 는 봉인만 읽고 이 저장소를 부르지 않는다 —
결정 [`0011`](docs/decisions/0011-split-mode1-and-report.md). 계약을 바꾸면 `tools/gen_contract.py` 로 다시 내고
`contracts/` 둘을 같은 날 그쪽에 복사한다.

## 명령

```bash
npm run setup
npm run doctor
.venv/bin/python -m pytest -q
npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
.venv/bin/python tools/gen_contract.py --check
.venv/bin/python runner/run_mode1.py <저장소> --dry-run
.venv/bin/python runner/run_mode1.py <저장소>          # 증분 — 바뀐 파일만 다시 읽고, 그 파일을 인용하는 위키 장만 다시 쓰고, 봉인한다
```

### 게이트 여섯 — 전부 초록이어야 한다

| 게이트 | 명령 |
|---|---|
| 파이썬 시험 | `.venv/bin/python -m pytest -q` |
| 파이썬 타입 | `npm run typecheck:py` |
| README 표류 | `.venv/bin/python tools/gen_readme.py --check machine runner viz tools` |
| 계약 표류 | `.venv/bin/python tools/gen_contract.py --check` |
| 환경 | `npm run doctor` |
| 전수조사 | `.venv/bin/python machine/terms_db.py out/codegraph-raw/codegraph.json --repo . --reading machine/terms-reading.json` |

**건너뛰는 시험은 골든 저장소 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO`)가 없어서다.**
**알려진 빨강 — 위키와 전수조사 표류.** 분리와 리소스 이전으로 줄이 밀렸다. 재굽기(자기 실행)로 푼다.
**노랑** — `machine/test_survey_plan.py::test_이_저장소_실측` 은 분리로 코드 지도가 바뀌어 건너뛴다.

## 경로 변수

`$REPO_ROOT` · `$TOOLS_ROOT` · `$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO` · `REPORT_PYTHON`. 표는 [`machine/CLAUDE.md`](machine/CLAUDE.md) 의 "경로 변수" 절.

## 작업 규약

`.claude/CLAUDE.md` 의 13개 체크포인트가 그대로 적용된다. 그 위에:

- **리소스와 코드를 가른다 (최우선).** LLM 프롬프트는 단계당 한 파일 `runner/**/prompts/<단계>.md`(안은
  `<!-- section: 이름 -->`), 파일 템플릿은 `**/templates/*`, 설정값은 `config/*.toml`. 파이썬은 읽기만 한다 —
  `PromptResource.load_prompt("<파일>#<절>")` · `tools.template.render_file`. 자리표시는 `{{이름}}`. `test/test_prompt_resources.py` 가 막는다.
- 확신도는 🔵/🟡/💭 + 정수. **🔵는 이번 세션에서 실제로 읽은 file:line 또는 돌린 명령의 출력만.**
- 결정은 `[제안됨]` 으로 먼저 기록하고 검증 후 승격. 객관 사실과 💭 판단을 한 문장에 섞지 않는다.
- 구조 신설 제안 시 `design-decision-discipline` §2.5 의 4항목을 공개하고 §2.7 의 축을 선언한다.
- **남의 제안을 기각할 때는 `docs/overturn/README.md` 의 검사표를 먼저 지난다.**
- 코드 주석에는 "지금 이 코드가 무엇인가" 만 쓴다.
- `# <include …/>` 블록은 폐지된 주석 주입의 잔재다([`0010`](docs/decisions/0010-xmldoc-retired.md)). 새로 심지 않는다.
- 커밋 메시지는 `personal-commit-messages` 스킬을 따른다.
- 거울 함정 — 구현자 1, 소비자 1 이면 인터페이스를 만들지 않는다. 계약은 데이터로 둔다(결정 0011).

## 전수조사 스킬 원본

`codebase-terms-survey` 의 원본은 `.agents/skills/` 이고 `.claude/skills/` 는 심볼릭 링크다. `~/.claude/skills/` 의 것은 사본이다.
```

- [ ] **Step 2: `README.md`**

```markdown
# codebase-wiki

코드베이스를 읽어 **코드 지도 · 용어 DB · 위키**를 만들고, 검사를 통과한 실측을 대상 저장소에 봉인하는 도구다.
**사람이 부를 때만 돈다.**

| 명령 | 하는 일 |
|---|---|
| `report-wiki prep <저장소>` | 정적 수집 → `out/codegraph-raw/codegraph.json` · `facts/*.md` · `ranking.json` |
| `report-wiki build <저장소>` | `docs/wiki/*.md` → Mermaid 사전 렌더 → VitePress 정적 사이트 |
| `report-wiki check <저장소>` | 위키 산문의 `파일:줄` 인용을 3값으로 판정 |
| `runner/run_mode1.py <저장소>` | 위 셋과 LLM 칸(전수조사 · 위키 산문)을 한 번에 돌리고 `docs/codegraph/` 에 봉인한다 |

형제 저장소 `report-builder` 는 봉인을 읽는다 — `docs/contract-mode1-artifacts.md`. 봉인을 커밋하는 것은 사람이다.

## 다른 컴퓨터에서 시작하기

| | 무엇 | 왜 |
|---|---|---|
| **필수** | Node 22.13+ | VitePress 와 Mermaid 사전 렌더 |
| **필수** | Python 3.12+ | 기계축 전부 |
| **필수** | Graphviz 10.0.1+ (`dot`) | 모듈·클래스 다이어그램 |
| **필수** | git | 커밋 해시 · 파일 목록 · 봉인 지문 |
| 선택 | `clang-uml` · `clangd` | C++ 저장소 |
| 선택 | .NET SDK | C# 저장소 (`machine/roslyn-dump`) |

```bash
npm run setup
export PATH="<이 저장소>/bin:$PATH"
```
골든 변수가 없으면 해당 시험은 건너뛴다. 실패가 아니다.
```

- [ ] **Step 3: `ARCHITECTURE.md` 절삭**

| 절 | 조치 |
|---|---|
| §0 | "갈래는 셋이고 …" → "갈래는 하나(Mode 1)다. 사람이 부르면 돌고, 검사를 통과한 산출물을 대상 저장소 `docs/codegraph/` 에 봉인한다. 형제 저장소 `report-builder` 가 그 봉인을 읽는다 — `docs/contract-mode1-artifacts.md`." |
| §1 | `BIN` "진입점 1개". `specs/<slug>/…` 행 · `MS` 노드 · (가) (나) 삭제. 표에 `docs/codegraph/` 행(git 추적 · 봉인) |
| §2 | Mode 1.5 · 2 행 · `bin/report` 문장 · `M15` · `M2` · "Mode 2 단계별로" · "Mode 1.5 는 사람 앞에서 멈춘다" 삭제. 단계 표 끝에 `seal-artifacts` |
| §3 | "🔵 Mode 2 도 같은 모양이다…" 삭제 |
| §4 | `SPEC` · `TERM` · `SRC` 노드, `run_mode1_5` · `run_mode2` 행, Node 문단의 `viz/build.py` · `viz/src` 삭제 |
| §5 | `TDB --> MAN["docs/codegraph/manifest.json — 봉인"] -. 파일로 .-> RB["report-builder 가 판정한다"]`. `term-candidates.json` 이하 여섯 행 · "`terms.json` → `data.ts`" 문단 삭제 |
| §6 | 불변식은 인용 L1/L2/L3 와 봉인 규칙(§3.3) 두 행. `npm test` · `npm run typecheck` 행 · "시험이 `viz/src/` 를…" 삭제 |
| §7 | "일부러 막아 둔 곳" 의 Mode 2 네 행 · "컴포넌트 층" 삭제 |

- [ ] **Step 4: 모듈 문서**

| 파일 | 조치 |
|---|---|
| `runner/CLAUDE.md` | `run_mode1_5.py` · `run_mode2.py` · `term/` 행, 명령의 `run_mode1_5` · `run_mode2` · `test_import_isolation` 줄, 다이어그램 `term` 노드와 `dispatch → viz` 간선, "Mode 1.5 · 2 는 STAGES …" 줄, 의존 표의 `dispatch 표(init·build·check)` · `run_mode1_5.py` 삭제. `mode1/` 행에 `seal` |
| `viz/CLAUDE.md` | 남기는 절 — 직접 실행 가드 · `-Tsvg_inline` 과 Mermaid 대체 금지 · 위키 그림 사전 렌더 · Owns · 의존 표. 표는 `render_classes.py` · `render_modules.py` · `demermaid.py` · `templates/dot/` 네 행 |
| `test/CLAUDE.md` | `test_components` · `test_graph_math` · `test_check…test_wrap_terms` · `test_term` · `test_config` · `svg.test.mjs` 행, `npm test`, `.tmp/lib.mjs` 묶음, `Node · esbuild` 행 삭제 |
| `machine/CLAUDE.md` | "세 실행기가 여기를 부른다" → "실행기가 여기를 부른다", Mode 1.5 · 2 두 줄 삭제. 표에 `\| manifest.py \| 다시 읽고 검사를 통과한 산출물을 docs/codegraph 에 봉인한다 \|`. Owns 끝 → "`report-builder` 는 봉인만 읽는다(결정 0011)" |
| `tools/CLAUDE.md` | `python.py` 행의 `runner/run_mode1_5.py` 삭제. 표에 `\| gen_contract.py \| 계약 리소스를 형에서 낸다. --check 면 낡았을 때 exit 1 \| 게이트 "계약 표류" \|` |
| `evals/README.md` | mode 1.5 · 2 행과 그 문장 삭제 |

- [ ] **Step 5:**
```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools
.venv/bin/python -m pytest test/test_docs_citations.py -q
git add CLAUDE.md README.md ARCHITECTURE.md runner/CLAUDE.md viz/CLAUDE.md test/CLAUDE.md machine/CLAUDE.md tools/CLAUDE.md evals/README.md */README.md
git commit -m "[docs] : codebase-wiki - 컨텍스트 문서를 mode 1 저장소 것으로"
```

#### Task B7: 층 분포 고정값 시험을 노랑으로

`machine/test_survey_plan.py` 의 `test_이_저장소_실측` 위에(`import pytest` 가 없으면 더한다):
```python
@pytest.mark.skip(reason="두 저장소 분리로 이 저장소의 코드 지도가 바뀌었다. 기계마다 값이 다른 원인을 본 뒤 다시 잰다 — CLAUDE.md 게이트 절")
```
```bash
.venv/bin/python -m pytest machine/test_survey_plan.py -q
git add machine/test_survey_plan.py
git commit -m "[test] : 층 분포 고정값 시험을 분리 뒤 재측정까지 건너뛴다"
```

#### Task B8: `.github`

워크플로의 README 스텝 아래에:
```yaml
      - name: contract drift
        run: pip install -r requirements.txt && python tools/gen_contract.py --check
```
PR 템플릿에서 `npm test` 줄 · `npm run typecheck (tsc --noEmit) ·` 앞부분 · `<script>` 두 줄 · "컴포넌트 API 는 추가만…" 삭제, `- [ ] \`.venv/bin/python tools/gen_contract.py --check\`` 추가.
```bash
git add .github
git commit -m "[docs] : codebase-wiki - ci 에 계약 표류, pr 템플릿에서 mode 2 게이트 삭제"
```

#### Task B9: 스킬 · 에이전트 자리 (Q1 · Q7)

```bash
ls -la .claude/skills .agents/skills .claude/agents
ls -L .claude/skills/codebase-terms-survey >/dev/null && echo "링크 살아 있음"
```

#### Task B10: 게이트 여섯

```bash
.venv/bin/python -m pytest -q
npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
.venv/bin/python tools/gen_contract.py --check
npm run doctor
.venv/bin/python runner/run_mode1.py . --dry-run | tail -n 3
```
Expected: pytest 실패는 `test_wiki.py::test_check_는_통과를_통과로_보고한다` 하나. 전수조사 게이트는 B5 의 L2 만 빨강. `--dry-run` 은 `seal-artifacts` 로 끝난다.

#### Task B11: 올린다

```bash
git push -u origin main
```
`~/.zshrc` 에 `export PATH="$HOME/LLM-Tools/codebase-wiki/bin:$PATH"` 를 더하는 것은 사용자가 한다.

### Phase C — `report-builder` 를 Mode 1.5 + Mode 2 로 줄인다

#### Task C1: Mode 1 파일을 지운다

- [ ] **Step 1**
```bash
cd "$TOOLS_ROOT/report-builder" && git checkout main
git ls-files machine | grep -vE '^machine/(evidence|test_evidence|contract_types)\.py$' | xargs git rm -q
git rm -r -q bin/report-wiki config/mode1.toml runner/run_mode1.py runner/mode1 runner/wiki runner/check_shard.py \
  runner/runner_presudo.md runner/test_mode1.py runner/test_run_mode1.py runner/test_import_isolation.py \
  viz/render_classes.py viz/render_modules.py viz/demermaid.py viz/templates/dot \
  tools/gen_contract.py tools/test_gen_contract.py test/test_wiki.py evals/runs resources \
  .claude/agents/mode-1-codebase-wiki.md .claude/skills/codebase-terms-survey .agents/skills/codebase-terms-survey \
  docs/wiki/machine-cpp-collectors.md docs/wiki/machine-facts.md docs/wiki/machine-normalize.md docs/wiki/machine-py-collectors.md \
  docs/wiki/machine-survey-plan.md docs/wiki/machine-terms-db.md docs/wiki/machine-verify-citations.md docs/wiki/machine-warmup.md \
  docs/wiki/machine-xmldoc.md docs/wiki/runner-mode1-wiki.md \
  "docs/2026-09-19-mode1-역대-실측과-패치-이력.md" "docs/2패스개선.md" docs/analysis-2026-08-31-cpp-collectors.md \
  "docs/코드베이스 분석 보고서 파이프라인.png" "docs/코드베이스_분석_보고서_파이프라인.pdf"
grep -E '^docs/(handoffs|superpowers)/' "$TOOLS_ROOT/split-work/mode1-paths.txt" \
  | grep -vE 'mode-1-5-agents|runner-common-axis|runner-pipeline\.md|runner-msgspec|split-mode1-and-report' \
  | while IFS= read -r p; do git rm -r -q -- "$p"; done
```
- [ ] **Step 2: 이 저장소를 대상으로 한 전수조사 원본을 규약 자리로**
```bash
mkdir -p docs/codegraph
cp "$TOOLS_ROOT/split-work/reading-mode2.json" docs/codegraph/terms-reading.json
git add docs/codegraph/terms-reading.json
```
- [ ] **Step 3:** `grep -n 'machine-\|runner-mode1-wiki' docs/wiki/*.md` 가 보이는 링크 줄만 지운다.
- [ ] **Step 4:**
```bash
git add -A
git commit -m "[chore] : mode 1 을 codebase-wiki 저장소로 보내고 여기서 지운다"
```

#### Task C2: `tools/gen_readme.py` 가 `pycalls` 없이 돈다

- [ ] **Step 1:** `tools/test_gen_readme.py` 의 시험 이름과 독스트링만:
```python
def test_signature_is_rendered_from_the_ast(tmp_path: Path) -> None:
    """시그니처는 `signature_of` 가 ast 에서 만든다. 주석 · 기본값 · 키워드 전용 구분자가 그대로 살아야 한다."""
```
Run → Expected: `ModuleNotFoundError: No module named 'pycalls'`.
- [ ] **Step 2:** `tools/gen_readme.py:21-22` 두 줄을 지우고 그 자리에:
```python
def signature_of(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """`(a, b=..., *args, **kw) -> T` 꼴. 주석은 원문 그대로 살린다.

    codebase-wiki 의 `machine/pycalls.py` 의 같은 이름 함수와 같은 사본이다 — 결정 0011.
    """
    a = fn.args

    def one(arg: ast.arg, default: ast.expr | None) -> str:
        s = arg.arg
        if arg.annotation is not None:
            s += ": " + ast.unparse(arg.annotation)
        if default is not None:
            s += " = " + ast.unparse(default) if arg.annotation is not None \
                else "=" + ast.unparse(default)
        return s

    parts: list[str] = []
    positional = list(a.posonlyargs) + list(a.args)
    pad = len(positional) - len(a.defaults)
    for i, arg in enumerate(positional):
        parts.append(one(arg, a.defaults[i - pad] if i >= pad else None))
    if a.vararg is not None:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")
    for kw, kwdefault in zip(a.kwonlyargs, a.kw_defaults):
        parts.append(one(kw, kwdefault))
    if a.kwarg is not None:
        parts.append("**" + a.kwarg.arg)
    ret = " -> " + ast.unparse(fn.returns) if fn.returns is not None else ""
    return "(" + ", ".join(parts) + ")" + ret
```
`:11` 의 `pycalls` 언급 삭제. `DIR_DESCRIPTIONS` 의 `"machine"` → `"봉인된 Mode 1 산출물 판정 · 계약에서 생성한 형."`, `"runner"` → `"두 mode 실행기(1.5 · 2). 단계마다 벽시계 시간과 토큰을 잰다."`.
- [ ] **Step 3:**
```bash
.venv/bin/python -m pytest tools/ -q
.venv/bin/python tools/gen_readme.py machine runner viz tools
git add tools/gen_readme.py tools/test_gen_readme.py */README.md
git commit -m "[fix] : gen_readme 가 pycalls 없이 돈다 - signature_of 사본"
```

#### Task C3: 의존성 · 설정 · doctor

- [ ] **Step 1: `requirements.txt`**
```
# runner/ · viz/ · machine/ · tools/ 가 쓰는 서드파티. 표준 라이브러리는 적지 않는다. 판을 고정한다.
#   npm run setup                                     # .venv 를 만들고 이 목록을 깐다 (tools/setup.sh)
pytest==9.1.1      # 시험 전량
msgspec==0.21.1    # runner/pipeline.py · measure.py · machine/evidence.py 가 바깥 JSON · TOML 을 형으로 읽는다
```
- [ ] **Step 2:** `package.json` devDependencies 에서 `@mermaid-js/mermaid-cli` · `vitepress` · `vitepress-plugin-mermaid` 삭제 → `npx --yes npm@11.11.0 install --no-audit --no-fund`. `pyrightconfig.json` 의 `exclude` 에서 `"machine/roslyn-dump"` 삭제. `tools/doctor.py:117-120` 선택 네 행과 `:9-10` 의 괄호 삭제. `test/test_portability.py` 끝 줄 `"griffe"` → `"msgspec"`. `.github` 의 CI 에 `python tools/gen_contract_types.py --check` 스텝, PR 템플릿에 같은 줄과 `( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 )` 줄, "(골든 변수 없으면 19 건너뜀이 정상)" 삭제.
- [ ] **Step 3:**
```bash
rm -rf .venv && npm run setup
.venv/bin/python -m pytest -q && npm test && npm run typecheck && npm run typecheck:py
.venv/bin/python tools/gen_contract_types.py --check && ( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 )
git add requirements.txt package.json package-lock.json pyrightconfig.json tools/doctor.py test/test_portability.py .github
git commit -m "[chore] : report-builder - mode 1.5 와 2 만 남긴 의존성과 게이트"
```
Expected: pytest 실패 0 · 건너뜀 0. `npm test` 8 통과.

#### Task C4: 시험 목록

`test/test_no_any.py` COVERED 에서 `runner/run_mode1.py` · `runner/mode1/*.py` 삭제(지우기 전 `test_덮는_파일이_실제로_있다` 가 빨간지 먼저 본다). `test/test_docs_citations.py` contextDocs 에서 `.claude/agents/mode-1-codebase-wiki.md` · `.agents/skills/codebase-terms-survey/SKILL.md` 삭제.
```bash
.venv/bin/python -m pytest test/test_no_any.py test/test_prompt_resources.py -q
git add test/test_no_any.py test/test_docs_citations.py
git commit -m "[test] : report-builder - 게이트 목록에서 mode 1 을 뺀다"
```

#### Task C5: 컨텍스트 문서

- [ ] **Step 1: `machine/CLAUDE.md` 새로**
```markdown
# machine/ — 판정한다. 봉인된 Mode 1 산출물이 계약대로 있는가, 봉인 뒤 소스가 움직였는가

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 계약은 [`../docs/contract-mode1-artifacts.md`](../docs/contract-mode1-artifacts.md).

| 파일 | 하는 일 |
|---|---|
| `evidence.py` | 대상 저장소 `docs/codegraph/manifest.json` 으로 구조 문제(exit 1)와 낡음(경고)을 가른다 |
| `contract_types.py` | **생성물.** `tools/gen_contract_types.py` 가 `contracts/mode1-artifacts.v1.json` 에서 낸다. 손대지 않는다 |

**부르는 곳** — `runner/term/collect.py`(`terms-db`, 구조 문제면 멈춘다) · `runner/run_mode2.py`(`--list`, 없어도 진행). 둘 다 자식 프로세스로.
**봉인 계산(`source_files` · `blob_ids`)은 codebase-wiki `machine/manifest.py` 의 사본이다** — 결정 0011. 한쪽을 고치면 같은 날 다른 쪽도.
```
- [ ] **Step 2: 루트 `CLAUDE.md` 절삭**

| 절 | 조치 |
|---|---|
| 나침반 표 | `machine/CLAUDE.md` 행 → "**판정** — 봉인된 Mode 1 산출물의 꼴과 낡음". 새 행 `\| [docs/contract-mode1-artifacts.md](docs/contract-mode1-artifacts.md) \| **codebase-wiki 가 봉인하고 이 저장소가 판정하는 것.** 정본은 contracts/mode1-artifacts.v1.json \|` |
| 새 절 "Mode 사이의 실행 규칙" (나침반 바로 아래) | "Mode 1 은 codebase-wiki 에 있고 사람이 부를 때만 돈다. 이 저장소는 그것을 부르지 않는다. Mode 1.5 는 봉인이 없으면 멈추고 낡았으면 경고하고 돈다. Mode 2 는 Mode 1 과 독립이고 봉인이 있으면 근거로 쓴다 — 결정 0011." |
| 현재 상태 표 | 테스트 행을 C3 실측값으로 |
| "위키는 RAG 다" | "자기 자신에게 Mode 1 을 돌려" → "codebase-wiki 의 Mode 1 을 이 저장소에 돌려". 실측 표 → "분리 직후라 낡았다 — Phase E 뒤에 다시 잰다". "다시 굽는 것은 …" → "codebase-wiki 의 `runner/run_mode1.py <이 저장소>` 를 사람이 돌린다" |
| "그림은 두 도구가 굽고…" | `viz/svg.mjs` 행만 남기고 나머지 삭제 |
| "사양 원본과 인계 문서" | `RESUME-2026-09-11-runner-stage-machine.md` · `HANDOFF-codebase-wiki.md` 삭제. 재개 진입점은 이 계획서 |
| "게이트 여섯" | 행 추가 `\| 계약 사본 · 생성 형 \| ( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 ) && .venv/bin/python tools/gen_contract_types.py --check \|`. "빨강 하나" · "빨강 둘" → "`report-term collect` 는 봉인 없는 저장소에서 멈춘다(결정 0011). 이 저장소 자신은 codebase-wiki 가 다시 굽고 봉인하기 전까지 그렇다" |
| "mode 별 진입점" | `report-wiki` 행 삭제, "셋이" → "둘이", `report-term collect <plan.md> [terms-db.json]` → `<plan.md> <저장소>/docs/codegraph/terms-db.json` |
| "성격축 셋" | 기계 행 → "`machine/` — 판정(`evidence.py`)과 생성 형. Mode 1 의 기계축은 codebase-wiki 에 있다" |
| 스킬 두 자리 표 | `codebase-terms-survey` 언급 삭제. `16개 … 14개` → `15개 — 심볼릭 링크 13개 + 실제 디렉토리 2개` |
| "문서 정본" | `2026-08-29-mode-1-terms-db-first` 행 삭제 |

- [ ] **Step 3: `README.md`** — mode 표에서 1 행 삭제, 머리에 "코드베이스 위키(Mode 1)는 형제 저장소 `codebase-wiki` 이고 사람이 부를 때만 돈다. 이 저장소는 그것이 대상 저장소 `docs/codegraph/` 에 남긴 봉인을 판정하고 읽는다 — `docs/contract-mode1-artifacts.md`." "필요한 것" 표의 `clang-uml` · .NET · `clangd` · mermaid-cli 행 삭제.
- [ ] **Step 4: `ARCHITECTURE.md`** — §0 "셋" → "둘(1.5 · 2). Mode 1 은 codebase-wiki. 경계는 봉인된 데이터 계약". §1 의 `docs/wiki/*.md` 행 → "codebase-wiki 가 쓰고 봉인한다", `docs/codegraph/` 행 추가, (다) 삭제. §2 의 Mode 1 행 · 단계 표 · `M1` · "Mode 1 만 둘이다" 삭제. §3 Mode 1 실측 표 둘 삭제, 제목 "(Mode 2 실측)". §4 `WIKI` · `PY` 노드, `machine/*` 네 행 삭제. §5 머리 `MAN["docs/codegraph/manifest.json — codebase-wiki 가 봉인"] --> EV["machine/evidence.py"] --> CAND["term-candidates.json"]`. §6 인용 L1/L2/L3 행 · "인용 3값 판정" 절 삭제, 행 추가 `\| 봉인 \| 구조 문제면 1.5 가 멈춘다 · 낡음은 경고 \| report-term collect (machine/evidence.py) \|`. §7 "새 정적 수집기를 더하려면" · §8 삭제.
- [ ] **Step 5: 모듈 문서**

| 파일 | 조치 |
|---|---|
| `runner/CLAUDE.md` | `run_mode1.py` · `mode1/` · `wiki/` 행, `run_mode1` 명령 두 줄 · `test_import_isolation` 줄, `wiki` · `machine` 노드, Mode 1 전용 Gotcha 다섯("`run_mode1.py` 와 `mode1/` 만 `machine/` 을 import" · "Mode 1 에 단계를 더한다" · "`run_mode1.py` 를 import 하면 해석기가 바뀐다" · "기계축 선언이 실물과 어긋난다" · "대상 저장소의 전수조사 원본은…") 삭제. 의존 표 `여기 → ../machine/*` → "`term/collect.py` · `run_mode2.py` → `machine/evidence.py`(자식 프로세스)" |
| `viz/CLAUDE.md` | `render_*` · `demermaid` · `templates/dot/` 행, "파이썬 셋이 왜 기계축이 아닌가", "위키 그림 사전 렌더" 절, `../runner/* → 여기` 행 삭제 |
| `test/CLAUDE.md` | 머리의 `machine/ test_*.py 11개` → `machine/ test_evidence.py`, `test_wiki.py` 행, "건너뜀 19개" Gotcha, `bin/report-wiki` 행 삭제 |
| `tools/CLAUDE.md` | `python.py` 행의 `runner/wiki/*.py` 삭제. `signature_of` 문장 → "codebase-wiki `machine/pycalls.py` 와 같은 사본(결정 0011)". `여기 → ../machine/pycalls.py` 행 삭제. 표에 `\| gen_contract_types.py \| 계약 json 에서 machine/contract_types.py 를 낸다. --check 면 낡았을 때 exit 1 \| 게이트 "계약 사본 · 생성 형" \|` |
| `evals/README.md` | Mode 1 행 · "다음에 잴 것" 삭제 |

- [ ] **Step 6:**
```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools
.venv/bin/python -m pytest test/test_docs_citations.py -q
git add CLAUDE.md README.md ARCHITECTURE.md machine/CLAUDE.md runner/CLAUDE.md viz/CLAUDE.md test/CLAUDE.md tools/CLAUDE.md evals/README.md */README.md
git commit -m "[docs] : report-builder - 컨텍스트 문서를 mode 1.5 와 2 저장소 것으로"
```

#### Task C6: 게이트와 올리기

```bash
.venv/bin/python -m pytest -q
npm test && npm run typecheck && npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
.venv/bin/python tools/gen_contract_types.py --check && ( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 )
npm run doctor
grep -rn 'machine/' --include='*.py' --include='*.mjs' --include='*.ts' --include='*.tsx' runner viz tools test bin \
  | grep -v '<include file="machine/comments.xml"' | grep -vE 'machine/(evidence|contract_types)\.py'
git push origin main
```
Expected: 전부 초록 · 마지막 `grep` 출력 없음.

### Phase E — 재굽기와 봉인 (LLM 과금 · Q8 · 사람이 부른다)

#### Task E1: `codebase-wiki` 가 자기 자신을 굽고 봉인한다

```bash
cd "$TOOLS_ROOT/codebase-wiki"
.venv/bin/python runner/run_mode1.py . --cold --json "evals/runs/$(date +%F)-mode1-codebase-wiki-cold-sonnet.json"
.venv/bin/python bin/report-wiki check .
.venv/bin/python -m pytest -q
```
Expected: `seal-artifacts` 가 `terms-db, wiki` 를 `docs/codegraph/` 에 봉인한다. L1 · L2 실패 0, pytest 전부 초록. `docs/wiki/` · `docs/codegraph/` · `machine/terms-reading.json` · `evals/runs/*.json` 을 `[update] : 분리 뒤 첫 자기 실행 - 위키, 전수조사 재굽기와 봉인` 으로 커밋.

#### Task E2: `codebase-wiki` 가 `report-builder` 를 굽고 봉인한다

```bash
cd "$TOOLS_ROOT/codebase-wiki"
.venv/bin/python runner/run_mode1.py "$TOOLS_ROOT/report-builder" --cold
cd "$TOOLS_ROOT/report-builder"
.venv/bin/python machine/evidence.py . --need terms-db,wiki; echo "exit $?"
```
Expected: `exit 0`. `docs/wiki/*.md` · `docs/codegraph/*` 를 `[update] : codebase-wiki 로 다시 구운 위키와 봉인` 으로 커밋. 루트 `CLAUDE.md` "위키는 RAG 다" 의 실측 표를 이때 다시 적는다.

#### Task E3: 규칙이 실제로 그렇게 도는지 본다

```bash
cd "$TOOLS_ROOT/report-builder"
.venv/bin/python machine/evidence.py . --need terms-db,wiki --status      # 기대: "Mode 1 봉인 — 있음" (E2 의 봉인을 커밋했으면. 안 했으면 "… · 미커밋")
P=docs/superpowers/plans/2026-10-22-split-mode1-and-report.md
.venv/bin/python runner/term/collect.py "$P" docs/codegraph/terms-db.json; echo "exit $?"   # 기대: exit 0 · 경고 없음
echo "# 탐침" >> runner/measure.py
.venv/bin/python runner/term/collect.py "$P" docs/codegraph/terms-db.json; echo "exit $?"   # 기대: "경고 — 1건 · 소스 바뀜 runner/measure.py" · exit 0
.venv/bin/python -c "import json; d=json.load(open('term-candidates.json')); print(d['evidence']['stale'], sorted(k for k,v in d['known'].items() if v.get('stale')))"
                                                                                           # 기대: ['바뀜 runner/measure.py'] 와 measure.py 의 용어 이름들
( cd docs/superpowers && ../../.venv/bin/python ../../viz/init.py 2>&1 | head -1 )         # 기대: "Mode 1 봉인 — 있음 · 낡음 1건"
.venv/bin/python runner/run_mode2.py docs/superpowers plan-citation-precheck --dry-run | grep -E "Mode 1 (봉인|자료)"  # 기대: 상태 줄 + "…건 (낡음 1)"
git checkout -- runner/measure.py
mv docs/codegraph/manifest.json "$TOOLS_ROOT/split-work/manifest.bak"
.venv/bin/python runner/term/collect.py "$P" docs/codegraph/terms-db.json; echo "exit $?"   # 기대: "manifest.json 이 없다" · exit 1
.venv/bin/python runner/run_mode2.py docs/superpowers plan-citation-precheck --dry-run | grep "Mode 1 자료"  # 기대: "없음 — 근거 자리 없이 진행" · 멈추지 않는다
mv "$TOOLS_ROOT/split-work/manifest.bak" docs/codegraph/manifest.json
rm -f term-candidates.json
```
(`docs/superpowers` 는 `plans/` 를 가진 프로젝트 자리이고 `plan-citation-precheck` 은 report-builder 에 남는 보고서다 — §2.3.)

---

## 5. 자기 검토

**사양 대조.** (1) 두 git 저장소 — B · C. (2) 양방향 결합 제거 — §1.1 일곱 곳이 A2 · A3 · C2 와 "함께 간다" 로 닫힌다. 두 저장소 사이 호출 0 은 C6 의 `grep` 이 본다. (3) 실행 규칙 U0 — Mode 1 은 무엇도 대신 돌리지 않는다(자동 실행 코드가 계획에 없다) · 1.5 관문(K6) · Mode 2 독립(K7). (4) 리소스 분리 — R, §1.2 열여덟 곳, §1.3 넷, 게이트 R9. (5) U2 · U2b · U3 · U5 · U6 · U8 · U9 — 각각 K1 · K3 · K1 · R2/R4/R5 · K5 · K1 · K6. (6) 조용한 실행 · 조용한 실패 — U11 K2b · U12 K3 · U13 K1/K2/K6 · U14 K6/K7/K7b · U15 K6/K7 · U16 K6/K8. **묻는 코드는 없다** — 전부 찍고 진행하거나 멈춘다.

**자리표시자.** DOT 템플릿 셋(R6 Step 2)은 기계(`extract.py`)와 이름 규칙으로 만들고 바이트 대조(R8)가 결과를 고정한다. K2 Step 3 의 "지문 범위" 는 실물을 돌려 보고 맞추는 확인 단계다 — 🟡 `snapshot-sources` 가 찍는 범위를 이번 세션에서 읽지 않았다. `ctx.cold` 는 🔵 `runner/mode1/edges.py:41` · `run_mode1.py:228`.

**이름 일관성.** `PromptResource.load_prompt` · `sections` · `prompt_dir` · `prompt_names("<파일>#<절>")` (R2) → R4 · R5 · K7 · R9 에서 같다. `render` · `render_file` (R1) → R2 · R6. 생산자 `ArtifactManifest` · `ArtifactEntry`(K1) · `TermsDb`(`terms_db.py`) → 계약 `types`(K4) → 생성 형(K5) → `evidence.py`(K6) import. `ctx.verified` · `X.MANIFEST` · `X.WIKI_STATE`(K2) · `ctx.wiki_stale` · `stale_pages`(K3). `problems` · `staleness` · `load_manifest`(K6) · `evidence` · `manifest` · `stale`(K7).

**알려진 미결.** `machine/test_survey_plan.py` 의 새 기대값 · 복제한 커널과 봉인 계산의 표류 감시(0011 이 두지 않는다고 적었다) · §0.3 의 기본값 일곱.
