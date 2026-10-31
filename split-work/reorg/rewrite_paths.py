#!/usr/bin/env python3
"""코드 · 설정 · 스크립트 안의 옛 경로를 새 경로로 — 경로 토큰, import 문, ROOT 사슬, sys.path 의 디렉토리 이름.
줄 수를 바꾸지 않는다. 문서와 terms-reading.json 은 remap_citations.py 의 몫이다(줄 번호까지 옮긴다)."""
import os
import re
import subprocess
import sys

from reorg_lib import ROOT, TOKEN, dotted_map, load_map, map_dotted, map_token

TARGET_PREFIXES = ("bin/", "codewiki/", "term/", "spec/", "core/", "common/", "tools/", "test/", "qa/",
                   ".github/workflows/", "split-work/")
TARGET_EXACT = {"package.json", "pyrightconfig.json", "tsconfig.json", ".gitignore",
                "resource/spec/config.toml", "resource/codewiki/samples/OBSERVATION-template.md"}
SKIP_SUFFIX = (".png", ".svg", ".pdf", ".json", ".lock", ".csproj", ".cs")   # 설정 JSON 셋은 TARGET_EXACT 로 들어온다
IMPORT_RE = re.compile(r"^(\s*)(from|import)\s+([A-Za-z_][\w.]*)(.*)$")
FLAT_CORE = [
    (re.compile(r"^(\s*)import pipeline(\s*(?:#.*)?)$"), r"\1from core import pipeline\2"),
    (re.compile(r"^(\s*)import pipeline as (\w+)(\s*(?:#.*)?)$"), r"\1from core import pipeline as \2\3"),
    (re.compile(r"^(\s*)from pipeline import "), r"\1from core.pipeline import "),
    (re.compile(r"^(\s*)import measure(\s*(?:#.*)?)$"), r"\1from core import measure\2"),
    (re.compile(r"^(\s*)import measure as (\w+)(\s*(?:#.*)?)$"), r"\1from core import measure as \2\3"),
    (re.compile(r"^(\s*)from measure import "), r"\1from core.measure import "),
    (re.compile(r"^(\s*)import pipeline, measure(\s*(?:#.*)?)$"), r"\1from core import pipeline, measure\2"),
]
ROOT_CHAIN = re.compile(r"^(?P<head>\s*\w+\s*=\s*)(?P<chain>(?:os\.path\.dirname\()+)os\.path\.abspath\(__file__\)(?P<tail>\)+)(?P<rest>.*)$")
SYSPATH_DIR = re.compile(r'os\.path\.join\((ROOT|root|_ROOT), "(runner|machine|viz)"\)')
# 파일의 새 최상위 폴더 → sys.path 에 적힌 옛 디렉토리 이름 → 그 모듈들이 이제 사는 자리
MODE_DIRS = {
    "codewiki": {"runner": '"codewiki", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"codewiki", "python", "viz"'},
    "term": {"runner": '"term", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "spec": {"runner": '"spec", "python", "runner"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "core": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "common": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
    "tools": {"runner": '"core"', "machine": '"codewiki", "python", "machine"', "viz": '"spec", "python", "viz"'},
}


def mode_of(new_rel: str) -> str:
    parts = new_rel.split("/")
    if parts[0] in ("test", "qa") and len(parts) > 1 and parts[1] in MODE_DIRS:
        return parts[1]
    return parts[0] if parts[0] in MODE_DIRS else "core"


def rewrite(text: str, new_rel: str, old_rel: str | None, moved: dict[str, str], dot: dict[str, str], report: list[str]) -> str:
    out: list[str] = []
    is_code = new_rel.endswith(".py") or new_rel.startswith("bin/")
    for line in text.split("\n"):
        line = TOKEN.sub(lambda m: map_token(m.group("path"), moved, report, new_rel) + (m.group("ln") or ""), line)
        if is_code:
            m = IMPORT_RE.match(line)
            if m:
                line = m.group(1) + m.group(2) + " " + map_dotted(m.group(3), dot) + m.group(4)
            for pat, rep in FLAT_CORE:
                line = pat.sub(rep, line)
            if old_rel is not None and old_rel != new_rel:
                m = ROOT_CHAIN.match(line)
                if m:
                    n = m.group("chain").count("os.path.dirname(")
                    if n == old_rel.count("/") + 1:
                        k = new_rel.count("/") + 1
                        line = m.group("head") + "os.path.dirname(" * k + "os.path.abspath(__file__)" + ")" * k + m.group("rest")
            md = MODE_DIRS[mode_of(new_rel)]
            line = SYSPATH_DIR.sub(lambda mm: "os.path.join(%s, %s)" % (mm.group(1), md[mm.group(2)]), line)
        out.append(line)
    return "\n".join(out)


def main() -> int:
    moved, _ = load_map()
    back = {n: o for o, n in moved.items()}
    dot = dotted_map(moved)
    report: list[str] = []
    tracked = [l for l in subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split("\n") if l]
    changed = 0
    for rel in tracked:
        if rel in TARGET_EXACT:
            pass
        elif (not rel.startswith(TARGET_PREFIXES) or rel.endswith(SKIP_SUFFIX) or rel.startswith(("resource/", "split-work/reorg/"))
              or rel == "split-work/README.md"):   # 줄 인용이 있어 remap_citations.py 가 줄까지 옮긴다
            continue
        p = os.path.join(ROOT, rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        new = rewrite(text, rel, back.get(rel), moved, dot, report)
        if new != text:
            assert new.count("\n") == text.count("\n"), rel
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)
            changed += 1
    print("고친 파일:", changed)
    print("\n".join(sorted(set(report))) or "손으로 볼 상대 경로 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
