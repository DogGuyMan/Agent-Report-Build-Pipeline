import ast, glob, os, sys
ROOT = sys.argv[1]
tops = sys.argv[2:]
def docstring_nodes(tree):
    ids=set()
    for n in ast.walk(tree):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body:
            b=n.body[0]
            if isinstance(b,ast.Expr) and isinstance(b.value,ast.Constant) and isinstance(b.value.value,str):
                ids.add(id(b.value))
    return ids
for top in tops:
    for p in sorted(glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True)):
        if os.path.basename(p).startswith("test_") or "__pycache__" in p: continue
        tree = ast.parse(open(p,encoding="utf-8").read())
        docs = docstring_nodes(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value,str) and id(n) not in docs:
                if n.value.count("\n")>=6 or len(n.value)>=200:
                    print("%s:%d nl=%d len=%d %r" % (os.path.relpath(p,ROOT), n.lineno, n.value.count("\n"), len(n.value), n.value[:80]))
