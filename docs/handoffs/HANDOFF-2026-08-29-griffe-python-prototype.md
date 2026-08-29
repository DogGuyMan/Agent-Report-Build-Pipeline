# HANDOFF — griffe 기반 Python 정적 수집기 프로토타입 (Option B)

> 이 문서는 **Artifact A(자기완결형 에이전트 프롬프트)** 다. 아래 펜스 블록 하나를 새 Claude Code
> 세션에 그대로 붙여넣으면 실행할 수 있다. 펜스 밖 내용은 오케스트레이터(사용자)를 위한 메모다.

## 배경 (오케스트레이터용 메모)

`docs/handoffs/RESUME-2026-08-29-mode-1-5-orchestrator.md` §6 R11 표가 Python·JS/TS 의 정적 수집기를
**"없음"** 으로 기록해 뒀다(지금 정책은 `codebase-terms-survey` 스킬의 LLM 전수조사 →
`terms_db.py::project_codegraph` 투영). 외부 조사 문서(`compass_artifact_wf-9ef6b1d8-…md`, 사용자 제공)가
Python 은 **griffe**, JS/TS 는 **ts-morph 자작 덤퍼**를 1순위로 추천했고, 세션 내 대조 결과 이 계약
(`codegraph/normalize.py` 의 `_assemble` 출구, kind 8종 enum, R1~R7 규칙)과 구조적으로는 맞지만 두 지점
(소유권 축 부재, R5 제네릭 파싱)이 미검증이었다.

**사용자 결정 — Option B: griffe(Python) 만 우선 프로토타입.** ts-morph/JS-TS 는 범위 밖.
**지금 실행하지 않고 핸드오프로 인계한다.**

---

## 펜스 블록 — 아래를 그대로 새 세션에 붙여넣을 것

```
[ROLE]
너는 report-builder 저장소($REPO_ROOT)의 codegraph 파이프라인에
Python 정적 수집기 경로를 하나 추가하는 작업을 맡는다. griffe 라는 기성 라이브러리를 얇게
감싸 codegraph.json(schema_version 2) 으로 정규화하는 `normalize_python()` 을
`codegraph/normalize.py` 에 추가하는 것이 전부다. 이 저장소의 codegraph 파이프라인은 이미
C++(clang-uml)·C#(roslyn-dump) 두 언어를 같은 방식으로 처리하고 있으니, 그 패턴을 세 번째
언어로 확장하는 작업이라고 이해하면 된다.

이 작업은 "프로토타입 시험"이다 — 완성된 기능이 아니라 실제로 돌려서 마찰 지점을
찾는 것이 목적이다. 완벽을 목표로 범위를 넓히지 말 것.

[Hard rules]
- **커밋하지 말 것.** 이 저장소는 사용자가 명시적으로 요청할 때만 커밋한다
  (CLAUDE.md 최상위 규약). 변경 후 diff 와 테스트 결과만 보고하라.
- 커밋 메시지가 필요해지면(사용자가 나중에 커밋을 요청하면) `personal-commit-messages` 스킬을
  따른다 — 소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음, 트레일러 없음.
- 주석은 한국어 + 필요한 곳만 영문 기술용어 병기. `normalize.py` 기존 함수들의 스타일
  (`# ── 절 제목` 구분선, 함수 위 한 줄 요약 + docstring)을 그대로 따른다.
- **`<include file="docs/codegraph/comments.xml" .../>` 꼴 주석 태그를 손으로 달지 말 것.**
  이건 `codebase-terms-survey` 스킬의 전수조사 결과를 `codegraph/xmldoc.py inject` 가
  자동으로 박아 넣는 것이다(🔵 이번 세션에 `xmldoc.py` 를 읽어 `run_check()` 존재를 확인함 —
  기존 함수 흉내로 태그만 손으로 붙이면 `terms-reading.json` 과 어긋나 별도 파이프라인이
  깨진다). 새 함수에는 태그 없는 평범한 한 줄 요약 주석만 남겨라.
