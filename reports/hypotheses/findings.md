### A linear band-power model matches NeuroBOLT

- Ridge regression on log power in five classic bands, over the same 16 s window NeuroBOLT sees, scores the same as NeuroBOLT's baseline (0.469 against 0.468). It also scores slightly higher on the validation scans.
- So far the transformer's extra capacity buys nothing measurable across people. This is the bar every NeuroBOLT change below has to clear.

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
