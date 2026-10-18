#!/usr/bin/env python3
"""What does NeuroBOLT use, compared with ridge? Matched permutation importance and a linear surrogate.

Models: the seven per-ROI NeuroBOLT checkpoints of the inter-subject reproduction (16 s windows,
authors' split) and, optionally, the authors' published checkpoints; and ridge on log power in
1 Hz bins x 8 two-second lags over the same 16 s windows, trained on the same split.

1. Permutation importance on the six held-out scans. One part of each EEG window is replaced by
   the same part of a window from at least 60 s away in the same scan, so its statistics stay
   realistic but its timing relative to BOLD is broken. Parts: a frequency band (swapped in the
   Fourier domain), a scalp region or single channel, or a 4 s segment of the window. Every model
   sees exactly the same perturbed EEG; ridge recomputes its features from it. Reported: the drop
   in test R, and how much the prediction itself moves (variance of the change / variance of the
   prediction), which measures reliance whether or not the part helps.
2. Linear surrogate. Ridge is fitted from the band-power features to NeuroBOLT's own predictions on
   the training scans (penalty chosen on validation) and scored on the held-out scans: if it
   reproduces NeuroBOLT's output closely, NeuroBOLT is in effect a linear band-power model.

    python scripts/interp_attribution.py --runs $M3_OUT/paper_resting/inter --published-dir checkpoints/published \
        --dataset-root $M3_DATA --out $M3_OUT/interp/attribution
"""
import argparse
import csv
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS, BAND_SETS, band_power_features, ridge_path  # noqa: E402
from eval_inter_per_scan import CH_NAMES, ROIS, load_model, load_scan, predict, selected_checkpoint  # noqa: E402

FS, WINDOW_SEC, N_LAGS = 200, 16, 8
BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "gamma": (30, 45),
         "above 45 Hz": (45, 100)}
REGIONS = {"frontal": ["FP1", "FP2", "FPZ", "F3", "F4", "F7", "F8", "FZ"], "central": ["C3", "C4", "CZ"],
           "temporal": ["T7", "T8", "FT9", "FT10", "TP9", "TP10"], "parietal": ["P3", "P4", "P7", "P8", "PZ"],
           "occipital": ["O1", "O2", "OZ", "POZ"]}
SEGMENTS = {f"{16 - 4 * i}-{12 - 4 * i} s before": (i * 4 * FS, (i + 1) * 4 * FS) for i in range(4)}


def perturbations():
    out = [("band", name) for name in BANDS] + [("region", name) for name in REGIONS]
    out += [("channel", name) for name in CH_NAMES] + [("segment", name) for name in SEGMENTS]
    return out


def donors(n, rng, min_gap=29):  # 29 frames x 2.1 s = 61 s
    return (np.arange(n) + rng.integers(min_gap, n - min_gap, size=n)) % n


def perturb(eeg, spectrum, kind, name, donor):
    if kind == "band":
        lo, hi = BANDS[name]
        freqs = np.fft.rfftfreq(eeg.shape[-1], 1 / FS)
        mask = ((freqs >= lo) & (freqs < hi)).astype(np.float32)
        mixed = spectrum * (1 - mask) + spectrum[donor] * mask
        return np.fft.irfft(mixed, n=eeg.shape[-1], axis=-1).astype(np.float32)
    out = eeg.copy()
    if kind in ("region", "channel"):
        idx = [CH_NAMES.index(c) for c in (REGIONS[name] if kind == "region" else [name])]
        out[:, idx] = eeg[donor][:, idx]
    else:
        a, b = SEGMENTS[name]
        out[:, :, a:b] = eeg[donor][:, :, a:b]
    return out


