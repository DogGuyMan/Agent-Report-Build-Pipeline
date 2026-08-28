// src/components/terms.tsx — 용어집 계열
// 정의는 data.ts 의 terms 배열 한 곳에만 있다. 본문·용어집·그래프가 모두 그것을 읽는다.
import type { Term, TermKind, ReactNode } from "../types.js";

const KIND_LABEL: Record<TermKind, string> = {
  decision: "결정",
  artifact: "산출물",
  concept: "개념",
  tool: "도구",
};

/**
 * 용어 목록을 묶어 인라인 참조 컴포넌트를 돌려준다.
 * 전역 변수도 React 컨텍스트도 쓰지 않는다 — 빌드 시점 함수 호출 하나다.
 *
 *   const T = defineTerms(data.terms ?? []);
 *   <T id="C-19" />
 */
export function defineTerms(terms: Term[]) {
  const byId = new Map(terms.map((t) => [t.id, t]));
  return function TermRef({ id, children }: { id: string; children?: ReactNode }) {
    const t = byId.get(id);
    // 정의가 없으면 조용히 넘어가지 않는다. 화면에 드러내야 저자가 고친다.
    if (!t) return <span className="term-ref term-missing">{children ?? id}</span>;
    return (
      <span className="term-ref" tabIndex={0}>
        {children ?? t.label}
        <span className="term-card">
          <span className="term-card-head">
            <span className={`term-kind term-kind-${t.kind}`}>{KIND_LABEL[t.kind]}</span>
            {t.id}
          </span>
          <span className="term-card-body">{t.short}</span>
        </span>
      </span>
    );
  };
}

/** 용어집 절. 정의 전량을 한 번에 보인다. */
export function Glossary({ terms }: { terms: Term[] }) {
  return (
    <div className="card table-wrap">
      <table>
        <thead>
          <tr>
            <th>용어</th>
            <th>갈래</th>
            <th>뜻</th>
          </tr>
        </thead>
        <tbody>
          {terms.map((t) => (
            <tr key={t.id}>
              <td className="mono">{t.id}</td>
              <td><span className={`term-kind term-kind-${t.kind}`}>{KIND_LABEL[t.kind]}</span></td>
              <td>
                <div>{t.short}</div>
                {t.body && <div className="term-body">{t.body}</div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * 용어 관계 그물 그래프.
 *
 * 마크업만 빌드 시점에 내고 좌표 계산과 조작은 런타임 스크립트가 한다.
 * 데이터는 `data-terms` 속성에 실어 보낸다 — `<script type="application/json">` 을 쓰면
 * 산출물 불변식(`<script>` 개수)이 2가 되어 깨진다.
 */
export function TermGraph({ terms, height = 460 }: { terms: Term[]; height?: number }) {
  const payload = JSON.stringify(
    terms.map((t) => ({ id: t.id, label: t.label, short: t.short, kind: t.kind, links: t.links ?? [] }))
  );
  return (
    <div className="term-graph" data-terms={payload} style={{ height: `${height}px` }}>
      <svg className="term-graph-svg" />
      <div className="term-graph-tip" hidden />
      <div className="term-graph-hint">노드를 끌어 옮기고, 커서를 올리면 뜻이 뜬다. 빈 곳을 끌면 화면이 움직이고 휠로 확대된다.</div>
    </div>
  );
}
