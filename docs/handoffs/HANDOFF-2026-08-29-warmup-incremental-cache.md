# HANDOFF — WarmUp 증분 캐시 (graphify manifest 방식)

> **작성** 2026-08-29 · **수신** 다른 Claude Code 에이전트
> **한 줄** — 전수조사를 **매번 전량 다시 하지 않도록** 파일별 캐시와 무효화를 만든다.
> 설계는 `graphify` 의 `manifest.json` 을 참고했고, **원안(git blob SHA)의 결함 하나를 고친다.**
>
> 이 문서 하나만 읽고 착수할 수 있어야 한다.

---

## 1. 왜 이 일이 필요한가

Mode 1 은 코드베이스를 LLM 이 읽어 `terms-reading.json` 을 만든다. **지금은 그것이 매번 전량이다.**

🔵 2026-08-29 실측 — QtVisionEdit(30파일 2,982줄) 전수조사에 입력 183,638 + 출력 103,926 =
**287,564 토큰**, StickRush(110파일 8,164줄)에 **266,475 토큰**이 들었다.
코드가 조금 바뀌었을 때도 같은 값을 다시 낸다.

**변경은 원래 작다.** 계획서 근거 M4 — 일상 커밋 하나에 바뀌는 사용자 `.cs` 는 **2 / 114 (1.8%)** 다.

---

## 2. 참고한 것 — graphify 의 `manifest.json`

`$CPP_REPO/graphify-out/manifest.json` 에 실물이 있다(🔵 175항목 실측).
**읽을 수 있으면 먼저 열어 보라.** 없으면 아래 요약으로 충분하다.

```json
"core/panorama/panorama.cpp": {
  "mtime": 1787477654.325784,      ← 싼 1차 관문. stat 만 부른다
  "seen":  1788011298.1971562,     ← 이번 훑기에 봤다는 표시
  "ast_hash":      "c371c7c0…",    ← 구조가 바뀌었나
  "semantic_hash": "c371c7c0…"     ← 뜻이 바뀌었나
}
```

곁에 `cache/ast/<해시>.json` 과 `cache/semantic/<해시>.json` 이 있다 —
**해시가 무효화 열쇠이자 캐시 파일 이름이다**(내용 주소 저장).

🔵 실측 관찰 — 175항목 중 **`ast_hash != semantic_hash` 인 것은 0개**다. 두 겹 구조는 스키마에
있으나 아직 갈라지지 않았다. **우리는 갈라 쓴다**(아래 §4). 그리고 코드가 아닌 것도 담는다
(175 중 94가 이미지·md·txt) — 우리는 소스만 담는다.

### 이 방식에서 배울 다섯

| # | graphify | 우리 원안 (`2026-08-28-llm-load-reduction.md` Task 5) | 판정 |
|---|---|---|---|
| 1 | `mtime` 으로 먼저 거른다 | 없음 — 바로 해시 비교 | **배운다.** `stat` 이 훨씬 싸다 |
| 2 | **파일 내용 해시** | **`git ls-tree HEAD` 의 blob SHA** | ⚠ **원안이 틀렸다 (§3)** |
| 3 | `seen` 타임스탬프 | 없음 부재로 추정 | **배운다** |
| 4 | 무효화 두 겹 | 한 겹 | **배운다** |
| 5 | 코드 아닌 것도 담음 | 소스만 | 원안 유지 |

---

## 3. ⚠ 원안의 결함 — 반드시 고칠 것

계획서 `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` 의 `## Task 5`(현재 544줄 근처)는
`git ls-tree -r HEAD` 의 blob SHA 를 무효화 열쇠로 쓴다. **그건 커밋된 내용이다.**

작업 트리를 고쳐 놓고 커밋하지 않은 상태에서 돌리면 **"유효" 로 판정되어 낡은 요약이
그대로 재사용된다.** 개발 중에 가장 흔한 상태가 바로 그 상태다.

**고침** — 파일 내용을 직접 해싱한다(`hashlib.sha256`, 정규화 없이 바이트 그대로).
git 은 **삭제·추적 여부**를 묻는 데만 쓴다.

> 계획서 Task 5 에는 **이미 🔴 대체 배너가 달려 있다**(2026-08-29). 그 절의 `blob_hashes()` ·
> `status()` · 시험 코드는 따르지 마라. 살아 있는 것은 `blast_radius()` 하나다.

---

## 4. 만들 것 — 두 겹 무효화

우리 파이프라인에 대는 지도:

