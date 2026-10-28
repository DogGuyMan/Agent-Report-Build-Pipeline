# 지식 기반(knowledge base) · 웹 규모 말뭉치(web-scale corpus) · 개발자 커뮤니티 텍스트로 영어 개발 용어의 한국어 후보와 사용 근거를 찾는 방법

조사일 2026-10-28. 이 세션의 네트워크 정책 때문에 `wikidata.org` · `*.wikipedia.org` · `dumps.wikimedia.org` · `query.wikidata.org` · `huggingface.co` · `dbpedia.org` · `kli.korean.go.kr` · `ko-nlp.github.io` · `cdimage.debian.org` 는 열지 못했다(WebFetch 는 `getaddrinfo ENOTFOUND`, curl 은 프록시 403). 이 호스트들에 관한 주장은 **검색 결과 요약(snippet)에만 근거**하며, 그런 줄에는 "(검색 요약)" 이라고 적었다. GitHub 저장소는 `git clone --depth 1 --filter=blob:none` 으로 실제로 받아 이 세션에서 직접 셌다 — 그런 줄에는 "(직접 측정)" 과 커밋을 적었다. 클론은 측정 후 지웠다.

판정 기준(모든 출처에 적용): ①결정론적(deterministic, LLM·신경망 추론 없이 같은 입력+같은 스냅샷=같은 출력) ②스냅샷 고정(reproducible snapshot: 덤프 날짜·해시·커밋) ③오프라인·로컬 가능(크기·형식) ④소프트웨어 개발 어휘의 한국어 커버리지 ⑤라이선스(로컬 저장 · 파생 데이터 공개) ⑥알려진 실패 양상(failure mode).

## 질문 1 — 지식 기반: Wikidata · 위키백과 언어 간 링크(interlanguage link)와 넘겨주기(redirect) · Wiktionary · BabelNet · DBpedia (+ 우리말샘)

### Takeaway
라이선스와 스냅샷 측면에서 쓸 만한 것은 Wikidata(CC0, 주간 JSON 덤프)와 위키백과 SQL 테이블 덤프(langlinks · redirect · page)다. 둘 다 결정론적인 "영어 표제 → 한국어 표제 + 별칭/넘겨주기 변형" 후보 집합을 만들 수 있다. 다만 개발 용어의 한국어 표제·별칭이 실제로 얼마나 채워져 있는지는 이번 조사에서 수치로 확인하지 못했다(Wikidata·위키백과 접속 차단). BabelNet 은 비상업 라이선스이고 최신판은 일괄 덤프가 없다는 보고가 있어 "로컬 고정"이라는 전제와 맞지 않는다. 우리말샘(CC BY-SA 2.0 KR)은 국가 기관이 운영하는 개방형 사전이고 전문용어가 들어 있어, 지식 기반 갈래에서 빠뜨리면 안 되는 후보다.

