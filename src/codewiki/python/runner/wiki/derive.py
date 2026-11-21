#!/usr/bin/env python3
"""derive.py — 검사를 지난 지도에서 파생물을 만든다: facts/*.md · ranking.json · 모듈 그림. derive-facts 단계와 report-wiki prep 의 꼬리가 부른다."""
import argparse
import json
import os
import sys
from typing import cast

# 이 파일은 <ROOT>/src/codewiki/python/runner/wiki/ 에 있다. 스크립트로 띄우면 sys.path[0] 이 그 폴더라
# `codewiki` 도 `common` 도 보이지 않는다 — 패키지 import 보다 먼저 `src/` 를 넣는다.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if os.path.join(ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "src"))

from codewiki.python.runner.wiki.paths import wikiPaths  # noqa: E402
from codewiki.python.runner.wiki.proc import run  # noqa: E402
from common.python import pythonPath  # noqa: E402


def derive_steps(repo: str, paths: dict[str, str], py: str, generation_id: str) -> None:
    """facts → render-modules. ranking.json 에 generation_id 를 찍는다. 이 단계의 실패는 수집 실패 기록에 적지 않는다."""
    detail = os.path.join(paths["raw"], "roslyn-dump.json")
    extra = ["--detail", detail] if os.path.exists(detail) else []
    run("facts", py, [os.path.join(ROOT, "src", "codewiki", "python", "machine", "facts.py"), paths["codegraph"], "--repo", repo,
                      "--generation", generation_id] + extra + ["-o", paths["raw"]])
    run("render-modules", py, [os.path.join(ROOT, "src", "codewiki", "python", "viz", "render_modules.py"), paths["codegraph"],
                               "-o", os.path.join(paths["raw"], "modules")])


def main() -> int:
    ap = argparse.ArgumentParser(description="검사를 지난 지도에서 facts · ranking · 모듈 그림을 만든다")
    ap.add_argument("repo")
    a = ap.parse_args()
    repo = os.path.abspath(cast(str, a.repo))
    paths = wikiPaths(repo)
    with open(paths["fingerprint"], encoding="utf-8") as f:
        manifest = cast(dict[str, object], json.load(f))
    derive_steps(repo, paths, pythonPath(ROOT, sys.platform, dict(os.environ)), str(manifest["generation_id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
