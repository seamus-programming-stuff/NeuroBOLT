"""Turn per-frame predictions into what an operator or analyst needs: arousal trace, flags and a QC summary."""
import numpy as np

GLOBAL, THALAMUS = "global signal clean", "Thalamus"


def robust_z(x):
    med = np.median(x)
    mad = np.median(np.abs(x - med)) * 1.4826 + 1e-8
    return (x - med) / mad


def episodes(mask, times, min_sec):
    """Runs of True in mask lasting at least min_sec, as (start s, end s) pairs."""
    out, start = [], None
    for i, flag in enumerate(np.append(mask, False)):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if times[i - 1] - times[start] + (times[1] - times[0] if len(times) > 1 else 0) >= min_sec:
                out.append((float(times[start]), float(times[i - 1])))
            start = None
    return out


def analyse(times, predictions, labels, vigilance, z_threshold=-1.0, min_sec=10.0):
    """Per-frame outputs and a run summary.

    - predicted global BOLD: the arousal-driven, brain-wide BOLD component the EEG predicts
      (higher = more BOLD, which in eyes-closed rest goes with lower vigilance)
    - vigilance: log alpha / (delta + theta); its robust z within the run flags low-vigilance
      periods (below z_threshold for at least min_sec)
    - arousal fluctuation: the SD of the predicted global BOLD over the run; in the VU and ds006040
      data, runs with more arousal fluctuation have larger global-signal swings and are more predictable
    """
    gs = predictions[:, labels.index(GLOBAL)]
    thal = predictions[:, labels.index(THALAMUS)]
    vz = robust_z(vigilance)
    low = vz < z_threshold
    eps = episodes(low, times, min_sec)
    frames = {"time_s": times, "vigilance": vigilance, "vigilance_z": vz, "pred_global": gs, "pred_thalamus": thal,
              "low_vigilance": low.astype(int)}
    flagged = sum(e - s for s, e in eps) + len(eps) * (times[1] - times[0] if len(times) > 1 else 0)
    summary = {"frames": int(len(times)), "duration_s": float(times[-1] - times[0]) if len(times) else 0.0,
               "arousal_fluctuation": float(np.std(gs)), "vigilance_sd": float(np.std(vigilance)),
               "low_vigilance_episodes": [{"start_s": s, "end_s": e} for s, e in eps],
               "low_vigilance_fraction": float(flagged / max(times[-1] - times[0], 1e-9)) if len(times) > 1 else 0.0}
    return frames, summary
