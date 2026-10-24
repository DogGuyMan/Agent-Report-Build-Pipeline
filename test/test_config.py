"""원본 문서 자리 규칙과 Mode 2 모델 기본값은 config/report.toml 한 곳에서 온다 — 두 읽는 쪽이 그 파일을 본다."""
import os
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner")]

import run_mode2  # noqa: E402
from viz.init import DOC_DIRS as VIZ_DOC_DIRS  # noqa: E402


def _report_toml() -> dict[str, object]:
    with open(os.path.join(ROOT, "config", "report.toml"), "rb") as f:
        return tomllib.load(f)


def test_원본_문서_자리_규칙은_한_곳에서_온다():
    doc_dirs = _report_toml()["doc_dirs"]
    assert isinstance(doc_dirs, list)
    want = [(str(d["dir"]), str(d["pattern"])) for d in doc_dirs]
    assert [(d, p.pattern) for d, p in run_mode2.DOC_DIRS] == want
    assert [(d["dir"], d["re"].pattern) for d in VIZ_DOC_DIRS] == want
    assert [d for d, _ in want] == ["specs", "plans"]


def test_mode2_모델_기본값은_설정에서_온다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                  capsys: pytest.CaptureFixture[str]):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "2026-01-01-x-design.md").write_text("# x\n", encoding="utf-8")
    monkeypatch.setitem(run_mode2.CONFIG["models"], "mode2_agent", "설정에서-온-모델")
    assert run_mode2.main([str(tmp_path), "x", "--dry-run"]) == 0
    assert "LLM Model 설정에서-온-모델 " in capsys.readouterr().out
