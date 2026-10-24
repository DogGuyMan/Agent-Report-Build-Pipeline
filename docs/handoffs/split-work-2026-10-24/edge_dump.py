"""한 트리(old/new)의 Mode 1 프롬프트 함수를 경계 입력으로 돌려 결과를 JSON 으로 찍는다."""
import json
import os
import sys
import tempfile

tree = sys.argv[1]
sys.path.insert(0, os.path.join(tree, "runner"))
sys.path.insert(0, os.path.join(tree, "machine"))
sys.path.insert(0, tree)

from mode1 import lang as LG  # noqa: E402
from mode1 import survey as SV  # noqa: E402
from mode1 import wiki as W  # noqa: E402

A = SV.AnnotateSymbolsStage
out: dict[str, str] = {}
weird = ["", "\n", "A\n", "A\n\n", "\nA", "{{docs}}", "x {{y}} %s {0} }} {{", "<!-- section: batch -->\n본문"]

for i, d in enumerate(weird):
    out["hint%d" % i] = LG.LangHintStage.hint_prompt(d)

for i, t in enumerate([["a"], ["a", "b"], ["{{x}}", "%s"], ["a\n"]]):
    out["warm%d" % i] = A.warmup_section(t, 0 if i == 0 else 77, repo="/r")
out["warm_none"] = A.warmup_section(None, 3, repo="/r")
out["warm_empty"] = A.warmup_section([], 3, repo="/r")

for i, p in enumerate(weird[1:]):
    out["pend%d" % i] = A.pending_section(p)

batch = {"id": "L0-B{{x}}", "files": ["a.py"], "symbols": [
    {"id": "C1", "name": "a.{{f}}", "file": "a.py", "line": 3, "kind": "function", "in_cycle": False,
     "depends_on": ["C2"]},
    {"id": "C2", "name": "b%s", "file": None, "line": None, "kind": None, "in_cycle": False, "depends_on": []}]}
for i, (deps, pend, tg) in enumerate([("", "", None), ("  - x — {{y}}\n", "p\n", ["a"]),
                                       ("d", "", ["a"]), ("", "p", []), ("\n", "\n", ["\n"])]):
    out["batch%d" % i] = A.survey_batch_prompt("/r", "/root{{z}}", batch, deps, targets=tg, total=5,
                                               pending=pend, name_of={"C2": "b.{{g}}"})

out["nonnode"] = A.nonnode_prompt("/r{{a}}", "/root%s")

with tempfile.TemporaryDirectory() as d:
    faults = [{"kind": "malformed", "batch": "B", "path": "p", "at": "byte {{7}}", "detail": "a\nb",
               "fix": "%s {0}"}, {"kind": "shape", "batch": "B", "path": "p", "at": "$[0]", "detail": "",
               "fix": "\n"}]
    with open(os.path.join(d, "B.json.bad.why"), "w", encoding="utf-8") as f:
        json.dump(faults, f, ensure_ascii=False)
    out["retry"] = A.retry_section(d, "B").replace(d, "<D>")
    out["retry_none"] = A.retry_section(d, "Z")

shallow = {"a.f": {"means": "{{m}}", "shallow": ["b"]}}
out["pass2a"] = A.pass2_prompt("/r", "/root", "F{{1}}", "a{{x}}.py", shallow, {"b": {"means": "%s", "does": "{0}"}})
out["pass2b"] = A.pass2_prompt("/r", "/root", "F", "a.py", {}, {})

out["outline"] = W.OutlineWikiStage.wiki_catalogue_prompt("/r{{x}}", "/root")
for i, (pg, low) in enumerate([({"file": "index.md"}, ""), ({"file": "a.md", "title": "", "symbols": []}, "\n"),
                               ({"file": "{{f}}.md", "title": "%s", "symbols": ["a", "{{b}}"]}, "  - x — y")]):
    out["page%d" % i] = W.WriteWikiStage.wiki_page_prompt("/r", "/root", pg, low)


