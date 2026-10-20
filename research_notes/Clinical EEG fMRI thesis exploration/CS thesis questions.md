# CS thesis questions for EEG-to-fMRI

**Evidence cutoff: 21 October 2026. Recommendation: pursue a thesis on target-specific inference, transferable dynamical estimation and selective prediction.** The defensible ambition is to determine which individual BOLD features can be recovered, with which observations and calibration costs, and when the estimator must withhold a result. Clinical fMRI replacement is not the thesis hypothesis.

This exploration builds on [Clinical EEG to fMRI feasibility](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/Clinical EEG to fMRI feasibility.md>). That report supplies project context, not independent validation. Primary sources were checked online for this note; source-specific limitations are identified below. Equations labelled as deductions are standard mathematical consequences under stated assumptions. Experiments, numerical decision margins and resource envelopes are **proposals**, not published findings, clinical acceptance standards or claims of novelty. No experiments were run for this exploration.

**Poster title:** *When can EEG support individual BOLD inference? Information, transfer and selective prediction.*

**Poster-ready thesis hypothesis:** *For prespecified regional BOLD targets, a model that accounts for measurement geometry, haemodynamic dynamics and limited personal calibration will outperform brain-state and physiology priors on unseen people and sites; calibrated abstention will reduce accepted-prediction error at useful coverage under explicitly stated sampling and shift assumptions.*

**Three research questions:**

1. **Information:** Which target-relevant information is absent from the available measurements, and which prediction errors can be reduced by better estimation, richer measurements or personal calibration?
2. **Identification and transfer:** Can a structured multimodal dynamical estimator preserve individual regional BOLD variation beyond brain-state priors across subjects, sessions and acquisition sites?
3. **Reliability:** Which uncertainty and selection guarantees are defensible for these targets under dependence and distribution shift, and when is withholding a prediction preferable?

These questions form three linked work packages. The first specifies the target and information budget, the second learns the estimator, and the third determines its supported operating conditions. The positive hypothesis can fail in parts or as a conjunction. A rigorous negative result can support a thesis contribution without supporting a clinical product.

## 1. Which errors reflect information limits, and which reflect estimation?

### Takeaway

Observability is a property of a specified target, measurement process and dynamical model. A residual from a fitted predictor does not separate missing information from model error; the practical research task is to test competing explanations through controlled changes in measurements, training data and estimator capacity.

### Cited Findings

