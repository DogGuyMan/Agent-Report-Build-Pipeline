"""재개 JSON. 모든 중단이 이것을 남기고, 팩토리가 이것을 읽어 멈춘 자리부터 짓는다."""
import json
import os
from collections.abc import Iterable
from typing import NotRequired, TypedDict

import measure as M
import pipeline as P


class ResumeDoc(TypedDict):
    """`verified` 는 이 실행까지 검사를 통과한 산출물 종류다. 재개한 실행이 이어받는다. 없는 문서도 읽힌다."""
    graph: str
    failed_at: str
    why: str
    done: list[str]
    rows: list[M.StageRow]
    verified: NotRequired[list[str]]


def write_resume(path: str, graph: str, rows: list[M.StageRow], order: list[str],
                 verified: Iterable[str]) -> ResumeDoc | None:
    """실패한 행이 없으면 아무것도 쓰지 않고 `None`. 있으면 쓴다."""
    failed = [r for r in rows if not r.get("ok") and not r.get("skipped")]
    if not failed:
        return None
    failed_at = failed[0]["stage"].split("/")[0]
    done = [n for n in order if n != failed_at and order.index(n) < order.index(failed_at)]
    doc: ResumeDoc = {"graph": graph, "failed_at": failed_at,
                      "why": failed[0].get("why") or "", "done": done, "rows": rows,
                      "verified": sorted(verified)}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return doc


def read_resume(path: str) -> ResumeDoc | None:
    """없으면 `None`. 있는데 꼴이 틀리면 예외다."""
    return P.load(path, ResumeDoc) if os.path.exists(path) else None


def start_stage(doc: ResumeDoc | None, for_graph: str) -> str | None:
    """이 그래프용 재개 문서면 시작할 단계를, 아니면 `None`."""
    if doc is None or doc["graph"] != for_graph:
        return None
    return doc["failed_at"]


def carried_verified(doc: ResumeDoc | None, for_graph: str) -> set[str]:
    """이 그래프용 재개 문서면 앞선 실행이 검사를 통과시킨 산출물 종류를, 아니면 빈 집합."""
    if doc is None or doc["graph"] != for_graph:
        return set()
    return set(doc.get("verified", []))
