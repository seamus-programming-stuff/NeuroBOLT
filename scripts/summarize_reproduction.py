#!/usr/bin/env python3
"""Build the NeuroBOLT rows of the paper's Table 1 and a Figure 5 recreation from the M3 runs.

Reads the reproduction tree written by reproduce_rest_m3.sbatch (intra/<scan>/<roi>/log.txt,
inter/<roi>/log.txt) plus eval_inter_per_scan.py's per_scan/ outputs, and writes CSV tables,
markdown tables and figures:

    python scripts/summarize_reproduction.py --results <paper_resting dir> --out reports/reproduction

Intra-scan: one run per scan, scored at the min-validation-MSE epoch (main.py's own rule);
mean +/- SD across the 29 scans. Inter-subject: one model per ROI, scored per held-out scan;
mean +/- SD across the six test scans. The 95% CIs are t-intervals across scans.

The Figure 5 bands are split-conformal 95% prediction intervals: the 95th-percentile absolute
residual on the five validation scans, added around each held-out prediction. Predictions are
normalized per scan (demeaned, divided by their 95th-percentile absolute value) as in the
authors' inference demo, so they share the target's scale; this does not change R.
"""
import argparse
import csv
import json
import math
import os
import re
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROIS = [  # (DiFuMo label, short name, published checkpoint stem)
    ("Cuneus", "Cuneus", "Cuneus"),
    ("Heschl’s gyrus", "Heschl's gyrus", "Heschl"),
    ("Middle frontal gyrus anterior", "Middle frontal", "Midfront"),
    ("Precuneus anterior", "Precuneus anterior", "Precuneus"),
    ("Putamen", "Putamen", "Putamen"),
    ("Thalamus", "Thalamus", "Thalamus"),
    ("global signal clean", "Global signal", "glb"),
]
# NeuroBOLT rows of Table 1 in Li et al., NeurIPS 2024: (mean, SD) per ROI
PAPER = {
    "intra": [(0.588, 0.166), (0.566, 0.183), (0.502, 0.168), (0.559, 0.141),
              (0.437, 0.184), (0.480, 0.213), (0.587, 0.162)],
    "inter": [(0.482, 0.100), (0.561, 0.046), (0.423, 0.115), (0.496, 0.136),
              (0.335, 0.144), (0.453, 0.106), (0.564, 0.115)],
}
# Scans shown in the paper's Figure 5 ("scans with the median performance"), with the R printed
# on each panel. Identified by re-scoring the authors' published checkpoints per held-out scan:
# each printed R matches exactly one scan.
PAPER_FIG5 = {
    "Cuneus": ("sub21-scan01", 0.548),
    "Heschl’s gyrus": ("sub07-scan01", 0.570),
    "Middle frontal gyrus anterior": ("sub16-scan01", 0.465),
    "Precuneus anterior": ("sub07-scan02", 0.529),
    "Putamen": ("sub07-scan02", 0.427),
    "Thalamus": ("sub11-scan01", 0.427),
    "global signal clean": ("sub11-scan01", 0.615),
}
SELECTION_RULES = {  # how an epoch is picked from one run's 30 log rows
    "min val MSE (main.py)": lambda rows: min(rows, key=lambda r: r["val_mse"]),
    "max val R": lambda rows: max(rows, key=lambda r: r["val_corr"]),
    "last epoch": lambda rows: rows[-1],
    "max test R (oracle)": lambda rows: max(rows, key=lambda r: r["test_corr"]),
}
TR = 2.1

# Chart tokens: reference palette slots 1-2 (validated in both modes), ink and chrome steps.
# Each figure is drawn once per theme; the markdown report uses light, the web page swaps.
THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink_2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7", "ours": "#2a78d6", "paper": "#eb6834", "band": 0.14},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink_2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835", "ours": "#3987e5", "paper": "#d95926", "band": 0.24},
}


