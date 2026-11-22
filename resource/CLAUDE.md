# resource/ — 코드가 읽기만 하는 것들. mode 별로 산다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 자리 규칙의 출처는 결정 0014.

| 자리 | 무엇 | 읽는 코드 |
|---|---|---|
| `codewiki/prompts/<단계>.md` · `codewiki/faults.toml` | Mode 1 LLM 단계의 프롬프트(파일 이름 = 단계 이름, `<!-- section: 이름 -->` 절) · 결함 표. `verify-graph.md` · `collect-graph.md` 는 LLM 을 부르지 않는 `verify-graph` · `collect-graph` 가 결함을 이어받을 사람 · 에이전트에게 남기는 핸드오프 템플릿이다 — 앞의 것은 검사 결함을, 뒤의 것은 죽은 수집 단계와 stderr 끝줄을 싣는다 | `src/codewiki/python/runner/mode1/context.py` 의 `PROMPT_DIR` · `FAULTS_PATH` |
| `codewiki/templates/` | VitePress 설정 · 모듈 · 클래스 DOT 의 머리와 범례 | `src/codewiki/python/runner/wiki/build.py` · `src/codewiki/python/viz/render_*.py` 의 `TEMPLATES` |
| `codewiki/config.toml` | Mode 1 의 Model id 와 비용 어림 | `context.py` 의 `CONFIG_PATH` |
| `codewiki/samples/` | 수집기 출력의 골든 꼴(C++ · C# Unity)과 `OBSERVATION-template.md` | `codebase-terms-survey` 스킬 · 골든 시험 |
| `codewiki/terms-reading.json` | 이 저장소 자신의 전수조사 레코드(자기호스팅) | `context.py` 의 `reading_path()` · `terms_db.py --reading` |
| `term/prompts/ask.md` | Mode 1.5 가 사람에게 묻는 세션의 글 | `src/term/python/runner/run_mode1_5.py` |
| `spec/prompts/agent.md` · `spec/templates/report/` · `spec/config.toml` | Mode 2 에이전트 프롬프트 · 보고서 뼈대 다섯 · 원본 문서 자리 규칙과 Model 별명 | `src/spec/python/runner/run_mode2.py` · `src/spec/python/viz/init.py` · `src/spec/python/viz/build.py` |

**규칙.** 프롬프트는 단계당 한 파일, 글은 Jinja2 — 반복 · 빈 값 대체 · 조건부 절을 파일 안에 쓴다. **템플릿은 꼴만, 데이터 결정은 단계.** 파일 템플릿의 자리표시는 `{{이름}}` 하나(`src/common/template.py`). 파이썬은 여기 것을 읽기만 한다. `qa/gates/test_prompt_resources.py` 가 막는다.

**프롬프트 글이 저장소 안 경로를 실행시키면** — 예: `annotate-symbols.md` 의 `{{root}}/src/codewiki/python/runner/check_shard.py` — 그 파일을 옮길 때 여기도 함께 고친다. 코드 쪽 경로 치환 도구는 이 폴더를 보지 않는다.

**전수조사의 배치 · 2패스 세션은 허용된 명령만 돈다.** 그 목록은 `src/codewiki/python/runner/mode1/survey.py` 의 `AnnotateSymbolsStage.session_calls` 하나이고, 허용 규칙과 프롬프트의 알림 절(`annotate-symbols.md` 의 `allowed`)이 둘 다 거기서 나온다. `annotate-symbols.md` 가 세션에 시키는 명령을 더하거나 바꾸면 같은 변경에서 그 목록도 고친다 — `test/codewiki/test_mode1.py` 의 `test_세션_종류마다_허용된_명령은_제_샤드의_검문_하나이고_프롬프트가_시키는_명령과_같다` 와 `test_프롬프트가_시키는_명령은_전부_그_세션의_허용_규칙이_덮는다` 가 어긋남을 잡는다. 비노드 세션은 허용 규칙 아래에 있지 않아 `nonnode` 절에는 알림 자리가 없다. 어느 종류가 규칙을 받는지는 같은 파일의 `AnnotateSymbolsStage.kind_args` 가 정하고, 규칙을 받는 종류의 절에만 알림을 싣는다(`test_허용_규칙과_알림은_같은_종류에_함께_실린다`).

두 mode 가 같은 리소스를 읽게 되면 `resource/common/` 을 더한다(0014 의 되살릴 조건).
