#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='codegraph/warmup.py']"/>
# 전수조사를 매번 전량 다시 하지 않게 하는 캐시와 무효화의 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""warmup.py — 전수조사를 매번 전량 다시 하지 않게 하는 파일별 캐시와 무효화.

**이 도구는 요약을 만들지 않는다.** 요약(전수조사 레코드)은 LLM 이 내고,
여기는 **수명과 무효화**만 맡는다. 그 분리가 이 설계의 요점이다 — 판단은 LLM, 판정은 기계.

**왜 필요한가.** 🔵 2026-08-29 실측 — QtVisionEdit(30파일 2,982줄) 전수조사에
287,564 토큰, StickRush(110파일 8,164줄)에 266,475 토큰이 들었다. 코드가 조금 바뀌었을
때도 지금은 같은 값을 다시 낸다. 그런데 일상 커밋 하나에 바뀌는 파일은 원래 몇 개뿐이다.

**무효화 열쇠는 파일 내용이다 — git 의 blob SHA 가 아니다.**
`git ls-tree HEAD` 의 blob SHA 는 **커밋된 내용**이라, 작업 트리를 고쳐 놓고 커밋하지
않은 상태에서 돌리면 "유효" 로 판정되어 낡은 요약이 그대로 재사용된다. 개발 중에 가장
흔한 상태가 바로 그 상태다. 그래서 `hashlib.sha256` 으로 바이트를 그대로 해싱한다.
git 은 **어떤 파일이 추적 대상인가**(= 삭제 판정)를 묻는 데만 쓴다.

**두 겹으로 무효화한다.** 파일 해시가 바뀌어도 선언 목록이 같으면 LLM 을 다시 부를 일이
없다. 주석만 고치거나 줄만 밀린 변경이 그렇다. 그때 필요한 것은 좌표 재계산뿐이고
그 일은 `codegraph/xmldoc.py inject` 가 이미 마커 기준으로 한다.

  파일 해시 같음                → 유효    (아무것도 안 한다)
  파일 해시 다름 · 선언 같음    → 위치만  (xmldoc inject. LLM 을 부르지 않는다)
  파일 해시 다름 · 선언 다름    → 재읽기  (그 파일만 다시 읽는다)
  git 이 모름                   → 삭제됨  (레코드를 지울지 사람에게 묻는다)

⚠ **매니페스트가 못 잡는 것이 하나 있다.** 파일 A 는 안 바뀌었는데 A 를 서술한 문장이
B 의 변경 때문에 틀려지는 경우다. 매니페스트는 파일 단위라 그것을 볼 수 없다.
그것은 `codegraph.json` 의 의존 간선이 푼다 — `blast_radius()` 참조. 둘은 겹치지 않는다.

  python codegraph/warmup.py status <저장소> --lang cs
  python codegraph/warmup.py blast  <저장소> --lang cs --codegraph <codegraph.json> --hops 1
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import declmap  # noqa: E402

