# HANDOFF — 코드지도 노드 id 와 레코드 키의 이름공간 불일치

> 작성 2026-09-07 · 기준 커밋 `60dfac5` · 실측 저장소 `$REPO_ROOT` (자기호스팅)
> 대상: 이 결함을 고칠 다른 Claude Code 세션
> 짝 문서: [`HANDOFF-2026-09-07-warmup-increment-unreachable.md`](HANDOFF-2026-09-07-warmup-increment-unreachable.md) — **먼저 이 문서를 읽는다.** 그쪽은 증분 경로 문제이고 여기는 이름공간 문제다. 둘 다 `runner/run_mode1.py` 를 고치므로 **동시에 두 세션을 띄우지 말 것**

## TL;DR

전수조사 배치 프롬프트는 세션에게 의존 대상을 **코드지도 노드 id**(`C85`, `C86`)로 건네준다.
그런데 그 id 를 받아 쓰는 두 곳은 **레코드 키**(세션이 정하고 충돌 시 `<파일줄기>.<이름>` 으로
개명된 이름)를 기대한다. 두 이름공간이 만난 적이 없다.

**결과가 둘이고, 둘째가 훨씬 크다.**

| # | 증상 | 실측 |
|---|---|---|
| 1 | `terms` 인용 검사가 `uses.to 가 용어에 없다` 로 무더기 실패 | 실패 490건 중 **375건(77%)** 이 `C<숫자>` 꼴 |
| 2 | **층 오름차순 설계의 이득이 통째로 0** — 모든 배치가 "너는 최하층이다" 를 받는다 | `dep_excerpt` 조회 **895건 중 0건** 적중 · **88개 배치 전부** 발췌가 비었다 |

②가 이 문서의 핵심이다. `survey_plan.py` 로 층을 나누고 층 오름차순으로 도는 이유가
"아래층 결과를 위층에 물려준다" 인데, **물려주는 통로가 처음부터 끊겨 있었다.**

## 재현 — 믿지 말고 직접 돌려라

```bash
cd $REPO_ROOT
.venv/bin/python -c "
import json, sys
sys.path.insert(0,'runner'); sys.path.insert(0,'machine')
import run_mode1 as R
plan=json.load(open('out/codegraph-raw/survey-plan.json'))
recs=json.load(open('machine/terms-reading.json'))
hit=miss=empty=total=0
for L in plan['layers']:
    for b in L.get('batches',[]):
        total+=1
        if not R.dep_excerpt(recs, b).strip(): empty+=1
        for s in b.get('symbols',[]):
            for d in s.get('depends_on',[]):
                if d in recs: hit+=1
                else: miss+=1
print('배치',total,'중 발췌가 빈 것:',empty,'· 조회 적중:',hit,'· 빗나감:',miss)
"
```

**2026-09-07 실측 출력:** `배치 88 중 발췌가 빈 것: 88 · 조회 적중: 0 · 빗나감: 895`

## 실측된 사실 — file:line

세 이름공간이 있다. **이것이 문제의 전부다.**

| 이름공간 | 예 | 어디서 나오나 |
|---|---|---|
| 코드지도 **노드 id** | `C88` | `machine/normalize.py` 가 매긴다. 787노드 전부 `C<숫자>` |
| 코드지도 **노드 name** (FQN) | `machine.clang_doc._symbol` | 같은 노드의 다른 칸 |
| 레코드 **키** | `load_clang_doc` 또는 `clang_doc.machine.clang_doc.load_clang_doc` | **세션이 정한다.** 충돌하면 `merge_shards` 가 개명 |

- **노드는 id 와 name 을 둘 다 갖는다.** 매핑이 이미 코드지도 안에 있다:
  ```json
  {"id": "C88", "name": "machine.clang_doc._symbol", "kind": "function",
   "module": "machine", "file": "machine/clang_doc.py", "line": 123, "signature": "…"}
  ```
- **층 계획의 `depends_on` 은 노드 id 다.** `out/codegraph-raw/survey-plan.json` 의 심볼:
  `{"id": "C88", "depends_on": ["C85", "C86"], …}`
