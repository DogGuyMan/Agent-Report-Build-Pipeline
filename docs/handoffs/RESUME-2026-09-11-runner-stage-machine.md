# RESUME — 러너 단계 기계 리팩터링 (3단계 완료 · 후속은 xmldoc 재주입 · 위키 재굽기 · 결함 ③④)

> 작성 2026-09-11 · 2026-09-11 저녁 `main` 에 fast-forward 병합(`8d80494`, 브랜치 삭제) · 이후 작업은 `main` 에서 · 최신 커밋은 `git log -1`
> 저장소 `$REPO_ROOT` (= `report-builder`)
> **이 문서가 이 작업의 단일 진입점이다.** 앞선 `RESUME-2026-09-08-…` 은 이 문서가 대체한다.
> ⚠ **2026-09-13 갱신 — 아래 "바로 다음 할 일" 1번(xmldoc 재주입)은 무효다.** 주석 주입은 폐지됐다(`docs/decisions/0010`). 2번(위키 재굽기)부터 간다.
> 🔵 **2026-09-17 갱신 — 위키 재굽기(2번)에 착수해 `annotate-symbols` 층 0 까지 끝났고 노트북 수면으로 멈췄다. 그 뒤 사용자가 `out/` 을 통째로 지웠다 — 재개할 것이 없다. 다음은 처음부터다.** 실측과 교훈은 아래 "2026-09-17" 절. **`caffeinate -i` 를 앞에 붙여 돌린다.**

## TL;DR + 바로 다음 한 걸음

`runner/` 의 실행기 셋을 **공통 단계 기계**(`runner/pipeline.py`) 위로 올리는 3단계 작업이 **전부 끝났다.**
Mode 1 은 `runner/mode1/` 패키지(모듈 열둘)의 단계 12개 위에서 돌고, `run_mode1.py` 는 279줄의 `main` + 파사드다.
🔵 2026-09-11 저녁 실측: pytest **598 통과 · 실패 1(아래) · 19 건너뜀** · pyright **0** · `npm test` 8 · tsc · README · doctor 초록.

**바로 다음 할 일 — 셋, 순서대로.**
1. ~~**`xmldoc emit` → `inject` 를 한 번**~~ — **무효**(`docs/decisions/0010`, 2026-09-13). 2026-09-17 사용자가 근거를 다시 확인했다 — 고변동 저장소에서 읽을 곳이 둘 생기면 정합을 맞추려 들게 되므로 한 곳(Mode 1 산출물)만 둔다.
2. **위키 재굽기(Mode 1 자기 실행) — 2026-09-17 층 0 까지 갔다가 산출물을 지웠다. 처음부터 다시.** `test/test_wiki.py::test_check_는_통과를_통과로_보고한다` 가 빨갛다. `docs/wiki/runner-mode1-wiki.md:110` 이 `run_mode1.py:1114` 를 가리키는데 파일이 281줄이다. 위키는 스냅샷이라 손으로 안 고친다. **`--resume` 할 것이 없다 — 아래 절의 "다시 돌릴 때" 대로.**
3. **결함 ③④** — `HANDOFF-2026-09-07-warmup-increment-unreachable.md` 배너대로. 자리: `runner/mode1/survey.py` 의 `AnnotateSymbolsStage.harvest` · `merge_shards`, `machine/survey_plan.py` 의 배치 id. 그 뒤 D17 · `삭제됨` 삭제 · D15 둘째 걸음.

    계획서(에이전트용)  docs/superpowers/plans/2026-09-11-runner-mode1-v2.md       Task 2~13 전부 [x]. 매 Task 의 실측 메모가 그 자리에 있다
    앞선 판             docs/superpowers/plans/2026-09-11-runner-mode1.md          Task 1 만 유효
    스펙                docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md  "3단계 구현이 되돌려 적는 것" 절