# ── R10 확장 — 빈 값 문구 · 목록 줄 꼴 · FIX ─────────────────────────
import subprocess  # noqa: E402
import types  # noqa: E402
from mode1 import survey_files as SF  # noqa: E402

names = {"C1": "a.f", "C2": "b.g", "C3": "c.h", "C4": "", "C5": "e{{x}}"}
merged = {"a.f": {"means": "뜻 a"}, "b.g": {"means": ""}, "c.h": None, "e{{x}}": {"means": 7},
          "z": {"means": ["l", 1]}}
dep_batches = [
    {"id": "B0", "files": [], "symbols": []},
    {"id": "B1", "files": [], "symbols": [{"id": "S", "depends_on": []}]},
    {"id": "B2", "files": [], "symbols": [{"id": "S", "depends_on": ["C1", "C2", "C3", "C4", "C5", "C9"]}]},
    {"id": "B3", "files": [], "symbols": [{"id": "S"}]},
    {"id": "B4", "files": [], "symbols": [{"id": "S", "depends_on": ["C2"]}, {"id": "T", "depends_on": ["C1"]}]},
]
for i, b in enumerate(dep_batches):
    out["dep%d" % i] = A.dep_excerpt(merged, b, names)
out["dep_empty_merged"] = A.dep_excerpt({}, dep_batches[2], names)
out["dep_z"] = A.dep_excerpt(merged, {"id": "B", "files": [], "symbols": [{"id": "S", "depends_on": ["Z"]}]},
                             {"Z": "z"})

sym_batches = [
    {"id": "Q0", "files": [], "symbols": []},
    {"id": "Q1", "files": [], "symbols": [{"id": "s", "name": "n", "kind": "class", "file": "f.py", "line": 9,
                                         "depends_on": []}]},
    {"id": "Q2", "files": [], "symbols": [{"id": "s", "name": None, "kind": None, "file": None, "line": None}]},
    {"id": "Q3", "files": [], "symbols": [{"id": "s", "name": "n", "kind": "k", "file": "f", "line": 0,
                                         "depends_on": None}]},
    {"id": "Q4", "files": [], "symbols": [{"id": "s", "name": "{{n}}", "kind": "%s", "file": "a\nb", "line": "7",
                                         "depends_on": ["C1", "X9", "C4"]},
                                        {"id": "t", "name": "m", "kind": "k", "file": "g", "line": 2,
                                         "depends_on": ["C2"]}]},
]
for i, b in enumerate(sym_batches):
    for j, dr in enumerate(["", "  - x — y", "\n"]):
        out["sym%d_%d" % (i, j)] = A.survey_batch_prompt("/r", "/root", b, dr, name_of=names)
    out["sym%d_noname" % i] = A.survey_batch_prompt("/r", "/root", b, "")

for i, deps in enumerate([{}, {"a": {}}, {"a": {"means": "", "does": ""}}, {"b": {"means": "m"}, "a": {"does": "d"}},
                          {"c": {"means": 3, "does": ["x"]}, "d{{y}}": {"means": "{{z}}", "does": "\n"}}]):
    out["p2_%d" % i] = A.pass2_prompt("/r", "/root", "F", "a.py", {}, deps)
    out["p2s_%d" % i] = A.pass2_prompt("/r", "/root", "F", "a.py", {"k": {"means": "x"}}, deps)

pages = [{"file": "a.md"}, {"file": "b.md", "title": ""}, {"file": "c.md", "title": "C", "symbols": []},
         {"file": "d.md", "title": "D", "symbols": ["s1"]}, {"file": "e{{x}}.md", "title": "%s\n"},
         {"file": "f.md", "symbols": None}]
for i, pg in enumerate(pages):
    for j, low in enumerate(["", "  - x — y", "\n"]):
        out["pg%d_%d" % (i, j)] = W.WriteWikiStage.wiki_page_prompt("/r", "/root", pg, low)

