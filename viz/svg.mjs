// <include file="machine/comments.xml" path="//term[@id='svg.mjs']"/>
// Graphviz 가 낸 SVG 를 HTML 본문에 그대로 넣을 수 있게 다듬는 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/svg.mjs
// Graphviz 가 낸 SVG 를 HTML 본문에 인라인할 수 있는 형태로 정규화한다.
// 규칙: 헤더 제거 / width·height 제거하고 viewBox 유지 / id 접두사.

const PT_TO_PX = 4 / 3;

/**
 * @param {string} raw       dot -Tsvg_inline 출력
 * @param {string} idPrefix  한 페이지에 SVG 가 2개 이상일 때의 충돌 방지 접두사
 * @returns {{svg: string, naturalWidthPx: number|null, naturalHeightPx: number|null}}
 */
export function inlineSvg(raw, idPrefix) {
  const start = raw.indexOf("<svg");
  if (start === -1) throw new Error("<svg> 엘리먼트를 찾지 못했다");

  const rest = raw.slice(start);
  const tagEnd = rest.indexOf(">");
  let openTag = rest.slice(0, tagEnd + 1);
  const body = rest.slice(tagEnd + 1);

  const w = openTag.match(/\bwidth="([\d.]+)pt"/);
  const h = openTag.match(/\bheight="([\d.]+)pt"/);
  const naturalWidthPx = w ? Math.round(Number(w[1]) * PT_TO_PX) : null;
  const naturalHeightPx = h ? Math.round(Number(h[1]) * PT_TO_PX) : null;

  // width/height 제거. viewBox 는 그대로 둔다 — 반응형 축소는 CSS 가 맡는다.
  openTag = openTag.replace(/\s+(?:width|height)="[^"]*"/g, "");

  let svg = openTag + body;

  // id 정의와 그 참조 3종을 함께 치환한다. 하나라도 빠지면 clipPath/marker 가 깨진다.
  svg = svg.replace(/\bid="([^"]+)"/g, (_, id) => `id="${idPrefix}-${id}"`);
  svg = svg.replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${idPrefix}-${id})`);
  svg = svg.replace(/\b(xlink:href|href)="#([^"]+)"/g, (_, attr, id) => `${attr}="#${idPrefix}-${id}"`);

  return { svg, naturalWidthPx, naturalHeightPx };
}
