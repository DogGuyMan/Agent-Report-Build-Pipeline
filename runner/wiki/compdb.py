import os
import json
import re
from typing import Any

EXTERNAL_MARKERS: list[str] = [
  "/vcpkg_installed/", "/_deps/", "/node_modules/", "/Qt/", "/homebrew/",
  "autogen", "/CMakeFiles/", "moc_", "qrc_", "ui_",
]

SIDECAR_DIRS: list[str] = [".qtc_clangd", ".cache"]

def findCompdbs(repo: str) -> list[str]:
    out: list[str] = []
    def walk(dir_path: str, depth: int) -> None:
        if depth > 6:
            return
        try:
            entries = os.listdir(dir_path)
        except Exception:
            return
        for name in entries:
            p = os.path.join(dir_path, name)
            if name == "compile_commands.json":
                out.append(p)
                continue
            if name.startswith(".") and name not in SIDECAR_DIRS:
                continue
            if name in ["vcpkg_installed", "node_modules", ".git", "out"]:
                continue
            try:
                if os.path.isdir(p):
                    walk(p, depth + 1)
            except Exception:
                pass
    walk(repo, 0)
    primary = [p for p in out if not any(f"/{s}/" in p.replace('\\', '/') for s in SIDECAR_DIRS)]
    return sorted(primary if primary else out)

def mergeEntries(lists: list[list[dict[str, Any]]], repo: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for lst in lists:
        for e in lst:
            f = e.get("file")
            if not isinstance(f, str) or f in seen:
                continue
            if not f.startswith(repo):
                continue
            if any(m in f for m in EXTERNAL_MARKERS):
                continue
            seen.add(f)
            out.append(e)
    return out

def relativeFiles(entries: list[dict[str, Any]], repo: str) -> list[str]:
    repo_len = len(repo) + 1
    files: set[str] = {str(e["file"])[repo_len:] for e in entries if "file" in e}
    return sorted(list(files))

def clangUmlConfig(compdbDir: str, repo: str, outDir: str, files: list[str], flags: list[str], paths: list[str]) -> str:
    lines: list[str] = [
        "# report-wiki prep 이 생성한다. 손으로 고치지 말 것 — 다음 실행에서 덮어쓴다.",
        "# 대상 파일은 합친 compile_commands.json 에서 열거한다(글로브는 깊이 4에서 죽는다).",
        f"compilation_database_dir: {compdbDir}",
        f"relative_to: {repo}",
        f"output_directory: {outDir}",
    ]
    if flags:
        lines.append("add_compile_flags:")
        for f in flags:
            lines.append(f"  - {f}")
    lines.extend(["diagrams:", "  full_class:", "    type: class", "    glob:"])
    for f in files:
        lines.append(f"      - {f}")
    if paths:
        lines.append("    include:")
        lines.append(f"      paths: [{', '.join(paths)}]")
    return "\n".join(lines) + "\n"

def readAuthorConfig(path: str) -> dict[str, list[str]]:
    if not os.path.exists(path):
        return {"flags": [], "paths": []}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    flags: list[str] = []
    m = re.search(r"^add_compile_flags:\s*\n((?:\s+-\s.*\n)+)", text, re.MULTILINE)
    if m:
        for l in m.group(1).split("\n"):
            t = re.sub(r"^\s*-\s*", "", l).strip()
            if t:
                flags.append(t)
    inline = re.search(r"^add_compile_flags:\s*\[([^\]]*)\]", text, re.MULTILINE)
    if inline:
        for t in inline.group(1).split(","):
            s = t.strip()
            if s:
                flags.append(s)
    p = re.search(r"paths:\s*\[([^\]]*)\]", text)
    paths: list[str] = [s.strip() for s in p.group(1).split(",") if s.strip()] if p else []
    return {"flags": flags, "paths": paths}
