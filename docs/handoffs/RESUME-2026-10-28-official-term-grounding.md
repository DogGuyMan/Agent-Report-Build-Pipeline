# 재개 — 공식 용어 근거 스킬 (Mode 1.5 강화 갈래) · 0단계 확인

> 2026-10-28 · 클라우드 세션 · 받은 인계 문서 "HandOff - 추론 없는 공식 개발 도메인 용어 근거 스킬" 을 받아 0단계를 돈 기록
> 받은 인계 문서 본문 — 같은 폴더의 [`HANDOFF-2026-10-28-official-term-grounding.md`](HANDOFF-2026-10-28-official-term-grounding.md). 공개 저장소라 원 프로젝트 고유 내용만 일반화한 사본이다(사용자 결정)
> **데이터 내려받기와 스킬 파일은 아직 없다.** 받은 인계 문서의 승인 조건(9절 결정 전 · 0단계 확인 전에는 만들지 않는다)을 지켰다. 9절 결정은 받았다(4절)
> **구체화 계획 [제안됨]** — [`docs/superpowers/plans/2026-10-28-ko-dev-terms.md`](../superpowers/plans/2026-10-28-ko-dev-terms.md). 사용자 승인 전에는 실행하지 않는다

아래 "8절 · 9절 · 7-2" 같은 절 번호는 전부 받은 인계 문서의 절이다.

## 1. 사용자가 인계하며 덧붙인 것 (2026-10-28 원문)

> Mode 1.5를 강화 하기 위한 새로운 아이디어다.
> Mode 1.5가 사용자의 용어 이해도를 측정하는것이지.
> 하지만 만약, 사용자가 공식 용어를 알고 있었고, 개발 용어를 잘 알고 있었지만
> 서술이나, AI의 오역, 만들어진 단어, 직역으로 단어를 관리하고 있었다면
> 이거는 Mode 1 에서도 크나큰 해악인것이다.
>
> 코드베이스 그래프를 그리는 상황에서 만약 주석, 설명이 이상한 단어라
> 개발자 도메인에서 의사소통에 악영향을 미치는 치명적인 이슈가 있을것이다.
>
> 그래서 실측가능한 단어집, 용어집에 대한 DB를
> ① 권위 출처 & ② 사용 빈도 말뭉치 : 이 부분에 대해서는 보장하는 Skill이 필요한 상황이다.
>
> 다음
> ③ 팀의 실제 사용과 결정 ( 팀 · 선임의 선호는 사용자만 줄 수 있음)
> ④ 판정 규칙 + 강제 도구
> 추가로 더 해야 하는것은 (사용자의 언어 사용 경향성과, 사용자 자의로 만든 비유와 해석 마치 LLM 에이전트에게 발생되는 문제를 반대로 사람이 수행하고 있다면? 에 대한 해법)
> ⑤ 사용자 개인 언어 Node와 실제 단어집에서 의미하는, 말하고 싶었던 언어 가중치 그래프를 그리는 랭기지 모델 가중치 학습 그래프가 필요할 수 있다
>
> 예를 들어 사용자가
> C# 에서 객체 다중 상속 하는 기법 (사용자 만의 어휘) -> C# 여러 인터페이스 구현 (실제 실측된 공식 언어)
>
> 이런식으로 Mapping 하기 위한 가중치 그래프를 학습하는 내용도 필요할 것 같지만
> 이번 단계는 아니니 노트만 확실히 적는식으로

⑤ 는 [결정 0013](../decisions/0013-personal-language-graph-deferred.md) 에 보류로 적었다. 이 갈래에서 만드는 것은 ①② 뿐이다.

## 2. 0단계 확인 결과 (V1 ~ V6)

전부 이 세션에서 돌린 명령의 출력이거나 이 세션에서 읽은 원문이다. 재현 명령은 6절.

| # | 결과 | 확인한 사실 |
|---|---|---|
| V1 | ❌ **확인 못 함** | 이 클라우드 세션의 네트워크 정책이 `download.microsoft.com` 을 막는다(프록시 CONNECT 403). zip 끝 central directory 를 HTTP Range 로 읽는 방법은 호스트만 열리면 그대로 쓸 수 있다 |
| V2 | △ **부분** | 아래 2-1 |
| V3 | ✅ | 아래 2-2 |
| V4 | ✅ — 받은 인계 문서의 "번역은 3.9 브랜치 · 마지막 push 2025-04" 는 **낡았다** | 아래 2-3 |
| V5 | ❌ **확인 못 함** | `terms.tta.or.kr` 이 이 세션의 허용 도메인 밖이다(이름 풀이 실패). 웹 검색 1회로 공식 Open API 를 찾지 못했다 — 보인 것은 비공식 Ruby gem `tta_terms_api` 뿐. `data.go.kr` 은 시도하지 않았다. 결론은 받은 인계 문서와 같다 — 손 조회 + URL · 날짜 기록으로만 근거 |
| V6 | ✅ | 아래 2-4 |

