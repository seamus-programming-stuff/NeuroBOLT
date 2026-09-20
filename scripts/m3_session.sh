#!/bin/bash
# Start (or report) a persistent interactive GPU job on M3.
# Run on an M3 LOGIN node:  bash scripts/m3_session.sh [hours]
#
# Uses smux, which runs a tmux inside the SLURM job, so the allocation
# survives your laptop disconnecting -- which it will, while VS Code reconnects.
set -euo pipefail
source "$(dirname "$0")/m3_env.sh"

HOURS="${1:-8}"

existing="$(squeue -u "$USER" -h -o '%i %T %N' | awk '$2=="RUNNING" && $3!="" {print; exit}')"
if [[ -n "$existing" ]]; then
    echo "You already have a running job:"
    echo "  jobid=$(echo "$existing" | awk '{print $1}')  node=$(echo "$existing" | awk '{print $3}')"
    echo
    echo "Attach with:   smux attach-session $(echo "$existing" | awk '{print $1}')"
    echo "VS Code host:  $(echo "$existing" | awk '{print $3}')"
    exit 0
fi

echo "==> Requesting 1 GPU on partition ${M3_PARTITION} for ${HOURS}h"
smux new-session \
    --partition="${M3_PARTITION}" \
    --gres=gpu:1 \
    --cpus-per-task=8 \
    --mem=32G \
    --time="${HOURS}:00:00"

echo
echo "==> Waiting for the node to be assigned..."
for _ in $(seq 1 60); do
    node="$(squeue -u "$USER" -h -o '%T %N' | awk '$1=="RUNNING" && $2!="" {print $2; exit}')"
    [[ -n "${node:-}" ]] && break
    sleep 5
done

if [[ -z "${node:-}" ]]; then
    echo "Still pending. Check with: squeue -u $USER"
    exit 0
fi

echo
echo "Node: $node"
echo "Point VS Code Remote-SSH at that hostname (or run scripts/m3_connect.ps1 locally)."
