# Mode 1 에이전트 칸을 Bottom-Up 층 병렬로 — 실행 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mode 1 파이프라인의 LLM 칸 하나(`agent`)를 **의존 위상 층 오름차순 · 층 안 병렬**로 도는 하네스로 갈라, 시험과 dry-run 까지 통과시킨다.

**이 계획은 파이프라인을 실제로 돌리지 않는다.** `ARCHITECTURE.md:155-166` 의 `agent` 벽시계 26분 53.1초를 줄였는지 확인하는 A/B 실측은 **계획 밖의 후속 작업**이다(맨 아래 절). 계획 단계에서 27분·$15 짜리 실행을 돌리는 것은 계획이 하는 일이 아니다.

**Architecture:** 다섯 단계 `prep → agent → terms → build → check` 를 여섯 단계 `prep → survey → terms → wiki → build → check` 로 가른다. `survey` 와 `wiki` 는 둘 다 LLM 칸이고, 각각 **층 오름차순으로 여러 번** `claude -p` 를 부른다. 층 안에서는 `ThreadPoolExecutor` 로 최대 8개를 동시에 띄우고, 층 사이는 순차다. 층을 계산하는 것은 새 결정론 스크립트 `codegraph/survey_plan.py` 이고, 층 경계에서 같은 파일을 다시 통독하지 않도록 `codegraph/file_cache.py` 가 디스크 캐시를 놓는다. 배치 세션은 자기 샤드에만 쓰고, 키 충돌 해소와 병합은 전역을 보는 오케스트레이터(파이썬)만 한다.

**Tech Stack:** Python 3 (`.venv/bin/python`) · `networkx`(이미 있다) · 표준 라이브러리 `concurrent.futures` · `pytest`. **새 파이썬 의존성 0개.** Node 쪽은 건드리지 않는다.

---

## 🔴🔴 서브에이전트 모델 — **Claude Sonnet 5** 🔴🔴

> # 배치·페이지 세션이 쓰는 모델은 `claude-sonnet-5` 다.
>
> **정확한 모델 ID 문자열은 `claude-sonnet-5` 하나뿐이다.** 날짜 꼬리표를 붙이지 않는다
> (`claude-sonnet-5-20260101` 같은 것은 없다). 별명 `sonnet` 도 CLI 가 받지만,
> **계획과 코드에는 정확한 ID 를 적는다** — 별명은 최신판을 따라 움직여 측정이 흔들린다.
>
> **적용 대상 — 오케스트레이터가 `claude -p` 로 띄우는 세션 전부:**
> - `survey` 의 배치 세션 (`survey_batch_prompt`)
> - `survey` 의 비노드 층 세션 (`nonnode_prompt`)
> - `wiki` 의 목차 세션 (`wiki_catalogue_prompt`)
> - `wiki` 의 장 세션 (`wiki_page_prompt`)
>
> **코드에 박히는 자리 — `run_mode1.py` 의 `main()` 인자 기본값 한 곳뿐이다:**
> ```python
> ap.add_argument("--model", default="claude-sonnet-5",
>                 help="배치·장 세션이 쓸 모형 (기본: claude-sonnet-5). "
>                      "별명이 아니라 정확한 ID 를 적는다 — 별명은 최신판을 따라 움직여 측정이 흔들린다")
> ```
> 예전 기본값은 `opus` 였다. **이 한 줄이 바뀌는 것을 잊지 마라.**

**⚠ 이것이 A/B 대조를 오염시킨다 — 반드시 알고 있어야 한다.**

🔵 기준선(26분 53.1초 · $15.4991)은 **opus 한 세션**으로 잰 값이다. 새 구조는
**sonnet-5 여러 세션**이다. 즉 한 번에 **변수 둘**(모형 · 세션 위상)이 바뀐다.
그래서 "층 병렬 덕분에 빨라졌다" 고 말할 수 없다 — 모형이 싸고 빨라서일 수도 있다.

귀속(attribution)이 필요하면 측정을 **셋** 해야 한다:

| 조건 | 모형 | 위상 | 무엇을 알려주나 |
|---|---|---|---|
| 기준선 (있음) | opus | 한 세션 | 출발점 |
| 새 하네스 | `claude-sonnet-5` | 층 병렬 | **done 조건이 보는 값** |
| (선택) 대조군 | `claude-sonnet-5` | 한 세션 — 이 구조에서는 못 만든다 | 모형 몫과 위상 몫의 분리 |

세 번째는 옛 다섯 단계 코드가 필요하므로 `git worktree add /tmp/rb-old 9223143` 로 떼어 돌린다.
**하지 않아도 done 조건은 닫힌다**(K8 은 벽시계만 본다). 다만 "무엇 덕분인가" 를 물으면
답할 수 없다는 것을 보고에 적는다.

---

## ⚠ warmup 배선 위에 합친다 — 단계는 **여덟**이다 (2026-08-30 사용자 확정)

**이 계획을 쓰는 동안 다른 세션이 `2026-08-30-warmup-mode1-wiring.md` 를 작업 트리에 구현했다.**
사용자가 **그 작업의 완료를 보장**했고 **`warmup.py` 를 고쳐도 좋다**고 했다. 그러므로
되돌리지 않고 **그 위에 합친다.**

| | 다섯 단계(옛) | 일곱 단계(warmup 배선, 지금 트리) | **여덟 단계(이 계획의 결과)** |
|---|---|---|---|
| 흐름 | `prep agent terms build check` | `prep warmup agent warmup-save terms build check` | `prep warmup survey warmup-save terms wiki build check` |
| LLM 칸 | `agent` 1개 | `agent` 1개 | **`survey` · `wiki` 2개, 각각 층별 여러 세션** |
| pytest | 201 통과 · 19 건너뜀 | **235 통과 · 19 건너뜀** ← **이 계획의 기준선** | 235 + 더한 만큼 |

### `warmup-save` 는 왜 `survey` 바로 뒤인가 — `wiki` 뒤가 아니다

warmup 배선의 급소는 **"판정은 앞, 확정은 뒤"** 다. 에이전트가 실패했는데 매니페스트를
"유효" 로 갱신하면 다음 실행이 읽지 않은 파일을 읽은 것으로 친다.

그 관문이 감싸야 하는 것은 **레코드를 만드는 단계**다. `survey` 가 레코드를 만들고
`wiki` 는 산문을 쓴다. 그래서 `warmup < survey < warmup-save` 다.

💭 `wiki` 뒤에 두면 **산문이 실패했을 때 다음 실행이 전량을 다시 조사하게 된다** —
레코드는 멀쩡한데 27분을 다시 쓰는 비용 회귀다. 그래서 `wiki` 앞에 둔다.
`terms` 는 그대로 `survey` 와 `wiki` 사이에 남는다(산문이 검사 통과한 재료를 보게 하려는 것).

### 🔴 이 합치기가 만드는 조용한 버그 하나 — 반드시 고친다

`save_warmup` (`run_mode1.py:557`)이 이렇게 판정한다:

```python
    실패한_에이전트 = [r for r in rows if r["stage"] == "agent" and not r.get("ok")]
```

**이 계획은 행 라벨을 `survey/L0-B00` 꼴로 바꾼다.** 그러면 이 비교가 **영원히 거짓**이 되어
**survey 가 실패해도 매니페스트가 갱신된다** — warmup 배선이 막으려던 바로 그 사고가 되살아난다.
Task 8 에서 `r["stage"].split("/")[0] == "survey"` 로 고치고, 그것을 단언하는 시험을 더한다.

### warmup 과 층 계획은 서로 맞물린다 — 공짜로 얻는 것

`run_warmup` 이 내는 `targets`(= `blast_radius(재읽기 ∪ 위치만)`)가
`survey_plan.plan(cg, target, only_files=targets)` 의 `only_files` 로 그대로 들어간다.
이 계획이 처음부터 증분용으로 설계해 둔 자리다(`test_증분은_층_번호를_보존한다`).
층 번호는 **전체 그래프 기준으로 매긴 뒤** 거르므로 사라진 의존 대상 때문에 층이 잘못 내려가지 않는다.

`warmup_section(targets, total, repo)` 도 죽지 않는다 — **배치 프롬프트 머리에 붙인다.**
증분 조사임을 배치 세션이 알아야 하기 때문이다(`codebase-terms-survey` SKILL.md:82 —
*"증분 재조사에서는 기존 레코드의 `means` `does` 를 바꾸지 않는다 — Mode 1.5 정답지로 이미 쓰였다"*).

---

## 착수 전에 읽을 것 — 왜 이 모양인가

### 🔵 기준선 (2026-08-30 실측, `evals/runs/2026-08-30-mode1-qtvisionedit-cold-opus.json`)

| 단계 | 벽시계 | 합계 토큰 | 비용 | 턴 |
|---|---:|---:|---:|---:|
| `prep` | 1.3초 | 0 | $0 | 0 |
| **`agent`** | **26분 53.1초** | **17,925,770** | **$15.4991** | **84** |
| `terms` | 0.1초 | 0 | $0 | 0 |
| `build` | 13.6초 | 0 | $0 | 0 |
| `check` | 0.2초 | 0 | $0 | 0 |
| 합계 | 27분 08.1초 | 17,925,770 | $15.4991 | 84 |

캐시읽기가 전체 토큰의 97.3% 였다. 대상은 `$QT_REPO`(QtVisionEdit, C++ 77파일)이며 실제 경로는 `evals/runs/*.json` 의 `repo` 칸에 있다.

### 사용자가 확정한 결정 — 다시 논쟁하지 않는다

| # | 결정 |
|---|---|
| K1 | 정렬 축은 **위상 깊이**. 남에게 의존하지 않는 것(out_deg 0)이 층0, 거기서 한 겹씩 벗긴다 |
| K2 | 층 안은 **병렬**, 층 사이는 **순차**. 층 k 는 층 <k 가 전부 끝나고 병합된 뒤 시작 |
| K3 | 배치는 고정 크기 **N = 8 심볼** |
| K4 | 한 층에서 **동시에 8배치**까지 |
| K5 | 그래프 노드가 아닌 용어(`file` `module` `artifact` `key` `concept`)는 **맨 마지막 별도 층** |
| K6 | 위키 산문도 같은 층 순서. **페이지의 층 = 그 페이지가 인용하는 심볼의 최대 층** |
| K7 | 고립 노드(간선 0개)는 의존 대상이 없으므로 **층0 에 함께 둔다** |
| K8 | 성공 판정은 **벽시계만.** 토큰·비용 증가는 허용하되 반드시 기록한다 (2026-08-30 사용자 확정) |

### ⚠ 이 계획은 잠긴 결정 하나를 뒤집는다

`codegraph/run_mode1.py:26-28` 과 `codegraph/CLAUDE.md` 는 **"에이전트를 하나로 묶은 것이 이 설계의 급소"** 라고 못 박고 있다. 이유는 캐시였다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어 토큰이 부풀고, 측정값이 파이프라인 비용이 아니라 세션 수의 함수가 된다.

**사용자가 2026-08-30 에 이 결정을 뒤집었다.** 층 병렬은 세션 분리가 전제다. 뒤집은 사실을 **코드·테스트·문서 세 곳에 모두** 적는다(Task 3 · Task 9). 조용히 지우지 않는다.

### 🔵 위험 — 병렬 이득이 층0 에만 있다 (이번 세션 실측, 2026-08-30)

대상 저장소의 `out/codegraph-raw/codegraph.json`(1차 노드 86 · 간선 53)을 K1~K4 규칙으로 직접 갈라 본 결과:

| 층 | 심볼 | 파일 | 배치(N=8) | 동시 8이면 물결 |
|---|---:|---:|---:|---:|
| 0 | 72 | 31 | 11 | **2** |
| 1 | 5 | 5 | 1 | 1 |
| 2 | 4 | 4 | 1 | 1 |
| 3 | 4 | 4 | 1 | 1 |
| 4 | 1 | 1 | 1 | 1 |
| 계 | 86 | 39(유일) | 15 | **6** |

**심볼의 84%가 층0 에 몰려 있고 층1~4 는 배치가 1개씩이라 병렬 이득이 없다.** 임계 경로는 층 물결 6개에 비노드 층 1개를 더해 **최소 7 세션 깊이**다. 여기에 `wiki` 의 카탈로그 1 + 페이지 층들이 더 붙는다.

💭 그러므로 **"층 병렬이면 당연히 빨라진다" 는 성립하지 않는다.** 한 세션 84턴이 26분 53초였으니 턴당 약 19초다. 7~11 물결이 각각 몇 분이 걸리는지는 **모른다.** 그래서 이 계획은 하네스를 세우되 **빨라졌다고 주장하지 않는다** — 그 판정은 후속 A/B 실측의 몫이다. "더 싸졌다" "더 빨라졌다" 를 재기 전에 쓰지 않는다.

⚠ 위 층 분포는 **투영된**(terms_db 가 덮어쓴) 코드 지도에서 잰 값이다. 후속 A/B 는 백지에서 `prep` 을 다시 돌리므로 정적 수집기가 낸 코드 지도의 층 분포는 다를 수 있다. **그때 다시 재고, 위 표를 기대값으로 쓰지 않는다.**

### 🔵 층 경계 중복 통독은 실재한다 (이 저장소 실측)

이 저장소 자신의 코드 지도(1차 노드 167)에서 유일 파일은 41개인데 층별 파일 수를 합치면 84개다 — **중복 43회.** `codegraph/normalize.py` 는 심볼 21개가 층 0·1·2·3 에 흩어져 있다. 배치 세션은 컨텍스트가 분리돼 있어 lock 으로는 못 막는다(lock 은 동시 쓰기를 막을 뿐 이미 읽은 내용을 남에게 넘기지 못한다). 그래서 **디스크에 남는 통독 캐시**가 답이다 — `codegraph/file_cache.py`.

### 이 계획이 건드리지 않는 것

- **prep 계층** — `scripts/wiki/{prep,paths,compdb,clang-doc}.mjs` · `codegraph/{normalize,facts,render_modules,clang_doc}.py`
- **`codegraph/terms_db.py`** — 오케스트레이터가 참조만 한다. 출력을 읽기만 한다
- **뒤쪽 기계 단계** — `scripts/wiki/{build,check}.mjs` · `codegraph/{demermaid,verify_citations}.py`
- **Mode 2 소유** — `src/*` · `scripts/build.mjs` · `scripts/check.mjs`
- **전수조사 실행 자체** — 이 계획은 하네스만 만든다. `claude -p` 를 실제로 부르는 일은 없다
- **`~/.claude/plugins/cache/skills/deep-wiki/**`** — 플러그인 캐시라 업데이트에 덮인다. deep-wiki 의 산문 규정을 바꾸려면 그 파일이 아니라 **우리 프롬프트가 감싸서** 지시한다

## 파일 lock 검토 — 결론: **lock 을 걸지 않는다. 필요가 없기 때문이다** (2026-08-30 실측)

사용자 질의 — *"한 Agent 가 8개 파일을 분석할 때 다른 Agent 가 접근 못 하도록 파일 lock 이 보장되어 있나?"*

**답: lock 은 없다. 그리고 이 설계에서는 두 세션이 같은 파일을 동시에 여는 일 자체가 일어나지 않는다.**
배타성이 lock 이 아니라 **배치를 나누는 규칙**에서 나온다.

### 왜 동시 접근이 없는가 — 두 겹

1. **층 안** — `survey_plan.pack()` 이 같은 파일의 심볼을 **한 배치에 몰아넣는다**.
   그래서 한 층 안에서 두 배치가 같은 파일을 가리키는 일이 없다. 이게 병렬 단위의 배타성이다.
2. **층 사이** — 층 k 는 층 <k 가 **전부 끝나고 병합된 뒤** 시작한다(K2). 같은 파일이 여러 층에
   걸치는 것은 실재하지만(🔵 이 저장소 41파일 중 25개), 그 둘은 **시간상 겹치지 않는다.**

🔵 **이번 세션에 두 저장소에서 실제로 확인했다:**

| 저장소 | 층별 배치 수 | 층 안 파일 중복 | 층을 가로지르며 다시 열리는 파일 |
|---|---|---|---|
| report-builder | 16 · 4 · 2 · 1 · 1 | **모든 층 0건** | 25개 (순차라 동시 아님) |
| QtVisionEdit | 11 · 1 · 1 · 1 · 1 | **모든 층 0건** | 6개 (순차라 동시 아님) |

