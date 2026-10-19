#!/usr/bin/env python3
"""External validation on ds006040: do models trained on the VU people predict new people at another site?

Models (ridge, penalties per target taken from the VU 5-fold CV of interp_cv.py, median over folds):
  full       26 channels x 44 one-Hz bins x 12 lags
  bands60    channel-averaged five bands x 12 lags
  vigilance  alpha / (delta + theta) x 12 lags
Transfer protocols, all applied to ds006040's eyes-closed (EC) and eyes-open (EO) rest runs:
  zero-shot     fitted on all 29 VU scans; ds006040 features standardized with VU statistics
  target-stats  the same model, ds006040 features standardized with ds006040's own feature mean and SD
                (uses only the new site's EEG, no fMRI: unsupervised adaptation)
  in-domain     5-fold subject-grouped CV within ds006040 (penalty on the fold's validation people)
  pooled        VU + the ds006040 training folds, each site standardized with its own statistics
Targets: 64 DiFuMo regions + the global signal, and the 64 regions after per-run global-signal
regression (gsr64). Also: a mismatched-person null for the zero-shot predictions, model-free
EEG-BOLD coupling by band and lag in ds006040 (to compare with VU), and an export of the frozen
VU model for the arousal-monitor prototype.

    python scripts/ext_transfer.py --vu-eeg features_fine_w24_sub12.npz --vu-aux interp_cache.npz \
        --vu-cv $M3_OUT/interp/cv_A/scores.csv --ext ds006040_cache.npz --out $M3_OUT/ext/transfer
"""
import argparse
import csv
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interp_cv import BANDS, LAG_CENTRES, as_cube, band_power, gsr, ridge_path_multi  # noqa: E402
from baseline_ridge import ALPHAS  # noqa: E402

ROI7 = ["Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior", "Precuneus anterior", "Putamen", "Thalamus",
        "global signal clean"]


def feature_sets(x):
    cube = as_cube(x)
    return {"full": x,
            "bands60": np.concatenate([band_power(cube, lo, hi) for lo, hi in BANDS.values()], axis=1).astype(np.float32),
            "vigilance": (band_power(cube, 8, 13) - band_power(cube, 1, 8)).astype(np.float32)}


def vu_alphas(cv_path, labels):
    """{(feature set, target set): per-target penalty}, the median over folds of what VU CV chose."""
    cv = pd.read_csv(cv_path)
    name = {"eeg_full": "full", "bands60": "bands60", "vigilance": "vigilance"}
    out = {}
    for feats, short in name.items():
        for tset, tlabels in (("all65", labels), ("gsr64", [l for l in labels if l != "global signal clean"])):
            sub = cv[(cv["features"] == feats) & (cv["targets"] == tset)].drop_duplicates(["roi", "fold"])
            sub = sub.assign(alpha=sub["chosen"].map(lambda c: float(re.search(r"alpha=([0-9.e+-]+)", c).group(1))))
            med = np.exp(sub.groupby("roi")["alpha"].apply(lambda a: np.median(np.log(a))))
            out[(short, tset)] = np.array([med[l] for l in tlabels])
    return out


def fit_fixed(x, y, alphas):
    """Ridge weights and intercepts with one penalty per target column, via one SVD."""
    import torch
    xt, yt = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)), torch.from_numpy(y.astype(np.float32))
    xm, ym = xt.mean(dim=0), yt.mean(dim=0)
    u, s, vt = torch.linalg.svd(xt - xm, full_matrices=False)
    uty = u.T @ (yt - ym)
    w = torch.stack([vt.T @ ((s / (s ** 2 + a)) * uty[:, j]) for j, a in enumerate(alphas)], dim=1)
    return w.numpy(), (ym - xm @ w).numpy()


def fit_select(x_tr, y_tr, x_va, y_va, x_te):
    """Ridge with the penalty chosen per target on validation data; returns test predictions."""
    path = ridge_path_multi(x_tr, y_tr, [x_va, x_te], ALPHAS)
    best = {}
    for a, (pv, pt) in path.items():
        mse = ((pv - y_va) ** 2).mean(axis=0)
        for j in range(y_tr.shape[1]):
            if j not in best or mse[j] < best[j][0]:
                best[j] = (mse[j], pt[:, j])
    return np.stack([best[j][1] for j in range(y_tr.shape[1])], axis=1)


