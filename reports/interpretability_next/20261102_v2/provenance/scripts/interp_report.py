#!/usr/bin/env python3
"""Tables and figures for the interpretability report, from the M3 outputs copied into one folder.

    python scripts/interp_report.py --data reports/interpretability/data --out reports/interpretability

Inputs in --data (see scripts/refresh_interp_report.sh): cv_scores.csv, raw/predictions_eeg_full.npz,
nonlinear_scores.csv, attribution_permutation.csv, attribution_surrogate.csv, maps.npz,
labels_64_dictionary.csv and maps.nii.gz (DiFuMo-64). Missing inputs skip their sections.
Writes tables.md and one PNG per figure and theme (light, and *_dark).
"""
import argparse
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interp_cv import BANDS, LAG_CENTRES, spm_hrf  # noqa: E402

THEMES = {  # same tokens as plot_hypotheses.py and plot_ridge_weights.py
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink_2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7", "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a",
              "low": "#2a78d6", "mid": "#f0efec", "high": "#e34948", "band": "#d6e6f8"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink_2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835", "s1": "#3987e5", "s2": "#d95926", "s3": "#199e70",
             "low": "#3987e5", "mid": "#383835", "high": "#e66767", "band": "#1f3550"},
}
ROI7 = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior", "Putamen", "Thalamus",
        "global signal clean"]
SHORT = {"Cuneus": "Cuneus", "Heschl’s gyrus": "Heschl's", "Middle frontal gyrus anterior": "Mid. frontal",
         "Precuneus anterior": "Precuneus", "Putamen": "Putamen", "Thalamus": "Thalamus",
         "global signal clean": "Global"}
NETWORKS = {"VisCent": "Visual", "SomMotA": "Somatomotor", "DorsAttnB": "Dorsal attention",
            "SalVentAttnA": "Salience", "ContA": "Control", "DefaultB": "Default"}
SPECIAL = {"Thalamus": "Subcortical", "Putamen": "Subcortical", "Caudate": "Subcortical",
           "Cerebellum I-V": "Cerebellum", "Cerebellum Crus II": "Cerebellum",
           "ventricles": "Ventricles, sinus, fornix", "Transverse sinus": "Ventricles, sinus, fornix",
           "Superior fornix and isthmus": "Ventricles, sinus, fornix", "Fusiform gyrus": "Visual"}
NETWORK_ORDER = ["Visual", "Somatomotor", "Dorsal attention", "Salience", "Control", "Default", "Subcortical",
                 "Cerebellum", "Ventricles, sinus, fornix", "Global signal"]
SET_LABELS = {
    "eeg_full": "EEG: 26 channels × 44 1 Hz bins × 12 lags", "bands60": "EEG: 5 bands, channel-averaged × 12 lags",
    "regional300": "EEG: 5 bands × 5 scalp regions × 12 lags", "vigilance": "EEG: vigilance index × 12 lags",
    "hrf_canon": "EEG: channels × bins, canonical-HRF weighted (no free lags)",
    "hrf_3basis": "EEG: channels × bins × HRF + 2 derivatives", "time": "Time in scan only",
    "eeg+time": "EEG + time in scan", "eog": "Eye channels (EOG) only", "emg": "Muscle channels (EMG) only",
    "ecg_hr": "ECG power + heart rate only", "physio": "EOG + EMG + ECG + heart rate",
    "eeg+physio": "EEG + EOG + EMG + ECG + heart rate", "bands60+physio": "5 EEG bands + physiology",
    "hr": "Heart rate only", "eog_slow": "EOG below 4 Hz only (eye movements, blinks)",
    "emg_high": "EMG above 30 Hz only (muscle)", "phys_specific": "Heart rate + slow EOG + high EMG",
    "eeg+phys_specific": "EEG + heart rate + slow EOG + high EMG", "eeg+hr": "EEG + heart rate",
    "eeg_cwlsub": "EEG only (19 scans)", "cwl": "Motion loops only (19 scans)", "eeg+cwl": "EEG + motion loops (19 scans)",
    "physio_cwlsub": "Physiology only (19 scans)", "physio+cwl": "Physiology + motion loops (19 scans)",
    "phys_specific_cwlsub": "Heart rate + slow EOG + high EMG (19 scans)",
    "phys_specific+cwl": "Specific physiology + motion loops (19 scans)",
    "eeg+phys_specific+cwl": "EEG + specific physiology + motion loops (19 scans)",
}


def person(scan):
    return re.match(r"sub\d+", scan).group(0)


def network_of(name, yeo):
    if name == "global signal clean":
        return "Global signal"
    return SPECIAL.get(name, NETWORKS.get(yeo.get(name, ""), "Other"))


def by_person(df, value="corr"):
    """Per-person mean of value (mean over that person's scans of the scan-level value)."""
    return df.groupby("person")[value].mean()


