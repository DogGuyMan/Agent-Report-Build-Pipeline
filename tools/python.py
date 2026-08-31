import os
import sys
from typing import List, Dict

def pythonCandidates(root: str, platform: str, env: Dict[str, str]) -> List[str]:
    c: List[str] = []
    if env.get("REPORT_PYTHON"):
        c.append(env["REPORT_PYTHON"])
    
    if platform == "win32":
        c.append(os.path.join(root, ".venv", "Scripts", "python.exe"))
        c.append(os.path.join(root, ".venv", "Scripts", "python"))
    else:
        c.append(os.path.join(root, ".venv", "bin", "python3"))
        c.append(os.path.join(root, ".venv", "bin", "python"))
        
    c.append("python3")
    c.append("python")
    return c

def pythonPath(root: str, platform: str, env: Dict[str, str]) -> str:
    c = pythonCandidates(root, platform, env)
    for p in c:
        if os.path.basename(p) == p:
            return p
        if os.path.exists(p):
            return p
    return "python3"
