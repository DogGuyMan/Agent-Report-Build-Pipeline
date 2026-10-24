# Handoff — rev.4 분리 계획 실행 재개 (2026-10-24, lossless)

> **이 문서가 다음 세션의 유일한 진입점이다.** Mode 1 / Mode 1.5+2 두 저장소 분리 계획 rev.4 를 서브에이전트 주도로 실행하는 중이다. Phase R 의 R1 · R2 · R3 · R4 가 끝났다(R4 는 검토 둘이 남았다).
> **작성**: 2026-10-24 Mac 세션(R1) → **2026-10-24 클라우드 세션에서 갱신**(R1 검토 · R2 · R3 · R4). 브랜치 `survey-per-file-2pass` · HEAD `f87e877`(이 문서 커밋 직전).
> **대체하는 것**: 메모리 `resume-entry-point` 가 가리키던 `RESUME-2026-09-11-runner-stage-machine.md`(그쪽은 러너 단계 기계 갈래 — 이 작업과 다른 갈래라 배너는 달지 않는다). 파일 이름이 그대로라 포인터는 고치지 않아도 된다.
> ⚠ 시작할 때 `git pull origin survey-per-file-2pass` → `git log --oneline -8` · `git status --short` 를 다시 잰다.

## 0. 한눈에 (TL;DR)

- **무엇을**: `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`(rev.4, `ddeef75` 로 커밋됨) 의 Phase **R → A → K → M** 을 이 저장소에서 실행해 `main` 에 fast-forward 한다. 두 저장소로 가르는 B · C 와 재굽기 E 는 그 뒤 별 세션.
- **진척**: R1 ✅ · R2 ✅ · R3 ✅(커밋 없음 — 산출물이 클라우드 scratch 에 있었다 → §6 으로 다시 만든다) · **R4 커밋 `f87e877`, spec 검토 ⬜ · 품질 검토 ⬜** · R5~M 미착수.
- **바로 다음 세 걸음**: (1) §6 으로 `split-work/` 와 `before/` 를 다시 만든다 (2) R4 spec · 품질 검토 (3) R5 구현자 — §5.
- **방법**: Task 마다 구현자 1(sonnet) → spec 검토 → 품질 검토 1(opus). 한 Task 한 커밋. **본체 `.py` 는 사용자가 diff 를 보고 승인한다**(§7). spec 검토가 "계획서 코드 블록이 글자 그대로 들어갔는가" 뿐이면 오케스트레이터가 기계 대조로 한다(R2 가 그렇게 됐다).
- **정본 문서**: rev.4(위) · 정정표 14건(§4) · 이 세션의 검토에서 나온 이월 사항(§4.2).

## 1. 상태 (클라우드 실측 2026-10-24 — 다시 잰다)

```
HEAD:    f87e877 [refactor] : mode 1 프롬프트를 단계당 한 파일 리소스로 - 죽은 사본 넷 삭제   ← R4
         e9ddfc3 [update] : tools/template 시험 - 쉼표 목록 이스케이프 잔재 꼴도 고정            ← R1 검토 Minor
         83eb828 [fix] : pipeline - PromptResource 가 틀린 절 표식 · 상대 prompt_dir 을 거부한다  ← R2 검토 보강
         9fa0f41 [fix] : tools/template - 자리가 못 된 {{이름 꼴도 예외다                        ← R1 검토 Important
         22c80a3 [update] : pipeline - PromptResource 믹스인, 단계당 한 파일과 절               ← R2
         59a43fb [docs] : tools README 재생성 - template.py 행                                ← R1 이 남긴 README 표류
         7dfc33a [update] : unused skill                                                    ← 사용자(skill-creator 삭제 — 이제 커밋됨)
         ddeef75 [docs] : 두 저장소 분리 계획 rev.4 와 실행 재개 문서
         53ddd2f [update] : tools/template - 리소스 파일의 {{이름}} 자리를 채운다               ← R1
         fdb1c3a [update] : doctor prompt-audit                                              ← 분리 전 마지막 (rev.4 기준 ref)
Uncommitted: 없음 (이 문서 커밋 뒤)
```

게이트(클라우드, `out/` 있음 · HEAD `f87e877`):

| 게이트 | 값 |
|---|---|
| `pytest -q` | **693 통과 · 2 실패 · 19 건너뜀**. 실패 둘은 알려진 빨강(`machine/test_survey_plan.py::test_이_저장소_실측` — 지금 값 `[569, 349, …]` · `test/test_wiki.py::test_check_는_통과를_통과로_보고한다`) |
| `npm run typecheck:py` | 0 errors |
| `gen_readme.py --check machine runner viz tools` | 4개 일치 |

`out/` 이 없는 새 클론이면 층 분포 시험은 건너뛰고(건너뜀 20) 위키 시험은 `codegraph.json 이 없다` 로 실패한다. `report-wiki prep .` 을 먼저 돌리면 위 표가 된다(2.6초).

## 2. Task 상태표

