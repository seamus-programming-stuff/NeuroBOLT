#!/usr/bin/env python3
"""Compare inter-subject hypothesis arms with the baseline arm, matched by seed, ROI and held-out scan.

Reads <root>/<arm>/<ROI index | all>/seed<k>/log.txt as written by hypotheses_m3.sbatch (or a
one-row log.txt from a non-neural baseline). Every run is scored at its min-validation-MSE epoch,
where main.py logs per-scan R for each validation and test scan.

    python scripts/collect_hypotheses.py --root $M3_OUT/hypotheses --out <dir>

Writes runs.csv (one row per arm x seed x ROI x split x scan) and summary.md. Arms are compared
on validation scans first: decisions should rest on those, with the six test scans as the
confirmation, since every arm is scored on the same test scans.

With --aligned, scores are recomputed from each run's best_predictions.npz on the frames every
arm shares: arms with longer EEG windows lose a few frames at each scan's start, so each scan is
cut to its last K frames, K being the smallest window count any arm has for that scan.
"""
import argparse
import csv
import json
import os
from collections import defaultdict

import numpy as np

ROIS = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior",
        "Putamen", "Thalamus", "global signal clean"]
SHORT = ["Cuneus", "Heschl's", "Mid. frontal", "Precuneus", "Putamen", "Thalamus", "Global"]
SPLIT_SCANS = {  # fold1 of scan_split_example.xlsx, in sheet order (the order main.py logs them)
    "val": ["sub06-scan01", "sub13-scan01", "sub13-scan02", "sub15-scan01", "sub22-scan01"],
    "test": ["sub07-scan01", "sub07-scan02", "sub11-scan01", "sub16-scan01", "sub18-scan01", "sub21-scan01"],
}


def read_run(run_dir):
    path = os.path.join(run_dir, "log.txt")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    rows = [r for r in rows if "test_scan_corr" in r]
    if not rows:
        return None
    extra = os.path.join(run_dir, "extra_args.txt")
    if os.path.isfile(extra) and "--train_on_val" in open(extra, encoding="utf-8").read():
        best = rows[-1]  # validation scans were trained on, so the run stops at a preset epoch
    else:
        best = min(rows, key=lambda r: r["val_mse"])
    return {"best": best, "epochs_run": len(rows), "done": os.path.isfile(os.path.join(run_dir, "done"))}


def finished_runs(root):
    """(arm, key, seed directory, run) for every finished run under root."""
    for arm in sorted(os.listdir(root)):
        arm_dir = os.path.join(root, arm)
        if not os.path.isdir(arm_dir):
            continue
        for key in sorted(os.listdir(arm_dir)):
            key_dir = os.path.join(arm_dir, key)
            if not os.path.isdir(key_dir):
                continue
            for seed_dir in sorted(os.listdir(key_dir)):
                run = read_run(os.path.join(key_dir, seed_dir))
                if run is not None and run["done"]:
                    yield arm, key, os.path.join(key_dir, seed_dir), run


def aligned_scores(run_dir, split, keep):
    """Per-scan (R, MSE) lists per output, scoring each scan's last keep[s] frames, and the scan names."""
    z = np.load(os.path.join(run_dir, "best_predictions.npz"))
    names = [str(s) for s in z[f"{split}_scans"]] if len(z[f"{split}_scans"]) else SPLIT_SCANS[split]
    pred = z[f"{split}_pred"].reshape(len(z[f"{split}_pred"]), -1)
    true = z[f"{split}_true"].reshape(len(z[f"{split}_true"]), -1)
    corr, mse, start = [], [], 0
    for n, k in zip(z[f"{split}_sizes"], keep):
        p, t = pred[start + n - k:start + n], true[start + n - k:start + n]
        start += n
        corr.append([float(np.corrcoef(p[:, j], t[:, j])[0, 1]) for j in range(p.shape[1])])
        mse.append([float(np.mean((p[:, j] - t[:, j]) ** 2)) for j in range(p.shape[1])])
    return corr, mse, names


