# Handoff — rev.4 분리 계획 실행 재개 (2026-10-24, lossless · 클라우드 재개판)

> **이 문서가 다음 세션의 유일한 진입점이다.** Mode 1 / Mode 1.5+2 두 저장소 분리 계획 rev.4 를 서브에이전트 주도로 실행하는 중이다. **Phase R 은 끝났다**(R1~R10). Phase A 는 A1 · A4 가 끝났고 A2 · A3 가 남았다. 그 뒤가 Phase K · M 이다.
> **작성**: 2026-10-24 Mac 세션(R1) → 클라우드(R1 검토 ~ R4) → **Mac 세션(R4 검토 ~ R10 · A1 · A4)** → 사용자 지시로 **클라우드에서 다시 시작**한다. 브랜치 `survey-per-file-2pass` · HEAD `5837c32`(이 문서 커밋 직전).
> **대체하는 것**: 같은 파일의 이전 판. 이전 판의 §5 "바로 다음"(R4 검토 · R5 구현자)은 끝났다.
> ⚠ 시작할 때 `git pull origin survey-per-file-2pass` → `git log --oneline -8` · `git status --short` 를 다시 잰다.

## 0. 한눈에 (TL;DR)

- **무엇을**: `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`(rev.4) 의 Phase **R → A → K → M** 을 이 저장소에서 실행해 `main` 에 fast-forward 한다. 두 저장소로 가르는 B · C 와 위키 재굽기 E 는 그 뒤 별 세션.
- **진척**: R1~R10 ✅ · A1 ✅ · A4 ✅ · **R9 보강 ⬜(검토 Important 둘) · R10 품질 검토 ⬜ · R11 ⬜(사용자 결정) · A2 · A3 ⬜ · K1~K8 ⬜ · M1 · M2 ⬜**.
- **바로 다음**(§5 순서): (0) §6 으로 `split-work/` 와 `before/` 준비 (1) R9 보강(게이트 둘 조이기 + HTML 뼈대 옮기기 — 본체 승인) · R10 품질 검토 (2) R11 — 목록 밖 LLM 글 옮기기 (3) A2 · A3 (4) Phase K (5) M1 · M2.
- **방법**: Task 마다 구현자 1 → spec 검토 → 품질 검토 1. 한 Task 한 커밋(검토 보강은 별 커밋). spec 검토가 "계획서 코드 블록이 글자 그대로 들어갔는가" 면 오케스트레이터가 기계 대조로 한다. **본체 `.py` 는 사용자가 diff 를 보고 승인한다**(§7 — 클라우드는 질문 창).
- **모델(사용자 동의 2026-10-24)**: 오케스트레이터 Opus 5.5 · 구현자 `sonnet` · 검토자 `opus`. 여러 파일을 엮거나 설계 판단이 드는 Task(K2 · K3 · K6 · R11)는 구현자도 `opus`.
- **정본**: rev.4(Task 본문) · 정정표(§4) · 이월 사항(§4.2) · 저장소 밖 도구 사본(`docs/handoffs/split-work-2026-10-24/`, §6).

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
| R9 | 게이트 시험 + Phase R 문서 정리 | ✅ spec ✅ · 품질 **With fixes(미처리)** | Important 둘 · Minor 열하나 — §5 (1) 에 전문. 사용자 지시로 이 세션에서 고치지 않고 넘김 |
| R10 | 남은 문구 → 리소스(A) · 검토 이월 본체 정리(B) | ✅ `d598822` · `5837c32` · 사용자 승인 · **품질 ⬜** | 새 절 — `annotate-symbols.md` 12(`batch-symbol` `batch-symbol-no-deps` `batch-dep` `batch-dep-no-means` `batch-no-deps` `pass2-dep` `pass2-no-deps` `fix-missing` `fix-malformed` `fix-schema` `fix-where` `fix-coverage`) · `write-wiki.md` 3(`page-no-symbols` `lower-page` `no-lower-pages`, 본문은 `main`). `FIX` 는 이름 · 형 그대로, 클래스 뒤 모듈 수준 대입 한 번(`survey.py` 끝). 고정 31 + 경계 입력 128 동일 |
| R11 | 목록 밖 LLM 글 옮기기 | ⬜ **사용자 결정 — 옮긴다** | §5 (2) |
| A1 | 결정 0011 | ✅ `1325398` | 계획 문안 그대로 |
| A2 | Mode 1.5 · 2 시험이 `measure` 를 import | ⬜ 시험만 남음 | 실행기 독스트링은 `5837c32` 에서 끝났다. §5 (3) |
| A3 | 실행기 스크립트 실재 시험 셋 | ⬜ | 시험만. §5 (3) |
| A4 | `split_reading.py` | ✅ 커밋 없음 | 1,318 = mode1 1,025 + mode2 463 − 둘 다 176 + 버림 6. rev.4 어림(960 · 500)보다 갈림이 크지만 경로별 분류는 목록대로다 |
| K1 → K8 | 봉인 · seal 단계 · 진입 알림 · 위키 부분 재작성 · 계약 · 형 생성 · 판정+collect · run_mode2 근거 · init 상태 줄 · 문서/스킬 | ⬜ | rev.4 :1473-3234 · **정정표 §4 가 이긴다** · §5 (4) |
| M1 · M2 | 게이트 여섯 · `main` ff 병합 + 태그 | ⬜ | rev.4 :3235-3259. **`main` 에 미는 것은 사용자에게 먼저 묻는다** |

