// <include file="docs/codegraph/comments.xml" path="//term[@id='quiz.mjs']"/>
// 객관식 답안을 채점하는 스크립트. 사람에게 묻지 않는다.
// 쓰는 것: term-grades.json · 쓰이는 곳: 없음
// scripts/term/quiz.mjs — Mode 1.5 2·3단계. 객관식 채점.
//
// **이 파일은 사람에게 묻지 않는다.** 답안 파일을 받아 채점만 한다.
// 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다 — 도구는 판정하지 않는다는 규율의 연장이다.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** 한 용어당 문항 수. 2026-08-29 사용자 변경 — 5 에서 3 으로. 100문항 첫 시험에서 피로가 실측됐다. */
export const QUESTIONS_PER_TERM = 3;

// <include file="docs/codegraph/comments.xml" path="//term[@id='gradeOne']"/>
// 용어 하나의 답안을 채점해 확실 · 애매 · 모름을 매긴다.
// 쓰는 것: QUESTIONS_PER_TERM · 쓰이는 곳: gradeAll
/**
 * 한 용어의 답안을 채점한다. 두 갈래다 — 확실 / 모름.
 * 구간은 사용자가 확정한 값이다(2026-08-29, 3문항 규칙). 임의로 바꾸지 말 것.
 *   "모른다" 2회 이상        -> 모름 (찍어서 맞힌 것을 안다고 세지 않는다)
 *   맞힌 수 2~3 (67% 이상)   -> 확실
 *   맞힌 수 0~1              -> 모름
 * "애매" 는 이 규칙이 내지 않는다 — 5문항 시절의 산출물과 Term.mental 타입에만 남아 있다.
 */
export function gradeOne({ correct, dontKnow }) {
  const rate = Math.round((correct / QUESTIONS_PER_TERM) * 100);
  let mental;
  if (dontKnow >= 2) mental = "모름";
  else if (correct >= 2) mental = "확실";
  else mental = "모름";
  return { rate, mental };
}

// <include file="docs/codegraph/comments.xml" path="//term[@id='gradeAll']"/>
// 답안 전체를 채점한다. 입력이 같으면 출력도 같다.
// 쓰는 것: gradeOne · 쓰이는 곳: 없음
/** 답안 전체를 채점한다. 입력이 같으면 출력도 같다. */
export function gradeAll(answers) {
  const out = {};
  for (const [term, a] of Object.entries(answers)) {
    // means 는 다음 단계(emit)가 정답 문구로 쓰기 위해 그대로 넘긴다.
    out[term] = { ...gradeOne(a), means: a.means ?? "" };
  }
  return out;
}

if (process.argv[1] && process.argv[1].endsWith("quiz.mjs")) {
  // dispatch.mjs 는 명령어 이름(grade)을 소비하고 나머지 인자만 넘긴다 — collect.mjs 와 같은 꼴.
  // 직접 실행(node quiz.mjs grade answers.json)도 받도록 앞에 남은 "grade" 는 벗겨 낸다.
  const args = process.argv.slice(2);
  if (args[0] === "grade") args.shift();
  const [file] = args;
  if (file) {
    const answers = JSON.parse(readFileSync(file, "utf8"));
    const graded = gradeAll(answers);
    const path = join(process.cwd(), "term-grades.json");
    writeFileSync(path, JSON.stringify(graded, null, 2) + "\n");
    const tally = { 확실: 0, 애매: 0, 모름: 0 };
    for (const g of Object.values(graded)) tally[g.mental]++;
    console.log(`${path}`);
    console.log(`  확실 ${tally.확실} · 애매 ${tally.애매} · 모름 ${tally.모름}`);
  } else {
    console.error("사용법 — report-term grade <answers.json>");
    console.error("  문항 작성과 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다.");
    process.exit(1);
  }
}
