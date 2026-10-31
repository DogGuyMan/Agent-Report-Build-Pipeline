# MT·LLM 용어 처리 방법론 — 제약 · 검색 · 평가 · 환각 (영어 개발 용어의 한국어 표기 근거 관점)

> 조사 조건(2026-10-28): 이 세션에서 `aclanthology.org` · `arxiv.org` 는 WebFetch 가 `getaddrinfo ENOTFOUND` 로 실패했고, GitHub API(`wmt-conference/wmt25-terminology`)는 403 으로 막혔다. **아래 모든 내용은 WebSearch 결과 스니펫에서 온 것이고 논문 본문은 열지 못했다.** 스니펫에 없는 수치는 적지 않았다. 원문 확인이 필요하면 세션 네트워크 설정에서 `aclanthology.org` · `arxiv.org` 를 허용해야 한다.
>
> 기준 6개(모든 방법에 적용): ① 결정성(Deterministic) ② 재현성(Reproducible — 무엇을 고정해야 하나) ③ 오프라인/로컬 가능성 ④ 한국어·en–ko 근거 ⑤ 판정자(chooser)가 아니라 검증·측정기(verifier/measure)로 쓸 수 있나 ⑥ 알려진 실패 양상.

## 1. 어휘 제약 디코딩(Lexically constrained decoding)과 용어 인지 학습(Terminology-aware training) — 용어집이 어디서 온다고 가정하나

### Takeaway
제약 디코딩(Hokamp & Liu 2017 → Post & Vilar 2018 → Hu et al. 2019)과 용어 인지 학습(Dinu et al. 2019 → Exel et al. 2020) 계열은 모두 **용어집이 이미 주어져 있다(오라클)** 고 가정한다. 이 방법들은 용어집을 *소비*하지, 용어집 항목의 타당성을 *근거*하지 않는다. 따라서 ko-dev-terms 의 상류(근거 산출)가 아니라 하류(산출물을 쓰는 쪽)에 위치한다.

