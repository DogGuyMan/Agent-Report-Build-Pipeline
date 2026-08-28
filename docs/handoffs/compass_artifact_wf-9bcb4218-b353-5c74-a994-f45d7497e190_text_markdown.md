# Obsidian 스타일 그래프 네트워크 렌더링을 위한 JS/TS 오픈소스 라이브러리 심층 리서치

## TL;DR
- **Obsidian 자체 그래프 뷰는 PixiJS(WebGL) 렌더러 + 자체 구현 force 시뮬레이션**으로 동작한다. Obsidian 팀은 원래 d3.js로 force 계산과 SVG 렌더링을 모두 했으나 수천 개 노트에서 성능이 부족해 PixiJS/WebGL로 교체했다고 공식적으로 밝혔다. 코어가 클로즈드 소스라 세부는 개발자 증언·리버스 엔지니어링으로만 확인된다. 가장 충실한 오픈소스 재현은 **Quartz의 graph 컴포넌트(PixiJS + d3-force, MIT)**다.
- 목적별 추천: (a) **Obsidian 룩앤필 재현** → PixiJS v8 + d3-force(Quartz 방식); (b) **10만+ 노드 GPU 가속** → cosmos.gl(WebGL GPU 시뮬레이션) 또는 WebGPU 기반 GraphWaGu/GraphGPU; (c) **그래픽스 포트폴리오용 from-scratch** → WebGL2 transform feedback / WebGPU compute shader로 직접 force 시뮬레이션 + 인스턴싱 렌더러 작성.
- 사용자의 OpenGL/C++/게임 배경은 GPGPU force 시뮬레이션(텍스처 기반 위치 업데이트, transform feedback, compute shader Barnes-Hut) 직접 구현에 직접 활용 가능하며, 채용 시장에서 차별화되는 포트폴리오가 된다.

## Key Findings

1. **Obsidian 코어 그래프 뷰**: 렌더링은 PixiJS(WebGL), 나머지는 전부 커스텀. Obsidian 팀 멤버 "Silver"는 공식 포럼(2020-06-03)에서 *"We used to use d3.js for both force simulation and SVG drawing, but the performance was subpar for thousands of notes. PIXI.js uses WebGL and is way faster."* 라고 명시했다. API가 매우 제한적이며 내부가 복잡해 공식 확장 API 제공 계획이 없다.
2. **오픈소스 재현의 대표주자는 Quartz**(정적 사이트 생성기)로, `graph.inline.ts`에서 d3-force로 시뮬레이션하고 PixiJS로 렌더링하며 @tweenjs/tween.js로 애니메이션한다. Obsidian 방식과 거의 동일한 스택이다.
3. **범용 라이브러리**는 렌더링 백엔드로 나뉜다: SVG(d3 기본, React Flow), Canvas 2D(Cytoscape.js, vis-network, force-graph 2D, G6 기본), WebGL(Sigma.js, cosmos.gl, reagraph, 3d-force-graph, VivaGraph, G6 옵션), WebGPU(GraphWaGu, GraphGPU).
4. **GPU 가속 시뮬레이션**의 최전선은 cosmos.gl(WebGL 프래그먼트/버텍스 셰이더에서 force 계산, OpenJS Foundation 인큐베이팅)과 WebGPU compute shader 프로젝트다.
5. **시뮬레이션과 렌더링 분리** 패턴(worker에서 레이아웃 + WebGL 렌더러)은 pixi-graph, Jan Zak의 Neo4j/Observable 데모, graphology의 FA2Layout worker 등에서 표준화되어 있다.

## Details

### 1. Obsidian 자체 그래프 뷰의 구현

Obsidian 코어는 클로즈드 소스다. 그러나 다음은 **확인된 사실**이다:
- **렌더링: PixiJS(WebGL)**. Obsidian 팀 멤버 "Silver"의 공식 포럼 답변(2020-06-03): *"We used to use d3.js for both force simulation and SVG drawing, but the performance was subpar for thousands of notes. PIXI.js uses WebGL and is way faster."* 또 다른 커뮤니티 개발자 joethei도 "Pixi.js가 렌더링을 담당하고 나머지는 전부 커스텀이며, 예전엔 D3였다"고 확인했다(개발자 Discord 인용).
- 버그 리포트들(mesa WebGL 깨짐, PixiJS 셰이더 문제, WebGL 메모리 누수)이 그래프 뷰가 WebGL/PixiJS로 렌더링됨을 교차 확인해 준다.
- 노드 색상은 PixiJS 컬러 포맷 `{ a: 1, rgb: 0xRRGGBB }`을 쓰며, 노드는 `renderer.nodes`에 PixiJS Text/Graphics 객체로 존재한다(플러그인 리버스 엔지니어링으로 확인). 링크는 `metadataCache.resolvedLinks`(실선)와 `unresolvedLinks`(가상 노드)로부터 PixiJS 링크 객체로 그려진다.

