#!/bin/bash
# Run ONCE, on an M3 *login* node (compute nodes may have no internet access).
#   bash scripts/m3_setup_env.sh
set -euo pipefail
source "$(dirname "$0")/m3_env.sh"

if [[ "$M3_PROJ" == "YOUR_PROJECT_CODE" ]]; then
    echo "ERROR: set M3_PROJ in scripts/m3_env.sh first (run 'user_info' to find it)." >&2
    exit 1
fi

echo "==> Creating directories"
mkdir -p "$M3_BASE" "$M3_DATA" "$M3_OUT" "$M3_LOG" \
         "$PIP_CACHE_DIR" "$HF_HOME" "$TORCH_HOME" \
         "$M3_REPO/slurm_logs" "$M3_REPO/checkpoints"

if [[ ! -d "$M3_CONDA" ]]; then
    echo "==> Installing Miniforge into $M3_CONDA (home quota is too small for this)"
    installer="${M3_SCRATCH}/Miniforge3-Linux-x86_64.sh"
    wget -q --show-progress -O "$installer" \
        https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash "$installer" -b -p "$M3_CONDA"
    rm -f "$installer"
else
    echo "==> Miniforge already present at $M3_CONDA"
fi

source "${M3_CONDA}/etc/profile.d/conda.sh"

if ! conda env list | grep -q "^neurobolt "; then
    echo "==> Creating the 'neurobolt' env (python 3.9)"
    conda create -y -n neurobolt python=3.9
fi
conda activate neurobolt

echo "==> Installing PyTorch 2.0.0 / CUDA 11.8"
conda install -y pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 \
    pytorch-cuda=11.8 -c pytorch -c nvidia
conda install -y tensorboardX

echo "==> Installing requirements.txt"
pip install -r "${M3_REPO}/requirements.txt"

echo
echo "Done. Still to do by hand:"
echo "  1. Put labram-base.pth in ${M3_REPO}/checkpoints/"
echo "     https://github.com/935963004/LaBraM/tree/main/checkpoints"
echo "  2. Put the EEG / fMRI data under ${M3_DATA}/"
echo "     https://huggingface.co/datasets/NeurdyLab/NeuroBOLT"
echo "  Download both on a LOGIN node, not a compute node."
