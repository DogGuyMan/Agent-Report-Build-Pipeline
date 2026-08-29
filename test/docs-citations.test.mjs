// test/docs-citations.test.mjs — 컨텍스트 문서의 `파일:줄` 인용이 실재하는지 본다 (L1).
//
// **왜 이 시험이 있는가.** 이 저장소는 인용 검증기(`codegraph/verify_citations.py`)를
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

// `codegraph/verify_citations.py` 의 CITE 와 같은 확장자 목록이다.
// 확장자를 못박는 이유는 "3:4" 같은 글자를 인용으로 오인하지 않기 위해서다.
const CITE =
  /([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot)):(\d+)(?:-(\d+))?/g;

/** 검사 대상 — 저장소의 컨텍스트 문서. 없는 것은 조용히 건너뛴다. */
export function contextDocs(root = ROOT, exists = existsSync) {
  return ["CLAUDE.md", "README.md", "ARCHITECTURE.md",
          "codegraph/CLAUDE.md", "scripts/CLAUDE.md", "src/CLAUDE.md"]
    .filter((rel) => exists(join(root, rel)));
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
  assert.equal(citationsIn("보라 `src/a.h:67` 을").length, 1);
});

test("확장자가 있는 것만 인용으로 센다 — 시각 3:4 를 물지 않는다", () => {
  assert.equal(citationsIn("3:4 로 나뉜다").length, 0);
  assert.equal(citationsIn("`scripts/build.mjs:152`").length, 1);
});

test("컨텍스트 문서를 실제로 하나 이상 찾는다", () => {
  const docs = contextDocs();
  assert.ok(docs.includes("CLAUDE.md"), "CLAUDE.md 를 못 찾았다");
});

for (const rel of contextDocs()) {
  test(`${rel} 의 인용이 전부 실재한다 (L1)`, () => {
    const broken = brokenCitations(readFileSync(join(ROOT, rel), "utf8"));
    const 목록 = broken.map((b) => `  ${rel} — ${b.path}:${b.line} 파일 없음`).join("\n");
    assert.equal(broken.length, 0,
      `죽은 인용 ${broken.length}건. 낡은 인용은 없는 인용보다 나쁘다.\n${목록}`);
  });
}