**2026-09-11 오후 판정 — 자유 함수를 단계에 종속시킨다.** 한 단계만 쓰는 계산·프롬프트는 그 단계 클래스의
`@staticmethod`, 둘 이상이면 믹스인(`SnapshotScan` · `Measured`), 파일 꼴만 산출물 옆(`context.py` · `diff.py` · `resume.py`).
v2 계획서의 "규칙 R4" 와 "함수 → 소속 대조표". 착수 전 판정 셋은 기본값으로 갔다(믹스인 · `test_run_mode1.py:757` 한 줄 · D15 첫 걸음).

**이 세션의 사용자 규칙**: *"본체 `.py` 를 고치기 전에 diff 를 보이고 사용자가 직접 판단한다. 시험 파일은 예외."* — 새 세션은 유지할지 먼저 묻는다.

## 2026-09-17 — 위키 재굽기 착수 · 층 0 까지 (🔵 전부 이 세션 실측)

> ⚠ **결과는 남아 있지 않다.** 사용자가 2026-09-17 저녁 `out/`(`codegraph-raw/` 의 샤드 47개 · `batches.json` · `codegraph.json` · `changes.json` · `resume.json` 전부)을 **지웠다.** 복구하지 않는다.
> 남은 것은 셋 — 측정값 `evals/runs/2026-09-17-mode1-report-builder-warm-sonnet.json`(미추적), 층 0 을 합쳐 쓴 `machine/terms-reading.json` 1,087 레코드(미커밋 — 층 0 의 레코드만 새것이고 층 1~5 자리는 옛 조사 그대로라 **섞여 있다**), 그리고 이 절.
> `terms-reading.json` 을 어느 판으로 둘지는 사용자가 정한다 — `git checkout` 이면 896 레코드의 09-08 판(+18줄 삭제 미커밋)으로 돌아간다.


### 한 일

| 무엇 | 근거 |
|---|---|
| **결함 수정 `c7fe041`** — `out/codegraph-raw/` 가 없는 기계에서 `lang-decide` 가 `FileNotFoundError` 로 죽었다 | `Pipeline.run` 이 각 단계의 `writes` 폴더를 `perform` 직전에 만든다(`runner/pipeline.py`, 시험 `test_드라이버가_쓸_산출물의_폴더를_미리_만든다`). 러너 시험 290 통과 · pyright 0 |
| 앞 다섯 단계 완료 | `lang-hint` $0.15 · 나머지 결정론. 옛 지문이 없어 `detect-changes` 가 98파일 전부를 `재읽기` 로 냈다 — **사실상 전량** |
| 층 계획 | 심볼 **1,086** · 배치 **116**(층 0~5 = 49·32·20·10·3·2, 층 6 비노드 1) |
| `annotate-symbols` 층 0 | 배치 49 — 성공 46 · 실패 3(`L0-B38` · `L0-B46` · `L0-B47`). 층 0 합쳐 씀 → `machine/terms-reading.json` 896 → **1,087** 레코드(미커밋) |

### 성능 · 비용 (`evals/runs/2026-09-17-mode1-report-builder-warm-sonnet.json`)

| 항목 | 값 |
|---|---|
| 층 0 비용 | **$31.35** (sonnet-5, 동시 8) |
| 배치당 | 평균 **$0.65** · 80초 (최장 198초) · 턴 4~16 |
| 캐시 | 읽기 35.4M · 생성 5.1M 토큰 — 비용의 대부분이 캐시 읽기다 |
| 남은 것의 추정 | 배치 67 + 비노드 1 + 위키 장 쓰기 ≈ **$45~55 추가, 합계 $80 안팎**. 앞선 자기 조사 $50.73 과 같은 규모 |
| 벽시계 | 보고서의 "9분 19초" 는 **잠든 시간을 뺀 값**(`time.monotonic` 은 macOS 수면 중 멈춘다). 실제 18:46 → 20:44 |

**착수 전 추정($15~30)이 틀렸다.** 다음 추정은 이 배치 단가로 한다.

### 왜 멈췄나 — 노트북 수면