def ci(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    half = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    return values.mean(), values.mean() - half, values.mean() + half


def style(ax, c):
    ax.set_facecolor(c["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(c["axis"])
    ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=8.5, length=2)
    ax.grid(axis="y", color=c["grid"], linewidth=0.6)
    ax.set_axisbelow(True)


def save(fig, out, name, theme, c):
    suffix = "" if theme == "light" else "_dark"
    fig.savefig(os.path.join(out, f"{name}{suffix}.png"), dpi=150, facecolor=c["surface"], bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- feature-set table
def feature_table(cv, md):
    cv = cv.copy()
    cv["person"] = cv["scan"].map(person)
    sets = [s for s in SET_LABELS if s in set(cv["features"])]
    ref = {}
    md.append("## Feature sets (ridge, 5-fold subject-grouped CV)\n")
    md.append("Mean R per held-out scan, averaged within person, then over people (95% CI over people). "
              "Δ is paired by person against EEG-only on the same scans.\n")
    md.append("| Features | 7 ROIs | Δ vs EEG (7 ROIs) | All 65 targets | 64 regions after GSR | People |")
    md.append("|---|---|---|---|---|---|")
    for s in sets:
        sub = cv[cv["features"] == s]
        roi7 = sub[(sub["targets"] == "all65") & sub["roi"].isin(ROI7)].groupby(["scan", "person"])["corr"].mean().reset_index()
        all65 = sub[sub["targets"] == "all65"].groupby(["scan", "person"])["corr"].mean().reset_index()
        gsr = sub[sub["targets"] == "gsr64"].groupby(["scan", "person"])["corr"].mean().reset_index()
        p7 = by_person(roi7)
        ref_name = "eeg_cwlsub" if s.endswith("cwl") or s.endswith("cwlsub") else "eeg_full"
        if s == ref_name:
            ref[s] = p7
        delta = ""
        if s != ref_name and ref_name in ref:
            d = (p7 - ref[ref_name]).dropna()
            m, lo, hi = ci(d)
            delta = f"{m:+.3f} ({lo:+.3f} to {hi:+.3f})"
        m, lo, hi = ci(p7)
        md.append(f"| {SET_LABELS[s]} | {m:.3f} ({lo:.3f} to {hi:.3f}) | {delta} | {by_person(all65).mean():.3f} | "
                  f"{by_person(gsr).mean():.3f} | {int(p7.notna().sum())} |")
    md.append("")


# ---------------------------------------------------------------- nulls
def null_analysis(pred_file, out, md):
    z = np.load(pred_file)
    targets = [str(t) for t in z["targets"]]
    cols = [targets.index(f"all65|{r}") for r in ROI7]
    scans = sorted(k[5:] for k in z.files if k.startswith("pred_"))
    real, shift_null, rows = {}, {}, []
    for s in scans:
        p, t = z[f"pred_{s}"][:, cols], z[f"true_{s}"][:, cols]
        n = len(p)
        real[s] = np.mean([np.corrcoef(p[:, j], t[:, j])[0, 1] for j in range(len(cols))])
        shifts = range(30, n - 30, 2)
        shift_null[s] = np.array([np.mean([np.corrcoef(p[:, j], np.roll(t[:, j], k))[0, 1] for j in range(len(cols))])
                                  for k in shifts])
    mismatch = []
    for a in scans:
        for b in scans:
            if person(a) == person(b):
                continue
            pa, tb = z[f"pred_{a}"][:, cols], z[f"true_{b}"][:, cols]
            m = min(len(pa), len(tb))
            mismatch.append(np.mean([np.corrcoef(pa[:m, j], tb[:m, j])[0, 1] for j in range(len(cols))]))
    mismatch = np.array(mismatch)
    for s in scans:
        rows.append({"scan": s, "real": real[s], "null_mean": shift_null[s].mean(), "null_sd": shift_null[s].std(),
                     "null_95": np.percentile(shift_null[s], 95), "p": (1 + (shift_null[s] >= real[s]).sum()) / (1 + len(shift_null[s]))})
    df = pd.DataFrame(rows).sort_values("real")
    df.to_csv(os.path.join(out, "data", "nulls_per_scan.csv"), index=False)
    n_sig = int((df["p"] < 0.05).sum())
    group_null = np.mean([shift_null[s].std() for s in scans]) / np.sqrt(len(scans))
    md.append("## Chance level\n")
    md.append(f"- Per scan, ridge R (mean of 7 ROIs) against its circular-shift null (prediction vs the scan's own BOLD "
              f"shifted by ≥ 63 s): null mean {df['null_mean'].mean():+.3f}, null SD {df['null_sd'].mean():.3f}, "
              f"95th percentile {df['null_95'].mean():.3f} on average. {n_sig} of {len(df)} scans beat their own null at p < 0.05.")
    md.append(f"- Mismatched people (prediction for one person scored against another person's BOLD, "
              f"{len(mismatch)} pairs): mean R {mismatch.mean():+.3f} (2.5–97.5%: {np.percentile(mismatch, 2.5):+.3f} to "
              f"{np.percentile(mismatch, 97.5):+.3f}), against {np.mean(list(real.values())):.3f} for the matched scans.")
    md.append(f"- Over all 29 scans the circular-shift null of the mean has SD ≈ {group_null:.3f}.\n")
    for theme, c in THEMES.items():
        fig, ax = plt.subplots(figsize=(9, 3.6), facecolor=c["surface"])
        style(ax, c)
        x = np.arange(len(df))
        ax.vlines(x, df["null_mean"] - 2 * df["null_sd"], df["null_95"], color=c["axis"], linewidth=5, label="Circular-shift null (mean −2 SD to 95th pct)")
        ax.axhspan(np.percentile(mismatch, 2.5), np.percentile(mismatch, 97.5), color=c["grid"], zorder=0,
                   label="Mismatched-person null (95% range)")
        ax.scatter(x, df["real"], s=26, color=c["s2"], zorder=3, edgecolor=c["surface"], linewidth=1, label="Ridge, held-out scan")
        ax.axhline(0, color=c["axis"], linewidth=0.8)
        ax.set_xticks(x, df["scan"], rotation=90, fontsize=7)
        ax.set_ylabel("R, mean of 7 ROIs", fontsize=9, color=c["ink_2"])
        leg = ax.legend(frameon=False, fontsize=8, loc="upper left", labelcolor=c["ink_2"])
        save(fig, out, "nulls", theme, c)
    return df


# ---------------------------------------------------------------- whole brain
def region_table(cv, labels_csv):
    yeo = dict(zip(labels_csv["Difumo_names"], labels_csv["Yeo_networks7"]))
    cv = cv.copy()
    cv["person"] = cv["scan"].map(person)
    out = []
    for tset in ("all65", "gsr64"):
        sub = cv[(cv["features"] == "eeg_full") & (cv["targets"] == tset)]
        per = sub.groupby(["roi", "person"])["corr"].mean().groupby("roi").mean()
        for roi, r in per.items():
            out.append({"roi": roi, "targets": tset, "r": r, "network": network_of(roi, yeo)})
    return pd.DataFrame(out)


def global_loading(pred_file):
    """Per region: mean within-scan correlation of its true BOLD with the true global signal."""
    z = np.load(pred_file)
    targets = [str(t) for t in z["targets"]]
    all65 = [t for t in targets if t.startswith("all65|")]
    g = targets.index("all65|global signal clean")
    scans = sorted(k[5:] for k in z.files if k.startswith("true_"))
    load = {t[6:]: np.mean([np.corrcoef(z[f"true_{s}"][:, targets.index(t)], z[f"true_{s}"][:, g])[0, 1] for s in scans])
            for t in all65}
    return pd.Series(load)


def whole_brain(cv, labels_csv, pred_file, atlas_file, out, md):
    regions = region_table(cv, labels_csv)
    wide = regions.pivot(index="roi", columns="targets", values="r")
    wide["network"] = regions.drop_duplicates("roi").set_index("roi")["network"]
    if pred_file:
        wide["gs_loading"] = global_loading(pred_file)
    wide.to_csv(os.path.join(out, "data", "regions.csv"))
    md.append("## Whole brain\n")
    md.append("| Network | Regions | R (raw BOLD) | R after global-signal regression |")
    md.append("|---|---|---|---|")
    for net in NETWORK_ORDER:
        sel = wide[wide["network"] == net]
        if len(sel):
            md.append(f"| {net} | {len(sel)} | {sel['all65'].mean():.3f} | {sel['gsr64'].mean():.3f} |")
    md.append("")
    ranked = wide.sort_values("all65", ascending=False)
    md.append("Best: " + ", ".join(f"{r} {v:.2f}" for r, v in ranked["all65"].head(8).items()))
    md.append("\nWorst: " + ", ".join(f"{r} {v:.2f}" for r, v in ranked["all65"].tail(8).items()))
    if "gs_loading" in wide:
        sel = wide.drop(index="global signal clean", errors="ignore")
        rho, p = stats.spearmanr(sel["gs_loading"], sel["all65"])
        rho2, p2 = stats.spearmanr(sel["gs_loading"], sel["gsr64"])
        md.append(f"\nAcross the 64 regions, predictability tracks how strongly a region follows the global signal: "
                  f"Spearman ρ = {rho:+.2f} (p = {p:.1g}) on raw BOLD, {rho2:+.2f} (p = {p2:.1g}) after GSR.\n")
        for theme, c in THEMES.items():
            fig, axes = plt.subplots(1, 2, figsize=(10, 4), facecolor=c["surface"], sharex=True)
            for ax, col, title in zip(axes, ("all65", "gsr64"), ("Raw BOLD", "After global-signal regression")):
                style(ax, c)
                ax.scatter(sel["gs_loading"], sel[col], s=22, color=c["s2"], edgecolor=c["surface"], linewidth=1)
                for roi in ("Thalamus", "ventricles", "Transverse sinus", "Heschl’s gyrus", "Cuneus", "Putamen"):
                    if roi in sel.index:
                        ax.annotate(SHORT.get(roi, roi), (sel.loc[roi, "gs_loading"], sel.loc[roi, col]), fontsize=7.5,
                                    color=c["ink_2"], xytext=(4, 2), textcoords="offset points")
                ax.axhline(0, color=c["axis"], linewidth=0.8)
                ax.set_title(title, fontsize=10, color=c["ink"], loc="left")
                ax.set_xlabel("Correlation of the region with the global signal", fontsize=9, color=c["ink_2"])
            axes[0].set_ylabel("Cross-subject ridge R", fontsize=9, color=c["ink_2"])
            fig.tight_layout()
            save(fig, out, "global_loading", theme, c)
    if atlas_file:
        brain_maps(wide, labels_csv, atlas_file, out)
    return wide


def brain_maps(wide, labels_csv, atlas_file, out):
    import nibabel as nib
    from nilearn import plotting
    img = nib.load(atlas_file)
    data = img.get_fdata()
    peak = data.max(axis=-1)
    label = data.argmax(axis=-1)
    mask = peak > np.percentile(peak[peak > 0], 40)
    names = list(labels_csv["Difumo_names"])
    for col, name in (("all65", "brain_r"), ("gsr64", "brain_r_gsr")):
        values = np.array([wide[col].get(n, np.nan) for n in names])
        vol = np.where(mask, values[label], 0.0)
        vol = np.nan_to_num(vol)
        out_img = nib.Nifti1Image(vol.astype(np.float32), img.affine)
        for theme, c in THEMES.items():
            ramp = LinearSegmentedColormap.from_list("seq", ["#fbe3d4", "#f2a679", c["s2"], "#8a3210"])
            display = plotting.plot_stat_map(out_img, display_mode="z", cut_coords=[-20, -4, 8, 24, 40, 56], cmap=ramp,
                                             vmin=0, vmax=0.5, symmetric_cbar=False, threshold=0.01,
                                             black_bg=theme == "dark", draw_cross=False, annotate=False, colorbar=True)
            suffix = "" if theme == "light" else "_dark"
            display.savefig(os.path.join(out, f"{name}{suffix}.png"), dpi=150)
            display.close()


# ---------------------------------------------------------------- physiology partition
def physio_partition(cv, out, md):
    cv = cv.copy()
    cv["person"] = cv["scan"].map(person)
    sub = cv[(cv["targets"] == "all65")]

    def r2(name):
        s = sub[sub["features"] == name]
        s = s.assign(r2=np.sign(s["corr"]) * s["corr"] ** 2)
        return s.groupby(["roi", "person"])["r2"].mean().groupby("roi").mean()

    for phys, both, title, fig_name in (
            ("physio", "eeg+physio", "all non-EEG channels (EOG, EMG, ECG power + heart rate)", "physio_partition_all"),
            ("phys_specific", "eeg+phys_specific", "EEG-free physiology (heart rate, EOG < 4 Hz, EMG > 30 Hz)",
             "physio_partition")):
        if not {"eeg_full", phys, both} <= set(sub["features"]):
            continue
        eeg, ph, bo = r2("eeg_full"), r2(phys), r2(both)
        part = pd.DataFrame({"unique EEG": bo - ph, "unique physiology": bo - eeg, "shared": eeg + ph - bo,
                             "EEG": eeg, "physiology": ph, "both": bo})
        part.to_csv(os.path.join(out, "data", f"{fig_name}.csv"))
        md.append(f"## EEG versus {title}: variance partition (cross-validated R²)\n")
        md.append("| Target | R² EEG | R² physiology | R² both | Unique EEG | Unique physiology | Shared |")
        md.append("|---|---|---|---|---|---|---|")
        for roi in ROI7:
            r = part.loc[roi]
            md.append(f"| {SHORT[roi]} | {r['EEG']:.3f} | {r['physiology']:.3f} | {r['both']:.3f} | {r['unique EEG']:.3f} | "
                      f"{r['unique physiology']:.3f} | {r['shared']:.3f} |")
        m = part.mean()
        md.append(f"| Mean of 65 | {m['EEG']:.3f} | {m['physiology']:.3f} | {m['both']:.3f} | {m['unique EEG']:.3f} | "
                  f"{m['unique physiology']:.3f} | {m['shared']:.3f} |\n")
        for theme, c in THEMES.items():
            fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=c["surface"])
            style(ax, c)
            names = ROI7 + ["Mean of 65"]
            rows = [part.loc[r] for r in ROI7] + [m]
            x = np.arange(len(names))
            bottom = np.zeros(len(names))
            for key, color in (("shared", c["axis"]), ("unique EEG", c["s2"]), ("unique physiology", c["s3"])):
                vals = np.array([max(r[key], 0) for r in rows])
                ax.bar(x, vals, bottom=bottom, color=color, width=0.62, label=key.capitalize(), edgecolor=c["surface"],
                       linewidth=2)
                bottom += vals
            ax.set_xticks(x, [SHORT.get(n, n) for n in names], fontsize=8.5)
            ax.set_ylabel("Cross-validated R²", fontsize=9, color=c["ink_2"])
            ax.legend(frameon=False, fontsize=8.5, labelcolor=c["ink_2"], loc="upper right")
            save(fig, out, fig_name, theme, c)


# ---------------------------------------------------------------- maps: HRF, coupling, patterns
CH_NAMES = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T7", "T8", "P7", "P8", "FPZ",
            "FZ", "CZ", "PZ", "POZ", "OZ", "FT9", "FT10", "TP9", "TP10"]


def montage_info():
    import mne
    rename = {"FP1": "Fp1", "FP2": "Fp2", "FPZ": "Fpz", "FZ": "Fz", "CZ": "Cz", "PZ": "Pz", "POZ": "POz", "OZ": "Oz"}
    info = mne.create_info([rename.get(n, n) for n in CH_NAMES], 200, "eeg")
    info.set_montage(mne.channels.make_standard_montage("standard_1005"))
    return info


def hrf_figure(maps, cv_lookup, out, md):
    lag = maps["rank1_lag"]
    se = maps["rank1_lag_se"]
    spec = maps["rank1_spectrum"]
    spec_se = maps["rank1_spectrum_se"]
    chan = maps["rank1_channel"]
    rois = [str(r) for r in maps["rois"]]
    seconds = LAG_CENTRES
    canon = spm_hrf(seconds)
    canon = canon / np.abs(canon).max()
    md.append("## Rank-1 separable model: an empirical EEG-to-BOLD impulse response\n")
    md.append("| ROI | Rank-1 CV R | Full ridge CV R | Peak of lag profile (s before frame) | Spectrum sign at alpha (8–13 Hz) |")
    md.append("|---|---|---|---|---|")
    freqs = np.arange(1, 45) + 0.5
    for j, roi in enumerate(rois):
        alpha_sign = spec[j][(freqs >= 8) & (freqs < 13)].mean()
        md.append(f"| {SHORT[roi]} | {maps['rank1_cv_r'][j]:.3f} | {cv_lookup.get(roi, float('nan')):.3f} | "
                  f"{seconds[np.argmax(lag[j])]:.0f} | {'negative' if alpha_sign < 0 else 'positive'} ({alpha_sign:+.3f}) |")
    md.append("")
    info = montage_info()
    import mne
    for theme, c in THEMES.items():
        fig = plt.figure(figsize=(13, 9.5), facecolor=c["surface"])
        grid = fig.add_gridspec(3, 7, height_ratios=[1, 1, 0.9], hspace=0.55, wspace=0.35)
        for j, roi in enumerate(rois):
            ax = fig.add_subplot(grid[0, j])
            style(ax, c)
            ax.fill_between(-seconds, lag[j] - 2 * se[j], lag[j] + 2 * se[j], color=c["band"], linewidth=0)
            ax.plot(-seconds, canon, color=c["muted"], linewidth=1.2, linestyle="--")
            ax.plot(-seconds, lag[j], color=c["s2"], linewidth=2)
            ax.axhline(0, color=c["axis"], linewidth=0.7)
            ax.set_title(SHORT[roi], fontsize=10, color=c["ink"], loc="left")
            ax.set_ylim(-0.8, 1.15)
            if j == 0:
                ax.set_ylabel("Lag profile (max = 1)", fontsize=8.5, color=c["ink_2"])
            ax.set_xlabel("s before frame", fontsize=8, color=c["ink_2"])
            ax2 = fig.add_subplot(grid[1, j])
            style(ax2, c)
            ax2.fill_between(freqs, spec[j] - 2 * spec_se[j], spec[j] + 2 * spec_se[j], color=c["band"], linewidth=0)
            ax2.plot(freqs, spec[j], color=c["s2"], linewidth=1.8)
            ax2.axhline(0, color=c["axis"], linewidth=0.7)
            for edge in (4, 8, 13, 30):
                ax2.axvline(edge, color=c["grid"], linewidth=0.8)
            if j == 0:
                ax2.set_ylabel("Spectrum weight", fontsize=8.5, color=c["ink_2"])
            ax2.set_xlabel("Hz", fontsize=8, color=c["ink_2"])
            ax3 = fig.add_subplot(grid[2, j])
            ax3.set_facecolor(c["surface"])
            limit = np.abs(chan[j]).max()
            mne.viz.plot_topomap(chan[j], info, axes=ax3, show=False, cmap=LinearSegmentedColormap.from_list(
                "div", [c["low"], c["mid"], c["high"]]), vlim=(-limit, limit), contours=0, sensors=True)
        fig.text(0.01, 0.98, "Top: lag profile (orange; band = ±2 jackknife SE over people) vs canonical HRF (dashed). "
                 "Middle: spectrum (sign carries the coupling). Bottom: channel weights.", fontsize=9, color=c["ink_2"], va="top")
        save(fig, out, "empirical_hrf", theme, c)


def coupling_figures(maps, region_wide, out, md):
    """Model-free alpha-BOLD coupling by lag for every region, and coupling vs pattern for the 7 ROIs."""
    band = maps["band_coupling"]  # (5 bands, 12 lags, 65 targets)
    band_t = maps["band_coupling_t"]
    labels = [str(l) for l in maps["labels"]]
    bands = [str(b) for b in maps["bands"]]
    alpha = band[bands.index("alpha")]
    order = sorted(range(len(labels)), key=lambda i: (NETWORK_ORDER.index(region_wide.loc[labels[i], "network"])
                                                      if labels[i] in region_wide.index else 99, alpha[:, i].min()))
    md.append("## Model-free EEG–BOLD coupling\n")
    md.append("Within-scan correlation of channel-averaged band power with BOLD, averaged over 29 scans; "
              "t over scans in brackets; lag of the strongest coupling.\n")
    md.append("| Target | Band | Strongest r | Lag (s before frame) |")
    md.append("|---|---|---|---|")
    for roi in ROI7:
        i = labels.index(roi)
        for b in ("alpha", "theta", "beta"):
            k = bands.index(b)
            l = int(np.argmax(np.abs(band[k, :, i])))
            md.append(f"| {SHORT[roi]} | {b} | {band[k, l, i]:+.3f} (t = {band_t[k, l, i]:+.1f}) | {LAG_CENTRES[l]:.0f} |")
    md.append("")
    neg = (alpha.min(axis=0) < -0.05).sum()
    pos = (alpha.max(axis=0) > 0.05).sum()
    md.append(f"Alpha power couples negatively (r < −0.05 at some lag) with {neg} of 65 targets and positively (r > 0.05) "
              f"with {pos}; positive: " + ", ".join(labels[i] for i in range(len(labels)) if alpha[:, i].max() > 0.05) + ".\n")
    for theme, c in THEMES.items():
        cmap = LinearSegmentedColormap.from_list("div", [c["low"], c["mid"], c["high"]])
        fig, ax = plt.subplots(figsize=(7.5, 12), facecolor=c["surface"])
        ax.set_facecolor(c["surface"])
        limit = np.percentile(np.abs(alpha), 99)
        image = ax.pcolormesh(-LAG_CENTRES, np.arange(len(order)), alpha[:, order].T, cmap=cmap, vmin=-limit, vmax=limit,
                              shading="nearest")
        ax.set_yticks(np.arange(len(order)), [SHORT.get(labels[i], labels[i]) for i in order], fontsize=6.8, color=c["ink_2"])
        nets = [region_wide.loc[labels[i], "network"] if labels[i] in region_wide.index else "" for i in order]
        for y in range(1, len(nets)):
            if nets[y] != nets[y - 1]:
                ax.axhline(y - 0.5, color=c["surface"], linewidth=2.5)
        starts = {}
        for y, n in enumerate(nets):
            starts.setdefault(n, []).append(y)
        for n, ys in starts.items():
            ax.text(0.4, np.mean(ys), n, fontsize=7.5, color=c["ink_2"], va="center")
        ax.set_xlim(-24, 0)
        ax.set_xlabel("Seconds before the BOLD frame", fontsize=9, color=c["ink_2"])
        ax.tick_params(colors=c["muted"], labelsize=7, length=2)
        for side in ax.spines.values():
            side.set_visible(False)
        bar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.25)
        bar.set_label("Within-scan r, alpha power vs BOLD", fontsize=8.5, color=c["ink_2"])
        bar.ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=8)
        bar.outline.set_visible(False)
        save(fig, out, "alpha_coupling_by_lag", theme, c)

    freqs = np.arange(1, 45) + 0.5
    rois = [str(r) for r in maps["rois"]]
    for theme, c in THEMES.items():
        cmap = LinearSegmentedColormap.from_list("div", [c["low"], c["mid"], c["high"]])
        fig, axes = plt.subplots(2, 7, figsize=(17, 5.8), facecolor=c["surface"], sharex=True, sharey=True)
        for row, (key, title) in enumerate((("coupling", "Model-free: r(feature, BOLD)"),
                                            ("pattern", "Haufe pattern: r(feature, ridge prediction)"))):
            data = maps[key].mean(axis=1)  # (ROI, bins, lags), channel-averaged
            limit = np.percentile(np.abs(data), 99)
            for j, roi in enumerate(rois):
                ax = axes[row, j]
                ax.set_facecolor(c["surface"])
                image = ax.pcolormesh(-LAG_CENTRES, freqs, data[j], cmap=cmap, vmin=-limit, vmax=limit, shading="nearest")
                for edge in (4, 8, 13, 30):
                    ax.axhline(edge, color=c["muted"], linewidth=0.4, alpha=0.6)
                for side in ax.spines.values():
                    side.set_visible(False)
                ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=7.5, length=2)
                if row == 0:
                    ax.set_title(SHORT[roi], fontsize=10, color=c["ink"], loc="left")
            axes[row, 0].set_ylabel(f"{title}\nHz", fontsize=8.5, color=c["ink_2"])
            bar = fig.colorbar(image, ax=axes[row, :].tolist(), fraction=0.012, pad=0.01)
            bar.ax.tick_params(colors=c["muted"], labelcolor=c["ink_2"], labelsize=7.5)
            bar.outline.set_visible(False)
        for ax in axes[1]:
            ax.set_xlabel("s before frame", fontsize=8, color=c["ink_2"])
        save(fig, out, "coupling_vs_pattern", theme, c)


