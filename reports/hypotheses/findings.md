### The best predictor so far is linear

- Ridge regression on log EEG power in 1 Hz bins (1–45 Hz), over 32 s of history in sixteen 2 s lag bins, scores 0.525 on the held-out scans and 0.371 on validation. NeuroBOLT scores 0.466 (0.475 when its three seeds are averaged), and the paper reports 0.473.
- The gain comes from two things NeuroBOLT does not exploit across people. 1 Hz bins alone take ridge from 0.469 to 0.497, and 32 s of history alone takes it to 0.493. Going to 48 s or 64 s adds nothing (0.486 and 0.488), so the useful history matches the slow tail of the haemodynamic response.
- With the same 16 s window and five classic bands, ridge already matches NeuroBOLT (0.469 against 0.466 on test, 0.337 against 0.335 on validation). The transformer's extra capacity buys nothing measurable across people.

### For NeuroBOLT, only the window length matters

- A 24 s window (pretrained time embedding stretched from 16 to 24 slots) raises per-region NeuroBOLT from 0.466 to 0.481 on the held-out scans and from 0.325 to 0.338 on validation, with all three seeds better. The 95% interval over the six held-out scans runs from −0.004 to +0.034.
- One shared model with seven outputs scores 0.462, against 0.466 for seven separate models, at a seventh of the training cost. The changes below therefore ran on the shared model and are compared with it.
- Shortening the window to 8 s costs 0.10, and lengthening it to 24 s gains 0.019, so EEG history is the one setting that matters. Six other changes move the score by 0.009 or less in either direction. Log-compressing the spectral branch's input, the change that band-power ridge suggested, hurts on the held-out scans.
- Unlike ridge, NeuroBOLT does not keep improving with more history. A 32 s window drops the shared model to 0.447, below even the 16 s baseline, and the per-region 32 s runs that finished trail their 24 s counterparts. Stretching LaBraM's 16 pretrained time slots twofold may distort them, and 833 tokens per window is a lot to fit from 13 people. The per-region 32 s arm was stopped there, and 20 s and 28 s windows are running to pin down the optimum.
- Dropping the high-pass on top of the 24 s window adds nothing (0.481 either way).

