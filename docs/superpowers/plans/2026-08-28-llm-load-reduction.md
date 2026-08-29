# Track C — LLM 전수조사 부담 감축 조사·구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 위키 생성의 LLM 토큰 소모와 판단 책임을 줄인다 — 정적 계층이 낼 수 있는 사실을 LLM 이 다시 읽지 않게 하고, 한 번 읽은 이해는 git 기반 증분으로 재사용한다.

**Architecture:** 세 갈래를 순서대로 붙인다. ① `calls[]` 로 정적 계층을 넓혀 LLM 이 읽을 이유 자체를 줄인다 → ② 파일별 이해 요약을 캐시하고 git 으로 무효화해 재실행 비용을 없앤다 → ③ 모듈을 중요도로 2계층(싸게/정독)으로 갈라 정독 대상을 소수로 제한한다. 각 갈래는 앞 갈래 없이도 이득이 나므로 독립 커밋이 가능하다.

**Tech Stack:** Python 3.14 (`.venv`) · Roslyn(`Microsoft.CodeAnalysis.CSharp` 5.9) · clang-uml 0.6.3 · networkx · pytest 9.1 · git plumbing(`ls-tree`/`diff --name-only`)

---

## 착수 전 실측 근거 (2026-08-28, StickRushGame `bf54917`)

이 계획 전체가 아래 네 수치 위에 서 있다. **재현 명령을 함께 적는다.**

| # | 실측 | 값 |
|---|---|---|
| M1 | 위키 인용 745건 중 **정적 계층이 이미 아는 위치** | **616 (82.7%)** |
| M2 | 구현 본문을 읽어야 아는 곳 | 129 (17.3%) — 그중 **호출식 64** · 선언 16 · 주석 18 · 기타 31 |
| M3 | 사용자 코드 규모 / 서드파티(안 읽음) | 114파일 8,456줄 / 1,599파일 262,096줄 |
| M4 | **1커밋당 바뀌는 사용자 `.cs`** | **2 / 114 (1.8%)** (2커밋 3개, 5커밋 94개) |
| M5 | 확인된 에이전트 토큰(4개) | 624K (Data 150K · Utils 174K · Interface 130K · 소형4종 170K) |

**M1+M2 가 이 계획의 논거다.** 8,456줄을 읽어 만든 서술의 82.7% 는 이미 `codegraph.json` /
`roslyn-dump.json` 에 있던 정보를 가리킨다 — LLM 이 그것을 **다시** 읽었다.
남은 17.3% 중 **절반(64건)은 호출식**이고, 그것은 Track C §7 이 "나중에 붙일 자리" 로
미뤄 둔 `calls[]` 다. 즉 전수조사는 불가피한 것이 아니라 **정적 계층이 안 내고 있어서** 발생했다.

**M4 가 WarmUp 의 논거다.** 일상 커밋 1개에 바뀌는 파일이 2개뿐이므로, 파일별 캐시가 있으면
재실행 비용이 1.8% 로 떨어진다. (5커밋 94개는 Unity 6 업그레이드 같은 대규모 커밋이 섞인 결과다 —
그런 회차는 캐시가 대부분 무효화되는 것이 **정상**이고, 그때는 전체 재생성이 맞다.)

### 사용자 확정 사항 (2026-08-28)

| ID | 결정 |
|---|---|
| U1 | 목적은 **비용·속도와 정확성 둘 다.** 하나의 원인(LLM 이 구현 본문을 읽는 것)에서 나온다고 본다 |
| U2 | **계층화 허용** — 모든 모듈은 구조·시그니처로 싸게, **중요한 소수만** 구현 정독 |
| U3 | 코드 규약은 **검증 가능한 것만** 받는다 (기계가 어긋남을 잡아낼 수 있는 형식) |
| U4 | WarmUp 캐시 단위는 **파일별 이해 요약(중간 산물)** |
| U5 | **`codegraph.json` 스키마 확장 허용** — M1 을 근거로 `calls[]` 재검토 |
| U6 | 캐시 무효화는 **git 기반**으로 검토 (사용자 착안) |

### 재현 명령

```bash
cd $REPO_ROOT
CS=$CSHARP_REPO

# M1·M2 — 인용이 가리키는 곳의 분류
.venv/bin/python codegraph/measure_citation_origin.py "$CS"      # Task 1 에서 만든다

# M4 — 커밋당 변경 파일 수
git -C "$CS" diff --name-only HEAD~1..HEAD -- 'Assets/@Scripts/*.cs' 'Assets/@Editors/*.cs' | wc -l
```

---

## File Structure

| 파일 | 책임 | 신규/수정 |
|---|---|---|
| `codegraph/measure_citation_origin.py` | 위키 인용이 어디를 가리키는지 분류. **모든 이득 주장의 계측기** | 신규 |
| `codegraph/roslyn-dump/Program.cs` | `calls[]` 추출 추가 (F15) | 수정 |
| `codegraph/normalize.py` | `calls[]` 통과 + `nodes[].members` 없이 유지 | 수정 |
| `codegraph/facts.py` | `facts/calls.md` 추가 · 계층 분류(`tier`) 열 | 수정 |
| `codegraph/warmup.py` | 파일별 이해 요약 캐시 + git 무효화 | 신규 |
| `codegraph/test_normalize.py` | 위 전부의 회귀 | 수정 |
| `docs/handoffs/HANDOFF-codebase-wiki.md` | C-19~C-21 결정 기록 | 수정 |
| `docs/handoffs/DECISION-csharp-intermediate-format.md` | F15 형식 확장 기록 | 수정 |

**분리 이유** — `warmup.py` 는 캐시 수명·무효화만 맡고 요약 생성은 하지 않는다(요약은 LLM 이
낸다). `measure_citation_origin.py` 를 먼저 만드는 것은 **이득을 수치로 말하기 위해서**다.
계측기 없이 "줄었다" 고 쓰면 이 파이프라인이 잡으려는 실패를 우리가 저지르는 것이다.

---

## Task 1: 계측기 — 인용이 어디서 오는지 분류한다