# 매니페스트가 놓이는 자리. 파생물이므로 gitignore 대상인 out/ 아래다.
DEFAULT_CACHE = os.path.join("out", "codegraph-raw", "warmup.json")


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.file_hash']"/>
# 파일 내용을 한 줄의 지문으로 줄인다.
# 쓰는 것: 없음 · 쓰이는 곳: warmup.status
def file_hash(path):
    """바이트 그대로의 sha256. 커밋 여부와 무관하다.

    정규화하지 않는다 — 줄끝 변환이나 공백 정리는 "안 바뀌었다" 는 거짓 판정을 만들 수 있고,
    이 함수가 틀리면 낡은 요약이 조용히 재사용된다. 없는 파일은 None 이다.
    """
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.decl_hash']"/>
# 한 파일의 선언 목록을 한 줄의 지문으로 줄인다.
# 쓰는 것: declmap.scan · 쓰이는 곳: warmup.status
def decl_hash(entry):
    """선언 목록의 해시. `declmap.scan` 의 **한 파일 몫**을 받는다.

    **줄 번호와 문서 주석은 일부러 뺀다.** 둘은 주석 한 줄만 고쳐도 바뀌는데, 그때
    LLM 이 다시 추론할 것은 없다 — 고칠 것은 좌표뿐이다. 남기는 것은 선언의 정체
    (`kind`+`name`)이고 그것이 바뀔 때만 그 파일을 다시 읽는다.

    entry 가 None 이면(선언이 하나도 없는 파일) None 을 낸다.
    """
    if not entry:
        return None
    ident = sorted((d.get("kind", ""), d.get("name", "")) for d in entry.get("decls", []))
    blob = json.dumps(ident, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.load']"/>
# 지난번 훑기의 기록을 읽는다.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
def load(cache_path):
    """매니페스트를 읽는다. 없거나 깨졌으면 빈 것으로 친다 — 그러면 전량 재읽기다."""
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data.get("files", {}) if isinstance(data, dict) and "files" in data else data


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.save']"/>
# 이번 훑기의 결과를 기록으로 남긴다.
# 쓰는 것: 없음 · 쓰이는 곳: warmup.main
def save(cache_path, entries):
    """매니페스트를 쓴다. 상위 폴더가 없으면 만든다."""
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"files": entries}, f, ensure_ascii=False, indent=1, sort_keys=True)
    return entries


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.status']"/>
# 파일마다 무엇을 해야 하는지를 네 갈래로 가른다.
# 쓰는 것: warmup.file_hash, warmup.decl_hash · 쓰이는 곳: warmup.main
def status(cache_path, repo, files, decls=None):
    """판정 네 갈래와 갱신된 매니페스트를 함께 낸다. **쓰지는 않는다** — 쓰기는 `save` 다.

    files  이번에 훑을 상대경로 목록(= `declmap.tracked_files`). git 이 아는 것만 온다.
    decls  `declmap.scan` 의 결과 `{상대경로: {lines, decls[]}}`. 없으면 두 겹째를
           판정할 수 없으므로 내용이 바뀐 파일은 전부 `재읽기` 로 간다 — 안전한 쪽이다.

    반환 ({"유효": [...], "재읽기": [...], "위치만": [...], "삭제됨": [...]}, 새_항목)

    **삭제 판정은 `files` 에 없다는 것으로 한다.** files 는 git 이 아는 목록이므로,
    지워졌거나 추적에서 빠진 파일은 자연히 빠진다. `seen` 은 매 실행마다 갱신하고
    이번에 안 본 항목이 곧 삭제됨이다.
    """
    old = load(cache_path)
    now = time.time()
    판정 = {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}
    entries = {}

    for rel in files:
        path = os.path.join(repo, rel)
        try:
            st = os.stat(path)
        except OSError:
            판정["삭제됨"].append(rel)          # git 은 아는데 디스크에 없다
            continue
        prev = old.get(rel)
        새_선언 = decl_hash(decls.get(rel)) if decls is not None else None

        # ── 1차 관문. mtime 과 크기가 같으면 해싱조차 하지 않는다.
        if prev and prev.get("mtime") == st.st_mtime and prev.get("size") == st.st_size:
            판정["유효"].append(rel)
            entries[rel] = dict(prev, seen=now)
            continue

        새_해시 = file_hash(path)
        if prev and prev.get("file_hash") == 새_해시:
            판정["유효"].append(rel)            # mtime 만 밀렸다(체크아웃 따위)
        elif prev is None:
            판정["재읽기"].append(rel)          # 처음 보는 파일
        elif decls is None or 새_선언 != prev.get("decl_hash"):
            판정["재읽기"].append(rel)
        else:
            판정["위치만"].append(rel)          # 내용은 달라졌으나 선언은 같다

        entries[rel] = {
            "mtime": st.st_mtime,
            "size": st.st_size,
            "seen": now,
            "file_hash": 새_해시,
            # decls 를 안 받은 실행이 옛 선언 해시를 지우면 다음 실행이 두 겹을 잃는다.
            "decl_hash": 새_선언 if decls is not None else (prev or {}).get("decl_hash"),
        }

    for rel in old:
        if rel not in entries and rel not in 판정["삭제됨"]:
            판정["삭제됨"].append(rel)

    for k in 판정:
        판정[k].sort()
    return 판정, entries


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.blast_radius']"/>
# 바뀐 파일 때문에 서술이 틀려질 수 있는 이웃 파일까지 넓힌다.
# 쓰는 것: 없음 · 쓰이는 곳: warmup.main
def blast_radius(codegraph, changed_files, hops=1):
    """바뀐 파일이 영향을 주는 파일 집합. 매니페스트가 못 잡는 전이 오염을 여기서 잡는다.

    codegraph 의 간선을 **양방향으로** 타고 hops 만큼 퍼뜨린다 —
    A 가 B 를 쓰는데 B 가 바뀌면 A 의 서술이 틀려질 수 있고, 그 반대도 마찬가지다.
    `file` 이 없는 노드(외부 심볼)는 뺀다 — 저장소 밖이라 다시 읽을 것이 없다.
    """
    with open(codegraph, encoding="utf-8") as f:
        g = json.load(f)
    nid = {n["id"]: n for n in g.get("nodes", [])}
    adj = defaultdict(set)
    for e in g.get("edges", []):
        a, b = nid.get(e.get("from")), nid.get(e.get("to"))
        if not a or not b or not a.get("file") or not b.get("file"):
            continue
        adj[a["file"]].add(b["file"])
        adj[b["file"]].add(a["file"])
    frontier = set(changed_files)
    seen = set(frontier)
    for _ in range(hops):
        nxt = set()
        for f_ in frontier:
            nxt |= adj.get(f_, set())
        frontier = nxt - seen
        seen |= frontier
    return sorted(seen)


