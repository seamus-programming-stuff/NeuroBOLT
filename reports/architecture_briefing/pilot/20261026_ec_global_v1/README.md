# Exploratory lag-token architecture pilot — completed

**Job 61455229 completed, exit 0:0.** All **12 model-by-fold fits** (three ridge selections, nine neural fits) and all **27 outer people** completed in the originally frozen scope. No model retry, scope reduction, post-test search or retraining was performed. This is a scalar EC/global-BOLD development-data prototype on engineered lagged EEG power, **not a published NeuroBOLT reproduction or branch replacement**.

Protocol SHA-256: **`24e4f3af183a31cc336a0ee99f8487ec3ecc669f7cc464c44af81d77dc3fcb74`**. The [protocol](protocol.json) and its [digest](protocol.sha256) were frozen before training. Local/M3 source, parent-protocol and feature-cache hashes matched before submission and again after execution. [Verification](verification.json), [post-run remote hashes](remote_integrity_after.sha256), [download hashes](remote_hashes.sha256).

## Task and fixed comparison

Existing ds006040 300-feature paired cache; **EC only, `global signal clean`**. Original three person-disjoint folds; first 12 training people in the existing order, first 120 retained frames/person (240 retained target-seconds), all eligible EC frames for the four validation and nine test people in each fold. Input imputation/means/SDs use selected training frames only. Gaps retain original frame numbers. Raw cached normalized BOLD is the scalar MSE target for every estimator; there is no output standardization, affine calibration or test-lag tuning.

The cache order is `[group=5, band=5, lag=12]`. Conversion is `N×300 → N×5×5×12 → N×12×25`, checked by semantic values and an inverse roundtrip. Both transformers have width 32, one encoder layer, two heads, feed-forward width 64, GELU, dropout .1 and fixed sinusoidal positions. They start from identical encoder/head weights and train separately. Learned pooling adds a zero-initialized `Linear(32,1)` score and a softmax over lag tokens; its initial prediction equals the mean-pool model.

All neural arms use seed **41**, AdamW LR **.001**, weight decay **.01**, batch **128**, max **60** epochs, patience **10**, gradient clipping **5** and minimum equal-person **inner-validation MSE** selection. Ridge selects from `.1,1,10,100,1000,10000` by the same inner-validation criterion. The first fold profiled training/validation only and accepted the original full scope before outer scoring. **All twelve selections completed before outer prediction.** [Selection record](selections.json), [profile](profile.json), [stdout](slurm-61455229.out).

## Results

Scores below are equal-person means on 27 held-out EC runs, one run/person. Predictive R² uses `1 − SSE / Σ(y − evaluation-run mean(y))²`; the evaluation mean only defines the metric denominator. Its value is not a model input. Intervals are 2,000 paired person-bootstrap resamples, conditional on this exploratory design and its shared training sets, with no multiplicity adjustment.

| Model | Parameters | Raw predictive R² [95% interval] | Pearson r | RMSE | Predicted/observed SD | People with negative R² |
|---|---:|---:|---:|---:|---:|---:|
| Ridge | 301 fitted coefficients/intercept | **.06513 [.03211, .09909]** | .27650 | .49226 | .22267 | 4/27 |
| MLP 300→32→1 | 9,665 | .03845 [−.00288, .08158] | .24065 | .49903 | .30430 | 9/27 |
| Transformer, mean pool | 9,409 | −.03157 [−.06534, .00584] | .10183 | .51709 | .25292 | 20/27 |
| Same transformer, learned lag pool | 9,442 | −.01593 [−.05426, .02472] | .16738 | .51291 | .28779 | 15/27 |
| Training-mean constant | 1 fitted mean | −.00032 [−.00052, −.00016] | undefined | .50929 | 0 | 27/27 |

Primary paired raw-R² differences:

- **Learned minus mean pooling:** +.01564 [−.00109, +.03226], 17/27 people favor learned pooling. The improvement remains uncertain.
- **Learned pooling minus ridge:** −.08105 [−.10522, −.05815], 1/27 favors learned pooling.
- **Mean pooling minus ridge:** −.09670 [−.12060, −.07350], 2/27 favors mean pooling.
- **MLP minus ridge:** −.02668 [−.04632, −.00943], 9/27 favors MLP.

Ridge is the strongest tested estimator in this fixed pilot. Neither transformer demonstrates useful average raw predictive R². These results do not support a claim that learned pooling beats ridge or repairs NeuroBOLT. They also do not establish that attention cannot help under another independently specified representation/protocol. The ridge global score matches the historical cached task, as expected; reused people/data mean this is not fresh independent confirmation. Region-specific recovery, clinical use, online operation and prospective Emotiv access were not evaluated.

## Numerical diagnostic: constant-baseline Pearson correlation

**Preserve `summary.json` and `per_person_scores.csv` as raw frozen-run outputs.** The reused correlation helper centers float32 constant predictions; rounding leaves a tiny nonzero residual in one run. Consequently the raw summary reports **one defined training-mean Pearson r (0)** and `undefined_r_frequency=26/27`, and a tiny nonzero SD ratio. Mathematically a constant prediction has undefined Pearson correlation in **all 27 people**, with **SD ratio zero**. The associated `Mean of empty slice` warning in stderr concerns bootstrap replicates for this constant-baseline diagnostic.

This artifact does **not affect any fitted-model metric or the primary R² results**, including the training-mean R². The explicit post-audit files [summary_verified.json](summary_verified.json) and [per_person_scores_verified.csv](per_person_scores_verified.csv) correct only the constant baseline's correlation/SD reporting. They leave the raw outputs intact and describe the correction. The frozen source, run, protocol and hash are unchanged. No fit was rerun.

## Verification and measured resources

Local compilation and shell syntax checks passed. All **10 synthetic tests passed locally and on M3**. They check semantic token order, inverse layout, person separation, train-only transforms, equal-person validation weights, equal initial encoder/head predictions, gradient flow, parameter ceiling, correlation/error distinctions, ridge algebra, runtime gate and selected-checkpoint validation loss. [Local tests](local_tests.txt), [M3 tests/stderr](slurm-61455229.err).

Independent float64 recomputation from the locally retained `predictions.npz` archive verified **all 108 fitted-model person rows**; maximum raw-R² difference was **2.07×10⁻⁷**, with smaller discrepancies for the other metrics. The archive is intentionally excluded from Git; it remains available locally and on M3. Fold memberships, 120 selected training frames/person, validation epoch minima, aggregate means, negative-R² counts and paired-bootstrap intervals were checked. All collected files match remote digests. [Verification](verification.json).

One **NVIDIA L40S** allocation, four CPUs, 32 GB, 90-minute requested wall cap. Actual SLURM wall time **3m36s**, exit **0:0**, about **.06 allocated GPU-hours** and **.24 allocated CPU-hours**. The validation-only profile took **13.07s**; study process including scoring **18.27s**; peak allocated GPU memory **74.63 MB**; batch MaxRSS **1,015,820 KB**. Package/runtime startup is included in SLURM time, not study-process time. These are measured engineering costs, not acquisition, physiological or clinical latency. [Accounting](sacct.tsv), [profile](profile.json), [environment/start metadata](run_started.json), [completion status](status.json).

Small derived results/logs were collected locally. Task-trained `.pt` files remain on M3; no raw recordings or pretrained weights were downloaded. Original model code/results were not changed or pushed.

M3 directory: `/projects/hz18/stay0060/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/`.

Source note for the presentation: [Code explanation and next hypotheses](../../../../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md).
