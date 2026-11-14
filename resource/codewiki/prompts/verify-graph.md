# 코드 지도 검사 실패 — 이어받기

- 대상 `{{ repo }}`
- 지도 `{{ codegraph }}`
- 언어 `{{ language }}` · 수집기 `{{ source_tool }}` · 커밋 `{{ repo_commit }}`
- 결함 {{ total }}건. 전부는 같은 폴더의 `graph-faults.json` 에 있다.
- 수행한 검사 {{ checks_run }} · 전수조사 적합 {{ fit }}

**검사를 완화해 통과시키지 말라.** 결함은 지도를 만든 쪽(수집기 · 정제)을 고쳐서 없앤다. `verify_graph.py` 의 규칙은 그 규칙이 틀렸다는 근거가 있을 때만 바꾸고, 그 근거를 끝의 "해결 불가" 양식으로 남긴다.

## 결함 — 많은 순
{% for g in groups %}

### `{{ g.code }}` · {{ g.section }} / {{ g.layer }} · {{ g.count }}건
{% for f in g.examples %}
- `{{ f.at }}` — {{ f.detail }}
{% endfor %}
{% endfor %}

## 층마다 볼 곳

- **V0 읽기** — 지도 파일이 없거나 JSON 이 아니다. `collect-graph` 가 끝까지 돌았는지, 정제가 도중에 죽지 않았는지 본다.
- **V1 꼴** — 정제가 계약(`src/codewiki/python/machine/codegraph_types.py`)의 필수 열쇠나 형을 빠뜨렸다. 그 언어의 `normalize_*` 와 `_assemble` 을 본다.
- **V1 external-only** — 1차 노드가 없다: 수집기가 대상 폴더를 못 봤거나 R1 이 전부를 외부로 접었다.
- **V2 정합** — 지도 안에서 서로 어긋난다(겹친 id · 끊긴 간선 · 외부 노드 규칙 · 모듈 목록). 정제의 접기 규칙 R1~R7 을 본다.
- **V2 module-dep-mismatch** — `_assemble` 의 모듈 의존 유도(normalize.py)와 지도의 `depends_on` 이 다르다.
- **V3 근거** — 노드 · 간선의 `file:line` 이 지금 저장소와 맞지 않는다. 지도가 낡았으면 다시 수집하면 사라진다.
- **최신성 source-drift / generation-mismatch / freshness-unknown** — 지도를 만든 뒤 소스가 바뀌었거나, manifest 가 다른 지도의 것이거나, prep 밖에서 만든 지도다. 다시 수집하면 사라진다 — 검사를 완화하지 않는다.
- **V4 장부 unknown-kind / unresolved-drop / report-stale** — normalize.py 의 DROP_CLASS 와 표본을 본다. 정제를 고쳐 사유를 없앤다 — 표의 등급을 바꿔 통과시키지 않는다.
- **범위 language-not-collected / coverage-gap** — 막지 않는다. 지도가 말하지 않는 파일 · 언어다. 전수조사 결과에 그 범위를 적는다.
- **범위 inventory-stale** — inventory 가 없거나 이번 수집의 것이 아니다. 다시 수집하면 사라진다.
- **수집 collect-failed** — collect-failure.json 의 단계 · stderr 꼬리를 본다.

## 보강 후보

1. 수집 보강 — 수집기가 그 정보를 내게 한다
2. 정제 보강 — 수집기 원본에는 있는데 정제가 버리거나 틀리게 옮긴다
3. 슈퍼셋 스키마 — 언어마다 다른 칸을 공통 계약에 선택 칸으로 더한다(계약 변경이라 사용자 승인이 먼저다)
4. 언어별 외래키 — 언어 전용 정보를 별도 파일에 두고 지도에서는 id 로만 가리킨다

## 다시 재기

```bash
.venv/bin/python src/codewiki/python/runner/run_mode1.py {{ repo }} --resume
```

`--resume` 은 `collect-graph` 부터 다시 돈다 — 고친 수집기 · 정제가 지도에 들어간 뒤 검사한다.

## 해결 불가

고쳐서 없앨 수 없는지는 기계가 아니라 이 글을 받은 에이전트가 판정한다. 그렇다면 아래를 채운 새 핸드오프를 남긴다.

- 결함 코드와 예시
- 수집 · 정제로 고칠 수 없는 까닭(근거 `file:line`)
- 대안 — 검사 규칙을 바꿀 근거, 또는 이 언어의 지도를 읽는 파이프라인을 따로 구체화하는 안
