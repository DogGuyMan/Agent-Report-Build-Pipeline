"""Read MS Terminology glossary xlsx (Xbench export) and match probe terms on the English source column."""
import sys, re, json, zipfile, xml.etree.ElementTree as ET, collections
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def rows(path):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
    for row in ET.fromstring(z.read(sheet)).iter("{%s}row" % NS["m"]):
        out = {}
        for c in row.findall("m:c", NS):
            ref = re.match(r"[A-Z]+", c.get("r")).group(0)
            v = c.find("m:v", NS); t = c.get("t")
            if t == "s" and v is not None: out[ref] = ss[int(v.text)]
            elif t == "inlineStr": out[ref] = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is not None: out[ref] = v.text
        yield out
sys.path.insert(0, sys.argv[1])
PROBE = json.load(open(sys.argv[2]))
def norm(s):
    s = s.lower().strip(); s = re.sub(r"[_\-/–]+", " ", s); s = re.sub(r"\s+", " ", s)
    return re.sub(r"(?<=[a-z])(es|s)$", "", s) if not s.endswith("ss") else s
PN = {norm(p): p for p in PROBE}
for path in sys.argv[3:]:
    rs = list(rows(path))
    print("==", path.split("/")[-1], "rows", len(rs), "header", rs[0])
    print("  sample", rs[1:4])
    # guess english column = header containing 'en' or first column
    hdr = rs[0]
    cols = sorted(hdr)
    en_col = next((k for k in cols if re.search(r"en[-_]?us|english|source", str(hdr[k]), re.I)), cols[0])
    tgt_col = next((k for k in cols if k != en_col and not re.search(r"pos|part|defin|id|note|status", str(hdr[k]), re.I)), cols[1])
    en_terms = collections.defaultdict(list)
    for r in rs[1:]:
        e = r.get(en_col, "")
        if e: en_terms[norm(e)].append(r.get(tgt_col, ""))
    print("  en_col", en_col, hdr.get(en_col), "tgt_col", tgt_col, hdr.get(tgt_col), "distinct en", len(en_terms))
    hits = {p: en_terms[n] for n, p in PN.items() if n in en_terms}
    print("  probe exact hits", len(hits), "/", len(PROBE))
    for p, v in hits.items(): print("    ", p, "->", v[:3])
    miss = [p for n, p in PN.items() if n not in en_terms]
    print("  misses:", miss)
    # partial: english term contains probe as words
    part = collections.Counter()
    ex = collections.defaultdict(list)
    for n in en_terms:
        for pn, p in PN.items():
            if n != pn and re.search(r"\b" + re.escape(pn) + r"\b", n):
                part[p] += 1
                if len(ex[p]) < 4: ex[p].append(n)
    print("  partial-containing entries:", dict(part))
    print("  partial examples:", dict(ex))
