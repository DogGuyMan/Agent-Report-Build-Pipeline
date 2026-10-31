# 디렉토리 정리 — mode 1차 축 · `resource/` · `test/` 와 `qa/`

> 이 문서는 `2026-10-31-directory-reorg-design.md`(영어 정본)의 한국어 번역본이다. 고칠 때는 정본을 고치고 이 번역본을 다시 만든다.

**상태** [제안됨] · 2026-10-31 · 아홉 축 질의(묶음 넷 · 열네 문항)로 사용자가 설계를 승인했다. **아직 이행하지 않았다.** 두 저장소 분리의 R · A · K · M 이 2026-10-31 에 끝났으므로(`main` 병합 `6c4009d`) Phase B 앞에 실행한다 — "범위와 순서" 절.
**결정 기록** `docs/decisions/0014-mode-first-layout-and-resource-dir.md`.
**계획서** `docs/superpowers/plans/2026-10-31-directory-reorg.md`(영어 정본) · `docs/superpowers/plans/2026-10-31-directory-reorg.ko.md`(한국어 번역본).

> 계획서가 실행되기 전까지 `CLAUDE.md` · 모듈 `CLAUDE.md` · `ARCHITECTURE.md` · `README.md` · `docs/wiki/` 의 경로는 전부 **지금** 구조다. 이 문서는 **목표**를 적는다.

## 0. 요약

저장소 최상위를 **mode**(`codewiki/` = Mode 1, `term/` = Mode 1.5, `spec/` = Mode 2)로, 그 아래를 **언어**(`python/` · `csharp/` · `typescript/`)로, 그 아래를 지금의 **성격축**(`runner/` · `machine/` · `viz/`)으로 가른다. 성격축을 남기는 이유는 파일 이름과 import 경로가 살아남게 하려는 것이다. 세 mode 가 함께 쓰는 파일 다섯은 자리를 따로 받는다(단계 기계는 `core/`, 유틸은 `common/`). 리소스 전부 — 프롬프트 · 결함 표 · 파일 템플릿 · 설정 · 수집기 골든 꼴 · 이 저장소 자신의 전수조사 레코드 — 는 `resource/<mode>/` 아래로 간다. 모듈 시험은 `test/<mode|core|common|tools>/` 로, 저장소 규약 게이트와 실행기 측정값은 `qa/` 로 간다. 폐지된 xmldoc 잔재는 같은 변경에서 지운다. `docs/wiki/` 와 `terms-reading.json` 의 인용은 기계로 다시 쓴다(경로 치환 + 결정론적 줄 번호 재계산). 아카이브 디렉토리는 손대지 않고, Mode 1 은 **다시 돌리지 않는다**.

🔵 이 문서의 수치는 전부 2026-10-31 커밋 `b0bdb50` 에서 `git ls-files` · `grep` · 계획서에 실은 경로 지도의 예행 실행으로 잰 것이다. 추적 파일 480 → 192 이동 · 8 삭제 · 280 그대로. 두 원본이 한 목적지로 겹치는 경우 0.

## 1. 범위와 순서

| | |
|---|---|
| 범위 안 | 추적 파일 이동 · 개명, xmldoc 잔재 삭제, 경로 · import · `sys.path` · 게이트 목록 · 설정 파일 · CI · 진입점 수정, 위키 · 전수조사 레코드 · 컨텍스트 문서의 인용 재작성, 모듈 `CLAUDE.md` 재구성, 디렉토리별 `README.md` 재생성 |
| 범위 밖 | 동작 변경 일체, mode 안의 패키지 개명(`runner/mode1/` 은 `mode1` 그대로), Mode 1 재실행, 아카이브 문서 편집(`docs/handoffs/` · `docs/superpowers/` · `docs/my.self/` · `docs/decisions/` · `docs/overturn/`), `test_survey_plan.py` 의 층 분포 고정값(이미 빨강이고 원인 미상 — 루트 `CLAUDE.md` "게이트 여섯") |
| 언제 | 두 저장소 분리(결정 0011 · 계획 rev.4)의 **M** 뒤 · **B** 앞(R · A · K · M 은 2026-10-31 끝, `6c4009d`). 그 뒤 Phase B 는 `codewiki/` 를 통째로 `codebase-wiki` 저장소로 떼어낸다 |
| 어디서 | 사용자 Mac 의 로컬 세션(클라우드 핸드오프 대신 사용자가 고른 것) |
| 합격 | 커밋마다 게이트 여섯이 초록, `split-work/capture.sh` 의 산출물 31개가 전후 바이트 동일, `report-wiki check .` 의 실패 집합이 경로 접두사만 빼면 같다 |

