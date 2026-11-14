"""collect_manifest.py — 수집 manifest(`collect-fingerprint.json`)의 꼴과 계산. prep 이 쓰고 verify_graph 가 읽는다."""
import hashlib
import json
import os
from typing import Literal, TypedDict, cast


class CollectManifest(TypedDict):
    """한 번의 수집. `generation_id` 가 이 수집의 지도 · 소스 · 수집기 셋을 한 이름으로 묶는다."""
    fingerprint: str
    tool_versions: dict[str, str]
    config_inputs: dict[str, str]
    codegraph_sha256: str
    sources: dict[str, str]
    sources_sha256: str
    raw_provenance: Literal["prep", "unknown"]
    generation_id: str


def file_sha256(path: str) -> str | None:
    """바이트 그대로의 sha256. 없거나 못 열면 None."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def cited_files(codegraph: str) -> list[str]:
    """지도의 노드 · 간선이 인용한 파일(상대 경로)을 이름순으로."""
    with open(codegraph, encoding="utf-8") as f:
        g = cast(dict[str, object], json.load(f))
    out: set[str] = set()
    for key in ("nodes", "edges"):
        for x in cast(list[dict[str, object]], g.get(key) or []):
            if isinstance(x.get("file"), str):
                out.add(cast(str, x["file"]))
    return sorted(out)


def hash_sources(repo: str, files: list[str]) -> dict[str, str]:
    """파일마다 지금 내용의 sha256. 없는 파일은 "missing"."""
    return {rel: file_sha256(os.path.join(repo, rel)) or "missing" for rel in files}


def sources_digest(sources: dict[str, str]) -> str:
    """파일별 해시를 이름순으로 이어 붙인 sha256."""
    h = hashlib.sha256()
    for rel in sorted(sources):
        h.update(f"{rel}={sources[rel]}\n".encode())
    return h.hexdigest()


def generation_id(fingerprint: str, codegraph_sha256: str, sources_sha256: str) -> str:
    """수집기 지문 · 지도 바이트 · 소스 바이트를 한 이름으로. 셋 중 하나만 달라도 다른 세대다."""
    return hashlib.sha256(f"{fingerprint}\n{codegraph_sha256}\n{sources_sha256}\n".encode()).hexdigest()


def build_manifest(fingerprint: str, versions: dict[str, str], codegraph: str, repo: str, collector: str,
                   inputs: dict[str, str] | None = None) -> CollectManifest:
    """정제 직후에 부른다 — 소스 해시는 수집 시점의 것이어야 뒤에 붙인 거짓 최신성이 되지 않는다.

    roslyn-dump 의 원본은 prep 밖에서 만들어지므로 `raw_provenance` 가 unknown 이다.
    """
    sha = file_sha256(codegraph) or ""
    sources = hash_sources(repo, cited_files(codegraph))
    digest = sources_digest(sources)
    return {"fingerprint": fingerprint, "tool_versions": versions, "config_inputs": inputs or {},
            "codegraph_sha256": sha, "sources": sources, "sources_sha256": digest,
            "raw_provenance": "unknown" if collector == "roslyn-dump" else "prep",
            "generation_id": generation_id(fingerprint, sha, digest)}


def read_manifest(path: str, codegraph: str) -> CollectManifest | None:
    """기록된 manifest. 없거나 깨졌거나 지금 지도가 그때의 지도가 아니면 None — 셋 다 다시 수집하라는 뜻이다."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = cast(object, json.load(f))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    d = cast(dict[str, object], raw)
    need = ("fingerprint", "codegraph_sha256", "sources", "sources_sha256", "generation_id", "raw_provenance")
    if any(k not in d for k in need) or d["codegraph_sha256"] != file_sha256(codegraph):
        return None
    return cast(CollectManifest, d)


def changed_sources(manifest: CollectManifest, repo: str) -> list[str]:
    """manifest 에 적힌 파일 중 지금 내용이 다른 것(없어진 것 포함)."""
    now = hash_sources(repo, sorted(manifest["sources"]))
    return [rel for rel in sorted(now) if now[rel] != manifest["sources"][rel]]
