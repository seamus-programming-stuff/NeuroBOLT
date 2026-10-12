### The best predictor so far is linear

- Ridge regression on log EEG power in 1 Hz bins (1–45 Hz), over 32 s of history in sixteen 2 s lag bins, scores 0.525 on the held-out scans and 0.371 on validation. NeuroBOLT scores 0.466 (0.475 when its three seeds are averaged), and the paper reports 0.473.
- The gain comes from two things NeuroBOLT does not exploit across people. 1 Hz bins alone take ridge from 0.469 to 0.497, and 32 s of history alone takes it to 0.493. Going to 48 s or 64 s adds nothing (0.486 and 0.488), so the useful history matches the slow tail of the haemodynamic response.
- With the same 16 s window and five classic bands, ridge already matches NeuroBOLT (0.469 against 0.466 on test, 0.337 against 0.335 on validation). The transformer's extra capacity buys nothing measurable across people.

### NeuroBOLT gains a little from a longer window

- A 24 s window (pretrained time embedding stretched from 16 to 24 slots) raises NeuroBOLT from 0.466 to 0.481 on the held-out scans and from 0.325 to 0.338 on validation, and all three seeds improve. It is the first NeuroBOLT change that helps, matching what history does for ridge.
- The gain is small next to ridge's lead: its 95% interval over the six held-out scans runs from −0.004 to +0.034. A 32 s NeuroBOLT arm, where ridge's gains level off, runs next.

### One shared model does as well as seven separate ones

- A single NeuroBOLT with seven outputs, one per region, scores 0.462 on the held-out scans against 0.466 for seven separate models, and 0.007 higher on validation, at a seventh of the training cost. It does better for the middle frontal gyrus and putamen and worse for the cuneus and Heschl's gyrus.
- Because it is seven times cheaper, the remaining NeuroBOLT changes (log spectra, no high-pass, learned scale weights, lower learning rate, AdamW β₂ 0.99, no window baseline, 8 s and 24 s windows) now run on the shared model, compared with this shared baseline. The 32 s window still runs per region, to extend the 24 s result.

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
