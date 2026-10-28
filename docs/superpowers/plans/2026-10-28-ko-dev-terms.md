# 계획 — `ko-dev-terms` : 영어 개발 용어 → 한국어 표기 근거 스킬

> **상태 [제안됨]** · 2026-10-28 · 실행 전 구체화. 사용자 승인 전에는 실행하지 않는다
> 사양 원본: [`docs/handoffs/HANDOFF-2026-10-28-official-term-grounding.md`](../../handoffs/HANDOFF-2026-10-28-official-term-grounding.md) (아래 "인계 문서 n절" 은 이 문서의 절)
> 재개 진입점과 0단계 실측: [`docs/handoffs/RESUME-2026-10-28-official-term-grounding.md`](../../handoffs/RESUME-2026-10-28-official-term-grounding.md)

## 0. 한 줄

영어 개발 용어 하나를 넣으면, 기계가 읽은 출처에서 나온 한국어 표기 후보와 그 근거(출처 · 항목 id 또는 `파일:줄` · 개수 · 스냅숏)를 내놓는다.
**고르지 않는다.** 근거가 없으면 `근거 없음` 을 그대로 낸다.

이 저장소에서 만들지만 Mode 1.5 에만 딸린 것이 아니다. 어느 컴퓨터에서나 쓰는 범용 스킬이 목표이고,
뒤에 report-builder 와 코드베이스 위키 도구 양쪽에 쓰일 예정이다(사용자 진술 2026-10-28).

## 1. 정해진 것 (2026-10-28 사용자 답)

| 축 | 결정 |
|---|---|
| 범위 | **독립 스킬까지** — 인계 문서 8절 1~7단계. Mode 1.5 · 2 · 위키와의 연결은 시범 결과를 보고 따로 정한다 |
| 조회 방향 | **영어 → 한국어만.** 한국어 → 영어 역조회는 하지 않는다 |
| 자리 | **이 저장소 최상위 폴더 `ko-dev-terms/`** — Mode 를 개발하듯 자기 `CLAUDE.md` · `README.md` · 시험을 갖추고 게이트에 올린다. 나중에 떼어 내기 쉽게 저장소의 다른 축(`runner` · `machine` · `viz` · `tools`)을 import 하지 않는다. `SKILL.md` 는 폴더 안에 두고 `.claude/skills/ko-dev-terms` 링크로 보인다 |
| 이름 | **`ko-dev-terms`** — 폴더 이름이자 `SKILL.md` 의 `name` |
| 캐시 | **출처에서 직접 받는다.** 공개 저장소에는 매니페스트(URL · 해시 · 커밋)만 둔다. 클라우드는 환경 캐시(설정 스크립트 스냅숏) |
| 프로젝트 용어집 셋의 갈래 | **① 권위 출처** — 쿠버네티스 · MDN · Python 용어집. 행마다 출처 이름과 범위를 적는다 |
| MS 라이선스 (D1) | 조건부 수락. zip 안에서 별도 약관이 나오면 원문을 보이고 다시 묻는다 |
| 말뭉치 범위 (D3) | 쿠버네티스 · MDN · Python 셋 |
| LLM 후보 (D4) | 표시를 붙여서만 — `후보 출처 = LLM (추론)` |
| 판정 순서 (D5) | 스킬에 넣지 않는다 |

## 2. 출처

| 갈래 | 출처 | 스냅숏 고정 | 꺼내는 것 | 범위 표시 |
|---|---|---|---|---|
| ① | Microsoft Terminology Collection (TBX, `ko`) | zip URL · SHA-256 · Last-Modified | 영어 용어 → 한국어 용어 · 항목 id · 정의 | MS 제품 UI · IT 일반 |
| ① | 쿠버네티스 용어집 `content/ko/docs/reference/glossary/*.md` | 커밋 SHA | 머리말 `id` → `title` 의 한국어 | 클라우드 |
| ① | MDN 용어집 `files/ko/glossary/**/index.md` | 커밋 SHA | 머리말 `slug: Glossary/<영어>` → `title` | 웹 |
| ① | python-docs-ko `glossary.po` (브랜치 `3.14`) | 커밋 SHA | `msgid` → `msgstr` | Python |
| ② | 위 세 저장소의 한국어 본문 | 같음 | `한글(영어)` 병기 개수 · 후보 낱말 개수 | 웹 · 클라우드 · Python |
| — | TTA 정보통신용어사전 | 손 조회 URL · 날짜 | 사용자가 넣은 기록만 (공식 기계 접근을 찾지 못했다) | 표준어 |

