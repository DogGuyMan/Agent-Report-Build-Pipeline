"""리소스 파일의 `{{이름}}` 자리를 채운다. 자리와 값이 하나라도 어긋나면 예외다.

이름은 영문자 · 숫자 · 밑줄이다. 한 겹 중괄호와 `$` 는 글자 그대로 둔다 — 프롬프트와 템플릿에
JSON 과 환경변수 표기가 흔하다. 바꾼 값 안의 `{{…}}` 는 다시 펴지 않는다.
"""
import re
from collections.abc import Mapping

SLOT = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(ValueError):
    """템플릿의 자리와 넘긴 값이 맞지 않는다."""


def render(text: str, values: Mapping[str, str]) -> str:
    """`{{이름}}` 을 값으로 바꾼다. 값이 없는 자리 · 자리가 없는 값은 둘 다 `TemplateError`."""
    slots = set(SLOT.findall(text))
    missing = sorted(slots - set(values))
    unused = sorted(set(values) - slots)
    if missing or unused:
        raise TemplateError("값이 없는 자리 %s · 자리가 없는 값 %s" % (missing, unused))
    return SLOT.sub(lambda m: values[m.group(1)], text)


def render_file(path: str, values: Mapping[str, str]) -> str:
    """파일 하나를 UTF-8 로 읽어 `render` 한다."""
    with open(path, encoding="utf-8") as f:
        return render(f.read(), values)
