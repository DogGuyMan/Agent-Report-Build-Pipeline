# Mode 1 을 단계 기계 위로 — 사람이 읽는 요약

> 에이전트용 전문은 [`2026-09-11-runner-mode1.md`](2026-09-11-runner-mode1.md) (1,500줄). 이 문서는 그것의 **판정용 요약**이다.
> 여기서 정한 것이 전문을 이긴다 — 둘이 어긋나면 이 문서를 고치고 전문을 따라 고친다.

## 1. 무엇을 하는가 — 한 문단

`runner/run_mode1.py` 는 1,147줄이고, 단계 열 개가 `if/elif` 한 덩어리 안에 산다. 1·2단계에서 만든
**단계 기계**(`runner/pipeline.py`) 위에 Mode 2 와 Mode 1.5 는 이미 올라갔고, **Mode 1 만 남았다.**
이 계획은 그것을 올린다. 올리면서 셋을 함께 고친다 — 증분 판정을 **파일**로 남기고, 전량과 증분을
**두 그래프**로 가르고, 멈춘 자리에서 다시 시작할 **재개 파일**을 남긴다.

## 2. 결과 — 파일이 어떻게 바뀌나

```
지금                              뒤
runner/run_mode1.py  1,147줄      runner/run_mode1.py    main + 옛 이름 재수출 (~250줄)
                                  runner/mode1/
                                    context.py           문맥 한 상자 · 산출물 10개
                                    diff.py              changes.json  ← 새 파일
                                    prompts.py           프롬프트 (그대로 옮김)
                                    layers.py            층 · 샤드 병합 (그대로 옮김)
                                    stages.py            단계 12개
                                    edges.py             전이표 · 팩토리
                                    resume.py            resume.json       ← 새 파일
```

단계는 열에서 **열둘**이 된다 — `lang-select` 와 `wiki` 가 각각 둘로 갈린다.

```
증분:  lang-hint ▶ lang-decide ▶ detect-changes ▶ collect-graph ▶ schedule-batches ▶ annotate-symbols
       ▶ snapshot-sources ▶ verify-terms ▶ outline-wiki ▶ write-wiki ▶ publish-wiki ▶ verify-wiki
전량:  같되 detect-changes 가 없다 (11개)

          LLM(싼)  기계      대조→changes   수집      층·배치        LLM 층별
          지문 찍기         기계          LLM 1회     LLM 층별    기계        기계

| 옛 | 새 | 산출 파일 |
|---|---|---|
| lang-select | lang-hint + lang-decide | lang-select.json |
| warmup | detect-changes | changes.json (새 파일) |
| prep | collect-graph | codegraph.json |
| survey-plan | schedule-batches | batches.json (← survey-plan.json) |
| survey | annotate-symbols | terms-reading.json |
| warmup-save | snapshot-sources | snapshot.json (← warmup.json, 한 번짜리 이주) |
| terms | verify-terms | terms-db.json |
| wiki-catalogue | outline-wiki | outline.json (← wiki-plan.json) |
| wiki-pages | write-wiki | docs/wiki/*.md |
| build | publish-wiki | VitePress dist/ |
| check | verify-wiki | — |

결 — 전부 **동사-목적어.** 위키 넷이 `outline · write · publish · verify` 한 줄, 검증 둘이 `verify-terms · verify-wiki` 짝.
옛 이름 열 개는 `--only` 별명으로 산다.
```

## 3. 오늘(09-11) 결정이 어디에 들어갔나

