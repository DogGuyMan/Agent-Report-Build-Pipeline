"""리소스와 코드를 가르는 게이트 — 긴 글은 리소스 파일에 살고, 프롬프트 선언과 파일 · 절은 1:1 이다."""
import ast
import glob
import importlib
import os
import sys
from collections.abc import Iterator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner"), os.path.join(ROOT, "machine")]

LONG_LINES = 6     # 줄바꿈이 이만큼 이상인 글(문자열 상수 · f-문자열)은 리소스로 뺀다
LONG_CHARS = 200   # 한 줄이라도 이 길이 이상이면 리소스로 뺀다
CODE_TOPS = ("runner", "viz", "machine", "tools")   # 긴 글을 찾는 폴더 — 시험 파일은 뺀다
TEMPLATE_TOPS = ("runner", "viz")   # 코드가 쓰는 템플릿이 사는 폴더 — `<폴더>/**/templates/**`
RUNNERS = ("run_mode1", "run_mode1_5", "run_mode2")   # 이 저장소에 있는 것만 import 해 단계 클래스를 모은다


def code_files(tops: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for top in tops:
        for p in glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True):
            if not os.path.basename(p).startswith("test_") and "__pycache__" not in p:
                out.append(p)
    return sorted(out)


def parse(path: str) -> ast.Module:
    with open(path, encoding="utf-8") as f:
        return ast.parse(f.read())


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                ids.add(id(b.value))
    return ids


def string_constants(tree: ast.AST) -> Iterator[ast.Constant]:
    """독스트링을 뺀 문자열 상수 노드."""
    docs = docstring_nodes(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            yield n


def texts(tree: ast.AST) -> Iterator[tuple[int, str]]:
    """잴 글을 (줄, 글) 로 — 독스트링을 뺀 문자열 상수 하나하나, 그리고 f-문자열은 글자 조각을 이은 한 덩어리."""
    for n in string_constants(tree):
        yield n.lineno, n.value
    for n in ast.walk(tree):
        if isinstance(n, ast.JoinedStr):
            yield n.lineno, "".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str))


def is_long(text: str) -> bool:
    return text.count("\n") >= LONG_LINES or len(text) >= LONG_CHARS


def template_files() -> list[str]:
    return sorted(t for top in TEMPLATE_TOPS
                  for t in glob.glob(os.path.join(ROOT, top, "**", "templates", "**", "*"), recursive=True)
                  if os.path.isfile(t))


def all_subclasses(cls: type) -> set[type]:
    out: set[type] = set()
    for c in cls.__subclasses__():
        out |= {c} | all_subclasses(c)
    return out


def is_production_class(c: type) -> bool:
    """시험 모듈(`test_*`)이 정의한 클래스는 단계 선언이 아니다. 최상위 클래스든 시험 함수 안의 지역 클래스든 모듈 이름으로 걸러진다."""
    return not c.__module__.rsplit(".", 1)[-1].startswith("test_")


def test_파이썬에_리소스로_뺄_긴_글이_없다() -> None:
    hits = sorted({"%s:%d" % (os.path.relpath(p, ROOT), line)
                   for p in code_files(CODE_TOPS) for line, text in texts(parse(p)) if is_long(text)})
    assert hits == [], "리소스 파일로 옮길 글이 코드에 있다:\n" + "\n".join(hits)


def test_프롬프트_선언과_파일_절이_1대1이다() -> None:
    for name in RUNNERS:
        if os.path.exists(os.path.join(ROOT, "runner", name + ".py")):
            importlib.import_module(name)
    import pipeline as P
    stages = sorted((c for c in all_subclasses(P.PromptResource) if is_production_class(c)),
                    key=lambda c: (c.__module__, c.__qualname__))
    declared = {os.path.normpath(os.path.join(c.prompt_dir, n)) for c in stages for n in c.prompt_names}
    on_disk: set[str] = set()
    malformed: list[str] = []
    for p in sorted(glob.glob(os.path.join(ROOT, "runner", "**", "prompts", "*.md"), recursive=True)):
        base = os.path.normpath(p[:-len(".md")])
        with open(p, encoding="utf-8") as f:
            text = f.read()
        try:
            on_disk |= {base + ("#" + sec if sec else "") for sec in P.PromptResource.sections(text)}
        except ValueError as e:
            malformed.append("%s: %s" % (os.path.relpath(p, ROOT), e))
    assert malformed == [], "절 표식이 틀린 프롬프트 파일이 있다:\n" + "\n".join(malformed)
    unread = sorted(os.path.relpath(n, ROOT) for n in on_disk - declared)
    missing = sorted(os.path.relpath(n, ROOT) for n in declared - on_disk)
    assert unread == [], "아무 단계도 읽지 않는 프롬프트 파일 · 절이 있다:\n" + "\n".join(unread)
    assert missing == [], "선언했는데 없는 프롬프트 파일 · 절이 있다:\n" + "\n".join(missing)
    strays = ["%s.%s(%r): %s" % (c.__module__, c.__qualname__, getattr(c, "name", ""), ", ".join(c.prompt_names))
              for c in stages if {n.partition("#")[0] for n in c.prompt_names} - {getattr(c, "name", "")}]
    assert strays == [], "프롬프트 파일 이름이 단계 이름과 다르다 — 단계당 한 파일이다:\n" + "\n".join(strays)


def test_템플릿_파일은_모두_코드가_부른다() -> None:
    names = {n.value for p in code_files(CODE_TOPS) for n in string_constants(parse(p))}
    templates = template_files()
    basenames = [os.path.basename(t) for t in templates]
    dups = sorted(os.path.relpath(t, ROOT) for t in templates if basenames.count(os.path.basename(t)) > 1)
    assert dups == [], "템플릿 파일 이름이 겹친다 — 이름 하나가 파일 하나를 가리켜야 한다:\n" + "\n".join(dups)
    orphans = sorted(os.path.relpath(t, ROOT) for t in templates if os.path.basename(t) not in names)
    assert orphans == [], "어느 코드의 문자열 상수에도 이름이 없는 템플릿이 있다:\n" + "\n".join(orphans)
