#!/usr/bin/env python3
"""Shared-factor Hammerstein distributed-lag model of EEG-to-BOLD, 5-fold subject-grouped CV.

An interpretable time-series architecture (proposed in reports/EEG BOLD interpretability and directions.md):
  s_k(t - l) = sum_c sum_f a_kc b_kf logP_cf(t - l)        K components shared by all 65 targets:
                                                           a scalp topography and a 1 Hz spectral profile
  y_r(t)     = beta_r + sum_k sum_l h_rk(l) g_k(s_k(t - l))  a region-specific lag kernel per component
  h_rk(l)    = sum_j theta_rkj phi_j(l)                     5 smooth B-spline basis functions over 0-24 s
  g_k        = identity ('linear') or identity + 4 hinge functions of the standardized component ('spline')
With K = 4 and 65 targets this has about 1,600 parameters, against 892,000 ridge weights.
Fitted with Adam on all 65 targets, weight decay chosen and training stopped on each fold's validation
people, test predictions averaged over 3 seeds. Hypothesis: K <= 5 linear components lose at most
0.01 R against full ridge; the spline arm adds >= 0.015 if vigilance-gated coupling matters.

    python scripts/interp_hammerstein.py --eeg-cache features_fine_w24_sub12.npz --interp-cache interp_cache.npz \
        --out $M3_OUT/interp/hammerstein

Writes scores.csv (variant x scan x target) and components.npz (topographies, spectra and kernels
from fold 1 and from a fit on all scans) for interpretation.
"""
import argparse
import csv
import os
import re
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interp_cv import N_BINS, N_CH, N_LAGS  # noqa: E402

KNOTS = (-1.5, -0.5, 0.5, 1.5)


def bspline_basis(n_lags=N_LAGS, n_basis=5, degree=3):
    """(n_basis, n_lags) cubic B-splines on equally spaced knots over the lag axis."""
    from scipy.interpolate import BSpline
    inner = np.linspace(0, n_lags - 1, n_basis - degree + 1)
    knots = np.concatenate([[inner[0]] * degree, inner, [inner[-1]] * degree])
    t = np.arange(n_lags, dtype=float)
    basis = np.stack([BSpline(knots, np.eye(n_basis)[j], degree)(t) for j in range(n_basis)])
    return basis / basis.max(axis=1, keepdims=True)


class Hammerstein(torch.nn.Module):
    def __init__(self, n_targets, k, nonlinear):
        super().__init__()
        self.a = torch.nn.Parameter(torch.full((k, N_CH), 1.0 / N_CH) + 0.01 * torch.randn(k, N_CH))
        self.b = torch.nn.Parameter(0.1 * torch.randn(k, N_BINS))
        self.theta = torch.nn.Parameter(0.01 * torch.randn(n_targets, k, 5))
        self.beta = torch.nn.Parameter(torch.zeros(n_targets))
        self.register_buffer("phi", torch.tensor(bspline_basis(), dtype=torch.float32))
        self.norm = torch.nn.BatchNorm1d(k, affine=False)
        self.nonlinear = nonlinear
        if nonlinear:
            self.w = torch.nn.Parameter(torch.zeros(k, len(KNOTS)))
            self.register_buffer("knots", torch.tensor(KNOTS, dtype=torch.float32))

    def components(self, x):  # x: (B, C, F, L) -> (B, K, L)
        s = torch.einsum("bcfl,kc,kf->bkl", x, self.a, self.b)
        return self.norm(s)

    def kernels(self):  # (R, K, L)
        return torch.einsum("rkj,jl->rkl", self.theta, self.phi)

    def forward(self, x):
        s = self.components(x)
        if self.nonlinear:
            hinge = torch.relu(s[..., None] - self.knots)  # (B, K, L, M)
            s = s + torch.einsum("bklm,km->bkl", hinge, self.w)
        return torch.einsum("bkl,rkl->br", s, self.kernels()) + self.beta


