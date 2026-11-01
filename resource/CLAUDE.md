# resource/ — 코드가 읽기만 하는 것들. mode 별로 산다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 규칙의 출처는 결정 0012(프롬프트는 Jinja2) 와 결정 0014(자리).

| 자리 | 무엇 | 읽는 코드 |
|---|---|---|
| `codewiki/prompts/<단계>.md` · `codewiki/faults.toml` | Mode 1 LLM 단계의 프롬프트(파일 이름 = 단계 이름, `<!-- section: 이름 -->` 절) · 결함 표 | `src/codewiki/python/runner/mode1/context.py` 의 `PROMPT_DIR` · `FAULTS_PATH` |
| `codewiki/templates/` | VitePress 설정 · 모듈 · 클래스 DOT 의 머리와 범례 | `src/codewiki/python/runner/wiki/build.py` · `src/codewiki/python/viz/render_*.py` 의 `TEMPLATES` |
| `codewiki/config.toml` | Mode 1 의 Model id 와 비용 어림 | `context.py` 의 `CONFIG_PATH` |
| `codewiki/samples/` | 수집기 출력의 골든 꼴(C++ · C# Unity)과 `OBSERVATION-template.md` | `codebase-terms-survey` 스킬 · 골든 시험 |
| `codewiki/terms-reading.json` | 이 저장소 자신의 전수조사 레코드(자기호스팅) | `context.py` 의 `reading_path()` · `terms_db.py --reading` |
| `term/prompts/ask.md` | Mode 1.5 가 사람에게 묻는 세션의 글 | `src/term/python/runner/run_mode1_5.py` |
| `spec/prompts/agent.md` · `spec/templates/report/` · `spec/config.toml` | Mode 2 에이전트 프롬프트 · 보고서 뼈대 다섯 · 원본 문서 자리 규칙과 Model 별명 | `src/spec/python/runner/run_mode2.py` · `src/spec/python/viz/init.py` · `src/spec/python/viz/build.py` |

**규칙.** 프롬프트는 단계당 한 파일, 글은 Jinja2 — 반복 · 빈 값 대체 · 조건부 절을 파일 안에 쓴다. **템플릿은 꼴만, 데이터 결정은 단계.** 파일 템플릿의 자리표시는 `{{이름}}` 하나(`src/common/template.py`). 파이썬은 여기 것을 읽기만 한다. `qa/gates/test_prompt_resources.py` 가 막는다.

두 mode 가 같은 리소스를 읽게 되면 `resource/common/` 을 더한다(0014 의 되살릴 조건).

## 이 모듈이 소유하는 것 (Owns)

`resource/**`. 소유하지 않는 것 — 위 표의 "읽는 코드"와, 프롬프트를 검사하는 `qa/gates/test_prompt_resources.py`. 여기 파일은 데이터라서 import 되지 않는다.

## 새 프롬프트 단계를 더하는 법 (How to)

1. `resource/<mode>/prompts/<단계>.md` 를 만든다. 파일 이름이 단계 이름이고, 안은 `<!-- section: 이름 -->` 으로 가른다.
2. 단계가 `prompt_names` 에 `"<파일>#<절>"` 을 선언한다(절이 없는 파일은 `"<파일>"`). 파이썬은 `PromptResource.load_prompt` 로 읽는다.
3. 글에 쓴 Jinja2 이름과 단계가 넘기는 값을 맞춘다. 무엇을 싣는가는 단계가 정하고, 글은 꼴만 갖는다.

고친 뒤에는 게이트로 파일과 절의 1:1 · Jinja2 컴파일 · 줄 끝 공백을 한 번에 본다:

```bash
.venv/bin/python -m pytest qa/gates/test_prompt_resources.py -q
```

## 비직관적인 것 (Gotchas)

- **Gotcha:** 프롬프트 글이 저장소 안 경로를 실행시키면 — 예: `annotate-symbols.md` 의 `{{root}}/src/codewiki/python/runner/check_shard.py` — 그 파일을 옮길 때 여기도 함께 고친다. 코드 쪽 경로 치환 도구는 이 폴더를 보지 않는다.
- **Warning:** 프롬프트 글에 `{#` 를 쓰면 Jinja2 가 주석 시작으로 읽는다. 줄 끝 공백과 함께 게이트가 막는다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `../src/**` → 여기 | 위 표의 "읽는 코드"가 읽기만 한다. 경로 상수는 `context.py` 의 `PROMPT_DIR` · `FAULTS_PATH` · `CONFIG_PATH` 처럼 코드 쪽에 있다 |
| `../qa/gates/test_prompt_resources.py` → 여기 | 프롬프트 · 결함 표 · 템플릿이 코드와 맞는지 검사한다 |
| 여기 → 바깥 | **없다.** 이 폴더는 아무것도 import 하지 않는다 |
