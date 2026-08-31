# <include file="machine/comments.xml" path="//term[@id='link_paths.py']"/>
# 본문에 글자로 적힌 파일 경로를 그 파일을 여는 링크로 바꾸는 스크립트.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
# viz/link_paths.py — 빌드 후 통과 둘째. 본문에 글자로 적힌 경로 꼴 낱말을
# 실제 로컬 파일 · 폴더의 file:// 링크로 바꾼다.
#
# 자동 참조(wrap_terms.py)와 같은 자리에서 돈다. 용어(term-ref)는 뜻 카드, 코드 글꼴(.mono)은
# 파일 링크 — 역할이 갈리므로 term-ref 안은 건너뛰고 .mono 안은 포함한다.
# 없는 파일은 링크하지 않는다 — 계획에만 있는 파일이 링크되면 독자가 속는다.
#
# 파일 시스템을 읽는 함수(buildIndex · makeResolver)는 내보내되 모듈 최상위에서 실행하지 않는다.
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Match, Optional

# 이 요소 안의 글자는 건드리지 않는다. a 가 들어 있는 이유는 링크 안에 링크를 넣지 않기 위함이다.
SKIP_TAGS = frozenset({"script", "style", "svg", "summary", "h1", "h2", "h3",
                       "th", "title", "a", "textarea"})
# class 에 이 낱말이 있으면 그 요소 안을 건드리지 않는다 — 용어 참조 · 카드 · 용어집 · 관계도 · 다이어그램.
SKIP_CLASSES = ("term-ref", "term-card", "term-groups", "term-graph", "svg-wrap")
VOID_TAGS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "source", "track", "wbr"})
EXT = "md|mjs|py|ts|tsx|json|css|html|dot|svg|yaml|yml|toml|cs|cpp|h"

TAG_RE = re.compile(r"<\/?([A-Za-z][A-Za-z0-9-]*)\b[^>]*>|<!--[\s\S]*?-->")
VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def pathPattern() -> re.Pattern[str]:
    """경로 꼴 — `a/b.md:3` `c.json` `facts/*.md` `x.py`.

    앞뒤가 낱말 · 경로 글자가 아니어야 한다. URL(`http://x.com/a.md`)은 앞 글자가
    `/` 나 `.` 라 lookbehind 에 막힌다. 그룹 1 은 줄 번호를 뗀 경로, 그룹 2 는 줄 번호다.
    """
    return re.compile(
        r"(?<![\w/.:-])((?:[\w.@-]+/)*(?:[\w.@-]+\.(?:" + EXT + r")|\*\.(?:" + EXT + r")))"
        r"(?::(\d+(?:-\d+)?))?(?![\w/])")


def buildIndex(repoRoot: str) -> dict[str, list[str]]:
    """저장소 추적 파일의 이름 색인. {basename: [상대경로…]}. git 밖이면 빈 사전."""
    index: dict[str, list[str]] = {}
    try:
        r = subprocess.run(["git", "-C", repoRoot, "ls-files"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return index
    except OSError:
        return index
    for rel in r.stdout.split("\n"):
        if not rel:
            continue
        index.setdefault(os.path.basename(rel), []).append(rel)
    return index


def expandRoot(base: str) -> str:
    """경로 앞머리의 `~` 와 `$VAR` / `${VAR}` 를 편다.

    공개 저장소에 유저명을 남기지 않으려고 `data.ts` 의 `linkRoots` 를
    `$CSHARP_REPO/out/codegraph-raw` 같은 꼴로 적는다. 값이 없으면 그 자리는 빈 문자열이
    되고 디렉토리 검사가 걸러 내므로, 그 폴더가 없는 독자에게는 조용히 링크가 안 걸릴 뿐이다.
    """
    out = str(base)
    if out == "~" or out.startswith("~/"):
        out = os.path.join(os.path.expanduser("~"), out[1:].lstrip("/"))
    return VAR_RE.sub(lambda m: os.environ.get(m.group(1) or m.group(2) or "", ""), out)


def makeResolver(bases: list[str], repoRoot: str,
                 index: Optional[dict[str, list[str]]] = None
                 ) -> Callable[[str], Optional[dict[str, str]]]:
    """해석기. token(줄 번호 뗀 경로) -> {href, kind: "file"|"dir"} 또는 None.

    순서: bases 를 차례로(보고서 폴더 → specs/ → 저장소 루트 → out/codegraph-raw → linkRoots)
    → 이름만이면 색인에서 **유일할 때만**.
    """
    seen: list[str] = []
    for b in bases:
        if not b:
            continue
        e = expandRoot(b)
        if e and e not in seen and os.path.isdir(e):
            seen.append(e)

    def resolve(token: str) -> Optional[dict[str, str]]:
        if "*" in token:
            d = os.path.dirname(token)
            for b in seen:
                p = os.path.join(b, d)
                if os.path.isdir(p):
                    return {"href": Path(p).as_uri(), "kind": "dir"}
            return None
        for b in seen:
            p = os.path.join(b, token)
            if os.path.isfile(p):
                return {"href": Path(p).as_uri(), "kind": "file"}
        if "/" not in token and index and repoRoot:
            hits = index.get(token, [])
            if len(hits) == 1 and os.path.isfile(os.path.join(repoRoot, hits[0])):
                return {"href": Path(os.path.join(repoRoot, hits[0])).as_uri(), "kind": "file"}
        return None

    return resolve


def skipsByClass(tag: str) -> bool:
    """여는 태그의 class 에 건너뛸 낱말이 있는지 본다."""
    m = re.search(r'\sclass=["\']([^"\']*)["\']', tag)
    if not m:
        return False
    cls = m.group(1).split()
    return any(c in cls for c in SKIP_CLASSES)


def linkPaths(html: str, resolve: Callable[[str], Optional[dict[str, str]]],
              onMiss: Optional[Callable[[str], None]] = None) -> str:
    """html 의 글자 부분에서 경로 꼴을 찾아 resolve 가 답하는 것만 링크로 감싼다.

    글자(줄 번호 포함)는 그대로 남는다. 감싼 결과는 a 안이라 다시 훑지 않는다(멱등).
    onMiss 는 못 찾은 경로를 알리는 선택 콜백이다.
    """
    re_path = pathPattern()
    stack: list[tuple[str, bool]] = []

    def sub_one(m: Match[str]) -> str:
        whole, path = m.group(0), m.group(1)
        r = resolve(path)
        if not r:
            if onMiss:
                onMiss(path)
            return whole
        # 새 탭 — 보고서 탭을 덮지 않는다. rel=noopener 는 새 탭이 이 창을 잡지 못하게 한다.
        return ('<a class="path-link" target="_blank" rel="noopener" href="%s">%s</a>'
                % (r["href"], whole))

    def text(s: str) -> str:
        if not s or any(skip for _, skip in stack):
            return s
        return re_path.sub(sub_one, s)

    out: list[str] = []
    last = 0
    for m in TAG_RE.finditer(html):
        out.append(text(html[last:m.start()]))
        tag = m.group(0)
        last = m.end()
        out.append(tag)
        if tag.startswith("<!--"):
            continue
        name = (m.group(1) or "").lower()
        if tag.startswith("</"):
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == name:
                    del stack[i:]
                    break
        elif name not in VOID_TAGS and not tag.endswith("/>"):
            stack.append((name, name in SKIP_TAGS or skipsByClass(tag)))
    out.append(text(html[last:]))
    return "".join(out)
