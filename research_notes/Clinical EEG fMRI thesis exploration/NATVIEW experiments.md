# NATVIEW bounded new-data experiments

Execution date: 21 October 2026, Australia/Sydney. All experiment computation is on M3 CPU SLURM jobs. Public downloads run on the M3 login node. This branch owns only `scripts/natview_*`, `reports/thesis_exploration/natview/`, and this note. No core/thesis scripts, raw source objects, poster files, commits or pushes are changed.

The authoritative machine-readable index is `reports/thesis_exploration/natview/study_summary.json`, with separate results in `v1/machine_summary.json` and `v2/machine_summary.json`. Each version retains its own `protocol.json` and `freeze.json`; the frozen model stays on M3. Closing hash and table checks are in `verification.json`, scheduler states in `jobs_sacct_complete.psv`, and exact local file paths/hashes in `delivery_manifest.json`. This document is an execution record, not a clinical claim.

## Pilot ingestion and clocks

The pilot is **sub-01/ses-01/rest**, development only. Nineteen audited objects total **127,034,404 bytes**, excluding the unsuitable Schaefer table. Sources are the audited NKI NATVIEW public S3 objects, attributed under **CC BY 4.0**; SHA256, public URLs, listed ETags, returned version/header metadata and local M3 paths are in `pilot_assets.json`. The reserved session-01 panel is fixed as **sub-04,05,06,08,10,11,12,13**, 152 objects / **980,089,695 bytes**. Its channel TSVs were inspected as acquisition metadata before freeze; no reserved EEG or BOLD outcome bodies were opened then.

Actual pilot EEG: 59 scalp channels, 250 Hz, average reference, 150,380 retained samples. `urevent` contains 288 R128 scanner events; the cleaned event stream contains 280, with 17 boundaries including the initial recording boundary. `clean_sample_mask` covers 155,600 original samples and removes 5,220 samples = **20.88 physical seconds**.

The raw task-relative R128 clock runs from -0.0446 to 602.6554 seconds. Original resampled SET recording time equals raw task time + **7.9356 s**, with constant offset independently checked across all scanner events. Surviving event-to-urevent links provide actual original volume identities; compressed cleaned event indices are never treated as volume numbers.

One source boundary at cleaned 1-based latency 149,895.5 stores duration335 samples, but the cumulative mask removes **732** samples there, original half-open interval `[154260,154992)`. The source duration is preserved. The discrepancy explains the extra397 samples; it is not silently overwritten. All **2,344** surviving event/urevent anchors agree with the mask to **2.91e-11 samples**, and every interior gap has a boundary at the correct compressed position. The mask is used only under those checks. Every removed interval, both clocks, event/volume link and excluded volume is retained in the clock/QC JSON files.

Independent eye clock: **285** scanner pulses identify original volumes **1–285**, missing **0,286,287**. Maximum absolute eye/raw-event difference is **15.4 ms**. The eye `Time` column already contains task-relative time; its first sample is -16.887 s despite sidecar `StartTime=-8.952`. The offset is not applied twice. Time formatting creates **75,019 nonincreasing steps**, largely quantized repeated timestamps. These limitations are explicit.

BIOPAC trigger TSV is a **sparse high-sample list**, not a regular binary waveform. Its447 rows all carry code5. Grouping neighboring high timestamps within100 ms yields **288** scanner pulses; elapsed time relative to the first pulse agrees with raw EEG within **24 ms**. Thus zero binary rising edges would have been an incorrect missing-trigger conclusion. The respiratory waveform covers0–609.696 s at62.5 Hz, with explicit time and voltage columns.

The pinned released CCS wrapper specifies **numDropping=0**. Bounded raw-header inspection and the processed volume each confirm288 frames atTR2.1 s. This payload/code evidence supersedes the paper's generic first-five-volume description for this particular release path. Pinned source code and the bounded header response have SHA256 receipts under `provenance/`.

Pilot retained **134 / 288** feature/target frames = **281.4 seconds** retained target duration, with six retained frame gaps. Each feature uses a nominal 24 s physical context ending at its scanner event, within one retained sample-mask segment, with the original baseline/crop and 5 s filtering margins on both sides. Filters are retrospective; endpoint handling and filter margins mean end-to-end causality is unclaimed. It never bridges an excised segment. This retained duration is not an independent number of24-second samples or continuous acquisition duration. Motion FD mean0.1213 mm, maximum0.5418 mm; FD>0.5 mm plus the following frame excludes volumes24/25, already outside valid histories here.

## Fixed feature/model bridge

