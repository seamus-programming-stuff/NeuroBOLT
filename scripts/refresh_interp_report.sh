#!/bin/bash
# Copy the interpretability results from M3 and rebuild the tables and figures (run locally, from the repo root):
#   PY=/c/Users/Seamus/anaconda3/envs/neurobolt/python.exe bash scripts/refresh_interp_report.sh
set -eo pipefail
PY="${PY:-python}"
DATA=reports/interpretability/data
mkdir -p "$DATA/raw"
REMOTE=/scratch/hz18/stay0060/NeuroBOLT/checkpoints/interp

ssh -o BatchMode=yes m3 "cd $REMOTE && for d in cv_A cv_B cv_C cv_D cv_E; do if [ -f \$d/scores.csv ]; then tail -n +2 \$d/scores.csv; fi; done" >"$DATA/cv_body.csv"
ssh -o BatchMode=yes m3 "head -1 $REMOTE/cv_A/scores.csv" | cat - "$DATA/cv_body.csv" > "$DATA/cv_scores.csv" && rm "$DATA/cv_body.csv"
fetch() { scp -q "m3:$REMOTE/$1" "$DATA/$2" 2>/dev/null || echo "not yet: $1"; }
fetch cv_A/predictions_eeg_full.npz raw/predictions_eeg_full.npz
fetch nonlinear/scores.csv nonlinear_scores.csv
fetch attribution/permutation.csv attribution_permutation.csv
fetch attribution/surrogate.csv attribution_surrogate.csv
fetch maps/maps.npz maps.npz
fetch nonlinear_loso/scores.csv nonlinear_loso_scores.csv
fetch tsmodel/scores.csv tsmodel_scores.csv
fetch tsmodel/filters.csv tsmodel_filters.csv
fetch personal/personal.csv personal.csv
fetch personal/scan_physiology.csv scan_physiology.csv
fetch hammerstein/scores.csv hammerstein_scores.csv
fetch hammerstein/components.npz hammerstein_components.npz
"$PY" -X utf8 scripts/interp_report.py --data "$DATA" --out reports/interpretability