`pmset -g log`: `18:57:44 Entering Sleep state due to 'Clamshell Sleep'`. 20:44 에 깨어난 직후 Wi-Fi 가 오르기 전에
진행 중이던 세 세션이 같은 초에 죽었다 — transcript 의 마지막 항목이 셋 다 `API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)`.
러너 로그에는 "종료 코드 1 — success" 로만 남았다. `agent_verdict` 가 `subtype` 만 적고 `result` 본문을 버려서다.

### 다시 돌릴 때 — 처음부터, `--cold`, 빈 원본 (🔵 2026-09-18 판정)

```bash
rm machine/terms-reading.json          # git 에 09-08 판이 있다. 조사가 다시 쓴다
caffeinate -i .venv/bin/python runner/run_mode1.py . --cold --json evals/runs/$(date +%F)-mode1-report-builder-cold-sonnet.json
```

- **`--cold` 인 이유** — 옛 지문(`snapshot.json`)이 없어 증분이어도 98파일 전부 `재읽기` 다. 전량 그래프는 `detect-changes` 없이 같은 일을 하고 끝에 `snapshot-sources` 가 첫 지문을 찍는다 — 그 다음부터가 진짜 증분이다.
- **원본을 비우는 이유** — `verify-terms` 는 L1(파일 없음) · L2(줄 없음) 을 **실패**로 세고 exit 1 이라 단계가 멈춘다(`machine/terms_db.py` `check_terms` · `main`). 옛 카드 43장(`run_mode1.py:414~1075`, 파일은 281줄)이 L2 실패라 **$80 조사 뒤 위키 직전에 멈춘다.** 전부 다시 읽는 실행에 옛 카드를 깔 이유가 없다. 잃는 것은 `.tsx` · `.ts` 의 `file` 카드 12장뿐이고 비노드 층이 다시 낸다.
- 배치 116 전부 돈다. 합계 **$80 안팎 · 벽시계 30~40분**(동시 8). 층 0 단가 $0.65/배치가 기준.
- 재실행 전 고친 것 — `3d8b049`(같은 파일 키 개명 결함) · `88f988e`(프롬프트의 `file_cache put` 인자가 JSON 문자열이라 배치마다 traceback 1~2턴 — 파일 경로로).
- **덮개를 닫지 않는다.** `caffeinate -i` 는 유휴 수면만 막고 Clamshell Sleep 은 못 막는다 — 덮개를 닫으려면 `caffeinate -is` 와 외부 전원, 또는 닫지 않는다.
- 샤드는 층마다 `out/codegraph-raw/_shards/` 에 남고 `--resume` 이 그것을 건너뛴다(`runner/mode1/survey.py` `jobs`). **`out/` 을 지우면 이 재개 근거도 같이 사라진다** — 이번에 그랬다.

### 검사표 — 다음 실행 뒤

- [ ] `annotate-symbols` 층 1~6 성공 · `terms-reading.json` 레코드 수 · 실패 배치 0
- [ ] `snapshot-sources` 가 `out/codegraph-raw/snapshot.json` 을 처음 찍는다 — 다음 실행부터 진짜 증분
- [ ] `verify-terms` L1/L2/L3 · `outline-wiki` → `write-wiki` 가 `docs/wiki/*.md` 21쪽을 다시 쓴다
- [ ] `verify-wiki` 초록 → `pytest -q` 의 빨강 1 (`test_wiki.py`) 이 사라진다 → **게이트 여섯 전부 초록**
- [ ] 커밋 셋으로 나눈다 — `machine/terms-reading.json` · `docs/wiki/` · `evals/runs/*.json` + 이 문서. **`git add -A` 금지**
- [x] `machine/terms-reading.json` 의 섞인 판 — **지우고 빈 원본으로** (위 "다시 돌릴 때"). 2026-09-18 판정
- [ ] 루트 `CLAUDE.md` "게이트 여섯" 의 🔴 를 지우고 실측값으로
- [ ] `runner/mode1/prompt/*.md` 4개가 조사 도중(18:53~18:56) 생겼다 — **누가 썼는지 모른다.** 사용자가 판정. 이 세션은 담지 않았다