def ridge_features(eeg):
    return band_power_features(eeg, BAND_SETS["fine"], N_LAGS)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", required=True, help="inter-subject reproduction root with one directory per ROI")
    parser.add_argument("--published-dir", default=None)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_example.xlsx")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    input_chans = utils.get_input_chans(CH_NAMES)

    model_sets = {"NeuroBOLT": [load_model(selected_checkpoint(os.path.join(args.runs, str(j)))[0], device)[0]
                                for j in range(len(ROIS))]}
    if args.published_dir:
        model_sets["NeuroBOLT (published)"] = [load_model(os.path.join(args.published_dir, f"{stem}.pth"), device)[0]
                                               for _, stem in ROIS]

    sheet = pd.read_excel(args.split_sheet, sheet_name="fold1")
    split = {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("train", "val", "test")}
    feats, targets, nb_preds, test_eeg = {}, {}, {}, {}
    for name, scans in split.items():
        for scan in scans:
            eeg, y = load_scan(scan, args.dataset_root, highpass=True, window_sec=WINDOW_SEC)
            eeg = eeg.astype(np.float32)
            feats[scan], targets[scan] = ridge_features(eeg), y.astype(np.float32)
            nb_preds[scan] = {m: np.stack([predict(model, eeg, device, input_chans) for model in models], axis=1)
                              for m, models in model_sets.items()}
            if name == "test":
                test_eeg[scan] = eeg
            print(f"{name} {scan}: {len(y)} windows", flush=True)

    stack = lambda d, scans: np.concatenate([d[s] for s in scans])  # noqa: E731
    x_train = stack(feats, split["train"])
    mean, std = x_train.mean(axis=0), x_train.std(axis=0) + 1e-8
    z = {name: (stack(feats, scans) - mean) / std for name, scans in split.items()}

    def fit_ridge(y_train, y_val):
        """Per-column penalty by validation MSE; returns the weights and intercepts as a predictor."""
        path = ridge_path(z["train"], y_train, [z["val"]], ALPHAS)
        best = [min(path, key=lambda a: float(np.mean((path[a][0][:, j] - y_val[:, j]) ** 2)))
                for j in range(y_train.shape[1])]
        xt = torch.from_numpy(np.ascontiguousarray(z["train"]))
        xm = xt.mean(dim=0)
        u, s, vt = torch.linalg.svd(xt - xm, full_matrices=False)
        yt = torch.from_numpy(y_train)
        uty = u.T @ (yt - yt.mean(dim=0))
        w = torch.stack([vt.T @ ((s / (s ** 2 + a)) * uty[:, j]) for j, a in enumerate(best)], dim=1)
        b = yt.mean(dim=0) - xm @ w
        return lambda f: ((torch.from_numpy(np.ascontiguousarray((f - mean) / std)) @ w) + b).numpy(), best

    ridge, ridge_alphas = fit_ridge(stack(targets, split["train"]), stack(targets, split["val"]))
    print("ridge penalties:", ridge_alphas, flush=True)

    # 2. Linear surrogates of each NeuroBOLT model set
    rows = []
    for m in model_sets:
        surrogate, _ = fit_ridge(np.concatenate([nb_preds[s][m] for s in split["train"]]),
                                 np.concatenate([nb_preds[s][m] for s in split["val"]]))
        for scan in split["test"]:
            sur, nb, rd, y = surrogate(feats[scan]), nb_preds[scan][m], ridge(feats[scan]), targets[scan]
            for j, (label, _) in enumerate(ROIS):
                c = lambda a, b: float(np.corrcoef(a[:, j], b[:, j])[0, 1])  # noqa: E731
                rows.append({"model": m, "scan": scan, "roi": label, "surrogate_vs_model": c(sur, nb),
                             "ridge_vs_model": c(rd, nb), "model_vs_bold": c(nb, y), "surrogate_vs_bold": c(sur, y),
                             "ridge_vs_bold": c(rd, y)})
    with open(os.path.join(args.out, "surrogate.csv"), "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for m in model_sets:
        mine = [r for r in rows if r["model"] == m]
        print(f"{m}: surrogate reproduces model R={np.mean([r['surrogate_vs_model'] for r in mine]):.3f}; "
              f"ridge-on-BOLD vs model R={np.mean([r['ridge_vs_model'] for r in mine]):.3f}", flush=True)

    # 1. Permutation importance on the held-out scans
    rows = []
    rng = np.random.default_rng(0)
    for scan in split["test"]:
        eeg, y = test_eeg[scan], targets[scan]
        spectrum = np.fft.rfft(eeg, axis=-1).astype(np.complex64)
        base = {"ridge": ridge(feats[scan]), **nb_preds[scan]}
        for kind, name in perturbations():
            for r in range(args.repeats):
                donor = donors(len(eeg), rng)
                x = perturb(eeg, spectrum, kind, name, donor)
                preds = {"ridge": ridge(ridge_features(x)),
                         **{m: np.stack([predict(model, x, device, input_chans) for model in models], axis=1)
                            for m, models in model_sets.items()}}
                for m, p in preds.items():
                    for j, (label, _) in enumerate(ROIS):
                        p0 = base[m][:, j]
                        rows.append({"model": m, "kind": kind, "part": name, "repeat": r, "scan": scan, "roi": label,
                                     "base_r": float(np.corrcoef(p0, y[:, j])[0, 1]),
                                     "perturbed_r": float(np.corrcoef(p[:, j], y[:, j])[0, 1]),
                                     "shift": float(np.var(p[:, j] - p0) / (np.var(p0) + 1e-12))})
        print(f"permutation importance done for {scan}", flush=True)
        with open(os.path.join(args.out, "permutation.csv"), "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    np.savez_compressed(os.path.join(args.out, "predictions.npz"),
                        **{f"{m}|{s}": nb_preds[s][m] for s in nb_preds for m in model_sets},
                        **{f"true|{s}": targets[s] for s in targets})
    print("done")


if __name__ == "__main__":
    main()