**용어집 셋은 꼴이 서로 다르다** — 출처마다 따로 읽는다(2026-10-28 표본):

```
쿠버네티스  title: 어피니티 (원문, Affinity)          id: affinity
MDN         title: 콜백 함수                          slug: Glossary/Callback_function
MDN         title: 트리 셰이킹(Tree shaking)          slug: Glossary/Tree_shaking
Python      msgid "argument"                          msgstr "argument (인자)"
```

표본이 출처마다 2개뿐이다. 읽는 규칙은 3단계에서 실제 파일 전부에 돌려 예외를 센 뒤 정한다 — 합성 시험만으로 정하지 않는다.

## 3. 한국어 후보를 어디서 얻나 (인계 문서 7-2 의 1번)

| 기호 | 후보 출처 | 결정적인가 |
|---|---|---|
| (a) | MS TBX 의 한국어 대상어 | 예 |
| (b) | 말뭉치의 병기 패턴 `<한글 낱말>\s*\(\s*<영어>\s*\)` | 예 |
| (e) | 프로젝트 용어집 셋의 짝 — 인계 문서에 없던 출처, 0단계에서 찾았다 | 예 |
| (c) | 사용자가 준 후보 | 예 |
| (d) | LLM 이 낸 후보 — 행마다 `후보 출처 = LLM (추론)`, 개수는 실측, 0 이면 0 | 아니오 (표시) |

행마다 후보를 어느 출처에서 얻었는지 적는다(G3).

## 4. 세기 규칙 (인계 문서 7-2 의 2번 · 4번)

- **산문만 센다.** 빼는 것: 머리말, 코드 블록, 인라인 코드, Hugo shortcode `{{< … >}}`, MDN 매크로 `{{ … }}`, HTML 주석.
  `.po` 는 `msgstr`(번역문)만 세고 `msgid` 는 뺀다.
- **경계 규칙 v1** — 앞 글자가 한글이 아니고, 뒤가 조사이거나 한글이 아닐 때만 센다(`트리` ⊂ `트리거` · `층` ⊂ `계층` · `엣지` ⊂ `엣지케이스` 를 막는다).
  조사 목록은 코드가 아니라 리소스 파일에 둔다.
- **정밀도 표본 검사** — 시범 낱말마다 개수가 100 이상이면 무작위 100줄, 아니면 전부를 사람이 본다(인계 문서 8절 4단계의 예를 그대로 쓴다).
- MDN `files/ko` 의 `conflicting` · `orphaned` 는 빼는 것을 기본으로 한다. 바꿀 수 있다.

## 5. 출력 (G3 · G4 · G5)

- 한 행 = 원어 · 한국어 후보 · 출처 · 근거(TBX 항목 id / `파일:줄` · 개수) · 스냅숏 id · 후보 출처.
- 출처마다 범위를 적는다. 항목이 없으면 `근거 없음` 과 함께 "이 출처의 범위 밖일 수 있음" 을 적는다(G4).
- 맨 끝에 `판정 : 하지 않음` (G5).
- MS 행이 하나라도 있으면 라이선스 고지문 한 줄을 붙인다 — "Entry from Microsoft Learn's Globalization Essentials. © … Microsoft Corporation. All rights reserved."
- 행은 파이썬이 자료로 만들고, 글 꼴은 리소스 템플릿이 그린다(루트 `CLAUDE.md` 의 "리소스와 코드를 가른다").

## 6. 데이터와 캐시

**원칙 — 원본도 색인도 저장소 밖에 둔다.** git 에 들어갈 길을 처음부터 없앤다. MS 라이선스 2(i) 가 "publish … for others to copy" 를 막는다.

| 무엇 | 자리 | git |
|---|---|---|
| 매니페스트 `ko-dev-terms/manifest.json` | 출처마다 URL · 크기 · SHA-256 · Last-Modified · 커밋 SHA · 받은 날 | 추적 |
| 받은 원본 · 색인 | 환경 변수 `KO_DEV_TERMS_DATA`. 없으면 OS 캐시 폴더 — Linux · Mac `~/.cache/ko-dev-terms`, Windows `%LOCALAPPDATA%\ko-dev-terms` | 밖 |

