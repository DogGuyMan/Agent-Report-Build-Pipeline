---
description: "report-builder 저장소의 파이썬 규약. 실측으로 확인한 이 저장소의 실제 관행이다."
globs: "**/*.py"
alwaysApply: false
---

# Python Rules — report-builder

> 이 문서는 일반론이 아니라 **이 저장소의 실측 관행**이다.
> 충돌하면 루트 `CLAUDE.md` 와 모듈 `CLAUDE.md` 가 우선한다.
> 수치는 🔵 2026-08-31 에 `git ls-files '*.py'` 66개 파일(15,444줄, 시험 477개)을 실제로 세어 얻었다.

## 이 저장소가 무엇인지부터

**웹 서비스가 아니다.** 코드베이스를 읽어 보고서와 위키를 굽는 **CLI 도구 모음**이다.
서버도 데이터베이스도 인증도 요청 처리도 없다.

그래서 다음 주제는 **이 저장소에 존재하지 않는다.** 여기에 규칙을 쓰지 않는다 —
없는 것에 대한 규칙은 지킬 수도 어길 수도 없고, 읽는 사람을 헷갈리게만 한다:

> Flask · Blueprint · SQLAlchemy · Alembic · 마이그레이션 · 커넥션 풀 · ORM 모델 ·
> OAuth · 세션 · CSRF · bcrypt · REST · HTTP 상태 코드 · 레이트 리밋 · CORS ·
> HTTPS · 캐싱 · 페이지네이션 · 백그라운드 작업

🔵 서드파티 의존은 `requirements.txt` 의 **다섯 개가 전부**다 —
`networkx` · `numpy` · `scipy` · `pytest` · `griffe`.
**표준 라이브러리로 풀 수 있으면 새 의존성을 더하지 않는다.**

---

## 1. 구조 — src-layout 을 쓰지 않는다

성격축으로 가른 **최상위 디렉토리 넷**이다. 언어가 아니라 **하는 일**로 가른다.

| 자리 | 가르는 질문 |
|---|---|
| `runner/` + `bin/` | **시키는가** — 순서를 잡고 자식 프로세스를 띄운다 |
| `machine/` | **계산하는가** — 정적 수집·정규화·용어 DB. 그림을 그리지 않는다 |
| `viz/` | **그리는가** — HTML·SVG·다이어그램 |
| `tools/` | 셋 어디에도 속하지 않는 것만 |

- `src/패키지명/` 을 만들지 않는다. 새 최상위 디렉토리를 만들기 전에 위 네 질문에 답해 본다.
- 각 디렉토리의 `README.md` 는 **`tools/gen_readme.py` 가 소스에서 생성한다.** 손으로 고치지 않는다.
- 모듈·클래스·함수의 목록과 역할은 그 `README.md` 에 있다. `CLAUDE.md` 는 나침반이지 지도가 아니다.

### 시험 파일의 자리

🔵 두 관례가 공존한다 — `machine/` · `runner/` · `tools/` 는 **코드 옆**,
그 밖 일부는 `test/`. **아직 정리되지 않았다.**

**새 시험은 그 코드가 사는 디렉토리 옆에 둔다.** `tests/` 라는 별도 디렉토리를 만들지 않는다.

### import 꼴 — 두 가지가 산다

```python
# (가) 패키지 import — runner/ viz/ tools/ 는 __init__.py 를 갖는다
from runner.dispatch import run_dispatch
from viz.check import countScripts        # ⚠ 이 이름은 드리프트다 — §2 를 보라

# (나) 평평한 import — machine/ 은 __init__.py 가 없다
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clang_doc as CD
```

🔵 (가) 25곳 · (나) 33곳. **상대 import(`from .x import y`)는 0곳이다 — 쓰지 않는다.**

⚠ **(나)를 바꾸지 마라.** `machine/pycalls.py` 의 이름 해소기가 이 평평한 관습 위에 서 있다.
디렉토리 뿌리로 거르도록 고쳤더니 모듈을 넘는 호출이 338개에서 1개로 떨어진 적이 있다.

---

## 2. 코드 스타일

### 이름

