#!/usr/bin/env python3
"""Descriptive maps of the EEG-BOLD relation: model-free correlations, model patterns, and an empirical HRF.

1. Model-free coupling. Within each scan, the correlation of every EEG feature (channel x 1 Hz bin
   x lag) with each region's BOLD, averaged over the 29 scans (Fisher z), with a t-statistic over
   scans. Saved in full for the seven ROIs and channel-averaged by band for all 65 targets.
2. Model patterns (Haufe et al. 2014). Ridge weights are filters: with correlated features their
   sign and size need not show what drives the prediction. The pattern is the covariance of each
   feature with the model's prediction; computed within scan from the cross-validated eeg_full
   predictions of interp_cv.py and averaged over scans, as a correlation.
3. A rank-1 separable model (weights = channel pattern x spectrum x lag profile, by alternating
   ridge) per ROI, penalty chosen by 5-fold CV, refitted on all scans and on every
   leave-one-person-out subset, so each factor gets a jackknife interval. The lag profile is the
   EEG-to-BOLD impulse response the data support, to compare with the canonical HRF.

    python scripts/interp_maps.py --eeg-cache features_fine_w24_sub12.npz --interp-cache interp_cache.npz \
        --cv-predictions $M3_OUT/interp/cv_A/predictions_eeg_full.npz --out $M3_OUT/interp/maps
"""
import argparse
import os
import re
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import cp_regression  # noqa: E402
from eval_inter_per_scan import ROIS  # noqa: E402
from interp_cv import BANDS, LAG_CENTRES, N_BINS, N_CH, N_LAGS, as_cube, band_power  # noqa: E402

CP_ALPHAS = np.logspace(1, 5, 5)


def zscore(a, axis=0):
    return (a - a.mean(axis=axis, keepdims=True)) / (a.std(axis=axis, keepdims=True) + 1e-8)


def within_scan_corr(x, y):
    """(features,) x (n, targets) -> (features, targets) correlations within one scan."""
    return zscore(x).T @ zscore(y) / len(x)


def summarise(per_scan):
    """Fisher-z mean over scans (back to r) and one-sample t over scans."""
    zs = np.arctanh(np.clip(np.stack(per_scan), -0.999, 0.999))
    t = zs.mean(axis=0) / (zs.std(axis=0, ddof=1) / np.sqrt(len(zs)))
    return np.tanh(zs.mean(axis=0)).astype(np.float32), t.astype(np.float32)


def orient(factors):
    """Fix the rank-1 sign ambiguity: lag profile and channel pattern sum positive; the spectrum carries the sign."""
    chan, spec, lag = (f.copy() for f in factors)
    if lag.sum() < 0:
        lag, spec = -lag, -spec
    if chan.sum() < 0:
        chan, spec = -chan, -spec
    scale = np.abs(lag).max() * np.abs(chan).max()
    return chan / np.abs(chan).max(), spec * scale, lag / np.abs(lag).max()


