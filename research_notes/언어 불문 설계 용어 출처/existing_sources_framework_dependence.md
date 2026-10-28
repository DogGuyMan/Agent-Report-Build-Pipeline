# ko-dev-terms 계획의 기존 출처 넷 — 플랫폼 종속도와 언어 불문 설계·SE 용어 적중

기준일 2026-10-28. 표지: 🔵 이번 세션에서 실제로 돌린 명령·읽은 파일 / 🟡 검색 결과 요약(snippet)만 / 💭 추론(정수는 확신도).

**탐침 목록(probe list)에 대해.** 아래의 "적중" 은 조정자(coordinator)가 고른 **63개 낱말**(side effect … pipeline)에 대한 것이다. 연구 도구일 뿐 정답(ground truth)이 아니다. 목록에는 `edge` · `node` · `tree` · `stage` · `layer` 처럼 여러 분야에서 쓰는 일반어가 섞여 있다. 그래서 "적중" 과 "의도한 설계 의미로 적중" 을 따로 센다.

**재현 정보.** 스크립트는 같은 폴더의 `scripts/` (조정자가 세션 임시 폴더에서 옮겨 왔다. 측정 결과 JSON 은 고정 커밋에서 다시 만들 수 있어 옮기지 않았다) 에 있다(`measure.py` 용어집·본문 측정, `classify.py` 갈래 나누기, `contexts.py` 문맥·느슨한 개수, `msxlsx.py` · `msdefs.py` · `msshare.py` MS 용어집). 첫 클론 디렉토리 `research-clones/` 는 측정 도중 다른 병렬 작업이 통째로 지웠다. 그래서 `research-clones-fwdep/` 에 **같은 커밋으로 고정해** 다시 받았고, 다시 돌린 결과는 첫 실행과 숫자 하나까지 같았다 🔵.

## Q1. 쿠버네티스 · MDN · python-docs-ko — 용어집 크기, 플랫폼 종속 비율, 탐침 적중, 본문 병기 개수

### Takeaway
세 저장소 용어집을 합쳐도 탐침 63개 중 **의도한 설계 의미로 들어 있는 것은 5개뿐이다**(전부 MDN: abstraction · encapsulation · idempotent · inheritance · polymorphism). 쿠버네티스 용어집은 1개(node, "작업 장비" 의미), Python 용어집은 1개(decorator, 언어 문법 의미)가 걸렸고 둘 다 동형이의(homonym)다. 본문에서 `한글(English)` 병기로 탐침 낱말이 나온 것도 저장소마다 14~19건이다. 각 저장소 병기 전체(약 2,500건)의 0.6~0.7% 에 그치고, **SOLID 다섯 원칙 · 의존성 주입 · 제어의 역전 · 관심사 분리(1건 제외) · 코드 스멜 · 바운디드 컨텍스트는 세 말뭉치 모두 0건**이다.

### Cited Findings

