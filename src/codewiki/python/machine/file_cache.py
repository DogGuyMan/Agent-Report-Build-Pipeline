#!/usr/bin/env python3
"""file_cache.py — 파일 통독 캐시.

파일마다 개요 한 건을 디스크에 둔다. 쓰는 쪽은 조사 단계다 — 세션을 띄우기 전에 계획의 파일마다
개요를 `put` 으로 쓰고, 배치 프롬프트를 만들 때 `get` 으로 읽어 싣는다. 세션은 캐시를 쓰지 않는다.

lock 을 쓰지 않는다. 임시 파일에 쓰고 `os.replace` 로 갈아 끼우면 POSIX 에서 원자적이라
반쯤 쓰인 파일을 남이 읽는 일이 없다.

⚠ 캐시는 개요일 뿐 근거가 아니다. 세션은 자기가 맡은 심볼의 실제 줄 범위를 열어 읽어야 한다.

  file_cache.py get <repo> <파일경로>   → 캐시 출력. 없거나 낡았으면 종료 코드 1
"""
import hashlib
import json
import os
import sys


def _paths(repo: str, rel: str) -> tuple[str, str]:
    """내용 해시로 캐시를 무효화한다. mtime 은 체크아웃으로 흔들려 못 믿는다."""
    with open(os.path.join(repo, rel), "rb") as f:
        h = hashlib.sha1(f.read()).hexdigest()
    key = hashlib.sha1(rel.encode("utf-8")).hexdigest()
    return h, os.path.join(repo, "out", "codegraph-raw", "_filecache", key + ".json")


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
    else:
        sys.exit("모르는 명령 %s" % cmd)
