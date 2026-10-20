# Visual revision 2

The A0 poster is a visual iteration of the reviewed research poster from commit
b42bb3c. The user requested a more visually striking design. The original
Examples.zip / Files / example2.pdf remains the reference for the A0 canvas,
cyan/orange palette, asymmetric columns and full-width central divider. The
internal panels are deliberately reorganized to put the completed evidence first.
The private example itself is not embedded or republished.

The exact canvas remains 2383.937 x 3370.394 points (841 x 1189 mm), A0 portrait.
The measured original reference SHA256 is
6cbcaa767705fab9f998e7bfbe85e27b66d7da3c3dcd356359c5c3fd43cd6e83.

## Visual changes

- Dark navy title panel, cyan accent and a shorter two-line research question.
- A concise summary at the top and an original vector EEG-to-BOLD schematic.
  These traces are explicitly illustrative, not measured participant signals.
- The primary four-arm chart is now the largest evidence panel, with enlarged
  estimates, confidence intervals and explicit participant/experiment/input counts.
- Thin accents, soft cards and a restrained pale background replace heavy boxes.
- The NATVIEW result has a separate panel, denominator, uncertainty and coverage
  indicator. It is not pooled into the main development-data chart.
- The three PhD questions are numbered and arranged as an actionable research path.
- EEG and BOLD definitions, named model references and clinical validation gates
  remain visible for stakeholder discussion.

## Evidence retained

The four preselected primary rows, four learning points, NATVIEW panel and all
28 scientific source-file hashes are identical to the previous reviewed build.
The code still audits native exports against participant CSVs and the frozen
protocol before authoring. The experiment report, model results and data are
unchanged. The poster is a 612-word condensation, not a new experiment.

The clinical/model distinction remains explicit: the small matched-feature MLP
is not UnEBOLT; published models were not reproduced. Literature scores use
different protocols. The paired global-template increment remains uncertain.
Strict NATVIEW timing QC was 1/8; amended QC was 6/8. Its accuracy is secondary
exploratory after a metadata-only amendment, with the ingestion pilot excluded.
The CI includes zero; negative predictive R2, all-eight frame coverage and the
interpolation policy remain visible. Clinical benefit and end-to-end live use
are untested, and normalized retrospective targets do not establish absolute
%BOLD calibration.

## Typography and reproduction

All elements are vector; Arial and Arial Black are embedded. Display sizes are
38-102 pt, body text 30-34 pt, figure labels 23-29 pt and decorative annotations
20-23 pt. No content is silently shrunk to fit. Text has explicit height limits.
Source geometry is GEOMETRY in the builder and build_manifest.json.

Build with the bundled ReportLab Python runtime:

    python scripts/build_thesis_exploration_poster.py --final

The private reference is optional. The final 2400-pixel PNG was inspected and
spacing refined. Release checks confirm a single A0 page, embedded fonts, no
raster figures, all five reference links, no release placeholders, unchanged
statistics and matching scientific hashes. release_checks.json and qa.json
record final hashes and review evidence. The artifact edit marker already ran
once before this revision's first authoring command; it is not part of rebuilding.
