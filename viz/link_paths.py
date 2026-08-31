import os
import re
from typing import Callable, Optional, Dict, List, Set, Any, Match

def buildIndex(repoRoot: str) -> Dict[str, str]:
    if not repoRoot or not os.path.isdir(repoRoot):
        return {}
    
    idx: Dict[str, str] = {}
    
    def walk(path: str) -> None:
        try:
            entries = os.listdir(path)
        except OSError:
            return
        
        for name in entries:
            if name in (".git", "node_modules", "out"):
                continue
            
            full = os.path.join(path, name)
            rel = os.path.relpath(full, repoRoot).replace('\\', '/')
            if name not in idx:
                idx[name] = rel
            
            if os.path.isdir(full):
                walk(full)
                
    walk(repoRoot)
    return idx

def makeResolver(bases: List[str], repoRoot: str, index: Optional[Dict[str, str]] = None) -> Callable[[str], Optional[str]]:
    actual_index = index or {}
    
    def resolve(path: str) -> Optional[str]:
        if '<' in path or '>' in path:
            return None
            
        for base in bases:
            candidate = os.path.join(base, path)
            if os.path.exists(candidate):
                try:
                    rel = os.path.relpath(candidate, repoRoot)
                    return rel.replace('\\', '/') if not rel.startswith('..') else candidate.replace('\\', '/')
                except ValueError:
                    return candidate.replace('\\', '/')
                    
        basename = os.path.basename(path)
        if basename in actual_index:
            found = actual_index[basename]
            if path.replace('\\', '/').endswith(found) or found.endswith(path.replace('\\', '/')):
                return found
                
        return None
        
    return resolve

def linkPaths(html: str, resolve: Callable[[str], Optional[str]], onMiss: Optional[Callable[[str], None]] = None) -> str:
    pattern = re.compile(r'(?<![A-Za-z0-9_$/@~.-])((?:\.\./)*(?:\.?[A-Za-z0-9_@+~-]+/)+[A-Za-z0-9_@.+~-]+\.(?:h|hpp|hh|c|cc|cpp|cxx|mm|cs|py|mjs|js|ts|tsx|json|md|yaml|yml|toml|shader|glsl|dot|html|css|xml))(?![A-Za-z0-9])')
    
    def repl(m: Match[str]) -> str:
        path = m.group(1)
        if path.startswith("out/") or '<' in path or '>' in path:
            return m.group(0)
            
        resolved = resolve(path)
        if resolved:
            return f'<a class="path-link" href="file://{resolved}">{path}</a>'
        else:
            if onMiss:
                onMiss(path)
            return m.group(0)
            
    out: List[str] = []
    i = 0
    
    while i < len(html):
        if html[i] == '<':
            next_tag = html.find('>', i)
            if next_tag != -1:
                out.append(html[i:next_tag+1])
                i = next_tag + 1
            else:
                out.append(html[i:])
                break
        else:
            next_tag = html.find('<', i)
            chunk = html[i:next_tag] if next_tag != -1 else html[i:]
            out.append(pattern.sub(repl, chunk))
            if next_tag != -1:
                i = next_tag
            else:
                break
                
    return "".join(out)
