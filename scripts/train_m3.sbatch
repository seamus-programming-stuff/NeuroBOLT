#!/bin/bash
#SBATCH --job-name=neurobolt
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=slurm_logs/%x-%j.out
#SBATCH --error=slurm_logs/%x-%j.err
#
# Submit from the repo root (slurm_logs/ must already exist):
#   mkdir -p slurm_logs && sbatch scripts/train_m3.sbatch
set -euo pipefail
# SLURM copies the batch script into a spool dir before running it, so
# $(dirname "$0") is NOT the repo -- use the submit directory instead.
REPO_DIR="${SLURM_SUBMIT_DIR:-/projects/hz18/stay0060/NeuroBOLT}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt

# utils.init_distributed_mode() takes the SLURM_PROCID branch whenever this is
# set (it always is under sbatch/srun), flips distributed on, but leaves
# dist_url at 'env://' -- which then reads these two from the environment and
# crashes if they are missing. See utils.py:417.
export MASTER_ADDR="$(hostname)"
export MASTER_PORT=29500

nvidia-smi

# Intra-scan example. Swap for the cross-subject command below as needed.
python main.py \
    --batch_size 16 \
    --finetune ./checkpoints/labram-base.pth \
    --labels_roi Thalamus \
    --dataset VU \
    --train_test_mode intrascan \
    --dataname sub11-scan01 \
    --dataset_root "${M3_DATA}/" \
    --output_dir  "${M3_OUT}/" \
    --log_dir     "${M3_LOG}/" \
    --num_workers 8

# Cross-subject variant:
# python main.py \
#     --batch_size 64 \
#     --finetune ./checkpoints/labram-base.pth \
#     --labels_roi Thalamus \
#     --dataset VU \
#     --train_test_mode full_test \
#     --split_index_sheet ./scan_split_example.xlsx \
#     --dataset_root "${M3_DATA}/" \
#     --output_dir  "${M3_OUT}/" \
#     --log_dir     "${M3_LOG}/" \
#     --num_workers 8
