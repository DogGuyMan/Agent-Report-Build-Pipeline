import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfBadge, StatusTag, DecisionTable, OptionTable, LockTable } from "../.tmp/lib.mjs";

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