# ---------------------------------------------------------------- attribution
MODEL_ORDER = ["ridge", "NeuroBOLT", "NeuroBOLT (published)"]


def attribution(perm, surr, out, md):
    if surr is not None:
        md.append("## Is NeuroBOLT a linear band-power model in disguise?\n")
        md.append("Held-out scans of the authors' split, mean over 6 scans × 7 ROIs.\n")
        md.append("| NeuroBOLT checkpoints | Linear surrogate vs NeuroBOLT output | Ridge (trained on BOLD) vs NeuroBOLT output | "
                  "NeuroBOLT vs BOLD | Surrogate vs BOLD | Ridge vs BOLD |")
        md.append("|---|---|---|---|---|---|")
        for m, g in surr.groupby("model"):
            md.append(f"| {m} | {g['surrogate_vs_model'].mean():.3f} | {g['ridge_vs_model'].mean():.3f} | "
                      f"{g['model_vs_bold'].mean():.3f} | {g['surrogate_vs_bold'].mean():.3f} | {g['ridge_vs_bold'].mean():.3f} |")
        md.append("")
    if perm is None:
        return
    perm = perm.assign(drop=perm["base_r"] - perm["perturbed_r"])
    agg = perm.groupby(["model", "kind", "part"])[["drop", "shift"]].mean().reset_index()
    agg.to_csv(os.path.join(out, "data", "permutation_summary.csv"), index=False)
    md.append("## Permutation importance (same perturbed EEG for every model)\n")
    md.append("Drop in held-out R when one part of the EEG is swapped with a window ≥ 60 s away; "
              "'moves' is the variance of the prediction change relative to the prediction's variance.\n")
    models = [m for m in MODEL_ORDER if m in set(agg["model"])]
    md.append("| Part | " + " | ".join(f"{m}: ΔR / moves" for m in models) + " |")
    md.append("|---|" + "---|" * len(models))
    for kind in ("band", "region", "segment"):
        parts = list(dict.fromkeys(agg[agg["kind"] == kind]["part"]))
        for p in parts:
            cells = []
            for m in models:
                r = agg[(agg["model"] == m) & (agg["kind"] == kind) & (agg["part"] == p)].iloc[0]
                cells.append(f"{r['drop']:+.3f} / {r['shift']:.2f}")
            md.append(f"| {kind}: {p} | " + " | ".join(cells) + " |")
    md.append("")
    colors = lambda c: {"ridge": c["s2"], "NeuroBOLT": c["s1"], "NeuroBOLT (published)": c["s3"]}  # noqa: E731
    for theme, c in THEMES.items():
        fig, axes = plt.subplots(1, 3, figsize=(14, 3.8), facecolor=c["surface"], gridspec_kw={"width_ratios": [6, 5, 4]})
        for ax, kind, title in zip(axes, ("band", "region", "segment"), ("Frequency band", "Scalp region", "Part of the 16 s window")):
            style(ax, c)
            parts = list(dict.fromkeys(agg[agg["kind"] == kind]["part"]))
            width = 0.8 / len(models)
            for i, m in enumerate(models):
                vals = [agg[(agg["model"] == m) & (agg["kind"] == kind) & (agg["part"] == p)]["drop"].iloc[0] for p in parts]
                ax.bar(np.arange(len(parts)) + (i - (len(models) - 1) / 2) * width, vals, width=width * 0.92,
                       color=colors(c)[m], label=m)
            ax.set_xticks(np.arange(len(parts)), [p.replace(" before", "") for p in parts], fontsize=8, rotation=0)
            ax.axhline(0, color=c["axis"], linewidth=0.8)
            ax.set_title(title, fontsize=10, color=c["ink"], loc="left")
        axes[0].set_ylabel("Drop in held-out R", fontsize=9, color=c["ink_2"])
        axes[0].legend(frameon=False, fontsize=8.5, labelcolor=c["ink_2"])
        fig.tight_layout()
        save(fig, out, "permutation_importance", theme, c)

    import mne
    info = montage_info()
    chan = agg[agg["kind"] == "channel"]
    for theme, c in THEMES.items():
        fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 3.4), facecolor=c["surface"])
        cmap = LinearSegmentedColormap.from_list("seq", [c["mid"], c["s2"]])
        limit = chan["drop"].max()
        for ax, m in zip(np.atleast_1d(axes), models):
            ax.set_facecolor(c["surface"])
            vals = [chan[(chan["model"] == m) & (chan["part"] == ch)]["drop"].iloc[0] for ch in CH_NAMES]
            mne.viz.plot_topomap(vals, info, axes=ax, show=False, cmap=cmap, vlim=(0, limit), contours=0)
            ax.set_title(m, fontsize=10, color=c["ink"])
        save(fig, out, "channel_importance", theme, c)