같은 차단에 걸린 호스트: `download.microsoft.com` · `learn.microsoft.com` · `huggingface.co` · `terms.tta.or.kr`.
`learn.microsoft.com` 의 쪽은 Microsoft Learn MCP 도구로는 읽혔다. GitHub 공개 저장소는 익명 git 읽기로 열린다.

### 2-1. V2 — Microsoft 용어집 라이선스

- Learn 의 terminology 쪽(`/en-us/globalization/reference/microsoft-terminology`) 본문에는 라이선스 문장이 없다.
  조회 화면 링크와 zip 내려받기 링크뿐이다.
- 같은 사이트의 License agreement 쪽(`/en-us/globalization/license-agreement`, "Microsoft Learn Globalization License")이
  "documentation, terminology and other product information" 을 Globalization Materials 로 묶는다. 원문에서 이 갈래에 걸리는 문장:
  - 1.1 — "Microsoft grants you a non-exclusive, nontransferable, royalty-free, license to use, copy, and distribute the Globalization Materials."
    배포할 때 조건 넷. 그중 고지문 — "Entry from Microsoft Learn's Globalization Essentials. © 2023 [or applicable year] Microsoft Corporation. All rights reserved."
  - 2 — "You may not (i) publish the Globalization Materials for others to copy; or (ii) sell, rent, lease or lend the Globalization Materials in whole."
  - 서두 — "unless we have provided more specific terms, in which case those more specific terms will apply to the relevant item."
    **zip 안에 더 구체적인 약관이 들어 있는지는 V1 이 막혀 모른다.**
- 받은 인계 문서가 적은 이름 "Microsoft Language Portal Materials License" 의 원문은 찾지 못했다(웹 검색 1회).

### 2-2. V3 — 말뭉치 둘

| 저장소 @ 커밋 (커밋 날짜) | 한국어 폴더 | 크기 | 확인한 것 |
|---|---|---|---|
| `kubernetes/website` @ `ed70e311` (2026-10-26) | `content/ko` | 849 파일 (md 594 · yaml 216 · html 18 · 그림 12) · 디스크 9.1 MB · md 합 99,035 줄 · 4,865,722 B | 한글화 가이드 `content/ko/docs/contribute/localization_ko.md` · `localization_ko_best_practice.md` 실재. 용어집 `content/ko/docs/reference/glossary/` 124 파일. 저장소 `LICENSE` 첫 줄 "Attribution 4.0 International" |
| `mdn/translated-content` @ `2a7c03a4` (2026-10-27) | `files/ko` — 받은 인계 문서의 "추정 경로" 가 맞다 | 3,349 파일 · 디스크 37 MB · md 합 352,890 줄 · 16,065,848 B | 하위 폴더 중 `glossary` md 564 · `conflicting` 71 · `orphaned` 8 (뒤 둘은 이름만 봤다 — 뜻은 확인하지 않음). 산문 라이선스 CC-BY-SA 2.5 (`LICENSE.md`) |

두 용어집 폴더의 파일 안 꼴(한국어 제목과 영어 원어가 어떻게 들어 있는가)은 열어 보지 않았다.

### 2-3. V4 — `python/python-docs-ko`

| 브랜치 | 마지막 커밋 |
|---|---|
| `master` (기본) | `57e56ff` 2025-05-11 "remove TRANSLATORS" |
| **`3.14`** | `242bdce` **2026-10-03** "#1127 translate library/string.templatelib.po" |
| `3.13` | `3d98d1a` 2025-10-11 |
| `3.9` | `dada548` 2023-09-23 |
| `3.6` · `3.7` · `3.8` | 2018 ~ 2020 |

`3.14` 은 `.po` 523 파일 · 디스크 29 MB · `msgid` 줄 81,809.

**새로 드러난 것 — 용어 단위의 원문 · 번역 쌍이 있다.** `glossary.po` 의 항목이 영어 용어와 한국어 번역을 짝으로 갖는다:

```
glossary.po:58   msgid "abstract base class"
glossary.po:59   msgstr "abstract base class (추상 베이스 클래스)"
glossary.po:132  msgid "argument"
glossary.po:133  msgstr "argument (인자)"
```

