#!/bin/bash
# Shared M3 settings, sourced by the other scripts. Edit these two lines.
export M3_PROJ="${M3_PROJ:-hz18}"     # verify with `user_info`
export M3_PARTITION="${M3_PARTITION:-gpu}"    # A100/L40S/A40/T4; m3h is H100

export M3_BASE="/projects/${M3_PROJ}/${USER}"
export M3_SCRATCH="/scratch/${M3_PROJ}/${USER}"
export M3_REPO="${M3_BASE}/NeuroBOLT"
export M3_CONDA="${M3_BASE}/miniforge3"
export M3_DATA="${M3_SCRATCH}/NeuroBOLT/data"
export M3_OUT="${M3_SCRATCH}/NeuroBOLT/checkpoints"
export M3_LOG="${M3_SCRATCH}/NeuroBOLT/log"

# Keep caches off the small home quota.
export PIP_CACHE_DIR="${M3_SCRATCH}/.cache/pip"
export HF_HOME="${M3_SCRATCH}/.cache/huggingface"
export TORCH_HOME="${M3_SCRATCH}/.cache/torch"

activate_neurobolt() {
    source "${M3_CONDA}/etc/profile.d/conda.sh"
    conda activate neurobolt
}
