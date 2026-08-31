# 계획서 인용 기계 점검 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mode 2 에이전트가 원본 문서(`specs/*-design.md` · `plans/*.md`)의 `파일:줄` 인용과 경로 참조가
지금 저장소에서 실재하는지를 **스스로 grep 하지 않고** 알 수 있게 한다 — 기존 문서 인용 검사기를
재사용해 기계로 미리 판정하고, 그 결과를 에이전트 프롬프트에 실어 준다.

**Architecture:** `test/test_docs_citations.py` 안에 갇혀 있던 순수 함수(`citationsIn` · `pathRefsIn` ·
`brokenCitations` · `brokenPathRefs` 등)를 `machine/doc_citations.py` 로 옮겨 시험과 실행기 양쪽에서
재사용 가능하게 만든다(Task 1). 이어서 **임의 markdown 파일**(고정 아홉 문서 밖 — 계획서·스펙)을
검사하는 `citationReport()` 를 더한다(Task 2). `runner/run_mode2.py` 의 `agent_prompt` 가 원본 문서에
그것을 돌려 깨진 인용이 있으면 `terms_block` 과 같은 방식으로 프롬프트에 블록을 얹는다(Task 3).
**판정은 여전히 기계가 낸다 — LLM 은 그 결과를 정본 대조표에 옮겨 적을 뿐이다.**

**Tech Stack:** Python 3.14 표준 라이브러리만(`os` · `re`) · pytest. 새 정규식을 만들지 않는다 —
기존 `CITE` · `PATH_REF` 를 그대로 옮긴다.

---

## 배경 — 이 계획이 근거로 삼는 실측

🔵 이 계획을 쓰며 실제로 확인한 것:

- `machine/terms_db.py:check_terms`(321-387행)가 Mode 1 전수조사 레코드에 대해 정확히 이 일을 한다
  — LLM 이 쓴 `where`(파일:줄)만 골라 L1(파일 존재)·L2(줄 존재)·L3(그 이름이 근처에 있나)로 기계
  판정한다. **Mode 2 에는 이 짝이 없다.**
- `test/test_docs_citations.py` 에 이미 같은 일을 하는 순수 함수 셋(`citationsIn` · `pathRefsIn` ·
  `brokenCitations` · `brokenPathRefs`, 7-62행)이 있지만 **시험 파일 안에 갇혀 있고**, 대상도
  `contextDocs()` 가 반환하는 고정 아홉 문서(`CLAUDE.md` 계열)뿐이다 — `docs/superpowers/plans/*.md` 는
  대상이 아니다(`docs/CLAUDE.md` 가 "여기 문서의 인용은 검사되지 않는다" 로 명시).
- `docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md` 를 Mode 2 로 실제로 돌린 세션에서
  에이전트가 `grep`·`sed` 로 8~9회 파일을 직접 열어 계획서의 옛 경로(`codegraph/*.py`)가 지금
  `machine/`+`runner/` 로 갈라졌음을 스스로 확인했다 — 검증에만 약 2분을 썼다. 이 계획은 그 2분 중
  **경로/인용 존재 판정 부분**을 기계로 옮긴다.
- `machine` 은 `__init__.py` 가 없는 네임스페이스 패키지다. `machine/terms_db.py` 같은 파일은 내부에서
  `from codegraph_types import …` 처럼 **평평한** 이름으로 서로를 부르므로 `machine/` 이 직접
  `sys.path` 에 있어야 한다(`runner/run_mode1.py:122-131`). 반면 `machine/doc_citations.py` 는
  다른 `machine/*` 모듈을 import 하지 않으므로(표준 라이브러리만 씀) **저장소 뿌리를 `sys.path` 에
  넣고 `from machine.doc_citations import …` 로 부르는 쪽이 더 안전하다** — 직접 돌려 확인했다:
  `from machine.declmap import X` 는 `ImportError: cannot import name 'X'` 로 실패한다(모듈은
  찾았다는 뜻). `from machine.terms_db import X` 는 `codegraph_types` 를 못 찾아 죽는다(내부에
  평평한 import 가 있어서다). `doc_citations.py` 는 그 문제가 없다.

---

## File Structure

