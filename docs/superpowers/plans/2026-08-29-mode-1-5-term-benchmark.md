# Mode 1.5 — 용어 이해도 벤치마크 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 설계 검토(Mode 2) 이전에 **읽는 사람의 머릿속 빈 칸을 실측으로 찾아내고**, 그 결과를 보고서의 용어집으로 결정적으로 흘려보낸다.

**Architecture:** 인공지능 모델을 평가하는 벤치마크 절차를 사람 쪽으로 뒤집어 쓴다. 정답지를 만들고 → 객관식으로 묻고 → 정답률로 채점해 → 확실/애매/모름으로 가른다. **객관적 정답(`TermMeans`)과 주관적 이해도(`UserMentalValue`)를 한 레코드에 담되 필드로 분리**한다. 전자는 코드베이스에서 기계로 뽑은 정적·결정론적 값이고, 후자는 사람마다·시점마다 다른 값이다. CLI 는 결정론적인 부분(수집·채점·산출)만 맡고, 사람에게 묻는 절차는 Skill 이 맡는다 — **도구는 판정하지 않는다**는 이 저장소의 규율을 그대로 잇는다.

**Tech Stack:** Node 25.8 (ESM `.mjs`) · Python 3.14.6 (`.venv`, pytest 9.1.1) · esbuild 0.28.2 · React 19 `renderToStaticMarkup` · d3-force 3.0

---

## 이 계획의 범위

| Phase | 내용 | 성격 | 산출물 |
|---|---|---|---|
| 0 | CLI 빌드 타깃 분리 | 코드 | `bin/report-wiki` · `report-term` · `report-spec` |
| 1 | 코드베이스 용어 DB — Mode 1 확장 | 코드 (Python) | `codegraph/terms_db.py` → `terms-db.json` |
| 2 | 용어 후보 수집 — Plan 교차 | 코드 (Node) | `scripts/term/collect.mjs` |
| 3 | 출제와 채점 | 코드 (Node) | `scripts/term/quiz.mjs` |
| 4 | 산출물 두 갈래 | 코드 (Node) | 학습 노트 `.md` + 용어집 DB `.json` |
| 5 | Mode 2 연동 | 코드 (TS) | `Term.mental` 필드 + 이해도 표시 + init 스켈레톤 연결 자리 |
| 6 | 사람에게 묻는 절차 | **Skill 문서** | `~/.claude/skills/term-benchmark/SKILL.md` |

**Phase 0 을 맨 앞에 둔 이유:** Mode 1.5 의 명령이 기존 `report init|build|check` 와 성격이 다르다. 지금 한 바구니에 넣으면 나중에 가르는 비용이 커진다. 빌드 타깃을 먼저 갈라 두고 그 안에 새 모드를 넣는다.

**Phase 6 을 맨 뒤에 둔 이유:** 사람에게 묻는 절차는 CLI 가 무엇을 내는지 확정된 뒤에야 쓸 수 있다.

---

## File Structure

```
report-builder/
  bin/
    report              [수정] 기존 진입점 — report-spec 으로 위임하고 안내를 낸다
    report-wiki         [신설] Mode 1   — 코드베이스 위키
    report-term         [신설] Mode 1.5 — 용어 이해도 점검
    report-spec         [신설] Mode 2   — 설계 검토 보고서
  codegraph/
    terms_db.py         [신설] 코드베이스 용어 전수 수집 → terms-db.json
    test_normalize.py   [수정] terms_db 단위 테스트 추가
  scripts/
    term/
      collect.mjs       [신설] 용어 후보 수집 — 코드베이스 DB 와 Plan 의 교차
      quiz.mjs          [신설] 객관식 출제와 채점
      emit.mjs          [신설] 학습 노트와 용어집 DB 출력
  src/
    types.ts            [수정] Term 에 mental 필드 추가
    components/terms.tsx[수정] 이해도별 표시 구분
    theme.css           [수정] 이해도 표시 스타일
  test/
    term.test.mjs       [신설] collect / quiz / emit 의 순수 함수 테스트
```

**분해 축(design-decision-discipline §2.7):** `scripts/term/` 을 하위 디렉토리로 묶은 것은 **파이프라인 단계 친화도**다. 세 파일이 한 흐름의 연속 단계이고 같이 고쳐진다. `scripts/` 최상위에 흩으면 기존 `build.mjs`·`check.mjs`(Mode 2 전용)와 섞인다.

---

## 착수 전 확인된 사실 (2026-08-29 실측)

| 항목 | 값 | 확인 방법 |
|---|---|---|
| Node | v25.8.0 | `node -v` |
| Python | 3.14.6 (`.venv/bin/python`) | `.venv/bin/python --version` |
| pytest | 9.1.1 | `.venv/bin/python -m pytest --version` |
| `facts.py` 산출물 | `<out>/facts/` 에 `modules.md` `classes.md` `external.md` `entrypoints.md` `hotspot.md` | `codegraph/facts.py:200-296` |
| `facts.py` 인자 | `facts.py <codegraph.json> --repo <저장소> [--detail roslyn-dump.json] [-o 출력디렉토리]` | `codegraph/facts.py:128-133` |
| `bin/report` | `init`/`build`/`check` 를 `scripts/*.mjs` 로 디스패치만 | `bin/report:11-15` |
| PATH 등록 | `~/.zshrc:211` — `export PATH="$HOME/LLM-Tools/report-builder/bin:$PATH"` | `grep -n report-builder ~/.zshrc` |
| 현재 컴포넌트 export | 17개 | `node -e 'import("./.tmp/lib.mjs")...'` |
| 산출물 `<script>` 예산 | 1개. 용어 그래프 런타임이 이미 사용 중 | `CLAUDE.md` 산출물 불변식 절 |
| deep-wiki 스킬 (Mode 1) | `wiki-architect` `wiki-researcher` `wiki-page-writer` 등 10종 | `ls ~/.claude/plugins/cache/skills/deep-wiki/*/skills/` |

---

## 채점 구간 — 2026-08-29 사용자 확정

한 용어당 **5문항**이다. 4문항이면 정답률이 0/25/50/75/100 이라 80% 임계에 딱 떨어지는 값이 없다.

| 맞힌 수 | 정답률 | 갈래 |
|---|---|---|
| 4~5개 | 80~100% | **확실** |
| 2~3개 | 40~60% | **애매** |
| 0~1개 | 0~20% | **모름** |

