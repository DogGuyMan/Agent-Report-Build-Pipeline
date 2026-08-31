# <include file="machine/comments.xml" path="//term[@id='python.py']"/>
# 파이썬 해석기를 기계에 상관없이 찾아 주는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
import os
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
