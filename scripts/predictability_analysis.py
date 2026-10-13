#!/usr/bin/env python3
"""Exploratory: which scan properties go with how predictable a scan's BOLD is from its EEG?

Per scan, the outcome is the cross-validated ridge R (from ridge_learning_curve.py, each fold's full
training set), averaged over the seven ROIs. Candidate explanations, from the cached log band-power
features (most recent 2 s lag bin, averaged over channels):
  - alpha (8-13 Hz) and theta (4-8 Hz) power: scan mean and fluctuation (SD over time)
  - high-frequency (30-45 Hz) power, a proxy for residual muscle and scanner artefact
Spearman correlations over the 29 scans; exploratory, uncorrected. Raw BOLD amplitude cannot be
tested: the released ROI time series are already standardized (every scan's SD is 1).

    python scripts/predictability_analysis.py --cache features.npz --curve learning_curve.csv
"""
import argparse
import csv
from collections import defaultdict

import numpy as np
from scipy import stats

FREQS = np.arange(1, 45) + 0.5  # 1 Hz bins of BAND_SETS["fine"], by centre
N_CHANNELS, N_BANDS, N_LAGS = 26, 44, 12


def band(log_power, lo, hi):
    """Channel-averaged log power in [lo, hi) Hz per window, from the most recent lag bin."""
    x = log_power.reshape(len(log_power), N_CHANNELS, N_BANDS, N_LAGS)[:, :, :, -1]
    return x[:, :, (FREQS >= lo) & (FREQS < hi)].mean(axis=(1, 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--curve", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.curve, encoding="utf-8")))
    full = {}
    for r in rows:  # each fold's largest training set
        full[int(r["fold"])] = max(full.get(int(r["fold"]), 0), int(r["people"]))
    outcome = defaultdict(list)
    for r in rows:
        if int(r["people"]) == full[int(r["fold"])]:
            outcome[r["scan"]].append(float(r["corr"]))

    z = np.load(args.cache)
    table = []
    for scan in sorted(outcome):
        x = z[f"x_{scan}"]
        alpha, theta, high = band(x, 8, 13), band(x, 4, 8), band(x, 30, 45)
        table.append({"scan": scan, "ridge_R": float(np.mean(outcome[scan])),
                      "alpha_mean": float(alpha.mean()), "alpha_sd": float(alpha.std()),
                      "theta_mean": float(theta.mean()), "theta_sd": float(theta.std()),
                      "high_freq_mean": float(high.mean())})
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=table[0].keys())
            writer.writeheader()
            writer.writerows(table)

    r = np.array([t["ridge_R"] for t in table])
    print(f"{len(table)} scans; ridge R from {r.min():.2f} to {r.max():.2f}\n")
    print("| Scan property | Spearman ρ with ridge R | p |")
    print("|---|---|---|")
    for key in ("alpha_sd", "theta_sd", "alpha_mean", "theta_mean", "high_freq_mean"):
        rho, p = stats.spearmanr([t[key] for t in table], r)
        print(f"| {key} | {rho:+.2f} | {p:.3f} |")
    print("\nHardest and easiest scans:")
    for t in sorted(table, key=lambda t: t["ridge_R"])[:4] + sorted(table, key=lambda t: t["ridge_R"])[-3:]:
        print(f"  {t['scan']}: R {t['ridge_R']:.3f}, alpha SD {t['alpha_sd']:.3f}, theta SD {t['theta_sd']:.3f}, "
              f"high-freq {t['high_freq_mean']:.2f}")


if __name__ == "__main__":
    main()
