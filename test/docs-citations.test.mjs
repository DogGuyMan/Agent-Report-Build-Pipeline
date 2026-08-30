// test/docs-citations.test.mjs — 컨텍스트 문서의 `파일:줄` 인용이 실재하는지 본다 (L1).
//
// **왜 이 시험이 있는가.** 이 저장소는 인용 검증기(`machine/verify_citations.py`)를
// 만들어 위키 산문에는 쓰면서 **자기 문서에는 한 번도 걸지 않았다.** 그 사이에
// `CLAUDE.md` 안에 죽은 인용이 3건 쌓였다(🔵 2026-08-30 실측). 낡은 인용은 없는 인용보다
// 나쁘다 — 읽는 사람이 그 자리를 실제로 찾아가기 때문이다.
//
// **왜 파이썬 검증기를 부르지 않는가.** 그것은 `--codegraph` 를 필수로 요구하는데
// `out/codegraph-raw/codegraph.json` 은 재생성 대상이라 새로 받은 저장소에는 없다.
// 게이트가 환경에 따라 못 돌면 게이트가 아니다. 그래서 **L1(파일이 있나)만** 여기서 본다.
// L2·L3(줄이 있나 · 그 자리에 그 이름이 있나)는 위키 산문에서 그 검증기가 계속 맡는다.
//
// **환경변수로 시작하는 경로는 건너뛴다.** 이 저장소의 규약이 바깥 저장소를
// `$GRAPHICS_REPO/...` 처럼 적으라고 정해 두었다(CLAUDE.md 의 "경로 변수" 절).
// 그 경로는 이 기계에 없는 것이 정상이다. 파이썬 검증기는 `$` 를 모르고 실패로 세는데,
// 그것이 규약과 도구가 어긋나 있던 자리다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

// `machine/verify_citations.py` 의 CITE 와 같은 확장자 목록이다.
// 확장자를 못박는 이유는 "3:4" 같은 글자를 인용으로 오인하지 않기 위해서다.
const CITE =
  /([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot)):(\d+)(?:-(\d+))?/g;

/** 검사 대상 — 저장소의 컨텍스트 문서. 없는 것은 조용히 건너뛴다. */
export function contextDocs(root = ROOT, exists = existsSync) {
  return ["CLAUDE.md", "README.md", "ARCHITECTURE.md",
          "machine/CLAUDE.md", "viz/CLAUDE.md", "viz/src/CLAUDE.md",
          "runner/CLAUDE.md", "tools/CLAUDE.md",
          "docs/CLAUDE.md"]
    .filter((rel) => exists(join(root, rel)));
}

// ── 줄 번호 없는 맨 경로 (2026-08-30 신설) ────────────────────────────────
//
// **왜 따로 있는가.** 위 CITE 는 `파일:줄` 만 잡는다. 그런데 컨텍스트 문서가 가리키는
// 것의 대부분은 줄 번호 없는 맨 경로(`viz/build.mjs`)다. 외부 채점기가 이 저장소에서
// "hallucinated path 9건" 을 보고했고 그 중 8건은 오탐이었지만 **1건은 진짜였다** —
// 다른 세션이 `machine/terms-reading.json` 을 옮기면서 문서를 안 고쳤다.
// 사람이 눈으로 세는 한 이 종류는 계속 새어 나간다.
const PATH_REF = new RegExp(
  // 앞 글자가 경로/식별자 조각이면 중간을 문 것이라 버린다. `$` 도 여기서 걸러진다.
  "(?<![A-Za-z0-9_$/@~.-])" +
  // **`../` 로 시작하는 것도 잡는다.** 모듈 문서는 형제 모듈을 그렇게 부른다.
  // 이 조각이 없던 동안 `machine/CLAUDE.md` 의 죽은 `../src/CLAUDE.md` 가
  // 177개 통과 속에 숨어 있었다 — 게이트를 만들면서 낸 사각이다(🔵 2026-08-30).
  "((?:\\.\\./)*" +
  // 최소 한 칸의 디렉토리 — 맨 파일 이름(`data.ts`)은 대상 저장소의 것이라 검사하지 않는다.
  "(?:\\.?[A-Za-z0-9_@+~-]+/)+[A-Za-z0-9_@.+~-]+" +
  "\\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot|html|css|xml))" +
  // **확장자 뒤에 글자가 이어지면 안 된다.** 이 잠금이 없으면 교대(`|`)가 먼저 맞는 것을
  // 집어 `theme.css` 를 `theme.c` 로, `terms-reading.json` 을 `…​.js` 로 자른다.
  // 외부 채점기가 정확히 이 버그로 오탐 2건을 냈고, 여기서도 처음에 같은 실수를 했다.
  "(?![A-Za-z0-9])",
  "g",
);

