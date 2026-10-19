"""Write the monitor's outputs: frames.csv, summary.json and a two-panel figure."""
import csv
import json
import os

import numpy as np


def write(out_dir, frames, summary, measured_global=None, title=""):
    os.makedirs(out_dir, exist_ok=True)
    keys = list(frames)
    if measured_global is not None:
        frames = {**frames, "measured_global": measured_global}
        keys.append("measured_global")
        r = float(np.corrcoef(frames["pred_global"], measured_global)[0, 1])
        summary = {**summary, "r_predicted_vs_measured_global": r}
    with open(os.path.join(out_dir, "frames.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(keys)
        for i in range(len(frames["time_s"])):
            writer.writerow([f"{frames[k][i]:.4f}" if isinstance(frames[k][i], (float, np.floating)) else frames[k][i]
                             for k in keys])
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)
    figure(os.path.join(out_dir, "monitor.png"), frames, summary, title)
    return summary


def figure(path, frames, summary, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, muted, grid, orange, blue = "#1c1b19", "#6b6860", "#e1e0d9", "#eb6834", "#2a78d6"
    t = np.asarray(frames["time_s"]) / 60
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, facecolor="#fcfcfb")
    for ax in axes:
        ax.set_facecolor("#fcfcfb")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="y", color=grid, linewidth=0.6)
        ax.tick_params(colors=muted, labelsize=8.5)
        for ep in summary["low_vigilance_episodes"]:
            ax.axvspan(ep["start_s"] / 60, ep["end_s"] / 60, color="#f3e1d6", zorder=0, linewidth=0)
    axes[0].plot(t, frames["vigilance_z"], color=ink, linewidth=1.4)
    axes[0].axhline(-1, color=muted, linewidth=0.8, linestyle="--")
    axes[0].set_ylabel("EEG vigilance (robust z)", fontsize=9, color=muted)
    axes[0].set_title(title or "EEG arousal monitor", fontsize=10.5, color=ink, loc="left")
    axes[1].plot(t, frames["pred_global"], color=orange, linewidth=1.8, label="Predicted from EEG")
    if "measured_global" in frames:
        axes[1].plot(t, frames["measured_global"], color=blue, linewidth=1.4, label="Measured (fMRI)")
        axes[1].legend(frameon=False, fontsize=8.5, labelcolor=muted, loc="upper right")
    axes[1].set_ylabel("Global BOLD", fontsize=9, color=muted)
    axes[1].set_xlabel("Minutes (shaded: low-vigilance episodes)", fontsize=9, color=muted)
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor="#fcfcfb")
    plt.close(fig)
