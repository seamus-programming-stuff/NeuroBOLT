# Introductory honours EEG project: reuse and learning scope

Local review: 26 October 2026. **Recommendation: one student builds and explains a small, reproducible EEG-feature regression benchmark: ridge, a small MLP, and one fixed tiny transformer predicting one global BOLD time course.** A sound comparison and an honest negative result are sufficient outcomes; improved accuracy is not a graduation requirement. This is an introductory CS/AI project proposal. The 12 weeks below are a planning example, **not a claim about Monash's official honours duration or requirements**.

Review boundary: local sources and existing numerical exports, at repository HEAD `e0ae415445d87a16a54fdf87c12aecc2ef1549f4`. No new model fits, cluster submissions, downloads, commits, pushes or publication were performed. The earlier poster/guide explicitly propose a PhD programme; reuse their explanations and evidence, not their three-part research agenda. [Earlier guide][guide]

## 1. What can students reuse, and what do the existing results actually establish?

### Takeaway

The compact paired feature cache, frozen person splits, scoring code, numerical exports and browser replay already provide a practical starting point. The strongest verified headline is modest retrospective prediction on development data, with substantial limitations in amplitude, regional detail and generalization. [Cache][cache]; [protocol][protocol]; [scores][people]

### Cited Findings

#### Concrete reuse register

All linked source paths are absolute. Repository root: `C:/Users/Seamus/Documents/GitHub/NeuroBOLT`. “Reuse” means proposed future student work; this review did not copy or change these assets.

| Reusable asset and exact source link | What to reuse; boundary |
| --- | --- |
| [reports/thesis_exploration/data/features_causal.npz][cache] | **Preferred starting data**, 3,756,893 bytes. Contains 54 runs, 27 people, 9,544 retained frame rows, 65 target labels. Each run has `eeg_<run>` (N×300), `phys_<run>` (N×24), `y_<run>` (N×65), `frame_<run>`, `onset_<run>`, `fd_<run>`. These are derived paired EEG/BOLD data, not raw EEG or independent people per row. |
| [reports/thesis_exploration/data/manifest_inventory.json][inventory] and [feature_qc.json][qc] | Inventory, raw/cache provenance, sensor identities and exclusions. The inventory identifies the staged 27-person paired subset, not the size of the whole public release. Raw source paths recorded here point to M3; they are provenance, not proof those files exist on this laptop. |
| [reports/thesis_exploration/data/protocol.json][protocol] and [training_frame_manifest.csv][frames] | Reuse exact people and frame accounting. Three folds each have nine test people, four separate validation people and a 14-person training pool; the selected high-resource arm uses its first 12. All sets are disjoint within each fold; all 27 people occur in test exactly once. Training manifests have 540 rows across reused conditions, not 540 participants. |
| [scripts/thesis_data.py][data-code] | Feature definition, channel grouping, bands, timing and protocol construction. **Read the feature routine; do not rebuild raw preprocessing for the MVP.** |
| [scripts/thesis_study.py][study-code] | Training-only transforms, ridge selection, grouped validation weights, metrics and frame handling. Adapt a small single-target runner in future student-owned files. Existing MLP predicts 193 outputs and its entry point requires GPU/profile artifacts, so running it unchanged is not the proposed laptop MVP. |
| [scripts/thesis_tests.py][tests] and [reports/thesis_exploration/data/synthetic_tests.txt][test-log] | Reuse meaningful checks: train-only transforms, group separation, actual frame gaps, future exclusion and correlation versus calibration. Existing log records ten passing tests; this review inspected that record rather than rerunning training. |
| [per_person_scores.csv][people], [summary.json][summary], [poster_scores.csv][poster-scores], [poster_learning.csv][learning] under `reports/thesis_exploration/data/` | Recompute headline tables and redraw a small result/learning plot. Preserve model, condition, target and aggregation labels. The 192 files in [data/cells](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/cells>) are 96 JSON/CSV pairs, not extra cohorts. |
| [artifact_hashes.sha256][hashes], [protocol.sha256][protocol-hash], [environment.json][environment], [verification.json][verification] | Provenance and environment starting point. This review checked all **227 listed artifact hashes**, feature/protocol hashes and all seven protocol-listed source hashes: all match. The saved environment is Linux/Python 3.9/Torch 2.0; a new local environment still needs a smoke check. |
| [reports/external/monitor.html][demo], [monitor_template.html][template], [data/demo.json][demo-data], [data/monitor_runs.csv][monitor-scores] | Existing selectable-run browser replay and 56-run derived data. Ready for a kickoff demonstration; not the output of the new transformer benchmark. HTML embeds its trace data but requests Google Fonts. The builder defaults to the **best EC run**; choose and label a fixed ordinary/poor run too. |
| [scripts/build_monitor_demo.py][demo-builder] | Shows demo data contract and best-run selection. The template separately z-scores measured and predicted traces, which makes shape visible but hides amplitude errors. Show predictive R²/amplitude alongside any such plot. |
| [app/README.md][app-readme], [app/arousal_monitor/model.py][app-model], [stream.py][stream], [monitor.py][monitor] | Research application structure, frozen-model inference, running statistics and flags. These provide teaching examples; using past EEG for a frame does not validate the entire acquisition/cleaning/flagging workflow as live or clinical. |
| [app/models/vu_model_bands60.npz][bands-model] and [vu_model_full.npz][full-model] | Actual local frozen ridge models, with weights shaped 60×65 and 13,728×65 respectively. **Neither accepts the 300-feature cache directly.** Keep this demo pipeline separate from the new benchmark. |
| [reports/thesis_exploration/guide_figures/correlation_scale.svg][math-figure] and [build_manifest.json][guide-manifest] | Reusable teaching figure: perfect correlation yet predictive R² = −0.64. Explicitly mathematical/synthetic, not a participant recording. |
| [reports/external/ext_monitor_example.png][example-figure] and [ext_transfer.png][transfer-figure] | Existing data figures. Visually inspected monitor example is **sub-019 EC, r≈0.49**, a selected good run, with relative vigilance flags. It is not typical performance or an independently verified sleep episode. Transfer plot belongs to the older 28-person study. |
| [output/pdf/EEG_fMRI_thesis_exploration_poster_preview.png][poster-preview], [reports/thesis_exploration/README.md][poster-readme], [scripts/build_thesis_exploration_poster.py][poster-builder] | Reuse pipeline/result explanations or numeric sources. Preview inspected: its title, clinical question and “PhD opportunity” panels need replacement for an honours kickoff; do not present the whole poster as this project brief. |
| [models/model.py][neurobolt-model], [models/model_multiscale.py][multiscale], [main.py][main], [scan_split_cv5.xlsx][vu-splits], [scripts/make_cv_splits.py][split-code] | Optional original NeuroBOLT architecture/split reading. These VU splits are distinct from the compact cache's three folds. Full reproduction, pretrained encoder training and architecture migration are outside the MVP. |

