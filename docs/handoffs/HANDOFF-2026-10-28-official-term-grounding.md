# HandOff - 추론 없는 공식 개발 도메인 용어 근거 스킬 (영어 개발 용어 → 한국어 개발 용어)

> 작성 2026-10-28 · 받는 쪽 : 이 스킬을 설계 · 구현할 Claude Code 에이전트 - 이 문서만 보고 시작할 수 있게 썼다
> 성격 : 원 프로젝트 제품 코드와 무관한 **개발 도구 (Claude Code 스킬)** 일. 원 프로젝트 저장소에서 작업 후기를 쓰다 문제가 드러나 여기에 기록함
> 근거 : 10/28 사용자와의 대화 (1절 원문 표, 2절 분석, 3 ~ 5절 리서치). 리서치 출처는 11절에 빠짐없이
> 승인 : **9절 사용자 결정을 받기 전 · 0 단계 확인 전에는 데이터를 내려받거나 스킬 파일을 만들지 않는다**
> 이 사본 : 받은 원본에서 원 프로젝트 고유 내용 (프로젝트 · 저장소 이름, 문서 경로, 프로젝트 개념어 예, 분야 이름) 만 "원 프로젝트" 로 일반화했다 - 이 저장소가 공개 저장소라서 (사용자 결정 2026-10-28). 나머지는 받은 그대로다. 받은 뒤의 0 단계 결과와 사용자 결정은 같은 폴더의 `RESUME-2026-10-28-official-term-grounding.md`

---

## 0. 한 줄과 핵심 결론

LLM 이 개발 문서를 한국어로 쓸 때 낱말을 **추론 (감각)** 으로 고르면 오역 · 직역 · 사적인 비유 · 과한 줄임이 섞인다. 이 스킬은 낱말 선택의 근거를 **실측** 으로만 내놓는다.
- **① 공식 권위 출처** (기계가 읽을 수 있는 공식 용어집)
- **② 사용 빈도 말뭉치** (공개 한국어 개발 문서에서 센 개수)

**리서치 결론 (10/28) : 이 조건을 만족하는 기성 스킬 · MCP 는 없다** (4절). 통과하는 것은 **자료** 뿐이고 (5절), 자료를 묶어 실측을 보장하는 스킬은 새로 만들어야 한다.

**역할 분담 (사용자 결정 10/28)**

| # | 무엇 | 누구 |
|---|---|---|
| ① | 권위 출처 실측 | **스킬이 보장** |
| ② | 사용 빈도 말뭉치 실측 | **스킬이 보장** |
| ③ | 팀 · 선임이 실제 쓰는 어휘, 프로젝트 고유 뜻 | 사용자 책임 (스킬 밖) |
| ④ | 판정 순서 (출처가 엇갈릴 때 무엇을 이기게 하나) · 강제 도구 (금지어 검사) | 사용자 책임 (스킬 밖) |

## 1. 문제를 만난 순간 (원문)

10/28, 작업 후기 (코드 읽기 방식) 를 정리하던 중 사용자가 "트리면 트리로 번역해야지 트리가 아니라", "입장권도 entry 같은 건가" 라고 짚었다. 그때 내가 (Claude) 고친 표가 아래다. 사용자가 이 문서에 넣으라고 준 그대로다.

| 전 | 종류 | 관행어 |
|---|---|---|
| 트리 (호출하는 쪽 · 불리는 쪽) | 오역 | **호출 트리** (호출자 caller · 피호출자 callee) |
| 입장권 | 내 비유 | **필수 입력 · 전제 조건 (prerequisite)** |
| 부작용 | **오역** - 프로그래밍에서 side effect 는 "부수 효과" | **부수 효과 (side effect)** |
| 층 · 위층 · 아래층 | 직역 | **레이어 · 상위 / 하위 레이어** |
| 노드 (파이프라인 안에서) | 그래프 용어를 섞음 | **스테이지 (stage)** |
| 제품 · 시험 | 직역 | **프로덕션 코드 · 테스트 코드** |
| 줄 · 칸 | 직역 | **라인 · 픽셀** |
| 그림 (호출 · include) | 직역 | **호출 그래프 (call graph) · include 의존성 그래프** |
| 데이터 길 하나 | 내 비유 | **데이터 흐름 추적 (data flow tracing)** |
| 의존 방향 | 줄인 말 | **의존성 방향 (dependency direction)** |
| 식은 한 곳 / 설계의 틈 | 내 비유 | **단일 진실 공급원 (SSOT) / 중복 코드 (code smell)** |
| 형제 모듈 · 선례 따르기 | 내 말 | **기존 구현 패턴 · 컨벤션 (convention) 따르기** |
| 실측으로 좁히기 | 내 말 | **과학적 디버깅 (scientific debugging) · 이분 탐색 (bisect)** |
| 금지 간선 검사 | 내 말 | **레이어 위반 검사 (layering violation check)** |
| 모양이 바뀌나 | 내 비유 | **데이터 표현 (representation) · 타입이 바뀌나** |
| 반복 단위 | 직역 | **처리 단위 (granularity)** |
| 끊는 게 있나 | 내 비유 | **비동기 · I/O 경계가 있나** |
| 떼어 볼 수 있나 | 내 비유 | **독립적으로 테스트할 수 있나 (testability)** |
| 결과를 정하는 것이 모두 인자 | 풀어 쓴 말 | **결정적 (deterministic) - 숨은 의존성 · 전역 상태 없음** |
| 출구에서 약속을 검사 | 내 비유 | **사후 조건 (postcondition) 검증** |
| 약속 (함수) | 내 비유 | **인터페이스 (interface)** |
| 같이 바뀌나 | 줄인 말 | **변경 이유가 같은가** (단일 책임 SRP · 공통 폐쇄 CCP) |
| 한쪽만 아나 | 내 비유 | **의존성이 단방향인가** (순환 의존 없음) |

