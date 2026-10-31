# `src/common/` — mode 를 가리지 않는 유틸 — 해석기 탐색 · 리소스 자리 채우기.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`contract_types.py`](contract_types.py) | 생성물 — tools/gen_contract_types.py 가 contracts/mode1-artifacts.v1.json 에서 낸다. 손대지 마라. |
| [`evidence.py`](evidence.py) | 대상 저장소에 봉인된 Mode 1 산출물이 계약대로 있는지 판정하고, 봉인 뒤 소스가 움직였는지 알린다. |
| [`python.py`](python.py) | — |
| [`template.py`](template.py) | 리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외다. |

---

## `contract_types.py`

생성물 — tools/gen_contract_types.py 가 contracts/mode1-artifacts.v1.json 에서 낸다. 손대지 마라.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ArtifactEntry`** | *class* |  |
| **`SupersededBy`** | *class* |  |
| **`ArtifactManifest`** | *class* |  |
| **`DbUse`** | *class* |  |
| **`TermRecord`** | *class* |  |

---

## `evidence.py`

대상 저장소에 봉인된 Mode 1 산출물이 계약대로 있는지 판정하고, 봉인 뒤 소스가 움직였는지 알린다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `git` | `(repo: str, *args) -> str` | 대상 저장소에서 git 을 부르고 stdout 을 낸다. 실패하면 CalledProcessError 다. |
| `sha256_of` | `(path: str) -> str` | 파일 바이트 그대로의 sha256. |
| `source_files` | `(repo: str, exts: Sequence[str], skip: Sequence[str]) -> list[str]` | git 이 추적하는 파일 중 확장자가 맞고, 경로의 어느 성분(파일 이름 포함)도 `skip` 에 없는 것. 정렬해 낸다. |
| `missing` | `(repo: str, sources: Sequence[str]) -> list[str]` | git 이 추적하는데 작업 트리에 없는 소스. 지운 것을 아직 커밋하지 않은 상태다. |
| `blob_ids` | `(repo: str, rels: Sequence[str]) -> dict[str, str]` | 작업 트리 내용 그대로의 blob id. `git hash-object` 는 인자 순서대로 한 줄씩 낸다. |
| `load_manifest` | `(repo: str) -> tuple[ArtifactManifest \| None, str]` | 매니페스트와 빈 글, 또는 None 과 읽지 못한 이유. |
| `judged` | `(m: ArtifactManifest, need: Sequence[str], optional: bool) -> list[str]` | 판정할 종류. `optional` 이면 봉인에 있는 것만 남기고, 하나도 없으면 `need` 그대로다 — 없다는 문제가 나오게. |
| `entry_fits` | `(kind: str, path: str) -> bool` | 봉인 항목 경로가 종류의 자리인가 — terms-db 는 `docs/codegraph/terms-db.json` 하나, wiki 는 `docs/wiki/` 바로 아래 `*.md`. |
| `problems` | `(repo: str, need: Sequence[str], optional: bool = False) -> list[str]` | 구조 문제. 비면 봉인을 근거로 쓸 수 있다. `optional` 이면 봉인에 없는 종류는 묻지 않는다(`judged`). |
| `staleness` | `(repo: str) -> list[str]` | 봉인 뒤 소스의 움직임. 매니페스트에 적힌 규칙으로 다시 모은다 — Mode 1 을 몰라도 된다. |
| `uncommitted` | `(repo: str, m: ArtifactManifest) -> list[str]` | 매니페스트와 거기 적힌 산출물 전부 중 커밋된 내용과 다른 것 — 바뀜 · 추적 안 됨 · 무시됨. 비면 커밋된 봉인이다. |
| `warnings` | `(repo: str, m: ArtifactManifest) -> list[str]` | 낡음 — 멈추지 않는 것들. 소스 움직임 · 미커밋 · 뒤 실행 실패. |
| `status_line` | `(repo: str, need: Sequence[str], optional: bool = False) -> str` | `--status` 의 한 줄. 어느 경우든 예외 없이 글 하나를 돌려준다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` | 구조 문제면 1 과 사람이 칠 명령, 아니면 낡음을 경고로 찍고 0. `--status` 는 늘 0, `--need` 가 틀리면 2 다. |

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

