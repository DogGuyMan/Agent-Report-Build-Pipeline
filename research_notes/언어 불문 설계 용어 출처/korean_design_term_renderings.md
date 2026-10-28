# 언어 불문 설계·공학 용어의 한국어 표기 출처 — 영어 원어가 짝지어진 비공식·비프레임워크 출처 목록

조사 일자 2026-10-28. 표지: 🔵 이번 세션 실측(복제한 저장소의 커밋, 직접 받은 페이지) · 🟡 검색 스니펫(원문 페이지가 막혀 확인 못 함) · 💭 추론(정수는 확신도).

네트워크 사정(🔵): `refactoring.guru` 는 WebFetch 에서 `getaddrinfo ENOTFOUND`, curl 에서 `CONNECT tunnel failed, response 403` 이었다. `wikidocs.net` 은 WebFetch `ENOTFOUND`. `cockpit.ireb.org` PDF 는 curl 응답 코드 000(받기 실패). `ko.wikipedia.org` 는 앞선 조사 보고서가 막혔다고 기록했다. 그래서 refactoring.guru·위키백과·위키독스·IREB 의 내용은 **전부 🟡** 이다. 보관소·중계 서비스(웹 아카이브 등)로 우회하는 것은 세션 정책이 거부했으므로 쓰지 않았다. Microsoft Learn 한국어 페이지는 Microsoft Learn MCP 의 `microsoft_docs_fetch` 로 원문을 받아 읽었다(🔵). GitHub 공개 저장소는 익명 `git clone` 이 됐다(🔵). GitHub 검색 API 는 세션 정책상 막혀 있었다("sessions are bound to their configured repositories").

탐침 용어(probe terms) 표기: 아래 본문에서 "탐침 51개" 는 과제가 준 개념어 28개와 GoF 패턴 이름 23개를 합친 수다.

## 1. refactoring.guru 에 한국어판이 있는가 (디자인 패턴 · 리팩터링 카탈로그 · 코드 스멜), 한국어 이름과 라이선스

### Takeaway
refactoring.guru 에는 `/ko/` 한국어판이 있다. **디자인 패턴 쪽은 22개 패턴의 한국어 표제가 검색 색인에서 확인된다**(🟡). 표기는 국립국어원 외래어 표기 쪽(`싱글턴` · `옵서버`)이고, 의미 번역은 `복합체` · `반복자` · `책임 연쇄` · `중재자` 정도다. 리팩터링 기법과 코드 스멜의 한국어판은 확인하지 못했다. 사이트 콘텐츠는 "All rights reserved" 이고, 재사용은 출처 페이지에 링크를 다는 조건으로만 허용된다. 그 밖의 용도는 이메일로 허락을 받아야 한다. 그러니 로컬에 저장해 파생 행을 공개하는 출처로는 맞지 않다(💭 80).

