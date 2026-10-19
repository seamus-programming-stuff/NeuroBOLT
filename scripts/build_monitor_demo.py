#!/usr/bin/env python3
"""Fill the arousal-monitor demo page (reports/external/monitor.html) with real ds006040 validation data.

    python scripts/build_monitor_demo.py --data reports/external/data --out reports/external/monitor.html
"""
import argparse
import json
import os
import sys

import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interp_report import ci  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "reports", "external", "monitor_template.html")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="reports/external/data")
    parser.add_argument("--out", default="reports/external/monitor.html")
    args = parser.parse_args()
    demo = json.load(open(os.path.join(args.data, "demo.json"), encoding="utf-8"))
    mon = pd.read_csv(os.path.join(args.data, "monitor_runs.csv"))
    fluct = dict(zip(mon["run"], mon["arousal_fluctuation"]))
    runs = {}
    for run in sorted(demo, key=lambda r: (r.split("_")[1], r)):
        d = demo[run]
        runs[run] = {**d, "fluctuation": float(fluct.get(run, float("nan")))}
    accuracy = []
    for key, label in (("r_offline", "Offline"), ("r_streaming", "Streaming (live)")):
        row = [label]
        for cond in ("EC", "EO"):
            pp = mon[mon["condition"] == cond].groupby("subject")[key].mean()
            m, lo, hi = ci(pp)
            row.append(f"{m:.2f} ({lo:.2f}–{hi:.2f})")
        accuracy.append(row)
    accuracy.append(["Compute per volume", f"{mon['latency_ms_median'].median():.0f} ms", ""])
    qc = []
    for target, label in (("measured_gs_sd_raw", "Measured global-signal swing"), ("r_offline", "How predictable the run is"),
                          ("mean_fd", "Head motion (mean FD)")):
        rho, p = stats.spearmanr(mon["arousal_fluctuation"], mon[target])
        qc.append([label, f"{rho:+.2f} (p = {p:.2g})"])
    best = max(runs, key=lambda r: runs[r]["r"] if r.endswith("EC") else -1)
    payload = json.dumps({"runs": runs, "accuracy": accuracy, "qc": qc, "default": best}, separators=(",", ":"))
    page = open(TEMPLATE, encoding="utf-8").read().replace("__DATA__", payload.replace("</", "<\\/"))
    with open(args.out, "w", encoding="utf-8") as stream:
        stream.write(page)
    print(f"Wrote {args.out}: {len(runs)} runs, {len(page) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
