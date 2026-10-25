# EEG to fMRI thesis exploration

For the introductory honours project and optional student-team version, start
with the [Monash EEG project kickoff](../honours_kickoff/README.md). The evidence
below remains background for the optional paired EEG-to-BOLD extension.

The current poster and explanatory guide synthesize the reviewed literature and
completed M3 experiments. Revision 3 develops the explanatory structure of the
supplied examples: background, technique, evaluation and further research.

- [A0 research poster](../../output/pdf/EEG_fMRI_thesis_exploration_poster_A0.pdf)
- [Nine-page illustrated explanation](../../output/pdf/EEG_fMRI_poster_explained.pdf)
- [Read the explanation on GitHub](poster_reading_guide.md)
- [Full literature and research report](../Clinical%20EEG%20fMRI%20thesis%20exploration.md)
- [Earlier clinical feasibility and resource-planning report](../Clinical%20EEG%20to%20fMRI%20feasibility.md)
- [Earlier reproduction/interpretability poster](../poster/README.md)
- [ds006040 results and protocol](data/)
- [NATVIEW strict and amended evidence](natview/)

The poster now shows the actual 24-second EEG-to-feature-to-estimator workflow,
explains correlation versus predictive R2, and distinguishes completed findings
from proposed thesis contributions. Its QR code links to the editable explanation.
The guide includes physiology, person-level validation, a mathematical worked
example, NATVIEW accounting, model/clinical evidence, conditional-risk reasoning,
three falsifiable work packages, resources and an advisor discussion script.

No new model experiment was run for this explanatory revision. The four primary
estimates, four learning points, NATVIEW values and 28 scientific source hashes
are unchanged. The guide's plotted signals are labelled mathematical examples,
not participant recordings. Clinical benefit and diagnostic substitution remain
unestablished. Dataset/resource brackets are proposals, not proven requirements.

## Rebuild the artifacts

Use a Python environment with the packages listed in
[requirements_poster.txt](../../scripts/requirements_poster.txt) and installed
Windows Arial/Arial Black fonts. From the repository root:

    python scripts/build_thesis_exploration_poster.py --final
    python scripts/build_poster_reading_guide.py

Editable sources are the two builder scripts, poster/content.json and
poster_reading_guide.md. The original example PDFs are optional local inspection
assets and are not republished. Current geometry, numeric selections and SHA256
checks are recorded in poster/build_manifest.json and poster/release_checks.json.
Guide source, illustration and PDF hashes are in guide_figures/build_manifest.json.

GitHub is the primary project handover location. Earlier visual revisions remain
in Git history; the earlier OneDrive bundle is a separate revision-2 snapshot.
