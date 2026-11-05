# 핸드오프 — 코드 지도 검증과 언어 통일 재개 (2026-11-05, 무손실)

> **이 문서가 다음 세션의 단일 진입점이다.** Mode 1 의 `codegraph.json` 을 LLM 앞에서 검증하고 언어 간 입도를 맞추는 작업이다. 조사와 실측은 끝났고 **구현은 0** 이다.
> **작성** 2026-11-05 · 브랜치 `main` · HEAD `89269d8` · `origin/main` 보다 12 커밋 앞섬
> **대체하는 문서** 없음. `docs/handoffs/remain-process-merged.md` 는 별개 작업이다.
> ⚠ 작성 세션 중에 브랜치가 `mode-boundaries` 에서 `main` 으로 바뀌고 HEAD 가 움직였다. 시작할 때 `git status -sb` · `git log --oneline -8` 을 다시 재라.
> ⚠ 이 문서와 조사 자료는 `public.handoff/` 에 있고 git 이 추적한다. 공개 저장소이므로 기계별 경로와 비밀을 적지 않는다.

## 0. 한눈에

- **무엇을 하나.** `collect-graph` 가 낸 코드 지도를 검사하지 않은 채 LLM 단계로 넘기는 구멍을 막고, C++ · C# · Python 지도의 입도를 맞춘다. 사용자는 이 작업에 다섯 문제(정제의 조용한 버림, 수집 중 사망, C++ · C# 호출 부재, 혼합 언어, 수집기 수정 뒤 `--resume`)를 함께 묶으라고 지시했다.
- **어디까지 왔나.** 코드 변경 없음. `verify-graph` 첫 구현은 시험까지 썼다가 사용자 지시로 전부 되돌렸다. 그 뒤 조사 · 실측을 끝냈다.
- **가장 큰 결론.** 스키마는 이미 하나다. 문제는 정제가 메서드를 버리고 호출을 안 모으는 것이다. 호출은 Joern · SCIP 없이 이미 쓰는 Roslyn 과 clang 으로 실제 골든에서 추출했다.
- **다음 행동.** 구현 전에 사용자에게 §4.3 의 결정을 받는다. 그다음 1단계(도구 지문과 안전한 쓰기)를 TDD 로 시작한다. **설계 확인 없이 구현부터 들어가지 마라** — 지난번에 그렇게 해서 되돌렸다.
- **정본 문서.** §3 표. 충돌하면 이 문서가 이긴다.

## 1. 상태 (작성 시점 — 다시 재라)

```
HEAD      89269d8 [chore] : 쓰지 않는 저장소 분리 작업물 제거
브랜치    main (origin/main 보다 12 앞섬). mode-boundaries 브랜치는 이제 없다
미커밋    코드 변경 없음
게이트    이번 세션은 코드를 안 고쳐서 전체 게이트를 돌리지 않았다. 시작 전에 기준선을 잰다
```

## 2. 체크리스트 — 실측 문제와 해법

전부 미착수다. 끝나면 `[x]` 로 바꾸고 커밋을 적는다. `(N단계)` 는 §6 의 순서다.

### A. 검사 경계 (3단계 — `verify-graph`)

- [ ] **A1 경계가 최상위만 본다.** 실측: `{"nodes":[{"x":1}],"edges":[{"y":2}]}` 가 `CodeGraphDoc` 을 통과하고 `survey_plan.plan` 에서 `KeyError: 'id'` 로 죽는다. 해법: 원소별 꼴 · 뜻 검사(§7).
- [ ] **A2 판과 빈 지도를 막지 않는다.** 실측: `schema_version: 1` 에 빈 노드가 통과해 심볼 0개 계획이 성공한다. `render_modules.py:100` 은 경고만 낸다. 해법: `schema-version` · `empty-graph` 결함.
- [ ] **A3 첫 오류에서 멈춘다.** 실측: msgspec 은 첫 오류만 낸다. 해법: 원소마다 `msgspec.convert` 를 따로 불러 전부 모은다.
- [ ] **A4 소스 위치를 안 본다.** 해법: `--repo` 로 파일 존재 · 저장소 안 경로 · 줄 범위를 잰다. 노드와 간선 둘 다. 실제 지도의 줄 범위와 간선 위치는 아직 안 쟀다.
- [ ] **A5 낡은 통과 기록이 재사용될 수 있다.** 해법: 통과 표시를 지도 안에 두고, 정제가 다시 쓰면 사라지게 한다(§7).

### B. 정제가 조용히 버린 정보 (2단계)

- [ ] **B1 버림 통계가 사라진다.** 실측: `stats` 는 화면 출력뿐이고 파일로 안 남는다. 버림 지점은 20곳 남짓. 해법: `normalize-report.json` 에 사유별 수와 표본을 쓴다. 선례는 `dropped-uses.csv`(`context.py:172`).
- [ ] **B2 모르는 C++ 관계가 정상 종료한다.** 실측: 모르는 `type` 을 넣으면 `normalize.py:433` 이 세고 버린 뒤 exit 0. 해법: 장부에 `unknown-kind` 로 적고 `verify-graph` 가 결함으로 막는다.
- [ ] **B3 정책 버림과 미해결 버림이 안 갈린다.** 해법: 사유마다 `policy` · `unresolved` 를 표로 고정한다(§5.4). 미해결만 경고나 결함이 된다.
- [ ] **B4 C++ 끝점 해소 실패 48건의 정체를 모른다.** 실측: 관계 671개 중 48개. 끝점은 전부 원본 요소에 있다 — 없는 id 가 아니라 노드가 못 된 타입을 가리킨다. 해법: 장부 표본으로 정책인지 손실인지 판정한다.

