# HANDOFF — warmup 이 증분을 계산하고 나서 버린다

> 🔴 **상태 갱신 2026-09-08 — 이 문서는 아직 유효하다. 다만 착수 시점이 정해졌다.**
>
> **지금 착수하지 마라. 단계 기계 리팩터링이 끝난 뒤의 후속 작업이다.**
> 리팩터링 사양: [`../superpowers/specs/2026-09-08-runner-stage-machine-design.md`](../superpowers/specs/2026-09-08-runner-stage-machine-design.md)
>
> | 원인 | 2026-09-08 판정 | 누가 |
> |---|---|---|
> | ① `plan_stages` 가 `survey` 를 영구히 뺀다 | **흡수됨** — 리팩터링 D13(증분/전량 그래프 분리)이 정적 건너뜀을 없앤다 | 리팩터링 |
> | ② `targets` 가 프로세스 경계를 못 넘는다 | **흡수됨** — 리팩터링 D14(`survey-plan.json` 이 자기 범위를 싣는다) | 리팩터링 |
> | ③ 배치 id 가 위치 기반이라 샤드가 남의 배치를 대신한다 | 🔴 **미해결 · 이 문서 소관 · 리팩터링 후속** | 이 문서 |
> | ④ `merge_shards` 가 재조사를 충돌로 오인해 키를 개명한다 | 🔴 **미해결 · 이 문서 소관 · 리팩터링 후속** | 이 문서 |
>
> **왜 리팩터링이 먼저인가.** ③④ 를 고칠 자리가 리팩터링으로 **옮겨간다.**
> `run_layer` 는 `llmstage.perform` 안으로 들어가고, `merge_shards` 는 `survey` 단계의
> `harvest` 훅이 된다. 지금 고치면 고친 코드를 곧바로 옮기게 되어 두 번 일한다.
>
> **③④ 가 고쳐지기 전에는 증분 그래프를 쓰지 않는다.** 리팩터링 사양이 그 순서 제약을
> "순서 제약 — ③④가 먼저다" 절에 박아 두었다. 리팩터링이 끝나도 증분은 **아직 신뢰할 수 없다.**
>
> **재개 JSON(리팩터링 D12)은 단계 수준만 담는다** — 배치 수준 재개는 ③ 때문에 신뢰할 수 없어서다.
> ③ 이 고쳐지면 배치 수준 재개를 그 위에 얹는 것이 이 작업의 자연스러운 확장이다.
>
> 아래 본문의 재현 절차와 갈래표(③ → E/F, ④ → G/H)는 **그대로 유효하다.**
> 다만 착수 시점에 `file:line` 과 함수 이름을 **다시 실측하라** — 리팩터링이 전부 옮겨 놓았을 것이다.

> 작성 2026-09-07 · 기준 커밋 `60dfac5` · 실측 저장소 `$REPO_ROOT` (자기호스팅)
> 대상: 이 결함을 고칠 다른 Claude Code 세션
> 짝 문서: [`HANDOFF-2026-09-07-codegraph-id-namespace.md`](HANDOFF-2026-09-07-codegraph-id-namespace.md)
> — 둘 다 `runner/run_mode1.py` 를 고친다. **동시에 두 세션을 띄우지 말 것.** 이 문서를 먼저 한다

## TL;DR

증상은 "WarmUp 을 해 뒀는데 증분이 되지 않고 전수조사를 처음부터 반복했다" 이다.
**실측해 보니 원인이 셋이고, 성격이 다르다. 하나는 사람의 조작 실수이고 둘은 도구의 구조 결함이다.**

| # | 원인 | 성격 | 실측 |
|---|---|---|---|
| 1 | 레코드가 있으면 `plan_stages` 가 `survey` 를 단계 목록에서 **아예 뺀다** | **구조 결함** — 🟢 리팩터링 D13 이 흡수 | 아래 재현 ① |
| 2 | `targets` 는 프로세스 메모리라, `warmup` 과 `survey-plan` 을 **다른 호출로 쪼개면 조용히 전량으로 되돌아간다** | **구조 결함 (경고 없음)** — 🟢 리팩터링 D14 가 흡수 | 아래 재현 ② |
| 3 | 배치 id 가 위치 기반이라 계획이 바뀌면 **남은 샤드가 다른 배치를 대신한다** | 🔴 **미해결 — 이 문서 소관** | 아래 재현 ③ |
| 4 | `merge_shards` 가 **같은 심볼의 재조사를 "충돌" 로 오인**해 레코드 키를 개명한다 | 🔴 **미해결 — 이 문서 소관 · 증분의 진짜 걸림돌** | 아래 재현 ④ |

