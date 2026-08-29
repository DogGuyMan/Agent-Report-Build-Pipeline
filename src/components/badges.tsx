// <include file="docs/codegraph/comments.xml" path="//term[@id='badges.tsx']"/>
// 확신도 배지와 상태 태그 두 조각이 있는 파일.
// src/components/badges.tsx — theme.css 의 확신도·상태 배지 구획에 대응
import type { Conf, StatusVariant, ReactNode } from "../types.js";

/** tier 가 함의하는 기본 이모지. conf.emoji 로 덮어쓸 수 있다. */
const TIER_EMOJI: Record<Conf["tier"], string> = {
  green: "🔵",
  amber: "🟡",
  red: "💭",
};

// <include file="docs/codegraph/comments.xml" path="//term[@id='ConfBadge']"/>
// 확신도 배지 한 개를 그린다. 이모지와 숫자가 함께 나온다.
export function ConfBadge({ conf }: { conf: Conf }) {
  const emoji = conf.emoji ?? TIER_EMOJI[conf.tier];
  return <span className={`conf-badge conf-${conf.tier}`}>{`${emoji} ${conf.anchor}`}</span>;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='StatusTag']"/>
// 상태 태그를 그린다. 색 계열만 정해 주고 문구는 자유다.
export function StatusTag({ variant, children }: { variant: StatusVariant; children: ReactNode }) {
  return <span className={`status-tag status-${variant}`}>{children}</span>;
}
