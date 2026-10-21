# EEG to fMRI: what the poster means

**Summary.** EEG can predict some fluctuations in healthy resting BOLD, but the completed experiments do not demonstrate accurate clinical fMRI replacement. More training people and retained recording time helped within development data. A matched-feature MLP did not improve the strongest simple baseline. External transfer was weak and depended on substantial timing and quality checks. A defensible computer science PhD would investigate measurement information, constrained adaptation and calibrated abstention, with one clearly defined application.

## 1. What is being reconstructed?

EEG measures voltage differences at the scalp. Those voltages mix electrical activity from many sources and depend on electrode locations and reference. BOLD is an MRI contrast linked to blood oxygenation. It depends on neural activity, vascular responses and systemic state. An EEG-to-BOLD model learns a statistical relationship between these observations; it does not turn an electrical measurement into a direct measurement of blood flow.

<!-- figure: physiology -->

The target in these studies is usually an atlas-region time course. A region of interest, or ROI, compresses an area's MRI signal into one number per frame. Predicting 64 such series is narrower than reconstructing a complete clinical scan, an individual's anatomy or a lesion map.

The mapping may be ambiguous: different underlying states can produce similar EEG while producing different BOLD. This motivates asking which targets are recoverable from a specified history and sensor setup. It does not prove that no useful target can be predicted, or that the observed error is an unavoidable biological ceiling.

Keep four endpoints separate: **signal fidelity** asks whether the predicted trajectory matches measured BOLD; **representation quality** asks whether features help another task; **target engagement** asks whether feedback changes a chosen physiological target; **clinical benefit** asks whether patients or workflow improve. Success on one does not establish the others.

**Say to an advisor:** "We are testing a limited cross-modal estimator. The clinical question has to name the target and the decision, rather than promise an MRI replacement."