| 결정 | 한 줄 | 계획의 자리 |
|---|---|---|
| **diff 는 파일이다** (D14) | `detect-changes` 이 `out/codegraph-raw/changes.json` 을 쓴다. 유효·재읽기·위치만·삭제됨 넷 전부 | Task 3 |
| **지시서와 대조한다** (D14) | `annotate-symbols` 가 시작 전에 계획과 diff 를 **양방향**으로 맞춰 본다. 어긋나면 세션 하나도 안 띄우고 멈춘다 | Task 7 |
| **prep 이 diff 를 본다** (D15) | 증분: 바뀐 게 하나라도 있으면 다시 수집. 전량: `--force` 로 무조건. "파일이 있으면 건너뜀" 판정이 사라진다 | Task 4 |
| **락은 뒤로** (D17) | 배치 id 가 위치 기반이라 지금 넣으면 남의 배치를 막는다. 결함 ③ 뒤 | 범위 밖 |
| **삭제된 파일의 레코드** | diff 에 **싣기만**. 지우는 건 결함 ④ 고칠 때 같은 자리에서 | 범위 밖 |

**왜 양방향인가.** 계획이 diff 보다 **넓으면** 전량 지시서에 부분 쪽지가 붙은 것 — 7월의 $50 사고다.
**좁으면** 부분 지시서에 전량 쪽지 — 레코드가 조용히 빈다. 두 번째가 더 위험하다.

## 4. 판정이 필요한 것 둘 — 착수 전에

**① 🔴 확정 (2026-09-11) — 전량 그래프에는 `detect-changes` 이 없다. `snapshot-sources` 가 끝에 직접 훑어 지문을 찍는다.**

먼저 낱말부터. `snapshot.json` 은 **옛 판의 지문**이다 — 지난 조사 때 파일마다 찍어 둔 해시(바이트 · 선언).
`changes.json` 은 그 지문과 지금 소스를 **대조한 결과**다. 지문이 없으면 대조할 것이 없어 diff 를 못 낸다.

| | 전량 (`--cold` · 첫 실행) | 증분 |
|---|---|---|
| 옛 지문 | 없거나 안 쓴다 | 있다 |
| `detect-changes` (대조 → diff) | **없다.** 대조할 것이 없는데 대조 단계를 돌리고 버리지 않는다 | 있다 |
| `changes.json` | **안 생긴다** — 전량에는 diff 가 없다는 것이 불변식 | 생긴다 |
| `collect-graph` | `--force` 로 무조건 재수집 | diff 를 보고 재수집 여부 판정 |
| `annotate-symbols` | diff 대조 없음 | diff 와 양방향 대조 |
| `snapshot-sources` (지문 찍기) | **있다.** 끝에 직접 훑어 찍는다 — 다음 실행이 증분을 시작할 옛 판이 된다 | 있다. `detect-changes` 이 넘긴 것을 찍는다 |

스펙 D13 의 그림이 **그대로** 맞다. 이전 판(메모 ①)은 전량에도 `detect-changes` 을 두려 했는데, 그것은 대조할 옛
지문이 없는 자리에서 대조 단계를 돌리는 것이라 물렸다. graphify 의 매니페스트 운용(늘 갱신되는 색인, 조건부
단계 아님)이 결정에 참고가 됐다. **두 안 모두 `collect-graph` 에 `--force` 가 필요했다** — 앞선 계획에서 빠져 있던 것.

**② D15 는 두 걸음으로 나눈다.** 수집기(clang-uml · roslyn-dump · griffe)가 파일 목록을 받는지 아직
재지 않았다. 그래서 이 계획은 "바뀐 파일만 수집"(둘째 걸음)이 아니라 "**다시 수집할지의 판정**"(첫 걸음)만
한다. 지금의 결함 — 지도가 낡은 채 남는 것 — 은 첫 걸음으로 사라진다.
→ 이 나눔에 이견이 없는지 판정.

**작은 것 하나 — D4 의 폴백 표현.** 스펙은 `lang-propose 실패 → lang-decide` 간선으로 적었다. 계획은
`lang-hint` 가 실패를 **`SKIP`** 으로 내고 `SKIP → 다음` 으로 잇는다. 같은 효과다. 관문이 아닌 단계의
실패를 "실패" 라 부르지 않는 편이 정직해서다.

## 5. Task 12개 — 한 줄씩