- **거울 함정 경계.** `normalize_python()` 하나만 만들어라. "언어별 플러그인 구조",
  "파서 레지스트리", "추상 Collector 인터페이스" 를 만들면 그 자체가 이 저장소의
  CLAUDE.md 가 명시적으로 금지하는 실패다(구현자 1·소비자 1일 때 인터페이스 금지).
- **R5(컨테이너 투과)는 이번 범위에서 명시적으로 제외한다.** griffe 는 타입힌트를
  구조화된 값이 아니라 **문자열**로 준다(`List[Foo]` 같은 것을 파싱해야 함) — 이건
  clang-uml/Roslyn 과 다른 지점이고, 첫 프로토타입에서 다루면 범위가 커진다. 컨테이너
  타입(list/dict/Optional 등)은 그냥 "해소 안 됨"으로 두고 통계에 남겨라. 이 결정을
  코드 주석과 보고서에 명시적으로 적을 것 — 조용히 빠뜨리지 말 것.
- **R11(schema_version 3, `loc`/`url` 필드 확장)은 범위 밖이다.** 건드리지 마라 — 별도 열린
  결정(RESUME 문서 §6)이고 사용자 승인 전이다.
- **`src/`(JS/TS 쪽), `scripts/*.mjs`, `report-spec`/`report-term` CLI 는 절대 건드리지 않는다.**
  Mode 2(보고서 빌더) 파이프라인이고 이 작업과 무관하다.
- **`docs/codegraph/terms-reading.json` / `comments.xml` 을 건드리지 않는다.** 별도
  전수조사 파이프라인 소유다.

[VERIFIED FACTS — 이 보고를 믿지 말고 재검증하라]
🔵 아래는 이 핸드오프를 쓴 세션이 2026-08-29 시점에 실제로 읽거나 실행해 확인한 것이다.
저장소는 여러 세션이 동시에 건드릴 수 있으므로, 작업 시작 전에 `git log -3`·`git status` 로
다시 확인하라.