### 층 0 추적 — 배치 49개를 transcript 까지 대조한 것 (🔵 `~/.claude/projects/…/*.jsonl` 49개 + `evals/runs/2026-09-17-…json`)

| 단계 | 결과 | 시간 | 비용 | 낸 것 |
|---|---|---|---|---|
| `lang-hint` | OK | 25.7초 · 1턴 | $0.15 | 제안 python |
| `lang-decide` · `detect-changes` · `collect-graph` · `schedule-batches` | OK | 0.1 · 0.0 · 2.5 · 0.0초 | 0 | 98파일 전부 `재읽기` → 심볼 1,086 · 배치 116 |
| `annotate-symbols` 층 0 | 46/49 | 9분 19초(수면 제외) · 400턴 | $31.35 | 심볼 490 → `terms-reading.json` 896 → 1,087 |
| `snapshot-sources` 이후 여섯 | 안 돎 | — | — | — |

- **토큰 40.9M 중 캐시 읽기 35.4M(87%)** · 캐시 생성 5.1M · 출력 0.36M. 비용은 심볼 수가 아니라 **턴 수 × 문맥 크기**를 따른다 — 10심볼 B21 $0.39, 5심볼 B00 $0.66.
- **배치 크기 1~49 심볼**(목표 8). 패커가 한 파일을 쪼개지 않아 `test_run_mode1.py` 49개가 배치 하나(B38, 214초, 실패), `normalize.py` 27개(198초 $1.08), `test_mode1.py` 24개(176초 $1.08).
- 축별 — runner 291심볼/35배치 $14.72 · machine 154/27 $13.27 · viz 38/8 $2.89(실패 2) · tools 7/4 $0.46.
- 성공한 46개 전부 "레코드 N/N" 을 보고했고 confidence HIGH 428 · MEDIUM 4. 에이전트마다 Read 1~7 · Bash 1~7.
- **도구 오류 57건** — 대부분 `machine/file_cache.py put` 을 잘못 불러서(파일 경로 대신 JSON 을 인자로). B26 · B48 이 "부가 작업이라 무시" 라고 적었다. 배치당 1~2턴 낭비.

**합친 결과에서 드러난 것 셋 — 다음 실행 전에 볼 것.**

1. **키 꼴 결함 — 🔵 2026-09-18 원인 확정 · 고침 `3d8b049`.** 원인은 `collect-graph` 가 아니라 `runner/mode1/survey.py` `merge_shards` 의 충돌 판정이었다 — 원본(`baseline`)에 있는 키를 같은 파일에서 다시 읽으면 `got[key] != rec` 만 보고 "다른 파일과 겹침" 으로 판정해 `qualified()` 가 둘 다 `<stem>.<키>` 로 개명, 새 카드가 코드 지도가 모르는 자리로 이사했다. 고침은 조건 하나 — `file_of(got[key]) != file_of(rec)` 일 때만 충돌. 시험 둘 추가(같은 파일은 갈아 끼움 · 다른 파일은 여전히 개명), 층 0 실데이터 재연으로 이사 0 확인. 아래는 발견 당시 기록. 추가된 432 레코드 중 **241개의 키가 `<파일 stem>.<모듈 경로>.<이름>`** 꼴이다 — `normalize.machine.normalize.foo` · `build.runner.wiki.build.run` · `check.viz.check.LinkResult`. 옛 판의 바른 키 241개(`machine.normalize.foo`)가 지워지고 이것으로 갈렸다. 09-08 이후 생긴 파일(`runner/mode1/*` · `measure.py` · `pipeline.py`)은 바른 꼴이다. 프롬프트가 그 키를 그대로 줬으니 원인은 `collect-graph` 의 노드 id(`machine/pycalls.py` `stem_to_module` 근처 또는 `normalize.py:1005`) 쪽이다 — **원인 미확인**, `codegraph.json` 이 지워져 재확인하려면 `collect-graph` 를 다시 돌려야 한다(결정론, 2.5초).
2. **`runner/run_mode1.py` 의 옛 레코드 43개가 그대로 남았다.** 심볼이 코드에서 사라져 어느 배치에도 안 들어가 합치기가 못 지운다 — 결함 ④(`삭제됨` 삭제)가 그대로 살아 있다는 실측.
3. `.agents/skills/*/scripts/*.py` 6개가 조사 대상이다.

