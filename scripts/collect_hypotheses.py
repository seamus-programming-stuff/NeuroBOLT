#!/usr/bin/env python3
"""Compare inter-subject hypothesis arms with the baseline arm, matched by seed, ROI and held-out scan.

Reads <root>/<arm>/<ROI index | all>/seed<k>/log.txt as written by hypotheses_m3.sbatch (or a
one-row log.txt from a non-neural baseline). Every run is scored at its min-validation-MSE epoch,
where main.py logs per-scan R for each validation and test scan.

    python scripts/collect_hypotheses.py --root $M3_OUT/hypotheses --out <dir>

Writes runs.csv (one row per arm x seed x ROI x split x scan) and summary.md. Arms are compared
on validation scans first: decisions should rest on those, with the six test scans as the
confirmation, since every arm is scored on the same test scans.
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
    best = min(rows, key=lambda r: r["val_mse"])
    return {"best": best, "epochs_run": len(rows), "done": os.path.isfile(os.path.join(run_dir, "done"))}


def collect(root):
    records = []
    for arm in sorted(os.listdir(root)):
        arm_dir = os.path.join(root, arm)
        if not os.path.isdir(arm_dir):
            continue
        for key in sorted(os.listdir(arm_dir)):
            key_dir = os.path.join(arm_dir, key)
            if not os.path.isdir(key_dir):
                continue
            roi_indices = list(range(len(ROIS))) if key == "all" else [int(key)]
            for seed_dir in sorted(os.listdir(key_dir)):
                run = read_run(os.path.join(key_dir, seed_dir))
                if run is None or not run["done"]:
                    continue
                best = run["best"]
                for split in ("val", "test"):
                    for s, (corrs, mses) in enumerate(zip(best[f"{split}_scan_corr"], best[f"{split}_scan_mse"])):
                        for out, roi_index in enumerate(roi_indices):
                            records.append({
                                "arm": arm, "seed": seed_dir.removeprefix("seed"), "roi": ROIS[roi_index],
                                "split": split, "scan": SPLIT_SCANS[split][s], "corr": corrs[out],
                                "mse": mses[out], "selected_epoch": best["epoch"], "epochs_run": run["epochs_run"],
                                "shared_model": key == "all"})
    return records


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
    args = parser.parse_args()
    out = args.out or args.root
    os.makedirs(out, exist_ok=True)

    records = collect(args.root)
    if not records:
        raise SystemExit(f"No finished runs under {args.root}")
    with open(os.path.join(out, "runs.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    lines = ["# Inter-subject hypothesis arms", "",
             "Mean test R per ROI (averaged over seeds and the six held-out scans). Δ columns are paired "
             f"differences from `{args.baseline}` on matched seed, ROI and scan, averaged over ROIs; "
             "the last column counts seeds whose average improved.", ""]
    lines += summarize(records, args.baseline)
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n{len(records)} rows -> {os.path.join(out, 'runs.csv')}")


if __name__ == "__main__":
    main()
