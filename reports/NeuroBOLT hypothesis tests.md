# NeuroBOLT hypothesis tests

*Updated 12 Oct 2026, 11:46 AEDT. Running: NeuroBOLT 24 s window (seed 12345 done) and intra-scan transfer runs. Queued: one shared 7-region model, 32 s window, then 6 more NeuroBOLT arms (about 17 GPU-hours). Band-power baselines: 16 of 18 inter-subject variants finished.*

Inter-subject prediction on the authors' split (18 training, 5 validation and 6 held-out scans). NeuroBOLT arms train every ROI with three seeds (12345, 1, 2); band-power baselines are deterministic. Every run is scored at its validation-selected point on the frames all arms share. Test R is averaged over the six held-out scans and, for NeuroBOLT, the seeds.

![Every arm's average test R](hypotheses/arms_overview.png)

| Arm | Seeds | Cuneus | Heschl's | Mid. frontal | Precuneus | Putamen | Thalamus | Global | Avg. test R | Avg. val R | Δ test vs baseline (95% CI) | Δ val |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ridge · 1 Hz bins · 32 s / 16 lags | 1 | 0.538 | 0.609 | 0.498 | 0.567 | 0.395 | 0.472 | 0.597 | 0.525 | 0.371 | +0.059 (+0.023 to +0.095) | +0.046 |
| Ridge · 1 Hz bins · 32 s / 8 lags | 1 | 0.528 | 0.602 | 0.493 | 0.559 | 0.390 | 0.451 | 0.587 | 0.516 | 0.365 | +0.049 (+0.018 to +0.081) | +0.040 |
| Ridge · 1 Hz bins · 16 s / 4 lags | 1 | 0.503 | 0.572 | 0.475 | 0.536 | 0.373 | 0.450 | 0.570 | 0.497 | 0.374 | +0.031 (+0.020 to +0.041) | +0.049 |
| Ridge · 5 bands · 32 s / 32 lags | 1 | 0.537 | 0.568 | 0.460 | 0.532 | 0.350 | 0.458 | 0.557 | 0.495 | 0.316 | +0.028 (-0.006 to +0.062) | -0.009 |
| Ridge · 5 bands · 32 s / 16 lags | 1 | 0.523 | 0.572 | 0.462 | 0.527 | 0.352 | 0.455 | 0.556 | 0.493 | 0.344 | +0.026 (+0.001 to +0.052) | +0.019 |
| Ridge · 5 bands · 64 s / 32 lags | 1 | 0.525 | 0.575 | 0.447 | 0.530 | 0.350 | 0.440 | 0.552 | 0.488 | 0.338 | +0.022 (-0.008 to +0.052) | +0.013 |
| Ridge · 5 bands · 48 s / 24 lags | 1 | 0.524 | 0.567 | 0.445 | 0.524 | 0.347 | 0.447 | 0.545 | 0.486 | 0.339 | +0.019 (-0.008 to +0.047) | +0.014 |
| NeuroBOLT · 24 s window | 2 | 0.486 | 0.518 | 0.451 | 0.526 | 0.364 | 0.446 | 0.583 | 0.482 | 0.344 | +0.016 (+0.000 to +0.032) | +0.019 |
| Ridge · 5 bands · 32 s / 8 lags | 1 | 0.511 | 0.558 | 0.451 | 0.515 | 0.341 | 0.447 | 0.539 | 0.480 | 0.338 | +0.014 (-0.002 to +0.031) | +0.013 |
| Ridge · per-scan z · 1 Hz bins | 1 | 0.473 | 0.553 | 0.462 | 0.491 | 0.358 | 0.451 | 0.533 | 0.474 | 0.379 | +0.008 (-0.008 to +0.024) | +0.054 |
| Ridge · 5 bands · 16 s / 4 lags | 1 | 0.470 | 0.536 | 0.445 | 0.506 | 0.327 | 0.456 | 0.546 | 0.469 | 0.337 | +0.003 (-0.016 to +0.022) | +0.012 |
| Ridge · 5 bands · no high-pass | 1 | 0.469 | 0.535 | 0.445 | 0.507 | 0.327 | 0.456 | 0.546 | 0.469 | 0.336 | +0.003 (-0.015 to +0.022) | +0.011 |
| NeuroBOLT (baseline) | 3 | 0.468 | 0.520 | 0.436 | 0.502 | 0.327 | 0.460 | 0.551 | 0.466 | 0.325 | reference |  |
| Ridge · per-scan z · 32 s / 8 lags | 1 | 0.481 | 0.545 | 0.441 | 0.505 | 0.336 | 0.424 | 0.511 | 0.463 | 0.342 | -0.003 (-0.021 to +0.016) | +0.017 |
| Boosted trees · 32 s / 16 lags | 1 | 0.501 | 0.527 | 0.430 | 0.532 | 0.257 | 0.378 | 0.552 | 0.454 | 0.306 | -0.012 (-0.073 to +0.048) | -0.019 |
| Ridge · per-scan z-scored | 1 | 0.450 | 0.517 | 0.434 | 0.477 | 0.312 | 0.451 | 0.498 | 0.448 | 0.337 | -0.018 (-0.041 to +0.005) | +0.012 |
| Boosted trees · 16 s / 4 lags | 1 | 0.442 | 0.507 | 0.376 | 0.472 | 0.176 | 0.383 | 0.527 | 0.412 | 0.282 | -0.054 (-0.128 to +0.019) | -0.043 |

Δ is paired by ROI and held-out scan; its 95% CI is a t-interval over the six held-out scans. Rows with a dash in any ROI are still running.

## Findings so far

### The best predictor so far is linear

- Ridge regression on log EEG power in 1 Hz bins (1–45 Hz), over 32 s of history in sixteen 2 s lag bins, scores 0.525 on the held-out scans and 0.371 on validation. NeuroBOLT scores 0.466 (0.475 when its three seeds are averaged), and the paper reports 0.473.
- The gain comes from two things NeuroBOLT does not exploit across people. 1 Hz bins alone take ridge from 0.469 to 0.497, and 32 s of history alone takes it to 0.493. Going to 48 s or 64 s adds nothing (0.486 and 0.488), so the useful history matches the slow tail of the haemodynamic response.
- With the same 16 s window and five classic bands, ridge already matches NeuroBOLT (0.469 against 0.466 on test, 0.337 against 0.335 on validation). The transformer's extra capacity buys nothing measurable across people.

### NeuroBOLT gains from a longer window (early result)

- With seed 12345 complete, the 24 s window (pretrained time embedding stretched from 16 to 24 slots) scores 0.478 against the baseline's 0.466, and gains 0.026 on validation. It is the first NeuroBOLT change that helps, matching what history does for ridge. Seeds 1 and 2 are running, and a 32 s NeuroBOLT arm is queued next.

### Ensembles: NeuroBOLT adds little to the best ridge

| Predictions averaged (z-scored per scan) | Validation R | Test R |
|---|---|---|
| NeuroBOLT, 3 seeds | 0.335 | 0.475 |
| Ridge, 1 Hz bins, 32 s / 16 lags | 0.371 | **0.525** |
| NeuroBOLT + that ridge | **0.381** | 0.524 |
| NeuroBOLT + ridge 1 Hz 16 s + ridge 5 bands 32 s | **0.381** | 0.514 |

- Averaging NeuroBOLT with weaker ridge models helps both, so their errors are partly independent. With the strongest ridge, NeuroBOLT still nudges validation up by 0.010 but leaves the held-out scans unchanged.

### Within a single scan, ridge clearly beats NeuroBOLT

- Ridge on 16 s of band power, trained with NeuroBOLT's exact intra-scan split and scored on the same last 48 frames of each scan, averages 0.493 over the 29 scans and 7 regions, and 0.505 with 1 Hz bins. Our NeuroBOLT reproduction averages 0.377 on those frames, and the paper reports 0.531.
- Ridge also fails far less often: 0–7% of its runs score below zero, against 13% for NeuroBOLT. With 453 training windows per scan, the transformer has too little data, and its validation-selected epoch is noisy.
- On the six inter-subject test scans, the cross-subject NeuroBOLT with no fine-tuning (0.579) already beats NeuroBOLT trained on each person's own scan (0.532), while ridge reaches 0.662. Runs starting intra-scan training from the cross-subject model are finishing now.

| Intra-scan, 29 scans | Cuneus | Heschl's | Mid. frontal | Precuneus | Putamen | Thalamus | Global | Avg. |
|---|---|---|---|---|---|---|---|---|
| Ridge, 1 Hz bins, 16 s | 0.602 | 0.580 | 0.427 | 0.492 | 0.388 | 0.428 | 0.619 | **0.505** |
| Ridge, 5 bands, 16 s | 0.561 | 0.553 | 0.431 | 0.488 | 0.399 | 0.415 | 0.602 | 0.493 |
| NeuroBOLT, our reproduction | 0.480 | 0.420 | 0.290 | 0.401 | 0.253 | 0.273 | 0.521 | 0.377 |
| Paper | 0.588 | 0.566 | 0.502 | 0.559 | 0.437 | 0.480 | 0.587 | 0.531 |

### Ideas that did not help

- **Per-scan normalization of the EEG features** lowers ridge from 0.469 to 0.448 with five bands, and from 0.497 to 0.474 with 1 Hz bins. Overall power levels carry information across people, so NeuroBOLT will not get this change.
- **Boosted trees** on the same features score below ridge (0.412 at 16 s, 0.454 at 32 s). A nonlinear map overfits the 13 training people.
- **Dropping the 0.5 Hz EEG high-pass** changes nothing for ridge (0.469 both ways).
- **Averaging NeuroBOLT's three seeds** adds only 0.009 (0.466 to 0.475), so seed noise is not what holds it back.

