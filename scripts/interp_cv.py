#!/usr/bin/env python3
"""What does cross-subject EEG-to-BOLD ridge actually use? Feature-set and target-set comparisons, 5-fold CV.

Every model is ridge (penalty chosen per target on each fold's validation people) scored on the
fold's held-out people, so each of the 29 scans is held out once. Feature sets, all built from the
cached 24 s / 12-lag windows:
  eeg_full     log power, 26 channels x 44 one-Hz bins x 12 lags (the best ridge model)
  bands60      channel-averaged power in five classic bands x 12 lags
  vigilance    alpha / (delta + theta) power ratio x 12 lags
  regional300  five bands x five scalp regions x 12 lags
  hrf_canon    eeg_full collapsed over lags with the canonical HRF (one weight per channel x bin)
  hrf_3basis   the same with the HRF's temporal and dispersion derivatives (3 x 1,144 features)
  eog, emg, ecg_hr, physio   power of the non-EEG channels (and heart rate) x 12 lags
  eeg+physio   EEG and physiology together, with a separate penalty scale for each block
  time         smooth functions of the frame's position in the scan (a drift control)
  cwl, eeg_cwlsub, eeg+cwl   on the 19 scans recorded with carbon-wire motion loops only
Targets: all 64 DiFuMo regions plus the global signal (all65), and the 64 regions after
regressing out each scan's global signal (gsr64).

    python scripts/interp_cv.py --eeg-cache features_fine_w24_sub12.npz --interp-cache interp_cache.npz \
        --split-sheet scan_split_cv5.xlsx --out $M3_OUT/interp/cv

Writes scores.csv (one row per feature set x target x held-out scan) and predictions_<set>.npz.
"""
import argparse
import csv
import os
import sys

import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp
from scipy.stats import gamma

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS  # noqa: E402
from eval_inter_per_scan import CH_NAMES  # noqa: E402

