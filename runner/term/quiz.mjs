// <include file="machine/comments.xml" path="//term[@id='quiz.mjs']"/>
// 객관식 답안을 채점하는 스크립트. 사람에게 묻지 않는다.
// 쓰는 것: term-grades.json · 쓰이는 곳: 없음
// runner/term/quiz.mjs — Mode 1.5 2·3단계. 객관식 채점.
//
// **이 파일은 사람에게 묻지 않는다.** 채운 기입란과 문항지를 받아 대조하고 채점만 한다.
// 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다 — 도구는 판정하지 않는다는 규율의 연장이다.
//
// 파일 둘을 받는 이유 — 사람이 채우는 기입란(`answers.json`)에는 정답이 없고 문항지
// (`questions.json`)에만 있다. 정답을 기입란에 실었다면 인자가 하나로 줄었겠지만,
// 그러면 사람이 풀기 전에 정답을 본다.
//
//     report-term grade <answers.json> <questions.json>
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** 한 용어당 문항 수. 2026-08-29 사용자 변경 — 5 에서 3 으로. 100문항 첫 시험에서 피로가 실측됐다. */
export const QUESTIONS_PER_TERM = 3;

/**
 * 한 문항의 보기 수. 실제 뜻 4개 + 마지막 "모르겠다" 하나.
 * `runner/run_mode1_5.py` 의 `CHOICES_PER_QUESTION` 과 **같은 값이어야 한다.**
 * 마지막 자리가 "모르겠다" 라는 것이 채점의 전제다 — 그 번호를 고르면 dontKnow 로 센다.
 */
export const CHOICES_PER_QUESTION = 5;

// <include file="machine/comments.xml" path="//term[@id='flattenQuestions']"/>
// 문항지를 용어 순 · 문항 순으로 펴고 1부터 번호를 매긴다.
// 쓰는 것: 없음 · 쓰이는 곳: tallySheet
/**
 * 중첩된 문항지를 한 줄로 펴고 `QNum` 을 1부터 매긴다.
 *
 * **`runner/run_mode1_5.py` 의 `flatten_questions` 와 같은 순서여야 한다.**
 * 번호 규칙이 두 언어에 살고 있어서, 한쪽만 고치면 채점이 남의 답을 본다.
 * 그래서 걸러 내지 않는다 — 이름이 빈 용어도 자리를 차지한 채 그대로 센다.
 *
 * `Answer` 는 **1부터 센 보기 번호**다. 문항지의 `answer` 는 0부터라 하나를 더한다.
 * 기입란의 `UserAns` 가 1부터이므로 여기서 자릿수를 맞춰 두고 뒤에서는 그냥 견준다.
 */
export function flattenQuestions(doc) {
  const out = [];
  for (const entry of doc?.terms ?? []) {
    const term = String(entry?.term ?? "").trim();
    const means = String(entry?.means ?? "");
    for (const q of entry?.questions ?? []) {
      out.push({
        QNum: out.length + 1,
        Term: term,
        Question: String(q?.ask ?? ""),
        Answer: Number.isInteger(q?.answer) ? q.answer + 1 : null,
        Means: means,
      });
    }
  }
  return out;
}

// <include file="machine/comments.xml" path="//term[@id='choiceNumber']"/>
// 사람이 적은 UserAns 를 보기 번호로 읽는다.
// 쓰는 것: 없음 · 쓰이는 곳: tallySheet
/**
 * `UserAns` 를 보기 번호로 읽는다. 못 읽으면 `null`.
 *
 * 사람이 손으로 채우는 칸이라 `3` 과 `"3"` 이 섞인다. 둘 다 받는다.
 *
 * **빈 칸은 `null` 이고, "모르겠다" 로 대신 채우지 않는다.** 안 푼 것과 모르는 것은
 * 다르다. 자동으로 메우면 그 차이가 점수에 조용히 섞인다.
 */
export function choiceNumber(value) {
  if (typeof value === "number") return Number.isInteger(value) ? value : null;
  const text = String(value ?? "").trim();
  return /^\d+$/.test(text) ? Number(text) : null;
}

// <include file="machine/comments.xml" path="//term[@id='tallySheet']"/>
// 채운 기입란을 문항지와 대조해 용어마다 맞힌 수와 모르겠다 수를 센다.
// 쓰는 것: flattenQuestions, choiceNumber · 쓰이는 곳: 없음
/**
 * 채운 기입란을 문항지와 대조해 용어마다 맞힌 수를 센다.
 * `{ counts, problems }` 를 낸다 — `counts` 는 `gradeAll` 이 그대로 받는 꼴이다.
 *
 * **사람이 세던 자리를 없앤 것이 이 함수다.** 예전에는 사람이 맞힌 수를 직접 적었고,
 * 그래서 "3문항인데 맞힌 수 5" 같은 것이 채점을 통과했다.
 *
 * `problems` 가 비지 않으면 **채점하지 않는다.** 특히 `Term` 과 물음 문구를 대조하는 것은
 * 위 `flattenQuestions` 의 번호 규칙이 파이썬 쪽과 어긋났을 때 조용히 남의 답을
 * 채점하는 일을 막으려는 것이다. 판정이 아니라 아귀가 맞는지만 본다.
 */