### 쓰기 충돌은 어떤가 — 넷 다 구조로 막힌다

| 무엇을 쓰나 | 누가 | 동시에 겹치나 |
|---|---|---|
| `_shards/<배치id>.json` | 배치 세션 | **아니다.** 배치 id 가 유일하다 |
| `_filecache/<파일해시>.json` | 배치 세션 | **아니다.** 층 안 파일이 배타적이다. 게다가 `os.replace` 라 원자적이다 |
| `docs/codegraph/terms-reading.json` | **오케스트레이터만** | **아니다.** 층 사이에서 단일 스레드로 쓴다 |
| `docs/wiki/<장>.md` | 장 세션 | **아니다.** 장마다 파일이 다르다 |

### 💭 그래도 남는 구멍 둘 — 정직하게 적는다

1. **강제(enforcement)가 아니라 규약(convention)이다.** `claude_argv` 가 `--permission-mode
   bypassPermissions` 를 준다(`run_mode1.py:175`). 세션이 마음먹으면 어떤 파일이든 열고 쓸 수 있다.
   "자기 샤드에만 써라" 는 **프롬프트의 문장일 뿐** 커널이 막는 것이 아니다.
   - 💭 그래도 lock 을 넣지 않는 이유 — 파일 lock 은 **협조적(advisory)** 이라 규약을 어기기로 한
     쪽을 어차피 못 막는다. 규약을 지키는 쪽에게는 이미 배타성이 있으므로 아무것도 더 사지 못한다.
     이걸 넣는 것은 거울 함정이다.
   - 대신 **검출**을 넣는다 — 층이 끝날 때 `merge_shards` 가 배치가 쓰지 않아야 할 키를 냈는지
     세지는 않지만, `git status` 로 예상 밖 파일이 바뀌었는지는 사람이 본다(Task 11 Step 6).
2. **배타성이 `pack()` 하나에 걸려 있는데 시험이 합성 자료뿐이었다.** `test_같은_파일은_한_배치에`
   는 손으로 만든 5심볼짜리다. **실제 지도에서 그 성질이 성립하는지 단언하는 시험을 더한다**
   (Task 1 Step 1 에 추가). 이 성질이 깨지면 lock 없는 설계의 전제가 무너지므로 게이트여야 한다.

### 🔵 발견한 작은 결함 하나 — 빈 파일 이름

사양의 `pack()` 은 `file` 이 없는 노드를 `byfile[""]` 로 묶는다. 그러면 배치의 `files` 목록에
빈 문자열이 섞이고, 프롬프트가 `file_cache.py get <repo> ` 를 빈 인자로 부르라고 시킨다.
🔵 이번 세션 실측 — 두 저장소 모두 `file` 없는 1차 노드가 **0개**라 지금은 안 터진다.
그래도 C# 쪽에서 나올 수 있으니 **`files` 를 낼 때 빈 이름을 거른다**(Task 1 Step 3 에 반영).

---

### 계획서를 쓰면서 내린 판단 — 사용자가 뒤집을 수 있다

| # | 판단 | 왜 |
|---|---|---|
| J1 | 샤드는 `docs/codegraph/_shards/` 가 아니라 **`out/codegraph-raw/_shards/`** 에 둔다 | `out/` 은 `.gitignore:8` 이라 재생성 파생물이 사는 곳이다. `docs/` 는 git 추적이라 중간 산물이 커밋에 섞인다. 통독 캐시(`_filecache/`)와 같은 자리에 두어 규칙이 하나가 된다 |
| J2 | `agent_prompt()` 와 `run_agent()` 를 **지운다**(껍질로 남기지 않는다) | `git grep` 확인 — `run_mode2.py` 와 `run_mode1_5.py` 는 `M.normalize_usage` `M._hms` `M._Heartbeat` `M.sum_usage` `M.format_report` `M.claude_argv` `M.agent_verdict` 만 쓴다. 둘 다 자기 `agent_prompt`/`run_agent` 를 따로 갖는다. 남기면 아무도 안 부르는 죽은 코드다 |
| J3 | `wiki` 단계는 **카탈로그 세션 1개**를 먼저 돌린다 | K6 의 "페이지가 인용하는 심볼" 을 알려면 페이지 목록과 그 인용 대상이 먼저 있어야 한다. deep-wiki 의 페이지는 심볼도 모듈도 아닌 **주제** 단위라 기계가 결정론으로 못 만든다 |
| J4 | 배치는 **샤드가 이미 있으면 건너뛴다** | 재시도 구조를 만들지 않고도 재개가 된다. `--only survey` 로 다시 돌리면 실패한 배치만 다시 돈다. 코드 두 줄이고 추상화가 아니다 |
| J5 | Task 마다 커밋한다 (`personal-commit-messages` — 소문자 `[tag] : 제목` 한 줄, 한국어, 본문 없음) | 🔵 이번 세션 확인 — `git status --porcelain` 이 1줄(이 계획서의 원본 PROMPT 문서)뿐이라 트리가 깨끗하다. 입력 PROMPT 의 "커밋 금지" 는 트리가 39개 파일 더러웠을 때 쓴 것이고 그 전제가 사라졌다 |

---

## File Structure

| 파일 | 책임 | 신규/개조 |
|---|---|---|
| `codegraph/survey_plan.py` | 코드 지도 → 층·배치 계획. **판정하지 않는다.** 순서를 계산하고 나눌 뿐 | 신규 |
| `codegraph/test_survey_plan.py` | 위의 시험. 합성 그래프로 규칙을, 실제 지도로 규모를 | 신규 |
| `codegraph/file_cache.py` | 파일 통독 개요를 내용 해시 키로 디스크에 남긴다. lock 없음 | 신규 |
| `codegraph/test_file_cache.py` | 위의 시험 | 신규 |
| `codegraph/run_mode1.py` | **본체.** 단계 여섯 · 프롬프트 네 종 · 층 실행기 · 샤드 병합 · 보고 | 개조 |
| `codegraph/test_run_mode1.py` | 잠긴 결정이 바뀐 것을 테스트로 드러낸다 | 개조 |
| `.agents/skills/codebase-terms-survey/SKILL.md` | 절차의 정본. `.claude/skills/` 는 여기로 가는 심볼릭 링크다 | 개조 |
| `codegraph/CLAUDE.md` · `ARCHITECTURE.md` · `docs/codegraph/terms-reading.json` | 코드와 어긋나지 않게 | 개조 |

**여섯 파일 규칙의 예외 2건** — 입력 PROMPT 는 작업 파일을 6개로 못 박았으나, `test_file_cache.py`(테스트 없는 새 모듈을 만들지 않는다) 와 `ARCHITECTURE.md`(done 조건이 그 표의 갱신이다)를 더한다. `terms-reading.json` · `comments.xml` 은 저장소 규약상 새 함수를 만들면 반드시 따라오는 파생물이다.

---

## Task 1: `survey_plan.py` — 층과 배치를 결정론으로 계산한다

**Files:**
- Create: `codegraph/survey_plan.py`
- Test: `codegraph/test_survey_plan.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`codegraph/test_survey_plan.py` 를 새로 만든다:

```python
#!/usr/bin/env python3
"""survey_plan.py 시험. 합성 그래프로 규칙을, 실제 지도로 규모를 본다."""
import collections
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from survey_plan import layer_of, pack, plan  # noqa: E402


def _cg(nodes, edges):
    return {"nodes": [{"id": i, "name": i, "kind": "function", "file": f, "line": 1}
                      for i, f in nodes],
            "edges": [{"from": s, "to": d} for s, d in edges]}


def test_층은_의존_대상이_없는_것부터():
    """a -> b -> c 면 c 가 층0, b 가 층1, a 가 층2 (K1)."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "c")])
    assert (lv["c"], lv["b"], lv["a"]) == (0, 1, 2)


def test_고립_노드는_층0():
    """간선이 하나도 없어도 의존 대상이 없으므로 층0 이다 (K7)."""
    lv, _ = layer_of({"x": 1}, [])
    assert lv["x"] == 0


def test_순환은_한_덩어리로_접힌다():
    """a <-> b 는 위상 깊이가 정의되지 않는다. 같은 층으로 접고 표시한다."""
    lv, cyc = layer_of({"a": 1, "b": 1, "c": 1}, [("a", "b"), ("b", "a"), ("a", "c")])
    assert lv["a"] == lv["b"] and cyc["a"] and cyc["b"] and not cyc["c"]


def test_out_deg_가_아니라_위상_깊이다():
    """a 는 out_deg 1, d 는 out_deg 2 지만 둘 다 층2 다 — out_deg 로 나누면 순서가 틀린다."""
    lv, _ = layer_of({"a": 1, "b": 1, "c": 1, "d": 1},
                     [("a", "b"), ("b", "c"), ("d", "b"), ("d", "c")])
    assert lv["a"] == 2 and lv["d"] == 2 and lv["b"] == 1 and lv["c"] == 0


def test_같은_파일은_한_배치에():
    """파일이 쪼개지면 두 세션이 같은 파일을 각각 통독하게 된다."""
    bs = pack(["a", "b", "c", "d", "e"],
              {"a": "f1.py", "b": "f1.py", "c": "f1.py", "d": "f2.py", "e": "f2.py"}, target=3)
    for f in ["f1.py", "f2.py"]:
        assert sum(1 for b in bs if f in b["files"]) == 1


def test_큰_파일은_초과를_허용한다():
    """심볼 5개짜리 파일은 target 3 이어도 쪼개지 않는다."""
    bs = pack(list("abcde"), {c: "big.py" for c in "abcde"}, target=3)
    assert len(bs) == 1 and len(bs[0]["symbols"]) == 5


def test_층_안에서_한_파일은_한_배치에만_있다():
    """**lock 없는 설계의 전제다.** 이 성질이 깨지면 두 세션이 같은 파일을 동시에 연다.

    `pack` 을 직접 부르는 위 시험과 달리 `plan` 이 낸 실제 배치를 본다 —
    층을 나누고 배치를 묶는 두 단계가 함께 성립해야 의미가 있다.
    """
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f1"), ("d", "f2"),
              ("e", "f3"), ("f", "f4"), ("g", "f5")], [])
    for L in plan(cg, target=2)["layers"]:
        seen = collections.Counter(f for b in L.get("batches", []) for f in b["files"])
        assert [f for f, n in seen.items() if n > 1] == []


def test_배치의_파일_목록에_빈_이름이_없다():
    """file 이 없는 노드는 빈 문자열로 묶인다. 그대로 두면 프롬프트가
    `file_cache.py get <repo> ` 를 빈 인자로 부르라고 시킨다."""
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "b", "name": "b", "kind": "function", "line": 1})  # file 없음
    for L in plan(cg)["layers"]:
        for b in L.get("batches", []):
            assert "" not in b["files"]


def test_결정론():
    """같은 입력이면 같은 출력. 순서가 흔들리면 계획이 재현되지 않는다."""
    cg = _cg([("a", "f1"), ("b", "f1"), ("c", "f2")], [("a", "b"), ("b", "c")])
    assert json.dumps(plan(cg), sort_keys=True) == json.dumps(plan(cg), sort_keys=True)


def test_external_은_제외():
    cg = _cg([("a", "f1")], [])
    cg["nodes"].append({"id": "ext", "name": "ext", "kind": "external"})
    assert plan(cg)["totals"]["symbols"] == 1


def test_마지막은_비노드_층():
    """K5 — file · module · artifact · key · concept 는 층 축이 없어 맨 뒤 별도 층이다."""
    assert plan(_cg([("a", "f1")], []))["layers"][-1]["kind"] == "non-node"


def test_배치는_자기_심볼의_의존_대상을_들고_있다():
    """배치 프롬프트가 아래층 레코드를 발췌하려면 depends_on 이 계획 안에 있어야 한다."""
    cg = _cg([("a", "f1"), ("b", "f2")], [("a", "b")])
    top = [L for L in plan(cg)["layers"] if L.get("level") == 1][0]
    assert top["batches"][0]["symbols"][0]["depends_on"] == ["b"]


def test_증분은_층_번호를_보존한다():
    """warmup 이 준 파일만 남기되 층은 **전체 그래프 기준**이어야 한다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다."""
    cg = _cg([("a", "f1"), ("b", "f2"), ("c", "f3")], [("a", "b"), ("b", "c")])
    p = plan(cg, only_files=["f1"])
    assert p["totals"]["symbols"] == 1 and p["layers"][0]["level"] == 2


REAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "out", "codegraph-raw", "codegraph.json")


@pytest.mark.skipif(not os.path.exists(REAL), reason="out/codegraph-raw/codegraph.json 이 없다")
def test_이_저장소_실측():
    """🔵 2026-08-30 기준 층 분포 110/32/16/7/2. 코드가 바뀌면 숫자도 바뀐다 — 그때는 값을 갱신한다."""
    p = plan(json.load(open(REAL, encoding="utf-8")))
    sizes = [L["symbol_count"] for L in p["layers"] if L.get("kind") != "non-node"]
    assert sizes == [110, 32, 16, 7, 2]
    assert sum(sizes) == p["totals"]["symbols"] == 167
    # lock 없는 설계의 전제 — 실제 지도에서도 층 안 파일이 배타적이어야 한다
    for L in p["layers"]:
        seen = collections.Counter(f for b in L.get("batches", []) for f in b["files"])
        assert [f for f, n in seen.items() if n > 1] == []
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python -m pytest codegraph/test_survey_plan.py -q
```

기대: `ModuleNotFoundError: No module named 'survey_plan'` 로 수집 단계에서 실패.

- [ ] **Step 3: `codegraph/survey_plan.py` 를 만든다**

```python
#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/survey_plan.py']"/>
# 전수조사를 어떤 순서로 어떻게 쪼개 돌릴지 계획하는 파일.
# 쓰는 것: survey-plan.json, networkx · 쓰이는 곳: run_mode1.main
"""survey_plan.py — 전수조사 배치 계획.

**왜 필요한가.** 심볼의 뜻은 그것이 의존하는 심볼의 뜻 위에 선다. 아무 순서로나 읽으면
아직 안 읽은 것을 가리키게 되고, 그 자리는 추론으로 메워진다. 그래서 **의존 대상이 없는 것부터**
한 겹씩 올라간다. 같은 층끼리는 서로 의존하지 않으므로 병렬로 읽어도 안전하다.

**이 파일은 판정하지 않는다.** 순서를 계산하고 배치를 나눌 뿐이다.

입력은 `prep` 이 이미 낸 `codegraph.json` 이다 — LLM 이 한 글자도 읽기 전에 존재한다.

  survey_plan.py <codegraph.json> [--target 8] [--only-files a.py,b.py] [-o survey-plan.json]
