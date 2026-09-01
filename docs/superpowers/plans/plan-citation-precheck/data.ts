import type { ReportData, Term } from "report-builder/types";

// 용어집 — 정의는 여기 한 곳에만 있다. 본문 인라인 참조도, 관계 그래프도 이 배열에서 나온다.
// 읽는 사람은 배경 지식이 없다고 가정하고 쓴다.
// mental 은 Mode 1.5 용어 이해도 점검(terms.json)의 실측이다 — 확실 2 · 모름 15.
export const terms: Term[] = [
  { id: "citationReport", kind: "tool", mental: "모름",
    label: "citationReport",
    short: "문서 하나를 열어, 그 안에 적힌 파일 이름과 줄 번호 중 지금 저장소에 실제로는 없는 것만 골라 돌려주는 함수. 이 계획이 새로 만든다",
    body: "돌려주는 값은 두 칸짜리 꾸러미다 — 깨진 인용 목록과 깨진 경로 목록. 둘 다 비어 있으면 그 문서의 인용은 지금 저장소와 어긋난 곳이 없다는 뜻이다. 계획서와 스펙처럼 아무 자리에나 있는 문서도 검사할 수 있는 것이 contextDocs 와 다른 점이다.",
    links: ["contextDocs", "CITE", "PATH_REF", "citation_block", "L1", "L2", "verify_citations.py", "거울 함정"] },

  { id: "contextDocs", kind: "tool", mental: "모름",
    label: "contextDocs",
    short: "저장소 뿌리와 각 폴더에 놓인 길잡이 문서 아홉 개 중 실제로 있는 것만 목록으로 돌려주는 함수",
    body: "아홉 개의 이름이 함수 안에 그대로 박혀 있다. 계획서와 스펙은 그 목록에 없어서, 지금까지 기계가 인용을 봐 준 적이 한 번도 없다. 이 계획이 메우려는 구멍이 바로 이 자리다.",
    links: ["CITE", "PATH_REF"] },

  { id: "CITE", kind: "artifact", mental: "모름",
    label: "CITE",
    short: "문서 안에서 `machine/terms_db.py:497` 처럼 파일 이름 뒤에 콜론과 줄 번호가 붙은 대목을 찾아내는 글자 검색 규칙",
    body: "확장자 목록(py · ts · md 같은 것)이 규칙 안에 박혀 있어서 `3:4 로 나뉜다` 같은 평범한 문장은 걸리지 않는다. 바로 앞에 달러 기호가 붙은 것은 다른 저장소를 가리키는 약속이라 일부러 건너뛴다.",
    links: ["L1", "L2", "L3", "행동 불변"] },

  { id: "PATH_REF", kind: "artifact", mental: "모름",
    label: "PATH_REF",
    short: "줄 번호 없이 `runner/run_mode2.py` 처럼 경로만 적힌 대목을 찾아내는 글자 검색 규칙",
    body: "이 규칙을 돌리기 전에, 다른 저장소의 폴더 그림을 그려 둔 코드 상자는 먼저 걷어낸다. 다만 걷어내는 기준은 상자 첫 줄이 달러 기호로 시작하는지 하나뿐이라, 이 저장소처럼 생긴 상자는 그대로 검사 대상이 된다.",
    links: ["L1", "행동 불변"] },

  { id: "L1", kind: "concept", mental: "모름",
    label: "L1 파일 존재",
    short: "인용 판정 세 단계 중 첫째 — 인용이 가리키는 그 파일이 지금 저장소에 정말 있는가",
    links: ["L2"] },

  { id: "L2", kind: "concept", mental: "모름",
    label: "L2 줄 존재",
    short: "인용 판정 세 단계 중 둘째 — 그 파일이 그 줄 번호만큼 길기는 한가",
    links: ["L3"] },

  { id: "L3", kind: "concept", mental: "모름",
    label: "L3 이름 근접",
    short: "인용 판정 세 단계 중 셋째 — 인용한 그 이름이 정말 그 줄 언저리에 적혀 있는가",
    body: "이 계획이 만드는 citationReport 는 여기까지 가지 않는다. 첫째 단계만 본다.",
    links: ["terms_db.py"] },

  { id: "agent_prompt", kind: "tool", mental: "확실",
    label: "agent_prompt",
    short: "보고서 원고를 쓸 인공지능에게 건넬 지시문 전체를 한 덩어리 글로 조립해 주는 함수",
    body: "이 계획은 이 함수에 선택 인자 하나를 더한다. 기존 호출부는 그 인자를 주지 않으므로 예전과 똑같이 돈다.",
    links: ["terms_block", "citation_block"] },

  { id: "terms_block", kind: "artifact", mental: "모름",
    label: "terms_block",
    short: "지시문에 얹히는 선택 조각. 용어집 재료가 있을 때만 붙고, 없으면 빈 글자로 남아 아무것도 얹지 않는다",
    body: "이 계획이 새로 더하는 조각도 정확히 이 방식을 흉내 낸다 — 이미 저장소 안에 있는 본보기라 새 규칙을 만들 필요가 없다." },

  { id: "citation_block", kind: "artifact", mental: "모름",
    label: "citation_block",
    short: "이 계획이 새로 더하는 지시문 조각. 기계가 미리 찾아낸 깨진 인용과 경로 목록을 싣는다",
    body: "깨진 것이 하나도 없으면 빈 글자로 남아 지시문에 아무것도 붙지 않는다. 소음을 더하지 않으려는 장치다.",
    links: ["정본 대조표"] },

  { id: "네임스페이스 패키지", kind: "concept", mental: "모름",
    label: "네임스페이스 패키지",
    short: "파이썬에서 `__init__.py` 라는 표식 파일이 없는데도 폴더째로 가져다 쓸 수 있는 묶음. 이 저장소의 machine 폴더가 그렇다",
    links: ["평평한 import", "terms_db.py"] },

  { id: "평평한 import", kind: "concept", mental: "모름",
    label: "평평한 import",
    short: "같은 폴더 안의 파일끼리 폴더 이름을 빼고 서로를 부르는 방식. 이렇게 쓰인 파일은 그 폴더 자체가 검색 경로에 올라가 있어야 돌아간다",
    body: "이 계획이 만드는 새 파일은 표준 라이브러리만 쓰고 이웃 파일을 부르지 않으므로 이 제약에서 자유롭다. 그래서 부르는 방식이 기존 것과 달라진다.",
    links: ["terms_db.py"] },

  { id: "행동 불변", kind: "concept", mental: "모름",
    label: "행동 불변",
    short: "코드를 다른 파일로 옮기되 하는 일은 한 톨도 바꾸지 않는 것",
    body: "옮긴 뒤에 기존 시험이 이름도 개수도 그대로 통과하는 것으로 확인한다. 통과 개수가 달라졌다면 옮기는 김에 무언가를 고친 것이다." },

  { id: "정본 대조표", kind: "artifact", mental: "모름",
    label: "정본 대조표",
    short: "계획서가 말하는 내용과 지금 저장소의 실제 모습을 나란히 놓고, 어긋난 곳을 표류라고 적는 표",
    body: "이 보고서에도 그 표가 들어 있다. 계획서를 읽는 사람이 옛말과 지금 사실을 헷갈리지 않게 하는 것이 목적이다." },

  { id: "거울 함정", kind: "concept", mental: "모름",
    label: "거울 함정",
    short: "지나친 설계를 잡아내려고 만드는 도구를 정작 지나치게 설계해 버리는 실패",
    body: "이 계획이 검사 규칙을 갈아 끼우는 구조나 규칙 목록판을 두지 않고 함수 하나로 끝내는 이유다." },

  { id: "terms_db.py", kind: "tool", mental: "확실",
    label: "terms_db.py",
    short: "코드베이스에 나오는 이름들의 뜻을 한 곳에 모은 사전을 만드는 도구",
    body: "이 안에 있는 판정 함수가 인공지능이 적은 파일과 줄 번호를 세 단계로 검사한다. 이 계획은 그 짝이 보고서 쪽에는 없다는 데서 출발한다.",
    links: ["L1", "L2", "verify_citations.py"] },

  { id: "verify_citations.py", kind: "tool", mental: "모름",
    label: "verify_citations.py",
    short: "위키 산문에 적힌 인용이 진짜인지 기계로 판정하는 별개 도구",
    body: "돌아가려면 코드 지도 파일이 먼저 있어야 한다. 계획서와 스펙에는 그 재료가 없을 수 있어서, 이 계획은 그 도구와 합치지 않고 따로 둔다." },
];

