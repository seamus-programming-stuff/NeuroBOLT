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
