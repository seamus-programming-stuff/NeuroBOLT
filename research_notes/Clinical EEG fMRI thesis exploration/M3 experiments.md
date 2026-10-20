# M3 clinical EEG–fMRI thesis exploration

This is an actual, bounded development experiment implementing the empirical proposal on page 10 of `output/pdf/Clinical_EEG_to_fMRI_feasibility.pdf`. VU and ds006040 had already been inspected. This study uses ds006040 as development data, including its EC/EO shift; it reserves no claim of untouched external validation. It does not reproduce old VU physiology/nonlinearity analyses as new evidence.

## Scope and protocol fixed before model outcomes

Only new `scripts/thesis_*` files, `reports/thesis_exploration/data/`, and this note are owned by this work. Existing training code, raw recordings, checkpoints, reports and poster files are read-only. No commit, push, publication, automation, or message to another chat was performed. The local M3 skill was read first. No additional AGENTS.md files were found in the repository or checked ancestor directories. The PDF's last four pages were extracted directly with pypdf; the existing report source and relevant dataset, preprocessing, ridge, external-transfer and interpretability scripts were inspected. No literature/web review was repeated.

The early inventory is `manifest_inventory.json`. The immutable `protocol.json` and `protocol.sha256` are written before the ridge and neural fits and include exact people, subsets, tuning rules, metrics, source hashes and feature hash. The inventory covers **27 people / 54 EC+EO runs** represented in the existing ds006040 cache. It is an inventory of this staged paired cache, not an assertion that the public release contains only 27 people. Other staged raw people without cached paired targets are outside this first bounded experiment.

The intended factorial is 4 versus 12 training people × 120 versus 240 retained target-seconds/person × EEG versus ECG timing/availability versus combined × tuned ridge versus compact MLP. Three disjoint outer folds evaluate each person once; four separate inner validation people per fold select hyperparameters, epochs and affine calibration. Training subsets have one fixed nested order per fold, so these are bounded development comparisons, not a scaling law. Validation people are never refitted into the training set. EC training evaluates the same held-out people's EC and EO frames in every arm. A highest-resource extension uses equal total label budget, 120 s EC + 120 s EO per training person, with the same outer test people. An availability-only control at 12 people/240 s tests whether ECG-derived missingness can explain apparent physiological information.

Before outcomes the coordinator selected the illustrative poster primary: EC-trained/test-EC, 12 training people, 240 retained target-seconds/person, full regional64 temporal r; ridge EEG, ridge ECG timing/availability, ridge combined, and MLP EEG. The learning panel is ridge EEG, EC train/test, full regional64, the full 4/12 × 120/240 grid. Full conditions and metrics are retained regardless of these panels' results.

120/240 seconds means 60/120 retained labels at TR=2 s. Missing-frame gaps mean this need not equal contiguous acquired time. Each selected training run records original first/last frame, gap count, retained seconds, target acquisition span and input acquisition span. Inputs require 24 s of preceding context. Mixed-state label seconds are split equally between EC and EO; those are separate scans, not one contiguous segment. **The duration levels use nested early eligible segments: more retained seconds changes both sample amount and the state/content covered. There are no randomized clip/subset repeats. These are bounded resource/content comparisons, not an isolated information-theoretic sample-count effect.**

## Sensors, features and causal audit

The staged cleaned EEG files contain 63 EEG channels plus a named ECG channel, sampled at 5 kHz and referenced to FCz according to their sidecars. The 26 channels matching the VU montage are used, aggregated to five fixed scalp groups × five fixed bands × twelve 2 s lags = 300 EEG features. A sixth-order one-pass 70 Hz anti-alias low-pass precedes integer decimation to 200 Hz; a one-pass 0.5 Hz high-pass is then applied. Welch spectra use only the strictly preceding 24 s, excluding the endpoint. No whole-test-run input normalization is used. Imputation, means and standard deviations are fitted only on the selected training frames.

