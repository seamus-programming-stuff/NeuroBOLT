#!/bin/bash
#SBATCH --partition=comp
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=reports/thesis_exploration/data/slurm-%x-%j.out
#SBATCH --error=reports/thesis_exploration/data/slurm-%x-%j.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
source scripts/m3_env.sh
activate_neurobolt
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}" MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}" PYTHONUNBUFFERED=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
script="$1"
shift
case "$script" in thesis_*.py) ;; *) echo 'Only thesis scripts allowed'; exit 2;; esac
date -u
echo "job=$SLURM_JOB_ID host=$(hostname) cpus=$SLURM_CPUS_PER_TASK script=$script args=$*"
sha256sum "scripts/$script"
python -u "scripts/$script" "$@"
date -u
