"""소비자 하나를 실제 지도로 돌리며 어떤 칸을 읽는지 잰다. 쓰기는 전부 임시 폴더로 보낸다."""
import collections, json, os, runpy, sys
ROOT, name, graph, repo, out, detail = sys.argv[1:7]
M = os.path.join(ROOT, "src/codewiki/python/machine"); V = os.path.join(ROOT, "src/codewiki/python/viz"); R = os.path.join(ROOT, "src/codewiki/python/runner")
sys.path[:0] = [M, V, R, os.path.join(ROOT, "src")]
SEEN = collections.Counter()
class T(dict):
    def __init__(self, d, p):
        super().__init__(d); self.p = p
    def hit(self, k): SEEN[(self.p, k)] += 1
    def __getitem__(self, k): self.hit(k); return super().__getitem__(k)
    def get(self, k, *a): self.hit(k); return super().get(k, *a)
    def __contains__(self, k): self.hit(k); return super().__contains__(k)
    def __iter__(self): self.hit("*"); return super().__iter__()
    def keys(self): self.hit("*"); return super().keys()
    def items(self): self.hit("*"); return super().items()
    def values(self): self.hit("*"); return super().values()
def wrap(d):
    t = T(d, "$")
    for key in ("nodes", "edges", "modules"):
        if key in d:
            dict.__setitem__(t, key, [T(x, key + "[]") for x in d[key]])
    return t
real = json.load
def tracked(fp, *a, **k):
    got = real(fp, *a, **k)
    return wrap(got) if str(getattr(fp, "name", "")).endswith("codegraph.json") else got
json.load = tracked
os.makedirs(out, exist_ok=True)
def script(path, *argv):
    sys.argv = [path, *argv]
    try:
        runpy.run_path(path, run_name="__main__")
    except SystemExit:
        pass
raw = json.load.__wrapped__ if hasattr(json.load, "__wrapped__") else None
with open(graph, encoding="utf-8") as f:
    plain = real(f)
mods = collections.Counter(n["module"] for n in plain["nodes"] if n["kind"] != "external" and n["module"])
top = mods.most_common(1)[0][0]
if name == "facts":
    script(os.path.join(M, "facts.py"), graph, "--repo", repo, *(["--detail", detail] if detail != "-" else []), "-o", out)
elif name == "render_modules":
    script(os.path.join(V, "render_modules.py"), graph, "-o", os.path.join(out, "modules"))
elif name == "render_classes":
    script(os.path.join(V, "render_classes.py"), graph, "--module", top, *(["--detail", detail] if detail != "-" else []), "-o", os.path.join(out, "classes"))
elif name == "terms_db":
    script(os.path.join(M, "terms_db.py"), graph, "--repo", repo, "-o", out)
elif name == "verify_citations":
    n = next(x for x in plain["nodes"] if x["kind"] != "external")
    doc = os.path.join(out, "cite.md")
    with open(doc, "w", encoding="utf-8") as f:
        f.write("`%s` 는 `%s:%d` 에 있다.\n" % (n["name"], n["file"], n["line"]))
    script(os.path.join(M, "verify_citations.py"), doc, "--repo", repo, "--codegraph", graph)
elif name == "survey_plan":
    import survey_plan
    survey_plan.plan(wrap(plain), 8); survey_plan.plan_by_file(wrap(plain)); survey_plan.file_weights(wrap(plain))
elif name == "warmup":
    import warmup
    f = next(x["file"] for x in plain["nodes"] if x["kind"] != "external")
    warmup.blast_radius(graph, [f], 1)
elif name == "into_of":
    from mode1.survey import AnnotateSymbolsStage
    AnnotateSymbolsStage.into_of(wrap(plain))
out_rows = sorted("%s.%s" % k for k in SEEN)
print(json.dumps({"name": name, "fields": out_rows}, ensure_ascii=False))