## 3. 문서 색인

| 문서 | 경로 | git | 역할 |
|---|---|---|---|
| rev.4 계획(사양) | `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md` | 추적 | Task 본문 전부. 서브에이전트에게는 해당 Task 를 **떼어 scratch 파일로** 넘긴다(아래 §5 의 꼴) — 계획서 자체를 읽게 하지 않는다 |
| 저장소 밖 도구 사본 | `docs/handoffs/split-work-2026-10-24/` | 추적 | `capture.py` · `capture.sh` · `extract.py` · `split_reading.py` · `edge_dump.py`. §6 |
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

**기록만**
- `agent_prompt` · `ask_argv` 는 모듈 함수가 `AgentStage.load_prompt` · `AskStage.load_prompt` 를 부른다(단계 소유 `@staticmethod` 꼴과 다르다). 범위 밖.
- `runner/mode1/lang.py` 가 import 때 `config/mode1.toml` 을 읽어, 그 파일이 깨지면 러너 시험 네 파일이 수집 단계에서 죽는다(메시지는 정확하다). `[estimate]` 가 빠져도 그렇다.
- R10 으로 심볼 줄마다 `load_prompt` 가 파일을 다시 읽는다(실행당 심볼 수만큼, 비용 작음).
- `render.mjs.tmpl` 의 `'file://{{bundle}}'` 은 경로에 `'` 가 있거나 Windows 경로면 깨진다(옛 동작 그대로).

## 5. 남은 일 — 순서와 brief 요지

공통: 서브에이전트 brief 에 (가) 이 프로젝트가 무엇이고 Phase R 이 무엇을 했는지 두세 줄 (나) 떼어 둔 Task 본문 파일 경로 (다) 그 Task 에 걸리는 정정표 · 이월 항목 (라) §7 의 승인 프로토콜 (마) worktree `.venv` 꼴(§6-4) (바) 검증 명령과 기대값 (사) 커밋 메시지 글자 그대로 (아) `docs/handoffs/` · `docs/superpowers/` · `docs/my.self/` 를 열지 말 것 을 넣는다.

**(0) 준비** — §6.

**(1) R9 보강 · R10 품질 검토**

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
- 처리 순서 제안: I2 + M1 · M3(게이트 2 줄) · M4 (시험) → 문서 M3 · M5 · M6 · M7 · M8 · M10 · 권고 → I1 (본체 · 승인, 게이트 조이기와 한 커밋) → M2 는 사용자에게 물어 정한다. 끝나면 같은 꼴로 재검토(opus).