Source: [reviewed research report](../Clinical%20EEG%20fMRI%20thesis%20exploration.md), [brain-body coupling](https://www.nature.com/articles/s41593-025-01945-y).

<!-- page -->

## 2. What the M3 experiment actually tested

The completed ds006040 study used 27 people and 54 eyes-closed/eyes-open recordings. Three outer folds held out whole people. Separate inner validation selected settings. This prevents neighbouring windows or another run from the same person from appearing on both sides of the primary person-level test.

<!-- figure: pipeline -->

Each EEG input summarized the preceding 24 seconds: five scalp groups, five frequency bands and twelve lag bins. Multiplying these dimensions gives **300 log-power features**. Both the ridge model and small multilayer perceptron, or MLP, received these EEG features. This isolates a bounded comparison of estimators on this representation; the MLP is not a raw-waveform foundation model.

Ridge regression fits a linear weighted combination of features with a penalty on large coefficients. The penalty stabilizes a problem with correlated features. The MLP can learn nonlinear interactions, but additional flexibility also requires more evidence to estimate reliably.

The experiment crossed 4/12 training people, 120/240 retained target-seconds per person, and EEG/ECG timing-and-availability/combined inputs. Mixed-state and availability controls completed **96 fitted outer cells, 48 per estimator**. These cells reuse the same 27 people; they are not 96 independent cohorts.

The MLP learned four equally weighted target groups: global, regional, global-adjusted regional, and global-plus-physiology-adjusted regional outputs. Ridge and MLP therefore differ in both estimator and training objective. Their comparison cannot establish a general theorem that nonlinear models are unnecessary.

The primary plot was specified before outcomes: eyes-closed training/testing, 12 training people, 240 retained seconds, 64 full regional targets. Intervals resample people, not individual frames. One training subset order and one neural seed limit the generality of the comparison.

**An important boundary:** past-only feature windows do not make the complete pipeline online. Inherited cleaning, target filtering/normalization and QC margins remain retrospective. The experiment tested prediction from processed data.

Sources: [protocol](data/protocol.json), [primary results](data/poster_scores.csv), [execution note](../../research_notes/Clinical%20EEG%20fMRI%20thesis%20exploration/M3%20experiments.md).

<!-- page -->

## 3. How to read the performance numbers

**Temporal correlation, r,** measures whether predictions rise and fall with the target. It ignores positive rescaling and constant offsets. **Predictive R²** compares squared prediction error with a specified mean-reference benchmark. It penalizes scale and offset errors; a negative value means greater squared error than that benchmark. Predictive R² is not generally the square of r.

<!-- figure: correlation -->

In the mathematical example above, the target has mean zero and variance one. Predicting 0.2 times the target plus 1 gives perfect correlation, but predictive R² is 1 - (0.8² + 1²) = -0.64. The model tracks timing while getting the trajectory badly wrong. These are illustrative signals, not participant data.

| Completed primary arm | Regional r | Predictive R² |
| --- | ---: | ---: |
| Ridge EEG | 0.1886 | 0.02788 |
| Ridge ECG timing/availability | 0.0177 | -0.00441 |
| Ridge EEG + ECG | 0.1782 | 0.02309 |
| Small MLP EEG | 0.1223 | 0.00678 |

The EEG ridge result shows modest temporal agreement and a small squared-error improvement in normalized target units. It does not mean that 18.9% of a scan or 2.8% of neural activity was recovered. The poster's confidence bars describe uncertainty across people under this design, not a guarantee for a future patient.

**Regional specificity also matters.** A global state signal can help predict many regions at once. Ridge's regional correlation gain over its own predicted-global template was only 0.004, with a paired 95% interval from -0.008 to 0.017. These data do not establish a reliable regional advantage. Connectivity agreement and accurate individual trajectories are also different endpoints.

More people and retained time improved the learning comparison, but longer segments also change sampled state/content. Four learning points from fixed subsets are not a scaling law or a data-size requirement for clinical use.

Sources: [full estimates and contrasts](data/summary.json), [learning points](data/poster_learning.csv).

<!-- page -->

## 4. What NATVIEW revealed about transfer

NATVIEW introduced recordings from another acquisition setting. This study froze a VU-trained ridge model and attempted eight reserved people; an additional ingestion pilot was excluded from accuracy estimates. NATVIEW is instructed eyes-open rest. Site, state, reference and preprocessing differences remain intertwined.

<!-- figure: natview -->

The original strict protocol required a particular cumulative sample-mask contract. Only one of eight recordings passed. This means the planned eight-person confirmation was not achieved. It does not mean that seven recordings contained no useful data.

A separately frozen amendment reconstructed timing using original/processed event relationships and independent clock evidence. It split at physical gaps rather than filling or stretching time. Model coefficients, scalers, spatial bridge and numeric QC thresholds stayed fixed. Because this amendment followed the first QC results, its accuracy analysis is **secondary exploratory**, not the original untouched confirmation.

Six people met the amended eligibility threshold; two did not have enough usable frames. The scored set contained 740 of 2,304 possible frames across all eight people, or 32.1%. A required continuous 24-second history and filter margins make gaps costly. An estimator that handles irregular observations is therefore a concrete research direction, not yet a demonstrated solution.

Regional r was **0.1038**, with a person-bootstrap 95% interval of **-0.0002 to 0.2071**. Predictive R² was **-0.0714** against the retained-target-mean benchmark. These results do not establish accurate external reconstruction. High rejection can also change the population and states being evaluated, so coverage must accompany accepted-set accuracy.

This model used **23 target sites x 44 frequency bins x 12 lags = 12,144 features**, unlike the 300-feature M3 comparison. Two prime-labelled target sites were always interpolated; some records required additional interpolation. References were not shown to be physically equivalent. Do not subtract the two studies' scores and call the difference a pure site effect.

Sources: [strict/amended study record](natview/study_summary.json), [v2 results](natview/v2/machine_summary.json), [QC and coverage](natview/v2/coverage_QC.csv).

<!-- page -->

## 5. What newer models and clinical evidence support

The following are published results, not models reproduced in the current M3 comparison. Their targets, preprocessing and evaluation protocols differ. Their reported plus/minus values are standard deviations, not the confidence intervals used in the project plots.

| Model | Main reported technical result | Interpretation |
| --- | --- | --- |
| UnEBOLT | 64 ROIs; temporal r 0.418; 8.2M parameters | Shared EEG encoder with ROI-conditioned adapters/heads; candidate regional feedback representation. |
| UniEFS | 512 ROIs; temporal r 0.367 | fMRI-pretrained decoder plus EEG/context; its Parkinson classification probe is a different endpoint. |
| MARBLE | 64 ROIs; temporal r 0.434; 2.6M parameters | Compact Mamba/attention model; stronger temporal scores did not also give the best connectivity score. |

<!-- figure: unebolt -->

The main evaluations share substantial VU data. Three papers are not three independent clinical replications. UnEBOLT also reports a small healthy auditory-cohort transfer test; that is distinct from demonstrating reliable performance in patients or arbitrary new sites.

UniEFS's main paired experiment contains 29 healthy people/39 scans. Its fMRI decoder pretraining uses 375 people/1,500 HCP scans, which are not 1,500 paired EEG-fMRI recordings. Its Parkinson probe used EEG-only data from 44 people and a fitted classifier. Classification performance does not measure whether patient BOLD trajectories were reconstructed correctly.

**A real clinical precedent is narrower.** Prism's FDA clearance covers adjunctive PTSD EEG biofeedback under professional supervision and excludes diagnostic interpretation. This is evidence for a specified intervention, not regulatory approval of UnEBOLT, UniEFS, MARBLE or diagnostic fMRI substitution. Likewise, a rehabilitation study using actual simultaneous EEG-fMRI cannot by itself validate synthetic BOLD feedback.

The two plausible research routes here are a wakefulness advisory, compared with direct EEG, and feedback from one prespecified ROI, first validated against actual paired patient fMRI. Each route needs its own reference, success criteria and benefit study. A model leaderboard cannot substitute for those steps.

Sources: [UnEBOLT](https://proceedings.mlr.press/v315/li26g.html), [UniEFS](https://proceedings.mlr.press/v306/li26gp.html), [MARBLE](https://papers.miccai.org/miccai-2026/0612-Paper4437.html), [FDA K222101](https://www.accessdata.fda.gov/cdrh_docs/pdf22/K222101.pdf).

<!-- page -->

## 6. The mathematics behind a useful PhD

Let X contain the available sensor history and Y be one specified BOLD target. Under squared loss and finite variance, the best predictor for a fixed population is the conditional mean m(X) = E[Y | X]. Prediction error separates as follows:

> E[(Y - f(X))²] = E[Var(Y | X)] + E[(m(X) - f(X))²].

The first term is variation that remains after observing this X. The second is error in estimating the conditional mean. A larger model may reduce the second term; different sensors, better measurements or a different target can change the first. An observed residual includes both, so it cannot identify an irreducible ceiling on its own.

**Observability is target-specific.** The question is whether a target or function of a latent state can be recovered from the observations under stated dynamics and measurement assumptions. It is not necessary to identify every neural generator to predict one useful target. Conversely, a model with a convincing latent-state diagram need not uniquely identify its underlying physiology.

This suggests a constrained contribution: specify the classes of observation/haemodynamic operators, characterize equivalent parameterizations, and test whether an information diagnostic predicts which measurement changes improve held-out targets. Known-state simulations can test these assumptions directly; observational human data cannot automatically identify all of them.

**Selective prediction introduces a second trade-off.** Let A(X) indicate whether the model reports an estimate. Coverage is P(A = 1); accepted risk is E[loss | A = 1]. A system can appear accurate simply by rejecting almost everything. Always compare risk at matched coverage, including simple signal-quality rejection.

Calibration guarantees require a defined sampling regime. Exchangeable-person calibration does not guarantee every individual or an arbitrary new hospital. Covariate-shift corrections need support and conditional-law assumptions. A vascular change may alter BOLD given EEG without an obvious EEG-input alarm. EEG-only deployment does not reveal the true BOLD residual.

**The CS opportunity:** an assumption-explicit estimator, calibration method or useful limitation result that addresses the failures observed here. A new HRF layer, latent-state name or adaptation module alone is not evidence of novelty.

Sources: [functional observability](https://arxiv.org/abs/2201.07256), [grouped calibration](https://arxiv.org/abs/2306.06342), [covariate shift](https://arxiv.org/abs/1904.06019), [risk control](https://arxiv.org/abs/2101.02703).

<!-- page -->

## 7. Three experiments that could form the thesis

### WP1: measure which observations help

Develop a finite-history, noise-aware measurement diagnostic for a specified target. Compare its recommended montage, history length and auxiliary sensors with random, uniform and cost-matched alternatives. Establish behaviour first in simulations with known operators, then in person/site holdouts.

**Positive evidence:** predicted rankings anticipate held-out improvements with useful precision. **Failure criterion:** recommendations do not improve target error or are too conservative to guide acquisition. A carefully established failure can still clarify what the proposed diagnostic cannot identify.

### WP2: estimate dynamics through gaps and domain changes

Compare a structured, time-aware estimator with fixed-window ridge. Preserve actual timestamps and missingness; do not interpolate across missing time as if it were observed EEG. First validate a physical montage/reference harmonization baseline, then test constrained operator/haemodynamic adaptation.

Count every paired calibration minute and test later people, visits and a frozen domain. Include output-only recalibration, state/physiology priors and a predicted-global template. Missingness-aware dynamics should earn its complexity through target error and useful coverage.

**Failure criterion:** apparent gains vanish after these controls, or adaptation does not generalize. The engineering harmonization baseline is necessary, but is not itself an original PhD contribution.

### WP3: make reporting a calibrated decision

Combine measurement diagnostics and predictive uncertainty to choose which estimates to report. Compare accepted risk, coverage and interval width with quality rejection, model disagreement and established calibration methods. Reserve independent people for calibration and external audit.

**Failure criterion:** useful coverage collapses, intervals become uninformative, or errors violate the supported-domain claim. Report these outcomes rather than weakening the acceptance rule after seeing test targets.

### What would connect the packages?

WP1 chooses information; WP2 estimates the target; WP3 decides whether to report it. The shared hypothesis is that measurement structure and constrained calibration improve useful prediction beyond simply increasing model capacity. Each package still needs an original algorithm or rigorous result, strong controls and a falsifiable claim.

The candidate and supervisors should select one primary target and one decisive test per package. A nominal 0.02 predictive-R² gain is a planning example, not an established clinical threshold. Required precision and tolerances must be fixed before the new audit.

Sources: [full thesis rationale and prior art](../Clinical%20EEG%20fMRI%20thesis%20exploration.md), [frozen NATVIEW protocol](natview/v2/protocol.json).

<!-- page -->

## 8. Prototype, resources and human responsibilities

The first application prototype could be a **research wakefulness advisory** during one specified adult MRI protocol. It would display a review prompt or insufficient-signal state. It would compare direct EEG vigilance, power-based BOLD proxies and a proposed structured estimator using the same causal inputs. This is a next prototype to build and evaluate, not a clinically validated product delivered by these experiments.

<!-- figure: prototype -->

A sleep clinician and technologist must define the event, action and tolerable false-alert burden. Use blinded adjudication with suitable independent corroboration; pupil missingness is not a sleep label. Compare event sensitivity, false alerts/hour, onset delay, calibration and monitored coverage. If inferred BOLD adds no useful value, remove that intermediary.

| Resource | What it is needed for |
| --- | --- |
| Public paired data and M3 | QC, ridge controls, modest profiled neural models and reproducible thesis experiments. |
| EEG/MR specialists | Physical clocks, montage/reference, units, artifacts, prospective cleaning and target validity. |
| Repeated paired visits | Separate personal calibration from later-visit evaluation; measure stability without assuming repeated trajectories. |
| Clinician, statistician and research partners | Independent events, clustered precision, patient recruitment, ethics, funding and workflow evaluation. |

Earlier ranges of 40-80 people for feasibility, 150-300 for advisory development, 300-600 for feedback, or a conditional 1,000+ programme are **planning scenarios**, not known accuracy requirements. No verified scaling law maps a parameter count and number of people to clinical readiness.

For illustration, 40-80 people with two 30-minute visits yield 40-80 acquired paired hours; hypothetical 75% retention leaves 30-60 usable hours. The real budget must separately cover training diversity, calibration people, untouched sites and sufficient independent clinical events. More windows from the same recording do not provide the same evidence as more independent people.

For ROI feedback, the sequence changes: choose one meaningful target, validate paired patient sign/amplitude/lag/repeatability, then test controlled intervention benefit. Neither clinical clearance nor a large patient trial should be a PhD graduation dependency.

Sources: [planning assumptions and collaborators](../Clinical%20EEG%20fMRI%20thesis%20exploration.md), [DECIDE-AI](https://www.bmj.com/content/377/bmj-2022-070904), [TGA AI evidence guidance](https://www.tga.gov.au/products/medical-devices/software-and-artificial-intelligence-ai/manufacturing/artificial-intelligence-ai-and-medical-device-software-regulation/evidence-requirements-software-using-ai).

<!-- page -->

## 9. How to explain this to an advisor

### A five-minute account

**Question, 30 seconds:** "Can EEG support one clinically useful BOLD-related target, and can a model know when its estimate is unreliable? We are not assuming that an atlas time course replaces a diagnostic scan."

**Method, one minute:** "We compared simple and nonlinear estimators on identical lagged power features, tested unseen people and varied the number of training people and retained seconds. We also froze a VU model for an external NATVIEW feasibility test."

**Finding, one minute:** "The simple EEG baseline led the matched-feature comparison, with r about .189 and predictive R² about .028. More data helped within this design, but regional improvement over a global template was uncertain. This is not a proof of a biological ceiling."

**Transfer, one minute:** "The original NATVIEW input contract admitted only one of eight people. A separately frozen timing amendment admitted six, but covered only 32.1% of attempted frames and gave weak, poorly calibrated predictions. This motivates physical measurement audits and missing-observation models."

**Thesis and request, 90 seconds:** "I propose measurement diagnostics, constrained transfer with counted calibration, and selective prediction under explicit assumptions. I need help choosing the original mathematical contribution, one primary target, and collaborators who can validate the physical measurements and clinical references."

### Questions worth deciding together

- Which target would still be useful if whole-scan reconstruction remains weak?
- What would a simpler direct-EEG method have to achieve to make BOLD synthesis unnecessary?
- Which part of the proposed method is novel relative to functional observers, adaptation and calibration research?
- Can the required measurement/reference assumptions be checked in available data?
- What result would make us abandon each positive hypothesis, while preserving a viable thesis?

### How to divide human and AI work

AI can accelerate code drafting, literature triage, traceable tables, plots and reproducibility checks. Humans must determine clinical meaning, inspect raw physiological/clock/reference validity, challenge causal interpretations, negotiate access and ethics, and judge originality against the actual primary literature. Require versioned protocols and auditable results from both human and AI contributions. A fluent explanation is not new evidence.

The immediate next step is a supervisor-approved WP1 target and a frozen WP2 benchmark specification. Clinical recruitment follows a credible acquisition and validation plan, rather than being assumed into the thesis schedule.

Evidence cutoff: 21 October 2026. The revised poster and this explanatory guide add interpretation and presentation; no new M3 experiment was run for this revision. See the [reviewed report](../Clinical%20EEG%20fMRI%20thesis%20exploration.md) for the full literature and uncertainty record, and the [project repository](https://github.com/seamus-programming-stuff/NeuroBOLT) for source and results.
