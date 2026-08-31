import os
import subprocess
import sys
from typing import Any, cast, Callable, Mapping

BREW_FORMULAE: list[str] = ["llvm@22", "llvm"]

def clangDocCandidates(env: Mapping[str, str], prefixes: list[str]) -> list[str]:
    out: list[str] = []
    if env.get("CLANG_DOC"):
        out.append(env["CLANG_DOC"])
    for p in prefixes:
        out.append(os.path.join(p, "bin", "clang-doc"))
    for d in env.get("PATH", "").split(os.pathsep):
        if d:
            out.append(os.path.join(d, "clang-doc"))
    return out

def brewPrefixes(run: Callable[..., Any] = subprocess.run) -> list[str]:
    out: list[str] = []
    for formula in BREW_FORMULAE:
        try:
            r = run(["brew", "--prefix", formula], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout:
                out.append(r.stdout.strip())
        except Exception:
            pass
    return out

def clangDocPath(env: Mapping[str, str] | None = None, exists: Callable[[str], bool] = os.path.exists, prefixes: list[str] | None = None) -> str | None:
    if env is None:
        env = cast(Mapping[str, str], os.environ)
    if prefixes is None:
        prefixes = brewPrefixes()
    for c in clangDocCandidates(env, prefixes):
        if exists(c):
            return c
    return None

def clangDocArgs(outDir: str, repo: str, compdbPath: str, flags: list[str] | None = None) -> list[str]:
    if flags is None:
        flags = []
    out: list[str] = [
        "--executor=all-TUs", "--format=json",
        "--output", outDir,
        "--source-root", repo,
        "--ignore-map-errors"
    ]
    for f in flags:
        out.extend(["--extra-arg", f])
    out.append(compdbPath)
    return out

if __name__ == "__main__":
    found = clangDocPath()
    print(found if found else "clang-doc 을 못 찾았다. CLANG_DOC 환경변수로 알려 주거나 brew install llvm 하라.")
    sys.exit(0 if found else 1)