"""
import argparse
import collections
import json
import os
import sys

import networkx as nx


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.layer_of']"/>
# 노드마다 위상 깊이를 매긴다. 순환은 한 덩어리로 접는다.
# 쓰는 것: networkx · 쓰이는 곳: survey_plan.plan
def layer_of(first, edges):
    """의존 대상이 없으면 층0, 아니면 1 + 의존 대상들의 최대 층.

    순환이 있으면 위상 깊이가 정의되지 않으므로 **강결합 성분(SCC)으로 접어** DAG 로 만든 뒤 센다.
    같은 순환에 든 심볼은 같은 층이 되어 같은 배치 후보가 된다 — 서로를 보며 함께 읽으라는 뜻이다.
    이 저장소 자신은 순환이 0개지만 C++ · C# 저장소에서는 흔하다.
    """
    G = nx.DiGraph()
    G.add_nodes_from(first)
    for s, d in edges:
        if s in first and d in first and s != d:
            G.add_edge(s, d)
    C = nx.condensation(G)                 # SCC 를 접은 DAG. C.graph["mapping"] 이 노드->성분
    lv = {}
    for c in reversed(list(nx.topological_sort(C))):   # 뒤에서부터 = 의존 대상이 먼저
        succ = list(C.successors(c))
        lv[c] = 0 if not succ else 1 + max(lv[s] for s in succ)
    m = C.graph["mapping"]
    size = collections.Counter(m.values())
    return {n: lv[m[n]] for n in G}, {n: size[m[n]] > 1 for n in G}


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.pack']"/>
# 한 층의 심볼을 파일이 쪼개지지 않게 목표 크기로 묶는다.
# 쓰는 것: 없음 · 쓰이는 곳: survey_plan.plan
def pack(members, file_of, target):
    """같은 파일의 같은 층 심볼은 **한 배치에** 몰아넣는다 — 층 안 중복 통독을 0으로 만든다.

    파일 하나가 target 을 넘으면 그 파일만으로 배치 하나가 된다(초과를 허용한다).
    쪼개면 그 파일을 두 세션이 각각 통독하게 되어 더 비싸기 때문이다.
    파일명 정렬 뒤 그리디라 같은 입력이면 같은 출력이다.
    """
    byfile = collections.defaultdict(list)
    for n in members:
        byfile[file_of.get(n) or ""].append(n)
    out, cur, curf = [], [], []
    for f in sorted(byfile):
        syms = sorted(byfile[f])
        if cur and len(cur) + len(syms) > target:
            out.append({"files": curf, "symbols": cur})
            cur, curf = [], []
        cur += syms
        curf.append(f)
    if cur:
        out.append({"files": curf, "symbols": cur})
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='survey_plan.plan']"/>
# 코드 지도를 층과 배치로 나눈 계획을 만든다.
# 쓰는 것: survey_plan.layer_of, survey_plan.pack · 쓰이는 곳: run_mode1.main
def plan(cg, target=8, only_files=None):
    """코드 지도 -> 층 · 배치 계획.

    `only_files` 는 증분 재조사용이다 — `warmup.py` 의 `blast_radius` 가 낸 파일 목록을 주면
    그 파일의 심볼만 남긴다. 층 번호는 **전체 그래프 기준으로 매긴 뒤** 거른다.
    거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다.
    """
    nodes = {n["id"]: n for n in cg["nodes"]}
    first = {i: n for i, n in nodes.items() if n.get("kind") != "external"}
    edges = [(e["from"], e["to"]) for e in cg.get("edges", [])]
    lv, in_cycle = layer_of(first, edges)
    file_of = {i: n.get("file") for i, n in first.items()}

    keep = set(first)
    if only_files is not None:
        want = set(only_files)
        keep = {i for i in first if file_of.get(i) in want}

    bylv = collections.defaultdict(list)
    for n in keep:
        bylv[lv[n]].append(n)

    layers = []
    for k in sorted(bylv):
        bs = pack(bylv[k], file_of, target)
        layers.append({
            "level": k,
            "symbol_count": len(bylv[k]),
            "file_count": len({file_of.get(n) for n in bylv[k] if file_of.get(n)}),
            "batches": [
                {"id": "L%d-B%02d" % (k, i),
                 # 빈 이름을 거른다 — file 이 없는 노드가 "" 로 묶여 들어온다.
                 # 그대로 두면 배치 프롬프트가 빈 경로로 통독 캐시를 부르라고 시킨다.
                 "files": [f for f in b["files"] if f],
                 "symbols": [{"id": s, "name": first[s].get("name"), "file": file_of.get(s),
                              "line": first[s].get("line"), "kind": first[s].get("kind"),
                              "in_cycle": in_cycle.get(s, False),
                              "depends_on": sorted({d for (o, d) in edges
                                                    if o == s and d in first and d != s})}
                             for s in b["symbols"]]}
                for i, b in enumerate(bs)],
        })

    # K5 — 그래프 노드가 아닌 용어는 맨 마지막 별도 층. 심볼이 다 읽힌 뒤라야 정확해진다.
    last = (max(bylv) + 1) if bylv else 0
    layers.append({
        "level": last, "kind": "non-node", "symbol_count": None, "batches": [],
        "note": "file · module · artifact · key · concept. 심볼 층이 전부 끝난 뒤 한 세션으로 돈다. "
                "파일 레코드는 그 파일 안 심볼들의 완성 레코드를 재료로 쓴다.",
    })
    return {"target": target, "layers": layers,
            "totals": {"symbols": len(keep), "edges": len(edges), "levels": len(bylv),
                       "cyclic_symbols": sum(1 for n in keep if in_cycle.get(n))}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="전수조사를 층과 배치로 나눈다.")
    ap.add_argument("codegraph", help="prep 이 낸 codegraph.json")
    ap.add_argument("--target", type=int, default=8, help="배치당 목표 심볼 수 (기본 8)")
    ap.add_argument("--only-files", help="증분 재조사. 쉼표로 나눈 파일 목록(warmup blast 의 출력)")
    ap.add_argument("-o", "--out", help="출력 경로. 기본은 codegraph.json 옆 survey-plan.json")
    a = ap.parse_args(argv)
    try:
        cg = json.load(open(a.codegraph, encoding="utf-8"))
    except Exception as ex:
        print("에러 — codegraph.json 을 읽지 못했다: %s" % ex, file=sys.stderr)
        return 1
    p = plan(cg, a.target, a.only_files.split(",") if a.only_files else None)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.codegraph)), "survey-plan.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=1)
    print(out)
    print("  심볼 %d · 간선 %d · 층 %d · 순환에 든 심볼 %d"
          % (p["totals"]["symbols"], p["totals"]["edges"],
             p["totals"]["levels"], p["totals"]["cyclic_symbols"]))
    for L in p["layers"]:
        if L.get("kind") == "non-node":
            print("  층%d — 비노드 용어 (한 세션)" % L["level"])
        else:
            print("  층%d — 심볼 %d · 파일 %d · 배치 %d"
                  % (L["level"], L["symbol_count"], L["file_count"], len(L["batches"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_survey_plan.py -q
```

기대: `14 passed`.

- [ ] **Step 5: 실제 코드 지도로 돌려 층 분포를 눈으로 본다**

```bash
.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json
```

기대 출력 (🔵 2026-08-30 실측과 같아야 한다. **다르면 멈추고 보고한다**):

```
/Users/escatrgot/LLM-Tools/report-builder/out/codegraph-raw/survey-plan.json
  심볼 167 · 간선 105 · 층 5 · 순환에 든 심볼 0
  층0 — 심볼 110 · 파일 39 · 배치 16
  층1 — 심볼 32 · 파일 23 · 배치 4
  층2 — 심볼 16 · 파일 13 · 배치 2
  층3 — 심볼 7 · 파일 7 · 배치 1
  층4 — 심볼 2 · 파일 2 · 배치 1
  층5 — 비노드 용어 (한 세션)
```

- [ ] **Step 6: 결정론과 층 안 파일 중복을 확인한다**

```bash
.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p1.json
.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p2.json
diff /tmp/p1.json /tmp/p2.json && echo "결정론 OK"
.venv/bin/python -c "
import json, collections
p = json.load(open('/tmp/p1.json'))
for L in p['layers']:
    c = collections.Counter(f for b in L.get('batches', []) for f in b['files'])
    print(L['level'], '중복', [f for f, n in c.items() if n > 1] or '없음')"
```

기대: `결정론 OK` 가 찍히고, 모든 층이 `중복 없음`.

- [ ] **Step 7: 커밋**

```bash
git add codegraph/survey_plan.py codegraph/test_survey_plan.py
git commit -m "[feat] : 전수조사를 의존 위상 층과 배치로 나누는 계획기"
```

---

## Task 2: `file_cache.py` — 층 경계 중복 통독을 없앤다

**왜 지금인가.** 🔵 이 저장소 실측 — 유일 파일 41개인데 층별 파일 수를 합치면 84개다(중복 43회). 배치 세션은 컨텍스트가 분리돼 있어 먼저 읽은 쪽의 이해를 나중 쪽에 넘길 방법이 디스크뿐이다.

**Files:**
- Create: `codegraph/file_cache.py`
- Test: `codegraph/test_file_cache.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`codegraph/test_file_cache.py` 를 새로 만든다:

```python
#!/usr/bin/env python3
"""file_cache.py 시험. 캐시가 **내용 해시로** 무효화되는지가 급소다.

mtime 으로 무효화하면 체크아웃 한 번에 멀쩡한 캐시가 통째로 죽고, 반대로
같은 mtime 으로 내용만 바뀌면 낡은 개요가 조용히 살아남는다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import file_cache as FC  # noqa: E402


def _repo(tmp_path, text="처음 내용\n"):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(text, encoding="utf-8")
    return str(tmp_path)


def test_없으면_None(tmp_path):
    """캐시가 없으면 None 이다 — 부르는 쪽이 통독하라는 뜻이다."""
    assert FC.get(_repo(tmp_path), "src/a.py") is None


def test_넣은_것을_그대로_돌려준다(tmp_path):
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"imports": ["os"], "symbols": []})
    got = FC.get(repo, "src/a.py")
    assert got["path"] == "src/a.py"
    assert got["outline"]["imports"] == ["os"]


def test_내용이_바뀌면_무효(tmp_path):
    """줄이 밀린 개요를 그대로 쓰면 where 가 거짓말을 한다."""
    repo = _repo(tmp_path)
    FC.put(repo, "src/a.py", {"symbols": [{"name": "f", "line": 1}]})
    (tmp_path / "src" / "a.py").write_text("바뀐 내용\n", encoding="utf-8")
    assert FC.get(repo, "src/a.py") is None


def test_없는_파일이면_None(tmp_path):
    """지워진 파일에 해시를 낼 수 없다. 터지지 말고 None 이어야 한다."""
    assert FC.get(_repo(tmp_path), "src/없다.py") is None


def test_캐시는_out_아래에_산다(tmp_path):
    """out/ 은 gitignore 다. 재생성 가능한 파생물이 커밋에 섞이면 안 된다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    assert os.path.join("out", "codegraph-raw", "_filecache") in path


def test_파일마다_다른_자리(tmp_path):
    """경로 해시를 키로 쓰므로 두 파일이 서로를 덮지 않는다."""
    repo = _repo(tmp_path)
    (tmp_path / "src" / "b.py").write_text("다른 파일\n", encoding="utf-8")
    FC.put(repo, "src/a.py", {"who": "a"})
    FC.put(repo, "src/b.py", {"who": "b"})
    assert FC.get(repo, "src/a.py")["outline"]["who"] == "a"
    assert FC.get(repo, "src/b.py")["outline"]["who"] == "b"


def test_임시파일을_남기지_않는다(tmp_path):
    """os.replace 로 갈아 끼우므로 .tmp 가 남으면 안 된다 — 남으면 다음 읽기가 반쯤 쓰인 것을 본다."""
    repo = _repo(tmp_path)
    d = os.path.dirname(FC.put(repo, "src/a.py", {}))
    assert [f for f in os.listdir(d) if f.endswith(".tmp")] == []


def test_망가진_캐시는_None(tmp_path):
    """손으로 고쳐 깨졌거나 반쯤 쓰인 파일을 만나도 터지지 않는다."""
    repo = _repo(tmp_path)
    path = FC.put(repo, "src/a.py", {})
    open(path, "w", encoding="utf-8").write("{ 이건 json 이 아니다")
    assert FC.get(repo, "src/a.py") is None
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_file_cache.py -q
```

기대: `ModuleNotFoundError: No module named 'file_cache'`.

- [ ] **Step 3: `codegraph/file_cache.py` 를 만든다**

```python
#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/file_cache.py']"/>
# 파일을 한 번만 통독하도록 통독 결과를 디스크에 남기는 파일.
# 쓰는 것: _filecache/*.json · 쓰이는 곳: 없음
"""file_cache.py — 파일 통독 캐시.

층이 올라가면 같은 파일을 다시 열게 된다(🔵 이 저장소 실측 — 유일 파일 41개, 층별 합계 84개,
중복 43회). 배치 세션끼리는 컨텍스트를 공유하지 못하므로, 먼저 읽은 쪽이 **개요를 디스크에 남기고**
나중 쪽이 그것을 읽는다.

**lock 을 쓰지 않는다.** 임시 파일에 쓰고 `os.replace` 로 갈아 끼우면 POSIX 에서 원자적이라
반쯤 쓰인 파일을 남이 읽는 일이 없다. lock 은 동시 쓰기를 막을 뿐, 이미 읽은 내용을
남에게 넘겨주지는 못한다 — 그건 lock 이 풀 수 있는 문제가 아니다.

**캐시는 개요일 뿐 근거가 아니다.** 자기가 맡은 심볼은 반드시 실제 줄 범위를 열어 읽는다.
캐시만 보고 쓴 레코드는 `confidence` 가 HIGH 일 수 없다.

  file_cache.py get <repo> <파일경로>            → 캐시 출력. 없거나 낡았으면 종료 코드 1
  file_cache.py put <repo> <파일경로> <개요json> → 캐시 기록
