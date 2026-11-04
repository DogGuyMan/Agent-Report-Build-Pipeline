# qa/ — 저장소가 규약을 지키는가. 코드가 맞는가는 test/ 의 몫

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 모듈 시험은 [`../test/CLAUDE.md`](../test/CLAUDE.md).

## gates/ — 규약 게이트 다섯

| 파일 | 무엇을 고정하나 |
|---|---|
| `test_docs_citations.py` | 컨텍스트 문서(루트 · 모듈 `CLAUDE.md` · `README.md` · `ARCHITECTURE.md` · 에이전트 셋 · 스킬 셋 · 계약 문서)의 `파일:줄` 인용과 경로가 실재하는가. 목록은 `contextDocs()` |
| `test_no_any.py` | 형 자리의 `Any` 를 글자로 막는다. `COVERED` 의 파일은 `Any` 0 |
| `test_prompt_resources.py` | 리소스와 코드를 가르는 게이트 — 코드에 긴 글이 없다 · 단계의 `prompt_names` 와 `resource/<mode>/prompts/*.md` 의 파일 · 절이 1:1 · 템플릿마다 코드에 같은 값의 문자열 상수 · 프롬프트와 결함 표가 Jinja2 로 컴파일 · 줄 끝 공백과 `{#` 없음 |
| `test_rule_copies.py` | 두 mode 에 사본으로 사는 규칙이 같은가 — 용어 찾기 규칙(`collect.py` · `check.py` 의 `TERM_PATTERNS`, 꼴과 플래그)과 봉인 소스 집합(`declmap.tracked_files` · `evidence.source_files`, `blob_ids`) |
| `test_wiki.py` | `report-wiki prep · build · check` 가 실제로 돈다. `check` 는 `docs/wiki/` 를 이 저장소 기준으로 검사한다 — 산문이 없으면 건너뛰고, 빨강이면 위키 재굽기가 답이다 |

CI(`.github/workflows/docs-gates.yml`)는 앞의 둘만 돈다 — 나머지는 Graphviz · Node · 골든 저장소 · 파이썬 의존성이 필요해 로컬 몫이다.

## evals/ — 실행기가 잰 값

세 mode 실행기가 `--json` 으로 낸 단계별 시간 · 토큰 · 비용. 판정하지 않고 쌓아 둔다 — `evals/README.md`.

```bash
.venv/bin/python -m pytest qa/ -q                     # 게이트 다섯
.venv/bin/python src/codewiki/python/runner/run_mode1.py <저장소> --model opus --json qa/evals/runs/$(date +%F)-mode1-<대상>-<조건>.json
```

## 이 모듈이 소유하는 것 (Owns)

`qa/**`. 소유하지 않는 것 — 검사 대상인 코드와 문서. 게이트가 빨개지면 대상을 고치지 게이트를 느슨하게 만들지 않는다.
