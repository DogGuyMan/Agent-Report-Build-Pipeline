// <include file="machine/comments.xml" path="//term[@id='emit.mjs']"/>
// 채점 결과를 학습 노트와 용어집 두 갈래로 내보내는 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// runner/term/emit.mjs — Mode 1.5 4단계. 두 갈래 산출물을 낸다.
//   (1) 학습 노트 .md   — 사람이 읽고 공부하는 것. 모름·애매만 싣는다
//   (2) 용어집 DB .json — Mode 2 의 terms 가 되는 것. **전부 싣고 표시를 달리 한다**
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/**
 * Mode 2 로 넘길 용어집. 객관적 정답과 주관적 이해도를 필드로 가른다.
 * 필드명 TermMeans · UserMentalValue 는 사용자가 확정한 이름이다. 바꾸지 말 것.
 * 확실로 판정된 용어도 빠뜨리지 않는다 — 표시를 달리하는 것은 Mode 2 컴포넌트의 일이다.
 */
export function toTermsDb(graded) {
  const out = {};
  for (const [term, rec] of Object.entries(graded)) {
    out[term] = {
      TermMeans: rec.means,
      UserMentalValue: rec.mental,
    };
  }
  return out;
}

/** 사람이 읽는 학습 노트. 이미 아는 것을 다시 싣지 않는다. 정답률 낮은 것부터. */
export function toStudyNote(graded) {
  const rows = Object.entries(graded)
    .filter(([, r]) => r.mental !== "확실")
    .sort((a, b) => (a[1].rate ?? 0) - (b[1].rate ?? 0));

  const head = "# 용어 학습 노트\n\n실측으로 가려낸, 아직 확실하지 않은 용어들이다.\n\n";
  if (rows.length === 0) return head + "학습할 용어가 없다. 전부 확실로 판정됐다.\n";

  const body = rows
    .map(([term, r]) => `## ${term}\n\n- 이해도 — **${r.mental}** (정답률 ${r.rate}%)\n- 뜻 — ${r.means}\n`)
    .join("\n");
  return head + body;
}

// 직접 실행됐을 때만 파일을 읽고 쓴다. import 시에는 순수 함수만 노출한다(러너·시각축 .mjs 규약).
if (process.argv[1] && process.argv[1].endsWith("emit.mjs")) {
  // dispatch.mjs 는 명령어 이름(emit)을 소비하고 나머지 인자만 넘긴다 — collect·quiz 와 같은 꼴.
  // 직접 실행(node emit.mjs emit term-grades.json)도 받도록 앞에 남은 "emit" 은 벗겨 낸다.
  const args = process.argv.slice(2);
  if (args[0] === "emit") args.shift();
  const [file] = args;
  if (!file) {
    console.error("사용법 — report-term emit <term-grades.json>");
    process.exit(1);
  }
  const graded = JSON.parse(readFileSync(file, "utf8"));

  const dbPath = join(process.cwd(), "terms.json");
  writeFileSync(dbPath, JSON.stringify(toTermsDb(graded), null, 2) + "\n");

  const notePath = join(process.cwd(), "term-study-note.md");
  writeFileSync(notePath, toStudyNote(graded));

  const n = Object.keys(graded).length;
  const study = Object.values(graded).filter((r) => r.mental !== "확실").length;
  console.log(`${dbPath} — 용어 ${n}개 (전부 실림)`);
  console.log(`${notePath} — 학습 대상 ${study}개`);
}
