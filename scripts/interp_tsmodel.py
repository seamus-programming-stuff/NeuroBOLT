#!/usr/bin/env python3
"""An interpretable end-to-end spectral model of EEG-to-BOLD with learned frequency bands, 5-fold CV.

Each layer has a physical meaning, so the fitted model can be read off directly:
  1. a bank of K learnable band-pass filters shared by all channels, applied in the frequency
     domain: each filter is a smooth pass-band (sigmoid edges, 0.5 Hz wide) with learnable low and
     high cut-offs over the 0.5 Hz periodogram of each 2 s piece of the EEG window. This is the
     frequency-domain equivalent of a SincNet filterbank followed by power in 2 s bins;
  2. log power per channel x filter x lag, standardized;
  3. readout per ROI: a full linear map over channel x filter x lag ('full', ridge with learned
     bands) or rank-2 components of channel pattern x filter weights x lag profile ('cp').
Trained on all seven ROIs at once with AdamW, weight decay chosen and training stopped on the
fold's validation people, scored on its held-out people; test predictions averaged over seeds.
The question: do learned bands beat fixed 1 Hz bins, and where do the learned bands settle?

    python scripts/interp_tsmodel.py --dataset-root $M3_DATA --out $M3_OUT/interp/tsmodel

Writes scores.csv (per variant x scan x ROI) and filters.csv (learned band edges per fold and seed).
"""
import argparse
import csv
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_inter_per_scan import ROIS, load_scan  # noqa: E402

FS, WINDOW_SEC, LAG_SEC, K = 200, 24, 2, 10
N_LAGS = WINDOW_SEC // LAG_SEC
FREQS = np.fft.rfftfreq(LAG_SEC * FS, 1 / FS)
KEEP = (FREQS >= 0.5) & (FREQS <= 45)


def periodograms(eeg):
    """(n, C, T) -> (n, C, lags, freqs) Hann-windowed power of each 2 s piece, 0.5-45 Hz."""
    n, c, _ = eeg.shape
    pieces = eeg[..., : N_LAGS * LAG_SEC * FS].reshape(n, c, N_LAGS, LAG_SEC * FS)
    spec = np.abs(np.fft.rfft(pieces * np.hanning(LAG_SEC * FS), axis=-1)) ** 2
    return spec[..., KEEP].astype(np.float32)


class LearnedBands(torch.nn.Module):
    def __init__(self, channels, n_rois, readout="full", rank=2, k=K):
        super().__init__()
        edges = np.geomspace(1.0, 45.0, k + 1)
        self.low = torch.nn.Parameter(torch.tensor(edges[:-1], dtype=torch.float32))
        self.high = torch.nn.Parameter(torch.tensor(edges[1:], dtype=torch.float32))
        self.register_buffer("freqs", torch.tensor(FREQS[KEEP], dtype=torch.float32))
        n_feat = channels * N_LAGS * k
        self.norm = torch.nn.BatchNorm1d(n_feat, affine=False)
        self.readout = readout
        if readout == "full":
            self.linear = torch.nn.Linear(n_feat, n_rois)
        else:
            self.chan = torch.nn.Parameter(torch.randn(n_rois, rank, channels) * 0.1)
            self.lag = torch.nn.Parameter(torch.randn(n_rois, rank, N_LAGS) * 0.1)
            self.spec = torch.nn.Parameter(torch.randn(n_rois, rank, k) * 0.1)
            self.bias = torch.nn.Parameter(torch.zeros(n_rois))

    def edges(self):
        low = self.low.clamp(0.5, 44.0)
        high = torch.maximum(self.high, low + 0.5).clamp(max=45.0)
        return low, high

    def masks(self):
        low, high = self.edges()
        f = self.freqs[None]
        return torch.sigmoid((f - low[:, None]) / 0.25) * torch.sigmoid((high[:, None] - f) / 0.25)  # (K, F)

    def forward(self, p):  # p: (B, C, lags, F) power
        m = self.masks()
        power = torch.einsum("bclf,kf->bclk", p, m) / (m.sum(dim=1) + 1e-3)
        f = self.norm(torch.log(power + 1e-6).reshape(len(p), -1))
        if self.readout == "full":
            return self.linear(f)
        w = torch.einsum("orc,orl,ork->oclk", self.chan, self.lag, self.spec).reshape(len(self.bias), -1)
        return f @ w.T + self.bias


