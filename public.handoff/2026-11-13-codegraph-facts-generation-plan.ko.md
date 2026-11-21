# 🧭 코드 지도 — 근거 경계 · generation · 범위 — 구현 계획 (0~3단계 상세 · 4~6단계 개요) — 요약 번역본

> **이 문서는 요약 번역본이다.** 영어 정본은 `public.handoff/2026-11-13-codegraph-facts-generation-plan.md` 이고, Task 0~25 의 본문(코드 · 단계 · 기대값)은 정본에만 있다. 👍 2026-11-13 — 11-13 교차 점검의 Q6'(전역 번역 규칙)이 열려 있는 동안 이 문서 한 건에만 적용하는 예외다. 정본과 어긋나면 정본이 이긴다.
> 📅 2026-11-13 · 브랜치 `main` · **Before = `a21dd4d`** (= `origin/main` + 2). 작성 시점 작업 트리: 미추적 `public.handoff/2026-11-09-codegraph-adversarial-review.md` + 폴더, `public.handoff/2026-11-13-h4-adversarial-review-handoff.md`; 병렬 세션이 고친 머리말 넷(11-05 재개 핸드오프 · 3단계 사양 `.md` · `.ko.md` · H4 권고) 미커밋 — Task 0 이 함께 커밋한다
> 📄 출처: 적대적 검토(2026-11-09, 이하 "검토")와 그 `repro.py` · `results.json`(이 세션에서 다시 돌려 바이트 단위로 같음) · 3단계 설계 사양(2026-11-08, **흡수** 👍) · 11-05 계획(1 · 2단계 완료) · 11-05 재개 핸드오프(체크리스트 A~H) · 11-13 H4 권고(R1 은 별개 트랙 👍). 이 세션에서 읽은 코드 목록은 정본 머리말에 있다
> 🔒 지킬 규칙: **검사를 완화해 통과시키지 않는다** · `codegraph_types.py` 는 이 계획이 diff 를 먼저 보인 자리(4단계 `Edge.sites`)만 바꾼다 · `normalize.py` 출력 **열쇠**가 바뀌면 멈추고 보고(`terms_db.py` 가 `from`/`to` · `id`/`depends_on` 에 의존) · 골든 저장소는 읽기만 · 코드 주석은 현 상황만 · 긴 글은 `resource/` · 커밋은 사용자가 요청할 때만, `personal-commit-messages` 꼴
> 🧪 검증: **구현 → Task 마다 커밋 → 끝(Task 25)에 시험 한 번 → 실패하면 `git bisect run`** (👍 2026-11-13 유지). 아직 통과할 수 없는 회귀 명세는 `xfail(strict=True)` 로 커밋해 모든 커밋이 혼자서도 초록이다
> ✋ 승인: 👍 **2026-11-14 구현 승인** — Task 0(문서)은 `main` 에 커밋한다. Task 1~24 는 별도 git worktree 의 브랜치 `codegraph-facts-generation` 에서 Task 마다 커밋하고 push 하지 않는다. `main` 반영은 Task 25 뒤에 묻는다. 같은 날 정한 것: Task 1 전에 기준선을 재지 않는다(Task 25 가 Before 커밋의 worktree 에서 잰다) · Root 지침 §7 의 정정 14건을 이 문서와 정본에 줄 안에서 반영했다 · 낡은 샤드 재사용은 Task 10 뒤에 Task 하나를 더한다(설계안을 먼저 보인다)

**목표:** `verify-graph` 의 통과가 LLM 단계가 필요로 하는 뜻을 갖게 한다 — 지도가 열리고 · 안에서 어긋나지 않고 · **지금 그대로의 소스**에서 만들어졌고 · 수집하지 못한 것을 명시한다 — 그리고 `schedule-batches` 하나가 아니라 **모든 LLM 진입점**이 그것을 대조한다.

**구조:** 검사기가 원본 파일을 직접 연다(산출물 경계에 꼴 검사 없음). 결과는 네 절 — <span style="color:cyan">integrity</span> · <span style="color:cyan">freshness</span> · <span style="color:cyan">coverage</span> · <span style="color:cyan">capabilities</span> — 와 목적별 적합(fit)으로 낸다. 성공 기록은 수집 시점에 계산한 <span style="color:cyan">generation id</span>(수집기 지문 · 지도 바이트 · 인용한 소스 파일 전부의 바이트)에 묶인다. 그 id 가 `batches.json` · `ranking.json` 에 찍히고, 믹스인 하나(`VerifiedGraph`)가 LLM 진입마다 대조한다. 정제는 <span style="color:cyan">버림 장부</span>를, prep 은 <span style="color:cyan">소스 inventory</span> 와 <span style="color:cyan">수집 실패 기록</span>을 쓴다. `facts` · 그림은 검사 뒤의 `derive-facts` 로 옮긴다. 전부 평평한 `out/codegraph-raw/` 에 산다(👍 generation 디렉터리 없음).

---

## 📋 한 장 요약