*R10 품질 검토* — `opus` · 읽기 전용. 위 R9 보강의 구현자와 같이 돌려도 된다(R10 검토는 `runner/mode1/` 을 읽고, R9 보강은 `test/` · `viz/build.py` · 문서를 고친다).
- R10: 범위 `d6286be..5837c32`. 볼 것 — 새 절 15개와 `prompt_names` · `FIX` 의 모듈 수준 대입(`ClassVar` 선언 + 클래스 뒤 채움)의 위험(import 순서 · 하위 클래스) · 한 낱말 절 둘(`batch-symbol-no-deps` "없음" · `pass2-no-deps` "  (없음)")의 값(사용자가 남기기로 했다 — 결함이 아니면 지적만) · 바이트 보존(§6 의 `edge_dump.py` 로 `git archive d6286be` 대 HEAD) · B 의 독스트링 사실 대조.
- Important 이상은 그 Task 안에서 고친다(본체면 승인). Minor 는 묶어 보강하거나 §4.2 로.

**(2) R11 — 목록 밖 LLM 글 옮기기(사용자 결정 2026-10-24: "같은 방식으로 옮긴다")** — 구현자 `opus`. 대상(`runner/mode1/survey.py`, 줄은 내용으로 찾는다):
- `pending_excerpt` 의 줄 꼴 `"  - %s (%s) %s:%s"`(미조사 의존 절에 실린다).
- `fault_line` 의 `"[%s] %s — %s\n    → %s"`(stderr · 재조사 절 · `runner/check_shard.py` 출력에 함께 나온다).
- 결함 설명 문구 넷 — "샤드 없음" · "계획에 있는데 샤드에 없다" · "샤드에 있는데 계획에 없다" · "where 없음 (kind %s)"(재조사 절에 실린다). **이 넷은 `.bad.why` JSON 에도 기록되는 데이터다** — 기록 바이트도 같아야 한다.
- R10 과 같은 제약: 기존 절 표식만 · 새 서식 · 파서 · 렌더러 기능 금지 · 빈 값 고르기는 파이썬에 · 새 절은 `AnnotateSymbolsStage.prompt_names` 에. 절 수를 보고하고, 옮길 가치가 약한 것은 사용자에게 보이게 한다.
- 합격: 고정 31 동일 + `edge_dump.py` 로 옛 트리(`git archive HEAD`) 대 후보 트리 JSON 동일(필요하면 `pending_excerpt` 경계 입력을 더한다) + 전량 pytest(알려진 둘) + 게이트 3 + pyright 0.
- 커밋 제안: `[refactor] : mode 1 의 미조사 의존 줄 · 결함 줄 · 결함 설명을 프롬프트 리소스로`. 그 뒤 품질 검토(`opus`).

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

## 6. `split-work/` 준비 (저장소 밖 · 커밋하지 않는다)

도구 다섯은 `docs/handoffs/split-work-2026-10-24/` 에 사본이 있다(Mac 의 `$HOME/LLM-Tools/split-work/` 와 바이트로 같다 · 보강 셋이 들어 있다 — `.raw` 사본 · Graphviz 단언 우회 · `TOOLS_ROOT` 기본값).

1. 저장소 **밖** 아무 곳에 `split-work/` 이름으로 복사한다 — `capture.sh` 는 자기 폴더의 부모를 `TOOLS_ROOT` 로 잡고 `$TOOLS_ROOT/split-work/capture.py` 를 부르므로 **폴더 이름이 `split-work` 여야 한다**:
   ```bash
   SW="$(dirname "$PWD")/split-work"; mkdir -p "$SW" && cp docs/handoffs/split-work-2026-10-24/* "$SW/" && chmod +x "$SW/capture.sh"
   ```
2. `out/codegraph-raw/codegraph.json` 이 없으면 `.venv/bin/python bin/report-wiki prep .`.
3. `before/` 를 지금 HEAD 에서 찍고 결정적인지 본다:
   ```bash
   "$SW/capture.sh" "$PWD" "$SW/before" && ls "$SW/before" | wc -l    # 31 = .txt 14 · .raw 14 · modules.dot · classes.dot · report.html
   "$SW/capture.sh" "$PWD" "$SW/before-again" && diff -r "$SW/before" "$SW/before-again" && rm -rf "$SW/before-again"
   ```
   Phase R 전체가 이 31개를 바이트로 보존했으므로 HEAD 에서 찍어도 기준이 같다.