**받기(fetch)** — 매니페스트와 대조하고 다르면 멈춘다(G2).

- MS: zip 을 받아 SHA-256 을 대조하고, 한국어 TBX 만 꺼낸다. zip 을 남길지는 V1 에서 안의 구조를 본 뒤 정한다.
- 말뭉치: `git clone --filter=blob:none --no-checkout` + 한국어 폴더만 sparse checkout + 매니페스트의 커밋으로 checkout.
- **GitHub 아카이브 URL(`codeload.github.com`)은 쓰지 않는다.** 클라우드의 GitHub 프록시가 세션에 붙이지 않은 저장소의 아카이브를 공개 저장소라도 403 으로 막는다(클라우드 환경 문서의 GitHub proxy 절). 익명 git 읽기는 열려 있다.

**클라우드** — 사용자가 환경 설정에서 두 가지를 한다:

1. Network access 를 Custom 으로 두고 Allowed domains 에 `download.microsoft.com` 을 더한다("Also include default list" 는 켜 둔다).
2. 설정 스크립트(`tools/cloud_env.sh` 가 원본)에 받기를 더한다.

설정 스크립트가 약 5분 안에 끝나면 파일 시스템이 스냅숏되고, 약 7일 동안 새 세션이 그것으로 시작한다.
5분을 넘기면 캐시되지 않는다 — 그때는 MS 받기만 SessionStart 훅의 배경 작업으로 옮긴다(문서가 권하는 길).

**로컬** — 처음 한 번 받고, 그 뒤 조회는 오프라인이다(G6).

## 7. 폴더 구성 (제안)

```
ko-dev-terms/
  CLAUDE.md            모듈 나침반
  README.md            gen_readme 가 소스에서 생성
  SKILL.md             G1 ~ G6 · 출력 꼴 · "근거 없음" 규칙 · 사용법
  manifest.json        스냅숏 고정값
  resources/           조사 목록 · 출력 템플릿 · 고지문
  ko_dev_terms/        파이썬 패키지 — 받기 · 출처별 읽기 · 색인 · 세기 · 조회
  test_*.py            시험은 모듈 옆에 (machine/ 와 같은 관례)
.claude/skills/ko-dev-terms -> ../../ko-dev-terms
```

- **파이썬 표준 라이브러리만** 쓴다 — 어느 컴퓨터에서나 돈다(`zipfile` · `xml.etree.ElementTree.iterparse` · `re` · `json` · `hashlib` · `urllib.request` · 자식 프로세스 `git`). 최소 판은 Windows PC 의 판을 확인한 뒤 정한다.
- 출처는 꼴마다 함수 하나다. 출처 레지스트리 · 플러그인 구조 · 추상 인터페이스를 두지 않는다 — 구현자 1 · 소비자 1(루트 `CLAUDE.md` 의 거울 함정).

**게이트에 올리기**

| 게이트 | 할 일 |
|---|---|
| pytest | 최상위 폴더라 저절로 모인다(`.claude/` 아래였다면 모이지 않았다 — 0개 실측) |
| pyright strict | `pyrightconfig.json` 의 `include` · `extraPaths` 에 `ko-dev-terms` |
| 인용 검사 | `test/test_docs_citations.py` 의 `contextDocs()` 에 `ko-dev-terms/CLAUDE.md` · `ko-dev-terms/SKILL.md` |
| 리소스와 코드 | `test/test_prompt_resources.py` 의 긴 글 검사 범위에 `ko-dev-terms` |
| README 표류 | `tools/gen_readme.py --check` 인자에 `ko-dev-terms` — 그 도구가 이 폴더 꼴을 읽는지 먼저 본다 |
| 격리 | `ko-dev-terms` 가 `runner` · `machine` · `viz` · `tools` 를 import 하지 않는다는 시험 (선례 `runner/test_import_isolation.py`) |

## 8. 단계 — 인계 문서 8절을 이 결정에 맞춘 것

