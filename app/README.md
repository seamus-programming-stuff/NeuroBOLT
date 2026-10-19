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
    --model models/vu_model_full.npz --out monitor_report/
python -m app.arousal_monitor --eeg ... --marker TR --model ... --out ... --stream   # real-time replay
```

Input EEG must already be cleaned of MR gradient and ballistocardiogram artefacts. Volume onsets come
from an annotation (`--marker`, e.g. `TR`, `R128`) or a fixed `--tr`. Outputs: `frames.csv`,
`summary.json`, `monitor.png`.

## Validation

See `reports/NeuroBOLT external validation.md` for the ds006040 results (28 people the model never
saw, another site and scanner): agreement with the measured global signal for eyes-closed and
eyes-open rest, offline and streaming, the QC relationship, and per-volume latency.

## Limitations

- Trained on 22 people from one site (eyes-closed rest). Expect lower accuracy on other montages,
  artefact-correction pipelines and eyes-open rest.
- Accuracy depends on how much arousal varies in a run: a person who stays alert and still gives the
  model little to track.
- The vigilance flag is relative to the run itself. It marks the least-vigilant periods of that run,
  not an absolute sleep stage.
