import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfBadge, StatusTag, DecisionTable, OptionTable, LockTable, NewStructNote, Reversal, Correction, TriageBlock } from "../.tmp/lib.mjs";

const html = (el) => renderToStaticMarkup(el);

test("ConfBadge 는 tier 에 맞는 이모지와 앵커를 낸다", () => {
  assert.equal(
    html(ConfBadge({ conf: { tier: "green", anchor: 99 } })),
    '<span class="conf-badge conf-green">🔵 99</span>'
  );
  assert.equal(
    html(ConfBadge({ conf: { tier: "amber", anchor: 75 } })),
    '<span class="conf-badge conf-amber">🟡 75</span>'
  );
  assert.equal(
    html(ConfBadge({ conf: { tier: "red", anchor: 65 } })),
    '<span class="conf-badge conf-red">💭 65</span>'
  );
});

test("ConfBadge 의 앵커는 숫자가 아니어도 된다", () => {
  assert.equal(
    html(ConfBadge({ conf: { tier: "green", anchor: "실측" } })),
    '<span class="conf-badge conf-green">🔵 실측</span>'
  );
});

test("ConfBadge 는 이모지 재정의를 허용한다 — 정본의 tier/이모지 불일치 재현", () => {
  assert.equal(
    html(ConfBadge({ conf: { tier: "green", anchor: 80, emoji: "🟡" } })),
    '<span class="conf-badge conf-green">🟡 80</span>'
  );
});

test("StatusTag 는 색 계열과 자유 문구를 분리한다", () => {
  assert.equal(
    html(StatusTag({ variant: "accepted", children: "검증됨 · 기록 완료" })),
    '<span class="status-tag status-accepted">검증됨 · 기록 완료</span>'
  );
  assert.equal(
    html(StatusTag({ variant: "proposed", children: "비-목표 (남은 갭)" })),
    '<span class="status-tag status-proposed">비-목표 (남은 갭)</span>'
  );
});

test("DecisionTable 은 card/table-wrap 으로 감싸고 결정마다 행을 낸다", () => {
  const out = html(DecisionTable({
    decisions: [{
      id: "D0", title: "권한 경계를 어디에 둘 것인가",
      variant: "accepted", statusText: "검증됨 · 기록 완료",
      conf: { tier: "green", anchor: 99 }, optionCount: 2,
    }],
  }));
  assert.ok(out.includes('<div class="card table-wrap">'), "카드 래퍼 없음");
  assert.ok(out.includes("<th>#</th>"), "헤더 없음");
  assert.ok(out.includes("D0"), "결정 id 없음");
  assert.ok(out.includes("권한 경계를 어디에 둘 것인가"));
  assert.ok(out.includes('<span class="conf-badge conf-green">🔵 99</span>'));
  assert.ok(out.includes('<span class="status-tag status-accepted">검증됨 · 기록 완료</span>'));
  assert.ok(out.includes('<td class="num mono">2</td>'), "옵션 수 셀 없음");
});

test("OptionTable 은 추천 행에만 row-recommended 를 붙인다", () => {
  const out = html(OptionTable({
    columns: ["옵션", "결합도", "비용"],
    rows: [
      { cells: ["A — Model 소유", "높음", "낮음"], recommended: false },
      { cells: ["B — Material 소유", "낮음", "낮음"], recommended: true },
    ],
  }));
  assert.equal((out.match(/row-recommended/g) || []).length, 1, "추천 행이 1개가 아니다");
  assert.ok(out.includes('<tr class="row-recommended">'));
  assert.ok(out.includes("B — Material 소유"));
});

test("LockTable 은 판정별로 다른 클래스를 붙인다", () => {
  const out = html(LockTable({
    rows: [
      { lockId: "D2", claim: "소유는 Material", verdict: "consistent", note: "일치" },
      { lockId: "D5", claim: "패스는 Model", verdict: "conflicting", note: "상충" },
      { lockId: "D7", claim: "무관", verdict: "unrelated", note: "-" },
    ],
  }));
  assert.ok(out.includes('class="verdict-consistent"'));
  assert.ok(out.includes('class="verdict-conflicting"'));
  assert.ok(out.includes('class="verdict-unrelated"'));
});

test("NewStructNote 는 4항목을 모두 낸다", () => {
  const out = html(NewStructNote({
    kind: "인터페이스", implementers: 1, consumers: 1,
    deletionTest: "삭제 시 Material 이 직접 패스를 들고 있으면 된다",
    grepEvidence: "git grep -c ': public ITechnique' → 1",
  }));
  assert.ok(out.includes('class="newstruct-note"'));
  assert.ok(out.includes("인터페이스"));
  assert.ok(out.includes("구현자 1"));
  assert.ok(out.includes("소비자 1"));
  assert.ok(out.includes("삭제 시 Material"));
  assert.ok(out.includes("git grep -c"));
});

test("Reversal 은 이전 rev 와 근거를 함께 낸다", () => {
  const out = html(Reversal({
    rev: "rev.1", previous: "Model 이 패스를 소유한다",
    now: "Material 이 소유한다", reason: "역방향 화살표가 드러났다",
  }));
  assert.ok(out.includes('class="reversal-note"'));
  assert.ok(out.includes("rev.1"));
  assert.ok(out.includes("Model 이 패스를 소유한다"));
  assert.ok(out.includes("역방향 화살표가 드러났다"));
});

test("Correction 은 정정 대상과 정정 내용을 낸다", () => {
  const out = html(Correction({
    target: "§3.2 의 구현자 수 3",
    correction: "그때의 grep 으로 세면 1이다",
  }));
  assert.ok(out.includes('class="correction-note"'));
  assert.ok(out.includes("§3.2 의 구현자 수 3"));
  assert.ok(out.includes("그때의 grep"));
});

test("TriageBlock 은 상위 항목을 순서대로 낸다", () => {
  const out = html(TriageBlock({
    items: [
      { id: "D2", title: "뒤집기의 의미", why: "되돌리기 비용이 가장 크다" },
      { id: "D0", title: "권한 경계", why: "나머지 결정의 전제" },
    ],
  }));
  assert.ok(out.includes('class="triage-block"'));
  const posD2 = out.indexOf("D2"), posD0 = out.indexOf("D0");
  assert.ok(posD2 < posD0, "입력 순서가 보존되지 않았다");
  assert.ok(out.includes("되돌리기 비용이 가장 크다"));
});
