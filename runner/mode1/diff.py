"""`changes.json` 의 꼴. 옛 판(지문)과 새 판(지금 소스)을 대조한 결과가 여기 남는다."""
import json
import os
from typing import TypedDict

import measure as M
import pipeline as P
import warmup

BUCKETS = ("유효", "재읽기", "위치만", "삭제됨")


class WarmupDiff(TypedDict):
    """`targets` 가 `None` 이면 판정 불가 = 전량이다."""
    verdicts: warmup.Verdicts
    targets: list[str] | None
    hops: int
    tracked: int


def write_diff(path: str, verdicts: warmup.Verdicts, targets: list[str] | None,
               hops: int, tracked: int) -> WarmupDiff:
    doc: WarmupDiff = {"verdicts": verdicts, "targets": targets, "hops": hops, "tracked": tracked}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    return doc


def _str_list(v: object) -> list[str] | None:
    """문자열만 든 목록이면 그것을, 아니면 `None`. `as_list` 를 좁히기 전에 부른다 — 뒤에 부르면 원소 형을 잃는다."""
    raw = M.as_list(v)
    if not isinstance(v, list):
        return None
    items = [x for x in raw if isinstance(x, str)]
    return items if len(items) == len(raw) else None


def check_diff(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["diff 가 객체가 아니다"]
    out: list[str] = []
    v = M.as_map(top.get("verdicts"))
    for b in BUCKETS:
        if _str_list(v.get(b)) is None:
            out.append("`verdicts.%s` 가 문자열 배열이 아니다" % b)
    t = top.get("targets")
    if t is not None and _str_list(t) is None:
        out.append("`targets` 가 `null` 도 문자열 배열도 아니다")
    if M.as_int(top.get("tracked")) < 0:
        out.append("`tracked` 가 정수가 아니다")
    return out


def read_diff(path: str) -> WarmupDiff | None:
    raw = P.read_json(path)
    if check_diff(raw):
        return None
    top = M.as_map(raw)
    v = M.as_map(top.get("verdicts"))
    verdicts: warmup.Verdicts = {b: _str_list(v.get(b)) or [] for b in BUCKETS}
    t = top.get("targets")
    return {"verdicts": verdicts, "targets": None if t is None else (_str_list(t) or []),
            "hops": M.as_int(top.get("hops")), "tracked": M.as_int(top.get("tracked"))}


def all_files(d: WarmupDiff) -> set[str]:
    """지금 존재하는 추적 파일 전체. `삭제됨` 은 뺀다."""
    v = d["verdicts"]
    return set(v["유효"]) | set(v["재읽기"]) | set(v["위치만"])
