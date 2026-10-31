# Handoff — rev.4 분리 계획 실행 재개 (2026-10-24, lossless · 클라우드 재개판)

> **이 문서가 다음 세션의 유일한 진입점이다.** Mode 1 / Mode 1.5+2 두 저장소 분리 계획 rev.4 를 서브에이전트 주도로 실행하는 중이다. **Phase R 은 끝났다**(R1~R10). Phase A 는 A1 · A4 가 끝났고 A2 · A3 가 남았다. 그 뒤가 Phase K · M 이다.
> **작성**: 2026-10-24 Mac 세션(R1) → 클라우드(R1 검토 ~ R4) → **Mac 세션(R4 검토 ~ R10 · A1 · A4)** → 사용자 지시로 **클라우드에서 다시 시작**한다. 브랜치 `survey-per-file-2pass` · HEAD `5837c32`(이 문서 커밋 직전).
> **대체하는 것**: 같은 파일의 이전 판. 이전 판의 §5 "바로 다음"(R4 검토 · R5 구현자)은 끝났다.
> ⚠ 시작할 때 `git fetch origin && git checkout survey-per-file-2pass && git pull origin survey-per-file-2pass` → `git log --oneline -8` · `git status --short` 를 다시 잰다. **claude.ai 프로젝트 스레드로 이어가면 §0.1 부터.**

## 0. 한눈에 (TL;DR)

- **무엇을**: `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`(rev.4) 의 Phase **R → A → K → M** 을 이 저장소에서 실행해 `main` 에 fast-forward 한다. 두 저장소로 가르는 B · C 와 위키 재굽기 E 는 그 뒤 별 세션.
- **진척**: R1~R10 ✅ · R9 보강 ✅(`0ba79a3` `a7a66c4` `3c4c4e8` `bae47de` `44b55c5` · 재검토 Ready: Yes · 문서 정리 `128c25b`) · R10 품질 ✅ + 보강 `6e9cc72` · A1 ✅ · A4 ✅ · R11 폐기(→ R12, 시험 커밋 `8d71d38` 만 남김) · R12 ✅(R12a `a6e484d` + 보강 `46b9f5b` · b `60c500c` · c `644f6f0` · d `aae87e4` · e `47b8f56` · f `22d67e0` `082a1d3` · 결정 0012 확정) · A2 ✅ `f1355c7` · A3 ✅ `77fe047` · **K ✅**(K1 `5c88f2d` · K2 `813ffb1` · K2b `3691fe7` · K3 `cefaed9` · K4 `88c6d52` · K5 `e171e9d` · 생산자 검토 보강 `8945e62` · K6 `f223170` · K7 `fd3b8d5` · 상태 줄 `bda0584` · K7b `ec7314b` · K8 `59674d0` · 소비자 검토 보강 `90f5843` `82c10b0`) · **M1 ✅ · M2 ⬜(사용자 승인 대기)**.
- **바로 다음**(§5 순서): (0) §6 으로 `split-work/` 와 `before/` 준비 (1) ~~R9 보강 · R10 검토~~ 끝 ~~(2) R12 · (3) A2 · A3~~ 끝 ~~(4) Phase K~~ 끝 (5) M1 ✅ · **M2 — `main` 에 미는 것은 사용자에게 묻는다**.
- **방법**: Task 마다 구현자 1 → spec 검토 → 품질 검토 1. 한 Task 한 커밋(검토 보강은 별 커밋). spec 검토가 "계획서 코드 블록이 글자 그대로 들어갔는가" 면 오케스트레이터가 기계 대조로 한다. **본체 `.py` 는 사용자가 diff 를 보고 승인한다**(§7 — 클라우드는 질문 창).
- **모델(사용자 동의 2026-10-24)**: 오케스트레이터 Opus 5.5 · 구현자 `sonnet` · 검토자 `opus`. 여러 파일을 엮거나 설계 판단이 드는 Task(K2 · K3 · K6 · R11)는 구현자도 `opus`.
- **정본**: rev.4(Task 본문) · 정정표(§4) · 이월 사항(§4.2) · 대조 도구 `split-work/`(§6) · 원격 세션용 스킬 사본 `.claude/skills/`(§3).

## 0.1 claude.ai 프로젝트 스레드로 이어갈 때 (사용자 결정 2026-10-24)

공식 문서(code.claude.com — claude-projects · cloud-environments)에 따르면 **프로젝트 스레드는 일반 클라우드 세션과 다르다.** 다음은 확인된 차이와 대응이다.

| 스레드에서 | 대응 |
|---|---|
| 기본 브랜치(`main`)에서 **새 브랜치를 딴다**(따로 말하지 않으면) | 지금까지의 작업은 전부 `survey-per-file-2pass` 에 있다 — 시작하자마자 `git fetch origin && git checkout survey-per-file-2pass && git pull origin survey-per-file-2pass`. 새 브랜치를 따지 않고 여기에 커밋 · push 한다 |
| 저장소 `.claude/settings.json` 의 **훅이 돌지 않는다** — `tools/setup.sh`(`.venv` · `node_modules` · `.tmp/lib.mjs` · doctor)가 자동으로 안 돈다 | 시작할 때 `bash tools/setup.sh` 를 직접 돌린다. Graphviz 는 프로젝트의 Cloud environment 설정 스크립트(`tools/cloud_env.sh` 를 붙여 넣은 것)가 깐다 |
| 루트 `CLAUDE.md` · `.claude/CLAUDE.md` 만 읽힌다 — **하위 폴더 `CLAUDE.md` 는 안 읽힌다** | `runner/` · `viz/` · `machine/` · `tools/` · `test/` · `docs/` 를 고치기 전에 그 폴더의 `CLAUDE.md` 를 직접 읽는다. 서브에이전트 brief 에도 "해당 폴더의 CLAUDE.md 를 먼저 읽어라" 를 넣는다 |
| 저장소 `.claude/skills/` · `.claude/agents/` · 플러그인 설정이 **안 읽힌다** | superpowers 는 Project settings > Plugins 에서 켠다(사용자). 스킬 사본 다섯(`personal-commit-messages` 등)은 claude.ai 계정의 스킬로 켜야 보인다 — 안 켜도 커밋 형식은 루트 `CLAUDE.md` 와 §7 에 글자로 있다 |
| 저장소 권한 규칙이 적용되지 않는다 · 스레드는 auto mode | 승인 창은 **그 스레드 안에** 뜨고 스레드는 거기서 기다린다. 프로젝트 대화에서 "진행해" 라고 해도 스레드에 닿지 않는다. 본체 `.py` 승인(§7)도 스레드 안의 질문 창으로 받는다 — `AskUserQuestion` 은 **이 claude.ai/code 원격 세션에서는 떴다(5회 — R2 · R1 수정 · R2 보강 · R4 승인, M2)**. 프로젝트 스레드에서 뜨는지는 문서로 확인하지 못했다. 안 뜨면 diff 경로와 요약을 남기고 멈춰 사용자 답을 기다린다 |
| `env` 가 적용되지 않는다 | 이 작업에 필요한 환경변수는 없다(`TOOLS_ROOT` 는 `split-work/capture.sh` 가 스스로 잡는다) |

**클라우드 세션 실측(2026-10-24 13:40 UTC, 넘김 문서 `HANDOFF-2026-10-24-cloud-thread-to-local.md` §3).** ⚠ 이 세션이 프로젝트 스레드인지는 확인하지 못했다 — R1 검토 ~ R4 를 한 **같은 claude.ai/code 원격 세션**이 컨테이너 재시작으로 이어진 것이고, 프로젝트 지시문은 자동으로 들어오지 않아 사용자가 대화에 붙여 넣었다. 그래서 아래는 위 표가 틀렸다는 뜻이 아니라 "이 종류의 세션에서는 이렇다" 는 기록이다.

| 위 표의 주장(프로젝트 스레드) | 이 원격 세션에서 본 것 |
|---|---|
| 저장소 훅이 돌지 않는다 | SessionStart 훅이 **돌았다** — 시작(`startup`)과 재시작(`resume`) 둘 다 `tools/setup.sh` 출력이 떴다 |
| 하위 폴더 `CLAUDE.md` 는 안 읽힌다 | 그 폴더의 파일을 읽거나 고칠 때 하네스가 그 폴더의 `CLAUDE.md` 를 **끼워 넣었다**(`runner/` · `tools/` · `docs/`). 미리 읽히지는 않는다 |
| 저장소 `.claude/skills/` 가 안 읽힌다 | `git pull` 뒤 저장소 사본 다섯이 스킬 목록에 **나타났고** 실제로 불러 썼다(`lossless-handoff`) |
| `AskUserQuestion` 이 뜨는지 모른다 | **떴다**(5회) |
| 스레드는 auto mode | 이 세션도 auto mode — `Edit` 에 권한 창이 없어 본체 승인은 질문 창으로 받았다 |

**결론**: 훅 · 저장소 스킬 · 하위 `CLAUDE.md` 는 **세션 종류에 따라 다르다.** 시작 절차(브랜치 체크아웃 · `bash tools/setup.sh` · 하위 `CLAUDE.md` 직접 읽기)는 어느 쪽이든 해가 없으니 그대로 지킨다. 시작 때 `git fetch origin` 은 **인자 없이 전체**로 받고 `git branch -r` 로 원격 가지를 한 번 본다(클라우드 스레드가 처음에 한 가지만 받았다가 사용자가 짚었다).

**프로젝트 지시문(Project settings > Memory > Project instructions 에 붙여 넣는다 — 새 스레드마다 받는다):**
```text
이 프로젝트의 작업은 저장소 report-builder 의 브랜치 survey-per-file-2pass 에서 이어간다.
- main 에서 새 브랜치를 따지 않는다. 시작하면 git fetch origin && git checkout survey-per-file-2pass && git pull origin survey-per-file-2pass 를 하고 거기에 커밋 · push 한다.
- 저장소 훅이 돌지 않는다. 시작하면 bash tools/setup.sh 를 먼저 돌린다.
- 재개 진입점은 docs/handoffs/RESUME-2026-10-24-split-rev4-execution.md 하나다. §0 → §0.1 → §1 → §6 → §5 순서로 간다.
- 하위 폴더의 CLAUDE.md 는 자동으로 읽히지 않는다. 그 폴더를 고치기 전에 직접 읽는다.
- 커밋은 [tag] : 한국어 제목 한 줄, 본문 · 트레일러 없음, 파일을 이름으로 git add 한다(루트 CLAUDE.md).
- 본체 .py 는 diff 를 보여 승인받은 뒤 적용한다(재개 문서 §7). main 에 push 하기 전에는 묻는다.
```

## 1. 상태 (Mac 실측 2026-10-24 — 다시 잰다)