**④ 가 증분 작업의 진짜 걸림돌이다.** ①②③ 을 다 고쳐도 ④ 가 남으면 증분 재조사를 돌릴 때마다
레코드 키가 갈려 나가고, 소스의 주석 마커(`# <include … @id='…'/>`)와의 연결이 끊긴다.

**2026-09-07 의 전량 재조사($50.73 · 89배치)는 ②를 작업자가 밟아서 일어났다.**
warmup 은 제대로 49개 파일을 골라냈고, 계획을 좁히는 장치도 멀쩡히 작동한다 —
다만 그 둘을 잇는 통로가 프로세스 경계를 못 넘는다.

**증분 장치 자체는 정상이다.** 한 프로세스에서 돌리면 88배치 → **17배치**로 좁혀진다(재현 ②).

## 재현 — 믿지 말고 직접 돌려라

### ① `survey` 는 기본 경로에서 불릴 수 없다

```bash
cd $REPO_ROOT
.venv/bin/python -c "
import sys; sys.path.insert(0,'runner')
import run_mode1 as R
print('레코드 있음:', R.plan_stages(True, True, False))
print('레코드 없음:', R.plan_stages(True, False, False))
print('should_call_agent(바뀐파일 7개, 레코드 있음) ->', R.should_call_agent(['a']*7, True))
"
```

**2026-09-07 실측 출력:**

```
레코드 있음: ['lang-select','prep','warmup','survey-plan','warmup-save','terms','wiki','build','check']
레코드 없음: ['lang-select','prep','warmup','survey-plan','survey','warmup-save','terms','wiki','build','check']
should_call_agent(바뀐파일 7개, 레코드 있음) -> True
```

읽어야 할 것 — **`terms-reading.json` 이 한 번 생기고 나면 `survey` 가 목록에서 영구히 빠진다.**
`should_call_agent` 는 "불러야 한다(True)" 라고 답하는데 **불릴 자리가 없다.**
warmup 이 파일을 고르고 `survey-plan` 이 계획을 좁혀 놓아도 그것을 쓸 단계가 없다.

문제의 줄 — `runner/run_mode1.py` 의 `plan_stages`:

```python
if s == "survey" and has_reading:
    continue
```

**정적 건너뜀(`plan_stages`)과 동적 건너뜀(`should_call_agent`)이 겹쳐 있고 정적 쪽이 이긴다.**
`should_call_agent` 의 독스트링은 "빈 목록(`[]`)은 정말로 바뀐 것이 없다는 판정이다. 그때만 …
건너뛴다" 라고 적어 두었다 — **그 함수는 자기가 기본 경로에서 불릴 것을 전제로 쓰였다.**
지금은 `--only` 로 강제할 때만 불린다.

### ② 단계를 쪼개면 좁히기가 조용히 사라진다

```bash
cd $REPO_ROOT
cp out/codegraph-raw/survey-plan.json /tmp/plan-backup.json     # 원복용
.venv/bin/python runner/run_mode1.py . --only warmup,survey-plan | grep -E "증분|합계 —"
cp /tmp/plan-backup.json out/codegraph-raw/survey-plan.json     # 반드시 원복
```

**2026-09-07 실측 출력:**

```
… survey-plan.json (증분: warmup 이 준 7파일)
  합계 — 심볼 203 · 층 5 · 배치 17 (LLM 세션이 그만큼 뜬다)
```

같은 저장소에서 **전량은 배치 88개**다. 즉 좁히기는 작동한다.

**그런데 이렇게 쪼개면 사라진다:**

```bash
.venv/bin/python runner/run_mode1.py . --only prep,survey-plan   # ← targets 가 None
.venv/bin/python runner/run_mode1.py . --only warmup,survey      # ← 디스크의 전량 계획을 읽는다
```

