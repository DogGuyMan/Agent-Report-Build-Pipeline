import sys
import subprocess
import os

def resolve_script(table: dict[str, str], cmd: str) -> str | None:
    if not cmd:
        return None
    # We don't have prototype pollution in Python dicts like in JS
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
    
    # Determine runner by extension
    runner = "python3" if script.endswith(".py") else "node"
    
    res = subprocess.run([runner, script_path] + rest)
    sys.exit(res.returncode)
