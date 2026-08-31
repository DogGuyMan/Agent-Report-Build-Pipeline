# <include file="machine/comments.xml" path="//term[@id='paths.py']"/>
# 위키 세 명령이 함께 보는 경로 규약.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
import json
from typing import Any, Optional, cast

def wikiPaths(repo: str) -> dict[str, str]:
    raw = os.path.join(repo, "out", "codegraph-raw")
    return {
        "repo": repo,
        "raw": raw,
        "wiki": os.path.join(repo, "docs", "wiki"),
        "built": os.path.join(raw, "wiki-built"),
        "site": os.path.join(raw, "wiki-site"),
        "codegraph": os.path.join(raw, "codegraph.json"),
    }

def collectorFor(entries: list[str]) -> str:
    if any(f.endswith(".csproj") or f.endswith(".slnx") or f.endswith(".sln") for f in entries):
        return "roslyn-dump"
    if "CMakeLists.txt" in entries:
        return "clang-uml"
    if "pyproject.toml" in entries or "requirements.txt" in entries:
        return "griffe+pycalls"
    return "none"

def collectorFromSelect(text: str) -> Optional[str]:
    try:
        got: Any = json.loads(text)
    except Exception:
        return None
    
    if isinstance(got, dict):
        d = cast(dict[str, Any], got)
        if "collector" in d:
            c = d["collector"]
            return c if isinstance(c, str) and c else None
    return None