```
HEAD 5837c32  origin 과 같음 · 작업 트리 깨끗(이 문서 커밋 전)

Phase R (fdb1c3a 분리 전 기준 이후)
  53ddd2f 9fa0f41 e9ddfc3 59a43fb  R1 tools/template.py + 검토 보강 + README
  22c80a3 83eb828                  R2 PromptResource + 보강
  f87e877 eeb4976 d00388a          R4 mode1 프롬프트 넷 + 시험 + removesuffix(사용자 승인)
  b627831 95f9758                  R5 runner/prompts/{agent,ask}.md + 시험 셋
  283aec3 a3ac974                  R6 템플릿 일곱 + str(lang) 수정 · test/test_templates.py
  3665cc5 850a6a0                  R7 config/{mode1,report}.toml + 시험 강화
  36fb98d 83c22a1 116bd73          R9 test/test_prompt_resources.py + 문서 정리 + ARCHITECTURE
  d598822 5837c32                  R10 남은 문구 → 리소스 + 검토 이월 본체 정리
Phase A
  1325398                          A1 결정 0011
문서
  ddeef75 b6bd0a4 082d3a9 b74af29 7cacbde 4d7c70d d6286be   rev.4 · 이 문서의 판들
사용자
  7dfc33a                          skill-creator 삭제
```

게이트(Mac, `out/` 있음 · HEAD `5837c32`):

| 게이트 | 값 |
|---|---|
| `.venv/bin/python -m pytest -q` | **709 통과 · 2 실패 · 19 건너뜀**. 실패 둘은 알려진 빨강 — `machine/test_survey_plan.py::test_이_저장소_실측`(층 분포 고정값 · 기계마다 다름) · `test/test_wiki.py::test_check_는_통과를_통과로_보고한다`(위키 표류) |
| `npm test` | 8 통과 |
| `npm run typecheck:py` | 0 errors |
| `npm run typecheck` | 통과 |
| `gen_readme.py --check machine runner viz tools` | 4개 일치 |
| `test/test_prompt_resources.py` | 3 통과 |
| 고정 출력 31개 (`capture.sh`) | Phase R 전(`e9ddfc3` 이전)과 바이트로 같다 — R5 · R6 · R7 · R10A · R10B 적용 때마다 다시 쟀다 |

`out/` 이 없는 새 클론이면 층 분포 시험은 건너뛰고 위키 시험은 `codegraph.json 이 없다` 로 실패한다. `.venv/bin/python bin/report-wiki prep .` 을 먼저 돌리면 위 표가 된다.

## 2. Task 상태표

| Task | 내용 | 상태 | 근거 · 편차 |
|---|---|---|---|
| R1 | `tools/template.py` | ✅ spec ✅ 품질 ✅ | `{{이름…` 꼴 잔재도 예외(`STRAY`) |
| R2 | `PromptResource` 믹스인 | ✅ spec ✅ 품질 ✅ | 틀린 절 표식 · 상대 `prompt_dir` 은 `ValueError` |
| R3 | 옮기기 전을 찍는다 | ✅ 커밋 없음 | 도구는 §6 |
| R4 | Mode 1 프롬프트 넷 → `runner/mode1/prompts/` | ✅ spec ✅ 품질 ✅ | `hint_prompt` 는 `.removesuffix("\n")`(사용자 승인) |
| R5 | Mode 1.5 · 2 → `runner/prompts/` | ✅ spec ✅ 품질 ✅(시험 셋 보강) · 사용자 승인 | 정정 ⑤ 는 K6 으로 옮겼다(§4) |
| R6 | 템플릿 일곱 → `viz/templates/{report,dot}/` · `runner/wiki/templates/` | ✅ spec ✅ 품질 ✅(시험 + `str(lang)` 사용자 승인) · 사용자 승인 | 범례는 `"\n" + render_file(…).removesuffix("\n")`. `render.mjs.tmpl` 은 계획대로 들여쓰기를 뗐다(빌드 중 지워지는 임시 파일 바이트만 다르고 HTML 은 같다) |
| R7 | 설정값 → `config/*.toml` | ✅ spec ✅ 품질 ✅ · 사용자 승인 | `run_mode2.py --model` 도움말은 `(기본: %(default)s)`(사용자 결정) |
| R8 | 옮긴 뒤 대조 | ✅ 커밋 없음 | 31 동일 |
| R9 | 게이트 시험 + Phase R 문서 정리 + 보강 | ✅ `36fb98d` `83c22a1` `116bd73` + 보강 `0ba79a3` `a7a66c4` `3c4c4e8` `bae47de` `44b55c5` · spec ✅ · 품질 With fixes → 보강 ✅(로컬 세션 2026-10-24) · 재검토 ✅ Ready: Yes(Important 0) · 문서 정리 `128c25b` · 사용자 승인(본체 셋) | I1 — 긴 글 게이트가 f-문자열을 한 덩어리로 잰다 · HTML 뼈대는 `viz/templates/report/page.html.tmpl`. I2 — 템플릿을 문자열 상수와 같은 값으로 찾고 basename 겹침을 본다. M2 확정 — 게이트를 `machine` · `tools` 까지 · `tools/doctor.py` 의 `python -c` 스크립트는 `tools/doctor_packages.py`. 31 동일 · `doctor` 표 동일. "줄 번호 ≤ 파일 끝" 인용 검사는 넣지 않았다 — 루트 `CLAUDE.md` 의 `runner/run_mode1.py:414`(위키가 낡은 줄을 인용한다는 설명 문장)가 걸린다 |
| R10 | 남은 문구 → 리소스(A) · 검토 이월 본체 정리(B) | ✅ `d598822` · `5837c32` · 사용자 승인 · 품질 ✅(With fixes) → 보강 `6e9cc72` · 사용자 승인 | 새 절 — `annotate-symbols.md` 12(`batch-symbol` `batch-symbol-no-deps` `batch-dep` `batch-dep-no-means` `batch-no-deps` `pass2-dep` `pass2-no-deps` `fix-missing` `fix-malformed` `fix-schema` `fix-where` `fix-coverage`) · `write-wiki.md` 3(`page-no-symbols` `lower-page` `no-lower-pages`, 본문은 `main`). `FIX` 는 이름 · 형 그대로, 클래스 뒤 모듈 수준 대입 한 번(`survey.py` 끝). 고정 31 + 경계 입력 128 동일. 검토 보강 — 아래층 장 목록 절(`write-wiki#lower-page`)을 지나는 시험(그전에는 자리 이름이 어긋나도 통과 · 실제로는 둘째 층에서 러너가 죽는다) · `FIX` 가 빈 줄이 아닌 한 줄인지 · 심볼 줄 들여쓰기를 줄 경계로. 돌연변이 셋을 넣어 잡히는 것 확인. 독스트링 셋과 `wiki.py` 호출 꼴 |
| R11 | 목록 밖 LLM 글 옮기기 | **폐기 → R12** · 시험 커밋 `8d71d38` 만 들어감 | 후보(새 절 6 · 고정 28 동일 · `edge_dump` 209 동일)는 적용하지 않았다(`split-work/patches/R11/`, git 밖). §5 (2) |
| R12 | 프롬프트의 동적 부분 → Jinja2 · 결함 문구 → TOML | ✅ a `a6e484d` `46b9f5b` · b `60c500c` · c `644f6f0` · d `aae87e4` · e `47b8f56` · f `22d67e0` `082a1d3` · **결정 0012 확정** | §5 (2) |
| A1 | 결정 0011 | ✅ `1325398` | 계획 문안 그대로 |
| A2 | Mode 1.5 · 2 시험이 `measure` 를 import | ✅ `f1355c7` | 실행기 독스트링은 `5837c32` 에서 끝났다. §5 (3) |
| A3 | 실행기 스크립트 실재 시험 셋 | ✅ `77fe047` | 시험만. §5 (3) |
| A4 | `split_reading.py` | ✅ 커밋 없음 | 1,318 = mode1 1,025 + mode2 463 − 둘 다 176 + 버림 6. rev.4 어림(960 · 500)보다 갈림이 크지만 경로별 분류는 목록대로다 |
| K1 → K8 | 봉인 · seal 단계 · 진입 알림 · 위키 부분 재작성 · 계약 · 형 생성 · 판정+collect · run_mode2 근거 · init 상태 줄 · 문서/스킬 | ✅ §0 의 커밋 · 생산자 · 소비자 검토 각 1회 + 보강 · 사용자 승인(본체 전부) | 계획과 다르게 한 것과 남은 것은 §4.3 |
| M1 · M2 | 게이트 여섯 · `main` ff 병합 + 태그 | M1 ✅(pytest 874 · 2 · 19 · `npm test` 8 · tsc · pyright 0 · README 4 · 계약 `--check` 둘 · doctor · `evidence.py . --need terms-db` → `manifest.json 이 없다` exit 1 — Phase E 까지 정상) · M2 ⬜ | rev.4 :3235-3259. **`main` 에 미는 것은 사용자에게 먼저 묻는다** |

## 3. 문서 색인

| 문서 | 경로 | git | 역할 |
|---|---|---|---|
| rev.4 계획(사양) | `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md` | 추적 | Task 본문 전부. 서브에이전트에게는 해당 Task 를 **떼어 scratch 파일로** 넘긴다(아래 §5 의 꼴) — 계획서 자체를 읽게 하지 않는다 |
| 대조 도구 | `split-work/`(설명서 `split-work/README.md`) | 스크립트만 추적 · 산출물은 git 밖 | `capture.py` · `capture.sh` · `extract.py` · `split_reading.py` · `edge_dump.py` · `r9-gate-proto/`. §6 |
| 스킬 사본(깊은 복사) | `.claude/skills/{personal-commit-messages,design-decision-discipline,lossless-handoff,confidence-and-sourcing,response-quality-calibration,spec-review-dashboard,term-benchmark}/` | 추적 | 원본은 Mac 의 `~/.claude/skills/` — 일반 클라우드 세션(claude.ai/code · 저장소 하나)은 저장소 스킬로 읽는다. **프로젝트 안의 클라우드 스레드는 저장소 스킬을 읽지 않는다**(그때는 claude.ai 계정에서 스킬을 켠다). **원본을 고치면 사본도** 같은 변경에서 맞춘다(루트 CLAUDE.md) |
| 플러그인 superpowers | `.claude/settings.json` 의 `enabledPlugins`(`superpowers@claude-plugins-official`) | 추적 | **로컬 세션용이다.** 공식 문서(code.claude.com — cloud-environments "What carries over")에 따르면 클라우드 세션은 저장소가 켜는 플러그인을 설치하지 않는다. 클라우드에서는 서브에이전트 주도 절차를 이 문서 §5 · §7 에 풀어 적은 대로 따른다(플러그인 없이 된다). 클라우드에도 꼭 있어야 하면 — 일반 세션은 필요한 스킬을 MIT 사본으로 `.claude/skills/` 에 넣는다 · 프로젝트 스레드는 claude.ai 의 Project settings > Plugins 에서 켠다 · 조직이면 서버 관리 설정 |
| 결정 기록 | `docs/decisions/0011-split-mode1-and-report.md` | 추적 | A1 |
| 실행 계획(plan mode) | `~/.claude/plans/docs-superpowers-plans-2026-10-22-split-sprightly-codd.md` | Mac 만 | 내용은 §4 에 들어 있다 |
| 메모리 | `~/.claude/projects/<이 저장소>/memory/` | Mac 만 | 사용자 결정 요약 · 승인 규칙 |

