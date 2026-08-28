import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: "v1",
  slug: "llm-load-reduction",
  specName: "Track C — LLM 전수조사 부담 감축 조사·구현 계획",
  date: "2026-08-28",
  branch: "feat/report-builder",
  decisions: [
    {
      id: "D1",
      title: "계측기를 먼저 만든다 — 모든 “줄였다” 주장은 measure_citation_origin.py 로 잰다 (Task 1)",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: 95 },
      optionCount: 0,
    },
    {
      id: "D2",
      title: "C-19 · calls[] 는 roslyn-dump.json 에만 넣고 codegraph.json 의 edges[] 로 승격하지 않는다 (Task 2·3·4)",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: 90 },
      optionCount: 3,
    },
    {
      id: "D3",
      title: "C-20 · WarmUp 캐시는 파일별 요약 단위, 무효화는 git blob SHA, 판정은 유효 / 낡음 / 판정불가 3값 (Task 5)",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "amber", anchor: 72 },
      optionCount: 0,
    },
    {
      id: "D4",
      title: "C-21 · 모듈을 정독 / 개요 2계층으로 가른다 — PageRank 누적 60% · 순환 참여 · hotspot 상위10 (Task 6)",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "amber", anchor: 62 },
      optionCount: 0,
    },
    {
      id: "D5",
      title: "U3 · 검증 가능한 코드 규약은 이번 계획에서 구현하지 않는다 — 격차를 모르고 규약부터 만들면 거울 함정",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: 90 },
      optionCount: 0,
    },
    {
      id: "D6",
      title: "C++ calls[] 는 보류 — clang-uml 이 호출을 내지 않는다. C# 에서 이득이 확인된 뒤 검토",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "amber", anchor: 70 },
      optionCount: 0,
    },
  ],
};