### 미루는 것 (기록만)

- `agent_verdict` 가 `returncode != 0` 일 때 `result` 앞 120자를 사유에 붙이면 ENOTFOUND 가 로그에 보인다.
- `machine/file_cache.py` 머리의 사용법 글(`<개요json>`)도 코드(넷째 인자 = 파일 경로)와 어긋난다. 프롬프트는 고쳤고(`88f988e`) 기계축 파일은 소유자 몫.
- 결함 ④(`삭제됨` 삭제)는 이번 실행에 필요 없다 — 빈 원본이라 고아 카드가 없다. 첫 **증분** 실행 전에 필요하다.
- 벽시계는 `time.time()` 로 따로 재야 수면을 포함한다. 측정의 뜻(잠든 시간을 넣을지)은 사용자가 정한다.

## 2026-09-13 — msgspec 도입 (계획 `docs/superpowers/plans/2026-09-13-runner-msgspec.md`, 커밋 `89d7709` · `bab8e6b` · `70e1e4a` + 문서)

`measure.py` 의 좁히기 도우미 `as_*` 다섯을 없애고 바깥 JSON 을 `TypedDict` + `msgspec` 으로 읽는다. **안 맞으면 예외**,
`Pipeline.run` 이 `FAIL` 로 바꾼다. `Artifact.check` → `schema`(꼴) + `check`(뜻). `pipeline.read_json` 삭제.
🔵 발견 둘 — (1) msgspec 0.21.1 은 한글 열쇠 `TypedDict` 를 모듈 경계 너머에서 못 맞춘다(`runner/CLAUDE.md` Gotcha).
(2) **기계축 선언이 실물과 어긋난다**: `codegraph.json` ↔ `survey_plan.CodeGraph`(`file` 에 `null`), `warmup.json` ↔
`warmup.Manifest`(`mtime` 없음). 러너는 느슨한 형으로만 본다 — 기계축 소유자가 볼 것.

## 지금 상태 — 다시 잰 것 (2026-09-11)

### 브랜치와 커밋

`main`(병합됨). 워킹 트리는 **깨끗하다** — 미추적 둘만 있다(사용자 것, 건드리지 않는다):
`docs/overturn/2026-07-05-번복기록-분석보고서.md` · `runner/runner_presudo.md`.

| 커밋 | 무엇 |
|---|---|
| `f30a6e7` | 단계·산출물 이름 12개 확정 (계획 · 요약 · 스펙) |
| `4110b21` | 전량 그래프에서 `warmup` 을 빼고 `warmup-save` 가 직접 훑는 것으로 확정 |
| `bb7be52` | 3단계 계획서의 사람용 요약 |
| `a66a107` | 3단계 실행 계획 |
| `5974a73` | 번복 기록 0004 · 재개 문서에 D14 재번복 반영 |
| `d6efbb1` | D14 를 `warmup-diff.json` 으로 재번복 · D17(claim 파일) 신설 |
| `196df24` … `62c88e4` | 2단계 — `pipeline.py` 신설, Mode 2 · 1.5 이주, 문서 |

### 게이트 (🔵 2026-09-11 저녁 실측 — 3단계 완료 시점)

| 게이트 | 지금 | 비고 |
|---|---|---|
| `pytest -q` | **598 통과 · 실패 1 · 19 건너뜀** | 실패 1 = `test_wiki.py::test_check_는_통과를_통과로_보고한다` — 위키 인용 표류(스냅샷). 위키 재굽기로 해소 |
| `npm run typecheck:py` | 0 errors | |
| `test/test_no_any.py` | 3 통과 · **19파일** 덮음 | `mode1/*` 12개 추가됨 |
| `gen_readme --check` | 4개 일치 | 생성기가 `mode1/` 을 훑는다 |
| `xmldoc check` | **레퍼런스 506 · 문제 339** — 알려진 빨강 | 1·2·3단계가 심볼을 옮겨 마커가 어긋났다. **한 번에** 재주입 |
| `npm test` · `typecheck` · `doctor` | 8 · 통과 · 필수 전부 있다 | |

