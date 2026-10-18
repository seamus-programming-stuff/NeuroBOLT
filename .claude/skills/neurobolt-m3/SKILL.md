---
name: neurobolt-m3
description: Run NeuroBOLT experiments on Monash MASSIVE M3 end to end — deploy changed scripts, submit SLURM jobs (GPU NeuroBOLT arms, CPU ridge/analysis jobs), watch the queue and logs, pull results back, rebuild the hypothesis or interpretability reports, republish the artifacts and push to main. Use this whenever the user mentions M3, MASSIVE, sbatch, SLURM, "run it on the cluster", a new hypothesis arm, cross-validation folds, interpretability analyses, or refreshing the NeuroBOLT reports, even if they don't say "M3" explicitly.
---

# NeuroBOLT on M3

The local repo (Windows, Git Bash) is where code is written; M3 is where it runs. The M3 clone at
`/projects/hz18/stay0060/NeuroBOLT` tracks upstream (`soupeeli/NeuroBOLT`), not the fork, so
**code reaches M3 by copying, never by `git pull`**. Results come back by `ssh`/`scp` and are committed
from the local repo to `origin main` (the fork). Never push to `upstream`.

## Connection and layout

- `ssh -o BatchMode=yes m3 '<cmd>'` works non-interactively (key in `~/.ssh/config`). Every remote
  command starts with `cd /projects/hz18/stay0060/NeuroBOLT && source scripts/m3_env.sh >/dev/null && activate_neurobolt >/dev/null 2>&1`
  when it needs Python.
- `scripts/m3_env.sh` defines `$M3_REPO` (code), `$M3_DATA` (EEG + DiFuMo ROI data on scratch), `$M3_OUT`
  (all results: `hypotheses/`, `cv/fold<k>/`, `learning_curve/`, `interp/`, `paper_resting/`), and `$M3_LOG`.
- Local Python is `/c/Users/Seamus/anaconda3/envs/neurobolt/python.exe` (the `neurobolt` conda env).
- Compute nodes have no internet: download checkpoints, atlases (nilearn data lives in
  `$M3_SCRATCH/nilearn_data`) or datasets on the login node first.

## Deploy

Copy only the files you changed, and strip Windows line endings (CRLF breaks bash and sbatch headers):

```bash
tar cf - scripts/foo.py scripts/foo_m3.sbatch | ssh -o BatchMode=yes m3 \
  'cd /projects/hz18/stay0060/NeuroBOLT && tar xf - && sed -i "s/\r$//" scripts/foo.py scripts/foo_m3.sbatch'
```

Core training files (`main.py`, `engine.py`, `utils.py`, `dataset_maker/`, `models/`) are the fork's
versions and go the same way. Run `python -m py_compile` locally before deploying, since a syntax
error only shows up once the job reaches a node.

## Submit

Submit from the repo root on M3 (the sbatch scripts use `$SLURM_SUBMIT_DIR`). Pick the entry point:

| Job | Script | How |
|---|---|---|
| Any analysis script (CPU) | `scripts/interp_m3.sbatch` | `CMD="scripts/x.py --out \$M3_OUT/interp/x ..." sbatch --job-name=nb-x scripts/interp_m3.sbatch` — escape `$` so it expands inside the job |
| Same, on a GPU | `scripts/interp_m3.sbatch` | add `--partition=gpu --gres=gpu:1` |
| NeuroBOLT arm, 7 ROIs × 3 seeds | `scripts/hypotheses_m3.sbatch` | `EXP=<arm> EXTRA="<main.py flags>" sbatch --array=0-20 ...`; a shared 7-output model is `EXP=m7_<name> MULTI=1 --array=0-2` |
| Band-power ridge arm | `scripts/baseline_ridge_m3.sbatch` | `ARM=<name> EXTRA="--bands fine --window-sec 24 --sub-windows 12" sbatch ...` |

Resources that have bitten before:
- **4-GPU QOS cap** per user: extra GPU jobs queue rather than fail, so order them by priority.
- Ridge on the full 13,728-feature set: `--cpus-per-task=16 --mem=96G`. Do the linear algebra in torch
  (`baseline_ridge.ridge_path`): the M3 numpy links single-threaded reference LAPACK.
- NeuroBOLT windows above 24 s need `--mem=64G` and `--batch_size 32 --update_freq 2`.
- Chain dependent jobs with `--dependency=afterok:<jobid>` instead of waiting by hand.
- Scratch (`/fs04`) runs ~94% full: train with `--no_save_ckpt` unless checkpoints are needed, and ask
  before deleting anything there.

## Monitor

```bash
ssh -o BatchMode=yes m3 'squeue -u $USER -o "%.10i %.12j %.8T %.10M %R"'
ssh -o BatchMode=yes m3 'tail -5 /projects/hz18/stay0060/NeuroBOLT/slurm_logs/interp-<job-name>-<jobid>.out'
```

MNE floods logs with epoching messages; grep for the script's own progress lines (`fold`, `mean R`,
`done`) rather than tailing blindly. A job missing from `squeue` has finished or failed: check
`sacct -j <id> -o JobID,State,Elapsed,MaxRSS` and the `.err` file before assuming success.

## Collect and report

- Hypothesis arms: `PY=<local python> bash scripts/refresh_hypotheses_report.sh "<status line>"`, then edit
  `reports/hypotheses/findings.md` by hand and republish the hypothesis page.
- Interpretability: `PY=<local python> bash scripts/refresh_interp_report.sh` copies `$M3_OUT/interp/*`
  results into `reports/interpretability/data/` and rebuilds `tables.md` and the figures.
- Cross-validation summaries: `scripts/summarize_cv.py` on M3.

Report numbers the way the existing reports do: mean R per held-out scan, averaged within person, then
over people, with paired 95% CIs over people for differences. Decide on validation, not on the six
test scans every arm shares.

## Publish and commit

- Write-ups are published as Claude artifacts (the reproduction, hypothesis and interpretability pages);
  republish to the existing URL rather than creating a new one.
- Commit code and small results straight to `main` on `origin` and push; the user pulls on a laptop.
  Keep large raw arrays out of git (`reports/interpretability/data/raw/` is ignored).

## Traps worth remembering

- `--seed` only changes model init since the loaders were fixed; old runs are reproducible only to GPU
  nondeterminism (cudnn.benchmark), so compare arms against a fresh `base`, not old logs.
- Pretrained checkpoints need `use_abs_pos_emb=True, use_rel_pos_bias=False`.
- The EOG/EMG/ECG leads share the EEG reference, so their power in EEG bands partly *is* EEG; use heart
  rate, EOG below 4 Hz and EMG above 30 Hz when a physiology control must be EEG-free.
