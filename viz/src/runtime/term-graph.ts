// <include file="machine/comments.xml" path="//term[@id='term-graph.ts']"/>
// 용어 관계 그물을 브라우저에서 그리는 코드. src 에서 유일하게 산출물에 실린다.
// 쓰는 것: d3-force · 쓰이는 곳: 없음
// viz/src/runtime/term-graph.ts — 용어 관계 그물 그래프의 런타임.
//
// **이 파일만이 산출물에 실려 브라우저에서 실행된다.** 나머지 viz/src/ 는 전부 빌드 시점 전용이다.
// 산출물 불변식상 <script> 는 1개까지이므로 이 번들 하나로 끝낸다.
//
// 노드 규모는 수십 개다(용어집). 조사 문서의 임계값 "노드 2천 미만이면 d3+SVG 로 충분" 에 해당해
// WebGL·GPU 시뮬레이션을 쓰지 않는다.
import { forceSimulation, forceLink, forceX, forceY, forceCollide } from "d3-force";
import type { Simulation, SimulationNodeDatum, SimulationLinkDatum } from "d3-force";
import { select } from "d3-selection";
import { zoom, zoomIdentity } from "d3-zoom";
import { drag } from "d3-drag";
import { components, bounds, clampBox, rectOverlap } from "./graph-math.js";
import type { Rect } from "./graph-math.js";

// -- 조정 손잡이 -- 값은 사용자가 tune 슬라이더로 육안 판정해 확정한 것(2026-08-29 17:40). 바꾸려면 여기 숫자를, 실험은 <TermGraph tune /> 로
// 상수가 아니라 객체인 이유: 슬라이더가 값을 바꾸면 힘이 다음 틱부터 그대로 읽어 가게 하려고.
const KNOBS = {
  REPEL_IN: -200, // 같은 덩어리(이어진 그래프) 안에서 노드끼리 밀어내는 세기
  REPEL_OUT: -200, // 서로 다른 덩어리 사이의 세기 - 약하게
  REPEL_MAX_DIST: 410, // 이 거리(px) 밖에서는 아예 밀지 않는다
  GRAVITY: 0.035, // 노드마다 화면 가운데로 끄는 힘
  BOUNDS_SCALE: 2.5, // 움직일 수 있는 상자 = 캔버스 x 이 값 (중심 기준)
  LINK_DISTANCE: 90, // 이어진 두 노드가 놓이고 싶어 하는 거리(px)
  LINK_STRENGTH: 0.35, // 그 거리를 지키려는 세기
  COLLIDE_RADIUS: 49, // 노드끼리 겹치지 않게 두는 반지름(px)
  GROUP_PAD: 24, // 덩어리 경계 사각형 바깥 여백(px) - 이만큼 떨어져야 안 겹친 것
  GROUP_STRENGTH: 0.6, // 덩어리를 밀어내는 세기 (0~1)
};
type Knob = keyof typeof KNOBS;
// 슬라이더가 쓸 범위 [min, max, step]
const KNOB_RANGES: Record<Knob, [number, number, number]> = {
  REPEL_IN: [-900, 0, 10],
  REPEL_OUT: [-400, 0, 5],
  REPEL_MAX_DIST: [40, 900, 10],
  GRAVITY: [0, 0.3, 0.005],
  BOUNDS_SCALE: [1, 4, 0.1],
  LINK_DISTANCE: [30, 260, 5],
  LINK_STRENGTH: [0, 1, 0.05],
  COLLIDE_RADIUS: [4, 70, 1],
  GROUP_PAD: [0, 150, 2],
  GROUP_STRENGTH: [0, 1, 0.05],
};
const KNOB_DEFAULTS = { ...KNOBS };

interface RawTerm {
  id: string;
  label: string;
  short: string;
  kind: string;
  links: string[];
}
interface Node extends SimulationNodeDatum {
  id: string;
  label: string;
  short: string;
  kind: string;
}
type Link = SimulationLinkDatum<Node>;

