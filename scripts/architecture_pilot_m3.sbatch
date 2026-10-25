#!/bin/bash
# A single bounded allocation for all fixed exploratory cache-pilot fits.
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=reports/architecture_briefing/pilot/architecture-%j.out
#SBATCH --error=reports/architecture_briefing/pilot/architecture-%j.err
set -eo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the NeuroBOLT repository root}"
source scripts/m3_env.sh >/dev/null
activate_neurobolt >/dev/null 2>&1
export PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
OUT="${PILOT_OUT:?Set PILOT_OUT to the frozen new run directory}"
echo "ARCHITECTURE_PILOT job=${SLURM_JOB_ID} host=$(hostname) out=${OUT}"
python -B scripts/architecture_pilot_tests.py
python -B scripts/architecture_pilot.py run --out "$OUT"
