// <include file="machine/comments.xml" path="//term[@id='blocks.tsx']"/>
// 경고 · 번복 · 정정 · 분류 같은 네모 상자 조각들이 있는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/src/components/blocks.tsx — 경고·신고·분류 박스 계열
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

/**
 * 실측 근거와 주관 판단을 **별개 행**으로 갈라놓는 주석 블록.
 * 인계 문서 §5 — "객관 사실과 💭 주관 판단을 한 문장에 섞지 않는다" 를 마크업으로 강제한다.
 *
 * 문장 분리는 호출자가 배열로 넘긴다. 마침표로 자동 분할하지 않는다 —
 * 실제 본문에 `geometry.cpp:231`, `material_property_block.h:70-89` 같은
 * 마침표 포함 토큰이 흔해서 휴리스틱이 깨진다.
 */
export function EvidenceNote({
  measured, judged,
}: { measured: ReactNode[]; judged?: ReactNode[] }) {
  return (
    <div className="newstruct-note">
      <div className="note-row">
        <span className="conf-badge conf-green">🔵 실측</span>
        <div className="note-body">
          {measured.map((p, i) => <p key={i}>{p}</p>)}
        </div>
      </div>
      {judged && judged.length > 0 && (
        <div className="note-row">
          <span className="conf-badge conf-red">💭 판단</span>
          <div className="note-body">
            {judged.map((p, i) => <p key={i}>{p}</p>)}
          </div>
        </div>
      )}
    </div>
  );
}