| | |
|---|---|
| 🎯 다루는 것 | 검토의 실행 순서 0~6(`검토 §4`)이 11-05 계획의 3~6단계 개요를 대체한다. **0~3단계는 Task 단위(Task 0~25)**, 4~6단계는 결정 · 산출물 · 남은 진입 질문만. 상세로 다루는 핸드오프 항목: A(문구) · B1~B3 · B5 · C1 · C3 · C5 · C6 · E1 · 검토의 F1~F11 · G1 · G2 · G3(조건부) |
| 🧩 한 줄 결론 | 지금 통과는 "JSON 열림 · 열쇠 있음 · id 정합 · 인용 파일이 그 줄 수 이상으로 있음" 을 증명한다. 3단계 뒤에는 그것에 더해 **"수집기 코드 · 설정 · 인용한 소스 바이트가 지도를 만들 때의 것 · 정제가 버린 것 중 정보 손실 없음 · 고른 언어의 모든 파일이 장부에 있음 · 수집 못 한 언어는 이름이 적힘"** 을 증명하고, 그 증명이 파생 파일과 함께 LLM 진입점마다 간다 |
| 🟰 그대로 | 4단계까지 `codegraph.json` 의 열쇠 꼴 · UML 어휘 간선 종류와 R1~R7 · `report-wiki prep` 은 여전히 끝에 facts · 그림을 만든다 · `graph-verified.json` 은 별도 파일 · 평평한 `out/codegraph-raw/` · 시험 정책 |
| 🗘 바뀜 | `CODEGRAPH` 산출물의 스키마 제거(검사기가 원본을 연다) · 결과 문서에 네 절 + `checks_run` + `fit` · `collect-fingerprint.json` 이 수집 manifest 가 됨(`sources` · `generation_id` · `raw_provenance`) · `batches.json` · `ranking.json` 에 `generation_id` · 단계 14 → **15**(`derive-facts`) · `annotate-symbols` · `outline-wiki` · `write-wiki` 가 `GRAPH_VERIFIED` 를 읽음 · 결함 코드 21 → **34** |
| ⚠️ 함정 | 옛 `out/` 이 있는 저장소는 첫 prep 에서 한 번 재수집한다(manifest 꼴이 바뀜) · 러너 시험의 가짜 단계 — `verify-graph` 대역은 성공 기록을, `schedule-batches` 대역은 `codegraph_sha256` · `generation_id` 를 남겨야 한다(Task 25 Step 2 에 도우미) · C# 원본 덤프는 prep 밖에서 나오므로 5단계가 수집기 manifest 를 더하기 전까지 최신성이 `unknown` — **막지 않고 보고한다** · C++ 골든은 B4(Mac 세션)까지 `끝점 해소 실패` 48건으로 막힌 채다 — Task 19 뒤에는 골든만이 아니라 `끝점 해소 실패` 가 있는 C++ 대상 전부가 `verify-graph` 에서 멈춘다 |
| 🚫 범위 밖 | B4 · G3 · G4(골든 원본 — Mac 세션, 👍 S2) · G5~G8 · H4 권고 R1~R7(별개 트랙, R2 는 Task 22 뒤이고 소비자 조건도 필요하다 · 측정은 도구 커밋을 고정한 별도 작업 공간에서 시작 상태를 적고 — Root 지침 §4) · 사실 저장소 + 투영 구조(👎, 대신 `Edge.sites`) · generation 디렉터리 · writer 잠금(👎) · C++ 다중 설정 수집(👎, 단일 설정 선언) |

## 🗺️ 7단계 한눈에

| 🧬 단계 | 검토 항목 | 핸드오프 항목 | 진입 결정 | 산출물 |
|---|---|---|---|---|
| 0 문서 · 보장 정의 · 반례 고정 | F10 · F1 문구 · 회귀 명세 | — | 👍 이번 세션 | superseded 표시 · 핸드오프 머리말 · `test_graph_adversarial.py`(xfail) |
| 1 검증 경계 · 모든 LLM 진입 | F2 · F3 · F8(규칙) · F9(원자적) · F1(`checks_run`) | G1 · G2 | 👍 이번 세션 | `VerifyDoc` · `VerifiedGraph` 믹스인 · `jsonio.write_json_atomic` |
| 2 수집 manifest · generation | F4 · F1(소스 해시) · F9(무효화) | 핸드오프 F2 · F3 확장 | 👍 평평한 폴더 + `generation_id` | `sources` · `generation_id` 가 있는 manifest · `source-drift` 결함 |
| 3 inventory · 버림 장부 · 원본 검문 · 파생 분리 | F6(이름) · F7(경로 규약) · F8(coverage) | B1~B3 · B5 · C1 · C3 · C5 · C6 · E1 · G3(조건부) | 👍 S1~S6 흡수 | `normalize-report.json` · `source-inventory.json` · `collect-failure.json` · `derive-facts` |
| 4 사실 모델 · 안정 id · 후단 열쇠 이주 | F5 · F6(`sites`) | D1 · E2 · E3 | 👍 메서드 전량 보존 + 조사 필터 · 👍 `Edge.sites` | `언어:한정이름(인자형)` id · `terms_db` · `survey` 의 `symbol_id` 열쇠 |
| 5 언어별 메서드 · 호출 수집 | F7(선언) · F11 | D2~D5 | §4.3-6 은 D4 측정 뒤 | sites 가 붙은 C# · C++ 호출 간선 · 정답 대조 정밀도 |
| 6 언어별 병합 · 투영 | — | E4~E6 · H1 · Q2 · Q3 | §4.3-7(보고 먼저, 병합 나중) | `languages` · 성공 기록의 언어별 capabilities |

## ✅ 정한 것 — 다시 열지 않는다

