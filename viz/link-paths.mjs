// <include file="machine/comments.xml" path="//term[@id='viz/link-paths.mjs']"/>
// 본문에 글자로 적힌 파일 경로를 그 파일을 여는 링크로 바꾸는 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/link-paths.mjs — 빌드 후 통과 둘째. 본문에 글자로 적힌 경로 꼴 낱말을 실제 로컬 파일 · 폴더의 file:// 링크로 바꾼다.
//
// 자동 참조(wrap-terms.mjs)와 같은 자리에서 돈다. 용어(term-ref)는 뜻 카드, 코드 글꼴(.mono)은 파일 링크 — 역할이 갈리므로
// term-ref 안은 건너뛰고 .mono 안은 포함한다. 없는 파일은 링크하지 않는다 — 계획에만 있는 파일이 링크되면 독자가 속는다.
//
// 파일 시스템을 읽는 함수(buildIndex · makeResolver)는 내보내되 모듈 최상위에서 실행하지 않는다 — import 만으로는
// 아무 일도 일어나지 않아야 한다(scripts/*.mjs 규약).
import { statSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import { homedir } from "node:os";
import { execFileSync } from "node:child_process";

/** 이 요소 안의 글자는 건드리지 않는다. a 가 들어 있는 이유는 링크 안에 링크를 넣지 않기 위함이다. */
const SKIP_TAGS = new Set(["script", "style", "svg", "summary", "h1", "h2", "h3", "th", "title", "a", "textarea"]);
/** class 에 이 낱말이 있으면 그 요소 안을 건드리지 않는다 — 용어 참조 · 카드 · 용어집 · 관계도 · 다이어그램. */
const SKIP_CLASSES = ["term-ref", "term-card", "term-groups", "term-graph", "svg-wrap"];
const VOID_TAGS = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
const EXT = "md|mjs|py|ts|tsx|json|css|html|dot|svg|yaml|yml|toml|cs|cpp|h";

// <include file="machine/comments.xml" path="//term[@id='pathPattern']"/>
// 본문에서 경로처럼 생긴 낱말을 찾아낼 정규식을 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: linkPaths
/**
 * 경로 꼴 — `a/b.md:3` `c.json` `facts/*.md` `x.py`. 앞뒤가 낱말 · 경로 글자가 아니어야 한다.
 * URL(`http://x.com/a.md`)은 앞 글자가 `/` 나 `.` 라 lookbehind 에 막힌다.
 * 그룹 1 은 줄 번호를 뗀 경로, 그룹 2 는 줄 번호. m[0] 은 줄 번호까지 포함한 글자 전체다.
 */
export function pathPattern() {
  return new RegExp(
    String.raw`(?<![\w/.:-])((?:[\w.@-]+/)*(?:[\w.@-]+\.(?:${EXT})|\*\.(?:${EXT})))(?::(\d+(?:-\d+)?))?(?![\w/])`,
    "g",
  );
}

// <include file="machine/comments.xml" path="//term[@id='buildIndex']"/>
// 저장소가 추적하는 파일들의 이름 색인을 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/** 저장소 추적 파일의 이름 색인. { basename -> [상대경로…] }. git 밖이면 빈 Map. */
export function buildIndex(repoRoot) {
  const index = new Map();
  try {
    const out = execFileSync("git", ["-C", repoRoot, "ls-files"], { stdio: ["ignore", "pipe", "ignore"] }).toString();
    for (const rel of out.split("\n")) {
      if (!rel) continue;
      const b = basename(rel);
      if (!index.has(b)) index.set(b, []);
      index.get(b).push(rel);
    }
  } catch {
    /* git 밖이면 이름 검색만 못 한다 */
  }
  return index;
}

const isFile = (p) => {
  try {
    return statSync(p).isFile();
  } catch {
    return false;
  }
};
const isDir = (p) => {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
};

// <include file="machine/comments.xml" path="//term[@id='expandRoot']"/>
// 경로 앞머리의 물결표와 달러 변수를 실제 폴더 이름으로 편다.
// 쓰는 것: 없음 · 쓰이는 곳: makeResolver
/**
 * 경로 앞머리의 `~` 와 `$VAR` / `${VAR}` 를 편다.
 *
 * **왜 필요한가.** 공개 저장소에 맥 유저명을 남기지 않으려고 `data.ts` 의 `linkRoots` 를
 * `$CSHARP_REPO/out/codegraph-raw` 같은 꼴로 적는다. 값이 없으면 그 자리는 빈 문자열이
 * 되고 `isDir` 이 걸러 내므로, 그 폴더가 없는 독자에게는 조용히 링크가 안 걸릴 뿐이다.
 */
export function expandRoot(base) {
  let out = String(base);
  if (out === "~" || out.startsWith("~/")) out = join(homedir(), out.slice(1));
  return out.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g,
    (_, a, b) => process.env[a ?? b] ?? "");
}