| Task | 내용 | 상태 | 근거 |
|---|---|---|---|
| R1 | `tools/template.py` 렌더러 | ✅ `53ddd2f` + `9fa0f41` + `e9ddfc3` · spec ✅ · 품질 ✅(재검토 승인) | Important 하나 — 이름 꼴로 시작했지만 자리가 못 된 `{{repo}/bin` · `{{n.}}` 가 조용히 남았다 → `STRAY` 검사. 따옴표로 시작하는 `{{"…` 는 사양 시험이 글자 그대로를 고정해 막지 않는다 |
| R2 | `PromptResource` 믹스인 | ✅ `22c80a3` + `83eb828` · spec ✅(기계 대조) · 품질 ✅ | 보강 셋 — 틀린 절 표식(대문자 · 밑줄 · 앞뒤 공백 · 끝 줄바꿈 없음) `ValueError` · `load_prompt(cls, name, /, **values)` · 절대 경로 아닌 `prompt_dir` `ValueError`. 380 통과 |
| R3 | 옮기기 전을 찍는다 | ✅ 커밋 없음 · **Mac 에 다시 만듦(2026-10-24)** | `$HOME/LLM-Tools/split-work/before/` 31개, 두 번 찍어 같음. 보강 셋째 — `capture.sh` 가 `TOOLS_ROOT` 없을 때 자기 자리에서 기본값을 잡는다 |
| R4 | Mode 1 프롬프트 넷 → `runner/mode1/prompts/` | ✅ `f87e877` + `eeb4976`(시험) · spec ✅(기계 대조 + `e9ddfc3` worktree 대 HEAD 28 동일) · 품질 ✅(Ready: Yes) | 검토 처리: Important — `pipeline.py` 독스트링이 아직 없는 `test/test_prompt_resources.py` 를 가리킨다 → R9 가 만든다(고아 절은 R9 전까지 안 잡힌다). Minor — `hint_prompt` docs 끝 줄바꿈 시험 `eeb4976`. 나머지는 §4.2 | 바이트 대조 `.txt` 14 + `.raw` 14 = **28 동일**(R2 보강 뒤 본 저장소에서 다시 잼). 계획서 편차 하나: `hint_prompt` 는 `load_prompt("lang-hint", docs=docs)[:-1]`(절이 줄바꿈 하나로 끝나 docs 뒤에 1바이트가 붙는다). `annotate-symbols.md` 끝 빈 줄 하나 뗌(출력 같음) |
| R5 | Mode 1.5 · 2 프롬프트 → `runner/prompts/` | ✅ `b627831` + `95f9758`(시험) · spec ✅(기계 대조) · 품질 ✅(With fixes → 시험 셋) · 사용자 승인 | 28 동일. ⑤ 는 K6 으로. 검토: 옮긴 글의 배치 · 줄바꿈 · 명령줄을 바꾸는 돌연변이 9개가 기존 시험을 다 통과 → 시험 셋 `95f9758`(돌연변이 셋을 다시 넣어 잡히는 것 확인). Minor 는 R10 묶음 |
| R6 | 템플릿 일곱 → `viz/templates/{report,dot}/` · `runner/wiki/templates/` | ✅ `283aec3` + `a3ac974`(수정 · 시험) · spec ✅ · 품질 ✅(With fixes → I1 시험 `test/test_templates.py` · I2 `str(lang)` 사용자 승인) · 사용자 승인 | 본 저장소 31 동일(글 28 · DOT 2 · report.html). 편차: 범례 `"\n" + render_file(…).removesuffix("\n")` · `render.mjs.tmpl` 은 계획대로 들여쓰기를 뗐다(임시 파일 바이트만 다르고 HTML 은 같다) · `entry.ts` 끝 줄바꿈 |
| R7 | 모델 id · 비용 어림 · 원본 문서 자리 규칙 → `config/{mode1,report}.toml` | ✅ `3665cc5` + `850a6a0`(시험 강화 · 패턴 계약 주석) · spec ✅ · 품질 ✅(Ready: Yes) · 사용자 승인 | 편차 하나(사용자 결정): `run_mode2.py --model` 도움말은 `(기본: %(default)s)` — `--help` 가 실효값을 보인다 |
| R8 | 옮긴 뒤 대조 | ✅ 커밋 없음 | R7 적용 뒤 본 저장소 `capture.sh` 31 = `before/` 31 (`diff -r` 같음). `a3ac974` 뒤에도 31 같음 |
| R9 | 게이트 시험 + Phase R 문서 정리 | ✅ `36fb98d` + `83c22a1` + `116bd73`(ARCHITECTURE) · spec ✅ · 품질 ⬜ | 전량 두 번 같음(1:1 게이트 안 흔들림). 일부러 깨기는 scratch worktree 에서 — 각 게이트가 실패. 계획의 `ask.md` 깨기 예시는 게이트보다 먼저 `sections()` 의 `ValueError` 로 죽는다 |
| R10 | 남은 문구 옮기기 + 본체 Minor 묶음 | ⬜ (opus 구현 중) | rev.4 :1159-1283 · §4.2. R9 는 본체 .py 없음(게이트 셋이 HEAD 에서 이미 통과 — scratch 실측). R10 은 §4.2 의 사용자 결정 + 본체 Minor 묶음 |
| A1 | 결정 0011 | ✅ `1325398` | 계획 문안 그대로 |
| A2 | Mode 1.5 · 2 시험이 `run_mode1` 대신 `measure` 를 import | ⬜ (R10 커밋 뒤) | **편차**: 두 실행기 머리의 `# 쓰는 것: run_mode1` 줄은 `# <include …/>` 잔재라 고치지 않는다(루트 CLAUDE.md). 그래서 계획의 grep 확인은 주석 줄을 뺀다(`grep -v ':#'` 꼴). 모듈 독스트링 "재는 코드는 `run_mode1.py` 의…" 수정은 본체라 R10 B 승인 묶음에 넣었다 |
| A3 | 실행기 스크립트 실재 시험 셋 | ⬜ (R10 커밋 뒤) | 시험만 |
| A4 | `split-work/split_reading.py` | ✅ 커밋 없음 | 1,318 = mode1 1,025 + mode2 463 − 둘 다 176 + 버림 6. 어림(960 · 500)보다 갈림이 크다 — 경로별 분포를 보니 분류는 계획 목록대로다(시험 파일 · `machine/` 이 mode1 쪽을 키운다) |
| K1 → K8 | 봉인 · seal 단계 · 진입 알림 · 위키 부분 재작성 · 계약 생성 · 형 생성 · 판정+collect · run_mode2 · init 상태 줄 · 문서/스킬 | ⬜ | rev.4 :1473-3234 · **정정표 §4 가 이긴다** |
| M1 · M2 | 게이트 여섯 · `main` ff 병합 + 태그 `split-base-2026-10-24` | ⬜ | rev.4 :3235-3259. `main` 에 미는 것은 사용자에게 먼저 묻는다 |

