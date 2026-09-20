#!/bin/bash
# Allocate a GPU node and hold it, so VS Code Remote-SSH can connect to it.
# Run on an M3 LOGIN node:  bash scripts/m3_session.sh [hours]
#
# Uses a batch job running `sleep infinity` rather than `smux`. smux needs a
# TTY and then attaches you to tmux, which is fine when you are sitting at a
# terminal but cannot be scripted -- and for Remote-SSH all you actually need
# is a live allocation on the node, since SLURM lets you ssh into any node
# where you have a running job.
#
# For a terminal session with tmux instead, use smux directly over `ssh -t`:
#   ssh -t m3 'smux new-session --partition=gpu --gres=gpu:1 --cpuspertask 8 --mem 32G --time 8:00:00'
set -eo pipefail
source "$(dirname "$0")/m3_env.sh"

HOURS="${1:-8}"

existing="$(squeue -u "$USER" -h -o '%i %T %N %j' | awk '$2=="RUNNING" && $4=="nb-session" {print; exit}')"
if [[ -n "$existing" ]]; then
    jobid="$(awk '{print $1}' <<< "$existing")"
    node="$(awk '{print $3}' <<< "$existing")"
    echo "Already holding a session: jobid=$jobid node=$node"
    echo "VS Code host: $node"
    echo "(cancel it with: scancel $jobid)"
    exit 0
fi

mkdir -p "${M3_REPO}/slurm_logs"
echo "==> Holding 1 GPU on partition ${M3_PARTITION} for ${HOURS}h"
jobid="$(sbatch --parsable \
    --job-name=nb-session \
    --partition="${M3_PARTITION}" \
    --gres=gpu:1 \
    --cpus-per-task=8 \
    --mem=32G \
    --time="${HOURS}:00:00" \
    --output="${M3_REPO}/slurm_logs/%x-%j.out" \
    --wrap="sleep infinity")"
echo "    job $jobid submitted"

echo "==> Waiting for the node to be assigned..."
node=""
for _ in $(seq 1 90); do
    node="$(squeue -j "$jobid" -h -o '%T %N' | awk '$1=="RUNNING" && $2!="" {print $2; exit}')"
    [[ -n "$node" ]] && break
    sleep 5
done

if [[ -z "$node" ]]; then
    echo "Still pending. Check with: squeue -j $jobid"
    exit 0
fi

echo
echo "Node: $node"
echo "Run scripts/m3_connect.ps1 locally, then connect VS Code to host 'm3-node'."
echo "Release it when you are done with: scancel $jobid"