def corr_cols(p, y):
    p, y = p - p.mean(axis=0), y - y.mean(axis=0)
    return (p * y).sum(axis=0) / np.sqrt((p ** 2).sum(axis=0) * (y ** 2).sum(axis=0) + 1e-12)


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
    parser.add_argument("--vu-eeg", required=True)
    parser.add_argument("--vu-aux", required=True)
    parser.add_argument("--vu-cv", required=True)
    parser.add_argument("--ext", required=True, nargs="+")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", torch.get_num_threads())))
    os.makedirs(args.out, exist_ok=True)

    vu_eeg, vu_aux, ext = np.load(args.vu_eeg), np.load(args.vu_aux), load_ext(args.ext)
    labels = [str(s) for s in vu_aux["labels"]]
    region_labels = [l for l in labels if l != "global signal clean"]
    vu_scans = [str(s) for s in vu_aux["scans"]]
    runs = [str(r) for r in ext["runs"]]
    bad = [r for r in runs if not (np.isfinite(ext[f"x_{r}"]).all() and np.isfinite(ext[f"y_{r}"]).all())]
    if bad:
        print(f"skipping runs with non-finite values: {bad}", flush=True)
        runs = [r for r in runs if r not in bad]
    alphas = vu_alphas(args.vu_cv, labels)

    vu = {s: (feature_sets(vu_eeg[f"x_{s}"]), vu_aux[f"y_all_{s}"]) for s in vu_scans}
    ex = {r: (feature_sets(ext[f"x_{r}"]), ext[f"y_{r}"]) for r in runs}
    tgt = lambda y: {"all65": y, "gsr64": gsr(y, labels)}  # noqa: E731
    subject = lambda r: r.split("_")[0]  # noqa: E731
    cond = lambda r: r.split("_")[1]  # noqa: E731
    rows, preds_keep = [], {}

    def record(model, protocol, run, pred, tset, y):
        r = corr_cols(pred, y)
        names = labels if tset == "all65" else region_labels
        for j, lab in enumerate(names):
            rows.append({"model": model, "protocol": protocol, "targets": tset, "run": run, "subject": subject(run),
                         "condition": cond(run), "roi": lab, "corr": float(r[j])})

    for fs in ("full", "bands60", "vigilance"):
        xv = np.concatenate([vu[s][0][fs] for s in vu_scans])
        vu_mean, vu_sd = xv.mean(axis=0), xv.std(axis=0) + 1e-8
        xe_all = np.concatenate([ex[r][0][fs] for r in runs])
        ex_mean, ex_sd = xe_all.mean(axis=0), xe_all.std(axis=0) + 1e-8
        for tset in ("all65", "gsr64"):
            yv = np.concatenate([tgt(vu[s][1])[tset] for s in vu_scans])
            w, b = fit_fixed((xv - vu_mean) / vu_sd, yv, alphas[(fs, tset)])
            if tset == "all65" and fs in ("full", "bands60"):
                np.savez_compressed(os.path.join(args.out, f"vu_model_{fs}.npz"), weights=w.astype(np.float32),
                                    intercept=b.astype(np.float32), mean=vu_mean, sd=vu_sd, labels=np.array(labels),
                                    alphas=alphas[(fs, tset)], feature_set=fs, window_sec=24, lags=12, fs=200,
                                    channels=np.array(["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7",
                                                       "F8", "T7", "T8", "P7", "P8", "FPZ", "FZ", "CZ", "PZ", "POZ", "OZ",
                                                       "FT9", "FT10", "TP9", "TP10"]))
            for r in runs:
                y = tgt(ex[r][1])[tset]
                for protocol, (m, sd) in (("zero-shot", (vu_mean, vu_sd)), ("target-stats", (ex_mean, ex_sd))):
                    pred = ((ex[r][0][fs] - m) / sd) @ w + b
                    record(fs, protocol, r, pred, tset, y)
                    if fs == "full" and protocol == "target-stats":
                        preds_keep[f"{tset}|{r}"] = pred
        print(f"{fs}: transfer done", flush=True)

        # in-domain and pooled 5-fold CV over ds006040 people
        people = sorted({subject(r) for r in runs})
        folds = np.array_split(np.random.default_rng(0).permutation(people), 5)
        for k, test_people in enumerate(folds):
            rest = [p for p in people if p not in set(test_people)]
            val_people = set(rest[-4:])
            split = {"train": [r for r in runs if subject(r) in set(rest) - val_people],
                     "val": [r for r in runs if subject(r) in val_people],
                     "test": [r for r in runs if subject(r) in set(test_people)]}
            m = np.concatenate([ex[r][0][fs] for r in split["train"]]).mean(axis=0)
            sd = np.concatenate([ex[r][0][fs] for r in split["train"]]).std(axis=0) + 1e-8
            z = {n: np.concatenate([(ex[r][0][fs] - m) / sd for r in g]) for n, g in split.items()}
            for tset in ("all65", "gsr64"):
                yy = {n: np.concatenate([tgt(ex[r][1])[tset] for r in g]) for n, g in split.items()}
                pred = fit_select(z["train"], yy["train"], z["val"], yy["val"], z["test"])
                # pooled: VU (own statistics) + this fold's ds006040 training people
                zv = (xv - vu_mean) / vu_sd
                yv = np.concatenate([tgt(vu[s][1])[tset] for s in vu_scans])
                pooled = fit_select(np.concatenate([zv, z["train"]]), np.concatenate([yv, yy["train"]]),
                                    z["val"], yy["val"], z["test"])
                start = 0
                for r in split["test"]:
                    n = len(ex[r][1])
                    record(fs, "in-domain", r, pred[start:start + n], tset, yy["test"][start:start + n])
                    record(fs, "pooled", r, pooled[start:start + n], tset, yy["test"][start:start + n])
                    start += n
            print(f"{fs}: in-domain/pooled fold {k + 1} done", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(args.out, "transfer.csv"), index=False)

    # mismatched-person null for the zero-shot-with-target-stats full model (7 ROIs)
    cols = [labels.index(l) for l in ROI7]
    nulls = []
    for a in runs:
        for b2 in runs:
            if subject(a) == subject(b2) or cond(a) != cond(b2):
                continue
            pa, yb = preds_keep[f"all65|{a}"][:, cols], ex[b2][1][:, cols]
            n = min(len(pa), len(yb))
            nulls.append({"condition": cond(a), "corr": float(np.mean(corr_cols(pa[:n], yb[:n])))})
    pd.DataFrame(nulls).to_csv(os.path.join(args.out, "mismatched_null.csv"), index=False)

    # model-free coupling in ds006040: channel-averaged band power at each lag vs each target, per run
    coupling = {}
    for c in ("EC", "EO"):
        per_run = []
        for r in [r for r in runs if cond(r) == c]:
            bands = np.stack([band_power(as_cube(ext[f"x_{r}"]), lo, hi) for lo, hi in BANDS.values()], axis=1)
            b = bands.reshape(len(bands), -1)
            y = ex[r][1]
            zb = (b - b.mean(axis=0)) / (b.std(axis=0) + 1e-8)
            zy = (y - y.mean(axis=0)) / (y.std(axis=0) + 1e-8)
            per_run.append(np.clip(zb.T @ zy / len(b), -0.999, 0.999).reshape(len(BANDS), -1, y.shape[1]))
        zs = np.arctanh(np.stack(per_run))
        coupling[f"{c}_r"] = np.tanh(zs.mean(axis=0))
        coupling[f"{c}_t"] = zs.mean(axis=0) / (zs.std(axis=0, ddof=1) / np.sqrt(len(zs)))
    np.savez_compressed(os.path.join(args.out, "coupling_ext.npz"), labels=np.array(labels), bands=np.array(list(BANDS)),
                        lag_centres=LAG_CENTRES, **coupling)
    np.savez_compressed(os.path.join(args.out, "predictions_full.npz"),
                        **{k.replace("|", "__"): v for k, v in preds_keep.items()},
                        **{f"true__{r}": ex[r][1] for r in runs}, labels=np.array(labels))

    # summary
    df7 = df[df["roi"].isin(ROI7) & (df["targets"] == "all65")]
    summary = df7.groupby(["model", "protocol", "condition", "subject"])["corr"].mean().groupby(
        ["model", "protocol", "condition"]).agg(["mean", "std", "count"])
    print(summary.round(3).to_string())
    g = df[(df["targets"] == "gsr64")].groupby(["model", "protocol", "condition", "subject"])["corr"].mean().groupby(
        ["model", "protocol", "condition"]).mean()
    print("\nGSR targets:\n" + g.round(3).to_string())
    nd = pd.DataFrame(nulls)
    print("\nmismatched null:", nd.groupby("condition")["corr"].agg(["mean", "std"]).round(3).to_string())


if __name__ == "__main__":
    main()