## 단계 현황

| 단계 | 무엇 | 계획서 | 상태 |
|---|---|---|---|
| 1 | `measure.py` 추출 · 파사드 · import 부작용 제거 · `Any` 게이트 | `docs/superpowers/plans/2026-09-08-runner-common-axis.md` | ✅ |
| 2 | `pipeline.py` 신설 · Mode 2 · 1.5 이주 | `docs/superpowers/plans/2026-09-08-runner-pipeline.md` | ✅ |
| **3** | Mode 1 을 `mode1/` 패키지로 · 증분/전량 그래프 · `changes.json` · 재개 JSON · 이름 12개 | `docs/superpowers/plans/2026-09-11-runner-mode1-v2.md` | ✅ (`f88265a` … 마지막 커밋은 `git log`) |

## 2026-09-11 에 확정된 것 — 다시 논쟁하지 말 것

### ① 낱말 — "매니페스트" 는 옛 판의 지문이고 diff 가 아니다

| 파일 | 역할 |
|---|---|
| `snapshot.json` (← `warmup.json`) | **옛 판의 지문** — 지난 조사 때 파일마다 찍은 해시 둘(바이트 · 선언) |
| `changes.json` (새 파일) | 지문과 지금 소스를 **대조한 결과** — 유효 · 재읽기 · 위치만 · 삭제됨 + 파급 넓힌 `targets` |
| `codegraph.json` | 구조 지도. 바뀌었는지는 모른다 |

사용자가 인용한 우화("조수의 메모는 사라지고 지시서만 남았다")는 인계 문서 결함 ②를 다른 말로 쓴 것이다.
조수(`warmup.status()`)는 **이미 기계**다. 고칠 것은 메모가 파일이 아니었다는 것 하나.

### ② 전량 그래프에는 `detect-changes` 가 없다 (B안 · 요약 §4-①)

대조할 옛 지문이 없는데 대조 단계를 돌리지 않는다. 끝의 `snapshot-sources` 가 **직접 훑어** 지문을 찍는다.
스펙 D13 그림이 그대로 맞다. 두 안 모두 `collect-graph` 에 `--force` 가 필요했다(앞선 계획에서 빠졌던 것).
graphify 의 매니페스트 운용(늘 갱신되는 색인)이 참고가 됐다. **A안(전량에도 warmup)은 물렸다** — 번복 기록 0004 의 모양.

### ③ D14 ×2 — `detect-changes` 가 `changes.json` 을 쓰고 `annotate-symbols` 가 지시서와 양방향 대조

09-08 "계획에 싣기" → 09-10 "경고만"(소유 경계) → **09-11 "diff 를 러너 소유 파일로"**. 셋째 안이 앞의 두
제약(파일에 남긴다 / `machine/` 안 건드린다)을 둘 다 만족한다. 대조는 **양방향** — 넓으면 $50 사고, 좁으면 레코드 누락.
`삭제됨` 은 diff 에 싣기만 하고, 지우는 것은 결함 ④ 와 같은 자리에서.

### ④ D17 — 실행 둘이 겹칠 때 claim 파일. push 그대로. **결함 ③ 뒤**

한 실행 안에서는 `survey_plan.pack` 이 파일을 겹치지 않게 나눠 충돌이 없다. 메모리 락은 자식 프로세스·별개
실행 경계를 못 넘는다. 배치 id 가 위치 기반이라 지금 넣으면 남의 배치를 막는다.

