import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfBadge, StatusTag, DecisionTable, OptionTable, LockTable, NewStructNote, Reversal, Correction, TriageBlock, BeforeAfter, VerdictFooter, EvidenceNote, Glossary, defineTerms } from "../.tmp/lib.mjs";

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

test("BeforeAfter 는 토글과 두 패널을 낸다", () => {
  const out = html(BeforeAfter({
    id: "d1",
    before: { title: "Before", diagram: { svg: "<svg id='a'></svg>", naturalWidthPx: 2615, naturalHeightPx: 681 } },
    after:  { title: "After",  diagram: { svg: "<svg id='b'></svg>", naturalWidthPx: 1896, naturalHeightPx: 1051 } },
    legend: [{ color: "var(--green)", label: "added" }, { color: "var(--red)", label: "removed" }],
  }));
  assert.ok(out.includes('id="zoom-d1"'), "토글 id 없음");
  assert.ok(out.includes('class="zoom-toggle"'));
  assert.ok(out.includes('for="zoom-d1"'));
  assert.ok(out.includes('class="diagram-panel before"'));
  assert.ok(out.includes('class="diagram-panel after"'));
  assert.ok(out.includes('class="diagram-legend"'));
});

test("BeforeAfter 는 원본 폭을 --svg-w 로 주입한다 — B1 복구의 핵심", () => {
  const out = html(BeforeAfter({
    id: "d1",
    before: { title: "Before", diagram: { svg: "<svg></svg>", naturalWidthPx: 2615, naturalHeightPx: 681 } },
    after:  { title: "After",  diagram: { svg: "<svg></svg>", naturalWidthPx: 1896, naturalHeightPx: 1051 } },
    legend: [],
  }));
  assert.ok(out.includes("--svg-w:2615px"), "before 폭 미주입");
  assert.ok(out.includes("--svg-w:1896px"), "after 폭 미주입");
});

test("BeforeAfter 는 SVG 문자열을 이스케이프하지 않고 넣는다", () => {
  const out = html(BeforeAfter({
    id: "d1",
    before: { title: "B", diagram: { svg: '<svg id="x"><g/></svg>', naturalWidthPx: 10, naturalHeightPx: 10 } },
    after:  { title: "A", diagram: { svg: "<svg/>", naturalWidthPx: 10, naturalHeightPx: 10 } },
    legend: [],
  }));
  assert.ok(out.includes('<svg id="x"><g/></svg>'), "SVG 가 이스케이프됐다");
  assert.ok(!out.includes("&lt;svg"), "SVG 가 이스케이프됐다");
});

test("BeforeAfter 는 토글과 diagram-grid 를 형제로 낸다 — 형제 결합자 요건", () => {
  const out = html(BeforeAfter({
    id: "d1",
    before: { title: "B", diagram: { svg: "<svg/>", naturalWidthPx: 10, naturalHeightPx: 10 } },
    after:  { title: "A", diagram: { svg: "<svg/>", naturalWidthPx: 10, naturalHeightPx: 10 } },
    legend: [],
  }));
  const toggle = out.indexOf('class="zoom-toggle"');
  const label = out.indexOf('class="zoom-label"');
  const grid = out.indexOf('class="diagram-grid"');
  assert.ok(toggle !== -1 && label !== -1 && grid !== -1, "셋 중 빠진 것이 있다");
  assert.ok(toggle < label && label < grid, "토글 → 라벨 → 그리드 순서가 아니다");
  assert.ok(!out.slice(0, grid).includes("<div class=\"diagram-panel"), "그리드보다 패널이 먼저 나온다");
});

test("VerdictFooter 는 값을 채우지 않은 빈 기입란을 낸다", () => {
  const out = html(VerdictFooter({}));
  assert.ok(out.includes('class="verdict-footer"'));
  assert.ok(out.includes("승인"));
  assert.ok(out.includes("보류"));
  assert.ok(out.includes("번복"));
  assert.equal((out.match(/class="box"/g) || []).length, 3, "체크박스가 3개가 아니다");
  assert.ok(out.includes('class="owner-note"'));
});

test("EvidenceNote 는 실측과 판단을 별개 행으로 낸다", () => {
  const out = html(EvidenceNote({
    measured: ["노멀 반전 4지점 실측.", "back_face=true 호출부 0건."],
    judged: ["지금 만들면 검증할 대상이 없는 코드가 된다."],
  }));
  assert.equal((out.match(/class="note-row"/g) || []).length, 2, "행이 2개가 아니다");
  assert.ok(out.includes('<span class="conf-badge conf-green">🔵 실측</span>'));
  assert.ok(out.includes('<span class="conf-badge conf-red">💭 판단</span>'));
  // 두 배지가 같은 행에 있으면 안 된다
  const firstRowEnd = out.indexOf('class="note-row"', out.indexOf('class="note-row"') + 1);
  assert.ok(out.slice(0, firstRowEnd).includes("🔵 실측"), "첫 행에 실측이 없다");
  assert.ok(!out.slice(0, firstRowEnd).includes("💭 판단"), "판단이 실측과 같은 행에 있다");
});

test("EvidenceNote 는 문장마다 단락을 나눈다", () => {
  const out = html(EvidenceNote({
    measured: ["첫 문장.", "둘째 문장.", "셋째 문장."],
    judged: ["판단 한 문장."],
  }));
  assert.equal((out.match(/<p>/g) || []).length, 4, "단락이 4개가 아니다");
  assert.ok(out.includes("<p>첫 문장.</p>"));
  assert.ok(out.includes("<p>둘째 문장.</p>"));
  assert.ok(!out.includes("&nbsp;·&nbsp;"), "한 줄로 이어붙였다");
});

