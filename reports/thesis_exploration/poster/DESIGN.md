# Exact reference and current status

The reference is **Examples.zip / Files / example2.pdf**, supplied by the user,
not a hybrid of the two examples. Both examples were extracted, rendered and
visually inspected before PDF authoring. The untouched reference PDFs and
their rendered PNGs are private local inspection assets in ignored `reference/`.
They are optional for rebuilding and must not be republished. Reference material supplies design
only: none of its engineering text, author identities or images is reused in
the scientific poster. The coordinator selected example2 to satisfy the user's
request to mirror a supplied example; the user did not choose or reconfirm a
particular example. Seamus Taylor is the confirmed author. No department, supervisor,
institutional affiliation or logo is inferred.

**Current artifact is the reviewed final exploratory poster.** Both studies and
clinical/theory claims were approved by the coordinator. The final report has
no DRAFT/PENDING release markers and its SHA256 is locked in integration.json.
The output retains the explicit PhD-exploration and secondary-exploratory NATVIEW
scope; final file status does not imply clinical validation. The release was
rendered, visually inspected and checked against the actual CSVs and provenance.
Earlier draft-design descriptions below document the iteration history; final
numeric state and hashes are authoritative in build_manifest.json, native_audit.json,
natview_audit.json and release_checks.json.

## Measurement and visual correspondence

PDF geometry was read with pdfplumber (rectangles, images, character fonts and
sizes), rather than estimated from a screenshot. Origin below is top left;
all numbers are PDF points, 72 points/inch. Divide by 2.834646 for millimetres.
Page MediaBox is **2383.937 x 3370.394 points = 841 x 1189 mm**, A0 portrait.
The output uses that exact MediaBox rather than a rounded A0 preset.

| Reference role / new role | x | y | width | height |
|---|---:|---:|---:|---:|
| Cyan title / two-line research title | 56.693 | 56.693 | 2270.551 | 264.323 |
| Narrow definition / clinical question | 97.691 | 349.564 | 562.301 | 412.130 |
| Narrow process diagram / verified UnEBOLT schematic | 96.423 | 823.416 | 563.569 | 811.990 |
| Wide rationale / thesis aim | 727.681 | 349.142 | 1556.084 | 554.643 |
| Wide motivation / working hypothesis | 727.681 | 923.500 | 1556.084 | 284.932 |
| Small plant image / clinical validation path | 725.000 | 1242.000 | 457.000 | 335.000 |
| SAGE2 explanation / models and possible uses | 1270.667 | 1244.524 | 1015.599 | 388.382 |
| Orange full-width divider / M3 evidence and next steps | 56.693 | 1665.627 | 2270.551 | 102.619 |
| Lower left orange methods box / actual study methods | 96.423 | 1820.803 | 920.102 | 461.395 |
| Lower right paired-image region / prominent empirical dot-CI chart | 1078.925 | 1820.803 | 1204.341 | 420.554 |
| Lower left 2x2 views / controlled learning-curve figure | 96.423 | 2440.000 | 920.102 | 737.000 |
| Nested NATVIEW inset within that lower-left science region | 96.423 | 2905.000 | 920.102 | 272.000 |
| Middle right orange box / three proposed PhD work packages | 1078.925 | 2285.198 | 1204.341 | 420.554 |
| Bottom right orange box / applications, limits, compact references | 1078.925 | 2753.248 | 1204.341 | 484.668 |
| Cyan author line / Seamus Taylor, PhD thesis exploration | centred | 3275.274 | - | - |

The title is 20 mm from each side, 801 mm wide and 93.25 mm tall. Upper
columns have widths 198 mm and 549 mm; their gap is 23.9 mm. The orange divider
starts at 587.6 mm. Lower columns are 324.6 mm and 424.9 mm, with a 22 mm gap.
This is intentionally not an equal-column poster.