결정 0011 과의 관계 — 분리의 **전 단계**이지 대체가 아니다. 0011 이 "양쪽에 복제한다" 고 한 공통 커널이 바로 `core/` + `common/` 이고, 자리를 따로 두면 복제 경계가 이름으로 보인다.

## 2. 결정 — 아홉 축

| # | 축 | 결정 | 고르지 않은 것 | 왜 |
|---|---|---|---|---|
| ① | 0011 과의 관계 | 분리의 전 단계. M 뒤 · B 앞 | 분리를 대체(0011 을 뒤집는 새 결정) · 분리 뒤 저장소 각각에 적용 | 사용자 선택. 0011 을 그대로 두고 Phase B 를 디렉토리 추출로 만든다 |
| ② | 1차 축과 이름 | mode → 언어 → 성격. 이름 `codewiki` · `term` · `spec` | `mode1 · mode1_5 · mode2`(1.5 가 어색) · `wiki · term · spec`(먼저 골랐으나 `wiki` 가 최상위 · `docs/wiki/` · `runner/wiki/` 세 겹으로 겹쳤다) | 사용자 선택. `codewiki` 는 0011 의 저장소 이름 `codebase-wiki` 와도 가깝다 |
| ② | mode 안 | 언어 폴더 아래 성격축 유지 | 언어 아래 평평하게(파이썬 약 40 파일이 한 폴더, `clang_doc.py` 둘과 `wiki.py`/`wiki/` 충돌) · 파이썬은 언어 폴더 없이 | import 경로와 파일 이름 보존, 충돌 0 |
| ③ | `core` 와 `common` | `core/` = 단계 기계(`pipeline.py` 소비 16 · `measure.py` 7 · `dispatch.py` 진입점 3), `common/` = 유틸(`python.py` 5 · `template.py` 6), `tools/` 는 저장소 유지보수만 | `core` = 기계축 전체 · `common` 하나만 | 사용자 선택. 소비자 수는 grep 실측 |
| ④ | `test` 와 `qa` | `test/` = 모듈 시험 전부(mode 별), `qa/gates/` = 저장소 규약 게이트(인용 · `Any` · 리소스 분리 · 위키 표류), `qa/evals/` = 실행기 측정값 | 시험은 코드 옆에 두고 `qa` = 가로지르는 시험 · `qa` = 측정값만 | 사용자 선택 |
| ⑤ | `resource/` 범위 | 전부 — 프롬프트 · 결함 표 · 파일 템플릿 · `config/*.toml` · 수집기 골든 꼴 · `terms-reading.json` | 실측 자료만 · 실측 자료 + config | 사용자 선택. 결정 0012 의 자리 조항을 고친다 |
| ⑥ | `docs/` | `docs/superpowers/{plans,specs}` 유지, `docs/notes/`(흩어진 분석)와 `docs/research/`(루트 `reports/` · `research_notes/` 흡수) 신설, `remain-process-merged.md` → `docs/handoffs/` | `docs/plans` · `docs/specs` 로 평평하게(superpowers 스킬 기본 경로가 바뀐다) · 루트 폴더는 그대로 | 사용자 선택 |
| ⑦ | 인용과 아카이브 | 기계 경로 치환 + 결정론적 줄 번호 재계산, 아카이브 그대로, 재굽기 없음 | 아카이브도 치환 · 위키와 레코드는 다음 Mode 1 까지 빨강 | 순수 이동은 줄 번호를 지킨다. 2026-08-30 축 이동(`c1e4496`)도 아카이브를 두었다. 재굽기는 2026-09-19 실측 $57 |
| ⑧ | xmldoc 잔재 | 전부 삭제 — `machine/xmldoc.py` · `machine/test_xmldoc.py` · `machine/comments.xml` · `# <include …/>` 블록(62 파일에 표식 686줄) | 이동만 · 파일만 지우고 블록은 둔다 | 사용자 선택. 지운 줄 번호를 기록하므로 재계산이 정확하다 |
| ⑨ | 절차 | 파일마다 받던 파이썬 편집 승인 규칙 폐지(사용자, 2026-10-31). 이번 세션은 문서만 쓴다 | — | 사용자 선택 |

묻지 않고 정한 것(승인 질문에 적어 두었다): `bin/` 은 `~/.zshrc` 가 PATH 에 등록해 루트 그대로 · `config/report.toml` 은 읽는 쪽이 Mode 2 둘(`viz/init.py` · `runner/run_mode2.py`)뿐이라 `resource/spec/config.toml` · `test_wiki.py` 는 `docs/wiki/` 표류를 보는 게이트 · 빈 `docs/prompt/checklist.yaml` 은 삭제 · `OBSERVATION-template.md` 는 그것이 꼴을 주는 samples 옆 · `resources/` 는 사용자가 적은 대로 `resource/` · `split-work/` 는 Phase B 까지 그대로.

