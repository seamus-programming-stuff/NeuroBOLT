#!/usr/bin/env python3
"""How does cross-subject prediction improve with more training people? A ridge learning curve.

Uses the 5-fold, subject-grouped split (scan_split_cv5.xlsx). In each fold, ridge is trained on
random subsets of that fold's training people (both scans of a person together), its penalty is
chosen on the fold's validation people, and it is scored on the fold's held-out people. Features
(log band power, 1 Hz bins, 24 s / 12 lags by default) are computed once per scan and cached.

    python scripts/ridge_learning_curve.py --dataset-root $M3_DATA --split-sheet scan_split_cv5.xlsx \
        --cache features.npz --out learning_curve.csv

Writes one row per fold x subset size x repeat x held-out scan x ROI, and prints mean test R by the
number of training people.
"""
import argparse
import csv
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS, BAND_SETS, band_power_features, ridge_path  # noqa: E402
from eval_inter_per_scan import ROIS, load_scan  # noqa: E402


def cached_features(scans, args):
    if os.path.isfile(args.cache):
        z = np.load(args.cache)
        if all(f"x_{s}" in z for s in scans):
            return {s: (z[f"x_{s}"], z[f"y_{s}"]) for s in scans}
    data = {}
    for scan in scans:
        eeg, y = load_scan(scan, args.dataset_root, highpass=True, window_sec=args.window_sec)
        data[scan] = (band_power_features(eeg, BAND_SETS[args.bands], args.sub_windows), y.astype(np.float32))
        print(f"features {scan}: {data[scan][0].shape}", flush=True)
    np.savez(args.cache, **{f"x_{s}": x for s, (x, _) in data.items()}, **{f"y_{s}": y for s, (_, y) in data.items()})
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--bands", choices=sorted(BAND_SETS), default="fine")
    parser.add_argument("--window-sec", type=int, default=24)
    parser.add_argument("--sub-windows", type=int, default=12)
    parser.add_argument("--sizes", type=int, nargs="+", default=[3, 6, 9, 12], help="training people per subset")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    person = lambda scan: re.match(r"sub\d+", scan).group(0)  # noqa: E731
    all_scans = pd.read_excel(args.split_sheet, sheet_name="fold1")["scan_name"].tolist()
    data = cached_features(all_scans, args)
    rows = []
    for k in range(1, args.folds + 1):
        sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
        split = {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("train", "val", "test")}
        pool = sorted({person(s) for s in split["train"]})
        plans = [(m, r) for m in args.sizes if m < len(pool) for r in range(args.repeats)] + [(len(pool), 0)]
        for m, r in plans:
            rng = np.random.default_rng(1000 * k + 10 * m + r)
            chosen = set(rng.choice(pool, size=m, replace=False))
            train = [s for s in split["train"] if person(s) in chosen]
            x_train = np.concatenate([data[s][0] for s in train])
            mean, std = x_train.mean(axis=0), x_train.std(axis=0) + 1e-8
            scale = lambda scans: np.concatenate([(data[s][0] - mean) / std for s in scans])  # noqa: E731
            y_train = np.concatenate([data[s][1] for s in train])
            y_val = np.concatenate([data[s][1] for s in split["val"]])
            path = ridge_path((x_train - mean) / std, y_train, [scale(split["val"]), scale(split["test"])], ALPHAS)
            best = [min(path, key=lambda a: float(np.mean((path[a][0][:, j] - y_val[:, j]) ** 2)))
                    for j in range(len(ROIS))]
            start = 0
            for scan in split["test"]:
                n = len(data[scan][1])
                for j, (label, _) in enumerate(ROIS):
                    pred = path[best[j]][1][start:start + n, j]
                    rows.append({"fold": k, "people": m, "repeat": r, "scan": scan, "roi": label,
                                 "corr": float(np.corrcoef(pred, data[scan][1][:, j])[0, 1])})
                start += n
            print(f"fold{k} people={m} repeat={r}: test R {np.mean([x['corr'] for x in rows[-len(split['test']) * len(ROIS):]]):.3f}",
                  flush=True)

    with open(args.out, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("\npeople | mean test R (pooled over folds, scans, ROIs, repeats)")
    for m in sorted({r["people"] for r in rows}):
        values = [r["corr"] for r in rows if r["people"] == m]
        print(f"{m:6d} | {np.mean(values):.3f}  ({len(values)} scores)")


if __name__ == "__main__":
    main()
