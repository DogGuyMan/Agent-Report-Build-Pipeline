// <include file="machine/comments.xml" path="//term[@id='graph-math.ts']"/>
// 관계도 런타임이 쓰는 순수 계산만 모아 둔 파일.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/src/runtime/graph-math.ts — 관계도 런타임의 순수 계산.
// 브라우저 API 를 쓰지 않아 node --test 로 고정한다.

/**
 * 이어진 노드끼리 같은 번호를 매긴다(연결 성분).
 * 모르는 id 가 든 간선은 무시한다. 링크 없는 노드는 혼자 한 덩어리다.
 */
export function components(ids: string[], edges: [string, string][]): Map<string, number> {
  const parent = new Map<string, string>();
  for (const id of ids) parent.set(id, id);
  const find = (x: string): string => {
    let r = x;
    while (parent.get(r) !== r) r = parent.get(r) as string;
    while (parent.get(x) !== r) {
      const next = parent.get(x) as string;
      parent.set(x, r);
      x = next;
    }
    return r;
  };
  for (const [a, b] of edges) {
    if (!parent.has(a) || !parent.has(b)) continue;
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  }
  const index = new Map<string, number>();
  const out = new Map<string, number>();
  for (const id of ids) {
    const r = find(id);
    if (!index.has(r)) index.set(r, index.size);
    out.set(id, index.get(r) as number);
  }
  return out;
}

/** 노드가 움직일 수 있는 상자. 캔버스 중심 기준 가로·세로 scale 배. */
export function bounds(w: number, h: number, scale: number) {
  const hw = (w * scale) / 2;
  const hh = (h * scale) / 2;
  return { minX: w / 2 - hw, maxX: w / 2 + hw, minY: h / 2 - hh, maxY: h / 2 + hh };
}

/** 값을 [min, max] 안으로 자른다. */
export function clampBox(v: number, min: number, max: number): number {
  return v < min ? min : v > max ? max : v;
}

/** 경계 사각형(AABB). 덩어리가 차지한 자리를 나타낸다. */
export interface Rect {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

/**
 * 두 사각형이 (여백 pad 를 포함해) 겹치면 겹침이 작은 축과 그 양, 그리고 a 가 움직일 방향(sign)을 준다.
 * 안 겹치면 null. 겹침이 작은 축으로 미는 이유는 그쪽이 더 짧은 이동으로 빠져나오기 때문이다.
 */
export function rectOverlap(a: Rect, b: Rect, pad: number): { axis: "x" | "y"; amount: number; sign: 1 | -1 } | null {
  const ox = Math.min(a.maxX, b.maxX) - Math.max(a.minX, b.minX) + 2 * pad;
  const oy = Math.min(a.maxY, b.maxY) - Math.max(a.minY, b.minY) + 2 * pad;
  if (ox <= 0 || oy <= 0) return null;
  if (ox < oy) return { axis: "x", amount: ox, sign: a.minX + a.maxX <= b.minX + b.maxX ? -1 : 1 };
  return { axis: "y", amount: oy, sign: a.minY + a.maxY <= b.minY + b.maxY ? -1 : 1 };
}
