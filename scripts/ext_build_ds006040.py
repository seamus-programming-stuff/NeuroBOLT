#!/usr/bin/env python3
"""Turn ds006040's resting runs into the VU feature and target format, for external validation.

ds006040 (Cha et al., Sci Data 2026; OpenNeuro, CC0): 28 people, simultaneous EEG-fMRI at 3T, TR 2 s,
eyes-closed (EC) and eyes-open (EO) rest with the scanner on, about 6.3 min each. EEG: 64-channel
BrainCap MR at 5 kHz, gradient and BCG artefacts removed by the authors (desc-anc0qrsrm). fMRI:
fMRIPrep 23.0.1 output in MNI152NLin2009cAsym, 3.5 mm.

Per run, built to match the VU pipeline exactly where the data allow:
  EEG   the 26 VU channels, resampled to 200 Hz, 0.5 Hz high-pass, 24 s windows ending at each
        fMRI volume's "TR" marker, mean-removed per window, log power in 44 one-Hz bins x 12 two-second
        lags (baseline_ridge.band_power_features), in microvolts
  BOLD  DiFuMo-64 region time series (nilearn NiftiMapsMasker) and the brain-mask mean (global signal),
        after regressing 24 motion parameters (6 + derivatives + squares) and a linear trend;
        then the VU target steps: 0.15 Hz low-pass and demeaned 95th-percentile scaling
Targets are written in the VU label order (64 regions + 'global signal clean').

    python scripts/ext_build_ds006040.py --root $M3_SCRATCH/ext/ds006040 --atlas maps.nii.gz \
        --labels labels_64_dictionary.csv --vu-labels-from $M3_OUT/interp/interp_cache.npz --out ds006040_cache.npz
"""
import argparse
import glob
import os
import re
import sys

import mne
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataset_maker import preproc  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import BAND_SETS, band_power_features  # noqa: E402
from eval_inter_per_scan import CH_NAMES  # noqa: E402

TR, FS, WINDOW_SEC, N_LAGS = 2.0, 200, 24, 12
RENAME = {"Fp1": "FP1", "Fp2": "FP2", "Fpz": "FPZ", "Fz": "FZ", "Cz": "CZ", "Pz": "PZ", "POz": "POZ", "Oz": "OZ"}
MOTION = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]


def eeg_features(set_path):
    raw = mne.io.read_raw_eeglab(set_path, preload=True, verbose=False)
    raw.rename_channels({k: v for k, v in RENAME.items() if k in raw.ch_names})
    missing = [c for c in CH_NAMES if c not in raw.ch_names]
    if missing:
        raise ValueError(f"{set_path}: missing channels {missing}")
    raw.pick(CH_NAMES)
    # Some runs have stretches of missing EEG (NaN on every channel, e.g. the first ~30 s of sub-007 EC,
    # where the authors' artefact correction did not run). Zero-fill them so filtering does not spread
    # NaN through the run, and drop every frame whose window (plus a 5 s filter margin) touches a gap.
    data = raw.get_data()
    gap = ~np.isfinite(data).all(axis=0)
    gap_times = raw.times[gap]
    if gap.any():
        raw._data[:, gap] = 0.0
    raw.resample(FS, verbose=False)
    raw.filter(l_freq=0.5, h_freq=None, verbose=False)
    events, event_id = mne.events_from_annotations(raw, verbose=False)
    volumes = mne.pick_events(events, include=event_id["TR"])
    epochs = mne.Epochs(raw, volumes, tmin=-WINDOW_SEC, tmax=0, baseline=(None, None), preload=True, verbose=False)
    data = epochs.get_data(units="uV")[:, :, :WINDOW_SEC * FS].astype(np.float32)
    feats = band_power_features(data, BAND_SETS["fine"], N_LAGS)
    selection = epochs.selection
    if gap.any():
        onsets = (volumes[selection, 0] - raw.first_samp) / FS
        ok = np.array([not ((gap_times > t - WINDOW_SEC - 5) & (gap_times < t + 5)).any() for t in onsets])
        print(f"  {os.path.basename(set_path)}: {gap.mean():.1%} of samples missing; dropping {int((~ok).sum())} frames",
              flush=True)
        feats, selection = feats[ok], selection[ok]
    return feats, selection, len(volumes)