"""
import hashlib
import json
import os
import sys


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache._paths']"/>
# 파일의 내용 해시와 그 캐시가 놓일 자리를 함께 낸다.
# 쓰는 것: 없음 · 쓰이는 곳: file_cache.get, file_cache.put
def _paths(repo, rel):
    """내용 해시로 캐시를 무효화한다. mtime 은 체크아웃으로 흔들려 못 믿는다."""
    with open(os.path.join(repo, rel), "rb") as f:
        h = hashlib.sha1(f.read()).hexdigest()
    key = hashlib.sha1(rel.encode("utf-8")).hexdigest()
    return h, os.path.join(repo, "out", "codegraph-raw", "_filecache", key + ".json")


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache.get']"/>
# 남이 남긴 통독 개요가 아직 쓸 만하면 돌려준다.
# 쓰는 것: file_cache._paths · 쓰이는 곳: 없음
def get(repo, rel):
    """캐시가 있고 내용 해시가 같으면 돌려준다. 아니면 None — 부르는 쪽이 통독한다.

    파일이 없거나 캐시가 깨졌어도 터지지 않고 None 이다. 캐시는 최적화라
    실패해도 조사 자체는 굴러가야 한다.
    """
    try:
        h, path = _paths(repo, rel)
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if d.get("sha1") == h else None
    except Exception:
        return None


# <include file="docs/codegraph/comments.xml" path="//term[@id='file_cache.put']"/>
# 통독 개요를 원자적으로 남긴다.
# 쓰는 것: file_cache._paths · 쓰이는 곳: 없음
def put(repo, rel, outline):
    """개요를 남긴다. 임시 파일 + os.replace 라 원자적이다."""
    h, path = _paths(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"path": rel, "sha1": h, "outline": outline}, f,
                  ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    cmd, repo, rel = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "get":
        d = get(repo, rel)
        if d is None:
            sys.exit(1)
        json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
    elif cmd == "put":
        with open(sys.argv[4], encoding="utf-8") as f:
            print(put(repo, rel, json.load(f)))
    else:
        sys.exit("모르는 명령 %s" % cmd)
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_file_cache.py -q
```

기대: `8 passed`.

- [ ] **Step 5: CLI 를 손으로 한 번 돌려 본다**

```bash
echo '{"imports":["os"],"symbols":[]}' > /tmp/outline.json
.venv/bin/python codegraph/file_cache.py put . codegraph/survey_plan.py /tmp/outline.json
.venv/bin/python codegraph/file_cache.py get . codegraph/survey_plan.py
```

기대: `put` 이 `out/codegraph-raw/_filecache/<해시>.json` 경로를 찍고, `get` 이 그 JSON 을 되돌려준다.

- [ ] **Step 6: 커밋**

```bash
git add codegraph/file_cache.py codegraph/test_file_cache.py
git commit -m "[feat] : 층 경계 중복 통독을 막는 파일 통독 캐시"
```

---

## Task 3: 단계를 여섯으로 가른다 — 잠긴 결정을 테스트로 뒤집는다

**Files:**
- Modify: `codegraph/run_mode1.py:64-104` (`STAGES` · `AGENT_STAGES` · `plan_stages`)
- Modify: `codegraph/test_run_mode1.py:30-53` (갈아 끼운다)

- [ ] **Step 1: 옛 결정을 지키던 시험을 새 결정을 지키는 시험으로 갈아 끼운다**

`codegraph/test_run_mode1.py` 에서 `test_plan_runs_everything_on_an_empty_repo`(`:30`) · `test_only_one_stage_calls_the_model`(`:36`) · `test_plan_skips_the_agent_when_its_output_already_exists`(`:42`) · `test_plan_keeps_the_agent_when_only_half_its_work_is_done`(`:49`) 네 개를 아래로 **교체**한다. **지우지 말고 갈아 끼운다** — 무엇이 왜 바뀌었는지가 docstring 에 남아야 한다.

```python
def test_빈_저장소면_여섯_단계를_순서대로_돈다():
    """예전에는 다섯이었다(prep agent terms build check).

    2026-08-30 사용자 결정으로 `agent` 가 `survey` 와 `wiki` 로 갈리고 `terms` 가 그 사이로 왔다.
    `terms` 를 가운데 둔 이유는 산문 세션이 **인용 검사를 통과한** terms-db.json 을
    재료로 받게 하려는 것이다. 예전에는 산문이 검사 전 레코드를 봤다.
    """
    assert R.plan_stages(has_codegraph=False, has_reading=False, has_prose=False) == [
        "prep", "survey", "terms", "wiki", "build", "check"]


def test_두_단계가_모형을_부른다():
    """예전에는 `agent` 한 칸이었고 그것이 **이 설계의 급소**라고 적혀 있었다.

    이유는 캐시였다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어 토큰이 부풀고,
    측정값이 파이프라인 비용이 아니라 세션 수의 함수가 된다.
    **2026-08-30 사용자가 그 결정을 뒤집었다.** 층 오름차순 병렬이 세션 분리를 전제하기 때문이다.
    캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다 — 어느 쪽이 큰지는 **아직 재지 않았다.**
    """
    stages = R.plan_stages(False, False, False)
    assert [s for s in stages if R.is_agent_stage(s)] == ["survey", "wiki"]


def test_산출물이_있는_LLM_단계만_각자_빠진다():
    """예전에는 `agent` 하나를 `has_reading and has_prose` 로 걸렀다.

    이제 각자 자기 산출물로 걸린다 — 한쪽만 있으면 그쪽만 건너뛴다. 이건 **개선**이지 회귀가 아니다.
    """
    both = R.plan_stages(has_codegraph=True, has_reading=True, has_prose=True)
    assert "survey" not in both and "wiki" not in both
    assert both == ["prep", "terms", "build", "check"]

    only_reading = R.plan_stages(True, True, False)
    assert "survey" not in only_reading and "wiki" in only_reading

    only_prose = R.plan_stages(True, False, True)
    assert "survey" in only_prose and "wiki" not in only_prose
```

`test_plan_only_and_skip_are_honoured`(`:60`) 의 `only=["prep", "check"]` 는 그대로 통과한다. 고치지 않는다.

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: 위 세 개가 `AssertionError` 로 실패. `survey` 가 아직 `STAGES` 에 없으므로 `plan_stages` 는 여전히 다섯을 낸다.

- [ ] **Step 3: `run_mode1.py:64-68` 의 상수를 고친다**

```python
# 단계는 여섯 고정이다. 레지스트리도 플러그인도 만들지 않는다(거울 함정).
STAGES = ["prep", "survey", "terms", "wiki", "build", "check"]

# 모형을 부르는 단계. **둘 다 층 오름차순으로 여러 번** 부른다 — 예전의 한 번이 아니다.
AGENT_STAGES = {"survey", "wiki"}
```

- [ ] **Step 4: `plan_stages` 의 걸러내는 분기를 고친다**

`run_mode1.py:83-104` 의 docstring 과 루프를 아래로 바꾼다. 시그니처는 **그대로 둔다** — 부르는 쪽(`main`)과 시험이 이미 그 이름을 쓴다.

```python
def plan_stages(has_codegraph, has_reading, has_prose, only=None, skip=None):
    """무엇을 돌릴지 정한다. 파일 시스템을 보지 않는 순수 함수라 시험이 쉽다.

    `prep` 은 늘 남긴다 — 이미 코드 지도가 있으면 건너뛸지를 `prepPlan` 자신이 정한다
    (`scripts/wiki/prep.mjs` 의 `hasCodegraph`). 여기서 미리 빼면 그 판단을 뺏는 것이다.

    LLM 단계 둘은 **각자 자기 산출물로 걸린다.** `survey` 는 읽기 레코드가 있으면,
    `wiki` 는 산문이 있으면 빠진다. 한쪽만 있으면 그쪽만 건너뛴다.
    """
    for name in list(only or []) + list(skip or []):
        if name not in STAGES:
            raise ValueError("모르는 단계: %s (있는 것: %s)" % (name, ", ".join(STAGES)))
    if only:
        return [s for s in STAGES if s in set(only)]
    out = []
    for s in STAGES:
        if s in set(skip or []):
            continue
        if s == "survey" and has_reading:
            continue
        if s == "wiki" and has_prose:
            continue
        out.append(s)
    return out
```

- [ ] **Step 5: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q
```

기대: 실패가 남는다 — `main()` 이 아직 `stage == "agent"` 를 보고, `agent_prompt` 를 쓰는 `test_the_prompt_names_both_halves_of_the_one_agent_job` 도 살아 있다. **`plan_stages` 관련 시험 세 개가 통과하는 것만 확인하고 다음 Task 로 간다:**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "단계 or 모형을_부른다 or 산출물이_있는"
```

기대: `3 passed`.

- [ ] **Step 6: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[refactor] : mode 1 의 에이전트 칸을 survey 와 wiki 로 가른다"
```

---

## Task 4: `run_agent_with` 와 `run_layer` — 층 하나를 동시에 돌린다

**왜 이 모양인가.** 배치마다 다른 글을 주므로 프롬프트를 인자로 받는 함수가 필요하다. 시간을 그 안에서 재는 이유는, 배치가 동시에 도는 동안 부르는 쪽은 **층 전체**만 잴 수 있어 어느 배치가 비쌌는지 모르기 때문이다.

**자식 프로세스를 기다리는 일이라 스레드로 충분하다.** GIL 은 여기서 문제가 되지 않는다. 새 의존성 없이 표준 라이브러리 `concurrent.futures` 를 쓴다.

**Files:**
- Modify: `codegraph/run_mode1.py` (`run_agent` 를 `run_agent_with` 로 가르고 `run_layer` 를 더한다)
- Modify: `codegraph/test_run_mode1.py` (새 시험을 더한다)

- [ ] **Step 1: 실패하는 시험을 쓴다**

`codegraph/test_run_mode1.py` 맨 아래에 절을 하나 더한다:

```python
# ── 7. 층 병렬 — 동시에 몇 개까지 뜨는가 (2026-08-30 신설)
def test_run_layer_는_동시_한도를_넘지_않는다(monkeypatch):
    """K4 — 한 층에서 동시에 8배치까지. 넘으면 rate limit 에 걸려 층 전체가 무너진다.

    실제로 `claude` 를 부르지 않는다. `run_agent_with` 를 바꿔 끼워 **동시에 몇 개가
    살아 있었는지**만 센다.
    """
    import threading
    lock, live, peak = threading.Lock(), [0], [0]

    def fake(model, repo, root, prompt, timeout=None, label=None):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.02)
        with lock:
            live[0] -= 1
        return 0.02, 0, {"usage": {"output_tokens": 1}, "num_turns": 1}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B%02d" % i, "글 %d" % i) for i in range(20)]
    got = R.run_layer("opus", "/r", "/root", jobs, concurrency=3)
    assert peak[0] <= 3
    assert len(got) == 20


def test_run_layer_는_라벨_순서로_돌려준다(monkeypatch):
    """배치가 끝나는 순서는 흔들린다. 보고 표가 실행마다 달라지면 대조를 못 한다."""
    monkeypatch.setattr(R, "run_agent_with",
                        lambda *a, **k: (0.01, 0, {"usage": {}, "num_turns": 0}))
    jobs = [("L0-B02", "다"), ("L0-B00", "가"), ("L0-B01", "나")]
    labels = [row[0] for row in R.run_layer("opus", "/r", "/root", jobs)]
    assert labels == ["L0-B00", "L0-B01", "L0-B02"]


def test_run_layer_는_한_배치가_죽어도_나머지를_돌린다(monkeypatch):
    """배치 하나가 터졌다고 층 전체를 버리면 20분이 날아간다. 실패는 행으로 남기고 계속 간다."""
    def fake(model, repo, root, prompt, timeout=None, label=None):
        if label == "L0-B01":
            raise RuntimeError("자식이 죽었다")
        return 0.01, 0, {"usage": {}, "num_turns": 0}

    monkeypatch.setattr(R, "run_agent_with", fake)
    jobs = [("L0-B00", "가"), ("L0-B01", "나"), ("L0-B02", "다")]
    rows = R.run_layer("opus", "/r", "/root", jobs)
    bad = [r for r in rows if r[0] == "L0-B01"][0]
    assert bad[2] != 0 and bad[3] is None      # (라벨, 초, 종료코드, 결과)
    assert len(rows) == 3


def test_빈_층은_모형을_부르지_않는다(monkeypatch):
    """샤드가 이미 다 있으면 할 일이 없다. 그런데도 부르면 돈만 나간다(J4)."""
    monkeypatch.setattr(R, "run_agent_with",
                        lambda *a, **k: pytest.fail("빈 층에서 모형을 불렀다"))
    assert R.run_layer("opus", "/r", "/root", []) == []
```

파일 맨 위 import 에 `time` 을 더한다:

```python
import os
import sys
import time
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "run_layer or 빈_층"
```

기대: `AttributeError: module 'run_mode1' has no attribute 'run_layer'` 로 4건 실패.

- [ ] **Step 3: `run_mode1.py:355-370` 의 `run_agent` 를 가른다**

기존 `run_agent` 를 **지우고**(J2 — `run_mode2.py` 와 `run_mode1_5.py` 는 자기 것을 따로 갖는다) 아래 둘을 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_agent_with']"/>
# 주어진 글로 모형을 한 번 부르고 걸린 시간과 결과를 함께 낸다.
# 쓰는 것: run_mode1.claude_argv · 쓰이는 곳: run_mode1.run_layer
def run_agent_with(model, repo, root, prompt, timeout=None, label=None):
    """`claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`.

    **시간을 여기서 잰다.** 배치들이 동시에 도는 동안 부르는 쪽은 층 전체만 잴 수 있어
    어느 배치가 비쌌는지 모른다. 다음에 `--target` 을 조절하려면 배치별 값이 있어야 한다.

    **하트비트를 여기 두지 않는다.** 8개가 동시에 찍으면 화면이 못 읽는 글이 된다 —
    층 하나를 감싸는 하트비트 하나면 충분하다(`run_layer` 를 부르는 쪽이 건다).
    """
    argv = claude_argv(model=model, repo=repo, extra_dirs=[root])
    t0 = time.monotonic()
    p = subprocess.run(argv, input=prompt, cwd=repo,
                       capture_output=True, text=True, timeout=timeout)
    seconds = time.monotonic() - t0
    try:
        return seconds, p.returncode, json.loads(p.stdout)
    except (ValueError, TypeError):
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print("[%s] %s" % (label or "?", tail), file=sys.stderr)
        return seconds, p.returncode, None


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_layer']"/>
# 한 층의 배치들을 동시에 돌리고 각각의 측정값을 모은다.
# 쓰는 것: run_mode1.run_agent_with · 쓰이는 곳: run_mode1.main
def run_layer(model, repo, root, jobs, concurrency=8, timeout=None):
    """한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다(K2).

    같은 층끼리는 서로 의존하지 않으므로 순서가 결과를 바꾸지 않는다 — 그래서 병렬이 안전하다.
    **자식 프로세스를 기다리는 일이라 스레드로 충분하다.** GIL 은 여기서 문제가 되지 않는다.

    `jobs` 는 `[(라벨, 프롬프트), …]`. 낸 것은 `[(라벨, 초, 종료코드, 결과 또는 None), …]` 이고
    **라벨 순서로 정렬**해서 낸다 — 끝나는 순서는 실행마다 흔들려 보고 표를 대조할 수 없게 된다.

    **한 배치가 터져도 층을 버리지 않는다.** 20분짜리 층이 예외 하나로 날아가면 안 된다.
    터진 배치는 종료 코드 -1 · 결과 None 인 행으로 남고, 부르는 쪽이 실패로 센다.
    """
    if not jobs:
        return []
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
        futs = {ex.submit(run_agent_with, model, repo, root, prompt, timeout, label): label
                for label, prompt in jobs}
        for f in futs:
            label = futs[f]
            try:
                rows.append((label,) + f.result())
            except Exception as ex_:                      # noqa: BLE001 — 층을 살린다
                print("[%s] 배치가 터졌다: %s" % (label, ex_), file=sys.stderr)
                rows.append((label, 0.0, -1, None))
    return sorted(rows, key=lambda r: r[0])
```

`run_mode1.py` 의 import 절(`:53-59`)에 한 줄을 더한다:

```python
from concurrent.futures import ThreadPoolExecutor
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "run_layer or 빈_층"
```

기대: `4 passed`.

- [ ] **Step 5: 다른 두 실행기가 안 깨졌는지 확인한다**

`run_agent` 를 지웠으므로 확인이 필요하다.

```bash
grep -n "M\.run_agent\b\|M\.agent_prompt\b" codegraph/run_mode2.py codegraph/run_mode1_5.py
.venv/bin/python -m pytest codegraph/test_run_mode2.py codegraph/test_run_mode1_5.py -q
```

기대: `grep` 이 아무것도 못 찾고(종료 코드 1), 두 시험 파일이 전부 통과.

- [ ] **Step 6: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[feat] : 층 하나를 동시에 도는 실행기와 배치별 측정"
```

---

## Task 5: `merge_shards` — 키 충돌은 전역을 보는 쪽만 푼다

**왜 오케스트레이터인가.** 배치 세션은 자기 배치만 본다. `main` 이라는 이름이 9개 파일에 있다는 것을 알 수 없다. 전역을 보는 것은 이 함수뿐이므로 **개명은 여기서만** 한다. 한쪽만 한정하면 나중에 또 겹친다 — 겹친 **전원**을 `<파일줄기>.<이름>` 으로 고친다.

**Files:**
- Modify: `codegraph/run_mode1.py` (`merge_shards` 를 더한다)
- Modify: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`codegraph/test_run_mode1.py` 에 이어 붙인다:

```python
# ── 8. 샤드 병합 — 키 충돌은 전역을 보는 쪽만 푼다
def _shard(tmp_path, name, payload):
    import json as _j
    d = tmp_path / "_shards"
    d.mkdir(exist_ok=True)
    (d / (name + ".json")).write_text(_j.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(d)


def test_샤드를_하나로_합친다(tmp_path):
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    _shard(tmp_path, "L0-B01", {"나": {"where": "b.py:1"}})
    got = R.merge_shards(d, {})
    assert sorted(got) == ["가", "나"]


def test_키가_겹치면_양쪽_다_개명한다(tmp_path):
    """한쪽만 한정하면 나중에 또 겹친다. `main` 이 9파일이면 9개 전부 개명이다."""
    d = _shard(tmp_path, "L0-B00", {"main": {"where": "app/gui.py:10"}})
    _shard(tmp_path, "L0-B01", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {})
    assert "main" not in got
    assert sorted(got) == ["gui.main", "net.main"]


def test_아래층_레코드를_보존한다(tmp_path):
    """층 k 의 병합이 층 <k 의 결과를 지우면 조사가 층마다 초기화된다."""
    d = _shard(tmp_path, "L1-B00", {"위": {"where": "b.py:1"}})
    got = R.merge_shards(d, {"아래": {"where": "a.py:1"}})
    assert sorted(got) == ["아래", "위"]


def test_이미_있는_키와_겹쳐도_양쪽_다_개명한다(tmp_path):
    """아래층이 이미 쓴 이름과 겹치는 경우다. 새 것만 한정하면 옛 것이 계속 모호하다."""
    d = _shard(tmp_path, "L1-B00", {"main": {"where": "core/net.py:20"}})
    got = R.merge_shards(d, {"main": {"where": "app/gui.py:10"}})
    assert sorted(got) == ["gui.main", "net.main"]


def test_망가진_샤드는_건너뛰고_나머지를_살린다(tmp_path):
    """배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 20분을 버리지 않는다."""
    d = _shard(tmp_path, "L0-B00", {"가": {"where": "a.py:1"}})
    (tmp_path / "_shards" / "L0-B01.json").write_text("{ 깨진", encoding="utf-8")
    assert sorted(R.merge_shards(d, {})) == ["가"]


def test_샤드_폴더가_없으면_있던_것을_그대로(tmp_path):
    assert R.merge_shards(str(tmp_path / "없다"), {"가": {}}) == {"가": {}}
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "샤드 or 키가_겹치면 or 아래층 or 이미_있는_키"
```

기대: `AttributeError: … has no attribute 'merge_shards'` 로 6건 실패.

- [ ] **Step 3: `merge_shards` 를 만든다**

`run_mode1.py` 의 `run_layer` 아래에 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.merge_shards']"/>
# 배치들이 따로 쓴 조각을 하나로 합치고 이름 충돌을 푼다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def merge_shards(shard_dir, existing):
    """샤드를 합쳐 읽기 레코드 하나로 만든다. **키 충돌 해소는 여기서만 한다.**

    배치 세션은 자기 배치만 보므로 `main` 이 9파일에 있다는 것을 알 수 없다.
    전역을 보는 것은 이 함수뿐이다 — 겹치면 겹친 **전원**을 `<파일줄기>.<이름>` 으로 고친다.
    한쪽만 한정하면 나중에 또 겹친다(`codebase-terms-survey` 스킬의 키 규칙).

    **망가진 샤드는 건너뛴다.** 배치 하나가 반쯤 쓰고 죽어도 나머지 배치의 결과를 버리지 않는다.
    무엇을 건너뛰었는지는 stderr 에 적어 사람이 다시 돌릴 수 있게 한다.
    """
    got = dict(existing or {})
    if not os.path.isdir(shard_dir):
        return got
    for fname in sorted(os.listdir(shard_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(shard_dir, fname), encoding="utf-8") as f:
                shard = json.load(f)
        except (ValueError, OSError) as ex:
            print("샤드를 건너뛴다 — %s: %s" % (fname, ex), file=sys.stderr)
            continue
        for key, rec in shard.items():
            if key in got and got[key] is not rec:
                # 겹친 전원을 개명한다. 이미 들어와 있던 쪽도 함께 고친다.
                old = got.pop(key)
                got[_qualified(key, old)] = old
                got[_qualified(key, rec)] = rec
            else:
                got[key] = rec
    return got


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1._qualified']"/>
# 겹친 이름 앞에 파일 줄기를 붙여 서로 구별되게 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.merge_shards
def _qualified(key, rec):
    """`<파일줄기>.<이름>`. `where` 가 없으면 손댈 근거가 없으므로 이름을 그대로 둔다."""
    where = (rec or {}).get("where") or ""
    stem = os.path.splitext(os.path.basename(where.split(":")[0]))[0]
    return "%s.%s" % (stem, key) if stem else key
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "샤드 or 키가_겹치면 or 아래층 or 이미_있는_키"
```

기대: `6 passed`.

- [ ] **Step 5: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[feat] : 배치 샤드를 합치고 키 충돌을 전원 개명으로 푼다"
```

---

## Task 6: 전수조사 프롬프트 둘 — 배치와 비노드 층

**Files:**
- Modify: `codegraph/run_mode1.py` (`agent_prompt` 를 지우고 `dep_excerpt` · `survey_batch_prompt` · `nonnode_prompt` 를 넣는다)
- Modify: `codegraph/test_run_mode1.py:140-145` (`test_the_prompt_names_both_halves_of_the_one_agent_job` 을 갈아 끼운다)

- [ ] **Step 1: 옛 시험을 갈아 끼우고 새 시험을 더한다**

`codegraph/test_run_mode1.py:140` 의 `test_the_prompt_names_both_halves_of_the_one_agent_job` 을 **지우고** 그 자리에 넣는다:

```python
def test_배치_프롬프트는_자기_심볼과_자기_샤드만_말한다():
    """예전에는 한 프롬프트가 전수조사와 산문을 **둘 다** 지시했다
    (`test_the_prompt_names_both_halves_of_the_one_agent_job`).

    2026-08-30 사용자 결정으로 갈렸다. 배치 세션은 자기 심볼만 읽고 자기 샤드에만 쓴다 —
    terms-reading.json 을 직접 고치면 동시에 도는 다른 배치가 서로를 지운다.
    """
    batch = {"id": "L1-B00", "files": ["core/net.py"],
             "symbols": [{"id": "send", "name": "send", "file": "core/net.py",
                          "line": 42, "kind": "function", "in_cycle": False,
                          "depends_on": ["encode"]}]}
    p = R.survey_batch_prompt(repo="/어느/저장소", root="/도구/뿌리",
                              batch=batch, dep_records="  - encode — 바이트로 바꾼다")
    assert "/어느/저장소" in p and "/도구/뿌리" in p
    assert "L1-B00" in p
    assert "core/net.py" in p and "42" in p
    assert "encode — 바이트로 바꾼다" in p           # 아래층 레코드를 발췌해 준다
    assert "_shards/L1-B00.json" in p               # 쓰는 곳은 자기 샤드뿐
    assert "terms-reading.json" in p                # 열지도 고치지도 말라고 적혀 있다
    assert "file_cache.py" in p                     # 통독 캐시를 먼저 본다
    assert "이름으로 보아" in p                       # 금지표
    assert "confidence" in p


def test_배치_프롬프트는_아래층이_없으면_최하층이라고_말한다():
    """층0 은 의존 대상이 없다. 빈 칸을 그냥 두면 세션이 무엇이 빠졌는지 헷갈린다."""
    batch = {"id": "L0-B00", "files": ["a.py"],
             "symbols": [{"id": "f", "name": "f", "file": "a.py", "line": 1,
                          "kind": "function", "in_cycle": False, "depends_on": []}]}
    p = R.survey_batch_prompt("/r", "/root", batch, "")
    assert "최하층" in p


def test_비노드_프롬프트는_심볼이_아닌_종류만_말한다():
    """K5 — file · module · artifact · key · concept 는 층 축이 없다.
    심볼 레코드가 재료이므로 심볼 층이 전부 끝난 뒤에 돈다."""
    p = R.nonnode_prompt(repo="/어느/저장소", root="/도구/뿌리")
    for kind in ["file", "module", "artifact", "key", "concept"]:
        assert kind in p
    assert "_shards/" in p
    assert "이름으로 보아" in p


def test_의존_발췌는_아래층에_있는_것만_낸다():
    """전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 캐시 이점이 사라진다."""
    merged = {"encode": {"means": "바이트로 바꾼다"}, "무관": {"means": "상관없다"}}
    batch = {"symbols": [{"id": "send", "depends_on": ["encode", "아직없음"]}]}
    got = R.dep_excerpt(merged, batch)
    assert "encode" in got and "바이트로 바꾼다" in got
    assert "무관" not in got
    assert "아직없음" not in got


def test_의존_발췌는_아무것도_없으면_빈_문자열():
    assert R.dep_excerpt({}, {"symbols": [{"id": "a", "depends_on": []}]}) == ""
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "배치_프롬프트 or 비노드 or 의존_발췌"
```

기대: `AttributeError: … has no attribute 'survey_batch_prompt'` 로 5건 실패.

- [ ] **Step 3: `agent_prompt` 를 지우고 세 함수를 넣는다**

`run_mode1.py:181-240` 의 `agent_prompt` 를 통째로 **지우고**(J2) 그 자리에 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.dep_excerpt']"/>
# 이 배치가 의존하는 아래층 레코드만 골라 짧은 글로 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.survey_batch_prompt
def dep_excerpt(merged, batch):
    """배치의 심볼들이 `depends_on` 으로 가리키는 것 중 **이미 완성된** 레코드만 발췌한다.

    전량을 주입하면 층이 올라갈수록 프롬프트가 부풀어 쪼갠 이점이 사라진다.
    아직 레코드가 없는 이름은 아예 뺀다 — 없는 것을 가리키면 세션이 그 자리를 추론으로 메운다.
    """
    want = sorted({d for s in batch.get("symbols", []) for d in s.get("depends_on", [])})
    lines = ["  - %s — %s" % (k, (merged[k] or {}).get("means") or "(뜻 없음)")
             for k in want if k in merged]
    return "\n".join(lines)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.survey_batch_prompt']"/>
# 배치 하나를 맡을 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def survey_batch_prompt(repo, root, batch, dep_records):
    """배치 하나 = 세션 하나. **자기 심볼만** 읽고 자기 샤드에만 쓴다.

    `dep_records` 는 **아래층에서 이미 완성된** 레코드 중 이 배치의 심볼이 의존하는 것만
    발췌한 것이다(`dep_excerpt`). 전량을 주입하면 층이 올라갈수록 프롬프트가 부푼다.
    """
    syms = "\n".join(
        "  - %s (%s) %s:%s   의존 -> %s"
        % (s["name"], s["kind"], s["file"], s["line"],
           ", ".join(s.get("depends_on") or []) or "없음")
        for s in batch["symbols"])
    return """\
