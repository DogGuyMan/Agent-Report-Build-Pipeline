# `runner/` — 세 mode 실행기. 단계마다 벽시계 시간과 토큰을 잰다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`check_shard.py`](check_shard.py) | 샤드 파일 하나를 기계 검문한다. 배치 세션이 끝내기 전에 스스로 돌리는 문이다. |
| [`dispatch.py`](dispatch.py) | — |
| [`measure.py`](measure.py) | 세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트. |
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
| [`mode1/survey.py`](mode1/survey.py) | `annotate-symbols`. 층 오름차순 · 층 안 병렬로 전수조사 배치를 돌리고, 층마다 샤드를 합쳐 쓴다. |
| [`mode1/survey_files.py`](mode1/survey_files.py) | `annotate-symbols` 의 파일 전략. 파일 하나가 세션 하나, 가중치 순, 장벽 없는 풀. |
| [`mode1/terms.py`](mode1/terms.py) | `verify-terms`. 읽기 레코드를 인용 검사하고 용어 DB 로 투영한다. |
| [`mode1/wiki.py`](mode1/wiki.py) | `outline-wiki` · `write-wiki` · `publish-wiki` · `verify-wiki`. 산문을 쓰고 사이트로 짓고 대조한다. |
| [`pipeline.py`](pipeline.py) | 세 실행기가 함께 쓰는 단계 기계. 갈래 · 단계 · 전이표 · 그래프 · 드라이버. |
| [`run_grade.py`](run_grade.py) | 채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기. |
| [`run_mode1.py`](run_mode1.py) | Mode 1(코드베이스 위키) 파이프라인을 단계 기계 위에서 돌리고 단계마다 시간과 토큰을 재는 실행기. |
| [`run_mode1_5.py`](run_mode1_5.py) | Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.** |
| [`run_mode2.py`](run_mode2.py) | Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기. |
| [`term/__init__.py`](term/__init__.py) | — |
| [`term/collect.py`](term/collect.py) | — |
| [`term/emit.py`](term/emit.py) | — |
| [`term/quiz.py`](term/quiz.py) | — |
| [`test_import_isolation.py`](test_import_isolation.py) | Mode 2 와 Mode 1.5 를 import 하는 것만으로 해석기가 바뀌거나 networkx 가 실리면 안 된다. |
| [`test_measure.py`](test_measure.py) | — |
| [`test_mode1.py`](test_mode1.py) | `runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON. |
| [`test_pipeline.py`](test_pipeline.py) | 단계 기계의 시험. 갈래 · 전이표 · 그래프 · 시뮬레이터 · 드라이버. |
| [`test_run_grade.py`](test_run_grade.py) | — |
| [`test_run_mode1.py`](test_run_mode1.py) | Mode 1 실행기의 회귀 테스트. |
| [`test_run_mode1_5.py`](test_run_mode1_5.py) | Mode 1.5 실행기의 회귀 시험. |
| [`test_run_mode2.py`](test_run_mode2.py) | Mode 2 실행기의 회귀 시험. |
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

## `dispatch.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `resolve_script` | `(table: dict[str, str], cmd: str) -> str \| None` | 명령 이름을 스크립트 경로로 바꾼다. 표에 없으면 None. |
| `run_dispatch` | `(root: str, table: dict[str, str], argv: list[str], usage: str) -> None` |  |

---

## `measure.py`

세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ClaudeUsage`** | *class* | `claude -p --output-format json` 의 `usage`. 칸은 빠질 수 있고, 있으면 정수여야 한다. |
| **`ClaudeResult`** | *class* | `claude -p --output-format json` 이 stdout 으로 내는 객체 하나. |
| `parse_result` | `(text: str \| bytes) -> ClaudeResult` | `claude` 의 stdout 을 형으로 읽는다. 깨졌으면 `DecodeError`, 꼴이 틀리면 `ValidationError`. |
| **`StageRow`** | *class* | 측정 표의 한 줄. 세 실행기가 모두 이 꼴로 쌓고 `format_report` 가 읽는다. |
| `normalize_usage` | `(result: ClaudeResult \| None) -> Usage` | `claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다. |
| `sum_usage` | `(usages: Sequence[Usage]) -> Usage` | `normalize_usage` 가 낸 사전들을 열쇠별로 접는다. 표 맨 아래 '합계' 줄이 이것이다. |
| `agent_verdict` | `(returncode: int, result: ClaudeResult \| None) -> tuple[bool, str]` | 에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다. |
| `claude_argv` | `(model: str, repo: str, extra_dirs: Iterable[str]) -> list[str]` | 헤드리스 `claude` 명령줄. 프롬프트는 여기 싣지 않는다 — 표준 입력으로 준다. |
| `hms` | `(seconds: float) -> str` | 초를 사람이 읽는 꼴로. 재는 것이 목적이라 소수 첫째 자리까지 남긴다. |
| `format_report` | `(rows: Sequence[StageRow], wall_seconds: float \| None = None) -> str` | 단계별 표 + 합계 줄. 실행기의 산출물 본체다. |
| `stage_totals` | `(rows: Sequence[StageRow]) -> collections.OrderedDict[str, Usage]` | `survey/L0-B00` 같은 행을 `/` 앞까지로 접는다. `{단계: 합친 usage}`. |
| **`Heartbeat`** | *class* | 오래 도는 단계 옆에서 경과 시간을 stderr 로 알린다. |
| `Heartbeat.__init__` | `(self, label: str, every: float = 30.0) -> None` |  |
| `Heartbeat._tick` | `(self) -> None` |  |
| `Heartbeat.__enter__` | `(self) -> 'Heartbeat'` |  |
| `Heartbeat.__exit__` | `(self, *_) -> None` |  |

---

## `context.py`

Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ShardUse`** | *class* |  |
| **`ShardRecord`** | *class* | `where` 는 `module` · `external` 만 없어도 된다 — 그 규칙은 형이 아니라 검문이 본다. |
| **`ShardFault`** | *class* | `at` 은 결함의 자리 — 문법이면 `byte N`, 꼴이면 `$[...].칸`, where 면 레코드 키. |
| **`UnresolvedRow`** | *class* | `unresolved.csv` 의 한 줄 — 얕게 쓴 레코드(`key`) 하나가 기다리는 의존 대상(`dep`) 하나. |
| **`DroppedUse`** | *class* | `dropped-uses.csv` 의 한 줄 — 병합 보정이 레코드에서 떼어 낸 `uses[]` 하나 또는 `shallow` 이름 하나. |
| **`WikiPage`** | *class* | `outline.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다. |
| `_no_records` | `() -> Records` | `field(default_factory=dict)` 는 원소 형을 잃는다. 형이 붙은 빈 사전을 낸다. |
| `_no_pages` | `() -> Pages` |  |
| `_no_ints` | `() -> list[int]` |  |
| `_no_levels` | `() -> dict[str, int]` |  |
| **`Mode1Context`** | *class* | 칸마다 이름과 형이 있다. 자루(dict)는 없다. |
| `raw_dir` | `(c: Mode1Context) -> str` |  |
| **`CodeGraphDoc`** | *class* | `codegraph.json` 의 최상위만. 노드 안은 기계축 선언(`survey_plan.CodeGraph`)이 실물과 |
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
| **`ScheduleBatchesStage`** | *class* | 코드 지도를 배치로. 층 전략은 위상 층으로 나누고 증분이면 diff 의 `targets` 로 좁힌다. |
| `ScheduleBatchesStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `ScheduleBatchesStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `ScheduleBatchesStage.plan_summary` | `(plan: survey_plan.SurveyPlan) -> list[str]` | 층·배치 수를 줄 목록으로. `--dry-run` 과 `schedule-batches` 단계가 같은 글을 쓴다. |
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
| `Mode1Machine.wiki_argv` | `(python: str, root: str, script: str, repo: str) -> list[str]` | `runner/wiki/*.py` 하나를 부른다. |

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
| **`ResumeDoc`** | *class* |  |
| `write_resume` | `(path: str, graph: str, rows: list[M.StageRow], order: list[str]) -> ResumeDoc \| None` | 실패한 행이 없으면 아무것도 쓰지 않고 `None`. 있으면 쓴다. |
| `read_resume` | `(path: str) -> ResumeDoc \| None` | 없으면 `None`. 있는데 꼴이 틀리면 예외다. |
| `start_stage` | `(doc: ResumeDoc \| None, for_graph: str) -> str \| None` | 이 그래프용 재개 문서면 시작할 단계를, 아니면 `None`. |

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
| `AnnotateSymbolsStage.warmup_section` | `(targets: Sequence[str] \| None, total: int, repo: str = '') -> str` | 프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다. |
| `AnnotateSymbolsStage.name_of` | `(plan: survey_plan.SurveyPlan) -> dict[str, str]` | 계획 전체의 `id -> name`. `depends_on` 은 노드 id 이고 레코드 키는 이름이라 이 표로 건넌다. |
| `AnnotateSymbolsStage.dep_excerpt` | `(merged: Mapping[str, Mapping[str, object]], batch: survey_plan.PlanBatch, name_of: Mapping[str, str]) -> str` | 배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다. |
| `AnnotateSymbolsStage.survey_batch_prompt` | `(repo: str, root: str, batch: survey_plan.PlanBatch, dep_records: str, targets: Sequence[str] \| None = None, total: int = 0, pending: str = '', name_of: Mapping[str, str] \| None = None) -> str` | 배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다. |
| `AnnotateSymbolsStage.pending_section` | `(pending: str) -> str` | 미조사 의존 대상이 있을 때만 붙는 절. 열지 말고 얕게 쓰고 `shallow` 를 표시하라고 시킨다. |
| `AnnotateSymbolsStage.pending_excerpt` | `(merged: Mapping[str, Mapping[str, object]], batch: survey_plan.PlanBatch, nodes: Mapping[str, Mapping[str, object]]) -> str` | `depends_on` 중 **아직 레코드가 없는** 것을 `이름 (종류) 파일:줄` 로. 세션이 열지 않고 볼 최소 정보다. |
| `AnnotateSymbolsStage.nonnode_prompt` | `(repo: str, root: str) -> str` | K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다. |
| `AnnotateSymbolsStage.write_schema` | `(path: str) -> None` | `ShardRecords` 의 JSON Schema 를 읽기 전용으로 쓴다. 배치 세션이 읽는 견본이자 검문의 형이다. |
| `AnnotateSymbolsStage.fault` | `(kind: FaultKind, batch: str, path: str, at: str, detail: str) -> ShardFault` |  |
| `AnnotateSymbolsStage.check_shard` | `(raw: bytes, batch: str = '', path: str = '') -> list[ShardFault]` | 샤드 하나의 결함 목록. 문법 → 꼴 → `where` 규칙 순으로 보고, 앞이 틀리면 뒤는 보지 않는다. |
| `AnnotateSymbolsStage.fault_line` | `(f: ShardFault) -> str` | 결함 하나를 사람이 읽을 한 줄로. |
| `AnnotateSymbolsStage.plan_ids` | `(plan: survey_plan.SurveyPlan) -> list[str]` | 계획이 띄우는 세션의 이름 전부 — 배치 id 들과, 비노드 층이 있으면 `NONNODE`. |
| `AnnotateSymbolsStage.check_coverage` | `(raw: bytes, batch: survey_plan.PlanBatch, path: str) -> list[ShardFault]` | 계획의 심볼 이름과 샤드의 키를 양방향으로 대조한다. 문법·꼴이 맞은 뒤에만 부른다. |
| `AnnotateSymbolsStage.check_shards` | `(shard_dir: str, plan: survey_plan.SurveyPlan) -> dict[str, list[ShardFault]]` | 계획의 배치마다 샤드를 찾아 검문한다 — 문법·꼴·where 가 맞으면 coverage 까지. 틀린 것만 `{배치: 결함들}`. |
| `AnnotateSymbolsStage.quarantine` | `(shard_dir: str, bid: str, faults: Sequence[ShardFault] = ()) -> str` | 틀린 샤드를 `.json.bad` 로 옮기고 결함들을 `.json.bad.why` 에 JSON 으로 남긴다. |
| `AnnotateSymbolsStage.load_faults` | `(shard_dir: str, bid: str) -> list[ShardFault]` | 격리 사유. 없거나 꼴이 틀리면 빈 목록 — 낡은 사유로 재조사를 오도하지 않는다. |
| `AnnotateSymbolsStage.clear_quarantine` | `(shard_dir: str, bid: str) -> None` | 검문을 통과한 배치의 옛 격리 흔적을 치운다. 남기면 다음 재조사가 낡은 오류를 받는다. |
| `AnnotateSymbolsStage.retry_section` | `(shard_dir: str, bid: str) -> str` | 지난 시도가 격리됐으면 그 결함들을 프롬프트 뒤에 붙일 절. 없으면 빈 글. |
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
| **`WriteWikiStage`** | *class* | 장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛴다. |
| `WriteWikiStage.repo` | `(self, ctx: Mode1Context) -> str` |  |
| `WriteWikiStage.prompt` | `(self, ctx: Mode1Context) -> str` |  |
| `WriteWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `WriteWikiStage.writes` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| `WriteWikiStage.symbol_layers` | `(plan: survey_plan.SurveyPlan) -> dict[str, int]` | `batches.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다. |
| `WriteWikiStage.page_layers` | `(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]` | K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층. |
| `WriteWikiStage.wiki_page_prompt` | `(repo: str, root: str, page: WikiPage, lower_pages: str) -> str` | 장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다. |
| `WriteWikiStage.prepare` | `(self, ctx: Mode1Context) -> None` |  |
| `WriteWikiStage.perform` | `(self, ctx: Mode1Context) -> P.Outcome` |  |
| `WriteWikiStage.rounds` | `(self, ctx: Mode1Context) -> int` |  |
| `WriteWikiStage.jobs` | `(self, ctx: Mode1Context, rnd: int) -> list[tuple[str, str]]` |  |
| `WriteWikiStage.harvest` | `(self, ctx: Mode1Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome` |  |
| **`PublishWikiStage`** | *class* |  |
| `PublishWikiStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `PublishWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |
| **`VerifyWikiStage`** | *class* |  |
| `VerifyWikiStage.argv` | `(self, ctx: Mode1Context) -> list[str]` |  |
| `VerifyWikiStage.reads` | `(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]` |  |

