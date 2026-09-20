#!/bin/bash
# Fetch the LaBraM base checkpoint and the NeuroBOLT dataset.
# Run on an M3 LOGIN node (compute nodes may have no internet):
#   bash scripts/m3_fetch_data.sh
#
# Uses plain curl so it does not depend on the conda env being healthy.
# Safe to re-run: existing, correctly-sized files are skipped.
set -euo pipefail
source "$(dirname "$0")/m3_env.sh"

CKPT_DIR="${M3_REPO}/checkpoints"
mkdir -p "$CKPT_DIR" "${M3_DATA}/EEG" "${M3_DATA}/fMRI_difumo"

# --- 1. LaBraM base checkpoint (needed for --finetune) --------------------
LABRAM_URL="https://github.com/935963004/LaBraM/raw/main/checkpoints/labram-base.pth"
LABRAM_SIZE=96612769
if [[ -f "$CKPT_DIR/labram-base.pth" ]] && \
   [[ "$(stat -c%s "$CKPT_DIR/labram-base.pth")" == "$LABRAM_SIZE" ]]; then
    echo "==> labram-base.pth already present"
else
    echo "==> Downloading labram-base.pth (92 MiB)"
    curl -fL --retry 3 --progress-bar -o "$CKPT_DIR/labram-base.pth" "$LABRAM_URL"
    got="$(stat -c%s "$CKPT_DIR/labram-base.pth")"
    [[ "$got" == "$LABRAM_SIZE" ]] || { echo "SIZE MISMATCH: $got != $LABRAM_SIZE" >&2; exit 1; }
fi

# --- 2. Dataset -----------------------------------------------------------
# HuggingFace lays it out as EEG_set/ and fMRI_difumo64/, but
# dataset_maker/get_datasets.py:19-20 looks for EEG/ and fMRI_difumo/.
# The filenames within already match, so only the directories are remapped.
REPO="NeurdyLab/NeuroBOLT"
API="https://huggingface.co/api/datasets/${REPO}/tree/main?recursive=true"
RESOLVE="https://huggingface.co/datasets/${REPO}/resolve/main"
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT

echo "==> Listing dataset files"
curl -fsS "$API" | python3 -c '
import json, sys
DIRMAP = {"EEG_set": "EEG", "fMRI_difumo64": "fMRI_difumo"}
for f in json.load(sys.stdin):
    if f.get("type") != "file":
        continue
    path = f["path"]
    if "/" not in path:
        continue
    top, name = path.split("/", 1)
    if top not in DIRMAP:
        continue
    size = (f.get("lfs") or {}).get("size") or f.get("size") or 0
    print("%s\t%s/%s\t%d" % (path, DIRMAP[top], name, size))
' > "$LIST"

echo "==> $(wc -l < "$LIST") files to consider"

fetch_one() {
    IFS=$'\t' read -r remote local size <<< "$1"
    dest="${M3_DATA}/${local}"
    if [[ -f "$dest" && "$(stat -c%s "$dest")" == "$size" ]]; then
        return 0
    fi
    curl -fsSL --retry 3 -o "$dest" "${RESOLVE}/${remote}"
    got="$(stat -c%s "$dest")"
    if [[ "$got" != "$size" ]]; then
        echo "  SIZE MISMATCH $local: $got != $size" >&2
        return 1
    fi
    echo "  ok $local"
}
export -f fetch_one
export M3_DATA RESOLVE

# 8 at a time; the files are small and the login node is shared.
< "$LIST" xargs -d '\n' -P 8 -I{} bash -c 'fetch_one "$@"' _ {}

echo
echo "==> Result"
printf '  EEG          %s files  %s\n' \
    "$(find "${M3_DATA}/EEG" -type f | wc -l)" "$(du -sh "${M3_DATA}/EEG" | cut -f1)"
printf '  fMRI_difumo  %s files  %s\n' \
    "$(find "${M3_DATA}/fMRI_difumo" -type f | wc -l)" "$(du -sh "${M3_DATA}/fMRI_difumo" | cut -f1)"
printf '  checkpoint   %s\n' "$(ls -lh "$CKPT_DIR/labram-base.pth" | awk '{print $5}')"
