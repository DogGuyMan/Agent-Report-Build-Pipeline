# `tools/` — 저장소 관리용 잡도구.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`doctor.py`](doctor.py) | — |
| [`doctor_packages.py`](doctor_packages.py) | `doctor.py` 가 고른 파이썬으로 띄우는 패키지 확인 — 인자로 받은 배포 이름 중 깔리지 않은 것을 한 줄로 낸다. |
| [`gen_contract.py`](gen_contract.py) | 계약 리소스 `contracts/mode1-artifacts.v1.json` 과 지문 `.sha256` 을 Mode 1 의 형에서 낸다. |
| [`gen_contract_types.py`](gen_contract_types.py) | 계약 리소스(JSON Schema)에서 소비자 형을 낸다 — 생성물 `src/common/contract_types.py`. `--check` 면 낡았을 때 exit 1. |
| [`gen_readme.py`](gen_readme.py) | 소스에서 디렉토리별 README.md 를 생성한다. |

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

## `doctor_packages.py`

`doctor.py` 가 고른 파이썬으로 띄우는 패키지 확인 — 인자로 받은 배포 이름 중 깔리지 않은 것을 한 줄로 낸다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `missing` | `(names: list[str]) -> list[str]` | 깔리지 않은 배포 이름들. 순서는 받은 그대로. |
| `main` | `() -> int` | `전부 있다` 또는 `빠짐: <이름>, …` 한 줄을 낸다. 빠진 것이 있어도 exit 0 — 판정은 `doctor.py` 가 그 줄로 한다. |

---

## `gen_contract.py`

계약 리소스 `contracts/mode1-artifacts.v1.json` 과 지문 `.sha256` 을 Mode 1 의 형에서 낸다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `strip_names` | `(node: object) -> object` | 스키마 객체에서 `title` · `description` 을 뗀다. `properties` · `$defs` 안의 칸 이름은 남긴다. |
| `contract_text` | `() -> str` | 계약 JSON 본문. 열쇠를 정렬해 같은 형이면 같은 바이트다. |
| `sha_text` | `(text: str) -> str` | `sha256sum -c` 가 읽는 한 줄 — 계약 본문의 지문과 파일 이름. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` | 계약 리소스와 지문을 쓴다. `--check` 면 쓰지 않고 파일이 형과 같은지만 본다. |

---

## `gen_contract_types.py`

계약 리소스(JSON Schema)에서 소비자 형을 낸다 — 생성물 `src/common/contract_types.py`. `--check` 면 낡았을 때 exit 1.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `py_type` | `(s: Schema) -> str` | 스키마 하나를 파이썬 형 표기로. 모르는 꼴이면 ValueError. |
| `refs` | `(node: object) -> set[str]` | 스키마 안의 `$ref` 가 가리키는 이름 전부. |
| `class_text` | `(name: str, s: Schema) -> str` | 객체 스키마 하나를 TypedDict 클래스 글로. 칸은 이름순이고 `required` 에 없는 칸은 `NotRequired` 다. |
| `module_text` | `(doc: Mapping[str, object]) -> str` | 계약 문서 전체를 `contract_types.py` 의 글로. 클래스는 참조되는 것이 먼저 오게 늘어놓는다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` | 계약에서 `src/common/contract_types.py` 를 쓴다. `--check` 면 쓰지 않고 파일이 계약과 같은지만 본다. |

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

