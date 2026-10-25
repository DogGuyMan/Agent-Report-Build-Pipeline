#!/usr/bin/env python3
"""리소스로 옮기기 전후의 글을 고정 입력으로 찍는다 — `capture.py <저장소> <출력폴더> <샤드폴더>`.

이름마다 `<출력폴더>/<이름>.txt` 하나. 끝 줄바꿈은 하나로 맞춘다(리소스 절은 줄바꿈 하나로 끝난다).
샤드폴더는 전후 두 번 다 같은 경로여야 한다 — 재조사 절이 그 경로를 글에 싣는다.
"""
import os
import sys
import tempfile

ROOT, OUT, SHARDS = (os.path.abspath(p) for p in sys.argv[1:4])
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner"), os.path.join(ROOT, "machine")]
os.makedirs(OUT, exist_ok=True)
os.makedirs(SHARDS, exist_ok=True)

from mode1.lang import LangHintStage  # noqa: E402
from mode1.survey import AnnotateSymbolsStage as S  # noqa: E402
from mode1.wiki import OutlineWikiStage, WriteWikiStage  # noqa: E402
from runner.wiki.build import sidebarFrom, vitepressConfig  # noqa: E402
import run_mode1_5  # noqa: E402
import run_mode2  # noqa: E402
from viz.init import writeSkeleton  # noqa: E402


def put(name: str, text: str) -> None:
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(text.rstrip("\n") + "\n")
    with open(os.path.join(OUT, name + ".raw"), "w", encoding="utf-8") as f:
        f.write(text)


batch = {"id": "L0-B1", "files": ["a.py"],
         "symbols": [{"id": "n1", "name": "f", "kind": "function", "file": "a.py", "line": 1,
                      "depends_on": ["n2"]}]}
put("lang-hint", LangHintStage.hint_prompt("# README\n본문\n"))
put("annotate-batch.full", S.survey_batch_prompt(
    "/대상", "/도구", batch, [{"name": "g", "means": "뜻"}], targets=["a.py"], total=3,
    pending=[{"name": "h", "kind": "function", "file": "b.py", "line": "2"}], name_of={"n2": "g"}))
put("annotate-batch.bare", S.survey_batch_prompt("/대상", "/도구", batch, []))
put("annotate-nonnode", S.nonnode_prompt("/대상", "/도구"))
put("annotate-pass2", S.pass2_prompt("/대상", "/도구", "L0-B1", "a.py", {"f": {"kind": "function"}},
                                     {"g": {"means": "뜻", "does": "함"}}))
S.quarantine(SHARDS, "L0-B1", S.check_shard(b"{", "L0-B1", "/x.json"))
put("annotate-retry", S.survey_batch_prompt("/대상", "/도구", batch, [], **S.retry_inputs(SHARDS, "L0-B1")))
put("outline-wiki", OutlineWikiStage.wiki_catalogue_prompt("/대상", "/도구"))
put("write-wiki", WriteWikiStage.wiki_page_prompt(
    "/대상", "/도구", {"file": "index.md", "title": "개요", "symbols": ["f"]}, [{"fname": "a.md", "title": "A"}]))
put("mode2-agent.bare", run_mode2.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구"))
put("mode2-agent.terms", run_mode2.agent_prompt("/프로젝트", "슬러그", "2026-01-01-슬러그-design.md", "/도구",
                                                terms_json="/프로젝트/specs/슬러그/terms.json"))
put("mode1_5-ask", run_mode1_5.ask_argv("/도구", "/계획.md", "/작업", "/py")[-1])
put("vitepress-config", vitepressConfig("대상", sidebarFrom(["index.md", "a.md"]), "/out"))
with tempfile.TemporaryDirectory() as d:
    writeSkeleton(d, "슬러그", "2026-01-01", "제목 `백틱`", "main", "v1")
    for name in ("data.ts", "report.tsx"):
        with open(os.path.join(d, name), encoding="utf-8") as f:
            put("skeleton-" + name, f.read())
print(OUT)
