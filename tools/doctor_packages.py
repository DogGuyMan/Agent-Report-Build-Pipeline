"""`doctor.py` 가 고른 파이썬으로 띄우는 패키지 확인 — 인자로 받은 배포 이름 중 깔리지 않은 것을 한 줄로 낸다.

이 저장소의 어느 것도 import 하지 않는다. 판이 낮은 해석기에서도 돌아야 해서 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import importlib.metadata as md
import sys


def missing(names: list[str]) -> list[str]:
    """깔리지 않은 배포 이름들. 순서는 받은 그대로."""
    out: list[str] = []
    for n in names:
        try:
            md.version(n)
        except md.PackageNotFoundError:
            out.append(n)
    return out


def main() -> int:
    """`전부 있다` 또는 `빠짐: <이름>, …` 한 줄을 낸다. 빠진 것이 있어도 exit 0 — 판정은 `doctor.py` 가 그 줄로 한다."""
    gone = missing(sys.argv[1:])
    print("전부 있다" if not gone else "빠짐: " + ", ".join(gone))
    return 0


if __name__ == "__main__":
    sys.exit(main())
