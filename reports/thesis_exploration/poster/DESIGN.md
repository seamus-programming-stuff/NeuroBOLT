# Revision 3: an explanatory research narrative

The user asked to keep iterating, give an in-depth explanation and use the
supplied examples as a guide. Both original example images were inspected again.
Example1's background/method/evaluation/further-research narrative informs the
explanation; example2 remains the guide for the A0 canvas, asymmetric composition,
cyan/orange palette, process diagram and central divider. The navy title panel
and enlarged evidence chart retain the stronger hierarchy developed in revision2.
No source example text, images, author identity or institutional logo is copied.

## Current deliverables

- One-page A0 poster: 636 words; exact canvas 2383.937 x 3370.394 points,
  841 x 1189 mm, portrait. Stable output/pdf filenames are retained.
- Nine-page A4 companion explanation, sourced from poster_reading_guide.md.
  It is approximately 3,200 source words, with teaching diagrams, tables,
  mathematical reasoning and an advisor discussion script.

## Why this revision is more explanatory

The main process figure now describes the actual M3 experiment: 24 seconds of
EEG, five scalp groups x five frequency bands x twelve lags, 300 power features,
training-only standardization, ridge/small MLP and regional evaluation. It no
longer uses a published UnEBOLT schematic as the main methods illustration.
The small model was not a reproduction of UnEBOLT or the other frontier models.

The interpretation panel distinguishes temporal correlation from predictive R2,
retains the uncertain global-template increment and avoids equating correlation
with a percentage of brain activity recovered. Methods explicitly say that the
96 fitted cells reuse the same 27 people. Proposed thesis questions include tests
against cost-matched measurements, state templates and simple quality rejection.
Application gates name independent events, paired patient targets and benefit.

The QR code, inspired by example1's printable handover, resolves to the editable
GitHub reading guide. It is a vector QR and a clickable PDF link. Five primary
reference links remain, for six hyperlinks total. The original reference SHA256
is still recorded in the build manifest; private example files are not published.

## Companion explanation

The nine sections cover: physiology and target scope; grouped M3 evaluation;
r versus predictive R2 and regional specificity; strict/amended NATVIEW timing;
frontier models and clinical endpoints; conditional-variance decomposition and
selective risk; three falsifiable work packages; prototype/resources/human roles;
and a five-minute advisor account with decision questions.

The correlation plot is an explicitly labelled mathematical example, not
participant data. It uses a zero-mean, unit-variance target and prediction
0.2 x target + 1, with verified r=1 and predictive R2=-0.64. Explanatory diagrams
separate clinical event references from deployment inputs. Forecasting theory
and resource brackets are scoped proposals, not new empirical results.

## Reproduction and quality checks

Use Windows Arial/Arial Black fonts and scripts/requirements_poster.txt:

    python scripts/build_thesis_exploration_poster.py --final
    python scripts/build_poster_reading_guide.py

The artifact-operation marker ran once before authoring these two PDF outputs.
It is not part of the reusable builders. Both PDF outputs were rendered; all
nine guide pages and the full poster were visually inspected. Diagram labels
and figure annotations were refined to avoid collisions. All used text fonts
are embedded, and every figure is vector. An unused default Helvetica resource
in the guide does not paint text; the content-stream audit records this fact.

The four primary rows, four learning points, NATVIEW panel and all 28 scientific
input hashes match revision2. No experiment was rerun and the reviewed research
report is unchanged. Native input audits remain enforced. Guide links, rounded
primary table values and the mathematical example were checked. Current checks
and output/source hashes are in release_checks.json and qa.json. Geometry and
numeric selections are in build_manifest.json; guide provenance is in
../guide_figures/build_manifest.json.

GitHub is the primary project location per the user's clarification. Earlier
visual versions and the original example-style build remain in Git history.
The earlier OneDrive bundle is a separate revision2 snapshot and is not the
primary handover for this revision.