There is also one local raw example: [sub16-scan01_eeg.set](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/data/EEG/sub16-scan01_eeg.set>), its [companion .fdt](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/data/EEG/sub16-scan01_eeg.fdt>) and [paired ROI pickle](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/data/fMRI_difumo/sub16-scan01_difumo64_roi.pkl>). File inventory confirmed these, and [checkpoints/Thalamus.pth](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/checkpoints/Thalamus.pth>) exists. These files were not loaded or validated in this review; one scan is useful for inspection/inference, not a population evaluation. Preserve source attribution and the repository's [LICENSE](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/LICENSE>) in any eventual handover.

#### Verified headline findings, with their scope

The following are **old results**, independently recomputed here from the 27 corresponding person rows per arm. Panel: ds006040, EC training/EC evaluation, 12 training people × 240 retained target-seconds/person, 64 regional targets. Correlations average across regions within person, then across people. [Person rows][people]; [panel export][poster-scores]

| Existing arm | Mean temporal r | Mean predictive R² |
| --- | ---: | ---: |
| Ridge EEG | 0.188609 | 0.027883 |
| Tiny MLP EEG | 0.122349 | 0.006781 |
| Ridge EEG + ECG timing/availability | 0.178236 | 0.023090 |
| Ridge ECG timing/availability | 0.017686 | −0.004406 |

