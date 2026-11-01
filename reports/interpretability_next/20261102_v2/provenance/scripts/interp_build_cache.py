#!/usr/bin/env python3
"""Whole-brain targets and physiological-channel features for the interpretability analyses.

Extends the cached EEG features of ridge_learning_curve.py (log power, 1 Hz bins x 26 channels x
12 lag bins over 24 s) with, for every scan and the same fMRI frames:
  y_all     all 64 DiFuMo regions plus the cleaned global signal (65 targets), preprocessed like
            the seven-ROI targets (0.15 Hz low-pass, demeaned 95th-percentile scaling)
  eog/emg/ecg/cwl  log power of the recording's non-EEG channels in 7 bands x 12 lag bins. EOG
            tracks eye movements and blinks, EMG muscle, ECG the heart, and the four carbon-wire
            loops (19 of 29 scans) head motion inside the scanner.
  hr        heart rate (beats/min) averaged in each 2 s lag bin, from ECG R peaks
  frame     the frame's index in the scan, for a time-in-scan control
The EEG features themselves are not duplicated; the frames are checked against the cache instead.

    python scripts/interp_build_cache.py --dataset-root $M3_DATA --eeg-cache features_fine_w24_sub12.npz \
        --out interp_cache.npz
"""
import argparse
import os
import re
import sys

import mne
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, welch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataset_maker import preproc  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_inter_per_scan import ROIS, TR  # noqa: E402

GROUPS = {"eog": ["EOG1", "EOG2"], "emg": ["EMG1", "EMG2", "EMG3"], "ecg": ["ECG"],
          "cwl": ["CWL1", "CWL2", "CWL3", "CWL4"]}
NUIS_BANDS = [(0.5, 1), (1, 4), (4, 8), (8, 13), (13, 30), (30, 45), (45, 95)]
FS, WINDOW_SEC, N_LAGS = 200, 24, 12


def heart_rate(ecg, fs):
    """Instantaneous heart rate (bpm) at every sample, from R peaks; NaN where it is implausible."""
    events, _, _ = mne.preprocessing.find_ecg_events(
        mne.io.RawArray(ecg[None], mne.create_info(["ECG"], fs, "ecg"), verbose=False),
        ch_name="ECG", l_freq=5, h_freq=35, verbose=False)
    peaks = events[:, 0]
    rate = 60.0 * fs / np.diff(peaks)
    keep = (rate > 35) & (rate < 140)
    times = (peaks[1:] + peaks[:-1]) / 2
    if keep.sum() < 10:
        return np.full(len(ecg), np.nan), float("nan")
    hr = np.interp(np.arange(len(ecg)), times[keep], rate[keep])
    return hr, float(np.median(rate[keep]))


