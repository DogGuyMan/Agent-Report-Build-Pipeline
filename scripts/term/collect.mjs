// <include file="docs/codegraph/comments.xml" path="//term[@id='collect.mjs']"/>
// 이 Plan 을 읽는 데 필요한 용어를 모으는 스크립트. Mode 1.5 의 1단계다.
// scripts/term/collect.mjs — Mode 1.5 1단계. 이 Plan 을 이해하는 데 필요한 용어를 모은다.
//
// 두 갈래에서 모은다.
//   (가) 코드베이스 용어 DB 와 Plan 본문의 교차 — 정답이 이미 있다
//   (나) Plan 이 새로 만든 개념 — 정답이 없다. **Plan 저자가 직접 써야 한다**
//
// 출제 범위는 코드베이스 전체가 아니다. 이 Plan 이 실제로 요구하는 용어만 낸다.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

// <include file="docs/codegraph/comments.xml" path="//term[@id='escapeRe']"/>
// 이름에 든 정규식 특수문자를 막는다. calls[] 같은 이름이 그대로 들어오기 때문이다.
/** 정규식 특수문자를 막는다. calls[] 같은 이름이 그대로 들어온다. */
function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='pickTerms']"/>
// 코드베이스 용어 중 Plan 본문에 실제로 나오는 것만 고른다.
/** 코드베이스 용어 DB 중 Plan 본문에 실제로 등장하는 것만 고른다. */
export function pickTerms(db, planText) {
  const out = {};
  for (const [name, rec] of Object.entries(db)) {
    // 이름이 기호로 끝나면(calls[]) 낱말 경계를 뒤에 붙일 수 없다.
    const tail = /[A-Za-z0-9_]$/.test(name) ? "\\b" : "";
    const re = new RegExp("\\b" + escapeRe(name) + tail);
    if (re.test(planText)) out[name] = rec;
  }
  return out;
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='findNewConcepts']"/>
// Plan 이 새로 만든 개념을 찾는다. 정답이 없으므로 저자가 써야 한다.
/**
 * Plan 이 새로 만든 개념을 찾는다. `scripts/check.mjs` 의 undefinedTerms 와 같은 세 꼴을 쓴다.
 * 두 곳이 어긋나면 안 된다 — 한쪽을 고치면 다른 쪽도 같이 고친다.
 * 자연어 용어(WarmUp·PageRank)는 기계가 가릴 수 없어 저자가 직접 넣어야 한다.
 */
export function findNewConcepts(db, planText) {
  const known = new Set(Object.keys(db));
  const found = new Set();
  const patterns = [
    /\b(?!D\d)[A-Z]{1,3}-?\d{1,3}\b/g,
    /\b[a-z][a-z0-9_-]*\.json\b/g,
    /\b[a-z][A-Za-z0-9_]*\[\]/g,
  ];
  for (const re of patterns) {
    for (const m of planText.matchAll(re)) {
      if (!known.has(m[0])) found.add(m[0]);
    }
  }
  return [...found].sort();
}

// 직접 실행됐을 때만 파일을 읽고 쓴다. import 시에는 순수 함수만 노출한다.
if (process.argv[1] && process.argv[1].endsWith("collect.mjs")) {
  const [planPath, dbPath] = process.argv.slice(2);
  if (!planPath) {
    console.error("사용법 — report-term collect <plan.md> [terms-db.json]");
    process.exit(1);
  }
  const planText = readFileSync(planPath, "utf8");
  const db = dbPath && existsSync(dbPath) ? JSON.parse(readFileSync(dbPath, "utf8")) : {};

  const known = pickTerms(db, planText);
  const fresh = findNewConcepts(db, planText);

  const out = { plan: planPath, known, newConcepts: fresh };
  const path = join(process.cwd(), "term-candidates.json");
  writeFileSync(path, JSON.stringify(out, null, 2) + "\n");

  console.log(`${path}`);
  console.log(`  코드베이스 용어 ${Object.keys(known).length}개`);
  console.log(`  Plan 신규 개념 ${fresh.length}개 — 정답은 Plan 저자가 써야 한다`);
  if (fresh.length) console.log(`    ${fresh.join(", ")}`);
}