Task 본문 떼기(계획서 줄 범위는 `grep -n "^#### Task" <rev.4>`):
```bash
P=docs/superpowers/plans/2026-10-22-split-mode1-and-report.md
.venv/bin/python - "$P" "$BRIEFS" <<'PY'
import re, sys, pathlib
lines = open(sys.argv[1], encoding="utf-8").read().splitlines(keepends=True)
ends = [i for i, l in enumerate(lines) if l.startswith("### Phase ") or l.startswith("#### Task ")]
for i, l in enumerate(lines):
    m = re.match(r"#### Task (\w+)", l)
    if m:
        nxt = min([e for e in ends if e > i] + [len(lines)])
        pathlib.Path(sys.argv[2], "rev4-%s.md" % m.group(1)).write_text("".join(lines[i:nxt]), encoding="utf-8")
PY
```

## 4. 확정된 결정 (다시 논쟁하지 않는다) + 정정표

**사용자 결정** — 경계는 A3 데이터 계약(스키마 사본 + `docs/codegraph/manifest.json` 봉인) · Mode 1 은 **사람이 부를 때만** 돌고 **묻지 않는다**(예상 비용 한 줄만) · Mode 1.5 는 봉인 없으면 멈추고 낡음 · 미커밋은 경고 · Mode 2 는 Mode 1 과 독립(봉인 있으면 근거) · 프롬프트는 단계당 한 파일 + `<!-- section: 이름 -->` 절 · 소비자 형은 계약 JSON 에서 생성 · 손댄 위키 장은 `.bak` · 범위 R→A→K→M · 서브에이전트 주도 · **본체 .py 승인 규칙 유지**.
2026-10-24 Mac 세션에서 더해진 결정 — 파이썬에 남은 LLM 글(빈 값 문구 · 목록 줄 꼴 · 고침 안내)도 리소스로(R10 끝) · 목록 밖에서 더 찾은 글도 같은 방식으로(R11) · R7 도움말은 실효값 · R6 `str(lang)`.
2026-10-24 클라우드 세션에서 더해진 결정(결정 0012, 제안됨) — 프롬프트의 동적 부분(반복 · 빈 값 대체 · 조건부 절 · 잇기 · 들여쓰기)은 프롬프트 파일 안 **Jinja2**(명시 의존) · 파일은 **마크다운 그대로, 절 표식 유지** · YAML 은 쓰지 않는다 · **엄격 검사**(빠진 값 · 남는 값 둘 다 오류) · 공백 `trim_blocks` · `lstrip_blocks` · `keep_trailing_newline` · 결함 문구 9개는 **`runner/mode1/faults.toml`** · **프롬프트만**(파일 템플릿 일곱은 `tools/template.py` 그대로) · **템플릿은 꼴만, 데이터 결정은 단계** · 바이트 대조는 합격 기준이 아니다(바뀐 글은 diff 로 사람이 본다) · R11 후보 폐기.

**정정표 — rev.4 를 코드 실물로 고친 것.** 해당 Task 를 시킬 때 반드시 brief 에 넣는다. ⑪ ⑫ 는 소진됐다.

| # | Task | 고칠 것 |
|---|---|---|
| ① | K2 | `VerifyTermsStage`(`runner/mode1/terms.py`)에 `def writes(self, ctx): return [X.TERMS_DB]` 추가. 없으면 `seal-artifacts` 의 `reads` 가 사슬 검사(`pipeline.py` 의 시뮬레이터)에서 `GraphError` |
| ② | K1 · K6 | 봉인의 소스 집합 = `declmap.tracked_files(repo, lang, [])` **그대로 호출**(`git ls-files` 추적 파일만 · `SKIP_DIRS` 성분 제외 · `docs` 제외 없음). `manifest.json` 의 `skip_dirs = sorted(declmap.SKIP_DIRS)`. `evidence.py` 사본은 `git ls-files`(`-co` 없이). 시험 "새 파일도 넣는다" → "미추적 파일은 넣지 않는다" |
| ③ | K2 | `runner/test_mode1.py` 의 `len(E.ORDER) == 12`(시험 `test_증분은_열둘_전량은_열하나`) → 13 / 12 |
| ④ | K2 · K3 | `context.py` 새 칸은 형 붙은 공장 — `_no_strs() -> set[str]` · `_no_names() -> list[str]` |
| ⑤ | **K6** | **`--terms-db` 를 필수로 만드는 같은 커밋에서 한다**(R5 에서 하면 선택 인자일 때 스킬이 값 없는 `--terms-db` 명령을 받는다). `ask_argv(root, plan, workdir, python, terms_db)` · `runner/prompts/ask.md` 명령 자리에 `--terms-db {{terms_db}}` · `AskStage.perform` 이 `ctx.terms_db` 전달 · 시험 `test_ask_명령줄은…` 에 `"--terms-db" in prompt` · `test_ask_첫_프롬프트는_한_줄이고…`(`95f9758`)의 기입란 명령 기대값도 맞춘다 · §6 도구의 `capture.py` 의 `ask_argv(...)` 호출에 값을 더하고 `mode1_5-ask` 둘(`.txt` · `.raw`)의 차이는 의도된 차이로 기록 |
| ⑥ | K2b | `estimate_line` 을 `ScheduleBatchesStage.perform` 끝 **과** `run_mode1.py` dry-run 블록 둘에. 세션 수 `sum(len(L.get("batches", [])) or 1 …)`. 값은 `config/mode1.toml [estimate]`(R7 이 이미 만들었다 — `X.load_config()["estimate"]`) |
| ⑦ | K2b | `DetectChangesStage.perform`: `not os.path.exists(X.snapshot_path(ctx))` 면 `⚠ 증분으로 불렸지만 전량이다 — 지난 지문(snapshot.json)이 없다`(stderr). 기존 알림 문구도 같은 꼴 |
| ⑧ | K3 | `runner/wiki/build.py` **안 고친다**(demermaid · check · sidebar 전부 최상위 `*.md` 만 본다). 대신 `.gitignore` 에 `docs/wiki/.bak/` |
| ⑨ | K3 | `wiki.py` 에 `json` · `msgspec` · `from mode1 import diff as D` · `from mode1.scan import DetectChangesStage` import(순환 아님) |
| ⑩ | K3 | `test_write_wiki_는_이미_쓴_장을_건너뛴다` 는 그대로 통과 — 고치지 않는다. ⚠ R10 으로 `write-wiki.md` 는 절 넷이 됐다(`main` 등) — K3 의 시험 · 코드가 `"write-wiki"` 맨 이름을 부르면 `write-wiki#main` 으로 |
| ⑬ | K7 | `runner/test_run_mode2.py` 의 `test_the_prompt_mentions_the_glossary_source_only_when_it_exists` — 새 절(`agent#evidence*`)에 `terms.json` 글자를 넣지 않는다. `95f9758` 의 배치 시험 둘(`금지 목록 → 용어집 → 규율` 사이 빈 줄)도 근거 절 자리에 맞춰 다시 본다 |
| ⑭ | K7b | `viz/init.py` 상태 한 줄은 `docs = listDocs(cwd)` 바로 뒤 한 번 — 세 종료 경로(목록 · 이어 쓰기 · 새 뼈대) 모두 지난다 |

### 4.1 시험 fixture 주석
pyright strict 가 `machine/ runner/ viz/ tools/` 를 포함하므로 그 아래 시험의 fixture 는 주석을 붙인다: `tmp_path: Path` · `monkeypatch: pytest.MonkeyPatch` · `capsys: pytest.CaptureFixture[str]` · parametrize 인자(`text: str`). `test/` 아래는 pyright 밖. rev.4 시험 코드에는 이 주석이 빠져 있다 — brief 에 매번 적는다.

### 4.2 이월 사항 (아직 열린 것만)

**모든 Task**
- Step 끝에 README 재생성 — `.venv/bin/python tools/gen_readme.py machine runner viz tools` 뒤 `--check` 가 `README 4개 — 소스와 일치`, 바뀐 README 를 이름으로 `git add`. 새 `.py` · 함수 · 시험 · 독스트링이 모두 README 를 바꾼다. README 를 건드리는 Task 둘의 커밋은 순서대로.
- 실험 파일은 scratch 에만. 저장소 뿌리에 임시 폴더를 만들지 않는다.
- 새 LLM 글은 리소스로(R9 게이트가 긴 글 · 선언 1:1 · 고아 템플릿을 잡는다). 새 절은 그 단계의 `prompt_names` 에 선언. 한 줄 조각은 `load_prompt(...).removesuffix("\n")`.
- 프롬프트 · 템플릿 렌더 값은 전부 `str`(렌더러는 `None` 을 빈 글자로, `int` 를 `TypeError` 로 다룬다 — R6 I2 실측).

**K 에 걸리는 것**
- K6 · K7 이 프롬프트를 바꾸면 R5 의 배치 시험 · R10 의 절 선언 · R9 게이트가 함께 움직인다. 바꾼 뒤 `test/test_prompt_resources.py` 를 꼭 돌린다.
- `config/mode1.toml [estimate]` 는 지금 읽는 곳이 시험뿐이다 — K2b 가 첫 런타임 독자다.

**Phase B 로**
- `split-work/` 는 분리 작업 도구라 두 저장소 어느 쪽 제품도 아니다 — rev.4 B1 경로 목록에서 report-builder 쪽에 두고 분리가 끝나면 지운다. `.claude/skills/` 의 사본 다섯(`personal-commit-messages` 등)은 두 저장소 모두에서 쓰인다 — Mode 1 저장소에도 넣을지 B 에서 정한다.
- `tools/template.py` 는 **두 저장소 모두에 필요하다** — Mode 1 쪽 `viz/render_*.py` · `runner/wiki/build.py` · `runner/pipeline.py` 와 Mode 2 쪽 `viz/init.py` · `viz/build.py` 가 함께 import 한다. rev.4 B1 경로 목록 양쪽에 넣는다. `config/mode1.toml` 은 Mode 1, `config/report.toml` 은 Mode 2 쪽.

**Phase E 로**
- `machine/terms-reading.json` 의 줄 인용이 Phase R 로 많이 낡았다(R6 다섯 파일만 43건) · 옛 시험 이름 `test_doc_dirs_matches_the_javascript_side` 가 키로 남았다 — Mode 1 증분으로 갱신.
- `docs/wiki/` 의 L2 인용 낡음, `docs/wiki/runner-mode2-spec.md` 가 옮겨 간 문구를 `agent_prompt` 로 인용 — 재굽기.