| 파일 | 책임 | 이 계획에서 |
|---|---|---|
| `machine/doc_citations.py` | 신설. 인용/경로 정규식과 판정 함수 | Task 1: `test/test_docs_citations.py` 의 로직을 그대로 옮긴다(행동 불변). Task 2: `citationReport()` 를 더한다 |
| `test/test_docs_citations.py` | 회귀 | Task 1: 지역 정의를 지우고 import 로 바꾼다. 나머지 시험은 그대로 둔다 |
| `runner/run_mode2.py` | `agent_prompt` · `run_agent` · `main` | Task 3: 인용 점검 블록을 배선한다 |
| `runner/test_run_mode2.py` | 회귀 | Task 3: 새 블록 시험을 더한다 |
| `runner/CLAUDE.md` | 모듈 나침반 | Task 4: "run_mode1.py 만 machine 을 import 한다" gotcha 를 갱신한다 |

새 정규식·새 판정 규칙을 만들지 않는다 — 있는 것을 옮기고 잇는다. 플러그인 구조나 검사 규칙
레지스트리는 두지 않는다(루트 `CLAUDE.md` 의 거울 함정 경고 대상) — 함수 하나(`citationReport`)면
충분하다.

---

### Task 1: 인용 판정 함수를 `machine/doc_citations.py` 로 옮긴다

**Files:**
- Create: `machine/doc_citations.py`
- Modify: `test/test_docs_citations.py:1-62`
- Test: `test/test_docs_citations.py`

- [ ] **Step 1: 새 자리를 요구하는 실패 시험을 쓴다**

`test/test_docs_citations.py` 맨 위, 기존 함수 정의(7-62행)는 그대로 둔 채 파일 맨 아래에 임시로 더한다:

```python
def test_functions_will_live_in_machine_doc_citations():
    """이 시험은 Task 1 을 끝내면 지운다 — 이동이 끝났다는 확인용이다."""
    from machine.doc_citations import citationsIn
    assert citationsIn("`a/b.py:3` 을 보라") == [
        {"path": "a/b.py", "line": 3, "index": 1}
    ]
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest test/test_docs_citations.py -k machine_doc_citations -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'machine.doc_citations'`

- [ ] **Step 3: `machine/doc_citations.py` 를 만든다 — 기존 코드를 그대로 옮긴다**

```python
"""machine/doc_citations.py — 문서의 `파일:줄` 인용과 경로 참조가 실재하는지 기계로 판정한다.

Mode 1 의 `terms_db.check_terms` 가 전수조사 레코드에 대해 하는 L1(파일)·L2(줄)·L3(근처에
그 이름) 판정과 같은 계열이지만, 여기는 **자유 형식 산문**(CLAUDE.md · 계획서 · 스펙) 안의
인용을 본다 — codegraph 노드 대조는 하지 않는다(그건 `verify_citations.py` 의 일이다).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITE = re.compile(
    r'([A-Za-z0-9_@./+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot)):(\d+)(?:-(\d+))?'
)

PATH_REF = re.compile(
    r'(?<![A-Za-z0-9_$/@~.-])((?:\.\./)*(?:\.?[A-Za-z0-9_@+~-]+/)+[A-Za-z0-9_@.+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot|html|css|xml))(?![A-Za-z0-9])'
)


def contextDocs(root=ROOT, exists=os.path.exists):
    docs = ["CLAUDE.md", "README.md", "ARCHITECTURE.md",
            "machine/CLAUDE.md", "viz/CLAUDE.md", "viz/src/CLAUDE.md",
            "runner/CLAUDE.md", "tools/CLAUDE.md",
            "docs/CLAUDE.md"]
    return [d for d in docs if exists(os.path.join(root, d))]


def isExempt(p):
    return p.startswith("out/") or "<" in p or ">" in p


def stripExternalTrees(text):
    def repl(m):
        block = m.group(1)
        lines = block.split('\n')
        first_line = next((l for l in lines if l.strip()), "")
        if re.match(r'^\s*\$[A-Za-z_][A-Za-z0-9_]*/', first_line):
            return ""
        return m.group(0)
    return re.sub(r'```[^\n]*\n([\s\S]*?)```', repl, text)


def pathRefsIn(text):
    body = stripExternalTrees(text)
    refs = []
    for m in PATH_REF.finditer(body):
        p = m.group(1)
        if not isExempt(p):
            refs.append(p)
    return list(dict.fromkeys(refs))


def brokenPathRefs(text, docRel=".", root=ROOT, exists=os.path.exists):
    base = os.path.dirname(os.path.join(root, docRel))
    broken = []
    for p in pathRefsIn(text):
        if not exists(os.path.join(root, p)) and not exists(os.path.join(base, p)):
            broken.append(p)
    return broken


def citationsIn(text):
    out = []
    for m in CITE.finditer(text):
        if m.start() > 0 and text[m.start() - 1] == "$":
            continue
        out.append({"path": m.group(1), "line": int(m.group(2)), "index": m.start()})
    return out


def brokenCitations(text, root=ROOT, exists=os.path.exists):
    return [c for c in citationsIn(text) if not exists(os.path.join(root, c["path"]))]
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest test/test_docs_citations.py -k machine_doc_citations -v`
Expected: PASS