### C. `collect-graph` 안에서 죽는 경우 (1 · 2 · 3단계)

- [ ] **C1 C# 에 모르는 값이 오면 죽는다.** 실측: `normalize.py:736` 의 `CS_KIND[r["kind"]]` 가 `KeyError: 'calls'` 로 exit 1. 결함이 안 모인다. 해법: C++ 처럼 `.get` 으로 받아 장부에 적고 계속한다. (2단계)
- [x] **C2 죽어도 옛 지도가 그대로 남는다.** 실측: 위 사망 뒤 대상 파일 해시가 같았다. 통과 표시가 있는 옛 지도면 `--only schedule-batches` 로 낡은 지도가 LLM 까지 간다. 해법: 수집을 시작할 때 옛 지도를 지운다. (1단계) — `d375e94`
- [ ] **C3 수집 원본의 꼴이 깨지면 죽는다.** 실측: `{"types": []}` 를 주면 `KeyError: 'compilation'`. 해법: 원본 경계에서 `RoslynDump` 등의 형으로 검사하고 결함으로 낸다. (2단계)
- [x] **C4 지도 쓰기가 원자적이지 않다.** 실측: `normalize.py:1239` 는 `open(…, "w")` 에 바로 쓴다. 해법: 같은 폴더 임시 파일에 쓰고 `os.replace`. (1단계) — `5d9b10d`
- [ ] **C5 수집 실패가 결함 파일로 안 남는다.** 해법: `prep.py:75` 의 `run` 이 실패한 단계 · 종료 코드 · stderr 꼬리를 남기고, `collect-graph` 도 같은 결함 보고와 핸드오프를 쓴다. 두 단계가 쓰므로 믹스인이다. 실패 간선을 `verify-graph` 로 보내는 안은 기각 — `--only collect-graph` 에서 매달림으로 `GraphError` 가 난다. (3단계)
- [ ] **C6 `facts` · `render_modules` 가 검사 전에 지도를 읽는다.** 실측: `prep.py:36` 의 꼬리 단계라 `collect-graph` 안에서 돈다. 해법: 검사 뒤의 새 단계로 옮긴다. `report-wiki prep` 명령은 지금 동작을 유지한다. (3단계)

### D. 입도와 호출 (4 · 5단계)

- [ ] **D1 C++ · C# 지도에 메서드가 없다.** 실측: 원본 메서드 C++ 890 · C# 532. `normalize.py` 에 `methods` 글자가 0회다. 해법: 노드로 승격한다. 범위는 결정 사항(§4.3). (4단계)
- [ ] **D2 C# 호출이 없다.** 실측: 수집기 사본에 루프 하나를 넣어 1,295건 중 1,288건 해소(99.5%), 6초. 해법: `Program.cs` 에 호출 루프를 넣고 `CS_KIND` 에 호출을 `dependency` 로 더한다. 주석 `Program.cs:366` 이 비워 둔 자리다. (5단계)
- [ ] **D3 C++ 호출이 없다.** 실측: clang 분석기로 번역 단위 106/106, 32초, 양끝이 지도 메서드인 호출 575쌍. clangd 는 작은 예제에서 나가는 · 들어오는 호출 모두 동작. 해법: 경로를 결정해 `prep` 단계로 넣는다(§4.3). (5단계)
- [ ] **D4 호출 정밀도를 모른다.** 해법: 파일 몇 개를 손으로 정답을 만들어 대조한다. 가상 호출은 C++ 예제에서 `Base::draw` 처럼 정적 대상으로 잡힌다. (5단계)
- [ ] **D5 C++ 자유 함수 층이 비어 있다.** 실측: 이 기계에 `clang-doc` 이 없다. 해법: 호출 수집 결과로 자유 함수 노드를 채울 수 있는지 본다. (5단계)

### E. 언어가 섞인 저장소 (4 · 6단계)

- [ ] **E1 소수 언어가 말없이 빠진다.** 실측: 세 저장소가 모두 혼합이다(§5.6). 해법: 먼저 수집 못 한 언어를 지도에 명시한다. 가장 싼 단계다. (6단계)
- [ ] **E2 노드 id 가 실행마다 매기는 번호다.** 실측: `C%d`. 코드 어디도 그 꼴에 의존하지 않아 교체할 수 있다. 해법: `언어:한정이름(인자형)` 꼴의 안정 id. (4단계)
- [ ] **E3 C# 메서드에 인자 형이 없다.** 실측: `MethodRec` 은 `param_count` 만 갖고, 인자 수까지 써도 1곳이 겹친다. 해법: 인자 형 목록을 더한다. (4단계)
- [ ] **E4 `language` 가 단수다.** 해법: `languages` 와 노드별 언어로 바꾼다. `facts` · `render_modules` · `terms_db` · `scan` · `lang_select` · `warmup --lang` 을 함께 고친다. (6단계)
- [ ] **E5 언어별 지도를 합치는 단계가 없다.** 해법: 언어별로 정제한 뒤 병합한다. 지금 수집기는 하나만 돈다. (6단계)
- [ ] **E6 언어를 넘는 호출.** 확인된 도구가 없다. 범위 밖으로 문서에 적는다. (6단계)

