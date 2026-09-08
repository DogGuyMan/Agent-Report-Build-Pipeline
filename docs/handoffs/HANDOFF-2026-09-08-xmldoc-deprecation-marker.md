# HANDOFF — `# <include …/>` 주석 주입에 폐지 예정 표시를 단다

> 🟢 **완료됨 (2026-09-08) — 다시 실행하지 마라.**
> 커밋 `5afbbd0` `[chore] : xmldoc - 폐지 예정 배너와 모듈 설명 갱신` 이 이 작업이다.
> `machine/xmldoc.py` 에 모듈 독스트링 표시 · `DEPRECATED` 상수 · `check` 의 배너 한 줄이 들어갔다.
> 확인: `.venv/bin/python machine/xmldoc.py check` 마지막 줄에 `알림 — 폐지 예정 …` 이 나온다.
>
> **남은 것 둘** — 둘 다 이 문서의 범위 밖이고 사용자 결정 대기다:
> - `emit_xml()` 에 `deprecated` 속성 넣기 → `machine/comments.xml` 재생성(약 5,700줄)을 부른다.
>   러너 리팩터링 3단계 뒤 `emit`→`inject` 를 한 번 돌릴 때 함께 한다
> - **대체 마크업이 무엇인가** → 미정. `docs/decisions/0007-xmldoc-include-deprecated.md` 의
>   후보 셋(독스트링만 / 곁딸린 파일 / 데코레이터)만 적혀 있다

> 작성 2026-09-08 · 기준 커밋 `6b45e3b` · 저장소 `$REPO_ROOT`
> 대상: **Sonnet 서브에이전트 1회 작업.** 파일 하나만 고친다
> 근거 결정: [`docs/decisions/0007-xmldoc-include-deprecated.md`](../decisions/0007-xmldoc-include-deprecated.md)

## 붙여넣을 프롬프트

```
너는 report-builder 저장소($REPO_ROOT, 브랜치 main)에서 **한 파일만 고치는** 작업을 맡았다.
목표 — `machine/xmldoc.py` 가 만드는 주석 주입 체계를 **폐지 예정(deprecated)** 으로 표시한다.
C# 의 [Obsolete] 가 호출 자리마다가 아니라 선언 한 곳에 붙고 컴파일러가 경고를 내듯이,
표시는 생성기 한 곳에 달고 `check` 가 그 경고를 낸다.

## 반드시 지킬 것

- **커밋하지 마라.** `git add` · `git commit` 금지. 고치고 보고만 한다.
- **`machine/xmldoc.py` 외의 파일을 고치지 마라.** 특히 아래 셋은 절대 건드리지 않는다:
    machine/comments.xml       ← 이유는 [사실 3]
    machine/terms-reading.json ← $50 짜리 산출물이다
    소스에 박힌 `# <include …/>` 블록 751곳
- **`xmldoc.py emit` 과 `xmldoc.py inject` 를 돌리지 마라.** 거대한 diff 가 난다([사실 3]).
- 주석과 문서는 **한국어**. 약어를 피한다.
- **코드 주석에는 현 상황만 적는다.** 날짜 · 측정 수치 · 확신도 표기 · 설계 철학 서사를
  코드에 남기지 않는다(이 저장소의 CLAUDE.md 규약). 폐지 사유 서사는 decisions 문서의 몫이다.
- **`# <include …/>` 블록을 손대지 마라** — `xmldoc.py` 자신의 파일 머리에도 하나 있다(2줄째).

## 실측된 사실 — 믿지 말고 재검증하라

[사실 1] `machine/xmldoc.py` 는 명령 셋을 갖는다. 파일 맨 끝:

    if __name__ == "__main__":
        ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
        ap.add_argument("cmd", choices=["emit", "inject", "check"])
        ...
        if a.cmd == "emit":   ...
        elif a.cmd == "inject": run_inject(a.dry_run, a.all_kinds)
        else: sys.exit(run_check())

[사실 2] `run_check()` 는 마지막에 이렇게 끝난다:

        for p in problems[:20]:
            print("실패", p)
        print(f"레퍼런스 확인 {seen}건 · 문제 {len(problems)}건")
        return 1 if problems else 0

  ⚠ `problems[:20]` 이라 **처음 20건만 보인다.** 지금 문제는 94건이다.

[사실 3] **`machine/comments.xml` 은 지금 `terms-reading.json` 과 5,686줄 어긋나 있다.**
  `emit_xml(terms)` 의 산출물인데 재조사(용어 898개) 뒤 `emit` 을 안 돌렸기 때문이다.
  그래서 comments.xml 을 건드리거나 `emit` 을 돌리면 **대기 중인 거대 재생성이 딸려 온다.**
  그 결정은 사용자에게 계류 중이다. 이 작업의 범위 밖이다.
  직접 확인하려면:

      .venv/bin/python -c "
      import sys, json; sys.path.insert(0,'machine')
      import xmldoc
      t = json.load(open(xmldoc.READING, encoding='utf-8'))
      print('동기인가:', xmldoc.emit_xml(t) == open(xmldoc.XML_ABS, encoding='utf-8').read())"

[사실 4] `.venv/bin/python machine/xmldoc.py check` 는 **지금도 종료 코드 1** 이다
  (문제 94건). 이 작업이 그 숫자를 **바꾸면 안 된다.**

## 할 일 — 둘뿐이다

### STEP 1 · 모듈 수준 폐지 표시

