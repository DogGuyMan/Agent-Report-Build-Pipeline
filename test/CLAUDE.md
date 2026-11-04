# test/ — 모듈 시험. mode 별로 모은다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 저장소 규약 게이트는 [`../qa/CLAUDE.md`](../qa/CLAUDE.md).

| 폴더 | 무엇을 | `sys.path` 에 넣는 것 |
|---|---|---|
| `codewiki/` | Mode 1 — 수집기 · 정규화 · 용어 DB · warmup · 층 계획 · 봉인 매니페스트 · 단계 기계 위의 Mode 1 실행기 · 모듈 DOT 템플릿 | `src/` · `src/codewiki/python/{runner,machine,viz}` |
| `term/` | Mode 1.5 — 실행기 · 채점 · collect/quiz/emit | `src/` · `src/term/python/runner` |
| `spec/` | Mode 2 — `init` 의 slug · `check` 의 `<script>` 상한 · 경로 링크 · 용어 감싸기 · React 컴포넌트와 용어 그래프 수학(Node 자식 프로세스) · `config.toml` 대조 · 보고서 뼈대 템플릿 · **유일한 Node 시험** `svg.test.mjs` | `src/` · `src/spec/python/{runner,viz}` |
| `core/` | 단계 기계 · 측정 · 명령 갈림길 · Mode 1.5 와 2 를 import 해도 networkx 가 실리지 않는가 | `src/` 만 |
| `common/` | 리소스 자리 채우기 · 봉인 판정(`evidence.py`) | `src/` 만, 봉인 판정은 `src/common` |
| `tools/` | README 표류 · 해석기 탐색 · doctor 출력 · 계약 JSON 과 계약 형 생성기 | `src/` 만, 생성기는 `tools` |

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest -q                       # 전량 — test/ 와 qa/ 를 pytest 가 모은다
.venv/bin/python -m pytest test/spec -q             # 한 mode
.venv/bin/python -m pytest -k "링크" -q              # 이름으로 고르기
npm test                                            # pretest 가 src/spec/typescript/lib.mjs 로 .tmp/ 에 lib.mjs 를 굽고 node --test
GRAPHICS_REPO=… CSHARP_REPO=… .venv/bin/python -m pytest -q   # 골든 19개까지 돈다
```

## 비직관적인 것 (Gotchas)

- **건너뜀 19개는 실패가 아니다.** 골든 저장소 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO`)가 없어서다. 전부 `test/codewiki/` 쪽이다.
- **pytest 설정 파일이 없다.** 저장소 루트에서 `test_*.py` 를 전부 모은다. 루트 밖에서 돌리면 import 경로가 어긋난다.
- **시험 파일마다 자기 `sys.path` 를 넣는다.** 다른 시험이 먼저 넣은 폴더에 기대면 그 파일만 따로 돌릴 때 깨진다 — 위 표의 줄을 쓴다.
  코드는 `src/` 아래 있고 `src/` 는 패키지가 아니다 — `from core import …` · `from spec.python.viz.… import …` 는 `os.path.join(ROOT, "src")` 가 있어야 된다.
- **`node --test test/` 는 Node v25 에서 죽는다.** 인자 없는 `node --test` 를 쓴다.
- **렌더 시험은 임시 파일을 `ROOT` 에 쓴다**(`.tmp-eval.mjs` · `.tmp-eval-math.ts`). 동적 `import()` 가 파일 위치 기준으로 `react` 를 찾는다.
- **`src/spec/typescript/src/` 를 고쳤는데 시험이 옛 동작을 보인다** — `.tmp/` 의 `lib.mjs` 가 낡았다. `npm test` 로 다시 굽는다.
- **pyright 가 보지 않는 시험 넷** — `test/term/test_term.py` · `test/spec/test_link_paths.py` · `qa/gates/test_docs_citations.py` · `qa/gates/test_prompt_resources.py` 는 형 주석이 없어 `pyrightconfig.json` 의 `exclude` 에 있다. 넷 다 정리 전의 `test/` 에 있던 파일이라 처음부터 검사 밖이었다.
