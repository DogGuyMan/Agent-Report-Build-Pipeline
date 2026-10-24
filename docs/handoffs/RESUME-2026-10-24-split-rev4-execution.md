# Handoff — rev.4 분리 계획 실행 재개 (2026-10-24, lossless)

> **이 문서가 다음 세션의 유일한 진입점이다.** Mode 1 / Mode 1.5+2 두 저장소 분리 계획 rev.4 를 서브에이전트 주도로 실행하는 중이고, Task R1 이 커밋됐다(spec 검토 ✅ · 품질 검토는 사용량 한도로 **중단됨**).
> **작성**: 2026-10-24 · 브랜치 `survey-per-file-2pass` · HEAD `53ddd2f`.
> **대체하는 것**: 메모리 `resume-entry-point` 가 가리키던 `RESUME-2026-09-11-runner-stage-machine.md`(그쪽은 러너 단계 기계 갈래 — 이 작업과 다른 갈래라 배너는 달지 않는다).
> ⚠ 시작할 때 `git log --oneline -5` · `git status --short` 를 다시 잰다.

## 0. 한눈에 (TL;DR)

- **무엇을**: `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`(rev.4, **아직 git 미추적 `??`**) 의 Phase **R → A → K → M** 을 이 저장소에서 실행해 `main` 에 fast-forward 한다. 두 저장소로 가르는 B · C 와 재굽기 E 는 그 뒤 별 세션.
- **진척**: R1 커밋 `53ddd2f` · R1 spec 검토 ✅ · **R1 품질 검토 ⬜(에이전트가 중단됨 — 다시 띄운다)** · R2~M 미착수.
- **바로 다음 한 걸음**: R1 품질 검토 서브에이전트를 다시 띄운다(§5 의 brief). 승인(✅)이면 R2 구현자 dispatch.
- **방법**: `superpowers:subagent-driven-development` — Task 마다 구현자 1(sonnet) → spec 검토 1(opus) → 품질 검토 1(opus). 한 Task 한 커밋. **본체 `.py` 는 사용자가 권한 창에서 diff 를 보고 승인한다**(§7 프로토콜).
- **정본 문서**: rev.4(위) · 실행 계획 `~/.claude/plans/docs-superpowers-plans-2026-10-22-split-sprightly-codd.md`(**이 기계에만 있다** — 그 핵심인 정정표 14건은 §4 에 그대로 옮겼다).

## 1. 상태 (작성 시점 실측 — 다시 잰다)

```
HEAD:    53ddd2f [update] : tools/template - 리소스 파일의 {{이름}} 자리를 채운다   ← R1 (이 작업)
         fdb1c3a [update] : doctor prompt-audit                                       ← 분리 전 마지막 (rev.4 기준 ref)
Branch:  survey-per-file-2pass (main 보다 42 커밋 앞 · main 에만 있는 커밋 0)
Uncommitted (이 작업 것):   ?? docs/superpowers/plans/2026-10-22-split-mode1-and-report.md   ← rev.4. A1 커밋에 함께 넣는다
Uncommitted (내 것 아님):   D .agents/skills/skill-creator/** (8) · D .claude/skills/skill-creator · M skills-lock.json
                           ← 사용자가 벤더 스킬을 지운 것으로 보인다. 절대 스테이징하지 않는다. git add -A 금지
Scratch (저장소 밖):        $HOME/LLM-Tools/split-work/patches/R1/{tools__template.py, R1.diff}
```

게이트 실측(분리 전 · 지금도 같아야 한다): `pytest -q` → **665 통과 · 2 실패 · 19 건너뜀** + R1 의 6. 실패 둘은 알려진 빨강(`test/test_wiki.py::test_check_는_통과를_통과로_보고한다` · `machine/test_survey_plan.py::test_이_저장소_실측`). pyright `0 errors`.

## 2. Task 상태표

