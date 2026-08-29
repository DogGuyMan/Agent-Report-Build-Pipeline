#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='reverse_refs.py']"/>
# 1차 심볼을 누가 쓰고 있는지 전수로 뽑는 도구.
# 쓰는 것: Clangd · 쓰이는 곳: 없음
"""1차 심볼 전수 역참조를 뽑는다 (E6 + 전수 확정).

산출물은 엔진 중립이다 (E7 제약) — LSP 의 uri/range 를 내보내지 않고
{저장소 상대경로, line, col} 로 정규화한다. E5(libclang) 로 갈아끼워도 소비자가 안 바뀐다.

⚠ 색인 완료 게이트가 이 스크립트의 핵심이다. clangd 는 색인이 덜 찬 상태에서
부분 결과를 조용히 돌려준다(에러 없음). $/progress 의 end 를 기다린 뒤에만 질의한다.

사용:  python3 reverse_refs.py <repo_root> <compdb_dir> <clang_uml_json> <out_json>
"""
import json, subprocess, sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from clangd_refs import Clangd, to_repo_relative

FIRST_PARTY_PREFIXES = ("SJH", "MyApp")


# <include file="docs/codegraph/comments.xml" path="//term[@id='reverse_refs.main']"/>
# 1차 심볼 전수 역참조를 뽑는 진입점.
# 쓰는 것: Clangd, to_repo_relative · 쓰이는 곳: 없음
def main(root, compdb, uml_path, out_path, binary=None):
    # 경로를 박지 않는다 — 기계마다 다르다. PATH 에서 찾고, 없으면 그 사실을 말한다.
    binary = binary or shutil.which("clangd")
    if not binary:
        raise SystemExit("clangd 를 PATH 에서 찾지 못했다. 설치하거나 네 번째 인자로 경로를 줘라.")
    uml = json.load(open(uml_path))
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
    tu_total = None
    for n in c.notifications():
        if n["method"] == "$/progress":
            msg = (n.get("params", {}).get("value", {}) or {}).get("message", "")
            if "/" in msg:
                tu_total = msg.split("/")[-1]
    if not ok:
        print("  ⚠ 색인 완료 신호를 받지 못했다. 결과가 부분일 수 있다.", file=sys.stderr)
    print(f"  완료={ok}  소요={secs:.1f}s  TU={tu_total}")

    opened, out, t0, total = set(), [], time.time(), 0
    for e in targets:
        sl = e["source_location"]
        rel = sl["file"]
        if rel not in opened:
            c.did_open(rel)
            opened.add(rel)
        r = c.references(rel, sl["line"], sl["column"], include_decl=False)
        refs = [{"file": to_repo_relative(loc["uri"], root),
                 "line": loc["range"]["start"]["line"] + 1,
                 "col": loc["range"]["start"]["character"] + 1}
                for loc in (r.get("result") or [])]
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
    doc = {
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
