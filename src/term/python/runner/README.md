# `src/term/python/runner/` — Mode 1.5 실행기. 용어를 모으고 채점하고 내보낸다. 사람에게 묻지 않는다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`run_grade.py`](run_grade.py) | 채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기. |
| [`run_mode1_5.py`](run_mode1_5.py) | Mode 1.5(용어 이해도 점검) 파이프라인 실행기. **사람 앞에서 멈춘다.** |
| [`term/__init__.py`](term/__init__.py) | — |
| [`term/collect.py`](term/collect.py) | — |
| [`term/emit.py`](term/emit.py) | — |
| [`term/quiz.py`](term/quiz.py) | — |

---

## `run_grade.py`

채운 기입란 하나를 문항지와 대조해 채점만 하는 실행기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `find_sheet` | `(workdir: str, names: Sequence[str] = SHEET_NAMES) -> str \| None` | 채운 기입란의 경로. 없으면 None. |
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
| `_term_script` | `(root: str, name: str) -> str` | `src/term/python/runner/term/<이름>` 의 절대 경로. 작업 폴더가 어디든 같은 파일을 부른다. |
| `collect_argv` | `(root: str, plan: str, terms_db: str) -> list[str]` | `collect.py` 명령줄. node 는 PATH 에서 찾는다. |
| `grade_argv` | `(root: str, answers: str, questions: str) -> list[str]` | `quiz.py` 명령줄. 산출물은 **부르는 쪽의 작업 폴더**에 떨어진다. |
| `emit_argv` | `(root: str, grades: str) -> list[str]` | `emit.py` 명령줄. `terms.json` 과 `term-study-note.md` 를 작업 폴더에 쓴다. |
| `ask_argv` | `(root: str, plan: str, workdir: str, python: str, terms_db: str) -> list[str]` | 대화형 `claude` 명령줄. 첫 프롬프트가 `/term-benchmark …` 라 세션이 뜨자마자 스킬이 돈다. |
| `run_interactive` | `(argv: Sequence[str], cwd: str) -> int` | 터미널을 그대로 넘겨 자식을 띄우고 끝날 때까지 기다린다. 출력을 가로채지 않는다. |
| `gate_notice` | `(questions: str, sheet: str, answers: str, held: Sequence[str], answer_key: str, unasked: Sequence[str] = ()) -> str` | 사람 차례에서 화면에 낼 안내문. |
| `format_run` | `(rows: Sequence[M.StageRow], skipped: Sequence[tuple[str, str]] \| None, gate: str \| None) -> str` | `measure.format_report` 의 표를 쓰고, 그 표가 말하지 못하는 둘을 덧붙인다. |
| `run_machine` | `(argv: Sequence[str], label: str, cwd: str) -> int` | 기계 단계 하나. 출력은 그대로 흘려보낸다. |
| **`Mode15Context`** | *class* | Mode 1.5 의 단계 사이를 건너다니는 값. 산출 파일 자리는 `workdir` 이 정한다. |
| `Mode15Context.p_cand` | `(self) -> str` |  |
| `Mode15Context.p_key` | `(self) -> str` |  |
| `Mode15Context.p_ques` | `(self) -> str` |  |
| `Mode15Context.p_sheet` | `(self) -> str` |  |
| `Mode15Context.p_ans` | `(self) -> str` |  |
| `Mode15Context.p_grades` | `(self) -> str` |  |
| **`Mode15Machine`** | *class* | 세 단계 모두 `src/term/python/runner/term/` 의 스크립트를 자식 프로세스로 부른다. |
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

## `collect.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`EvidenceList`** | *class* | `src/common/evidence.py --list` 가 stdout 에 내는 JSON. `stale_files` 는 봉인 뒤 움직인 소스 경로다. |
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

