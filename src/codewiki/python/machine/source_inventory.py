"""source_inventory.py — git 이 추적하는 소스 파일을 언어별로 세고 파일마다 수집 상태를 적는다. prep 이 수집 전에 쓴다."""
import os
import subprocess
import sys
from typing import Literal, NotRequired, TypedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lang_select import COLLECTOR, LANG_EXTS, Lang  # noqa: E402

Status = Literal["collected", "excluded", "unsupported", "failed", "no-symbols"]


class FileEntry(TypedDict):
    """파일 하나의 수집 상태. `reason` 은 `excluded` · `unsupported` 일 때의 사유다."""
    language: str
    status: Status
    reason: NotRequired[str]


class LanguageRow(TypedDict):
    """언어 하나 — 추적 파일 수, 맡는 수집기, 이번에 수집했는가."""
    files: int
    collector: str
    collected: bool


class InventoryDoc(TypedDict):
    """`source-inventory.json`. `selected` 는 수집기가 고른 언어, `languages` 는 전부."""
    selected: str | None
    languages: dict[str, LanguageRow]
    files: dict[str, FileEntry]


def tracked_files(repo: str) -> list[str]:
    """`git ls-files -z` 의 경로를 이름순으로. git 저장소가 아니면 빈 목록이다."""
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=repo, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return sorted(p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p)


def language_of(path: str) -> Lang | None:
    """확장자로 본 언어. 소스가 아니면 `None`."""
    ext = os.path.splitext(path)[1]
    return next((lang for lang, exts in LANG_EXTS.items() if ext in exts), None)


def language_for(collector: str | None) -> Lang | None:
    """수집기 이름이 맡는 언어. 수집기가 없는 언어(`none`)와 모르는 이름은 `None`."""
    return next((lang for lang, name in COLLECTOR.items() if name == collector and name != "none"), None)


def build_inventory(repo: str, selected: str | None, excluded: dict[str, str]) -> InventoryDoc:
    """수집 전의 장부. 고른 언어의 파일은 `collected`(잠정), `excluded` 에 든 파일은 그 사유, 다른 언어는 `unsupported`."""
    files: dict[str, FileEntry] = {}
    counts: dict[Lang, int] = {}
    for rel in tracked_files(repo):
        lang = language_of(rel)
        if lang is None:
            continue
        counts[lang] = counts.get(lang, 0) + 1
        if rel in excluded:
            files[rel] = {"language": lang, "status": "excluded", "reason": excluded[rel]}
        elif lang == selected:
            files[rel] = {"language": lang, "status": "collected"}
        else:
            files[rel] = {"language": lang, "status": "unsupported", "reason": "collector %s" % COLLECTOR[lang]}
    languages: dict[str, LanguageRow] = {
        lang: {"files": n, "collector": COLLECTOR[lang], "collected": lang == selected}
        for lang, n in sorted(counts.items())}
    return {"selected": selected, "languages": languages, "files": files}


def mark_no_symbols(doc: InventoryDoc, cited: set[str]) -> None:
    """정제 뒤 — 고른 언어인데 지도가 한 번도 인용하지 않은 파일은 `no-symbols` 다."""
    for rel, entry in doc["files"].items():
        if entry["status"] == "collected" and rel not in cited:
            entry["status"] = "no-symbols"
