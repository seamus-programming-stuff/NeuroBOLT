#!/usr/bin/env python3
"""Standalone EEG-to-fMRI inference, extracted from Copy_of_NeuroBOLT_inference_demo.ipynb
so it can run headless (no Colab, no notebook kernel) -- locally or as an M3 sbatch job.

    python scripts/run_inference.py --scan sub16-scan01 --roi Thalamus \
        --dataset-root ./data --output reports/inference

Mirrors the notebook's full-channel and partial-channel cells exactly, including
the use_abs_pos_emb=True / use_rel_pos_bias=False checkpoint config (see
models/model.py:270 for the model's own defaults, which already match this).
"""
import argparse
import json
import math
import os
import re
import shutil
import sys

import matplotlib
matplotlib.use("Agg")  # headless: no X server on M3 compute nodes
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import torch
from einops import rearrange
from huggingface_hub import hf_hub_download
from scipy.signal import butter, filtfilt
from sklearn.metrics import mean_squared_error
from timm.models import create_model

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils  # noqa: E402  (repo root import, after sys.path fixup above)
import models.model  # noqa: E402,F401  (side-effect: registers 'neurobolt_default' with timm)
from dataset_maker import get_datasets, preproc  # noqa: E402

CH_NAMES_FULL = [
    "FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8",
    "T7", "T8", "P7", "P8", "FPZ", "FZ", "CZ", "PZ", "POZ", "OZ", "FT9",
    "FT10", "TP9", "TP10",
]  # 26 channels, order the model was trained on

DATA_REPO_ID = "NeurdyLab/NeuroBOLT"
CHECKPOINT_REPO_ID = "ssssssup/NeuroBOLT"


def ensure_scan_data(scan_name, dataset_root):
    eeg_dir = os.path.join(dataset_root, "EEG")
    fmri_dir = os.path.join(dataset_root, "fMRI_difumo")
    os.makedirs(eeg_dir, exist_ok=True)
    os.makedirs(fmri_dir, exist_ok=True)

    files_to_fetch = [
        (f"EEG_set/{scan_name}_eeg.set", eeg_dir),
        (f"EEG_set/{scan_name}_eeg.fdt", eeg_dir),
        (f"fMRI_difumo64/{scan_name}_difumo64_roi.pkl", fmri_dir),
    ]
    for remote_name, target_dir in files_to_fetch:
        target_path = os.path.join(target_dir, os.path.basename(remote_name))
        if os.path.exists(target_path):
            continue
        cached_file = hf_hub_download(
            repo_id=DATA_REPO_ID, repo_type="dataset", filename=remote_name
        )
        shutil.copy(cached_file, target_path)
        print(f"Downloaded {remote_name} -> {target_path}")


def ensure_checkpoint(roi_ckpt_name, checkpoint_dir):
    os.makedirs(checkpoint_dir, exist_ok=True)
    local_path = os.path.join(checkpoint_dir, f"{roi_ckpt_name}.pth")
    if os.path.exists(local_path):
        return local_path
    cached_file = hf_hub_download(
        repo_id=CHECKPOINT_REPO_ID,
        filename=f"checkpoints/{roi_ckpt_name}.pth",
        repo_type="model",
    )
    shutil.copy(cached_file, local_path)
    print(f"Downloaded checkpoint {roi_ckpt_name}.pth -> {local_path}")
    return local_path


def build_model():
    return create_model(
        "neurobolt_default",
        pretrained=False,
        num_roi=1,
        drop_rate=0.0,
        drop_path_rate=0.1,
        attn_drop_rate=0.0,
        drop_block_rate=None,
        use_mean_pooling=True,
        init_scale=0.001,
        use_rel_pos_bias=False,
        use_abs_pos_emb=True,
        init_values=0.1,
        qkv_bias=False,
    )


