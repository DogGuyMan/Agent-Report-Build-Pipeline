import {
  Page, Section, DecisionTable, OptionTable, LockTable,
  NewStructNote, TriageBlock, EvidenceNote, Glossary, TermGraph, VerdictFooter,
} from "report-builder";
import { data } from "./data.js";

export { data };

export default function Report() {
  return (
    <Page data={data}>

      <Section title="용어집 — 먼저 읽는다">
        <Glossary terms={data.terms ?? []} />
      </Section>

      <Section title="용어 관계도">
        <TermGraph terms={data.terms ?? []} />
      </Section>

      <Section title="먼저 볼 것">
        <TriageBlock items={[
          {
            id: "T1",
            title: "계획서가 가리키는 경로가 지금 저장소에 없다",
            why: "계획서는 codegraph/survey_plan.py · codegraph/run_mode1.py · codegraph/terms_db.py 를 고치라고 적었다. 그 디렉토리는 지금 없고 machine/survey_plan.py · runner/run_mode1.py · machine/terms_db.py 로 갈라져 있다. 착수 전에 경로와 줄 번호를 전부 다시 잡아야 한다.",
          },
          {
            id: "T2",
            title: "계획서가 집 아래 절대 경로를 그대로 적었다",
            why: "Task 7 Step 3 과 Task 8 이 /Users/ 로 시작하는 경로를 명령 안에 박아 두었다. 저장소 규약은 그 자리에 변수 이름을 쓰라고 못박고 있다. 다만 이 검사는 docs/ 아래 문서를 보지 않으므로 기계가 잡아 주지 않는다.",
          },
          {
            id: "T3",
            title: "골든 시험이 실측을 낸 저장소와 다른 저장소를 볼 수 있다",
            why: "Task 7 의 골든은 CPP_REPO 를 본다. 그 상수는 지금 GRAPHICS_REPO 환경 변수에 묶여 있고, 실측을 낸 QtVisionEdit 저장소를 가리키는 변수는 따로 있다. 어느 저장소를 볼 것인지 착수 전에 정해야 한다.",
          },
        ]} />
      </Section>

      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
        <EvidenceNote
          measured={[
            "일곱 건 모두 아직 구현되지 않았다. machine/terms_db.py 에서 resolve_target · synthesize_record · resolve_uses · EXTERNAL_PREFIXES 를 찾으면 한 건도 나오지 않는다.",
            "계획서 본문에는 D 번호가 달린 결정 표가 없다. 위 일곱 건은 계획서의 Architecture 절 · Task 본문 · 「이 계획이 하지 않는 것」 표에 흩어져 있던 판단을 이 보고서가 번호만 붙여 모은 것이다.",
          ]}
        />
      </Section>

      <Section title="D1 — 두 갈래로 고친다: 원인 제거와 사후 해석">
        <EvidenceNote
          measured={[
            "결함 1 — 계획 파일의 depends_on 이 내부 번호다. machine/survey_plan.py:223 이 간선의 도착점 번호를 그대로 담는다. 받는 쪽 runner/run_mode1.py:422-425 는 그 값으로 terms-reading.json 을 뒤진다. 그 사전의 열쇠는 이름이므로 교집합이 언제나 빈 집합이다.",
            "결함 2 — 배치 프롬프트가 내부 번호를 그대로 보여 준다. runner/run_mode1.py:442 가 의존 대상을 그대로 찍는다. 세션은 그 글자가 무엇인지 풀 방법이 없다.",
            "시험이 못 잡은 이유 — machine/test_survey_plan.py:21 의 가짜 코드 지도와 runner/test_run_mode1.py:316 의 가짜 배치가 둘 다 번호와 이름을 같은 값으로 만든다. 지어낸 데이터에서는 두 결함이 보이지 않는다.",
            "2026-08-30 QtVisionEdit 실행 기록(evals/runs/2026-08-30-mode1-qtvisionedit-cold-sonnet.json)에서 전수조사 배치 열여섯 개는 전부 성공했고 그 다음 terms 단계만 실패했다.",
          ]}
          judged={[
            "원인 제거만으로는 부족하다는 계획서의 판단에 동의한다 — 이름꼴이 다른 참조와 남의 라이브러리 참조는 프롬프트를 고쳐도 남는다. 다만 사후 해석 쪽이 더 큰 덩어리라, 이 계획을 「원인 제거」 라고 부르면 실제 무게를 잘못 전달한다.",
          ]}
        />
      </Section>

      <Section title="D2 — 의존 목록을 이름으로 낸다">
        <EvidenceNote
          measured={[
            "고칠 곳은 한 줄이다. machine/survey_plan.py:223 의 집합 표현식이 도착점 번호 대신 그 번호의 이름을 담게 바꾸면 된다. 계획서는 바로 위에 번호를 이름으로 옮기는 표를 하나 만들어 두라고 적었다.",
            "고친 뒤에도 기존 시험은 그대로 통과한다. 가짜 코드 지도가 번호와 이름을 같은 값으로 만들기 때문이다. 그래서 계획서가 번호와 이름이 다른 시험을 따로 더한다.",
            "받는 쪽은 손댈 것이 없다. runner/run_mode1.py:442 는 이미 심볼 자신은 이름으로 찍고 있다.",
          ]}
        />
      </Section>

      <Section title="D3 — 사다리 순서: 되돌리기 먼저, 합성 나중">
        <OptionTable
          columns={["안", "무슨 일이 일어나나", "잃는 것", "출처"]}
          rows={[
            {
              cells: [
                "되돌리기를 먼저 (채택)",
                "아는 심볼로 되돌릴 수 있으면 그렇게 한다. 안 되는 것만 합성한다.",
                "가리키는 정밀도. AddHandler 가 MessageRouter 로 뭉개진다.",
                "채택(D3) — 계획서 resolve_uses 본문",
              ],
              recommended: true,
            },
            {
              cells: [
                "합성을 먼저",
                "분류만 되면 새 레코드를 만든다. 되돌리기는 남은 것만 본다.",
                "뜻이 빈 레코드가 늘어난다. 용어 이해도 점검의 재료가 되지 못한다.",
                "기각 — 계획서 resolve_uses 본문이 이 이유로 물리쳤다",
              ],
              recommended: false,
            },
            {
              cells: [
                "둘 다 걸고 나중에 고른다",
                "두 결과를 다 만들어 두고 점수로 고른다.",
                "고르는 규칙이 새 결정이 된다. 함수 둘이 규칙 얹은 구조물로 자란다.",
                "미검토 — 이 보고서가 추가",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "계획서는 실측 대상 서른여섯 개에 이 순서를 손으로 적용한 결과를 표로 실었다 — 정확한 조상 2 · 짧은 이름 15 · 저장소 밖 합성 10 · 파일 합성 1 · 남음 8.",
            "그 시뮬레이션은 계획서 저자가 손으로 돌린 것이고, 이 보고서는 그것을 다시 돌려 보지 않았다.",
          ]}
          judged={[
            "「합성 레코드는 뜻이 비어 있어 다음 단계의 재료가 못 된다」 는 근거는 설득력이 있다. 다만 되돌리기가 뭉개는 정밀도의 값을 아무도 재지 않았다 — 서른여섯 개 중 열일곱 개가 뭉개진다는 뜻이므로 적은 양이 아니다.",
          ]}
        />
      </Section>

      <Section title="D4 — 짧은 이름이 둘 이상이면 포기한다">
        <OptionTable
          columns={["안", "규칙", "위험", "출처"]}
          rows={[
            {
              cells: [
                "하나로 좁혀질 때만 (채택)",
                "짧은 이름이 사전에 딱 하나일 때만 그것으로 본다.",
                "못 푸는 참조가 남는다. 그것은 근거 없음으로 흘러간다.",
                "채택(D4) — 계획서 resolve_target 본문",
              ],
              recommended: true,
            },
            {
              cells: [
                "여럿이면 첫 번째를 쓴다",
                "정렬해서 앞의 것을 고른다.",
                "틀린 화살표가 생긴다. 사전이 틀렸다는 것을 아무도 모른다.",
                "기각 — 계획서가 「틀린 간선을 만드느니 못 찾은 것이 낫다」 로 물리쳤다",
              ],
              recommended: false,
            },
            {
              cells: [
                "임베딩 유사도로 고른다",
                "이름을 벡터로 바꿔 가장 가까운 것에 붙인다.",
                "확률적 매칭이라 틀린 화살표를 만든다. 이 문제는 애초에 정확 문자열 문제다.",
                "기각 — 계획서 「이 계획이 하지 않는 것」 표",
              ],
              recommended: false,
            },
          ]}
        />
      </Section>

      <Section title="D5 — 저장소 밖 접두사 목록은 손으로만 늘린다">
        <EvidenceNote
          measured={[
            "목록은 다섯이다 — cv:: std:: Ui:: Qt:: boost::.",
            "계획서는 자동 확장을 「하지 않는 것」 표에 넣었다. 목록이 늘어난다는 것은 정적 수집기가 우리 심볼을 놓쳤다는 신호일 수 있고, 그때는 목록이 아니라 수집기를 고쳐야 한다는 근거다.",
            "레코드 스키마는 이미 저장소 밖 종류를 받는다. machine/terms_db.py:38-39 의 종류 집합에 external 이 들어 있다.",
          ]}
          judged={[
            "다섯 개로 충분한지는 아무도 재지 않았다. 실측 한 건은 Qt 와 OpenCV 를 쓰는 저장소 하나뿐이라, 다른 언어나 다른 프레임워크의 저장소에서 이 목록이 얼마나 빨리 모자라게 될지 알 수 없다. 이 결정의 확신도를 낮게 둔 이유다.",
            "「목록이 늘면 수집기를 의심하라」 는 뜻은 좋으나, 그 의심을 사람에게 전달하는 장치가 이 계획에 없다. 목록을 늘리는 사람이 주석을 읽는다는 보장에 기대고 있다.",
          ]}
        />
      </Section>

      <Section title="D6 — 못 푼 참조는 「실패」가 아니라 「근거 없음」이다">
        <OptionTable
          columns={["안", "파이프라인", "남는 흔적", "출처"]}
          rows={[
            {
              cells: [
                "근거 없음으로 격하 (채택)",
                "돈다. 다음 단계가 이어서 실행된다.",
                "검사 결과 목록에 남고, 실행 중에도 못 푼 건수와 앞 열 건을 찍는다.",
                "채택(D6) — 계획서 Task 5",
              ],
              recommended: true,
            },
            {
              cells: [
                "실패로 멈춘다 (현행)",
                "멈춘다. 2026-08-30 실행이 실제로 여기서 멈췄다.",
                "종료 코드 1 과 실패 목록.",
                "현행 — machine/terms_db.py:371",
              ],
              recommended: false,
            },
            {
              cells: [
                "못 푼 참조를 조용히 지운다",
                "돈다.",
                "없다. 사전이 조용히 얇아진다.",
                "기각 — 계획서가 「조용히 지우지 않고 목록으로 돌려준다」 로 물리쳤다",
              ],
              recommended: false,
            },
          ]}
        />
        <EvidenceNote
          measured={[
            "지금 그 자리는 machine/terms_db.py:371 한 줄이다. 계획서는 codegraph/terms_db.py:321-322 라고 적었는데, 파일이 옮겨졌고 줄도 밀렸다.",
            "격하가 실제로 효과를 내려면 실행 진입점도 함께 봐야 한다. 그 진입점은 검사 결과 중 「실패」 만 세어 종료 코드를 정한다.",
            "이 결정은 기존 시험 한 건과 정면으로 부딪친다. machine/test_terms_db.py:218 의 시험이 같은 상황을 「실패」 로 기대한다. 계획서가 그 함수를 통째로 지우라고 명시했다.",
          ]}
          judged={[
            "정책을 바꾸면서 옛 시험을 지우는 것은 옳다. 다만 지우기만 하면 「예전에는 멈췄다」 는 사실이 코드에서 사라진다. 새 시험 이름에 그 뜻이 남아 있어야 다음 사람이 되돌리지 않는다.",
          ]}
        />
      </Section>

      <Section title="D7 — 실제 저장소 레코드로 대조한다">
        <EvidenceNote
          measured={[
            "이 골든은 바깥 저장소가 없으면 건너뛴다. 저장소 규약은 그런 건너뜀을 실패가 아니라고 못박고 있다.",
            "계획서의 골든은 CPP_REPO 라는 상수를 쓴다. machine/test_terms_db.py:22 에서 그 상수는 GRAPHICS_REPO 환경 변수를 읽는다. 실측을 낸 QtVisionEdit 은 그 변수가 아니라 별도의 변수로 가리키는 저장소다.",
            "계획서는 통과 기준을 숫자로 못 박지 않고 「못 푼 것이 절반 아래로 줄었는가」 만 본다.",
          ]}
          judged={[
            "숫자를 못 박지 않은 것은 옳은 절제다. 다만 「절반」 이라는 문턱 자체도 근거가 없는 수라, 통과해도 무엇이 확인된 것인지 말하기 어렵다. 이 골든은 사다리가 도는지를 보는 장치이지 사다리가 옳은지를 보는 장치가 아니다.",
          ]}
        />
      </Section>

      <Section title="정본 대조">
        <LockTable rows={[
          {
            lockId: "L1",
            claim: "거울 함정 — 구현자 1, 소비자 1 이면 인터페이스를 만들지 않는다",
            verdict: "consistent",
            note: "계획서가 플러그인 구조와 레지스트리를 「하지 않는 것」 표에 스스로 넣었다. 순수 함수 둘과 배선 하나로 끝난다.",
          },
          {
            lockId: "L2",
            claim: "합성 데이터만으로 검증하지 말 것",
            verdict: "consistent",
            note: "D7 의 골든이 이 조항에 직접 대응한다. 결함 두 건이 지어낸 데이터를 통과했다는 자기 진단도 함께 적혀 있다.",
          },
          {
            lockId: "L3",
            claim: "성격축 셋 — 시키는 것은 runner, 계산하는 것은 machine",
            verdict: "conflicting",
            note: "계획서의 파일 표가 전부 codegraph/ 를 가리킨다. 그 디렉토리는 없다. 착수 전에 machine/ 과 runner/ 로 다시 나눠 잡아야 한다.",
          },
          {
            lockId: "L4",
            claim: "집 아래 경로를 문서·코드·커밋에 그대로 적지 않고 변수 이름을 쓴다",
            verdict: "conflicting",
            note: "Task 7 Step 3 과 Task 8 의 명령이 /Users/ 로 시작하는 경로를 그대로 적었다. 이 저장소는 공개된다.",
          },
          {
            lockId: "L5",
            claim: "파이썬이 본체이고 JavaScript 는 경계에만 남는다",
            verdict: "conflicting",
            note: "Task 8 Step 4 가 node 로 인용 검사를 돌리라고 적었다. 그 검사는 지금 test/test_docs_citations.py 이고 pytest 로 돈다.",
          },
          {
            lockId: "L6",
            claim: "커밋 메시지는 소문자 대괄호 태그와 한 줄 한국어 제목",
            verdict: "consistent",
            note: "여덟 Task 의 커밋 명령이 모두 그 꼴이다.",
          },
          {
            lockId: "L7",
            claim: "코드 주석에는 현 상황만 적는다 — 날짜 붙은 관찰과 실측 수치를 남기지 않는다",
            verdict: "conflicting",
            note: "계획서가 심는 주석 여럿이 날짜와 실측 문장을 담고 있다. 형식·동작 사실은 남기되 날짜와 수치는 빼는 쪽으로 다듬어야 한다.",
          },
        ]} />
      </Section>

      <Section title="신규 구조물 신고">
        <NewStructNote
          kind="같은 파일 안의 순수 함수 둘과 그것을 부르는 배선 함수 하나 — 새 파일·새 클래스·새 인터페이스 없음"
          implementers={1}
          consumers={1}
          deletionTest="셋을 지우면 전수조사 사전 검사가 다시 종료 코드 1 로 멈춘다. 2026-08-30 실행이 정확히 그 상태였다."
          grepEvidence="grep -n 'resolve_target|synthesize_record|resolve_uses|EXTERNAL_PREFIXES' machine/terms_db.py -> 0건 (미구현)"
        />
        <EvidenceNote
          measured={[
            "되돌리기 함수가 쓰는 짧은 이름 도우미는 이미 machine/terms_db.py:31 에서 가져와 있다. 계획서의 코드가 그대로 붙는다.",
            "합성 함수가 쓰는 파일 존재 확인 모듈도 machine/terms_db.py:24 에 이미 있다.",
            "구조 그림을 붙이지 않았다. 이 계획은 새 파일도 새 층도 만들지 않고 기존 파일 안에 함수를 더하는 변경이라, 앞뒤를 견줄 구조가 없다. 계획서 스스로 「새 파일은 만들지 않는다」 고 적었다.",
          ]}
        />
      </Section>

      <Section title="컴포넌트 후보">
        <EvidenceNote
          measured={[
            "이 보고서에서 EvidenceNote 를 여덟 번 썼다. 그중 일곱 번이 「결정 한 건 - 근거 몇 줄 - 판단 몇 줄」 이라는 같은 모양이다. 결정 절 전용 블록이 있으면 그 일곱 자리가 한 줄씩으로 줄어든다.",
            "옵션표 세 개가 모두 마지막 열을 출처(채택·기각·현행·미검토)로 쓴다. 그 열은 자유 문자열이라 표기가 흔들릴 수 있다.",
          ]}
          judged={[
            "지금 만들지 않는다. 소비자가 이 보고서 하나뿐이다. 반복 횟수만 남긴다.",
          ]}
        />
      </Section>

      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>

    </Page>
  );
}