- [ ] **Step 5: 시험 파일을 import 로 바꾼다 — 지역 정의를 지운다**

`test/test_docs_citations.py` 의 1-62행(기존 `import` 셋 · `CITE`/`PATH_REF` · 함수 여섯 개)을
전부 지우고 이걸로 바꾼다:

```python
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from machine.doc_citations import (  # noqa: E402
    CITE, PATH_REF, contextDocs, isExempt, stripExternalTrees,
    pathRefsIn, brokenPathRefs, citationsIn, brokenCitations,
)
```

방금 Step 1 에서 파일 맨 아래에 더한 `test_functions_will_live_in_machine_doc_citations` 는 지운다
— 이동이 끝났다는 확인용이었고, 이제 나머지 시험들이 같은 것을 매번 확인한다.

- [ ] **Step 6: 전체가 그대로 통과하는지 확인한다 (행동 불변)**

Run: `.venv/bin/python -m pytest test/test_docs_citations.py -v`
Expected: 기존 12개 시험 전부 PASS — 이름과 개수가 이동 전과 같아야 한다

- [ ] **Step 7: 커밋**

```bash
git add machine/doc_citations.py test/test_docs_citations.py
git commit -m "[refactor] : 문서 인용 판정 함수를 시험 파일 밖 machine/doc_citations.py 로 옮긴다"
```

---

### Task 2: 임의 markdown 파일을 점검하는 `citationReport()` 를 더한다

`contextDocs()` 는 고정 아홉 문서만 본다. 계획서·스펙은 그 목록 밖이라 별도 진입점이 필요하다.

**Files:**
- Modify: `machine/doc_citations.py` (맨 아래에 추가)
- Test: `test/test_doc_citations_report.py` (신설)

- [ ] **Step 1: 실패 시험을 쓴다**

`test/test_doc_citations_report.py` 를 새로 만든다:

```python
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from machine.doc_citations import citationReport  # noqa: E402


def test_citation_report_flags_broken_things(tmp_path):
    """실재하지 않는 인용과 경로를 둘 다 잡는다."""
    doc = tmp_path / "plan.md"
    doc.write_text(
        "`no/such/file.py:10` 을 보라. `also/missing.ts` 도 있다.",
        encoding="utf-8",
    )
    rep = citationReport(str(doc), root=str(tmp_path))
    assert rep["broken_citations"] == ["no/such/file.py:10"]
    assert rep["broken_paths"] == ["also/missing.ts"]


def test_citation_report_is_clean_for_real_things(tmp_path):
    """실재하는 파일을 가리키면 아무것도 걸리지 않는다."""
    (tmp_path / "real.py").write_text("x = 1\n" * 5, encoding="utf-8")
    doc = tmp_path / "plan.md"
    doc.write_text("`real.py:2` 를 보라.", encoding="utf-8")
    rep = citationReport(str(doc), root=str(tmp_path))
    assert rep == {"broken_citations": [], "broken_paths": []}


def test_citation_report_resolves_paths_relative_to_the_document():
    """docs/CLAUDE.md 자신이 인용하는 상대 경로도 검사된다 — 실제 저장소로 확인한다."""
    rep = citationReport(os.path.join(ROOT, "docs", "CLAUDE.md"), root=ROOT)
    assert rep == {"broken_citations": [], "broken_paths": []}
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest test/test_doc_citations_report.py -v`
Expected: FAIL — `ImportError: cannot import name 'citationReport'`

- [ ] **Step 3: 구현한다**

`machine/doc_citations.py` 맨 아래에 더한다:

```python
def citationReport(path, root=ROOT):
    """한 markdown 파일의 인용을 기계로 판정한다.

    반환은 `{"broken_citations": [...], "broken_paths": [...]}` — 둘 다 실재하지 않는
    항목만 담는다. 전부 비어 있으면 그 문서의 인용은 지금 저장소와 어긋난 곳이 없다는 뜻이다.

    `contextDocs()` 가 보는 고정 아홉 문서 밖 — 계획서·스펙처럼 임의 위치의 markdown 도
    이 함수로 검사할 수 있다.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    doc_rel = os.path.relpath(path, root)
    broken_cites = brokenCitations(text, root=root)
    broken_paths = brokenPathRefs(text, doc_rel, root=root)
    return {
        "broken_citations": [f"{c['path']}:{c['line']}" for c in broken_cites],
        "broken_paths": broken_paths,
    }
```

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest test/test_doc_citations_report.py -v`
Expected: 3개 PASS

- [ ] **Step 5: 커밋**

```bash
git add machine/doc_citations.py test/test_doc_citations_report.py
git commit -m "[feat] : 계획서·스펙처럼 임의 위치의 markdown 인용을 점검하는 citationReport 를 더한다"
```

---

### Task 3: `run_mode2.py` 의 에이전트 프롬프트에 인용 점검 블록을 배선한다

**Files:**
- Modify: `runner/run_mode2.py:59-61` (import) · `:222-303`(`agent_prompt`) · `:310-330`(`run_agent`) · `:404-459`(`main`)
- Test: `runner/test_run_mode2.py`

- [ ] **Step 1: 실패 시험을 쓴다**

`runner/test_run_mode2.py` 의 `_prompt()` 정의(261-269행 부근) 아래에 더한다:

```python
def test_the_prompt_flags_broken_citations_from_the_spec():
    """기계가 미리 찾은 깨진 인용을 프롬프트가 그대로 보여 준다."""
    rep = {"broken_citations": ["ghost.py:9"], "broken_paths": ["old/path.ts"]}
    p = R.agent_prompt(project="/프로젝트", slug="붙임", spec_file="붙임-design.md",
                       root="/도구", citation_report=rep)
    assert "ghost.py:9" in p
    assert "old/path.ts" in p


def test_the_prompt_is_silent_when_citations_are_clean():
    """깨진 것이 없으면 점검 블록 자체를 넣지 않는다 — 소음을 더하지 않는다."""
    rep = {"broken_citations": [], "broken_paths": []}
    p = R.agent_prompt(project="/프로젝트", slug="붙임", spec_file="붙임-design.md",
                       root="/도구", citation_report=rep)
    assert "기계 점검" not in p


def test_the_prompt_defaults_to_no_citation_block_when_report_is_absent():
    """citation_report 를 안 주면(기존 호출부) 예전처럼 조용하다 — 새 인자는 선택이다."""
    p = _prompt()
    assert "기계 점검" not in p
```

- [ ] **Step 2: 실패를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -k "broken_citations or citations_are_clean or citation_block_when_report" -v`
Expected: FAIL — `TypeError: agent_prompt() got an unexpected keyword argument 'citation_report'`

- [ ] **Step 3: `agent_prompt` 시그니처와 블록을 더한다**

`runner/run_mode2.py:222-223` 을 연다. 현재:

```python
def agent_prompt(project: str, slug: str, spec_file: str, root: str,
                 terms_json: str | None = None, doc_dir: str = "specs") -> str:
```

이렇게 바꾼다:

```python
def agent_prompt(project: str, slug: str, spec_file: str, root: str,
                 terms_json: str | None = None, doc_dir: str = "specs",
                 citation_report: dict[str, list[str]] | None = None) -> str:
```

`terms_block` 을 만드는 블록(234-245행) 바로 아래에 `citation_block` 을 더한다:

```python
    citation_block = ""
    if citation_report and (citation_report["broken_citations"] or citation_report["broken_paths"]):
        items = citation_report["broken_citations"] + citation_report["broken_paths"]
        citation_block = """
## 원본 문서의 인용 — 기계 점검에서 걸린 것

기계가 `{spec_file}` 을 미리 훑어, 다음 인용·경로가 **지금 이 저장소에는 없다**는 것을
확인했다:

{items}

계획서가 옛 구조를 말하고 있다는 뜻일 수 있다. 정본 대조표에 "표류" 로 적고, 지금 실제
경로로 바로잡아 옮긴다 — 없는 파일을 그대로 인용하지 마라. 이 목록은 grep 으로 다시 확인할
필요가 없다 — 기계가 이미 확인했다.
""".format(spec_file=spec_file, items="\n".join("- `%s`" % x for x in items))
```