Physiology is **ECG beat timing only**, with 12 past-bin mean heart rates and 12 detector-availability fractions. ECG spectral power and EOG EEG-band power are not used as physiology. This avoids directly treating shared-reference EEG-band leakage as independent physiological information, but does not make ECG detection immune to scanner/artifact contamination. The fixed causal detector uses one-pass 5–25 Hz filtering, a past-only adaptive energy threshold, 100 ms peak confirmation, a sequential refractory period and forward-held observed RR intervals, expiring after 3 s. There is no future interpolation/backfill. Missing values are imputed using training-only medians. Detector availability is explicitly controlled and reported. Its beat accuracy is not independently annotated or clinically validated. Across 54 runs the median valid-sample fraction is **0.3918**, range **0.2351–0.7320**. This is a sparse unannotated detector, not a comprehensive test of useful physiology. The detector was kept fixed after QC and predictive results; no threshold was tuned on BOLD accuracy.

Respiration, capnography and independently labelled arousal are not staged in this branch. There is no respiration or CO2 surrogate claim and no arousal prototype. EC/EO is an acquisition condition, not an independent clinical arousal reference. Only ds006040 was staged as an external release; no new release was already available. A new-data branch is deferred under the coordinator's instruction to finish this bounded experiment first; scratch was 96% full (about 161 GB available), and no speculative large download was made.

**Causal input construction does not establish an end-to-end online pipeline.** The authors' gradient/BCG-cleaned EEG was already processed retrospectively; prospective causality of that cleaning is unverified. Existing cached targets use fMRIPrep motion/trend regression, a zero-phase 0.15 Hz low-pass and whole-run demeaning/95th-percentile normalization. The inherited eligible-frame mask also used a future gap margin. New exclusion additionally requires 30 s startup, complete past context, no missing samples in the past 30 s, and no boundary event in that interval. This is retrospective coverage/QC and offline target definition even though the new feature values use past samples only. Output R² and amplitude ratios are in these cached normalized target units, **not absolute patient BOLD calibration**.

## Models, target definitions and selection

Ridge fits each output independently on the 300/24/324-dimensional lagged features. Six penalties (.1, 1, 10, 100, 1,000, 10,000) are selected per output by equal-person inner validation MSE. This is a compact structured lagged baseline, not the old 13,728-dimensional VU ridge rerun.

The compact one-hidden-layer GELU MLP considers widths 32 and 128, AdamW with LR .001 and weight decay .01, batches 128, at most 60 epochs and patience 10. It uses one fixed seed (41). Each outer cell chooses width and epoch on inner validation only. The single fit profile precedes the serial GPU study. No model checkpoint files are written.

Both models predict global BOLD, full 64-region targets, 64 global-adjusted regional targets, and 64 global-plus-physiology-adjusted regional targets. Nuisance coefficients are fitted solely on selected training frames and applied to held-out measured targets. Residual target construction uses held-out measured global BOLD only to define the retrospective outcome; the model never receives held-out BOLD. The physiological nuisance transform is fitted on training input statistics; its fixed ridge penalty is 1 with an unpenalized intercept. These residuals are operational definitions, not a pure neural fraction. Residual definitions match between input/model arms at fixed training people, duration and state; their training-fitted coefficients can change across resource or training-state levels, so residual learning-curve contrasts also change the target definition. Full regional/global targets remain identical.

The MLP jointly predicts 193 standardized outputs, with each of the four target groups receiving weight 1/4, so the one global output does not get 1/193 of the objective. Ridge has independent output fits and raw per-output MSE selection; scaling an individual target would not change its selected ridge penalty. MLP representation sharing, objective, and optimization differ from ridge. A null neural comparison cannot isolate parameter count or prove that nonlinearity/capacity never helps. Both fit exactly the same selected rows and score exactly the same outer frames.

Affine output calibration is fitted on inner validation predictions only. Both raw predictive R² and validation-calibrated R² are reported, along with raw temporal r, normalized-target amplitude ratio, RMSE, best signed/absolute lag in ±10 s, negative-R² and undefined-correlation fractions. Positive lag means the prediction occurs later than the target. Lag matching uses original volume indices and does not bridge missing frames. Boundary optima are descriptive, not a physiological delay estimate.

