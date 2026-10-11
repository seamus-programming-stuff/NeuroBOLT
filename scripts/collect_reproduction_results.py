#!/usr/bin/env python3
"""Collect best-validation-epoch metrics from the resting-state SLURM runs."""

import csv
import json
import math
import os
import statistics
from pathlib import Path


REPO = Path(os.environ.get("M3_REPO", "/projects/hz18/stay0060/NeuroBOLT"))
OUT = Path(os.environ.get("M3_OUT", "/scratch/hz18/stay0060/NeuroBOLT/checkpoints"))
EEG = Path(os.environ.get("M3_DATA", "/scratch/hz18/stay0060/NeuroBOLT/data")) / "EEG"
RESULTS = OUT / "paper_resting"
ROIS = [
    "Cuneus",
    "Heschl’s gyrus",
    "Middle frontal gyrus anterior",
    "Precuneus anterior",
    "Putamen",
    "Thalamus",
    "global signal clean",
]


def read_best(log_path):
    if not log_path.is_file():
        return None, "missing"
    records = []
    with log_path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records:
        return None, "empty"
    best = min(records, key=lambda row: float(row.get("val_mse", math.inf)))
    status = "complete" if max(int(row.get("epoch", -1)) for row in records) >= 29 else "incomplete"
    return best, status


def main():
    scans = sorted(path.name.removesuffix("_eeg.set") for path in EEG.glob("*_eeg.set"))
    if len(scans) != 29:
        raise SystemExit(f"Expected 29 resting scans; found {len(scans)} under {EEG}")

    rows = []
    for scan in scans:
        for index, roi in enumerate(ROIS):
            key = f"intra/{scan}/{index}"
            best, status = read_best(RESULTS / key / "log.txt")
            rows.append({"experiment": "intrascan", "scan": scan, "roi": roi,
                         "status": status, "selected_epoch": "" if best is None else best.get("epoch", ""),
                         "val_mse": "" if best is None else best.get("val_mse", ""),
                         "test_mse": "" if best is None else best.get("test_mse", ""),
                         "test_corr": "" if best is None else best.get("test_corr", "")})

    for index, roi in enumerate(ROIS):
        best, status = read_best(RESULTS / f"inter/{index}" / "log.txt")
        rows.append({"experiment": "full_test", "scan": "all", "roi": roi,
                     "status": status, "selected_epoch": "" if best is None else best.get("epoch", ""),
                     "val_mse": "" if best is None else best.get("val_mse", ""),
                     "test_mse": "" if best is None else best.get("test_mse", ""),
                     "test_corr": "" if best is None else best.get("test_corr", "")})

    RESULTS.mkdir(parents=True, exist_ok=True)
    detail_path = RESULTS / "reproduction_runs.csv"
    fields = ["experiment", "scan", "roi", "status", "selected_epoch", "val_mse", "test_mse", "test_corr"]
    with detail_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    for mode, expected_n in (("intrascan", 29), ("full_test", 1)):
        for roi in ROIS:
            selected = [row for row in rows if row["experiment"] == mode and row["roi"] == roi]
            complete = [row for row in selected if row["status"] == "complete"]
            summary.append({
                "experiment": mode,
                "roi": roi,
                "completed_runs": len(complete),
                "expected_runs": expected_n,
                "mean_test_corr": statistics.mean(float(row["test_corr"]) for row in complete) if complete else "",
                "sd_test_corr": statistics.stdev(float(row["test_corr"]) for row in complete) if len(complete) > 1 else "",
                "mean_test_mse": statistics.mean(float(row["test_mse"]) for row in complete) if complete else "",
            })
    summary_path = RESULTS / "reproduction_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)

    completed = sum(row["status"] == "complete" for row in rows)
    print(f"Completed runs: {completed}/{len(rows)}")
    print(f"Per-run metrics: {detail_path}")
    print(f"Paper-table summaries: {summary_path}")
    for row in summary:
        if row["completed_runs"]:
            print("{experiment} | {roi} | n={completed_runs}/{expected_runs} | "
                  "R={mean_test_corr:.3f} +/- {sd_test_corr:.3f} | MSE={mean_test_mse:.3f}".format(**{
                      **row,
                      "mean_test_corr": float(row["mean_test_corr"]),
                      "sd_test_corr": float(row["sd_test_corr"] or 0),
                      "mean_test_mse": float(row["mean_test_mse"]),
                  }))


if __name__ == "__main__":
    main()