| Task | 내용 | 상태 | 근거 |
|---|---|---|---|
| R1 | `tools/template.py` 렌더러 + `tools/test_template.py` + `test/test_no_any.py` COVERED | ✅ 커밋 `53ddd2f` · spec ✅ | 9 통과 · pyright 0. 유일한 편차: `tmp_path: Path` 주석(pyright strict 가 `tools/` 를 봄 — 정당) |
| R1 품질 검토 | code-quality reviewer | ⬜ **중단됨** | 다시 띄운다 — §5 |
| R2 | `PromptResource` 믹스인 in `runner/pipeline.py` | ⬜ | rev.4 :370-488 |
| R3 → R9 | before 찍기 · 프롬프트 넷 · 프롬프트 둘 · 템플릿 일곱 · config toml · after 대조 · 게이트 시험 | ⬜ | rev.4 :489-1283 |
| A1 → A4 | 결정 0011 · 시험 결합 끊기 둘 · 레코드 분리 스크립트 | ⬜ | rev.4 :1284-1472 |
| K1 → K8 | 봉인 · seal 단계 · 진입 알림 · 위키 부분 재작성 · 계약 생성 · 형 생성 · 판정+collect · run_mode2 · init 상태 줄 · 문서/스킬 | ⬜ | rev.4 :1473-3234 · **정정표 §4 가 이긴다** |
| M1 · M2 | 게이트 여섯 · `main` ff 병합 + 태그 `split-base-2026-10-24` | ⬜ | rev.4 :3235-3259 |

## 3. 문서 색인

| 문서 | 경로 | git | 역할 |
|---|---|---|---|
| rev.4 계획(사양) | `docs/superpowers/plans/2026-10-22-split-mode1-and-report.md` | **미추적** (디스크엔 있다) | Task 본문 전부. 서브에이전트에게 Task 텍스트를 **붙여 넣어** 준다(파일을 읽게 하지 않는다) |
| 실행 계획(plan mode) | `~/.claude/plans/docs-superpowers-plans-2026-10-22-split-sprightly-codd.md` | 저장소 밖 · 이 기계만 | 순서 · 검문 · 정정표. 내용은 이 문서 §4 · §5 에 들어 있다 |
| 결정 기록 | `docs/decisions/0011-…`(A1 이 만든다) | 미작성 | rev.4 A1 에 전문 |
| 메모리 | `~/.claude/projects/-Users-escatrgot-LLM-Tools-report-builder/memory/split-plan-2026-10-22.md` 등 | 저장소 밖 | 사용자 결정 요약 |

## 4. 확정된 결정 (다시 논쟁하지 않는다) + 정정표

**사용자 결정(2026-10-24)** — 경계는 A3 데이터 계약(스키마 사본 + `docs/codegraph/manifest.json` 봉인) · Mode 1 은 **사람이 부를 때만** 돌고 **묻지 않는다**(예상 비용 한 줄만) · Mode 1.5 는 봉인 없으면 멈추고 낡음·미커밋은 경고 · Mode 2 는 Mode 1 과 독립(봉인 있으면 근거) · 프롬프트는 단계당 한 파일 + `<!-- section: 이름 -->` 절 · 소비자 형은 계약 JSON 에서 생성 · 손댄 위키 장은 `.bak` · 범위 R→A→K→M · 서브에이전트 주도 · **본체 .py 승인 규칙 유지**.

**정정표 — rev.4 를 코드 실물로 고친 열넷(🔵 2026-10-24 탐색).** 해당 Task 를 시킬 때 반드시 brief 에 넣는다.

