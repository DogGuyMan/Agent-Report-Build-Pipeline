# `runner/` — 세 mode 실행기. 단계마다 벽시계 시간과 토큰을 잰다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`run_mode1.py`](run_mode1.py) | Mode 1(코드베이스 위키) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기. |
| [`run_mode1_5.py`](run_mode1_5.py) | Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.** |
| [`run_mode2.py`](run_mode2.py) | Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기. |
| [`test_run_mode1.py`](test_run_mode1.py) | Mode 1 실행기의 회귀 테스트. |
| [`test_run_mode1_5.py`](test_run_mode1_5.py) | Mode 1.5 실행기의 회귀 시험. |
| [`test_run_mode2.py`](test_run_mode2.py) | Mode 2 실행기의 회귀 시험. |

---

## `run_mode1.py`

Mode 1(코드베이스 위키) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_bootstrap_venv` | `() -> None` | `.venv` 밖 해석기로 불렸으면 이 파일 안에서만 `.venv` 로 재실행한다. |
| **`StageRow`** | *class* | 측정 표의 한 줄. **세 실행기가 모두 이 꼴로 쌓고 `format_report` 가 읽는다.** |
| **`WikiPage`** | *class* | `wiki-plan.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다. |
| `lang_of` | `(codegraph_path: str \| None) -> str \| None` | 코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다. |
| `changed_seed` | `(판정: warmup.Verdicts) -> list[str]` | 다시 읽어야 할 파일의 씨앗. **`재읽기` 와 `위치만` 의 합집합이다.** |
| `should_call_agent` | `(targets: Sequence[str] \| None, has_reading: bool) -> bool` | 에이전트를 부를 것인가. |
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 모형을 부르는가. 토큰이 잡히는 자리는 여기뿐이다. |
| `plan_stages` | `(has_codegraph: bool, has_reading: bool, has_prose: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None) -> list[str]` | 무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `normalize_usage` | `(result: AgentResult \| None) -> Usage` | `claude -p --output-format json` 의 결과에서 잴 값만 뽑아 평평하게 만든다. |
| `sum_usage` | `(usages: Sequence[Usage]) -> Usage` | `normalize_usage` 가 낸 사전들을 키별로 접는다. 표 맨 아래 '합계' 줄이 이것이다. |
| `agent_verdict` | `(returncode: int, result: AgentResult \| None) -> tuple[bool, str]` | 에이전트가 정말 해냈는가. `(성공인가, 아니라면 왜)` 를 낸다. |
| `claude_argv` | `(model: str, repo: str, extra_dirs: Iterable[str]) -> list[str]` | 헤드리스 `claude` 명령줄. **프롬프트는 여기 싣지 않는다** — 표준 입력으로 준다. |
| `reading_path` | `(repo: str, root: str) -> str` | 전수조사 원본 `terms-reading.json` 의 자리. |
| `warmup_section` | `(targets: Sequence[str] \| None, total: int, repo: str = '') -> str` | 프롬프트에 실을 범위 지시문. 범위가 없으면 빈 글이다. |
| `dep_excerpt` | `(merged: Records, batch: survey_plan.PlanBatch) -> str` | 배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다. |
| `survey_batch_prompt` | `(repo: str, root: str, batch: survey_plan.PlanBatch, dep_records: str, targets: Sequence[str] \| None = None, total: int = 0) -> str` | 배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다. |
| `nonnode_prompt` | `(repo: str, root: str) -> str` | K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다. |
| `symbol_layers` | `(plan: survey_plan.SurveyPlan) -> dict[str, int]` | `survey-plan.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다. |
| `page_layers` | `(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]` | K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층. |
| `wiki_catalogue_prompt` | `(repo: str, root: str) -> str` | 페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다. |
| `wiki_page_prompt` | `(repo: str, root: str, page: WikiPage, lower_pages: str) -> str` | 장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다. |
| `node_argv` | `(root: str, script: str, repo: str) -> list[str]` | `runner/wiki/*.mjs` 하나를 부른다. node 는 PATH 에서 찾는다. |
| `terms_argv` | `(python: str, root: str, repo: str, codegraph: str \| None, reading: str \| None) -> list[str]` | `terms_db.py` 명령줄. |
| `hms` | `(seconds: float) -> str` | 초를 사람이 읽는 꼴로. 재는 것이 목적이라 소수 첫째 자리까지 남긴다. |
| `format_report` | `(rows: Sequence[StageRow], wall_seconds: float \| None = None) -> str` | 단계별 표 + 합계 줄. 이 실행기의 **산출물 본체**다. |
| `plan_summary` | `(plan: survey_plan.SurveyPlan) -> list[str]` | 층·배치 수를 줄 목록으로. `--dry-run` 과 `survey-plan` 단계가 같은 글을 쓴다. |
| `stage_totals` | `(rows: Sequence[StageRow]) -> collections.OrderedDict[str, Usage]` | `survey/L0-B00` 같은 행을 `/` 앞까지로 접는다. `{단계: 합친 usage}`. |
| **`Heartbeat`** | *class* | 오래 도는 단계 옆에서 경과 시간을 stderr 로 알린다. |
| `Heartbeat.__init__` | `(self, label: str, every: float = 30.0) -> None` |  |
| `Heartbeat._tick` | `(self) -> None` |  |
| `Heartbeat.__enter__` | `(self) -> 'Heartbeat'` |  |
| `Heartbeat.__exit__` | `(self, *_) -> None` |  |
| `run_agent_with` | `(model: str, repo: str, root: str, prompt: str, timeout: float \| None = None, label: str \| None = None) -> tuple[float, int, AgentResult \| None]` | `claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`. |
| `run_layer` | `(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]], concurrency: int = 8, timeout: float \| None = None) -> list[tuple[str, float, int, AgentResult \| None]]` | 한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다(K2). |
| `merge_shards` | `(shard_dir: str, existing: Records \| None) -> Records` | 샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.** |
| `_qualified` | `(key: str, rec: Record \| None) -> str` | `<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다. |
| `run_machine` | `(argv: Sequence[str], label: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다. |
| `run_lang_select` | `(repo: str, root: str, timeout: float \| None) -> tuple[bool, str, Usage]` | 루트 문서를 모형에게 읽히고 언어 하나를 받아 `lang-select.json` 을 쓴다. |
| `run_warmup` | `(repo: str, codegraph: str, hops: int) -> tuple[list[str] \| None, warmup.Manifest \| None, str \| None, int, bool, str]` | 관문 ① — 무엇을 다시 읽어야 하는지 판정한다. **매니페스트를 쓰지는 않는다.** |
| `save_warmup` | `(cache_path: str \| None, entries: warmup.Manifest \| None, rows: Sequence[StageRow]) -> tuple[bool, str]` | 관문 ② — **전수조사가 실제로 해낸 뒤에만** 매니페스트를 갱신한다. |
| `run_survey` | `(model: str, repo: str, root: str, plan: survey_plan.SurveyPlan, concurrency: int, timeout: float \| None, reading_path: str, targets: Sequence[str] \| None = None, total: int = 0) -> list[StageRow]` | 층 사이는 순차, 층 안은 병렬(K2). `[행, …]` 을 낸다. |
| `run_wiki` | `(model: str, repo: str, root: str, plan: survey_plan.SurveyPlan, concurrency: int, timeout: float \| None) -> list[StageRow]` | 카탈로그 한 세션(J3) -> 장들을 층 오름차순 병렬(K6). |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `run_mode1_5.py`

Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.**

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 큰 언어 모형을 부르는 자리인지 답한다. 토큰이 잡히는 곳은 여기뿐이다. |
| `plan_stages` | `(has_candidates: bool, has_questions: bool, has_answers: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None) -> list[str]` | 무엇을 실제로 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `human_gate_open` | `(has_answers: bool) -> bool` | 사람 차례가 아직 안 끝났는가. 답안 파일 하나로 판정한다. |
| `split_new_concepts` | `(new_concepts: Iterable[str], answer_key: dict[str, Any] \| None) -> tuple[list[str], list[str]]` | Plan 이 새로 만든 개념을 **출제할 것**과 **미룰 것**으로 가른다. |
| `validate_questions` | `(doc: dict[str, Any] \| None) -> list[str]` | `questions.json` 이 채점 가능한 꼴인지 본다. 불평 목록을 낸다(없으면 빈 목록). |
| `unasked_known` | `(candidates: dict[str, Any] \| None, doc: dict[str, Any] \| None) -> list[str]` | 후보의 `known` 중 **출제도 안 되고 뺀 이유도 안 적힌** 용어를 낸다. |
| `flatten_questions` | `(doc: dict[str, Any] \| None) -> list[tuple[int, str, dict[str, Any]]]` | 중첩된 문항지를 한 줄로 펴고 `QNum` 을 1부터 매긴다. `(번호, 용어, 문항)` 목록. |
| `answer_sheet` | `(doc: dict[str, Any] \| None) -> dict[str, Any]` | `questions.json` 에서 사람이 채울 `answer-sheet.json` 을 만든다. |
| `choice_number` | `(value: object) -> int \| None` | `UserAns` 를 보기 번호로 읽는다. 못 읽으면 `None`. |
| `validate_answers` | `(sheet: dict[str, Any] \| None, doc: dict[str, Any] \| None) -> list[str]` | 채운 기입란이 문항지와 아귀가 맞는지 본다. 불평 목록을 낸다(없으면 빈 목록). |
| `_term_script` | `(root: str, name: str) -> str` | `runner/term/<이름>` 의 절대 경로. 작업 폴더가 어디든 같은 파일을 부른다. |
| `collect_argv` | `(root: str, plan: str, terms_db: str \| None) -> list[str]` | `collect.mjs` 명령줄. node 는 PATH 에서 찾는다. |
| `grade_argv` | `(root: str, answers: str, questions: str) -> list[str]` | `quiz.mjs` 명령줄. 산출물은 **부르는 쪽의 작업 폴더**에 떨어진다. |
| `emit_argv` | `(root: str, grades: str) -> list[str]` | `emit.mjs` 명령줄. `terms.json` 과 `term-study-note.md` 를 작업 폴더에 쓴다. |
| `author_argv` | `(model: str, workdir: str, root: str, plan: str) -> list[str]` | 출제 세션의 헤드리스 명령줄. **프롬프트는 여기 싣지 않는다** — 표준 입력으로 준다. |
| `author_prompt` | `(workdir: str, root: str, plan: str) -> str` | 한 세션이 할 일 전부. **용어 보충과 출제를 둘 다** 여기서 시킨다. |
| `gate_notice` | `(questions: str, sheet: str, answers: str, held: Sequence[str], answer_key: str, unasked: Sequence[str] = ()) -> str` | 사람 차례에서 화면에 낼 안내문. |
| `format_run` | `(rows: Sequence[M.StageRow], skipped: Sequence[tuple[str, str]] \| None, gate: str \| None) -> str` | `run_mode1.format_report` 의 표를 쓰고, 그 표가 말하지 못하는 둘을 덧붙인다. |
| `_read_json` | `(path: str) -> Any` | 있으면 읽고 없거나 깨졌으면 `None`. 재개 판단은 파일 존재만으로 하지 않는다. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다. |
| `run_author` | `(model: str, workdir: str, root: str, plan: str, timeout: float \| None = None) -> tuple[int, M.AgentResult \| None]` | 출제 세션을 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `run_mode2.py`

Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `report_dir` | `(project: str, slug: str) -> str` | 보고서가 사는 폴더. 프로젝트 뿌리 아래 `specs/<slug>/` 다. |
| `stage_cwd` | `(stage: str, project: str, report_dir: str) -> str` | 단계 하나를 어느 폴더에서 돌릴지 답한다. **여기서 틀리면 오류 없이 엉뚱한 곳에 쓴다.** |
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 큰 언어 모형을 부르는 자리인지 답한다. 토큰이 잡히는 자리는 여기뿐이다. |
| `plan_stages` | `(has_manuscript: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None) -> list[str]` | 무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `manuscript_is_written` | `(data_source: str \| None, report_source: str \| None) -> bool` | 원고가 이미 채워졌는가. 뼈대와 채워진 글을 **글자로** 가른다. |
| `find_spec` | `(filenames: Iterable[str], slug: str) -> dict[str, str] \| None` | 설계 문서 파일 목록에서 이 slug 의 것을 찾는다. 없으면 `None`. |
| `script_argv` | `(root: str, stage: str, slug: str) -> list[str]` | `viz/<단계>.mjs` 하나를 부른다. node 는 PATH 에서 찾는다. |
| `agent_prompt` | `(project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None) -> str` | 원고를 쓰는 한 세션이 할 일 전부. |
| `run_agent` | `(model: str, project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None, timeout: float \| None = None) -> tuple[int, M.AgentResult \| None]` | `claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다. |
| `_read` | `(path: str) -> str \| None` | 파일을 읽어 문자열로. 없으면 `None` — 순수 함수에 존재 여부를 떠넘기지 않는다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` |  |

---

## `test_run_mode1.py`

Mode 1 실행기의 회귀 테스트.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_빈_저장소면_열_단계를_순서대로_돈다` | `()` | `terms` 가 `survey` 와 `wiki` 사이인 것은 산문 세션이 **인용 검사를 통과한** |
| `test_warmup_관문이_survey_를_감싼다` | `()` | 관문이 감싸야 하는 것은 **레코드를 만드는 단계**다. `wiki` 뒤에 확정을 두면 |
| `test_세_단계가_모형을_부른다` | `()` | 모형을 부르는 칸은 `survey` 와 `wiki` 둘뿐이다. 토큰도 그 둘에서만 잡힌다. |
| `test_산출물이_있는_LLM_단계만_각자_빠진다` | `()` | LLM 단계 둘은 각자 자기 산출물로 걸린다 — 한쪽만 있으면 그쪽만 건너뛴다. |
| `test_the_save_gate_comes_before_terms` | `()` | 매니페스트 확정이 terms 뒤로 밀리면, terms 가 실패했을 때 판정이 사라진다. |
| `test_skip_은_열_단계_흐름_기준으로_걸러낸다` | `()` | `skip` 이 열 단계 목록에서 걸러내는 필터로 옳게 도는지만 본다. |
| `test_plan_keeps_prep_even_when_codegraph_exists` | `()` | prep 은 늘 부른다 — 건너뛸지는 prep 자신이 정한다(prepPlan 의 hasCodegraph). |
| `test_plan_only_and_skip_are_honoured` | `()` |  |
| `test_plan_rejects_an_unknown_stage` | `()` |  |
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
| `test_agent_is_skipped_when_nothing_changed_and_records_exist` | `()` | 국소 변경의 이득이 여기서 나온다 — 조사 단계를 통째로 건너뛴다. |
| `test_agent_still_runs_when_there_are_no_records_yet` | `()` | 조사 결과가 아예 없으면 warmup 이 뭐라 하든 부른다 — 백지에서 시작하는 실행이다. |
| `test_agent_runs_when_something_changed` | `()` |  |
| `test_agent_runs_when_warmup_could_not_judge` | `()` | targets 가 None 이면 warmup 이 못 돌았다는 뜻이다. 그때는 옛 동작(전량)으로 돌아간다. |
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
| `test_survey_가_실패하면_매니페스트를_갱신하지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | 행 라벨이 `survey/L0-B00` 꼴이므로 `r["stage"] == "survey"` 로 비교하면 영원히 |
| `test_판정을_못_했으면_아무것도_쓰지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | `entries is None` 은 warmup 이 언어를 몰라 판정을 건너뛴 경우다. |
| `test_run_layer_는_동시_한도를_넘지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | K4 — 한 층에서 동시에 8배치까지. 넘으면 rate limit 에 걸려 층 전체가 무너진다. |
| `test_run_layer_는_라벨_순서로_돌려준다` | `(monkeypatch: pytest.MonkeyPatch)` | 배치가 끝나는 순서는 흔들린다. 보고 표가 실행마다 달라지면 대조를 못 한다. |
| `test_run_layer_는_한_배치가_죽어도_나머지를_돌린다` | `(monkeypatch: pytest.MonkeyPatch)` | 배치 하나가 터졌다고 층 전체를 버리면 20분이 날아간다. 실패는 행으로 남기고 계속 간다. |
| `test_빈_층은_모형을_부르지_않는다` | `(monkeypatch: pytest.MonkeyPatch)` | 샤드가 이미 다 있으면 할 일이 없다. 그런데도 부르면 돈만 나간다(J4). |
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
| `test_층_계획은_LLM_단계가_아니다` | `()` | `survey-plan` 은 `AGENT_STAGES` 에 없다. |
| `test_층_계획은_조사와_산문보다_먼저다` | `()` | 계획이 없으면 배치도 페이지 층도 만들 수 없다. |
| `test_계획_요약은_층과_배치와_합계를_낸다` | `()` | 돈을 쓰기 전에 몇 세션이 뜨는지 사람이 봐야 한다. |
| `test_lang_of_maps_every_collector_language_to_declmap` | `(tmp_path: Path) -> None` | 코드 지도가 적는 언어 이름 셋이 전부 declmap 이 아는 이름으로 풀려야 한다. |
| `test_every_runner_script_path_actually_exists` | `() -> None` | 세 실행기가 부르는 node 스크립트가 **디스크에 실재하는지** 본다. |
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
| `test_a_fresh_run_stops_before_grading` | `()` | 아무것도 없으면 모으고 출제하고 **거기서 끝난다.** 답안은 사람이 쓴다. |
| `test_grading_only_starts_once_a_human_answered` | `()` | 답안이 생긴 뒤에야 채점과 산출이 붙는다. |
| `test_only_one_stage_calls_the_model` | `()` | 모형을 부르는 자리는 `author` **하나**다. 보충과 출제를 한 세션에서 이어 한다. |
| `test_collect_is_skipped_when_candidates_already_exist` | `()` | 다시 모으면 앞 실행이 쌓은 후보 파일을 덮어쓴다. |
| `test_authoring_is_skipped_when_questions_already_exist` | `()` | 문항을 다시 내면 사람이 이미 푼 시험과 어긋난다. 돈도 두 번 든다. |
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
| `filled_sheet` | `(doc: dict[str, Any] \| None = None, picks: Sequence[int \| str] = (1, 2, 3)) -> dict[str, Any]` | 기입란을 만들고 `UserAns` 를 채운 것. `picks` 는 문항 차례대로 고른 보기 번호. |
| `test_the_answer_sheet_never_carries_the_answer` | `()` | **이 시험이 기입란의 존재 이유다.** 풀기 전에 정답이 보이면 이해도가 아니라 눈을 잰다. |
| `test_the_answer_sheet_numbers_every_question_from_one` | `()` | `QNum` 은 용어를 건너뛰며 이어진다 — 용어마다 1로 되돌아가지 않는다. |
| `test_the_answer_sheet_carries_the_term_on_every_question` | `()` | 채점 단위가 문항이 아니라 **용어**다. `Term` 이 없으면 되짚을 수가 없다. |
| `test_the_answer_sheet_numbers_the_choices_from_one_and_ends_with_dont_know` | `()` | 사람이 적는 번호는 1부터다. 문항지의 `answer` 는 0부터라 자리가 하나 어긋난다. |
| `test_the_answer_sheet_leaves_the_user_column_empty` | `()` | 사람이 채울 자리는 비워서 낸다. 미리 채우면 안 푼 것이 답으로 실린다. |
| `test_the_answer_sheet_matches_the_shape_quiz_mjs_reads` | `()` | `runner/term/quiz.mjs` 의 `tallySheet` 가 읽는 열쇠 그대로여야 한다. |
| `test_flatten_keeps_the_order_the_sheet_was_built_in` | `()` | 번호 규칙이 파이썬과 `quiz.mjs` 두 곳에 산다. 여기서 한 번 못 박아 둔다. |
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
| `test_author_argv_is_headless_json_and_opens_every_folder_it_reads` | `()` |  |
| `test_author_argv_does_not_repeat_a_folder` | `()` | 계획서가 작업 폴더 안에 있으면 같은 폴더가 두 번 열린다. |
| `test_the_prompt_carries_the_two_jobs_and_the_whole_question_discipline` | `()` | 보충(3단계)과 출제(5단계)를 한 세션에서 이어 하고, 출제 규율을 다 싣는다. |
| `test_the_prompt_forbids_asking_the_human` | `()` | 헤드리스 세션은 되물을 수 없다. 되물으려 하면 그대로 막힌다. |
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

---

## `test_run_mode2.py`

Mode 2 실행기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_init_runs_at_the_project_root` | `()` | `init` 은 `specs/` 가 있는 프로젝트 뿌리에서 돈다. `init.mjs` 가 `join(cwd, "specs")` 를 본다. |
| `test_the_agent_also_runs_at_the_project_root` | `()` | 모형은 설계 문서(`specs/*-design.md`)와 보고서 폴더를 **둘 다** 봐야 한다. 뿌리에 세운다. |
| `test_build_and_check_run_inside_the_report_folder` | `()` | `build`·`check` 는 보고서 폴더를 `cwd` 로 본다 — 거기서 data.ts 와 report.tsx 를 읽는다. |
| `test_stage_cwd_rejects_an_unknown_stage` | `()` |  |
| `test_report_dir_is_specs_slash_slug` | `()` |  |
| `test_plan_runs_all_four_stages_on_an_empty_report` | `()` |  |
| `test_only_one_stage_calls_the_model` | `()` | 모형을 부르는 자리는 **원고 쓰기 하나**다. 나머지 셋은 기계다. |
| `test_plan_skips_the_agent_when_the_manuscript_is_already_written` | `()` | 사람이 쓴 원고를 모형이 덮어쓰면 안 된다. 이미 채워졌으면 굽기만 한다. |
| `test_plan_keeps_init_even_when_the_manuscript_exists` | `()` | `init` 은 늘 부른다 — 건너뛸지는 `init.mjs` 자신이 정한다(data.ts 가 있으면 exit 0). |
| `test_plan_only_and_skip_are_honoured` | `()` |  |
| `test_plan_rejects_an_unknown_stage` | `()` |  |
| `test_a_fresh_skeleton_is_not_a_manuscript` | `()` | `decisions: []` 는 `init` 이 방금 만든 뼈대다. 모형을 불러야 한다. |
| `test_a_filled_data_and_report_is_a_manuscript` | `()` |  |
| `test_decisions_without_matching_sections_is_not_a_manuscript` | `()` | 결정은 있는데 본문 절이 없으면 반쯤 쓰다 만 것이다. 이어 쓰게 다시 부른다. |
| `test_missing_files_are_not_a_manuscript` | `()` |  |
| `test_find_spec_returns_the_date_from_the_filename` | `()` |  |
| `test_find_spec_returns_nothing_for_an_unknown_slug` | `()` |  |
| `test_find_spec_does_not_match_a_partial_slug` | `()` | 부분 문자열로 걸리면 엉뚱한 문서를 원본으로 삼는다. |
| `test_script_argv_points_at_the_renderer_scripts` | `()` |  |
| `test_only_init_takes_the_slug_on_the_command_line` | `()` | `build`·`check` 는 `cwd` 로 대상을 안다. slug 를 주면 인자를 오해한다. |
| `_prompt` | `(project: str = '/프로젝트', slug: str = '붙임', spec_file: str = '2026-08-28-붙임-design.md', root: str = '/도구/뿌리', terms_json: str \| None = None) -> str` | `agent_prompt` 를 기본값으로 부른다. 시험마다 바꾸는 칸만 이름 인자로 준다. |
| `test_the_prompt_forbids_the_model_from_filling_the_verdict` | `()` | 수용/보류/번복은 **언제나 사용자 몫**이다. 이 한 줄이 빠지면 모형이 채운다. |
| `test_the_prompt_states_the_single_script_invariant` | `()` |  |
| `test_the_prompt_forbids_the_d_axis` | `()` | D축은 보류 상태다. 프롬프트가 말하지 않으면 모형이 필드를 넣는다. |
| `test_the_prompt_names_the_canonical_procedure_skill` | `()` |  |
| `test_the_prompt_uses_korean_status_tags_only` | `()` |  |
| `test_the_prompt_names_the_paths_the_model_must_touch` | `()` |  |
| `test_the_prompt_forbids_committing` | `()` |  |
| `test_the_prompt_mentions_the_glossary_source_only_when_it_exists` | `()` | Mode 1.5 의 terms.json 은 **알려 주기만** 한다. 기계로 병합하면 뜻을 다듬는 단계가 사라진다. |
| `test_the_prompt_is_not_passed_on_the_command_line` | `()` | 프롬프트는 표준 입력으로 준다 — 명령줄에 실으면 길이 한계와 따옴표 지옥에 걸린다. |
| `test_the_measuring_code_is_reused_not_reimplemented` | `()` | 두 실행기가 각자 세면 같은 이름의 숫자가 서로 다른 뜻을 갖는다. |
| `test_a_machine_stage_row_is_all_zero_tokens` | `()` |  |
| `test_the_report_table_has_a_row_per_stage_and_a_total` | `()` |  |

