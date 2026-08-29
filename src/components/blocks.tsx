// <include file="docs/codegraph/comments.xml" path="//term[@id='blocks.tsx']"/>
// 경고 · 번복 · 정정 · 분류 같은 네모 상자 조각들이 있는 파일.
// src/components/blocks.tsx — 경고·신고·분류 박스 계열
import type { ReactNode } from "../types.js";

// <include file="docs/codegraph/comments.xml" path="//term[@id='NewStructNote']"/>
// 새 구조를 들일 때 근거를 적는 상자. 구현자 수와 소비자 수를 함께 보인다.
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

// <include file="docs/codegraph/comments.xml" path="//term[@id='Reversal']"/>
// 옛 결정을 뒤집은 기록 상자. 이전 · 현재 · 근거 세 줄이다.
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

// <include file="docs/codegraph/comments.xml" path="//term[@id='Correction']"/>
// 잘못 적은 것을 바로잡는 상자. 대상과 정정 두 줄이다.
export function Correction({ target, correction }: { target: string; correction: string }) {
  return (
    <div className="correction-note">
      <div className="note-title">⚠ 정정</div>
      <div><strong>대상</strong> — {target}</div>
      <div><strong>정정</strong> — {correction}</div>
    </div>
  );
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='TriageItem']"/>
// 먼저 볼 것 목록의 한 줄이 갖는 모양. id · 제목 · 이유.
export interface TriageItem {
  id: string;
  title: string;
  why: string;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='TriageBlock']"/>
// 먼저 볼 것 목록 상자. 보고서 맨 위에 놓는다.
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

// <include file="docs/codegraph/comments.xml" path="//term[@id='EvidenceNote']"/>
// 실측 근거와 주관 판단을 별개 행으로 갈라 놓는 상자.
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
