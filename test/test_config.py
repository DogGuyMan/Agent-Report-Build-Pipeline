"""원본 문서 자리 규칙은 config/report.toml 한 곳에서 온다 — 두 읽는 쪽이 같은 것을 본다."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "runner")]

import run_mode2  # noqa: E402
from viz.init import DOC_DIRS as VIZ_DOC_DIRS  # noqa: E402


def test_원본_문서_자리_규칙은_한_곳에서_온다():
    assert [(d, p.pattern) for d, p in run_mode2.DOC_DIRS] == \
        [(d["dir"], d["re"].pattern) for d in VIZ_DOC_DIRS]
    assert [d for d, _ in run_mode2.DOC_DIRS] == ["specs", "plans"]


def test_mode2_모델_기본값은_설정에서_온다():
    assert run_mode2.CONFIG["models"]["mode2_agent"] == "opus"
