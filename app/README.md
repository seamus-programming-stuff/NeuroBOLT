# EEG arousal monitor (research prototype)

Estimates, from scalp EEG alone and once per fMRI volume, the arousal-driven brain-wide BOLD
component and an EEG vigilance trace, and flags low-vigilance periods. It is built on the finding of
the NeuroBOLT interpretability study that what resting EEG predicts about BOLD is mostly where a
person sits on the arousal axis, seen through the haemodynamic delay.

**Intended uses**
- **Scan-time QC for resting-state fMRI:** see drowsiness as it happens, or flag runs and periods
  afterwards, without waiting for fMRI preprocessing.
- **An arousal covariate:** a per-volume EEG-derived estimate of the global, arousal-related BOLD
  fluctuation, for analyses that want to model or report vigilance.
- **EEG-only settings:** a principled, fMRI-calibrated arousal index where no scanner is available.

**Not for** clinical decisions, regional brain mapping (the model mostly predicts the brain-wide
component), or eyes-open data without checking performance first (see Validation).

## How it works

1. Pick the 26 model channels (FP1 … TP10; names are case-insensitive), resample to 200 Hz, high-pass at 0.5 Hz.
2. For each fMRI volume, take the preceding 24 s of EEG, in twelve 2 s pieces, and compute log power
   in 44 one-Hz bins (13,728 features), exactly as in training.
3. Standardize the features within the recording (offline) or with running statistics (streaming),
   then apply a ridge model trained on all 29 scans of the VU dataset (22 people).
4. Report per volume: predicted global BOLD, predicted thalamic BOLD, vigilance index
   (log alpha / (delta + theta)) and its robust z within the run; flag runs of z < −1 lasting ≥ 10 s.
   Per run: arousal fluctuation (SD of the predicted global BOLD), vigilance SD, flagged fraction.

The model is causal: a volume's prediction uses only EEG recorded before it, so it can run live.

## Usage

```bash
python -m app.arousal_monitor --eeg sub-01_task-rest_eeg.set --marker TR \
    --model app/models/vu_model_full.npz --out monitor_report/
python -m app.arousal_monitor --eeg ... --marker TR --model ... --out ... --stream   # real-time replay
```

Input EEG must already be cleaned of MR gradient and ballistocardiogram artefacts. Volume onsets come
from an annotation (`--marker`, e.g. `TR`, `R128`) or a fixed `--tr`. Outputs: `frames.csv`,
`summary.json`, `monitor.png`.

## Validation

On OpenNeuro ds006040 (28 people the model never saw, another site, scanner and EEG cap; 56 rest runs):

| | Eyes closed | Eyes open |
| --- | --- | --- |
| r, predicted vs measured fMRI global BOLD (offline) | 0.26 (95% CI 0.20–0.31) | 0.17 (0.11–0.24) |
| Same, streaming (causal, live) | 0.26 (0.21–0.32) | 0.16 (0.10–0.22) |
| Compute per fMRI volume | 3 ms | 3 ms |

Across runs, the arousal-fluctuation score tracks the fMRI-measured global-signal swing (Spearman ρ = +0.50,
p < 0.001) and how predictable the run is (+0.42). The low-vigilance flags are **not yet validated**. Details:
`reports/NeuroBOLT external validation.md`; interactive replay: https://claude.ai/artifact/M3MtScwGda3GP4d2e27dUU.

Models: `app/models/vu_model_full.npz` (13,728 features) and `vu_model_bands60.npz` (60 channel-averaged band
powers, nearly as accurate and far smaller), both ridge regression trained on all 29 VU scans.

## Limitations

- Trained on 22 people from one site (eyes-closed rest). Expect lower accuracy on other montages,
  artefact-correction pipelines and eyes-open rest.
- Accuracy depends on how much arousal varies in a run: a person who stays alert and still gives the
  model little to track.
- The vigilance flag is relative to the run itself. It marks the least-vigilant periods of that run,
  not an absolute sleep stage.
