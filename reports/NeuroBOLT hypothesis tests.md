# NeuroBOLT hypothesis tests

*Updated 12 Oct 2026, 09:21 AEDT. NeuroBOLT baseline: 12 of 21 runs finished; 8 more NeuroBOLT arms queued. Band-power baselines: 9 of 16 inter-subject variants and 1 of 3 intra-scan variants finished.*

Inter-subject prediction on the authors' split (18 training, 5 validation and 6 held-out scans). NeuroBOLT arms train every ROI with three seeds (12345, 1, 2); band-power baselines are deterministic. Every run is scored at its validation-selected point on the frames all arms share. Test R is averaged over the six held-out scans and, for NeuroBOLT, the seeds.

![Every arm's average test R](hypotheses/arms_overview.png)

| Arm | Seeds | Cuneus | Heschl's | Mid. frontal | Precuneus | Putamen | Thalamus | Global | Avg. test R | Avg. val R | Δ test vs baseline (95% CI) | Δ val |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ridge · 5 bands · 32 s / 16 lags | 1 | 0.523 | 0.572 | 0.462 | 0.527 | 0.352 | 0.455 | 0.556 | 0.493 | 0.344 | +0.026 (+0.000 to +0.052) | +0.025 |
| Ridge · 5 bands · 48 s / 24 lags | 1 | 0.524 | 0.567 | 0.445 | 0.524 | 0.347 | 0.447 | 0.545 | 0.486 | 0.339 | +0.019 (-0.009 to +0.047) | +0.020 |
| Ridge · 5 bands · 32 s / 8 lags | 1 | 0.511 | 0.558 | 0.451 | 0.515 | 0.341 | 0.447 | 0.539 | 0.480 | 0.338 | +0.014 (-0.003 to +0.031) | +0.019 |
| Ridge · 5 bands · 16 s / 4 lags | 1 | 0.470 | 0.536 | 0.445 | 0.506 | 0.327 | 0.456 | 0.546 | 0.469 | 0.337 | +0.003 (-0.015 to +0.021) | +0.018 |
| Ridge · 5 bands · no high-pass | 1 | 0.469 | 0.535 | 0.445 | 0.507 | 0.327 | 0.456 | 0.546 | 0.469 | 0.336 | +0.003 (-0.015 to +0.021) | +0.017 |
| NeuroBOLT (baseline) | 2 | 0.463 | 0.512 | 0.437 | 0.500 | 0.332 | 0.463 | 0.557 | 0.466 | 0.319 | reference |  |
| Ridge · per-scan z · 32 s / 8 lags | 1 | 0.481 | 0.545 | 0.441 | 0.505 | 0.336 | 0.424 | 0.511 | 0.463 | 0.342 | -0.003 (-0.022 to +0.016) | +0.023 |
| Boosted trees · 32 s / 16 lags | 1 | 0.501 | 0.527 | 0.430 | 0.532 | 0.257 | 0.378 | 0.552 | 0.454 | 0.306 | -0.013 (-0.072 to +0.047) | -0.013 |
| Ridge · per-scan z-scored | 1 | 0.450 | 0.517 | 0.434 | 0.477 | 0.312 | 0.451 | 0.498 | 0.448 | 0.337 | -0.018 (-0.041 to +0.004) | +0.018 |
| Boosted trees · 16 s / 4 lags | 1 | 0.442 | 0.507 | 0.376 | 0.472 | 0.176 | 0.383 | 0.527 | 0.412 | 0.282 | -0.055 (-0.127 to +0.018) | -0.037 |
| Ridge · per-scan z · 1 Hz bins | 1 | 0.473 | 0.553 | 0.462 | 0.491 | 0.358 | – | – | – | – | – | – |
| Ridge · 1 Hz bins · 32 s / 8 lags | 1 | 0.528 | – | – | – | – | – | – | – | – | – | – |
| Ridge · 1 Hz bins · 16 s / 4 lags | 1 | 0.503 | 0.572 | 0.475 | 0.536 | – | – | – | – | – | – | – |
| Ridge · 5 bands · 64 s / 32 lags | 1 | 0.525 | 0.575 | 0.447 | 0.530 | 0.350 | 0.440 | – | – | – | – | – |
| Ridge · 5 bands · 32 s / 32 lags | 1 | 0.537 | 0.568 | 0.460 | 0.532 | – | – | – | – | – | – | – |

Δ is paired by ROI and held-out scan; its 95% CI is a t-interval over the six held-out scans. Rows with a dash in any ROI are still running.

## Findings so far

### A linear band-power model matches NeuroBOLT

- Ridge regression on log power in five classic bands, over the same 16 s window NeuroBOLT sees, scores the same as NeuroBOLT's baseline (0.469 against 0.468). It also scores slightly higher on the validation scans.
- So far the transformer's extra capacity buys nothing measurable across people. This is the bar every NeuroBOLT change below has to clear.

### Within a single scan, ridge clearly beats NeuroBOLT

- Ridge on 16 s of band power, trained with NeuroBOLT's exact intra-scan split and scored on the same last 48 frames of each scan, averages 0.493 over the 29 scans and 7 regions. Our NeuroBOLT reproduction averages 0.377 on those frames, and the paper reports 0.531.
- Ridge also fails far less often: 0–7% of its runs score below zero, against 13% for NeuroBOLT. With 453 training windows per scan, the transformer has too little data, and its validation-selected epoch is noisy.

| Intra-scan, 29 scans | Cuneus | Heschl's | Mid. frontal | Precuneus | Putamen | Thalamus | Global | Avg. |
|---|---|---|---|---|---|---|---|---|
| Ridge, 16 s band power | 0.561 | 0.553 | 0.431 | 0.488 | 0.399 | 0.415 | 0.602 | **0.493** |
| NeuroBOLT, our reproduction | 0.480 | 0.420 | 0.290 | 0.401 | 0.253 | 0.273 | 0.521 | 0.377 |
| Paper | 0.588 | 0.566 | 0.502 | 0.559 | 0.437 | 0.480 | 0.587 | 0.531 |

### More EEG history helps, up to about 32 s

- Giving ridge 32 s of history instead of 16 s raises its average test R from 0.469 to 0.480 with 8 lag bins, and to 0.493 with 16 two-second bins. That beats NeuroBOLT's baseline and the paper's 0.473.
- 48 s and 64 s add nothing further, so the useful history matches the slow tail of the haemodynamic response rather than growing without limit.
- NeuroBOLT sees only 16 s. The 24 s NeuroBOLT arm, which stretches its pretrained time embedding, runs next to test whether the network benefits the same way.

### Finer frequency resolution helps

- 1 Hz bins instead of five bands improve ridge in every region finished so far, for example Heschl's gyrus 0.572 against 0.536 at 16 s. The variants that combine 1 Hz bins with 32 s of history are running.

### Ideas that did not help

- **Per-scan normalization of the EEG features** lowers ridge to 0.448. Overall power levels carry information across people, so NeuroBOLT will not get this change.
- **Boosted trees** on the same features score below ridge (0.412 at 16 s, 0.454 at 32 s). A nonlinear map overfits the 13 training people.
- **Dropping the 0.5 Hz EEG high-pass** changes nothing for ridge (0.469 both ways).

