"""proc.py — 자식 프로세스 하나를 돌린다. 죽으면 그 종료 코드로 끝내고, 실패 기록 자리를 받았으면 그 전에 기록을 남긴다. prep 과 derive 가 함께 쓴다."""
import subprocess
import sys
from collections import deque
from typing import Optional

from codewiki.python.machine.jsonio import write_json_atomic

TAIL = 40


def run(step: str, cmd: str, args: list[str], cwd: Optional[str] = None, failure_path: Optional[str] = None) -> None:
    """stderr 를 화면에 흘리면서 끝 40줄을 쥔다. 종료 코드가 0 이 아니면 그 코드로 끝내고, `failure_path` 가 있으면 그 전에 수집 실패 기록을 쓴다."""
    proc = subprocess.Popen([cmd] + args, cwd=cwd, stderr=subprocess.PIPE, text=True, errors="replace")
    tail: deque[str] = deque(maxlen=TAIL)
    assert proc.stderr is not None
    for line in proc.stderr:
        sys.stderr.write(line)
        tail.append(line.rstrip("\n"))
    rc = proc.wait()
    if rc != 0:
        print(f"실패 — {step}: {cmd} {' '.join(args)}", file=sys.stderr)
        if failure_path:
            write_json_atomic(failure_path, {"status": "failed", "step": step, "argv": [cmd] + args,
                                             "returncode": rc, "stderr_tail": list(tail)}, indent=1)
        sys.exit(rc if rc else 1)
