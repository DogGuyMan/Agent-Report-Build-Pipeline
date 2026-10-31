# `src/spec/python/runner/` — Mode 2 실행기. 설계 검토 보고서를 짓는 흐름을 돌리며 잰다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`run_mode2.py`](run_mode2.py) | Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기. |

---

## `run_mode2.py`

Mode 2(설계 검토 보고서) 파이프라인을 한 번에 돌리고 단계마다 시간과 토큰을 재는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`DocDirConfig`** | *class* | `[[doc_dirs]]` 하나 — 원본 문서가 사는 폴더와 그 파일명 꼴. |
| **`ModelsConfig`** | *class* | `[models]` — `agent` 세션의 Model. |
| **`ReportConfig`** | *class* | `resource/spec/config.toml`. 원본 문서 자리 규칙은 `src/spec/python/viz/init.py` 도 같은 파일에서 읽는다. |
| `report_dir` | `(project: str, slug: str, doc_dir: str = 'specs') -> str` | 보고서가 사는 폴더. **원본 문서 옆**이다 — `specs/<slug>/` 또는 `plans/<slug>/`. |
| `stage_cwd` | `(stage: str, project: str, report_dir: str) -> str` | 단계 하나를 어느 폴더에서 돌릴지 답한다. **여기서 틀리면 오류 없이 엉뚱한 곳에 쓴다.** |
| `is_agent_stage` | `(stage: str) -> bool` | 이 단계가 큰 언어 LLM Model을 부르는 자리인지 답한다. 토큰이 잡히는 자리는 여기뿐이다. |
| `plan_stages` | `(has_manuscript: bool, only: Iterable[str] \| None = None, skip: Iterable[str] \| None = None) -> list[str]` | 무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수다. |
| `manuscript_is_written` | `(data_source: str \| None, report_source: str \| None) -> bool` | 원고가 이미 채워졌는가. 뼈대와 채워진 글을 **글자로** 가른다. |
| `find_spec` | `(filenames: Iterable[str], slug: str, doc_dir: str = 'specs') -> dict[str, str] \| None` | 한 자리의 파일 목록에서 이 slug 의 원본 문서를 찾는다. 없으면 `None`. |
| `script_argv` | `(root: str, stage: str, slug: str) -> list[str]` | `viz/<단계>.py` 하나를 부른다. |
| `agent_prompt` | `(project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None, doc_dir: str = 'specs', evidence: Sequence[str] = (), manifest: str = '', stale: Sequence[str] = (), uncommitted: bool = False) -> str` | 원고를 쓰는 한 세션이 할 일 전부. |
| `run_agent` | `(model: str, project: str, slug: str, spec_file: str, root: str, terms_json: str \| None = None, timeout: float \| None = None, doc_dir: str = 'specs', evidence: Sequence[str] = (), manifest: str = '', stale: Sequence[str] = (), uncommitted: bool = False) -> tuple[int, M.AgentResult \| None]` | `claude -p` 를 한 번 부르고 결과 JSON 을 돌려준다. `(종료코드, 결과 또는 None)`. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다 — 진행 상황이 곧 그 명령의 출력이다. |
| `_read` | `(path: str) -> str \| None` | 파일을 읽어 문자열로. 없으면 `None` — 순수 함수에 존재 여부를 떠넘기지 않는다. |
| **`SealedEvidence`** | *class* | `src/common/evidence.py --list` 가 stdout 에 내는 JSON 중 여기서 읽는 칸. 나머지 칸은 버린다. |
| `no_seal` | `() -> SealedEvidence` | 봉인을 쓰지 않는 값. 근거 절이 프롬프트에 실리지 않는다. |
| `read_seal` | `(project: str) -> SealedEvidence` | 프로젝트가 든 저장소에 봉인된 Mode 1 산출물을 읽는다. 상태 한 줄을 찍고, 못 읽으면 `no_seal()` 이다. |
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

