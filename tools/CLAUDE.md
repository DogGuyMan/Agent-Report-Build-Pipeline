# tools/ — 어느 파이프라인도 아닌 것

> 루트 나침반은 `../CLAUDE.md`.

**세 축(러너·기계·시각) 어디에도 속하지 않는 것만 여기 둔다.** 크기가 아니라 소속이 기준이다.

| 자리 | 하는 일 | 부르는 곳 |
|---|---|---|
| `python.mjs` | 파이썬 해석기를 찾는다 — `$REPORT_PYTHON` → `.venv` → PATH | `doctor.mjs` · `runner/wiki/*.mjs` |
| `doctor.mjs` | 이 컴퓨터에 무엇이 있고 없는지 한 화면. 필수가 없으면 exit 1 | `npm run doctor` |
| `scrub_local_paths.py` | 홈 아래 경로와 개인 식별자를 작업 트리·git 이력에서 지운다 | **아무 데서도 안 부른다** — 손으로 돌린다 |

## 왜 여기 모였나

- `python.mjs` 는 **경계를 넘는 접착제**다. Node 쪽이 파이썬 쪽을 부를 수 있게만 해 주고
  자신은 아무 파이프라인에도 속하지 않는다.
- `scrub_local_paths.py` 는 **저장소 위생 도구**다. 코드 지도도 HTML 도 만들지 않는다.
  `git-filter-repo` 로 이력을 다시 쓰므로 **되돌릴 수 없다** — 돌리기 전에 안전 번들을 만든다.

**Gotcha — `scrub_local_paths.py` 는 파이썬인데 Node 폴더(`scripts/`)에 살고 있었다.**
축을 나눌 때 드러난 것이고, 부르는 곳이 0곳이라 옮겨도 아무것도 깨지지 않았다(🔵 2026-08-30 실측).

## 이 모듈이 소유하는 것 (Owns)

`tools/**`. **소유하지 않는 것** — 여기 코드는 남을 고치지 않는다. `scrub_local_paths.py` 만
예외로 작업 트리 전체를 고치지만, 그것은 사람이 명시적으로 부를 때뿐이다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `../runner/wiki/*.mjs` → 여기 | `pythonPath()` 로 해석기를 찾는다 |
| 여기 → 바깥 | `git` · `dot` · `dotnet` · `clangd` 를 PATH 로 찾는다. **경로를 박지 않는다** |