def log_band_power(epochs, bands, n_lags, fs=FS):
    """(windows, channels, samples) -> (windows, channels * bands * lags), as band_power_features."""
    n, channels, samples = epochs.shape
    pieces = epochs.reshape(n, channels, n_lags, samples // n_lags)
    freqs, psd = welch(pieces, fs=fs, nperseg=samples // n_lags, axis=-1)
    power = np.stack([psd[..., (freqs >= lo) & (freqs < hi)].mean(axis=-1) for lo, hi in bands], axis=2)
    return np.log(power + 1e-12).reshape(n, -1).astype(np.float32)


def build_scan(scan_name, root):
    sub, scan = (int(x) for x in re.findall(r"\d+", scan_name))
    stem = f"sub{sub:02d}-scan{scan:02d}"
    raw = mne.io.read_raw_eeglab(os.path.join(root, "EEG", f"{stem}_eeg.set"), preload=True, verbose=False)
    if raw.info["sfreq"] != FS:
        raw.resample(FS, verbose=False)
    nuisance = [c for group in GROUPS.values() for c in group if c in raw.ch_names]
    eeg_raw = raw.copy().drop_channels(nuisance)
    eeg_raw.filter(l_freq=0.5, h_freq=None, verbose=False)  # as load_scan, so the frames match

    fmri = pd.read_pickle(os.path.join(root, "fMRI_difumo", f"{stem}_difumo64_roi.pkl"))
    labels = [c for c in fmri.columns if c != "global signal raw"]
    b, a = butter(N=5, Wn=0.15 / (0.5 / TR), btype="low", analog=False)
    targets = filtfilt(b, a, fmri[labels].to_numpy().T, axis=1)
    targets, _ = preproc.normalize_data(targets)
    # Frame index rides along as an extra target row, so the epoching picks the same frames.
    with_index = np.vstack([targets, np.arange(targets.shape[1])[None]])

    data, eeg_epochs = preproc.epoching_seq2one(eeg_raw, with_index, -WINDOW_SEC, 0, "R149", ifnorm=0,
                                                crop=WINDOW_SEC * FS)
    fmri_rows = np.stack(data["fmri"])
    out = {"y_all": fmri_rows[:, :-1].astype(np.float32), "frame": fmri_rows[:, -1].astype(np.int32)}

    # Non-EEG channels: same events and windows, no high-pass (slow eye movements live below 0.5 Hz).
    nuis_raw = raw.copy().pick(nuisance)
    ecg = raw.get_data(picks=["ECG"])[0] * 1e6
    hr, median_rate = heart_rate(ecg, FS)
    hr_raw = mne.io.RawArray(np.nan_to_num(hr, nan=np.nanmedian(hr) if np.isfinite(hr).any() else 0)[None],
                             mne.create_info(["HR"], FS, "misc"), verbose=False)
    nuis_raw.add_channels([hr_raw], force_update_info=True)
    events, event_id = mne.events_from_annotations(raw, verbose=False)
    events = mne.pick_events(events, include=event_id["R149"])
    epochs = mne.Epochs(nuis_raw, events, tmin=-WINDOW_SEC, tmax=0, baseline=None, preload=True,
                        picks="all", verbose=False)
    if not np.array_equal(epochs.selection, eeg_epochs.selection):
        raise RuntimeError(f"{scan_name}: nuisance and EEG epochs cover different frames")
    arr = epochs.get_data(picks="all")[:, :, :WINDOW_SEC * FS]
    names = epochs.ch_names
    for group, channels in GROUPS.items():
        idx = [names.index(c) for c in channels if c in names]
        if len(idx) == len(channels):
            out[group] = log_band_power(arr[:, idx] * 1e6, NUIS_BANDS, N_LAGS)
    hr_epochs = arr[:, names.index("HR")].reshape(len(arr), N_LAGS, -1).mean(axis=-1)
    out["hr"] = hr_epochs.astype(np.float32)
    out["median_hr"] = np.float32(median_rate)
    return out, labels


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--eeg-cache", required=True, help="ridge_learning_curve.py features (x_<scan>, y_<scan>)")
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--out", required=True)
    parser.add_argument("--scans", nargs="*", help="only these scans (for testing)")
    args = parser.parse_args()
    mne.set_log_level("ERROR")

    scans = args.scans or pd.read_excel(args.split_sheet, sheet_name="fold1")["scan_name"].tolist()
    cache = np.load(args.eeg_cache)
    roi7 = [label for label, _ in ROIS]
    arrays, labels = {}, None
    for scan in scans:
        out, labels = build_scan(scan, args.dataset_root)
        y7 = cache[f"y_{scan}"]
        if len(y7) != len(out["y_all"]):
            raise RuntimeError(f"{scan}: {len(out['y_all'])} frames, cache has {len(y7)}")
        gap = np.abs(out["y_all"][:, [labels.index(r) for r in roi7]] - y7).max()
        if gap > 1e-4:
            raise RuntimeError(f"{scan}: targets differ from the cache by {gap}")
        for key, value in out.items():
            arrays[f"{key}_{scan}"] = value
        print(f"{scan}: {len(y7)} frames, groups {[g for g in GROUPS if g in out]}, "
              f"median HR {float(out['median_hr']):.0f} bpm, HR NaN-free {np.isfinite(out['hr']).all()}", flush=True)
    np.savez(args.out, labels=np.array(labels), scans=np.array(scans), nuis_bands=np.array(NUIS_BANDS), **arrays)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