**추론(확정 아님)**: force 시뮬레이션은 자체 구현이며 현재는 d3-force가 아니다(과거엔 d3였음이 위 인용으로 확정). 개발팀은 "저수준 그래픽스 코드까지 동원한 대량의 내부 최적화"를 한다고 언급했다(Juggl 개발자와의 논의에서 인용). 정확한 알고리즘(Barnes-Hut 여부 등)은 공개되지 않았다.

### 2. 오픈소스 클론/재구현

#### Quartz graph 컴포넌트 (가장 충실한 재현)
- 저장소: `github.com/jackyzha0/quartz`, 라이선스 **MIT**, 별 약 12.7k / 포크 4k / 컨트리뷰터 249명. Linux Foundation LFX Insights 집계로는 13,210 stars이며 "최근 365일 중 364일 활동"으로 매우 활발.
- 구현: `quartz/components/scripts/graph.inline.ts`에서 `d3`(forceSimulation, forceRadial, zoom, drag)로 물리 계산, `pixi.js`의 Application/Container/Graphics/Text로 렌더링, `@tweenjs/tween.js`로 트윈. `/static/contentIndex.json`(ContentIndex emitter 생성)에서 링크 데이터를 가져온다.
- 별도 커뮤니티 플러그인 `quartz-community/graph`로도 분리 제공되며, D3Config(repelForce, centerForce, linkDistance, opacityScale, enableRadial 등)로 Obsidian과 유사한 파라미터를 노출한다.

#### Obsidian 커뮤니티 플러그인 (그래프 렌더링)

| 플러그인 | 렌더링 라이브러리 | 라이선스 | 유지보수 상태(2026) |
|---|---|---|---|
| **3D Graph** (AlexW00/obsidian-3d-graph) | 3d-force-graph(ThreeJS/WebGL) + D3.js | MIT | **사실상 방치**. 마지막 푸시 2023-10, 별 ~331 |
| **3D Graph New** (HananoshikaYomaru/obsidian-3d-graph) | vasturiano 3d-force-graph(ThreeJS/WebGL) | MIT | AlexW00 포크, 더 활발. 성능 이슈 자인 |
| **Juggl** (HEmile/juggl) | **Cytoscape.js**(Canvas) | 오픈소스(juggl-api) | 저활동. 로컬/서브그래프 특화, 글로벌 그래프는 느림 |
| **Extended Graph** (ElsaTam/obsidian-extended-graph) | 코어 그래프(PixiJS)에 훅으로 기능 추가 | 오픈소스, 무료 | **활발**. 2.7.7 (2025-10), 별 ~210 |
| **Advanced Graph View** (graph-insight) | **PixiJS v8(WebGL)**, worker force 레이아웃 | 커뮤니티 플러그인 | 활발. 아래 인용 참조 |
| **Three D Graph View** (Sidepath Studio) | 3D 그래프 뷰(구-표면 구형 레이아웃) | 커뮤니티 플러그인 | 신규/활발 |

Advanced Graph View 플러그인은 공식 페이지에서 *"WebGL rendering (Pixi.js v8) — 10,000+ nodes at 50+ FPS. Force layout runs in a Web Worker; the UI thread never computes physics."*라고 명시하며, 엣지는 단일 GPU line-list mesh로, 커뮤니티 검출은 Louvain + TF-IDF 자동 명명으로 구현한다. 이는 사용자가 참고할 "worker 시뮬레이션 + WebGL 렌더러" 아키텍처의 실전 사례다.

Juggl은 Cytoscape.js를 그대로 노출하므로 스타일링(CSS/YAML/Style Pane)이 강력하지만, 개발자 본인이 "Obsidian 내부 그래프보다 절대 빠를 수 없다 — Obsidian은 저수준 그래픽스 최적화를 하기 때문"이라 인정했고 10,000+ 노트 글로벌 그래프는 사용 불가라 밝혔다.