- Saved exploratory 95% person-bootstrap intervals for ridge EEG are r **[0.14879, 0.22646]** and R² **[0.01163, 0.04299]**. Its predicted/observed SD ratio is **0.16150**, and five of 27 people have negative mean regional R². The intervals were read from the existing summary; the means, SD ratio and negative-person count were independently recomputed. [Summary][summary]; [person rows][people]
- Existing ridge learning-grid r values are **0.08885, 0.14447, 0.14186, 0.18861** for (4 people,120 s), (4,240), (12,120), (12,240), verified against person rows. Longer nested early segments change both duration and content. This is a bounded resource comparison, not a scaling law. At nominal 240 retained seconds, actual target acquisition spans reach 330 seconds because of gaps. [Learning export][learning]; [frame manifest][frames]
- Ridge's predicted-global regional template reaches r **0.18451**; full-region minus template Δr is **0.00410**, with saved interval **[−0.00813, 0.01680]**. Regional advantage is uncertain. The existing MLP shares four target-group objectives across 193 outputs, while ridge fits outputs independently: its loss does not prove that nonlinear models are unnecessary. [Summary][summary]; [implementation][study-code]
- Older demo scores are a different evaluation: **28 people/56 runs**, EC global r **0.25473 offline / 0.26291 streaming**, EO **0.17071 / 0.16094**, independently recomputed from `monitor_runs.csv`. These are not the 27-person regional benchmark and are not evidence that low-vigilance flags detect sleep. Earlier wording such as “no site penalty” and “works live” should be replaced by a precise account of this retrospective evaluation. [Monitor rows][monitor-scores]; [older report][external-report]; [app limitations][app-readme]
- NATVIEW is an optional failure-analysis case study: strict v1 admitted one of eight; amended v2 evaluated six, with regional r **0.10381**, predictive R² **−0.07137**, and 740/2,304 possible frames scored. V2 followed QC findings and is secondary exploratory, not the original untouched confirmation. Values were checked in the saved machine summary/guide, not re-estimated from raw recordings. [NATVIEW record][natview]; [v2 summary][natview-summary]; [coverage explanation][guide]

### Inferences

Start from the 3.8 MB cache and scalar global target. This removes raw-data acquisition, scanner synchronization, artifact cleaning and atlas extraction from the student's critical path while preserving supervised learning, temporal features and person-level evaluation. The cache has a global label `global signal clean` at index 64; select by label and assert its identity. Existing high-resource ridge global scores are r≈0.27650 and R²≈0.06513, **different endpoints** from the regional headline above. [Cache][cache]; [person rows][people]

### Gaps

This was a source/array/summary audit, not an end-to-end reproduction. Raw recordings were not inspected, prospective preprocessing was not verified, and no independent sleep labels were found in this compact study. The 42 high-resource prediction archives described in the execution record are **not in the local `data/predictions/` directory**, which is absent; person summaries remain available. [Execution record][m3-note]

Only directory names were inventoried under `C:/Users/Seamus/Documents/GitHub`: `a01_sportsgame`, `a01_sportsgame2`, `a01_tankgame`, `a01_tankgamev176`, `learnharness`, `NeuroBOLT`, `neurogrip`, `sel-internal-tools`, `WebApp`. No sibling project contents were crawled. Names alone do not establish reusable EEG assets; recommend none without a separate authorized review. [Inventory location](<C:/Users/Seamus/Documents/GitHub>)

## 2. What is the minimum viable project, and how could a small team extend it?

### Takeaway

One student can own the entire small pipeline and explain every transformation. A team should share the same data and interfaces, with each person owning an understandable component; three independent advanced research programmes are unnecessary.

### Cited Findings

The existing code already supplies train-only imputation/scaling, small-model training, scoring and fixed subject folds. The earlier experiments used past-context features but inherited retrospective cleaning, whole-run target normalization/filtering and future-margin frame QC. Reusing these assets supports an **offline development benchmark**, not a new prospective validation. [Study code][study-code]; [feature code][data-code]; [QC][qc]

### Inferences — proposed student work, not completed results

#### One-student MVP and bounded transformer comparison

**Question:** “On identical past-EEG features and held-out people, does a tiny attention model improve global-BOLD prediction relative to ridge and an MLP, and what does the comparison teach us?”

