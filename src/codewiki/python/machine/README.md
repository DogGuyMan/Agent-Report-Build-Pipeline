# `src/codewiki/python/machine/` — 정적 수집 · 인용 검증 · 측정. 산문을 쓰지 않고 판정하지 않는다.

> 이 문서는 `tools/gen_readme.py` 가 소스에서 생성한다. **손으로 고치지 마라** —
> 다음 생성에 덮인다. 갱신: `.venv/bin/python tools/gen_readme.py <이 폴더>` (아홉 폴더 전부는 루트 `CLAUDE.md` 의 README 표류 게이트)

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
| [`manifest.py`](manifest.py) | Mode 1 산출물을 봉인한다 — `docs/codegraph/` 에 terms-db.json 사본과 manifest.json 을 낸다. |
| [`normalize.py`](normalize.py) | 언어별 정적 분석 산출물을 codegraph.json(스키마 v2)으로 바꾼다. |
| [`pycalls.py`](pycalls.py) | 파이썬 소스에서 심볼과 호출 관계를 뽑는 수집기. |
| [`reading_types.py`](reading_types.py) | 전수조사 원본 `terms-reading.json` 의 모양. `does` 와 `confidence` 만 선택이고 나머지는 모든 레코드에 있다. |
| [`reverse_refs.py`](reverse_refs.py) | 1차 심볼 전수 역참조를 뽑는다 (E6 + 전수 확정). |
| [`survey_plan.py`](survey_plan.py) | 전수조사 배치 계획. |
| [`terms_db.py`](terms_db.py) | 코드베이스 용어 전수 수집. |
| [`verify_citations.py`](verify_citations.py) | 문서의 file:line 인용을 기계로 판정한다 (L1/L2/L3). |
| [`verify_graph.py`](verify_graph.py) | codegraph.json 을 읽기 · 꼴 · 정합 · 근거 네 층으로 검사해 결함을 전부 모은다. |
| [`warmup.py`](warmup.py) | 전수조사를 매번 전량 다시 하지 않게 하는 파일별 캐시와 무효화. |

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

## `manifest.py`

Mode 1 산출물을 봉인한다 — `docs/codegraph/` 에 terms-db.json 사본과 manifest.json 을 낸다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`ArtifactEntry`** | *class* | 봉인된 산출물 파일 하나. `path` 는 대상 저장소 뿌리 기준. |
| **`SupersededBy`** | *class* | 이 봉인 뒤의 Mode 1 실행이 실패했다는 표식. 봉인 자체는 그대로다 — 읽는 쪽이 경고로 본다. |
| **`ArtifactManifest`** | *class* | `docs/codegraph/manifest.json` 의 꼴. `inputs` 는 봉인 시점 소스 파일마다의 git blob id 다. |
| **`LangPick`** | *class* | `lang-select.json` 에서 봉인이 읽는 칸. 언어를 못 골랐으면 None 이다. |
| **`WikiState`** | *class* | `write-wiki` 의 상태. `pages` 는 장마다 마지막으로 쓴 해시, `sources` 는 낡음 판정의 기준, `snapshot_sha256` 은 따라잡은 지문이다. |
| `git` | `(repo: str, *args) -> str` | 대상 저장소에서 git 을 부르고 stdout 을 낸다. 실패하면 CalledProcessError 다. |
| `sha256_of` | `(path: str) -> str` | 파일 바이트 그대로의 sha256. |
| `blob_ids` | `(repo: str, rels: Sequence[str]) -> dict[str, str]` | 작업 트리 내용 그대로의 blob id. `git hash-object` 는 인자 순서대로 한 줄씩 낸다. |
| `missing` | `(repo: str, sources: Sequence[str]) -> list[str]` | git 이 추적하는데 작업 트리에 없는 소스. 지운 것을 아직 커밋하지 않은 상태다. |
| `unsurveyed` | `(repo: str, sources: Sequence[str], snapshot: str) -> list[str]` | 지난 전수조사의 지문과 다른 소스. 지문에 없는 새 파일도 넣는다. |
| `wiki_caught_up` | `(raw: str) -> bool` | `wiki-state.json` 이 지금 `snapshot.json` 의 지문을 가리키는가. 둘 중 하나라도 읽지 못하거나 따라잡은 적이 없으면 아니다. |
| `entries` | `(repo: str, kind: str) -> list[ArtifactEntry]` | 봉인한 종류의 파일 목록과 sha256. terms-db 는 `docs/codegraph/` 의 사본, wiki 는 `docs/wiki/*.md` 다. |
| `refuse` | `(head: str, rels: Sequence[str]) -> int` | 봉인을 거부한 이유를 stderr 에 적고 종료 코드 3 을 낸다. 파일은 스무 개까지 보인다. |
| `main` | `(argv: Sequence[str] \| None = None) -> int` | `seal` 명령. 거부 조건을 모두 지나야 `docs/codegraph/` 에 쓴다. |

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
| `py_abstraction` | `(cls: GriffeObject) -> Literal['interface', 'abstract'] \| None` | 클래스가 인터페이스인가 추상 클래스인가. 구체면 None. |
| `py_resolve` | `(name: str, mod_path: str, imports: dict[str, str], first_party: set[str]) -> str` | 이름 해소 순서: 모듈의 import 표 -> 같은 모듈의 1차 클래스 -> 못 품. |
| `py_walk_expr` | `(expr: GriffeExpr \| None, mod_path: str, imports: dict[str, str], first_party: set[str], stats: Counter[str], depth: int = 0) -> list[str]` | R5 — 컨테이너 껍데기를 벗기고 안의 타입 이름들을 모아 돌려준다. |
| `normalize_python` | `(dump: GriffeDump, repo: str, source_tool: str, calls: PyCallsDump \| None = None) -> tuple[CodeGraph, Counter[str]]` | griffe dump(JSON) -> codegraph.json. C++/C# 과 같은 모양(노드 -> 간선 -> _assemble)이다. |
| `merge_py_calls` | `(nodes: dict[str, Node], node_id: dict[str, str], edges: dict[tuple[str, str, str], Edge], calls: PyCallsDump, stats: Counter[str]) -> None` | `pycalls.py` 가 뽑은 함수·메서드와 호출을 합친다. |
| `write_json_atomic` | `(path: str, obj: object) -> None` | JSON 을 같은 폴더의 임시 파일에 쓰고 `os.replace` 로 바꿔 끼운다. 도중에 끊겨도 옛 파일이 그대로 남는다. |
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
| `import_table` | `(tree: ast.Module, name_to_module: dict[str, str]) -> dict[str, str]` | `from mode1.context import RunContext` -> {"RunContext": "codewiki.python.runner.mode1.context.RunContext"}. |
| `scan_module` | `(tree: ast.Module, mod: str, rel: str, name_to_module: dict[str, str]) -> tuple[list[PySymbol], list[tuple[str, str, int]]]` | 한 모듈의 (심볼, 미해석 호출) 을 낸다. 호출의 대상은 아직 쓰인 그대로다. |
| `tracked_paths` | `(repo: str) -> set[str] \| None` | git 이 아는 파일의 저장소 상대경로 집합. 저장소가 아니거나 git 이 없으면 None 이다. |
| `collect` | `(repo: str, roots: list[str]) -> PyCallsDump` | `roots` 아래 `*.py` 를 읽어 심볼과 해석된 호출을 낸다. |
| `main` | `() -> None` |  |

