#!/bin/bash
# Copy the ds006040 external-validation and arousal-monitor results from M3 and rebuild tables and figures:
#   PY=/c/Users/Seamus/anaconda3/envs/neurobolt/python.exe bash scripts/refresh_ext_report.sh
set -eo pipefail
PY="${PY:-python}"
DATA=reports/external/data
mkdir -p "$DATA"
REMOTE=/scratch/hz18/stay0060/NeuroBOLT/checkpoints/ext
fetch() { scp -q "m3:$REMOTE/$1" "$DATA/$2" 2>/dev/null || echo "not yet: $1"; }
fetch transfer/transfer.csv transfer.csv
fetch transfer/mismatched_null.csv mismatched_null.csv
fetch transfer/coupling_ext.npz coupling_ext.npz
fetch transfer/vu_model_full.npz vu_model_full.npz
fetch transfer/vu_model_bands60.npz vu_model_bands60.npz
ssh -o BatchMode=yes m3 "cd $REMOTE/neurobolt 2>/dev/null && f=\$(ls neurobolt_*.csv 2>/dev/null | head -1); if [ -n \"\$f\" ]; then head -1 \$f; for g in neurobolt_*.csv; do tail -n +2 \$g; done; fi" > "$DATA/neurobolt.csv"
[ -s "$DATA/neurobolt.csv" ] || rm -f "$DATA/neurobolt.csv"
ssh -o BatchMode=yes m3 "cd $REMOTE/monitor 2>/dev/null && f=\$(ls monitor_runs_*.csv 2>/dev/null | head -1); if [ -n \"\$f\" ]; then head -1 \$f; for g in monitor_runs_*.csv; do tail -n +2 \$g; done; fi" > "$DATA/monitor_runs.csv"
[ -s "$DATA/monitor_runs.csv" ] || rm -f "$DATA/monitor_runs.csv"
ssh -o BatchMode=yes m3 "cd $REMOTE/monitor 2>/dev/null && python3 -c 'import json,glob; d={}; [d.update(json.load(open(f))) for f in sorted(glob.glob(\"demo_*.json\"))]; print(json.dumps(d))'" > "$DATA/demo.json" || true
[ -s "$DATA/demo.json" ] || rm -f "$DATA/demo.json"
"$PY" -X utf8 scripts/ext_report.py --data "$DATA" --vu-maps reports/interpretability/data/maps.npz --out reports/external
