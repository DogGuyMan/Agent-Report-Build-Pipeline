# `tools/` — 저장소 관리용 잡도구.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`doctor.py`](doctor.py) | — |
| [`gen_readme.py`](gen_readme.py) | 소스에서 디렉토리별 README.md 를 생성한다. |
| [`python.py`](python.py) | — |
| [`template.py`](template.py) | 리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외다. |
| [`test_gen_readme.py`](test_gen_readme.py) | README 가 소스와 어긋나지 않는지 본다. |
| [`test_template.py`](test_template.py) | 리소스 자리 채우기가 자리와 값의 어긋남을 예외로 막는지 본다. |

---

## `doctor.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `version_of` | `(text: str \| None) -> tuple[int, ...] \| None` | 글 속 첫 x.y 또는 x.y.z 를 숫자 묶음으로. 없으면 None. |
| `meets` | `(version: str \| None, minimum: tuple[int, ...] \| None) -> bool` | 버전 글이 하한 이상인가. 하한이 없으면 있기만 하면 된다. |
| `node_minimum` | `(root: str) -> tuple[int, ...] \| None` | package.json 의 engines.node 하한. |
| `requirement_names` | `(root: str) -> list[str]` | requirements.txt 의 배포 이름들. 주석과 판 조건은 뗀다. |
| `bin_on_path` | `(root: str) -> str \| None` | PATH 의 report-spec 이 이 저장소 bin/ 의 것이면 그 경로. 아니면 None. |
| `probe` | `(cmd: str \| None, args: list[str]) -> str \| None` | 명령 하나를 돌려 첫 줄을 돌려준다. 못 돌리면 None. |
| `line` | `(name: str, version: str \| None, required: bool, minimum: tuple[int, ...] \| None = None) -> str` | 결과 줄 하나를 글자로. 하한보다 낮으면 낮음, 필수인데 없으면 없음, 선택이면 선택. |
| `main` | `() -> int` |  |

---

## `gen_readme.py`

소스에서 디렉토리별 README.md 를 생성한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `first_line` | `(node: ast.AST) -> str` |  |
| `cell` | `(text: str) -> str` |  |
| `ignored` | `(repo: str, rels: list[str]) -> set[str]` |  |
| `render_dir` | `(repo: str, d: str) -> str` |  |
| `main` | `() -> int` |  |

---

## `python.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `pythonCandidates` | `(root: str, platform: str, env: Dict[str, str]) -> List[str]` |  |
| `pythonPath` | `(root: str, platform: str, env: Dict[str, str]) -> str` |  |

---

## `template.py`

리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`TemplateError`** | *class* | 템플릿의 자리와 넘긴 값이 맞지 않는다. |
| `render` | `(text: str, values: Mapping[str, str]) -> str` | `{{이름}}` 을 값으로 바꾼다. 값이 없는 자리 · 자리가 없는 값 · 자리가 못 된 `{{…` 는 모두 `TemplateError`. |
| `render_file` | `(path: str, values: Mapping[str, str]) -> str` | 파일 하나를 UTF-8 로 읽어 `render` 한다. |

---

## `test_gen_readme.py`

README 가 소스와 어긋나지 않는지 본다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_readme_is_not_stale` | `() -> None` | 소스를 고치고 생성기를 안 돌리면 여기서 깨진다. |
| `test_every_directory_has_one` | `() -> None` | 네 디렉토리 전부 README 를 갖는다. |
| `test_signature_comes_from_pycalls_not_a_copy` | `(tmp_path: Path) -> None` | 시그니처는 pycalls.signature_of 하나에서만 온다. 두 곳에서 만들면 어긋난다. |
| `test_pipe_in_signature_is_escaped` | `(tmp_path: Path) -> None` | `str \| None` 의 파이프가 마크다운 표 칸을 깨뜨리지 않는다. |
| `test_subdirectory_file_links_relative_to_its_readme` | `(tmp_path: Path) -> None` | 하위 폴더 파일의 링크는 README 자리 기준 상대 경로다. 파일 이름만 적으면 링크가 깨진다. |
| `test_git_ignored_file_is_left_out` | `(tmp_path: Path) -> None` | git 이 무시하는 파일은 싣지 않는다. 기계마다 있고 없는 파일이 README 를 기계마다 다르게 만든다. |

---

## `test_template.py`

리소스 자리 채우기가 자리와 값의 어긋남을 예외로 막는지 본다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_자리를_값으로_바꾼다` | `()` |  |
| `test_값이_없는_자리는_예외다` | `()` |  |
| `test_자리가_없는_값도_예외다` | `()` |  |
| `test_한겹_중괄호와_달러는_건드리지_않는다` | `()` |  |
| `test_값_안의_자리는_다시_펴지_않는다` | `()` |  |
| `test_render_file_은_UTF8_파일을_읽어_채운다` | `(tmp_path: Path)` |  |
| `test_자리가_못_된_꼴은_예외다` | `(text: str, values: dict[str, str], 꼴: str)` |  |
| `test_자리를_지운_자리에서_새_꼴이_생기지_않는다` | `()` |  |
| `test_값_안의_백슬래시는_그대로_들어간다` | `()` |  |
| `test_같은_자리가_여러_번_나오면_모두_바꾼다` | `()` |  |