"모른다"를 **3회 이상** 고르면 정답률과 무관하게 **모름**이다. 찍어서 맞힌 것을 안다고 세지 않기 위해서다.

**이 구간은 임의값이 아니라 사용자가 확정한 값이다. 코드에서 바꾸지 말 것.**

---

# Phase 0 — CLI 빌드 타깃 분리

## Task 0.1: 공통 디스패처를 함수로 뺀다

**Files:**
- Create: `scripts/dispatch.mjs`
- Test: `test/dispatch.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/dispatch.test.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveScript } from "../scripts/dispatch.mjs";

test("resolveScript 는 등록된 명령을 스크립트 경로로 바꾼다", () => {
  const table = { init: "scripts/init.mjs", build: "scripts/build.mjs" };
  assert.equal(resolveScript(table, "init"), "scripts/init.mjs");
});

test("resolveScript 는 없는 명령에 null 을 낸다", () => {
  const table = { init: "scripts/init.mjs" };
  assert.equal(resolveScript(table, "nope"), null);
});

test("resolveScript 는 명령이 없으면 null 을 낸다", () => {
  assert.equal(resolveScript({ init: "x" }, undefined), null);
});

test("resolveScript 는 프로토타입 오염을 통과시키지 않는다", () => {
  assert.equal(resolveScript({ init: "x" }, "toString"), null);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `node --test test/dispatch.test.mjs`
Expected: FAIL — `Cannot find module '.../scripts/dispatch.mjs'`

- [ ] **Step 3: 최소 구현을 쓴다**

`scripts/dispatch.mjs`:

```javascript
// scripts/dispatch.mjs — mode 별 bin 진입점이 공유하는 디스패처.
// 각 bin 은 자기 명령표만 갖고 이 함수를 부른다.
import { spawnSync } from "node:child_process";
import { join } from "node:path";

/** 명령표에서 스크립트 상대경로를 찾는다. 없으면 null. */
export function resolveScript(table, cmd) {
  if (!cmd) return null;
  if (!Object.hasOwn(table, cmd)) return null;
  return table[cmd];
}

// 직접 실행 가드 — import 시에는 순수 함수만 노출한다(scripts/*.mjs 규약).
export function runDispatch({ root, table, argv, usage }) {
  const [cmd, ...rest] = argv;
  const script = resolveScript(table, cmd);
  if (!script) {
    console.error(usage);
    process.exit(1);
  }
  const r = spawnSync(process.execPath, [join(root, script), ...rest], { stdio: "inherit" });
  process.exit(r.status ?? 1);
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `node --test test/dispatch.test.mjs`
Expected: PASS — 4 tests

- [ ] **Step 5: 커밋**

```bash
git add scripts/dispatch.mjs test/dispatch.test.mjs
git commit -m "[refactor] : mode 별 bin 이 공유할 디스패처를 함수로 분리"
```

## Task 0.2: 세 진입점을 만든다

**Files:**
- Create: `bin/report-spec` · `bin/report-term` · `bin/report-wiki`
- Modify: `bin/report`

- [ ] **Step 1: `bin/report-spec` 을 만든다**

```javascript
#!/usr/bin/env node
// bin/report-spec — Mode 2. Spec/Plan 설계 검토 보고서.
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runDispatch } from "../scripts/dispatch.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

runDispatch({
  root: ROOT,
  argv: process.argv.slice(2),
  table: {
    init: "scripts/init.mjs",
    build: "scripts/build.mjs",
    check: "scripts/check.mjs",
  },
  usage: "사용법 — report-spec <init|build|check> [인자]",
});
```

- [ ] **Step 2: `bin/report-term` 을 만든다**

```javascript
#!/usr/bin/env node
// bin/report-term — Mode 1.5. 용어 이해도 점검.
//   collect : 이 Plan 을 이해하는 데 필요한 용어를 모은다
//   quiz    : 객관식 문항을 낸다
//   grade   : 답안을 채점해 확실/애매/모름을 매긴다
//   emit    : 학습 노트와 용어집 DB 를 낸다
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runDispatch } from "../scripts/dispatch.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

runDispatch({
  root: ROOT,
  argv: process.argv.slice(2),
  table: {
    collect: "scripts/term/collect.mjs",
    quiz: "scripts/term/quiz.mjs",
    grade: "scripts/term/quiz.mjs",
    emit: "scripts/term/emit.mjs",
  },
  usage: "사용법 — report-term <collect|quiz|grade|emit> [인자]",
});
```

- [ ] **Step 3: `bin/report-wiki` 를 만든다**

Mode 1 은 아직 Node 스크립트가 없고 Python 파이프라인과 deep-wiki 스킬로 돈다. 지금은 **길잡이만** 낸다. 없는 기능을 있는 척하지 않는다.

```javascript
#!/usr/bin/env node
// bin/report-wiki — Mode 1. 코드베이스 위키.
// 아직 Node 진입점이 없다. 실제 파이프라인은 codegraph/*.py 와 deep-wiki 스킬이다.
// 이 파일은 그 사실을 알려 주는 자리 표시자이며, Mode 1 이 Node 로 옮겨오면 채운다.
console.log(`Mode 1 — 코드베이스 위키

아직 이 진입점은 비어 있다. 현재 Mode 1 은 아래로 돈다:

  1) 정적 계층   codegraph/normalize.py · codegraph/facts.py
  2) 용어 DB     codegraph/terms_db.py   (Mode 1.5 의 재료)
  3) 위키 작성   deep-wiki 스킬 (wiki-architect · wiki-researcher · wiki-page-writer)

용어 DB 만 필요하면:
  .venv/bin/python codegraph/terms_db.py <codegraph.json> --repo <저장소> -o <출력디렉토리>
`);
process.exit(0);
```

- [ ] **Step 4: 기존 `bin/report` 를 위임으로 바꾼다**

기존 사용자가 `report build` 를 계속 쓸 수 있어야 한다. 끊지 않는다.

```javascript
#!/usr/bin/env node
// bin/report — 옛 진입점. Mode 2(report-spec)로 위임한다.
// mode 별 바이너리 분리(2026-08-29) 이전의 습관을 끊지 않기 위해 남긴다.
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
console.error("알림 — report 는 report-spec 으로 바뀌었다. 같은 동작을 그대로 수행한다.");
const r = spawnSync(process.execPath, [join(ROOT, "bin/report-spec"), ...process.argv.slice(2)], {
  stdio: "inherit",
});
process.exit(r.status ?? 1);
```