| 대상 | 표기 | 실측 |
|---|---|---|
| 함수 · 변수 | `snake_case` | 🔵 299 / 348 |
| 클래스 · TypedDict | `PascalCase` | |
| 상수 | `UPPER_CASE` | |
| 내부용 | 앞에 `_` 하나 | |

⚠ **드리프트 경고 (🔵 2026-08-31 실측).** camelCase 함수가 **49개** 있다.
전부 JavaScript 에서 옮겨 온 파일에 몰려 있다 — `viz/init.py`(8) · `viz/link_paths.py`(6) ·
`viz/check.py`(5) · `runner/wiki/compdb.py`(5) 등.

**JS 이름을 그대로 들고 오지 마라.** `parseSpecFilename` → `parse_spec_filename`,
`prepPlan` → `prep_plan`. 이름을 바꾸면 그것을 부르는 시험도 함께 고친다.
(이미 들어온 49개를 언제 정리할지는 저장소 주인이 정한다 — 새로 늘리지만 않으면 된다.)

### 줄 길이 — 강제하는 도구가 없다

🔵 중앙값 42자 · p95 120자 · 100자 초과 12%. **Black 도 isort 도 설정돼 있지 않다.**
포매터를 새로 도입하지 마라 — 전체 재포맷은 diff 를 못 읽게 만든다.

**100자쯤을 목표로 하되 규칙이 아니다.** 표·긴 문자열·f-string 은 넘겨도 된다.

⚠ `# <include file="machine/comments.xml" …/>` 로 시작하는 **주입 블록 세 줄은 길이를 재지 않는다.**
`machine/xmldoc.py` 가 자동 생성하는 것이라 **줄바꿈으로 접으면 검사가 깨진다.**

### 주석 — 현 상황만 적는다

| 쓴다 | 쓰지 않는다 |
|---|---|
| 함수·클래스마다 한 줄 요약 | `**왜 필요한가.**` 절 |
| 코드가 의존하는 형식·동작 사실 | `🔵 2026-08-29 실측 — …` 날짜 붙은 관찰 |
| 비직관적 제약과 그 즉각적 귀결 | `~에 뒤집힌 결정` · `이전 판은 ~라고 적었다` |
| | `거울 함정 경계 — …` 같은 설계 철학 |
| | 관찰 보고서·계획서·핸드오프 참조 |

**형식·동작 사실은 남긴다** — 지우면 다음 사람이 버그를 만든다.
예: `clang-doc 의 Namespace 는 안쪽부터 온다. 뒤집어야 한다.` 날짜와 수치만 뺀다.

**주장이 아니라 시험으로 적는다.** 바깥 도구의 동작에 기대는 사실은 주석 대신 그것을 고정하는
시험을 두고, 주석은 그 이름을 가리킨다. 주석은 썩지만 시험은 깨진다.
(`machine/test_external_contracts.py` 가 그 자리다.)

🔵 주석의 76%(2201/2909줄)가 한국어다. **한국어 + 영문 기술용어 병기**로 쓴다.
약어와 압축 표현을 피한다.

---

## 3. 타입 힌트 — pyright strict 다

🔵 `pyrightconfig.json` 이 `"typeCheckingMode": "strict"` 이고 `pythonVersion` 은 `3.14` 다.
`npm run typecheck:py` 가 **0 errors** 여야 한다.

- **모든 인자와 반환에 타입을 붙인다.** strict 가 강제한다.
- **`X | None` 을 쓴다. `Optional[X]` 를 쓰지 마라.**
  🔵 `| None` 222곳 vs `Optional[` 12곳 — 그리고 그 12곳은 전부 JS 에서 옮겨 온 파일이다.
  `Union[A, B]` 도 마찬가지로 `A | B` 로 쓴다.
- **`dict[str, int]` 을 쓴다. `Dict`/`List`/`Tuple` 을 `typing` 에서 가져오지 마라.**
  🔵 옛 별칭이 남은 파일은 `tools/python.py` 와 `viz/wrap_terms.py` **둘뿐**이고,
  둘 다 JS 에서 옮겨 온 것이다. 나머지 17개 모듈은 전부 내장 제네릭을 쓴다.

