// <include file="machine/comments.xml" path="//term[@id='page.tsx']"/>
// 보고서의 뼈대(머리말 · 본문 자리 · 꼬리말)를 만드는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/src/page.tsx — 보고서 골격. 개별 보고서의 report.tsx 가 children 을 채운다.
import type { ReportData, ReactNode } from "./types.js";

export function Page({ data, children }: { data: ReportData; children: ReactNode }) {
  return (
    <div className="page">
      <header className="header">
        <div>
          <div className="eyebrow">설계 검토 보고서</div>
          <h1>{data.specName}</h1>
        </div>
        <div className="meta">
          <div><strong>{data.date}</strong></div>
          <div className="mono">{data.branch}</div>
          <div className="mono">{data.slug}</div>
        </div>
      </header>
      {children}
      <footer className="page-footer">
        report-builder {data.builderVersion} · {data.slug}
      </footer>
    </div>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