# <include file="docs/codegraph/comments.xml" path="//term[@id='warmup.main']"/>
# 명령줄에서 판정과 파급을 부르고 결과를 사람이 읽게 찍는다.
# 쓰는 것: declmap.tracked_files, declmap.scan, warmup.status, warmup.blast_radius, warmup.save · 쓰이는 곳: 없음
def main():
    ap = argparse.ArgumentParser(description="전수조사 증분 캐시 — 무엇을 다시 읽어야 하는가")
    ap.add_argument("action", choices=["status", "blast"])
    ap.add_argument("repo")
    ap.add_argument("--lang", default="cs", choices=sorted(declmap.LANGS))
    ap.add_argument("--include", action="append", default=[],
                    help="이 접두사로 시작하는 경로만 (여러 번 줄 수 있다)")
    ap.add_argument("--cache", help=f"매니페스트 자리 (기본: <저장소>/{DEFAULT_CACHE})")
    ap.add_argument("--codegraph", help="blast 에 필요하다")
    ap.add_argument("--hops", type=int, default=1)
    ap.add_argument("--write", action="store_true",
                    help="판정 뒤 매니페스트를 갱신한다. 없으면 읽기만 한다")
    a = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(a.repo))
    cache = a.cache or os.path.join(repo, DEFAULT_CACHE)
    files = declmap.tracked_files(repo, a.lang, a.include)
    if not files:
        print(f"{a.lang} 소스가 없다 — git 이 아는 파일 0개", file=sys.stderr)
        return 1
    decls, _ = declmap.scan(repo, a.lang, a.include, 0)

    판정, entries = status(cache, repo, files, decls)
    총 = len(files)
    재읽기 = len(판정["재읽기"])
    print(f"{a.lang} 파일 {총}개 — 유효 {len(판정['유효'])} · 재읽기 {재읽기} · "
          f"위치만 {len(판정['위치만'])} · 삭제됨 {len(판정['삭제됨'])}")
    print(f"재읽기 비율 {재읽기 / 총 * 100:.1f}%")
    for 갈래 in ("재읽기", "위치만", "삭제됨"):
        for p in 판정[갈래][:10]:
            print(f"  {갈래}: {p}")
        if len(판정[갈래]) > 10:
            print(f"  {갈래}: … 그 밖 {len(판정[갈래]) - 10}개")

    if a.action == "blast":
        if not a.codegraph:
            print("--codegraph 가 필요하다", file=sys.stderr)
            return 1
        바뀐 = 판정["재읽기"] + 판정["위치만"]
        r = blast_radius(a.codegraph, 바뀐, a.hops)
        print(f"\n파급 범위({a.hops}홉): {len(r)}개 파일 — 바뀐 {len(바뀐)}개에서 퍼진 것")
        print(f"파급 비율 {len(r) / 총 * 100:.1f}%")
        for p in r[:15]:
            print(f"  {p}")
        if len(r) > 15:
            print(f"  … 그 밖 {len(r) - 15}개")

    if a.write:
        save(cache, entries)
        print(f"\n매니페스트 갱신 — {cache}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
