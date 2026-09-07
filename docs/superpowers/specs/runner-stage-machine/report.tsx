import { readFileSync } from "node:fs";
import {
  Page, Section, DecisionTable, OptionTable, LockTable, NewStructNote,
  EvidenceNote, BeforeAfter, VerdictFooter, Glossary, TermGraph,
} from "report-builder";
import { inlineSvg } from "report-builder/svg";
import { data } from "./data.js";

export { data };

const before = inlineSvg(readFileSync("before.svg", "utf8"), "rsmbefore");
const after = inlineSvg(readFileSync("after.svg", "utf8"), "rsmafter");

export default function Report() {
  return (
    <Page data={data}>
      <Section title="용어집">
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
          id="rsm"
          before={{ title: "지금 — 같은 루프가 세 벌, 재는 코드는 run_mode1.py 에 얹혀 있다", diagram: before }}
          after={{ title: "제안 — 공통축 한 벌 + 모드마다 전이표 하나", diagram: after }}
          legend={[
            { color: "#d2a03c", label: "중복된 것 / 모드별 데이터" },
            { color: "#d9534f", label: "결함 — import 부작용, 형 없는 값" },
            { color: "#8fa4d4", label: "재는 코드 · 형과 검증" },
            { color: "#6aa06f", label: "새로 생기는 공통축" },
            { color: "#9a7fd4", label: "모형을 부르는 자리" },
          ]}
        />
      </Section>

      <Section title="근거 — 무엇을 재서 알았고 무엇이 판단인가">
        <EvidenceNote
          measured={[
            "같은 단계 루프가 세 벌이다 — run_mode1.main · run_mode1_5.main · run_mode2.main. plan_stages 도 세 벌, is_agent_stage 도 세 벌이다.",
            "기계 단계의 토큰 0(normalize_usage(None))을 사람이 아홉 군데에 손으로 적는다.",
            "시스템 파이썬으로 run_mode2 를 import 하면 os.execv 가 해석기를 .venv 로 갈아치우고 networkx 가 실린다. Mode 2 는 둘 다 쓰지 않는다.",
            "단계 사이를 건너다니는 지역 변수가 다섯이다 — targets · entries · warmup_cache · tracked_n · plan_json.",
            "run_survey 와 run_wiki 의 반환형이 list[StageRow] 다. 한 단계가 측정 행을 여러 개 낸다.",
            "run_mode1.main 이 층 계획을 cast 로 받으며 주석에 \"기계가 꼴을 확인할 수 없다\" 고 적어 두었다.",
            "pyright strict 는 명시적 Any 를 잡지 못한다. 탐침으로 확인했다 — Any 로 받은 값에 없는 열쇠와 없는 메서드를 붙여도 오류 0건이다.",
            "설정에 reportExplicitAny 와 reportAny 를 넣어도 pyright 1.1.413 은 무시한다. 오류 수가 5로 그대로였다. 그 둘은 basedpyright 의 규칙이다.",
            "같은 코드를 object 로 받으면 검사기가 잡는다 — reportIndexIssue. 그리고 Any 를 한 개도 쓰지 않고 pyright strict 0 오류가 되는 모양을 실제로 짜서 통과시켰다.",
            "러너의 Any 는 24곳이다 — run_mode1_5.py 20 · run_mode1.py 4. run_mode2.py 와 run_grade.py 는 이미 0이다.",
            "시험 네 파일(2,011줄)이 모듈 최상위 이름을 약 200회 참조한다. plan_stages 만 29회다.",
          ]}
          judged={[
            "💭 Fall-Back 과 Cascade 는 아직 코드에 없다. 이 제안은 그 확장을 미리 짓는 것이고, 근거는 실측이 아니라 사용자가 밝힌 확장 의도다. D4 가 유일한 첫 소비자다.",
            "💭 전이표를 밖에 두면 단계만 읽어서는 다음이 어딘지 모른다. 흐름 전체가 한 화면에 모이는 대신 두 곳을 봐야 한다.",
            "💭 D7(모듈 경계)은 셋 다 동작하므로 옳고 그름이 아니라 탐색 비용의 문제다.",
          ]}
        />
      </Section>

      <Section title="신규 구조물 신고">
        <NewStructNote
          kind="공통 파이프라인 계층 — abstractstage 계층 + 전이표 + Artifact 경계 검증"
          implementers={3}
          consumers={3}
          deletionTest="지우면 위 표의 중복(루프 3벌 · plan_stages 3벌 · 토큰 0 아홉 곳)이 그대로 되살아난다. 지금이 바로 그 상태다."
          grepEvidence="grep -rn 'for stage in stages' runner → 3건 · grep -c 'normalize_usage(None)' → 7+1+1 · 시험의 최상위 이름 참조 약 200회"
        />
      </Section>

      <Section title="정본 대조 — 이 저장소가 이미 못 박은 것들과 어긋나는가">
        <LockTable
          rows={[
            { lockId: "확정된 스택", claim: "esbuild · React renderToStaticMarkup · tsc --noEmit · 파이썬 문자열 조립",
              verdict: "unrelated", note: "이 제안은 runner/ 만 건드린다. viz/ 의 스택을 손대지 않는다" },
            { lockId: "산출물 <script> 1개", claim: "빌드된 report.html 의 script 태그는 1개를 넘지 않는다",
              verdict: "unrelated", note: "러너 리팩터링이라 산출물 예산과 무관하다" },
            { lockId: "0004 D축 보류", claim: "viz/src/types.ts 에 D축 필드를 넣지 않는다",
              verdict: "unrelated", note: "D축을 건드리지 않는다" },
            { lockId: "0006 빈 옵션표", claim: "🟡 결정에 없는 대안을 지어내지 않고 보고만 한다",
              verdict: "consistent", note: "옵션이 실제로 둘 이상인 결정에만 옵션표를 붙였다" },
            { lockId: "runner Owns", claim: "machine/*.py 와 viz/* 는 부르기만 하고 고치지 않는다",
              verdict: "consistent", note: "D10 이 스키마를 새로 만들지 않고 machine/ 의 TypedDict 를 가져다 쓴다" },
            { lockId: "직접 실행 가드", claim: ".py 는 if __name__ == \"__main__\": sys.exit(main()) 을 둔다",
              verdict: "consistent", note: "새로 쪼개는 모듈에도 그대로 적용한다" },
            { lockId: "거울 함정", claim: "구현자 1 · 소비자 1이면 인터페이스를 만들지 마라",
              verdict: "consistent", note: "구현자 3 · 소비자 3이라 문턱을 넘는다. 다만 계층 상태·가드 함수·플러그인 등록기는 범위 밖으로 명시해 두었다" },
          ]}
        />
      </Section>

      <Section title="D0 · 공통축은 Stage 기반 클래스 + 교체 가능한 착지점">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["데이터 주도 드라이버", "StageSpec 목록 + drive() 루프. 상속 0", "기각 — 사용자가 상속 기반을 원했다"], recommended: false },
            { cells: ["재는 코드만 분리", "measure 모듈만 빼고 루프는 세 곳에 그대로", "기각 — 개방-폐쇄 원칙을 못 만족한다"], recommended: false },
            { cells: ["추상 기반 클래스 + 착지점", "abstractstage 계층. 흐름은 자료로 교체", "채택 (D0) — 사용자 선택"], recommended: true },
            { cells: ["명시적 State/Transition 그래프", "State 객체 + guard 함수를 가진 진짜 상태 기계", "기각 — 분기하는 guard 가 지금 하나도 없다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D1 · 전이표는 파이프라인 밖에 하나">
        <OptionTable
          columns={["안", "착지점을 어디에 적는가", "판정 · 출처"]}
          rows={[
            { cells: ["단계가 기본값, 파이프라인이 덮어쓰기", "단계 옆에 적고 조립할 때 인자로 바꾼다", "기각 — 사용자 선택 밖"], recommended: false },
            { cells: ["Outcome 이 착지점을 들고 온다", "단계 본문이 그때그때 정한다", "기각 — 바꾸려면 단계 본문을 고쳐야 한다"], recommended: false },
            { cells: ["파이프라인 밖 전이표 하나", "(단계, 갈래) → 목적지 를 표 한 곳에", "채택 (D1) — 사용자 선택"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D2 · Stage 는 상태를 갖지 않는다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["curtransition 을 멤버 변수로", "원본 pseudo code 가 그렇게 적었다", "기각 — 전수조사 단계는 층마다 다시 돌아 앞 층 값이 남는다"], recommended: false },
            { cells: ["Outcome 반환값으로", "낼 수 있는 갈래의 집합만 클래스에 선언한다", "권고 — 그 선언으로 전이표 완결성을 시작 전에 검사할 수 있다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D3 · llmstage 의 가상 훅은 셋">
        <OptionTable
          columns={["안", "가상 훅", "판정 · 출처"]}
          rows={[
            { cells: ["프롬프트 훅 하나", "getabstract_llm_prompt() → 문자열", "기각 — 원본 pseudo code 의 안. 세 LLM 단계가 호출 횟수·병렬·거두기까지 다르다"], recommended: false },
            { cells: ["훅 셋", "rounds · jobs · harvest", "권고 — 층별 병렬 실행 코드가 한 벌만 남는다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D4 · lang-select 를 두 단계로 쪼갠다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["두 단계로 쪼갠다", "lang-propose(모형) → lang-decide(기계 판정)", "채택 (D4) — 사용자 선택. 폴백이 전이표 한 줄로 드러난다"], recommended: true },
            { cells: ["한 단계로 두고 harvest 안에서 검사기를 부른다", "지금 구조 그대로", "기각 — \"모형만 부르는 단계\" 라는 불변식이 깨진다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D5 · 단계 사이의 값은 형이 붙은 Context 로">
        <OptionTable
          columns={["안", "값을 어디에 두는가", "판정 · 출처"]}
          rows={[
            { cells: ["단계의 멤버 변수", "각 단계가 들고 있는다", "기각 — 단계끼리 서로를 알게 된다"], recommended: false },
            { cells: ["모듈 전역", "지금의 지역 변수를 모듈 수준으로", "기각 — 시험이 격리되지 않는다"], recommended: false },
            { cells: ["무엇이든 담는 자루(dict)", "bag: dict[str, Any]", "기각 — 꺼낼 때마다 cast 가 붙어 형 검사를 켜 둔 채로 끈다"], recommended: false },
            { cells: ["칸마다 이름과 형이 있는 dataclass", "모드마다 자기 Context. 형 인자는 하나", "권고 — pyright strict 가 게이트라 이것만 통과한다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D6 · pipeline.run 은 가상 함수가 아니다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["모드마다 run 을 override", "원본 pseudo code 가 그렇게 적었다", "기각 — 드라이버 루프가 다시 세 벌이 되어 없애려던 중복이 돌아온다"], recommended: false },
            { cells: ["run 은 고정, 모드는 자료만", "단계 목록과 전이표만 모드가 정한다", "권고 — 개방-폐쇄 원칙에서 고쳐지지 말아야 하는 쪽이 루프다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D7 · 모듈 경계">
        <OptionTable
          columns={["안", "모양", "대가 · 판정"]}
          rows={[
            { cells: ["A. 공통 2파일 + mode1 패키지", "measure.py · pipeline.py · mode1/{prompts,stages,layers,edges}.py", "💭 권고 — 파일 9개. 모든 파일이 400줄 아래로 내려간다"], recommended: true },
            { cells: ["B. 공통도 패키지로", "pipeline/{outcome,stage,transition,driver,measure}.py", "개념당 파일 하나지만 소비자 3에 파일 5는 거울 함정 위험"], recommended: false },
            { cells: ["C. 평면 — 패키지 없이", "runner/ 아래 mode1_prompts.py 등 형제 모듈", "import 가 가장 덜 바뀌지만 접두사가 패키지를 흉내 낸다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D8 · run_mode1.py 는 파사드로 남는다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["옛 이름을 재수출한다", "속은 쪼개고 겉은 그대로", "권고 — 시험 네 파일을 한 줄도 안 고치고 분리할 수 있다"], recommended: true },
            { cells: ["시험을 새 모듈로 옮긴다", "약 200개 참조를 전부 고친다", "미검토 — 이 보고서가 추가. 파사드를 지울 때의 되살릴 조건으로 남긴다"], recommended: false },
          ]}
        />
      </Section>

      <Section title="D9 · --only · --skip · 재개 거르기는 사전 거르기로">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["전이 갈래로 흡수", "건너뛸 단계도 전이표가 정한다", "기각 — \"돌지 않은 단계\" 와 \"돌았는데 건너뛴 단계\" 가 섞여 --dry-run 이 모호해진다"], recommended: false },
            { cells: ["루프 전 사전 거르기로 유지", "전이표는 실행 중에 생긴 갈래만 다룬다", "권고 — 다만 plan_stages 세 벌은 한 벌로 합친다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D10 · 입력·출력을 기존 TypedDict 로 못 박는다">
        <OptionTable
          columns={["안", "읽은 JSON 을 어떻게 받는가", "판정 · 출처"]}
          rows={[
            { cells: ["지금처럼 dict + .get()", "형이 없다", "기각 — 열쇠 오타가 조용히 None 이 된다"], recommended: false },
            { cells: ["cast 만 붙인다", "검사기에게 형을 선언만 한다", "기각 — 검사가 아니라서 어긋나면 엉뚱한 자리에서 터진다"], recommended: false },
            { cells: ["경계에서 얕게 검증한다", "machine/ 의 TypedDict + 최상위 열쇠 검사", "권고 — Mode 1.5 의 문항지 검사가 이미 이 깊이로 돌고 있다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="D11 · Any 를 러너에서 완전히 없앤다">
        <OptionTable
          columns={["안", "무엇", "판정 · 출처"]}
          rows={[
            { cells: ["지금대로 Any 를 허용한다", "형 없는 자리 24곳을 그대로 둔다", "기각 — 사용자 요구가 \"일절 쓰지 않도록\" 이다"], recommended: false },
            { cells: ["줄이되 바깥 경계에는 남긴다", "claude 출력과 조사 레코드만 예외로", "기각 — 모양을 못 박지 못하는 것과 검사를 끄는 것은 다른 문제다"], recommended: false },
            { cells: ["완전히 없애고 게이트로 막는다", "object + isinstance 좁히기. grep 게이트 추가", "권고 — 탐침으로 pyright strict 0 오류를 확인했다"], recommended: true },
          ]}
        />
      </Section>

      <Section title="컴포넌트 후보">
        <p>없다. 이 보고서는 기존 컴포넌트 밖으로 나가지 않았다.</p>
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
