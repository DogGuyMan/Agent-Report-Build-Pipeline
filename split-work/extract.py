#!/usr/bin/env python3
"""파이썬 안의 문자열 하나를 `{{이름}}` 리소스 글로 옮긴다 — `extract.py <파일.py> <줄> <출력>`.

`<줄>` 이 걸치는 가장 바깥 문자열(`.format()` 용 상수 또는 f-문자열)을 고른다.
- `.format()` 자리 `{x}` → `{{x}}`. 이스케이프 `{{ }}` 는 한 겹 `{ }` 로 풀린다.
- f-문자열 식 `{식}` → `{{slotN}}`. 대응을 찍는다 — 리소스에서 slotN 을 뜻 있는 이름으로 바꾸고,
  부르는 쪽에서 `이름=str(식)` 으로 넘긴다.
- 앞뒤 줄바꿈은 뗀다. 앞에서 뗀 수를 찍는다 — 부르는 쪽이 그만큼 `"\n"` 을 앞에 붙인다.
"""
import ast
import string
import sys

path, line, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(path, encoding="utf-8") as f:
    tree = ast.parse(f.read())
spans = [n for n in ast.walk(tree)
         if (isinstance(n, ast.JoinedStr) or (isinstance(n, ast.Constant) and isinstance(n.value, str)))
         and n.end_lineno is not None and n.lineno <= line <= n.end_lineno]
node = min(spans, key=lambda n: n.lineno)     # 같은 줄에서 시작하면 ast.walk 가 바깥을 먼저 낸다
parts: list[str] = []
slots: list[str] = []
if isinstance(node, ast.Constant):
    for literal, field, spec, conv in string.Formatter().parse(node.value):
        parts.append(literal)
        if field is not None:
            assert not spec and not conv, "서식 지정자가 있다: %s" % field
            parts.append("{{%s}}" % field)
            slots.append(field)
else:
    for v in node.values:
        if isinstance(v, ast.Constant):
            parts.append(str(v.value))
        else:
            assert isinstance(v, ast.FormattedValue) and v.format_spec is None and v.conversion == -1, ast.unparse(v)
            name = "slot%d" % (len(slots) + 1)
            parts.append("{{%s}}" % name)
            slots.append("%s = %s" % (name, ast.unparse(v.value)))
text = "".join(parts)
lead = len(text) - len(text.lstrip("\n"))
with open(out, "w", encoding="utf-8") as f:
    f.write(text.strip("\n") + "\n")
print(out)
print("  앞 줄바꿈 %d개를 뗐다" % lead)
for s in sorted(set(slots)):
    print("  자리", s)
