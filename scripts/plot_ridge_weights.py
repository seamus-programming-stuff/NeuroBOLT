#!/usr/bin/env python3
"""Heatmaps of the band-power ridge weights: frequency x time-before-the-BOLD-frame, per ROI.

    python scripts/plot_ridge_weights.py --weights weights.npz --out reports/hypotheses

Weights (from ridge_weights.py) are averaged over channels. Positive weight means more power at
that frequency and lag predicts higher BOLD. One shared, symmetric colour scale across ROIs, on a
blue-grey-red diverging ramp; drawn once per theme.
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

THEMES = {  # diverging poles: palette blue and red; neutral grey midpoint for each surface
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink_2": "#52514e", "muted": "#898781",
              "low": "#2a78d6", "mid": "#f0efec", "high": "#e34948"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink_2": "#c3c2b7", "muted": "#898781",
             "low": "#3987e5", "mid": "#383835", "high": "#e66767"},
}
SHORT = {"Cuneus": "Cuneus", "Heschl’s gyrus": "Heschl's gyrus", "Middle frontal gyrus anterior": "Middle frontal",
         "Precuneus anterior": "Precuneus anterior", "Putamen": "Putamen", "Thalamus": "Thalamus",
         "global signal clean": "Global signal"}


def draw(z, path, c):
    weights = z["weights"].mean(axis=1)  # (roi, band, lag), averaged over channels
    limit = float(np.percentile(np.abs(weights), 99))
    cmap = LinearSegmentedColormap.from_list("div", [c["low"], c["mid"], c["high"]])
    freqs = (z["band_lo"] + z["band_hi"]) / 2
    lag_mid = -(z["lag_start_sec"] + z["lag_end_sec"]) / 2  # negative: seconds before the frame
    fig, axes = plt.subplots(2, 4, figsize=(15, 7.2), facecolor=c["surface"], sharex=True, sharey=True)
    for ax, roi, w in zip(axes.flat, z["rois"], weights):
        ax.set_facecolor(c["surface"])
        image = ax.pcolormesh(lag_mid, freqs, w, cmap=cmap, vmin=-limit, vmax=limit, shading="nearest")
        ax.set_title(SHORT.get(str(roi), str(roi)), fontsize=10.5, color=c["ink"], loc="left")
        for side in ax.spines.values():
            side.set_visible(False)
        ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=8.5, length=2)
        for band_edge in (4, 8, 13, 30):
            ax.axhline(band_edge, color=c["muted"], linewidth=0.5, alpha=0.6)
    axes.flat[-1].axis("off")
    for ax in axes[1]:
        ax.set_xlabel("Seconds before the BOLD frame", fontsize=9, color=c["ink_2"])
    for ax in axes[:, 0]:
        ax.set_ylabel("Frequency (Hz)", fontsize=9, color=c["ink_2"])
    bar = fig.colorbar(image, ax=axes.flat[-1], location="left", fraction=0.6, shrink=0.8, pad=0.0)
    bar.set_label("Ridge weight per SD of log power,\naveraged over channels", fontsize=9, color=c["ink_2"])
    bar.ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=8)
    bar.outline.set_visible(False)
    axes.flat[-1].text(0.62, 0.5, "Red: more power predicts\nhigher BOLD.\nBlue: lower BOLD.\n\nGrey lines: 4, 8, 13\nand 30 Hz band edges.",
                       transform=axes.flat[-1].transAxes, va="center", fontsize=9, color=c["ink_2"])
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=c["surface"])
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--out", default="reports/hypotheses")
    args = parser.parse_args()
    z = np.load(args.weights)
    for theme, suffix in (("light", ""), ("dark", "_dark")):
        draw(z, os.path.join(args.out, f"ridge_weights{suffix}.png"), THEMES[theme])
    weights = z["weights"].mean(axis=1)
    freqs = (z["band_lo"] + z["band_hi"]) / 2
    lag_mid = (z["lag_start_sec"] + z["lag_end_sec"]) / 2
    alpha = (freqs >= 8) & (freqs < 13)
    for roi, w in zip(z["rois"], weights):
        profile = w[alpha].mean(axis=0)
        peak = np.argmax(np.abs(profile))
        print(f"{str(roi)[:22]:22s} alpha-band weight peaks {lag_mid[peak]:.0f} s before the frame "
              f"({profile[peak]:+.4f}); strongest frequency {freqs[np.argmax(np.abs(w).max(axis=1))]:.1f} Hz")


if __name__ == "__main__":
    main()
