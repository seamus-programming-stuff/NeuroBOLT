#!/bin/bash
#SBATCH --partition=comp
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=reports/thesis_exploration/natview/slurm-%x-%j.out
#SBATCH --error=reports/thesis_exploration/natview/slurm-%x-%j.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
source scripts/m3_env.sh
activate_neurobolt
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK" MKL_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK" PYTHONUNBUFFERED=1
script="$1"
shift
case "$script" in natview_*.py) ;; *) exit 2;; esac
date -u
echo "job=$SLURM_JOB_ID host=$(hostname) script=$script args=$*"
sha256sum "scripts/$script"
python -u "scripts/$script" "$@"
date -u