#### 퍼블리싱 도구
- **Perlite** (secure77/Perlite): PHP 기반 Obsidian Publish 대안, 그래프는 공식 Wiki에 따라 **vis.js(vis-network)**로 구현. 라이선스 MIT, 별 ~1.7k, 활발(1.6.1, 2026-01).
- **Digital Garden** (oleeskild/obsidian-digital-garden): 백링크/그래프 지원. Flowershow/Quartz Syncer/Enveloppe의 코드 기반이 됨.
- **Flowershow**: Obsidian 스타일 그래프 뷰를 **아직 지원하지 않음**(콘텐츠 렌더링 중심). 별 ~1.1k.
- **Obsidian Publish**(공식·유료): 그래프 뷰 제공하나 클로즈드 소스. 내부 렌더 라이브러리는 비공개(코어와 동일한 커스텀 canvas/WebGL force 추정).
- MkDocs용 `mkdocs-obsidian-interactive-graph-plugin`: Apache ECharts로 Obsidian 유사 그래프 렌더링.

### 3. 범용 JS/TS 그래프 렌더링 라이브러리 비교

| 라이브러리 | 렌더링 백엔드 | 실용 최대 노드 | TS 지원 | 라이선스 | 유지보수(2026) | API 스타일 |
|---|---|---|---|---|---|---|
| **d3-force / d3.js** | SVG 또는 Canvas(직접) | 수백~수천(SVG), 수천(Canvas) | 좋음(@types) | ISC | 활발 | 저수준, 직접 조립 |
| **Sigma.js (+graphology)** | **WebGL** | 수만 엣지 용이, 5k+ 아이콘 노드는 부담 | 우수(TS 작성) | MIT | 활발, 별 ~12.1k, v4 알파 | 렌더러 전용, graphology와 분리 |
| **Cytoscape.js** | Canvas 2D(WebGL 렌더러 프리뷰 진행 중) | ~8k–10k 요소에서 한계 | 좋음 | MIT | 활발, 별 ~10k | 배터리 포함, 분석/알고리즘 강력 |
| **vis-network** | Canvas 2D | 수천 | 보통 | Apache-2.0 OR MIT | 활발, v10.1.0 (2026-05), 별 ~3.6k | 쉬운 대화형 다이어그램 |
| **force-graph (2D)** | HTML5 Canvas + d3-force | 수천~1만 | 좋음 | MIT | 활발, 별 ~1.8k | 간결한 체이닝 API |
| **3d-force-graph** | ThreeJS/WebGL + d3-force-3d/ngraph | 수천~수만 | 좋음 | MIT | 활발, 별 ~6.3k | 3D, 체이닝 API |
| **react-force-graph** | 2D Canvas/3D WebGL 래퍼 | 상동 | 좋음 | MIT | 활발, 별 ~3.1k | React 바인딩 |
| **cosmos.gl (@cosmos.gl/graph)** | **WebGL2(luma.gl), GPU 시뮬레이션** | **수십만~100만+** | 우수 | MIT | 활발, OpenJS 인큐베이팅, 별 ~1.2k | GPU force + 렌더 통합 |
| **G6 (AntV)** | Canvas 기본, SVG/WebGL 선택, WASM/GPU 레이아웃 | 수만(WebGL/GPU) | 우수 | MIT | 활발, 5.0.49 (2026-06), 별 ~12k | 배터리 포함, 선언형 |
| **VivaGraphJS / ngraph** | SVG 또는 WebGL | 수천~수만(WebGL) | 보통 | BSD-3-Clause | **저활동/사실상 정체**, 별 ~3.7k | 모듈러, ngraph 계열 |
| **ngraph.forcelayout** | 렌더러 없음(레이아웃 전용) | 대규모(offline/native 옵션) | 보통 | MIT | 저빈도 유지 | 레이아웃만, 임의 차원 |
| **pixi-graph** | **PixiJS(WebGL)** + Graphology | 수만 | 좋음 | MIT | **아카이브됨(2023-06-02)**, 별 ~160 | Pixi 렌더러 |
| **reagraph** | WebGL(React Three Fiber/Three.js) | 수천~수만 | 우수 | Apache-2.0 | 활발 | React 컴포넌트 |
| **React Flow (xyflow)** | **SVG/DOM** | 수백~수천(노드 UI용) | 우수 | MIT | 매우 활발, 별 ~38k+ | 노드 에디터, **force 레이아웃 기본 없음** |
| **GraphGPU** (drkameleon) | **WebGPU** 네이티브 | 대규모(GPU compute) | TS | MIT | 신규/소형, v0.3.2 (2026-03), 별 ~28 | WebGPU 렌더+시뮬 |
| **GraphWaGu** (harp-lab) | **WebGPU** compute | 10만 노드/200만 엣지 렌더 | TS | 라이선스 불명확 | 연구용/정체, 별 ~41 | 학술 프로토타입 |

