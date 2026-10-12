#!/usr/bin/env python3
"""Band-power ridge regression baseline for inter-subject EEG-to-BOLD prediction.

Same scans, fold1 split, EEG windows and target preprocessing as the NeuroBOLT full_test runs,
but the network is replaced by log band power per channel in consecutive sub-windows (a coarse
lag design), standardized on the training scans and fed to ridge regression. The penalty is
chosen per ROI by validation MSE, the rule main.py uses to choose epochs.

    python scripts/baseline_ridge.py --dataset-root $M3_DATA --out $M3_OUT/hypotheses/ridge_bandpower

Writes <out>/<ROI index>/seed0/log.txt in the one-row layout collect_hypotheses.py reads, plus
best_predictions.npz with the same keys main.py writes, so ridge can join prediction ensembles.
"""
import argparse
import json
import os
import sys

import itertools

import numpy as np
import pandas as pd
import torch
from scipy.signal import welch
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_inter_per_scan import ROIS, load_scan  # noqa: E402  (same preprocessing as the loader)

BAND_SETS = {
    "classic": [(1, 4), (4, 8), (8, 13), (13, 30), (30, 45)],  # delta .. gamma, Hz
    "fine": [(f, f + 1) for f in range(1, 45)],  # 1 Hz bins
}
ALPHAS = np.logspace(-1, 6, 15)
HGB_GRID = [  # gradient-boosted trees, to test whether a nonlinear map of the same features helps
    {"learning_rate": 0.05, "max_iter": iters, "max_leaf_nodes": leaves, "l2_regularization": l2}
    for iters, leaves, l2 in itertools.product((200, 500), (15, 31), (0.0, 1.0))]


def candidate_models(estimator):
    if estimator == "ridge":
        return [(f"alpha={a:g}", Ridge(alpha=a)) for a in ALPHAS]
    return [(" ".join(f"{k}={v}" for k, v in params.items()),
             HistGradientBoostingRegressor(early_stopping=False, random_state=0, **params)) for params in HGB_GRID]


def ridge_path(x_train, y_train, x_eval, alphas):
    """{alpha: [predictions for each array in x_eval]} for ridge with an intercept, all targets at once.

    One economy SVD of the centred training features, X = U S V', gives every penalty's weights
    as V diag(S / (S^2 + alpha)) U'y, so a wide feature set costs one decomposition instead of a
    solve per penalty and ROI. Matches sklearn's Ridge(alpha, fit_intercept=True).

    The algebra runs in torch: the M3 env's numpy links single-threaded reference LAPACK, while
    torch uses MKL across every core SLURM grants.
    """
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))
    as_tensor = lambda a: torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32))  # noqa: E731
    x, y = as_tensor(x_train), as_tensor(y_train)
    x_mean, y_mean = x.mean(dim=0), y.mean(dim=0)
    u, s, vt = torch.linalg.svd(x - x_mean, full_matrices=False)
    uty = u.T @ (y - y_mean)
    rotated = [(as_tensor(e) - x_mean) @ vt.T for e in x_eval]
    return {alpha: [(r @ ((s / (s ** 2 + alpha))[:, None] * uty) + y_mean).numpy() for r in rotated]
            for alpha in alphas}


