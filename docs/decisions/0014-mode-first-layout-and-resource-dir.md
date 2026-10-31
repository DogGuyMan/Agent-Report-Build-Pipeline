# 결정 0014 — 1차 축은 mode 다. 리소스는 `resource/` 한 자리에 두고, 시험과 규약 게이트를 가른다

**상태** 확정 · 2026-10-31 · 사용자 판단 (아홉 축 질의 — 묶음 넷 · 열네 문항)

**이행** 아직 없다. 두 저장소 분리 계획(0011)의 R · A · K · M 이 2026-10-31 에 끝났으므로(`main` 병합 `6c4009d`) **Phase B(실제 분리) 앞**에 실행한다 — 사양
`docs/superpowers/specs/2026-10-31-directory-reorg-design.md`(영어 정본 · `.ko.md` 번역본) ·
계획 `docs/superpowers/plans/2026-10-31-directory-reorg.md`(영어 정본 · `.ko.md` 번역본).
그 전까지 코드와 문서의 경로는 지금 구조다.

**무엇을.**
- **1차 축을 성격(2026-08-30 "성격축 셋")에서 mode 로 바꾼다.** 최상위 `codewiki/`(Mode 1) · `term/`(Mode 1.5) ·
  `spec/`(Mode 2). 그 아래 2차 축은 언어(`python/` · `csharp/` · `typescript/`), 3차 축은 지금의 성격축
  (`runner/` · `machine/` · `viz/`)을 그대로 둔다 — import 경로와 파일 이름이 살고 이름 충돌이 0 이다.
- 세 mode 가 함께 쓰는 것은 둘뿐이고 자리를 따로 준다 — `core/`(단계 기계 `pipeline.py` · `measure.py` · `dispatch.py`) ·
  `common/`(`python.py` · `template.py`). `tools/` 는 저장소 유지보수(doctor · setup · gen_readme)만 남는다.
- **리소스는 전부 `resource/<mode>/`** — 프롬프트 · 결함 표 · 파일 템플릿 · 설정(`config/*.toml`) · 실측 자료
  (수집기 골든 꼴 `samples/` · 이 저장소의 전수조사 레코드 `terms-reading.json`). 0012 의 "프롬프트는 단계 옆
  `runner/**/prompts/`" 자리 조항과 루트 `CLAUDE.md` 최우선 규약의 자리 문장을 이것으로 고친다. 0012 의 나머지
  (Jinja2 · 절 표식 · 엄격 검사 · 템플릿은 꼴만)는 그대로다.
- **시험과 규약 게이트를 가른다** — `test/<mode|core|common|tools>/` 에 모듈 시험 전부, `qa/gates/` 에 저장소 규약
  게이트(문서 인용 · Any · 리소스 분리 · 위키 표류), `qa/evals/` 에 실행기 측정값.
- 문서는 `docs/superpowers/` 계층을 유지하고 `docs/notes/`(흩어진 분석 문서) · `docs/research/`(루트의 `reports/` ·
  `research_notes/`)를 더한다.
- 폐지된 xmldoc 잔재(0010)를 이때 전부 지운다 — `machine/xmldoc.py` · `test_xmldoc.py` · `comments.xml` · 소스의
  `# <include …/>` 블록. 줄 번호는 지운 줄 수만큼 결정론으로 다시 센다.
- 이름은 `wiki` 대신 `codewiki` 다 — `docs/wiki/`(이 저장소의 RAG)와 `runner/wiki/`(prep · build · check)와
  겹치지 않게. 0011 의 새 저장소 이름 `codebase-wiki` 와도 가깝다.

**사용 규칙.**
- 순수 이동과 알려진 삭제만 한다. 옮긴 파일 안의 수정은 줄 수를 바꾸지 않는 한 줄 치환(`sys.path` · 경로 문자열)뿐이다.
  그래야 `docs/wiki` 의 `파일:줄` 인용 203건과 `terms-reading.json` 의 `where` 3,053건을 기계로 정확히 옮길 수 있다
  (🔵 2026-10-31 실측).
