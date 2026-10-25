# NeuroBOLT: code explanation and next hypotheses

**Checked 26 October 2026, Australia/Sydney.** Source note for an introductory architecture presentation and supervisor research discussion on 27 October; presentation/PDF deadline **08:30 AEDT**. The academic question is which representations and readouts improve EEG-to-BOLD estimation within a bounded two-week investigation. This is not an employment or application narrative. The presentation/report is owned separately; this assignment supplies this note and, following explicit authorization, a separate bounded exploratory cache pilot.

**Evidence labels:** **CODE** means inspected implementation; **COMPLETED** means existing recorded experiments; **AUDIT** means read-only calculations/synthetic shape checks on 26 October; **PROPOSED** means an untested design. No proposed gain is an observed result. Local source anchors refer to the inspected working tree, Git HEAD `240e8c5d367a47d14cc8a1e929e1b4e2b88aa4c1`; older notes contain obsolete line numbers and implementation descriptions. The original experiment record states **33 NeuroBOLT arms and 21 band-power variants**. Preserve that historical accounting; the per-ROI 32-second arm was stopped incomplete. [Original status, line 3][results-status]; [stopping explanation][results-window].

## 1. What does the implemented NeuroBOLT compute, and how is it trained?

### Takeaway

NeuroBOLT is supervised regression: a preceding multichannel EEG window produces one normalized BOLD value per selected region at one MRI frame. Two encoders convert the same window into 200-number summaries; the implementation adds them, applies GELU and a linear readout. A series of overlapping inputs produces a time course. It does not directly generate a clinical MRI volume. [CODE: forward][forward]; [CODE: pairing][pairing]; [primary paper, §§2.1–2.2, checked 2026-10-26](https://arxiv.org/html/2410.05341v2).

### Cited Findings

#### An introductory explanation

- **A tensor is an array with named axes.** Here `B` is batch size, `C=26` scalp channels, `W` seconds of history, `T=200W` samples and embedding width `D=200`. The engine divides microvolt inputs by 100 and reshapes `[B,C,T]` to `[B,C,W,200]`; each 200-sample patch represents one channel-second. These definitions follow the actual rearrangement, not a frequency-band feature input. [CODE: engine.py:72][engine-input].
- **The temporal encoder learns relationships between channel-second patches.** Convolutions turn each patch into 200 features; learned electrode and time embeddings identify where/when a patch came from. Twelve transformer blocks mix patches using attention and feed-forward networks. A query/key comparison controls which other tokens contribute value features; these weights are learned predictive computations, not anatomical localization. The default readout averages non-CLS tokens, then applies LayerNorm. [CODE: convolutions][conv]; [CODE: attention][attention]; [CODE: position, blocks and pooling][ts-features].
- **The spectral encoder describes oscillations at several resolutions.** It takes STFT magnitudes, projects frequency axes to 200 features and maps each scale's window axis to a common size. It sums scales, adds channel identities and sinusoidal positions, applies four layers of linear attention, then averages tokens. Despite its name, this branch is a nonlinear neural predictor after encoding and GELU. [CODE: spectral setup][mss-setup]; [CODE: STFT/forward][mss-forward].
- **Pretraining is an initialization, not BOLD supervision.** LaBraM originally learns EEG representations through masked neural-code prediction. NeuroBOLT subsequently optimizes paired EEG/BOLD regression. The local loader strips the `student.` prefix and loads compatible weights; this is not the LaBraM tokenizer/codebook pretraining procedure running inside NeuroBOLT. [CODE: checkpoint loading][checkpoint-load]; [LaBraM authors' explanation, checked 2026-10-26](https://github.com/935963004/LaBraM#readme).

#### Precise functional diagram specification

Use a two-lane figure, with tensor sizes on arrows and **one frame's target** on the right. This diagram describes the **baseline implementation**, not the new pilot. [CODE: complete model forward][forward]; [CODE: spectral forward][mss-forward].

```text
Paired, processed EEG strictly preceding target frame t
                  [B,26,3200] microvolts, 16 seconds
                          divide by 100
                       [B,26,16,200]
                  /                         \
TEMPORAL / LaBraM lane                 MULTISCALE SPECTRAL lane
channel-second patches                flatten back to [B,26,3200]
TemporalConv                          per channel: four magnitude STFTs
[B,416,200]                           n_fft=100,200,400,800
prepend CLS -> [B,417,200]             [B,F_i,K_i] for each scale
electrode + second embeddings         frequency projection -> [B,K_i,200]
12 blocks; 10 attention heads          dense window map -> [B,32,200]
mean of 416 non-CLS tokens             sum four scales for each channel
LayerNorm -> [B,200]                   channel + sinusoidal embeddings
                                      concatenate -> [B,832,200]
                                      4 linear-attention layers; 8 heads
                                      mean 832 tokens -> [B,200]
                  \                         /
                       elementwise ADD [B,200]
                               GELU
                       Linear(200,R) -> [B,R]
                 R=1 original per-ROI recipe; R=7 shared arm
```

**CODE/AUDIT shape details.** In `TemporalConv`, rearrangement gives `[B,1,26W,200]`. The first convolution, width 15/stride 8/padding 7, gives `[B,8,26W,25]`; the two width-3 convolutions preserve it. Flattening 25×8 yields 200 features. For 16 seconds there are **416 data tokens plus one temporal CLS**. CLS participates in attention but is excluded from default averaging. The spectral branch has **no CLS**, so it has **832**, not 833, tokens. A CPU evaluation on zeros with synthetic channel indices confirmed `[1,416,200]`, `[1,832,200]` and `[1,7]`; this verifies plumbing, not prediction quality. [CODE: TemporalConv][conv]; [CODE: temporal pooling][ts-features]; [CODE: spectral concatenation][mss-pool].

| STFT scale at 200 Hz | Frequency bins `F_i` | Frames `K_i`, 16 s | Frames `K_i`, 24 s | After frequency projection, per channel |
|---|---:|---:|---:|---|
| 100 samples / 0.5 s | 51 | 32 | 48 | `[B,K_i,200]` |
| 200 / 1 s | 101 | 16 | 24 | same form |
| 400 / 2 s | 201 | 8 | 12 | same form |
| 800 / 4 s | 401 | 4 | 6 | same form |

These are **derived shapes**: `F_i=n_fft/2+1`, `K_i=1+floor((T-n_fft)/n_fft)`. STFT uses hop equal to FFT length, `center=False`, no supplied taper and magnitude `abs(complex)`—**not power, log power or just 1–45 Hz**. The log arm uses `log1p(magnitude)`. `PatchWindowEmbedding` is a **dense learned linear map over the entire window-index axis**, applied independently to feature coordinates; it is not interpolation between physically aligned timestamps. Common output length is `M=T//100=2W`. At 24 s, spectral tokens number **1,248**, temporal tokens **625 including CLS**, and both final vectors remain 200-dimensional. [CODE: embedding definitions][mss-embeddings]; [CODE: STFT][mss-stft]; [CODE: temporal construction][model-setup].

The local dependency's default linear attention separately normalizes queries across features and keys across sequence positions, contracts `KᵀV`, then applies Q; this is not an explicit quadratic token-token attention matrix. NeuroBOLT supplies no Linformer configuration. Its `max_seq_len=1024` argument does not impose a hard 1,024-token assertion in that default path; it should not be cited as proof that the completed 24 s arm could not run. Pin the M3 environment before future reproduction. [CODE: local installed implementation](<C:/Users/Seamus/anaconda3/envs/neurobolt/Lib/site-packages/linear_attention_transformer/linear_attention_transformer.py:204>); [versioned dependency source, checked 2026-10-26](https://raw.githubusercontent.com/lucidrains/linear-attention-transformer/0.19.1/linear_attention_transformer/linear_attention_transformer.py).

#### Which parts are active, trainable or frozen?

| Configuration | Temporal forward | Spectral forward | Interpretation |
|---|---|---|---|
| Default `branch=both` | computed; gradients allowed | computed; gradients allowed | Both feed their sum to the head. |
| `branch=spectral` | skipped | computed | Temporal modules still exist in memory and in the generic parameter count. |
| `branch=temporal` | computed | skipped | Spectral modules likewise remain allocated. |
| `tmp_norm=batchnorm` | pooled vector gets BatchNorm | unchanged | Not token-level pooling repair; already tested. |

There is **no explicit baseline freeze of the temporal branch** (`requires_grad=False` is used for a spectral integer index, not the backbone). Its early layers instead receive small learning rates. Gradients being permitted, forward computation and useful predictive contribution are three different statements. Optional `return_patch_tokens`/`return_all_tokens` already exist for the temporal features; simply passing them through the existing fused forward is not a complete decoder change because the head expects compatible pooled features. [CODE: branch control][forward]; [CODE: optional normalization][model-setup]; [CODE: optimizer filtering][optimizer].

**AUDIT parameter counts**, from fresh in-memory construction using current defaults, `init_values=.1`, seven outputs, no training:

| Window | Temporal parameters | Spectral parameters | Seven-output head | Allocated trainable total | Active spectral + head if temporal skipped |
|---|---:|---:|---:|---:|---:|
| 16 s | 5,819,936 | 2,086,848 | 1,407 | 7,908,191 | 2,088,255 |
| 24 s | 5,821,536 | 2,089,312 | 1,407 | 7,912,255 | 2,090,719 |

These exclude buffers/non-trainable integer indices; counting all checkpoint tensor entries would include them. The 24 s increase includes time embeddings and window projection sizes. The implementation's generic count can overstate the parameters actually used by a branch ablation. [CODE: model setup][model-setup]; [CODE: spectral sizes][mss-setup]; [CODE: parameter-count expression][parameter-count].

#### Training recipe and learning rates

- **CODE:** the hypothesis SLURM recipe uses batch 64, up to 30 epochs, five warmup epochs, seeds `12345,1,2`, early-stopping patience 10 and no saved checkpoints; the CLI alone defaults to batch 16/20 epochs. Multi-output labels separated by `|` already select several columns. There is no current single-output-only loader limitation. [Recipe][recipe]; [CODE: label selection][roi-selection]; [CODE: main output count][main-output].
- **CODE:** loss is ordinary mean squared error, averaged over batch/output entries, not correlation loss or classification. AdamW defaults are LR `.0003`, weight decay `.05`, epsilon `1e-8`; unless overridden, beta settings use PyTorch defaults. Correlation is a reporting metric. Normal non-DeepSpeed execution disables autocast. [CODE: defaults][training-defaults]; [CODE: optimizer construction][adamw]; [CODE: MSE and schedules][training-loss]; [CODE: engine][engine-input].
- **CODE/DERIVATION:** with 12 blocks and layer decay `.65`, group `i` gets `base_lr × .65^(13-i)`. Token/position/convolution group 0 peaks at **1.109×10⁻⁶**; block 0 at **1.706×10⁻⁶**; block 5 at **1.471×10⁻⁵**; block 11 at **1.95×10⁻⁴**. The spectral module, head, `fc_norm` and, easily missed, **`time_embed`** take group 13/full **3×10⁻⁴**. `time_embed` is not specially mapped to group 0. Thus “the whole temporal branch is frozen” is inaccurate. [CODE: layer-ID mapping][layer-map]; [CODE: decay assignment][lr-assignment]; [CODE: scheduled application][engine-lr].
- **CODE:** the scheduler warms up from **zero** to base LR and then decays towards `1e-6`; the parser's `warmup_lr` is not passed to this call. Biases, 1-D parameters and named positional parameters avoid weight decay. Checkpoint time embeddings are linearly interpolated for longer windows; that changes initialization, not just the number of input samples. [CODE: scheduler call][training-loss]; [CODE: scheduler default][scheduler]; [CODE: exclusions][optimizer]; [CODE: interpolation][interpolation].
- **CODE:** epochs are selected by minimum validation MSE. Test predictions/scores are also computed each epoch, though selection normally uses validation. Existing checkpoint saving additionally requires positive test correlation; future validation-only runs should not inherit this test-dependent save gate. The experiment recipe disabled checkpoint saving. [CODE: epoch selection/save gate][epoch-selection]; [Recipe][recipe].

### Inferences

Mean pooling may make a weak or poorly adapted representation hard to use, but averaging after positional encoding and attention **does not prove all temporal order has been erased**. Likewise, dense spectral window projections can encode lag-specific combinations even though their output indices lack an explicit physical-time interpretation. “Make lag structure easier to learn” is a valid hypothesis; “NeuroBOLT has no lag information” is false as a code description. [Temporal pooling][ts-features]; [spectral projection][mss-embeddings].

### Gaps

The reported temporal/spectral variability figures (about 2% versus 91%) and a within-scan feature-ridge r≈.42 were found in the narrative, not an independently recoverable feature-audit export inspected here. Do not turn them into a causal pooling diagnosis. The local `Thalamus.pth` was safely inspected: its historical mode is `same_sub_same_scan`, with a one-output head and saved epoch 4; it is not a verified shared seven-output, cross-subject, 24 s checkpoint. Task-specific checkpoints for future decoder comparisons must be explicitly created/provenanced. [Reported diagnostic][results-branches]; [local checkpoint](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/checkpoints/Thalamus.pth>).

## 2. What do the completed experiments establish, and what remains interpretation?

### Takeaway

The strongest completed comparison favors a well-regularized lagged-power ridge baseline. The original-split ablations show spectral dominance under the tested recipe; they do not prove that temporal EEG representations, nonlinear models or a particular pooling method can never help. Repeatedly inspected development data cannot supply fresh confirmation for new architectures. [Completed comparisons][results-cv]; [completed branch ablations][results-branches].

### Cited Findings

#### Recorded result versus justified claim

| COMPLETED result | What it establishes | What it does not establish |
|---|---|---|
| Original split: shared 16 s full model r=.46249; spectral-only .46143; temporal-only .02442 | Removing temporal computation has little observed cost on these scans under this recipe. | Formal equivalence, no temporal information, or spectral dominance on every cohort. |
| Temporal-only without layer decay r=.17662; scratch .160; scratch+BN .167 | The temporal path can learn some signal when training changes; performance remains much lower here. | That learning-rate decay alone explains the entire failure. |
| Full model without layer decay .46492; no pretraining .46428; pooled temporal BN .46245 | These tested repairs did not produce a substantial improvement. | A reason to repeat the same pretraining/freeze/BN arms as new research. |
| Shared 24 s full .48120; spectral-only .47821 | Spectral-only nearly matches test r. | Identical performance: validation r is .34017 versus .32988. |
| Five-fold person-grouped CV: ridge .381, NB24 .336, NB16 .323 | Ridge leads NB24 by .045, paired 95% interval .023–.067 over 22 people. | Population-optimal linearity or a biological information ceiling. |
| NB24 minus NB16 in that CV: +.013, interval −.003 to +.029 | Longer history is a promising limited change with uncertain average gain. | A universal 24 s optimum or a securely positive independent effect. |

Sources for rows 1–4: [original export, shared baseline starts at row 7009][csv-shared], [spectral starts at row 2389][csv-spectral], [temporal starts at row 2851][csv-temporal], [report branch table][results-branches]. Means above were recomputed from the exported per-seed/ROI/scan correlations, not fitted anew. Rows 5–6: [five-fold results][results-cv]; [person-level aggregation implementation][cv-code]. Original-split means weight scans, whereas headline CV means average repeated scans within person; seed-mean r is also different from scoring an ensemble-averaged prediction. Keep these labels in any slide.

#### Do not repeat completed work

The **historical record is 33 NB/21 band-power variants**; the current aligned CSV has 51 distinct arm names, including baselines and partial records. Counting that export is not a replacement for historical experiment accounting. In particular, `win32` has only three ROIs for one seed (33 validation/test rows), and the narrative says it was stopped; the completed **shared** 32 s arm is a different configuration. The generic generated table footnote saying missing rows are “still running” is stale for that stopped arm. [Status][results-status]; [partial record starts at CSV row 8626][csv-partial]; [stop statement][results-window]; [arm naming/reference logic][arm-map].

Already answered locally, within their recorded scope: 8/20/24/28/32 s neural windows; high-pass/window-baseline removal; LR/AdamW beta changes; scale softmax weights; log-magnitudes; temporal/spectral branch ablations; initialization/layer-decay/pooled-BN repairs; seven versus 65 outputs; stronger dropout/weight decay; train+validation refits; ridge band/lag/window/normalization grids; low-rank tensor readouts. The new baseline rerun below is a matched control, not a new hypothesis. [Arm labels][arm-map]; [result table][results-status].

Beyond those arms, **learned frequency bands, MLP/spline/interactions, and shared-factor smooth distributed-lag/Hammerstein models were also completed**. Learned-band CP/full r=.355/.336 versus fine-bin ridge; a five-component smooth-kernel model scores about .362 for seven targets and does not beat ridge. “Learn some bands” or “add a smooth HRF-like low-rank head” is therefore not a fresh answer to this project's results. A genuinely canonical-HRF prior with a specifically controlled residual could be a separate future question, but it is not selected here. [Completed learned-band/nonlinear tables][interp-nonlinear]; [Hammerstein tables][interp-hammer]; [its five-basis kernel implementation][hammer-code].

#### Preprocessing and evaluation boundaries

- **CODE:** VU EEG is resampled to 200 Hz and nuisance leads dropped; cross-subject loading defaults to .5 Hz high-pass, unlike intra-scan loading. MNE extracts `[-W,0]`, subtracts the whole-window channel mean by default and crops to `200W` samples, removing the endpoint sample. Targets are paired by retained scanner-event indices. [Loader][loader]; [epoching/pairing][pairing].
- **CODE:** targets are fifth-order .15 Hz Butterworth-filtered with `filtfilt`, then demeaned and divided by the scan's 95th percentile of absolute demeaned amplitude. This is **not ordinary unit-SD z-scoring**. It happens before intra-scan splitting. Optional robust EEG scan scaling uses the entire scan's MAD and a fixed 15 μV reference; optional ridge per-scan feature z-scoring also uses the entire held-out EEG scan. These are retrospective operations, even when no held-out BOLD becomes an input. [Target processing][target-processing]; [normalization][target-norm]; [EEG robust scaling][scan-norm]; [ridge transforms][ridge-transform].
- **CODE:** ridge computes Welch log-power for each channel×band×subwindow, then fits feature means/SDs from training data only. That is different from log-compressing NeuroBOLT magnitudes, and the ridge/NeuroBOLT comparison changes representation as well as estimator. [Ridge features/transforms][ridge-features].
- **CODE:** the loader trusts workbook split membership rather than validating person-disjointness. The intra-scan split skips `ceil(max(20,W)/TR)` frames at each boundary; guard frames do not undo whole-run filtering/scaling. The cached-input path bypasses preprocessing/configuration reconstruction, so a future window experiment must not silently load incompatible cached 16 s tensors. [Split and cache paths][loader-full]; [intra-scan split][intra-split].
- **CODE:** saved `scan_sizes` and per-scan rescoring support real scan boundaries; aligned comparison trims each scan to common ending frames. However, the ordinary evaluation loader uses total length divided by scan count to choose batch size. If scan sizes differ, its batch-based online correlations can mix boundaries. New analysis must retain actual scan/person identifiers. [Batch sizing][eval-batches]; [rescoring][per-scan]; [alignment][aligned-code].
- **COMPLETED:** the later ds006040 cache contains 300 group×band×lag features, not NeuroBOLT waveforms. Its 27-person, 54-run study's high-resource regional ridge r=.1886/R²=.02788 and MLP r=.1223/R²=.00678 concern another task/objective/target grouping. They are not a new NB reproduction. The cache records inherited retrospective artifact cleaning, whole-run BOLD processing and future-margin QC. [Prior report][clinical-result]; [feature construction][cache-features]; [recorded limitations][cache-limitations].
- **COMPLETED:** VU/ds006040 tests have a substantial inspection history. NATVIEW strict v1 accepted one of eight; amended v2 evaluated six with weak transfer and negative regional R². It must not be relabelled an untouched architecture test. [Prior report and amended evaluation](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/Clinical EEG fMRI thesis exploration.md:76>); [earlier learning-scope caveats](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Monash honours EEG project/Reuse and learning scope.md:142>).

### Inferences

The defensible mechanistic reading is **consistent with** a useful slow spectral/state representation and insufficient benefit from the tested waveform path. It is not proof that all predictable BOLD is arousal, that EEG identifies local vascular mechanisms, or that the observed plateau is irreducible. Nonsignificant differences are not equivalence. A high temporal r is not calibrated amplitude or subject-specific connectivity; predictive R² can be negative even with positive r. The introductory worked example `prediction=.2×target+1` has r=1 but R²=−.64 for zero-mean/unit-variance targets. [Existing numerical explanation](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/poster_reading_guide.md:49>); [completed model contrasts][results-cv].

### Gaps

Original-split scan-based intervals treat six scans from five people as their units and do not correct the many adaptive comparisons. Five-fold person intervals improve aggregation but do not undo model selection informed by earlier folds/results. No causally processed, untouched clinical validation follows from these files. No new architecture performance has been established by this code audit. [Original interval construction](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/build_hypotheses_report.py:43>); [CV aggregation][cv-code].

## 3. Which two new architectural questions are worth a two-week investigation?

### Takeaway

Select **two questions**, both explicitly **PROPOSED**: (H1) replace unrestricted spectral time-axis mixing with an explicit aligned lag grid, and (H2) allow content-dependent readout of retained tokens, eventually conditioned on ROI. The newly authorized overnight cache pilot tests a narrow **H2 teaching prototype**; it is not either published NeuroBOLT or an implementation/evaluation of H1. Existing ROI-conditioned models also mean these are local controlled research questions, not claims of worldwide novelty. [Current spectral mixing][mss-embeddings]; [existing adaptive multi-ROI work, checked 2026-10-26](https://proceedings.mlr.press/v315/li26g.html); [MARBLE primary record, checked 2026-10-26](https://papers.miccai.org/miccai-2026/0612-Paper4437.html).

### Cited Findings

#### H1 — Explicitly aligned spectral lag representation

**Hypothesis/proposal:** with the 24 s spectral-only NB configuration fixed, replacing the dense `K_i→48` scale window maps by fixed support-overlap maps makes the relation between lag and output easier to fit and improves held-out error without more parameters. Each coarse STFT frame contributes only to the .5 s bins its support covers; for these divisible scales, this is local replication/overlap weighting. Preserve magnitudes, frequency projections, equal scale sum, channel/position embeddings, transformer and mean readout. There is no extra pooling change in the primary H1 comparison. [Existing layer to replace][mss-embeddings]; [baseline branch implementation][forward].

**Baseline/control:** rerun unchanged spectral-only NB24 against alignment-only, same folds/frames/seeds/optimizer and validation selection. Ridge on 24 s/12-lag fine-bin power is the external performance baseline. A parameter-matched local learned interpolation is a possible later control if the main comparison suggests a benefit, not a pretext for an overnight grid. Fixed physical alignment also reduces capacity; an observed gain alone would not isolate chronology from regularization.

**Budget, derived:** the four existing 24 s window maps have `48×(48+24+12+6)+4×48 = 4,512` parameters. Fixed maps use buffers, so the active spectral+seven-output head drops from **2,090,719 to 2,086,207** trainable parameters. Temporal modules can be bypassed as now; actually removing them requires a separate engineering change. An alignment-only result is more interpretable than changing encoder width, history, log transform and readout simultaneously. [Existing size calculation][mss-setup]; [AUDIT counts in §1].

**Minimum future code changes:** `models/model_multiscale.py` (fixed support maps/optional alignment mode), `models/model.py` (thread option to encoder), `main.py` (option/default). Add a separate validation-only runner and shape/support checks before execution; current `main.py` always evaluates test each epoch. These model files are **not modified in this assignment**. [Option plumbing][model-options]; [test access][epoch-eval].

**Evaluation/failure:** primary equal-person predictive R²/MSE at identical timestamps; also r/RMSE/SD ratio, negative-R² frequency and per-ROI effects. Fail if it does not beat its matched spectral baseline on validation, if improvement comes only from amplitude drift, or if it remains inferior to ridge without a meaningful efficiency benefit. Broad STFT windows can blur local lag detail; fixed maps can remove useful flexibility. A positive result supports this inductive bias on this data, not a neural HRF mechanism.

**Feasibility:** actual NB change is a **days-to-two-weeks** job including implementation, profiling and limited matched folds, using already staged waveforms. An overnight fit is possible only after that preparation; no wall-time guarantee follows from a two-hour SLURM request. Do not begin a full 33-arm rerun. No new pretraining checkpoint is required for a spectral-only implementation.

#### H2 — Token readout before global pooling, with ROI queries as the bounded extension

**Hypothesis/proposal:** a target query can select useful spectral channel/lag tokens more effectively than compressing every target through the same mean. Return `Z:[B,26M,200]` before `mean(dim=1)`. Form keys/values with `200→64` projections, one learned 64-vector query per target, and normalized query–key weights; weighted values feed one shared `64→1` scalar readout. Keep MSE and target normalization fixed. For a single global target this is learned token pooling; seven distinct queries make it ROI-conditioned decoding. Learned queries are an established architectural ingredient, not inherently interpretable physiology. [Current pool site][mss-pool]; [learned-query primary example, checked 2026-10-26](https://arxiv.org/abs/2005.12872); [existing EEG-to-BOLD multi-ROI work](https://proceedings.mlr.press/v315/li26g.html).

**Baseline/control:** same encoder and training budget with mean pooling; mean pooling plus a size-matched MLP head; ridge; and, for a regional claim, an EEG-predicted-global template fitted using training outcomes only. Query attention must improve actual regional trajectories or declared contrasts, rather than only sharing a global fluctuation. Do not add measured held-out global BOLD as a prediction input. Inspect attention stability as a diagnostic, not as causal localization.

**Budget, derived:** at seven targets, keys and values contribute `2×(200×64+64)=25,728`, queries `7×64=448`, shared readout `65`: **26,241 decoder parameters**, replacing the old 1,407-parameter head, a net **24,834** increase. Active spectral24 model ≈**2,115,553** parameters. A mean-pooled `200→127→7` MLP has 26,423 parameters, a close capacity control. Count the eventual implementation; these formulas specify a proposal, not a trained model. [Original readout definition][model-setup].

**Minimum future actual-NB changes:** `model_multiscale.py` (return tokens), `model.py` (query decoder and compatible forward), `main.py` (decoder option), plus a validation-only runner/checks. A frozen-encoder decoder comparison needs a task-appropriate, validation-selected saved checkpoint: existing hypothesis runs saved predictions instead. Starting from the one local thalamus/intra-scan checkpoint is not an equivalent shortcut. [Pool site][mss-pool]; [recipe][recipe]; [checkpoint limitations in §1].

**Evaluation/failure:** use the same primary/error panel as H1, with mean/MLP head controls. Fail if query attention collapses to the same weights, if it increases r but worsens raw R²/amplitude, if a mean head matches it, or if only population/global structure improves. An advantage does not establish recoverable anatomy or person-specific connectivity.

**Feasibility:** the **small feature-cache prototype below is bounded overnight work**. An actual NB query decoder plus capacity controls/checkpoint study needs the two-week implementation window; a full MARBLE/UnEBOLT reproduction or new foundation encoder needs a separate multiweek/team plan and checkpoint/environment audit. Those are not dependencies for the presentation.

#### Authorized overnight pilot: a separate scalar global-BOLD teaching prototype

**COMPLETED exploratory pilot, authorized after this audit began; the design below was frozen before training.** The run used the existing ds006040 `features_causal.npz`, EC only, `global signal clean` selected by exact label; the original person folds, selected 12 training people and 240 retained target-seconds/person. All corresponding inner-validation/test eligible EC rows were used as specified by the existing protocol. Transforms were fitted on the selected training frames only. Exact subsets/weights came from the study helper code. [Cache/protocol reuse register](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Monash honours EEG project/Reuse and learning scope.md:19>); [existing feature order][cache-features]; [frozen pilot protocol](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/protocol.json>).

Four prespecified models receive the **same 300 features and scalar MSE objective**: ridge, `300→32 GELU→1` MLP, tiny transformer with mean pooling, and the **same transformer architecture** with learned lag pooling. Token conversion must be `N×300 → N×5×5×12 → N×12×25`, with an inverse roundtrip check. The transformer has width 32, one encoder layer, two heads, feed-forward width 64 and dropout .1; record actual parameters and require <20,000. One fixed seed **41**, max **60 epochs**, patience **10**, AdamW LR **.001**, weight decay **.01**, batch **128**. Ridge uses the existing protocol's six penalties and inner-validation selection. Neural epoch selection uses equal-person inner-validation MSE, not outer scores. [Source of cached layout][cache-features]; [existing training protocol](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/thesis_data.py:220>).

Primary score is **raw predictive R², equal-person aggregation**, with Pearson r, RMSE, predicted/observed SD ratio and negative-R² frequency. Name its mean-reference denominator; also report the deployable training-mean baseline. The evaluation-mean denominator is not an input to the model. No test-tuned calibration, lag shifts, repeated architecture search or outer-score-driven retraining. Existing data are reused development data, not fresh confirmation. Its global task is different from the historical 64-region joint MLP objective. [Existing scalar/global scope and metric distinctions](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Monash honours EEG project/Reuse and learning scope.md:59>); [metric caveats](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/poster_reading_guide.md:49>).

**What this pilot can establish:** feasibility, shapes, a transparent paired comparison of compact estimators and the effect of learned lag pooling under one fixed task/seed. **What it cannot establish:** that replacing NeuroBOLT's STFT mixing helps; that its pretrained branch was repaired; that waveform spectral tokens improve; that a full ROI-query decoder is superior; external, prospective or clinical validity. Its inputs already contain hand-engineered lagged log power, unlike published NB. A negative result remains useful for deciding not to invest further.

Execution ceiling: **one GPU allocation, 90-minute wall time, 32 GB; ≤2 GPU-hours or ≤8 CPU-hours**, with explicit reporting if blocked/capped. Profile training/inner validation first; any reduced scope must be declared **before outer scoring**. Write new pilot code/results only; no raw/weight downloads, alteration of original results, main model edits or pushes. At most the three existing folds × four fixed models, not a hyperparameter search. If the M3 cache/protocol is absent or incompatible, retain the protocol and report the blocker. Job identity, protocol hash and observed completion status will be appended after submission.

#### Two-week schedule, conditional on profiling and staged data

| Dates | Bounded deliverable | Decision |
|---|---|---|
| Night 26–27 Oct; PDF by 08:30 | Architecture diagram/explanation, old-results evidence panel, two proposals; optional fixed cache pilot with protocol/hash and explicit run status. | Report incomplete work honestly; do not delay the briefing for a speculative model gain. |
| 27–28 Oct | Freeze task/frames/scoring; verify person separation, feature order, target units and parameter counts; interpret the tiny pilot. | Choose **one actual NB modification**, H1 by default; drop expansion if cache/profiling fails. |
| 29–30 Oct | Implement H1 alignment behind a default-off option; synthetic support checks; profile unchanged versus changed spectral24. | Continue only if shapes, shared frames and validation-only selection work. |
| 31 Oct–3 Nov | Limited matched development folds/seeds, ridge control, raw-error and amplitude panel; preserve failed runs. | A well-documented negative result is complete evidence; no test-guided rescue grid. |
| 4–6 Nov | If H1 finished within budget, prototype H2 on retained tokens; otherwise finish H1 analysis. Save a validation-selected checkpoint if frozen-readout comparisons are required. | ROI-query full reproduction and new pretraining remain out of this fortnight. |
| 7–9 Nov | Final annotated diagram, methods/configuration, per-person results/failures and a short research-directions presentation. | State what changed, what was actually run and what remains proposed. |

This is a **14-day investigation plan**, not a promise of a positive result or a longer degree programme. No Emotiv access, new acquisition, external checkpoint availability or employment contact is assumed.

#### Execution update — completed and independently checked, 26 October

The audit note was completed before pilot implementation. **M3 SLURM job `61455229` completed, exit `0:0`: all 12 model-by-fold fits and all 27 outer people, without scope reduction or model retries.** The one-GPU/four-CPU/32 GB allocation used **3m36s wall time**, about **.06 allocated GPU-hours**, within its 90-minute cap. The validation-only first-fold profile passed before outer access; all twelve selections completed before outer scoring. The study process took **18.27s**, excluding package/startup overhead; peak allocated GPU memory was **74.63 MB** on an L40S. These are compute measurements, not clinical latency. [Accounting](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/sacct.tsv>); [profile](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/profile.json>); [completion](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/status.json>).

The frozen protocol SHA-256 is **`24e4f3af183a31cc336a0ee99f8487ec3ecc669f7cc464c44af81d77dc3fcb74`**. The existing M3 feature cache, parent protocol and both reused helper sources matched local hashes before deployment. Actual compact-model parameter counts are **9,665 MLP / 9,409 mean-pool transformer / 9,442 learned-pool transformer**. The two transformer arms start from identical encoder/head weights, with learned pooling initialized uniformly; they are then fitted independently under identical settings. These are architecture/engineering facts, not performance findings. [Frozen protocol](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/protocol.json>); [implementation](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/architecture_pilot.py:77>).

Local Python compilation, shell syntax validation and **10 synthetic tests passed**. Tests cover semantic token order and inverse mapping, training-only transforms, actual person-fold separation and overlap rejection, equal initial transformer predictions, gradient flow to pooling weights, the parameter cap, raw R² versus correlation, equal-person validation weighting, ridge algebra, the runtime gate and selected-checkpoint validation loss. No real-data model fit ran locally. [Test record](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/local_tests.txt>); [tests](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/architecture_pilot_tests.py:16>).

M3 output directory: `/projects/hz18/stay0060/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/`. Scheduler stdout/stderr: `/projects/hz18/stay0060/NeuroBOLT/reports/architecture_briefing/pilot/architecture-61455229.{out,err}`. Small results, profile, selections, derived predictions, logs and accounting were collected into [the new local pilot folder](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1>). Local independent float64 recomputation verified all **108 fitted-model person rows**, with maximum R² discrepancy **2.07×10⁻⁷**. Person/frame selection, validation epoch minima, aggregate means, negative-R² counts, paired-bootstrap intervals and remote/local file hashes were checked. Frozen source/protocol/cache hashes remained unchanged after the run. [Verification](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/verification.json>); [all-selections-before-scoring gate](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/architecture_pilot.py:432>).

**COMPLETED pilot results — global target only, equal-person means:**

| Model | Raw predictive R² [exploratory 95% interval] | Pearson r | RMSE | SD ratio | Negative-R² people |
|---|---:|---:|---:|---:|---:|
| Ridge | **.06513 [.03211, .09909]** | .27650 | .49226 | .22267 | 4/27 |
| MLP 300→32→1 | .03845 [−.00288, .08158] | .24065 | .49903 | .30430 | 9/27 |
| Transformer, mean pool | −.03157 [−.06534, .00584] | .10183 | .51709 | .25292 | 20/27 |
| Transformer, learned lag pool | −.01593 [−.05426, .02472] | .16738 | .51291 | .28779 | 15/27 |

Learned-minus-mean pooling raw-R² difference was **+.01564 [−.00109, +.03226]**, with 17/27 people favoring learned pooling: **uncertain**. Learned-pool-minus-ridge was **−.08105 [−.10522, −.05815]**, only 1/27 favoring learned pooling. Ridge remains strongest; neither transformer demonstrates positive average raw R². No result here supports a published-NB improvement, regional recovery or a global theorem about attention. Intervals use 2,000 paired person bootstraps and are exploratory; reuse and shared training sets limit inference. [Verified summary](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/summary_verified.json>); [person scores](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/per_person_scores.csv>).

**Explicit numerical diagnostic:** float32 centering of the constant training-mean baseline produced one spuriously defined Pearson r=0 in the raw summary; mathematically all 27 constant-baseline correlations are undefined and SD ratio is zero. Primary R² and all fitted-model metrics are unaffected. The original `summary.json`/CSV, frozen code and protocol were preserved; separate `summary_verified.json` and `per_person_scores_verified.csv` make only this documented reporting correction. The warning in stderr concerns empty bootstrap diagnostic slices for this baseline. No fit was retried. [README with correction and full results](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/README.md>); [raw summary](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/summary.json>).

### Inferences

A useful presentation can already make a concrete contribution: explain the actual tensors/optimizer, correct overstrong interpretations of spectral dominance, and define a fair test that could fail. Improvements must earn their complexity against ridge. The compact pilot should be presented as a worked research experiment alongside the architecture diagram, with a conspicuous boundary between engineered feature tokens and NeuroBOLT waveform/STFT tokens. [Completed ridge advantage][results-cv]; [representation code][ridge-features]; [NeuroBOLT representation][mss-forward].

### Gaps

The compact pilot's compatibility, completion and compute costs are now measured. H1's actual NB implementation, H2's full token/ROI decoder, their task-specific checkpoints and their runtimes remain untested. Cross-site validation, physiological identification, a full modern-model reproduction and acquisition with prospective sensors cannot reasonably be guaranteed in this two-week scope. The exploratory cache results do not settle those questions. [Pilot verification](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/architecture_briefing/pilot/20261026_ec_global_v1/verification.json>).

[forward]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py:410>
[model-setup]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py:264>
[conv]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py:233>
[attention]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py:134>
[ts-features]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model.py:368>
[mss-embeddings]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py:23>
[mss-setup]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py:94>
[mss-stft]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py:152>
[mss-forward]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py:165>
[mss-pool]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/models/model_multiscale.py:210>
[engine-input]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/engine.py:72>
[engine-lr]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/engine.py:59>
[model-options]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:274>
[main-output]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:347>
[checkpoint-load]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:465>
[interpolation]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:491>
[parameter-count]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:523>
[training-defaults]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:84>
[training-loss]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:573>
[lr-assignment]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:537>
[layer-map]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/optim_factory.py:33>
[optimizer]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/optim_factory.py:58>
[adamw]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/optim_factory.py:126>
[scheduler]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/utils.py:557>
[epoch-eval]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:638>
[epoch-selection]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:650>
[eval-batches]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:419>
[per-scan]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/main.py:299>
[recipe]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/hypotheses_m3.sbatch:57>
[loader]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:17>
[loader-full]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:183>
[intra-split]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:149>
[scan-norm]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:91>
[roi-selection]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:66>
[target-processing]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/get_datasets.py:257>
[target-norm]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/preproc.py:5>
[pairing]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/dataset_maker/preproc.py:75>
[ridge-features]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/baseline_ridge.py:98>
[ridge-transform]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/baseline_ridge.py:139>
[aligned-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/collect_hypotheses.py:68>
[arm-map]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/plot_hypotheses.py:27>
[cv-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/summarize_cv.py:41>
[results-status]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/NeuroBOLT hypothesis tests.md:3>
[results-window]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/NeuroBOLT hypothesis tests.md:101>
[results-branches]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/NeuroBOLT hypothesis tests.md:128>
[results-cv]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/NeuroBOLT hypothesis tests.md:74>
[csv-shared]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/hypotheses/runs_aligned.csv:7009>
[csv-spectral]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/hypotheses/runs_aligned.csv:2389>
[csv-temporal]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/hypotheses/runs_aligned.csv:2851>
[csv-partial]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/hypotheses/runs_aligned.csv:8626>
[interp-nonlinear]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/interpretability/tables.md:166>
[interp-hammer]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/interpretability/tables.md:222>
[hammer-code]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/interp_hammerstein.py:47>
[clinical-result]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/Clinical EEG fMRI thesis exploration.md:40>
[cache-features]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/scripts/thesis_data.py:82>
[cache-limitations]: <C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/feature_qc.json:1222>
