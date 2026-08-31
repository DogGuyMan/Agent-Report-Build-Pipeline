import pytest
from viz.check import countScripts, linkIntegrity, versionMatch

def test_countScripts_allows_up_to_one():
    assert countScripts("<html></html>")["ok"] is True
    assert countScripts("<script>a</script>")["ok"] is True
    assert countScripts("<script>a</script><script>b</script>")["ok"] is False

def test_countScripts_returns_count():
    assert countScripts("<script>a</script><script>b</script>")["count"] == 2

def test_linkIntegrity_catches_missing_section():
    r = linkIntegrity(["D0", "D1", "D2"], '<Section title="D0 — 가">\n<Section title="D1 — 나">')
    assert r["ok"] is False
    assert r["missingSections"] == ["D2"]

def test_linkIntegrity_catches_orphan_section():
    r = linkIntegrity(["D0"], '<Section title="D0 — 가">\n<Section title="D9 — 유령">')
    assert r["ok"] is False
    assert r["orphanSections"] == ["D9"]

def test_linkIntegrity_passes_when_match():
    r = linkIntegrity(["D0", "D1"], '<Section title="D0 — 가">\n<Section title="D1 — 나">')
    assert r["ok"] is True

def test_linkIntegrity_passes_when_both_empty():
    assert linkIntegrity([], "")["ok"] is True

def test_versionMatch_warns_on_mismatch():
    r = versionMatch("v1", "v2")
    assert r["ok"] is True
    assert r["warn"] is True

def test_versionMatch_no_warning_when_match():
    assert versionMatch("v2", "v2") == {"ok": True, "warn": False}
