#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='file_cache.py']"/>
# 파일을 한 번만 통독하도록 통독 결과를 디스크에 남기는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""file_cache.py — 파일 통독 캐시.

배치 세션끼리는 컨텍스트를 공유하지 못하므로, 먼저 읽은 쪽이 개요를 디스크에 남기고
나중 쪽이 그것을 읽는다.

lock 을 쓰지 않는다. 임시 파일에 쓰고 `os.replace` 로 갈아 끼우면 POSIX 에서 원자적이라
반쯤 쓰인 파일을 남이 읽는 일이 없다.

⚠ 캐시는 개요일 뿐 근거가 아니다. 자기가 맡은 심볼은 실제 줄 범위를 열어 읽어야 하고,
캐시만 보고 쓴 레코드는 `confidence` 가 HIGH 일 수 없다.

  file_cache.py get <repo> <파일경로>            → 캐시 출력. 없거나 낡았으면 종료 코드 1
  file_cache.py put <repo> <파일경로> <개요json> → 캐시 기록
"""
import hashlib
import json
import os
import sys


# <include file="machine/comments.xml" path="//term[@id='machine.file_cache._paths']"/>
# 어떤 파일의 통독 캐시가 어디에 저장돼야 하는지, 그리고 그 파일이 바뀌었는지 확인할 지문(해시)을 만들어주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.file_cache.get, machine.file_cache.put
def _paths(repo: str, rel: str) -> tuple[str, str]:
    """내용 해시로 캐시를 무효화한다. mtime 은 체크아웃으로 흔들려 못 믿는다."""
    with open(os.path.join(repo, rel), "rb") as f:
        h = hashlib.sha1(f.read()).hexdigest()
    key = hashlib.sha1(rel.encode("utf-8")).hexdigest()
    return h, os.path.join(repo, "out", "codegraph-raw", "_filecache", key + ".json")


# <include file="machine/comments.xml" path="//term[@id='machine.file_cache.get']"/>
# 다른 배치 세션이 이미 통독해 남긴 파일 요약(개요)을 다시 읽어오는 함수다.
# 쓰는 것: machine.file_cache._paths · 쓰이는 곳: machine.test_file_cache.test_내용이_바뀌면_무효, machine.test_file_cache.test_넣은_것을_그대로_돌려준다, machine.test_file_cache.test_망가진_캐시는_None, machine.test_file_cache.test_없는_파일이면_None, machine.test_file_cache.test_없으면_None (+1)
def get(repo: str, rel: str) -> dict[str, object] | None:
    """캐시가 있고 내용 해시가 같으면 돌려준다. 아니면 None — 부르는 쪽이 통독한다.

    파일이 없거나 캐시가 깨졌어도 터지지 않고 None 이다.
    """
    try:
        h, path = _paths(repo, rel)
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if d.get("sha1") == h else None
    except Exception:
        return None


# <include file="machine/comments.xml" path="//term[@id='machine.file_cache.put']"/>
# 통독해서 만든 개요를 나중에 다른 세션이 읽을 수 있도록 디스크에 저장하는 함수다.
# 쓰는 것: machine.file_cache._paths · 쓰이는 곳: machine.test_file_cache.test_내용이_바뀌면_무효, machine.test_file_cache.test_넣은_것을_그대로_돌려준다, machine.test_file_cache.test_망가진_캐시는_None, machine.test_file_cache.test_임시파일을_남기지_않는다, machine.test_file_cache.test_캐시는_out_아래에_산다 (+1)
def put(repo: str, rel: str, outline: object) -> str:
    """개요를 남긴다. 임시 파일 + os.replace 라 원자적이다."""
    h, path = _paths(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"path": rel, "sha1": h, "outline": outline}, f,
                  ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    cmd, repo, rel = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "get":
        d = get(repo, rel)
        if d is None:
            sys.exit(1)
        json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
    elif cmd == "put":
        with open(sys.argv[4], encoding="utf-8") as f:
            print(put(repo, rel, json.load(f)))
    else:
        sys.exit("모르는 명령 %s" % cmd)
