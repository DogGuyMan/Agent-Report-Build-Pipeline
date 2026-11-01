# split-work/ — 분리 작업 동안만 쓰는 바이트 대조 도구. 제품 코드가 아니다

> 루트 나침반은 [`../CLAUDE.md`](../CLAUDE.md). 파일별 설명과 쓰는 꼴은 [`README.md`](README.md) 에 있다 — 여기 다시 적지 않는다.

## 이 모듈이 소유하는 것 (Owns)

`split-work/**`. 소유하지 않는 것 — 대조 대상인 `resource/**` 와 `src/**`. 여기 도구는 대상을 고치지 않고 찍어서 비교만 한다.

## 작업 흐름 (Workflow)

리소스나 코드를 옮기거나 프롬프트 꼴을 고친 Task 는 앞뒤 출력이 바이트로 같은지로 끝낸다. 저장소 루트에서 기준을 찍고, 고친 뒤 다시 찍어 비교한다:

```bash
.venv/bin/python bin/report-wiki prep .        # out/codegraph-raw/codegraph.json 이 없으면 먼저
split-work/capture.sh "$PWD" split-work/before
split-work/capture.sh "$PWD" split-work/after && diff -r split-work/before split-work/after && echo 같다
```

## 비직관적인 것 (Gotchas)

- **Warning:** 산출물(`before*/` · `after*/` 따위)에는 이 기계의 절대 경로가 실린다. `.gitignore` 가 막으니 커밋하지 않는다.
- **주의:** `pyright` · `gen_readme` · 게이트 시험이 이 폴더를 보지 않는다. 여기 파일을 망가뜨려도 게이트는 빨개지지 않는다.
- 분리가 끝나면(Phase B 뒤) 이 폴더를 지운다. 지울 때 루트 `CLAUDE.md` 표의 `split-work/` 행도 함께 지운다.

## 다른 모듈과의 의존 (Cross-module dependencies)

| 방향 | 무엇 |
|---|---|
| 여기 → `../bin/report-wiki` | `capture.sh` 가 먼저 `prep` 으로 코드 지도를 만들어 둬야 돈다 |
| 여기 → `../src/` · `../resource/` | 대조 대상. `capture.py` 가 프롬프트 · 뼈대 · VitePress 설정 글을 찍는다 |
| 바깥 → 여기 | **없다.** 제품 코드 · 시험 · 게이트 어디서도 이 폴더를 부르지 않는다 |
