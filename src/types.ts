// <include file="docs/codegraph/comments.xml" path="//term[@id='types.ts']"/>
// 보고서 조각들이 주고받는 자료의 모양만 적어 둔 파일. 실행되는 코드가 없다.
// src/types.ts — props 타입만. 런타임 코드 없음.
import type { ReactNode } from "react";

// <include file="docs/codegraph/comments.xml" path="//term[@id='ConfTier']"/>
// 확신도 색 계열 세 값. green · amber · red.
/** E축 확신도 티어. D축은 이후 단계(소급 검증 통과 후)까지 도입하지 않는다. */
export type ConfTier = "green" | "amber" | "red";

// <include file="docs/codegraph/comments.xml" path="//term[@id='StatusVariant']"/>
// 상태 태그의 색 계열 세 값.
/** 상태 배지의 색 계열. 문구는 자유 문자열이므로 children 으로 받는다. */
export type StatusVariant = "proposed" | "accepted" | "superseded";

// <include file="docs/codegraph/comments.xml" path="//term[@id='Conf']"/>
// 확신도 하나의 모양. 색 계열과 숫자 앵커, 그리고 덮어쓸 이모지.
export interface Conf {
  tier: ConfTier;
  /** 정수 앵커. 정본에 "실측" 같은 문자열 사례가 있어 string 도 허용한다. */
  anchor: number | string;
  /** tier 가 함의하는 이모지를 덮어쓴다. 정본의 tier/이모지 불일치 2건 재현용. */
  emoji?: string;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='Decision']"/>
// 결정 하나의 모양. 번호 · 제목 · 상태 · 확신도 · 옵션 수.
export interface Decision {
  /** "D0", "D1" — report.tsx 의 절 제목과 대조된다(링크 무결성 검사). */
  id: string;
  title: string;
  variant: StatusVariant;
  statusText: string;
  conf: Conf;
  /** 옵션 비교표를 가진 결정이면 옵션 수. 없으면 0. */
  optionCount: number;
}


// <include file="docs/codegraph/comments.xml" path="//term[@id='TermKind']"/>
// 용어 분류 네 값. 결정 · 산출물 · 개념 · 도구. 그래프 노드 색을 정한다.
/** 용어 분류. 그래프 노드의 색 계열을 정한다. */
export type TermKind = "decision" | "artifact" | "concept" | "tool";

// <include file="docs/codegraph/comments.xml" path="//term[@id='Term']"/>
// 용어 하나의 모양. 정의는 이 배열 한 곳에만 쓴다.
/**
 * 용어 하나. **정의는 여기 한 곳에만 쓴다** — 본문·그래프·용어집이 전부 이 배열에서 나온다.
 * 읽는 사람은 배경 지식이 없다고 가정한다. `short` 와 `body` 를 그 눈높이로 쓴다.
 */
export interface Term {
  /** 본문에서 참조하는 키. 예: "C-19", "calls[]" */
  id: string;
  /** 그래프 노드에 표시되는 짧은 이름 */
  label: string;
  /** 커서를 올렸을 때 뜨는 한 줄. 문장으로 쓴다 */
  short: string;
  /** 용어집 절에만 나오는 자세한 설명 */
  body?: string;
  kind: TermKind;
  /** 이어지는 다른 용어의 id. 방향 없는 그물 간선이 된다 */
  links?: string[];
  /** Mode 1.5 가 실측한 읽는 사람의 이해도. 없으면 "미측정" 으로 표시된다 */
  mental?: "확실" | "애매" | "모름";
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='ReportData']"/>
// 보고서 하나가 갖는 결정 데이터 전부의 모양.
export interface ReportData {
  /** ~/report-builder 의 git 태그. build 시 현재 버전과 대조된다. */
  builderVersion: string;
  slug: string;
  specName: string;
  date: string;
  branch: string;
  decisions: Decision[];
  /** 용어집. 없으면 용어 기능이 통째로 빠진다 */
  terms?: Term[];
  /**
   * 경로 링크가 파일을 찾을 때 더 뒤지는 절대 경로 폴더. 외부 저장소의 산출물(예: 대상 저장소의
   * out/codegraph-raw)을 가리킬 때 쓴다. 없으면 보고서 폴더 · specs/ · 저장소 루트 · out/codegraph-raw 만 본다
   */
  linkRoots?: string[];
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='InlinedSvg']"/>
// 인라인된 SVG 하나의 모양. 본문 문자열과 원본 가로·세로 픽셀.
/** scripts/svg.mjs 의 반환 형태. */
export interface InlinedSvg {
  svg: string;
  naturalWidthPx: number | null;
  naturalHeightPx: number | null;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='DiagramPanel']"/>
// 다이어그램 한 쪽의 모양. 제목과 SVG.
export interface DiagramPanel {
  title: string;
  diagram: InlinedSvg;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='LegendItem']"/>
// 다이어그램 범례 한 줄. 색과 설명.
export interface LegendItem {
  color: string;
  label: string;
}

export type { ReactNode };