| 단계 | 할 일 | 끝 조건 |
|---|---|---|
| V1 | MS 가 열린 곳(로컬 또는 허용 도메인을 더한 클라우드)에서 zip 목록과 안의 약관 파일을 본다. 약관이 있으면 원문을 사용자에게 보이고 D1 을 다시 묻는다 | 목록이 사실로 채워짐 |
| 2 | 매니페스트 + 받기 + 클라우드 설정 스크립트 | 두 번 받아도 해시가 같다. 설정 스크립트 시간을 잰다 |
| 3 | 색인 — MS TBX `ko` · 용어집 셋 → 영어 → 한국어 표 | 원어 다섯 개를 원본 파일을 열어 본 값과 색인 결과가 같다. 용어집 셋의 꼴 예외를 센다 |
| 4 | 세기 — 병기 추출 · 낱말 개수 · 경계 규칙 v1 | 정밀도 표본 검사(4절) |
| 5 | `SKILL.md` + `.claude/skills` 링크 + 게이트 편입 | 새 게이트 초록. 기존 빨강 둘(위키 표류 · 층 분포)은 별개 |
| 6 | 시범 — 인계 문서 1절 두 표의 원어 | 행마다 근거 또는 `근거 없음` · 범위 표시 · 두 번 돌려 같음 · 표본 5행을 원본과 손 대조 |
| 7 | 시범 결과를 사용자에게 — ③④ 를 정할 재료 | 사용자 확인 |

**시범 원어 목록은 [제안됨] 으로 먼저 사용자에게 보인다.** 1절 표의 영어 병기에서 기계적으로 뽑고,
병기가 없는 행(예: `나무` · `입장권`)은 비워 둔 채 사용자가 채운다 — 입력 목록도 LLM 이 지어내지 않는다.

## 9. 실행할 때 재야 할 것 — 지금 모른다

| # | 무엇 | 왜 모르나 |
|---|---|---|
| M1 | zip 안의 구조(언어별 파일인가 하나인가)와 별도 약관 | 이 클라우드 세션에서 `download.microsoft.com` 이 막힌다 |
| M2 | MS 다운로드 시간 — 설정 스크립트 5분 안에 드는가 | 같은 이유 |
| M3 | 설정 스크립트가 돌 때 저장소 클론이 있는가 | 문서에서 찾지 못했다. 없으면 받기 코드를 설정 스크립트에 넣거나 `raw.githubusercontent.com` 에서 받는다 |
| M4 | GitHub 이 커밋 SHA 로 얕은 fetch 를 받아 주는가 | 돌려 보지 않았다 |
| M5 | Windows PC 의 파이썬 판 | 인계 문서는 "python 있음" 만 적는다 |
| M6 | 용어집 셋의 꼴 예외 | 출처마다 표본 2개만 봤다 |

## 10. 하지 않는 것

- 한국어 → 영어 역조회 (1절)
- Mode 1.5 · 2 · 위키 연결 (1절 — 시범 뒤 따로)
- 개인어 가중치 그래프 ⑤ — [결정 0013](../../decisions/0013-personal-language-graph-deferred.md)
- ④ 판정 순서 · 강제 도구 — 사용자 몫
- MS 원본 · 색인을 git 에 넣기
- 웹 검색 결과 수를 빈도로 쓰기
- 인계 문서 1절 표를 정답으로 쓰기 — 그 표는 LLM 감각으로 고친 것이라 시범의 입력이다

## 11. 새 구조 공개 (`design-decision-discipline` §2.5 · §2.7)

새 최상위 폴더 하나를 만든다.

| 항목 | 값 |
|---|---|
| 구현자 수 | 지금 0 → 1. 저장소에서 TBX · `.po` 를 읽는 파이썬을 찾았더니 0건이다(`termEntry` · `.tbx` · `msgstr` grep — 걸린 1건은 `runner/run_mode1_5.py` 의 `TermEntry` 형으로 무관) |
| 소비자 수 | 지금 0 — 범위가 독립 스킬이다. 예정 둘(report-builder · 코드베이스 위키)은 사용자 진술이고 측정이 아니다 |
| 삭제 시험 | 지우면 복잡도가 되살아나는 곳 0 — 소비자가 아직 없다 |
| 계획 문서와의 관계 | 인계 문서 7-1 은 스크립트를 스킬 폴더 안 `scripts/` 에 두었다. 2026-10-28 사용자 답으로 바뀌었다 — "새로운 스킬 프로젝트로 만들자 .claude/ 아래가 아니라 마치 Mode 개발하듯" |

축 선언 — 자리 · 이름 · 캐시 · 출처 분류 · 범위 · 조회 방향은 사용자가 하나씩 정했다.
남은 축은 데이터 폴더의 기본 위치(6절)와 출력 꼴의 세부(5절)다. 둘 다 이 문서의 제안이고 미결이다.
