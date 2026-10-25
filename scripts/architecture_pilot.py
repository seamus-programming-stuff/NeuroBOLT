#!/usr/bin/env python3
"""Fixed exploratory EC/global-BOLD cache pilot, separate from NeuroBOLT.

Freeze reads no prediction scores. Run fits/selects every model before outer
evaluation; a first-fold training/validation profile gates the full scope.
Only the explicitly supplied new output directory is written.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from thesis_study import correlations, r2, ridge_select, stack, standardize, write_csv

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("ridge", "mlp32", "transformer_mean", "transformer_lag")
SOURCE_NAMES = ("architecture_pilot.py", "architecture_pilot_m3.sbatch",
                "architecture_pilot_tests.py", "thesis_study.py", "thesis_data.py")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def save(path, value, exclusive=False):
    with Path(path).open("x" if exclusive else "w", encoding="utf-8", newline="\n") as f:
        json.dump(clean_json(value), f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def tokenize(x):
    """Cached flatten[group, band, lag] -> ordered lag tokens, never reshape-only."""
    if x.ndim != 2 or x.shape[1] != 300:
        raise ValueError("Expected N x 300 cached features")
    return x.reshape(-1, 5, 5, 12).permute(0, 3, 1, 2).reshape(-1, 12, 25)


def untokenize(tokens):
    if tokens.ndim != 3 or tuple(tokens.shape[1:]) != (12, 25):
        raise ValueError("Expected N x 12 x 25 tokens")
    return tokens.reshape(-1, 12, 5, 5).permute(0, 2, 3, 1).reshape(-1, 300)


class TinyTransformer(nn.Module):
    def __init__(self, learned_pool=False):
        super().__init__()
        self.embedding = nn.Linear(25, 32)
        layer = nn.TransformerEncoderLayer(32, 2, 64, dropout=0.1,
                                          activation="gelu", batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=1)
        self.head = nn.Linear(32, 1)
        pos = torch.arange(12, dtype=torch.float32)[:, None]
        div = torch.exp(torch.arange(0, 32, 2) * (-math.log(10000.0) / 32))
        pe = torch.zeros(12, 32)
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("position", pe[None])
        self.pool_score = nn.Linear(32, 1) if learned_pool else None
        if self.pool_score is not None:
            nn.init.zeros_(self.pool_score.weight)
            nn.init.zeros_(self.pool_score.bias)

    def forward(self, x, return_weights=False):
        z = self.encoder(self.embedding(tokenize(x)) + self.position)
        if self.pool_score is None:
            weights = torch.full_like(z[:, :, :1], 1.0 / 12)
        else:
            weights = self.pool_score(z).softmax(dim=1)
        prediction = self.head((z * weights).sum(dim=1))
        return (prediction, weights) if return_weights else prediction


def make_model(name, seed=41):
    torch.manual_seed(seed)
    if name == "mlp32":
        return nn.Sequential(nn.Linear(300, 32), nn.GELU(), nn.Linear(32, 1))
    if name not in ("transformer_mean", "transformer_lag"):
        raise ValueError(name)
    return TinyTransformer(name == "transformer_lag")


def model_counts():
    counts = {name: sum(p.numel() for p in make_model(name).parameters())
              for name in MODELS if name != "ridge"}
    if any(counts[n] >= 20000 for n in counts if n.startswith("transformer")):
        raise ValueError("Transformer parameter ceiling exceeded")
    return counts


def validate_groups(folds):
    seen = []
    for fold in folds:
        train = set(fold["training_order"])
        val = set(fold["validation_people"])
        test = set(fold["test_people"])
        if train & val or train & test or val & test:
            raise ValueError("Person overlap inside fold")
        if len(train) < 12 or len(val) != 4 or len(test) != 9:
            raise ValueError("Unexpected original fold dimensions")
        if any(len(fold[k]) != len(set(fold[k])) for k in
               ("training_order", "validation_people", "test_people")):
            raise ValueError("Duplicated person")
        seen.extend(test)
    if len(folds) != 3 or len(seen) != 27 or len(set(seen)) != 27:
        raise ValueError("Expected all 27 people held out exactly once")


def validate_cache(z, base):
    validate_groups(base["folds"])
    labels = z["labels"].astype(str).tolist()
    if labels.count("global signal clean") != 1:
        raise ValueError("Exact unique global target missing")
    gi = labels.index("global signal clean")
    people = sorted({p for f in base["folds"] for p in f["test_people"]})
    manifest = []
    for person in people:
        run = person + "_EC"
        x, y = z["eeg_" + run], z["y_" + run]
        frames, onsets = z["frame_" + run], z["onset_" + run]
        if x.ndim != 2 or x.shape[1] != 300 or len(x) < 120:
            raise ValueError("Incompatible EEG cache: " + run)
        if y.shape != (len(x), len(labels)) or not np.isfinite(y[:, gi]).all():
            raise ValueError("Invalid global target: " + run)
        if len(frames) != len(x) or len(onsets) != len(x):
            raise ValueError("Frame alignment: " + run)
        if not np.all(np.diff(frames) > 0) or not np.all(np.diff(onsets) > 0):
            raise ValueError("Nonmonotone original frames: " + run)
        manifest.append({"run": run, "n_frames": len(x), "first": int(frames[0]),
                         "last": int(frames[-1]), "gaps": int((np.diff(frames) != 1).sum())})
    fixture = torch.arange(600).reshape(2, 300)
    if not torch.equal(untokenize(tokenize(fixture)), fixture):
        raise ValueError("Token roundtrip failure")
    return gi, manifest


def freeze(args):
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    base = json.loads(args.base_protocol.read_text(encoding="utf-8"))
    if sha(args.cache) != base["feature_sha256"]:
        raise ValueError("Cache hash differs from the existing study protocol")
    expected = {"seed": 41, "mlp_max_epochs": 60, "mlp_patience": 10,
                "mlp_learning_rate": .001, "batch_size": 128}
    if any(base[k] != v for k, v in expected.items()):
        raise ValueError("Original training-budget contract differs")
    for name in ("thesis_study.py", "thesis_data.py"):
        if sha(ROOT / "scripts" / name) != base["source_sha256"][name]:
            raise ValueError("Existing helper changed since original protocol: " + name)
    with np.load(args.cache, allow_pickle=False) as z:
        gi, manifest = validate_cache(z, base)
    counts = model_counts()
    protocol = {
        "study": "architecture_lag_token_ec_global_v1", "created_utc": utc(),
        "scope": "exploratory reused-development-data teaching prototype; NOT a NeuroBOLT modification or fresh confirmation",
        "cache": args.cache.relative_to(ROOT).as_posix(),
        "base_protocol": args.base_protocol.relative_to(ROOT).as_posix(),
        "feature_sha256": sha(args.cache), "base_protocol_sha256": sha(args.base_protocol),
        "source_sha256": {n: sha(ROOT / "scripts" / n) for n in SOURCE_NAMES},
        "folds": base["folds"], "ec_manifest": manifest,
        "training_people": 12, "retained_target_seconds_per_person": 240,
        "training_frame_selection": "first 120 retained EC frames/person, same thesis_study.stack helper; gaps retained",
        "validation_test_selection": "all eligible EC rows for those original person sets; no EO",
        "input": "300 cached log-power values, flatten[group=5,band=5,lag=12]; tokenize N5,5,12 -> N12,25",
        "target": "global signal clean", "global_index": gi,
        "objective": "same scalar MSE on raw cached normalized BOLD for all models; no output z-score or calibration",
        "transforms": "training-only median imputation, feature mean/SD from selected frames; apply unchanged to validation/test",
        "models": list(MODELS), "parameter_counts": counts, "ridge_parameters": 301,
        "ridge_alphas": base["ridge_alphas"], "seed": 41,
        "mlp": "300 -> 32 GELU -> 1",
        "transformer": {"tokens": 12, "input_width": 25, "width": 32, "layers": 1,
                        "heads": 2, "feedforward": 64, "activation": "gelu", "dropout": .1,
                        "position": "fixed sinusoidal", "norm_first": False,
                        "mean_pool": "uniform over lag tokens", "learned_pool": "Linear(32,1) content logits -> softmax over lag -> weighted sum; zero logits at initialization",
                        "comparison": "separately trained from identical encoder/head initialization; not a frozen common encoder"},
        "optimizer": "AdamW", "learning_rate": .001, "weight_decay": .01,
        "batch_size": 128, "max_epochs": 60, "patience": 10, "gradient_clip": 5.,
        "selection": "minimum equal-person inner-validation scalar MSE; improvement tolerance 1e-7; no validation refit",
        "primary": "equal-person mean raw predictive_R2, per-person denominator sum(y - that evaluation run mean)^2",
        "secondary": ["Pearson_r", "RMSE", "SD_ratio", "negative_R2_frequency", "undefined_r_frequency", "training_mean_R2"],
        "contrasts": [["transformer_lag", "transformer_mean"], ["transformer_lag", "ridge"],
                      ["transformer_mean", "ridge"], ["mlp32", "ridge"]],
        "intervals": "2000 paired person bootstrap resamples, seed 20261026; exploratory, no multiplicity correction; shared training sets not fully accounted for",
        "profile_gate": "first fold all four fits use train/validation only; conservative 1.5x extrapolation of three-fold runtime + 120s must fit remaining 80min process budget; otherwise stop CAP_BLOCKED before any outer score",
        "outer_access": "only after all 12 model-fold selections complete; no test-guided retries or scope change",
        "limits": {"gpu_allocations": 1, "wall_minutes": 90, "memory_GB": 32,
                   "cpus": 4, "process_minutes": 80, "gpu_hours_cap": 2, "cpu_hours_cap": 8},
        "limitations": ["previously explored development people and outcomes", "one seed",
                        "engineered spectral features, not raw/STFT NeuroBOLT tokens",
                        "inherited retrospective cleaning/BOLD normalization and future-margin QC",
                        "global target only; no regional specificity, prospective, clinical or external claim"],
    }
    save(out / "protocol.json", protocol, exclusive=True)
    digest = sha(out / "protocol.json")
    (out / "protocol.sha256").write_text(digest + "  protocol.json\n", encoding="utf-8")
    print("FROZEN", digest, json.dumps(counts), flush=True)


class CapBlocked(RuntimeError):
    pass


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise CapBlocked("80-minute process cap reached; no further training/scoring")


def profile_gate(elapsed, remaining, folds=3):
    return 1.5 * elapsed * (folds - 1) + 120 < remaining


def neural_fit(name, x, y, xv, yv, wv, protocol, device, deadline):
    seed = protocol["seed"]
    net = make_model(name, seed).to(device)
    # Pool construction must not change dropout's initial RNG stream.
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    tx, ty = torch.as_tensor(x, device=device), torch.as_tensor(y, device=device)
    vx, vy = torch.as_tensor(xv, device=device), torch.as_tensor(yv, device=device)
    vw = torch.as_tensor(wv, device=device)
    optimizer = torch.optim.AdamW(net.parameters(), lr=protocol["learning_rate"],
                                 weight_decay=protocol["weight_decay"])
    generator = torch.Generator().manual_seed(seed)
    best, best_epoch, state = math.inf, 0, None
    history = []
    started = time.monotonic()
    for epoch in range(1, protocol["max_epochs"] + 1):
        check_time(deadline)
        net.train()
        order = torch.randperm(len(x), generator=generator)
        total = 0.
        for idx in order.split(protocol["batch_size"]):
            check_time(deadline)
            idx = idx.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(net(tx[idx]), ty[idx])
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), protocol["gradient_clip"])
            optimizer.step()
            total += float(loss.detach()) * len(idx)
        net.eval()
        with torch.no_grad():
            val = float((((net(vx) - vy).square().squeeze(1)) * vw).sum())
        if not math.isfinite(val):
            raise ValueError("Nonfinite validation loss")
        history.append({"epoch": epoch, "training_mse": total / len(x), "validation_mse": val})
        if val < best - 1e-7:
            best, best_epoch = val, epoch
            state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}
        if epoch - best_epoch >= protocol["patience"]:
            break
    net.load_state_dict(state)
    net.eval()
    metadata = {"model": name, "best_epoch": best_epoch, "epochs_run": epoch,
                "validation_mse": best, "fit_seconds": time.monotonic() - started,
                "parameters": sum(p.numel() for p in net.parameters()), "history": history}

    def predict(a):
        with torch.no_grad():
            return np.concatenate([net(torch.as_tensor(a[i:i + 1024], device=device)).cpu().numpy()
                                   for i in range(0, len(a), 1024)])

    return predict, metadata, state


def apply_transform(x, transform):
    return ((np.where(np.isfinite(x), x, transform["median"]) - transform["mean"])
            / transform["sd"]).astype("float32")


def metrics(pred, true):
    pred = np.asarray(pred).reshape(-1, 1)
    true = np.asarray(true).reshape(-1, 1)
    sd = float(true.std())
    return {"predictive_R2": float(r2(pred, true)[0]),
            "Pearson_r": float(correlations(pred, true)[0]),
            "RMSE": float(np.sqrt(np.mean((pred - true) ** 2))),
            "SD_ratio": float(pred.std() / sd) if sd > 1e-10 else float("nan")}


def summarize(rows, protocol):
    names = list(MODELS) + ["training_mean"]
    subjects = sorted({r["subject"] for r in rows})
    cells = {(r["model"], r["subject"]): r for r in rows}
    if len(subjects) != 27 or any((m, s) not in cells for m in names for s in subjects):
        raise ValueError("Incomplete outer panel; cannot mark complete")
    rng = np.random.default_rng(20261026)
    boot = rng.integers(len(subjects), size=(2000, len(subjects)))
    result = {"n_people": len(subjects), "models": {}, "paired_contrasts": [],
              "scope": protocol["scope"], "primary": protocol["primary"]}
    for name in names:
        panel = [cells[name, s] for s in subjects]
        entry = {}
        for key in ("predictive_R2", "Pearson_r", "RMSE", "SD_ratio"):
            values = np.array([r[key] for r in panel], dtype=float)
            finite = np.isfinite(values)
            means = np.nanmean(values[boot], axis=1) if finite.any() else np.full(2000, np.nan)
            entry[key] = {"mean": float(np.nanmean(values)) if finite.any() else None,
                          "ci95": np.nanpercentile(means, [2.5, 97.5]).tolist() if finite.any() else [None, None],
                          "defined_people": int(finite.sum())}
        r2s = np.array([r["predictive_R2"] for r in panel])
        entry["negative_R2_count"] = int((r2s < 0).sum())
        entry["negative_R2_frequency"] = float((r2s < 0).sum() / np.isfinite(r2s).sum())
        entry["undefined_r_frequency"] = float(np.mean([not math.isfinite(r["Pearson_r"]) for r in panel]))
        result["models"][name] = entry
    for a, b in protocol["contrasts"]:
        diff = np.array([cells[a, s]["predictive_R2"] - cells[b, s]["predictive_R2"] for s in subjects])
        result["paired_contrasts"].append({"first": a, "second": b, "metric": "raw_predictive_R2",
                                            "mean_difference": float(diff.mean()),
                                            "ci95": np.percentile(diff[boot].mean(1), [2.5, 97.5]).tolist(),
                                            "people_favoring_first": int((diff > 0).sum())})
    return clean_json(result)


def verify_frozen(out):
    protocol_path = out / "protocol.json"
    expected = (out / "protocol.sha256").read_text().split()[0]
    if sha(protocol_path) != expected:
        raise ValueError("Frozen protocol hash mismatch")
    p = json.loads(protocol_path.read_text(encoding="utf-8"))
    for name, digest in p["source_sha256"].items():
        if sha(ROOT / "scripts" / name) != digest:
            raise ValueError("Frozen source hash mismatch: " + name)
    if sha(ROOT / p["cache"]) != p["feature_sha256"]:
        raise ValueError("Feature hash mismatch")
    if sha(ROOT / p["base_protocol"]) != p["base_protocol_sha256"]:
        raise ValueError("Original protocol hash mismatch")
    if model_counts() != p["parameter_counts"]:
        raise ValueError("Parameter-count mismatch")
    return p, expected


def run(args):
    out = args.out
    protocol, protocol_hash = verify_frozen(out)
    if int(os.environ.get("SLURM_CPUS_PER_TASK", "4")) > 4:
        raise ValueError("More than four CPUs would exceed the declared fallback envelope")
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Required by deterministic CUDA matmul on the installed Torch/CUDA versions.
    started = time.monotonic()
    deadline = started + 80 * 60
    save(out / "run_started.json", {"started_utc": utc(), "protocol_sha256": protocol_hash,
                                  "job_id": os.environ.get("SLURM_JOB_ID"), "device": device,
                                  "python": sys.version, "torch": torch.__version__,
                                  "numpy": np.__version__, "platform": platform.platform()}, exclusive=True)
    save(out / "status.json", {"state": "VALIDATING", "outer_scored": False})
    with np.load(ROOT / protocol["cache"], allow_pickle=False) as z:
        validate_cache(z, protocol)
        gi = protocol["global_index"]
        fitted = []
        selections = []
        for fi, fold in enumerate(protocol["folds"]):
            check_time(deadline)
            # Only training and validation arrays are materialized here.
            tr = stack(z, fold["training_order"][:12], "EC", "eeg", 240)
            va = stack(z, fold["validation_people"], "EC", "eeg")
            (x, xv), transform = standardize(tr[0], va[0])
            y, yv = tr[1][:, [gi]].astype("float32"), va[1][:, [gi]].astype("float32")
            if not np.allclose(va[3].sum(), 1):
                raise ValueError("Validation weights must sum to one")
            for name in MODELS:
                check_time(deadline)
                t0 = time.monotonic()
                if name == "ridge":
                    predict, selection = ridge_select(x, y, xv, yv, va[3], protocol["ridge_alphas"])
                    state = None
                else:
                    predict, selection, state = neural_fit(name, x, y, xv, yv, va[3], protocol, device, deadline)
                if device == "cuda":
                    torch.cuda.synchronize()
                selection = {**selection, "fold": fold["fold"], "model": name,
                             "elapsed_seconds": time.monotonic() - t0,
                             "training_rows": tr[4], "validation_rows": va[4]}
                selections.append(selection)
                fitted.append((fold, name, predict, transform, float(y.mean())))
                save(out / "selections.json", selections)
                if state is not None:
                    torch.save(state, out / f"selected_{name}_fold{fold['fold']}.pt")
                print("SELECTED", fold["fold"], name,
                      round(selection["elapsed_seconds"], 3), flush=True)
            if fi == 0:
                elapsed = time.monotonic() - started
                accepted = profile_gate(elapsed, deadline - time.monotonic())
                profile = {"elapsed_seconds": elapsed, "all_four_first_fold_models_fit": True,
                           "outer_scored": False, "full_three_fold_scope_accepted": accepted,
                           "parameter_counts": protocol["parameter_counts"], "device": device,
                           "gpu": torch.cuda.get_device_name() if device == "cuda" else None,
                           "gpu_peak_allocated_MB": torch.cuda.max_memory_allocated() / 2**20 if device == "cuda" else 0}
                save(out / "profile.json", profile)
                print("PROFILE", json.dumps(profile), flush=True)
                if not accepted:
                    raise CapBlocked("Profile cannot support full frozen scope; no outer scoring performed")
        save(out / "status.json", {"state": "ALL_SELECTIONS_COMPLETE", "outer_scored": False,
                                   "model_fold_fits": len(fitted)})
        print("ALL_SELECTIONS_COMPLETE; OUTER_EVALUATION_START", flush=True)
        rows, archive = [], {}
        for fold, name, predict, transform, training_mean in fitted:
            for person in fold["test_people"]:
                check_time(deadline)
                run_name = person + "_EC"
                xx = apply_transform(z["eeg_" + run_name], transform)
                yy = z["y_" + run_name][:, [gi]].astype("float32")
                pp = predict(xx)
                row = {"model": name, "fold": fold["fold"], "subject": person,
                       "condition": "EC", "n_frames": len(yy), **metrics(pp, yy)}
                rows.append(row)
                archive[name + "_" + person] = pp.astype("float32").ravel()
                if name == "ridge":
                    archive["true_" + person] = yy.ravel()
                    archive["frame_" + person] = z["frame_" + run_name]
                    baseline = np.full_like(yy, training_mean)
                    rows.append({"model": "training_mean", "fold": fold["fold"],
                                 "subject": person, "condition": "EC", "n_frames": len(yy),
                                 **metrics(baseline, yy)})
        summary = summarize(rows, protocol)
        summary.update({"protocol_sha256": protocol_hash, "completed_utc": utc(),
                        "elapsed_seconds": time.monotonic() - started,
                        "parameter_counts": protocol["parameter_counts"], "model_fold_fits": len(fitted),
                        "gpu_peak_allocated_MB": torch.cuda.max_memory_allocated() / 2**20 if device == "cuda" else 0})
        write_csv(out / "per_person_scores.csv", rows)
        np.savez_compressed(out / "predictions.npz", **archive)
        save(out / "summary.json", summary)
        save(out / "status.json", {"state": "COMPLETE", "outer_scored": True,
                                   "model_fold_fits": len(fitted), "people": 27,
                                   "protocol_sha256": protocol_hash,
                                   "elapsed_seconds": time.monotonic() - started})
        print("PILOT_COMPLETE", json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT / "reports/thesis_exploration/data/features_causal.npz")
    parser.add_argument("--base-protocol", type=Path, default=ROOT / "reports/thesis_exploration/data/protocol.json")
    args = parser.parse_args()
    args.out = args.out.resolve()
    allowed = (ROOT / "reports/architecture_briefing/pilot").resolve()
    if args.out == allowed or allowed not in args.out.parents:
        raise ValueError("Output must be a new run folder under reports/architecture_briefing/pilot")
    args.cache, args.base_protocol = args.cache.resolve(), args.base_protocol.resolve()
    try:
        freeze(args) if args.command == "freeze" else run(args)
    except Exception as exc:
        if args.out.exists() and args.command == "run":
            save(args.out / "failure.json", {"state": "CAP_BLOCKED" if isinstance(exc, CapBlocked) else "FAILED",
                                            "error": repr(exc), "utc": utc(),
                                            "partial_results_are_not_complete": True})
        raise


if __name__ == "__main__":
    main()
