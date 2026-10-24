# split-work/ — 두 저장소 분리 작업 동안만 쓰는 대조 도구

리소스 · 코드 분리(rev.4 Phase R)와 그 뒤 Task 가 **출력을 바이트로 보존하는지** 재는 도구다. 제품 코드가 아니라
`pyright` · `gen_readme` · 게이트 시험의 대상이 아니다. 산출물(`before*/` · `after*/` · `fixture-shards/` · `patches/` ·
`frag/` · `reading-mode*.json`)은 이 기계의 절대 경로가 실려 git 밖이다(`.gitignore`). 분리가 끝나면(Phase B 뒤) 지운다.

저장소 뿌리에서 돌린다. `capture.sh` 는 자기 폴더의 부모(= 저장소 뿌리)를 `TOOLS_ROOT` 로 잡는다 — rev.4 본문의
`$TOOLS_ROOT/split-work/…` 는 `TOOLS_ROOT=$PWD` 로 읽는다.

| 파일 | 하는 일 |
|---|---|
| `capture.py <저장소> <출력> <샤드폴더>` | 고정 입력으로 프롬프트 · 뼈대 · VitePress 설정 글 14개를 찍는다. 이름마다 `.txt`(끝 줄바꿈 하나로 맞춤) · `.raw`(그대로) |
| `capture.sh <저장소> <출력>` | `capture.py` + `modules.dot` · `classes.dot` + 실제 `report-spec build` 의 `report.html` — 31개. Graphviz 15.1.1 의 `mincross.c` 단언은 `classes.dot` 이 써졌으면 넘긴다 |
| `edge_dump.py <트리>` | Mode 1 프롬프트 함수 · `FIX` · 재조사 절 · `check_shard` 출력을 경계 입력 128개로 돌려 JSON 을 stdout 에 낸다. 옛 트리(`git archive <기준> \| tar -x -C <폴더>`)와 후보 트리를 각각 돌려 `cmp`. `python -I` 로 돌린다 |
| `extract.py <파일.py> <줄> <출력>` | 파이썬 문자열 하나를 `{{이름}}` 리소스 글로 옮긴다 — `.format` 이스케이프를 풀고 f-문자열 식은 `slotN` 으로 |
| `split_reading.py <terms-reading.json> <mode1 출력> <mode2 출력>` | 전수조사 레코드를 두 저장소 몫으로 가른다(A4) |
| `r9-gate-proto/` | R9 품질 검토가 남긴 게이트 강화 원형 — 아래 |

## 쓰는 꼴

```bash
.venv/bin/python bin/report-wiki prep .                      # out/codegraph-raw/codegraph.json 이 없으면 먼저
split-work/capture.sh "$PWD" split-work/before                # 기준 — 31개
split-work/capture.sh "$PWD" split-work/after && diff -r split-work/before split-work/after && echo 같다
```

## r9-gate-proto/ — `test/test_prompt_resources.py` 를 조이는 원형

R9 품질 검토(2026-10-24)의 Important 둘을 재현하고 고친 판을 미리 돌려 본 진단 스크립트다. 셋 다 첫 인자로 저장소 뿌리를 받는다.

| 파일 | 보여 주는 것 | HEAD `5837c32` 기대 출력 |
|---|---|---|
| `stricter.py <뿌리>` | 고친 게이트 둘을 한 번에 — ① 긴 글 게이트가 f-문자열(`ast.JoinedStr`)의 글자 조각을 **합쳐** 잰다(I1) ② 템플릿 고아 게이트가 소스의 부분 문자열이 아니라 **문자열 상수와 같은 값**으로 찾고, basename 중복을 따로 낸다(I2) | `gate1+fstr: ['viz/build.py:125']` · `dup basenames: []` · `orphans(exact const): []` |
| `scan_evasion.py <뿌리> <폴더…>` | 게이트를 비켜 가는 꼴 셋 — f-문자열 · 문자열 목록 · `+` 이어붙이기 | `runner viz machine tools` 로 돌리면 `LIST runner/mode1/survey.py:26`(R10 의 `prompt_names` 튜플 — 프롬프트 이름 목록이라 **오탐**) · `FSTR viz/build.py:125`(진짜 — HTML 문서 뼈대 15줄) |
| `scan_long.py <뿌리> <폴더…>` | 지금 게이트 기준(상수 하나 ≥6줄 또는 ≥200자)을 다른 폴더에 대면 무엇이 걸리나 — 범위 판단(M2)용 | `machine tools` 로 돌리면 `tools/doctor.py:98`(`python -c` 7줄 스크립트) 하나 |

고치는 순서(재개 문서 §5 (1)): `stricter.py` 의 두 갈래를 게이트에 옮긴다 → `viz/build.py:125` 의 뼈대를 `viz/templates/report/page.html.tmpl` 로 옮기고 `render_file` 로 채운다(본체 · 사용자 승인 · 게이트 조이기와 **한 커밋**) → `report.html` 이 바이트로 같은지 `capture.sh` 로 본다.