Original typography: Arial Black title 84 pt, heading 48 pt, divider 56 pt;
Helvetica Neue body 36 pt; image-region heading 46 pt; author 48 pt. Output
uses the same installed Arial Black for display text and embedded Arial as
the body substitute (Helvetica Neue is not available). Body is 34-36 pt,
work packages 33 pt, technical diagram labels 25-30 pt and references 24 pt.
No type is automatically shrunk to force an overflow. Shorter content respects
the supplied example's proportions. The final poster has 662 words;
the 1000-word upper bound is enforced, with room for actual findings and
reviewed evidence. No padding is added to reach a literature-dump word count.

Fill colours from the reference: cyan approximately RGB (0.001, .634, 1),
orange approximately (1, .576, 0). Output rounds to #00A2FF / #FF9300.
White ground, unfilled blue/orange outlines, no new background treatment.
Outlines are 5 pt above, 5-6 pt below, as measured in the reference.
The reference has no numbered section headings; only proposed WP1-WP3 and
source citations are numbered in the output.

The original uses eight scientific/technical images totalling roughly 17% of
page area. The replacement keeps the same figure locations and comparable
space allocation through architecture, pathway, dot-CI and learning-curve
panels. Those scientific figures are vector ReportLab marks, not screenshots.
The two primary empirical regions together occupy about 15% of the page;
architecture and pathway add visual explanation in the upper region.
The primary results panel deliberately has no orange outline: the reference
uses bare images at that position. The two subsequent text boxes retain their
orange outlines. The lower left chart inherits the four-view image's role.

## Scientific boundary and source handling

`content.json` is the editable text source. At the coordinator's request the
initial NeuroBOLT reference architecture was replaced by a simplified
**UnEBOLT schematic**. It was verified directly in the full UnEBOLT manuscript,
section 2.2, PDF pp. 3-5: shared spatiotemporal/spectral encoder, gated adaptive
fusion, learnable ROI embeddings concatenated with EEG context, representation
adapter and ROI-specific linear heads. Sequential predictions form regional
time courses. No layer counts or detailed mechanisms are invented. The diagram
depicts a published model, not an implementation reproduced in the M3 study.

The generic evidence-tier box was replaced by **Models and possible uses**
from the newly completed `clinical applications.md` research audit. Healthy
technical temporal correlations are UnEBOLT 64-region .418, UniEFS 512-region
.367 and MARBLE 64-region .434. MARBLE's 2.6M model-size result is not a
clinical latency guarantee. Protocols differ and the panel is not a ranking.
Feedback/compact-predictor uses are proposed; UniEFS's EEG-only Parkinson
probe does not establish patient BOLD fidelity. Prism remains the separate
clinical precedent below. Primary URLs and qualifications are in
`sources.json`; final citation wording awaits coordinator synthesis.

The clinical precedent is FDA Prism K222101: adjunctive PTSD biofeedback;
diagnostic interpretation is excluded. This does not transfer clearance or
efficacy to NeuroBOLT, UnEBOLT, MARBLE, UniEFS or this project. DECIDE-AI is
reporting guidance, not empirical proof of utility. Draft references stay
compact; model-specific claims must acquire exact primary-source references
from the reviewed evidence before finalization. Numeric summaries are qualified,
not pooled. Evidence labels distinguish clinical precedent, healthy technical
validation, internal experiments and proposed PhD work; these are types of
support, not a validated evidence-grading instrument.

Never infer a biological ceiling from a plateau, equivalence from similar site
means, live performance from cleaned replay, or patient BOLD recovery from an
EEG-only disease classifier. Label all already-inspected sites as development
data. Arousal labels require independent adjudication/corroboration. A future
prospective pathway remains proposed until actually evaluated.

The worker's `M3 experiments.md` was read after creation. The coordinator
confirmed final post-QC N=27 people/54 EC+EO runs, not all 28 public people;
that actual N appears in methods and captions. MLP uses one seed and equal weights on four target
groups. Its objective differs from independent-output ridge. New input features
use past samples, but inherited EEG cleaning, eligible-frame masking and target
processing are retrospective. Amplitude/R-squared use cached normalized targets,
not absolute patient %BOLD calibration. ECG beat detection is unvalidated;
respiration/CO2 and independent arousal labels are absent. These limitations
must remain visible after actual results arrive.

## Incoming results contract

