// src/runtime/term-graph.ts — 용어 관계 그물 그래프의 런타임.
//
// **이 파일만이 산출물에 실려 브라우저에서 실행된다.** 나머지 src/ 는 전부 빌드 시점 전용이다.
// 산출물 불변식상 <script> 는 1개까지이므로 이 번들 하나로 끝낸다.
//
// 노드 규모는 수십 개다(용어집). 조사 문서의 임계값 "노드 2천 미만이면 d3+SVG 로 충분" 에 해당해
// WebGL·GPU 시뮬레이션을 쓰지 않는다.
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from "d3-force";
import type { Simulation, SimulationNodeDatum, SimulationLinkDatum } from "d3-force";
import { select } from "d3-selection";
import { zoom, zoomIdentity } from "d3-zoom";
import { drag } from "d3-drag";

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

const SVG_NS = "http://www.w3.org/2000/svg";
const el = (name: string, cls?: string) => {
  const n = document.createElementNS(SVG_NS, name);
  if (cls) n.setAttribute("class", cls);
  return n;
};

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

  const svgEl = container.querySelector("svg.term-graph-svg") as SVGSVGElement | null;
  const tip = container.querySelector(".term-graph-tip") as HTMLElement | null;
  if (!svgEl) return;

  const w = container.clientWidth || 800;
  const h = container.clientHeight || 460;
  svgEl.setAttribute("viewBox", "0 0 " + w + " " + h);

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

  const sim: Simulation<Node, Link> = forceSimulation<Node>(nodes)
    .force("link", forceLink<Node, Link>(links).id((d) => d.id).distance(96).strength(0.5))
    .force("charge", forceManyBody().strength(-420))
    .force("center", forceCenter(w / 2, h / 2))
    .force("collide", forceCollide(28))
    .on("tick", () => {
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
          d.fx = ev.x;
          d.fy = ev.y;
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
}

function boot() {
  document.querySelectorAll<HTMLElement>(".term-graph").forEach(build);
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
