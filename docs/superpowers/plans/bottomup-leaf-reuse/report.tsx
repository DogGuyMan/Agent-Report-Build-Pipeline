import { readFileSync } from "node:fs";
import {
  Page, Section, DecisionTable, OptionTable, LockTable, NewStructNote,
  EvidenceNote, BeforeAfter, VerdictFooter, Glossary, TermGraph,
} from "report-builder";
import { inlineSvg } from "report-builder/svg";
import { data } from "./data.js";

export { data };

const before = inlineSvg(readFileSync("before.svg", "utf8"), "blrbefore");
const after = inlineSvg(readFileSync("after.svg", "utf8"), "blrafter");

export default function Report() {
  return (
    <Page data={data}>
      <Section title="용어집 — Mode 1.5 실측 (확실 4 · 모름 12 · 미측정 11)">
        <Glossary terms={data.terms ?? []} />
      </Section>

      <Section title="용어 관계도">
        <TermGraph terms={data.terms ?? []} />
      </Section>

      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>

      <Section title="구조가 어떻게 바뀌는가">
        <BeforeAfter
          id="blr"
          before={{ title: "지금(R6) — 프롬프트 78개가 t0 에 얼고, 세션이 id 를 베끼고, 병합은 고치지 않는다", diagram: before }}
          after={{ title: "제안 — 의존 파일이 끝난 것만 투입하고 투입 순간 조립, 병합이 id 를 이름으로 고치고 모르는 것은 떼어 기록", diagram: after }}
          legend={[
            { color: "#d9534f", label: "끊김 — 오늘 실측으로 확인된 결함" },
            { color: "#6aa06f", label: "새로 생기는 것" },
            { color: "#8fa4d4", label: "기계 계산 · 병합" },
            { color: "#9a7fd4", label: "LLM 세션" },
            { color: "#d2a03c", label: "산출물" },
          ]}
        />
      </Section>

      <Section title="근거 — 무엇을 재서 알았고 무엇이 판단인가">
        <EvidenceNote
          measured={[
            "runner/mode1/survey_files.py:135-141 이 78개 프롬프트를 시작 때 전부 제출한다. 첫 완료 로그가 '돌고 있는 것 77' 이었다 — 병합 0개 시점에 조립됐다.",
            "F03(machine/normalize.py)은 시작 7분 뒤 끝났고 F75(machine/test_normalize.py)는 거의 마지막에 돌았는데, F75 레코드의 uses.to 와 shallow 가 C218 · C380 이다 — 20분 넘게 있던 normalize_python 레코드를 못 받았다.",
            "F75 의 '열지 마라' 목록에 자기 파일의 _griffe_dump 가 들어 있었다 — pending_excerpt 가 같은 배치 심볼을 빼지 않는다.",
            "verify-terms 실패 533건의 분류 — 노드 id 94 · 짧은 이름 179 · 모듈 접두 틀림 79 · stdlib/서드파티 181. 커밋된 옛 층 전략 레코드(09-08)에도 unknown uses.to 488건(id 377)이 있다 — 두 전략 공통이다.",
            "HANDOFF-2026-09-07-codegraph-id-namespace.md 가 같은 결함을 12일 전에 적었다 — dep_excerpt 적중 0/895, C-id 375/490. 09-19 수정(f5abefc)은 그 문서의 갈래 B 만 했고 갈래 A(프롬프트가 이름을 준다)는 착수되지 않았다.",
            "오늘 codegraph.json 의 파일 의존 그래프 — 파일 78 · 파일 간 간선 56 · 순환 0 · 임계 경로 5 · 잎 파일 40. 준비 집합으로 기다려도 동시 8 기준 물결 10 → 11.",
            "shallow 레코드 376개 중 피의존수 > 0 은 12개. 2패스는 그중 10개(F06 · F13)를 다듬었고 나머지 2개는 의존 이름이 id 라 unknown 으로 탈락했다.",
            "unresolved.csv — resolved 413 · unknown 94 · shallow 0. resolved 413 은 '끝났을 때는 의존 대상이 있었는데 시작할 때 프롬프트가 몰랐던' 자리다.",
            "Mode 1.5 실측(이 보고서의 용어집) — 계획의 새 장치 셋(준비 집합 스케줄러 · 강제 투입 · normalize_records)과 그것이 고치는 셋(dep_excerpt · pending_excerpt · name_of)이 전부 모름.",
          ]}
          judged={[
            "💭 '통독 중복이 비용의 주범' 은 반만 맞았다 — 세션당 캐시 쓰기가 층 0 93K vs 파일 84K 로 거의 같다. 파일 전략의 -20% 는 세션 수(116 → 79)에서 왔다. 이 계획은 비용이 아니라 재사용의 성립을 겨눈다.",
            "💭 준비 집합의 벽시계 대가는 이 저장소에서 한 물결이지만, 파일 간 순환이 많은 저장소에서는 강제 투입이 자주 일어나 shallow/2패스가 다시 주역이 된다 — 그 경우의 측정은 없다.",
            "💭 D2 의 '짧은 이름은 고치지 않는다' 로 258건이 떼여 나가는데, 프롬프트 계약(D3)이 그 수를 줄일지는 실행해 보기 전엔 모른다. 남으면 dropped-uses.csv 에서 본다.",
            "💭 verify-terms 의 다음 걸림돌은 where 줄 번호 틀림 5건 · 파일 없음 3건이다 — 이 계획 밖이고, 그 8건이 exit 1 을 내면 파이프라인은 여전히 멈춘다.",
          ]}
        />
      </Section>

      <Section title="신규 구조물 신고">
        <NewStructNote
          kind="병합 보정 한 벌 — normalize_records + dropped_csv + refresh_merged (AnnotateSymbolsStage 의 메서드), 파일 전략의 dep_files + 준비 집합 refill"
          implementers={1}
          consumers={2}
          deletionTest="refresh_merged 를 지우면 층 전략 harvest 와 파일 전략 write_merged 가 각자 병합·쓰기를 다시 갖게 되고, 보정이 한쪽에만 붙는 어긋남이 생긴다. dep_files 를 지우면 준비 집합이 재료를 잃어 t0 전량 제출로 되돌아간다."
          grepEvidence="merge_shards 를 부르는 곳 — survey.py harvest · survey_files.py write_merged · 초기 병합 2곳 (소비자 2 이상 → 메서드로 올린다는 규약에 맞다) · dep_files 소비자는 AnnotateFilesStage 하나 → staticmethod"
        />
      </Section>

      <Section title="정본 대조 — 이 저장소가 이미 못 박은 것들과 어긋나는가">
        <LockTable
          rows={[
            { lockId: "계산은 단계에 종속", claim: "자유 함수 모음을 만들지 않는다. 소비자 1 → staticmethod, 2 이상 → 공유 메서드",
              verdict: "consistent", note: "normalize_records · dropped_csv · refresh_merged 는 AnnotateSymbolsStage 안. dep_files 는 AnnotateFilesStage 의 staticmethod" },
            { lockId: "사용자 결정 2026-09-20", claim: "의존 파일이 끝난 뒤 투입 · 외부 의존은 떼어 기록 · 보정은 id 만",
              verdict: "consistent", note: "D0 · D1 · D2 가 그 셋을 그대로 옮긴 것이다. 세 결정의 근거는 사용자 선택이지 실측이 아니다" },
            { lockId: "혼자 정하지 말 것", claim: "정책 성격의 결정은 사용자에게 표로 올린다",
              verdict: "consistent", note: "외부 의존 처리 · 이름 보정 범위 · 스케줄 방식 셋을 표로 물어 정했다(AskUserQuestion)" },
            { lockId: "09-07 인계 문서 갈래표", claim: "A 프롬프트가 이름을 준다 · B 조회 때 푼다 · C where 로 잇는다",
              verdict: "consistent", note: "D3 = A, 09-19 f5abefc = B. C 는 채택하지 않았다 — 줄 드리프트라는 새 실패 축을 들이므로" },
            { lockId: "927684f (08-31) 헤드리스 출제 제거", claim: "실행기에 헤드리스 LLM 출제 칸을 두지 않는다",
              verdict: "unrelated", note: "이 계획은 Mode 1 조사 세션만 건드린다. Mode 1.5 --ask 는 별개 커밋(1339d1f)" },
            { lockId: "코드 주석은 현 상황만", claim: "주석에 날짜·수치·번복 서사를 남기지 않는다",
              verdict: "consistent", note: "계획의 독스트링 초안은 형식·동작 사실만 적었다. 실측 수치는 이 보고서와 docs/ 에 있다" },
            { lockId: "커밋 규약", claim: "[tag] : 제목 한 줄, 본문·트레일러 없음, ASCII 구두점",
              verdict: "consistent", note: "계획의 커밋 메시지 6개를 그 꼴로 고쳐 두었다" },
            { lockId: "컴포넌트는 추가만", claim: "viz/src 컴포넌트의 props 를 지우거나 뜻을 바꾸지 않는다",
              verdict: "unrelated", note: "runner/mode1 만 건드린다" },
            { lockId: "0004 D축 보류 · <script> 1개", claim: "D축 필드 · 산출물 스크립트 예산",
              verdict: "unrelated", note: "보고서 산출물과 무관한 러너 변경이다" },
          ]}
        />
      </Section>

      <Section title="D0 · 의존 파일이 전부 병합된 뒤 투입한다">
        <OptionTable
          columns={["안", "무엇", "벽시계 · 재사용", "판정 · 출처"]}
          rows={[
            { cells: ["준비 집합 (Kahn 식)", "의존 파일이 전부 끝난 파일만 풀에. 프롬프트는 투입 순간 조립", "물결 10 → 11 (실측 그래프) · dep_excerpt 항상 차 있다", "채택 (D0) — 사용자 선택 2026-09-20"], recommended: true },
            { cells: ["즉시 투입 + 프롬프트만 늦게 조립", "지금처럼 가중치 순으로 바로 넣고, 워커가 집는 순간의 병합본으로 조립", "물결 10 · 이미 끝난 의존만 재활용, 나머지는 shallow → 2패스", "기각 — 재활용이 부분적. 사용자가 '완벽히' 를 목적으로 정했다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D1 · 외부 의존은 적지 않게 하고, 적힌 것은 떼어 기록한다">
        <OptionTable
          columns={["안", "무엇", "대가", "판정 · 출처"]}
          rows={[
            { cells: ["프롬프트 금지 + 기계가 떼어 기록", "uses[].to 는 저장소 안 레코드 키만. 병합이 모르는 to 를 떼고 dropped-uses.csv 에 남긴다", "외부 의존 정보가 사전에서 빠진다(CSV 에만 남음)", "채택 (D1) — 사용자 선택"], recommended: true },
            { cells: ["external 레코드로 살린다", "stdlib 심볼마다 kind=external 레코드를 기계가 만들어 사전에 넣는다", "사전이 수백 개 커지고 뜻은 비어 있다", "기각 — 사용자 선택 밖"], recommended: false },
            { cells: ["verify-terms 를 관대하게", "to 가 사전에 없어도 실패로 세지 않는다", "검문의 뜻이 약해진다 — id·짧은 이름 오류도 함께 통과한다", "기각 — 사용자 선택 밖"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D2 · 보정은 노드 id 만 이름으로 고친다">
        <OptionTable
          columns={["안", "무엇", "오늘 데이터에서", "판정 · 출처"]}
          rows={[
            { cells: ["id 만", "C218 → machine.normalize.normalize_python 처럼 코드 지도로 100% 확정되는 것만", "고침 94 · 떼기 439", "채택 (D2) — 사용자 선택"], recommended: true },
            { cells: ["id + 유일한 짧은 이름", "GraphNode → machine.facts.GraphNode 처럼 접미가 유일할 때도 고친다", "고침 약 264 · 떼기 약 269 · 오탐 위험 > 0", "기각 — 사용자 선택 밖. 남는 것은 dropped-uses.csv 에서 본다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D3 · 프롬프트가 id 대신 이름을 보인다 — 09-07 인계의 갈래 A">
        <OptionTable
          columns={["안", "무엇", "장점 · 대가", "판정 · 출처"]}
          rows={[
            { cells: ["A. 프롬프트에서 이름을 준다", "의존 -> C218 을 의존 -> machine.normalize.normalize_python 으로. 계약에 '레코드 키 그대로' 명시", "새 레코드가 깨끗해진다 · 이미 쌓인 id 는 그대로", "채택 (D3) — 이 계획"], recommended: true },
            { cells: ["B. 조회할 때 푼다", "dep_excerpt · 병합이 id 를 코드 지도로 풀고 나서 찾는다", "옛 레코드까지 살아난다 · 이름공간 둘을 영구히 떠안는다", "채택됨 (09-19 f5abefc · D2 의 보정) — A 와 함께 간다"], recommended: false },
            { cells: ["C. where 로 잇는다", "노드의 파일:줄과 레코드의 where 를 맞춘다", "키를 무엇으로 정하든 무관 · 줄이 밀리면 어긋난다", "기각 — 인계 문서의 💭 판단대로, 새 실패 축을 들인다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D4 · pending_excerpt 는 자기 배치의 심볼을 뺀다">
        <EvidenceNote
          measured={[
            "F75(machine/test_normalize.py) 프롬프트의 '열지 마라' 목록에 같은 파일의 _griffe_dump 가 있었고, 레코드의 shallow 에 C380(_griffe_dump 의 id)이 적혔다.",
            "고치는 자리는 runner/mode1/survey.py pending_excerpt 한 줄 — 배치 심볼 id 집합을 빼고 정렬한다.",
          ]}
          judged={["💭 대안이 없어 옵션표가 없다 — 지금 읽는 파일을 '열지 마라' 고 하는 것은 어느 해석으로도 맞지 않다."]}
        />
      </Section>

      <Section title="D5 · 층·파일 전략이 같은 refresh_merged 를 부른다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["공유 메서드 하나", "병합 → 보정 → terms-reading.json · dropped-uses.csv 쓰기를 refresh_merged 에 모으고 harvest 와 파일 세션 끝이 부른다", "채택 (D5) — 병합의 정의가 한 곳. 소비자 2 이상이라 메서드로 올리는 규약과 맞다"], recommended: true },
            { cells: ["각 전략이 자기 병합을 쓴다", "harvest 와 write_merged 가 각자 merge_shards 뒤에 보정을 붙인다", "기각 — 같은 여섯 줄이 두 곳에 생기고 한쪽만 고쳐질 위험"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D6 · 실패한 파일도 done 으로 센다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["실패해도 done", "격리·실패한 파일도 done_files 에 넣는다. 의존하는 쪽은 pending 절을 받아 shallow 로 쓴다", "채택 (D6) — 한 파일의 실패가 그 위 전부를 영원히 막지 않는다. 미검토 — 이 계획이 추가"], recommended: true },
            { cells: ["실패하면 의존하는 쪽을 보류", "그 파일이 --resume 으로 다시 성공할 때까지 위 파일들을 투입하지 않는다", "기각 — 한 실행 안에서는 재시도가 없어 교착이 된다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D7 · 순환이면 남은 의존이 가장 적은 파일을 강제 투입한다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["남은 의존 최소, 같으면 계획 순", "준비된 것도 도는 것도 없을 때만. 그 세션만 미조사 절 → shallow → 2패스", "채택 (D7) — 이 저장소는 순환 0 이라 오늘은 안 쓰인다. 미검토 — 순환 있는 저장소 실측 없음"], recommended: true },
            { cells: ["가중치 최대", "순환 안에서 가중치가 가장 큰 파일을 먼저", "기각 — 남은 의존이 많은 파일을 먼저 넣으면 shallow 가 늘어난다"], recommended: false },
          ]}
        />
      </Section>

      <VerdictFooter />
    </Page>
  );
}
