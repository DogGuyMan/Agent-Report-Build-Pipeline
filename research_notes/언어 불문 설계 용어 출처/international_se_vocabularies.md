# 국제 영어 소프트웨어 공학 표준 어휘와 닫힌 용어 목록 (ko-dev-terms 의 영어 쪽 범위 후보)

> 조사 시점 2026-10-28. 표지: 🔵 이번 세션 실측(저장소를 커밋으로 받아 직접 셈) · 🟡 검색 결과 스니펫(snippet)만 · 💭 추론(뒤 정수는 확신도).
>
> **네트워크 제약 (🔵 이번 세션 `curl` 실측).** `pascal.computer.org` · `www.computer.org` · `www.swebok.org` · `ieeecs-media.computer.org` · `www.iso.org` · `obp.iso.org` · `standards.iso.org` · `refactoring.com` · `martinfowler.com` · `www.enterpriseintegrationpatterns.com` · `microservices.io` · `en.wikipedia.org` · `www.wikidata.org` · `domainlanguage.com` · `sebokwiki.org` 는 모두 연결 실패(HTTP 코드 000, WebFetch 는 `getaddrinfo ENOTFOUND`). GitHub 검색 API 는 "sessions are bound to their configured repositories" 로 403. **익명 `git clone` 과 Microsoft Learn MCP 는 동작했다.** 그래서 SEVOCAB · SWEBOK · ISO · Fowler · EIP · microservices.io · Wikipedia · Wikidata 에 관한 사실은 전부 🟡 이고, GitHub 저장소 3곳(Azure Architecture Center · iSAQB 용어집 · java-design-patterns)과 MS Learn 한국어 페이지 1쪽만 🔵 다.
>
> 탐침 용어 16개: side effect · postcondition · invariant · coupling · cohesion · single responsibility principle · dependency inversion · design pattern · layered architecture · circular dependency · call graph · idempotent · technical debt · code smell · refactoring · bounded context.

## ISO/IEC/IEEE 24765 (Systems and software engineering — Vocabulary) 와 SEVOCAB

### Takeaway
24765 는 영어 소프트웨어 공학 어휘의 유일한 국제 표준(de jure)이고, 같은 내용을 IEEE Computer Society 가 SEVOCAB 으로 무료 공개한다. 그러나 **현행판은 2017 년 2판(유료 PDF), 3판은 위원회 초안 단계이며, 항목 수·내보내기(export)·대량 추출 허용 여부는 확인하지 못했고, 한국어는 없다.** "출처를 밝히면 정의를 복사해도 된다"는 허락 문구는 2차 출처로만 확인됐다.