---

## `pipeline.py`

세 실행기가 함께 쓰는 단계 기계. 갈래 · 단계 · 전이표 · 그래프 · 드라이버.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_no_rows` | `() -> list[StageRow]` | `field(default_factory=list)` 는 원소 형을 잃는다. 형이 붙은 빈 목록을 낸다. |
| **`Outcome`** | *class* | `perform()` 이 낸 것. 갈래는 정확히 하나이고, 세션 N개면 행도 N개다. |
| **`RunContext`** | *class* | 세 모드가 공유하는 칸만. 모드마다 이것을 상속해 자기 칸을 더한다. |
| **`Artifact`** | *class* | 단계가 읽고 쓰는 파일 하나. 자리는 `ctx` 가 정하므로 경로를 박지 않는다. |
| `load` | `(path: str, t: type[T]) -> T` | JSON 파일을 형 `t` 로 읽는다. 없거나 깨졌거나 꼴이 틀리면 예외다 — 여기서 잡지 않는다. |
| `check_file` | `(path: str, schema: type[object] \| None, check: Callable[[object], list[str]] \| None = None) -> list[str]` | 꼴을 먼저, 통과하면 뜻을 본다. 불평 목록을 낸다. 산출물 경계에서만 쓴다. |
| **`Stage`** | *class* | 단계 하나. `emits` 는 **선언**이고 실제로 난 갈래는 `perform` 이 반환한다. |
| `Stage.reads` | `(self, ctx: C) -> list[Artifact[C]]` | 돌기 전에 있어야 하는 것. 없으면 단계를 돌리지 않는다. |
| `Stage.writes` | `(self, ctx: C) -> list[Artifact[C]]` | **돌고 나면 있어야 하는 것.** 꼴이 어긋나면 `FAIL` 이 된다. |
| `Stage.perform` | `(self, ctx: C) -> Outcome` |  |
| `missing_reads` | `(stage: Stage[C], ctx: C) -> list[str]` | 읽을 산출물 중 없거나 꼴이 어긋난 것의 불평 목록. |
| `bad_writes` | `(stage: Stage[C], ctx: C) -> list[str]` | 쓴 산출물 중 안 나왔거나 꼴이 어긋난 것의 불평 목록. |
| **`Edges`** | *class* | `(단계 이름, 갈래) -> 목적지`. 목적지는 단계 이름이거나 `HALT` · `NEXT` 다. |
| `Edges.__init__` | `(self, table: Mapping[tuple[str, int], str]) -> None` |  |
| `Edges.dest` | `(self, stage: str, kind: int) -> str \| None` |  |
| **`StageDagGraph`** | *class* | 실제로 돌 흐름. `order` 는 위상 순서이고 모든 간선이 앞으로만 간다. |
| `StageDagGraph.first` | `(self) -> str \| None` |  |
| `StageDagGraph.next_of` | `(self, cur: str, kind: int) -> str \| None` | 이 갈래로 갈 다음 단계. 흐름이 끝나면 `None`. |
| `StageDagGraph.render` | `(self) -> str` | `--dry-run` 이 찍는 것. 폴백 간선까지 화면에 보인다. |
| **`GraphError`** | *class* | 팩토리가 지은 그래프가 검사를 통과하지 못했다. 단계는 하나도 돌지 않았다. |
| `simulate` | `(graph: StageDagGraph[C], ctx: C) -> list[str]` | 아무것도 실행하지 않고 그래프만 걷는다. 불평 목록을 낸다(없으면 빈 목록). |
| `build_graph` | `(name: str, order: Sequence[str], stages: Mapping[str, Stage[C]], edges: Edges, given: Sequence[Artifact[C]], ctx: C) -> StageDagGraph[C]` | 흐름을 짓고 **그 자리에서 보장한다.** 어긋나면 단계를 하나도 돌리지 않고 죽는다. |
| `existing` | `(artifacts: Sequence[Artifact[C]], ctx: C) -> list[Artifact[C]]` | 이미 디스크에 있는 산출물만 고른다. `build_graph` 의 `given` 에 넣는다. |
| **`Pipeline`** | *class* | 그래프를 따라 도는 루프. 세 실행기가 이 한 벌을 쓴다. |
| `Pipeline.run` | `(self, graph: StageDagGraph[C], ctx: C) -> list[StageRow]` |  |
| **`MachineStage`** | *class* | 자식 프로세스 하나. LLM 을 부르지 않으므로 토큰은 늘 0이고 행도 하나다. |
| `MachineStage.argv` | `(self, ctx: C) -> list[str]` |  |
| `MachineStage.cwd` | `(self, ctx: C) -> str` |  |
| `MachineStage.perform` | `(self, ctx: C) -> Outcome` |  |
| `run_agent_with` | `(model: str, repo: str, root: str, prompt: str, timeout: float \| None = None, label: str \| None = None) -> tuple[float, int, AgentResult \| None]` | `claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`. |
| `run_layer` | `(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]], concurrency: int = 8, timeout: float \| None = None) -> list[JobResult]` | 한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다. |
| **`PromptResource`** | *class* | 프롬프트 글을 리소스 파일에서 읽는 단계의 믹스인. 단계당 파일 하나 `<prompt_dir>/<파일>.md`. |
| `PromptResource.sections` | `(text: str) -> dict[str, str]` | 절 이름 → 글. 표식이 없으면 `{"": 본문}`. 글은 앞뒤 줄바꿈을 떼고 줄바꿈 하나로 끝낸다. |
| `PromptResource.load_prompt` | `(cls, name: str, **values) -> str` | `"<파일>"` 또는 `"<파일>#<절>"` 을 읽어 `{{이름}}` 자리를 채운다. |
| **`LlmStage`** | *class* | LLM Model을 부르는 단계. 훅 여섯 중 `prompt` 와 `repo` 만 필수다. |
| `LlmStage.prompt` | `(self, ctx: C) -> str` |  |
| `LlmStage.repo` | `(self, ctx: C) -> str` | `claude -p` 가 열 저장소이자 자식 프로세스의 작업 폴더. |
| `LlmStage.model` | `(self, ctx: C) -> str` |  |
| `LlmStage.rounds` | `(self, ctx: C) -> int` |  |
| `LlmStage.jobs` | `(self, ctx: C, rnd: int) -> list[tuple[str, str]]` |  |
| `LlmStage.harvest` | `(self, ctx: C, got: Sequence[JobResult], rnd: int) -> Outcome` | 세션마다 행 하나. 하나라도 실패하면 층이 실패다. |
| `LlmStage.perform` | `(self, ctx: C) -> Outcome` |  |

---

## `run_grade.py`

채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `find_sheet` | `(workdir: str, names: Sequence[str] = SHEET_NAMES) -> str \| None` | 채운 기입란의 경로. 없으면 None. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `run_mode1.py`

Mode 1(코드베이스 위키) 파이프라인을 단계 기계 위에서 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_bootstrap_venv` | `() -> None` | `.venv` 밖 해석기로 불렸으면 이 파일 안에서만 `.venv` 로 재실행한다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `run_mode1_5.py`

Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.**

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 큰 언어 LLM Model을 부르는 자리인지 답한다. 토큰이 잡히는 곳은 여기뿐이다. |
| `plan_stages` | `(has_candidates: bool, has_answers: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None, ask: bool = False) -> list[str]` | 무엇을 실제로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `human_gate_open` | `(has_answers: bool) -> bool` | 사람 차례가 아직 안 끝났는가. 답안 파일 하나로 판정한다. |
| `_text` | `(v: object) -> str` | `str(v or "")` 와 같다. 숫자가 와도 글자로 본다. |
| **`Question`** | *class* | `questions.json` 의 문항 하나. LLM 이 쓰고 사람이 손댈 수 있어 칸은 전부 선택이다 — |
| **`TermEntry`** | *class* |  |
| **`QuestionsDoc`** | *class* |  |
| **`Candidates`** | *class* | `term-candidates.json`. |
| **`SheetDoc`** | *class* | 사람이 채운 `answers.json`. 칸 안은 무엇이든 올 수 있어 `validate_answers` 가 하나씩 본다. |
| `split_new_concepts` | `(new_concepts: Iterable[str], answer_key: object) -> tuple[list[str], list[str]]` | Plan 이 새로 만든 개념을 **출제할 것**과 **미룰 것**으로 가른다. |
| `validate_questions` | `(doc: object) -> list[str]` | `questions.json` 이 채점 가능한 꼴인지 본다. 불평 목록을 낸다(없으면 빈 목록). |
| `unasked_known` | `(candidates: object, doc: object) -> list[str]` | 후보의 `known` 중 **출제도 안 되고 뺀 이유도 안 적힌** 용어를 낸다. |
| **`SheetQuestion`** | *class* | `answer-sheet.json` 의 한 칸. 사람은 `UserAns` 에만 적는다. |
| **`AnswerSheet`** | *class* | 정답을 뺀 기입란 전체. **`answer` 를 싣지 않는 것이 요점이다.** |
| `answer_sheet` | `(doc: object) -> AnswerSheet` | `questions.json` 에서 사람이 채울 `answer-sheet.json` 을 만든다. |
| `validate_answers` | `(sheet: object, doc: object) -> list[str]` | 채운 기입란이 문항지와 아귀가 맞는지 본다. 불평 목록을 낸다(없으면 빈 목록). |
| `plan_slug` | `(plan: str) -> str` | 계획서 경로에서 작업 폴더 이름으로 쓸 slug 를 뽑는다. |
| `default_workdir` | `(root: str, plan: str) -> str` | `--workdir` 를 안 주면 여기로 떨어진다 — `<root>/out/mode1_5/<slug>/`. |
| `_term_script` | `(root: str, name: str) -> str` | `runner/term/<이름>` 의 절대 경로. 작업 폴더가 어디든 같은 파일을 부른다. |
| `collect_argv` | `(root: str, plan: str, terms_db: str \| None) -> list[str]` | `collect.py` 명령줄. node 는 PATH 에서 찾는다. |
| `grade_argv` | `(root: str, answers: str, questions: str) -> list[str]` | `quiz.py` 명령줄. 산출물은 **부르는 쪽의 작업 폴더**에 떨어진다. |
| `emit_argv` | `(root: str, grades: str) -> list[str]` | `emit.py` 명령줄. `terms.json` 과 `term-study-note.md` 를 작업 폴더에 쓴다. |
| `ask_argv` | `(root: str, plan: str, workdir: str, python: str) -> list[str]` | 대화형 `claude` 명령줄. 첫 프롬프트가 `/term-benchmark …` 라 세션이 뜨자마자 스킬이 돈다. |
| `run_interactive` | `(argv: Sequence[str], cwd: str) -> int` | 터미널을 그대로 넘겨 자식을 띄우고 끝날 때까지 기다린다. 출력을 가로채지 않는다. |
| `gate_notice` | `(questions: str, sheet: str, answers: str, held: Sequence[str], answer_key: str, unasked: Sequence[str] = ()) -> str` | 사람 차례에서 화면에 낼 안내문. |
| `format_run` | `(rows: Sequence[M.StageRow], skipped: Sequence[tuple[str, str]] \| None, gate: str \| None) -> str` | `run_mode1.format_report` 의 표를 쓰고, 그 표가 말하지 못하는 둘을 덧붙인다. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다. |
| **`Mode15Context`** | *class* | Mode 1.5 의 단계 사이를 건너다니는 값. 산출 파일 자리는 `workdir` 이 정한다. |
| `Mode15Context.p_cand` | `(self) -> str` |  |
| `Mode15Context.p_key` | `(self) -> str` |  |
| `Mode15Context.p_ques` | `(self) -> str` |  |
| `Mode15Context.p_sheet` | `(self) -> str` |  |
| `Mode15Context.p_ans` | `(self) -> str` |  |
| `Mode15Context.p_grades` | `(self) -> str` |  |
| **`Mode15Machine`** | *class* | 세 단계 모두 `runner/term/` 의 스크립트를 자식 프로세스로 부른다. |
| `Mode15Machine.cwd` | `(self, ctx: Mode15Context) -> str` |  |
| **`CollectStage`** | *class* |  |
| `CollectStage.argv` | `(self, ctx: Mode15Context) -> list[str]` |  |
| `CollectStage.writes` | `(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]` |  |
| **`GradeStage`** | *class* |  |
| `GradeStage.argv` | `(self, ctx: Mode15Context) -> list[str]` |  |
| `GradeStage.reads` | `(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]` | 채운 기입란이 문항지와 아귀가 맞는지 채점 **전에** 본다. |
| `GradeStage.writes` | `(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]` |  |
| **`EmitStage`** | *class* |  |
| `EmitStage.argv` | `(self, ctx: Mode15Context) -> list[str]` |  |
| `EmitStage.reads` | `(self, ctx: Mode15Context) -> list[P.Artifact[Mode15Context]]` |  |
| **`GateStage`** | *class* | 사람 차례. 기입란을 깔아 두고 흐름을 멈춘다 — **실패가 아니다.** |
| `GateStage.perform` | `(self, ctx: Mode15Context) -> P.Outcome` |  |
| **`AskStage`** | *class* | `--ask` 의 사람 차례. 대화형 `claude` 세션을 띄워 `term-benchmark` 스킬이 출제하고 묻게 한다. |
| `AskStage.perform` | `(self, ctx: Mode15Context) -> P.Outcome` |  |
| `build_mode1_5_graph` | `(ctx: Mode15Context, has_candidates: bool, has_answers: bool, only: Iterable[str] \| None, skip: Iterable[str] \| None, ask: bool = False) -> P.StageDagGraph[Mode15Context]` | 진입점에서 부른다. 사람 차례가 안 끝났으면 `gate` 를 맨 뒤에 붙인다 — `ask` 면 |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `run_mode2.py`

Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `report_dir` | `(project: str, slug: str, doc_dir: str = 'specs') -> str` | 보고서가 사는 폴더. **원본 문서 옆**이다 — `specs/<slug>/` 또는 `plans/<slug>/`. |
| `stage_cwd` | `(stage: str, project: str, report_dir: str) -> str` | 단계 하나를 어느 폴더에서 돌릴지 답한다. **여기서 틀리면 오류 없이 엉뚱한 곳에 쓴다.** |
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 큰 언어 LLM Model을 부르는 자리인지 답한다. 토큰이 잡히는 자리는 여기뿐이다. |
| `plan_stages` | `(has_manuscript: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None) -> list[str]` | 무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `manuscript_is_written` | `(data_source: str \| None, report_source: str \| None) -> bool` | 원고가 이미 채워졌는가. 뼈대와 채워진 글을 **글자로** 가른다. |
| `find_spec` | `(filenames: Iterable[str], slug: str, doc_dir: str = 'specs') -> dict[str, str] \| None` | 한 자리의 파일 목록에서 이 slug 의 원본 문서를 찾는다. 없으면 `None`. |
| `script_argv` | `(root: str, stage: str, slug: str) -> list[str]` | `viz/<단계>.py` 하나를 부른다. |
| `agent_prompt` | `(project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None, doc_dir: str = 'specs') -> str` | 원고를 쓰는 한 세션이 할 일 전부. |
| `run_agent` | `(model: str, project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None, timeout: float \| None = None, doc_dir: str = 'specs') -> tuple[int, M.AgentResult \| None]` | `claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다. |
| `_read` | `(path: str) -> str \| None` | 파일을 읽어 문자열로. 없으면 `None` — 순수 함수에 존재 여부를 떠넘기지 않는다. |
| **`Mode2Context`** | *class* | Mode 2 의 단계 사이를 건너다니는 값. 칸마다 이름과 형이 있다. |
| **`Mode2Machine`** | *class* | `init` · `build` · `check` — 셋 다 `viz/` 의 스크립트를 자식 프로세스로 부른다. |
| `Mode2Machine.argv` | `(self, ctx: Mode2Context) -> list[str]` |  |
| `Mode2Machine.cwd` | `(self, ctx: Mode2Context) -> str` |  |
| **`InitStage`** | *class* |  |
| `InitStage.writes` | `(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]` |  |
| **`BuildStage`** | *class* |  |
| `BuildStage.reads` | `(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]` |  |
| `BuildStage.writes` | `(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]` |  |
| **`CheckStage`** | *class* |  |
| `CheckStage.reads` | `(self, ctx: Mode2Context) -> list[P.Artifact[Mode2Context]]` |  |
| **`AgentStage`** | *class* | 세션 하나. `--add-dir` 로 프로젝트와 도구 저장소를 둘 다 열어 준다. |
| `AgentStage.prompt` | `(self, ctx: Mode2Context) -> str` |  |
| `AgentStage.repo` | `(self, ctx: Mode2Context) -> str` |  |
| `AgentStage.harvest` | `(self, ctx: Mode2Context, got: Sequence[P.JobResult], rnd: int) -> P.Outcome` | LLM Model이 낸 글을 화면에 흘린 뒤 기본 거두기를 그대로 쓴다. |
| `build_mode2_graph` | `(ctx: Mode2Context, has_manuscript: bool, only: Iterable[str] \| None, skip: Iterable[str] \| None) -> P.StageDagGraph[Mode2Context]` | 진입점에서 부른다. 어긋나면 단계를 하나도 돌리지 않고 죽는다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `collect.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `escape_re` | `(s: str) -> str` |  |
| `pick_terms` | `(db: dict[str, Any], plan_text: str) -> dict[str, Any]` |  |
| `find_new_concepts` | `(db: dict[str, Any], plan_text: str) -> list[str]` |  |

