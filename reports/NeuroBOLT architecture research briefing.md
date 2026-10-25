# NeuroBOLT architecture guides the next experiment

**NeuroBOLT predicts regional BOLD from preceding EEG by adding two pooled representations: a waveform transformer and a multiscale spectral encoder.** The audited implementation makes a specific next experiment possible: replace unrestricted spectral window mixing with an explicitly aligned lag grid, keeping the remaining model fixed. Completed five-fold evaluation across 22 people favours lagged-power ridge over the tested NeuroBOLT models; this supports a demanding baseline, not a universal ceiling. UnEBOLT, UniEFS and MARBLE suggest regional conditioning, retained tokens and learned fMRI priors, but their published scores concern different targets and resources. A feasible two-week project should explain the actual architecture, implement one controlled change and present results or a documented negative finding. A new exploratory cache pilot also favours ridge; it does not test the proposed NeuroBOLT change. Public paired data support the core; prospective Emotiv access is optional.

## 1. Read the architecture through one research question

**Central question: can a physically explicit spectral lag representation improve NeuroBOLT's prediction of measured BOLD in unseen people, beyond its current encoder and a strong ridge baseline?** Read Sections 2–4 for the computation, Sections 5–6 for evidence, and Sections 7–10 for the proposed investigation. Sections 11–13 support discussion and presentation.

