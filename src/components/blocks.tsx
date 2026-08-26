// src/components/blocks.tsx — 경고·신고·분류 박스 계열
import type { ReactNode } from "../types.js";

export function NewStructNote({
  kind, implementers, consumers, deletionTest, grepEvidence,
}: {
  kind: string; implementers: number; consumers: number;
  deletionTest: string; grepEvidence: string;
}) {
  return (
    <div className="newstruct-note">
      <div><strong>종류</strong> — {kind}</div>
      <div><strong>구현자 {implementers}</strong> · <strong>소비자 {consumers}</strong> (grep, now)</div>
      <div><strong>삭제 테스트</strong> — {deletionTest}</div>
      <div className="mono">{grepEvidence}</div>
    </div>
  );
}

export function Reversal({
  rev, previous, now, reason,
}: { rev: string; previous: string; now: string; reason: string }) {
  return (
    <div className="reversal-note">
      <div className="note-title">⚠ {rev} 번복 기록</div>
      <div><strong>이전</strong> — {previous}</div>
      <div><strong>현재</strong> — {now}</div>
      <div><strong>근거</strong> — {reason}</div>
    </div>
  );
}

export function Correction({ target, correction }: { target: string; correction: string }) {
  return (
    <div className="correction-note">
      <div className="note-title">⚠ 정정</div>
      <div><strong>대상</strong> — {target}</div>
      <div><strong>정정</strong> — {correction}</div>
    </div>
  );
}

export interface TriageItem {
  id: string;
  title: string;
  why: string;
}

export function TriageBlock({ items }: { items: TriageItem[] }) {
  return (
    <div className="triage-block">
      <div className="note-title">먼저 볼 것</div>
      <ol>
        {items.map((it) => (
          <li key={it.id}>
            <span className="mono">{it.id}</span> {it.title}
            <div className="triage-why">{it.why}</div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export type { ReactNode };