---

## `emit.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `to_terms_db` | `(graded: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]` |  |
| `to_study_note` | `(graded: dict[str, dict[str, Any]]) -> str` |  |

---

## `quiz.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `flatten_questions` | `(doc: dict[str, Any]) -> list[dict[str, Any]]` |  |
| `choice_number` | `(value: Any) -> int \| None` |  |
| `tally_sheet` | `(sheet: dict[str, Any], doc: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]` |  |
| `grade_one` | `(counts: dict[str, Any]) -> dict[str, Any]` |  |
| `grade_all` | `(answers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]` |  |

---

## `test_import_isolation.py`

Mode 2 와 Mode 1.5 를 import 하는 것만으로 해석기가 바뀌거나 networkx 가 실리면 안 된다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_probe` | `(mod: str) -> dict[str, object]` |  |
| `test_mode2_는_networkx_를_끌어오지_않는다` | `()` |  |
| `test_mode1_5_는_networkx_를_끌어오지_않는다` | `()` |  |
| `test_mode2_import_는_해석기를_바꾸지_않는다` | `()` |  |
| `test_mode1_5_import_는_해석기를_바꾸지_않는다` | `()` |  |

---

## `test_measure.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_토큰_합계는_캐시_둘을_포함한다` | `()` |  |
| `test_결과가_없으면_전부_0이다` | `()` |  |
| `test_망가진_값은_읽는_자리에서_거부된다` | `()` | 옛 정책(조용히 0)을 뒤집었다 — 꼴이 틀린 결과는 `parse_result` 가 던지고 세션 행이 실패로 남는다. |
| `test_사용량을_열쇠별로_접는다` | `()` |  |
| `test_종료_코드가_0이어도_is_error_면_실패다` | `()` |  |
| `test_결과_JSON_이_없으면_실패다` | `()` |  |
| `test_정상이면_성공이다` | `()` |  |
| `test_명령줄에_프롬프트를_싣지_않는다` | `()` |  |
| `test_초를_사람이_읽는_꼴로` | `()` |  |
| `_행` | `(name: str, ok: bool = True, skipped: bool = False) -> M.StageRow` |  |
| `test_표는_단계마다_한_줄과_합계를_낸다` | `()` |  |
| `test_벽시계를_주면_합계_시간이_그것이다` | `()` |  |
| `test_건너뛴_단계는_실패가_아니다` | `()` |  |
| `test_배치_행을_단계_이름으로_접는다` | `()` |  |
| `test_하트비트는_문맥_관리자다` | `()` |  |
| `test_결과_JSON_은_형으로_읽힌다` | `()` |  |
| `test_토큰_칸에_참거짓이나_문자열이_오면_거부한다` | `()` |  |
| `test_깨진_JSON_은_DecodeError_다` | `()` |  |
| `test_없는_칸은_0으로_센다` | `()` |  |

---

## `test_mode1.py`

`runner/mode1/` 의 시험. 문맥 · 산출물 · diff · 단계 · 전이표 · 재개 JSON.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_ctx` | `(tmp_path: Path) -> X.Mode1Context` |  |
| `test_문맥의_기본값은_전량이_아니다` | `(tmp_path: Path)` |  |
| `test_산출물은_저장소_아래_자리를_가리킨다` | `(tmp_path: Path)` |  |
| `test_코드지도_검사는_최상위_열쇠만_본다` | `(tmp_path: Path)` |  |
| `test_층계획_검사는_실제_형으로_본다` | `(tmp_path: Path)` |  |
| `test_읽기_레코드_자리는_자기호스팅만_다르다` | `(tmp_path: Path)` |  |
| `test_측정_행은_단계_이름과_토큰_0_을_담는다` | `()` |  |
| `test_기계_단계는_저장소를_cwd_로_한다` | `(tmp_path: Path)` |  |
| `_verdicts` | `() -> dict[str, list[str]]` |  |
| `test_diff_는_넷_갈래와_범위를_담는다` | `(tmp_path: Path)` |  |
| `test_전량이면_targets_가_None_이다` | `(tmp_path: Path)` |  |
| `test_diff_검사는_형으로_보고_갈래_넷은_쓰는_쪽이_채운다` | `(tmp_path: Path)` |  |
| `test_전체_파일_집합은_삭제됨을_뺀_셋의_합이다` | `()` |  |
| `test_prep_은_diff_에_바뀐_것이_있으면_다시_수집한다` | `()` |  |
| `_plan_with` | `(files: list[str]) -> survey_plan.SurveyPlan` | 배치 하나짜리 계획 — 실제 `SurveyPlan` 꼴이라 msgspec 검증을 통과한다. |
| `test_기계_단계_다섯은_저장소를_cwd_로_한다` | `(tmp_path: Path)` |  |
| `test_prep_은_전량이면_force_증분이면_diff_를_넘긴다` | `(tmp_path: Path)` |  |
| `test_terms_argv_는_정적_지도를_위치_인자로_준다` | `()` |  |
| `test_schedule_batches_는_diff_의_targets_로_좁힌다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_계획_요약은_층과_합계를_낸다` | `()` |  |
| `test_lang_hint_는_싼_모형을_고정한다` | `(tmp_path: Path)` |  |
| `test_lang_hint_는_낱말_하나만_받아들인다` | `(tmp_path: Path)` |  |
| `test_lang_hint_는_실패해도_SKIP_이지_FAIL_이_아니다` | `(tmp_path: Path)` |  |
| `test_lang_hint_는_문서가_없으면_세션을_띄우지_않는다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_lang_hint_프롬프트는_넷_중_하나를_낱말로_답하라고_한다` | `()` |  |
| `test_lang_hint_프롬프트는_docs_를_바이트_그대로_끝에_싣는다` | `(docs: str)` |  |
| `test_lang_decide_는_제안이_있으면_넘긴다` | `(tmp_path: Path)` |  |
| `_no_change` | `() -> dict[str, list[str]]` |  |
| `test_lang_for_는_lang_select_을_먼저_보고_코드_지도로_폴백한다` | `(tmp_path: Path)` |  |
| `test_씨앗은_재읽기와_위치만의_합집합이다` | `()` |  |
| `test_detect_changes_는_diff_파일을_쓴다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_detect_changes_는_언어를_모르면_전량_diff_를_쓴다` | `(tmp_path: Path)` |  |
| `test_snapshot_sources_는_조사가_실패하면_쓰지_않는다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_snapshot_sources_는_전량이면_직접_훑어_찍는다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_지문은_옛_이름도_읽고_새_이름으로_쓴다` | `(tmp_path: Path)` |  |
| `_empty_plan` | `() -> survey_plan.SurveyPlan` | 층 0개 계획. `annotate-symbols` 가 세션 없이 OK 로 끝나야 하는 시험에 쓴다. |
| `_diff` | `(targets: list[str] \| None) -> D.WarmupDiff` |  |
| `test_계획이_diff_보다_넓으면_잡는다` | `()` |  |
| `test_계획이_diff_보다_좁으면_잡는다` | `()` |  |
| `test_계획과_diff_가_맞으면_통과한다` | `()` |  |
| `test_annotate_symbols_는_어긋난_계획을_돌리지_않는다` | `(tmp_path: Path)` |  |
| `test_annotate_symbols_는_바뀐_것이_없고_레코드가_있으면_SKIP` | `(tmp_path: Path)` |  |
| `test_annotate_symbols_는_레코드가_없으면_바뀐_것이_없어도_돈다` | `(tmp_path: Path)` |  |
| `test_샤드를_합치고_충돌은_전원을_개명한다` | `(tmp_path: Path)` |  |
| `test_같은_파일의_같은_키는_개명_없이_갈아_끼운다` | `(tmp_path: Path)` | 증분 조사. 다시 읽은 카드는 옛 카드의 자리를 그대로 잇는다 — 코드 지도가 그 이름을 안다. |
| `test_다른_파일의_같은_키는_여전히_양쪽_다_개명한다` | `(tmp_path: Path)` |  |
| `test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다` | `()` |  |
| `test_outline_wiki_는_목차_파일을_쓴다고_선언하고_있으면_세션_없이_OK` | `(tmp_path: Path)` |  |
| `test_목차_프롬프트는_새_이름의_파일을_말한다` | `()` |  |
| `test_write_wiki_는_이미_쓴_장을_건너뛴다` | `(tmp_path: Path)` |  |
| `test_페이지_층은_인용한_심볼의_최대` | `()` |  |
| `test_증분은_열둘_전량은_열하나` | `()` |  |
| `test_순서의_불변식_셋` | `()` |  |
| `test_별명은_쪼갠_단계로_펴진다` | `()` |  |
| `test_모르는_단계는_거부한다` | `()` |  |
| `test_전량_그래프는_이름이_다르고_표는_같다` | `(tmp_path: Path)` |  |
| `test_전량에서는_annotate_symbols_가_SKIP_을_내지_않는다` | `(tmp_path: Path)` |  |
| `test_증분_그래프는_diff_를_읽는_단계가_셋이다` | `(tmp_path: Path)` |  |
| `test_팩토리는_어긋난_그래프를_거부한다` | `(tmp_path: Path)` |  |
| `test_재개는_그_앞을_잘라_낸다` | `(tmp_path: Path)` |  |
| `test_재개_문서는_어디서_왜_멈췄는지를_담는다` | `(tmp_path: Path)` |  |
| `test_실패가_없으면_재개_문서를_쓰지_않는다` | `(tmp_path: Path)` |  |
| `test_다른_그래프의_재개_문서는_거부한다` | `(tmp_path: Path)` |  |
| `_good_record` | `() -> dict[str, object]` |  |
| `_one_batch_plan` | `(bid: str = 'L0-B00') -> survey_plan.SurveyPlan` |  |
| `test_샤드_형은_계약의_칸을_전부_요구한다` | `()` |  |
| `test_샤드_형은_값의_어휘도_본다` | `()` |  |
| `test_깨진_JSON_샤드는_결함_하나로_짚는다` | `()` |  |
| `test_결함은_네_갈래이고_갈래마다_고치는_법이_다르다` | `()` |  |
| `test_module_과_external_만_where_없이_통과한다` | `()` |  |
| `test_샤드_검문은_계획의_배치마다_파일을_찾는다` | `(tmp_path: Path)` |  |
| `test_틀린_샤드는_격리되어_병합에서_빠지고_다음_실행에서_다시_뜬다` | `(tmp_path: Path)` |  |
| `test_스키마_파일은_읽기_전용이고_다시_쓸_수_있다` | `(tmp_path: Path)` |  |
| `test_프롬프트_둘은_스키마_파일을_가리킨다` | `()` |  |
| `test_annotate_symbols_는_끝에_샤드_전량을_검문하고_틀리면_FAIL` | `(tmp_path: Path)` |  |
| `test_annotate_symbols_는_샤드가_전부_맞으면_검문_행을_남기고_OK` | `(tmp_path: Path)` |  |
| `_fault` | `(kind: X.FaultKind = 'malformed', at: str = 'byte 7014') -> X.ShardFault` |  |
| `test_격리는_결함을_JSON_으로_옆에_남기고_그대로_읽어_낸다` | `(tmp_path: Path)` |  |
| `test_재조사_프롬프트는_지난_오류를_싣는다` | `(tmp_path: Path)` |  |
| `test_프롬프트_둘은_자가검사_명령을_준다` | `()` |  |
| `test_검문이_통과한_배치의_옛_격리_흔적은_치운다` | `(tmp_path: Path)` |  |
| `test_check_shard_명령은_통과_0_불평_1` | `(tmp_path: Path)` |  |
| `test_전략_file_이면_schedule_batches_가_파일_계획과_우선순위_csv_를_낸다` | `(tmp_path: Path)` |  |
| `test_계획_요약은_파일_계획도_읽는다` | `()` |  |
| `test_전략_기본값은_layer_이고_file_이면_writes_에_csv_가_있다` | `(tmp_path: Path)` |  |
| `test_coverage_검문은_빠진_심볼과_남의_심볼을_짚는다` | `(tmp_path: Path)` |  |
| `test_coverage_는_문법_꼴이_맞을_때만_본다` | `(tmp_path: Path)` |  |
| `test_check_shard_명령은_옆의_batches_json_이_있으면_coverage_도_본다` | `(tmp_path: Path)` |  |
| `test_dep_excerpt_는_depends_on_의_id_를_이름으로_바꿔_찾는다` | `()` |  |
| `test_배치_프롬프트의_의존_줄은_id_가_아니라_이름을_보인다` | `()` |  |
| `test_배치_프롬프트는_이름표_없이도_돈다` | `()` |  |
| `test_name_of_는_계획_전체의_id_이름_표다` | `()` |  |
| `test_샤드_형은_shallow_를_선택_칸으로_받는다` | `()` |  |
| `test_미조사_의존_절은_아직_없는_의존_대상을_이름_종류_자리로_적는다` | `()` |  |
| `test_미조사_의존_절은_같은_배치의_심볼을_넣지_않는다` | `()` | 자기 파일 안의 함수는 지금 읽고 있는 것이다 — "열지 마라" 목록에 들어가면 안 된다. |
| `test_파일_전략_프롬프트는_미조사_절과_shallow_지시를_싣는다` | `()` |  |
| `test_into_of_는_다른_파일에서_들어오는_간선_수를_이름으로_센다` | `()` |  |
| `test_미해결_표는_shallow_레코드마다_의존_대상_한_줄이고_상태를_가른다` | `()` |  |
| `test_미해결_csv_머리줄` | `()` |  |
| `test_2패스_프롬프트는_파일을_열지_말라_하고_얕은_레코드와_의존_뜻을_준다` | `()` |  |
| `test_2패스_결과는_원_샤드의_같은_키만_덮고_shallow_를_뗀다` | `(tmp_path: Path)` |  |
| `test_2패스_결과가_깨졌으면_원_샤드를_건드리지_않는다` | `(tmp_path: Path)` |  |
| `test_병합_보정은_id_를_이름으로_바꾸고_모르는_대상은_떼어_기록한다` | `()` |  |
| `test_병합_보정은_shallow_가_다_떨어지면_칸을_뗀다` | `()` |  |
| `test_dropped_csv_머리줄과_label_의_따옴표` | `()` |  |
| `test_refresh_merged_는_보정본을_reading_과_dropped_csv_로_쓴다` | `(tmp_path: Path)` |  |
| `_fake_agent` | `(shards: dict[str, dict[str, object]], calls: list[str])` | 라벨을 보고 샤드를 써 주는 가짜 세션. 프롬프트의 '쓰는 곳' 줄에서 경로를 뽑는다. |
| `_three_file_graph` | `() -> X.CodeGraphDoc` | b.py 는 의존 없음(먼저) · a.f 가 b.g 에 의존 · c.k 가 a.f 에 의존. |
| `_rec` | `(where: str, **more) -> dict[str, object]` |  |
| `test_파일_스케줄러는_가중치_순으로_돌고_shallow_가_풀리면_2패스를_넣는다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_파일_스케줄러는_틀린_샤드를_격리하고_FAIL_로_끝낸다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_전략_file_이면_annotate_symbols_가_파일_단계이고_그래프_이름이_갈린다` | `(tmp_path: Path)` |  |