이후 모든 Task 의 이득을 이 도구로 잰다. **먼저 만든다.**

**Files:**
- Create: `codegraph/measure_citation_origin.py`
- Test: `codegraph/test_normalize.py` (추가)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`codegraph/test_normalize.py` 끝에 추가:

```python
# ── 8. 계측기 — 인용 출처 분류
def test_citation_origin_categories_are_total():
    """분류가 전수여야 한다 — 합이 전체 인용 수와 같지 않으면 어딘가 빠뜨린 것이다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import measure_citation_origin as M
    wiki = os.path.join(CS_REPO, "out/codegraph-raw/wiki")
    if not os.path.isdir(wiki):
        pytest.skip("위키 없음")
    r = M.measure(CS_REPO)
    assert r["total"] == sum(r["by_category"].values())
    assert r["total"] > 0


def test_citation_origin_static_share_is_measured():
    """정적 계층이 아는 비중이 나와야 한다. 착수 시점 실측은 82.7% 다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import measure_citation_origin as M
    wiki = os.path.join(CS_REPO, "out/codegraph-raw/wiki")
    if not os.path.isdir(wiki):
        pytest.skip("위키 없음")
    r = M.measure(CS_REPO)
    assert 0.0 <= r["static_share"] <= 1.0
    assert r["static_share"] > 0.5      # 착수 시점 0.827
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k citation_origin -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'measure_citation_origin'`

- [ ] **Step 3: 계측기를 만든다**

`codegraph/measure_citation_origin.py`:

```python
#!/usr/bin/env python3
"""measure_citation_origin.py — 위키 인용이 어디서 오는지 분류한다.

**이 파이프라인의 모든 "줄였다" 주장은 이 도구로 잰다.** 계측기 없이 이득을 말하면
Track C 가 잡으려는 실패(근거 없는 단정)를 우리가 저지르는 것이다.

  정적 계층이 아는 곳  = 노드 선언 · 간선(관계) · 멤버/메서드 선언
  본문을 읽어야 아는 곳 = 그 밖 — 호출식 · 주석 · 스키마 미수록 선언 · 기타

  measure_citation_origin.py <저장소> [--json]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_citations as V

STATIC = ("선언(노드)", "간선(관계)", "멤버·메서드 선언")
DECL_RE = re.compile(r"^(public|private|protected|internal|partial|abstract|static|\[)")
CALL_RE = re.compile(r"\w+\s*\(")


def measure(repo, wiki=None, codegraph=None, detail=None):
    repo = os.path.abspath(os.path.expanduser(repo))
    raw = os.path.join(repo, "out/codegraph-raw")
    wiki = wiki or os.path.join(raw, "wiki")
    codegraph = codegraph or os.path.join(raw, "codegraph.json")
    detail = detail or os.path.join(raw, "roslyn-dump.json")

    _, nodes, owns = V.build_index(codegraph)
    flesh = V.load_detail_index(detail) if os.path.isfile(detail) else {}

    cat = Counter()
    src_cache = {}

    def lines_of(p):
        if p not in src_cache:
            try:
                src_cache[p] = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                src_cache[p] = None
        return src_cache[p]

    for f in sorted(os.listdir(wiki)):
        if not f.endswith(".md"):
            continue
        for raw_line in open(os.path.join(wiki, f), encoding="utf-8"):
            for m in V.CITE.finditer(raw_line):
                loc = (m.group(1), int(m.group(2)))
                if loc in nodes:
                    cat["선언(노드)"] += 1
                elif loc in owns:
                    cat["간선(관계)"] += 1
                elif loc in flesh:
                    cat["멤버·메서드 선언"] += 1
                else:
                    content = lines_of(os.path.join(repo, loc[0]))
                    if content is None:
                        cat["비소스(facts 등)"] += 1
                        continue
                    t = content[loc[1] - 1].strip() if 0 < loc[1] <= len(content) else ""
                    if DECL_RE.match(t):
                        cat["선언(스키마 미수록)"] += 1
                    elif t.startswith("//") or t.startswith("*"):
                        cat["주석"] += 1
                    elif CALL_RE.search(t):
                        cat["호출식"] += 1
                    else:
                        cat["기타 본문"] += 1

    total = sum(cat.values())
    static = sum(cat[k] for k in STATIC)
    return {
        "repo": repo,
        "total": total,
        "by_category": dict(cat),
        "static": static,
        "static_share": (static / total) if total else 0.0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = measure(a.repo)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print(f"위키 인용 {r['total']}건이 가리키는 곳:\n")
    for k, v in sorted(r["by_category"].items(), key=lambda x: -x[1]):
        mark = "정적" if k in STATIC else "본문"
        print(f"  [{mark}] {k:22s} {v:4d}  ({v / r['total'] * 100:4.1f}%)")
    print(f"\n  정적 계층이 이미 아는 위치: {r['static']} ({r['static_share'] * 100:.1f}%)")
    print(f"  본문을 읽어야 아는 곳     : {r['total'] - r['static']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k citation_origin -q`
Expected: PASS (2 passed)

- [ ] **Step 5: 착수 시점 수치를 기록한다**

```bash
.venv/bin/python codegraph/measure_citation_origin.py $CSHARP_REPO --json \
  > docs/superpowers/plans/baseline-citation-origin.json
cat docs/superpowers/plans/baseline-citation-origin.json
```

Expected: `"static_share"` 가 0.82~0.83 부근

- [ ] **Step 6: 커밋**

```bash
git add codegraph/measure_citation_origin.py codegraph/test_normalize.py \
        docs/superpowers/plans/baseline-citation-origin.json
git commit -m "[feature] : 인용 출처 계측기와 착수 시점 기준선"
```

---

## Task 2: `roslyn-dump` 에 `calls[]` 추가 (C# 정적 계층 확장)

M2 의 호출식 64건이 이 Task 의 대상이다. **Track C §7 이 금지한 것은 `codegraph.json` 의
`calls[]` 이고, `roslyn-dump.json` 은 우리 형식이다** — `members[]`/`methods[]` 를 넣을 때와 같은 논거.