| # | Task | 고칠 것 |
|---|---|---|
| ① | K2 | `VerifyTermsStage`(`runner/mode1/terms.py`)에 `def writes(self, ctx): return [X.TERMS_DB]` 추가. 없으면 `seal-artifacts` 의 `reads` 가 사슬 검사(`pipeline.py:273-305`)에서 `GraphError` |
| ② | K1 · K6 | 봉인의 소스 집합 = `declmap.tracked_files(repo, lang, [])` **그대로 호출**(`git ls-files` 추적 파일만 · `SKIP_DIRS` 성분 제외 · `docs` 제외 없음). `manifest.json` 의 `skip_dirs = sorted(declmap.SKIP_DIRS)`. `evidence.py` 사본은 `git ls-files`(`-co` 없이). 시험 "새 파일도 넣는다" → "미추적 파일은 넣지 않는다" |
| ③ | K2 | `runner/test_mode1.py:475-479` `len(E.ORDER) == 12` → 13 / 12 |
| ④ | K2 · K3 | `context.py` 새 칸은 형 붙은 공장 — `_no_strs() -> set[str]` · `_no_names() -> list[str]` |
| ⑤ | R5 · K6 | `ask_argv(root, plan, workdir, python, terms_db)` 매개변수 추가, `runner/prompts/ask.md` 명령 자리에 `--terms-db {{terms_db}}`, `AskStage.perform`(`run_mode1_5.py:739`)이 `ctx.terms_db or ""` 전달. 시험 `:713-718` 에 `"--terms-db" in prompt` |
| ⑥ | K2b | `estimate_line` 을 `ScheduleBatchesStage.perform` 끝 **과** `run_mode1.py` dry-run 블록(`:255` 근처) 둘에. 세션 수 `sum(len(L.get("batches", [])) or 1 …)` |
| ⑦ | K2b | `DetectChangesStage.perform`: `not os.path.exists(X.snapshot_path(ctx))` 면 `⚠ 증분으로 불렸지만 전량이다 — 지난 지문(snapshot.json)이 없다`(stderr). `scan.py:101` 문구도 같은 꼴 |
| ⑧ | K3 | `runner/wiki/build.py` **안 고친다**(demermaid · check · sidebar 전부 최상위 `*.md` 만 본다). 대신 `.gitignore` 에 `docs/wiki/.bak/` |
| ⑨ | K3 | `wiki.py` 에 `json` · `msgspec` · `from mode1 import diff as D` · `from mode1.scan import DetectChangesStage` import 추가(순환 아님) |
| ⑩ | K3 | `test_write_wiki_는_이미_쓴_장을_건너뛴다`(`:453-464`)는 그대로 통과 — 고치지 않는다 |
| ⑪ | R4 | `lang-hint` 는 이어붙임 문자열 — `extract.py` 쓰지 않고 손으로(rev.4 대로) |
| ⑫ | R5 · K7 | `agent_prompt` 의 `.format(slug=…)` 는 자리가 없다 — 새 호출에서 `slug` 를 뺀다 |
| ⑬ | K7 | `test_run_mode2.py:339-341` — 새 절(`agent#evidence*`)에 `terms.json` 글자를 넣지 않는다 |
| ⑭ | K7b | `viz/init.py` 상태 한 줄은 `docs = listDocs(cwd)` 바로 뒤(`:133` 다음) 한 번 — 세 종료 경로 모두 지난다 |

**R1 에서 추가로 확정된 규칙** — pyright strict 가 `machine/ runner/ viz/ tools/` 를 포함하므로 그 아래 시험 파일의 fixture 는 주석을 붙인다: `tmp_path: Path` · `monkeypatch: pytest.MonkeyPatch` · `capsys: pytest.CaptureFixture[str]`. `test/` 아래는 pyright 밖이라 불필요. rev.4 의 시험 코드에는 이 주석이 빠져 있다 — 구현자 brief 에 매번 적는다.

## 5. 남은 일 — 바로 다음 두 dispatch

**(1) R1 품질 검토 재실행** — `general-purpose` · model `opus` · 읽기 전용. 범위 `fdb1c3a..53ddd2f`. 템플릿은 `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/requesting-code-review/code-reviewer.md`. 검토 질문: `re.sub` 람다 치환에서 값 속 백슬래시 안전성 · `{{ name }}` 공백 · `{{{a}}}` 같은 비정상 괄호 · 빈 글 · 열두 프롬프트 + 일곱 템플릿이 쓰게 될 때 바뀔 것. 명령: `.venv/bin/python -m pytest tools/test_template.py test/test_no_any.py -q`(9 통과) · `/opt/homebrew/bin/pyright --project pyrightconfig.json | tail -1`(0 errors). 결과가 ✅ 면 (2). Important 이상이 있으면 R1 구현자(새로 띄움)가 고치고 다시 검토.

**(2) R2 구현자** — rev.4 `:370-488` 전문을 붙인다. `general-purpose` · model `sonnet`. 본체 `.py` = `runner/pipeline.py` 하나 → §7 프로토콜(scratch 에 완성본 + diff, 보고 후 멈춤). 시험 `runner/test_pipeline.py` 끝 다섯은 구현자가 직접 쓰고 실패를 본다(`import pytest` 는 이미 있다 🔵 `:9`). 추가 지시: 머리 import 에 `import re` · `from typing import ClassVar, Generic, TypeVar`; `sys.path.insert(0, runner dir)`(`:22`) 아래에 ROOT 삽입 + `from tools.template import render`. 커밋 `[update] : pipeline - PromptResource 믹스인, 단계당 한 파일과 절`. 검문: `pytest runner/ -q` 실패 0 · `runner/test_import_isolation.py` 초록 · pyright 0.