---

## `test_pipeline.py`

단계 기계의 시험. 갈래 · 전이표 · 그래프 · 시뮬레이터 · 드라이버.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Terms`** | *class* | 시험용 산출물 꼴. |
| `test_갈래_넷은_서로_다른_비트다` | `()` |  |
| `test_Outcome_은_행_없이도_만들어진다` | `()` |  |
| `test_Outcome_둘이_행_목록을_공유하지_않는다` | `()` |  |
| `test_RunContext_는_네_칸을_갖는다` | `()` |  |
| `test_Artifact_는_ctx_로_자리를_정한다` | `()` |  |
| **`가짜단계`** | *class* | 시험용. 정해진 갈래를 그대로 낸다. |
| `가짜단계.__init__` | `(self, name: str, kind: int = P.OK, emits: int = P.OK \| P.FAIL, reads: list[P.Artifact[P.RunContext]] \| None = None, writes: list[P.Artifact[P.RunContext]] \| None = None) -> None` |  |
| `가짜단계.reads` | `(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]` |  |
| `가짜단계.writes` | `(self, ctx: P.RunContext) -> list[P.Artifact[P.RunContext]]` |  |
| `가짜단계.perform` | `(self, ctx: P.RunContext) -> P.Outcome` |  |
| `cast_가짜` | `(st: 'P.Stage[P.RunContext]') -> 가짜단계` |  |
| `test_읽을_것이_없으면_이름으로_말해_준다` | `(tmp_path: Path)` |  |
| `test_읽을_것이_있으면_불평이_없다` | `(tmp_path: Path)` |  |
| `test_꼴이_어긋난_산출물은_불평이_된다` | `(tmp_path: Path)` |  |
| `test_load_는_형으로_읽고_틀리면_던진다` | `(tmp_path: Path)` |  |
| `test_단계_안의_꼴_예외는_FAIL_행이_된다` | `(tmp_path: Path)` |  |
| `test_쓰지_못한_산출물은_없다고_말한다` | `(tmp_path: Path)` |  |
| `test_드라이버가_쓸_산출물의_폴더를_미리_만든다` | `(tmp_path: Path)` |  |
| `test_전이표는_단계별_규칙을_먼저_본다` | `()` |  |
| `test_전이표에_없는_갈래는_None_이다` | `()` |  |
| `test_전이표는_넘겨받은_사전을_복사한다` | `()` |  |
| `삼단_그래프` | `(kinds: dict[str, int] \| None = None) -> P.StageDagGraph[P.RunContext]` |  |
| `test_첫_단계는_순서의_맨_앞이다` | `()` |  |
| `test_빈_그래프의_첫_단계는_None_이다` | `()` |  |
| `test_NEXT_는_순서상_다음_단계다` | `()` |  |
| `test_HALT_는_흐름을_끝낸다` | `()` |  |
| `test_이름을_적은_간선은_그리로_점프한다` | `()` |  |
| `test_render_는_단계마다_갈래를_보인다` | `()` |  |
| `test_어긋난_것이_없으면_불평이_없다` | `(tmp_path: Path)` |  |
| `test_완결성_emits_비트에_간선이_없으면_잡는다` | `(tmp_path: Path)` |  |
| `test_매달림_없는_단계를_가리키면_잡는다` | `(tmp_path: Path)` |  |
| `test_순환_뒤로_가는_간선을_잡는다` | `(tmp_path: Path)` |  |
| `test_도달성_아무도_가지_않는_단계를_잡는다` | `(tmp_path: Path)` |  |
| `test_산출물_어떤_경로에서만_없는_것을_잡는다` | `(tmp_path: Path)` | `a` 가 FAIL 로 `c` 에 떨어지면 `b` 가 쓸 파일이 없다. 한 줄 흐름이면 안 보인다. |
| `test_산출물_이미_있는_것은_given_으로_통과한다` | `(tmp_path: Path)` |  |
| `test_팩토리는_어긋나면_단계를_하나도_돌리지_않고_죽는다` | `(tmp_path: Path)` |  |
| `test_팩토리는_멀쩡하면_그래프를_낸다` | `(tmp_path: Path)` |  |
| `test_드라이버는_전이표를_따라_끝까지_돈다` | `(tmp_path: Path)` |  |
| `test_드라이버는_FAIL_에서_멈춘다` | `(tmp_path: Path)` |  |
| `test_드라이버는_읽을_것이_없으면_단계를_돌리지_않는다` | `(tmp_path: Path)` |  |
| `test_드라이버는_재정의할_수_있다` | `(tmp_path: Path)` | D6 — 사용자 판정. `run` 은 닫히지 않는다. |
| **`참말단계`** | *class* |  |
| `참말단계.argv` | `(self, ctx: P.RunContext) -> list[str]` |  |
| `참말단계.cwd` | `(self, ctx: P.RunContext) -> str` |  |
| **`거짓말단계`** | *class* |  |
| `거짓말단계.argv` | `(self, ctx: P.RunContext) -> list[str]` |  |
| `test_기계_단계는_성공하면_OK_한_행이다` | `(tmp_path: Path)` |  |
| `test_기계_단계는_종료코드를_사유로_적는다` | `(tmp_path: Path)` |  |
| `test_기계_단계는_작업_폴더가_없으면_돌지_않는다` | `(tmp_path: Path)` |  |
| **`한번부르는단계`** | *class* |  |
| `한번부르는단계.prompt` | `(self, ctx: P.RunContext) -> str` |  |
| `한번부르는단계.repo` | `(self, ctx: P.RunContext) -> str` |  |
| **`두층부르는단계`** | *class* |  |
| `두층부르는단계.rounds` | `(self, ctx: P.RunContext) -> int` |  |
| `두층부르는단계.jobs` | `(self, ctx: P.RunContext, rnd: int) -> list[tuple[str, str]]` |  |
| `가짜층` | `(결과: P.AgentResult \| None, rc: int = 0)` |  |
| `test_LLM_단계는_기본으로_자기_이름의_세션_하나다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_LLM_단계는_기본_LLM_Model이_ctx_의_것이다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_LLM_단계는_층마다_세션마다_행을_낸다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_LLM_단계는_층이_실패하면_다음_층을_돌지_않는다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_prompt_resource_는_절_없는_파일을_통째로_읽는다` | `(tmp_path: Path)` |  |
| `test_prompt_resource_는_절을_이름으로_꺼낸다` | `(tmp_path: Path)` |  |
| `test_prompt_resource_는_선언_밖의_이름을_거부한다` | `(tmp_path: Path)` |  |
| `test_sections_는_첫_표식_앞의_글과_겹친_절을_거부한다` | `()` |  |
| `test_llm_stage_는_prompt_resource_다` | `()` |  |
| `test_sections_는_꼴이_틀린_표식을_거부한다` | `(text: str)` |  |
| `test_sections_는_본문_속_낱말_section_을_통과시킨다` | `()` |  |
| `test_load_prompt_는_name_과_cls_자리도_채운다` | `(tmp_path: Path)` |  |
| `test_load_prompt_는_절대_경로가_아닌_prompt_dir_을_거부한다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_load_prompt_는_없는_절을_KeyError_로_낸다` | `(tmp_path: Path)` |  |
| `test_load_prompt_는_자리_어긋남을_TemplateError_로_낸다` | `(tmp_path: Path)` |  |

---

## `test_run_grade.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_questions` | `() -> dict[str, Any]` |  |
| `_sheet` | `(answers: list[str]) -> dict[str, Any]` |  |
| `_workdir` | `(tmp_path: Path, sheet_name: str, answers: list[str]) -> Path` |  |
| `test_answers_json_wins_over_answer_sheet` | `(tmp_path: Path)` | 둘 다 있으면 answers.json 이 이긴다 — 스킬이 따로 떠 놓은 것이 사람의 최종 답안이다. |
| `test_falls_back_to_answer_sheet` | `(tmp_path: Path)` | answers.json 이 없으면 실행기가 깔아 준 기입란을 그대로 본다. |
| `test_returns_none_when_no_sheet` | `(tmp_path: Path)` |  |
| `test_grades_the_answer_sheet_in_place` | `(tmp_path: Path)` | answer-sheet.json 만 있어도 채점하고 term-grades.json 을 그 폴더에 낸다. |
| `test_dont_know_twice_is_모름` | `(tmp_path: Path)` |  |
| `test_explicit_answers_path_overrides_lookup` | `(tmp_path: Path)` |  |
| `test_missing_workdir_fails` | `(tmp_path: Path)` |  |
| `test_missing_questions_fails` | `(tmp_path: Path)` |  |
| `test_missing_sheet_fails` | `(tmp_path: Path)` |  |
| `test_broken_questions_are_refused_before_grading` | `(tmp_path: Path)` | 문항지가 채점 불가능한 꼴이면 quiz.py 를 부르지 않고 멈춘다. |
| `test_plan_flag_resolves_the_slug_workdir` | `()` | --plan 은 run_mode1_5 와 같은 자리를 잡는다 — 두 실행기가 어긋나면 안 된다. |
| `test_needs_workdir_or_plan` | `(tmp_path: Path)` |  |

---

## `test_run_mode1.py`

Mode 1 실행기의 회귀 테스트.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_usage_totals_include_cache` | `()` | 캐시 읽기와 캐시 생성까지 더해야 실제로 흘러간 토큰이다. |
| `test_usage_of_a_machine_stage_is_all_zero` | `()` | 기계 단계는 토큰을 쓰지 않는다. None 이 아니라 0 이어야 표가 더해진다. |
| `test_usage_tolerates_missing_fields` | `()` |  |
| `test_usage_sums_across_stages` | `()` |  |
| `test_agent_result_is_a_failure_when_is_error_is_set` | `()` |  |
| `test_agent_result_is_a_failure_when_the_process_died` | `()` |  |
| `test_agent_result_is_a_failure_when_json_is_unreadable` | `()` |  |
| `test_lang_of_bridges_the_two_naming_schemes` | `(tmp_path: Path)` | 코드 지도는 'csharp' 이라 적고 declmap 은 'cs' 로 안다. 이 한 칸이 어긋나면 단계가 죽는다. |
| `test_lang_of_passes_through_a_name_declmap_already_knows` | `(tmp_path: Path)` |  |
| `test_lang_of_is_none_when_it_cannot_tell` | `()` | 모르는 언어와 없는 파일은 둘 다 None 이다 — 부르는 쪽이 단계를 건너뛴다. 실패가 아니다. |
| `test_seed_includes_position_only_files` | `()` | 함수 본문만 바꾼 변경은 '위치만' 으로 온다 — `warmup.decl_hash` 가 (kind, name) |
| `test_seed_excludes_valid_and_deleted` | `()` | 유효는 읽을 것이 없고, 삭제됨은 읽을 파일 자체가 없다. |
| `test_seed_is_sorted_and_deduplicated` | `()` | 같은 파일이 두 갈래에 들어와도 한 번만 센다 — 프롬프트에 두 번 실리면 안 된다. |
| `test_seed_tolerates_missing_buckets` | `()` |  |
| `test_warmup_section_lists_every_target_and_the_ratio` | `()` | 에이전트가 범위를 알려면 목록과 비율이 둘 다 있어야 한다. |
| `test_warmup_section_is_empty_when_there_is_nothing_to_scope` | `()` | 범위가 없으면 빈 글이다 — 부르는 쪽이 이 절을 통째로 뺀다. |
| `_배치` | `() -> PlanBatch` |  |
| `test_배치_프롬프트는_증분일_때_범위_지시문을_붙인다` | `()` | warmup 이 판정한 목록이 있으면 증분 조사다. 배치 세션이 그것을 알아야 |
| `test_배치_프롬프트는_범위가_없으면_전량_조사다` | `()` | warmup 이 못 돌았거나 백지 실행이면 범위 지시문이 붙지 않는다. |
| `test_claude_argv_is_headless_json_and_names_the_model` | `()` |  |
| `test_claude_argv_does_not_pass_the_prompt_on_the_command_line` | `()` | 프롬프트는 표준 입력으로 준다. 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다. |
| `test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다` | `()` | 배치 세션은 자기 심볼만 읽고 자기 샤드에만 쓴다 — terms-reading.json 을 직접 |
| `test_배치_프롬프트는_아래층이_없으면_최하층이라고_말한다` | `()` | 층0 은 의존 대상이 없다. 빈 칸을 그냥 두면 세션이 무엇이 빠졌는지 헷갈린다. |
| `test_비노드_프롬프트는_심볼이_아닌_종류만_말한다` | `()` | K5 — file · module · artifact · key · concept 는 층 축이 없다. |
| `test_의존_발췌는_아래층에_있는_것만_낸다` | `()` | 전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라진다. |
| `test_의존_발췌는_아무것도_없으면_빈_문자열` | `()` |  |
| `test_terms_argv_passes_the_static_codegraph_positionally` | `()` | `--reading` 만 주면 투영이 codegraph.json 을 **덮어쓴다**. 실제로 겪은 사고다. |
| `test_report_has_a_row_per_stage_and_a_total` | `()` |  |
| `test_report_marks_a_failed_stage` | `()` |  |
| `test_report_marks_a_skipped_stage` | `()` | 건너뜀을 '성공' 으로 그리면 시간이 확 준 이유를 읽는 사람이 알 수 없다. |
| `test_a_skipped_stage_does_not_break_the_total` | `()` |  |
| `test_run_layer_는_동시_한도를_넘지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | K4 — 한 층에서 동시에 8배치까지. 넘으면 rate limit 에 걸려 층 전체가 무너진다. |
| `test_run_layer_는_라벨_순서로_돌려준다` | `(monkeypatch: pytest.MonkeyPatch)` | 배치가 끝나는 순서는 흔들린다. 보고 표가 실행마다 달라지면 대조를 못 한다. |
| `test_run_layer_는_한_배치가_죽어도_나머지를_돌린다` | `(monkeypatch: pytest.MonkeyPatch)` | 배치 하나가 터졌다고 층 전체를 버리면 20분이 날아간다. 실패는 행으로 남기고 계속 간다. |
| `test_빈_층은_LLM_Model을_부르지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | 샤드가 이미 다 있으면 할 일이 없다. 그런데도 부르면 돈만 나간다(J4). |
| `_shard` | `(tmp_path: Path, name: str, payload: R.Records) -> str` |  |
| `test_샤드를_하나로_합친다` | `(tmp_path: Path)` |  |
| `test_키가_겹치면_양쪽_다_개명한다` | `(tmp_path: Path)` | 한쪽만 한정하면 나중에 또 겹친다. `main` 이 9파일이면 9개 전부 개명이다. |
| `test_아래층_레코드를_보존한다` | `(tmp_path: Path)` | 층 k 의 병합이 층 <k 의 결과를 지우면 조사가 층마다 초기화된다. |
| `test_이미_있는_키와_겹쳐도_양쪽_다_개명한다` | `(tmp_path: Path)` | 아래층이 이미 쓴 이름과 겹치는 경우다. 새 것만 한정하면 옛 것이 계속 모호하다. |
| `test_망가진_샤드는_건너뛰고_나머지를_살린다` | `(tmp_path: Path)` | 배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 20분을 버리지 않는다. |
| `test_샤드_폴더가_없으면_있던_것을_그대로` | `(tmp_path: Path)` |  |
| `test_심볼_층_표를_계획에서_뽑는다` | `()` | 페이지 층을 매기려면 심볼마다 층이 몇인지 알아야 한다. |
| `test_페이지_층은_인용한_심볼의_최대` | `()` | 가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다. |
| `test_인용_심볼이_없는_페이지는_층0` | `()` | index.md 처럼 개괄만 있는 장이다. 맨 먼저 써도 아무것도 앞지르지 않는다. |
| `test_모르는_심볼은_층을_올리지_않는다` | `()` | 카탈로그가 지어낸 이름 하나로 페이지가 맨 뒤로 밀리면 안 된다. |
| `test_카탈로그_프롬프트는_계획_파일을_내라고_말한다` | `()` |  |
| `test_페이지_프롬프트는_아래층_페이지를_링크하라고_말한다` | `()` | 재설명 대신 링크하게 하는 것이 층 순서를 지키는 이유다. |
| `test_페이지_프롬프트는_아래층이_없으면_그렇게_말한다` | `()` |  |
| `test_보고표는_진짜_벽시계를_따로_받는다` | `()` | `wall_seconds` 를 주면 합계 줄이 그 값을 쓰고, 안 주면 행의 초를 더한다 — |
| `test_단계별_소계를_낸다` | `()` | 어느 단계가 비쌌는지 보려면 배치 행을 단계로 접어야 한다. |
| `test_같은_샤드를_두_번_합쳐도_개명하지_않는다` | `(tmp_path: Path)` | 층마다 `merge_shards` 를 부르면 샤드를 매번 다시 읽는다. `is not` 으로 충돌을 |
| `test_계획_요약은_층과_배치와_합계를_낸다` | `()` | 돈을 쓰기 전에 몇 세션이 뜨는지 사람이 봐야 한다. |
| `test_lang_of_maps_every_collector_language_to_declmap` | `(tmp_path: Path) -> None` | 코드 지도가 적는 언어 이름 셋이 전부 declmap 이 아는 이름으로 풀려야 한다. |
| `test_every_runner_script_path_actually_exists` | `() -> None` | 세 실행기가 부르는 node 스크립트가 **디스크에 실재하는지** 본다. |
| `test_얼갈이_스크립트가_자식_프로세스로_import_까지_간다` | `() -> None` | `runner/wiki/*.py` 를 **스크립트로** 띄웠을 때 import 가 서는가. |
| `test_자기호스팅_읽기레코드_경로가_실재한다` | `() -> None` | 이 저장소 자신을 조사할 때 원본은 `machine/terms-reading.json` 이다. |
| `test_남의_저장소는_docs_codegraph_아래를_본다` | `() -> None` |  |
| `test_배치_프롬프트의_범위_지시문이_같은_자리를_말한다` | `() -> None` | 프롬프트가 말하는 자리와 실행기가 읽고 쓰는 자리가 갈리면 세션이 없는 파일을 찾는다. |