**Files:**
- Modify: `codegraph/roslyn-dump/Program.cs`
- Test: `codegraph/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`codegraph/test_normalize.py` 끝에 추가:

```python
# ── 9. calls[] — 호출 관계 (F15)
def test_roslyn_dump_emits_calls():
    """호출식이 calls[] 로 나와야 한다. M2 실측 — 위키 본문 인용 129건 중 64건이 호출식이다."""
    p = os.path.join(CS_REPO, "out/codegraph-raw/roslyn-dump.json")
    if not os.path.isfile(p):
        pytest.skip("roslyn-dump 산출물 없음")
    d = json.load(open(p, encoding="utf-8"))
    assert "calls" in d, "calls[] 가 없다 — Program.cs 가 아직 v3 가 아니다"
    assert len(d["calls"]) > 0
    c = d["calls"][0]
    for key in ("src", "member", "receiver", "method", "file", "line"):
        assert key in c, f"calls[] 레코드에 {key} 가 없다"


def test_roslyn_dump_calls_have_locations():
    """호출은 위치가 있어야 인용 검증 대상이 된다."""
    p = os.path.join(CS_REPO, "out/codegraph-raw/roslyn-dump.json")
    if not os.path.isfile(p):
        pytest.skip("roslyn-dump 산출물 없음")
    d = json.load(open(p, encoding="utf-8"))
    calls = d.get("calls") or []
    if not calls:
        pytest.skip("calls 미생성")
    assert all(c.get("file") and c.get("line") for c in calls)
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k roslyn_dump_emits_calls -q`
Expected: FAIL — `AssertionError: calls[] 가 없다 — Program.cs 가 아직 v3 가 아니다`

- [ ] **Step 3: `Program.cs` 에 호출 수집을 더한다**

`codegraph/roslyn-dump/Program.cs` — `depend` 의 `local`/`new` 를 걷는 구문 순회 루프 안,
`BaseObjectCreationExpressionSyntax` 처리 **바로 뒤**에 추가한다:

```csharp
    // ── calls[] (F15) — 호출 관계. depend 와 다른 축이라 relations 가 아니라 별도 배열이다.
    //   ⚠ 간선이 아니다. codegraph.json 의 edges[] 로 승격하지 않는다(Track C §7).
    //   위키가 "A 가 B.C() 를 부른다" 를 쓸 때 인용 검증 L3 가 성립하게 하는 것이 목적이다.
    foreach (var inv in root.DescendantNodes().OfType<InvocationExpressionSyntax>())
    {
        var sym = sm.GetSymbolInfo(inv).Symbol as IMethodSymbol;
        var sid = EnclosingTypeId(inv);
        if (sym == null || sid == null) { if (sym == null) unresolvedCalls++; continue; }
        var (cf, cl) = Loc(inv);
        callRecs.Add(new CallRec
        {
            Src = sid,
            Member = EnclosingMember(inv),
            Receiver = sym.ContainingType?.ToDisplayString(NameFmt),
            ReceiverAssembly = sym.ContainingType?.ContainingAssembly?.Name,
            Method = sym.Name,
            File = cf,
            Line = cl,
        });
    }
```

같은 파일 맨 위 `int unresolved = 0;` 아래에 추가:

```csharp
int unresolvedCalls = 0;
var callRecs = new List<CallRec>();
```

`Dump` 클래스에 필드를 추가:

```csharp
    [JsonPropertyName("calls")] public List<CallRec>? Calls { get; set; }
```

레코드 클래스를 파일 끝에 추가:

```csharp
class CallRec
{
    [JsonPropertyName("src")] public string Src { get; set; } = "";
    [JsonPropertyName("member")] public string? Member { get; set; }
    [JsonPropertyName("receiver")] public string? Receiver { get; set; }
    [JsonPropertyName("receiver_assembly")] public string? ReceiverAssembly { get; set; }
    [JsonPropertyName("method")] public string? Method { get; set; }
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("line")] public int? Line { get; set; }
}
```

`dump` 객체 생성부에 `Calls = callRecs,` 를 더하고, 요약 출력에 한 줄 추가:

```csharp
Console.WriteLine($"  calls {callRecs.Count} (심볼 해석 실패 {unresolvedCalls})");
```

- [ ] **Step 4: 빌드하고 실행한다**

```bash
cd $REPO_ROOT
dotnet build codegraph/roslyn-dump 2>&1 | grep -E "error|경고 0개"
dotnet run --project codegraph/roslyn-dump -- $CSHARP_REPO
```

Expected: `calls 1200~1300` 부근 (probe 실측 — 호출식 1,295건 중 해석 성공 1,288)

- [ ] **Step 5: 회귀를 확인한다 — 구조 수치가 하나도 바뀌면 안 된다**

Run:
```bash
.venv/bin/python codegraph/normalize.py \
  --roslyn-dump $CSHARP_REPO/out/codegraph-raw/roslyn-dump.json \
  --repo $CSHARP_REPO \
  -o $CSHARP_REPO/out/codegraph-raw/codegraph.json