The existing VU EEG feature cache has29 scans /16,327 rows. Before locking, every scan is audited against the original loader/epoch selector with original frame identities carried as artificial targets. All source frame indices and all65 normalized target rows are checked, the seven shared cache target columns are compared, and first/middle/last full feature rows are recomputed. The feature cache contains no frame keys itself; an equal concatenated row total alone is not accepted. Results and helper/cache hashes are in `VU_per_scan_cache_audit.json`.

The model retains23 selected source feature positions after removing VU F4/FT9/FT10, using44 one-Hz log-power bins ×12 two-second lags over24 s =12,144 inputs. It is refitted using only existing VU data. **Per-target alphas are retained from the existing all26-channel VU cv_A selector (geometric median across five folds); they are not newly optimized for common23 or NATVIEW.** Feature scaling uses only VU means and SDs. No NATVIEW target-stat adaptation, calibration or outcome tuning is used.

VU's last two source channels are literally **TP9'/TP10'**, and their stored locations differ from NATVIEW TP9/TP10. They are **always explicitly interpolated at the VU target directions**, not renamed to the NATVIEW measured channels. The geometry uses source SET donor directions and recorded VU target directions, normalized to a95 mm sphere; EEGLAB `[Xanterior,Yleft,Zup]` maps to head `[-Y,X,Z]`. MNE accurate spherical splines use fixed origin0. No signal-based geometry fit is performed. VU coefficients/scalers remain bitwise unchanged when the final model container records literal prime channel names.

There are **21 directly overlapping nonprime site names plus two always-interpolated primed sites**. Sub-05 additionally interpolates T8/CZ; sub-06 T8/FZ/CZ; sub-13 FP1/FP2/O2. These missing identities were inspected in channel metadata before outcomes. The fixed rule permits at most three such additional absent sites and requires at least40 measured donors with finite source coordinates. Thus five people have21 measured +2 interpolated feature sites, sub-05 has19+4, and sub-06/sub-13 have18+5, conditional on payload confirmation. This is not23 commonly measured channels across eight people.

The initial coefficient-fit container hash is `c7d2a46c05f711f89e5da4e24d148d47655ce868a1d0c1819b05044b10174fd4`. The **final model** hash is `dd9b894b805dd5a33fb5f5fbf741f8670439f81a3de709410320aba16ed0c7a9`. Only channel metadata changes between containers. The final protocol and freeze must reference the final hash and `bridge_geometry.json`, not the initial hash or an earlier draft standard-montage policy.

EEGLAB native microvolts agree with MNE volts×1e6 within1.42e-14 uV on the pilot check. Native VU SET reference is recorded as `common`; its physical electrode reference is not independently established here. NATVIEW is average reference over its retained scalp montage. Dropping/selecting channels does **not** harmonize those references. NATVIEW donor interpolation retains its existing voltage reference. Antialiased250→200 Hz resampling and0.5-Hz highpass are applied separately to each continuous physical segment; per-window baseline/cropping and log-power extraction reuse the existing baseline helper. Source cleaning, zero-phase filters and full-run target processing are retrospective; no complete online-causal claim follows from past-context feature windows.

## Targets, exclusions and endpoints

DiFuMo64 targets are re-extracted from the released no-filter/no-GSR/sm0 MNI3mm volume with `NiftiMapsMasker`, matching all64 VU region identities and ordering. The native EPI mask is64×64×38 and is not silently treated as an MNI mask. Global signal is the mean over explicit nonzero temporal support with SD>1e-8 in the released MNI volume (77,449 voxels in the pilot). Maps are resampled by their world-coordinate affine; shape or array-index equality is not assumed. The ragged supplied Schaefer table is unused.

Existing target steps are fifth-order0.15-Hz Butterworth `filtfilt`, full-run demeaning and absolute95th-percentile scaling. Released CCS nuisance correction uses motion24 and WM/CSF, without GSR for this path; no further fitted nuisance model is added. Atlas names/order are matched, but source spatial normalization, global-mask and nuisance-processing differences remain site confounds.

The frozen inclusion policy requires exact raw/urevent/BOLD counts, supported independent clocks, finite arrays, permissible geometry and at least60 retained frames. It excludes any history touching an excision/edge (including5 s filter margins), any selected-channel peak-to-peak>500 uV, and FD>0.5 mm plus the following frame. All eight people remain in the attempted-panel denominator, and failed checks or exclusions remain visible.

Primary accuracy endpoints use the **unshifted** scanner-volume mapping: temporal r for global signal and each of64 regions, normalized-target predictive R2, prediction/target SD amplitude ratio, and VU-global-adjusted regional residual skill. The residual endpoint subtracts a VU-trained global coefficient from both measured and predicted targets; measured BOLD is never a model input. This is an algebraic residual endpoint, not a separately tuned residual head.

