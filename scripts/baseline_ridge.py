#!/usr/bin/env python3
"""Band-power ridge regression baseline for inter-subject EEG-to-BOLD prediction.

Same scans, fold1 split, 16 s EEG windows and target preprocessing as the NeuroBOLT full_test runs,
but the network is replaced by log band power (delta, theta, alpha, beta, gamma) per channel in
four 4-second sub-windows, standardized on the training scans and fed to ridge regression. The
penalty is chosen per ROI by validation MSE, the rule main.py uses to choose epochs.

    python scripts/baseline_ridge.py --dataset-root $M3_DATA --out $M3_OUT/hypotheses/ridge_bandpower

Writes <out>/<ROI index>/seed0/log.txt in the one-row layout collect_hypotheses.py reads.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.signal import welch
from sklearn.linear_model import Ridge

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_inter_per_scan import ROIS, load_scan  # noqa: E402  (same preprocessing as the loader)

BANDS = [(1, 4), (4, 8), (8, 13), (13, 30), (30, 45)]  # Hz
SUB_WINDOWS = 4  # 16 s window -> four 4 s pieces, keeping coarse timing relative to the frame
ALPHAS = np.logspace(-1, 5, 13)


def band_power_features(eeg, fs=200):
    """(windows, channels, samples) -> (windows, channels * bands * sub-windows) log band power."""
    n, channels, samples = eeg.shape
    pieces = eeg.reshape(n, channels, SUB_WINDOWS, samples // SUB_WINDOWS)
    freqs, psd = welch(pieces, fs=fs, nperseg=fs, noverlap=fs // 2, axis=-1)
    power = np.stack([psd[..., (freqs >= lo) & (freqs < hi)].mean(axis=-1) for lo, hi in BANDS], axis=2)
    return np.log(power + 1e-12).reshape(n, -1)


def scan_scores(pred, true, sizes):
    corr, mse, start = [], [], 0
    for n in sizes:
        p, t = pred[start:start + n], true[start:start + n]
        start += n
        corr.append([float(np.corrcoef(p, t)[0, 1])])
        mse.append([float(np.mean((p - t) ** 2))])
    return corr, mse


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_example.xlsx")
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-highpass", action="store_true", help="skip the loader's 0.5 Hz EEG high-pass")
    args = parser.parse_args()

    sheet = pd.read_excel(args.split_sheet, sheet_name="fold1")
    data = {}
    for split in ("train", "val", "test"):
        feats, targets, sizes = [], [], []
        for scan in sheet.loc[sheet[split] == 1, "scan_name"]:
            eeg, y = load_scan(scan, args.dataset_root, highpass=not args.no_highpass)
            feats.append(band_power_features(eeg))
            targets.append(y)
            sizes.append(len(y))
            print(f"{split} {scan}: {len(y)} windows", flush=True)
        data[split] = (np.concatenate(feats), np.concatenate(targets), sizes)

    mean, std = data["train"][0].mean(axis=0), data["train"][0].std(axis=0) + 1e-8
    x = {split: (feats - mean) / std for split, (feats, _, _) in data.items()}

    for roi_index, (label, _) in enumerate(ROIS):
        y = {split: targets[:, roi_index] for split, (_, targets, _) in data.items()}
        fits = []
        for alpha in ALPHAS:
            model = Ridge(alpha=alpha).fit(x["train"], y["train"])
            fits.append((float(np.mean((model.predict(x["val"]) - y["val"]) ** 2)), alpha, model))
        val_mse, alpha, model = min(fits, key=lambda f: f[0])

        row = {"epoch": 0, "alpha": float(alpha)}
        for split in ("val", "test"):
            pred = model.predict(x[split])
            corr, mse = scan_scores(pred, y[split], data[split][2])
            row.update({f"{split}_mse": float(np.mean(mse)), f"{split}_corr": float(np.mean(corr)),
                        f"{split}_scan_corr": corr, f"{split}_scan_mse": mse})
        run_dir = os.path.join(args.out, str(roi_index), "seed0")
        os.makedirs(run_dir, exist_ok=True)
        with open(os.path.join(run_dir, "log.txt"), "w", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        open(os.path.join(run_dir, "done"), "w").close()
        print(f"{label:30s} alpha={alpha:g}  val R={row['val_corr']:.3f}  test R={row['test_corr']:.3f}")


if __name__ == "__main__":
    main()