def collect(root, aligned=False):
    runs = list(finished_runs(root))
    keep = {}
    if aligned:  # frames every run has, per scan
        missing = [run_dir for _, _, run_dir, _ in runs
                   if not os.path.isfile(os.path.join(run_dir, "best_predictions.npz"))]
        for run_dir in missing:
            print(f"skipping {run_dir}: no best_predictions.npz to rescore")
        runs = [r for r in runs if r[2] not in missing]
        for split in ("val", "test"):
            sizes = [np.load(os.path.join(run_dir, "best_predictions.npz"))[f"{split}_sizes"]
                     for _, _, run_dir, _ in runs]
            keep[split] = np.min(sizes, axis=0)
    records = []
    for arm, key, run_dir, run in runs:
        if key == "all":  # shared model: map outputs to ROIs by name (whole-brain runs have 65 outputs)
            npz = os.path.join(run_dir, "best_predictions.npz")
            names = ([str(r) for r in np.load(npz)["rois"]] if os.path.isfile(npz) else ROIS)
            outputs = [(i, ROIS.index(n)) for i, n in enumerate(names) if n in ROIS]
        else:
            outputs = [(0, int(key))]
        best = run["best"]
        for split in ("val", "test"):
            if aligned:
                scan_corr, scan_mse, names = aligned_scores(run_dir, split, keep[split])
            else:  # logs carry no scan names; they follow the authors' fold1 order
                scan_corr, scan_mse, names = best[f"{split}_scan_corr"], best[f"{split}_scan_mse"], SPLIT_SCANS[split]
            for s, (corrs, mses) in enumerate(zip(scan_corr, scan_mse)):
                for out, roi_index in outputs:
                    records.append({
                        "arm": arm, "seed": os.path.basename(run_dir).removeprefix("seed"),
                        "roi": ROIS[roi_index], "split": split, "scan": names[s],
                        "corr": corrs[out], "mse": mses[out], "selected_epoch": best["epoch"],
                        "epochs_run": run["epochs_run"], "shared_model": key == "all"})
    return records, {split: [int(k) for k in v] for split, v in keep.items()}


def summarize(records, baseline):
    cell = defaultdict(list)  # (arm, split, roi, seed) -> per-scan R
    for r in records:
        cell[(r["arm"], r["split"], r["roi"], r["seed"])].append(r["corr"])
    arms = sorted({r["arm"] for r in records}, key=lambda a: (a != baseline, a))
    lines = ["| Arm | Runs | " + " | ".join(SHORT) + " | Avg. test R | Δ test vs base | Δ val vs base | "
             "Seeds better (test) |", "|---|---|" + "---|" * (len(SHORT) + 4)]
    for arm in arms:
        seeds = sorted({k[3] for k in cell if k[0] == arm})
        complete = [s for s in seeds if all((arm, "test", roi, s) in cell for roi in ROIS)]
        per_roi = []
        for roi in ROIS:
            values = [np.mean(cell[(arm, "test", roi, s)]) for s in seeds if (arm, "test", roi, s) in cell]
            per_roi.append(f"{np.mean(values):.3f}" if values else "–")
        avg = (np.mean([np.mean([np.mean(cell[(arm, "test", roi, s)]) for roi in ROIS]) for s in complete])
               if complete else float("nan"))
        deltas = {}
        for split in ("test", "val"):
            paired = [s for s in complete if all((baseline, split, roi, s) in cell for roi in ROIS)]
            deltas[split] = [np.mean([np.mean(np.array(cell[(arm, split, roi, s)]) - np.array(cell[(baseline, split, roi, s)]))
                                      for roi in ROIS]) for s in paired]
        delta = (lambda d: f"{np.mean(d):+.3f}" if d and arm != baseline else "")
        better = (f"{sum(d > 0 for d in deltas['test'])}/{len(deltas['test'])}"
                  if deltas["test"] and arm != baseline else "")
        n_runs = len({(k[2], k[3]) for k in cell if k[0] == arm and k[1] == "test"})
        lines.append(f"| {arm} | {n_runs} | " + " | ".join(per_roi)
                     + f" | {avg:.3f} | {delta(deltas['test'])} | {delta(deltas['val'])} | {better} |")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.join(os.environ.get(
        "M3_OUT", "/scratch/hz18/stay0060/NeuroBOLT/checkpoints"), "hypotheses"))
    parser.add_argument("--out", default=None, help="directory for runs.csv and summary.md (default: --root)")
    parser.add_argument("--baseline", default="base")
    parser.add_argument("--aligned", action="store_true",
                        help="rescore every run on the frames all arms share (see module docstring)")
    args = parser.parse_args()
    out = args.out or args.root
    os.makedirs(out, exist_ok=True)

    records, keep = collect(args.root, aligned=args.aligned)
    if not records:
        raise SystemExit(f"No finished runs under {args.root}")
    suffix = "_aligned" if args.aligned else ""
    with open(os.path.join(out, f"runs{suffix}.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    lines = ["# Inter-subject hypothesis arms", "",
             "Mean test R per ROI (averaged over seeds and the six held-out scans). Δ columns are paired "
             f"differences from `{args.baseline}` on matched seed, ROI and scan, averaged over ROIs; "
             "the last column counts seeds whose average improved."]
    if args.aligned:
        lines.append(f"Scored on each scan's last {min(keep['test'])}–{max(keep['test'])} test frames, "
                     "the frames every arm shares.")
    lines.append("")
    lines += summarize(records, args.baseline)
    with open(os.path.join(out, f"summary{suffix}.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n{len(records)} rows -> {os.path.join(out, f'runs{suffix}.csv')}")


if __name__ == "__main__":
    main()
