# 이중 언어·병렬 말뭉치로 영어 개발 용어의 한국어 표기 후보를 찾는 방법 (bilingual / parallel-corpus methods)

> 조사일 2026-10-28. 판정 기준 6종: ① 결정론(deterministic, LLM·신경망 추론 없이 같은 입력+같은 스냅샷=같은 출력) ② 스냅샷 고정(dump 날짜·해시·커밋) ③ 오프라인·로컬(크기·형식) ④ 개발 어휘 한국어 수록량 ⑤ 라이선스(로컬 보관 · 파생 데이터 공개) ⑥ 알려진 실패 양상·정밀도.
>
> **네트워크 제약 (이번 세션):** `aclanthology.org` · `opus.nlpl.eu` · `object.pouta.csc.fi` · `huggingface.co` · `arxiv.org` · `koreascience.or.kr` · `www.rcs.cic.ipn.mx` · `transvision.mozfr.org` · `pontoon.mozilla.org` · `l10n.gnome.org` · `invent.kde.org` · `*.googlesource.com` 는 이 세션의 프록시가 막아(403 / ENOTFOUND) 본문을 열지 못했다. 이 호스트들의 내용은 **검색 결과 요약(snippet)** 에만 기대며, 그렇게 표시한다. GitHub 과 PyPI 는 열려 있어 **저장소를 직접 클론해 센 수치는 "이번 세션 실측"** 으로 표시하고 커밋을 붙였다.

## 1. 괄호 병기 번역 채굴 (parenthetical translation mining)

### Takeaway
"원어 용어(English term)" 꼴 채굴은 Lin et al. 2008 이 CJK 웹에 대해 정립했고, 핵심 난제는 **괄호 앞 원어 용어의 왼쪽 경계(left boundary)** 와 **괄호가 번역이 아닌 경우(모델 번호·약어·부연)** 의 분리다. 한국어 전용 선행 연구(이·서 2002)는 기본 대역 사전 + 음운 유사도 + 부분 일치로 경계를 정했다. ko-dev-terms 는 영어 쪽이 이미 입력으로 주어지므로 경계 문제를 "후보 구간을 전부 증거 행으로 내기"로 결정론적으로 바꿀 수 있다.