| # | 무엇 | 성격 |
|---|---|---|
| 1 | 패키지 뼈대 · 문맥 상자 · 산출물 10개 선언 | 신설 |
| 2 | 프롬프트와 층 코드를 **그대로** 옮기고 옛 이름 재수출 | 이동. 시험 963줄 한 줄도 안 고침 |
| 3 | `changes.json` 형 · 쓰기 · 읽기 · 검사 | 신설 (D14) |
| 4 | `prep.py` 에 `--diff` 하나 | 얼갈이 경계를 한 파일만큼 연다 (D15) |
| 5 | 기계 단계 여섯 (`collect-graph` · `schedule-batches` · `snapshot-sources` · `verify-terms` · `publish-wiki` · `verify-wiki`) | 이동 |
| 6 | `lang-hint` + `lang-decide` | 쪼갬 (D4) |
| 7 | `detect-changes` 이 diff 를 쓰고 `annotate-symbols` 가 대조한다 | 핵심 (D14) |
| 8 | `outline-wiki` + `write-wiki` | 쪼갬 (D16) |
| 9 | 전이표 · 팩토리 · `--cold` · 옛 이름 별명 | 신설 (D13 · D9) |
| 10 | `resume.json` 쓰기 · 읽기 · 팩토리에 먹이기 | 신설 (D12) |
| 11 | `main` 을 그래프 위로. `--dry-run` 이 흐름과 좁힌 계획을 찍는다 | 교체 |
| 12 | 게이트 일곱 · 문서 · `Any` 게이트 확장 · 인계 문서 배너 갱신 | 마무리 |

**Task 4 끝과 Task 9 끝에 판정 요청이 있다** — 위 §4 의 둘, 그리고 `collect-graph` 을 `collect` + `facts` 로 쪼갤지.

## 6. 하지 않는 것

| 무엇 | 왜 지금 아닌가 |
|---|---|
| 락(claim 파일, D17) | 배치 id 가 위치 기반(`L0-B00`). 내용 해시 id(결함 ③)가 먼저 |
| 삭제된 파일의 옛 레코드 지우기 | 지우는 자리(`merge_shards`)가 결함 ④ 의 수정 대상 |
| 바뀐 파일만 수집 (D15 둘째 걸음) | 수집기가 부분 수집을 받는지 안 잼 |
| `collect-graph` 을 둘로 쪼개기 | 관찰만 있고 판정이 없다 → Task 4 끝에 묻는다 |
| 결함 ③④ 자체 | 인계 문서 소관. **이 계획 뒤.** 고칠 자리가 이 계획으로 옮겨간다 |
| `xmldoc` 재주입 | 1·2·3단계가 옮긴 심볼 전부를 **한 번에**. 이 계획 뒤 |

**증분 그래프는 만들되 "된다" 고 말하지 않는다.** ③④ 가 남아 있는 동안은 전량으로만 쓴다.

## 7. 끝났다고 말할 조건

- `run_mode1.py` 에 `for stage in` 이 없다
- 시험 **562 이상 통과 · 실패 0**. 시험 파일 963줄은 손대지 않았다 (지운 시험이 있으면 이름이 보고에 있다)
- `changes.json` 이 실제로 생긴다 — 자기 저장소에 `--only warmup` (LLM 0)
- `--only survey` 를 diff 없이 부르면 **팩토리가 거부**한다
- 낡은 전량 계획 + 좁힌 diff 로 `--only survey` 를 부르면 **`annotate-symbols` 가 멈춘다** — 7월 사고가 더는 재현되지 않는다
- `Any` 0 · `pyright` 0 · README 일치

## 8. 이 계획 뒤

1. `xmldoc emit → inject` 한 번 (0007 의 폐지 속성도 이때)
2. 결함 ③④ → 그 뒤 D17 락 · 삭제됨 삭제
3. D15 둘째 걸음 — 수집기별로
4. 그제야 증분 그래프를 실제로 쓴다