The builder reads owned `integration.json` by default. Its native adapter reads
worker `data/summary.json`, `per_person_scores.csv` and `protocol.json`, then
checks displayed means against 27 unique held-out people. It matches all
plotted values/intervals to `poster_scores.csv` and `poster_learning.csv` by
estimator, inputs and resources, retaining the predeclared order despite the
worker CSV order. It checks the protocol hash, passed verification files and
nine COMPLETED 0:0 root jobs. `--audit-native` records that source/statistics
audit without authoring a PDF. The coordinator approved both studies and the finalized report; all three
review flags are true. The final report hash is checked before authoring.

The poster agent owns neither raw results nor experiment/research notes.
`input_contract.example.json` documents an optional CSV-only route. The native
adapter is preferred for the delivered files.

Required scores CSV columns:

`condition,model,target,metric,mean,ci_low,ci_high,n_people`

Optional `label` supplies a concise display name. `primary_view` filters on
exact column/value pairs, including extra columns if necessary, to select
2-5 comparable models in one condition/target/metric. No automatic winner
selection or aggregation occurs. Means and confidence intervals must already
be computed using people as the inferential unit; no window-level error bars.
Caption must state target aggregation and interval method. Keep labels below
about 24 characters and result captions below 30 words.

The learning CSV has those same columns plus `train_people` and
`target_seconds_per_person`. Retained target-seconds are not acquired paired
minutes. Select one condition/target/metric and at most four model-duration
series on identical evaluation people. Intervals are drawn
without recomputation. The figure is descriptive development evidence, not
a fitted scaling law. If actual results need another second figure, change
this new builder rather than manufacturing a learning curve.

Final manifest requirements:

- `status`: `completed`.
- `results_reviewed`: true and `evidence_reviewed`: true, set only after review.
- `completed_jobs`: objects with real `job_id` and `state: COMPLETED`, checked
  against worker sacct/provenance, not inferred from an empty queue.
- Existing `experiment_note` and `reviewed_report` paths.
- Existing `source_files`, scores CSV, selected primary view and learning CSV.
- Exact `protocol_caption`, `result_scope`, `result_caption`,
  `result_takeaway`, `metric_label`, and short `methods_text` describing what
  actually completed, including missing/failed intended branches.
- Reviewed `content.json`, including application/model evidence, source
  citations and limitations.

NATVIEW occupies a separate inset at y=2905, h=272 points, within the original
lower-left science area. The controlled learning plot is 196 points high,
retaining 25-28 pt ticks/labels and two duration series. NATVIEW has its own
N, metric label, scale, interval and QC caption; it never pools the ds006040
CI. One ingestion pilot (sub01) precedes eight modality-preselected people;
those planned counts are not a claim all survive QC. Report the VU-trained
frozen 23-channel bridge, clock reconciliation, target extraction and montage
checks from actual outputs. Exclude the pilot from confirmation. A completed
QC failure can be reported instead of fabricating accuracy. See
`natview_input.example.json`.

The report and `poster_brief.md` were read as drafts. WP1-WP3 now address
measurement design, structured estimation with counted calibration, and
selective prediction under stated shift assumptions. The published UnEBOLT
reference was not reproduced; tested neural capacity is a small one-seed MLP.
UniEFS says EEG-only Parkinson classification probe, patient BOLD unvalidated.
The uncertain regional increment over the predicted-global template is the
main takeaway. Neither study supports diagnostic use or clinical adequacy.

`--final --validate-only` checks the gate without authoring a PDF.
`--final` refuses missing evidence or result rows and cannot leave a pending
empirical panel. A machine-readable `build_manifest.json` records reference,
source and output SHA256 hashes, exact box/text positions, fonts, words and
selected numeric rows. It does not alter the source results.

## Rebuild and QA

The build is self-contained with respect to the private example. The source
stores the measured geometry and verified reference SHA256:
`6cbcaa767705fab9f998e7bfbe85e27b66d7da3c3dcd356359c5c3fd43cd6e83`.
This was verified against both the local supplied example and the existing
build manifest. If the private PDF exists, the helper verifies its bytes and
rejects a mismatch. If absent, it uses the recorded hash and labels the
manifest `not loaded; recorded verified SHA256 and measured geometry`.
The poster is generated from geometry and original source, without loading or
embedding the example's content. No original example assets are published.

