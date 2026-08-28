#!/usr/bin/env python3
"""demermaid.py — C-18 집행. 위키의 Mermaid 를 사전 렌더 SVG 로 치환한다.

C-8 이 "다이어그램은 deep-wiki 의 Mermaid 가 아니라 Graphviz P1~P6" 로 정했는데,
VitePress 기성 경로(`vitepress-plugin-mermaid`)는 **클라이언트에서 Mermaid 를 그린다.**
그대로 두면 C-8 이 무력화되므로 빌드 전에 전면 치환한다(C-18, A안).

치환은 두 단이다:

  1. **교체** — 우리가 이미 Graphviz 로 그린 구조 다이어그램이 있으면 그것으로 바꾼다.
     `<!-- graphviz: <이름> -->` 표식이 Mermaid 블록 **앞줄**에 있으면 그 SVG 를 쓴다.
     이것이 C-8 의 본뜻이다 — 구조는 Graphviz 가 정본.
  2. **렌더** — 표식이 없는 나머지(순서도·상태도 등 구조가 아닌 것)는 `mmdc` 로 SVG 를 굽는다.
     Mermaid 문법 자체는 살리되 **클라이언트 JS 의존을 없앤다.**

⚠ 이 스크립트는 원본을 고치지 않는다. `--out` 디렉토리에 치환본을 낸다 —
원본 위키는 인용 검증기의 대상으로 그대로 남아야 한다.

  demermaid.py <위키디렉토리> --out <출력디렉토리> [--svg-dir <graphviz svg 디렉토리>]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

FENCE = re.compile(r"^```mermaid\s*$")
MARK = re.compile(r"<!--\s*graphviz:\s*([A-Za-z0-9_.-]+)\s*-->")


# ── 알려진 mermaid 11.16 문법 제약 셋. 🔵 전부 이 저장소 위키에서 실측됐다.
#    전부 **색 지시자나 표기 문제**라 걷어내도 그림의 내용(노드·간선)은 바뀌지 않는다.
#    클라이언트 렌더에 맡겼다면 브라우저에서 조용히 깨졌을 것들이다 — C-18 전면 치환이
#    이것을 빌드 시점에 잡아낸다는 것이 A안의 실질 이득이다.

# (1) `style X~T~ fill:...` — 제네릭 클래스에 style 을 걸면 GENERICTYPE 토큰 오류
# (2) `style 한글이름 fill:...` — 비ASCII 식별자에 style 을 걸면 파서가 죽는다
GENERIC_STYLE = re.compile(r"^[ \t]*style[ \t]+(?:\S*~[^~]*~\S*|[^\s\x00-\x7f][^\s]*)[ \t][^\n]*\n?", re.M)

# (3) HTML 엔티티 — `&lt;T&gt;` 가 라벨에 그대로 들어오면 렉서가 못 읽는다.
#     VitePress 호환을 위해 제네릭을 이스케이프한 것이 mmdc 에서는 역효과다.
ENTITY = [("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"), ("&quot;", '"')]

# (4) 라벨 안의 백틱 — `["`이름`"]` 은 mermaid 의 markdown-string 문법이라
#     <br> 이나 꺾쇠와 섞이면 렉서가 죽는다. 백틱만 빼면 라벨 내용은 같다.
LABEL_BACKTICK = re.compile(r'(\["\[?)`([^`]*)`')


def _mmdc(src_text, out_svg):
    tmp = out_svg + ".mmd"
    open(tmp, "w", encoding="utf-8").write(src_text)
    r = subprocess.run(
        ["npx", "--no-install", "mmdc", "-i", tmp, "-o", out_svg,
         "-b", "transparent", "-t", "dark"],
        capture_output=True, text=True)
    os.remove(tmp)
    return r


def render_mermaid(src_text, out_svg):
    """mmdc 로 Mermaid 하나를 SVG 로 굽는다. 실패하면 None.

    한 번 실패하면 **알려진 문법 제약을 걷어내고 한 번만 재시도**한다.
    걷어내는 것은 색 지시자뿐이라 그림의 내용은 바뀌지 않는다."""
    r = _mmdc(src_text, out_svg)
    if r.returncode == 0:
        return out_svg

    stripped = GENERIC_STYLE.sub("", src_text)
    for a, b in ENTITY:
        stripped = stripped.replace(a, b)
    stripped = LABEL_BACKTICK.sub(r"\1\2", stripped)
    if stripped != src_text:
        r2 = _mmdc(stripped, out_svg)
        if r2.returncode == 0:
            print("  ↻ style 지시자/HTML 엔티티를 정리하고 재시도해 성공", file=sys.stderr)
            return out_svg
        r = r2

    tail = [l for l in (r.stderr or "").strip().splitlines() if l.strip()]
    print(f"  ⚠ mmdc 실패: {tail[0] if tail else '?'}", file=sys.stderr)
    return None


def process(path, outdir, assets, svg_dir, rel_assets):
    lines = open(path, encoding="utf-8").read().splitlines()
    out, i = [], 0
    stats = {"교체": 0, "렌더": 0, "실패": 0}
    base = os.path.splitext(os.path.basename(path))[0]

    while i < len(lines):
        if not FENCE.match(lines[i]):
            out.append(lines[i]); i += 1; continue

        # 블록 수집
        j = i + 1
        body = []
        while j < len(lines) and not lines[j].strip().startswith("```"):
            body.append(lines[j]); j += 1

        # 앞줄들에서 graphviz 표식 찾기 (빈 줄 건너뜀)
        mark = None
        for back in range(len(out) - 1, max(-1, len(out) - 4), -1):
            m = MARK.search(out[back])
            if m:
                mark = m.group(1); break

        n = stats["교체"] + stats["렌더"] + stats["실패"] + 1
        if mark and svg_dir:
            src = os.path.join(svg_dir, mark if mark.endswith(".svg") else mark + ".svg")
            if os.path.isfile(src):
                dst = os.path.join(assets, os.path.basename(src))
                shutil.copyfile(src, dst)
                out.append(f"![{mark}]({rel_assets}/{os.path.basename(src)})")
                out.append("")
                out.append(f"<!-- C-18: Graphviz 정본으로 교체됨 ({mark}). 원본 Mermaid 는 위키 원본에 있다 -->")
                stats["교체"] += 1
                i = j + 1
                continue
            print(f"  ⚠ 표식 '{mark}' 의 SVG 를 못 찾음 — mmdc 로 폴백", file=sys.stderr)

        name = f"{base}-{n}.svg"
        got = render_mermaid("\n".join(body), os.path.join(assets, name))
        if got:
            out.append(f"![diagram {n}]({rel_assets}/{name})")
            out.append("")
            out.append("<!-- C-18: mmdc 사전 렌더. 클라이언트 Mermaid JS 의존 없음 -->")
            stats["렌더"] += 1
        else:
            out.append("```mermaid"); out.extend(body); out.append("```")
            out.append("<!-- C-18: mmdc 실패 — Mermaid 원문 유지 -->")
            stats["실패"] += 1
        i = j + 1

    open(os.path.join(outdir, os.path.basename(path)), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wiki", help="위키 마크다운 디렉토리")
    ap.add_argument("--out", required=True, help="치환본 출력 디렉토리 (원본은 안 고친다)")
    ap.add_argument("--svg-dir", help="Graphviz SVG 디렉토리 — <!-- graphviz: 이름 --> 표식이 여기서 찾는다")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    assets = os.path.join(a.out, "assets")
    os.makedirs(assets, exist_ok=True)

    total = {"교체": 0, "렌더": 0, "실패": 0}
    docs = sorted(f for f in os.listdir(a.wiki) if f.endswith(".md"))
    for f in docs:
        s = process(os.path.join(a.wiki, f), a.out, assets, a.svg_dir, "assets")
        for k in total:
            total[k] += s[k]
        print(f"  {f} — 교체 {s['교체']} · 렌더 {s['렌더']} · 실패 {s['실패']}")

    print(f"\n{a.out} — 문서 {len(docs)}개")
    print(f"  Graphviz 교체 {total['교체']} · mmdc 렌더 {total['렌더']} · 실패 {total['실패']}")
    left = total["실패"]
    print(f"  남은 클라이언트 Mermaid 의존: {left}  (0 이어야 C-18 집행 완료)")
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