### F. 수집기 수정 뒤 재개 (1단계)

- [ ] **F1 `--resume` 이 옛 지도를 다시 검사한다.** 실측: `resume.py:43` 은 실패 단계를 그대로 돌려준다. 해법: `verify-graph` 실패의 재개 지점을 `collect-graph` 로 둔다. (구현 계획에서 2단계 `verify-graph` 로 옮겼다 — `verify-graph` 가 생겨야 시험할 수 있다)
- [x] **F2 증분이 다시 수집하지 않는다.** 실측: `needs_collect` 가 소스 변화 없으면 `False`(`prep.py:31`). 해법: 지도에 도구 지문을 적고 다르면 다시 수집한다. — `9066c57` · `d375e94` (지문은 지도 밖 `collect-fingerprint.json`, 👍 2026-11-05)
- [x] **F3 지문이 커밋 전 수정과 외부 도구를 놓치면 안 된다.** 해법: 정제 코드의 **내용 해시** 와 수집기 판을 합친다. 커밋 해시는 쓰지 않는다. — `b7d3bea`

### G. 계약과 시험 정리 (3단계 전후)

- [ ] **G1 `survey_plan` 의 형 선언이 실물과 다르다.** 실측: `survey_plan.py:40` 의 `file: NotRequired[str]` 라 실제 지도가 `$.nodes[102].file` 에서 실패하고 러너가 `cast` 로 넘긴다. 해법: 공용 계약 형을 쓴다.
- [ ] **G2 계약 문구가 거짓이다.** 실측: `codegraph_types.py` 와 `src/codewiki/CLAUDE.md` 는 소비자 전부가 계약을 본다고 적지만 import 는 `normalize` · `terms_db` · `warmup` 뿐이다. 해법: 소비자를 맞추거나 문구를 고친다.
- [ ] **G3 골든 시험이 저장된 지도만 읽는다.** 실측: `test_normalize.py:126` 의 `_load` 는 `out/codegraph-raw/codegraph.json` 을 읽어 정제 변경을 못 잡는다. 해법: 수집 원본을 다시 정제해 대조하는 시험을 더한다.
- [ ] **G4 C++ 재정제가 저장본과 다르다.** 실측: 같은 원본에서 191 · 417 대신 195 · 419, 이름 일치 190/191. 해법: 원인을 찾고 기대값을 의도적으로 갱신한다.
- [ ] **G5 `render_classes.py` 를 부르는 파이프라인이 없다.** 소유 관계로 동작이 갈리는 유일한 코드다. 해법: 연결할지 문서에 도구로만 표시할지 결정한다.
- [ ] **G6 아무도 안 읽는 칸.** 실측: `constraint` · `origin` · `attrs` · `signature` · `doc` · `platform`. 해법: 언어 전용 층으로 옮길지 지울지 결정한다. `external-constraint` 검사의 가치도 함께 본다.
- [ ] **G7 스킬 문서가 실물과 다르다.** 실측: `.agents/skills/codebase-terms-survey/SKILL.md:189` 가 Mode 2 를 소비자로 적었지만 Mode 2 코드에 지도를 여는 곳이 없다. 해법: 문구 수정. 스킬 사본 규약을 따른다.
- [ ] **G8 조사 보고서 본문에 틀린 값이 있다.** 보고서 맨 위에 정정 표지는 달았다. 해법: 본문의 532, 3.9배, 여덟 모듈을 고친다. 사용자 승인 대기.

### H. 후속

- [ ] **H1 TypeScript 수집기가 없다.** `lang_select.py:37` 이 `none` 이라 `prep` 이 막힌다. 해법 후보: TS 컴파일러 API, `scip-typescript`. 이때 SCIP 을 다시 본다.

## 3. 문서 색인

| 문서 | 자리 | git | 역할 |
|---|---|---|---|
| 이 문서 | `public.handoff/2026-11-05-codegraph-verify-unify-resume-handoff.md` | 추적 | 단일 진입점 |
| 구현 계획 | `public.handoff/2026-11-05-codegraph-verify-unify-plan.md`(영어 정본) · `.ko.md`(한국어 번역본) | 추적 | 1 · 2단계 Task 단위 상세(지문 · 원자적 쓰기 · `verify-graph` V0~V3) · 3~6단계 개요. 👍 승인 2026-11-05 — 이 문서의 §4.3 결정 1~4 와 단계 순서가 거기서 바뀌었다 |
| 조사 보고서 | `public.handoff/언어 불문 코드 그래프 통일.md` | 추적 | 도구 · 스키마 · UML 조사. 일부 값은 §4.2 가 정정한다 |
| 측정 스크립트 | `public.handoff/언어 불문 코드 그래프 통일/scripts/` | 추적 | §9 의 재현 명령 |
| 측정 결과 | `public.handoff/언어 불문 코드 그래프 통일/results/` | 추적 | 정제 출력 · 파일 열기 기록 · 칸 추적 |

