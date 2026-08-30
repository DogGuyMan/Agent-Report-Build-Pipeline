# RESUME — Python strict 전환 · 수집기 확장 · 자기 검토 파이프라인

> **이 문서 하나로 이어받을 수 있어야 한다.** 다른 문서를 먼저 읽지 않아도 되도록 핵심은 여기 인라인이다.
> 작성 2026-08-30. 작성 시점에 **다시 측정한 값만** 적었다.

## TL;DR — 지금 어디이고 다음 한 걸음은 무엇인가

Python 쪽을 pyright strict 0 으로 만들었고(5,409 → 0), `codegraph.json` 수집기에 **호출 관계**를
더했다(노드 2 → 613, 간선 0 → 840). 지금은 **코드 주석에서 설계 서사를 걷어내는 작업**이 돌고 있다.

**A-1 ~ A-3 완료. 그리고 Mode 1 이 이 저장소에서 처음으로 돈다.**

`lang-select` 단계를 신설해 Mode 1 이 열 단계가 됐고, `prep` 에 Python 갈래를 배선했다.
그 과정에서 **세 실행기가 전부 삭제된 `scripts/` 를 가리키던 것**을 찾아 고쳤다 —
시험이 경로 문자열만 대조해서 초록인 채로 깨져 있었다.

**바로 다음 한 걸음:** §5 의 **A-6(Mode 1 → 1.5 → 2 자기 검토)**. 이제 막는 것이 없다.

---

## 1. 다시 잰 현재 상태

```
브랜치      main
최신 커밋   671af75 [chore] : PR 서식 - 검증 명령과 문서 동기화 체크리스트
            456c5f2 [docs] : docs - 보관소 선언, 첨부 없이 인계 문서를 열지 않는다
            2605e24 [docs] : 축 분리를 나침반, 아키텍처, 모듈 문서에 반영
```

**이 세션의 작업은 전부 미커밋이다.** 이 저장소는 사용자가 명시적으로 요청할 때만 커밋한다.

| 검증 | 값 | 명령 |
|---|---|---|
| pytest | **352 통과 · 19 건너뜀** | `.venv/bin/python -m pytest machine/ runner/ tools/ -q` |
| pytest (골든 포함) | **367 통과 · 4 건너뜀** | 아래 §6 의 환경변수와 함께 |
| pyright strict | **0 errors** | `npm run typecheck:py` |
| npm test | **178 통과** | `npm test` |
| tsc | 통과 | `npm run typecheck` |
| xmldoc check | **문제 0건** (292건 확인) | `.venv/bin/python machine/xmldoc.py check` |
| 인용 검사 | 27 통과 | `node --test test/docs-citations.test.mjs` |

**A-1(`xmldoc inject`)은 완료됐다.** 148건 → 0건. `--dry-run` 이 "고칠 파일 0개" 로 확인했듯
소스는 한 파일도 안 바뀌었고 `terms-reading.json`/`comments.xml` 의 `where` 148건만 갱신됐다.

### 새로 생긴 파일 (전부 미커밋)

| 파일 | 무엇 |
|---|---|
| `pyrightconfig.json` | strict 게이트 설정. `venvPath`·`extraPaths` 가 급소다(§6) |
| `machine/codegraph_types.py` | `codegraph.json` 계약 한 곳. `Node`·`Edge`·`Module`·`CodeGraph`·`EdgeKind` |
| `machine/pycalls.py` | AST 호출 수집기. griffe 가 못 내는 함수·호출을 낸다 |
| `machine/test_pycalls.py` | 위의 회귀 시험 13개 |
| `machine/test_external_contracts.py` | **바깥 도구 계약 시험 6건**(A-3). griffe·Graphviz·networkx·declmap |
| `tools/gen_readme.py` | 소스에서 디렉토리별 README 를 생성. `--check` 로 드리프트 판정 |
| `tools/test_gen_readme.py` | 위의 드리프트 게이트 4건 |
| `machine/README.md` · `runner/` · `viz/` · `tools/` | **생성물. 손으로 고치지 마라** |
| `machine/lang_select.py` | **언어 판별.** 모형의 제안을 결정론 검사로 거른다 |
| `machine/test_lang_select.py` | 위의 회귀 시험 9건 |
| `docs/superpowers/plans/2026-08-30-griffe-python-collector.md` | Python 수집기 실행 계획(완료됨) |
| `docs/superpowers/specs/griffe-python-collector/` | 그 계획의 Mode 2 검토 대시보드 |

