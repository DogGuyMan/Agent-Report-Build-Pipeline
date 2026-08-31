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
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.python import pythonPath  # noqa: E402


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


def line(name: str, version: str | None, required: bool) -> str:
    """결과 줄 하나를 글자로. 필수인데 없으면 없음, 선택이면 선택."""
    mark = "OK " if version else ("없음" if required else "선택")
    return "  %s  %s%s" % (mark, name.ljust(22), version or "(찾지 못했다)")


def main() -> int:
    py = pythonPath(ROOT, sys.platform, dict(os.environ))
    py_mods = probe(py, [
        "-c",
        "import importlib.util as u;"
        "m=[n for n in ('networkx','numpy','scipy','pytest') if u.find_spec(n) is None];"
        "print('전부 있다' if not m else '빠짐: '+', '.join(m))",
    ])

    node_modules = os.path.join(ROOT, "node_modules", "esbuild")
    checks: list[tuple[str, str, str | None, bool]] = [
        ("필수", "Node", probe("node", ["--version"]), True),
        ("필수", "npm 의존성", "node_modules 설치됨" if os.path.exists(node_modules) else None, True),
        ("필수", "git", probe("git", ["--version"]), True),
        ("필수", "python", probe(py, ["--version"]), True),
        ("필수", "python 패키지", py_mods if py_mods and py_mods.startswith("전부") else None, True),
        ("필수", "Graphviz dot", probe("dot", ["-V"]), True),
        ("선택", "clang-uml (C++)", probe("clang-uml", ["--version"]), False),
        ("선택", "dotnet (C#)", probe("dotnet", ["--version"]), False),
        ("선택", "clangd", probe("clangd", ["--version"]), False),
        ("선택", "mmdc (Mermaid)", probe("npx", ["--no-install", "mmdc", "--version"]), False),
    ]

    print("저장소 %s" % ROOT)
    print("파이썬 %s\n" % py)
    group = ""
    for g, name, ver, required in checks:
        if g != group:
            print("── %s ──" % g)
            group = g
        print(line(name, ver, required))

    print("\n── 골든 저장소 환경변수 (없으면 해당 테스트를 건너뛴다) ──")
    for v in ("GRAPHICS_REPO", "CSHARP_REPO", "CPP_REPO"):
        val = os.environ.get(v)
        mark = "OK " if val and os.path.exists(val) else "없음"
        print("  %s  %s%s" % (mark, v.ljust(22), val or "(설정 안 됨)"))

    missing = [name for _, name, ver, required in checks if required and not ver]
    if missing:
        print("\n필수 %d개가 없다: %s" % (len(missing), ", ".join(missing)), file=sys.stderr)
        print("설치 방법은 README.md 를 보라.", file=sys.stderr)
        return 1
    print("\n필수 항목이 전부 있다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
