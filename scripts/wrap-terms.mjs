// <include file="docs/codegraph/comments.xml" path="//term[@id='scripts/wrap-terms.mjs']"/>
// 다 만들어진 HTML 글자에서 용어집 용어를 찾아 뜻 카드가 뜨는 참조로 감싸는 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// scripts/wrap-terms.mjs — 빌드 후 통과. 본문 글자에 나오는 용어집 용어를 전부 term-ref 로 감싼다.
//
// 왜 여기인가. 본문 산문의 대부분이 컴포넌트의 props(measured · cells · title)로 들어가 React 트리의
// 자식 순회로는 닿지 않고, 전역 변수와 컨텍스트는 이 저장소가 쓰지 않는다(defineTerms 의 원칙).
// 그래서 renderToStaticMarkup 이 낸 HTML 문자열에 한 번 더 통과시킨다. 감싸는 마크업은 손으로 흉내 내지
// 않고 TermRef 컴포넌트를 실제로 렌더한 문자열(refs)을 받는다 — 마크업의 출처는 하나다.
//
// 글자만 건드린다. 태그와 속성은 그대로 지나가고, 아래 요소 안은 통째로 건너뛴다.
//
// 전제 — 입력은 renderToStaticMarkup 의 출력이다. React 는 글자와 속성값 양쪽에서 < > & " ' 를
// 실체 참조로 바꾸므로, 태그를 `<...>` 로 자르는 이 훑기가 속성값 안의 꺾쇠에 걸려 넘어지지 않는다.
// 같은 이유로 용어 id 에 그 다섯 글자가 들어 있으면 글자 쪽과 모양이 달라 맞지 않는다(현재 그런 id 는 없다).

/** 이 요소 안의 글자는 건드리지 않는다. */
const SKIP_TAGS = new Set(["script", "style", "svg", "code", "pre", "summary", "h1", "h2", "h3", "th", "title", "textarea"]);
/** class 에 이 낱말이 있으면 그 요소 안을 건드리지 않는다 — 이미 감싼 곳 · 카드 · 코드 글꼴 · 용어집 · 관계도 · 다이어그램. */
const SKIP_CLASSES = ["term-ref", "term-card", "mono", "term-groups", "term-graph", "svg-wrap"];
const VOID_TAGS = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
const ASCII = /[A-Za-z0-9_]/;

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='termPattern']"/>
// 용어 이름 목록으로 본문에서 그 이름을 찾아낼 정규식을 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: wrapTerms
/**
 * 용어 id 목록으로 매칭 정규식을 만든다. 긴 것부터 — "git blob SHA" 가 "git" 에 먼저 잘리지 않게.
 *
 * 뒤쪽 경계는 **항상** 요구한다. "M10" 의 앞 두 글자가 M1 이 아닌 것과 같은 이유로 "edges[]x" 도
 * edges[] 가 아니다. 한국어 조사는 ASCII 가 아니므로 이 경계에 걸리지 않는다 — "모듈을" 은 그대로 잡힌다.
 * 앞쪽 경계는 id 가 ASCII 로 시작할 때만 요구한다. 한글은 낱말 경계가 없어 요구하면 대부분을 놓친다.
 */
export function termPattern(ids) {
  const sorted = [...new Set(ids)].filter(Boolean).sort((a, b) => b.length - a.length);
  if (sorted.length === 0) return null;
  const alts = sorted.map((id) => {
    const lead = ASCII.test(id[0]) ? "(?<![A-Za-z0-9_])" : "";
    return lead + escapeRe(id) + "(?![A-Za-z0-9_])";
  });
  return new RegExp(alts.join("|"), "g");
}

function skipsByClass(tag) {
  const m = tag.match(/\sclass=["']([^"']*)["']/);
  if (!m) return false;
  const cls = m[1].split(/\s+/);
  return SKIP_CLASSES.some((c) => cls.includes(c));
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='wrapTerms']"/>
// HTML 글자에 나오는 용어를 전부 용어 참조 마크업으로 바꾼다.
// 쓰는 것: termPattern · 쓰이는 곳: build.mjs
/**
 * html 의 글자 부분에서 refs 의 키(용어 id)가 나오는 곳을 전부 refs 의 값(TermRef 마크업)으로 바꾼다.
 * refs: Map<id, markup>. markup 은 그 id 를 글자로 담은 term-ref 여야 한다 — build.mjs 가 TermRef 를 렌더해 만든다.
 * 한 번 지나가며 바꾸므로 감싼 결과를 다시 훑지 않는다(멱등).
 */
export function wrapTerms(html, refs) {
  const re = termPattern([...refs.keys()]);
  if (!re) return html;
  const tagRe = /<\/?([A-Za-z][A-Za-z0-9-]*)\b[^>]*>|<!--[\s\S]*?-->/g;
  const stack = [];                                   // 열린 요소 { name, skip }
  const skipping = () => stack.some((s) => s.skip);
  const text = (s) => (skipping() || !s ? s : s.replace(re, (hit) => refs.get(hit) ?? hit));
  let out = "", last = 0, m;
  while ((m = tagRe.exec(html))) {
    out += text(html.slice(last, m.index));
    const tag = m[0];
    last = m.index + tag.length;
    out += tag;
    if (tag.startsWith("<!--")) continue;
    const name = m[1].toLowerCase();
    if (tag.startsWith("</")) {
      const i = stack.map((s) => s.name).lastIndexOf(name);
      if (i >= 0) stack.length = i;
    } else if (!VOID_TAGS.has(name) && !tag.endsWith("/>")) {
      stack.push({ name, skip: SKIP_TAGS.has(name) || skipsByClass(tag) });
    }
  }
  out += text(html.slice(last));
  return out;
}
