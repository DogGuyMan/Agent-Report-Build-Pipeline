# runner/ — 러너축. 순서를 잡고 남을 부른다

> 루트 나침반은 `../CLAUDE.md`. 결정론 기계는 `../machine/CLAUDE.md`, 시각은 `../viz/CLAUDE.md`.

**여기 있는 코드는 스스로 계산하지 않는다.** 단계의 순서를 잡고, 자식 프로세스를 띄우고,
시간을 재고, LLM 칸을 부른다. 계산은 전부 `../machine/` 과 `../viz/` 가 한다.

## 무엇이 여기 있나

| 자리 | 하는 일 |
|---|---|
| `run_mode1.py` | Mode 1 열 단계 — `lang-select→prep→warmup→survey-plan→survey→warmup-save→terms→wiki→build→check`. LLM 칸은 `lang-select`(1회) · `survey`(층별) · `wiki`(층별) 셋(`AGENT_STAGES`) |
| `run_mode1_5.py` | Mode 1.5 — `collect→[사람]→grade→emit`. 사람 칸에서 멈춘다. `author` 단계는 없다 |
| `run_mode2.py` | Mode 2 — `init→[LLM]→build→check` |
| `dispatch.py` | `bin/` 진입점 셋이 공유하는 명령 갈림길 (`run_dispatch`). `report` 만 예외다 |
| `wiki/` | Mode 1 의 얼갈이 — `prep` · `build` · `check` · `compdb` · `clang_doc` · `paths`. 전부 `.py` |
| `term/` | Mode 1.5 의 얼갈이 — `collect` · `quiz` · `emit`. **아직 `.mjs` 다** |

**`bin/` 은 왜 여기 없나.** `~/.zshrc` 가 `$REPO_ROOT/bin` 을 PATH 에 넣으므로 **옮기면 셸이 깨진다.**
성격은 러너축이지만 자리는 뿌리에 고정이다.

## 두 방향의 자식 프로세스 — 순환이 아니다

```
bin/*  →  dispatch.py  →  viz/*.py · runner/wiki/*.py · runner/term/*.mjs(아직 JS)
run_mode*.py  →  python runner/wiki/*.py · python viz/*.py   (되돌아오는 방향)
              →  python machine/*.py
```

**`dispatch.py` 는 확장자를 보고 해석기를 고른다** — `.py` 면 python, 아니면 node.
`runner/term/*.mjs` 셋이 아직 JS 라 이 갈림이 필요하다.

**Why — 서로 부르는데 왜 순환이 아닌가.** 파이썬 실행기가 최상위 오케스트레이터이고 얼갈이는
그 아래 한 단계다. 같은 프로세스 안에서 import 로 얽히는 것이 아니라 **자식 프로세스 경계**로
갈려 있어, 어느 쪽도 상대의 메모리를 보지 않는다.

**Gotcha — `run_mode1.py` 만 `machine/` 을 import 한다.** `declmap` · `survey_plan` · `warmup` 셋이다.
축이 갈린 뒤로 같은 폴더가 아니게 되어 파일 머리에서 `sys.path` 에 `machine/` 을 직접 넣는다.
다른 러너는 러너끼리만 import 하므로 그 줄이 없다.

## `.py` 는 직접 실행 가드를 둔다 — 규약

```python
if __name__ == "__main__":
    sys.exit(main())
```

가드가 없으면 시험이 import 하는 순간 CLI 본체가 돌아 `sys.exit()` 이 러너 자체를 죽인다.

## 이 모듈이 소유하는 것 (Owns)

`runner/**` 와 `../bin/**`. **소유하지 않는 것** — `../machine/*.py` 와 `../viz/*` 는
부르기만 하고 고치지 않는다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| `../bin/*` → 여기 | `report-wiki` · `report-spec` · `report-term` 셋이 `dispatch.py` 의 `runDispatch` 를 쓴다. `report` 만 `report-spec` 을 자식 프로세스로 띄운다 |
| 여기 → `../machine/*` | `wiki/prep.py`(normalize·facts) · `wiki/check.py`(verify_citations) · `run_mode1.py`(terms_db) |
| 여기 → `../viz/*` | `wiki/build.py`(demermaid) · `wiki/prep.py`(render_modules) · `dispatch` 표(init·build·check) |
| 여기 → `../tools/python.py` | 파이썬 해석기를 찾는다. 경로를 박지 않는다 |

## 비직관적인 것 (Gotchas)

- **Note — 위키 정적 사이트는 대상 저장소가 아니라 이 저장소 안에서 짓는다.** 대상에는
  `node_modules` 가 없어 `Cannot find package 'vitepress'` 로 죽는다. 산출물만 되돌아간다.
- **주의 — 대상 저장소의 전수조사 원본은 `<repo>/docs/codegraph/terms-reading.json` 이다.**
  이 저장소 자신의 것만 `../machine/terms-reading.json` 으로 옮겨져 있어 두 경로가 다르다.
  `run_mode1.py` 의 프롬프트 문자열은 **대상 저장소 쪽**을 말한다 — 고칠 때 헷갈리지 말 것.
- **Gotcha — Mode 2 의 원본 문서 자리 규칙이 두 곳에 중복돼 산다.** `run_mode2.py` 의
  `DOC_DIRS` 와 `../viz/init.py` 의 `DOC_DIRS` 가 같은 값이어야 한다(`specs/` 는
  `-design.md`, `plans/` 는 접미사 없음). 언어가 달라 한 곳에 못 모은다 — 한쪽만 고치면
  `init` 은 찾는데 러너는 못 찾는 어긋남이 조용히 생긴다. 전체 표는 `../viz/CLAUDE.md` 에 있다.
