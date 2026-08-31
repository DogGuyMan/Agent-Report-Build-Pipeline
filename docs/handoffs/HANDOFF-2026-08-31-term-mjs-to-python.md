HANDOFF — runner/term/*.mjs 를 파이썬으로 옮긴다

- **작성** 2026-08-31 · **저장소** `$REPO_ROOT` (= `report-builder`) · **브랜치** `main`
- **수신** 파이썬 담당 개발자 / 파이썬 담당 에이전트
- **산출물 종류** 자기완결형 작업 지시. 이 문서 하나만 읽고 수행할 수 있어야 한다.

---

## 0. 한 줄 요약과 바로 다음 걸음

`runner/term/` 에 남은 JavaScript 세 파일을 **파이썬으로 옮긴다.** 그리고 `test/test_term.py` 가
node 를 자식 프로세스로 띄워 `.mjs` 를 시험하던 것을 **네이티브 pytest 로 바꾼다.**

바로 다음 걸음 — 아래 §3 의 기준선 명령 다섯 개를 먼저 돌려 전부 초록인지 확인한다.
초록이 아니면 그 상태에서 시작하지 말고 보고한다.

---

## 1. 왜 하는가 — 중복이 이미 사고를 예고하고 있다

이 포팅의 값어치는 "언어 통일" 이 아니다. **같은 규칙이 두 언어에 살고 있고, 코드 주석이 그
위험을 스스로 적어 두었다는 것**이 이유다.

`runner/quiz.mjs` 의 `flattenQuestions` 주석 (`runner/term/quiz.mjs:37` 위):

> `**runner/run_mode1_5.py` 의 `flatten_questions` 와 같은 순서여야 한다.**
> 번호 규칙이 두 언어에 살고 있어서, 한쪽만 고치면 채점이 남의 답을 본다.

🔵 2026-08-31 실측 — 실제로 다음 다섯 쌍이 두 언어에 이중으로 산다:


| 규칙           | JavaScript                                       | Python                                             |
| ------------ | ------------------------------------------------ | -------------------------------------------------- |
| 용어당 문항 수 `3` | `runner/term/quiz.mjs:18` `QUESTIONS_PER_TERM`   | `runner/run_mode1_5.py:112` `QUESTIONS_PER_TERM`   |
| 문항당 보기 수 `5` | `runner/term/quiz.mjs:25` `CHOICES_PER_QUESTION` | `runner/run_mode1_5.py:119` `CHOICES_PER_QUESTION` |
| 문항 번호 매기기    | `quiz.mjs:37` `flattenQuestions`                 | `run_mode1_5.py:273` `flatten_questions`           |
| 보기 번호 읽기     | `quiz.mjs:63` `choiceNumber`                     | `run_mode1_5.py:314` `choice_number`               |
| 기입란·문항지 대조   | `quiz.mjs:80` `tallySheet`                       | `run_mode1_5.py:332` `validate_answers`            |


한쪽만 고치면 **오류 없이 남의 답을 채점한다.** 포팅하면 이 다섯 쌍을 하나로 합칠 수 있다.

부수 이유 하나 — 🔵 `bin/report-term` 은 `.mjs` 를 가리키는 **마지막 남은 디스패치 표**다.
`bin/report-spec` 과 `bin/report-wiki` 는 이미 전부 `.py` 다(`bin/report-spec:17-19`,
`bin/report-wiki:17-19`).

---

## 2. 지켜야 할 규칙 (Hard rules)

### 2.1 `.gemini/PythonRule.md` 를 먼저 읽는다

**2026-08-31 에 이 저장소의 실측 관행으로 다시 썼다.** 파이썬 규약 전량이 거기 있으므로
이 절은 요약만 두고, 자세한 것은 그 문서를 본다.

⚠ **옛 판(2026-08-31 이전)을 보고 있다면 따르지 마라.** 그것은 Flask·SQLAlchemy 용 일반
보일러플레이트였고 이 저장소와 정면으로 어긋났다 — `Optional[Type]` 강요(여기는
🔵 `X | None` 222곳 vs `Optional[` 12곳) · src-layout · `tests/` 디렉토리 · Black 88자.
문서 첫머리에 `description: "report-builder 저장소의 파이썬 규약"` 이 있으면 새 판이다.

**드리프트가 이미 일어나고 있다 (🔵 2026-08-31 실측) — 이 작업에서 되풀이하지 마라:**


| 드리프트             | 실측       | 어디서 왔나                                                                          |
| ---------------- | -------- | ------------------------------------------------------------------------------- |
| camelCase 함수 이름  | 49 / 348 | 전부 JS 에서 옮겨 온 파일 (`viz/init.py` 8 · `viz/link_paths.py` 6 · `viz/check.py` 5 …) |
| `Optional[X]`    | 12 / 234 | `runner/wiki/*.py` · `viz/init.py` · `viz/link_paths.py`                        |
| `Dict`/`List` 별칭 | 2개 파일    | `tools/python.py` · `viz/wrap_terms.py`                                         |


**JS 이름을 그대로 들고 오지 마라.** `pickTerms` → `pick_terms`, `flattenQuestions` →
`flatten_questions` (§5 STEP 2 의 대응표). 그리고 `X | None` 을 쓴다.

**이미 들어온 49개를 이번에 정리하지 마라** — 별개 작업이고 범위를 넘는다. 새로 늘리지만 않으면 된다.

### 2.2 실제 규약 — `CLAUDE.md` 에서 온 것

- **주석·독스트링은 현 상황만 적는다.** 확신도 표기(🔵/🟡/💭)·날짜·측정 수치·번복 기록·설계 철학·
존재 이유 서사를 **코드에 남기지 않는다.** 그런 것은 이 문서와 `docs/` 의 몫이다.
  - 쓴다: 함수마다 한 줄 요약 / 코드가 의존하는 형식·동작 사실 / 비직관적 제약과 그 즉각적 귀결
  - 쓰지 않는다: `🔵 2026-08-31 실측 — …` · `~에 뒤집힌 결정` · `거울 함정 경계 — …`
- **주장이 아니라 시험으로 적는다.** 바깥 동작에 기대는 사실은 주석 대신 그것을 고정하는 시험을 둔다.
- 설명은 **한국어 + 영문 기술용어 병기.** 약어와 압축 표현을 피한다.
- **컴포넌트·API 는 추가만 한다.** 이번 작업에서 공개 함수의 이름과 인자 의미를 바꾸지 않는다.
- `# <include file="machine/comments.xml" …/>` 블록은 `machine/xmldoc.py` 가 자동 주입한다 —
**손으로 쓰지도 고치지도 않는다.** §6 의 절차로 다시 생성한다.

### 2.3 커밋

- **커밋하지 마라.** 구현하고 §9 형식으로 보고만 한다. 커밋 여부는 저장소 주인이 정한다.
- 만약 커밋을 지시받으면 `personal-commit-messages` 규약을 따른다 —
소문자 `[tag] : subject` **한 줄**, 한국어, 본문 없음.
- `git add -A` 를 쓰지 마라. 🔵 작업 트리에 이번 작업과 무관한 변경이 30여 개 떠 있다
(pyright strict 전환 · `viz/svg.mjs` 신설). 경로를 좁혀 스테이징한다.

### 2.4 바꾸면 안 되는 값 (사용자 확정)


| 값                                   | 자리                                                                                | 비고                                                |
| ----------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| `QUESTIONS_PER_TERM = 3`            | `quiz.mjs:18`                                                                     | 2026-08-29 사용자 변경(5→3)                            |
| `CHOICES_PER_QUESTION = 5`          | `quiz.mjs:25`                                                                     | 실제 뜻 4 + 마지막 "모르겠다" 1                             |
| 채점 구간                               | `quiz.mjs:153` `gradeOne`                                                         | `dontKnow>=2 → 모름` · `correct>=2 → 확실` · 그 외 `모름` |
| 필드명 `TermMeans` · `UserMentalValue` | `emit.mjs:19-20`                                                                  | Mode 2 가 읽는 이름                                    |
| 산출 파일명                              | `term-candidates.json` · `term-grades.json` · `terms.json` · `term-study-note.md` | 그대로                                               |


**"애매" 는 현재 규칙이 내지 않는다.** 5문항 시절의 잔재로 `emit`/`Term.mental` 타입에만 남아 있다.
없애지 말고 그대로 옮긴다.

### 2.5 동작을 바꾸지 않는다

이것은 **순수 포팅**이다. 같은 입력에 같은 파일이 나와야 한다. 개선하고 싶은 것이 보이면
**고치지 말고 §9 보고서에 적는다.**

---

## 3. 시작 전 기준선 (🔵 2026-08-31 실측, 그대로 재현되어야 한다)

```bash
cd $REPO_ROOT

.venv/bin/python -m pytest -q
#   기대: 466 passed, 19 skipped
#   건너뛰는 19개는 골든 저장소 환경변수($GRAPHICS_REPO·$CSHARP_REPO·$CPP_REPO)가 없어서다. 실패가 아니다.

npm test
#   기대: pass 8, fail 0

npm run typecheck:py
#   기대: 0 errors   (pyright strict — pyrightconfig.json 의 typeCheckingMode 가 "strict")

.venv/bin/python machine/xmldoc.py check
#   기대: 문제 0건

.venv/bin/python tools/gen_readme.py --check machine runner viz tools
#   기대: "README 4개 — 소스와 일치"
```

다섯 개가 전부 초록이 아니면 **시작하지 말고 보고한다.**

---

## 4. ⚠ 이식 함정 넷 — 여기가 이 작업의 급소다

JS 를 파이썬으로 옮길 때 **오류 없이 조용히 다르게 동작하는** 자리가 넷 있다.
전부 🔵 2026-08-31 이 기계에서 실제로 돌려 확인했다.

### 함정 1 (가장 위험) — `\b` `\w` `\d` 가 파이썬에서는 유니코드다

JavaScript 의 `\b` `\w` `\d` 는 **ASCII 전용**이다. 파이썬 `re` 는 str 패턴에서 **유니코드**다.
그래서 **한글이 낱말 문자(`\w`)로 취급된다.**

```
js   /\bRay\b/.test("Ray를 쓴다")                      -> true
py   re.search(r"\bRay\b", "Ray를 쓴다")               -> None      ← 조용히 안 맞는다
py   re.search(r"\bRay\b", "Ray를 쓴다", re.ASCII)     -> Match      ← 이렇게 해야 한다

py   re.fullmatch(r"\d+", "٣")                         -> Match     ← 아라비아-인도 숫자가 통과한다
py   re.fullmatch(r"\d+", "٣", re.ASCII)               -> None
```

**결과가 무엇인가.** `collect.mjs` 의 `pickTerms` 는 Plan 본문에서 용어를 찾는다. 한국어 Plan 은
"`Renderer`를 고친다" 처럼 **조사가 바로 붙는다.** `re.ASCII` 없이 옮기면 그런 용어를 전부 놓치고,
출제 대상이 조용히 줄어든다. 오류는 나지 않는다.

**조치 — 옮긴 정규식 전부에 `re.ASCII` 를 준다.** 대상:

- `collect.mjs:20` `pickTerms` 의 `"\\b" + escapeRe(name) + tail`
- `collect.mjs:36` `findNewConcepts` 의 패턴 세 개
- `quiz.mjs:63` `choiceNumber` 의 `/^\d+$/`

**⚠ 기존 시험이 이것을 못 잡는다.** `test/test_term.py:39` `test_pickterms_keeps_word_boundaries`
는 `"Ray 를 쓴다"` 처럼 **띄어쓴** 본문을 쓴다. 조사가 붙은 꼴을 넣는 시험을 새로 더한다(§5 STEP 6).

### 함정 2 — 반올림 방향이 다르다

```
js   Math.round(12.5)   -> 13     (half-up)
py   round(12.5)        -> 12     (banker's rounding, half-to-even)
py   math.floor(12.5+0.5) -> 13
```

`quiz.mjs:153` `gradeOne` 의 `Math.round((correct / QUESTIONS_PER_TERM) * 100)` 이 이것을 쓴다.
`QUESTIONS_PER_TERM = 3` 인 지금은 `.5` 가 나오지 않아 두 언어가 우연히 같다. 그러나 그 상수가
바뀌는 순간 갈린다. `**math.floor(x + 0.5)` 로 옮기고, 그것을 고정하는 시험을 둔다.**

### 함정 3 — 파이썬에서 `True` 는 정수다

```
js   Number.isInteger(true)      -> false
py   isinstance(True, int)       -> True
```

`quiz.mjs:47` 의 `Number.isInteger(q?.answer)` 와 `quiz.mjs:64` 의 `typeof value === "number"`,
`quiz.mjs:95` 의 `Number.isInteger(num)` 이 이 검사를 쓴다. 그대로 `isinstance(x, int)` 로 옮기면
JSON 의 `true` 가 보기 번호 `1` 로 통과한다.

**조치 —** `isinstance(x, int) and not isinstance(x, bool)` 로 옮긴다. 도우미 하나를 두고 세 곳이
그것을 쓰게 하는 편이 낫다.

### 함정 4 — JSON 을 쓸 때 한글이 이스케이프된다

`JSON.stringify(x, null, 2) + "\n"` 은 한글을 그대로 쓴다. 파이썬 `json.dumps` 는 기본으로
`\uXXXX` 로 escape 한다.

**조치 —** `json.dumps(x, ensure_ascii=False, indent=2) + "\n"` 로 옮긴다. 끝의 개행도 잊지 않는다
(`emit.mjs` 의 `toStudyNote` 산출물은 개행을 붙이지 **않는다** — 원본을 그대로 따른다).

기타 사소한 대응:


| JS                                  | Python                                                          |
| ----------------------------------- | --------------------------------------------------------------- |
| `obj?.key ?? "기본"`                  | `(obj or {}).get("key") or "기본"` — `None` 이 `"None"` 이 되지 않게 주의 |
| `String(x ?? "")`                   | `str(x) if x is not None else ""`                               |
| `[...set].sort()`                   | `sorted(set)` — ASCII 식별자라 두 언어의 정렬이 같다                         |
| `Object.entries(o)` 순서              | 파이썬 dict 도 삽입 순서를 지킨다. 그대로                                      |
| `process.argv[1].endsWith("x.mjs")` | `if __name__ == "__main__":`                                    |
| `process.cwd()`                     | `os.getcwd()` — 산출물이 **부르는 쪽 작업 폴더**에 떨어져야 한다                   |


---

## 5. 작업 단계

### STEP 1 — `runner/term/__init__.py` 를 만든다

🔵 `runner/__init__.py` 는 있으나 `runner/term/__init__.py` 는 **없다.**
`from runner.term.quiz import ...` 가 되려면 필요하다. 빈 파일로 만든다.

### STEP 2 — 세 파일을 옮긴다


| 원본                        | 새 파일                     | 줄 수 |
| ------------------------- | ------------------------ | --- |
| `runner/term/collect.mjs` | `runner/term/collect.py` | 73  |
| `runner/term/quiz.mjs`    | `runner/term/quiz.py`    | 203 |
| `runner/term/emit.mjs`    | `runner/term/emit.py`    | 64  |


**공개 이름은 snake_case 로 바꾼다** (파이썬 규약이자 이 저장소의 실제 관행 —
`run_mode1_5.py` 가 이미 `flatten_questions` · `choice_number` 를 쓴다):


| JS                                            | Python                          |
| --------------------------------------------- | ------------------------------- |
| `pickTerms`                                   | `pick_terms`                    |
| `findNewConcepts`                             | `find_new_concepts`             |
| `QUESTIONS_PER_TERM` · `CHOICES_PER_QUESTION` | 그대로 (상수는 이미 UPPER_CASE)         |
| `flattenQuestions`                            | `flatten_questions`             |
| `choiceNumber`                                | `choice_number`                 |
| `tallySheet`                                  | `tally_sheet`                   |
| `gradeOne` · `gradeAll`                       | `grade_one` · `grade_all`       |
| `toTermsDb` · `toStudyNote`                   | `to_terms_db` · `to_study_note` |


**지켜야 할 구조:**

- 각 파일은 **import 시에는 순수 함수만 노출**하고, `if __name__ == "__main__":` 아래에서만
파일을 읽고 쓴다. 원본의 규약이다.
- `quiz.mjs` 와 `emit.mjs` 는 앞에 남은 명령 이름을 벗겨 낸다
(`if args[0] == "grade": args.pop(0)` / `"emit"`). 디스패처가 이미 소비하지만 직접 실행도
받으려는 것이다 — **이 동작을 그대로 유지한다.**
- `tally_sheet` 는 `{counts, problems}` 두 값을 낸다. `problems` 가 비지 않으면 **채점하지 않고
종료 코드 1** 로 멈춘다. 아귀가 안 맞는 채로 낸 점수는 틀린 것보다 나쁘다 — 맞아 보인다.
- 표준 출력 문구를 **글자 그대로** 옮긴다. `run_mode1_5.py` 와 `term-benchmark` 스킬이 사람에게
보여주는 안내다.

**타입 힌트를 전부 붙인다.** 🔵 `pyrightconfig.json` 이 `"typeCheckingMode": "strict"` 이고
`include` 에 `runner` 가 있다. `npm run typecheck:py` 가 0 errors 여야 한다.
`X | None` 을 쓴다 — `Optional[X]` 가 아니다(§2.1).

### STEP 3 — `bin/report-term` 의 표를 바꾼다

```python
    table={
        "collect": "runner/term/collect.py",
        "grade": "runner/term/quiz.py",
        "emit": "runner/term/emit.py",
    },
```

`runner/dispatch.py` 의 `run_dispatch` 가 확장자를 보고 해석기를 고른다
(`runner/dispatch.py` 의 `runner = "python3" if script.endswith(".py") else "node"`).
`**dispatch.py` 는 고치지 않는다** — 확장자만 바뀌면 알아서 파이썬으로 간다.

### STEP 4 — `runner/run_mode1_5.py` 의 명령줄 세 개를 바꾼다

`collect_argv` (`:391`) · `grade_argv` (`:406`) · `emit_argv` (`:418`) 에서
`"node"` 를 파이썬 해석기로, `*.mjs` 를 `*.py` 로 바꾼다.

**해석기 경로를 박지 마라.** `CLAUDE.md` 규약이다 — `tools/python.py` 의 `pythonPath()` 로 찾는다.
`run_mode1_5.py` 가 그 모듈을 아직 안 쓰면 import 를 더한다.

`_term_script` (`:383`) 는 그대로 두고 인자만 `"collect.py"` 등으로 바꾼다.

⚠ `runner/test_run_mode1_5.py` 에 이 세 함수를 고정하는 시험이 있다
(`test_collect_argv_names_the_plan_and_the_term_database` ·
`test_grade_and_emit_argv_point_at_the_right_scripts` 등). **함께 고친다.**

### STEP 5 — 중복 다섯 쌍을 합친다 (§1 의 본론)

`run_mode1_5.py` 가 자기 사본을 갖는 대신 `runner.term.quiz` 에서 가져오게 한다:

```python
from runner.term.quiz import (
    QUESTIONS_PER_TERM, CHOICES_PER_QUESTION,
    flatten_questions, choice_number,
)
```

그리고 `run_mode1_5.py` 안의 같은 이름 정의를 지운다.

**단, `validate_answers`(`:332`)와 `tally_sheet` 는 합치지 마라.** 이름은 닮았으나 하는 일이
다르다 — `validate_answers` 는 사람에게 보여줄 **한국어 지적 목록**을 만들고,
`tally_sheet` 는 **채점 전 대조**를 한다. 두 자리 다 필요하다. 그 둘이 공유하는 것은 이미 위에서
import 하는 `flatten_questions` · `choice_number` 뿐이다.

⚠ **순환 import 를 만들지 마라.** `runner/term/quiz.py` 는 `run_mode1_5.py` 를 import 하지 않는다.
의존은 한 방향(`run_mode1_5` → `term.quiz`)이다.

⚠ `**run_machine`(`:498`)의 자식 프로세스 실행 방식은 바꾸지 마라.** 단계마다 벽시계를 재는
`M.Heartbeat` 가 거기 걸려 있다. import 로 바꾸면 측정 모델이 달라진다. 순수 함수만 import 하고,
**실행은 지금처럼 자식 프로세스로 둔다.**

### STEP 6 — `test/test_term.py` 를 네이티브 pytest 로 바꾼다

지금은 파이썬이 임시 `.mjs` 를 쓰고 `node` 를 띄워 `assert` 하는 얼개다
(`test/test_term.py:7-27` 의 `run_js_eval`). **그 얼개를 통째로 없앤다.**

- `run_js_eval` · `run_js_quiz_eval` · `JS_HELPERS` 문자열을 지운다
- `.tmp-term-eval.mjs` 를 쓰고 지우던 것도 없어진다
- 각 시험은 `from runner.term.quiz import ...` 처럼 **직접 import 해서 assert** 한다
- **시험 이름과 검사 내용은 그대로 옮긴다.** 🔵 현재 29개다. 줄이지 마라.

**자리는 `test/test_term.py` 그대로 둔다.** 시험 파일을 코드 옆(`runner/`)으로 옮길지는 아직
정해지지 않은 별개 문제다 — 이 작업에 끼워 넣지 마라.

**시험을 셋 더한다** (§4 의 함정을 고정하는 것 — 주장 대신 시험으로 적는다):

1. `pick_terms` 가 **조사가 바로 붙은** 용어를 잡는다
 — 예: db `{"Renderer": …}`, plan `"Renderer를 고친다"` → `["Renderer"]`
 (`re.ASCII` 가 빠지면 이 시험이 깨진다)
2. `grade_one` 의 백분율이 half-up 이다 — `.5` 가 나오는 입력을 만들어 고정한다
3. `choice_number` 가 `True` 를 보기 번호로 받지 않는다 — `choice_number(True) is None`

### STEP 7 — 옛 `.mjs` 셋을 지운다

`runner/term/collect.mjs` · `quiz.mjs` · `emit.mjs` 를 지운다.
**남겨 두면 다음 사람이 어느 쪽이 사는 코드인지 모른다.**

지운 뒤 확인 — 저장소에 이들을 가리키는 참조가 남으면 안 된다:

```bash
grep -rn "collect\.mjs\|quiz\.mjs\|emit\.mjs" \
  --include="*.py" --include="*.md" --include="*.json" \
  bin runner machine viz tools test docs
#   기대: 산출물(machine/comments.xml)을 뺀 자리에 0건
```

`runner/README.md` 와 `runner/CLAUDE.md` 의 서술도 함께 고친다.

---

## 6. 레코드·문서 갱신 — 빠뜨리면 게이트에 걸린다

### 6.1 전수조사 레코드 아홉 개

🔵 `machine/terms-reading.json` 에 `runner/term/*.mjs` 를 가리키는 레코드가 **9개** 있다:


| 키                      | 현재 `where`                   | `kind`   |
| ---------------------- | ---------------------------- | -------- |
| `collect.mjs`          | `runner/term/collect.mjs:1`  | file     |
| `quiz.mjs`             | `runner/term/quiz.mjs:1`     | file     |
| `emit.mjs`             | `runner/term/emit.mjs:1`     | file     |
| `term-candidates.json` | `runner/term/collect.mjs:66` | artifact |
| `term-grades.json`     | `runner/term/quiz.mjs:197`   | artifact |
| `terms.json`           | `runner/term/emit.mjs:54`    | artifact |
| `term-study-note.md`   | `runner/term/emit.mjs:57`    | artifact |
| `TermMeans`            | `runner/term/emit.mjs:19`    | key      |
| `UserMentalValue`      | `runner/term/emit.mjs:20`    | key      |


해야 할 것:

1. `file` 세 개의 **키를 `collect.py` · `quiz.py` · `emit.py` 로 바꾸고** `where` 도 새 경로로
2. 나머지 여섯 개의 `where` 를 새 파일의 **실제 줄 번호**로 고친다
3. ⚠ `kind` 가 `file` `artifact` `key` 인 레코드는 **그 이름이 해당 줄에 글자 그대로 있어야 한다**
 (`machine/terms_db.py` 의 L3 검사). 예 — `terms.json` 레코드가 가리키는 줄에 `terms.json` 이라는
 글자가 있어야 한다
4. 새로 만든 함수마다 레코드를 쓴다 — 계약은
 `{kind, module, where, means, does, uses[], confidence, source}`
5. 없어진 함수의 레코드를 지운다

그런 다음:

```bash
.venv/bin/python machine/xmldoc.py emit
.venv/bin/python machine/xmldoc.py inject
.venv/bin/python machine/xmldoc.py check     # 기대: 문제 0건
```

`inject` 가 소스에 `# <include …/>` 블록을 박고 줄이 밀린 만큼 `where` 를 다시 센다.
**그 블록을 손으로 쓰지 마라.**

### 6.2 README 재생성

🔵 `tools/gen_readme.py` 의 `render_dir` 은 `**.py` 만 훑는다.** 그래서 지금
`runner/README.md` 에 `runner/term/*.mjs` 가 없다. 포팅하면 세 파일이 새로 나타난다.

```bash
.venv/bin/python tools/gen_readme.py machine runner viz tools
.venv/bin/python tools/gen_readme.py --check machine runner viz tools   # 기대: "README 4개 — 소스와 일치"
```

### 6.3 문서

- `CLAUDE.md` 의 "남는 JS" 표에서 `runner/term/*.mjs` 줄을 지운다.
🔵 지금 그 줄은 "Mode 1.5 얼갈이. 아직 포팅 전 — `dispatch.py` 가 확장자를 보고 node 로 띄운다" 다.
- `runner/CLAUDE.md` · `runner/README.md` 에서 `.mjs` 를 가리키는 서술을 고친다.
- **다른 표의 수치를 손으로 고치지 마라.** 시험 개수 같은 것은 §9 보고서에 실측값을 적고
저장소 주인이 반영한다.

---

## 7. 소유 경계 (Boundaries)

### 소유한다 — 마음껏 고친다

```
runner/term/__init__.py          (신설)
runner/term/collect.py           (신설)
runner/term/quiz.py              (신설)
runner/term/emit.py              (신설)
runner/term/collect.mjs          (삭제)
runner/term/quiz.mjs             (삭제)
runner/term/emit.mjs             (삭제)
bin/report-term                  (표 세 줄)
runner/run_mode1_5.py            (argv 세 함수 + 중복 제거)
runner/test_run_mode1_5.py       (argv 시험)
test/test_term.py                (네이티브 재작성)
machine/terms-reading.json       (레코드 9개 + 신설분)
machine/comments.xml             (xmldoc emit 이 생성 — 손대지 않는다)
runner/README.md                 (gen_readme 이 생성)
CLAUDE.md · runner/CLAUDE.md     (해당 절만)
```

### 건드리지 않는다


| 파일                                                     | 왜                                      |
| ------------------------------------------------------ | -------------------------------------- |
| `runner/dispatch.py`                                   | 확장자로 해석기를 고르므로 **이미 옳다.** 고칠 것이 없다     |
| `runner/run_mode1.py` · `run_mode2.py`                 | 다른 mode. 이 작업과 무관                      |
| `machine/**` (`terms-reading.json` 제외)                 | 기계축. 이번 작업의 소유가 아니다                    |
| `viz/**`                                               | 시각축. 무관                                |
| `.gemini/PythonRule.md`                                | 규약 문서다. **읽되 고치지 않는다** (§2.1)          |
| `viz/svg.mjs` · `viz/lib.mjs` · `viz/patch-legacy.mjs` | esbuild·React 가 읽는 자리라 JS 로 **남아야 한다** |


### 병렬 작업 지형

🔵 작업 트리에 이번 작업과 무관한 커밋되지 않은 변경이 30여 개 있다(pyright strict 전환 ·
`viz/svg.mjs` 신설 · 여러 `.py` 포팅). `**git stash` 를 쓰지 마라** — 같은 작업 트리에 다른
작업이 얹혀 있다. 원인을 가려야 하면 `git stash create` 로 스냅샷만 뜬다.

---

## 8. 검증 (Verify)

전부 초록이어야 한다.

```bash
cd $REPO_ROOT

# 1. 파이썬 시험 — 466 이 기준선. test_term.py 재작성으로 수가 바뀔 수 있으나 실패는 0 이어야 한다
.venv/bin/python -m pytest -q

# 2. JS 시험 — 8 그대로. 이 작업이 건드리지 않는다
npm test

# 3. 파이썬 타입 — strict. 0 errors
npm run typecheck:py

# 4. 주석 주입 — 문제 0건
.venv/bin/python machine/xmldoc.py check

# 5. README 표류 — 4개 일치
.venv/bin/python tools/gen_readme.py --check machine runner viz tools

# 6. 남은 참조 0건 (machine/comments.xml 은 산출물이라 제외)
grep -rn "collect\.mjs\|quiz\.mjs\|emit\.mjs" \
  --include="*.py" --include="*.md" --include="*.json" bin runner viz tools test docs

# 7. 끝에서 끝까지 실제로 돈다 — 임시 폴더에서
#    report-term collect <plan.md> → grade <answers.json> <questions.json> → emit <term-grades.json>
#    산출물이 **부르는 쪽 작업 폴더**에 떨어지는지 확인한다
```

### 동등성 확인 — 이것을 반드시 한다

`.mjs` 를 지우기 **전에**, 같은 입력으로 옛 것과 새 것을 각각 돌려 산출 파일을 바이트로 대조한다.

```bash
# 예 — grade 단계
mkdir -p /tmp/old /tmp/new
(cd /tmp/old && node  $REPO_ROOT/runner/term/quiz.mjs answers.json questions.json)
(cd /tmp/new && python3 $REPO_ROOT/runner/term/quiz.py  answers.json questions.json)
diff /tmp/old/term-grades.json /tmp/new/term-grades.json   # 기대: 차이 없음
```

세 단계 전부 이렇게 대조한다. **합성 입력만 쓰지 마라** — 한글 조사가 붙은 실제 Plan 본문을
`collect` 에 한 번은 먹여야 §4 함정 1 이 드러난다.

---

## 9. 보고 형식 (Report)

작업을 마치면 아래 꼴로 보고한다. **커밋하지 않는다.**

```
상태: DONE | DONE_WITH_CONCERNS | BLOCKED

바꾼 파일:
  신설 — …
  삭제 — …
  수정 — …

검증 결과 (실제 명령 출력을 붙인다):
  pytest            : N passed, M skipped
  npm test          : pass 8
  typecheck:py      : 0 errors
  xmldoc check      : 문제 0건
  gen_readme --check: 4개 일치
  남은 .mjs 참조    : 0건
  동등성 대조       : collect/grade/emit 세 단계 diff 결과

고치지 않고 남긴 것 (§2.5 — 개선안이 보였다면 여기 적는다):
  …

막힌 것 / 판단이 필요한 것:
  …
```

### 자기 점검 — 보고 전에 확인한다

- [ ] 정규식 전부에 `re.ASCII` 를 줬는가 (§4 함정 1)
- [ ] `Math.round` 를 `math.floor(x+0.5)` 로 옮겼는가 (함정 2)
- [ ] 정수 검사에서 `bool` 을 뺐는가 (함정 3)
- [ ] `json.dumps` 에 `ensure_ascii=False` 와 끝 개행을 줬는가 (함정 4)
- [ ] 표준 출력 문구를 글자 그대로 옮겼는가
- [ ] 시험 29개를 하나도 줄이지 않고 옮겼고, 함정 시험 3개를 더했는가
- [ ] 주석에 날짜·확신도 표기·설계 철학을 넣지 않았는가 (§2.2)
- [ ] `# <include …/>` 블록을 손으로 쓰지 않았는가 (§6.1)
- [ ] camelCase 이름과 `Optional[X]` 를 새로 만들지 않았는가 (§2.1 드리프트)
- [ ] 커밋하지 않았는가 (§2.3)

---

## 10. 이 작업 밖에서 발견된 것 — 고치지 말고 보고만

작업 중 마주치더라도 **손대지 않는다.** 저장소 주인이 판단할 몫이다.

1. 🔵 `package.json` 의 `"build": "node viz/build.mjs"` 와 `"check": "node viz/check.mjs"` 가
 **없는 파일을 가리킨다.** `viz/` 에는 `build.py` · `check.py` 만 있다.
 `npm run build` · `npm run check` 는 지금 깨져 있다.
2. 🔵 `runner/dispatch.py` 가 해석기를 `"python3"` 으로 **박아 쓴다.** `CLAUDE.md` 규약은
 `tools/python.py` 의 `pythonPath()` 로 찾으라는 것이다. 이번 작업 뒤에는 모든 디스패치가
 이 자리를 지나므로 무게가 커진다.
3. 시험 파일의 자리가 두 관례로 갈려 있다 — `machine/` `runner/` `tools/` 는 코드 옆,
 `test/` 는 별도 자리. 미결.

---

## 부록 — 옮길 함수 목록 (한눈에)

```
runner/term/collect.py
  escape_re(s)                     내부. 정규식 특수문자 막기
  pick_terms(db, plan_text)        DB ∩ Plan 본문                    [re.ASCII]
  find_new_concepts(db, plan_text) Plan 이 새로 만든 개념 세 꼴        [re.ASCII]
  __main__                         -> term-candidates.json

runner/term/quiz.py
  QUESTIONS_PER_TERM = 3
  CHOICES_PER_QUESTION = 5
  flatten_questions(doc)           문항지를 펴고 QNum 을 1부터
  choice_number(value)             UserAns 읽기. 빈 칸은 None        [re.ASCII, bool 제외]
  tally_sheet(sheet, doc)          -> (counts, problems)
  grade_one(correct, dont_know)    -> (rate, mental)                 [floor(x+0.5)]
  grade_all(answers)               -> {용어: {rate, mental, means}}
  __main__                         problems 있으면 exit 1, 없으면 -> term-grades.json

runner/term/emit.py
  to_terms_db(graded)              -> {용어: {TermMeans, UserMentalValue}}
  to_study_note(graded)            확실이 아닌 것만, 정답률 낮은 순
  __main__                         -> terms.json + term-study-note.md
```

---

## 변경 기록

- 2026-08-31 — 최초 작성. 기준선 실측(pytest 466/19 · npm test 8 · pyright 0), 이식 함정 4종
실측 확인, 중복 다섯 쌍 확인.

