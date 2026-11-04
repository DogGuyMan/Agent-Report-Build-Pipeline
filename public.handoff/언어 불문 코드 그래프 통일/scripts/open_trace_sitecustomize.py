import json, os, sys
LOG = os.environ.get("CG_TRACE_LOG")
ROOT = os.environ.get("CG_TRACE_ROOT", "")
def frames():
    out, f = [], sys._getframe(2)
    while f and len(out) < 5:
        fn = f.f_code.co_filename
        if "/lib/python" not in fn and "sitecustomize" not in fn and not fn.startswith("<"):
            out.append("%s:%d %s" % (fn.replace(ROOT + "/", ""), f.f_lineno, f.f_code.co_name))
        f = f.f_back
    return out
def hook(event, args):
    if event != "open" or not LOG or not args or not isinstance(args[0], (str, bytes)):
        return
    p = os.fsdecode(args[0])
    if not p.endswith("codegraph.json"):
        return
    mode = args[1] if len(args) > 1 else None
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"step": os.environ.get("CG_TRACE_STEP"), "script": os.path.basename(sys.argv[0]) if getattr(sys, "argv", None) else "?", "mode": mode, "stack": frames()}, ensure_ascii=False) + "\n")
sys.addaudithook(hook)
