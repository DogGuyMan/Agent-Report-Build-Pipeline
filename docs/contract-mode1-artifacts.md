# Mode 1 산출물 계약 v1 — Mode 1 이 봉인하고 Mode 1.5 · 2 가 판정한다

**정본은 `contracts/mode1-artifacts.v1.json` 이다.** 이 문서는 그것을 사람이 읽게 푼 것이다. 두 저장소로 갈리면
이 문서와 `contracts/` 의 두 파일은 양쪽에 같은 사본으로 산다. 코드는 서로를 부르지 않는다 — 결정 [`0011`](decisions/0011-split-mode1-and-report.md).

| 대상 저장소 안의 자리 (git 추적) | 만드는 것 (Mode 1) | 읽는 것 (Mode 1.5 · 2) |
|---|---|---|
| `<대상>/docs/codegraph/manifest.json` | `machine/manifest.py` · 마지막 단계 `seal-artifacts` | `machine/evidence.py` |
| `<대상>/docs/codegraph/terms-db.json` | 봉인이 작업 파일(`out/codegraph-raw/terms-db.json`)을 복사해 낸다 | `report-term collect` · `term-benchmark` 스킬 |
| `<대상>/docs/wiki/*.md` | `write-wiki` 단계 | Mode 2 에이전트 프롬프트(봉인돼 있을 때만) |

형은 생산자 쪽 `machine/manifest.py` 의 `ArtifactManifest` 와 `machine/terms_db.py` 의 `TermsDb` 다.
`tools/gen_contract.py` 가 그 둘에서 계약 JSON 과 지문(`contracts/mode1-artifacts.v1.sha256`)을 내고,
`tools/gen_contract_types.py` 가 계약 JSON 에서 소비자 형 `machine/contract_types.py` 를 되낸다. 둘 다 `--check` 로 낡음을 잡는다.

## 실행 규칙

- **Mode 1 은 사람이 부를 때만 돈다.** 무엇도 대신 돌리지 않고 묻지도 않는다 — 시작할 때 예상 비용 한 줄만 찍는다.
  다시 돌린 뒤 `docs/codegraph/` 와 `docs/wiki/` 를 커밋하는 것도 사람이다.
- **Mode 1.5 는 봉인이 없으면 돌지 않는다.** `report-term collect` 는 봉인 자리(`<대상>/docs/codegraph/terms-db.json`)의
  용어 사전만 받고, 봉인 뒤 소스가 움직였으면 경고하고 있는 자료로 돈다(그 파일의 용어에 `stale` 표시).
- **Mode 2 는 Mode 1 과 독립이다.** 봉인이 있으면 에이전트 프롬프트에 근거로 싣고, 없거나 깨져도 돈다.
  `report-spec init` 과 `run_mode2.py` 는 봉인 상태 한 줄(`evidence.py --status`)을 찍는다.

## 봉인 — 무엇을 싣나

그 실행에서 검사기(`verify-terms` · `verify-wiki`)를 통과하고 **지금 소스를 다시 읽은** 것만 싣는다.

- **소스 집합** — git 이 추적하는 파일 중 언어의 확장자에 맞고, 경로의 어느 성분도 건너뛸 폴더가 아닌 것
  (`machine/declmap.py` 의 `tracked_files` · `SKIP_DIRS`). 매니페스트가 그 규칙(`source_exts` · `skip_dirs`)과
  파일마다의 git blob id(`inputs`)를 함께 적어, 읽는 쪽이 Mode 1 을 몰라도 같은 규칙으로 다시 잰다.
- **어느 종류든** 소스 파일마다의 지문이 지난 전수조사의 지문(`out/codegraph-raw/snapshot.json`)과 같아야 한다.
  다르면 봉인하지 않는다(exit 3) — 해결은 Mode 1 증분 실행 하나다. 다시 읽지 않고 봉인만 고치는 길은 없다.
- **wiki** 는 그 위에 `write-wiki` 가 그 지문을 따라잡았다는 표(`out/codegraph-raw/wiki-state.json`)가 있어야 한다.
  `write-wiki` 는 위키가 따라잡은 시점의 소스 지도(`sources`)와 지금 지문을 견주어 바뀐 파일을 인용하는 장만 다시 쓰고,
  사람이 고친 장은 `docs/wiki/.bak/` 에 덮지 않는 이름으로 옮겨 둔다. 기준이 없어 기존 장의 신선도를 모르면
  따라잡았다고 적지 않고, 그 실행의 봉인은 위키를 빼고 `terms-db` 만 싣는다.
- 실패한 실행은 새로 봉인하지 않고 이전 봉인에 `superseded_by`(실패한 단계 · 시각)만 적는다. 읽는 쪽은 경고로 본다.

## 판정 — 구조 문제와 낡음

`machine/evidence.py <저장소> --need terms-db,wiki` 가 판정한다.

| 갈래 | 무엇 | 종료 |
|---|---|---|
| 구조 문제 | 봉인 없음 · 계약 판 다름 · 필요한 종류 없음 · 봉인 뒤 산출물이 바뀜 · 봉인 뒤 위키 장이 생김 · `terms-db.json` 이 계약 꼴이 아님 | 1 (사람이 칠 명령을 함께 찍는다) |
| 낡음 | 봉인 뒤 소스가 바뀜 · 생김 · 사라짐, 봉인이 커밋되지 않음, 뒤 실행 실패 표식 | 0 (경고) |

보고서 원고(`data.ts` · `report.tsx`) 커밋은 대상 저장소의 언어가 `ts` 가 아니면 소스 집합의 확장자 밖이라 낡음이 아니다.
`ts` 저장소에서는 원고가 `생김` 으로 잡힌다 — 경고일 뿐 멈추지 않는다. `--list` 는 통과하면 봉인된 경로와 낡음을 JSON 으로,
`--status` 는 어느 경우든 한 줄(`Mode 1 봉인 — 없음` · `있음 · 낡음 N건 · 미커밋` · `깨짐: …`)과 exit 0 을 낸다.

## 판 올림

열쇠를 더하는 것은 같은 판이다. 빼거나 뜻을 바꾸면 `v2` 파일을 새로 만든다. 생산자 쪽에서 `tools/gen_contract.py` 로
내고, 두 저장소로 갈린 뒤에는 `contracts/` 의 두 파일을 소비자 쪽으로 복사한 다음 `tools/gen_contract_types.py` 로 형을 다시 낸다.