/** 알파를 받아 속도를 고치는 힘. d3 가 시작할 때 initialize 로 노드 배열을 넘겨 준다. */
type RepelForce = ((alpha: number) => void) & { initialize?: (nodes: Node[]) => void };

// <include file="machine/comments.xml" path="//term[@id='componentRepulsion']"/>
// 노드끼리 서로 밀어내는 힘. 같은 무리인지 아닌지에 따라 세기를 달리한다.
// 쓰는 것: KNOBS · 쓰이는 곳: term-graph.build
/**
 * d3 forceManyBody 를 대신하는 쌍 전수 척력.
 * 같은 덩어리는 REPEL_IN, 다른 덩어리는 REPEL_OUT, REPEL_MAX_DIST 밖은 0.
 * 세 값은 틱마다 KNOBS 에서 새로 읽는다 - 슬라이더로 바꾼 값이 바로 먹게.
 * 노드 수십 개라 O(n^2) 로 충분하다.
 */
function componentRepulsion(comp: Map<string, number>): RepelForce {
  let ns: Node[] = [];
  const force: RepelForce = (alpha: number) => {
    const maxD2 = KNOBS.REPEL_MAX_DIST * KNOBS.REPEL_MAX_DIST;
    for (let i = 0; i < ns.length; i++) {
      const a = ns[i];
      for (let j = i + 1; j < ns.length; j++) {
        const b = ns[j];
        let dx = (b.x ?? 0) - (a.x ?? 0);
        let dy = (b.y ?? 0) - (a.y ?? 0);
        let d2 = dx * dx + dy * dy;
        if (d2 === 0) {
          // 겹친 두 점은 살짝 떼어 준다(d3 의 jiggle 과 같은 뜻)
          dx = 1e-3 * (i - j);
          dy = 1e-3;
          d2 = dx * dx + dy * dy;
        }
        if (d2 > maxD2) continue;
        const strength = comp.get(a.id) === comp.get(b.id) ? KNOBS.REPEL_IN : KNOBS.REPEL_OUT;
        const k = (strength * alpha) / d2; // d3 forceManyBody 와 같은 꼴 - 음수면 서로 멀어진다
        a.vx = (a.vx ?? 0) + dx * k;
        a.vy = (a.vy ?? 0) + dy * k;
        b.vx = (b.vx ?? 0) - dx * k;
        b.vy = (b.vy ?? 0) - dy * k;
      }
    }
  };
  force.initialize = (nodes: Node[]) => {
    ns = nodes;
  };
  return force;
}

// <include file="machine/comments.xml" path="//term[@id='componentCollide']"/>
// 무리끼리 겹치지 않게 통째로 밀어내는 힘.
// 쓰는 것: rectOverlap, KNOBS · 쓰이는 곳: term-graph.build
/**
 * 덩어리(연결 성분)의 경계 사각형이 여백을 두고 겹치면 양쪽 덩어리를 통째로 밀어낸다.
 * d3-force 에는 그룹 단위 충돌 힘이 없어 직접 만든다. forceCollide 와 같은 꼴로 속도(vx/vy)를 고쳐 푼다.
 * 덩어리 수가 적어 쌍 전수 비교로 충분하다.
 */