The global-template control predicts the global trace from the same inputs, then projects through regional coefficients learned on training targets. It never receives measured test global BOLD. Thirty deterministic within-run circular surrogates shift on the **original volume grid**, at least 30 volumes/60 s in either circular direction; only matching available original frame pairs are scored, and matched coverage is recorded. Fixed adjacent atlas-index regional contrasts are secondary; these are convenient reproducibility contrasts, not independently chosen clinical targets. Training-mean R² is retained as an intercept-only control.

## Uncertainty and limits of inference

Scores are computed per target/run, averaged across targets within the named target group, then per person-condition. Each person is an outer test person once. CIs use 2,000 percentile bootstrap resamples of people; differences use the same paired people. This respects temporal dependence more than treating windows as independent observations, but it does not capture every source of uncertainty from overlapping training sets. There is one subset order, one neural seed and only one development site. Intervals are exploratory and not multiplicity-corrected. Undefined correlations and negative R² are counted; missingness cannot silently become a success. Nonsignificance is not equivalence, and neither EC/EO nor a single development site establishes a clinical ceiling, no site penalty, or prospective/live performance.

## Execution evidence (updated through completion below)

Code is copied by scp to `/projects/hz18/stay0060/NeuroBOLT/scripts/`; no git pull is used. Derivatives and SLURM logs are written under the remote repository's `reports/thesis_exploration/data/`, with only small outputs returned locally. Existing raw data at `/scratch/hz18/stay0060/ext/ds006040` and caches at `/scratch/hz18/stay0060/ext/cache` remain intact.

Initial inventory execution on the login node failed only at JSON export because an MNE sample count was a NumPy int64. It inspected metadata, not predictive outcomes. Converting it to a Python int fixed the issue; the successful scheduled audit is retained. A local wildcard py_compile invocation was also corrected to explicit file enumeration on PowerShell. Neither error produced fitted results or motivated outcome-based changes.

Exact scheduled commands, from the remote repository root:

```bash
sbatch --job-name=thesis-audit scripts/thesis_m3.sbatch thesis_data.py audit --out reports/thesis_exploration/data
# 61207131
sbatch --dependency=afterok:61207131 --job-name=thesis-features scripts/thesis_m3.sbatch thesis_data.py build --out reports/thesis_exploration/data
# 61207170
sbatch --dependency=afterok:61207170 --job-name=thesis-freeze scripts/thesis_m3.sbatch thesis_prepare.py --out reports/thesis_exploration/data
# 61207266
sbatch --dependency=afterok:61207266 --job-name=thesis-ridge scripts/thesis_m3.sbatch thesis_study.py --model ridge --out reports/thesis_exploration/data
# 61207267
sbatch --dependency=afterok:61207266 --partition=gpu --gres=gpu:1 --time=00:10:00 --job-name=thesis-profile scripts/thesis_m3.sbatch thesis_study.py --model mlp --profile --out reports/thesis_exploration/data
# 61207268
sbatch --dependency=afterok:61207268 --partition=gpu --gres=gpu:1 --nodelist=m3g103 --time=00:45:00 --job-name=thesis-mlp scripts/thesis_m3.sbatch thesis_study.py --model mlp --out reports/thesis_exploration/data
# 61207409; pending node restriction subsequently cleared with:
scontrol update JobId=61207409 ReqNodeList=
sbatch --dependency=afterok:61207409:61207267 --nodelist=m3e116 --job-name=thesis-summary scripts/thesis_m3.sbatch thesis_summarize.py --out reports/thesis_exploration/data
# 61207416
sbatch --dependency=afterok:61207416 --nodelist=m3e116 --job-name=thesis-verify scripts/thesis_m3.sbatch thesis_verify.py --out reports/thesis_exploration/data
# 61207432
sbatch --dependency=afterok:61207432 --nodelist=m3e116 --job-name=thesis-package scripts/thesis_m3.sbatch thesis_package.py --out reports/thesis_exploration/data
# 61207479
scontrol update JobId=61207416 ReqNodeList=
scontrol update JobId=61207432 ReqNodeList=
scontrol update JobId=61207479 ReqNodeList=
```

