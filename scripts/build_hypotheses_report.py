#!/usr/bin/env python3
"""Build the hypothesis-test report (repo markdown and web page) from the collected scores.

    python scripts/build_hypotheses_report.py --runs <runs_aligned.csv> --status "<one line>"

Reads collect_hypotheses.py --aligned output, the hand-written findings in
reports/hypotheses/findings.md and the charts from plot_hypotheses.py, and writes
reports/NeuroBOLT hypothesis tests.md plus reports/hypotheses/index.html (the artifact page).

Differences from the NeuroBOLT baseline are paired by ROI and held-out scan: for each test scan,
the arm's R (averaged over its seeds) minus the baseline's, averaged over ROIs. The 95% CI is a
t-interval over those per-scan differences, so it reflects the six held-out scans (five people).
"""
import argparse
import csv
import html
import math
import os
import re
from collections import defaultdict

import numpy as np
from scipy import stats

from plot_hypotheses import LABELS

ROIS = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior",
        "Putamen", "Thalamus", "global signal clean"]
SHORT = ["Cuneus", "Heschl's", "Mid. frontal", "Precuneus", "Putamen", "Thalamus", "Global"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    cells = defaultdict(list)  # (arm, split, roi, scan) -> R per seed
    seeds = defaultdict(set)
    for row in csv.DictReader(open(path, encoding="utf-8")):
        cells[(row["arm"], row["split"], row["roi"], row["scan"])].append(float(row["corr"]))
        seeds[row["arm"]].add(row["seed"])
    return cells, seeds


def arm_rows(cells, seeds, baseline):
    arms = {k[0] for k in cells}
    scans = {split: sorted({k[3] for k in cells if k[1] == split}) for split in ("val", "test")}
    rows = []
    for arm in arms:
        def roi_mean(split, roi):
            values = [np.mean(cells[(arm, split, roi, s)]) for s in scans[split] if (arm, split, roi, s) in cells]
            return float(np.mean(values)) if len(values) == len(scans[split]) else None
        per_roi = {split: [roi_mean(split, roi) for roi in ROIS] for split in ("val", "test")}
        complete = all(v is not None for v in per_roi["test"])
        row = {"arm": arm, "label": LABELS.get(arm, arm), "seeds": len(seeds[arm]), "complete": complete,
               "test": per_roi["test"], "avg_test": float(np.mean(per_roi["test"])) if complete else None,
               "avg_val": float(np.mean(per_roi["val"])) if all(v is not None for v in per_roi["val"]) else None,
               "delta": None, "ci": None, "delta_val": None}
        if complete and arm != baseline and (baseline, "test", ROIS[0], scans["test"][0]) in cells:
            for split in ("test", "val"):
                per_scan = []
                for s in scans[split]:
                    diffs = [np.mean(cells[(arm, split, roi, s)]) - np.mean(cells[(baseline, split, roi, s)])
                             for roi in ROIS if (baseline, split, roi, s) in cells and (arm, split, roi, s) in cells]
                    if len(diffs) == len(ROIS):
                        per_scan.append(np.mean(diffs))
                if len(per_scan) == len(scans[split]):
                    mean = float(np.mean(per_scan))
                    if split == "test":
                        half = float(stats.t.ppf(0.975, len(per_scan) - 1) * np.std(per_scan, ddof=1)
                                     / math.sqrt(len(per_scan)))
                        row["delta"], row["ci"] = mean, (mean - half, mean + half)
                    else:
                        row["delta_val"] = mean
        rows.append(row)
    rows.sort(key=lambda r: (not r["complete"], -(r["avg_test"] or 0)))
    return rows


def fmt(v, digits=3, signed=False):
    if v is None:
        return "–"
    return f"{v:+.{digits}f}" if signed else f"{v:.{digits}f}"


def markdown_table(rows, baseline):
    head = ("| Arm | Seeds | " + " | ".join(SHORT) + " | Avg. test R | Avg. val R | "
            f"Δ test vs baseline (95% CI) | Δ val |")
    lines = [head, "|---|---|" + "---|" * (len(SHORT) + 4)]
    for r in rows:
        ci = f" ({r['ci'][0]:+.3f} to {r['ci'][1]:+.3f})" if r["ci"] else ""
        delta = "reference" if r["arm"] == baseline else fmt(r["delta"], signed=True) + ci
        lines.append(f"| {r['label']} | {r['seeds']} | " + " | ".join(fmt(v) for v in r["test"])
                     + f" | {fmt(r['avg_test'])} | {fmt(r['avg_val'])} | {delta} | "
                     + ("" if r["arm"] == baseline else fmt(r["delta_val"], signed=True)) + " |")
    return "\n".join(lines)


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)