EEG measures voltage differences at scalp electrodes, mixing electrical sources. BOLD is a slower MRI signal influenced by neural activity, vascular responses and systemic state. An ROI, or region of interest, summarizes a specified brain region into one value per MRI frame. Predicting successive ROI values estimates a time course; it does not recover an anatomical or diagnostic scan. Delayed haemodynamics motivate using seconds of EEG history. ([NeuroBOLT paper](https://arxiv.org/html/2410.05341v2))

Evidence is distinguished as **audited code**, **completed local experiment**, **published result**, or **proposal**. Implementation claims follow local commit **240e8c5**, overriding older narrative descriptions. ([Code audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md))

<!-- page -->

## 2. Two encoders summarize the same EEG window

<!-- figure: neurobolt -->

A tensor is an array whose axes describe batch, channel, time or features. Let `B` denote batch size, `W` history in seconds and `R` output regions. At 200 Hz, the default 16-second input contains 26 channels and 3,200 samples/channel. The engine divides microvolt inputs by 100 and groups them into channel-second patches. ([Input handling](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/engine.py#L72))

| Stage | Default tensor | Meaning |
| --- | --- | --- |
| Input and reshape | `[B,26,3200]` → `[B,26,16,200]` | Sixteen one-second patches per electrode. |
| Temporal convolution | `[B,416,200]` | 26 × 16 data tokens, each with 200 features. |
| Temporal transformer | `[B,417,200]` | Adds one CLS token; 12 blocks, 10 heads. |
| Temporal readout | `[B,200]` | Mean of 416 non-CLS tokens, then LayerNorm. |
| Spectral encoder | `[B,832,200]` | 26 × 32 spectral tokens; **no CLS**. |
| Spectral readout | `[B,200]` | Mean after four linear-attention layers. |
| Fusion and head | `[B,200]` → `[B,R]` | Elementwise addition, GELU, linear prediction. |

The temporal convolution converts each channel-second into a token: its first layer produces eight feature maps with 25 positions, flattened into 200 features. Electrode and time embeddings identify token locations. Attention compares learned queries and keys to combine value features; subsequent feed-forward layers transform them. CLS participates in attention but is excluded from default averaging. **Fusion adds the two vectors; it does not concatenate them.** The original recipe trains separate one-output models; the shared local arm has seven outputs. ([Audited temporal model](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/models/model.py#L233))

LaBraM supplies EEG-pretrained initialization, not an already learned EEG-to-BOLD mapping. Positional encoding and attention operate before pooling, so mean pooling does not prove that temporal order has disappeared. ([LaBraM source](https://github.com/935963004/LaBraM))

<!-- page -->

## 3. Spectral tokens have learned indices, not explicit lag bins

The spectral branch computes four short-time Fourier transforms, or STFTs, separately for each channel. Short windows locate changes more precisely; long windows distinguish frequencies more finely. The implementation uses nonoverlapping windows, `center=False`, no supplied taper, and **complex magnitude**, not squared power or log power. Its optional log arm applies `log1p` to magnitude. ([Spectral source](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/models/model_multiscale.py#L94))

| STFT window at 200 Hz | Frequency bins | Frames: 16 s / 24 s |
| --- | ---: | ---: |
| 100 samples: 0.5 s | 51 | 32 / 48 |
| 200 samples: 1 s | 101 | 16 / 24 |
| 400 samples: 2 s | 201 | 8 / 12 |
| 800 samples: 4 s | 401 | 4 / 6 |

Each scale projects frequency bins into 200 features. `PatchWindowEmbedding` then applies a **dense learned map across its entire window axis**, giving every scale a common length `M=2W`. The four scale embeddings are summed per electrode. Electrode identities and sinusoidal positions are added, and electrode sequences are concatenated before linear attention and averaging. An output position can mix all input windows; it is not an interpolation onto a physical timestamp. Nevertheless, dense maps can learn lag-dependent combinations.

At 24 seconds, the spectral sequence contains **1,248 tokens**; the temporal sequence has **624 data tokens plus CLS**. Both still produce 200-feature summaries. The inspected default linear-attention dependency does not enforce a hard 1,024-token limit on this path; that constructor setting does not invalidate the completed 24-second runs. ([Audit and dependency check](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md))

Ridge instead uses Welch **log-power** features over channel, frequency band and lag. It fits a weighted sum with a penalty shrinking coefficients. Thus ridge versus NeuroBOLT changes representation as well as estimator; it is not a clean linear-versus-nonlinear test on identical inputs. ([Ridge implementation](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/scripts/baseline_ridge.py#L98))

<!-- page -->

## 4. Training and preprocessing determine what the model learns

Training minimizes **mean squared error (MSE)** over examples and outputs. The local experiment recipe uses AdamW, peak learning rate .0003, weight decay .05, batch 64, up to 30 epochs and validation-MSE early stopping. Three historical seeds are used. ([Recipe](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/scripts/hypotheses_m3.sbatch#L57))

**The temporal backbone is not explicitly frozen.** Layer decay .65 gives its earliest parameter group a peak learning rate about 1.11 × 10⁻⁶, versus 3 × 10⁻⁴ for the spectral encoder/head. The time embedding also receives the full rate. Small updates, permitted gradients and useful predictive contribution are different properties. ([Optimizer mapping](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/optim_factory.py#L33))

| Audited seven-output configuration | Allocated trainable parameters | Active spectral + head |
| --- | ---: | ---: |
| 16-second window | 7,908,191 | 2,088,255 |
| 24-second window | 7,912,255 | 2,090,719 |

At 16 seconds, allocation comprises 5,819,936 temporal, 2,086,848 spectral and 1,407 head parameters. Skipping a branch leaves its modules allocated, so a generic parameter total overstates active computation. Counts exclude buffers and nontrainable indices. ([Construction audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md))

EEG windows undergo channel-mean baseline subtraction; cross-person loading defaults to .5-Hz high-pass filtering. BOLD targets undergo fifth-order .15-Hz Butterworth filtering with `filtfilt`, demeaning, and division by the scan's **95th percentile of absolute demeaned amplitude**, not standard unit-SD z-scoring. Whole-run processing and inherited artifact correction make this retrospective estimation, even though input windows precede their target. ([Loader](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/dataset_maker/get_datasets.py#L257), [normalization](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/dataset_maker/preproc.py#L5))

Future comparisons need validation-only selection: current training evaluates test each epoch, and checkpoint saving has an additional positive-test-correlation gate. Historical hypothesis runs disabled checkpoint saving. Preserve actual scan boundaries rather than assuming equal-length evaluation batches.

<!-- page -->

## 5. Completed tests favour ridge within their studied scope

<!-- figure: results -->

The historical record contains **33 NeuroBOLT arms and 21 band-power variants**. The per-ROI 32-second arm stopped incomplete; the completed shared 32-second model is different. The old table's “still running” missing-row footnote is stale. ([Completed experiment record](NeuroBOLT%20hypothesis%20tests.md))

| Five-fold VU evaluation: 22 people, seven outputs | Mean temporal r | Interpretation |
| --- | ---: | --- |
| Ridge: fine-bin power, 24 s, 12 lags | **.381** | Strongest of these matched evaluations. |
| Shared NeuroBOLT, 24 s | .336 | Ridge leads in **19/22 people**. |
| Shared NeuroBOLT, 16 s | .323 | Longer history has uncertain average benefit. |

Ridge-minus-NB24 is **+.045**, paired 95% interval **+.023 to +.067**. NB24-minus-NB16 is +.013, interval −.003 to +.029. Repeated scans are averaged within person. The authors' original split is unusually favourable among these folds; it contains six test scans from five people. Reused folds and adaptive development still limit confirmation.

On that original split, shared full/spectral-only/temporal-only r values are **.462/.461/.024**. Removing layer decay raises temporal-only to .177, while full-model pretraining, normalization and learning-rate repairs produce little improvement. The reported **2% versus 91% embedding-variability diagnostic was not independently recovered in this audit**. It cannot establish that pooling caused the failure. Learned frequency bands, nonlinear feature heads and smooth distributed-lag/Hammerstein variants have also been tested; generic proposals to repeat them are insufficient. ([Code audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md), [additional completed tests](interpretability/tables.md))

**The separate ds006040 study used 27 people/54 runs and 300 engineered features.** Its primary regional ridge r/R² were .1886/.02788, versus .1223/.00678 for a joint-objective MLP. A predicted-global template reached r=.1845; regional improvement was uncertain. NATVIEW was already attempted: strict eligibility admitted 1/8 people; an exploratory amendment scored six, with 32.1% coverage and regional r=.1038/R²=−.0714. These are separate endpoints and pipelines, not new NeuroBOLT scores or evidence of a universal biological ceiling. ([Reviewed study](Clinical%20EEG%20fMRI%20thesis%20exploration.md))

<!-- page -->

## 6. Newer models change the readout and prior

**UnEBOLT** retains two pooled branches, learns a scalar fusion gate per example, then combines the shared EEG summary with each ROI identity through a residual adapter and separate head. It conditions an existing summary on a region; it does not retain separate spectral tokens for ROI attention. ([Pinned implementation](https://github.com/neurdylab/UnEBOLT/blob/09a382897b85820854ddd4e47a1f851fa43d32d9/models/unebolt_model.py))

**UniEFS**, published as *Mind the State*, retains EEG tokens and aligns them to a pretrained fMRI representation/decoder. Dataset, demographic and EEG-derived vigilance prompts provide context. Its fMRI pretraining uses 375 HCP people/1,500 scans; its main paired study uses 29 people/39 scans. Those populations must not be combined as paired supervision. Exact token plumbing remains unverified without released code. ([Final paper](https://raw.githubusercontent.com/mlresearch/v306/main/assets/li26gp/li26gp.pdf))

**MARBLE** uses overlapping Hann-window spectra, Mamba sequence processing and attention, without the LaBraM waveform branch. Learned ROI queries read retained channel–time tokens, producing region-specific summaries. Mamba introduces a memory bias; it does not identify a physiological haemodynamic response function (HRF). Attention weights are predictive computations, not causal brain-source maps. ([Pinned implementation](https://github.com/emeelkaa/marble/blob/28ae2ab16585f7a0cd57fcc961952661cce3e1d6/models/marble.py))

| Published experiment | Target and temporal r, mean ± SD | Within-paper comparator |
| --- | --- | --- |
| [UnEBOLT](https://raw.githubusercontent.com/mlresearch/v315/main/assets/li26g/li26g.pdf) | 64 ROIs: .418 ± .036 | NeuroBOLT .413 ± .052. |
| [UniEFS](https://raw.githubusercontent.com/mlresearch/v306/main/assets/li26gp/li26gp.pdf) | 512 ROIs: .367 ± .052 | NeuroBOLT .331 ± .044. |
| [MARBLE](https://papers.miccai.org/miccai-2026/paper/4437_paper.pdf) | 64 ROIs: .434 ± .047 | UnEBOLT .412 ± .049. |

**This is not a cross-paper ranking.** Main tests reuse VU, target resolutions/resources differ, and SDs are not confidence intervals. MARBLE's stronger temporal score did not give stronger FC-edge correlation than its UnEBOLT comparator. UnEBOLT/MARBLE combine MSE with temporal/spatial correlation losses; these are not explicit FC-matrix losses. None was reproduced in this project.

UnEBOLT/MARBLE code exists, but task-trained checkpoints were not verified. UniEFS lists code/data as forthcoming. MARBLE's paper and quick-start configurations differ; full reproduction needs author settings and environment checks. ([Release audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Frontier%20models%20and%20architecture.md))

<!-- page -->

## 7. First priority: make spectral lag positions physical

<!-- figure: alignment -->

**H1 proposes one actual NeuroBOLT change:** in spectral-only NB24, replace each dense scale-window map with a fixed support-overlap map onto 48 half-second bins. Each STFT frame contributes only where its physical support overlaps the grid. Preserve magnitudes, frequency projections, equal scale summation, embeddings, attention, mean pooling and MSE. This tests whether explicit alignment makes useful delays easier to learn. It does not assume the baseline lacks lag information. ([Audited change specification](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md))

The primary comparator is an unchanged spectral-only NB24 rerun on identical people, frames, seeds and optimizer. Fine-bin 24-second ridge remains the performance benchmark. Change the spectral mapping in `model_multiscale.py`, pass an option through `model.py`/`main.py`, and add support/shape checks plus validation-only execution.

**Capacity is a confound:** the four dense maps contain **4,512 parameters**. Fixed maps reduce the active spectral-plus-seven-output model from 2,090,719 to **2,086,207**. A gain could reflect regularization as well as physical alignment. A later local learned interpolation/capacity control can distinguish explanations if the primary comparison warrants it.

**Falsifier:** no validation error improvement over the matched spectral baseline, deteriorating amplitude/error despite higher r, or continued inferiority to ridge without useful efficiency benefit. Fixed maps can discard useful flexibility; coarse spectra already blur timing. An improvement would support an inductive bias on these data, not prove an HRF mechanism.

**Needs and feasibility:** staged waveform data, the existing spectral environment and modest profiled compute; implementation and limited comparisons fit the fortnight. MBI expertise is relevant to checking physical time support. This is the default because it isolates a small, auditable intervention.

<!-- page -->

## 8. Second and third priorities test regional information

### H2: retain tokens for ROI-query decoding

Expose spectral tokens before averaging. Project keys/values from 200 to 64 features; one learned query per ROI selects a weighted summary, followed by a shared scalar head. This adapts an established MARBLE-style mechanism; UnEBOLT supplies related ROI-conditioning precedent. It is not a claim to invent regional attention. ([MARBLE source](https://github.com/emeelkaa/marble/blob/28ae2ab16585f7a0cd57fcc961952661cce3e1d6/models/marble.py))

Compare with the same mean-pooled encoder, a similarly sized pooled MLP head, ridge and an EEG-predicted-global template. The proposed seven-query decoder has **26,241 parameters**, replacing a 1,407-parameter head; a pooled `200→127→7` MLP is a close capacity control. **Reject the hypothesis** if it only improves global tracking, loses raw R²/amplitude, or a pooled head matches it. Attention stability is diagnostic evidence only.

This needs token-return plumbing, regional targets and matched training; frozen-encoder comparisons additionally need a suitable validation-selected checkpoint. The local thalamus checkpoint is an intra-scan single-output model, not a shared cross-person substitute. H2 is optional only after H1 is complete. Turner modelling expertise could help define meaningful regional contrasts.

### H3: separate global prediction from regional residuals

As a future study, predict each ROI as a training-derived loading times **EEG-predicted global BOLD**, plus a learned regional residual. The completed near-tie with a global template motivates this decomposition. Compare direct multi-output, global-only and global-plus-residual heads with identical inputs/MSE. **Reject a regional-information claim** if residual/contrast R² stays non-positive or gains occur only in correlation/FC resemblance. Never supply measured test global BOLD as an input. ([Template evidence](Clinical%20EEG%20fMRI%20thesis%20exploration.md))

This needs enough paired regional variation and explicit outcome definitions. It suits later Turner/MBI interpretation work and remains outside the core fortnight. Large-scale EEG pretraining or montage robustness can become subsequent projects; combining them now would obscure the three hypotheses.

<!-- page -->

## 9. Evaluate people, timing and amplitude together

<!-- figure: evaluation -->

MSE penalizes magnitude errors. Pearson r measures cofluctuation while ignoring positive rescaling and offsets. Raw predictive R² compares squared error with a declared mean reference:

> R² = 1 − Σ(y − prediction)² / Σ(y − evaluation mean)².

Negative R² means worse error than that reference. For a zero-mean, unit-variance target, `prediction = .2 × target + 1` has r=1 but R²=−.64. Report RMSE, prediction/target SD ratio, negative-R² frequency and retained-frame coverage alongside r. The evaluation mean defines a scoring denominator; also include a deployable training-mean predictor. ([Teaching explanation](thesis_exploration/poster_reading_guide.md))

Keep every person's runs together; fit transforms on training data and select epochs/settings on inner validation. Aggregate scans/ROIs within person before equal-person comparisons. Thousands of overlapping windows or tokens do not create thousands of independent people. Person-based intervals remain conditional on fitted models and reused development choices. FC agreement is insufficient: applying the same time permutation to every ROI preserves FC while destroying event timing.

### The completed compact pilot answers a narrower question

**Verified status: M3 job 61455229 completed successfully; 10 tests passed, 12 model-fold fits and all 27 people evaluated.** [Protocol, results and verification records](architecture_briefing/pilot/20261026_ec_global_v1/README.md) document a separate exploratory scalar global-BOLD proxy comparison. Ridge gives raw R²=.065, MLP .038, mean-pool transformer -.032 and learned-pool transformer -.016. The appendix explains the uncertainty and amplitude errors.

Inputs are **300 log-power features**, reshaped into 12 lag tokens of 25 features, not NeuroBOLT STFT tokens. All models use scalar MSE, three existing folds and one fixed seed. The allocation used .06 GPU-hours and .24 CPU-hours, within the declared ceiling. This teaches compact estimator/readout comparison; it cannot validate H1, repair LaBraM, establish ROI-query superiority or supply fresh confirmation on previously explored data. ([Pilot protocol specification](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md))

<!-- page -->

## 10. Two weeks should complete one controlled investigation

Choose **H1 alone** as the primary architecture experiment. A negative result with verified execution and clear interpretation is a complete outcome.

| Period | Concrete output | Decision gate |
| --- | --- | --- |
| Days 1–2 | Annotated forward pass; fixed people, targets, frames, scoring and compute budget; interpret any verified pilot output. | Confirm staged waveforms and compatible preprocessing. |
| Days 3–4 | Default-off H1 option, support/shape checks, validation-only runner; profile unchanged/changed NB24. | Stop scaling if alignment or shared-frame checks fail. |
| Days 5–8 | Limited matched development folds/seeds; unchanged spectral baseline and ridge control. | Freeze scope before outer scoring; preserve failures. |
| Days 9–10 | Paired person results, amplitude/error panel, runtime and capacity discussion. | Decide H1 against its declared falsifier. |
| Days 11–14 | Reproducible configuration/results package and academic presentation. | H2 only if H1 is finished; otherwise finish analysis. |

No full foundation-model reproduction or new collection is required. If compute prevents a complete comparison, present the verified implementation, bounded partial execution and unresolved question explicitly. Do not pursue an outer-score-driven rescue grid.

**What you should be able to explain yourself:** trace one window through the tensor table; draw the support of a four-second STFT frame on the half-second grid; explain why r can rise while error worsens; and identify which people influenced each selection. Use AI to propose code, checks and alternative explanations, then inspect the time alignment, data contract and actual outputs. These demonstrations of understanding are part of the presentation deliverable.

<!-- page -->

## 11. Paired data support BOLD claims; Emotiv supports other roles

<!-- figure: data -->

| Resource | People and availability | Role and remaining work |
| --- | --- | --- |
| [VU](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT) | 22 people/29 scans; public EEG/DiFuMo-64 derivatives. | Existing architecture core; heavily explored development data. |
| [ds006040](https://openneuro.org/datasets/ds006040/versions/1.0.2) | Published 28 people; project analysed 27/54 rest runs. | Existing cache pilot; different features/targets from VU. |
| [NATVIEW](https://fcon_1000.projects.nitrc.org/indi/retro/nat_view.html) | 22 released people; eight-person transfer attempt already explored. | Timing amendment/QC are prior work, not a fresh test. |
| [MULTI-CLARID](https://github.com/OpenNeuroDatasets/ds005795/tree/a225eb4608bd72e20a6aa6fdda09692f77a7f) | 34 people with rest pairs, plus five learning pairs; **not 39 people**. | Preferred next site; reference, MRI processing and atlas need work. |
| [ATR/CWL](https://bicr.atr.jp/dbi/download/dataset-of-eeg-fmri-with-cwl/) | **39 unique people**, 43.6 paired hours; raw data after registration/DUA. | 33 Prisma + 16 Verio − 10 overlapping people. Larger-data prospect needs preprocessing infrastructure. |

Before pooling resources, reconcile montage/reference, units, clock/excision boundaries, scanner TR, target atlas and preprocessing. Nominal recordings are not verified usable paired hours. ATR access and new external ingestion are outside the fortnight. ([Dataset audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Datasets%20Monash%20and%20Emotiv.md))

<!-- page -->

## 12. Monash discussion should resolve measurements and scope

Mahsa Salehi's **Temporal Analytics Lab** project explicitly studies contrastive EEG representations and between-person variation, including Emotiv-recorded EEG. This supplies a methodological connection, not a confirmed dataset allocation. **Monash Biomedical Imaging** lists EEG–fMRI/physiology support; **Turner's Adeel Razi lab** describes computational brain dynamics and imaging. These public research alignments connect representation learning, measurement and brain dynamics. ([EEG project](https://supervisorconnect.it.monash.edu/projects/research/learning-massive-amounts-eeg-data), [MBI support](https://www.monash.edu/researchinfrastructure/mbi/about-us/clinical-support-team), [Turner lab](https://www.monash.edu/turner-institute/adeel-razi-lab))

Discuss which ROI/contrast is meaningful beyond global state, whether the proposed lag-grid support is physically correct, which validation comparison would justify extra complexity, and which failure would end H1. Clarify who can review the measurement contract and bounded analysis.

**Emotiv access is prospective, potentially in summer; no data are held.** EEG without simultaneous measured BOLD can support self-supervised pretraining, headset/session robustness or downstream behavioural tasks. It cannot alone train or test BOLD fidelity. EPOC-family 14-channel recordings are not equivalent to VU's 26 channels; missing electrodes cannot be created by relabelling. Public Emotiv-recorded resources and authorized Cortex streams have separate permissions. ([Official data index](https://github.com/Emotiv/emotiv-eeg-datasets), [academic route](https://www.emotiv.com/academic-research-and-education))

For a later **author request**, verified paper/repository contacts include Yamin Li/Catie Chang for NeuroBOLT/UniEFS and Emil Kim/Jin Kyu Gahm for MARBLE. Request exact configuration, task checkpoint/licence, split manifests, channel/ROI order, preprocessing and executable loss. ([Author/contact audit](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Frontier%20models%20and%20architecture.md))

For **Emotiv scoping**, request collection/custodian, people/repeats/tasks, measured versus model-generated labels, device/montage/reference, filters/units, timestamps/dropouts/quality streams, actual simultaneous BOLD if any, and research/storage/publication permissions. Begin with metadata and a manifest. These are information checklists; no outreach has been sent.

### A concrete application and its evidence boundary

**Proposed research demonstration:** an offline comparison figure showing measured versus estimated ROI time courses, retained EEG quality, amplitude and per-person error. This makes the application's useful question visible: when does EEG support a specified BOLD surrogate? State-linked research summaries and future feedback studies are directions to evaluate, not established clinical uses.

A clinical study would first need a specific patient group, decision and acceptable error, followed by prospective processing, repeatability and independent-site validation. Neither these correlations nor the present learning curves identify a required clinical dataset or model size. Estimate those requirements from a defined endpoint and learning curves over independent people/sites; token counts and more parameters cannot supply the answer alone. ([Existing feasibility evidence and limitations](Clinical%20EEG%20fMRI%20thesis%20exploration.md))

<!-- page -->

## 13. Nine slides should explain and defend the experiment

| Slide | Visual or evidence | What the student explains |
| --- | --- | --- |
| 1. Task and question | EEG history → one ROI frame | Why BOLD is delayed and prediction differs from measurement. |
| 2. Actual NeuroBOLT | Two-lane diagram | Temporal/spectral inputs, tokens, pooling and additive fusion. |
| 3. Spectral detail | Scale/frame table | Magnitude versus power; dense maps versus physical lag. |
| 4. Completed evidence | 22-person CV chart | Ridge advantage and uncertainty; no universal ceiling. |
| 5. Modern alternatives | Decoder comparison | UnEBOLT conditioning, UniEFS prior, MARBLE token queries. |
| 6. Ranked hypotheses | H1, H2, H3 | Why H1 is first and what each hypothesis could fail on. |
| 7. Fair experiment | Person-separated evaluation | MSE, r, raw R², amplitude, coverage and capacity controls. |
| 8. Two-week delivery | Schedule and data | One actual change; pilot status separate; no acquisition dependency. |
| 9. Research decision | H1 acceptance/failure | What the evidence would justify and which Monash questions remain. |

The strongest contribution is a traceable explanation linking one implementation choice to one falsifiable comparison. A positive result earns further testing; a negative result narrows which representation changes deserve investment. Neither requires claiming anatomical recovery or worldwide architectural novelty.

## Selected primary references and local records

- [NeuroBOLT paper](https://arxiv.org/html/2410.05341v2) and [audited local model](https://github.com/seamus-programming-stuff/NeuroBOLT/blob/240e8c5/models/model.py).
- [LaBraM source and pretraining description](https://github.com/935963004/LaBraM).
- [UnEBOLT, MIDL 2026](https://proceedings.mlr.press/v315/li26g.html).
- [UniEFS / Mind the State, ICML 2026](https://proceedings.mlr.press/v306/li26gp.html).
- [MARBLE, MICCAI 2026](https://papers.miccai.org/miccai-2026/0612-Paper4437.html).
- [Public VU release](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT).
- [ds006040 release](https://openneuro.org/datasets/ds006040/versions/1.0.2).
- [MULTI-CLARID author README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds005795/master/README).
- [ATR/CWL official access and cohort](https://bicr.atr.jp/dbi/download/dataset-of-eeg-fmri-with-cwl/).
- [Monash EEG representation project](https://supervisorconnect.it.monash.edu/projects/research/learning-massive-amounts-eeg-data).
- [Emotiv public dataset index](https://github.com/Emotiv/emotiv-eeg-datasets).
- [Completed hypothesis tests](NeuroBOLT%20hypothesis%20tests.md).
- [Completed paired-cache and NATVIEW synthesis](Clinical%20EEG%20fMRI%20thesis%20exploration.md).
- [Current code audit and hypothesis/pilot specification](../research_notes/NeuroBOLT%20architecture%20research%20briefing/Code%20explanation%20and%20next%20hypotheses.md).
- [Metric teaching guide](thesis_exploration/poster_reading_guide.md).

<!-- page -->

## Appendix. What the new M3 pilot established

<!-- figure: pilot -->

This **exploratory development-data comparison** used 27 people from ds006040, eyes-closed rest, and one global-BOLD target. Three original person folds each fit 12 training people using 120 retained target frames/person; four different people selected settings/epochs and nine supplied outer outcomes. Each person was evaluated once. All 12 fits were selected before outer scoring; there was no result-driven retry or scope reduction.

| Estimator | Mean raw R² | Mean r | People with R² < 0 |
| --- | ---: | ---: | ---: |
| Ridge | **.0651** | .2765 | 4/27 |
| MLP, 9,665 parameters | .0384 | .2406 | 9/27 |
| Transformer, mean pool, 9,409 parameters | -.0316 | .1018 | 20/27 |
| Transformer, learned pool, 9,442 parameters | -.0159 | .1674 | 15/27 |

Learned pooling versus mean pooling gives **+.0156 R²**, person-bootstrap 95% interval **-.0011 to +.0323**; the interval includes zero. Against ridge it gives **-.0811**, interval **-.1052 to -.0582**. These intervals condition on the fitted models and reused development choices; they are not fresh confirmatory evidence. The two transformers share encoder/head initialization but train separately, so this is a readout-design comparison, not an isolated intervention on a frozen encoder.

Amplitude remains compressed: mean prediction/target SD ratios are .223 for ridge, .304 for MLP, .253 for mean pooling and .288 for learned pooling. A positive r alone therefore does not establish faithful waveform reconstruction. **The practical conclusion is to retain ridge and test a precise inductive bias, rather than infer that adding attention solves the task. H1 remains untested.**

Source: [verified summary](architecture_briefing/pilot/20261026_ec_global_v1/summary_verified.json), [per-person scores](architecture_briefing/pilot/20261026_ec_global_v1/per_person_scores_verified.csv), [integrity audit](architecture_briefing/pilot/20261026_ec_global_v1/verification.json). Protocol/source hashes, all 108 fitted-model person scores, validation-only minima and negative-R² counts were checked. Allocation: one L40S GPU, 3 min 36 s, .06 GPU-hours; study process 18.27 s, peak GPU allocation about 75 MB. Raw outputs are preserved; a constant-baseline Pearson-r reporting artifact is explicitly corrected in the verified summary without changing model fits or R².