FREQS = np.arange(1, 45) + 0.5
N_CH, N_BINS, N_LAGS, LAG_SEC = 26, 44, 12, 2.0
BANDS = {"delta": (1, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "gamma": (30, 45)}
REGIONS = {"frontal": ["FP1", "FP2", "FPZ", "F3", "F4", "F7", "F8", "FZ"], "central": ["C3", "C4", "CZ"],
           "temporal": ["T7", "T8", "FT9", "FT10", "TP9", "TP10"], "parietal": ["P3", "P4", "P7", "P8", "PZ"],
           "occipital": ["O1", "O2", "OZ", "POZ"]}
# seconds before the frame at the centre of each lag bin, oldest first (bin 0 covers 24-22 s)
LAG_CENTRES = 24 - LAG_SEC * np.arange(N_LAGS) - LAG_SEC / 2
BLOCK_SCALES = (0.25, 0.5, 1.0, 2.0, 4.0)


def spm_hrf(t, peak=6.0, under=16.0, disp=1.0):
    """SPM's canonical double-gamma HRF at delays t (s), unnormalized."""
    return gamma.pdf(t, peak / disp, scale=disp) - gamma.pdf(t, under / disp, scale=disp) / 6.0


def hrf_kernels():
    canon = spm_hrf(LAG_CENTRES)
    temporal = canon - spm_hrf(LAG_CENTRES - 1.0)
    dispersion = (canon - spm_hrf(LAG_CENTRES, disp=1.01)) / 0.01
    return np.stack([k / np.abs(k).max() for k in (canon, temporal, dispersion)])


def as_cube(x):
    return x.reshape(len(x), N_CH, N_BINS, N_LAGS)


def band_power(cube, lo, hi, channels=None):
    """(windows, lags) log of total power in [lo, hi) Hz, averaged over the given channels."""
    sel = cube[:, :, (FREQS >= lo) & (FREQS < hi), :]
    total = logsumexp(sel, axis=2)
    return total.mean(axis=1) if channels is None else total[:, channels].mean(axis=1)


def time_basis(frames, n_basis=8, length=576):
    centres = np.linspace(0, length, n_basis)
    width = length / (n_basis - 1)
    return np.exp(-0.5 * ((frames[:, None] - centres[None]) / width) ** 2).astype(np.float32)


def build_features(x, extra):
    """{name: array or list of blocks} for one scan."""
    cube = as_cube(x)
    region_idx = {name: [CH_NAMES.index(c) for c in chans] for name, chans in REGIONS.items()}
    kernels = hrf_kernels()
    bands = np.concatenate([band_power(cube, lo, hi) for lo, hi in BANDS.values()], axis=1)
    feats = {
        "eeg_full": x,
        "bands60": bands,
        "vigilance": band_power(cube, 8, 13) - band_power(cube, 1, 8),
        "regional300": np.concatenate([band_power(cube, lo, hi, idx) for lo, hi in BANDS.values()
                                       for idx in region_idx.values()], axis=1),
        "hrf_canon": np.einsum("ncfl,l->ncf", cube, kernels[0]).reshape(len(x), -1),
        "hrf_3basis": np.einsum("ncfl,kl->nkcf", cube, kernels).reshape(len(x), -1),
        "eog": extra["eog"], "emg": extra["emg"],
        "ecg_hr": np.concatenate([extra["ecg"], extra["hr"]], axis=1),
        "time": time_basis(extra["frame"]),
    }
    feats["physio"] = np.concatenate([feats["eog"], feats["emg"], feats["ecg_hr"]], axis=1)
    # The EOG, EMG and ECG leads share the EEG reference, so their power in EEG bands partly is EEG.
    # These subsets keep what EEG amplitude cannot explain: heart timing, slow eye movements and
    # blinks (EOG below 4 Hz), and muscle (EMG above 30 Hz). Bands: 0.5-1, 1-4, 4-8, 8-13, 13-30, 30-45, 45-95 Hz.
    n = len(x)
    feats["hr"] = extra["hr"]
    feats["eog_slow"] = extra["eog"].reshape(n, 2, 7, 12)[:, :, :2].reshape(n, -1)
    feats["emg_high"] = extra["emg"].reshape(n, 3, 7, 12)[:, :, 5:].reshape(n, -1)
    feats["phys_specific"] = np.concatenate([feats["hr"], feats["eog_slow"], feats["emg_high"]], axis=1)
    if "cwl" in extra:
        feats["cwl"] = extra["cwl"]
    return {k: v.astype(np.float32) for k, v in feats.items()}


# feature set name -> (blocks, scans restricted to CWL recordings)
SETS = {
    "eeg_full": (["eeg_full"], False), "bands60": (["bands60"], False), "vigilance": (["vigilance"], False),
    "regional300": (["regional300"], False), "hrf_canon": (["hrf_canon"], False),
    "hrf_3basis": (["hrf_3basis"], False), "eog": (["eog"], False), "emg": (["emg"], False),
    "ecg_hr": (["ecg_hr"], False), "physio": (["physio"], False), "time": (["time"], False),
    "eeg+physio": (["eeg_full", "physio"], False), "eeg+time": (["eeg_full", "time"], False),
    "bands60+physio": (["bands60", "physio"], False),
    "hr": (["hr"], False), "eog_slow": (["eog_slow"], False), "emg_high": (["emg_high"], False),
    "phys_specific": (["phys_specific"], False), "eeg+phys_specific": (["eeg_full", "phys_specific"], False),
    "eeg+hr": (["eeg_full", "hr"], False),
    "phys_specific_cwlsub": (["phys_specific"], True), "phys_specific+cwl": (["phys_specific", "cwl"], True),
    "eeg+phys_specific+cwl": (["eeg_full", "phys_specific", "cwl"], True),
    "cwl": (["cwl"], True), "eeg_cwlsub": (["eeg_full"], True), "eeg+cwl": (["eeg_full", "cwl"], True),
    "physio_cwlsub": (["physio"], True), "physio+cwl": (["physio", "cwl"], True),
}


def ridge_path_multi(x_train, y_train, x_eval, alphas):
    """{alpha: [predictions per eval array]} for multi-target ridge with intercept (as baseline_ridge.ridge_path)."""
    as_t = lambda a: torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32))  # noqa: E731
    x, y = as_t(x_train), as_t(y_train)
    x_mean, y_mean = x.mean(dim=0), y.mean(dim=0)
    if x.shape[1] > x.shape[0]:
        u, s, vt = torch.linalg.svd(x - x_mean, full_matrices=False)
    else:  # tall: eigendecomposition of the Gram matrix is much cheaper
        evals, v = torch.linalg.eigh((x - x_mean).T @ (x - x_mean))
        s = evals.clamp(min=0).sqrt()
        keep = s > 1e-6 * s.max()
        s, vt = s[keep], v[:, keep].T
        u = (x - x_mean) @ vt.T / s
    uty = u.T @ (y - y_mean)
    rotated = [(as_t(e) - x_mean) @ vt.T for e in x_eval]
    return {a: [(r @ ((s / (s ** 2 + a))[:, None] * uty) + y_mean).numpy() for r in rotated] for a in alphas}


