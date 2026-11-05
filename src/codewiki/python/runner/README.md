# `src/codewiki/python/runner/` — Mode 1 실행기와 단계. 코드베이스를 읽어 위키를 만드는 순서를 잡고 자식 프로세스를 띄운다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`check_shard.py`](check_shard.py) | 샤드 파일 하나를 기계 검문한다. 배치 세션이 끝내기 전에 스스로 돌리는 문이다. |
| [`mode1/__init__.py`](mode1/__init__.py) | — |
| [`mode1/context.py`](mode1/context.py) | Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다. |
| [`mode1/diff.py`](mode1/diff.py) | `changes.json` 의 꼴. 옛 판(지문)과 새 판(지금 소스)을 대조한 결과가 여기 남는다. |
| [`mode1/edges.py`](mode1/edges.py) | Mode 1 의 흐름 — 단계 순서 · 전이표 하나 · 팩토리. 단계는 자기 다음을 모른다. |
| [`mode1/graph.py`](mode1/graph.py) | `collect-graph` · `schedule-batches`. 코드 지도를 만들고 층과 배치로 나눈다. |
| [`mode1/lang.py`](mode1/lang.py) | `lang-hint` · `lang-decide`. 언어 하나를 제안받고 결정론으로 채택한다. |
| [`mode1/machine_stage.py`](mode1/machine_stage.py) | 자식 프로세스 하나를 띄우는 Mode 1 단계의 베이스. 대상 저장소가 작업 폴더다. |
| [`mode1/measured.py`](mode1/measured.py) | 측정 표의 행을 스스로 내는 단계의 믹스인. |
| [`mode1/resume.py`](mode1/resume.py) | 재개 JSON. 모든 중단이 이것을 남기고, 팩토리가 이것을 읽어 멈춘 자리부터 짓는다. |
| [`mode1/scan.py`](mode1/scan.py) | `detect-changes` · `snapshot-sources`. 옛 지문과 지금 소스를 대조하고, 조사가 해낸 뒤 지문을 찍는다. |
| [`mode1/seal.py`](mode1/seal.py) | `seal-artifacts`. 이 실행에서 검사를 통과하고 지금 소스를 다시 읽은 산출물을 docs/codegraph 에 봉인한다. |
| [`mode1/survey.py`](mode1/survey.py) | `annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다. |
| [`mode1/survey_files.py`](mode1/survey_files.py) | `annotate-symbols` 의 파일 전략. 파일 하나가 세션 하나, 가중치 순, 장벽 없는 풀. |
| [`mode1/terms.py`](mode1/terms.py) | `verify-terms`. 읽기 레코드를 인용 검사하고 용어 DB 로 투영한다. |
| [`mode1/wiki.py`](mode1/wiki.py) | `outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다. |
| [`run_mode1.py`](run_mode1.py) | Mode 1(코드베이스 위키) 파이프라인을 단계 기계 위에서 돌리고 단계마다 시간과 토큰을 재는 실행기. |
| [`wiki/build.py`](wiki/build.py) | — |
| [`wiki/check.py`](wiki/check.py) | — |
| [`wiki/clang_doc.py`](wiki/clang_doc.py) | — |
| [`wiki/compdb.py`](wiki/compdb.py) | — |
| [`wiki/paths.py`](wiki/paths.py) | — |
| [`wiki/prep.py`](wiki/prep.py) | — |

---

## `check_shard.py`

