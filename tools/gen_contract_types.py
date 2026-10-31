#!/usr/bin/env python3
"""계약 리소스(JSON Schema)에서 소비자 형을 낸다 — 생성물 `machine/contract_types.py`. `--check` 면 낡았을 때 exit 1.

계약 `contracts/mode1-artifacts.v1.json` 은 codebase-wiki 가 형에서 생성해 보낸 사본이다. 여기서 그 스키마를
TypedDict 로 되돌린다 — 소비자 형을 손으로 쓰지 않는다. 다루는 꼴은 계약이 실제로 쓰는 것뿐이다:
object(properties · required) · dict[str, T](additionalProperties) · array · string · integer · boolean · null · anyOf · $ref.
"""
import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from typing import cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")
OUT = os.path.join(ROOT, "machine", "contract_types.py")
SCALARS = {"string": "str", "integer": "int", "boolean": "bool", "null": "None"}

Schema = Mapping[str, object]


def py_type(s: Schema) -> str:
    """스키마 하나를 파이썬 형 표기로. 모르는 꼴이면 ValueError."""
    if "$ref" in s:
        return str(s["$ref"]).rsplit("/", 1)[-1]
    if "anyOf" in s:
        return " | ".join(py_type(cast(Schema, x)) for x in cast(list[object], s["anyOf"]))
    t = s.get("type")
    if isinstance(t, str) and t in SCALARS:
        return SCALARS[t]
    if t == "array":
        return "list[%s]" % py_type(cast(Schema, s["items"]))
    if t == "object" and "additionalProperties" in s and "properties" not in s:
        return "dict[str, %s]" % py_type(cast(Schema, s["additionalProperties"]))
    raise ValueError("이 생성기가 모르는 꼴: %s" % json.dumps(s, ensure_ascii=False))


def refs(node: object) -> set[str]:
    """스키마 안의 `$ref` 가 가리키는 이름 전부."""
    if isinstance(node, dict):
        d = cast(dict[str, object], node)
        here: set[str] = {str(d["$ref"]).rsplit("/", 1)[-1]} if "$ref" in d else set()
        return here.union(*(refs(v) for v in d.values()))
    if isinstance(node, list):
        return set[str]().union(*(refs(v) for v in cast(list[object], node)))
    return set()


def class_text(name: str, s: Schema) -> str:
    """객체 스키마 하나를 TypedDict 클래스 글로. 칸은 이름순이고 `required` 에 없는 칸은 `NotRequired` 다."""
    props = cast(Mapping[str, Schema], s.get("properties", {}))
    required = set(cast(list[str], s.get("required", [])))
    lines = ["class %s(TypedDict):" % name]
    for p in sorted(props):
        t = py_type(props[p])
        lines.append("    %s: %s" % (p, t if p in required else "NotRequired[%s]" % t))
    return "\n".join(lines)


def module_text(doc: Mapping[str, object]) -> str:
    """계약 문서 전체를 `contract_types.py` 의 글로. 클래스는 참조되는 것이 먼저 오게 늘어놓는다."""
    defs: dict[str, Schema] = {}
    schemas = cast(Mapping[str, Schema], doc["schemas"])
    for sch in schemas.values():
        defs.update(cast(Mapping[str, Schema], sch.get("$defs", {})))
    order: list[str] = []

    def visit(n: str) -> None:
        if n in order:
            return
        for r in sorted(refs(defs[n]) - {n}):
            visit(r)
        order.append(n)

    for n in sorted(defs):
        visit(n)
    aliases = ["%s = %s" % (tname, py_type(schemas[fname]))
               for fname, tname in sorted(cast(Mapping[str, str], doc["types"]).items())
               if py_type(schemas[fname]) != tname]
    head = ('"""생성물 — tools/gen_contract_types.py 가 contracts/mode1-artifacts.v1.json 에서 낸다. 손대지 마라."""\n'
            "from typing import NotRequired, TypedDict\n\n"
            "CONTRACT = %s\nVERSION = %d\n" % (json.dumps(doc["contract"]), cast(int, doc["version"])))
    return head + "\n\n" + "\n\n\n".join(class_text(n, defs[n]) for n in order) + "\n\n\n" + "\n".join(aliases) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """계약에서 `machine/contract_types.py` 를 쓴다. `--check` 면 쓰지 않고 파일이 계약과 같은지만 본다."""
    ap = argparse.ArgumentParser(description="계약에서 소비자 형을 낸다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    with open(CONTRACT, encoding="utf-8") as f:
        text = module_text(cast(Mapping[str, object], json.load(f)))
    if a.check:
        try:
            with open(OUT, encoding="utf-8") as f:
                same = f.read() == text
        except OSError:
            same = False
        if not same:
            print("machine/contract_types.py 가 계약과 다르다 — python tools/gen_contract_types.py", file=sys.stderr)
            return 1
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
