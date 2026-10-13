#!/usr/bin/env python3
"""Score prediction ensembles built from the runs' saved best_predictions.npz files.

Every hypothesis run (and the ridge baselines) saves validation and test predictions at its
selected epoch. Averaging them over seeds, or across different models such as NeuroBOLT and the
band-power ridge, tests whether their errors are independent enough for an ensemble to beat each
member. Members are z-scored per scan before averaging, so a model with shrunken outputs gets an
equal vote; only R is reported, since z-scoring discards the MSE scale.

    python scripts/ensemble_predictions.py --root $M3_OUT/hypotheses \
        --ensemble base=base --ensemble base+ridge=base,ridge_bandpower

Each --ensemble is NAME=ARM[,ARM...]: seeds within an arm are averaged first, then arms with
equal weight. Arms with longer EEG windows lose a few frames at each scan's start, so members are
aligned on each scan's last frames.
"""
import argparse
import glob
import os

import numpy as np

ROIS = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior",
        "Putamen", "Thalamus", "global signal clean"]
SHORT = ["Cuneus", "Heschl's", "Mid. frontal", "Precuneus", "Putamen", "Thalamus", "Global"]


def zscore(x):
    return (x - x.mean()) / (x.std() + 1e-8)


def load_arm(root, arm, split):
    """{roi: [(pred, true, sizes), ...] one per seed} for one arm and split."""
    members = {roi: [] for roi in ROIS}
    for path in sorted(glob.glob(os.path.join(root, arm, "*", "seed*", "best_predictions.npz"))):
        if not os.path.isfile(os.path.join(os.path.dirname(path), "done")):
            continue
        z = np.load(path)
        rois = [str(r) for r in z["rois"]]
        for col, roi in enumerate(rois):
            if roi not in members:  # whole-brain runs predict regions outside the seven compared here
                continue
            members[roi].append((z[f"{split}_pred"].reshape(len(z[f"{split}_pred"]), -1)[:, col],
                                 z[f"{split}_true"].reshape(len(z[f"{split}_true"]), -1)[:, col],
                                 z[f"{split}_sizes"]))
    return members


def split_scans(values, sizes, keep):
    """Per-scan arrays, keeping each scan's last `keep[s]` frames."""
    out, start = [], 0
    for n, k in zip(sizes, keep):
        out.append(values[start + n - k:start + n])
        start += n
    return out


def common_frames(root, split):
    """Per-scan frame counts every finished run under root shares (as collect_hypotheses --aligned)."""
    sizes = [np.load(path)[f"{split}_sizes"]
             for path in glob.glob(os.path.join(root, "*", "*", "seed*", "best_predictions.npz"))
             if os.path.isfile(os.path.join(os.path.dirname(path), "done"))]
    return np.min(sizes, axis=0)


def score(members_by_arm, roi, keep=None):
    """Per-scan R of the ensemble for one ROI, or None if an arm has no runs for it."""
    runs = [members_by_arm[arm][roi] for arm in members_by_arm]
    if any(not seeds for seeds in runs):
        return None
    if keep is None:
        keep = np.min([sizes for seeds in runs for _, _, sizes in seeds], axis=0)
    true = split_scans(runs[0][0][1], runs[0][0][2], keep)
    arm_means = []
    for seeds in runs:
        per_seed = [[zscore(p) for p in split_scans(pred, sizes, keep)] for pred, _, sizes in seeds]
        arm_means.append([zscore(np.mean([seed[s] for seed in per_seed], axis=0)) for s in range(len(keep))])
    ensemble = [np.mean([arm[s] for arm in arm_means], axis=0) for s in range(len(keep))]
    return [float(np.corrcoef(e, t)[0, 1]) for e, t in zip(ensemble, true)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.join(os.environ.get(
        "M3_OUT", "/scratch/hz18/stay0060/NeuroBOLT/checkpoints"), "hypotheses"))
    parser.add_argument("--ensemble", action="append", required=True, help="NAME=ARM[,ARM...]")
    parser.add_argument("--split", default="test", choices=["val", "test"])
    parser.add_argument("--out", default=None, help="write ensembles.md here (default: print only)")
    parser.add_argument("--align-all", action="store_true",
                        help="score on the frames every run under --root shares, matching collect_hypotheses --aligned")
    args = parser.parse_args()
    keep = common_frames(args.root, args.split) if args.align_all else None

    cache = {}
    lines = [f"| Ensemble ({args.split} scans) | " + " | ".join(SHORT) + " | Avg. R |",
             "|---|" + "---|" * (len(SHORT) + 1)]
    for spec in args.ensemble:
        name, arms = spec.split("=", 1)
        members = {}
        for arm in arms.split(","):
            if arm not in cache:
                cache[arm] = load_arm(args.root, arm, args.split)
            members[arm] = cache[arm]
        per_roi = [score(members, roi, keep) for roi in ROIS]
        cells = [f"{np.mean(r):.3f}" if r else "–" for r in per_roi]
        avg = np.mean([np.mean(r) for r in per_roi]) if all(per_roi) else float("nan")
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {avg:.3f} |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, f"ensembles_{args.split}.md"), "w", encoding="utf-8") as stream:
            stream.write(text + "\n")


if __name__ == "__main__":
    main()