Within-person CIs use2,000 stationary block-bootstrap replicates (expected10TR/21 s blocks, restarting at physical frame gaps); across-person means use10,000 equally weighted person resamples. The prespecified lag profile spans-5..5 original TR indices, minimum20 matched pairs, positive meaning prediction later than target. It is descriptive and never changes mapping or primary scores. The small panel, autocorrelation and overlapping EEG contexts limit precision and generalization.

Eye/pupil and respiration are independent measurements for timing/coverage QC here. Pilot pupil interpolation is**76.4%**; finite positive pupil area is not equivalent to directly measured coverage. No pupil-BOLD association or clinical arousal/sleep diagnosis is claimed. Missing pupil is not relabelled sleep, and EEG/ECG-derived proxies are not called independent truth. NATVIEW rest is instructed eyes-open fixation; VU/site/eye-state and target-processing differences remain confounded.

## Strict v1 result and preserved denominator

The original strict eight-person attempt is **not achieved as an eight-person accuracy confirmation**. Job **61207877** attempted all eight and retained only **sub-12,135 frames**. Six supplied masks have more true samples than final EEG samples: sub04+5796, sub05+14291, sub06+5466, sub08+3856, sub11+8331, sub13+4041. Sub10 has matching true count but an interior mask gap lacks the expected boundary position. These are failures of the pilot-derived cumulative-mask contract, not evidence that the dataset lacks scanner timing. Strict-v1 artifacts, original hashes and frozen source code are copied under `reports/thesis_exploration/natview/v1/`; the original derivatives remain on M3. Seven exclusions and the eight-person denominator are preserved. A single eligible recording is an ingestion result, not the requested eight-person external accuracy validation.

Independent metadata diagnostics (job **61207906**) show288 raw/urevent scanner events,285 eye pulses and288 BIOPAC pulses for every reserved person, with consistent clocks. Event-only segment audit **61207930** finds **no decreases in original-minus-processed sample offsets in any person**, across all surviving event links. No BOLD values or prediction correlation enter this diagnostic.

## Separately versioned v2 secondary adapter

The coordinator requested a metadata-only engineering correction within the authorized research scope after the strict attempt. **V2 is secondary and exploratory, not the original untouched confirmation.** It preserves the trained coefficients/scalers, the exact prime-electrode bridge and every numeric gate. It creates neither a repaired source mask nor filled temporal data.

For each retained event, compute the difference between its original `urevent` sample and its processed event sample. With fixed250 Hz sampling and excision-only changes, that offset cannot decrease. Equal offsets at two bracketing events rule out an intervening excision; an excision would increase the offset. V2 requires exact integer offsets (floating residual at most1e-6 sample), monotonicity over **all** surviving links, and both endpoints bracketing the complete24 s history plus the original5 s filter margins. It also splits at **every** source boundary, even if its stored duration is misleading, and never extrapolates beyond the first/last certifying anchor. Original R128 identities and all independent clock gates remain unchanged. The already-cleaned EEG is indexed within these certified excerpts; the helper's computational identity index does not claim to be the physical timeline.

The metadata-only audited frame counts before amplitude/motion exclusions are:

| Person | Candidate physical-history frames | Retained target seconds | Original minimum60 gate |
|---|---:|---:|---|
| sub-04 |166|348.6|pass before additional QC|
| sub-05 |27|56.7|exclude|
| sub-06 |142|298.2|pass before additional QC|
| sub-08 |64|134.4|pass before additional QC|
| sub-10 |28|58.8|exclude|
| sub-11 |98|205.8|pass before additional QC|
| sub-12 |133|279.3|pass before additional QC|
| sub-13 |176|369.6|pass before additional QC|

Most supplied masks are consistent with an intermediate mask followed by additional excision when compared with the full event chronology. Sub08 additionally places one surviving anchor in a source-mask-false interval. The published ASR call enables both burst and window rejection, but the exact internal writer/stage for each released mask is **not established**. These observations are preserved in v2 metadata diagnostics; stage identity is not assumed by the adapter.

V2 audit **61208083** reads metadata/clock/coverage only. V2 freeze **61208097** runs the amended invariant tests and locks policy, metadata, unchanged helper sources, geometry and final model before v2 prediction job **61208118**. Sub05/sub10 remain excluded: the60-frame minimum is not relaxed, and no accuracy scores are computed for them. Amended final metrics and actual scheduler outcomes are recorded in `v2/machine_summary.json`, `v2/per_person_metrics.csv`, `v2/regional_metrics.csv`, `v2/coverage_QC.csv` and the combined `study_summary.json`.

## Completed amended secondary results

