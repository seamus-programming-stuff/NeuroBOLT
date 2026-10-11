#!/bin/bash
# Rebuild the hypothesis-test report from the latest M3 results (run locally, from the repo root):
#   bash scripts/refresh_hypotheses_report.sh "<status line>"
# Collects aligned scores on M3, downloads them to reports/hypotheses/runs_aligned.csv, redraws
# the overview chart and rebuilds the markdown report and web page. Publishing the page and
# committing stay manual.
set -eo pipefail

STATUS="${1:?Pass a one-line status note}"
PY="${PY:-python}"
OUT=reports/hypotheses

ssh -o BatchMode=yes m3 'cd /projects/hz18/stay0060/NeuroBOLT && source scripts/m3_env.sh >/dev/null &&
    activate_neurobolt >/dev/null 2>&1 &&
    python scripts/collect_hypotheses.py --root "$M3_OUT/hypotheses" --aligned >/dev/null &&
    cat "$M3_OUT/hypotheses/runs_aligned.csv"' > "$OUT/runs_aligned.csv"

"$PY" -X utf8 scripts/plot_hypotheses.py --runs "$OUT/runs_aligned.csv" --out "$OUT"
(cd scripts && "$PY" -X utf8 build_hypotheses_report.py --runs "../$OUT/runs_aligned.csv" --status "$STATUS")