너는 코드베이스 전수조사의 배치 {bid} 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 너보다 아래층은 이미 끝났다 — 다시 조사하지 마라

{deps}

## 네가 맡은 심볼 {n}개 — 이것만 한다

{syms}

## 읽는 법 — 순서를 지킨다

1. 담당 파일마다 통독 캐시를 먼저 본다:
     {root}/.venv/bin/python {root}/codegraph/file_cache.py get {repo} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 남긴다:
     {root}/.venv/bin/python {root}/codegraph/file_cache.py put {repo} <파일경로> <개요json>
     개요 꼴 — 심볼마다 {{name, kind, line, end_line, signature, one_line}} 에
     파일의 imports 와 head_comment 를 더한 객체.
2. **네 심볼은 캐시로 때우지 않는다.** 반드시 그 줄 범위를 실제로 읽는다.
   캐시는 남의 심볼을 uses[].to 로 가리킬 때만 쓴다.

## 레코드 계약

{{kind, module, where, means, does, uses[], confidence, source:"reading"}}
- where = `경로:줄` (필수. 기계가 L1 파일 / L2 줄 / L3 근처에 이름 으로 검사한다)
- means = 무엇인가, 한 문장. **객체지향을 갓 배운 대학 1학년 눈높이.** 어려운 용어로 설명하지 않는다
- does  = 무엇을 하는가, 한두 문장
- uses[] = {{to, kind, label, where}}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
- confidence = HIGH(코드를 읽고 썼다) / MEDIUM(일부 읽고 나머지는 추론) / LOW(이름·구조에서 추론)
  **전부 HIGH 로 적으면 그 칸이 장식이 된다.**

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 함수를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "…에 연결될 것 같다"    -> import 나 호출을 실제로 따라간다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 쓰는 곳 — 여기 말고 아무 데도 쓰지 않는다

  {repo}/out/codegraph-raw/_shards/{bid}.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 열지도 고치지도 않는다.** 지금 다른 배치들이 동시에 돌고 있다.
키가 다른 파일과 겹칠 것 같아도 **네가 고치지 않는다** — 층이 끝날 때 일괄 해소된다. 보고에 적기만 한다.
**커밋하지 않는다.**

## 끝내기 전에

- 심볼 {n}개에 레코드가 {n}개 있는가
- where 의 줄 번호를 실제로 열어 확인했는가
- confidence 가 전부 HIGH 는 아닌가
- 샤드 파일 하나만 만들었는가

보고: 레코드 수 · confidence 분포 · 통독한 파일과 캐시로 때운 파일 · 키 충돌 후보 · 읽지 못한 것과 이유.
""".format(repo=repo, root=root, bid=batch["id"], n=len(batch["symbols"]),
           syms=syms, deps=dep_records or "  (없음 — 너는 최하층이다)")


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.nonnode_prompt']"/>
# 지도에 없는 용어들을 맡을 마지막 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def nonnode_prompt(repo, root):
    """K5 — file · module · artifact · key · concept. 심볼이 전부 읽힌 뒤 한 세션으로 돈다.

    이것들은 코드 지도의 노드가 아니라 **층 축이 없다.** 대신 심볼 레코드가 재료다 —
    파일 레코드는 그 파일 안 심볼들의 완성된 means/does 를 보고 쓴다.
    그래서 심볼 층이 하나라도 남아 있으면 이 세션을 띄우면 안 된다.
    """
    return """\
너는 코드베이스 전수조사의 **마지막 층** 담당이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 심볼은 이미 전부 끝났다

  {repo}/docs/codegraph/terms-reading.json   앞선 층들이 합쳐 놓은 심볼 레코드

이 파일을 **읽기만** 한다. 고치지 않는다.

## 네가 맡은 것 — 코드 지도의 노드가 아닌 용어 다섯 종류

| kind | 무엇 | where 는 어디 |
|---|---|---|
| `file` | 소스 파일 하나 | `경로:1` |
| `module` | 디렉토리 하나 | 없어도 된다 |
| `artifact` | 이 저장소가 **만들어 내는** 파일 | 그 파일을 **쓰는** 줄 |
| `key` | 설정·JSON 의 이름난 칸 | 그 키를 **채우는** 줄 |
| `concept` | 코드에 글자로 있는 낱말 | 그 낱말이 있는 줄 |

**`file` `module` `artifact` `key` `concept` 는 이름이 그 줄에 글자 그대로 있어야 한다** —
기계가 L3(근처에 그 이름) 으로 검사한다.

`file` 레코드는 **그 파일 안 심볼들의 완성된 means/does 를 재료로** 쓴다. 다시 통독하지 않는다.
`concept` 은 **코드에 글자로 없는 것을 만들지 않는다** — 계획서에만 있는 개념은 여기 싣지 않는다.

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 자리를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 레코드 계약과 쓰는 곳

{{kind, module, where, means, does, uses[], confidence, source:"reading"}} 이고
쓰는 곳은 **여기 하나뿐**이다:

  {repo}/out/codegraph-raw/_shards/NONNODE.json      꼴은 {{"키": 레코드}}

**terms-reading.json 을 고치지 않는다. 커밋하지 않는다.**

