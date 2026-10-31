# tools/ — 저장소 유지보수. 어느 mode 의 파이프라인도 아니다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 세 mode 가 함께 쓰는 유틸은 [`../src/core/CLAUDE.md`](../src/core/CLAUDE.md) 의 `src/common/` 행.

**환경 점검 · README 생성 · 계약 생성 · 설치 · 경로 세척만 여기 둔다.** 실행 중에 mode 가 부르는 코드는 `src/common/` 에 산다.

| 자리 | 하는 일 | 부르는 곳 |
|---|---|---|
| `doctor.py` | 이 컴퓨터에 무엇이 있고 없는지 한 화면. 필수가 없거나 하한보다 낮으면 exit 1. 하한은 `package.json` 의 `engines` · `PYTHON_MIN` · `DOT_MIN`, 파이썬 패키지 목록은 `requirements.txt` 에서 읽는다 | `npm run doctor` · `setup.sh` |
| `doctor_packages.py` | 받은 배포 이름 중 깔리지 않은 것을 한 줄로(`전부 있다` · `빠짐: …`). 이 저장소의 어느 것도 import 하지 않는다 | `doctor.py` 가 고른 파이썬의 자식 프로세스로 |
| `gen_readme.py` | 소스 독스트링에서 디렉토리별 `README.md` 를 생성한다. `--check` 면 낡았을 때 exit 1 | 게이트 "README 표류" · `test_gen_readme.py` |
| `gen_contract.py` | 계약 리소스 `contracts/mode1-artifacts.v1.json` 과 지문 `.sha256` 을 생산자 형(`src/codewiki/python/machine/manifest.py` · `src/codewiki/python/machine/terms_db.py`)에서 낸다. `--check` 면 낡았을 때 exit 1 | 사람 · `test_gen_contract.py` |
| `gen_contract_types.py` | 계약 JSON 에서 소비자 형 `src/common/contract_types.py` 를 낸다(생성물 — 손대지 않는다). `--check` 면 낡았을 때 exit 1 | 사람 · `test_gen_contract_types.py` |
| `scrub_local_paths.py` | 홈 아래 경로와 개인 식별자를 작업 트리·git 이력에서 지운다 | **아무 데서도 안 부른다** — 손으로 돌린다 |
| `setup.sh` | 저장소 의존성을 고정된 판으로 깐다 — `.venv` + `requirements.txt`, `npm@11.11.0 ci`. 끝에 doctor 를 돌린다. 시스템 도구는 깔지 않는다 | `npm run setup` · `.claude/settings.json` 의 SessionStart 훅(클라우드에서만) |
| `cloud_env.sh` | 클라우드 환경 설정 스크립트의 원본 — Graphviz 공식 `.deb` 와 그 라이브러리. 저장소에서는 아무도 부르지 않는다 | **claude.ai/code 환경 설정의 Setup script 칸에 손으로 붙여 넣는다** |

해석기 탐색(`python.py`)과 리소스 자리 채우기(`template.py`)는 세 mode 가 함께 쓰므로 2026-10-31 에 `src/common/` 으로 갔다.

## 자주 쓰는 명령

저장소 루트에서 돌린다. 새 기계라면 `npm run setup` 이 먼저다.

```bash
npm run setup                                                         # .venv · node_modules 를 고정된 판으로 깔고 doctor
npm run doctor                                                        # 필수 · 선택 · 골든 환경변수 한 화면
.venv/bin/python tools/gen_readme.py src/codewiki/python/runner src/codewiki/python/machine src/codewiki/python/viz src/term/python/runner src/spec/python/runner src/spec/python/viz src/core src/common tools   # README 아홉을 다시 쓴다
.venv/bin/python tools/gen_readme.py --check src/codewiki/python/runner src/codewiki/python/machine src/codewiki/python/viz src/term/python/runner src/spec/python/runner src/spec/python/viz src/core src/common tools   # 게이트
.venv/bin/python -m pytest test/tools -q
```

## 왜 여기 모였나

- `gen_readme.py` 는 **문서 생성기**다. 시그니처는 `src/codewiki/python/machine/pycalls.py` 의 `signature_of` 를 그대로 쓴다 — 두 곳에서 만들면 어긋난다.
- `scrub_local_paths.py` 는 **저장소 위생 도구**다. 코드 지도도 HTML 도 만들지 않는다.
  `git-filter-repo` 로 이력을 다시 쓰므로 **되돌릴 수 없다** — 돌리기 전에 안전 번들을 만든다.

## 이 모듈이 소유하는 것 (Owns)

`tools/**`. **소유하지 않는 것** — 여기 코드는 남을 고치지 않는다. `scrub_local_paths.py` 만
예외로 작업 트리 전체를 고치지만, 그것은 사람이 명시적으로 부를 때뿐이다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../src/common/python.py` | `doctor.py` 가 쓸 해석기를 고른다 |
| 여기 → `../src/codewiki/python/machine/` | `gen_readme.py` 가 `pycalls.signature_of` 를, `gen_contract.py` 가 `manifest` · `terms_db` 의 형을 import 한다 |
| 여기 → `../src/common/contract_types.py` | `gen_contract_types.py` 가 쓴다(생성물) |
| 여기 → 바깥 | `git` · `dot` · `dotnet` · `clangd` 를 PATH 로 찾는다. **경로를 박지 않는다** |