def band_power_features(eeg, bands, sub_windows, fs=200):
    """(windows, channels, samples) -> (windows, channels * bands * sub-windows) log band power."""
    n, channels, samples = eeg.shape
    pieces = eeg.reshape(n, channels, sub_windows, samples // sub_windows)
    freqs, psd = welch(pieces, fs=fs, nperseg=min(fs, samples // sub_windows), axis=-1)
    power = np.stack([psd[..., (freqs >= lo) & (freqs < hi)].mean(axis=-1) for lo, hi in bands], axis=2)
    return np.log(power + 1e-12).reshape(n, -1).astype(np.float32)


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
    parser.add_argument("--window-sec", type=int, default=16, help="seconds of EEG history per fMRI frame")
    parser.add_argument("--sub-windows", type=int, default=4, help="consecutive pieces (lags) per window")
    parser.add_argument("--bands", choices=sorted(BAND_SETS), default="classic")
    parser.add_argument("--per-scan-zscore", action="store_true",
                        help="standardize each feature within each scan (uses only that scan's EEG), "
                             "removing between-subject differences in overall band power")
    parser.add_argument("--estimator", choices=["ridge", "hgb"], default="ridge",
                        help="ridge regression, or histogram gradient-boosted trees on the same features")
    args = parser.parse_args()
    bands = BAND_SETS[args.bands]

    sheet = pd.read_excel(args.split_sheet, sheet_name="fold1")
    data = {}
    for split in ("train", "val", "test"):
        feats, targets, names = [], [], []
        for scan in sheet.loc[sheet[split] == 1, "scan_name"]:
            eeg, y = load_scan(scan, args.dataset_root, highpass=not args.no_highpass, window_sec=args.window_sec)
            scan_feats = band_power_features(eeg, bands, args.sub_windows)
            if args.per_scan_zscore:
                scan_feats = (scan_feats - scan_feats.mean(axis=0)) / (scan_feats.std(axis=0) + 1e-8)
            feats.append(scan_feats)
            targets.append(y)
            names.append(scan)
            print(f"{split} {scan}: {len(y)} windows, {feats[-1].shape[1]} features", flush=True)
        data[split] = (np.concatenate(feats), np.concatenate(targets), [len(t) for t in targets], names)

    mean, std = data["train"][0].mean(axis=0), data["train"][0].std(axis=0) + 1e-8
    x = {split: (feats - mean) / std for split, (feats, _, _, _) in data.items()}
    if args.estimator == "ridge":  # every penalty for every ROI from one decomposition
        path = ridge_path(x["train"], data["train"][1], [x["val"], x["test"]], ALPHAS)

    for roi_index, (label, _) in enumerate(ROIS):
        y = {split: targets[:, roi_index] for split, (_, targets, _, _) in data.items()}
        if args.estimator == "ridge":
            fits = [(float(np.mean((preds[0][:, roi_index] - y["val"]) ** 2)), f"alpha={alpha:g}",
                     {"val": preds[0][:, roi_index], "test": preds[1][:, roi_index]})
                    for alpha, preds in path.items()]
        else:
            fits = []
            for name, model in candidate_models(args.estimator):
                model.fit(x["train"], y["train"])
                val_pred = model.predict(x["val"])
                fits.append((float(np.mean((val_pred - y["val"]) ** 2)), name,
                             {"val": val_pred, "test": model.predict(x["test"])}))
        _, chosen, predictions = min(fits, key=lambda f: f[0])

        row, outputs = {"epoch": 0, "chosen": chosen}, {"epoch": 0}
        for split in ("val", "test"):
            pred = predictions[split]
            corr, mse = scan_scores(pred, y[split], data[split][2])
            row.update({f"{split}_mse": float(np.mean(mse)), f"{split}_corr": float(np.mean(corr)),
                        f"{split}_scan_corr": corr, f"{split}_scan_mse": mse})
            outputs.update({f"{split}_pred": pred[:, None], f"{split}_true": y[split][:, None],
                            f"{split}_scans": np.array(data[split][3]), f"{split}_sizes": np.array(data[split][2])})
        run_dir = os.path.join(args.out, str(roi_index), "seed0")
        os.makedirs(run_dir, exist_ok=True)
        with open(os.path.join(run_dir, "log.txt"), "w", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        np.savez_compressed(os.path.join(run_dir, "best_predictions.npz"), **outputs, rois=np.array([label]))
        open(os.path.join(run_dir, "done"), "w").close()
        print(f"{label:30s} {chosen}  val R={row['val_corr']:.3f}  test R={row['test_corr']:.3f}")


if __name__ == "__main__":
    main()