### Cited Findings
- Lin, Zhao, Van Durme, Paşca, "Mining Parenthetical Translations from the Web by Word Alignment", ACL-08: HLT, pp. 994–1002 (Columbus, Ohio, 2008). 중국어·일본어·한국어 문서가 용어 뒤 괄호 안에 영어 번역을 다는 관행을 대상으로 한다 — [ACL Anthology P08-1113](https://aclanthology.org/P08-1113/) (본문은 차단되어 검색 요약에 의존), [Google Research 페이지](https://research.google/pubs/mining-parenthetical-translations-from-the-web-by-word-alignment/)
- 방법: 후보 쌍이 든 텍스트 조각을 "부분 병렬 말뭉치(partially parallel corpus)" 로 보고 단어 정렬(word alignment) 알고리즘으로 대응을 세운다. 추출에는 **괄호 앞 단어 중 첫 단어가 괄호 안 단어와 정렬되기만 하면 되고**(즉 정렬된 가장 왼쪽 단어가 원어 용어의 시작이 된다), 완전 정렬은 모든 쌍의 연결을 요구한다는 차이를 논문이 명시한다 — [ACL 2008 Lin PDF (mt-archive 사본, 검색 요약)](https://aclanthology.org/www.mt-archive.info/ACL-2008-Lin.pdf)
- 규모: 중국어 웹에서 **2,600만 쌍 이상**을 뽑아 이전 결과보다 두 자릿수(100배) 이상 많았고, 웹 전체에서 **단 한 번만 나온 번역도 신뢰성 있게** 뽑는다고 주장한다. 뽑은 쌍을 SMT 학습 데이터에 더하자 BLEU 가 유의하게 올랐다 — [sciweavers 초록 사본](https://sciweavers.org/node/207110), [ACL 2008 Lin PDF](https://aclanthology.org/www.mt-archive.info/ACL-2008-Lin.pdf)
- Lin 2008 의 정밀도(precision) 수치와 일본어·한국어 개별 결과는 검색 요약에 나오지 않았다(아래 Gaps).
- Cao, Gao, Nie (MT Summit XI, 2007) 는 단일 언어 중국어 웹 페이지에서 영–중 쌍을 채굴하며, 후속 논문은 이를 **음차 탐지(transliteration detection) + 번역 어휘 채굴** 두 갈래로 나눈 **지도 학습(supervised)** 방식으로 묘사한다 — [MTS 2007 Cao PDF](https://aclanthology.org/www.mt-archive.info/MTS-2007-Cao.pdf) (검색 요약)
- NAACL 2009 의 N09-1048 은 채굴 전에 **진짜 괄호 번역과 다른 괄호 표현을 먼저 가려야** 하며, 원어 구간의 **왼쪽 경계**를 핵심 요소로 그림에 표시한다 — [N09-1048 PDF](https://preview.aclanthology.org/fix_video/N09-1048.pdf) (검색 요약, 저자명 미확인)
- Jiang et al. (ACL 2009) 는 괄호 기반 방법이 일–영 · 한–영 같은 다른 언어 쌍으로 확장 가능하다고 적는다 — [ACL 2009 Jiang PDF](https://aclanthology.org/www.mt-archive.info/ACL-2009-Jiang-1.pdf) (검색 요약)
- **한국어 전용 선행 연구 (2002):** 이·서(충북대)는 한영 혼용 문서의 괄호 안 한–영 번역 구를 인식하기 위해 **기본 대역 사전(base translation dictionary) + 음운 유사도(phonetic similarity) + 부분 일치(partial matching)** 를 쓴다 — [KoreaScience JAKO200211921122601](https://koreascience.or.kr/article/JAKO200211921122601.page) (본문 차단, 검색 요약)
- **잡음:** Jung et al. (2006) 는 한국어 신문의 괄호가 모델 번호 등 번역이 아닌 내용에도 쓰여 추출 오류를 많이 낸다고 보고한다 — ["Clustering of English-Korean Translation Word Pairs Using Bi-grams", Research in Computing Science 18](https://www.rcs.cic.ipn.mx/2006_18/Clustering%20of%20English-Korean%20Translation%20Word%20Pairs%20Using%20Bi-grams.pdf) (본문 차단, 검색 요약)
- Oh & Choi (IJCNLP 2005) 는 기술 용어의 **구성 요소(constituent)** 단위 한–영 번역을 자동 추출한다 — [I05-2012](https://preview.aclanthology.org/menus/I05-2012/) (검색 요약)
- Myung et al. (2024) 의 "Parenthetical Terminology Translation(PTT)" 은 번역문에 영어 원어를 괄호로 병기하게 하는 과제로, **LLM 으로 학습 데이터를 생성**한다 — [arXiv 2410.00683](https://arxiv.org/html/2410.00683v1) (검색 요약). 기준 ①(결정론) 위반.

### Inferences
- **경계 결정의 결정론적 대안 (ko-dev-terms 용):** 입력이 영어 용어 하나로 고정되므로 괄호 안 쪽은 정확 일치(대소문자·복수형 정규화)로 거르고, 괄호 바로 앞의 어절 1개·2개·…·k개 구간을 **각각 별도 후보 행**으로 세면 "승자를 고르지 않는다"는 설계와 맞는다. 한국어에서 조사는 보통 괄호 **뒤**에 붙으므로(`부수 효과(side effect)를`) 괄호 바로 앞 문자열에는 조사가 없는 경우가 많다 — 이 관찰은 이번 세션에 말뭉치로 세어 보지 않았다(💭).
- 이·서 2002 의 "기본 사전 앵커" 방식은 ko-dev-terms 에서 이미 고른 용어집(MS Terminology · K8s · MDN · python-docs-ko)을 앵커로 써서 왼쪽 경계를 잘라 내는 결정론적 변형으로 옮길 수 있다(💭).
- Lin 2008 식 정렬 기반 경계 결정은 정렬기에 따라 결정론 여부가 갈린다(2절).

| 기준 | 판정 |
|---|---|
| ① 결정론 | 정규식 패턴 + 구간 열거는 결정론. 정렬 기반(Lin)·지도 학습(Cao)·LLM(PTT)은 아니거나 조건부 |
| ② 스냅샷 | 대상 저장소 커밋으로 고정 가능 |
| ③ 로컬 | 가능 (이미 고른 세 저장소) |
| ④ 수록량 | 미측정 — 세 저장소 산문에서 실제로 세어야 함 |
| ⑤ 라이선스 | 원 저장소 라이선스를 따름 |
| ⑥ 실패 양상 | 왼쪽 경계 과다·과소, 괄호가 약어·버전·예시인 경우(Jung 2006), 정밀도 수치는 확보 못 함 |

### Gaps
- Lin 2008 · Cao 2007 의 정밀도·재현율 수치, Lin 2008 의 일본어·한국어별 결과: aclanthology.org 가 막혀 PDF 를 열지 못했다.
- 이·서 2002 의 정확도 수치와 경계 결정 세부 규칙: KoreaScience 차단.
- 한국어 개발 문서(괄호 병기)에서의 실제 정밀도를 잰 논문은 찾지 못했다.

## 2. 병렬 말뭉치의 통계적 이중 언어 용어 정렬 (association measures · word aligners)

### Takeaway
연관 척도(Dice · 로그 우도비 LLR · PMI)와 Melamed 의 경쟁 연결(competitive linking)은 순수 계수 기반이라 결정론적이다. 정렬기 중 **fast_align 은 코드에 난수가 없고**(단 OpenMP 부동소수 합산 순서 주의), **eflomal 은 `/dev/urandom` 으로 시드를 잡는 깁스 표집(Gibbs sampling)이라 기본 설정에선 비결정론**이며, awesome-align · SimAlign 은 mBERT 신경망 추론이라 기준 ①을 어긴다. 영–한 공개 AER 기준표는 찾지 못했고, 가장 가까운 일–영에서 통계 정렬기 AER 은 0.47~0.51 수준이다.

### Cited Findings
- **경쟁 연결:** Melamed 의 competitive linking 은 1:1 가정 위의 탐욕(greedy) 알고리즘으로, 가장 강한 단어 쌍부터 연결하고 그 행·열을 지운다. 점수는 우도비(likelihood ratio)이며 φ² · Dice 같은 대칭 척도로 바꿔 끼울 수 있다고 적는다 — [Melamed, arXiv cmp-lg/9706026](https://arxiv.org/pdf/cmp-lg/9706026), [ACL-EACL 1997 Melamed](https://aclanthology.org/www.mt-archive.info/ACL-EACL-1997-Melamed-1.pdf) (검색 요약)
- 약점: 다대다(many-to-many) 연결을 못 만든다 — [Kobdani, MT Summit 2009](https://aclanthology.org/www.mt-archive.info/MTS-2009-Kobdani.pdf) (검색 요약). Kobdani 2009 는 Dice · PMI 의 문제도 보고한다(같은 출처).
- 한 2002 연구(C02-1002)는 MI · Dice · LLR · χ² 를 비교한 뒤 **LLR 임계값 9** 를 택했다 — [C02-1002](https://preview.aclanthology.org/moar-dois/C02-1002.pdf) (검색 요약)
- 번역 어휘의 정밀도 정의는 문맥상 여러 번역이 맞을 수 있어 어렵다고 Melamed 1995 가 적는다 — [VLC 1995 Melamed](https://aclanthology.org/www.mt-archive.info/VLC-1995-Melamed.pdf) (검색 요약)
- **fast_align (이번 세션 실측, commit `cab1e9a` 2020-01-08):** `src/` 전체에 `rand`/`seed`/`mt19937` 호출이 없다. 단 `src/fast_align.cc:139` 에 `#pragma omp parallel for schedule(dynamic) reduction(+:emp_feat_,c0_,likelihood_)` 가 있어 다중 스레드 시 부동소수 합산 순서가 실행마다 달라질 수 있다. 라이선스 Apache-2.0 — [clab/fast_align](https://github.com/clab/fast_align/blob/cab1e9a/src/fast_align.cc)
- **eflomal (이번 세션 실측, commit `1fe2a43` 2025-01-15):** `src/random.c:66-76` 의 `random_system_state()` 가 `/dev/urandom`(실패 시 `time(NULL)`)에서 상태를 읽고, `src/eflomal.c:1158` 에서 이를 호출한다. README · `python/` 에 시드 옵션 문자열(`seed`)이 없다. 라이선스 GPL-3.0 — [robertostling/eflomal](https://github.com/robertostling/eflomal/blob/1fe2a43/src/random.c)
- eflomal README 의 AER: 영–불 1,130,551문장 0.081, 루마니아–영 48,681문장 0.298, 영–힌디 3,530문장 0.467. 같은 표의 fast_align: 영–불 0.153, 루마니아–영 0.325, 영–힌디 0.672 — [eflomal README (commit 1fe2a43)](https://github.com/robertostling/eflomal/blob/1fe2a43/README.md)
- **awesome-align README 의 AER (commit `5f150d4`)** — 일–영(KFTT): fast_align 51.1 · eflomal 47.5 · MGIZA 48.0 · awesome-align(미세조정 없음) 45.6 · 다국어 미세조정 37.4. 중–영: 38.1 · 28.7 · 35.1 · 18.1 · 13.4. 한국어는 표에 없다 — [neulab/awesome-align README](https://github.com/neulab/awesome-align/blob/5f150d4/README.md)
- SimAlign README 의 F1(영–체코·독·페르시아·불·힌디·루마니아): eflomal 이 fast-align 을 전부 앞서고 mBERT-Argmax 가 대부분 선두. 한국어 없음 — [cisnlp/simalign README](https://github.com/cisnlp/simalign)
- **한–영 정렬 평가:** Lee et al. (COLING 2010) 은 400문장쌍 참조 집합을 만들어 정밀도·재현율·F 로 평가했고 기준선은 GIZA++ + grow-diag-final 대칭화였다 — [Coling 2010 Lee](https://aclanthology.org/www.mt-archive.info/Coling-2010-Lee-2.pdf) (검색 요약)
- AER 은 번역 품질 향상과 일관되게 대응하지 않는다는 비판이 있다 — [Fraser & Marcu, CL 2007](https://aclanthology.org/www.mt-archive.info/CL-2007-Fraser.pdf) (검색 요약)
- 저자원 언어(로만시)에서 eflomal 정확도 0.86 vs SimAlign 0.33 · awesome-align 0.4(미세조정 전), 미세조정 후 awesome-align 0.92 — [arXiv 2306.08702](https://arxiv.org/pdf/2306.08702) (검색 요약)

### Inferences
- ko-dev-terms 에 쓸 수 있는 정렬 계열은 **"영어 용어가 든 TU(번역 단위)만 골라 한국어 쪽 n-gram 과의 연관 척도(LLR·Dice)를 세는 방식"** 이다. 정렬 모델 학습이 필요 없고, 같은 TMX 스냅샷이면 같은 수가 나온다(💭, 알고리즘 성질에서 도출).
- fast_align 을 쓰려면 `OMP_NUM_THREADS=1` 로 고정하고 두 번 돌려 출력 해시를 비교하는 시험이 필요하다(코드 `fast_align.cc:139` 에서 도출한 추론, 실제로 돌려 보지는 않음).
- eflomal 은 시드 고정 수단이 소스에 없으므로 결정론 요구를 충족하려면 코드 수정이 필요하다(실측 사실에서 도출).
- GIZA++/MGIZA 는 IBM 모델 EM 이 고정 초기화에서 출발하므로 단일 스레드라면 결정론일 가능성이 높지만, 이번 세션에 소스로 확인하지 않았다(💭).
- 한국어는 교착어이고 어순이 SOV 라 일본어와 유형이 가깝다. 일–영 AER 0.47~0.51(통계 정렬기)을 한–영의 대략적 기대치로 볼 수 있으나 측정값이 아니다(💭).
- 개발 용어 하나를 찾는 데는 전체 문장 정렬보다 **TU 수준 공기(co-occurrence)** 가 더 직접적이다. TU 가 짧은 UI 문자열(평균 수 단어)이면 공기 기반 후보가 꽤 정확해진다 — 3절 실측(`breakpoint` → `중단점` 100 TU)이 그 사례다.

| 방법 | ① 결정론 | ② 고정 | ③ 로컬 | ⑤ 라이선스 | ⑥ 실패 양상 |
|---|---|---|---|---|---|
| Dice/LLR/PMI + 경쟁 연결 | 예 | 입력 스냅샷으로 | 예 | 구현 자유 | 1:1 가정, 다대다 불가, 저빈도에서 PMI 과대 |
| fast_align | 조건부 (단일 스레드) | 예 | 예 | Apache-2.0 | 일–영 AER 51.1 |
| GIZA++/MGIZA | 미확인 (💭 예) | 예 | 예 | — (미확인) | 일–영 AER 48.0 |
| eflomal | 아니오 (urandom 시드) | — | 예 | GPL-3.0 | 일–영 AER 47.5 |
| awesome-align / SimAlign | 아니오 (신경망) | 모델 해시로 가능 | GPU 없이도 가능하나 무거움 | — | 일–영 37.4~45.6 |

### Gaps
- 영–한 공개 정렬 기준(gold standard)과 AER: 찾지 못했다(Lee 2010 의 400문장은 공개 여부 미확인).
- GIZA++/MGIZA 의 결정론 여부와 라이선스: 이번 세션에 소스를 열지 않았다.

## 3. 한국어가 든 소프트웨어 현지화 병렬 말뭉치 · 번역 메모리 (software-localization corpora / TMs)

### Takeaway
UI 현지화 TM 은 **도구·UI 어휘(`breakpoint` → `중단점`, `callback` → `콜백`)는 잘 덮지만 개념 어휘(`side effect` · `single source of truth` · `postcondition`)는 0건**이었다(Pontoon 한국어 TMX 110,374 TU 실측). 커밋으로 고정 가능한 1차 원천은 GitHub 의 `mozilla-l10n/mt-training-data`(한국어 TMX 한 파일) · `firefox-l10n`+`firefox-l10n-source` · `microsoft/vscode-loc` · Chromium `.xtb` · GNOME `po/ko.po` · AOSP `values-ko` 이고, OPUS 의 KDE4 · GNOME · PHP · Mozilla-I10n 은 릴리스 번호로 고정되지만 2018~2021 년 스냅샷이다.

### Cited Findings
**A. Mozilla (Pontoon · Transvision)**
- `mozilla-l10n/mt-training-data` (commit `cda8e0c`, 2026-10-01): `ko/ko_pontoon.tmx`(33,486,005 바이트)와 `ko/sumo_ko.csv` 가 있다. TMX 헤더 `creationtool="pontoon"`, `srclang="en-US"`, `creationdate="2026-10-01T00:56:26"`. 저장소 LICENSE 는 MPL-2.0 — [mozilla-l10n/mt-training-data](https://github.com/mozilla-l10n/mt-training-data/tree/cda8e0c/ko) (이번 세션 실측)
- 같은 TMX 의 TU 수 **110,374**. `tuid` 접두어(프로젝트)별: firefox 24,246 · thunderbird 14,758 · firefox-beta 12,593 · sumo 5,873 · firefox-os 5,439 · firefox-os-25 5,341 · mozilla-accounts 5,266 · amo 4,268 · mozillaorg 3,746 · firefox-for-ios 2,942 · firefox-for-android 2,765 · common-voice 2,762 · mdn 2,150 — [ko_pontoon.tmx](https://github.com/mozilla-l10n/mt-training-data/blob/cda8e0c/ko/ko_pontoon.tmx) (이번 세션 실측, `xml.etree.ElementTree.iterparse` 로 셈)
- **예시 용어 탐침(영어 쪽 단어 경계 정규식, 대소문자 무시, 복수 `s` 허용):** `side effect` 0 · `single source of truth` 0 · `postcondition` 0 · `breakpoint` 100(예: `Add Breakpoint` → `중단점 추가`, `firefox:devtools/client/debugger.properties`) · `callback` 12(`JSONP → callback %S()` → `JSONP → 콜백 %S()`) · `tree` 52(`Hide or unhide tree` → `트리 숨김/표시` 와 `tree-planting` → `나무 심기` 혼재) · `edge` 122(대부분 `right edge` → `오른쪽 가장자리` 같은 화면 기하) · `dependency` 1(`외부 의존성`) — 같은 파일 (이번 세션 실측)
- OPUS 의 Mozilla-I10n v1(2021-03-03 릴리스)은 바로 이 저장소에서 모은 TMX 이고 라이선스 MPL-2.0, en-ko 정렬 82,034 — [Helsinki-NLP/OPUS corpus/Mozilla-I10n/v1](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/Mozilla-I10n/v1) (README · LICENSE · statistics.yaml, 이번 세션 실측)
- `mozilla-l10n/firefox-l10n` (commit `3b935d8`, 2026-10-28): 모든 로캘의 번역만 담고 원문은 `firefox-l10n-source` 에 있다. 번역은 PR 이 아니라 Pontoon 동기화로 `main` 에 커밋된다. LICENSE MPL-2.0 — [firefox-l10n README](https://github.com/mozilla-l10n/firefox-l10n/blob/3b935d8/README.md) (이번 세션 실측)
- 같은 저장소 `ko/` 에 `.ftl` 233개 · `.properties` 96개, FTL 메시지 행 12,532 · properties 항목 4,049(정규식 계수, 대략값). `ko/devtools/` 가 있어 `whypaused-breakpoint = 중단점에서 일시 중지됨` 같은 개발 도구 문자열이 있다 — [firefox-l10n/ko](https://github.com/mozilla-l10n/firefox-l10n/tree/3b935d8/ko) (이번 세션 실측). 원문 저장소 `firefox-l10n-source` 는 commit `1b65ce5` (2026-10-26) — [firefox-l10n-source](https://github.com/mozilla-l10n/firefox-l10n-source/tree/1b65ce5)
- Transvision(commit `2af2374`, MPL-2.0)은 바로 이 두 저장소를 클론해 TM 을 만든다(`app/scripts/setup.sh:53,60`). API v1 서비스: `entity` · `locales` · `repositories` · `search` · `suggestions` · `tm`(품질 지수 포함 번역) · `transliterate` · `versions` (`app/classes/Transvision/API.php:20-28,41-43`) — [mozfr/transvision](https://github.com/mozfr/transvision/blob/2af2374/app/classes/Transvision/API.php) (이번 세션 실측). `transvision.mozfr.org` 자체는 이 세션에서 접속 불가.
- Pontoon 은 번역 화면 프로필 메뉴의 "Download Translation Memory" 로 TMX 를 받고, 파일은 요청 시 생성되어 직전 제출분도 포함된다. 용어집(.tbx)·TM(.tmx)·번역은 누구나 받을 수 있다 — [Mozilla L10N 블로그 2017-05-30](https://blog.mozilla.org/l10n/2017/05/30/reuse-mozilla-translations/) (검색 요약)

**B. OPUS (Tiedemann 2012) — 이번 세션 실측: `Helsinki-NLP/OPUS` 메타데이터 저장소 commit `42d4fbe`(2026-07-20)의 `statistics.yaml`**
- KDE4 v2 (릴리스 2018-12-23): en-ko XML 비텍스트 정렬 87,273 · 파일 597 · 영어 토큰 566,747 / 한국어 383,968; moses 76,708; TMX 69,609 TU. LICENSE 는 "원 출처와 같은 라이선스" — [corpus/KDE4/v2](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/KDE4/v2)
- GNOME v1 (릴리스 2018-12-23, 출처 l10n.gnome.org): en-ko XML 정렬 565,920 · 파일 1,581 · 영어 토큰 3,132,808 / 한국어 2,350,813. 그러나 **moses · TMX 판은 165 TU 뿐**(별도 `en-kr` 334)이라 내려받는 형식에 따라 수량이 크게 다르다. LICENSE "원 출처와 같음" — [corpus/GNOME/v1](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/GNOME/v1)
- PHP v1 (릴리스 2018-03-04, PHP 매뉴얼 부분 번역): en-ko XML 정렬 50,662(비텍스트 통계의 한국어 토큰 0 — 이상값); moses 14,312; TMX 10,909 TU — [corpus/PHP/v1](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/PHP/v1)
- Ubuntu v14.10 (릴리스 2018-12-24, 출처 Launchpad): en-ko 정렬 수 항목이 없고 moses 내려받기 11,602 바이트 · TMX 10,094 바이트로 소량 — [corpus/Ubuntu/v14.10](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/Ubuntu/v14.10)
- OpenOffice v3: en-ko 없음 — [corpus/OpenOffice](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/OpenOffice)
- wikimedia v20260327 (위키백과 Content Translation, CC-BY-SA 4.0): en-ko 196,062 정렬, TMX 178,885 TU — [corpus/wikimedia/v20260327](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/wikimedia/v20260327)
- LinguaTools-WikiTitles v2014 (위키백과 문서 제목 + 넘겨주기·링크 텍스트, CC-BY-SA): en-ko 4,826,614 정렬, TMX 3,862,915 TU — [corpus/LinguaTools-WikiTitles/v2014](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/LinguaTools-WikiTitles/v2014)
- XLEnt v1: en-ko 개체명 쌍 2,852,501. FastAlign + LASER 임베딩 + 음차 정렬을 합쳐 만든 **개체명(named entity)** 쌍이라 일반 개발 용어와는 거리가 있고, 생성에 신경망(LASER)을 썼다 — [corpus/XLEnt/v1](https://github.com/Helsinki-NLP/OPUS/tree/42d4fbe/corpus/XLEnt/v1)
- 내려받기 URL 은 `https://object.pouta.csc.fi/OPUS-<코퍼스>/<버전>/{tmx,moses,xml}/en-ko.*` 꼴로 릴리스 버전이 경로에 박혀 있다 — 같은 statistics.yaml. (이 호스트는 이번 세션에서 차단되어 실제 파일을 받지 못했다.)
- OPUS 인용 규약: J. Tiedemann, 2012, "Parallel Data, Tools and Interfaces in OPUS", LREC 2012 — 각 코퍼스 README

**C. 그 밖의 1차 원천 (GitHub 커밋으로 고정)**
- `microsoft/vscode-loc` (commit `62d5443`, 2026-10-19, MIT): `i18n/vscode-language-pack-ko/translations/` 아래 main + 확장별 JSON 에 한국어 문자열 **약 28,000개**. 키는 `모듈 경로 → 메시지 키`(예: `vs/base/browser/ui/dialog/dialog` → `dialogClose: 대화 상자 닫기`)이고 **영어 원문은 이 저장소에 없다** — [microsoft/vscode-loc](https://github.com/microsoft/vscode-loc/tree/62d5443/i18n/vscode-language-pack-ko) (이번 세션 실측)
- Chromium (`chromium/chromium` GitHub 미러, commit `4f6e0f57`, 2026-10-27): `chrome/app/resources/generated_resources_ko.xtb` 1,166,826 바이트, `<translation>` 10,773개. 각 항목은 숫자 ID(메시지 지문 fingerprint)로만 식별되어 영어 원문(.grd/.grdp)과 따로 맞춰야 한다 — [generated_resources_ko.xtb](https://github.com/chromium/chromium/blob/4f6e0f57/chrome/app/resources/generated_resources_ko.xtb) (이번 세션 실측)
- GNOME GTK (`GNOME/gtk` 미러, commit `2f51d3c`, 2026-10-27): `po/ko.po` 의 `msgid` 1,811개, 머리말 "distributed under the same license as the gtk+ package" — [GNOME/gtk po/ko.po](https://github.com/GNOME/gtk/blob/2f51d3c/po/ko.po) (이번 세션 실측)
- AOSP (`aosp-mirror/platform_frameworks_base`, 마지막 커밋 `1cdfff55` 2025-03-26): `core/res/res/values-ko/strings.xml` 의 `<string>` 2,402개(영어 `values/strings.xml` 2,424개), Apache-2.0 머리말. 미러의 마지막 커밋이 2025-03 이라 갱신이 멈췄을 수 있다 — [values-ko/strings.xml](https://github.com/aosp-mirror/platform_frameworks_base/blob/1cdfff55/core/res/res/values-ko/strings.xml) (이번 세션 실측)
- KDE: Debian 의 PO 현황 페이지가 KF6 한국어 파일을 `po/ko/kio6.po` (kf6-kio 99%, 1142 번역) · `po/ko/ktexteditor6.po` (1318 번역) 처럼 나열하고 번역자는 Shinjo Park(kde-kr) — [Debian l10n PO ko](https://www.debian.org/international/l10n/po/ko) (검색 요약). KDE 원 저장소(SVN)는 이번 세션에서 열지 못했다.
- Weblate: 사용자별·프로젝트별 TM 을 JSON 또는 TMX 로 내려받을 수 있고, 인스턴스 전체는 관리 명령 `dump_memory`(JSON)로 덤프한다 — [Weblate 문서 Translation Memory](https://docs.weblate.org/en/weblate-5.8.4/admin/memory.html) (검색 요약)
- **Apple 현지화 용어집(localization glossaries):** 개발자 로그인 뒤의 DMG 로 배포되며 안에 XML 인 `.lg` 파일이 있고 한국어(ko)도 포함된다. 라이선스는 "사이트에서 복사·재배포하지 않으면 ToS 범위"라는 2012년경 포럼 답변 정도만 있다 — [douglashill gist](https://gist.github.com/douglashill/c5b08a9099883475294d27cecc56ec29), [Xojo 포럼](https://forum.xojo.com/t/apple-language-glossary-translation/75627), [ProZ 포럼](https://esl.proz.com/forum/apple_mac_operating_systems/238694-ios_multilingual_glossary.html) (검색 요약)
- **Microsoft Learn 한국어 문서 저장소:** `MicrosoftDocs/azure-docs.ko-kr` · `visualstudio-docs.ko-kr` · `cpp-docs.ko-kr` · `dotnet/docs.ko-kr` 등에 `git ls-remote` 하면 자격 증명을 요구했다(공개 저장소로 존재하지 않음) — 이번 세션 실측. 2020년 스냅샷에는 `powerbi-docs.ko-kr` 가 보인다 — [Wayback 2020-12 MicrosoftDocs](https://webcf.waybackmachine.org/web/20201206060401/https://github.com/MicrosoftDocs)

### Inferences
- **개념 어휘 공백:** Pontoon 한국어 TMX 에서 `side effect` · `single source of truth` · `postcondition` 이 0건인 것은 UI 현지화 TM 이 "사용자에게 보이는 문자열"만 담기 때문으로 보인다(💭). 이런 용어에는 문서 번역(이미 고른 MDN · K8s · python-docs-ko 산문)이 더 맞고, TM 은 도구·UI 용어(`breakpoint` · `callback` · `stack trace` 류) 쪽 증거원이다.
- **다의어 위험:** `edge` 122 TU 가 대부분 화면 기하(`가장자리`)라서 그래프 의미(`간선`)의 증거로 셀 수 없다. 증거 행에 `tuid`(예: `firefox:devtools/...`)를 같이 실으면 사람이 맥락을 판단할 수 있다(💭). `devtools` 경로 접두어로 거르는 것이 개발 어휘 정밀도를 올리는 결정론적 필터다(💭).
- **중복 계수:** firefox / firefox-beta / firefox-os / firefox-os-25 가 같은 문자열을 반복하므로, 수를 셀 때 (영어, 한국어) 쌍 단위로 중복을 없애지 않으면 부풀려진다(💭).
- **고정(pinning):** GitHub 원천은 커밋 SHA 로, OPUS 는 릴리스 버전(v1/v2) + 내려받은 파일의 sha256 으로 고정하는 것이 자연스럽다(💭). `mt-training-data` 는 TMX 한 파일이 33 MB 라 로컬 보관이 쉽다.
- vscode-loc · Chromium 은 영어 원문을 따로 맞춰야(join) 하므로 TMX 보다 손이 많이 간다. vscode 는 원문이 `microsoft/vscode` 소스의 `nls.localize(키, 영어)` 호출에 있고, Chromium 은 .grd 메시지에서 지문 ID 를 계산해야 한다 — 둘 다 결정론이지만 이번 세션에 결합을 구현해 보지 않았다(💭).

| 원천 | 형식 | en–ko 규모 | ① | ② 고정 | ③ 로컬 | ⑤ 라이선스 |
|---|---|---|---|---|---|---|
| mt-training-data `ko_pontoon.tmx` | TMX 1.4 | 110,374 TU (2026-10-01) | 예 | 커밋 `cda8e0c` | 33 MB | MPL-2.0 |
| firefox-l10n + -source | FTL/properties | ko 약 16.6k 항목 | 예 | 커밋 | 작음 | MPL-2.0 |
| OPUS KDE4 v2 | TMX/moses/XML | 69,609 TU (2018) | 예 | 릴리스 v2 | 1.7 MB(TMX gz) | 원 출처 따름(KDE: 대개 GPL/LGPL 계열 — 미확인) |
| OPUS GNOME v1 | XML(TMX 는 165 TU 뿐) | 565,920 정렬 (2018) | 예 | 릴리스 v1 | XML 정렬 3.3 MB | 원 출처 따름 |
| OPUS PHP v1 | TMX | 10,909 TU (2018) | 예 | v1 | 작음 | 원 출처 따름 |
| OPUS wikimedia | TMX | 178,885 TU (2026-03) | 예 | v20260327 | 36 MB | CC-BY-SA 4.0 |
| OPUS WikiTitles v2014 | TMX | 3.86M TU (2014) | 예 | v2014 | 31 MB | CC-BY-SA |
| vscode-loc | JSON (ko 만) | 약 28,000 | 예 | 커밋 | 3 MB | MIT |
| Chromium xtb | XTB (ko 만, ID) | 10,773 (파일 1개) | 예 | 커밋 | 1.2 MB | 미확인 |
| GTK po/ko.po | PO | 1,811 msgid | 예 | 커밋 | 작음 | LGPL(gtk+ 와 같음) |
| AOSP values-ko | Android XML | 2,402 | 예 | 커밋(미러 2025-03 정지) | 작음 | Apache-2.0 |
| Apple glossaries | .lg(XML) in DMG | 미확인 | 예 | 다운로드 날짜뿐 | — | 재배포 불가로 보임 |

### Gaps
- OPUS 원본 파일(TMX)을 내려받아 예시 용어를 세어 보지 못했다(`object.pouta.csc.fi` 차단). 위 OPUS 수치는 메타데이터 저장소 기준이다.
- OPUS GNOME v1 의 en-ko TMX 가 165 TU 뿐인 이유: 확인하지 못했다.
- KDE 의 실제 라이선스(코퍼스는 "원 출처와 같음"), Chromium 의 LICENSE 파일, GIZA++ 라이선스: 이번 세션에 원문을 열지 않았다.
- Apple 용어집의 현재 라이선스·한국어 항목 수: 로그인 필요로 확인 불가.
- vscode-loc 의 영어 원문 결합 경로: 미검증.

## 4. 비교 말뭉치 기반 용어 번역 (comparable corpora: Rapp · Fung)

### Takeaway
문맥 벡터(context vector) + 씨앗 사전(seed dictionary) 방식은 계수 기반이라 결정론적으로 만들 수 있지만, **정확도가 낮고 큰 씨앗 사전과 대용량 말뭉치가 필요**하며 결과가 "근거 행"이 아니라 "유사도 순위"라서 ko-dev-terms 의 증거 모델과 맞지 않는다. 한국어 쪽 연구는 주로 영어를 피벗(pivot)으로 쓰는 병렬 말뭉치 방식으로 우회했다.

### Cited Findings
- Rapp (ACL 1999, pp. 519–526): 영어 "teacher"–"school" 이 우연 이상으로 함께 나오면 독일어 번역어끼리도 그렇다는 가정. 독일어 FAZ 1억 3,500만 단어, 영어 Guardian 1억 6,300만 단어, Collins 독영 사전 기반 기초 어휘 — [ACL P99-1067](https://aclanthology.org/P99-1067/) (검색 요약)
- 한 목록 요약은 Rapp 1999 의 정답률을 **약 72%** 로 적지만, 시험 단어 수·top-N 기준은 확인하지 못했다 — [P99-1067 검색 요약](https://aclanthology.org/www.mt-archive.info/ACL-1999-Rapp.pdf) (미검증 수치)
- 표준 절차: (1) 비교 말뭉치에서 문맥 벡터를 만들고 (2) 씨앗 사전으로 원어 벡터를 번역한 뒤 (3) 목표어 벡터와 유사도를 잰다. 한 한국어 관련 논문은 비교 말뭉치 기반 어휘 추출의 **정확도가 상당히 낮고, 정확도를 높이려면 대규모 씨앗 사전이 필요**하다고 적는다 — [KoreaScience JAKO201424750260684](https://koreascience.kr/article/JAKO201424750260684.pdf) (검색 요약; 어느 문장이 어느 논문인지 요약 수준에서만 확인)
- Fung (1995) 이 비교 말뭉치 연구의 고전으로 인용된다 — 같은 검색 요약 ([KoreaScience JAKO201424750260684](https://koreascience.kr/article/JAKO201424750260684.pdf))
- 서형원 · 권홍석 · 김재훈 그룹은 한–스페인 · 한–불 같은 저자원 쌍에 대해 **한–영 병렬 + 영–X 병렬** 두 말뭉치를 쓰는 피벗 방식을 제안했다(BUCC 2013, 2014 확장, 2015 학위논문) — [BUCC 2013 Kwon](https://aclanthology.org/www.mt-archive.info/10/BUCC-2013-Kwon.pdf) (검색 요약)

### Inferences
- `postcondition` 같은 저빈도 용어는 한국어 비교 말뭉치에서 후보 자체의 빈도가 낮아 문맥 벡터가 성기다. 순위 1위가 맞을 확률이 낮고, 출력에 "어느 파일 몇 줄에서 이 번역이 쓰였다"는 근거가 붙지 않는다(💭).
- 결정론 조건: 토큰화기·씨앗 사전·말뭉치 스냅샷·유사도 함수를 모두 고정하면 결정론이다. 단 씨앗 사전 자체가 ko-dev-terms 의 다른 원천(MS Terminology 등)이 되어 순환한다(💭).
- 결론적으로 기준 ①②③은 충족 가능하나 ④⑥(정밀도·근거성)에서 ko-dev-terms 의 "증거 행" 원천으로는 부적합하다(💭).

### Gaps
- 영–한 비교 말뭉치로 개발 용어를 찾은 정량 결과는 찾지 못했다.
- Rapp 1999 의 72% 수치의 평가 조건: 원문 미확인.

## 5. 음차 탐지 · 역음차 (transliteration detection / back-transliteration)

### Takeaway
"트리"가 tree 의 음차인지, "나무"가 번역인지를 **결정론적으로** 가리는 길은 (a) 발음 사전(CMUdict)으로 영어 발음을 얻어 외래어 표기 규칙으로 예상 한글을 만들고 비교하는 규칙 방식(이도길 2009 계열), (b) 음절 단위 HMM 태깅(오종훈·최기선 2001)처럼 고정 모델의 Viterbi 추론이다. 외래어 한글 표기 도구 Hangulize 에는 **영어 규칙이 없다**(이번 세션 실측). 평가용 영–한 음차 쌍은 NEWS 공유 과제의 EnKo(약 7천 쌍, CJK Institute 제공)가 있으나 라이선스가 불명확하다.

### Cited Findings
- 정길순(Jeong) · 맹성현(Myaeng) · 이재성 · 최기선, "Automatic identification and back-transliteration of foreign words for information retrieval", *Information Processing & Management* 35(4), 1999, pp. 523–540. 과학·공학 분야 한국어 텍스트에 외래어·영어가 많다는 문제를 IR 관점에서 다룬다 — [IR Anthology IPM 1999 35(4)](https://ir.webis.de/anthology/1999.ipm_journal-ir0anthology0volumeA35A4.6/), [dblp](https://dblp.dagstuhl.de/rec/journals/ipm/JeongMLC99.html) (서지·초록 수준, 본문 미확인)
- Kang & Choi (LREC 2000 / ACL 2000 demo): **결정 트리(decision tree)** 로 음차와 역음차를 같은 방법론으로 학습하며, 음운 정렬된 영어–한국어 음차 쌍이 많이 필요하다고 적는다 — [LREC 2000 Kang](https://aclanthology.org/www.mt-archive.info/LREC-2000-Kang.pdf), [ACL 2000 demo](https://cse.hkust.edu.hk/acl2000/Demo/10_kang.pdf) (검색 요약)
- 오종훈 · 최기선, "Automatic Detection and Extraction of Transliterated Foreign Words Using Hidden Markov Model", 인지과학 12(3), 2001, pp. 19–28: 각 음절을 "순수 한국어 / 음차 외래어" 로 태깅하는 이진 상태 HMM. 초록은 높은 재현율·정밀도를 주장하나 수치는 요약에 없다 — [KoreaScience JAKO200111920902923](https://koreascience.kr/article/JAKO200111920902923.page) (검색 요약)
- 2002 IP&M 의 같은 그룹 논문은 대규모 레이블 데이터가 필요 없는 HMM 기반 외래어 인식기를 보고한다 — ["Effective foreign word extraction for Korean information retrieval", KAIST 저장소](https://koasas.kaist.ac.kr/handle/10203/85164) (검색 요약)
- 검색 요약은 2005년 SVM 기반 외래어 추출 연구가 10겹 교차 검증 정밀도 96.55% · 재현율 89.30% 를 보고했다고 전하지만, 어느 문헌인지 요약에서 특정되지 않았다 — 후보 출처 [성신여대 저장소](https://repository.sungshin.ac.kr/handle/2025.oak/1893) (미검증)
- Oh & Choi (COLING 2002) "An English-Korean Transliteration Model Using Pronunciation and Contextual Rules" 는 발음·문맥 규칙 기반 정방향 음차 모델이다 — [2006 일본 학회 논문의 참고문헌](https://www.anlp.jp/proceedings/annual_meeting/2006/pdf_dir/E2-5.pdf) (검색 요약)
- Oh & Isahara, "Extracting English-Korean Transliteration Pairs from Web Corpora", ICCPOL 2006, pp. 222–233 — [dblp](https://dblp.org/rec/conf/iccpol/OhI06.html) (서지만)
- 이도길(2009) 은 기존 **발음 사전에서 추출한 발음 정보**로 영–한 음차 표기 사전을 만들어, 철자에서 발음을 추측하는 불완전한 단계를 피한다 — [KoreaScience JAKO200934939598182](https://koreascience.kr/article/JAKO200934939598182.pdf) (검색 요약)
- CMUdict (`cmusphinx/cmudict`, commit `7479086`, 2025-10-24): `cmudict.dict` 135,166행, BSD 계열 재배포 허용 라이선스(Copyright 1993–2015 CMU) — [cmusphinx/cmudict](https://github.com/cmusphinx/cmudict/tree/7479086) (이번 세션 실측)
- Hangulize (`hangulize/hangulize`, commit `b951421`, 2026-05-14): 외래어를 한글로 바꾸는 도구로 `specs/` 에 40개 언어 규칙(.hsl: deu, ita, jpn, rus, spa 등)이 있으나 **영어(eng) 규칙은 없다** — [hangulize/specs](https://github.com/hangulize/hangulize/tree/b951421/specs) (이번 세션 실측)
- NEWS 2009 공유 과제의 EnKo 데이터는 CJK Institute 가 제공한 약 7K 이름이고, NEWS 2018 의 T-EnKo 는 학습 7,387 · 개발 1,000 · 시험 1,000 — [NEWS 2009 whitepaper](https://aclanthology.org/www.mt-archive.info/NEWS-2009-Li-2.pdf), [NEWS 2018 W18-2408](https://preview.aclanthology.org/fix_video/W18-2408.pdf) (검색 요약). 라이선스 조항은 찾지 못했다.
- Firefox TMX 에서 `tree` 가 문맥에 따라 `트리`(UI) 와 `나무`(나무 심기)로 모두 번역된다 — [ko_pontoon.tmx](https://github.com/mozilla-l10n/mt-training-data/blob/cda8e0c/ko/ko_pontoon.tmx) (이번 세션 실측). 즉 같은 영어 용어에 음차형과 번역형 후보가 동시에 생긴다.

### Inferences
- **결정론적 판별 절차 제안(💭):** 영어 용어 → CMUdict ARPAbet 발음 → 국립국어원 "영어의 표기" 세칙을 손으로 옮긴 규칙표 → 예상 한글 표기 → 후보 한글과 자모(jamo) 단위 편집 거리. `TREE` → `트리` 는 거리 0, `나무` 는 큼. 규칙표·CMUdict 커밋을 고정하면 같은 입력에 같은 판정이 나온다. CMUdict 에 없는 합성어·약어(`OAuth`, `kubectl`)는 판정 불가로 남긴다.
- 이 판정은 승자를 고르는 것이 아니라 후보 행에 "음차형/번역형" 열을 붙이는 용도로만 쓰는 것이 ko-dev-terms 설계와 맞는다(💭).
- 음차는 표기 변이(`엣지`/`에지`, `콜백`/`콜 백`)가 많아 계수 전에 변이형 묶기가 필요하다(💭). 이번 세션 Kiwi 시험에서 `엣지` 는 NNP 로, `콜백` 은 `콜/NNG 백/NNG` 로 쪼개졌다(6절).

### Gaps
- 오종훈·최기선 2001, 정길순 외 1999 의 정밀도 수치: 본문 미확인.
- 공개된 규칙 기반 영어→한글 외래어 표기 변환기(오픈소스)는 찾지 못했다.
- NEWS EnKo 데이터의 현재 입수 경로와 라이선스: 미확인.

## 6. 말뭉치에서 한국어 용어 세기 (형태소 분석기 vs 정규식 + 조사 목록)

### Takeaway
Kiwi(kiwipiepy 0.24.1, Apache-2.0, Windows 휠 있음)는 **같은 입력에 같은 출력**을 냈고(이번 세션 두 인스턴스 비교) 띄어쓰기 변이(`부수 효과`/`부수효과`)를 같은 형태소 열로 통일하지만, **외래어·미등록어를 잘못 쪼갠다**(`콜백` → `콜`+`백`, `정점` → `정`+`점`). 사용자 사전(`add_user_word`)으로 합성어를 고정할 수 있다. MeCab-ko 는 Windows 휠이 있고, KoNLPy 는 2022년 이후 릴리스가 없고 GPL-3.0 이다. 정규식 + 조사 목록은 결정론적이고 의존성이 없지만 **조사를 떼는 방식**은 `효과`→`효`(과) 같은 오절단을 낸다.

### Cited Findings
- Kiwi 논문: 이민철(Kakao), "Kiwi: 통계적 언어 모델과 Skip-Bigram 을 이용한 한국어 형태소 분석기 구현", 디지털인문학 1(1), 2024, pp. 109–136. 모호성 해소 평균 정확도 **86.7%**(기존 오픈소스 분석기 50~70%), 한계로 **미등록어 처리와 방언** — [accesson.kr KJDH 1(1)](https://accesson.kr/kjdh/v.1/1/109/43508), [Kiwi README 인용 절 (commit bebfd76)](https://github.com/bab2min/Kiwi/blob/bebfd76/README.md)
- Kiwi README: 세종 품사 체계, 세종 말뭉치 + 모두의 말뭉치로 학습, **웹 텍스트 약 87% · 문어 약 94%** 형태소 분석 정확도. Windows · Linux · macOS · Android 바이너리 배포. 0.23.2 이하 LGPL, 이후 Apache-2.0(모델 파일 포함) — [bab2min/Kiwi README (commit bebfd76)](https://github.com/bab2min/Kiwi/blob/bebfd76/README.md) (README 17행, 46행, 라이선스 절; 이번 세션 실측)
- 같은 README 의 예시에서 Kiwi 는 외래 고유명 `엠마누엘` 을 `엠마누/NNP 에/JKB ᆯ/JKO` 로 잘못 쪼갠다 — 같은 출처 "성능" 절
- PyPI (이번 세션 조회, 2026-10-28): kiwipiepy 0.24.1 (Apache-2.0, 2026-10-20 업로드, 휠 win_amd64 · manylinux x86_64/aarch64 · macOS) — [PyPI kiwipiepy](https://pypi.org/project/kiwipiepy/); python-mecab-ko 1.3.7 (BSD-3, 2024-07-14, 휠 win32 · win_amd64 · win_arm64 · manylinux · macOS) — [PyPI python-mecab-ko](https://pypi.org/project/python-mecab-ko/); mecab-ko 1.0.2 (BSD, 2025-09-23, win_amd64 포함) — [PyPI mecab-ko](https://pypi.org/project/mecab-ko/); konlpy 0.6.0 (GPL v3, 2022-01-02, 순수 파이썬 휠) — [PyPI konlpy](https://pypi.org/project/konlpy/)
- **Kiwi 결정론·분절 시험 (이번 세션 실측, kiwipiepy 0.24.1, 기본 모델):**
  - `함수의 부수 효과를` → `부수/NNG 효과/NNG 를/JKO`; `부수효과가` → `부수/NNG 효과/NNG 가/JKS` (띄어쓰기 변이가 같은 형태소 열)
  - `사후 조건을` · `사후조건이` → 둘 다 `사후/NNG 조건/NNG`; `단일 진실 공급원을` → `단일/NNG 진실/NNG 공급원/NNG 을/JKO`
  - `트리를` → `트리/NNG 를/JKO`; `중단점에서` → `중단점/NNP 에서/JKB`; `엣지를` → `엣지/NNP 를/JKO`; `사이드이펙트가` → `사이드 이펙트/NNP 가/JKS`
  - 오분절: `콜백으로` → `콜/NNG 백/NNG 으로/JKB`; `간선과 정점을` → `간선/NNG 과/JC 정/NNG 점/NNG 을/JKO`
  - 새 `Kiwi()` 인스턴스 둘의 출력 전체가 동일(sha256 앞 16자 `22d0f288e743d4db`)
  - `add_user_word('부수효과','NNG')` · `add_user_word('사후조건','NNG')` 후 `부수효과/NNG` · `사후조건/NNG` 하나로 나온다
  - (시험 스크립트는 scratchpad 에서 돌렸고 저장소에 남기지 않았다)
- KoNLPy 문서 예시에서 `아버지가방에들어가신다` 를 꼬꼬마·Mecab 은 `아버지+가+방`, 코모란은 고유명사 하나, Okt 는 `아버지+가방` 으로 나눠, 자기 데이터로 직접 비교해 고르라는 권고가 있다 — [wikidocs KoNLPy 분석기 비교](https://wikidocs.net/302542) (검색 요약). Okt 는 신조어·외래어에 강하다는 평, 코모란은 복합명사 분리가 약하다는 평이 있다 — 같은 검색의 [wikidocs 213362](https://wikidocs.net/213362) · [velog 비교 글](https://velog.io/@metterian/한국어-형태소-분석기POS-분석-3편.-형태소-분석기-비교) (검색 요약, 2차 자료)
- 2023 Findings of EMNLP 는 L2 한국어 글에서 Stanza · Trankit · Kkma · Komoran 을 평가했고 Kiwi 는 포함하지 않았다 — [2023.findings-emnlp.767](https://aclanthology.org/2023.findings-emnlp.767.pdf) (검색 요약)
- 정규식 기반 조사 제거·명사 빈도 계산을 정면으로 평가한 자료는 찾지 못했다 — 위 한국어 검색 결과 전반

### Inferences
- **추천 계수 방식(💭):** 분석기로 조사를 "떼는" 대신, 후보 문자열(띄어쓰기 제거형과 원형 둘 다)을 어절 **앞부분 일치**로 찾고 남은 꼬리가 고정 조사 목록(을/를/이/가/은/는/의/에/에서/으로/로/와/과/도/만/까지 …)에 있거나 빈 문자열일 때만 센다. 조사를 떼지 않으므로 `효과` 가 `효`+`과` 로 잘리는 문제가 없고, 의존성 0 · 결정론 · Windows 무관이다. 단 `트리` 가 `트리거`(trigger)의 앞부분과 일치하는 오탐은 꼬리 검사로 막히지만, 조사 목록에 없는 어미(`트리이다`→`이다`)를 놓칠 수 있다 — 목록을 시험으로 고정해야 한다.
- 형태소 분석기는 띄어쓰기 변이 통일에 유리하지만 외래어 음차 후보(`콜백` 류)를 쪼개므로, 쓰려면 **후보를 사용자 사전에 먼저 넣고** 형태소 열 일치로 세야 한다. 이 경우 kiwipiepy 판 + 모델 판을 증거 행의 스냅샷 id 에 함께 적어야 재현된다(💭).
- 기준 판정: Kiwi ①예(이번 시험 범위) ②PyPI 판 고정 ③Windows 휠 있음 ⑤Apache-2.0 ⑥미등록 외래어 오분절; MeCab-ko ①예(사전 기반 CRF, 미시험) ③Windows 휠 있음 ⑤BSD; KoNLPy Okt/Komoran ③JVM 필요(💭, 이번 세션 미확인) ⑤GPL-3.0(래퍼), 2022년 이후 릴리스 없음; 정규식+조사 목록 ①예 ③어디서나 ⑤자체 코드 ⑥어미·변이형 누락.

### Gaps
- MeCab-ko · Komoran · Okt 로 같은 개발 용어 문장을 돌려 비교하지 않았다(Kiwi 만 시험).
- Kiwi 가 다중 스레드(`num_workers`>0)에서도 같은 결과를 내는지: 시험하지 않았다(`num_workers=0` 만 사용; 0.21.0 이후 의미가 바뀌었다는 경고가 나왔다).
- 정규식 + 조사 목록 방식의 정밀도·재현율을 잰 공개 평가: 찾지 못했다.
