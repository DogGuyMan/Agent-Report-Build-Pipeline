# RESUME — Track C 코드베이스 위키 파이프라인 (2026-08-28)

> 🟡 **부분 대체됨 (2026-08-29 18:15)** — Mode 1 파이프라인이 **terms-db 우선** 구조로 바뀌었다(계획서 `docs/superpowers/plans/2026-08-29-mode-1-terms-db-first.md`, 7/7 완료).
> `codegraph/terms_db.py` 가 `--reading terms-reading.json`(LLM 전수조사 원본)을 받아 `terms-db.json`(원본)을 만들고 `codegraph.json` 을 **투영**한다. 정적 수집기(roslyn/clang-uml)가 있는
> 저장소에서는 기존 호출 꼴 `terms_db.py <codegraph.json> --repo …` 이 그대로 돌고 투영이 상위집합인지 대조한다. **`normalize.py` 출력 키는 불변이다.**
> 전수조사 절차는 `.claude/agents/mode-1-codebase-wiki.md` `## 전수조사 절차`. 이 문서의 C#/C++ 갈래 서술과 함정 절은 그대로 유효하다. 세션 재개의 단일 진입점은
> `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

> **이 문서가 재개의 단일 진입점이다.** 새 세션은 이것 하나만 읽고 이어갈 수 있어야 한다.
> 다른 문서는 심화 자료이지 시작 전제가 아니다.

---

## TL;DR + 바로 다음 한 걸음

**어디까지 왔나** — Track C 의 **C# 갈래가 끝까지 완주**했다.
정적 수집(`roslyn-dump`) → 정규화(`normalize.py`) → 사실 표(`facts.py`) → 다이어그램 →
위키 10장 → 인용 검증 → Mermaid 치환. **C++ 갈래는 위키 0장으로 미완**이다.

**바로 다음 한 걸음** — 사용자가 실행 방식을 고르는 것이 막힌 지점이다:

> `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` (Task 1~8) 를
> **① 서브에이전트 방식**(Task 마다 새 에이전트 + 사이 검토) 으로 갈지
> **② 인라인 실행**(이 세션에서 순차) 으로 갈지 — **사용자에게 물어보고 시작하라.**

그 계획을 시작하기 전에 **아래 §2 의 미커밋 9항목을 먼저 커밋**하는 것을 권한다(사유는 거기 적었다).

---

## 1. ⚠ 함정 둘 — 재개 전에 반드시 읽을 것

### (가) 대상 저장소의 산출물은 **git 에 안 올라간다**

🔵 실측 — 두 대상 저장소 모두 `out/codegraph-raw/` 가 `.gitignore` 에 걸려 있다.

```
StickRushGame/.gitignore:82   out/codegraph-raw/
GlobalMedia-.../.gitignore:192 out/codegraph-raw/
```

**즉 위키 10장 · `codegraph.json` · `facts/` · `ranking.json` · `roslyn-dump.json` 은
이 머신에만 있다.** 다른 머신에서 재개하면 **전부 없다** — 파이프라인을 처음부터 다시 돌려야 한다.
같은 머신에서 재개하는 것이라면 그대로 있다. **먼저 존재를 확인하라:**

```bash
ls $CSHARP_REPO/out/codegraph-raw/wiki/*.md | wc -l   # 10 이어야 함
ls $GRAPHICS_REPO/out/codegraph-raw/        # codegraph.json 등
```

없으면 §5 의 재생성 명령을 순서대로 돌린다.

### (나) `__pycache__/*.pyc` 가 git 에 추적되고 있다

🔵 `git ls-files codegraph/__pycache__` 가 `.pyc` 를 낸다 — `.gitignore` 에 `__pycache__` 가 없다.
**커밋할 때마다 바이너리 diff 가 섞인다.** 정리하려면:

```bash
printf '\n__pycache__/\n*.pyc\n' >> .gitignore
git rm -r --cached codegraph/__pycache__
```

⚠ **사용자 승인 없이 하지 말 것** — 추적 파일을 지우는 변경이다.

---

## 2. 현재 상태 — 재측정 (2026-08-28)

**브랜치** `feat/report-builder`

```
1b477b2 [feature] : LLM 추론 전단계 파이프라인 제작     ← 사용자가 세션 중 커밋
8b4b6c6 [feature] : render_module                      ← 사용자가 세션 중 커밋
ea33069 feat : 실측과 판단을 별개 행으로 가르는 주석 블록
```

### 미커밋 9항목 — **이 세션의 산물 중 아직 안 들어간 것**

| 파일 | 상태 | 무엇 |
|---|---|---|
| `codegraph/test_normalize.py` | 신규 | **회귀 테스트 28개** — 정규화 계층의 "틀려도 오류가 안 나는" 자리 고정 |
| `codegraph/fix_citation_paths.py` | 신규 | 인용 경로 축약 복구기 |
| `codegraph/demermaid.py` | 수정 | mermaid 문법 제약 4종 폴백 추가 |
| `codegraph/verify_citations.py` | 수정 | 오탐 2건 수정(인접 줄 대조 · Sources 주석 제외) |
| `docs/handoffs/HANDOFF-codebase-wiki.md` | 수정 | Phase 9·10·10-1·5-3 + C-16~C-18 |
| `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` | 신규 | **다음 작업 계획 8 Task** |
| `codegraph/__pycache__/*.pyc` ×3 | 수정/신규 | ⚠ §1(나) 참조 — **커밋에 넣지 말 것** |

**권장 커밋(경로를 좁혀서, `git add -A` 쓰지 말 것):**

```bash
git add codegraph/test_normalize.py codegraph/fix_citation_paths.py \
        codegraph/demermaid.py codegraph/verify_citations.py
git commit -m "[feature] : 회귀 테스트와 인용 경로 복구기"

git add docs/handoffs/HANDOFF-codebase-wiki.md \
        docs/superpowers/plans/2026-08-28-llm-load-reduction.md
git commit -m "[docs] : llm 부담 감축 계획과 phase 기록"
```

### 산출물 현황 (이 머신)

| | C# (StickRushGame) | C++ (GlobalMedia) |
|---|---|---|
| `codegraph.json` | ✅ 노드 231 / 간선 540 / 모듈 10 | ✅ 노드 191 / 간선 417 / 모듈 20 |
| `facts/` | ✅ 5종 | ✅ 5종 |
| 모듈 다이어그램 | ✅ 순환 5 | ✅ 순환 11 |
| 클래스 다이어그램 | ✅ 4개 | ✅ 1개(`material`) |
| **위키** | ✅ **10장** (인용 745건 전량 L1/L2 통과) | ❌ **0장** |
| `wiki-built/` (Mermaid 치환본) | ✅ 10장 + SVG 자산 33 | — |
| `codegraph-rules.toml` | 🔸 골격만 (`[[layer]]` 6, `[[allow]]` 0) | 🔸 골격만 (`[[layer]]` 0) |

---

## 3. 확정된 결정 — 다시 논쟁하지 말 것

전문은 `docs/handoffs/HANDOFF-codebase-wiki.md` §2 (C-1~C-18) 와
`docs/handoffs/DECISION-csharp-intermediate-format.md` (F1~F14).
**재개에 꼭 필요한 것만 여기 인라인으로 옮긴다:**

| ID | 결정 | 재개 시 중요한 이유 |
|---|---|---|
| **C-9** | 외부 의존은 전이 확장 없이 단일 노드로 접고 외딴 섬에 모은다 (R1~R7) | 서드파티 262,096줄(96.9%)이 이것으로 막혔다. **감축 대상이 아니다** |
| **C-12** | 파이프라인 코드는 전부 `report-builder/codegraph/`. 대상 저장소 경로는 **인자** | 사용자 프로젝트에 도구를 심지 않는다 |
| **C-13→C-16** | 인용 검증 L3 대상 = 노드 + **위치 있는 간선 전부** + (`--detail` 시) 멤버·메서드 | ⚠ **C-11 은 번복됐다.** 낡은 절을 정본으로 읽지 말 것 |
| **C-14** | `containment` 는 버린다 (`dependency` 흡수 안 함) | P4 의미축에 역방향 화살표가 생겨 오독을 부른다 |
| **C-15** | `modules[].depends_on` 은 클래스 간선 유도. CMake 조인 안 함 | **링크 의존이 아니라 타입 의존**이다 |
| **C-17** | 큰 모듈 생략 = 간선 0(고아)은 본문에서 빼고 목록에만 | 생략하되 숨기지 않는다 |
| **C-18** | Mermaid **전면 치환**(A안). VitePress 클라이언트 렌더에 맡기지 않음 | 🔵 이것이 mermaid 문법 오류 5건을 빌드 시점에 잡았다 |

### 이 세션에서 사용자가 확정했으나 **아직 문서에 안 박힌 것** (계획서 Task 7 이 기록한다)

| | 결정 |
|---|---|
| U1 | 목적은 비용·속도와 정확성 **둘 다** |
| U2 | **계층화 허용** — 전 모듈은 구조·시그니처로 싸게, 중요 소수만 정독 |
| U3 | 코드 규약은 **검증 가능한 것만** |
| U4 | WarmUp 캐시 단위 = **파일별 이해 요약** |
| U5 | **`codegraph.json` 스키마 확장 허용** — `calls[]` 재검토 |
| U6 | 캐시 무효화는 **git 기반** |

---

## 4. 가드레일과 컨벤션 — Step 0 실측

### 커밋

🔵 `git log` 실측 — **한 줄 제목만. 본문도 트레일러도 없다.**

```
[feature] : LLM 추론 전단계 파이프라인 제작
[docs] : 오케스트레이터 회신 인계 문서 작성
```

⚠ **`Co-Authored-By` / `Claude-Session` 트레일러를 붙이지 말 것.** 이 저장소의 기존 커밋 어디에도 없다.
`personal-commit-messages` 스킬(소문자 `[tag] : subject` 한 줄, 한국어, 본문 없음)을 따른다.
**커밋은 사용자 요청이 있을 때만 한다.**

### 검증 명령

```bash
cd $REPO_ROOT
.venv/bin/pytest codegraph/test_normalize.py -q     # 28 passed (2026-08-28 실측)
npm test                                            # Track B(렌더러) 쪽. 44개
```

### Python 환경

`.venv` 사용 필수 — Homebrew Python 3.14 는 전역 설치를 거부한다(PEP 668).
설치된 것: `networkx pydot lxml numpy scipy pytest`.
⚠ `networkx.pagerank` 가 **scipy 구현만** 갖고 있어 numpy/scipy 없이는 죽는다.

### 코드 컨벤션

- 주석·문서는 **한국어**, 기술 용어는 영문 병기. **약어·압축 표현 회피**
- 확신도는 🔵/🟡/💭 + 정수. **🔵 는 이번 세션에서 실제로 돌린 명령의 출력만**
- 객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다
- **거울 함정 경계** — 도구는 JSON 을 표로 바꾸는 스크립트다. 플러그인 구조·추상 인터페이스가
  나오면 그 자체가 Track C 가 잡으려는 실패다

### 사용자 프로젝트를 바꾸지 않는다

두 대상 저장소에 남기는 것은 `out/codegraph-raw/` 산출물과 `.gitignore` 한두 줄뿐이다.
소스 코드·`.asmdef` 신설·씬/프리팹 저장은 **금지**.

---

## 5. 파이프라인 재생성 명령 (산출물이 없을 때)

```bash
cd $REPO_ROOT
CS=$CSHARP_REPO
CPP=$GRAPHICS_REPO

# ── C# ──
dotnet run --project codegraph/roslyn-dump -- "$CS"
.venv/bin/python codegraph/normalize.py --roslyn-dump "$CS/out/codegraph-raw/roslyn-dump.json" \
  --repo "$CS" -o "$CS/out/codegraph-raw/codegraph.json"
.venv/bin/python codegraph/facts.py "$CS/out/codegraph-raw/codegraph.json" --repo "$CS" \
  --detail "$CS/out/codegraph-raw/roslyn-dump.json"
.venv/bin/python codegraph/render_modules.py "$CS/out/codegraph-raw/codegraph.json" -o out/diagrams/csharp-modules

# ── C++ ── (clang-uml 설정은 저장소의 .clang-uml 을 **먼저 읽을 것**. 최소 설정으로 덮으면 1·2차 실패가 재현된다)
cd "$CPP" && clang-uml -c .clang-uml -n full_class_all -g json --paths-relative-to-pwd -q
cd $REPO_ROOT
.venv/bin/python codegraph/normalize.py --clang-uml "$CPP/out/codegraph-raw/full_class_all.json" \
  --repo "$CPP" -o "$CPP/out/codegraph-raw/codegraph.json"
.venv/bin/python codegraph/facts.py "$CPP/out/codegraph-raw/codegraph.json" --repo "$CPP"

# ── 검증 · 치환 ──
.venv/bin/python codegraph/verify_citations.py "$CS"/out/codegraph-raw/wiki/*.md \
  --repo "$CS" --codegraph "$CS/out/codegraph-raw/codegraph.json" \
  --detail "$CS/out/codegraph-raw/roslyn-dump.json"
.venv/bin/python codegraph/demermaid.py "$CS/out/codegraph-raw/wiki" \
  --out "$CS/out/codegraph-raw/wiki-built" --svg-dir out/diagrams
```

---

## 6. 남은 작업 — 우선순위 순

| # | 작업 | 막는 것 | 문서 |
|---|---|---|---|
| 1 | **LLM 부담 감축 계획 8 Task** | 사용자의 실행 방식 선택 | `plans/2026-08-28-llm-load-reduction.md` |
| 2 | **VitePress 조립** | `wiki-built/` 준비 완료 — 바로 가능 | `deep-wiki:build` 스킬 |
| 3 | C++ 위키 (0장) | 없음 — `material` 클래스 SVG 까지 있다 | `wiki/managers.md` 를 형식 정본으로 |
| 4 | C++ 문서 마감 5건 | 없음 | `HANDOFF-cpp-pattern-collection.md` §0-1 "⏳ C++ 쪽 미완" |
| 5 | `codegraph-rules.toml` 판정 | **사용자만 가능** — 순환 허용/위반 | `HANDOFF-*-boundary-rules.md` |
| 6 | Graphviz `Managers` 모듈 크래시 | 원인 미확정 💭 55 | `HANDOFF-unity-roslyn-dump-v2.md` 끝 |

⚠ **5번은 에이전트가 판정하면 안 된다.** 무엇이 허용된 누수인지는 저장소 주인만 안다.

---

## 7. 병렬 작업 충돌 매트릭스

이 세션에서 띄운 서브에이전트 6개는 **전부 완료**됐다. 현재 다른 에이전트가 잡고 있는 파일은 없다.
계획서를 서브에이전트로 실행할 경우의 소유권은 다음과 같다:

| 파일 | Task | 동시 편집 위험 |
|---|---|---|
| `codegraph/measure_citation_origin.py` | 1 | 없음(신규) |
| `codegraph/roslyn-dump/Program.cs` | 2 | 없음 |
| `codegraph/verify_citations.py` | 3 | ⚠ **Task 1 도 이 모듈을 import 한다** — 순서대로 |
| `codegraph/facts.py` | 4, 6 | ⚠ **두 Task 가 같은 파일** — 반드시 순차 |
| `codegraph/warmup.py` | 5 | 없음(신규) |
| `codegraph/test_normalize.py` | 1~6 전부 | ⚠ **모든 Task 가 끝에 추가한다** — 병렬 금지 |

**결론: 이 계획은 병렬 실행에 맞지 않는다.** `test_normalize.py` 와 `facts.py` 가 여러 Task 에
걸쳐 있어 순차가 안전하다. 서브에이전트를 쓰더라도 **Task 하나씩** 돌리고 사이에 검토한다.

---

## 8. 포인터

| 문서 | 역할 |
|---|---|
| `docs/handoffs/HANDOFF-codebase-wiki.md` | **Track C 정본.** 결정 C-1~C-18 · Phase 0~11 · 스키마 §7 · 인용 검증 §8 |
| `docs/superpowers/plans/2026-08-28-llm-load-reduction.md` | **다음 작업.** Task 1~8, 실측 근거 M1~M5 |
| `docs/handoffs/DECISION-csharp-intermediate-format.md` | `roslyn-dump.json` 형식 F1~F14 + 구현 노트 |
| `docs/handoffs/HANDOFF-cpp-pattern-collection.md` | C++ 수집 기록 + **§0-1 "⏳ C++ 쪽 미완" 5건** |
| `docs/handoffs/HANDOFF-unity-roslyn-dump-v2.md` | C# 살(멤버·메서드) 확장 기록 |
| `docs/handoffs/HANDOFF-*-boundary-rules.md` | 경계 규칙 선언 인계(사용자 판정 대기) |
| `samples/cpp/OBSERVATION.md` · `samples/csharp-unity/OBSERVATION.md` | 수집 관찰 보고서 A~I |

⚠ `DECISION-cpp-symbol-index.md` 는 🔴 **SUPERSEDED** 배너가 붙어 있다 — 따르지 말 것.
⚠ `HANDOFF-clangd-reverse-refs.md` 는 **보류 + 산출물 낡음** 표시가 붙어 있다.

---

## 9. 변경 이력 (append-only)

- **2026-08-28** — 이 문서 작성. C# 갈래 완주(위키 10장 · 인용 745/745 · Mermaid 치환 실패 0),
  회귀 테스트 28개, LLM 부담 감축 계획 8 Task 수립. 미커밋 9항목 존재.
