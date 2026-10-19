#!/usr/bin/env python3
"""Does NeuroBOLT itself transfer to ds006040? Zero-shot scoring of the per-ROI checkpoints.

Models: the seven per-ROI checkpoints of our inter-subject reproduction (16 s windows) and the authors'
published checkpoints. Input: the same 26 channels at 200 Hz, 0.5 Hz high-pass, 16 s windows ending at
each volume marker, divided by 100 as in training. Two input scalings: as recorded ("raw"), and each
channel rescaled so its SD matches the median SD of that channel in three VU scans ("vu-scaled": a
fix for amplitude differences between sites that needs no fMRI). Scored on the frames that
ext_build_ds006040.py kept (24 s windows clear of missing EEG), so ridge and NeuroBOLT see the same frames.

    python scripts/ext_neurobolt.py --root $M3_SCRATCH/ext/ds006040 --ext chunk*.npz --runs-dir $M3_OUT/paper_resting/inter \
        --published-dir checkpoints/published --dataset-root $M3_DATA --out $M3_OUT/ext/neurobolt --subjects sub-001 ...
"""
import argparse
import csv
import glob
import os
import sys

import mne
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_inter_per_scan import CH_NAMES, ROIS, load_model, load_scan, predict, selected_checkpoint  # noqa: E402
from ext_build_ds006040 import RENAME  # noqa: E402
from ext_transfer import load_ext  # noqa: E402

FS, WINDOW_SEC = 200, 16


def windows(set_path):
    raw = mne.io.read_raw_eeglab(set_path, preload=True, verbose=False)
    raw.rename_channels({k: v for k, v in RENAME.items() if k in raw.ch_names})
    raw.pick(CH_NAMES)
    gap = ~np.isfinite(raw.get_data()).all(axis=0)
    if gap.any():
        raw._data[:, gap] = 0.0
    raw.resample(FS, verbose=False)
    raw.filter(l_freq=0.5, h_freq=None, verbose=False)
    events, event_id = mne.events_from_annotations(raw, verbose=False)
    volumes = mne.pick_events(events, include=event_id["TR"])
    epochs = mne.Epochs(raw, volumes, tmin=-WINDOW_SEC, tmax=0, baseline=(None, None), preload=True, verbose=False)
    return epochs.get_data(units="uV")[:, :, :WINDOW_SEC * FS].astype(np.float32), epochs.selection


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True)
    parser.add_argument("--ext", nargs="+", required=True)
    parser.add_argument("--runs-dir", required=True)
    parser.add_argument("--published-dir", required=True)
    parser.add_argument("--dataset-root", required=True, help="VU data, for the channel-SD reference")
    parser.add_argument("--subjects", nargs="*")
    parser.add_argument("--tag", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    mne.set_log_level("ERROR")
    os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    input_chans = utils.get_input_chans(CH_NAMES)
    sets = {"NeuroBOLT (ours)": [load_model(selected_checkpoint(os.path.join(args.runs_dir, str(j)))[0], device)[0]
                                 for j in range(len(ROIS))],
            "NeuroBOLT (published)": [load_model(os.path.join(args.published_dir, f"{stem}.pth"), device)[0]
                                      for _, stem in ROIS]}
    ref = []
    for scan in ("sub11-scan01", "sub16-scan01", "sub02-scan01"):
        eeg, _ = load_scan(scan, args.dataset_root, highpass=True, window_sec=WINDOW_SEC)
        ref.append(eeg.std(axis=(0, 2)))
    vu_sd = np.median(np.stack(ref), axis=0)

    ext = load_ext(args.ext)
    labels = [str(s) for s in ext["labels"]]
    cols = [labels.index(label) for label, _ in ROIS]
    runs = [str(r) for r in ext["runs"] if not args.subjects or str(r).split("_")[0] in set(args.subjects)]
    rows = []
    for run in runs:
        sub, cond = run.split("_")
        path = glob.glob(os.path.join(args.root, "derivatives", sub, "eeg", f"{sub}_task-{cond}ON_run-1_desc-anc0qrsrm_eeg.set"))[0]
        eeg, selection = windows(path)
        frames = ext[f"frame_{run}"]
        pos = {f: i for i, f in enumerate(selection)}
        keep = [i for i, f in enumerate(frames) if f in pos]
        x = eeg[[pos[frames[i]] for i in keep]]
        y = ext[f"y_{run}"][keep][:, cols]
        scaled = x * (vu_sd / (x.std(axis=(0, 2)) + 1e-6))[None, :, None]
        for scaling, inp in (("raw", x), ("vu-scaled", scaled)):
            for name, models in sets.items():
                pred = np.stack([predict(m, inp, device, input_chans) for m in models], axis=1)
                for j, (label, _) in enumerate(ROIS):
                    rows.append({"model": name, "scaling": scaling, "run": run, "subject": sub, "condition": cond,
                                 "roi": label, "corr": float(np.corrcoef(pred[:, j], y[:, j])[0, 1])})
        mine = [r["corr"] for r in rows if r["run"] == run and r["scaling"] == "vu-scaled" and r["model"] == "NeuroBOLT (published)"]
        print(f"{run}: {len(keep)} frames, published NeuroBOLT (vu-scaled) mean R {np.mean(mine):.3f}", flush=True)
        with open(os.path.join(args.out, f"neurobolt{args.tag}.csv"), "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