# ---------------------------------------------------------------- nonlinear
def nonlinear(nl, md, title="5-fold CV"):
    nl = nl.copy()
    nl["person"] = nl["scan"].map(person)
    md.append(f"## Linear versus nonlinear readouts of the same band powers ({title}, 7 ROIs)\n")
    md.append("| Features | Standardisation | Model | Mean R over people | Δ vs ridge, same features (95% CI) | People better |")
    md.append("|---|---|---|---|---|---|")
    for (feat, norm), g in nl.groupby(["features", "norm"]):
        per = g.groupby(["model", "person"])["corr"].mean().unstack("model")
        for model in [m for m in ("ridge", "spline", "interact", "vig_x", "mlp") if m in per]:
            m_all = per[model].mean()
            if model == "ridge":
                md.append(f"| {feat} | {norm} | ridge | {m_all:.3f} | | |")
                continue
            d = per[model] - per["ridge"]
            m, lo, hi = ci(d)
            md.append(f"| {feat} | {norm} | {model} | {m_all:.3f} | {m:+.3f} ({lo:+.3f} to {hi:+.3f}) | {(d > 0).sum()} of {len(d)} |")
    md.append("")


def tsmodel(ts, cv, filters, out, md):
    """Learned-band end-to-end model against ridge on fixed 1 Hz bins, paired by person on the same scans."""
    ridge = cv[(cv["features"] == "eeg_full") & (cv["targets"] == "all65") & cv["roi"].isin(ROI7)].copy()
    ridge["person"] = ridge["scan"].map(person)
    ts = ts.copy()
    ts["person"] = ts["scan"].map(person)
    base = ridge.groupby(["scan", "person"])["corr"].mean().reset_index()
    md.append("## End-to-end model with learned frequency bands (5-fold CV, 7 ROIs)\n")
    md.append("| Model | Folds done | Mean R over people | Δ vs ridge on 1 Hz bins, same scans (95% CI) |")
    md.append("|---|---|---|---|")
    for model, g in ts.groupby("model"):
        per = g.groupby(["scan", "person"])["corr"].mean().reset_index()
        merged = per.merge(base, on=["scan", "person"], suffixes=("", "_ridge"))
        pp = merged.groupby("person")[["corr", "corr_ridge"]].mean()
        m, lo, hi = ci(pp["corr"] - pp["corr_ridge"]) if len(pp) > 2 else (np.nan, np.nan, np.nan)
        md.append(f"| {model} | {g['fold'].nunique()} | {pp['corr'].mean():.3f} | {m:+.3f} ({lo:+.3f} to {hi:+.3f}) |")
    md.append("")
    if filters is None:
        return
    for theme, c in THEMES.items():
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), facecolor=c["surface"], sharey=True)
        for ax, readout in zip(axes, ("full", "cp")):
            style(ax, c)
            f = filters[filters["readout"] == readout].sort_values(["fold", "seed", "low_hz"])
            for y, (_, g) in enumerate(f.groupby(["fold", "seed"])):
                for _, r in g.iterrows():
                    ax.plot([r["low_hz"], r["high_hz"]], [y, y], color=c["s2"], linewidth=3, solid_capstyle="butt")
            for edge in (4, 8, 13, 30):
                ax.axvline(edge, color=c["grid"], linewidth=0.8)
            ax.set_xscale("log")
            ax.set_xticks([1, 2, 4, 8, 13, 20, 30, 45], ["1", "2", "4", "8", "13", "20", "30", "45"])
            ax.set_xlabel("Hz (learned pass-bands; one row per fold and seed)", fontsize=9, color=c["ink_2"])
            ax.set_title("Full linear readout" if readout == "full" else "Rank-2 readout", fontsize=10, color=c["ink"],
                         loc="left")
            ax.set_yticks([])
        save(fig, out, "learned_bands", theme, c)


