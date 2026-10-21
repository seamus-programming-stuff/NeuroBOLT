# EEG-to-fMRI research poster

This is the earlier poster covering the project's existing reproduction,
interpretability and prototype work. The current thesis-exploration poster and
illustrated guide are indexed in [the thesis research folder](../thesis_exploration/README.md).
The studies use different protocols and targets; their scores should be read in
their own experimental context.

The poster follows the A0 portrait format of `example1.pdf` and `example2.pdf`
in the supplied `Examples.zip`, with the blue/orange section treatment of the
second example. The examples are design references only.

## Deliverables

- `output/pdf/NeuroBOLT_research_poster_A0.pdf`: one-page, 841 x 1189 mm poster.
- `output/pdf/NeuroBOLT_research_poster_preview.png`: screen preview.
- `scripts/build_research_poster.py`: editable text, chart and layout source.
- `reports/poster/poster_data.json`: plotted data, source paths and text positions.

Print the PDF at **100% / actual size on A0 portrait**, without cropping. Fonts
are embedded; the figures, text and QR code are vector objects.

## Rebuild

Run `python scripts/build_research_poster.py` with `numpy`, `pandas` and
`reportlab` installed. The build uses the Windows Arial font files. The Codex
bundled Python runtime contains the dependencies used for this version.

## Content choices

The four results cover subject-grouped VU validation, transfer to ds006040,
interpretability, and the arousal-monitor prototype. The poster uses existing
project results; it does not run new models.

- Prediction means and intervals use people as the inferential unit (22 at VU,
  28 at the external site). Seven targets are six DiFuMo regions plus global BOLD.
- The external figure uses the strictly frozen VU-statistics protocol. Its paired
  local-minus-frozen interval was recomputed for that exact comparison:
  +0.00146, 95% CI -0.01692 to +0.01983. Similar means do not demonstrate equivalence.
- The GSR comparison uses the same 64 regions on both sides: mean R 0.34259
  before, 0.14384 after removing the global signal. It does not compare 65 raw
  targets against 64 residual targets.
- Coupling curves are descriptive Fisher-z means over the 29 VU scans. They
  are correlations, not causal haemodynamic response estimates.
- The prototype example is the eyes-closed run closest to median offline
  accuracy, `sub-008_EC` (r = 0.275). Lines break at missing/excluded windows.
- The streaming score is from replay of cleaned EEG, rather than a prospective
  scanner trial. Arousal flags still need independent pupil or sleep-stage labels.

The PDF was rendered with Poppler and visually checked as a complete poster.