wiki = W.WriteWikiStage()
for i, done in enumerate([[], pages[:1], pages]):
    ctx = types.SimpleNamespace(wiki_levels=[0], wiki_pages=[{"file": "z.md", "title": "Z"}],
                                wiki_level_of={"z.md": 0}, repo="/nonexistent-r10", root="/root",
                                wiki_done=list(done))
    out["jobs%d" % i] = json.dumps(wiki.jobs(ctx, 0), ensure_ascii=False)
    out["jobs%d_done" % i] = json.dumps(ctx.wiki_done, ensure_ascii=False)

kinds = ("missing", "malformed", "schema", "where", "coverage")
out["FIX_items"] = json.dumps(list(A.FIX.items()), ensure_ascii=False)
out["FIX_files_items"] = json.dumps(list(SF.AnnotateFilesStage.FIX.items()), ensure_ascii=False)
out["FIX_type"] = type(A.FIX).__name__
for k in kinds:
    out["FIX_" + k] = A.FIX[k]
    f = A.fault(k, "B", "/p", "at", "detail")
    out["fault_" + k] = json.dumps(f, ensure_ascii=False)
    out["fline_" + k] = A.fault_line(f)
with tempfile.TemporaryDirectory() as d:
    with open(os.path.join(d, "B.json.bad.why"), "w", encoding="utf-8") as fh:
        json.dump([A.fault(k, "B", "/p", "at" + k, "d" + k) for k in kinds], fh, ensure_ascii=False)
    out["retry_all"] = A.retry_section(d, "B").replace(d, "<D>")
    for k in kinds:
        with open(os.path.join(d, k + ".json.bad.why"), "w", encoding="utf-8") as fh:
            json.dump([A.fault(k, k, "/p", "at", "d")], fh, ensure_ascii=False)
        out["retry_" + k] = A.retry_section(d, k).replace(d, "<D>")

with tempfile.TemporaryDirectory() as d:
    sh = os.path.join(d, "_shards")
    os.makedirs(sh)
    plan = {"target": 8, "totals": {"symbols": 1, "edges": 0, "levels": 1, "cyclic_symbols": 0},
            "layers": [{"level": 0, "symbol_count": 1, "file_count": 1, "batches": [
        {"id": "COV", "files": ["x.py"], "symbols": [{"id": "s", "name": "want", "kind": "function", "file": "x.py",
                                                     "line": 1, "in_cycle": False, "depends_on": []}]}]}]}
    with open(os.path.join(d, "batches.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh)
    good = {"kind": "function", "module": "m", "where": "x.py:1", "means": "m", "does": "d", "uses": [],
            "confidence": "HIGH", "source": "reading"}
    nowhere = dict(good)
    del nowhere["where"]
    shards = {"MAL": b"{", "SCH": json.dumps({"f": {"kind": "function"}}).encode(),
              "WHE": json.dumps({"f": nowhere}, ensure_ascii=False).encode(),
              "COV": json.dumps({"other": good}).encode(), "OK": json.dumps({"f": good}).encode()}
    for bid, raw in shards.items():
        p = os.path.join(sh, bid + ".json")
        with open(p, "wb") as fh:
            fh.write(raw)
        r = subprocess.run([sys.executable, os.path.join(tree, "runner", "check_shard.py"), p],
                           capture_output=True, text=True)
        out["cmd_" + bid] = ("%d\n%s\n%s" % (r.returncode, r.stdout, r.stderr)).replace(d, "<D>")
    os.remove(os.path.join(sh, "OK.json"))
    out["shards_missing"] = json.dumps(A.check_shards(sh, plan), ensure_ascii=False).replace(d, "<D>")
    out["shards_cov"] = json.dumps(A.check_shards(sh, plan), ensure_ascii=False).replace(d, "<D>")
    os.remove(os.path.join(sh, "COV.json"))
    out["shards_missing2"] = json.dumps(A.check_shards(sh, plan), ensure_ascii=False).replace(d, "<D>")

json.dump(out, sys.stdout, ensure_ascii=False, indent=0, sort_keys=True)