### ⑤ 단계·산출물 이름 12개 (사용자가 하나씩 골랐다)

    증분:  lang-hint ▶ lang-decide ▶ detect-changes ▶ collect-graph ▶ schedule-batches ▶ annotate-symbols
           ▶ snapshot-sources ▶ verify-terms ▶ outline-wiki ▶ write-wiki ▶ publish-wiki ▶ verify-wiki
    전량:  같되 detect-changes 없음 (11개)

| 옛 → 새 | 파일 |
|---|---|
| `lang-select` → `lang-hint` + `lang-decide` | `lang-select.json` |
| `warmup` → `detect-changes` | `changes.json` |
| `prep` → `collect-graph` | `codegraph.json` |
| `survey-plan` → `schedule-batches` | `batches.json` (← `survey-plan.json`) |
| `survey` → `annotate-symbols` | `terms-reading.json` |
| `warmup-save` → `snapshot-sources` | `snapshot.json` (← `warmup.json`, **읽기만 이주**) |
| `terms` → `verify-terms` | `terms-db.json` |
| `wiki-catalogue` → `outline-wiki` | `outline.json` (← `wiki-plan.json`) |
| `wiki-pages` → `write-wiki` | `docs/wiki/*.md` |
| `build` → `publish-wiki` · `check` → `verify-wiki` | — |

옛 이름은 `ALIASES` 로 `--only` 에서만 산다. `machine/warmup.py` 의 `DEFAULT_CACHE` 는 손대지 않는다.
**스펙의 결정 본문은 옛 이름 그대로다** — 번복 이력이 그 이름으로 적혀 있어서. 스펙 머리의 "이름 확정" 절이 대응표다.

### ⑥ D4 표현 — `lang-hint` 실패는 `SKIP → 다음`

`FAIL → lang-decide` 간선이 아니다. 같은 효과이고 관문 아닌 단계의 실패를 "실패"라 부르지 않는다.

### 앞선 재개 문서에서 그대로 유효한 것

D0·D1·D2·D5·D6·D7·D8·D9·D10·D11·D12·D13·D15·D16 은 `RESUME-2026-09-08` 의 "확정된 결정" 절 그대로다.
`pipeline.py` 의 공개 API 와 Mode 2 이주 본보기도 그 문서에 있다 — **3단계 코드는 그것을 그대로 따른다.**

## 3단계에서 판정이 남았던 것 — 전부 기본값으로 갔다

| 어디 | 무엇 | 결과 |
|---|---|---|
| 요약 §4-② | D15 두 걸음 | 첫 걸음만(`prep.py --diff/--force` · `needs_collect`). 둘째 걸음은 후속 |
| Task 4 끝 | `collect-graph` 를 `collect` + `facts` 로 쪼갤지 | 안 쪼갬. 판정 요청만 남긴다 |
| v2 ① | 둘이 쓰는 훑기 — 믹스인 vs 복제 | 믹스인 `SnapshotScan` |
| v2 ② | `test_run_mode1.py:757` `wiki-plan.json` → `outline.json` | 바꿈 |

## 병렬 작업 충돌 매트릭스

| 파일·자리 | 누가 | 이 작업 |
|---|---|---|
| `runner/**` (`mode1/` 신설 포함) | **이 작업** | 소유 |
| `runner/wiki/prep.py` | 이 작업 — **한 파일만** (`--diff` · `--force`) | D15 로 열린 경계 |
| `machine/**` · `viz/**` | 다른 작업 | 읽기만. `DEFAULT_CACHE` 도 안 건드린다 |
| `machine/comments.xml` · `# <include …/>` | xmldoc 재주입 작업 | **지금이 그때다** — 후속 1 |
| `docs/overturn/2026-07-05-…` · `runner/runner_presudo.md` | 사용자 (미추적) | 담지 마라 |
| 결함 ③④ (`merge_shards` · 배치 id) | `HANDOFF-2026-09-07-warmup-increment-unreachable.md` | **착수 가능.** 자리는 `runner/mode1/survey.py` |

## 가드레일 · 규약

