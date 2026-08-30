#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='clangd_refs.py']"/>
# clangd 라는 언어 서버에게 직접 말을 거는 얇은 통신 계층.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""clangd 에 stdio JSON-RPC 로 직접 말해 역방향 참조를 받아온다 (E6).

E7 제약 — 산출물은 엔진 중립이다. LSP 의 uri/range 를 그대로 내보내지 않고
{repo 상대경로, line, col} 로 정규화해서 낸다.
"""
import json, os, subprocess, threading, time
from typing import IO, Any
from urllib.parse import urlparse, unquote


# <include file="machine/comments.xml" path="//term[@id='machine.clangd_refs.Clangd']"/>
# clangd 언어 서버 프로세스 하나를 감싸서 다루기 쉽게 만든 상자다.
# 쓰는 것: subprocess.Popen, threading.Thread · 쓰이는 곳: machine.reverse_refs.main
class Clangd:
    def __init__(self, root: str, compdb_dir: str,
                 binary: str = "clangd", background_index: bool = True) -> None:
        self.root = os.path.abspath(root)
        argv = [binary, f"--compile-commands-dir={compdb_dir}", "--log=error"]
        if background_index:
            argv.append("--background-index")
        self.proc: subprocess.Popen[bytes] = subprocess.Popen(
            argv, cwd=self.root,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 파이프 셋을 여기서 한 번만 좁혀 붙들어 둔다. 위에서 셋 다 subprocess.PIPE 로
        # 고정해 넘겼으므로 None 이 될 수 없다.
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        assert self.proc.stderr is not None
        self._stdin: IO[bytes] = self.proc.stdin
        self._stdout: IO[bytes] = self.proc.stdout
        self._stderr: IO[bytes] = self.proc.stderr
        self._id = 0
        self._pending: dict[int, dict[str, Any]] = {}
        self._notifications: list[dict[str, Any]] = []   # 서버가 보낸 알림 전량 (관찰용)
        self._progress: dict[str, str] = {}              # token -> 마지막 kind
        self._lock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()

    # ---- 프레이밍: Content-Length 헤더 + CRLF CRLF + 본문 ----
    def _send(self, obj: dict[str, Any]) -> None:
        body = json.dumps(obj).encode()
        self._stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self._stdin.flush()

    def _reader(self) -> None:
        f = self._stdout
        while True:
            length: int | None = None
            while True:
                line = f.readline()
                if not line:
                    return
                line = line.strip()
                if not line:
                    break
                if line.lower().startswith(b"content-length:"):
                    length = int(line.split(b":")[1])
            if length is None:
                continue
            msg: dict[str, Any] = json.loads(f.read(length))
            if "id" in msg and ("result" in msg or "error" in msg):
                with self._lock:
                    self._pending[msg["id"]] = msg
            elif "method" in msg and "id" in msg:
                # 서버->클라이언트 요청. 응답하지 않으면 clangd 가 진행을 멈춘다.
                self._send({"jsonrpc": "2.0", "id": msg["id"], "result": None})
                with self._lock:
                    self._notifications.append(msg)
            elif "method" in msg:
                with self._lock:
                    self._notifications.append(msg)
                    if msg["method"] == "$/progress":
                        pr = msg.get("params", {})
                        val = pr.get("value", {})
                        if "kind" in val:
                            self._progress[str(pr.get("token"))] = val["kind"]

    def _drain_stderr(self) -> None:
        for _ in iter(self._stderr.readline, b""):
            pass

    def request(self, method: str, params: Any, timeout: float = 120) -> dict[str, Any]:
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if rid in self._pending:
                    return self._pending.pop(rid)
            time.sleep(0.01)
        raise TimeoutError(f"{method} 가 {timeout}s 안에 응답하지 않았다")

    def notify(self, method: str, params: Any) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    # ---- 수명 ----
    def initialize(self) -> dict[str, Any]:
        r = self.request("initialize", {
            "processId": os.getpid(),
            "rootUri": "file://" + self.root,
            "capabilities": {
                "textDocument": {"references": {"dynamicRegistration": False}},
                # 이것을 켜야 clangd 가 $/progress 로 색인 진행을 알려준다.
                "window": {"workDoneProgress": True},
            },
        })
        self.notify("initialized", {})
        return r

    def did_open(self, rel: str) -> None:
        path = os.path.join(self.root, rel)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        self.notify("textDocument/didOpen", {"textDocument": {
            "uri": "file://" + path, "languageId": "cpp", "version": 1, "text": text}})

    def references(self, rel: str, line: int, col: int,
                   include_decl: bool = True) -> dict[str, Any]:
        """line/col 은 clang-uml 과 같은 1-based 로 받는다. LSP 는 0-based 라 여기서 변환한다."""
        path = os.path.join(self.root, rel)
        r = self.request("textDocument/references", {
            "textDocument": {"uri": "file://" + path},
            "position": {"line": line - 1, "character": col - 1},
            "context": {"includeDeclaration": include_decl},
        })
        return r

    def shutdown(self) -> None:
        try:
            self.request("shutdown", None, timeout=10)
            self.notify("exit", None)
        except Exception:
            pass
        self.proc.terminate()

    # ---- 관찰 / 색인 완료 판정 ----
    def notifications(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._notifications)

    def progress_state(self) -> dict[str, str]:
        with self._lock:
            return dict(self._progress)

    def index_idle(self) -> bool:
        """진행 중인(begin/report 상태로 남은) progress 토큰이 하나도 없으면 idle."""
        with self._lock:
            return all(k == "end" for k in self._progress.values())

    def wait_for_index(self, timeout: float = 600, settle: float = 2.0,
                       poll: float = 0.25) -> tuple[bool, float]:
        """색인이 시작됐다가 전부 end 로 끝날 때까지 기다린다. (완료했나, 걸린 초).

        settle 은 '아직 시작도 안 한' 상태와 '이미 끝난' 상태를 가르는 유예다.
        begin 이 한 번도 안 왔는데 idle 이라고 판정하면 콜드 상태에서 오답을 낸다.
        """
        t0 = time.time()
        seen_any = False
        last_change = time.time()
        prev: dict[str, str] | None = None
        while time.time() - t0 < timeout:
            st = self.progress_state()
            if st:
                seen_any = True
            if st != prev:
                prev, last_change = st, time.time()
            if seen_any and self.index_idle() and time.time() - last_change >= settle:
                return True, time.time() - t0
            if not seen_any and time.time() - t0 >= settle * 4:
                return False, time.time() - t0     # progress 가 아예 안 온다
            time.sleep(poll)
        return False, time.time() - t0


# <include file="machine/comments.xml" path="//term[@id='machine.clangd_refs.to_repo_relative']"/>
# clangd 가 돌려준 file:// URI 를 저장소 기준 상대경로 문자열로 바꿔주는 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.reverse_refs.main
def to_repo_relative(uri: str, root: str) -> str:
    p = unquote(urlparse(uri).path)
    return os.path.relpath(p, root)
