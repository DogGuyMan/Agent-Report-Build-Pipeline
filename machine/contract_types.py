"""생성물 — tools/gen_contract_types.py 가 contracts/mode1-artifacts.v1.json 에서 낸다. 손대지 마라."""
from typing import NotRequired, TypedDict

CONTRACT = "mode1-artifacts"
VERSION = 1


class ArtifactEntry(TypedDict):
    path: str
    sha256: str


class SupersededBy(TypedDict):
    at: str
    producer_commit: str
    stage: str


class ArtifactManifest(TypedDict):
    artifacts: dict[str, list[ArtifactEntry]]
    contract: str
    inputs: dict[str, str]
    producer_commit: str
    skip_dirs: list[str]
    source_commit: str
    source_exts: list[str]
    superseded_by: NotRequired[SupersededBy]
    version: int


class DbUse(TypedDict):
    kind: str
    label: str | None
    source: NotRequired[str]
    to: str
    where: str


class TermRecord(TypedDict):
    confidence: NotRequired[str]
    does: NotRequired[str]
    hotspot: NotRequired[bool]
    id: NotRequired[str]
    kind: str
    means: str
    module: str | None
    neighbors: list[str]
    source: str
    uses: list[DbUse]
    where: str


TermsDb = dict[str, TermRecord]