4. **worktree 에서 `pytest` 를 돌릴 때 `.venv` 를 통째로 심볼릭 링크하지 않는다.** `runner/run_mode1.py` 의 `_bootstrap_venv()` 가 `sys.prefix` 를 `<wt>/.venv` 와 견주는데 링크를 풀면 본 저장소 `.venv` 라 어긋나 `os.execv` 를 끝없이 되풀이한다(수집 단계에서 출력 없이 멈춘다). 꼴:
   ```bash
   git worktree add --detach "$S/wt" HEAD
   mkdir -p "$S/wt/.venv/bin" && cp .venv/pyvenv.cfg "$S/wt/.venv/"
   for f in .venv/bin/*; do ln -s "$PWD/$f" "$S/wt/.venv/bin/"; done
   ln -s "$PWD/.venv/lib" "$S/wt/.venv/lib"; ln -s "$PWD/node_modules" "$S/wt/node_modules"
   # worktree 에서: npm test 먼저(.tmp/lib.mjs 를 굽는다) → .venv/bin/python -m pytest -q → pyright
   git worktree remove --force "$S/wt"; git worktree prune
   ```
   worktree 에는 `out/` 이 없다 — 층 분포 시험은 건너뛰고 위키 시험은 실패한다(정상). 글 28개는 `"$PWD/.venv/bin/python" "$SW/capture.py" "$S/wt" "$S/after" "$SW/fixture-shards"` 로, DOT 는 worktree 의 `viz/render_*.py` 를 **본 저장소의** `out/codegraph-raw/codegraph.json` 경로로 돌려 대조한다(DOT 머리 주석에 그 경로가 찍힌다). `report.html` 은 파일 링크에 저장소 경로가 실려 본 저장소에서 적용 뒤 대조한다.
5. 경계 입력 대조: `edge_dump.py <트리>` 가 Mode 1 프롬프트 함수 · `FIX` · 재조사 절 · `check_shard` 출력 128개를 JSON 으로 stdout 에 낸다. `git archive <기준> | tar -x -C <옛트리>` 와 후보 트리를 각각 돌려 `cmp`. `python -I` 로 돌린다.
6. 그 밖: `extract.py <파일.py> <줄> <출력>` — 파이썬 문자열 하나를 `{{이름}}` 리소스 글로 옮긴다(`.format` 이스케이프를 푼다 · f-문자열 식은 `slotN` 으로). `split_reading.py` — A4(끝났다).

## 7. 가드레일 · 규약

- **본체 `.py` 승인(사용자 규칙)**: 구현자는 시험 파일 · `.md` · `.toml` · `.tmpl` · 생성물(`contracts/*` · `machine/contract_types.py` · `*/README.md`)은 직접 쓴다. 본체 `.py`(새 파일 포함)는 **저장소에 쓰지 않고** `$SW/patches/<Task>/` 에 완성본(경로의 `/` → `__`)과 `diff -u`(묶음 diff 하나 포함)를 두고, 임시 worktree 에서 후보를 검증한 뒤 `DONE_WITH_CONCERNS — 본체 파일 적용 대기` 로 멈춘다.
  - **클라우드 · auto mode(권한 창이 안 뜬다)**: 오케스트레이터가 diff 를 직접 읽고 spec 대조를 한 뒤 `AskUserQuestion` 으로 승인을 받는다. **미리보기 꼴(사용자가 요구한 것)**: 무엇을 옮기거나 바꾸나(전 → 후 표) · 파이썬 쪽 대표 hunk · **"이전에는 안 되던 것 → 이제 되는 것"** · 확인한 것(시험 · 바이트 대조 수치) · 계획과 다른 점. 선택지는 적용(권장) · 보류 — diff 를 직접 본다 · 거부. 승인 뒤 `cp` + `cmp` 또는 `git apply` 로 적용하고 본 저장소에서 다시 검증한다.
  - Mac(권한 창이 뜨는 세션)이면 `Edit`/`Write` 로 적용해 권한 창에 diff 를 띄운다.
  - 적용 뒤 마무리(전량 pytest · pyright · README 재생성 · 이름으로 `git add` · 커밋 · push)는 오케스트레이터가 직접 해도 된다.
- **커밋**: `[tag] : 한국어 제목` 한 줄. **본문 · 트레일러 없음**(루트 `CLAUDE.md` · `personal-commit-messages` 가 하네스의 `Co-Authored-By` 안내를 이긴다). 파일을 **이름으로** `git add`. `git add -A` 금지. 커밋마다 `git push -u origin survey-per-file-2pass`.
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