1. **Fix one task:** EC only; global target; 300 EEG features; existing three folds; first 12 training people and first 120 eligible frames/person (240 retained target-seconds). Use all eligible EC validation/test frames from those folds. No ECG arm, residual targets, external dataset or clinical classifier in the core project.
2. **Fit preprocessing only on selected training rows:** median imputation, feature mean/SD and target mean/SD. Restore original cached target units before scoring. Keep original subject/run/frame identities and gaps. Validation chooses settings/epochs; outer test never does.
3. **Use three bounded estimators:** ridge with the existing six penalties `{0.1,1,10,100,1000,10000}` chosen by equal-person validation MSE; MLP `300 → 32 GELU → 1`; transformer with 12 temporal tokens, 25 values/token, linear embedding to width 32, fixed positional encoding, one encoder layer, two heads, feedforward width 64, dropout 0.1, mean pooling and one scalar head. Cap the transformer at 20,000 trainable parameters and record the actual count. These are proposed teaching configurations, not claims about optimal models.
4. **Respect the stored layout:** the feature code flattens **[scalp group, band, lag]**. Convert `[N,300] → [N,5,5,12] → transpose to [N,12,5,5] → [N,12,25]`. A direct reshape to `[N,12,25]` scrambles token meaning. Add an index-coded round-trip check. All 12 tokens precede the target endpoint; this scalar prediction does not need a next-token autoregressive objective. [Feature definition][data-code]
5. **Limit training:** neural seed 41; AdamW, learning rate 0.001, weight decay 0.01, batch 128, maximum 60 epochs, patience 10. Same single-target standardized MSE and equal-person validation criterion for both neural models. Three folds mean **18 ridge penalty evaluations + three MLP fits + three transformer fits**. No architecture sweep. Profile one validation-only fit; propose a four-hour total fitting ceiling on agreed hardware, reducing scope before outer scoring if needed. This is a budget, not a measured runtime promise.
6. **Evaluate once after freezing the specification:** primary mean per-person **raw predictive R²**; secondary Pearson r, RMSE, predicted/observed SD ratio, undefined-r count and fraction of people with negative R². Include a training-mean predictor. Average people equally. Report paired per-person differences and exploratory person-bootstrap intervals, acknowledging shared training sets and one seed. Never treat windows, folds or repeated seeds as independent participants.

**Deliverables:** a short frozen protocol and source/data hashes; a small readable runner; per-frame predictions with identifiers; per-person scores; one model comparison plot and one trace in common target units; a research-replay demonstration; a concise explanation of failures. The student must reproduce the historical regional table from its CSV as a provenance exercise, but **new single-global-target MLP results are not directly comparable to the old 193-output MLP's regional score**. [Historical objectives][protocol]

**Success:** another student can rerun the benchmark, all split/transform/layout checks pass, and the author can explain the results without AI assistance. A transformer tie or loss is a successful learning outcome. If implementation remains unreliable at the week-6 gate, deliver the verified ridge/MLP benchmark and document the transformer attempt as incomplete; do not quietly present a reduced project as a completed three-model comparison.

**Defer:** new sensor acquisition, foundation-model pretraining, reproducing UnEBOLT/UniEFS/MARBLE, patient recruitment, clinical thresholds, mathematical observability guarantees, domain adaptation and calibrated abstention. The earlier report supplies background for those topics, not prerequisites for this introductory project. [Earlier proposal][guide]

#### Compact extension for three or four students

| Owner/package | Bounded responsibility | Integration contract and acceptance |
| --- | --- | --- |
| A — data and evaluation | Wrap the existing cache, folds, train-only transforms and metrics. | One versioned manifest containing feature/protocol hashes and exact frame keys. Loader returns `X[N,300]`, `y[N,1]`, `subject`, `run`, `frame`, `onset_s`, split role. No subject overlap; no dropped rows without a logged reason. |
| B — models | Implement ridge/MLP/tiny transformer using A's arrays. | Shared `fit(train, validation, config)` and `predict(X)` interface; predict accepts no measured targets. Save config, preprocessing, seed, epoch, parameter count and timing. Every model emits exactly the same requested row keys. |
| C — explanation and demo | Build understandable plots and an annotated replay from saved outputs. | Consume predictions only; no fitting or metric redefinition in the UI. Distinguish measured reference, estimate, missing frames, synthetic examples and historical demo. Include an ordinary and poor run under a declared selection rule. |
| Optional D — robustness audit | Repeat neural seeds 42/43, or one frozen EC→EO check; choose one. | Same interfaces, frame accounting and metrics. Report seed variation or condition shift separately; keep the core EC task unchanged. No tuning on EO outcomes. |

Three students cover A/B/C; a fourth takes D. Integrate a tiny fixture by week 2, valid ridge predictions by week 4 and all model outputs by week 7. Freeze the interface rather than passing undocumented arrays between students. For the new benchmark use prediction columns `study_id, fold, seed, model, subject, run, frame, onset_s, y_true, y_pred`; run A's scorer centrally. Existing demo uses a different JSON schema (`t`, `vigilance_z`, `pred_global`, `measured_global`, `episodes`, `r`); adapt explicitly. [Existing demo data][demo-data]