- 지금은 `main` 이다(2026-09-11 병합). 새 갈래를 열지 말지는 사용자가 정한다.
- **커밋은 Task 마다.** `[tag] : subject` 소문자 한 줄 한국어, 빈 줄, `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. **`git add -A` 금지** — 경로를 좁힌다.
- **TDD.** 시험 먼저, 실패 확인, 구현, 통과. 계획서가 시험 코드를 전부 담고 있다.
- **`Any` 금지.** `object` + 좁히기(`measure.as_map` 등). `test/test_no_any.py` 가 게이트.
- **`# <include …/>` 블록** — 새로 심지 않는다. 정의를 옮기면 위 세 줄 블록을 함께 지운다. `xmldoc check` 가 느는 것은 정상.
- **코드 주석에는 현 상황만.** 날짜 · 수치 · 확신도 · 설계 철학 금지.
- **`runner/test_run_mode1.py`(이제 759줄)** — 파사드 재수출로 통과한다. 없앤 이름의 시험 17개를 지웠고(v2 Task 12 목록) `:757` 의 파일 이름 한 줄을 바꿨다.
- **실제 `annotate-symbols` 를 돌려 검증하지 마라.** 세션당 약 $0.5. `--dry-run` 과 순수 함수 시험까지만.
- **파이썬 편집 전 확인** — 위 TL;DR 의 세션 규칙. 새 세션은 유지 여부를 먼저 묻는다.

## 포인터

| 문서 | 무엇 |
|---|---|
| `docs/superpowers/plans/2026-09-11-runner-mode1-v2.md` | **3단계 계획 개정판 (에이전트용).** Task 2~13 전부 [x] · 실측 메모 |
| `docs/superpowers/plans/2026-09-11-runner-mode1.md` | 앞선 판. Task 1 만 유효 |
| `docs/superpowers/plans/2026-09-11-runner-mode1-요약.md` | 사람용 요약. 판정은 여기서 |
| `docs/superpowers/specs/2026-09-08-runner-stage-machine-design.md` | 스펙. 결정 18건. 머리에 "이름 확정" 절 |
| `docs/superpowers/specs/runner-stage-machine/out/report.html` | Mode 2 보고서 (재생성 가능) |
| `docs/handoffs/RESUME-2026-09-08-runner-stage-machine.md` | 앞선 재개 문서. `pipeline.py` API · Mode 2 본보기 · 1·2단계 상세는 여기 |
| `docs/handoffs/HANDOFF-2026-09-07-warmup-increment-unreachable.md` | 결함 ③④. 🔴 리팩터링 후속 |
| `docs/overturn/README.md` | 번복 기록 4건 · 검사표 5항목. **남의 안을 물리치기 전에 읽는다** |
| `docs/decisions/0007-xmldoc-include-deprecated.md` | xmldoc 폐지 예정. 재주입 때 `emit_xml()` 속성 함께 |

## 변경 이력

- 2026-09-18 — 키 이사 결함의 원인을 `merge_shards` 로 확정하고 고침(`3d8b049`). 프롬프트의 `file_cache put` 인자 고침(`88f988e`). 재실행 판정: `--cold` + 빈 원본 — `verify-terms` 가 옛 카드 43장의 L2 실패로 멈추기 때문.
- 2026-09-17 — 위키 재굽기 착수. `c7fe041` 폴더 보장 수정. 층 0 실측($31.35 · 배치당 $0.65) · 수면 중단 원인 · 검사표. 저녁에 사용자가 `out/` 을 지워 재개 불가 — 처음부터 다시 도는 명령으로 바꿈.
- 2026-09-11 저녁 — 3단계 완료. TL;DR 을 후속 셋으로. 스펙에 "3단계 구현이 되돌려 적는 것" 절.
- 2026-09-11 — 최초 작성. `RESUME-2026-09-08` 을 대체. 3단계 계획서 확정, 미결 셋 판정(B안 · D15 두 걸음은 미확인 · prep 쪼개기는 Task 4 뒤), 이름 12개 확정, 번복 기록 0004, 세션 규칙(파이썬 편집 전 확인) 기록.
