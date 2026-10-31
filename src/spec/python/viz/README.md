# `src/spec/python/viz/` — 보고서 뼈대 · 빌드 · 검사. 원고를 하나짜리 HTML 로 굽는다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`build.py`](build.py) | — |
| [`check.py`](check.py) | — |
| [`init.py`](init.py) | — |
| [`link_paths.py`](link_paths.py) | — |
| [`wrap_terms.py`](wrap_terms.py) | — |

---

## `build.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `currentBuilderVersion` | `() -> str` |  |
| `main` | `() -> None` |  |

---

## `check.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ScriptCount`** | *class* |  |
| **`LinkResult`** | *class* |  |
| **`TermResult`** | *class* |  |
| `countScripts` | `(html: str) -> ScriptCount` | `<script>` 는 pan/zoom 하나까지만 허용된다(산출물 불변식). |
| `linkIntegrity` | `(decisionIds: list[str], reportSource: str) -> LinkResult` | `data.ts` 의 결정 id 와 `report.tsx` 의 절이 1:1 인지 본다. |
| `undefinedTerms` | `(reportSource: str, termIds: list[str]) -> TermResult` | 본문의 식별자 꼴 낱말 중 용어집에 정의가 없는 것을 찾는다. |
| `versionMatch` | `(dataVersion: str, currentVersion: str) -> dict[str, bool]` | `builderVersion` 불일치는 경고이지 실패가 아니다. |
| `currentBuilderVersion` | `() -> str` |  |
| `main` | `() -> int` |  |

---

## `init.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `parseSpecFilename` | `(basename: str, dir: str = 'specs') -> Optional[dict[str, str]]` |  |
| `findSimilar` | `(slug: str, candidates: list[str]) -> list[str]` |  |
| `currentBuilderVersion` | `(root: str) -> str` |  |
| `currentBranch` | `(cwd: str) -> str` |  |
| `reportDir` | `(cwd: str, docDir: str, slug: str) -> str` |  |
| `hasReport` | `(cwd: str, docDir: str, slug: str) -> bool` |  |
| `listDocs` | `(cwd: str) -> list[dict[str, str]]` |  |
| `writeSkeleton` | `(dir: str, slug: str, date: str, specName: str, branch: str, version: str) -> None` |  |
| `repoTopLevel` | `(cwd: str) -> str` | git 최상위. git 밖이거나 git 이 없으면 cwd 그대로 — build.py 가 링크 뿌리를 찾는 것과 같은 규칙. |
| `modeOneStatus` | `(python: str, repo: str) -> str` | 봉인 상태 한 줄. 판정만 하고 막지 않는다 — Mode 2 는 Mode 1 과 독립이다. |
| `main` | `() -> None` |  |

---

## `link_paths.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `pathPattern` | `() -> re.Pattern[str]` | 경로 꼴 — `a/b.md:3` `c.json` `facts/*.md` `x.py`. |
| `buildIndex` | `(repoRoot: str) -> dict[str, list[str]]` | 저장소 추적 파일의 이름 색인. {basename: [상대경로…]}. git 밖이면 빈 사전. |
| `expandRoot` | `(base: str) -> str` | 경로 앞머리의 `~` 와 `$VAR` / `${VAR}` 를 편다. |
| `makeResolver` | `(bases: list[str], repoRoot: str, index: Optional[dict[str, list[str]]] = None) -> Callable[[str], Optional[dict[str, str]]]` | 해석기. token(줄 번호 뗀 경로) -> {href, kind: "file"\|"dir"} 또는 None. |
| `skipsByClass` | `(tag: str) -> bool` | 여는 태그의 class 에 건너뛸 낱말이 있는지 본다. |
| `linkPaths` | `(html: str, resolve: Callable[[str], Optional[dict[str, str]]], onMiss: Optional[Callable[[str], None]] = None) -> str` | html 의 글자 부분에서 경로 꼴을 찾아 resolve 가 답하는 것만 링크로 감싼다. |

---

## `wrap_terms.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `termPattern` | `(terms: List[str]) -> Pattern[str] \| None` |  |
| `skipsByClass` | `(tag: str) -> bool` |  |
| `wrapTerms` | `(html: str, refs: Dict[str, str]) -> str` |  |

