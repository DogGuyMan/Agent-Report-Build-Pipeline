# test/ — 축을 가로지르는 시험만 여기 둔다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 축 안의 시험은 그 축 옆에 산다 —
> [`../machine/`](../machine/CLAUDE.md) `test_*.py` 11개 · [`../runner/`](../runner/CLAUDE.md) `test_*.py` 8개 · [`../tools/`](../tools/CLAUDE.md) 2개.

**여기 있는 시험은 한 축에 속하지 않는다.** 문서 게이트, Node 를 자식으로 띄우는 렌더 시험,
`bin/` 진입점, 이식성 검사처럼 **두 축 이상을 함께 물거나 저장소 전체를 보는 것**만 온다.
한 모듈의 함수만 부르는 시험은 그 모듈 폴더에 둔다.

## 무엇이 여기 있나

| 파일 | 무엇을 고정하나 |
|---|---|
| `test_docs_citations.py` | 루트·모듈 `CLAUDE.md` · `README.md` · `ARCHITECTURE.md` · `.claude/CLAUDE.md` · 서브에이전트 셋 · 이 저장소의 스킬 셋의 `파일:줄` 인용이 실재하는가. `$` · `~` 로 시작하는 경로는 바깥으로 보고 건너뛴다. 대상 목록은 `contextDocs()` |
| `test_no_any.py` | 형 자리의 `Any` 를 글자로 막는다. `COVERED` 목록의 파일은 `Any` 0 이어야 한다 |
| `test_wiki.py` | `report-wiki prep · build · check` 가 실제로 돈다. `check` 는 `docs/wiki/` 를 이 저장소 기준으로 검사한다 |
| `test_components.py` · `test_graph_math.py` | React 컴포넌트와 용어 그래프 수학을 **Node 자식 프로세스**로 렌더해 본다. `.tmp/lib.mjs` 와 esbuild 가 필요하다 |
| `test_check.py` · `test_init.py` · `test_link_paths.py` · `test_wrap_terms.py` | Mode 2 의 `viz/*.py` 순수 함수 — `<script>` 상한 · slug 검증 · 경로 링크 · 용어 감싸기 |
| `test_dispatch.py` · `test_portability.py` | `bin/` 의 명령 갈림길과 `tools/python.py` 의 해석기 탐색 |
| `test_prompt_resources.py` | 리소스와 코드를 가르는 게이트 — 코드 안에 리소스로 뺄 긴 글이 없다 · 단계의 `prompt_names` 선언과 `prompts/*.md` 의 파일 · 절이 1:1 이고 파일 이름이 단계 이름이다 · 템플릿마다 그 파일 이름과 같은 값의 문자열 상수가 코드에 있고 템플릿 파일 이름은 겹치지 않는다 |
| `test_config.py` | `config/report.toml` 을 직접 읽어 코드가 같은 값을 쓰는지 대조한다 — 원본 문서 자리 규칙(`DOC_DIRS`) 두 곳 · Mode 2 모델 기본값 배선 |
| `test_templates.py` | 템플릿에서 짓는 파일 꼴 — 보고서 뼈대 `data.ts` 의 값 주입, 모듈 DOT 의 머리 · 범례 |
| `test_term.py` | Mode 1.5 얼갈이 `runner/term/*` |
| `svg.test.mjs` | **유일한 Node 시험.** `viz/svg.mjs` 의 id 접두사 · `viewBox` 규칙. `npm test` 가 돌린다 |

## 자주 쓰는 명령

전부 저장소 루트에서 돌린다 — 설정 파일이 없어 pytest 가 루트에서 `test_*.py` 를 모은다(아래 Gotchas).

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest -q                       # 전량 — machine/ runner/ tools/ test/ 를 pytest 가 알아서 모은다
.venv/bin/python -m pytest test/test_check.py -q    # 한 파일
.venv/bin/python -m pytest -k "링크" -q              # 이름으로 고르기 (시험 이름은 한국어여도 된다)
npm test                                            # pretest 가 viz/lib.mjs 로 .tmp/lib.mjs 를 다시 굽고 node --test
GRAPHICS_REPO=… CSHARP_REPO=… .venv/bin/python -m pytest -q   # 골든 19개까지 돈다
```

## 흔한 변경 패턴 (Common modification patterns)

```bash
# 새 컨텍스트 문서를 만들었다 — 인용 검사 대상에 올린다
$EDITOR test/test_docs_citations.py               # contextDocs() 의 목록에 한 줄

# 파일에서 Any 를 다 없앴다 — 게이트에 올려 되돌아오지 못하게 한다
$EDITOR test/test_no_any.py                       # COVERED 에 한 줄. Any 가 남아 있으면 바로 빨개진다

# viz/src/ 를 고쳤는데 test_components 가 옛 동작을 보인다 — .tmp/lib.mjs 가 낡았다
npm test                                          # 다시 굽는다. pytest 는 굽지 않는다

# 외부 도구의 동작에 기대는 사실을 알았다 — 주석이 아니라 시험으로 적는다 (루트 "코드 주석" 절)
```

## 이 모듈이 소유하는 것 (Owns)

`test/**`. **소유하지 않는 것** — 검사 대상인 코드와 문서. 시험이 빨개지면 대상을 고치지
시험을 느슨하게 만들지 않는다. 단 `test_wiki.py` 의 빨강처럼 **2차 산출물이 낡은 것**은
재생성(위키 재굽기)이 답이다 — 루트 "게이트 여섯" 절.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../viz/*.py` · `../runner/*` · `../tools/python.py` | 함수를 직접 import 한다. `ROOT` 를 `sys.path` 에 넣는 파일도 있다 |
| 여기 → `bin/report-wiki` | `test_wiki.py` 가 자식 프로세스로 띄운다 |
| 여기 → Node · esbuild | `test_components.py` · `test_graph_math.py` 가 `node` 와 `npx esbuild` 를 자식으로 띄운다. 없으면 실패하지 건너뛰지 않는다 |

## 비직관적인 것 (Gotchas)

- **Note — 건너뜀 19개는 실패가 아니다.** 골든 저장소 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO`)가
  없어서다. 전부 `machine/test_normalize.py` · `test_clang_doc.py` · `test_terms_db.py` 쪽이다.
- **Gotcha — pytest 설정 파일이 없다.** `pyproject.toml` · `pytest.ini` 둘 다 없고 `.venv/bin/python -m pytest`
  가 저장소 루트에서 `test_*.py` 를 전부 모은다. 루트 밖에서 돌리면 import 경로가 어긋난다.
- **Gotcha — `node --test test/` 는 Node v25 에서 죽는다.** 디렉토리를 파일로 취급한다. 인자 없는 `node --test` 를 쓴다.
- **Gotcha — 렌더 시험은 임시 파일을 `ROOT` 에 쓴다** (`.tmp-eval.mjs` · `.tmp-eval-math.ts`). 동적 `import()` 가
  파일 위치 기준으로 `react` 를 찾기 때문이다 — `viz/CLAUDE.md` 의 같은 규칙.
- **Note — `test_docs_citations.py` 는 `out/` 아래와 `<…>` 자리표시자를 면제한다.** 문서에 예시 경로를 적을 때
  실재하지 않는 파일은 그 꼴로 적는다.