| graphify | 우리 것 | 다시 안 해도 되는 일 |
|---|---|---|
| `ast_hash` | 그 파일의 **선언 목록** — `codegraph/declmap.py` 산출 | 파일 다시 읽기 |
| `semantic_hash` | 그 파일에서 나온 **전수조사 레코드**(`means`·`does`·`uses`) | **LLM 재추론** ← 값어치의 전부 |

**두 겹이 왜 중요한가.** 주석만 고치거나 줄만 밀린 변경은 파일 해시가 바뀌어도
**선언 목록은 같다.** 그러면 LLM 을 다시 부를 필요가 없고 `where` 만 고치면 된다 —
그 일은 `codegraph/xmldoc.py inject` 가 **이미 마커 기준으로 하고 있다.**

### 판정 표 (이대로 구현하라)

| 파일 해시 | 선언 해시 | 해야 할 일 |
|---|---|---|
| 같음 | — | **아무것도 안 한다** (mtime 만 갱신) |
| 다름 | 같음 | `xmldoc inject` 로 `where` 만 고친다. **LLM 부르지 않는다** |
| 다름 | 다름 | **그 파일만** 다시 읽는다 |
| git 이 모름 | — | `삭제됨` — 레코드를 지울지 사람에게 묻는다 |

### 여기에 더해 — 파급은 따로 잡는다

manifest 는 **파일 단위**라 "A 는 안 바뀌었는데 B 가 바뀌어 A 의 서술이 틀려지는" 경우를 못 잡는다.
원안의 `blast_radius()`(codegraph 의존 간선 **양방향 1홉**)가 그것을 맡는다. **둘은 겹치지 않는다.**
원안의 그 함수는 살아 있다 — 계획서 Task 5 Step 3 에 코드가 있으니 가져다 쓰되,
`from`/`to` 키 이름과 `nodes[].file` 유무를 **실제 codegraph.json 으로 재확인하라.**

---

## 5. 검증된 사실 — 착수 전 직접 재확인하라

| 사실 | 확인 |
|---|---|
| `codegraph/warmup.py` 는 **아직 없다** | `ls codegraph/warmup.py` |
| 선언 추출기는 있다 | `codegraph/declmap.py` — `--lang cs\|cpp\|py\|ts`, `scan()` 이 `{파일: {lines, decls[]}}` 를 낸다 |
| 사전 원본 | `<대상저장소>/docs/codegraph/terms-reading.json` — `{키: 레코드}`, 레코드에 `where: "경로:줄"` |
| 좌표 재계산 | `codegraph/xmldoc.py inject` — 마커 기준. `uses[].where` 는 **재계산되지 않는다**(L3 경고로 남는다) |
| 검사 둘 | `terms_db.py --repo <r> --reading <json>` (L1/L2/L3) · `xmldoc.py check` (마커 대조) |
| 시험 재료 | `$CSHARP_REPO`(StickRush) · `$CPP_REPO`(QtVisionEdit). 둘 다 `docs/codegraph/terms-reading.json` 을 갖고 있다 |
| 파이썬 의존성 | `requirements.txt` — `networkx numpy scipy pytest`. **표준 라이브러리로 풀 수 있으면 새 의존성을 더하지 마라** |

---

## 6. 할 일

### STEP 1 — 시험을 먼저 쓴다

**파일:** `codegraph/test_warmup.py` (신규). `tmp_path` 로 진짜 파일을 만들어 시험한다.
**가짜 경로를 쓰지 마라** — 이 저장소에서 그 실수로 시험 둘이 잘못 통과한 적이 있다.

못박을 것: ① 안 바뀐 파일은 `유효` ② 내용이 바뀌면 `낡음` ③ **커밋하지 않은 변경도 `낡음`**
(원안의 결함을 못박는 시험이다) ④ 없어진 파일은 `삭제됨` ⑤ 선언이 같으면 `LLM 불필요`.

### STEP 2 — `codegraph/warmup.py` 를 만든다

```python
def file_hash(path):        """바이트 그대로 sha256. 커밋 여부와 무관하다."""
def load(cache_path):       """없으면 빈 매니페스트."""
def save(cache_path, entries)
def status(cache_path, repo, files):
    """{'유효': [...], '재읽기': [...], '위치만': [...], '삭제됨': [...]}"""
def decl_hash(decls):       """선언 목록의 해시. declmap.scan 의 한 파일 몫을 받는다."""
```

**mtime 을 1차 관문으로 쓴다** — `mtime` 과 크기가 같으면 해싱을 건너뛴다.
**`seen` 을 매 실행마다 갱신**하고, 이번에 안 본 항목은 `삭제됨` 으로 낸다.

