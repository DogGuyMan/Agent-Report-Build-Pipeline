#!/usr/bin/env python3
"""확신도 표기(🔵/🟡/💭 + 정수)를 쓴 글을 기계로 본다. 표준 라이브러리만 쓰고 어느 저장소에서나 돈다.

    python3 check_confidence.py <글 파일>… [--root <저장소 뿌리>]

넷을 본다.
  1. 정수가 0–100 안인가                                  — 밖이면 실패(종료 코드 1)
  2. 정수가 티어 구간 안인가(🔵 90–100 · 🟡 60–89 · 💭 0–59)  — 경고
  3. 숫자나 `실측` 이 붙은 🔵 와 같은 단위에 근거 인용이 있는가  — 경고
  4. 글이 인용한 `파일:줄` 이 실제로 있는가                    — 경고

통과는 "표기가 계약의 꼴이고 가리킨 줄이 있다" 까지다. 인용이 주장을 뒷받침하는지, 확신도가 옳은지는 보지 않는다.
🟡 의 옵션 표와 💭 의 보류는 글에서 기계로 가릴 수 없어 보지 않는다.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import Callable, NamedTuple, Optional

# 티어마다 정수가 움직일 수 있는 구간. SKILL.md §1.5 의 글과 같아야 한다(test_bands_are_the_ones_the_skill_text_states).
BANDS = {"🔵": (90, 100), "🟡": (60, 89), "💭": (0, 59)}
MEASURED = "실측"
SKIPPED = ""   # 해석기의 답 — 값이 없는 변수로 적혀 판정할 수 없는 경로

# 숫자 뒤에 낱말 글자(`11개`) · 날짜(`2026-11`) · 소수(`1.2`) · 범위(`90–100`)가 이어지면 확신도가 아니다.
ANCHOR = re.compile(r"(🔵|🟡|💭)[ \t]?(?:([0-9]+)(?![\w/%]|[.:\-–~][0-9])|(실측))?")
CODE_SPAN = re.compile(r"`[^`\n]*`")
FENCE = re.compile(r"^\s*(?:```|~~~)")
# 새 단위를 여는 줄 — 목록 머리 · 제목 · 표의 행.
UNIT_HEAD = re.compile(r"^\s*(?:[-*+]\s|[0-9]+[.)]\s|#|\|)")
# `경로.확장자:줄` 또는 `:줄-줄`. 그룹 1 경로, 2 첫 줄, 3 끝 줄. 줄 번호 뒤에 한글 조사가 붙어도 된다.
CITE = re.compile(
    r"(?<![\w/.:@$~{}-])((?:~/|\$\{?[A-Za-z_]\w*\}?/|/)?(?:[\w.@+-]+/)*[\w.@+-]+\.[A-Za-z][A-Za-z0-9]{0,7})"
    r":([0-9]+)(?:[-–]([0-9]+))?(?![A-Za-z0-9_/])")
# `[이름](경로#L12)` · `(경로#L12-L20)`. 그룹 1 경로, 2 첫 줄, 3 끝 줄.
LINE_LINK = re.compile(r"\[[^\]\n]*\]\(([^)#\s]+)#L([0-9]+)(?:-L?([0-9]+))?\)")
ANY_LINK = re.compile(r"\]\([^)\s]+\)|https?://\S+")

Resolver = Callable[[str], Optional[str]]


class Anchor(NamedTuple):
    """글에서 찾은 표기 하나. `value` 는 정수 앵커(없으면 None), `measured` 는 `실측` 표기다."""
    line: int
    tier: str
    value: Optional[int]
    measured: bool


class Notation(NamedTuple):
    out_of_range: list[str]
    off_band: list[str]


class Citations(NamedTuple):
    """`total` 은 판정한 서로 다른 인용 수, `found` 는 그중 파일과 줄이 다 있는 수, `skipped` 는 판정하지 못한 수다."""
    total: int
    found: int
    skipped: int
    missing: list[str]
    beyond: list[str]


def show(a: Anchor) -> str:
    return "%d줄 %s %s" % (a.line, a.tier, MEASURED if a.measured else a.value)


def fenced(lines: list[str]) -> list[bool]:
    """줄마다 코드 블록 안인지. 울타리 줄도 안으로 친다."""
    out: list[bool] = []
    inside = False
    for line in lines:
        edge = bool(FENCE.match(line))
        out.append(inside or edge)
        inside = inside != edge
    return out


def find_anchors(text: str) -> list[Anchor]:
    """글의 표기를 줄 번호와 함께 찾는다. 코드 글꼴과 코드 블록 안의 것은 예시라 뺀다."""
    lines = text.split("\n")
    skip = fenced(lines)
    out: list[Anchor] = []
    for i, line in enumerate(lines):
        if skip[i]:
            continue
        for m in ANCHOR.finditer(CODE_SPAN.sub(lambda s: " " * len(s.group(0)), line)):
            out.append(Anchor(i + 1, m.group(1), int(m.group(2)) if m.group(2) else None, bool(m.group(3))))
    return out


def check_notation(anchors: list[Anchor]) -> Notation:
    """정수가 0–100 안이고 티어 구간 안인지 본다."""
    out = Notation([], [])
    for a in anchors:
        if a.value is None:
            continue
        lo, hi = BANDS[a.tier]
        if a.value > 100:
            out.out_of_range.append(show(a))
        elif not lo <= a.value <= hi:
            out.off_band.append(show(a))
    return out


def unit_of(lines: list[str], i: int) -> str:
    """`i` 번째 줄이 속한 단위. 표의 행은 그 한 줄, 그 밖에는 빈 줄이나 새 단위의 머리에서 끊기는 이어진 줄들이다."""
    if lines[i].lstrip().startswith("|"):
        return lines[i]
    start = end = i
    while start > 0 and not UNIT_HEAD.match(lines[start]) and lines[start - 1].strip() \
            and not lines[start - 1].lstrip().startswith(("|", "#")):
        start -= 1
    while end + 1 < len(lines) and lines[end + 1].strip() and not UNIT_HEAD.match(lines[end + 1]):
        end += 1
    return "\n".join(lines[start:end + 1])


def check_binding(text: str, anchors: list[Anchor]) -> list[str]:
    """숫자나 `실측` 이 붙은 🔵 가운데, 같은 단위에 근거 인용(`파일:줄` · 링크 · URL)이 없는 것."""
    lines = text.split("\n")
    out: list[str] = []
    for a in anchors:
        if a.tier != "🔵" or (a.value is None and not a.measured):
            continue
        unit = unit_of(lines, a.line - 1)
        if not (CITE.search(unit) or ANY_LINK.search(unit)):
            out.append(show(a))
    return out


def git_root(folder: str) -> str:
    """`folder` 가 속한 git 저장소의 뿌리. git 밖이거나 git 이 없으면 `folder` 그대로다."""
    try:
        r = subprocess.run(["git", "-C", folder, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    except OSError:
        return folder
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else folder


def make_resolver(doc_dir: str, root: str) -> Resolver:
    """인용한 경로를 실제 파일로 푼다. 찾으면 그 경로, 없으면 None, 판정할 수 없으면 `SKIPPED` 다.

    순서: 글이 있는 폴더 → 저장소 뿌리 → 이름만 적혔으면 git 이 추적하는 파일 중 그 이름이 **하나일 때만**.
    `~/` 와 `$VAR/` 는 편다. 값이 없는 변수로 적힌 경로는 판정하지 않는다.
    """
    index: dict[str, list[str]] = {}
    loaded = False

    def tracked(name: str) -> list[str]:
        nonlocal loaded
        if not loaded:
            loaded = True
            try:
                r = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True)
            except OSError:
                return []
            for rel in r.stdout.split("\n") if r.returncode == 0 else []:
                index.setdefault(os.path.basename(rel), []).append(rel)
        return index.get(name, [])

    def resolve(token: str) -> Optional[str]:
        path = os.path.expandvars(os.path.expanduser(token))
        if "$" in path:
            return SKIPPED
        if os.path.isabs(path):
            return path if os.path.isfile(path) else None
        for base in (doc_dir, root):
            candidate = os.path.normpath(os.path.join(base, path))
            if os.path.isfile(candidate):
                return candidate
        if "/" not in path:
            hits = tracked(path)
            if len(hits) == 1 and os.path.isfile(os.path.join(root, hits[0])):
                return os.path.join(root, hits[0])
        return None

    return resolve


def line_count(path: str) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def find_citations(text: str) -> dict[str, tuple[str, int, int]]:
    """글이 인용한 `파일:줄`. {적힌 꼴: (경로, 첫 줄, 끝 줄)}.

    줄 번호 없는 경로는 인용으로 세지 않는다. 같은 인용은 하나다. 코드 블록 안은 보지 않는다.
    """
    lines = text.split("\n")
    skip = fenced(lines)
    body = "\n".join("" if skip[i] else line for i, line in enumerate(lines))
    cites: dict[str, tuple[str, int, int]] = {}
    for m in LINE_LINK.finditer(body):
        cites.setdefault(m.group(0).rsplit("](", 1)[1][:-1], (m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))))
    for m in CITE.finditer(LINE_LINK.sub(lambda s: " " * len(s.group(0)), body)):
        cites.setdefault(m.group(0), (m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))))
    return cites


def check_citations(text: str, resolve: Resolver) -> Citations:
    """글이 인용한 `파일:줄` 마다 파일이 있고 그 줄이 파일 안인지 본다."""
    found = skipped = 0
    missing: list[str] = []
    beyond: list[str] = []
    for shown, (token, first, last) in find_citations(text).items():
        path = resolve(token)
        if path == SKIPPED:
            skipped += 1
        elif path is None:
            missing.append(shown)
        elif 1 <= first <= last <= line_count(path):
            found += 1
        else:
            beyond.append(shown)
    return Citations(found + len(missing) + len(beyond), found, skipped, missing, beyond)


class Examined(NamedTuple):
    """글 하나를 본 결과 넷."""
    anchors: list[Anchor]
    notation: Notation
    unbound: list[str]
    cites: Citations


CLOSING = "표기의 꼴과 인용의 실재만 본 것이다 — 확신도가 옳다는 뜻은 아니다"


def examine(text: str, doc_dir: str, root: str) -> Examined:
    """글의 표기 정합 · 🔵 의 근거 인용 · 인용의 실재를 본다."""
    anchors = find_anchors(text)
    return Examined(anchors, check_notation(anchors), check_binding(text, anchors),
                    check_citations(text, make_resolver(doc_dir, root)))


def render(found: Examined, root: str) -> list[str]:
    """본 결과를 사람이 읽는 줄들로 만든다."""
    notation, cites = found.notation, found.cites
    out = ["  표기 %d개 (%s)" % (len(found.anchors), " · ".join(
        "%s %d" % (tier, sum(1 for a in found.anchors if a.tier == tier)) for tier in BANDS))]
    if notation.out_of_range:
        out.append("  실패 — 0–100 밖의 정수: %s" % ", ".join(notation.out_of_range))
    if notation.off_band:
        out.append("  경고 — 티어 구간 밖의 정수: %s" % ", ".join(notation.off_band))
    if found.unbound:
        out.append("  경고 — 🔵 인데 같은 단위에 근거 인용(`파일:줄` · 링크 · URL)이 없다: %s" % ", ".join(found.unbound))
    counted = "`파일:줄` %d건 중 %d건 실재" % (cites.total, cites.found)
    if cites.skipped:
        counted += ", 판정 못 함 %d건(값이 없는 변수로 적은 경로)" % cites.skipped
    if not (cites.missing or cites.beyond):
        return out + ["  인용: %s" % counted]
    out.append("  경고 — 인용: %s" % counted)
    if cites.missing:
        out.append("    파일이 없다: %s" % ", ".join(cites.missing))
        out.append("    찾은 자리: 글의 폴더와 %s — 다른 저장소의 파일이면 --root 로 그 뿌리를 준다" % root)
    if cites.beyond:
        out.append("    줄이 파일 밖이다: %s" % ", ".join(cites.beyond))
    return out


def clean(found: Examined) -> bool:
    """실패도 경고도 없는가."""
    return not (found.notation.out_of_range or found.notation.off_band or found.unbound
                or found.cites.missing or found.cites.beyond)


def report(path: str, root: Optional[str]) -> bool:
    """글 하나를 검사해 찍는다. 실패(0–100 밖의 정수)가 있으면 참이다."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    doc_dir = os.path.dirname(os.path.abspath(path))
    root = os.path.abspath(root) if root else git_root(doc_dir)
    found = examine(text, doc_dir, root)

    print(path)
    print("\n".join(render(found, root)))
    print("  %s%s" % ("통과 — " if clean(found) else "", CLOSING))

    return bool(found.notation.out_of_range)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="확신도 표기를 쓴 글의 표기 정합 · 🔵 의 근거 인용 · 인용의 실재를 본다.")
    parser.add_argument("files", nargs="+", help="표기를 쓴 글 파일")
    parser.add_argument("--root", help="인용한 경로를 찾을 저장소 뿌리. 없으면 글이 속한 git 저장소의 뿌리")
    args = parser.parse_args(argv)
    failed = [report(path, args.root) for path in args.files]
    return 1 if any(failed) else 0


if __name__ == "__main__":
    sys.exit(main())