def train(x, y, splits, k, nonlinear, wd, seed, device, max_epochs=200, patience=15, batch=256, smooth=0.0):
    torch.manual_seed(seed)
    model = Hammerstein(y["train"].shape[1], k, nonlinear).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    reg = [model.a, model.b, model.theta]
    best, best_state, wait = np.inf, None, 0
    gen = torch.Generator().manual_seed(seed)
    for _ in range(max_epochs):
        model.train()
        for idx in torch.randperm(len(x["train"]), generator=gen).split(batch):
            idx = idx.to(device)
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(model(x["train"][idx]), y["train"][idx])
            loss = loss + wd * sum((p ** 2).sum() for p in reg)
            if smooth:  # roughness of each spectral profile across neighbouring 1 Hz bins
                loss = loss + smooth * wd * (model.b.diff(n=2, dim=1) ** 2).sum()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            val = float(torch.nn.functional.mse_loss(model(x["val"]), y["val"]))
        if val < best - 1e-5:
            best, wait = val, 0
            best_state = {n: v.detach().clone() for n, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    return best, model


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg-cache", required=True)
    parser.add_argument("--interp-cache", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--variants", nargs="*", default=["linear1", "linear2", "linear3", "linear5", "linear8",
                                                          "spline3", "spline5"])
    parser.add_argument("--wds", type=float, nargs="+", default=[1e-5, 1e-4, 1e-3])
    parser.add_argument("--smooth", type=float, default=0.0,
                        help="penalty on second differences of the spectral profiles, as a multiple of the weight decay")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    eeg, aux = np.load(args.eeg_cache), np.load(args.interp_cache)
    labels = [str(s) for s in aux["labels"]]
    scans = [str(s) for s in aux["scans"]]
    xs = {s: eeg[f"x_{s}"] for s in scans}
    ys = {s: aux[f"y_all_{s}"] for s in scans}
    rows, saved = [], {}
    for fold in range(1, args.folds + 1):
        sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{fold}")
        split = {n: sheet.loc[sheet[n] == 1, "scan_name"].tolist() for n in ("train", "val", "test")}
        xtr = np.concatenate([xs[s] for s in split["train"]])
        mean, std = xtr.mean(axis=0), xtr.std(axis=0) + 1e-8
        to_dev = lambda a: torch.from_numpy(((a - mean) / std).astype(np.float32)).reshape(len(a), N_CH, N_BINS, N_LAGS).to(device)  # noqa: E731
        x = {n: to_dev(np.concatenate([xs[s] for s in g])) for n, g in split.items()}
        y = {n: torch.from_numpy(np.concatenate([ys[s] for s in g]).astype(np.float32)).to(device) for n, g in split.items()}
        del xtr
        for variant in args.variants:
            nonlinear, k = variant.startswith("spline"), int(re.search(r"\d+", variant).group())
            tried = {wd: train(x, y, split, k, nonlinear, wd, 0, device, smooth=args.smooth) for wd in args.wds}
            wd = min(tried, key=lambda w: tried[w][0])
            models = [tried[wd][1]] + [train(x, y, split, k, nonlinear, wd, s, device, smooth=args.smooth)[1]
                                       for s in range(1, args.seeds)]
            with torch.no_grad():
                pred = torch.stack([m(x["test"]) for m in models]).mean(dim=0).cpu().numpy()
            if fold == 1:
                m = models[0]
                saved[f"{variant}_a"] = m.a.detach().cpu().numpy()
                saved[f"{variant}_b"] = m.b.detach().cpu().numpy()
                saved[f"{variant}_h"] = m.kernels().detach().cpu().numpy()
                if nonlinear:
                    saved[f"{variant}_w"] = m.w.detach().cpu().numpy()
            start = 0
            for scan in split["test"]:
                n = len(ys[scan])
                for j, label in enumerate(labels):
                    rows.append({"variant": variant, "fold": fold, "scan": scan, "roi": label, "weight_decay": wd,
                                 "corr": float(np.corrcoef(pred[start:start + n, j], ys[scan][:, j])[0, 1])})
                start += n
            mine = [r["corr"] for r in rows if r["fold"] == fold and r["variant"] == variant]
            print(f"fold{fold} {variant}: wd={wd:g} mean R over {len(labels)} targets {np.mean(mine):.3f}", flush=True)
            with open(os.path.join(args.out, "scores.csv"), "w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        del x, y
        torch.cuda.empty_cache()
    np.savez_compressed(os.path.join(args.out, "components.npz"), labels=np.array(labels), **saved)
    table = pd.DataFrame(rows).groupby("variant")["corr"].mean()
    print(table.round(3).to_string())


if __name__ == "__main__":
    main()