**사용자 판단 거리 (급하지 않음 — 묻지 않고 진행해도 된다)**
1. `config/report.toml` 을 두 파서(`runner/run_mode2.py` msgspec · `viz/init.py` tomllib)가 읽는다. `tools/` 에 읽기 함수 하나를 두고 함께 쓰면 모양 · 검증이 하나가 된다. 지금 판도 `test/test_config.py` 가 지켜 합리적이다.
2. `config/report.toml` 의 `mode2_agent = "opus"` 는 별명이다. 옆의 `config/mode1.toml` 은 "별명이 아니라 정확한 ID" 원칙을 적었다. 값은 옛것을 보존했다.
3. 폐지된 `# <include …/>` 블록 잔재를 지울 시점(루트 CLAUDE.md — 사용자가 정한다). A2 의 `# 쓰는 것: run_mode1` 줄이 그 안에 있어 지금은 손대지 않는다.
4. 프롬프트 예외(`KeyError` · `ValueError` · `TemplateError` · `FileNotFoundError`)를 `Pipeline.run` 이 `FAIL` 행으로 바꾸지 않는다(지금 `msgspec.DecodeError` 만) — 정책 변경이다.
5. 템플릿 BOM — `utf-8-sig` 로 읽지 않는다. 바꾸려면 `render_file` 과 `load_prompt` 를 함께.

**R9 보강 · R10 검토에서 남은 것(기록)**
- `ARCHITECTURE.md` 에 확인하지 않은 낡은 줄 인용이 더 있다(`viz/build.py:54` · `:36` · `viz/check.py:124` · `runner/run_mode1.py:247` 등) · "측정 코드는 `run_mode1.py` 만" 은 지금 `measure.py` 다. 줄 인용 검사("줄 번호 ≤ 파일 끝")를 넣으려면 먼저 이것과 루트 `CLAUDE.md` 의 설명 문장 하나를 정리한다.
- 루트 `CLAUDE.md` "현재 상태" 표의 `660 통과` 는 2026-10-21 측정 행이라 낡았다(지금 711). 측정 행을 다시 잴 때 고친다.
- `.tmpl` 은 인용 검사기의 `PATH_REF` 가 확장자를 몰라 폴더째 인용하지 못한다 — 문서에 "`viz/templates/report/` 의 `data.ts.tmpl`" 꼴로 적는다.
- `WriteWikiStage.jobs` 의 `wiki_done` 은 이번 실행에서 쓴 장만 담는다 — `--resume` 으로 첫 층이 이미 있으면 둘째 층 프롬프트가 "(없음 — 네가 첫 장이다)" 라고 말한다(R10 이전부터).
- 게이트가 아직 못 보는 꼴은 R9 재검토가 판정했다 — 닫지 않는다(위 *상태*).

### 4.3 Phase K 에서 계획과 다르게 한 것 · 남은 것 (2026-10-31 클라우드 세션)

**계획과 다르게 한 것**(전부 사용자 승인)
- K2 — 재개 문서(`resume.json`)가 통과한 검사 목록 `verified` 를 싣는다(없으면 `write-wiki` 실패 뒤 재개한 봉인에서 terms-db 가 빠진다). 재개가 아닌 실제 실행은 시작할 때 옛 `resume.json` 을 지운다(끊긴 실행이 옛 `verified` 를 남기지 않게).
- K2b — 비용 줄은 `전수조사 세션 N개 · 예상 $lo~hi · 증분|전량` · 꼬리는 "계획이 diff 로 좁혀졌는가". 합계 줄도 배치 · 전수조사 세션을 따로. 지문 없음 알림은 `DetectChangesStage`(전량 경로에서 거짓말 방지).
- K3 — 낡은 장 판정 기준은 `changes.json` 이 아니라 `wiki-state.json` 의 `sources`(위키가 따라잡은 시점의 소스 지도) — 전량 · 증분 같음. 기준이 없으면(이 저장소의 위키 21장) 기존 장은 건너뛰고 따라잡았다고 적지 않는다(사용자 결정) → 봉인은 terms-db 만. 낡은 장은 세션 전에 지우고(사람이 고친 · 출처 모를 장은 `docs/wiki/.bak/<stem>.N.md` 로) 세션 뒤 "장이 있는가" 로 판정. 장 해시는 층마다 적고 처음 굽기면 기준도. 위 층 프롬프트의 아래층 장 목록은 디스크에 있는 것.
- K6 — 소스 집합 사본은 `declmap.tracked_files` 와 같은 규칙 · `-z` 로 비ASCII 경로까지(생산자도 함께). `collect` 는 봉인 자리(`<대상>/docs/codegraph/terms-db.json`)의 파일만 받는다. `evidence.py --optional`(봉인된 종류만 판정 — Mode 2 · init 이 쓴다), `--status` 는 `--need` 오류(exit 2) 말고는 늘 exit 0.
- K7 — 근거는 절 셋이 아니라 `agent.md` 의 `main` 안 `{% if evidence %}` 블록(R12 규칙). `--dry-run` 은 `evidence.py` 를 부르지 않는다.
- K8 — 스킬 **원본**(`~/.claude/skills/term-benchmark` · `spec-review-dashboard`)이 클라우드에 없어 **저장소 사본만 고쳤다 — Mac 에서 원본 동기화 필요**(사본 → 원본 복사).

**남은 것(기록만 — 고치지 않았다)**
- 산출물 sha256 을 날 바이트로 잰다 — 줄끝을 바꾸는 `.gitattributes` 저장소의 새 클론에서 "봉인 뒤 바뀌었다". 고치려면 계약 v2(산출물도 blob id).
- `write-wiki` 의 기준이 장마다가 아니라 하나라서 되돌린 소스가 낡은 장을 숨기고, 층 중간 실패 뒤 재개하면 이미 다시 쓴 장을 또 쓴다. 세션이 실패하면 지운 낡은 장은 다음 실행까지 빠진 채다.
- 사람이 고친 장이 쌓이는 `docs/wiki/.bak/` 은 이 저장소 `.gitignore` 에만 있다(다른 대상 저장소에서는 git 에 보인다). 정리는 사람 몫.
- 지문이 없을 때 비용 줄 꼬리가 `증분` 으로 찍힐 수 있다(targets 가 전체 목록). 빈 저장소에서 `--skip verify-terms` 류는 `seal-artifacts` 의 읽기 때문에 `GraphError` — `--skip seal-artifacts` 로 우회.
- UTF-8 이 아닌 파일 이름이면 생산자 · 소비자 둘 다 디코드 오류. `ts` 대상 저장소에서는 보고서 원고(`data.ts` · `report.tsx`)가 낡음(`생김`)으로 잡힌다(경고뿐).
- Mode 2 한 번 실행에 봉인 상태 줄이 두 번(실행기 · init 자식). `stale` 목록 길이 상한 없음.
- `90f5843` 하나는 시험 둘이 빨간 채로 push 됐다(프롬프트 문구를 고친 뒤 배치 시험 기대값을 못 맞춤) — 다음 커밋 `82c10b0` 이 맞췄다. 이력은 고치지 않는다.
- 이 저장소에는 봉인이 없다 — Phase E(위키 재굽기 · Mode 1 자기 실행) 전까지 Mode 1.5 는 `collect` 에서 멈추고, Mode 2 · init 은 `Mode 1 봉인 — 없음` 을 찍는다.

**기록만**
- `agent_prompt` · `ask_argv` 는 모듈 함수가 `AgentStage.load_prompt` · `AskStage.load_prompt` 를 부른다(단계 소유 `@staticmethod` 꼴과 다르다). 범위 밖.
- `runner/mode1/lang.py` 가 import 때 `config/mode1.toml` 을 읽어, 그 파일이 깨지면 러너 시험 네 파일이 수집 단계에서 죽는다(메시지는 정확하다). `[estimate]` 가 빠져도 그렇다.
- R10 으로 심볼 줄마다 `load_prompt` 가 파일을 다시 읽는다(실행당 심볼 수만큼, 비용 작음).
- `render.mjs.tmpl` 의 `'file://{{bundle}}'` 은 경로에 `'` 가 있거나 Windows 경로면 깨진다(옛 동작 그대로).

## 5. 남은 일 — 순서와 brief 요지

공통: 서브에이전트 brief 에 (가) 이 프로젝트가 무엇이고 Phase R 이 무엇을 했는지 두세 줄 (나) 떼어 둔 Task 본문 파일 경로 (다) 그 Task 에 걸리는 정정표 · 이월 항목 (라) §7 의 승인 프로토콜 (마) worktree `.venv` 꼴(§6-4) (바) 검증 명령과 기대값 (사) 커밋 메시지 글자 그대로 (아) `docs/handoffs/` · `docs/superpowers/` · `docs/my.self/` 를 열지 말 것 을 넣는다.

**(0) 준비** — §6.

**(1) R9 보강 · R10 품질 검토**

*상태(2026-10-24 로컬 세션)*: **R9 보강 끝** — 1단계 시험 · 문서 커밋 셋(`0ba79a3` `a7a66c4` `3c4c4e8`) + 3단계 본체 커밋 둘(`bae47de` I1 · `44b55c5` M2, 사용자 승인). 재검토(opus, 범위 `88c8123..44b55c5`) **Ready: Yes** — I1 · I2 를 다시 넣어도 잡히고 다섯 커밋이 각각 초록. 남긴 Minor 는 기록만: 게이트 1 을 아직 비켜 가는 꼴(중첩 f-문자열 · `+` 이어붙이기 · `"\n".join` 목록)은 "걸림줄이지 벽이 아니다 — 더 쫓으면 거울 함정" 판정, 200자를 넘는 정규식이 처음 걸리면 그때 `re.compile` 첫 인자만 빼는 몇 줄을 검토. **R10 품질 검토 끝** — With fixes → `6e9cc72`. 아래는 기록으로 남긴다.
*M2 확정(2026-10-24 로컬 세션 질의 — 클라우드의 잠정안은 버렸다)*: 긴 글 게이트(게이트 1)의 탐색 폴더를 `runner` · `viz` · `machine` · `tools` 로 넓힌다. 걸리는 유일한 것 `tools/doctor.py:98`(패키지 확인용 `python -c` 7줄)은 파일로 빼 자식 프로세스로 부른다 — **본체 승인**이고 게이트 넓히기 · 루트 `CLAUDE.md` 의 규약 범위 문장과 **한 커밋**이다(따로 넣으면 게이트가 빨개지거나 문서가 앞서간다). 그래서 아래 커밋 3 에서는 M2 를 빼고 3단계로 옮긴다.