샤드 파일 하나를 기계 검문한다. 배치 세션이 끝내기 전에 스스로 돌리는 문이다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `context.py`

Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ModelsConfig`** | *class* | `[models]` — 배치 · 목차 · 장 세션의 Model 과 `lang-hint` 의 Model. |
| **`EstimateConfig`** | *class* | `[estimate]` — 배치당 비용 어림(USD)의 하한과 상한. |
| **`Mode1Config`** | *class* | `resource/codewiki/config.toml`. |
| `load_config` | `(path: str = CONFIG_PATH) -> Mode1Config` | 설정 파일을 형으로 읽는다. 꼴이 안 맞으면 msgspec 예외 — 조용히 기본값으로 가지 않는다. |
| **`ShardUse`** | *class* |  |
| **`ShardRecord`** | *class* | `where` 는 `module` · `external` 만 없어도 된다 — 그 규칙은 형이 아니라 검문이 본다. |
| **`ShardFault`** | *class* | `at` 은 결함의 자리 — 문법이면 `byte N`, 꼴이면 `$[...].칸`, where 면 레코드 키. |
| **`FaultTable`** | *class* | `faults.toml` — `line` 은 결함 하나를 찍는 꼴, `kind` 는 갈래마다 `fix` 와 `detail…` 글. |
| `load_fault_table` | `(path: str = FAULTS_PATH) -> FaultTable` | 결함 표를 형으로 읽는다. 꼴이 안 맞거나 갈래 이름이 `FaultKind` 밖이면 msgspec 예외. |
| **`SymbolRow`** | *class* | 배치 프롬프트의 심볼 줄 하나. `deps` 는 의존 대상의 이름 — 이름표에 없는 id 는 id 그대로다. |
| **`DepRow`** | *class* | 배치 프롬프트의 아래층 발췌 한 줄 — 레코드가 이미 있는 의존 대상. `means` 는 빈 글일 수 있다. |
| **`PendingRow`** | *class* | 배치 프롬프트의 미조사 의존 줄 하나 — 레코드가 아직 없는 의존 대상의 코드 지도 칸들. |
| **`Pass2DepRow`** | *class* | 2패스 프롬프트의 의존 대상 한 줄. `means` · `does` 는 빈 글일 수 있다. |
| **`RetryInputs`** | *class* | 재조사 절의 값 — 지난 시도의 결함 줄들(`fault_line`)과 격리된 샤드 자리. `faults` 가 비면 절이 실리지 않는다. |
| **`LowerPageRow`** | *class* | 위키 장 프롬프트의 이미 선 장 한 줄 — 파일명과 제목. |
| **`UnresolvedRow`** | *class* | `unresolved.csv` 의 한 줄 — 얕게 쓴 레코드(`key`) 하나가 기다리는 의존 대상(`dep`) 하나. |
| **`DroppedUse`** | *class* | `dropped-uses.csv` 의 한 줄 — 병합 보정이 레코드에서 떼어 낸 `uses[]` 하나 또는 `shallow` 이름 하나. |
| **`WikiPage`** | *class* | `outline.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다. |
| `_no_records` | `() -> Records` | `field(default_factory=dict)` 는 원소 형을 잃는다. 형이 붙은 빈 사전을 낸다. |
| `_no_pages` | `() -> Pages` |  |
| `_no_ints` | `() -> list[int]` |  |
| `_no_levels` | `() -> dict[str, int]` |  |
| `_no_strs` | `() -> set[str]` |  |
| `_no_names` | `() -> list[str]` |  |
| **`Mode1Context`** | *class* | 칸마다 이름과 형이 있다. 자루(dict)는 없다. |
| `raw_dir` | `(c: Mode1Context) -> str` |  |
| **`CodeGraphDoc`** | *class* | `codegraph.json` 의 최상위만. 노드 안은 기계축 선언(`survey_plan.CodeGraph`)이 실물과 |
| **`GraphVerifiedDoc`** | *class* | `graph-verified.json` 의 두 칸 — 단계 경계는 이것만 본다. 전체 꼴은 `verify_graph.PassedDoc` 다. |
| **`LangSelect`** | *class* | `lang-select.json`. `language` 는 못 골랐으면 `null` 이다. |
| **`Outline`** | *class* | `outline.json`. |
| `reading_path` | `(repo: str, root: str) -> str` | 전수조사 원본 `terms-reading.json` 의 자리. |
| `snapshot_path` | `(c: Mode1Context) -> str` | 읽을 지문 파일. `snapshot.json` 이 없고 옛 이름 `warmup.json` 이 있으면 그것을 읽는다. |

---

## `diff.py`

`changes.json` 의 꼴. 옛 판(지문)과 새 판(지금 소스)을 대조한 결과가 여기 남는다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`WarmupDiff`** | *class* | `targets` 가 `None` 이면 판정 불가 = 전량이다. |
| `write_diff` | `(path: str, verdicts: warmup.Verdicts, targets: list[str] \| None, hops: int, tracked: int) -> WarmupDiff` |  |
| `read_diff` | `(path: str) -> WarmupDiff \| None` | 없으면 `None`. 있는데 꼴이 틀리면 예외다 — 드라이버가 받는다. |
| `all_files` | `(d: WarmupDiff) -> set[str]` | 지금 존재하는 추적 파일 전체. `삭제됨` 은 뺀다. |

---

## `edges.py`

Mode 1 의 흐름 — 단계 순서 · 전이표 하나 · 팩토리. 단계는 자기 다음을 모른다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `restart_from` | `(failed_at: str \| None) -> str \| None` | 재개 문서의 실패 단계에서 실제로 다시 시작할 단계. |
| `graph_name` | `(ctx: Mode1Context) -> str` | 전량/증분과 전략이 이름을 가른다 — `resume.json` 이 이 이름으로 자기 그래프를 알아본다. |
| `stages_for` | `(ctx: Mode1Context) -> dict[str, P.Stage[Mode1Context]]` | 전략이 고르는 단계는 하나뿐이다 — annotate-symbols. |
| `expand` | `(names: Iterable[str]) -> list[str]` |  |
| `plan_stages` | `(only: Iterable[str] \| None, skip: Iterable[str] \| None, cold: bool = False) -> list[str]` | `--only` · `--skip` · 전량 여부만 본다. 재개 건너뛰기는 갈래(SKIP)와 재개 JSON 이 한다. |
| `build_mode1_graph` | `(ctx: Mode1Context, only: Iterable[str] \| None, skip: Iterable[str] \| None, start_at: str \| None = None) -> P.StageDagGraph[Mode1Context]` | 진입점에서 부른다. `start_at` 은 재개 JSON 이 준 단계다 — 그 앞을 잘라 낸다. |

