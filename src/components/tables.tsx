// src/components/tables.tsx — theme.css 의 .card/.table-wrap/table 구획에 대응
import type { Decision, ReactNode } from "../types.js";
import { ConfBadge, StatusTag } from "./badges.js";

function Card({ children }: { children: ReactNode }) {
  return <div className="card table-wrap">{children}</div>;
}

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

export interface OptionRow {
  cells: ReactNode[];
  recommended: boolean;
}

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

export type LockVerdict = "consistent" | "unrelated" | "conflicting";

const VERDICT_LABEL: Record<LockVerdict, string> = {
  consistent: "일치",
  unrelated: "무관",
  conflicting: "상충",
};

export interface LockRow {
  lockId: string;
  claim: string;
  verdict: LockVerdict;
  note: string;
}

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
