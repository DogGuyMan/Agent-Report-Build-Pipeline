"""`changes.json` 의 꼴. 옛 판(지문)과 새 판(지금 소스)을 대조한 결과가 여기 남는다."""
import json
import os
from typing import TypedDict

import pipeline as P
import warmup

BUCKETS = ("유효", "재읽기", "위치만", "삭제됨")



class WarmupDiff(TypedDict):
    """`targets` 가 `None` 이면 판정 불가 = 전량이다.

    `verdicts` 의 갈래 넷(`BUCKETS`)이 다 있는 것은 `write_diff` 가 보장한다. 형으로 못 박지 않는
    이유 — msgspec 은 한글 열쇠의 `TypedDict` 칸을 모듈 경계 너머에서 못 맞춘다(`Buckets` 시도가 그렇게 죽었다).
    """
    verdicts: warmup.Verdicts
    targets: list[str] | None
    hops: int
    tracked: int


def write_diff(path: str, verdicts: warmup.Verdicts, targets: list[str] | None,
               hops: int, tracked: int) -> WarmupDiff:
    buckets: warmup.Verdicts = {b: list(verdicts.get(b, [])) for b in BUCKETS}
    doc: WarmupDiff = {"verdicts": buckets, "targets": targets, "hops": hops, "tracked": tracked}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    return doc


def read_diff(path: str) -> WarmupDiff | None:
    """없으면 `None`. 있는데 꼴이 틀리면 예외다 — 드라이버가 받는다."""
    return P.load(path, WarmupDiff) if os.path.exists(path) else None


def all_files(d: WarmupDiff) -> set[str]:
    """지금 존재하는 추적 파일 전체. `삭제됨` 은 뺀다."""
    v = d["verdicts"]
    return set(v.get("유효", [])) | set(v.get("재읽기", [])) | set(v.get("위치만", []))
