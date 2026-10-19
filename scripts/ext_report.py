#!/usr/bin/env python3
"""Tables and figures for the ds006040 external validation and the arousal-monitor prototype.

    python scripts/ext_report.py --data reports/external/data --vu-maps reports/interpretability/data/maps.npz \
        --out reports/external

Inputs in --data (copied from $M3_OUT/ext by scripts/refresh_ext_report.sh): transfer.csv,
mismatched_null.csv, coupling_ext.npz, monitor_runs.csv, demo.json. Writes tables.md and PNG figures
(light and *_dark).
"""
import argparse
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interp_report import THEMES, ci, save, style  # noqa: E402

ROI7 = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior", "Putamen", "Thalamus",
        "global signal clean"]
PROTOCOLS = ["zero-shot", "target-stats", "in-domain", "pooled"]
PROTOCOL_LABELS = {"zero-shot": "Zero-shot (VU statistics)", "target-stats": "Zero-shot + new-site EEG statistics",
                   "in-domain": "Trained within ds006040", "pooled": "VU + ds006040 pooled"}
LAG_CENTRES = 24 - 2.0 * np.arange(12) - 1.0


def per_person(df):
    return df.groupby("subject")["corr"].mean()


def transfer_tables(tr, nulls, md):
    md.append("## Transfer to ds006040 (28 people, another site)\n")
    md.append("Mean R per run, averaged within person, then over people (95% CI over people).\n")
    out = {}
    for tset, label, rois in (("all65", "7 ROIs", ROI7), ("all65", "65 targets", None), ("gsr64", "64 regions after GSR", None)):
        md.append(f"### {label}\n")
        md.append("| Model | Protocol | Eyes closed | Eyes open |")
        md.append("|---|---|---|---|")
        sub = tr[tr["targets"] == tset]
        if rois:
            sub = sub[sub["roi"].isin(rois)]
        for model in ("full", "bands60", "vigilance"):
            for protocol in PROTOCOLS:
                cells = []
                for cond in ("EC", "EO"):
                    d = sub[(sub["model"] == model) & (sub["protocol"] == protocol) & (sub["condition"] == cond)]
                    if not len(d):
                        cells.append("–")
                        continue
                    m, lo, hi = ci(per_person(d))
                    out[(tset, label, model, protocol, cond)] = (m, lo, hi)
                    cells.append(f"{m:.3f} ({lo:.3f} to {hi:.3f})")
                md.append(f"| {model} | {PROTOCOL_LABELS[protocol]} | " + " | ".join(cells) + " |")
        md.append("")
    md.append("Mismatched-person null (one person's prediction vs another person's BOLD, same condition, 7 ROIs): " +
              ", ".join(f"{c} {g['corr'].mean():+.3f} (SD {g['corr'].std():.3f})" for c, g in nulls.groupby("condition")) + "\n")
    # paired: target-stats vs zero-shot, EC vs EO, full model 7 ROIs
    sub = tr[(tr["targets"] == "all65") & tr["roi"].isin(ROI7) & (tr["model"] == "full")]
    pp = sub.groupby(["protocol", "condition", "subject"])["corr"].mean().unstack(["protocol", "condition"])
    lines = []
    for a, b, text in ((("target-stats", "EC"), ("zero-shot", "EC"), "new-site statistics vs VU statistics, eyes closed"),
                       (("target-stats", "EC"), ("target-stats", "EO"), "eyes closed vs eyes open (new-site statistics)"),
                       (("in-domain", "EC"), ("target-stats", "EC"), "trained within ds006040 vs transferred, eyes closed"),
                       (("pooled", "EC"), ("in-domain", "EC"), "pooled vs within-ds006040, eyes closed")):
        if a in pp and b in pp:
            d = (pp[a] - pp[b]).dropna()
            m, lo, hi = ci(d)
            lines.append(f"- Δ {text}: {m:+.3f} ({lo:+.3f} to {hi:+.3f}), {int((d > 0).sum())} of {len(d)} people")
    md.append("Paired differences (full model, 7 ROIs):\n")
    md += lines + [""]
    # per-region transfer, best and worst (target-stats, EC, full)
    reg = tr[(tr["targets"] == "all65") & (tr["model"] == "full") & (tr["protocol"] == "target-stats") &
             (tr["condition"] == "EC")].groupby(["roi", "subject"])["corr"].mean().groupby("roi").mean().sort_values()
    md.append("Best regions (eyes closed, transferred): " + ", ".join(f"{r} {v:.2f}" for r, v in reg.tail(6)[::-1].items()))
    md.append("\nWorst regions: " + ", ".join(f"{r} {v:.2f}" for r, v in reg.head(4).items()) + "\n")
    return out