function componentCollide(comp: Map<string, number>): RepelForce {
  let ns: Node[] = [];
  const force: RepelForce = () => {
    // 매 틱 덩어리마다 경계 사각형(AABB)을 다시 잰다
    const groups = new Map<number, Rect & { members: Node[] }>();
    for (const n of ns) {
      const c = comp.get(n.id) ?? -1;
      const x = n.x ?? 0;
      const y = n.y ?? 0;
      const g = groups.get(c);
      if (!g) {
        groups.set(c, { minX: x, maxX: x, minY: y, maxY: y, members: [n] });
      } else {
        if (x < g.minX) g.minX = x;
        if (x > g.maxX) g.maxX = x;
        if (y < g.minY) g.minY = y;
        if (y > g.maxY) g.maxY = y;
        g.members.push(n);
      }
    }
    const list = [...groups.values()];
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const r = rectOverlap(list[i], list[j], KNOBS.GROUP_PAD);
        if (!r) continue;
        // 절반씩 나눠 서로 반대로 민다. 한 틱에 너무 튀지 않게 12px 로 막는다.
        const push = Math.min(r.amount / 2, 12) * KNOBS.GROUP_STRENGTH;
        for (const m of list[i].members) {
          if (r.axis === "x") m.vx = (m.vx ?? 0) + r.sign * push;
          else m.vy = (m.vy ?? 0) + r.sign * push;
        }
        for (const m of list[j].members) {
          if (r.axis === "x") m.vx = (m.vx ?? 0) - r.sign * push;
          else m.vy = (m.vy ?? 0) - r.sign * push;
        }
      }
    }
  };
  force.initialize = (nodes: Node[]) => {
    ns = nodes;
  };
  return force;
}

// <include file="machine/comments.xml" path="//term[@id='mountTune']"/>
// 힘 세기를 눈으로 맞춰 보는 임시 슬라이더 판을 그래프 아래에 깐다.
// 쓰는 것: KNOBS · 쓰이는 곳: term-graph.build
/**
 * 임시 조정 패널 — 그래프 **아래**에 슬라이더를 깐다. `data-tune` 이 붙은 그래프에만 생긴다.
 * 눈으로 값을 찾기 위한 임시물이다. 값이 정해지면 KNOBS 기본값에 박고 tune 을 뗀다.
 * 새 <script> 를 만들지 않으려고 이 런타임 번들 안에 함께 둔다(산출물 불변식).
 */
function mountTune(container: HTMLElement, hooks: { apply: (k: Knob) => void; shake: () => void }) {
  const panel = document.createElement("div");
  panel.className = "term-graph-tune";

  // 현재 값을 KNOBS 선언에 그대로 붙여 넣을 수 있는 줄로 보여 준다
  const out = document.createElement("textarea");
  out.className = "tune-out";
  out.readOnly = true;
  const keys = Object.keys(KNOBS) as Knob[];
  const rows: { key: Knob; input: HTMLInputElement; view: HTMLOutputElement }[] = [];
  const format = () => {
    out.value = keys.map((k) => "  " + k + ": " + KNOBS[k] + ",").join("\n");
  };

  for (const key of keys) {
    const [min, max, step] = KNOB_RANGES[key];
    const row = document.createElement("label");
    row.className = "tune-row";
    const name = document.createElement("span");
    name.className = "tune-name";
    name.textContent = key;
    const input = document.createElement("input");
    input.type = "range";
    input.min = String(min);
    input.max = String(max);
    input.step = String(step);
    input.value = String(KNOBS[key]);
    const view = document.createElement("output");
    view.textContent = String(KNOBS[key]);
    input.addEventListener("input", () => {
      KNOBS[key] = Number(input.value);
      view.textContent = input.value;
      format();
      hooks.apply(key);
    });
    row.appendChild(name);
    row.appendChild(input);
    row.appendChild(view);
    panel.appendChild(row);
    rows.push({ key, input, view });
  }

  const actions = document.createElement("div");
  actions.className = "tune-actions";
  const reset = document.createElement("button");
  reset.type = "button";
  reset.textContent = "기본값";
  reset.addEventListener("click", () => {
    for (const r of rows) {
      KNOBS[r.key] = KNOB_DEFAULTS[r.key];
      r.input.value = String(KNOB_DEFAULTS[r.key]);
      r.view.textContent = r.input.value;
      hooks.apply(r.key);
    }
    format();
  });
  const shake = document.createElement("button");
  shake.type = "button";
  shake.textContent = "다시 풀기";
  shake.addEventListener("click", () => hooks.shake());
  actions.appendChild(reset);
  actions.appendChild(shake);

  panel.appendChild(actions);
  panel.appendChild(out);
  format();
  container.insertAdjacentElement("afterend", panel);
}