보고: 종류별 레코드 수 · confidence 분포 · 근거를 못 찾아 뺀 것과 이유.
""".format(repo=repo, root=root)
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "배치_프롬프트 or 비노드 or 의존_발췌"
```

기대: `5 passed`.

- [ ] **Step 5: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[feat] : 배치와 비노드 층의 전수조사 프롬프트"
```

---

## Task 7: 위키 프롬프트 둘과 페이지 층 매기기 (K6)

**왜 카탈로그 세션이 먼저인가 (J3).** K6 은 "페이지의 층 = 그 페이지가 인용하는 심볼의 최대 층" 이다. 그러려면 **페이지 목록과 각 페이지가 인용할 심볼**이 먼저 있어야 한다. deep-wiki 의 페이지는 심볼도 모듈도 아닌 **주제** 단위(Getting Started / Deep Dive)라 기계가 결정론으로 만들 수 없다. 그래서 `wiki` 단계는 카탈로그 세션 1개로 시작한다.

**왜 최대 층인가.** 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신 링크할 수 있다. 가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다.

**deep-wiki 플러그인을 고치지 않는다.** `~/.claude/plugins/cache/` 에 사는 캐시라 업데이트에 덮인다. 대신 우리 프롬프트가 감싸서 지시한다 — 지금 코드가 이미 쓰는 방식이다.

**Files:**
- Modify: `codegraph/run_mode1.py` (`symbol_layers` · `page_layers` · `wiki_catalogue_prompt` · `wiki_page_prompt`)
- Modify: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
# ── 9. 위키도 같은 층 순서로 (K6)
def test_심볼_층_표를_계획에서_뽑는다():
    """페이지 층을 매기려면 심볼마다 층이 몇인지 알아야 한다."""
    plan = {"layers": [
        {"level": 0, "batches": [{"id": "L0-B00", "symbols": [{"id": "encode"}]}]},
        {"level": 1, "batches": [{"id": "L1-B00", "symbols": [{"id": "send"}]}]},
        {"level": 2, "kind": "non-node", "batches": []},
    ]}
    assert R.symbol_layers(plan) == {"encode": 0, "send": 1}


def test_페이지_층은_인용한_심볼의_최대():
    """가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다."""
    sym = {"encode": 0, "send": 1, "retry": 3}
    pages = [{"file": "protocol.md", "symbols": ["encode", "send"]},
             {"file": "net.md", "symbols": ["retry", "encode"]}]
    assert R.page_layers(pages, sym) == {"protocol.md": 1, "net.md": 3}


def test_인용_심볼이_없는_페이지는_층0():
    """index.md 처럼 개괄만 있는 장이다. 맨 먼저 써도 아무것도 앞지르지 않는다."""
    assert R.page_layers([{"file": "index.md", "symbols": []}], {}) == {"index.md": 0}


def test_모르는_심볼은_층을_올리지_않는다():
    """카탈로그가 지어낸 이름 하나로 페이지가 맨 뒤로 밀리면 안 된다."""
    assert R.page_layers([{"file": "a.md", "symbols": ["없는것"]}], {"x": 4}) == {"a.md": 0}


def test_카탈로그_프롬프트는_계획_파일을_내라고_말한다():
    p = R.wiki_catalogue_prompt(repo="/어느/저장소", root="/도구/뿌리")
    assert "/어느/저장소" in p and "/도구/뿌리" in p
    assert "wiki-plan.json" in p
    assert "terms-db.json" in p          # 인용 검사를 통과한 재료를 본다
    assert "index.md" in p
    assert "symbols" in p                # 페이지마다 인용할 심볼 키를 적게 한다


def test_페이지_프롬프트는_아래층_페이지를_링크하라고_말한다():
    """재설명 대신 링크하게 하는 것이 층 순서를 지키는 이유다."""
    page = {"file": "net.md", "title": "네트워크", "symbols": ["send"]}
    p = R.wiki_page_prompt(repo="/어느/저장소", root="/도구/뿌리", page=page,
                           lower_pages="  - protocol.md — 프로토콜")
    assert "net.md" in p and "네트워크" in p
    assert "protocol.md — 프로토콜" in p
    assert "deep-wiki" in p
    assert "사이트 조립은 하지" in p       # 그건 report-wiki build 의 일이다
    assert "(경로:줄)" in p               # 로컬 인용 규격


def test_페이지_프롬프트는_아래층이_없으면_그렇게_말한다():
    p = R.wiki_page_prompt("/r", "/root", {"file": "index.md", "title": "머리", "symbols": []}, "")
    assert "첫 장" in p
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "심볼_층 or 페이지_층 or 카탈로그 or 페이지_프롬프트 or 인용_심볼 or 모르는_심볼"
```

기대: `AttributeError: … has no attribute 'symbol_layers'` 로 7건 실패.

- [ ] **Step 3: 네 함수를 넣는다**

`run_mode1.py` 의 `nonnode_prompt` 아래에 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.symbol_layers']"/>
# 배치 계획에서 심볼마다 몇 층인지만 뽑아 표로 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.page_layers
def symbol_layers(plan):
    """`survey-plan.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다."""
    return {s["id"]: L["level"]
            for L in plan.get("layers", [])
            for b in L.get("batches", [])
            for s in b.get("symbols", [])}


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.page_layers']"/>
# 위키 페이지마다 몇 번째로 써야 하는지 층을 매긴다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def page_layers(pages, sym_layer):
    """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층.

    **왜 최대인가.** 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신
    링크할 수 있다. 가장 위층 심볼 하나가 아직 안 다뤄졌으면 그 페이지는 아직 못 쓴다.

    아는 심볼이 하나도 없으면 층0 이다 — `index.md` 처럼 개괄만 있는 장이 여기 온다.
    카탈로그가 지어낸 이름 하나로 페이지가 맨 뒤로 밀리는 일도 이 규칙이 막는다.
    """
    out = {}
    for p in pages:
        known = [sym_layer[s] for s in p.get("symbols", []) if s in sym_layer]
        out[p["file"]] = max(known) if known else 0
    return out


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.wiki_catalogue_prompt']"/>
# 위키에 어떤 장을 둘지 정하는 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def wiki_catalogue_prompt(repo, root):
    """페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다.

    K6 의 층을 매기려면 이 둘이 있어야 하는데, deep-wiki 의 페이지는 심볼도 모듈도 아닌
    **주제** 단위라 기계가 결정론으로 못 만든다. 그래서 이 한 세션만 먼저 돈다.
    """
    return """\
너는 코드베이스 위키의 **목차 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

**산문을 쓰지 마라.** 이 세션이 낼 것은 목차 파일 하나뿐이다. 각 장은 다음 세션들이 쓴다.

## 재료 — 이미 다 있다. 다시 만들지 마라

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/ranking.json     모듈 중요도(PageRank · hotspot)
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/survey-plan.json 심볼의 의존 층

## 할 일

`/deep-wiki:catalogue` 의 규정을 따라 주제 카탈로그를 짠다 —
Getting Started / Deep Dive 계열, 최대 4단, 절당 자식 8장 이하.
장 수는 모듈 수에 맞춘다. `ranking.json` 상위 모듈부터.

낼 것은 이 파일 하나다:

  {repo}/out/codegraph-raw/wiki-plan.json

```json
{{"pages": [
  {{"file": "index.md", "title": "이 저장소는 무엇인가", "symbols": []}},
  {{"file": "protocol.md", "title": "프로토콜", "symbols": ["encode", "decode"]}}
]}}
```

- `file` 은 하위 폴더 없는 평평한 이름이다. **`index.md` 를 반드시 넣는다.**
- `symbols` 는 그 장이 **본문에서 다룰** 용어 키다. `terms-db.json` 에 **실제로 있는 키만** 적는다.
  지어낸 이름은 넣지 않는다 — 기계가 이 목록으로 장의 집필 순서를 정한다.
- 개괄만 하는 장은 `symbols` 를 빈 배열로 둔다. 그 장이 맨 먼저 쓰인다.

**마크다운 페이지를 만들지 마라. 커밋하지 마라.**

보고: 장 수 · 장마다 인용 심볼 수 · terms-db 에 없어서 뺀 이름.
""".format(repo=repo, root=root)


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.wiki_page_prompt']"/>
# 위키 한 장을 맡을 세션에게 줄 글을 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: run_mode1.main
def wiki_page_prompt(repo, root, page, lower_pages):
    """장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다.

    **deep-wiki 플러그인을 고치지 않는다.** 그건 `~/.claude/plugins/cache/` 에 사는 캐시라
    업데이트에 덮인다. 대신 이 프롬프트가 감싸서 지시한다 — 지금 코드가 이미 쓰는 방식이다.
    """
    return """\
너는 코드베이스 위키의 **{fname} 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 네가 쓸 장 하나

  제목   {title}
  파일   {repo}/docs/wiki/{fname}
  다룰 것 {syms}

**이 한 장만 쓴다.** 다른 장을 만들지 않는다.

## 이미 선 장들 — 재설명하지 말고 링크한다

{lower}

## 재료

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/modules.svg      모듈 관계도(큰 그림)

## 규정

`/deep-wiki:page` 의 규정(3단계 절차 · Mermaid · 인용 규격 · 미확인 영역 표기)을 따르되
**사이트 조립은 하지 마라** — 그건 이 도구의 `report-wiki build` 가 한다. 평평한 마크다운만 쓴다.

- **인용은 로컬 규격 `(경로:줄)`** 로 쓴다. 저장소 뿌리 기준 상대 경로다. 기계가 대조한다
- Mermaid 는 소형만(노드 10개 이하). 큰 그림은 `out/codegraph-raw/modules.svg` 를 가리킨다
- 확인 못 한 것은 `(Unknown - verify in <파일>)` 로 남긴다. 지어내지 않는다
- 읽는 사람은 배경 지식이 없다고 가정한다(객체지향을 갓 배운 대학 1학년 눈높이)
- 한국어로 쓰고 영문 기술용어를 병기한다. 약어와 압축 표현을 피한다

**대상 저장소의 소스는 읽기만 한다. 쓰는 곳은 위 파일 하나뿐이다. 커밋하지 마라.**

보고: 줄 수 · 인용 수 · Mermaid 수 · Unknown 으로 남긴 자리.
""".format(repo=repo, root=root, fname=page["file"], title=page.get("title") or page["file"],
           syms=", ".join(page.get("symbols") or []) or "(개괄 — 특정 심볼 없음)",
           lower=lower_pages or "  (없음 — 네가 첫 장이다)")
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "심볼_층 or 페이지_층 or 카탈로그 or 페이지_프롬프트 or 인용_심볼 or 모르는_심볼"
```

기대: `7 passed`.

- [ ] **Step 5: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[feat] : 위키 산문도 같은 층 순서로 쓰는 프롬프트"
```

---

## Task 8: `main()` 배선 — 층을 순차로 돌고 배치를 병렬로 띄운다

**Files:**
- Modify: `codegraph/run_mode1.py` (`format_report` · `stage_totals` · `main`)
- Modify: `codegraph/test_run_mode1.py`

- [ ] **Step 1: 보고 표 시험을 먼저 쓴다**

배치가 병렬로 돌면 **행의 초를 다 더한 값은 사람이 기다린 시간이 아니다.** 층 안에서 8개가 동시에 돌았으면 합계가 벽시계의 8배까지 부푼다. 그래서 진짜 벽시계를 따로 받는 칸이 필요하다.

```python
# ── 10. 병렬이면 행의 초 합계는 벽시계가 아니다
def test_보고표는_진짜_벽시계를_따로_받는다():
    """8개가 동시에 돌면 행의 초를 더한 값이 사람이 기다린 시간의 8배가 된다.

    `wall_seconds` 를 주면 합계 줄이 그 값을 쓴다. 안 주면 예전처럼 행을 더한다 —
    `run_mode2.py` 와 `run_mode1_5.py` 가 인자 없이 부르므로 기본값이 있어야 한다.
    """
    rows = [{"stage": "survey/L0-B00", "seconds": 100.0, "ok": True,
             "usage": R.normalize_usage(None)},
            {"stage": "survey/L0-B01", "seconds": 100.0, "ok": True,
             "usage": R.normalize_usage(None)}]
    assert "3분 20.0초" in R.format_report(rows)              # 100+100, 예전 방식
    assert "1분 45.0초" in R.format_report(rows, wall_seconds=105.0)


def test_단계별_소계를_낸다():
    """어느 단계가 비쌌는지 보려면 배치 행을 단계로 접어야 한다.
    `ARCHITECTURE.md` 의 표와 대조할 수 있는 모양이 이것이다."""
    rows = [
        {"stage": "prep", "seconds": 1.0, "usage": R.normalize_usage(None), "ok": True},
        {"stage": "survey/L0-B00", "seconds": 10.0, "ok": True,
         "usage": R.normalize_usage({"usage": {"output_tokens": 5}, "num_turns": 2})},
        {"stage": "survey/L1-B00", "seconds": 20.0, "ok": True,
         "usage": R.normalize_usage({"usage": {"output_tokens": 7}, "num_turns": 3})},
    ]
    got = R.stage_totals(rows)
    assert got["survey"]["total"] == 12 and got["survey"]["turns"] == 5
    assert got["prep"]["total"] == 0
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "벽시계 or 단계별_소계"
```

기대: `TypeError: format_report() got an unexpected keyword argument 'wall_seconds'` 와 `AttributeError: … 'stage_totals'`.

- [ ] **Step 3: `format_report` 에 칸을 더하고 `stage_totals` 를 넣는다**

`run_mode1.py:287-288` 의 시그니처와 합계 줄을 고친다. **인자를 빼거나 뜻을 바꾸지 않는다** — `run_mode2.py:75` 가 `format_report = M.format_report` 로 그대로 물려받고 `test_run_mode2.py:237` 이 동일성을 단언한다.

```python
def format_report(rows, wall_seconds=None):
    """단계별 표 + 합계 줄. 이 실행기의 **산출물 본체**다.

    `wall_seconds` 는 **병렬 때문에** 생겼다. 층 안에서 배치 8개가 동시에 돌면
    행의 초를 더한 값이 사람이 기다린 시간의 8배까지 부푼다. 진짜 벽시계를 부르는 쪽이
    재서 넘긴다. 안 넘기면 예전처럼 행을 더한다 — Mode 1.5 와 Mode 2 는 병렬이 아니라 그게 맞다.
    """
```

합계 줄(`run_mode1.py:302-307`)의 시간 칸만 바꾼다:

```python
    tot = sum_usage([r["usage"] for r in rows])
    total_seconds = (sum(float(r["seconds"]) for r in rows)
                     if wall_seconds is None else float(wall_seconds))
    body.append([
        "합계", "", _hms(total_seconds),
        "{:,}".format(tot["input"]), "{:,}".format(tot["output"]),
        "{:,}".format(tot["cache_read"]), "{:,}".format(tot["cache_write"]),
        "{:,}".format(tot["total"]), str(tot["turns"]), "%.4f" % tot["cost_usd"],
    ])
```

그 아래에 새 함수를 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.stage_totals']"/>
# 배치 행들을 단계 단위로 접어 소계를 낸다.
# 쓰는 것: run_mode1.sum_usage · 쓰이는 곳: run_mode1.main
def stage_totals(rows):
    """`survey/L0-B00` 같은 행을 `survey` 로 접는다. `{단계: 합친 usage}`.

    배치가 스물이 넘으면 표를 눈으로 훑어 "어느 단계가 비쌌나" 를 못 본다.
    `ARCHITECTURE.md` 의 다섯 줄짜리 표와 대조할 수 있는 모양이 이것이다.
    """
    byname = collections.OrderedDict()
    for r in rows:
        name = r["stage"].split("/")[0]
        byname.setdefault(name, []).append(r["usage"])
    return collections.OrderedDict((k, sum_usage(v)) for k, v in byname.items())
```

`run_mode1.py` 의 import 절에 한 줄을 더한다:

```python
import collections
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

```bash
.venv/bin/python -m pytest codegraph/test_run_mode1.py -q -k "벽시계 or 단계별_소계"
.venv/bin/python -m pytest codegraph/test_run_mode2.py codegraph/test_run_mode1_5.py -q
```

기대: 앞이 `2 passed`, 뒤가 전부 통과(기본값 덕분에 부르는 쪽이 안 깨진다).

- [ ] **Step 5: `main()` 의 단계 루프를 갈아 끼운다**

`run_mode1.py:428-455` 의 `for stage in stages:` 루프를 아래로 바꾼다. `survey` 와 `wiki` 를 각각 도우미 함수로 빼서 `main` 이 부풀지 않게 한다.

먼저 도우미 둘을 `main` 위에 넣는다:

```python
# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_survey']"/>
# 전수조사를 층 오름차순으로 돌리고 층마다 샤드를 합친다.
# 쓰는 것: run_mode1.run_layer, run_mode1.merge_shards, run_mode1.survey_batch_prompt, run_mode1.nonnode_prompt, run_mode1.dep_excerpt · 쓰이는 곳: run_mode1.main
def run_survey(model, repo, root, plan, concurrency, timeout, reading_path):
    """층 사이는 순차, 층 안은 병렬(K2). `[(행 라벨, 초, 종료코드, 결과), …]` 를 낸다.

    **층이 끝날 때마다 병합해서 디스크에 쓴다.** 다음 층의 배치가 아래층 레코드를 발췌해
    받아야 하고, 중간에 죽어도 거기까지는 남아야 한다.

    **샤드가 이미 있는 배치는 건너뛴다(J4).** 재시도 구조를 만들지 않고도 `--only survey` 로
    다시 돌리면 실패한 배치만 다시 돈다.
    """
    shard_dir = os.path.join(repo, "out", "codegraph-raw", "_shards")
    os.makedirs(shard_dir, exist_ok=True)
    merged = {}
    if os.path.exists(reading_path):
        with open(reading_path, encoding="utf-8") as f:
            merged = json.load(f)

    rows = []
    for L in plan["layers"]:
        if L.get("kind") == "non-node":
            jobs = [("NONNODE", nonnode_prompt(repo, root))]
            label_of = {"NONNODE": "survey/L%d-비노드" % L["level"]}
        else:
            jobs, label_of = [], {}
            for b in L["batches"]:
                jobs.append((b["id"], survey_batch_prompt(repo, root, b, dep_excerpt(merged, b))))
                label_of[b["id"]] = "survey/" + b["id"]
        jobs = [(bid, p) for bid, p in jobs
                if not os.path.exists(os.path.join(shard_dir, bid + ".json"))]
        if not jobs:
            print("  층%d — 샤드가 이미 다 있다. 건너뛴다." % L["level"], flush=True)
            continue

        print("  층%d — 배치 %d개를 동시 %d 로 돌린다"
              % (L["level"], len(jobs), concurrency), flush=True)
        with _Heartbeat("survey 층%d" % L["level"]):
            got = run_layer(model, repo, root, jobs, concurrency, timeout)
        for bid, seconds, rc, result in got:
            ok, why = agent_verdict(rc, result)
            rows.append({"stage": label_of[bid], "seconds": seconds,
                         "usage": normalize_usage(result), "ok": ok, "why": why})

        merged = merge_shards(shard_dir, merged)
        os.makedirs(os.path.dirname(reading_path), exist_ok=True)
        with open(reading_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("  층%d 끝 — 레코드 %d개" % (L["level"], len(merged)), flush=True)
        if not all(r["ok"] for r in rows):
            print("층%d 에 실패한 배치가 있다. 다음 층으로 가지 않는다 — "
                  "아래층이 비면 위층이 추론으로 메운다." % L["level"], file=sys.stderr)
            break
    return rows


# <include file="docs/codegraph/comments.xml" path="//term[@id='run_mode1.run_wiki']"/>
# 위키 목차를 받고 장들을 층 오름차순으로 쓰게 한다.
# 쓰는 것: run_mode1.run_layer, run_mode1.wiki_catalogue_prompt, run_mode1.wiki_page_prompt, run_mode1.page_layers, run_mode1.symbol_layers · 쓰이는 곳: run_mode1.main
def run_wiki(model, repo, root, plan, concurrency, timeout):
    """카탈로그 한 세션(J3) -> 장들을 층 오름차순 병렬(K6).

    목차를 기계가 못 만드는 이유는 deep-wiki 의 장이 심볼도 모듈도 아닌 **주제** 단위라서다.
    그래서 이 한 세션만 먼저 돈다.
    """
    raw = os.path.join(repo, "out", "codegraph-raw")
    wiki_plan_path = os.path.join(raw, "wiki-plan.json")
    rows = []

    if not os.path.exists(wiki_plan_path):
        with _Heartbeat("wiki 목차"):
            got = run_layer(model, repo, root,
                            [("catalogue", wiki_catalogue_prompt(repo, root))], 1, timeout)
        bid, seconds, rc, result = got[0]
        ok, why = agent_verdict(rc, result)
        rows.append({"stage": "wiki/목차", "seconds": seconds,
                     "usage": normalize_usage(result), "ok": ok, "why": why})
        if not ok:
            return rows
    if not os.path.exists(wiki_plan_path):
        rows.append({"stage": "wiki/목차", "seconds": 0.0, "usage": normalize_usage(None),
                     "ok": False, "why": "wiki-plan.json 이 나오지 않았다"})
        return rows

    with open(wiki_plan_path, encoding="utf-8") as f:
        pages = json.load(f)["pages"]
    lv = page_layers(pages, symbol_layers(plan))
    done = []
    for k in sorted(set(lv.values())):
        here = [p for p in pages if lv[p["file"]] == k
                and not os.path.exists(os.path.join(repo, "docs", "wiki", p["file"]))]
        if not here:
            continue
        lower = "\n".join("  - %s — %s" % (p["file"], p.get("title") or p["file"])
                          for p in done)
        jobs = [(p["file"], wiki_page_prompt(repo, root, p, lower)) for p in here]
        print("  층%d — 장 %d개를 동시 %d 로 쓴다" % (k, len(jobs), concurrency), flush=True)
        with _Heartbeat("wiki 층%d" % k):
            got = run_layer(model, repo, root, jobs, concurrency, timeout)
        for fname, seconds, rc, result in got:
            ok, why = agent_verdict(rc, result)
            rows.append({"stage": "wiki/" + fname, "seconds": seconds,
                         "usage": normalize_usage(result), "ok": ok, "why": why})
        done += here
        if not all(r["ok"] for r in rows):
            print("층%d 에 실패한 장이 있다. 다음 층으로 가지 않는다." % k, file=sys.stderr)
            break
    return rows
```

그리고 `main` 의 루프를 이렇게 바꾼다:

```python
    rows, t_all = [], time.monotonic()
    survey_plan_path = os.path.join(raw, "survey-plan.json")
    plan_json = None
    for stage in stages:
        print("\n── %s ──────────────────────────────" % stage, flush=True)
        t0 = time.monotonic()
        if stage in AGENT_STAGES:
            if plan_json is None:
                if not os.path.exists(codegraph):
                    print("에러 — 코드 지도가 없다: %s (prep 이 먼저다)" % codegraph,
                          file=sys.stderr)
                    return 1
                with open(codegraph, encoding="utf-8") as f:
                    plan_json = survey_plan.plan(json.load(f), a.target)
                with open(survey_plan_path, "w", encoding="utf-8") as f:
                    json.dump(plan_json, f, ensure_ascii=False, indent=1)
                print("배치 계획 %s" % survey_plan_path, flush=True)
            if stage == "survey":
                got = run_survey(a.model, repo, ROOT, plan_json,
                                 a.concurrency, a.timeout, reading)
            else:
                got = run_wiki(a.model, repo, ROOT, plan_json, a.concurrency, a.timeout)
            rows += got
            ok = bool(got) and all(r["ok"] for r in got)
            print("%s — %s (%s · 세션 %d개)"
                  % (stage, "성공" if ok else "실패", _hms(time.monotonic() - t0), len(got)),
                  flush=True)
        else:
            if stage == "terms":
                # 없는 파일은 넘기지 않는다 — terms_argv 는 순수 함수라 존재를 모른다
                cmd = terms_argv(sys.executable, ROOT, repo,
                                 codegraph if os.path.exists(codegraph) else None,
                                 reading if os.path.exists(reading) else None)
            else:
                cmd = node_argv(ROOT, stage + ".mjs", repo)
            rc = run_machine(cmd, stage)
            ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
            seconds = time.monotonic() - t0
            rows.append({"stage": stage, "seconds": seconds,
                         "usage": normalize_usage(None), "ok": ok, "why": why})
            print("%s — %s (%s)" % (stage, "성공" if ok else "실패", _hms(seconds)), flush=True)
        if not all(r["ok"] for r in rows):
            print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            break

    wall = time.monotonic() - t_all
    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % _hms(wall))
    print("=" * 72)
    print(format_report(rows, wall_seconds=wall))
    print("\n단계 소계 — 병렬이라 행의 초 합계는 벽시계가 아니다")
    for name, u in stage_totals(rows).items():
        print("  %-8s 토큰 %12s · 턴 %3d · 비용 $%.4f"
              % (name, "{:,}".format(u["total"]), u["turns"], u["cost_usd"]))

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": a.model, "stages": rows,
                       "stage_totals": stage_totals(rows),
                       "concurrency": a.concurrency, "target": a.target,
                       "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": wall},
                      f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % a.json_out)

    return 0 if all(r["ok"] for r in rows) else 1
```

`main` 의 인자 선언에 둘을 더하고 **`--model` 의 기본값을 바꾼다**(`run_mode1.py:391` 근처):

```python
    # 🔴 서브에이전트 모델은 Claude Sonnet 5 다. 별명(`sonnet`)이 아니라 정확한 ID 를 적는다 —
    #    별명은 최신판을 따라 움직여 측정이 흔들린다. 예전 기본값은 `opus` 였다.
    ap.add_argument("--model", default="claude-sonnet-5",
                    help="배치·장 세션이 쓸 모형 (기본: claude-sonnet-5)")
    ap.add_argument("--concurrency", type=int, default=8,
                    help="한 층에서 동시에 띄울 세션 수 (기본 8 = K4)")
    ap.add_argument("--target", type=int, default=8,
                    help="배치당 목표 심볼 수 (기본 8 = K3)")
```

⚠ `--model` 은 **이미 있는 인자**다(`:391`). 새로 더하지 말고 **기본값만** `opus` 에서
`claude-sonnet-5` 로 바꾼다. 두 번 선언하면 `argparse` 가 터진다.

그리고 파일 맨 위 import 에 한 줄:

```python
import survey_plan
```

⚠ `run_mode1.py` 는 `codegraph/` 안에 있고 `sys.path` 에 자기 폴더가 없을 수 있다. `import survey_plan` 앞에 `sys.path` 를 세운다 — `run_mode2.py:68` 이 이미 쓰는 방식을 그대로 본뜬다:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import survey_plan  # noqa: E402
```

- [ ] **Step 6: dry-run 으로 단계 목록을 확인한다**

```bash
.venv/bin/python codegraph/run_mode1.py . --dry-run
```

기대: `모형 claude-sonnet-5 · 단계 prep -> survey -> terms -> wiki -> build -> check` 가 찍힌다.
**모형이 `opus` 로 나오면 기본값을 안 바꾼 것이다.** (이 저장소는 `docs/codegraph/terms-reading.json` 이 있으므로 실제로는 `survey` 가 빠진 목록이 나올 수 있다 — 그때는 `--skip` 없이 빈 임시 폴더로 확인한다:)

```bash
mkdir -p /tmp/빈저장소 && .venv/bin/python codegraph/run_mode1.py /tmp/빈저장소 --dry-run
```

기대: 여섯 단계가 모두 나온다.

- [ ] **Step 7: 전체 시험을 돌린다**

```bash
.venv/bin/python -m pytest codegraph/ -q
```

기대: 실패 0. 통과 수가 **201 + (더한 시험 수)** 로 늘어야 한다. **줄어들면 무언가를 조용히 깬 것이다.**

- [ ] **Step 8: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/test_run_mode1.py
git commit -m "[feat] : mode 1 실행기가 층을 순차로 배치를 병렬로 돌린다"
```

---

## Task 9: 코드·문서·레코드를 어긋나지 않게 맞춘다

**왜 한 Task 인가.** 저장소 규약상 새 함수를 만들면 그 자리에서 레코드를 쓰고 `xmldoc` 로 주석 블록을 박아야 한다. 그리고 **뒤집은 잠긴 결정은 세 곳에 적어야 한다** — 코드 docstring · 갈아 낀 테스트의 docstring(Task 3·6 에서 이미 했다) · `codegraph/CLAUDE.md`.

**Files:**
- Modify: `codegraph/run_mode1.py:13-28` (모듈 docstring)
- Modify: `codegraph/CLAUDE.md`
- Modify: `ARCHITECTURE.md`
- Modify: `docs/codegraph/terms-reading.json` · `docs/codegraph/comments.xml`

- [ ] **Step 1: `run_mode1.py` 의 모듈 docstring 을 고친다**

`:13-28` 의 다섯 단계 그림과 "에이전트를 하나로 묶은 것이 이 설계의 급소다" 문단을 바꾼다:

```
## 여섯 단계 — LLM 이 도는 칸은 **둘**이다

    prep ──▶ survey ──▶ terms ──▶ wiki ──▶ build ──▶ check
    기계     LLM 층별     기계     LLM 층별   기계      기계

| 단계 | 무엇 | 부르는 것 |
|---|---|---|
| `prep`   | 정적 계층. clang-uml/clang-doc 또는 roslyn-dump 를 돌려 코드 지도를 만든다 | `scripts/wiki/prep.mjs` |
| `survey` | 전수조사. **의존 위상 층 오름차순 · 층 안 병렬** | `claude -p` 배치마다 1회 |
| `terms`  | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `codegraph/terms_db.py` |
| `wiki`   | 위키 산문. 목차 1회 + 장마다 1회, 같은 층 순서 | `claude -p` 장마다 1회 |
| `build`  | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `scripts/wiki/build.mjs` |
| `check`  | 산문의 인용을 저장소 실물과 대조한다 | `scripts/wiki/check.mjs` |

**⚠ 이 파일의 이전 판은 "에이전트를 하나로 묶은 것이 이 설계의 급소다" 라고 적었다.**
이유는 캐시였다 — 세션을 쪼개면 두 번째가 저장소를 처음부터 다시 읽어 토큰이 부풀고,
측정값이 파이프라인 비용이 아니라 세션 수의 함수가 된다.
**2026-08-30 사용자가 그 결정을 뒤집었다.** 심볼의 뜻은 그것이 의존하는 심볼의 뜻 위에 서므로
아무 순서로나 읽으면 아직 안 읽은 것을 가리키게 되고 그 자리가 추론으로 메워진다.
그래서 **의존 대상이 없는 것부터** 한 겹씩 올라가고(K1), 같은 층은 서로 의존하지 않으므로
병렬로 읽는다(K2 · K4).

**비용은 아직 재지 않았다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 훨씬 적다.
어느 쪽이 큰지는 **모른다.** 이 파일 자신이 재는 도구이므로 A/B 를 돌려 숫자로 답한다.
그 전에는 "더 싸졌다" "더 빨라졌다" 를 쓰지 않는다.

`terms` 가 `survey` 와 `wiki` 사이로 온 이유 — 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다. 예전에는 산문이 검사 전 레코드를 봤다.
```

`## 쓰는 법` 절의 예시도 고친다:

```
    .venv/bin/python codegraph/run_mode1.py <저장소> [--model opus] [--only prep,check]
                                            [--skip wiki] [--concurrency 8] [--target 8]
                                            [--json 측정.json] [--dry-run]
```

- [ ] **Step 2: `codegraph/CLAUDE.md` 의 같은 주장을 고친다**

"세 실행기 — 재는 것이 목적이다" 절의 파이프라인 그림에서 Mode 1 줄을 바꾼다:

```
Mode 1    prep ─▶ survey ─▶ terms ─▶ wiki ─▶ build ─▶ check
```

그 아래 "무엇이 여기 있나" 표에 두 줄을 보탠다:

```
| `survey_plan.py` | 코드 지도를 의존 위상 층과 배치로 나눈다. **판정하지 않는다** |
| `file_cache.py` | 층 경계에서 같은 파일을 다시 통독하지 않도록 개요를 디스크에 남긴다 |
```

그리고 새 절을 붙인다:

```markdown
## Bottom-Up 층 병렬 — 2026-08-30 에 뒤집힌 결정

이 문서의 이전 판과 `run_mode1.py` 는 **"에이전트를 하나로 묶은 것이 이 설계의 급소"** 라고
적고 있었다. 이유는 캐시였다. **사용자가 2026-08-30 에 그 결정을 뒤집었다.**

| # | 결정 |
|---|---|
| K1 | 정렬 축은 **위상 깊이** (out_deg 가 아니다 — 🔵 실측에서 out_deg 1 무리 안에 깊이 1·2·3·4 가 섞여 있었다) |
| K2 | 층 안은 병렬, 층 사이는 순차 |
| K3 · K4 | 배치는 8심볼, 한 층에 동시 8배치 |
| K5 | 비노드 용어(file · module · artifact · key · concept)는 맨 마지막 별도 층 |
| K6 | 위키도 같은 층 순서. 페이지의 층 = 인용하는 심볼의 최대 층 |
| K7 | 고립 노드는 층0 |

**비용은 아직 재지 않았다.** 쪼개면 캐시가 나빠지는 대신 배치마다 읽는 양이 크게 준다.
어느 쪽이 큰지 **모른다** — `--json` 으로 A/B 를 돌려 `evals/runs/` 에 쌓고 대조한다.

🔵 2026-08-30 이 저장소 실측 — 1차 노드 167개의 층 분포는 **0:110 · 1:32 · 2:16 · 3:7 · 4:2**,
순환 0개, 고립 노드 42개. 층 경계 중복 통독은 유일 파일 41개에 층별 합계 84개(**중복 43회**)다.
```

- [ ] **Step 3: `ARCHITECTURE.md` 의 Mode 1 그림을 고친다**

`ARCHITECTURE.md:155-166` 의 **실측 표는 건드리지 않는다** — 그건 옛 다섯 단계로 잰 값이고, 새 값은 A/B 를 돌린 뒤에 붙는다. 대신 그 표 **아래**에 한 문단을 더한다:

```markdown
⚠ **위 표는 옛 다섯 단계(`prep agent terms build check`)로 잰 값이다.** 2026-08-30 에
`agent` 가 `survey` 와 `wiki` 로 갈리고 층 병렬이 됐다(`codegraph/CLAUDE.md` 의 K1~K7).
**새 구조의 값은 아직 재지 않았다.** 재면 `evals/runs/` 에 쌓고 이 표를 갱신한다.
```