### Gaps

Supervisor agreement, student prerequisites, hardware availability and assessment expectations are not established by these repository files. Confirm them at kickoff. The proposed tiny transformer and its runtime are not implemented or measured here. No claim of an untouched new cohort is available merely by re-splitting these previously inspected data.

## 3. How should the example schedule build understanding and support the kickoff?

### Takeaway

Use each deliverable as a teach-back checkpoint. The project should leave the student able to explain and debug a small AI experiment, including why an attractive plot can be misleading.

### Cited Findings

The existing teaching example has `prediction = 0.2 × target + 1` for a mean-zero, unit-variance target: r=1 but predictive R²=−0.64. Existing tests explicitly check group separation, train-only transforms and future exclusion. These are immediately reusable teaching materials. [Worked figure/manifest][guide-manifest]; [tests][tests]

### Inferences — example planning and assessment

#### A 12-week planning example

| Week | Concrete output | Student teach-back, without an AI-generated script |
| --- | --- | --- |
| 1 | Load cache; explain one run and target; agree scope. | What do EEG, BOLD, a frame, a run and a person mean? What remains a prediction? |
| 2 | Print disjoint folds and a small loader fixture; team integrates fixture. | Why can two recordings of one person not straddle train and test? |
| 3 | Train-only preprocessing and training-mean predictor; implement metrics. | Derive predictive R² and work through r=1/R²=−0.64. |
| 4 | Ridge validation result, penalty explanation and export contract. | What does regularization do to correlated features? Which data chose alpha? |
| 5 | Small MLP and train/validation learning curves. | Explain a forward pass, gradient update and overfitting; identify what early stopping sees. |
| 6 | Tiny transformer on validation; feature-layout check; scope/budget gate. | Draw 12 tokens, explain Q/K/V, attention weights, positions and the scalar head. |
| 7 | Freeze task, metrics, configs, seeds, code/data hashes and run-selection rule. | Which decisions remain allowed after viewing outer scores? Why is this still development data? |
| 8 | One locked outer evaluation; per-person score table and failures. | Explain one person's error in original target units, then the group aggregation. |
| 9 | Paired comparison plot and uncertainty explanation; optional D audit. | Why do thousands of windows not make thousands of independent people? |
| 10 | Annotated saved-output replay with ordinary and poor cases. | What changes when each trace is separately z-scored? Are flagged periods sleep labels? |
| 11 | Rerun/handover check and draft concise findings. | Trace one plotted number to its rows, fold, transform, model and source hash. |
| 12 | Short presentation and demonstration; reflection on AI assistance. | Defend one design choice, diagnose one failure and state one claim the evidence cannot support. |

#### Pitfalls that must appear in the student's own explanation

- **Repeated held-out test use:** VU/ds006040 and the NATVIEW amendments already have a research history. Freezing a student protocol limits further adaptation; it does not restore historical independence. Reproducing an old test result is useful education. Repeatedly choosing architectures from that result is test-guided development, not fresh confirmation. Keep all such use explicit. [Development protocol][protocol]; [NATVIEW history][natview]
- **r versus predictive R²:** use `1 − Σ(y−prediction)² / Σ(y−mean_evaluation_y)²`, as in the existing scorer, per person/run. The evaluation mean defines the denominator; it must not become a prediction-time input. Also show the deployable training-mean baseline. Pearson r is invariant to positive scale/offset; predictive R² can be negative and is not r². [Scorer][study-code]; [math example][math-figure]
- **Samples versus people:** 9,544 overlapping frame rows, 54 runs, 27 people and 96 historical fitted cells count different things. Resample people for exploratory uncertainty, keep all runs of a person together, and disclose overlapping training sets. [Cache][cache]; [protocol][protocol]; [verification][verification]
- **EEG-only versus paired data:** inference can consume EEG alone; training and accuracy assessment here need simultaneous paired BOLD targets. EEG-only patient classification data, unrelated fMRI pretraining or a vigilance index cannot verify reconstructed patient BOLD. This project uses the existing paired cache; it does not create a new patient dataset. [Cache/target construction][data-code]; [earlier evidence distinctions][guide]
- **Offline versus live:** past-only feature values do not make inherited artifact cleaning, target processing or exclusion rules prospective. Compute milliseconds exclude acquisition, cleaning and physiological delay. A displayed replay is a saved-data demonstration. [QC limitations][qc]; [stream implementation][stream]
- **No clinical promise:** no independent sleep scoring or clinical outcome validation is supplied for the compact benchmark. Label outputs “research estimate”; flags remain unvalidated relative thresholds. Do not promise MRI replacement, diagnosis, treatment benefit or safe alarms. [App limitations][app-readme]; [guide][guide]