def transfer_figure(tr, nulls, out):
    sub = tr[(tr["targets"] == "all65") & tr["roi"].isin(ROI7) & (tr["model"] == "full")]
    for theme, c in THEMES.items():
        fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor=c["surface"])
        style(ax, c)
        for k, cond in enumerate(("EC", "EO")):
            for i, protocol in enumerate(PROTOCOLS):
                d = sub[(sub["protocol"] == protocol) & (sub["condition"] == cond)]
                if not len(d):
                    continue
                pp = per_person(d)
                m, lo, hi = ci(pp)
                x = i + (k - 0.5) * 0.3
                color = c["s2"] if cond == "EC" else c["s1"]
                ax.scatter(np.full(len(pp), x) + np.random.default_rng(i).uniform(-0.05, 0.05, len(pp)), pp, s=9,
                           color=color, alpha=0.35, linewidth=0)
                ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="o", color=color, markersize=6, capsize=0, linewidth=2,
                            label=("Eyes closed" if cond == "EC" else "Eyes open") if i == 0 else None)
        nm = nulls["corr"]
        ax.axhspan(np.percentile(nm, 2.5), np.percentile(nm, 97.5), color=c["grid"], zorder=0,
                   label="Mismatched-person null (95%)")
        ax.axhline(0, color=c["axis"], linewidth=0.8)
        ax.set_xticks(range(len(PROTOCOLS)), [PROTOCOL_LABELS[p].replace(" + ", "\n+ ").replace(" pooled", "\npooled")
                                              .replace("Trained within", "Trained\nwithin") for p in PROTOCOLS], fontsize=8)
        ax.set_ylabel("R per person, mean of 7 ROIs", fontsize=9, color=c["ink_2"])
        ax.legend(frameon=False, fontsize=8, labelcolor=c["ink_2"], loc="upper left")
        save(fig, out, "ext_transfer", theme, c)


def coupling_figure(cext, vu_maps, out, md):
    labels = [str(l) for l in cext["labels"]]
    bands = [str(b) for b in cext["bands"]]
    vu_labels = [str(l) for l in vu_maps["labels"]]
    targets = [("global signal clean", "Global signal"), ("Cuneus", "Cuneus"), ("Thalamus", "Thalamus")]
    md.append("## Do the coupling signatures replicate?\n")
    md.append("Within-run correlation of channel-averaged band power with BOLD, by lag; strongest value and its lag.\n")
    md.append("| Target | Band | VU (29 scans, eyes closed) | ds006040 eyes closed | ds006040 eyes open |")
    md.append("|---|---|---|---|---|")
    for lab, name in targets:
        for band in ("alpha", "beta", "theta"):
            cells = []
            for src, arr, lbls in (("vu", vu_maps["band_coupling"], vu_labels), ("EC", cext["EC_r"], labels),
                                   ("EO", cext["EO_r"], labels)):
                prof = arr[bands.index(band), :, lbls.index(lab)]
                j = int(np.argmax(np.abs(prof)))
                cells.append(f"{prof[j]:+.3f} at {LAG_CENTRES[j]:.0f} s")
            md.append(f"| {name} | {band} | " + " | ".join(cells) + " |")
    md.append("")
    for theme, c in THEMES.items():
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), facecolor=c["surface"], sharey=True)
        for ax, (lab, name) in zip(axes, targets):
            style(ax, c)
            for src, arr, lbls, color, ls in (("VU, eyes closed", vu_maps["band_coupling"], vu_labels, c["muted"], "-"),
                                              ("ds006040, eyes closed", cext["EC_r"], labels, c["s2"], "-"),
                                              ("ds006040, eyes open", cext["EO_r"], labels, c["s1"], "--")):
                ax.plot(-LAG_CENTRES, arr[bands.index("alpha"), :, lbls.index(lab)], color=color, linewidth=2,
                        linestyle=ls, label=src)
            ax.axhline(0, color=c["axis"], linewidth=0.8)
            ax.set_title(name, fontsize=10, color=c["ink"], loc="left")
            ax.set_xlabel("Seconds before the BOLD frame", fontsize=8.5, color=c["ink_2"])
        axes[0].set_ylabel("r, alpha power vs BOLD", fontsize=9, color=c["ink_2"])
        axes[0].legend(frameon=False, fontsize=7.5, labelcolor=c["ink_2"], loc="lower left")
        fig.tight_layout()
        save(fig, out, "ext_coupling", theme, c)


