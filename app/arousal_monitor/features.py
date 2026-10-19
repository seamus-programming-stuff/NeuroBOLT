"""EEG preparation and features, identical to the VU training pipeline (scripts/baseline_ridge.py).

Per fMRI frame: the 24 s of EEG before it, in twelve 2 s pieces; Welch power (1 s Hann segments,
50% overlap) in 44 one-Hz bins from 1 to 45 Hz; log; ordered channel x bin x lag. 26 x 44 x 12 = 13,728.
"""
import numpy as np
from scipy.signal import welch
from scipy.special import logsumexp

CHANNELS = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T7", "T8", "P7", "P8",
            "FPZ", "FZ", "CZ", "PZ", "POZ", "OZ", "FT9", "FT10", "TP9", "TP10"]
FS, WINDOW_SEC, N_LAGS = 200, 24, 12
WINDOW = FS * WINDOW_SEC
FREQS = np.arange(1, 45) + 0.5
BANDS = {"delta": (1, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "gamma": (30, 45)}


def load_raw(path):
    """Any MNE-readable EEG file (EEGLAB .set, BrainVision .vhdr, EDF, FIF), loaded into memory."""
    import mne
    return mne.io.read_raw(path, preload=True, verbose=False)


def prepare(raw, highpass=0.5):
    """Pick the 26 model channels (case-insensitive), resample to 200 Hz, high-pass. Returns µV array and raw."""
    lookup = {name.upper(): name for name in raw.ch_names}
    missing = [c for c in CHANNELS if c not in lookup]
    if missing:
        raise ValueError(f"EEG lacks the model's channels {missing}; the model needs all 26 of {CHANNELS}")
    raw = raw.copy().pick([lookup[c] for c in CHANNELS])
    raw.rename_channels({lookup[c]: c for c in CHANNELS})
    # Missing stretches (NaN) are zero-filled so filtering cannot spread them; their times are kept
    # on the returned raw as raw.gap_times so frames that touch them can be refused.
    gap = ~np.isfinite(raw._data).all(axis=0)
    gap_times = raw.times[gap]
    if gap.any():
        raw._data[:, gap] = 0.0
    if raw.info["sfreq"] != FS:
        raw.resample(FS, verbose=False)
    if highpass:
        raw.filter(l_freq=highpass, h_freq=None, verbose=False)
    raw.gap_times = gap_times
    return raw.get_data(units="uV").astype(np.float32), raw


def frame_samples(raw, marker=None, tr=None):
    """Sample index (at 200 Hz) of each fMRI frame: from volume markers if given, else every `tr` seconds."""
    if marker:
        onsets = [a["onset"] for a in raw.annotations if a["description"] == marker]
        if not onsets:
            found = sorted({a["description"] for a in raw.annotations})
            raise ValueError(f"no '{marker}' annotations; found {found[:12]}")
        samples = np.round((np.array(onsets) - raw.first_time) * FS).astype(int)
    else:
        if not tr:
            raise ValueError("give a volume marker or a TR")
        samples = np.arange(WINDOW, raw.n_times + 1, int(round(tr * FS)))
    return samples


def window_features(windows):
    """(n, 26, 4800) µV windows -> (n, 13,728) log power, channel x 1 Hz bin x lag."""
    n, channels, samples = windows.shape
    pieces = windows.reshape(n, channels, N_LAGS, samples // N_LAGS)
    freqs, psd = welch(pieces, fs=FS, nperseg=FS, axis=-1)
    power = np.stack([psd[..., (freqs >= f) & (freqs < f + 1)].mean(axis=-1) for f in range(1, 45)], axis=2)
    return np.log(power + 1e-12).reshape(n, -1).astype(np.float32)


def features_at(data, samples, gap_times=None, margin_sec=5.0):
    """Features for every frame whose 24 s window lies inside the recording and clear of missing EEG.

    Returns (features, kept mask). gap_times: seconds (from the recording start) of missing samples.
    """
    keep = (samples >= WINDOW) & (samples <= data.shape[1])
    if gap_times is not None and len(gap_times):
        ends = samples / FS
        keep &= np.array([not ((gap_times > e - WINDOW_SEC - margin_sec) & (gap_times < e + margin_sec)).any()
                          for e in ends])
    windows = np.stack([data[:, s - WINDOW:s] for s in samples[keep]]) if keep.any() else np.zeros((0, 26, WINDOW))
    windows = windows - windows.mean(axis=-1, keepdims=True)
    return window_features(windows), keep


def band_power(features, lo, hi):
    """(n, lags) channel-averaged log total power in [lo, hi) Hz."""
    cube = features.reshape(len(features), len(CHANNELS), len(FREQS), N_LAGS)
    return logsumexp(cube[:, :, (FREQS >= lo) & (FREQS < hi)], axis=2).mean(axis=1)


def bands60(features):
    return np.concatenate([band_power(features, lo, hi) for lo, hi in BANDS.values()], axis=1).astype(np.float32)


def vigilance(features, recent_lags=4):
    """EEG vigilance index per frame: log alpha minus log (delta + theta) power, channel mean, averaged over
    the most recent 8 s (4 two-second lags) to steady it."""
    return (band_power(features, 8, 13) - band_power(features, 1, 8))[:, -recent_lags:].mean(axis=1)
