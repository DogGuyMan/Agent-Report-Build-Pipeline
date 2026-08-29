# HANDOFF ⑫ — Mode 2 관계도 조정 슬라이더(임시) + 덩어리 충돌 (mode-2-spec-report 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 17:45).** `mode-2-spec-report` DONE_WITH_CONCERNS(`shake` 훅 추가). 사용자가 슬라이더로 값을 확정 — `REPEL_IN -200 · REPEL_OUT -200 · REPEL_MAX_DIST 410 · GRAVITY 0.035 · BOUNDS_SCALE 2.5 · LINK_DISTANCE 90 · LINK_STRENGTH 0.35 · COLLIDE_RADIUS 49 · GROUP_PAD 24 · GROUP_STRENGTH 0.6`. 오케스트레이터가 `KNOBS` 에 박고 두 보고서의 `tune` 을 뗐다(기본 꺼짐, 기능은 남음). ⑪ 과 함께 `6ef58b3` 로 커밋. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.
> 앞선 ⑪(척력 약화 · 2배 상자)은 미커밋 상태로 작업 트리에 있다 — 이 작업이 그 위에 쌓인다.

**사용자 지시 (2026-08-29 17:05)** — (1) "지금은 독립 그래프끼리 너무 겹친다. 덩어리의 볼록 껍질이나 경계(사각형·원)를 얻어 서로 겹치지 못하게 할 수 없나?
context7 로 레퍼런싱해라." (2) "일단 임시로 슬라이더 바를 하단에 넣어 — 테스트용 휴리스틱 값을 찾기 위해."

**context7 실측** — `/d3/d3-force`: 그룹·덩어리 충돌 힘은 **없다**. 커스텀 힘(`force(alpha)` + `initialize`)이 공식 방식. `forceCollide` 는 겹침을 **속도**로 푼다.
`/d3/d3-polygon`: `polygonHull` 이 볼록 껍질을 주지만(설치 안 됨) 껍질끼리 충돌 판정은 없다. → **덩어리마다 경계 사각형(AABB) + 여백**을 매 틱 계산해 겹치면 양쪽을 밀어내는 커스텀 힘.

**설계** — 조정 상수 8개 + 새 상수 2개(`GROUP_PAD` `GROUP_STRENGTH`)를 살아 있는 `KNOBS` 객체로. `TermGraph` 에 `tune?: boolean` prop(추가만) → `data-tune` → 런타임이 그래프 **아래**에 슬라이더 패널을
만든다(같은 번들, `<script>` 1 유지). 슬라이더를 움직이면 힘을 갱신하고 시뮬레이션을 다시 데운다. 현재 값을 `const …` 줄로 보여 주는 칸 — 사용자가 복사해 넘긴다.
두 보고서에 `tune` 을 **임시로** 켠다. 값이 정해지면 상수로 박고 `tune` 을 끈다.

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — 7블록. 소유: `src/runtime/term-graph.ts` · `src/runtime/graph-math.ts` · `src/components/terms.tsx`(`TermGraph` 만) · `src/theme.css`(추가만) · `test/graph-math.test.mjs` · `test/components.test.mjs`(추가만) · 두 보고서 `report.tsx` 의 `<TermGraph …>` 한 줄.
