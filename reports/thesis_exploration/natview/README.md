# NATVIEW execution results

**Strict original v1: not achieved as an8-person confirmation.** Seven recordings failed the cumulative source-mask contract; sub12 alone passed135 frames. The unchanged v1 record, sources and hashes are preserved in `v1/`.

**Amended v2 secondary exploration: 6/8 eligible after metadata-certified clock reconstruction.** All8 were attempted; sub05/sub10 remain below the unchanged60-frame gate. This is not the original untouched confirmation. Model coefficients, scalers, spatial bridge and all numeric QC thresholds stay unchanged.

| Endpoint | Person-mean r (95% person-bootstrap CI) | Normalized-target predictive R2 | Amplitude ratio |
|---|---:|---:|---:|
| global | 0.1249 [-0.0330, 0.2760] | -0.0431 | 0.1585 |
| regional64 | 0.1038 [-0.0002, 0.2071] | -0.0714 | 0.1492 |
| VU_global_adjusted_residual64 | 0.0248 [-0.0050, 0.0546] | -0.0722 | 0.0968 |

Per-person CIs, amplitude, lag profiles and all64 regional values are in `v2/per_person_metrics.csv` and `v2/regional_metrics.csv`. Lag is descriptive and never repairs clock alignment. `v2/coverage_QC.csv` retains all8 denominators, source mask counts, direct/interpolated channel counts, physical history coverage, motion and independent-clock evidence.

The v2 adapter requires monotonic exact integer original-minus-processed event offsets, anchors bracketing the whole history and filter margins, and a split at every source boundary. It never extrapolates or bridges a gap. The source mask is preserved as provenance. Some masks are consistent with an internal cleaning-stage mask; exact ASR substep identity is not established.

There are21 directly named nonprime sites plus2 always-interpolated VU TP9-prime/TP10-prime targets. Additional missing2–3 sites are interpolated in3 prespecified people using the fixed source-coordinate bridge. Native references remain different. Whole-run artifact correction/filtering/normalization are retrospective.

NATVIEW is instructed eyes-open rest at a new site; site, eye state and target preprocessing differences remain confounded. Pupil/respiration support independent timing/coverage QC only; missing/interpolated pupil is not sleep, and no clinical arousal claim is supported.

The observed coverage loss under fixed24s history motivates later tests of estimators that handle irregular/missing observations and explicitly abstain when context is insufficient. Those are future experiments, not results of an additional model arm here.

Reproduce from the repository on M3 using `scripts/natview_m3.sbatch`; phase order is stage pilot, inspect/train/cache audit/pilot/tests, v1 freeze, stage reserved8, v1 panel, preserve v1, metadata diagnostics, v2 audit, v2 freeze, v2 run. Exact locks and job records are supplied.

Model SHA256: `dd9b894b805dd5a33fb5f5fbf741f8670439f81a3de709410320aba16ed0c7a9`. V1 protocol: `005d4145fd51f297df8133ee28870bb7b9f97f1eb04f0533e047817ce241d035`. V2 protocol: `02f3138499a33c3f683a3c7b17899651bc968dd44ca2791edf7bc96bb71531d7`.

Data attribution: Nathan Kline Institute NATVIEW EEG-fMRI release, CC BY4.0. Source URLs, SHA256, ETags/response headers and licenses are retained in asset receipts and provenance. Original volumes/EEG remain on M3; there are no git commits or pushes.