### 구조화된 사전은 `TypedDict` 다

🔵 `TypedDict` 150곳 · `NotRequired` 77곳. `dataclass` 는 **0곳**이다.

JSON 을 주고받는 것이 이 저장소가 하는 일의 대부분이라, 사전의 모양을 `TypedDict` 로 못박는다.
계약이 여러 모듈에 걸치면 **한 곳에 모은다** — `machine/codegraph_types.py` 가 그 예다.

```python
class Symbol(TypedDict):
    name: str
    kind: str
    file: str
    line: int
    doc: NotRequired[str]
```

### `cast()` 에는 이유를 적는다

🔵 57곳. 타입 검사기를 이기려고 쓰는 것이므로 **왜 안전한지를 한 줄 남긴다.**
이 저장소는 `⚠ cast — …` 로 시작하는 관습을 쓴다:

```python
# ⚠ cast — `symbol_count` 가 None 인 것은 비노드 층뿐이고 그것은 바로 위 조건이 걸렀다.
assert sum(cast(list[int], sizes)) == p["totals"]["symbols"]
```

`# pyright: ignore[...]` 도 같다 — **무엇을 왜 무시하는지** 옆에 적는다.

---

## 4. 시험 — pytest, 모킹 없이

🔵 시험 477개. `.venv/bin/python -m pytest -q` 로 전량이 돈다.

### 진짜를 쓴다. 모킹하지 않는다

🔵 `unittest.mock` · `MagicMock` · `pytest-mock` 사용 **0곳**이다.
대신 `tmp_path`(346곳) 안에 **진짜 파일과 진짜 git 저장소**를 만든다.

```python
def test_uncommitted_change_is_stale(tmp_path: Path):
    """커밋하지 않은 작업 트리 변경도 낡음이다 — blob SHA 로 판정하면 이것을 놓친다."""
    repo = _repo(tmp_path, {"a.py": ONE})     # 실제로 git init 하고 커밋한다
```

**Why —** 이 저장소의 코드는 파일 시스템과 `git` 과 바깥 도구의 실제 동작에 기댄다.
모킹하면 그 전제가 시험되지 않고, 전제가 틀렸을 때 시험이 초록인 채로 남는다.

쓰는 픽스처: `tmp_path`(346) · `monkeypatch`(26) · `pytest.skip`(12) · `pytest.raises`(6) ·
`capsys`(3) · `parametrize`(5).

### 골든 시험 — 없으면 건너뛴다, 실패가 아니다

실제 저장소 산출물로 검사하는 시험이 있다. 환경변수(`$GRAPHICS_REPO` · `$CSHARP_REPO` ·
`$CPP_REPO`)가 없으면 `pytest.skip` 한다. 🔵 지금 19개가 그렇게 건너뛴다.

⚠ **경로 상수가 빈 문자열이 되면 안 된다.** `os.path.join("", "out/…")` 이 **상대경로**가 되어
이 저장소의 산출물을 골든으로 착각해 읽는다(실제로 겪었다):

```python
CS_REPO = os.path.expandvars(os.environ.get("CSHARP_REPO", "")) or "/골든저장소_미지정/CSHARP_REPO"
```

### 시험 이름과 독스트링

- 이름은 **무엇이 참인지**를 문장으로 쓴다 — `test_uncommitted_change_is_stale`
- 🔵 한글 이름도 64개 있다(`test_없으면_None`). 둘 다 받는다 — 한 파일 안에서만 섞지 마라
- 독스트링 한 줄에 **왜 이것이 중요한지**를 적는다. 시험이 깨졌을 때 그 줄이 다음 사람을 살린다

### 합성 데이터만으로 검증하지 마라

**루트 `CLAUDE.md` 의 함정 목록에 있는 것이다.** 백틱 제목 결함은 실제 저장소 데이터를
확인하다 발견됐다 — 합성 시험만 썼으면 안 나왔다.

---

## 5. JavaScript 에서 옮겨 올 때 (지금 진행 중인 일)

