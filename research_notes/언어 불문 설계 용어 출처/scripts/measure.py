"""Measure glossary entries and prose parenthetical counts for probe terms."""
import sys, os, re, json, glob, collections

ROOT = sys.argv[1]
OUT = sys.argv[2]

PROBE = [
 "side effect","precondition","postcondition","invariant","single source of truth",
 "single responsibility principle","open-closed principle","Liskov substitution principle",
 "interface segregation principle","dependency inversion principle","common closure principle",
 "dependency injection","inversion of control","coupling","cohesion","encapsulation",
 "information hiding","abstraction","polymorphism","inheritance","composition","interface",
 "layer","layered architecture","layering violation","separation of concerns",
 "circular dependency","dependency graph","call graph","call tree","caller","callee",
 "data flow","deterministic","idempotent","granularity","testability","representation",
 "design pattern","singleton","factory method","observer","strategy","adapter","facade",
 "decorator","visitor","code smell","refactoring","technical debt","convention","bisect",
 "bounded context","ubiquitous language","production code","test code","prerequisite",
 "edge","node","vertex","tree","stage","pipeline"]

def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[_\-/–]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?<=[a-z])(es|s)$", "", s) if not s.endswith("ss") else s
    return s

PROBE_N = {norm(p): p for p in PROBE}

def eng_regex(p):
    words = p.split(" ")
    parts = []
    for w in words:
        sub = re.split(r"-", w)
        parts.append(r"[\-\s/–]?".join(re.escape(x) for x in sub))
    body = r"[\s\-/–]?".join(parts)
    return body + r"(?:s|es)?"

HANGUL_WORD = r"[가-힣]+"
PAT = {}
for p in PROBE:
    e = eng_regex(p)
    # forward: Korean (1-4 words) then (English) ; English must be whole content of parens
    PAT[p] = (re.compile(r"((?:[가-힣]+[ ]){0,3}[가-힣]+)[ ]?\([ ]*(" + e + r")[ ]*\)", re.I),
              re.compile(r"(?<![A-Za-z])(" + e + r")[ ]?\([ ]*((?:[가-힣]+[ ]){0,3}[가-힣]+)[ ]*\)", re.I))

def strip_md(text):
    # front matter
    if text.startswith("---"):
        m = re.match(r"---\n.*?\n---\n", text, re.S)
        if m: text = text[m.end():]
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", " ", text, flags=re.S | re.M)
    text = re.sub(r"\{\{[<%].*?[%>]\}\}", " ", text, flags=re.S)
    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    return text

def po_msgstrs(path):
    out = []
    cur = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("msgstr "):
                cur = [line[7:].strip()]
                out.append(cur)
            elif line.startswith('"') and cur is not None:
                cur.append(line.strip())
            else:
                cur = None
    res = []
    for parts in out:
        s = "".join(json.loads(x) if x.startswith('"') else "" for x in parts)
        res.append(s)
    return res

def strip_rst(text):
    text = re.sub(r"``.*?``", " ", text)
    text = re.sub(r":[a-zA-Z:]+:`[^`]*`", " ", text)
    text = re.sub(r"`[^`]*`_?", " ", text)
    return text

def prose_docs(name):
    if name == "k8s":
        files = glob.glob(os.path.join(ROOT, "k8s/content/ko/**/*.md"), recursive=True)
        for fp in files:
            with open(fp, encoding="utf-8") as f: yield fp, strip_md(f.read())
    elif name == "mdn":
        files = glob.glob(os.path.join(ROOT, "mdn/files/ko/**/*.md"), recursive=True)
        for fp in files:
            rel = os.path.relpath(fp, os.path.join(ROOT, "mdn/files/ko"))
            if rel.startswith("conflicting") or rel.startswith("orphaned"): continue
            with open(fp, encoding="utf-8") as f: yield fp, strip_md(f.read())
    elif name == "pyko":
        files = glob.glob(os.path.join(ROOT, "pyko/**/*.po"), recursive=True)
        for fp in files:
            if "/out/" in fp: continue
            yield fp, "\n".join(strip_rst(s) for s in po_msgstrs(fp))