## 4. 결정과 정정

### 4.1 사용자가 지시한 것 — 다시 논쟁하지 않는다

- `collect-graph` 와 `schedule-batches` 사이에 검증 단계를 둔다. 선례를 확인하고 상속받아 만든다.
- 실패해도 바로 죽지 않고 오류를 전부 모아 JSON 파일로 저장한 뒤, LLM 단계에 들어가기 전에 끝낸다.
- 실패를 근거로 C++ · C# · Python 의 수집과 정제를 보강할 계획을 짜도록 핸드오프를 만든다. 슈퍼셋 스키마, 언어별 외래키 데이터 등을 후보로 본다.
- 그래도 해결되지 않는 문제는 그 문제 자체를 핸드오프로 만든다.
- 문제가 없으면 Success JSON 을 저장한다.
- 통일이 불가능하면 `collect-graph` 산출물을 읽는 파이프라인을 언어별로 구체화하는 것을 대안으로 삼는다.
- 위 다섯 문제를 이 작업에 추가한다. 실측 문제의 해법을 체크리스트로 관리한다.

### 4.2 실측으로 굳은 사실과 정정

- ⚠ **C++ 원본 메서드는 532 가 아니라 890 이다.** `full_class.json`(532)이 아니라 `full_class_all.json` 이 8월 지도의 원본이다. 조사 보고서의 532 는 틀렸다.
- ⚠ **메서드 전량 승격 규모는 C++ 약 5.7배, C# 약 3.5배다.** 보고서의 3.9배는 틀렸다. 890 에는 노드가 안 되는 요소의 메서드가 섞여 있어 상한이다.
- ⚠ **보고서의 "지도를 읽는 모듈 여덟" 은 틀렸다.** `render_classes` 는 파이프라인이 부르지 않고 `survey_files` 가 빠졌다. §5.2 가 맞다.
- ⚠ **`normalize` 는 지도를 깨뜨리지 않는다.** 실제 지도의 id 중복 · 끊긴 간선 · 없는 파일이 모두 0건이다. 문제는 깨짐이 아니라 빈약함이다.
- ⚠ **Joern · SCIP 선행 대조안을 철회했다.** 호출을 기존 컴파일러로 얻었다. 두 도구는 TypeScript 때 다시 본다.
- 전면 언어별 구체화는 불필요하다는 것이 현재 판단이다. 지금 언어로 동작이 갈리는 자리는 `facts.py:328` · `facts.py:356` 정도다. 사용자 확정은 아니다.
- 소유 관계는 통일 대상이 아니다. Joern · SCIP · code-graph-rag · Codebase-Memory 모두 없다. 다만 파이프라인에서 소유로 동작이 갈리는 코드는 없고, `terms_db` 가 값을 전달할 뿐이다.
- UML 은 간선 어휘로 유지하고 저장 형식이나 수집 경로로 쓰지 않는다. `EdgeKind` 8종이 이미 UML 어휘다.

### 4.3 사용자에게 받아야 할 결정 — 구현 전에 묻는다

첫 구현에서 혼자 정했던 넷은 **아직 승인받지 않았다.**

1. 성공 JSON 의 형태 — `codegraph.json` 안의 `verification` 칸(제안), 별도 파일, 영수증 중 무엇인가.
2. 핸드오프를 LLM 없이 템플릿으로 만드는가(제안: 그렇다).
3. 해결 불가 판정을 핸드오프를 받은 에이전트가 하는가(제안: 그렇다. 기계는 판정하지 않는다).
4. `--only prep` 이 검사까지 돌도록 별명을 넓히는가(제안: 그렇다).

이번 조사에서 새로 나온 셋이다.

5. 메서드 승격 범위 — 전량, 공개 표면, 호출이 닿는 것.
6. C++ 호출 경로 — clang 분석기(빠름, 위치 없음, 디버그용 인터페이스), clangd(위치 있음, 심볼마다 질의, 골든 미측정).
7. 혼합 언어 — 수집 못 한 언어를 보고만 하는가, 병합까지 하는가.

지난번에 사용자가 `codegraph_types.py` 수정을 거절하고 전체 롤백을 지시했다. 이유는 말하지 않았지만, 그 직후 "무엇을 하려던 것인가" 를 물었고 설계 한계로 대화가 옮겨 갔다. 계약을 바꾸는 작업은 먼저 보여 주고 시작한다.

## 5. 실측 결과

수집기는 다시 돌리지 않았다. C++ · C# 은 골든 저장소의 2026-08 산출물을 읽었고, 정제만 임시 폴더에서 다시 돌렸다.

### 5.1 세 언어