The common script requests 4 CPU cores, 12 GB RAM, and 30 minutes on `comp`, overridden to one GPU for neural work. It prints UTC time, job ID, node, arguments and entrypoint SHA256. Ten synthetic tests cover future-sample invariance of filters, ECG timing and windows; train-only imputation/standardization; ridge versus closed-form algebra; correlation versus amplitude/R²; lag and surrogates using original frames with gaps; residual coefficient reuse; and group separation. `thesis_prepare.py` saves package versions, reruns tests and freezes the protocol before fits. A separate local synthetic MLP training/prediction smoke also passed with finite 8×193 output. The freeze was delayed by cold shared-filesystem library imports; inspecting the allocated process showed `cl_sync_io_wait`, not a test result. All ten tests subsequently passed on M3 in 10.892 s, before fitting.

The frozen protocol SHA256 is **59505927a5f9073c0c1fda106baa161576b18e1c58db74838dc28f036050032e**. New feature SHA256 is **d0857caad515135b091a2e23b6609762892feb99d6711ad37f4671141e597863**. Fitting source `thesis_study.py` SHA256 is **b4dcd002ee57cbfb51b773d9802a7b09f911b9e1cda86e3e45d46768b9831447**. Exact frozen hashes for the other analysis scripts are in the protocol. `thesis_package.py` is explicitly a later reporting-only addition: it checks every frozen source hash and adds sensor limitations plus the already-prespecified poster subsets, without changing fitted results, CIs or contrasts.

## Results and completed job evidence

**The bounded factorial completed: 48 ridge cells and 48 MLP cells, with 27 outer test people and 54 EC/EO runs.** Each neural cell evaluated both fixed widths (96 candidate fits, plus the separate one-fit profile). The export contains **10,368 person-condition-target rows, 384 condition summaries and 928 paired contrasts**. These numbers are newly run results, not copied prior VU or external-test scores. `summary.json.complete=true`. The separate archive verification passed all 96 cells, source/protocol hashes, exact training label budgets, person separation and all 42 highest-resource prediction archives. Every archived prediction uses the same original held-out frame array as the new feature cache, and all full target arrays match the cached labels after their explicit reordering.

### Prespecified primary panel

EC training, held-out EC, 12 training people, 240 retained target-seconds/person, full regional64. The denominator is 27 held-out people, each evaluated once. r and R² are means of per-person regional means; CIs resample people. These are raw temporal correlations and predictive R² **in cached normalized target units**.

| Arm | Temporal r [95% person CI] | Predictive R² [95% CI] | Validation-calibrated R² | Predicted/observed target SD |
|---|---:|---:|---:|---:|
| Ridge EEG | **.1886 [.1488, .2265]** | **.02788 [.01163, .04299]** | .02555 | .1615 |
| Ridge ECG timing + availability | .0177 [−.0082, .0438] | −.00441 [−.00747, −.00134] | −.00524 | .0555 |
| Ridge EEG + ECG timing/availability | .1782 [.1388, .2163] | .02309 [.00697, .03817] | .02129 | .1632 |
| Compact MLP EEG | .1223 [.0803, .1647] | .00678 [−.01054, .02380] | .01468 | .1662 |

The paired combined-minus-EEG difference is **Δr −.01037 [−.01623, −.00395]**, ΔR² −.00479 [−.00780, −.00181]. For MLP minus ridge with EEG, **Δr −.06626 [−.09821, −.03607]**, ΔR² −.02110 [−.03100, −.01171]. These estimates describe this feature map, small training budget, fixed detector and finite tuning. They do not establish that richer physiology or larger/nonlinear models cannot help. In particular, the combined ridge uses one selected penalty per output for the joint standardized design; separate physiology-block shrinkage was not an additional tuned dimension. MLP target sharing/objective differences and a single seed also prevent interpreting its loss as pure proof about capacity.

