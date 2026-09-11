"""Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다."""
import os
from dataclasses import dataclass, field
from typing import NotRequired, TypedDict

import measure as M
import pipeline as P
import survey_plan
import warmup

# 이 파일은 <ROOT>/runner/mode1/ 에 있다. 저장소 뿌리는 그 셋 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 레코드의 칸은 배치 세션이 채우므로 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
Record = dict[str, object]
Records = dict[str, Record]


class WikiPage(TypedDict):
    """`outline.json` 의 장 하나. 목차 세션이 쓰는 파일이라 제목과 심볼은 빠질 수 있다."""

    file: str
    title: NotRequired[str]
    symbols: NotRequired[list[str]]


Pages = list[WikiPage]


def _no_records() -> Records:
    """`field(default_factory=dict)` 는 원소 형을 잃는다. 형이 붙은 빈 사전을 낸다."""
    return {}


def _no_pages() -> Pages:
    return []


def _no_ints() -> list[int]:
    return []


def _no_levels() -> dict[str, int]:
    return {}


@dataclass
class Mode1Context(P.RunContext):
    """칸마다 이름과 형이 있다. 자루(dict)는 없다."""
    repo: str = ""
    target: int = 8
    hops: int = 1
    cold: bool = False
    # 단계 사이를 건너다니는 값. 채우는 단계 → 읽는 단계.
    proposed: str | None = None                      # lang-hint → lang-decide
    targets: list[str] | None = None                 # detect-changes → schedule-batches · annotate-symbols
    entries: warmup.Manifest | None = None           # detect-changes → snapshot-sources
    warmup_cache: str | None = None                  # detect-changes → snapshot-sources
    tracked_n: int = 0                               # detect-changes → annotate-symbols (프롬프트 쪽지)
    plan: survey_plan.SurveyPlan | None = None       # schedule-batches → annotate-symbols · write-wiki
    survey_ok: bool = False                          # annotate-symbols → snapshot-sources
    baseline: Records = field(default_factory=_no_records)   # annotate-symbols 층 사이
    merged: Records = field(default_factory=_no_records)                     # annotate-symbols 층 사이
    wiki_pages: Pages = field(default_factory=_no_pages)                     # write-wiki 층 사이
    wiki_levels: list[int] = field(default_factory=_no_ints)
    wiki_level_of: dict[str, int] = field(default_factory=_no_levels)
    wiki_done: Pages = field(default_factory=_no_pages)


def raw_dir(c: Mode1Context) -> str:
    return os.path.join(c.repo, "out", "codegraph-raw")


# ── 산출물 검사. 최상위 열쇠와 성긴 형까지만 본다 ────────────────────────


def check_codegraph(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["코드 지도가 객체가 아니다"]
    out: list[str] = []
    for k in ("nodes", "edges"):
        if not isinstance(top.get(k), list):
            out.append("`%s` 가 배열이 아니다" % k)
    return out


def check_batches(obj: object) -> list[str]:
    top = M.as_map(obj)
    if not top:
        return ["층 계획이 객체가 아니다"]
    out: list[str] = []
    if not isinstance(top.get("layers"), list):
        out.append("`layers` 가 배열이 아니다")
    if not isinstance(top.get("totals"), dict):
        out.append("`totals` 가 객체가 아니다")
    return out


def check_lang_select(obj: object) -> list[str]:
    top = M.as_map(obj)
    return [] if "collector" in top else ["`collector` 가 없다"]


def check_outline(obj: object) -> list[str]:
    top = M.as_map(obj)
    return [] if isinstance(top.get("pages"), list) else ["`pages` 가 배열이 아니다"]


def check_reading(obj: object) -> list[str]:
    return [] if isinstance(obj, dict) else ["읽기 레코드가 객체가 아니다"]


def reading_path(repo: str, root: str) -> str:
    """전수조사 원본 `terms-reading.json` 의 자리.

    대상 저장소는 `<repo>/docs/codegraph/` 아래에 둔다. **이 저장소 자신만 다르다** —
    자기 것은 `machine/` 으로 옮겨져 있어 자기호스팅일 때 자리가 갈린다.
    """
    if os.path.abspath(repo) == os.path.abspath(root):
        return os.path.join(root, "machine", "terms-reading.json")
    return os.path.join(repo, "docs", "codegraph", "terms-reading.json")


# ── 산출물 선언. 자리는 ctx 가 정한다 ────────────────────────────────────

LANG_SELECT = P.Artifact[Mode1Context](
    "lang-select.json", lambda c: os.path.join(raw_dir(c), "lang-select.json"), check_lang_select)
CODEGRAPH = P.Artifact[Mode1Context](
    "codegraph.json", lambda c: os.path.join(raw_dir(c), "codegraph.json"), check_codegraph)
SNAPSHOT = P.Artifact[Mode1Context](
    "snapshot.json", lambda c: os.path.join(raw_dir(c), "snapshot.json"))
CHANGES = P.Artifact[Mode1Context](
    "changes.json", lambda c: os.path.join(raw_dir(c), "changes.json"))
BATCHES = P.Artifact[Mode1Context](
    "batches.json", lambda c: os.path.join(raw_dir(c), "batches.json"), check_batches)
READING = P.Artifact[Mode1Context](
    "terms-reading.json", lambda c: reading_path(c.repo, c.root), check_reading)
TERMS_DB = P.Artifact[Mode1Context](
    "terms-db.json", lambda c: os.path.join(raw_dir(c), "terms-db.json"))
OUTLINE = P.Artifact[Mode1Context](
    "outline.json", lambda c: os.path.join(raw_dir(c), "outline.json"), check_outline)
WIKI_DIR = P.Artifact[Mode1Context](
    "docs/wiki", lambda c: os.path.join(c.repo, "docs", "wiki"))
RESUME = P.Artifact[Mode1Context](
    "resume.json", lambda c: os.path.join(raw_dir(c), "resume.json"))

ARTIFACTS = [LANG_SELECT, CODEGRAPH, SNAPSHOT, CHANGES, BATCHES,
             READING, TERMS_DB, OUTLINE, WIKI_DIR, RESUME]


def snapshot_path(c: Mode1Context) -> str:
    """읽을 지문 파일. `snapshot.json` 이 없고 옛 이름 `warmup.json` 이 있으면 그것을 읽는다.

    쓰는 것은 늘 `snapshot.json` 이다 — 한 번 돌면 이주가 끝난다.
    """
    new = SNAPSHOT.locate(c)
    old = os.path.join(raw_dir(c), "warmup.json")
    return old if not os.path.exists(new) and os.path.exists(old) else new
