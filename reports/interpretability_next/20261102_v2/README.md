# NeuroBOLT interpretability continuation

**Short summary.** Correcting the existing ridge predictions gives mean regional raw R² 0.094 for EEG, 0.044 for physiology-focused features and 0.092 jointly. EEG predicts better than these physiology features. Participant-level inference replaces repeated-scan certainty. Neural CKA/IG are blocked by checkpoint provenance; physical spectral-lag alignment remains the next untested architecture hypothesis.

- [Presentation and speaker notes](presentation.md)
- [Claim audit](claim_audit.md)
- [Two-week plan](next_two_weeks.md)
- [Reading/presentation PDF](../../../output/pdf/NeuroBOLT_interpretability_next.pdf)

## New primary comparisons

| Contrast: regional mean raw R² | Mean difference ± SD | 95% CI | p | BH / BY | Paired d_z | n |
|---|---|---|---|---|---|---|
| eeg_full minus phys_specific | +0.0497 ± 0.0778 | [+0.0185, +0.0828] | 0.0063 | 0.0126 / 0.0189 | 0.639 | 22 people |
| eeg+phys_specific minus eeg_full | -0.0011 ± 0.0064 | [-0.0040, +0.0011] | 0.4611 | 0.4611 / 0.6916 | -0.179 | 22 people |

## Evidence status

- P0 metrics/partitions: completed from existing predictions; no refit.
- P1 participant lag/temporal-null/perturbation corrections: completed.
- P2 CKA/IG/representation probes: blocked under the complete-CV checkpoint requirement.
- P3 physical spectral-lag alignment: proposed; no model improvement claimed.

Bootstrap B=10000; participant-level sign flips use 9,999 Monte Carlo draws at n=22, exact 32 sign configurations at n=5. BH/BY families are declared in protocol.json.

## Reproduce and inspect

Run `python scripts/interp_next_tests.py` for synthetic checks. The analysis protocol records source/input hashes and original M3 locations; large data/predictions remain there. A new analysis must use a new output directory and must not silently overwrite this frozen record. Run `python scripts/build_interp_next.py --run reports/interpretability_next/20261102_v2` to rebuild figures and documents from the small outputs.

See execution_log.json, submission.json, accounting.json and verification.json for actual completion/resource/provenance details. Rendering/QA records are separate from scientific evidence. Historical reports were preserved.

## Reading support

- [Earlier architecture briefing](../../NeuroBOLT%20architecture%20research%20briefing.md)
- [Architecture and frontier-model review notes](../../../research_notes/NeuroBOLT%20architecture%20research%20briefing/)
- [Checkpoint provenance qualification](checkpoint_provenance_note.json)

Training-mean GSR R² is numerically zero; negative-sign counts at approximately machine precision are not meaningful failures. All frozen outputs are retained.

The primary 63-second temporal null rejects 28/29 scans under BH and 27/29 under BY; the 126-second sensitivity has the same counts. Alpha autocorrelation persists in some training scans, so cyclic stationarity is a substantive assumption.
