"""형 자리의 `Any` 를 0으로 막는 게이트.

`pyright` 의 strict 모드는 `Unknown` 의 전파는 잡지만 저자가 손으로 적은 `Any` 는
그냥 통과시킨다. 그래서 글자로 막는다.

`COVERED` 는 리팩터링이 진행되면 는다. 아직 `Any` 가 남은 파일을 여기 넣으면 게이트가 빨개진다.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# `Any` 를 0으로 지켜야 하는 파일.
COVERED = [
    "runner/measure.py",
    "runner/pipeline.py",
    "runner/run_mode1.py",
    "runner/mode1/context.py",
    "runner/mode1/measured.py",
    "runner/mode1/machine_stage.py",
    "runner/mode1/diff.py",
    "runner/mode1/lang.py",
    "runner/mode1/scan.py",
    "runner/mode1/graph.py",
    "runner/mode1/survey.py",
    "runner/mode1/terms.py",
    "runner/mode1/wiki.py",
    "runner/mode1/edges.py",
    "runner/mode1/resume.py",
    "runner/mode1/seal.py",
    "runner/run_mode1_5.py",
    "runner/run_mode2.py",
    "runner/run_grade.py",
    "runner/dispatch.py",
    "tools/template.py",
]

# 낱말 경계로 본다 — `Anything` 같은 이름을 잘못 잡지 않는다.
ANY = re.compile(r"\bAny\b")


def code_lines(path: str) -> list[tuple[int, str]]:
    """주석과 독스트링 줄을 뺀 나머지. 글자 검사라 완벽하지 않고 그럴 필요도 없다."""
    out: list[tuple[int, str]] = []
    in_doc = False
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            stripped = line.strip()
            quote_count = stripped.count('"""')
            if not in_doc and quote_count >= 2:
                # 한 줄 안에서 열리고 닫히는 독스트링 — 토글할 필요 없이 통째로 건너뛴다.
                continue
            if quote_count % 2 == 1:
                in_doc = not in_doc
                continue
            if in_doc or stripped.startswith("#"):
                continue
            out.append((i, line))
    return out


def test_러너_공통축에_Any_가_없다():
    hits: list[str] = []
    for path in COVERED:
        for lineno, line in code_lines(path):
            if ANY.search(line):
                hits.append("%s:%d %s" % (path, lineno, line.strip()))
    assert hits == [], "형 자리에 Any 가 남았다:\n" + "\n".join(hits)


def test_덮는_파일이_실제로_있다():
    for path in COVERED:
        assert os.path.exists(os.path.join(ROOT, path)), path


def test_산문_속_Any_는_걸리지_않는다(tmp_path):
    """독스트링과 주석의 `Any` 는 형 자리가 아니다 — 걸러야 한다."""
    p = tmp_path / "샘플.py"
    p.write_text('"""여기서 Any 를 쓰지 않는다."""\n# Any 도 주석이다\nx: int = 1\n',
                 encoding="utf-8")
    rel = os.path.relpath(p, ROOT)
    assert [l for _, l in code_lines(rel) if ANY.search(l)] == []