#### Transparent human and AI roles

The student owns the question, data interpretation, mathematical explanations, code review and final claims. A supervisor checks scope and evaluation; physiological/clinical questions require an appropriately qualified collaborator rather than an AI answer.

AI may explain concepts, draft small functions, suggest debugging checks or help edit captions. Keep a brief assistance log: date, tool/model if known, task, accepted changes, checks performed and what the student corrected. For each major component require a teach-back plus a small unaided modification or bug diagnosis. AI-generated claims must be traced to the actual source/data; generated code must pass the meaningful split, transform, shape and metric checks. Do not send participant material to an external AI service without the project's applicable authorization. These are proposed teaching practices, not claims about a university policy.

#### Compact 12-slide kickoff map

| Slide | Focus |
| --- | --- |
| 1 | One question: compare three small estimators on one EEG→global-BOLD task. |
| 2 | EEG, BOLD and paired observations; inference differs from training. |
| 3 | Exact ready-to-use cache, scripts, manifests and replay. |
| 4 | Verified historical result: ridge r≈.189, predictive R²≈.028, with scope. |
| 5 | Worked correlation-versus-error figure. |
| 6 | People, runs, windows and disjoint split diagram. |
| 7 | Student MVP: pipeline, deliverables and what counts as success. |
| 8 | Tiny transformer tokens versus ridge/MLP; fixed fitting budget. |
| 9 | Demo of selected ordinary/poor runs; distinguish old replay from new model output. |
| 10 | Example 12-week schedule and teach-backs. |
| 11 | Optional A/B/C(+D) team packages and shared contract. |
| 12 | Limitations, AI disclosure and immediate kickoff decisions. |

### Gaps

The schedule and slides are proposed teaching structures, not an official course calendar or an implemented deck. Before any future student experiments, agree available time, compute ceiling, assessment rubric, source/data permissions and who will verify domain interpretations. If the goal is stronger independent evidence later, identify genuinely reserved people/data and a separate frozen evaluation; it is not needed to finish this introductory learning project.

[guide]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/poster_reading_guide.md>
[cache]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/features_causal.npz>
[protocol]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/protocol.json>
[people]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/per_person_scores.csv>
[inventory]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/manifest_inventory.json>
[qc]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/feature_qc.json>
[frames]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/training_frame_manifest.csv>
[data-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/thesis_data.py>
[study-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/thesis_study.py>
[tests]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/thesis_tests.py>
[test-log]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/synthetic_tests.txt>
[summary]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/summary.json>
[poster-scores]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/poster_scores.csv>
[learning]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/poster_learning.csv>
[hashes]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/artifact_hashes.sha256>
[protocol-hash]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/protocol.sha256>
[environment]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/environment.json>
[verification]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/verification.json>
[demo]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/monitor.html>
[template]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/monitor_template.html>
[demo-data]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/data/demo.json>
[monitor-scores]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/data/monitor_runs.csv>
[demo-builder]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/build_monitor_demo.py>
[app-readme]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/README.md>
[app-model]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/arousal_monitor/model.py>
[stream]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/arousal_monitor/stream.py>
[monitor]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/arousal_monitor/monitor.py>
[bands-model]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/models/vu_model_bands60.npz>
[full-model]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/app/models/vu_model_full.npz>
[math-figure]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/guide_figures/correlation_scale.svg>
[guide-manifest]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/guide_figures/build_manifest.json>
[example-figure]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/ext_monitor_example.png>
[transfer-figure]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/external/ext_transfer.png>
[poster-preview]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/output/pdf/EEG_fMRI_thesis_exploration_poster_preview.png>
[poster-readme]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/README.md>
[poster-builder]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/build_thesis_exploration_poster.py>
[neurobolt-model]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py>
[multiscale]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py>
[main]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py>
[vu-splits]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scan_split_cv5.xlsx>
[split-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/make_cv_splits.py>
[external-report]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/NeuroBOLT external validation.md>
[natview]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/natview/README.md>
[natview-summary]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/natview/v2/machine_summary.json>
[m3-note]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Clinical EEG fMRI thesis exploration/M3 experiments.md>
