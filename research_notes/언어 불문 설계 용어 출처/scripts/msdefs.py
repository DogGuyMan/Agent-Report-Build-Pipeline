"""Print English definitions for probe hits in an MS glossary xlsx."""
import sys, json, re, importlib.util, os
spec = importlib.util.spec_from_file_location("x", os.path.join(os.path.dirname(os.path.abspath(__file__)), "msxlsx_lib.py"))
x = importlib.util.module_from_spec(spec); spec.loader.exec_module(x)
PROBE = json.load(open(sys.argv[1]))
PN = {x.norm(p): p for p in PROBE}
rs = list(x.rows(sys.argv[2]))
seen = 0
for r in rs[1:]:
    n = x.norm(r.get("A", ""))
    if n in PN or n in ("abstraction layer", "dependency injection container", "information hiding", "abstract"):
        print(f"{r.get('A')!s:22} | {r.get('B')!s:35} | {r.get('C','')[18:150]} | {r.get('D','')[19:]}")
print("rows", len(rs) - 1)
