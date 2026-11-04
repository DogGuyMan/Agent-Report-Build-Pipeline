import concurrent.futures as cf, json, os, re, shlex, subprocess, sys, time
repo, out = sys.argv[1], sys.argv[2]
db = json.load(open(os.path.join(repo, "build_ninja", "compile_commands.json")))
print("db 항목", len(db))
def argv(e):
    a = e.get("arguments") or shlex.split(e["command"])
    res, skip = [], False
    for x in a[1:]:
        if skip: skip = False; continue
        if x in ("-c",): continue
        if x == "-o": skip = True; continue
        res.append(x)
    return ["clang++"] + res
own = [e for e in db if os.path.realpath(os.path.join(e["directory"], e["file"])).startswith(os.path.realpath(repo) + "/") and "/build" not in os.path.relpath(os.path.join(e["directory"], e["file"]), repo).split("/")[0] and "_deps" not in e["file"] and "external" not in e["file"].lower() and "third" not in e["file"].lower()]
print("저장소 번역 단위", len(own))
def one(e):
    t = time.time()
    a = argv(e) + ["--analyze", "-Xclang", "-analyzer-checker=debug.DumpCallGraph", "-o", "/dev/null"]
    try:
        p = subprocess.run(a, cwd=e["directory"], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return e["file"], "timeout", ""
    return e["file"], p.returncode, p.stdout + p.stderr
edges, rc, deadline = {}, {"ok": 0, "bad": 0, "timeout": 0}, time.time() + 270
with cf.ThreadPoolExecutor(8) as ex:
    futs = [ex.submit(one, e) for e in own]
    for f in cf.as_completed(futs, timeout=280):
        name, code, text = f.result()
        rc["timeout" if code == "timeout" else ("ok" if code == 0 else "bad")] += 1
        for m in re.finditer(r"Function: (.+?) calls: ?(.*)", text):
            caller = m.group(1).strip()
            if caller == "< root >": continue
            edges.setdefault(caller, set()).update(x for x in m.group(2).split() if x)
print("결과", rc)
json.dump({k: sorted(v) for k, v in edges.items()}, open(out, "w"), ensure_ascii=False)
