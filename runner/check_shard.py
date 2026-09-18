#!/usr/bin/env python3
"""샤드 파일 하나를 기계 검문한다. 배치 세션이 끝내기 전에 스스로 돌리는 문이다.

검사는 `AnnotateSymbolsStage.check_shard` 와 같다 — 층 끝 검문과 한 검사기다.
통과하면 0, 불평이 있으면 그것을 찍고 1.
"""
import os
import sys
from collections.abc import Sequence

# 러너는 `runner/`, 결정론 기계는 `machine/` 이다. CLI 로 돌 때 machine 을 못 찾으므로 여기서 넣는다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine"
    ),
)

from mode1.survey import AnnotateSymbolsStage  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("사용법: check_shard.py <샤드.json>", file=sys.stderr)
        return 2
    try:
        with open(args[0], "rb") as f:
            got = AnnotateSymbolsStage.check_shard(f.read(), path=args[0])
    except OSError as e:
        print("✗ 파일을 못 읽었다 — %s" % e)
        return 1
    for fault in got:
        print("✗ " + AnnotateSymbolsStage.fault_line(fault))
    print("통과 — %s" % args[0] if not got else "불평 %d — 고치고 다시 돌린다" % len(got))
    return 1 if got else 0


if __name__ == "__main__":
    sys.exit(main())
