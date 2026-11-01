# src/ — 코드가 사는 자리. 패키지가 아니라 import 뿌리다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 시험은 [`../test/CLAUDE.md`](../test/CLAUDE.md), 규약 게이트는 [`../qa/CLAUDE.md`](../qa/CLAUDE.md).

`src/` 안에는 `__init__.py` 가 없다. 진입점(`bin/`)과 시험이 `src/` 를 `sys.path` 에 넣어 `from core import …` 꼴로 쓴다.

| 자리 | 무엇 | 문서 |
|---|---|---|
| `codewiki/` | Mode 1 — 코드베이스 위키 | [`codewiki/CLAUDE.md`](codewiki/CLAUDE.md) |
| `term/` | Mode 1.5 — 용어 이해도 점검 | [`term/CLAUDE.md`](term/CLAUDE.md) |
| `spec/` | Mode 2 — 설계 검토 보고서 | [`spec/CLAUDE.md`](spec/CLAUDE.md) · [`spec/typescript/CLAUDE.md`](spec/typescript/CLAUDE.md) |
| `core/` | 세 실행기가 함께 타는 단계 기계 · 측정 · 명령 갈림길 | [`core/CLAUDE.md`](core/CLAUDE.md) |
| `common/` | 해석기 탐색 · 자리 채우기 · 봉인 판정 | 자기 `CLAUDE.md` 가 없다 — [`core/CLAUDE.md`](core/CLAUDE.md) 가 함께 설명한다 |

## 이 모듈이 소유하는 것 (Owns)

`src/**` 의 자리 구분 — 어느 mode 의 것인가, 둘 이상이 쓰면 `core/` 나 `common/`. 소유하지 않는 것 — 각 폴더 안쪽의 규칙. 그것은 위 표의 문서가 소유한다.

## 새 코드를 어디에 둘까 (How to)

- 한 mode 만 쓰면 그 mode 폴더 안에 둔다. 언어(`python/` · `typescript/`) 아래에서 시키는 것은 `runner/`, 계산하는 것은 `machine/`, 그리는 것은 `viz/`.
- 실행 중에 둘 이상의 mode 가 부르면 `common/` 에 둔다. 유지보수 도구(환경 점검 · README 생성 · 계약 생성)는 `src/` 가 아니라 `tools/` 다.
- 새 파이썬 폴더에 `README.md` 가 필요하면 `tools/gen_readme.py` 의 폴더 목록에 더한다. 같은 목록이 루트 `CLAUDE.md` 의 "게이트 여섯" 표 · `tools/CLAUDE.md` · `.github/workflows/docs-gates.yml` 에 있으니 함께 고친다.
- 파일을 옮기면 컨텍스트 문서가 인용한 경로도 함께 고친다. `qa/gates/test_docs_citations.py` 가 어긋난 인용을 잡는다.

한 영역의 시험만 돌릴 때는 저장소 루트에서 폴더를 고른다:

```bash
.venv/bin/python -m pytest test/core test/common -q   # 단계 기계 · 측정 · 갈림길 · 유틸
.venv/bin/python -m pytest test/term -q               # Mode 1.5
```

## 비직관적인 것 (Gotchas)

- **Gotcha:** `common/` 은 자기 `CLAUDE.md` 가 없다. 그 폴더의 파일을 고치기 전에 `core/CLAUDE.md` 를 읽어야 역할을 안다.
- **Warning:** `codewiki/` 가 `term/` 이나 `spec/` 를 import 하면 두 저장소 분리 때 `codewiki/` 를 통째로 떼어낼 수 없다. mode 끼리 나눠 쓸 것은 `common/` 으로 올린다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `codewiki/` · `term/` · `spec/` → `core/` · `common/` | 단계 기계와 유틸을 import 한다 |
| `core/` → `common/` | `pipeline.py` 는 `template.TemplateError` 만, `dispatch.py` 는 `python.pythonPath` 를 쓴다 |
| `term/` · `spec/` → `codewiki/` | **import 하지 않는다.** 봉인된 Mode 1 산출물을 읽을 뿐이다 — `test/core/test_import_isolation.py` 가 `run_mode2` · `run_mode1_5` 를 import 해도 networkx 가 실리지 않음을 잰다 |
| `codewiki/` → `term/` · `spec/` | **import 하지 않는다** |
| 바깥 → `src/` | `bin/` 진입점 · `tools/` · `test/` 가 `sys.path` 에 `src/` 를 넣어 import 한다 |
