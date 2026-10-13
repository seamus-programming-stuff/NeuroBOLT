#!/usr/bin/env python3
"""How much of the predictable BOLD is a single EEG vigilance index? Nested ridge models, 5-fold CV.

From the cached features (log power in 1 Hz bins x 26 channels x 12 lag bins over 24 s, written by
ridge_learning_curve.py), three feature sets of increasing detail:
  vigilance  12 features: per lag bin, channel-averaged log alpha (8-13 Hz) power minus log
             delta+theta (1-8 Hz) power, a standard EEG vigilance index
  bands      60 features: per lag bin, channel-averaged log power in five classic bands
  full       13,728 features: the best ridge model's full feature set
Each is fitted per cross-validation fold (penalty chosen on the fold's validation people) and
scored on the fold's held-out people, so every scan is held out once.

    python scripts/vigilance_model.py --cache features.npz --split-sheet scan_split_cv5.xlsx
"""
import argparse
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.special import logsumexp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS, ridge_path  # noqa: E402
from eval_inter_per_scan import ROIS  # noqa: E402

FREQS = np.arange(1, 45) + 0.5  # centres of the 1 Hz bins
N_CHANNELS, N_BANDS, N_LAGS = 26, 44, 12
BANDS = [(1, 4), (4, 8), (8, 13), (13, 30), (30, 45)]
SHORT = ["Cuneus", "Heschl's", "Mid. frontal", "Precuneus", "Putamen", "Thalamus", "Global"]


def band_log_power(x, lo, hi):
    """(windows, lags) channel-averaged log of total power in [lo, hi) Hz."""
    x = x.reshape(len(x), N_CHANNELS, N_BANDS, N_LAGS)
    return logsumexp(x[:, :, (FREQS >= lo) & (FREQS < hi), :], axis=2).mean(axis=1)


def feature_sets(x):
    return {"vigilance": band_log_power(x, 8, 13) - band_log_power(x, 1, 8),
            "bands": np.concatenate([band_log_power(x, lo, hi) for lo, hi in BANDS], axis=1),
            "full": x}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    z = np.load(args.cache)
    scans = sorted(k[2:] for k in z.files if k.startswith("x_"))
    feats = {s: feature_sets(z[f"x_{s}"]) for s in scans}
    targets = {s: z[f"y_{s}"] for s in scans}
    scores = defaultdict(list)  # (feature set, roi) -> per-scan R
    for k in range(1, args.folds + 1):
        sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
        split = {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("train", "val", "test")}
        for name in ("vigilance", "bands", "full"):
            x_train = np.concatenate([feats[s][name] for s in split["train"]])
            mean, std = x_train.mean(axis=0), x_train.std(axis=0) + 1e-8
            scale = lambda group: np.concatenate([(feats[s][name] - mean) / std for s in group])  # noqa: E731
            y_train = np.concatenate([targets[s] for s in split["train"]])
            y_val = np.concatenate([targets[s] for s in split["val"]])
            path = ridge_path((x_train - mean) / std, y_train, [scale(split["val"]), scale(split["test"])], ALPHAS)
            for j in range(len(ROIS)):
                alpha = min(path, key=lambda a: float(np.mean((path[a][0][:, j] - y_val[:, j]) ** 2)))
                start = 0
                for scan in split["test"]:
                    n = len(targets[scan])
                    pred = path[alpha][1][start:start + n, j]
                    scores[(name, j)].append(float(np.corrcoef(pred, targets[scan][:, j])[0, 1]))
                    start += n
        print(f"fold{k} done", flush=True)

    print(f"\n| Features (ridge, 5-fold CV, {len(scans)} held-out scans) | " + " | ".join(SHORT) + " | Avg. R |")
    print("|---|" + "---|" * (len(SHORT) + 1))
    labels = {"vigilance": "Vigilance index only (12 features)", "bands": "Five band powers, channel-averaged (60)",
              "full": "Full: 26 channels x 44 bins x 12 lags (13,728)"}
    for name in ("vigilance", "bands", "full"):
        per_roi = [np.mean(scores[(name, j)]) for j in range(len(ROIS))]
        print(f"| {labels[name]} | " + " | ".join(f"{v:.3f}" for v in per_roi) + f" | {np.mean(per_roi):.3f} |")


if __name__ == "__main__":
    main()