| | C++ | C# | Python |
|---|---|---|---|
| 대상 | `$GRAPHICS_REPO` `bfb72b4` | `$CSHARP_REPO` `bf54917` | 이 저장소 |
| 수집기 | clang-uml 0.6.3 | roslyn-dump 0.1 | griffe 2.2.0 + pycalls |
| 원본 | `full_class_all.json` 요소 318 · 관계 671 | `roslyn-dump.json` 타입 403 · 관계 1,586 | 심볼 700 · 호출 321 |
| 원본 메서드 · 멤버 | 890 · 561 | 532 · 695 | 지도에 노드로 있음 |
| 저장된 지도 | 191 · 417 | 231 · 540 | 706 · 559 |
| 재정제 지도 | 195 · 419 | 231 · 540 | 706 · 559 |
| 1차 노드 종류(재정제) | class 171 · enum 19 | class 121 · enum 62 · interface 24 · struct 7 | function 341 · method 187 · class 172 |
| 소유 간선 | composition 123 · aggregation 84 | 없음 | 없음 |

### 5.2 `codegraph.json` 을 읽는 곳

파일 열기를 감사 훅으로 기록했다. 13단계 중 6단계가 직접 읽는다. 작성자는 파이프라인 안에서 `normalize.py:1239` 하나다.

| 단계 | 코드 | 조건 | 노드 칸 | 간선 칸 |
|---|---|---|---|---|
| `detect-changes` | `warmup.py:176` | 증분에서 바뀐 파일이 있을 때 | id, file | from, to |
| `collect-graph` | `facts.py:222` | 항상 | id, name, kind, module, file, line, collapsed_from | from, to, occurrences |
| `collect-graph` | `render_modules.py:99` | 항상 | id, name, kind, module | from, to, occurrences |
| `schedule-batches` | `graph.py:90` | 항상 | id, name, kind, file, line, abstraction | from, to |
| `annotate-symbols` | `survey_files.py:38` | `--strategy file` 만 | id, name, kind, file, line | from, to |
| `verify-terms` | `terms_db.py:420` | 항상 | id, name, kind, module, file, line | from, to, kind, label, file, line |
| `verify-wiki` | `verify_citations.py:109` | 항상 | id, name, file, line | from, to, kind, label, file, line |

- 단계 기계도 `pipeline.py:100` 에서 최상위 꼴만 본다. `--dry-run` 은 `run_mode1.py:244`, 언어가 `null` 이면 `scan.py:35` 가 읽는다.
- `lang-decide` · `annotate-symbols` 기본 전략 · `outline-wiki` 는 세션을 띄우는 지점까지 지도를 열지 않았다.
- `write-wiki` · `publish-wiki` · `seal-artifacts` · Mode 1.5 · 2 는 지도를 여는 코드가 없다. 앞의 셋은 실행으로 끝까지 확인하지 못했다.
- **LLM 도 읽을 수 있다.** `annotate-symbols.md:43` 이 목록 밖 이름은 `codegraph.json` 을 근거로 쓰라고 지시한다. 가짜 `claude` 로 돌려 빈도는 못 쟀다.
- 간접 소비: `batches.json`(annotate · outline · write), `facts/*.md` · `ranking.json` · 모듈 그림(outline · write), `terms-db.json`(outline · write · 봉인 후 Mode 1.5 · 2).

### 5.3 소비자 계약

정제를 고치거나 교체할 때 지켜야 할 칸은 노드 8칸(id, name, kind, module, file, line, abstraction, collapsed_from), 간선 7칸(from, to, kind, label, occurrences, file, line), 모듈 2칸(id, depends_on)이다. 최상위는 `nodes` · `edges` · `modules` · `language` · `repo_commit` · `schema_version` · `source_tool` 이다. `id` 는 전 소비자가 불투명한 결합 열쇠로만 쓴다.

### 5.4 버림 집계와 사유 분류 제안

| 사유 | C++ | C# | Python | 분류 제안 |
|---|---:|---:|---:|---|
| 원시 타입 제외(R7) | — | 584 | 567 | 정책 |
| 투과 래퍼 · 컨테이너(R5) | 94 | 134 | 173 | 정책 |
| 중복 간선 접음 | 96 | 246 | 158 | 정책 |
| 자기참조 | 90 | 8 | 1 | 정책 |
| 외부발 간선(R4) | 26 | — | — | 정책 |
| enum 멤버 | — | 209 | — | 정책 |
| 끝점 해소 실패 | 48 | — | — | 미해결 (B4 후 재판정) |
| 해소 실패(빌트인 · 타입변수) | — | — | 32 | 미해결 |
| containment | 7 | — | — | 정책 |
| 타입 변수 대상 | — | 32 | — | 정책 |
| git 추적 밖 모듈 | — | — | 42 | 정책 |
| 모르는 관계 종류 | 주입 시 1 | 주입 시 사망 | — | 결함 |

### 5.5 호출

| 언어 | 방법 | 결과 | 시간 | 약점 |
|---|---|---|---|---|
| C# | 수집기 사본에 `InvocationExpressionSyntax` 루프 | 해소 1,288 · 못 찾음 7. 대상이 1차 타입 662. 유일 멤버 쌍 557, 타입 쌍 233. 위치 전부 있음 | 6초 | 대상 메서드 식별에 인자 형 필요 |
| C++ | `clang++ --analyze -Xclang -analyzer-checker=debug.DumpCallGraph` | 106/106 성공. 호출자 21,784(시스템 헤더 포함). 지도 메서드 호출자 708. 양끝 지도 메서드 575쌍 | 32초 | 위치 없음. 이름으로 연결. 오버로드 구분 없음 |
| C++ | clangd `prepareCallHierarchy` · `outgoingCalls` · `incomingCalls` | 예제에서 동작. `free_fn` → draw, helper, twice | 미측정 | 심볼마다 질의. 이 저장소 `clangd_refs.py` 가 클라이언트 선례지만 파이프라인에 안 묶임 |
| Python | pycalls | 호출 321 | — | 이미 있음 |

