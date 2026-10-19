#!/usr/bin/env python3
"""Validate the arousal-monitor prototype on ds006040, which the model never saw.

For every eyes-closed and eyes-open rest run: run the monitor offline (features standardized within
the run) and in streaming mode (causal filter, running statistics), and compare its predicted global
BOLD with the measured one. Then test the QC use: across runs, does the EEG-derived arousal
fluctuation track the measured global-signal swing (SD of fMRIPrep's raw global signal) and how
predictable the run is? Writes per-run results, latency, and compact JSON for the demo page.

    python scripts/ext_eval_monitor.py --root $M3_SCRATCH/ext/ds006040 --ext ds006040_cache.npz \
        --model $M3_OUT/ext/transfer/vu_model_full.npz --out $M3_OUT/ext/monitor
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.arousal_monitor import features, monitor  # noqa: E402
from app.arousal_monitor.model import FrozenModel  # noqa: E402
from app.arousal_monitor.stream import StreamingMonitor  # noqa: E402


def load_ext(paths):
    """Merge the per-chunk outputs of ext_build_ds006040.py into one dict-like mapping."""
    merged, runs = {}, []
    for path in paths:
        z = np.load(path)
        merged.update({k: z[k] for k in z.files if k not in ("runs", "labels")})
        merged["labels"] = z["labels"]
        runs += [str(r) for r in z["runs"]]
    merged["runs"] = np.array(sorted(runs))
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True)
    parser.add_argument("--ext", required=True, nargs="+", help="ext_build_ds006040.py output (measured targets per run)")
    parser.add_argument("--model", required=True)
    parser.add_argument("--demo-runs", type=int, default=6, help="subjects whose EC and EO runs go into the demo")
    parser.add_argument("--subjects", nargs="*", help="only these subjects (to split the work across jobs)")
    parser.add_argument("--tag", default="", help="suffix for this chunk's output files")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    model = FrozenModel(args.model)
    ext = load_ext(args.ext)
    labels = [str(s) for s in ext["labels"]]
    g = labels.index("global signal clean")
    rows, demo = [], {}
    runs = [str(r) for r in ext["runs"]]
    if args.subjects:
        runs = [r for r in runs if r.split("_")[0] in set(args.subjects)]
    for run in runs:
        sub, cond = run.split("_")
        path = glob.glob(os.path.join(args.root, "derivatives", sub, "eeg", f"{sub}_task-{cond}ON_run-1_desc-anc0qrsrm_eeg.set"))[0]
        raw = features.load_raw(path)
        data, prepared = features.prepare(raw)
        samples = features.frame_samples(prepared, "TR")
        feats, keep = features.features_at(data, samples, prepared.gap_times)
        frame_idx = np.flatnonzero(keep)
        # measured targets from the builder, aligned by frame index
        built_frames = ext[f"frame_{run}"]
        common = np.intersect1d(frame_idx, built_frames)
        sel_f = np.searchsorted(frame_idx, common)
        sel_y = np.searchsorted(built_frames, common)
        measured = ext[f"y_{run}"][sel_y, g]
        offline = model.predict(feats, standardize="self")[sel_f]
        vig = features.vigilance(feats)[sel_f]
        times = samples[common] / features.FS
        frames, summary = monitor.analyse(times, offline, model.labels, vig)

        # streaming replay
        mon = StreamingMonitor(model)
        stream_raw = features.prepare(raw, highpass=None)[0]
        preds, cursor, stream_frames = [], 0, []
        for i, s in enumerate(samples):
            mon.push(stream_raw[:, cursor:s])
            cursor = s
            out = mon.frame()
            if out is not None:
                preds.append(out[0][g])
                stream_frames.append(i)
        stream_pred = pd.Series(preds, index=stream_frames).reindex(common).to_numpy()
        ok = np.isfinite(stream_pred)
        r_off = float(np.corrcoef(frames["pred_global"], measured)[0, 1])
        r_stream = float(np.corrcoef(stream_pred[ok], measured[ok])[0, 1])
        r_agree = float(np.corrcoef(stream_pred[ok], frames["pred_global"][ok])[0, 1])
        gs_raw = ext[f"gsraw_{run}"]
        rows.append({"run": run, "subject": sub, "condition": cond, "frames": len(common),
                     "r_offline": r_off, "r_streaming": r_stream, "r_stream_vs_offline": r_agree,
                     "arousal_fluctuation": summary["arousal_fluctuation"], "vigilance_sd": summary["vigilance_sd"],
                     "low_vigilance_fraction": summary["low_vigilance_fraction"],
                     "measured_gs_sd_raw": float(np.std(gs_raw)), "mean_fd": float(np.mean(ext[f"fd_{run}"])),
                     "latency_ms_median": float(np.median(mon.latency_ms))})
        print(f"{run}: r offline {r_off:.3f} streaming {r_stream:.3f} (agreement {r_agree:.3f}), "
              f"latency {rows[-1]['latency_ms_median']:.1f} ms", flush=True)
        demo[run] = {"t": np.round(times, 1).tolist(), "vigilance_z": np.round(frames["vigilance_z"], 3).tolist(),
                     "pred_global": np.round(frames["pred_global"], 4).tolist(),
                     "measured_global": np.round(measured, 4).tolist(),
                     "episodes": summary["low_vigilance_episodes"], "r": round(r_off, 3)}
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(args.out, f"monitor_runs{args.tag}.csv"), index=False)
    lines = []
    for cond, d in df.groupby("condition"):
        lines.append(f"{cond}: offline r {d.r_offline.mean():.3f} (SD {d.r_offline.std():.3f}), streaming r "
                     f"{d.r_streaming.mean():.3f}, stream-offline agreement {d.r_stream_vs_offline.mean():.3f}, n={len(d)}")
    for key in ("arousal_fluctuation", "vigilance_sd"):
        for target in ("measured_gs_sd_raw", "r_offline", "mean_fd"):
            rho, p = stats.spearmanr(df[key], df[target])
            lines.append(f"Spearman {key} vs {target}: rho {rho:+.2f} (p {p:.3g})")
    lines.append(f"median latency per volume {df.latency_ms_median.median():.1f} ms")
    print("\n".join(lines))
    with open(os.path.join(args.out, f"summary{args.tag}.txt"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    picks = sorted({r.split("_")[0] for r in runs})[: args.demo_runs]
    with open(os.path.join(args.out, f"demo{args.tag}.json"), "w", encoding="utf-8") as stream:
        json.dump({r: v for r, v in demo.items() if r.split("_")[0] in picks}, stream)


if __name__ == "__main__":
    main()
