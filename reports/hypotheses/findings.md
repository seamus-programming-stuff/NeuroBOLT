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