---

## `test_run_mode1_5.py`

Mode 1.5 실행기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `one_question` | `(ask: str = 'PageRank 는 무엇을 하는가?', answer: int = 0) -> dict[str, Any]` | 검사를 통과하는 문항 하나. 시험마다 한 군데씩만 망가뜨려 쓴다. |
| `good_doc` | `() -> dict[str, Any]` | 정상 `questions.json` 한 장. 용어 하나 · 문항 셋. |
| `test_a_fresh_run_stops_before_grading` | `()` | 아무것도 없으면 모으고 **거기서 끝난다.** 출제도 답안도 사람 쪽 일이다. |
| `test_grading_only_starts_once_a_human_answered` | `()` | 답안이 생긴 뒤에야 채점과 산출이 붙는다. |
| `test_no_stage_calls_the_model` | `()` | **`--ask` 없이는 이 실행기가 LLM Model을 부르지 않는다.** 출제는 term-benchmark 스킬의 일이다. |
| `test_collect_is_skipped_when_candidates_already_exist` | `()` | 다시 모으면 앞 실행이 쌓은 후보 파일을 덮어쓴다. |
| `test_nothing_runs_while_the_human_turn_is_open` | `()` | 후보는 있고 답안은 없는 자리가 사람 차례다 — 돌릴 기계 단계가 없다. |
| `test_only_and_skip_are_honoured` | `()` |  |
| `test_an_unknown_stage_is_rejected` | `()` |  |
| `test_the_gate_is_open_until_a_human_writes_answers` | `()` | `claude -p` 는 되물을 수 없다. 답안이 없으면 멈추는 것 말고 할 일이 없다. |
| `test_the_gate_notice_tells_the_human_exactly_which_files_to_touch` | `()` | 멈췄을 때 사람이 무엇을 해야 하는지 화면만 보고 알 수 있어야 한다. |
| `test_the_gate_notice_stays_quiet_when_nothing_was_held_back` | `()` |  |
| `test_new_concepts_without_a_meaning_are_held_back` | `()` | 정답 문구가 없으면 출제하지 않는다. 채점할 수 없는 문항이 되기 때문이다. |
| `test_a_blank_meaning_counts_as_undefined` | `()` | 빈 문자열이나 공백은 정답이 아니다 — `emit` 이 그대로 용어집으로 넘긴다. |
| `test_the_machine_never_judges_whether_a_concept_is_a_false_positive` | `()` | `E402`(린트 코드)든 진짜 개념이든 규칙은 같다 — 정답이 있으면 낸다. |
| `test_a_well_formed_question_sheet_has_no_complaints` | `()` |  |
| `test_each_term_must_have_exactly_three_questions` | `()` | 세 문항이 아니면 채점 구간(맞힌 수 2 이상 -> 확실)이 뜻을 잃는다. |
| `test_dont_know_must_be_the_last_choice_and_always_the_same_words` | `()` | 자리와 문구가 흔들리면 그것을 고르는 비용이 문항마다 달라진다. |
| `test_the_answer_may_not_point_at_dont_know` | `()` |  |
| `test_an_answer_outside_the_choices_is_caught` | `()` |  |
| `test_duplicate_choices_are_caught` | `()` | 같은 보기가 둘이면 정답이 둘이 되거나 보기 수가 준다. |
| `test_the_number_of_choices_is_fixed_at_five` | `()` | 실제 뜻 4개 + "모르겠다" = 다섯 고정. 문항마다 개수가 다르면 찍어서 맞을 확률이 |
| `test_four_choices_are_no_longer_enough` | `()` | 보기가 넷이면 걸린다. |
| `test_a_term_without_a_meaning_is_caught` | `()` | `means` 가 비면 `emit` 이 뜻 없는 용어집을 낸다. |
| `test_a_sheet_with_no_terms_is_caught` | `()` |  |
| `filled_sheet` | `(doc: dict[str, Any] \| None = None, picks: Sequence[int \| str] = (1, 2, 3)) -> R.AnswerSheet` | 기입란을 만들고 `UserAns` 를 채운 것. `picks` 는 문항 차례대로 고른 보기 번호. |
| `test_the_answer_sheet_never_carries_the_answer` | `()` | **이 시험이 기입란의 존재 이유다.** 풀기 전에 정답이 보이면 이해도가 아니라 눈을 잰다. |
| `test_the_answer_sheet_numbers_every_question_from_one` | `()` | `QNum` 은 용어를 건너뛰며 이어진다 — 용어마다 1로 되돌아가지 않는다. |
| `test_the_answer_sheet_carries_the_term_on_every_question` | `()` | 채점 단위가 문항이 아니라 **용어**다. `Term` 이 없으면 되짚을 수가 없다. |
| `test_the_answer_sheet_numbers_the_choices_from_one_and_ends_with_dont_know` | `()` | 사람이 적는 번호는 1부터다. 문항지의 `answer` 는 0부터라 자리가 하나 어긋난다. |
| `test_the_answer_sheet_leaves_the_user_column_empty` | `()` | 사람이 채울 자리는 비워서 낸다. 미리 채우면 안 푼 것이 답으로 실린다. |
| `test_the_answer_sheet_matches_the_shape_quiz_py_reads` | `()` | `runner/term/quiz.py` 의 `tallySheet` 가 읽는 열쇠 그대로여야 한다. |
| `test_flatten_keeps_the_order_the_sheet_was_built_in` | `()` | 번호 규칙이 파이썬과 `quiz.py` 두 곳에 산다. 여기서 한 번 못 박아 둔다. |
| `test_a_fully_filled_sheet_has_no_complaints` | `()` |  |
| `test_choosing_dont_know_is_a_valid_answer` | `()` | "모르겠다" 는 답을 안 쓴 것이 아니라 고른 것이다. |
| `test_a_blank_user_answer_is_caught` | `()` | **안 푼 것과 모르는 것은 다르다.** 자동으로 "모르겠다" 로 메우지 않는다. |
| `test_a_user_answer_outside_the_choices_is_caught` | `()` |  |
| `test_a_number_written_as_text_is_accepted` | `()` | 사람이 손으로 채우는 칸이라 `3` 과 `"3"` 이 섞인다. 둘 다 받는다. |
| `test_a_missing_answer_is_caught` | `()` |  |
| `test_an_answer_to_a_question_that_was_never_asked_is_caught` | `()` |  |
| `test_the_same_question_answered_twice_is_caught` | `()` |  |
| `test_a_sheet_whose_terms_drifted_is_caught` | `()` | **번호 규칙이 두 언어에 살아서 필요한 검사다.** |
| `test_a_sheet_whose_question_text_drifted_is_caught` | `()` |  |
| `test_the_old_count_shaped_answers_file_is_rejected` | `()` | 옛 꼴(`{용어: {correct, dontKnow}}`)을 주면 조용히 0점이 아니라 거부한다. |
| `test_collect_argv_names_the_plan_and_the_term_database` | `()` |  |
| `test_collect_argv_works_without_a_term_database` | `()` | DB 가 없으면 코드베이스 용어는 0개다 — 그래도 신규 개념은 잡힌다. |
| `test_grade_and_emit_argv_point_at_the_right_scripts` | `()` |  |
| `test_grade_argv_hands_over_both_files` | `()` | 채운 기입란에는 정답이 없다. 문항지가 같이 가야 채점이 된다. |
| `test_the_report_reuses_the_mode_1_table` | `()` |  |
| `test_a_stage_skipped_on_resume_is_marked_as_skipped_not_failed` | `()` | 재개해서 건너뛴 단계를 '실패' 로 그리면 읽는 사람이 오해한다. |
| `test_the_gate_is_appended_to_the_report_and_is_not_a_failure` | `()` |  |
| `test_an_unshuffled_sheet_is_caught` | `()` | 정답이 전부 같은 자리에 있으면 사람이 **위치로** 맞힌다. 보기의 좋고 나쁨은 |
| `test_a_shuffled_sheet_passes` | `()` |  |
| `test_the_shuffle_check_stays_quiet_on_a_tiny_sheet` | `()` | 문항이 셋뿐이면 우연히 몰릴 수 있다. 표본이 적을 때 단정하지 않는다. |
| `test_known_terms_that_were_neither_asked_nor_excluded_are_reported` | `()` | 출제도 안 되고 `excluded` 에도 안 적힌 용어를 잡는다 — 무엇이 빠졌는지 보여야 |
| `test_nothing_is_reported_when_every_known_term_is_accounted_for` | `()` |  |
| `test_the_gate_notice_lists_the_silently_dropped_terms` | `()` |  |
| `test_plan_slug_strips_the_date_prefix` | `()` |  |
| `test_plan_slug_falls_back_to_the_bare_filename` | `()` | 날짜 접두사가 없으면 확장자만 뗀 파일 이름을 그대로 쓴다 — 빈 문자열을 내지 않는다. |
| `test_two_plans_get_two_different_workdirs` | `()` |  |
| `_m15` | `(tmp_path: Path) -> R.Mode15Context` |  |
| `test_답안이_없으면_그래프_끝에_관문이_붙는다` | `(tmp_path: Path)` |  |
| `test_답안이_있으면_관문이_없다` | `(tmp_path: Path)` |  |
| `test_관문은_GATE_로_흐름을_끝낸다` | `(tmp_path: Path)` |  |
| `test_문항지가_없으면_관문은_아무것도_하지_않는다` | `(tmp_path: Path)` |  |
| `test_문항지가_있으면_관문이_기입란을_깔고_안내를_남긴다` | `(tmp_path: Path)` |  |
| `_claude_found` | `(name: str) -> str \| None` |  |
| `_claude_missing` | `(name: str) -> str \| None` |  |
| `_session_left_nothing` | `(argv: Sequence[str], cwd: str) -> int` |  |
| `test_ask_를_주면_사람_차례_자리에_ask_가_서고_채점이_뒤따른다` | `()` | 답안이 없을 때만 `ask` 가 들어가고, 그 뒤에 `grade` `emit` 이 이어진다. |
| `test_ask_는_LLM_을_부르는_유일한_단계다` | `()` |  |
| `test_ask_명령줄은_대화형_claude_에_스킬_호출을_첫_프롬프트로_준다` | `(tmp_path: Path)` |  |
| `test_ask_첫_프롬프트는_한_줄이고_기입란_명령과_산출물_자리를_그대로_싣는다` | `(tmp_path: Path)` |  |
| `test_ask_그래프는_답안이_남지_않으면_GATE_로_끝나고_남으면_채점으로_간다` | `(tmp_path: Path)` |  |
| `test_ask_는_터미널이_아니면_세션을_띄우지_않고_실패한다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_ask_뒤에_답안이_없으면_기입란을_깔고_GATE_로_멈춘다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_ask_뒤에_답안이_있으면_OK_로_채점에_넘긴다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |
| `test_ask_는_claude_가_없으면_실패한다` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` |  |

