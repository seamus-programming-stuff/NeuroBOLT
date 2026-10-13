#!/usr/bin/env python3
"""Five-fold, subject-grouped comparison of the best models over every scan (scan_split_cv5.xlsx).

Each fold's runs live in <root>/fold<k>/<arm>/... (fold 1 links to the authors'-split runs). Within a
fold, every arm is rescored on the frames all its arms share; then the held-out scans of all folds
are pooled, so each of the 29 scans (22 people) is scored exactly once by each arm.

    python scripts/summarize_cv.py --root $M3_OUT/cv --arms multi7 m7_win24 ridge_fine_w24_sub12

Reports mean test R per ROI over people, per-fold means, and paired differences between arms with
95% t-intervals over people (a person's two scans are averaged first, so people are the unit).
"""
import argparse
import math
import os
import re
import sys
from collections import defaultdict

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_hypotheses import ROIS, SHORT, collect  # noqa: E402
from plot_hypotheses import LABELS  # noqa: E402


def interval(values):
    values = np.asarray(values, dtype=float)
    half = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / math.sqrt(len(values))
    return values.mean(), values.mean() - half, values.mean() + half


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True)
    parser.add_argument("--arms", nargs="+", required=True)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    # (arm, roi, scan) -> R averaged over seeds; fold of each scan
    cells, fold_of = defaultdict(list), {}
    for k in range(1, args.folds + 1):
        fold_root = os.path.join(args.root, f"fold{k}")
        records, _ = collect(fold_root, aligned=True)
        for r in records:
            if r["split"] == "test" and r["arm"] in args.arms:
                cells[(r["arm"], r["roi"], r["scan"])].append(r["corr"])
                fold_of[r["scan"]] = k
    scans = sorted(fold_of)
    people = sorted({re.match(r"sub\d+", s).group(0) for s in scans})
    score = {key: float(np.mean(v)) for key, v in cells.items()}

    def per_person(arm, rois=ROIS):
        """{person: R averaged over ROIs and that person's scans} where every cell exists."""
        out = {}
        for person in people:
            values = [score[(arm, roi, s)] for s in scans if s.startswith(person) for roi in rois
                      if (arm, roi, s) in score]
            expected = len([s for s in scans if s.startswith(person)]) * len(rois)
            if len(values) == expected:
                out[person] = float(np.mean(values))
        return out

    print(f"{len(scans)} held-out scans from {len(people)} people across {args.folds} folds\n")
    print("| Model | " + " | ".join(SHORT) + " | Avg. R over people | 95% CI |")
    print("|---|" + "---|" * (len(SHORT) + 2))
    for arm in args.arms:
        rois = []
        for roi in ROIS:
            by_person = per_person(arm, [roi])
            rois.append(f"{np.mean(list(by_person.values())):.3f}" if len(by_person) == len(people) else "–")
        overall = per_person(arm)
        if len(overall) == len(people):
            mean, lo, hi = interval(list(overall.values()))
            print(f"| {LABELS.get(arm, arm)} | " + " | ".join(rois) + f" | {mean:.3f} | {lo:.3f} to {hi:.3f} |")
        else:
            print(f"| {LABELS.get(arm, arm)} | " + " | ".join(rois) + f" | {len(overall)}/{len(people)} people | |")

    print("\n| Fold | Test people | " + " | ".join(LABELS.get(a, a) for a in args.arms) + " |")
    print("|---|---|" + "---|" * len(args.arms))
    for k in range(1, args.folds + 1):
        fold_scans = [s for s in scans if fold_of[s] == k]
        fold_people = sorted({re.match(r"sub\d+", s).group(0) for s in fold_scans})
        row = []
        for arm in args.arms:
            values = [score[(arm, roi, s)] for s in fold_scans for roi in ROIS if (arm, roi, s) in score]
            row.append(f"{np.mean(values):.3f}" if len(values) == len(fold_scans) * len(ROIS) else "–")
        print(f"| {k} | {', '.join(p.replace('sub', '') for p in fold_people)} | " + " | ".join(row) + " |")

    print("\n| Comparison (paired over people) | Mean Δ R | 95% CI | People favouring the first |")
    print("|---|---|---|---|")
    for i, a in enumerate(args.arms):
        for b in args.arms[i + 1:]:
            pa, pb = per_person(a), per_person(b)
            shared = [p for p in people if p in pa and p in pb]
            if len(shared) < 3:
                continue
            diffs = [pa[p] - pb[p] for p in shared]
            mean, lo, hi = interval(diffs)
            print(f"| {LABELS.get(a, a)} − {LABELS.get(b, b)} | {mean:+.3f} | {lo:+.3f} to {hi:+.3f} | "
                  f"{sum(d > 0 for d in diffs)} of {len(diffs)} |")


if __name__ == "__main__":
    main()
