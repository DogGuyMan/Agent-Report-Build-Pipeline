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
| [`test_gen_readme.py`](test_gen_readme.py) | README 가 소스와 어긋나지 않는지 본다. |

---

## `doctor.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `probe` | `(cmd: str \| None, args: list[str]) -> str \| None` | 명령 하나를 돌려 첫 줄을 돌려준다. 못 돌리면 None. |
| `line` | `(name: str, version: str \| None, required: bool) -> str` | 결과 줄 하나를 글자로. 필수인데 없으면 없음, 선택이면 선택. |
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