이 저장소는 JS 를 파이썬으로 옮기는 중이다. **오류 없이 조용히 다르게 동작하는** 자리가 넷 있다.
🔵 전부 실제로 돌려 확인했다.

### 정규식 — `re.ASCII` 를 빠뜨리지 마라

JS 의 `\b` `\w` `\d` 는 **ASCII 전용**이고, 파이썬 `re` 는 str 패턴에서 **유니코드**다.
그래서 **파이썬은 한글을 낱말 문자로 본다.**

```
js   /\bRay\b/.test("Ray를 쓴다")                    -> true
py   re.search(r"\bRay\b", "Ray를 쓴다")             -> None    ← 조용히 안 맞는다
py   re.search(r"\bRay\b", "Ray를 쓴다", re.ASCII)   -> Match

py   re.fullmatch(r"\d+", "٣")                       -> Match   ← 아라비아-인도 숫자가 통과한다
py   re.fullmatch(r"\d+", "٣", re.ASCII)             -> None
```

한국어 본문에서 낱말 경계를 보는 코드는 **조사가 붙은 꼴로 시험한다.**
`"Ray 를"` 처럼 띄어쓴 시험은 이 결함을 못 잡는다.

### 반올림 방향

```
js   Math.round(12.5)      -> 13   (half-up)
py   round(12.5)           -> 12   (banker's rounding)
py   math.floor(12.5 + 0.5) -> 13
```

`Math.round` 는 `math.floor(x + 0.5)` 로 옮긴다.

### `True` 는 파이썬에서 정수다

```
js   Number.isInteger(true)  -> false
py   isinstance(True, int)   -> True
```

정수 검사는 `isinstance(x, int) and not isinstance(x, bool)` 로 쓴다.
JSON 의 `true` 가 숫자 `1` 로 통과하는 것을 막는다.

### JSON 쓰기

🔵 `ensure_ascii=False` 36곳. `JSON.stringify(x, null, 2)` 는
`json.dumps(x, ensure_ascii=False, indent=2)` 다. **끝의 개행도 원본을 따른다.**

### 나머지 대응

| JS | Python |
|---|---|
| `obj?.key ?? "기본"` | `(obj or {}).get("key") or "기본"` |
| `String(x ?? "")` | `str(x) if x is not None else ""` |
| `process.argv[1].endsWith("x.mjs")` | `if __name__ == "__main__":` |
| `process.cwd()` | `os.getcwd()` |
| `camelCase` 함수 이름 | `snake_case` — §2 를 보라 |

**포팅은 순수 이동이다.** 같은 입력에 같은 출력이 나와야 한다.
지우기 전에 옛것과 새것을 각각 돌려 산출물을 `diff` 로 대조한다.
개선하고 싶은 것이 보이면 **고치지 말고 보고한다.**

---

## 6. 경로와 바깥 명령 — 박지 않는다

**이 저장소는 공개된다.** 홈 아래 경로를 문서·코드·커밋에 그대로 적지 않는다.

- 파이썬 해석기는 `tools/python.py` 의 **`pythonPath()`** 로 찾는다. `"python3"` 을 박지 마라
  (이름이 camelCase 인 것 자체가 §2 의 드리프트다 — 부를 때는 있는 이름 그대로 부른다)
- 바깥 명령(`git` · `dot` · `clang-uml` · `dotnet` · `clangd` · `node`)은 **PATH 로 부른다**
- 문서에 경로를 적을 일이 생기면 변수 이름을 쓴다 —
  `$REPO_ROOT` · `$GRAPHICS_REPO` · `$CSHARP_REPO` · `$CPP_REPO` · `REPORT_PYTHON`
- 새 기계에 무엇이 빠졌는지는 `npm run doctor` 가 한 화면으로 말한다

🔵 `os.path.` 393곳 vs `pathlib.Path` 18곳. **`os.path` 가 이 저장소의 기본**이고,
`Path` 는 주로 시험의 `tmp_path: Path` 서명에 쓰인다. 섞어 써도 되지만
한 함수 안에서 왔다 갔다 하지 마라.

---

## 7. 오류 처리 — 조용히 넘기지 않는다

🔵 `except` 45곳. `subprocess` 98곳.