*R9 보강을 다시 띄울 때 brief 에 더할 것(클라우드 스레드가 쓴 brief, 넘김 문서 §6)* — 아래 R9 검토 결과를 글자 그대로 붙이고 이것을 더한다.
- 1단계는 시험 · 문서라 승인 없이 커밋한다. 커밋 셋, 제목은 ASCII 구두점만:
  1. `[test] : 리소스 게이트 - 템플릿을 문자열 상수와 같은 값으로 찾고 단계당 한 파일을 본다` — I2, M1, M3(게이트 2 줄), M4. **I1 의 f-문자열 갈래는 아직 넣지 않는다**(넣으면 `viz/build.py:125` 때문에 게이트가 빨개진다).
  2. `[test] : run_mode2 시험 - test_config 와 겹치는 DOC_DIRS 시험을 지운다` — M11. 먼저 `test/test_config.py` 가 같은 것을 단언하는지 확인한다.
  3. `[docs] : phase R 문서 - 규약 범위, 산출물 수, 모델 사슬, tools 의존, 낡은 줄 인용` — M3 문장(규약 범위 문장은 빼고), M5, M6, M7, M8, M10, 권고. "줄 번호 ≤ 파일 끝" 검사는 HEAD 의 모든 컨텍스트 문서가 통과할 때만 넣고, 걸리면 목록만 보고한다.
- 3단계(I1, 본체 승인): 게이트의 f-문자열 갈래와 `viz/templates/report/page.html.tmpl` 은 저장소에 직접 쓰고 커밋하지 않는다. `viz/build.py` 후보는 `split-work/patches/R9b/viz__build.py` + `R9b.diff`. `render_file` 은 글을 정규화하지 않으니 `.tmpl` 은 f-문자열이 내던 바이트 그대로(끝 줄바꿈 하나까지). 커밋 제목 `[refactor] : 보고서 HTML 뼈대를 templates 로 - 긴 글 게이트가 f-문자열을 한 덩어리로 잰다` — 게이트 조이기, `.tmpl`, `viz/build.py`, 바뀐 README 를 한 커밋에.
- `report.html` 미리 대조(§6-3 의 worktree 꼴로 후보를 얹은 뒤, `$PWD` 는 본 저장소 뿌리):
  ```bash
  ( cd docs/superpowers/specs/runner-stage-machine && "$S/wt/bin/report-spec" build >/dev/null \
      && sed "s#$S/wt#$PWD#g" out/report.html > "$S/report.html.wt" )
  cmp "$S/report.html.wt" split-work/before/report.html && echo "report.html 동일"
  ```
  진짜 대조는 적용 뒤 본 저장소에서 `split-work/capture.sh` 로 한다.

*R9 품질 검토 결과(opus, 범위 `4d7c70d..116bd73`, 2026-10-24) — "With fixes". 아직 고치지 않았다.* 줄 번호는 `116bd73` 기준이고 그 뒤 커밋은 `test/test_prompt_resources.py` · `viz/build.py` 를 건드리지 않았다.
- **I1 — 게이트 1 이 f-문자열을 못 본다.** `ast.JoinedStr` 안의 글자 조각이 따로 `Constant` 로 잡혀 조각별로만 잰다(`test/test_prompt_resources.py:52-58`). 그래서 `viz/build.py:125` 의 **15줄 HTML 문서 뼈대**(조각마다 최대 5줄 · 139자)가 통과한다 — 루트 `CLAUDE.md` 의 "파일 템플릿은 `**/templates/*` … 게이트가 막는다" 와 어긋난다. 고치는 법: ① 게이트에 `JoinedStr` 이면 안의 `Constant` 조각을 합쳐 한 덩어리로 재는 갈래(몇 줄) — HEAD 에서 걸리는 것은 `viz/build.py:125` 하나 ② 그 뼈대를 `viz/templates/report/page.html.tmpl` 로 옮기고 `render_file` 로 채운다(조립은 여전히 파이썬 — 루트 CLAUDE.md "단일 파일화 = 파이썬 문자열 조립" 과 부딪히지 않는다) ③ **본체 `.py` 라 승인** ④ 옮기기와 게이트 조이기는 한 커밋(아니면 게이트가 빨개진다). 합격: `report.html` 바이트 동일(§6 `capture.sh`).
- **I2 — 게이트 3 이 소스 글자의 부분 문자열로만 찾는다**(`:88`). 거짓 통과 셋을 확인했다: 호출을 지우고 주석에만 이름이 남음 · 다른 자리의 같은 basename(`viz/templates/dot/entry.ts` 가 `report/entry.ts` 덕에 통과) · 부분 문자열(`try.ts` 가 `"entry.ts"` 안에). 고치는 법(시험만): 게이트 1 의 AST 순회로 독스트링을 뺀 문자열 상수 집합을 모으고 템플릿 basename 이 그 집합에 **같은 값으로** 있는지 본다 + "템플릿 basename 은 저장소에서 유일하다" 단언 한 줄. HEAD 는 통과, 셋 다 잡힌다.
- Minor(묶어 보강 — 시험 · 문서라 승인 없음, 단 M2 의 `tools/doctor.py` 는 본체):
  - M1 실패 메시지 — 게이트 2 는 절대 경로를 내고 항목이 둘 이상이면 첫 항목만 보인다 → `relpath` 목록을 `"\n".join`. `sections()` 의 `ValueError` 가 파일 이름 없이 올라온다 → `try` 로 감싸 `pytest.fail(f"{rel}: {e}")`.
  - M2 범위 — 규약 문장에는 범위 제한이 없는데 게이트 1 은 `runner` · `viz` 만 본다. `machine/` 은 0건이라 넣어도 된다. `tools/` 는 1건(`tools/doctor.py:98` 의 `python -c` 7줄 스크립트) — 그 스크립트를 파일로 빼거나(본체 · 승인) 규약 문장을 "`runner/` · `viz/` 의 파이썬" 으로 좁히거나 — **사용자 판단**.
  - M3 규약 문장 — `**/templates/*` 라 적었지만 게이트는 `runner` · `viz` 만 본다. `resources/templates/OBSERVATION-template.md` 는 사람이 복사하는 템플릿이라 그 글롭대로면 고아다 → "코드가 쓰는 템플릿은 `runner/**/templates/` · `viz/templates/`" 로 좁힌다. "단계당 한 파일" 은 참이지만 강제되지 않는다 → 게이트 2 에 `{n.partition("#")[0] for n in c.prompt_names} <= {c.name}` 한 줄(HEAD 통과 확인). 절 없는 파일은 `"<파일>"` 로 선언한다는 것도 규약에 적는다(`runner/CLAUDE.md` 의 변경 패턴 줄도).
  - M4 `is_production_class` 의 둘째 조건은 셋째에 포함된다. 실제로 걸러지는 것은 시험 모듈의 최상위 클래스(`runner.test_pipeline` 의 둘)이고 `<locals>` 는 관찰되지 않았다 — 독스트링을 그에 맞게.
  - M5 `runner/CLAUDE.md` "흔한 변경 패턴" 머리말 "넷을 … 빠지면 GraphError" — 새 프롬프트 줄은 시뮬레이터가 보지 않는다 → "(프롬프트는 `test/test_prompt_resources.py` 가 잡는다)".
  - M6 `runner/CLAUDE.md:13` "산출물 10개" 는 실제 14개(`context.py` `ARTIFACTS`) · "단계 모듈 여섯" 에 `survey_files` 가 빠졌다.
  - M7 `ARCHITECTURE.md:133-138` · `machine/CLAUDE.md:152-154` 모델 사슬 — `--strategy file` 이면 `AnnotateFilesStage.perform` 이 `P.run_agent_with` 를 직접 불러 `run_layer` 를 건너뛴다(`survey_files.py:60`) · `outline-wiki` 도 `sessions` 값을 쓴다.
  - M8 `tools/CLAUDE.md` 의존 표에 `template.py` 로 들어오는 화살표(viz · `runner/pipeline.py` · `runner/wiki/build.py`)가 없다 · 루트 `CLAUDE.md:12` 의 tools 설명도.
  - M10 루트 `CLAUDE.md:13` "Mode 1 · Mode 2 의 Model id" — Mode 2 값은 별명 `"opus"` · `[estimate]` 를 읽는 운영 코드는 아직 없다(K2b 가 첫 독자).
  - M11 `runner/test_run_mode2.py` 의 `test_doc_dirs_are_specs_then_plans` 는 `test/test_config.py` 와 완전히 겹친다 — 지워도 된다.
  - 권고: `ARCHITECTURE.md` 의 줄 인용이 낡았다 — `:360` `viz/init.py:107-110` 의 글은 `viz/templates/report/data.ts.tmpl:10-13` 으로 옮겨졌다 · `:379-380` `viz/build.py:80` / `:99` 는 지금 `:74` / `:97` · `:86-87` `runner/wiki/build.py:98` / `:109` 는 파일 끝(80줄)을 넘는다. `test/test_docs_citations.py` 는 파일 존재만 본다 → 함수 이름으로 인용하거나 "줄 번호 ≤ 파일 끝" 검사를 몇 줄 더한다.
- **원형이 저장소에 있다**: `split-work/r9-gate-proto/stricter.py` 가 I1 · I2 를 고친 게이트를 미리 돌린다(HEAD 기대 출력 `gate1+fstr: ['viz/build.py:125']` · 중복 basename 없음 · 고아 없음). `scan_evasion.py` · `scan_long.py` 는 비켜 가는 꼴과 범위(M2) 판단용 — 기대 출력은 `split-work/README.md`.
- 처리 순서 제안: I2 + M1 · M3(게이트 2 줄) · M4 (시험) → 문서 M3 · M5 · M6 · M7 · M8 · M10 · 권고 → I1 (본체 · 승인, 게이트 조이기와 한 커밋) → M2 는 확정(위)대로 3단계에서 I1 과 함께. 끝나면 같은 꼴로 재검토(opus).

*R10 품질 검토* — `opus` · 읽기 전용. 위 R9 보강의 구현자와 같이 돌려도 된다(R10 검토는 `runner/mode1/` 을 읽고, R9 보강은 `test/` · `viz/build.py` · 문서를 고친다).
- R10: 범위 `d6286be..5837c32`. 볼 것 — 새 절 15개와 `prompt_names` · `FIX` 의 모듈 수준 대입(`ClassVar` 선언 + 클래스 뒤 채움)의 위험(import 순서 · 하위 클래스) · 한 낱말 절 둘(`batch-symbol-no-deps` "없음" · `pass2-no-deps` "  (없음)")의 값(사용자가 남기기로 했다 — 결함이 아니면 지적만) · 바이트 보존(§6 의 `edge_dump.py` 로 `git archive d6286be` 대 HEAD) · B 의 독스트링 사실 대조.
- Important 이상은 그 Task 안에서 고친다(본체면 승인). Minor 는 묶어 보강하거나 §4.2 로.

**(2) R12 — 프롬프트의 동적 부분을 Jinja2 로(결정 0012 · R11 을 대체)** — 구현자 `opus`(여러 파일 · 설계 판단).

*R11 경과(2026-10-24 클라우드).* 구현자가 목록 밖 글 여섯(미조사 의존 줄 · 결함 줄 · 결함 설명 넷)을 새 절 6개로 옮긴 후보를 냈다 — 고정 28 동일 · `edge_dump` 경계 입력 209 동일. 사용자가 그 구조를 되묻는 과정에서 방향이 바뀌었고 후보는 **적용하지 않고 버렸다**(`split-work/patches/R11/`, git 밖). 들어간 것은 커밋 1 `8d71d38` 뿐이다 — `runner/test_mode1.py` 의 바이트 고정 시험 넷(미조사 의존 줄 · 결함 줄 · 결함 설명이 `check_shards` 와 `.bad.why` 에 실리는지 · `check_shard.py` 출력)과 `split-work/edge_dump.py` 경계 입력 128 → 209.