The availability-only ridge control has regional r **.0319** and predictive R² **−.00037**. RR+availability minus availability-only gives **Δr −.01422 [−.03378, .00532]**, ΔR² −.00403 [−.00687, −.00160]. There is no demonstrated added value from this sparse RR representation beyond its availability pattern under this fit. This is not an equivalence result and does not exclude better ECG extraction or independent respiratory/vascular information.

### People × retained-duration panel

Ridge EEG, EC train/test, identical outer people/frames and full regional64:

| Training people | Retained seconds/person | Temporal r [95% person CI] | Predictive R² |
|---:|---:|---:|---:|
| 4 | 120 | .0889 [.0598, .1185] | −.00055 |
| 4 | 240 | .1445 [.1066, .1823] | .00678 |
| 12 | 120 | .1419 [.1112, .1720] | .00710 |
| 12 | 240 | .1886 [.1488, .2265] | .02788 |

At 240 retained seconds/person, 12 versus 4 training people gives **Δr +.04414 [.02367, .06285]**, ΔR² +.02110 [.01191, .02980]. At 12 people, 240 versus 120 retained seconds gives **Δr +.04674 [.02357, .07105]**, ΔR² +.02078 [.01083, .03069]. The other two paired resource contrasts are retained in the summary. The 4-person/240-second and 12-person/120-second point estimates are similar; this design does not establish interchangeability or an optimal acquisition allocation.

The actual EC target acquisition spans are approximately **120–210 s** for 120 retained seconds, and **240–330 s** for 240 retained seconds. Corresponding input spans are **142–232 s** and **262–352 s**, from the first window's start to the last window's endpoint. For example sub-008 EC needs a 330 s target acquisition span for 240 retained seconds because of an internal gap. Thus nominal retained time, actual acquisition coverage and extra input history are explicitly different quantities. Longer early segments also contain different state/content, as noted above.

### EC/EO development shift and balanced-state extension

For EC-trained, 12-person/240-second ridge EEG, regional r falls from **.1886 (EC) to .1190 (EO)**. The paired EO-minus-EC difference is **−.06962 [−.12128, −.02004]**; ΔR² is −.02810 [−.04613, −.01005]. EO predictive R² is approximately **−.00022**, and validation-calibrated R² approximately **−.00542**. This is a within-site acquisition-condition shift in development people, not a new-site estimate.

At the same total retained training-label budget, 120 s EC + 120 s EO improves ridge EEG on held-out EO by **Δr +.02221 [.00518, .04054]** and ΔR² +.01326 [.00634, .02013] relative to 240 s EC-only training. That gives EO r approximately **.1412** and R² **.0130**. It supports including relevant states in this bounded development setting. It does not establish complete invariance, clinical arousal recognition, or absence of a site penalty. Both EC and EO outcomes, including MLP/physiology arms, remain in the full export.

### Regional specificity, amplitude, lag and failures

For the highest-resource EC ridge EEG arm:

| Target/control | Temporal r [95% person CI] | Predictive R² | Validation-calibrated R² |
|---|---:|---:|---:|
| Global | .2765 [.2174, .3309] | .06513 | .06595 |
| Full regional64 | .1886 [.1488, .2265] | .02788 | .02555 |
| Predicted-global template regional64 | .1845 [.1409, .2267] | .02943 | .03159 |
| Training-defined global residual64 | .0905 [.0695, .1086] | −.00047 | −.00366 |
| Training-defined global+physiology residual64 | .0891 [.0677, .1063] | −.00055 | −.00278 |
| Fixed regional contrasts32 | .0872 [.0623, .1078] | −.00789 | −.01251 |