def run_fold(data, split, readout, wd, device, seed, max_epochs=150, patience=12, batch=128):
    torch.manual_seed(seed)
    x_tr = torch.cat([data[s][0] for s in split["train"]]).to(device)
    y_tr = torch.cat([data[s][1] for s in split["train"]]).to(device)
    x_va = torch.cat([data[s][0] for s in split["val"]]).to(device)
    y_va = torch.cat([data[s][1] for s in split["val"]]).to(device)
    model = LearnedBands(x_tr.shape[1], y_tr.shape[1], readout=readout).to(device)
    bands = [model.low, model.high]
    rest = [p for n, p in model.named_parameters() if n not in ("low", "high")]
    opt = torch.optim.AdamW([{"params": bands, "lr": 0.05, "weight_decay": 0.0},
                             {"params": rest, "lr": 1e-3, "weight_decay": wd}])
    best, best_state, wait = np.inf, None, 0
    gen = torch.Generator().manual_seed(seed)
    for _ in range(max_epochs):
        model.train()
        for idx in torch.randperm(len(x_tr), generator=gen).split(batch):
            idx = idx.to(device)
            opt.zero_grad()
            torch.nn.functional.mse_loss(model(x_tr[idx]), y_tr[idx]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            val = float(torch.nn.functional.mse_loss(model(x_va), y_va))
        if val < best - 1e-5:
            best, wait = val, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        preds = [model(data[s][0].to(device)).cpu() for s in split["test"]]
    low, high = model.edges()
    return best, preds, (low.detach().cpu().numpy(), high.detach().cpu().numpy())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    scans = pd.read_excel(args.split_sheet, sheet_name="fold1")["scan_name"].tolist()
    data = {}
    for scan in scans:
        eeg, y = load_scan(scan, args.dataset_root, highpass=True, window_sec=WINDOW_SEC)
        data[scan] = (torch.from_numpy(periodograms(eeg.astype(np.float32))), torch.from_numpy(y.astype(np.float32)))
        print(f"loaded {scan}: {tuple(data[scan][0].shape)}", flush=True)
    rows, filters = [], []
    for k in range(1, args.folds + 1):
        sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
        split = {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("train", "val", "test")}
        for readout in ("full", "cp"):
            tried = {wd: run_fold(data, split, readout, wd, device, seed=0) for wd in (1e-2, 1e-1, 1.0, 10.0)}
            wd = min(tried, key=lambda w: tried[w][0])
            runs = [tried[wd]] + [run_fold(data, split, readout, wd, device, seed=s) for s in range(1, args.seeds)]
            for s_i, run in enumerate(runs):
                low, high = run[2]
                filters += [{"fold": k, "readout": readout, "seed": s_i, "filter": f, "low_hz": float(a),
                             "high_hz": float(b)} for f, (a, b) in enumerate(zip(low, high))]
            for i, scan in enumerate(split["test"]):
                pred = torch.stack([r[1][i] for r in runs]).mean(dim=0).numpy()
                y = data[scan][1].numpy()
                for j, (label, _) in enumerate(ROIS):
                    rows.append({"model": f"learned_bands_{readout}", "fold": k, "scan": scan, "roi": label,
                                 "weight_decay": wd, "corr": float(np.corrcoef(pred[:, j], y[:, j])[0, 1])})
            mine = [r["corr"] for r in rows if r["fold"] == k and r["model"] == f"learned_bands_{readout}"]
            print(f"fold{k} learned_bands_{readout} wd={wd:g}: R={np.mean(mine):.3f}", flush=True)
            for name, table in (("scores.csv", rows), ("filters.csv", filters)):
                with open(os.path.join(args.out, name), "w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=table[0].keys())
                    writer.writeheader()
                    writer.writerows(table)


if __name__ == "__main__":
    main()
