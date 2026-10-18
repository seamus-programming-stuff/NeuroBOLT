#!/usr/bin/env python3
"""How much does a few minutes of a person's own data improve the population model?

For every held-out scan, the first half (calibration) and the second half (evaluation) are separated
by a 25 s gap, longer than the 24 s EEG window, so no frame's input overlaps the other half.
Scored on the second half, mean over seven ROIs:
  population    the cross-validated eeg_full ridge prediction (trained on other people only)
  lag_adapted   the population prediction shifted by -3..+3 frames (±6 s), the shift chosen on the
                first half: a person-specific haemodynamic delay
  own_only      ridge on that person's 60 band powers, trained on the first half only
  stacked       ridge on [population prediction, 60 band powers], trained on the first half only
Also writes per-scan physiology summaries (heart-rate and slow-EOG fluctuation) and their Spearman
correlation with the population R, extending the earlier predictability analysis.

    python scripts/interp_personal.py --eeg-cache features_fine_w24_sub12.npz --interp-cache interp_cache.npz \
        --cv-predictions $M3_OUT/interp/cv_A/predictions_eeg_full.npz --out $M3_OUT/interp/personal
"""
import argparse
import csv
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS  # noqa: E402
from eval_inter_per_scan import ROIS  # noqa: E402
from interp_cv import BANDS, as_cube, band_power  # noqa: E402

GAP = 12  # frames (25 s)
SHIFTS = range(-3, 4)


def ridge_inner(x, y, x_eval, n_folds=4):
    """Ridge with the penalty chosen by contiguous-block CV inside the calibration half."""
    mean, std = x.mean(axis=0), x.std(axis=0) + 1e-8
    xs, xe = (x - mean) / std, (x_eval - mean) / std
    blocks = np.array_split(np.arange(len(x)), n_folds)
    def fit(a, xt, yt):
        xm, ym = xt.mean(axis=0), yt.mean(axis=0)
        w = np.linalg.solve((xt - xm).T @ (xt - xm) + a * np.eye(xt.shape[1]), (xt - xm).T @ (yt - ym))
        return lambda z: (z - xm) @ w + ym
    err = {}
    for a in ALPHAS:
        e = 0.0
        for b in blocks:
            keep = np.setdiff1d(np.arange(len(x)), np.arange(max(b[0] - GAP, 0), min(b[-1] + GAP + 1, len(x))))
            e += float(np.mean((fit(a, xs[keep], y[keep])(xs[b]) - y[b]) ** 2))
        err[a] = e
    best = min(err, key=err.get)
    return fit(best, xs, y)(xe)


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg-cache", required=True)
    parser.add_argument("--interp-cache", required=True)
    parser.add_argument("--cv-predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    eeg, aux, cvp = np.load(args.eeg_cache), np.load(args.interp_cache), np.load(args.cv_predictions)
    labels = [str(s) for s in aux["labels"]]
    cols = [labels.index(label) for label, _ in ROIS]
    targets = [str(t) for t in cvp["targets"]]
    pcols = [targets.index(f"all65|{label}") for label, _ in ROIS]
    rows, summary = [], []
    for scan in (str(s) for s in aux["scans"]):
        x = eeg[f"x_{scan}"]
        cube = as_cube(x)
        bands = np.concatenate([band_power(cube, lo, hi) for lo, hi in BANDS.values()], axis=1)
        y = aux[f"y_all_{scan}"][:, cols]
        pop = cvp[f"pred_{scan}"][:, pcols]
        n = len(y)
        half = n // 2
        cal, ev = np.arange(0, half - GAP), np.arange(half, n)
        for j, (label, _) in enumerate(ROIS):
            r = {"scan": scan, "roi": label, "population": corr(pop[ev, j], y[ev, j])}
            # person-specific delay: shift the population prediction, choose the shift on the calibration half
            fits = {}
            for s in SHIFTS:
                idx = np.clip(cal - s, 0, n - 1)
                fits[s] = corr(pop[idx, j], y[cal, j])
            best = max(fits, key=fits.get)
            r["lag_adapted"] = corr(pop[np.clip(ev - best, 0, n - 1), j], y[ev, j])
            r["chosen_shift_frames"] = best
            r["own_only"] = corr(ridge_inner(bands[cal], y[cal, j], bands[ev]), y[ev, j])
            stacked = np.concatenate([pop[:, [j]], bands], axis=1)
            r["stacked"] = corr(ridge_inner(stacked[cal], y[cal, j], stacked[ev]), y[ev, j])
            rows.append(r)
        hr = aux[f"hr_{scan}"][:, -1]
        eog_slow = aux[f"eog_{scan}"].reshape(n, 2, 7, 12)[:, :, :2, -1].mean(axis=(1, 2))
        summary.append({"scan": scan, "population_r": float(np.mean([corr(pop[:, j], y[:, j]) for j in range(len(cols))])),
                        "hr_mean": float(hr.mean()), "hr_sd": float(hr.std()), "eog_slow_sd": float(eog_slow.std()),
                        "median_hr": float(aux[f"median_hr_{scan}"])})
        print(f"{scan}: " + " ".join(f"{k}={np.mean([r[k] for r in rows[-len(cols):]]):.3f}"
                                      for k in ("population", "lag_adapted", "own_only", "stacked")), flush=True)
    for name, table in (("personal.csv", rows), ("scan_physiology.csv", summary)):
        with open(os.path.join(args.out, name), "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=table[0].keys())
            writer.writeheader()
            writer.writerows(table)
    print("\nmean over scans x ROIs (second half of each scan):")
    for k in ("population", "lag_adapted", "own_only", "stacked"):
        print(f"  {k:12s} {np.mean([r[k] for r in rows]):.3f}")
    r = np.array([s["population_r"] for s in summary])
    for key in ("hr_sd", "eog_slow_sd", "hr_mean"):
        v = np.array([s[key] for s in summary])
        ok = np.isfinite(v) & (v > 0)
        rho, p = stats.spearmanr(v[ok], r[ok])
        print(f"Spearman population R vs {key}: rho={rho:+.2f} p={p:.3f} (n={ok.sum()})")


if __name__ == "__main__":
    main()
