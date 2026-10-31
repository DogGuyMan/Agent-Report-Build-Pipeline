import ast, glob, os, sys
ROOT = sys.argv[1]
def code_files():
    out=[]
    for top in ("runner","viz"):
        for p in glob.glob(os.path.join(ROOT,top,"**","*.py"),recursive=True):
            if not os.path.basename(p).startswith("test_") and "__pycache__" not in p: out.append(p)
    return sorted(out)
def docstring_nodes(tree):
    ids=set()
    for n in ast.walk(tree):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body:
            b=n.body[0]
            if isinstance(b,ast.Expr) and isinstance(b.value,ast.Constant) and isinstance(b.value.value,str): ids.add(id(b.value))
    return ids
# gate 1 with JoinedStr
hits=[]
consts=set()
for p in code_files():
    tree=ast.parse(open(p,encoding="utf-8").read()); docs=docstring_nodes(tree)
    for n in ast.walk(tree):
        if isinstance(n,ast.JoinedStr):
            s="".join(v.value for v in n.values if isinstance(v,ast.Constant))
        elif isinstance(n,ast.Constant) and isinstance(n.value,str) and id(n) not in docs:
            s=n.value; consts.add(s)
        else: continue
        if s.count("\n")>=6 or len(s)>=200: hits.append("%s:%d"%(os.path.relpath(p,ROOT),n.lineno))
print("gate1+fstr:", hits)
templates=[t for top in ("runner","viz") for t in glob.glob(os.path.join(ROOT,top,"**","templates","**","*"),recursive=True) if os.path.isfile(t)]
names=[os.path.basename(t) for t in templates]
print("dup basenames:", sorted({n for n in names if names.count(n)>1}))
print("orphans(exact const):", sorted(os.path.relpath(t,ROOT) for t in templates if os.path.basename(t) not in consts))