**측정 방법(결정적 기준)**
- 스냅숏은 다음과 같다 🔵. 쿠버네티스 `kubernetes/website` `ed70e311737a341574ed5758b7af24e3bba232cb`(2026-10-26, main, sparse `content/ko`) — [GitHub](https://github.com/kubernetes/website/tree/ed70e311737a341574ed5758b7af24e3bba232cb/content/ko/docs/reference/glossary). MDN `mdn/translated-content` `2a7c03a449507969b925ac954f41c340d7c50263`(2026-10-27, main, sparse `files/ko`) — [GitHub](https://github.com/mdn/translated-content/tree/2a7c03a449507969b925ac954f41c340d7c50263/files/ko/glossary). Python `python/python-docs-ko` `242bdce63d20a3042fa438fea9677f289d7a6d0c`(2026-10-03, 브랜치 `3.14`) — [GitHub](https://github.com/python/python-docs-ko/blob/242bdce63d20a3042fa438fea9677f289d7a6d0c/glossary.po).
- **용어집 적중 기준(결정적)**: 영어 표제를 정규화한 뒤(소문자화, `_` · `-` · `/` 를 공백으로, 끝의 `s`/`es` 제거) 탐침과 **완전 일치**할 때만 센다. 영어 표제는 쿠버네티스에서 `title` 의 `(원문, X)`(없으면 `id`), MDN 에서 `slug: Glossary/<X>` 의 첫 마디, Python 에서 `msgid` 다. 부분 포함(예: "Container Runtime Interface" ⊃ interface)은 따로 센다 🔵.
- **본문 병기 기준(결정적)**: 계획서 4절의 산문 규칙을 따랐다. 머리말, 코드 블록, 인라인 코드, Hugo shortcode, MDN 매크로, HTML 주석을 빼고, `.po` 는 `msgstr` 만 보며 rst 인라인 리터럴과 역할(role)도 뺀다. 그 위에 `한글 1~4어절 + 선택적 공백 + ( 탐침 영어[복수형 허용, 대소문자 무시] )` 를 센다. MDN 의 `conflicting` · `orphaned` 는 뺐다. 대상 파일은 쿠버네티스 `.md` 594개(산문 2,120,498자), MDN `.md` 3,266개(6,075,636자), Python `.po` 523개(`msgstr` 3,962,143자)다 🔵.
- **플랫폼 종속 판정(판단, 💭)**: 항목마다 네 갈래 중 하나로 나눴다. **S2** 는 언어 불문 설계·아키텍처·패턴·SE 공정 어휘, **S1** 은 언어 불문 일반 프로그래밍·CS 개념, **P** 는 제품·API 종류·표준·기관 이름이나 그 플랫폼이 정의한 메커니즘, **G** 는 나머지 일반 IT 분야 개념이다. P 판정에는 규칙을 썼다. 쿠버네티스는 `tags` 가 core-object · tool · community · workload · extension · operation 등이거나 CamelCase API 종류일 때, MDN 은 대문자 약어 · 브랜드 목록 · 웹 접두어(CSS/HTML/HTTP/Grid 등)일 때, Python 은 S1·S2 목록에 없는 나머지 전부다. S1·S2 목록은 손으로 정했다(`classify.py` 에 그대로 있다). **S2 와 S1 의 경계는 판단이다.** G 와 P 의 경계는 규칙이 거칠어서 오분류가 있다(예: MDN 의 CalDAV · XPath 가 G 로 들어갔다).

**쿠버네티스 용어집 `content/ko/docs/reference/glossary/*.md`**
- 항목은 **123개**다(`index.md` 제외). `tags` 분포는 fundamental 62 · core-object 26 · operation 18 · architecture 18 · extension 13 · community 11 · workload 10 · networking 9 · tool 7 · storage 7 · security 5 순이다 🔵 ([glossary 디렉토리](https://github.com/kubernetes/website/tree/ed70e311737a341574ed5758b7af24e3bba232cb/content/ko/docs/reference/glossary)).
- 갈래는 **P 105(85.4%) · G 10(8.1%) · S1 8(6.5%) · S2 0(0%)** 이다. S1 은 Garbage Collection · Object · Name · Namespace · Event · Logging · Proxy · uid, G 는 Affinity · Annotation · Applications · Disruption · Image · Label · Manifest · Node · Selector · Workload 다 🔵 측정 / 💭 판정 80.
- 탐침 완전 일치는 **1/63**(`node` → `노드`)이다. 정의는 "노드는 쿠버네티스의 작업 장비(worker machine)이다" 로 그래프의 노드(node) 의미가 아니다 🔵 ([node.md:2,6](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/content/ko/docs/reference/glossary/node.md)). 부분 포함은 6건으로 Aggregation Layer · CNI · CRI(2건) · CSI · Node-pressure eviction 이며, 전부 쿠버네티스 고유 명칭이다 🔵.
- **계획 밖의 같은 저장소 자원.** 한글화 가이드 `localization_ko.md` 에 "한글화 용어집" 표가 **257행** 있다. 탐침 완전 일치는 3개다 — `idempotent | 멱등성`(395행), `Node | 노드(Node) | API 오브젝트인 경우`(435행), `pipeline | 파이프라인`(448행). 같은 문서 155~171행은 용어 정책을 명시한다: 우선순위는 "한글 단어(순우리말 > 한자어·외래어) > 한영 병기(예: 훅(hook)) > 영어 단어", 한영 병기는 "페이지 내에서 처음 사용될 때 1회". 254~271행은 이 용어집이 "쿠버네티스 문서 한글화팀 회의를 통해 결정" 되며 툴팁용 `glossary` 와 "용도가 다르다" 고 적는다 🔵 ([localization_ko.md](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/content/ko/docs/contribute/localization_ko.md)).
- **본문 병기**는 탐침 **14건, 63개 중 7개 낱말**이다: node 6(`노드(Node)`, 전부 API 오브젝트·장비 의미), singleton 2(`싱글톤`), stage 2(`단계`), representation 1(`표현`), convention 1(`규칙`), separation of concerns 1(`관심사 분리`, `concepts/workloads/pods/_index.md`), idempotent 1(`멱등성`, `init-containers.md`). 같은 기준으로 센 `한글(영어)` 병기 전체는 2,515건이다 🔵.
- 참고로 한국어 후보를 접두 경계만 두고 센 원시 개수(뒤 경계가 없어 과다 집계됨)는 결합도 2 · 응집도 0 · 캡슐화 12 · 추상화 33 · 관심사 분리 2 · 의존성 주입 0 · 리팩터링 4 · 기술 부채 4 · 노드 3,156 이다 🔵.

**MDN 용어집 `files/ko/glossary/**/index.md`**
- 항목은 **564개**다(동음이의를 가르는 하위 폴더 포함 — `node/dom` · `node/networking` · `boolean/javascript` 등) 🔵.
- 갈래는 **P 325(57.6%) · S1 159(28.2%) · G 43(7.6%) · S2 37(6.6%)** 이다. S2 37개는 Abstraction · API · Camel case · CRUD · DSL(domain-specific language) · Encapsulation · Fork · Fuzzing · Graceful degradation · IDE · Idempotent · Information architecture · Inheritance · Kebab case · Middleware · Mixin · Modularity · MVC · Non-normative · Normative · OOP · Placeholder names · Polymorphism · Principle of least privilege · Progressive Enhancement · Prototype-based programming · Pseudocode · Repo · REST · SCM · SDK · Shim · Smoke Test · Snake case · Specification · State machine · Wrapper 다 🔵 측정 / 💭 판정 70.
- 탐침 완전 일치는 **6개 낱말, 8항목**이다: `abstraction → 추상화`, `encapsulation → 캡슐화 (Encapsulation)`, `idempotent → 멱등성`, `inheritance → 상속 (Inheritance)`, `polymorphism → 다형성 (Polymorphism)`, `node → 노드 (Node)` · `노드 (DOM)` · `노드 (networking)`. 각 파일 2행의 `title` 에서 읽었다 🔵 ([MDN glossary](https://github.com/mdn/translated-content/tree/2a7c03a449507969b925ac954f41c340d7c50263/files/ko/glossary)). 부분 포함은 7건(Accessibility tree · Microsoft Edge · Node.js · Representation header · Shadow tree · Top layer · Tree shaking)으로 전부 웹 고유 의미다 🔵.
- **본문 병기**는 탐침 **18건, 63개 중 9개 낱말**이다: side effect 5(`부수 효과` 2 · `부수효과` 2 · `부작용` 1 — HTTP 메서드·CORS·XSLT 문맥), inheritance 4(`상속`, 주로 CSS 상속), node 3, encapsulation 1(`캡슐화`), polymorphism 1(`다형성`), decorator 1(`데코레이터`, Django 문맥), granularity 1(`입도`, 오디오 문맥), edge 1(`가장자리`, CSS float 문맥), callee 1(`유저`, WebRTC 통화 수신자). 병기 전체는 2,496건이다 🔵.
- 원시 개수(접두 경계만): 부작용 16 · 부수 효과 9 · 부수효과 5 · 의존성 주입 4 · 결합도 1 · 응집도 0 · 캡슐화 34 · 정보 은닉 2 · 관심사 분리 1 · 디자인 패턴 9 · 팩토리 메서드 13 · 리팩터링 2 · 리팩토링 3 · 기술 부채 1 · 상속 709 이다 🔵.

**python-docs-ko `glossary.po` (3.14)**
- `msgid` 444개 중 표제 후보는 163행이다. 판별에는 "60자 이하, 끝이 마침표·콜론이 아님" 이라는 발견법(heuristic)을 썼다. 여기서 rst 조각·색인 항목 15개(``>>>`` · `:pep:`302`` 등)를 빼면 **약 148개**가 남는다 🔵. 꼴은 `msgid "argument"` / `msgstr "argument (인자)"` — 영어를 먼저 쓰고 한국어를 괄호에 넣는다 🔵 ([glossary.po:132-133](https://github.com/python/python-docs-ko/blob/242bdce63d20a3042fa438fea9677f289d7a6d0c/glossary.po)).
- **읽기 함정 둘.** 첫째, `#, fuzzy` 가 12개이고, 그중 표제 5개는 번역문이 다른 항목에서 잘못 복사돼 있다 — `walrus operator → "asynchronous iterator (비동기 이터레이터)"`(3199~3201행), `evaluate function → "key function (키 함수)"`(970~972행), `t-string` · `t-strings` · `f-strings`. 둘째, 3.14 신규 표제 6개(attached thread state · cyclic isolate · REPL · standard library · stdlib · thread state)는 `msgstr` 이 비어 있다 🔵.
- 갈래는 **S1 86(58.1%) · P 51(34.5%) · S2 11(7.4%)** 이다. S2 는 abstract base class · duck-typing · EAFP · generic function · immutable · LBYL · method resolution order · mutable · provisional API · single dispatch · soft deprecated 다 🔵 측정 / 💭 판정 65 — 이 중 EAFP · LBYL · duck-typing 은 Python 관용 표현에 가깝다.
- 탐침 완전 일치는 **1/63**(`decorator → "decorator (데코레이터)"`, 777~779행)이다. 정의는 "다른 함수를 돌려주는 함수인데, 보통 ``@wrapper`` 문법을 사용한 함수 변환으로 적용됩니다" — 언어 문법이지 GoF 데코레이터 패턴이 아니다 🔵 ([glossary.po:777-788](https://github.com/python/python-docs-ko/blob/242bdce63d20a3042fa438fea9677f289d7a6d0c/glossary.po)). 부분 포함은 0건이다.
- **본문 병기**는 탐침 **19건, 63개 중 11개 낱말**이다: idempotent 4(`멱등적`), invariant 3(`불변적` · `불변량` · `불변성` — 변성(variance) 의미가 하나 섞임), representation 2(`표현`), side effect 2(`부작용`), singleton 2(`싱글톤` · `단일자`), deterministic 1(`결정적`), caller 1(`호출자`), inheritance 1(`계승`), vertex 1(`꼭짓점`), edge 1(`에지`, epoll 문맥), abstraction 1(`것` — "추상화한 것(abstraction)", 1어절 창의 한계로 생긴 오추출). 역방향 `English (한글)` 은 1건뿐이다. 병기 전체는 2,589건이다 🔵.
- 원시 개수(접두 경계만): 부작용 52 · 호출자 162 · 피호출자 8 · 캡슐화 27 · 추상화 26 · 순환 참조 11 · 결정론적 11 · 결정적 10 · 리팩토링 11 · 테스트 코드 21 · 데코레이터 205 · 결합도 0 · 응집도 0 · 의존성 주입 0 · 관심사 분리 0 이다. 영어 원문이 남은 `bisect` 16회는 **Python `bisect` 모듈**로, git bisect 가 아니다 🔵.

**세 저장소 합계**
- 용어집 적중의 합집합은 7개 낱말이다(abstraction · encapsulation · idempotent · inheritance · polymorphism · node · decorator). 그중 **의도한 언어 불문 의미는 5개이고 전부 MDN** 에서 나왔다 🔵 측정 / 💭 의미 판정 85.
- 본문 병기로 1건 이상 나온 탐침은 합집합 20개이고, **43개는 세 말뭉치 어디에도 병기가 없다**. 병기·원시 개수가 모두 0인 것은 single responsibility · open-closed · Liskov substitution · interface segregation · dependency inversion · common closure principle, inversion of control, code smell, bounded context, ubiquitous language 다(한국어 후보 단일 책임 원칙 · 제어의 역전 · 코드 스멜 · 바운디드 컨텍스트 · 유비쿼터스 언어도 0) 🔵.

### Inferences
- 💭 85 — 세 저장소의 **용어집**은 계획이 정한 무게 중심(언어 불문 설계·아키텍처·패턴·SOLID·SE)과 거의 겹치지 않는다. 쿠버네티스는 S2 가 0, Python 은 표제의 92% 이상이 Python 고유이거나 일반 프로그래밍 어휘다. MDN 만 객체지향 기본 넷과 멱등성을 갖는다.
- 💭 80 — 동형이의가 실제 위험이다. 같은 영어 표제가 node(쿠버네티스 장비 · DOM · 네트워크), decorator(Python 문법), annotation(쿠버네티스 메타데이터 · Python 형 주석), bisect(Python 모듈), inheritance(CSS 상속)처럼 **플랫폼 의미로** 들어 있다. 증거 행에 출처 범위만 적고 정의나 의미 표지를 싣지 않으면, LLM 이 "노드 = 확립된 용어" 를 그래프 문맥에 잘못 옮겨 쓸 수 있다.
- 💭 70 — 본문 병기 개수(저장소당 14~19건)로는 대부분의 탐침에 대해 "근거 없음" 이 나온다. 말뭉치 ② 갈래의 증거력은 원시 한국어 개수(예: Python 의 부작용 52, 호출자 162)가 더 크지만, 그 개수에는 의미 구분이 없다.
- 💭 65 — 쿠버네티스의 진짜 쓸모는 `glossary/*.md` 가 아니라 `localization_ko.md` 의 **번역 정책과 결정 이력**(한글 > 병기 > 영어, 첫 등장 1회 병기)일 수 있다. 다만 이것도 클라우드 용어 중심이다(257행 중 탐침 3개).

### Gaps
- S1/S2/P/G 판정은 한 사람(이 연구자)의 판단이고 교차 검증을 하지 않았다. S2 목록은 그대로 공개했으니 다른 사람이 다시 판정할 수 있다.
- 본문 병기 정규식은 정밀도를 문맥 출력으로 손검사했다(51건 전부). **재현율은 재지 않았다** — `부수 효과(side effect, 부작용)` 같은 혼합 괄호, 전각 괄호, 영어 동의어(idempotency · idempotence)는 세지 않았다. 느슨한 패턴(괄호 안이 탐침 뒤 `,` `;` `/` 로 이어지는 경우)을 따로 돌렸지만 세 저장소 모두 엄격한 패턴과 개수가 같았다 🔵.
- 원시 한국어 개수에는 뒤 경계 규칙(계획서의 경계 규칙 v1)을 적용하지 않았다. 과다 집계이므로 비교용으로만 써야 한다.

## Q2. Microsoft Terminology Collection — 다루는 분야, 설계·SE 개념어의 포함 여부, 한국어 현지화 스타일 가이드

### Takeaway
공식 문서는 이 모음을 "Microsoft 제품과 통합되는 애플리케이션의 현지화" 용이면서 "기본 IT 용어집(base IT glossary)" 으로 소개한다 🔵. 제3자가 TBX 를 변환한 같은 모음의 프랑스어·독일어판을 영어 쪽에서 재 보면 **탐침 63개 중 36개(프랑스어)·35개(독일어)가 표제로 있다** 🔵. 넷 중 압도적으로 많다. 그러나 36개 중 13개는 설계가 아닌 의미로만 들어 있다(coupling = CRM 레코드 연결, encapsulation = 네트워크 프로토콜 캡슐화, inheritance = ACL 상속, singleton = 데이터베이스 인스턴스 등). 전체 항목의 약 31% 는 고유명사다. **한국어판 자체는 이번에도 받지 못했다** — download.microsoft.com 이 막혀 있다.

### Cited Findings
- Microsoft Learn 의 공식 설명(MCP 로 읽음): "Microsoft Terminology can be used to develop localized versions of applications that integrate with Microsoft products. It can also be used to integrate Microsoft terminology into other terminology collections or serve as a base IT glossary for language development in the nearly 100 languages available." 내려받기는 `.tbx` 형식, `download.microsoft.com/.../MicrosoftTermCollection.zip` 이고 조회는 Power BI 기반 "Microsoft Terminology Search" 다 🔵 ([Microsoft Terminology](https://learn.microsoft.com/globalization/reference/microsoft-terminology); [Microsoft language resources](https://learn.microsoft.com/globalization/reference/microsoft-language-resources)).
- 같은 Learn 의 용어 관리 지침은 제품명·핵심 기능을 번역할지, 음역(transliterate)할지, 원어로 둘지를 정하라고 한다. 또 "the market might prefer the 'English' term even if an equivalent term exists in the target language" 일 때 번역 금지(DNT)가 될 수 있다고 적는다. 이것은 Microsoft 의 **일반 현지화 지침**이고 한국어 규칙이 아니다 🔵 ([Manage terminology](https://learn.microsoft.com/globalization/localization/managing-terminology)).
- Hugging Face `ms_terms` 카드는 단일 train 분할 33,738 예제와 필드 `entry_id` · `term_source` · `pos` · `definition` · `term_target` 을 적고, 언어별 개수는 문서화하지 않았다 🟡 ([ms_terms README](https://huggingface.co/datasets/ms_terms/blob/main/README.md); [ms_terms.py](https://huggingface.co/datasets/microsoft/ms_terms/blob/refs%2Fpr%2F2/ms_terms.py)). TBX Scope 는 전체 모음이 "around 33,000 individual entries" 라고 쓴다 🟡 ([TBX Scope](https://git.tdem.in/buresdv/TBX-Scope)). Beijerterm 에는 "33,004 Dutch-English entries" 라는 제목의 쪽이 있다 🟡 ([Beijerterm](https://beijerterm.com/Microsoft_Terminology_Collection_(33,004_Dutch-English_entries))). 이 세션에서 `huggingface.co` · `download.microsoft.com` 은 프록시가 403/ENOTFOUND 로 막았다 🔵.
- **대리 측정(proxy) 자료.** `spidersouris/termic` README 는 그 용어집들을 "retrieved from the Microsoft Terminology Collection … .tbx files that were converted to .xlsx using Xbench" 라고 적는다 🔵 ([termic @6e4fe2a](https://github.com/spidersouris/termic/tree/6e4fe2a5b80f2efd06e117db19037aa6c207fe55)). 그 데이터 저장소 `spidersouris/termic-data`(보관됨, 커밋 `af955efdeab80e42452c435428d4d7077008b917`, 2023-07-04)에는 11개 언어의 `glossary_*.xlsx` 가 있지만 **한국어는 없다** 🔵 ([termic-data/data](https://github.com/spidersouris/termic-data/tree/af955efdeab80e42452c435428d4d7077008b917/data)). 열은 `term_en_US` · `term_fr_FR` · `def_en_US` · `pos_en_US` · `pos_fr_FR` 다 🔵.
- 프랑스어판은 36,647행에 서로 다른 영어 표제 33,909개, 독일어판은 36,697행에 34,153개, 베트남어판은 17,561행이다 🔵. 품사는 프랑스어판 기준 Noun 23,512 · **Proper Noun 11,398(31.1%)** · Verb 999 · Adjective 590 이다(독일어 30.6%, 베트남어 35.2%) 🔵.
- 결정적 표지로 잰 제품 종속 비율은 다음과 같다(프랑스어판). 정의에 Microsoft 제품명(Azure · Dynamics · Office · Windows · SharePoint · Xbox · Teams · Visual Studio 등 정규식)이 나오는 항목이 9,762(26.6%), 표제에 제품명이 든 항목이 4,083(11.1%)이다. 고유명사 · 정의 · 표제 중 하나라도 걸리면 14,969(40.8%)다. 정의에 프로그래밍 어휘(object-oriented · class · method · subroutine · function · module · programming · algorithm · data structure 등)가 나오는 항목은 2,379(6.5%)다. 정규식이 거칠어서 `Access` · `Edge` 같은 낱말은 과다 집계될 수 있다 🔵.
- **탐침 완전 일치(영어 쪽).** 프랑스어판 36/63, 독일어판 35/63 이다(독일어판에는 `idempotent` 가 없다) 🔵. 없는 27~28개는 precondition · postcondition · invariant · single source of truth · SOLID 다섯 · common closure principle · dependency injection · inversion of control · information hiding · **abstraction** · layered architecture · layering violation · separation of concerns · testability · observer · facade · visitor · code smell · bisect · bounded context · production code · test code · prerequisite 다 🔵.
- **적중 36개의 의미를 정의(`def_en_US`)로 확인했다(프랑스어판)** 🔵 측정 / 💭 의미 판정 80.
  - 설계·프로그래밍 의미의 행이 하나 이상 있는 것은 23개다. side effect("Any change of state caused by a subroutine…") · cohesion("The degree to which the elements of a module belong together…") · polymorphism("In an object-oriented programming language…") · design pattern("A repeatable solution to a design problem in software design") · factory method · refactoring · technical debt · ubiquitous language("A language structured around the domain model…") · circular dependency · dependency graph · call graph · call tree · deterministic · idempotent · granularity · interface("A defined set of properties, methods…") · convention · edge("A link between two nodes on a tree or graph data structure") · node(트리 의미 행) · tree · pipeline(소프트웨어 파이프라인 행) · stage(워크플로·릴리스 단계) · data flow(ETL 의미, 부분적).
  - 설계가 아닌 의미로만 있는 것은 13개다. coupling(CRM 레코드 연결) · encapsulation(네트워크 프로토콜 캡슐화) · inheritance(ACL 의 ACE 상속) · composition(워크플로) · representation(계약상 "진술", 프랑스어 déclaration) · singleton(고정 자원 데이터베이스 인스턴스) · decorator(WPF 스타일 컨트롤) · strategy(게임 장르) · adapter(전송 구성 요소·하드웨어 카드) · layer(프로토콜 계층·페이지 레이어) · caller(전화 거는 사람) · callee(통화 수신자·호출되는 컴퓨터) · vertex(그래픽스).
- 표제당 행이 여러 개 있어 의미가 갈린다. `stage` 는 6행(파일 스테이징 · 온라인 회의 공유 창 · 릴리스 단계 · git 인덱스 · 창고 적치 · 워크플로 단계), `pipeline` 은 2행(영업 기회 "opportunités" · 소프트웨어 파이프라인)이다 🔵.
- **한국어 현지화 스타일 가이드.** Learn 의 목록은 Korean 을 `aka.ms/korean-styleguide` 로 연결하고 🔵 ([Localization Style Guides](https://learn.microsoft.com/globalization/reference/microsoft-style-guides)), 실제 파일은 `download.microsoft.com/.../kor-kor-StyleGuide.pdf` 다. 이 세션에서는 `aka.ms` 가 403, `download.microsoft.com` 이 ENOTFOUND 여서 본문을 열지 못했다 🔵. 검색 요약에 따르면 이 가이드는 표준국어대사전을 기준 사전으로 들고, 나머지 용어는 Microsoft Terminology 를 보라고 한다 🟡 ([kor-kor-StyleGuide.pdf](https://download.microsoft.com/download/5/b/6/5b62389f-4e3b-4c77-bc18-94efba2fa7bb/kor-kor-StyleGuide.pdf)). 음역 대 번역, 영어 병기 규칙은 요약에 나오지 않았다 🟡.

### Inferences
- 💭 75 — 이 모음은 "제품 UI 만" 담은 것이 아니다. 정의가 붙은 일반 IT·소프트웨어 개념어(cohesion · side effect · polymorphism · design pattern · refactoring · technical debt · ubiquitous language · circular dependency · call graph)를 상당수 담는다. 탐침 기준으로는 넷 중 유일하게 설계·SE 어휘를 의미 있게 덮는다.
- 💭 80 — 그러나 **표제 일치만으로 행을 내면 오도한다.** 적중 36개 중 13개는 설계 의미의 행이 아예 없다. coupling · encapsulation · inheritance 처럼 설계 문서에서 가장 자주 쓰는 말이 MS 모음에서는 다른 제품 의미로 번역돼 있다. 그러므로 MS 행에는 `def_en_US`(정의)를 함께 싣거나, 정의로 의미를 거르는 단계가 필요하다.
- 💭 60 — 한국어 TBX 의 영어 표제 집합이 프랑스어·독일어와 같은지는 모른다. 언어별 행 수가 크게 다르다(프랑스어 36,647 대 베트남어 17,561). 한국어는 Microsoft 의 주력 현지화 언어이므로 프랑스어·독일어 쪽에 가까울 것으로 추정하지만, 받아서 확인해야 한다(계획서 V1 · M1).
- 💭 70 — 이번 대리 측정은 2023-07 이전에 변환된 xlsx(제3자, Xbench)를 썼다. 지금 `MicrosoftTermCollection.zip` 과 판이 같은지 확인하지 않았다. 앞선 메모에 따르면 Language Portal 이 2023-06-30 내려간 뒤 갱신이 없다고 공지됐으므로 큰 차이는 없을 것으로 보인다.

### Gaps
- 한국어 TBX 를 직접 열지 못했다. 따라서 한국어 대상어, 한국어판의 표제 수, 상태 필드(`administrativeStatus`) 존재 여부는 모두 미확인이다. 세션 네트워크 설정에서 `download.microsoft.com` 을 허용해야 한다.
- Microsoft Korean Localization Style Guide 의 외래어·음역·영어 병기 규칙은 확인하지 못했다(PDF 차단, 검색 요약에 해당 절 없음). 이 가이드가 개발 용어 표기의 권위 출처가 될 수 있는지는 미결이다.
- Microsoft Terminology Search(Power BI 페이지)는 시도하지 않았다.

## Q3. 출처별 결론 — 그대로 둔다 / 설계·SE 로 걸러서 둔다 / 뺀다

### Takeaway
측정 숫자로 보면 **Microsoft 는 "걸러서 둔다"**, **쿠버네티스 용어집은 ① 권위 출처로서는 "뺀다"**(말뭉치 ② 와 한글화 정책 문서는 낮은 비중으로 남길 여지), **MDN 은 "걸러서 둔다"**, **python-docs-ko 용어집은 "뺀다"**(말뭉치는 일반 CS 어휘용으로 남길 여지)가 자연스럽다. 사용자가 둘 쪽으로 기운 Microsoft 와 쿠버네티스 중 **Microsoft 는 측정이 그 선택을 지지하고, 쿠버네티스는 지지하지 않는다**. 아래 판정은 모두 💭 추론이다.

### Cited Findings
- 탐침 63개에 대한 측정 요약 🔵(근거는 Q1·Q2 의 항목과 같다):

| 출처 | 항목 수 | 플랫폼 종속 비율(판정·표지) | 탐침 완전 일치 | 그중 의도한 설계 의미 | 본문 `한글(English)` 탐침 병기 |
|---|---|---|---|---|---|
| MS Terminology (프랑스어·독일어판 영어 쪽 대리) | 약 36,650행 / 영어 표제 약 34,000 | 고유명사 31%, 제품 표지 41% | 36 / 35 | 23 (13은 다른 의미만) | — (말뭉치 아님) |
| 쿠버네티스 용어집 | 123 | P 85% · S2 0% | 1 (node) | 0 | 14건 / 7개 낱말 |
| (참고) 쿠버네티스 `localization_ko.md` 표 | 257 | 클라우드 중심 | 3 | 2 (idempotent · pipeline) | — |
| MDN 용어집 | 564 | P 58% · S2 6.6% · S1 28% | 6 (8항목) | 5 | 18건 / 9개 낱말 |
| python-docs-ko `glossary.po` | 약 148 | P 35% · S1 58% · S2 7% | 1 (decorator) | 0 | 19건 / 11개 낱말 |

### Inferences
- 💭 70 — **Microsoft TBX: 걸러서 둔다.** 넷 중 유일하게 설계·SE 어휘를 상당히 덮는다(대리 측정 36/63). 고유명사(약 31%)는 빼고, 정의로 의미를 걸러야 한다. 최소한 MS 행에는 `def_en_US` 를 실어서 coupling · encapsulation · inheritance 같은 동형이의 행이 설계 근거로 오인되지 않게 해야 한다. 한국어판의 실제 적중은 V1 에서 다시 재야 한다.
- 💭 75 — **쿠버네티스 용어집: ① 권위 출처로서는 뺀다.** 항목의 85% 가 쿠버네티스 고유이고 S2 는 0이며, 유일한 탐침 적중(node)은 장비 의미다. 사용자가 두려는 이유가 "번역 공동체의 결정 이력" 이라면, 그 가치는 `glossary/*.md` 가 아니라 `localization_ko.md`(정책 155~171행 + 257행 표, 한글화팀 회의 결정)에 있다. 남긴다면 범위 표지 "클라우드" 를 달고 말뭉치 ② 로만 낮은 비중을 주는 편이 측정과 맞는다.
- 💭 70 — **MDN 용어집: 걸러서 둔다.** S2 37개와 S1 159개만 남기면 탐침 의도 의미 5개를 모두 지키면서 제품·웹 표준 이름 325개를 덜어 낼 수 있다. 하위 폴더 동음이의(node/dom · node/networking)는 범위 표지로 그대로 보여 준다.
- 💭 65 — **python-docs-ko 용어집: 뺀다.** 설계 탐침 의미 적중이 0이고, fuzzy 오역 5개와 미번역 6개가 있다. 다만 `msgstr` 본문의 일반 CS 어휘 원시 빈도(부작용 52 · 호출자 162)는 말뭉치 ② 로 쓸모가 있을 수 있다. 계획서의 말뭉치 범위(D3)를 바꿀지는 사용자가 정한다.
- 💭 80 — 넷을 다 두어도 SOLID · DI · IoC · 관심사 분리 · 계층 위반 · 코드 스멜 · 바운디드 컨텍스트는 근거가 0이다(MS 대리 측정 포함). 계획이 정한 무게 중심을 채우려면 언어 불문 설계·SE 전용 출처가 따로 있어야 한다. 그 후보 조사는 이 연구의 범위 밖이다.

### Gaps
- 판정 기준(S1/S2 경계, "의도한 의미")은 탐침 목록과 마찬가지로 연구 도구다. 사용자가 다른 어휘 목록을 쓰면 비율이 달라진다.
- MS 결론은 한국어가 아닌 대리 판본으로 냈다. 한국어 TBX 를 받으면 같은 스크립트(`msxlsx.py` 의 매칭 · `msdefs.py` 의 정의 출력)를 TBX 판독기로 바꿔 다시 재야 한다.
