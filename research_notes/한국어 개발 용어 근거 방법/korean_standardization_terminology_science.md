# 한국어 IT 용어 표준화와 용어학 — 영어 개발 용어의 한국어 표기를 고를 때 쓸 근거 자원과 연구

> 작성일 2026-10-28. **조사 환경의 한계부터 밝힌다.** 이 세션의 네트워크 정책 때문에 국내 공식 사이트를 하나도 열지 못했다.
> `opendict.korean.go.kr` · `www.data.go.kr` 는 WebFetch 가 `getaddrinfo ENOTFOUND` 로 실패했고, curl 로 시험한
> `stdict.korean.go.kr` · `terms.tta.or.kr` · `www.korean.go.kr` · `krdict.korean.go.kr` · `www.kms.or.kr` · `www.kiise.or.kr` ·
> `www.electropedia.org` · `iate.europa.eu` 는 모두 프록시가 `CONNECT tunnel failed, response 403` 으로 막았다.
> 따라서 **아래의 국내 자원 관련 사실은 전부 WebSearch 결과 스니펫(snippet)에서 왔고, 원문 페이지는 열어 보지 못했다.**
> 스니펫이 서로 어긋나는 곳은 그렇다고 적었다. 같은 이유로 GitHub 저장소 README 도 `gh` 권한이 없어 직접 읽지 못했다.
>
> 각 자원은 과제가 정한 여섯 기준으로 판정한다 — ① 결정론적(Deterministic, LLM·신경망 추론 없이 근거를 낼 수 있는가)
> ② 재현 가능한 스냅숏(Reproducible snapshot, 날짜·판·해시로 고정 가능한가) ③ 오프라인·로컬 가능성(bulk download 인가, 웹 조회·API 뿐인가)
> ④ 소프트웨어 개발 어휘 포괄 범위(coverage) ⑤ 사용 조건(license, 로컬 저장·파생 데이터 공개) ⑥ 상태 정보(status: 표준/허용/비권장, 순화어·다듬은 말 여부).

## Q1. 국립국어원 자원 — 우리말샘 · 표준국어대사전 · 다듬은 말 · 외래어 표기법/용례 · 온용어 · 전문용어 표준화 고시

### Takeaway
국립국어원 계열에서 **로컬에 통째로 내려받을 수 있는 것은 우리말샘(로그인 후 "전체 내려받기" XML ZIP, CC BY-SA 2.0 KR)** 이 사실상 유일하게 확인됐고, 나머지(다듬은 말 약 1.8만 건, 외래어 표기 용례, 2025-05 개통한 용어 통합 플랫폼 **온용어**)는 웹 목록이나 Open API 조회로만 확인된다. 상태 정보에 가장 가까운 것은 다듬은 말의 "다듬을 말 → 다듬은 말" 쌍, 외래어 용례 API 의 "관련 표기(이표기·오표기)", 우리말샘의 "참여자 제안 정보 / 전문가 감수 정보" 구분이다. **온용어의 출처 목록에 TTA 정보통신용어사전이 들어 있다는 스니펫이 있다** — 사실이면 TTA 용어를 기계로 조회하는 간접 경로가 된다(미확인).

### Cited Findings