def personal(pers, phys, md):
    pers = pers.copy()
    pers["person"] = pers["scan"].map(person)
    md.append("## Personalisation: the first half of each held-out scan as calibration (second half scored, 7 ROIs)\n")
    md.append("| Prediction | Mean R over people | Δ vs population model (95% CI) | People better |")
    md.append("|---|---|---|---|")
    per = pers.groupby("person")[["population", "lag_adapted", "own_only", "stacked"]].mean()
    labels = {"population": "Population model (other people only)", "lag_adapted": "Population, person-specific delay (±6 s)",
              "own_only": "Person's own 60 band powers only", "stacked": "Population + own band powers"}
    for key, label in labels.items():
        if key == "population":
            md.append(f"| {label} | {per[key].mean():.3f} | | |")
            continue
        m, lo, hi = ci(per[key] - per["population"])
        md.append(f"| {label} | {per[key].mean():.3f} | {m:+.3f} ({lo:+.3f} to {hi:+.3f}) | "
                  f"{int((per[key] > per['population']).sum())} of {len(per)} |")
    shifts = pers["chosen_shift_frames"].value_counts().sort_index()
    md.append("\nChosen delay shifts (frames of 2.1 s, positive = prediction delayed): "
              + ", ".join(f"{int(k):+d}: {v}" for k, v in shifts.items()) + "\n")
    if phys is not None:
        md.append("| Scan property (29 scans) | Spearman ρ with population R | p |")
        md.append("|---|---|---|")
        for key, label in (("hr_sd", "Heart-rate fluctuation (SD)"), ("eog_slow_sd", "Slow-EOG power fluctuation (SD)"),
                           ("hr_mean", "Mean heart rate")):
            ok = np.isfinite(phys[key]) & (phys[key] > 0)
            rho, p = stats.spearmanr(phys.loc[ok, key], phys.loc[ok, "population_r"])
            md.append(f"| {label} | {rho:+.2f} | {p:.3f} |")
        md.append("")