def load_checkpoint(model, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    missing, unexpected = model.load_state_dict(checkpoint["model"], strict=False)
    print(f"Checkpoint load: {len(missing)} missing, {len(unexpected)} unexpected keys")
    if missing:
        print("  missing:", missing)
    if unexpected:
        print("  unexpected:", unexpected)
    return model


def prepare_dataloader(roi_name, scan_name, dataset_root, mode):
    seed = 12345
    np.random.seed(seed)
    TR = 2.1
    tmin, tmax = -16, 0
    event_sync_name = "R149"

    sub, scan = re.findall(r"\d+", scan_name)
    sub, scan = int(sub), int(scan)

    eeg_raw, fmri, labels_roi_full = get_datasets.download_vu_dataset(
        sub, scan, dataset_root, output_eegmneraw=True
    )
    fmri_np = fmri.to_numpy().T

    df = pd.DataFrame(data=fmri_np.T, columns=labels_roi_full)
    df_filter = df[roi_name]
    fmri_np = df_filter.to_numpy().T
    if len(fmri_np.shape) < 2:
        fmri_np = fmri_np[np.newaxis, ...]

    fs = 1 / TR
    nyquist = 0.5 * fs
    low = 0.15 / nyquist
    b, a = butter(N=5, Wn=low, btype="low", analog=False)
    fmri_np = filtfilt(b, a, fmri_np)

    fmri_norm, _ = preproc.normalize_data(fmri_np)

    data_epoch, _ = preproc.epoching_seq2one(
        eeg_raw, fmri_norm, tmin, tmax, event_sync_name, ifnorm=1, crop=3200
    )

    if mode == "fullscan-inference":
        return data_epoch["eeg"], data_epoch["fmri"]

    traincrop = int(0.8 * len(data_epoch["eeg"]))
    valcrop = int(0.1 * len(data_epoch["eeg"])) + traincrop
    t_overlap = 20 if abs(tmin) <= 20 else abs(tmin)
    N_overlap = math.ceil(t_overlap / TR)
    traincrop += N_overlap
    valcrop += N_overlap
    return data_epoch["eeg"][valcrop:], data_epoch["fmri"][valcrop:]


def run_pass(model, eeg_test, fmri_test, ch_names_input, device):
    input_chans = utils.get_input_chans(ch_names_input)
    used_chan_ind = [CH_NAMES_FULL.index(ch) for ch in ch_names_input]

    X_test = np.array(eeg_test)
    y_test = np.array(fmri_test)

    x_batch = torch.from_numpy(X_test).float().to(device)
    EEG = x_batch[:, used_chan_ind, :] / 100
    if len(EEG.shape) < 3:
        EEG = EEG.unsqueeze(1)
    EEG = rearrange(EEG, "B N (A T) -> B N A T", T=200)

    y_hat = model(EEG, input_chans=input_chans, input_chans_spect=used_chan_ind)
    y_hat = y_hat.to("cpu").detach().numpy().squeeze()
    y_hat, _ = preproc.normalize_data(y_hat)

    corrval = float(np.corrcoef(y_hat.squeeze(), y_test.squeeze())[0, 1])
    mse = float(mean_squared_error(y_hat.squeeze(), y_test.squeeze()))
    return y_hat, y_test, corrval, mse


def save_plot(y_hat, y_test, title, out_path, TR=2.1):
    xdata = np.arange(len(y_test)) * TR
    plt.figure(figsize=(10, 2))
    plt.plot(xdata, y_test.squeeze(), label="true", color="grey", linestyle="dashed")
    plt.plot(xdata, y_hat.squeeze(), label="predicted", color="purple", linewidth=3, alpha=0.7)
    plt.legend()
    plt.xlim(-5, int(xdata[-1]) + 5)
    plt.xlabel("Time (sec)")
    plt.ylabel("Normalized fMRI ROI signal")
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(1))
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", default="sub16-scan01", help="e.g. sub16-scan01")
    parser.add_argument("--roi", default="Thalamus", help="DiFuMo ROI label")
    parser.add_argument("--roi-checkpoint", default=None,
                         help="checkpoint filename stem on HF, defaults to --roi")
    parser.add_argument("--dataset-root", default="./data")
    parser.add_argument("--checkpoint-dir", default="./checkpoints")
    parser.add_argument("--mode", default="fullscan-inference",
                         choices=["fullscan-inference", "intrascan-inference"])
    parser.add_argument("--channels", default=None,
                         help="comma-separated subset of CH_NAMES_FULL for a second, "
                              "partial-channel pass (default: full-channel only)")
    parser.add_argument("--output", default="reports/inference",
                         help="directory for the JSON result and plots")
    parser.add_argument("--plot", action="store_true", help="save PNG plots")
    parser.add_argument("--device", default=None, help="cuda:0 / cpu, default: autodetect")
    args = parser.parse_args()

    roi_ckpt_name = args.roi_checkpoint or args.roi
    device = torch.device(args.device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
    print(f"scan={args.scan} roi={args.roi} mode={args.mode} device={device}")

    ensure_scan_data(args.scan, args.dataset_root)
    checkpoint_path = ensure_checkpoint(roi_ckpt_name, args.checkpoint_dir)

    model = build_model()
    load_checkpoint(model, checkpoint_path)
    model = model.to(device)
    model.eval()

    eeg_test, fmri_test = prepare_dataloader(args.roi, args.scan, args.dataset_root, args.mode)

    os.makedirs(args.output, exist_ok=True)
    result = {"scan": args.scan, "roi": args.roi, "mode": args.mode}

    with torch.no_grad():
        y_hat, y_test, corr_full, mse_full = run_pass(model, eeg_test, fmri_test, CH_NAMES_FULL, device)
    print(f"Full-channel  R={corr_full:.4f}  MSE={mse_full:.4f}")
    result["full_channel"] = {"channels": CH_NAMES_FULL, "corr": corr_full, "mse": mse_full}
    if args.plot:
        save_plot(y_hat, y_test, f"{args.roi} {args.scan} R={corr_full:.4f}",
                   os.path.join(args.output, f"{args.scan}_{args.roi}_full.png"))

    if args.channels:
        ch_subset = [c.strip() for c in args.channels.split(",")]
        with torch.no_grad():
            y_hat_p, y_test_p, corr_partial, mse_partial = run_pass(
                model, eeg_test, fmri_test, ch_subset, device
            )
        print(f"Partial-channel ({len(ch_subset)} ch)  R={corr_partial:.4f}  MSE={mse_partial:.4f}")
        result["partial_channel"] = {"channels": ch_subset, "corr": corr_partial, "mse": mse_partial}
        if args.plot:
            save_plot(y_hat_p, y_test_p, f"{args.roi} {args.scan} (partial) R={corr_partial:.4f}",
                       os.path.join(args.output, f"{args.scan}_{args.roi}_partial.png"))

    out_json = os.path.join(args.output, f"{args.scan}_{args.roi}.json")
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