| 무엇 | 👍 고른 것 · 👎 버린 것 | 누가 · 언제 |
|---|---|---|
| 검토 반영 방식 | 👍 3~6단계를 검토 순서 0~6 으로 재작성 · 👎 3단계 앞 짧은 보강 단계 · 👎 기존 단계 안에 흡수 | 사용자 · 2026-11-10 |
| 시험 정책 | 👍 "구현 → Task 마다 커밋 → 끝에 한 번 시험 → bisect" 유지 · 👎 변경마다 회귀 시험 · 👎 혼합. bisect 스크립트의 "시험 파일 없음 = 통과" 한계는 지침에 적는다 | 사용자 · 2026-11-10 |
| F6 사실을 두는 자리 | 👍 `codegraph_types.py` 의 `Edge.sites: NotRequired[list[Site]]`(4단계, diff 먼저) · 👎 별도 사실 파일 · 👎 사실 저장소 + 투영 · 👎 보류 | 사용자 · 2026-11-10 |
| §4.3-5 메서드 승격 범위 | 👍 선언된 메서드 **전량**을 사실로 보존, 배치 · 위키 범위는 필터 · 👎 공개 표면만 · 👎 호출 도달만 | 사용자 · 2026-11-10 |
| generation 장치 | 👍 평평한 `out/codegraph-raw/` + 성공 기록 · 배치 · 순위에 `generation_id` 도장 + 모든 쓰기 원자적 · 👎 불변 generation 디렉터리 + manifest 포인터 + writer 잠금 | 사용자 · 2026-11-10 |
| F7 C++ 빌드 설정 | 👍 번역 단위당 설정 하나(첫 항목) 선언, 상대 `file` 은 clang 규약대로 `directory` 기준으로 풀고, 버린 중복은 inventory 에 `excluded(policy: duplicate-config)` · 👎 다중 설정 수집 · 👎 측정 뒤 결정 | 사용자 · 2026-11-10 |
| F8 결과 꼴 | 👍 네 절 `integrity` · `freshness` · `coverage` · `capabilities` + 목적별 `fit` · 👎 층만 유지 | 사용자 · 2026-11-10 |
| 문서 자리 | 👍 이 새 계획 + 11-05 계획의 3~6단계 개요에 superseded 표시 · 👎 옛 파일의 §3~6 교체 · 👎 핸드오프에 합치기 | 사용자 · 2026-11-10 |
| 3단계 사양(S1~S6) | 👍 그대로 흡수 — S1 미해결 버림 차단 · S2 B4 · G3 는 Mac · S3 이 저장소 미해결 0 이 완료 조건 · S4 G1 · G2 는 A안 · S5 점 경로 꼬리 해소 · S6 `derive-facts` 는 `verify-graph` 바로 뒤. 그 문서 머리에 "흡수됨" 표시, Python 해소 규칙의 근거 설명으로 남긴다 · 👎 참조만 · 👎 S1 재검토 | 사용자 · 2026-11-13 |
| H4 R1 측정 | 👍 별개 트랙 — 이 계획은 기다리지 않는다, R2 는 Task 22(`derive-facts`) 뒤 · 👎 0단계 기준선 · 👎 3단계 뒤 | 사용자 · 2026-11-13 |
| 이 계획의 한국어 번역본 | 👍 **요약 번역**(이 문서) — 교차 점검 Q6' 이 열려 있는 동안 한 건 예외 · 👎 지금 전역 · 👎 보류 | 사용자 · 2026-11-13 |
| 여전히 유효한 앞선 결정 | 👍 `collect-graph` 와 `schedule-batches` 사이의 검증 · 결함 전부 모아 JSON + 템플릿 핸드오프, LLM 없음 · 해결 불가 판정은 받는 에이전트 · `--only prep` 은 검사까지 · 별도 성공 기록 파일 · Q1 지문 파일(핸드오프 §4.1 · §4.3-1~4, 11-05 계획 "Decided") | 사용자 · 2026-11-05 |

## 📊 상태

| 항목 | 상태 |
|---|---|
| 11-05 계획의 1 · 2단계(지문 · 원자적 지도 쓰기 · `verify-graph` V0~V3) | ✅ `9066c57` … `bef937a` |
| 적대적 검토 · 반례 12건 재현 | ✅ 2026-11-09 · 2026-11-10 재실행(바이트 동일) |
| 3단계 사양 결정 S1~S6 | ✅ 👍 여기 흡수 |
| 이 계획 | ✅ 2026-11-14 구현 승인 (✋ 승인 줄) |
| 0~3단계(Task 0~25) | ❌ |
| 4~6단계 | ❌ (남은 진입 질문에 답하면 각자 Task 단위 계획) |

## 🔎 통과가 보장하는 것 — 전후 (검토 0단계의 "보장 정의")

| 주장 | Before `a21dd4d` | 1단계 뒤 | 2단계 뒤 | 3단계 뒤 |
|---|---|---|---|---|
| JSON 으로 열리고 계약 열쇠 · 형이 있다 | ✅ 그러나 산출물 경계가 먼저 죽어 한 줄 `why` 만 남고 **결함 파일 · 핸드오프 없음**(검토 F2, 재현) | ✅ 검사기가 읽기를 소유 — 깨졌거나 없는 파일 → `unreadable` + 핸드오프 | — | — |
| id 유일 · 간선 해소 · 외부 규칙 · 모듈 목록 | ✅ V2 아홉 규칙 | ✅ + `external-only` · `occurrences-range` · `module-dep-mismatch` | — | — |
| 인용 파일이 저장소 안에 그 줄 수 이상으로 있다 | ✅ V3(`graph.py:46` 이 `--repo` 를 늘 넘김) | ✅ + 어떤 검사가 돌았는지(`checks_run`) · 전수조사에 맞는지(`fit.survey`) | ✅ + **인용 파일의 바이트가 수집 시점과 같다**(`source-drift`) · 수집기 코드 · 설정이 기록된 것(`generation-mismatch` · `freshness-unknown`) | — |
| 성공 기록이 이 지도의 것이고 LLM 단계가 그것을 지킨다 | ❌ `schedule-batches` 만 sha 를 본다; `--only annotate-symbols` 는 어떤 `batches.json` 으로도 돈다(검토 F3, 재현) | ✅ `VerifiedGraph` 검문이 `schedule-batches` · `annotate-symbols` · `outline-wiki` · `write-wiki` 에; `batches.json` 이 `codegraph_sha256` 을 가짐 | ✅ 성공 기록 · 배치에 `generation_id` | ✅ `ranking.json` 도; `facts` · 그림은 검사 지난 지도에서만. ⚠ 샤드와 읽기 레코드는 이 사슬 **밖**이다 — Task 10 뒤의 추가 Task 가 막는다(👍 2026-11-14, 설계 먼저) |
| 정제가 버린 것 중 정보 손실이 없다 | ❌ `stats` 는 화면만 | — | — | ✅ 장부 `normalize-report.json`; `unresolved-drop` · `unknown-kind` 가 막는다(👍 S1) |
| 고른 언어의 모든 파일이 장부에 있고 다른 언어는 이름이 적힌다 | ❌ | — | — | ✅ `source-inventory.json`; `coverage-gap` · `language-not-collected` 는 **보고만, 막지 않음** |
| 수집 실패가 구조화된 기록을 남긴다 | ❌ 화면만(검토 C5) | — | — | ✅ `collect-failure.json` → `collect-failed` 결함 + `collect-graph` 자신이 핸드오프 |
| 어느 단계도 주장하지 않는 것 | 이름의 의미 정확성 · 호출 완전성 · 런타임 디스패치 대상. 성공 기록은 **이 입력 · 이 정책으로 지정된 검사를 수행했다**는 증거이고, 코드의 뜻이 참이라는 보증이 아니다(검토 §3) | | | |

