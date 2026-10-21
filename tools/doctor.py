# <include file="machine/comments.xml" path="//term[@id='doctor.py']"/>
# 이 컴퓨터에서 무엇이 되고 무엇이 안 되는지 한 화면으로 말하는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# `npm run doctor` — 이 컴퓨터에서 무엇이 되고 무엇이 안 되는지 한 화면으로 말한다.
#
# 이 저장소는 Node 와 파이썬과 바깥 명령 여럿에 걸쳐 있다. 다른 컴퓨터로 옮기면 무엇이
# 빠졌는지가 파이프라인 한복판에서 처음 드러나므로, 이 명령이 그 실패를 앞으로 당긴다.
#
# 필수가 하나라도 없으면 exit 1. 선택은 없어도 통과시킨다 — 쓰는 갈래가 정해져 있어서다
# (C++ 만 clang-uml, C# 만 dotnet).
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.python import pythonPath  # noqa: E402

# requirements.txt 의 numpy · scipy 판이 요구하는 하한.
PYTHON_MIN = (3, 12)
# -Tsvg_inline 이 이 판부터 있다.
DOT_MIN = (10, 0, 1)


def version_of(text: str | None) -> tuple[int, ...] | None:
    """글 속 첫 x.y 또는 x.y.z 를 숫자 묶음으로. 없으면 None."""
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    if not m:
        return None
    return tuple(int(g) for g in m.groups() if g is not None)


def meets(version: str | None, minimum: tuple[int, ...] | None) -> bool:
    """버전 글이 하한 이상인가. 하한이 없으면 있기만 하면 된다."""
    if not version:
        return False
    found = version_of(version)
    return minimum is None or (found is not None and found >= minimum)


def node_minimum(root: str) -> tuple[int, ...] | None:
    """package.json 의 engines.node 하한."""
    with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
        spec = json.load(fh).get("engines", {}).get("node")
    return version_of(spec if isinstance(spec, str) else None)


def requirement_names(root: str) -> list[str]:
    """requirements.txt 의 배포 이름들. 주석과 판 조건은 뗀다."""
    names: list[str] = []
    with open(os.path.join(root, "requirements.txt"), encoding="utf-8") as fh:
        for raw in fh:
            item = raw.split("#", 1)[0].strip()
            if item:
                names.append(re.split(r"[=<>!~\[; ]", item, maxsplit=1)[0])
    return names


def bin_on_path(root: str) -> str | None:
    """PATH 의 report-spec 이 이 저장소 bin/ 의 것이면 그 경로. 아니면 None."""
    found = shutil.which("report-spec")
    if found and os.path.dirname(os.path.realpath(found)) == os.path.realpath(os.path.join(root, "bin")):
        return found
    return None


def probe(cmd: str | None, args: list[str]) -> str | None:
    """명령 하나를 돌려 첫 줄을 돌려준다. 못 돌리면 None."""
    if not cmd:
        return None
    try:
        r = subprocess.run([cmd, *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return ((r.stdout or "") + (r.stderr or "")).strip().split("\n")[0][:70]


def line(name: str, version: str | None, required: bool, minimum: tuple[int, ...] | None = None) -> str:
    """결과 줄 하나를 글자로. 하한보다 낮으면 낮음, 필수인데 없으면 없음, 선택이면 선택."""
    if meets(version, minimum):
        return "  OK   %s%s" % (name.ljust(22), version)
    if version and minimum is not None:
        return "  낮음  %s%s (최소 %s)" % (name.ljust(22), version, ".".join(map(str, minimum)))
    mark = "없음" if required else "선택"
    return "  %s  %s%s" % (mark, name.ljust(22), "(찾지 못했다)")


def main() -> int:
    py = pythonPath(ROOT, sys.platform, dict(os.environ))
    py_mods = probe(py, [
        "-c",
        "import importlib.metadata as md, sys\n"
        "m = []\n"
        "for n in sys.argv[1:]:\n"
        "    try:\n"
        "        md.version(n)\n"
        "    except md.PackageNotFoundError:\n"
        "        m.append(n)\n"
        "print('전부 있다' if not m else '빠짐: ' + ', '.join(m))",
        *requirement_names(ROOT),
    ])

    node_modules = os.path.join(ROOT, "node_modules", "esbuild")
    checks: list[tuple[str, str, str | None, bool, tuple[int, ...] | None]] = [
        ("필수", "Node", probe("node", ["--version"]), True, node_minimum(ROOT)),
        ("필수", "npm 의존성", "node_modules 설치됨" if os.path.exists(node_modules) else None, True, None),
        ("필수", "git", probe("git", ["--version"]), True, None),
        ("필수", "python", probe(py, ["--version"]), True, PYTHON_MIN),
        ("필수", "python 패키지", py_mods if py_mods and py_mods.startswith("전부") else None, True, None),
        ("필수", "Graphviz dot", probe("dot", ["-V"]), True, DOT_MIN),
        ("선택", "clang-uml (C++)", probe("clang-uml", ["--version"]), False, None),
        ("선택", "dotnet (C#)", probe("dotnet", ["--version"]), False, None),
        ("선택", "clangd", probe("clangd", ["--version"]), False, None),
        ("선택", "mmdc (Mermaid)", probe("npx", ["--no-install", "mmdc", "--version"]), False, None),
        ("선택", "bin/ 이 PATH 에", bin_on_path(ROOT), False, None),
    ]

    print("저장소 %s" % ROOT)
    print("파이썬 %s\n" % py)
    group = ""
    for g, name, ver, required, minimum in checks:
        if g != group:
            print("── %s ──" % g)
            group = g
        print(line(name, ver, required, minimum))

    print("\n── 골든 저장소 환경변수 (없으면 해당 테스트를 건너뛴다) ──")
    for v in ("GRAPHICS_REPO", "CSHARP_REPO", "CPP_REPO"):
        val = os.environ.get(v)
        mark = "OK " if val and os.path.exists(val) else "없음"
        print("  %s  %s%s" % (mark, v.ljust(22), val or "(설정 안 됨)"))

    missing = [name for _, name, ver, required, minimum in checks if required and not meets(ver, minimum)]
    if missing:
        print("\n필수 %d개가 없거나 판이 낮다: %s" % (len(missing), ", ".join(missing)), file=sys.stderr)
        print("설치 방법은 README.md 를 보라. 저장소 의존성은 npm run setup 이 깐다.", file=sys.stderr)
        return 1
    print("\n필수 항목이 전부 있다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
