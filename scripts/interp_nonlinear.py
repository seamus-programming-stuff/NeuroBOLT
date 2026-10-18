#!/usr/bin/env python3
"""Does a nonlinear readout of EEG band power beat ridge across people? 5-fold, subject-grouped CV.

Motivated by the MEL preprint (arXiv 2608.29304), which reports that a small MLP on a lag x channel
x band log-power cube beats ridge on the same VU data under leave-one-subject-out. Same features
for every model, all from the cached 24 s windows:
  cube   26 channels x 5 classic bands x 12 two-second lags (1,560 features)
  bands  channel-averaged five bands x 12 lags (60 features)
Models, each fitted on a fold's training people, tuned on its validation people, scored on its
held-out people:
  ridge        penalty by validation MSE
  spline       ridge on an additive basis (each feature through 4 hinge functions at its training quantiles)
  interact     ridge on the features plus every pairwise product (bands only)
  vig_x        ridge on the features plus each feature times the vigilance index at the same lag
  mlp          one hidden layer (width, weight decay chosen on validation), early stopping on validation,
               averaged over 5 seeds
Input standardisation: over the training scans (as our ridge), or within each scan ("scanz",
which uses only that scan's own EEG and may be what MEL's z-scoring does).

    python scripts/interp_nonlinear.py --eeg-cache features_fine_w24_sub12.npz --out $M3_OUT/interp/nonlinear
"""
import argparse
import csv
import itertools
import os
import sys

import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ridge import ALPHAS, ridge_path  # noqa: E402
from eval_inter_per_scan import ROIS  # noqa: E402
from interp_cv import BANDS, FREQS, as_cube, band_power  # noqa: E402

N_SEEDS = 5
MLP_GRID = list(itertools.product((32, 128), (1e-4, 1e-2, 1e-1), (0.0, 0.3)))  # width, weight decay, dropout


def features(x, kind):
    """(features, vigilance index per lag): 'bands' is band-major (5 x 12), 'cube' channel x band x lag."""
    cube = as_cube(x)
    if kind == "bands":
        out = np.concatenate([band_power(cube, lo, hi) for lo, hi in BANDS.values()], axis=1)
    else:
        out = np.stack([logsumexp(cube[:, :, (FREQS >= lo) & (FREQS < hi)], axis=2) for lo, hi in BANDS.values()],
                       axis=2).reshape(len(x), -1)
    vig = band_power(cube, 8, 13) - band_power(cube, 1, 8)
    return out.astype(np.float32), vig.astype(np.float32)


def hinge_basis(train, others, n_knots=4):
    knots = np.quantile(train, np.linspace(0.2, 0.8, n_knots), axis=0)  # (knots, features)
    expand = lambda a: np.concatenate([a] + [np.maximum(a - k, 0) for k in knots], axis=1)  # noqa: E731
    return expand(train), [expand(o) for o in others]


def pairwise(a):
    i, j = np.triu_indices(a.shape[1], k=1)
    return np.concatenate([a, a[:, i] * a[:, j]], axis=1)


def ridge_fit(x_tr, y_tr, x_va, y_va, x_te):
    mean, std = x_tr.mean(axis=0), x_tr.std(axis=0) + 1e-8
    path = ridge_path((x_tr - mean) / std, y_tr, [(x_va - mean) / std, (x_te - mean) / std], ALPHAS)
    out = np.zeros((len(x_te), y_tr.shape[1]), dtype=np.float32)
    for j in range(y_tr.shape[1]):
        best = min(path, key=lambda a: float(np.mean((path[a][0][:, j] - y_va[:, j]) ** 2)))
        out[:, j] = path[best][1][:, j]
    return out


def mlp_fit(x_tr, y_tr, x_va, y_va, x_te, device, max_epochs=200, patience=15):
    """Best validation-MSE configuration from MLP_GRID, test predictions averaged over N_SEEDS seeds."""
    as_t = lambda a: torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32)).to(device)  # noqa: E731
    xt, yt, xv, yv, xe = map(as_t, (x_tr, y_tr, x_va, y_va, x_te))

    def train(width, wd, dropout, seed):
        torch.manual_seed(seed)
        model = torch.nn.Sequential(torch.nn.Dropout(dropout), torch.nn.Linear(xt.shape[1], width), torch.nn.GELU(),
                                    torch.nn.Linear(width, yt.shape[1])).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=wd)
        best, best_state, wait = np.inf, None, 0
        gen = torch.Generator(device="cpu").manual_seed(seed)
        for _ in range(max_epochs):
            model.train()
            for idx in torch.randperm(len(xt), generator=gen).split(256):
                opt.zero_grad()
                loss = torch.nn.functional.mse_loss(model(xt[idx.to(device)]), yt[idx.to(device)])
                loss.backward()
                opt.step()
            model.eval()
            with torch.no_grad():
                val = float(torch.nn.functional.mse_loss(model(xv), yv))
            if val < best - 1e-5:
                best, wait = val, 0
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            else:
                wait += 1
                if wait >= patience:
                    break
        model.load_state_dict(best_state)
        with torch.no_grad():
            return best, model(xe).cpu().numpy()

    scored = [(train(w, wd, d, 0)[0], (w, wd, d)) for w, wd, d in MLP_GRID]
    _, (w, wd, d) = min(scored, key=lambda s: s[0])
    preds = [train(w, wd, d, seed)[1] for seed in range(N_SEEDS)]
    return np.mean(preds, axis=0), f"width={w} wd={wd:g} dropout={d}"