// <include file="machine/comments.xml" path="//term[@id='makeResolver']"/>
// 경로 낱말 하나를 받아 실제 파일 주소를 돌려주는 함수를 만든다.
// 쓰는 것: expandRoot · 쓰이는 곳: 없음
/**
 * 해석기. token(줄 번호 뗀 경로) -> { href, kind: "file"|"dir" } | null.
 * 순서: bases 를 차례로(보고서 폴더 → specs/ → 저장소 루트 → out/codegraph-raw → linkRoots) → 이름만이면 index 에서 유일할 때.
 */
export function makeResolver({ bases, repoRoot, index }) {
  const roots = [...new Set(bases.filter(Boolean).map(expandRoot))].filter((b) => isDir(b));
  return function resolve(token) {
    if (token.includes("*")) {
      const dir = dirname(token);
      for (const b of roots) {
        const p = join(b, dir);
        if (isDir(p)) return { href: pathToFileURL(p).href, kind: "dir" };
      }
      return null;
    }
    for (const b of roots) {
      const p = join(b, token);
      if (isFile(p)) return { href: pathToFileURL(p).href, kind: "file" };
    }
    if (!token.includes("/") && index && repoRoot) {
      const hits = index.get(token) ?? [];
      if (hits.length === 1 && isFile(join(repoRoot, hits[0]))) {
        return { href: pathToFileURL(join(repoRoot, hits[0])).href, kind: "file" };
      }
    }
    return null;
  };
}

function skipsByClass(tag) {
  const m = tag.match(/\sclass=["']([^"']*)["']/);
  if (!m) return false;
  const cls = m[1].split(/\s+/);
  return SKIP_CLASSES.some((c) => cls.includes(c));
}

// <include file="machine/comments.xml" path="//term[@id='linkPaths']"/>
// HTML 글자의 경로 낱말 중 실제로 있는 파일만 골라 링크로 감싼다.
// 쓰는 것: pathPattern, path-link · 쓰이는 곳: build.mjs
/**
 * html 의 글자 부분에서 경로 꼴을 찾아 resolve 가 답하는 것만 <a class="path-link" href="file://…"> 로 감싼다.
 * 글자(줄 번호 포함)는 그대로 남는다. 감싼 결과는 a 안이라 다시 훑지 않는다(멱등).
 * onMiss 는 못 찾은 경로를 알리는 선택 콜백이다.
 */
export function linkPaths(html, resolve, onMiss) {
  const re = pathPattern();
  const tagRe = /<\/?([A-Za-z][A-Za-z0-9-]*)\b[^>]*>|<!--[\s\S]*?-->/g;
  const stack = []; // 열린 요소 { name, skip }
  const skipping = () => stack.some((s) => s.skip);
  const text = (s) =>
    skipping() || !s
      ? s
      : s.replace(re, (whole, path) => {
          const r = resolve(path);
          if (!r) {
            onMiss?.(path);
            return whole;
          }
          // 새 탭 — 보고서 탭을 덮지 않는다(사용자 확정 2026-08-29). rel=noopener 는 새 탭이 이 창을 잡지 못하게 한다.
    return `<a class="path-link" target="_blank" rel="noopener" href="${r.href}">${whole}</a>`;
        });
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
  return out + text(html.slice(last));
}
