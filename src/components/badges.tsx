// src/components/badges.tsx — theme.css 의 확신도·상태 배지 구획에 대응
import type { Conf, StatusVariant, ReactNode } from "../types.js";

/** tier 가 함의하는 기본 이모지. conf.emoji 로 덮어쓸 수 있다. */
const TIER_EMOJI: Record<Conf["tier"], string> = {
  green: "🔵",
  amber: "🟡",
  red: "💭",
};

export function ConfBadge({ conf }: { conf: Conf }) {
  const emoji = conf.emoji ?? TIER_EMOJI[conf.tier];
  return <span className={`conf-badge conf-${conf.tier}`}>{`${emoji} ${conf.anchor}`}</span>;
}

export function StatusTag({ variant, children }: { variant: StatusVariant; children: ReactNode }) {
  return <span className={`status-tag status-${variant}`}>{children}</span>;
}