---

## 2. 확정된 결정 — 다시 논쟁하지 말 것

사용자가 이번 세션에서 명시적으로 정한 것들이다.

| # | 결정 | 근거 |
|---|---|---|
| D1 | **R5(컨테이너 투과)를 구현한다** | 인계 문서의 제외 근거("griffe 가 타입힌트를 문자열로 준다")가 사실이 아니었다. griffe 2.2.0 은 구조화된 식 트리를 준다 |
| D2 | 골든 시험은 **합성 픽스처 + 빈약한 자기호스팅** | `machine/` 에 클래스가 거의 없어 자기호스팅만으로는 빈 그래프를 검증하게 된다 |
| D3 | **전면 strict** — 다른 모듈 확장을 막는 울타리 | 사용자 지시 |
| D4 | `machine/codegraph_types.py` 신설 | 소비자 다섯이 같은 스키마를 각자 적었고 이미 어긋나 있었다 |
| D5 | `_hms`→`hms`, `_Heartbeat`→`Heartbeat` 개명 (`comments.xml` 까지) | 밑줄은 모듈 전용인데 실제로는 세 mode 가 공유하는 API |
| D6 | `xmldoc inject` 는 **전부 끝난 뒤 한 번** | 중간에 여러 번 돌리면 그때마다 다시 밀려 낭비 |
| D7 | **의존 추적은 수집기 확장으로. 27개 파일은 안 바꾼다** | 파일명 클래스 래핑을 해도 griffe 는 호출을 안 내므로 목표를 달성하지 못한다. AST 는 코드 무변경으로 달성한다 |
| D8 | **코드 주석은 현 상황만.** 설계 서사·번복 기록·날짜·확신도 표기를 코드에서 뺀다 | 사용자 지시. 규약을 `CLAUDE.md` 의 "코드 주석 — 현 상황만 적는다" 절에 박아 뒀다 |

### D8 에 붙은 단서 — 반드시 지킬 것

**"형식·동작 사실"은 남긴다.** 지우면 다음 사람이 버그를 만든다. 날짜와 수치만 뺀다.

```
남긴다:  clang-doc 의 Namespace 는 안쪽부터 온다. 뒤집어야 SJH::Core::Panorama 가 된다.
지운다:  🔵 2026-08-29 QtVisionEdit 실측 — record 참조 64개가 전량 Location 없음이었다.
```

---

## 3. 이 세션이 실제로 한 일

### 3-1. pyright strict 전환 (5,409 → 0)

`machine/` 21 + `runner/` 6 + `viz/` 3 + `tools/` 1 생산 파일과 시험 12파일 전부.
**동작 보존은 "테스트 통과" 가 아니라 "산출물 대조" 로 증명했다:**