Full-regional minus predicted-global-template Δr is **+.00410 [−.00813, .01680]** and ΔR² **−.00155 [−.00850, .00411]**. The result does not establish added regional fidelity beyond this template. The positive residual/contrast correlations coexist with approximately zero or negative predictive R². They are not evidence of dependable patient-specific regional synthesis or a pure neural signal fraction. The intercept-only training-mean regional R² is −.00042.

The ridge EEG regional amplitude ratio is **.1615 [.1429, .1811]** in normalized target units: trajectories have much smaller variance than measured targets despite positive r. The mean absolute best lag is **3.225 s [2.697, 3.846]**, with signed mean +.498 s [−.263, 1.255]. The primary r/R² were evaluated without posthoc time shifting; lag is an offline diagnostic, not a test-tuned correction or a validated physiological delay. The regional circular-shift control mean r is **.00146 [−.00399, .00608]**, with mean original-frame matched fraction .98825. These surrogate summaries supplement the person-based comparisons and do not turn windows into independent samples.

Among 27 EC test people, mean regional predictive R² is negative for **5 ridge EEG**, **7 ridge combined**, **20 ridge ECG**, and **14 MLP EEG** people. For ridge EEG the five are sub-007 (−.01346), sub-014 (−.01341), sub-018 (−.03404), sub-024 (−.00196), and sub-025 (−.07273). Under EO, **15/27** ridge EEG people have negative mean regional R²; sub-004 and sub-023 also have negative regional mean r. Across individual person-region pairs in the EC panel, negative-R² fractions are **28.5% ridge EEG**, **30.3% ridge combined**, **56.0% ridge ECG**, and **50.1% MLP EEG**. The primary arms have no undefined regional correlation values. These are predictive-error failures relative to their metric baseline, not a clinical failure adjudication. All individual scores remain available rather than restricting the export to successes.

### Runtime, storage and reproducibility

The one-fit neural profile used **16,769 parameters**, width 32, 11 epochs run / best validation epoch 1, **22.953 s fit time**, **27.666 s inside the profile cell**, and **70.214 MB peak allocated VRAM** on an NVIDIA L40S. Its SLURM wall time includes cold imports. In the full neural study, width 32 was selected for **33/48** cells and width 128 for **15/48**; best validation epochs range **1–23**. No test score chose these settings. The full neural cell times sum to **97.537 s**, ridge cell times to **123.115 s**; these include metric/export work inside each cell and exclude process startup. Peak in-process fit RSS was **656.742 MB** and peak allocated VRAM **73.853 MB**. SLURM accounting below is the source for allocation wall times and batch peak RSS, which differ from library counters.

Feature extraction completed in **3m52s** with a batch MaxRSS of **12,583,404 K** against a 12 GB request, essentially at the requested limit. It succeeded without data loss, but a future larger raw extraction should request more memory. The new feature archive is approximately **3.6 MB**. Existing `.set/.fdt`, fMRI and old caches/checkpoints were preserved; only derived feature/prediction/metric files were added. Small results, manifests, hashes, test evidence, cell metadata and logs are returned locally; prediction archives can remain on M3. No checkpoints were written.

Both GPU jobs used one GPU at a time. The full MLP job finished in **1m48s**, and ridge in **2m17s**, both `COMPLETED`, exit `0:0`; no fitted arm failed or required an outcome-driven rerun. Initial inventory serialization, cold-import waits, and queue/node-affinity delays are recorded above. Frozen protocol and fit source hashes remained unchanged. Final machine-readable job accounting is saved as `sacct.tsv` and `job_evidence.json` alongside the outputs.

Final `sacct` pull: all nine root jobs and their batch steps are **COMPLETED / 0:0**. Timestamps in the saved accounting use `TZ=UTC`; the work ran on 21 October 2026 AEDT. Queue wait is not included in the elapsed times below.