*판단 근거.*
- 동적 프롬프트 해부 페이지(claude.ai artifact `XWA74HNoJpkWuo4EWb2hYq`, 생성기는 클라우드 scratch — 사라진다). 실제 리소스 · 저장소 데이터로 렌더한 다섯 장면이다. 실제 출력에서 본 것:
  - 조건부 절 셋(미조사 · 범위 · 재조사)이 마무리 줄 "보고:" **뒤에** 붙는다. Mode 2 의 용어집 절은 본문 자리에 들어간다.
  - 미조사 의존 이름이 심볼 줄의 `의존 ->` 와 미조사 절에 두 번 나온다.
  - 프롬프트가 이미 데이터를 경로로 넘기는 꼴을 쓴다(`record-schema.json` · `file_cache.py` · `check_shard.py`).
  - 재조사 절은 `.bad.why` 를 산문으로 옮겨 싣는다.
- 라이브러리 조사(deep-research, 검증 단계에서 멈춤 — 주장 84개 중 통과 19 · 정정 2 · 나머지 검증 전). 출처 20곳.
  - 이 분야의 주류는 **파일에 기존 엔진의 문법을 둔다**: banks · promptly · Prompty · LangChain 은 Jinja2, Dotprompt 는 Handlebars, POML 은 자체 문법.
  - 코드 조합기 쪽은 목적이 다르다: priompt 계열은 토큰 예산(낮은 우선순위를 조용히 떼어 냄), Guidance 는 생성 제약.
  - POML 은 Node 를, promptl-py 는 WebAssembly 를 쓰고, LangChain 은 프레임워크 부품이다.
  - 엄격 검사와 바이트 안정을 기본으로 주는 기성 라이브러리는 그 범위에서 못 찾았다 — Jinja2 를 엄격하게 설정해 직접 쓰는 것이 가장 가깝다.
  - YAML 안의 Jinja2 는 Ansible 이 대표 사례다(일반 지식).

*이행 단계(Task 마다 한 커밋 · 본체 `.py` 는 승인).*
- **R12a 의존과 렌더.**
  - `requirements.txt` 에 `jinja2` 를 더한다. 판은 설치되는 판으로 고정한다(2026-10-24 실측 — `.venv` 에 Jinja2 · MarkupSafe · PyYAML 모두 없다).
  - `PromptResource.load_prompt` 가 절 글을 Jinja2 로 렌더한다. 설정: `StrictUndefined`, 남는 값은 `meta.find_undeclared_variables` 로 대조해 오류, `trim_blocks` · `lstrip_blocks` · `keep_trailing_newline`, `autoescape` 끔.
  - 값 형을 `str` 에서 목록 · 사전까지 넓힌다.
  - **이 단계는 글을 고치지 않는다.** 지금의 `{{이름}}` 은 Jinja 문법과 같고, 리소스의 Jinja 특수 글자(`{%` `{#` 자리 아닌 `{{…}}`)는 0건이다(실측). 그래서 고정 28 과 `edge_dump` 가 같게 나와야 한다 — 이것만은 바이트로 본다.
- **R12b 결함 표.**
  - `runner/mode1/faults.toml` 에 갈래마다 `detail` · `fix` 를 둔다. 결함 설명 중 `where` 는 `{{ kind }}` 를 가진다.
  - `FIX` 표와 결함 설명 네 자리가 이 표를 읽는다.
  - 표 머리에 결함 줄 꼴 `line` 하나를 둔다(설계 판단 (나)). `fault_line` 의 몸이 이것을 렌더하고 호출처 다섯은 그대로다.
  - `annotate-symbols.md` 의 `fix-*` 절 다섯을 지운다.
  - 시험: 표의 키 = `FaultKind` 값.
- **R12c Mode 1 `annotate-symbols`.**
  - 한 줄 절 일곱(`batch-symbol` · `batch-symbol-no-deps` · `batch-dep` · `batch-dep-no-means` · `batch-no-deps` · `pass2-dep` · `pass2-no-deps`)을 본문 절 안 `{% for %}…{% else %}` 로 합친다.
  - 범위 · 미조사 · 재조사 절을 `{% if %}` 로 `batch` 본문의 자리에 둔다.
  - `survey.py` 는 조립한 문자열 대신 **행(사전 목록)** 을 넘긴다 — 데이터 결정(무엇이 미조사인가 · 어느 결함인가)만 남는다.
  - `8d71d38` 시험의 기대값을 새 꼴로 바꾼다.
- **R12d `write-wiki`.** `lower-page` · `no-lower-pages` · `page-no-symbols` 를 `main` 안으로 합친다.
- **R12e Mode 2 `agent`.** `terms` 절을 `{% if terms_json %}` 로 `main` 안에 둔다. `ask` 는 그대로다.
- **R12f 게이트와 문서.**
  - `test/test_prompt_resources.py` 에 "모든 절이 Jinja2 로 컴파일된다" 를 더한다. 절이 줄어 게이트 2 의 1:1 은 그대로 통한다.
  - 같은 게이트에 프롬프트 파일의 **줄 끝 공백**과 **`{#`** 를 막는 검사를 더한다. 블록 태그 뒤 공백은 공백 줄을 남기고(`trim_blocks` 가 줄바꿈을 못 먹는다), `{#` 는 이제 Jinja 주석을 열어 글을 조용히 삼킨다. 2026-10-24 실측으로 지금 파일에는 둘 다 0건이다(R12a 품질 검토).
  - 루트 `CLAUDE.md` 최우선 규약("자리표시는 `{{이름}}` 하나" → 프롬프트는 Jinja2, 파일 템플릿은 `{{이름}}`)과 `runner/` · `test/` · `tools/` 의 `CLAUDE.md` 를 고친다.
  - 끝나면 0012 를 **확정**으로 올린다.

*설계 판단 둘 — 사용자 결정 2026-10-24.*
- (가) 조건부 절 셋은 **각자 맞는 자리**에 둔다. 재조사 절은 역할 소개 바로 아래에 둔다(가장 먼저 읽힌다). 범위 · 미조사 의존 절은 "네가 맡은 심볼" 바로 아래, "읽는 법" 앞에 둔다. "이번 배치의 사정" 한 절로 모으는 안과 자리를 그대로 두는 안은 고르지 않았다.
- (나) 결함 줄 꼴은 **`faults.toml` 의 `line`** 에 Jinja2 꼴로 둔다. 호출처 다섯 — 재조사 절(`survey.py` 의 `retry_section`) · stderr 셋(`survey.py` 하나 · `survey_files.py` 둘) · `check_shard.py` 의 stdout — 이 모두 이 꼴로 렌더한다. `fault_line` 은 이름을 남기고 몸만 표를 읽게 바꾼다. 결정 0012 의 "범위는 프롬프트만" 에 이 한 자리가 예외로 적혔다. 파이썬에 두는 안과 프롬프트가 칸을 받는 안은 고르지 않았다.

*검토 장치.*
- 옮기기 전후를 `split-work/capture.sh` 로 찍어 diff 를 사람이 본다. 같을 필요는 없다(R12a 만 예외).
- `edge_dump.py` 는 함수 인자가 문자열에서 행으로 바뀌면 맞춰 고치거나 이 Task 에서 은퇴한다.

커밋 제목 제안(ASCII 구두점):
- `[update] : prompt 렌더를 jinja2 로 - 엄격 검사와 공백 규칙`
- `[refactor] : 결함 문구를 faults.toml 결함 표로`
- `[refactor] : mode 1 프롬프트의 반복, 빈 값, 조건부 절을 jinja2 로`
- `[refactor] : write-wiki 와 agent 프롬프트를 jinja2 로`
- `[docs] : 결정 0012 확정과 규약 문장`

**(3) A2 · A3** — 시험 파일만이라 승인 없이 구현자가 커밋해도 된다(`sonnet`, 둘을 한 구현자에게 차례로).
- A2: `runner/test_run_mode1_5.py:23` · `runner/test_run_mode2.py:20` 의 `import run_mode1 as M  # noqa: E402` → `import measure as M  # noqa: E402`. 두 시험이 쓰는 `M.` 이름 여섯(`StageRow` `agent_verdict` `claude_argv` `format_report` `normalize_usage` `sum_usage`)은 모두 `runner/measure.py` 에 있다(실측). 실행기 쪽 독스트링은 `5837c32` 에서 끝났다. **확인 grep 은 주석 줄을 뺀다** — `# <include …/>` 잔재의 `# 쓰는 것: run_mode1` 줄은 고치지 않는다:
  ```bash
  grep -rn 'run_mode1\b' runner/run_mode1_5.py runner/run_mode2.py runner/run_grade.py runner/term/ runner/test_run_mode1_5.py runner/test_run_mode2.py runner/test_run_grade.py viz/ test/ tools/ | grep -v ':[0-9]*:#'
  ```
  기대: 출력 없음(`runner/run_grade.py` · `runner/test_run_grade.py` 가 없으면 grep 이 그 경로만 경고한다 — 정상). 커밋 `[test] : mode 1.5 와 2 시험이 run_mode1 대신 measure 를 import 한다`.
- A3: rev.4 A3 본문 그대로(`R._term_script` — `runner/run_mode1_5.py` · `R.script_argv` — `runner/run_mode2.py` · `R.wiki_argv` — `runner/run_mode1.py` 의 `Mode1Machine.wiki_argv` 재수출, 셋 다 실측). 커밋 `[test] : 실행기 스크립트 실재 시험을 mode 별로 가른다`.
- Phase A 끝: 전량 게이트.

**(4) Phase K** — 순서가 중요하다: 생산자(K1 · K2 · K2b · K3 · K4)를 먼저, 소비자(K5 · K6 · K7 · K7b · K8)를 뒤에. K5 는 K4 의 생성물을 읽는다. 시작 전에 §6 의 `before/` 를 HEAD 에서 다시 찍어 둔다(K 는 프롬프트를 일부러 바꾼다 — 의도된 차이만 남아야 한다).

