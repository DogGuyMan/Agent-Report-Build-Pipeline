// <include file="machine/comments.xml" path="//term[@id='terms.tsx']"/>
// 용어집 계열 조각 셋(본문 인라인 참조 · 용어집 표 · 관계 그래프)이 있는 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/src/components/terms.tsx — 용어집 계열
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
            {t.mental && <span className={`term-mental mental-${t.mental}`}>{t.mental}</span>}
          </span>
          <span className="term-card-body">{t.short}</span>
          {t.body && <span className="term-card-more">{t.body}</span>}
        </span>
      </span>
    );
  };
}

const MENTAL_ORDER = ["모름", "애매", "확실", "미측정"] as const;

/**
 * 용어집 — 이해도 그룹별 아코디언.
 * 모름 → 애매 → 확실 → 미측정 순. 빈 그룹은 그리지 않는다. 모름 그룹만 열린 채 시작한다.
 * 접기/펼치기는 브라우저 기본 <details> 다 — 스크립트 0줄 (예산 1개는 용어 그래프가 쓴다).
 * 그룹 안 순서는 terms 배열 순서 그대로 — 정렬하지 않는다(저자가 정한 순서가 곧 서사다).
 */
export function Glossary({ terms }: { terms: Term[] }) {
  const groups = MENTAL_ORDER
    .map((m) => ({ mental: m, items: terms.filter((t) => (t.mental ?? "미측정") === m) }))
    .filter((g) => g.items.length > 0);
  return (
    <div className="card term-groups">
      {groups.map((g) => (
        <details key={g.mental} className="term-group" open={g.mental === "모름"}>
          <summary className="term-group-head">
            <span className={`term-mental mental-${g.mental}`}>{g.mental}</span>
            <span className="term-group-count">{g.items.length}</span>
          </summary>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>용어</th>
                  <th>갈래</th>
                  <th>이해도</th>
                  <th>뜻</th>
                </tr>
              </thead>
              <tbody>
                {g.items.map((t) => (
                  <tr key={t.id}>
                    <td className="mono">{t.id}</td>
                    <td><span className={`term-kind term-kind-${t.kind}`}>{KIND_LABEL[t.kind]}</span></td>
                    <td>
                      <span className={`term-mental mental-${t.mental ?? "미측정"}`}>{t.mental ?? "미측정"}</span>
                    </td>
                    <td>
                      <div>{t.short}</div>
                      {t.body && <div className="term-body">{t.body}</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}
    </div>
  );
}

/**
 * 용어 관계 그물 그래프.
 *
 * 마크업만 빌드 시점에 내고 좌표 계산과 조작은 런타임 스크립트가 한다.
 * 데이터는 `data-terms` 속성에 실어 보낸다 — `<script type="application/json">` 을 쓰면
 * 산출물 불변식(`<script>` 개수)이 2가 되어 깨진다.
 *
 * `tune` 을 켜면 `data-tune="1"` 이 붙고 런타임이 그래프 아래에 임시 조정 슬라이더를 깐다.
 * 끄면(기본) 그 속성이 아예 나오지 않아 마크업이 이전과 같다.
 */
export function TermGraph({ terms, height = 460, tune }: { terms: Term[]; height?: number; tune?: boolean }) {
  const payload = JSON.stringify(
    terms.map((t) => ({ id: t.id, label: t.label, short: t.short, kind: t.kind, links: t.links ?? [] }))
  );
  return (
    <div className="term-graph" data-terms={payload} data-tune={tune ? "1" : undefined} style={{ height: `${height}px` }}>
      <svg className="term-graph-svg" />
      <div className="term-graph-tip" hidden />
      <div className="term-graph-hint">노드를 끌어 옮기고, 커서를 올리면 뜻이 뜬다. 빈 곳을 끌면 화면이 움직이고 휠로 확대된다.</div>
    </div>
  );
}