---

## `graph.py`

`collect-graph` · `schedule-batches`. 코드 지도를 만들고 층과 배치로 나눈다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`CollectGraphStage`** | *class* | 정적 수집 → 코드 지도. 전량이면 `--force`, 증분이면 `--diff changes.json`. |
| `CollectGraphStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `CollectGraphStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `CollectGraphStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| **`VerifyGraphStage`** | *class* | 코드 지도를 LLM 단계 앞에서 검사한다. 결함이 있으면 결함 JSON 옆에 핸드오프를 남기고 멈춘다. |
| `VerifyGraphStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `VerifyGraphStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `VerifyGraphStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `VerifyGraphStage.handoff_text` | `(cls, repo: str, codegraph: str, doc: verify_graph.FaultsDoc) -> str` | 결함 문서를 이어받을 핸드오프 글로. 코드별로 묶어 많은 순, 예시는 `EXAMPLES` 개까지. |
| `VerifyGraphStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| **`ScheduleBatchesStage`** | *class* | 코드 지도를 배치로. 층 전략은 위상 층으로 나누고 증분이면 diff 의 `targets` 로 좁힌다. |
| `ScheduleBatchesStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `ScheduleBatchesStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `ScheduleBatchesStage.plan_summary` | `(plan: survey_plan.SurveyPlan) -> list[str]` | 층·배치 수를 줄 목록으로. `--dry-run` 과 `schedule-batches` 단계가 같은 글을 쓴다. |
| `ScheduleBatchesStage.session_count` | `(plan: survey_plan.SurveyPlan) -> int` | 계획이 띄울 전수조사(`annotate-symbols`) 세션 수. 배치가 없는 층(비노드 층)은 한 세션이다. 위키 · 목차 세션은 세지 않는다. |
| `ScheduleBatchesStage.estimate_line` | `(n_sessions: int, cfg: X.EstimateConfig, full: bool) -> str` | `전수조사 세션 N개 · 예상 $lo~hi · 증분\|전량`. 범위는 resource/codewiki/config.toml 의 [estimate]. |
| `ScheduleBatchesStage.stale_verification` | `(codegraph: str, verified: str) -> str` | 성공 기록이 지금 지도의 것이 아니면 그 이유를, 맞으면 빈 문자열을 낸다. |
| `ScheduleBatchesStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `lang.py`

`lang-hint` · `lang-decide`. 언어 하나를 제안받고 결정론으로 채택한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`LangHintStage`** | *class* | 루트 문서를 읽혀 언어 하나를 제안받는다. 못 받아도 막지 않는다 — 관문이 아니다. |
| `LangHintStage.model` | `(self, ctx: Mode1Context) -> str` |  |
| `LangHintStage.repo` | `(self, ctx: Mode1Context) -> str` |  |
| `LangHintStage.hint_prompt` | `(docs: str) -> str` |  |
| `LangHintStage.docs` | `(self, ctx: Mode1Context) -> str` | 루트 문서 묶음. `lang_select.py --print-docs` 가 고른다. |
| `LangHintStage.prompt` | `(self, ctx: Mode1Context) -> str` |  |
| `LangHintStage.jobs` | `(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]` |  |
| `LangHintStage.harvest` | `(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome` |  |
| **`LangDecideStage`** | *class* | 제안을 결정론으로 기각하거나 채택해 `lang-select.json` 을 쓴다. |
| `LangDecideStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `LangDecideStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |

---

## `machine_stage.py`

