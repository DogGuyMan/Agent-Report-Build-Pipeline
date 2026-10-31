"""디렉토리 정리(결정 0014) 스크립트들이 함께 쓰는 것 — 지도 읽기 · 디렉토리 접두사 표 · 점 표기 표 · 경로 토큰 정규식."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "split-work", "reorg", "out")
TSV = os.path.join(OUT, "pathmap.tsv")
REMOVED = os.path.join(OUT, "removed-lines.json")

# 디렉토리째 옮긴 것만 — 여러 자리로 갈라진 디렉토리(runner/ · viz/ · tools/ · test/ · config/ · runner/prompts/ · viz/templates/)는 없다.
# 긴 것이 먼저 맞아야 하므로 순서가 뜻을 갖는다.
DIRS = [
    ("runner/mode1/prompts/", "resource/codewiki/prompts/"),
    ("runner/mode1/", "codewiki/python/runner/mode1/"),
    ("runner/wiki/templates/", "resource/codewiki/templates/"),
    ("runner/wiki/", "codewiki/python/runner/wiki/"),
    ("runner/term/", "term/python/runner/term/"),
    ("machine/roslyn-dump/", "codewiki/csharp/roslyn-dump/"),
    ("machine/", "codewiki/python/machine/"),
    ("viz/src/", "spec/typescript/src/"),
    ("viz/templates/dot/", "resource/codewiki/templates/dot/"),
    ("viz/templates/report/", "resource/spec/templates/report/"),
    ("resources/samples/", "resource/codewiki/samples/"),
    ("resources/", "resource/codewiki/"),
    ("evals/runs/", "qa/evals/runs/"),
    ("evals/", "qa/evals/"),
    ("research_notes/", "docs/research/"),
    ("reports/", "docs/research/"),
]
# Task 3 이 손으로 먼저 옮기는 문서 다섯 — 지도(TSV)에는 "그대로" 로 적히므로 여기서 따로 안다.
EXTRA = {
    "docs/analysis-2026-08-31-cpp-collectors.md": "docs/notes/analysis-2026-08-31-cpp-collectors.md",
    "docs/2026-09-19-mode1-역대-실측과-패치-이력.md": "docs/notes/2026-09-19-mode1-역대-실측과-패치-이력.md",
    "docs/2패스개선.md": "docs/notes/2패스개선.md",
    "runner/runner_presudo.md": "docs/notes/runner_presudo.md",
    "remain-process-merged.md": "docs/handoffs/remain-process-merged.md",
}
# 점 표기 모듈 id 로도 쓰이는 디렉토리 — 파이썬 패키지인 것만.
DOTTED_DIRS = {a.rstrip("/").replace("/", "."): b.rstrip("/").replace("/", ".")
               for a, b in DIRS if a in ("runner/mode1/", "runner/wiki/", "runner/term/", "machine/")}

# 경로 토큰 — 빗금이 하나 이상 있는 낱말. 앞에 식별자 글자가 없어야 한다. 뒤에 `:줄` 또는 `:줄-줄` 이 붙을 수 있다.
TOKEN = re.compile(r"(?<![A-Za-z0-9_\-])(?P<path>(?:[A-Za-z0-9_.$\-]+/)+[A-Za-z0-9_.\-]*)"
                   r"(?P<ln>:(?P<a>\d+)(?:(?P<sep>[-~])(?P<b>\d+))?)?")


def load_map() -> tuple[dict[str, str], set[str]]:
    """TSV → ({옛 경로: 새 경로}(옮긴 것만), {지운 경로})."""
    moved: dict[str, str] = {}
    deleted: set[str] = set()
    with open(TSV, encoding="utf-8") as f:
        for line in f:
            old, new = line.rstrip("\n").split("\t")
            if new == "DELETE":
                deleted.add(old)
            elif new != old:
                moved[old] = new
    return moved, deleted


def map_rel(rel: str, moved: dict[str, str]) -> str:
    """저장소 상대 경로 하나 — 파일 지도가 먼저, 없으면 디렉토리 접두사(DIRS 순서). 못 옮기면 그대로."""
    if rel in moved:
        return moved[rel]
    if rel in EXTRA:
        return EXTRA[rel]
    for a, b in DIRS:
        if rel.startswith(a):
            return b + rel[len(a):]
        if rel == a.rstrip("/"):          # 빗금 없는 디렉토리 이름 — 레코드의 module 값 꼴
            return b.rstrip("/")
    return rel


def repo_key(tok: str) -> tuple[list[str], str]:
    """토큰을 (앞머리 조각들, 저장소 상대 경로) 로 가른다. 첫 조각이 `.` 이나 `$변수` 면 그 다음부터가 저장소 상대 경로다."""
    segs = tok.split("/")
    start = 1 if segs[0] == "." or segs[0].startswith("$") else 0
    return segs[:start], "/".join(segs[start:])


def map_token(tok: str, moved: dict[str, str], report: list[str], where: str) -> str:
    """경로 토큰 하나를 옮긴다. `..` 로 시작하는 상대 경로는 파일 자리에 따라 뜻이 달라지므로 옮기지 않고 보고한다."""
    segs = tok.split("/")
    if segs[0] == "..":
        core = "/".join(s for s in segs if s not in ("..", "."))
        if map_rel(core, moved) != core:
            report.append(f"{where}: 상대 경로 {tok} 는 손으로 고친다")
        return tok
    head, rest = repo_key(tok)
    tail = ""
    while rest.endswith("."):
        rest, tail = rest[:-1], tail + "."
    new = map_rel(rest, moved)
    if new == rest:
        return tok
    return "/".join(head + [new + tail])


def dotted(path: str) -> str | None:
    return path[:-3].replace("/", ".") if path.endswith(".py") else None


def dotted_map(moved: dict[str, str]) -> dict[str, str]:
    """{옛 점 표기 모듈: 새 점 표기 모듈} — 파일 단위 + 패키지 디렉토리."""
    out: dict[str, str] = {}
    for o, n in moved.items():
        do, dn = dotted(o), dotted(n)
        if do and dn:
            out[do] = dn
    out.update(DOTTED_DIRS)
    return out


def map_dotted(name: str, table: dict[str, str]) -> str:
    """점 표기 이름 하나를 옮긴다 — 정확히 같거나, `옛.` 으로 시작하면 그 머리만 바꾼다. 긴 열쇠가 먼저."""
    if name in table:
        return table[name]
    for k in sorted(table, key=len, reverse=True):
        if name.startswith(k + "."):
            return table[k] + name[len(k):]
    return name