def read_log(path):
    with open(path, encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    if [r["epoch"] for r in rows] != list(range(len(rows))):
        raise ValueError(f"{path}: epochs are not a single 0..N-1 run")
    return rows


def mean_sd_ci(values):
    values = np.asarray(values, dtype=float)
    n, mean, sd = len(values), float(values.mean()), float(values.std(ddof=1))
    half = float(stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n))
    return {"n": n, "mean": mean, "sd": sd, "ci_lo": mean - half, "ci_hi": mean + half}


def normalize(x):
    """preproc.normalize_data for one series: demean, divide by the 95th-percentile |x|."""
    x = x - x.mean()
    return x / (np.quantile(np.abs(x), 0.95) + 1e-8)


def conformal_halfwidth(residuals, alpha=0.05):
    """Split-conformal radius: the ceil((n+1)(1-alpha))-th smallest absolute residual."""
    ranked = np.sort(np.abs(residuals))
    k = min(math.ceil((len(ranked) + 1) * (1 - alpha)), len(ranked))
    return float(ranked[k - 1])


def block_bootstrap_r(pred, true, block=20, reps=2000, seed=0):
    """95% CI for one scan's R, resampling circular blocks of `block` frames (default ~42 s)."""
    rng = np.random.default_rng(seed)
    n = len(pred)
    n_blocks = math.ceil(n / block)
    draws = np.empty(reps)
    for i in range(reps):
        idx = (rng.integers(0, n, n_blocks)[:, None] + np.arange(block)).ravel()[:n] % n
        draws[i] = np.corrcoef(pred[idx], true[idx])[0, 1]
    return np.percentile(draws, [2.5, 97.5])