**적합성 주의**:
- **React Flow / Reaflow**: 워크플로우/다이어그램 에디터용. SVG/DOM 기반이라 노드 수백~수천 규모의 정형 다이어그램에는 최적이나, force-directed 지식 그래프나 대규모에는 부적합(기본 물리 레이아웃 없음, d3-zoom으로 pan/zoom만).
- **ReGraph(주의)**: Cambridge Intelligence의 **상용(유료)** WebGL 제품으로 오픈소스가 아니다. 오픈소스 유사품인 **reagraph**(reaviz, Apache-2.0)와 이름이 비슷해 혼동하기 쉬우니 구분할 것.
- **Cytoscape.js**: 그래프 이론/분석(중심성, 경로 탐색)이 제품의 일부일 때 최적. Canvas 단일 스레드라 대규모 애니메이션엔 한계(공식 문서상 요소 다수 시 프레임레이트 저하). 2025년부터 WebGL 렌더러 프리뷰 진행 중.

### 4. 레이아웃/Force 시뮬레이션 라이브러리(렌더링과 분리)

- **d3-force**: 사실상 표준. Barnes-Hut 근사(quadtree)로 many-body force 계산. SVG/Canvas/WebGL 어디에도 좌표만 공급 가능. 3D는 d3-force-3d.
- **ngraph.forcelayout**: 임의 차원(2D/3D/4D…). 브라우저에서 무거우면 `ngraph.offline.layout`(사전 계산) 또는 anvaka README가 명시한 대로 *"ngraph.native which is fully implemented in C++ and is 9x faster than javascript version."* 사용.
- **graphology-layout-forceatlas2**: Gephi ForceAtlas2 알고리즘의 JS 구현. `graphology-layout-forceatlas2/worker`의 `FA2Layout` supervisor로 **Web Worker**에서 실행, transferable ArrayBuffer로 메인 스레드와 공유(`postMessage(..., [NODES.buffer])`). graphology-layout-force는 드래그 등 인터랙션에 더 유기적인 단순 force.
- **WebWorker + WebGL 렌더러 결합 패턴**: 시뮬레이션(CPU)을 worker에서 돌려 UI 스레드를 막지 않고, 위치 배열을 WebGL 렌더러(PixiJS/Sigma)로 전달. Jan Zak(Neo4j Developer Blog)은 *"D3 기반 시각화에서 SVG 렌더링을 PIXI.js로 교체하고 레이아웃을 별도 WebWorker 스레드로 옮기라"*고 권고하며, pixi-graph와 Advanced Graph View 플러그인이 이 방식을 쓴다.
- **GPU 시뮬레이션**:
  - **cosmos.gl**: 창시자 Nikita Rokotyan, 공동 유지 Olya Stukova. many-body force를 *"fragment and vertex shaders"*에서 계산(랜덤 메모리 접근 회피). Apache Arrow로 데이터 전송, v3에서 luma.gl(WebGL2)로 이식. OpenJS Foundation 발표에 따르면 *"over one million nodes and links"* 시각화 가능.
  - **WebGPU compute**: GraphWaGu(Fruchterman-Reingold + Barnes-Hut를 compute shader로, 10만 노드/200만 엣지 렌더), GraphGPU(5-pass GPU compute 파이프라인, CPU Barnes-Hut 대안 병행). ParaGraphL은 WebGL GPGPU로 Sigma 레이아웃 플러그인을 구현한 참고 사례.

### 5. 실전 가이드 (목적별 조합)

**(a) Obsidian 룩앤필을 충실히 재현**
- 스택: **PixiJS v8(WebGL) + d3-force + tween.js** — Quartz의 검증된 조합이자 Obsidian 코어와 동일 계열. Quartz의 `graph.inline.ts`를 참고 구현으로 삼는 것이 가장 빠르다.
- 대안: Sigma.js(+graphology, forceAtlas2 worker). pixi-graph는 아카이브되었으니 학습 참고용으로만.

**(b) 매우 큰 그래프(1만~10만+ 노드), GPU 가속 필요**
- 1순위: **cosmos.gl** — 브라우저에서 수십만~100만 노드 실시간 force. MIT, OpenJS 재단, 활발.
- 2순위: **Sigma.js + graphology**(수만 엣지) 또는 **G6**(WASM/GPU 레이아웃).
- 실험적: WebGPU 기반 **GraphWaGu/GraphGPU** — 최신이나 소규모/연구용.