## 3. 목표 구조

```
report-builder/
  bin/                     report · report-spec · report-term · report-wiki        (그대로. PATH 에 있다)
  codewiki/                Mode 1
    CLAUDE.md
    python/
      runner/              run_mode1.py · check_shard.py · mode1/(단계) · wiki/(prep · build · check · clang_doc · compdb · paths)
      machine/             normalize · facts · terms_db · verify_citations · survey_plan · warmup · declmap · pycalls ·
                           clang_doc · clangd_refs · reverse_refs · lang_select · file_cache · fix_citation_paths ·
                           codegraph_types · reading_types(신설 — xmldoc.py 에 있던 Term/Terms 형)
      viz/                 render_modules · render_classes · demermaid
    csharp/
      roslyn-dump/         Program.cs · roslyn-dump.csproj · .gitignore
  term/                    Mode 1.5
    CLAUDE.md
    python/runner/         run_mode1_5.py · run_grade.py · term/(collect · quiz · emit)
  spec/                    Mode 2
    CLAUDE.md
    python/
      runner/              run_mode2.py
      viz/                 init · build · check · link_paths · wrap_terms
    typescript/            CLAUDE.md · src/(components · runtime · page.tsx · index.ts · types.ts · theme.css) · svg.mjs · svg.d.mts · lib.mjs
  core/                    CLAUDE.md · pipeline.py · measure.py · dispatch.py
  common/                  python.py · template.py
  tools/                   CLAUDE.md · doctor.py · doctor_packages.py · gen_readme.py · setup.sh · cloud_env.sh(· scrub_local_paths.py 는 git 밖)
  test/
    CLAUDE.md
    codewiki/              machine 시험 10 + test_mode1 · test_run_mode1
    term/                  test_run_mode1_5 · test_run_grade · test_term
    spec/                  test_run_mode2 · test_check · test_init · test_link_paths · test_wrap_terms · test_components · test_graph_math · test_config · svg.test.mjs
    core/                  test_pipeline · test_measure · test_import_isolation · test_dispatch
    common/                test_template · test_templates
    tools/                 test_gen_readme · test_portability
  qa/
    CLAUDE.md
    gates/                 test_docs_citations · test_no_any · test_prompt_resources · test_wiki
    evals/                 README.md · runs/*.json
  resource/
    CLAUDE.md
    codewiki/              prompts/(annotate-symbols · lang-hint · outline-wiki · write-wiki) · faults.toml ·
                           templates/(vitepress.config.mts.tmpl · dot/ ×3) · config.toml · samples/(cpp · csharp-unity · OBSERVATION-template.md) ·
                           terms-reading.json
    term/                  prompts/ask.md
    spec/                  prompts/agent.md · templates/report/(data.ts.tmpl · entry.ts · page.html.tmpl · render.mjs.tmpl · report.tsx.tmpl) · config.toml
  docs/
    superpowers/{plans,specs}   handoffs/(+ remain-process-merged.md)   my.self/   decisions/   overturn/   wiki/   diagrams/
    notes/                 analysis-2026-08-31-cpp-collectors · 2026-09-19-mode1-역대-실측과-패치-이력 · 2패스개선 · runner_presudo
    research/              ← reports/* · research_notes/*
    CLAUDE.md · ai-readiness-map.html · ai-readiness-score.json · (png · pdf)
  split-work/              그대로(Phase B 뒤 삭제). 이 계획의 일회용 스크립트가 reorg/ 에 생긴다
  out/                     git 밖, 그대로
  CLAUDE.md · ARCHITECTURE.md · README.md · package.json · package-lock.json · pyrightconfig.json · tsconfig.json · requirements.txt · skills-lock.json · .gitignore
  .agents/ · .claude/ · .gemini/ · .github/                                     (그대로)

사라지는 것: config/ · evals/ · resources/ · reports/ · research_notes/ · docs/prompt/ · runner/ · machine/ · viz/ ·
      machine/xmldoc.py · machine/test_xmldoc.py · machine/comments.xml · 모든 `# <include …/>` 블록 · 생성 README.md 넷(새 자리에 다시 생성)