- **터지지 말아야 할 자리와 터져야 할 자리를 가른다.** 없는 파일·깨진 JSON 을 만나면
  `None` 이나 빈 목록을 돌려주고, **아귀가 맞지 않으면 멈춘다**
- 맞아 보이는 틀린 결과가 명백한 실패보다 나쁘다. 채점기가 문항지와 안 맞으면
  점수를 내지 않고 종료 코드 1 로 멈추는 것이 그 예다
- **`except:` 나 `except Exception:` 로 뭉뚱그리지 마라.** 잡을 예외를 이름으로 적는다
- 사용자에게 보이는 오류 메시지는 **한국어로, 무엇을 어떻게 고치라는지까지** 적는다
- 커스텀 예외 클래스를 만들기 전에 멈춘다 — 🔵 이 저장소에 그런 계층이 없다.
  구현자 1, 소비자 1이면 인터페이스를 만들지 않는다(루트 `CLAUDE.md` 의 "거울 함정")

---

## 8. 전수조사 레코드 — 코드를 쓰면 레코드도 쓴다

**이 저장소만의 규약이다. 빠뜨리면 게이트에 걸린다.**

새 함수·클래스를 만들면 그 자리에서 `machine/terms-reading.json` 에 레코드를 쓴다.
계약은 `{kind, module, where, means, does, uses[], confidence, source}` 이고
`where` 는 **실제 `파일:줄`** 이어야 한다.

```bash
.venv/bin/python machine/xmldoc.py emit      # comments.xml 생성
.venv/bin/python machine/xmldoc.py inject    # 소스에 블록 주입 + where 재계산
.venv/bin/python machine/xmldoc.py check     # 기대: 문제 0건
```

⚠ **`# <include …/>` 블록을 손으로 쓰지도 고치지도 마라.** 위 명령이 생성한다.

---

## 9. 게이트 — 전부 초록이어야 한다

```bash
.venv/bin/python -m pytest -q                                        # 시험
npm test                                                             # JS 경계만
npm run typecheck                                                    # tsc --noEmit
npm run typecheck:py                                                 # pyright strict, 0 errors
.venv/bin/python machine/xmldoc.py check                             # 주석 주입
.venv/bin/python tools/gen_readme.py --check machine runner viz tools  # README 표류
npm run doctor                                                       # 환경
```

**건너뜀은 실패가 아니다** — 골든 저장소 환경변수가 없는 시험이다.

### 개발 흐름

- 가상환경은 `.venv` 하나. `pip install -r requirements.txt`
- **커밋은 지시받았을 때만 한다.** 메시지는 소문자 `[tag] : subject` **한 줄**, 한국어, 본문 없음
- `git add -A` 를 쓰지 마라 — 작업 트리에 다른 작업이 얹혀 있다. 경로를 좁혀 스테이징한다
- 같은 작업 트리에 병렬 에이전트가 있을 수 있다. **`git stash` 를 쓰지 마라.**
  스냅샷이 필요하면 `git stash create`

---

## 10. 단순함이 최우선

- **일회용 코드에는 추상화가 필요 없다.** 200줄을 썼는데 50줄로 줄일 수 있으면 다시 쓴다
- 요청받지 않은 "유연성" 이나 "설정 가능성" 을 넣지 않는다. 필요하면 물어본다
- 플러그인 구조 · 레지스트리 · 추상 인터페이스가 떠오르면 멈춘다.
  **구현자 1, 소비자 1이면 인터페이스를 만들지 않는다**
- 좋은 아이디어가 떠올라도 범위를 넓히지 말고 **기록만 하고 보고한다**

---

## 이 문서에 대하여

- 이 파일은 아직 git 에 추가되지 않았다(`.gitignore` 에 걸린 것은 아니다).
  추적할지는 저장소 주인이 정한다.
- 여기 적힌 수치는 🔵 2026-08-31 실측이다. **낡을 수 있다** — 어긋나면 실제 코드가 맞다.
- 루트 `CLAUDE.md` · `machine/CLAUDE.md` · `viz/CLAUDE.md` 와 충돌하면 **그쪽이 우선한다.**