**(c) 그래픽스/렌더링 실력을 보여주는 from-scratch 포트폴리오** ⭐ (사용자에게 가장 권장)
- 사용자의 OpenGL/C++/게임 배경을 살려 **직접 렌더러 + GPU 시뮬레이션**을 작성:
  1. **렌더러**: raw WebGL2 또는 WebGPU로 인스턴싱 기반 노드(SDF 원)·엣지(quad) 렌더링. PixiJS를 쓰더라도 커스텀 셰이더/필터로 글로우·블룸 등 Obsidian풍 효과 추가.
  2. **GPU force 시뮬레이션**: WebGL2 **transform feedback** 또는 텍스처 핑퐁(위치를 float 텍스처에 저장, 프래그먼트 셰이더에서 업데이트 — cosmos.gl 방식)으로 many-body/spring/gravity 계산. 고급: WebGPU **compute shader**로 Barnes-Hut quadtree(GraphWaGu 방식)를 구현.
  3. 비교 벤치마크(CPU d3-force worker vs GPU)를 곁들이면 렌더링 엔지니어 포지션에서 강한 인상.
- 학습 참고 소스: cosmos.gl(WebGL GPGPU), GraphWaGu 논문/코드(WebGPU compute, harp-lab), drkameleon/GraphGPU, anvaka/ngraph.pixi 예제, ParaGraphL(WebGL GPGPU 레이아웃).

## Recommendations
1. **지금 당장 동작하는 Obsidian풍 그래프가 필요하면**: Quartz의 graph 컴포넌트(PixiJS+d3-force, MIT)를 복제·개조하라. 가장 검증되고 룩앤필이 일치한다.
2. **포트폴리오 목적이라면(권장 경로)**: 2단계로 접근하라. (1단계) PixiJS + d3-force로 기능 완성형 클론을 만들어 UX/인터랙션(zoom/pan/drag/hover/local graph)을 확보. (2단계) 렌더러를 raw WebGL2/WebGPU로 교체하고 force 시뮬레이션을 GPU(transform feedback → compute shader)로 이식. 이 "CPU→GPU 마이그레이션 + 벤치마크" 서사가 렌더링 엔지니어 면접에서 강력하다.
3. **대규모 데이터가 핵심 요구면**: cosmos.gl을 기준선으로 삼고, 필요 시 WebGPU로 자체 구현하라.
4. **의사결정 임계값**: 노드 <2k이면 d3+SVG/Canvas로 충분; 2k~2만이면 WebGL(Sigma/PixiJS); 2만~10만+이면 GPU 시뮬레이션(cosmos.gl/WebGPU) 필수. React 앱에 임베드면 reagraph 또는 react-force-graph, 순수 다이어그램 에디터면 React Flow.
5. **피해야 할 것**: pixi-graph(아카이브 2023-06), VivaGraphJS(정체)를 프로덕션 신규 채택하지 말 것 — 학습 참고로만. ReGraph(상용)와 reagraph(오픈소스)를 혼동하지 말 것.

## Caveats
- Obsidian 코어는 클로즈드 소스다. "PixiJS + 커스텀 force"는 개발자 공식 증언(과거 d3→PixiJS 전환은 확정)·리버스 엔지니어링에 기반하며, 현재의 정확한 시뮬레이션 알고리즘은 비공개다.
- 별 수·릴리스 날짜는 2026년 8월 기준 근사치이며 변동한다. GraphWaGu의 라이선스는 명시적으로 확인되지 않았으니(같은 이름의 다른 학술 repo와 혼동 주의) 사용 전 저장소를 직접 확인하라. reagraph·ngraph.forcelayout의 정확한 별 수도 재확인 권장.
- "실용 최대 노드 수"는 엣지 밀도, 라벨, 스타일, 하드웨어에 크게 좌우된다. 범용 벤치마크 인용은 위험하니 반드시 실제 데이터로 직접 벤치마크하라.
- cosmos.gl 등 GPU 라이브러리는 특정 WebGL 확장에 의존한다. 공식 README는 *"iOS 15.4부터 many-body force에 쓰이는 EXT_float_blend 확장 지원이 중단"*되었고 *"OES_texture_float 확장을 지원하지 않는 Android 기기에서는 동작하지 않는다"*고 명시한다(이후 iOS는 재지원). 크로스플랫폼 배포 시 폴백을 고려하라.
- WebGPU는 2026년 기준 주요 브라우저에서 지원되나, 관련 그래프 프로젝트(GraphWaGu, GraphGPU)는 아직 연구·초기 단계로 프로덕션 성숙도는 낮다.