`machine/xmldoc.py` 의 모듈 독스트링(`"""xmldoc.py — …"""`) **안 맨 앞**에 한 문단을 넣는다.
독스트링 첫 줄은 `argparse` 의 description 으로 쓰이므로(사실 1) **첫 줄은 그대로 둔다.**
둘째 줄부터 아래를 끼운다:

    ⚠ **폐지 예정(deprecated).** 이 체계는 유지되지만 **새 코드에 새로 심지 않는다.**
    있는 레퍼런스는 그대로 두고 `inject` 로 갱신한다. 사유와 대체안 후보는
    docs/decisions/0007-xmldoc-include-deprecated.md 에 있다.

그리고 모듈 수준 상수를 하나 더한다(`ROOT` · `READING` 같은 상수들 근처, import 아래):

    # 이 주석 주입 체계는 폐지 예정이다. check 가 이 값을 배너로 낸다.
    DEPRECATED = "폐지 예정 — 새 코드에 <include …/> 를 새로 심지 않는다. docs/decisions/0007 참조."

### STEP 2 · `check` 가 배너를 낸다

`run_check()` 의 마지막 `print` **다음 줄**에 배너 한 줄을 더한다. 반환값은 바꾸지 않는다:

        print(f"레퍼런스 확인 {seen}건 · 문제 {len(problems)}건")
        print(f"알림 — {DEPRECATED}")
        return 1 if problems else 0

  ⚠ `return` 을 건드리지 마라. 폐지 표시는 **경고이지 실패가 아니다.**

## 경계

**소유** — `machine/xmldoc.py` 하나.

**건드리지 않음**

| 파일 | 이유 |
|---|---|
| `machine/comments.xml` | `emit_xml` 산출물이고 지금 5,686줄 어긋나 있다(사실 3) |
| `machine/terms-reading.json` | 재조사 산출물($50.73). 다른 작업이 소유한다 |
| 소스의 `# <include …/>` 751곳 | 재주입은 별개 작업이다 |
| `runner/**` · `viz/**` | 무관하다 |

**⚠ 워킹 트리에 다른 사람의 미커밋 작업이 있다** (2026-09-08 실측):

    M machine/terms-reading.json   M machine/test_survey_plan.py
    M runner/README.md             M runner/run_mode1.py
    M runner/test_run_mode1.py     M runner/wiki/{build,check,prep}.py
    M test/test_wiki.py

**`git add -A` 금지.** 애초에 커밋하지 않는다.

## 검증

    cd $REPO_ROOT
    .venv/bin/python machine/xmldoc.py check ; echo "종료 코드 $?"
    .venv/bin/python -m pytest -q
    .venv/bin/python tools/gen_readme.py --check machine runner viz tools
    npm run typecheck:py

**기대**

| 검사 | 기대 |
|---|---|
| `xmldoc.py check` 출력 | `레퍼런스 확인 751건 · 문제 94건` **뒤에 `알림 — 폐지 예정 …` 한 줄이 새로 붙는다** |
| `xmldoc.py check` 종료 코드 | **1 그대로.** 0 이 되거나 다른 값이 되면 잘못 고친 것이다 |
| 문제 건수 | **94 그대로.** 늘거나 줄면 범위를 벗어난 것이다 |
| `pytest` | 483 통과 · 19 건너뜀 (숫자가 줄면 안 된다) |
| `gen_readme --check` | `README 4개 — 소스와 일치` |
| `typecheck:py` | 0 errors |

**`xmldoc.py emit` 과 `inject` 는 검증에도 돌리지 마라.**

## 자기 점검 (보고 전에)

- [ ] 고친 파일이 `machine/xmldoc.py` **하나뿐인가** (`git status --short`)
- [ ] `run_check` 의 `return 1 if problems else 0` 을 그대로 두었는가
- [ ] 독스트링 **첫 줄**을 그대로 두었는가 (argparse description 으로 쓰인다)
- [ ] 코드 주석에 날짜·수치·설계 철학을 넣지 않았는가
- [ ] 커밋하지 않았는가

## 보고

- **상태** DONE / DONE_WITH_CONCERNS / BLOCKED
- **바뀐 파일** 경로 목록 (`git status --short` 출력 그대로)
- **검증 결과** 위 표의 다섯 항목 실제 출력
- **미룬 것** 과 이유
- **커밋 안 함**
```

## 오케스트레이터용 메모 (프롬프트 밖)

- 모형은 **Sonnet** 이면 충분하다. 파일 하나 · 삽입 두 곳 · 판단 자리 없음.
- 이 작업이 **하지 않는** 것 둘을 알아 둘 것:
  - `emit_xml()` 에 `deprecated` 속성을 더하는 것 — `comments.xml` 재생성(5,686줄)을 부르므로 뺐다.
    사용자가 대기 중인 `emit`/`inject` 결정을 내린 뒤에 함께 한다.
  - 대체 마크업 이주 — **대체안 자체가 미정**이다(0007 · 루트 `CLAUDE.md` 의 "혼자 정하지 말 것").
- 커밋 메시지 제안(사용자 승인 후): `[docs] : xmldoc 주석 주입에 폐지 예정 표시`

## 변경 이력

- 2026-09-08 — 최초 작성. 0007 의 안 A 를 실행 가능한 단위로 좁혔다. 작성 중 `comments.xml`
  이 `terms-reading.json` 과 5,686줄 어긋나 있음을 실측해 범위를 세 파일에서 한 파일로 줄였다.
