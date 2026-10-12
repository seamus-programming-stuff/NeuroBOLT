#!/usr/bin/env python3
"""Overview chart of the hypothesis arms from collect_hypotheses.py's runs CSV.

One row per arm: each seed's test R averaged over ROIs and held-out scans (dots) and the arm's
mean (bar end), with the NeuroBOLT baseline's mean as a reference line. NeuroBOLT variants and
non-neural baselines get the two validated palette slots. Drawn once per theme.

    python scripts/plot_hypotheses.py --runs <runs_aligned.csv> --out reports/hypotheses
"""
import argparse
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

THEMES = {  # same tokens as summarize_reproduction.py
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink_2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7", "neural": "#2a78d6", "linear": "#eb6834"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink_2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835", "neural": "#3987e5", "linear": "#d95926"},
}
N_ROIS = 7
LABELS = {  # readable names for the arms; unknown arms fall back to their directory name
    "base": "NeuroBOLT (baseline)", "multi7": "NeuroBOLT · one model for 7 ROIs",
    "nohp": "NeuroBOLT · no EEG high-pass", "softmax": "NeuroBOLT · learned scale weights",
    "beta099": "NeuroBOLT · AdamW β₂ 0.99", "nobaseline": "NeuroBOLT · no window baseline",
    "win8": "NeuroBOLT · 8 s window", "win24": "NeuroBOLT · 24 s window", "lr1e4": "NeuroBOLT · lr 1e-4",
    "ridge_bandpower": "Ridge · 5 bands · 16 s / 4 lags", "ridge_nohp": "Ridge · 5 bands · no high-pass",
    "ridge_scanz": "Ridge · per-scan z-scored", "ridge_scanz_w32": "Ridge · per-scan z · 32 s / 8 lags",
    "ridge_scanz_fine": "Ridge · per-scan z · 1 Hz bins", "ridge_w32": "Ridge · 5 bands · 32 s / 8 lags",
    "ridge_w32_sub16": "Ridge · 5 bands · 32 s / 16 lags", "ridge_w32_sub32": "Ridge · 5 bands · 32 s / 32 lags",
    "ridge_w48_sub24": "Ridge · 5 bands · 48 s / 24 lags", "ridge_w64_sub32": "Ridge · 5 bands · 64 s / 32 lags",
    "ridge_fine": "Ridge · 1 Hz bins · 16 s / 4 lags", "ridge_fine_w32": "Ridge · 1 Hz bins · 32 s / 8 lags",
    "ridge_fine_w32_sub16": "Ridge · 1 Hz bins · 32 s / 16 lags",
    "ridge_fine_w32_sub32": "Ridge · 1 Hz bins · 32 s / 32 lags",
    "hgb_bandpower": "Boosted trees · 16 s / 4 lags", "hgb_w32_sub16": "Boosted trees · 32 s / 16 lags",
    "ridge_fine_w24_sub12": "Ridge · 1 Hz bins · 24 s / 12 lags", "win32": "NeuroBOLT · 32 s window",
    "msslog": "NeuroBOLT · log spectra",
}
# Shared 7-ROI model arms (m7_*) reuse the single-ROI change names
LABELS.update({f"m7_{arm}": "Shared model · " + LABELS[arm].split(" · ", 1)[1]
               for arm in ("nohp", "softmax", "beta099", "nobaseline", "win8", "win24", "lr1e4", "msslog", "win32")})


def baseline_for(arm, baseline="base"):
    """Shared-model arms compare with the shared baseline, everything else with the per-ROI one."""
    return "multi7" if arm.startswith("m7_") else baseline


def arm_seed_means(path, split="test"):
    """{arm: {seed: mean R over ROIs and scans}}, keeping only seeds with all seven ROIs."""
    cells = defaultdict(list)
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["split"] == split:
            cells[(row["arm"], row["seed"], row["roi"])].append(float(row["corr"]))
    per_seed = defaultdict(dict)
    for arm, seed in {(a, s) for a, s, _ in cells}:
        rois = [np.mean(v) for (a, s, _), v in cells.items() if a == arm and s == seed]
        if len(rois) == N_ROIS:
            per_seed[arm][seed] = float(np.mean(rois))
    return per_seed


def draw(per_seed, path, c, baseline="base", labels=None):
    arms = sorted(per_seed, key=lambda a: np.mean(list(per_seed[a].values())))
    fig, ax = plt.subplots(figsize=(9.5, 0.42 * len(arms) + 1.4), facecolor=c["surface"])
    ax.set_facecolor(c["surface"])
    for i, arm in enumerate(arms):
        color = c["linear"] if arm.startswith(("ridge", "hgb")) else c["neural"]
        values = list(per_seed[arm].values())
        ax.plot([min(values), max(values)], [i, i], color=color, linewidth=2, alpha=0.35, solid_capstyle="round")
        ax.scatter(values, [i] * len(values), s=22, color=color, alpha=0.6, linewidths=0, zorder=3)
        ax.scatter([np.mean(values)], [i], s=60, color=color, edgecolors=c["surface"], linewidths=1.5, zorder=4)
        seeds = f"  ({len(values)} seeds)" if len(values) > 1 else ""
        ax.text(max(values) + 0.002, i, f"{np.mean(values):.3f}{seeds}", va="center", fontsize=8.5,
                color=c["ink_2"])
    if baseline in per_seed:
        ax.axvline(np.mean(list(per_seed[baseline].values())), color=c["muted"], linewidth=1, zorder=1)
    ax.set_yticks(range(len(arms)), [(labels or {}).get(a, a) for a in arms], fontsize=9, color=c["ink"])
    ax.set_xlabel("Test R, averaged over 7 ROIs and 6 held-out scans", fontsize=9, color=c["ink_2"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(c["axis"])
    ax.tick_params(axis="x", colors=c["muted"], labelcolor=c["ink_2"], labelsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=c["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=c["neural"], label="NeuroBOLT variant"),
               plt.Line2D([], [], marker="o", linestyle="", color=c["linear"], label="Band-power baseline"),
               plt.Line2D([], [], color=c["muted"], linewidth=1, label="NeuroBOLT baseline mean")]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5, labelcolor=c["ink_2"])
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=c["surface"])
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", default="reports/hypotheses")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    per_seed = arm_seed_means(args.runs)
    for theme, suffix in (("light", ""), ("dark", "_dark")):
        draw(per_seed, os.path.join(args.out, f"arms_overview{suffix}.png"), THEMES[theme], labels=LABELS)
    for arm in sorted(per_seed, key=lambda a: -np.mean(list(per_seed[a].values()))):
        values = per_seed[arm]
        print(f"{arm:20s} mean {np.mean(list(values.values())):.4f}  seeds " +
              " ".join(f"{s}:{v:.4f}" for s, v in sorted(values.items())))


if __name__ == "__main__":
    main()