| Task | 구현자 | 정정 · 이월 | 검문 |
|---|---|---|---|
| K1 `machine/manifest.py` | sonnet | ② | `pytest machine/test_manifest.py` |
| K2 `seal-artifacts` 단계 | **opus** | ① ③ ④ | `.venv/bin/python runner/run_mode1.py . --dry-run` 이 `GraphError` 없이 `seal-artifacts` 로 끝 |
| K2b 진입 알림 | sonnet | ⑥ ⑦ · `[estimate]` 첫 독자 | `pytest runner/test_mode1.py -k "estimate or 전량이라고"` |
| K3 `write-wiki` 부분 재작성 · `.bak` | **opus** | ④ ⑧ ⑨ ⑩(`write-wiki#main`) | `pytest runner/ -q` |
| K4 `tools/gen_contract.py` → `contracts/` | sonnet | — | `( cd contracts && shasum -a 256 -c mode1-artifacts.v1.sha256 )` |
| K5 `tools/gen_contract_types.py` → `machine/contract_types.py` | sonnet | — | 왕복 시험 |
| K6 `machine/evidence.py` + collect 관문 | **opus** | ② ⑤ | `pytest machine/test_evidence.py test/test_term.py runner/test_run_mode1_5.py` · `capture` 에서 `mode1_5-ask` 만 다름 |
| K7 `run_mode2.py` 근거 자리 | sonnet | ⑬ · 새 절은 `runner/prompts/agent.md` 에 · `AgentStage.prompt_names` | `pytest runner/test_run_mode2.py` · 게이트 3 |
| K7b `viz/init.py` 상태 한 줄 | sonnet | ⑭ | `pytest test/test_init.py` |
| K8 계약 문서 · 스킬 둘 | sonnet | 스킬 원본은 `~/.claude/skills/*/SKILL.md` — 클라우드에 없으면 저장소 사본만 고치고 "원본 동기화 필요" 를 이 문서에 남긴다 | `pytest test/test_docs_citations.py` |

각 Task 뒤 spec 대조 · 품질 검토. 본체 `.py` 는 §7 승인.

**(5) M1 · M2** — M1 은 rev.4 의 게이트 묶음(`gen_contract.py --check` · `gen_contract_types.py --check` · `npm run doctor` · `machine/evidence.py . --need terms-db,wiki --status` → `Mode 1 봉인 — 없음` 포함). M2 는 `main` fast-forward + 태그 `split-base-2026-10-24` — **push 전에 사용자에게 묻는다**. `Fast-forward` 가 아니면 멈추고 알린다.

## 6. `split-work/` 준비 (저장소 안 · 산출물은 git 밖)

대조 도구는 저장소 뿌리의 **`split-work/`** 에 있다(설명서 `split-work/README.md`). 2026-10-24 Mac 의 `$HOME/LLM-Tools/split-work/` 를 통째로 옮겼고 바깥 폴더는 지웠다 — report-builder 에만 매인 도구였다(다른 프로젝트 참조 0). 산출물 `before*/` · `after*/` · `fixture-shards/` · `patches/` · `frag/` · `reading-mode*.json` 은 이 기계의 절대 경로가 실려 `.gitignore` 로 git 밖이다 — **클라우드에서는 `before/` 를 다시 찍는다.** rev.4 본문의 `$TOOLS_ROOT/split-work/…` 는 `TOOLS_ROOT=$PWD`(저장소 뿌리)로 읽는다 — `capture.sh` 가 자기 폴더의 부모를 기본값으로 잡는다.

1. `out/codegraph-raw/codegraph.json` 이 없으면 `.venv/bin/python bin/report-wiki prep .`.
2. `before/` 를 지금 HEAD 에서 찍고 결정적인지 본다(경로는 상대여도 된다 — `capture.sh` 가 절대 경로로 바꾼다):
   ```bash
   split-work/capture.sh "$PWD" split-work/before && ls split-work/before | wc -l    # 31 = .txt 14 · .raw 14 · modules.dot · classes.dot · report.html
   split-work/capture.sh "$PWD" split-work/before-again && diff -r split-work/before split-work/before-again && rm -r split-work/before-again
   ```
   Phase R 전체가 이 31개를 바이트로 보존했으므로 HEAD 에서 찍어도 기준이 같다. ⚠ 재조사 절(`annotate-retry`)은 샤드 폴더 `split-work/fixture-shards/` 의 **절대 경로**를 글에 싣는다 — 기준과 대조는 같은 자리에서 찍어야 한다(worktree 대조도 샤드 폴더는 본 저장소의 것을 넘긴다).
3. **worktree 에서 `pytest` 를 돌릴 때 `.venv` 를 통째로 심볼릭 링크하지 않는다.** `runner/run_mode1.py` 의 `_bootstrap_venv()` 가 `sys.prefix` 를 `<wt>/.venv` 와 견주는데 링크를 풀면 본 저장소 `.venv` 라 어긋나 `os.execv` 를 끝없이 되풀이한다(수집 단계에서 출력 없이 멈춘다). 꼴:
   ```bash
   git worktree add --detach "$S/wt" HEAD
   mkdir -p "$S/wt/.venv/bin" && cp .venv/pyvenv.cfg "$S/wt/.venv/"
   for f in .venv/bin/*; do ln -s "$PWD/$f" "$S/wt/.venv/bin/"; done
   ln -s "$PWD/.venv/lib" "$S/wt/.venv/lib"; ln -s "$PWD/node_modules" "$S/wt/node_modules"
   # worktree 에서: npm test 먼저(.tmp/lib.mjs 를 굽는다) → .venv/bin/python -m pytest -q → pyright
   git worktree remove --force "$S/wt"; git worktree prune
   ```
   worktree 에는 `out/` 이 없다 — 층 분포 시험은 건너뛰고 위키 시험은 실패한다(정상). 글 28개는 `.venv/bin/python split-work/capture.py "$S/wt" "$S/after" "$PWD/split-work/fixture-shards"` 로, DOT 는 worktree 의 `viz/render_*.py` 를 **본 저장소의** `out/codegraph-raw/codegraph.json` 경로로 돌려 대조한다(DOT 머리 주석에 그 경로가 찍힌다). `report.html` 은 파일 링크에 저장소 경로가 실려 본 저장소에서 적용 뒤 대조한다.
4. 경계 입력 대조: `split-work/edge_dump.py <트리>` 가 Mode 1 프롬프트 함수 · `FIX` · 재조사 절 · `check_shard` 출력 128개를 JSON 으로 stdout 에 낸다. `git archive <기준> | tar -x -C <옛트리>` 와 후보 트리를 각각 `python -I` 로 돌려 `cmp`.
5. R9 보강용 원형: `split-work/r9-gate-proto/`(`stricter.py` · `scan_evasion.py` · `scan_long.py`) — HEAD 기대 출력과 고치는 순서는 `split-work/README.md` 에 있다. ⚠ 셋 다 **첫 인자로 저장소 뿌리를 받는다**(`.venv/bin/python split-work/r9-gate-proto/stricter.py "$PWD"`) — 인자 없이 돌리면 `IndexError`.
6. 그 밖: `split-work/extract.py <파일.py> <줄> <출력>`(파이썬 문자열 → `{{이름}}` 리소스 글) · `split-work/split_reading.py`(A4 — 끝났다).

## 7. 가드레일 · 규약

- **본체 `.py` 승인(사용자 규칙)**: 구현자는 시험 파일 · `.md` · `.toml` · `.tmpl` · 생성물(`contracts/*` · `machine/contract_types.py` · `*/README.md`)은 직접 쓴다. 본체 `.py`(새 파일 포함)는 **저장소에 쓰지 않고** `split-work/patches/<Task>/`(git 밖) 에 완성본(경로의 `/` → `__`)과 `diff -u`(묶음 diff 하나 포함)를 두고, 임시 worktree 에서 후보를 검증한 뒤 `DONE_WITH_CONCERNS — 본체 파일 적용 대기` 로 멈춘다.
  - **클라우드 · auto mode(권한 창이 안 뜬다)**: 오케스트레이터가 diff 를 직접 읽고 spec 대조를 한 뒤 `AskUserQuestion` 으로 승인을 받는다. **미리보기 꼴(사용자가 요구한 것)**: 무엇을 옮기거나 바꾸나(전 → 후 표) · 파이썬 쪽 대표 hunk · **"이전에는 안 되던 것 → 이제 되는 것"** · 확인한 것(시험 · 바이트 대조 수치) · 계획과 다른 점. 선택지는 적용(권장) · 보류 — diff 를 직접 본다 · 거부. 승인 뒤 `cp` + `cmp` 또는 `git apply` 로 적용하고 본 저장소에서 다시 검증한다.
  - Mac(권한 창이 뜨는 세션)이면 `Edit`/`Write` 로 적용해 권한 창에 diff 를 띄운다.
  - 적용 뒤 마무리(전량 pytest · pyright · README 재생성 · 이름으로 `git add` · 커밋 · push)는 오케스트레이터가 직접 해도 된다.
- **커밋**: `[tag] : 한국어 제목` 한 줄. **본문 · 트레일러 없음**(루트 `CLAUDE.md` · `personal-commit-messages` 가 하네스의 `Co-Authored-By` 안내를 이긴다). 파일을 **이름으로** `git add`. `git add -A` 금지. 커밋마다 `git push -u origin survey-per-file-2pass`.
- **커밋 제목은 ASCII 구두점만**(`personal-commit-messages` 의 "제목에는 ASCII 구두점만" 절). 가운뎃점 `·` 는 두 항목이면 `&`, 셋 이상이면 `,` 로 쓰고 `—` · `→` 도 쓰지 않는다. 문서 본문은 이 규칙 밖이다. 분리 작업(`fdb1c3a..`)에서 이 규칙을 어긴 커밋이 **16개**다 — 클라우드 세션 둘(`83eb828` · `b6bd0a4`), 로컬 Mac 세션 열넷(`082d3a9` ~ `04796fe`). 넘김 문서는 "둘뿐" 이라 적었지만 로컬 쪽을 세지 않았다. 이미 push 된 이력이라 고치지 않는다. 서브에이전트에게 주는 제안 커밋 제목도 이 규칙으로 쓴다.
- **검증 명령**: `.venv/bin/python -m pytest -q`(저장소 루트에서) · `npm run typecheck:py` · `npm test` · `npm run typecheck` · `.venv/bin/python tools/gen_readme.py --check machine runner viz tools` · `.venv/bin/python -m pytest test/test_prompt_resources.py -q`.
- **TDD**: rev.4 Task 마다 "실패하는 시험 → 구현 → 통과". 옮기기 Task 는 바이트 대조가 합격 기준.
- **코드 규약**: 주석 · 독스트링 한국어 · 지금 무엇인지만(날짜 · 확신도 · 설계 서사 금지) · `# <include …/>` 블록은 새로 심지도 고치지도 않는다 · `Any` 금지(`test/test_no_any.py`) · 자유 함수 모음 금지(계산은 단계의 `@staticmethod`, 둘 이상이면 믹스인) · LLM 이 읽는 글은 리소스로.
- **검토 발견**: Important 이상은 그 Task 안에서 고친다. Minor 는 묶어 보강하거나 §4.2 로.
- **멈추지 않는다**: Task 사이에 "계속할까요" 를 묻지 않는다. 멈추는 이유는 BLOCKED · 진짜 모호함 · 전부 완료 · 본체 `.py` 승인 대기.
- **병렬**: 구현자는 한 번에 하나. 검토자(읽기 전용)는 다음 구현자와 같이 돌려도 된다 — 단 다음 구현자가 건드릴 파일과 검토 대상이 겹치지 않을 때만, 그리고 검토 보강 커밋이 다음 Task 커밋보다 먼저.