.venv/bin/pytest codegraph/test_normalize.py -q
```

Expected: `노드 231 / 간선 540 / 모듈 10` 그대로, 테스트 전부 PASS
(`calls[]` 는 `relations[]` 가 아니므로 정규화 결과가 바뀌면 안 된다)

- [ ] **Step 6: 커밋**

```bash
git add codegraph/roslyn-dump/Program.cs codegraph/test_normalize.py
git commit -m "[feature] : roslyn-dump 호출 관계 수집"
```

---

## Task 3: 검증기가 `calls[]` 를 판정 대상에 넣는다

`calls[]` 를 뽑아도 검증기가 모르면 호출식 인용은 계속 "근거 없음" 에 떨어진다.

**Files:**
- Modify: `codegraph/verify_citations.py`
- Test: `codegraph/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
def test_verifier_recognizes_call_sites(tmp_path):
    """호출식 인용이 '근거 없음' 이 아니라 '호출' 로 판정돼야 한다."""
    R = os.path.join(CS_REPO, "out/codegraph-raw")
    if not os.path.isfile(os.path.join(R, "roslyn-dump.json")):
        pytest.skip("산출물 없음")
    d = json.load(open(os.path.join(R, "roslyn-dump.json"), encoding="utf-8"))
    calls = d.get("calls") or []
    if not calls:
        pytest.skip("calls 미생성")
    c = calls[0]
    body = f"어떤 주장이다 ({c['file']}:{c['line']}).\n"
    out = _run_verifier(tmp_path, body, CS_REPO,
                        os.path.join(R, "codegraph.json"),
                        os.path.join(R, "roslyn-dump.json"))
    assert "근거없음 0" in out, out
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k recognizes_call_sites -q`
Expected: FAIL — `근거없음 1` 이 나온다

- [ ] **Step 3: 검증기에 호출 색인을 더한다**

`codegraph/verify_citations.py` 의 `load_detail_index` 끝(`return idx` 직전)에 추가:

```python
    # calls[] (F15) — 호출식도 근거가 있는 위치다. C-16 이 "위치 있는 간선 전부" 로 넓힌 것과
    # 같은 논리로, 위치가 있는 호출은 판정 대상이 된다.
    for c in d.get("calls") or []:
        if c.get("file") and c.get("line"):
            idx.setdefault((c["file"], c["line"]), []).append(
                f"{short(c.get('receiver') or '?')}.{c.get('method')}")
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -q`
Expected: 전부 PASS

- [ ] **Step 5: 이득을 잰다 — 계측기로**

```bash
.venv/bin/python codegraph/measure_citation_origin.py $CSHARP_REPO
```

Expected: `static_share` 가 82.7% 에서 상승. **수치를 그대로 기록한다** — 오르지 않으면
`calls[]` 가 위키의 호출식 인용과 위치가 어긋난다는 뜻이므로 원인을 적고 멈춘다.

- [ ] **Step 6: 커밋**

```bash
git add codegraph/verify_citations.py codegraph/test_normalize.py
git commit -m "[feature] : 인용 검증기 호출식 판정"
```

---

## Task 4: `facts/calls.md` — LLM 이 읽지 않고도 호출을 알게 한다

`calls[]` 가 있어도 위키 작성자에게 주지 않으면 여전히 소스를 읽는다. C-3(입력 주입)의 재료를 늘린다.

**Files:**
- Modify: `codegraph/facts.py`
- Test: `codegraph/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
def test_facts_calls_md_generated():
    """facts/calls.md 가 생성되고 인용 형식을 쓴다."""
    p = os.path.join(CS_REPO, "out/codegraph-raw/facts/calls.md")
    if not os.path.isfile(os.path.join(CS_REPO, "out/codegraph-raw/roslyn-dump.json")):
        pytest.skip("산출물 없음")
    assert os.path.isfile(p), "facts/calls.md 가 없다"
    text = open(p, encoding="utf-8").read()
    assert "(Assets/" in text, "로컬 인용 규격이 아니다"
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k facts_calls -q`
Expected: FAIL — `facts/calls.md 가 없다`

- [ ] **Step 3: `facts.py` 에 호출 표를 더한다**

`codegraph/facts.py` 의 `main()` 안, `facts/hotspot.md` 를 쓰는 블록 **앞**에 추가:

```python
    # ── facts/calls.md — 호출 관계 (F15). LLM 이 구현 본문을 읽지 않고도
    #    "A 가 B.C() 를 부른다" 를 인용과 함께 쓸 수 있게 하는 것이 목적이다.
    if a.detail and os.path.isfile(a.detail):
        dump = json.load(open(a.detail, encoding="utf-8"))
        calls = dump.get("calls") or []
        tyname = {t["id"]: t["name"] for t in dump.get("types", [])}
        L = [f"# 호출 관계 — {lang} ({commit})", "", HEAD_NOTE]
        if not calls:
            L.append("(`calls[]` 없음 — roslyn-dump v3 이상이 필요하다)")
        else:
            first = [c for c in calls
                     if (c.get("receiver_assembly") == dump["compilation"]["assembly"])]
            L.append(f"호출식 {len(calls)}건 중 **1차 코드끼리 {len(first)}건**. "
                     f"외부 호출은 C-9 로 접히므로 표에 올리지 않는다.")
            L.append("")
            L.append("| 호출하는 타입 | 안에서 | 호출 대상 | 위치 |")
            L.append("|---|---|---|---|")
            for c in sorted(first, key=lambda x: (x.get("file") or "", x.get("line") or 0)):
                src = tyname.get(c["src"], c["src"]).split(".")[-1]
                L.append(f"| {src} | {c.get('member') or '?'} | "
                         f"{(c.get('receiver') or '?').split('.')[-1]}.{c.get('method')} | "
                         f"({c.get('file')}:{c.get('line')}) |")
        open(os.path.join(fdir, "calls.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
```

- [ ] **Step 4: 실행하고 테스트한다**

```bash
CS=$CSHARP_REPO
.venv/bin/python codegraph/facts.py "$CS/out/codegraph-raw/codegraph.json" --repo "$CS" \
  --detail "$CS/out/codegraph-raw/roslyn-dump.json"
.venv/bin/pytest codegraph/test_normalize.py -k facts_calls -q
```

Expected: PASS. `facts/calls.md` 에 1차 호출 표가 생긴다.

- [ ] **Step 5: 커밋**

```bash
git add codegraph/facts.py codegraph/test_normalize.py
git commit -m "[feature] : facts 호출 관계 표"
```

---

## Task 5: WarmUp 캐시 — 파일별 이해 요약 + git 무효화

> # 🔴 대체됨 — `docs/handoffs/HANDOFF-2026-08-29-warmup-incremental-cache.md` 를 따르라
>
> **이 절의 무효화 방식에 결함이 있다.** `git ls-tree HEAD` 의 blob SHA 는 **커밋된 내용**이라,
> 작업 트리를 고쳐 놓고 커밋하지 않은 상태에서 돌리면 "유효" 로 판정되어 낡은 요약을 재사용한다.
> 개발 중에 가장 흔한 상태가 바로 그 상태다. 새 핸드오프는 **파일 내용을 직접 해싱**한다.
>
> **살아 있는 부분** — `blast_radius()`(의존 간선 양방향 1홉). 파일 단위 캐시가 못 잡는
> "A 는 안 바뀌었는데 B 때문에 A 의 서술이 틀려지는" 경우를 그것이 맡는다. 새 핸드오프가 가져다 쓴다.
> **죽은 부분** — `blob_hashes()` · `status()` 의 3값 판정 · Step 1~4 의 시험 코드.

U4·U6 의 구현. **캐시가 요약을 만들지 않는다** — 요약은 LLM 이 내고, 이 도구는 수명과 무효화만 맡는다.

**Files:**
- Create: `codegraph/warmup.py`
- Test: `codegraph/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
# ── 10. WarmUp 캐시
def test_warmup_blob_hash_from_git():
    """파일 해시를 직접 계산하지 않는다 — git 이 이미 blob SHA 를 갖고 있다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import warmup as W
    if not os.path.isdir(os.path.join(CS_REPO, ".git")):
        pytest.skip("git 저장소 아님")
    blobs = W.blob_hashes(CS_REPO, ["Assets/@Scripts/Managers/Managers.cs"])
    assert "Assets/@Scripts/Managers/Managers.cs" in blobs
    assert len(blobs["Assets/@Scripts/Managers/Managers.cs"]) == 40


def test_warmup_stale_detection_is_three_valued(tmp_path):
    """유효 / 낡음 / 판정불가 세 값이다 — 검증기와 같은 태도."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import warmup as W
    cache = tmp_path / "warmup.json"
    W.save(str(cache), CS_REPO, {"Assets/@Scripts/Managers/Managers.cs": "요약 본문"})
    st = W.status(str(cache), CS_REPO)
    assert set(st) == {"유효", "낡음", "판정불가"}
    assert "Assets/@Scripts/Managers/Managers.cs" in st["유효"]


def test_warmup_detects_change_via_blob(tmp_path):
    """blob SHA 가 바뀌면 낡음으로 잡힌다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import warmup as W
    cache = tmp_path / "warmup.json"
    W.save(str(cache), CS_REPO, {"Assets/@Scripts/Managers/Managers.cs": "요약"})
    data = json.load(open(cache, encoding="utf-8"))
    data["files"]["Assets/@Scripts/Managers/Managers.cs"]["blob"] = "0" * 40
    json.dump(data, open(cache, "w", encoding="utf-8"))
    st = W.status(str(cache), CS_REPO)
    assert "Assets/@Scripts/Managers/Managers.cs" in st["낡음"]
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k warmup -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'warmup'`

- [ ] **Step 3: `warmup.py` 를 만든다**

```python
#!/usr/bin/env python3
"""warmup.py — 파일별 이해 요약 캐시와 git 기반 무효화 (U4·U6).

**이 도구는 요약을 만들지 않는다.** 요약은 LLM 이 내고, 여기는 **수명과 무효화**만 맡는다.
그 분리가 이 계획의 요점이다 — 판단은 LLM, 판정은 기계.

무효화는 git 에 맡긴다. 내용 해시를 직접 계산하지 않는다 —
`git ls-tree` 의 blob SHA 가 이미 내용 해시이고 공짜다.

  유효     캐시의 blob SHA == 현재 blob SHA
  낡음     다르다 → 그 파일만 재요약하면 된다
  판정불가 git 이 그 경로를 모른다(미추적·삭제) → 사람이 본다

⚠ **git 이 못 잡는 것이 하나 있다.** 파일 A 는 안 바뀌었는데 A 를 서술한 페이지가 B 의 변경
때문에 틀려지는 경우다. 그것은 `codegraph.json` 의 의존 간선이 푼다 — `blast_radius()` 참조.

  warmup.py status <캐시.json> --repo <저장소>
  warmup.py blast  <캐시.json> --repo <저장소> --codegraph <codegraph.json>
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict


def blob_hashes(repo, paths=None):
    """git 이 이미 갖고 있는 blob SHA 를 읽는다. 우리가 해싱하지 않는다."""
    cmd = ["git", "ls-tree", "-r", "HEAD", "--"] + (list(paths) if paths else [])
    r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    out = {}
    if r.returncode != 0:
        return out
    for line in r.stdout.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 3:
            out[path] = parts[2]
    return out


def head_commit(repo):
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def save(cache_path, repo, summaries):
    """summaries: {상대경로: 요약문}. blob SHA 를 함께 박아 둔다."""
    repo = os.path.abspath(os.path.expanduser(repo))
    blobs = blob_hashes(repo, list(summaries))
    data = {
        "repo_commit": head_commit(repo),
        "files": {p: {"blob": blobs.get(p), "summary": s} for p, s in summaries.items()},
    }
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    json.dump(data, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return data


def status(cache_path, repo):
    """3값 판정 — 유효 / 낡음 / 판정불가."""
    repo = os.path.abspath(os.path.expanduser(repo))
    data = json.load(open(cache_path, encoding="utf-8"))
    files = data.get("files", {})
    now = blob_hashes(repo, list(files))
    out = {"유효": [], "낡음": [], "판정불가": []}
    for p, rec in files.items():
        cur = now.get(p)
        if cur is None:
            out["판정불가"].append(p)
        elif cur == rec.get("blob"):
            out["유효"].append(p)
        else:
            out["낡음"].append(p)
    return out


def blast_radius(codegraph, changed_files, hops=1):
    """바뀐 파일이 영향을 주는 파일 집합. git 이 못 잡는 전이 오염을 여기서 잡는다.

    codegraph 의 간선을 **양방향으로** 타고 hops 만큼 퍼뜨린다 —
    A 가 B 를 쓰는데 B 가 바뀌면 A 의 서술이 틀려질 수 있고, 그 반대도 마찬가지다.
    """
    g = json.load(open(codegraph, encoding="utf-8"))
    nid = {n["id"]: n for n in g["nodes"]}
    adj = defaultdict(set)
    for e in g["edges"]:
        a, b = nid.get(e["from"]), nid.get(e["to"])
        if not a or not b or not a.get("file") or not b.get("file"):
            continue
        adj[a["file"]].add(b["file"])
        adj[b["file"]].add(a["file"])
    frontier = set(changed_files)
    seen = set(frontier)
    for _ in range(hops):
        nxt = set()
        for f in frontier:
            nxt |= adj.get(f, set())
        frontier = nxt - seen
        seen |= frontier
    return sorted(seen)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["status", "blast"])
    ap.add_argument("cache")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--codegraph")
    ap.add_argument("--hops", type=int, default=1)
    a = ap.parse_args()

    st = status(a.cache, a.repo)
    total = sum(len(v) for v in st.values())
    print(f"캐시 {total}개 — 유효 {len(st['유효'])} · 낡음 {len(st['낡음'])} · "
          f"판정불가 {len(st['판정불가'])}")
    for p in st["낡음"][:10]:
        print(f"  낡음: {p}")
    for p in st["판정불가"][:10]:
        print(f"  판정불가: {p}")

    if a.action == "blast":
        if not a.codegraph:
            print("--codegraph 가 필요하다", file=sys.stderr)
            return 1
        r = blast_radius(a.codegraph, st["낡음"], a.hops)
        print(f"\n파급 범위({a.hops}홉): {len(r)}개 파일 — 재요약 대상")
        for p in r[:15]:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k warmup -q`
Expected: PASS (3 passed)

- [ ] **Step 5: 증분 이득을 실측한다**

```bash
CS=$CSHARP_REPO
.venv/bin/python - <<'EOF'
import os, sys, subprocess
sys.path.insert(0, "codegraph"); import warmup as W
CS = os.path.expanduser("$CSHARP_REPO")
files = subprocess.run(["git","ls-files","Assets/@Scripts/*.cs","Assets/@Editors/*.cs"],
                       cwd=CS, capture_output=True, text=True).stdout.split()
W.save("/tmp/warm.json", CS, {f: "(요약 자리)" for f in files})
changed = subprocess.run(["git","diff","--name-only","HEAD~1..HEAD","--",
                          "Assets/@Scripts","Assets/@Editors"],
                         cwd=CS, capture_output=True, text=True).stdout.split()
r = W.blast_radius(f"{CS}/out/codegraph-raw/codegraph.json", changed, hops=1)
print(f"전체 {len(files)} / 1커밋 변경 {len(changed)} / 파급 1홉 {len(r)}")
print(f"재요약 비율: {len(r)/len(files)*100:.1f}%")
EOF
```

Expected: 재요약 비율이 100% 보다 크게 작다. **수치를 기록한다** —
M4 기준 변경 2개이므로 파급 1홉이 20개를 크게 넘으면 `hops=0`(직접 의존만) 을 검토한다.

- [ ] **Step 6: 커밋**

```bash
git add codegraph/warmup.py codegraph/test_normalize.py
git commit -m "[feature] : warmup 캐시와 git 기반 무효화"
```

---

## Task 6: 계층 분류 — 정독 대상을 소수로 제한한다 (U2)

**Files:**
- Modify: `codegraph/facts.py`
- Test: `codegraph/test_normalize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
# ── 11. 계층화 (U2)
def test_facts_modules_have_tier():
    """모듈마다 정독/개요 계층이 붙어야 한다."""
    p = os.path.join(CS_REPO, "out/codegraph-raw/ranking.json")
    if not os.path.isfile(p):
        pytest.skip("산출물 없음")
    r = json.load(open(p, encoding="utf-8"))
    assert all("tier" in m for m in r["modules"]), "modules[] 에 tier 가 없다"
    tiers = {m["tier"] for m in r["modules"]}
    assert tiers <= {"정독", "개요"}
    assert "정독" in tiers and "개요" in tiers, "전부 한 계층이면 분류가 의미 없다"
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `.venv/bin/pytest codegraph/test_normalize.py -k modules_have_tier -q`
Expected: FAIL — `modules[] 에 tier 가 없다`

- [ ] **Step 3: `facts.py` 에 계층 분류를 더한다**

`codegraph/facts.py` 의 `ranking` 딕셔너리를 만드는 부분에서 `modules` 계산을 교체한다.
기존:

```python
        "modules": sorted(
            [{"id": m, "classes": mod_cnt[m], "pagerank_sum": round(mod_pr[m], 6),
              "in_cycle": m in cyc_mods} for m in mod_cnt],
            key=lambda x: -x["pagerank_sum"]),
```

새로:

```python
        "modules": _tier(sorted(
            [{"id": m, "classes": mod_cnt[m], "pagerank_sum": round(mod_pr[m], 6),
              "in_cycle": m in cyc_mods} for m in mod_cnt],
            key=lambda x: -x["pagerank_sum"]), hs_code),
```

같은 파일 상단(`HEAD_NOTE` 아래)에 함수를 추가:

```python
# ── 계층 분류 (U2) — 정독 대상을 소수로 제한한다.
#    기준은 이미 계산된 것만 쓴다: PageRank 누적 · 순환 참여 · hotspot 상위.
#    ⚠ **도구는 "무엇을 생략할지" 를 정하지 않는다.** 그것은 Track C §1 20번으로 LLM 몫이다.
#    여기서 정하는 것은 "어느 모듈에 정독 예산을 쓸 것인가" 하나다.
TIER_PAGERANK_COVER = 0.60   # PageRank 누적 60% 까지가 정독 후보


def _tier(modules, hs_code):
    hot = {h["module"] for h in (hs_code or [])[:10]}
    total = sum(m["pagerank_sum"] for m in modules) or 1.0
    acc = 0.0
    for m in modules:
        acc += m["pagerank_sum"]
        deep = (acc / total <= TIER_PAGERANK_COVER) or m["in_cycle"] or (m["id"] in hot)
        m["tier"] = "정독" if deep else "개요"
        m["tier_reason"] = " · ".join(filter(None, [
            "PageRank 상위" if acc / total <= TIER_PAGERANK_COVER else "",
            "순환 참여" if m["in_cycle"] else "",
            "hotspot 상위10" if m["id"] in hot else "",
        ])) or "해당 없음"
    return modules
```

`facts/modules.md` 의 표에도 열을 더한다. 기존 헤더 줄:

```python
    L.append("| 모듈 | 클래스 | PageRank 합 | 의존 대상 | 순환 참여 |")
    L.append("|---|---|---|---|---|")
```

를 다음으로 바꾸고:

```python
    L.append("| 모듈 | 계층 | 근거 | 클래스 | PageRank 합 | 의존 대상 | 순환 참여 |")
    L.append("|---|---|---|---|---|---|---|")
```

행 생성부를 다음으로 바꾼다:

```python
        L.append(f"| {m['id']} | {m['tier']} | {m['tier_reason']} | {m['classes']} | "
                 f"{m['pagerank_sum']} | {deps} | {'⚠ 예' if m['in_cycle'] else '아니오'} |")
```

- [ ] **Step 4: 실행하고 테스트한다**

```bash
CS=$CSHARP_REPO
.venv/bin/python codegraph/facts.py "$CS/out/codegraph-raw/codegraph.json" --repo "$CS" \
  --detail "$CS/out/codegraph-raw/roslyn-dump.json"
.venv/bin/pytest codegraph/test_normalize.py -k modules_have_tier -q
head -20 "$CS/out/codegraph-raw/facts/modules.md"
```

Expected: PASS. 정독 3~5개 / 개요 5~7개 부근. **어느 모듈이 어느 계층인지 기록한다.**

- [ ] **Step 5: 커밋**

```bash
git add codegraph/facts.py codegraph/test_normalize.py
git commit -m "[feature] : 모듈 정독 개요 계층 분류"
```

---

## Task 7: 이득 측정과 결정 기록

**Files:**
- Modify: `docs/handoffs/HANDOFF-codebase-wiki.md`
- Modify: `docs/handoffs/DECISION-csharp-intermediate-format.md`

- [ ] **Step 1: 착수 전후를 나란히 잰다**

```bash
cd $REPO_ROOT
CS=$CSHARP_REPO
echo "── 착수 시점 ──"; cat docs/superpowers/plans/baseline-citation-origin.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"  static_share {d['static_share']*100:.1f}%\")"
echo "── 현재 ──"; .venv/bin/python codegraph/measure_citation_origin.py "$CS"
```

Expected: `static_share` 상승. **오르지 않으면 원인을 §5 에 적고 멈춘다.**

- [ ] **Step 2: `DECISION-csharp-intermediate-format.md` 에 F15 를 기록한다**

`## 2. 확정 결정` 표 끝에 행을 추가:

```markdown
| **F15** | **`calls[]` 를 낸다** — 호출식의 `src` · `member` · `receiver` · `method` · `file` · `line`. **`relations[]` 가 아니라 별도 배열**이다 | 2026-08-28 사용자 확정(U5). 🔵 위키 본문 인용 129건 중 **64건이 호출식**이었다 — 정적 계층이 안 내서 LLM 이 본문을 읽고 있었다 |
```

- [ ] **Step 3: `HANDOFF-codebase-wiki.md` 에 C-19~C-21 을 기록한다**

`## 2. 확정된 결정` 표의 `C-18` 행 뒤에 추가:

```markdown
| C-19 | **`calls[]` 를 정적 계층에 넣는다** — `roslyn-dump.json` 에 담고 검증기·facts 가 소비한다. **`codegraph.json` 의 `edges[]` 로 승격하지 않는다** | 2026-08-28 사용자 확정(U5). §7 의 "나중에 붙일 자리" 를 붙일 근거가 실측으로 생겼다 — 인용 745건 중 82.7% 는 이미 정적 계층이 알고, 남은 17.3% 의 절반이 호출식이다 |
| C-20 | **WarmUp 캐시는 파일별 이해 요약 단위이고, 무효화는 git blob SHA 로 한다.** 판정은 **유효/낡음/판정불가 3값** | 2026-08-28 사용자 확정(U4·U6). 내용 해시를 직접 계산하지 않는다 — git 이 이미 갖고 있다. 🔵 1커밋당 사용자 `.cs` 변경 **2/114 (1.8%)** |
| C-21 | **모듈을 정독·개요 2계층으로 가른다.** 기준은 PageRank 누적 60% · 순환 참여 · hotspot 상위10 | 2026-08-28 사용자 확정(U2). ⚠ **도구는 "무엇을 생략할지" 를 정하지 않는다**(§1 20번은 LLM 몫). 정하는 것은 "정독 예산을 어디 쓸까" 하나다 |
```

- [ ] **Step 4: Phase 절을 추가한다**

`### Phase 6 — Windows 산출물로 검증` **앞**에 삽입:

```markdown
### Phase 11 — LLM 부담 감축 🔵 2026-08-28

**문제** — 위키 10장을 만드는 데 확인된 것만 624K 토큰이 들었고, 사용자 코드 8,456줄이 100% 읽혔다.

**진단(실측)** — 인용 745건 중 **616건(82.7%)이 이미 정적 계층이 아는 위치**를 가리킨다.
LLM 이 그것을 **다시** 읽었다. 남은 129건 중 **64건이 호출식**으로, §7 이 미뤄 둔 `calls[]` 다.
**전수조사는 불가피한 것이 아니라 정적 계층이 안 내고 있어서 발생했다.**

**처방 셋** — C-19(`calls[]`) · C-20(WarmUp) · C-21(계층화).
계측기는 `codegraph/measure_citation_origin.py` 이고 **모든 "줄였다" 주장은 이것으로 잰다.**

⚠ **서드파티는 원래부터 안 읽었다** — C-9 외부 접기가 262,096줄(96.9%)을 노드 17개로
눌렀고 LLM 은 근처도 가지 않았다. 감축 대상은 사용자 코드 8,456줄뿐이다.
```

- [ ] **Step 5: 회귀 전체를 돌린다**

```bash
.venv/bin/pytest codegraph/test_normalize.py -q
```

Expected: 전부 PASS

- [ ] **Step 6: 커밋**

```bash
git add docs/handoffs/HANDOFF-codebase-wiki.md docs/handoffs/DECISION-csharp-intermediate-format.md
git commit -m "[docs] : llm 부담 감축 결정과 실측 기록"
```

---

## Task 8: 실전 검증 — 한 모듈을 새 재료로 다시 써 본다

계획 전체가 실제로 이득을 내는지 **한 번 돌려서 확인한다.** 조기 성공 선언을 막는 단계다.

**Files:**
- Create: `<Unity저장소>/out/codegraph-raw/wiki-v2/interface.md` (에이전트 산출)

- [ ] **Step 1: 대상을 고른다**

`Interface` 모듈로 한다 — 소스 207줄로 작아 **정적 재료만으로 얼마나 되는지** 가장 선명하게 보인다.
기존 `wiki/interface.md`(330줄 · 인용 89건)가 대조군이다.

- [ ] **Step 2: 새 재료만 주고 다시 쓰게 한다**

`deep-wiki:wiki-writer` 서브에이전트에 다음을 준다. **소스 파일 읽기를 금지한다:**

```
`Interface` 모듈 위키를 아래 정적 재료만으로 작성하라. **소스 `.cs` 파일을 읽지 말 것.**
- out/codegraph-raw/facts/classes.md · modules.md · calls.md · entrypoints.md
- out/codegraph-raw/codegraph.json · roslyn-dump.json (members/methods 포함)
출력: out/codegraph-raw/wiki-v2/interface.md
읽을 수 없어 쓸 수 없는 것은 `(Unknown – verify in 경로)` 로 남겨라. **추측하지 말 것.**
```

- [ ] **Step 3: 두 판본을 비교한다**

```bash
CS=$CSHARP_REPO
for v in wiki wiki-v2; do
  f="$CS/out/codegraph-raw/$v/interface.md"
  [ -f "$f" ] || continue
  echo "── $v"
  .venv/bin/python codegraph/verify_citations.py "$f" --repo "$CS" \
    --codegraph "$CS/out/codegraph-raw/codegraph.json" \
    --detail "$CS/out/codegraph-raw/roslyn-dump.json" | head -5
  echo "  Unknown: $(grep -c 'Unknown – verify' "$f")"
done
```

- [ ] **Step 4: 판정한다**

표를 만들어 기록한다 — **토큰 · 인용 수 · 근거없음 · Unknown 수 · 서술 깊이**.

| | 기존(정독) | 신규(정적만) |
|---|---|---|
| 에이전트 토큰 | 130K | ? |
| 인용 / 근거없음 | 89 / ? | ? / ? |
| `Unknown` 표기 | 4 | ? |

**판정 기준** — 토큰이 절반 이하로 줄고 `Unknown` 이 5건 이내면 계층화가 성립한다.
`Unknown` 이 크게 늘면 **그 항목들이 정독이 필요한 진짜 대상**이고, 그것이 C-21 의
"정독" 계층이 무엇을 담아야 하는지 알려주는 실측이다.

⚠ **"성공" 이라고 쓰지 말 것.** 표본 1개다. 목표는 "명백한 반례가 없는가" 수준의 sanity check 이다.

- [ ] **Step 5: 결과를 기록하고 커밋한다**

`HANDOFF-codebase-wiki.md` Phase 11 절에 비교 표를 붙인다.

```bash
git add docs/handoffs/HANDOFF-codebase-wiki.md
git commit -m "[docs] : 정적 재료만으로 쓴 위키 대조 결과"
```

---

## 조사만 하고 구현하지 않는 것 — 기록만

| 항목 | 왜 지금 안 하나 |
|---|---|
| **C++ `calls[]`** | clang-uml 은 호출을 안 낸다. `clangd` 역방향 갈래(보류 중)나 별도 도구가 필요하다. **C# 에서 이득이 확인된 뒤에 검토한다** |
| **코드 규약(U3)** | 검증 가능한 규약만 받기로 했으나, `calls[]` 로 82.7% → ?% 가 오른 뒤에도 남는 격차를 보고 정해야 한다. **격차를 모르고 규약부터 만들면 거울 함정이다** |
| **요약 자동 검증** | 파일별 요약은 LLM 산물이라 인용 검증기로 재지 못한다. 요약에 인용을 강제하면 잴 수 있으나, 그 설계는 캐시 이득이 실측된 뒤에 |
| **서드파티 262,096줄** | 이미 C-9 가 막고 있다. 감축 대상이 아니다 |

---

## Self-Review

**1. 사용자 확정 사항 커버리지**

| | 대응 Task |
|---|---|
| U1 비용·속도·정확성 | Task 1(계측) · 2~4(정적 확장) · 5(캐시) |
| U2 계층화 | Task 6 · 8 |
| U3 검증 가능한 규약만 | **구현 없음 — "조사만 하고 구현하지 않는 것" 에 사유와 함께 기록** |
| U4 파일별 요약 캐시 | Task 5 |
| U5 스키마 확장 허용 | Task 2(F15) · Task 7(C-19) |
| U6 git 무효화 | Task 5 (`blob_hashes` · `status` · `blast_radius`) |

**2. 자리표시자 점검** — "TBD"·"적절한 처리"·"Task N 과 유사" 없음. 모든 코드 단계에 실제 코드가 있다.

**3. 타입 일관성** — `measure()` 는 Task 1 정의대로 Task 3·7 에서 호출된다.
`blob_hashes`/`status`/`blast_radius` 는 Task 5 정의와 테스트가 일치한다.
`_tier` 는 Task 6 안에서만 쓰인다. `CallRec` 의 필드명(`src`/`member`/`receiver`/`method`/
`file`/`line`)이 Task 2 테스트·Task 3 검증기·Task 4 facts 에서 동일하게 쓰인다.

**4. 남은 위험**

- Task 3 의 이득이 안 나올 수 있다 — 위키의 호출식 인용 줄과 `calls[]` 의 줄이 **어긋날** 수 있다
  (호출이 여러 줄에 걸치면 시작 줄이 다르다). Step 5 에서 수치로 확인하고, 안 오르면 멈춘다.
- Task 5 의 `blast_radius` 가 너무 넓을 수 있다. `hops=0` 폴백을 Step 5 에 적어 뒀다.
