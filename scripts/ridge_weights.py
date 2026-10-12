#!/usr/bin/env python3
"""Coefficients of the band-power ridge model, as channel x frequency x lag maps per ROI.

Refits ridge on the training scans with the penalty an earlier baseline_ridge.py run chose for
each ROI (read from that arm's log.txt), and saves the weights on the standardized features, so
they are comparable across features in "per SD of log power" units.

    python scripts/ridge_weights.py --dataset-root $M3_DATA --arm-dir $M3_OUT/hypotheses/ridge_fine_w24_sub12 \
        --bands fine --window-sec 24 --sub-windows 12 --out weights.npz

Feature order follows band_power_features: channel, then frequency band, then lag bin (oldest
EEG first), so weights reshape to (ROI, channel, band, lag).
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import BAND_SETS, band_power_features  # noqa: E402
from eval_inter_per_scan import CH_NAMES, ROIS, load_scan  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_example.xlsx")
    parser.add_argument("--arm-dir", required=True, help="baseline_ridge.py output whose penalties to reuse")
    parser.add_argument("--bands", choices=sorted(BAND_SETS), default="fine")
    parser.add_argument("--window-sec", type=int, default=24)
    parser.add_argument("--sub-windows", type=int, default=12)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))

    alphas = []
    for j in range(len(ROIS)):
        row = json.loads(open(os.path.join(args.arm_dir, str(j), "seed0", "log.txt"), encoding="utf-8").readline())
        alphas.append(float(re.search(r"alpha=([0-9.e+-]+)", row["chosen"]).group(1)))

    sheet = pd.read_excel(args.split_sheet, sheet_name="fold1")
    feats, targets = [], []
    for scan in sheet.loc[sheet["train"] == 1, "scan_name"]:
        eeg, y = load_scan(scan, args.dataset_root, highpass=True, window_sec=args.window_sec)
        feats.append(band_power_features(eeg, BAND_SETS[args.bands], args.sub_windows))
        targets.append(y)
        print(f"train {scan}: {len(y)} windows", flush=True)
    x = np.concatenate(feats)
    x = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-8)
    y = np.concatenate(targets)

    xt = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32))
    yt = torch.from_numpy(y.astype(np.float32))
    u, s, vt = torch.linalg.svd(xt - xt.mean(dim=0), full_matrices=False)
    uty = u.T @ (yt - yt.mean(dim=0))
    weights = np.stack([(vt.T @ ((s / (s ** 2 + a)) * uty[:, j])).numpy() for j, a in enumerate(alphas)])

    bands = BAND_SETS[args.bands]
    weights = weights.reshape(len(ROIS), len(CH_NAMES), len(bands), args.sub_windows)
    lag_ends = np.arange(args.sub_windows, 0, -1) * args.window_sec / args.sub_windows  # seconds before the frame
    np.savez_compressed(args.out, weights=weights, alphas=np.array(alphas), rois=np.array([r for r, _ in ROIS]),
                        channels=np.array(CH_NAMES), band_lo=np.array([b[0] for b in bands]),
                        band_hi=np.array([b[1] for b in bands]), lag_start_sec=lag_ends,
                        lag_end_sec=lag_ends - args.window_sec / args.sub_windows)
    print(f"Wrote {args.out}: weights {weights.shape}")


if __name__ == "__main__":
    main()
