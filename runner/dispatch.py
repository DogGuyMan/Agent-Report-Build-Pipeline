import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.python import pythonPath  # noqa: E402

def resolve_script(table: dict[str, str], cmd: str) -> str | None:
    """명령 이름을 스크립트 경로로 바꾼다. 표에 없으면 None."""
    if not cmd:
        return None
    return table.get(cmd)

def run_dispatch(root: str, table: dict[str, str], argv: list[str], usage: str) -> None:
    if not argv:
        print(usage, file=sys.stderr)
        sys.exit(1)
        
    cmd = argv[0]
    rest = argv[1:]
    
    script = resolve_script(table, cmd)
    if not script:
        print(usage, file=sys.stderr)
        sys.exit(1)
        
    script_path = os.path.join(root, script)
    
    # 해석기는 확장자로 고른다. `runner/term/*.mjs` 셋이 아직 JS 라 이 갈림이 필요하다.
    # 파이썬 경로는 박지 않는다 — tools/python.py 가 .venv → PATH 순으로 찾는다.
    runner = pythonPath(root, sys.platform, dict(os.environ)) if script.endswith(".py") else "node"

    res = subprocess.run([runner, script_path] + rest)
    sys.exit(res.returncode)
