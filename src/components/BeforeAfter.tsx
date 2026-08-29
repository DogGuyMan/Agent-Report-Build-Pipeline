// <include file="docs/codegraph/comments.xml" path="//term[@id='BeforeAfter.tsx']"/>
// 바뀌기 전후 다이어그램을 나란히 놓는 조각이 있는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// src/components/BeforeAfter.tsx
// B1 결함 복구가 여기에 걸려 있다.
// 원본 폭(px)을 --svg-w 로 주입해야 theme.css 의 "실제 크기" 모드가 동작한다.
import type { CSSProperties } from "react";
import type { DiagramPanel, LegendItem } from "../types.js";

// <include file="docs/codegraph/comments.xml" path="//term[@id='Panel']"/>
// 다이어그램 한 쪽(전 또는 후)을 그린다.
// 쓰는 것: 없음 · 쓰이는 곳: BeforeAfter
function Panel({ side, panel }: { side: "before" | "after"; panel: DiagramPanel }) {
  const style = panel.diagram.naturalWidthPx
    ? ({ ["--svg-w"]: `${panel.diagram.naturalWidthPx}px` } as CSSProperties)
    : undefined;
  return (
    <div className={`diagram-panel ${side}`}>
      <div className="panel-title">{panel.title}</div>
      <div className="svg-wrap" style={style}
           dangerouslySetInnerHTML={{ __html: panel.diagram.svg }} />
    </div>
  );
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='BeforeAfter']"/>
// 바뀌기 전후 다이어그램 두 장을 나란히 놓고 확대 토글을 붙인다.
// 쓰는 것: Panel · 쓰이는 곳: 없음
export function BeforeAfter({
  id, before, after, legend,
}: { id: string; before: DiagramPanel; after: DiagramPanel; legend: LegendItem[] }) {
  const toggleId = `zoom-${id}`;
  return (
    <>
      <input type="checkbox" className="zoom-toggle" id={toggleId} />
      <label className="zoom-label" htmlFor={toggleId} />
      <div className="diagram-grid">
        <Panel side="before" panel={before} />
        <Panel side="after" panel={after} />
      </div>
      {legend.length > 0 && (
        <div className="diagram-legend">
          {legend.map((l) => (
            <span key={l.label}>
              <i style={{ background: l.color }} />
              {l.label}
            </span>
          ))}
        </div>
      )}
    </>
  );
}