- `normalize.py` — 네 갈래 전부 실제 골든 저장소로 바이트 대조
  (C++ 195노드/419간선 · C+++clang-doc 95/53 · C# 231/540 · Python 59/107)
- `facts.py` · `terms_db.py` · `viz/render_*` · `demermaid` — 산출물 바이트 동일
- `run_mode1.py` — 측정 함수 8종을 값과 **각 칸의 파이썬 타입까지** 대조

우회 장치는 최소다: `# type: ignore` **0건**, `pyright: ignore` 소수(전부 근거 주석 있음).

### 3-2. 진짜 버그 하나

`machine/reverse_refs.py` — `shutil.which()` 를 쓰는데 `import shutil` 이 없었다.
CLI 로 부르면 `main()` 첫 줄에서 항상 `NameError`. 시험이 그 경로를 안 타서 여태 안 잡혔다. 고쳤다.

### 3-3. 수집기 확장 — `pycalls.py`

griffe 는 시그니처 추출기라 **호출 관계를 아예 내지 않는다.** 그래서 함수 위주 저장소에서
노드가 거의 없고 간선이 0 이 된다.

```bash
.venv/bin/python -m griffe dump machine runner -o g.json -s .
.venv/bin/python machine/pycalls.py machine runner --repo . -o pycalls.json
.venv/bin/python machine/normalize.py --griffe-dump g.json --py-calls pycalls.json --repo . -o codegraph.json
```

| | 노드 | 간선 |
|---|---:|---:|
| strict 전, griffe 만 | 2 | 0 |
| griffe 만 (지금) | 67 | 122 |
| **griffe + pycalls** | **613** | **840** (모듈 넘는 호출 340) |

`--py-calls` 는 `--clang-doc` 과 같은 자리다 — **배타 그룹이 아니라 합치는 인자**이고 안 주면 옛 동작
그대로다(바이트 대조로 확인). 호출의 kind 는 `dependency`(8종 enum 안, "부른다"의 UML 대응)다.

**함정 — 이름 해소가 이 수집기의 급소다.** 틀려도 오류가 안 나고 간선이 조용히 사라진다.
이 저장소는 `import machine.warmup` 이 아니라 `sys.path` 를 조작한 뒤 **`import warmup`** 이라는
평평한 이름을 쓴다. 개발 중 디렉토리 뿌리로 걸렀더니 모듈 넘는 호출이 **338 → 1** 로 떨어졌다.
`import_table` 이 **파일 이름(stem)** 을 열쇠로 잡는 이유다. 이름이 겹치면 조용히 고르지 않고 **둘 다 버린다.**

### 3-4. 심볼 해석 플랜의 핵심 주장을 재현했다

`docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md` 의 결함 1(= `depends_on` 이 노드 id 라
`dep_excerpt` 가 언제나 빈 문자열)을 **Python 쪽에서 독립적으로 재현**했다. 계획서의 근거는 C++ 실행 1건이었다.

| 산출물 | 노드 | `id == name` |
|---|---|---|
| `normalize.py` 원본 | 61 | **0개** (`id='C1'`, `name='machine.clang_doc.Symbol'`) |
| `terms_db` 투영 | 173 | **173개 전부** |

원본으로 `survey_plan.plan()` 을 돌리면 `depends_on` 34개가 **전부 노드 id** 이고 이름은 0개다.

**그리고 왜 이 저장소가 못 봤는지도 나왔다** — `out/codegraph-raw/codegraph.json` 은 `normalize.py`
원본이 아니라 **`terms_db` 투영**이고, 투영은 이름을 id 로 쓴다. 계획서가 지목한 "합성 픽스처가
`id==name` 을 만들어 못 잡았다" 외에 **실데이터 경로에도 같은 은폐가 하나 더 있다.**

---

## 4. 주석 정리(D8) — 완료

서브에이전트 5개가 34파일을 처리했다. **넷은 정상 종료, `runner/` 담당 하나는 세션 한도(HTTP 429)로
검증 직전에 죽어 내가 대신 검증했다.**

```
① machine/normalize.py · clang_doc.py · pycalls.py · codegraph_types.py
② machine/ 나머지 생산 11파일 (terms_db · xmldoc · warmup · survey_plan · declmap · clangd_refs
   · reverse_refs · verify_citations · file_cache · fix_citation_paths · facts)
③ machine/test_*.py 9파일
④ runner/ 파이썬 6파일
⑤ viz/ 3파일 + tools/scrub_local_paths.py
```

### 동작 보존을 어떻게 증명했나 — 묶음마다 강도가 다르다

| 묶음 | 증명 |
|---|---|
| `viz/`+`tools/` · `normalize` 묶음 · `machine/` 생산 11 | **AST 대조로 코드 무변경** + 산출물 바이트 동일 |
| `machine/test_*` 9 | `test_` 함수 184개 불변 · pytest 수 불변 |
| **`runner/` 6** | ⚠ **AST 대조 불가** — 깨끗한 편집 전 사본이 안 남았다. 대신 동작으로 확인: 측정 함수(`hms`·`normalize_usage`)가 세션 초반 기록값과 **타입까지** 일치, 세 mode 가 같은 객체 참조, `--help` 3개, `pytest runner/` 158 통과 |

**`runner/` 만 증거가 한 단계 약하다.** 이후에 그쪽을 의심할 일이 생기면 이 사실을 감안할 것.

각 에이전트가 보고한 **"남긴 형식·동작 사실"** 목록이 §5 의 A-3 재료다 — 합쳐서 100건이 넘는다.

---

## 5. 남은 작업 — 우선순위 순

### ~~A-1. `xmldoc inject`~~ — **완료** (148건 → 0건)

```bash
cd $REPO_ROOT
.venv/bin/python machine/xmldoc.py check          # 문제 건수 확인
.venv/bin/python machine/xmldoc.py inject --dry-run   # "고칠 파일 0개" 인지 본다
.venv/bin/python machine/xmldoc.py inject
.venv/bin/python machine/xmldoc.py check          # 기대: 문제 0건
```

⚠ 이것은 `machine/terms-reading.json` 과 `machine/comments.xml` 을 갱신한다.
**소스 파일은 건드리지 않는다**(`--dry-run` 이 "고칠 파일 0개" 로 확인해 준다).
같은 작업 트리의 다른 세션 몫 드리프트도 함께 정리된다 — 그쪽에 알려 두는 것이 좋다.

### ~~A-2. 디렉토리별 `README.md`~~ — **완료**

**손으로 쓰지 않고 생성기를 만들었다.** 손으로 쓰면 다음 커밋에 낡는데 그게 고치려던 문제다.

```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools           # 쓴다
.venv/bin/python tools/gen_readme.py machine runner viz tools --check   # 낡았으면 exit 1
```

| 산출 | 줄 |
|---|---|
| `machine/README.md` | 636 |
| `runner/README.md` | 309 |
| `viz/README.md` | 71 |
| `tools/README.md` | 44 |

시그니처는 **`pycalls.signature_of` 를 그대로 재사용**한다 — 두 곳에서 만들면 어긋난다.
설명 한 줄은 각 심볼 독스트링의 첫 줄이다. **즉 README 를 갱신하려면 코드 주석을 고치면 된다.**

`tools/test_gen_readme.py` 4건이 드리프트 게이트다 — 소스를 고치고 생성기를 안 돌리거나
README 를 손으로 고치면 **깨진다**(일치 exit 0 · 낡음 exit 1 로 양방향 확인).

⚠ **README 를 손으로 고치지 마라.** 다음 생성에 덮이고 게이트가 먼저 빨개진다.
디렉토리 한 줄 설명만 사람이 쓰는 자리이고 `tools/gen_readme.py` 의 `DIR_ROLE` 에 있다.

### A-3. 걷어낸 사실을 시험으로 — **착수했고 6건 완료. 나머지는 선택**

원리: **주석은 썩지만 시험은 깨진다.**

`machine/test_external_contracts.py` 6건으로 시작했다. 커버리지를 먼저 재 보니
**Graphviz 와 Mermaid 는 시험이 0건**인데 주석에는 그 도구들의 동작 주장이 여럿이었다.

| 시험 | 고정한 주장 |
|---|---|
| Graphviz 범례 `constraint` | false 면 캔버스가 옆으로 넓어진다 — **156pt → 250pt** 로 실측 |
| networkx `DiGraph` | 런타임에 첨자를 못 받는다 (그래서 주석을 따옴표에 넣는다) |
| griffe 주석 | 문자열이 아니라 **식 트리** — R5 의 전제 |
| declmap `LANGS` | 다섯 칸 형 고정, None 되는 건 `strip` 뿐(실제로 `cs` 만) |
| declmap 정규식 | 문법을 모른다 — 문자열 안 `class` 에도 걸린다 |
| `ast.unparse` | 주석을 원문 그대로 되살린다 |

**이 작업의 값어치가 즉시 드러났다.** 요약을 보고 쓴 첫 판이 **두 번 틀렸다** —
`LANGS` 의 `doc` 을 Pattern 이라 했는데 튜플이었고(`lead` 칸도 하나 더 있었다),
`scan()` 이 `git ls-files` 를 타는 걸 몰랐다. **시험이 즉시 잡았다.**
같은 내용을 주석에 적었으면 아무도 몰랐다.

그래서 `declmap` 시험은 `scan()` 이 아니라 **정규식을 직접** 겨눈다 — `scan` 을 태우면
이 한계와 무관한 것(git 추적 여부)까지 함께 시험하게 된다. **주장의 실제 단위를 겨눌 것.**

**남은 후보**
- **Mermaid 제약 4종** (`style X~T~` 의 GENERICTYPE 오류 등) — `mmdc` 가 필요해 무겁다. 미착수
- 에이전트들이 보고한 "남긴 형식·동작 사실" 100건+ — 대부분 **저장소 내부 불변식**이라
  이미 각 모듈 시험이 덮는다. **바깥 도구에 기대는 것만** 골라 옮기는 것이 비용 대비 이득이 크다

### A-4. 중복 스키마 5곳을 `codegraph_types` 로 접기 (D4, 미완 — **사용자 승인 필요**)

`machine/facts.py` · `survey_plan.py` · `verify_citations.py` · `viz/render_modules.py` ·
`viz/render_classes.py` 가 각자 `CodeGraph`/`Node`/`Edge` 를 선언한다.

**측정해 둔 것:** 로컬 선언들의 열쇠는 **전부 정본의 진부분집합**이다(정본 밖 열쇠 0개).
서로 모순이 아니라 각자 읽는 부분만 좁게 적은 것이다. 형이 다른 자리는 9군데이고 전부
"로컬이 더 좁다"(`str` vs `str | None`, `str` vs `EdgeKind` Literal).

그래서 **통째 치환은 위험하다** — 필수성을 넓혀 지금 초록인 파일 5개를 건드리게 된다.
대안은 **정합 시험**이다: 각 로컬 선언이 정본의 부분집합인지 자동으로 검사한다. 드리프트를
잡는다는 목표는 그것으로 달성된다. **어느 쪽으로 갈지 사용자에게 물어볼 것.**

⚠ `viz/` 는 `python viz/render_modules.py` 로 직접 실행돼 `machine/` 이 경로에 없다.
런타임 import 를 늘리지 않으려면 `if TYPE_CHECKING:` 을 쓴다(Python 3.14 는 주석 지연 평가가 기본).

### A-5. 심볼 해석 플랜 실행 — 착수 전 세 가지를 고쳐야 한다

`docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md`

1. **경로가 전부 낡았다.** File Structure 가 `codegraph/survey_plan.py` 를 가리키는데
   지금은 `machine/survey_plan.py` + `runner/run_mode1.py` 다. 코드 조각의
   `<include file="docs/codegraph/comments.xml">` 도 `machine/comments.xml` 로 바뀌었다.
2. **계획이 건드릴 3파일이 strict 0 이 됐다.** `survey_plan.py`·`run_mode1.py`·`terms_db.py` 에
   TypedDict 가 붙었으므로 계획서의 코드 조각을 그대로 붙이면 타입 검사에 걸린다.
   반대로 말하면 이제 그 수정이 정적으로 검증된다.
3. **결함 1을 정적으로 불가능하게 만들 수 있다.** 지금 `depends_on: list[str]` 이라
   "id 문자열"과 "이름 문자열"이 같은 형이다. `NodeId = NewType("NodeId", str)` /
   `SymbolName = NewType("SymbolName", str)` 로 가르면 **id 를 이름 자리에 넣는 것이 타입 오류**가 된다.
   계획서 Task 1 이 값을 고친다면 이건 재발을 구조로 막는다. **제안이고 미승인이다.**

### A-6. 자기 검토 파이프라인 — **막는 것이 없어졌다. 다음 에이전트 몫**

```
① Mode 1     machine/ + runner/ 전수조사 → terms-db.json
② Mode 1.5   심볼 해석 플랜의 용어로 이해도 측정 → terms.json
③ Mode 2     그 용어집을 달고 플랜 검토 대시보드
```

목적은 **이 도구의 확장 설계를 이 도구 자신으로 검토**하는 것이다.

**이번에 치운 장애물 넷** — 넷 다 Mode 1 을 못 돌게 하던 것이다.

1. **세 실행기가 삭제된 `scripts/` 를 가리켰다.** 개편으로 `runner/`·`viz/` 로 갈렸는데
   `run_mode1.py`·`run_mode1_5.py`·`run_mode2.py` 가 옛 경로 그대로였다.
   **시험이 경로 문자열만 대조해서 초록인 채로 깨져 있었다** — `runner/test_run_mode1.py` 의
   `test_every_runner_script_path_actually_exists` 가 이제 **파일 존재**를 본다.
2. **`prep` 에 Python 갈래가 없었다.** `clang-uml`(C++)과 `roslyn-dump`(C#) 둘뿐이라
   파이썬 저장소는 `"none"` 으로 막혔다. `griffe -> pycalls -> normalize` 갈래를 더했다.
3. **`LANG_ALIAS` 에 `python` 이 없었다.** `lang_of` 가 `None` 을 내고 **warmup 이 조용히
   건너뛰어졌다** — 죽지 않아 알아채기 어렵다. 한 줄 고치고 시험으로 못박았다.
4. **언어를 고르는 자리가 파일 이름 추론뿐이었다.** `collectorFor` 가 `.csproj`/`CMakeLists.txt`
   만 보므로 파이썬·TS 는 판정 불가였다.

**새 단계 `lang-select`** (Mode 1 의 맨 앞, 열 단계 중 첫째)

```bash
.venv/bin/python runner/run_mode1.py <저장소> --only lang-select
# 또는 손으로
.venv/bin/python machine/lang_select.py <저장소> --propose py -o out/codegraph-raw/lang-select.json
```

**설계 원칙 — 모형은 제안하고, 결정론이 판정한다.** Haiku(`claude-haiku-4-5-20251001`)가
루트 문서(README·CLAUDE·ARCHITECTURE·AGENTS)를 읽고 `cpp|cs|py|ts` 중 낱말 하나를 낸다.
`machine/lang_select.py` 가 그 제안을 세 가지로 거른다:

| 제안 | 판정 |
|---|---|
| 아는 언어가 아니다 (`rust`) | 버리고 파일 수로 |
| 그 언어 소스가 0개 | 버리고 파일 수로 |
| **수집기가 없다 (`ts`)** | **수집 가능한 언어로 물러선다** — 지도가 없는 것보다 부분 지도가 낫다 |
| 통과 | 따른다. 파일 수 1위와 다르면 `why` 에 적는다 |

소수파 제안을 **따르는 것이 의도**다 — 세는 것으로는 "많은 쪽이 도구이고 주제는 적은 쪽"을
알 수 없고 그게 모형이 문서를 읽는 이유다.

⚠ **실제로 돌려 보니 Haiku 가 `ts` 를 제안했다.** 이 저장소의 루트 `CLAUDE.md` 는
React/TypeScript 서사가 지배적이라 틀린 판단은 아니지만 **TS 는 수집기가 없다.**
그래서 위 셋째 규칙을 넣었고, 프롬프트도 "문서가 무엇을 많이 이야기하는지가 아니라
**분석해서 얻을 것이 있는 코드**가 어느 언어인지" 로 고쳤다. 그 한 번의 실행이
설계 구멍을 드러냈다 — 다음 저장소에서도 `why` 를 반드시 읽을 것.

**🔵 이 저장소에서 `prep` 이 완주하는 것을 확인했다:**
```
수집기 griffe+pycalls · 단계 griffe -> pycalls -> normalize -> facts -> render-modules
클래스 697 / 모듈 4 / 순환 0 · 언어 python · 간선 933
```

⚠ **`out/codegraph-raw/codegraph.json` 이 있으면 `prep` 이 수집을 건너뛴다**(`hasCodegraph` 갈래).
낡은 지도가 남아 있으면 그것을 쓰므로, 다시 수집하려면 먼저 지워야 한다. `out/` 은 git 제외라 안전하다.

## 6. 가드레일 — 그대로 지킬 것

### 커밋

**사용자가 명시적으로 요청할 때만 커밋한다.** 이 세션의 작업 전부가 미커밋이다.
커밋하게 되면 `personal-commit-messages` 스킬을 따른다 — 소문자 `[tag] : subject` 한 줄, 한국어,
본문 없음, 트레일러 없음.

**`git add -A` 를 쓰지 마라.** 같은 작업 트리에 다른 세션의 변경이 섞여 있다(아래).

### 병렬 세션 — 충돌 지형

이 저장소는 **여러 세션이 같은 작업 트리를 공유한다.** 이번 대화 중에도 다른 세션이
`codegraph/`→`machine/`+`runner/`, `scripts/`→`viz/`, `src/`→`viz/src/` 개편을 커밋했다.

| 건드리지 말 것 | 이유 |
|---|---|
| `docs/my.self/**` | 사용자 개인 메모. 요청 없이 읽지도 않는다 |
| `ARCHITECTURE.md` · `viz/src/CLAUDE.md` · `test/docs-citations.test.mjs` | 다른 세션이 수정 중 |
| `docs/superpowers/plans/` 의 옛 계획서 | 아카이브. 과거 코드 인용이 박혀 있고 그대로 두는 것이 맞다 |

**`git stash` · `git checkout` · 브랜치 전환 금지.** 남의 작업을 날린다.

### 절대 손으로 건드리지 말 것

- **`# <include file="machine/comments.xml" .../>` 블록과 그 아래 두 줄** —
  `machine/xmldoc.py` 가 `machine/terms-reading.json` 에서 자동 주입한다.
  손으로 달거나 지우면 `xmldoc.py check` 가 깨진다. **새 함수에 태그를 손으로 달지 마라.**
- **`machine/comments.xml`** — `terms-reading.json` 의 파생물이다.
  고쳐야 하면 `xmldoc.py emit` 으로 재생성한다(`run_check` 가 바이트 대조를 한다).

### 알려진 함정

- **`terms_db.py` 의 투영이 입력 `codegraph.json` 을 덮어쓴다.** 정적 파일을 위치 인자로
  주지 않고 `--reading` 만 주면 노드가 조용히 줄어든다. 시험할 때는 **사본을 만들어 스크래치패드에서** 돌려라.
- **골든 경로 상수가 빈 문자열이 되면 안 된다.** `os.path.join("", "out/…")` 이 상대경로가 되어
  이 저장소 산출물을 골든으로 착각해 읽는다. 그래서 `… or "/골든저장소_미지정/<변수>"` 를 쓴다.
- **`node --test test/` 는 죽는다.** 인자 없는 `node --test` 를 쓴다.
- **`viz/render_classes.py` 가 일부 모듈에서 Graphviz 자체를 죽인다**
  (`Assertion failed: … fixLabelOrder, mincross.c:273`). 이 작업과 무관한 기존 문제이고
  `.dot` 은 dot 실행 전에 쓰이므로 대조는 성립한다.
- **`out/codegraph-raw/codegraph.json` 이 낡았다.** 모듈이 `codegraph`·`scripts`·`src` 로 되어 있어
  개편 **전** 산출물이다. 여기에 기대는 시험·대조를 할 때 이 사실을 감안하고, 필요하면
  §3-3 의 세 명령으로 다시 만든다.

### ⚠ 스크래치패드가 세션 간에 공유된다

편집 전 사본을 스크래치패드에 두면 **다른 세션이 덮어쓸 수 있다.** 실제로 이번에 한 에이전트의
스냅샷이 지워졌다(편집 스크립트를 역순으로 되감아 복원했고, 줄 수 대조로 검증했다).

**사본은 세션 고유 이름의 디렉토리에 둔다.** 예: `/private/tmp/claude-501/rb-<작업이름>-<세션id>/`.
그리고 사본을 만든 직후 `wc -lc` 를 찍어 두면 나중에 복원본이 맞는지 대조할 수 있다.

### 주석만 고쳤음을 증명하는 법 — AST 대조

D8 작업처럼 "주석만 고쳤다" 는 주장은 **독스트링을 뺀 AST 를 비교**하면 증명된다.
시험 통과보다 강하다 — 코드가 한 글자라도 바뀌면 잡힌다.

```python
import ast
def strip(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                n.body = b[1:] or [ast.Pass()]
    return ast.dump(t)
# strip(편집_직전_사본) == strip(현재) 이면 코드 무변경이다
```

⚠ **기준선을 `git show HEAD:` 로 잡으면 안 된다.** 이 세션의 strict 작업으로 파일들이 이미
HEAD 와 다르다. **편집 직전 사본**을 스크래치패드에 `cp` 해 두고 그것과 비교해야 한다.
(이 함정에 실제로 한 번 걸렸다 — HEAD 와 비교해 "코드가 바뀌었다" 는 거짓 경보가 났다.)

### 검증 명령 (정확히 이대로)

```bash
cd $REPO_ROOT
npm run typecheck:py                                  # pyright strict — 기대 0 errors
npm run typecheck                                     # tsc --noEmit
npm test                                              # 기대 178 통과
.venv/bin/python -m pytest machine/ runner/ tools/ -q  # 기대 352 통과 · 19 건너뜀
.venv/bin/python machine/xmldoc.py check              # 기대 문제 0건

# 골든 저장소까지 (기대 367 통과 · 4 건너뜀)
GRAPHICS_REPO=$HOME/DevelopProjects/SSU/GlobalMedia-OpenGL-ComputerGraphics \
CSHARP_REPO=$HOME/DevelopProjects/UnityProjects/StickRushGame \
  .venv/bin/python -m pytest machine/ runner/ tools/ -q
```

⚠ **`pyrightconfig.json` 의 `venvPath`/`venv` 와 `extraPaths` 를 지워서는 안 된다.**
없으면 `pytest` 같은 설치된 패키지와 형제 디렉토리 import 를 못 찾아 **유령 오류 12건**이 난다.

---

## 7. 보고만 하고 고치지 않은 것들

전부 런타임 결함은 아니지만 누군가 판단해야 한다.

| 자리 | 무엇 |
|---|---|
| `machine/terms_db.py` `STRUCTURE_FIELDS` | 정의만 있고 **아무 데서도 안 쓰인다.** 주석은 "LLM 이 덮어쓸 수 없는 필드" 라는데 `merge_terms` 가 참조하지 않는다. 죽은 상수인지 빠진 배선인지 미판단 |
| `machine/warmup.py` `decl_hash` | `(kind, name)` 만 해싱해 **본문을 통째로 다시 써도 "위치만"** 으로 판정된다. 알려진 구멍이고 이번에 안 건드렸다 |
| `runner/run_mode1.py` `StageRow` | `ok`·`why` 를 required 로 적었는데 `format_report` 는 셋 다 `.get()` 으로 읽는다. `NotRequired` 로 내리면 시험 11건이 사라지면서 `stage`·`seconds`·`usage` 검사는 유지된다 |
| `machine/test_terms_db.py` `_graph` | 주석은 "normalize.py 출력 키 그대로" 인데 `platform`·`source_tool` 이 빠져 있다 |
| `machine/test_xmldoc.py` 픽스처 | `Term.source` 가 필수인데 한 번도 안 채운다. 주입 경로가 그 필드를 안 읽어서 통과해 왔다 |
| `xmldoc.Use.label` vs `terms_db.DbUse.label` | `str` vs `str \| None`. **불일치가 아니라** 서로 다른 두 파일(`terms-reading.json` vs `terms-db.json`)을 서술한다. 이름이 비슷해 헷갈릴 뿐 |
| `docs/superpowers/plans/` 두 계획서 | `_hms`·`_Heartbeat` 옛 이름이 9곳 남아 있다. **과거 코드 인용**이라 그대로 두는 것이 맞다 |

---

## 8. 이 세션이 배운 것 — 왜 작업이 길어졌나

측정이 네 번 계획을 뒤집었다. 원인을 따라가 보면 **코드 주석이 낡아서가 아니었다:**

| 뒤집힌 것 | 출처 |
|---|---|
| R5 제외 근거 · 자기호스팅 골든 | `docs/handoffs/` 인계 문서의 **미검증 주장** |
| 94%/6% 갈라내기 | 아무도 주장 안 함. 안 쟀을 뿐 |
| 파일명 클래스 래핑 | 요청의 전제 |

그리고 틀린 코드 주석 둘은 **썩은 게 아니라** 쓸 때부터 틀렸거나(한 번 본 것을 일반화) 개명이
무효화한 것이었다.

**구조적 원인:** 이 저장소의 게이트는 전부 **위치**만 검사한다.
`docs-citations` 는 L1(파일이 있나), `xmldoc check` 는 "마커와 `where` 가 같은 자리인가",
`verify_citations` L3 는 "그 줄 근처에 그 이름이 있나". 어느 것도 **주장의 참거짓**은 못 본다.

**같은 인계 문서 안에서 갈렸다.** 한 미검증 주장은 "이건 전언이다" 로 표시됐고 다른 하나는 안 됐는데,
**표시된 쪽은 무해했고 표시 안 된 쪽이 R5 를 밀어냈다.** 규약은 있었고 작동했다 — 강제하는 장치가 없었을 뿐이다.

→ 그래서 A-3(주장을 시험으로 옮기기)이 이 문제를 실제로 닫는 유일한 항목이다.

---

## 변경 이력

- 2026-08-30 — 최초 작성. Python strict 전환(5,409→0) · `pycalls.py` 수집기 신설 ·
  주석 정리(진행 중) 시점에서 인계. 남은 작업 A-1 ~ A-6.
- 2026-08-31 — A-1(`xmldoc inject` 148→0) · A-2(README 생성기 + 드리프트 게이트) ·
  A-3(바깥 도구 계약 시험 6건) 완료. pytest 331 → 341. 남은 것은 A-4 · A-5 · A-6 이고
  A-4/A-5 는 사용자 승인이 필요하다.
- 2026-08-31 — `lang-select` 단계 신설(Haiku 제안 + 결정론 판정) · `prep` 에 Python 갈래 ·
  세 실행기의 죽은 `scripts/` 경로 수정 · `LANG_ALIAS` 에 python. **Mode 1 이 이 저장소에서
  처음으로 완주한다.** pytest 341 → 352.
