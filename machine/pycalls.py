#!/usr/bin/env python3
"""pycalls.py — 파이썬 소스에서 심볼과 호출 관계를 뽑는 수집기.

    python3 pycalls.py machine runner --repo . -o pycalls.json

griffe 는 시그니처 추출기라 `imports` · `bases` · `parameters` · `returns` 만 내고
호출 관계를 내지 않는다. griffe(클래스·상속·타입 주석)와 이 파일(함수·메서드·호출)을
합쳐야 코드 지도가 선다.

표준 라이브러리 `ast` 만 쓴다. 코드를 실행하지 않으므로 import 부작용이 없고,
문법이 맞는 파일이면 의존성 설치 없이도 읽힌다.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import json
import os
import sys
from typing import Literal, NotRequired, TypedDict

SymbolKind = Literal["function", "method", "class"]


class PySymbol(TypedDict):
    """정의 하나. `name` 은 모듈 경로를 앞에 붙인 완전 수식 점 이름이다."""

    name: str
    kind: SymbolKind
    module: str
    file: str
    line: int
    signature: NotRequired[str]


class PyCall(TypedDict):
    """호출 하나. 양끝은 `PySymbol.name` 과 같은 꼴이다."""

    caller: str
    callee: str
    file: str
    line: int


class PyCallsDump(TypedDict):
    tool: str
    symbols: list[PySymbol]
    calls: list[PyCall]


# ── 이 이름들은 호출 대상으로 세지 않는다. 빌트인은 관계가 아니라 문법에 가깝다.
_BUILTIN_CALLS = frozenset(dir(builtins))


# 저장소 상대 경로를 파이썬 점 경로로 바꾼다.
# 쓰는 것: 없음 · 쓰이는 곳: collect
def module_path(rel: str) -> str:
    """`machine/normalize.py` -> `machine.normalize`.

    griffe 가 내는 모듈 이름과 같은 축으로 맞춘다 — 두 수집기의 노드를 이름으로 합치려면
    신원이 같은 낱말이어야 한다.
    """
    stem = rel[:-3] if rel.endswith(".py") else rel
    return stem.replace(os.sep, "/").replace("/", ".")


# 함수 정의에서 사람이 읽는 시그니처를 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: collect
def signature_of(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """`(a, b=..., *args, **kw) -> T` 꼴. 주석은 원문 그대로 살린다."""
    a = fn.args

    def one(arg: ast.arg, default: ast.expr | None) -> str:
        s = arg.arg
        if arg.annotation is not None:
            s += ": " + ast.unparse(arg.annotation)
        if default is not None:
            # PEP 8 — 주석이 있으면 `=` 양옆에 공백을 둔다. 없으면 붙여 쓴다.
            s += " = " + ast.unparse(default) if arg.annotation is not None \
                else "=" + ast.unparse(default)
        return s

    parts: list[str] = []
    positional = list(a.posonlyargs) + list(a.args)
    pad = len(positional) - len(a.defaults)
    for i, arg in enumerate(positional):
        parts.append(one(arg, a.defaults[i - pad] if i >= pad else None))
    if a.vararg is not None:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")                         # 키워드 전용 구분자
    for kw, kwdefault in zip(a.kwonlyargs, a.kw_defaults):
        parts.append(one(kw, kwdefault))
    if a.kwarg is not None:
        parts.append("**" + a.kwarg.arg)
    ret = " -> " + ast.unparse(fn.returns) if fn.returns is not None else ""
    return "(" + ", ".join(parts) + ")" + ret


# 모듈 하나의 import 표를 만든다. 지역 이름 -> 완전 점 경로.
# 쓰는 것: 없음 · 쓰이는 곳: scan_module
def import_table(tree: ast.Module, stem_to_module: dict[str, str]) -> dict[str, str]:
    """`from warmup import status` -> {"status": "machine.warmup.status"}.

    이 저장소는 패키지 import 를 쓰지 않는다. `sys.path` 에 형제 디렉토리를 넣고
    `import warmup` 처럼 평평한 이름으로 부른다. 디렉토리 뿌리로 걸러서는 이 꼴을 못 풀어
    모듈을 넘는 호출이 거의 사라지므로, 여기서는 파일 이름(stem)을 열쇠로 잡는다.

    저장소 밖 라이브러리(`json` · `subprocess`)는 담지 않는다 — 호출 해석이 밖으로 새면
    그 노드는 `_assemble` 의 R1 이 어차피 지운다.
    """
    out: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            # `from warmup import status` 도 `from machine.warmup import status` 도 받는다.
            head = (n.module or "").split(".")[0]
            target = stem_to_module.get(head)
            if target is not None:
                for al in n.names:
                    out[al.asname or al.name] = f"{target}.{al.name}"
        elif isinstance(n, ast.Import):
            for al in n.names:
                target = stem_to_module.get(al.name.split(".")[0])
                if target is not None:
                    out[al.asname or al.name] = target
    return out


# 한 소스 나무에서 정의와 호출을 뽑는다.
# 쓰는 것: signature_of, import_table · 쓰이는 곳: collect
def scan_module(tree: ast.Module, mod: str, rel: str,
                stem_to_module: dict[str, str]) -> tuple[list[PySymbol], list[tuple[str, str, int]]]:
    """한 모듈의 (심볼, 미해석 호출) 을 낸다. 호출의 대상은 아직 쓰인 그대로다.

    해석(이름 -> 완전 점 경로)은 전체 정의 표가 모인 뒤에 `collect` 가 한다 —
    같은 모듈 안의 앞뒤 참조를 놓치지 않기 위해서다.
    """
    alias = import_table(tree, stem_to_module)
    syms: list[PySymbol] = []
    raw: list[tuple[str, str, int]] = []          # (부르는 쪽, 쓰인 그대로의 이름, 줄)
    local_names: set[str] = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            local_names.add(node.name)

    def calls_in(scope: ast.AST, owner: str) -> None:
        for c in ast.walk(scope):
            if not isinstance(c, ast.Call):
                continue
            f = c.func
            if isinstance(f, ast.Name):
                written = f.id
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                written = f"{f.value.id}.{f.attr}"
            else:
                continue                          # obj.attr.method() 꼴은 정적으로 못 푼다
            raw.append((owner, written, getattr(c, "lineno", 0)))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qname = f"{mod}.{node.name}"
            syms.append({"name": qname, "kind": "function", "module": mod,
                         "file": rel, "line": node.lineno, "signature": signature_of(node)})
            calls_in(node, qname)
        elif isinstance(node, ast.ClassDef):
            cname = f"{mod}.{node.name}"
            syms.append({"name": cname, "kind": "class", "module": mod,
                         "file": rel, "line": node.lineno})
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mname = f"{cname}.{m.name}"
                    syms.append({"name": mname, "kind": "method", "module": mod,
                                 "file": rel, "line": m.lineno,
                                 "signature": signature_of(m)})
                    calls_in(m, mname)

    # 모듈 최상위(함수 밖)의 호출은 소유자가 없다 — 모듈 자신을 소유자로 둔다.
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            calls_in(node, mod)

    # 이름 해소 — import 표가 먼저고, 없으면 같은 모듈 안에서 찾는다.
    #   `collect` 가 전체 정의 표로 한 번 더 거르므로 여기서 못 푼 것은 그때 버려진다.
    resolved: list[tuple[str, str, int]] = []
    for owner, written, line in raw:
        head, _, rest = written.partition(".")
        if head in alias:
            resolved.append((owner, alias[head] + ("." + rest if rest else ""), line))
        elif not rest and head not in _BUILTIN_CALLS:
            resolved.append((owner, f"{mod}.{head}", line))       # 같은 모듈의 정의
        else:
            resolved.append((owner, written, line))               # 못 품 — collect 가 버린다
    return syms, resolved


# 여러 뿌리 아래의 파이썬 파일을 전부 훑어 심볼과 호출을 낸다.
# 쓰는 것: module_path, scan_module · 쓰이는 곳: pycalls.main
def collect(repo: str, roots: list[str]) -> PyCallsDump:
    """`roots` 아래 `*.py` 를 전부 읽어 심볼과 해석된 호출을 낸다.

    호출은 양끝이 모두 이 저장소의 정의일 때만 남긴다. 바깥 라이브러리로 나가는 호출은
    버린다 — `_assemble` 의 R1 이 어차피 지운다.
    """
    files: list[tuple[str, str]] = []             # (저장소 상대경로, 절대경로)
    for root in roots:
        base = os.path.join(repo, root)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                if fn.endswith(".py"):
                    ap = os.path.join(dirpath, fn)
                    files.append((os.path.relpath(ap, repo), ap))
    files.sort()

    # ── 0패스: 파일 이름 -> 모듈 점 경로. 이 저장소의 평평한 import 관습을 푸는 표다.
    #    이름이 겹치면 어느 쪽인지 알 수 없다. 조용히 하나를 고르지 않고 둘 다 버린다 —
    #    잘못 이은 간선은 없는 간선보다 나쁘다.
    stem_to_module: dict[str, str] = {}
    collided: set[str] = set()
    for rel, _ in files:
        stem = os.path.basename(rel)[:-3]
        mod = module_path(rel)
        if stem in stem_to_module and stem_to_module[stem] != mod:
            collided.add(stem)
        stem_to_module[stem] = mod
    for stem in collided:
        del stem_to_module[stem]
        print(f"경고 — 파일 이름 '{stem}' 이 여러 디렉토리에 있어 호출 해석에서 뺐다.",
              file=sys.stderr)

    symbols: list[PySymbol] = []
    pending: list[tuple[str, str, int, str]] = []  # (부르는 쪽, 대상, 줄, 파일)
    for rel, ap in files:
        try:
            tree = ast.parse(open(ap, encoding="utf-8").read(), filename=ap)
        except SyntaxError:
            continue                               # 문법이 깨진 파일은 조용히 지나간다
        mod = module_path(rel)
        syms, raw = scan_module(tree, mod, rel, stem_to_module)
        symbols.extend(syms)
        pending.extend((owner, target, line, rel) for owner, target, line in raw)

    defined = {s["name"] for s in symbols}
    calls: list[PyCall] = []
    seen: set[tuple[str, str]] = set()
    for caller, callee, line, rel in pending:
        if caller not in defined or callee not in defined or caller == callee:
            continue
        if (caller, callee) in seen:
            continue
        seen.add((caller, callee))
        calls.append({"caller": caller, "callee": callee, "file": rel, "line": line})

    return {"tool": f"pycalls (ast, python {sys.version_info.major}.{sys.version_info.minor})",
            "symbols": symbols, "calls": sorted(calls, key=lambda c: (c["caller"], c["callee"]))}


# pycalls 도구의 명령줄 진입점. pycalls.json 을 쓴다.
# 쓰는 것: collect · 쓰이는 곳: 없음
def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("roots", nargs="+", help="훑을 디렉토리 (저장소 상대). 예: machine runner")
    ap.add_argument("--repo", default=".", help="대상 저장소")
    ap.add_argument("-o", "--out", default="pycalls.json")
    a = ap.parse_args()

    dump = collect(a.repo, list(a.roots))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(dump, fh, ensure_ascii=False, indent=2)

    kinds: dict[str, int] = {}
    for s in dump["symbols"]:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print(f"{a.out} — 심볼 {len(dump['symbols'])} / 호출 {len(dump['calls'])}")
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    cross = sum(1 for c in dump["calls"]
                if c["caller"].split(".")[0] != c["callee"].split(".")[0]
                or c["caller"].rsplit(".", 1)[0] != c["callee"].rsplit(".", 1)[0])
    print(f"  그중 모듈을 넘는 호출 {cross}")


if __name__ == "__main__":
    main()
