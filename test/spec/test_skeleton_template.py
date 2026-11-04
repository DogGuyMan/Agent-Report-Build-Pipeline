"""보고서 뼈대 템플릿이 제자리에서 렌더되는지 — data.ts."""
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from spec.python.viz.init import writeSkeleton  # noqa: E402

DATA_TS = '''import type { ReportData } from "report-builder/types";

export const data: ReportData = {
  builderVersion: "v1",
  slug: "s",
  specName: "T `x` \\"q\\" {{b}}",
  date: "2026-01-01",
  branch: "main",
  decisions: [],
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮겨 적는다.
  //   report-term collect <plan.md> <terms-db.json>  →  (스킬이 묻는다)  →  report-term grade  →  report-term emit
  // terms.json 의 { "용어": { TermMeans, UserMentalValue } } 를
  // { id, label, short, kind, mental } 로 옮긴다. 자동 import 하지 않는다 — 이 파일은 사람이 읽는 파일이다.
  terms: [],
};
'''


def test_뼈대_data_ts_는_값만_바뀌고_나머지는_글자_그대로다(tmp_path: Path):
    writeSkeleton(str(tmp_path), "s", "2026-01-01", 'T `x` "q" {{b}}', "main", "v1")
    assert (tmp_path / "data.ts").read_text(encoding="utf-8") == DATA_TS
