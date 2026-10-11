#!/bin/bash
# CPU-only intra-scan band-power ridge on NeuroBOLT's intra-scan split, all 29 scans x 7 ROIs.
# Submit from the repo root, e.g.:
#   ARM=intra_ridge EXTRA="" sbatch scripts/baseline_ridge_intra_m3.sbatch
#   ARM=intra_ridge_fine EXTRA="--bands fine" sbatch scripts/baseline_ridge_intra_m3.sbatch
#SBATCH --job-name=nb-intra-ridge
#SBATCH --partition=comp
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=slurm_logs/intra-ridge-%x-%j.out
#SBATCH --error=slurm_logs/intra-ridge-%x-%j.err
set -eo pipefail

REPO_DIR="${SLURM_SUBMIT_DIR:?Submit this job from the NeuroBOLT repository root}"
source "${REPO_DIR}/scripts/m3_env.sh"
activate_neurobolt
cd "$REPO_DIR"

ARM="${ARM:-intra_ridge}"
echo "arm=${ARM} extra=${EXTRA:-none}"
# EXTRA is deliberately unquoted so it splits into separate flags
python scripts/baseline_ridge_intra.py --dataset-root "${M3_DATA}/" --out "${M3_OUT}/intra_baselines/${ARM}" ${EXTRA:-}
