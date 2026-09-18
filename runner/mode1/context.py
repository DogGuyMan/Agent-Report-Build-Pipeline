"""Mode 1 의 문맥과 산출물. 단계 사이를 건너다니는 값은 전부 여기 칸이 있다."""
import os
from dataclasses import dataclass, field
from typing import Literal, NotRequired, TypedDict

import pipeline as P
import survey_plan
import warmup
from mode1.diff import WarmupDiff
from mode1.resume import ResumeDoc

# 이 파일은 <ROOT>/runner/mode1/ 에 있다. 저장소 뿌리는 그 셋 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 레코드의 칸은 배치 세션이 채우므로 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
Record = dict[str, object]
Records = dict[str, Record]

# 배치 세션이 샤드에 쓰는 레코드의 꼴. 프롬프트의 "레코드 계약" 과 같은 칸이고, 기계가 이 형으로
# 샤드를 검문한다. `method` 는 코드 지도(pycalls)가 내는 종류라 함께 받는다.
RecordKind = Literal["file", "module", "function", "method", "class", "struct", "enum", "interface",
                     "delegate", "record", "external", "artifact", "key", "concept"]
UseKind = Literal["dependency", "inheritance", "aggregation", "composition", "association", "realization"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]


class ShardUse(TypedDict):
    to: str
    kind: UseKind
    label: str | None
    where: str


class ShardRecord(TypedDict):
    """`where` 는 `module` · `external` 만 없어도 된다 — 그 규칙은 형이 아니라 검문이 본다."""
    kind: RecordKind
    module: str | None
    where: NotRequired[str]
    means: str
    does: NotRequired[str]
    uses: list[ShardUse]
    confidence: Confidence
    source: Literal["reading"]


ShardRecords = dict[str, ShardRecord]

# 샤드 검문이 내는 결함 하나. 격리 사유(`.json.bad.why`)와 재조사 프롬프트가 같은 꼴을 쓴다.
FaultKind = Literal["missing", "malformed", "schema", "where"]


class ShardFault(TypedDict):
    """`at` 은 결함의 자리 — 문법이면 `byte N`, 꼴이면 `$[...].칸`, where 면 레코드 키."""
    kind: FaultKind
    batch: str
    path: str
    at: str
    detail: str
    fix: str


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


# ── 산출물의 꼴. `Artifact.schema` 가 되어 경계에서 msgspec 이 검증한다 ─────────


class CodeGraphDoc(TypedDict):
    """`codegraph.json` 의 최상위만. 노드 안은 기계축 선언(`survey_plan.CodeGraph`)이 실물과
    어긋나(`file` 에 `null` 이 온다) 러너는 열지 않는다 — `survey_plan.plan` 에 넘길 때 `cast` 한다.
    """
    nodes: list[dict[str, object]]
    edges: list[dict[str, object]]


class LangSelect(TypedDict):
    """`lang-select.json`. `language` 는 못 골랐으면 `null` 이다."""
    language: str | None
    collector: str


class Outline(TypedDict):
    """`outline.json`."""
    pages: list[WikiPage]


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
    "lang-select.json", lambda c: os.path.join(raw_dir(c), "lang-select.json"), LangSelect)
CODEGRAPH = P.Artifact[Mode1Context](
    "codegraph.json", lambda c: os.path.join(raw_dir(c), "codegraph.json"), CodeGraphDoc)
SNAPSHOT = P.Artifact[Mode1Context](
    "snapshot.json", lambda c: os.path.join(raw_dir(c), "snapshot.json"))
CHANGES = P.Artifact[Mode1Context](
    "changes.json", lambda c: os.path.join(raw_dir(c), "changes.json"), WarmupDiff)
BATCHES = P.Artifact[Mode1Context](
    "batches.json", lambda c: os.path.join(raw_dir(c), "batches.json"), survey_plan.SurveyPlan)
RECORD_SCHEMA = P.Artifact[Mode1Context](
    "record-schema.json", lambda c: os.path.join(raw_dir(c), "record-schema.json"))
READING = P.Artifact[Mode1Context](
    "terms-reading.json", lambda c: reading_path(c.repo, c.root), Records)
TERMS_DB = P.Artifact[Mode1Context](
    "terms-db.json", lambda c: os.path.join(raw_dir(c), "terms-db.json"))
OUTLINE = P.Artifact[Mode1Context](
    "outline.json", lambda c: os.path.join(raw_dir(c), "outline.json"), Outline)
WIKI_DIR = P.Artifact[Mode1Context](
    "docs/wiki", lambda c: os.path.join(c.repo, "docs", "wiki"))
RESUME = P.Artifact[Mode1Context](
    "resume.json", lambda c: os.path.join(raw_dir(c), "resume.json"), ResumeDoc)

ARTIFACTS = [LANG_SELECT, CODEGRAPH, SNAPSHOT, CHANGES, BATCHES, RECORD_SCHEMA,
             READING, TERMS_DB, OUTLINE, WIKI_DIR, RESUME]


def snapshot_path(c: Mode1Context) -> str:
    """읽을 지문 파일. `snapshot.json` 이 없고 옛 이름 `warmup.json` 이 있으면 그것을 읽는다.

    쓰는 것은 늘 `snapshot.json` 이다 — 한 번 돌면 이주가 끝난다.
    """
    new = SNAPSHOT.locate(c)
    old = os.path.join(raw_dir(c), "warmup.json")
    return old if not os.path.exists(new) and os.path.exists(old) else new