7-2 의 1번(한국어 후보를 어디서 얻나)에 결정적인 출처가 하나 더 생긴다 — (a) MS TBX · (b) 병기 패턴 추출 옆의
"번역 프로젝트 용어집의 원문 · 번역 쌍". 문서 본문의 `.po` 는 문장 단위 짝이라 낱말 대응을 뽑는 방법은 따로 정해야 한다.

### 2-4. V6 — 빌려 쓸 후보

- `lqez/korean-technical-writing` @ `1a2e11f` (2026-09-25), MIT, `SKILL.md` 185 줄. 받은 인계 문서의 판정 그대로 규칙 수준이고 판단은 LLM 이다.
  ④(사용자 몫)의 재료로 쓸 만한 문장 — §6 "**용어집이 있으면 그것이 정본이다.** … 용어집 다음은 코드다. 코드에 존재하는 심볼, 설정 키, 파일명, 공식 용어가 있으면 임의의 동의어보다 우선한다."
- `terrylica/cc-skills` 의 glossary-management 는 읽지 않았다. ④ 의 강제 도구라 이 스킬 밖이고, 설치할 계획이 없다.

## 3. 0단계에서 드러난 설계 사실

1. **MS 원본과 그것으로 만든 색인은 공개 git 에 넣지 않는다.** 라이선스 2(i) 때문이다. 이 저장소는 공개 저장소다
   (GitHub 저장소 정보 `private: false`). 받은 인계 문서 7-1 의 "`data/` (git 밖)" 과 같은 결론이 라이선스에서도 나온다.
2. MS 항목을 인용한 근거 행을 커밋되는 산출물에 실으면 1.1 의 배포 조건이 걸릴 수 있다 — 근거 행 꼴(G3)에 고지문 자리를 둘지 정해야 한다.
   💭 근거 행 한 줄이 "배포" 에 해당하는지는 해석 문제라 사용자가 판단한다.
3. 후보 출처가 하나 늘었다 — 2-3 의 `glossary.po` 쌍.
4. MDN `files/ko` 의 `conflicting` · `orphaned` 를 셀지 정해야 한다.
5. 실행 환경이 둘이다. 받은 인계 문서 7-2 의 5번(Windows 11 · node 없음)은 사용자 PC 이야기다. 이 클라우드 세션은 Linux · node 있음 ·
   네트워크 정책이 Microsoft · Hugging Face · TTA 를 막는다. 2단계(fetch)를 어디서 돌리는가가 D2 와 함께 정해져야 한다 — 4-1 에서 정했다(출처에서 직접 받고 클라우드는 환경 캐시).
   💭 스크립트를 파이썬 표준 라이브러리만으로 쓰면 두 환경에서 다 돈다.

## 4. 9절 결정 (2026-10-28 사용자 답)

| # | 물은 것 | 답 |
|---|---|---|
| D1 | MS 용어집 라이선스 수락 | **조건부 수락.** zip 목록(V1)을 열 때 별도 약관이 나오면 그 원문을 보여 주고 다시 묻는다. 원본과 색인은 git 밖 |
| D2 | 스킬 위치 | **이 저장소 최상위 폴더 `ko-dev-terms/`** — Mode 를 개발하듯 자기 `CLAUDE.md` · 시험을 갖추고 게이트에 올린다. `SKILL.md` 는 폴더 안, `.claude/skills/ko-dev-terms` 링크로 보인다. 같은 날 답이 두 번 바뀌었다 — "사용자 전역만" → ".claude/skills 로 프로젝트의 root" → "새로운 스킬 프로젝트로 만들자 .claude/ 아래가 아니라 마치 Mode 개발하듯" |
| D3 | 말뭉치 범위 | 받은 인계 문서 기본안 — 셋 다(쿠버네티스 · MDN · Python). 0단계에서 셋 다 쓸 수 있음을 확인했다. 따로 묻지 않았다 |
| D4 | LLM 후보 허용 | **표시 붙여서만 허용.** 행마다 `후보 출처 = LLM (추론)`. 개수는 말뭉치에서 실측하고 0 이면 0 으로 보고한다 |
| D5 | ④ 판정 순서를 스킬에 넣을지 | **넣지 않는다.** 사용자가 10/28 역할 분담에서 ④ 를 스킬 밖으로 정했다. 따로 묻지 않았다 |

받은 인계 문서 본문을 공개 저장소에 둘지도 물었다 — 원 프로젝트 고유 내용만 일반화해 둔다.