메커니즘 — `survey-plan` 단계가 증분 장치 본체다:

```python
plan_json = survey_plan.plan(json.load(f), a.target, only_files=targets)
```

`targets` 는 `warmup` 단계가 **같은 프로세스의 지역 변수**에 담아 둔 것이고 **파일로 남지 않는다.**
`survey-plan` 이 그 호출에 없으면 `plan_json` 은 `None` 인 채로 `survey` 로 내려가고, 거기서
디스크의 계획을 그대로 읽는다:

```
층 계획을 디스크에서 읽었다 — …/survey-plan.json
```

**이때 아무 경고도 나오지 않는다.** 그 계획이 좁혀진 것인지 전량인지 화면에 구분이 없다.
`targets` 는 프롬프트의 범위 지시문으로는 계속 넘어가므로, **"증분이라고 말하는 프롬프트를 든
전량 배치 88개"** 라는 최악의 조합이 조용히 만들어진다. 2026-09-07 에 실제로 그렇게 돌았다.

### ③ 배치 id 는 위치 기반이라 샤드 재사용이 불건전하다

```bash
cd $REPO_ROOT
.venv/bin/python -c "
import json, sys; sys.path.insert(0,'machine')
import survey_plan
cg=json.load(open('out/codegraph-raw/codegraph.json'))
full=survey_plan.plan(cg,8)
narrow=survey_plan.plan(cg,8, only_files=['machine/xmldoc.py','machine/warmup.py','runner/dispatch.py'])
def ids(p): return {b['id']: tuple(sorted(s['name'] for s in b['symbols']))
                    for L in p['layers'] for b in L.get('batches',[])}
F,N=ids(full),ids(narrow); common=sorted(set(F)&set(N))
print('전량',len(F),'· 좁힘',len(N),'· id 겹침',len(common))
print('  같은 묶음:',sum(1 for k in common if F[k]==N[k]))
print('  다른 묶음:',sum(1 for k in common if F[k]!=N[k]))
k=[k for k in common if F[k]!=N[k]][0]
print(k,'전량:',F[k][:2]); print(k,'좁힘:',N[k][:2])
"
```

**2026-09-07 실측 출력:**

```
전량 88 · 좁힘 9 · id 겹침 9
  같은 묶음: 0
  다른 묶음: 9
L0-B00 전량: ('machine.clang_doc.Symbol', 'machine.clang_doc._json_root')
L0-B00 좁힘: ('machine.warmup.Entry', 'machine.warmup.blast_radius')
```

(`common` 을 `sorted` 로 감싸지 않으면 예시로 뽑히는 id 가 실행마다 달라진다. 숫자 셋은 그대로다.)

**겹치는 id 9개가 전부 다른 심볼 묶음이다.** 그리고 `run_survey` 는 샤드가 있으면 그 배치를
건너뛴다(J4):

```python
jobs = [(bid, pr) for bid, pr in jobs
        if not os.path.exists(os.path.join(shard_dir, bid + ".json"))]
```

**두 사실이 만나면 조용한 오염이 된다** — 지난 실행이 남긴 `L1-B02.json`(normalize 심볼들)이
이번 계획의 `L1-B02`(dispatch 심볼)를 "이미 했다" 로 만든다. 오류가 나지 않고, 조사되지 않은
심볼이 조사된 것으로 남는다.

**2026-09-07 세션은 이것을 의심해 샤드 74개를 손으로 치웠다**(`out/codegraph-raw/_shards.old-20260907/`).
그 판단은 맞았지만, 도구가 사람에게 그 판단을 떠넘기고 있다는 뜻이기도 하다.

### ④ 재조사가 레코드 키를 갈아 버린다 — 주석 마커와의 연결이 끊긴다

2026-09-07 재조사 직후 실측:

| | 값 |
|---|---|
| 옛 키 | 813 |
| 새 키 | 898 |
| **유지된 키** | **138** |
| **개명된 키** | **675** |
| 진짜 새 심볼 | 85 |

개명의 꼴 — 소스 마커가 가리키는 이름이 왼쪽이다:

```
옛: machine.clang_doc.Symbol                 ← runner/wiki 소스의 <include @id='…'> 가 이것을 쓴다
새: clang_doc.machine.clang_doc.Symbol       ← 줄기가 중복됐다
```

**원인** — `merge_shards` ([`runner/run_mode1.py:906`](../../runner/run_mode1.py#L906)):

```python
if key in got and got[key] != rec:
    old = got.pop(key)
    got[_qualified(key, old)] = old      # <파일줄기>.<원래키>
    got[_qualified(key, rec)] = rec      # 둘이 같은 이름으로 가서 뒤엣것이 이긴다
```

`got` 의 초기값은 **조사 이전의 원본 레코드**(baseline)다. 같은 심볼을 다시 조사하면
`means` 문장이 조금이라도 달라지므로 `got[key] != rec` 가 참이 되고, **"두 심볼이 이름을
겹쳤다" 로 오인해 개명**한다. 실제로는 **같은 심볼의 갱신**이다.

`_qualified` 는 `<where 의 파일 줄기>.<키>` 이므로 ([`runner/run_mode1.py:948`](../../runner/run_mode1.py#L948)),
원래 키가 이미 FQN 이면 줄기가 한 번 더 붙어 `clang_doc.machine.clang_doc.Symbol` 이 된다.

**파급** — `machine/xmldoc.py check` 가 **문제 0건 → 737건**이 됐다. 소스의 마커는 옛 id 를
가리키는데 레코드에는 그 id 가 없어서다.

**되돌릴 수 있다(실측).** 개명은 결정론이라 앞 조각을 떼면 옛 키가 나온다 — 새 키 760개 중
**675개가 정확히 그렇게 복원**됐고, 복원 후 `xmldoc check` 는 737건 → 94건으로 떨어졌다.
남은 94건은 **진짜 새 심볼 85개**가 아직 마커를 못 받은 정상 상태다.
2026-09-07 세션이 이 복원을 이미 적용해 두었다 — `machine/terms-reading.json` 이 그 상태다.

**고칠 자리** — 충돌 판정이 "같은 키 + 다른 내용" 이면 안 된다. 후보:

| 갈래 | 무엇 | 대가 |
|---|---|---|
| G | baseline 에서 온 키는 **갱신으로 본다**(개명하지 않는다). 충돌 판정은 **같은 층의 샤드끼리만** | 의미가 맞다. `merge_shards` 가 baseline 출처를 알아야 한다 |
| H | 레코드에 코드지도 `id` 를 싣고 그것으로 동일성을 판정한다 | 이름과 무관해진다. 결함1(이름공간) 해결과 한 묶음이 된다 |

💭 **판단(신뢰도 🟡 60):** H 가 결함1과 함께 풀리므로 이득이 크다. G 는 더 좁고 안전하다.
**제안이지 결정이 아니다.**

## 실측된 사실 — file:line

| 자리 | 무엇 |
|---|---|
| `runner/run_mode1.py` `plan_stages` | `if s == "survey" and has_reading: continue` — ①의 자리 |
| `runner/run_mode1.py` `should_call_agent` | 동적 판정. ① 때문에 기본 경로에서 죽은 코드다 |
| `runner/run_mode1.py` `main` 의 `survey-plan` 가지 | `survey_plan.plan(…, only_files=targets)` — 증분 장치 본체 |
| `runner/run_mode1.py` `main` 의 `AGENT_STAGES` 가지 | `plan_json is None` 이면 디스크에서 읽는다 — ②가 새는 자리 |
| `runner/run_mode1.py` `run_survey` | 샤드 존재로 배치를 거른다(J4) — ③의 자리 |
| `machine/survey_plan.py` `plan(…, only_files=…)` | 좁히기 구현. **정상 작동한다** |
| `machine/warmup.py` | 판정 넷(`유효`·`위치만`·`재읽기`·`삭제됨`). **정상 작동한다** |

**2026-09-07 warmup 실측:** py 파일 78개 — 유효 36 · 재읽기 39 · 위치만 3 · 삭제됨 0 →
1홉 퍼뜨려 49개(64.1%). 전수조사 뒤 `warmup-save` 가 확정한 다음에는 7개로 떨어졌다.
**즉 매니페스트 갱신도 정상이다.**

## 무엇을 고칠지는 열려 있다 — 혼자 정하지 말 것

`CLAUDE.md` 의 "혼자 정하지 말 것" 이 걸리는 자리다. 아래는 **후보이지 결정이 아니다.**

**① 에 대해**

| 갈래 | 무엇 | 대가 |
|---|---|---|
| A | `plan_stages` 에서 `survey` 정적 건너뜀을 없애고 `should_call_agent` 에 맡긴다 | 바뀐 것이 0이면 세션 0개로 끝나므로 비용은 안 는다. **다만 warmup 이 판정 못 하면(`targets is None`) 전량으로 도는 기존 동작이 기본 경로에 살아난다** — 실수로 $50 짜리 실행이 시작될 수 있다 |
| B | 그대로 두고 문서에 "증분은 `--only` 로만" 이라고 못박는다 | 도구가 사람 기억에 기댄다 |

**② 에 대해**

| 갈래 | 무엇 | 대가 |
|---|---|---|
| C | `targets` 를 계획 파일 안에 적는다(예: `survey-plan.json` 에 `only_files` 칸) | 프로세스를 쪼개도 살아남는다. 계획이 자기가 좁혀진 것인지 스스로 말한다 |
| D | 디스크에서 계획을 읽을 때 **경고를 낸다** — "이 계획은 전량이다. warmup 의 범위가 반영되지 않았다" | 가장 싸다. 조용한 실패를 시끄럽게 만든다 |

**③ 에 대해**

| 갈래 | 무엇 | 대가 |
|---|---|---|
| E | 배치 id 를 위치(`L1-B02`)가 아니라 **내용 해시**로 매긴다 | 계획이 바뀌면 id 도 바뀌어 샤드가 저절로 무효가 된다. 재개도 정확해진다 |
| F | 샤드 안에 자기 심볼 목록을 적고, 건너뛰기 전에 **대조**한다 | id 규칙을 안 바꾼다. 검사 한 번이 는다 |

💭 **판단(신뢰도 🟡 65):** D → E → A 순으로 하는 것이 위험 대비 이득이 좋아 보인다.
D 는 한 줄짜리인데 2026-09-07 의 $50 사고를 막았을 것이고, E 는 ③의 조용한 오염을 구조로 없앤다.
A 는 마지막에 — 기본 경로에서 비싼 실행이 자동으로 시작될 수 있어 별도 안전장치(예: 예상 세션
수를 먼저 보이고 확인받기)와 함께 가는 것이 낫다. **제안이지 결정이 아니다.**

## 경계 (Boundaries)

**소유**

- `runner/run_mode1.py` 의 `plan_stages` · `should_call_agent` · `main` 의 단계 갈림 · `run_survey`
- `machine/survey_plan.py` 의 배치 id 매김 (갈래 E 를 고를 때만)
- `runner/test_run_mode1.py` · `machine/test_survey_plan.py` 에 시험 추가

**건드리지 않는 것**

- `machine/warmup.py` 의 판정 로직 — **실측으로 정상 확인됐다.** 여기서 원인을 찾지 마라
- `machine/terms-reading.json` — $50.73 짜리 산출물이다
- `out/codegraph-raw/_shards.old-20260907/` — 2026-09-07 이전 조사 결과의 백업. 지우지 마라

**⚠ 커밋되지 않은 작업이 있다** (2026-09-07 기준, `git status`):

| 파일 | 무엇 | 누구 |
|---|---|---|
| `runner/run_mode1.py` | 주석의 `LLM Model` → `Model` 이름 바꾸기 27줄. 로직 변경 없음 | 사용자가 IDE 에서 작업 중 |
| `runner/wiki/prep.py` · `runner/wiki/build.py` · `runner/wiki/check.py` | ⑴ 스크립트 실행 시 `ModuleNotFoundError` 수정 ⑵ VitePress `ignoreDeadLinks` ⑶ `check` 의 종료 코드 뒤집힘 수정 | 2026-09-07 세션 |
| `runner/test_run_mode1.py` · `test/test_wiki.py` | 위 셋의 회귀 시험 | 같음 |
| `machine/test_survey_plan.py` | 층 분포 기대값 갱신 (`[232,217,145,87,12,4]`/697 → `[287,254,146,86,9,4]`/786). 코드지도 재수집으로 실제 값이 바뀌었고, 그 시험의 독스트링이 "코드가 바뀌면 기대값을 함께 고친다" 라고 지시한다 | 같음 |
| `machine/terms-reading.json` | 재조사 결과 898개 + **④ 의 키 복원 적용본** | 같음 |
| `CLAUDE.md` · `runner/README.md` | 게이트 실측값 · 자동 생성 README 갱신 | 같음 |
| `docs/wiki/` (미추적) | Mode 1 이 만든 위키 산문 21장 | 같음 |

**⚠ `machine/xmldoc.py check` 는 지금 문제 94건이다** — ④ 의 여파로 새 심볼 85개가 마커를
못 받은 상태다. `xmldoc.py emit` → `inject` 를 돌리면 0 이 되지만 **소스 전반의 주석 블록이
다시 쓰이는 큰 diff** 가 난다(comments.xml 만 해도 4884줄 변경). 사용자 판단 대기 중이다.
이 작업을 시작하기 전에 그 결정이 났는지 확인한다.

**`runner/run_mode1.py` 는 사용자가 열어 두고 있고 이 작업의 주 대상이다.**
시작 전에 `git status` 로 다시 확인하고, 충돌하면 사용자에게 묻는다. **`git add -A` 금지.**

## 가드레일 (프로젝트 규약 — Step 0 실측)

- **커밋하지 않는다.** 사용자 요청 시에만. 형식은 `personal-commit-messages` 스킬 —
  소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음, 트레일러 없음
- **시험 먼저 쓴다**(TDD)
- **코드 주석에는 현 상황만** — 날짜 · 측정 수치 · 확신도 표기 · 번복 기록을 코드에 남기지 않는다.
  형식·동작 사실은 남긴다
- **`# <include …/>` 블록은 손대지 않는다** — `machine/xmldoc.py` 가 주입한다. 함수를 새로
  만들었으면 `terms-reading.json` 에 레코드를 쓰고 `xmldoc.py emit` → `inject`
- **`--dry-run` 은 좁히기를 반영하지 않는다** — dry-run 가지는 `only_files` 없이 계획을 미리
  계산하므로 늘 전량을 보인다. 고칠 때 이 갈래도 함께 볼 것

## 검증 (Verify)

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest -q                                   # 기대: 483 통과 · 20 건너뜀 이상
npm test && npm run typecheck && npm run typecheck:py
.venv/bin/python machine/xmldoc.py check
.venv/bin/python tools/gen_readme.py --check machine runner viz tools
```

**이 작업 고유의 검증 — 위 재현 ①②③을 다시 돌려 숫자가 바뀌었는지 본다.**

**⚠ 실제 `survey` 를 돌려 검증하지 마라.** 세션당 약 $0.5 다 — 2026-09-07 의 89배치가 $50.73 였다.
계획 단계(`--only warmup,survey-plan`)와 순수 함수 시험까지만으로 검증한다.
**돌려야 한다면 사용자에게 예상 세션 수와 비용을 먼저 보이고 승인받는다.**

## 보고 (Report)

- **상태** DONE / DONE_WITH_CONCERNS / BLOCKED
- **고른 갈래** ①②③ 각각에 대해 무엇을 골랐고 왜 (사용자 승인 여부 명시)
- **바뀐 파일** 경로 목록
- **검증 결과** 게이트 출력 + 재현 ①②③의 before/after 숫자
- **미룬 것** 과 이유
- **커밋 안 함**

## 변경 이력

- 2026-09-08 — 착수 시점을 못박았다. ①②는 단계 기계 리팩터링(D13·D14)이 흡수하고,
  ③④만 이 문서 소관으로 남아 **리팩터링 후속**이 된다. 고칠 자리가 리팩터링으로 옮겨가기 때문이다.

- 2026-09-07 — 최초 작성. Mode 1 자기호스팅 실행 중 "증분이 안 된다" 는 사용자 지적에서 출발해
  원인 셋을 갈라 실측했다. 전량 재조사의 직접 원인은 ②(작업자가 단계를 쪼갬)였고, ①③은 그와
  별개로 남아 있는 구조 결함이다.