def record(rows, results, split, data, k, kind, norm):
    for model, (pred, chosen) in results.items():
        start = 0
        for scan in split["test"]:
            n = len(data[scan]["y"])
            for j, (label, _) in enumerate(ROIS):
                rows.append({"features": kind, "norm": norm, "model": model, "fold": k, "scan": scan,
                             "roi": label, "chosen": chosen,
                             "corr": float(np.corrcoef(pred[start:start + n, j], data[scan]["y"][:, j])[0, 1])})
            start += n
        mine = [r["corr"] for r in rows if (r["fold"], r["features"], r["norm"], r["model"]) == (k, kind, norm, model)]
        print(f"fold{k} {kind:5s} {norm:6s} {model:8s} R={np.mean(mine):.3f} {chosen}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg-cache", required=True)
    parser.add_argument("--split-sheet", default="./scan_split_cv5.xlsx")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--loso", action="store_true",
                        help="leave one person out instead of the 5 folds (validation: the next 3 people in order); "
                             "ridge and MLP on globally standardized features only, as in MEL")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    z = np.load(args.eeg_cache)
    scans = sorted(k[2:] for k in z.files if k.startswith("x_"))
    data = {}
    for s in scans:
        x = z[f"x_{s}"]
        data[s] = {kind: features(x, kind) for kind in ("cube", "bands")}
        data[s]["y"] = z[f"y_{s}"].astype(np.float32)
    rows = []
    people = sorted({s.split("-")[0] for s in scans})
    plans = []
    if args.loso:
        for i, held in enumerate(people):
            val_people = {people[(i + d) % len(people)] for d in (1, 2, 3)}
            plans.append((i + 1, {"test": [s for s in scans if s.startswith(held + "-")],
                                  "val": [s for s in scans if s.split("-")[0] in val_people],
                                  "train": [s for s in scans if s.split("-")[0] not in val_people | {held}]}))
    else:
        for k in range(1, args.folds + 1):
            sheet = pd.read_excel(args.split_sheet, sheet_name=f"fold{k}")
            plans.append((k, {name: sheet.loc[sheet[name] == 1, "scan_name"].tolist() for name in ("train", "val", "test")}))
    combos = [("bands", "global"), ("cube", "global")] if args.loso else list(itertools.product(("bands", "cube"), ("global", "scanz")))
    for k, split in plans:
        y = {name: np.concatenate([data[s]["y"] for s in group]) for name, group in split.items()}
        for kind, norm in combos:
            def get(group, which=0):
                parts = []
                for s in group:
                    a = data[s][kind][which]
                    if norm == "scanz":
                        a = (a - a.mean(axis=0)) / (a.std(axis=0) + 1e-8)
                    parts.append(a)
                return np.concatenate(parts)
            x = {name: get(group) for name, group in split.items()}
            vig = {name: get(group, 1) for name, group in split.items()}
            mean, std = x["train"].mean(axis=0), x["train"].std(axis=0) + 1e-8
            xs = {name: (a - mean) / std for name, a in x.items()}
            results = {"ridge": (ridge_fit(xs["train"], y["train"], xs["val"], y["val"], xs["test"]), "")}
            if args.loso:
                results["mlp"] = mlp_fit(xs["train"], y["train"], xs["val"], y["val"], xs["test"], device)
                record(rows, results, split, data, k, kind, norm)
                continue
            tr, (va, te) = hinge_basis(xs["train"], [xs["val"], xs["test"]])
            results["spline"] = (ridge_fit(tr, y["train"], va, y["val"], te), "")
            vm, vsd = vig["train"].mean(axis=0), vig["train"].std(axis=0) + 1e-8
            n_lags = vig["train"].shape[1]
            vx = {name: np.concatenate([xs[name], xs[name] * np.tile((vig[name] - vm) / vsd,
                                                                     xs[name].shape[1] // n_lags)], axis=1)
                  for name in xs}
            results["vig_x"] = (ridge_fit(vx["train"], y["train"], vx["val"], y["val"], vx["test"]), "")
            if kind == "bands":
                results["interact"] = (ridge_fit(pairwise(xs["train"]), y["train"], pairwise(xs["val"]), y["val"],
                                                 pairwise(xs["test"])), "")
            results["mlp"] = mlp_fit(xs["train"], y["train"], xs["val"], y["val"], xs["test"], device)
            record(rows, results, split, data, k, kind, norm)
        if rows:
            with open(os.path.join(args.out, "scores.csv"), "w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    table = pd.DataFrame(rows).groupby(["features", "norm", "model"])["corr"].mean().unstack("model")
    print(table.round(3).to_string())


if __name__ == "__main__":
    main()
