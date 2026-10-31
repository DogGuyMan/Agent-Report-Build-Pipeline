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

**프롬프트 글이 저장소 안 경로를 실행시키면** — 예: `annotate-symbols.md` 의 `{{root}}/src/codewiki/python/runner/check_shard.py` — 그 파일을 옮길 때 여기도 함께 고친다. 코드 쪽 경로 치환 도구는 이 폴더를 보지 않는다.

두 mode 가 같은 리소스를 읽게 되면 `resource/common/` 을 더한다(0014 의 되살릴 조건).