def gsr(y_all, labels):
    """Each region's time series with the scan's global signal regressed out (64 regions)."""
    g = y_all[:, labels.index("global signal clean")]
    design = np.stack([np.ones_like(g), g], axis=1)
    regions = [i for i, lab in enumerate(labels) if lab != "global signal clean"]
    beta, *_ = np.linalg.lstsq(design, y_all[:, regions], rcond=None)
    return (y_all[:, regions] - design @ beta).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg-cache", required=True)
    parser.add_argument("--interp-cache", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--sets", nargs="*", default=list(SETS))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))
    os.makedirs(args.out, exist_ok=True)

    eeg = np.load(args.eeg_cache)
    aux = np.load(args.interp_cache)
    labels = [str(s) for s in aux["labels"]]
    region_labels = [lab for lab in labels if lab != "global signal clean"]
    scans = [str(s) for s in aux["scans"]]
    feats, targets = {}, {}
    for scan in scans:
        extra = {k: aux[f"{k}_{scan}"] for k in ("eog", "emg", "ecg", "hr", "frame", "cwl") if f"{k}_{scan}" in aux}
        if not np.isfinite(aux[f"median_hr_{scan}"]):  # no usable R peaks (sub17-scan02): a neutral constant
            extra["hr"] = np.full_like(extra["hr"], 65.0)
        feats[scan] = build_features(eeg[f"x_{scan}"], extra)
        y_all = aux[f"y_all_{scan}"]
        targets[scan] = np.concatenate([y_all, gsr(y_all, labels)], axis=1)
    target_names = [("all65", lab) for lab in labels] + [("gsr64", lab) for lab in region_labels]
    print(f"{len(scans)} scans, {len(target_names)} targets; feature sizes: "
          + ", ".join(f"{k}={v.shape[1]}" for k, v in feats[scans[0]].items()), flush=True)

    rows = []
    for set_name in args.sets:
        blocks, cwl_only = SETS[set_name]
        preds = {}
        for k in range(1, args.folds + 1):
            sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
            split = {name: [s for s in sheet.loc[sheet[name] == 1, "scan_name"]
                            if not cwl_only or "cwl" in feats[s]] for name in ("train", "val", "test")}
            if not split["test"]:
                continue
            if len(split["val"]) < 2:  # too few motion-loop scans among the fold's validation people
                person = lambda scan: scan.split("-")[0]  # noqa: E731
                movers = sorted({person(s) for s in split["train"]})[-2:]
                split["val"] += [s for s in split["train"] if person(s) in movers]
                split["train"] = [s for s in split["train"] if person(s) not in movers]
            stacked = {}
            for name, group in split.items():
                stacked[name] = [np.concatenate([feats[s][b] for s in group]) for b in blocks]
            means = [b.mean(axis=0) for b in stacked["train"]]
            stds = [b.std(axis=0) + 1e-8 for b in stacked["train"]]
            y = {name: np.concatenate([targets[s] for s in group]) for name, group in split.items()}
            scales = [(1.0,)] + [BLOCK_SCALES] * (len(blocks) - 1)
            best_val = np.full(y["val"].shape[1], np.inf)
            best_test = np.zeros_like(y["test"])
            best_choice = [None] * y["val"].shape[1]
            for combo in np.array(np.meshgrid(*scales)).T.reshape(-1, len(blocks)):
                z = {name: np.concatenate([(b - m) / sd * w for b, m, sd, w in zip(parts, means, stds, combo)], axis=1)
                     for name, parts in stacked.items()}
                path = ridge_path_multi(z["train"], y["train"], [z["val"], z["test"]], ALPHAS)
                for alpha, (pv, pt) in path.items():
                    mse = ((pv - y["val"]) ** 2).mean(axis=0)
                    better = mse < best_val
                    best_val[better] = mse[better]
                    best_test[:, better] = pt[:, better]
                    for j in np.flatnonzero(better):
                        best_choice[j] = f"alpha={alpha:g} scales={'/'.join(f'{w:g}' for w in combo)}"
            start = 0
            for scan in split["test"]:
                n = len(targets[scan])
                p = best_test[start:start + n]
                preds[scan] = p
                start += n
                for j, (tset, lab) in enumerate(target_names):
                    rows.append({"features": set_name, "targets": tset, "roi": lab, "fold": k, "scan": scan,
                                 "corr": float(np.corrcoef(p[:, j], targets[scan][:, j])[0, 1]),
                                 "chosen": best_choice[j]})
            print(f"{set_name} fold{k}: {len(split['train'])} train scans, {len(split['test'])} test", flush=True)
        np.savez_compressed(os.path.join(args.out, f"predictions_{set_name}.npz"),
                            targets=np.array([f"{t}|{lab}" for t, lab in target_names]),
                            **{f"pred_{s}": p for s, p in preds.items()},
                            **{f"true_{s}": targets[s] for s in preds})
        mine = [r for r in rows if r["features"] == set_name and r["targets"] == "all65"]
        print(f"  {set_name}: mean R over all65 targets {np.mean([r['corr'] for r in mine]):.3f}", flush=True)
        with open(os.path.join(args.out, "scores.csv"), "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