- [ ] **Step 5: 실행 권한을 준다**

```bash
chmod +x bin/report-spec bin/report-term bin/report-wiki
ls -l bin/
```

Expected: 네 파일 모두 `-rwxr-xr-x`

- [ ] **Step 6: 기존 동작이 안 깨졌는지 확인한다**

```bash
cd docs/superpowers/specs/llm-load-reduction
report check
report-spec check
```

Expected: 둘 다 같은 검사 4줄을 낸다. `report` 쪽에는 앞에 알림 한 줄이 더 붙는다.

- [ ] **Step 7: 커밋**

```bash
git add bin scripts/dispatch.mjs
git commit -m "[refactor] : mode 별 CLI 진입점 분리 - report-wiki, report-term, report-spec"
```

## Task 0.3: 문서를 갱신한다

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 명령 절을 고친다**

`## 명령` 절의 `report init` / `report build` / `report check` 를 `report-spec ...` 으로 바꾸고, 아래 표를 넣는다.

```markdown
| 바이너리 | Mode | 하는 일 |
|---|---|---|
| `report-wiki` | 1 | 코드베이스 위키. 현재는 길잡이만 내고 실제 파이프라인은 `codegraph/*.py` + deep-wiki 스킬 |
| `report-term` | 1.5 | 용어 이해도 점검. `collect` → `quiz` → `grade` → `emit` |
| `report-spec` | 2 | 설계 검토 보고서. `init` → `build` → `check` |
| `report` | — | 옛 이름. `report-spec` 으로 위임한다 |
```

- [ ] **Step 2: 커밋**

```bash
git add CLAUDE.md
git commit -m "[docs] : mode 별 CLI 진입점 분리 반영"
```

---

# Phase 1 — 코드베이스 용어 DB (Mode 1 확장)

**이 Phase 의 산출물이 Mode 1.5 의 재료다.** `{ "용어": "의미/정답" }` 꼴의 정적·결정론적 데이터이며, LLM 이 세션마다 용어를 다시 해석해 흔들리는 것을 막는 것이 목적이다.

## Task 1.1: 용어 추출 — 실패하는 테스트 먼저

> **⚠ 2026-08-29 실측 정정 — 아래 코드의 키 두 곳이 실제 `codegraph.json` 과 다르다.** 구현 서브에이전트가
> `codegraph/normalize.py:237,287` 을 열어 확인했다. 실제 산출물 기준으로 구현된 `codegraph/terms_db.py` 가 정본이다.
>
> | 항목 | 이 계획서 (틀림) | 실제 |
> |---|---|---|
> | 간선 | `source` / `target` | **`from` / `to`** |
> | 모듈 | `name` / `files` | **`id` / `depends_on`** |
>
> 이 계획서 초안대로였다면 간선이 전부 무시돼 `neighbors` 가 항상 비고 모듈 항목이 하나도 안 만들어졌을 것이다 —
> 그런데도 합성 데이터 테스트 3개는 통과했을 것이다. **합성 데이터만으로 검증하지 말 것**의 실례다.
>
> **남은 우려 (사용자 결정 대기):**
> - C++ 용어 키가 네임스페이스를 포함한다 (`SJH::Material`). C# 은 단순 이름. Mode 1.5 가 `Material` 로 찾으면 못 찾는다
> - 외부 노드 6건(`(STL) std` 등)이 수집에 포함된다. `means` 가 "__external__ 모듈의 external." 로 어색하다

**Files:**
- Create: `codegraph/terms_db.py`
- Test: `codegraph/test_normalize.py` (추가)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`codegraph/test_normalize.py` 끝에 추가:

```python
# ── 8. 코드베이스 용어 DB (Mode 1.5 의 재료)

def test_terms_db_extracts_modules_and_classes():
    """codegraph.json 의 노드와 모듈이 용어 항목이 돼야 한다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {
        "language": "csharp",
        "nodes": [
            {"id": "A.B.Renderer", "name": "Renderer", "module": "render",
             "file": "src/render/renderer.cs", "line": 12, "kind": "class"},
        ],
        "edges": [],
        "modules": [{"name": "render", "files": 3}],
    }
    db = T.build_terms(g, facts={}, hotspot=[])
    assert "Renderer" in db, "클래스 이름이 용어로 안 들어갔다"
    assert "render" in db, "모듈 이름이 용어로 안 들어갔다"
    assert db["Renderer"]["kind"] == "class"
    assert db["Renderer"]["where"] == "src/render/renderer.cs:12"


def test_terms_db_means_is_never_empty():
    """정답 칸이 비면 Mode 1.5 가 출제할 수 없다. 최소한 기계가 아는 사실로 채운다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {"language": "cpp",
         "nodes": [{"id": "N", "name": "Thing", "module": "core",
                    "file": "src/core/thing.h", "line": 4, "kind": "struct"}],
         "edges": [], "modules": [{"name": "core", "files": 1}]}
    db = T.build_terms(g, facts={}, hotspot=[])
    for name, rec in db.items():
        assert rec["means"].strip(), f"{name} 의 means 가 비었다"


def test_terms_db_is_deterministic():
    """같은 입력이면 같은 출력이어야 한다. LLM 혼선을 막는 것이 이 파일의 목적이다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import terms_db as T
    g = {"language": "cpp",
         "nodes": [{"id": "N1", "name": "B", "module": "m", "file": "b.h", "line": 1, "kind": "class"},
                   {"id": "N2", "name": "A", "module": "m", "file": "a.h", "line": 2, "kind": "class"}],
         "edges": [], "modules": [{"name": "m", "files": 2}]}
    first = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    second = json.dumps(T.build_terms(g, facts={}, hotspot=[]), ensure_ascii=False, sort_keys=True)
    assert first == second
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_normalize.py -k terms_db -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'terms_db'`

- [ ] **Step 3: 최소 구현을 쓴다**

`codegraph/terms_db.py`:

```python
#!/usr/bin/env python3
"""terms_db.py — 코드베이스 용어 전수 수집.

**왜 필요한가.** Mode 1.5(용어 이해도 점검)가 사람에게 문제를 내려면 정답지가 있어야 한다.
그 정답지를 LLM 이 매번 새로 지어내면 세션마다 설명이 흔들린다. 여기서 한 번 뽑아 고정한다.

**이 파일은 판정하지 않는다.** 기계가 아는 사실(이름, 종류, 위치, 이웃)만 적는다.
사람이 읽을 설명은 Mode 1.5 가 LLM 으로 채우고 사용자가 검수한다.

  terms_db.py <codegraph.json> --repo <저장소> [-o 출력디렉토리]
"""
import argparse
import json
import os


def _where(node):
    f = node.get("file") or ""
    ln = node.get("line")
    if not f:
        return ""
    return f"{f}:{ln}" if ln else f


def build_terms(graph, facts, hotspot):
    """codegraph.json 에서 용어 사전을 만든다. 입력이 같으면 출력도 같다."""
    db = {}
    by_id = {n.get("id"): n for n in graph.get("nodes", [])}

    # 이웃 — 무엇과 이어져 있는지가 용어를 설명하는 가장 값싼 재료다.
    neighbors = {}
    for e in graph.get("edges", []):
        s, t = e.get("source"), e.get("target")
        for a, b in ((s, t), (t, s)):
            if a in by_id and b in by_id:
                neighbors.setdefault(a, set()).add(by_id[b].get("name", ""))

    for node in graph.get("nodes", []):
        name = node.get("name")
        if not name:
            continue
        kind = node.get("kind", "type")
        module = node.get("module", "")
        near = sorted(x for x in neighbors.get(node.get("id"), set()) if x)
        means = f"{module} 모듈의 {kind}."
        if near:
            means += " " + ", ".join(near[:5]) + " 와(과) 이어져 있다."
        db[name] = {
            "kind": kind,
            "module": module,
            "where": _where(node),
            "means": means,
            "neighbors": near,
            "source": "codegraph",
        }

    for m in graph.get("modules", []):
        name = m.get("name")
        if not name or name in db:
            continue
        db[name] = {
            "kind": "module",
            "module": name,
            "where": "",
            "means": f"파일 {m.get('files', 0)}개를 묶은 모듈.",
            "neighbors": [],
            "source": "codegraph",
        }

    for h in hotspot:
        name = h.get("name") if isinstance(h, dict) else None
        if name and name in db:
            db[name]["hotspot"] = True

    return dict(sorted(db.items()))


# 직접 실행됐을 때만 CLI 를 수행한다(scripts/*.mjs 와 같은 규약).
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codegraph")
    ap.add_argument("--repo", required=True)
    ap.add_argument("-o", "--out", help="출력 디렉토리. 기본: codegraph.json 옆")
    a = ap.parse_args()

    g = json.load(open(a.codegraph, encoding="utf-8"))
    base = a.out or os.path.dirname(os.path.abspath(a.codegraph))
    os.makedirs(base, exist_ok=True)

    db = build_terms(g, facts={}, hotspot=[])
    path = os.path.join(base, "terms-db.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"{path} — 용어 {len(db)}개")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `.venv/bin/python -m pytest codegraph/test_normalize.py -k terms_db -v`
Expected: PASS — 3 tests

- [ ] **Step 5: 커밋**

```bash
git add codegraph/terms_db.py codegraph/test_normalize.py
git commit -m "[feat] : codegraph - 코드베이스 용어 전수 수집 단계 신설"
```

---

# Phase 2 — 용어 후보 수집 (Plan 과의 교차)

**출제 범위는 코드베이스 전체가 아니다.** 지금 검토할 Plan 이 실제로 요구하는 용어만 낸다. 여기에 그 Plan 이 새로 만든 개념이 더해진다.

## Task 2.1: 교차 추출 — 실패하는 테스트 먼저

> **2026-08-29 실측 (구현 완료 후 실제 Plan 으로 돌린 결과).** `2026-08-28-llm-load-reduction.md` 에서 신규 개념 **34개**가 잡혔다.
> 기대한 `C-19` · `calls[]` · `codegraph.json` 은 전부 들어왔다. 오탐도 있다 — **고치지 않고 기록만 한다**:
>
> | 잡힌 것 | 실물 | 판단 |
> |---|---|---|
> | `a.json` | Plan 218행 `if a.json:` — Python 속성 접근 | 🔵 오탐. 마크다운 코드 펜스를 안 걷어내서다 |
> | `M1`~`M5` · `U1`~`U6` | Plan 내부 표의 행 라벨 | 🟡 결정 코드 꼴이라 잡혔으나 "이해에 필요한 용어"인지는 저자 판단 |
> | `L3` · `F15` | 다른 인계 문서에서 온 기존 식별자로 보임 | 🟡 DB 가 비어 있어 신규/기존을 못 가름. 실제 `terms-db.json` 이 붙으면 해소 |
> | `warm.json` 1건 · `warmup.json` 2건 | Plan 쪽 표기 불일치 | 🔵 실재. Plan 의 오기 |
>
> **코드 펜스 제거 여부는 사용자 결정 대기.** 넣으면 `a.json` 은 사라지지만 `# ── 9. calls[]` 처럼 코드 블록 안에만
> 있는 진짜 개념을 놓칠 수 있다.

**Files:**
- Create: `scripts/term/collect.mjs`
- Test: `test/term.test.mjs`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/term.test.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { pickTerms, findNewConcepts } from "../scripts/term/collect.mjs";

test("pickTerms 는 Plan 본문에 나오는 코드베이스 용어만 고른다", () => {
  const db = {
    Renderer: { kind: "class", means: "render 모듈의 class." },
    Unused: { kind: "class", means: "안 쓰이는 것." },
  };
  const plan = "이 계획은 Renderer 를 고친다.";
  const got = pickTerms(db, plan);
  assert.deepEqual(Object.keys(got), ["Renderer"]);
});

test("pickTerms 는 낱말 경계를 지킨다", () => {
  const db = { Ray: { kind: "class", means: "x" } };
  assert.deepEqual(Object.keys(pickTerms(db, "Raycast 를 쓴다")), []);
  assert.deepEqual(Object.keys(pickTerms(db, "Ray 를 쓴다")), ["Ray"]);
});

test("findNewConcepts 는 Plan 이 새로 만든 식별자를 찾는다", () => {
  const db = { Renderer: { kind: "class", means: "x" } };
  const plan = "C-19 결정에 따라 calls[] 를 roslyn-dump.json 에 넣는다. Renderer 는 그대로다.";
  const got = findNewConcepts(db, plan);
  assert.deepEqual(got.sort(), ["C-19", "calls[]", "roslyn-dump.json"]);
});

test("findNewConcepts 는 이미 DB 에 있는 것을 새 개념으로 세지 않는다", () => {
  const db = { "calls[]": { kind: "field", means: "x" } };
  assert.deepEqual(findNewConcepts(db, "calls[] 를 쓴다"), []);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: FAIL — `Cannot find module '.../scripts/term/collect.mjs'`

- [ ] **Step 3: 최소 구현을 쓴다**

`scripts/term/collect.mjs`:

```javascript
// scripts/term/collect.mjs — Mode 1.5 1단계. 이 Plan 을 이해하는 데 필요한 용어를 모은다.
//
// 두 갈래에서 모은다.
//   (가) 코드베이스 용어 DB 와 Plan 본문의 교차 — 정답이 이미 있다
//   (나) Plan 이 새로 만든 개념 — 정답이 없다. **Plan 저자가 직접 써야 한다**
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

/** 정규식 특수문자를 막는다. calls[] 같은 이름이 그대로 들어온다. */
function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** 코드베이스 용어 DB 중 Plan 본문에 실제로 등장하는 것만 고른다. */
export function pickTerms(db, planText) {
  const out = {};
  for (const [name, rec] of Object.entries(db)) {
    // 이름이 기호로 끝나면(calls[]) 낱말 경계를 뒤에 붙일 수 없다.
    const tail = /[A-Za-z0-9_]$/.test(name) ? "\\b" : "";
    const re = new RegExp("\\b" + escapeRe(name) + tail);
    if (re.test(planText)) out[name] = rec;
  }
  return out;
}