**All8 clocks are certified;6/8 people pass unchanged final QC.** Final retained frames in panel order are **166,4,134,64,23,67,133,176**. Additional amplitude/motion exclusions reduce the metadata-only candidate counts; the full per-volume reason lists and FD traces/summary are retained. Sub05/sub10 remain in the denominator and have no accuracy score. The six evaluated people contribute **740/2304 possible frames (32.1%) /1554.0 retained target seconds**, across discontinuous acquisition spans. These are not740 independent24-second contexts.

| Endpoint | Equal-person mean temporal r | 95% person-bootstrap interval | Mean normalized-target predictive R2 | Mean amplitude ratio |
|---|---:|---|---:|---:|
| Global |0.1249|[-0.0330,0.2760]|-0.0431|0.1585|
| Regional64 mean |0.1038|[-0.0002,0.2071]|-0.0714|0.1492|
| VU-global-adjusted regional residual64 |0.0248|[-0.0050,0.0546]|-0.0722|0.0968|

This is **weak transfer with under-amplitude predictions and negative predictive R2**, not demonstrated external reconstruction accuracy. Regional/global correlation intervals include zero, and the remaining residual association is small. The result does not establish that EEG-to-fMRI transfer is impossible: native reference, geometry interpolation, eye/task/site differences, cleaning/target definitions and limited continuous histories remain confounded. No hyperparameters, participant choices, clock offsets, calibration or lags were selected from these outcomes.

The exact v2 protocol SHA256 is `02f3138499a33c3f683a3c7b17899651bc968dd44ca2791edf7bc96bb71531d7`; v1 is `005d4145fd51f297df8133ee28870bb7b9f97f1eb04f0533e047817ce241d035`. Both reference the same final model `dd9b894b805dd5a33fb5f5fbf741f8670439f81a3de709410320aba16ed0c7a9`. V2 is frozen before its new predictions and after v1 exposure; it is not relabelled untouched confirmation.

Selected actual scheduler evidence:

| SLURM job | Purpose | Actual outcome |
|---|---|---|
|61207459|Pilot payload inspection|completed|
|61207492|Common23 VU ridge fit, all26 selector|completed,5:59, peak7,853,476 KiB|
|61207729|All29 VU per-scan source-frame/cache checks|completed; exact frame identities and recomputed feature checks|
|61207771|Prime-site geometry/model container finalization|completed; coefficients/scalers bitwise unchanged|
|61207781|Final v1 pilot QC|completed,134 frames|
|61207783|Original invariant tests|8 tests passed|
|61207793|Original v1 freeze|completed|
|61207877|Original strict8-person attempt|completed operationally;7 clock-contract exclusions,1 eligible,5:09, peak2,768,668 KiB|
|61207884|Strict-v1 compact result package|completed|
|61207906|Independent clock/mask diagnostics|completed; all8 scanner clocks independently supported|
|61207930|All-event piecewise timing certificate audit|completed;0 offset decreases in all8|
|61207961|Preserve v1 artifacts/frozen sources|completed;103 top-level files copied plus provenance/frozen sources|
|61208050|Initial v2 metadata parser|failed on JSON null boundary duration; repaired before v2 freeze, no v2 predictions existed|
|61208083|Final metadata-only v2 audit|completed|
|61208097|V2 freeze and amended tests|completed,1:36,4 tests passed, peak295,856 KiB|
|61208118|V2 secondary extraction/prediction/scoring|completed0:0,6:59, peak3,285,036 KiB,8 CPU/32 GiB requested|
|61208120|Amended result tables/plots/provenance|COMPLETED0:0,1:07, peak264,568 KiB|
|61208309|Closing hash and table verification|COMPLETED0:0,0:05, peak56,896 KiB; PASS|

Closing verification **61208309** passed **207 hash checks**, including current and archived frozen source code, both protocols, the final model copies, fixed spatial bridge, metadata certificates and preserved strict-v1 artifacts. All reported equal-person means match the per-person tables. The original invariant suite passed8 tests, the amended suite passed4, and the VU correspondence audit passed all29 scans. These checks add no experiment arm.

Earlier pilot/cache-audit repairs and their actual exit states are preserved in the full scheduler ledger and logs; operational `COMPLETED` alone is not equated with a passed scientific gate. Downloads are login-node receipts rather than SLURM jobs. Source EEG/BOLD and prediction arrays remain on M3; only compact results/docs/plots are returned locally. No deletion, commit or push occurred.

The empirical constraint is coverage: fixed24 s history and retrospective filter margins lose usable targets around source excisions, even where scanner clocks are recoverable. This motivates future tests of estimators for irregular/missing observations and selective prediction with explicit abstention. No extra model arm or larger architecture is tested in this extension.
