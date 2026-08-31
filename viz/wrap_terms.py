import re
from typing import Any, Callable, Match, Pattern, Dict, List

SKIP_TAGS = {"script", "style", "svg", "code", "pre", "summary", "h1", "h2", "h3", "th", "title", "textarea"}
SKIP_CLASSES = {"term-ref", "term-card", "mono", "term-groups", "term-graph", "svg-wrap"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

def termPattern(terms: List[str]) -> Pattern[str] | None:
    if not terms:
        return None
    sorted_terms = sorted(terms, key=len, reverse=True)
    alts: List[str] = []
    for t in sorted_terms:
        lead = r"(?<![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", t[0]) else ""
        alts.append(lead + re.escape(t) + r"(?![A-Za-z0-9_])")
    
    return re.compile("|".join(alts))

def skipsByClass(tag: str) -> bool:
    m = re.search(r'\sclass=["\']([^"\']*)["\']', tag)
    if not m: return False
    cls = m.group(1).split()
    return any(c in SKIP_CLASSES for c in cls)

def wrapTerms(html: str, refs: Dict[str, str]) -> str:
    if not refs: return html
    pattern = termPattern(list(refs.keys()))
    if not pattern: return html
    
    tagRe = re.compile(r'<\/?([A-Za-z][A-Za-z0-9-]*)\b[^>]*>|<!--[\s\S]*?-->')
    stack: List[Dict[str, Any]] = []
    
    def is_skipping() -> bool:
        return any(s["skip"] for s in stack)
        
    def replace_text(s: str) -> str:
        if is_skipping() or not s:
            return s
        return pattern.sub(lambda m: refs.get(m.group(0), m.group(0)), s)
        
    out: List[str] = []
    last = 0
    for m in tagRe.finditer(html):
        out.append(replace_text(html[last:m.start()]))
        tag = m.group(0)
        last = m.end()
        out.append(tag)
        
        if tag.startswith("<!--"):
            continue
            
        name = m.group(1).lower()
        if tag.startswith("</"):
            idx = -1
            for i in range(len(stack) - 1, -1, -1):
                if stack[i]["name"] == name:
                    idx = i
                    break
            if idx >= 0:
                stack = stack[:idx]
        elif name not in VOID_TAGS and not tag.endswith("/>"):
            stack.append({"name": name, "skip": name in SKIP_TAGS or skipsByClass(tag)})
            
    out.append(replace_text(html[last:]))
    return "".join(out)