## 🧪 실행 · 시험 지침 (👍 2026-11-05, 2026-11-10 유지)

1. **Task 0 → 24 순서로 구현, Task 하나가 커밋 하나.** 시험 코드는 Task 안에서 쓰고 같은 커밋에 넣는다; "⏭ 기대" 줄은 Task 25 에서 읽는다. 함수 서명 · 독스트링을 바꾸는 Task 는 같은 커밋에서 README 를 다시 생성한다(`tools/gen_readme.py`).
2. **뒤 Task 가 통과시키는 회귀 명세는 Task 1 에서 `@pytest.mark.xfail(strict=True, reason="Task N")` 으로 커밋**하고 Task N 이 표식을 뗀다. `strict=True` 라 예상 밖 통과는 실패로 잡힌다 — 떼는 것을 잊으면 걸린다. 모든 커밋이 혼자서도 초록이다.
3. **bisect 스크립트의 알려진 한계**(검토 F11): 시험 파일이 없는 커밋은 통과로 치므로 지목된 범인은 "시험이 있으면서 실패하는 첫 커밋" 이다 — 그 커밋의 Task 를 읽고, 시험 도입 커밋이 무죄라고 단정하지 않는다. `out/` 은 git 밖이라 커밋을 따라 움직이지 않는다 — 실제 지도를 읽는 검사(실데이터 시험 · 레코드 검사)는 **bisect 의 걸음마다** 지도를 다시 만든다: 스크립트를 `PREP=1` 로 띄우면 커밋마다 `bin/report-wiki prep . --force` 뒤에 검사한다(`prep` 이 실패한 커밋은 125 로 건너뛰고 따로 본다). 시작 전에 한 번으로는 부족하다 — 다른 커밋들이 같은 지도로 판정된다.
4. **Task 25 — 최종 시험**이 게이트 여섯 · 적대적 시험 파일 · 실제 실행을 돈다. 실패하면 `git bisect run` 으로 범인을 찾아 **새 커밋**으로 고치고 Task 25 를 처음부터 다시 돈다. 스크립트는 정본에 있다(좋은 끝 `a21dd4d`, 나쁜 끝 HEAD).

## 🔁 Before / After — 검토 발견 하나에 한 줄

| 📍 이전 (안 되던 것 · 지금) | 🛠️ After · 제안 | 🎉 해결되는 것 | 🔭 기대 | 진행 |
|---|---|---|---|---|
| 🐞 F2 `CODEGRAPH` 에 스키마 `CodeGraphDoc`(`context.py:300-301`); `missing_reads`(`pipeline.py:137-147`) 가 `verify_graph.py` 전에 실패 — 깨진 JSON 은 결함 파일을 못 남긴다 | 산출물 스키마 `None`; `VerifyGraphStage.reads = []` — 검사기가 부재 · 비가독을 소유 | V0 · V1 최상위가 CLI 뿐 아니라 파이프라인에서 산다 | `{` → `graph-faults.json` {`unreadable` 1} + `graph-handoff.md`, 단계 FAIL | ❌ |
| 🐞 F3 `annotate-symbols` 가 `BATCHES` 만 읽음(`survey.py:34-35`); 어떤 `batches.json` 도 돈다; `stale_verification` 이 지도를 두 번 읽음(`graph.py:140-151`) | ★ `VerifiedGraph` 믹스인: 지도 바이트 한 번 읽기, 성공 기록의 `status` · `fit` · sha, `batches.codegraph_sha256` · `generation_id`; LLM 인접 네 단계의 `reads` 에 `GRAPH_VERIFIED` | 낡은 배치로 세션을 띄울 수 없다 | 성공 기록 없는 `--only annotate-symbols` → 시작 전 `GraphError` | ❌ |
| 🐞 F8 외부 노드만 있는 지도 · 음수 `occurrences` · 간선과 어긋난 `depends_on` 통과(`verify_graph.py:127-128,212-218`) | integrity 코드 3 추가; 결과를 네 절 + `fit` 으로 | "결함 0" 이 무엇을 봤는지 말한다 | 합성 지도 셋 → 각 1 결함 | ❌ |
| 🐞 F9 `_replace` 가 `open(…, "w")` 로 쓴다(`verify_graph.py:285-292`); 지문 · 배치 · 재개 파일도 같다 | ★ `jsonio.write_json_atomic`(`normalize.py:1187` 에서 이동)을 모든 writer 가 쓴다 | 반쯤 쓰인 성공 기록 · 계획 · manifest 가 없다 | 중단 시험: 옛 파일 그대로 | ❌ |
| 🐞 F1 성공 기록 = 지도 sha 만(`verify_graph.py:59-68`); 같은 줄의 본문 변경이 통과; 계획 문구가 V3 를 과장 | `checks_run` · `fit`(1단계) · 수집 시점의 인용 파일별 `sources_sha256` → `source-drift`(2단계); 문구 정정(0단계) | 성공 기록이 지도 **와** 소스 바이트 **와** 수집기에 묶인다 | 같은 줄의 `def completely_different()` → `source-drift` 1 | ❌ |
| 🐞 F4 `COLLECT_CODE`(`prep.py:24-30`) 에 `compdb.py` · 러너 `clang_doc.py` · `paths.py` 없음; 시험은 `normalize` import 만 봄; `--diff` 없는 직접 `report-wiki prep` 은 소스를 안 봄; C# `--force` 는 옛 덤프 재정제 | 지문 확대(코드 + `.clang-uml` + `compile_commands.json` 바이트); `needs_collect` 에 manifest `sources` 기반 `source_changed`; C# `raw_provenance: "unknown"` 보고 | `wiki/` 어디의 수집기 수정도 재수집; 소스 수정은 `--diff` 없이도 재수집 | `compdb.py` 바이트 변경 → 지문 다름 | ❌ |
| 🐞 B1~B3 · C1 · C3 · C5 · C6(3단계 사양) | `Ledger` · `DROP_CLASS` · `normalize-report.json` · `CS_KIND.get` · `validate_raw` · `collect-failure.json` · `GraphFaultReport` · `derive-facts` | 버림이 분류되고 크래시가 결함이 되며 파생물은 검사 지난 지도에서 나온다 | 이 저장소: 미해결 0 · 결함 0(👍 S3) | ❌ |
| 🐞 E1 · F8-coverage 소수 언어가 말없이 빠짐(이 저장소: cpp 1 · cs 1 · ts 13 추적, py 는 git ls-files -z 로 센다) | ★ `source-inventory.json` 언어별 · 파일별 상태; coverage 절 + `language-not-collected` · `coverage-gap`(보고) | 수집 못 한 것이 성공 기록과 핸드오프에 있다 | 이 저장소 → `languages_not_collected: ["cpp", "cs", "ts"]` | ❌ |
| 🐞 F7 `mergeEntries` 가 파일명으로 명령 하나만 남기고 상대 `file` 을 버림(`compdb.py:39-52`) | `file` 을 `directory` 기준으로 풀고 첫 설정만 남기며 나머지는 장부 | clang 규약에 맞고 버린 선택이 보인다 | 명령 2 → 항목 1 + `excluded(policy: duplicate-config)` 1 | ❌ |
| 🐞 F6 타입 간선에 접힌 호출이 위치를 잃음; 재귀가 `호출 양끝 해소 실패` 로 셈(`normalize.py:1174`) | 3단계: 사유 `자기참조 버림(policy)`; 4단계: `Edge.sites` 가 발생 전부를 보존 | 사실이 보기 정책을 견딘다 | 4단계 | ❌ |
| 🐞 F5 `terms_db` 가 `name` 으로 레코드 키를 잡음(`terms_db.py:134`); id 둘 · 이름 하나 → 레코드 하나 | 4단계: `symbol_id` 를 끝까지 결합 열쇠로; 이름은 표시 | 메서드 승격이 오버로드를 잃지 않는다 | 4단계 | ❌ |
| 🐞 F10 핸드오프 머리말 "구현 0"; §7 이 지도 안 `verification` 칸을 서술; 11-05 계획 §3~6 개요가 대체됨 | Task 0 이 머리말 고치고 superseded · absorbed 표시 | 상태 표 정본 하나(이 문서) | — | ❌ |