## 3. 문서 색인

| 문서 | 경로 | git | 역할 |
|---|---|---|---|
| rev.4 계획(사양) | `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md` | 추적(`ddeef75`) | Task 본문 전부. 서브에이전트에게 Task 텍스트를 **붙여 넣어** 준다(파일을 읽게 하지 않는다). `grep -n "^#### Task" <rev.4>` 로 범위를 잡는다 |
| 실행 계획(plan mode) | `~/.claude/plans/docs-superpowers-plans-2026-10-22-split-sprightly-codd.md` | 저장소 밖 · Mac 만 | 순서 · 검문 · 정정표. 내용은 이 문서 §4 에 들어 있다 |
| 결정 기록 | `docs/decisions/0011-…`(A1 이 만든다) | 미작성 | rev.4 A1 에 전문 |
| 메모리 | `~/.claude/projects/-Users-escatrgot-LLM-Tools-report-builder/memory/split-plan-2026-10-22.md` 등 | 저장소 밖 · Mac 만 | 사용자 결정 요약 |

## 4. 확정된 결정 (다시 논쟁하지 않는다) + 정정표

**사용자 결정(2026-10-24)** — 경계는 A3 데이터 계약(스키마 사본 + `docs/codegraph/manifest.json` 봉인) · Mode 1 은 **사람이 부를 때만** 돌고 **묻지 않는다**(예상 비용 한 줄만) · Mode 1.5 는 봉인 없으면 멈추고 낡음·미커밋은 경고 · Mode 2 는 Mode 1 과 독립(봉인 있으면 근거) · 프롬프트는 단계당 한 파일 + `<!-- section: 이름 -->` 절 · 소비자 형은 계약 JSON 에서 생성 · 손댄 위키 장은 `.bak` · 범위 R→A→K→M · 서브에이전트 주도 · **본체 .py 승인 규칙 유지**.

**정정표 — rev.4 를 코드 실물로 고친 열넷(🔵 2026-10-24 탐색).** 해당 Task 를 시킬 때 반드시 brief 에 넣는다. ⑪ 은 R4 에서 소진됐다.

