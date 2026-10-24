"""리소스와 코드를 가르는 게이트 — 긴 글은 리소스 파일에 살고, 프롬프트 선언과 파일 · 절은 1:1 이다."""
import ast
import glob
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner"), os.path.join(ROOT, "machine")]

LONG_LINES = 6     # 줄바꿈이 이만큼 이상인 글 상수는 리소스로 뺀다
LONG_CHARS = 200   # 한 줄이라도 이 길이 이상이면 리소스로 뺀다
RUNNERS = ("run_mode1", "run_mode1_5", "run_mode2")   # 이 저장소에 있는 것만 import 해 단계 클래스를 모은다


def code_files() -> list[str]:
    out: list[str] = []
    for top in ("runner", "viz"):
        for p in glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True):
            if not os.path.basename(p).startswith("test_") and "__pycache__" not in p:
                out.append(p)
    return sorted(out)


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                ids.add(id(b.value))
    return ids


def all_subclasses(cls: type) -> set[type]:
    out: set[type] = set()
    for c in cls.__subclasses__():
        out |= {c} | all_subclasses(c)
    return out


def is_production_class(c: type) -> bool:
    """시험 함수 안에서 정의한 클래스나 시험 모듈의 클래스는 단계 선언이 아니다."""
    return ("<locals>" not in c.__qualname__
            and not c.__module__.startswith("test_")
            and not c.__module__.rsplit(".", 1)[-1].startswith("test_"))


def test_파이썬에_리소스로_뺄_긴_글이_없다() -> None:
    hits: list[str] = []
    for p in code_files():
        with open(p, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        docs = docstring_nodes(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                if n.value.count("\n") >= LONG_LINES or len(n.value) >= LONG_CHARS:
                    hits.append("%s:%d" % (os.path.relpath(p, ROOT), n.lineno))
    assert hits == [], "리소스 파일로 옮길 글이 코드에 있다:\n" + "\n".join(hits)


def test_프롬프트_선언과_파일_절이_1대1이다() -> None:
    for name in RUNNERS:
        if os.path.exists(os.path.join(ROOT, "runner", name + ".py")):
            importlib.import_module(name)
    import pipeline as P
    declared = {os.path.normpath(os.path.join(c.prompt_dir, n))
                for c in all_subclasses(P.PromptResource) if is_production_class(c)
                for n in getattr(c, "prompt_names", ())}
    on_disk: set[str] = set()
    for p in glob.glob(os.path.join(ROOT, "runner", "**", "prompts", "*.md"), recursive=True):
        base = os.path.normpath(p[:-len(".md")])
        with open(p, encoding="utf-8") as f:
            for sec in P.PromptResource.sections(f.read()):
                on_disk.add(base + ("#" + sec if sec else ""))
    assert sorted(on_disk - declared) == [], "아무 단계도 읽지 않는 프롬프트 파일 · 절이 있다"
    assert sorted(declared - on_disk) == [], "선언했는데 없는 프롬프트 파일 · 절이 있다"


def test_템플릿_파일은_모두_코드가_부른다() -> None:
    sources = ""
    for p in code_files():
        with open(p, encoding="utf-8") as f:
            sources += f.read()
    templates = [t for top in ("runner", "viz")
                 for t in glob.glob(os.path.join(ROOT, top, "**", "templates", "**", "*"), recursive=True)
                 if os.path.isfile(t)]
    orphans = sorted(os.path.relpath(t, ROOT) for t in templates if os.path.basename(t) not in sources)
    assert orphans == [], "아무도 부르지 않는 템플릿이 있다:\n" + "\n".join(orphans)