clang-uml 시퀀스 다이어그램은 시작 지점 지정이 필수이고 전체 추출 옵션이 문서에 없어 제외했다.

### 5.6 혼합 언어와 열쇠

| 저장소 | git 추적 소스 수 | 지금 지도에 실리는 것 |
|---|---|---|
| `$GRAPHICS_REPO` | cpp 456 · py 17 | cpp |
| `$CSHARP_REPO` | cs 1,713 · cpp 1 | cs |
| 이 저장소 | py 122 · ts 13 · cs 1 | py |

- 1차 노드 이름 겹침은 세 언어 모두 0 이다(C++ 190 · C# 214 · Python 700, 재정제 기준).
- 메서드까지 내리면 겹친다. C++ 890개 — 클래스+이름 76곳 겹침, 인자 형을 더하면 4곳, `const` 까지 더하면 **0곳**. C# 532개 — 클래스+이름 4곳, 인자 수를 더하면 1곳.
- 안정 id 선례: SCIP 심볼 문법(`scheme package descriptors`, 메서드 구분자 `name(disambiguator).`), Kythe VName(corpus · root · path · language · signature).

## 6. 권고 순서와 구현 자리

1. **도구 지문과 안전한 쓰기** — C2 · C4 · F1 · F2 · F3. `normalize.py:1239`, `prep.py:21`(`needs_collect`) · `prep.py:187`(normalize 단계), `resume.py:43`. 시험은 `test/codewiki/test_mode1.py` · `qa/gates/test_wiki.py` 에 있다.
2. **버림 장부와 크래시 제거** — B1~B4 · C1 · C3. `normalize.py` 의 `stats` 지점들, `normalize.py:736`, 원본을 읽는 `main`(`normalize.py:1201`). 입력 형은 이미 `RoslynDump` · `UmlElement` · `GriffeDump` 로 선언돼 있다.
3. **`verify-graph` 와 파생 단계 분리** — A1~A5 · C5 · C6 · G1 · G2 · G3. §7.
4. **안정 id 와 메서드 승격** — D1 · E2 · E3. `normalize.py:334` · `:373` · `:698` · `:1040` · `:1156` 의 `"C%d"`, `roslyn-dump/Program.cs:502` 의 `MethodRec`. 메서드 열쇠에 인자 형이 필요하므로 id 가 먼저다.
5. **호출 수집** — D2~D5. C# 은 `Program.cs:366` 뒤, `normalize.py` 의 `CS_KIND`. C++ 은 결정 6 에 따른다. 호출의 kind 는 `dependency` 다(`src/codewiki/CLAUDE.md`).
6. **혼합 언어** — E1 · E4 · E5 · E6. `lang_select.py`, `prep.py:115`, `normalize.py:1188` 의 배타 그룹.

순서의 근거: 2 가 만든 장부를 3 이 읽는다. 4 의 열쇠 없이는 메서드 노드가 오버로드에서 충돌한다. 5 의 호출 간선은 메서드 노드에 붙는다. 1 은 다른 작업과 독립이라 가장 작다.

## 7. `verify-graph` 설계 (첫 구현을 되돌린 뒤의 정본)

시험 본문은 보존하지 않았다. 아래 동작 목록이 명세다.

**구조.** `src/codewiki/python/machine/verify_graph.py`(판정만, 산문 없음)와 `mode1/graph.py` 의 `VerifyGraphStage(P.PromptResource, Mode1Machine)`. `VerifyTermsStage` 와 같은 구조로, `super().perform()` 을 감싼다. 결함 표는 `resource/codewiki/graph-faults.toml`, 핸드오프 글은 `resource/codewiki/prompts/verify-graph.md`(단계당 한 파일, `prompt_names = ("verify-graph",)`).

**명령.** `verify_graph.py <codegraph.json> [--repo <저장소>] [--faults <결함.json>]`. 통과 0, 결함 1. `--repo` 가 없으면 소스 위치만 건너뛴다.

**결과.**

| 결과 | 동작 |
|---|---|
| 통과 | 같은 지도에 `verification: {status: "passed", nodes, edges, first_party}` 를 적고 옛 결함 파일을 지운다. 시각을 넣지 않아 같은 입력은 같은 바이트다 |
| 실패 | 전 결함을 `graph-faults.json` 에 적고 `verification` 칸을 뗀다. 단계가 `graph-handoff.md` 를 렌더하고 `FAIL` 로 멈춘다 |

**결함 파일.** `{status, language, source_tool, repo_commit, total, counts, faults: [{code, at, subject, detail}]}`.

**결함 코드 21종.** `unreadable` · `top-field` · `schema-version` · `language` · `node-shape` · `edge-shape` · `module-shape` · `empty-graph` · `duplicate-node` · `node-kind` · `external-node` · `first-party-location` · `file-outside-repo` · `file-missing` · `line-out-of-range` · `dangling-edge` · `external-source` · `external-constraint` · `duplicate-edge` · `module-list` · `module-dep`. 다섯 문제로 `collect-failed` · `unknown-kind` 가 더해진다.

**계약 변경.** `codegraph_types.py` 에 `NodeKind`(function · method · class · struct · enum · interface · delegate · record · external. `RecordKind` 의 부분집합)와 `GraphVerification`, `CodeGraph.verification: NotRequired`. 이 파일은 사용자가 수정을 거절했던 자리다.

**산출물 사슬.** 사슬 검사는 `.name` 으로 대조한다. `UNVERIFIED_GRAPH`(이름 `codegraph.json`, 꼴 검사 없음)를 `collect-graph.writes` 와 `verify-graph.reads` 에 쓰고, `VERIFIED_GRAPH`(별도 이름, `VerifiedGraphDoc` 꼴)를 `verify-graph.writes` 와 `schedule-batches.reads` 에 쓴다. `CODEGRAPH` 는 `verify-terms` 가 그대로 읽는다.

**시험할 동작.** 온전한 지도는 결함 0. 꼴이 틀린 원소를 전부 모으되 같은 원소를 뜻 검사에서 다시 불평하지 않는다. 꼴이 틀린 노드 때문에 끊긴 간선 · 모듈 목록 결함이 연쇄로 나지 않는다. 코드마다 결함 하나. 줄 범위는 1 이상 파일 끝 이하. 통과는 같은 바이트. 재검사 실패는 통과 칸을 뗀다. 깨진 JSON 과 없는 파일도 결함 파일로 남는다. 표와 코드가 1대1. `NodeKind ⊂ RecordKind`. 미검사 지도는 `schedule-batches` 경계를 못 넘는다. 재수집하면 통과가 사라진다. 새 저장소에서 `--skip verify-graph` 는 `GraphError`. 실패 시 뒤 단계가 돌지 않고 `batches.json` 이 안 생긴다. 재통과하면 옛 결함과 핸드오프가 지워진다. 핸드오프는 혼자 읽어도 이어받을 수 있다(언어 경로 · 보강 후보 · 실제 결함 · 재측정 명령 · 해결 불가 절차).

**핸드오프 내용.** 대상 · 언어 · 수집기 · 변환 함수, 코드별 묶음(많은 순, 예시 5개), 보강 후보 넷(수집 보강 · 정제 보강 · 슈퍼셋 스키마 · 언어별 외래키), 재측정 명령, 해결 불가 시 별도 핸드오프 양식. **검사를 완화해 통과시키지 말라** 는 규칙을 넣는다.

**함께 고칠 자리.** `mode1/context.py`(산출물 · `ARTIFACTS`), `mode1/edges.py`(`ORDER` · `STAGES` · `ALIASES`), `run_mode1.py` 독스트링, `src/codewiki/CLAUDE.md`, `resource/CLAUDE.md`, `test/codewiki/test_mode1.py:880`(`len(E.ORDER) == 13`), README(`tools/gen_readme.py`), `resource/codewiki/terms-reading.json` 레코드.

## 8. 병렬 작업

작성 세션 중 다른 주체가 커밋과 브랜치 전환을 했고 메모리 폴더도 바뀌었다. 이 작업과 겹치는 자리는 확인하지 못했다. 시작할 때 `git log` 로 `normalize.py` · `prep.py` · `mode1/` · `codegraph_types.py` 의 변경을 먼저 본다.

## 9. 가드레일과 재현

- **커밋** 은 사용자가 요청할 때만, `main` 이면 브랜치부터. `personal-commit-messages` 스킬 형식이고, 계획은 제목 한 줄씩만 보이고 파일명은 적지 않는다.
- **긴 측정은 먼저 묻는다.** 무엇을 왜 재는지와 예상 시간을 말한다. 도구가 막히면 원래 과제와 무관한 진단으로 넘어가지 말고 보고한다.
- **TDD.** 실패하는 시험을 먼저 보고 구현한다. 작성 세션은 그렇게 시작했다.
- **`normalize.py` 출력 키를 바꾸면 멈추고 보고한다.** `terms_db.py` 가 간접 의존한다.
- **골든 저장소는 읽기만 한다.** 두 저장소는 작성 전부터 작업 중 파일이 있다(`git status` C++ 31줄 · C# 3줄, 8월 파일). `verify_graph.py` 는 통과하면 지도를 고치므로 사본으로 돌린다. 산출물은 임시 폴더로 보낸다.
- **유료 세션 방지.** LLM 단계를 시험할 때는 실패하는 가짜 `claude` 를 PATH 앞에 둔다.
- **경로.** 문서 · 코드 · 커밋에 홈 경로를 적지 않고 `$GRAPHICS_REPO` · `$CSHARP_REPO` 를 쓴다. 이 기계의 셸에는 두 변수가 비어 있다. `find "$HOME" -maxdepth 4 -type d -name StickRushGame` 처럼 찾아 그 명령에만 넘긴다.
- **zsh 함정.** `echo ====` 는 명령 확장으로 죽고, `--include=*.py` 는 따옴표가 필요하며, `$k[` 는 배열 첨자다. `${k}` 로 쓴다.
- **코드 주석** 에는 현 상황만 적는다. 긴 글은 `resource/` 로 뺀다(`qa/gates/test_prompt_resources.py`).

```bash
# 게이트 여섯
.venv/bin/python -m pytest -q
npm test
npm run typecheck
npm run typecheck:py
.venv/bin/python tools/gen_readme.py --check src/codewiki/python/runner src/codewiki/python/machine src/codewiki/python/viz src/term/python/runner src/spec/python/runner src/spec/python/viz src/core src/common tools
npm run doctor

# 단계 흐름 확인 (자식 프로세스 0개)
.venv/bin/python src/codewiki/python/runner/run_mode1.py <저장소> --dry-run

# 측정 재현 — public.handoff/언어 불문 코드 그래프 통일/scripts/ 에서
GRAPHICS_REPO=… CSHARP_REPO=… python3 raw_counts.py      # 지도와 수집 원본의 수
python3 lsp_caps.py                                       # 언어 서버 선언
python3 cpp_calls.py "$GRAPHICS_REPO" <임시>/calls.json    # C++ 호출
python3 roslyn_call_poc.py <임시>/roslyn-poc/Program.cs    # C# 호출. 사용법은 파일 머리
python3 clangd_calls.py <임시 폴더>                        # call_probe_sample.cpp 를 a.cpp 로 두고 compile_commands.json 을 함께 둔다
```

`open_trace_sitecustomize.py` 는 `sitecustomize.py` 이름으로 폴더에 두고 `PYTHONPATH` 로 넘기면 `CG_TRACE_LOG` 에 파일 열기를 기록한다. `fieldtrace.py` 는 소비자별 칸 사용을 잰다.

## 10. 알려진 한계

- Joern · SCIP 은 실행하지 않았다. 호출 정밀도도 재지 않았다. 해소율은 정확도가 아니다.
- clangd 는 작은 예제에서만 돌렸다. `--background-index` 는 대상 저장소에 캐시를 쓸 수 있으니 골든에서는 사본으로 돌린다.
- `debug.DumpCallGraph` 는 이름대로 디버그용이라 출력 형식이 보장되지 않을 수 있다.
- Python 재정제는 저장본과 `repo_commit` 칸만 다르다(`7e73103` · `89269d8`). 정제 결과는 같다.
- `os.replace` 의 원자성은 Python 공식 문서 원문을 확인하지 못했다.
- UML `«call»` · `«utility»` 의 근거는 Visual Studio 2015 보관 문서다. OMG 원문은 읽지 못했다.

## 11. 출처 (보고서에 없는 것)

- 도구 지문: [ccache 매뉴얼](https://ccache.dev/manual/latest.html) · [Bazel 이슈 4558](https://github.com/bazelbuild/bazel/issues/4558) · [SCIP 스키마](https://raw.githubusercontent.com/scip-code/scip/main/scip.proto)의 `ToolInfo`
- 안정 id: [SCIP 심볼 문법](https://raw.githubusercontent.com/scip-code/scip/main/docs/scip.md) · [Kythe storage.proto](https://android.googlesource.com/platform/external/kythe/+/1f8c41cede4dbfcbd47c3f55f3d3a12c1c7a9301/kythe/proto/storage.proto) · [Kythe 스키마](https://android.googlesource.com/platform/external/kythe/+/426b1bf1b623b49e465e978a54235aedac87d7fd/kythe/docs/schema/schema.txt)
- 버림 장부: [dead letter queue 개요](https://conduktor.io/glossary/dead-letter-queues-for-error-handling) · [재처리 패턴](https://datadriven.io/learn/pa_pattern_dead_letter_queue)
- 호출: [clang-uml 시퀀스 다이어그램](https://raw.githubusercontent.com/bkryza/clang-uml/master/docs/sequence_diagrams.md) · [Roslyn IInvocationOperation](https://learn.microsoft.com/ko-kr/dotnet/api/microsoft.codeanalysis.operations.iinvocationoperation?view=roslyn-dotnet-3.1)
- 혼합 언어: [cpggen](https://pypi.org/project/cpggen/1.1.4)

## 12. 변경 기록

| 날짜 | 변경 |
|---|---|
| 2026-11-04 | `verify-graph` 첫 구현 시작. 시험까지 쓴 뒤 `codegraph_types.py` 수정이 거절되어 전부 되돌림 |
| 2026-11-04 | 언어 불문 코드 그래프 조사와 보고서 작성. `codegraph.json` 소비자 실측 |
| 2026-11-04~05 | 다섯 문제의 해법 조사와 실측. 수집기 원본 오인(532 → 890)을 찾아 정정 |
| 2026-11-05 | 이 핸드오프 작성. 실측 문제와 해법을 체크리스트로 정리 |
| 2026-11-05 | 핸드오프와 조사 자료를 `docs/` 에서 `public.handoff/` 로 옮겨 git 추적 대상으로 바꿈 |