def hammerstein(ham, cv, comps, out, md):
    ham = ham.copy()
    ham["person"] = ham["scan"].map(person)
    ridge = cv[(cv["features"] == "eeg_full") & (cv["targets"] == "all65")].copy()
    ridge["person"] = ridge["scan"].map(person)
    md.append("## Shared-factor Hammerstein distributed-lag model (5-fold CV)\n")
    md.append("| Variant | Parameters (65 targets) | R, 65 targets | Δ vs full ridge, 65 targets (95% CI) | R, 7 ROIs | Δ vs ridge, 7 ROIs |")
    md.append("|---|---|---|---|---|---|")
    for variant in sorted(ham["variant"].unique(), key=lambda v: (v.startswith("spline"), int(re.search(r"\d+", v).group()))):
        g = ham[ham["variant"] == variant]
        k = int(re.search(r"\d+", variant).group())
        n_par = k * (26 + 44) + 65 * k * 5 + 65 + (4 * k if variant.startswith("spline") else 0)
        cells = []
        for rois in (None, ROI7):
            a = g if rois is None else g[g["roi"].isin(rois)]
            b = ridge if rois is None else ridge[ridge["roi"].isin(rois)]
            pa = a.groupby(["scan", "person"])["corr"].mean().groupby("person").mean()
            pb = b[b["scan"].isin(a["scan"].unique())].groupby(["scan", "person"])["corr"].mean().groupby("person").mean()
            m, lo, hi = ci(pa - pb)
            cells.append((pa.mean(), m, lo, hi))
        md.append(f"| {variant} | {n_par:,} | {cells[0][0]:.3f} | {cells[0][1]:+.3f} ({cells[0][2]:+.3f} to {cells[0][3]:+.3f}) | "
                  f"{cells[1][0]:.3f} | {cells[1][1]:+.3f} ({cells[1][2]:+.3f} to {cells[1][3]:+.3f}) |")
    md.append("")
    if comps is None:
        return
    labels = [str(l) for l in comps["labels"]]
    variant = "linear3" if "linear3_a" in comps.files else sorted(f[:-2] for f in comps.files if f.endswith("_a"))[0]
    a, b, h = comps[f"{variant}_a"], comps[f"{variant}_b"], comps[f"{variant}_h"]
    # orient each component so its channel pattern sums positive; the spectrum and kernels carry the sign
    for k in range(len(a)):
        if a[k].sum() < 0:
            a[k], b[k] = -a[k], -b[k]
    import mne
    info = montage_info()
    freqs = np.arange(1, 45) + 0.5
    for theme, c in THEMES.items():
        fig, axes = plt.subplots(3, len(a), figsize=(4.2 * len(a), 10), facecolor=c["surface"],
                                 gridspec_kw={"height_ratios": [1, 0.8, 1]})
        cmap = LinearSegmentedColormap.from_list("div", [c["low"], c["mid"], c["high"]])
        for k in range(len(a)):
            ax = axes[0, k]
            ax.set_facecolor(c["surface"])
            lim = np.abs(a[k]).max()
            mne.viz.plot_topomap(a[k], info, axes=ax, show=False, cmap=cmap, vlim=(-lim, lim), contours=0)
            ax.set_title(f"Component {k + 1}: topography", fontsize=10, color=c["ink"])
            ax = axes[1, k]
            style(ax, c)
            ax.plot(freqs, b[k], color=c["s2"], linewidth=2)
            ax.axhline(0, color=c["axis"], linewidth=0.8)
            for edge in (4, 8, 13, 30):
                ax.axvline(edge, color=c["grid"], linewidth=0.8)
            ax.set_xlabel("Hz", fontsize=8.5, color=c["ink_2"])
            ax.set_title("spectrum", fontsize=10, color=c["ink"], loc="left")
            ax = axes[2, k]
            style(ax, c)
            for roi, color in zip(("Thalamus", "Cuneus", "Heschl’s gyrus", "global signal clean"),
                                  (c["s1"], c["s2"], c["s3"], c["muted"])):
                ax.plot(-LAG_CENTRES, h[labels.index(roi), k], color=color, linewidth=2, label=SHORT[roi])
            ax.axhline(0, color=c["axis"], linewidth=0.8)
            ax.set_xlabel("s before frame", fontsize=8.5, color=c["ink_2"])
            ax.set_title("regional lag kernels", fontsize=10, color=c["ink"], loc="left")
        axes[2, 0].legend(frameon=False, fontsize=8.5, labelcolor=c["ink_2"])
        fig.tight_layout()
        save(fig, out, "hammerstein_components", theme, c)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="reports/interpretability/data")
    parser.add_argument("--out", default="reports/interpretability")
    args = parser.parse_args()
    path = lambda name: os.path.join(args.data, name)  # noqa: E731
    have = lambda name: os.path.isfile(path(name))  # noqa: E731
    md = ["# Interpretability tables\n", "Generated by scripts/interp_report.py.\n"]
    labels_csv = pd.read_csv(path("labels_64_dictionary.csv"))
    pred_file = path("raw/predictions_eeg_full.npz") if have("raw/predictions_eeg_full.npz") else None
    region_wide, cv = None, None
    if have("cv_scores.csv"):
        cv = pd.read_csv(path("cv_scores.csv"))
        feature_table(cv, md)
        if pred_file:
            null_analysis(pred_file, args.out, md)
        if "eeg_full" in set(cv["features"]):
            region_wide = whole_brain(cv, labels_csv, pred_file, path("maps.nii.gz") if have("maps.nii.gz") else None,
                                      args.out, md)
        physio_partition(cv, args.out, md)
    if have("maps.npz") and region_wide is not None:
        maps = np.load(path("maps.npz"))
        lookup = region_wide["all65"].to_dict()
        hrf_figure(maps, lookup, args.out, md)
        coupling_figures(maps, region_wide, args.out, md)
    perm = pd.read_csv(path("attribution_permutation.csv")) if have("attribution_permutation.csv") else None
    surr = pd.read_csv(path("attribution_surrogate.csv")) if have("attribution_surrogate.csv") else None
    if perm is not None or surr is not None:
        attribution(perm, surr, args.out, md)
    if have("nonlinear_scores.csv"):
        nonlinear(pd.read_csv(path("nonlinear_scores.csv")), md)
    if have("nonlinear_loso_scores.csv"):
        nonlinear(pd.read_csv(path("nonlinear_loso_scores.csv")), md, "leave one person out, as in MEL")
    if have("tsmodel_scores.csv") and cv is not None:
        tsmodel(pd.read_csv(path("tsmodel_scores.csv")), cv,
                pd.read_csv(path("tsmodel_filters.csv")) if have("tsmodel_filters.csv") else None, args.out, md)
    if have("personal.csv"):
        personal(pd.read_csv(path("personal.csv")),
                 pd.read_csv(path("scan_physiology.csv")) if have("scan_physiology.csv") else None, md)
    if have("hammerstein_scores.csv") and cv is not None:
        smooth = have("hammerstein_smooth_components.npz")
        hammerstein(pd.read_csv(path("hammerstein_scores.csv")), cv,
                    None if smooth or not have("hammerstein_components.npz") else np.load(path("hammerstein_components.npz")),
                    args.out, md)
        if have("hammerstein_smooth_scores.csv"):
            md.append("Same model with a smoothness penalty on the spectral profiles (used for the component figure):\n")
            hammerstein(pd.read_csv(path("hammerstein_smooth_scores.csv")), cv,
                        np.load(path("hammerstein_smooth_components.npz")) if smooth else None, args.out, md)
    with open(os.path.join(args.out, "tables.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