def fmt(cell):
    return f"{cell['mean']:.3f} ± {cell['sd']:.3f}"


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))  # union, first-seen order
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def style_axes(ax, c):
    ax.set_facecolor(c["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(c["axis"])
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=9, width=0.8)
    ax.grid(axis="y", color=c["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def intra_results(results_dir):
    scans = sorted(os.listdir(os.path.join(results_dir, "intra")))
    per_scan, by_rule = [], {rule: np.zeros((len(scans), len(ROIS))) for rule in SELECTION_RULES}
    for i, scan in enumerate(scans):
        for j, (label, _, _) in enumerate(ROIS):
            rows = read_log(os.path.join(results_dir, "intra", scan, str(j), "log.txt"))
            picked = {rule: pick(rows) for rule, pick in SELECTION_RULES.items()}
            for rule, row in picked.items():
                by_rule[rule][i, j] = row["test_corr"]
            main_row = picked["min val MSE (main.py)"]
            per_scan.append({"scan": scan, "roi": label, "selected_epoch": main_row["epoch"],
                             "val_mse": main_row["val_mse"], "test_mse": main_row["test_mse"],
                             "test_corr": main_row["test_corr"],
                             **{f"test_corr[{rule}]": row["test_corr"] for rule, row in picked.items()},
                             **{f"epoch[{rule}]": row["epoch"] for rule, row in picked.items()}})
    return scans, per_scan, by_rule


def inter_results(results_dir):
    with open(os.path.join(results_dir, "per_scan", "per_scan_metrics.csv"), encoding="utf-8") as stream:
        metrics = list(csv.DictReader(stream))
    for row in metrics:
        row["corr"], row["mse"], row["n"] = float(row["corr"]), float(row["mse"]), int(row["n"])
        row["eeg_highpass"] = row["eeg_highpass"] == "True"
    with open(os.path.join(results_dir, "per_scan", "checkpoints.json"), encoding="utf-8") as stream:
        meta = json.load(stream)
    predictions = np.load(os.path.join(results_dir, "per_scan", "per_scan_predictions.npz"))
    return metrics, meta, predictions


def pick_rows(metrics, model, highpass, split, roi):
    return [r for r in metrics if r["model"] == model and r["eeg_highpass"] == highpass
            and r["split"] == split and r["roi"] == roi]


def logged_score(epoch_string, key):
    match = re.search(rf"{key}(-?[0-9.]+)", epoch_string)
    return float(match.group(1)) if match else float("nan")


def figure_table1(path, intra, inter, c):
    """Per-scan R (dots), our mean with 95% CI, and the paper's mean, per ROI and setting."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True, facecolor=c["surface"])
    rng = np.random.default_rng(0)
    for ax, (title, setting) in zip(axes, (("Intra-scan (29 scans)", intra), ("Inter-subject (6 held-out scans)", inter))):
        style_axes(ax, c)
        x = np.arange(len(ROIS))
        for j, (values, cell, paper) in enumerate(setting):
            jitter = rng.uniform(-0.12, 0.12, len(values))
            ax.scatter(j - 0.12 + jitter, values, s=12, color=c["muted"], alpha=0.55, linewidths=0, zorder=2)
            ax.plot([j + 0.12] * 2, [cell["ci_lo"], cell["ci_hi"]], color=c["ours"], linewidth=2,
                    solid_capstyle="round", zorder=3)
            ax.scatter(j + 0.12, cell["mean"], s=46, color=c["ours"], edgecolors=c["surface"], linewidths=1.5, zorder=4)
            ax.scatter(j + 0.30, paper[0], s=52, marker="D", color=c["paper"], edgecolors=c["surface"],
                       linewidths=1.5, zorder=4)
        ax.axhline(0, color=c["axis"], linewidth=0.8, zorder=1)
        ax.set_xticks(x, [short for _, short, _ in ROIS], rotation=25, ha="right")
        ax.set_title(title, color=c["ink"], fontsize=11, loc="left")
    axes[0].set_ylabel("Pearson R on held-out data", color=c["ink_2"], fontsize=10)
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=c["muted"], alpha=0.55, markersize=5, label="One scan (ours)"),
        plt.Line2D([], [], marker="o", color=c["ours"], markersize=7, linewidth=2, label="Ours: mean and 95% CI"),
        plt.Line2D([], [], marker="D", linestyle="", color=c["paper"], markersize=7, label="Paper, Table 1"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9.5,
               labelcolor=c["ink_2"], bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=150, facecolor=c["surface"])
    plt.close(fig)


def figure5(path, panels, c):
    """Paper Figure 5 layout: sensory | cognitive | subcortical columns, global signal below."""
    fig = plt.figure(figsize=(17, 8.6), facecolor=c["surface"])
    grid = fig.add_gridspec(3, 3, hspace=0.62, wspace=0.12)
    slots = {"Cuneus": (0, 0), "Heschl's gyrus": (1, 0), "Middle frontal": (0, 1),
             "Precuneus anterior": (1, 1), "Putamen": (0, 2), "Thalamus": (1, 2), "Global signal": (2, 1)}
    for column, heading in enumerate(("Primary sensory", "High-level cognitive", "Subcortical")):
        fig.text(0.125 + column * 0.2715 + 0.13, 0.955, heading, ha="center", fontsize=13,
                 fontweight="bold", color=c["ink"])
    for panel in panels:
        ax = fig.add_subplot(grid[slots[panel["short"]]])
        style_axes(ax, c)
        ax.grid(False)
        t = np.arange(len(panel["true"])) * TR
        ax.fill_between(t, panel["pred"] - panel["q"], panel["pred"] + panel["q"], color=c["ours"],
                        alpha=c["band"], linewidth=0, zorder=1)
        ax.plot(t, panel["true"], color=c["ink_2"], linewidth=0.8, zorder=2)
        ax.plot(t, panel["pred"], color=c["ours"], linewidth=1.2, zorder=3)
        ax.set_xlim(0, t[-1])
        ax.set_title(f"{panel['short']}  ·  {panel['scan']}", fontsize=10, color=c["ink"], loc="left")
        lo, hi = panel["r_ci"]
        ax.text(0.01, 0.97, f"R = {panel['r']:.3f}  (95% CI {lo:.2f} to {hi:.2f})   paper: {panel['paper_r']:.3f}",
                transform=ax.transAxes, va="top", fontsize=9, color=c["ink"],
                bbox={"facecolor": c["surface"], "edgecolor": "none", "alpha": 0.85, "pad": 1.5})
        ax.set_xlabel("Time (s)", fontsize=9, color=c["ink_2"])
        if slots[panel["short"]][1] == 0:
            ax.set_ylabel("Normalized ROI signal", fontsize=9, color=c["ink_2"])
    handles = [
        plt.Line2D([], [], color=c["ours"], linewidth=2, label="Predicted (ours, held-out scan)"),
        plt.Rectangle((0, 0), 1, 1, color=c["ours"], alpha=c["band"], label="95% prediction interval"),
        plt.Line2D([], [], color=c["ink_2"], linewidth=1.2, label="True ROI signal"),
    ]
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(0.80, 0.19), frameon=False,
               fontsize=11, labelcolor=c["ink_2"])
    fig.savefig(path, dpi=150, facecolor=c["surface"], bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", required=True, help="paper_resting directory (intra/, inter/, per_scan/)")
    parser.add_argument("--out", default="reports/reproduction")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    md = []

    # ---- intra-scan: one run per scan, main.py's min-val-MSE epoch ----
    scans, intra_rows, by_rule = intra_results(args.results)
    write_csv(os.path.join(args.out, "intra_per_scan.csv"), intra_rows)
    main_rule = by_rule["min val MSE (main.py)"]
    intra_cells = [mean_sd_ci(main_rule[:, j]) for j in range(len(ROIS))]

    # ---- inter-subject: per held-out scan ----
    metrics, meta, predictions = inter_results(args.results)
    test_scans = meta["splits"]["test"]
    inter_cells, published_cells, checks = [], {True: [], False: []}, []
    for j, (label, short, stem) in enumerate(ROIS):
        ours = pick_rows(metrics, "ours", True, "test", label)
        inter_cells.append(mean_sd_ci([r["corr"] for r in ours]))
        log_row = meta["checkpoints"]["ours"][label]["log_row"]
        checks.append({"roi": label, "model": "ours", "eeg_highpass": True,
                       "logged_test_corr": log_row["test_corr"], "mean_per_scan_corr": inter_cells[-1]["mean"],
                       "logged_val_corr": log_row["val_corr"],
                       "mean_per_scan_val_corr": statistics.mean(
                           r["corr"] for r in pick_rows(metrics, "ours", True, "val", label)),
                       "epoch": log_row["epoch"]})
        if label in meta["checkpoints"]["published"]:
            epoch_string = meta["checkpoints"]["published"][label]["epoch"]
            for highpass in (True, False):
                rows = pick_rows(metrics, "published", highpass, "test", label)
                published_cells[highpass].append(mean_sd_ci([r["corr"] for r in rows]))
                checks.append({"roi": label, "model": "published", "eeg_highpass": highpass,
                               "logged_test_corr": logged_score(epoch_string, "testcorr"),
                               "mean_per_scan_corr": published_cells[highpass][-1]["mean"],
                               "logged_val_corr": logged_score(epoch_string, "valcorr"),
                               "mean_per_scan_val_corr": statistics.mean(
                                   r["corr"] for r in pick_rows(metrics, "published", highpass, "val", label)),
                               "epoch": epoch_string.split("-")[0]})
    write_csv(os.path.join(args.out, "inter_logged_vs_per_scan.csv"), checks)
    write_csv(os.path.join(args.out, "inter_per_scan.csv"),
              [{k: v for k, v in r.items()} for r in metrics])

    # ---- Table 1, NeuroBOLT rows only ----
    header = "| Setting | Source | " + " | ".join(short for _, short, _ in ROIS) + " | Avg. R |"
    rule_line = "|---|---|" + "---|" * (len(ROIS) + 1)
    md += ["## Table 1, NeuroBOLT rows (mean ± SD of per-scan Pearson R)", "", header, rule_line]
    table_rows = []
    for setting, cells, source in (("Intra-scan", [{"mean": m, "sd": s} for m, s in PAPER["intra"]], "Paper"),
                                   ("Intra-scan", intra_cells, "Ours (29 scans)"),
                                   ("Inter-subject", [{"mean": m, "sd": s} for m, s in PAPER["inter"]], "Paper"),
                                   ("Inter-subject", inter_cells, "Ours (6 held-out scans)")):
        avg = statistics.mean(c["mean"] for c in cells)
        md.append(f"| {setting} | {source} | " + " | ".join(fmt(c) for c in cells) + f" | {avg:.3f} |")
        for (label, _, _), cell in zip(ROIS, cells):
            table_rows.append({"setting": setting, "source": source, "roi": label, **cell})
    for highpass in (True, False):
        if published_cells[highpass]:
            cells = published_cells[highpass]
            avg = statistics.mean(c["mean"] for c in cells)
            md.append(f"| Inter-subject | Authors' checkpoints, EEG high-pass {'on' if highpass else 'off'} | "
                      + " | ".join(fmt(c) for c in cells) + f" | {avg:.3f} |")
            for (label, _, _), cell in zip(ROIS, cells):
                table_rows.append({"setting": "Inter-subject", "roi": label, **cell,
                                   "source": f"Authors' checkpoints (high-pass {'on' if highpass else 'off'})"})
    write_csv(os.path.join(args.out, "table1_neurobolt.csv"), table_rows)

    md += ["", "## 95% confidence intervals for our means (t-interval across scans)", "",
           "| Setting | " + " | ".join(short for _, short, _ in ROIS) + " |", "|---|" + "---|" * len(ROIS)]
    for setting, cells, paper in (("Intra-scan", intra_cells, PAPER["intra"]), ("Inter-subject", inter_cells, PAPER["inter"])):
        md.append(f"| {setting} | " + " | ".join(
            f"{c['ci_lo']:.3f} to {c['ci_hi']:.3f}{'' if c['ci_lo'] <= p[0] <= c['ci_hi'] else ' ✱'}"
            for c, p in zip(cells, paper)) + " |")
    md.append("")
    md.append("✱ the paper's mean lies outside our 95% CI.")

    # ---- intra-scan sensitivity to the epoch-selection rule ----
    paper_means = np.array([m for m, _ in PAPER["intra"]])
    md += ["", "## Intra-scan mean R by epoch-selection rule (29 scans)", "",
           "| Rule | " + " | ".join(short for _, short, _ in ROIS) + " | Avg. R | RMS gap to paper |",
           "|---|" + "---|" * (len(ROIS) + 2)]
    md.append("| Paper | " + " | ".join(f"{m:.3f} ± {s:.3f}" for m, s in PAPER["intra"])
              + f" | {paper_means.mean():.3f} | |")
    rule_rows = []
    for rule, values in by_rule.items():
        cells = [mean_sd_ci(values[:, j]) for j in range(len(ROIS))]
        gap = float(np.sqrt(np.mean((values.mean(axis=0) - paper_means) ** 2)))
        md.append(f"| {rule} | " + " | ".join(fmt(c) for c in cells) + f" | {values.mean():.3f} | {gap:.3f} |")
        for (label, _, _), cell in zip(ROIS, cells):
            rule_rows.append({"rule": rule, "roi": label, **cell, "rms_gap_to_paper": gap})
    test_mask = np.array([scan in test_scans for scan in scans])
    subset = main_rule[test_mask]
    md.append(f"| min val MSE, only the 6 inter-subject test scans | " + " | ".join(
        f"{subset[:, j].mean():.3f} ± {subset[:, j].std(ddof=1):.3f}" for j in range(len(ROIS)))
        + f" | {subset.mean():.3f} | {np.sqrt(np.mean((subset.mean(axis=0) - paper_means) ** 2)):.3f} |")
    write_csv(os.path.join(args.out, "intra_selection_rules.csv"), rule_rows)
    negative = (main_rule < 0).mean(axis=0)
    md += ["", "Share of intra-scan runs with negative test R (min val MSE): "
           + ", ".join(f"{short} {100 * f:.0f}%" for (_, short, _), f in zip(ROIS, negative))
           + f"; overall {100 * (main_rule < 0).mean():.0f}%."]
    epochs = np.array([[r["selected_epoch"] for r in intra_rows if r["roi"] == label] for label, _, _ in ROIS])
    md.append("Median selected epoch (of 0-29): " + ", ".join(
        f"{short} {int(np.median(e))}" for (_, short, _), e in zip(ROIS, epochs)) + ".")

    for theme, suffix in (("light", ""), ("dark", "_dark")):
        figure_table1(os.path.join(args.out, f"table1_neurobolt{suffix}.png"),
                      [(main_rule[:, j], intra_cells[j], PAPER["intra"][j]) for j in range(len(ROIS))],
                      [([r["corr"] for r in pick_rows(metrics, "ours", True, "test", label)], inter_cells[j],
                        PAPER["inter"][j]) for j, (label, _, _) in enumerate(ROIS)], THEMES[theme])

    # ---- Figure 5: the paper's scans, with conformal 95% prediction intervals ----
    md += ["", "## Figure 5 recreation: the paper's scans, our models", "",
           "| ROI | Scan (as in paper) | Paper R | Our R (block-bootstrap 95% CI) | Interval half-width "
           "(model scale) | Coverage, this scan | Coverage, all 6 test scans (model scale) | "
           "MC-dropout band coverage |", "|---|---|---|---|---|---|---|---|"]
    panels, coverage_rows = [], []
    for label, short, stem in ROIS:
        # Calibrate on validation scans, in the plotted (normalized) space and at the model's own scale
        q = conformal_halfwidth(np.concatenate([
            predictions[f"hp|{scan}|{stem}|true"] - normalize(predictions[f"ours|hp|{scan}|{stem}|pred"])
            for scan in meta["splits"]["val"]]))
        q_raw = conformal_halfwidth(np.concatenate([
            predictions[f"hp|{scan}|{stem}|true"] - predictions[f"ours|hp|{scan}|{stem}|pred"]
            for scan in meta["splits"]["val"]]))
        inside = inside_raw = mc_inside = total = 0
        for scan in test_scans:
            true = predictions[f"hp|{scan}|{stem}|true"]
            raw = predictions[f"ours|hp|{scan}|{stem}|pred"]
            inside += int(np.sum(np.abs(true - normalize(raw)) <= q))
            inside_raw += int(np.sum(np.abs(true - raw) <= q_raw))
            total += len(true)
            mc_key = f"ours|hp|{scan}|{stem}|mc"
            if mc_key in predictions:
                lo, hi = np.percentile(predictions[mc_key], [2.5, 97.5], axis=0)
                mc_inside += int(np.sum((true >= lo) & (true <= hi)))
        shown, paper_r = PAPER_FIG5[label]
        true = predictions[f"hp|{shown}|{stem}|true"]
        pred = normalize(predictions[f"ours|hp|{shown}|{stem}|pred"])
        r = float(np.corrcoef(pred, true)[0, 1])
        r_ci = block_bootstrap_r(pred, true)
        cover_shown = float(np.mean(np.abs(true - pred) <= q))
        panels.append({"short": short, "scan": shown, "true": true, "pred": pred, "q": q, "r": r,
                       "r_ci": r_ci, "paper_r": paper_r})
        coverage_rows.append({"roi": label, "scan_shown": shown, "paper_r": paper_r, "r": r,
                              "r_ci_lo": r_ci[0], "r_ci_hi": r_ci[1], "halfwidth": q, "halfwidth_model_scale": q_raw,
                              "coverage_shown": cover_shown, "coverage_all_test": inside / total,
                              "coverage_all_test_model_scale": inside_raw / total,
                              "mc_dropout_coverage_all_test": mc_inside / total if mc_inside else ""})
        md.append(f"| {short} | {shown} | {paper_r:.3f} | {r:.3f} ({r_ci[0]:.2f} to {r_ci[1]:.2f}) | "
                  f"±{q:.2f} (±{q_raw:.2f}) | {100 * cover_shown:.0f}% | {100 * inside / total:.0f}% "
                  f"({100 * inside_raw / total:.0f}%) | "
                  + (f"{100 * mc_inside / total:.0f}% |" if mc_inside else "n/a |"))
    write_csv(os.path.join(args.out, "figure5_intervals.csv"), coverage_rows)
    for theme, suffix in (("light", ""), ("dark", "_dark")):
        figure5(os.path.join(args.out, f"figure5_recreation{suffix}.png"), panels, THEMES[theme])

    with open(os.path.join(args.out, "tables.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
