// test/golden.test.mjs — 정본 골든 대조
//
// components.test.mjs 는 "컴포넌트가 설계대로 렌더되는가" 를 본다.
// 이 파일은 다른 것을 본다 — **정본 HTML 이 실제로 쓴 마크업과 같은가.**
// 출처가 이 저장소 밖의 문서라 파일을 나눴다.
//
// 골든 출처 (2026-08-28 실측):
//   $GRAPHICS_REPO/doc/superpowers/specs/
//     2026-07-27-geometry-winding-ownership-design-review.html          (이하 G)
//     2026-07-27-matrix-rain-parameterization-design-review.html        (이하 M)
//
// **외부 저장소를 읽지 않는다.** 조각을 리터럴로 박아 이 저장소만으로 돌아가게 한다.
// 정본이 갱신되면 이 리터럴을 손으로 다시 뜬다.
//
// 대조 단위는 **정본에서 한 줄로 나타나는 인라인 조각**이다.
// 블록(<tr>, <div class="verdict-footer">)은 정본이 들여쓰기·줄바꿈을 갖는 반면
// renderToStaticMarkup 은 태그 사이 공백을 내지 않아 바이트 동등이 원리적으로 불가능하다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfBadge, StatusTag, DecisionTable, VerdictFooter } from "../.tmp/lib.mjs";

const html = (el) => renderToStaticMarkup(el);

// ── 통과 항목 — 정본과 바이트 동일 ────────────────────────────────

test("정본 골든 — ConfBadge 가 정본의 배지 문자열과 바이트 동일하다", () => {
  // G:136,171,157,178 · G:973,975 (실측/판단 주석 블록)
  const golden = [
    [{ tier: "green", anchor: 99 }, '<span class="conf-badge conf-green">🔵 99</span>'],
    [{ tier: "green", anchor: 85 }, '<span class="conf-badge conf-green">🔵 85</span>'],
    [{ tier: "amber", anchor: 75 }, '<span class="conf-badge conf-amber">🟡 75</span>'],
    [{ tier: "red", anchor: 65 }, '<span class="conf-badge conf-red">💭 65</span>'],
    [{ tier: "green", anchor: "실측" }, '<span class="conf-badge conf-green">🔵 실측</span>'],
    [{ tier: "red", anchor: "판단" }, '<span class="conf-badge conf-red">💭 판단</span>'],
  ];
  for (const [conf, want] of golden) {
    assert.equal(html(ConfBadge({ conf })), want, `conf=${JSON.stringify(conf)}`);
  }
});

test("정본 골든 — emoji 재정의가 정본의 tier/이모지 불일치를 재현한다", () => {
  // G:143 — conf-green 인데 🟡 80. 정본 전체에서 유일한 불일치 1건이다
  // (정본 2개 파일의 conf-badge 24개를 전수 검사한 2026-08-28 실측).
  // CLAUDE.md 와 계획서는 "2건" 이라고 적어 뒀으나 실측은 1건이다.
  // 사용자 방침: 저작 실수로 보고 tier 를 amber 로 정정한다 — 다만 정본 파일 자체는 건드리지 않는다.
  assert.equal(
    html(ConfBadge({ conf: { tier: "green", anchor: 80, emoji: "🟡" } })),
    '<span class="conf-badge conf-green">🟡 80</span>'
  );
});

test("정본 골든 — StatusTag 가 정본의 상태 배지와 바이트 동일하다", () => {
  // G:139,142(accepted) · G:? (proposed) · M:? (superseded)
  const golden = [
    ["accepted", "확정 사용자 · rev.1 번복", '<span class="status-tag status-accepted">확정 사용자 · rev.1 번복</span>'],
    ["accepted", "확정 사용자 · 구현됨", '<span class="status-tag status-accepted">확정 사용자 · 구현됨</span>'],
    ["accepted", "검증됨 · 전수 비교 GREEN", '<span class="status-tag status-accepted">검증됨 · 전수 비교 GREEN</span>'],
    ["proposed", "비-목표 (남은 갭)", '<span class="status-tag status-proposed">비-목표 (남은 갭)</span>'],
    ["proposed", "제안됨 · 실측 반례 확보", '<span class="status-tag status-proposed">제안됨 · 실측 반례 확보</span>'],
    ["superseded", "번복됨", '<span class="status-tag status-superseded">번복됨</span>'],
  ];
  for (const [variant, text, want] of golden) {
    assert.equal(html(StatusTag({ variant, children: text })), want, `${variant}/${text}`);
  }
});

test("정본 골든 — VerdictFooter 의 선택지 마크업이 정본과 바이트 동일하다", () => {
  // G — <span class="choice"><span class="box"></span>승인</span>
  const out = html(VerdictFooter({}));
  for (const label of ["승인", "보류", "번복"]) {
    assert.ok(
      out.includes(`<span class="choice"><span class="box"></span>${label}</span>`),
      `${label} 선택지 마크업이 정본과 다르다`
    );
  }
});

// ── 정본과 다른 항목 — 미결정. 값을 고정해 변경을 감지한다 ──────────
//
// 아래 테스트는 "정본과 같다" 를 주장하지 않는다. **현재 값을 고정**해 두고,
// 누가 바꾸면 실패시켜 미결정 사항을 다시 꺼내게 하는 것이 목적이다.

test("미결정 — 결정 표 헤더 3곳이 정본과 다르다", () => {
  const out = html(DecisionTable({ decisions: [] }));
  // 정본 G:131 — <th>D#</th><th>결정</th><th>확신도</th><th>Status</th><th class="num">옵션 수</th>
  const canonical = '<tr><th>D#</th><th>결정</th><th>확신도</th><th>Status</th><th class="num">옵션 수</th></tr>';
  const current = '<tr><th>#</th><th>결정</th><th>확신도</th><th>상태</th><th class="num">옵션</th></tr>';
  assert.ok(out.includes(current), "헤더가 바뀌었다 — 정본에 맞출지 미결정이었다. 결정을 먼저 하라");
  assert.notEqual(current, canonical, "정본과 같아졌다면 이 테스트를 골든 대조로 승격하라");
  // 차이: D# vs # · Status vs 상태 · "옵션 수" vs 옵션
});

test("미결정 — VerdictFooter 의 사유란·안내문이 정본과 다르다", () => {
  const out = html(VerdictFooter({}));
  // 정본 G — <div class="reason-line">사유: &nbsp;</div>
  //          <div class="owner-note"><strong>판정 주체 = 사용자.</strong> 이 칸은 AI가 채우지 않는다.</div>
  assert.ok(out.includes('<div class="reason-line">사유 —</div>'),
    "사유란이 바뀌었다 — 정본은 '사유: &nbsp;' 다. 맞출지 미결정이었다");
  assert.ok(out.includes('<div class="owner-note">이 칸은 사용자가 직접 채운다.'),
    "안내문이 바뀌었다 — 정본은 <strong> 강조를 쓴다. 맞출지 미결정이었다");
});
