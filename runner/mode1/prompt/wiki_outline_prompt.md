    """목차 한 세션. 이미 있으면 세션 없이 OK — 산출물이 있으면 계약은 지켜진 것이다.

    `SKIP` 은 "산출물 없이 다음으로" 라는 뜻이라 여기에 맞지 않는다. `SKIP` 으로 내면
    시뮬레이터가 `write-wiki` 의 읽기(`outline.json`)를 보장하지 못해 그래프를 거부한다.
    """
    name = "outline-wiki"

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return self.wiki_catalogue_prompt(ctx.repo, ctx.root)

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE]

    @staticmethod
    def wiki_catalogue_prompt(repo: str, root: str) -> str:
        """페이지 목록과 **각 페이지가 인용할 심볼**을 먼저 받는다.

        K6 의 층을 매기려면 이 둘이 있어야 하는데, 위키 페이지는 심볼도 모듈도 아닌 **주제**
        단위라 기계가 결정론으로 못 만든다. 그래서 이 한 세션만 먼저 돈다.
        """
        return """\
너는 코드베이스 위키의 **목차 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

**산문을 쓰지 마라.** 이 세션이 낼 것은 목차 파일 하나뿐이다. 각 장은 다음 세션들이 쓴다.

## 재료 — 이미 다 있다. 다시 만들지 마라

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/ranking.json     모듈 중요도(PageRank · hotspot)
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/batches.json 심볼의 의존 층

## 할 일

`/deep-wiki:catalogue` 의 규정을 따라 주제 카탈로그를 짠다 —
Getting Started / Deep Dive 계열, 최대 4단, 절당 자식 8장 이하.
장 수는 모듈 수에 맞춘다. `ranking.json` 상위 모듈부터.

낼 것은 이 파일 하나다:

  {repo}/out/codegraph-raw/outline.json

  {{"pages": [
    {{"file": "index.md", "title": "이 저장소는 무엇인가", "symbols": []}},
    {{"file": "protocol.md", "title": "프로토콜", "symbols": ["encode", "decode"]}}
  ]}}

- `file` 은 하위 폴더 없는 평평한 이름이다. **`index.md` 를 반드시 넣는다.**
- `symbols` 는 그 장이 **본문에서 다룰** 용어 키다. `terms-db.json` 에 **실제로 있는 키만** 적는다.
  지어낸 이름은 넣지 않는다 — 기계가 이 목록으로 장의 집필 순서를 정한다.
- 개괄만 하는 장은 `symbols` 를 빈 배열로 둔다. 그 장이 맨 먼저 쓰인다.

**마크다운 페이지를 만들지 마라. 커밋하지 마라.**

보고: 장 수 · 장마다 인용 심볼 수 · terms-db 에 없어서 뺀 이름.
""".format(repo=repo, root=root)

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if os.path.exists(X.OUTLINE.locate(ctx)):
            row = self.row(t0, True, "목차가 이미 있다")
            row["skipped"] = True
            return P.Outcome(P.OK, "", [row])
        return super().perform(ctx)


class WriteWikiStage(Measured, P.LlmStage[Mode1Context]):
    """장들을 층 오름차순 병렬로. 이미 쓴 장은 건너뛴다."""
    name = "write-wiki"

    def repo(self, ctx: Mode1Context) -> str:
        return ctx.repo

    def prompt(self, ctx: Mode1Context) -> str:
        return ""

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.OUTLINE, X.BATCHES]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        # 장들은 LLM 자식 프로세스가 쓴다. "돌고 나면 있어야 한다" 는 선언이지 누가 쓰는가가 아니다 —
        # 이것이 없으면 시뮬레이터가 `publish-wiki` 의 읽기(`docs/wiki`)를 보장 못 해 그래프를 거부한다.
        return [X.WIKI_DIR]

    @staticmethod
    def symbol_layers(plan: survey_plan.SurveyPlan) -> dict[str, int]:
        """`batches.json` -> `{심볼 id: 층}`. 비노드 층은 심볼이 없으므로 저절로 빠진다."""
        return {s["id"]: L["level"]
                for L in plan.get("layers", [])
                for b in L.get("batches", [])
                for s in b.get("symbols", [])}

    @staticmethod
    def page_layers(pages: Iterable[WikiPage], sym_layer: Mapping[str, int]) -> dict[str, int]:
        """K6 — 페이지의 층 = 그 페이지가 인용하는 심볼들의 **최대** 층.

        아는 심볼이 하나도 없으면 층0 이다 — `index.md` 처럼 개괄만 있는 장이 여기 온다.
        `sym_layer` 에 없는 이름은 세지 않으므로, 카탈로그가 지어낸 이름 하나로 페이지가
        맨 뒤로 밀리지 않는다.
        """
        out: dict[str, int] = {}
        for p in pages:
            known = [sym_layer[s] for s in p.get("symbols", []) if s in sym_layer]
            out[p["file"]] = max(known) if known else 0
        return out

    @staticmethod
    def wiki_page_prompt(repo: str, root: str, page: WikiPage, lower_pages: str) -> str:
        """장 하나 = 세션 하나. `lower_pages` 는 이미 선 아래층 장들의 파일명과 제목이다."""
        return """\
너는 코드베이스 위키의 **{fname} 담당**이다. 대상 저장소 {repo}. 도구 저장소 {root}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 네가 쓸 장 하나

  제목   {title}
  파일   {repo}/docs/wiki/{fname}
  다룰 것 {syms}

**이 한 장만 쓴다.** 다른 장을 만들지 않는다.

## 이미 선 장들 — 재설명하지 말고 링크한다

{lower}

## 재료

  {repo}/out/codegraph-raw/terms-db.json    용어 사전. **인용 검사를 통과한** 레코드다
  {repo}/out/codegraph-raw/facts/*.md       모듈 · 클래스 · 외부 의존 · 진입점 표
  {repo}/out/codegraph-raw/modules.svg      모듈 관계도(큰 그림)

## 규정

`/deep-wiki:page` 의 규정(3단계 절차 · Mermaid · 인용 규격 · 미확인 영역 표기)을 따르되
**사이트 조립은 하지 마라** — 그건 이 도구의 `report-wiki build` 가 한다. 평평한 마크다운만 쓴다.

- **인용은 로컬 규격 `(경로:줄)`** 로 쓴다. 저장소 뿌리 기준 상대 경로다. 기계가 대조한다
- Mermaid 는 소형만(노드 10개 이하). 큰 그림은 `out/codegraph-raw/modules.svg` 를 가리킨다
- 확인 못 한 것은 `(Unknown - verify in <파일>)` 로 남긴다. 지어내지 않는다
- 읽는 사람은 배경 지식이 없다고 가정한다(객체지향을 갓 배운 대학 1학년 눈높이)
- 한국어로 쓰고 영문 기술용어를 병기한다. 약어와 압축 표현을 피한다
- **네가 서브에이전트를 띄운다면 Sonnet 5 계열로 띄운다.** deep-wiki 의 것들은 이미 그렇게 돼 있다

**대상 저장소의 소스는 읽기만 한다. 쓰는 곳은 위 파일 하나뿐이다. 커밋하지 마라.**

보고: 줄 수 · 인용 수 · Mermaid 수 · Unknown 으로 남긴 자리.