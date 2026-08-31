# `machine/` — 정적 수집 · 인용 검증 · 측정. 산문을 쓰지 않고 판정하지 않는다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py machine runner viz tools`

## 파일

| 파일 | 하는 일 |
|---|---|
| [`clang_doc.py`](clang_doc.py) | clang-doc 이 흩뿌린 JSON 을 평평한 심볼 목록 하나로 모은다. |
| [`clangd_refs.py`](clangd_refs.py) | clangd 에 stdio JSON-RPC 로 직접 말해 역방향 참조를 받아온다 (E6). |
| [`codegraph_types.py`](codegraph_types.py) | `codegraph.json`(schema_version 2) 의 계약을 적어 둔 한 곳. |
| [`declmap.py`](declmap.py) | 선언과 그 위의 문서 주석을 뽑아 한 장으로 만든다. |
| [`facts.py`](facts.py) | codegraph.json 에서 deep-wiki 주입물(facts/*.md + ranking.json)을 만든다. |
| [`file_cache.py`](file_cache.py) | 파일 통독 캐시. |
| [`fix_citation_paths.py`](fix_citation_paths.py) | 인용의 맨 파일명을 저장소 기준 전체 경로로 보강한다. |
| [`lang_select.py`](lang_select.py) | 어떤 정적 수집기를 돌릴지 고른다. |
| [`normalize.py`](normalize.py) | 언어별 정적 분석 산출물을 codegraph.json(스키마 v2)으로 바꾼다. |
| [`pycalls.py`](pycalls.py) | 파이썬 소스에서 심볼과 호출 관계를 뽑는 수집기. |
| [`reverse_refs.py`](reverse_refs.py) | 1차 심볼 전수 역참조를 뽑는다 (E6 + 전수 확정). |
| [`survey_plan.py`](survey_plan.py) | 전수조사 배치 계획. |
| [`terms_db.py`](terms_db.py) | 코드베이스 용어 전수 수집. |
| [`test_clang_doc.py`](test_clang_doc.py) | clang-doc 적재기의 회귀 시험. |
| [`test_declmap.py`](test_declmap.py) | 선언·문서주석 추출기의 회귀 시험. |
| [`test_external_contracts.py`](test_external_contracts.py) | 바깥 도구의 동작에 기대는 주장을 고정한다. |
| [`test_file_cache.py`](test_file_cache.py) | 파일 캐시의 회귀 시험. |
| [`test_lang_select.py`](test_lang_select.py) | 언어 판별의 회귀 시험. |
| [`test_normalize.py`](test_normalize.py) | 정규화 계층의 회귀 시험. |
| [`test_pycalls.py`](test_pycalls.py) | AST 호출 수집기의 회귀 시험. |
| [`test_survey_plan.py`](test_survey_plan.py) | 층 계획기의 회귀 시험. |
| [`test_terms_db.py`](test_terms_db.py) | terms-db 우선 파이프라인의 회귀 시험. |
| [`test_warmup.py`](test_warmup.py) | 증분 무효화 판정의 회귀 시험. |
| [`test_xmldoc.py`](test_xmldoc.py) | 주석 블록 주입기의 회귀 시험. |
| [`verify_citations.py`](verify_citations.py) | 문서의 file:line 인용을 기계로 판정한다 (L1/L2/L3). |
| [`warmup.py`](warmup.py) | 전수조사를 매번 전량 다시 하지 않게 하는 파일별 캐시와 무효화. |
| [`xmldoc.py`](xmldoc.py) | 주석 본문을 .xml 한 곳에 모으고 코드에는 레퍼런스만 남긴다. |

---

## `clang_doc.py`

clang-doc 이 흩뿌린 JSON 을 평평한 심볼 목록 하나로 모은다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Symbol`** | *class* | 이 파일이 내는 심볼 하나. `normalize.py::merge_clang_doc` 이 그대로 받아 읽는 꼴이다. |
| `qualified_namespace` | `(item: dict[str, Any]) -> str` | `Namespace` 배열을 바깥부터의 `A::B::C` 로 편다. |
| `flatten_description` | `(desc: Any) -> str` | 저자 문서 주석에서 글자만 순서대로 뽑아 한 줄로 잇는다. |
| `function_signature` | `(item: dict[str, Any]) -> str` | 사람이 읽는 한 줄 시그니처. `bool ApplyHomography(const cv::Mat & image, …)`. |
| `_symbol` | `(item: dict[str, Any], kind: str, signature: str = '') -> Symbol \| None` | 공통 꼴로 옮긴다. 급소 ② — 위치가 없으면 None 을 돌려 버리게 한다. |
| `_json_root` | `(out_dir: str) -> str` | `clang-doc --output <D>` 는 `<D>/json/` 을 만든다. 둘 중 어느 쪽을 받아도 되게 한다. |
| `load_clang_doc` | `(out_dir: str) -> list[Symbol]` | clang-doc 의 흩어진 산출물을 모아 평평한 심볼 목록으로 만든다. |

---

## `clangd_refs.py`

clangd 에 stdio JSON-RPC 로 직접 말해 역방향 참조를 받아온다 (E6).

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Clangd`** | *class* |  |
| `Clangd.__init__` | `(self, root: str, compdb_dir: str, binary: str = 'clangd', background_index: bool = True) -> None` |  |
| `Clangd._send` | `(self, obj: dict[str, Any]) -> None` |  |
| `Clangd._reader` | `(self) -> None` |  |
| `Clangd._drain_stderr` | `(self) -> None` |  |
| `Clangd.request` | `(self, method: str, params: Any, timeout: float = 120) -> dict[str, Any]` |  |
| `Clangd.notify` | `(self, method: str, params: Any) -> None` |  |
| `Clangd.initialize` | `(self) -> dict[str, Any]` |  |
| `Clangd.did_open` | `(self, rel: str) -> None` |  |
| `Clangd.references` | `(self, rel: str, line: int, col: int, include_decl: bool = True) -> dict[str, Any]` | line/col 은 clang-uml 과 같은 1-based 로 받는다. LSP 는 0-based 라 여기서 변환한다. |
| `Clangd.shutdown` | `(self) -> None` |  |
| `Clangd.notifications` | `(self) -> list[dict[str, Any]]` |  |
| `Clangd.progress_state` | `(self) -> dict[str, str]` |  |
| `Clangd.index_idle` | `(self) -> bool` | 진행 중인(begin/report 상태로 남은) progress 토큰이 하나도 없으면 idle. |
| `Clangd.wait_for_index` | `(self, timeout: float = 600, settle: float = 2.0, poll: float = 0.25) -> tuple[bool, float]` | 색인이 시작됐다가 전부 end 로 끝날 때까지 기다린다. (완료했나, 걸린 초). |
| `to_repo_relative` | `(uri: str, root: str) -> str` |  |

---

## `codegraph_types.py`

`codegraph.json`(schema_version 2) 의 계약을 적어 둔 한 곳.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Node`** | *class* | 코드 지도의 점. 1차 타입 하나 또는 접힌 외부 섬 하나. |
| **`Module`** | *class* | 폴더 트리 한 칸. `depends_on` 은 클래스 간선에서 유도된 타입 의존이다. |
| **`CodeGraph`** | *class* | `normalize.py::_assemble` 이 내는 최종 모양. |

---

## `declmap.py`

선언과 그 위의 문서 주석을 뽑아 한 장으로 만든다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`LangRule`** | *class* | LANGS 한 칸의 생김새. 다섯 칸 중 None 이 될 수 있는 것은 `strip` 하나뿐이다. |
| **`Decl`** | *class* | 선언 하나. `line` 은 1-based 다. `scan` 이 내고 `render` · warmup · run_mode1 이 읽는다. |
| **`FileDecls`** | *class* | 파일 한 개 몫. `warmup.decl_hash` 가 받는 것이 이 꼴이다. |
| `tracked_files` | `(repo: str, lang: str, includes: list[str]) -> list[str]` | git 이 아는 파일만 본다 — 빌드 산출물과 캐시를 걸러 내는 가장 싼 방법이다. |
| `doc_above` | `(lines: list[str], i: int, rule: LangRule) -> str` | 선언 위에 붙은 문서 주석을 모은다. 빈 줄과 특성(attribute) 줄은 건너뛴다. |
| `scan` | `(repo: str, lang: str, includes: list[str], doc_chars: int) -> tuple[dict[str, FileDecls], dict[str, int]]` |  |
| `render` | `(result: dict[str, FileDecls]) -> str` | 사람과 LLM 이 그대로 읽을 수 있는 글자로. JSON 보다 짧다. |
| `main` | `() -> int` |  |

---

## `facts.py`

codegraph.json 에서 deep-wiki 주입물(facts/*.md + ranking.json)을 만든다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`GraphModule`** | *class* |  |
| **`CodeGraph`** | *class* | `normalize.py` 가 낸 codegraph.json 중 이 파일이 실제로 읽는 부분만. |
| **`HotspotStat`** | *class* | git log 에서 센 파일 하나의 변경량. |
| **`HotspotRow`** | *class* | 변경량에 "어느 파일 · 어느 모듈" 을 더한 것. ranking.json 에 실린다. |
| **`ClassRow`** | *class* | 1차 클래스 하나의 사실 행. `build` 가 내고 표 넷이 쓴다. |
| **`ModuleRow`** | *class* |  |
| **`HotspotBlock`** | *class* |  |
| **`Ranking`** | *class* | ranking.json 전체. |
| **`RoslynType`** | *class* | `--detail` 로 받는 roslyn-dump.json 의 타입 하나 (C# 전용). |
| **`RoslynDump`** | *class* |  |
| `sh` | `(cmd: list[str], cwd: str) -> str \| None` |  |
| `collect_hotspot` | `(repo: str) -> dict[str, HotspotStat] \| None` | 파일별 커밋 수·증감 줄수. 이름변경(old => new)은 새 경로로 귀속시킨다(단순 규칙). |
| `build` | `(g: CodeGraph) -> tuple[list[ClassRow], 'nx.DiGraph[str]', list[list[str]], set[str]]` |  |
| `cite` | `(r: ClassRow) -> str` |  |
| `main` | `() -> int` |  |

---

## `file_cache.py`

파일 통독 캐시.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_paths` | `(repo: str, rel: str) -> tuple[str, str]` | 내용 해시로 캐시를 무효화한다. mtime 은 체크아웃으로 흔들려 못 믿는다. |
| `get` | `(repo: str, rel: str) -> dict[str, object] \| None` | 캐시가 있고 내용 해시가 같으면 돌려준다. 아니면 None — 부르는 쪽이 통독한다. |
| `put` | `(repo: str, rel: str, outline: object) -> str` | 개요를 남긴다. 임시 파일 + os.replace 라 원자적이다. |

---

## `fix_citation_paths.py`

인용의 맨 파일명을 저장소 기준 전체 경로로 보강한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `index_repo` | `(repo: str) -> dict[str, list[str]]` | 파일명 -> 저장소 기준 상대경로 목록. |
| `main` | `() -> int` |  |

---

## `lang_select.py`

어떤 정적 수집기를 돌릴지 고른다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`LangSelect`** | *class* |  |
| `count_sources` | `(repo: str) -> dict[str, int]` | 언어별 소스 파일 수. git 이 추적하는 것만 센다 — 빌드 산출물과 vendored 를 피한다. |
| `read_docs` | `(repo: str, limit: int = 6000) -> str` | 루트 문서 몇 개를 앞부분만 잘라 잇는다. 없으면 빈 문자열이다. |
| `select` | `(repo: str, proposed: str \| None = None) -> LangSelect` | 제안이 검사를 통과하면 그것을, 아니면 파일 수가 가장 많은 언어를 고른다. |
| `main` | `() -> int` |  |

---

## `normalize.py`

언어별 정적 분석 산출물을 codegraph.json(스키마 v2)으로 바꾼다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`SourceLocation`** | *class* | clang-uml 의 `source_location`. 남의 헤더가 아니라 이 저장소의 첫 사용 지점을 |
| **`UmlMember`** | *class* | `elements[].members[]` 한 칸. 소유 간선의 근거 위치가 여기서 나온다. |
| **`UmlTemplateParam`** | *class* | `elements[].template_parameters[]` 한 칸. R5 투과가 `type` 을 따라 내려간다. |
| **`UmlIdentity`** | *class* | 1차 판정에 필요한 최소한 — clang-uml 의 element 와 clang-doc 심볼의 교집합이다. |
| **`UmlElement`** | *class* | `elements[]` 한 칸. 위의 교집합에 clang-uml 만 갖는 열쇠를 더한 것이다. |
| **`UmlRelationship`** | *class* | `relationships[]` 한 칸. `type` 은 clang-uml 의 낱말이라 `CLANG_UML_KIND` 를 거쳐야 한다. |
| `git_commit` | `(repo: str) -> str \| None` |  |
| `module_of` | `(path: str \| None) -> str \| None` | 모듈 경계 = 폴더 트리. C# 쪽(`cs_module_of`)과 축이 같다. |
| `load_clang_uml` | `(path: str) -> tuple[list[UmlElement], list[UmlRelationship], dict[str, Any]]` |  |
| `defines_at` | `(repo: str, rel_file: str \| None, line_no: int \| None, name: str) -> bool` | `source_location` 이 가리키는 줄이 실제로 그 타입을 정의하는지 본다. |
| `tracked_set` | `(repo: str) -> set[str] \| None` | git 이 추적하는 파일 집합. 1차 판정의 급소다 — 남의 헤더는 추적되지 않는다. |
| `is_first_party` | `(el: UmlIdentity, repo: str \| None = None, ns: tuple[str, ...] = CPP_FIRST_PARTY_NS, tracked: set[str] \| None = None) -> bool` | 1차 코드 판정. 두 갈래다. |
| `external_group` | `(el: UmlElement) -> str` | R2 — 외부 하나 = 노드 하나. 입도는 라이브러리·서브모듈 이름이다. |
| `is_transparent_wrapper` | `(el: UmlElement) -> bool` | R5 — 컨테이너·스마트포인터는 노드로 만들지 않고 투과시킨다. |
| `member_location` | `(src_el: UmlElement \| None, label: str \| None) -> tuple[str \| None, int \| None]` | 간선의 근거 위치. label(멤버 이름)로 members[] 를 정확히 찾는다. |
| `node_name` | `(el: UmlElement) -> str` | 중첩 타입의 name 은 구분자가 :: 가 아니라 ## 이고 바깥 클래스가 namespace 에 없다. |
| `doc_qualified_name` | `(sym: Symbol) -> str` | clang-doc 심볼의 완전 수식 이름. clang-uml 의 `display_name` 과 같은 축으로 맞춘다. |
| `_doc_element` | `(sym: Symbol) -> UmlIdentity` | clang-doc 심볼을 `is_first_party` 가 읽는 꼴로 옮긴다. |
| `merge_clang_doc` | `(nodes: dict[str, Node], doc_symbols: Sequence[Symbol] \| None, repo: str, tracked: set[str] \| None, stats: Counter[str]) -> None` | clang-doc 의 심볼을 clang-uml 이 만든 노드 표에 합친다. |
| `normalize_cpp` | `(elements: list[UmlElement], relationships: list[UmlRelationship], repo: str, source_tool: str, doc_symbols: Sequence[Symbol] = ()) -> tuple[CodeGraph, Counter[str]]` |  |
| `_assemble` | `(nodes: dict[str, Node], edges: dict[tuple[str, str, str], Edge], stats: Counter[str], *, language: str, source_tool: str, repo: str) -> tuple[CodeGraph, Counter[str]]` | 언어 공통 꼬리 — R1 제거, 모듈 의존 유도, 최종 dict 조립. |
| **`RoslynCompilation`** | *class* | `compilation` — F5 게이트가 보는 곳. |
| **`RoslynType`** | *class* | `types[]` 한 칸. 1차 판정은 file 유무가 아니라 `assembly` 다. |
| **`RoslynRelation`** | *class* | `relations[]` 한 칸. `origin` 과 `attrs` 는 C# 만 갖는 비대칭 기록이다. |
| **`RoslynDump`** | *class* | `roslyn-dump.json` 통째. `tool` 은 없을 수 있어 `main` 이 기본값을 준다. |
| `cs_module_of` | `(path: str \| None) -> str \| None` | 모듈 경계 = 폴더 트리. `module_of`(C++)와 축이 같다. |
| `cs_asm2pkg` | `(repo: str) -> dict[str, str]` | 어셈블리 이름 -> 패키지 id. `Library/PackageCache/<pkg>@<hash>/**/*.asmdef` 의 |
| `cs_external_group` | `(asm: str \| None, asm2pkg: dict[str, str]) -> str` | R2 — 외부 하나 = 노드 하나. 입도는 패키지 이름. |
| `normalize_csharp` | `(dump: RoslynDump, repo: str) -> tuple[CodeGraph, Counter[str]]` |  |
| **`GriffeExprNode`** | *class* | 식 트리 한 마디. `cls` 가 어느 마디인지 말하고, 나머지 열쇠는 마디마다 다르다. |
| **`GriffeParam`** | *class* | `parameters[]` 한 칸. `self`·`cls` 와 주석 없는 매개변수는 호출부가 거른다. |
| **`GriffeObject`** | *class* | 모듈·클래스·속성·함수를 한 형으로 받는다 — griffe 가 `kind` 로만 가르기 때문이다. |
| `py_external_group` | `(target: str) -> str` | R2 — 외부 하나 = 노드 하나. 입도는 import 루트 이름이다. |
| `py_expr_name` | `(expr: GriffeExpr \| None) -> str \| None` | 식이 단순 이름이면 그 이름을, 아니면 None. |
| `py_resolve` | `(name: str, mod_path: str, imports: dict[str, str], first_party: set[str]) -> str` | 이름 해소 순서: 모듈의 import 표 -> 같은 모듈의 1차 클래스 -> 못 품. |
| `py_walk_expr` | `(expr: GriffeExpr \| None, mod_path: str, imports: dict[str, str], first_party: set[str], stats: Counter[str], depth: int = 0) -> list[str]` | R5 — 컨테이너 껍데기를 벗기고 안의 타입 이름들을 모아 돌려준다. |
| `normalize_python` | `(dump: GriffeDump, repo: str, source_tool: str, calls: PyCallsDump \| None = None) -> tuple[CodeGraph, Counter[str]]` | griffe dump(JSON) -> codegraph.json. C++/C# 과 같은 모양(노드 -> 간선 -> _assemble)이다. |
| `merge_py_calls` | `(nodes: dict[str, Node], node_id: dict[str, str], edges: dict[tuple[str, str, str], Edge], calls: PyCallsDump, stats: Counter[str]) -> None` | `pycalls.py` 가 뽑은 함수·메서드와 호출을 합친다. |
| `build_parser` | `() -> argparse.ArgumentParser` | 명령줄 규약. `--clang-doc` 과 `--py-calls` 는 배타 그룹에 넣지 않는다. |
| `main` | `() -> None` |  |

---

## `pycalls.py`

파이썬 소스에서 심볼과 호출 관계를 뽑는 수집기.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`PySymbol`** | *class* | 정의 하나. `name` 은 모듈 경로를 앞에 붙인 완전 수식 점 이름이다. |
| **`PyCall`** | *class* | 호출 하나. 양끝은 `PySymbol.name` 과 같은 꼴이다. |
| **`PyCallsDump`** | *class* |  |
| `module_path` | `(rel: str) -> str` | `machine/normalize.py` -> `machine.normalize`. |
| `signature_of` | `(fn: ast.FunctionDef \| ast.AsyncFunctionDef) -> str` | `(a, b=..., *args, **kw) -> T` 꼴. 주석은 원문 그대로 살린다. |
| `import_table` | `(tree: ast.Module, stem_to_module: dict[str, str]) -> dict[str, str]` | `from warmup import status` -> {"status": "machine.warmup.status"}. |
| `scan_module` | `(tree: ast.Module, mod: str, rel: str, stem_to_module: dict[str, str]) -> tuple[list[PySymbol], list[tuple[str, str, int]]]` | 한 모듈의 (심볼, 미해석 호출) 을 낸다. 호출의 대상은 아직 쓰인 그대로다. |
| `collect` | `(repo: str, roots: list[str]) -> PyCallsDump` | `roots` 아래 `*.py` 를 전부 읽어 심볼과 해석된 호출을 낸다. |
| `main` | `() -> None` |  |

---

## `reverse_refs.py`

1차 심볼 전수 역참조를 뽑는다 (E6 + 전수 확정).

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`_SourceLocation`** | *class* | clang-uml 이 적는 선언 자리. 줄·칸 모두 1-based 다. |
| **`_UmlElement`** | *class* | clang-uml 의 element 한 칸. |
| **`_Uml`** | *class* |  |
| **`_LspPosition`** | *class* | LSP 좌표. 줄·칸 모두 0-based 라 산출물로 나갈 때 1을 더한다. |
| **`_LspRange`** | *class* |  |
| **`_LspLocation`** | *class* |  |
| **`_Loc`** | *class* | 산출물의 자리 한 칸. uri/range 가 아니라 저장소 상대경로와 1-based 좌표다(E7). |
| **`_Symbol`** | *class* |  |
| **`_IndexStat`** | *class* |  |
| **`_QueryStat`** | *class* |  |
| **`ReverseRefs`** | *class* | `reverse_refs/1` 산출물 전체. |
| `main` | `(root: str, compdb: str, uml_path: str, out_path: str, binary: str \| None = None) -> ReverseRefs` |  |

---

## `survey_plan.py`

전수조사 배치 계획.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`CodeGraph`** | *class* | `prep` 이 낸 codegraph.json 중 이 파일이 실제로 읽는 부분만. |
| **`PackedBatch`** | *class* | `pack` 이 내는 중간 묶음. 아직 배치 id 도 심볼 레코드도 붙지 않았다. |
| **`PlanSymbol`** | *class* |  |
| **`PlanBatch`** | *class* |  |
| **`PlanLayer`** | *class* | 심볼 층과 맨 끝 비노드 층이 한 목록에 섞여 있다. |
| **`PlanTotals`** | *class* |  |
| **`SurveyPlan`** | *class* |  |
| `layer_of` | `(first: Collection[str], edges: Iterable[tuple[str, str]]) -> tuple[dict[str, int], dict[str, bool]]` | 의존 대상이 없으면 층0, 아니면 1 + 의존 대상들의 최대 층. |
| `pack` | `(members: Iterable[str], file_of: Mapping[str, str \| None], target: int) -> list[PackedBatch]` | 같은 파일의 같은 층 심볼은 **한 배치에** 몰아넣는다 — 층 안 중복 통독을 0으로 만든다. |
| `plan` | `(cg: CodeGraph, target: int = 8, only_files: Iterable[str] \| None = None) -> SurveyPlan` | 코드 지도 -> 층 · 배치 계획. |
| `main` | `(argv: list[str] \| None = None) -> int` |  |

---

## `terms_db.py`

코드베이스 용어 전수 수집.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`DbUse`** | *class* | 레코드의 `uses[]` 한 칸. `source` 는 merge_terms 가 LLM 이 보탠 간선에만 남긴다. |
| **`TermRecord`** | *class* | 용어 하나. `id` 는 codegraph 에서 온 레코드에만 있다 — reading 레코드는 키가 곧 이름이다. |
| `_where` | `(node: Node \| Edge) -> str` | `file:line` 위치 문자열. 파일이 없으면(외부 노드) 빈 문자열. |
| `_split_where` | `(where: str) -> tuple[str \| None, int \| None]` | `file:line` -> (file, line). 빈 문자열이면 (None, None). 줄 번호가 없으면 (file, None). |
| `_recompute_neighbors` | `(db: TermsDb) -> None` | uses(방향 있음)에서 neighbors(방향 없음)를 다시 센다. |
| `build_terms` | `(graph: CodeGraph, facts: Mapping[str, object], hotspot: Sequence[Mapping[str, str]]) -> TermsDb` | codegraph.json 에서 용어 사전을 만든다. 입력이 같으면 출력도 같다. |
| `project_codegraph` | `(db: TermsDb, language: str = 'unknown', repo_commit: str = '') -> CodeGraph` | terms-db -> codegraph.json (schema_version 2). codegraph 는 terms-db 의 부분집합이다. |
| `_stem` | `(key: str, kind: str) -> str` | L3 대조용 이름 조각. `calls[]` -> `calls`, `Outer::Inner` -> `Inner`, `terms_db.main` -> `main`. |
| `_written_by_llm` | `(rec_source: str, use: DbUse) -> bool` | 이 간선을 LLM 이 썼는가. 표시가 없는 간선은 정적 도구가 낸 것이다. |
| `check_terms` | `(db: TermsDb, repo: str) -> list[tuple[str, str, str]]` | 3값 판정 목록 [(등급, 용어, 사유)]. 등급은 "실패" \| "근거 없음". 비어 있으면 전부 통과. |
| `merge_terms` | `(base: TermsDb, reading: Terms) -> TermsDb` | reading(LLM 이 쓴 것)을 base(codegraph 가 만든 것)에 합친다. 구조 필드는 codegraph 가 이긴다. |
| `_git_commit` | `(repo: str) -> str` | 저장소 HEAD. git 이 없거나 저장소가 아니면 빈 문자열 — 실패시키지 않는다. |
| `main` | `() -> int` |  |

---

## `test_clang_doc.py`

clang-doc 적재기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_write` | `(root: str, rel: str, obj: object) -> str` |  |
| `_by_name` | `(syms: list[Symbol], name: str) -> Symbol` |  |
| `test_namespace_is_reversed` | `(tmp_path: Path)` | 네임스페이스를 뒤집어 이어 완전 수식 이름을 만든다. |
| `test_global_namespace_becomes_empty` | `(tmp_path: Path)` | 전역 네임스페이스라는 가짜 이름은 빈 문자열이 된다. |
| `test_symbol_without_location_is_dropped` | `(tmp_path: Path)` | 위치가 없는 심볼은 적재에서 빠진다. |
| `test_description_nested_text_is_flattened` | `(tmp_path: Path)` | 중첩된 TextComment 를 한 줄로 편다. |
| `test_description_absent_gives_empty_doc` | `(tmp_path: Path)` | 주석이 없으면 doc 은 빈 문자열이다. |
| `test_records_come_from_mangled_files_not_index` | `(tmp_path: Path)` | 레코드의 위치·종류·네임스페이스는 맹글링 파일에서 온다. |
| `test_enum_kind_and_location_come_from_index` | `(tmp_path: Path)` | enum 은 index.json 에 위치가 함께 실려 온다. |
| `test_function_signature_has_return_type_and_params` | `(tmp_path: Path)` | 반환형과 인자를 사람이 읽는 한 줄로 만든다. |
| `test_record_has_no_signature` | `(tmp_path: Path)` | 레코드에는 시그니처가 없다. |
| `test_duplicate_usr_is_collapsed_and_order_is_deterministic` | `(tmp_path: Path)` | 같은 USR 은 한 번만 나오고, 두 번 읽어도 순서가 같다. |
| `test_accepts_the_parent_directory_of_json` | `(tmp_path: Path)` | `<D>` 와 `<D>/json` 둘 다 적재 뿌리로 받는다. |
| `test_missing_directory_gives_empty_list` | `(tmp_path: Path)` | 없는 디렉토리를 주면 터지지 않고 빈 목록이다. |
| `_golden` | `() -> list[Symbol]` |  |
| `test_golden_compute_panorama_is_located` | `()` | 자유 함수가 파일:줄과 함께 잡히는지를 실제 산출물에서 본다. |
| `test_golden_counts` | `()` | 종류별 개수를 못박는다 — 의도한 변경이면 기대값을 함께 고친다. |
| `test_golden_every_symbol_has_a_location` | `()` | 위치 없는 심볼이 새면 전수조사 레코드의 `where` 가 빈다. |
| `test_golden_author_comments_are_carried` | `()` | 저자 문서 주석이 심볼에 실린다 — clang-uml 이 주지 못하는 값이다. |

---

## `test_declmap.py`

선언·문서주석 추출기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_doc` | `(lines: list[str], i: int, lang: str) -> str` |  |
| `test_cs_decl_catches_modifiers_and_generics` | `() -> None` | 수식어가 여러 개 붙고 들여쓰여 있어도 종류와 이름을 뽑는다. |
| `test_cs_decl_catches_interface_with_constraint` | `() -> None` | 제네릭 제약절이 뒤에 붙은 인터페이스 선언도 잡는다. |
| `test_cpp_decl_catches_enum_class` | `() -> None` | `enum class` 는 두 낱말이 한 종류다. |
| `test_py_decl_catches_def_and_class` | `() -> None` | def 와 class 를 모두 잡고 이름을 두 번째 그룹에 둔다. |
| `test_ts_decl_catches_export_function` | `() -> None` | export 가 앞에 붙은 함수 선언을 잡는다. |
| `test_cs_doc_strips_slashes_and_xml_tags` | `() -> None` | `///` 와 XML 태그를 벗기고 본문만 남긴다. |
| `test_cs_doc_skips_attribute_between_comment_and_decl` | `() -> None` | 주석과 선언 사이에 낀 속성 줄을 건너뛴다. |
| `test_cpp_doc_strips_comment_marker` | `() -> None` | `//` 표시를 벗기고 본문만 남긴다. |
| `test_doc_stops_at_code` | `() -> None` | 주석이 아닌 코드 줄을 만나면 멈춘다 — 위쪽 딴 함수의 주석을 끌어오지 않는다. |
| `test_doc_has_a_ceiling` | `() -> None` | 아무리 긴 주석 더미라도 정해진 줄 수까지만 거슬러 올라간다. |
| `test_skip_dirs_covers_build_and_cache` | `() -> None` | 빌드 산출물과 캐시 디렉토리가 거름망에 들어 있다. |
| `test_first_party_rejects_qt_type_seen_inside_repo` | `() -> None` | 저장소 안에서 보였어도 git 이 추적하지 않는 파일의 타입은 1차가 아니다. |
| `test_first_party_accepts_tracked_global_namespace_type` | `(tmp_path: Path) -> None` | git 이 추적하는 파일에서 정의된 전역 네임스페이스 타입은 1차다. |

---

## `test_external_contracts.py`

바깥 도구의 동작에 기대는 주장을 고정한다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_networkx_digraph_is_not_subscriptable_at_runtime` | `() -> None` | `nx.DiGraph[str]` 은 TypeError 다. 그래서 서명의 주석을 따옴표에 넣는다. |
| `_svg_size` | `(dot_src: str, tmp: Path) -> tuple[float, float]` |  |
| `test_graphviz_legend_edge_without_constraint_widens_the_canvas` | `(tmp_path: Path) -> None` | 범례 간선을 `constraint=false` 로 두면 랭크 제약이 없어 캔버스가 옆으로 넓어진다. |
| `test_langs_table_shape_is_uniform` | `() -> None` | 네 언어 전부 같은 다섯 칸을 갖고, 칸마다 형이 고정돼 있다. |
| `test_declmap_regex_is_line_based_and_syntax_blind` | `() -> None` | 정규식이라 문법을 모른다 — 문자열 안의 `class` 에도 걸리고, 한 줄만 본다. |
| `test_griffe_gives_expression_trees_not_strings` | `(tmp_path: Path) -> None` | 타입 주석은 문자열이 아니라 구조화된 식 트리로 온다. |
| `test_python_ast_unparse_round_trips_annotations` | `() -> None` | `pycalls.signature_of` 는 `ast.unparse` 로 주석을 되살린다. 원문 그대로여야 한다. |

---

## `test_file_cache.py`

파일 캐시의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_repo` | `(tmp_path: Path, text: str = '처음 내용\n') -> str` |  |
| `_outline` | `(got: dict[str, object] \| None) -> dict[str, object]` | 캐시 한 건에서 개요만 꺼낸다. json 에서 온 사전이라 값이 `object` 다 — 한 번 좁힌다. |
| `test_없으면_None` | `(tmp_path: Path)` | 캐시가 없으면 None 이다 — 부르는 쪽이 통독하라는 뜻이다. |
| `test_넣은_것을_그대로_돌려준다` | `(tmp_path: Path)` | 넣은 개요가 경로와 함께 그대로 돌아온다. |
| `test_내용이_바뀌면_무효` | `(tmp_path: Path)` | 줄이 밀린 개요를 그대로 쓰면 where 가 거짓말을 한다. |
| `test_없는_파일이면_None` | `(tmp_path: Path)` | 지워진 파일에 해시를 낼 수 없다. 터지지 말고 None 이어야 한다. |
| `test_캐시는_out_아래에_산다` | `(tmp_path: Path)` | out/ 은 gitignore 다. 재생성 가능한 파생물이 커밋에 섞이면 안 된다. |
| `test_파일마다_다른_자리` | `(tmp_path: Path)` | 경로 해시를 키로 쓰므로 두 파일이 서로를 덮지 않는다. |
| `test_임시파일을_남기지_않는다` | `(tmp_path: Path)` | os.replace 로 갈아 끼우므로 .tmp 가 남으면 안 된다 — 남으면 다음 읽기가 반쯤 쓰인 것을 본다. |
| `test_망가진_캐시는_None` | `(tmp_path: Path)` | 손으로 고쳐 깨졌거나 반쯤 쓰인 파일을 만나도 터지지 않는다. |

---

## `test_lang_select.py`

언어 판별의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_repo` | `(tmp: Path, files: dict[str, str]) -> str` |  |
| `test_counts_only_git_tracked_files` | `(tmp_path: Path) -> None` | 빌드 산출물과 vendored 를 세지 않기 위해 git 이 아는 파일만 센다. |
| `test_no_proposal_falls_back_to_file_counts` | `(tmp_path: Path) -> None` | 제안이 없으면 파일 수가 가장 많은 언어로 간다. |
| `test_proposal_can_override_the_count` | `(tmp_path: Path) -> None` | 세는 것으로는 '많은 쪽이 도구이고 주제는 적은 쪽' 을 알 수 없다. |
| `test_proposal_with_no_sources_is_rejected` | `(tmp_path: Path) -> None` | 그 언어의 소스가 한 개도 없으면 헛소리다. 버리고 파일 수로 간다. |
| `test_proposal_without_a_collector_falls_back` | `(tmp_path: Path) -> None` | 수집기가 없는 언어(ts)를 고르면 prep 이 막힌다 — 수집 가능한 쪽으로 물러선다. |
| `test_unknown_word_is_rejected` | `(tmp_path: Path) -> None` | 모형이 아는 낱말 밖을 내면 버린다. |
| `test_empty_repo_selects_nothing` | `(tmp_path: Path) -> None` | 소스가 하나도 없으면 고르지 않는다 — 지어내지 않는다. |
| `test_collector_names_match_prep` | `(tmp_path: Path) -> None` | 여기서 내는 수집기 이름이 prep 이 아는 이름과 같아야 한다. |
| `test_read_docs_picks_root_documents` | `(tmp_path: Path) -> None` | 모형에게는 루트 문서만 준다. 없는 것은 조용히 건너뛴다. |

---

## `test_normalize.py`

정규화 계층의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `test_clang_uml_kind_is_not_identity` | `() -> None` | clang-uml 의 낱말을 그대로 옮기면 안 된다. 값 멤버는 composition, 포인터는 aggregation. |
| `test_clang_uml_kind_passthrough` | `() -> None` | 뜻이 같은 것은 그대로 간다. |
| `test_containment_is_not_mapped` | `() -> None` | containment 는 8종 enum 에 자리가 없어 버린다. 대응표에 있으면 안 된다. |
| `test_csharp_kind_map_is_total` | `() -> None` | roslyn-dump 가 내는 4종이 전부 사상된다. |
| `test_r5_cpp_is_list_based_not_all_std_templates` | `() -> None` | basic_string 은 투과하지 않는다. 일반화하면 (STL) std 노드가 통째로 사라진다. |
| `test_r5_cpp_requires_std_namespace` | `() -> None` | 이름이 같아도 std 가 아니면 투과 대상이 아니다. |
| `test_r5_csharp_uses_generic_def_and_covers_array_and_tuple` | `() -> None` | C# 은 generic_def 기준이고 배열("[]")과 튜플도 투과 목록에 든다. |
| `test_r7_csharp_uses_canonical_names_not_keywords` | `() -> None` | roslyn-dump 는 System.String 으로 내므로 R7 도 정식 이름이어야 매칭된다. |
| `test_cpp_module_of` | `(path: str, expected: str) -> None` | C++ 은 경로의 폴더가 곧 모듈이다. |
| `test_cs_module_of` | `(path: str, expected: str) -> None` | C# 도 폴더 트리를 따르되 Assets/@Scripts 아래 한 겹을 모듈로 본다. |
| `test_cs_external_group_naming` | `() -> None` | 어셈블리 이름을 패키지·엔진·벤더링 무리로 접는다. |
| `_load` | `(repo: str) -> CodeGraph` |  |
| `test_golden_counts` | `(repo: str, lang: str, nodes: int, edges: int, mods: int) -> None` | 노드 · 간선 · 모듈 수를 못박는다 — 의도한 변경이면 기대값을 함께 고친다. |
| `test_golden_cpp_association_is_zero` | `() -> None` | C++ 에서 association 은 0이어야 한다 — 0이 아니면 대응표가 항등으로 되돌아간 것이다. |
| `test_golden_csharp_has_no_ownership_kinds` | `() -> None` | C# 은 언어에 소유 표지가 없어 composition/aggregation 이 0이다. |
| `test_golden_no_containment_leaked` | `() -> None` | containment 는 버린다. 산출물에 남아 있으면 안 된다. |
| `test_golden_external_nodes_have_no_location` | `() -> None` | 외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다. |
| `test_golden_r4_no_edges_out_of_island` | `() -> None` | 간선은 사용자 코드 → 외부 단방향만. 외부발 간선이 있으면 안 된다. |
| `test_golden_module_deps_exclude_external` | `() -> None` | 모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 모든 모듈이 그리로 향해 노이즈가 된다. |
| `test_golden_cpp_r5_recovered_first_party_ownership` | `() -> None` | R5 를 빼면 사용자 코드끼리의 소유 간선이 사라진다 — 표본 하나가 살아 있는지 본다. |
| `test_golden_ownership_edges_all_have_location` | `() -> None` | 소유 간선은 멤버 선언 줄을 가진다 — clang-uml 의 members[] 를 따로 뒤져 얻는다. |
| `test_nested_name_uses_double_hash` | `() -> None` | 중첩 타입의 구분자는 Outer##Inner 다. :: 로 쪼개면 L3 대조가 반드시 틀린다. |
| `_run_verifier` | `(tmp_path: Path, body: str, repo: str, codegraph: str, detail: str \| None = None) -> str` |  |
| `test_verifier_catches_l1_l2_and_wrong_name` | `(tmp_path: Path) -> None` | 없는 파일 · 줄 초과 · 엉뚱한 이름을 각각 제 갈래로 잡는다. |
| `test_verifier_does_not_warn_on_sources_comment` | `(tmp_path: Path) -> None` | `<!-- Sources: ... -->` 는 근거 목록이지 주장이 아니다 — 이름이 없어도 경고하면 안 된다. |
| `test_verifier_matches_name_on_adjacent_line` | `(tmp_path: Path) -> None` | 산문이 줄바꿈되면 인용과 심볼 이름이 다른 줄에 있다 — 경고하면 안 된다. |
| `test_terms_db_extracts_modules_and_classes` | `() -> None` | codegraph.json 의 노드와 모듈이 용어 항목이 돼야 한다. 이웃은 간선 from/to 에서 온다. |
| `test_terms_db_means_is_never_empty` | `() -> None` | 정답 칸이 비면 Mode 1.5 가 출제할 수 없다. 최소한 기계가 아는 사실로 채운다. |
| `test_terms_db_is_deterministic` | `() -> None` | 같은 입력이면 같은 출력이어야 한다. LLM 혼선을 막는 것이 이 파일의 목적이다. |
| `test_first_party_by_namespace_allowlist` | `() -> None` | 허용목록에 있는 네임스페이스는 저장소 경로를 몰라도 1차다. |
| `test_first_party_by_declaration_path` | `(tmp_path: Path) -> None` | 네임스페이스가 없어도 저장소 안에서 **정의**됐으면 1차다 — app/ 이 이 경우다. |
| `test_first_party_rejects_forward_declaration` | `(tmp_path: Path) -> None` | 전방 선언은 정의가 아니다 — 이 검사가 없으면 외부 타입이 중요도 상위에 올라온다. |
| `test_first_party_rejects_use_site` | `(tmp_path: Path) -> None` | 멤버 선언 줄은 정의가 아니다 — cv::Mat3b img; 가 이 경우다. |
| `test_first_party_accepts_nested_type` | `(tmp_path: Path) -> None` | 중첩 타입은 이름 구분자가 ## 다. 벗기지 않으면 우리 enum 이 외부로 밀린다. |
| `test_first_party_never_accepts_std_even_inside_repo` | `() -> None` | clang-uml 은 std 타입의 위치로도 이 저장소의 첫 사용 지점을 준다 — 막지 않으면 1차가 된다. |
| `test_first_party_rejects_generated_files` | `() -> None` | Qt autogen 의 Ui::* 는 빌드 산출물이라 1차가 아니다. |
| `test_first_party_rejects_outside_repo` | `() -> None` | 저장소 밖에서 선언된 것은 1차가 아니다. |
| `test_first_party_without_repo_keeps_old_behavior` | `() -> None` | repo 를 안 주면 예전처럼 네임스페이스만 본다 — 기존 호출자가 안 깨진다. |
| `_doc` | `(name: str, kind: str, namespace: str, file: str, line: int, signature: str = '', doc: str = '') -> Symbol` | clang_doc.load_clang_doc 이 내는 꼴 하나. |
| `test_clang_doc_adds_function_nodes` | `(tmp_path: Path) -> None` | clang-uml 이 내지 않는 자유 함수가 clang-doc 쪽에서 노드로 들어온다. |
| `test_clang_doc_wins_on_where_for_a_shared_type` | `(tmp_path: Path) -> None` | 같은 타입이면 노드를 늘리지 않고 위치만 clang-doc 것으로 갈아 끼운다. |
| `test_clang_doc_does_not_add_edges` | `(tmp_path: Path) -> None` | clang-doc 은 관계를 분류하지 않는다. 간선 수가 늘면 안 된다. |
| `test_clang_doc_symbols_go_through_is_first_party` | `(tmp_path: Path) -> None` | clang-doc 심볼도 1차 판정을 그대로 탄다 — 우회하면 외부 타입이 샌다. |
| `test_clang_doc_carries_signature_and_author_comment` | `(tmp_path: Path) -> None` | clang-uml 이 못 주던 둘 — 시그니처와 저자 문서 주석이 노드에 실린다. |
| `test_uml_only_nodes_keep_their_shape` | `(tmp_path: Path) -> None` | 골든 보호 — clang-doc 을 안 주면 노드의 키 구성이 예전 그대로여야 한다. |
| `test_cli_accepts_clang_uml_and_clang_doc_together` | `() -> None` | --clang-doc 은 --clang-uml 과 **배타가 아니다**. 배타 그룹에 들어가면 합치기가 불가능해진다. |
| `test_cli_clang_doc_is_optional` | `() -> None` | 안 주면 None 이고 예전 동작 그대로다. |
| `test_py_kind_map_has_no_ownership` | `() -> None` | 파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같은 이유로 소유 kind 를 쓰지 않는다. |
| `test_py_r7_covers_builtin_scalars_and_literals` | `() -> None` | R7 — 원시 스칼라뿐 아니라 식 자리에 리터럴로 오는 None 과 ... 도 노드가 아니다. |
| `test_py_transparent_is_concrete_containers_only` | `() -> None` | R5 투과 목록은 구체 컨테이너와 typing 별칭까지다. |
| `test_py_external_group_folds_stdlib_into_one` | `() -> None` | R2 — 외부 하나 = 노드 하나. 표준 라이브러리는 C++ 의 "(STL) std" 와 같은 축으로 하나에 접는다. |
| `test_py_module_of_reuses_folder_tree` | `(path: str, expected: str) -> None` | Python 도 모듈 경계는 폴더 트리다 — 그래서 module_of() 를 **그대로 재사용**한다. |
| `test_py_expr_name_reads_name_and_dotted_attribute` | `() -> None` | 식 트리에서 '쓰인 그대로의 점 이름' 을 꺼낸다. 이름이 아닌 식이면 None 이다. |
| `test_py_resolve_prefers_import_table_then_same_module` | `() -> None` | 이름 해소 순서: import 표 -> 같은 모듈 -> 못 품(쓰인 그대로). |
| `_walk` | `(expr: 'N.GriffeExpr \| None') -> tuple[list[str], Counter[str]]` | py_walk_expr 를 픽스처 문맥으로 감싼다. (결과, stats) 를 돌려준다. |
| `test_py_r5_unwraps_builtin_generic` | `() -> None` | R5 — list[Node] 는 껍데기를 벗고 Node 로 내려간다. |
| `test_py_r5_unwraps_dict_and_drops_key_by_r7` | `() -> None` | dict[str, Node] — 속이 ExprTuple 이다. str 은 R7 로 죽고 Node 만 남는다. |
| `test_py_r5_unwraps_optional_and_pep604_union` | `() -> None` | Optional[Node] 와 Node \| None 은 같은 뜻이고 griffe 는 다른 모양으로 준다. |
| `test_py_r5_nests_two_levels_deep` | `() -> None` | list[dict[str, Node]] — 문자열로 쓴 주석도 griffe 가 트리로 파싱해 준다. |
| `test_py_r5_does_not_unwrap_abstract_interface` | `() -> None` | abc.Mapping[str, Node] — 인터페이스는 투과하지 않는다. Mapping 자신이 남는다. |
| `test_py_walk_drops_ellipsis_and_typing_plumbing` | `() -> None` | tuple[Node, ...] 의 "..." 도, Generic[T] 의 Generic 도 R7 로 죽는다. |
| `test_py_walk_drops_unresolvable_type_variable` | `() -> None` | 투과 컨테이너를 지나 도달한 타입변수 T 는 해소 실패로 죽는다 — 노드가 아니다. |
| `test_py_walk_stops_at_depth_limit` | `() -> None` | 무한 중첩을 만나도 죽지 않는다 — C# resolve() 의 depth 가드와 같은 자리. |
| `_pyfx_dump` | `(root: str) -> N.GriffeDump` | griffe 출력 모양 그대로의 최소 덤프. 두 모듈 · 두 클래스. |
| `test_python_nodes_are_classes_with_qualified_names` | `(tmp_path: Path) -> None` | 노드 이름은 완전 수식 점 이름이다 — griffe 가 짧은 이름만 주므로 순회하며 이어 붙인다. |
| `test_python_has_no_ownership_kinds` | `(tmp_path: Path) -> None` | 파이썬에는 값 멤버/포인터 멤버 구분이 없다 — C# 과 같이 소유 간선이 0이어야 한다. |
| `test_python_edge_kinds_and_labels` | `(tmp_path: Path) -> None` | 상속 = inheritance · 속성 주석 = association · 시그니처 = dependency. |
| `test_python_external_is_folded_and_marked` | `(tmp_path: Path) -> None` | R2/R6 — json.JSONEncoder 는 "(표준) stdlib" 하나로 접히고 constraint=False 를 단다. |
| `test_python_r4_no_edges_leave_the_external_island` | `(tmp_path: Path) -> None` | 간선은 1차 -> 외부 단방향만. 파이썬 갈래는 구조상 발생조차 하지 않는다. |
| `test_python_module_deps_exclude_external` | `(tmp_path: Path) -> None` | 모듈 의존은 1차 모듈끼리만 — __external__ 이 끼면 안 된다. |
| `test_cli_griffe_dump_is_a_third_source` | `() -> None` | 수집기 셋은 고르는 관계다 — 배타 그룹의 셋째로 들어간다. |
| `test_cli_griffe_dump_conflicts_with_other_sources` | `() -> None` | --clang-uml 과 함께 줄 수 없다. --clang-doc 과 달리 이건 합치는 관계가 아니다. |
| `_griffe_dump` | `(tmp_path: Path, files: dict[str, str], pkg: str) -> N.GriffeDump` | 픽스처를 tmp_path 에 쓰고 실제 griffe 로 덤프해 dict 로 돌려준다. |
| `test_golden_python_fixture_counts` | `(tmp_path: Path) -> None` | griffe 의 출력 모양이 바뀌면 여기가 먼저 깨진다 — 의도한 변경이면 기대값을 함께 고친다. |
| `test_golden_python_r5_recovered_first_party_through_containers` | `(tmp_path: Path) -> None` | R5 가 없으면 nodes/table/spare/later 네 속성이 통째로 사라진다 — 그게 안 일어나는지 본다. |
| `test_golden_python_external_nodes_have_no_location` | `(tmp_path: Path) -> None` | 외부 노드는 저장소에 소스가 없으므로 file/line 이 null 이고 L3 대상이 아니다. |
| `test_golden_python_ownership_edges_are_absent` | `(tmp_path: Path) -> None` | C# 과 같은 자리 — 파이썬은 모든 바인딩이 참조라 소유 kind 가 나올 수 없다. |
| `test_selfhost_python_smoke` | `() -> None` | 실제 저장소를 태워도 파이프라인이 죽지 않는지만 본다 — 불변식 검증이 아니다. |
| `test_pyfx_namespace_package_filepath_is_a_list` | `(tmp_path: Path) -> None` | 네임스페이스 패키지(= __init__.py 없음)는 filepath 가 디렉토리 목록(list)으로 온다. |

---

## `test_pycalls.py`

AST 호출 수집기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_write` | `(tmp: Path, files: dict[str, str]) -> None` |  |
| `test_flat_import_across_directories_is_resolved` | `(tmp_path: Path) -> None` | `from util import helper` 를 `pkga.util.helper` 로 푼다 — 패키지 접두가 없어도. |
| `test_builtin_and_external_calls_are_dropped` | `(tmp_path: Path) -> None` | 빌트인(`len`)과 저장소 밖(`json.dumps`)은 간선이 아니다 — 양끝이 다 우리 것이어야 한다. |
| `test_methods_and_classes_become_symbols` | `(tmp_path: Path) -> None` | 클래스·메서드도 심볼이고, 메서드에서 나가는 호출도 잡는다. |
| `test_same_stem_in_two_directories_is_dropped_not_guessed` | `(tmp_path: Path) -> None` | 파일 이름이 겹치면 **버린다.** 잘못 이은 간선은 없는 간선보다 나쁘다. |
| `test_signature_is_captured` | `(tmp_path: Path) -> None` | 시그니처를 원문 주석 그대로 살린다 — 위키가 읽는 자리다. |
| `test_syntax_error_file_is_skipped_not_fatal` | `(tmp_path: Path) -> None` | 문법이 깨진 파일 하나가 수집 전체를 죽이지 않는다. |
| `test_merge_adds_function_nodes_and_call_edges` | `(tmp_path: Path) -> None` | griffe 가 못 낸 함수 노드가 들어오고, 호출이 dependency 간선이 된다. |
| `test_merge_is_opt_in` | `(tmp_path: Path) -> None` | calls 를 안 주면 옛 동작 그대로 — 노드도 간선도 늘지 않는다. |
| `test_merge_never_makes_ownership_kinds` | `(tmp_path: Path) -> None` | 호출은 dependency 다. 부른다고 갖는 것이 아니므로 소유 kind 로 올리지 않는다. |
| `test_selfhost_smoke` | `() -> None` | 이 저장소를 실제로 훑는다. 수치는 주장하지 않고 '판이 커졌다' 만 본다. |
| `test_cli_runs_end_to_end` | `(tmp_path: Path) -> None` | 명령줄로도 돌고 JSON 을 낸다. |
| `test_signature_covers_star_and_kwargs` | `(tmp_path: Path) -> None` | 가변·키워드 전용·`**kw` 를 빠뜨리지 않는다. 키워드 전용 앞의 `*` 도 살린다. |

---

## `test_survey_plan.py`

층 계획기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_cg` | `(nodes: list[tuple[str, str]], edges: list[tuple[str, str]]) -> CodeGraph` |  |
| `test_층은_의존_대상이_없는_것부터` | `()` | a -> b -> c 면 c 가 층0, b 가 층1, a 가 층2 다. |
| `test_고립_노드는_층0` | `()` | 간선이 하나도 없어도 의존 대상이 없으므로 층0 이다. |
| `test_순환은_한_덩어리로_접힌다` | `()` | a <-> b 는 위상 깊이가 정의되지 않는다. 같은 층으로 접고 표시한다. |
| `test_out_deg_가_아니라_위상_깊이다` | `()` | a 는 out_deg 1, d 는 out_deg 2 지만 둘 다 층2 다 — out_deg 로 나누면 순서가 틀린다. |
| `test_같은_파일은_한_배치에` | `()` | 파일이 쪼개지면 두 세션이 같은 파일을 각각 통독하게 된다. |
| `test_큰_파일은_초과를_허용한다` | `()` | 심볼 5개짜리 파일은 target 3 이어도 쪼개지 않는다. |
| `test_층_안에서_한_파일은_한_배치에만_있다` | `()` | lock 없는 설계의 전제다 — 깨지면 두 세션이 같은 파일을 동시에 연다. |
| `test_배치의_파일_목록에_빈_이름이_없다` | `()` | file 이 없는 노드는 빈 문자열로 묶인다. 그대로 두면 프롬프트가 |
| `test_결정론` | `()` | 같은 입력이면 같은 출력. 순서가 흔들리면 계획이 재현되지 않는다. |
| `test_external_은_제외` | `()` | external 노드는 계획에 세지 않는다. |
| `test_마지막은_비노드_층` | `()` | file · module · artifact · key · concept 는 층 축이 없어 맨 뒤 별도 층이다. |
| `test_배치는_자기_심볼의_의존_대상을_들고_있다` | `()` | 배치 프롬프트가 아래층 레코드를 발췌하려면 depends_on 이 계획 안에 있어야 한다. |
| `test_증분은_층_번호를_보존한다` | `()` | warmup 이 준 파일만 남기되 층은 **전체 그래프 기준**이어야 한다. |
| `test_이_저장소_실측` | `()` | 이 저장소의 실제 지도로 층 분포를 못박는다 — 코드가 바뀌면 기대값을 함께 고친다. |
| `test_간선은_from_이_의존하는_쪽이다` | `()` | `{from: A, to: B}` 는 "A 가 B 에 의존" 이다 — 뒤집어 읽으면 정렬이 정반대가 된다. |
| `test_진입점은_맨_위층이다` | `()` | in_deg 0 은 아무도 안 쓰는 것 = 진입점이다. 거기서 시작하면 top-down 이 된다. |

---

## `test_terms_db.py`

terms-db 우선 파이프라인의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_graph` | `() -> CodeGraph` | 합성 codegraph — 클래스 2, 외부 1, 간선 2, 모듈 1. normalize.py 출력 키 그대로. |
| `test_build_terms_keeps_id_and_typed_uses` | `()` | codegraph 의 id 와 종류 붙은 간선이 용어 레코드에 그대로 실린다. |
| `_triples` | `(g: CodeGraph) -> set[tuple[str, str, str]]` |  |
| `test_project_round_trips_synthetic_graph` | `()` | 투영이 노드 · 간선 · 모듈을 그대로 되돌린다. |
| `test_project_drops_terms_that_are_not_code` | `()` | 코드가 아닌 용어와 그리로 가는 간선은 지도에 싣지 않는다. |
| `test_project_golden_is_superset_of_real_codegraph` | `(repo: str, lang: str)` | 실제 산출물로 확인한다 — codegraph 의 노드 · 간선 · 모듈이 투영에 전부 있다. |
| `_repo` | `(tmp_path: Path) -> str` | 가짜 저장소 — codegraph/x.py 8줄. |
| `_reading` | `() -> Terms` |  |
| `test_check_passes_on_grounded_reading` | `(tmp_path: Path)` | 근거가 맞는 reading 레코드는 아무 지적도 나오지 않는다. |
| `test_check_l1_missing_file_is_failure` | `(tmp_path: Path)` | 없는 파일을 가리키면 L1 실패다. |
| `test_check_l2_line_past_eof_is_failure` | `(tmp_path: Path)` | 파일 끝을 넘는 줄을 가리키면 L2 실패다. |
| `test_check_l3_name_absent_is_unfounded_not_failure` | `(tmp_path: Path)` | 근처에 이름이 없으면 실패가 아니라 "근거 없음" 이다. |
| `test_check_reading_record_requires_where` | `(tmp_path: Path)` | reading 레코드에 where 가 비면 실패다. |
| `test_check_flags_unknown_uses_target` | `(tmp_path: Path)` | 사전에 없는 용어를 가리키는 uses 는 실패다. |
| `test_check_skips_citations_of_codegraph_records` | `(tmp_path: Path)` | 정적 도구가 낸 레코드의 위치는 여기서 재판정하지 않는다 — verify_citations.py 의 영역. |
| `test_merge_reading_overrides_means_but_not_structure` | `()` | 뜻은 reading 이 덮고 구조(id · kind · module · where)는 codegraph 가 이긴다. |
| `test_merge_adds_new_reading_records_and_links_neighbors` | `()` | codegraph 에 없던 reading 레코드가 들어오고 이웃이 양쪽에 걸린다. |
| `test_merge_is_deterministic` | `()` | 같은 입력이면 같은 출력이다. |
| `_run` | `(args: list[str]) -> subprocess.CompletedProcess[str]` |  |
| `test_cli_reading_only_writes_db_and_projection` | `(tmp_path: Path)` | reading 만 줘도 terms-db.json 과 투영 codegraph.json 을 낸다. |
| `test_cli_exits_1_when_a_citation_fails` | `(tmp_path: Path)` | 인용이 하나라도 실패하면 종료 코드가 1 이다. |
| `test_cli_still_accepts_codegraph_positional` | `(tmp_path: Path)` | 기존 호출 꼴 `terms_db.py <codegraph.json> --repo` 가 그대로 돈다. |
| `test_cli_needs_at_least_one_input` | `(tmp_path: Path)` | 입력을 하나도 안 주면 사용법 오류로 끝난다. |
| `test_check_does_not_judge_edge_kinds_that_came_from_codegraph` | `(tmp_path: Path)` | 정적 도구의 간선 어휘는 재판정하지 않는다 — 여섯 어휘 제한은 LLM 이 쓴 간선에만 산다. |

---

## `test_warmup.py`

증분 무효화 판정의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `_git` | `(repo: str, *args) -> None` |  |
| `_repo` | `(tmp_path: Path, files: dict[str, str]) -> str` | 진짜 git 저장소 하나를 만들고 files 를 커밋한다. files: {상대경로: 본문} |
| `test_file_hash_is_content_not_commit` | `(tmp_path: Path)` | 커밋 여부와 무관하다 — 바이트 그대로의 sha256 이다. |
| `test_file_hash_returns_none_for_missing` | `(tmp_path: Path)` | 없는 파일이면 터지지 않고 None 이다. |
| `test_unchanged_file_is_valid` | `(tmp_path: Path)` | 안 바뀐 파일은 유효다. |
| `test_first_run_is_all_reread` | `(tmp_path: Path)` | 매니페스트가 없으면 전부 재읽기다 — 첫 실행의 기준선. |
| `test_uncommitted_change_is_stale` | `(tmp_path: Path)` | 커밋하지 않은 작업 트리 변경도 낡음이다 — blob SHA 로 판정하면 이것을 놓친다. |
| `test_missing_file_is_deleted` | `(tmp_path: Path)` | 이번 훑기에 안 보인 항목은 삭제됨이다. |
| `test_decl_hash_ignores_line_and_doc` | `(tmp_path: Path)` | 줄 번호와 문서 주석이 달라도 선언 목록이 같으면 같은 해시다. |
| `test_decl_hash_changes_when_declaration_added` | `()` | 선언이 하나 늘면 선언 해시가 달라진다. |
| `test_comment_only_change_needs_no_llm` | `(tmp_path: Path)` | 선언이 같으면 위치만 — LLM 을 부르지 않는다. |
| `test_declaration_change_forces_reread` | `(tmp_path: Path)` | 선언이 달라지면 그 파일만 재읽기다. |
| `test_mtime_gate_skips_hashing` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` | mtime 과 크기가 같으면 해싱하지 않는다 — stat 이 훨씬 싸다. |
| `test_seen_is_refreshed_every_run` | `(tmp_path: Path)` | `seen` 은 매 실행마다 갱신된다 — 이번에 봤다는 표시다. |
| `test_load_missing_cache_is_empty` | `(tmp_path: Path)` | 매니페스트가 없으면 빈 사전이다. |
| `test_save_then_load_roundtrip` | `(tmp_path: Path)` | 없는 중간 디렉토리를 만들어 저장하고 그대로 다시 읽는다. |
| `test_blast_radius_spreads_both_ways` | `(tmp_path: Path)` | 간선을 양방향으로 탄다 — B 가 바뀌면 B 를 쓰는 A 의 서술도 틀려질 수 있다. |
| `test_blast_radius_skips_nodes_without_file` | `(tmp_path: Path)` | 외부 노드는 file 이 null 이다 — 간선에서 빼야 한다. |

---

## `test_xmldoc.py`

주석 블록 주입기의 회귀 시험.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| `marker` | `(tid: str, prefix: str = '#') -> str` |  |
| `fake_repo` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, terms: Terms) -> None` | tmp_path 를 저장소 뿌리로 삼는다. 상수 세 개만 갈아 끼우면 된다. |
| `test_relocate_reads_markers_not_arithmetic` | `()` | 블록이 앞에 몇 개 있든 각 용어의 자리는 '그 마커 줄 + 3' 이다. |
| `test_relocate_skips_comment_chunk_below_block` | `()` | 블록은 원래 있던 주석 덩어리보다 위에 놓인다. 선언은 그 덩어리 아래다. |
| `test_block_is_three_lines_with_uses` | `()` | 블록은 마커 · 뜻 · 의존 세 줄이고 셋째 줄에 쓰는 것과 쓰이는 곳이 든다. |
| `test_block_says_none_when_no_uses` | `()` | 의존이 없어도 "없음" 으로 세 줄을 채운다. |
| `test_block_caps_at_five_and_counts_the_rest` | `()` | 의존은 다섯 개까지 적고 나머지는 개수로 접는다. |
| `test_strip_removes_whole_block` | `()` | 블록은 통째로 걷힌다. |
| `test_strip_removes_legacy_two_line_block` | `()` | 이행기 — 옛 두 줄 블록도 남기지 않는다. |
| `test_inject_is_idempotent` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` | 두 번 돌린 결과가 한 번과 같다 — 덧붙지 않고 갈린다. |
| `test_inject_finds_anchor_from_marker_even_if_where_is_stale` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` | json 의 where 가 낡아도 파일에 마커가 있으면 그 자리를 믿는다. |
| `test_check_flags_where_mismatch` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str])` | 어긋난 where 를 찾아 이름과 함께 알리고 1 로 끝난다. |
| `test_inject_carries_unmarked_where_and_uses` | `(tmp_path: Path, monkeypatch: pytest.MonkeyPatch)` | 마커를 못 박는 용어의 where 와 uses[].where 도 밀린 줄만큼 따라 내려간다. |

---

## `verify_citations.py`

문서의 file:line 인용을 기계로 판정한다 (L1/L2/L3).

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Node`** | *class* |  |
| **`CodeGraph`** | *class* |  |
| **`_ClangMember`** | *class* |  |
| **`_ClangElement`** | *class* |  |
| **`_RoslynType`** | *class* |  |
| **`_DetailFile`** | *class* |  |
| `short` | `(name: str) -> str` | 이름 대조용 마지막 조각. `##` · `::` · `.` 로 잘라 마지막만, `<` 뒤는 버린다 (F-2). |
| `build_index` | `(codegraph: str) -> tuple[CodeGraph, Index, Index]` | codegraph -> (노드 색인, 간선 색인). 둘 다 (file,line) 로 찾는다. |
| `load_detail_index` | `(path: str) -> Index` | 살 파일의 멤버·메서드 선언 줄 색인. clang-uml(elements)과 roslyn-dump(types) 양쪽을 안다. |
| `main` | `() -> int` |  |

