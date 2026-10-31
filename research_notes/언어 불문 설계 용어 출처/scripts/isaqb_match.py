"""iSAQB 용어집의 영어 표제어와 탐침 목록을 맞춘다. 인자: <glossary 루트> <probe.json>"""
import json, re, sys, glob, os

def norm(s):
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[-/–_]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()

root, probe_path = sys.argv[1], sys.argv[2]
probes = json.load(open(probe_path, encoding="utf-8"))
entries = []
for f in sorted(glob.glob(os.path.join(root, "docs/1-terms/*/*.adoc"))):
    t = open(f, encoding="utf-8").read()
    m = re.search(r"// tag::EN\[\]\s*\n(.*?)// end::EN\[\]", t, re.S)
    if not m:
        continue
    body = m.group(1)
    h = re.search(r"^=+ (.+)$", body, re.M)
    if not h:
        continue
    head = h.group(1).strip()
    rest = body[h.end():].strip().splitlines()
    first = next((l.strip() for l in rest if l.strip() and not l.startswith(("[", "//", "image"))), "")
    entries.append((head, os.path.relpath(f, root), first))

print("entries", len(entries))
by_norm = {}
for head, rel, first in entries:
    by_norm.setdefault(norm(head), []).append((head, rel, first))
exact, loose = [], []
for p in probes:
    n = norm(p)
    if n in by_norm:
        exact.append((p, by_norm[n][0]))
    else:
        hits = [e for k, v in by_norm.items() for e in v if re.search(r"\b" + re.escape(n) + r"\b", k)]
        if hits:
            loose.append((p, [h[0] for h in hits][:4]))
print("exact", len(exact))
for p, (head, rel, first) in exact:
    print(f"E\t{p}\t{head}\t{rel}\t{first[:110]}")
print("loose-only", len(loose))
for p, heads in loose:
    print(f"L\t{p}\t{' | '.join(heads)}")
