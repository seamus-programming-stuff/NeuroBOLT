### A linear band-power model matches NeuroBOLT

- Ridge regression on log power in five classic bands, over the same 16 s window NeuroBOLT sees, scores the same as NeuroBOLT's baseline across all three seeds: 0.469 against 0.466 on the held-out scans, and 0.337 against 0.335 on validation.
- The transformer's extra capacity buys nothing measurable across people. This is the bar every NeuroBOLT change below has to clear.

### Two things make the linear model clearly better: frequency detail and history

- **1 Hz frequency bins** instead of five bands raise ridge from 0.469 to 0.497 at 16 s, and from 0.337 to 0.374 on validation.
- **32 s of EEG history** in 2 s lag bins raises it to 0.493, and 1 s lag bins to 0.495. Going to 48 s or 64 s adds nothing (0.486 and 0.488), so the useful history matches the slow tail of the haemodynamic response.
- NeuroBOLT uses a fixed 16 s window and spectral windows of 0.5–4 s. The 24 s NeuroBOLT arm is running now, and a ridge combining 1 Hz bins with 32 s of history is running on CPU.

### Combining NeuroBOLT with ridge gives the best predictions so far

- Averaging z-scored predictions from NeuroBOLT's three seeds and two ridge models reaches 0.514 on the held-out scans and 0.381 on validation. NeuroBOLT's own seed ensemble reaches 0.475 and 0.335, and the paper reports 0.473.
- Almost all of the gain comes from the ridge models: the two ridges together reach 0.513 and 0.380 without NeuroBOLT. NeuroBOLT and ridge make partly different errors, but two ridges with different strengths complement each other as well.

| Predictions averaged (z-scored per scan) | Validation R | Test R |
|---|---|---|
| NeuroBOLT, 3 seeds | 0.335 | 0.475 |
| Ridge, 1 Hz bins, 16 s | 0.374 | 0.497 |
| Ridge, 5 bands, 32 s / 16 lags | 0.344 | 0.493 |
| NeuroBOLT + ridge 32 s | 0.363 | 0.506 |
| Ridge 1 Hz + ridge 32 s | 0.380 | 0.513 |
| **NeuroBOLT + both ridges** | **0.381** | **0.514** |

### Within a single scan, ridge clearly beats NeuroBOLT

- Ridge on 16 s of band power, trained with NeuroBOLT's exact intra-scan split and scored on the same last 48 frames of each scan, averages 0.493 over the 29 scans and 7 regions. Our NeuroBOLT reproduction averages 0.377 on those frames, and the paper reports 0.531. With 1 Hz bins, ridge reaches 0.505.
- Ridge also fails far less often: 0–7% of its runs score below zero, against 13% for NeuroBOLT. With 453 training windows per scan, the transformer has too little data, and its validation-selected epoch is noisy.

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
