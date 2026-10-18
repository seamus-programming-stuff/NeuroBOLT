#!/bin/bash
# Runs one interpretability analysis script on M3. Submit from the repo root, e.g.:
#   CMD="scripts/interp_build_cache.py --dataset-root \$M3_DATA/ ..." sbatch scripts/interp_m3.sbatch
#   CMD="scripts/interp_attribution.py ..." sbatch --partition=gpu --gres=gpu:1 scripts/interp_m3.sbatch
# CMD is expanded inside the job, so it can use $M3_DATA, $M3_OUT and $M3_REPO.
#SBATCH --job-name=nb-interp
#SBATCH --partition=comp
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=slurm_logs/interp-%x-%j.out
#SBATCH --error=slurm_logs/interp-%x-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}" MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
mkdir -p "${M3_OUT}/interp"

echo "cmd=${CMD:?Set CMD to the script and its arguments}"
eval python -X utf8 ${CMD}
