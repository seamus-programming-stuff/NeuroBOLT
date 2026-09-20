#!/bin/bash
#SBATCH --job-name=nb-smoke
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=slurm_logs/%x-%j.out
#SBATCH --error=slurm_logs/%x-%j.out
#
# End-to-end check on real GPU hardware: 1 epoch of the intra-scan example.
#   mkdir -p slurm_logs && sbatch scripts/smoke_m3.sbatch
set -eo pipefail
# SLURM copies the batch script into a spool dir before running it, so
# $(dirname "$0") is NOT the repo -- use the submit directory instead.
REPO_DIR="${SLURM_SUBMIT_DIR:-/projects/hz18/stay0060/NeuroBOLT}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt

export MASTER_ADDR="$(hostname)"
export MASTER_PORT=29500

echo "=== node: $(hostname) ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python -c "import torch; print('cuda available:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0))"

echo "=== 1 epoch, intra-scan, sub11-scan01 ==="
cd "$M3_REPO"
python main.py \
    --batch_size 16 \
    --epochs 1 \
    --warmup_epochs 0 \
    --finetune ./checkpoints/labram-base.pth \
    --labels_roi Thalamus \
    --dataset VU \
    --train_test_mode intrascan \
    --dataname sub11-scan01 \
    --dataset_root "${M3_DATA}/" \
    --output_dir  "${M3_OUT}/smoke/" \
    --log_dir     "${M3_LOG}/smoke/" \
    --num_workers 8

echo "=== SMOKE TEST COMPLETE ==="
