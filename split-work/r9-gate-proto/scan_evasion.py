import ast, glob, os, sys
ROOT = sys.argv[1]
for top in sys.argv[2:]:
    for p in sorted(glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True)):
        if os.path.basename(p).startswith("test_") or "__pycache__" in p: continue
        tree = ast.parse(open(p,encoding="utf-8").read())
        for n in ast.walk(tree):
            # f-strings: sum of literal parts
            if isinstance(n, ast.JoinedStr):
                lit = "".join(v.value for v in n.values if isinstance(v, ast.Constant))
                if lit.count("\n") >= 6 or len(lit) >= 200:
                    print("FSTR %s:%d nl=%d len=%d" % (os.path.relpath(p,ROOT), n.lineno, lit.count("\n"), len(lit)))
            # list/tuple of string literals joined
            if isinstance(n, (ast.List, ast.Tuple)) and len(n.elts) >= 6 and all(isinstance(e, ast.Constant) and isinstance(e.value,str) for e in n.elts):
                tot = sum(len(e.value) for e in n.elts)
                if tot >= 200:
                    print("LIST %s:%d n=%d len=%d" % (os.path.relpath(p,ROOT), n.lineno, len(n.elts), tot))
            # BinOp + chains of strings
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                parts=[]; ok=True
                def flat(x):
                    if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add):
                        flat(x.left); flat(x.right)
                    elif isinstance(x, ast.Constant) and isinstance(x.value,str):
                        parts.append(x.value)
                flat(n)
                s="".join(parts)
                if s.count("\n")>=6 or len(s)>=200:
                    print("ADD %s:%d nl=%d len=%d" % (os.path.relpath(p,ROOT), n.lineno, s.count("\n"), len(s)))