| # | Task | 고칠 것 |
|---|---|---|
| ① | K2 | `VerifyTermsStage`(`runner/mode1/terms.py`)에 `def writes(self, ctx): return [X.TERMS_DB]` 추가. 없으면 `seal-artifacts` 의 `reads` 가 사슬 검사(`pipeline.py:273-305`)에서 `GraphError` |
| ② | K1 · K6 | 봉인의 소스 집합 = `declmap.tracked_files(repo, lang, [])` **그대로 호출**(`git ls-files` 추적 파일만 · `SKIP_DIRS` 성분 제외 · `docs` 제외 없음). `manifest.json` 의 `skip_dirs = sorted(declmap.SKIP_DIRS)`. `evidence.py` 사본은 `git ls-files`(`-co` 없이). 시험 "새 파일도 넣는다" → "미추적 파일은 넣지 않는다" |
| ③ | K2 | `runner/test_mode1.py:475-479` `len(E.ORDER) == 12` → 13 / 12 |
| ④ | K2 · K3 | `context.py` 새 칸은 형 붙은 공장 — `_no_strs() -> set[str]` · `_no_names() -> list[str]` |
| ⑤ | **K6**(R5 에서 옮김) | **K6 이 `--terms-db` 를 필수로 만드는 같은 커밋에서 한다** — R5 에서 넣으면 `--terms-db` 없이 부를 때(`run_mode1_5.py:791` 은 아직 선택 인자) 스킬이 받는 명령이 값 없는 `--terms-db` 로 깨진다. 할 것: `ask_argv(root, plan, workdir, python, terms_db)` 매개변수 추가, `runner/prompts/ask.md` 명령 자리에 `--terms-db {{terms_db}}`, `AskStage.perform`(`run_mode1_5.py:739`)이 `ctx.terms_db` 전달(K6 뒤로는 늘 값이 있다). 시험 `:713-718` 에 `"--terms-db" in prompt`. `split-work/capture.py` 의 `ask_argv(...)` 호출도 맞추고 그 차이는 의도된 차이로 기록 |
| ⑥ | K2b | `estimate_line` 을 `ScheduleBatchesStage.perform` 끝 **과** `run_mode1.py` dry-run 블록(`:255` 근처) 둘에. 세션 수 `sum(len(L.get("batches", [])) or 1 …)` |
| ⑦ | K2b | `DetectChangesStage.perform`: `not os.path.exists(X.snapshot_path(ctx))` 면 `⚠ 증분으로 불렸지만 전량이다 — 지난 지문(snapshot.json)이 없다`(stderr). `scan.py:101` 문구도 같은 꼴 |
| ⑧ | K3 | `runner/wiki/build.py` **안 고친다**(demermaid · check · sidebar 전부 최상위 `*.md` 만 본다). 대신 `.gitignore` 에 `docs/wiki/.bak/` |
| ⑨ | K3 | `wiki.py` 에 `json` · `msgspec` · `from mode1 import diff as D` · `from mode1.scan import DetectChangesStage` import 추가(순환 아님) |
| ⑩ | K3 | `test_write_wiki_는_이미_쓴_장을_건너뛴다`(`:453-464`)는 그대로 통과 — 고치지 않는다 |
| ⑪ | R4 | ~~`lang-hint` 는 이어붙임 문자열 — 손으로~~ **소진(R4)** |
| ⑫ | R5 · K7 | `agent_prompt` 의 `.format(slug=…)` 는 자리가 없다 — 새 호출에서 `slug` 를 뺀다 |
| ⑬ | K7 | `test_run_mode2.py:339-341` — 새 절(`agent#evidence*`)에 `terms.json` 글자를 넣지 않는다 |
| ⑭ | K7b | `viz/init.py` 상태 한 줄은 `docs = listDocs(cwd)` 바로 뒤(`:133` 다음) 한 번 — 세 종료 경로 모두 지난다 |

### 4.1 R1 에서 확정된 규칙
pyright strict 가 `machine/ runner/ viz/ tools/` 를 포함하므로 그 아래 시험 파일의 fixture 는 주석을 붙인다: `tmp_path: Path` · `monkeypatch: pytest.MonkeyPatch` · `capsys: pytest.CaptureFixture[str]` · parametrize 인자도(`text: str`). `test/` 아래는 pyright 밖이라 불필요. rev.4 의 시험 코드에는 이 주석이 빠져 있다 — 구현자 brief 에 매번 적는다.

### 4.2 이월 사항 — 이 세션의 검토에서 나왔다 (해당 Task brief 에 넣는다)

**모든 Task**
- **Step 3 에 README 재생성을 넣는다** — `.venv/bin/python tools/gen_readme.py machine runner viz tools` 뒤 `--check` 가 `README 4개 — 소스와 일치`, 바뀐 README 를 이름으로 `git add`. rev.4 Step 3 들에 빠져 있고 R1 이 실제로 README 표류를 남겼다(`59a43fb` 로 고침). 새 `.py` · 새 함수 · 새 시험 · 독스트링 변경이 모두 README 를 바꾼다.
- 실험 파일은 scratch 에만. **저장소 뿌리에 임시 폴더를 만들지 않는다**(R2 검토자가 `tmpuoesb2kf/` 를 남겼다).
- 병렬로 띄운 구현자가 같은 README 를 다시 구우면 남의 변경이 커밋에 섞인다 — README 를 건드리는 Task 둘은 커밋을 순서대로 한다.

**R5 · R6 (옮기기)**
- `.format` 원문의 `{{`/`}}` 이스케이프는 한 겹으로 푼다(`extract.py` 가 푼다 — 손으로 쓰는 글은 원문과 대조). 렌더러는 이름 꼴로 시작하는 `{{x…` 만 예외로 막고 따옴표로 시작하는 `{{"…` 는 조용히 둔다.
- 값은 전부 `str` — 정수는 `str()`.
- 줄바꿈(R2 검토 N1, 실측): 끝에 이어붙는 조각(`terms_block`)은 앞 `\n` 1 · 뒤 `\n` 1 → 호출부 `"\n" + load_prompt(...)`. `ask_argv` 프롬프트는 앞 0 · 뒤 0 → `.rstrip("\n")`. rev.4 R5 본문이 이미 둘 다 그렇게 적었다. `agent` 본체는 앞 0 · 뒤 1 로 맞다.
- 절 이름은 `[a-z0-9-]` 만(밑줄 금지). `prompt_dir` 는 절대 경로(`os.path.join(ROOT, "runner", "prompts")` — `ROOT` 가 abspath 기반인지 확인).
- 템플릿 일곱의 호출자(`viz/*` · `runner/wiki/build.py`)는 `render_file` 을 쓴다 — R6 에서 오류 글에 파일 이름을 넣을지 판단(넣으면 그 일곱에는 효과가 있다. 지금 `TemplateError` 글에는 파일 이름이 없다).

