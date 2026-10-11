#!/usr/bin/env python3
"""Band-power ridge baseline for intra-scan prediction, on NeuroBOLT's exact intra-scan split.

For every scan and ROI: train on the first 80% of the 16 s EEG windows, choose the ridge penalty
on the next 10% (after a 10-TR gap) by MSE, and score R on the last 10% (after another gap), as
prepare_onesub_dataloader does. No EEG high-pass, as in the intra-scan loader. The test frames
are the same 48 per scan that the NeuroBOLT intra-scan reproduction was scored on.

    python scripts/baseline_ridge_intra.py --dataset-root $M3_DATA --out <dir> [--bands fine] [--sub-windows 8]

Writes intra_ridge.csv: one row per scan and ROI with the chosen penalty and validation/test R.
"""
import argparse
import csv
import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS, BAND_SETS, band_power_features, ridge_path  # noqa: E402
from eval_inter_per_scan import ROIS, load_scan  # noqa: E402

TR = 2.1


def intra_split(n, window_sec=16):
    """Index ranges for train, validation and test, as in prepare_onesub_dataloader."""
    train_end = int(0.8 * n)
    val_end = int(0.1 * n) + train_end
    gap = math.ceil((20 if window_sec <= 20 else window_sec) / TR)
    return slice(0, train_end), slice(train_end + gap, val_end), slice(val_end + gap, n)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sub-windows", type=int, default=4)
    parser.add_argument("--bands", choices=sorted(BAND_SETS), default="classic")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)

    scans = sorted(os.path.basename(p).removesuffix("_eeg.set")
                   for p in glob.glob(os.path.join(args.dataset_root, "EEG", "*_eeg.set")))
    rows = []
    for scan in scans:
        eeg, y = load_scan(scan, args.dataset_root, highpass=False)
        feats = band_power_features(eeg, BAND_SETS[args.bands], args.sub_windows)
        train, val, test = intra_split(len(y))
        mean, std = feats[train].mean(axis=0), feats[train].std(axis=0) + 1e-8
        x = (feats - mean) / std
        path = ridge_path(x[train], y[train], [x[val], x[test]], ALPHAS)
        for j, (label, _) in enumerate(ROIS):
            mse, alpha, (val_pred, test_pred) = min(
                (float(np.mean((preds[0][:, j] - y[val, j]) ** 2)), alpha, preds) for alpha, preds in path.items())
            rows.append({"scan": scan, "roi": label, "alpha": float(alpha), "n_train": train.stop,
                         "n_test": len(y[test]), "val_corr": float(np.corrcoef(val_pred[:, j], y[val, j])[0, 1]),
                         "test_corr": float(np.corrcoef(test_pred[:, j], y[test, j])[0, 1]),
                         "test_mse": float(np.mean((test_pred[:, j] - y[test, j]) ** 2))})
        print(f"{scan}: " + " ".join(f"{r['test_corr']:.2f}" for r in rows[-len(ROIS):]), flush=True)

    with open(os.path.join(args.out, "intra_ridge.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for label, _ in ROIS:
        values = [r["test_corr"] for r in rows if r["roi"] == label]
        print(f"{label:30s} test R {np.mean(values):.3f} ± {np.std(values, ddof=1):.3f}")
    print(f"average over ROIs: {np.mean([r['test_corr'] for r in rows]):.3f}")


if __name__ == "__main__":
    main()