### Cited Findings
- **Grid Beam Search(Hokamp & Liu 2017)** 는 제약 개수에 대해 선형(linear) 복잡도이고, 빔을 제약 수만큼 곱해 실효 빔 크기가 k(C+1) 이 된다(Post & Vilar 의 서술). Anderson et al. 2017 방식은 제약 수에 지수(exponential) 복잡도 — [Post & Vilar 2018, arXiv 1804.06609 (ar5iv)](https://ar5iv.labs.arxiv.org/html/1804.06609)
- **Dynamic Beam Allocation, DBA(Post & Vilar 2018, NAACL, pp.1314–1324)** 는 크기 k 의 단일 빔을 유지하고 매 시점 빔 슬롯을 "제약 뱅크(constraint bank)" 들에 동적으로 나눠 준다 — 제약 수 C 에 대해 O(1). "빔을 제약 수로 곱하는 대신 나눈다." 구현은 Sockeye 에 포함 — [ACL Anthology N18-1119](https://aclanthology.org/N18-1119/); [ar5iv 1804.06609](https://ar5iv.labs.arxiv.org/html/1804.06609)
- 제약은 **대상 언어 쪽 제약(target-side constraints)** 으로 디코딩 시점에 외부에서 주어진다(복잡도 표의 정의) — [ar5iv 1804.06609](https://ar5iv.labs.arxiv.org/html/1804.06609)
- **Hu et al. 2019(NAACL, pp.839–850)** 는 DBA 를 벡터화(vectorized)하고 다중 상태 트라이(multi-state trie)를 넣어 양(positive) 제약 디코딩을 약 5배 빠르게 했다. Fairseq 의 constrained decoding 구현이 이 작업을 기반으로 하며, 벡터 확장은 Sockeye 메인 브랜치에 병합되지 않았다 — [ACL Anthology N19-1090](https://aclanthology.org/N19-1090/); [fairseq constrained_decoding README 사본(HF)](https://huggingface.co/datasets/echodict/StreamSpeech/blob/main/fairseq/examples/constrained_decoding/README.md)
- **Dinu et al. 2019(ACL, pp.3063–3068, Amazon)** 는 제약 디코딩 없이, 원문 안에 용어 주석을 인라인으로 넣어(원문 용어 옆에 대상 용어를 덧붙이기 append, 또는 원문 용어를 대상 용어로 치환 replace) Transformer 를 학습시킨다. 제약 디코딩 최신 구현보다 효과적이고 무제약 디코딩만큼 빠르다고 보고. 실험은 en→de(WMT 2018 뉴스), 용어는 **기존 용어 사전 두 개에서 가져왔다**, 학습 데이터 220만 문장 — [arXiv 1906.01105 (ar5iv)](https://ar5iv.labs.arxiv.org/html/1906.01105); [ACL Anthology P19-1294](https://preview.aclanthology.org/setup/P19-1294)
- **Exel et al. 2020(EAMT, pp.271–280, SAP)** 는 Dinu et al. 의 인라인 주석 + 원천 팩터 임베딩(source factor embeddings) 변형을 제약 디코딩과 비교하고, 새 언어쌍으로 확장, 오류 분류와 인간 평가를 덧붙였다. 출발점은 **SAP 사용 시나리오의 용어 문제**(사내 용어집) — [ACL Anthology 2020.eamt-1.29](https://aclanthology.org/2020.eamt-1.29)
- **Bogoychev & Chen 2023(WMT23)** 은 단어 정렬(word alignment)에서 얻은 **유사 용어(pseudo-terminology)** 를 원문 단어에 주석해 용어 인지 모델을 학습시킨다 — 즉 학습용 "용어집" 자체를 정렬로 합성한다 — [ACL Anthology 2023.wmt-1.80](https://aclanthology.org/2023.wmt-1.80); [arXiv 2310.05824](https://arxiv.org/abs/2310.05824v1)

### Inferences
- 💭 다섯 계열 모두 "올바른 대상 용어가 무엇인가" 는 입력으로 받는다. Dinu 는 기존 사전, Exel 은 사내 용어집, Bogoychev 는 정렬로 만든 유사 용어, Post & Vilar 는 외부 제약. **이 문헌에는 "어떤 한국어 표기가 맞는가" 를 근거하는 절차가 없다** — ko-dev-terms 가 채우려는 빈칸과 정확히 겹친다.
- 💭 이 방법들은 ko-dev-terms 의 검증기로는 쓰기 어렵다: 이들은 *생성 장치*이고, 출력이 제약을 만족했는지는 별도의 문자열 검사(아래 3절 지표)로 확인한다.

#### 기준 판정
| 방법 | ① 결정성 | ② 고정 대상 | ③ 로컬 | ④ 한국어 근거 | ⑤ 검증기 가능성 | ⑥ 실패 양상 |
|---|---|---|---|---|---|---|
| GBS / DBA / 벡터화 DBA | 빔 탐색 자체는 결정적 알고리즘. 단 GPU 추론 커널의 배치 불변성 문제(6절)는 그대로 적용된다고 추론(💭) | 모델 가중치 · 디코더 구현 판(Sockeye/Fairseq) · 빔 크기 · 제약 목록 | 가능(오픈소스 Sockeye/Fairseq) | 이 조사에서 원 논문의 한국어 실험은 찾지 못함 | 낮음 — 생성기다 | 제약을 강제로 넣어 문맥상 부적절한 위치에 배치(2절 WMT21 이 "끝에 덧붙이기" 꼼수를 지적) |
| 인라인 주석 학습(Dinu/Exel) | 학습 후 디코딩은 위와 동일 | + 학습 데이터 · 주석에 쓴 용어집 스냅샷 | 가능 | Dinu 는 en–de. Exel 의 추가 언어쌍은 스니펫에서 확인 불가 | 낮음 | 소프트 제약이라 용어가 빠질 수 있음(Bogoychev 의 "soft constraint" 서술과 같은 성질 — 💭) |

### Gaps
- Hokamp & Liu 2017 원문(ACL Anthology P17-1141 로 알려짐)은 열지 못했다 — 서술은 Post & Vilar 의 인용에 의존한다.
- Exel et al. 2020 의 추가 언어쌍, Dinu et al. 의 append vs replace 성능 비교 수치는 스니펫에 없었다.
- 제약 디코딩을 en→ko 에 적용한 논문은 이번 검색에서 찾지 못했다.

## 2. WMT 용어 공유 과제(Terminology shared tasks) 2021 · 2023 · 2025 · 2026 — 설정, 지표, 언어쌍, 결과

### Takeaway
**한국어가 들어간 WMT 용어 과제는 2021년(en→ko, COVID-19, TICO-19 용어)뿐이다.** 2023(zh→en, en→cs, de→en), 2025(en→de/es/ru/zh 등, 금융·IT), 2026(es→eu, en→pl, en↔zh-Hant)에는 한국어가 없다. 과제가 거듭될수록 "용어 정확도(success rate)" 외에 **문서 단위 용어 일관성(consistency)** 이 별도 지표로 자리 잡았고, 2025 결론은 "정확한 용어집을 주면 품질과 용어 정확도가 함께 오른다(특히 좋은 MT 일수록)".

### Cited Findings
**WMT 2021 (Alam et al., WMT21 pp.652–663)**
- 의료·COVID-19 도메인, 5개 언어쌍: en→fr, en→zh, en→ru, **en→ko**, cs→de — [ACL Anthology 2021.wmt-1.69](https://aclanthology.org/2021.wmt-1.69); 언어쌍·용어 출처는 [검색 결과 요약(WMT21 PDF 스니펫)](https://aclanthology.org/2021.wmt-1.69.pdf)
- 한국어 쌍의 용어집은 공개된 **TICO-19 테스트 데이터**에서 왔고, 원래 개발·테스트 데이터가 이 용어집 제약 아래 만들어지지 않았기 때문에 주최 측이 데이터를 용어집에 맞게 고쳤다 — [WMT21 Findings PDF (스니펫)](https://aclanthology.org/2021.wmt-1.69.pdf)
- 저자 명단에 Kweonwoo Jung 포함 — [ACL Anthology 2021.wmt-1.69](https://aclanthology.org/2021.wmt-1.69)
- 지표: 정확 일치(exact match, 출력을 표제어화(lemmatize)해 표제어와 표층형 모두로 대조), 창 겹침(window overlap, 2·3 토큰 창), 1-TERm, 그리고 BLEU 등 — [CUNI WMT21 시스템 논문 arXiv 2109.09350](https://arxiv.org/html/2109.09350); [Alam et al. 2021, arXiv 2106.11891](https://arxiv.org/abs/2106.11891)
- 결론(초록): 용어를 제대로 다루는 방법과 **과제의 정식화·평가 방법 자체**에 더 연구가 필요하다 — [ACL Anthology 2021.wmt-1.69](https://aclanthology.org/2021.wmt-1.69)

**WMT 2023 (Semenov, Zouhar, Kocmi, Zhang, Zhou, Jiang; WMT23 pp.663–671)**
- 언어쌍 zh→en, en→cs, de→en. 세 조건: Base(용어집 없음) · Proper(용어집) · Random(무작위로 고른, 정렬은 맞는 원문→참조 구) — [WMT23 Findings](https://aclanthology.org/2023.wmt-1.54); [과제 슬라이드](https://wmt-terminology-task.github.io/wmt_terminology_2023_slides.pdf)
- 지표: chrF · COMET · COMET-Kiwi(전반 품질) + consistency · success rate. success rate 는 **정규식(regex) 또는 퍼지 매칭(fuzzy matching)** 으로, 표층 토큰 또는 표제어 기준으로 계산 — [과제 슬라이드](https://wmt-terminology-task.github.io/wmt_terminology_2023_slides.pdf)
- 결과: 어떤 사전이든 주면 chrF·COMET 이 오르지만, consistency·success rate 는 Proper 용어집에 더 반응. 시스템 순위는 chrF·COMET·success rate 에서 비슷하나 **consistency 에서는 달랐다** — [과제 슬라이드](https://wmt-terminology-task.github.io/wmt_terminology_2023_slides.pdf)
- 초록의 결론: 결과가 "용어가 번역 의미의 핵심(crux)" 이라는 시각에 도전하며, 일부는 지표가 용어 중심이 아니기 때문일 수 있다 — [ACL Anthology 2023.wmt-1.54](https://aclanthology.org/2023.wmt-1.54)
- 테스트 데이터·용어집·제출물이 Hugging Face `zouharvi/wmt-terminology-2023` 에 공개 — [HF README](https://huggingface.co/datasets/zouharvi/wmt-terminology-2023/blob/main/README.md)

**WMT 2025 (Semenov et al., "Terminology is Useful Especially for Good MTs", WMT25 pp.554–576)**
- Track 1(문장·문단) 13팀 20시스템, Track 2(문서 단위) 4팀. "정확한 용어를 주면 전반 품질과 용어 정확도가 일관되게 오르고, 무작위 용어는 이득이 작다" — [WMT25 Findings (preview)](https://preview.aclanthology.org/setup/2025.wmt-1.30); [statmt PDF](https://www2.statmt.org/wmt25/pdf/2025.wmt-1.30.pdf)
- 과제 페이지: en→de/es/ru/zh(+ 저자원 유럽어는 추후 공지), 금융·IT 도메인, 문장/문단 트랙과 문서 트랙. 초기 공고는 zh→en 도 포함 — 최종 목록은 Findings 표로 확인 필요 — [WMT25 과제 페이지](https://www2.statmt.org/wmt25/terminology.html); [LINGUIST List 36.1825](https://linguistlist.org/issues/36/1825/)
- 일관성 지표: "한 텍스트 안에서 같은 원문 용어의 모든 번역을 비교하여, **가장 일관된 번역에서 벗어난 비율**" 로 측정. 정답 여부와 무관. 문서 트랙에서 더 중요하지만 두 트랙 모두 사용. no-term · random 모드의 출력도 **proper 용어집 기준으로** 채점. 정의는 Semenov & Bojar 2022 를 가리킴 — [WMT25 과제 페이지](https://www2.statmt.org/wmt25/terminology.html); [wmt25-terminology 저장소(검색 요약)](https://github.com/wmt-conference/wmt25-terminology)
- 참가 논문 보고: random 모드의 용어 정확도(0.77–0.96)가 proper(약 0.40–0.55)보다 훨씬 높게 나왔는데, 무작위 단어는 대개 일반어·불용어라서다 — [Lingua Custodia WMT25, arXiv 2510.17504](https://arxiv.org/pdf/2510.17504)
- random 모드의 목적: 품질 향상이 "용어 반영" 때문인지 "정답 일부를 본 것" 때문인지 가르기 — [WMT25 과제 페이지](https://www2.statmt.org/wmt25/terminology.html)

**WMT 2026 (진행 중)**
- 언어쌍 es→eu, en→pl, en→zh-Hant, zh-Hant→en, 공학·의학·금융. 문서 트랙은 명시적 사전 유지, 문장 트랙은 더 어려운 용어 중심 과제로 교체. 워크숍 2026-10-28~29 부다페스트(EMNLP 2026 동반) — [WMT26 과제 페이지](https://www2.statmt.org/wmt26/terminology.html); LINGUIST 공고는 en→zh-Hant 를 빠뜨려 3쌍으로 적음 — [LINGUIST List 37.2259](https://linguistlist.org/issues/37/2259/)
- 참가 시스템 논문 예: SalamandraTA at WMT 2026 — [arXiv 2609.09999](https://arxiv.org/html/2609.09999v1)

### Inferences
- 💭 WMT 과제 전체가 "용어집이 주어졌을 때 지켰는가" 를 재는 설계다(Proper/Random/None 비교). 즉 **WMT 는 용어집의 옳음을 묻지 않고 준수(adherence)만 묻는다** — ko-dev-terms 의 "승자를 고르지 않는다" 원칙과 같은 분업 위치에 있다.
- 💭 2023 의 "consistency 순위가 다르다" 와 2025 의 일관성 독립 지표화는, **정확도와 일관성이 서로 다른 축**이라는 실증이다. ko-dev-terms 의 증거 행에 "한 말뭉치 안에서 같은 영어 용어의 한국어 표기가 몇 갈래인가" 를 따로 세는 것은 이 축과 대응한다.
- 💭 random 모드에서 정확도가 더 높게 나온 보고는 **단순 문자열 일치 지표가 일반어에 유리**하다는 경고다 — 개발 용어 중 일반어와 겹치는 것(예: "map", "table")의 빈도 측정에도 같은 편향이 있을 수 있다.

#### 기준 판정(과제의 평가 체계로서)
| 항목 | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| WMT21 용어 평가 | 문자열·표제어 지표는 결정적(표제어 분석기 판 고정 시 — 💭) | 테스트셋 · 용어집 · 평가 스크립트 커밋 · 표제어 분석기 | 가능(오픈 코드 — 3절) | **en→ko 포함(TICO-19)** | 높음 — 생성 없이 측정 | 꼼수(용어를 끝에 덧붙이기) 가능 |
| WMT23/25 success rate · consistency | 정규식·퍼지 매칭 설정 고정 시 결정적(💭) | + 퍼지 임계값 · 표제어/표층 선택 | 가능 | 한국어 없음 | 높음 | 일반어에 유리한 편향(random 결과) |

### Gaps
- WMT21 의 **en→ko 쌍별 점수와 한국어 고유 관찰**은 Findings 본문을 열지 못해 확보하지 못했다. 스니펫 범위에서는 en→fr · en→ru · cs→de 결과만 나왔다.
- WMT25 최종 언어쌍 표와 consistency 수치표는 확인하지 못했다.
- WMT26 Findings 는 워크숍 당일(2026-10-28)이라 아직 확인할 수 없다.
- 2024년에는 별도 WMT 용어 과제를 찾지 못했다(검색 결과에 없음 — 부재의 증거로 보지 말 것).

## 3. 용어 지표 — 정확 일치, TERm, 창 겹침, 문서 일관성: 결정적인가, 한국어 용어집 준수 측정에 재사용할 수 있나

### Takeaway
정확 일치(exact match) · 창 겹침(window overlap) · 1-TERm · 일관성(consistency)은 모두 **신경망 없이 계산되는 문자열/편집거리 지표**라서, 토크나이저·표제어 분석기·매칭 설정을 고정하면 결정적이고 오프라인으로 돈다. 다만 정확 일치는 꼼수에 약하고, 창 겹침·TERm 은 **참조 번역이 필요**하며, 일관성 지표는 참조 없이 돈다. ko-dev-terms 의 "말뭉치 안 출현 횟수" 는 정확 일치 계열, "표기 갈래 수" 는 일관성 계열에 해당한다.

### Cited Findings
- Alam, Anastasopoulos 외(2021, arXiv 2106.11891)는 COVID-19 도메인 5개 언어에서 용어 준수 지표를 제안하고 용어 표적 인간 평가도 수행. BLEU 와 용어 정확 일치 사이에 **약한(mild) 상관만** 있었다. 코드 공개: `github.com/mahfuzibnalam/terminology_evaluation` — [arXiv 2106.11891](https://arxiv.org/abs/2106.11891); [Slator 요약](https://tech.slator.com/?p=66831)
- **정확 일치**: 출력을 표제어화하고 표제어·표층형 모두로 대조. 제약 용어를 아무 데나(예: 무제약 번역 끝에) 붙여 넣는 꼼수로 점수를 올릴 수 있다 — [CUNI WMT21, arXiv 2109.09350](https://arxiv.org/html/2109.09350)
- **창 겹침**: 번역문과 참조문 각각에서 제약 용어 주변 n 토큰 창을 뽑아 비슷한 문맥에 놓였는지 비교. 2·3 토큰 창 사용 — [CUNI WMT21, arXiv 2109.09350](https://arxiv.org/html/2109.09350)
- **TERm / 1-TERm**: 용어에 속한 토큰에 더 큰 가중치를 주는 가중 TER. CUNI 는 1-TERm 이 용어 반영보다 **전반 번역 품질에 주로 좌우**됐다고 관찰 — [CUNI WMT21, arXiv 2109.09350](https://arxiv.org/html/2109.09350)
- 창 겹침과 1-TERm 만이 꼼수 시스템을 벌한다 — [검색 요약: Alam et al. 2021](https://arxiv.org/pdf/2106.11891)
- **Semenov & Bojar 2022(WMT22 pp.450–457)**: 텍스트 전체의 용어 일관성·비모호성(unambiguity)을 재는 지표. **참조 번역이 필요 없다.** 수동 조정 매개변수(manually tuned parameters)를 포함할 수 있다. 적합성(adequacy)은 BLEU·chrF 에 맡긴다. cs→en(ELITR 2021 합의 말뭉치, WMT21 뉴스 시스템)에서 일반 지표와 유의하게 다르고 인간 평가와 상관 — [ACL Anthology 2022.wmt-1.41](https://aclanthology.org/2022.wmt-1.41)
- WMT25 일관성: 같은 원문 용어의 번역들 중 최빈(가장 일관된) 번역에서 벗어난 비율 — [WMT25 과제 페이지](https://www2.statmt.org/wmt25/terminology.html)
- WMT23 success rate: 정규식 또는 퍼지 매칭, 표층 토큰 또는 표제어 — [WMT23 슬라이드](https://wmt-terminology-task.github.io/wmt_terminology_2023_slides.pdf)
- 2026년 실무 가이드: 1단계로 **결정적 문자열 매칭**("원문에 원어 용어가 있고 대상에 표준 대역어가 없으면 위반")을 돌리고, 그 밖의 문제에 LLM 판정(LLM-as-judge) 루브릭을 쓰라고 권고(비학술 자료) — [futureagi 블로그 2026](https://futureagi.com/blog/evaluating-llm-translation-quality-2026/)

### Inferences
- 💭 한국어 적용 시 핵심 위험은 **교착어 조사(particle)** 다. "컨테이너를", "컨테이너에서" 처럼 명사 뒤에 조사가 붙으므로, 공백 토큰 단위 정확 일치는 놓치고 부분 문자열(substring) 일치는 "컨테이너화" 같은 파생어까지 센다. WMT21 의 "표제어+표층형 대조" 를 한국어에 쓰려면 형태소 분석기가 필요하고, 그 분석기의 이름·판·사전을 스냅샷에 고정해야 결정성이 유지된다(이 판단은 한국어 형태론 일반 지식에 기댄 추론이며 이번 조사에서 근거 문헌을 찾지 않았다).
- 💭 창 겹침·TERm 은 참조 번역을 요구하므로 "말뭉치에서 후보 표기의 출현 횟수를 센다" 는 ko-dev-terms 의 측정에는 직접 맞지 않는다. 반면 **Semenov & Bojar 식 일관성 지표는 참조 없이** 돌므로, Kubernetes/MDN/python-docs-ko 의 "한글(English)" 괄호 패턴처럼 영어 원어가 명시돼 정렬이 공짜로 얻어지는 문장에서 "같은 영어 용어 → 한국어 표기 분포" 를 재는 데 그대로 쓸 수 있다.
- 💭 "0 은 0 으로 보고" 원칙은 정확 일치 지표와 궁합이 맞다 — 지표가 존재/부재만 세므로 해석이 끼지 않는다.

#### 기준 판정
| 지표 | ① 결정성 | ② 고정 대상 | ③ 로컬 | ④ 한국어 근거 | ⑤ 검증기 | ⑥ 실패 양상 |
|---|---|---|---|---|---|---|
| 정확 일치(표층/표제어) | 결정적(💭 설정 고정 시) | 토크나이저 · 표제어/형태소 분석기 판 · 용어집 스냅샷 | 가능 | WMT21 en→ko 에 쓰였음(점수 미확인) | **높음** | 꼼수 · 일반어 편향 · 조사 결합 |
| 창 겹침(2·3 토큰) | 결정적(💭) | + 참조 번역 · 토큰화 | 가능 | 위와 같음 | 참조가 있을 때만 | 토큰화 의존 |
| 1-TERm | 결정적(💭 TER 계열) | + 참조 · 가중치 | 가능 | 위와 같음 | 참조가 있을 때만 | 전반 품질에 끌려감(CUNI) |
| 일관성(Semenov & Bojar / WMT25) | 결정적(💭) | + 수동 조정 매개변수 · 용어 정렬 방법 | 가능 | 한국어 적용 사례 미발견 | **높음 · 참조 불요** | 일관되게 틀린 번역도 만점(정답과 무관하게 설계됨) |

### Gaps
- TERm 의 정식 정의(가중치 값)는 스니펫에 없었다.
- Semenov & Bojar 2022 의 점수 공식은 스니펫에 없었다.
- `terminology_evaluation` · `wmt25-terminology/term-consistency` 코드가 한국어 형태소 분석을 지원하는지는 GitHub 접근이 막혀 확인하지 못했다.

## 4. LLM 의 용어 준수 — 프롬프트 내 용어집, 용어 DB 검색 증강(RAG), 일관성·용어 환각 (2023–2026), en–ko 결과

### Takeaway
프롬프트에 용어집을 넣거나 검색으로 주입하면 대체로 용어 정확도가 오르지만(DiPMT 2023, Moslem 2023, WMT25, 2026 사례 연구), **어느 연구도 LLM 이 용어를 반드시 지킨다고 보장하지 않는다** — 저자들 스스로 "소프트 제약" 이라 부르고, 모호한 용어에서는 프롬프트 용어집이 오히려 정확도를 낮춘 보고도 있다. 그리고 **검색된 지식이 LLM 이 생성한 지식보다 일관되게 낫다**(Li et al. 2025). en–ko 직접 근거는 괄호 병기 용어 번역(PTT, WMT 2024)과 ja→ko 특허 용어집 연구 정도다.

### Cited Findings
**프롬프트 내 사전·용어집**
- **DiPMT(Ghazvininejad, Gonen, Zettlemoyer 2023, Meta)**: 원문 일부 단어의 사전 대역어 후보를 프롬프트에 넣어 구 단위 제어. 희귀어가 LLM 번역의 약점이며, 저자원·도메인 외(out-of-domain) MT 에서 기준선보다 낫다 — [arXiv 2302.07856 (ar5iv)](https://ar5iv.labs.arxiv.org/html/2302.07856)
- **Moslem et al. 2023(WMT23)**: LLM 으로 용어집 기반 합성 병렬 데이터를 만들어 MT 를 미세조정하고, 필요한 용어가 빠진 번역을 LLM 이 사후 편집. 필요 용어 출현율 약 36.67% → 약 72.88% — [ACL Anthology 2023.wmt-1.82](https://aclanthology.org/2023.wmt-1.82); [arXiv 2310.14451](https://arxiv.org/abs/2310.14451v1)
- **Bogoychev & Chen 2023**: LLM 에 용어 제약을 주고 가설을 다듬게 하면 용어 재현율(recall)이 더 오르지만, "부정 제약 디코딩이나 LLM 이 재생성에서 제약을 반드시 반영한다는 보장이 없으므로 둘 다 **소프트 제약**" — [ACL Anthology 2023.wmt-1.80](https://aclanthology.org/2023.wmt-1.80); [arXiv 2310.05824](https://arxiv.org/abs/2310.05824v1)
- **DuTerm(Jaswal 2025, WMT25 pp.1344–1350)**: 용어 인지 NMT 초안 + GPT-4o 프롬프트 사후 편집. **엄격한 제약 강제보다 문맥 기반의 유연한 용어 처리**가 더 나은 번역을 냈고, LLM 은 1차 생성기보다 문맥 기반 편집자로 잘 작동한다고 결론 — [arXiv 2511.07461](https://arxiv.org/html/2511.07461v1)
- 모호한 용어에 대한 선호 최적화 논문: 프롬프트에 용어 사전을 준 GPT-4.1 의 정답 용어 정확도가 43.5% → 37.1% 로 떨어졌다고 보고(검색 요약 기준, 원문 미확인) — [arXiv 2507.03580](https://arxiv.org/pdf/2507.03580)

**검색 증강(Retrieval) vs 생성(Generation)**
- **Li, Luo, Briakou, Cherry 2025(Google/UPenn)**: 도메인 적응 LLM 번역에서 "**예시(demonstrations)가 용어보다 일관되게 낫고, 검색이 생성보다 일관되게 낫다**". 약한 모델이 예시를 생성하면 큰 모델의 제로샷 성능과의 격차를 좁힐 수 있다. 실험용 은(silver) 용어 사전은 같은 병렬 말뭉치를 LLM 이 분석해 만들었다. 검색 방식은 고품질 도메인 자원(병렬 예시 풀, 용어 풍부한 이중어 사전)이 필요해 비싸다 — [arXiv 2503.05010](https://arxiv.org/html/2503.05010v1); [KnowledgeNLP 2025 PDF](https://preview.aclanthology.org/fix-sig-urls/2025.knowledgenlp-1.7.pdf)
- 2026 EAMT 사례 연구(암각화 문서, es→en, 감사한 용어 출현 194건): 용어집 검색 설정 정확 일치 81.4% · 기본 프롬프트 LLM 69.1% · DeepL 64.4%. DA 평균은 85.3 vs 85.2 로 전반 품질은 같음. 단일 텍스트 표본 — [arXiv 2605.14679](https://arxiv.org/abs/2605.14679); [ACL Anthology 2026.eamt-1.49](https://aclanthology.org/2026.eamt-1.49/)
- 업체 연구(비심사): 언어쌍당 72개 용어를 검색 주입하자 5개 LLM 제공자에서 용어 오류가 16.6%–44.6% 감소. 첫 시도(37개 용어)는 용어집 적중이 적어 효과 없음 — [Lingo.dev](https://lingo.dev/en/research/retrieval-augmented-localization)
- WMT25 Findings: 정확한 용어집이 품질·용어 정확도 모두를 끌어올린다 — [WMT25 Findings](https://preview.aclanthology.org/setup/2025.wmt-1.30)

**일관성·환각**
- **Guerreiro et al. 2023(TACL 11, pp.1500–1517)**: 100개 이상 언어쌍에서 M2M NMT 와 GPT 계열 LLM 의 환각 분석. 환각은 **저자원 방향과 영어에서 나가는(out of English) 방향**에 몰리고, LLM 의 환각은 NMT 와 질적으로 다르며, 같은 데이터로 규모만 키워서는 잘 줄지 않는다. 다른 데이터·절차로 학습한 다양한 대체(fallback) 시스템이 특정 병리를 거의 없앤다 — [ACL Anthology 2023.tacl-1.85](https://aclanthology.org/2023.tacl-1.85)
- 대형 추론 모델(LRM) 번역 연구는 핵심어 통일(keyword unification)·대명사·어조 일관성이 문서 단위 MT 에서 특히 문제라고 서술 — [arXiv 2503.10351](https://arxiv.org/pdf/2503.10351)
- LLM-BT-Terms(역번역으로 용어 표준화): "agentic framework" 같은 신생 용어는 표준 번역이 없어 정확 일치율이 낮다 — [arXiv 2506.08174](https://arxiv.org/pdf/2506.08174)

**en–ko · 한국어 관련**
- **괄호 병기 용어 번역(Parenthetical Terminology Translation, PTT; Myung et al., WMT 2024 pp.1410–1427)**: 한국어 번역 옆에 영어 원어를 괄호로 병기. 동기는 "fine-tuning" 이 "파인튜닝" 과 "미세조정" 으로 갈리는 **한국어 표기 불일치**. 데이터는 GPT-4o-mini/GPT-4-turbo 기반 4개 에이전트(Writer·Translator·Evaluator·Executor)가 생성 — 1,398 en–ko 문장쌍, 233 용어 군집(699 고유 용어). 이후 HF 의 `PTT_advanced_en_ko` 는 1,063 문장쌍으로 수치가 다르다. 소형 NMT·소형 LLM 으로 지식 증류(knowledge distillation), Qwen2 1.5B · Llama-3-KoEn-8B 체크포인트 공개 — [arXiv 2410.00683](https://arxiv.org/html/2410.00683v1); [WMT24 PDF](https://preview.aclanthology.org/dois-2013-emnlp/2024.wmt-1.129.pdf); [HF 데이터셋](https://huggingface.co/datasets/PrompTartLAB/PTT_advanced_en_ko/blame/main/README.md); [HF 모델](https://huggingface.co/PrompTartLAB/qwen2_1.5B_PTT_en_ko)
- WMT 2024 특허 번역(ja→ko): ChatGPT 는 용어집이 없으면 점수가 낮지만 용어집을 주면 크게 오르고, 용어집 사용을 학습한 모델이 용어집을 받은 ChatGPT 보다 낫다. **ChatGPT 가 때때로 용어집 항목을 제대로 적용하지 못하고 일본어 용어를 그대로 출력** — [WMT24 pp.636–642](https://www2.statmt.org/wmt24/pdf/2024.wmt-1.51.pdf)
- SemEval-2025 Task 2(Team ACK): en–ko 에서 13개 LLM·NMT 를 개체명이 든 문화 간 텍스트로 평가 — [arXiv 2504.20451](https://arxiv.org/pdf/2504.20451)
- DaCoM(COLING 2025 Industry, HD한국조선해양 AI센터): 도메인 용어집 + LLM + NMT 혼합 파이프라인으로 조선 도메인 데이터셋 구축. 도메인 포함 여부에 따라 BLEURT 최대 53.7점 차 — [ACL Anthology 2025.coling-industry.53](https://aclanthology.org/2025.coling-industry.53.pdf)

### Inferences
- 💭 **PTT 는 ko-dev-terms 가 고른 근거원("한글(English)" 패턴)과 같은 표기 관습을 MT 출력 형식으로 채택한 연구**다. 다만 PTT 데이터는 LLM 에이전트가 생성한 것이라, ko-dev-terms 의 기준으로는 "candidate source = LLM (inference)" 행에 해당하고 근거 말뭉치로 쓸 수 없다.
- 💭 Li et al. 2025 의 "검색 > 생성" 은 ko-dev-terms 의 설계(검색된 용어집·말뭉치 행이 1차, LLM 후보는 표지를 붙인 2차)를 지지하는 가장 직접적인 실험 근거다. 단 그 실험은 번역 품질을 잰 것이지 한국어 표기 근거를 잰 것이 아니다.
- 💭 "소프트 제약"(Bogoychev), "용어집 미적용·원어 그대로 출력"(ja→ko 특허), "모호어에서 정확도 하락"(2507.03580)을 합치면: **LLM 은 용어 판정자로 쓸 수 없고**, 출력은 결정적 문자열 검사로 사후 확인해야 한다.

#### 기준 판정
| 방법 | ① 결정성 | ② 고정 대상 | ③ 로컬 | ④ 한국어 근거 | ⑤ 검증기 | ⑥ 실패 양상 |
|---|---|---|---|---|---|---|
| 프롬프트 내 용어집(DiPMT 류) | 아니오 — 호스팅 LLM 은 T=0 에서도 비결정(6절) | 모델 ID·판 · 프롬프트 원문 · 용어집 스냅샷 · seed · (가능하면) system_fingerprint | 로컬 LLM 이면 가능, 결정성은 vLLM 배치 불변 모드 등 필요(6절) | ja→ko 특허(용어집 미적용 사례), PTT(en–ko) | 아니오 — 생성기·판정자 | 소프트 제약, 원어 잔류, 모호어 오판 |
| 검색 증강 용어(RAG) | 검색 단계는 결정적(💭 색인 고정 시), 생성 단계는 비결정 | + 색인 스냅샷 · 검색기 설정 · top-k | 가능 | 직접 en–ko 연구 미발견 | 검색 단계만 측정기로 재사용 가능(💭) | 적중이 적으면 효과 없음(Lingo.dev 37개 시도) |
| LLM 사후 편집(Moslem, DuTerm) | 아니오 | 위와 같음 | 조건부 | 미발견 | 아니오 | 보장 없음(소프트) |

### Gaps
- **en→ko 에서 LLM 의 용어집 준수율·용어 환각률을 정량화한 논문은 찾지 못했다.** 소프트웨어 UI 문자열 en→ko 벤치마크도 찾지 못했다.
- "용어 환각(term hallucination)" 을 독립 범주로 측정한 문서 단위 기술 번역 연구는 이번 검색에서 나오지 않았다 — 관련 증거는 일반 MT 환각(Guerreiro)과 일관성 서술(2503.10351)뿐이다.
- 2507.03580 의 43.5→37.1% 수치는 스니펫 요약에만 근거하며 실험 조건을 확인하지 못했다.
- 검색 결과에 인용된 "Kim et al. (2024) — 용어 탐지 → 용어 DB 구축 → 번역 전 용어 정보 검색" 은 원 논문을 찾지 못해 다룰 수 없다.

## 5. 생성 후 검증(Generate-then-verify) 설계 — LLM 이 후보를 내고 결정적 단계가 말뭉치·용어 DB 로 확인하는 사례, 재현을 위한 기록·고정

### Takeaway
"LLM 이 한국어 후보를 내고, 결정적 단계가 말뭉치 빈도로 검증한다" 는 **정확히 같은 파이프라인의 출판 사례는 찾지 못했다.** 가장 가까운 것은 (a) 번역 출력에 대해 *결정적 검사 → 생성적 수리* 를 도는 WMT 시스템(Bogoychev & Chen 2023, Moslem 2023), (b) LLM 이 용어 정렬 초안을 내고 **사람이** 검토하는 WMT25 시스템·법률 용어 DB 다. 즉 문헌의 "검증" 은 대개 사람이거나, 검증 대상이 *번역 출력*이지 *후보 용어*가 아니다.

### Cited Findings
- **Bogoychev & Chen 2023**: 번역 후 단어 정렬로 용어 위반을 **탐지**하고, 위반 시 해당 단어에 부정 제약(negative constraint)을 걸어 재디코딩하거나 LLM 에 제약을 주어 다듬는다 — 탐지(정렬 검사)와 수리(생성)가 분리된 구조 — [arXiv 2310.05824](https://arxiv.org/abs/2310.05824v1)
- **Moslem et al. 2023**: 필요한 용어가 **빠진** 번역만 골라 LLM 이 사후 편집 — [ACL Anthology 2023.wmt-1.82](https://aclanthology.org/2023.wmt-1.82)
- WMT25 참가 시스템: GPT-4.1 에 원문·번역 문서쌍을 주어 용어를 식별·정렬하게 한 뒤 **저자 두 명이 독립적으로 검토·수정**. 수정 대부분은 이미 표준 번역이 있는 일반 개체명을 지우는 것이었다. 검색 요약이 이 서술을 WMT25 용어 과제 자료로 묶어 보여 줬지만 **어느 참가 논문인지는 특정하지 못했다** — [검색 결과에 함께 나온 WMT25 Findings PDF](https://www2.statmt.org/wmt25/pdf/2025.wmt-1.30.pdf)
- IRB-MT(WMT25): "지표 유도 다중 에이전트(metric-guided multi-agent)" 방식 — 제목 수준 정보만 확보 — [ACL Anthology 2025.wmt-1.110](https://aclanthology.org/2025.wmt-1.110/)
- 다국어 법률 용어 매핑(Springer AI & Law 2025): 언어 모델과 **도메인 전문가 검증**을 결합한 다중 에이전트 + 인간 개입(human-in-the-loop) 체계, LLM 이 접근할 수 있는 용어 DB 를 지향. 단일 언어 용어 추출의 고전 기준선은 TF-IDF·TextRank — [Springer 2025](https://link.springer.com/article/10.1007/s10506-025-09490-6)
- Li et al. 2025: 은(silver) 용어 사전을 LLM 이 병렬 말뭉치에서 분석해 생성 — LLM 생성 용어집을 *입력*으로 쓴 예이며 검증 단계는 스니펫에 없다 — [arXiv 2503.05010](https://arxiv.org/html/2503.05010v1)
- 기록·고정: OpenAI 는 `seed` 와 함께 응답의 `system_fingerprint` 를 감시하라고 하고, 실무 글은 seed · 매개변수 · fingerprint 를 매 실행마다 저장하라고 권한다 — [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter); [Typefully 글](https://typefully.com/capeandcode/achieving-reproducible-outputs-with-openai-trfbtpM)
- 실무 가이드(2026): 결정적 문자열 매칭을 1단계 검사로, LLM 판정은 그 다음 — [futureagi 블로그](https://futureagi.com/blog/evaluating-llm-translation-quality-2026/)

### Inferences
- 💭 문헌의 공통 구조는 **"결정적 탐지기 + 비결정적 생성기"** 의 분리다(정렬 검사 → 재생성, 누락 검사 → 사후 편집). ko-dev-terms 는 이 구조에서 *수리 단계를 버리고 탐지 단계만 남긴* 형태로 볼 수 있다: LLM 후보 → 말뭉치 정확 일치 횟수(0 포함) 보고, 승자 선택 없음.
- 💭 재현을 위해 LLM 후보 행에 기록할 최소 집합(이번 조사의 근거로부터 도출): 모델 ID·판(별칭이 아닌 고정 ID), 프롬프트 원문 해시, 온도·top-p·seed, 제공자가 주면 `system_fingerprint`, 호출 시각, 그리고 **원 응답 텍스트 자체**. 6절 근거상 같은 설정으로 재호출해도 같은 후보가 나온다는 보장이 없으므로, "재생성으로 재현" 이 아니라 **"기록된 응답을 재검증으로 재현"** 하는 것이 맞다 — 검증 단계(말뭉치 카운트)는 스냅샷 해시만 같으면 결정적으로 재현된다.
- 💭 이 분리 덕분에 ①결정성 요구는 *검증 단계에만* 걸린다. 후보 생성의 비결정성은 "LLM (inference)" 표지와 원응답 보존으로 격리된다.

#### 종합 기준 판정 — 결정적(측정) vs 추론(후보 생성)
| 역할 | 해당 방법 | ① | ③ | ⑤ |
|---|---|---|---|---|
| **결정적 측정·검증** | 정확 일치/표제어 일치, 일관성 지표, 정렬 기반 위반 탐지, 색인 검색 단계 | 예(설정·스냅샷 고정 시, 💭) | 예 | 예 |
| **추론(후보 생성)** | LLM 프롬프트(용어집 유무), LLM 사후 편집, LLM 생성 은 사전, LLM 정렬 초안 | 아니오(6절) | 조건부 | 아니오 — 판정자로 쓰면 소프트 제약·환각이 그대로 결론이 된다 |
| 생성기지만 결정적일 수 있음 | 제약 디코딩·용어 인지 학습 NMT(로컬) | 알고리즘상 예, 커널 배치 불변성은 별도(💭) | 예 | 아니오(생성기) |

### Gaps
- LLM 이 *용어 후보*(번역 출력이 아님)를 내고 *말뭉치 빈도*로 자동 검증하는 출판 사례는 찾지 못했다.
- IRB-MT 의 "지표 유도" 가 결정적 지표로 LLM 출력을 걸러내는지는 본문을 열지 못해 확인 불가.

## 6. 온도 0 에서도 LLM API 가 비결정적이라는 증거 (2023–2026)

### Takeaway
온도 0(temperature 0)은 결정성을 보장하지 않는다. 학술 측정(Atil et al.: 정확도 최대 15% 요동), 원인 분석(Thinking Machines 2025: 서버 부하에 따른 배치 크기 변화 + 배치 불변이 아닌 커널), 그리고 **제공자 문서 자체**(OpenAI "결정성은 보장되지 않음", Azure "변동이 드물지 않음", Anthropic "온도 0.0 에서도 완전히 결정적이지 않음")가 일치한다. 로컬에서는 vLLM 의 배치 불변(batch invariance) 모드로 결정성을 얻을 수 있으나 베타이고 GPU 조건이 있다.

### Cited Findings
- **Atil et al.(arXiv 2408.04667)**: "결정적으로 설정한" 5개 LLM 을 8개 과제(BBH·MMLU)에 10회씩, 제로샷·퓨샷으로 실행. 자연 발생 실행 간 정확도가 **최대 15%** 요동하고, 가능한 최고·최저 성능 격차는 **최대 70%**. 원출력 전체 일치율 TARr@N 과 파싱된 답 일치율 TARa@N 을 도입. 코드·데이터 `github.com/breckbaldwin/llm-stability` — [arXiv 2408.04667](https://arxiv.org/abs/2408.04667)
  - 제3자 요약은 GPT-4o 의 TARr 중앙값 약 3%, GPT-3.5 Turbo 약 97% 라고 전하지만 원문 대조를 못 했다 — [Emergent Mind](https://www.emergentmind.com/papers/2408.04667)
- **Thinking Machines Lab(Horace He 외, 2025-09, 블로그·비심사)**: 흔한 "동시성 + 부동소수점" 가설 대신, **추론 커널의 배치 불변성 결여**가 진짜 원인이며 서버 부하에 따라 배치 크기가 비결정적으로 바뀌는 것이 거의 모든 추론 엔드포인트가 비결정적인 주된 이유라고 주장. 배치 불변 커널로 vLLM 에서 Qwen3-8B 를 결정적으로 돌리는 PyTorch 구현 공개, 대가로 속도 저하 — [Simon Willison 요약](https://simonwillison.net/2025/Sep/11/defeating-nondeterminism); [Medium 해설](https://medium.com/@siddhantg314/defeating-nondeterminism-in-llm-inference-in-practice-38a7dd1e4112). 처리량 34–60% 감소·1,000회 동일 출력 수치는 2차 출처라 미검증 — [morphllm](https://www.morphllm.com/defeating-nondeterminism-llm-inference)
- **OpenAI(2023-11~)**: `seed` 로 "(대체로) 일관된((mostly) consistent)" 출력을 얻는다. "결정성은 보장되지 않으며 백엔드 변화는 `system_fingerprint` 로 감시하라." fingerprint 는 요청 매개변수가 바뀌거나 **서빙 인프라의 수치 설정이 바뀔 때(1년에 몇 차례)** 바뀌고, 매개변수와 fingerprint 가 같아도 작은 확률로 응답이 다를 수 있다 — [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter)
- **Microsoft Azure OpenAI**: seed 와 system_fingerprint 가 같아도 "응답에 어느 정도 변동이 관찰되는 것이 현재 드물지 않다" — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reproducible-output)
- **Anthropic**: SDK 생성 참조 문서의 `temperature` 설명 — "온도 0.0 에서도 결과는 완전히 결정적이지 않다(Note that even with temperature of 0.0, the results will not be fully deterministic)." docs.anthropic.com 원문은 직접 열지 못했고 SDK 참조·제3자 미러로 확인 — [anthropic-sdk-ruby rubydoc](https://rubydoc.info/github/anthropics/anthropic-sdk-ruby/main/Anthropic%2FModels%2FBeta%2FMessageCreateParams:temperature); [CAMEL-AI 문서](https://docs.camel-ai.org/reference/camel.configs.anthropic_config). Anthropic API 에 seed 매개변수가 없다는 제3자 서술은 확인하지 못했다.
- **vLLM 배치 불변 모드**: `VLLM_BATCH_INVARIANT` 환경 변수로 켜며, 출력이 배치 크기·요청 순서에 의존하지 않게 하는 것이 목표. 예시는 고정 seed·온도와 함께 쓰고 성능 비용이 있다. **베타**. GPU 요건이 문서 판마다 다름(stable: compute capability 8.0 이상, latest: 9.0 이상 — H100/H200/B100/B200). 검증된 계열: Llama 3, Qwen2.5, Qwen3, GPT-OSS, DeepSeek, Mistral 7B v0.3 — [vLLM stable 문서](https://docs.vllm.ai/en/stable/features/batch_invariance/); [vLLM latest 문서](https://docs.vllm.ai/en/latest/features/batch_invariance/)
- 2026 단신(arXiv 2604.22411): 명목 T=0 에서도 구현 의존적 섭동으로 남는 실효 무작위성을 "배경 온도(background temperature)" 로 형식화 — [arXiv 2604.22411](https://arxiv.org/html/2604.22411v1)
- arXiv 2601.06118: 비결정성을 출력 문자열 비교가 아니라 토큰 확률의 불확실성으로 다루는 지표 제안 — [arXiv 2601.06118](https://web3.arxiv.org/pdf/2601.06118)

### Inferences
- 💭 ko-dev-terms 의 "같은 입력 + 같은 스냅샷 = 같은 출력" 요구는 **호스팅 LLM 후보 생성에는 원리적으로 걸 수 없다** — 제공자 셋이 문서로 부정한다. 그래서 LLM 후보 행은 *재생성 가능성*이 아니라 *기록된 원응답 + 메타데이터*로 재현성을 확보해야 한다(5절 추론과 같음).
- 💭 로컬 실행으로 결정성을 원하면 "로컬" 만으로는 부족하고 **배치 불변 커널**(vLLM 모드)과 GPU 조건이 함께 필요하다. CPU 전용 llama.cpp 의 결정성은 이번 조사에서 근거를 찾지 못했다.

#### 기준 판정(후보 생성기로서의 LLM 실행 방식)
| 실행 방식 | ① | ② 고정 대상 | ③ | ⑥ |
|---|---|---|---|---|
| 호스팅 API, T=0 | 아니오(제공자 문서) | 모델 ID · seed(있으면) · system_fingerprint(있으면) · 원응답 저장 | 아니오 | fingerprint 변경 연 수회(OpenAI), 같은 설정에서도 변동 |
| 로컬 vLLM + 배치 불변 모드 | 목표상 예(베타) | 모델 가중치 해시 · vLLM 판 · GPU 종류 · seed · 온도 | 예(GPU 조건) | 미검증 모델, 성능 비용 |

### Gaps
- Atil et al. 의 모델별 TARr 수치를 원문에서 확인하지 못했다.
- Google(Gemini/Vertex)의 결정성 관련 공식 문구는 이번에 검색하지 않았다.
- llama.cpp · Ollama 등 CPU 로컬 추론의 실행 간 결정성에 대한 근거 문서는 찾지 못했다.

## 7. 한국어 기술 문서의 번역투·MT 유발 용어 오류(소프트웨어 용어 직역 등) 연구

### Takeaway
한국어 소프트웨어 용어의 직역·번역투를 **직접** 다룬 학술 연구는 이번 검색에서 찾지 못했다. 가까운 근거는 (a) 특허·법률 한영 MT 평가에서 용어 오류가 빈번하다는 KCI 연구(방향은 ko→en), (b) 한국어 표기 불일치("파인튜닝"/"미세조정")를 동기로 한 PTT(WMT 2024), (c) 비학술 실무 사례("backpressure" → "배압") 정도다.

### Cited Findings
- 이지은·최효은(번역학연구 24권 1호, 2023): 인공신경망 기반 맞춤형 MT 엔진의 법률·특허 **한영** 번역 평가 — 용어 문제가 빈번했고, 특허 MT 에서 법령 MT 보다 용어 문제가 더 광범위. 한국어 대응어가 같은 전문용어 쌍에서 오류가 많았다(예: passivation film 을 passivation layer 로) — [KCI ART002945403](https://journal.kci.go.kr/kats/archive/articlePdf?artiId=ART002945403)
- 번역학 연구: 직역식 MT 의 특성에 따른 오류와 창의성 부족으로 출판 가능 품질에 못 미친다는 평가(검색 요약) — [번역학연구 25(2), 2024](https://journal.kci.go.kr/kats/archive/articlePdf?artiId=ART003092847)
- 온라인 MT(Google·Papago·Kakao) 오류 분석 — 사회문화적 의미 표현의 한계 — [KCI ART002616585 / 언어연구 36(2), 2020](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002616585)
- PTT 의 동기: "fine-tuning" 이 "파인튜닝" 또는 "미세조정" 으로 갈리는 한국어 표기 불일치 — [arXiv 2410.00683](https://arxiv.org/html/2410.00683v1)
- 비학술 사례: 개발 문서에서 "backpressure" 를 "배압"(기계공학 용어)으로 옮긴 것을 번역투로 지적하고 "백프레셔" 또는 증상 서술을 제안한 GitHub 이슈 — [nil-park/claude-workflow-kit #11](https://github.com/nil-park/claude-workflow-kit/issues/11)
- 한국 OTT 현지화 문헌 리뷰(2026): LLM 사후 편집이 초안 품질·생산성을 높이지만 경어 등급·문화 결속 표현은 현재 LLM 역량 밖 — [MDPI Information 17(9):835](https://www.mdpi.com/2078-2489/17/9/835)

### Inferences
- 💭 "배압" 사례는 **다른 도메인에 이미 자리 잡은 한국어 용어로 직역되는 오류**(도메인 간 동형 충돌)의 전형이다. ko-dev-terms 의 증거 행 관점에서는, 후보 "배압" 의 개발 문서 말뭉치(Kubernetes/MDN/python-docs-ko) 빈도가 0 또는 낮고 다른 도메인 말뭉치에서 높다면 그 대비 자체가 측정 가능한 신호다 — 다만 이것은 도구가 *판정*하지 않고 행으로만 보여야 한다.
- 💭 PTT 와 KCI 연구 모두 "같은 영어 용어 → 여러 한국어 표기" 를 문제로 본다 — 3절 일관성 지표로 정량화할 수 있는 현상이다.

### Gaps
- 한국어 소프트웨어 용어의 MT 직역 오류율·번역투 분류를 다룬 KCI/HCLT 논문은 이번 검색에서 찾지 못했다(검색 1회 — 부재의 증거가 아님). KCI 에서 "번역투" + "IT 용어" 조합으로 추가 검색이 필요하다.
- HCLT(한글 및 한국어 정보처리 학술대회) 논문집은 검색 결과에 나오지 않았다.
