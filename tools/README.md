# `tools/` — 저장소 관리용 잡도구.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`gen_readme.py`](gen_readme.py) | 소스에서 디렉토리별 README.md 를 생성한다. |
| [`scrub_local_paths.py`](scrub_local_paths.py) | 로컬 사용자 경로와 개인 식별자를 작업 트리와 git 히스토리에서 지운다. |
| [`test_gen_readme.py`](test_gen_readme.py) | README 가 소스와 어긋나지 않는지 본다. |

---

## `gen_readme.py`

소스에서 디렉토리별 README.md 를 생성한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `first_line` | `(node: ast.AST) -> str` |  |
| `cell` | `(text: str) -> str` |  |
| `render_dir` | `(repo: str, d: str) -> str` |  |
| `main` | `() -> int` |  |

---

## `scrub_local_paths.py`

로컬 사용자 경로와 개인 식별자를 작업 트리와 git 히스토리에서 지운다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `git` | `(*args, cwd: str \| Path \| None = None, check: bool = True) -> str` |  |
| `rules_for` | `(include_tilde: bool) -> list[Rule]` |  |
| `tracked_files` | `(repo: str) -> list[str]` |  |
| `replace_all` | `(text: str, rules: list[Rule]) -> tuple[str, dict[str, int]]` | 규칙을 순서대로 적용한다. (바뀐 텍스트, {규칙: 적중수}) |
| `cmd_scan` | `(repo: str, rules: list[Rule], args: argparse.Namespace) -> int` |  |
| `cmd_worktree` | `(repo: str, rules: list[Rule], args: argparse.Namespace) -> int` |  |
| `cmd_history` | `(repo: str, rules: list[Rule], args: argparse.Namespace) -> int` |  |
| `main` | `() -> int` |  |

---

## `test_gen_readme.py`

README 가 소스와 어긋나지 않는지 본다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_readme_is_not_stale` | `() -> None` | 소스를 고치고 생성기를 안 돌리면 여기서 깨진다. |
| `test_every_directory_has_one` | `() -> None` | 네 디렉토리 전부 README 를 갖는다. |
| `test_signature_comes_from_pycalls_not_a_copy` | `(tmp_path: Path) -> None` | 시그니처는 pycalls.signature_of 하나에서만 온다. 두 곳에서 만들면 어긋난다. |
| `test_pipe_in_signature_is_escaped` | `(tmp_path: Path) -> None` | `str \| None` 의 파이프가 마크다운 표 칸을 깨뜨리지 않는다. |

