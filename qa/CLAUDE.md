# qa/ — 저장소가 규약을 지키는가. 코드가 맞는가는 test/ 의 몫

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 모듈 시험은 [`../test/CLAUDE.md`](../test/CLAUDE.md).

## gates/ — 규약 게이트 넷

| 파일 | 무엇을 고정하나 |
|---|---|
| `test_docs_citations.py` | 컨텍스트 문서(루트 · 모듈 `CLAUDE.md` · `README.md` · `ARCHITECTURE.md` · 에이전트 셋 · 스킬 셋 · 계약 문서)의 `파일:줄` 인용과 경로가 실재하는가. 목록은 `contextDocs()` |
| `test_no_any.py` | 형 자리의 `Any` 를 글자로 막는다. `COVERED` 의 파일은 `Any` 0 |
| `test_prompt_resources.py` | 리소스와 코드를 가르는 게이트 — 코드에 긴 글이 없다 · 단계의 `prompt_names` 와 `resource/<mode>/prompts/*.md` 의 파일 · 절이 1:1 · 템플릿마다 코드에 같은 값의 문자열 상수 · 프롬프트와 결함 표가 Jinja2 로 컴파일 · 줄 끝 공백과 `{#` 없음 |
| `test_wiki.py` | `report-wiki prep · build · check` 가 실제로 돈다. `check` 는 `docs/wiki/` 를 이 저장소 기준으로 검사한다 — 빨강이면 위키 재굽기가 답이다 |

CI(`.github/workflows/docs-gates.yml`)는 앞의 둘만 돈다 — 나머지는 Graphviz · Node · 골든 저장소가 필요해 로컬 몫이다.

## evals/ — 실행기가 잰 값

세 mode 실행기가 `--json` 으로 낸 단계별 시간 · 토큰 · 비용. 판정하지 않고 쌓아 둔다 — `evals/README.md`.

```bash
.venv/bin/python -m pytest qa/ -q                     # 게이트 넷
.venv/bin/python src/codewiki/python/runner/run_mode1.py <저장소> --model opus --json qa/evals/runs/$(date +%F)-mode1-<대상>-<조건>.json
```

## 이 모듈이 소유하는 것 (Owns)

`qa/**`. 소유하지 않는 것 — 검사 대상인 코드와 문서. 게이트가 빨개지면 대상을 고치지 게이트를 느슨하게 만들지 않는다.

## 자주 하는 변경 (Common changes)

- **새 컨텍스트 문서(`CLAUDE.md` · 에이전트 · 스킬)를 만들었다** — `qa/gates/test_docs_citations.py` 의 `contextDocs()` 목록에 올린다. 안 올리면 그 문서의 인용과 경로는 검사 밖이다.
- **`Any` 를 모두 걷어낸 파일을 지키고 싶다** — `qa/gates/test_no_any.py` 의 `COVERED` 에 더한다. 아직 `Any` 가 남은 파일을 넣으면 게이트가 빨개진다.
- **새 프롬프트 단계를 더했다** — 파일과 절 이름이 단계의 `prompt_names` 와 1:1 이어야 `qa/gates/test_prompt_resources.py` 가 통과한다. 방법은 [`../resource/CLAUDE.md`](../resource/CLAUDE.md).

## 비직관적인 것 (Gotchas)

- **Important:** CI(`.github/workflows/docs-gates.yml`)는 `test_docs_citations.py` 와 `test_no_any.py` 둘만 돈다. 나머지 둘의 빨강은 로컬에서만 보이니 푸시 전에 `pytest qa/` 를 돌린다.
- **Note:** `qa/evals/runs/` 의 JSON 은 실행기의 `--json` 출력이다. 게이트가 아니라서 빨개지지 않는다 — 판정하지 않고 쌓기만 한다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → 컨텍스트 문서 | `test_docs_citations.py` 가 `contextDocs()` 의 문서를 읽는다 |
| 여기 → `../src/**` | `test_no_any.py` 가 `COVERED` 의 파일을, `test_prompt_resources.py` 가 단계의 `prompt_names` 를 읽는다 |
| 여기 → `../resource/**` | `test_prompt_resources.py` 가 프롬프트 · 결함 표 · 템플릿을 읽는다 |
| 여기 → `../bin/report-wiki` | `test_wiki.py` 가 `prep · build · check` 를 실제로 돌린다 |
| 바깥 → 여기 | 제품 코드와 시험은 `qa` 를 import 하지 않는다 |
