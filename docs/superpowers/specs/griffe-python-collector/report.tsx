import { readFileSync } from "node:fs";
import {
  Page, Section, DecisionTable, OptionTable, LockTable, NewStructNote,
  Reversal, EvidenceNote, BeforeAfter, VerdictFooter, Glossary, TermGraph,
} from "report-builder";
import { inlineSvg } from "report-builder/svg";
import { data, terms } from "./data.js";

export { data };

// 경로는 cwd(= specs/<slug>) 기준이다. idPrefix 는 before/after 가 달라야 한다.
const before = inlineSvg(readFileSync("before.svg", "utf8"), "gpcbefore");
const after = inlineSvg(readFileSync("after.svg", "utf8"), "gpcafter");

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

      <Section title="구조 변경 — 언어 갈래를 셋으로 늘린다">
        <BeforeAfter
          id="gpc"
          before={{ title: "Before — 언어 갈래 2개. Python 수집기 없음", diagram: before }}
          after={{ title: "After — 셋째 갈래 + 식 트리 순회기. 출구는 그대로", diagram: after }}
          legend={[
            { color: "#d2a03c", label: "이번에 더하는 것" },
            { color: "#8fa4d4", label: "기존 수집기" },
            { color: "#6aa06f", label: "공통 출구 — 재구현하지 않는다" },
            { color: "#d9534f", label: "지금 비어 있는 자리" },
          ]}
        />
      </Section>

      <Section title="D0 · griffe 를 Python 정적 수집기로 채택한다">
        <OptionTable
          columns={["안", "비용", "위험", "판정 · 출처"]}
          rows={[
            {
              cells: [
                "기성 라이브러리 griffe 를 얇게 감싼다",
                "함수 5개. 파서를 쓰지 않는다",
                "버전이 오르면 출력 모양이 바뀔 수 있다",
                "채택 (D0 · 사용자 승인 2026-08-29)",
              ],
              recommended: true,
            },
            {
              cells: [
                "표준 ast 모듈로 직접 덤퍼를 만든다",
                "파서·이름 해소를 전부 자작",
                "griffe 가 이미 푼 문제를 다시 푼다",
                "기각 (인계 문서 배경절)",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "실제로 설치해 machine/ 을 덤프했다 — griffe 2.2.0, 모듈 22 · 함수 265 · 클래스 1.",
            "출력은 {패키지이름: 모듈객체} 하나짜리 사전이고 members 는 이름으로 키질한 사전이다.",
          ]}
          judged={[
            "자작 덤퍼로 같은 수준(이름 해소 · 문자열 주석 파싱)에 도달하는 비용이 더 크다고 본다.",
          ]}
        />
      </Section>

      <Section title="D1 · R5(컨테이너 투과)를 범위에 포함한다">
        <Reversal
          rev="R5 제외 → R5 포함"
          previous="인계 문서: griffe 는 타입힌트를 문자열로 주므로 list[Foo] 를 직접 잘라 읽어야 한다. 첫 프로토타입에서 다루면 범위가 커지니 제외한다."
          now="R5 를 이번 범위에 포함한다. 껍데기를 벗기는 코드는 C# 갈래가 이미 하는 일과 같은 모양이다."
          reason="제외의 근거였던 전제가 사실이 아니었다. griffe 2.2.0 은 타입 표기를 문자열이 아니라 식 트리로 준다 — 껍데기와 알맹이가 이미 나뉘어 있다. 근거가 사라진 지시를 그대로 따르면 타입 주석을 쓴 파이썬 코드에서 관계가 통째로 사라진다."
        />
        <OptionTable
          columns={["안", "무엇이 달라지나", "판정 · 출처"]}
          rows={[
            {
              cells: [
                "R5 를 구현한다",
                "목록·사전·Optional 안에 든 관계가 살아난다",
                "채택 (D1 · 사용자 결정 2026-08-30)",
              ],
              recommended: true,
            },
            {
              cells: [
                "인계 문서대로 제외하고 카운터만 남긴다",
                "픽스처 기준 네 속성이 통째로 사라진다",
                "기각 — 근거였던 전제가 무너졌다",
              ],
              recommended: false,
            },
          ]}
        />
      </Section>

      <Section title="D2 · 골든 테스트 대상">
        <OptionTable
          columns={["안", "검사할 것이 남는가", "외부 의존", "판정 · 출처"]}
          rows={[
            {
              cells: [
                "합성 픽스처를 진짜 griffe 로 덤프 + 자기호스팅은 연기 시험",
                "남는다 — 상속·컨테이너·외부 참조를 픽스처가 전부 담는다",
                "없음",
                "채택 (D2 · 사용자 결정 2026-08-30)",
              ],
              recommended: true,
            },
            {
              cells: [
                "자기호스팅만 쓴다 (인계 문서안)",
                "거의 없다 — 클래스 1개 · 상속 0개",
                "없음",
                "기각 — 빈 그래프를 검증하게 된다",
              ],
              recommended: false,
            },
            {
              cells: [
                "외부 Python 저장소를 골든 대상으로 지정",
                "남는다",
                "있음 — 대상 저장소가 이 컴퓨터에 있어야 한다",
                "미검토 — 이 보고서가 추가한 안",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "machine/ 은 클래스 1개(machine.clangd_refs.Clangd) · 상속 0개 · 타입 주석 0개다.",
            "그래서 자기호스팅 결과는 노드 1개 · 간선 0개가 된다.",
          ]}
        />
      </Section>

      <Section title="D3 · kind 사상은 association-only">
        <EvidenceNote
          measured={[
            "C# 갈래는 같은 이유로 소유 kind 가 이미 0이고, 그 사실이 코드에 'C# 정상 — 함정 5' 로 적혀 있다.",
            "kind 8종은 고정이고 새 값을 만들 수 없다.",
          ]}
          judged={[
            "파이썬은 모든 이름이 대상을 가리키기만 하므로 담았는지 가리켰는지 구분이 언어에 없다 — 소유 kind 를 만들면 근거 없는 정보를 지어내는 것이 된다.",
          ]}
        />
      </Section>

      <Section title="D4 · 노드 입도는 클래스">
        <OptionTable
          columns={["안", "얻는 것", "잃는 것", "판정 · 출처"]}
          rows={[
            {
              cells: [
                "클래스만 노드로 삼는다",
                "C++/C# 과 같은 계약을 지킨다",
                "모듈 수준 함수의 관계가 전부 빠진다",
                "채택 (D4)",
              ],
              recommended: true,
            },
            {
              cells: [
                "클래스 + 모듈 수준 함수",
                "함수 위주 코드에서도 지도가 채워진다",
                "범위가 커진다",
                "보류 — C++ 이 clang-doc 으로 함수 노드를 내는 선례가 있어 길은 열려 있다",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "machine/ 은 함수 265개 · 클래스 1개다. 클래스만 노드로 삼으면 그 265개가 전부 간선을 만들지 못한다.",
            "C++ 갈래는 clang-doc 이 함수도 노드로 만든다 — 함수 노드는 이 형식에 이미 있는 것이지 새로 만들 것이 아니다.",
          ]}
          judged={[
            "이 대가는 작지 않다고 본다. 실제 파이썬 프로젝트에 써 본 뒤 다시 판단할 자리다.",
          ]}
        />
      </Section>

      <Section title="D5 · 모듈 경계는 module_of() 재사용">
        <OptionTable
          columns={["안", "근거", "판정 · 출처"]}
          rows={[
            {
              cells: [
                "기존 module_of() 를 그대로 쓴다",
                "폴더 트리 규칙이 파이썬에도 맞고 src 배치까지 이미 처리한다",
                "채택 (D5)",
              ],
              recommended: true,
            },
            {
              cells: [
                "py_module_of() 를 새로 만든다",
                "C++ 사정으로 원본이 바뀌어도 안전하다",
                "기각 — 결과가 같은 함수를 둘로 늘리는 것은 거울 함정 쪽이다",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "module_of() 는 폴더 트리 규칙이고 src/pkg/... 를 pkg 로 접는다 — 파이썬의 src 배치와 그대로 맞는다.",
            "machine/normalize.py 를 넣으면 machine 이 나온다. 파이썬 전용 규칙을 더할 것이 없다.",
          ]}
          judged={[
            "재사용의 위험은 남는다 — 그 함수의 주인은 C++ 이다. 그래서 파이썬 경로를 못박는 테스트를 함께 넣어, C++ 사정으로 바뀔 때 시끄럽게 깨지게 한다.",
          ]}
        />
      </Section>

      <Section title="Lock 대조 — 저장소의 확정 사항과 충돌하지 않는가">
        <LockTable
          rows={[
            { lockId: "거울 함정 금지", claim: "함수 5개만 더한다. 플러그인 구조 · 파서 레지스트리 · 추상 인터페이스 없음", verdict: "consistent", note: "구현자 1 · 소비자 1" },
            { lockId: "kind 8종 고정", claim: "기존 셋만 쓰고 새 kind 를 만들지 않는다", verdict: "consistent", note: "" },
            { lockId: "_assemble 은 공통 출구", claim: "재구현하지 않고 그대로 호출한다", verdict: "consistent", note: "" },
            { lockId: "커밋은 요청 시에만", claim: "계획의 마지막 단계가 커밋이 아니라 검증이다", verdict: "consistent", note: "" },
            { lockId: "R11 은 열린 결정", claim: "schema_version 3 · loc/url 을 건드리지 않는다", verdict: "consistent", note: "사용자 승인 전" },
            { lockId: "script 예산 1칸 · 컴포넌트 17개", claim: "Mode 2 파이프라인은 건드리지 않는다", verdict: "unrelated", note: "다른 갈래" },
          ]}
        />
      </Section>

      <Section title="신규 구조물 신고">
        <NewStructNote
          kind="함수 5개와 상수 3개를 기존 파일에 더한다 (새 파일 · 새 클래스 · 새 인터페이스 없음)"
          implementers={1}
          consumers={1}
          deletionTest="이 다섯 함수를 지우면 Python 갈래만 사라지고 C++/C# 은 그대로 돈다"
          grepEvidence="같은 모양의 언어 갈래가 normalize_cpp · normalize_csharp 로 이미 둘 있다. 세 번째를 같은 자리에 같은 방식으로 더하는 것이다"
        />
      </Section>

      <Section title="검증 상태 — 무엇이 실측이고 무엇이 아직인가">
        <EvidenceNote
          measured={[
            "계획 안의 구현을 scratchpad 에서 실제로 돌렸다 — 픽스처 기준 노드 3 · 간선 4 · 모듈 1.",
            "그 과정에서 지뢰 둘을 미리 밟았다. macOS 의 /var 가 /private/var 로 가는 링크라 상대경로가 어긋나 모듈 이름이 '..' 로 나온 것, 그리고 griffe 가 멤버를 알파벳 순으로 준다는 것.",
            "저장소 시험은 지금 전부 초록이다 — pytest 287 통과 · 19 건너뜀, npm test 177 통과.",
          ]}
          judged={[
            "실제 파이썬 프로젝트에 써 본 적은 없다. 자기호스팅은 시험이지 실사용이 아니므로 '소비자 0명' 문제는 그대로 남는다.",
            "griffe 버전을 requirements.txt 에 고정하지 않았다. 멤버 표현이 바뀐 전례가 있어 실사용 전에 핀을 박을지 정해야 한다.",
          ]}
        />
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
