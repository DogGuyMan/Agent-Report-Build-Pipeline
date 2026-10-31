import os
import subprocess
import sys
from pathlib import Path

import pytest
from viz.init import parseSpecFilename, findSimilar, DOC_DIRS

def test_parse_spec_filename_splits_date_and_slug():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md") == {
        "date": "2026-07-27", "slug": "geometry-winding-ownership"
    }

def test_parse_spec_filename_handles_many_hyphens():
    assert parseSpecFilename("2026-05-20-sp1-shader-program-resource-consolidation-design.md") == {
        "date": "2026-05-20", "slug": "sp1-shader-program-resource-consolidation"
    }

def test_parse_spec_filename_null_if_not_ending_with_design():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-before.svg") is None
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design-review.html") is None

def test_parse_spec_filename_null_if_not_date():
    assert parseSpecFilename("26-7-27-my-topic-design.md") is None
    assert parseSpecFilename("not-a-date-my-topic-design.md") is None

def test_parse_spec_filename_null_for_unrelated_files():
    assert parseSpecFilename("README.md") is None
    assert parseSpecFilename("data.ts") is None

def test_doc_dirs_has_specs_and_plans():
    assert [d["dir"] for d in DOC_DIRS] == ["specs", "plans"]

def test_plans_matched_by_date_and_slug_without_suffix():
    assert parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "plans") == {
        "date": "2026-08-30", "slug": "symbol-resolution-survey"
    }

def test_plans_convention_does_not_work_for_specs():
    assert parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "specs") is None

def test_specs_convention_works_in_plans_if_filename_matches():
    assert parseSpecFilename("2026-08-30-foo-design.md", "plans") == {
        "date": "2026-08-30", "slug": "foo-design"
    }

def test_parse_spec_filename_defaults_to_specs():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md") == {
        "date": "2026-07-27", "slug": "geometry-winding-ownership"
    }

def test_plans_null_if_not_date():
    assert parseSpecFilename("README.md", "plans") is None
    assert parseSpecFilename("not-a-date-topic.md", "plans") is None

def test_find_similar_proposes_candidates_for_typo():
    candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"]
    assert findSimilar("geometry-winding-ownershp", candidates) == ["geometry-winding-ownership"]

def test_find_similar_finds_substrings():
    candidates = ["geometry-winding-ownership"]
    assert findSimilar("geometry-winding", candidates) == ["geometry-winding-ownership"]

def test_find_similar_returns_empty_for_unrelated():
    candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"]
    assert findSimilar("totally-unrelated-topic", candidates) == []


# ── 봉인 상태 한 줄 — 판정만 하고 막지 않는다 ─────────────────────────────
STATUS = "Mode 1 봉인 — 없음"
INIT_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viz", "init.py")


def project(tmp_path: Path) -> Path:
    """`specs/` 에 원본 문서 하나가 있는 git 저장소."""
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "2026-01-01-x-design.md").write_text("# X\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    return tmp_path


def run_init(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, INIT_PY, *args], cwd=cwd, capture_output=True, text=True)


def test_mode_one_status_는_한_줄을_돌려준다(tmp_path: Path):
    from viz.init import modeOneStatus
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    assert modeOneStatus(sys.executable, str(tmp_path)) == STATUS


def test_mode_one_status_는_evidence_가_답하지_않아도_글을_돌려준다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import viz.init as I
    monkeypatch.setattr(I, "EVIDENCE", str(tmp_path / "없는-파일.py"))
    assert "상태를 알 수 없다" in I.modeOneStatus(sys.executable, str(tmp_path))


def test_repo_top_level_은_git_밖이면_cwd_를_돌려준다(tmp_path: Path):
    from viz.init import repoTopLevel
    assert repoTopLevel(str(tmp_path)) == str(tmp_path)


def test_repo_top_level_은_하위_폴더에서_최상위를_돌려준다(tmp_path: Path):
    from viz.init import repoTopLevel
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert os.path.realpath(repoTopLevel(str(tmp_path / "a" / "b"))) == os.path.realpath(str(tmp_path))


def test_init_은_상태를_찍고_막지_않는다(tmp_path: Path):
    repo = project(tmp_path)
    r = run_init(repo, "x")
    assert r.returncode == 0 and STATUS in r.stdout
    assert (repo / "specs" / "x" / "data.ts").exists()


def test_init_은_이어_쓰기에서도_상태를_찍는다(tmp_path: Path):
    repo = project(tmp_path)
    (repo / "specs" / "x").mkdir()
    (repo / "specs" / "x" / "data.ts").write_text('builderVersion: "v1"\n', encoding="utf-8")
    r = run_init(repo, "x")
    assert r.returncode == 0 and STATUS in r.stdout and "기존 작업 파일이 있다" in r.stdout


def test_init_은_목록만_보일_때도_상태를_찍고_종료_코드를_바꾸지_않는다(tmp_path: Path):
    repo = project(tmp_path)
    r = run_init(repo)
    assert r.returncode == 1 and STATUS in r.stdout and "보고서가 없는 문서" in r.stdout


def test_init_은_원본이_없어_거부할_때도_상태를_찍는다(tmp_path: Path):
    repo = project(tmp_path)
    r = run_init(repo, "없는-slug")
    assert r.returncode == 1 and STATUS in r.stdout and "에러" in r.stderr
