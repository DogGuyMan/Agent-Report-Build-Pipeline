// src/types.ts — props 타입만. 런타임 코드 없음.
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

export interface ReportData {
  /** ~/report-builder 의 git 태그. build 시 현재 버전과 대조된다. */
  builderVersion: string;
  slug: string;
  specName: string;
  date: string;
  branch: string;
  decisions: Decision[];
}

/** scripts/svg.mjs 의 반환 형태. */
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
