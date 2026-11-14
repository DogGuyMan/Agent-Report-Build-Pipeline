# 코드 지도 수집 실패 — 이어받기

- 대상 `{{ repo }}`
- 죽은 단계 `{{ step }}` · 종료 코드 {{ returncode }}
- 결함 {{ total }}건 · 수행한 검사 {{ checks_run }} · 전수조사 적합 {{ fit }}

규칙은 `verify-graph.md` 의 첫 절과 같다 — **검사를 완화해 통과시키지 말라.** 수집기 · 정제를 고쳐서 없앤다.

## stderr 끝 {{ stderr_tail | length }}줄
{% for line in stderr_tail %}
    {{ line }}
{% endfor %}

## 결함
{% for g in groups %}
- `{{ g.code }}` · {{ g.section }} / {{ g.layer }} · {{ g.count }}건
{% endfor %}

## 다시 재기

```bash
bin/report-wiki prep {{ repo }}
```

`원본 꼴이 틀렸다` 로 죽었으면 수집기 산출물(`out/codegraph-raw/` 의 `griffe.json` · `pycalls.json` · `full_class.json` · `roslyn-dump.json`)을 먼저 본다. `--resume` 은 `collect-graph` 부터 다시 돈다.

## 해결 불가

고쳐서 없앨 수 없는지는 이 글을 받은 에이전트가 판정한다. 그렇다면 `verify-graph.md` 끝의 양식으로 새 핸드오프를 남긴다.
