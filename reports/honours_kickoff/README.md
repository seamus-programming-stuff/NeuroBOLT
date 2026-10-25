# Monash EEG honours kickoff

This planning package reframes the earlier NeuroBOLT thesis exploration as an
introductory CS/AI honours project. The recommended starter is one public DREAM
EEG subset, a spectral classifier and a small transformer comparison. The
existing paired EEG-to-BOLD pipeline is an alternative or later extension.
One student can complete the core; three or four can divide the shared pipeline.

- [Reusable AI working prompt](working_prompt.md)
- [Source-linked project and Monash opportunity brief](../Monash%20honours%20EEG%20project.md)
- [Editable Project Kickoff deck](../../output/presentations/Monash_EEG_honours_kickoff_v2.pptx)
- [Printable kickoff PDF](../../output/pdf/Monash_EEG_honours_kickoff_v2.pdf)
- [Editable slide text and source notes](content.json)
- [Dataset and related-project audit](../../research_notes/Monash%20honours%20EEG%20project/Datasets%20and%20related%20projects.md)
- [Monash resources and access actions](../../research_notes/Monash%20honours%20EEG%20project/Monash%20resources.md)
- [Existing-code reuse and learning audit](../../research_notes/Monash%20honours%20EEG%20project/Reuse%20and%20learning%20scope.md)
- [Earlier EEG-to-fMRI evidence](../thesis_exploration/README.md)

The brief distinguishes public access from potential collaborations and
controlled data. DREAM catalogue counts are not usable sample counts after QC.
Report labels do not establish dream decoding or consciousness. The 12-week
schedule and compute cap are proposals, not official course rules or measured
resource requirements. Confirm the actual honours assessment and supervision.

No new modelling, raw-recording download, recruitment or external contact was
performed. A read-only M3 queue check succeeded on 26 October 2026 and showed no
current jobs for this account. Individual student access and allocation still
need the relevant project leader. The new transformer and viewer are proposals.

## Template and reproducibility

The deck imports all 12 slides of the explicitly requested Project Kickoff
reference. It retains the 1280 x 720 canvas, layouts, colours, recurring elements
and reference font families. The checkerboard picture placeholder becomes an
editable method diagram. The original reference is unchanged and is not copied
into this repository.

Reference SHA256:
`b1b15cb0c23ad524f9832749ec31b775719bae2bdba897de9c9d8556ca00a44c`.

[build_honours_kickoff.mjs](../../scripts/build_honours_kickoff.mjs) uses the bundled
`@oai/artifact-tool` Node runtime. From the repository root, run it with that
runtime's Node executable. `--reference` can point to another retained copy of
the same reference; `--content` and `--out` override the default source and build
directories. `CODEX_ARTIFACT_NODE_MODULES` overrides the bundled modules location.
It writes a draft PPTX, all slide previews and layout snapshots under
`tmp/honours_kickoff/build/`, not over a delivered file.

The delivered PPTX passed the bundled package, slide-size, heading, native-table,
font-policy and re-import checks. See [validation.json](validation.json).
The template-family validator cannot parse the unmodified reference itself
because it contains duplicate placeholder identities. Instead, the separate
comparison checked all 99 original shape/table frames without a change and
visually reviewed every slide against its reference. The source timeline's
intentional crop on slide 8 remains. See [qa.json](qa.json).

[export_honours_kickoff_pdf.ps1](../../scripts/export_honours_kickoff_pdf.ps1)
exports the final deck using installed Microsoft PowerPoint, opening it read-only
without a visible document window. The PDF has 12 pages and selectable text.
All pages were rendered for visual inspection. A different presentation renderer
may wrap text differently, so repeat the visual review after edits.

Scientific source data and older results are unchanged. Raw recordings, ignored
feature caches, private examples and temporary build files are not part of this
GitHub handoff. The alternative paired-data cache requires a separately arranged
permitted handover; a fresh clone does not include it.