### Cited Findings
**Wikidata**
- Wikidata 의 main · Property · Lexeme · EntitySchema 이름공간의 구조화 데이터는 전부 CC0 다. Data access 문서는 이를 "퍼블릭 도메인"이라고 쉽게 풀어 쓴다 (검색 요약) — [Wikidata:Data access](https://www.wikidata.org/wiki/Wikidata:Data_access)
- 권장 형식은 JSON 덤프다. 모든 엔티티를 담은 배열 하나이고, `dumps.wikimedia.org/wikidatawiki/entities/` 아래에 있으며, ID 순으로 정렬돼 있지 않고 매주 만들어진다 (2022년 보관본, 검색 요약) — [Wikidata:Database download (Wayback 2022-03-22)](https://webcf.waybackmachine.org/web/20220322162328/https://www.wikidata.org/wiki/Special:MyLanguage/Wikidata:Database_download)
- 렉심(Lexeme) 엔티티에는 label · description · alias · sitelink 가 없다. 표제어와 형태(form)·의미(sense) 구조만 있다 — [WikibaseLexeme JSON 문서](https://doc.wikimedia.org/WikibaseLexeme/master/php/md_docs_2topics_2json.html)
- 렉심만 따로 담은 덤프(`wikidata-YYYYMMDD-lexemes.json.bz2`)를 요청한 티켓이 있다. 구현됐는지는 검색 결과로 확인되지 않았다 — [Phabricator T220883](https://phabricator.wikimedia.org/T220883)
- 제3자가 만든 Hugging Face 판은 2024-09-18 덤프에서 **위키백과 문서와 연결된 엔티티만** 추린 부분집합이고 CC0 다 (검색 요약) — [philippesaade/wikidata](https://huggingface.co/datasets/philippesaade/wikidata)
- 2025-05-09 에 Wikidata Query Service(WDQS)가 둘로 나뉘었다. 학술 데이터는 별도 서비스로 옮겨졌다 — [Meta: WikiCite/WDQS graph split](https://meta.wikimedia.org/wiki/WikiCite/WDQS_graph_split)
- WDQS 의 Blazegraph 엔진은 60초 제한시간(timeout)이 있어 복잡한 질의에서 결과가 불완전할 수 있다. 이 수치는 출처 하나뿐이다 (검색 요약) — [CEUR-WS Vol-4064 PD-paper3](https://ceur-ws.org/Vol-4064/PD-paper3.pdf)
- 다국어 지식 그래프의 꼬리 엔티티(tail entity)는 일본어·중국어 이름 커버리지가 15% 미만이라고 보고됐다. 원인은 영어 사용 편집자 쏠림이다. 한국어 수치는 없다 (검색 요약) — [arXiv 2311.15781](https://arxiv.org/pdf/2311.15781)
- Wikidata 렉심 커버리지 2024 순위(2023년 말 기준)는 말뭉치 커버리지가 2/3 를 넘는 언어만 싣는다. 영어가 93.1% 로 1위이고, 검색 요약에 보인 부분에는 한국어가 없다 — [simia.net 2024](https://simia.net/wiki/Languages_with_the_best_lexicographic_data_coverage_in_Wikidata_2024)
- "한국어 label 이 있는 Wikidata 항목 수"의 현재 값은 찾지 못했다. 2021년 분석 PDF 에는 영어 label 항목 수(79,778,129)만 보인다 (검색 요약) — [WikidataAnalysis LabelsId 2021](https://upload.wikimedia.org/wikipedia/labs/archive/4/45/20210810160050%21WikidataAnalysis_LabelsId.pdf)

**위키백과 언어 간 링크 · 넘겨주기**
- Wikimedia 덤프는 위키마다 SQL 테이블을 따로 낸다. `langlinks`(다른 프로젝트로 나가는 링크)와 `page_props` 가 그 예이고, 파일 이름 꼴은 `<위키이름>-YYYYMMDD-langlinks.sql.gz` 다 (검색 요약) — [Meta: Data dumps/What's available for download](https://meta.wikimedia.org/wiki/Data_dumps/What%27s_available_for_download)
- 덤프 텍스트의 라이선스는 GFDL 과 CC BY-SA 4.0 이다(미러에 실린 legal.html 기준, 검색 요약) — [Wikimedia dumps legal (Debian 미러)](https://cdimage.debian.org/mirror/wikimedia.org/dumps/legal.html). 옛 사본은 CC BY-SA 3.0 이라고 적고 있다 — [gwern 사본](https://www.gwern.net/wiki/Wikipedia:DD)
- Erdmann 외(2008)는 위키백과의 언어 간 링크, 넘겨주기 문서, 링크 앵커 텍스트(anchor text)를 써서 이중언어 용어 사전을 만들었다. 문서 하나에는 대개 언어 간 링크가 최대 1개라서 링크만 쓰면 커버리지가 낮다. 넘겨주기와 앵커 텍스트를 더하면 결과가 크게 나아지고, 병렬 말뭉치(parallel corpus) 방식보다 낫다고 보고했다 (초록 수준, 검색 요약) — [Erdmann 외, DASFAA 2008, LNCS 4947 pp.580–587 (AMiner)](https://aminer.org/pub/53e9b484b7602d9703f8b48d/an-approach-for-extracting-bilingual-terminology-from-wikipedia); [IPSJ Journal 49(7) 2468–2479](https://ipsj.ixsq.nii.ac.jp/record/9505/files/IPSJ-JNL4907020.pdf)
- 이 방법의 두 전제는 이렇게 요약된다. "언어 간 링크로 이어진 문서의 제목은 서로의 번역이다", "넘겨주기 문서의 제목은 대상 문서 제목의 동의어다" — [Ivanova, BUCC 2012](https://aclanthology.org/www.mt-archive.info/BUCC-2012-Ivanova.pdf)
- 한국어 위키백과 문서 수는 767,370 개로 표시돼 있으나 측정 날짜가 적혀 있지 않다 (검색 요약) — [Korean Wikipedia (en.wikipedia)](https://en.wikipedia.org/wiki/Korean_Wikipedia)
- DBpedia 의 `Side_effect_(computer_science)` 페이지에 한국어 대응 문서가 있다고 나온다. 한국어 제목 자체는 검색 요약에 보이지 않았다 — [DBpedia: Side effect (computer science)](https://dbpedia.org/page/Side_effect_(computer_science))

**Wiktionary**
- Wiktextract 의 영어판 추출기는 표제어마다 "가능하면 모든 언어의 번역(translations)"을 뽑아 JSONL 로 낸다. 미리 추출한 파일은 kaikki.org 의 rawdata 페이지에 있다 (검색 요약) — [tatuylonen/wiktextract](https://github.com/tatuylonen/wiktextract); [PyPI wiktextract](https://pypi.org/project/wiktextract); [Ylonen, LREC 2022](https://preview.aclanthology.org/setup/2022.lrec-1.140)
- Wiktextract 저장소의 라이선스는 "other" 로 표시된다. kaikki.org 데이터 자체의 라이선스 문구는 확인하지 못했다 (검색 요약) — [awesome.ecosyste.ms: wiktextract](https://awesome.ecosyste.ms/projects/github.com%2Ftatuylonen%2Fwiktextract)

**BabelNet**
- BabelNet 은 자체 "BabelNet Non-Commercial" 라이선스를 정의하고, 가공판에 붙일 귀속 문구 예시로 v5.3 을 든다 — [BabelNet full license](https://babelnet.org/full-license)
- Java API 의 라이선스 열거형에는 CC BY-NC-SA 3.0 · CC BY-NC-SA 4.0 · BabelNet NonCommercial 이 함께 있다 — [BabelNet Javadoc 5.3 BabelLicense](https://www.babelnet.org/javadoc/5.3/it/uniroma1/lcl/babelnet/data/BabelLicense.html)
- 2.5 이후 판은 내려받을 수 없고 비상업 약정 아래 API 로만 쓸 수 있다는 사용자 글이 있다(공식 문서 아님, 날짜 오래됨) — [ConceptNet users 그룹](https://groups.google.com/g/conceptnet-users/c/Pegrq0JGEWA)

**DBpedia (한국어)**
- ko.dbpedia.org 의 라이선스와 현재 상태는 찾지 못했다. Hugging Face 의 `KETI-AIR/kor_dbpedia_14` 는 cc-by-sa-3.0 으로 표시돼 있지만 ko.dbpedia.org 와는 별개의 분류용 데이터셋이다 (검색 요약) — [KETI-AIR/kor_dbpedia_14](https://huggingface.co/datasets/KETI-AIR/kor_dbpedia_14/blob/main/README.md?code=true)

**우리말샘 (국립국어원 개방형 사전)**
- 우리말샘 콘텐츠는 따로 표시가 없으면 CC BY-SA 2.0 KR 이고, 상업적 이용을 포함해 쓸 수 있으며 출처 표시가 필요하다 (검색 요약) — [Urimalsaem (en.wikipedia)](https://en.wikipedia.org/wiki/Urimalsaem)
- 2016년 개통 당시 보도는 전문용어 약 35만 개가 들어 있다고 전했다(2016년 사실) — [뉴시스 2016-09-28](https://mobile.newsis.com/view/NISX20160928_0014415310); [파이낸셜뉴스 2016-09-28](https://www.fnnews.com/news/201609281036548794)

### Inferences
- **후보 집합을 결정론적으로 뽑는 경로(추론).** Wikidata 주간 JSON 덤프(파일 이름의 날짜와 sha1 로 고정)를 쓴다. 영어 label/alias 가 질의어와 같은 항목을 찾고, 그 항목의 `ko` label 과 `ko` aliases 를 후보로 낸다. 증거 행은 (Q-id, 덤프 날짜, 필드)다. 위키백과는 `enwiki-YYYYMMDD-langlinks.sql.gz` 로 영어 문서 → 한국어 제목을 얻고, `kowiki-…-redirect.sql.gz` + `page.sql.gz` 로 그 한국어 문서를 가리키는 넘겨주기 제목들을 모으면 철자 변형 집합이 된다(예상 예: 엣지/에지/간선/변 — **실제 넘겨주기 존재 여부는 위키백과 차단으로 확인하지 못했다**). 두 경로 모두 숫자는 "있다/없다"와 별칭 개수뿐이고 사용 빈도는 아니다.
- **동음이의 갈림이 가장 큰 실패 양상(추론).** "side effect" 는 의학 항목과 컴퓨터 과학 항목이 따로 있다. 영어 표제가 같은 항목이 여럿이면 하나를 고르는 규칙이 있어야 결정론이 유지된다. 예를 들어 영어 위키 sitelink 제목에 "(computer science)/(programming)" 이 붙은 항목만 받거나, P31/P279 경로가 정해 둔 상위 개념에 닿는 항목만 받는 식이다. 규칙 없이 사람이 고르면 재현할 수 없다.
- **문체 편향(추론).** 위키백과 표제는 백과사전·학술 문체를 따른다(그래프 이론 쪽은 학술 용어). 그래서 개발 현장의 음차(예: 사이드 이펙트)는 표제가 아니라 넘겨주기에만 있거나 아예 없을 수 있다. 이 갈래는 "공식·학술 후보"를 주는 쪽이고 "현장 사용"의 근거는 아니다.
- **넘겨주기의 잡음(추론).** 넘겨주기에는 오타, 옛 표기, 상위·하위 개념이 섞인다. 후보로는 내되 "넘겨주기에서 왔다"는 출처 표지를 증거 행에 남겨야 한다.
- **판정 요약(추론, 위 인용에 근거)**

| 출처 | ①결정론 | ②스냅샷 | ③로컬 | ④한국어 개발 어휘 | ⑤라이선스 | ⑥실패 양상 |
|---|---|---|---|---|---|---|
| Wikidata JSON 덤프 | 예 | 예(주간 덤프 날짜) | 가능하지만 전체 덤프가 큼(크기 수치 미확인). 필요한 필드만 한 번 추출해 보관 | 미확인. 꼬리 엔티티는 동아시아어 커버리지가 낮다는 보고 | CC0 — 저장·공개 자유 | 동음이의, 별칭이 비어 있음, 렉심에 label 이 없음 |
| WDQS(SPARQL) | 질의는 결정론적이나 **데이터가 살아 있다** | 아니오 | 아니오 | 위와 같음 | CC0 | 60초 제한시간, 2025 그래프 분할, 시점 고정 불가 |
| 위키백과 langlinks/redirect SQL 덤프 | 예 | 예(덤프 날짜) | 가능(테이블 단위로 받음) | 미확인 | CC BY-SA 4.0 + GFDL — 제목 목록 재공개 시 동일조건 고려 | 언어 간 링크는 문서당 1개뿐(Erdmann), 학술 문체 편향, 넘겨주기 잡음 |
| Wiktionary(wiktextract/kaikki) | 추출물 자체는 결정론적 | kaikki 파일 날짜로 가능 | 가능(JSONL) | 미확인. 일반어 중심일 것으로 추정 | Wiktionary 원문은 CC BY-SA 계열(확인 필요). kaikki 문구 미확인 | 개발 전문어의 번역 칸이 빈약할 가능성 |
| BabelNet | 색인은 결정론적 | 판 번호로 가능 | **최신판 일괄 덤프 없음 보고** | 미확인 | 비상업 — 파생 공개 제약 | 자동 매핑 오류 상속, 접근 약정 필요 |
| DBpedia(한국어) | 예 | 판 날짜로 가능 | 가능 | 미확인 | 미확인 | 위키백과의 2차 파생이라 위키백과 덤프와 중복 |
| 우리말샘 | 예 | 내려받은 날짜(공식 판 번호는 미확인) | 가능(형식 미확인) | 전문용어 약 35만(2016). 정보·통신 분야 수치 미확인 | CC BY-SA 2.0 KR — 저장·공개 가능, 동일조건 | 개방형이라 편집 품질이 고르지 않을 수 있음, 원어 칸 채움률 미확인 |

### Gaps
- Wikidata 에서 `ko` label/alias 를 가진 소프트웨어 공학 개념의 수, 그리고 예시 4개 용어(side effect · edge · single source of truth · postcondition)의 실제 `ko` label/alias — WDQS·엔티티 페이지 접속이 차단돼 확인하지 못했다.
- kowiki 넘겨주기 테이블 크기, 예시 용어의 넘겨주기 실례(엣지 → ?) — dumps.wikimedia.org · ko.wikipedia.org 차단.
- Wikidata 전체 JSON 덤프와 kowiki SQL 테이블의 현재 크기 — 원문 미접속.
- kaikki.org 데이터 라이선스 문구, BabelNet 5.x 의 오프라인 색인 제공 조건, ko.dbpedia.org 의 운영 상태와 라이선스 — 출처를 찾지 못했다.
- 우리말샘 내려받기 형식(XML/JSON 여부)과 "원어" 칸·"정보·통신" 분야 표지의 채움률 — opendict.korean.go.kr 을 열지 못했다.
- Wikipedia 기반 이중언어 사전 유도(bilingual lexicon induction)를 한국어–영어 개발 용어에 적용해 정밀도를 잰 논문 — 찾지 못했다.

## 질문 2 — 검색 엔진 적중 수(hit count)를 믿을 수 없는 이유와, 한국어에서 재현 가능한 웹 규모 대안

### Takeaway
적중 수는 추정치이고, 계산 방법이 공개되지 않으며, 다음 날 다시 돌리면 값이 크게 달라진다(Kilgarriff 2007). 재현 가능한 대안은 날짜·리비전이 고정된 Common Crawl 파생 말뭉치다. 한국어 규모는 이렇다: CC-100 54.2 GiB / 약 56억 토큰, mC4 약 260억 토큰, OSCAR 23.01 38–46 GB, FineWeb-2 kor_Hang 5,816만 문서 / 94.73 GB. 이 가운데 라이선스가 가장 분명한 것은 FineWeb-2(ODC-By)다. Google Books Ngram 에는 한국어가 없다. 모두의 말뭉치는 이용 약정 원문을 확인하지 못했고, 2022년 저작권 분쟁 이력이 있다.

### Cited Findings
**적중 수가 불안정하다는 근거**
- Kilgarriff, "Googleology is Bad Science", *Computational Linguistics* 33(1):147–151, 2007. 검색 엔진 적중 수는 추정치이고 엔진의 방법이 문서화돼 있지 않으므로 언어학 증거로 쓰는 것은 비과학적이라는 주장이다. 대안으로 투명하고 재현 가능한 웹 말뭉치를 제안한다 — [ACL Anthology J07-1010](https://preview.aclanthology.org/menus/J07-1010/); [dblp](https://dblp.org/rec/journals/coling/Kilgarriff07.html)
- 이 글에 인용된 작은 실험에서, 같은 질의를 다음 날 다시 돌리면 30건 중 9건이 10% 넘게, 6건이 두 배 이상 달랐다(2차 인용, 원문 미확인) — [Sketch Engine 블로그](https://www.sketchengine.eu/?p=5597); [ProZ 스레드](https://tha.proz.com/topic/266089)
- Nakov(2005)는 n-gram 적중 수의 불안정성을 잠재적 문제로 지적했다 — [Nakov, RANLP 2005](https://biotext.ischool.berkeley.edu/papers/nakov_ranlp2005.pdf)
- Sánchez · Martínez-Sanahuja · Batet(2018, *Information Systems* 73:50–60)은 여러 검색 엔진의 적중 수를 연구 도구 관점에서 정확성, 수학적 일관성(mathematical coherence), 시간적 일관성(temporal consistency)으로 평가했다. 본문 결과는 확인하지 못했다 — [UOC 기록](https://recerca.uoc.edu/documentos/655f4dafdfaaaa22360751a1?lang=ca); [dblp](https://dblp.uni-trier.de/rec/html/journals/is/SanchezMB18)
- Thelwall(2008)과 Uyar(2009)도 적중 수의 정확성을 연구했다(2차 언급) — [jdebp: Google result counts are a meaningless metric](https://www.jdebp.uk/FGA/google-result-counts-are-a-meaningless-metric.html)
- 2005년 Corpora-List 에는 Google 적중 수가 오락가락하다가 나중에 엔진이 값을 조정했다는 보고가 있다 — [Corpora-List 2005-03](https://listserv.linguistlist.org/pipermail/corpora/2005-March/005992.html)

**Common Crawl 파생 말뭉치 — 한국어 규모**
- **CC-100**: XLM-R 논문 Table 6 에서 한국어는 5,644M 토큰, 54.2 GiB 다 — [Conneau 외, ACL 2020, arXiv 1911.02116](https://arxiv.org/pdf/1911.02116). HF 판은 2018년 1–12월 Common Crawl 스냅샷을 CC-Net 의 URL·문단 색인으로 재구성했고, `ko` 를 14G 로 표시한다(측정 단위 차이로 보임) — [statmt/cc100](https://huggingface.co/datasets/statmt/cc100)
- **OSCAR 23.01**: 2022년 11/12월 Common Crawl 덤프 기반이다. 프로젝트 문서는 한국어 46G, 문서·단어 수는 "soon" 으로 표시한다 — [OSCAR 23.01 문서](https://oscar-project.github.io/documentation/versions/oscar-2301). HF 카드에는 약 1,515만 문서, 약 34.4억 단어, 38.1 GB 로 나와 크기가 서로 다르다. 접근하려면 약관 동의(gated)가 필요하다 (검색 요약) — [oscar-corpus/OSCAR-2301](https://huggingface.co/datasets/oscar-corpus/OSCAR-2301)
- **OSCAR 22.01**: 한국어 약 51.8 GB, 약 588만 문서, 약 38.5억 단어(메타데이터 포함 비압축 크기) (검색 요약) — [oscar-corpus/OSCAR-2201](https://huggingface.co/datasets/oscar-corpus/OSCAR-2201)
- **mC4**: mT5 논문 Table 6 에서 한국어는 약 260억 토큰, 약 1,600만 페이지, mT5 학습 표본에서 약 1.14% 다. PDF 텍스트 추출에서 읽은 값이라 원표로 다시 확인해야 한다 — [Xue 외, arXiv 2010.11934](https://arxiv.org/pdf/2010.11934)
- **FineWeb-2**: 옛 카드 커밋에서 `kor_Hang` 은 58,160,164 문서, 94.73 GB 이고 라이선스는 `odc-by` 다 (검색 요약) — [HuggingFaceFW/fineweb-2 README @cab26bb](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2/blob/cab26bb3cab1ca7c26bb13a48f80fc3d2def4620/README.md); 논문 [arXiv 2506.20920](https://arxiv.org/html/2506.20920v1). 이를 재필터한 한국어 말뭉치는 fineweb2_ko 를 46,470,574 문서로 센다(ODC-BY-1.0) — [seongchaeae/sage-pretrain-corpus](https://huggingface.co/datasets/seongchaeae/sage-pretrain-corpus)
- Common Crawl 의 언어 통계는 HTML 페이지마다 CLD2 로 판정한 **주 언어** 기준이고, 페이지 수 비율이다(토큰 비율이 아니다) — [Common Crawl 블로그: statistics on Hugging Face](https://commoncrawl.org/blog/common-crawl-statistics-now-available-on-hugging-face)
- 한국어 LLM 학습 데이터를 Naver · Daum · Tistory 세 사이트에서 모은 사례가 있다 — [Thunder-LLM, arXiv 2506.21595](https://arxiv.org/html/2506.21595v1)

**Google Books Ngram**
- 2020년 무렵 Ngram 말뭉치 언어는 영어, 중국어(간체), 프랑스어, 독일어, 히브리어, 이탈리아어, 러시아어, 스페인어와 영어 하위 말뭉치였다 — [Google Ngram Viewer (위키백과 사본)](https://static.hlt.bme.hu/semantics/external/pages/n-gram/en.wikipedia.org/wiki/Google_Ngram_Viewer.html)
- 2024년 7월 개정에서 2009 · 2012 · 2019 데이터셋은 선택 목록에서 빠졌지만 `:eng_2019` 같은 연산자로는 여전히 부를 수 있다 — [Ngram Viewer release notes](https://books.google.com/ngrams/about)

**국립국어원 모두의 말뭉치**
- Korpora 패키지가 다루는 모두의 말뭉치는 신문 · 메신저 · 형태 분석 · 개체명 · 구어 · 웹 · 문어이고, 출처는 corpus.korean.go.kr 이다. Korpora 의 CC-BY 는 패키지에만 적용되며 "말뭉치의 라이선스는 말뭉치별로 별도 적용"된다 — [ko-nlp/Korpora README](https://github.com/ko-nlp/korpora)
- 2022년 문어 말뭉치 일부에서 저작권 문제가 불거져 서비스가 일시 중단됐고, 전수 검토 후 재공개하기로 했다. 웅진 관련 소송은 1·2심 모두 저작권자가 이겼고 공정이용(fair use)이 인정되지 않았다 — [비즈한국](https://bizhankook.com/articles/woongjin-loses-ai-copyright-lawsuit.html); [서울신문 2022-08-26](https://m.seoul.co.kr/news/2022/08/26/20220826500076)

### Inferences
- **적중 수의 대체물(추론).** 고정된 HF 리비전(커밋 해시)의 FineWeb-2 `kor_Hang` 샤드(shard)들에서 후보 문자열을 정확히 일치(exact match)로 세면 ①②가 성립한다. 증거 행은 (데이터셋@리비전, 샤드 파일, 일치 수)다. 다만 94.73 GB 는 로컬 보관이 "가능하지만 무겁다". 한 번 훑어 후보 n-gram 빈도표만 남기는 방식이 현실적이다.
- **정렬(alignment)이 없다는 근본 한계(추론).** 웹 말뭉치에서 "부작용" 을 세도 그것이 "side effect" 의 번역인지 의학 용어인지 알 수 없다. 그래서 웹 말뭉치에서도 이미 택한 "한글(English)" 괄호 패턴을 세는 것이 정렬을 대신하는 유일하게 결정론적인 방법이다. 개발 문서 저장소에서 이 패턴이 실제로 나온다는 것은 질문 3 의 측정이 보여 준다.
- **도메인 희석(추론).** 일반 웹에서 개발 텍스트는 작은 부분이다. 그래서 일반 웹 빈도는 "일반 독자에게 익숙한 표기" 쪽으로 기운다. 증거 행에 말뭉치 성격(일반 웹 / 개발 문서)을 꼭 적어야 비교가 왜곡되지 않는다.
- **띄어쓰기 변형(추론).** 한국어는 "부수 효과/부수효과", "사후 조건/사후조건" 처럼 띄어쓰기가 갈린다. 세기 전에 공백을 정규화하는 규칙을 고정해야 결정론적인 비교가 된다.
- **판정 요약(추론)**

| 출처 | ①결정론 | ②스냅샷 | ③로컬 | ④한국어 규모 | ⑤라이선스 | ⑥실패 양상 |
|---|---|---|---|---|---|---|
| 검색 엔진 적중 수 | 아니오 | 아니오 | 아니오 | — | 서비스 약관 | 추정치, 날마다 변동(Kilgarriff) — **이미 배제됨** |
| CC-100 | 예 | 예(2018 스냅샷 고정판) | 54.2 GiB | 56억 토큰 | 재배포판의 이용 조건은 미확인(Common Crawl 파생) | 2018 년에 멈춤, 문단 단위 |
| OSCAR 23.01 | 예 | 예(판 번호) | 38–46 GB | 34억 단어 | gated, 약관 동의 필요(조건 미확인) | 크기 표기 불일치 |
| mC4 | 예 | 예 | 큼 | 260억 토큰 | 미확인(AllenAI 호스팅) | 언어 판정 오류, 중복 |
| FineWeb-2 kor_Hang | 예 | 예(HF 커밋) | 94.73 GB | 5,816만 문서 | ODC-By — 저장·파생 공개 가능(귀속), 원문 저작권은 별개 | 일반 웹 희석, 중복 제거 정책에 따라 값이 달라짐 |
| Google Books Ngram | 예 | 예 | 예 | **한국어 없음** | — | 해당 없음 |
| 모두의 말뭉치 | 예 | 신청 시점 판 | 가능 | 웹·문어 등 | 약정 원문 미확인, 2022 저작권 분쟁 이력 | 파생 데이터 공개 가능 여부 불명 |

### Gaps
- 모두의 말뭉치 이용 약정 원문(재배포, 제3자 제공, 파생물 공개, 상업 이용) — kli.korean.go.kr · corpus.korean.go.kr 을 열지 못했고 검색 결과에도 조항이 없다.
- FineWeb-2 현재 카드의 kor_Hang 토큰 수, OSCAR 23.01 한국어 수치 불일치(38.1 GB 대 46G)의 원인 — huggingface.co 차단.
- Common Crawl 최근 크롤에서 한국어 페이지 비율 — cc-crawl-statistics 표를 열지 못했다.
- 일반 웹 말뭉치 안에서 개발 텍스트 비율을 잰 연구 — 찾지 못했다.
- Kilgarriff 2007 본문의 실험 수치(9/30, 6/30)는 2차 인용으로만 확인했다.

## 질문 3 — 고정하고 셀 수 있는 한국어 개발자 커뮤니티·문서 텍스트

### Takeaway
GitHub 의 공식 문서 한국어 번역 저장소는 커밋으로 고정되고, 크기가 MB 단위이며, 대부분 CC BY 4.0 / MIT / Apache-2.0 이다. 그래서 여섯 기준을 가장 잘 만족하는 "현장 사용" 근거다. 직접 세어 보니 같은 "side effect" 라도 프로젝트마다 우세한 번역이 달랐다. ko.react.dev 는 사이드 이펙트 46 · 부수 효과 32, Vue 는 부수 효과 47 · 사이드 이펙트 9, ko.javascript.info 는 부작용 21 · 부수 효과 3 이다. "승자를 고르지 않고 증거만 나열한다"는 설계가 실제 데이터와 맞는다. 한편 블로그(velog/Tistory)와 OKKY 는 고정 가능한 공개 데이터셋을 찾지 못했다. MicrosoftDocs 의 ko-kr 저장소들은 2026-10-28 현재 익명 git 으로 접근되지 않는다.

### Cited Findings
**직접 측정한 저장소 (2026-10-28, `git clone --depth 1`, 확장자 .md/.mdx/.asc/.jade 만, 한글 줄 = `[가-힣]` 을 포함한 줄)**

| 저장소@커밋 (커밋 날짜) | 라이선스(저장소 파일) | 파일 / 줄 / 한글 줄 | "한글(English)" 괄호 출현 / 고유 영어 |
|---|---|---|---|
| [reactjs/ko.react.dev@89f79e9](https://github.com/reactjs/ko.react.dev/tree/89f79e9e971e9ad424ea5ebabdf8d5fa66c87375) (2026-10-01), `src/content` | `LICENSE-DOCS.md` = CC BY 4.0 | 229 / 125,104 / 13,568 | 160 / 119 |
| [vuejs-translations/docs-ko@6e646ac](https://github.com/vuejs-translations/docs-ko/tree/6e646acb5687510feda533281faa546b26ea243c) (2026-08-21), `src` | 이미지 제외 CC BY 4.0 | 119 / 28,975 / 6,501 | 813 / 133 |
| [rust-kr/doc.rust-kr.org@cbbea2c](https://github.com/rust-kr/doc.rust-kr.org/tree/cbbea2ca830cb0c090651111b3a18f5d5beabace) (2026-06-22), `src` | Apache-2.0 또는 MIT | 105 / 23,161 / 14,078 | 448 / 352 |
| [javascript-tutorial/ko.javascript.info@2489814](https://github.com/javascript-tutorial/ko.javascript.info/tree/2489814d15d09791bf6edfe00774ce0171e3bd1e) (2026-08-06) | "basically CC-BY-NC, revocable and exclusive" | 715 / 58,193 / 14,391 | 750 / 607 |
| [typescript-kr/typescript-kr.github.io@3fad5f8](https://github.com/typescript-kr/typescript-kr.github.io/tree/3fad5f8dab80e88a9190aae8c3256ce0b9bc7869) (2021-10-13), `pages` | MIT | 84 / 18,879 / 5,323 | 594 / 463 |
| [microsoft/TypeScript-Website-Localizations@40b00e0](https://github.com/microsoft/TypeScript-Website-Localizations/tree/40b00e0a2434315e760cff02d0739533e7ff0e8e) (2026-10-07), `docs/documentation/ko` | 문서 CC BY 4.0, 코드 MIT | 62 / 4,223 / 1,057 | 91 / 89 |
| [progit/progit2-ko@f50647d](https://github.com/progit/progit2-ko/tree/f50647da032bf210ef91802290d60d05da1a9416) (2025-03-05) | CC BY-NC-SA 3.0 | 114 / 32,438 / 6,774 | 82 / 70 |

- 예시 용어 원시 빈도(직접 측정, 대소문자 무시, 정규식 `부수 ?효과` 등):
  - **side effect** — ko.react.dev: 사이드 이펙트 46 · 부수 효과 32 · 부작용 12 · 영어 그대로 "side effect" 3. Vue: 부수 효과 47 · 사이드 이펙트 9, 그리고 "부수 효과(side effects)" 형태가 있다(`src/tutorial/src/step-10/description.md:3`). ko.javascript.info: 부작용 21 · 부수 효과 3. Rust 책: 부작용 1. TypeScript-Website-Localizations ko: 부수 효과 1. angular-ko(2017): 부작용 12 — 각 저장소 링크는 위 표
  - **edge** — 간선은 모든 저장소에서 0. 엣지/에지가 나오지만 대부분 "에지 케이스(edge case)" 맥락이다(ko.javascript.info "에지 케이스(edge case)" 2회). ko.react.dev 엣지 10 · Vue 에지 4 · 엣지 1 · Rust 에지 3
  - **single source of truth** — Vue: "진실의 원천" 3회(`src/guide/scaling-up/state-management.md:55,149`, `src/guide/essentials/forms.md:53`). ko.react.dev: 영어 그대로 "source of truth" 1회. 나머지 0
  - **postcondition** — 사후 조건 · 후조건 · `(postcondition)` 이 측정한 7개 저장소 모두에서 0
- 괄호 패턴을 정규식으로 뽑으면 한국어 쪽 경계가 모호하다. 앞말이 따라붙는 것이 실제로 나왔다(예: "할 불변성 (invariant)", "없는 불변성 (invariant)") (직접 측정, 위 저장소들)
- 지금의 microsoft/TypeScript-Website(커밋 `70d14cd`, 2026-10-27)의 `packages/documentation/copy/` 에는 `en` 만 있다. 한국어 핸드북은 TypeScript-Website-Localizations 로 옮겨져 있다(직접 측정) — [microsoft/TypeScript-Website](https://github.com/microsoft/TypeScript-Website); [microsoft/TypeScript-Website-Localizations](https://github.com/microsoft/TypeScript-Website-Localizations)
- 낡거나 비어 있는 저장소: [angular/angular-ko@6048a5b](https://github.com/angular/angular-ko/tree/6048a5b39a3afb57047f847f37c986e4c8275616) 은 마지막 커밋이 2017-06-23 이다. [golang-kr/golang-doc@113791b](https://github.com/golang-kr/golang-doc/tree/113791b64bdbdbcb51d59ef813429e5cf7e6cf6d)(2017-02-07)는 README 하나뿐이고, 번역은 GitHub 위키에 있다고 적혀 있다(직접 측정)
- `pytorch-korea/PyTorch-tutorials-kr` · `nextjs-ko/nextjs-docs-ko` · `kotlin-korea/kotlinlang-ko` · `spring-kr/spring-docs` 는 익명 `git ls-remote` 에서 자격 증명을 요구했다. 저장소 이름을 추측한 것이라 없는 저장소일 수 있다(직접 측정)
- `MicrosoftDocs/azure-docs.ko-kr` · `visualstudio-docs.ko-kr` · `cpp-docs.ko-kr` · `dotnet-docs.ko-kr` · `sql-docs.ko-kr` 도 2026-10-28 익명 `git ls-remote` 에서 자격 증명을 요구했다(직접 측정). 2020년 12월 보관본에는 `powerbi-docs.ko-kr` 같은 현지화 저장소가 공개돼 있었다 — [MicrosoftDocs (Wayback 2020-12-06)](https://webcf.waybackmachine.org/web/20201206060401/https://github.com/MicrosoftDocs). Microsoft Learn 이 문서 저장소 다수를 비공개로 돌린다고 발표했다는 보도가 있다(날짜는 검색 요약에 없음) — [office365itpros](https://office365itpros.com/tag/microsoft-learn/). 제3자 미러로 Gitee 의 `dotnet-api-docs.ko-kr` 가 있다 — [Gitee 미러](https://gitee.com/mirrors_dotnet/dotnet-api-docs.ko-kr)

**git 밖의 공식 한국어 문서**
- Unity 한국어 매뉴얼은 `docs.unity3d.com/kr/<버전>/` 경로로 판별로 제공된다. 이용 약관 페이지는 매뉴얼의 코드 스니펫만 Unity Companion License 로 허가한다고 적는다 (검색 요약) — [Unity Manual TermsOfUse (kr)](https://docs.unity3d.com/kr/current/Manual/TermsOfUse.html); [ManualVersions](https://docs.unity3d.com/kr//Manual/ManualVersions.html)
- Epic 개발자 문서에는 `?lang=ko` 한국어 페이지가 있다(예: Fortnite "side effect") — [dev.epicgames.com](https://dev.epicgames.com/documentation/fortnite/side-effect?lang=ko)

**블로그 · Q&A · GitHub 이슈**
- velog 나 개발 블로그만 모은 공개 데이터셋은 검색에서 나오지 않았다. 일반 한국어 웹 텍스트 데이터셋으로는 `HAERAE-HUB/KOREAN-WEBTEXT`, `OpenLab-NLP/corpus-ko-23m`(Apache-2.0)이 있다 (검색 요약) — [HAERAE-HUB/KOREAN-WEBTEXT](https://huggingface.co/datasets/HAERAE-HUB/KOREAN-WEBTEXT/blob/main/README.md); [OpenLab-NLP/corpus-ko-23m](https://huggingface.co/datasets/OpenLab-NLP/corpus-ko-23m/blob/main/README.md)
- "side effect" 를 영어 그대로 쓰거나, 프로그래밍의 Side Effect 는 일상어 "부작용" 처럼 부정적인 뜻만은 아니라고 설명하는 개발 블로그 글이 있다(질적 예시 2건, 빈도 아님) — [velog @jchy16 SideEffect](https://velog.io/@jchy16/SideEffect); [velog @kimhyesu-_-](https://velog.io/@kimhyesu-_-/wecode세션정리-useEffect)
- GH Archive 는 GitHub 공개 이벤트 전체를 BigQuery 공개 데이터셋으로 제공하고 매시간 갱신한다. 코드는 MIT, 웹사이트는 CC-BY-4.0 이지만 이벤트 데이터는 제3자 권리 대상일 수 있다고 적혀 있다 (검색 요약) — [gharchive.org](https://gharchive.org/); [gharchive.org 저장소 미러](https://github.com/stjordanis/gharchive.org)
- GH Archive 를 가공한 한 HF 데이터셋은 "GitHub 약관상 이슈·PR 본문과 댓글은 해당 저장소의 라이선스를 따른다"고 해석한다(제3자 해석) — [open-index/open-github](https://huggingface.co/datasets/open-index/open-github/blob/main/README.md)

### Inferences
- **문서 번역 저장소가 이 갈래의 중심(추론).** ①②③⑤가 모두 성립한다(커밋 해시, 수십 MB, CC BY 4.0/MIT/Apache). 이미 택한 Kubernetes/MDN/python-docs-ko 와 같은 방식(괄호 패턴 + 후보 문자열 원시 빈도)을 그대로 넓힐 수 있다. 측정한 7개 저장소만으로도 괄호 패턴이 3,000건 가까이(160+813+448+750+594+91+82=2,938) 나온다.
- **라이선스 주의(추론).** ko.javascript.info(CC-BY-NC, "revocable and exclusive", 저자 허락 권장)와 progit2-ko(CC BY-NC-SA 3.0)는 로컬 저장과 비상업 파생은 괜찮아 보이지만 상업 배포에는 걸린다. 빈도 수치 같은 사실 데이터만 공개하면 위험이 작다고 보지만 법률 판단은 아니다.
- **표본이 독립적이지 않다(추론).** 각 저장소는 번역 용어집으로 표기를 강제한다(ko.react.dev 는 textlint 로 검사, 질문 5). 그래서 저장소 안의 빈도는 "편집 정책"의 결과이고 독립적인 사용 표본이 아니다. 증거 행은 저장소 단위로 묶어 보여 주는 것이 맞다(합산하면 큰 저장소 하나가 지배한다).
- **원시 빈도의 함정(추론, 측정에 근거).** ①동음이의: "부작용" 은 일상어로도 쓰인다. ②영어 그대로 남김: "source of truth" 를 번역하지 않은 사례. ③미번역 비율: ko.react.dev `src/content` 는 한글 줄이 약 11% 다(코드 블록과 미번역 문서 포함). ④낡은 저장소: angular-ko 2017, typescript-kr 2021. ⑤괄호 패턴의 한국어 경계 모호성. 그래서 "괄호 안 영어 = 질의어"로 정렬된 행과, 정렬되지 않은 한국어 원시 빈도 행을 나눠 표시해야 한다.
- **희귀 용어는 0 이 나온다(추론).** postcondition 은 7개 저장소 어디에도 없었다. 커버리지는 프레임워크 사용자 문서 쪽으로 치우쳐 있고, 계약에 의한 설계(design by contract) 같은 공학 용어는 이 갈래로 근거를 얻기 어렵다. 0건이라는 사실도 증거 행으로 내야 한다.
- **git 밖 문서(추론).** Unity · Epic · Android 개발자 문서처럼 웹에만 있는 문서는 스냅샷을 고정할 수 없고 약관이 제한적이다. 수동 확인용 참고에 그치게 된다.
- **판정 요약(추론)**

| 출처 | ①결정론 | ②스냅샷 | ③로컬 | ④커버리지 | ⑤라이선스 | ⑥실패 양상 |
|---|---|---|---|---|---|---|
| 공식 문서 한국어 번역 저장소(react/vue/rust/TS/js.info 등) | 예 | 예(커밋) | 예(수~수십 MB) | 프레임워크 사용자 어휘에 강하고 공학 용어에 약함 | 대부분 CC BY 4.0/MIT/Apache, 일부 NC | 편집 정책 편향, 동음이의, 미번역, 낡음 |
| MicrosoftDocs ko-kr | — | — | — | — | 익명 접근 불가(2026-10-28) | 비공개로 바뀐 것으로 보임 |
| Unity/Epic 웹 문서 | 크롤 결과로는 가능 | 아니오 | 크롤 필요 | 게임 엔진 어휘 | 제한적(스니펫만 허가) | 시점 고정 불가 |
| 개발 블로그(velog/Tistory) | 크롤하면 가능 | 자체 크롤 시점만 | 크롤 필요 | 현장 표기에 가장 가깝다 | 글쓴이 저작권 — 공개 데이터셋 없음 | 품질 편차, 중복, 고정 불가 |
| GH Archive(이슈·댓글) | 예(BigQuery 질의) | 시간 단위 테이블로 가능 | BigQuery 비용 | 한국어 비율 미확인 | 이벤트 데이터 권리 불명확 | 영어·한국어 혼용, 봇 텍스트 |

### Gaps
- OKKY, 커리어리, 인프런 Q&A 같은 한국어 개발 Q&A 의 공개 덤프·약관 — 찾지 못했다.
- 한국어 Stack Overflow 류 데이터셋 — 찾지 못했다.
- Spring · Kotlin · Android · Go 공식 문서의 현재 한국어 번역 저장소 이름과 라이선스 — 확인하지 못했다(Go 는 2017년 이후 갱신이 없는 저장소만 확인).
- GH Archive 에서 한국어 이슈·README 비율 — BigQuery 를 돌리지 않았다.
- 측정한 빈도는 정규식 원시 빈도다. "부작용" 의 의학적 용례 비율 같은 정밀도는 재지 않았다.

## 질문 4 — 코드 말뭉치: 공개 코드의 한국어 주석과 식별자

### Takeaway
The Stack v2(Software Heritage 기반, gated, 일괄 다운로드에 SWH/INRIA 약정 필요)와 The Stack v3(2026년 7월 공개, GitHub 직접 크롤, ODC-BY, 학습 분할 약 15.9 TB)는 리비전을 고정할 수 있다. 하지만 TB 단위라 통째로 로컬에 둘 수 없다. 파일마다 원래 라이선스를 따라야 하고, 동의(consent)가 아니라 거부(opt-out) 방식이라는 논란이 있다. GitHub 코드 검색 API 는 살아 있는 색인이고 결과가 1,000건으로 잘려서 적중 수와 같은 문제를 가진다. 한국어 주석 비율을 잰 수치는 찾지 못했다.

### Cited Findings
- The Stack v2 는 HF 에서 gated 이고, 일괄 다운로드에는 Software Heritage 와 INRIA 와의 약정이 필요하다. 코드를 쓰려면 원래 라이선스(귀속 조항 포함)를 지켜야 하며, "Am I in The Stack?" 도구와 거부 절차가 있다 (검색 요약) — [bigcode/the-stack-v2](https://huggingface.co/datasets/bigcode/the-stack-v2)
- 라이선스가 없는 코드가 들어 있고 거부 절차로는 침해가 해소되지 않는다는 커뮤니티 주장이 있다(공식 입장 아님) — [the-stack-v2 discussion #12](https://huggingface.co/datasets/bigcode/the-stack-v2/discussions/12)
- The Stack v3 는 2026년 7월에 공개됐다. 학습 분할은 약 15.9 TB, 약 4.9조 토큰이고, 전체판은 HF Storage Bucket 으로 호스팅된다 — [HuggingFaceCode/stack-v3-train README](https://huggingface.co/datasets/HuggingFaceCode/stack-v3-train/blob/main/README.md); [DEV Community](https://dev.to/breachprotocol/hugging-face-ships-the-stack-v3-and-this-time-the-code-is-actually-in-the-box-2fo4)
- v3 는 Software Heritage 가 아니라 GitHub 에서 직접 크롤했다 — [DeepLearning.AI The Batch](https://www.deeplearning.ai/the-batch/fresh-data-for-coding-models-hugging-face-updated-the-stack-the-largest-crawl-of-public-github-repositories)
- v3 의 데이터셋 라이선스는 ODC-BY v1.0 이고 파일마다 원래 라이선스를 유지한다. 거부한 저장소는 패치 릴리스마다 제거된다. 2차 출처들 사이에 언어 수(713 대 770)와 저장소 수(1.73억 대 2.24억)가 엇갈린다 — [ai-tldr.dev](https://ai-tldr.dev/releases/huggingface-the-stack-v3/); [explainx.ai](https://explainx.ai/blog/hugging-face-the-stack-v3-5-trillion-tokens-july-2026)
- GitHub REST 검색 API 에서 코드 검색은 인증이 필요하고 분당 9회로 제한된다 — [GitHub Docs: REST search](https://docs.github.com/en/rest/search/search). 결과는 최대 1,000건(100건 × 10쪽)까지만 볼 수 있다 — [fulll github-code-search: API limits](https://fulll.github.io/github-code-search/reference/github-api-limits.html); [Sourcegraph: GitHub API oddities](https://docs-legacy.sourcegraph.com/dev/background-information/github-api-oddities)

### Inferences
- **결정론은 성립하지만 규모가 맞지 않다(추론).** 고정된 HF 리비전의 The Stack 에서 한글을 포함한 주석 줄만 걸러 한 번 훑으면 ①②가 성립한다. 남기는 것은 (리비전, 파일 경로/저장소, 일치 수)다. 하지만 원본이 TB 단위이고 gated 라서, 이 도구의 "로컬·오프라인" 전제와는 "선행 추출 1회 + 빈도표만 보관" 으로만 타협된다.
- **커버리지 추정(추론, 수치 근거 없음).** 식별자는 대개 영어로 쓰므로 한국어 근거는 주석과 문서 문자열(docstring)에 몰릴 것이다. 주석은 "부수효과 없음" 처럼 띄어쓰기가 자유롭고 약어가 많다. 문서 저장소보다 현장 표기에 가깝지만 잡음이 크다.
- **라이선스(추론).** 원문을 보관하면 파일마다 라이선스 의무가 따라온다. 빈도 수치만 공개하는 것은 위험이 낮아 보이지만, v2 의 동의 논란이 있으므로 "어느 저장소에서 왔는가"를 증거 행으로 공개하는 것(저장소 경로 노출)은 신중해야 한다.
- **GitHub 코드 검색은 배제(추론).** 살아 있는 색인, 1,000건 상한, 속도 제한 — Kilgarriff 가 적중 수에 대해 지적한 것과 같은 재현 불가 문제다.
- **판정 요약(추론)**

| 출처 | ①결정론 | ②스냅샷 | ③로컬 | ④한국어 커버리지 | ⑤라이선스 | ⑥실패 양상 |
|---|---|---|---|---|---|---|
| The Stack v2 | 예 | 예(HF 리비전) | 아니오(TB, SWH 약정) | 미확인 | 파일별 원 라이선스, gated | 거부 방식 논란, 무라이선스 코드 |
| The Stack v3 | 예 | 예(패치 릴리스) | 아니오(약 15.9 TB 학습 분할) | 미확인 | ODC-BY + 파일별 원 라이선스 | 거부 저장소 제거로 릴리스마다 값이 바뀜 |
| GitHub 코드 검색 API | 아니오 | 아니오 | 아니오 | — | GitHub 약관 | 1,000건 상한, 분당 9회, 색인이 바뀜 |

### Gaps
- The Stack v2/v3 에서 한글을 포함한 주석의 비율이나 파일 수 — 찾지 못했다.
- Software Heritage 이용 약관 원문, v3 "full" 버킷의 접근 조건 — 원문 미확인(huggingface.co 차단).
- 한국어 주석에서 개발 용어 표기를 계량한 선행 연구 — 찾지 못했다.

## 질문 5 — 출판사 · 커뮤니티 번역 용어집 (대역표)

### Takeaway
기계가 읽을 수 있는 커뮤니티 용어집 가운데 가장 구조가 좋은 것은 ko.react.dev 의 `textlint/data/rules/translateGlossary.js` 다. 68개 항목이 있고, 항목마다 금지 표기 정규식(sources), 채택 번역(target), 논의 이슈 번호(discussions)가 붙어 있으며, CC BY 4.0 이다. 나머지는 마크다운 표, 글머리표 목록, 이슈 토론뿐인 형태로 기계 판독성이 떨어진다. 한빛 · 인사이트 · 제이펍 같은 IT 출판사의 번역 대역표는 공개된 기계 판독 자료를 찾지 못했다. GNOME 한국어 팀 용어집도 위치만 확인했다.

### Cited Findings
- **ko.react.dev** (직접 측정, [@89f79e9](https://github.com/reactjs/ko.react.dev/tree/89f79e9e971e9ad424ea5ebabdf8d5fa66c87375)): `textlint/data/rules/translateGlossary.js` 는 JS 모듈이다. `translated.react`(470행 앞)와 `translated.others` 두 묶음에 `target:` 항목이 68개 있다. 항목 꼴은 `{sources: [/\bComponent\b/, /컴퍼넌트/, /컴포넌츠/], target: '컴포넌트', meta: {term, discussions: [2], note}}` 이다. 즉 영어 정규식과 **틀린 한국어 변형 정규식**이 함께 있다. `wiki/translate-glossary.md` 는 이 파일에서 자동 생성된다("임의 수정을 금지"). 옛 용어집 `wiki/translate-glossary-legacy.md` 는 표 행이 81줄이다(머리줄·구분줄 포함). 이슈 템플릿 `.github/ISSUE_TEMPLATE/term.md` 는 용어 논의가 끝나면 이 JS 파일을 고치라고 요구한다. 예: Stateful → 유상태, Stateless → 무상태, Tutorial → 자습서, Attribute → 어트리뷰트, Example → 예시, Spec → 명세
- **Vue docs-ko** (직접 측정, [@6e646ac](https://github.com/vuejs-translations/docs-ko/tree/6e646acb5687510feda533281faa546b26ea243c)): `src/glossary/index.md` 는 Vue 개념을 설명하는 용어집(예: "비동기 컴포넌트")이고 영–한 대역표는 아니다
- **angular-ko** (직접 측정, [@6048a5b](https://github.com/angular/angular-ko/tree/6048a5b39a3afb57047f847f37c986e4c8275616), 2017): `ko-trans-guide.md`(163줄)는 `* property: 프로퍼티 (attribute는 속성으로 … 차이를 두고 있으니 …)` 같은 글머리표 목록이다. "언어, 프레임워크, 라이브러리, 전문용어는 영문 그대로 사용", "번역이 애매한 기술용어는 영어 그대로 한글로 표기" 같은 규칙 절이 있다
- **progit2-ko** (직접 측정, [@f50647d](https://github.com/progit/progit2-ko/tree/f50647da032bf210ef91802290d60d05da1a9416)): `TRANSLATION_NOTES.asc` 는 "용어는 초판을(https://github.com/progit/progit/tree/master/ko) 기준으로 합니다" 라고 적은 지침 문서이고 대역표는 아니다. 저장소 라이선스는 CC BY-NC-SA 3.0 이다
- **rust-kr/translation** (직접 측정, [@c607197](https://github.com/rust-kr/translation/tree/c607197997f0802c018d2968275388f4c1d5f7bc), 2021-02-05): README 한 줄("번역 용어 등을 논의합니다.")뿐이고 용어 논의는 GitHub 이슈에 있다. Rust 책 한국어판의 `ci/dictionary.txt`(587줄)는 aspell 형식의 영어 맞춤법 사전이고 용어 대역표가 아니다([doc.rust-kr.org@cbbea2c](https://github.com/rust-kr/doc.rust-kr.org/tree/cbbea2ca830cb0c090651111b3a18f5d5beabace))
- **Kubernetes 한글화 가이드**에는 "한글화 과정에서 자주 등장하여 논의가 이루어진 용어"를 모은 용어집 절이 있다(이미 택한 출처, 참고만) — [kubernetes.io/ko 한글화 가이드](https://www.kubernetes.io/ko/docs/contribute/localization_ko/)
- **Koreabulary-LLM**: 프롬프트 엔지니어링 가이드 한국어 번역 기여자를 위한 용어집 사이트(AI 분야) — [11mLLM/Koreabulary-LLM](https://www.github.com/11mLLM/Koreabulary-LLM)
- **GNOME 한국어 번역팀**: 팀 페이지는 처음 참여하는 사람에게 `wiki.gnome.org/KoreanTranslation` 을 읽으라고 안내하고, GNOME 50(개발판) UI 번역률을 83% 로 보여 준다. 용어집 원문은 확인하지 못했다 (검색 요약) — [l10n.gnome.org/teams/ko](https://l10n.gnome.org/teams/ko)
- 2006년 메일링 리스트에는 GNOME 공통 용어집이 사실상 버려졌고 언어별 팀이 각자 용어집을 관리한다는 설명이 있다(2006년 사실) — [rosetta-users 2006-06](https://lists.ubuntu.com/archives/rosetta-users/2006-June/001622.html)
- IT 출판사(한빛미디어 · 인사이트 · 제이펍 등)의 번역 용어 대역표를 공개한 자료는 검색에서 나오지 않았다(결과는 무관한 위키독스 프로필뿐이었다) — [검색 결과 예: wikidocs 프로필](https://wikidocs.net/profile/info/comment/24318)

### Inferences
- **기계 판독성 순위(추론, 측정에 근거).** JS 모듈(ko.react.dev: 정규식 + 채택어 + 이슈 번호) > 자동 생성 마크다운 표 > 손으로 쓴 마크다운 표(Kubernetes, react legacy) > 글머리표 목록(angular-ko) > 이슈 토론만(rust-kr/translation, 이슈는 git 밖이라 고정 불가).
- **용어집은 "정책 근거"이지 "사용 근거"가 아니다(추론).** 용어집 항목은 한 팀의 결정이다. 같은 저장소 본문의 빈도는 그 결정이 강제된 결과다. 증거 행의 종류를 `glossary`(정책)와 `prose-count`(사용)로 나누어야 이중 계산을 피한다.
- **ko.react.dev 형식이 특히 쓸모 있는 이유(추론).** `sources` 정규식에 "피해야 할 한국어 변형"(예: 컴퍼넌트, 랜더링, 어플리케이션)이 들어 있다. 그래서 후보 집합에 "기각된 변형"까지 출처와 함께 실을 수 있다. `discussions` 의 이슈 번호는 왜 그렇게 정했는지를 가리키는 고정 ID 이지만, 이슈 본문 자체는 git 밖이라 스냅샷이 되지 않는다.
- **출판사 대역표(추론).** 공개된 기계 판독 자료가 없으므로 TTA 처럼 "수동 조회 전용"으로 분류하는 것이 맞다.
- **판정 요약(추론)**

| 출처 | ①결정론 | ②스냅샷 | ③로컬 | ④항목 수 | ⑤라이선스 | ⑥실패 양상 |
|---|---|---|---|---|---|---|
| ko.react.dev translateGlossary.js | 예 | 예(커밋) | 예 | 68 | CC BY 4.0 | React 어휘로 한정, 일반어(팁·예시·장)도 섞임 |
| Vue docs-ko glossary | — | — | — | 대역표 아님 | CC BY 4.0 | 개념 설명용 |
| angular-ko ko-trans-guide.md | 파싱 필요 | 예 | 예 | 글머리표(정확한 수 미측정) | LICENSE 파일은 있으나 종류 미확인 | 2017년에 멈춤, 음차 위주 정책 |
| progit2-ko 번역 노트 | — | 예 | 예 | 대역표 없음(초판 참조) | CC BY-NC-SA 3.0 | 용어가 초판 저장소에 흩어져 있음 |
| rust-kr/translation | 아니오(이슈) | 아니오 | 아니오 | 미측정 | — | git 밖 |
| GNOME 한국어 팀 | 미확인 | 미확인 | 미확인 | 미확인 | 미확인 | 위치만 확인 |
| IT 출판사 대역표 | — | — | — | 공개 자료 없음 | — | 수동 조회만 가능 |

### Gaps
- GNOME `wiki.gnome.org/KoreanTranslation` 의 용어집 형식과 항목 수, KDE · Ubuntu · Django · Debian 한국어 팀 용어집 — 열어 보지 못했다.
- KLDP 용어 번역 목록의 현존 여부와 형식 — 찾지 못했다.
- 한국정보과학회(KIISE) 용어집, KS X ISO/IEC 2382 한국어판 같은 학회·표준 용어집의 기계 판독 공개본 — 이번 범위에서 찾지 못했다.
- angular-ko 저장소 LICENSE 의 정확한 종류와 ko-trans-guide 의 정확한 항목 수 — 세지 않았다.
- 출판사 내부 대역표를 공개한 역자 블로그나 GitHub 저장소 — 검색 결과에 없었다.