매니페스트 위치: `<대상저장소>/out/codegraph-raw/warmup.json` (파생물이라 gitignore 대상).
**⚠ 그러면 다른 머신·다음 세션에서 캐시가 없다.** 추적 경로에 둘지는 **혼자 정하지 말고 보고하라.**

### STEP 3 — CLI

```bash
python codegraph/warmup.py status <저장소> --lang cs
python codegraph/warmup.py blast  <저장소> --codegraph <codegraph.json> --hops 1
```

`scripts/*.mjs` 와 같은 규약으로 **직접 실행 가드**를 둔다(`if __name__ == "__main__":`).
import 시에는 순수 함수만 노출한다.

### STEP 4 — 실측한다. **이것이 이 작업의 목적이다**

```bash
# ① baseline — 지금 몇 파일을 읽어야 하나
python codegraph/warmup.py status "$CSHARP_REPO" --lang cs      # 첫 실행: 전부 재읽기
# ② 아무것도 안 고치고 다시                                     # 기대: 전부 유효
# ③ 파일 하나의 주석만 고치고 다시                              # 기대: 위치만 1
# ④ 파일 하나에 함수를 더하고 다시                              # 기대: 재읽기 1
# ⑤ 파급까지
python codegraph/warmup.py blast "$CSHARP_REPO" --codegraph .../codegraph.json --hops 1
```

**보고에 이 표를 채워라** — 전체 파일 수 / 1커밋 변경 / 1홉 파급 / **재읽기 비율(%)**.
이 숫자가 나오기 전에는 **"증분으로 좋아졌다" 고 쓰지 마라.**

---

## 7. 경계 — 건드리지 말 것

| 파일 | 왜 |
|---|---|
| `codegraph/normalize.py` | 다른 작업(clang-doc 합치기)이 만지는 중일 수 있다 |
| `codegraph/xmldoc.py` | 좌표 재계산의 주인. **부르되 고치지 마라** |
| `codegraph/terms_db.py` | 사전 병합. 여기에 캐시를 끼워 넣지 마라 — `warmup.py` 는 **독립 도구**다 |
| 대상 저장소의 `docs/codegraph/terms-reading.json` | 사람과 LLM 이 쓴 원고다. **캐시가 자동으로 고치게 하지 마라** |

**`warmup.py` 는 요약을 만들지 않는다.** 수명과 무효화만 맡는다. 요약은 LLM 이 낸다.
이 분리가 원안의 요점이고 그대로 지킨다.

---

## 8. 검증

```bash
cd <report-builder 루트>
export GRAPHICS_REPO=... CSHARP_REPO=... CPP_REPO=...
.venv/bin/python -m pytest codegraph/ -q     # 기대: 신규 시험 포함 전부 통과
npm test                                     # 기대: fail 0 (이 작업은 Node 를 안 건드린다)
.venv/bin/python codegraph/xmldoc.py check   # 기대: 문제 0건
.venv/bin/python codegraph/terms_db.py --repo "$CSHARP_REPO" \
  --reading "$CSHARP_REPO/docs/codegraph/terms-reading.json" -o /tmp/w
#   기대: 실패 0 · 근거 없음 0  ← 캐시가 사전을 망가뜨리지 않았다는 증거
```

---

## 9. 이 저장소의 규약 (반드시 지킬 것)

- **커밋하지 마라.** 사용자 승인 후 오케스트레이터가 한다. `git add -A` 금지.
- **새 코드를 쓰면 그 자리에서 전수조사 레코드도 쓴다** — `docs/codegraph/terms-reading.json` 에
  `{kind, module, where, means, does?, uses[], confidence, source:"reading"}` 를 넣고
  `xmldoc.py emit` → `inject`. **코드와 좌표는 같은 커밋에.**
- **경로를 코드에 박지 마라.** 환경변수와 탐색으로 찾는다.
- 주석과 문서는 **한국어**, 약어를 피하고 메커니즘 먼저.
- **거울 함정** — 캐시 백엔드 추상화·플러그인을 만들지 마라. 파일 하나, 소비자 하나다.
- **조기 성공 선언 금지.** 표본이 둘이면 "검증됨" 이라고 쓰지 않는다.

---

## 10. 보고

`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` 로 시작하고 아래를 담아라.

- 바뀐 파일 목록
- §8 검증의 **실제 출력**
- §6 STEP 4 의 **재읽기 비율 표** (숫자 없이 이득을 주장하지 마라)
- 매니페스트를 추적 경로에 둘지에 대한 **의견과 근거** (결정은 사용자 몫)
- 미룬 것과 그 이유

**이 문서의 수치를 그대로 믿지 말고 시작 전에 재확인하라.**