### Cited Findings
- 🟡 현행판은 **ISO/IEC/IEEE 24765:2017, 2판(Second edition 2017-09)** 이다 — [VDE 미리보기 PDF](https://www.vde-verlag.de/iec-normen/preview-pdf/info_isoiecieee24765{ed2.0}en.pdf); 2017 년판이 2010 년 1판을 취소·대체했다 — [iTeh 카탈로그](https://standards.iteh.ai/catalog/standards/iso/8a918aae-6e85-410f-b166-4b076301f461/iso-iec-ieee-24765-2017).
- 🟡 2017 년판은 2022 년에 검토·확인(reviewed and confirmed)되어 현행으로 남아 있다는 스니펫 — [ISO 71952](https://www.iso.org/standard/71952.html). 2010 년판은 2017-10-31 에 대체되었다 — [shop.standards.ie](https://shop.standards.ie/en-ie/standards/bs-iso-iec-ieee-24765-2010-268772_saig_bsi_bsi_620519).
- 🟡 **3판(Edition 3) 프로젝트 ISO 92875** 가 진행 중이며 2017 년판을 대체할 예정이다. 그러나 단계 표기가 엇갈린다 — 한 기록은 2025-09-19 에 "DIS 가 FDIS 로 등록 승인", 다른 기록은 2026 년 초 "CD 공개 검토" — [ISO 92875](https://www.iso.org/standard/92875.html); [ISS 프로젝트 기록](https://iss.rs/en/project/show/iso:proj:92875); [DIN 프로젝트](https://www.din.de/en/wdc-proj:din21:395840411).
- 🟡 AS/NZS ISO/IEC/IEEE 24765:2024 는 2017 년판을 그대로 채택(identical adoption)한 것이다 — [Standards Australia](https://store.standards.org.au/product/as-nzs-iso-iec-ieee-24765-2024).
- 🟡 분량은 판매처마다 532~541 쪽으로 다르게 표기된다 — [technickenormy.cz](https://www.technickenormy.cz/bs-iso-iec-ieee-24765-2017-systems-and-software-engineering-vocabulary/); [globalspec](https://standards.globalspec.com/std/1311749/iso-iec-ieee-24765). **항목(용어) 수는 어느 스니펫에도 없었다.**
- 🟡 24765 의 1차 원본(base document)은 **IEEE Std 610.12-1990** 이고, 정의의 약 3분의 2 가 1990 년 이후 새로 들어온 것이다. 나머지 출처는 ISO/IEC JTC 1/SC 7·IEEE CS 표준과 PMI Glossary 다 — [SEVOCAB 도움말 스니펫](https://pascal.computer.org/sev_display/help.jsp); [globalspec](https://standards.globalspec.com/std/10181116/ieee-24765). PMI Glossary 의 판이 "Fourth Edition" 과 "Fifth Edition" 으로 출처마다 다르다 — [globalspec](https://standards.globalspec.com/std/1311749/iso-iec-ieee-24765) 대 [technickenormy.cz](https://www.technickenormy.cz/bs-iso-iec-ieee-24765-2017-systems-and-software-engineering-vocabulary/).
- 🟡 SEVOCAB 은 IEEE Computer Society 와 ISO/IEC JTC 1/SC 7 의 공동 프로젝트로 `www.computer.org/sevocab` 에서 공개 접근할 수 있다. 24765 는 이 데이터베이스의 주기적 "스냅숏(snapshot)" 으로 발행된다 — [SEVOCAB](https://www.computer.org/sevocab); [globalspec](https://standards.globalspec.com/std/1311749/iso-iec-ieee-24765).
- 🟡 SEVOCAB 은 한 용어의 정의를 찾거나 **한 출처 표준의 정의 전부를 뽑아 보는** 검색을 제공하고, 용어마다 정의를 선호 순서(또는 일반→특수 순)로 번호 매겨 나열한다 — [Using SEVOCAB](https://pascal.computer.org/sev_display/help.jsp). 파일 내보내기(CSV·XML 등)나 API 에 관한 언급은 찾지 못했다.
- 🟡 **허락 문구:** "데이터베이스에 딸린 저작권 고지는 정의의 출처를 밝히는 한 정의를 복사하도록 허용한다" — 판매처 요약에만 보이는 2차 인용이다 — [iTeh](https://iteh.es/catalog/standards/iso/8a918aae-6e85-410f-b166-4b076301f461/iso-iec-ieee-24765-2017); [globalspec](https://standards.globalspec.com/std/10181116/ieee-24765). 공개 사용 허락의 취지는 "IEEE · ISO/IEC JTC1 · PMI 표준의 사용을 장려하려는 것" 이다 — [Using SEVOCAB](https://pascal.computer.org/sev_display/help.jsp). PMI Glossary 정의는 별도 저작권 협정에 따라 수정 없이 실렸다 — 같은 출처.
- 🟡 인쇄 표준 자체는 저작권 보호 문서이고, 복제에는 ISO·IEC·IEEE 의 서면 허락이 필요하다(`copyright@iso.org`, `stds.ipr@ieee.org`) — [VDE 미리보기 PDF](https://www.vde-verlag.de/iec-normen/preview-pdf/info_isoiecieee24765{ed2.0}en.pdf).
- 🟡 **언어:** IEC 웹스토어는 24765:2017 의 사용 언어를 **영어만** 으로 표기한다 — [IEC webstore 61433](https://webstore.iec.ch/publication/61433). **한국 국가표준(KS X ISO/IEC/IEEE 24765) 채택본은 검색으로 찾지 못했다** — 같은 검색 결과.
- 🟡 **탐침 용어 확인(2개만):** `cohesion` = "The manner and degree to which the tasks performed by a single software module are related to one another." [ISO/IEC/IEEE 24765] — [Squoring 매뉴얼](https://support.squoring.com/documentation/16.3/reference_manual/ch07s39.html); [SEBoK Cohesion (glossary)](https://sebokwiki.org/wiki/Cohesion_(glossary)). `coupling` = "The manner and degree of interdependence between software modules." [ISO/IEC/IEEE 24765] — [Squoring 매뉴얼](https://support.squoring.com/documentation/16.3/reference_manual/ch07s67.html); Wikipedia 의 coupling 문서도 24765:2010 을 출처로 단다 — [Wikipedia](https://en.wikipedia.org/wiki/Coupling_(computer_programming)).
- 🟡 `technical debt` · `postcondition` · `side effect` · `design pattern` · `refactoring` 의 24765 항목 여부를 검색했으나 스니펫에 나오지 않았다 — [globalspec](https://standards.globalspec.com/std/1311749/iso-iec-ieee-24765)(검색 결과 페이지는 서지 정보만 반환).

### Inferences
- 💭 75 — 24765/SEVOCAB 은 "국제 표준 어휘" 라는 사용자 기준을 문자 그대로 만족하는 **유일한** 후보다. 다만 기계 판독 목록을 합법적으로 얻는 경로가 확인되지 않았으므로, 지금 상태로는 TTA 와 같은 **"손 조회 기록" 꼴(조회 날짜 + 24765 판 + 출처 표준 표기)** 로 쓰는 것이 안전하다.
- 💭 65 — "출처 표기 시 복사 허용" 은 낱낱의 정의 인용을 상정한 문구로 읽힌다. SEVOCAB 전체를 긁어(scraping) 로컬에 저장하고 파생 행을 공개 저장소에 싣는 것까지 허용되는지는 문구만으로 알 수 없다. 용어 **이름만**(정의 없이) 저장하면 위험이 낮아진다(아래 "닫힌 목록" 절의 Circular 33 참고) — 법적 판단은 사용자 몫이다.
- 💭 70 — 고정(pinning)은 "ISO/IEC/IEEE 24765:2017 + SEVOCAB 조회 날짜" 로만 가능하다. SEVOCAB 은 살아 있는 데이터베이스이고 3판이 FDIS/CD 단계라, 2026~2027 년 사이 판이 바뀔 가능성이 높다. 판이 바뀌면 다시 고정하는 절차가 필요하다.
- 💭 60 — 24765 의 뿌리가 610.12-1990(일반 소프트웨어 공학 용어)이고 SC 7 표준(프로세스·수명 주기·품질) 정의가 대부분이라, `technical debt` · `code smell` · `bounded context` 같은 실무 설계 어휘는 빠져 있을 가능성이 있다. 확인하지 못했다.

### Gaps
- SEVOCAB 의 항목 수, 내보내기 기능, 이용 약관 원문 — `pascal.computer.org` · `www.computer.org` 차단으로 열지 못함. 네트워크 허용 목록에 두 호스트를 더해야 확인 가능.
- 탐침 16개 중 14개(coupling·cohesion 제외)의 SEVOCAB 수록 여부 — 위와 같은 이유.
- 3판의 실제 단계와 발행 예정 시기 — 출처 간 불일치.
- NASA SWEHB 에 첨부된 `c071952_ISO_IEC_IEEE_24765_2017.pdf` 가 무엇인지(ISO 무료 공개 표준인지, 무단 사본인지) — 열지 못했고, 검색으로도 24765 가 ISO 무료 공개 표준(Publicly Available Standards) 목록에 있다는 근거를 찾지 못했다 — [SWEHB 첨부](https://swehb.nasa.gov/download/attachments/16450104/c071952_ISO_IEC_IEEE_24765_2017.pdf?api=v2).

## SWEBOK Guide v4.0 (2024)

### Takeaway
SWEBOK v4.0 은 **무료로 받을 수 있지만(이메일 양식) "All rights reserved" 저작물이고, 무료 사본은 개인·학술용으로만 허용된다(2차 출처).** 18개 지식 영역(knowledge area)에 Software Architecture 가 새로 들어왔다. 용어집(glossary)이나 용어 색인이 있는지는 확인하지 못했고, 공식 한국어판도 찾지 못했다.

### Cited Findings
- 🟡 인용 서지: H. Washizaki, eds., *Guide to the Software Engineering Body of Knowledge (SWEBOK Guide), Version 4.0*, IEEE Computer Society, 2024 — [SWEBOK 참조 목록](https://www.computer.org/education/bodies-of-knowledge/software-engineering/swebok-reference-list).
- 🟡 **2025-09-25 에 소폭 수정되어 지금 판은 "SWEBOK v4.0a"** 이고, 같은 양식으로 받으면 최신판이 온다 — [SWEBOK 페이지](https://www.computer.org/education/bodies-of-knowledge/software-engineering).
- 🟡 v4 는 이메일 양식을 제출하면 내려받기 링크를 메일로 보내 준다 — [SWEBOK v4 Download](https://computer.org/education/bodies-of-knowledge/software-engineering/v4); [v4 감사 페이지](https://www.computer.org/education/bodies-of-knowledge/software-engineering/v4-ty). IEEE CS 는 "적어도 한 형식으로는 계속 무료로 접근 가능하게 둔다" 고 밝힌다 — [computer.org/web/swebok](https://computer.org/web/swebok).
- 🟡 **v4 앞부분(front matter) 저작권 문구(제3자 미러로만 확인):** "Copyright © 2014–2024 IEEE. All rights reserved." 상업·광고·판촉 목적의 재인쇄나 재판매·재배포용 새 집합 저작물 제작은 IEEE 허락이 필요하고, 무료 디지털 사본은 개인·학술용(personal and academic use)으로 swebok.org 에서 받을 수 있다 — [studylib.es 미러](https://studylib.es/doc/9522264/guide-to-the-software-engineering-swebok-v4). v3 앞부분에도 같은 취지의 문구가 있다 — [SWEBOK v3 사본](https://reda-isw-tdg.netlify.app/espa%C3%B1ol/resources/others/pdf/SWEBOKv3.pdf).
- 🟡 v4 는 18개 지식 영역 + 새 표준 부록(Appendix on Standards)으로 구성되며, Software Architecture · Software Engineering Operations · Software Security 가 새로 추가됐다 — [SWEBOK 페이지](https://www.computer.org/education/bodies-of-knowledge/software-engineering); [V4.0 Topics](https://computer.org/education/bodies-of-knowledge/software-engineering/topics).
- 🟡 SWEBOK v3 는 **ISO/IEC TR 19759:2015** 로 ISO/IEC 기술 보고서로 채택됐다(IEEE CS 가 준비, 특별 협정). 무료 내려받기 가능 여부는 출처마다 엇갈린다 — 한 목록은 "ITTF 웹사이트에서 받을 수 있다", 다른 목록은 유료 가격을 표기한다 — [globalspec](https://reference.globalspec.com/ref/3887014/iso-iec-tr-19759-2015); [DIN Media](https://dinmedia.de/en/technical-rule/iso-iec-tr-19759/243238310); [ISO 67604](https://www.iso.org/standard/67604.html).
- 🟡 **선례:** Kehrer 외(2025, *Computing in Science & Engineering*)는 연구 소프트웨어 엔지니어(RSE)와 소프트웨어 공학 연구자(SER)의 용어 대응을 만들 때 **SWEBOK v3 의 15개 지식 영역 중 앞 10개를 초기 용어 목록의 기준(anchor)** 으로 삼았고, 용어마다 Markdown + YAML 전단(frontmatter, `swebok_section` 등 배열 필드)으로 Jekyll 사이트에 저장했다 — [arXiv 2507.02665](https://arxiv.org/html/2507.02665v1); [ORNL](https://impact.ornl.gov/en/publications/do-research-software-engineers-and-software-engineering-researche/).
- 🟡 **한국어:** 공식 한국어 번역판은 검색에서 찾지 못했다. IT 위키(itwiki.kr)가 지식 영역 이름을 한국어로 정리한 개요만 있다 — [itwiki.kr SWEBOK](https://www.itwiki.kr/w/SWEBOK).
- 🟡 SWEBOK 이 24765 의 정의를 채택한다는 직접 근거는 찾지 못했다 — 검색 결과는 둘을 별개 참고 자료로만 나열한다 — [Medium 글](https://medium.com/@helymarleena/software-engineering-important-terminology-315a44414fd5).

### Inferences
- 💭 75 — "개인·학술용 무료" 조건이면, SWEBOK 에서 뽑은 **용어 이름 목록**을 공개 저장소에 싣는 것은 회색 지대다. 본문(정의·설명)을 싣는 것은 허락 범위를 넘을 가능성이 높다.
- 💭 60 — SWEBOK 은 정의 사전이 아니라 지식 영역·주제(topic) 체계다. 영어 쪽 범위로 쓴다면 "용어 목록" 이 아니라 **주제 계층(KA → topic 제목)** 을 범위 분류(어느 영역에 속하는가)의 축으로 쓰는 편이 자연스럽다. Kehrer 외의 방식이 그 선례다.
- 💭 55 — 판 고정은 "v4.0a(2025-09-25 수정)" + 받은 PDF 의 SHA-256 으로 할 수 있다. 다만 PDF 를 저장소에 넣는 것은 재배포라 피해야 하고, 해시만 기록해야 한다.

### Gaps
- v4 에 용어집·색인이 있는지, 몇 항목인지 — PDF 와 computer.org 를 열지 못함.
- v4 저작권 문구 원문 — 미러로만 확인. 공식 PDF 앞부분 확인 필요.
- 탐침 16개의 SWEBOK 수록 여부 — 본문 미확인.

## ISO/IEC 2382 (Information technology — Vocabulary) 와 ISO Online Browsing Platform(OBP)

### Takeaway
ISO/IEC 2382:2015 는 **영어·프랑스어 2개 언어** 정보기술 어휘이고 OBP 에서 **무료로 열람(browse)할 수 있지만 내려받기(download)는 안 된다.** 소프트웨어 설계·아키텍처 어휘가 아니라 정보기술 일반 어휘이며, 한국어는 들어 있지 않다.

### Cited Findings
- 🟡 2382:2015 는 2개 언어로 선택된 개념의 용어와 정의를 제시하고, 정의는 언어 특유의 성질을 피해 번역하기 쉽게 썼다 — [IEC webstore 22380](https://webstore.iec.ch/publication/22380); 사용 가능 언어는 English, French — [shop.standards.ie](https://shop.standards.ie/en-ie/standards/iso-iec-2382-2015-604968_saig_iso_iso_1386043).
- 🟡 2022-10 일자 정정판(Corrected version 2022-10)이 있다 — [iTeh](https://standards.iteh.ai/catalog/standards/iso/238f7a76-6c27-4e1d-96dc-073acbb3b38e/iso-iec-2382-2015).
- 🟡 무료 경로가 두 가지로 언급된다 — "ITTF 웹사이트에서 전자판을 받을 수 있다" ([IEC webstore](https://webstore.iec.ch/publication/22380)), "OBP 에서 무료로 온라인 열람" ([EVS](https://www.evs.ee/en/iso-iec-2382-2015); [ISO 63598](https://www.iso.org/standard/63598.html)).
- 🟡 **OBP 의 어휘 표준 용어와 정의는 일반인이 무료로 열람할 수 있으나 내려받을 수는 없다** — [ANSI ISOT Guidance Note 010](https://share.ansi.org/ISOT/ISOT%20Guidance%20Notes/ISOT%20Guidance%20Note%20010%20-%20ISO's%20Online%20Browsing%20Platform.pdf). OBP 이용 약관은 접근 유형에 따라 권한이 다르다고 적는다 — [ISO OBP Terms of Use](https://www.iso.org/home/store/iso-obp-terms.html).
- 🟡 ISO 용어로 인정되는 것은 공식 언어(영어·프랑스어)로 쓰인 용어와 정의뿐이다 — [ANSI 어휘 표준 모범 사례](https://share.ansi.org/ISOT/Other%20ISOT%20Resources/Resources%20for%20Drafting%20Standards/Vocabulary%20Standards%20Best%20practices.pdf).
- 🟡 OBP 데이터에 접근하는 비공식 Ruby gem(`obp-access`)이 있다 — [rubydoc obp-access](https://www.rubydoc.info/gems/obp-access/0.1.7).
- 🟡 과거 1993 년판 Part 1 은 일반 용어·정보 표현·하드웨어·소프트웨어·프로그래밍 등 144 개 용어를 담았다 — [shop.standards.ie](https://shop.standards.ie/en-ie/standards/iso-iec-2382-2015-604968_saig_iso_iso_1386043).
- 🟡 (선행 보고서 재인용) 한국의 정보기술 용어 표준은 "KS X ISO/IEC 2382" 가 아니라 **KS X 0001 시리즈**로 보이며 유료로 추정된다 — [KS X 0001-1](https://ndls.org.cn/standard/detail/d6c6c7e9c0fb2d2ebd28edcf06ba080c).

### Inferences
- 💭 75 — OBP 의 "열람 무료·내려받기 불가" 조건은 로컬 결정적 조회(offline deterministic lookup)와 정면으로 충돌한다. 비공식 gem 으로 긁는 것은 약관 위반 위험이 있어 권하지 않는다.
- 💭 65 — 2382 는 정보기술 일반(하드웨어·데이터·통신) 어휘라서 설계·아키텍처·패턴·SOLID 에 무게를 두라는 기준과 범위가 맞지 않는다. 24765 와 겹치는 일반 용어를 확인하는 보조 출처 이상이 되기 어렵다.

### Gaps
- 2382:2015 의 항목 수와 탐침 16개 수록 여부 — `obp.iso.org` 차단.
- ITTF 무료 공개 표준 목록에 2382 가 지금도 있는지 — `standards.iso.org` 차단.

## IEEE 610.12-1990 (Standard Glossary of Software Engineering Terminology)

### Takeaway
610.12-1990 은 **대체(superseded)된 표준**이고 그 내용은 24765 로 흡수됐다. 따로 고를 이유가 없다.

### Cited Findings
- 🟡 IEEE 는 610.12-1990 을 "Superseded Standard, superseded by 24765-2010" 으로 표기한다 — [IEEE SA 610.12](https://standards.ieee.org/ieee/610.12/855). 24765:2010 서문은 자신이 IEEE Std 610.12-1990 을 대체한다고 적는다 — [iTeh 24765:2010](https://standards.iteh.ai/catalog/standards/iso/38870dfe-5236-479f-b75f-98987d9f042b/iso-iec-ieee-24765-2010).
- 🟡 **출처 충돌:** DIN 목록은 610.12 를 "withdrawn, 대체 없음" 으로 적는다 — [DIN Media](https://dinmedia.de/en/standard/iso-iec-ieee-24765/141530584). IEEE 기록과 24765:2010 서문이 더 권위 있다.
- 🟡 610.12-1990 은 지금도 판매처에서 유료로 팔린다 — [shop.standards.ie](https://shop.standards.ie/en-ie/standards/ieee-610-12-1990-571124_saig_ieee_ieee_1307033).

### Inferences
- 💭 85 — 24765 가 610.12 를 기반 문서로 삼았으므로(앞 절), 610.12 를 따로 받는 것은 이득이 없다. 옛 판이라 `technical debt` 같은 이후 용어도 없을 것이다.

### Gaps
- 610.12 의 `call graph` 정의 문구 — 검색으로 확인하지 못했다.

## 닫힌 목록(closed catalog) — GoF · SOLID · 패키지 원칙 · GRASP · Fowler 리팩터링 · PoEAA · EIP · DDD · Azure · microservices.io · Wikipedia

### Takeaway
닫힌 목록은 크기가 작고 이름이 고정되어 있어 **씨앗 목록(seed list)으로 쓰기 쉽다.** 그중 **기계 판독 + 커밋 고정 + 공개 라이선스**를 실측으로 확인한 것은 **Azure Architecture Center 클라우드 디자인 패턴 44개(CC BY 4.0, 커밋 `6d1df20`)** 하나다. EIP 65개(이름 등 CC BY)와 Evans 의 DDD Reference(CC BY 4.0)는 라이선스가 열려 있으나 원문을 열지 못했다. GoF 23 · SOLID 5 · 패키지 원칙 6 · GRASP 9 는 이름만으로 된 작은 고정 목록이라 사람이 손으로 옮겨 적으면 된다. 미국 저작권청은 **이름·짧은 문구는 저작권 대상이 아니라고** 밝힌다(정의 본문은 별개).

### Cited Findings
- 🟡 **이름·짧은 문구:** 미국 저작권청 Circular 33 — "names, titles, and slogans" 같은 낱말과 짧은 문구는 저작성이 부족해 저작권 보호를 받지 못하며, 새롭거나 독특해도 마찬가지다. 37 C.F.R. §202.1(a) 도 같다 — [Circular 33](https://www.copyright.gov/circs/circ33.pdf). 단 상표법 보호는 따로 있을 수 있다 — 같은 출처.
- 🟡 **GoF 23개** = 생성(creational) 5 · 구조(structural) 7 · 행위(behavioral) 11. 저자 Gamma · Helm · Johnson · Vlissides, 1994 — [GeeksforGeeks](https://www.geeksforgeeks.org/?p=1063972); [journaldev](https://www.journaldev.com/31902/gangs-of-four-gof-design-patterns) (2차 출처, 일부 출처에 범주 제목 오류가 있다는 지적도 같은 검색 결과에 있음).
- 🟡 **GRASP 9개** — Information Expert · Creator · Controller · Low Coupling · High Cohesion · Polymorphism · Pure Fabrication · Indirection · Protected Variations, Larman 의 *Applying UML and Patterns*(1997) — [Tübingen 강의 자료](https://handin-ps.informatik.uni-tuebingen.de/teaching/ss18/se/5_grasp.pdf); [Wikipedia 사본](https://kaweah.freedombox.rocks/kiwix/wikipedia_en_all_maxi_2023-10/GRASP_(object-oriented_design)).
- 🟡 **패키지 원칙 6개** — 응집 쪽 REP(Reuse/Release Equivalence) · CCP(Common Closure) · CRP(Common Reuse), 결합 쪽 ADP(Acyclic Dependencies) · SDP(Stable Dependencies) · SAP(Stable Abstractions). Martin 의 *Agile Principles, Patterns, and Practices in C#* 28장 — [Sitecore Helix](https://helix.sitecore.com/appendix/package-principles.html); [Avenue Code](https://blog.avenuecode.com/principles-of-package-and-component-design).
- 🔵 SOLID 5개와 패키지 원칙 6개는 iSAQB 용어집에 **표제어로 모두** 있다: Single Responsibility Principle (SRP) · Open-Close-Principle (OCP) · Liskov Substitution Principle · Interface Segregation Principle (ISP) · Dependency Inversion Principle · S.O.L.I.D. principles · Reuse/Release Equivalence Principle · Common Closure Principle · Common Reuse Principle · Acyclic Dependencies Principle · Stable Dependencies Principle · Stable Abstractions Principle · Package Principles — [isaqb-org/glossary @bd3ce64](https://github.com/isaqb-org/glossary/tree/bd3ce64e1f4a250ccd1806719723ff80b7202cb8/docs/1-terms). 같은 용어집에 GoF 23개 중 11개(Singleton · Adapter · Bridge · Facade · Proxy · Command · Interpreter · Observer · Strategy · Template Method · Visitor)가 표제어로 있고 **GRASP 9개는 하나도 없다** — 같은 출처.
- 🟡 **Fowler 리팩터링 카탈로그(refactoring.com):** 온라인 카탈로그는 2판(2018)의 동반 자료이며 1판과 Ruby Edition 의 리팩터링까지 포함한다 — [refactoring.com/catalog](https://refactoring.com/catalog/). 1판의 리팩터링은 68개였고 2판에서 "big refactorings" 4개를 뺐으며 완전히 새로운 리팩터링이 15개다 — [Changes for the 2nd Edition](https://www.martinfowler.com/articles/refactoring-2nd-changes.html). 책 소개는 "약 70개" 라 한다 — [martinfowler.com/books/refactoring](https://www.martinfowler.com/books/refactoring.html). **정확한 총수와 사이트 라이선스는 확인하지 못했다.**
- 🟡 한국어판 『리팩터링 2판』(개앞맵시·남기혁 옮김, 한빛미디어, 2020)은 원서 웹 버전을 기준으로 번역했다(지원 저장소 README) — 🔵 [WegraLee/Refactoring @48bca38](https://github.com/WegraLee/Refactoring/blob/48bca38e3bb10766d7da2121ec5933fba1f7fc85/README.md). 이 저장소는 README 한 파일뿐이고 **영–한 기법 이름 대응표는 없다** 🔵. 한국어 이름과 IDE 리팩터링을 나란히 놓은 구글 스프레드시트가 있다는 스니펫 — [Google Sheets](https://docs.google.com/spreadsheets/d/1nFx-PjZ9Qs3QBZFzaMo6MSUSrWjSsO-iz5kpBtlVRPQ/edit); [justinadpark 블로그](https://justinadpark.tistory.com/221) (열지 못함).
- 🟡 **PoEAA 카탈로그(martinfowler.com/eaaCatalog):** 책 본문은 "forty or so patterns" 의 참조이고, 카탈로그는 Domain Logic · Data Source Architectural · Object-Relational Structural/Behavioral/Metadata Mapping · Web Presentation · Distribution · Offline Concurrency · Session State · Base 로 묶인다 — [eaaCatalog](https://martinfowler.com/eaaCatalog/); [PoEAA 책 페이지](https://www.martinfowler.com/books/eaa.html). 라이선스는 확인하지 못했다.
- 🟡 **EIP(enterpriseintegrationpatterns.com):** 카탈로그는 **65개 통합 패턴**이고, 패턴의 **이름 · 아이콘 · 문제/해법 문장 · 스케치**는 CC BY 로 공개되어 출처 표기(사이트 링크 또는 책 인용) 시 공유·수정할 수 있다. 다른 부분은 저작권 보호 — [EIP 카탈로그](https://www.enterpriseintegrationpatterns.com/eaipatterns.html); [2022 Wayback 사본](https://webcf.waybackmachine.org/web/20220605144612/https://www.enterpriseintegrationpatterns.com/eaipatterns.html).
- 🟡 **DDD Reference(Evans, 2015):** PDF 저작권 면에 "Creative Commons Attribution 4.0 International License" 로 표기되어 있고, 원서 이후 중요해진 패턴 3개를 더했다. 2004 년 책에서 발췌한 옛 요약 페이지의 배지는 CC BY 3.0 이다 — [domainlanguage.com DDD Reference](https://domainlanguage.com/ddd/reference/); [DDD_Reference_2015-03.pdf](https://domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf). 패턴 총수는 확인하지 못했다.
- 🔵 **Azure Architecture Center 클라우드 디자인 패턴:** `MicrosoftDocs/architecture-center` 는 익명 `git clone` 가능한 공개 저장소다. 커밋 `6d1df20e7433ce2b765b4944c10a3ed0f9625caf`(2026-10-28)의 `docs/patterns/index.md`(`ms.date: 05/03/2026`) 표에 **패턴 44개**가 `| [이름](./파일.md) | 요약 | Well-Architected 기둥 |` 꼴로 있다. 문서 라이선스는 `LICENSE` = **CC BY 4.0**, 코드는 `LICENSE-CODE` = MIT — [architecture-center @6d1df20](https://github.com/MicrosoftDocs/architecture-center/blob/6d1df20e7433ce2b765b4944c10a3ed0f9625caf/docs/patterns/index.md).
- 🔵 **Azure 패턴의 한국어판:** MS Learn MCP 로 `learn.microsoft.com/ko-kr/azure/architecture/patterns/` 를 받았다. 44개 이름의 한국어 표기가 있고, 페이지 자체가 "기술에 구애받지 않으므로 … Azure, 다른 클라우드 플랫폼, 온-프레미스 … 에 적용할 수 있다" 고 적는다. 표기 예: Idempotent Consumer → `멱등 소비자`, Anti-Corruption Layer → `반부패 계층`, Bulkhead → `격벽`, Circuit Breaker → `회로 차단기`, Ambassador → `대사`, Choreography → `안무`, Leader Election → `리더 선거`, Strangler Fig → `스트랭글러 무화과`, 그리고 **Rate Limiting 과 Throttling 이 둘 다 `속도 제한`** 이다 — [MS Learn ko-kr Cloud Design Patterns](https://learn.microsoft.com/ko-kr/azure/architecture/patterns/).
- 🟡 **microservices.io:** Chris Richardson 의 "pattern language" 로 범주별로 정리된다. 사이트 패턴 총수는 찾지 못했고, 책 *Microservices Patterns* 1판은 "44 reusable patterns" 를 다룬다 — [microservices.io/patterns](https://microservices.io/patterns/); [Skillsoft 책 소개](https://skillsoft.com/book/microservices-patterns-8a74ccea-f809-4f79-a901-4a1c1f69a9c5). 사이트 원본 저장소와 라이선스는 찾지 못했다.
- 🟡 **Wikipedia:** "Glossary of computer science" 는 CC BY-SA(DBpedia 기록은 3.0 Unported) — [Glossary of computer science](https://en.wikipedia.org/wiki/Glossary_of_computer_science); [DBpedia](https://dbpedia.org/page/Glossary_of_computer_science). "Category:Software design patterns" 에 148 쪽이 있다는 스니펫(날짜 미상) — [Category:Software design patterns](https://en.Wikipedia.com/wiki/Category:Software_design_patterns).

### Inferences
- 💭 70 — Circular 33 이 맞다면(미국법 기준), GoF·GRASP·SOLID·패키지 원칙·EIP·PoEAA·리팩터링 **이름 목록**은 라이선스와 무관하게 로컬 저장과 공개 저장소 게시가 가능하다. **정의·요약 본문**은 출처마다 라이선스를 따라야 한다(EIP·DDD Reference·Azure 는 CC BY, PoEAA·refactoring.com 은 미확인). 한국법 판단은 하지 않았다.
- 💭 75 — 언어 불문 설계 범위에 가장 가까운 닫힌 목록은 GoF 23 · SOLID 5 · 패키지 원칙 6 · GRASP 9 · DDD 패턴이다. Azure 44 · EIP 65 · microservices.io 는 분산 시스템·통합 쪽으로 기울고, PoEAA 는 엔터프라이즈 애플리케이션(객체–관계 매핑 등)에 기운다. 사용자가 말한 "가중치 = 범위와 우선순위" 로 옮기면 앞의 묶음이 1순위, 뒤의 묶음이 2순위라는 분류가 가능하다 — 이것은 제안일 뿐이다.
- 💭 70 — MS Learn ko-kr 표기(`대사` · `안무` · `리더 선거` · 두 패턴이 같은 `속도 제한`)는 기계 번역의 흔적으로 보인다. 근거 행으로 쓰려면 "MS Learn ko-kr (현지화 방식 미확인)" 표지를 붙여야 하고, 정책 근거로 세면 안 된다. 다만 `멱등 소비자` · `회로 차단기` 처럼 쓸 만한 표기도 함께 있어 한국어 후보 행의 출처는 될 수 있다.
- 💭 60 — 리팩터링 카탈로그는 탐침의 `refactoring` · `code smell` 을 채우는 자연스러운 출처지만, refactoring.com 원문을 열지 못해 이름 목록조차 고정하지 못했다. 손으로 옮겨 적을 경우 조회 날짜로만 고정할 수 있다.

### Gaps
- refactoring.com 카탈로그의 정확한 개수와 이용 조건, PoEAA 카탈로그의 정확한 개수(약 40 개 이상이라는 표현만 확인)와 이용 조건 — 호스트 차단.
- microservices.io 패턴 수 · 라이선스 · 원본 저장소.
- DDD Reference 의 패턴 수 — PDF 를 열지 못함.
- Wikipedia "Glossary of computer science" 의 항목 수와 탐침 수록 여부 — 차단.

## 공개 기계 판독 집계(aggregation) — GitHub 저장소 · Wikidata · SEBoK

### Takeaway
실측으로 확인한 가장 쓸 만한 집계는 **iSAQB "Glossary of Software Architecture"(CC BY 4.0, 표제어 274개, AsciiDoc + JSON, 판 `2024.1`, 커밋 고정)** 다. 탐침 16개 중 8개를 표제어로 갖고(Layer 까지 치면 9개) SOLID·패키지 원칙·DDD 핵심 용어를 모두 담는다. 다만 영어·독일어뿐이다. `iluwatar/java-design-patterns`(MIT, 패턴 192개, 범주 필드)는 이름 목록으로는 크지만 자바 저장소이고 탐침 적중이 2개뿐이다. Wikidata 는 CC0 덤프로 고정할 수 있지만 이번 세션에서 열지 못했다.

### Cited Findings
- 🔵 **iSAQB 용어집:** `isaqb-org/glossary` 커밋 `bd3ce64e1f4a250ccd1806719723ff80b7202cb8`(2026-10-09), `document.version` = `2024.1`. `docs/1-terms/<첫 글자>/term-*.adoc` 파일 275개, 영어 표제어(`==== 제목`) **274개**. 파일마다 `// tag::EN[]` 과 `// tag::DE[]` 구간에 영어·독일어 정의가 함께 있다. `translations/isaqb-terms-translated.json` 은 `{"en": "Accessibility", "de": ["Barrierefreiheit", "Zugänglichkeit"]}` 꼴 153 항목이다 — [isaqb-org/glossary @bd3ce64](https://github.com/isaqb-org/glossary/tree/bd3ce64e1f4a250ccd1806719723ff80b7202cb8).
- 🔵 라이선스는 `docs/0-preamble/04-license.adoc` 에 **CC BY 4.0**("Share … Adapt … even commercially")이다. README 는 "Natural Languages: English and German … (currently) don't support additional languages, but are _very open_ for suggestions" 라고 적는다 — [04-license.adoc](https://github.com/isaqb-org/glossary/blob/bd3ce64e1f4a250ccd1806719723ff80b7202cb8/docs/0-preamble/04-license.adoc); [README.adoc](https://github.com/isaqb-org/glossary/blob/bd3ce64e1f4a250ccd1806719723ff80b7202cb8/README.adoc).
- 🔵 iSAQB 의 `Coupling` 정의는 "the kind and degree of _interdependence_ between building blocks of software" 로 시작하고 Wikipedia 로 링크한다 — [term-coupling.adoc](https://github.com/isaqb-org/glossary/blob/bd3ce64e1f4a250ccd1806719723ff80b7202cb8/docs/1-terms/C/term-coupling.adoc).
- 🔵 iSAQB 의 DDD 관련 표제어: Domain-Driven Design (DDD) · Bounded Context · Aggregate · Entity · Value Object · Repository · Service (DDD) · Ubiquitous Language · Domain Model · ACL — 같은 저장소.
- 🔵 **java-design-patterns:** `iluwatar/java-design-patterns` 커밋 `4cabb204f240240bea319605a5ffa46ded728001`(2026-09-13), MIT. 최상위 패턴 디렉터리 192개의 `README.md` 모두에 YAML 전단 `shortTitle:` · `category:` 가 있다. 범주 분포: Behavioral 41 · Structural 34 · Architectural 28 · Concurrency 23 · Creational 14 · Data access 12 · Resilience 8 · Functional 8 · Integration 6 · 기타(Behavioral 과 Data access 는 공백·대소문자 표기 변이 1건씩을 합친 값). `localization/` 에 23개 언어가 있고 그중 `ko` 는 **17개 패턴**뿐이며, 한국어판도 `title:` 은 영어(`Adapter` 등)로 두고 본문만 한국어다(예: Strategy 의 "동의어: 정책(Policy) 패턴") — [java-design-patterns @4cabb20](https://github.com/iluwatar/java-design-patterns/tree/4cabb204f240240bea319605a5ffa46ded728001).
- 🟡 **SEBoK 용어집:** 시스템 공학 지식 체계(SEBoK) 위키의 용어집 범주에 436 쪽이 있다(날짜 미상). Stevens 가 저작권을 가진 부분은 CC BY-NC-SA 3.0, 편집물 전체는 CC BY-NC-ND 3.0, 제3자 자료는 제외 — [Glossary of Terms](https://sebokwiki.org/wiki/Glossary_of_Terms); [Bkcase Wiki:Copyright](https://sebokwiki.org/wiki/Bkcase_Wiki:Copyright). 용어집 항목이 24765 정의를 인용한다(예 Cohesion) — [SEBoK Cohesion](https://sebokwiki.org/wiki/Cohesion_(glossary)).
- 🟡 **Wikidata:** 구조화 데이터는 CC0 이고 매주 JSON 덤프로 나온다(선행 보고서 재인용) — [Wikidata:Data access](https://www.wikidata.org/wiki/Wikidata:Data_access). Wikidata 의 온톨로지는 형식화되어 있지 않고 클래스·속성의 사용에서 아래로부터 생겨난다는 논문 지적이 있어, "software design pattern" 클래스의 인스턴스 질의 결과는 편집자의 사용 관행에 좌우된다 — [UvA, Empirical ontology design patterns from Wikidata](https://dare.uva.nl/id/1a9c5a6c-8bea-4c4e-b82e-0ec822abdc71). 해당 항목(QID)과 인스턴스 수는 확인하지 못했다.
- 🔵 **탐침 16개 적중표**(표제어·패턴 이름 기준. Azure·jdp 는 이름 문자열 포함 여부, iSAQB 는 영어 표제어):

  | 탐침 | SEVOCAB 🟡 | iSAQB 274 🔵 | Azure 44 🔵 | jdp 192 🔵 | 닫힌 목록 🟡 |
  |---|---|---|---|---|---|
  | side effect | 미확인 | 없음(본문 언급 1) | 없음 | 없음 | — |
  | postcondition | 미확인 | 없음 | 없음 | 없음 | — |
  | invariant | 미확인 | **Invariant** | 없음 | 없음 | — |
  | coupling | **있음** | **Coupling** · Temporal Coupling | 없음 | 없음 | GRASP Low Coupling |
  | cohesion | **있음** | **Cohesion** | 없음 | 없음 | GRASP High Cohesion |
  | single responsibility principle | 미확인 | **SRP** | 없음 | 없음 | SOLID |
  | dependency inversion | 미확인 | **Dependency Inversion Principle** | 없음 | 없음 | SOLID |
  | design pattern | 미확인 | **Design Pattern** | 없음 | 없음 | GoF(상위 개념) |
  | layered architecture | 미확인 | 없음(**Layer** 만) | 없음 | **Layered Architecture** | — |
  | circular dependency | 미확인 | 없음 | 없음 | 없음 | (ADP 가 개념만 다룸) |
  | call graph | 미확인 | 없음 | 없음 | 없음 | — |
  | idempotent | 미확인 | 없음 | **Idempotent Consumer** | **Microservices Idempotent Consumer** | — |
  | technical debt | 미확인 | 없음 | 없음 | 없음 | — |
  | code smell | 미확인 | 없음 | 없음 | 없음 | (리팩터링 책의 장 제목, 미확인) |
  | refactoring | 미확인 | **Refactoring** | 없음 | 없음 | refactoring.com |
  | bounded context | 미확인 | **Bounded Context** | 없음 | 없음 | DDD Reference(미확인) |

  출처 — [iSAQB @bd3ce64](https://github.com/isaqb-org/glossary/tree/bd3ce64e1f4a250ccd1806719723ff80b7202cb8); [Azure index.md @6d1df20](https://github.com/MicrosoftDocs/architecture-center/blob/6d1df20e7433ce2b765b4944c10a3ed0f9625caf/docs/patterns/index.md); [jdp @4cabb20](https://github.com/iluwatar/java-design-patterns/tree/4cabb204f240240bea319605a5ffa46ded728001); SEVOCAB 2건 — [Squoring cohesion](https://support.squoring.com/documentation/16.3/reference_manual/ch07s39.html), [Squoring coupling](https://support.squoring.com/documentation/16.3/reference_manual/ch07s67.html).

### Inferences
- 💭 75 — iSAQB 용어집은 기준 (1)~(5)를 모두 만족한다: 기계 판독(AsciiDoc 표제어 + JSON) · 고정(`2024.1` + 커밋) · 오프라인(저장소 수 MB) · 설계·아키텍처 중심 · CC BY 4.0(출처 표기로 공개 게시 가능). 단 **"국제 표준 어휘" 가 아니라 국제 자격 인증 단체(iSAQB)의 공동체 용어집**이므로, 사용자의 "국제 표준 어휘" 정의에 넣을지는 사용자가 정해야 한다.
- 💭 70 — 어느 열린 목록에도 없는 탐침이 6개다: `side effect` · `postcondition` · `circular dependency` · `call graph` · `technical debt` · `code smell`. 이 6개는 SEVOCAB 에 있는지 확인되기 전까지 **사용자 제공 목록**으로만 범위에 들어온다. 선행 보고서에서 한국어 근거가 비었던 `postcondition` 이 영어 쪽 목록에서도 빈다는 점은, 공백이 번역 자원만의 문제가 아니라 "영어 쪽 범위 목록" 자체의 문제이기도 하다는 뜻이다.
- 💭 65 — java-design-patterns 는 자바 코드 저장소라 "프레임워크 의존 용어집은 권하지 않는다" 는 기준과 결이 다르다. 이름 자체는 대부분 언어 불문이지만 Bytecode · Game Loop · Bloc · Flux · Monad · Currying 같은 게임·함수형·UI 프레임워크 쪽 이름이 섞여 있어, 쓰려면 `category` 필드로 걸러야 한다.
- 💭 60 — Wikidata 는 CC0 · 주간 덤프라 고정·공개 조건이 가장 깔끔하고 한국어 label 도 있을 가능성이 높다. 그러나 "무엇이 설계 패턴 클래스의 인스턴스인가" 가 편집 관행에 달려 있어 닫힌 목록으로는 경계가 흐리다. 범위 결정용이 아니라 다국어 label 조회용 보조 출처로 맞다.
- 💭 70 — SEBoK 용어집은 24765 정의를 재인용하는 2차 집계이고 NC-SA/NC-ND 라이선스라, 공개 저장소에 파생 행을 싣는 데 제약이 크다. 24765 확인용 우회로로만 쓸 만하다.

### Gaps
- Wikidata "software design pattern" 클래스의 QID · 인스턴스 수 · 한국어 label 채움률 — `wikidata.org` · `dumps.wikimedia.org` 차단.
- Kehrer 외 RSE/SER 용어집의 GitHub 저장소 위치와 라이선스 — GitHub 검색 API 차단으로 찾지 못함.
- GoF · GRASP · 리팩터링 이름을 기계 판독 꼴로 모은 공개 저장소 — GitHub 검색 API 차단으로 탐색하지 못함(java-design-patterns 는 직접 이름을 알고 받았다).

## 종합 — 영어 쪽 범위 목록 후보의 기준별 판정 (Objective)

### Takeaway
**"국제 표준 어휘" 를 24765/SEVOCAB 으로 한정하면, 그것은 지금 기계 판독 목록으로 받을 수 없고 손 조회 기록 꼴로만 쓸 수 있다.** 기계 판독·고정·공개 게시가 모두 되는 후보는 iSAQB 용어집(CC BY 4.0)과 Azure 패턴 44개(CC BY 4.0), 그리고 이름만 손으로 옮기는 작은 닫힌 목록들(GoF · SOLID · 패키지 원칙 · GRASP)이다. 어느 국제 어휘도 한국어를 담고 있지 않다.

### Cited Findings
- 아래 표는 위 절들의 인용을 기준 6개로 모은 것이다(각 칸의 근거는 해당 절에 있다).

  | 후보 | (1) 기계 판독 | (2) 고정 수단 | (3) 오프라인 | (4) 설계 탐침 적중 | (5) 로컬 저장 · 공개 게시 | (6) 한국어 | 표지 |
  |---|---|---|---|---|---|---|---|
  | ISO/IEC/IEEE 24765:2017 PDF | PDF(유료) | 판 번호 | 구매 시 | 미확인 | 복제에 서면 허락 필요 | 없음(영어만) | 🟡 |
  | SEVOCAB | 웹 검색만, 내보내기 미확인 | 조회 날짜 + 24765 판 | 아니오 | coupling · cohesion 확인, 나머지 미확인 | 정의 복사는 출처 표기 시 허용(2차 인용), 대량 추출 미확인, PMI 정의 별도 | 없음 | 🟡 |
  | SWEBOK v4.0a | PDF(무료, 이메일) | 판 + PDF 해시 | 예(PDF) | 미확인 | All rights reserved, 무료는 개인·학술용 | 공식판 없음 | 🟡 |
  | ISO/IEC 2382:2015 (OBP) | 열람만, 내려받기 불가 | 판 + 2022-10 정정 | 아니오 | 범위 밖(IT 일반) | 열람만 | 없음(영·불) | 🟡 |
  | IEEE 610.12-1990 | PDF(유료) | 판 | 구매 시 | 24765 로 흡수 | 저작권 | 없음 | 🟡 |
  | iSAQB Glossary | AsciiDoc + JSON | `2024.1` + 커밋 `bd3ce64` | 예 | 8/16 (+Layer) | CC BY 4.0 | 없음(영·독) | 🔵 |
  | Azure 클라우드 디자인 패턴 | Markdown 표 | 커밋 `6d1df20` | 예 | 1/16 | CC BY 4.0 | ko-kr 페이지 있음(기계 번역 의심) | 🔵 |
  | java-design-patterns | YAML 전단 | 커밋 `4cabb20` | 예 | 2/16 | MIT | ko 17개(제목 영어) | 🔵 |
  | GoF 23 · SOLID 5 · 패키지 6 · GRASP 9 | 손으로 옮김 | 책 판 | 예 | SRP · DIP · coupling · cohesion | 이름은 미국법상 비저작물 | 번역서에 있음(미측정) | 🟡 |
  | EIP 65 | 웹(이름 등 CC BY) | 조회 날짜 | 아니오 | 0/16 | 이름·문제/해법 문장 CC BY | 미확인 | 🟡 |
  | DDD Reference 2015 | PDF | 판(2015-03) | 예 | bounded context(미확인) | CC BY 4.0 | 미확인 | 🟡 |
  | PoEAA 카탈로그 | 웹 | 조회 날짜 | 아니오 | 미확인 | 미확인 | 번역서 있음(미측정) | 🟡 |
  | refactoring.com | 웹 | 조회 날짜 | 아니오 | refactoring(미확인) | 미확인 | 『리팩터링 2판』 | 🟡 |
  | microservices.io | 웹 | 조회 날짜 | 아니오 | 미확인 | 미확인 | 미확인 | 🟡 |
  | SEBoK 용어집 | 위키 | 조회 날짜 | 아니오 | cohesion(24765 재인용) | CC BY-NC-SA / NC-ND | 없음 | 🟡 |
  | Wikidata | JSON 덤프 | 덤프 날짜 | 가능(큼) | 미확인 | CC0 | label 있을 가능성(미측정) | 🟡 |
  | Wikipedia 용어집·범주 | 덤프 | 덤프 날짜 | 가능 | 미확인 | CC BY-SA | 언어 간 링크(미측정) | 🟡 |

### Inferences
- 💭 70 — 사용자 결정("국제 표준 어휘 + 사용자 제공 목록, LLM 판단 없음")을 지키는 가장 단순한 구성은 다음과 같다. ① 24765/SEVOCAB 을 **범위의 권위 출처**로 두되 손 조회 기록(조회 날짜 · 24765:2017 · 출처 표준 표기)으로만 싣고, ② 기계 판독 씨앗 목록은 이름만으로 된 닫힌 목록(GoF · SOLID · 패키지 원칙 · GRASP)과 iSAQB 표제어를 쓰고, ③ 나머지(`side effect` · `postcondition` · `call graph` 등)는 사용자 제공 목록이 맡는다. 각 행에 "어느 목록에서 왔는가" 를 열로 남기면 범위 결정에 LLM 이 끼지 않는다.
- 💭 65 — 우선순위(가중치)를 출처 종류로 매기는 것이 자연스럽다: 국제 표준(24765) > 설계 원칙 닫힌 목록(SOLID · 패키지 원칙 · GRASP · GoF) > 아키텍처 공동체 용어집(iSAQB) > 분산·통합 패턴 목록(Azure · EIP · microservices.io) > 프레임워크·언어 저장소(java-design-patterns). 이것은 제안이고 사용자가 정한다.
- 💭 80 — 한국어 쪽은 이 목록들에서 얻을 수 없다. 영어 쪽 범위 목록과 한국어 근거 출처는 완전히 별개 갈래로 두어야 한다. 예외는 MS Learn ko-kr 의 Azure 패턴 이름(기계 번역 의심 표지 필요)과 java-design-patterns 의 한국어 본문 17개뿐이다.

### Gaps
- SEVOCAB 의 실제 수록 범위가 이 종합의 가장 큰 미지수다. `pascal.computer.org` 와 `www.computer.org` 를 네트워크 허용 목록에 넣으면 탐침 16개를 바로 손 조회해 이 표의 "미확인" 칸 대부분을 메울 수 있다.
- 각 출처의 한국어 번역서(GoF · PoEAA · 리팩터링 · EIP)에 실린 이름 대응은 이번 범위(영어 쪽 목록) 밖이라 재지 않았다.