def bold_targets(bold_path, mask_path, confounds_path, maps_img, labels, vu_labels):
    from nilearn.maskers import NiftiMapsMasker, NiftiMasker
    conf = pd.read_csv(confounds_path, sep="\t")
    cols = [c for c in conf.columns if any(c == m or c.startswith(m + "_") for m in MOTION)]
    regressors = conf[cols].fillna(0.0).to_numpy()
    regions = NiftiMapsMasker(maps_img, mask_img=mask_path, detrend=True, standardize=False, t_r=TR,
                              resampling_target="data").fit_transform(bold_path, confounds=regressors)
    voxels = NiftiMasker(mask_img=mask_path, detrend=True, standardize=False, t_r=TR).fit_transform(
        bold_path, confounds=regressors)
    series = pd.DataFrame(regions, columns=labels)
    series["global signal clean"] = voxels.mean(axis=1)
    y = series[vu_labels].to_numpy().T  # (targets, volumes)
    b, a = butter(N=5, Wn=0.15 / (0.5 / TR), btype="low", analog=False)
    y = filtfilt(b, a, y, axis=1)
    y, _ = preproc.normalize_data(y)
    fd = conf["framewise_displacement"].fillna(0.0).to_numpy()
    gs_raw = conf["global_signal"].to_numpy()
    return y.T.astype(np.float32), fd.astype(np.float32), gs_raw.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True)
    parser.add_argument("--atlas", required=True, help="DiFuMo-64 2 mm maps.nii.gz")
    parser.add_argument("--labels", required=True, help="DiFuMo labels_64_dictionary.csv")
    parser.add_argument("--vu-labels-from", required=True, help="interp_cache.npz, for the VU target order")
    parser.add_argument("--subjects", nargs="*")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    mne.set_log_level("ERROR")

    labels = pd.read_csv(args.labels)["Difumo_names"].tolist()
    vu_labels = [str(s) for s in np.load(args.vu_labels_from)["labels"]]
    import nibabel as nib
    maps_img = nib.load(args.atlas)
    subjects = args.subjects or sorted(os.path.basename(p) for p in glob.glob(os.path.join(args.root, "derivatives", "sub-*")))
    arrays, rows = {}, []
    for sub in subjects:
        for cond in ("EC", "EO"):
            eeg = glob.glob(os.path.join(args.root, "derivatives", sub, "eeg", f"{sub}_task-{cond}ON_run-1_desc-anc0qrsrm_eeg.set"))
            func = os.path.join(args.root, "derivatives", sub, "func", f"{sub}_task-{cond}_run-1_")
            bold = func + "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            if not eeg or not os.path.isfile(bold):
                print(f"{sub} {cond}: missing files, skipped", flush=True)
                continue
            try:
                x, selection, n_markers = eeg_features(eeg[0])
                y, fd, gs_raw = bold_targets(bold, func + "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
                                             func + "desc-confounds_timeseries.tsv", maps_img, labels, vu_labels)
            except Exception as error:  # one bad run should not stop the batch
                print(f"{sub} {cond}: FAILED {error}", flush=True)
                continue
            n_vol = len(y)
            if n_markers != n_vol:
                print(f"{sub} {cond}: {n_markers} TR markers vs {n_vol} volumes; using the first {min(n_markers, n_vol)}",
                      flush=True)
            keep = selection < n_vol
            key = f"{sub}_{cond}"
            arrays[f"x_{key}"] = x[keep]
            arrays[f"y_{key}"] = y[selection[keep]]
            arrays[f"frame_{key}"] = selection[keep].astype(np.int32)
            arrays[f"fd_{key}"] = fd[selection[keep]]
            arrays[f"gsraw_{key}"] = gs_raw[selection[keep]]  # fMRIPrep global signal in raw BOLD units
            rows.append({"run": key, "subject": sub, "condition": cond, "frames": int(keep.sum()),
                         "volumes": n_vol, "markers": n_markers, "mean_fd": float(fd.mean())})
            print(f"{key}: {int(keep.sum())} frames of {n_vol} volumes, mean FD {fd.mean():.3f} mm", flush=True)
    np.savez(args.out, labels=np.array(vu_labels), runs=np.array([r["run"] for r in rows]), **arrays)
    pd.DataFrame(rows).to_csv(os.path.splitext(args.out)[0] + "_runs.csv", index=False)
    print(f"Wrote {args.out}: {len(rows)} runs")


if __name__ == "__main__":
    main()
