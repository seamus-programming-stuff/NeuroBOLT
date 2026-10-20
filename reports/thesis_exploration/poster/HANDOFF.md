# Final poster ready

The final PDF and 2400-pixel preview are at the requested stable output/pdf
paths. The complete page was rendered and visually inspected. It directly
mirrors example2's measured A0 geometry, cyan banner, asymmetric columns,
orange divider/boxes and cyan author line. The poster remains explicitly
PhD thesis exploration; reviewed file status is not clinical validation.

The main figure has the four outcome-independent ds006040 rows in their
preselected order. All 27 held-out person means, intervals and selected cells
were checked against native summary/person CSV and both worker poster exports.
Methods state 300 matched EEG-power features and 96 fitted outer cells; the
small MLP does not see raw waveforms or reproduce UnEBOLT. The published
UnEBOLT schematic is labelled reference/unrun. Regional increment over the
predicted-global template remains uncertain.

The NATVIEW inset separately preserves strict timing QC 1/8 and amended
secondary exploratory QC 6/8, pilot exclusion, r .104 with 95% CI
[-.0002,.207], normalized predictive R2 -.071 and 740/2304 scored frames
(32.1% of all eight). The CI includes zero. Its point, interval and scale are
not pooled with ds006040. The frozen VU model/thresholds and interpolation
of target sites are explicit. Native per-person means, six/two partition,
frame counts, model/protocol/freeze hashes and scoring/reporting jobs were
independently checked. Full details remain in the reviewed report and notes.

All three review flags are true under the parent's authorization once the
writer removed DRAFT/PENDING from the final report. Its exact SHA256 is locked
in integration.json. No further child notification was required. The final
PDF has no draft/pending placeholders. Five numbered source references link
to primary proceedings/regulatory/guidance pages.

Rebuild with the bundled Python:

    python scripts/build_thesis_exploration_poster.py --final

Then render with Poppler as in DESIGN.md. The private examples are optional:
measured geometry and the constant verified reference SHA256 are sufficient.
A present reference is verified; an absent reference is recorded as not
loaded. The final build explicitly exercised that absence without copying,
embedding or republishing any original example. Do not rerun the PDF marker:
it already ran once immediately before this poster's first authoring command.

Editable source: scripts/build_thesis_exploration_poster.py, content.json,
integration.json. Exact geometry/provenance: DESIGN.md and build_manifest.json.
Source audits: native_audit.json and natview_audit.json. Release QA, links and
output/source hashes: release_checks.json (also qa.json).

No old poster/research report was edited. No git stage, commit, push or
publication. The parent handles publication.
