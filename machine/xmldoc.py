#!/usr/bin/env python3
"""xmldoc.py — 주석 본문을 .xml 한 곳에 모으고 코드에는 레퍼런스만 남긴다.

**정본은 machine/terms-reading.json 이다.** comments.xml 은 파생물이라
손으로 고치지 않는다. 뜻을 바꾸려면 json 을 고치고 `emit` 을 다시 돌린다.

  xmldoc.py emit                 -> machine/comments.xml 생성
  xmldoc.py inject [--dry-run]   -> 코드에 레퍼런스 블록 주입/갱신 + json 의 where 재계산 + emit
  xmldoc.py check                -> 코드의 레퍼런스가 json 과 맞는지만 본다. 어긋나면 종료 코드 1

주입 블록은 늘 세 줄(마커 · 뜻 · 의존)이고 include 줄로 식별한다. 다시 돌리면 덧붙지 않고 갈린다.
줄 번호는 셈으로 내지 않는다 — 파일에 박힌 마커를 다시 읽어 그 아래 선언 줄을 찾는다.

⚠ `check` 는 json 의 where 와 파일에 박힌 마커 기준 선언 줄이 **같은지** 본다. 대상 파일에서
줄이 하나라도 늘거나 줄면 그 아래 용어가 전부 어긋나 실패한다. 그때 고치는 것은 `inject` 다.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Literal, NotRequired, TypedDict, cast
from xml.sax.saxutils import escape, quoteattr


# ── terms-reading.json 의 모양. `does` 와 `confidence` 만 선택이고 나머지는 모든 레코드에 있다.

class Use(TypedDict):
    """`uses[]` 한 칸 — 이 용어가 무엇을 쓰는가."""
    to: str
    kind: str
    label: str
    where: str
    source: NotRequired[str]


class Term(TypedDict):
    """용어 하나. 열쇠 이름은 json 의 것 그대로다."""
    kind: str
    means: str
    module: str
    source: str
    where: str
    uses: list[Use]
    does: NotRequired[str]
    confidence: NotRequired[str]


# {용어 id: 레코드}. json 최상위가 이 모양이다.
Terms = dict[str, Term]
# {용어: 그것을 쓰는 용어들} — used_by_index 가 내는 역색인.
UsedBy = dict[str, list[str]]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READING = os.path.join(ROOT, "machine/terms-reading.json")
XML_REL = "machine/comments.xml"
XML_ABS = os.path.join(ROOT, XML_REL)

# 확장자별 한 줄 주석 접두사. 확장자가 없으면 bin/ 의 node 스크립트라 // 다.
LINE_COMMENT = {".py": "#", ".ts": "//", ".tsx": "//", ".mjs": "//", ".js": "//", "": "//"}

INCLUDE_RE = re.compile(r"^\s*(#|//)\s*<include file=\"" + re.escape(XML_REL) + r"\"")
ID_RE = re.compile(r"@id='([^']*)'")
# 블록 셋째 줄(의존 줄)을 알아보는 자. 걷어낼 때 옛 두 줄 블록과 가르는 데 쓴다.
USES_LINE_RE = re.compile(r"^\s*(?:#|//)\s*(?:\S+ — )?쓰는 것: ")

# 용어 하나에 붙는 줄 수 — 마커 · 뜻 · 의존.
BLOCK_ROWS = 3
# 의존 줄에 이름을 몇 개까지 적을지. 넘치면 (+n) 으로 센다.
USES_SHOWN = 5

# 코드에 레퍼런스를 박을 수 있는 kind. 선언 줄이 실제로 있는 것만이다.
# external · key · artifact · concept 의 where 는 쓰이는 자리를 가리킨다 — 문자열 안이거나
# 식 한복판일 수 있어 그 위에 블록을 얹을 수 없다. 이것들은 XML 에만 산다.
DECL_KINDS = frozenset({"function", "class", "struct", "enum", "interface",
                        "delegate", "record", "file"})


def prefix_for(path: str) -> str:
    ext = os.path.splitext(path)[1]
    if ext not in LINE_COMMENT:
        raise SystemExit(f"주석 접두사를 모르는 확장자: {path}")
    return LINE_COMMENT[ext]


def split_where(where: str | None) -> tuple[str | None, int | None]:
    """`file:line` -> (file, line). 위치가 없으면 (None, None)."""
    if not where:
        return None, None
    path, sep, ln = where.rpartition(":")
    if sep and ln.isdigit():
        return path, int(ln)
    return None, None


def anchor_name(term_id: str) -> str:
    """앵커 줄에서 찾을 이름. 점 표기는 마지막 마디, 배열 키는 [] 를 뗀다."""
    return term_id.split(".")[-1].removesuffix("[]")


# ---------------------------------------------------------------- XML 내보내기

def emit_xml(terms: Terms) -> str:
    # TypedDict 첨자는 열쇠가 문자열 리터럴이어야 풀린다. 열쇠 목록에 Literal 형을 박아 맞춘다.
    # 이 순서가 곧 XML 속성·본문의 출력 순서다.
    attr_keys: tuple[Literal["kind", "module", "where", "source"], ...] = (
        "kind", "module", "where", "source")
    body_keys: tuple[Literal["means", "does"], ...] = ("means", "does")
    use_keys: tuple[Literal["to", "kind", "label", "where", "source"], ...] = (
        "to", "kind", "label", "where", "source")
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           "<!-- 이 파일은 파생물이다. machine/terms-reading.json 을 고치고",
           "     machine/xmldoc.py emit 을 다시 돌려서 만든다. 손으로 고치지 않는다. -->",
           "<terms>"]
    for tid in sorted(terms):
        rec = terms[tid]
        attrs = f"id={quoteattr(tid)}"
        for k in attr_keys:
            if rec.get(k):
                attrs += f" {k}={quoteattr(rec[k])}"
        uses = rec.get("uses") or []
        # 앞의 `if rec.get(k)` 가 존재를 보장하지만 .get() 을 통해서는 좁혀지지 않는다.
        body = [f'    <{k}>{escape(rec[k])}</{k}>' for k in body_keys if rec.get(k)]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        for u in uses:
            # 위와 같은 이유 — 앞의 `if u.get(k)` 가 존재를 보장한다.
            ua = " ".join(f"{k}={quoteattr(str(u[k]))}" for k in use_keys if u.get(k))  # pyright: ignore[reportTypedDictNotRequiredAccess]
            body.append(f"    <uses {ua}/>")
        if body:
            out.append(f"  <term {attrs}>")
            out.extend(body)
            out.append("  </term>")
        else:
            out.append(f"  <term {attrs}/>")
    out.append("</terms>")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------- 레퍼런스 주입
#
# 블록의 모양 — 용어 하나마다 세 줄이다. include 줄 n 개가 먼저, 그 다음 뜻 n 개,
# 마지막이 의존 n 개. 길이는 항상 3n 이라 다시 돌릴 때 자를 범위를 세지 않고 알 수 있다.
#
#   # <include file="machine/comments.xml" path="//term[@id='Fact']"/>
#   # 사실 한 건을 담는 자료 구조.
#   # 쓰는 것: 없음 · 쓰이는 곳: collect, emit
#   class Fact:
#
# 놓는 자리는 **선언 위에 이미 있는 주석 덩어리보다 더 위**다. JSDoc 이나 파이썬 주석과
# 선언 사이를 갈라놓으면 편집기의 hover 문서가 끊긴다.

COMMENTISH = ("#", "//", "/*", "*", "*/")


def is_commentish(line: str) -> bool:
    s = line.strip()
    return s.startswith(COMMENTISH) if s else False


def used_by_index(terms: Terms) -> UsedBy:
    """{용어: 그것을 쓰는 용어들}. uses 를 거꾸로 뒤집은 것뿐이다."""
    back: dict[str, set[str]] = {}
    for tid, rec in terms.items():
        for u in rec.get("uses") or []:
            to = u.get("to")
            if to:
                back.setdefault(to, set()).add(tid)
    return {k: sorted(v) for k, v in back.items()}


def name_list(names: list[str]) -> str:
    """이름들을 한 줄로. 다섯 개까지 적고 남는 건 (+n) 으로 센다."""
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    if not seen:
        return "없음"
    line = ", ".join(seen[:USES_SHOWN])
    rest = len(seen) - USES_SHOWN
    return f"{line} (+{rest})" if rest > 0 else line


def uses_line(tid: str, terms: Terms, used_by: UsedBy) -> str:
    mine = [u.get("to") for u in (terms[tid].get("uses") or []) if u.get("to")]
    return f"쓰는 것: {name_list(mine)} · 쓰이는 곳: {name_list(used_by.get(tid, []))}"


def block_lines(tids: list[str], terms: Terms, prefix: str, indent: str,
                used_by: UsedBy | None = None) -> list[str]:
    """한 앵커에 붙일 레퍼런스 블록. 같은 줄에 여러 용어가 걸리면 함께 낸다."""
    if used_by is None:
        used_by = used_by_index(terms)
    lines = [f"{indent}{prefix} <include file=\"{XML_REL}\" path=\"//term[@id='{t}']\"/>" for t in tids]
    for tid in tids:
        means = (terms[tid].get("means") or "").replace("\n", " ").strip()
        label = f"{tid} — " if len(tids) > 1 else ""
        lines.append(f"{indent}{prefix} {label}{means}".rstrip())
    for tid in tids:
        label = f"{tid} — " if len(tids) > 1 else ""
        lines.append(f"{indent}{prefix} {label}{uses_line(tid, terms, used_by)}")
    return lines


def file_anchor(lines: list[str]) -> int:
    """kind=file 의 삽입 지점(0-based). 셔뱅이 있으면 그 아래."""
    return 1 if lines and lines[0].startswith("#!") else 0


def in_py_string(path: str, lines: list[str], idx: int) -> bool:
    """파이썬 파일에서 idx 줄이 삼중 따옴표 문자열 안인가. 홀짝만 센다 — 안전판이다."""
    if not path.endswith(".py"):
        return False
    head = "\n".join(lines[:idx])
    return (head.count(chr(34) * 3) % 2 == 1) or (head.count(chr(39) * 3) % 2 == 1)


def scan_top(lines: list[str], anchor_idx: int) -> int:
    """선언 위에 붙어 있는 주석 덩어리의 첫 줄. 빈 줄을 만나면 멈춘다."""
    i = anchor_idx
    while i > 0 and is_commentish(lines[i - 1]):
        i -= 1
    return i


def block_extent(lines: list[str], i: int) -> tuple[int, int]:
    """lines[i] 가 include 줄일 때 (용어 수, 블록이 차지한 줄 수).

    3n 이라고 못 박지 않고 의존 줄이 실제로 있는지 세어 더한다. 못 박으면 의존 줄이 없는
    블록을 걷어낼 때 코드 줄을 한 줄 삼킨다."""
    c = 0
    while i + c < len(lines) and INCLUDE_RE.match(lines[i + c]):
        c += 1
    n = 2 * c                       # include c 줄 + 뜻 c 줄은 의존 줄 없이도 늘 있다
    u = 0
    while u < c and i + n + u < len(lines) and USES_LINE_RE.match(lines[i + n + u]):
        u += 1
    return c, n + u


def relocate(lines: list[str]) -> dict[str, int]:
    """파일 본문에 박힌 마커를 읽어 {용어: 선언 줄(1-based)} 을 만든다.

    끼워 넣은 줄 수를 더해 셈하지 않고 파일에 실제로 박힌 자리를 본다 — 셈하면 한 번의
    누락이 그 아래 전부를 어긋내고, 그 값이 다시 저장돼 다음 판에서 더 어긋난다.

    선언은 블록 바로 아래다. 다만 블록 위쪽 놓기(scan_top) 때문에 원래 있던 주석
    덩어리가 사이에 낀다 — 그 덩어리를 지나쳐 첫 코드 줄을 찾는다."""
    out: dict[str, int] = {}
    i = 0
    while i < len(lines):
        if INCLUDE_RE.match(lines[i]):
            c, n = block_extent(lines, i)
            tids: list[str] = []
            for k in range(c):
                m = ID_RE.search(lines[i + k])
                # @id 없이 넘기면 그 아래 용어들의 줄 번호가 통째로 어긋난 채 저장된다.
                if m is None:
                    raise SystemExit(f"include 줄에 @id 가 없다: {lines[i + k].strip()}")
                tids.append(m.group(1))
            j = i + n
            while j < len(lines) and is_commentish(lines[j]) and not INCLUDE_RE.match(lines[j]):
                j += 1
            for t in tids:
                out[t] = j + 1
            i += n
            continue
        i += 1
    return out


def strip_blocks(lines: list[str]) -> tuple[list[str], list[int]]:
    """이미 박힌 레퍼런스 블록을 전부 걷어낸다. (깨끗한 줄들, 각 줄 앞에서 지워진 줄 수).

    남겨 두고 고치면 파일 용어의 블록과 첫 함수의 블록이 같은 자리를 두고 싸운다."""
    out: list[str] = []
    removed_before: list[int] = []
    i = 0
    while i < len(lines):
        if INCLUDE_RE.match(lines[i]):
            i += block_extent(lines, i)[1]
            continue
        removed_before.append(i - len(out))
        out.append(lines[i])
        i += 1
    return out, removed_before


def plan_file(path: str, tids: list[str], terms: Terms,
              src: str) -> tuple[str, dict[str, int], dict[int, int]]:
    """한 파일에 블록을 넣는다. 반환 (새 본문, {용어: 새 줄번호}, {옛 줄번호: 새 줄번호}).

    앵커는 **이미 박힌 마커**가 알려 준다. json 의 where 는 마커가 없는 새 용어에만
    쓴다 — 그 값은 낡았을 수 있고, 낡은 값을 다시 앵커로 삼으면 어긋남이 굳는다.

    셋째 반환값(옛 줄 -> 새 줄)이 필요한 이유 — 블록을 끼워 넣으면 그 아래 모든 줄이 밀린다.
    마커를 못 박는 용어(artifact·key·concept·external)와 `uses[].where` 는 밀린 만큼을
    스스로 알 수 없어, 이 대응표로 같이 옮기지 않으면 주입할 때마다 조금씩 어긋난다."""
    raw = src.split("\n")
    known = relocate(raw)
    lines, removed_before = strip_blocks(raw)
    stripped = list(lines)            # 삽입 자리를 되돌려 셀 때 쓴다
    # 걷어낸 뒤의 줄 번호로 옮긴다. removed_before[new_idx] = 그 줄 앞에서 지워진 줄 수.
    old_to_new: dict[int, int] = {}
    for new_idx, gap in enumerate(removed_before):
        old_to_new[new_idx + gap] = new_idx

    prefix = prefix_for(path)
    used_by = used_by_index(terms)

    file_tids = sorted(t for t in tids if terms[t].get("kind") == "file")
    anchors: dict[int, list[str]] = {}
    for t in sorted(tids):
        if terms[t].get("kind") == "file":
            continue
        # collect_targets 가 위치 없는 용어를 이미 걸렀으므로 줄 번호는 반드시 있다.
        ln = cast(int, known.get(t) or split_where(terms[t].get("where"))[1])
        old = ln - 1
        if old not in old_to_new:
            raise SystemExit(f"앵커가 옛 블록 안이다: {t} @ {path}:{ln}")
        anchors.setdefault(old_to_new[old], []).append(t)

    inserts: list[tuple[int, int]] = []   # (걷어낸 좌표에서의 삽입 자리, 넣은 줄 수)
    floor = file_anchor(lines)
    if file_tids:
        blk = block_lines(file_tids, terms, prefix, "", used_by)
        inserts.append((floor, len(blk)))
        lines[floor:floor] = blk
        shift = len(blk)
        floor += shift
        anchors = {a + shift: t for a, t in anchors.items()}

    delta = 0
    for a in sorted(anchors):
        here = sorted(anchors[a])
        anchor = a + delta
        name = anchor_name(here[0])
        if anchor >= len(lines) or name not in lines[anchor]:
            raise SystemExit(f"앵커 불일치: {here[0]} @ {path} — 그 줄에 {name} 이 없다")
        if in_py_string(path, lines, anchor):
            raise SystemExit(f"앵커가 문자열 안이다: {here[0]} @ {path}")
        cur = lines[anchor]
        indent = cur[: len(cur) - len(cur.lstrip())]
        # 선언 위의 주석 덩어리(JSDoc 등)보다 더 위에 놓는다. 그 사이를 가르면 hover 문서가 끊긴다.
        # 다만 셔뱅과 앞선 블록 아래로는 절대 못 내려간다.
        top = max(scan_top(lines, anchor), floor)
        blk = block_lines(here, terms, prefix, indent, used_by)
        inserts.append((top - (len(lines) - len(stripped)), len(blk)))
        lines[top:top] = blk
        delta += len(blk)
        floor = top + len(blk)

    where = relocate(lines)
    for t in file_tids:
        where[t] = 1                  # 파일 용어의 자리는 늘 첫 줄이다

    moved: dict[int, int] = {}
    for raw_idx, new_idx in old_to_new.items():
        shift = sum(n for pos, n in inserts if pos <= new_idx)
        moved[raw_idx + 1] = new_idx + shift + 1
    return "\n".join(lines), {t: where[t] for t in tids if t in where}, moved


def collect_targets(terms: Terms,
                    all_kinds: bool = False) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """{파일: [용어…]} 와 XML 에만 남길 용어들. where 의 파일 이름만 쓴다."""
    by_file: dict[str, list[str]] = {}
    skipped: list[tuple[str, str]] = []
    for tid, rec in terms.items():
        path, _ = split_where(rec.get("where"))
        if not path:
            skipped.append((tid, "위치 없음"))
            continue
        if not all_kinds and rec.get("kind") not in DECL_KINDS:
            skipped.append((tid, rec.get("kind")))
            continue
        if not os.path.exists(os.path.join(ROOT, path)):
            raise SystemExit(f"파일 없음: {path} ({tid})")
        by_file.setdefault(path, []).append(tid)
    return by_file, skipped


def carry_lines(terms: Terms, path: str, line_map: dict[int, int], skip: set[str]) -> int:
    """블록 때문에 밀린 줄을 따라 옮긴다. 마커가 있는 용어(skip)는 이미 제자리다.

    `uses[].where` 도 같이 옮긴다 — 거기엔 마커가 없어 스스로 제자리를 찾지 못한다.
    옮기는 것은 **이번에 블록이 민 만큼**뿐이다. 코드가 딴 데서 바뀌어 생긴 어긋남은
    여기서 고치지 못하고 L3 경고로 남는다."""
    n = 0
    for tid, rec in terms.items():
        if tid not in skip:
            p, ln = split_where(rec.get("where"))
            if p == path and ln in line_map and line_map[ln] != ln:
                rec["where"] = f"{path}:{line_map[ln]}"
                n += 1
        for u in rec.get("uses") or []:
            p, ln = split_where(u.get("where"))
            if p == path and ln in line_map and line_map[ln] != ln:
                u["where"] = f"{path}:{line_map[ln]}"
                n += 1
    return n


def run_inject(dry: bool, all_kinds: bool = False) -> None:
    terms: Terms = json.load(open(READING, encoding="utf-8"))
    by_file, skipped = collect_targets(terms, all_kinds)

    changed: list[str] = []
    moved, carried = 0, 0
    for path, tids in sorted(by_file.items()):
        abspath = os.path.join(ROOT, path)
        src = open(abspath, encoding="utf-8").read()
        new, where, line_map = plan_file(path, sorted(tids), terms, src)
        if new != src:
            changed.append(path)
            if not dry:
                open(abspath, "w", encoding="utf-8").write(new)
        for tid, ln in where.items():
            w = f"{path}:{ln}"
            if terms[tid].get("where") != w:
                terms[tid]["where"] = w
                moved += 1
        carried += carry_lines(terms, path, line_map, skip=set(where))

    if dry:
        print(f"[dry-run] 고칠 파일 {len(changed)}개 · where 갱신 {moved}건 · 따라 옮길 줄 {carried}건 · XML 에만 남을 용어 {len(skipped)}개")
        return
    open(READING, "w", encoding="utf-8").write(json.dumps(terms, ensure_ascii=False, indent=2) + "\n")
    open(XML_ABS, "w", encoding="utf-8").write(emit_xml(terms))
    why = Counter(k for _, k in skipped)
    print(f"주입 완료 — 파일 {len(changed)}개 · where 갱신 {moved}건 · 따라 옮긴 줄 {carried}건 · XML 항목 {len(terms)}개")
    print(f"  XML 에만 남은 용어 {len(skipped)}개 — {dict(why)}")


def run_check() -> int:
    """코드의 마커와 json 의 where 가 같은 자리를 가리키는지만 본다."""
    terms: Terms = json.load(open(READING, encoding="utf-8"))
    by_file, _ = collect_targets(terms)
    problems: list[str] = []
    seen = 0
    for path, tids in sorted(by_file.items()):
        lines = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
        found = relocate(lines)
        for tid in sorted(tids):
            ln = split_where(terms[tid].get("where"))[1]
            if tid not in found:
                problems.append(f"{tid}: {path}:{ln} 둘레에 레퍼런스가 없다")
                continue
            want = 1 if terms[tid].get("kind") == "file" else found[tid]
            if ln != want:
                problems.append(f"{tid}: where 가 {path}:{ln} 인데 마커 기준은 {path}:{want} 다")
            else:
                seen += 1
    if not os.path.exists(XML_ABS):
        problems.append(f"{XML_REL} 이 없다")
    elif open(XML_ABS, encoding="utf-8").read() != emit_xml(terms):
        problems.append(f"{XML_REL} 이 terms-reading.json 과 다르다 — emit 을 다시 돌려라")
    for p in problems[:20]:
        print("실패", p)
    print(f"레퍼런스 확인 {seen}건 · 문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("cmd", choices=["emit", "inject", "check"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-kinds", action="store_true",
                    help="쓰이는 자리만 가리키는 kind(external·key·artifact·concept)에도 박는다")
    a = ap.parse_args()
    if a.cmd == "emit":
        t: Terms = json.load(open(READING, encoding="utf-8"))
        open(XML_ABS, "w", encoding="utf-8").write(emit_xml(t))
        print(f"{XML_REL} — 용어 {len(t)}개")
    elif a.cmd == "inject":
        run_inject(a.dry_run, a.all_kinds)
    else:
        sys.exit(run_check())