/**
 * Plan 이 새로 만든 개념을 찾는다. `check.mjs` 의 용어 대조와 같은 세 꼴을 쓴다.
 * 자연어 용어(WarmUp·PageRank)는 기계가 가릴 수 없어 저자가 직접 넣어야 한다.
 */
export function findNewConcepts(db, planText) {
  const known = new Set(Object.keys(db));
  const found = new Set();
  const patterns = [
    /\b[A-Z]{1,3}-?\d{1,3}\b/g,
    /\b[a-z][a-z0-9_-]*\.json\b/g,
    /\b[a-z][A-Za-z0-9_]*\[\]/g,
  ];
  for (const re of patterns) {
    for (const m of planText.matchAll(re)) {
      if (!known.has(m[0])) found.add(m[0]);
    }
  }
  return [...found].sort();
}

if (process.argv[1] && process.argv[1].endsWith("collect.mjs")) {
  const [planPath, dbPath] = process.argv.slice(2);
  if (!planPath) {
    console.error("사용법 — report-term collect <plan.md> [terms-db.json]");
    process.exit(1);
  }
  const planText = readFileSync(planPath, "utf8");
  const db = dbPath && existsSync(dbPath) ? JSON.parse(readFileSync(dbPath, "utf8")) : {};

  const known = pickTerms(db, planText);
  const fresh = findNewConcepts(db, planText);

  const out = { plan: planPath, known, newConcepts: fresh };
  const path = join(process.cwd(), "term-candidates.json");
  writeFileSync(path, JSON.stringify(out, null, 2) + "\n");

  console.log(`${path}`);
  console.log(`  코드베이스 용어 ${Object.keys(known).length}개`);
  console.log(`  Plan 신규 개념 ${fresh.length}개 — 정답은 Plan 저자가 써야 한다`);
  if (fresh.length) console.log(`    ${fresh.join(", ")}`);
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: PASS — 4 tests

- [ ] **Step 5: 실제 Plan 으로 돌려 본다**

```bash
cd $REPO_ROOT
report-term collect docs/superpowers/plans/2026-08-28-llm-load-reduction.md
```

Expected: `term-candidates.json` 이 생기고, 신규 개념 목록에 `C-19` · `calls[]` · `codegraph.json` 등이 뜬다. 용어 DB 를 안 넘겼으므로 코드베이스 용어는 0개다.

- [ ] **Step 6: 커밋**

```bash
git add scripts/term/collect.mjs test/term.test.mjs
git commit -m "[feat] : term - Plan 이 요구하는 용어와 신규 개념을 가려 모은다"
```

---

# Phase 3 — 출제와 채점

## Task 3.1: 채점 규칙 — 실패하는 테스트 먼저

**Files:**
- Create: `scripts/term/quiz.mjs`
- Test: `test/term.test.mjs` (추가)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

구간 경계는 위 "채점 구간" 절의 확정값을 쓴다.

`test/term.test.mjs` 끝에 추가:

```javascript
import { gradeOne, QUESTIONS_PER_TERM } from "../scripts/term/quiz.mjs";

test("한 용어당 문항 수는 5개다", () => {
  assert.equal(QUESTIONS_PER_TERM, 5);
});

test("gradeOne 은 4개 이상 맞히면 확실로 매긴다", () => {
  assert.equal(gradeOne({ correct: 5, dontKnow: 0 }).mental, "확실");
  assert.equal(gradeOne({ correct: 4, dontKnow: 0 }).mental, "확실");
});

test("gradeOne 은 2~3개 맞히면 애매로 매긴다", () => {
  assert.equal(gradeOne({ correct: 3, dontKnow: 0 }).mental, "애매");
  assert.equal(gradeOne({ correct: 2, dontKnow: 0 }).mental, "애매");
});

test("gradeOne 은 거의 못 맞히면 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).mental, "모름");
  assert.equal(gradeOne({ correct: 0, dontKnow: 0 }).mental, "모름");
});

test("gradeOne 은 모른다를 3회 이상 고르면 정답률과 무관하게 모름으로 매긴다", () => {
  assert.equal(gradeOne({ correct: 2, dontKnow: 3 }).mental, "모름");
});

test("gradeOne 은 정답률을 함께 돌려준다", () => {
  assert.equal(gradeOne({ correct: 4, dontKnow: 0 }).rate, 80);
  assert.equal(gradeOne({ correct: 1, dontKnow: 0 }).rate, 20);
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: FAIL — `Cannot find module '.../scripts/term/quiz.mjs'`

- [ ] **Step 3: 최소 구현을 쓴다**

`scripts/term/quiz.mjs`:

```javascript
// scripts/term/quiz.mjs — Mode 1.5 2·3단계. 객관식 출제와 채점.
//
// **이 파일은 사람에게 묻지 않는다.** 문항을 만들어 파일로 내고, 답안 파일을 받아 채점만 한다.
// 사람에게 묻는 절차는 term-benchmark 스킬이 맡는다 — 도구는 판정하지 않는다는 규율의 연장이다.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** 한 용어당 문항 수. 5개여야 정답률이 80% 임계에 딱 떨어지는 값을 갖는다. */
export const QUESTIONS_PER_TERM = 5;

/**
 * 한 용어의 답안을 채점한다.
 * 구간 경계는 사용자가 확정한 값이다. 임의로 바꾸지 말 것.
 */
export function gradeOne({ correct, dontKnow }) {
  const rate = Math.round((correct / QUESTIONS_PER_TERM) * 100);
  let mental;
  if (dontKnow >= 3) mental = "모름";        // 찍어서 맞힌 것을 안다고 세지 않는다
  else if (rate >= 80) mental = "확실";      // 4~5개
  else if (rate >= 40) mental = "애매";      // 2~3개
  else mental = "모름";                      // 0~1개
  return { rate, mental };
}

/** 답안 전체를 채점한다. 입력이 같으면 출력도 같다. */
export function gradeAll(answers) {
  const out = {};
  for (const [term, a] of Object.entries(answers)) {
    out[term] = gradeOne(a);
  }
  return out;
}

if (process.argv[1] && process.argv[1].endsWith("quiz.mjs")) {
  const [mode, file] = process.argv.slice(2);
  if (mode === "grade" && file) {
    const answers = JSON.parse(readFileSync(file, "utf8"));
    const graded = gradeAll(answers);
    const path = join(process.cwd(), "term-grades.json");
    writeFileSync(path, JSON.stringify(graded, null, 2) + "\n");
    const tally = { 확실: 0, 애매: 0, 모름: 0 };
    for (const g of Object.values(graded)) tally[g.mental]++;
    console.log(`${path}`);
    console.log(`  확실 ${tally.확실} · 애매 ${tally.애매} · 모름 ${tally.모름}`);
  } else {
    console.error("사용법 — report-term grade <answers.json>");
    console.error("  문항 작성은 term-benchmark 스킬이 맡는다.");
    process.exit(1);
  }
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: PASS — 10 tests (앞 4 + 새 6)

- [ ] **Step 5: 커밋**

```bash
git add scripts/term/quiz.mjs test/term.test.mjs
git commit -m "[feat] : term - 정답률로 확실 애매 모름을 가르는 채점 규칙"
```

---

# Phase 4 — 산출물 두 갈래

## Task 4.1: 학습 노트와 용어집 DB — 실패하는 테스트 먼저

**Files:**
- Create: `scripts/term/emit.mjs`
- Test: `test/term.test.mjs` (추가)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```javascript
import { toTermsDb, toStudyNote } from "../scripts/term/emit.mjs";

const SAMPLE = {
  "calls[]": { means: "누가 누구를 부르는지 모은 목록", mental: "모름", rate: 20 },
  Renderer: { means: "render 모듈의 class", mental: "확실", rate: 100 },
};

test("toTermsDb 는 확실한 것도 빠뜨리지 않는다", () => {
  const db = toTermsDb(SAMPLE);
  assert.equal(Object.keys(db).length, 2, "확실로 판정된 것이 빠졌다");
});

test("toTermsDb 는 정답과 이해도를 다른 필드에 담는다", () => {
  const db = toTermsDb(SAMPLE);
  assert.equal(db["calls[]"].TermMeans, "누가 누구를 부르는지 모은 목록");
  assert.equal(db["calls[]"].UserMentalValue, "모름");
});

test("toStudyNote 는 모름과 애매만 싣는다", () => {
  const md = toStudyNote(SAMPLE);
  assert.ok(md.includes("calls[]"), "모름인 용어가 학습 노트에 없다");
  assert.ok(!md.includes("Renderer"), "확실한 용어가 학습 노트에 들어갔다");
});

test("toStudyNote 는 학습할 것이 없으면 그 사실을 적는다", () => {
  const md = toStudyNote({ A: { means: "x", mental: "확실", rate: 100 } });
  assert.ok(md.includes("학습할 용어가 없다"));
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: FAIL — `Cannot find module '.../scripts/term/emit.mjs'`

- [ ] **Step 3: 최소 구현을 쓴다**

`scripts/term/emit.mjs`:

```javascript
// scripts/term/emit.mjs — Mode 1.5 4단계. 두 갈래 산출물을 낸다.
//   (1) 학습 노트 .md   — 사람이 읽고 공부하는 것. 모름·애매만 싣는다
//   (2) 용어집 DB .json — Mode 2 의 terms 가 되는 것. **전부 싣고 표시를 달리 한다**
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** Mode 2 로 넘길 용어집. 객관적 정답과 주관적 이해도를 필드로 가른다. */
export function toTermsDb(graded) {
  const out = {};
  for (const [term, rec] of Object.entries(graded)) {
    out[term] = {
      TermMeans: rec.means,
      UserMentalValue: rec.mental,
    };
  }
  return out;
}

/** 사람이 읽는 학습 노트. 이미 아는 것을 다시 싣지 않는다. */
export function toStudyNote(graded) {
  const rows = Object.entries(graded)
    .filter(([, r]) => r.mental !== "확실")
    .sort((a, b) => (a[1].rate ?? 0) - (b[1].rate ?? 0));

  const head = "# 용어 학습 노트\n\n실측으로 가려낸, 아직 확실하지 않은 용어들이다.\n\n";
  if (rows.length === 0) return head + "학습할 용어가 없다. 전부 확실로 판정됐다.\n";

  const body = rows
    .map(([term, r]) => `## ${term}\n\n- 이해도 — **${r.mental}** (정답률 ${r.rate}%)\n- 뜻 — ${r.means}\n`)
    .join("\n");
  return head + body;
}

if (process.argv[1] && process.argv[1].endsWith("emit.mjs")) {
  const [file] = process.argv.slice(2);
  if (!file) {
    console.error("사용법 — report-term emit <term-grades.json>");
    process.exit(1);
  }
  const graded = JSON.parse(readFileSync(file, "utf8"));

  const dbPath = join(process.cwd(), "terms.json");
  writeFileSync(dbPath, JSON.stringify(toTermsDb(graded), null, 2) + "\n");

  const notePath = join(process.cwd(), "term-study-note.md");
  writeFileSync(notePath, toStudyNote(graded));

  console.log(`${dbPath} — 용어 ${Object.keys(graded).length}개`);
  console.log(`${notePath}`);
}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `node --test test/term.test.mjs`
Expected: PASS — 14 tests

- [ ] **Step 5: 커밋**

```bash
git add scripts/term/emit.mjs test/term.test.mjs
git commit -m "[feat] : term - 학습 노트와 Mode 2 용어집 DB 출력"
```

---

# Phase 5 — Mode 2 연동

## Task 5.1: `Term` 에 이해도 필드를 더한다

**Files:**
- Modify: `src/types.ts`
- Modify: `src/components/terms.tsx`
- Modify: `src/theme.css`
- Test: `test/components.test.mjs` (추가)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test/components.test.mjs` 끝에 추가:

```javascript
test("Glossary 는 이해도를 표시한다", () => {
  const out = html(Glossary({ terms: [
    { id: "calls[]", label: "calls[]", short: "호출 목록", kind: "artifact", mental: "모름" },
  ] }));
  assert.ok(out.includes("mental-모름"), "이해도 클래스가 없다");
});

test("Glossary 는 이해도가 없어도 렌더된다", () => {
  const out = html(Glossary({ terms: [
    { id: "A", label: "A", short: "x", kind: "concept" },
  ] }));
  assert.ok(out.includes("<td"), "이해도 없는 용어에서 깨졌다");
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `npm test 2>&1 | grep -A3 "Glossary 는 이해도"`
Expected: FAIL — `이해도 클래스가 없다`

- [ ] **Step 3: 타입에 필드를 더한다**

`src/types.ts` 의 `Term` 에 추가한다. **기존 필드를 지우거나 뜻을 바꾸지 않는다**(컴포넌트는 추가만 한다 규약):

```typescript
  /** Mode 1.5 가 실측한 읽는 사람의 이해도. 없으면 표시하지 않는다 */
  mental?: "확실" | "애매" | "모름";
```

- [ ] **Step 4: 컴포넌트에 표시를 더한다**

`src/components/terms.tsx` 의 `Glossary` 표에 컬럼을 하나 붙인다.

```tsx
        <thead>
          <tr>
            <th>용어</th>
            <th>갈래</th>
            <th>이해도</th>
            <th>뜻</th>
          </tr>
        </thead>
```

행 쪽:

```tsx
              <td>
                {t.mental ? (
                  <span className={`term-mental mental-${t.mental}`}>{t.mental}</span>
                ) : (
                  <span className="term-mental mental-미측정">미측정</span>
                )}
              </td>
```

- [ ] **Step 5: 스타일을 더한다**

`src/theme.css` 의 용어집 구획에 추가한다. **확실한 것은 흐리게** 해 시선이 빈 칸으로 가게 한다.

```css
.term-mental { display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-size: 11px; font-weight: 700; white-space: nowrap; }
.mental-확실 { background: var(--gray-soft); color: var(--text-3); }
.mental-애매 { background: var(--amber-soft); color: var(--amber); }
.mental-모름 { background: var(--red-soft); color: var(--red); }
.mental-미측정 { background: transparent; color: var(--text-3); font-weight: 400; }
```

- [ ] **Step 6: 테스트가 통과하는지 확인한다**

Run: `npm test`
Expected: PASS — 기존 44 + 새 2 = 46 tests

- [ ] **Step 7: 커밋**

```bash
git add src/types.ts src/components/terms.tsx src/theme.css test/components.test.mjs
git commit -m "[feat] : 용어집에 Mode 1.5 가 실측한 이해도 표시"
```

## Task 5.2: 용어집 DB 를 읽어 `terms` 를 채운다

**Files:**
- Modify: `scripts/init.mjs`

- [ ] **Step 1: `report-spec init` 이 용어집 DB 를 찾도록 한다**

`writeSkeleton` 이 만드는 `data.ts` 템플릿에, 같은 디렉토리에 `terms.json` 이 있으면 그것을 읽어 `terms` 를 채우는 주석을 넣는다. **자동으로 import 하지 않는다** — `data.ts` 는 사람이 읽는 파일이고 값이 눈에 보여야 한다.

`data.ts` 템플릿에 추가:

```typescript
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮긴다.
  //   report-term emit term-grades.json
  // 그 파일의 { "용어": { TermMeans, UserMentalValue } } 를
  // { id, label, short, kind, mental } 로 옮겨 적는다.
  terms: [],
```

- [ ] **Step 2: 확인한다**

```bash
cd /tmp && rm -rf termtest && mkdir -p termtest/specs && cd termtest
git init -q && mkdir -p specs
printf '# 시험용\n' > specs/2026-08-29-sample-design.md
report-spec init sample
grep -n "terms" specs/sample/data.ts
```

Expected: `terms: [],` 와 위 주석이 보인다.

- [ ] **Step 3: 커밋**

```bash
cd $REPO_ROOT
git add scripts/init.mjs
git commit -m "[feat] : init 스켈레톤에 Mode 1.5 용어집 연결 자리 추가"
```

---

# Phase 6 — 사람에게 묻는 절차 (Skill)

**이 Phase 의 산출물은 코드가 아니라 프롬프트다.** CLI 가 결정론적인 부분을 맡으므로, 남은 것은 사람에게 어떻게 묻는가다.

## Task 6.1: `term-benchmark` 스킬을 쓴다

> **2026-08-29 — 슬롯 C 에 위임.** 붙여넣기용 프롬프트는 `docs/handoffs/HANDOFF-2026-08-29-mode-1-5-skill.md` (HANDOFF ④).
> 오케스트레이터가 결과를 검토하고 저장소 사본을 커밋한다. Task 0.1~5.2 는 전부 완료됐다.

**Files:**
- Create: `~/.claude/skills/term-benchmark/SKILL.md`

- [ ] **Step 1: 스킬 문서를 쓴다**

담아야 할 것:

1. **언제 쓰는가** — Mode 2 로 설계 검토에 들어가기 전, Plan 을 받았을 때
2. **전제 확인** — Mode 1 이 WarmUp 되어 있는가(`terms-db.json` 존재 확인). 없으면 중단하고 보고
3. **절차**
   - `report-term collect <plan.md> <terms-db.json>` 으로 후보를 모은다
   - 신규 개념의 정답은 **Plan 저자에게 묻는다** — LLM 이 지어내지 않는다
   - 용어마다 **객관식 5문항 + "모른다" 선택지**를 만든다. 정답지는 `TermMeans` 다
   - `AskUserQuestion` 으로 묻는다. 한 번에 한 용어씩
   - 답안을 `answers.json` 으로 적는다
   - `report-term grade answers.json` → `report-term emit term-grades.json`
4. **출제 규율**
   - 오답 보기는 **그럴듯해야** 한다. 명백히 틀린 보기만 넣으면 채점이 무의미해진다
   - 보기 순서를 섞는다. 정답 위치가 몰리면 안 된다
   - **정답지에 없는 것을 묻지 않는다.** 모르는 것을 묻는 시험이 아니라 아는지를 재는 시험이다
5. **함정**
   - **LLM 이 사용자의 지식 상태를 안다고 가정하지 말 것.** 추정은 초안일 뿐이고 사용자가 고친다
   - **확실로 판정된 것을 용어집에서 빼지 말 것.** 전부 싣되 표시를 달리 한다
   - **문항을 스크립트로 자동 생성하지 말 것.** 보기의 그럴듯함은 기계가 못 만든다

- [ ] **Step 2: 스킬이 잡히는지 확인한다**

새 세션에서 `/term-benchmark` 가 목록에 뜨는지 본다.

- [ ] **Step 3: 커밋 (스킬은 저장소 밖이므로 사본만)**

```bash
mkdir -p .claude/skills/term-benchmark
cp ~/.claude/skills/term-benchmark/SKILL.md .claude/skills/term-benchmark/SKILL.md
git add .claude/skills/term-benchmark
git commit -m "[docs] : term-benchmark 스킬 사본 - 사람에게 묻는 절차"
```

---

# 사용자 작업만 모은 목록

에이전트가 대신할 수 없는 것들이다.

| Phase | 종류 | 내용 |
|---|---|---|
| ~~3~~ | ✅ | ~~애매와 모름의 경계~~ — 2026-08-29 확정. 확실 4~5개 / 애매 2~3개 / 모름 0~1개 |
| ~~3~~ | ✅ | ~~문항 수~~ — 2026-08-29 확정. 5문항 |
| 6 | ⚖ | 실제로 시험을 쳐 본다. 문항이 너무 쉽거나 어려운지 판정 |
| 6 | ❓ | 재시험 주기 — `UserMentalValue` 를 언제 다시 재는가 |
| 5 | ❓ | 확실로 판정된 용어의 표시 방법(흐리게 vs 접기) |

---

# 검증 명령 모음

```bash
cd $REPO_ROOT
npm test                                     # Node 테스트 전량
npm run typecheck                            # tsc --noEmit
.venv/bin/python -m pytest codegraph/ -q     # Python 테스트 전량
node --test test/term.test.mjs               # Mode 1.5 만
```

산출물 불변식:

```bash
grep -c '<script' out/report.html            # 1 이하여야 한다
```

---

# Self-Review

**1. 명세 커버리지** — 확정된 14개 결정 사항 대조:

| # | 결정 | 대응 Task |
|---|---|---|
| 1 | 3-mode 구조 | Task 0.2 (바이너리 3개) |
| 2 | 세 갈래가 사람의 이해 상태 | Task 3.1 (`gradeOne`) |
| 3 | LLM 추정 → 사용자 교정 | Task 6.1 (스킬 절차) |
| 4 | 객관식 + 모른다 선택지 | Task 6.1 (출제 규율), Task 3.1 (`dontKnow` 처리) |
| 5 | 정답률 80% 임계 | Task 3.1 |
| 6 | 출제 범위 = Plan 교차 | Task 2.1 (`pickTerms` + `findNewConcepts`) |
| 7 | Mode 1 WarmUp 전제 | Task 6.1 (전제 확인 단계) |
| 8 | 용어 DB 를 codegraph 에 | Task 1.1 |
| 9 | Plan 신규 개념은 저자가 | Task 2.1 출력 문구, Task 6.1 규율 |
| 10 | 산출물 두 갈래 | Task 4.1 |
| 11 | `{ TermMeans, UserMentalValue }` | Task 4.1 (`toTermsDb`) |
| 12 | 전부 싣되 표시를 달리 | Task 4.1 테스트, Task 5.1 |
| 13 | 바이너리 3개 | Task 0.2 |
| 14 | report-builder 안에 | 전 Task |

빠진 것 없음.

**2. 자리표시자 점검** — "TBD"·"적절한 처리"·"Task N 과 유사" 없음. 모든 코드 단계에 실제 코드가 있다. 단 **Task 3.1 의 구간 경계는 제안값**이며 그 사실을 명시했다.

**3. 타입 일관성** — `mental` 은 `"확실"|"애매"|"모름"` 으로 `src/types.ts`(Task 5.1)·`quiz.mjs`(Task 3.1)·`emit.mjs`(Task 4.1)에서 동일하다. `TermMeans`/`UserMentalValue` 는 `emit.mjs` 에서 정의되고 Task 5.2 주석에서 같은 이름으로 참조된다. `QUESTIONS_PER_TERM` 은 `quiz.mjs` 에서만 쓰인다.

**4. 남은 위험**

- **Task 1.1 의 `means` 가 너무 기계적일 수 있다.** `"render 모듈의 class. A, B 와 이어져 있다."` 는 정답지로 쓰기엔 빈약하다. 실제로 돌려 보고 부족하면 Mode 1.5 가 LLM 으로 보강하는 단계를 Phase 2 에 더한다.
- **Task 2.1 의 `pickTerms` 가 오탐을 낼 수 있다.** 흔한 이름(`Node`·`Data`)이 Plan 본문에 우연히 나오면 잡힌다. 실측 후 필요하면 코드 블록 안의 등장만 세도록 좁힌다.
- **Phase 0 이 기존 `report` 사용자를 끊을 수 있다.** Task 0.2 Step 4 의 위임으로 막았고 Step 6 에서 확인한다.