자식 프로세스 하나를 띄우는 Mode 1 단계의 베이스. 대상 저장소가 작업 폴더다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Mode1Machine`** | *class* | 자식 프로세스 하나. 대상 저장소가 작업 폴더다. |
| `Mode1Machine.cwd` | `(self, ctx: Mode1Context) -> str` |  |
| `Mode1Machine.wiki_argv` | `(python: str, root: str, script: str, repo: str) -> list[str]` | `src/codewiki/python/runner/wiki/*.py` 하나를 부른다. |

---

## `measured.py`

측정 표의 행을 스스로 내는 단계의 믹스인.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Measured`** | *class* | 측정 표의 행(`measure.StageRow`) 하나를 스스로 내는 단계 — 토큰 0, 자기 이름, 경과 초. |
| `Measured.row` | `(self, t0: float, ok: bool, why: str = '') -> M.StageRow` |  |

---

## `resume.py`

재개 JSON. 모든 중단이 이것을 남기고, 팩토리가 이것을 읽어 멈춘 자리부터 짓는다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ResumeDoc`** | *class* | `verified` 는 이 실행까지 검사를 통과한 산출물 종류다. 재개한 실행이 이어받는다. 없는 문서도 읽힌다. |
| `write_resume` | `(path: str, graph: str, rows: list[M.StageRow], order: list[str], verified: Iterable[str]) -> ResumeDoc \| None` | 실패한 행이 없으면 아무것도 쓰지 않고 `None`. 있으면 쓴다. |
| `read_resume` | `(path: str) -> ResumeDoc \| None` | 없으면 `None`. 있는데 꼴이 틀리면 예외다. |
| `start_stage` | `(doc: ResumeDoc \| None, for_graph: str) -> str \| None` | 이 그래프용 재개 문서면 시작할 단계를, 아니면 `None`. |
| `carried_verified` | `(doc: ResumeDoc \| None, for_graph: str) -> set[str]` | 이 그래프용 재개 문서면 앞선 실행이 검사를 통과시킨 산출물 종류를, 아니면 빈 집합. |

---

## `scan.py`

`detect-changes` · `snapshot-sources`. 옛 지문과 지금 소스를 대조하고, 조사가 해낸 뒤 지문을 찍는다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`SnapshotScan`** | *class* | 옛 지문과 지금 소스를 대조하는 한 벌. `detect-changes` 와 `snapshot-sources` 가 상속한다. |
| `SnapshotScan.lang_of` | `(codegraph_path: str \| None) -> str \| None` | 코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다. |
| `SnapshotScan.lang_for` | `(ctx: Mode1Context) -> str \| None` | 언어. `lang-select.json` 을 먼저, 없으면 코드 지도를 본다. |
| `SnapshotScan.scan_snapshot` | `(ctx: Mode1Context) -> tuple[warmup.Verdicts, warmup.Manifest, str] \| None` | 지금 소스를 훑어 옛 지문과 대조한다. `(판정, 새 지문, 지문 파일 경로)`. |
| **`DetectChangesStage`** | *class* | 옛 지문과 지금 소스를 대조해 `changes.json` 을 쓴다. **증분 그래프에만 있다.** |
| `DetectChangesStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `DetectChangesStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `DetectChangesStage.changed_seed` | `(판정: warmup.Verdicts) -> list[str]` | 다시 읽어야 할 파일의 씨앗. **`재읽기` 와 `위치만` 의 합집합이다.** |
| `DetectChangesStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| **`SnapshotSourcesStage`** | *class* | 전수조사가 해낸 뒤에만 지문을 찍는다. |
| `SnapshotSourcesStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `SnapshotSourcesStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `seal.py`

`seal-artifacts`. 이 실행에서 검사를 통과하고 지금 소스를 다시 읽은 산출물을 docs/codegraph 에 봉인한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`SealArtifactsStage`** | *class* | `src/codewiki/python/machine/manifest.py seal` 을 부른다. 싣는 종류는 `ctx.verified` 에서 따라잡지 못한 위키를 뺀 것이고, 비었으면 부르지 않고 실패 행 하나로 `FAIL` 이다. |
| `SealArtifactsStage.producer_commit` | `(root: str) -> str` | 봉인한 도구의 판. git 밖이면 `unknown`. |
| `SealArtifactsStage.mark_superseded` | `(repo: str, stage: str, producer_commit: str) -> bool` | 실패한 실행 뒤 **이전 봉인**에 표식을 적는다. 봉인이 없거나 계약 꼴이 아니면 False. 봉인 자체는 새로 쓰지 않는다. |
| `SealArtifactsStage.sealable` | `(verified: Iterable[str], raw: str) -> list[str]` | 봉인할 종류. 위키는 `write-wiki` 가 지금 지문을 따라잡았다고 적었을 때만 싣는다(`manifest.wiki_caught_up`). |
| `SealArtifactsStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `SealArtifactsStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `SealArtifactsStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `SealArtifactsStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `survey.py`

`annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`AnnotateSymbolsStage`** | *class* | 배치 하나 = 세션 하나. 층 사이에 이어지는 값(`baseline` · `merged`)은 **문맥 칸**에 둔다. |
| `AnnotateSymbolsStage.repo` | `(self, ctx: Mode1Context) -> str` |  |
| `AnnotateSymbolsStage.prompt` | `(self, ctx: Mode1Context) -> str` |  |
| `AnnotateSymbolsStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `AnnotateSymbolsStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `AnnotateSymbolsStage.shard_dir` | `(ctx: Mode1Context) -> str` |  |
| `AnnotateSymbolsStage.name_of` | `(plan: survey_plan.SurveyPlan) -> dict[str, str]` | 계획 전체의 `id -> name`. `depends_on` 은 노드 id 이고 레코드 키는 이름이라 이 표로 건넌다. |
| `AnnotateSymbolsStage.dep_excerpt` | `(merged: Mapping[str, Mapping[str, object]], batch: survey_plan.PlanBatch, name_of: Mapping[str, str]) -> list[DepRow]` | 배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만, 이름 순의 줄로 낸다. |
| `AnnotateSymbolsStage.survey_batch_prompt` | `(repo: str, root: str, batch: survey_plan.PlanBatch, deps: Sequence[DepRow], targets: Sequence[str] \| None = None, total: int = 0, pending: Sequence[PendingRow] = (), name_of: Mapping[str, str] \| None = None, faults: Sequence[str] = (), bad: str = '') -> str` | 배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다. |
| `AnnotateSymbolsStage.pending_excerpt` | `(merged: Mapping[str, Mapping[str, object]], batch: survey_plan.PlanBatch, nodes: Mapping[str, Mapping[str, object]]) -> list[PendingRow]` | `depends_on` 중 **아직 레코드가 없는** 것을 id 순의 줄로 — 이름 · 종류 · 파일 · 줄. 세션이 열지 않고 볼 최소 정보다. |
| `AnnotateSymbolsStage.nonnode_prompt` | `(repo: str, root: str, faults: Sequence[str] = (), bad: str = '') -> str` | K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다. |
| `AnnotateSymbolsStage.write_schema` | `(path: str) -> None` | `ShardRecords` 의 JSON Schema 를 읽기 전용으로 쓴다. 배치 세션이 읽는 견본이자 검문의 형이다. |
| `AnnotateSymbolsStage.fault` | `(kind: FaultKind, batch: str, path: str, at: str, detail: str) -> ShardFault` |  |
| `AnnotateSymbolsStage.fault_detail` | `(kind: FaultKind, name: str = 'detail', **values) -> str` | 결함 표의 결함 설명 `kind.<갈래>.<name>` 을 `values` 로 렌더한다. 인자가 위치 전용이라 값 이름이 `kind` 여도 된다. |
| `AnnotateSymbolsStage.check_shard` | `(raw: bytes, batch: str = '', path: str = '') -> list[ShardFault]` | 샤드 하나의 결함 목록. 문법 → 꼴 → `where` 규칙 순으로 보고, 앞이 틀리면 뒤는 보지 않는다. |
| `AnnotateSymbolsStage.fault_line` | `(f: ShardFault) -> str` | 결함 하나를 사람이 읽을 줄로 — 결함 표의 `line` 꼴. 재조사 절 · stderr · check_shard 명령이 이 줄을 찍는다. |
| `AnnotateSymbolsStage.plan_ids` | `(plan: survey_plan.SurveyPlan) -> list[str]` | 계획이 띄우는 세션의 이름 전부 — 배치 id 들과, 비노드 층이 있으면 `NONNODE`. |
| `AnnotateSymbolsStage.check_coverage` | `(raw: bytes, batch: survey_plan.PlanBatch, path: str) -> list[ShardFault]` | 계획의 심볼 이름과 샤드의 키를 양방향으로 대조한다. 문법·꼴이 맞은 뒤에만 부른다. |
| `AnnotateSymbolsStage.check_shards` | `(shard_dir: str, plan: survey_plan.SurveyPlan) -> dict[str, list[ShardFault]]` | 계획의 배치마다 샤드를 찾아 검문한다 — 문법·꼴·where 가 맞으면 coverage 까지. 틀린 것만 `{배치: 결함들}`. |
| `AnnotateSymbolsStage.quarantine` | `(shard_dir: str, bid: str, faults: Sequence[ShardFault] = ()) -> str` | 틀린 샤드를 `.json.bad` 로 옮기고 결함들을 `.json.bad.why` 에 JSON 으로 남긴다. |
| `AnnotateSymbolsStage.load_faults` | `(shard_dir: str, bid: str) -> list[ShardFault]` | 격리 사유. 없거나 꼴이 틀리면 빈 목록 — 낡은 사유로 재조사를 오도하지 않는다. |
| `AnnotateSymbolsStage.clear_quarantine` | `(shard_dir: str, bid: str) -> None` | 검문을 통과한 배치의 옛 격리 흔적을 치운다. 남기면 다음 재조사가 낡은 오류를 받는다. |
| `AnnotateSymbolsStage.retry_inputs` | `(shard_dir: str, bid: str) -> RetryInputs` | 재조사 절의 값 — 격리 사유의 결함마다 `fault_line` 과, 격리된 샤드 자리. 사유가 없으면 결함 줄이 빈다. |
| `AnnotateSymbolsStage.shallow_of` | `(rec: Mapping[str, object]) -> list[str]` | 레코드의 `shallow` 를 이름 목록으로 좁힌다. 없거나 목록이 아니면 빈 목록. |
| `AnnotateSymbolsStage.into_of` | `(cg: X.CodeGraphDoc) -> dict[str, int]` | 심볼 이름마다 **다른 파일에서** 들어오는 간선 수 — 얕게 쓴 레코드를 다듬을 가치의 척도다. |
| `AnnotateSymbolsStage.unresolved_rows` | `(merged: Mapping[str, Mapping[str, object]], weight: Mapping[str, float], into: Mapping[str, int], known: Collection[str], queued: Collection[str] = ()) -> list[UnresolvedRow]` | `shallow` 를 가진 레코드마다 의존 대상 한 줄. `into` 의 키 집합이 "계획에 있는 이름" 이다. |
| `AnnotateSymbolsStage.unresolved_csv` | `(rows: Sequence[UnresolvedRow]) -> str` |  |
| `AnnotateSymbolsStage.pass2_prompt` | `(repo: str, root: str, bid: str, file: str, shallow: Mapping[str, Mapping[str, object]], deps: Mapping[str, Mapping[str, object]]) -> str` | 2패스 — 파일을 다시 읽지 않는다. 얕게 쓴 레코드와, 이제 조사된 의존 대상의 뜻만 받아 다듬는다. |
| `AnnotateSymbolsStage.apply_pass2` | `(shard_dir: str, bid: str) -> list[ShardFault]` | 2패스 샤드를 검문하고 원 샤드의 **같은 키만** 덮는다. 틀리면 원 샤드를 두고 결함을 낸다. |
| `AnnotateSymbolsStage.load_records` | `(path: str) -> Records` | 있으면 읽어 사전으로 좁혀 내고, 없거나 사전이 아니면 `{}`. |
| `AnnotateSymbolsStage.merge_shards` | `(shard_dir: str, existing: Records \| None) -> Records` | 샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.** |
| `AnnotateSymbolsStage.normalize_records` | `(got: Records, ids: Mapping[str, str]) -> tuple[Records, list[X.DroppedUse]]` | `uses[].to` 와 `shallow` 를 레코드 키로 맞춘다. 노드 id 는 이름으로 바꾸고, 어느 키도 아닌 것은 떼어 기록한다. |
| `AnnotateSymbolsStage.dropped_csv` | `(rows: Sequence[X.DroppedUse]) -> str` | `dropped-uses.csv` 본문. label 만 따옴표로 감싼다 — 세션이 쉼표를 쓰는 칸이 그것뿐이다. |
| `AnnotateSymbolsStage.refresh_merged` | `(self, ctx: Mode1Context) -> list[X.DroppedUse]` | 샤드를 다시 합치고 보정해 `terms-reading.json` 과 `dropped-uses.csv` 를 쓴다. |
| `AnnotateSymbolsStage.file_of` | `(rec: Record \| None) -> str` | `where` 의 파일 부분. 없으면 빈 글. |
| `AnnotateSymbolsStage.qualified` | `(key: str, rec: Record \| None) -> str` | `<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다. |
| `AnnotateSymbolsStage.plan_files` | `(plan: survey_plan.SurveyPlan) -> set[str]` | 계획에 든 배치들이 가리키는 파일 집합. |
| `AnnotateSymbolsStage.compare_plan` | `(plan: survey_plan.SurveyPlan, d: D.WarmupDiff) -> list[str]` | 계획과 diff 가 같은 범위를 말하는지 양방향으로 본다. 불평 목록을 낸다. |
| `AnnotateSymbolsStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| `AnnotateSymbolsStage.sweep` | `(self, ctx: Mode1Context, out: P.Outcome) -> P.Outcome` | 세션이 전부 끝난 뒤 샤드 전량을 검문한다. 틀린 샤드는 격리하고 단계를 실패로 세운다. |
| `AnnotateSymbolsStage.rounds` | `(self, ctx: Mode1Context) -> int` |  |
| `AnnotateSymbolsStage.jobs` | `(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]` |  |
| `AnnotateSymbolsStage.harvest` | `(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome` |  |

---

## `survey_files.py`

`annotate-symbols` 의 파일 전략. 파일 하나가 세션 하나, 가중치 순, 장벽 없는 풀.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`AnnotateFilesStage`** | *class* | 완료 콜백이 있는 풀. 끝난 세션마다 검문·병합·미해결 표·2패스 투입을 한다. |
| `AnnotateFilesStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `AnnotateFilesStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `terms.py`

`verify-terms`. 읽기 레코드를 인용 검사하고 용어 DB 로 투영한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`VerifyTermsStage`** | *class* |  |
| `VerifyTermsStage.terms_argv` | `(python: str, root: str, repo: str, codegraph: str \| None, reading: str \| None) -> list[str]` | `terms_db.py` 명령줄. |
| `VerifyTermsStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `VerifyTermsStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `VerifyTermsStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `VerifyTermsStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `wiki.py`

`outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`OutlineWikiStage`** | *class* | 목차 한 세션. 이미 있으면 세션 없이 OK — 산출물이 있으면 계약은 지켜진 것이다. |
| `OutlineWikiStage.repo` | `(self, ctx: Mode1Context) -> str` |  |
| `OutlineWikiStage.prompt` | `(self, ctx: Mode1Context) -> str` |  |
| `OutlineWikiStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `OutlineWikiStage.wiki_catalogue_prompt` | `(repo: str, root: str) -> str` | 페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다. |
| `OutlineWikiStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| **`WriteWikiStage`** | *class* | 장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛰고, 따라잡은 기준 뒤 바뀐 파일을 인용하는 장만 다시 쓴다. 사람이 고친 장은 .bak 에 남기고 덮는다. |
| `WriteWikiStage.repo` | `(self, ctx: Mode1Context) -> str` |  |
| `WriteWikiStage.prompt` | `(self, ctx: Mode1Context) -> str` |  |
| `WriteWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `WriteWikiStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `WriteWikiStage.symbol_layers` | `(plan: survey_plan.SurveyPlan) -> dict[str, int]` | `batches.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다. |
| `WriteWikiStage.page_layers` | `(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]` | K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층. |
| `WriteWikiStage.wiki_page_prompt` | `(repo: str, root: str, page: WikiPage, lower_pages: Sequence[X.LowerPageRow]) -> str` | 장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다. |
| `WriteWikiStage.page_hash` | `(path: str) -> str` | 파일 바이트 그대로의 sha256. |
| `WriteWikiStage.stale_pages` | `(wiki_dir: str, pages: Iterable[str], changed: set[str]) -> set[str]` | 이미 쓴 장 중 바뀐 파일의 경로를 글자 그대로 담은 것. 그 장은 다시 쓴다. |
| `WriteWikiStage.edited_pages` | `(wiki_dir: str, pages: Iterable[str], recorded: Mapping[str, str]) -> set[str]` | 있는 장 중 지난 write-wiki 가 적어 둔 해시가 없거나 지금 해시와 다른 것 — 사람이 고쳤거나 누가 썼는지 모른다. |
| `WriteWikiStage.back_up_edited` | `(wiki_dir: str, edited: Iterable[str]) -> list[str]` | 손댄 장을 `docs/wiki/.bak/` 으로 옮기고 옮긴 자리를 낸다. 같은 이름이 있으면 덮지 않고 `<stem>.1.md` · `<stem>.2.md` … 로. |
| `WriteWikiStage.remove_pages` | `(wiki_dir: str, names: Iterable[str]) -> list[str]` | write-wiki 가 쓴 그대로인 낡은 장을 지우고 지운 이름을 낸다. 지운 뒤에는 없는 장이라 `jobs` 가 다시 쓴다. |
| `WriteWikiStage.wiki_files` | `(wiki_dir: str) -> list[str]` | `docs/wiki` 의 최상위 `*.md` 이름 — 봉인(`manifest.entries`)이 싣는 집합과 같다. |
| `WriteWikiStage.read_state` | `(path: str) -> WikiState \| None` | 지난 write-wiki 의 상태. 없거나 꼴이 틀리면 None — 그러면 기준도 손댐도 판정하지 않는다. |
| `WriteWikiStage.write_state` | `(path: str, state: WikiState) -> None` | `wiki-state.json` 을 쓴다. 같은 폴더의 임시 파일에 쓰고 `os.replace` 로 바꿔 끼운다 — 도중에 끊겨도 반쪽 파일이 남지 않는다. |
| `WriteWikiStage.source_hashes` | `(snapshot: str) -> dict[str, str] \| None` | 지문 파일의 `{경로: file_hash}`. 지문이 없으면 None. 못 읽은 파일(`file_hash` 가 None)은 뺀다. |
| `WriteWikiStage.changed_sources` | `(prev: Mapping[str, str], cur: Mapping[str, str]) -> set[str]` | 기준 소스 지도와 지금 지문의 해시가 다른 경로 — 바뀐 것 · 새로 생긴 것 · 지운 것. |
| `WriteWikiStage.record_pages` | `(state_path: str, wiki_dir: str, names: Iterable[str], sources: Mapping[str, str] \| None = None) -> None` | 방금 쓴 장들의 해시를 `pages` 에 적는다. `sources` 를 주면 기준도 바꿔 적는다. `snapshot_sha256` 은 건드리지 않는다. |
| `WriteWikiStage.mark_caught_up` | `(state_path: str, snapshot: str, sources: Mapping[str, str]) -> None` | 위키가 이 지문을 따라잡았다고 적는다 — `sources` 와 `snapshot_sha256`. `pages` 는 그대로 둔다. |
| `WriteWikiStage.prepare` | `(self, ctx: Mode1Context) -> None` |  |
| `WriteWikiStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| `WriteWikiStage.rounds` | `(self, ctx: Mode1Context) -> int` |  |
| `WriteWikiStage.jobs` | `(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]` | 이 층의 없는 장. 낡은 장은 `prepare` 가 비워 두었다. 아래층 장 목록은 층 번호가 더 작은 개요 장 중 디스크에 있거나 이번 실행이 쓴 것이다(층 · 개요 순). |
| `WriteWikiStage.harvest` | `(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome` | 층이 끝날 때마다 세션이 실제로 쓴 장의 해시를 바로 적는다 — 뒤 층이 실패해도 그 장은 LLM 이 쓴 것으로 남는다. |
| **`PublishWikiStage`** | *class* |  |
| `PublishWikiStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `PublishWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| **`VerifyWikiStage`** | *class* |  |
| `VerifyWikiStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `VerifyWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `VerifyWikiStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |

---

## `run_mode1.py`

Mode 1(코드베이스 위키) 파이프라인을 단계 기계 위에서 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_bootstrap_venv` | `() -> None` | `.venv` 밖 해석기로 불렸으면 이 파일 안에서만 `.venv` 로 재실행한다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `build.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `sidebarFrom` | `(files: list[str]) -> list[dict[str, str]]` |  |
| `vitepressConfig` | `(repoName: str, sidebar: list[dict[str, str]], outDir: str) -> str` |  |
| `run` | `(cmd: str, args: list[str], cwd: str \| None = None) -> None` |  |

---

## `check.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `checkArgs` | `(repo: str, codegraph: str, detail: str \| None, docs: list[str]) -> list[str]` |  |

---

## `clang_doc.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `clangDocCandidates` | `(env: Mapping[str, str], prefixes: list[str]) -> list[str]` |  |
| `brewPrefixes` | `(run: Callable[..., Any] = subprocess.run) -> list[str]` |  |
| `clangDocPath` | `(env: Mapping[str, str] \| None = None, exists: Callable[[str], bool] = os.path.exists, prefixes: list[str] \| None = None) -> str \| None` |  |
| `clangDocArgs` | `(outDir: str, repo: str, compdbPath: str, flags: list[str] \| None = None) -> list[str]` |  |

---

## `compdb.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `findCompdbs` | `(repo: str) -> list[str]` |  |
| `mergeEntries` | `(lists: list[list[dict[str, Any]]], repo: str) -> list[dict[str, Any]]` |  |
| `relativeFiles` | `(entries: list[dict[str, Any]], repo: str) -> list[str]` |  |
| `clangUmlConfig` | `(compdbDir: str, repo: str, outDir: str, files: list[str], flags: list[str], paths: list[str]) -> str` |  |
| `readAuthorConfig` | `(path: str) -> dict[str, list[str]]` |  |

---

## `paths.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `wikiPaths` | `(repo: str) -> dict[str, str]` |  |
| `collectorFor` | `(entries: list[str]) -> str` |  |
| `collectorFromSelect` | `(text: str) -> Optional[str]` |  |

---

## `prep.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `tool_versions` | `(collector: Optional[str], py: str, raw: str, clang_doc: Optional[str]) -> dict[str, str]` | 바깥 수집기의 판. `--version` 첫 줄을 쓰고 못 얻으면 `?` 다. roslyn-dump 는 prep 밖에서 돌므로 산출물의 내용 해시를 쓴다. |
| `collect_fingerprint` | `(root: str, versions: dict[str, str]) -> str` | 수집 코드의 내용과 바깥 수집기 판을 합친 sha256. 커밋 해시가 아니라 내용이라 커밋 전 수정도 잡는다. |
| `recorded_fingerprint` | `(path: str, codegraph: str) -> Optional[str]` | 기록된 지문. 기록이 없거나 깨졌거나 지금 지도가 기록할 때의 지도가 아니면 `None` 이다 — 셋 다 다시 수집하라는 뜻이다. |
| `needs_collect` | `(has_codegraph: bool, verdicts: dict[str, list[str]] \| None, force: bool = False, tool_changed: bool = False) -> bool` | 수집기를 다시 돌릴 것인가. |
| `prepPlan` | `(collector: Optional[str], hasCodegraph: bool, hasClangUmlConfig: bool, hasRoslynDump: bool, hasClangDoc: bool, verdicts: dict[str, list[str]] \| None = None, force: bool = False, toolChanged: bool = False) -> dict[str, Any]` |  |
| `pyRoots` | `(repo: str) -> list[str]` |  |
| `run` | `(cmd: str, args: list[str], cwd: Optional[str] = None) -> None` |  |