def monitor_section(mon, demo, out, md):
    md.append("## Arousal-monitor prototype on ds006040\n")
    md.append("| Condition | Runs | r predicted vs measured global BOLD, offline | Streaming (causal) | Streaming vs offline agreement |")
    md.append("|---|---|---|---|---|")
    for cond, d in mon.groupby("condition"):
        pp = d.groupby("subject")[["r_offline", "r_streaming"]].mean()
        m1, l1, h1 = ci(pp["r_offline"])
        m2, l2, h2 = ci(pp["r_streaming"])
        md.append(f"| {'Eyes closed' if cond == 'EC' else 'Eyes open'} | {len(d)} | {m1:.3f} ({l1:.3f} to {h1:.3f}) | "
                  f"{m2:.3f} ({l2:.3f} to {h2:.3f}) | {d['r_stream_vs_offline'].mean():.3f} |")
    md.append(f"\nMedian compute time per fMRI volume (streaming, one CPU core): {mon['latency_ms_median'].median():.0f} ms.\n")
    md.append("QC validity across runs (Spearman ρ):\n")
    md.append("| EEG-derived measure | vs measured global-signal swing (raw SD) | vs how predictable the run is (r offline) | vs head motion (mean FD) |")
    md.append("|---|---|---|---|")
    for key, name in (("arousal_fluctuation", "Arousal fluctuation (SD of predicted global BOLD)"),
                      ("vigilance_sd", "Vigilance-index SD")):
        cells = []
        for target in ("measured_gs_sd_raw", "r_offline", "mean_fd"):
            rho, p = stats.spearmanr(mon[key], mon[target])
            cells.append(f"{rho:+.2f} (p = {p:.2g})")
        md.append(f"| {name} | " + " | ".join(cells) + " |")
    md.append("")
    for theme, c in THEMES.items():
        fig, ax = plt.subplots(figsize=(4.6, 3.6), facecolor=c["surface"])
        style(ax, c)
        for cond, color, name in (("EC", c["s2"], "Eyes closed"), ("EO", c["s1"], "Eyes open")):
            d = mon[mon["condition"] == cond]
            ax.scatter(d["arousal_fluctuation"], d["measured_gs_sd_raw"], s=22, color=color, edgecolor=c["surface"],
                       linewidth=1, label=name)
        ax.set_xlabel("EEG-derived arousal fluctuation", fontsize=9, color=c["ink_2"])
        ax.set_ylabel("Measured global-signal swing (raw SD)", fontsize=9, color=c["ink_2"])
        ax.legend(frameon=False, fontsize=8, labelcolor=c["ink_2"])
        save(fig, out, "ext_qc", theme, c)
    if demo:
        run = max(demo, key=lambda r: demo[r]["r"])
        d = demo[run]
        for theme, c in THEMES.items():
            fig, axes = plt.subplots(2, 1, figsize=(8.6, 4.4), sharex=True, facecolor=c["surface"])
            t = np.array(d["t"]) / 60
            for ax in axes:
                style(ax, c)
                for ep in d["episodes"]:
                    ax.axvspan(ep["start_s"] / 60, ep["end_s"] / 60, color=c["band"], zorder=0, linewidth=0)
            axes[0].plot(t, d["vigilance_z"], color=c["ink"], linewidth=1.3)
            axes[0].axhline(-1, color=c["muted"], linewidth=0.8, linestyle="--")
            axes[0].set_ylabel("Vigilance (z)", fontsize=9, color=c["ink_2"])
            z = lambda a: (np.array(a) - np.mean(a)) / np.std(a)  # noqa: E731
            axes[1].plot(t, z(d["pred_global"]), color=c["s2"], linewidth=2, label="Predicted from EEG")
            axes[1].plot(t, z(d["measured_global"]), color=c["s1"], linewidth=1.4, label="Measured fMRI global signal")
            axes[1].set_ylabel("Global BOLD (z)", fontsize=9, color=c["ink_2"])
            axes[1].set_xlabel(f"Minutes ({run.replace('_', ', ')}; r = {d['r']:.2f}; shaded: flagged low vigilance)",
                               fontsize=8.5, color=c["ink_2"])
            axes[1].legend(frameon=False, fontsize=8, labelcolor=c["ink_2"], loc="upper right")
            fig.tight_layout()
            save(fig, out, "ext_monitor_example", theme, c)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="reports/external/data")
    parser.add_argument("--vu-maps", default="reports/interpretability/data/maps.npz")
    parser.add_argument("--out", default="reports/external")
    args = parser.parse_args()
    path = lambda n: os.path.join(args.data, n)  # noqa: E731
    md = ["# External validation tables\n", "Generated by scripts/ext_report.py.\n"]
    if os.path.isfile(path("transfer.csv")):
        tr = pd.read_csv(path("transfer.csv"))
        nulls = pd.read_csv(path("mismatched_null.csv"))
        transfer_tables(tr, nulls, md)
        transfer_figure(tr, nulls, args.out)
    if os.path.isfile(path("coupling_ext.npz")):
        coupling_figure(np.load(path("coupling_ext.npz")), np.load(args.vu_maps), args.out, md)
    if os.path.isfile(path("monitor_runs.csv")):
        demo = json.load(open(path("demo.json"), encoding="utf-8")) if os.path.isfile(path("demo.json")) else {}
        monitor_section(pd.read_csv(path("monitor_runs.csv")), demo, args.out, md)
    with open(os.path.join(args.out, "tables.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
