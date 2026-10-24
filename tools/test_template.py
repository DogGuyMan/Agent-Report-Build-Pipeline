from pathlib import Path

import pytest

from tools.template import TemplateError, render, render_file


def test_자리를_값으로_바꾼다():
    assert render("대상 {{repo}} · 도구 {{ root }}", {"repo": "/a", "root": "/b"}) == "대상 /a · 도구 /b"


def test_값이_없는_자리는_예외다():
    with pytest.raises(TemplateError, match="repo"):
        render("{{repo}}", {})


def test_자리가_없는_값도_예외다():
    with pytest.raises(TemplateError, match="slug"):
        render("{{repo}}", {"repo": "/a", "slug": "x"})


def test_한겹_중괄호와_달러는_건드리지_않는다():
    text = '꼴은 {"키": 레코드} · { "용어": { TermMeans } } · $REPO_ROOT/bin · {{ "따옴표" }}'
    assert render(text, {}) == text


def test_값_안의_자리는_다시_펴지_않는다():
    assert render("{{a}}", {"a": "{{b}}"}) == "{{b}}"


def test_render_file_은_UTF8_파일을_읽어_채운다(tmp_path: Path):
    p = tmp_path / "t.md"
    p.write_text("안녕 {{who}}\n", encoding="utf-8")
    assert render_file(str(p), {"who": "세계"}) == "안녕 세계\n"