## 8. 병렬 트랙 / 충돌

단일 트랙이다. 백그라운드 에이전트는 세션과 함께 사라진다 — **에이전트 ID 로 재개하려 하지 말고 새로 띄운다.** Mac 에는 이 저장소의 다른 worktree `sandlance`(남의 것 · 다른 경로)가 있다 — 건드리지 않는다. `git worktree prune` 은 없어진 것만 지우니 안전하다.

## 9. 알려진 것 (이 작업과 무관 — 쫓지 말 것)

- `pytest` 빨강 둘(§1)은 분리 전부터 있다. Phase E · B7 이 푼다. 층 분포 값은 기계마다 다르다(Mac `[538, 342, …]` · 클라우드 `[569, 349, …]`).
- `viz/render_classes.py <codegraph> --module machine` 은 Graphviz 15.1.1 에서 `dot -Tsvg` 가 `mincross.c:273 fixLabelOrder` 단언으로 죽는다. DOT 는 정상으로 써진다(`capture.sh` 가 우회한다).
- rev.4 R9 의 "일부러 깨기" 예시(`ask.md` 에 절 표식 붙이기)는 게이트보다 먼저 `sections()` 의 `ValueError: 첫 절 표식 앞에 글이 있다` 로 죽는다 — 게이트는 다른 꼴로 깨 보아 확인했다.

## 10. 변경 기록 (append-only)

| 날짜 | 변경 |
|---|---|
| 2026-10-24 | 첫 작성(Mac). R1 커밋 `53ddd2f` · spec ✅ · 품질 검토 중단. 정정표 14건과 승인 프로토콜 수록 |
| 2026-10-24 | 클라우드 세션 갱신. R1 품질 검토(`9fa0f41` · `e9ddfc3`) · README `59a43fb` · R2 `22c80a3` + `83eb828` · R3(scratch) · R4 `f87e877`(28/28). 이월 사항 · split-work 재생성 · 클라우드 승인 꼴 추가 |
| 2026-10-24 | Mac 세션(오케스트레이터 Fable 5.1 → Opus 5.5). split-work 재생성 · R4 검토 둘 + `eeb4976` · `d00388a` · R5 `b627831` + `95f9758` · R6 `283aec3` + `a3ac974` · R7 `3665cc5` + `850a6a0` · R8 · R9 `36fb98d` + `83c22a1` + `116bd73` · R10 `d598822` + `5837c32` · A1 `1325398` · A4. 정정 ⑤ 를 K6 으로 옮김 · A2 의 include 잔재 편차 · 사용자 결정(R10 · R11 · 도움말 · `str(lang)`) |
| 2026-10-24 | 사용자 지시로 남은 일을 Claude Cloud 로 넘김. 이 판으로 문서를 다시 짰다 — 해결된 이월은 걷어내고 §5 에 Task 별 brief 요지, 저장소 밖 도구 다섯을 `docs/handoffs/split-work-2026-10-24/` 로. R9 품질 검토 결과(With fixes · I1 f-문자열 · I2 부분 문자열 · Minor 열하나)를 §5 (1) 에 그대로 넣었다 — 고치지 않았다 |
| 2026-10-24 | 사용자 지시로 `$HOME/LLM-Tools/split-work/` 를 저장소 뿌리 `split-work/` 로 옮겼다(report-builder 에만 매인 도구 · 바깥 폴더 지움 · 산출물은 `.gitignore`). `capture.sh` 가 인자를 절대 경로로 바꾸게 고쳤다(상대 출력 경로에서 `report.html` 복사가 실패했다). `before/` 를 새 자리에서 다시 찍었다(옛 기준과 차이는 재조사 절의 샤드 경로뿐). R9 검토 원형 셋을 `split-work/r9-gate-proto/` 로. 홈 전용 스킬 다섯을 `.claude/skills/` 에 깊은 복사 |
| 2026-10-24 | 사용자 결정으로 superpowers 를 프로젝트 설정 `.claude/settings.json` 의 `enabledPlugins` 로 켰다(그전에는 git 밖 `.claude/settings.local.json` 에만 있었다). 문서 확인 결과 클라우드 세션에는 닿지 않는다 — §3 에 대안 셋 |
| 2026-10-24 | 사용자 결정 — superpowers 는 claude.ai Project settings > Plugins 에서 켠다(프로젝트 스레드로 진행). §0.1 을 더했다 — 스레드는 `main` 에서 새 브랜치를 따고 · 훅 · 하위 CLAUDE.md · 저장소 스킬을 안 읽는다는 문서 확인과 대응, 붙여 넣을 프로젝트 지시문 |
| 2026-10-24 | 클라우드 스레드 — 시작 절차 · 게이트 재측정(Mac 과 같음) · `before/` 31 · R9 보강 구현자 사용자 중단(변경 0) · R10 검토 결과 미도착 · M2 잠정 결정 · 환경 실측은 `HANDOFF-2026-10-24-cloud-thread-to-local.md`. 로컬 세션이 반영 — §0.1 실측 표와 결론 · `AskUserQuestion` 줄 · §2 · §5 (1) 상태, M2, 재기동 brief 보강 · R11 제안 제목 ASCII · §6 원형 인자 · §7 ASCII 구두점 규칙(어긴 커밋 실제 16개) |
| 2026-10-24 | 로컬 세션 질의 결과 — M2 확정(게이트를 `machine` · `tools` 까지 · `tools/doctor.py` 스크립트를 파일로 · 본체 승인 · 3단계에서 I1 과 함께), R9 보강과 R10 검토는 로컬 세션에서 다시 띄움, 낡은 원격 가지 `claude/lucid-goodall-xdoeou` 삭제(그 가지에만 있던 커밋 0) |
| 2026-10-24 | 로컬 세션 — R9 보강 끝(1단계 `0ba79a3` `a7a66c4` `3c4c4e8` · 본체 `bae47de` `44b55c5` 사용자 승인, 31 동일 · `doctor` 표 동일) · R10 품질 검토 With fixes → `6e9cc72`(시험 셋 · 독스트링 셋 · 호출 꼴, 사용자 승인) · R9 재검토(opus) 띄움 |
| 2026-10-24 | 로컬 세션 — R9 재검토 Ready: Yes · 문서 정리 `128c25b`. 사용자 지시로 여기서 멈추고 클라우드로 넘긴다. 다음은 §5 (2) R11 부터 |
| 2026-10-24 | 클라우드 세션 — R11 커밋 1 `8d71d38`(바이트 고정 시험 넷 · `edge_dump` 경계 입력 209). 커밋 2 후보는 동적 프롬프트 해부와 라이브러리 조사를 거쳐 **버렸다**. 사용자 판단으로 결정 0012 [제안됨] — 프롬프트의 동적 부분을 프롬프트 파일 안 Jinja2 로. §5 (2) 를 R12(R12a~f)로 바꿨다. 구현 전에 (가) 조건부 절의 새 자리 · (나) `fault_line` 의 자리를 사용자에게 보인다 |
| 2026-10-24 | 클라우드 세션 — (가) 조건부 절은 각자 맞는 자리 · (나) 결함 줄 꼴은 `faults.toml` 의 `line` 으로 사용자 결정. 0012 에 적었다(아직 제안됨). 다음은 R12a |
| 2026-10-24 | 클라우드 세션 — R12a ✅ `a6e484d`(`jinja2==3.1.6` · `PROMPT_ENV` · `PromptResource.render_text` · 엄격 검사는 자유 변수 = 넘긴 값 이름. capture 31 · edge_dump 209 바이트 동일 · pytest 728/2/19). MarkupSafe 는 고정하지 않았다(직접 의존만 고정하는 관례). R12a 품질 검토와 R12b 구현을 띄웠다 |
| 2026-10-24 | 클라우드 세션 — R12a 품질 검토에서 결함 셋을 재현했다. 사전 열쇠가 dict 메서드에 가려졌고, `None` 이 "None" 으로 찍혔고, 안 타는 갈래의 없는 필터가 통과했다. 렌더 중 생 예외도 새어 나왔다. 보강 `46b9f5b` 으로 고쳤다(`PromptEnvironment.getattr` · `finalize` · AST 의 필터 · 검사 대조). R12b ✅ `60c500c` — `runner/mode1/faults.toml`(`line` + `[kind.<갈래>]`) · `context.load_fault_table` · `AnnotateSymbolsStage.FAULTS` · `fault_detail`. edge_dump 209 · 캡처 바이트 동일 · pytest 735/2/19. R12f 에 줄 끝 공백 · `{#` 게이트를 더했다. 다음은 R12c |
| 2026-10-24~25 | 클라우드 세션 — R12 끝. R12c `644f6f0` 은 annotate-symbols 절을 13 → 3 으로 줄였다(batch · nonnode · pass2). 재조사 절은 역할 소개 아래에, 범위 · 미조사 절은 심볼 목록과 읽는 법 사이에 둔다. stage 가 행(TypedDict)을 넘긴다. 재조사 절은 batch 와 nonnode 에 복제하고 같음 시험을 둔다(사용자 결정). 개수는 파이썬이 넘긴다(사용자 결정, `|length` 안 씀). `split-work/edge_dump.py` 은퇴, 검토는 capture + diff 다. R12d `aae87e4` 은 write-wiki 절을 4 → 1 로 줄였다(바이트 동일). R12e `47b8f56` 은 agent 의 terms 절을 `{% if %}` 로 바꿨다(바이트 동일). R12f `22d67e0` 에서 게이트가 Jinja2 컴파일 · 줄 끝 공백 · `{#` 를 보고, `PromptResource.free_names` 가 생겼다. `082a1d3` 에서 루트 규약 문장을 고치고 0012 를 확정했다. A2 `f1355c7` · A3 `77fe047`(Mode 1 시험 docstring 의 경위 문장은 주석 규약대로 뺐다). A2 확인 grep 에 `test/test_no_any.py:17` · `test/test_prompt_resources.py:17` 두 줄이 걸린다. 둘 다 파일 목록이라 import 가 아니다. 게이트 pytest 747/2/19 · pyright 0 · npm test 8 · README 4 · doctor OK. 다음은 Phase K(§5 (4)) — 시작 전에 `before/` 를 HEAD 에서 다시 찍는다 |
| 2026-10-31 | 클라우드 세션 — Phase K 끝(§0 커밋 열넷). 대조 기준 `split-work/before/` 를 `0be86cd` 에서 다시 찍었다(31 · 결정적). 생산자(K1 ~ K3) · 소비자(K6 ~ K8) 검토 각 1회 — Critical 1 · Important 7 을 보강으로 고쳤다. capture 31 중 다른 것은 `mode1_5-ask` 둘(`--terms-db` 한 조각 — 정정 ⑤ 의 의도된 차이)뿐 · `report.html` · DOT 같음. M1 ✅. 계획과 다른 것 · 남은 것은 §4.3. 다음은 M2(사용자 승인) |
