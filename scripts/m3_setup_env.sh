#!/bin/bash
# Run ONCE, on an M3 *login* node (compute nodes may have no internet access).
#   bash scripts/m3_setup_env.sh
# NB: no `set -u` -- conda's own activate/deactivate hooks reference unset
# variables, which would abort this script partway through.
set -eo pipefail
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

# Two things will silently break this env if left unpinned:
#   * numpy 2.x -- torch 2.0.0 was built against numpy 1.x, so any array/tensor
#     conversion dies with "RuntimeError: Numpy is not available".
#   * mkl > 2024.0 -- dropped the iJIT_NotifyEvent symbol torch 2.0.0 links
#     against, so `import torch` fails outright.
# A later `conda install <anything>` is enough to pull either one in, so pin
# them at the env level rather than relying on install order.
echo "==> Pinning numpy / mkl"
cat > "${CONDA_PREFIX}/conda-meta/pinned" <<'PIN'
numpy 1.24.*
mkl 2024.0.*
python 3.9.*
pytorch 2.0.0
PIN

echo "==> Installing PyTorch 2.0.0 / CUDA 11.8"
conda install -y pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 \
    pytorch-cuda=11.8 "mkl=2024.0.0" "numpy=1.24.3" -c pytorch -c nvidia

echo "==> Installing requirements.txt"
# Upstream requirements.txt carries `--no-deps` inline on the first
# requirement. That is not a valid per-requirement option, so modern pip
# rejects the whole file ("no such option: --no-deps") and installs NOTHING --
# silently leaving you without mne, timm, pandas and the rest.
# Split it: the --no-deps lines in one pass, everything else in another.
REQ="${M3_REPO}/requirements.txt"
REQ_NODEPS="$(mktemp)"; REQ_REST="$(mktemp)"
trap 'rm -f "$REQ_NODEPS" "$REQ_REST"' EXIT
tr -d '
' < "$REQ" | sed -n 's/[[:space:]]*--no-deps[[:space:]]*$//p' > "$REQ_NODEPS"
tr -d '
' < "$REQ" | grep -v -- '--no-deps' > "$REQ_REST"

if [[ -s "$REQ_NODEPS" ]]; then
    echo "    (--no-deps: $(tr '
' ' ' < "$REQ_NODEPS"))"
    pip install --no-deps -r "$REQ_NODEPS"
fi
pip install -r "$REQ_REST"

# `--no-deps` is not enough for linear-attention-transformer: it imports
# local_attention at module level, so it is unimportable without its deps.
# Install them under a constraint so they cannot drag torch off 2.0.0.
echo "==> Installing linear-attention-transformer's runtime deps"
CONSTRAINTS="$(mktemp)"
printf 'torch==2.0.0
numpy==1.24.3
timm==0.4.12
' > "$CONSTRAINTS"
pip install -c "$CONSTRAINTS"     axial-positional-embedding linformer local-attention product-key-memory
rm -f "$CONSTRAINTS"

# conda's tensorboardX can collide with the pins; pip's is fine.
pip install tensorboardX


# torch bundles its own cuDNN, and libcudnn_cnn_infer.so.8 dlopen()s the
# UNVERSIONED libnvrtc.so. conda only ships libnvrtc.so.11.2, and
# LD_LIBRARY_PATH is empty under SLURM, so the first conv aborts the process:
#   Could not load library libcudnn_cnn_infer.so.8
#   Error: libnvrtc.so: cannot open shared object file
# Fix both halves: the missing symlink, and the search path on every activate.
echo "==> Patching cuDNN/nvrtc library loading"
if [[ ! -e "${CONDA_PREFIX}/lib/libnvrtc.so" ]]; then
    nvrtc="$(cd "${CONDA_PREFIX}/lib" && ls libnvrtc.so.*.* 2>/dev/null | head -1)"
    [[ -n "$nvrtc" ]] && ln -s "$nvrtc" "${CONDA_PREFIX}/lib/libnvrtc.so"
fi
mkdir -p "${CONDA_PREFIX}/etc/conda/activate.d"
cat > "${CONDA_PREFIX}/etc/conda/activate.d/zz_ld_library_path.sh" <<'HOOK'
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH:-}"
HOOK

echo "==> Verifying the stack"
python - <<'VERIFY'
import numpy, torch
print("  numpy", numpy.__version__)
print("  torch", torch.__version__, "cuda", torch.version.cuda)
assert numpy.__version__.startswith("1.24"), "numpy must stay on 1.24.x for torch 2.0"
torch.from_numpy(numpy.zeros((2, 2), dtype=numpy.float32))
print("  numpy<->torch bridge OK")
print("  cuda visible:", torch.cuda.is_available(), "(False is expected on a login node)")
VERIFY

echo
echo "Done. Still to do by hand:"
echo "  1. Put labram-base.pth in ${M3_REPO}/checkpoints/"
echo "     https://github.com/935963004/LaBraM/tree/main/checkpoints"
echo "  2. Put the EEG / fMRI data under ${M3_DATA}/"
echo "     https://huggingface.co/datasets/NeurdyLab/NeuroBOLT"
echo "  Download both on a LOGIN node, not a compute node."
