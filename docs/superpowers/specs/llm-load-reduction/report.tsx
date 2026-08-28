import { readFileSync } from "node:fs";
import {
  Page, Section, DecisionTable, OptionTable, EvidenceNote, BeforeAfter, VerdictFooter,
} from "report-builder";
import { inlineSvg } from "report-builder/svg";
import { data } from "./data.js";

export { data };

// 경로는 cwd(= specs/<slug>) 기준이다. build.mjs 가 임시 번들을 ROOT 에 쓰므로
// import.meta.url 을 쓰면 ROOT 를 가리켜 파일을 못 찾는다.
// idPrefix 는 before/after 가 달라야 한다 — 같으면 clipPath·marker 가 충돌한다.
const before = inlineSvg(readFileSync("before.svg", "utf8"), "llmbefore");
const after = inlineSvg(readFileSync("after.svg", "utf8"), "llmafter");

const SPEC = "2026-08-28-llm-load-reduction-design.md";

export default function Report() {
  return (
    <Page data={data}>
      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>

      <Section title="구조 변경 — 전수 정독 경로를 끊는다">
        <BeforeAfter
          id="llm-load"
          before={{ title: "Before — 사용자 소스 114파일 8,456줄 전수 정독", diagram: before }}
          after={{ title: "After — 정적 재료 확대 + 캐시 재사용 + 정독 계층 축소", diagram: after }}
          legend={[
            { color: "#d9534f", label: "제거 대상 — 전수 정독 경로" },
            { color: "#d2a03c", label: "신설·확장 — calls[] · WarmUp · tier" },
            { color: "#6aa06f", label: "인용 검증기" },
            { color: "#8fa4d4", label: "LLM 계층" },
          ]}
        />
      </Section>

      <Section title="D1 — 계측기를 먼저 만든다">
        <EvidenceNote
          measured={[
            <>M1 — 위키 인용 745건 중 <strong>정적 계층이 이미 아는 위치 616건(82.7%)</strong>. <span className="mono">{SPEC}:20</span></>,
            <>M2 — 구현 본문을 읽어야 아는 곳 129건(17.3%). 그중 <strong>호출식 64</strong> · 선언 16 · 주석 18 · 기타 31. <span className="mono">{SPEC}:21</span></>,
            <>계획 본문 — “이후 모든 Task 의 이득을 이 도구로 잰다. <strong>먼저 만든다.</strong>” <span className="mono">{SPEC}:81</span></>,
            <>산출물 — <span className="mono">codegraph/measure_citation_origin.py</span> (신규) · <span className="mono">codegraph/test_normalize.py</span> (추가)</>,
          ]}
          judged={[
            <>M1+M2 가 이 계획 전체의 논거다. 계측기가 먼저 서지 않으면 이후 “줄였다” 주장이 전부 미검증으로 남는다.</>,
          ]}
        />
      </Section>

      <Section title="D2 — calls[] 는 roslyn-dump.json 에만 넣는다 (C-19)">
        <EvidenceNote
          measured={[
            <>Track C §7 이 금지한 것은 <span className="mono">codegraph.json</span> 의 <span className="mono">calls[]</span> 이고, <span className="mono">roslyn-dump.json</span> 은 자체 형식이다 — <span className="mono">members[]</span>/<span className="mono">methods[]</span> 를 넣을 때와 같은 논거. <span className="mono">{SPEC}:261-262</span></>,
            <>인계 문서가 <span className="mono">calls[]</span> 를 “나중에 붙일 자리(지금 만들지 말 것)” 로 적어 뒀다. <span className="mono">docs/handoffs/HANDOFF-codebase-wiki.md:900</span></>,
            <>사용자 확정 U5 — <span className="mono">codegraph.json</span> 스키마 확장 허용, M1 을 근거로 재검토. <span className="mono">{SPEC}:40</span></>,
            <>대상 Task — 2(추출) · 3(검증기 인식) · 4(<span className="mono">facts/calls.md</span> 주입)</>,
          ]}
          judged={[
            <>M2 의 호출식 64건이 17.3% 중 최대 단일 항목이므로 우선순위가 가장 높다.</>,
          ]}
        />
        <OptionTable
          columns={["안", "내용", "출처", "판정"]}
          rows={[
            {
              recommended: false,
              cells: [
                <>1안</>,
                <><span className="mono">codegraph.json</span> 의 <span className="mono">edges[]</span> 로 승격 — 호출을 그래프 간선으로 올린다</>,
                <span className="mono">{SPEC}:311</span>,
                <><strong>기각</strong> — 정본 Track C §7</>,
              ],
            },
            {
              recommended: true,
              cells: [
                <>2안</>,
                <><span className="mono">roslyn-dump.json</span> 에 별도 배열 — 자체 형식이라 §7 금지 대상이 아니다</>,
                <span className="mono">{SPEC}:311 · :920</span>,
                <><strong>채택</strong> — C-19</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>3안</>,
                <>별도 파일 <span className="mono">calls.json</span> 으로 분리</>,
                <><strong>없음</strong> — <span className="mono">grep "calls\.json"</span> 저장소 전체 0건</>,
                <><strong>미검토</strong> — 이 보고서가 대조군으로 추가</>,
              ],
            },
          ]}
        />
        <EvidenceNote
          measured={[
            <>원문이 검토한 안은 <strong>둘</strong>이다 — 1안(기각) · 2안(채택). <span className="mono">{SPEC}:311</span> 한 줄에 둘 다 들어 있다.</>,
          ]}
          judged={[
            <><strong>3안은 원문에 없다.</strong> 대안이 둘뿐이면 비교가 성립하지 않아 대조군으로 세운 것이며, 검토된 적 없는 안이다. 판정 열이 그 구분을 표시한다.</>,
          ]}
        />
      </Section>

      <Section title="D3 — WarmUp 캐시는 파일별 요약 + git blob SHA 무효화 (C-20)">
        <EvidenceNote
          measured={[
            <>사용자 확정 U4(파일별 이해 요약 단위) · U6(git 기반 무효화). <span className="mono">{SPEC}:39,42</span></>,
            <>M4 — <strong>1커밋당 바뀌는 사용자 <span className="mono">.cs</span> 는 2 / 114 (1.8%)</strong>. <span className="mono">{SPEC}:23</span></>,
            <>내용 해시를 직접 계산하지 않는다 — git 이 이미 blob SHA 를 갖고 있다. 판정은 <strong>유효 / 낡음 / 판정불가 3값</strong>. <span className="mono">{SPEC}:921</span></>,
            <>캐시가 요약을 만들지 않는다 — 요약은 LLM 이 내고 이 도구는 수명과 무효화만 맡는다. <span className="mono">{SPEC}:546</span></>,
            <>남은 위험 — <span className="mono">blast_radius</span> 가 너무 넓을 수 있다. <span className="mono">hops=0</span> 폴백이 Step 5 에 있다. <span className="mono">{SPEC}:1063</span></>,
          ]}
        />
      </Section>

      <Section title="D4 — 모듈을 정독 / 개요 2계층으로 가른다 (C-21)">
        <EvidenceNote
          measured={[
            <>사용자 확정 U2 — 모든 모듈은 구조·시그니처로 싸게, <strong>중요한 소수만</strong> 구현 정독. <span className="mono">{SPEC}:39</span></>,
            <>기준은 이미 계산된 것만 쓴다 — PageRank 누적 60% · 순환 참여 · hotspot 상위10. <span className="mono">{SPEC}:922</span></>,
            <><span className="mono">TIER_PAGERANK_COVER = 0.60</span>. <span className="mono">{SPEC}:829</span></>,
            <>⚠ <strong>도구는 “무엇을 생략할지” 를 정하지 않는다</strong> — 그것은 Track C §1 20번으로 LLM 몫이다. 정하는 것은 “정독 예산을 어디 쓸까” 하나다. <span className="mono">{SPEC}:827</span></>,
          ]}
        />
      </Section>

      <Section title="D5 — 검증 가능한 코드 규약은 이번 계획에서 구현하지 않는다 (U3)">
        <EvidenceNote
          measured={[
            <>사용자 확정 U3 — 코드 규약은 검증 가능한 것만 받는다. <span className="mono">{SPEC}:40</span></>,
            <><span className="mono">calls[]</span> 로 82.7% → ?% 가 오른 뒤에도 남는 격차를 보고 정해야 한다. <strong>격차를 모르고 규약부터 만들면 거울 함정이다.</strong> <span className="mono">{SPEC}:1033</span></>,
            <>Self-Review 가 U3 을 “구현 없음 — 사유와 함께 기록” 으로 명시한다. <span className="mono">{SPEC}:1047</span></>,
          ]}
        />
      </Section>

      <Section title="D6 — C++ calls[] 는 보류">
        <EvidenceNote
          measured={[
            <>clang-uml 은 호출을 내지 않는다. <span className="mono">clangd</span> 역방향 갈래(보류 중)나 별도 도구가 필요하다. <span className="mono">{SPEC}:1032</span></>,
            <><strong>C# 에서 이득이 확인된 뒤에 검토한다.</strong> <span className="mono">{SPEC}:1032</span></>,
          ]}
        />
      </Section>

      <Section title="이 보고서가 보유하지 못한 것">
        <EvidenceNote
          measured={[
            <><span className="mono">data.ts</span> 의 D2 는 <span className="mono">optionCount: 3</span> 이나 <strong>옵션 비교표를 싣지 못했다</strong> — 설계 문서 1,063줄과 <span className="mono">HANDOFF-codebase-wiki.md</span> 에서 대안 3안의 서술을 찾지 못했다.</>,
            <>🟡 3건(D3 72 · D4 62 · D6 70)이 <span className="mono">optionCount: 0</span> 이다. <span className="mono">confidence-and-sourcing</span> §1.5 는 🟡 60–89 에 옵션표를 필수로 규정한다.</>,
            <>정본 대조표(<span className="mono">LockTable</span>)를 싣지 않았다 — 이번 작업 범위 밖이다.</>,
          ]}
          judged={[
            <>위 세 건은 저작자가 결정할 사항이라 임의로 채우지 않았다. 옵션표 없이 🟡 로 남길지, 대안을 추가할지, 티어를 낮출지는 사용자 판단이다.</>,
          ]}
        />
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