1. `codegraph/normalize.py` 의 함수 구조 (커밋 `e0af02d`, 이후 이 파일 변경 없음 — 재확인할 것):
   - `git_commit(repo)` — 저장소 커밋 해시. **그대로 재사용**, 손대지 마라.
   - `module_of(path)` (C++용) / `cs_module_of(path)` (C#용) — 모듈 경계 = 폴더 트리.
     Python 도 같은 방식이 자연스럽다: `codegraph/normalize.py` → 모듈 `codegraph`.
   - `_assemble(nodes, edges, stats, *, language, source_tool, repo)` — **두 언어 파서가
     수렴하는 공통 출구.** R1(도달 안 하는 외부 노드 제거) · 모듈 의존 유도 · 최종 dict 조립을
     전부 여기서 한다. `normalize_python()` 은 이 함수를 그대로 호출하면 된다 — 재구현하지 마라.
   - `normalize_cpp(elements, relationships, repo, source_tool)` 와
     `normalize_csharp(dump, repo)` — 이 둘의 **모양**(1패스: 노드 결정 → 2패스: 간선 결정 →
     `_assemble` 호출)이 `normalize_python()` 이 따라야 할 템플릿이다.
   - `main()` — `argparse` 의 `mutually_exclusive_group(required=True)` 에
     `--clang-uml` / `--roslyn-dump` 두 개만 있다(`main()` 안, `add_argument` 두 줄).
     여기에 `--griffe-dump` 를 셋째로 추가한다.
   - kind enum 은 **8종 고정**(`composition`/`aggregation`/`dependency`/`instantiation`/
     `friendship`/`inheritance`/`realization`/`association`) — 주석에 "8종 enum 에 자리가
     없다" 라고 명시돼 있다. 새 kind 를 만들지 마라.
   - C# 경로는 언어에 소유 표지(값 멤버 vs 포인터 멤버)가 없어서 `composition`/`aggregation`
     이 항상 0 이고 `association` 만 쓴다(`main()` 의 출력 로직에 "C# 정상 — 함정 5" 로 이미
     문서화돼 있음). **Python 도 같은 패턴을 따라야 한다** — Python 은 모든 바인딩이
     참조라 값 멤버/포인터 멤버 구분이 아예 없다.

2. `codegraph/test_normalize.py` (326줄, 함수 30개) 의 테스트 관습:
   - kind 대응표가 항등이 아님을 못박는 단위 테스트(`test_clang_uml_kind_is_not_identity` 등).
   - **골든 테스트**는 실제 저장소 산출물을 쓰고, 파일이 없으면 `pytest.skip()` 한다
     (`CPP_REPO`/`CS_REPO` 는 이 머신의 다른 경로를 가리키는 외부 저장소).
     Python 쪽은 **외부 저장소가 필요 없다** — `codegraph/` 자기 자신이 유일한 Python
     패키지이므로 **자기호스팅 골든 테스트**로 만들 수 있다(griffe 로 `codegraph/` 를
     덤프해서 정규화한 뒤 불변식을 검증).
   - 기존 불변식 예시: 외부 노드는 위치가 없다(`test_golden_external_nodes_have_no_location`),
     R4(외부발 간선 없음)(`test_golden_r4_no_edges_out_of_island`), 모듈 의존이 외부를
     포함하지 않는다(`test_golden_module_deps_exclude_external`). 새 테스트도 같은 꼴의
     불변식을 검증하라.

3. 환경 — 🔵 이 세션에서 확인:
   - `.venv/bin/python` 은 3.14. **`griffe` 는 현재 설치돼 있지 않다**
     (`.venv/bin/pip show griffe` → `Package(s) not found`). 설치부터 해야 한다.
   - 외부 조사 문서(사용자 제공, `compass_artifact_wf-9ef6b1d8-…md`)가 적어 둔 캐치 —
     **"griffe v1 부터 멤버 직렬화가 list 에서 dict 로 바뀐다."** 이건 이 세션이 직접 확인한
     사실이 아니라 **그 문서의 주장**이다 — STEP 1 에서 실제로 설치된 버전의 실제 출력
     구조를 보고 확인하라. 상상하지 마라.

[STEP 1 — 설치 + 실제 출력 그라운딩 (반드시 먼저)]
griffe 의 정확한 JSON 필드명·중첩 구조를 이 핸드오프는 모른다(설치가 안 돼 있어 이번
세션이 실행해보지 못했다). **추측으로 파싱 코드를 쓰지 마라.** 먼저 실제로 돌려서 눈으로
확인해라:

    cd $REPO_ROOT
    .venv/bin/pip install griffe
    .venv/bin/python -m griffe dump codegraph --output /tmp/griffe-codegraph.json
    .venv/bin/python -c "import json; d=json.load(open('/tmp/griffe-codegraph.json')); print(json.dumps(d, indent=2)[:3000])"

`codegraph` 패키지(이 저장소의 유일한 Python 패키지, `codegraph/*.py`)를 대상으로 삼는다 —
외부 저장소가 필요 없다. 출력에서 다음을 직접 확인하고 메모하라(다음 STEP 에서 쓴다):
- 클래스/함수/모듈 각 객체가 `lineno`/`endlineno` 를 어디에 갖는지, 몇 번째 depth 인지
- 멤버(속성·메서드) 목록이 **list 인지 dict 인지** (버전에 따라 다르다고 조사 문서가 경고함)
- 상속(`bases`) 정보가 어떤 키에 어떤 형태로 들어있는지
- import 된 외부 모듈이 어떻게 표현되는지 (타입힌트 문자열 안에 있는지, 별도 필드인지)

[STEP 2 — `normalize_python()` 추가]
`codegraph/normalize.py` 에 C# 섹션(`# ═══ C# (roslyn-dump.json) ═══` 배너) 다음에
같은 형식의 새 배너로 Python 섹션을 추가한다:

    # ═══════════════════════════════ Python (griffe) ═══════════════════════════════

`normalize_cpp`/`normalize_csharp` 와 같은 모양(1패스 노드 → 2패스 간선 → `_assemble` 호출)을
따르되, 아래 정책을 코드로 옮긴다 — 정확한 딕셔너리 키는 STEP 1 에서 확인한 실제 구조를 써라:

1. **1차/외부 판정** — griffe 는 명시적으로 지정한 패키지만 로드한다. 즉 덤프에 나온 최상위
   객체는 전부 1차 코드다(C++ 의 네임스페이스 접두, C# 의 어셈블리 일치 같은 별도 판정이
   필요 없다). 타입힌트나 상속에서 참조되지만 덤프에 없는 이름 = 외부.
2. **모듈 경계** — `module_of()` 와 같은 정책(폴더 트리)으로 `py_module_of(path)` 를 새로
   만들거나, 이미 있는 `module_of()` 를 재사용할 수 있는지 먼저 검토해라(경로 규칙이 같으면
   중복 함수를 만들지 말고 공유하는 게 낫다 — 다만 억지로 합치다 C++ 전용 분기(`src`/`apps`
   접두 처리)를 오염시키지는 마라. 애매하면 별도 함수로 두고 그 이유를 주석에 적어라).
3. **kind 사상 — association-only.** Python 에는 값 멤버/포인터 멤버 구분이 없으므로
   `composition`/`aggregation` 을 만들지 마라. 상속은 `inheritance`, 그 외 클래스 간
   속성 참조는 전부 `association` 으로 사상한다(C# 의 `CS_KIND["assoc"]` 과 같은 자리).
4. **R5(컨테이너 투과) — 이번엔 구현하지 않는다.** `list[Foo]`/`Optional[Foo]` 같은 타입힌트를
   만나면 해소하려 하지 말고 통계 카운터(`stats["R5 미구현(범위 밖)"]`)에 세어서 정직하게
   보고하라. 조용히 버리거나 조용히 성공한 척하지 마라.
5. **R7(원시 타입 제외)** — Python 빌트인 스칼라(`str`/`int`/`float`/`bool`/`bytes`/`None`/
   `NoneType`) 를 노드로 만들지 않는다. `CPP_PRIMITIVES`/`CS_R7` 과 같은 자리에
   `PY_R7` 세트를 만들어라.
6. **외부 그룹핑(R2)** — import 루트 이름(예: `json`→`json`, `argparse`→`argparse`,
   `pytest`→`pytest`) 하나로 접는다. `external_group()`/`cs_external_group()` 과 같은
   자리에 `py_external_group()` 을 만들어라.
7. `source_tool` 은 `"griffe " + <설치된 버전>` (버전은 STEP 1 에서 확인), `language` 는
   `"python"`.
8. 마지막 줄은 반드시 `return _assemble(nodes, edges, stats, language="python", source_tool=…, repo=repo)`
   — `_assemble` 을 재구현하지 마라.

[STEP 3 — CLI 배선]
`main()` 의 `mutually_exclusive_group` 에 셋째 옵션을 추가:

    src.add_argument("--griffe-dump", help="Python — griffe dump 산출물(JSON)")

`if a.clang_uml: … elif a.roslyn_dump: … else: …` 형태로 분기(기존은 `if/else` 2분기이므로
3분기로 바꿔야 한다). `git_commit`/출력 통계 로직도 세 번째 갈래를 인식하도록 최소한만 손댄다.

[STEP 4 — 테스트]
`codegraph/test_normalize.py` 끝에 새 절을 추가한다 (기존 섹션 구분 스타일 `# ── N. 제목` 유지):
- 단위 테스트: kind 사상이 association-only 인지 고정(`composition`/`aggregation` 이
  결과에 없어야 함 — `test_golden_csharp_has_no_ownership_kinds` 와 같은 패턴).
- **자기호스팅 골든 테스트**: `codegraph/` 자신을 griffe 로 덤프 → `normalize_python()` →
  기존 골든 테스트들이 쓰는 불변식(외부 노드 위치 없음, R4, 모듈 의존이 외부 제외) 중
  적용 가능한 것을 재사용. griffe 가 설치돼 있지 않거나 산출물이 없으면 `pytest.skip()`
  (기존 관습 그대로).

    .venv/bin/pytest codegraph/test_normalize.py -q -k python

[Boundaries]
- 소유: `codegraph/normalize.py`, `codegraph/test_normalize.py` 만 수정한다.
- 절대 건드리지 않음: `src/`, `scripts/`, `docs/codegraph/*`, `report-spec`/`report-term`
  진입점(`bin/`), `codegraph/terms_db.py`(별도 파이프라인 — 이번 프로토타입과 무관).
- 이 저장소는 병렬로 여러 세션이 작업할 수 있다. 시작 전 `git status`/`git log -3` 로
  다른 세션이 같은 파일(`normalize.py`)을 건드리고 있지 않은지 확인하라.

[Verify]
    cd $REPO_ROOT
    .venv/bin/python -m pytest codegraph/ -q
    npm test          # normalize.py 는 JS 쪽과 무관하지만 회귀 확인 차 함께 돌린다
    npm run typecheck

기대: 기존 pytest 전부 통과 + 새로 추가한 Python 관련 테스트 통과(또는 griffe 미설치 시
정직하게 skip). `npm test`/`typecheck` 는 이 변경으로 영향받지 않아야 한다(영향받으면
범위를 벗어난 파일을 건드렸다는 신호다).

[Self-review]
- [ ] `composition`/`aggregation` kind 를 Python 경로에서 만들지 않았는가?
- [ ] R5(컨테이너 투과)를 "구현한 척" 하지 않고 정직하게 미구현으로 표시했는가?
- [ ] `<include>` xmldoc 태그를 손으로 달지 않았는가?
- [ ] `_assemble()` 을 재구현하지 않고 그대로 호출했는가?
- [ ] `src/`, `scripts/`, `docs/codegraph/*` 를 건드리지 않았는가?
- [ ] 커밋하지 않았는가?

[Report]
DONE / DONE_WITH_CONCERNS / BLOCKED 중 하나로 보고하고 다음을 포함하라:
- 변경한 파일과 diff 요약
- STEP 1 에서 실제로 관찰한 griffe JSON 구조(이 핸드오프가 몰랐던 부분이므로 반드시 적을 것)
- pytest/typecheck 실행 결과(그대로 붙여넣기)
- 이번 프로토타입이 드러낸 마찰 지점 — 특히 R5 미구현이 실제로 얼마나 아픈지
  (해소 실패 카운터가 몇 건인지), kind 를 association-only 로 접었을 때 정보 손실이
  체감상 큰지
- 이번 세션이 몰라서 STEP 1~2 사이에 스스로 내린 판단이 있다면 전부 명시할 것
  (예: 멤버가 dict 였다면 어떻게 순회했는지)
```

---

## 오케스트레이터용 메모 (펜스 밖)

- 이 작업은 **R9(다음 실사용 프로젝트)** 논의의 재료가 될 수 있다 — `codegraph/` 자체가
  Python 패키지이므로 이 프로토타입 하나로 "실제 소비자 0명" 문제를 부분적으로 완화한다.
  다만 이건 **자기호스팅 시험**이지 실사용은 아니라는 점을 R9 논의 때 구분해서 말할 것.
- ts-morph(JS/TS) 는 명시적으로 범위 밖에 뒀다 — Option B 만 승인됐다. 필요해지면 이 문서를
  본떠 별도 핸드오프를 만든다(같은 `_assemble()` 출구, `normalize_js()`, `kind` 는 마찬가지로
  association-only 가 유력하지만 그건 그때 다시 판단).
- 커밋 정책상 이 작업은 미커밋 상태로 남을 것이다 — 리뷰 후 사용자가 커밋을 요청하면
  `personal-commit-messages` 스킬로 메시지를 짓는다.

## 변경 이력

- 2026-08-29 — 최초 작성. Option B(griffe 프로토타입) 승인, ts-morph/JS-TS 는 범위 밖으로 확정.
