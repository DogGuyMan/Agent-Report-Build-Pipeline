#!/usr/bin/env python3
"""xmldoc.py — 주석 본문을 .xml 한 곳에 모으고 코드에는 레퍼런스만 남긴다.

**왜.** 같은 설명이 코드 주석과 terms-reading.json 두 군데 살면 반드시 어긋난다.
뜻은 XML 한 곳에 두고, 코드에는 그 항목을 가리키는 include 지시 한 줄과
사람이 스쳐 읽을 한 줄 설명만 박는다.

**정본은 docs/codegraph/terms-reading.json 이다.** comments.xml 은 파생물이라
손으로 고치지 않는다. 뜻을 바꾸려면 json 을 고치고 `emit` 을 다시 돌린다.

  xmldoc.py emit                 -> docs/codegraph/comments.xml 생성
  xmldoc.py inject [--dry-run]   -> 코드에 레퍼런스 블록 주입/갱신 + json 의 where 재계산 + emit
  xmldoc.py check                -> 코드의 레퍼런스가 json 과 맞는지만 본다. 어긋나면 종료 코드 1

주입 블록은 정확히 두 줄이고 include 줄로 식별한다. 다시 돌리면 덧붙지 않고 갈린다.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from xml.sax.saxutils import escape, quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READING = os.path.join(ROOT, "docs/codegraph/terms-reading.json")
XML_REL = "docs/codegraph/comments.xml"
XML_ABS = os.path.join(ROOT, XML_REL)

# 확장자별 한 줄 주석 접두사. 확장자가 없으면 bin/ 의 node 스크립트라 // 다.
LINE_COMMENT = {".py": "#", ".ts": "//", ".tsx": "//", ".mjs": "//", ".js": "//", "": "//"}

INCLUDE_RE = re.compile(r"^\s*(#|//)\s*<include file=\"" + re.escape(XML_REL) + r"\"")

# 코드에 레퍼런스를 박을 수 있는 kind. 선언 줄이 실제로 있는 것만이다.
# external · key · artifact · concept 의 where 는 **쓰이는 자리**를 가리킨다. 문자열 안이거나
# 식 한복판이라 그 위에 뜻풀이를 얹으면 거짓말이 된다 — 이것들은 XML 에만 산다.
DECL_KINDS = frozenset({"function", "class", "struct", "enum", "interface",
                        "delegate", "record", "file"})


def prefix_for(path):
    ext = os.path.splitext(path)[1]
    if ext not in LINE_COMMENT:
        raise SystemExit(f"주석 접두사를 모르는 확장자: {path}")
    return LINE_COMMENT[ext]


def split_where(where):
    """`file:line` -> (file, line). 위치가 없으면 (None, None)."""
    if not where:
        return None, None
    path, sep, ln = where.rpartition(":")
    if sep and ln.isdigit():
        return path, int(ln)
    return None, None


def anchor_name(term_id):
    """앵커 줄에서 찾을 이름. 점 표기는 마지막 마디, 배열 키는 [] 를 뗀다."""
    return term_id.split(".")[-1].removesuffix("[]")


# ---------------------------------------------------------------- XML 내보내기

def emit_xml(terms):
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           "<!-- 이 파일은 파생물이다. docs/codegraph/terms-reading.json 을 고치고",
           "     codegraph/xmldoc.py emit 을 다시 돌려서 만든다. 손으로 고치지 않는다. -->",
           "<terms>"]
    for tid in sorted(terms):
        rec = terms[tid]
        attrs = f"id={quoteattr(tid)}"
        for k in ("kind", "module", "where", "source"):
            if rec.get(k):
                attrs += f" {k}={quoteattr(rec[k])}"
        uses = rec.get("uses") or []
        body = [f'    <{k}>{escape(rec[k])}</{k}>' for k in ("means", "does") if rec.get(k)]
        for u in uses:
            ua = " ".join(f"{k}={quoteattr(str(u[k]))}" for k in ("to", "kind", "label", "where", "source") if u.get(k))
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
# 블록의 모양 — include 줄 n 개가 먼저, 그 다음 한 줄 설명 n 개. 길이는 항상 2n 이라
# 다시 돌릴 때 자를 범위를 세지 않고 알 수 있다.
#
#   # <include file="docs/codegraph/comments.xml" path="//term[@id='Fact']"/>
#   # 사실 한 건을 담는 자료 구조.
#   class Fact:
#
# 놓는 자리는 **선언 위에 이미 있는 주석 덩어리보다 더 위**다. JSDoc 이나 파이썬 주석과
# 선언 사이를 갈라놓으면 편집기의 hover 문서가 끊긴다.

COMMENTISH = ("#", "//", "/*", "*", "*/")


def is_commentish(line):
    s = line.strip()
    return s.startswith(COMMENTISH) if s else False


def block_lines(tids, terms, prefix, indent):
    """한 앵커에 붙일 레퍼런스 블록. 같은 줄에 여러 용어가 걸리면 함께 낸다."""
    lines = [f"{indent}{prefix} <include file=\"{XML_REL}\" path=\"//term[@id='{t}']\"/>" for t in tids]
    for tid in tids:
        means = (terms[tid].get("means") or "").replace("\n", " ").strip()
        label = f"{tid} — " if len(tids) > 1 else ""
        lines.append(f"{indent}{prefix} {label}{means}".rstrip())
    return lines


def file_anchor(lines):
    """kind=file 의 삽입 지점(0-based). 셔뱅이 있으면 그 아래."""
    return 1 if lines and lines[0].startswith("#!") else 0


def in_py_string(path, lines, idx):
    """파이썬 파일에서 idx 줄이 삼중 따옴표 문자열 안인가. 홀짝만 센다 — 안전판이다."""
    if not path.endswith(".py"):
        return False
    head = "\n".join(lines[:idx])
    return (head.count(chr(34) * 3) % 2 == 1) or (head.count(chr(39) * 3) % 2 == 1)


def scan_top(lines, anchor_idx):
    """선언 위에 붙어 있는 주석 덩어리의 첫 줄. 빈 줄을 만나면 멈춘다."""
    i = anchor_idx
    while i > 0 and is_commentish(lines[i - 1]):
        i -= 1
    return i


def own_block_len(lines, top):
    """top 부터 시작하는 우리 블록의 길이. 없으면 0. include 줄 n 개 -> 2n 줄."""
    c = 0
    while top + c < len(lines) and INCLUDE_RE.match(lines[top + c]):
        c += 1
    return 2 * c


def strip_blocks(lines):
    """이미 박힌 레퍼런스 블록을 전부 걷어낸다. (깨끗한 줄들, 각 줄 앞에서 지워진 줄 수).

    걷어내고 다시 넣는 이유는 자리다툼을 없애기 위해서다. 남겨 두고 고치려 들면
    파일 용어의 블록과 첫 함수의 블록이 같은 자리를 두고 싸운다."""
    out, removed_before = [], []
    i = 0
    while i < len(lines):
        if INCLUDE_RE.match(lines[i]):
            c = 0
            while i + c < len(lines) and INCLUDE_RE.match(lines[i + c]):
                c += 1
            i += 2 * c            # include 줄 c 개 + 설명 줄 c 개
            continue
        removed_before.append(i - len(out))
        out.append(lines[i])
        i += 1
    return out, removed_before


def plan_file(path, entries, terms, src):
    """한 파일에 블록을 넣는다. entries = [(현재 파일의 줄번호, [tid,...])].
    반환 (새 본문, {tid: 새 줄번호(1-based)}). 줄 번호는 다시 찾지 않고 셈으로 낸다."""
    raw = src.split("\n")
    lines, removed_before = strip_blocks(raw)
    # 걷어낸 뒤의 줄 번호로 옮긴다. removed_before[new_idx] = 그 줄 앞에서 지워진 줄 수.
    old_to_new = {}
    for new_idx, gap in enumerate(removed_before):
        old_to_new[new_idx + gap] = new_idx

    prefix = prefix_for(path)
    where = {}

    file_tids = sorted(t for _, tids in entries for t in tids if terms[t].get("kind") == "file")
    sym = []
    for ln, tids in entries:
        tids = [t for t in tids if terms[t].get("kind") != "file"]
        if not tids:
            continue
        old = ln - 1
        if old not in old_to_new:
            raise SystemExit(f"앵커가 옛 블록 안이다: {tids[0]} @ {path}:{ln}")
        sym.append((old_to_new[old], sorted(tids)))

    floor = file_anchor(lines)
    if file_tids:
        blk = block_lines(file_tids, terms, prefix, "")
        lines[floor:floor] = blk
        shift = len(blk)
        floor += shift
        sym = [(a + shift, t) for a, t in sym]
        for t in file_tids:
            where[t] = 1              # 파일 용어의 자리는 늘 첫 줄이다

    delta = 0
    for anchor, tids in sorted(sym):
        anchor += delta
        name = anchor_name(tids[0])
        if anchor >= len(lines) or name not in lines[anchor]:
            raise SystemExit(f"앵커 불일치: {tids[0]} @ {path} — 그 줄에 {name} 이 없다")
        if in_py_string(path, lines, anchor):
            raise SystemExit(f"앵커가 문자열 안이다: {tids[0]} @ {path}")
        cur = lines[anchor]
        indent = cur[: len(cur) - len(cur.lstrip())]
        # 선언 위의 주석 덩어리(JSDoc 등)보다 더 위에 놓는다. 그 사이를 가르면 hover 문서가 끊긴다.
        # 다만 셔뱅과 앞선 블록 아래로는 절대 못 내려간다.
        top = max(scan_top(lines, anchor), floor)
        blk = block_lines(tids, terms, prefix, indent)
        lines[top:top] = blk
        delta += len(blk)
        floor = top + len(blk)
        for t in tids:
            where[t] = anchor + len(blk) + 1
    return "\n".join(lines), where


def run_inject(dry, all_kinds=False):
    terms = json.load(open(READING, encoding="utf-8"))
    by_file, skipped = {}, []
    for tid, rec in terms.items():
        path, ln = split_where(rec.get("where"))
        if not path:
            skipped.append((tid, "위치 없음"))
            continue
        if not all_kinds and rec.get("kind") not in DECL_KINDS:
            skipped.append((tid, rec.get("kind")))
            continue
        if not os.path.exists(os.path.join(ROOT, path)):
            raise SystemExit(f"파일 없음: {path} ({tid})")
        by_file.setdefault(path, {}).setdefault(ln, []).append(tid)

    changed, moved = [], 0
    for path, per_line in sorted(by_file.items()):
        abspath = os.path.join(ROOT, path)
        src = open(abspath, encoding="utf-8").read()
        entries = [(ln, sorted(tids)) for ln, tids in sorted(per_line.items())]
        new, where = plan_file(path, entries, terms, src)
        if new != src:
            changed.append(path)
            if not dry:
                open(abspath, "w", encoding="utf-8").write(new)
        for tid, ln in where.items():
            w = f"{path}:{ln}"
            if terms[tid].get("where") != w:
                terms[tid]["where"] = w
                moved += 1

    if dry:
        print(f"[dry-run] 고칠 파일 {len(changed)}개 · where 갱신 {moved}건 · XML 에만 남을 용어 {len(skipped)}개")
        return
    open(READING, "w", encoding="utf-8").write(json.dumps(terms, ensure_ascii=False, indent=2) + "\n")
    open(XML_ABS, "w", encoding="utf-8").write(emit_xml(terms))
    why = Counter(k for _, k in skipped)
    print(f"주입 완료 — 파일 {len(changed)}개 · where 갱신 {moved}건 · XML 항목 {len(terms)}개")
    print(f"  XML 에만 남은 용어 {len(skipped)}개 — {dict(why)}")


def run_check():
    terms = json.load(open(READING, encoding="utf-8"))
    problems, seen = [], 0
    for tid, rec in terms.items():
        path, ln = split_where(rec.get("where"))
        if not path or rec.get("kind") not in DECL_KINDS:
            continue
        lines = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
        lo = 0 if rec.get("kind") == "file" else max(0, ln - 1 - 40)
        hi = 8 if rec.get("kind") == "file" else ln - 1
        want = f"path=\"//term[@id='{tid}']\"/>"
        if any(want in l and INCLUDE_RE.match(l) for l in lines[lo:hi]):
            seen += 1
        else:
            problems.append(f"{tid}: {path}:{ln} 둘레에 레퍼런스가 없다")
    if not os.path.exists(XML_ABS):
        problems.append(f"{XML_REL} 이 없다")
    elif open(XML_ABS, encoding="utf-8").read() != emit_xml(terms):
        problems.append(f"{XML_REL} 이 terms-reading.json 과 다르다 — emit 을 다시 돌려라")
    for p in problems[:20]:
        print("실패", p)
    print(f"레퍼런스 확인 {seen}건 · 문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["emit", "inject", "check"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-kinds", action="store_true",
                    help="쓰이는 자리만 가리키는 kind(external·key·artifact·concept)에도 박는다")
    a = ap.parse_args()
    if a.cmd == "emit":
        t = json.load(open(READING, encoding="utf-8"))
        open(XML_ABS, "w", encoding="utf-8").write(emit_xml(t))
        print(f"{XML_REL} — 용어 {len(t)}개")
    elif a.cmd == "inject":
        run_inject(a.dry_run, a.all_kinds)
    else:
        sys.exit(run_check())