| Shared 7-region NeuroBOLT, 3 seeds | Δ test R | Δ validation R | Seeds better (test) |
|---|---|---|---|
| 20 s window | +0.006 | +0.010 | 2 of 3 |
| 24 s window | **+0.019** | +0.009 | 3 of 3 |
| 24 s window, no EEG high-pass | +0.018 | +0.004 | 3 of 3 |
| 28 s window | +0.018 | −0.028 | 3 of 3 |
| 32 s window | −0.016 | −0.022 | 1 of 3 |
| No EEG high-pass | +0.009 | −0.002 | 3 of 3 |
| AdamW β₂ 0.99 (paper's Table 5) | +0.002 | +0.000 | 2 of 3 |
| No window baseline correction | +0.000 | +0.000 | 3 of 3 |
| Learned scale weights | −0.000 | −0.001 | 1 of 3 |
| Learning rate 1e-4 | −0.002 | +0.008 | 1 of 3 |
| Log-compressed spectra | −0.021 | +0.006 | 0 of 3 |
| 8 s window | **−0.100** | −0.088 | 0 of 3 |

- The window optimum is 24 s: 20 s gains less, and 28 s matches 24 s on the held-out scans but loses 0.028 on validation.
- Stronger regularization on top of the 24 s model does not help either. Weight decay 0.5 gives 0.485 on the held-out scans (+0.004) but 0.012 less on validation, and dropout and drop-path of 0.3 give 0.477. The models still peak within the first five epochs.

### All of NeuroBOLT's skill comes from its spectral branch

- With the LaBraM temporal branch removed, the shared model scores 0.461, the same as the full model (0.462). With only the temporal branch it scores 0.024: it never learns at all, and its training correlation stays at 0.00 for every epoch. Training from scratch, without LaBraM's pretrained weights, also changes nothing (0.464).
- The LaBraM branch's pooled embedding barely varies between windows. In the authors' trained Thalamus model it varies by only 2% of its size, against 91% for the spectral branch, because averaging 416 tokens and applying LayerNorm leaves an almost constant vector.
- Scale is not the whole story, though. A BatchNorm that rescales that embedding before the branches are added changes nothing: the LaBraM branch alone still never learns (0.022), and the full model is unchanged (0.462). Ridge on the trained model's LaBraM features does predict the thalamus within one scan (R = 0.42), but that most likely tracks slow drift within the scan rather than an EEG–BOLD relation that holds across people.
- The branch can learn, just not under the paper's recipe. Its layer-wise learning-rate decay leaves the pretrained blocks almost frozen, and their pretrained features do not predict BOLD across people. Without the decay the LaBraM branch alone reaches 0.177, and from random initialization 0.160 (0.167 with BatchNorm). It overfits quickly (training correlation 0.58 against 0.16 on validation) and stays far below the spectral branch's 0.461.
- Freeing the LaBraM branch inside the full model adds nothing (0.465 without the layer-wise decay, against 0.462). And the spectral branch alone at the best 24 s window nearly matches the full 24 s model (0.478 against 0.481), so NeuroBOLT could drop its LaBraM transformer and lose almost nothing.

| Shared 7-region NeuroBOLT, 3 seeds | Test R | Δ test R | Δ validation R |
|---|---|---|---|
| Both branches (shared baseline) | 0.462 | | |
| Spectral branch only | 0.461 | −0.001 | −0.001 |
| No LaBraM pretraining | 0.464 | +0.002 | −0.012 |
| No layer-wise LR decay | 0.465 | +0.002 | −0.002 |
| BatchNorm on the LaBraM embedding | 0.462 | +0.000 | +0.000 |
| Spectral branch only, 24 s window | 0.478 | +0.016 | −0.002 |
| Both branches, 24 s window | 0.481 | +0.019 | +0.009 |
| **LaBraM temporal branch only** | **0.024** | **−0.438** | **−0.302** |
| LaBraM branch only, with BatchNorm | 0.022 | −0.440 | −0.320 |
| LaBraM branch only, no layer-wise LR decay | 0.177 | −0.286 | −0.237 |
| LaBraM branch only, random initialization | 0.160 | −0.303 | −0.280 |

### More people help

- Refitting the best ridge on the training and validation scans together (17 people instead of 13), with the penalty still chosen on validation, raises it from 0.525 to 0.537 on the held-out scans. With 13 training people, data is a real limit.
- NeuroBOLT does not gain the same way. Trained on the validation scans too and stopped at the epoch its training-only runs chose, the shared model moves from 0.455 to 0.460 at 16 s and from 0.480 to 0.473 at 24 s, against training-only runs scored at the same fixed epoch. Its limit is not only the number of people.

### What the best ridge model uses

![Ridge weights by frequency and time before the BOLD frame, one map per region](hypotheses/ridge_weights.png)

- For the cuneus, Heschl's gyrus, thalamus and global signal, more alpha (8–13 Hz) and beta (15–25 Hz) power 5–12 s before a frame predicts lower BOLD. This is the long-established inverse coupling between alpha power and BOLD, delayed by the haemodynamic response, so the best model has rediscovered known physiology rather than an artefact.
- Power in the last few seconds before the frame often carries the opposite sign, so the model partly reads changes in power rather than levels. Neighbouring features are strongly correlated, so single cells should not be over-read; the broad bands of colour are the robust part.
- The middle frontal gyrus, precuneus and putamen maps are weaker and less structured.

### No model recovers individual connectivity

- For each held-out scan, the 7 × 7 connectivity of the predicted time courses was compared with the true connectivity (correlation over the 21 region pairs). The population average, taken from the five validation scans, already matches each held-out scan at 0.625. No model beats it: ridge reaches 0.61–0.65, and NeuroBOLT 0.60–0.61 with separate models per region.
- The shared NeuroBOLT models inflate connectivity, because their outputs come from one encoder and move together. That drops the 16 s shared model to 0.497, and roughly doubles the mean absolute error (0.29 against 0.15).
- So the predictions follow each region's own fluctuations, but say nothing about a person's networks beyond the population average. Six scans and 21 pairs make this noisy, but it argues against claiming individual connectivity from these models.

| Connectivity on 6 held-out scans | Similarity (r) | Mean absolute error |
|---|---|---|
| Population average (validation scans) | 0.625 ± 0.071 | 0.151 |
| Ridge, 5 bands, 16 s | 0.650 ± 0.213 | 0.168 |
| Ridge, 1 Hz bins, 24 s / 12 lags | 0.614 ± 0.153 | 0.169 |
| NeuroBOLT, per region | 0.607 ± 0.217 | 0.148 |
| NeuroBOLT, per region, 24 s | 0.597 ± 0.146 | 0.137 |
| NeuroBOLT, shared model, 24 s | 0.602 ± 0.175 | 0.229 |
| NeuroBOLT, shared model | 0.497 ± 0.202 | 0.293 |

### Ensembles: NeuroBOLT adds little to the best ridge

| Predictions averaged (z-scored per scan) | Validation R | Test R |
|---|---|---|
| NeuroBOLT, 3 seeds | 0.335 | 0.475 |
| Ridge, 1 Hz bins, 32 s / 16 lags | 0.371 | **0.525** |
| NeuroBOLT + that ridge | **0.381** | 0.524 |
| NeuroBOLT + ridge 1 Hz 16 s + ridge 5 bands 32 s | **0.381** | 0.514 |

- Averaging NeuroBOLT with weaker ridge models helps both, so their errors are partly independent. With the strongest ridge, NeuroBOLT still nudges validation up by 0.010 but leaves the held-out scans unchanged.
- The same holds for NeuroBOLT's best version. Its 24 s window with three seeds averaged reaches 0.490 on the held-out scans and 0.348 on validation. Averaged with ridge on 1 Hz bins over 24 s (0.525 and 0.385), it gives 0.524 and 0.389: no gain on the held-out scans.

### Within a single scan, ridge clearly beats NeuroBOLT

- Ridge on 16 s of band power, trained with NeuroBOLT's exact intra-scan split and scored on the same last 48 frames of each scan, averages 0.493 over the 29 scans and 7 regions, and 0.505 with 1 Hz bins. Our NeuroBOLT reproduction averages 0.377 on those frames, and the paper reports 0.531.
- Ridge also fails far less often: 0–7% of its runs score below zero, against 13% for NeuroBOLT. With 453 training windows per scan, the transformer has too little data, and its validation-selected epoch is noisy.

| Intra-scan, 29 scans | Cuneus | Heschl's | Mid. frontal | Precuneus | Putamen | Thalamus | Global | Avg. |
|---|---|---|---|---|---|---|---|---|
| Ridge, 1 Hz bins, 16 s | 0.602 | 0.580 | 0.427 | 0.492 | 0.388 | 0.428 | 0.619 | **0.505** |
| Ridge, 5 bands, 16 s | 0.561 | 0.553 | 0.431 | 0.488 | 0.399 | 0.415 | 0.602 | 0.493 |
| NeuroBOLT, our reproduction | 0.480 | 0.420 | 0.290 | 0.401 | 0.253 | 0.273 | 0.521 | 0.377 |
| Paper | 0.588 | 0.566 | 0.502 | 0.559 | 0.437 | 0.480 | 0.587 | 0.531 |

### Training on a person's own scan does not help NeuroBOLT, even from a cross-subject start

- On the six inter-subject test scans, starting intra-scan training from the cross-subject model beats a matched LaBraM start (0.582 against 0.546). But it is no better than applying the cross-subject model with no fine-tuning (0.579). Validation selection mostly picks early epochs that preserve that starting point, and by the last epoch fine-tuning has dropped it to 0.511.
- Ridge trained only on the same 16 minutes of each scan beats every NeuroBOLT variant here.

| Intra-scan, 6 held-out scans, same 48 test frames | Avg. R |
|---|---|
| NeuroBOLT trained on the scan, LaBraM start (0.5 Hz high-pass) | 0.546 |
| NeuroBOLT trained on the scan, cross-subject start | 0.582 |
| Cross-subject NeuroBOLT, no fine-tuning | 0.579 |
| Ridge trained on the scan, 5 bands | 0.628 |
| **Ridge trained on the scan, 1 Hz bins** | **0.662** |

### Ideas that did not help

- **Per-scan normalization of the EEG features** lowers ridge from 0.469 to 0.448 with five bands, and from 0.497 to 0.474 with 1 Hz bins. Overall power levels carry information across people, so NeuroBOLT will not get this change.
- **Boosted trees** on the same features score below ridge (0.412 at 16 s, 0.454 at 32 s). A nonlinear map overfits the 13 training people.
- **Dropping the 0.5 Hz EEG high-pass** changes nothing for ridge (0.469 both ways).
- **Averaging NeuroBOLT's three seeds** adds only 0.009 (0.466 to 0.475), so seed noise is not what holds it back.
