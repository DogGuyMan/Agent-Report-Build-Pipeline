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

def norm(s):
    s = s.lower().strip(); s = re.sub(r"[_\-/–]+", " ", s); s = re.sub(r"\s+", " ", s)
    return re.sub(r"(?<=[a-z])(es|s)$", "", s) if not s.endswith("ss") else s
