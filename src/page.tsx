// <include file="docs/codegraph/comments.xml" path="//term[@id='page.tsx']"/>
// 보고서의 뼈대(머리말 · 본문 자리 · 꼬리말)를 만드는 파일.
// src/page.tsx — 보고서 골격. 개별 보고서의 report.tsx 가 children 을 채운다.
import type { ReportData, ReactNode } from "./types.js";

// <include file="docs/codegraph/comments.xml" path="//term[@id='Page']"/>
// 보고서 한 장의 뼈대. 머리말 · 본문 자리 · 꼬리말을 그린다.
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

// <include file="docs/codegraph/comments.xml" path="//term[@id='Section']"/>
// 제목이 붙은 본문 절 하나를 감싼다.
export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