def cp_factors(x, y, alpha, shape, seed=0, iters=25):
    """Rank-1 CP regression factors on standardized features (same algorithm as baseline_ridge.cp_regression)."""
    gen = torch.Generator().manual_seed(seed)
    xt = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).reshape(len(x), *shape)
    yc = torch.from_numpy((y - y.mean()).astype(np.float32))
    factors = [torch.randn(size, 1, generator=gen) * 0.1 for size in shape]
    specs = ["ncfl,fr,lr->ncr", "ncfl,cr,lr->nfr", "ncfl,cr,fr->nlr"]
    for _ in range(iters):
        for k, spec in enumerate(specs):
            others = [factors[j] for j in range(3) if j != k]
            z = torch.einsum(spec, xt, *others).reshape(len(xt), -1)
            factors[k] = torch.linalg.solve(z.T @ z + alpha * torch.eye(z.shape[1]), z.T @ yc).reshape(shape[k], 1)
    return orient([f[:, 0].numpy() for f in factors])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg-cache", required=True)
    parser.add_argument("--interp-cache", required=True)
    parser.add_argument("--cv-predictions", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))
    os.makedirs(args.out, exist_ok=True)

    eeg, aux, cvp = np.load(args.eeg_cache), np.load(args.interp_cache), np.load(args.cv_predictions)
    labels = [str(s) for s in aux["labels"]]
    scans = [str(s) for s in aux["scans"]]
    roi_cols = [labels.index(label) for label, _ in ROIS]
    cv_targets = [str(t) for t in cvp["targets"]]
    cv_cols = [cv_targets.index(f"all65|{label}") for label, _ in ROIS]

    # 1-2. correlation maps
    full_r, pattern_r, band_r = [], [], []
    for scan in scans:
        x, y = eeg[f"x_{scan}"], aux[f"y_all_{scan}"]
        full_r.append(within_scan_corr(x, y[:, roi_cols]))
        pattern_r.append(within_scan_corr(x, cvp[f"pred_{scan}"][:, cv_cols]))
        cube = as_cube(x)
        bands = np.stack([band_power(cube, lo, hi) for lo, hi in BANDS.values()], axis=1)  # (n, 5, lags)
        band_r.append(within_scan_corr(bands.reshape(len(x), -1), y).reshape(len(BANDS), N_LAGS, -1))
        print(f"maps {scan}", flush=True)
    coupling, coupling_t = summarise(full_r)
    pattern, pattern_t = summarise(pattern_r)
    band_coupling, band_t = summarise(band_r)
    shape4 = lambda a: a.T.reshape(len(ROIS), N_CH, N_BINS, N_LAGS)  # noqa: E731

    # 3. rank-1 separable model: choose the penalty by CV, then fit on everything and jackknife
    person = lambda s: re.match(r"sub\d+", s).group(0)  # noqa: E731
    xs = {s: eeg[f"x_{s}"] for s in scans}
    ys = {s: aux[f"y_all_{s}"][:, roi_cols] for s in scans}
    shape = (N_CH, N_BINS, N_LAGS)
    cv_r = {}
    for k in range(1, 6):
        sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
        train = sheet.loc[(sheet["train"] == 1) | (sheet["val"] == 1), "scan_name"].tolist()
        test = sheet.loc[sheet["test"] == 1, "scan_name"].tolist()
        xtr = np.concatenate([xs[s] for s in train])
        mean, std = xtr.mean(axis=0), xtr.std(axis=0) + 1e-8
        xtr = (xtr - mean) / std
        xte = [(xs[s] - mean) / std for s in test]
        for j in range(len(ROIS)):
            ytr = np.concatenate([ys[s][:, j] for s in train])
            for alpha in CP_ALPHAS:
                preds = cp_regression(xtr, ytr, xte, 1, alpha, shape)
                cv_r.setdefault((j, alpha), []).extend(
                    float(np.corrcoef(p, ys[s][:, j])[0, 1]) for p, s in zip(preds, test))
        print(f"rank-1 CV fold{k}", flush=True)
    best_alpha = [max(CP_ALPHAS, key=lambda a: np.mean(cv_r[(j, a)])) for j in range(len(ROIS))]
    rank1_cv = [float(np.mean(cv_r[(j, a)])) for j, a in enumerate(best_alpha)]
    print("rank-1 CV R:", dict(zip([r for r, _ in ROIS], np.round(rank1_cv, 3))), flush=True)

    people = sorted({person(s) for s in scans})
    fits = {}
    for left_out in [None] + people:
        keep = [s for s in scans if person(s) != left_out]
        xall = np.concatenate([xs[s] for s in keep])
        xall = (xall - xall.mean(axis=0)) / (xall.std(axis=0) + 1e-8)
        for j in range(len(ROIS)):
            fits[(left_out, j)] = cp_factors(xall, np.concatenate([ys[s][:, j] for s in keep]), best_alpha[j], shape)
        print(f"rank-1 fit without {left_out}", flush=True)
    factor = lambda which, lo: np.stack([fits[(lo, j)][which] for j in range(len(ROIS))])  # noqa: E731
    jack = {w: np.stack([factor(w, p) for p in people]) for w in range(3)}  # (people, ROI, size)
    n = len(people)
    jack_se = {w: np.sqrt((n - 1) / n * ((jack[w] - jack[w].mean(axis=0)) ** 2).sum(axis=0)) for w in range(3)}

    np.savez_compressed(
        os.path.join(args.out, "maps.npz"), rois=np.array([r for r, _ in ROIS]), labels=np.array(labels),
        bands=np.array(list(BANDS)), lag_centres=LAG_CENTRES,
        coupling=shape4(coupling), coupling_t=shape4(coupling_t), pattern=shape4(pattern), pattern_t=shape4(pattern_t),
        band_coupling=band_coupling, band_coupling_t=band_t,  # (5 bands, 12 lags, 65 targets)
        rank1_channel=factor(0, None), rank1_spectrum=factor(1, None), rank1_lag=factor(2, None),
        rank1_channel_se=jack_se[0], rank1_spectrum_se=jack_se[1], rank1_lag_se=jack_se[2],
        rank1_lag_jack=jack[2], rank1_cv_r=np.array(rank1_cv), rank1_alpha=np.array(best_alpha))
    print(f"Wrote {args.out}/maps.npz")


if __name__ == "__main__":
    main()
