// <include file="docs/codegraph/comments.xml" path="//term[@id='tables.tsx']"/>
// 결정 표 · 옵션 표 · 정본 대조 표 세 조각이 있는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// src/components/tables.tsx — theme.css 의 .card/.table-wrap/table 구획에 대응
import type { Decision, ReactNode } from "../types.js";
import { ConfBadge, StatusTag } from "./badges.js";

// <include file="docs/codegraph/comments.xml" path="//term[@id='Card']"/>
// 표를 감싸는 카드 상자. 가로 스크롤을 여기서 준다.
// 쓰는 것: 없음 · 쓰이는 곳: DecisionTable, LockTable, OptionTable
function Card({ children }: { children: ReactNode }) {
  return <div className="card table-wrap">{children}</div>;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='DecisionTable']"/>
// 결정 목록 표. 번호 · 결정 · 확신도 · 상태 · 옵션 수 다섯 칸이다.
// 쓰는 것: Card, ConfBadge, StatusTag · 쓰이는 곳: 없음
export function DecisionTable({ decisions }: { decisions: Decision[] }) {
  return (
    <Card>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>결정</th>
            <th>확신도</th>
            <th>상태</th>
            <th className="num">옵션</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((d) => (
            <tr key={d.id}>
              <td className="mono">{d.id}</td>
              <td>{d.title}</td>
              <td><ConfBadge conf={d.conf} /></td>
              <td><StatusTag variant={d.variant}>{d.statusText}</StatusTag></td>
              <td className="num mono">{d.optionCount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='OptionRow']"/>
// 옵션 비교 표의 한 줄. 칸 목록과 추천 여부를 갖는다.
// 쓰는 것: 없음 · 쓰이는 곳: OptionTable
export interface OptionRow {
  cells: ReactNode[];
  recommended: boolean;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='OptionTable']"/>
// 설계 후보를 나란히 놓는 비교 표. 추천하는 줄은 강조된다.
// 쓰는 것: Card, OptionRow · 쓰이는 곳: 없음
export function OptionTable({ columns, rows }: { columns: string[]; rows: OptionRow[] }) {
  return (
    <Card>
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={r.recommended ? "row-recommended" : undefined}>
              {r.cells.map((cell, j) => <td key={j}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='LockVerdict']"/>
// 정본 대조 판정 세 값. 일치 · 무관 · 상충.
// 쓰는 것: 없음 · 쓰이는 곳: LockRow
export type LockVerdict = "consistent" | "unrelated" | "conflicting";

const VERDICT_LABEL: Record<LockVerdict, string> = {
  consistent: "일치",
  unrelated: "무관",
  conflicting: "상충",
};

// <include file="docs/codegraph/comments.xml" path="//term[@id='LockRow']"/>
// 정본 대조 표의 한 줄. 정본 번호 · 주장 · 판정 · 비고.
// 쓰는 것: LockVerdict · 쓰이는 곳: LockTable
export interface LockRow {
  lockId: string;
  claim: string;
  verdict: LockVerdict;
  note: string;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='LockTable']"/>
// 이번 제안이 이미 확정된 결정과 어긋나지 않는지 대조하는 표.
// 쓰는 것: Card, LockRow · 쓰이는 곳: 없음
export function LockTable({ rows }: { rows: LockRow[] }) {
  return (
    <Card>
      <table>
        <thead>
          <tr>
            <th>정본 #</th>
            <th>정본 주장</th>
            <th>판정</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.lockId}>
              <td className="mono">{r.lockId}</td>
              <td>{r.claim}</td>
              <td><span className={`verdict-${r.verdict}`}>{VERDICT_LABEL[r.verdict]}</span></td>
              <td>{r.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
