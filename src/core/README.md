# `src/core/` — 세 실행기가 함께 타는 단계 기계 · 측정 · 명령 갈림길.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`dispatch.py`](dispatch.py) | — |
| [`measure.py`](measure.py) | 세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트. |
| [`pipeline.py`](pipeline.py) | 세 실행기가 함께 쓰는 단계 기계. 갈래 · 단계 · 전이표 · 그래프 · 드라이버. |

---

## `dispatch.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `resolve_script` | `(table: dict[str, str], cmd: str \| None) -> str \| None` | 명령 이름을 스크립트 경로로 바꾼다. 표에 없으면 None. |
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
| **`PromptEnvironment`** | *class* | 프롬프트 글의 Jinja2 환경. 사전 값의 `.이름` 은 열쇠를 먼저 찾는다 — `items` · `values` 열쇠가 dict 메서드에 가리지 않는다. |
| `PromptEnvironment.getattr` | `(self, obj: object, attribute: str) -> object` |  |
| `_printable` | `(value: object) -> object` | `{{ }}` 로 찍히는 값. `None` 과 호출 가능한 것(메서드 · 함수)은 글이 될 수 없어 `TemplateError` 다. |
| **`PromptResource`** | *class* | 프롬프트 글을 리소스 파일에서 읽는 단계의 믹스인. 단계당 파일 하나 `<prompt_dir>/<파일>.md`. |
| `PromptResource.sections` | `(text: str) -> dict[str, str]` | 절 이름 → 글. 표식이 없으면 `{"": 본문}`. 글은 앞뒤 줄바꿈을 떼고 줄바꿈 하나로 끝낸다. |
| `PromptResource.free_names` | `(text: str) -> set[str]` | Jinja2 글 `text` 가 값으로 받아야 하는 이름들 — 타지 않는 `{% if %}` 갈래 안의 것도 센다. |
| `PromptResource.render_text` | `(text: str, **values) -> str` | Jinja2 글 `text` 를 `values` 로 렌더한다(`PROMPT_ENV`). |
| `PromptResource.load_prompt` | `(cls, name: str, **values) -> str` | `"<파일>"` 또는 `"<파일>#<절>"` 을 읽어 그 글을 `render_text` 로 렌더한다. |
| **`LlmStage`** | *class* | LLM Model을 부르는 단계. 훅 여섯 중 `prompt` 와 `repo` 만 필수다. |
| `LlmStage.prompt` | `(self, ctx: C) -> str` |  |
| `LlmStage.repo` | `(self, ctx: C) -> str` | `claude -p` 가 열 저장소이자 자식 프로세스의 작업 폴더. |
| `LlmStage.model` | `(self, ctx: C) -> str` |  |
| `LlmStage.rounds` | `(self, ctx: C) -> int` |  |
| `LlmStage.jobs` | `(self, ctx: C, rnd: int) -> list[tuple[str, str]]` |  |
| `LlmStage.harvest` | `(self, ctx: C, got: Sequence[JobResult], rnd: int) -> Outcome` | 세션마다 행 하나. 하나라도 실패하면 층이 실패다. |
| `LlmStage.perform` | `(self, ctx: C) -> Outcome` |  |

