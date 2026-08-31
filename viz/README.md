# `viz/` — 코드 지도와 위키를 사람이 보는 그림으로 만든다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`__init__.py`](__init__.py) | — |
| [`build.py`](build.py) | — |
| [`check.py`](check.py) | — |
| [`demermaid.py`](demermaid.py) | 위키의 Mermaid 를 사전 렌더 SVG 로 치환한다. |
| [`init.py`](init.py) | — |
| [`link_paths.py`](link_paths.py) | — |
| [`render_classes.py`](render_classes.py) | 모듈 하나를 골라 클래스 층 다이어그램을 그린다. |
| [`render_modules.py`](render_modules.py) | codegraph.json 의 모듈 의존 그래프를 Graphviz 로 그린다. |
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

## `demermaid.py`

위키의 Mermaid 를 사전 렌더 SVG 로 치환한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_mmdc` | `(src_text: str, out_svg: str) -> subprocess.CompletedProcess[str]` |  |
| `render_mermaid` | `(src_text: str, out_svg: str) -> str \| None` | mmdc 로 Mermaid 하나를 SVG 로 굽는다. 실패하면 None. |
| `process` | `(path: str, outdir: str, assets: str, svg_dir: str \| None, rel_assets: str) -> dict[str, int]` |  |
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

## `render_classes.py`

모듈 하나를 골라 클래스 층 다이어그램을 그린다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`CodeNode`** | *class* | codegraph.json 의 nodes[] 한 칸. |
| **`CodeModule`** | *class* | codegraph.json 의 modules[] 한 칸. |
| **`CodeGraph`** | *class* | codegraph.json 전체. |
| **`Member`** | *class* | 클래스 멤버 한 칸. 두 원시 형식이 name/type/access 로 키가 같다. |
| **`Method`** | *class* | `pick_methods` 와 `node_html` 이 실제로 보는 메서드 필드만. |
| **`Detail`** | *class* | `load_detail` 이 두 원시 형식을 맞춰 내는 공통 모양. |
| **`ClangElement`** | *class* | clang-uml(-g json) 의 elements[] 한 칸. |
| **`RoslynMethod`** | *class* | roslyn-dump 의 types[].methods[] 한 칸. 키 이름이 clang-uml 과 다르다. |
| **`RoslynType`** | *class* | roslyn-dump 의 types[] 한 칸. |
| **`DetailFile`** | *class* | `--detail` 로 들어오는 파일. 둘 중 어느 갈래인지는 키 유무로 가른다. |
| `esch` | `(s: object) -> str` |  |
| `esc` | `(s: object) -> str` |  |
| `short` | `(name: str) -> str` | SJH::Scene::Component -> Component. 모듈 클러스터가 이미 맥락을 준다. |
| `load_detail` | `(path: str) -> dict[str \| None, Detail]` | 원문에서 이름 -> (members, methods, is_abstract) 를 뽑는다. |
| `pick_methods` | `(methods: list[Method], limit: int = 6) -> tuple[list[Method], int]` | 책임을 전달하는 메서드만. 사소한 getter/setter·연산자·특수멤버는 뺀다. |
| `node_html` | `(name: str, det: Detail \| None, own_note: dict[str, str]) -> str` | UML 3분할 — 이름(+스테레오타입) / 멤버(+소유권 노트) / 메서드. |
| `main` | `() -> int` |  |

---

## `render_modules.py`

codegraph.json 의 모듈 의존 그래프를 Graphviz 로 그린다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`CodeNode`** | *class* | codegraph.json 의 nodes[] 한 칸. |
| **`CodeModule`** | *class* | codegraph.json 의 modules[] 한 칸. |
| **`CodeGraph`** | *class* | codegraph.json 전체. |
| `esc` | `(s: object) -> str` | DOT 문자열용. |
| `esch` | `(s: object) -> str` | HTML 라벨용. 클래스 이름에 제네릭/템플릿 꺾쇠가 실제로 들어온다 |
| `load` | `(path: str) -> CodeGraph` |  |
| `build` | `(g: CodeGraph) -> tuple['nx.DiGraph[str]', dict[str, list[str]], dict[tuple[str, str], int], dict[str, CodeNode], list[list[str]], set[tuple[str, str]]]` | 모듈 층 그래프와 노드별 부가 정보를 만든다. |
| `node_label` | `(mod: str, names: list[str]) -> str` | 이름 + 클래스 수 + 대표 이름 3개. |
| `emit_dot` | `(g: CodeGraph, path_in: str, G: 'nx.DiGraph[str]', members: dict[str, list[str]], ext_touch: dict[tuple[str, str], int], externals: dict[str, CodeNode], cycles: list[list[str]], cyc_edges: set[tuple[str, str]], show_external: bool) -> str` |  |
| `main` | `() -> int` |  |

---

## `wrap_terms.py`



| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `termPattern` | `(terms: List[str]) -> Pattern[str] \| None` |  |
| `skipsByClass` | `(tag: str) -> bool` |  |
| `wrapTerms` | `(html: str, refs: Dict[str, str]) -> str` |  |