**R8 (after 대조)**
- `.txt` 는 끝 줄바꿈을 정규화하므로 **`.raw` 도 대조한다**(§6 의 `capture.py` 보강).
- ⑤ 는 K6 으로 옮겨 R8 대조에는 걸리지 않는다 — R8 은 28 전부 같아야 한다. K6 뒤에 다시 찍으면 `mode1_5-ask` 둘만 `--terms-db` 로 다른 것이 의도된 차이다.

**R9 (게이트 시험)**
- `all_subclasses(P.PromptResource)` 가 시험 함수 안 클래스(`runner/test_pipeline.py` 의 `<locals>.S` — `prompt_dir = tmp_path`)를 **GC 시점에 따라** 집는다 → 전량 `pytest` 에서만 "선언했는데 없는 프롬프트" 로 흔들린다. 거른다: `"<locals>" not in c.__qualname__` 그리고 `c.__module__` 이 `test_` 로 시작하지 않을 것.
- 게이트도 `load_prompt` 와 같이 텍스트 모드 `open` 으로 읽는다(rev.4 코드가 이미 그렇다).

**R4 품질 검토에서 넘어온 것**
- ~~`hint_prompt` 의 `[:-1]` → `.removesuffix("\n")`~~ **사용자 승인 · `d00388a`**(28 동일).
- `runner/CLAUDE.md:13` "계산과 **프롬프트는** 단계 클래스의 `@staticmethod`" · `:142` "`mode1/survey.py` 의 **프롬프트 문자열은**…" 이 낡았다 — 산문은 이제 `runner/mode1/prompts/*.md`. Phase R 끝 문서 정리에서 한 줄씩.
- **사용자 결정(2026-10-24): Phase R 끝에 리소스로 옮긴다 — R9 뒤 Task 「R10」.** 옮긴 뒤 R8 대조(28 + DOT · HTML)와 R9 게이트를 다시 돌린다. 대상 — 빈 값 대체 문구가 파이썬에 남았다: `survey.py:81` `"(뜻 없음)"` · `:103` · `:107` `"  (없음 — 너는 최하층이다)"` · `:347` `"  (없음)"` · `wiki.py:99` `"(개괄 — 특정 심볼 없음)"` · `:100` `"  (없음 — 네가 첫 장이다)"`, 목록 줄 꼴(`survey.py:101` · `:343` · `wiki.py:123`), retry 에 실리는 `FIX` 표(`survey.py:150-156`). rev.4 가 그대로 두라고 적었다. 옮기면 작은 절 4~6개가 생긴다(거울 함정 위험). 절 이름은 `[a-z0-9-]`(예: `annotate-symbols#no-deps`). 렌더러에 조건문이 없으니 "값이 비면 이 절" 의 고르기는 파이썬에 남고 글만 리소스로 간다.

**R5 품질 검토에서 넘어온 것 (R10 승인 묶음 · R9)**
- 본체 `.py` — R10 에 함께 보인다: `runner/run_mode2.py:225` 절 머리 주석과 `:229-231` 독스트링("규율을 여기서 말한다" · "나눠 적는다")이 글이 옮겨 가 낡았다 → `runner/prompts/agent.md` 의 절을 가리키게. `runner/run_mode1_5.py:510-512` 도 `runner/prompts/ask.md` 를 가리키게. `runner/run_mode1_5.py:518` `.rstrip("\n")` → `.removesuffix("\n")`(형제 `lang.py` 와 맞춘다 · 템플릿이 자리로 끝나면 `rstrip` 이 값의 줄바꿈을 먹는다).
- 기록만: `agent_prompt` · `ask_argv` 는 모듈 함수가 `AgentStage.load_prompt` · `AskStage.load_prompt` 를 부른다(클래스 → 함수 → 클래스, `cls` 가 아니라 이름에 묶임). 단계 소유 `@staticmethod` 꼴과 다르다. 범위 밖.
- `runner/CLAUDE.md:11-20` "무엇이 여기 있나" 표에 `prompts/` · `mode1/prompts/` 행이 없다 — Phase R 끝 문서 정리.
- `docs/wiki/runner-mode2-spec.md:116` 이 옮겨 간 문구의 자리로 `agent_prompt` 를 인용 — Phase E 재굽기(L2 실패 수는 늘지 않음).
- **R9 게이트 주의**: `prompt_names` 는 상속된다 — `AnnotateFilesStage` 가 `AnnotateSymbolsStage` 의 선언을 물려받아 "중복 선언" 오탐이 난다. 클래스마다 `vars(cls)` 에 직접 선언된 것만 세거나 `(prompt_dir, 이름)` 으로 중복을 없앤다.

