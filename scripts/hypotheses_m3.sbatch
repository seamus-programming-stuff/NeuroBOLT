#!/bin/bash
# Inter-subject hypothesis runs. One arm = one set of extra main.py flags, trained for every
# ROI x seed on the authors' fold1 split, scored per held-out scan, with no checkpoints saved.
# Submit from the repo root, one array per arm:
#   EXP=base                                   sbatch --job-name=nb-base --array=0-20 scripts/hypotheses_m3.sbatch
#   EXP=nohp  EXTRA="--eeg_highpass 0"         sbatch --job-name=nb-nohp --array=0-20 scripts/hypotheses_m3.sbatch
#   EXP=multi7 MULTI=1                         sbatch --job-name=nb-multi7 --array=0-2 scripts/hypotheses_m3.sbatch
# Array index -> (seed, ROI index 0-6), seeds from SEEDS (default "12345 1 2"); with MULTI=1 the
# index picks only the seed and one model predicts all seven ROIs. The QOS caps us at 4 GPUs,
# so arrays queue behind each other without a % throttle.
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm_logs/hyp-%x-%A_%a.out
#SBATCH --error=slurm_logs/hyp-%x-%A_%a.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

EXP="${EXP:?Set EXP to the arm name}"
TASK_ID="${SLURM_ARRAY_TASK_ID:?Submit as a SLURM array}"
read -r -a SEED_LIST <<< "${SEEDS:-12345 1 2}"
ROIS=("Cuneus" "Heschl’s gyrus" "Middle frontal gyrus anterior" \
      "Precuneus anterior" "Putamen" "Thalamus" "global signal clean")
N_ROI=${#ROIS[@]}

if [[ "${MULTI:-0}" == 1 ]]; then
    SEED="${SEED_LIST[$TASK_ID]:?Array index beyond SEEDS}"
    ROI="$(IFS='|'; echo "${ROIS[*]}")"
    RUN_KEY="all/seed${SEED}"
else
    SEED="${SEED_LIST[$((TASK_ID / N_ROI))]:?Array index beyond SEEDS x ROIs}"
    ROI_INDEX=$((TASK_ID % N_ROI))
    ROI="${ROIS[$ROI_INDEX]}"
    RUN_KEY="${ROI_INDEX}/seed${SEED}"
fi

OUT_DIR="${M3_OUT}/hypotheses/${EXP}/${RUN_KEY}"
LOG_DIR="${M3_LOG}/hypotheses/${EXP}/${RUN_KEY}"
if [[ -f "${OUT_DIR}/done" ]]; then
    echo "${OUT_DIR} already finished; skipping"
    exit 0
fi
mkdir -p "$OUT_DIR" "$LOG_DIR"
rm -f "${OUT_DIR}/log.txt"  # main.py appends, so a retried task must start a fresh log

echo "Task ${TASK_ID}: exp=${EXP} seed=${SEED} roi=${ROI} extra=${EXTRA:-none}"
echo "GPU allocation: ${CUDA_VISIBLE_DEVICES:-not-set} on $(hostname)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "${EXTRA:-}" > "${OUT_DIR}/extra_args.txt"

# EXTRA is deliberately unquoted so it splits into separate flags
env -u SLURM_PROCID python main.py \
    --batch_size 64 --epochs 30 --warmup_epochs 5 --seed "$SEED" \
    --finetune "${M3_REPO}/checkpoints/labram-base.pth" \
    --labels_roi "$ROI" --dataset VU --train_test_mode full_test \
    --dataset_root "${M3_DATA}/" --split_index_sheet "${M3_REPO}/scan_split_example.xlsx" \
    --output_dir "${OUT_DIR}/" --log_dir "${LOG_DIR}/" --num_workers 8 \
    --no_save_ckpt --save_best_predictions --early_stop_patience 10 \
    ${EXTRA:-}
touch "${OUT_DIR}/done"
