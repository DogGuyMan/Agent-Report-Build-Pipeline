# ktword.co.kr 와 한국 공식·국가 출처의 언어 불문 소프트웨어 공학·설계 용어 (2026-10-28 기준)

표지: 🔵 이번 세션 실측 · 🟡 검색 결과 요약(snippet) · 💭 추론. 정수는 확신도(0~100).

**네트워크 실측 🔵.** `WebFetch http://www.ktword.co.kr` → `getaddrinfo ENOTFOUND`. `curl http://www.ktword.co.kr/robots.txt` → `Could not resolve host`, `https://…/robots.txt` → `CONNECT tunnel failed, response 403`, Wayback(`web.archive.org`) 사본도 `403`. 아래 16개 호스트는 `curl https://<host>/` 가 전부 `000`(연결 실패)이었다: `www.ncs.go.kr` `ncs.go.kr` `www.q-net.or.kr` `standard.go.kr` `www.standard.go.kr` `e-ks.kr` `www.kiise.or.kr` `www.kips.or.kr` `tta.or.kr` `www.tta.or.kr` `standard.tta.or.kr` `terms.tta.or.kr` `www.kssn.net` `www.kodl.or.kr` `itwiki.kr` `koreascience.kr`. **그래서 이 노트의 출처 내용은 전부 🟡 다.** 게다가 이 세션의 WebSearch 는 원문 snippet 이 아니라 **검색 도구가 요약한 글**을 돌려준다. 요약 안의 따옴표 인용도 원문 그대로라는 보장이 없다. 보고서에 인용할 때는 "검색 요약에 따르면" 으로 한정해야 한다. 이 노트를 다시 확인하려면 세션 네트워크 허용 목록에 `www.ktword.co.kr`(과 `ktword.co.kr`) · `www.ncs.go.kr` · `www.q-net.or.kr` · `standard.go.kr` 를 넣어야 한다.

## ktword.co.kr (정보통신기술용어해설) — 운영 주체 · 규모 · 소프트웨어 공학 범위 · 영한 짝 · 이용 조건 · 고정 수단

### Takeaway
ktword 는 차재복(Cha Jae Bok) 개인이 2002년부터 운영하는 "개인연구실" 사이트다. 해설 약 6,800건이 있고, "원출처를 밝히는 한 자유롭게 사용(상업화 포함)" 을 허락한다. 영어 표제어 뒤에 한국어 변형을 여러 개 나열하는 표제 형식이 있어서 ko-dev-terms 의 '승자 없이 후보 나열' 모델과 잘 맞는다. 다만 탐침 용어 16개 중 소프트웨어 공학 의미로 잡힌 것은 6~7개이고, 그나마 대부분 "소프트웨어 설계" · "소프트웨어 아키텍처" · "모듈" 같은 개요 항목 안의 하위 항목으로 들어 있다. 일괄 내려받기나 API 는 보이지 않고, 사이트가 계속 편집되고 있어 날짜 고정이 필요하다.

