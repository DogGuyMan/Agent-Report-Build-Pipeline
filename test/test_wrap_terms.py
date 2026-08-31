import pytest
import re
from viz.wrap_terms import wrapTerms, termPattern

def ref(id: str) -> str:
    return f'<span class="term-ref" tabindex="0">{id}<span class="term-card">뜻</span></span>'

def refs(*ids) -> dict:
    return {id: ref(id) for id in ids}

def test_wrapTerms_wraps_all_occurrences():
    out = wrapTerms("<p>M1 은 M1 이다. calls[] 도.</p>", refs("M1", "calls[]"))
    assert len(re.findall(r'class="term-ref"', out)) == 3
    assert ref("calls[]") in out

def test_wrapTerms_does_not_touch_already_wrapped():
    html = f'<p>{ref("M1")} 과 <span class="term-card">M1</span></p>'
    assert wrapTerms(html, refs("M1")) == html

def test_wrapTerms_skips_protected_tags():
    html = '<span class="mono">M1</span><code>M1</code><pre>M1</pre><h2>M1</h2><th>M1</th><summary>M1</summary><svg><text>M1</text></svg><script>var M1=1</script>'
    assert wrapTerms(html, refs("M1")) == html

def test_wrapTerms_skips_protected_blocks():
    html = '<div class="card term-groups"><td class="mono">M1</td><td>M1 뜻</td></div><div class="term-graph" data-terms="[M1]"></div><div class="svg-wrap">M1</div>'
    assert wrapTerms(html, refs("M1")) == html

def test_wrapTerms_matches_longest_id_first():
    out = wrapTerms("<p>git blob SHA 와 git</p>", refs("git", "git blob SHA"))
    assert ref("git blob SHA") in out
    assert len(re.findall(r'class="term-ref"', out)) == 2

def opens(out: str, id: str) -> int:
    return len(re.findall(rf'class="term-ref" tabindex="0">{re.escape(id)}<', out))

def test_wrapTerms_word_boundaries():
    out = wrapTerms("<p>M10 M1x edges[]x 모듈을 모듈</p>", refs("M1", "edges[]", "모듈"))
    assert opens(out, "M1") == 0
    assert opens(out, "edges[]") == 0
    assert opens(out, "모듈") == 2

def test_wrapTerms_idempotent():
    html = '<a title="M1" data-x="M1">M1</a>'
    once = wrapTerms(html, refs("M1"))
    assert once.startswith('<a title="M1" data-x="M1">')
    assert wrapTerms(once, refs("M1")) == once

def test_termPattern_null_on_empty():
    assert termPattern([]) is None