- **Useful prediction already exists, so “EEG contains no fMRI information” is untenable.** NeuroBOLT reports held-out-subject mean temporal correlation of .473 over six selected regions plus global BOLD. This is a particular target set and protocol, not a whole-brain or clinical fidelity threshold. — [NeuroBOLT, NeurIPS 2024, Table 1](https://arxiv.org/html/2410.05341v2).
- **The 2026 frontier already includes multi-region models and strong priors.** UnEBOLT predicts multiple regional time series and derives connectivity; MARBLE investigates lightweight Mamba/attention and ROI-conditioned decoding; UniEFS uses a pretrained fMRI decoder and context prompts. Therefore, multi-region prediction, efficient architectures, context conditioning and spatial pretraining are existing research directions. Official proceedings records/abstracts were verified; inaccessible full-paper fetches for some 2026 papers mean this note does not independently re-audit all their numerical results. — [UnEBOLT, MIDL 2026](https://proceedings.mlr.press/v315/li26g.html); [MARBLE, MICCAI 2026](https://papers.miccai.org/miccai-2026/0612-Paper4437.html); [Mind the State / UniEFS, ICML 2026](https://proceedings.mlr.press/v306/li26gp.html).
- **Recovering a target need not require recovering the entire hidden state.** Functional observability theory supplies target-specific rank conditions and sensor/observer design methods for dynamical networks. This is prior mathematics, not a new EEG thesis theorem. — [Montanari et al., PNAS 2022](https://arxiv.org/html/2201.07256).
- **Global brain state is a substantive competing explanation.** Bolt et al. find widespread coupling among global fMRI, EEG and autonomic measurements across independent samples. Their findings also argue against explaining the entire pattern by respiratory CO2 alone. A global/physiological predictor is therefore an essential comparator, and removing global variation does not automatically isolate a purely neural local signal. — [Bolt et al., Nature Neuroscience 2025, primary abstract](https://pubmed.ncbi.nlm.nih.gov/40335772/).
- **A measured-fMRI noise ceiling requires a measurement model.** Noise-ceiling estimates depend on assumptions about signal repetition, noise covariance and temporal structure; misspecification can bias the estimate. This constrains interpretation of a plateau against noisy BOLD, but does not supply an EEG-specific ceiling. — [Lage-Castellanos et al., PLOS Computational Biology 2019](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006397).

### Inferences

#### Work package 1: target-specific information and measurement design

**CS contribution candidate:** develop and evaluate a target-aware diagnostic for choosing EEG montage/history and auxiliary measurements, using a specified dynamical model and uncertainty about its measurement operators. The diagnostic should predict which additions improve a regional target, and be assessed against uniform, random and cost-matched choices. The controlled benchmark is necessary evidence; simply running more architectures is not the proposed methodological contribution.

Start with a small, declared target family: global BOLD as a positive control, a small set of cortical ROI traces, and prespecified regional contrasts. Keep subcortical targets as a separately reported difficulty stratum if data support them. Fix the temporal resolution, causal history, prediction timestamp and preprocessing. A target may be predictable at one spatial/temporal scale and poorly constrained at another.

**Deduction: the relevant decomposition is input- and distribution-specific.** Let \(X\) contain exactly the measurements and calibration information permitted at prediction time, and let \(Y\) be one specified measured BOLD target. For a fixed test distribution \(P\), finite second moments and a predictor fitted independently of the evaluated outcome, write \(m_P(X)=E_P[Y\mid X]\). Then

\[
E_P[(Y-f(X))^2]
=E_P[\operatorname{Var}_P(Y\mid X)]
+E_P[(m_P(X)-f(X))^2].
\]

More specifically,

\[
E_P[(Y-f(X))^2\mid X=x]
=\operatorname{Var}_P(Y\mid X=x)+(m_P(x)-f(x))^2.
\]

A large residual, residual variance or neural-network variance estimate does not identify the first term. Conditional variance is a well-defined functional of the population joint distribution; it is **not inherently unknowable**. Estimating it from finite, high-dimensional paired data needs assumptions, repeated information or a sufficiently accurate conditional model. Nor does statistical conditional variance identify how much variability is biological rather than measurement noise. A well-fitting model's residual can be informative under justified assumptions; a poorly fitting model's residual cannot be renamed “irreducible uncertainty.”

For an additional measurement \(W\), the population Bayes-risk reduction under squared loss is

\[
R_P^*(X)-R_P^*(X,W)
=E_P[(E_P[Y\mid X,W]-E_P[Y\mid X])^2]\geq0.
\]

This follows from conditional expectation and total variance. It explains what an information gain would mean, but the difference between two finite fitted models is not automatically this quantity. Extra inputs can hurt a finite estimator through variance, tuning or shift. Report **held-out predictive gain**, not an identified reduction in biological uncertainty, unless the additional identification assumptions are supported.

**Deduction: a narrow observability test is available.** For a known, noiseless linear system \(z_{t+1}=Az_t\), measurements \(e_t=Cz_t\), and target \(q=Fz_0\), define \(\mathcal O_T=[C^\top,(CA)^\top,\ldots,(CA^{T-1})^\top]^\top\). The target is uniquely determined from this observation history exactly when

\[
\ker\mathcal O_T\subseteq\ker F,
\quad\text{equivalently}\quad
\operatorname{rank}\begin{bmatrix}\mathcal O_T\\F\end{bmatrix}
=\operatorname{rank}(\mathcal O_T).
\]

Indistinguishable initial states must agree on the target. For a target at a later time, use its corresponding state-to-target operator. Known inputs can be accounted for; unknown neural/vascular inputs, noise and unknown operators require additional analysis. This is an application of established functional-observability reasoning, not a proof that scalp EEG can or cannot recover actual human BOLD. — [Mathematical antecedent](https://arxiv.org/html/2201.07256).

The research extension would be a useful **finite-history, noise-aware measurement diagnostic** over plausible lead fields and haemodynamic operators. For example, rank candidate sensor sets by worst-case target error amplification over a declared operator set, then test whether this ranking predicts held-out improvements. State the operator set and sensor costs. Distinguish exact rank from poor numerical conditioning: an observable system can still require impractically accurate measurements. A learned model's reassuring rank cannot certify the correctness of that model.

This extension needs a detailed comparison with existing functional observers and sensor-design methods before it can be called novel. A generic rank calculation, an observability Gramian or a standard greedy sensor-selection algorithm is not sufficient originality.

#### Experiments that discriminate explanations

Use a crossed design, restricted to what each dataset actually records. Keep evaluation subjects, target definitions and jointly available recordings fixed when comparing inputs. Report a separate analysis if requiring auxiliary sensors changes the cohort.

| Experimental axis | Proposed controlled comparison | What a positive result supports; what it does not establish |
|---|---|---|
| Measurements | Nested electrode subsets up to the acquired montage; electrode geometry/anatomy where available; EEG alone, available physiology alone, and their combination | Value of those measurements for that target/protocol. Subsampling one cap is not a complete test of a different physical cap or amplifier. |
| Representation/history | Spectral power versus retained broadband/phase-sensitive features; several prespecified causal history lengths | Recoverable representation/context loss. Features require artifact controls; a larger feature set does not constitute new sensing. |
| Estimation | Tuned lagged ridge, structured dynamical estimator, one compact nonlinear comparator, with matched information and tuning budgets | A demonstrable estimation improvement. A null comparison is not a Bayes-optimality result. |
| Training resource | Vary unique people, minutes/person and capacity separately, with fixed development evaluation subjects | Which sampled resource improves generalization. A small learning-curve plateau is not a universal biological ceiling. |
| Personal information | No paired calibration versus a declared amount from a separate visit | Benefit and cost of patient/person calibration. This changes the information regime and cannot be labelled zero-shot. |
| Target reliability | Repeated task responses, acquisition quality and justified noise models, when available | Target repeatability/noise sensitivity. Separate resting visits do not repeat an identical spontaneous trajectory. |

Never infer capnography from the existence of a respiration belt. Missing sensors are missing information. Include artifact references, motion and muscle-contamination controls where recorded, and ask whether physiological improvements reflect more faithful BOLD estimation, state prediction, contamination or some combination. These interpretations need physiological expertise.

**Falsifiable WP1 hypothesis:** a target-aware measurement choice predicts a larger held-out gain for prespecified regional contrasts than a cost-matched uniform/random choice, across declared operator perturbations and at least one independent real-data acquisition domain. Compare predicted ranking with observed ranking; report both failures and uncertainty. Simulations with known states establish behaviour inside the simulator, not human observability.

**Gate G1 — choose the next investment.** Before confirmation, define a smallest worthwhile predictive gain \(\Delta_{\min}\). An illustrative research margin is **0.02 in held-out predictive R²**, not 0.02 Pearson correlation and not a clinical standard. Support an added-sensor or added-model claim only when its prespecified effect exceeds the margin and the participant-level uncertainty interval excludes zero, with independent replication for a transfer claim. If an equivalence interval lies wholly inside a prespecified negligible-effect region, deprioritize that addition within the tested scope. If the interval is wide, the result is inconclusive. The candidate contribution fails if its recommended measurements do not beat cost-matched alternatives with adequate precision; the comparison still informs acquisition design.

**Useful negative result:** show that, within a declared target/montage/population and tested estimator family, extra capacity has little supported gain while a particular measurement change helps—or that neither helps with adequately narrow bounds. Publish the scope and uncertainty. Neither outcome licenses a numerical “maximum possible EEG-to-fMRI accuracy.”

### Gaps

- No universal EEG-to-fMRI accuracy ceiling, sufficient dataset size or sufficient parameter count was established by the inspected sources. This search cannot prove that no related bound exists; any applicable theorem would need its target, model and measurement assumptions checked.
- The actual conditional uncertainty for the project's deployment population remains unmeasured. Residuals and internal project reports do not settle it.
- Whether realistic uncertainty sets for lead fields and haemodynamics yield useful sensor rankings is a research question. A mathematically conservative bound could be too loose to guide acquisition.
- Auxiliary-channel availability, synchronization, repeat visits and target reliability must be audited before choosing the definitive information-value experiment. This note does not promise access to an unobserved physiological variable.

## 2. Can multimodal system identification support individual regional transfer?

### Takeaway

A defensible CS contribution would be a structured estimator that separates shared predictive dynamics from subject/session measurement variation and demonstrates economical adaptation. It must preserve individual regional variation beyond a population brain-state prior; naming latent units “neural” or using a state-space model does not establish biological or causal identification.

### Cited Findings

- **EEG/fMRI state-space fusion is established prior work.** Model-driven neural/haemodynamic fusion predates current deep translation models, and a NeurIPS 2019 model jointly estimates latent dynamics and effective connectivity from simultaneous recordings. Therefore, “the first multimodal state-space model” would be indefensible. — [Valdes-Sosa et al., Model driven EEG/fMRI fusion of brain oscillations, 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC6870602/); [A state-space model for inferring effective connectivity of latent neural dynamics from simultaneous EEG/fMRI, NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/file/6aed000af86a084f9cb0264161e29dd3-Paper.pdf).
- **Modern multiview identifiability theorems are assumption-dependent.** Yao et al.'s partial-observability framework assumes smooth invertible view-specific mixing functions and regular latent densities. Noisy scalp mixtures and haemodynamic convolution do not automatically satisfy those assumptions. Using paired modalities does not inherit the theorem without a valid mapping of assumptions. — [Yao et al., ICLR 2024, Assumption 2.1 and Theorem 3.2](https://proceedings.iclr.cc/paper_files/paper/2024/file/956e5427549a82a7472e02adc88360e9-Paper-Conference.pdf).
- **Causal identification can require stronger evidence than observational prediction.** Interventional state-space models establish identifiability under an explicit intervention model and demonstrate it in neural perturbation settings. Routine resting EEG-fMRI is not such an intervention dataset; a sensory task is not automatically an intervention satisfying their latent-target assumptions. — [Nejatbakhsh and Wang, ICML 2025](https://proceedings.mlr.press/v267/nejatbakhsh25a.html).
- **Domain invariance is not a universal solution.** Formal counterexamples show that low source error plus invariant representations need not ensure good target performance under conditional shift. These classification results motivate caution; they do not provide a numerical EEG-BOLD regression bound. — [Zhao et al., ICML 2019](https://proceedings.mlr.press/v97/zhao19a.html).
- **Cross-session prediction already has relevant precedents.** Mehta et al.'s January 2026 revised preprint reports significant somatomotor prediction across sessions for at least one session in 13/15 people in task-evoked conditions, versus 7/15 at rest. These are significance counts, not prediction R² or evidence of unseen-patient regional recovery. They make session transfer and temporal-null testing required prior-art comparisons. — [Mehta et al., arXiv:2504.10752v2, Table 1](https://arxiv.org/html/2504.10752v2).

### Inferences

#### Work package 2: structured dynamics with bounded personal adaptation

**CS contribution candidate:** a compact, target-aware multimodal dynamical estimator with explicit subject/session observation operators and a constrained personal calibration procedure. The proposed advance must be the adaptation/estimation method and its supported assumptions, rather than the existence of latent dynamics, an HRF layer or multimodal learning.

One starting family is

\[
z_{t+1}=g_\theta(z_t,u_t)+w_t,
\qquad E_t=\ell_s(z_t;\text{montage/anatomy})+a_t+\eta_t,
\]

\[
Y_{r,t}=\sum_{\tau=0}^{L}h_{r,s,v}(\tau)\,\phi_r(z_{t-\tau})
+d_r^\top P_{\leq t}+\epsilon_{r,t}.
\]

Here \(s\) denotes a person, \(v\) a visit, \(P\) recorded physiology, \(a\) modeled artifact, and \(h\) a finite-dimensional haemodynamic response family. This is a modelling proposal. Compare linear/low-rank dynamics with one compact nonlinear extension. Use shared parameters where supported and regularized subject/visit effects where needed. A useful algorithmic question is whether a small calibration budget should update the observation operator, haemodynamic parameters, dynamics or merely an output scale/offset. Compare these alternatives directly.

The scientific claim concerns **predictive functions or states up to an explicitly defined equivalence**, not necessarily unique biological generators. For linear latent systems, invertible changes of coordinates can leave observations unchanged. For flexible nonlinear systems, ambiguities can be broader. Fixing a parameterization for optimization does not prove biological identification. Separate structural identification with ideal data, finite-sample parameter estimation and successful held-out prediction.

Any proposed identifiability statement should specify the dynamical family, rank/excitation conditions, measured inputs, permissible observation mappings, noise assumptions and equivalence class. Start with a restricted linear/convolutional result or counterexample. If those assumptions cannot be defended for real data, retain a predictive model and report its interpretation limits. Causal claims require an appropriate human-designed intervention and assumptions; they are optional extensions, not a requirement for thesis completion.

#### Three information regimes, reported separately

| Regime | Allowed information | Required evaluation |
|---|---|---|
| Cold start | Population training, current/past EEG, declared metadata and available physiology; no paired data from the evaluated person | New person; then a frozen new acquisition domain/site |
| Limited paired calibration | A declared budget, for example 0, 5 and 15 minutes of paired data from visit 1 | Later visit/run with disjoint outcomes and a temporal guard interval; report MRI time and calibration failures |
| Site recalibration | Explicitly counted labelled target-site participants or scans | Separate new target-site people, with calibration subjects excluded from final testing |

These budgets are illustrative. An fMRI decoder learned from unpaired scans is a population prior; personal paired calibration supplies different evidence. Measured fMRI anchors, future BOLD, or a person's entire test-run BOLD cannot quietly enter an “EEG-only” condition.

#### The regional-fidelity test must defeat plausible priors

Build the following comparator ladder with the same allowable information and training/test protocol:

1. Training-set regional mean/template and metadata-only prediction.
2. Task schedule and low-dimensional brain-state prediction, including an EEG-derived vigilance representation where allowed.
3. Physiology-only and brain-state-plus-physiology predictors; a global-pattern model with training-derived regional loadings.
4. Properly tuned lagged ridge and the compact structured baseline.
5. The proposed adaptation model and one justified contemporary neural comparator.

Keep raw regional BOLD as an outcome. Add prespecified regional contrasts, such as homologous cortical differences when scientifically justified, and deviations from a common spatial mode with loadings learned on training data. If nuisance-adjusted targets are used, specify their regression and fitting data in advance. Measured test fMRI may define the **outcome** or an explicitly labelled oracle audit; it must not become a deployment input. Residualization changes the target, can remove meaningful neural variation, and does not establish a “pure neural” component.

Use a **regional evidence panel**, rather than one aggregate reconstruction score:

- Temporal correlation together with predictive R²/MSE, amplitude slope/intercept, regional contrast error and lag error. Define the R² reference and aggregation; mean correlation squared is not calibrated R².
- Within-state, within-task-condition and trial-to-trial variation after accounting for the repeated population response. A task template can predict a mean response without predicting an individual's deviation on a particular trial.
- Matched-state wrong-person EEG, misaligned EEG and constrained temporal surrogates. Preserve relevant autocorrelation and common task/state structure; validate null assumptions rather than treating every time shuffle as valid. If matched wrong-person EEG performs equally well, the evidence for person-specific correspondence is weak.
- Correct-person versus population-only or wrong-person calibration, tested on a later visit. An identity classifier or a characteristic connectivity matrix is insufficient evidence for recovery of the actual target trajectory.
- Individual failure distributions, montage/artifact strata and, only if paired patient data exist, prespecified abnormal or asymmetric regional responses adjudicated independently by clinicians.

A shared time permutation preserves a multivariate trace's functional connectivity while destroying its temporal alignment. Thus connectivity agreement, spatial resemblance or realistic generated images can be secondary outcomes; they cannot establish recovery of that person's particular regional event. Conversely, a regional contrast can still contain vascular or artifact effects, so positive contrast prediction is a scoped fidelity result rather than proof of localized neural causation.

#### Transfer experiments and decisions

Use subject-disjoint training/tuning and test all available visits of a held-out person consistently. Distinguish same-site new people, same-person new visits, new montage, new site and new population/task. Leave-one-dataset-out combines several changes; it is a valid composite challenge but does not isolate a scanner effect. If disease exists only at one site, disease and site cannot be disentangled from that design alone.

Split before learned normalization, feature selection, harmonization and prior construction. Use causal preprocessing for an online claim, with guard intervals covering filters, feature context and relevant haemodynamic support. Compare identical timestamps. A model that uses future EEG or retrospective scan-wide cleaning needs a separate offline label. Hyperparameters and final gates must not be repeatedly selected on the purported external test.

**Falsifiable WP2 hypothesis:** constrained adaptation of subject/session observation and haemodynamic parameters improves held-out regional-contrast predictive R² and calibration efficiency over population-only models, output-only recalibration and matched ridge. For an external-transfer claim, improvements must persist in a frozen acquisition domain and be attributable to correct-person correspondence in the controls above.

**Gate G2 — retain a regional and transfer claim.** Use a prespecified target aggregate, participant-level intervals and multiplicity control for confirmatory ROI comparisons. An illustrative methodological gate is a contrast-R² improvement of at least 0.02 with its interval excluding zero, reproduced in a genuinely held-out domain; require amplitude/lag tolerances agreed for the target as well. Show that the declared personal calibration budget improves the later-visit result beyond simpler calibration. A new-subject result at one site does not pass a new-site gate.

If improvements occur only for global BOLD or state templates, narrow the claim to state-mediated prediction. If observed gains require extensive personal MRI, report a calibration-intensive estimator and its cost. If only healthy volunteers were tested, say **individual/person-specific**, not validated patient-specific recovery. Patient claims require paired intended-population outcomes and explicit abnormality-preservation tests. A negative patient-specific result is scientifically meaningful even if healthy-state prediction remains strong.

**Useful negative results:** a carefully matched ridge model equals the structured estimator; a putatively invariant representation loses meaningful target variation; personal HRF fitting does not transfer across days; apparent regional gains disappear under matched-state controls; or a simulated identifiable model remains practically unidentifiable at the available SNR. Each distinguishes a methodological explanation from an unsupported biological story.

### Gaps

- The inspected literature motivates testing regional specificity and controlled personal adaptation; it does not prove that either is an untouched research area. UniEFS already studies context and transfer, and older fusion/system-identification research is substantial. A contribution must survive a focused prior-art review and matched comparisons.
- Exact latent biological identification from these observational data has not been established here. A more accurate decoder, attention map or interpretable parameter name does not close that gap.
- Healthy paired datasets cannot establish preservation of lesion-adjacent or disease-specific BOLD abnormalities. That would require collaborators, ethically approved acquisition and an appropriate reference.
- The proposed 0.02 research margin has no established clinical significance. Regional error tolerances and the acceptable calibration burden remain human decisions.

## 3. What reliability claims survive dependence, selection and shift?

### Takeaway

Specify the prediction unit, error criterion, sampling assumptions and available labels before choosing a calibration method. The central contribution candidate is an informative selective estimator whose supported guarantees and empirical failures are explicit; an unconditional coverage number is not a patient-specific reliability certificate.

### Cited Findings

- **Ordinary conformal coverage is not automatically retained under distribution shift.** Barber et al. bound coverage loss beyond exchangeability using distributional discrepancy terms. Those terms can be unknown or large; a bound does not certify an arbitrary new clinical site. — [Barber et al., Annals of Statistics 2023](https://arxiv.org/html/2202.13415v5).
- **Weighted conformal has a particular shift model.** The covariate-shift result assumes unchanged \(P(Y\mid X)\) and a known input-density ratio. Estimated ratios introduce another estimation problem, and changed neurovascular/measurement relationships can violate the unchanged-conditional assumption. — [Tibshirani et al., NeurIPS 2019](https://arxiv.org/html/1904.06019).
- **Exact useful distribution-free coverage at every individual covariate value is unavailable without assumptions.** The conditional-inference impossibility results concern unrestricted distributions and finite samples; they do not forbid useful model-based, asymptotic or restricted-group methods. — [Barber et al., Information and Inference 2021](https://arxiv.org/html/1903.04684).
- **Restricted conditional targets can be tractable.** Gibbs, Cherian and Candès construct coverage guarantees for specified function classes, including finite-dimensional shift/group classes. This does not grant universal conditional validity or coverage on an arbitrary unseen disease/site. — [Conformal Prediction with Conditional Guarantees, primary manuscript](https://arxiv.org/html/2305.12616).
- **Repeated observations require the correct exchangeability structure.** Hierarchical conformal methods study grouped/repeated data under hierarchical sampling assumptions. Ordered time points from a physiological trace cannot simply be declared exchangeable within a subject. — [Lee, Barber and Willett, Distribution-free inference with hierarchical data](https://arxiv.org/html/2306.06342).
- **Current time-series theory still has substantive conditions.** ResCP, ICLR 2026, gives asymptotic conditional coverage under assumptions including time-invariant strongly mixing data, reservoir stability, regular conditional laws and weighting conditions. Its guarantee conditions on the reservoir state; the paper explicitly distinguishes this from conditioning on the entire observed history. Its shift variants do not establish universal finite-sample validity under arbitrary clinical shift. — [Neglia et al., ICLR 2026, Assumptions 3.1–3.5, Corollary 3.7 and following remark](https://proceedings.iclr.cc/paper_files/paper/2026/file/b0a978efeb20d33c15e31a5beee9f6df-Paper-Conference.pdf).
- **Risk control and selection need their own analysis.** Risk-controlling prediction sets use held-out calibration to control a specified population loss with high probability under stated assumptions. That criterion differs from marginal prediction coverage, per-person conditional coverage and guaranteed clinical safety. — [Bates et al., JACM 2021](https://arxiv.org/html/2101.02703v3).
- **Selecting predictions can invalidate a calibration argument.** Sale and Ramdas identify failures in online selection/calibration strategies and construct alternatives preserving the required exchangeability. Their results concern particular selection rules and assumptions, rather than validating arbitrary EEG quality gates. — [Online Selective Conformal Prediction: Errors and Solutions, March 2025 primary manuscript](https://arxiv.org/html/2503.16809v1).
- **Adaptive guarantees have an information requirement.** OnlineSCI explicitly uses observed outcomes after decisions; its August 2026 revision distinguishes cumulative selected-error control from stronger conditional-rate results requiring regularity. EEG-only deployment does not supply true BOLD outcomes for residual updates. — [Humbert et al., arXiv:2508.10336v3, 30 August 2026, feedback setting and Section 2](https://arxiv.org/html/2508.10336v3). Publication status is treated conservatively as a preprint here.

### Inferences

#### Work package 3: selective inference with a declared validity domain

**CS contribution candidate:** a selective prediction procedure that uses the measurement diagnostics from WP1 and the predictive state/quality information from WP2 to choose which regional estimates to report, then calibrates a prespecified error criterion at the participant or complete-run level. Evaluate whether that information improves the risk–coverage tradeoff over conventional ensemble variance, simple signal-quality rejection and existing conformal/selective methods. Combining established methods is not, by itself, demonstrated originality.

Define \(A(X)\in\{0,1\}\) as the decision to report an estimate. At inference it may use recorded sensor quality, observed EEG/physiology and the fitted predictive state. It cannot use the unobserved BOLD residual. Predicted residual size and disagreement between models are features to validate, not directly observed uncertainty.

First choose one primary reliability task:

- **Prediction bands:** probability that the next exchangeable person's prespecified target/run lies within a band.
- **Selective error control:** population probability of an error exceeding a target tolerance among accepted estimates, with a lower bound on useful acceptance coverage.
- **Application alerts:** event sensitivity, false alerts/hour, event delay and probability calibration against independently adjudicated wakefulness events.

These are different outcomes. Success on one does not establish another.

#### Guarantee map

| Setting | Defensible statement to target | Limitation that the thesis must retain |
|---|---|---|
| Exchangeable complete subject records, independent fitted model | Split-conformal marginal coverage for a declared subject/run-level score | Not conditional accuracy for each patient; use the actual finite calibration count. |
| Temporally dependent traces | Calibrate entire records as units, or invoke an appropriate time-series result and check its assumptions | More overlapping windows do not create more exchangeable people. Blocking alone is not a theorem. |
| Prespecified state/montage groups with enough support | Restricted-group calibration or empirical group audits, with the selected method's conditions | Sparse groups may give vacuous results; known-group validity does not cover an unseen group. |
| Pure covariate shift | Weighted conformal under unchanged conditional law, support overlap and correct weighting assumptions | No guarantee if \(P(Y\mid X)\) changes; estimated weights require qualification. |
| Unknown new-site or disease shift | Frozen external evaluation, possible local labelled recalibration, and abstention outside supported conditions | No automatic distribution-free coverage claim for arbitrary shift. |
| Selectively reported predictions | Selection-aware calibration/risk control using an independent design and a justified sampling unit | Marginal coverage before selection is insufficient for the accepted subset. |
| Sequential adaptation | Appropriate feedback-based guarantees while true outcomes become available | No BOLD residual feedback in EEG-only use; long-run average control is not instantaneous patient coverage. |

These restrictions follow from the primary mathematical sources above. They are design constraints rather than a claim that reliable uncertainty estimation is impossible.

**A simple defensible starting construction:** fit the predictor and scale/selection models on development subjects. Reserve independent calibration subjects with a fixed run duration and target panel. Assign each one a maximum standardized error over the prespecified run/regions. A conformal quantile of these subject scores yields a simultaneous band for a new exchangeable subject record, allowing arbitrary dependence within that record. The result is marginal over the record-generating population. A different run length, selection process or site distribution needs separate justification. The band may be too wide to use; that is an informative outcome.

For ordinary nonrandomized split conformal, quantile resolution is \(1/(n_{cal}+1)\). At nominal 90% coverage, fewer than nine calibration subjects makes the usual corrected quantile infinite; nine only permits the maximum finite score. This arithmetic does not imply that nine subjects are adequate for external performance assessment. Thousands of correlated windows cannot replace the missing independent calibration subjects.

For selective error control, use a bounded indicator of error exceeding a prespecified regional tolerance. A proposed construction bounds the participant-balanced accepted-loss numerator and acceptance denominator on independent subjects, simultaneously across predeclared thresholds. Their ratio bounds accepted risk if the denominator's lower bound is positive. The exact procedure needs a proof; these standard concentration ideas are not a claimed new theorem. Low acceptance can make the result useless. Unbounded squared loss needs extra assumptions; clipping changes the claim. — [Relevant bounded-loss/UCB framework and limitations](https://arxiv.org/html/2101.02703v3).

The independent units in that construction must match the guarantee: for example, independently recruited subjects from the supported population, with a fixed within-record averaging rule. Shared site effects require appropriate conditioning or a different hierarchical model. Do not certify across unseen sites by treating all people at two familiar sites as independent draws of sites.

#### Experiments and falsification

Compare a fixed, small method set: ensemble/heteroscedastic uncertainty without a coverage theorem; subject-level conformal bands; a justified group/time-series method; and the proposed selective rule. Audit nominal levels such as 80%, 90% and 95% without choosing the most favourable one after testing.

Test three distinct shift families: controlled channel/quality perturbations; real held-out sessions/sites/tasks or sleep states; and, only with paired data, intended patient populations. Simulated HRF changes can expose a failure mechanism but cannot establish the prevalence or severity of disease effects. Report coverage, width, accepted risk, acceptance rate, worst supported group results and failures on all enrolled participants. Missing inputs, rejected scans and complete abstentions belong in the denominator.

A useful **deduced impossibility example** is two target domains with identical EEG-input distribution but different \(P(Y\mid X)\). An EEG-input-only shift detector has the same distribution of observations in both domains, so it cannot distinguish them from those inputs alone. This does not say every shift is undetectable; it prevents claiming that a passed input-quality check certifies unchanged neurovascular mapping.

**Falsifiable WP3 hypothesis:** information/measurement-aware selection achieves a lower accepted error than simple quality rejection and model-disagreement baselines at matched acceptance coverage, while a justified calibration procedure meets its declared criterion in supported populations. Unsupported shifts should trigger a documented loss of certification or empirically useful abstention; merely outputting wider intervals everywhere is not sufficient utility.

**Gate G3 — retain a useful reliability claim.** Freeze the selection rule and validity assumptions before the independent test. As an illustrative research gate, target 90% coverage with a five-percentage-point maximum tolerated undercoverage on the declared audit population; require a one-sided 95% upper confidence limit on miscoverage no larger than .15, plus a prespecified width limit. For selective risk, require its upper bound below the declared risk tolerance and an acceptance lower bound above a proposed minimum such as 50%. These are methodological planning values, not clinical standards. Account for all prespecified confirmatory audits. Wide intervals, insufficient independent records or near-total abstention fail the utility/evidence gate even if a theorem remains formally true under its assumptions. A finite external audit supports performance in that sampled domain, not a guarantee under all future shifts.

Online recalibration using measured BOLD is permissible in a paired research study, with the actual acquisition/processing delay respected. Once BOLD is absent, freeze that residual-based update or arrange explicitly counted paired recalibration. Updating from a model's own synthetic outputs is not equivalent to acquiring ground truth. If an EEG-only method claims ongoing coverage, it must supply a different valid argument.

#### One initial application: research-grade wakefulness monitoring during resting MRI

**Proposed setting:** adults instructed to remain awake during a specified resting MRI protocol. The initial output is a probability/abstention trace for sustained wakefulness loss, evaluated silently before any technologist action is studied. The eventual proposed action is a technologist reviewing a possible event under a human-approved workflow. This is an application to test the computational thesis, not a promise of diagnosis, scan replacement or improved treatment.

Simultaneous recordings allow the regional BOLD research endpoints to be tested alongside the advisory. At advisory inference, explicitly declare whether scanner BOLD is excluded; the EEG-only condition must exclude it. Do not confuse prediction of a haemodynamically delayed signal with immediate detection of a vigilance event.

Compare **direct EEG vigilance prediction**, EEG-plus-physiology prediction and a model using the inferred BOLD representation, at matched causal inputs and acquisition costs. The intermediary representation earns its place only if it adds external decision-relevant value, transfer or calibrated selectivity. If direct EEG performs just as well, use it for this application; the regional-fidelity research question remains separate.

References should include blinded sleep/arousal adjudication and, when feasible, independent eyelid/pupil or behavioural measurements. EEG-derived sleep labels are legitimate references with shared-modality limitations; they are not fully independent confirmation of EEG-based alert validity. Define events and ambiguous labels before testing. Report event sensitivity, false alerts/hour, delay from independently adjudicated onset, probability calibration, accepted monitoring time and total missing/abstained time. Raw computation time and context length do not measure end-to-end event delay.

**Application gate:** the sleep/clinical team must first set a concrete maximum false-alert rate \(F_*\), minimum sensitivity \(S_*\), maximum acceptable delay \(D_*\), and minimum monitored coverage \(C_*\), with confidence requirements. Freeze these before confirmation. Advance from retrospective replay to silent prospective acquisition only after a genuinely held-out evaluation supports all four and the causal pipeline is validated. Advance to an action study only through the human-led protocol. If references are inadequate or estimates are imprecise, remain a research study. If inferred BOLD fails to improve the direct-EEG comparator at matched alert burden, drop that extra application component rather than claiming clinical value from reconstruction correlation.

The existence of global EEG–BOLD–autonomic coupling motivates this application but does not validate its alerts. — [Physiological motivation](https://pubmed.ncbi.nlm.nih.gov/40335772/).

#### Compact contribution matrix

| Package | Candidate CS contribution | Existing work that constrains novelty | Decisive evidence / failure condition | Broader CS relevance |
|---|---|---|---|---|
| WP1: information | Target-aware measurement/history diagnostic under uncertain observation and haemodynamic operators, with cost-matched selection | Functional observability and sensor design already exist; no claim to invent the rank condition | Predicted measurement ranking improves held-out regional targets; fails if cost-matched alternatives equal/beat it with sufficient precision | Learning from partial observations; measurement design under model uncertainty |
| WP2: identification and transfer | Structured shared dynamics plus constrained subject/visit adaptation, evaluated on individual regional deviations | EEG-fMRI fusion, context-aware synthesis and session-transfer studies already exist | Frozen subject/session/domain gains beyond priors and ridge; correct-person controls matter; fails if gains reduce to state templates or do not transfer | Multimodal system identification, representation sufficiency and economical adaptation |
| WP3: reliability | Measurement-aware selective estimation with a proved, scoped calibration/risk statement and explicit unsupported conditions | Conformal, risk control, selection-aware and time-series methods already exist | Better risk–coverage utility and valid declared audit; fails if useful coverage disappears, errors remain under shift, or assumptions do not hold | Selective prediction with dependent observations and limited outcome feedback |

**Novelty status for all three rows: candidate, not proven.** A gap in what the inspected papers establish is not proof that no one has studied it. The advisor and candidate must compare exact assumptions, objectives, algorithms and guarantees against prior functional observers, multimodal identification, adaptation and selective inference. A genuine contribution may be a restricted new result plus an effective estimator, or a methodological benchmark/counterexample that changes a supported conclusion. “First to combine EEG and conformal” is not a defensible claim from this search. Routine application of known tools may be useful without constituting enough CS originality for a PhD.

#### Illustrative three-year plan, not a binding programme

| Period | Core work and reviewable outcomes | Decision and dependency |
|---|---|---|
| Year 1, months 1–12 | Refine target and prior-art map; audit cohorts, clocks, splits and causal preprocessing; reproduce ridge and one compact comparator; construct known-state counterexamples; develop WP1 measurement diagnostic and crossed learning curves. Seek collaborators/data permissions early. | G0: trustworthy paired targets and feasible independent evaluation. G1: choose measurements/model scope from supported gains. Deliver an information/measurement paper or a rigorous limitation study; do not infer a universal ceiling. |
| Year 2, months 13–24 | Develop WP2 estimator and constrained calibration; compare parameter-update choices; test regional contrasts, matched-state/wrong-person controls and subject/session/domain transfer. Run a modest repeat-visit pilot only if approved and funded. Start WP3 on frozen development models. | G2 determines whether the thesis supports regional individual inference, a calibration-intensive method, or only state-mediated prediction. If repeat visits/patients are unavailable, narrow claims and use simulations only for the corresponding identification mechanisms. |
| Year 3, months 25–36 | Complete selection-aware calibration analysis; freeze thresholds; conduct independent external audits and, if feasible, the silent monitoring pilot. Integrate positive and negative findings, release permitted benchmark material and write the thesis. | G3 and the application gate determine supported reliability and application claims. A clinical trial, regulatory clearance and a large multisite patient acquisition are not graduation dependencies. Scope/publication decisions remain with the human supervisory team. |

The packages can overlap, and an early negative regional result should change allocation: deepen measurement/identification analysis and uncertainty limits rather than automatically expanding an image generator. Actual milestones depend on data rights, recruitment, independent validation and supervisory judgment.

#### Achievable resource tiers

The following are alternative development envelopes, not sample-size calculations or promises of clinical validation. Compute needs must be profiled on one representative fit; paired hours do not determine participant or event diversity.

| Tier | Feasible study scope | Illustrative resources and outputs | Claims that remain unsupported |
|---|---|---|---|
| A: public-data thesis core | Existing paired cohorts, nested montages, known-state simulations, controlled cross-dataset tests and subject-level uncertainty | A workstation/CPU resources for QC and ridge; shared access to one GPU for compact models; a student with active methods supervision and specialist consultation. Audit storage and preprocessing before duplicating derivatives. Potentially sufficient for a methodological thesis if the contributions are substantive. | Prospective utility, unseen-disease fidelity, real repeat-day calibration without repeat data, or universal site coverage |
| B: collaboration pilot | Approximately 30–60 newly recruited people at two acquisition sites, two 30-minute paired visits each, plus independent public/development holdouts where appropriate | 30–60 acquired paired hours before QC; at a purely illustrative 75% retention, 22.5–45 usable hours. Add synchronized available physiology, repeat-visit staffing, reference adjudication and a small independent confirmation allocation. Supports calibration/measurement feasibility. | A deployment-ready device or a precise population-wide clinical safety claim; two sites poorly characterize the distribution of future sites |
| C: externally funded extension | Approximately 150–300 intended-use participants across 3–5 sites, with genuinely held-out people/sites/time periods and an explicitly sized event-validation cohort | Dedicated acquisition/QC coordination, MR/EEG expertise, clinical adjudication and statistical support. Modest model compute can remain adequate; no verified parameter-to-participant scaling law prescribes a giant model. | Whole-brain diagnostic substitution; sufficiency must follow actual event counts, effect sizes, clustered uncertainty and clinical thresholds |

Concrete public starting points are NeuroBOLT's VU cohort, the sleep/rest release ds003768, and the 28-participant gradCPT/rest dataset ds006040. The latter is a **single-session** study and cannot by itself establish repeat-day adaptation. Sleep annotations and behavioural tasks offer complementary references, not automatically interchangeable intended-use cohorts. Do not sum their participants or nominal hours without deduplication, synchronization and QC. — [NeuroBOLT](https://arxiv.org/html/2410.05341v2); [Gu et al., Data in Brief 2023, dataset descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583/); [Cha et al., Scientific Data 2026, participants and data availability](https://www.nature.com/articles/s41597-026-06616-6.pdf).

For a small programme, prioritize independent people and informative repeat visits over thousands of correlated windows. Clinical event prevalence and dependence determine how many reference-positive events/people are needed; training N and validation precision are separate budgets. Reserve enough participants for independent calibration and final testing, or explicitly remain exploratory. No scanner price, GPU-hour total, clinical sample-size minimum or post-QC usable-hour inventory was established here.

#### Human ownership

| Owner | Decisions and responsibilities |
|---|---|
| Human PhD advisor/supervisory committee and candidate | Select the CS problem and acceptable thesis scope; assess novelty and theorem assumptions; set methodological depth; challenge identifiability claims; preregister confirmatory claims; decide publications, pivots and the final thesis argument. The advisor cannot delegate academic originality judgment to this literature note. |
| Clinical/sleep collaborators, technologists and patient representatives | Define the initial monitoring action, population, event references, acceptable alert burden/delay and consequences of abstention. Own clinical interpretation and any patient-specific abnormality target. Vigilance does not imply motion or scan usability. |
| MR physicist, EEG acquisition/preprocessing specialists and research staff | Validate synchronization, montage/physiology availability, acquisition procedures, prospective causal cleaning and whether preprocessing artifacts could explain predictive gains. Own feasibility of repeat visits and physiological manipulations. |
| Biostatistician/methods collaborator | Design independent calibration and external tests; size participant/site/event denominators; handle temporal and site clustering, multiplicity, equivalence and acceptance-selection analysis. Confirm that an empirical audit matches the mathematical guarantee. |
| Human investigators and institutions | Obtain data permissions, consent/ethics approval, clinical partnerships, funding, governance and any prospective workflow approval. New CO2/CVR manipulations or patient acquisitions require a human-designed protocol. |

The student's computational ownership can include the measurement diagnostic, restricted theory/counterexamples, estimation/adaptation method, calibration analysis and reproducible evaluation. The clinical partners determine physiological and clinical validity; they do not need to promise that synthesis will replace a scan.

#### Valuable negative outcomes and a defensible thesis endpoint

- **Information result:** the tested montage/history fails for a defined regional contrast, with a model-based ambiguity example and empirical bounds; distinguish this from a universal impossibility claim.
- **Estimation result:** ridge or a small dynamical model matches a larger model under fair inputs and transfer. This can redirect computation and reveal which claimed gains depended on protocol choices.
- **Identification result:** multiple latent explanations fit equally well, but only a smaller family of predictive functions is stable. This motivates a restricted representation or a required extra measurement.
- **Transfer result:** personal calibration helps only within a visit, or a site shift destroys regional gains; quantify the calibration cost or supported deployment restriction.
- **Reliability result:** the requested risk is achievable only with very wide bands or little acceptance; a no-go map is useful when it is precise and compared with existing methods.
- **Application result:** inferred BOLD adds no decision value over direct EEG vigilance prediction. This rejects that intermediary for the advisory without settling all regional scientific targets.

A coherent successful thesis would explain **what is supported by the observations, how a new or materially improved estimator uses it, and how reliability degrades when the support changes**. Its strongest conclusion might be a useful restricted estimator and a sharp boundary around unsupported claims. Whether the final combination meets a computer science PhD standard depends on the actual originality, rigor and supervisory assessment, not on a promised number of positive papers.

### Gaps

- **Novelty is not proven.** This was a targeted, current primary-source review, not an exhaustive systematic review or a proof of absence. Detailed comparisons with functional sensor design, EEG-fMRI fusion/DCM, subject adaptation and selective inference remain necessary before claiming a new contribution.
- **Clinical gates are not yet numerical approvals.** The application thresholds \(F_*,S_*,D_*,C_*\), regional tolerances and prospective reference protocol must be specified by the human team before a confirmatory application study. Methodological planning margins above cannot substitute for them.
- **External data and labels are not guaranteed.** Public nominal cohorts do not establish usable synchronized hours, target physiology, repeat visits, patient pathology, permissions or sufficiently many independent calibration/test subjects. Reused/inspected datasets cannot become untouched tests by renaming them.
- **Some full texts were inaccessible in this session.** Numerical details from inaccessible 2026 translation papers were not expanded beyond the earlier feasibility report; official records and accessible abstracts support only the narrower statements made here. The main mathematical constraints were checked in accessible primary manuscripts/full texts. Relevant preprints are distinguished from verified proceedings papers, and the August 2026 OnlineSCI version is within the evidence cutoff.
- **No evidence here establishes clinical replacement, a universal ceiling or shift-proof coverage.** A future guarantee must state its target distribution, information regime, dependence structure, selection procedure and assumptions. A future patient-fidelity claim needs the patient's paired regional reference, not only plausible generated anatomy or a successful brain-state label.