/**
 * 검사에서 빼는 경로.
 *
 * **`out/` 은 재생성 대상이다.** 루트 CLAUDE.md 가 "git 제외 — 재생성" 이라 못박았고,
 * 빌드 전 저장소에는 없는 것이 정상이다. 있는지 따지면 갓 받은 저장소에서 게이트가 항상 깨진다.
 * **`<…>` 가 든 것은 자리 표시자다** (`specs/<slug>/data.ts`).
 */
export function isExempt(p) {
  return p.startsWith("out/") || p.includes("<") || p.includes(">");
}

/**
 * **첫 줄이 `$VAR/` 인 코드 울타리는 바깥 저장소의 트리 그림이라 통째로 지운다.**
 *
 * Why — 트리 그림은 뿌리에만 변수를 적고 자식은 들여쓰기로 잇는다.
 * 그래서 자식 줄만 보면 `superpowers/specs/….html` 처럼 이 저장소 경로로 보인다.
 * 반대로 `cd $REPO_ROOT` 로 시작하는 검증 블록은 **이 저장소**를 말하므로 지우면 안 된다 —
 * 첫 줄이 `$` 로 시작하느냐가 그 둘을 가른다.
 */
export function stripExternalTrees(text) {
  return text.replace(/```[^\n]*\n([\s\S]*?)```/g, (블록, 속) => {
    const 첫줄 = 속.split("\n").find((l) => l.trim() !== "") ?? "";
    return /^\s*\$[A-Za-z_][A-Za-z0-9_]*\//.test(첫줄) ? "" : 블록;
  });
}

/** 한 문서의 맨 경로 참조. 파일 시스템을 보지 않는 순수 함수다. */
export function pathRefsIn(text) {
  const 본문 = stripExternalTrees(text);
  return [...new Set([...본문.matchAll(PATH_REF)].map((m) => m[1]))]
    .filter((p) => !isExempt(p));
}

/**
 * 그 경로가 실재하는가. 저장소 뿌리 기준과 **문서 자신의 폴더 기준** 둘 다 본다.
 *
 * **Why — 모듈 문서는 제 폴더를 기준으로 쓴다.** `viz/src/CLAUDE.md` 는 형제를
 * `runtime/term-graph.ts` 라 부르지 `viz/src/runtime/term-graph.ts` 라 부르지 않는다.
 * 뿌리 기준만 보면 그 자연스러운 표기가 전부 거짓 경보가 된다.
 */
export function brokenPathRefs(text, docRel = ".", root = ROOT, exists = existsSync) {
  const base = dirname(resolve(root, docRel));
  return pathRefsIn(text).filter(
    (p) => !exists(resolve(root, p)) && !exists(resolve(base, p)),
  );
}

/**
 * 한 문서에서 인용을 뽑는다. 파일 시스템을 보지 않는 순수 함수다.
 *
 * 바로 앞 글자가 `$` 면 환경변수 경로라 건너뛴다 — 정규식에 `$` 가 없어서
 * `$GRAPHICS_REPO/a.h:1` 이 `GRAPHICS_REPO/a.h:1` 로 잡히기 때문이다.
 */
export function citationsIn(text) {
  const out = [];
  for (const m of text.matchAll(CITE)) {
    if (m.index > 0 && text[m.index - 1] === "$") continue;
    out.push({ path: m[1], line: Number(m[2]), index: m.index });
  }
  return out;
}

/** 인용이 가리키는 파일이 저장소 안에 있는가. */
export function brokenCitations(text, root = ROOT, exists = existsSync) {
  return citationsIn(text).filter((c) => !exists(resolve(root, c.path)));
}

