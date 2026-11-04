"""test_pycalls.py — AST 호출 수집기의 회귀 시험."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "codewiki", "python", "runner"), os.path.join(ROOT, "src", "codewiki", "python", "machine"),
                os.path.join(ROOT, "src", "codewiki", "python", "viz")]
import normalize as N  # noqa: E402
import pycalls as P  # noqa: E402


def _write(tmp: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


# ── 1. 이름 해소 — 이 저장소의 평평한 import 관습
FLAT = {
    "pkga/util.py": "def helper():\n    return 1\n",
    "pkgb/app.py": (
        "import sys\n"
        "sys.path.insert(0, '../pkga')\n"
        "from util import helper\n"
        "\n"
        "def run():\n"
        "    return helper()\n"
    ),
}


def test_flat_import_across_directories_is_resolved(tmp_path: Path) -> None:
    """`from util import helper` 를 `pkga.util.helper` 로 푼다 — 패키지 접두가 없어도.

    픽스처는 `sys.path` 를 조작한 뒤 평평한 이름으로 import 하는 이 저장소의 관습을 본뜬다.
    디렉토리 뿌리 이름으로 import 를 거르면 모듈을 넘는 간선이 사라진다.
    """
    _write(tmp_path, FLAT)
    d = P.collect(str(tmp_path), ["pkga", "pkgb"])
    got = {(c["caller"], c["callee"]) for c in d["calls"]}
    assert ("pkgb.app.run", "pkga.util.helper") in got


def test_builtin_and_external_calls_are_dropped(tmp_path: Path) -> None:
    """빌트인(`len`)과 저장소 밖(`json.dumps`)은 간선이 아니다 — 양끝이 다 우리 것이어야 한다."""
    _write(tmp_path, {"m/a.py": (
        "import json\n"
        "def f(xs):\n"
        "    return len(json.dumps(xs))\n"
    )})
    d = P.collect(str(tmp_path), ["m"])
    assert d["calls"] == []
    assert [s["name"] for s in d["symbols"]] == ["m.a.f"]


def test_methods_and_classes_become_symbols(tmp_path: Path) -> None:
    """클래스·메서드도 심볼이고, 메서드에서 나가는 호출도 잡는다."""
    _write(tmp_path, {"m/a.py": (
        "def top():\n    return 0\n"
        "\n"
        "class C:\n"
        "    def go(self):\n"
        "        return top()\n"
    )})
    d = P.collect(str(tmp_path), ["m"])
    kinds = {s["name"]: s["kind"] for s in d["symbols"]}
    assert kinds == {"m.a.top": "function", "m.a.C": "class", "m.a.C.go": "method"}
    assert ("m.a.C.go", "m.a.top") in {(c["caller"], c["callee"]) for c in d["calls"]}


def test_same_stem_in_two_directories_is_dropped_not_guessed(tmp_path: Path) -> None:
    """파일 이름이 겹치면 **버린다.** 잘못 이은 간선은 없는 간선보다 나쁘다."""
    _write(tmp_path, {
        "x/dup.py": "def f():\n    return 1\n",
        "y/dup.py": "def f():\n    return 2\n",
        "z/use.py": "from dup import f\n\ndef g():\n    return f()\n",
    })
    d = P.collect(str(tmp_path), ["x", "y", "z"])
    assert not [c for c in d["calls"] if c["callee"].endswith("dup.f")]


# ── 패키지 꼴 — `src/` 뿌리부터 쓴 점 경로와, `sys.path` 에 넣은 디렉토리 아래 패키지의 점 경로
PACKAGED = {
    "src/core/__init__.py": "",
    "src/core/pipeline.py": "def run():\n    return 1\n",
    "src/common/__init__.py": "",
    "src/common/python.py": "def pythonPath():\n    return 'py'\n",
    "src/cw/runner/mode1/__init__.py": "",
    "src/cw/runner/mode1/context.py": "def make():\n    return 2\n\ndef other():\n    return 3\n",
    "src/cw/runner/run.py": (
        "from core import pipeline as P\n"
        "from common.python import pythonPath\n"
        "from mode1.context import make\n"
        "import mode1.context as ctx\n"
        "\n"
        "def go():\n"
        "    P.run()\n"
        "    pythonPath()\n"
        "    make()\n"
        "    return ctx.other()\n"
    ),
}


def test_package_imports_are_resolved(tmp_path: Path) -> None:
    """import 에 쓴 점 경로가 모듈 · 패키지 점 경로의 꼬리와 하나로 맞으면 그 모듈로 푼다.

    `src/` 뿌리부터 쓴 경로(`from core import pipeline` · `from common.python import pythonPath`)와
    `sys.path` 에 넣은 디렉토리 아래 패키지 경로(`from mode1.context import make` · `import mode1.context as ctx`)가
    같은 규칙이다.
    """
    _write(tmp_path, PACKAGED)
    d = P.collect(str(tmp_path), ["src/core", "src/common", "src/cw"])
    got = {c["callee"] for c in d["calls"] if c["caller"] == "cw.runner.run.go"}
    assert got == {"core.pipeline.run", "common.python.pythonPath",
                   "cw.runner.mode1.context.make", "cw.runner.mode1.context.other"}


def test_dotted_path_matching_two_packages_is_dropped_not_guessed(tmp_path: Path) -> None:
    """점 경로의 꼬리가 두 패키지와 맞으면 **버린다** — 파일 이름이 겹칠 때와 같다."""
    _write(tmp_path, {
        "a/mode1/context.py": "def make():\n    return 1\n",
        "b/mode1/context.py": "def make():\n    return 2\n",
        "c/run.py": "from mode1.context import make\n\ndef go():\n    return make()\n",
    })
    d = P.collect(str(tmp_path), ["a", "b", "c"])
    assert [c for c in d["calls"] if c["caller"] == "c.run.go"] == []


def test_signature_is_captured(tmp_path: Path) -> None:
    """시그니처를 원문 주석 그대로 살린다 — 위키가 읽는 자리다."""
    _write(tmp_path, {"m/a.py": "def f(a: int, b: str = 'x') -> bool:\n    return True\n"})
    d = P.collect(str(tmp_path), ["m"])
    assert d["symbols"][0].get("signature") == "(a: int, b: str = 'x') -> bool"


def test_syntax_error_file_is_skipped_not_fatal(tmp_path: Path) -> None:
    """문법이 깨진 파일 하나가 수집 전체를 죽이지 않는다."""
    _write(tmp_path, {"m/ok.py": "def f():\n    return 1\n",
                      "m/broken.py": "def (((\n"})
    d = P.collect(str(tmp_path), ["m"])
    assert [s["name"] for s in d["symbols"]] == ["m.ok.f"]


# ── 2. normalize 와의 합류 — griffe 갈래에 얹힌다
def test_merge_adds_function_nodes_and_call_edges(tmp_path: Path) -> None:
    """griffe 가 못 낸 함수 노드가 들어오고, 호출이 dependency 간선이 된다."""
    _write(tmp_path, FLAT)
    calls = P.collect(str(tmp_path), ["pkga", "pkgb"])
    empty: N.GriffeDump = {}
    g, stats = N.normalize_python(empty, str(tmp_path), "test", calls=calls)
    by = {n["name"]: n for n in g["nodes"]}
    assert "pkga.util.helper" in by and "pkgb.app.run" in by
    assert by["pkga.util.helper"]["kind"] == "function"
    edge = [e for e in g["edges"] if e["kind"] == "dependency"]
    assert len(edge) == 1
    assert edge[0]["label"] == "호출"
    assert stats["호출 간선"] == 1


def test_merge_is_opt_in(tmp_path: Path) -> None:
    """calls 를 안 주면 옛 동작 그대로 — 노드도 간선도 늘지 않는다."""
    empty: N.GriffeDump = {}
    g, _ = N.normalize_python(empty, str(tmp_path), "test")
    assert g["nodes"] == [] and g["edges"] == []


def test_merge_never_makes_ownership_kinds(tmp_path: Path) -> None:
    """호출은 dependency 다. 부른다고 갖는 것이 아니므로 소유 kind 로 올리지 않는다."""
    _write(tmp_path, FLAT)
    calls = P.collect(str(tmp_path), ["pkga", "pkgb"])
    empty: N.GriffeDump = {}
    g, _ = N.normalize_python(empty, str(tmp_path), "test", calls=calls)
    assert not [e for e in g["edges"] if e["kind"] in ("composition", "aggregation")]


# ── 3. 자기호스팅 연기 시험 — 실저장소를 태워도 죽지 않는다
def test_module_path_drops_src_prefix() -> None:
    """`src/` 꼴 저장소는 그 안을 뿌리로 본다 — griffe 를 `-s <저장소>/src` 로 돌린 이름과 같아야 노드가 합쳐진다."""
    assert P.module_path("src/codewiki/python/machine/normalize.py") == "codewiki.python.machine.normalize"
    assert P.module_path("machine/normalize.py") == "machine.normalize"
    assert P.module_path("tools/doctor.py") == "tools.doctor"


def test_selfhost_smoke() -> None:
    """이 저장소를 실제로 훑는다. 수치는 주장하지 않고 '판이 커졌다' 만 본다."""
    d = P.collect(ROOT, ["src", "tools", "test"])   # 본체와 시험을 함께
    assert len(d["symbols"]) > 400
    assert len(d["calls"]) > 300
    # 모듈을 넘는 호출이 실제로 잡혀야 한다 — 여기가 0 이면 이름 해소가 깨진 것이다.
    cross = [c for c in d["calls"]
             if c["caller"].rsplit(".", 1)[0] != c["callee"].rsplit(".", 1)[0]]
    assert len(cross) > 100
    # `src/` 뿌리부터 쓴 패키지 꼴 import(`from core import pipeline`)로 이어진 간선이 있어야 한다.
    assert [c for c in d["calls"]
            if c["callee"].startswith("core.") and not c["caller"].startswith("core.")]


def test_cli_runs_end_to_end(tmp_path: Path) -> None:
    """명령줄로도 돌고 JSON 을 낸다."""
    _write(tmp_path, FLAT)
    out = tmp_path / "pc.json"
    r = subprocess.run([sys.executable, os.path.join(os.path.join(ROOT, "src", "codewiki", "python", "machine"), "pycalls.py"),
                        "pkga", "pkgb", "--repo", str(tmp_path), "-o", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["tool"].startswith("pycalls")
    assert d["calls"]


def test_signature_covers_star_and_kwargs(tmp_path: Path) -> None:
    """가변·키워드 전용·`**kw` 를 빠뜨리지 않는다. 키워드 전용 앞의 `*` 도 살린다."""
    _write(tmp_path, {"m/a.py": (
        "def f(a, /, b, *args, c: int = 1, **kw) -> None:\n    pass\n"
        "def g(x, *, y=2):\n    pass\n"
    )})
    d = P.collect(str(tmp_path), ["m"])
    sig = {s["name"]: s.get("signature") for s in d["symbols"]}
    assert sig["m.a.f"] == "(a, b, *args, c: int = 1, **kw) -> None"
    assert sig["m.a.g"] == "(x, *, y=2)"