---

## `reading_types.py`

전수조사 원본 `terms-reading.json` 의 모양. `does` 와 `confidence` 만 선택이고 나머지는 모든 레코드에 있다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Use`** | *class* | `uses[]` 한 칸 — 이 용어가 무엇을 쓰는가. |
| **`Term`** | *class* | 용어 하나. 열쇠 이름은 json 의 것 그대로다. |

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
| **`FileWeight`** | *class* | 파일 하나의 우선순위 재료와 결과. `out`·`into` 는 다른 파일과 오가는 간선 수. |
| `is_public` | `(name: str) -> bool` | 마지막 마디가 `_` 로 시작하지 않으면 공개. 던더(`__init__`)도 비공개로 친다. |
| `file_weights` | `(cg: CodeGraph) -> list[FileWeight]` | 파일마다 `(1 − out/out_max) + into/into_max + 추상점수/추상점수_max`. 큰 순, 같으면 이름순. |
| `weights_csv` | `(rows: Iterable[FileWeight]) -> str` | `file-priority.csv` 본문. 원값을 함께 적어 수식을 바꿔도 다시 세지 않는다. |
| `plan_by_file` | `(cg: CodeGraph) -> SurveyPlan` | 코드 지도 -> 파일 하나가 배치 하나인 계획. 층은 하나(0)이고 배치 순서가 곧 우선순위다. |
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

## `verify_graph.py`

codegraph.json 을 읽기 · 꼴 · 정합 · 근거 네 층으로 검사해 결함을 전부 모은다.

| 심볼 | 시그니처 | 하는 일 |
|---|---|---|
| **`Fault`** | *class* | 결함 하나. `at` 은 JSON 경로(`$.nodes[3].kind`)다. |
| **`FaultsDoc`** | *class* | `graph-faults.json` — 결함이 있을 때만 있다. |
| **`PassedDoc`** | *class* | `graph-verified.json` — 검사를 지난 지도의 기록. `codegraph_sha256` 이 그 지도 한 벌에만 묶는다. |
| `fault` | `(code: str, at: str, detail: str) -> Fault` | 결함 하나를 만든다. 표에 없는 코드는 `KeyError` 다. |
| `read_graph` | `(path: str) -> tuple[object, str, list[Fault]]` | V0 읽기 — 파일을 열어 JSON 으로 푼다. (문서, 바이트의 sha256, 결함) 을 낸다. 못 열거나 못 풀면 문서는 `None` 이다. |

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