### 4-1. 계획 전 구체화 (2026-10-28 두 번째 · 세 번째 질의)

사용자가 이 갈래의 목적을 다시 적었다(원문):

> 이 저장소에서 지금 현재 Mode 1.5 에만 귀속된게 아니라. Mode 전반적으로 사용하게 될 Skill 제작이고, 이 프로젝트에서 진행하게 된 계기는 현재 프로젝트가 가장 필요할것 같은 스킬이며 컨택스트 자료도 많기에 여기서 진행 및 구체화 하는것 뿐이다 -> 그렇다면 원래 이상적인 사용 사례는? 바로 어떤 컴퓨터 에서든 사용가능한 Skill로서 만드는것, 범용적인 목적이 되는것이 그렇고
> 이 skill이 곧 Agent-Report-Build와 CodeBase LLM Wiki 툴 제작에 구체화 될것으로 보인다. 그러면 176 MB 및 말뭉치를 지금 클라우드 세션이나 공간에 캐싱하기 위해서는 어떻게 하는게 좋겠느냐? 즉 private와 라이선스 문제를 해결하면서 지금 이 프로젝트에 다운로드 과정이 장애물이 되지 않게끔 하려면?

| 축 | 답 |
|---|---|
| 범위 | 독립 스킬까지 — Mode 1.5 · 2 · 위키 연결은 시범 뒤 따로 |
| 조회 방향 | 영어 → 한국어만 |
| 코드 자리 | 새 스킬 프로젝트 — 이 저장소 최상위 폴더, 다른 축을 import 하지 않는다 (D2 행) |
| 캐시 | 출처에서 직접 받는다. 공개 저장소에는 매니페스트만. 클라우드는 환경 캐시 — 설정 스크립트가 약 5분 안에 끝나면 스냅숏해 약 7일 재사용한다(클라우드 환경 문서) |
| 프로젝트 용어집 셋(쿠버네티스 · MDN · Python) | ① 권위 출처로 표시 |
| 이름 | `ko-dev-terms` |

같은 질의 사이에 리서치로 확인한 것 — 쿠버네티스 · MDN 용어집도 머리말에 영어 · 한국어 짝을 갖는다
(`title: 어피니티 (원문, Affinity)` · `id: affinity`, `title: 콜백 함수` · `slug: Glossary/Callback_function`).
`pyright strict` 와 `pytest` 는 `.claude/` 아래를 보지 않는다(`pyrightconfig.json` 의 `include` · pytest 가 모은 시험 0개).

## 5. 다음 할 일

1. 사용자가 계획서 [`2026-10-28-ko-dev-terms.md`](../superpowers/plans/2026-10-28-ko-dev-terms.md) [제안됨] 을 검토하고 승인한다.
2. 승인 뒤 계획서 8절 V1 부터 — Microsoft 가 열린 곳(로컬, 또는 허용 도메인에 `download.microsoft.com` 을 더한 클라우드)에서.
3. 계획서 9절의 측정 여섯(M1 ~ M6)은 실행하며 잰다.
4. 리서치 보고서 둘의 후보(K1 ~ K12 · E1 ~ E13)를 사용자가 고른다 — 계획서 12절. 같은 날 사용자가 정한 방향(무게는 언어 불문 설계 · 소프트웨어 공학 어휘, 프레임워크 종속 용어집은 권하지 않음, 범위는 국제 표준 어휘 + 사용자 목록)은 계획서 1절에 옮겼다.

## 6. 0단계 재현 명령

빈 작업 폴더에서 돌린다. `--filter=blob:none --no-checkout` 은 커밋과 트리만 받는다. 크기를 잴 때만 한국어 폴더를
sparse checkout 했고, 잰 뒤 지웠다 — 데이터로 쌓지 않았다.

```bash
curl -sSI https://download.microsoft.com/download/b/2/d/b2db7a7c-8d33-47f3-b2c1-ee5e6445cf45/MicrosoftTermCollection.zip
```

```bash
git clone -q --filter=blob:none --no-checkout --depth 1 https://github.com/kubernetes/website k8s
git -C k8s ls-tree -r --name-only HEAD content/ko | wc -l
```

```bash
git clone -q --filter=blob:none --no-checkout --depth 1 https://github.com/mdn/translated-content mdn
git -C mdn ls-tree -r --name-only HEAD files/ko | wc -l
```

```bash
git ls-remote --heads https://github.com/python/python-docs-ko
```

```bash
git clone -q --depth 1 https://github.com/lqez/korean-technical-writing lqez
```
