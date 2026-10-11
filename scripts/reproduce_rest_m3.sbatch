#!/bin/bash
# Reproduce NeuroBOLT's resting-state intra-scan and unseen-scan experiments.
# Submit from the repo root with: sbatch --array=0-209%2 scripts/reproduce_rest_m3.sbatch
# Tasks 0-202 cover 29 scans x 7 ROIs; tasks 203-209 cover 7 cross-subject ROIs.
# Uses one GPU per task and limits concurrency to two by default at submission.
# The auditory-task dataset is not part of this public release.
#SBATCH --job-name=nb-paper-rest
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=slurm_logs/paper-rest-%A_%a.out
#SBATCH --error=slurm_logs/paper-rest-%A_%a.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

TASK_ID="${SLURM_ARRAY_TASK_ID:?Submit as a SLURM array}"
ROIS=("Cuneus" "Heschl’s gyrus" "Middle frontal gyrus anterior" \
      "Precuneus anterior" "Putamen" "Thalamus" "global signal clean")
N_ROI=${#ROIS[@]}

if (( TASK_ID < 203 )); then
    mapfile -t SCANS < <(find "${M3_DATA}/EEG" -maxdepth 1 -type f -name '*_eeg.set' -printf '%f\n' | sed 's/_eeg\.set$//' | sort)
    if (( ${#SCANS[@]} != 29 )); then
        echo "Expected 29 resting-state EEG scans; found ${#SCANS[@]} in ${M3_DATA}/EEG" >&2
        exit 2
    fi
    SCAN_INDEX=$((TASK_ID / N_ROI))
    ROI_INDEX=$((TASK_ID % N_ROI))
    SCAN="${SCANS[$SCAN_INDEX]}"
    ROI="${ROIS[$ROI_INDEX]}"
    MODE="intrascan"
    BATCH_SIZE=16
    RUN_KEY="intra/${SCAN}/${ROI_INDEX}"
else
    ROI_INDEX=$((TASK_ID - 203))
    if (( ROI_INDEX >= N_ROI )); then
        echo "Array task ${TASK_ID} is outside the 210-task reproduction set" >&2
        exit 2
    fi
    ROI="${ROIS[$ROI_INDEX]}"
    SCAN="all"
    MODE="full_test"
    BATCH_SIZE=64
    RUN_KEY="inter/${ROI_INDEX}"
fi

OUT_DIR="${M3_OUT}/paper_resting/${RUN_KEY}"
LOG_DIR="${M3_LOG}/paper_resting/${RUN_KEY}"
mkdir -p "$OUT_DIR" "$LOG_DIR"

echo "Task ${TASK_ID}: mode=${MODE} scan=${SCAN} roi=${ROI} batch=${BATCH_SIZE}"
echo "GPU allocation: ${CUDA_VISIBLE_DEVICES:-not-set} on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

ARGS=(
    --batch_size "$BATCH_SIZE"
    --epochs 30
    --warmup_epochs 5
    --seed 12345
    --finetune "${M3_REPO}/checkpoints/labram-base.pth"
    --labels_roi "$ROI"
    --dataset VU
    --train_test_mode "$MODE"
    --dataset_root "${M3_DATA}/"
    --output_dir "${OUT_DIR}/"
    --log_dir "${LOG_DIR}/"
    --num_workers 8
)

if [[ "$MODE" == "intrascan" ]]; then
    ARGS+=(--dataname "$SCAN")
else
    ARGS+=(--split_index_sheet "${M3_REPO}/scan_split_example.xlsx")
fi

export MASTER_ADDR="$(hostname)"
export MASTER_PORT=$((29500 + TASK_ID % 1000))
env -u SLURM_PROCID python main.py "${ARGS[@]}"