export const data: ReportData = {
  builderVersion: "v1",
  slug: "plan-citation-precheck",
  specName: "계획서 인용 기계 점검 Implementation Plan",
  date: "2026-08-31",
  branch: "main",
  decisions: [
    {
      id: "D1",
      title: "인용 판정 순수 함수 7개를 시험 파일에서 machine/doc_citations.py 로 옮긴다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: "실측" },
      optionCount: 0,
    },
    {
      id: "D2",
      title: "고정 아홉 문서 밖의 markdown 을 검사하는 citationReport() 를 새로 만든다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "amber", anchor: 65 },
      optionCount: 0,
    },
    {
      id: "D3",
      title: "깨진 인용 목록을 agent_prompt 의 선택 블록으로 얹고, 0건이면 통째로 생략한다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: "실측" },
      optionCount: 0,
    },
    {
      id: "D4",
      title: "machine 폴더 대신 저장소 뿌리를 검색 경로에 넣어 새 모듈을 부른다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: "실측" },
      optionCount: 2,
    },
    {
      id: "D5",
      title: "새 정규식·플러그인 구조·검사 규칙 목록판을 만들지 않는다 — 함수 하나로 끝낸다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "green", anchor: "실측" },
      optionCount: 0,
    },
    {
      id: "D6",
      title: "범위 밖 4건을 명시적으로 배제한다",
      variant: "proposed",
      statusText: "[제안됨]",
      conf: { tier: "red", anchor: 50 },
      optionCount: 4,
    },
  ],
  terms,
};
