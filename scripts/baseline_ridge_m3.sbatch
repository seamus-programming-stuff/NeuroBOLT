#!/bin/bash
# CPU-only band-power ridge baseline on the inter-subject split; writes the arm ridge_bandpower
# next to the GPU hypothesis arms so collect_hypotheses.py compares them on the same scans.
# Submit from the repo root with: sbatch scripts/baseline_ridge_m3.sbatch
#SBATCH --job-name=nb-ridge
#SBATCH --partition=comp
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=slurm_logs/ridge-%j.out
#SBATCH --error=slurm_logs/ridge-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

python scripts/baseline_ridge.py \
    --dataset-root "${M3_DATA}/" \
    --split-sheet "${M3_REPO}/scan_split_example.xlsx" \
    --out "${M3_OUT}/hypotheses/ridge_bandpower"