## 🔀 Task 목록 (본문은 정본)

| 단계 | Task | 한 줄 | 커밋 제목 |
|---|---|---|---|
| 0 | 0 문서 변경 | 핸드오프 머리말 · 11-05 계획 · 3단계 사양 · 11-13 교차 점검(Q2' · Q3' · Q4' 답함) · `src/codewiki/CLAUDE.md` 의 보장 문구; 11-09 검토 파일 `git add` | `[docs] : 코드 지도 - 적대적 검토 반영 계획과 Root 지침, 핸드오프와 옛 계획에 대체 표시` |
| 0 | 1 반례 → 회귀 시험 | `test/codewiki/test_graph_adversarial.py` 12건, 고칠 Task 까지 `xfail(strict)` | `[test] : codewiki - 적대적 검토의 반례 12개를 회귀 시험으로 고정, 고칠 Task 까지 xfail` |
| 1 | 2 검사기가 원본을 소유(F2) | `CODEGRAPH` 스키마 제거 · `VerifyGraphStage.reads = []` | `[fix] : codewiki - 코드 지도 산출물의 꼴 검사를 경계에서 떼어 verify-graph 가 깨진 파일도 결함으로 남긴다` |
| 1 | 3 원자적 쓰기 하나(F9) | ★ `jsonio.py`; normalize · verify_graph · prep · 배치 · 재개 파일이 함께 쓴다 | `[refactor] : codewiki - 원자적 JSON 쓰기를 jsonio 로 모아 검사 결과, 지문, 배치, 재개 파일이 함께 쓴다` |
| 1 | 4 결과 문서(F8 · F1) | `VerifyDoc` 네 절 · `checks_run` · `fit`; `external-only` · `occurrences-range` · `module-dep-mismatch`(24코드) | `[feat] : codewiki - 검사 결과를 integrity, freshness, coverage, capabilities 넷과 적합 판정으로 내고 외부만, 음수 발생 수, 모듈 의존 불일치를 잡는다` |
| 1 | 5 공통 검문(F3) | ★ `VerifiedGraph.gate`; 배치에 `codegraph_sha256`; 네 단계의 `reads` · `perform` | `[feat] : codewiki - 성공 기록 대조를 VerifiedGraph 믹스인으로 모아 배치, 전수조사, 목차, 위키 단계가 같은 검문을 지난다` |
| 1 | 6 계약 문구(G1 · G2, S4) | `survey_plan.GraphNode` 를 실물에 · `cast` 제거 · 머리말 문구 | `[fix] : codewiki - survey_plan 의 노드 형을 실물에 맞춰 schedule-batches 가 cast 없이 읽고 계약 머리말을 바로잡는다` |
| 1 | 7 1단계 문서 | README · 레코드 · CLAUDE.md · 핸드오프 §2 I절 | `[docs] : codewiki - 검사 결과 넷 절과 공통 검문 설명, 레코드, 핸드오프 1단계 표시` |
| 2 | 8 지문 확대(F4) | `COLLECT_CODE` +4 · ★ `config_inputs` · 시험을 prep import 까지 | `[fix] : codewiki - 수집 지문이 prep 이 import 하는 모듈과 .clang-uml, compile_commands 내용까지 덮는다` |
| 2 | 9 수집 manifest(F1 · F4) | ★ `collect_manifest.py`(`sources` · `generation_id` · `raw_provenance`); `needs_collect(source_changed)`; 재수집 시 성공 기록도 지움 | `[feat] : codewiki - 수집 지문 파일이 인용 파일의 소스 해시와 generation_id 를 갖는 manifest 가 되고 소스가 바뀌면 다시 수집한다` |
| 2 | 10 manifest 대조(F1) | `--manifest`; `source-drift` · `generation-mismatch` · `freshness-unknown`(27코드); `fit` 은 manifest ok 요구 | `[feat] : codewiki - verify-graph 가 수집 manifest 와 대조해 소스 변화, 다른 지도의 manifest, 출처 불명을 최신성 결함으로 낸다` |
| 2 | 11 `generation_id` 전파 | 배치에 도장 · 검문이 대조 | `[feat] : codewiki - 배치가 generation_id 를 갖고 공통 검문이 성공 기록과 대조한다` |
| 2 | 12 2단계 문서 | README · 레코드 · CLAUDE.md Note · 핸드오프 표시 | `[docs] : codewiki - 수집 manifest 와 generation_id 설명, 레코드, 핸드오프 2단계 표시` |
| 3 | 13 장부(B1 · B3 · S1) | `Ledger` · `DROP_CLASS` · `ReportDoc`; 소스의 모든 사유 문자열 대조 시험; 재귀는 `자기참조 버림` | `[feat] : codewiki - 정제의 버림 사유를 등급표와 표본이 있는 장부로 세고 재귀는 해소 실패가 아니라 정책으로 센다` |
| 3 | 14 모르는 종류(B2 · C1) | C++ `CLANG_UML_KIND.get` · C# `CS_KIND.get` → `모르는 관계 종류`(fault) | `[fix] : codewiki - 모르는 C++ 관계 종류와 C# kind 를 죽거나 조용히 버리지 않고 결함 등급으로 장부에 적는다` |
| 3 | 15 원본 검문 · 장부 파일(C3 · B1) | ★ `validate_raw`(exit 2) · ★ `write_report` · `--report`; `wikiPaths` 에 `report` · `failure` · `inventory` | `[feat] : codewiki - 정제가 원본 꼴을 먼저 검사하고 지도 옆에 버림 장부를 쓴다` |
| 3 | 16 Python 패스 0(S3) | 타입 변수 · 형 별칭 · 함수 꼴 TypedDict 수집 | `[feat] : codewiki - 파이썬 정제가 모듈 속성에서 타입 변수, 형 별칭, 함수 꼴 TypedDict 를 미리 모은다` |
| 3 | 17 Python 해소(S3 · S5) | 점 경로 꼬리 맞춤 · 빌트인 · 사유 분리; **완료 조건 이 저장소 미해결 0 · 결함 0** | `[fix] : codewiki - 파이썬 이름 해소가 점 경로 꼬리와 형 별칭을 따라가 이 저장소의 미해결 버림을 0 으로 만든다` |
| 3 | 18 inventory · compdb 규약(E1 · F7) | ★ `source_inventory.py`; `mergeEntries` 가 상대경로를 풀고 중복을 `dropped` 로; manifest `inventory_sha256` | `[feat] : codewiki - prep 이 언어별 소스 inventory 를 쓰고 compile_commands 의 상대경로와 중복 설정을 규약대로 다룬다` |
| 3 | 19 coverage 절(S1 · F8) | `--report` · `--inventory` · `--failure`; `collect-failed` · `report-stale` · `unknown-kind` · `unresolved-drop` · `inventory-stale` · `language-not-collected` · `coverage-gap`(34코드); `REPORT_ONLY` 둘 | `[feat] : codewiki - verify-graph 가 장부, inventory, 수집 실패 기록을 범위 절로 읽고 미해결 버림과 모르는 종류를 막는다` |
| 3 | 20 수집 실패 기록 · `--collect-only` · `derive.py`(C5 · C6) | ★ `proc.run`(stderr 꼬리 · `collect-failure.json`) · ★ `derive.py`; `facts.py --generation` | `[feat] : codewiki - prep 이 실패한 단계와 stderr 꼬리를 기록으로 남기고 파생물 생성을 derive 로 뗀다` |
| 3 | 21 `GraphFaultReport`(C5) | 믹스인이 결함 문서 · 핸드오프를 쓴다; ★ `collect-graph.md`; `collect-graph` 가 실패 기록으로 보고 | `[feat] : codewiki - 수집 실패도 결함 문서와 핸드오프로 남긴다, 결함 보고 믹스인을 collect-graph 와 verify-graph 가 함께 쓴다` |
| 3 | 22 `derive-facts`(S6 · C6) | ★ `DeriveFactsStage` · `RANKING` · `ORDER` 15 · `ALIASES["prep"]`; `outline-wiki` · `write-wiki` 가 `RANKING` 을 읽고 검문 | `[feat] : codewiki - 단계 순서에 derive-facts, 파생물은 검사를 지난 지도에서만 그 generation_id 로 만든다` |
| 3 | 23 골든 재정제 · B4 절차(S2 · G3 · G4) | 골든 변수 있을 때만 도는 시험 · 핸드오프에 Mac 절차 | `[test] : codewiki - 골든 원본 재정제 대조 시험과 B4 판정 절차` |
| 3 | 24 3단계 문서 | README · 레코드 · 15단계 · Gotcha · `resource/CLAUDE.md` · ARCHITECTURE · 핸드오프 표시 | `[docs] : codewiki - 15단계와 장부, inventory, 수집 실패 기록, derive-facts 설명, 레코드, 핸드오프 3단계 표시` |
| — | 25 최종 시험 | 게이트 여섯 · 적대적 파일(10 통과 · 2 xfail) · 레코드 검사(`-o` 필수 · `prep` 뒤 · 기준선과 식별 대조) · `prep` 3회 · 러너 `--dry-run` · `--only prep --cold` · `--only schedule-batches` · 깨진 사본 · 빈 `out/`; 실패 시 bisect | — |

## 4~6단계 — 개요

| 단계 | 일(핸드오프 · 검토 항목) | 정한 것 | 남은 것(❓) | 끝났다는 증거 |
|---|---|---|---|---|
| 4 사실 모델 · 안정 id · 후단 열쇠 | D1 선언된 메서드 **전량** 승격 · E2 안정 id `언어:한정이름(인자형)`(C++ 은 `const` 포함; §5.6 충돌 0) · E3 C# `MethodRec` 인자 형 · F5 `terms_db` · `survey` 의 결합 열쇠를 `symbol_id` 로(이름은 표시; 일대다에서 임의 선택 없음) · F6 `Edge.sites: NotRequired[list[Site]]`(`Site = {file, line, label}`) — **Task 전에 diff 를 사용자에게 보인다** · 적대적 시험 5 · 12 un-xfail | 👍 전량 + 조사 필터 · 👍 `Edge.sites` · 👍 S4 문구 | ❓ 조사 필터 기본값(`is_public`? 가중치?) · ❓ 재귀를 자기 간선으로 둘지 — `layer_of` 의 `in_cycle` 에 영향 · ❓ id 안정성 시험 집합 · ❓ 봉인 계약 — `terms-db.json` 열쇠의 뜻이 바뀐다(계약 판과 Mode 1.5 용어 찾기를 같은 변경에서, diff 먼저) | 골든 C++ 메서드 열쇠 충돌 0 · id 둘 · 이름 하나 → 용어 레코드 둘 · 접힌 호출이 위치를 보존 · `terms-db.json` 이 지도를 되돌린다 |
| 5 언어별 메서드 · 호출 수집 | D2 C# `InvocationExpressionSyntax` 루프, **해소와 후보를 따로**(F11 — `CandidateSymbols[0]` 은 해소가 아니다) · D3 C++ 경로는 D4 **뒤** 결정 · D4 언어별 손 정답(호출 지점 단위, 검토의 사례 목록) — 지원 범위마다 정밀도 **와** 재현율 · D5 자유 함수 · F7 단일 설정 선언을 `capabilities` 에 · C# 수집기 manifest(`Program.cs` 가 소스 목록 · 해시 → `raw_provenance: "collector"`) | 👍 단일 설정 · 👍 후보 ≠ 해소 | ❓ §4.3-6 C++ 도구 — `debug.DumpCallGraph` · clangd · libclang/LibTooling — D4 정답으로 결정 | 언어별 정밀도 · 재현율 · 호출 간선에 sites · `capabilities.calls` 는 측정한 곳만 true |
| 6 언어별 병합 · 투영 | E1 은 **3단계에서 끝남**(보고) · E4 `language` → `languages` + 노드별 언어(계약 변경 — diff 먼저) · E5 언어별 정제 뒤 병합, **같은 generation 만** · E6 언어 간 호출은 범위 밖으로 문서화 · H1 TypeScript 수집기 — `scip-typescript` vs tree-sitter 를 정답 집합으로(Q3 권고 C) · Q2 성공 기록의 언어별 `capabilities` | 👍 보고 먼저(3단계), 병합 나중 · 👍 Q3 는 6단계에서 | ❓ §4.3-7 병합 방식 · ❓ H1 도구 · ❓ Q2 꼴 | 이 저장소의 성공 기록이 `ts` · `cs` 를 수집됨 또는 사유 있는 미지원으로 적음; 병합 지도가 언어별 capabilities 와 함께 `verify-graph` 를 지남 |

## ❓ 미결 — 이 계획 자체의 것

| # | 질문 | 근거 | 권고 `[내 판단]` | 막는 단계 |
|---|---|---|---|---|
| S4-filter | 메서드 전량이 노드가 된 뒤 조사 필터 기본값 | 노드 5.7배 / 3.5배(핸드오프 §4.2); `is_public` 있음(`survey_plan.py:226`) | 기본 공개 표면(`is_public`), `--all-symbols` 로 넓힘; 골든에서 배치 수를 양쪽으로 재고 정한다 | 4 |
| S4-self | 재귀를 자기 간선으로 둘지 | `layer_of` 가 자기 루프를 순환으로 봄; PageRank 무영향; UML 보기 잡음 | D4 가 재귀의 필요를 보일 **때까지** 장부만 | 4 |
| §4.3-6 | C++ 호출 도구 | 검토 §3 표; `clangd_refs.py` 선례; LibTooling API 안정성(clang 문서) | D4 정답을 `DumpCallGraph` 와 clangd 에 먼저 돌린다(둘은 이미 탐색); 위치나 id 가 빠질 때만 libclang | 5 |
| H1 · Q3 · Q2 | TS 수집기 · tree-sitter 역할 · 언어별 기록 칸 | 핸드오프 §5.6 · 11-05 계획 🌳 Q3 표 | 11-05 계획과 같음(C · 6단계) | 6 |
| — | 11-13 교차 점검의 Q1' · Q5' · Q6' · Q7' | 그 문서 §9 | **이 계획의 것이 아니다** — R0 · R1' 트랙. Q7'(가짜 `claude` 규약의 집)은 여기서 막지 않는다: 이 계획의 어느 Task 도 LLM 세션을 띄우지 않는다 | — |

## 🔀 충돌 매트릭스 — 이 트랙의 다른 문서

| 문서 | 이 계획 뒤의 상태 | 관계 |
|---|---|---|
| `2026-11-05-codegraph-verify-unify-plan.md` · `.ko.md` | 1 · 2단계 이력(완료); 3~6단계 개요는 **superseded**(Task 0 표시) | "Decided" 행은 여전히 유효하고 이 계획의 표에 옮겼다 |
| `2026-11-05-…-resume-handoff.md` | §2 체크리스트가 항목 장부(Task 7 · 12 · 24 가 표시); 머리말이 여기를 가리킴(Task 0) | §7 의 지도 안 `verification` 설계: superseded 주석(Task 0) |
| `2026-11-08-codegraph-stage3-design.md` · `.ko.md` | **흡수** — S1~S6 유효; Task 개요 → Task 13~24 | 의도한 편차 셋: 장부 없음 → `report-stale`(coverage), `unreadable` 아님 · `VerifiedGraph` 가 `fit` · 배치 · 순위 계보까지 봄(그쪽은 sha 만) · `collect-failure.json` 을 `collect-graph` **와** `verify-graph` 가 읽음 |
| `2026-11-09-codegraph-adversarial-review.md` + 폴더 | 이 계획의 **출처**; Task 0 이 커밋; 반례 12건은 `test_graph_adversarial.py` | 채택: F1~F4 · F6(`sites` 로) · F7(선언) · F8(네 절) · F9(원자적) · F10 · F11(후보 분리). 기각(👍): 사실 저장소 + 투영 · generation 디렉터리 · writer 잠금 · 다중 설정 수집 · 계약 6종 전체 · 시험 정책 재개 |
| `2026-11-13-h4-review-recommendations-handoff.md` | 손대지 않음; §3 은 11-13 교차 점검 §8 로 대체(그 세션의 배너, Task 0 이 커밋) | R2(`collect_hotspot` 변경 결합)는 **Task 22 뒤**(`facts.py` 가 `derive-facts` 뒤로; Task 20 이 `facts.main` 에 `--generation` 을 더함 — R2 는 `collect_hotspot` 을 고치므로 겹치지 않음). R3~R7: 파일 겹침 없음 |
| `2026-11-13-h4-adversarial-review-handoff.md` | Task 0 이 커밋; Q2' · Q3' · Q4' 는 이 계획의 Decided 표로 **답함**(Task 0 Step 4b 가 그 옆에 적음) | 그 문서의 💭 "3단계는 R1' 뒤 승인" 은 👍 2026-11-13 "R1 은 별개 트랙" 으로 **뒤집혔다** — 우연이 아니라 의도로 다시 열 수 있게 여기 적는다. R0 · R1' · R4' · R7' 는 독립 진행; R0 ③(레코드 선검사 `terms_db.py --reading … -o <임시>`)은 Task 25 Step 1 의 레코드 검사와 같은 명령이지만 시점이 둘이다 — R0 ③ 이 Before, Task 25 가 After 이고 식별로 대조한다 |
| 병렬 세션의 작업 트리 수정(작성 시점 미커밋) | 사용자에게 `git status --short` 를 보인 뒤 Task 0 커밋에 함께 | 머리말 정정만; 코드 없음 |

## ⚠️ 알려진 한계 · 미검증

- Task 2~24 의 어느 것도 이 세션에서 돌리지 않았다 — "⏭ 기대" 는 읽은 코드에서 낸 예측이다; 실측 둘은 재현된 반례 12건(🔵 바이트 동일 재실행)과 inventory 수 `cs 1 · py 125 · ts 13`(`-z` 없는 `git ls-files` 라 비 ASCII 경로가 빠진 값 — 정본 끝 절이 대체).
- 다른 `TypedDict` 를 **상속**한 `TypedDict`(`FreshnessDoc(SectionDoc)`)의 `msgspec` 디코딩 `[미검증]` — 거부하면 JSON 을 바꾸지 않고 칸을 펼친다.
- `COLLECTOR[lang]` 은 `Lang` 리터럴 열쇠다; `source_inventory.build_inventory` 의 `# pyright: ignore` 는 대안이고 `cast(Lang, lang)` 하나가 낫다.
- 네 단계의 `reads` 에 `GRAPH_VERIFIED` · `CODEGRAPH` · `RANKING` 을 더하면 시뮬레이터 ⑤ 산출물 사슬 검사가 `--only` 실행에 요구하는 것이 바뀐다(`--only annotate-symbols` 는 디스크의 성공 기록을 요구). 이것이 F3 의 의도다; 옛 허용을 못박은 `test_mode1.py` 시험이 있으면 **그 시험의 기대**를 고친다 — 구멍을 못박은 시험이었다.
- `module-dep-mismatch` 는 이 세션에서 읽은 `normalize._assemble`(`normalize.py:489-498`)을 반영한다; 실제 지도 시험(`test_이_저장소_지도는_…`, 결함 0)이 심판이다 — 어긋나면 규칙이 틀린 것이다.
- C# 원본 덤프는 5단계까지 `raw_provenance: "unknown"` — 보고만, 막지 않음. 성공 기록을 읽는 쪽이 `unknown` 을 `fresh` 로 읽어서는 안 된다.
- 4단계 `Edge.sites` 와 6단계 `languages` 는 `codegraph_types.py` 를 바꾼다; 둘 다 Task 시작 전에 diff 를 보인다(👍 2026-11-04 규칙).
- 이 기계의 로컬 `out/` 은 2026-09-19 것이다(🔵 11-13 교차 점검); Task 25 의 첫 `prep` 은 재수집한다 — 기대된 일이다. 교차 점검의 "로컬 `resume.json` 으로 `--resume` 하지 말라" 는 Task 25 에도 적용된다: `--cold` · `--only` 만.
- 이 번역본은 **요약**이다(👍 2026-11-13 한 건 예외). Q6' 이 전역 규칙을 유지하면 그때 확장한다.

## ➕ 승인 뒤에 더한 것 (2026-11-14 ~ 2026-11-21)

| 커밋 | 무엇 | 왜 |
|---|---|---|
| `19eac4b` | 1차 모듈 아래의 점 이름을 외부 노드로 접지 않고 `이름 해소 실패` 로 센다 | 사용자 결정 — 1차 모듈이 외부 노드로 나타나서는 안 된다 |
| `ae3bbc2` | 전수조사가 계획 도장(`_shards/.plan`, `batches.json` 의 sha256)을 대조하고 다른 계획의 샤드를 `_shards/_stale/` 로 옮긴다 | 사용자 결정, 설계 A — 샤드와 읽기 레코드가 성공 기록 ↔ 배치 사슬 밖에 있었다 |
| `2026-11-14-codegraph-pre-final-test-subplan.md` 의 Task A · B · B2 · C | 수집기 범위 · 파생 산출물 실패 · 파일 집계 · 문서 | 그 계획 참조 |

Task 25 는 그 하위 계획 Task D 의 기대값으로 돈다. 3단계 글이 몰랐던 사실 둘: 커밋 `49bcb7b` … `6f7fdde` 는 단독으로는 초록이 아니고(사유 문자열 하나가 `14ddbbe` 까지 `DROP_CLASS` 밖이었다), 이 저장소는 `public.handoff/` 아래 C++ 파일 하나를 추적하므로 수집하지 않은 언어가 cpp · cs · ts 다.