---

## `test_run_mode2.py`

Mode 2 실행기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_init_runs_at_the_project_root` | `()` | `init` 은 `specs/` 가 있는 프로젝트 뿌리에서 돈다. `init.py` 가 `join(cwd, "specs")` 를 본다. |
| `test_the_agent_also_runs_at_the_project_root` | `()` | LLM Model은 설계 문서(`specs/*-design.md`)와 보고서 폴더를 **둘 다** 봐야 한다. 뿌리에 세운다. |
| `test_build_and_check_run_inside_the_report_folder` | `()` | `build`·`check` 는 보고서 폴더를 `cwd` 로 본다 — 거기서 data.ts 와 report.tsx 를 읽는다. |
| `test_stage_cwd_rejects_an_unknown_stage` | `()` |  |
| `test_report_dir_is_specs_slash_slug` | `()` |  |
| `test_plan_runs_all_four_stages_on_an_empty_report` | `()` |  |
| `test_only_one_stage_calls_the_model` | `()` | LLM Model을 부르는 자리는 **원고 쓰기 하나**다. 나머지 셋은 기계다. |
| `test_plan_skips_the_agent_when_the_manuscript_is_already_written` | `()` | 사람이 쓴 원고를 LLM Model이 덮어쓰면 안 된다. 이미 채워졌으면 굽기만 한다. |
| `test_plan_keeps_init_even_when_the_manuscript_exists` | `()` | `init` 은 늘 부른다 — 건너뛸지는 `init.py` 자신이 정한다(data.ts 가 있으면 exit 0). |
| `test_plan_only_and_skip_are_honoured` | `()` |  |
| `test_plan_rejects_an_unknown_stage` | `()` |  |
| `test_a_fresh_skeleton_is_not_a_manuscript` | `()` | `decisions: []` 는 `init` 이 방금 만든 뼈대다. LLM Model을 불러야 한다. |
| `test_a_filled_data_and_report_is_a_manuscript` | `()` |  |
| `test_decisions_without_matching_sections_is_not_a_manuscript` | `()` | 결정은 있는데 본문 절이 없으면 반쯤 쓰다 만 것이다. 이어 쓰게 다시 부른다. |
| `test_missing_files_are_not_a_manuscript` | `()` |  |
| `test_find_spec_returns_the_date_from_the_filename` | `()` |  |
| `test_find_spec_returns_nothing_for_an_unknown_slug` | `()` |  |
| `test_find_spec_does_not_match_a_partial_slug` | `()` | 부분 문자열로 걸리면 엉뚱한 문서를 원본으로 삼는다. |
| `test_doc_dirs_matches_the_javascript_side` | `()` | `viz/init.py` 의 `DOC_DIRS` 와 순서·이름이 같아야 한다. 어긋나면 조용히 깨진다. |
| `test_find_spec_reads_plans_without_the_design_suffix` | `()` | plans/ 는 `-design` 접미사가 없다. 계획서만 사는 자리라 가드가 필요 없다. |
| `test_find_spec_keeps_the_suffix_guard_for_specs` | `()` | specs/ 에서는 접미사가 없으면 안 잡힌다 — 같은 폴더에 다른 산출물이 함께 산다. |
| `test_find_spec_defaults_to_specs` | `()` | 자리를 안 주면 specs 다 — 옛 호출을 깨지 않는다. |
| `test_report_dir_sits_next_to_its_source_document` | `()` | 보고서는 원본 옆에 산다. plans 문서의 보고서는 plans/<slug>/ 다. |
| `test_script_argv_points_at_the_renderer_scripts` | `()` |  |
| `test_only_init_takes_the_slug_on_the_command_line` | `()` | `build`·`check` 는 `cwd` 로 대상을 안다. slug 를 주면 인자를 오해한다. |
| `_prompt` | `(project: str = '/프로젝트', slug: str = '붙임', spec_file: str = '2026-08-28-붙임-design.md', root: str = '/도구/뿌리', terms_json: str \| None = None) -> str` | `agent_prompt` 를 기본값으로 부른다. 시험마다 바꾸는 칸만 이름 인자로 준다. |
| `test_the_prompt_forbids_the_model_from_filling_the_verdict` | `()` | 수용/보류/번복은 **언제나 사용자 몫**이다. 이 한 줄이 빠지면 LLM Model이 채운다. |
| `test_the_prompt_states_the_single_script_invariant` | `()` |  |
| `test_the_prompt_forbids_the_d_axis` | `()` | D축은 보류 상태다. 프롬프트가 말하지 않으면 LLM Model이 필드를 넣는다. |
| `test_the_prompt_names_the_canonical_procedure_skill` | `()` |  |
| `test_the_prompt_uses_korean_status_tags_only` | `()` |  |
| `test_the_prompt_names_the_paths_the_model_must_touch` | `()` |  |
| `test_the_prompt_forbids_committing` | `()` |  |
| `test_the_prompt_mentions_the_glossary_source_only_when_it_exists` | `()` | Mode 1.5 의 terms.json 은 **알려 주기만** 한다. 기계로 병합하면 뜻을 다듬는 단계가 사라진다. |
| `test_용어집_절은_금지_목록과_규율_사이에_빈_줄을_두고_들어간다` | `(tj: str)` |  |
| `test_용어집이_없으면_금지_목록_뒤에_빈_줄_하나로_규율이_온다` | `()` |  |
| `test_the_prompt_is_not_passed_on_the_command_line` | `()` | 프롬프트는 표준 입력으로 준다 — 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다. |
| `test_the_measuring_code_is_reused_not_reimplemented` | `()` | 두 실행기가 각자 세면 같은 이름의 숫자가 서로 다른 뜻을 갖는다. |
| `test_a_machine_stage_row_is_all_zero_tokens` | `()` |  |
| `test_the_report_table_has_a_row_per_stage_and_a_total` | `()` |  |
| `_ctx` | `(tmp_path: Path) -> R.Mode2Context` |  |
| `test_그래프는_고른_단계만_담는다` | `(tmp_path: Path)` |  |
| `test_원고가_있으면_그래프에_agent_가_없다` | `(tmp_path: Path)` |  |
| `test_그래프의_실패는_전부_멈춤이다` | `(tmp_path: Path)` |  |
| `test_build_만_고르면_이미_있는_파일이_given_이_된다` | `(tmp_path: Path)` |  |
| `test_build_만_고르는데_파일이_없으면_팩토리가_죽는다` | `(tmp_path: Path)` |  |

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
| `needs_collect` | `(has_codegraph: bool, verdicts: dict[str, list[str]] \| None, force: bool = False) -> bool` | 수집기를 다시 돌릴 것인가. |
| `prepPlan` | `(collector: Optional[str], hasCodegraph: bool, hasClangUmlConfig: bool, hasRoslynDump: bool, hasClangDoc: bool, verdicts: dict[str, list[str]] \| None = None, force: bool = False) -> dict[str, Any]` |  |
| `pyRoots` | `(repo: str) -> list[str]` |  |
| `run` | `(cmd: str, args: list[str], cwd: Optional[str] = None) -> None` |  |