**R6 · R7 품질 검토에서 넘어온 것**
- **R10 승인 묶음(본체 .py)**: `viz/init.py:23-24` 의 `str(d["dir"])` · `str(d["pattern"])` 를 뺀다 — 잘못된 설정에서 `run_mode2` 는 ValidationError 인데 `report-spec init` 은 조용히 받아들인다(R7 M1). `runner/run_mode1.py:50-55` 독스트링 · `:200` 주석이 Model ID 자리를 `config/mode1.toml` 로 말하게(R7 M5). TypedDict 넷(`context.py` `ModelsConfig` · `EstimateConfig`, `run_mode2.py` `DocDirConfig` · `ModelsConfig`)에 한 줄 독스트링(R7 M9 — README 설명 칸이 비었다).
- **R9 문서 정리에 넣는다**: `viz/CLAUDE.md:12-19` 표에 `templates/` 행 · `:143-150` 의존 표에 `여기 → ../tools/template.py`(그리고 "시각축은 잎" 문장 고침) · `runner/CLAUDE.md:19` `wiki/` 행 "전부 .py" · `:117` 에 `tools/template.py`(pipeline · wiki/build) · `tools/CLAUDE.md:7-14` 표에 `template.py` 행 · `viz/init.py:89` 주석과 `viz/CLAUDE.md:126` "네 값" → 다섯(주석은 본체라 R10) · `machine/CLAUDE.md:152-154` · `ARCHITECTURE.md:135-137` "`--model` 기본값 하나" → `config/mode1.toml` · `.claude/skills/spec-review-dashboard/SKILL.md:40-41` 과 홈 원본 `~/.claude/skills/spec-review-dashboard/SKILL.md:40` "DOC_DIRS 두 곳"(원본 먼저) · `remain-process-merged.md:133-136` 체크박스 · `runner/test_run_mode2.py:214-216` `test_doc_dirs_matches_the_javascript_side` 이름 · 독스트링(README 도) · `test/CLAUDE.md:12-21` 표에 `test_config.py` · `test_templates.py` · `test_prompt_resources.py` · 루트 `CLAUDE.md` 에 새 최상위 `config/`(나침반 · 성격축 · 소유).
- **Phase E 로**: `machine/terms-reading.json` 이 R6 다섯 파일을 인용하는 레코드 43건이 줄이 밀려 낡았다(terms_db L2 가 잡는다 · Mode 1 증분으로 갱신). `ARCHITECTURE.md` 의 줄 인용 몇은 EOF 를 넘는다(`test_docs_citations` 는 파일 존재만 본다).
- **Phase B 로**: `tools/template.py` 는 **두 저장소 모두에 필요하다** — Mode 1 쪽 `viz/render_*.py` · `runner/wiki/build.py` 와 Mode 2 쪽 `viz/init.py` · `viz/build.py` 가 함께 import 한다. B1 경로 목록 양쪽에 넣는다.
- **사용자 판단 거리(급하지 않음)**: ① `config/report.toml` 을 두 파서(msgspec · tomllib)가 읽는다 — `tools/` 에 읽기 함수 하나를 두고 둘이 함께 쓰면 모양 · 검증이 하나가 된다(소비자 2 → 공유). 지금 판도 시험으로 지켜져 합리적이다. ② `mode2_agent = "opus"` 는 별명이다 — 옆의 `config/mode1.toml` 은 "별명이 아니라 정확한 ID" 원칙을 적었다. 값은 옛것을 보존한 것.
- 기록만: `lang.py` 가 import 때 설정을 읽어 `config/mode1.toml` 이 깨지면 러너 시험 네 파일이 수집 단계에서 죽는다(메시지는 정확하다). `viz/init.py` 의 `tomllib` 으로 3.11 미만 해석기에서 안 돈다 — `doctor` 가 3.12 미만을 이미 막는다.

**기록만 — 범위 밖, 사용자 몫**
- 프롬프트 예외(`KeyError` · `ValueError` · `TemplateError` · `FileNotFoundError`)는 `Pipeline.run` 이 `FAIL` 행으로 바꾸지 않는다 — 지금 `msgspec.DecodeError` 만 잡는다(`pipeline.py:363` 근처). 단계 도중 터지면 프로세스가 죽고, `survey_files.py` 의 풀에 줄 선 세션은 프로세스 끝까지 돈다. 정책 변경이다.
- 템플릿 BOM: `utf-8-sig` 로 읽지 않는다 — `render_file` 과 `load_prompt` 를 함께 바꿔야 한다.

## 5. 남은 일 — 바로 다음

**(0) 준비** — §6 으로 `split-work/` 스크립트 셋과 `before/` 를 다시 만든다.

**(1) R4 spec 검토** — 오케스트레이터가 직접: rev.4 R4 Step 3 의 코드 블록이 `runner/mode1/{context,lang,survey,wiki}.py` 에 들어 있는지 기계 대조(편차는 `hint_prompt` 의 `[:-1]` 과 그 위 주석 한 줄뿐이어야 한다) + §6 의 `before/` 를 HEAD 에서 다시 찍어 28 동일을 한 번 더 본다.

**(2) R4 품질 검토** — `general-purpose` · `opus` · 읽기 전용 · 범위 `e9ddfc3..f87e877`. 볼 것: 리소스 넷의 절 표식과 `prompt_names` 1:1 · `hint_prompt[:-1]` 의 가정(절이 정확히 `\n` 하나로 끝난다)이 시험으로 고정됐는가(없으면 시험 하나 제안) · 남은 `# <include …/>` 블록이 옮겨 간 함수를 가리키지 않는가 · `runner/mode1/prompts/*.md` 가 위키 인용(`docs/wiki`)을 더 낡게 하는 것은 정상(Phase E). 실험 파일은 scratch 에만.