`return` 문의 `.format(...)` 호출(302-303행 부근)을 연다. 현재 마지막 줄:

```python
""".format(project=project, slug=slug, spec_file=spec_file, folder=folder,
           root=root, terms_block=terms_block, doc_dir=doc_dir)
```

이렇게 바꾼다:

```python
""".format(project=project, slug=slug, spec_file=spec_file, folder=folder,
           root=root, terms_block=terms_block, citation_block=citation_block,
           doc_dir=doc_dir)
```

그리고 프롬프트 본문(247행부터 시작하는 삼중따옴표 문자열) 안에서 `{terms_block}` 이 나오는
자리를 `{terms_block}{citation_block}` 으로 바꾼다 — 두 선택 블록을 나란히 얹는다.

- [ ] **Step 4: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -v`
Expected: 전부 PASS

- [ ] **Step 5: `run_agent` 와 `main` 에 배선한다**

`runner/run_mode2.py:59-61` 부근(`import run_mode1 as M` 아래)에 더한다:

```python
sys.path.insert(0, ROOT)
from machine.doc_citations import citationReport  # noqa: E402
```

`run_agent` 의 시그니처(310-313행)를 연다. 현재:

```python
def run_agent(model: str, project: str, slug: str, spec_file: str, root: str,
              terms_json: str | None = None,
              timeout: float | None = None,
              doc_dir: str = "specs") -> tuple[int, M.AgentResult | None]:
```

이렇게 바꾼다:

```python
def run_agent(model: str, project: str, slug: str, spec_file: str, root: str,
              terms_json: str | None = None,
              timeout: float | None = None,
              doc_dir: str = "specs",
              citation_report: dict[str, list[str]] | None = None
              ) -> tuple[int, M.AgentResult | None]:
```

같은 함수 안, `prompt = agent_prompt(...)` 줄을 이렇게 바꾼다:

```python
    prompt = agent_prompt(project, slug, spec_file, root, terms_json, doc_dir,
                          citation_report)
```

`main()` 안, `terms_json` 을 구하는 줄(404-405행 부근) 아래에 더한다:

```python
    citation_report = None
    if spec is not None:
        citation_report = citationReport(os.path.join(project, doc_dir, spec["file"]), root=ROOT)
```

`run_agent(...)` 호출부(agent 단계, 434-436행 부근)에 `citation_report=citation_report` 를 더한다:

```python
            rc, result = run_agent(a.model, project, a.slug, spec_file, ROOT,
                                   terms_json=terms_json, timeout=a.timeout,
                                   doc_dir=doc_dir, citation_report=citation_report)
```

"이미 있는 것" 을 찍는 줄(420-421행 부근) 아래에 한 줄을 더한다:

```python
    if citation_report and (citation_report["broken_citations"] or citation_report["broken_paths"]):
        n = len(citation_report["broken_citations"]) + len(citation_report["broken_paths"])
        print("인용 점검 — 원본 문서에서 깨진 인용·경로 %d건 (에이전트 프롬프트에 실림)" % n)