Latest NATVIEW scope: strict v1 accepted 1/8, retained as a QC outcome rather
than a population-accuracy estimate. The metadata-only v2 amendment accepted
6/8 (sub04,06,08,11,12,13); sub05/10 failed the unchanged 60-frame minimum.
Model weights and numeric QC thresholds did not change, but this is explicitly
**secondary exploratory after QC**, not untouched confirmation. The user
supplied these QC counts; six-person accuracy and CIs remain unapproved and
are not drawn. Final reporting must account for coverage/failures across all
eight reserved people and exclude the ingestion pilot. Pilot 134/288 eligible
frames must never be substituted for all-eight coverage.

The bridge comprises **23 target electrode sites**, not 23 shared measured
channels: VU TP9'/TP10' are always interpolated, with 2-3 extra missing sites
in three reserved people handled by the specified metadata-only policy.
Final numerical source is `natview/v2/machine_summary.json`, with the root
NATVIEW experiment note and worker reporting package. Reconcile exact event
maps, interpolation and denominators from those artifacts. Final-release
flags remain false until coordinator approval of NATVIEW metrics and report.

M3 methods now specify the same **300 EEG-power features** for matched ridge
and small-MLP arms (plus ECG timing/availability where selected), not raw EEG
waveform learning. The 96 fitted outer cells are not independent studies.
The UnEBOLT schematic remains a published reference, not a reproduced model.

Bundled runtime paths (resolved with load_workspace_dependencies):

```powershell
& 'C:/Users/Seamus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' scripts/build_thesis_exploration_poster.py --final
& 'C:/Users/Seamus/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe' -scale-to 2400 -singlefile -png output/pdf/EEG_fMRI_thesis_exploration_poster_A0.pdf output/pdf/EEG_fMRI_thesis_exploration_poster_preview
```

Add `--final` only after actual completed results and the reviewed report are
ready. The PDF artifact marker ran successfully **exactly once immediately
before the first PDF-authoring command** for this new poster. Do not repeat
the marker for iterative rebuilds in this operation.

Final output path is stable; the currently saved artifact at that path is
clearly marked internal draft. There is no claim that the final scientific
poster is complete. Render and visually inspect the entire latest page after
any text/results update; inspect the charts at greater magnification too.
Text wrap bounds raise on overflow. Confirm one-page A0, embedded fonts,
valid participant intervals, no mixed-metric plot and no obsolete draft labels
before delivery. Primary/learning paths have been checked with real data;
the NATVIEW numeric/visual check awaits its actual evidence. Print the reviewed
PDF at 100% A0.

No changes were made to the old poster, old builder or research report; no
git commit or push was performed.

## Final release record

The final build used --final and an explicitly absent optional --reference-pdf
path to verify a complete build without private examples. The build manifest
records `not loaded; recorded verified SHA256 and measured geometry` and
`reference_content_embedded: false`. Default rebuilds also work when the ignored
private reference folder is absent; no copy is needed or republished.

NATVIEW's reviewed regional r is .1038126, 95% person-bootstrap CI
[-.0001834, .2071132]; normalized-target predictive R2 is -.0713665. The
panel includes 740/2304 scored frames (32.1%) across all eight planned people,
with six contributing to the conditional accuracy mean. Strict v1 acceptance
remains 1/8; v2 acceptance is 6/8 after the metadata amendment. The exploratory
scope, pilot exclusion and interpolated target-site policy remain visible.
The six-person interval includes zero. No equality/site-cause/clinical claim
is inferred. No original example, report or model source was modified.

The main four-row comparison and four-point learning grid preserve the
outcome-independent selection. Rebuild validates native person means, worker
exports, nine successful M3 root jobs, separate NATVIEW jobs, model/protocol
hashes, all-eight coverage and review state. Release_checks.json records
single-page A0, embedded fonts, vector content, five active primary-source
links, no obsolete draft labels, exact output/source hashes and visual QA.
No git stage, commit, push or publication was performed.