test("EvidenceNote 는 판단이 없으면 실측 행만 낸다", () => {
  const out = html(EvidenceNote({ measured: ["실측만 있다."] }));
  assert.equal((out.match(/class="note-row"/g) || []).length, 1);
  assert.ok(!out.includes("💭 판단"), "빈 판단 행이 나왔다");
});

test("EvidenceNote 는 단락 안의 인라인 마크업을 보존한다", () => {
  const mono = createElement("span", { className: "mono" }, "geometry.cpp:231");
  const out = html(EvidenceNote({
    measured: [createElement("span", null, "실측 근거는 ", mono, " 이다.")],
  }));
  assert.ok(out.includes('<span class="mono">geometry.cpp:231</span>'));
});

test("Glossary 는 이해도를 표시한다", () => {
  const out = html(Glossary({ terms: [
    { id: "calls[]", label: "calls[]", short: "호출 목록", kind: "artifact", mental: "모름" },
  ] }));
  assert.ok(out.includes("mental-모름"), "이해도 클래스가 없다");
});

test("Glossary 는 이해도가 없어도 렌더된다", () => {
  const out = html(Glossary({ terms: [
    { id: "A", label: "A", short: "x", kind: "concept" },
  ] }));
  assert.ok(out.includes("<td"), "이해도 없는 용어에서 깨졌다");
  assert.ok(out.includes("mental-미측정"), "이해도 없음이 미측정으로 표시되지 않는다");
});

test("Glossary 는 이해도 그룹을 모름 → 애매 → 확실 → 미측정 순으로 낸다", () => {
  const out = html(Glossary({ terms: [
    { id: "a", label: "a", short: "확실한 것", kind: "concept", mental: "확실" },
    { id: "b", label: "b", short: "미측정인 것", kind: "concept" },
    { id: "c", label: "c", short: "모르는 것", kind: "concept", mental: "모름" },
    { id: "d", label: "d", short: "애매한 것", kind: "concept", mental: "애매" },
  ] }));
  const pos = (s) => out.indexOf(s);
  assert.ok(pos("모르는 것") < pos("애매한 것"), "모름이 애매보다 앞");
  assert.ok(pos("애매한 것") < pos("확실한 것"), "애매가 확실보다 앞");
  assert.ok(pos("확실한 것") < pos("미측정인 것"), "확실이 미측정보다 앞");
});

test("Glossary 는 그룹을 details 로 싸고 모름 그룹만 열어 둔다", () => {
  const out = html(Glossary({ terms: [
    { id: "a", label: "a", short: "확실한 것", kind: "concept", mental: "확실" },
    { id: "c", label: "c", short: "모르는 것", kind: "concept", mental: "모름" },
  ] }));
  assert.equal((out.match(/<details/g) ?? []).length, 2, "그룹 하나에 details 하나");
  assert.equal((out.match(/<details[^>]*\bopen\b/g) ?? []).length, 1, "열린 것은 하나");
  const openBlock = out.slice(out.search(/<details[^>]*\bopen\b/), out.indexOf("</details>"));
  assert.ok(openBlock.includes("모르는 것"), "열린 그룹은 모름");
  assert.equal((out.match(/<script/g) ?? []).length, 0, "스크립트 없음");
});

test("Glossary 는 빈 그룹을 그리지 않고 제목에 개수를 적는다", () => {
  const out = html(Glossary({ terms: [
    { id: "a", label: "a", short: "확실 1", kind: "concept", mental: "확실" },
    { id: "b", label: "b", short: "확실 2", kind: "concept", mental: "확실" },
  ] }));
  assert.equal((out.match(/<details/g) ?? []).length, 1, "확실 그룹 하나뿐");
  assert.ok(!out.includes("mental-모름") && !out.includes("mental-애매") && !out.includes("mental-미측정"), "빈 그룹 없음");
  assert.ok(/<summary[^>]*>[\s\S]*?확실[\s\S]*?2[\s\S]*?<\/summary>/.test(out), "제목에 이해도와 개수");
});

test("Glossary 는 그룹 안에서 terms 배열 순서를 지킨다", () => {
  const out = html(Glossary({ terms: [
    { id: "z", label: "z", short: "먼저 온 것", kind: "concept", mental: "모름" },
    { id: "a", label: "a", short: "나중 온 것", kind: "concept", mental: "모름" },
  ] }));
  assert.ok(out.indexOf("먼저 온 것") < out.indexOf("나중 온 것"), "정렬하지 않는다");
});

test("TermRef 카드는 뜻 · 용례(body) · 이해도를 싣고 글자를 children 으로 받는다", () => {
  const T = defineTerms([{ id: "X", label: "X 라벨", short: "짧은 뜻", body: "용례 설명", kind: "concept", mental: "모름" }]);
  const out = html(T({ id: "X", children: "X" }));
  assert.ok(out.startsWith('<span class="term-ref" tabindex="0">X<span class="term-card">'), "children 이 글자");
  assert.ok(out.includes('class="term-card-body">짧은 뜻'), "뜻");
  assert.ok(out.includes('class="term-card-more">용례 설명'), "용례");
  assert.ok(out.includes("mental-모름"), "이해도 배지");
});

test("TermRef 카드는 body 와 mental 이 없으면 그 칸을 내지 않는다", () => {
  const T = defineTerms([{ id: "Y", label: "Y", short: "뜻", kind: "tool" }]);
  const out = html(T({ id: "Y" }));
  assert.ok(!out.includes("term-card-more") && !out.includes("term-mental"));
  assert.ok(out.includes('tabindex="0">Y<span class="term-card">'), "children 없으면 label");
});
