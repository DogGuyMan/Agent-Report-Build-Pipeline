// <include file="machine/comments.xml" path="//term[@id='types.ts']"/>
// 보고서 조각들이 주고받는 자료의 모양만 적어 둔 파일. 실행되는 코드가 없다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/src/types.ts — props 타입만. 런타임 코드 없음.
import type { ReactNode } from "react";

/** E축 확신도 티어. D축은 이후 단계(소급 검증 통과 후)까지 도입하지 않는다. */
export type ConfTier = "green" | "amber" | "red";

/** 상태 배지의 색 계열. 문구는 자유 문자열이므로 children 으로 받는다. */
export type StatusVariant = "proposed" | "accepted" | "superseded";

export interface Conf {
  tier: ConfTier;
  /** 정수 앵커. 정본에 "실측" 같은 문자열 사례가 있어 string 도 허용한다. */
  anchor: number | string;
  /** tier 가 함의하는 이모지를 덮어쓴다. 정본의 tier/이모지 불일치 2건 재현용. */
  emoji?: string;
}

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


/** 용어 분류. 그래프 노드의 색 계열을 정한다. */
export type TermKind = "decision" | "artifact" | "concept" | "tool";

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

/** viz/svg.mjs 의 반환 형태. */
export interface InlinedSvg {
  svg: string;
  naturalWidthPx: number | null;
  naturalHeightPx: number | null;
}

export interface DiagramPanel {
  title: string;
  diagram: InlinedSvg;
}

export interface LegendItem {
  color: string;
  label: string;
}

export type { ReactNode };
