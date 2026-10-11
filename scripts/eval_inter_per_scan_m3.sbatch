#!/bin/bash
# Score the inter-subject reproduction checkpoints (and the authors' published ones) on
# each held-out scan separately, for the paper's mean +/- SD across held-out scans.
# Fetch the published checkpoints into checkpoints/published/ on the login node first
# (compute nodes may have no internet), then submit from the repo root with:
#   sbatch scripts/eval_inter_per_scan_m3.sbatch
#SBATCH --job-name=nb-per-scan
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm_logs/per-scan-%j.out
#SBATCH --error=slurm_logs/per-scan-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

echo "GPU allocation: ${CUDA_VISIBLE_DEVICES:-not-set} on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

python scripts/eval_inter_per_scan.py \
    --runs "${M3_OUT}/paper_resting/inter" \
    --published-dir "${M3_REPO}/checkpoints/published" \
    --dataset-root "${M3_DATA}/" \
    --split-sheet "${M3_REPO}/scan_split_example.xlsx" \
    --out "${M3_OUT}/paper_resting/per_scan" \
    --mc-passes 20