그리고 `ARCHITECTURE.md` 안의 Mode 1 파이프라인 그림들(mermaid 포함)에서 `agent` 한 칸을 `survey … terms … wiki` 로 고친다. 어디에 있는지는 이렇게 찾는다:

```bash
grep -n "prep.*agent.*terms\|agent" ARCHITECTURE.md
```

- [ ] **Step 4: 새 함수의 레코드를 쓰고 주석 블록을 박는다**

`docs/codegraph/terms-reading.json` 에서 **지운 것을 지우고**:

```bash
.venv/bin/python - <<'PY'
import json
p = "docs/codegraph/terms-reading.json"
d = json.load(open(p, encoding="utf-8"))
for k in ["run_mode1.agent_prompt", "run_mode1.run_agent"]:
    d.pop(k, None)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("남은 레코드", len(d))
PY
```

**새로 만든 것 15개의 레코드를 손으로 쓴다.** 계약은 `{kind, module, where, means, does, uses[], confidence, source}` 이고 `where` 는 실제 `파일:줄` 이다. 대상:

`codegraph/survey_plan.py` · `survey_plan.layer_of` · `survey_plan.pack` · `survey_plan.plan` · `codegraph/file_cache.py` · `file_cache._paths` · `file_cache.get` · `file_cache.put` · `run_mode1.run_agent_with` · `run_mode1.run_layer` · `run_mode1.merge_shards` · `run_mode1._qualified` · `run_mode1.dep_excerpt` · `run_mode1.survey_batch_prompt` · `run_mode1.nonnode_prompt` · `run_mode1.symbol_layers` · `run_mode1.page_layers` · `run_mode1.wiki_catalogue_prompt` · `run_mode1.wiki_page_prompt` · `run_mode1.stage_totals` · `run_mode1.run_survey` · `run_mode1.run_wiki`

보기 하나:

```json
"survey_plan.plan": {
 "kind": "function", "module": "codegraph", "where": "codegraph/survey_plan.py:212",
 "means": "코드 지도를 층과 배치로 나눈 계획을 만드는 함수.",
 "does": "external 을 빼고 위상 깊이를 매긴 뒤 같은 파일이 쪼개지지 않게 배치로 묶는다. 증분 재조사면 층은 전체 기준으로 매긴 뒤 거른다 — 거르고 나서 매기면 사라진 의존 대상 때문에 층이 잘못 내려간다.",
 "uses": [
  {"to": "survey_plan.layer_of", "kind": "dependency", "label": "calls", "where": "codegraph/survey_plan.py:222"},
  {"to": "survey_plan.pack", "kind": "dependency", "label": "calls", "where": "codegraph/survey_plan.py:236"}
 ],
 "confidence": "HIGH", "source": "reading"
}
```

- [ ] **Step 5: 마커를 맞춘다**

```bash
.venv/bin/python codegraph/xmldoc.py emit
.venv/bin/python codegraph/xmldoc.py inject
.venv/bin/python codegraph/xmldoc.py check
```

기대: `check` 가 **문제 0건**. 걸리면 `where` 의 줄 번호나 `<include>` 마커의 `@id` 가 레코드 키와 다른 것이다.

- [ ] **Step 6: 인용 검사를 돌린다**

```bash
.venv/bin/python codegraph/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading docs/codegraph/terms-reading.json
```

기대: 마지막 줄이 **실패 0**. "근거 없음" 은 경고이지 실패가 아니다.

- [ ] **Step 7: 커밋**

```bash
git add codegraph/run_mode1.py codegraph/CLAUDE.md ARCHITECTURE.md \
        docs/codegraph/terms-reading.json docs/codegraph/comments.xml
git commit -m "[docs] : 층 병렬로 뒤집힌 결정을 코드 문서 레코드 세 곳에 적는다"
```

---

## Task 10: 전수조사 스킬을 절차의 정본으로 고친다

`.claude/skills/codebase-terms-survey` 는 `.agents/skills/codebase-terms-survey` 로 가는 **심볼릭 링크**다(🔵 `ls -la .claude/skills/` 로 확인). **원본만 고친다.**

**Files:**
- Modify: `.agents/skills/codebase-terms-survey/SKILL.md`

- [ ] **Step 1: Workflow 5단계를 갈아 끼운다**

`SKILL.md:105` 의 `5. **레코드를 쓴다** — 파일 순서, 파일 안은 줄 순서.` 를 아래로 바꾸고, 기존 6·7·8 단계는 번호만 8·9·10 으로 민다. `## Workflow — 8단계` 라는 제목도 `## Workflow — 10단계` 로 고친다.

```markdown
5. **배치 계획을 만든다** — `python codegraph/survey_plan.py <codegraph.json> --target 8`
   → `survey-plan.json`. 층0(의존 대상이 없는 것)부터 층이 오른다.
   재료는 조사 **이전에** 있다 — `report-wiki prep` 이 정적 수집기로 코드 지도를 먼저 낸다.
   수집기가 없는 저장소는 `prep` 이 막히므로 애초에 Mode 1 대상이 아니다. 그때는 함께 막고 보고한다.
   증분 재조사면 `warmup.py blast` 의 파일 목록을 `--only-files` 로 준다.
6. **레코드를 쓴다 — 층 오름차순, 층 안은 병렬.**
   - 층 사이는 **순차**. 층 k 는 층 <k 가 전부 끝나고 병합된 뒤 시작한다.
   - 층 안은 **배치 8개까지 동시**. 같은 층끼리는 서로 의존하지 않으므로 안전하다.
   - 배치는 자기 샤드 `<repo>/out/codegraph-raw/_shards/L{층}-B{번호}.json` 에만 쓴다.
     **terms-reading.json 을 직접 고치지 않는다** — 동시에 여러 배치가 돌기 때문이다.
   - 층이 끝나면 오케스트레이터(`run_mode1.py` 의 `merge_shards`)가 샤드를 병합한다.
     **키 충돌 해소는 거기서만 한다** — 배치는 자기 것만 보므로 `main` 이 9파일에 있다는 것을 모른다.
   - 층 k 배치에는 **자기 심볼이 의존하는 아래층 레코드만** 발췌해 준다. 전량 주입은 낭비다.
   - 같은 파일을 층마다 다시 열지 않도록 `file_cache.py` 를 쓴다. 다만 **자기 심볼은 캐시로
     때우지 않는다** — 캐시만 보고 쓰면 `confidence` 가 HIGH 일 근거가 없다.
7. **비노드 용어는 맨 마지막 층** — file · module · artifact · key · concept.
   심볼이 전부 읽힌 뒤라야 파일 레코드가 그 안 심볼들의 완성 레코드를 재료로 쓸 수 있다.
```

- [ ] **Step 2: `## 산출물` 표에 두 줄을 보탠다**

```markdown
| `<repo>/out/codegraph-raw/survey-plan.json` | `survey_plan.py` | 층·배치 계획. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/_filecache/*.json` | 배치 세션 | 통독 캐시. gitignore, 재생성 |
| `<repo>/out/codegraph-raw/_shards/*.json` | 배치 세션 | 배치별 레코드 조각. gitignore, 재생성 |
```

- [ ] **Step 3: `## Common pitfalls` 에 세 줄을 보탠다**

```markdown
- **out_deg 로 정렬** — 그건 위상 깊이가 아니다. 🔵 실측에서 out_deg 1 무리 안에 깊이 1·2·3·4 가
  섞여 있었다. out_deg 로 나누면 아직 안 읽은 것을 가리키게 된다
- **층 경계에서 같은 파일을 다시 통독** — 🔵 유일 파일 41개인데 층별 합계 84개다. `file_cache.py` 를 쓴다
- **배치가 terms-reading.json 을 직접 고침** — 동시 쓰기로 서로를 지운다. 샤드에만 쓴다
```

- [ ] **Step 4: 새 절 하나를 붙인다**

```markdown
## deep-wiki 산문도 같은 층 순서로 (K6)

위키 페이지는 심볼도 모듈도 아닌 **주제** 단위다(Getting Started / Deep Dive, 최대 4단, 절당 ≤8장).
그래서 **페이지의 층 = 그 페이지가 인용하는 심볼들의 최대 층**으로 매긴다.
왜 최대인가 — 페이지는 자기가 다루는 모든 개념이 이미 설명된 뒤라야 재설명 대신 링크할 수 있다.

목차는 기계가 만들지 못한다(주제 단위라서). 그래서 `wiki` 단계는 **목차 세션 1개**로 시작해
`wiki-plan.json` 을 받고, 거기 적힌 페이지별 인용 심볼로 층을 매긴 뒤 장을 층 순서로 쓴다.

**deep-wiki 플러그인 파일을 고치지 않는다.** `~/.claude/plugins/cache/` 에 사는 캐시라 업데이트에
덮인다. 우리 프롬프트(`run_mode1.py` 의 `wiki_page_prompt`)가 감싸서 지시한다.
```

- [ ] **Step 5: 심볼릭 링크가 여전히 링크인지 확인한다**

```bash
ls -la .claude/skills/codebase-terms-survey
```

기대: `... -> ../../.agents/skills/codebase-terms-survey` 로 나온다. 실제 파일이 됐으면 원본이 아니라 사본을 고친 것이다 — 되돌린다.

- [ ] **Step 6: 커밋**

```bash
git add .agents/skills/codebase-terms-survey/SKILL.md
git commit -m "[docs] : 전수조사 스킬에 층 순서와 병렬 배치 절차"
```

---

## Task 11: 게이트 전부 — 하네스가 실제로 서는지 확인한다

**이 Task 는 코드를 고치지 않는다.** 앞선 열 Task 가 서로를 깨지 않았는지 한 번에 본다.

**Files:** 없음 (검증만)

- [ ] **Step 1: 파이썬 시험 전량**

```bash
cd /Users/escatrgot/LLM-Tools/report-builder
.venv/bin/python -m pytest codegraph/ -q 2>&1 | tail -3
```

기대: 실패 0. 🔵 기준선은 골든 변수 없이 **201 통과 · 19 건너뜀**이다. 통과 수는 더한 만큼 늘어야 한다 — **줄어들면 무언가를 조용히 깬 것이다.**

- [ ] **Step 2: Node 쪽이 그대로인지**

```bash
npm test 2>&1 | tail -5
```

기대: 통과 수가 **바뀌지 않는다**(145개). 이 계획은 `scripts/` 와 `src/` 를 건드리지 않았다. 숫자가 움직였으면 건드리면 안 될 것을 건드린 것이다.

- [ ] **Step 3: 층 계획의 결정론과 층 안 중복 0**

```bash
.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p1.json
.venv/bin/python codegraph/survey_plan.py out/codegraph-raw/codegraph.json -o /tmp/p2.json
diff /tmp/p1.json /tmp/p2.json && echo "결정론 OK"
.venv/bin/python -c "
import json, collections
p = json.load(open('/tmp/p1.json'))
for L in p['layers']:
    c = collections.Counter(f for b in L.get('batches', []) for f in b['files'])
    print(L['level'], '중복', [f for f, n in c.items() if n > 1] or '없음')"
```

기대: `결정론 OK` + 모든 층 `중복 없음`.

- [ ] **Step 4: 단계 목록**

```bash
mkdir -p /tmp/빈저장소 && .venv/bin/python codegraph/run_mode1.py /tmp/빈저장소 --dry-run
```

기대: `단계 prep -> survey -> terms -> wiki -> build -> check`.

- [ ] **Step 5: 마커와 인용**

```bash
.venv/bin/python codegraph/xmldoc.py check
.venv/bin/python codegraph/terms_db.py out/codegraph-raw/codegraph.json \
  --repo . --reading docs/codegraph/terms-reading.json 2>&1 | tail -5
```

기대: `check` 는 문제 0건, `terms_db` 는 실패 0.

- [ ] **Step 6: 건드리면 안 될 것을 안 건드렸는지**

```bash
git diff --name-only 9223143..HEAD | sort
```

기대 목록에 **없어야** 하는 것 — `scripts/wiki/*` · `codegraph/{normalize,facts,render_modules,clang_doc,terms_db,demermaid,verify_citations}.py` · `src/*` · `scripts/{build,check}.mjs` · `~/.claude/plugins/` 아래 무엇이든.

```bash
git status --short
```

기대: 깨끗하거나, 계획서 자신과 `out/`(gitignore) 뿐.

- [ ] **Step 7: 커밋 (필요하면)**

Step 1~6 에서 고칠 것이 나왔으면 고치고 커밋한다. 아무것도 안 나왔으면 커밋할 것이 없다.

---

## 이 계획이 끝난 뒤 — 계획 밖의 후속 작업

**하네스가 서면 그다음은 A/B 실측이다.** 이 계획은 거기까지 덮지 않는다 — 27분·$15 짜리 실행은 계획서가 시킬 일이 아니라 사람이 판단해 돌릴 일이다.

`done` 조건(`ARCHITECTURE.md:155-166` 의 `agent` 타이머가 줄었는지)은 그때 닫힌다. 돌릴 때 필요한 것만 적어 둔다:

- 대상은 **QtVisionEdit** 이어야 한다. 기준선 `evals/runs/2026-08-30-mode1-qtvisionedit-cold-opus.json` 이 그 저장소에서 나왔고, `evals/README.md` 가 **"같은 조건이 아니면 대조하지 않는다"** 고 못 박는다.
- **백지에서 시작해야 냉시동끼리 비교가 된다.** 그 저장소에는 산출물이 `0b73e03` 로 이미 커밋돼 있으므로 `git worktree` 로 따로 떼어 `docs/codegraph/` · `docs/wiki/` · `out/` 을 비운 뒤 돌린다. 원본 체크아웃을 건드리지 않는다.
- 기록은 `evals/runs/$(date +%F)-mode1-qtvisionedit-layered-opus.json` 으로 `--json` 을 준다. `evals/README.md` 의 표에도 한 줄 보탠다.
- **판정은 벽시계만이다(K8).** 토큰·비용은 기록하되 판정에 넣지 않는다.
- 🔵 이번 세션 실측 — 그 저장소의 층 구조는 층0 에 84%가 몰려 있고 층1~4 는 배치가 1개씩이다. **임계 경로가 최소 7 세션 깊이**라 병렬 이득이 크지 않을 수 있다. 결과가 나쁘면 `--target` 과 `--concurrency` 를 조절해 재측정하고, **그래도 나쁘면 그 숫자를 그대로 보고한다.**

---

## Self-Review — 계획을 사양과 대조한 결과

| 사양(`docs/handoffs/PROMPT-2026-08-30-bottomup-survey-harness.md`) | 덮은 Task |
|---|---|
| STEP 1 `survey_plan.py` | Task 1 |
| STEP 2 `file_cache.py` | Task 2 (+ 사양에 없던 시험 파일을 더했다) |
| STEP 3-1 상단 상수 · 3-2 `plan_stages` | Task 3 |
| STEP 3-3 프롬프트 세 함수 | Task 6(전수조사 둘) · Task 7(위키 둘 + 층 매기기) |
| STEP 3-4 `run_layer` · `run_agent_with` · `--concurrency` · 보고 행 | Task 4 · Task 8 |
| STEP 3-5 `merge_shards` | Task 5 |
| STEP 3-6 모듈 docstring | Task 9 |
| STEP 4 테스트 갈아 끼우기 | Task 3 · Task 6 (+ Task 4·5·7·8 의 새 시험) |
| STEP 5 `test_survey_plan.py` | Task 1 |
| STEP 6 `SKILL.md` | Task 10 |
| VERIFY 절 | Task 11 |

**사양과 어긋나게 정한 것 5건은 위 "계획서를 쓰면서 내린 판단" 표(J1~J5)에 이유와 함께 있다.** 사용자가 뒤집으면 해당 Task 의 해당 Step 만 고치면 된다.

**사양에 있었으나 이 계획이 뺀 것 1건** — `agent_prompt` 를 "얇은 껍질로 남긴다"(STEP 3-4 의 권고). `git grep` 으로 아무도 안 부르는 것을 확인해 지우기로 했다(J2). 남기면 죽은 코드다.

**사양에 없어서 계획이 채운 것 2건** — `wiki` 목차 세션(J3, K6 을 실행 가능하게 만드는 데 필요하다)과 `format_report(wall_seconds=)`(병렬이면 행의 초 합계가 벽시계가 아니다).
