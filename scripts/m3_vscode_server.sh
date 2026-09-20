#!/bin/bash
# Pre-install the VS Code remote server on M3 so the first Remote-SSH connect
# does not stall on a download (and fails loudly here if it cannot).
#
#   bash scripts/m3_vscode_server.sh <commit-sha>
#
# Find the sha locally with:
#   Code.exe --version          (third line)
# or read "commit" from resources/app/product.json in the VS Code install dir.
# It changes with every VS Code update; ~/.vscode-server is in shared home, so
# seeding it once covers the login node and every compute node.
set -eo pipefail

COMMIT="${1:?usage: m3_vscode_server.sh <commit-sha>}"
DEST="${HOME}/.vscode-server/bin/${COMMIT}"

if [[ -x "${DEST}/bin/code-server" ]]; then
    echo "Already installed: ${DEST}"
    exit 0
fi

URL="https://update.code.visualstudio.com/commit:${COMMIT}/server-linux-x64/stable"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> Downloading server for ${COMMIT}"
curl -fL --retry 3 --progress-bar -o "${TMP}/server.tar.gz" "$URL"

echo "==> Extracting to ${DEST}"
mkdir -p "$DEST"
# The tarball has a single top-level dir; strip it.
tar -xzf "${TMP}/server.tar.gz" -C "$DEST" --strip-components=1

echo "==> Verifying"
"${DEST}/bin/code-server" --version
echo "OK"