```

## 4. 경로 지도

계획서가 싣는 `split-work/reorg/pathmap.py` 가 이 규칙을 TSV 로 만들고, 추적 파일 중 지도에 없는 것이 있거나 두 원본이 한 목적지로 겹치면 거부한다. 적용 순서 — 정확 항목, 디렉토리 접두사(긴 것 먼저), 그대로 두는 것(루트 파일 · `bin/` · `tools/` · `docs/` · `split-work/` · 점 디렉토리).

| 지금 | 목표 | 비고 |
|---|---|---|
| `runner/run_mode1.py` · `runner/check_shard.py` · `runner/mode1/*.py` · `runner/wiki/*.py` | `codewiki/python/runner/…` | `mode1/` 은 이름 그대로 |
| `runner/mode1/prompts/*.md` · `runner/mode1/faults.toml` · `runner/wiki/templates/*` | `resource/codewiki/prompts/` · `resource/codewiki/faults.toml` · `resource/codewiki/templates/` | |
| `machine/*.py`(시험 · xmldoc 제외) · `machine/roslyn-dump/` · `machine/terms-reading.json` | `codewiki/python/machine/` · `codewiki/csharp/roslyn-dump/` · `resource/codewiki/terms-reading.json` | |
| `viz/render_modules.py` · `viz/render_classes.py` · `viz/demermaid.py` · `viz/templates/dot/*` | `codewiki/python/viz/` · `resource/codewiki/templates/dot/` | Mode 1 의 그림 |
| `config/mode1.toml` · `resources/samples/**` · `resources/templates/OBSERVATION-template.md` | `resource/codewiki/config.toml` · `resource/codewiki/samples/` · `resource/codewiki/samples/OBSERVATION-template.md` | |
| `runner/run_mode1_5.py` · `runner/run_grade.py` · `runner/term/*` · `runner/prompts/ask.md` | `term/python/runner/…` · `resource/term/prompts/ask.md` | |
| `runner/run_mode2.py` · `runner/prompts/agent.md` | `spec/python/runner/run_mode2.py` · `resource/spec/prompts/agent.md` | |
| `viz/{__init__,init,build,check,link_paths,wrap_terms}.py` · `viz/src/**` · `viz/svg.mjs` · `viz/svg.d.mts` · `viz/lib.mjs` · `viz/templates/report/*` · `config/report.toml` | `spec/python/viz/` · `spec/typescript/src/` · `spec/typescript/` · `resource/spec/templates/report/` · `resource/spec/config.toml` | |
| `runner/pipeline.py` · `runner/measure.py` · `runner/dispatch.py` · `runner/__init__.py` | `core/` | |
| `tools/python.py` · `tools/template.py` | `common/` | `tools/` 에는 doctor · doctor_packages · gen_readme · setup.sh · cloud_env.sh 가 남는다 |
| `machine/test_*.py`(10) · `runner/test_mode1.py` · `runner/test_run_mode1.py` | `test/codewiki/` | |
| `runner/test_run_mode1_5.py` · `runner/test_run_grade.py` · `test/test_term.py` | `test/term/` | |
| `runner/test_run_mode2.py` · `test/test_{check,init,link_paths,wrap_terms,components,graph_math,config}.py` · `test/svg.test.mjs` | `test/spec/` | |
| `runner/test_{pipeline,measure,import_isolation}.py` · `test/test_dispatch.py` | `test/core/` | |
| `tools/test_template.py` · `test/test_templates.py` | `test/common/` | `test_templates` 는 `common/template.py` 를 두 리소스 묶음에 대어 본다 |
| `tools/test_gen_readme.py` · `test/test_portability.py` | `test/tools/` | |
| `test/test_docs_citations.py` · `test/test_no_any.py` · `test/test_prompt_resources.py` · `test/test_wiki.py` | `qa/gates/` | |
| `evals/README.md` · `evals/runs/*.json` | `qa/evals/` | |
| `reports/*.md` · `research_notes/**` | `docs/research/` | 하위 폴더 이름 유지 |
| `docs/analysis-2026-08-31-cpp-collectors.md` · `docs/2026-09-19-mode1-역대-실측과-패치-이력.md` · `docs/2패스개선.md` · `runner/runner_presudo.md` | `docs/notes/` | |
| `remain-process-merged.md` | `docs/handoffs/remain-process-merged.md` | 2026-08-31 자 낡은 할일. 아카이브 |
| `runner/CLAUDE.md` · `machine/CLAUDE.md` · `viz/CLAUDE.md` · `viz/src/CLAUDE.md` | `core/CLAUDE.md` · `codewiki/CLAUDE.md` · `spec/CLAUDE.md` · `spec/typescript/CLAUDE.md` | 그 뒤 재구성(§11) |
| `runner/README.md` · `machine/README.md` · `viz/README.md` · `tools/README.md` | 삭제. 파이썬 디렉토리 아홉에 다시 생성 | `tools/gen_readme.py` |
| `machine/xmldoc.py` · `machine/test_xmldoc.py` · `machine/comments.xml` · `docs/prompt/checklist.yaml` | 삭제 | |

설계 커밋 뒤 Phase K 가 더한 파일(🔵 `6c4009d`) — `machine/manifest.py` · `runner/mode1/seal.py`(Mode 1 봉인)는 `codewiki/python/machine/` · `codewiki/python/runner/mode1/`, `machine/evidence.py` · `machine/contract_types.py`(Mode 1.5 와 2 가 읽는다)는 `common/`, 그 시험은 `test/codewiki/` · `test/common/`, `tools/gen_contract*.py` 는 `tools/` 에 그대로(시험은 `test/tools/`), `contracts/` 와 `docs/contract-mode1-artifacts.md` 는 그대로(0011 이 계약 경로를 두 저장소에서 그 이름 그대로 쓴다). 계획서의 경로 지도가 이것들을 이름으로 적고, 그 뒤 생긴 다른 파일이 있으면 실패하므로 새 파일은 의식해서 둔다.

## 5. 삭제

| 무엇 | 수(🔵 2026-10-31) | 귀결 |
|---|---|---|
| `# <include file="machine/comments.xml" …/>` 블록(표식 + 뜻 줄 + 선택적 의존 줄) | 62 파일 표식 686줄 | 블록 아래 줄 번호가 올라간다. 파일마다 지운 줄 번호를 기록해 인용을 정확히 재계산한다 |
| `machine/xmldoc.py` | 1 | `terms_db.py` · `test_terms_db.py` 가 `Terms` 를 import 한다 → TypedDict 셋 `Use` · `Term` · `Terms` 를 새 `machine/reading_types.py` 로 그대로 옮기고 import 두 줄을 한 줄 → 한 줄로 바꾼다 |
| `machine/test_xmldoc.py` · `machine/comments.xml` | 2 | 시험 수가 xmldoc 시험만큼 준다 |
| `docs/prompt/checklist.yaml` | 1(0 바이트) | `docs/CLAUDE.md` 의 행 삭제 |
| `runner/README.md` · `machine/README.md` · `viz/README.md` · `tools/README.md` | 4 | `tools/gen_readme.py` 가 새 자리에 다시 만든다 |

## 6. 실행 중 지키는 불변식

1. **줄 수 보존.** 전부터 있었고 시험 파일이 아닌 모든 이동 파일에서 내용 수정은 한 줄 → 한 줄 치환(`sys.path` 깊이 · 경로 문자열 · import 개명)과 기록된 블록 삭제뿐이다. 삽입은 없다. 이것이 인용 재계산을 어림이 아니라 함수로 만든다.
2. **아카이브 그대로.** `docs/handoffs/` · `docs/superpowers/` · `docs/my.self/` · `docs/decisions/` · `docs/overturn/` 의 옛 경로는 두 곳(이 설계가 더하는 재개 문서 변경 기록 행과 나침반 행)만 빼고 손대지 않는다.
3. **산출물 바이트 동일.** `split-work/capture.sh` 의 산출물 31개(프롬프트 · 뼈대 · VitePress 설정 · DOT · `report.html`)가 전후 같다.
4. **커밋마다 초록.** Task 마다 게이트 여섯이 기준선과 같은 상태로 끝난다(알려진 빨강 둘은 알려진 이유로 빨강, 그 밖에 빨강 없음).
5. **동작 불변.** §5 의 import 줄과 §9 의 경로 상수 밖에는 함수 본문을 바꾸지 않는다.

## 7. 인용과 식별자 재작성

| 대상 | 무엇을 | 어떻게 |
|---|---|---|
| `docs/wiki/*.md`(`파일:줄` 인용 203건, 🔵) | 경로는 지도로, 줄 번호는 파일별 지운 줄 기록으로 | `split-work/reorg/remap_citations.py` |
| `resource/codewiki/terms-reading.json`(`where` 3,053 · id 1,318 · `uses` 1,735, 🔵) | `where` 와 `uses[].where`(path:line) · `module`(점 또는 빗금 디렉토리) · 레코드 id · `uses[].to` · `depends_on`(파이썬 파일 지도에서 끌어낸 점 표기 모듈 id, 빗금 파일 id 는 파일 지도) | 같은 스크립트. 변경 없이 읽고 쓴 결과가 바이트 동일함을 먼저 확인한 뒤 같은 꼴(`indent=1` · `ensure_ascii=False`)로 다시 쓴다 |
| `contextDocs()` 의 컨텍스트 문서(루트 · 모듈 `CLAUDE.md` · `README.md` · `ARCHITECTURE.md` · `.claude/CLAUDE.md` · 에이전트 셋 · 스킬 셋) | 경로와 `파일:줄` 인용 | 같은 스크립트. 그 뒤 §11 의 손 편집 |
| `docs/diagrams/*.dot` · `qa/evals/README.md` · `split-work/README.md` · `split-work/*.py` · `split-work/*.sh` · `.gemini/PythonRule.md` | 경로 | 같은 스크립트 |
| 코드와 설정 | 경로 문자열 · import 문 · `sys.path` 항목 | §9 |

mode 사이로 갈라지는 디렉토리 이름의 id(`runner` · `viz` · `tools` · `test`)는 그대로 두고 스크립트 보고에 적는다. L1/L2/L3 검사는 id 가 아니라 `where` 를 읽는다. 위키 장 파일 이름(`machine-*.md` · `runner-*.md` · `viz-*.md`)은 다음 Mode 1 실행까지 옛 이름이다.

인용한 줄 자체가 지워진 경우(include 표식을 가리켰던 경우)는 조용히 옮기지 않고 보고한다. 🔵 그런 경우는 없을 것으로 본다 — `where` 는 선언 줄을 가리키고 선언 줄은 블록 아래에 있다.

## 8. import 와 `sys.path` 규칙

이동 뒤 최상위 패키지 — `codewiki` · `term` · `spec` · `core` · `common` · `tools`(`test` · `qa` 는 import 하지 않는다).

| 지금 | 뒤 | 어디에 |
|---|---|---|
| `from tools.template import …` · `from tools.python import …` | `from common.template import …` · `from common.python import …` | 11 문장 |
| `from runner.dispatch import …` | `from core.dispatch import …` | `bin/*` 셋 · `test_dispatch` |
| `import pipeline` · `import pipeline as P` · `from pipeline import …` · `import measure` · `from measure import …` | `from core import pipeline` · `from core import pipeline as P` · `from core.pipeline import …` · `from core import measure` · `from core.measure import …` | 실행기 · `check_shard.py` · `mode1/lang.py` · 시험 · 게이트 |
| `from runner.wiki.X import …` · `from runner.wiki import prep` | `from codewiki.python.runner.wiki.X import …` | 13 문장 |
| `from runner.term.X import …` · `import runner.term.quiz` | `from term.python.runner.term.X import …` · `import term.python.runner.term.quiz` | 4 문장 |
| `from viz.{init,check,link_paths,wrap_terms} import …` | `from spec.python.viz.… import …` | 시험 · `run_mode2.py` |
| `from viz.render_modules import …` | `from codewiki.python.viz.render_modules import …` | `render_classes.py` · `test_templates.py` |
| `from xmldoc import Terms` | `from reading_types import Terms` | `terms_db.py` · `test_terms_db.py` |
| `machine/` 안의 평평한 형제 import(`import normalize` · `from codegraph_types import …` …)와 `runner/` 폴더 안의 것(`run_grade.py` 의 `import run_mode1_5`) | 그대로 | 파일 자신의 디렉토리가 `sys.path` 에 있다는 전제가 그대로다 |

`ROOT` 계산 — 파일은 `os.path.dirname(…)` 사슬로 저장소 뿌리를 구한다. 사슬 길이는 파일의 깊이 변화만큼 는다(`runner/x.py` → `codewiki/python/runner/x.py` 는 +2, `runner/mode1/x.py` +2, `machine/x.py` · `viz/x.py` +2, `core/` · `common/` 0, 시험과 게이트 +1). 계획서는 모든 `.py` 에서 사슬 길이와 경로 깊이를 대조하는 검사기를 싣는다.

디렉토리를 이름으로 적은 `sys.path` 항목(`os.path.join(ROOT, "runner")` · `"machine"`)은 그 파일이 import 하는 모듈이 이제 사는 디렉토리로 바꾼다 — Mode 1 파일은 `codewiki/python/runner` 와 `codewiki/python/machine`, Mode 1.5 는 `term/python/runner`, Mode 2 는 `spec/python/runner` 와 `spec/python/viz`, `run_mode1_5.py` 가 만드는 자식 스크립트는 `term/python/runner`, `tools/gen_readme.py` 는 `codewiki/python/machine`.

`pyrightconfig.json` — `include` 는 코드 루트 여섯 + `test` + `qa`, `exclude` 에 `codewiki/csharp` 와 `spec/typescript` 추가, `extraPaths` 는 `.` · `runner/` 폴더 셋 · `codewiki/python/machine` · `codewiki/python/viz` · `spec/python/viz`. 🔵 지금 `test/` 는 `include` 에 없다 — 그 16 파일이 처음으로 형 검사를 받는다. 거기서 나는 오류는 사소하면 고치고 아니면 파일 이름으로 제외하고 계획서 최종 보고에 적는다.

## 9. 메타 파일과 게이트

| 파일 | 변경 |
|---|---|
| `pyrightconfig.json` | §8 |
| `tsconfig.json` | `include` → `spec/typescript/src/**/*.ts` · `spec/typescript/src/**/*.tsx` |
| `package.json` | `pretest` → `node spec/typescript/lib.mjs` |
| `spec/typescript/lib.mjs` | `entryPoints: ["spec/typescript/src/index.ts"]`(outfile `.tmp/lib.mjs` 그대로) |
| `spec/python/viz/build.py` · `check.py` | esbuild alias 와 생성 tsconfig `paths` → `spec/typescript/src/index.ts` · `types.ts` · `spec/typescript/svg.mjs`, `theme.css`, `runtime/term-graph.ts`, `TEMPLATES` → `resource/spec/templates/report` |
| `spec/python/viz/init.py` · `spec/python/runner/run_mode2.py` | `resource/spec/config.toml` · `resource/spec/prompts` · 단계 스크립트는 `spec/python/viz/` 아래 |
| `term/python/runner/run_mode1_5.py` | `term/python/runner/term/<name>` · `term/python/runner/run_mode1_5.py` · `resource/term/prompts` · 자식 스크립트의 `sys.path` |
| `codewiki/python/runner/mode1/context.py` | `PROMPT_DIR` → `resource/codewiki/prompts` · `CONFIG_PATH` → `resource/codewiki/config.toml` · `FAULTS_PATH` → `resource/codewiki/faults.toml` · `reading_path()` 의 자기호스팅 갈래 → `resource/codewiki/terms-reading.json`(대상 저장소 갈래 `docs/codegraph/` 는 그대로) |
| `codewiki/python/runner/mode1/terms.py` · `machine_stage.py` · `wiki/{build,check,prep}.py` | 자식 프로세스 대상 → `codewiki/python/machine/*.py` · `codewiki/python/viz/*.py` · `codewiki/python/runner/wiki/*.py`, `TEMPLATES` → `resource/codewiki/templates` |
| `codewiki/python/viz/render_modules.py` · `render_classes.py` | `TEMPLATES` → `resource/codewiki/templates/dot` |
| `bin/report-wiki` · `report-term` · `report-spec` | `from core.dispatch import run_dispatch`, 명령표 → 새 스크립트 경로 |
| `tools/gen_readme.py` | `DIR_ROLE` 열쇠는 파이썬 디렉토리 아홉, `BANNER` 명령, `sys.path` 의 `machine` → `codewiki/python/machine` |
| `tools/setup.sh` | `node spec/typescript/lib.mjs` |
| `.github/workflows/docs-gates.yml` | `qa/gates/test_docs_citations.py qa/gates/test_no_any.py`, `gen_readme.py --check` 에 디렉토리 아홉 |
| `.gitignore` | `split-work/reorg/out/` 추가 |
| `qa/gates/test_prompt_resources.py` | `CODE_TOPS = ("codewiki", "term", "spec", "core", "common", "tools")`, 템플릿 glob `resource/*/templates/**`, 프롬프트 glob `resource/*/prompts/*.md` 와 `resource/*/faults.toml`, mode 별 실행기 자리 표, `from core import pipeline as P` |
| `qa/gates/test_no_any.py` | `COVERED` 경로를 지도로 |
| `qa/gates/test_docs_citations.py` | `contextDocs()` → 새 모듈 `CLAUDE.md` 묶음(§11) |
| `split-work/capture.sh` · `capture.py` · `split_reading.py` | 경로를 지도로 |
| `~/.claude/skills/spec-review-dashboard/SKILL.md` · `term-benchmark/SKILL.md`(저장소 밖) | 저장소 안 사본과 같은 경로 치환 — 사본이 원본에서 표류하지 않게 |

## 10. 검증

```bash
# 기준선(Task 0)과 Task 마다
.venv/bin/python -m pytest -q                    # 통과 수 = 기준선 − xmldoc 시험. 알려진 빨강 둘만
npm test                                         # 8
npm run typecheck                                # 0 errors
npm run typecheck:py                             # 0 errors
.venv/bin/python tools/gen_readme.py --check codewiki/python/runner codewiki/python/machine codewiki/python/viz \
    term/python/runner spec/python/runner spec/python/viz core common tools