### Cited Findings
- 🟡 한국어 페이지 표제(검색 결과 제목 그대로): "싱글턴 패턴", "반복자 패턴", "비지터 패턴", "퍼사드 패턴", "브리지 패턴", "프로토타입 패턴", "책임 연쇄 패턴", "팩토리 메서드 패턴", "디자인 패턴 목록", "생성 디자인 패턴", "구조 디자인 패턴", "행동 디자인 패턴", "패턴의 분류" — [싱글턴](https://refactoring.guru/ko/design-patterns/singleton); [반복자](https://refactoring.guru/ko/design-patterns/iterator); [비지터](https://refactoring.guru/ko/design-patterns/visitor); [퍼사드](https://refactoring.guru/ko/design-patterns/facade); [브리지](https://refactoring.guru/ko/design-patterns/bridge); [프로토타입](https://refactoring.guru/ko/design-patterns/prototype); [책임 연쇄](https://refactoring.guru/ko/design-patterns/chain-of-responsibility); [팩토리 메서드](https://refactoring.guru/ko/design-patterns/factory-method); [목록](https://refactoring.guru/ko/design-patterns/catalog); [분류](https://refactoring.guru/ko/design-patterns/classification)
- 🟡 구조 패턴 목록 스니펫: "어댑터, 브리지, 복합체, 데코레이터, 퍼사드, 플라이웨이트, 프록시" — [디자인 패턴 목록](https://refactoring.guru/ko/design-patterns/catalog)
- 🟡 행동 패턴 관계 절 스니펫: "커맨드, 중재자, 옵서버, 책임 연쇄가 발신자와 수신자를 연결하는…". 페이지 제목 "PHP로 작성된 옵서버 / 디자인 패턴들" — [책임 연쇄](https://refactoring.guru/ko/design-patterns/chain-of-responsibility); [옵서버 PHP 예제](https://refactoring.guru/ko/design-patterns/observer/php/example)
- 🟡 "메멘토", "플라이웨이트", "복합체" 의 정의 스니펫이 같은 카탈로그 묶음에서 나왔다 — [디자인 패턴 목록](https://refactoring.guru/ko/design-patterns/catalog)
- 🟡 카탈로그 규모 "22 种设计模式及 8 条原则"(중국어 2차 자료). GoF 23개 중 해석자(Interpreter)가 없다는 뜻으로 읽힌다 — [검색 요약 출처 news.hada.io](https://news.hada.io/topic?id=7734) 계열 결과. 2차 자료라 현재 수치와 다를 수 있다.
- 🟡 한국어 사이트 루트 제목은 "리팩터링과 디자인 패턴"(`리팩터링` 표기)이다. `/ko/refactoring/techniques/organizing-data` URL 도 색인에 있다. 그러나 코드 스멜과 리팩터링 기법의 한국어 본문 스니펫은 나오지 않았고, 색인 결과는 영어 페이지("Long Method", "Large Class" 등)뿐이었다 — [refactoring.guru/ko](https://refactoring.guru/ko); [Organizing Data (ko URL)](https://refactoring.guru/ko/refactoring/techniques/organizing-data); [Code Smells (en)](https://refactoring.guru/refactoring/smells)
- 🟡 한국어 책 『디자인 패턴에 뛰어들기』 페이지가 있다. 2022 년 커뮤니티 댓글은 번역가를 따로 구하고 커뮤니티에서는 피드백만 받은 것 같다고 적었다 — [책 페이지](https://refactoring.guru/ko/design-patterns/book); [GeekNews 토론](https://news.hada.io/topic?id=7734)
- 🟡 콘텐츠 이용 정책: 사이트 대부분은 저작권 보호 대상이다. 콘텐츠와 그림은 그것을 가져온 특정 페이지로 링크를 달면 재사용할 수 있고, "If you want to use more than that, please send us email to support@refactoring.guru". 푸터는 "2014-2024 Refactoring.Guru. All rights reserved" — [content-usage-policy](https://refactoring.guru/content-usage-policy); [약관 사본(2019-04-19 판, 제3자 보관)](https://tostracker.app/document/refactoringguru-tos)
- 🔵 예제 코드 저장소 `RefactoringGuru/design-patterns-java` 는 공개(HEAD `f09ed68`)지만, 사이트 본문 저장소로 짐작한 `RefactoringGuru/refactoring.guru` 는 익명 접근에서 자격 증명을 요구했다(없거나 비공개) — [design-patterns-java](https://github.com/RefactoringGuru/design-patterns-java)

### Inferences
- 💭 75 영어–한국어 짝은 URL 슬러그(`/ko/design-patterns/observer` ↔ `/design-patterns/observer`)로 결정적으로 얻는다. 페이지 제목이 "옵서버 패턴" 이고 영어판 제목이 "Observer" 이므로, 같은 슬러그의 두 언어 제목을 맞추면 항목마다 명시적 짝이 된다. 다만 스냅숏은 받은 날짜로만 고정되고, 라이선스상 행을 공개 배포하기 어렵다.
- 💭 70 refactoring.guru/ko 의 표기(`싱글턴` · `옵서버` · `비지터` · `퍼사드` · `플라이웨이트` · `복합체`)는 한국어 위키백과 표제(`싱글턴 패턴` · `옵서버 패턴` · `비지터 패턴`)와 철자가 같다. 반면 cjk-compsci-terms(`싱글톤` · `옵저버`)와 『헤드 퍼스트 디자인 패턴』(`옵저버`)과는 다르다(4절·5절). 그래서 표기 변이 근거로는 독립 출처 하나의 가치가 있다.

### Gaps
- 추상 팩토리 · 빌더 · 상태 · 전략 · 템플릿 메서드 · 커맨드의 한국어 표제는 이번 스니펫에 문자 그대로 나오지 않았다("커맨드" 는 관계 절 본문에만 있었다). 사이트가 막혀 22개를 한 번에 세지 못했다.
- 코드 스멜(21종)과 리팩터링 기법(66종)에 한국어판이 있는지, 있다면 무슨 표기인지는 확인하지 못했다. 검색 요약 모델은 "번역이 완료되지 않아 대부분 영문 용어로 표시" 라고 했지만, 근거 스니펫이 없어 쓰지 않는다.
- 현재 약관 원문(`/terms`)은 받지 못했다. 2019 년 사본과 이용 정책 스니펫만 있다.
- 탐침 개념어(side effect, coupling 등)는 refactoring.guru 의 표제어가 아니므로 이 출처로는 덮이지 않는다.

## 2. Microsoft Azure Architecture Center 한국어판 — 패턴·원칙 이름을 어떻게 옮기고 영어를 병기하는가, 라이선스

### Takeaway
learn.microsoft.com/ko-kr 의 Architecture Center 와 .NET 아키텍처 전자책은 **기계 번역 흔적이 짙고 영어 병기가 거의 없다.** 한 페이지 안에서 `bounded context` 가 6가지로 옮겨지는 등 일관성이 없다. 괄호 병기는 약어(`DDD(도메인 기반 디자인)` · `DRY(반복 금지)` · `PI(지속성 무지)`)에만 붙는다. 사이트 이용 약관은 개인·비상업 용도로 한정하지만, 영어 원문 저장소 `MicrosoftDocs/architecture-center` 는 CC BY 4.0 이고 커밋으로 고정된다. 한국어 저장소는 비공개다. 그러므로 이 출처는 "확립된 개발자 용어" 의 근거라기보다 **기계 번역이 만드는 변이의 반례 표본**으로 쓰는 편이 맞다(💭 75).

### Cited Findings
- 🔵 클라우드 디자인 패턴 카탈로그 한국어판의 패턴 이름 열에는 영어 병기가 없다. 실제 표기: Ambassador → "대사", Anti-corruption Layer → "반부패 계층", Choreography → "안무", Circuit Breaker → "회로 차단기", Bulkhead → "격벽", Idempotent Consumer → "멱등 소비자", Publisher-Subscriber → "게시자-구독자", Strangler Fig → "스트랭글러 무화과", Valet Key → "발레 키", Sharding → "분할", Saga → "사가", Pipes and Filters → "파이프 및 필터". Rate Limiting 과 Throttling 은 둘 다 "속도 제한" 이다. Retry 는 표에서 "재시도", 아래 절에서 "다시 시도" 다. Queue-Based Load Leveling 은 "대기열 기반 부하 평준화" 와 "큐 기반 부하 평준화" 가 함께 나온다. 링크 텍스트가 뒤바뀐 문장("보상 [트랜잭션](saga)에서 [Saga](compensating-transaction)")도 있다 — [클라우드 디자인 패턴 (ko-kr)](https://learn.microsoft.com/ko-kr/azure/architecture/patterns/)
- 🔵 "도메인 분석을 사용하여 마이크로 서비스 모델링" 한 페이지 안의 `bounded context` 표기: "경계가 있는 각 컨텍스트", "경계가 지정된 각 컨텍스트", "경계된 컨텍스트"(그림 설명), "제한된 컨텍스트"(절 제목 포함), "바인딩된 컨텍스트", "경계가 설정된 컨텍스트" — 6가지. 같은 페이지에서 Anti-corruption layer 는 "손상 방지 계층" 이라 카탈로그의 "반부패 계층" 과 다르다. `ubiquitous language` 는 "*유비쿼터스 언어*", loose coupling 은 "느슨한 결합", cohesion 은 "응집력" 이다 — [도메인 분석 (ko-kr)](https://learn.microsoft.com/ko-kr/azure/architecture/microservices/model/domain-analysis)
- 🔵 .NET 전자책 "아키텍처 원칙" 한국어판 표기: Separation of Concerns → 절 제목 "문제의 분리", 본문 "**우려의 분리**", "문제를 분리하는 것". Encapsulation → "캡슐화". Dependency Inversion → "종속성 반전", "종속성 반전 원칙". Dependency injection → "종속성 주입". Explicit Dependencies → "명시적 종속성 원칙". Single Responsibility → "단일 책임 원칙". "DRY(반복 금지)". Persistence Ignorance → "PI(**지속성 무지**)", "지속성 무시". Bounded Contexts → 절 제목 "제한된 컨텍스트", 본문 "바인딩된 컨텍스트", "경계가 지정된 각 컨텍스트", "경계가 있는 컨텍스트". 이 페이지는 PDF 전자책에서 발췌했다고 밝힌다 — [아키텍처 원칙 (ko-kr)](https://learn.microsoft.com/ko-kr/dotnet/architecture/modern-web-apps-azure/architectural-principles)
- 🔵 Microsoft Learn 이용 약관: "Unless otherwise specified, the Services are for your personal and non-commercial use. You may not modify, copy, distribute, … create derivative works … without prior written consent". 같은 약관에 "Certain documentation may be subject to explicit license terms separate from the terms contained here … the explicit license terms control" 도 있다 — [learn.microsoft.com Terms of Use](https://learn.microsoft.com/en-us/legal/termsofuse)
- 🔵 영어 원문 저장소 `MicrosoftDocs/architecture-center` 는 공개다. HEAD `6d1df20` (2026-10-28T05:02:10Z), `LICENSE` = "Attribution 4.0 International", `LICENSE-CODE` = MIT — [architecture-center](https://github.com/MicrosoftDocs/architecture-center/tree/6d1df20e7433ce2b765b4944c10a3ed0f9625caf)
- 🔵 한국어 저장소로 짐작한 `MicrosoftDocs/architecture-center.ko-kr` 는 익명 `git ls-remote` 에서 자격 증명을 요구했다. 앞선 보고서도 `azure-docs.ko-kr` 등 현지화 저장소가 지금은 닫혔다고 기록했다 — [앞선 보고서](/home/user/Agent-Report-Build-Pipeline/reports/한국어%20개발%20용어%20근거%20방법.md)

### Inferences
- 💭 75 같은 페이지에서 한 영어 용어가 6갈래로 옮겨지는 것은 사람이 관리하는 용어집이 적용되지 않았다는 신호다(용어집이 있으면 한 갈래로 묶였을 것). 그래서 ko-dev-terms 가 이 출처의 표기를 "개발자 영역에서 확립된 용어" 근거로 세면 잘못된 행이 생긴다. 쓴다면 출처 종류를 `기계번역(현지화)` 같은 별도 표지로 달아야 한다.
- 💭 70 짝짓기는 결정적으로 할 수 있다. en-us 와 ko-kr 의 같은 경로 페이지는 표의 행 순서와 절 구조가 같으므로(카탈로그 표 45행), 행 단위로 맞추면 패턴 이름 짝이 나온다. 그러나 한국어 쪽은 git 고정 수단이 없고 받은 날짜로만 고정된다. 라이선스도 영어 저장소(CC BY 4.0)와 사이트 약관(비상업)이 갈리고, 한국어 번역본이 CC BY 4.0 을 물려받는지는 확인되지 않는다.
- 💭 60 Microsoft 표기의 계열 특징(`dependency` → `종속성`, `inversion` → `반전`)은 Microsoft 용어집 계열과 일관된 것으로 보인다. Microsoft 용어집 TBX 는 다른 조사자의 범위이므로 여기서 대조하지 않았다.

### Gaps
- "아키텍처 스타일"(N-tier/계층형), "설계 원칙" 페이지는 받지 않았다. 따라서 `layered architecture` 의 Microsoft 한국어 표기는 이번에 확인하지 않았다.
- 한국어 페이지가 기계 번역인지 사람 번역인지 표시하는 메타데이터는 MCP 출력에 없었다. "기계 번역" 은 위 변이에서 끌어낸 추론이다.

## 3. 한국어 위키백과의 설계·공학 개념 문서 — 표제, 넘겨주기, 표기 변이

### Takeaway
탐침 개념어 28개 가운데 **한국어 위키백과 표제가 검색으로 확인된 것은 약 20개**다(🟡, 정확한 수는 대조표 참조). 첫 문장의 괄호 병기(`결합도(coupling)` · `응집도(cohesion)` · `전제 조건(precondition)` · `사후 조건(postcondition)` · `IoC(Inversion of Control)`)가 항목별 명시적 짝을 준다. 표제 철자는 국립국어원 외래어 표기법 쪽(`옵서버` · `싱글턴` · `리팩터링`)이다. 한편 문서끼리 표기가 갈린다. precondition 은 `전제 조건`/`선행조건`, postcondition 은 `사후 조건`/`후행조건`, IoC 는 `제어 반전`/`역제어`, information hiding 은 `정보 은닉`/`정보 숨기기`, DIP 는 `의존관계 역전`/`의존성 역전` 이다. 덤프로 받으면 결정적이고 고정할 수 있다는 점은 앞선 보고서가 다뤘다. 이번 세션에는 접속이 막혀 넘겨주기 목록은 하나도 세지 못했다.

### Cited Findings
- 🟡 SOLID 묶음 표제: "SOLID (객체 지향 설계)", "단일 책임 원칙", "개방-폐쇄 원칙", "리스코프 치환 원칙", "의존관계 역전 원칙". 인터페이스 분리 원칙은 SOLID 문서 목록에만 이름이 나왔고 단독 문서는 검색되지 않았다 — [SOLID (객체 지향 설계)](https://ko.wikipedia.org/wiki/SOLID_(%EA%B0%9D%EC%B2%B4_%EC%A7%80%ED%96%A5_%EC%84%A4%EA%B3%84)); [단일 책임 원칙](https://ko.wikipedia.org/wiki/%EB%8B%A8%EC%9D%BC_%EC%B1%85%EC%9E%84_%EC%9B%90%EC%B9%99); [개방-폐쇄 원칙](https://ko.wikipedia.org/wiki/%EA%B0%9C%EB%B0%A9-%ED%8F%90%EC%87%84_%EC%9B%90%EC%B9%99); [리스코프 치환 원칙](https://ko.wikipedia.org/wiki/%EB%A6%AC%EC%8A%A4%EC%BD%94%ED%94%84_%EC%B9%98%ED%99%98_%EC%9B%90%EC%B9%99); [의존관계 역전 원칙](https://ko.wikipedia.org/wiki/%EC%9D%98%EC%A1%B4%EA%B4%80%EA%B3%84_%EC%97%AD%EC%A0%84_%EC%9B%90%EC%B9%99)
- 🟡 리스코프 치환 원칙 문서 본문 스니펫: "하위형에서 선행조건은 강화될 수 없다. 하위형에서 후행조건은 약화될 수 없다. 하위형에서 상위형의 불변조건은 반드시 유지되어야 한다." — [리스코프 치환 원칙](https://ko.wikipedia.org/wiki/%EB%A6%AC%EC%8A%A4%EC%BD%94%ED%94%84_%EC%B9%98%ED%99%98_%EC%9B%90%EC%B9%99)
- 🟡 호어 논리 문서: "P는 전제 조건(precondition), Q는 사후 조건(postcondition)". "루프 불변성" 문서가 따로 있다(본문에 "루프 불변량") — [호어 논리](https://ko.wikipedia.org/wiki/%ED%98%B8%EC%96%B4_%EB%85%BC%EB%A6%AC); [루프 불변성](https://ko.wikipedia.org/wiki/%EB%A3%A8%ED%94%84_%EB%B6%88%EB%B3%80%EC%84%B1)
- 🟡 결합도 문서: "소프트웨어 공학에서 결합도(coupling)는 모듈 간의 상호 의존 정도…". 응집도 문서: "응집도(cohesion)는 컴퓨터 프로그래밍에서 모듈 안의 요소들이 함께 속하는 정도". "느슨한 결합" 문서도 있다 — [결합도](https://ko.wikipedia.org/wiki/%EA%B2%B0%ED%95%A9%EB%8F%84); [응집도](https://ko.wikipedia.org/wiki/%EC%9D%91%EC%A7%91%EB%8F%84); [느슨한 결합](https://ko.wikipedia.org/wiki/%EB%8A%90%EC%8A%A8%ED%95%9C_%EA%B2%B0%ED%95%A9)
- 🟡 "부작용" 문서는 의학 용어이고 "컴퓨터 과학 용어에 대해 부작용 (컴퓨터 과학) 문서를 참고하십시오" 라고 안내한다. "효과 목록" 에 "부작용 (컴퓨터 과학)" 항목이 있다. 그 문서 본문은 스니펫에 나오지 않았다 — [부작용](https://ko.wikipedia.org/wiki/%EB%B6%80%EC%9E%91%EC%9A%A9); [효과 목록](https://ko.wikipedia.org/wiki/%ED%9A%A8%EA%B3%BC_%EB%AA%A9%EB%A1%9D)
- 🟡 제어 반전 문서: "줄여서 IoC(Inversion of Control)이라고 부른다". 의존성 주입 문서 스니펫: "의존성 주입은 광범위한 역제어 테크닉의 한 형태이다" — [제어 반전](https://ko.wikipedia.org/wiki/%EC%A0%9C%EC%96%B4_%EB%B0%98%EC%A0%84); [의존성 주입](https://ko.wikipedia.org/wiki/%EC%9D%98%EC%A1%B4%EC%84%B1_%EC%A3%BC%EC%9E%85)
- 🟡 관심사 분리 문서 스니펫에 "캡슐화는 정보 숨기기의 한 수단이다" 가 있다. "캡슐화 (컴퓨터 프로그래밍)" 은 "캡슐화 (네트워킹)" 과 구분되는 동음이의 표제다 — [관심사 분리](https://ko.wikipedia.org/wiki/%EA%B4%80%EC%8B%AC%EC%82%AC_%EB%B6%84%EB%A6%AC); [캡슐화 (컴퓨터 프로그래밍)](https://ko.wikipedia.org/wiki/%EC%BA%A1%EC%8A%90%ED%99%94_(%EC%BB%B4%ED%93%A8%ED%84%B0_%ED%94%84%EB%A1%9C%EA%B7%B8%EB%9E%98%EB%B0%8D))
- 🟡 느슨한 결합 문서 스니펫: "…인터페이스에만 포인터를 포함하고… 이를 의존성 역전이라고 한다" — [느슨한 결합](https://ko.wikipedia.org/wiki/%EB%8A%90%EC%8A%A8%ED%95%9C_%EA%B2%B0%ED%95%A9)
- 🟡 공학 실천 표제: "리팩터링", "코드 스멜", "기술 부채", "호출 그래프", "멱등법칙", "멱등원" — [리팩터링](https://ko.wikipedia.org/wiki/%EB%A6%AC%ED%8C%A9%ED%84%B0%EB%A7%81); [코드 스멜](https://ko.wikipedia.org/wiki/%EC%BD%94%EB%93%9C_%EC%8A%A4%EB%A9%9C); [기술 부채](https://ko.wikipedia.org/wiki/%EA%B8%B0%EC%88%A0_%EB%B6%80%EC%B1%84); [호출 그래프](https://ko.wikipedia.org/wiki/%ED%98%B8%EC%B6%9C_%EA%B7%B8%EB%9E%98%ED%94%84); [멱등법칙](https://ko.wikipedia.org/wiki/%EB%A9%B1%EB%93%B1%EB%B2%95%EC%B9%99)
- 🟡 도메인 주도 설계 문서: "도메인 주도 설계(Domain-driven design, DDD)는 … 큰 체계를 각각 정해진 맥락에 따라 각자의 모델을 갖는 부분들로 나눈다" — bounded context 를 이 스니펫에서는 "정해진 맥락" 으로 풀어 썼다. 별도 표제는 확인되지 않았다 — [도메인 주도 설계](https://ko.wikipedia.org/wiki/%EB%8F%84%EB%A9%94%EC%9D%B8_%EC%A3%BC%EB%8F%84_%EC%84%A4%EA%B3%84)
- 🟡 패턴 표제: "옵서버 패턴"(스니펫에 "발행/구독 모델로 알려져 있기도 하다"), "싱글턴 패턴"(별도 "싱글턴" 문서도 있음), "데코레이터 패턴", "비지터 패턴", "디자인 패턴 (책)", "소프트웨어 디자인 패턴", "멀티턴 패턴" — [옵서버 패턴](https://ko.wikipedia.org/wiki/%EC%98%B5%EC%84%9C%EB%B2%84_%ED%8C%A8%ED%84%B4); [싱글턴 패턴](https://ko.wikipedia.org/wiki/%EC%8B%B1%EA%B8%80%ED%84%B4_%ED%8C%A8%ED%84%B4); [데코레이터 패턴](https://ko.wikipedia.org/wiki/%EB%8D%B0%EC%BD%94%EB%A0%88%EC%9D%B4%ED%84%B0_%ED%8C%A8%ED%84%B4); [비지터 패턴](https://ko.wikipedia.org/wiki/%EB%B9%84%EC%A7%80%ED%84%B0_%ED%8C%A8%ED%84%B4); [디자인 패턴 (책)](https://ko.wikipedia.org/wiki/%EB%94%94%EC%9E%90%EC%9D%B8_%ED%8C%A8%ED%84%B4_(%EC%B1%85))
- 🟡(앞선 보고서) 위키백과 SQL 덤프의 라이선스는 CC BY-SA 4.0 + GFDL 이고, 덤프 날짜로 고정할 수 있다 — [앞선 보고서](/home/user/Agent-Report-Build-Pipeline/reports/한국어%20개발%20용어%20근거%20방법.md)

### Inferences
- 💭 75 위키백과에는 짝이 두 층으로 있다. (a) 언어 간 링크로 이어진 표제 짝(덤프 필요)과 (b) 첫 문장의 `한글(English)` 괄호 병기. (b) 는 같은 문서 안의 저자 정렬이므로 덤프 본문을 정규식으로 결정적으로 뽑을 수 있다. 다만 (b) 는 넘겨주기에 있는 다른 표기(예: `옵저버 패턴` → `옵서버 패턴` 넘겨주기 여부)를 보여 주지 않는다.
- 💭 70 위키백과 안에서도 표기가 문서마다 다르다(LSP 문서의 `선행조건` vs 호어 논리의 `전제 조건`). 그러니 "위키백과 = 한 표기" 로 묶지 말고 문서 단위로 행을 내야 한다. 이는 앞선 보고서의 "저장소 단위로 묶어 보인다" 와 같은 원리다.
- 💭 65 `부작용 (컴퓨터 과학)` 은 표제가 의학 용어 `부작용` 과 같은 낱말에 괄호 분류어만 붙인 꼴이다. 그래서 `side effect` → `부작용` 근거로 세면 의학 문서와 섞인다. 분류어 `(컴퓨터 과학)` 을 함께 실어야 결정성과 의미가 유지된다.

### Gaps
- 넘겨주기(redirect)는 하나도 확인하지 못했다. `옵저버 패턴` · `싱글톤 패턴` · `리팩토링` · `사이드 이펙트` 같은 다른 철자가 넘겨주기로 있는지는 덤프나 API 로만 알 수 있는데 둘 다 막혀 있었다.
- 다음 탐침은 표제를 찾지 못했다: interface segregation principle(단독 문서), information hiding(단독 문서; 관심사 분리 문서 안의 "정보 숨기기" 만 확인), layered architecture, circular dependency, deterministic(결정론적 알고리즘), bounded context, ubiquitous language. "없다" 는 뜻이 아니라 스니펫에 안 나왔다는 뜻이다.
- GoF 23개 중 옵서버·싱글턴·데코레이터·비지터 4개만 표제를 확인했다.

## 4. 번역 고전서와 출판사·번역자가 공개한 번역 용어 대조표

### Takeaway
GoF · 『리팩터링 2판』 · 『클린 코드』 · 『클린 아키텍처』 · 『도메인 주도 설계』 · 『실용주의 프로그래머』 · 『코드 컴플리트』 · 『헤드 퍼스트 디자인 패턴』 어느 것도 **기계가 읽을 수 있는 번역 용어 대조표를 공개한 흔적을 찾지 못했다.** 확인된 것은 조각뿐이다. 『리팩터링 2판』 역자의 지원 저장소(🔵, 용어표 없음)와 그 안에서 링크한 Google 문서·시트, 목차에 드러난 표기(『클린 코드』 "부수 효과", 『헤드 퍼스트』 "옵저버 패턴"·"싱글턴 패턴"), 그리고 GoF 한국어판 표기로 보이는 `원형`·`단일체`·`적응자` 스니펫(🟡, 낮은 신뢰)이 있다. 책 본문과 색인은 저작물이라 로컬 저장과 행 공개 모두 허락 없이는 어렵다(💭 80).

### Cited Findings
- 🔵 `WegraLee/Refactoring`(HEAD `48bca38`, 마지막 커밋 2020-12-30)은 "『리팩터링 2판』(한빛미디어, 2020)의 지원 사이트" 이고 파일은 `README.md` 하나다. 용어 대조표는 없다. 정오표는 Google 문서로, "IDE들이 제공하는 리팩터링 목록" 은 Google 시트로 링크한다. 본문에 "**덕 타이핑**(duck typing)" 같은 괄호 병기와 "'함수 인라인하기'와 '메서드 인라인하기'는 쓰이는 맥락만 다를 뿐 같은 리팩터링 기법" 이라는 표기 방침이 있다. 저장소에 LICENSE 파일은 없다 — [WegraLee/Refactoring](https://github.com/WegraLee/Refactoring/tree/48bca38e3bb10766d7da2121ec5933fba1f7fc85)
- 🟡 역자 표기 "『리팩터링, 2판』(개앞맵시/남기혁 옮김)". 한 블로그가 "리팩터링 이름 비교 & IDE들이 제공하는 리팩터링 목록" 을 같은 구글 문서로 소개했다 — [justinadpark.tistory.com/221](https://justinadpark.tistory.com/221)
- 🟡 『Refactoring』 한국어판 제목은 초판 『리팩토링』에서 2판 『리팩터링』으로 바뀌었다(검색 요약) — [검색 결과 묶음, wikidocs 번역 용어집 페이지](https://wikidocs.net/67062)
- 🟡 『Clean Code(클린 코드)』 인사이트판, "박재호 옮김", 국내 출간 2013-12-24. 목차에 "부수 효과를 일으키지 마라!" — [교보 eBook](https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000003160816)
- 🟡 『헤드 퍼스트 디자인 패턴(개정판)』 한빛미디어 2022-03, 번역 서환수, 656쪽. 목차 "02장 옵저버 패턴 | 객체들에게 연락 돌리기", "05장 싱글턴 패턴 | 하나뿐인 특별한 객체 만들기". GoF 패턴 14가지를 다룬다 — [O'Reilly 한국어판 목록](https://www.oreilly.com/library/view/-/9791162245262/); [교보 eBook](https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002942608)
- 🟡 『GoF의 디자인 패턴』 김정아 역: 프로텍미디어 2015 개정판, 피어슨에듀케이션코리아 2002 판 — [the-next-web-research-lab 정리](https://the-next-web-research-lab.github.io/fe-dev/design-patterns/gof/structural.html); [CiNii 서지](https://ci.nii.ac.jp/ncid/BA74418398). 같은 정리 페이지가 "적응자" 패턴, "클래스 적응자와 객체 적응자" 를 쓴다(🟡).
- 🟡 GoF 생성 패턴을 "추상 팩토리, 빌더, 팩토리 메서드, 원형(Prototype), 단일체(Singleton)" 로 적은 한국어 자료가 검색 요약에 나왔다(itwiki 등). 어느 책의 표기인지는 스니펫이 밝히지 않았다 — [itwiki GoF 디자인 패턴](https://itwiki.kr/w/GoF_%EB%94%94%EC%9E%90%EC%9D%B8_%ED%8C%A8%ED%84%B4)
- 🟡 『도메인 주도 설계』 번역판의 bounded context 표기는 이번 검색으로 확인되지 않았다. 블로그들은 대부분 음차 "바운디드 컨텍스트" 를 쓰고, "'제한된 문맥' 또는 '경계지어진 문맥'으로도 번역" 된다는 정리가 있다 — [esperer.tistory.com/19](https://esperer.tistory.com/19); [lunaticsy 블로그](https://lunaticsy.github.io/learning-domain-driven-design-03)
- 🟡 출판사 공개 용어표: 인사이트·한빛·위키북스의 공개 대역표는 검색되지 않았다. 대신 데브기어의 번역 지원자 안내가 "프로그래밍 업계에서 사용되는 한글 용어를 반영하지 못하는" 것을 자동 번역의 한계로 꼽는다 — [devgear 번역 안내](https://devgear.co.kr/?p=6383)
- 🟡 위키독스 "번역 용어집"(여러 책을 번역하며 만든 용어집을 분야별로 정리, 마지막 편집 2022-05)이 있다. 호스트가 막혀 내용·저자·라이선스를 확인하지 못했다 — [wikidocs.net/67062](https://wikidocs.net/67062)

### Inferences
- 💭 75 번역서 표기는 근거의 종류가 "편집 정책(한 역자·한 출판사의 결정)" 이다. 앞선 보고서의 ko.react.dev 용어집과 같은 범주다. 여러 책이 같은 표기를 쓰면 독립 표본처럼 보이지만, 같은 역자(예: 개앞맵시는 여러 한빛 책을 옮김)나 같은 출판사 편집 규칙이면 독립이 아니다. 행에 역자·출판사를 함께 실어야 한다.
- 💭 70 GoF 한국어판의 한자어 번역(`단일체` · `원형` · `적응자`)과 실무 음차(`싱글턴`/`싱글톤` · `프로토타입` · `어댑터`)의 대비가 바로 ko-dev-terms 가 보여 줘야 할 "확립된 개발자 용어인가" 의 사례다. 다만 이번 근거는 2차 스니펫이라 책 표기로 단정할 수 없다.
- 💭 65 『리팩터링 2판』 Google 시트("리팩터링 이름 비교")는 리팩터링 기법 이름의 영–한 대조표일 가능성이 높다. 그러나 Google 문서는 고정 수단(버전)이 공개 URL 로는 약하고 라이선스 표기가 없다.

### Gaps
- 『클린 아키텍처』(인사이트) · 『실용주의 프로그래머』(인사이트) · 『코드 컴플리트 2』 · 『도메인 주도 설계』(위키북스로 추정, 미확인)의 역자·용어표는 찾지 못했다.
- GoF 한국어판의 23개 표기를 한 출처에서 확인하지 못했다. 검색어로 넣은 `가교` · `장식자` · `감시자` · `방문자` · `플라이급` 은 이번 스니펫에서 **확인되지 않았다**.
- 『리팩터링 2판』 Google 시트·문서 내용(행 수, 영–한 열 유무)은 열지 못했다.

## 5. GitHub 의 일반 프로그래밍·공학 용어 커뮤니티 용어집 (단일 프레임워크가 아닌 것)

### Takeaway
실측으로 쓸 만한 것은 **`dahlia/cjk-compsci-terms` 하나**다(🔵). 259개 항목 전부에 영어·한국어 짝이 있고, CC BY-SA 4.0 이며, 커밋 `65a7584`(2026-10-19)로 고정된다. 스키마가 있는 YAML 이라 결정적으로 읽힌다. 다만 **탐침 51개 중 8개만 맞는다**(의존성 주입, 리팩토링, 싱글톤, 옵저버, 어댑터, 데코레이터, 전략, factory). 개념어(side effect, coupling, SOLID 다섯 원칙, invariant 등)는 하나도 없다. 그 밖의 후보는 데이터가 저장소 밖(Supabase, GitHub 이슈)에 있거나, 프레임워크 전용이거나, 받지 못했다.

### Cited Findings
- 🔵 `dahlia/cjk-compsci-terms` HEAD `65a7584c56df0757342632a5e567384ae739ed33`(2026-10-19T18:39:05+09:00). `LICENSE` = "Attribution-ShareAlike 4.0 International". `tables/` 에 YAML 28개, 6,771행. 스키마 `table.schema.yaml` 은 로캘 `en, ja, ko, zh-CN, zh-HK, zh-TW` 와 term 필드 `term · space · correspond · read · loan · norm` 을 정의한다. `yaml.safe_load` 로 센 결과 **항목 259개, 그중 `ko` 가 있는 것 259개** — [cjk-compsci-terms](https://github.com/dahlia/cjk-compsci-terms/tree/65a7584c56df0757342632a5e567384ae739ed33)
- 🔵 한국어 쪽은 두 꼴이다. 음차형은 `{term: 싱글톤, loan: singleton}`, 한자어형은 한자 키에 `read` 로 한글 음을 단다(`依存性 注入` → read `의 존 성` + `주 입`, `戰略` → `전 략`). 한글 표기를 얻으려면 `read` 를 이어 붙여야 한다 — [design-patterns.yaml](https://github.com/dahlia/cjk-compsci-terms/blob/65a7584c56df0757342632a5e567384ae739ed33/tables/design-patterns.yaml)
- 🔵 설계·공학 관련 표 내용: `design-patterns.yaml` 10항목 — design pattern(`設計 패턴` 과 `디자인 패턴` 두 갈래), singleton(`싱글톤`), factory(`팩토리`), observer(`옵저버`), adapter(`어댑터`), decorator(`데코레이터`), strategy(`戰略`/전략), MVC, dependency injection(`依存性 注入`/의존성 주입), interface(`인터페이스`). `software-eng.yaml` 10항목 — refactoring(`리팩토링`), debugging, unit test, integration test, deployment(`配布`/배포), code review, documentation, maintenance(`維持保守`/유지보수), agile, sprint. `architecture.yaml` 은 **컴퓨터 구조**(instruction set, register, ALU…)이지 소프트웨어 아키텍처가 아니다 — 같은 커밋의 [tables/](https://github.com/dahlia/cjk-compsci-terms/tree/65a7584c56df0757342632a5e567384ae739ed33/tables)
- 🔵 탐침 정확 일치(영어 키 소문자 비교): 맞음 = dependency injection, refactoring, singleton, adapter, decorator, observer, strategy, factory(GoF 의 "factory method"·"abstract factory" 와는 다른 일반 키), design pattern. 없음 = side effect, precondition, postcondition, invariant, coupling, cohesion, SOLID 다섯 원칙, inversion of control, encapsulation, information hiding, layered architecture, separation of concerns, circular dependency, call graph, idempotent, deterministic, technical debt, code smell, bounded context, ubiquitous language, 그리고 GoF 중 abstract factory · builder · factory method · prototype · bridge · composite · facade · flyweight · proxy · chain of responsibility · command · interpreter · iterator · mediator · memento · state · template method · visitor — 같은 커밋, 스크립트 `research-clones` 위에서 실행
- 🔵 `hwahyeon/terms-bridge`(HEAD `ff6e3ad`, 2025-07-14)는 Vite·React 앱이다. 용어 데이터는 저장소에 없고 `src/lib/supabase.ts` 로 외부 DB 에서 읽는다 → 커밋으로 고정할 수 없다 — [terms-bridge](https://github.com/hwahyeon/terms-bridge/tree/ff6e3ad)
- 🔵 `rust-kr/translation`(HEAD `c607197`, 2021-02-05)은 README 한 줄("번역 용어 등을 논의합니다.")뿐이다. 논의는 git 밖 이슈에 있다 — [rust-kr/translation](https://github.com/rust-kr/translation/tree/c607197997f0802c018d2968275388f4c1d5f7bc)
- 🟡 프레임워크·도구 전용이라 범위 밖으로 둔 것: `line/webpack.kr` 의 `glossary.json`, `kkweon/r-term-dict`(R 책 번역용), CNCF 클라우드 네이티브 용어집 한국어판(출시 때 18개 용어) — [webpack.kr glossary.json](https://www.github.com/line/webpack.kr/blob/kr/glossary.json); [r-term-dict](https://awesome.ecosyste.ms/projects/github.com%2Fkkweon%2Fr-term-dict); [CNCF 블로그 2022-09-23](https://www.cncf.io/blog/2022/09/23/cloud-native-glossary-the-korean-version-is-live/)
- 🟡 IREB CPRE 용어집 한국어판 2.1.0(PDF, 요구공학)이 공개되어 있고, IREB 와 ISTQB 용어집 사이의 용어 정렬이 이뤄졌다고 적는다. 이번 세션에서 PDF 받기는 실패했다(응답 코드 000) — [ireb_cpre_glossary_ko_2.1.0.pdf](https://cockpit.ireb.org/media/pages/downloads/cpre-glossary/fb04a92267-1742542398/ireb_cpre_glossary_ko_2.1.0.pdf)
- 🟡 ISTQB 한국 회원 단체 KSTQB 는 2005 년 설립. ISTQB 공식 용어집은 앱으로 배포되며, 회원 단체가 인터페이스를 번역할 수 있다. 한국어 용어집 일괄 내려받기는 찾지 못했다 — [KSTQB 회원 단체 페이지](https://www.istqb.org/directory/member-boards/kstqb); [ISTQB 용어집 앱 소식](https://istqb.org/news/posts/new-version-of-the-official-istqb-glossary-app-released)

### Inferences
- 💭 80 cjk-compsci-terms 는 기준 (1) 결정적, (2) 커밋 고정, (3) 오프라인(수백 KB 수준), (6) 항목별 명시적 짝을 모두 만족한다. 그러나 (4) 탐침 범위가 약하고, (5) CC BY-SA 4.0 이라 이 표에서 뽑은 행을 공개하면 동일조건 의무가 걸릴 수 있다. 법적 판단이므로 결론 내지 않는다.
- 💭 70 cjk-compsci-terms 는 표기가 실무 음차 쪽(`싱글톤` · `옵저버` · `리팩토링`)이다. 위키백과·refactoring.guru(`싱글턴` · `옵서버` · `리팩터링`)와 반대편에 서는 독립 출처라, 철자 변이 열의 근거로 값어치가 있다.
- 💭 65 IREB·ISTQB 한국어 용어집은 precondition·postcondition 같은 공학 개념어를 덮을 가능성이 있다(ISTQB 용어집에 이 표제가 있다는 것은 일반 지식이고 이번 세션에 확인하지 않았다). 다만 "국제 영어 어휘집의 번역판" 이라 다른 조사자 범위와 겹칠 수 있다.

### Gaps
- GitHub 검색 API 가 막혀, 한국어 번역 그룹의 일반 용어집 저장소를 체계적으로 훑지 못했다. 위 후보는 웹 검색으로만 찾은 것이다.
- IREB 한국어판 PDF 의 항목 수, 라이선스, 탐침 범위는 확인하지 못했다.
- 위키독스 번역 용어집(4절)의 기계 판독성과 라이선스는 확인하지 못했다.

## 6. 한국어 원저 공학서의 용어 규약 (예: 조영호 『오브젝트』)

### Takeaway
『오브젝트』를 비롯한 한국어 원저 설계서가 용어표나 표기 원칙을 공개했다는 자료는 찾지 못했다(🟡, 검색 1회). 이 갈래에서 근거로 쓸 만한 공개 자료는 이번 조사 범위에서 없다.

### Cited Findings
- 🟡 "조영호 오브젝트 책 용어 표기 원칙 영어 병기 용어집" 검색 결과는 무관한 분야(미술·군사·건축 용어집)만 나왔다 — [검색 결과 중 하나, gokams 미술 용어 안내](https://www.gokams.or.kr/visual-art/art-terms/intro/point.asp)

### Inferences
- 💭 60 원저서의 표기는 책 본문과 색인에만 있을 가능성이 높고, 저작물이라 기준 (5) 를 통과하기 어렵다.

### Gaps
- 저자 블로그·발표 자료·출판사(위키북스) 정오표 페이지는 따로 찾지 않았다. 검색이 한 번뿐이라 "없다" 는 결론은 약하다.

## 7. 출처별 기준 판정과 탐침 용어 교차표 (목표 항목)

### Takeaway
여섯 기준을 모두 만족하는 출처는 없다. **결정성·고정·오프라인·짝·라이선스를 깨끗하게 만족하는 것은 cjk-compsci-terms 하나인데, 탐침 범위가 가장 좁다.** 범위가 가장 넓은 것은 한국어 위키백과(개념어 약 20개 + 패턴 4개 확인)이고, 덤프로 받으면 결정성·고정·오프라인도 만족한다. 다만 이번 세션에서는 막혀 있었고 CC BY-SA 다. refactoring.guru/ko 는 GoF 이름을 가장 잘 덮지만 라이선스에서 막힌다. Microsoft Learn 한국어판은 짝이 없고 기계 번역 변이가 커서 "확립 용어" 근거로는 부적합하다. 탐침 개념어 중 **`circular dependency` · `layered architecture` · `deterministic` 은 이번에 본 어느 출처에서도 한국어 표기를 확인하지 못했다.**

### Cited Findings
기준 판정표 (근거는 위 1~6절의 인용과 같다):

| 출처 | (1) 결정적 | (2) 고정 | (3) 오프라인 | (4) 탐침 범위 | (5) 라이선스 | (6) 항목별 짝 | 표지 |
|---|---|---|---|---|---|---|---|
| refactoring.guru/ko 디자인 패턴 | 예(슬러그 맞춤) | 받은 날짜뿐 | 수집하면 가능 | GoF 22개(해석자 없음), 개념어 0 | All rights reserved, 링크 조건 재사용 · 그 밖은 허락 필요 | 슬러그로 얻음 | 🟡 |
| refactoring.guru/ko 리팩터링·스멜 | — | — | — | 한국어판 미확인 | 위와 같음 | — | 🟡 |
| MS Learn ko-kr Architecture Center · .NET 전자책 | 예(행·절 맞춤) | 영어만 커밋 `6d1df20`, 한국어는 날짜뿐 | 영어 저장소는 예, 한국어는 수집 필요 | DI·SRP·캡슐화·SoC·coupling·cohesion·DIP·idempotent·bounded context·ubiquitous language 등 일부 | 영어 저장소 CC BY 4.0 / 사이트 약관 개인·비상업 | 약어에만 병기, 그 밖은 정렬로 얻음 | 🔵 |
| 한국어 위키백과 (덤프) | 예 | 덤프 날짜 | 예(테이블 단위) | 개념어 약 20 / 28, 패턴 4 확인 | CC BY-SA 4.0 + GFDL | 첫 문장 괄호 병기 + 언어 간 링크 | 🟡 |
| `dahlia/cjk-compsci-terms` | 예(YAML) | 커밋 `65a7584` | 예 | 탐침 51개 중 8개 | CC BY-SA 4.0 | 예(en 키 ↔ ko 키) | 🔵 |
| 번역 고전서 본문·색인 | 손 조회 | 판·쇄 | 아니오(저작물) | 책마다 다름, 미측정 | 저작권 | 색인에 있을 것(미확인) | 🟡 |
| `WegraLee/Refactoring` | — | 커밋 `48bca38` | 예 | 용어표 없음 | LICENSE 없음 | 없음 | 🔵 |
| `hwahyeon/terms-bridge` | — | 불가(외부 DB) | 아니오 | 미측정 | 미확인 | — | 🔵 |
| IREB CPRE 용어집 ko 2.1.0 | 예(PDF) | 판 번호 2.1.0 | 예 | 미측정 | 미확인 | 미확인 | 🟡 |

탐침 교차표 (빈칸 = 이번에 확인 못 함, 출처 없음과 같은 뜻이 아님):

| 탐침 | 한국어 위키백과 🟡 | MS Learn ko-kr 🔵 | cjk-compsci-terms 🔵 | 번역서·기타 🟡 |
|---|---|---|---|---|
| side effect | 부작용 (컴퓨터 과학) | | 없음 | 『클린 코드』 목차 "부수 효과" |
| precondition | 전제 조건(precondition) · 선행조건 | | 없음 | |
| postcondition | 사후 조건(postcondition) · 후행조건 | | 없음 | |
| invariant | 불변조건 · 루프 불변성/불변량 | | 없음 | |
| coupling | 결합도(coupling) · 느슨한 결합 | 긴밀한 결합 · 느슨한 결합 | 없음 | |
| cohesion | 응집도(cohesion) | 응집력 | 없음 | |
| single responsibility principle | 단일 책임 원칙 | 단일 책임 원칙 | 없음 | |
| open-closed principle | 개방-폐쇄 원칙 | | 없음 | |
| Liskov substitution principle | 리스코프 치환 원칙 | | 없음 | |
| interface segregation principle | (SOLID 목록에 이름만) | | 없음 | |
| dependency inversion principle | 의존관계 역전 원칙 · 의존성 역전 | 종속성 반전 원칙 | 없음 | |
| dependency injection | 의존성 주입 | 종속성 주입 | 依存性 注入 (의존성 주입) | |
| inversion of control | 제어 반전 · 역제어 | | 없음 | |
| encapsulation | 캡슐화 (컴퓨터 프로그래밍) | 캡슐화 | 없음 | |
| information hiding | 정보 숨기기(관심사 분리 문서 안) | | 없음 | |
| layered architecture | | | 없음 | |
| separation of concerns | 관심사 분리 | 문제의 분리 · 우려의 분리 | 없음 | |
| circular dependency | | | 없음 | |
| call graph | 호출 그래프 | | 없음 | |
| idempotent | 멱등법칙 · 멱등원 | 멱등 소비자 | 없음 | |
| deterministic | | | 없음 | |
| technical debt | 기술 부채 | | 없음 | |
| code smell | 코드 스멜 | | 없음 | |
| refactoring | 리팩터링 | | 리팩토링 | 『리팩터링 2판』(초판 『리팩토링』) · refactoring.guru/ko "리팩터링" |
| bounded context | (DDD 문서 "정해진 맥락") | 제한된 · 바인딩된 · 경계가 있는 · 경계가 지정된 · 경계된 · 경계가 설정된 컨텍스트 | 없음 | 블로그 다수 "바운디드 컨텍스트" |
| ubiquitous language | | 유비쿼터스 언어 | 없음 | |
| GoF 23 | 옵서버 · 싱글턴 · 데코레이터 · 비지터 패턴 | | 싱글톤 · 옵저버 · 어댑터 · 데코레이터 · 전략 | refactoring.guru/ko 22개(싱글턴 · 옵서버 · 비지터 · 퍼사드 · 플라이웨이트 · 복합체 · 반복자 · 책임 연쇄 · 중재자 · 메멘토 …), 『헤드 퍼스트』 옵저버 · 싱글턴, GoF 한국어판(추정) 원형 · 단일체 · 적응자 |

표기 변이 관찰(🟡/🔵 혼합, 위 인용과 같음):
- Observer: `옵서버`(위키백과 표제, refactoring.guru/ko) vs `옵저버`(cjk-compsci-terms 🔵, 『헤드 퍼스트』 목차) vs `감시자`(GoF 한국어판으로 추정, 미확인).
- Singleton: `싱글턴`(위키백과, refactoring.guru/ko, 『헤드 퍼스트』) vs `싱글톤`(cjk-compsci-terms 🔵) vs `단일체`(🟡 스니펫).
- Refactoring: `리팩터링`(위키백과, 2판, refactoring.guru/ko) vs `리팩토링`(cjk-compsci-terms 🔵, 1판 제목).

### Inferences
- 💭 75 같은 음차라도 `옵서버`/`옵저버`, `싱글턴`/`싱글톤` 이 출처 계열에 따라 깔끔하게 갈린다. 표준 표기를 따르는 쪽(위키백과·refactoring.guru)과 실무 관행 쪽(cjk-compsci-terms·『헤드 퍼스트』)이다. ko-dev-terms 가 승자를 고르지 않고 이 두 줄을 출처와 함께 나란히 내면, 쓰는 사람이 문서 성격(공식·실무)에 맞춰 고를 수 있다.
- 💭 70 개념·공학 어휘의 공백(앞선 보고서의 `postcondition` 0건)은 위키백과가 가장 많이 메운다(호어 논리·LSP 문서). 그러니 앞선 보고서의 K8(Wikidata·위키백과 덤프 시범 측정)이 이 갈래에서도 1순위다.
- 💭 65 `circular dependency` · `layered architecture` · `deterministic` 의 공백은 이번 출처들로는 메워지지 않는다. 이들은 공식 사전(TTA 등, 다른 조사자 범위)이나 괄호 병기 채굴 쪽에 기대야 할 것으로 보인다.

### Gaps
- 위키백과 수치("약 20 / 28")는 스니펫에 표제가 나온 것만 센 하한이다. 덤프로 다시 재야 한다.
- refactoring.guru 22개 이름 중 6개(추상 팩토리 · 빌더 · 상태 · 전략 · 템플릿 메서드 · 커맨드 표제)는 문자 그대로 확인하지 못했다.
- 복제한 저장소(`research-clones/` 아래 5개)는 측정 뒤 지웠다. 위 커밋 해시로 다시 받을 수 있다.
