#!/usr/bin/env python3
"""언어 서버를 띄워 `initialize` 응답의 호출 · 타입 계층 선언을 읽는다. 저장소는 열지 않는다.

    python3 lsp_caps.py
"""
import json
import subprocess

SERVERS = (["clangd"], ["pyright-langserver", "--stdio"])
KEYS = ("documentSymbolProvider", "callHierarchyProvider", "typeHierarchyProvider",
        "referencesProvider", "implementationProvider")


def read(p: subprocess.Popen) -> dict:
    n = 0
    while True:
        line = p.stdout.readline().strip()
        if not line:
            break
        if line.lower().startswith(b"content-length"):
            n = int(line.split(b":")[1])
    return json.loads(p.stdout.read(n))


def capabilities(argv: list[str]) -> dict:
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    params = {"processId": None, "rootUri": None, "capabilities": {}}
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params}).encode()
    p.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    p.stdin.flush()
    # 응답 앞에 서버가 보내는 알림이 올 수 있어 id 로 응답을 가른다.
    while True:
        reply = read(p)
        if reply.get("id") == 1:
            break
    p.kill()
    return reply["result"]["capabilities"]


if __name__ == "__main__":
    for argv in SERVERS:
        caps = capabilities(argv)
        print(argv[0], {k: caps.get(k, "(없음)") for k in KEYS})