```

- [ ] **Step 6: dry-run 으로 실제 배선을 확인한다**

Run:
```bash
.venv/bin/python runner/run_mode2.py docs/superpowers symbol-resolution-survey --dry-run
```
Expected: 종료 코드 0. `docs/superpowers/plans/2026-08-30-symbol-resolution-survey.md` 는
이미 원고가 채워져 있어(`has_manuscript`) `agent` 단계는 빠지지만, **에러 없이** `citation_report`
계산이 끝나야 한다 — 계획서 자신이 옛 `codegraph/` 경로를 인용하므로 실제로 걸릴 것이다.

- [ ] **Step 7: 통과를 확인한다**

Run: `.venv/bin/python -m pytest runner/test_run_mode2.py -v`
Expected: 전부 PASS

- [ ] **Step 8: 커밋**

```bash
git add runner/run_mode2.py runner/test_run_mode2.py
git commit -m "[feat] : Mode 2 에이전트 프롬프트에 원본 문서 인용의 기계 점검 결과를 싣는다"
```

---

### Task 4: 전체 게이트를 돌리고 나침반 문서를 갱신한다

**Files:**
- Modify: `runner/CLAUDE.md` (import 표)

- [ ] **Step 1: 전체 시험을 돌린다**

Run: `.venv/bin/python -m pytest -q`
Expected: 기존 466 + 이 계획이 더한 시험(약 8개) 전부 통과, 실패 0

- [ ] **Step 2: 타입 검사를 돌린다**

Run: `npm run typecheck:py`
Expected: 0 errors

- [ ] **Step 3: `runner/CLAUDE.md` 의 gotcha 를 갱신한다**

`runner/CLAUDE.md` 의 "**Gotcha — `run_mode1.py` 만 `machine/` 을 import 한다.**" 문단을 찾아
아래 문장을 그 문단 끝에 더한다:

```markdown
`run_mode2.py` 도 하나 더 있다 — `machine.doc_citations`(표준 라이브러리만 쓰는 모듈이라
`machine/` 을 평평하게 `sys.path` 에 넣을 필요 없이 저장소 뿌리를 넣고
`from machine.doc_citations import …` 로 부른다). `machine/*` 를 서로 부르는 평평한 import(예:
`terms_db.py` 의 `from codegraph_types import …`)에 기대는 모듈은 여전히 `run_mode1.py` 식
배선이 필요하다 — 배선 방식이 모듈마다 다르다는 뜻이다.
```

- [ ] **Step 4: 인용 검사 자체를 돌려 이 문서 수정이 스스로 깨지지 않았는지 본다**

Run: `.venv/bin/python -m pytest test/test_docs_citations.py -v`
Expected: 전부 PASS — `runner/CLAUDE.md` 에 새로 적은 경로 인용(`machine/doc_citations` 는 확장자가
없어 `CITE`/`PATH_REF` 대상이 아니다)이 있다면 걸리지 않는지 확인

- [ ] **Step 5: 커밋**

```bash
git add runner/CLAUDE.md
git commit -m "[docs] : machine import 배선이 이제 두 갈래임을 나침반에 남긴다"
```

---

## 이 계획이 **하지 않는** 것

| 안 하는 것 | 왜 |
|---|---|
| 함수·심볼 **존재 여부**(예: 계획서가 말하는 `resolve_target`) 를 기계로 검사 | 파일:줄 인용과는 다른 문제 — 심볼 검색은 `codegraph.json` 이나 AST 가 있어야 하고, 이 계획의 범위(문서 인용) 밖이다. 하고 싶어지면 사용자에게 먼저 보고한다 |
| 벡터 유사도로 "옛 경로 → 새 경로" 후보 추천 | 확률적 매칭이라 이 계획(결정론적 존재 검사)의 성격과 다르다. 별도 결정 사안 — `resolve_target` 의 "모호하면 찍지 않는다" 규율과 같은 논의가 필요하다 |
| `verify_citations.py`(Mode 1 위키 산문의 L3 심볼 대조)와 통합 | 별개 도구다. `verify_citations.py` 는 `codegraph.json` 대조가 있어야 도는데, 계획서·스펙 문서에는 그 재료가 없을 수 있다 — 합치면 거울 함정이다 |
| Mode 1(`report-wiki`)에도 같은 인용 점검을 배선하기 | 이번 계획은 Mode 2 의 공백만 메운다. Mode 1 은 이미 `check_terms` 가 있다 |

---

## Self-Review

**1. 스펙 커버리지** — 이전 대화에서 제안한 "계획서 인용을 미리 기계로 검증해 에이전트 프롬프트에
싣는다"는 목표를 Task 1(재사용 가능한 자리로 이동) → Task 2(임의 문서 대상 확장) → Task 3(실제 배선)
순서로 전부 덮는다. Task 4 는 게이트와 문서 정합성.

**2. 자리표시자 없음** — 모든 단계에 실제 코드·실제 명령이 있다. "적절히 처리" 류 문구 없음.

**3. 이름 일관성** — `citationReport(path, root=ROOT) -> dict[str, list[str]]` 하나만 새로 만들고
Task 2·3 에서 같은 이름·같은 반환 꼴로 쓴다. 옮긴 여섯 함수(`citationsIn` 등)는 이름을 바꾸지
않았다 — 시험 파일과의 계약을 유지하기 위해서다.

**4. 알려진 위험** — Task 3 Step 3 의 `.format()` 자리 교체는 `run_mode2.py` 의 큰 삼중따옴표
문자열 안에서 이뤄진다. 문자열이 길어 오프셋이 실제 파일과 미세하게 어긋날 수 있으니, 적용 전
`grep -n "{terms_block}"` 로 정확한 줄을 다시 확인한다.
