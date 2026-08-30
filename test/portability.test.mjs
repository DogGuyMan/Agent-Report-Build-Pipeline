import { test } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { pythonCandidates, pythonPath } from "../tools/python.mjs";
import { line } from "../tools/doctor.mjs";

test("pythonCandidates 는 REPORT_PYTHON 을 가장 앞에 둔다", () => {
  const c = pythonCandidates("/r", "darwin", { REPORT_PYTHON: "/opt/py" });
  assert.equal(c[0], "/opt/py");
});

test("pythonCandidates 는 POSIX 에서 .venv/bin 을 본다", () => {
  const c = pythonCandidates("/r", "linux", {});
  assert.deepEqual(c.slice(0, 2), [join("/r", ".venv/bin/python3"), join("/r", ".venv/bin/python")]);
});

test("pythonCandidates 는 윈도우에서 .venv/Scripts 를 본다", () => {
  const c = pythonCandidates("/r", "win32", {});
  assert.deepEqual(c.slice(0, 2), [join("/r", ".venv/Scripts/python.exe"), join("/r", ".venv/Scripts/python")]);
});

test("pythonCandidates 는 마지막에 PATH 이름을 남긴다 — .venv 가 없는 기계", () => {
  const c = pythonCandidates("/r", "linux", {});
  assert.deepEqual(c.slice(-2), ["python3", "python"]);
});

test("pythonPath 는 없는 .venv 를 건너뛰고 PATH 이름을 낸다", () => {
  assert.equal(pythonPath("/절대로/없는/저장소", "linux", {}), "python3");
});

test("line 은 필수인데 없으면 '없음' 을 낸다", () => {
  assert.match(line("dot", null, true), /없음/);
  assert.match(line("dot", null, false), /선택/);
  assert.match(line("dot", "graphviz 15", true), /OK/);
});