**(3) R5 구현자** — rev.4 `:806-852` 전문을 붙인다. `sonnet`. 본체 `.py` = `runner/run_mode2.py` · `runner/run_mode1_5.py` → §7. 정정 ⑫ 와 §4.1 · §4.2 를 brief 에(⑤ 는 K6 으로 옮겼다 — 정정표). 합격 기준 = worktree 에서 `capture.py` 를 돌려 `before/` 와 대조 — 28 전부 동일. 커밋 `[refactor] : mode 1.5 와 2 프롬프트를 runner/prompts 리소스로`.

그 뒤는 rev.4 순서대로 R6 … K8 → M1 → M2. 각 Phase 끝 전량 게이트 — 기대값 "알려진 빨강 둘만 실패".

## 6. `split-work/` 다시 만들기 (R3 산출물 — 커밋하지 않는다)

R3 의 스크립트와 `before/` 는 클라우드 scratch 에 있었고 사라졌다. Mac 에서는 `$TOOLS_ROOT/split-work/`(= `$HOME/LLM-Tools/split-work/`)에 둔다.

1. rev.4 R3 의 코드 블록 셋을 **글자 그대로** 뽑는다(손으로 옮기지 않는다):
   ```bash
   SW="$TOOLS_ROOT/split-work"; mkdir -p "$SW"
   .venv/bin/python - "$SW" <<'EOF'
   import re, sys
   lines = open("docs/superpowers/plans/2026-10-22-split-mode1-and-report.md", encoding="utf-8").read().splitlines(keepends=True)
   start = next(i for i, l in enumerate(lines) if l.startswith("#### Task R3"))
   end = next(i for i, l in enumerate(lines) if l.startswith("#### Task R4"))
   blocks = re.findall(r"```(?:python|bash)\n(.*?)```", "".join(lines[start:end]), re.S)
   for body, name in zip(blocks[:3], ["capture.py", "capture.sh", "extract.py"]):
       open(f"{sys.argv[1]}/{name}", "w", encoding="utf-8").write(body)
   EOF
   chmod +x "$SW/capture.sh"
   ```
2. **보강 둘**(이 세션에서 더했다):
   - `capture.py` 의 `put()` 끝에 정규화 없는 사본을 더한다 — 끝 줄바꿈 표류를 보려고:
     ```python
         with open(os.path.join(OUT, name + ".raw"), "w", encoding="utf-8") as f:
             f.write(text)
     ```
   - `capture.sh` 의 `render_classes.py` 줄 끝을 `>/dev/null 2>&1 || test -s "$OUT/classes.dot"` 로. Graphviz 15.1.1 이 `--module machine` 그림에서 `mincross.c:273: fixLabelOrder` 단언으로 죽는다(이 작업과 무관 · 분리 전부터). DOT 는 `dot` 을 부르기 전에 끝까지 써지므로(`viz/render_classes.py:465`) 대조에는 지장이 없다.
3. `out/codegraph-raw/codegraph.json` 이 없으면 `.venv/bin/python bin/report-wiki prep .`.
4. **`before/` 는 HEAD(`f87e877` 이후, R5 착수 전)에서 찍어도 된다** — R4 가 Mode 1 글 열넷을 바이트로 보존했음을 28/28 로 쟀고, 그 밖의 글을 내는 코드는 `9fa0f41` 이후 바뀌지 않았다(`git diff --stat 9fa0f41..f87e877 -- runner/run_mode2.py runner/run_mode1_5.py viz/ runner/wiki/` 가 비어야 한다 — 확인하고 찍는다):
   ```bash
   "$SW/capture.sh" "$PWD" "$SW/before" && ls "$SW/before" | wc -l    # 31 = .txt 14 · .raw 14 · modules.dot · classes.dot · report.html
   "$SW/capture.sh" "$PWD" "$SW/before-again" && diff -r "$SW/before" "$SW/before-again" && rm -rf "$SW/before-again"   # 결정적인지
   ```
5. ⚠ **worktree 에서 `pytest` 를 돌릴 때 `.venv` 를 통째로 심볼릭 링크하지 않는다**(R5 구현자 실측). `runner/run_mode1.py` 의 `_bootstrap_venv()` 가 `sys.prefix` 를 `<wt>/.venv` 와 견주는데 링크를 풀면 본 저장소 `.venv` 라 어긋나 `os.execv` 를 끝없이 되풀이한다 — 수집 단계에서 출력 없이 멈춘다. 꼴: `mkdir <wt>/.venv <wt>/.venv/bin` · `cp .venv/pyvenv.cfg <wt>/.venv/` · `bin/` 안은 파일마다 링크 · `lib` 은 폴더 링크. `capture.py` 만 돌릴 때(본 저장소 `.venv/bin/python` 으로 부른다)는 통째 링크로 된다.
   구현자의 worktree 검증 꼴(R4 에서 썼다): `git worktree add --detach $S/wt HEAD` → `.venv`(위 꼴) · `node_modules` 를 심볼릭 링크 → 리소스와 후보를 복사 → `pytest runner/` · `typecheck:py` → `.venv/bin/python $SW/capture.py $S/wt $S/after $SW/fixture-shards` → `before/*.txt` · `before/*.raw` 를 `cmp` → `git worktree remove --force` · `prune`. worktree 에는 `out/` 이 없으니 `capture.py` 만 돌린다(DOT · HTML 은 R6 · R8 에서 본 저장소로).

