#!/usr/bin/env python3
"""Score inter-subject NeuroBOLT checkpoints on each held-out scan separately.

main.py's full_test path concatenates the held-out scans and logs a single R, so the
mean +/- SD across held-out scans that the paper reports cannot be read from log.txt.
This reloads each ROI's validation-selected checkpoint from a reproduction run (and,
optionally, the authors' published checkpoints), rebuilds every validation and test
scan with prepare_full_dataloader's preprocessing, and saves per-scan metrics plus the
predicted and true time series for plotting and interval calibration.

    python scripts/eval_inter_per_scan.py \
        --runs $M3_OUT/paper_resting/inter --published-dir checkpoints/published \
        --dataset-root $M3_DATA --out $M3_OUT/paper_resting/per_scan --mc-passes 20

Each scan is scored with and without the 0.5 Hz EEG high-pass that prepare_full_dataloader
hardcodes, since the published checkpoints do not record which one they were trained with.
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import torch
from einops import rearrange
from scipy.signal import butter, filtfilt
from timm.models import create_model

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils  # noqa: E402  (repo root import, after sys.path fixup above)
import models.model  # noqa: E402,F401  (side-effect: registers 'neurobolt_default' with timm)
from dataset_maker import get_datasets, preproc  # noqa: E402

# (DiFuMo label, published checkpoint stem), in reproduce_rest_m3.sbatch's ROI index order
ROIS = [
    ("Cuneus", "Cuneus"),
    ("Heschl’s gyrus", "Heschl"),
    ("Middle frontal gyrus anterior", "Midfront"),
    ("Precuneus anterior", "Precuneus"),
    ("Putamen", "Putamen"),
    ("Thalamus", "Thalamus"),
    ("global signal clean", "glb"),
]
CH_NAMES = [
    "FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8",
    "T7", "T8", "P7", "P8", "FPZ", "FZ", "CZ", "PZ", "POZ", "OZ", "FT9",
    "FT10", "TP9", "TP10",
]  # 26 channels, order the model was trained on
TR = 2.1


def build_model():
    # main.py's defaults; the dropout rates only matter for the MC-dropout passes
    return create_model(
        "neurobolt_default",
        pretrained=False,
        EEG_channel=len(CH_NAMES),
        num_roi=1,
        drop_rate=0.1,
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


def load_model(checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = build_model()
    model.load_state_dict(checkpoint["model"])  # strict: any key mismatch is an error
    train_args = checkpoint.get("args")
    info = {
        "path": checkpoint_path,
        "epoch": str(checkpoint.get("epoch")),
        "opt_betas": getattr(train_args, "opt_betas", None),
        "train_test_mode": getattr(train_args, "train_test_mode", None),
        "batch_size": getattr(train_args, "batch_size", None),
        "epochs": getattr(train_args, "epochs", None),
        "seed": getattr(train_args, "seed", None),
    }
    return model.to(device).eval(), info


def selected_checkpoint(run_dir):
    """The min-validation-MSE epoch's checkpoint, the row collect_reproduction_results.py reports."""
    with open(os.path.join(run_dir, "log.txt"), encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    best = min(records, key=lambda row: float(row["val_mse"]))
    matches = glob.glob(os.path.join(run_dir, "*", f"checkpoint-epoch{best['epoch']}-*.pth"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one checkpoint for epoch {best['epoch']} in {run_dir}, "
                                f"found {matches}")
    return matches[0], best


def load_scan(scan_name, dataset_root, highpass):
    """EEG windows and all seven targets for one scan, built as prepare_full_dataloader builds them."""
    sub, scan = (int(x) for x in re.findall(r"\d+", scan_name))
    eeg_raw, fmri, _ = get_datasets.download_vu_dataset(sub, scan, dataset_root, output_eegmneraw=True)
    eeg_raw.load_data()
    if highpass:
        eeg_raw.filter(l_freq=0.5, h_freq=None)

    # Per-ROI 0.15 Hz low-pass and demeaned 95th-percentile scaling; both act row-wise,
    # so doing all seven ROIs at once matches the loader's one-ROI-at-a-time version.
    b, a = butter(N=5, Wn=0.15 / (0.5 / TR), btype="low", analog=False)
    targets = filtfilt(b, a, fmri[[label for label, _ in ROIS]].to_numpy().T, axis=1)
    targets, _ = preproc.normalize_data(targets)

    data_epoch, _ = preproc.epoching_seq2one(eeg_raw, targets, -16, 0, "R149", ifnorm=0, crop=3200)
    return np.stack(data_epoch["eeg"]), np.stack(data_epoch["fmri"])


@torch.no_grad()
def predict(model, eeg, device, input_chans, batch_size=64):
    preds = []
    for start in range(0, len(eeg), batch_size):
        x = torch.from_numpy(eeg[start:start + batch_size]).float().to(device) / 100
        x = rearrange(x, "B N (A T) -> B N A T", T=200)
        preds.append(model(x, input_chans=input_chans).float().cpu().numpy()[:, 0])
    return np.concatenate(preds)


def enable_mc_dropout(model):
    """Eval mode, except every dropout and drop-path layer keeps sampling as in training."""
    model.eval()
    for module in model.modules():
        if isinstance(module, torch.nn.Dropout) or type(module).__name__ == "DropPath":
            module.train()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", required=True,
                        help="inter-subject run root holding one directory per ROI index (0-6)")
    parser.add_argument("--published-dir", default=None,
                        help="directory with the authors' Cuneus.pth ... glb.pth (optional)")
    parser.add_argument("--dataset-root", default="./data")
    parser.add_argument("--split-sheet", default="./scan_split_example.xlsx")
    parser.add_argument("--out", required=True, help="directory for metrics, predictions and metadata")
    parser.add_argument("--mc-passes", type=int, default=0,
                        help="MC-dropout passes per held-out scan for the reproduction models (0: skip)")
    parser.add_argument("--device", default=None, help="cuda:0 / cpu, default: autodetect")
    args = parser.parse_args()

    device = torch.device(args.device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
    sheet = pd.read_excel(args.split_sheet, sheet_name="fold1")
    splits = {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("val", "test")}
    print(f"device={device} val={splits['val']} test={splits['test']}")

    model_sets = {"ours": [], "published": []}
    checkpoints = {"ours": {}, "published": {}}
    for index, (label, stem) in enumerate(ROIS):
        path, log_row = selected_checkpoint(os.path.join(args.runs, str(index)))
        model, info = load_model(path, device)
        model_sets["ours"].append(model)
        checkpoints["ours"][label] = {**info, "log_row": log_row}
        if args.published_dir:
            model, info = load_model(os.path.join(args.published_dir, f"{stem}.pth"), device)
            model_sets["published"].append(model)
            checkpoints["published"][label] = info
    model_sets = {name: models for name, models in model_sets.items() if models}
    for name, by_roi in checkpoints.items():
        for label, info in by_roi.items():
            print(f"{name:9s} {label:30s} epoch {info['epoch']}")

    os.makedirs(args.out, exist_ok=True)
    input_chans = utils.get_input_chans(CH_NAMES)
    rows, arrays = [], {}
    for highpass in (True, False):
        hp = "hp" if highpass else "nohp"
        for split_name, scan_names in splits.items():
            for scan_name in scan_names:
                eeg, targets = load_scan(scan_name, args.dataset_root, highpass)
                print(f"{hp} {split_name} {scan_name}: {len(eeg)} windows")
                for roi_index, (label, stem) in enumerate(ROIS):
                    true = targets[:, roi_index]
                    arrays[f"{hp}|{scan_name}|{stem}|true"] = true
                    for set_name, models in model_sets.items():
                        pred = predict(models[roi_index], eeg, device, input_chans)
                        arrays[f"{set_name}|{hp}|{scan_name}|{stem}|pred"] = pred
                        rows.append({
                            "model": set_name, "eeg_highpass": highpass, "split": split_name,
                            "scan": scan_name, "roi": label, "n": len(true),
                            "corr": float(np.corrcoef(pred, true)[0, 1]),
                            "mse": float(np.mean((pred - true) ** 2)),
                        })
                        print(f"  {set_name:9s} {stem:10s} R={rows[-1]['corr']:.4f} MSE={rows[-1]['mse']:.4f}")

                if highpass and split_name == "test" and args.mc_passes and "ours" in model_sets:
                    torch.manual_seed(12345)
                    for roi_index, (label, stem) in enumerate(ROIS):
                        model = model_sets["ours"][roi_index]
                        enable_mc_dropout(model)
                        arrays[f"ours|{hp}|{scan_name}|{stem}|mc"] = np.stack(
                            [predict(model, eeg, device, input_chans) for _ in range(args.mc_passes)])
                        model.eval()

    with open(os.path.join(args.out, "per_scan_metrics.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with open(os.path.join(args.out, "checkpoints.json"), "w", encoding="utf-8") as stream:
        json.dump({"splits": splits, "mc_passes": args.mc_passes, "checkpoints": checkpoints},
                  stream, indent=2, ensure_ascii=False, default=str)
    np.savez_compressed(os.path.join(args.out, "per_scan_predictions.npz"), **arrays)
    print(f"Wrote {len(rows)} per-scan rows and {len(arrays)} arrays to {args.out}")


if __name__ == "__main__":
    main()
