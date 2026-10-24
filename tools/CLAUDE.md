# tools/ — 어느 파이프라인도 아닌 것

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 부르는 쪽은 [`../runner/CLAUDE.md`](../runner/CLAUDE.md).

**세 축(러너·기계·시각) 어디에도 속하지 않는 것만 여기 둔다.** 크기가 아니라 소속이 기준이다.

| 자리 | 하는 일 | 부르는 곳 |
|---|---|---|
| `python.py` | 파이썬 해석기를 찾는다 — `$REPORT_PYTHON` → `.venv` → PATH | `doctor.py` · `runner/dispatch.py` · `runner/wiki/*.py` · `runner/run_mode1_5.py` |
| `template.py` | 리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 어긋나면 예외 | `viz/*.py` · `runner/wiki/build.py`. `runner/pipeline.py` 는 `TemplateError` 만 쓴다 |
| `doctor.py` | 이 컴퓨터에 무엇이 있고 없는지 한 화면. 필수가 없거나 하한보다 낮으면 exit 1. 하한은 `package.json` 의 `engines` · `PYTHON_MIN` · `DOT_MIN`, 파이썬 패키지 목록은 `requirements.txt` 에서 읽는다 | `npm run doctor` · `setup.sh` |
| `doctor_packages.py` | 받은 배포 이름 중 깔리지 않은 것을 한 줄로(`전부 있다` · `빠짐: …`). 이 저장소의 어느 것도 import 하지 않는다 | `doctor.py` 가 고른 파이썬의 자식 프로세스로 |
| `gen_readme.py` | 소스 독스트링에서 디렉토리별 `README.md` 를 생성한다. `--check` 면 낡았을 때 exit 1 | 게이트 "README 표류" · `test_gen_readme.py` |
| `scrub_local_paths.py` | 홈 아래 경로와 개인 식별자를 작업 트리·git 이력에서 지운다 | **아무 데서도 안 부른다** — 손으로 돌린다 |
| `setup.sh` | 저장소 의존성을 고정된 판으로 깐다 — `.venv` + `requirements.txt`, `npm@11.11.0 ci`. 끝에 doctor 를 돌린다. 시스템 도구는 깔지 않는다 | `npm run setup` · `.claude/settings.json` 의 SessionStart 훅(클라우드에서만) |
| `cloud_env.sh` | 클라우드 환경 설정 스크립트의 원본 — Graphviz 공식 `.deb` 와 그 라이브러리. 저장소에서는 아무도 부르지 않는다 | **claude.ai/code 환경 설정의 Setup script 칸에 손으로 붙여 넣는다** |

## 자주 쓰는 명령

저장소 루트에서 돌린다. 새 기계라면 `npm run setup` 이 먼저다.

```bash
npm run setup                                                         # .venv · node_modules 를 고정된 판으로 깔고 doctor
npm run doctor                                                        # 필수 · 선택 · 골든 환경변수 한 화면
.venv/bin/python tools/gen_readme.py machine runner viz tools          # README 넷을 다시 쓴다
.venv/bin/python tools/gen_readme.py --check machine runner viz tools  # 낡았으면 exit 1 (게이트)
.venv/bin/python -m pytest tools/ -q
```

## 왜 여기 모였나

- `python.py` 는 **경계를 넘는 접착제**다. 진입점 · 러너 · `doctor` 가 같은 해석기를 쓰게만 해 주고
  자신은 아무 파이프라인에도 속하지 않는다.
- `gen_readme.py` 는 **문서 생성기**다. 시그니처는 `machine/pycalls.py` 의 `signature_of` 를 그대로 쓴다 — 두 곳에서 만들면 어긋난다.
- `scrub_local_paths.py` 는 **저장소 위생 도구**다. 코드 지도도 HTML 도 만들지 않는다.
  `git-filter-repo` 로 이력을 다시 쓰므로 **되돌릴 수 없다** — 돌리기 전에 안전 번들을 만든다.

## 이 모듈이 소유하는 것 (Owns)

`tools/**`. **소유하지 않는 것** — 여기 코드는 남을 고치지 않는다. `scrub_local_paths.py` 만
예외로 작업 트리 전체를 고치지만, 그것은 사람이 명시적으로 부를 때뿐이다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `../runner/dispatch.py` · `../runner/wiki/*.py` · `../runner/run_mode1_5.py` → 여기 | `pythonPath()` 로 해석기를 찾는다 |
| `../viz/*.py` · `../runner/wiki/build.py` → 여기 | `template.py` 의 `render_file` 로 리소스 파일의 `{{이름}}` 자리를 채운다 — 보고서 뼈대 · DOT 머리 · 위키 사이트 설정 |
| `../runner/pipeline.py` → 여기 | 프롬프트 렌더 오류를 `template.py` 의 `TemplateError` 로 낸다. 프롬프트 글 자체는 Jinja2 가 렌더한다 |
| 여기 → `../machine/pycalls.py` | `gen_readme.py` 가 `signature_of` 를 import 한다. 셋 축 중 기계축으로 가는 유일한 화살표다 |
| 여기 → 바깥 | `git` · `dot` · `dotnet` · `clangd` 를 PATH 로 찾는다. **경로를 박지 않는다** |