| Job ID | Work | Elapsed | Batch MaxRSS (K) |
|---|---|---:|---:|
| 61207131 | Metadata inventory | 1m47s | 1,990,460 |
| 61207170 | New causal feature cache | 3m52s | 12,583,404 |
| 61207266 | Environment, synthetic checks, protocol freeze | 3m59s | 886,296 |
| 61207267 | All 48 ridge conditions | 2m17s | 415,444 |
| 61207268 | One neural fit profile | 3m33s | 918,364 |
| 61207409 | All 48 neural conditions / 96 candidate fits | 1m48s | 583,536 |
| 61207416 | All summaries and paired person CIs | 1m22s | 265,604 |
| 61207432 | Full cell/archive/frame/source integrity checks | 1m58s | 799,600 |
| 61207479 | Prespecified poster package and source checks | 3s | 58,256 |

### Exports and immediate interpretation

`summary.json` contains every condition, person CI, paired contrast, selection/calibration role, target units, scope and resource metadata. `per_person_scores.csv` contains the 10,368 individual rows. `training_frame_manifest.csv` supplies retained time and actual spans; `feature_qc.json` supplies all sensor/exclusion counts. `protocol.json`, `protocol.sha256`, `environment.json`, `synthetic_tests.txt`, per-cell JSON/CSV files, SLURM logs and verification JSONs support reproduction. `poster_scores.csv` and `poster_learning.csv` are reporting-only exports of the exact prespecified four-row panels, with the columns expected by the parent's poster builder. Their creation adds no outcome-based arm selection.

All of those small artifacts, the 3.6 MB new feature cache, all 96 cell JSON/CSV pairs, final logs and accounting have been pulled to the local `reports/thesis_exploration/data/`. `artifact_hashes.sha256` records the returned artifacts' byte hashes. The 42 highest-resource prediction archives remain under the matching M3 `data/predictions/` folder; they are small derived audit arrays, not model checkpoints. Their contents were checked by the completed verifier. No original recording/cache/checkpoint was deleted or overwritten, and no study job remains queued or running.

Files added by this assignment:

- `scripts/thesis_data.py` — inventory, causal features, immutable protocol.
- `scripts/thesis_study.py` — fixed grouped ridge/MLP factorial and metrics.
- `scripts/thesis_tests.py` — ten synthetic/data-pipeline tests.
- `scripts/thesis_prepare.py` — M3 environment/checks/freeze entrypoint.
- `scripts/thesis_summarize.py` — person scores, all CIs and paired contrasts.
- `scripts/thesis_verify.py` — completed-cell/source/frame/archive checks.
- `scripts/thesis_package.py` — reporting-only prespecified poster exports.
- `scripts/thesis_m3.sbatch` — bounded CPU/one-GPU runner.
- New results under `reports/thesis_exploration/data/`, as enumerated above.
- This note, `research_notes/Clinical EEG fMRI thesis exploration/M3 experiments.md`.

The parent independently recomputed the four primary means and selected learning/template contrasts from the returned CSV/JSON and confirmed their values. Report/poster integration is left to the parent. Existing model/training scripts and report/poster files were not edited; there was no git commit/push or automation creation.

The useful new finding is a controlled resource/content gain coupled with a measurable EC/EO development shift; a matched-budget mixed-state arm recovers part of the EO loss. The small MLP and this sparse ECG-timing representation do not improve the prespecified primary result. Regional residual/contrast error and small predicted amplitudes remain material limits. This motivates better synchronized independent sensors, stronger causal cleaning/alignment checks and a genuinely reserved new-person/site test; it does not justify a biological ceiling, an arousal claim, or patient fMRI replacement.

The separate reproducibility audit now identifies a **127 MB NATVIEW sub-01/ses-01 alignment pilot** and explicitly reserves the other proposed participants before their outcomes. That pilot has montage gaps, 280 cleaned EEG markers versus 288 volumes, and a malformed released small Schaefer table requiring original-volume re-extraction. Its acquisition/inspection and common-montage work are being coordinated separately; **no NATVIEW predictive result is mixed into this factorial or presented as a completed untouched external test here**. The audit file `reproducibility and datasets.md` supplies the exact manifest and provenance; this work did not repeat its web review or duplicate its dataset jobs.
