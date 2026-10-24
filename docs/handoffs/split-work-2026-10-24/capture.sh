#!/bin/bash
# capture.sh <저장소> <출력폴더> — 파이썬 글 + DOT 둘 + 보고서 HTML 하나
set -e
REPO="$1"; OUT="$2"
TOOLS_ROOT="${TOOLS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
"$REPO/.venv/bin/python" "$TOOLS_ROOT/split-work/capture.py" "$REPO" "$OUT" "$TOOLS_ROOT/split-work/fixture-shards"
"$REPO/.venv/bin/python" "$REPO/viz/render_modules.py" "$REPO/out/codegraph-raw/codegraph.json" -o "$OUT/modules" >/dev/null
"$REPO/.venv/bin/python" "$REPO/viz/render_classes.py" "$REPO/out/codegraph-raw/codegraph.json" --module machine -o "$OUT/classes" >/dev/null 2>&1 || test -s "$OUT/classes.dot"
rm -f "$OUT"/modules.svg "$OUT"/modules.png "$OUT"/classes.svg "$OUT"/classes.png
( cd "$REPO/docs/superpowers/specs/runner-stage-machine" && "$REPO/bin/report-spec" build >/dev/null && cp out/report.html "$OUT/report.html" )