## 7. 가드레일 · 규약

- **본체 `.py` 승인 프로토콜(사용자 규칙 유지)**: 구현자는 시험 파일 · `.md` · `.toml` · `.tmpl` · 생성물은 직접 쓴다. 본체 `.py`(새 파일 포함)는 **저장소에 쓰지 않고** `$HOME/LLM-Tools/split-work/patches/<Task>/` 에 완성본과 `diff -u` 를 두고, **임시 worktree 에서 후보를 검증한 뒤**(§6-5) `DONE_WITH_CONCERNS — 본체 파일 적용 대기` 로 멈춘다.
  - **Mac(권한 창이 뜬다)**: 오케스트레이터가 `Write`/`Edit` 로 적용해 권한 창에 diff 가 뜨게 한다.
  - **클라우드 auto mode(권한 창이 안 뜬다)**: 적용 전에 `AskUserQuestion` 으로 diff 를 보여 승인받고, 승인 뒤 `Edit`(또는 승인받은 후보를 `cp` 하고 `cmp` 로 바이트 확인)로 적용. 이 세션의 R2 · R1 수정 · R2 보강 · R4 가 이 꼴이다.
  - 적용 뒤 같은 구현자에게 Step 3(시험 · pyright · README · 이름 박아 `git add` · 커밋 · 자가 검토)을 시킨다. 세션이 재시작돼 구현자에게 닿지 않으면 오케스트레이터가 직접 한다.
- **커밋**: `[tag] : 한국어 제목` 한 줄. 본문 · 트레일러 없음(루트 `CLAUDE.md` 가 하네스 안내를 이긴다). 파일을 **이름으로** `git add`. `git add -A` 금지. 커밋마다 `git push -u origin survey-per-file-2pass`.
- **검증 명령**: `.venv/bin/python -m pytest …`(저장소 루트에서) · `npm run typecheck:py`(Mac 은 `/opt/homebrew/bin/pyright --project pyrightconfig.json` 도 된다) · `npm test` · `npm run typecheck` · `gen_readme.py --check`.
- **TDD**: rev.4 Task 마다 "실패하는 시험 → 구현 → 통과". 옮기기 Task(R4~R6)는 시험 대신 **바이트 대조가 합격 기준**이다.
- **코드 규약**: 주석 · 독스트링 한국어, 날짜 · 확신도 · 설계 서사 금지, `# <include …/>` 블록 새로 심지 않음(있는 것도 고치지 않음), `Any` 금지(`test/test_no_any.py` COVERED), 자유 함수 모음 금지(계산은 단계의 `@staticmethod`, 둘 이상이면 믹스인).
- **모델**: 구현자 `sonnet`(기계적 Task) · 검토자 `opus`. K3 · K6 처럼 여러 파일을 엮는 Task 는 구현자도 `opus`.
- **검토 발견의 처리**: Important 이상은 그 Task 안에서 고친다(새 구현자 → 승인 → 같은 검토자에게 재검토). Minor 는 비용과 막는 것을 견줘 한 묶음 보강으로 하거나 §4.2 로 이월한다 — 이 세션은 R1 Minor 하나 · R2 Minor 셋을 고쳤고 나머지를 §4.2 로 넘겼다.
- **멈추지 않는다**: Task 사이에 사용자에게 "계속할까요" 를 묻지 않는다. 멈추는 이유는 BLOCKED · 진짜 모호함 · 전부 완료 · 본체 `.py` 승인 대기 넷뿐.

## 8. 병렬 트랙 / 충돌

단일 트랙이다. 백그라운드 에이전트는 세션과 함께 사라진다 — **에이전트 ID 로 재개하려 하지 말고 새로 띄운다.** 사용자 소유의 미추적 변경은 지금 없다(`skill-creator` 삭제는 `7dfc33a` 로 커밋됐다).

## 9. 알려진 것 (이 작업과 무관 — 쫓지 말 것)

- `pytest` 빨강 둘(§1)은 분리 전부터 있다. Phase E · B7 이 푼다.
- `docs/wiki` 의 L2 인용 낡음 — Phase R 이 줄을 더 밀어도 정상. Phase E 재굽기가 푼다.
- `viz/render_classes.py <codegraph> --module machine` 은 Graphviz 15.1.1 에서 `dot -Tsvg` 가 `mincross.c:273 fixLabelOrder` 단언으로 죽는다(클라우드 실측). DOT 는 정상으로 써진다.

## 10. 변경 기록 (append-only)

| 날짜 | 변경 |
|---|---|
| 2026-10-24 | 첫 작성(Mac). R1 커밋 `53ddd2f` · spec ✅ · 품질 검토 중단. 정정표 14건과 승인 프로토콜 수록 |
| 2026-10-24 | 클라우드 세션 갱신. R1 품질 검토(Important 1 → `9fa0f41` · Minor → `e9ddfc3`) · README 표류 `59a43fb` · R2 `22c80a3` + 보강 `83eb828` · R3(scratch) · R4 `f87e877`(28/28). §4.2 이월 사항 · §6 split-work 재생성 · §7 클라우드 승인 꼴 추가. 사용자 지시로 R4 검토부터는 다음 세션(Claude Code)에서 |