export function tallySheet(sheet, doc) {
  const problems = [];
  const counts = {};
  for (const entry of doc?.terms ?? []) {
    const term = String(entry?.term ?? "").trim();
    if (term) counts[term] = { correct: 0, dontKnow: 0, means: String(entry?.means ?? "") };
  }

  const got = sheet?.questions;
  if (!Array.isArray(got)) {
    return { counts, problems: ["기입란 파일이 아니다 — `questions` 배열이 없다"] };
  }

  // 번호로 찾을 수 있게 먼저 모은다. 파일 안의 차례는 상관하지 않는다 — 사람이 손으로
  // 채우다 순서를 흐트러뜨릴 수 있고, 그것 자체는 틀린 일이 아니다.
  const byNum = new Map();
  for (const [i, rec] of got.entries()) {
    const num = rec?.QNum;
    if (!Number.isInteger(num)) {
      problems.push(`${i + 1}번째 칸 — QNum 이 정수가 아니다: ${JSON.stringify(rec?.QNum)}`);
      continue;
    }
    if (byNum.has(num)) problems.push(`${num}번 문항의 답안이 둘 이상이다`);
    byNum.set(num, rec);
  }

  for (const q of flattenQuestions(doc)) {
    const rec = byNum.get(q.QNum);
    byNum.delete(q.QNum);
    if (!rec) {
      problems.push(`${q.QNum}번(${q.Term}) — 문항은 냈는데 답안이 없다`);
      continue;
    }
    if (String(rec.Term ?? "") !== q.Term) {
      problems.push(
        `${q.QNum}번 — 용어가 어긋난다. 문항지는 ${JSON.stringify(q.Term)} 인데 ` +
          `답안은 ${JSON.stringify(rec.Term ?? "")} 이다`,
      );
      continue;
    }
    if (String(rec.Question ?? "") !== q.Question) {
      problems.push(`${q.QNum}번(${q.Term}) — 물음 문구가 문항지와 다르다`);
      continue;
    }
    const ans = choiceNumber(rec.UserAns);
    if (ans === null) {
      problems.push(`${q.QNum}번(${q.Term}) — UserAns 가 비었다. 안 푼 것을 "모르겠다" 로 세지 않는다`);
      continue;
    }
    if (ans < 1 || ans > CHOICES_PER_QUESTION) {
      problems.push(`${q.QNum}번(${q.Term}) — UserAns 가 보기 밖이다(1~${CHOICES_PER_QUESTION}): ${ans}`);
      continue;
    }
    const bucket = counts[q.Term];
    if (!bucket) continue;                       // 이름 빈 용어. validate_questions 가 따로 잡는다
    if (ans === CHOICES_PER_QUESTION) bucket.dontKnow += 1;
    else if (ans === q.Answer) bucket.correct += 1;
  }

  for (const num of [...byNum.keys()].sort((a, b) => a - b)) {
    problems.push(`${num}번 — 내지 않은 문항의 답안이 있다`);
  }
  return { counts, problems };
}

// <include file="machine/comments.xml" path="//term[@id='gradeOne']"/>
// 용어 하나의 답안을 채점해 확실 · 애매 · 모름을 매긴다.
// 쓰는 것: QUESTIONS_PER_TERM · 쓰이는 곳: gradeAll
/**
 * 한 용어의 답안을 채점한다. 두 갈래다 — 확실 / 모름.
 * 구간은 사용자가 확정한 값이다(2026-08-29, 3문항 규칙). 임의로 바꾸지 말 것.
 *   "모르겠다" 2회 이상        -> 모름 (찍어서 맞힌 것을 안다고 세지 않는다)
 *   맞힌 수 2~3 (67% 이상)     -> 확실
 *   맞힌 수 0~1                -> 모름
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

// <include file="machine/comments.xml" path="//term[@id='gradeAll']"/>
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
  // 직접 실행(node quiz.mjs grade answers.json questions.json)도 받도록 앞의 "grade" 는 벗겨 낸다.
  const args = process.argv.slice(2);
  if (args[0] === "grade") args.shift();
  const [answersFile, questionsFile] = args;
  if (!answersFile || !questionsFile) {
    console.error("사용법 — report-term grade <answers.json> <questions.json>");
    console.error("  answers.json  — 실행기가 깐 기입란(answer-sheet.json)의 UserAns 를 채운 것");
    console.error("  questions.json — 정답이 든 문항지. 사람은 풀기 전에 열지 않는다");
    console.error("  문항 작성과 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다.");
    process.exit(1);
  }

  const sheet = JSON.parse(readFileSync(answersFile, "utf8"));
  const doc = JSON.parse(readFileSync(questionsFile, "utf8"));
  const { counts, problems } = tallySheet(sheet, doc);
  if (problems.length > 0) {
    // 채점하지 않고 멈춘다. 아귀가 안 맞는 채로 낸 점수는 틀린 것보다 나쁘다 — 맞아 보인다.
    console.error("채점하지 않는다 — 채운 기입란이 문항지와 맞지 않는다:");
    for (const p of problems) console.error(`  ${p}`);
    process.exit(1);
  }

  const graded = gradeAll(counts);
  const path = join(process.cwd(), "term-grades.json");
  writeFileSync(path, JSON.stringify(graded, null, 2) + "\n");
  const tally = { 확실: 0, 애매: 0, 모름: 0 };
  for (const g of Object.values(graded)) tally[g.mental]++;
  console.log(`${path}`);
  console.log(`  확실 ${tally.확실} · 애매 ${tally.애매} · 모름 ${tally.모름}`);
}
