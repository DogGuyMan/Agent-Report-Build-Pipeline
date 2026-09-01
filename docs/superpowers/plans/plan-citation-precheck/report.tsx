import {
  Page, Section, DecisionTable, OptionTable, LockTable, TriageBlock,
  EvidenceNote, NewStructNote, VerdictFooter, Glossary, TermGraph,
} from "report-builder";
import { data, terms } from "./data.js";

export { data };

// 원본 계획서. 인용 표기의 기준 파일이다.
const SPEC = "docs/superpowers/plans/2026-08-31-plan-citation-precheck.md";
// 대조군으로 같은 검사를 돌려 본 다른 계획서.
const SURVEY = "docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md";

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

      <Section title="먼저 볼 것">
        <TriageBlock
          items={[
            {
              id: "T1",
              title: "이 계획서 자신을 검사에 걸면 12건이 나오지만, 실제 표류는 0건이다",
              why: "이번 세션에 계획서가 제안한 판정 로직을 그대로 돌린 결과다. 걸린 12건은 전부 계획서 안 코드 상자에 적힌 가상 이름(a/b.py · no/such/file.py · ghost.py · also/missing.ts · old/path.ts)이거나 이 계획이 앞으로 만들 파일(machine/doc_citations.py · test/test_doc_citations_report.py)이다. 미검토 — 이 보고서가 추가.",
            },
            {
              id: "T2",
              title: "깨진 인용 목록은 같은 항목을 두 번 싣는다 — 경로 목록만 중복을 지운다",
              why: "이번 세션 실측 — 계획서 자신에서 인용 6건 중 고유 4건. 경로 쪽은 중복 제거를 거치지만 인용 쪽은 거치지 않는다. 사람이 읽을 목록이라면 갈래가 달라진 이유가 필요하다. 미검토 — 이 보고서가 추가.",
            },
            {
              id: "T3",
              title: "검사 기준 저장소가 도구 저장소로 고정된다",
              why: "계획서는 원본 문서 경로를 프로젝트 저장소에서 만들면서 대조 기준만 도구 저장소로 넘긴다. 두 저장소가 다를 때 무슨 값이 나오는지는 계획서에 적혀 있지 않다. 미검토 — 이 보고서가 추가.",
            },
          ]}
        />
      </Section>

      <Section title="D1 — 인용 판정 함수 7개를 시험 파일 밖으로 옮긴다">
        <EvidenceNote
          measured={[
            <>옮길 대상은 시험 파일 안의 <span className="mono">CITE</span> · <span className="mono">PATH_REF</span> 와 함수 7개다 — <span className="mono">test/test_docs_citations.py:7-62</span>. 이번 세션에 자리를 직접 확인했다.</>,
            <>지금 그 시험 파일은 <strong>10개</strong>가 통과한다 — <span className="mono">.venv/bin/python -m pytest test/test_docs_citations.py -q</span> → <span className="mono">10 passed</span>.</>,
            <><span className="mono">machine/doc_citations.py</span> 는 아직 없다. 이번 세션 <span className="mono">ls</span> 확인.</>,
            <>계획 본문 — 옮기되 하는 일은 바꾸지 않는다(행동 불변). <span className="mono">{SPEC}:192-195</span></>,
          ]}
          judged={[
            <>계획서가 옮긴 뒤 기대치로 적은 시험 개수와 함수 개수는 지금 저장소와 어긋난다. 정본 대조표 <span className="mono">K2</span> · <span className="mono">K3</span> 를 보라.</>,
          ]}
        />
      </Section>

      <Section title="D2 — 고정 아홉 문서 밖을 보는 citationReport() 를 새로 만든다">
        <EvidenceNote
          measured={[
            <>지금 검사 대상은 contextDocs 가 돌려주는 길잡이 문서 아홉 개뿐이고, 계획서와 스펙은 그 목록에 없다. <span className="mono">{SPEC}:28-31</span></>,
            <>새 함수는 L1(파일 존재)까지만 본다. L2 · L3 는 하지 않는다 — 반환 꼴이 깨진 인용 목록과 깨진 경로 목록 둘뿐이다. <span className="mono">{SPEC}:265-282</span></>,
            <><strong>이번 세션 실측 — 계획서 자신에 같은 판정을 돌린 결과 12건(인용 6 · 경로 6)이 걸렸고, 그중 실제 표류는 0건이다.</strong> 12건은 계획서 코드 상자의 가상 이름 10건과 이 계획이 만들 파일 2건이다.</>,
            <><strong>이번 세션 실측 — 대조군</strong> <span className="mono">{SURVEY}</span> 에 같은 판정을 돌리면 35건(인용 18 · 경로 17)이 걸리고 그중 19건이 옛 <span className="mono">codegraph/</span> 경로다. 나머지는 그 문서의 예시 이름이다.</>,
          ]}
          judged={[
            <>대조군 결과는 이 장치가 실제 표류를 잡는다는 쪽을 가리킨다. 같은 결과가 이 계획서 자신에 대해서는 소음만 낸다는 것도 함께 가리킨다 — 코드 상자 안의 이름을 걸러 낼 자리가 계획서에 없다.</>,
            <>거를 자리를 어디에 둘지(정규식 · 코드 상자 제외 · 사람 판정)는 이 보고서가 정하지 않는다.</>,
          ]}
        />
      </Section>

      <Section title="D3 — 지시문에 선택 블록으로 얹고 0건이면 생략한다">
        <EvidenceNote
          measured={[
            <>본보기가 이미 있다 — terms_block 이 같은 방식으로 붙는다. <span className="mono">runner/run_mode2.py:234</span> · 지시문 안 자리 <span className="mono">:292</span> · 조립 호출 <span className="mono">:303</span>. 이번 세션 확인.</>,
            <>손댈 함수의 자리도 계획서가 적은 그대로다 — agent_prompt <span className="mono">:222</span> · run_agent <span className="mono">:310</span> · 용어집 재료를 구하는 줄 <span className="mono">:404-405</span>.</>,
            <>새 인자는 선택이라 기존 호출부는 바뀌지 않는다. 계획서가 그 회귀 시험을 함께 적어 두었다. <span className="mono">{SPEC}:327-330</span></>,
          ]}
          judged={[
            <>지시문 조각이 두 개로 늘어난다. 셋째가 생기면 조립 방식을 다시 볼 자리가 되겠지만, 지금 두 개로는 볼 이유가 없다.</>,
          ]}
        />
      </Section>

      <Section title="D4 — 저장소 뿌리를 검색 경로에 넣어 새 모듈을 부른다">
        <OptionTable
          columns={["안", "배선", "이번 세션에 직접 돌려 본 결과", "판정"]}
          rows={[
            {
              recommended: false,
              cells: [
                <>1안</>,
                <>machine 폴더 자체를 검색 경로에 넣고 평평한 import 로 부른다 — <span className="mono">runner/run_mode1.py:122-131</span> 이 쓰는 방식</>,
                <><span className="mono">from machine.terms_db import check_terms</span> → <span className="mono">ModuleNotFoundError: No module named &apos;codegraph_types&apos;</span></>,
                <><strong>기각</strong> — 계획 배경 절 <span className="mono">{SPEC}:36-43</span></>,
              ],
            },
            {
              recommended: true,
              cells: [
                <>2안</>,
                <>저장소 뿌리를 검색 경로에 넣고 <span className="mono">from machine.doc_citations import …</span> 로 부른다</>,
                <><span className="mono">from machine.declmap import X</span> → <span className="mono">ImportError: cannot import name &apos;X&apos;</span> — 모듈 자체는 찾았다는 뜻</>,
                <><strong>채택</strong> — D4</>,
              ],
            },
          ]}
        />
        <EvidenceNote
          measured={[
            <>machine 은 <span className="mono">__init__.py</span> 가 없는 네임스페이스 패키지다. 그래도 뿌리를 넣으면 모듈은 찾힌다 — 위 2안의 오류 종류가 그 증거다.</>,
            <>2안이 되는 조건은 새 모듈이 이웃 모듈을 부르지 않는 것 하나뿐이다. 계획서가 표준 라이브러리(<span className="mono">os</span> · <span className="mono">re</span>)만 쓴다고 못박았다. <span className="mono">{SPEC}:16-17</span></>,
          ]}
          judged={[
            <>같은 폴더 안에서 부르는 방식이 두 갈래가 된다. 계획서는 그 사실을 Task 4 에서 나침반 문서에 남기게 해 두었다 — 갈래를 없애는 대신 적어 두는 쪽을 골랐다.</>,
          ]}
        />
      </Section>

      <Section title="D5 — 함수 하나로 끝낸다 (거울 함정 경계)">
        <EvidenceNote
          measured={[
            <>새 정규식을 만들지 않는다 — CITE · PATH_REF 를 글자 그대로 옮긴다. <span className="mono">{SPEC}:16-17</span> · <span className="mono">:102-108</span></>,
            <>플러그인 구조와 검사 규칙 목록판을 두지 않는다. 새로 생기는 이름은 citationReport 하나다. <span className="mono">{SPEC}:57-59</span></>,
            <>구현자 1 · 소비자 3 — 아래 신규 구조물 신고를 보라.</>,
          ]}
        />
      </Section>

      <Section title="D6 — 범위 밖 4건을 명시적으로 배제한다">
        <OptionTable
          columns={["배제한 것", "계획서가 든 이유", "출처", "판정"]}
          rows={[
            {
              recommended: false,
              cells: [
                <>함수·심볼이 실제로 있는지 검사</>,
                <>파일과 줄 번호와는 다른 문제다. 코드 지도나 구문 분석이 있어야 한다</>,
                <span className="mono">{SPEC}:529</span>,
                <><strong>배제</strong> — 하고 싶어지면 사용자에게 먼저 보고</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>옛 경로에서 새 경로 후보를 추천</>,
                <>확률로 맞추는 방식이라 이 계획(있나 없나만 본다)과 성격이 다르다</>,
                <span className="mono">{SPEC}:530</span>,
                <><strong>배제</strong> — 별도 결정 사안</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>verify_citations.py 와 합치기</>,
                <>그 도구는 코드 지도가 있어야 도는데 계획서·스펙에는 그 재료가 없을 수 있다</>,
                <span className="mono">{SPEC}:531</span>,
                <><strong>배제</strong> — 합치면 거울 함정</>,
              ],
            },
            {
              recommended: false,
              cells: [
                <>Mode 1 에도 같은 점검을 배선</>,
                <>Mode 1 에는 이미 짝이 되는 판정기가 있다</>,
                <span className="mono">{SPEC}:532</span>,
                <><strong>배제</strong> — 이번 계획은 Mode 2 의 공백만 메운다</>,
              ],
            },
          ]}
        />
        <EvidenceNote
          measured={[
            <>네 항목 모두 계획서 본문의 표에 그대로 적혀 있다. 이 보고서가 더한 항목은 없다.</>,
          ]}
          judged={[
            <>배제 사유는 전부 계획서 저자의 판단이고, 기계로 재어 볼 수 있는 값이 아니다. 그래서 이 결정만 확신도 앵커가 낮다 — 결정이 나쁘다는 뜻이 아니라 <strong>실측으로 뒷받침할 수 있는 몫이 없다</strong>는 뜻이다.</>,
          ]}
        />
      </Section>

      <Section title="정본 대조표 — 계획서의 주장과 지금 저장소">
        <LockTable
          rows={[
            {
              lockId: "K1",
              claim: "인용 판정 순수 함수가 test/test_docs_citations.py 의 7-62행에 있다",
              verdict: "consistent",
              note: "CITE 가 7행, 마지막 함수의 끝이 62행. 이번 세션 확인",
            },
            {
              lockId: "K2",
              claim: "옮긴 뒤 기존 12개 시험이 전부 통과해야 한다",
              verdict: "conflicting",
              note: "실제로는 10개다 — pytest 출력 10 passed. 기대치를 10 으로 고쳐야 행동 불변 확인이 성립한다",
            },
            {
              lockId: "K3",
              claim: "지울 지역 정의는 함수 여섯 개다",
              verdict: "conflicting",
              note: "실제로는 7개 — contextDocs · isExempt · stripExternalTrees · pathRefsIn · brokenPathRefs · citationsIn · brokenCitations. 계획서가 옮길 목록에는 7개가 다 적혀 있어 코드는 맞고 세는 말만 틀렸다",
            },
            {
              lockId: "K4",
              claim: "새 파일을 더할 자리는 runner/run_mode2.py 의 59-61행 부근, import run_mode1 as M 아래다",
              verdict: "conflicting",
              note: "그 import 는 63행이다. 부근이라는 완충이 있어 작업은 되지만 줄 번호는 어긋난다",
            },
            {
              lockId: "K5",
              claim: "machine/terms_db.py 의 check_terms 가 321행부터다",
              verdict: "consistent",
              note: "이번 세션 확인 — def check_terms 가 321행",
            },
            {
              lockId: "K6",
              claim: "runner/run_mode1.py:122-131 이 machine 폴더를 검색 경로에 넣는 자리다",
              verdict: "consistent",
              note: "이번 세션 확인 — 그 범위가 정확히 검색 경로 삽입과 평평한 import 셋이다",
            },
            {
              lockId: "K7",
              claim: "run_mode2.py 의 agent_prompt 222 · terms_block 234 · 지시문 자리 292 · 조립 303 · run_agent 310 · 용어집 재료 404-405",
              verdict: "consistent",
              note: "여섯 자리 모두 이번 세션 확인",
            },
            {
              lockId: "K8",
              claim: "machine/doc_citations.py 와 test/test_doc_citations_report.py 는 아직 없다",
              verdict: "consistent",
              note: "둘 다 없음. 계획서가 신설한다고 말한 그대로",
            },
            {
              lockId: "K9",
              claim: "runner/CLAUDE.md 에 run_mode1.py 만 machine 을 import 한다는 문단이 있다",
              verdict: "consistent",
              note: "36행. Task 4 가 손댈 자리가 실재한다",
            },
          ]}
        />
      </Section>

      <Section title="신규 구조물 신고 — machine/doc_citations.py">
        <NewStructNote
          kind="새 모듈 1개 + 새 함수 1개(citationReport). 새 클래스·새 인터페이스 없음"
          implementers={1}
          consumers={3}
          deletionTest="지우면 test/test_docs_citations.py 의 시험 10개가 전부 import 에서 죽고, Mode 2 지시문은 인용 점검 블록 없이 예전 그대로 돈다 — 즉 기능은 사라지지만 파이프라인은 선다"
          grepEvidence="소비자 3 = test/test_docs_citations.py · test/test_doc_citations_report.py(신설) · runner/run_mode2.py"
        />
        <EvidenceNote
          measured={[
            <>이 계획에는 Before/After 다이어그램이 없고, 계획서 폴더에도 그림 파일이 없다. 이번 세션 확인.</>,
            <>바뀌는 것은 파일 사이의 코드 위치와 함수 인자 하나이며, 층·소유·의존 방향이 바뀌지 않는다.</>,
          ]}
          judged={[
            <>그림 없이 읽어도 구조가 잡히는 규모라고 본다. 다만 그림을 요구할지는 사용자 몫이다 — 이 보고서는 없다는 사실만 적는다.</>,
          ]}
        />
      </Section>

      <Section title="확신도 앵커가 뜻하는 것">
        <EvidenceNote
          measured={[
            <>이 계획서에는 결정 기록표가 없어 확신도 앵커도 없다. 결정 요약표의 앵커는 <strong>이 보고서가 이번 세션에 근거를 얼마나 재어 봤는지</strong>를 나타낸다.</>,
            <>실측 = 계획서가 든 근거를 이번 세션에 파일이나 명령으로 직접 확인했다. 숫자 = 확인하지 못했거나 확인 결과가 계획서와 엇갈린다.</>,
          ]}
          judged={[
            <>따라서 앵커는 결정의 좋고 나쁨이 아니다. 판정은 아래 기입란의 몫이다.</>,
          ]}
        />
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>

      <Section title="컴포넌트 후보">
        <EvidenceNote
          measured={[
            <>이 보고서를 쓰며 <strong>EvidenceNote 를 8회</strong> 썼고, 그중 <strong>6회</strong>가 &quot;출처 표기가 붙은 실측 줄 + 판단 줄&quot; 이라는 같은 모양이었다.</>,
            <>정본 대조표에 <strong>상충 3건</strong>이 나왔다. 상충만 따로 세거나 도드라지게 보이는 자리가 없어 9행을 눈으로 훑어야 한다.</>,
            <>이 보고서의 실측 줄 <strong>전부</strong>가 <span className="mono">파일:줄</span> 을 mono 글꼴로 손수 감싼 것이다 — 인용 한 건을 적는 정해진 모양이 없다.</>,
          ]}
          judged={[
            <>세 가지 모두 지금 컴포넌트를 만들 근거로는 약하다고 본다. 소비자가 이 보고서 하나뿐이다. 횟수만 적어 두고 넘어간다.</>,
          ]}
        />
      </Section>
    </Page>
  );
}