const SVG_NS = "http://www.w3.org/2000/svg";
// <include file="machine/comments.xml" path="//term[@id='el']"/>
// SVG 요소 하나를 만드는 짧은 도우미.
// 쓰는 것: 없음 · 쓰이는 곳: term-graph.build
const el = (name: string, cls?: string) => {
  const n = document.createElementNS(SVG_NS, name);
  if (cls) n.setAttribute("class", cls);
  return n;
};

// <include file="machine/comments.xml" path="//term[@id='term-graph.build']"/>
// 용어 그래프 하나를 실제로 그린다.
// 쓰는 것: el, components, bounds, clampBox, componentRepulsion (+2) · 쓰이는 곳: boot
function build(container: HTMLElement) {
  const raw = container.getAttribute("data-terms");
  if (!raw) return;
  let terms: RawTerm[];
  try {
    terms = JSON.parse(raw) as RawTerm[];
  } catch {
    return; // 데이터가 깨졌으면 조용히 접는다. 보고서 본문은 그대로 읽힌다.
  }
  if (terms.length === 0) return;

  const nodes: Node[] = terms.map((t) => ({ id: t.id, label: t.label, short: t.short, kind: t.kind }));
  const known = new Set(nodes.map((n) => n.id));
  // 간선은 양쪽 끝이 모두 정의된 용어일 때만 만든다. 한쪽이 없으면 그리지 않는다.
  const seen = new Set<string>();
  const links: Link[] = [];
  for (const t of terms) {
    for (const to of t.links) {
      if (!known.has(to) || to === t.id) continue;
      const key = t.id < to ? t.id + " " + to : to + " " + t.id;
      if (seen.has(key)) continue;
      seen.add(key);
      links.push({ source: t.id, target: to });
    }
  }

  // 덩어리 나누기 - forceLink 가 source/target 을 객체로 바꾸기 **전**이라 아직 문자열 id 다. 이 순서를 지킨다.
  const comp = components(
    nodes.map((n) => n.id),
    links.map((l) => [l.source as string, l.target as string] as [string, string])
  );

  const svgEl = container.querySelector("svg.term-graph-svg") as SVGSVGElement | null;
  const tip = container.querySelector(".term-graph-tip") as HTMLElement | null;
  if (!svgEl) return;

  const w = container.clientWidth || 800;
  const h = container.clientHeight || 460;
  svgEl.setAttribute("viewBox", "0 0 " + w + " " + h);
  let box = bounds(w, h, KNOBS.BOUNDS_SCALE); // 슬라이더가 BOUNDS_SCALE 을 바꾸면 다시 잡는다

  const root = el("g", "term-graph-root");
  svgEl.appendChild(root);
  const linkLayer = el("g", "term-links");
  const nodeLayer = el("g", "term-nodes");
  root.appendChild(linkLayer);
  root.appendChild(nodeLayer);

  const linkEls = links.map(() => {
    const l = el("line", "term-link") as SVGLineElement;
    linkLayer.appendChild(l);
    return l;
  });

  const nodeEls = nodes.map((n) => {
    const g = el("g", "term-node term-kind-" + n.kind) as SVGGElement;
    const c = el("circle") as SVGCircleElement;
    c.setAttribute("r", "7");
    const label = el("text") as SVGTextElement;
    label.setAttribute("dy", "-11");
    label.setAttribute("text-anchor", "middle");
    label.textContent = n.label;
    g.appendChild(c);
    g.appendChild(label);
    nodeLayer.appendChild(g);

    const show = (ev: MouseEvent | FocusEvent) => {
      if (!tip) return;
      tip.textContent = n.id + " — " + n.short;
      tip.hidden = false;
      const box = container.getBoundingClientRect();
      const x = "clientX" in ev ? ev.clientX - box.left : box.width / 2;
      const y = "clientY" in ev ? ev.clientY - box.top : box.height / 2;
      tip.style.left = Math.min(Math.max(x + 12, 8), box.width - 12) + "px";
      tip.style.top = Math.max(y - 8, 8) + "px";
    };
    const hide = () => {
      if (tip) tip.hidden = true;
    };
    g.addEventListener("pointerenter", show);
    g.addEventListener("pointermove", show);
    g.addEventListener("pointerleave", hide);
    g.addEventListener("focus", show);
    g.addEventListener("blur", hide);
    g.setAttribute("tabindex", "0");
    return g;
  });

  // 힘을 이름 붙인 변수로 잡아 둔다 - 슬라이더가 값을 바꾸면 그 자리에서 갱신하려고
  const linkForce = forceLink<Node, Link>(links)
    .id((d) => d.id)
    .distance(KNOBS.LINK_DISTANCE)
    .strength(KNOBS.LINK_STRENGTH);
  const gx = forceX<Node>(w / 2).strength(KNOBS.GRAVITY);
  const gy = forceY<Node>(h / 2).strength(KNOBS.GRAVITY);
  const collide = forceCollide<Node>(KNOBS.COLLIDE_RADIUS);

  const sim: Simulation<Node, Link> = forceSimulation<Node>(nodes)
    .force("link", linkForce)
    .force("repel", componentRepulsion(comp))
    .force("group", componentCollide(comp))
    .force("gx", gx)
    .force("gy", gy)
    .force("collide", collide)
    .on("tick", () => {
      // 상자 밖으로 못 나간다 - 캔버스 가로 세로 BOUNDS_SCALE 배 (사용자 지시)
      for (const n of nodes) {
        n.x = clampBox(n.x ?? 0, box.minX, box.maxX);
        n.y = clampBox(n.y ?? 0, box.minY, box.maxY);
      }
      links.forEach((l, i) => {
        const s = l.source as Node;
        const t = l.target as Node;
        linkEls[i].setAttribute("x1", String(s.x ?? 0));
        linkEls[i].setAttribute("y1", String(s.y ?? 0));
        linkEls[i].setAttribute("x2", String(t.x ?? 0));
        linkEls[i].setAttribute("y2", String(t.y ?? 0));
      });
      nodes.forEach((n, i) => {
        nodeEls[i].setAttribute("transform", "translate(" + (n.x ?? 0) + "," + (n.y ?? 0) + ")");
      });
    });

  // 드래그 — 끄는 동안 물리를 데우고 놓으면 다시 식힌다.
  select(nodeLayer)
    .selectAll<SVGGElement, unknown>("g.term-node")
    .data(nodes)
    .call(
      drag<SVGGElement, Node>()
        .on("start", (ev, d) => {
          if (!ev.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (ev, d) => {
          d.fx = clampBox(ev.x, box.minX, box.maxX);
          d.fy = clampBox(ev.y, box.minY, box.maxY);
        })
        .on("end", (ev, d) => {
          if (!ev.active) sim.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
    );

  // 화면 이동과 확대. 노드 위에서는 드래그가 이기도록 filter 로 갈라 준다.
  select(svgEl).call(
    zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .filter((ev: Event) => !(ev.target instanceof Element && ev.target.closest(".term-node")))
      .on("zoom", (ev) => root.setAttribute("transform", ev.transform.toString()))
  );
  select(svgEl).call(zoom<SVGSVGElement, unknown>().transform, zoomIdentity);

  // 임시 조정 패널 — data-tune 이 있을 때만. 값을 찾으면 KNOBS 에 박고 tune 을 끈다.
  if (container.hasAttribute("data-tune")) {
    mountTune(container, {
      apply(k) {
        // 힘이 값을 미리 복사해 둔 것들만 다시 넣어 준다.
        if (k === "LINK_DISTANCE") linkForce.distance(KNOBS.LINK_DISTANCE);
        else if (k === "LINK_STRENGTH") linkForce.strength(KNOBS.LINK_STRENGTH);
        else if (k === "GRAVITY") {
          gx.strength(KNOBS.GRAVITY);
          gy.strength(KNOBS.GRAVITY);
        } else if (k === "COLLIDE_RADIUS") collide.radius(KNOBS.COLLIDE_RADIUS);
        else if (k === "BOUNDS_SCALE") box = bounds(w, h, KNOBS.BOUNDS_SCALE);
        // REPEL_* 과 GROUP_* 은 힘이 틱마다 KNOBS 를 직접 읽으므로 여기서 할 일이 없다
        sim.alpha(0.6).restart();
      },
      shake() {
        sim.alpha(1).restart(); // 같은 값으로 배치만 다시 흔든다
      },
    });
  }
}

// <include file="machine/comments.xml" path="//term[@id='mountTermCards']"/>
// 본문 용어에 커서를 올렸을 때 뜨는 뜻 카드의 자리를 잡아 준다.
// 쓰는 것: 없음 · 쓰이는 곳: boot
// 본문 용어 카드의 위치 — 뜨는 것은 CSS(:hover / :focus)가 하고, 여기서는 **위치만** 화면 기준(fixed)으로 옮긴다.
// 이유: 카드는 position:absolute 인데 표를 감싼 .table-wrap(overflow-x:auto)과 .card(overflow:hidden)가 그 상자 밖을
// 잘라 버린다(2026-08-29 사용자 관측). overflow 를 풀면 넓은 표의 가로 스크롤이 깨지므로, 화면 기준 좌표로 빼내는 쪽을 택했다.
// 화면 기준 요소는 조상의 overflow 에 잘리지 않는다. 카드가 없는 보고서에는 이 번들 자체가 실리지 않는다.
function mountTermCards() {
  let active: { ref: HTMLElement; card: HTMLElement } | null = null;
  const place = (ref: HTMLElement, card: HTMLElement) => {
    const r = ref.getBoundingClientRect();
    card.style.display = "block";
    card.style.position = "fixed";
    card.style.left = "0px";
    card.style.top = "0px";                       // 먼저 놓고 크기를 잰다
    const cw = card.offsetWidth, ch = card.offsetHeight;
    let left = r.left, top = r.bottom + 6;
    if (left + cw > window.innerWidth - 8) left = Math.max(8, window.innerWidth - 8 - cw);   // 오른쪽이 모자라면 왼쪽으로
    if (top + ch > window.innerHeight - 8) top = Math.max(8, r.top - 6 - ch);                 // 아래가 모자라면 낱말 위로
    card.style.left = left + "px";
    card.style.top = top + "px";
  };
  const clear = (card: HTMLElement) => {
    card.style.display = "";
    card.style.position = "";
    card.style.left = "";
    card.style.top = "";
  };
  document.querySelectorAll<HTMLElement>(".term-ref").forEach((ref) => {
    const card = ref.querySelector<HTMLElement>(":scope > .term-card");
    if (!card) return;
    const show = () => { active = { ref, card }; place(ref, card); };
    const hide = () => { clear(card); if (active && active.card === card) active = null; };
    ref.addEventListener("pointerenter", show);
    ref.addEventListener("focus", show);
    ref.addEventListener("pointerleave", hide);
    ref.addEventListener("blur", hide);
  });
  // 스크롤·창 크기 변경 중에는 떠 있는 카드 하나만 따라간다
  const follow = () => { if (active) place(active.ref, active.card); };
  window.addEventListener("scroll", follow, { passive: true });
  window.addEventListener("resize", follow);
}

// <include file="machine/comments.xml" path="//term[@id='boot']"/>
// 문서 안의 용어 그래프를 전부 찾아 그리기를 시작한다.
// 쓰는 것: term-graph.build, mountTermCards · 쓰이는 곳: 없음
function boot() {
  document.querySelectorAll<HTMLElement>(".term-graph").forEach(build);
  mountTermCards();
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