- **프롬프트가 그 id 를 그대로 세션에게 준다** — [`runner/run_mode1.py:442`](../../runner/run_mode1.py#L442)
  의 `"  - %s (%s) %s:%s   의존 -> %s"`. 세션은 시키는 대로 그 id 를 `uses[].to` 에 적었다.
  **세션이 이름을 지어낸 것이 아니다** — 이 오해를 하지 말 것.
- **소비처 1** `dep_excerpt` — `runner/run_mode1.py` 의 함수. `depends_on` 을 `merged`(레코드
  사전)에서 곧장 찾는다. C-id 는 레코드 키가 아니므로 전량 빗나간다.
- **소비처 2** `check_terms` — [`machine/terms_db.py:370-371`](../../machine/terms_db.py#L370-L371)
  의 `if u.get("to") not in db`. 같은 이유로 실패를 낸다.
- **레코드 키는 세션이 정한다** — `merge_shards` ([`runner/run_mode1.py:906`](../../runner/run_mode1.py#L906))
  가 겹칠 때만 `_qualified` 로 `<파일줄기>.<이름>` 개명을 한다. 그래서 **키를 FQN 으로 가정해도 안 된다.**
  실제 키 표본: `BeforeAfter.tsx` · `TermMeans` · `clang_doc.machine.clang_doc.load_clang_doc`

## 무엇을 고칠지는 열려 있다 — 혼자 정하지 말 것

`CLAUDE.md` 의 "혼자 정하지 말 것" 과 `design-decision-discipline` 이 걸리는 자리다.
**세 갈래가 있고 셋 다 결정론이며 추가 LLM 비용이 없다.** 고르기 전에 사용자에게 표로 올린다.

| 갈래 | 무엇 | 장점 | 대가 |
|---|---|---|---|
| **A. 프롬프트에서 이름을 준다** | `survey_batch_prompt` 가 `depends_on` 을 코드지도 `name` 으로 풀어서 넘긴다 | 세션이 사람이 읽는 이름을 본다. 새 레코드가 깨끗해진다 | **이미 쌓인 898개 레코드의 C-id 는 그대로 남는다** — 별도 정리 필요 |
| **B. 조회할 때 푼다** | `dep_excerpt` 와 `check_terms` 가 C-id 를 코드지도로 한 번 풀고 나서 찾는다 | 옛 레코드까지 같이 살아난다 | 이름공간 둘을 영구히 떠안는다 |
| **C. `where` 로 잇는다** | 노드의 `file:line` 과 레코드의 `where` 를 맞춘다 | **세션이 키를 무엇으로 정하든 무관** — 가장 튼튼하다 | 줄이 밀리면 어긋난다(`xmldoc.py inject` 가 재계산하는 범위 밖) |

💭 **판단(신뢰도 🟡 70):** A + B 를 같이 하는 것이 맞아 보인다. A 로 새 레코드를 깨끗하게 만들고,
B 로 옛 레코드 898개를 구제한다. C 는 튼튼하지만 줄 드리프트라는 새 실패 축을 들인다.
**다만 이건 제안이지 결정이 아니다.**

## 경계 (Boundaries)

**소유 — 이 작업이 고쳐도 되는 것**

- `runner/run_mode1.py` 의 `survey_batch_prompt` · `dep_excerpt` (그리고 필요하면 그 둘의 시험)
- `machine/terms_db.py` 의 `check_terms` 언저리
- `runner/test_run_mode1.py` · `machine/test_terms_db.py` 에 시험 추가

**건드리지 않는 것**

- `machine/terms-reading.json` 을 **손으로 고치지 않는다.** 898개 레코드는 $50.73 짜리 산출물이다.
  정리가 필요하면 스크립트로 하고, 돌리기 전에 백업을 뜬다
- `out/codegraph-raw/**` — 재생성물이라 판 관리 밖이지만, 지금 것을 지우면 재조사 비용이 다시 든다
- `machine/normalize.py` 의 id 매김 규칙 — `C<숫자>` 를 FQN 으로 바꾸는 것은 **훨씬 큰 변경**이고
  골든 시험 전량에 걸린다. 이 작업의 범위가 아니다

**⚠ 지금 작업 트리에 커밋되지 않은 것이 있다** (2026-09-07 기준):

| 파일 | 무엇 | 누구 |
|---|---|---|
| `runner/run_mode1.py` | 주석의 `LLM Model` → `Model` 이름 바꾸기 27줄. **로직 변경 없음** | 사용자가 IDE 에서 작업 중 |
| `runner/wiki/prep.py` · `runner/wiki/build.py` · `runner/wiki/check.py` | `ModuleNotFoundError` 수정 · VitePress `ignoreDeadLinks` · `check` 종료 코드 뒤집힘 수정 | 2026-09-07 세션 |
| `runner/test_run_mode1.py` · `test/test_wiki.py` · `machine/test_survey_plan.py` | 회귀 시험 추가 · 층 분포 기대값 갱신 | 같음 |
| `machine/terms-reading.json` | 재조사 결과 813 → 898 레코드 (키 복원 적용본 — 짝 문서의 ④ 를 보라) | 같음 |
| `CLAUDE.md` · `runner/README.md` | 게이트 실측값 · 자동 생성 README 갱신 | 같음 |
| `docs/wiki/` (미추적) | Mode 1 이 만든 위키 산문 21장 | 같음 |

**⚠ `machine/xmldoc.py check` 는 지금 문제 94건이다** — 새 심볼 85개가 아직 마커를 못 받았다.
`emit` → `inject` 결정이 사용자에게 걸려 있다. 시작 전에 확인한다.

**`runner/run_mode1.py` 는 사용자가 열어 두고 있다.** 같은 파일을 고치므로 **시작 전에
`git status` 로 다시 확인하고, 충돌하면 사용자에게 묻는다.** `git add -A` 금지 — 경로를 좁혀 담는다.

## 가드레일 (프로젝트 규약 — Step 0 실측)

- **커밋하지 않는다.** 사용자가 요청할 때만 커밋한다. 형식은 `personal-commit-messages` 스킬 —
  소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음, 트레일러 없음
- **시험 먼저 쓴다**(TDD). 이 저장소는 그 규율로 돌아간다
- **코드 주석에는 현 상황만 적는다** — 날짜 · 측정 수치 · 확신도 표기 · 번복 기록을 코드에 남기지
  않는다. 그런 것은 이 문서와 `docs/` 의 몫이다. 형식·동작 사실은 남긴다
- **`# <include file="machine/comments.xml" …/>` 블록은 손대지 않는다** — `machine/xmldoc.py` 가
  주입한다. 함수를 새로 만들었으면 `terms-reading.json` 에 레코드를 쓰고
  `xmldoc.py emit` → `inject` 를 돌린다
- **약어와 압축 표현을 피한다.** 한국어 + 영문 기술용어 병기

## 검증 (Verify) — 게이트 일곱이 전부 초록이어야 한다

```bash
cd $REPO_ROOT
.venv/bin/python -m pytest -q                                   # 기대: 483 통과 · 20 건너뜀 이상
npm test                                                        # 기대: 8 통과
npm run typecheck                                               # 기대: 통과
npm run typecheck:py                                            # 기대: 0 errors
.venv/bin/python machine/xmldoc.py check                        # 기대: 문제 0건
.venv/bin/python tools/gen_readme.py --check machine runner viz tools   # 기대: 4개 일치
npm run doctor                                                  # 기대: 필수 전부 있다
```

**건너뜀 20개는 골든 저장소 환경변수(`$GRAPHICS_REPO`·`$CSHARP_REPO`·`$CPP_REPO`)가 없어서다.
실패가 아니다.**

### 이 작업 고유의 검증 — 위 재현 스크립트를 다시 돌린다

```
고치기 전: 배치 88 중 발췌가 빈 것: 88 · 조회 적중: 0 · 빗나감: 895
고친 뒤  : 빈 것이 크게 줄고, 적중이 0 이 아니어야 한다
```

**층0 배치는 의존이 없으므로 발췌가 비는 것이 정상이다.** "전부 0" 이 아니게 되는 것이 목표이지
"전부 채워짐" 이 목표가 아니다.

인용 검사 쪽:

```bash
.venv/bin/python machine/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading machine/terms-reading.json -o out/codegraph-raw
```

```
고치기 전: 용어 907개 / 실패 490 / 근거 없음 16   (2026-09-07 실측, 키 복원 이후 상태)
고친 뒤  : 실패에서 C<숫자> 꼴 375건이 사라져야 한다
```

⚠ **이 명령은 고치기 전에도 exit 1 이다.** 옛 백업 레코드로 돌려도 exit 1(실패 88)이었다 —
`terms` 의 exit 1 은 이 저장소의 기존 상태다. **"실패 0" 을 목표로 삼지 마라.** C-id 계열이
사라졌는지만 본다. 나머지(표준 라이브러리 이름 24건 등)는 다른 문제다.

## 보고 (Report)

끝나면 이 꼴로 보고한다:

- **상태** DONE / DONE_WITH_CONCERNS / BLOCKED
- **고른 갈래** A · B · C 중 무엇이며 왜 (사용자 승인을 받았는지 명시)
- **바뀐 파일** 경로 목록
- **검증 결과** 게이트 일곱의 실제 출력 + 위 두 재현 명령의 before/after 숫자
- **미룬 것** 손대지 않은 것과 이유
- **커밋 안 함** — 사용자 승인 전까지

## 변경 이력

- 2026-09-07 — 최초 작성. Mode 1 자기호스팅 실행($50.73 · 89배치) 중 발견하고 실측했다.