그 뒤는 rev.4 순서대로 R3 … K8 → M1 → M2. 각 Phase 끝 전량 게이트 — 기대값 "알려진 빨강 둘만 실패".

## 6. 병렬 트랙 / 충돌

단일 트랙이다. 이 세션이 띄운 백그라운드 에이전트는 세션과 함께 사라진다 — **에이전트 ID 로 재개하려 하지 말고 새로 띄운다.** 사용자가 만든 미추적 변경(§1 "내 것 아님")만 피한다.

| 파일 | 소유 |
|---|---|
| `.agents/skills/skill-creator/**` · `.claude/skills/skill-creator` · `skills-lock.json` | 사용자(이 작업 밖). 스테이징 금지 |
| 그 밖 전부 | 이 작업 |

## 7. 가드레일 · 규약

- **본체 `.py` 승인 프로토콜(사용자 규칙 유지)**: 구현자는 시험 파일 · `.md` · `.toml` · `.tmpl` · 생성물은 직접 쓴다. 본체 `.py`(새 파일 포함)는 **저장소에 쓰지 않고** `$HOME/LLM-Tools/split-work/patches/<Task>/` 에 완성본과 `diff -u` 를 두고 `DONE_WITH_CONCERNS — 본체 파일 적용 대기` 로 멈춘다. 오케스트레이터(나)가 그 내용을 `Write`/`Edit` 로 적용해 **권한 창에 diff 가 뜨게** 한다. 적용 뒤 `SendMessage` 로 같은 구현자에게 "Step 3(시험 · pyright · 이름 박아 `git add` · 커밋 · 자가 검토)" 를 시킨다. R1 이 이 꼴로 됐다.
- **커밋**: `[tag] : 한국어 제목` 한 줄. 본문 · `Co-Authored-By` 없음(사용자 규칙이 하네스 안내를 이긴다). 파일을 **이름으로** `git add`. `git add -A` 금지.
- **검증 명령**: `.venv/bin/python -m pytest …`(저장소 루트에서) · `npm run typecheck:py` 또는 `/opt/homebrew/bin/pyright --project pyrightconfig.json` · `npm test` · `npm run typecheck`.
- **TDD**: rev.4 Task 마다 "실패하는 시험 → 구현 → 통과" 순서. 지킨다.
- **코드 규약**: 주석 · 독스트링 한국어, 날짜 · 확신도 · 설계 서사 금지, `# <include …/>` 블록 새로 심지 않음, `Any` 금지(`test/test_no_any.py` COVERED), 자유 함수 모음 금지(계산은 단계의 `@staticmethod`, 둘 이상이면 믹스인).
- **모델**: 구현자 `sonnet`(기계적 Task) · 검토자 `opus`. K3 · K6 처럼 여러 파일을 엮는 Task 는 구현자도 `opus`.
- **멈추지 않는다**: Task 사이에 사용자에게 "계속할까요" 를 묻지 않는다. 멈추는 이유는 BLOCKED · 진짜 모호함 · 전부 완료 · 본체 `.py` 승인 대기 넷뿐.

## 8. 유실 대비 — 커밋되지 않은 핵심

rev.4 문서(`docs/superpowers/plans/2026-10-22-split-mode1-and-report.md`, 3,913줄)는 디스크에 있고 미추적이다. 다른 기계로 가려면 먼저 커밋한다:
```bash
git add docs/superpowers/plans/2026-10-22-split-mode1-and-report.md docs/handoffs/RESUME-2026-10-24-split-rev4-execution.md
git commit -m "[docs] : 두 저장소 분리 계획 rev.4 와 실행 재개 문서"
```
(A1 에서 결정 0011 과 함께 넣어도 된다 — 둘 중 하나만.)

## 9. 알려진 것 (이 작업과 무관 — 쫓지 말 것)

- `pytest` 빨강 둘(§1)은 분리 전부터 있다. Phase E · B7 이 푼다.
- `runner/mode1/prompt/*.md` 넷은 아무도 읽지 않는 죽은 사본 — R4 가 지운다.
- `docs/wiki` 의 L2 인용 43건 낡음 — Phase R 이 줄을 더 밀어도 정상. Phase E 재굽기가 푼다.

## 10. 변경 기록 (append-only)

| 날짜 | 변경 |
|---|---|
| 2026-10-24 | 첫 작성. R1 커밋 `53ddd2f` · spec ✅ · 품질 검토 중단. 정정표 14건과 승인 프로토콜 수록 |
