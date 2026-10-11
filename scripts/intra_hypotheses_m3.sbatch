#!/bin/bash
# Intra-scan hypothesis runs on the six inter-subject test scans (scans the cross-subject models
# never saw), 7 ROIs each: does starting from a model trained on other people fix NeuroBOLT's
# data starvation within a scan? Submit from the repo root, one array (0-41) per arm:
#   EXP=intra_labram_hp                 sbatch --job-name=nb-intra_labram_hp   --array=0-41 scripts/intra_hypotheses_m3.sbatch
#   EXP=intra_transfer_hp TRANSFER=1    sbatch --job-name=nb-intra_transfer_hp --array=0-41 scripts/intra_hypotheses_m3.sbatch
# TRANSFER=1 initializes from the reproduction's inter-subject checkpoint for the same ROI (its
# minimum-validation-MSE epoch). Both arms apply the 0.5 Hz EEG high-pass those checkpoints were
# trained with, so the LaBraM arm is the matched control.
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=slurm_logs/intra-%x-%A_%a.out
#SBATCH --error=slurm_logs/intra-%x-%A_%a.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

EXP="${EXP:?Set EXP to the arm name}"
TASK_ID="${SLURM_ARRAY_TASK_ID:?Submit as a SLURM array}"
SEED="${SEED:-12345}"
SCANS=(sub07-scan01 sub07-scan02 sub11-scan01 sub16-scan01 sub18-scan01 sub21-scan01)
ROIS=("Cuneus" "Heschl’s gyrus" "Middle frontal gyrus anterior" \
      "Precuneus anterior" "Putamen" "Thalamus" "global signal clean")
SCAN="${SCANS[$((TASK_ID / 7))]:?Array index beyond 6 scans x 7 ROIs}"
ROI_INDEX=$((TASK_ID % 7))
ROI="${ROIS[$ROI_INDEX]}"

OUT_DIR="${M3_OUT}/intra_hypotheses/${EXP}/${SCAN}/${ROI_INDEX}"
if [[ -f "${OUT_DIR}/done" ]]; then
    echo "${OUT_DIR} already finished; skipping"
    exit 0
fi
mkdir -p "$OUT_DIR"
rm -f "${OUT_DIR}/log.txt"

INIT=(--finetune "${M3_REPO}/checkpoints/labram-base.pth")
if [[ "${TRANSFER:-0}" == 1 ]]; then
    RUN="${M3_OUT}/paper_resting/inter/${ROI_INDEX}"
    EPOCH=$(python -c "import json,sys; rows=[json.loads(l) for l in open(sys.argv[1])]; print(min(rows, key=lambda r: r['val_mse'])['epoch'])" "${RUN}/log.txt")
    CKPT=$(ls "${RUN}"/*/checkpoint-epoch"${EPOCH}"-*.pth)
    INIT=(--finetune "$CKPT" --model_filter_name "")  # load the whole state dict, not LaBraM's student.* keys
fi
echo "Task ${TASK_ID}: exp=${EXP} scan=${SCAN} roi=${ROI} init=${INIT[1]}"

# EXTRA is deliberately unquoted so it splits into separate flags
env -u SLURM_PROCID python main.py \
    --batch_size 16 --epochs 30 --warmup_epochs 5 --seed "$SEED" "${INIT[@]}" \
    --labels_roi "$ROI" --dataset VU --train_test_mode intrascan --dataname "$SCAN" \
    --dataset_root "${M3_DATA}/" --eeg_highpass 0.5 \
    --output_dir "${OUT_DIR}/" --log_dir "${OUT_DIR}/tb/" --num_workers 8 --no_save_ckpt \
    ${EXTRA:-}
touch "${OUT_DIR}/done"
