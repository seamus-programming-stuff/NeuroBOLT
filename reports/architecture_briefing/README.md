# NeuroBOLT architecture and research directions

Completed evidence review: **26 October 2026**. The current project is a two-week investigation ending in an architecture presentation. Earlier sleep-first kickoff recommendations and PhD-scale poster plans are background, rather than this briefing's scope.

- [Read the illustrated 14-page PDF](../../output/pdf/NeuroBOLT_architecture_research_briefing.pdf).
- [Editable report source](../NeuroBOLT%20architecture%20research%20briefing.md).
- [Presentation abstract](presentation_abstract.md); the report contains a nine-slide outline.
- [Completed M3 proxy pilot and its limitations](pilot/20261026_ec_global_v1/README.md).
- [Source review notes](../../research_notes/NeuroBOLT%20architecture%20research%20briefing/).
- [Separate careers reference](../../research_notes/NeuroBOLT%20architecture%20research%20briefing/Research%20assistant%20roles%20and%20alignment.md). Vacancies are time-sensitive and are excluded from the academic PDF.

## Recommended investigation

H1 replaces the dense spectral window-index maps in spectral-only, 24-second NeuroBOLT with fixed physical-support-overlap maps. All other components remain fixed. Compare against an unchanged spectral-only rerun and ridge, using person-separated selection, shared frames, raw predictive R², correlation, amplitude and coverage. Removing 4,512 parameters is an explicit regularization confound. H1 is a proposal, **not an implemented or validated improvement**. Token-preserving ROI queries are a later option if the primary investigation finishes.

The completed M3 pilot instead compares ridge, MLP and two tiny transformer readouts on **engineered lagged-power features**, using existing ds006040 development data. It completed all 12 model-fold fits and 27 outer people. Raw predictive R²: ridge .0651, MLP .0384, mean pooling -.0316, learned pooling -.0159. It does not test H1 or establish a full NeuroBOLT/clinical result. The frozen protocol, original outputs, explicitly corrected reporting copy, verification and measured resource use are retained in the pilot folder.

## Build and verification

On Windows with Python, ReportLab and Arial installed:

```powershell
python scripts/build_architecture_briefing.py
```

Run from the repository root. The renderer uses the report's figure markers and the versioned verified pilot summary. It records source, renderer, pilot-summary and PDF digests in `build_manifest.json`. Scientific diagrams are vectors. PDF text, links and all page layouts were checked using pypdf and Poppler renders; `qa.json` records the release checks. Temporary renders are excluded from this handoff.

The M3 pilot's `protocol.json` and `protocol.sha256` predate training. Its scripts and existing helper/cache hashes are frozen; the source was not revised after inspecting scores. A future rerun needs the same existing, intentionally unversioned feature cache and dependencies. It must use a **new run directory** and be treated as another development analysis. This task performs no further result-driven training.

Prediction arrays and task checkpoints are excluded from Git. No raw recordings, restricted data or pretrained weights were added. No researchers or employers were contacted. Emotiv data access remains prospective. The completed job is no longer running.
