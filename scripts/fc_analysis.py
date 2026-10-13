#!/usr/bin/env python3
"""Does each model reproduce the functional connectivity (FC) between the seven ROIs on held-out scans?

For every held-out scan, FC is the 7 x 7 correlation matrix of the ROI time series. Each model's
predicted FC is compared with the scan's true FC by correlating their 21 off-diagonal values
("FC similarity") and by their mean absolute difference. The reference is the population FC: the
average true FC over the five validation scans, compared with each test scan's true FC. A model
reproduces subject-specific connectivity only if it beats that reference.

    python scripts/fc_analysis.py --root $M3_OUT/hypotheses --arms base win24 multi7 m7_win24 ridge_fine_w24_sub12

All arms are scored on the frames every run under --root shares, like the aligned results table.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ensemble_predictions import ROIS, common_frames, load_arm, split_scans  # noqa: E402

UPPER = np.triu_indices(len(ROIS), k=1)


def fc(matrix):
    """Off-diagonal correlations between the columns (ROIs) of a frames x ROIs matrix."""
    return np.corrcoef(matrix.T)[UPPER]


def per_scan_series(members, keep, which):
    """[scan][seed] -> frames x 7 matrix of predictions (which=0) or truth (which=1)."""
    n_seeds = len(members[ROIS[0]])
    series = []
    for s in range(len(keep)):
        series.append([np.stack([split_scans(members[roi][k][which], members[roi][k][2], keep)[s] for roi in ROIS],
                                axis=1) for k in range(n_seeds)])
    return series


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.join(os.environ.get(
        "M3_OUT", "/scratch/hz18/stay0060/NeuroBOLT/checkpoints"), "hypotheses"))
    parser.add_argument("--arms", nargs="+", required=True)
    args = parser.parse_args()

    keep = {split: common_frames(args.root, split) for split in ("val", "test")}
    reference = load_arm(args.root, args.arms[0], "val")
    population = np.mean([fc(m[0]) for m in per_scan_series(reference, keep["val"], 1)], axis=0)
    truth = per_scan_series(load_arm(args.root, args.arms[0], "test"), keep["test"], 1)
    true_fc = [fc(scan[0]) for scan in truth]

    print("| Model | FC similarity (r) | FC mean absolute error |")
    print("|---|---|---|")
    sims = [np.corrcoef(population, t)[0, 1] for t in true_fc]
    errs = [np.mean(np.abs(population - t)) for t in true_fc]
    print(f"| Population FC (validation-scan average) | {np.mean(sims):.3f} ± {np.std(sims, ddof=1):.3f} | "
          f"{np.mean(errs):.3f} |")
    for arm in args.arms:
        members = load_arm(args.root, arm, "test")
        if any(not members[roi] for roi in ROIS):
            print(f"| {arm} | incomplete | |")
            continue
        preds = per_scan_series(members, keep["test"], 0)
        sims, errs = [], []
        for scan, t in zip(preds, true_fc):
            predicted = np.mean([fc(seed) for seed in scan], axis=0)  # average FC over seeds
            sims.append(np.corrcoef(predicted, t)[0, 1])
            errs.append(np.mean(np.abs(predicted - t)))
        print(f"| {arm} | {np.mean(sims):.3f} ± {np.std(sims, ddof=1):.3f} | {np.mean(errs):.3f} |")


if __name__ == "__main__":
    main()
