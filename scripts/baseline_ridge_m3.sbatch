#!/bin/bash
# CPU-only band-power ridge baselines on the inter-subject split. Each run writes an arm next to
# the GPU hypothesis arms, so collect_hypotheses.py compares them on the same scans.
# Submit from the repo root, e.g.:
#   ARM=ridge_bandpower                                   sbatch scripts/baseline_ridge_m3.sbatch
#   ARM=ridge_fine_w32 EXTRA="--bands fine --window-sec 32 --sub-windows 8" sbatch scripts/baseline_ridge_m3.sbatch
#SBATCH --job-name=nb-ridge
#SBATCH --partition=comp
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=slurm_logs/ridge-%x-%j.out
#SBATCH --error=slurm_logs/ridge-%x-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

ARM="${ARM:-ridge_bandpower}"
echo "arm=${ARM} extra=${EXTRA:-none}"
# EXTRA is deliberately unquoted so it splits into separate flags
python scripts/baseline_ridge.py \
    --dataset-root "${M3_DATA}/" \
    --split-sheet "${M3_REPO}/scan_split_example.xlsx" \
    --out "${M3_OUT}/hypotheses/${ARM}" \
    ${EXTRA:-}