- 아카이브(`docs/handoffs/` · `docs/superpowers/` · `docs/my.self/`)의 옛 경로는 고치지 않는다 — 2026-08-30 축 이동
  (`c1e4496`)과 같은 선례다.
- Mode 1 재굽기는 하지 않는다(2026-09-19 실측 $57). 위키 장 이름(`machine-*.md` 등)은 다음 재굽기까지 옛 이름이다.
- 분리 계획 Phase B 는 `codewiki/` 를 통째로 떼어내는 것이 된다.

**고르지 않은 것.**
- 이름 `mode1 · mode1_5 · mode2` — 문서의 호칭과는 같지만 1.5 표기가 어색하다. `wiki · term · spec` 은 `wiki` 가
  세 겹으로 겹쳐 최상위만 `codewiki` 로.
- 언어 아래 평평하게 — Mode 1 파이썬 약 40 파일이 한 폴더에 놓이고 `clang_doc.py` 둘과 `wiki.py`/`wiki/` 가 충돌한다.
- 파이썬은 언어 폴더 없이 — "언어별 폴더" 요청을 파이썬에만 빼는 것이라 고르지 않았다.
- `core` 없이 `common` 하나 · `core` = 기계축 전체.
- `resource` 에 실측 자료만 · 실측 자료 + config 만.
- `docs/` 를 `plans/` · `specs/` 로 평평하게 — superpowers 스킬의 기본 경로를 바꿔야 한다.
- 아카이브까지 경로 치환 · 위키 · 레코드 재굽기.
- xmldoc 잔재를 두고 이동만 · 파일만 지우고 블록은 둔다.
- 분리를 대체(0011 을 뒤집음) · 분리를 끝낸 뒤 각 저장소에 적용.

**대가로 받아들인 것.** import 깊이가 두 단 는다(`codewiki.python.runner.mode1.context`). `python` 이 패키지 이름이 된다.
컨텍스트 문서 일곱 · `ARCHITECTURE.md` · `README.md` · 생성 README 아홉 · 설정 파일 여섯 · 게이트 넷의 경로 목록을 한 번에
고친다. 층 분포 고정값 시험은 값이 또 바뀐다(기계마다 다른 원인을 먼저 본다는 규약대로 이 결정은 손대지 않는다).

**새 구조 공개(설계 규율 §2.5 — 🔵 2026-10-31 실측).**
1. 구현자 — `core/` 3 파일 · `common/` 2 파일 · `qa/gates/` 4 파일 · `resource/` 의 리소스 파일(프롬프트 6 · 결함 표 1 ·
   템플릿 9 · 설정 2 · 골든 꼴 24 · 레코드 1).
2. 소비자 — `pipeline.py` 16 파일 · `measure.py` 7 · `dispatch.py` 진입점 3 · `python.py` 5 · `template.py` 6.
   리소스 소비자는 각 단계 클래스(`prompt_names`)와 `render_file` 호출처.
3. 삭제 시험 — `core/` · `common/` 을 없애면 다섯 파일이 어느 mode 폴더에도 속하지 못해 지금처럼 `runner/` · `tools/` 에
   섞여 남는다. 0011 의 Phase B 가 양쪽에 복제할 "공통 커널" 이 바로 이 다섯이라, 자리를 따로 두면 복제 범위가 폴더 이름으로 보인다.
4. 계획과의 관계 — 0011 안. 분리의 전 단계로 M 뒤 · B 앞에 넣는다.

**되살릴 조건.**
- 한 mode 안의 성격축 폴더가 파일 둘 이하로 줄면 그 층을 걷는다.
- `resource/` 안의 파일을 두 mode 가 함께 읽는 일이 생기면 `resource/common/` 을 더한다.

계획서: `docs/superpowers/plans/2026-10-31-directory-reorg.md`