---

## `warmup.py`

전수조사를 매번 전량 다시 하지 않게 하는 파일별 캐시와 무효화.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Entry`** | *class* | 파일 하나 몫의 기록. `file_hash` 는 못 읽은 파일이면 None 이다. |
| `file_hash` | `(path: str) -> str \| None` | 바이트 그대로의 sha256. 커밋 여부와 무관하다. |
| `decl_hash` | `(entry: declmap.FileDecls \| None) -> str \| None` | 선언 목록의 해시. `declmap.scan` 의 **한 파일 몫**을 받는다. |
| `load` | `(cache_path: str) -> Manifest` | 매니페스트를 읽는다. 없거나 깨졌으면 빈 것으로 친다 — 그러면 전량 재읽기다. |
| `save` | `(cache_path: str, entries: Manifest) -> Manifest` | 매니페스트를 쓴다. 상위 폴더가 없으면 만든다. |
| `status` | `(cache_path: str, repo: str, files: list[str], decls: dict[str, declmap.FileDecls] \| None = None) -> tuple[Verdicts, Manifest]` | 판정 네 갈래와 갱신된 매니페스트를 함께 낸다. **쓰지는 않는다** — 쓰기는 `save` 다. |
| `blast_radius` | `(codegraph: str, changed_files: list[str], hops: int = 1) -> list[str]` | 바뀐 파일이 영향을 주는 파일 집합. |
| `main` | `() -> int` |  |

---

## `xmldoc.py`

주석 본문을 .xml 한 곳에 모으고 코드에는 레퍼런스만 남긴다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Use`** | *class* | `uses[]` 한 칸 — 이 용어가 무엇을 쓰는가. |
| **`Term`** | *class* | 용어 하나. 열쇠 이름은 json 의 것 그대로다. |
| `prefix_for` | `(path: str) -> str` |  |
| `shebang_is_python` | `(path: str) -> bool` | 확장자 없는 파일의 첫 줄 셔뱅이 파이썬을 가리키는지 본다. |
| `split_where` | `(where: str \| None) -> tuple[str \| None, int \| None]` | `file:line` -> (file, line). 위치가 없으면 (None, None). |
| `anchor_name` | `(term_id: str) -> str` | 앵커 줄에서 찾을 이름. 점 표기는 마지막 마디, 배열 키는 [] 를 뗀다. |
| `emit_xml` | `(terms: Terms) -> str` |  |
| `is_commentish` | `(line: str) -> bool` |  |
| `used_by_index` | `(terms: Terms) -> UsedBy` | {용어: 그것을 쓰는 용어들}. uses 를 거꾸로 뒤집은 것뿐이다. |
| `name_list` | `(names: list[str]) -> str` | 이름들을 한 줄로. 다섯 개까지 적고 남는 건 (+n) 으로 센다. |
| `uses_line` | `(tid: str, terms: Terms, used_by: UsedBy) -> str` |  |
| `block_lines` | `(tids: list[str], terms: Terms, prefix: str, indent: str, used_by: UsedBy \| None = None) -> list[str]` | 한 앵커에 붙일 레퍼런스 블록. 같은 줄에 여러 용어가 걸리면 함께 낸다. |
| `file_anchor` | `(lines: list[str]) -> int` | kind=file 의 삽입 지점(0-based). 셔뱅이 있으면 그 아래. |
| `in_py_string` | `(path: str, lines: list[str], idx: int) -> bool` | 파이썬 파일에서 idx 줄이 삼중 따옴표 문자열 안인가. 홀짝만 센다 — 안전판이다. |
| `scan_top` | `(lines: list[str], anchor_idx: int) -> int` | 선언 위에 붙어 있는 주석 덩어리의 첫 줄. 빈 줄을 만나면 멈춘다. |
| `block_extent` | `(lines: list[str], i: int) -> tuple[int, int]` | lines[i] 가 include 줄일 때 (용어 수, 블록이 차지한 줄 수). |
| `relocate` | `(lines: list[str]) -> dict[str, int]` | 파일 본문에 박힌 마커를 읽어 {용어: 선언 줄(1-based)} 을 만든다. |
| `strip_blocks` | `(lines: list[str]) -> tuple[list[str], list[int]]` | 이미 박힌 레퍼런스 블록을 전부 걷어낸다. (깨끗한 줄들, 각 줄 앞에서 지워진 줄 수). |
| `plan_file` | `(path: str, tids: list[str], terms: Terms, src: str) -> tuple[str, dict[str, int], dict[int, int]]` | 한 파일에 블록을 넣는다. 반환 (새 본문, {용어: 새 줄번호}, {옛 줄번호: 새 줄번호}). |
| `collect_targets` | `(terms: Terms, all_kinds: bool = False) -> tuple[dict[str, list[str]], list[tuple[str, str]]]` | {파일: [용어…]} 와 XML 에만 남길 용어들. where 의 파일 이름만 쓴다. |
| `carry_lines` | `(terms: Terms, path: str, line_map: dict[int, int], skip: set[str]) -> int` | 블록 때문에 밀린 줄을 따라 옮긴다. 마커가 있는 용어(skip)는 이미 제자리다. |
| `run_inject` | `(dry: bool, all_kinds: bool = False) -> None` |  |
| `run_check` | `() -> int` | 코드의 마커와 json 의 where 가 같은 자리를 가리키는지만 본다. |

