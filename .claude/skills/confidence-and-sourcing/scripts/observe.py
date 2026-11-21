#!/usr/bin/env python3
"""읽기 · 찾기 · 실행을 대신 돌리고 그 결과를 파일에 기억해 두는 얇은 관찰 세션. 표준 라이브러리만 쓴다.

    python3 observe.py read <파일> [<줄>|<줄-줄>] [--defer]     # 읽는다
    python3 observe.py grep <정규식> [<경로>…] [-i] [--defer]   # 찾는다. 경로가 없으면 git 이 추적하는 파일 전부
    python3 observe.py run [--defer] <명령…>                   # 셸로 돌린다. 임의의 명령이 그대로 돈다
    python3 observe.py show [E<번호>]                          # 모아 둔 출력을 받는다. 번호를 주면 그것 하나를 다시
    python3 observe.py check <글 파일>                          # 글의 인용을 이 세션이 본 줄과 대조한다
    python3 observe.py more <횟수>                             # 사용자에게 더 받은 시도 횟수를 더한다
    python3 observe.py status
    python3 observe.py end [--out <파일.json>]                 # 기억을 남길 자리에 옮기고 세션을 닫는다

떠 있는 프로세스는 없다. 호출마다 상태 파일을 읽고, 일을 하고, 다시 쓰고 끝난다. 세션은 그 파일이다 — 처음 관찰할 때
생기고 `end` 가 닫는다. 상태 파일은 저장소 밖(임시 폴더)에 있고, 쓰는 쪽이 열어 볼 일이 없다.

파일이 드는 것 — 사건 번호와 시각 · 부른 횟수와 거절한 횟수 · 파일별로 본 줄과 그때의 해시 · 찾기가 훑은 파일 수와
찾은 줄 · 돌린 명령과 종료 코드와 출력. 주장 · 전제 · 질문 · 티어 · 남은 검색의 어림은 들지 않는다 — 쓰는 쪽의 일이다.

출력은 호출마다 고른다. 그냥 부르면 답에 바로 오고, `--defer` 를 붙이면 확인 한 줄만 오고 출력은 파일에 쌓인다.
읽고 찾고 돌리는 횟수에는 위가 있다(기본 100번). 넘기면 거절하고, `more` 로 더 받아야 잇는다.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Any, NamedTuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_confidence as C  # noqa: E402

SCHEMA = "observe-session/1"
OBSERVATIONS = ("read", "grep", "run")
TRY_LIMIT = int(os.environ.get("CONFIDENCE_SESSION_LIMIT", "100"))   # 한 세션이 읽고 찾고 돌릴 수 있는 횟수의 위
MAX_LINES = 2000        # read 한 번이 보여 주는 줄 수의 위
MAX_HITS = 200          # grep 한 번이 기록하는 줄 수의 위. 넘는 것은 본 것으로 치지 않는다
MAX_OUTPUT = 400        # run 이 바로 보여 주는 줄 수의 위
MAX_STORE = 2000        # run 의 출력 중 기억에 남기는 줄 수의 위
MAX_BYTES = 2_000_000   # grep 이 훑는 파일 크기의 위
IDLE_SECONDS = 6 * 3600 # 이만큼 쓰지 않은 세션은 다음 관찰이 시작될 때 남길 자리로 옮기고 새로 시작한다
SKIP_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv"})
NO_SESSION = "세션이 없다 — read · grep · run 을 부르면 생긴다"

Event = dict[str, Any]


class Reply(NamedTuple):
    text: str
    code: int


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Context:
    """세션 하나의 기억. 호출마다 상태 파일에서 되살리고 다시 쓴다.

    관찰을 일어난 순서대로 쌓고, 어느 파일의 어느 줄을 봤는지를 그 사건들에서 찾는다.
    """

    def __init__(self, root: str, events: Optional[list[Event]] = None, started_at: Optional[str] = None,
                 limit: int = TRY_LIMIT, calls: Optional[int] = None, refused: int = 0,
                 grants: Optional[list[dict[str, Any]]] = None) -> None:
        self.root = os.path.realpath(root)
        self.started_at = started_at or now()
        self.ended_at: Optional[str] = None
        self.limit = limit                    # 읽고 찾고 돌릴 수 있는 횟수의 위
        self.refused = refused                # 위를 넘기려다 거절당한 횟수
        self.grants: list[dict[str, Any]] = grants or []   # 횟수를 더 받은 때와 양
        self.events: list[Event] = []
        self.seen: dict[str, set[int]] = {}   # 파일 -> 지금 아는 판에서 본 줄 번호
        self.sha: dict[str, str] = {}         # 파일 -> 마지막으로 봤을 때의 해시
        for event in events or []:
            self.events.append(event)
            self._index(event)
        # 읽고 찾고 돌리려고 부른 횟수. 실패해 사건을 남기지 못한 호출도 센다.
        self.calls = sum(1 for e in self.events if e["kind"] in OBSERVATIONS) if calls is None else calls

    # ── 기억 ─────────────────────────────────────────────────────────────
    def key(self, path: str) -> str:
        """저장소 안의 파일은 뿌리 기준 경로로, 밖의 파일은 절대 경로로 부른다."""
        real = os.path.realpath(path)
        return os.path.relpath(real, self.root) if real == self.root or real.startswith(self.root + os.sep) else real

    def _add(self, kind: str, **fields: Any) -> Event:
        event: Event = {"n": len(self.events) + 1, "at": now(), "kind": kind, **fields}
        self.events.append(event)
        self._index(event)
        return event

    def _mark(self, path: str, sha: str, lines: Any) -> None:
        """파일의 줄을 봤다고 적는다. 해시가 달라졌으면 전에 본 줄은 다른 판의 것이라 버린다."""
        if self.sha.get(path) != sha:
            self.seen[path] = set()
            self.sha[path] = sha
        self.seen[path].update(lines)

    def _index(self, event: Event) -> None:
        if event["kind"] == "read" and not event.get("missing"):
            lo, hi = event["lines"]
            self._mark(event["path"], event["sha256"], range(lo, hi + 1))
        elif event["kind"] == "grep":
            for path, sha in event["sha256"].items():
                self._mark(path, sha, [line for hit, line in event["hits"] if hit == path])

    def dump(self) -> dict[str, Any]:
        return {"schema": SCHEMA, "root": self.root, "started_at": self.started_at, "ended_at": self.ended_at,
                "limit": self.limit, "calls": self.calls, "refused": self.refused, "grants": self.grants,
                "events": self.events}

    @classmethod
    def load(cls, data: dict[str, Any]) -> "Context":
        return cls(data["root"], data["events"], data["started_at"], data.get("limit", TRY_LIMIT),
                   data.get("calls"), data.get("refused", 0), data.get("grants", []))

    # ── 횟수의 위 ────────────────────────────────────────────────────────
    def _used(self) -> str:
        return "[%d/%d]" % (self.calls, self.limit)

    def _take_try(self) -> Optional[Reply]:
        """호출 하나를 센다. 위에 닿았으면 세지 않고 거절한다."""
        if self.calls < self.limit:
            self.calls += 1
            return None
        self.refused += 1
        return Reply("시도 상한에 닿았다 %s — 더 읽거나 찾거나 돌리지 않는다.\n"
                     "남은 검색이 얼마쯤인지 사용자에게 보고하고, 더 찾으라는 답을 받으면 `more <횟수>` 로 잇는다. "
                     "스스로 늘리지 않는다." % self._used(), 3)

    def more(self, count: int) -> Reply:
        """사용자에게 더 받은 횟수를 위에 더하고, 언제 얼마를 받았는지 적는다."""
        if count <= 0:
            return Reply("더 받는 횟수는 1 이상이다", 2)
        self.limit += count
        self.grants.append({"at": now(), "more": count})
        return Reply("%d번을 더 받았다 %s" % (count, self._used()), 0)

    # ── 관찰 — 읽기 · 찾기 · 돌리기 ───────────────────────────────────────
    def _seen_before(self, key: str, lo: int, hi: int, sha: str) -> str:
        """이 줄들을 같은 판에서 이미 다 봤으면 그 알림. 그 범위를 덮는 읽기가 있으면 번호를 댄다."""
        seen = self.seen.get(key, set())
        if self.sha.get(key) != sha or hi < lo or any(n not in seen for n in range(lo, hi + 1)):
            return ""
        for e in self.events:
            if (e["kind"] == "read" and not e.get("missing") and e["path"] == key and e["sha256"] == sha
                    and e["lines"][0] <= lo and hi <= e["lines"][1]):
                return " · 이미 봄(E%d)" % e["n"]
        return " · 이미 봄"

    def read(self, path: str, lines: str = "", defer: bool = False) -> Reply:
        """파일의 줄을 번호와 함께 돌려주고, 본 범위와 그때의 해시를 쌓는다. `defer` 면 출력은 쌓아만 둔다."""
        refusal = self._take_try()
        if refusal:
            return refusal
        key = self.key(path)
        if not os.path.isfile(path):
            event = self._add("read", path=key, missing=True, shown=True)
            return Reply("E%d %s %s — 파일이 없다" % (event["n"], self._used(), key), 1)
        with open(path, encoding="utf-8", errors="replace") as f:
            body = f.read().split("\n")
        if body and body[-1] == "":
            body.pop()
        first, _, last = lines.partition("-")
        lo = max(1, int(first)) if first else 1
        hi = int(last) if last else (lo if first else len(body))
        hi = min(hi, len(body), lo + MAX_LINES - 1)
        if body and lo > len(body):
            return Reply("%s 는 %d줄이다. %d줄부터는 없다" % (key, len(body), lo), 1)
        sha = sha256_file(path)
        earlier = self._seen_before(key, lo, hi, sha)
        output = "\n".join("%d\t%s" % (i, body[i - 1]) for i in range(lo, hi + 1))
        event = self._add("read", path=key, lines=[lo, hi], total=len(body), sha256=sha, output=output, shown=not defer)
        head = "E%d %s %d줄%s" % (event["n"], self._used(), len(body), earlier)
        return Reply("%s · %d-%d 모아 둠" % (head, lo, hi) if defer else head + "\n" + output, 0)

    def _files(self, paths: list[str]) -> list[str]:
        """찾을 파일들. 경로를 주지 않으면 git 이 추적하는 파일, git 밖이면 뿌리 아래 전부다."""
        if not paths:
            try:
                r = subprocess.run(["git", "-C", self.root, "ls-files"], capture_output=True, text=True)
                tracked = [os.path.join(self.root, rel) for rel in r.stdout.split("\n") if rel] if r.returncode == 0 else []
            except OSError:
                tracked = []
            if tracked:
                return tracked
            paths = [self.root]
        out: list[str] = []
        for path in paths:
            if os.path.isfile(path):
                out.append(path)
            for folder, dirs, names in os.walk(path):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                out.extend(os.path.join(folder, name) for name in sorted(names))
        return out

    def grep(self, pattern: str, paths: list[str], ignore_case: bool = False, defer: bool = False) -> Reply:
        """정규식에 맞는 줄을 찾아 돌려주고, 찾은 줄 · 훑은 파일 수 · 그때의 해시를 쌓는다. 0건도 쌓는다."""
        refusal = self._take_try()
        if refusal:
            return refusal
        rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
        hits: list[list[Any]] = []
        shown: list[str] = []
        shas: dict[str, str] = {}
        scanned = count = 0
        for path in self._files(paths):
            try:
                with open(path, "rb") as f:
                    raw = f.read(MAX_BYTES + 1)
            except OSError:
                continue
            if len(raw) > MAX_BYTES or b"\0" in raw[:1024]:
                continue
            scanned += 1
            key = self.key(path)
            for i, line in enumerate(raw.decode("utf-8", errors="replace").split("\n"), 1):
                if rx.search(line):
                    count += 1
                    if len(hits) < MAX_HITS:
                        hits.append([key, i])
                        shown.append("%s:%d: %s" % (key, i, line.strip()[:200]))
                        shas[key] = hashlib.sha256(raw).hexdigest()
        if count > len(hits):
            shown.append("… 외 %d건은 기록하지 않았다. 경로나 정규식을 좁혀 다시 찾는다" % (count - len(hits)))
        output = "\n".join(shown)
        event = self._add("grep", pattern=pattern, paths=[self.key(p) for p in paths], ignore_case=ignore_case,
                          scanned=scanned, count=count, hits=hits, sha256=shas, output=output, shown=not defer)
        head = "E%d %s %d건 (%d파일)" % (event["n"], self._used(), count, scanned)
        if defer:
            return Reply(head + " 모아 둠", 0)
        return Reply(head + ("\n" + output if output else ""), 0)

    def run(self, command: str, cwd: str, defer: bool = False, timeout: int = 120) -> Reply:
        """명령을 셸로 돌려 출력을 돌려주고, 명령 · 종료 코드 · 출력과 그 해시를 쌓는다. 종료 코드는 그대로 넘긴다."""
        refusal = self._take_try()
        if refusal:
            return refusal
        try:
            done = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True,
                                  errors="replace", timeout=timeout)
            full, code = done.stdout + done.stderr, done.returncode
        except subprocess.TimeoutExpired:
            full, code = "(%d초 안에 끝나지 않아 멈췄다)\n" % timeout, 124
        body = full.split("\n")
        if body and body[-1] == "":
            body.pop()
        event = self._add("run", command=command, cwd=self.key(cwd), exit=code, lines=len(body),
                          sha256=hashlib.sha256(full.encode("utf-8")).hexdigest(),
                          output="\n".join(body[:MAX_STORE]), truncated=len(body) > MAX_STORE, shown=not defer)
        head = "E%d %s exit %d" % (event["n"], self._used(), code)
        if defer:
            return Reply("%s · %d줄 모아 둠" % (head, len(body)), code)
        out = [head] + body[:MAX_OUTPUT]
        if len(body) > MAX_OUTPUT:
            out.append("… 외 %d줄 — `show E%d` 로 받는다" % (len(body) - MAX_OUTPUT, event["n"]))
        return Reply("\n".join(out), code)

    # ── 모아 둔 출력 ─────────────────────────────────────────────────────
    def _title(self, event: Event) -> str:
        """출력 하나가 어느 호출의 것인지."""
        head = "E%d %s" % (event["n"], event["kind"])
        if event["kind"] == "read":
            return "%s %s%s" % (head, event["path"], " (없는 파일)" if event.get("missing") else ":%d-%d" % tuple(event["lines"]))
        if event["kind"] == "grep":
            return "%s %r %d건 (%d파일)" % (head, event["pattern"], event["count"], event["scanned"])
        return "%s exit %d $ %s" % (head, event["exit"], event["command"][:120])

    def show(self, number: Optional[int] = None) -> Reply:
        """아직 받지 않은 출력을 전부 돌려주고 받았다고 적는다. 번호를 주면 그 관찰 하나를 다시 돌려준다."""
        if number is None:
            picked = [e for e in self.events if e["kind"] in OBSERVATIONS and not e.get("shown", True)]
            if not picked:
                return Reply("모아 둔 출력이 없다", 0)
        elif 1 <= number <= len(self.events) and self.events[number - 1]["kind"] in OBSERVATIONS:
            picked = [self.events[number - 1]]
        else:
            return Reply("E%d 는 이 세션의 관찰이 아니다" % number, 2)
        out: list[str] = []
        for event in picked:
            out.append("── " + self._title(event))
            if event.get("output"):
                out.append(event["output"])
            event["shown"] = True
        return Reply("\n".join(out), 0)

    # ── 글 대조 ──────────────────────────────────────────────────────────
    def _unseen(self, path: str, lo: int, hi: int) -> str:
        """인용한 줄이 이 세션이 본 줄인지. 다 봤으면 빈 글, 아니면 `unread`(안 봄) 나 `stale`(본 뒤 바뀜)."""
        key = self.key(path)
        seen = self.seen.get(key, set())
        if any(n not in seen for n in range(lo, hi + 1)):
            return "unread"
        return "stale" if self.sha.get(key) != sha256_file(path) else ""

    def check(self, path: str) -> Reply:
        """글 하나의 표기와 인용을 본다. 한 번 부르는 검사기가 보는 것에, 인용한 줄을 이 세션이 봤는지를 더한다."""
        if not os.path.isfile(path):
            return Reply("%s — 글 파일이 없다" % self.key(path), 2)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        doc_dir = os.path.dirname(os.path.abspath(path))
        found = C.examine(text, doc_dir, self.root)
        resolve = C.make_resolver(doc_dir, self.root)
        problems: dict[str, list[str]] = {"unread": [], "stale": []}
        for shown, (token, lo, hi) in C.find_citations(text).items():
            real = resolve(token)
            if real and 1 <= lo <= hi <= C.line_count(real):
                state = self._unseen(real, lo, hi)
                if state:
                    problems[state].append(shown)
        unread, stale = problems["unread"], problems["stale"]
        observed = found.cites.found - len(unread) - len(stale)
        event = self._add("check", file=self.key(path), sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                          anchors=len(found.anchors), out_of_range=found.notation.out_of_range,
                          off_band=found.notation.off_band, unbound=found.unbound,
                          citations={"total": found.cites.total, "found": found.cites.found, "observed": observed},
                          unread=unread, stale=stale)
        out = ["E%d check %s" % (event["n"], event["file"])] + C.render(found, self.root)
        if unread:
            out.append("  경고 — 이번 세션에서 읽지 않은 인용: %s" % ", ".join(unread))
        if stale:
            out.append("  경고 — 읽은 뒤 바뀐 파일의 인용: %s" % ", ".join(stale))
        out.append("  실재하는 인용 %d건 중 이번 세션이 본 것 %d건" % (found.cites.found, observed))
        out.append("  %s%s" % ("통과 — " if C.clean(found) and not unread and not stale else "", C.CLOSING))
        return Reply("\n".join(out), 1 if found.notation.out_of_range else 0)

    # ── 상태 ─────────────────────────────────────────────────────────────
    def status(self) -> Reply:
        pending = sum(1 for e in self.events if e["kind"] in OBSERVATIONS and not e.get("shown", True))
        return Reply("사건 %d개 · 시도 %d/%d · 안 본 출력 %d건%s" % (
            len(self.events), self.calls, self.limit, pending,
            " · 거절 %d번" % self.refused if self.refused else ""), 0)

    def handle(self, cmd: str, args: dict[str, Any]) -> Reply:
        """명령 하나를 처리한다. 잘못된 입력은 예외로 죽지 않고 종료 코드 2 로 답한다."""
        try:
            if cmd == "read":
                return self.read(args["path"], args.get("lines", ""), args.get("defer", False))
            if cmd == "grep":
                return self.grep(args["pattern"], args.get("paths", []), args.get("ignore_case", False),
                                 args.get("defer", False))
            if cmd == "run":
                return self.run(args["command"], args["cwd"], args.get("defer", False))
            if cmd == "show":
                return self.show(args.get("number"))
            if cmd == "more":
                return self.more(args["count"])
            if cmd == "check":
                return self.check(args["path"])
            if cmd == "status":
                return self.status()
        except (ValueError, KeyError, OSError, re.error) as err:
            return Reply("오류 — %s: %s" % (type(err).__name__, err), 2)
        return Reply("모르는 명령이다: %s" % cmd, 2)


# ── 상태 파일 ────────────────────────────────────────────────────────────
def session_paths(root: str) -> tuple[str, str]:
    """이 뿌리의 세션이 쓰는 상태 파일과 잠금 파일. 저장소 밖 임시 폴더에 둔다."""
    base = os.environ.get("CONFIDENCE_SESSION_DIR") or tempfile.gettempdir()
    stem = os.path.join(base, "ob-" + hashlib.sha1(os.path.realpath(root).encode("utf-8")).hexdigest()[:10])
    return stem + ".json", stem + ".lock"


def load(path: str) -> Context:
    with open(path, encoding="utf-8") as f:
        return Context.load(json.load(f))


def save(ctx: Context, path: str, private: bool = False) -> None:
    """기억을 파일로 쓴다. 쓰다 죽어도 지난 파일이 깨지지 않게 옆에 쓰고 바꿔치운다.

    `private` 면 쓴 사람만 읽는 파일로 만든다 — 상태 파일에는 읽은 줄과 명령의 출력이 그대로 든다.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    opened = os.open(path + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    with os.fdopen(opened, "w", encoding="utf-8") as f:
        json.dump(ctx.dump(), f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(path + ".tmp", path)


def finish(ctx: Context, work: str, out: Optional[str]) -> str:
    """기억을 남길 자리에 쓰고 상태 파일을 지운다. 쓴 자리를 돌려준다."""
    target = out or os.path.join(ctx.root, ".confidence", "session-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
    ctx.ended_at = now()
    save(ctx, target)
    os.remove(work)
    return target


def request(a: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    """명령줄을 `Context.handle` 이 받는 꼴로 옮긴다. 경로는 지금 폴더 기준으로 편다."""
    if a.cmd == "read":
        return "read", {"path": os.path.abspath(a.path), "lines": a.lines, "defer": a.defer}
    if a.cmd == "grep":
        return "grep", {"pattern": a.pattern, "paths": [os.path.abspath(p) for p in a.paths],
                        "ignore_case": a.ignore_case, "defer": a.defer}
    if a.cmd == "run":
        words = a.command[1:] if a.command[:1] == ["--"] else a.command
        return "run", {"command": words[0] if len(words) == 1 else shlex.join(words),
                       "cwd": os.getcwd(), "defer": a.defer}
    if a.cmd == "show":
        return "show", {"number": int(a.event.lstrip("Ee")) if a.event else None}
    if a.cmd == "check":
        return "check", {"path": os.path.abspath(a.file)}
    if a.cmd == "more":
        return "more", {"count": a.count}
    return a.cmd, {}


def call(root: str, a: argparse.Namespace) -> tuple[list[str], int]:
    """호출 하나 — 상태 파일을 읽고, 명령을 처리하고, 다시 쓴다. 돌려줄 줄들과 종료 코드를 낸다.

    동시에 부른 호출들이 같은 파일을 덮어쓰지 않게 잠금을 잡고 한다.
    """
    work, lock_path = session_paths(root)
    out: list[str] = []
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        observing = a.cmd in OBSERVATIONS
        if observing and os.path.exists(work) and time.time() - os.path.getmtime(work) > IDLE_SECONDS:
            old = load(work)
            out.append("오래 쓰지 않은 지난 세션을 %s 에 남기고 새로 시작한다" % old.key(finish(old, work, None)))
        if not os.path.exists(work) and not observing:
            return [NO_SESSION], 2
        ctx = load(work) if os.path.exists(work) else Context(root)
        if a.cmd == "end":
            pending = sum(1 for e in ctx.events if e["kind"] in OBSERVATIONS and not e.get("shown", True))
            target = finish(ctx, work, os.path.abspath(a.out) if a.out else None)
            return out + ["끝 — 기억을 %s 에 남겼다 (사건 %d개 · 시도 %d/%d)%s" % (
                ctx.key(target), len(ctx.events), ctx.calls, ctx.limit,
                " · 받지 않은 출력 %d건이 파일에 있다" % pending if pending else "")], 0
        reply = ctx.handle(*request(a))
        save(ctx, work, private=True)
        return out + [reply.text], reply.code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="읽기 · 찾기 · 실행을 대신 돌리고 그 결과를 기억해 두는 관찰 세션.")
    parser.add_argument("--root", help="저장소 뿌리. 없으면 지금 폴더가 속한 git 저장소의 뿌리")
    sub = parser.add_subparsers(dest="cmd", required=True)
    defer = "출력을 답에 싣지 않고 세션에 쌓아 둔다. `show` 로 받는다"
    p = sub.add_parser("read", help="파일을 읽는다")
    p.add_argument("path")
    p.add_argument("lines", nargs="?", default="", help="줄 또는 줄-줄. 없으면 전체")
    p.add_argument("--defer", action="store_true", help=defer)
    p = sub.add_parser("grep", help="정규식으로 찾는다")
    p.add_argument("pattern")
    p.add_argument("paths", nargs="*")
    p.add_argument("-i", "--ignore-case", action="store_true")
    p.add_argument("--defer", action="store_true", help=defer)
    p = sub.add_parser("run", help="명령을 셸로 돌린다")
    p.add_argument("--defer", action="store_true", help=defer + ". 명령보다 앞에 적는다")
    p.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("show", help="모아 둔 출력을 받는다").add_argument("event", nargs="?", help="E7 또는 7. 그 관찰 하나를 다시 받는다")
    sub.add_parser("check", help="글의 표기와 인용을 본 것과 대조한다").add_argument("file")
    sub.add_parser("more", help="사용자에게 더 받은 시도 횟수를 더한다").add_argument("count", type=int)
    sub.add_parser("status", help="세션의 상태")
    sub.add_parser("end", help="기억을 남길 자리에 옮기고 세션을 닫는다").add_argument("--out")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    a = build_parser().parse_args(argv)
    lines, code = call(os.path.realpath(a.root or C.git_root(os.getcwd())), a)
    print("\n".join(lines), file=sys.stderr if lines == [NO_SESSION] else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
