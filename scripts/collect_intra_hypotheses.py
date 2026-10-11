#!/usr/bin/env python3
"""Compare intra-scan approaches on the six inter-subject test scans and their last 48 frames.

Sources, all scored on the same frames (the intra-scan test segment):
  - intra_hypotheses/<arm>/<scan>/<roi>/log.txt   NeuroBOLT runs from intra_hypotheses_m3.sbatch
  - paper_resting/intra/<scan>/<roi>/log.txt      the original reproduction (LaBraM init, no high-pass)
  - paper_resting/per_scan/per_scan_predictions.npz   cross-subject model, no fine-tuning ("zero-shot")
  - intra_baselines/<arm>/intra_ridge.csv          band-power ridge

    python scripts/collect_intra_hypotheses.py --root $M3_OUT

NeuroBOLT runs are scored at the minimum-validation-MSE epoch (main.py's rule) and at the last epoch.
"""
import argparse
import csv
import json
import os

import numpy as np

SCANS = ["sub07-scan01", "sub07-scan02", "sub11-scan01", "sub16-scan01", "sub18-scan01", "sub21-scan01"]
ROIS = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior",
        "Putamen", "Thalamus", "global signal clean"]
STEMS = ["Cuneus", "Heschl", "Midfront", "Precuneus", "Putamen", "Thalamus", "glb"]
SHORT = ["Cuneus", "Heschl's", "Mid. frontal", "Precuneus", "Putamen", "Thalamus", "Global"]
TEST_FRAMES = 48


def neurobolt(run_root):
    """{(scan, roi index): (R at min val MSE, R at last epoch)} for finished runs under run_root."""
    out = {}
    for scan in SCANS:
        for j in range(len(ROIS)):
            path = os.path.join(run_root, scan, str(j), "log.txt")
            if not os.path.isfile(path):
                continue
            rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
            if len(rows) < 30 and not os.path.isfile(os.path.join(run_root, scan, str(j), "done")):
                continue
            out[(scan, j)] = (min(rows, key=lambda r: r["val_mse"])["test_corr"], rows[-1]["test_corr"])
    return out


def zero_shot(npz_path):
    z = np.load(npz_path)
    out = {}
    for scan in SCANS:
        for j, stem in enumerate(STEMS):
            pred = z[f"ours|hp|{scan}|{stem}|pred"][-TEST_FRAMES:]
            true = z[f"hp|{scan}|{stem}|true"][-TEST_FRAMES:]
            out[(scan, j)] = float(np.corrcoef(pred, true)[0, 1])
    return out


def ridge(csv_path):
    return {(r["scan"], ROIS.index(r["roi"])): float(r["test_corr"])
            for r in csv.DictReader(open(csv_path, encoding="utf-8")) if r["scan"] in SCANS}


def row(name, scores):
    per_roi = []
    for j in range(len(ROIS)):
        values = [scores[(s, j)] for s in SCANS if (s, j) in scores]
        per_roi.append(np.mean(values) if len(values) == len(SCANS) else None)
    cells = [f"{v:.3f}" if v is not None else "–" for v in per_roi]
    avg = f"{np.mean(per_roi):.3f}" if all(v is not None for v in per_roi) else "–"
    return f"| {name} | " + " | ".join(cells) + f" | {avg} |"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.environ.get("M3_OUT", "/scratch/hz18/stay0060/NeuroBOLT/checkpoints"))
    args = parser.parse_args()

    lines = ["| Intra-scan, 6 held-out scans | " + " | ".join(SHORT) + " | Avg. |", "|---|" + "---|" * (len(SHORT) + 1)]
    sources = [("NeuroBOLT, LaBraM init (reproduction)", neurobolt(os.path.join(args.root, "paper_resting", "intra")))]
    for arm, label in (("intra_labram_hp", "NeuroBOLT, LaBraM init, 0.5 Hz high-pass"),
                       ("intra_transfer_hp", "NeuroBOLT, cross-subject init, 0.5 Hz high-pass")):
        sources.append((label, neurobolt(os.path.join(args.root, "intra_hypotheses", arm))))
    for label, scores in sources:
        lines.append(row(f"{label}, min val MSE epoch", {k: v[0] for k, v in scores.items()}))
        lines.append(row(f"{label}, last epoch", {k: v[1] for k, v in scores.items()}))
    npz = os.path.join(args.root, "paper_resting", "per_scan", "per_scan_predictions.npz")
    if os.path.isfile(npz):
        lines.append(row("Cross-subject NeuroBOLT, no fine-tuning", zero_shot(npz)))
    for arm, label in (("intra_ridge", "Ridge, 5 bands, 16 s"), ("intra_ridge_fine", "Ridge, 1 Hz bins, 16 s")):
        path = os.path.join(args.root, "intra_baselines", arm, "intra_ridge.csv")
        if os.path.isfile(path):
            lines.append(row(label, ridge(path)))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