같은 정정 때 원래 표에 함께 있던 나머지 행 (손실 없이 남김) :

| 전 | 종류 | 관행어 |
|---|---|---|
| 간선 | 교과서 번역어 (틀리진 않음) | **엣지 (edge)** - 실무 관행 |
| 쓰는 곳 · 읽는 곳 | 풀어 쓴 말 | **쓰기 참조 · 읽기 참조 (write / read reference)** |
| 구조로 찾기 | 풀어 쓴 말 | **구조 검색 (structural search, AST 기반)** |
| 값의 주소 (좌표) | 풀어 쓴 말 | **인덱싱 체계 (좌표계)** |
| 체스터턴의 울타리 | - | 그대로 (정착된 번역어) + 영문 병기 (Chesterton's Fence) |
| 스무고개 | 사용자 비유 | **체크리스트** (제목) |

"입장권" 에 대한 사실 : `compile_commands.json` 의 정식 이름은 **컴파일 데이터베이스 (JSON Compilation Database)**, 그 안의 번역 단위 하나하나의 기록이 **엔트리 (entry)**. 내가 뜻한 말은 entry 가 아니라 "다른 도구가 돌려면 먼저 있어야 한다" = **필수 입력 · 전제 조건 (prerequisite)**.

**이 문제의 바탕 :** 원 프로젝트 문서에서 쉬운 한국어 낱말 (줄 · 칸 · 시험) 을 쓰던 습관이 일반 개발 글에까지 넘어왔다. 그리고 같은 대화 안에서도 "간선" 과 "엣지" 를 오갔다 - 근거 없는 선택은 세션 · 대화마다 흔들린다.

## 2. 분석 - 원인 분류 · 내가 어떻게 고쳤나 · 용어집이 어디까지 막나

### 2-1. 원인 분류 (용어학 · 번역학 · 의사소통 이론 기준)

| # | 원인 | 이번 예 | 이론적 근거 | 막는 장치 |
|---|---|---|---|---|
| A | **한 낱말에 여러 뜻** (다의 · 동음이의) | "채널" = 원 프로젝트 안의 두 뜻, "부작용" = 의학 뜻 / side effect | 단의성 원칙 - 한 용어 = 한 개념 (Wüster, ISO 704). 의미 삼각형 - 기호 · 개념 · 대상이 사람마다 다르게 이어짐 (Ogden & Richards 1923) | 정의 + 맥락 (Bounded Context) |
| B | **한 뜻에 여러 낱말** (동의어 난립 · 표기 흔들림) | 간선 / 엣지, "단일 진실 공급원 / 원천" | ISO 704 일관성 원칙. 통제 어휘의 우선어 · 비우선어 (USE / UF) 관계 (ISO 25964) | 용어집의 쓰는 말 / 쓰지 않는 말 |
| C | **사적인 말 · 비유** (개인어) | 입장권, 떼어 볼 수 있나, 약속 | ISO 704 투명성 원칙. 개인어 (idiolect) 대 실천 공동체 (community of practice) 공용어. Grice 의 방식 격률 - 모호함 · 불분명함을 피하라 (1975) | 규칙 · 검사 |
| D | **직역 · 간섭** (차용 번역 · 거짓 짝) | 트리 ← tree, 층 ← layer, 시험 ← test | 번역의 간섭 법칙 (Toury 1995). 자국화 대 이국화 (Venuti 1995) - 한국 개발 공동체는 구조 이름에서 이국화 (음차) 가 규범 | 공동체 관행 (음차 / 정착 번역어) 확인 |
| E | **과한 줄임** (경제성 > 투명성) | 의존 방향, 식은 한 곳 | ISO 704 언어 경제성 ↔ 투명성 충돌. 지식의 저주 (Camerer · Loewenstein · Weber 1989) | 첫 등장에 정식 이름 + 영어 병기 |
| F | **개념 관계 손실** (요약 중 위계 · 관계가 뒤틀림) | 좌표 · 반복 단위를 "간선" 아래에 둠, "결정을 숨긴다" → "만든다" | ISO 704 개념 체계 (상하 · 부분 관계). Weaver 의 의미 수준 잡음 (B 수준 문제, 1949) | 정의에 관계를 적음 |

통째로 막도록 설계된 실례 : 항공 정비 문서 통제 언어 **ASD-STE100 (Simplified Technical English)** - 허용 낱말 목록 + "한 낱말 한 뜻" 으로 A · B · C · E 를 막음.

이론 짝의 범위 메모 : Evans 의 **Ubiquitous Language** (*Domain-Driven Design*, 2003) 는 **프로젝트 개념어** (원 프로젝트의 개념어) 통일에만 들어맞는다 - 도메인 개념을 말 · 문서 · 코드 이름에 같게, 맥락이 갈리면 Bounded Context. **일반 개발 어휘의 번역 · 표기** (트리, 부수 효과, 엣지) 는 DDD 가 아니라 **용어 관리 (terminology management)** 분야 (ISO 704, 교환 형식 TBX = ISO 30042) 의 일이다. 이 스킬은 뒤쪽이다.

### 2-2. 내가 (LLM) 어떻게 고쳤나 - 그리고 왜 그것이 문제인가

용어마다 네 단계를 거쳤다.
1. **역번역** : "이 한국어로 뜻한 영어 원어는?" - 원어가 없으면 내 비유 → 그 개념의 정식 이름으로.
2. **음차냐 번역어냐** : 구조 · 부품 이름은 음차가 관행 (트리 · 레이어 · 스테이지 · 엣지), 원칙 · 이론 이름은 정착된 한자어 (정보 은닉 · 부수 효과 · 순환 의존 · 사후 조건), 제품 화면 이름은 그 제품 한국어 UI.
3. **일상어 충돌 검사** : 부작용 (일상 = 약의 adverse effect), 시험 (exam), 층 (floor).
4. **첫 등장 영어 병기.**

**한계 (이 스킬이 필요한 까닭) :** 위 판단은 사전을 찾은 것이 아니라 내가 학습한 한국 개발 글의 감각이다. 그래서 확신이 낮은 곳이 남았다.
- SSOT : "단일 진실 공급원" 과 "단일 진실 원천" 이 둘 다 쓰임 - 무엇이 많은지 모름
- edge : "간선" 과 "엣지" - 같은 대화 안에서도 흔들림
- VS 한국어 UI 의 "호출 계층 구조" (Call Hierarchy) - 확인 안 함

### 2-3. 용어집 (DB) 가 막는 범위

| 갈래 | DB 로 막나 | 비고 |
|---|---|---|
| B 표기 흔들림, D 직역 | ✅ | 용어집이 채워지면 해결 |
| A 다의 | △ | 낱말 대응만으론 안 됨 - 정의 · 맥락까지 |
| C 비유, E 줄임, F 관계 손실 | ❌ | 번역이 아니라 글쓰기 문제 - 규칙 · 검사 (④ 사용자 몫) |

**더 큰 위험 :** DB 를 누가 어떤 근거로 채우나. LLM 이 채우면 그것도 추론이다 → 이 스킬의 존재 이유.

## 3. 사용자 요구 (10/28 원문 요지)

* "LLM 판단이 아니라 **실측** 을 통해서 단어 선택을 유도해야 한다"
* "DB 와 용어집을 반드시 **Official** 하고, 그것을 통해 개발자 도메인의 영역 단어를 가져올 수 있어야 한다"
* "③ ④ 는 사용자가 해야 하는 책임인 것을 인지하고 있으니, ① 권위 출처 & ② 사용 빈도 말뭉치를 확실하게 실측할 수 있는 자료로 해소할 수 있게 **보장되어야 하는 Skill**"

## 4. 리서치 - 기성 스킬 · 도구 : **통과하는 것 없음**

기준 = ① 공식 · 기계가 읽는 권위 출처를 담거나 조회하는가, ② 셀 수 있는 사용 빈도 말뭉치를 담거나 세는가. 아래는 모두 **둘 다 ✗** 라서 탈락. (각 SKILL.md 본문 전체를 읽은 것은 아님 - 검색 결과 · 미러 페이지로 확인. 쓰려면 직접 받아 읽을 것)

| 후보 | 무엇 | ① | ② | 탈락 까닭 · 메모 |
|---|---|---|---|---|
| **lqez/korean-technical-writing** (SKILL.md) | 한국어 기술 글쓰기 스킬. 검토 모드에 "한 개념에 여러 이름" 짚기, 내부 은어 · 즉흥 비유보다 널리 쓰는 기술 표현 권장 | ✗ | ✗ | 규칙 수준 (C · B) - 판단은 LLM. ④ 의 글쓰기 규칙으로는 빌려 쓸 만함 |
| **daleseo/korean-skills** (MIT) | `humanizer` · `grammar-checker` (맞춤법 · 띄어쓰기 · 문장부호, 표준 규칙) · `style-guide` (여러 문서 사이 문체 일관성 - 국립국어원 지침 · 대학 논문 기준 · 카카오엔터프라이즈 기술 글쓰기 가이드 참고). 설치 `npx skills add daleseo/korean-skills@<name>` | ✗ | ✗ | 문체 · 맞춤법. 용어 대응 DB 아님 |
| **terrylica/cc-skills - glossary-management** (doc-tools 플러그인) | 전역 `~/.claude/docs/GLOSSARY.md` 중심, 훅 2 개 (GLOSSARY 편집 시 · 프로젝트 CLAUDE.md 편집 시 용어 병합 · 충돌 표시), `bun ~/.claude/tools/bin/glossary-sync.ts` 가 `.vale/` 아래 Vale 치환 규칙 · 어휘 파일 생성. 주의 : `.vale.ini` 의 glob 은 현재 폴더 기준 | ✗ | ✗ | ④ 강제 장치. 내용은 사용자가 채움. **skills.sh 의 Socket 점검 (2026-02-28) 이 HIGH "Malware" 경고 1 건 · 실패 표시** (점검자는 목적과 일치한다고 적음), ClaudSkills 정적 점검은 위험 없음 - 설치 전 코드 검토 필수. `bun` 필요 |
| **Locize MCP (`get_glossary`)** | 다국어화 (i18n) 서비스의 승인 용어를 코딩 에이전트가 꺼냄. 프로젝트 전체 일관성 검사 (용어집에 없는데 다르게 번역된 용어 찾기) | ✗ | ✗ | 사용자 용어집 전달 통로. 외부 서비스 - 회사 문서 송신 |
| **DeepL 용어집 + MCP 조합** (사례 글) | PDF 명세 용어를 용어집 없이 번역하자 일본어 번역이 흔들림 → 명세 조회 MCP 의 정의 추출 도구로 용어집을 채우는 사례 | ✗ | ✗ | 사례. 외부 서비스 |
| **Metabase MCP glossary 도구** (PR #82696) | MCP 서버에 용어 조회 도구 추가 (대소문자 무시) | ✗ | ✗ | 자기 제품 용어 조회 |
| **ko-en-translator** (claudskills) | 기술 문서 특화 한영 양방향 번역 | ✗ | ✗ | 용어 관리 기능 확인 안 됨 |
| **translate** (skillstore, fuhehe12) | 문서 번역, 여러 파일 일괄 번역 때 용어 통일 | ✗ | ✗ | 통일 근거가 LLM |
| **glossary-builder** (claudeskills.info, pm-claude-skills) | 제품 핵심 용어를 번역 사이에 통일 | ✗ | ✗ | 용어집 작성 보조 |
| **learning-glossary-management** (skills.lc / claudskills) | 교육 콘텐츠 다국어 용어집 · 번역 메모리 | ✗ | ✗ | 교육 분야 |
| **engineering-terminology** (skills.sh, shino369) | 영 · 일 · 번체 중국어 공학 용어 | ✗ | ✗ | 한국어 없음 |
| **translator** (claude-skills-tutorial, oh-my-agent 등) | 언어별 규칙 (예 : 중국어는 API · SDK 영어 유지) | ✗ | ✗ | 규칙 수준 |
| **korean-technical-terminology** (voidmatcha, skillsmp 목록) | 기계 번역 같은 기술 용어를 검토 · 수정 | ✗ | ✗ | 저장소 원본 확인 못함 |
| **korean-writer** (alpoxdev/hypercore), **korean-writing-quality-standards** (mcpmarket) | 한국어 글쓰기 | ✗ | ✗ | 문체 |
| dotnetpower/fdai PR #2176 | 한국어 기술 교정 순서 (정확성 · 자연스러운 한국어 · 용어 · 확실성) | ✗ | ✗ | 다른 프로젝트 내부 지침 |
| **textlint + textlint-rule-prh** (npm 6.1.0) | 표기 흔들림 교정 사전 (prh.yml, `--fix` 지원), 일본어 프리셋 (kufu/smarthr) 이 선례 | ✗ | ✗ | 한국어 기술 용어 prh 사전은 찾지 못함. **이 PC 에는 node 없음** |
| **이 환경의 `humanize-korean` 플러그인** | 한국어 AI 문체 · 번역투 윤문 | ✗ | ✗ | 내용 · 용어를 건드리지 않는 설계 |

공식 지침 메모 : Anthropic 의 *Skill authoring best practices* 도 "한 용어를 골라 스킬 전체에서 그것만 쓰라, 동의어를 섞으면 Claude 가 지시를 해석하기 어려워진다" 고 적는다 - 이 스킬 자신의 SKILL.md 도 이를 따를 것.

## 5. 리서치 - 통과하는 자료

### 5-1. ① 권위 출처

| 자료 | 판정 | 확인한 사실 (10/28) |
|---|---|---|
| **Microsoft Terminology Collection** (TBX) | ✅ **통과** | **직접 확인** : Learn 공식 페이지 (`ms.date` 2023-06-06, `updated_at` 2024-05-02) 의 다운로드 링크 `MicrosoftTermCollection.zip` 이 살아 있음 - `curl -I` 결과 **HTTP 200, Content-Length 176,156,561 B, application/octet-stream, Last-Modified 2025-02-06 12:32:16 GMT**. 같은 페이지에 조회 화면 Microsoft Terminology Search (Power BI) 링크. 형식 TBX (ISO 표준 교환 형식), 약 100 개 언어, 한국어 (`ko`) 포함. 범위 = MS 제품 UI · IT 용어 |
| (참고) Hugging Face `microsoft/ms_terms` | 데이터 사본 **아님** | **직접 확인** : 파일은 `.gitattributes` · `README.md` · `ms_terms.py` (불러오기 스크립트) 뿐. 스크립트는 `MicrosoftTermCollection.tbx` 를 손으로 받아 넣으라 함 ("go to https://www.microsoft.com/en-us/language/terminology, and manually download the language of your interest"). 파싱 구조 : `termEntry` → `langSet` 2 개 (원어 · 대상어) → `term` (용어) · `descrip` (정의) · `termNote` (품사). 라이선스 태그 `ms-pl`, 본문 "See the Microsoft Language Portal Materials License and the Microsoft Terms of Use". 2024-01-18 갱신, 내려받기 39.0K |
| TTA 정보통신용어사전 (terms.tta.or.kr) | △ **조건부** | 국가 표준 기관 TTA 가 1993 년부터 운영, 표준 용어 · 시사 용어 · TTA 표준 용어로 구분, 2023 국가 지식정보 자원 지정, K-Knowledge 에서도 제공, 의견 제출 가능. **공식 기계 접근 (API) 확인 안 됨** - 공공데이터포털 등록 여부 미확인, 비공식 Ruby 클라이언트 `tta_terms_api` 만 보임. 표준어 위주라 실무 음차와 다를 수 있음 → 손 조회 + URL · 날짜 기록 방식으로만 근거 |

### 5-2. ② 사용 빈도 말뭉치 (공개 저장소 - 커밋을 고정해 셀 수 있음)

| 저장소 | 판정 | 확인한 사실 · 주의 |
|---|---|---|
| `kubernetes/website` 의 `content/ko` | ✅ | 한글화 가이드 (용어 한글화 일반 방침 · 한영 병기 대상 · API 오브젝트 용어 방침 · 용어집) 와 모범 사례 문서가 있음. 클라우드 분야 |
| `mdn/translated-content` 의 `files/ko` (추정 경로) | ✅ | MDN 공식 번역 원본 저장소, 한국어 이슈 라벨 `l10n-ko`, MDN 은 8 개 로캘, 한국어 관리자 명시. 웹 분야. **`files/ko` 구조는 확인 안 됨** |
| `python/python-docs-ko` | ✅ (최신성 확인 필요) | 현재 · 가까운 안정판만 번역. 미러 정보 : 마지막 push 2025-04, 번역은 3.9 브랜치, master 는 지원 파일 - **낡았을 수 있음**. 2018 년 Flowdas (오동권) 가 한국어 번역 조정자 제안 |

**웹 검색 결과 수는 빈도로 쓰지 않는다** (재현 · 신뢰 불가). 저장소를 받아 grep 으로 센다.

### 5-3. ① ② 에서 뺀 것 (의견 · 원칙 - 판단의 참고만)

| 자료 | 성격 |
|---|---|
| 서울대 이광근 연구실 "쉬운 전문용어" (easyword.kr) | 쉬운 우리말 용어 제안 - 순우리말 쪽이라 이번 정정 방향 (트리 → 트리) 과 반대일 수 있음 |
| KAIST 프로그래밍 시스템 연구실 `prosyslab/pl-wiki` "번역 용례" | 원칙 : 어색하게 꾸며낸 순우리말을 피함, 번역을 대충 하지 않음, 일상어를 적극 씀. 프로그래밍 언어 분야. 목록 본문은 확인 못함 |
| UbuCon Korea 2024 발표 (번역 기여) | 번역 모임의 용어집 주제, KAIST 자료 · Microsoft 언어 자료 소개 |
| Koreabulary-LLM (11mLLM) | 프롬프트 엔지니어링 가이드 한국어 번역 기여자 용어집 - 목록 확인 못함 |
| 인프런 블로그 "컴퓨터/IT 용어, 한국어로는 어떻게 옮길까?" · tilnote GitHub 용어 풀이 | 블로그 |

### 5-4. 실측해도 남는 빈칸

* **분야 편향** : 말뭉치가 웹 · 클라우드 · Python. 원 프로젝트 분야의 용어는 셀 거리가 적을 수 있음.
* **범위** : MS 용어집은 제품 UI 위주 - 설계 개념 (SSOT, postcondition …) 이 없을 수 있음.
* 그래서 **"근거 없음" 이 반드시 나온다.** 그때 LLM 이 빈칸을 채우지 않고 "근거 없음" 을 그대로 내놓는 것 자체가 실측 결과다.

## 6. 스킬이 보장해야 할 것 (요구 사항)

| # | 보장 | 뜻 |
|---|---|---|
| G1 | **추론 금지** | 답의 모든 행은 출처 데이터에서 나온다. 근거가 없으면 `근거 없음` - 추측 · 그럴듯한 번역으로 채우지 않는다 |
| G2 | **고정된 스냅숏 · 재현성** | MS zip 은 SHA-256 · Last-Modified (2025-02-06) 를, 말뭉치는 저장소 커밋 SHA 를 매니페스트에 적는다. 같은 질문 + 같은 매니페스트 = 바이트까지 같은 답 |
| G3 | **근거 행 꼴** | 한 행 = `원어 · 한국어 후보 · 출처 · 근거 (TBX 항목 id / 파일:줄 · 개수) · 스냅숏 id`. 한국어 후보 자체를 어디서 얻었는지도 적음 (7-2) |
| G4 | **범위 표시** | 결과마다 "이 출처가 이 분야를 덮나" 를 적음 (예 : MS 에 항목 없음 = MS 범위 밖일 수 있음) |
| G5 | **판정하지 않음** | 여러 후보 중 무엇을 쓸지는 ④ (사용자 판정 순서) 의 일. 스킬은 근거를 정렬해 보여 줄 뿐 고르지 않는다 (판정 순서를 사용자가 주면 그대로 적용만) |
| G6 | **오프라인 · 로컬** | 회사 문서 · 질문을 외부 서비스로 보내지 않는다. 데이터는 로컬에 받아 둠 |

## 7. 설계 안 (받는 쪽이 정함 - 근거와 함께 바꿔도 됨)

### 7-1. 구성

```
<스킬 폴더>/                 (위치는 9절 결정 - 사용자 전역 ~/.claude/skills/ 또는 프로젝트 .claude/skills/)
  SKILL.md                   추론 금지 · 출력 꼴 · "근거 없음" 규칙 · 사용법
  manifest.json              출처마다 URL · SHA-256 · 크기 · Last-Modified · 커밋 SHA · 받은 날
  scripts/fetch.*            MS zip · 말뭉치 sparse clone (ko 폴더만) - 매니페스트와 대조, 다르면 멈춤
  scripts/build_index.*      TBX (ko) → en→ko 표 (CSV 또는 SQLite), 말뭉치 → 검색용 텍스트
  scripts/query.*            원어 하나 → 근거 행들 (G3)
  data/                      내려받은 원본 · 색인 (git 밖, 큼)
```

### 7-2. 꼭 풀어야 할 설계 문제

1. **한국어 후보를 어디서 얻나 - 여기서 추론이 새기 쉽다.** 빈도를 세려면 후보 (트리 / 트리) 가 먼저 있어야 한다.
   - (a) MS TBX 의 한국어 대상어 - 결정적
   - (b) 말뭉치의 **한영 병기 패턴 추출** - 한국어 문서는 흔히 `파드(Pod)` · `트리 (tree)` 꼴로 원어를 병기함 → 정규식으로 `<한글 낱말>\s*\(\s*<원어>\s*\)` 를 뽑으면 후보와 개수가 함께 결정적으로 나옴
   - (c) 사용자가 준 후보
   - (d) LLM 이 낸 후보 - 허용한다면 반드시 `후보 출처 = LLM (추론)` 표시, 개수가 0 이면 그대로 0 으로 보고
   - 권하는 순서 : (a) + (b) 기본, (c) 추가, (d) 는 표시 붙여서만
2. **한국어 경계 문제** - 단순 부분 문자열 세기는 틀린다 : `트리` ⊂ `트리거`, `층` ⊂ `계층`, `엣지` ⊂ `엣지케이스`. 앞은 한글이 아니고 뒤는 조사 (을 · 를 · 이 · 가 · 의 · 에 · 와 · 과 · 로 · 으로 · 은 · 는 · 도 · 만 …) 또는 한글이 아닌 글자일 때만 세는 규칙 + 표본 검사로 정밀도 확인.
3. **TBX 크기 · 구조** - zip 176 MB 안에 언어별 TBX 가 들었는지 하나인지 **미확인** (8 절 V1). 한국어만 뽑아 색인.
4. **말뭉치 범위** - 코드 블록 · front matter 를 셀지 뺄지 (빼는 쪽 권함 - 산문 용례만).
5. **이 PC 환경** - Windows 11, Git Bash + PowerShell 5.1 (한글 경로가 든 ps1 은 UTF-8 BOM 필요), `python` · `uv` 있음, **node 없음** (textlint 계열은 못 씀). 큰 파일은 저장소 밖.

### 7-3. 출력 예 (꼴만 - 값은 지어낸 것이 아니라 자리 표시)

```
edge (그래프)
  MS TBX ko      : <term> (항목 <id>, 정의 "<descrip>")         | 스냅숏 ms-2025-02-06 sha256:<…>
  병기 추출      : 엣지(edge) <n>, 간선(edge) <m>                | k8s@<sha>, mdn@<sha>
  낱말 개수      : 엣지 <n1> · 간선 <m1>  (경계 규칙 v1)         | k8s@<sha>, mdn@<sha>, pydocs@<sha>
  범위           : MS = UI 용어 (그래프 이론 항목 없을 수 있음)
  판정           : 하지 않음 (④ 사용자 판정 순서 없음)
SSOT
  MS TBX ko      : 근거 없음
  병기 추출      : 근거 없음
  …
```

## 8. 진행 순서

| 단계 | 할 일 | 끝 조건 |
|---|---|---|
| **0 확인 (V)** | 아래 미확인 사항을 먼저 실측 - 데이터는 아직 쌓지 않음 | 표의 칸이 모두 사실로 채워짐 |
| 1 | 9절 결정 받기 (라이선스 수락 · 위치 · 말뭉치 범위 · 후보 (d) 허용 여부) | 사용자 답 |
| 2 | fetch + 매니페스트 (G2) | 두 번 받아도 해시 같음 |
| 3 | 색인 (TBX ko → 표, 말뭉치 정리) | 원어 하나 손 조회 결과와 색인 결과가 같음 |
| 4 | 조회 · 세기 (7-2 의 1 · 2) | 경계 규칙 표본 검사 (예 : `트리` 100 건 중 `트리거` 0) |
| 5 | SKILL.md (G1 ~ G6) | 공식 *Skill authoring best practices* 를 따름 |
| 6 | **시범** : 1절 두 표의 원어 전부를 돌림 | 행마다 근거 또는 `근거 없음`, 범위 표시, 두 번 돌려 같음, 표본 5 행을 원본 (TBX 항목 · 말뭉치 줄) 과 손 대조 |
| 7 | 시범 결과를 사용자에게 - ③ ④ 를 정할 재료로 | 사용자 확인 |

**0 단계 확인 목록**

| # | 확인할 것 | 방법 |
|---|---|---|
| V1 | MS zip 안에 한국어 TBX 가 있나, 언어별 파일인가 하나인가 | 내려받아 목록만 (또는 HTTP Range 로 zip 끝 central directory 만 읽기) |
| V2 | MS 용어집 라이선스 원문 (Microsoft Language Portal Materials License · Terms of Use) - 내부 도구에 저장 · 가공해도 되나 | 원문 확인 → 9절에서 사용자 수락 |
| V3 | `mdn/translated-content` 의 한국어 폴더 구조, `kubernetes/website` 의 `content/ko` 크기 | 저장소 트리 확인 |
| V4 | `python/python-docs-ko` 의 현재 번역 브랜치 · 마지막 갱신 | 저장소 확인 (미러 정보 2025-04 는 낡았을 수 있음) |
| V5 | TTA 정보통신용어사전의 공식 기계 접근 (Open API · 내려받기) 이 있나 | terms.tta.or.kr · data.go.kr 직접 확인. 없으면 손 조회 근거로만 |
| V6 | 4절 후보 가운데 빌려 쓸 것 (예 : lqez 글쓰기 규칙) 이 있다면 SKILL.md · 스크립트 본문 직접 읽기 | 본문 검토 (terrylica 는 보안 경고 때문에 특히) |

## 9. 사용자 결정 (받는 쪽이 묻고 받아야 할 것)

| # | 물을 것 | 기본안 |
|---|---|---|
| D1 | MS 용어집 라이선스 (V2 결과) 수락 | 원문을 보여 주고 받음 |
| D2 | 스킬 위치 - 사용자 전역 (`~/.claude/skills/`) 또는 특정 프로젝트 (`.claude/skills/`) | 전역 (일반 개발 어휘라 프로젝트 무관). 데이터 폴더는 git 밖 |
| D3 | 말뭉치 범위 - 쿠버네티스 · MDN · Python 셋 다, 또는 일부 + 추가 (예 : 원 프로젝트 분야의 한국어 자료가 있으면) | 셋 다로 시범 |
| D4 | 한국어 후보 (d) LLM 후보 허용 | 표시 붙여서만 허용 |
| D5 | ④ 판정 순서를 스킬에 넣을지 | 넣지 않음 (G5) - 사용자가 주면 적용만 |

③ (팀 · 선임 어휘, 프로젝트 고유 뜻) 은 이 스킬이 다루지 않는다. 원 프로젝트의 개념어 통일 예는 원 프로젝트 저장소의 별도 문서에 있고 이 저장소에는 옮기지 않았다.

## 10. 하지 말 것

* 근거가 없을 때 LLM 판단으로 빈칸 채우기 (G1) - "근거 없음" 이 정답
* 웹 검색 결과 수를 빈도로 쓰기
* 버전 · 해시 없이 출처 쓰기 (G2)
* 회사 문서 · 질문을 외부 번역 · 용어 서비스 (Locize · DeepL 등) 로 보내기 (G6)
* 보안 경고가 있는 스킬 (terrylica glossary-management) 을 코드 검토 없이 설치
* ③ ④ 를 에이전트가 정하기
* 받은 데이터 (176 MB zip · 말뭉치 clone) 를 원 프로젝트 저장소에 넣기
* 용어 판단 (어느 한국어가 맞나) 을 이 HandOff 의 1절 표로 확정 짓기 - 1절 표는 **LLM 감각으로 고친 것** 이라 시범의 입력이지 정답이 아니다

## 11. 출처 (10/28 리서치 전부)

**직접 확인한 것**
- [Microsoft Terminology - Globalization (Learn, ko-kr)](https://learn.microsoft.com/ko-kr/globalization/reference/microsoft-terminology) - 페이지 본문 확인
- [MicrosoftTermCollection.zip (Microsoft Download Center)](https://download.microsoft.com/download/b/2/d/b2db7a7c-8d33-47f3-b2c1-ee5e6445cf45/MicrosoftTermCollection.zip) - `curl -I` 로 200 · 176,156,561 B · 2025-02-06 확인 (10/28)
- [microsoft/ms_terms (Hugging Face)](https://huggingface.co/datasets/microsoft/ms_terms) - 파일 목록 · `ms_terms.py` 본문 확인
- Microsoft Terminology Search (Power BI) - 위 Learn 페이지의 링크 : `https://msit.powerbi.com/view?r=eyJrIjoiODJmYjU4Y2YtM2M0ZC00YzYxLWE1YTktNzFjYmYxNTAxNjQ0IiwidCI6IjcyZjk4OGJmLTg2ZjEtNDFhZi05MWFiLTJkN2NkMDExZGI0NyIsImMiOjV9`

**① 권위 출처 관련 (검색 결과 · 미러)**
- [MicrosoftDocs/globalization - microsoft-terminology.md (GitHub)](https://github.com/MicrosoftDocs/globalization/blob/main/globalization/reference/microsoft-terminology.md?plain=1)
- [Microsoft language resources (Learn)](https://learn.microsoft.com/en-us/globalization/reference/microsoft-language-resources)
- [Microsoft Terminology (Learn, ja-jp)](https://learn.microsoft.com/ja-jp/globalization/reference/microsoft-terminology)
- [Microsoft Terminology (microsoft.com, ja-jp)](https://www.microsoft.com/ja-jp/language/Terminology)
- [Redesigned Microsoft Language Portal - terminology downloads (2010 블로그 보관)](https://learn.microsoft.com/en-us/archive/blogs/terminology/redesigned-microsoft-language-portal-features-terminology-downloads)
- [ProZ 포럼 - Microsoft Language Portal no longer available?](https://bel.proz.com/forum/internet_for_translators/337918-microsoft_language_portal_no_longer_available.html)
- [MS 한국어 TBX 를 탭 구분으로 바꾸기 (thewordcracker)](https://www.thewordcracker.com/en-us/how-to-convert-tbx-glossary-into-tab-delimited-format/)
- [Microsoft Terminology Collection - Language Unlimited](https://www.languagesunlimited.com/microsoft-terminology-collection/)
- [Soluling - Terminology, termbases and glossaries](https://www.soluling.com/Help/Terminology.htm)
- [TermBase eXchange (Wikipedia)](https://en.wikipedia.org/wiki/TermBase_eXchange)
- [MultiTerm (Wikipedia)](https://en.wikipedia.org/wiki/MultiTerm)
- [TTA 정보통신용어사전 (BARTOC)](https://bartoc.org/en/node/20286)
- [TTA 관련 2024 논문 요약 (용어사전 운영 · 지정)](https://d2j16w31g89z0j.cloudfront.net/site/2024s/abs/0810-PCTXF.pdf)
- [정보통신용어사전 활용도 기사 (디지털타임스)](https://www.dt.co.kr/article/10521760)
- [공공데이터 이용가이드 (data.go.kr)](https://www.data.go.kr/ugs/selectPublicDataUseGuideView.do)
- [tta_terms_api (비공식 Ruby gem)](https://www.rubydoc.info/gems/tta_terms_api/0.0.2)

**② 말뭉치 관련**
- [쿠버네티스 한글화 모범 사례](https://www.kubernetes.io/ko/docs/contribute/localization_ko_best_practice/)
- [쿠버네티스 문서 한글화 가이드](https://www.kubernetes.io/ko/docs/contribute/localization_ko/)
- [mdn/translated-content (ecosyste.ms)](https://awesome.ecosyste.ms/projects/github.com%2Fmdn%2Ftranslated-content)
- [MDN Web Docs localization](https://developer.mozilla.org/docs/MDN/Contribute/Localize)
- [python/python-docs-ko (GitHub)](https://www.github.com/python/python-docs-ko)
- [python-docs-ko (ecosyste.ms 미러)](https://repos.ecosyste.ms/hosts/GitHub/repositories/python/python-docs-ko)
- [Doc-SIG - Korean translation coordination (2018)](https://www.python.org/pipermail/doc-sig/2018-January/003996.html)

**의견 · 원칙 자료 (5-3)**
- [UbuCon Korea 2024 번역 기여 발표](https://speakerdeck.com/studioego/ubucon-korea-2024-beonyeog-giyeoneun-eoddeohge-hago-isseulggayo-rinugseu-20nyeonjjae-sayongjaga-iyagihaneun-bof)
- [KAIST 프로그래밍 시스템 연구실](https://pl.kaist.ac.kr/) - 번역 용례 = `github.com/prosyslab/pl-wiki` (본문 미확인)
- 서울대 "쉬운 전문용어" - `easyword.kr`
- [Koreabulary-LLM (GitHub)](https://www.github.com/11mLLM/Koreabulary-LLM)
- [컴퓨터/IT 용어, 한국어로는 어떻게 옮길까? (인프런)](https://www.inflearn.com/blogs/3872)
- [GitHub 용어 풀이 (tilnote)](https://tilnote.io/pages/69b2600316b42015402bf1ea)

**4절 스킬 · 도구 후보**
- [lqez/korean-technical-writing SKILL.md](https://github.com/lqez/korean-technical-writing/blob/main/SKILL.md)
- [daleseo/korean-skills - humanizer (agskills.dev)](https://agskills.dev/daleseo/korean-skills/humanizer)
- [daleseo/korean-skills - grammar-checker (skills.sh)](https://www.skills.sh/daleseo/korean-skills/grammar-checker)
- [glossary-management (skills.sh)](https://www.skills.sh/terrylica/cc-skills/glossary-management)
- [glossary-management 보안 점검 (skills.sh / Socket)](https://skills.sh/terrylica/cc-skills/glossary-management/security/socket)
- [glossary-management (agent-skills.md)](https://agent-skills.md/skills/terrylica/cc-skills/glossary-management)
- [glossary-management (claudepluginhub)](https://claudepluginhub.com/skills/terrylica-doc-tools-plugins-doc-tools/glossary-management)
- [glossary-management (ClaudSkills)](https://claudskills.com/skills/glossary-management/)
- [glossary management vale integration (mcpmarket)](https://mcpmarket.com/tools/skills/glossary-management-vale-integration)
- [vale (ClaudSkills)](https://claudskills.com/skills/vale/)
- [vocab-drift-audit (nolte)](https://nolte.github.io/claude-shared/skills/nolte-shared/vocab-drift-audit/)
- [Locize - TBX / UTX](https://www.locize.com/file-formats/tbx-utx)
- [Locize - translation glossary](https://www.locize.com/blog/translation-glossary)
- [DeepL 용어집 + MCP 사례](https://www.deepl-bridges.com/developers/made-with-deepl/post/from-bulk-translation-to-terminology-consistency-using-deepl-glossaries-dsXXCaWo92axmXs)
- [ComLogos - Terminology Database for AI Translations](https://comlogos.com/en/technology/terminology-database/)
- [metabase PR #82696 - MCP glossary tool](https://github.com/metabase/metabase/pull/82696)
- [ko-en-translator (ClaudSkills)](https://claudskills.com/skills/ko-en-translator/)
- [translate (skillstore)](https://skillstore.io/ko/skills/fuhehe12-translate)
- [glossary-builder (claudeskills.info)](https://claudeskills.info/skill/glossary-builder/)
- [learning-glossary-management (skills.lc)](https://skills.lc/pauljbernard/content/pauljbernard-content-archive-old-content-directory-2025-11-06-content-claude-skills-learning-glossary-management-skill-md)
- [learning-glossary-management (ClaudSkills)](https://claudskills.com/skills/learning-glossary-management/)
- [engineering-terminology (skills.sh)](https://www.skills.sh/shino369/claude-code-personal-workspace/engineering-terminology)
- [translator SKILL.md (claude-skills-tutorial)](https://github.com/foreveryh/claude-skills-tutorial/blob/main/.claude/skills/translator/SKILL.md)
- [Translator - Context-Aware (oh-my-agent, skills.lc)](https://www.skills.lc/first-fluke/oh-my-agent/first-fluke-oh-my-agent-agents-skills-translator-skill-md)
- [Translation skill (skillsdirectory)](https://www.skillsdirectory.com/skills/seb1n-translation)
- [Claude skills for translation (Pairaphrase)](https://www.pairaphrase.com/blog/claude-skills-for-translation)
- [korean-technical-terminology (skillsmp, voidmatcha)](https://skillsmp.com/creators/voidmatcha/dotfiles/plugins-local-skills-skills-korean-technical-terminology)
- [korean-writer (skills.sh, alpoxdev)](https://www.skills.sh/alpoxdev/hypercore/korean-writer)
- [korean-writing-quality-standards (mcpmarket)](https://mcpmarket.com/tools/skills/korean-writing-quality-standards)
- [dotnetpower/fdai PR #2176](https://github.com/dotnetpower/fdai/pull/2176)
- [vincentkoc/dotskills](https://github.com/vincentkoc/dotskills)
- [textlint-rule-prh (GitHub)](https://github.com/textlint-rule/textlint-rule-prh)
- [textlint-rule-prh (npm)](https://www.npmjs.com/package/textlint-rule-prh)
- [kufu/textlint-rule-preset-smarthr](https://www.github.com/kufu/textlint-rule-preset-smarthr)

**스킬 작성 공식 문서**
- [Skill authoring best practices (Claude Platform Docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Glossary (Claude Code Docs)](https://code.claude.com/docs/en/glossary)
- [Claude Code 스킬 해설 (한국어 정리)](https://mygithub05253.github.io/Claude-Code-Study/skills/)

**이론 문헌 (2절 - URL 없음)**
- ISO 704 (Terminology work - Principles and methods), ISO 25964 (Thesauri and interoperability), ISO 30042 (TBX)
- Eugen Wüster - 일반 용어학 이론 (단의성)
- C. K. Ogden & I. A. Richards, *The Meaning of Meaning* (1923)
- H. P. Grice, "Logic and Conversation" (1975)
- Gideon Toury, *Descriptive Translation Studies and Beyond* (1995)
- Lawrence Venuti, *The Translator's Invisibility* (1995)
- Camerer, Loewenstein & Weber, "The Curse of Knowledge in Economic Settings" (1989)
- Warren Weaver, "Recent Contributions to the Mathematical Theory of Communication" (1949)
- ASD-STE100 Simplified Technical English
- Eric Evans, *Domain-Driven Design* (2003) - Ubiquitous Language · Bounded Context