test("환경변수로 시작하는 인용은 검사하지 않는다 — 바깥 저장소 규약이다", () => {
  assert.equal(citationsIn("보라 `$GRAPHICS_REPO/src/a.h:67` 을").length, 0);
  assert.equal(citationsIn("보라 `viz/src/a.h:67` 을").length, 1);
});

test("확장자가 있는 것만 인용으로 센다 — 시각 3:4 를 물지 않는다", () => {
  assert.equal(citationsIn("3:4 로 나뉜다").length, 0);
  assert.equal(citationsIn("`viz/build.mjs:152`").length, 1);
});

test("컨텍스트 문서를 실제로 하나 이상 찾는다", () => {
  const docs = contextDocs();
  assert.ok(docs.includes("CLAUDE.md"), "CLAUDE.md 를 못 찾았다");
});

test("맨 경로도 환경변수와 자리 표시자를 건너뛴다", () => {
  assert.equal(pathRefsIn("`$GRAPHICS_REPO/doc/a.html` 를 보라").length, 0);
  assert.equal(pathRefsIn("`specs/<slug>/data.ts` 가 생긴다").length, 0);
  assert.equal(pathRefsIn("`out/report.html` 이 나온다").length, 0);
  assert.deepEqual(pathRefsIn("`viz/build.mjs` 가 짓는다"), ["viz/build.mjs"]);
});

test("맨 파일 이름은 검사하지 않는다 — 대상 저장소의 것이다", () => {
  assert.equal(pathRefsIn("저자는 `data.ts` 를 고친다").length, 0);
});

test("앞에 점이 붙은 폴더를 통째로 잡는다", () => {
  assert.deepEqual(pathRefsIn("`.claude/CLAUDE.md` 의 13개"), [".claude/CLAUDE.md"]);
});

test("형제 모듈을 부르는 ../ 경로도 잡는다 — 게이트의 옛 사각", () => {
  assert.deepEqual(pathRefsIn("컴포넌트는 `../viz/src/CLAUDE.md`"), ["../viz/src/CLAUDE.md"]);
  assert.deepEqual(pathRefsIn("나침반은 `../CLAUDE.md`"), []); // 디렉토리 조각이 없다
});

test("바깥 트리 그림은 통째로 건너뛰고, $REPO_ROOT 검증 블록은 검사한다", () => {
  const 바깥 = "```\n$GRAPHICS_REPO/doc/\n  superpowers/specs/a.html\n```";
  assert.equal(pathRefsIn(바깥).length, 0);
  const 안쪽 = "```bash\ncd $REPO_ROOT\n.venv/bin/python machine/facts.py\n```";
  assert.ok(pathRefsIn(안쪽).includes("machine/facts.py"));
});

test("긴 확장자를 짧은 것으로 자르지 않는다 — 교대 순서 함정", () => {
  assert.deepEqual(pathRefsIn("`viz/src/theme.css`"), ["viz/src/theme.css"]);
  assert.deepEqual(pathRefsIn("`a/terms.json`"), ["a/terms.json"]);
  assert.deepEqual(pathRefsIn("`a/b.html`"), ["a/b.html"]);
  assert.deepEqual(pathRefsIn("`viz/src/components/x.tsx`"), ["viz/src/components/x.tsx"]);
});

for (const rel of contextDocs()) {
  test(`${rel} 의 인용이 전부 실재한다 (L1)`, () => {
    const broken = brokenCitations(readFileSync(join(ROOT, rel), "utf8"));
    const 목록 = broken.map((b) => `  ${rel} — ${b.path}:${b.line} 파일 없음`).join("\n");
    assert.equal(broken.length, 0,
      `죽은 인용 ${broken.length}건. 낡은 인용은 없는 인용보다 나쁘다.\n${목록}`);
  });

  test(`${rel} 의 맨 경로가 전부 실재한다`, () => {
    const broken = brokenPathRefs(readFileSync(join(ROOT, rel), "utf8"), rel);
    const 목록 = broken.map((p) => `  ${rel} — ${p} 없음`).join("\n");
    assert.equal(broken.length, 0,
      `가리키는 곳이 없는 경로 ${broken.length}건. 옮겼으면 문서도 옮긴다.\n${목록}`);
  });
}