**우리말샘 (opendict.korean.go.kr)**
- 2016년 10월 개통한 사용자 참여형 사전. 표준국어대사전 50만 어휘에 일상어·지역어·전문용어 등을 더해 100만 어휘, 그중 전문용어 약 35만 개(2016 개통 시점 보도). — [뉴시스 2016-09-28](https://mobile.newsis.com/view/NISX20160928_0014415310); [korea.kr 개통 브리핑](https://www.korea.kr/news/policyNewsView.do?newsId=156157539)
- 한 개인 저장소의 통계는 표제어를 **일상어 506,415 · 전문어 706,422** 로 나누어 적는다(작성 시점 불명, 2016년 수치와 다르다). — [mukenko/opendict-db (검색 스니펫)](https://github.com/mukenko/opendict-db)
- 2022-02-03 검색 기준 우리말샘 표제어 총 1,137,315개라는 학술 논문 수치가 있다. — [탐라문화 2022 논문 PDF](http://jst.re.kr/upload/pdf/RC00095177.pdf)
- 전문 분야 체계: 표준국어대사전의 **53개 분야를 우리말샘에서 67개로 확장**했다. 다만 "정보·통신" 분야의 표제어 수는 찾지 못했다. — [탐라문화 2022 논문 PDF](http://jst.re.kr/upload/pdf/RC00095177.pdf)
- 신뢰도 층위: 일반 사용자 정보는 표현·표기 감수를 거쳐 **"참여자 제안 정보"**, 분야 전문가 감수를 거치면 **"전문가 감수 정보"** 로 표시된다. — [bartoc.org 우리말샘 항목 (검색 요약)](https://bartoc.org/en/node/20607); [트리위키 우리말샘](https://namu.wiki/w/%EC%9A%B0%EB%A6%AC%EB%A7%90%EC%83%98)
- **라이선스: 크리에이티브 커먼즈 저작자표시-동일조건변경허락(CC BY-SA)** 이 사전 안의 모든 자료에 적용된다고 국립국어원 사용 설명 영상이 안내하고, 공공데이터포털 등록 정보도 이용허락범위를 "저작자표시-동일조건변경허락" 으로 적는다. — [국립국어원 우리말샘 사용 설명 영상](https://www.korean.go.kr/front/board/boardMovieView.do?board_id=16&b_movie_type=&mn_id=234&b_seq=221&pageIndex=1); [data.go.kr 국립국어원_개방형 사전(우리말샘)](https://www.data.go.kr/data/15019347/openapi.do)
- 판(version)은 **CC BY-SA 2.0 KR** 로 적힌다(개인 저장소 설명과 온용어 페이지 문구). 출판물에서 인용된 예문은 자유 사용이 제한된다. — [mukenko/opendict-db (검색 스니펫)](https://github.com/mukenko/opendict-db); [온용어 항목 페이지 (검색 스니펫)](https://kli.korean.go.kr/term/trgtWord/indexTrgtWord.do?trgtWordNo=619315)
- **충돌:** 2016년 개통 브리핑은 "저작권이 설정되지 않기 때문에 누구나 어떤 목적으로든 활용할 수 있다" 고 설명했다 — 현재 안내(CC BY-SA)와 어긋나며 오래된 자료다. — [korea.kr 브리핑](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156157539)
- **전체 내려받기(bulk download):** 회원 가입·로그인 후 "내 정보 관리 → 사전 내려받기" 에서 "전체 내려받기" 로 **XML ZIP** 을 받는다는 설명이 있다. 검색 결과를 골라 파일 형식·항목을 설정해 요청하면 잠시 뒤 같은 메뉴에서 받는 방식도 있다. 로그인 없이 요청하면 로그인 HTML 이 200 OK 로 돌아온다는 개발 기록도 있다. 공개 API 에는 전체 내려받기 기능이 없다. — [mukenko/opendict-db 등 (검색 스니펫)](https://github.com/mukenko/opendict-db); [국립국어원 자료 찾기 영상](https://m.korean.go.kr/front/board/boardMovieView.do?board_id=14&b_movie_type=4&mn_id=56&b_seq=292&pageIndex=1&searchCondition=&searchKeyword=)
- **Open API:** 검색 `https://opendict.korean.go.kr/api/search` (q, start, num; `advanced=y` 일 때 target·method·올린 날짜·고친 날짜 범위), 조회 `https://opendict.korean.go.kr/api/view` (method=word_info 또는 target_code). target_code 는 2026년 9월 기준 약 1,553,000 까지 있다는 기록과 약 500,000 까지였다는 옛 블로그 기록이 섞여 있다. **전문 분야 필터 코드표는 찾지 못했다.** — [mukenko/opendict-db (검색 스니펫)](https://github.com/mukenko/opendict-db); [Enphago 블로그 2020](https://blog.yjyoon.dev/project/2020/10/11/enphago-02/)
- 공공데이터포털에도 우리말샘 Open API 가 복수로 등록돼 있다(15019347, 15119597, 15105193). — [data.go.kr 15019347](https://www.data.go.kr/data/15019347/openapi.do); [data.go.kr 15119597](https://www.data.go.kr/data/15119597/openapi.do); [data.go.kr 15105193](https://www.data.go.kr/data/15105193/openapi.do)

**표준국어대사전 (stdict.korean.go.kr)**
- 우리말샘의 기반(50만 어휘)이며 전문 분야 53개 체계다. — [탐라문화 2022 논문 PDF](http://jst.re.kr/upload/pdf/RC00095177.pdf); [뉴시스 2016](https://mobile.newsis.com/view/NISX20160928_0014415310)
- 국립국어원 "우리말 다듬기" 사업은 **표준국어대사전 등재 여부를 정착도(定着度) 기준**으로 삼아 다듬을 말을 골랐다(엄밀한 기준은 아니라고 스스로 밝힘, 2005). — [박용찬, 새국어생활 2005-1](https://www.korean.go.kr/nkview/nklife/2005_1/2005_0103.pdf)
- 표준국어대사전과 교육부 편수자료의 수학 용어를 비교한 연구는 대사전에 잘못되거나 일관되지 않은 수학 용어 내용이 많다고 지적한다. — [한국수학사학회지 2020 PDF](https://koreascience.kr/article/JAKO202026252145012.pdf)
- 표준국어대사전 뜻풀이의 "~로 순화" 표지와 그 기계 판독 형태, 별도 내려받기와 라이선스 문구는 이번 검색에서 확인하지 못했다(→ Gaps).

**다듬은 말 (korean.go.kr/front/imprv/refineList.do)**
- 웹 목록은 "번호 · 다듬을 말 · 원어 · 다듬은 말" 열로 구성되고, 조회 시점에 따라 **18,319건 / 18,324건** 으로 표시됐다. — [국립국어원 다듬은 말 목록](https://www.korean.go.kr/front/imprv/refineList.do) (검색 스니펫)
- 상세 항목은 순화 대상어, 순화어, 원어, 의미/용례, **참고 사항(순화 이력 등)** 으로 구성된다. — [국립국어원 온라인가나다 답변](https://korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=216&qna_seq=261071)
- data.go.kr 에서 다듬은 말 전체 CSV 파일데이터는 확인되지 않았다. 문화체육관광부 정책 페이지에 2004-07-12 ~ 2013-07-01 순화어 목록이 **hwp 첨부**로 게시돼 있다. — [문화체육관광부 우리말 다듬기 순화어 목록](https://www.mcst.go.kr/site/s_policy/dept/deptView.jsp?pSeq=530&pDataCD=0417000000)
- 2026-07-01 문체부·국립국어원은 전국 15세 이상 3,000명 **수용도 조사**를 거쳐 외래어 13개를 다듬었다('래플' → '추첨 판매' 등). — [뉴데일리 2026-07-01](https://www.newdaily.co.kr/site/data/html/2026/07/01/2026070100031.html)

**외래어 표기법 · 외래어 표기 용례 (korean.go.kr/kornorms)**
- **외래어·로마자 용례 Open API** 가 있다. 요청 URL `https://korean.go.kr/kornorms/exampleReqList.do`, 인증키 `serviceKey`, `resultType` xml/json, `langType` 외래어 0003 · 로마자 0004. 응답 필드에 원어 표기·국명·언어명, 공통으로 한글 표기와 **관련 표기(이표기·오표기)** 가 있다. 1인 1키. — [국립국어원 kornorms Open API 안내 (검색 스니펫)](https://korean.go.kr/kornorms/main/openAPI.do)
- 정부·언론 외래어 심의 공동위원회가 새 외래어 표기를 계속 심의하며 결정 사항을 누리집에서 검색할 수 있다. 일반 용어·중국/일본/로마자 인지명 용례 파일은 누구나 내려받도록 공개돼 있다고 국립국어원 20년사가 소개한다. — [국립국어원 20년사](https://korean.go.kr/niklintro2/20years05_01_02.jsp)
- data.go.kr 에 "국립국어원_한국어 어문규범 규정 정보_20250902" 파일데이터가 있다(내용 구성은 열어 보지 못했다). — [data.go.kr 15122678](https://www.data.go.kr/data/15122678/fileData.do?recommendDataYn=Y)

**온용어 (kli.korean.go.kr/term) — 2025 개통 용어지식 플랫폼**
- 2025-05-15 정식 개통. 정보통신·국방·해양·무역·법령·문화 등 **36개 국가·공공기관이 간행한 53개 용어집의 용어 120만 개**를 통합했다. 2024년 9월부터 시범 운영했다. — [뉴시스 2025-05-15](https://www.newsis.com/view/NISX20250515_0003177165); [국립국어원 보도자료 "'온용어'의 용어지식, 인공지능 개발 자료로 거듭나다"](https://www.korean.go.kr/front/board/boardStandardView.do;front=B6D3D6D2C9ED52BB036BF1B0A6E34F58?board_id=6&b_seq=1001&mn_id=184)
- **충돌:** 사이트 현황 페이지는 용어집 수를 54로 표시한다는 스니펫이 있다(보도자료는 53). — [온용어](https://kli.korean.go.kr/term) (검색 스니펫)
- **출처 목록에 "정보 통신 용어 사전 (한국정보통신기술협회)"** 가 있다는 스니펫이 있다. — [온용어](https://kli.korean.go.kr/term) (검색 스니펫)
- **Open API:** 검색 `kli.korean.go.kr/term/api/search.do`, 필수 인증키(16진수 32자리)·`apiSearchWord`(UTF-8), 선택 `start` 1~1000. — [온용어 Open API 안내](https://kli.korean.go.kr/term/bbs/indexOpenApiInfo.do); [영문판](https://kli.korean.go.kr/term/bbs/indexOpenApiInfo.do?lang=en)
- **라이선스는 용어마다 다르다.** API 안내는 상업적 이용·2차적 저작물 허용 여부가 다른 이용허락 유형을 설명한다(1유형: 출처 표시, 상업적·비상업적 이용 가능, 변형 가능). 실제 항목 페이지에는 "공공누리 1유형" 표기와 "[제2유형] 출처 명시+상업적 이용 금지" 표기가 섞여 있고, 우리말샘 출처 항목은 CC BY-SA 2.0 KR 문구를 단다. — [온용어 Open API 안내](https://kli.korean.go.kr/term/bbs/indexOpenApiInfo.do); [온용어 항목 2175842](https://kli.korean.go.kr/term/trgtWord/indexTrgtWord.do?trgtWordNo=2175842); [온용어 항목 619315](https://kli.korean.go.kr/term/trgtWord/indexTrgtWord.do?trgtWordNo=619315); [공공누리 유형 설명](https://www.kogl.or.kr/info/license.do)

**국가 전문용어 표준화 · 고시**
- 근거는 국어기본법 제17조(전문용어의 표준화 등, 2017-03-21 개정 표기). 시행령 제12조는 중앙행정기관에 위원장 포함 5~20명의 전문용어 표준화협의회를 둔다(2017 시행령 기준, 그 뒤 개정 여부 미확인). — [위키문헌 국어기본법](https://ko.wikisource.org/wiki/%EA%B5%AD%EC%96%B4%EA%B8%B0%EB%B3%B8%EB%B2%95); [위키문헌 국어기본법 시행령 (제28306호)](https://ko.wikisource.org/wiki/%EA%B5%AD%EC%96%B4%EA%B8%B0%EB%B3%B8%EB%B2%95_%EC%8B%9C%ED%96%89%EB%A0%B9_(%EC%A0%9C28306%ED%98%B8))
- 절차(2005 시행령 기준): 기관장이 심의를 요청 → 문화부 장관이 국어심의회 심의를 거쳐 확정 → 기관장이 고시. 고시된 용어는 법령 제·개정, 교과용 도서, 공문서, 국가 시험 출제에 활용하도록 했다. — [위키문헌 국어기본법 시행령](https://ko.wikisource.org/wiki/%EA%B5%AD%EC%96%B4%EA%B8%B0%EB%B3%B8%EB%B2%95_%EC%8B%9C%ED%96%89%EB%A0%B9)
- 2013년 행정 분야 전문용어 312개를 고시하며 **정착할 때까지 기존 용어와 병용·병기를 허용**했다. — [문화체육관광부 보도자료](https://www.mcst.go.kr/site/s_notice/press/pressView.jsp?pSeq=12589) (검색 요약)
- 근래 사례는 철도(2022)·지적·공간정보(2024)·체육 분야이며, **정보통신 분야의 국가 고시 전문용어 목록은 찾지 못했다.** — [메트로서울 2022](https://www.metroseoul.co.kr/article/20221005500119); [뉴스서울](https://www.newsseoul.co.kr/news/view/1065599418691563)

### Inferences
- 💭 우리말샘 전체 XML ZIP 은 ②(내려받은 날짜 + ZIP 해시로 고정)과 ③(로컬)을 동시에 만족하는 국립국어원 자원으로는 확인된 유일한 후보다. 다만 로그인이 필요해 **자동 재현(무인 내려받기)은 어렵고**, 사람이 받은 파일의 해시를 고정하는 방식이 맞는다.
- 💭 CC BY-SA 2.0 KR 의 동일조건변경허락 때문에, ko-dev-terms 가 우리말샘에서 뽑은 **행(evidence row)을 공개하면 그 파생 데이터도 CC BY-SA 로 내야 할 가능성이 있다.** 근거 행이 "출처·표제어 id·건수" 수준의 사실 정보면 저작물성 판단이 달라질 수 있으나 이것은 법적 판단이라 이 노트에서 결론 내지 않는다.
- 💭 외래어 용례 API 의 "관련 표기(이표기·오표기)" 는 한국어 공식 자원 가운데 **비권장(deprecated) 표기를 기계적으로 돌려주는 거의 유일한 필드**로 보인다(예: 한 원어에 대한 표준 한글 표기 + 오표기). 개발 용어 대부분은 용례에 없을 것이므로 포괄 범위는 작을 것이다(미측정).
- 💭 온용어는 TTA 를 포함한 53~54개 용어집을 한 API 로 묶으므로 "TTA 는 수동 조회만" 이라는 기존 결정을 재검토할 근거가 된다. 단 ① 항목별 라이선스가 1·2유형으로 갈리고 ② bulk download 가 확인되지 않았으며 ③ TTA 용어 전체가 들어 있는지 확인되지 않았다.

**기준 판정표 (근거는 위 Cited Findings)**

| 자원 | ① 결정론 | ② 스냅숏 | ③ 오프라인 | ④ 개발 어휘 | ⑤ 라이선스 | ⑥ 상태 정보 |
|---|---|---|---|---|---|---|
| 우리말샘 전체 XML | 예(사전 조회) | 가능 — 내려받은 날짜+ZIP 해시. 공식 판 번호는 못 찾음 | 예(로그인 후 수동) | 정보·통신 분야 있음, 건수 미확인 | CC BY-SA 2.0 KR, 출판물 예문 제외 | 참여자 제안/전문가 감수 구분. 표준/비권장 표지는 미확인 |
| 우리말샘 Open API | 예 | 응답을 캐시해 해시로만 | 아니오(키 필요 온라인) | 위와 같음 | 위와 같음 | 위와 같음 |
| 표준국어대사전 | 예 | 미확인 | 미확인 | 53개 분야, 건수 미확인 | 미확인 | "~로 순화" 표지 존재 여부 미확인 |
| 다듬은 말 | 예 | 웹 목록 복사뿐(18,319~18,324건) | 웹/hwp(2004~2013) | 일반어 위주, IT 비중 미측정 | 미확인 | **있음 — 다듬을 말→다듬은 말, 순화 이력** |
| 외래어 용례 API | 예 | 응답 캐시 | 아니오 | 작을 것(미측정) | 미확인 | **있음 — 이표기·오표기** |
| 온용어 API | 예 | 응답 캐시 | 아니오 | 정보통신 용어집 포함(120만 중 비중 미확인) | 항목별 공공누리 1·2유형 / CC BY-SA 혼재 | 미확인 |
| 고시 전문용어 | 예 | 고시 번호·날짜 | 고시문(형식 미확인) | IT 분야 고시 못 찾음 | 공공저작물(조건 미확인) | 고시 = 표준, 기존 용어 병용 허용 |

### Gaps
- 우리말샘 "정보·통신" 분야 표제어 수, Open API 의 전문 분야 필터 코드, 전체 XML 의 스키마(전문 분야·감수 상태가 필드로 들어 있는지) — 원문 페이지 접근 불가로 확인 못 함.
- 표준국어대사전 별도 내려받기 존재 여부·라이선스, 뜻풀이의 "순화" 표지가 기계 판독 필드인지 — 확인 못 함.
- 다듬은 말의 공식 기계 판독 파일(CSV/JSON) 존재 여부 — data.go.kr 에서 찾지 못함. 페이지 자체 내려받기 버튼 유무는 열어 보지 못함.
- 온용어 bulk download(보도자료 제목이 "인공지능 개발 자료" 를 말하지만 형식·조건은 스니펫에 없음), 응답 필드에 상태(표준/권장) 정보가 있는지, TTA 수록 범위.
- 국어기본법 시행령의 2024 이후 현행 조문 — 국가법령정보센터를 열지 못함.

## Q2. TTA 정보통신용어사전 — 2026년 기준 공식 Open API · data.go.kr 데이터셋 · bulk export 유무

### Takeaway
2026-10-28 재확인에서도 **TTA 정보통신용어사전의 공식 Open API·data.go.kr 데이터셋·bulk export 는 찾지 못했다.** 확인된 기계 경로는 비공식 Ruby gem(스크래퍼)과, 사실이라면 국립국어원 온용어 API 를 거치는 간접 경로뿐이다. 항목에는 URL 상 `word_seq` 식별자가 있어 수동 조회 결과를 "출처·항목 id·조회 날짜" 로 고정하는 데는 쓸 수 있다.

### Cited Findings
- TTA 는 1993년부터 정보통신 용어를 해설·표준화해 정보통신용어사전(terms.tta.or.kr)을 웹과 모바일 앱으로 서비스한다. — [bartoc.org TTA 항목](https://bartoc.org/en/node/20286) (검색 요약)
- 검색된 data.go.kr 용어집 항목들은 TTA 가 아니라 다른 기관 것이었다(제약산업 용어집, 부산교통공사 도시철도 용어집 등). data.go.kr 은 파일데이터를 RestAPI(JSON/XML)로 자동 변환해 제공하는 구조다. — [data.go.kr 15153635](https://www.data.go.kr/data/15153635/fileData.do); [data.go.kr 15138985](https://data.go.kr/data/15138985/openapi.do)
- 비공식 Ruby gem `tta_terms_api` 가 정보통신용어사전을 Ruby 에서 호출하는 인터페이스로 존재한다(TTA 공식 아님). — [rubydoc tta_terms_api 0.0.2](https://www.rubydoc.info/gems/tta_terms_api/0.0.2)
- 2025년 검색에서도 TTA 의 API·개방 데이터 근거는 나오지 않았고, 비슷한 이름의 data.go.kr API 는 ETRI WiseWordNet 기반 어휘 정보 API 와 행정안전부 공공데이터 공통표준용어(CSV/JSON/XML·API 개방, 2025-12 약 1.3만 개로 확대)였다 — 둘 다 TTA 사전이 아니다. — [data.go.kr ETRI 어휘 정보 API](https://www.data.go.kr/data/15124651/openapi.do); [전자신문 2025-12-23](https://www.etnews.com/20251223000026)
- 항목 URL 은 `dictionaryView.do?word_seq=177559-1` 꼴의 식별자를 가진다. — [TTA 정보통신용어사전 Open API 항목](http://terms.tta.or.kr/dictionary/dictionaryView.do?word_seq=177559-1)
- 표준화 체계: TTA 정보통신용어표준화위원회가 TTA 표준에 포함되는 용어 정의를 포함해 정보통신 용어를 정리하고 우리말화한다. 분과위원회 검토 → 심의위원회 상정 → **"표준용어" 로 결정**하는 절차다. 1991년부터 분과·심의위원회를 운영해 왔다. — [TTA 정보통신용어표준화위원회](https://committee.tta.or.kr/standard/general.jsp?commit_code=WORDSTD); [TTA저널 기사 PDF](https://koreascience.kr/article/JAKO200370709953124.pdf)
- 채택 결과는 사전 공지로 발표된다. 예: 제2014-2차 심의에서 표준용어 "사물 인터넷(IoT)", "LTE-Advanced" 외 86어 채택. — [TTA 정보통신용어사전 공지 35](http://word.tta.or.kr/noticeView.do?public_no=35)
- 원고 작성 지침: 영문은 가능한 한 우리말화하고 원어·약어는 괄호 안에 쓰며, **외래어는 외래어 표기법에 따라** 표기한다. 관용 표기 허용 조항은 확인되지 않았다. — [TTA 공지·지침 (검색 스니펫)](http://word.tta.or.kr/noticeView.do?public_no=35)
- TTA 는 방송통신위원회와 2011년부터 순화어 작업을 해 왔다(2014 무렵 기사). 검색 요약이 두 기사 중 어느 쪽에서 왔는지 특정하지 못했다. — [블로터 포럼](https://www.bloter.net/news/articleView.html?idxno=16237); [매일신문 2014-10-04](http://news.imaeil.com/Life/2014100407544195295)
- 온용어의 출처 목록에 "정보 통신 용어 사전 (한국정보통신기술협회)" 이 있다는 스니펫(Q1 참조). — [온용어](https://kli.korean.go.kr/term)
- TTA 사전의 이용약관·저작권 정책·데이터 제공 요청 절차는 검색으로 확인되지 않았다. — [검색 결과 없음; bartoc.org TTA 항목만 확인](https://bartoc.org/en/node/20286)

### Inferences
- 💭 TTA 의 "표준용어" 채택은 ⑥ 상태 정보에 해당하는 개념(심의를 거친 표준 vs 그 밖의 해설 용어)을 가진다. 그러나 그것이 사전 항목에 필드로 표시되는지는 확인하지 못했다.
- 💭 수동 조회만 가능하다면 증거 행은 `source=TTA, entry=word_seq, accessed=날짜, (선택) 화면 저장 해시` 꼴이 현실적이다. `word_seq` 가 안정 식별자인지(개정 시 바뀌는지)는 모른다.
- 💭 온용어 API 로 TTA 출처 항목을 받을 수 있다면 ①·③(캐시)·⑤(항목별 공공누리 표기)가 TTA 직접 조회보다 낫다. 검증 전에는 가설로만 둔다.

**기준 판정표**

| 자원 | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| TTA 정보통신용어사전(웹) | 예(조회) | `word_seq`+조회 날짜. 판 번호 없음 | 아니오(웹·앱만) | 정보통신 전용 — 건수 미확인 | 미확인 | "표준용어" 채택 개념 있음, 항목 표시 미확인 |
| 비공식 `tta_terms_api` | 예 | 아니오(스크래핑) | 아니오 | 위와 같음 | 공식 허락 근거 없음 | — |
| 온용어 경유 TTA | 예 | 응답 캐시 | 아니오 | 수록 범위 미확인 | 항목별 공공누리 | 미확인 |

### Gaps
- `terms.tta.or.kr`·`data.go.kr` 를 열지 못해 공지·약관·내려받기 메뉴를 직접 보지 못했다. TTA 사전 전체 표제어 수도 찾지 못했다.
- TTA 표준용어 결정이 항목 화면에 표지로 남는지, 표준화 지침 원문(관용 표기 허용 여부)은 확인 못 함.

## Q3. 한국정보과학회(KIISE) · 대한수학회(KMS) · 한국표준협회 KS X · 교육부 편수 자료 — 기계 판독 가능성과 라이선스

### Takeaway
네 자원 중 **웹에서 영문명–한글명 대응표를 실제로 노출하는 것은 대한수학회 수학용어 사전뿐**이고(목록 URL 에 정렬·오프셋 매개변수가 있다), 내려받기·라이선스는 확인되지 않았다. KIISE 정보과학 용어집은 존재 자체를 확인하지 못했고, KS X 쪽은 "KS X ISO/IEC 2382" 라는 번호는 찾지 못했으며 대신 **KS X 0001 시리즈(정보기술 용어)** 가 제3자 목록에 보인다. 교육부 편수 자료의 정보 교과판은 찾지 못했다.

### Cited Findings
- **대한수학회 수학용어 사전:** 영문명–한글명 정보를 제공하고 한글명·영문명 키워드 검색과 알파벳순 목록을 지원한다. 목록 URL 예 `kms.or.kr/mathdict/list.html?...&sort=ename&start=420` (예: antipodal point → 대척점). — [kms 대한수학회 수학용어 목록](https://www.kms.or.kr/mathdict/list.html?alpa=&key=&keyword=&sort=ename&start=420)
- 2021년 "수학용어 개선방안 연구"(한국과학창의재단 제출)는 제3차 교육과정 이후 수학 용어가 거의 바뀌지 않은 이유를 교육과정 문서에 용어·기호를 명시해 표준화했기 때문으로 분석한다. — [2021 수학용어 개선방안 연구 최종보고서 PDF](https://cdn.kosac.re.kr/files/legacy_data/jnrepo/upload/jnBrdBoard/202204/3c2b5acba8d44707aaaf2bc30eb130bf_1650949858477.pdf)
- 그래프 이론에서 vertex 는 "꼭짓점·정점·버텍스·노드", edge 는 "간선·모서리·엣지" 가 함께 쓰인다(위키백과 계열 자료). 대한수학회의 공식 표기(꼭짓점 vs 정점)는 검색으로 확인하지 못했다. — [위키백과 꼭짓점 (그래프 이론)](https://www.wikiwand.com/ko/articles/%EA%BC%AD%EC%A7%93%EC%A0%90_(%EA%B7%B8%EB%9E%98%ED%94%84_%EC%9D%B4%EB%A1%A0))
- **KIISE:** 한국정보과학회 발간 정보과학 용어집이나 용어 표준화 위원회를 다룬 자료는 두 차례 검색에서 나오지 않았다. 1990년대 전산 용어 순화 사업은 문화체육부 후원·국어정보학회 주관이었고 뒤에 정보통신 용어 표준화위원회가 구성됐다. — [새국어생활 2001-1 PDF](https://www.korean.go.kr/nkview/nklife/2001_1/2001_0105.pdf)
- 남북 IT 용어 연구(한국어정보학회 2012)는 IT 용어가 **ISO 2382 의 한국 표준화를 기반**으로 상호 확인돼야 한다고 보고, 2005년 남북 컴퓨터용어사전(600단어) 발간을 언급한다. — [한국어정보학회 2012 학술대회 PDF](https://koreascience.kr/article/CFKO201221868478307.pdf)
- **KS X:** "KS X ISO/IEC 2382" 항목은 검색되지 않았다. 대신 **KS X 0001 시리즈(정보기술 용어)** — 예: KS X 0001-1(2022 확인) 정보기술 용어 제1부 기본 용어, KS X 0001-13(컴퓨터 그래픽스), KS X 0001-24(컴퓨터 집적 생산) — 가 제3자 표준 목록에 보인다. — [ndls.org.cn 표준 상세](https://ndls.org.cn/standard/detail/d6c6c7e9c0fb2d2ebd28edcf06ba080c); [ndls.org.cn 표준 상세 2](https://ndls.org.cn/standard/detail/2b452c374adaad0c1aebe21194f9bb84)
- **교육부 편수 자료:** 2022 개정 교육과정 정보 교과의 편수(용어) 자료는 검색되지 않았다. 정보과 표준 교육과정 제안·데이터 용어 텍스트 마이닝 연구만 나왔다. — [earticle A312045](https://www.earticle.net/Article/A312045); [SPRI](https://spri.kr/post/23121)
- 수학 분야는 교육과정 문서가 용어를 명시하고, 표준국어대사전과 교육부 편수자료를 비교한 연구가 있다. — [한국수학사학회지 2020 PDF](https://koreascience.kr/article/JAKO202026252145012.pdf)

### Inferences
- 💭 KMS 목록은 HTML 표라서 ① 결정론적 추출은 가능하지만 ② 판 고정은 "가져온 날짜 + HTML 해시" 수준이고, ⑤ 라이선스가 확인되지 않아 로컬 저장·공개 판단을 보류해야 한다.
- 💭 KS X 0001 은 ISO/IEC 2382 계열의 국내 부합 표준으로 보이나 번호 대응은 확인하지 못했다. KS 원문은 유료 판매 문서일 가능성이 높아(미확인) ③·⑤ 를 만족시키기 어려울 것이다.
- 💭 그래프 이론 용어처럼 **교과(편수)·수학회·IT 실무가 서로 다른 표기를 쓰는 영역**에서는 출처별 행을 나란히 보여 주는 ko-dev-terms 의 "승자를 고르지 않는다" 설계가 특히 필요하다.

**기준 판정표**

| 자원 | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| KMS 수학용어 사전 | 예 | HTML 해시뿐 | 웹 목록 순회만 | 수학(그래프 이론 포함). IT 일반은 아님 | 미확인 | 미확인 |
| KIISE 용어집 | — | — | — | 존재 미확인 | — | — |
| KS X 0001 시리즈 | 예 | 표준 번호·확인 연도 | 미확인(유료 추정) | 정보기술 기본 용어 | 미확인 | 표준 문서 자체가 규범 |
| 교육부 편수 자료(정보) | — | — | — | 찾지 못함 | — | — |

### Gaps
- KIISE 용어집 존재·형식·라이선스, KMS 사전 이용 조건과 bulk 형식, KS X 0001 각 부의 대응 ISO/IEC 2382 판과 구매 조건, 교육부 정보 교과 편수 자료 — 모두 원문 사이트 접근 불가로 확인 못 함.

## Q4. ISO/IEC 2382 와 한국 도입 · IEC Electropedia · ISO OBP 의 한국어 포괄

### Takeaway
ISO/IEC 2382(정보기술 어휘)는 2015년판이 현행이고 Part 1 개정 초안이 진행 중이며, 국내에서는 KS X 0001 시리즈가 그 역할을 하는 것으로 보인다. **IEC Electropedia(IEV)에는 한국어 용어 약 2만 766개가 2017~2018년에 등재**됐지만 전기전자 어휘라 소프트웨어 개발 어휘와는 겹침이 작고, 대량 복제에는 IEC 서면 허락이 필요하다. ISO OBP 의 한국어 포괄은 확인하지 못했다.

### Cited Findings
- ISO/IEC 2382:2015 는 발행돼 있고 ISO/IEC 2382-1:1993 은 폐지됐다. **ISO/IEC AWI 2382-1.2 (Part 1: Fundamental terms)** 초안이 2382:2015 와 2382-1:1993 을 대체할 예정이다. — [iss.rs ISO proj 63598](https://iss.rs/sr_Latn/project/show/iso:proj:63598); [NEK ISO/IEC 2382:2015](https://online.standard.no/en/nek-isoiec-2382-2015)
- IEV 한국어 용어 등재: 2017년 사업에서 **20,766개 한국어 전기 용어**가 Electropedia 에 등재됐다(등재 시점은 2017-12 와 2018-02 로 문헌마다 다르다). 황유모 외, 「IEV 한국어 용어 IEC Electropedia 등재」, 전기학회논문지 68(8), 2019, pp.943–950. — [koreascience JAKO201925454183556](https://koreascience.kr/article/JAKO201925454183556.pdf); [숙명 scholarworks 2924](https://scholarworks.sookmyung.ac.kr/handle/2020.sw.sookmyung/2924)
- 문봉희(2020): IEV 영어 정의 **20,996개를 한국어로 번역**하는 시스템과 프로토타입 한국어 Electropedia 웹 시스템을 구현했다. 1단계 DB 구축, 2단계 한국 TC 1 위원의 번역·수정. 정규 한국어 Electropedia 를 열어 IEC 와 연결할 필요를 제언한다. — [koreascience JAKO202008072030796](https://koreascience.kr/article/JAKO202008072030796.page?lang=ko)
- 2021년 후속 연구는 IEV 21,222개 정의를 IEV Online 에 등재하기 위한 정의 DB·용어 표준화 절차·작업 템플릿을 제안했다. — [koreascience JAKO202008072030796 (검색 요약)](https://koreascience.or.kr/article/JAKO202008072030796.pub)
- **Electropedia 이용 조건:** FAQ 는 IEC 를 출처로 밝히면 용어·정의를 쓸 수 있다고 하지만, 구조와 내용은 IEC 저작권이며 복제나 상업·무료 대량 공유에는 IEC 에 연락해야 한다. IEC 웹스토어 저작권 페이지는 더 엄격해서, 다른 사이트에 전부·일부를 재현하려면 서면 허락이 필요하고 데이터베이스의 전부·상당 부분 복제는 상업 계약 대상이라고 적는다. — [IEC webstore copyright](https://webstore.iec.ch/en/copyright); [electropedia.org](https://electropedia.org) (검색 요약)
- IEC CDD(별개 DB) 라이선스는 번역에 서면 허락이 필요하다고 한다 — Electropedia 에 같은 조항이 있는지는 확인 못 함. — [IEC CDD EULA](https://cdd.iec.ch/CDD/iec61360/iec61360.nsf/License)
- Electropedia 는 IEV 의 모든 용어·정의를 담은 "IEV Online" 이다. — [Wikipedia International Electrotechnical Vocabulary](https://en.wikipedia.org/wiki/International_Electrotechnical_Vocabulary)

### Inferences
- 💭 IEV 는 ⑥ 상태를 가진다(국제 표준 어휘라 그 자체가 규범). 그러나 ④ 소프트웨어 개발 어휘(메서드·클로저·커밋 등)와 겹치는 부분은 작을 것이다(측정하지 않음).
- 💭 ⑤ 조건상 ko-dev-terms 가 IEV 한국어 용어를 로컬에 대량 저장·공개하는 것은 허락 없이는 어렵고, 개별 항목 인용(IEV 번호 + 출처 표시) 정도가 안전한 범위로 보인다.
- 💭 ISO/IEC 2382 의 한국어 대응물을 찾는다면 ISO OBP 보다 KS X 0001 시리즈 쪽이 먼저 확인할 자리로 보인다(OBP 의 한국어 수록 여부는 아래 Gaps).

**기준 판정표**

| 자원 | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| ISO/IEC 2382:2015 | 예 | 판 연도 | 유료 표준 문서(추정, 미확인) | 정보기술 기본 어휘 — 한국어 없음(원문) | ISO 저작권 | 규범 |
| IEC Electropedia 한국어 | 예 | IEV 번호 + 조회 날짜 | 웹 조회. 대량 복제는 허락 필요 | 전기전자 위주. 한국어 용어 20,766 | 출처 표시 인용 가능, 대량 복제 서면 허락 | 국제 표준 어휘 |
| ISO OBP 한국어 | — | — | — | 확인 못 함 | — | — |

### Gaps
- KS X 0001 각 부와 ISO/IEC 2382 의 대응, ISO OBP 에 한국어 용어가 있는지, IEV 한국어 용어가 Electropedia 화면에 실제 표시되는지(2026 현재) — 확인 못 함.

## Q5. 한국어 IT 용어가 정해지고 정착하는 방식에 관한 연구 — 음역 vs 번역, 정착률, 용어 변이 측정

### Takeaway
**국가가 보급한 대체어(다듬은 말)가 영어 차용어 사용을 줄이지 못했다는 코퍼스 연구(Kim 2023, IJCL)** 가 가장 직접적인 근거이고, 국내 연구들은 순화어 정착 조건으로 "의미 범위의 정확한 대응 · 음절 수 · 결합 환경 · 이미 굳어진 외래어의 수용" 을 꼽는다. 정착도 측정은 인지율·이해율·사용률(일본 국립국어연구소 틀), 사전 등재 여부, 포털 뉴스 검색 빈도, 대규모 수용도 설문으로 이루어져 왔다. **정보통신 분야만 따로 말뭉치로 측정한 정착률 연구는 찾지 못했다.** 용어 변이(variation)는 Daille(어떻게 찾는가)과 Freixa(왜 생기는가)가 기본 문헌이고, 한국어 음역 변이 자동 추출 연구가 2000~2010년대에 있다.

### Cited Findings

**차용어 vs 대체어 — 코퍼스 연구**
- Eun-Young Julia Kim, "A corpus-based study of anglicized neologisms in Korea: A diachronic approach to Korean and English word pairs," *International Journal of Corpus Linguistics* 28(2), 2023, pp.125–143, DOI 10.1075/ijcl.20055.kim. 국립국어원 누리집이 **영어 사용을 줄인 성공 사례로 내세운 18개 한국어–영어 낱말 쌍**을 두 말뭉치·6년 범위로 조사했다. **한국어 대체어 보급이 영어 사용을 줄이지 못했고 영어 기반 낱말이 대체어와 함께 늘어났다.** 보급된 한국어 낱말 가운데 매우 드문 것이 여럿 있고 일부 차용어는 의미가 분화했다. — [EBSCO 초록](https://www.ebsco.com/articles/language-and-linguistics/b65c5723-0e17-54f1-8718-a78554bb7a92/a-corpus-based-study-of-anglicized-neologisms-in-korea-a-diachronic-approach-to-korean-and-english-word-pairs); [Scilit](https://www.scilit.net/article/8228076f939d607a046c15284943a196); [Benjamins IJCL 28:2](https://benjamins.com/catalog/ijcl.28.2)
- Oh & Son, "Lexical borrowing in Korean: a diachronic approach based on a corpus analysis," *Corpus Linguistics and Linguistic Theory* 20(2), 2024, pp.407–431, DOI 10.1515/cllt-2022-0102. 1970~2015년 여성지 주거 기사 말뭉치의 차용어 약 9,500개(보통명사·고유명사·동사·형용사)를 type/token 빈도와 문화 차용어/핵심 차용어로 분석했다. 차용어 사용은 점진적·급격하게 늘었고 1990년대에 뚜렷한 전환이 있다. — [De Gruyter PDF](https://www.degruyterbrill.com/document/doi/10.1515/cllt-2022-0102/pdf); [NCCU repository](https://irtest.lib.nccu.edu.tw/handle/140.119/151256)
- 2017~2021년 신어 1,856개 중 **58.2%** 가 차용 요소를 포함했고 주 원천 언어는 영어였다(*Lexicography*, 2023). — [EBSCO 초록](https://www.ebsco.com/articles/language-and-linguistics/cf8d6c95-3be3-5eb0-b781-8240ec0823a2/korean-neologisms-of-2017-2021-correlation-between-borrowing-semantic-characteristics-and-lexicographic-representation)

**순화어(다듬은 말) 정착 연구 — 국내**
- 문금현, 「순화어의 정착 원리에 따른 순화 정책 방안」, 『언어사실과 관점』 61, 2024, pp.159–183. 정책 순화어의 정착 성공·실패를 비교하고 생활용어 순화어를 설문으로 조사했다. 정착 조건으로 외래어와의 의미 범위 대응, 음절 수가 더 많지 않을 것, 문장 성분·결합 환경이 같을 것, 공공기관 홍보와 언중의 호응을 든다. 응답자들은 **이미 굳어졌거나 뜻이 달라진 외래어는 받아들여야 한다**는 의견이 많았다. — [KCI ART003054456](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003054456); [DBpia NODE11900673](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11900673)
- 심지연, 「국어 순화어의 생성과 정착에 대하여」, 『한국어학』 30, 2006, pp.159–180. 순화 대상어와 의미 범위가 일치할 때 정착 가능성이 높고, 의미 범위가 넓거나 미묘하게 다르면 사용 빈도가 낮다. — [KCI ART000992742](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART000992742)
- 정미령, 「공공언어 상용 용어의 순화어에 대하여」, 『국어교육연구』 81, 2023. 일부 순화어는 순화 대상어와 의미가 같지 않고, 다의어의 확장 의미에 대응하는 순화어가 빠져 있으며, 절·명사 나열 꼴이라 단어성이 떨어진다. — [KCI ART002933040](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002933040)
- 권정현, 「전문용어 순화정책을 위한 혼종어 연구」(한성대 석사논문): 전문용어 순화는 곧 용어의 **동기화(motivation)** 이며, 조어 방식 개발과 순화어 유통성 점검이 선행돼야 한다. — [ScienceON DIKO0014147447](https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=DIKO0014147447&dbt=DIKO)

**정착도를 재는 방법 — 국립국어원 자료**
- 박용찬(2005): 표준국어대사전 등재 여부를 정착도 기준으로 삼았다. 일본 국립국어연구소는 외래어 정착도를 **인지율·이해율·사용률**로 나누고 이해율을 가장 중시했으며, 일반 국민 대상 다듬기에서는 사용률 → 이해율 → 인지율 순으로 따질 필요가 있다고 제안한다. — [새국어생활 2005-1 PDF](https://www.korean.go.kr/nkview/nklife/2005_1/2005_0103.pdf)
- 국립국어원 2011 자료집 『요긴하게 쓸 만한 다듬은 말 61개』는 **포털 뉴스 검색으로 사용 빈도가 비교적 높다고 확인된** 다듬은 말을 실었다. — [국립국어원 2011-01-40 PDF](https://www.korean.go.kr/common/download.do;front=3D3AEBF97D9FAEFE992FC4CF584455CD?file_path=reportData&c_file_name=8fcf1116-87f9-470e-a89f-f23cd0f23c23_0.pdf&o_file_name=%EC%9A%94%EA%B8%B4%ED%95%98%EA%B2%8C+%EC%93%B8+%EB%A7%8C%ED%95%9C+%EB%8B%A4%EB%93%AC%EC%9D%80+%EB%A7%90+61%EA%B0%9C.pdf)
- 참고문헌으로 이홍식(2007) 『외래어·외국어 사용 및 순화어 수용 실태조사』(국립국어원)가 인용된다 — 원문은 열지 못했다. — [DBpia NODE11900673 참고문헌 (검색 요약)](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11900673)
- 「공공언어개선의 정책효과조사연구」(2021-09-30)가 있으나 정착률 수치는 스니펫에서 확인하지 못했다. — [kplain.kr PDF](https://kplain.kr/_UploadData/bod/ce2f40373b5849f1995357b8f6eceb4dBoard_filekor5.pdf)
- 2026-07: 3,000명 수용도 조사 결과를 바탕으로 13개 확정(Q1). — [뉴데일리 2026-07-01](https://www.newdaily.co.kr/site/data/html/2026/07/01/2026070100031.html)

**정보통신 분야 순화 사업**
- 2022년 영남대 국어문화연구소와 한국지능정보사회진흥원(NIA)은 정보통신기술 용어 약 500개를 발굴하고 언어·ICT 전문가 자문과 설문을 거쳐 순화어 50개를 선정했다. — [뉴시스 2022-11-24](https://www.newsis.com/view/NISX20221124_0002099356)
- 1990년대 전산 용어 순화 운동(패스워드→열쇠말, 패킷→보쌈, 다운로드→내려받기 등)은 커뮤니티 정리본에만 상세하며, 실제로는 "비밀번호" 같은 말이 더 널리 쓰인다고 서술한다 — 학술 근거로는 약하다. — [트리위키 전산용어 순화 운동](https://namu.wiki/w/%EC%A0%84%EC%82%B0%EC%9A%A9%EC%96%B4%20%EC%88%9C%ED%99%94%20%EC%9A%B4%EB%8F%99); [KLDP 토론](https://kldp.org/node/67779)
- 순화어가 있어도 찾아보는 사람이 많지 않다는 언론 지적(2014). — [매일신문 2014-10-04](http://news.imaeil.com/Life/2014100407544195295)

**용어 변이(terminological variation) — 국제 문헌**
- Daille 외(1996), "Empirical observation of term variations and principles for their description," *Terminology* — 변이형을 원 용어와 의미·개념적으로 관련된 항목으로 정의. 검색 요약에서 나온 서지이며, 요약이 근거로 든 페이지가 아래 둘 중 어느 것인지 특정하지 못했다. — [dialnet 4125119 PDF](https://dialnet.unirioja.es/descarga/articulo/4125119.pdf); [RITerm (seer.ufrgs.br)](https://seer.ufrgs.br/index.php/riterm/article/download/37170/24032/147634)
- Daille(2017), *Term Variation in Specialised Corpora: Characterisation, automatic discovery and applications*, Benjamins TLRP 19 — 명명 변이(denominative variants)와 개념 변이(conceptual variants), 코퍼스 기반 자동 발견. — [Benjamins TLRP 19 목차](https://lwc1.benjamins.com/catalog/tlrp.19.toc)
- Freixa, Judit(2006), "Causes of Denominative Variation in Terminology: A Typology Proposal," *Terminology* 12(1): 51–77. Freixa(2022), "Causes of terminological variation," *Theoretical Perspectives on Terminology* (TLRP 23), ch.18 — 원인을 담화적(discursive)·방언적(diatopic/diastratic/diachronic)·기능적(functional)·사회언어적(언어 접촉, language contact)·인지적(cognitive)으로 분류. — [De Gruyter Brill ch.18](https://www.degruyterbrill.com/document/doi/10.1075/tlrp.23.18fre/html); [Benjamins ch.18](https://benjamins.com/catalog/tlrp.23.18fre)
- Freixa(2005, *Meta*)는 전문가가 자기 글의 변이를 해석하는 면담을 통해 원인 유형을 객관화하는 방법을 제안했다. — [Érudit Meta 2005 50(4)](https://releve.erudit.org/en/journals/meta/2005-v50-n4-meta1024/019917ar)
- 스페인어 비판 논문 「Otra vez sobre las causas de la variación denominativa」는 "인지적 원인" 을 독립 범주로 두는 데 이의를 제기한다. — [Érudit Meta 2011 56(2)](https://releve.erudit.org/fr/revues/meta/2011-v56-n2-meta1821316/1006179ar.pdf)

**한국어 음역 변이의 자동 처리**
- 영어 차용어–원어 쌍을 자동 획득해 **기술 용어집의 철자 변이와 미등록어 문제**를 함께 다루는 통계적 식별 연구. — [ResearchGate 220746280](https://www.researchgate.net/publication/220746280_Statistical_Identification_of_English_Loanwords_in_Korean_Using_Automatically_Generated_Training_Data)
- 외래어/고유어 음절을 HMM 으로 태깅해 음역어를 추출, 정밀도/재현율 80/82. — [ResearchGate 220155775](https://www.researchgate.net/publication/220155775_A_Statistical_Model_for_Automatic_Extraction_of_Korean_Transliterated_Foreign_Words)
- 고빈도어를 고유어 시드, 모음 삽입 흔적이 있는 낱말을 외래어 시드로 삼아 문자 n-gram 분류기를 EM 으로 학습하는 비지도 차용어 식별. — [Language Resources and Evaluation, Springer 2015](https://link.springer.com/article/10.1007/s10579-015-9296-5)
- 일본어 말뭉치·사전을 매개로 한국어 말뭉치에서 외래어 용어 후보를 뽑는 방법(CompuTerm 2004). — [ACL Anthology W04-1809](https://aclanthology.org/W04-1809.pdf)

### Inferences
- 💭 Kim(2023)과 문금현(2024)을 함께 보면, **공식 대체어가 존재한다는 사실과 실제 사용 빈도는 따로 재야 한다.** ko-dev-terms 가 "권위 출처 행" 과 "사용 빈도 행" 을 분리해 나란히 보이는 설계와 맞는다.
- 💭 국내 정착도 측정은 대부분 설문(인지율·이해율)이거나 포털 검색 빈도라서 ② 재현 가능한 스냅숏이 없다. 고정된 커밋의 문서 말뭉치에서 "한글(English)" 패턴을 세는 기존 방식이 이 문헌들보다 재현성 면에서 앞선다.
- 💭 Freixa 의 "기능적·사회언어적(언어 접촉)" 원인은 메서드/메소드 같은 **음역 철자 변이**와 함수/펑션 같은 **음역 vs 번역 변이**를 구분해 셀 근거가 된다 — 두 종류를 한 칸에 섞지 않는 것이 좋다.
### Gaps
- "전문어의 용어 변이는 15~35%" 라는 추정(Daille 2005 인용)이 검색 요약에 나왔으나 원 출처 페이지를 특정하지 못했다 — 수치를 인용하지 말 것.
- **정보통신·소프트웨어 개발 용어에 한정한 말뭉치 기반 정착률 연구**를 찾지 못했다(국내 RISS/DBpia 원문 접근 불가).
- 이홍식(2007) 수용 실태조사 원문과 수치, 2021 정책효과조사의 정착률 수치, 2022 NIA 50개 순화어 목록 — 확인 못 함.
- 순수 고유어 조어(열쇠말 등)를 비판한 학술 논문은 찾지 못했다 — 커뮤니티 자료만 있다.
- Kim(2023)의 18개 쌍 목록과 말뭉치 이름 — 초록에 없다.

## Q6. 용어 관리 표준과 상태 필드 — ISO 704 · ISO 1087 · ISO 30042(TBX) · IATE · Microsoft TBX · 한국 자원

### Takeaway
국제 용어 관리 표준은 용어마다 **preferred / admitted / deprecated(+ obsolete, superseded)** 상태를 달 수 있게 하고, TBX 는 이것을 `administrativeStatus`(값 `preferredTerm-admn-sts` 등)와 `normativeAuthorization` 으로 실어 나른다. IATE 는 이 평가 표지와 별도로 1~4 별 신뢰도(reliability)를 둔다. 확인된 범위에서 **Microsoft TBX 로더는 정의·품사·용어만 읽고 상태 필드는 보이지 않으며**, 한국어 자원 가운데 TBX 식 상태 필드를 그대로 가진 것은 없다 — 대신 다듬은 말(대상어→다듬은 말), 외래어 용례(이표기·오표기), 우리말샘(참여자 제안/전문가 감수), 고시 전문용어(표준, 기존어 병용 허용)가 부분적으로 대응한다.

### Cited Findings
- **ISO 704:2000** 은 용어 형성 원칙(7.3.1)으로 투명성(transparency)·일관성(consistency)·적절성(appropriateness)·언어 경제성(linguistic economy)·파생성(derivability)·언어적 정확성(linguistic correctness)·**모국어 우선(preference for native language)** 을 든다. 2009년 3판과 2022년판이 뒤를 이었다. — [iTeh ISO 704:2000 목차](https://standards.iteh.ai/catalog/standards/iso/04ed99e1-8af4-4deb-bda8-85023f01405f/iso-704-2000); [ISO 704:2009 PDF (USP)](https://edisciplinas.usp.br/pluginfile.php/5662129/mod_resource/content/1/ISO704_2009_Terminology%20work%20-%20principles%20and%20methods.pdf)
- 간결성 요구는 정확성 요구와 자주 충돌한다는 해설(2차 자료). — [lexilogia.gr](https://lexilogia.gr/threads/%CE%91%CF%81%CF%87%CE%AD%CF%82-%CF%83%CF%87%CE%B7%CE%BC%CE%B1%CF%84%CE%B9%CF%83%CE%BC%CE%BF%CF%8D-%CF%84%CF%89%CE%BD-%CF%8C%CF%81%CF%89%CE%BD.456)
- **ISO 1087:2019** 2판(2019-09)이 ISO 1087-1:2000 을 대체했고 항목에 preferred term(s)·admitted terms 를 둔다. 정확한 정의 문구는 확보하지 못했다. — [iTeh ISO 1087:2019](https://standards.iteh.ai/catalog/standards/iso/3be3cd08-943b-4d38-898d-e5e7ce36141e/iso-1087-2019); [ISO 1087:2019 샘플 PDF](https://cdn.standards.iteh.ai/samples/62330/aa6fcc8f52e34cf39acee86fa098fc22/ISO-1087-2019.pdf)
- DIN 정의: preferred term = 우선해서 써야 할 용어, admitted term = 우선 용어에 덧붙여 낮은 우선순위로 쓸 수 있는 용어, deprecated term = 존재하지만 쓰지 말아야 할 용어. — [DIN-TERMinology 데이터 범주](https://din.de/en/services/din-term/datenkategorien)
- NISO JATS `term-status`: admitted 는 우선 용어 요건은 못 갖추었으나 비권장도 아닌 용어(흔히 쓰이기 때문일 수 있음), deprecated 는 우선 용어로 대체된 용어. obsolete·superseded 는 deprecated 의 하위. — [JATS 1.3 term-status](https://jats.nlm.nih.gov/publishing/tag-library/1.3/attribute/term-status.html)
- ISO 10241 의 수용성 척도(acceptability)는 preferred·admitted·deprecated·obsolete·superseded 를 포함한다(2010 메일링 리스트, 2차). — [W3C public-esw-thes 2010-06](https://lists.w3.org/Archives/Public/public-esw-thes/2010Jun/0015.html)
- **ISO 30042 (TBX):** 2008년판은 2019년판으로 개정됐고, 2026년 5월 기준 CD(ISO/CD 30042) 가 study 단계라는 기록이 있다. 2008년판 Annex G 가 TBX-Basic 을 다룬다. — [ISO 30042:2019 (iTeh)](https://standards.iteh.ai/catalog/standards/iso/a45e92fb-de7f-435f-bad9-ef4e753d31e4/iso-30042-2019); [dps.gov.al ISO proj 90295](https://dps.gov.al/en/project/show/iso:proj:90295); [BS ISO 30042:2008](https://infostore.saiglobal.com/en-us/Standards/BS-ISO-30042-2008-1132988/)
- ISO 12620 "administrative status" 데이터 범주의 허용값에 preferred·admitted·deprecated·superseded term admin-sts 가 있다(2010 W3C 첨부, 2차). — [W3C termAdminStatus.html](https://lists.w3.org/Archives/Public/public-esw-thes/2010Jun/att-0015/termAdminStatus.html)
- translate5 구현: 거부된 용어의 "Usage status"(TBX 의 `administrativeStatus`)를 `deprecatedTerm-admn-sts` 로 바꾸고, 어떤 TBX 방언에서는 `normativeAuthorization` 이 같은 기능을 하므로 둘을 동기화한다. — [translate5 Jira TRANSLATE-3434](https://jira.translate5.net/browse/TRANSLATE-3434)
- WorldServer: admitted = 우선 용어의 허용 동의어(ISO 12620 이름 admitted term), superseded = 더 이상 우선·허용이 아니어서 쓰지 말아야 할 용어. — [WorldServer 용어 DB 상태 아이콘](https://worldserver.mattel.com/ws-legacy/help/en/ws/source/GUID-DBF558E4-D0CA-436E-B59D-9AB34FA3813A.html)
- **IATE:** 신뢰도 1~4 별 — ★ 미검증, ★★ 최소(비용어학자 입력 시 자동), ★★★ Reliable, ★★★★ Very reliable(용어학자 평가 후 수동). 데이터베이스 병합 때 많은 항목에 ★★★ 가 자동 부여돼 실제 평가를 반영하지 않을 수 있다. 평가 표지 Preferred / Admitted(기본값) / Deprecated(널리 쓰이나 EU 문서에 쓰지 말 것, 검색되도록 보존) / Obsolete. — [IATE online help 5325](https://online-help.iate.europa.eu/?p=5325); [IATE 용어 수준 기타 필드](https://online-help.iate.europa.eu/entry-management/entry-structure-editors/term-level/other-fields-tl/)
- **충돌:** 2023 datos.gob.es 글은 신뢰도를 untested/minimal/reliable/very reliable, 평가를 preferable/admissible/discarded/obsolete/proposed 로 적어 공식 도움말과 이름이 다르다. — [datos.gob.es 2023-11-08](https://datos.gob.es/en/blog/discover-iate-european-unions-inter-institutional-terminology-bas)
- **Microsoft Terminology Collection:** Hugging Face 로더는 `descrip`(정의)·`termNote`(품사)·`term`(대상 용어)을 읽고, Microsoft Language Portal Materials License 와 Terms of Use 를 가리킨다(제3자 코드). 포털은 2023-06-30 내려갔고 그때까지 내려받을 수 있었으며 이후 갱신이 없다고 공지됐다. TBX 는 Microsoft Download Center 에서 받는다는 Microsoft 일본 페이지가 있다. — [huggingface ms_terms.py](https://huggingface.co/datasets/microsoft/ms_terms/blob/refs%2Fpr%2F2/ms_terms.py); [proz.com 포럼](https://nor.proz.com/forum/internet_for_translators/337918-microsoft_language_portal_no_longer_available.html); [Microsoft Terminology (ja-jp)](https://www.microsoft.com/ja-jp/language/Terminology)
- **한국 자원의 상태 대응물:** 다듬은 말 항목은 순화 대상어·순화어·원어·참고 사항(순화 이력) — [국립국어원 답변](https://korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=216&qna_seq=261071); 외래어 용례 API 는 관련 표기(이표기·오표기) — [kornorms Open API](https://korean.go.kr/kornorms/main/openAPI.do); 우리말샘은 참여자 제안/전문가 감수 — [bartoc.org 우리말샘](https://bartoc.org/en/node/20607); 고시 전문용어는 표준이되 기존 용어 병용·병기 허용(2013 행정 312개) — [문화체육관광부 보도자료](https://www.mcst.go.kr/site/s_notice/press/pressView.jsp?pSeq=12589); TTA 는 심의를 거쳐 "표준용어" 로 결정 — [TTA 공지 35](http://word.tta.or.kr/noticeView.do?public_no=35).

### Inferences
- 💭 ko-dev-terms 의 증거 행에 상태 칸을 둔다면 TBX 의 `administrativeStatus` 값 집합(preferred / admitted / deprecated / superseded)을 **원천 표지를 그대로 옮긴 원문 값과 별도로** 두는 것이 안전하다. 한국 자원의 표지(다듬을 말·오표기·전문가 감수·표준용어)는 TBX 값과 1:1 로 대응하지 않는다 — 예: "다듬을 말" 은 국립국어원 기준 비권장이지만 IATE 의 deprecated 처럼 "널리 쓰이나 쓰지 말 것" 인지, 단지 "쉬운 말이 따로 있음" 인지는 사전이 말하지 않는다.
- 💭 우리말샘의 참여자 제안/전문가 감수 구분은 IATE 의 신뢰도 별과 같은 축(근거의 신뢰도)이지, preferred/deprecated 축(사용 권고)이 아니다. 두 축을 한 칸에 섞지 않는다.
- 💭 ISO 704 의 "모국어 우선" 원칙은 순화 정책의 근거가 되지만, 같은 표준의 "일관성·언어 경제성" 원칙과 Kim(2023)의 사용 실태는 그 반대 방향 근거가 될 수 있다 — ko-dev-terms 가 승자를 고르지 않는 이유와 맞물린다.
- 💭 Microsoft TBX 에 상태 필드가 있는지는 로더 코드로 보아 **없을 가능성이 높지만**, 로더가 읽지 않았을 뿐 파일에 있을 수도 있다. 실제 TBX 파일을 열어 `administrativeStatus`·`normativeAuthorization` 을 grep 해야 결론 난다.

**기준 판정표**

| 자원 | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| IATE | 예 | 미확인 | 미확인(이번 세션에서 bulk export 확인 안 함) | EU 행정 위주. 한국어 수록 미확인 | 미확인 | **있음 — 평가 표지 + 신뢰도 1~4** |
| Microsoft TBX | 예 | 2023-06-30 동결 — 파일 해시 | 예 | 소프트웨어 UI 어휘 | Language Portal Materials License(원문 미확인) | 로더 기준 없음(파일 미확인) |
| ISO 30042 TBX 형식 | — | — | — | — | — | `administrativeStatus` · `normativeAuthorization` 로 상태 운반 |

### Gaps
- ISO 1087:2019·ISO 30042:2019 의 정확한 정의 문구와 TBX-Basic 의 상태 요소 규정 — 표준 원문을 확보하지 못했다.
- Microsoft TBX 실제 파일에 상태 필드가 있는지, Language Portal Materials License 원문 — 확인 못 함.
- IATE 의 한국어 수록 여부(EU 공식 언어가 아니므로 없을 것으로 보이나 이번 세션에서 확인하지 않았다), bulk 내려받기 조건.
- 한국 자원 중 TBX 로 배포되는 것 — 찾지 못했다.