npm run doctor
split-work/capture.sh "$PWD" split-work/after-reorg && diff -r split-work/before-reorg split-work/after-reorg   # 비어 있어야
.venv/bin/python bin/report-wiki prep . && .venv/bin/python bin/report-wiki check .   # L1/L2 수가 기준선과 같다
```

그 위에 — `report-spec` · `report-term` · `report-wiki` 를 인자 없이 PATH 에서 부르면 사용법 줄이 나온다. `git log --follow codewiki/python/machine/normalize.py` 가 이동 전 이력을 보인다.

## 11. 문서 재구성

| 목표 | 원본 | 경로 치환 밖의 내용 변경 |
|---|---|---|
| 루트 `CLAUDE.md` | 자신 | 나침반 표(모듈 문서) · "성격축 셋" 절은 "축 셋 — mode · 언어 · 성격" 으로 · 아키텍처 트리 · "리소스와 코드를 가른다" 규약(자리 → `resource/<mode>/`) · 명령 블록 · 게이트 표의 명령 · 진입점 표의 경로 · "파이썬이 본체" 표 · 스킬 주의문 |
| `codewiki/CLAUDE.md` | `machine/CLAUDE.md` | 제목과 머리말은 Mode 1, "무엇이 여기 있나" 표에 `runner/CLAUDE.md` · `viz/CLAUDE.md` 가 들고 있던 Mode 1 의 runner · viz 행 추가, xmldoc 행 삭제, Owns · 의존 표에 `core/` 와 `resource/codewiki/` |
| `core/CLAUDE.md` | `runner/CLAUDE.md` | 단계 기계 · 양방향 자식 프로세스 절 · 흐름을 미리 짓는 절은 유지, Mode 1 단계 추가 패턴은 `codewiki/CLAUDE.md` 로, Mode 1.5 줄은 `term/CLAUDE.md` 로, "common/" 짧은 절 추가 |
| `spec/CLAUDE.md` | `viz/CLAUDE.md` | Mode 1 그림 절(render · demermaid → `codewiki/CLAUDE.md`) 삭제, 렌더 경로 · SVG 인라인 규칙 · init 의 slug 검증 · check 의 용어 대조는 유지 |
| `spec/typescript/CLAUDE.md` | `viz/src/CLAUDE.md` | 경로만 |
| `term/CLAUDE.md` · `qa/CLAUDE.md` · `resource/CLAUDE.md` | 신설, 짧게 | 무엇이 사는가 · 누가 읽는가 · 게이트 목록 / 리소스 규칙(0012 + 0014) |
| `test/CLAUDE.md` | 자신 | 다시 쓴다 — mode 별 시험, 게이트는 `qa/` 로, 명령 |
| `tools/CLAUDE.md` | 자신 | `python.py` · `template.py` 행 삭제 |
| `docs/CLAUDE.md` | 자신 | `prompt/` 행 삭제, `notes/` · `research/` 행 추가 |
| `ARCHITECTURE.md` · `README.md` | 자신 | §1 흐름도와 §4 층 그림의 노드 이름, 명령 블록, "무엇이 어디에 사는가" 표 |
| `README.md` 아홉 | 생성 | `tools/gen_readme.py` |

## 12. 미결(이 설계가 정하지 않는 것)

- `6c4009d` 뒤에 생기는 최상위 디렉토리 — 계획 실행 때 분류한다(기본: 루트 그대로).
- `machine/test_survey_plan.py::test_이_저장소_실측` — 이동 뒤 층 분포가 또 바뀐다. 루트 `CLAUDE.md` 의 규칙("기대값을 고치기 전에 기계마다 다른 원인부터 본다")이 그대로다.
- 처음 형 검사를 받는 시험 파일 16개(§8).
- `codewiki/` 안의 `runner/mode1/` 개명 — 보류. 한다면 별도 커밋.

## 13. 새 구조 공개(설계 규율 §2.5, 🔵 2026-10-31)

1. 구현자 — `core/` 3 파일 · `common/` 2 파일 · `qa/gates/` 4 파일 · `resource/` 43 파일(프롬프트 6 · 결함 표 1 · 템플릿 9 · 설정 2 · 골든 꼴 24 · 레코드 1).
2. 소비자 — `pipeline.py` 16 파일 · `measure.py` 7 · `dispatch.py` 진입점 3 · `python.py` 5 · `template.py` 6. 리소스 소비자는 단계 클래스(`prompt_names`)와 `render_file` 호출처.
3. 삭제 시험 — `core/` · `common/` 이 없으면 공유 파일 다섯이 속할 mode 가 없어 지금처럼 `runner/` · `tools/` 에 섞여 남는다. 0011 의 Phase B 는 바로 이 다섯을 둘째 저장소에 복제해야 한다.
4. 계획 문서와의 관계 — 0011 안(M 과 B 사이의 전 단계).
