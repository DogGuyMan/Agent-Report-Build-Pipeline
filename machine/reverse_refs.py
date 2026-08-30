#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='reverse_refs.py']"/>
# 1차 심볼을 누가 쓰고 있는지 전수로 뽑는 도구.
# 쓰는 것: Clangd · 쓰이는 곳: 없음
"""1차 심볼 전수 역참조를 뽑는다 (E6 + 전수 확정).

산출물은 엔진 중립이다 (E7 제약) — LSP 의 uri/range 를 내보내지 않고
{저장소 상대경로, line, col} 로 정규화한다.

⚠ clangd 는 색인이 덜 찬 상태에서 부분 결과를 **에러 없이** 돌려준다.
$/progress 의 end 를 기다린 뒤에만 질의한다.

사용:  python3 reverse_refs.py <repo_root> <compdb_dir> <clang_uml_json> <out_json>
"""
import json, shutil, subprocess, sys, time
from typing import Any, NotRequired, TypedDict
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from clangd_refs import Clangd, to_repo_relative

FIRST_PARTY_PREFIXES = ("SJH", "MyApp")


# ── 이 파일이 읽고 쓰는 두 JSON 의 모양. clang-uml 이 입력, reverse_refs/1 이 산출물이다.

class _SourceLocation(TypedDict):
    """clang-uml 이 적는 선언 자리. 줄·칸 모두 1-based 다."""
    file: str
    line: int
    column: int


class _UmlElement(TypedDict):
    """clang-uml 의 element 한 칸.

    `source_location` 이 필수인 것은 `main` 의 `targets` 가 그것이 없는 원소를
    `"source_location" in e` 로 이미 걸러 내기 때문이다.
    """
    id: str
    display_name: str
    namespace: NotRequired[str]
    is_nested: NotRequired[bool]
    source_location: _SourceLocation


class _Uml(TypedDict):
    elements: list[_UmlElement]


class _LspPosition(TypedDict):
    """LSP 좌표. 줄·칸 모두 0-based 라 산출물로 나갈 때 1을 더한다."""
    line: int
    character: int


class _LspRange(TypedDict):
    start: _LspPosition
    end: _LspPosition


class _LspLocation(TypedDict):
    uri: str
    range: _LspRange


class _Loc(TypedDict):
    """산출물의 자리 한 칸. uri/range 가 아니라 저장소 상대경로와 1-based 좌표다(E7)."""
    file: str
    line: int
    col: int


class _Symbol(TypedDict):
    id: str
    display_name: str
    is_nested: bool
    decl: _Loc
    refs: list[_Loc]


class _IndexStat(TypedDict):
    tu_total: str | None
    completed: bool
    seconds: float


class _QueryStat(TypedDict):
    symbols: int
    refs: int
    seconds: float


class ReverseRefs(TypedDict):
    """`reverse_refs/1` 산출물 전체."""
    schema: str
    engine: str
    repo_commit: str
    index: _IndexStat
    query: _QueryStat
    symbols: list[_Symbol]


# <include file="machine/comments.xml" path="//term[@id='reverse_refs.main']"/>
# 1차 심볼 전수 역참조를 뽑는 진입점.
# 쓰는 것: Clangd, to_repo_relative · 쓰이는 곳: 없음
def main(root: str, compdb: str, uml_path: str, out_path: str,
         binary: str | None = None) -> ReverseRefs:
    # 경로를 박지 않는다 — PATH 에서 찾고, 없으면 그 사실을 말한다.
    binary = binary or shutil.which("clangd")
    if not binary:
        raise SystemExit("clangd 를 PATH 에서 찾지 못했다. 설치하거나 네 번째 인자로 경로를 줘라.")
    uml: _Uml = json.load(open(uml_path))
    targets = [e for e in uml["elements"]
               if (e.get("namespace", "") or "").startswith(FIRST_PARTY_PREFIXES)
               and "source_location" in e]
    print(f"1차 심볼 {len(targets)}개 / 전체 {len(uml['elements'])}개")

    c = Clangd(root, compdb, binary=binary)
    ver = subprocess.run([binary, "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    c.initialize()
    # 색인을 깨우려면 파일 하나는 열어야 한다.
    c.did_open(targets[0]["source_location"]["file"])

    print("색인 완료 대기 ($/progress end) ...", flush=True)
    ok, secs = c.wait_for_index(timeout=900)
    tu_total: str | None = None
    for n in c.notifications():
        if n["method"] == "$/progress":
            # 알림은 dict[str, Any] 라 한 칸씩 모양을 붙인다.
            params: dict[str, Any] = n.get("params", {})
            value: dict[str, Any] = params.get("value", {}) or {}
            msg: str = value.get("message", "")
            if "/" in msg:
                tu_total = msg.split("/")[-1]
    if not ok:
        print("  ⚠ 색인 완료 신호를 받지 못했다. 결과가 부분일 수 있다.", file=sys.stderr)
    print(f"  완료={ok}  소요={secs:.1f}s  TU={tu_total}")

    opened: set[str] = set()
    out: list[_Symbol] = []
    t0, total = time.time(), 0
    for e in targets:
        sl = e["source_location"]
        rel = sl["file"]
        if rel not in opened:
            c.did_open(rel)
            opened.add(rel)
        r = c.references(rel, sl["line"], sl["column"], include_decl=False)
        # clangd 응답은 dict[str, Any] 라 여기서 한 번만 모양을 붙인다.
        locs: list[_LspLocation] = r.get("result") or []
        refs: list[_Loc] = [{"file": to_repo_relative(loc["uri"], root),
                             "line": loc["range"]["start"]["line"] + 1,
                             "col": loc["range"]["start"]["character"] + 1}
                            for loc in locs]
        total += len(refs)
        out.append({
            "id": e["id"],
            "display_name": e["display_name"],
            "is_nested": e.get("is_nested", False),
            "decl": {"file": rel, "line": sl["line"], "col": sl["column"]},
            "refs": refs,
        })
    elapsed = time.time() - t0

    commit = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    doc: ReverseRefs = {
        "schema": "reverse_refs/1",
        "engine": ver,
        "repo_commit": commit,
        "index": {"tu_total": tu_total, "completed": ok, "seconds": round(secs, 1)},
        "query": {"symbols": len(out), "refs": total, "seconds": round(elapsed, 1)},
        "symbols": out,
    }
    json.dump(doc, open(out_path, "w"), indent=1, ensure_ascii=False)
    print(f"질의 {len(out)}개 / 역참조 {total}건 / {elapsed:.1f}s  ->  {out_path}")
    c.shutdown()
    return doc


if __name__ == "__main__":
    main(*sys.argv[1:5])