def markdown_to_html(text):
    """The subset findings.md uses: ### headings, - bullets, paragraphs, **bold**, `code`, links."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped.startswith("### "):
            flush()
            out.append(f"<h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            if para:
                flush()
            items.append(stripped[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + stripped
        else:
            para.append(stripped)
    flush()
    return "\n".join(out)


def html_table(rows, baseline):
    head = ("<tr><th class=\"left\">Arm</th><th>Seeds</th>" + "".join(f"<th>{s}</th>" for s in SHORT)
            + "<th>Avg. test R</th><th>Avg. val R</th><th>Δ test vs baseline (95% CI)</th><th>Δ val</th></tr>")
    body = []
    for r in rows:
        kind = "base" if r["arm"] == baseline else ("linear" if r["arm"].startswith(("ridge", "hgb")) else "neural")
        if r["arm"] == baseline:
            delta = "reference"
        elif r["delta"] is None:
            delta = "–"
        else:
            ci = f" <span class=\"ci\">({r['ci'][0]:+.3f} to {r['ci'][1]:+.3f})</span>" if r["ci"] else ""
            delta = f"{r['delta']:+.3f}{ci}"
        body.append(f"<tr class=\"{kind}{'' if r['complete'] else ' partial'}\"><td class=\"left\">"
                    f"<span class=\"swatch {kind}\"></span>{html.escape(r['label'])}</td><td>{r['seeds']}</td>"
                    + "".join(f"<td>{fmt(v)}</td>" for v in r["test"])
                    + f"<td><strong>{fmt(r['avg_test'])}</strong></td><td>{fmt(r['avg_val'])}</td><td>{delta}</td>"
                    f"<td>{'' if r['arm'] == baseline else fmt(r['delta_val'], signed=True)}</td></tr>")
    return f"<thead>{head}</thead><tbody>{''.join(body)}</tbody>"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--status", required=True, help="one-line progress note shown at the top")
    parser.add_argument("--baseline", default="base")
    parser.add_argument("--findings", default=os.path.join(REPO, "reports", "hypotheses", "findings.md"))
    parser.add_argument("--template", default=os.path.join(REPO, "reports", "hypotheses", "template.html"))
    args = parser.parse_args()

    cells, seeds = load(args.runs)
    rows = arm_rows(cells, seeds, args.baseline)
    findings = open(args.findings, encoding="utf-8").read()

    md = ["# NeuroBOLT hypothesis tests", "", f"*{args.status}*", "",
          "Inter-subject prediction on the authors' split (18 training, 5 validation and 6 held-out scans). "
          "NeuroBOLT arms train every ROI with three seeds (12345, 1, 2); band-power baselines are "
          "deterministic. Every run is scored at its validation-selected point on the frames all arms "
          "share. Test R is averaged over the six held-out scans and, for NeuroBOLT, the seeds.", "",
          "![Every arm's average test R](hypotheses/arms_overview.png)", "",
          markdown_table(rows, args.baseline), "",
          "Δ is paired by ROI and held-out scan; its 95% CI is a t-interval over the six held-out scans. "
          "Rows with a dash in any ROI are still running.", "", "## Findings so far", "", findings]
    with open(os.path.join(REPO, "reports", "NeuroBOLT hypothesis tests.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(md) + "\n")

    page = open(args.template, encoding="utf-8").read()
    page = (page.replace("{{STATUS}}", html.escape(args.status))
                .replace("{{TABLE}}", html_table(rows, args.baseline))
                .replace("{{FINDINGS}}", markdown_to_html(findings)))
    with open(os.path.join(REPO, "reports", "hypotheses", "index.html"), "w", encoding="utf-8") as stream:
        stream.write(page)
    for r in rows:
        print(f"{r['label']:40s} seeds={r['seeds']} avg_test={fmt(r['avg_test'])} delta={fmt(r['delta'], signed=True)}")


if __name__ == "__main__":
    main()
