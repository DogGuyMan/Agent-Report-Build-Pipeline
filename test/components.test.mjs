import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfBadge, StatusTag } from "../.tmp/lib.mjs";

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
