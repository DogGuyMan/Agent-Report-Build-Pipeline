#!/usr/bin/env python3
"""코드 다섯(codewiki · term · spec · core · common)을 src/ 아래로 옮긴다 — 결정 0014 의 고침(2026-11-01).

git mv 로 옮기고 추적 텍스트 파일의 경로 토큰을 고친다. 토큰은 옮긴 뒤 src/ 아래에 실재할 때만 바꾸고(예시 경로를
실제 경로로 착각하지 않으려고), `../` 상대 경로는 그 파일의 옛 자리와 새 자리로 다시 계산한다. 파이썬 파일에서는
저장소 뿌리를 가리키는 사슬의 깊이와 `os.path.join(ROOT, "<다섯 중 하나>", …)` 꼴도 고친다. 줄 수를 바꾸지 않는다.
아카이브 문서는 건드리지 않는다. id 는 점 표기라 그대로다 — 수집기가 src/ 를 떼고 그 안을 뿌리로 본다."""
import json
import os
import re
import subprocess
import sys

from reorg_lib import ROOT, TOKEN, repo_key

MOVED = ("codewiki", "term", "spec", "core", "common")
SKIP_PREFIX = ("docs/handoffs/", "docs/superpowers/", "docs/my.self/", "docs/decisions/", "docs/overturn/",
               "docs/notes/", "docs/research/", "split-work/reorg/", "contracts/", "resource/codewiki/samples/")
SKIP_SUFFIX = (".png", ".svg", ".pdf", ".lock", ".csproj", ".cs", ".ico", ".woff", ".woff2")
READING = "resource/codewiki/terms-reading.json"
ROOT_CHAIN = re.compile(r"^(?P<head>\s*\w+\s*=\s*)(?P<chain>(?:os\.path\.dirname\()+)os\.path\.abspath\(__file__\)(?P<tail>\)+)(?P<rest>.*)$")
JOIN = re.compile(r'((?:os\.path\.join|Path)\(\s*(?:[\w.]*ROOT|root|ctx\.root|\{root!r\})\s*,\s*)"(codewiki|term|spec|core|common)"')


def git(*args: str) -> list[str]:
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return [l for l in r.stdout.split("\n") if l]


def exists(rel: str) -> bool:
    return os.path.exists(os.path.join(ROOT, rel.rstrip("/")))


def moved_path(rel: str) -> str:
    return "src/" + rel if rel.split("/")[0] in MOVED else rel


def map_repo_rel(rel: str) -> str:
    """옛 저장소 상대 경로 → 새 경로. src/ 아래 실재하거나, 글로브 · 아직 없는 파일이라도 둘째 단계 폴더가 실재할 때만."""
    segs = rel.split("/")
    if segs[0] not in MOVED:
        return rel
    new = "src/" + rel
    if exists(new) or (len(segs) >= 3 and exists("src/" + "/".join(segs[:2]))):
        return new
    return rel


def map_token(tok: str, old_file: str, new_file: str) -> str:
    if tok.startswith("../"):
        target_old = os.path.normpath(os.path.join(os.path.dirname(old_file), tok))
        if target_old.startswith(".."):
            return tok
        target_new = moved_path(target_old)
        if not exists(target_new):
            return tok
        return os.path.relpath(target_new, os.path.dirname(new_file) or ".") + ("/" if tok.endswith("/") else "")
    head, rest = repo_key(tok)
    tail = ""
    while rest.endswith("."):
        rest, tail = rest[:-1], tail + "."
    new = map_repo_rel(rest)
    return tok if new == rest else "/".join(head + [new + tail])


def rewrite_text(text: str, old_file: str, new_file: str) -> str:
    return TOKEN.sub(lambda m: map_token(m.group("path"), old_file, new_file) + (m.group("ln") or ""), text)


def rewrite_code(text: str, old_file: str, new_file: str) -> str:
    out: list[str] = []
    for line in text.split("\n"):
        if old_file != new_file:
            m = ROOT_CHAIN.match(line)
            if m and m.group("chain").count("os.path.dirname(") == old_file.count("/") + 1:
                k = new_file.count("/") + 1
                line = m.group("head") + "os.path.dirname(" * k + "os.path.abspath(__file__)" + ")" * k + m.group("rest")
        out.append(JOIN.sub(r'\1"src", "\2"', line))
    return "\n".join(out)


def main() -> int:
    if os.path.exists(os.path.join(ROOT, "src", "core")):
        print("이미 옮겼다")
        return 1
    before = set(git("ls-files"))
    os.makedirs(os.path.join(ROOT, "src"), exist_ok=True)
    for d in MOVED:
        git("mv", d, "src/" + d)
    changed = 0
    for new_rel in git("ls-files"):
        old_rel = new_rel[4:] if new_rel.startswith("src/") and new_rel[4:] in before else new_rel
        if new_rel.startswith(SKIP_PREFIX) or new_rel.endswith(SKIP_SUFFIX) or new_rel == READING:
            continue
        p = os.path.join(ROOT, new_rel)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        new = rewrite_text(text, old_rel, new_rel)
        if new_rel.endswith(".py") or new_rel.startswith("bin/"):
            new = rewrite_code(new, old_rel, new_rel)
        if new != text:
            assert new.count("\n") == text.count("\n"), new_rel
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)
            changed += 1

    rp = os.path.join(ROOT, READING)
    with open(rp, encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    assert json.dumps(data, ensure_ascii=False, indent=1) == raw

    def where(w: str) -> str:
        return rewrite_text(w, READING, READING)

    def ident(s: str) -> str:
        return map_repo_rel(s) if "/" in s else s

    out: dict[str, dict[str, object]] = {}
    for tid, rec in data.items():
        rec = dict(rec)
        rec["where"] = where(rec["where"])
        rec["module"] = ident(rec["module"])
        rec["uses"] = [{**u, "to": ident(u["to"]), "where": where(u["where"])} for u in rec.get("uses", [])]
        out[ident(tid)] = rec
    assert len(out) == len(data), "id 가 겹쳤다"
    with open(rp, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("옮김:", ", ".join("src/" + d for d in MOVED), "| 고친 파일:", changed + 1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
