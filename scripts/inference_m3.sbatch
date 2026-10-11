#!/bin/bash
# Headless inference on M3, mirroring Copy_of_NeuroBOLT_inference_demo.ipynb.
# Submit from the repo root (slurm_logs/ must already exist):
#   mkdir -p slurm_logs && sbatch scripts/inference_m3.sbatch [scan] [roi]
#SBATCH --job-name=nb-inference
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=slurm_logs/%x-%j.out
#SBATCH --error=slurm_logs/%x-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

SCAN="${1:-sub16-scan01}"
ROI="${2:-Thalamus}"

echo "=== node: $(hostname) ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

python scripts/run_inference.py \
    --scan "$SCAN" \
    --roi "$ROI" \
    --dataset-root "${M3_DATA}/" \
    --checkpoint-dir "${REPO_DIR}/checkpoints" \
    --channels "FP2,F4,C4,O2,T8,P7,CZ,POZ" \
    --output "${M3_OUT}/inference" \
    --plot
