import { readFileSync } from "node:fs";
import {
  Page, Section, DecisionTable, OptionTable, LockTable, NewStructNote, EvidenceNote, BeforeAfter, VerdictFooter,
  Glossary, TermGraph, defineTerms,
} from "report-builder";
import { inlineSvg } from "report-builder/svg";
import { data, terms } from "./data.js";

export { data };

// 경로는 cwd(= specs/<slug>) 기준이다. idPrefix 는 before/after 가 달라야 한다 — 같으면 clipPath·marker 가 충돌한다.
const before = inlineSvg(readFileSync("before.svg", "utf8"), "tdbbefore");
const after = inlineSvg(readFileSync("after.svg", "utf8"), "tdbafter");

const SPEC = "2026-08-29-mode-1-terms-db-first-design.md";

// 용어 인라인 참조. 정의는 data.ts 의 terms 에만 있다.
const T = defineTerms(terms);

export default function Report() {
  return (
    <Page data={data}>
      <Section title="용어집 — 먼저 읽을 것">
        <Glossary terms={terms} />
      </Section>

      <Section title="용어 관계도">
        <TermGraph terms={terms} />
      </Section>

      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>

      <Section title="구조 변경 — 낱말 사전이 원본이 되고 코드 지도는 거기서 뽑는다">
        <BeforeAfter
          id="tdb"
          before={{ title: "Before — 코드 지도가 원본, 낱말 사전은 정형문 · 이 저장소는 재료 없음", diagram: before }}
          after={{ title: "After — 인공지능 전수조사 1회 → 낱말 사전(원본) → 코드 지도(투영)", diagram: after }}
          legend={[
            { color: "#d9534f", label: "결함 — 정형문 · 간선 유실 · 재료 없음" },
            { color: "#d2a03c", label: "신설 — 읽기 원본 · 합치기 · 투영" },
            { color: "#6aa06f", label: "인용 검사 (L1 · L2 · L3)" },
            { color: "#8fa4d4", label: "LLM 계층 · Mode 1.5" },
          ]}
        />
      </Section>

      <Section title="D1 — terms-db.json 이 원본, codegraph.json 은 투영">
        <EvidenceNote
          measured={[
            <>지금의 <T id="terms_db.py" /> 는 <T id="means" /> 를 정형문으로 만들고, 간선의 방향 · 종류 · 위치를 <strong>버린다</strong> — 그래서 <T id="codegraph.json" /> 을 되돌릴 수 없다. <span className="mono">{SPEC}:17-18</span></>,
            <>이 저장소에는 <T id="codegraph.json" /> 이 없다 — <T id="정적 수집기" /> 가 파이썬 · 자바스크립트용으로는 없다. <span className="mono">{SPEC}:27</span></>,
            <>사용자 확정 — 인공지능 추론은 <strong>한 번</strong>. 그 한 번에 뜻 · 동작 · 관계를 다 얻고 지도는 거기서 <T id="투영" /> 한다. <span className="mono">{SPEC}:42, :952</span></>,
            <>🔵 드라이런 — 계획서의 코드 5개 Task 분을 스크래치패드에 조립해 실행했다: 신규 테스트 <strong>19개 통과</strong>(<T id="골든 테스트" /> 2개 포함, skip 아님) · 기존 3개 통과 · <T id="StickRush" /> 실물에 기존 호출 꼴로 <span className="mono">용어 241개 / 실패 0 / 근거 없음 0</span> · <span className="mono">투영에 없는 것 0개</span>. 계획서 <span className="mono">{SPEC}:906</span> 의 기대 출력과 글자까지 같다.</>,
          ]}
          judged={[
            <>계획서의 코드가 이미 도는 상태라 남은 위험은 구현이 아니라 <strong>Task 7 의 인공지능 읽기 품질</strong>이다 — 그건 실행해 봐야 안다.</>,
          ]}
        />
        <OptionTable
          columns={["안", "내용", "출처", "판정"]}
          rows={[
            {
              recommended: false,
              cells: [
                <>1안</>,
                <>지금처럼 <T id="codegraph.json" /> 이 원본, <T id="terms-db.json" /> 은 거기서 뽑은 정형문. 뜻은 Mode 1.5 가 그때그때 인공지능으로 채운다</>,
                <span className="mono">{SPEC}:17-18</span>,
                <><strong>기각</strong> — 인공지능 추론이 사전마다 반복되고, 이 저장소는 아예 시작 못 한다</>,
              ],
            },
            {
              recommended: true,
              cells: [
                <>2안</>,
                <><T id="terms-db.json" /> 이 원본. 인공지능 <T id="전수조사" /> 1회로 뜻 · 동작 · 관계를 얻고 <T id="codegraph.json" /> 은 <T id="투영" /></>,
                <span className="mono">{SPEC}:42, :952</span>,
                <><strong>채택</strong> — D1, 사용자 확정</>,
              ],
            },
          ]}
        />
      </Section>

      <Section title="D2 — 인공지능이 쓴 레코드는 where 필수, L1 · L2 · L3 3값 검사">
        <EvidenceNote
          measured={[
            <>판정 규칙은 <T id="verify_citations.py" /> 의 것을 그대로 빌린다 — <T id="L1" /> 파일 · <T id="L2" /> 줄은 실패, <T id="L3" /> 이름은 <T id="근거 없음" />. 앞뒤 1줄까지 본다. <span className="mono">{SPEC}:554-556</span></>,
            <>reading 레코드에 <T id="where" /> 가 없으면 실패 — "인용 없는 뜻은 싣지 않는다". <span className="mono">{SPEC}:605</span></>,
            <>검사 대상은 인공지능이 쓴 부분뿐이다. 정적 도구가 낸 위치는 재판정하지 않는다 — 합칠 때 인공지능이 보탠 간선에 <span className="mono">source="reading"</span> 표시를 남겨 그것만 본다. <span className="mono">{SPEC}:708</span></>,
            <>코드에 글자로 없는 것(앞선 계획의 결정 코드 · 개념어)은 사전에 넣지 않는다 — Mode 1.5 의 신규 개념으로 남긴다. <span className="mono">{SPEC}:971</span></>,
          ]}
        />
      </Section>

      <Section title="D3 — 구조 필드는 codegraph 가 이긴다">
        <EvidenceNote
          measured={[
            <>합칠 때 <T id="구조 필드" /> 네 칸은 codegraph 쪽을 지키고, 인공지능은 <T id="means" /> · <T id="does" /> · 새 <T id="uses[]" /> 만 보탠다. 입력은 제자리에서 바꾸지 않는다. <span className="mono">{SPEC}:701, :670</span></>,
            <>사용자의 그림은 "인공지능이 한 번 훑어 구조까지 얻는다" 이다. 정적 사실과 <strong>어긋날 때</strong> 어느 쪽을 믿을지가 이 결정이다. <span className="mono">{SPEC}:50</span></>,
          ]}
          judged={[
            <>정적 쪽을 택한 이유는 하나 — 그래야 <T id="verify_citations.py" /> 의 <T id="L3" /> 가 계속 성립한다. <T id="결정론" /> 은 codegraph 와 투영이 지키고, 인공지능은 인용으로 붙든다. 반례를 아직 못 봤으므로 🟡 75.</>,
          ]}
        />
        <OptionTable
          columns={["안", "내용", "출처", "판정"]}
          rows={[
            {
              recommended: true,
              cells: [
                <>1안</>,
                <>codegraph 가 있으면 <T id="구조 필드" /> 는 codegraph 가 이긴다. 인공지능은 뜻과 새 관계만</>,
                <span className="mono">{SPEC}:44, :701</span>,
                <><strong>채택</strong> — D3</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>2안</>,
                <>인공지능 읽기가 이긴다 — 구조도 인공지능이 본 대로 덮는다</>,
                <><span className="mono">{SPEC}:50</span> (사용자 그림의 문자 그대로 해석)</>,
                <><strong>기각</strong> — 정적 사실이 인공지능 추정에 덮이면 <T id="L3" /> 판정의 기준이 사라진다</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>3안</>,
                <>어긋나면 멈추고 사람에게 보고한다 (둘 다 안 믿는다)</>,
                <><strong>없음</strong> — 계획서에 서술 없음</>,
                <><strong>미검토</strong> — 이 보고서가 대조군으로 추가</>,
              ],
            },
          ]}
        />
      </Section>

      <Section title="D4 — 읽기 원본은 추적하고 파생물은 재생성한다">
        <EvidenceNote
          measured={[
            <><T id="terms-reading.json" /> 은 <span className="mono">docs/codegraph/</span> 에 두어 git 이 추적한다. <T id="terms-db.json" /> · <T id="codegraph.json" /> 은 <span className="mono">out/codegraph-raw/</span> — gitignore 이며 원본에서 명령 한 줄로 다시 만든다. <span className="mono">{SPEC}:45, :63</span></>,
            <>🔵 <span className="mono">.gitignore:8</span> 이 <span className="mono">out/</span> 전체를 무시한다 — 인공지능 산출물을 거기 두면 다른 머신에서 사라진다. <span className="mono">{SPEC}:45</span></>,
          ]}
          judged={[
            <>"원본은 추적, 파생물은 재생성" 은 이 저장소의 기존 규칙("git 에는 소스만")과 같은 결이다. 디렉토리 이름은 취향이라 🟡 70.</>,
          ]}
        />
        <OptionTable
          columns={["안", "내용", "출처", "판정"]}
          rows={[
            {
              recommended: true,
              cells: [
                <>1안</>,
                <>원본 <span className="mono">docs/codegraph/terms-reading.json</span> 추적, 파생물 <span className="mono">out/codegraph-raw/</span> 무시</>,
                <span className="mono">{SPEC}:45</span>,
                <><strong>채택</strong> — D4</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>2안</>,
                <>셋 다 <span className="mono">out/codegraph-raw/</span> — 외부 저장소 관례 그대로</>,
                <span className="mono">{SPEC}:45</span>,
                <><strong>기각</strong> — gitignore 라 인공지능 추론 결과가 사라진다. "추론은 한 번" 이 깨진다</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>3안</>,
                <><span className="mono">.gitignore</span> 에 예외를 뚫어 <span className="mono">out/codegraph-raw/</span> 의 세 파일만 추적</>,
                <><strong>없음</strong> — 계획서에 서술 없음</>,
                <><strong>미검토</strong> — 이 보고서가 대조군으로 추가. git 은 무시된 상위 디렉토리 아래를 되살리지 못해 규칙 6줄이 필요하다</>,
              ],
            },
          ]}
        />
      </Section>

      <Section title="D5 — 키 규칙">
        <EvidenceNote
          measured={[
            <>파일은 <span className="mono">kind: "file"</span> 로 파일명 키, 함수 · 클래스는 맨 이름, 겹치면 <strong>겹친 전원</strong>이 <span className="mono">파일줄기.이름</span>, <span className="mono">module</span> 은 디렉토리. <span className="mono">{SPEC}:46</span></>,
            <>🔵 <span className="mono">main</span> 이 파이썬 5개 파일에 있다 — 충돌 규칙이 필요한 실측 근거.</>,
            <>Plan <span className="mono">llm-load-reduction</span> 은 코드를 파일명(<span className="mono">normalize.py</span>)으로 부른다. 그래서 파일이 낱말이 된다. <span className="mono">{SPEC}:46</span></>,
          ]}
        />
        <OptionTable
          columns={["안", "내용", "출처", "판정"]}
          rows={[
            {
              recommended: true,
              cells: [
                <>1안</>,
                <>맨 이름이 기본, 겹칠 때만 <span className="mono">파일줄기.이름</span></>,
                <span className="mono">{SPEC}:46</span>,
                <><strong>채택</strong> — D5. Plan 본문과 낱말이 맞아야 Mode 1.5 가 잡는다</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>2안</>,
                <>항상 <span className="mono">파일줄기.이름</span> — 규칙이 하나라 단순하다</>,
                <><strong>없음</strong> — 계획서에 서술 없음</>,
                <><strong>미검토</strong> — 이 보고서가 대조군으로 추가. Plan 이 <span className="mono">build_terms</span> 라고만 쓰면 못 잡는다는 대가</>,
              ],
            },
          ]}
        />
      </Section>

      <Section title="D6 — 전수조사는 mode-1-codebase-wiki 가 한다">
        <EvidenceNote
          measured={[
            <>사용자 확정. 그 에이전트가 <span className="mono">codegraph/</span> 를 소유한다. <span className="mono">{SPEC}:47</span></>,
            <>Task 1~5 는 파일이 둘뿐이라 한 번에 맡겨도 된다. 커밋은 Task 마다 오케스트레이터가 사용자 승인 후. <span className="mono">{SPEC}:1074</span></>,
            <>절차는 에이전트 정의 파일에 <span className="mono">## 전수조사 절차</span> 절로 들어가고, 역할 서술 원본과 <strong>같이</strong> 고친다. <span className="mono">{SPEC}:952-978</span></>,
          ]}
        />
      </Section>

      <Section title="D7 — C# 저장소의 C1 시험은 이 계획 밖">
        <EvidenceNote
          measured={[
            <><T id="C1" /> 은 진짜 뜻이 담긴 사전으로만 시험할 수 있고, 그건 <T id="StickRush" /> 241개 레코드를 인공지능이 다시 읽어야 한다. <span className="mono">{SPEC}:1060</span></>,
            <>되살릴 조건 — <T id="StickRush" /> 용 Plan 이 생겼을 때. <span className="mono">{SPEC}:1060</span></>,
          ]}
          judged={[
            <>이 계획의 목적은 이 저장소의 사전이다. C# 은 별개 비용이라 미루는 것이 맞다고 보지만, 판단뿐이라 💭 55.</>,
          ]}
        />
      </Section>

      <Section title="정본 정합표 — 이 계획이 건드리는 규율">
        <LockTable
          rows={[
            { lockId: "규율-01", claim: "도구는 판정하지 않는다 — 계산 · 정렬 · 병치만", verdict: "consistent",
              note: "check_terms 는 3값 목록을 돌려줄 뿐 무엇을 고칠지 정하지 않는다 (계획서 :554-556)" },
            { lockId: "규율-02", claim: "normalize.py 의 출력 키를 바꾸지 않는다 (terms_db 간접 의존)", verdict: "consistent",
              note: "읽기만 한다. 투영은 그 키를 그대로 흉내 낸다 (:280-288 실측 기반)" },
            { lockId: "규율-03", claim: "에이전트 정의 — means 를 풍부하게 쓰려고 하지 않는다. LLM 을 끼우면 결정론이 깨진다", verdict: "conflicting",
              note: "사용자 결정(D1 · D2)으로 Task 6 이 개정한다 — '인용 없이 쓰지 않는다' 로. 결정론은 codegraph · 투영 · 인용 검사가 지킨다" },
            { lockId: "규율-04", claim: "CLI 는 사람에게 묻지 않는다", verdict: "consistent",
              note: "terms_db.py 는 파일을 읽고 쓸 뿐이다. 묻는 것은 없다" },
            { lockId: "규율-05", claim: "거울 함정 — 스키마 파일 · 플러그인 · 레지스트리 금지. 구현자 1 · 소비자 1이면 인터페이스를 만들지 않는다", verdict: "consistent",
              note: "스키마는 docstring 과 계획서 표가 정본. JSON Schema 파일은 만들지 않는다 (:1062)" },
            { lockId: "규율-06", claim: "합성 데이터만으로 검증하지 말 것", verdict: "consistent",
              note: "골든 테스트 2개가 실제 저장소 산출물을 쓴다 (:350). 드라이런에서 skip 아닌 pass" },
            { lockId: "규율-07", claim: "컴포넌트는 추가만 · <script> 예산 1", verdict: "unrelated",
              note: "Mode 2 렌더러를 건드리지 않는다" },
            { lockId: "규율-08", claim: "옛 산출물은 기준이 아니다", verdict: "unrelated",
              note: "옛 보고서를 참조하는 Task 가 없다" },
            { lockId: "규율-09", claim: "서브에이전트는 커밋하지 않는다", verdict: "consistent",
              note: "모든 커밋 단계가 '오케스트레이터가 사용자 승인 후' 다" },
          ]}
        />
      </Section>

      <Section title="신규 구조물 신고">
        <NewStructNote
          kind="terms-db 레코드 v2 — id · uses[] · does · source 3값 (계획서 :68 레코드 꼴)"
          implementers={1}
          consumers={2}
          deletionTest="지우면 codegraph.json 을 되돌릴 수 없고(투영 불가), Mode 1.5 는 정형문 정답지로 돌아가 C1 을 영영 시험하지 못한다"
          grepEvidence="grep -rl terms-db.json scripts codegraph .claude -> 6개 파일 (2026-08-29): .claude/agents/mode-1-5-term-benchmark.md .claude/agents/mode-1-codebase-wiki.md .claude/skills/term-benchmark/SKILL.md codegraph/terms_db.py scripts/init.mjs scripts/term/collect.mjs "
        />
      </Section>

      <Section title="이 보고서가 보유하지 못한 것">
        <EvidenceNote
          measured={[
            <>Task 7 의 산출물(<T id="terms-reading.json" />)은 아직 없다 — 이 보고서는 <strong>계획</strong> 검토이지 결과 검토가 아니다. 인공지능 읽기의 품질과 "known 8개 이상" 인수 조건(<span className="mono">{SPEC}:1039</span>)은 실행 후에만 잰다.</>,
            <>🟡 3건(D3 · D4 · D5) 옵션표의 "미검토 — 이 보고서가 추가" 행은 계획서에 없다. 대조군이지 검토된 안이 아니다.</>,
            <>D7 은 💭 55 — 근거가 판단뿐이다.</>,
            <>용어 {terms.length}개의 이해도는 <strong>전부 미측정</strong>이다. 이 계획이 바로 그 측정의 재료(정답지)를 만드는 계획이라, 자기 자신을 Mode 1.5 로 먼저 통과시킬 수 없었다.</>,
          ]}
          judged={[
            <>사용자가 정할 것 — D3 · D4 · D5 의 안 선택(1안이 기본값), D7 을 되살릴 시점, 그리고 착수 승인.</>,
          ]}
        />
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