def glossary(name):
    rows = []
    if name == "k8s":
        for fp in sorted(f for f in glob.glob(os.path.join(ROOT, "k8s/content/ko/docs/reference/glossary/*.md")) if not f.endswith("/index.md")):
            t = open(fp, encoding="utf-8").read()
            fm = re.match(r"---\n(.*?)\n---", t, re.S).group(1)
            title = re.search(r"^title:\s*(.*)$", fm, re.M).group(1).strip()
            gid = re.search(r"^id:\s*(.*)$", fm, re.M).group(1).strip()
            tags = re.findall(r"^\s*-\s*(\S+)", fm.split("tags:")[1], re.M) if "tags:" in fm else []
            m = re.search(r"\(원문,\s*(.*?)\)\s*$", title)
            eng = m.group(1) if m else gid.replace("-", " ")
            ko = re.sub(r"\s*\(원문,.*?\)\s*$", "", title)
            rows.append(dict(file=os.path.relpath(fp, ROOT), id=gid, en=eng, ko=ko, title=title, tags=tags))
    elif name == "mdn":
        for fp in sorted(glob.glob(os.path.join(ROOT, "mdn/files/ko/glossary/**/index.md"), recursive=True)):
            t = open(fp, encoding="utf-8").read()
            fm = re.match(r"---\n(.*?)\n---", t, re.S).group(1)
            title = re.search(r"^title:\s*(.*)$", fm, re.M).group(1).strip().strip('"').strip("'")
            slug = re.search(r"^slug:\s*(.*)$", fm, re.M).group(1).strip()
            segs = slug.split("/")[1:]
            eng = segs[0].replace("_", " ") if segs else ""
            rows.append(dict(file=os.path.relpath(fp, ROOT), slug=slug, en=eng, qual="/".join(segs[1:]), ko=title))
    elif name == "pyko":
        fp = os.path.join(ROOT, "pyko/glossary.po")
        cur = {}
        entries = []
        state = None
        ref = None
        for line in open(fp, encoding="utf-8"):
            if line.startswith("#:"): ref = line[2:].strip()
            elif line.startswith("msgid "):
                cur = dict(ref=ref, msgid=[line[6:].strip()], msgstr=[]); state = "id"
            elif line.startswith("msgstr "):
                cur["msgstr"].append(line[7:].strip()); state = "str"
            elif line.startswith('"') and state:
                cur["msg" + state].append(line.strip()) if state == "id" else cur["msgstr"].append(line.strip())
            elif line.strip() == "" and cur:
                entries.append(cur); cur = {}; state = None
        if cur: entries.append(cur)
        for e in entries:
            mid = "".join(json.loads(x) for x in e["msgid"])
            mstr = "".join(json.loads(x) for x in e["msgstr"])
            if not mid: continue
            # term heading heuristic: short, no sentence period, no colon at end
            is_term = len(mid) <= 60 and not re.search(r"[.:]\s*$", mid) and "\n" not in mid
            rows.append(dict(ref=e["ref"], en=mid, ko=mstr, is_term=is_term))
    return rows

res = {}
for name in ["k8s", "mdn", "pyko"]:
    g = glossary(name)
    # probe hits in glossary
    hits = []
    for r in g:
        if name == "pyko" and not r["is_term"]: continue
        n = norm(r["en"].strip("`"))
        if n in PROBE_N:
            hits.append(dict(probe=PROBE_N[n], **r))
    # partial: probe term occurs as whole words inside the entry term
    partial = []
    for r in g:
        if name == "pyko" and not r["is_term"]: continue
        n = norm(r["en"].strip("`"))
        for pn, p in PROBE_N.items():
            if n != pn and re.search(r"\b" + re.escape(pn) + r"(s|es)?\b", n):
                partial.append(dict(probe=p, **r))
    # prose
    fwd = collections.defaultdict(collections.Counter)
    rev = collections.defaultdict(collections.Counter)
    fwd_files = collections.defaultdict(set)
    nfiles = 0; nchars = 0
    allpar = 0
    for fp, text in prose_docs(name):
        nfiles += 1; nchars += len(text)
        allpar += len(re.findall(r"[가-힣]+[ ]?\([ ]*[A-Za-z][A-Za-z \-]*[ ]*\)", text))
        for p, (pf, pr) in PAT.items():
            for m in pf.finditer(text):
                ko = m.group(1).split(" ")
                k = min(len(p.split(" ")), len(ko), 3)
                fwd[p][" ".join(ko[-k:])] += 1
                fwd_files[p].add(os.path.relpath(fp, ROOT))
            for m in pr.finditer(text):
                ko = m.group(2)
                rev[p][ko] += 1
    res[name] = dict(n_glossary=len(g), n_terms=(sum(1 for r in g if r.get("is_term", True))),
                     hits=hits, partial=partial,
                     prose_files=nfiles, prose_chars=nchars, all_hangul_paren_english=allpar,
                     fwd={p: dict(c.most_common()) for p, c in fwd.items()},
                     fwd_files={p: len(s) for p, s in fwd_files.items()},
                     rev={p: dict(c.most_common()) for p, c in rev.items()},
                     glossary=g)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("probe terms:", len(PROBE))
for name, r in res.items():
    print(name, "glossary rows", r["n_glossary"], "term rows", r["n_terms"], "hits", len(r["hits"]), "partial", len(r["partial"]),
          "prose files", r["prose_files"], "chars", r["prose_chars"], "allpar", r["all_hangul_paren_english"],
          "probe fwd total", sum(sum(v.values()) for v in r["fwd"].values()), "probe terms with fwd", len(r["fwd"]),
          "rev total", sum(sum(v.values()) for v in r["rev"].values()), "terms with rev", len(r["rev"]))