### Cited Findings
**운영 주체 · 연혁**
- 사이트는 스스로를 "정보통신 및 과학기술 지식을 간결하게 정리,체계화시키고 있는 개인연구실" 이라 소개하고, 하단에 "Copyright ⓒ 차재복 (Cha Jae Bok)" 이라고 적는다 🟡80 — [ktword 홈](http://www.ktword.co.kr/)
- 한 페이지에 "Copyrightⓒ since 2002 written by Cha Jae Bok" 이 있다. 도메인 등록인·책임자가 차재복이고 등록일이 2004년이라는 기록도 있다 🟡65. 검색 요약이 이 두 사실을 어느 URL 에서 가져왔는지 특정하지 못했다. 후보는 다음 셋이다 — [lhb.kr 사이트 소개 기사](https://lhb.kr/news/article.html?no=2821); [website.informer.com](https://website.informer.com/ktword.co.kr); [clien 소개 글](https://www.clien.net/service/board/useful/363153)
- 같은 검색에서 "기술사" 같은 운영자 자격은 확인되지 않았다 🟡70 — 위 검색 결과 동일.
- **TTA 와는 별개다.** 검색 도구는 "정보통신용어사전" 을 TTA(terms.tta.or.kr)와 섞어 요약하는 경향이 있었다. 그러나 ktword 저작권 표기는 개인 명의다 🟡75 — [ktword 홈](http://www.ktword.co.kr/); TTA 쪽은 [bartoc.org TTA 항목](https://bartoc.org/en/node/20286)

**규모 · 갱신**
- 홈 캐시는 "1,655개 분류 6,818건 해설" 이다. "용어해설 종합" 페이지의 스냅숏마다 1,661/6,851 · 1,649/6,782 · 1,648/6,780 으로 값이 다르다 🟡75 — [ktword 홈](http://www.ktword.co.kr/); [yoyak_v2 no=1858](http://ktword.co.kr/test/navigation/yoyak_v2.php?no=1858); [yoyak_v2 no=5641](http://www.ktword.co.kr/test/navigation/yoyak_v2.php?no=5641)
- "용어해설 편집이력" 페이지가 있다. 전체 레코드 수는 6836 이고, 가장 최근 편집 항목은 **2026년 9월 초** 날짜다 🟡65 — [history.php](http://www.ktword.co.kr/test/history/history.php)

**영한 짝 형식 (표제)**
- 검색에 잡힌 표제 가운데 **영어 표제어 + 한국어 변형 여러 개** 꼴이 있다. 예: "Life Cycle 순기, 생명 주기, 라이프 사이클" 🟡85 — [no=1200](http://www.ktword.co.kr/test/view/view.php?no=1200); "Spanning Tree 스패닝 트리, 신장 트리, 생성 트리" — [no=3444](http://www.ktword.co.kr/test/view/view.php?no=3444); "Coupler 커플러, 결합기" — [no=3812](http://www.ktword.co.kr/test/view/view.php?no=3812); "Convolution 콘벌루션, 콘볼루션, 컨벌루션, 컨볼루션, 길쌈 ..." — [no=1147](http://www.ktword.co.kr/test/view/view.php?no=1147)
- 소프트웨어 공학 쪽 항목은 표제가 **한국어뿐**으로 잡혔다. "소프트웨어 설계", "소프트웨어 아키텍처", "모듈", "부수 효과 [전산]", "인터페이스 [전산]" 이 그렇다. 대괄호 `[전산]` 은 분야 구분 표지로 보인다 🟡75 — [no=6552](http://www.ktword.co.kr/test/view/view.php?no=6552); [no=6543](http://www.ktword.co.kr/test/view/view.php?no=6543); [no=2226](http://www.ktword.co.kr/test/view/view.php?no=2226); [no=6742](http://www.ktword.co.kr/test/view/view.php?no=6742); [no=3021](http://www.ktword.co.kr/test/view/view.php?no=3021)
- 본문 안에서는 괄호 병기를 쓴다. 예: "결합도 (Coupling) : (낮을수록 좋음)" (모듈 항목) 🟡70 — [no=2226](http://www.ktword.co.kr/test/view/view.php?no=2226); "단일 책임의 원칙 (Single Responsibility Principle, SRP)" (소프트웨어 설계 항목) 🟡70 — [no=6552](http://www.ktword.co.kr/test/view/view.php?no=6552)

**탐침 용어 16개 결과** (`allowed_domains: ktword.co.kr` 검색 7회. 각 행이 무엇을 뜻하는지는 아래 범례와 같다.)

| 탐침 용어 | ktword 에서 보인 것 | 항목 · URL | 표지 |
|---|---|---|---|
| side effect | 독립 항목 "부수 효과 [전산]". 정의는 "함수나 연산이 실행될 때, 의도한 결과 외에 추가적인 상태 변화가 발생하는 현상" 이고 순수 함수·불변 데이터를 다룬다. 본문에 영어 "Side Effect" 가 병기됐는지는 요약으로 확인 불가 | [no=6742](http://www.ktword.co.kr/test/view/view.php?no=6742) | 🟡70 |
| postcondition | 못 찾음 | — | 🟡60 (부재) |
| invariant | 못 찾음. 신호처리 "시불변" 만 나옴 | [no=3621](http://www.ktword.co.kr/test/view/view.php?no=3621) | 🟡60 (부재) |
| coupling | "모듈" 항목 안 "결합도 (Coupling)". 독립 항목은 못 찾음. "결합 계수" · "커플러" 는 전자·통신 의미 | [no=2226](http://www.ktword.co.kr/test/view/view.php?no=2226) · [m_temp1=5903](http://www.ktword.co.kr/abbr_view.php?m_temp1=5903) | 🟡70 |
| cohesion | "모듈" 항목 안 응집도 설명. 영어 병기는 요약에 안 보임 | [no=2226](http://www.ktword.co.kr/test/view/view.php?no=2226) | 🟡55 |
| single responsibility principle | "소프트웨어 설계" 안 "단일 책임의 원칙 (Single Responsibility Principle, SRP)" | [no=6552](http://www.ktword.co.kr/test/view/view.php?no=6552) | 🟡70 |
| dependency inversion principle | "소프트웨어 설계" 안 "고수준 모듈이 저수준 모듈에 의존해서는 안 되며, 추상화에 의존해야 함". 한국어 표제어와 영어 병기는 요약에 안 보임 | [no=6552](http://www.ktword.co.kr/test/view/view.php?no=6552) | 🟡55 |
| design pattern / observer pattern | "소프트웨어 설계" 안에 싱글톤 · 어댑터 · 데코레이터 · 팩토리 메소드 · 상태 패턴 · MVC · 옵저버 패턴이 나열됨. 독립 항목은 못 찾음. 제어공학 "옵저버(observer, 상태 추정기)" 동음이의 항목이 따로 있음 | [m_temp1=6552&id=518](http://www.ktword.co.kr/test/view/view.php?m_temp1=6552&id=518) · [no=6895](http://www.ktword.co.kr/test/view/view.php?no=6895) | 🟡65 |
| layered architecture | "소프트웨어 아키텍처" 안 계층형 아키텍처(프레젠테이션 · 비즈니스 · 데이터 계층)와 MVC. 일반 원리는 "계층화" 항목 | [no=6543](http://www.ktword.co.kr/test/view/view.php?no=6543) · [no=1088](http://www.ktword.co.kr/test/view/view.php?no=1088) | 🟡70 |
| circular dependency | 못 찾음. 그래프 "사이클" 정의만 나옴 | [no=5226](http://www.ktword.co.kr/test/view/view.php?no=5226) | 🟡55 (부재) |
| call graph | 못 찾음. "재귀 호출" · "그래프 알고리즘" 만 나옴 | [m_temp1=5938](http://www.ktword.co.kr/test/view/view.php?m_temp1=5938) | 🟡55 (부재) |
| idempotent | 수학 의미만 나옴. "집합 연산" 의 멱등성(f(f(x)) = f(x)), "부울 대수 정리" 의 A·A = A. 소프트웨어(HTTP · 재시도) 의미 항목은 못 찾음 | [no=4084](http://www.ktword.co.kr/test/view/view.php?no=4084) · [no=5543](http://www.ktword.co.kr/test/view/view.php?no=5543) | 🟡60 |
| technical debt | 못 찾음 | — | 🟡55 (부재) |
| code smell | 못 찾음 | — | 🟡55 (부재) |
| refactoring | 못 찾음. "역공학" · "컴포넌트" · "Life Cycle" · "CM" 만 나옴 | [no=2666](http://www.ktword.co.kr/test/view/view.php?no=2666) | 🟡55 (부재) |

범례: "못 찾음" 은 검색 엔진 색인에 안 잡혔다는 뜻이다. 사이트에 없다는 증명이 아니다(그래서 확신도를 낮게 붙였다).

**식별자 · 고정 수단**
- 같은 항목이 `test/view/view.php?no=N`, `test/view/view.php?m_temp1=N`, `abbr_view.php?m_temp1=N` 세 꼴 URL 에 같은 정수 N 으로 나온다. 예: 결합 계수 5903, 커플러 3812 🟡80 — [abbr_view m_temp1=5903](http://www.ktword.co.kr/abbr_view.php?m_temp1=5903); [view m_temp1=5903](http://www.ktword.co.kr/test/view/view.php?m_temp1=5903); [view no=3812](http://www.ktword.co.kr/test/view/view.php?no=3812); [abbr_view m_temp1=3812](http://www.ktword.co.kr/abbr_view.php?m_temp1=3812)
- 공식 API, 내보내기(export), 덤프는 검색에서 하나도 나오지 않았다 🟡55 (부재). robots.txt 는 받지 못했다 🔵(접속 실패).

**이용 조건**
- "본 웹사이트 내 모든 저작물은 원출처를 밝히는 한 자유롭게 사용(상업화포함) 가능합니다" 라는 문구가 여러 페이지에 반복된다 🟡80 — [ktword 홈](http://www.ktword.co.kr/); [IT 항목](http://www.ktword.co.kr/abbr_view.php?m_temp1=305); [DRM 항목](http://www.ktword.co.kr/test/view/view.php?m_temp1=2392)

### Inferences
- 💭70 SE·설계 항목의 번호(6543 · 6552 · 6742)는 관측된 최대 번호(6895) 근처에 몰려 있다. 번호가 순차 발급이라면 소프트웨어 공학 범위는 **최근에 추가된 얇은 층**이다. 사이트의 중심은 여전히 통신·전자·신호처리다.
- 💭75 범위 판정: 16개 중 소프트웨어 공학 의미로 잡힌 것은 6~7개(side effect · coupling · cohesion · SRP · DIP · 디자인 패턴/옵저버 · layered architecture)다. 그중 독립 항목은 side effect 하나뿐이고, 나머지는 개요 항목 안의 줄이다. postcondition · invariant · circular dependency · call graph · technical debt · code smell · refactoring 은 공백이다. 앞선 보고서가 짚은 "개념·공학 어휘 공백" 을 ktword 는 **일부만** 메운다.
- 💭70 ko-dev-terms 의 행 단위는 "항목" 이 아니라 "**항목 + 본문 안 괄호 병기 한 줄**" 이 되어야 한다. 소프트웨어 공학 어휘가 대부분 개요 항목 안에 들어 있기 때문이다. 영어를 입력으로 받아 본문의 `한국어 (English…)` 패턴을 찾는 방식은 기존 괄호 병기 채굴 규칙을 그대로 쓸 수 있다.
- 💭65 옛 항목의 표제 꼴("Life Cycle 순기, 생명 주기, 라이프 사이클")은 영어 1개 : 한국어 n개를 저자가 직접 나열한 것이다. 근거 행으로는 가장 깨끗한 꼴이다(정렬이 저자 손으로 주어짐). 하지만 새 SE 항목에서는 이 꼴이 안 보인다. 영어 원문이 명시적으로 붙어 있는지(기준 6)는 **항목마다 다르다**.
- 💭70 수치가 스냅숏마다 다르고(6,780 → 6,851) 2026-09 편집 이력이 있다. 그러니 살아 있는 사이트다. 고정하려면 `no` 정수 + 받은 날짜 + 본문 sha256 을 행에 실어야 한다. 편집이력 페이지(history.php)를 함께 저장하면 받은 시점 이후 변경을 감지할 수 있다.
- 💭60 이용 문구는 출처 표시만 요구하는 관대한 허락이다(상업 이용 포함). 파생 행 공개에 유리하다. 다만 표준 라이선스(CC 등)가 아니고, 크롤링·전량 복제·데이터베이스 재배포를 명시적으로 다루지 않는다. 한국 저작권법에는 데이터베이스제작자 보호가 따로 있다(일반 지식, 이 세션에서 조문 미확인). 그러니 **사이트 전체를 로컬에 복제하는 것**은 운영자에게 묻는 편이 안전하다. 법적 판단은 하지 않는다.
- 💭55 개인 운영이라는 점은 '권위 출처(①)' 로 분류할지 '사용 근거(②)' 로 분류할지의 문제를 남긴다. 국가 표준이 아니라 한 전문가의 해설이므로, ①의 하위 표지("개인 해설 사전")로 따로 두는 편이 정직해 보인다.

### Gaps
- robots.txt 내용, 크롤링 허용 여부: 접속이 막혀 확인 못 함 🔵.
- 항목별 작성·수정 날짜가 본문에 표시되는지: 검색 요약에 없음.
- side effect · cohesion · DIP 항목 본문에 영어가 병기됐는지: 요약이 원문 글자를 보여 주지 않음. 원문 확인 필요.
- 소프트웨어 공학 전용 분류(카테고리) 트리가 있는지와 그 하위 항목 수: `id=` 파라미터(예: `id=518`)가 분류 번호로 보이지만 💭50, 분류명은 확인 못 함.
- 운영자의 서면 허락이 있으면 전량 복제가 가능한지: 연락 경로가 사이트에 공개돼 있다는 검색 결과는 있다(이 노트에는 개인 연락처를 적지 않는다). 문의는 사용자 몫.

## TTA — 정보통신용어사전과 별개인 소프트웨어 공학 용어 표준(TTAS/TTAK)이 있는가

### Takeaway
TTA 단체표준 가운데 "소프트웨어 공학 용어" 를 다루는 TTAS/TTAK 문서는 검색으로 찾지 못했다. TTA 의 용어 활동은 정보통신용어표준화 분과위원회를 통한 정보통신용어사전이 중심이다. 그 사전의 오프라인 경로 문제는 앞선 보고서가 이미 다뤘다.

### Cited Findings
- TTA 는 1991년부터 정보통신용어표준화 **4개 분과위원회(전기통신, 무선·방송, 정보기술, 데이터통신 및 S/W)** 와 심의위원회를 두고 용어 표준화를 해 왔다 🟡75 — [지식정보인프라 논문 JAKO200370709953124](https://koreascience.kr/article/JAKO200370709953124.pdf)
- 2003년 1차 분과위원회 회의에서는 제안된 254개 용어 가운데 164개를 사전 수록 용어로 골랐다(그 시점 회의 결과일 뿐 전체 규모는 아님) 🟡65 — 같은 논문
- TTA 소프트웨어 단체표준의 번호 예로 "소프트웨어 재사용 분류체계표준, TTAS.KO-11.0026, 2000" 이 학술 논문 참고문헌에 인용돼 있다. 용어 표준 번호는 나오지 않았다 🟡65 — [koreascience JAKO201426955812688](https://koreascience.kr/article/JAKO201426955812688.pdf) 계열 검색 결과(어느 논문의 참고문헌인지 요약이 특정하지 않음)
- 'TTAK.KO 24765' 로 검색해도 TTA 판 24765 는 나오지 않고 국제 표준 자료만 나왔다 🟡60 — [IEEE SA 24765](https://standards.ieee.org/ieee/24765/6800)

### Inferences
- 💭60 TTA 가 소프트웨어 공학 어휘를 별도 단체표준으로 냈다면, 24765 같은 국제 표준을 부합화한 TTAK.KO-ISO/IEC… 꼴이었을 가능성이 높다. 그런 번호가 검색에 전혀 안 잡히므로 없거나, 있어도 웹에 드러나지 않는다.
- 💭70 있더라도 TTA 표준 열람은 표준 포털(standard.tta.or.kr) 로그인·내려받기 방식일 것이다. 파생 행 공개 조건은 별도로 확인해야 한다.

### Gaps
- standard.tta.or.kr 에서 "용어" · "소프트웨어 공학" 을 직접 검색하지 못했다(접속 차단 🔵). 이 질문의 최종 답은 그 포털 검색 한 번으로 정해진다.

## KS 국가표준 — ISO/IEC/IEEE 24765 · ISO/IEC 2382 의 KS 부합화, KS X 0001

### Takeaway
"KS X ISO/IEC/IEEE 24765" 와 "KS X ISO/IEC 2382" 는 검색에서 존재를 확인하지 못했다. 정보처리 용어 KS 는 KS X 0001 시리즈로 알려져 있지만 소프트웨어 부(part)의 번호·한국어 수록·가격은 확인하지 못했다. 국제 원본인 24765:2017 은 현행이고 3판이 위원회 초안(CD) 단계이며, 2382:2015 는 영어·프랑스어 2개 언어판이다. 어느 쪽이든 한국어 용어는 KS 부합화판에만 들어갈 수 있다.

### Cited Findings
- ISO/IEC/IEEE 24765:2017(2판)은 IEC 웹스토어에 현행 국제 표준으로 올라 있고 날짜는 2017-09-06 이다. 시스템 및 소프트웨어 공학의 공통 어휘를 제공한다 🟡80 — [IEC webstore 61433](https://webstore.iec.ch/en/publication/61433)
- 2010년판은 2017년판으로 대체됐다 🟡80 — [IEEE SA 24765-2010](https://standards.ieee.org/ieee/24765/4750/)
- 3판 위원회 초안(CD)이 진행 중이고 2017년판을 대체할 예정이다 🟡70 — [ISO 92875](https://www.iso.org/standard/92875.html)
- 24765 는 ISO/IEC JTC 1/SC 7 이 IEEE Computer Society 와 함께 만들었다 🟡75 — [NASA SWEHB 사본](https://swehb.nasa.gov/download/attachments/16450104/c071952_ISO_IEC_IEEE_24765_2017.pdf?api=v2)
- "KS X ISO/IEC/IEEE 24765" · "KS X ISO/IEC 24765" 정확 일치 검색(extended)에서 KS 판은 하나도 나오지 않았다 🟡60 (부재) — 같은 검색
- ISO/IEC 2382:2015 는 2015-04-29 발행본이다. 용어와 정의를 **두 언어로** 싣는다(검색 요약) 🟡70 — [IEC webstore 2382](https://webstore.iec.ch/en/publication/22380); [Standard Norge](https://online.standard.no/en/isoiec-2382-2015-2)
- 앞선 보고서는 KS X 0001-1 을 제3자 목록에서 확인했다 🟡 — [ndls.org.cn KS X 0001-1](https://ndls.org.cn/standard/detail/d6c6c7e9c0fb2d2ebd28edcf06ba080c). 이번 검색 2회("KS X 0001" 정보 처리 용어 소프트웨어 부 / 영문)는 KS X 1001(문자 부호) 결과만 냈다 🟡 (부재)
- 옛 KS C 5[6-8]xx 정보 표준은 KS X 번호로 바뀌었다. 그래서 옛 번호로 남은 자료가 KS X 검색에 안 걸릴 수 있다 🟡70 — [Unicode 메일링 리스트](https://unicode.org/mail-arch/unicode-ml/Archives-Old/UML012/0566.html)
- 역사 자료: 1991년 정부가 컴퓨터 용어 113종을 표준화했다(디렉토리 → 목록, 백업 → 보관) 🟡70 — [서울신문 1991-10-15](https://www.seoul.co.kr/news/1991/10/15/19911015006004). 1996년에는 남북이 ISO 2382 를 바탕으로 컴퓨터 용어 약 2,100개에 합의하고 공동 정보처리용어사전을 내기로 했다는 보도가 있다(출간 여부는 미확인) 🟡65 — [서울신문 1996-08-30](https://www.seoul.co.kr/news/1996/08/30/19960830031001)

### Inferences
- 💭65 한국어 소프트웨어 공학 어휘의 국가표준 후보는 사실상 KS X 0001 의 해당 부뿐이다. 그 원천인 ISO/IEC 2382 계열은 2015년에 하나로 통합됐다. KS 쪽이 옛 다부(多部) 구성을 그대로 두고 있다면 내용이 오래됐을 수 있다.
- 💭75 KS 문서는 유료 판매 또는 열람 제한이 일반적이라, 오프라인 저장과 파생 행 공개(기준 3·5) 모두 막힐 가능성이 높다. 고정 수단(기준 2)은 표준 번호 + 제정·개정 연도로 깔끔하다.
- 💭60 1991년 113종 같은 정부 표준화는 "목록 · 보관" 처럼 지금 개발자가 쓰지 않는 순화어를 담고 있다. 권위 출처 행으로 실으면 "공식이지만 안 쓰이는" 표기의 대표 사례가 된다. ①과 ②를 나눈 계획 설계의 실례다.

### Gaps
- KS X 0001 의 부 목록, 소프트웨어 부 번호, 한국어·영어 병기 여부, 가격: e-나라표준인증(standard.go.kr) 접속 차단 🔵 · 검색 미검출.
- 24765 의 KS 부합화가 정말 없는지: 국가표준 검색 한 번으로 정해지는데 차단됐다.

## 정부 학습 자료 — NCS 학습모듈 · 정보처리기사 출제기준

### Takeaway
NCS 응용SW엔지니어링 학습모듈(애플리케이션 설계 · 개발)은 2014·2018 판이 학술 논문에 인용될 만큼 실재하고, 교육부가 해마다 개발·보완한다. 그러나 이용 조건(공공누리 유형)과 영어 병기 여부는 확인하지 못했다. 정보처리기사 출제기준은 주제 목록(syllabus)일 뿐 용어집이 아니다. 2026 기준 세부항목에 "객체지향(OOP) · 디자인패턴" 이 있고, 2027-01-01 부터 새 기준이 적용된다. 제3자 위키 전사본에는 영어 병기가 없다.

### Cited Findings
- "한국산업인력공단, NCS 학습 모듈 - 응용SW엔지니어링 학습모듈/03 애플리케이션 개발" 이 2014년판·2018년판으로 학술 논문에 인용됐다 🟡70 — [koreascience JAKO201908662573123](https://koreascience.or.kr/article/JAKO201908662573123.page?lang=en)
- NCS 능력단위요소 코드에는 판 표시가 붙는다. 예: "2001020211_16v4"(배치 프로그램 구현하기) 🟡55 — [sw-sury.tistory.com](https://sw-sury.tistory.com/category/%EC%9E%90%EA%B2%A9%EC%A6%9D?page=32)
- 교육부가 NCS 학습모듈 개발·보완 현황을 발표하고 "질 관리 강화 방안" 을 세우겠다고 했다(2026-07-17 기사) 🟡60 — [한국교육신문 2026-07-17](https://hangyo.com/news/article.html?no=79905)
- NCS 학습모듈의 저작권·공공누리 표시는 검색 2회로 확인되지 않았다. 확인된 것은 민간 판매자 한 명의 주장뿐이다. 그 판매자는 "원 자료의 신문기사, 도서, 이미지 등 원 저작권자가 존재하는 정보를 제외하는 것을 전제로 상업적 이용 허가를 받은 자료" 라고 적었다 🟡50 — [kmong 367527](https://kmong.com/gig/367527)
- 공공누리 유형: 1유형은 출처 표시만 하면 상업 이용·변경 가능, 2유형은 상업 이용 금지, 3유형은 변경 금지, 4유형은 둘 다 금지. 1~4유형 모두 출처 표시가 의무다 🟡80 — [한국저작권위원회 공공누리 안내](https://copyright.or.kr/gov/nuri/rule_info/index.do)
- 정보처리기사 필기 2026 출제기준: 적용 2026.01.01~2026.12.31, 객관식 100문항, 2시간 30분. '소프트웨어설계' 과목 '애플리케이션 설계' 주요항목 아래 '객체지향 설계' 세부항목에 "객체지향(OOP)" · "디자인패턴" 이 있다 🟡70 — [IT위키 필기 출제기준](https://www.itwiki.kr/w/%EC%A0%95%EB%B3%B4%EC%B2%98%EB%A6%AC%EA%B8%B0%EC%82%AC_%ED%95%84%EA%B8%B0_%EC%B6%9C%EC%A0%9C%EA%B8%B0%EC%A4%80)
- 2027 출제기준: 적용 2027.1.1~2029.12.31, 객관식 4과목 80문항, 2시간. 위키는 근거를 "Q-Net 정보처리기사 종목 정보 > 출제기준" 의 「정보처리기사 출제기준(2027.1.1 ~ 2029.12.31)」으로 적었다. 주요항목(요구사항 확인 · 화면 설계 · 애플리케이션 설계 · 인터페이스 설계 등)과 세부항목이 **한국어로만** 나열돼 있다 🟡65 — [IT위키 2027년 출제기준](https://www.itwiki.kr/w/%EC%A0%95%EB%B3%B4%EC%B2%98%EB%A6%AC%EA%B8%B0%EC%82%AC/2027%EB%85%84_%EC%B6%9C%EC%A0%9C%EA%B8%B0%EC%A4%80)
- 실기 출제기준은 2026 기준과 2027~2029 기준이 같다(위키) 🟡55 — [IT위키 실기](https://www.itwiki.kr/w/%EC%A0%95%EB%B3%B4%EC%B2%98%EB%A6%AC%EA%B8%B0%EC%82%AC_%EC%8B%A4%EA%B8%B0)

### Inferences
- 💭70 출제기준은 결정적이고(PDF 한 장) 적용 기간으로 고정되므로(기준 1·2 충족), 판(version) 개념이 가장 분명한 공식 문서다. 그러나 항목이 "디자인패턴" 수준의 주제명이고 영어 병기가 없어 보인다(기준 4·6 미흡). 영한 근거 행으로는 거의 쓸모가 없다.
- 💭60 NCS 학습모듈은 교재 산문이라 괄호 병기 채굴 대상이 될 수 있다. 정보처리기사 수험서 관행상 "결합도(Coupling)" 꼴 병기가 흔하지만, 학습모듈 자체에서 확인한 것은 아니다. 판 표시(`_16v4`)와 해마다 보완된다는 점은 고정에 유리하다. 파일이 PDF·HWP 라면 텍스트 추출이 결정적인지(추출기 판 고정)라는 별도 위험이 생긴다.
- 💭55 공공누리 유형이 확인되지 않는 한 파생 행 공개(기준 5)는 보류해야 한다. 2·4유형이면 상업 배포가 막히고, 3·4유형이면 변경(행 추출) 자체가 걸릴 수 있다.

### Gaps
- ncs.go.kr 학습모듈 다운로드 방식(로그인 여부), 파일 형식, 공공누리 유형, 본문 영어 병기 여부: 접속 차단 🔵 · 검색 미검출.
- Q-Net 출제기준 PDF 원문의 영어 병기 여부: 원문 미확인(위키 전사본만 봄).
- 애플리케이션 설계 학습모듈의 현행 판 번호와 마지막 개정일.

## 학회 용어집 — 한국정보과학회(KIISE) · 한국정보처리학회(KIPS), 2026년 재확인

### Takeaway
2026-10-28 검색 2회에서도 KIISE 나 KIPS 가 발행한 컴퓨터 과학·소프트웨어 공학 영한 용어집은 나오지 않았다. 남은 흔적은 1994년 전산기 용어 검토위원회, KIPS 학술대회의 ISO 2382 기반 남북 IT 용어 대조 연구, 1996년 남북 합의 보도뿐이다.

### Cited Findings
- 1994년 컴퓨터 용어 순화는 학회들이 공동으로 꾸린 "<전산기 용어 검토위원회>" 의 재검토와 국어심의회 의결을 거쳐 정해졌다. 요약에 학회 이름이 "…보학회" 로 잘려 있어 어느 학회인지 확인되지 않는다 🟡55 — [국립국어원 새국어생활 2001 PDF](https://www.korean.go.kr/nkview/nklife/2001_1/2001_0105.pdf)
- ISO 2382 를 기준으로 남북한 IT 용어를 대조하는 표준체계 연구가 한국정보처리학회 추계학술대회 논문집에 있다. 용어집 발행은 확인되지 않았다 🟡60 — [koreascience CFKO201221868478307](https://koreascience.kr/article/CFKO201221868478307.pdf)
- KIISE 공식 용어 사전은 확인되지 않았다(검색 요약) 🟡60 (부재) — 같은 검색 결과

### Inferences
- 💭65 학회 용어집이 있다 해도 오래된 인쇄본일 가능성이 높다. 기계 판독 가능한 공개 판(기준 3)은 기대하기 어렵다. 이 갈래는 ko-dev-terms 출처 후보에서 빼도 손실이 작아 보인다.

### Gaps
- kiise.or.kr · kips.or.kr 자료실을 직접 보지 못했다(접속 차단 🔵). 1994년 위원회 참여 학회 이름(원문 PDF 확인 필요).

## 기준 6개로 본 종합 판정

### Takeaway
이번 범위에서 ko-dev-terms 에 실제로 보탬이 될 후보는 ktword 하나다. 이유는 셋이다: 출처 표시만 하면 상업 이용까지 허락하고, 영어 원어를 표제나 본문 괄호에 저자가 직접 붙이며, 정수 항목 번호가 있다. 그러나 일괄 경로가 없어 "손 조회 기록" 이나 "운영자 허락 후 수집" 꼴이 된다. 공학 개념 어휘 공백(postcondition · invariant · circular dependency · call graph · technical debt · code smell · refactoring)은 그대로 남는다. 국가표준(KS)·TTA 단체표준·학회 용어집은 존재 확인부터 막혔다. NCS·출제기준은 고정은 쉽지만 영한 짝과 이용 조건이 불분명하다.

### Cited Findings
아래 표의 각 칸 근거는 위 절들의 인용과 같다. 표 자체는 그 인용을 기준별로 다시 배열한 것이다.

| 출처 | (1) 결정적 | (2) 스냅숏 고정 | (3) 오프라인 | (4) SE·설계 범위 (탐침 16개) | (5) 이용 조건 | (6) 영어 원어 명시 | 표지 |
|---|---|---|---|---|---|---|---|
| ktword.co.kr | 예 (사람이 쓴 해설) | `no` 정수 + 받은 날짜 + 본문 해시. 사이트는 살아 있음 (2026-09 편집) | 웹 조회뿐. API · 덤프 없음 · robots 미확인 | 6~7/16, 대부분 개요 항목 안의 줄 | 출처 표시 시 상업 이용 포함 자유. 크롤링 · DB 복제는 명시 없음 | 항목마다 다름. 옛 항목은 표제에 영어 + 한국어 n개, SE 항목은 본문 괄호 | 🟡 |
| TTA SE 용어 단체표준 | — | — | — | 존재 미확인 | — | — | 🟡 부재 |
| KS X ISO/IEC/IEEE 24765 | — | — | — | 존재 미확인 | — | — | 🟡 부재 |
| KS X 0001 (정보처리 용어) | 예 | 표준 번호 + 연도 | 유료 문서로 추정 💭 | 미확인 | 저작권 (KS 일반) 💭 | 미확인 | 🟡 |
| ISO/IEC/IEEE 24765:2017 (원본, 한국어 없음) | 예 | 판 (2017, 3판 CD 진행) | 유료 | 높을 것 💭 (SE 전용 어휘) | ISO/IEEE 저작권 | 영어만 → 한국어 짝 없음 | 🟡 |
| NCS 응용SW엔지니어링 학습모듈 | 예 (PDF 산문) | 판 코드 (`_16v4` 꼴) | 내려받기로 추정 💭 | 미측정 | 미확인 (공공누리 유형 모름) | 미확인 | 🟡 |
| 정보처리기사 출제기준 | 예 | 적용 기간 (2026 / 2027~2029) | PDF 내려받기 (위키가 경로 인용) | 주제명 수준 ("디자인패턴") | 미확인 | 위키 전사본에는 없음 | 🟡 |
| KIISE · KIPS 용어집 | — | — | — | 존재 미확인 | — | — | 🟡 부재 |

### Inferences
- 💭70 ktword 를 넣는다면 꼴은 TTA 와 같은 "손 조회 기록" 행이 맞다. 행 필드는 `source=ktword`, `entry=no`, `url`, `fetched_at`, `sha256(본문)`, 그리고 매칭된 괄호 병기 문자열이다. 전량 수집은 운영자 문의 결과에 달렸다.
- 💭65 ktword 가 TTA 정보통신용어사전보다 나은 점은 이용 조건이 명시적이고 관대하다는 것이다. 공학 개념 어휘 범위는 둘 다 얇을 것으로 본다. TTA 쪽 범위는 이번에 재지 못했다.
- 💭60 이번 범위의 "공식·국가" 갈래는 공학 개념 어휘 공백을 메우지 못한다. 앞선 보고서 결론대로 그 공백은 Wikidata · 위키백과(넘겨주기) 덤프나 개념 중심 번역서 같은 다른 갈래로 메울 수밖에 없다. 공식 갈래에서 남은 유일한 미확인 대어는 KS X 0001 의 소프트웨어 부다.

### Gaps
- 모든 판정이 검색 요약에 기대고 있다. ktword 범위 표는 `www.ktword.co.kr` 를 허용 목록에 넣고 16개 탐침을 다시 돌리면 🔵 로 올릴 수 있다. 그때는 본문 영어 병기도 함께 센다.
- 비공식 한국어 IT 위키(itwiki.kr — 정보처리기사·기술사 주제를 다루고 "소프트웨어 모듈화" 항목에 결합도·응집도가 있다 🟡 [itwiki 소프트웨어 모듈화](https://itwiki.kr/w/소프트웨어_모듈화))는 이번 범위(공식·국가·ktword) 밖이라 평가하지 않았다. 이용 조건도 확인하지 않았다.
