# Information and physiological limits of clinically accurate EEG-to-fMRI reconstruction

Research cutoff: **21 October 2026, Australia/Sydney (AEDT)**. Prepared for the report writer. This is a targeted primary-source evidence review, not a systematic review or a new experiment. Fifteen batched web-search/retrieval calls were used. No cluster experiments, existing-report edits, commits, or pushes were performed.

Evidence labels: **A** = mathematical result under stated assumptions, direct simultaneous recording, or physiological manipulation; **B** = primary empirical evidence with material population/design restrictions; **C** = indirect evidence or methodological analogy; **U** = relevant quantity not established. These labels grade support for the particular claim, not the overall quality of a paper. “Irreducible” always means **relative to specified inputs, target, history, and deployment population**, not unchangeable under every possible measurement system. Proposed experiments and mathematical deductions below are explicitly labeled as such.

Access: publisher pages, PubMed, primary papers in PMC, an author-hosted paper, and official conference proceedings were checked. Some PMC fetches returned CAPTCHA pages; indexed primary-paper text remained accessible in search. Europe PMC full-text XML was additionally obtained for Seeber, Murta's phase–amplitude study, and Lage-Castellanos. Other access limitations are identified below. Never silently fill an unverified cohort or split field from a review or previous AI summary.

## 1. Which blockers are irreducible, potentially reducible, or still unknown?

### Takeaway

There are sound reasons why additional parameters cannot recover arbitrary personal BOLD from a fixed scalp EEG recording. However, neither the anatomical inverse problem nor current prediction scores establish a universal numerical EEG-to-BOLD ceiling: the key question is whether the **specific BOLD target** varies among physiological states that the available EEG cannot distinguish.

### Cited Findings

| Blocker | Classification | Evidence and what is actually established | What parameters/data could change; what remains unmeasured |
|---|---|---|---|
| Source mixing and cancellation | **Irreducible for target-relevant differences in the fixed measurement's null space; practical magnitude U** | **A/B:** realistic cortical forward simulations demonstrate cancellation, including opposing cortical surfaces. This is a forward-model result, not a measured reconstruction ceiling. [Ahlfors et al., 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2797557/) | Priors can choose among compatible sources; they cannot verify which compatible event occurred. More sensors, anatomy, or complementary measurements change the problem. |
| Deep/small/incoherent generators | **Potentially reducible sensitivity loss; unrestricted recovery U** | **B:** selected deep alpha activity was recovered with high-density EEG, whereas simultaneous scalp/SEEG recording also documents scalp-missed seizures. [Seeber et al., 2019](https://www.nature.com/articles/s41467-019-08725-w); [Casale et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8290181/) | Better coverage and SNR can help. Neither categorical deep-source blindness nor complete deep-source observability is justified. |
| Montage, coverage, reference, electrode positions/head model | **Potentially reducible; residual ambiguity remains** | **B plus linear-algebra inference:** lead fields depend on sensor and anatomical geometry. [Ahlfors et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2797557/) | Better acquisition/anatomy helps; rereferencing existing channels adds no independent observations. Exact benefits for each BOLD ROI are U. |
| Discarded phase, broadband activity, long history | **Potentially reducible representation loss** | **B:** phase and phase–amplitude features can relate to hemodynamic responses beyond simple band power. [Scheeringa et al., 2011](https://pubmed.ncbi.nlm.nih.gov/21389236/); [Murta et al., 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5312786/) | Richer features can recover information already recorded, not unrecorded sources. Incremental generalization in resting scalp EEG is U. |
| High-frequency EMG and scanner contamination | **Potentially reducible measurement problem; attainable clean sensitivity U** | **B:** muscle paralysis changes high-frequency scalp power; simultaneous MRI adds gradient/pulse artifacts. [Whitham et al., 2007](https://pubmed.ncbi.nlm.nih.gov/17574912/); [multiband acquisition study, 2021](https://doi.org/10.1371/journal.pone.0238485) | Better hardware, synchronization, EMG/reference sensors and correction can help. A larger model can also exploit contamination. |
| EEG synchronization versus metabolic demand | **Possible residual ambiguity at fixed EEG; regional magnitude U** | **B/model:** human visual-cortex ECoG and BOLD can weight broadband activity and narrowband synchrony differently. [Hermes et al., 2017](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2001461) | Better source features may help; large EEG amplitude is not a universal measure of local metabolic demand. |
| CO2, respiration, cardiovascular and autonomic variation | **Irreducible if target-relevant variation remains unobserved given EEG; potentially reducible with sensing** | **A/B:** end-tidal CO2 and breathing/cardiac measures relate to fMRI; multimodal arousal coupling is not exhausted by CO2. [Wise et al., 2004](https://pubmed.ncbi.nlm.nih.gov/15050588/); [Bolt et al., 2025](https://www.nature.com/articles/s41593-025-01945-y) | Add capnography, respiration, ECG/PPG, blood pressure and pupil/behavior measurements. Their conditional contribution beyond EEG is U. |
| Person/region/state-specific HRF and baseline vascular properties | **Potentially reducible with calibration; latent changes remain U** | **B:** human HRFs vary; pharmacological manipulation alters flow–metabolism relationships. [Handwerker et al., 2004](https://pubmed.ncbi.nlm.nih.gov/15050587/); [Perthen et al., 2008](https://pubmed.ncbi.nlm.nih.gov/18191583/) | Individual HRF/CVR/ASL calibration and state/drug covariates may help. Population training cannot identify every new person's unmeasured vascular state. |
| Pathological neurovascular uncoupling | **Potentially reducible through disease measurements; clinical identifiability U** | **B:** glioma studies show impaired vascular response and compromised BOLD detectability. [Pillai and Zacà, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3235658/); [Agarwal et al., 2016](https://doi.org/10.1002/jmri.25012) | Disease-specific validation and vascular assessment are needed. Reproducing a healthy prior can conceal clinically important deviations. |
| BOLD target acquisition noise | **Irreducible for an independent noise realization; reducible by better acquisition/averaging** | **A/methods:** prediction must be interpreted against a target-specific test-data noise ceiling. [Lage-Castellanos et al., 2019](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006397) | Independent noise cannot be predicted. Estimating its size requires a justified measurement model; no project-specific ceiling has been supplied. |
| Limited training people/sites, optimization, leakage, distribution shift | **Potentially reducible; current share of error U** | **B:** published evaluation designs differ substantially in overlap and output. [NeuroBOLT, NeurIPS 2024](https://papers.neurips.cc/paper_files/paper/2024/file/29c294ddc628c94cd2c636383ef106c1-Paper-Conference.pdf) | More independent people and sites, rigorous splits, and better modeling can improve generalization. A short learning curve does not identify the Bayes error. |
| Generative plausibility versus personal correctness | **Plausibility does not resolve missing observations** | **A/C:** perception and distortion are different objectives in inverse problems; applicability to BOLD is an explicit analogy. [Blau and Michaeli, CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html) | A conditional generator can express uncertainty, but cannot verify the unobserved residual by drawing a plausible sample. |

### Inferences

- **Central distinction:** failure to identify every neural source does not prove failure to predict every function of those sources. A global arousal component could be predictable even when local sources are ambiguous. Conversely, a target-sensitive source or vascular difference invisible to the input defeats exact reconstruction for that target.
- Define the intended endpoint before using “clinically accurate”: a global arousal trace, regional continuous time courses, dynamic connectivity, static connectivity, task activation maps, or presurgical localization impose different information requirements. Good performance on one does not establish the others.
- Some missing information is fundamentally absent from a specified recording; some is merely weak, corrupted, or discarded by preprocessing. The practical division cannot be read off model parameter count.

### Gaps

- No reviewed study estimates a universal ceiling for arbitrary human regional BOLD from scalp EEG across clinical diseases, states, and sites.
- The conditional contributions of EEG sensor density, phase, high frequencies, physiology, individual HRFs, and pathology have not been jointly established for the supplied project evaluations.
- No verified clinical acceptance threshold is provided for the project's intended endpoint; prediction correlation alone cannot supply one.

## 2. How do the EEG inverse problem, montage, phase/power, and high frequencies constrain prediction?

### Takeaway

Scalp EEG is a spatially mixed measurement of population currents, not a voxelwise record of all neural energy use. Improved EEG can reveal additional information, but source priors, finer output grids, and larger networks do not themselves add measurements.

### Cited Findings

- **Ahlfors et al., “Cancellation of EEG and MEG signals generated by extended and distributed sources” (Human Brain Mapping, 2010; peer reviewed).** Realistic forward simulations based on one volunteer's anatomy show substantial cancellation for distributed dipoles and patches extending over opposing cortical surfaces. This supports a physical mechanism, not a human EEG-to-fMRI accuracy estimate. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC2797557/)
- **Seeber et al., “Subcortical electrophysiological activity is detectable with high-density EEG source imaging” (Nature Communications, 2019; peer reviewed, full text checked).** Four implanted patients: two with Tourette syndrome and thalamic electrodes, two with OCD and nucleus-accumbens electrodes. Simultaneous 256-channel scalp EEG and externalized DBS recordings during five-minute eyes-closed rest, outside MRI. One participant lacked a usable intracranial alpha peak and was excluded from further analysis. The result concerns selected alpha-envelope/source correspondence in the remaining three, not BOLD reconstruction. No unseen-site predictive evaluation was established. [Primary paper](https://www.nature.com/articles/s41467-019-08725-w)
- **Casale et al., “The Sensitivity of Scalp EEG at Detecting Seizures—A Simultaneous Scalp and Stereo EEG Study” (Journal of Clinical Neurophysiology, 2022; peer reviewed).** Twenty-seven patients undergoing simultaneous scalp/SEEG monitoring; 172 seizures, of which 100 appeared on scalp. This was clinical epilepsy monitoring, not an fMRI experiment or a random population sample. Seizures within patients are not 172 independent people. Medication was reduced or discontinued during monitoring. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8290181/)
- **Whitham et al., “Scalp electrical recording during paralysis: quantitative evidence that EEG frequencies above 20 Hz are contaminated by EMG” (Clinical Neurophysiology, 2007; peer reviewed, abstract checked).** Two people were recorded with and without neuromuscular blockade. Strong EMG contamination is directly demonstrated in that small design; the paper does not establish that every scalp signal above 20 Hz is non-neural or give an EEG-to-BOLD ceiling. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/17574912/)
- **Scheeringa et al., “Modulation of visually evoked cortical fMRI responses by phase of ongoing occipital alpha oscillations” (Journal of Neuroscience, 2011; peer reviewed).** Simultaneous human EEG-fMRI visual stimulation: alpha phase at stimulus onset related to evoked V1/V2 response. The methods describe 18 recruited participants; a final retained sample was not independently verified here. This concerns event-related amplitude modulation, not arbitrary resting BOLD. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/21389236/); [author-hosted paper](https://centaur.reading.ac.uk/31449/1/Bojak%20Modulation%20of%20visually%20evoked%20cortical%20responses%20by%20phase%20of%20ongoing%20occipital.pdf)
- **Hermes, Nguyen and Winawer, “Neuronal synchrony and the relation between the blood-oxygen-level dependent response and the local field potential” (PLOS Biology, 2017; peer reviewed, full text checked).** ECoG from two implanted Stanford patients and fMRI from four different healthy NYU participants, using related visual stimuli: broadband and alpha changes tracked BOLD differently from narrowband gamma. This is a population-response model and cross-modality stimulus comparison, not simultaneous personal EEG-to-BOLD recovery; the two acquisition institutions are not a held-out-site reconstruction test. [Primary paper](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2001461)

### Inferences

- **Forward-model deduction:** write the recorded potentials as `X = L J + e`, where `J` represents source currents, `L` the lead field/montage, and `e` measurement contamination. If `L deltaJ = 0`, then `J` and `J + deltaJ` yield identical ideal recordings. If their BOLD targets differ, an EEG-only deterministic model cannot be correct for both. This is a conditional counterexample, not a claim that every null-space perturbation occurs physiologically or affects the target.
- **Near-null directions matter too:** a source contribution can be nonzero but too small relative to sensor and physiological noise for reliable recovery. More data may help estimate stable statistical relationships; it does not make a single noisy observation arbitrarily informative.
- **Cancellation versus metabolism:** electrical fields add with signs and orientations. Local energy use need not cancel when opposing electrical fields do. A small scalp voltage therefore does not establish little regional neural activity. The magnitude of this mismatch for a particular ROI requires measurement.
- **Reference nuance:** voltages are measured as differences. A full-rank change among equivalent independent voltage differences changes coordinates, not information; common-average referencing makes a rank constraint explicit. Losing channels or retaining an impoverished bipolar montage can remove useful spatial contrasts. An imagined “absolute potential” is not an extra physiological observable recovered by a reference convention.
- **Source imaging:** individual MRI, skull/conductivity models, electrode digitization, inferior coverage, denser sensors, and good contact can improve the effective measurement. Priors may make a constrained inverse problem identifiable on a restricted source family. Neither numerical regularization nor fMRI-informed priors establish unique recovery without those assumptions.
- **Deep regions:** a predicted thalamic trace could reflect direct weak sensitivity, cortical consequences of thalamic activity, or shared arousal. Distinguish these experimentally; temporal correlation with a deep ROI does not itself localize the EEG generator.
- **Power versus phase:** band powers discard within-band phase and some cross-frequency/spatial interactions. Phase can matter through stimulus timing or phase–amplitude coupling. Conversely, second-scale hemodynamics often track slow envelopes; the existence of a phase effect does not prove raw millisecond phase is essential for resting reconstruction.
- **High frequencies:** broadband neural activity and narrowband gamma oscillations are different features. Do not equate intracranial high-frequency results with clean scalp gamma. Increasing the analyzed frequency range can add EMG, line, amplifier, and scanner residuals as well as neural information. Avoid the unsupported slogan that the skull imposes a universal temporal low-pass cutoff; cancellation, SNR, sensor bandwidth, and artifacts need separate assessment.
- **History/dynamics:** instantaneous nonuniqueness does not prove nonobservability from arbitrarily long histories. Dynamic assumptions and delayed cortical effects can reveal hidden state. A clinically causal model must be evaluated with the history actually available at prediction time; future EEG and offline whole-run processing are additional information.

### Gaps

- No validated per-region estimate here specifies the proportion of BOLD-relevant neural variation lost to cancellation, depth, weak synchrony, limited coverage, or power-only features.
- No universal channel-count, frequency-band, or source-resolution threshold guarantees clinical BOLD fidelity. The studies above do not establish one.
- **Unverified quantity:** the Scheeringa study's final retained sample, distinct from its 18 recruited participants, was not audited; do not present recruitment N as the analyzed N.

## 3. Which neural, metabolic, vascular, and body processes can scalp EEG miss?

### Takeaway

BOLD is a hemodynamic observation influenced by neural activity, blood flow/volume, oxygen use, vascular state, and systemic physiology. EEG can track shared arousal and some neural drivers, but it does not directly measure all these variables; their unexplained conditional variation is the relevant potential ceiling.

### Cited Findings

- **Logothetis et al., “Neurophysiological investigation of the basis of the fMRI signal” (Nature, 2001; peer reviewed).** Simultaneous intracortical electrophysiology/fMRI in anesthetized macaque visual cortex favored LFP over spiking as a BOLD correlate and found animal/site-specific impulse responses. This supports input/local-processing sensitivity in this preparation, not a universal neural fraction. Full cohort details and design limitations are in section 5. [Publisher/primary abstract](https://www.nature.com/articles/35084005)
- **Wise et al., “Resting fluctuations in arterial carbon dioxide induce significant low frequency variations in BOLD signal” (NeuroImage, 2004; peer reviewed, abstract checked).** Nine volunteers for resting end-tidal CO2/fMRI; a separate four-volunteer transcranial-Doppler cohort corroborated a blood-flow mechanism. Regional differences were present. These are not 13 paired EEG-fMRI participants; no EEG-based prediction was evaluated. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/15050588/)
- **Birn et al., “Separating respiratory-variation-related fluctuations from neuronal-activity-related fluctuations in fMRI” (NeuroImage, 2006; peer reviewed).** Ten healthy volunteers in a 3 T fMRI/physiology study. Slow respiratory variation overlapped regions used in resting-network analysis. Breathing motion and slower across-breath hemodynamic effects should be distinguished. Not an EEG reconstruction test. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/16632379/); [publisher methods extract](https://www.sciencedirect.com/science/article/pii/S1053811906001248)
- **Shmueli et al., “Low-frequency fluctuations in the cardiac rate as a source of variance in the resting-state fMRI BOLD signal” (NeuroImage, 2007; peer reviewed, abstract checked).** Concurrent cardiac/respiratory monitoring and resting fMRI identified time-lagged cardiac-rate relationships beyond established physiological regressors. Sample size was not verified from the accessible abstract; no EEG model or held-out-person/site reconstruction is established by this source. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/17869543/)
- **Handwerker, Ollinger and D'Esposito, “Variation of BOLD hemodynamic responses across subjects and brain regions and their effects on statistical analyses” (NeuroImage, 2004; peer reviewed, primary abstract checked).** Demonstrates variation relevant to HRF modeling. This review does not quote a numerical HRF range or a cohort count from secondary descriptions. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/15050587/)
- **Perthen et al., “Caffeine-induced uncoupling of cerebral blood flow and oxygen metabolism: a calibrated BOLD fMRI study” (NeuroImage, 2008; peer reviewed).** Ten healthy regular caffeine consumers, before/after 200 mg caffeine; eight additionally underwent a baseline-stability study. BOLD/ASL/hypercapnia calibration interrogated vascular–metabolic relationships. CMRO2 was model-estimated, not directly measured, and there was no simultaneous EEG proof of identical neural activity. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC2716699/); [author-hosted full paper](https://fmriusers.ucsd.edu/tliu/pdf/perthen08-caffeine.pdf)
- **Pillai and Zacà, “Clinical utility of cerebrovascular reactivity mapping in patients with low grade gliomas” (World Journal of Clinical Oncology, 2011; peer reviewed, pilot).** Seven patients; breath-hold CVR and perfusion imaging showed abnormal vascular responsiveness relative to homologous contralateral tissue. This supports vascular assessment, not an established correction that restores true neural activity. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3235658/)
- **Agarwal et al., “Neurovascular uncoupling in resting state fMRI demonstrated in patients with primary brain gliomas” (Journal of Magnetic Resonance Imaging, 2016; peer reviewed).** Seven patients showed reduced ipsilesional resting BOLD network detectability, using ICA/seed analyses. This is within-patient map comparison, not a seven-person EEG reconstruction trial or unseen-site clinical validation. [Primary publisher article](https://doi.org/10.1002/jmri.25012)
- **Bolt et al., “Autonomic physiological coupling of the global fMRI signal” (Nature Neuroscience, online 7 May 2025; peer reviewed).** Independent datasets connect global fMRI with EEG and cardiovascular, pulmonary, exocrine and smooth-muscle measures. Resting cofluctuations also occur with breathing cues, sensory events and sleep events. Persistence of spatial structure under end-tidal CO2 clamping argues against an exclusively respiratory-CO2 account, not against all vascular involvement. [Primary article](https://www.nature.com/articles/s41593-025-01945-y); [verified PubMed record](https://pubmed.ncbi.nlm.nih.gov/40335772/)
- **Title/version correction:** “Widespread brain–body integration during changes of arousal” is a separate Nature Neuroscience **Research Briefing**, not the Bolt research article's title. The earlier Bolt **preprint** is “Widespread Autonomic Physiological Coupling Across the Brain-Body Axis.” Its accessible methods specify 11 people/15 ME-REST scans and 6 people/9 ME-TASK scans; do not transfer these counts to the final paper's complete sample or add them into a unique-person total without verifying overlap and final supplementary tables. [Briefing](https://www.nature.com/articles/s41593-025-01946-x); [preprint methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11312447/)
- **Raut et al., “Arousal as a universal embedding for spatiotemporal brain dynamics” (Nature, online 24 September 2025; peer reviewed, full text checked).** Seven head-fixed mice with simultaneous pupil/face video and optical calcium, hemoglobin and flavoprotein measures; principal prediction analyses trained on six mice and tested the seventh. Additional Allen data included 16 mice, with individual decoder refitting for the shared-manifold analysis. This is animal optical/electrophysiological evidence, not human whole-brain EEG-to-BOLD validation. [Primary paper](https://www.nature.com/articles/s41586-025-09544-4)
- **Uhlirova et al., “Cell type specificity of neurovascular coupling in cerebral cortex” (eLife, 2016; peer reviewed).** Optogenetic/vascular mouse experiments support neuron-type-specific vasoactive mechanisms. The study's total was 103 mice across experiments, not 103 paired human fMRI scans. This gives mechanistic evidence that one scalar electrical-activity proxy need not specify vascular response. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4933561/)

### Inferences

- A useful causal sketch is `neural state -> electrical currents -> scalp EEG`, together with `neural/cell-type state + metabolism + vascular state + systemic physiology -> hemodynamics -> measured fMRI`. Arousal influences both branches. This is a conceptual synthesis, not a uniquely identified causal graph from the cited observational correlations.
- EEG can capture cortical rhythms, evoked responses, sleep/arousal patterns, and correlated consequences of deeper processes. It does not directly measure arterial CO2, blood oxygenation, blood pressure, vascular reserve, regional perfusion, oxygen extraction, hematocrit, or vessel-specific response properties. Predictability of those variables from EEG must be tested, not presumed absent or complete.
- Respiration/CO2 and autonomic activity are not cleanly separable into “artifact” versus “brain.” Neural arousal can drive body physiology, which itself changes the fMRI signal; body signals can also affect the brain. Removing all shared variation can remove neural information; retaining it can inflate claims about local neural reconstruction.
- Medication, caffeine, anesthesia, disease, sleep state, and vascular anatomy can change both EEG and the mapping to BOLD. Record these variables and validate the conditional mapping. The caffeine study is an existence proof of vascular–metabolic sensitivity, not evidence that every medication causes the same effect.
- Multimodal monitoring can reduce ambiguity, but peripheral physiology does not provide a voxelwise metabolic/vascular measurement. ECG/PPG is not equivalent to capnography or blood pressure; fNIRS adds superficial hemodynamic information with coverage and extracerebral limitations; individual ASL/CVR and anatomy may require an MRI calibration session. These are proposed measurement strategies, not demonstrated complete solutions.
- **Can better EEG alone solve it?** For a restricted global or task endpoint, it might meet a useful threshold; that remains empirical. For unrestricted personal regional hemodynamics, better EEG alone supplies no general guarantee. If two EEG-indistinguishable vascular/body states produce different BOLD, some additional information or a restricted claim is necessary. No reviewed study establishes the minimal sufficient sensor set.

### Gaps

- The final Bolt paper's complete retained participant counts, overlap across conditions, and acquisition-site total were not verified because full final methods/supplementary tables were not accessible in this pass. “Several independent samples” must not become an invented aggregate N or site count. It was a physiological coupling study, not a clinical reconstruction trial.
- A July 2026 peer-reviewed paper, “Physiological arousal as a predominant source of individual differences in functional brain networks,” was located. Its accessible publisher material did not allow a cohort/split audit; no numerical effect is imported. It does not establish EEG reconstruction accuracy. [Publisher record](https://www.nature.com/articles/s42003-026-10624-y)
- It remains unknown how much residual regional error is caused by unobserved neural activity, unobserved vascular state, or measurement contamination in the supplied project data.
- **Unverified quantities:** Shmueli's participant count and Handwerker's original cohort count were not established from the inspected primary material. No numerical effect, cohort total, or regional ceiling is inferred for either from secondary descriptions.

## 4. What do conditional expectation, irreducible variance, correlation, and noise ceilings mean?

### Takeaway

The best average answer obtainable from a specified EEG input is not necessarily the BOLD trace that actually occurred. Measurement repeatability and EEG observability are different ceilings, and neither a Pearson correlation nor its square measures the fraction of neural activity recovered.

### Cited Findings

- **Schoppe et al., “Measuring the Performance of Neural Models” (Frontiers in Computational Neuroscience, 2016; peer-reviewed methods).** Separates predictable response variation from trial-to-trial variability and develops normalized correlation measures. Its setting is sensory-neuron response modeling, so adaptation to ongoing human EEG-fMRI requires explicit assumptions. [Primary article](https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2016.00010/full)
- **Lage-Castellanos et al., “Methods for computing the maximum performance of computational models of fMRI responses” (PLOS Computational Biology, 2019; peer-reviewed methods, full text checked).** Distinguishes a test-data noise ceiling, compares analytical, Monte Carlo and split-half approaches, and tests noise-structure assumptions. It does not supply a numerical ceiling for spontaneous scalp EEG-to-fMRI reconstruction. [Primary article](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006397)

### Inferences

**Mathematical deductions below are supplied for interpretation, not reported empirical estimates.** They assume finite second moments and a fixed joint distribution of input and target. Let `X` include exactly what the deployed predictor receives: channels, preprocessing, EEG history, person/calibration information if available, and any allowed covariates. Let `Y` be one specified BOLD target/time point.

**Conditional expectation in ordinary language.** `m(X) = E[Y | X]` means: among all occasions compatible with this observed input, what is the average BOLD value? If several different regional or vascular states are compatible with the same EEG, this average need not be any occasion's actual value.

For squared-error prediction:

```text
E[(Y - f(X))^2]
  = E[Var(Y | X)] + E[(m(X) - f(X))^2].
```

- `E[Var(Y | X)]`: the average remaining spread among BOLD outcomes compatible with the input. This is irreducible **for that input and distribution**. It includes unobserved biology and measurement noise, not only intrinsic randomness.
- The second term: the model's failure to estimate the best conditional average. Data, architecture, optimization and better features can reduce it.
- More parameters can improve the second term. They cannot resolve the realized value of an independent missing driver. Adding a sensor, anatomy, calibration or longer usable history changes `X`, and can reduce the first term.
- If a trained model's residual remains large, the decomposition does not reveal which term dominates. A saturated finite-data model can still be far from `m(X)`.

**Population correlation ceiling.** For a nonconstant conditional mean, the maximum positive Pearson correlation attainable by a deterministic function of `X` is:

```text
r_max^2 = Var(E[Y | X]) / Var(Y)
        = 1 - E[Var(Y | X)] / Var(Y).
```

This follows because `Y - m(X)` is uncorrelated with every square-integrable function of `X`, then applying Cauchy–Schwarz. It is an oracle population identity, **not an estimator**. If `m(X)` is constant, no nonconstant input-based function has positive population correlation; correlation with the constant prediction itself is undefined. These qualifications matter when someone describes a numerical “information-theoretic ceiling.”

**Three different quantities that must be named.**

| Quantity | Definition/interpretation | Main trap |
|---|---|---|
| Temporal Pearson `r` | Correlation across matched time points for a specified person, run and target | Insensitive to positive scale and offset; high correlation can coexist with incorrect amplitude/baseline. |
| Predictive/calibrated `R²` | `1 - sum((y-yhat)^2)/sum((y-b)^2)`, with baseline `b` explicitly defined | Can be negative on held-out data. State whether `b` is the test-target mean, a training mean, or an operational baseline. Report calibration slope/intercept learned without test labels. |
| Explainable variance / noise-normalized performance | Model performance relative to an estimated repeatable component under a measurement model | Not automatically neural variance or an EEG observability ceiling. Normalizing an uncertain small ceiling can be unstable. |
| Fraction of neural signal | Requires a definition and measurement model for neural versus vascular/systemic contributions | Cannot be obtained from `r`, `r²`, GSR subtraction, or generic test-retest reliability alone. |

`r² = R²` only in specific settings, such as evaluating the best affine calibration of a prediction with the relevant means/variances under the same population. It is not generally true for frozen predictions. In a centered unit-variance example, `yhat = 2y` has `r = 1` but predictive `R² = 0`. This is an illustrative algebraic example, not project data. The oracle `m(X)` attains the variance-ratio `R²` above, but a finite trained model need not.

An average of `r` across people/regions cannot be squared to obtain average explained variance: `mean(r)^2` differs from `mean(r^2)`. Fisher-z averages, pooled-time correlations and averages of raw correlations are different estimands. Report all aggregation choices, weighting and handling of missing/negative values. Autocorrelated samples and overlapping EEG windows are not independent people; uncertainty should respect people/runs and temporal dependence.

**When a measurement ceiling can be estimated.** Suppose repeated observations really measure the same underlying `S`, with `Y1 = S + e1` and `Y2 = S + e2`, independent zero-mean errors of equal variance, also independent of `S`. Then:

```text
rho = Corr(Y1,Y2) = Var(S) / (Var(S) + Var(e))
Corr(S,Y1) = sqrt(rho).
```

Thus reliability is a variance fraction, whereas the corresponding correlation ceiling is its square root. Different trial counts/averaging require an appropriate correction. These relationships fail if the supposed repeats contain different underlying trajectories, correlated errors, or changed biological states.

- Repeated stimuli can support a ceiling for **stimulus-locked responses**, with trial variability defined as noise for that specific question. The same variability may be meaningful signal for a model using trial-specific EEG.
- Two resting runs do not replay identical spontaneous neural events. FC/map reliability estimates stability of those summaries, not timepoint-wise reliability of the original resting trace.
- Simultaneous multi-echo measurements sample the same event but have echo-dependent sensitivities and correlated errors. An explicit generative/noise model is needed; a raw echo-to-echo correlation is not a universal ceiling. TE-dependent systemic hemodynamics remain hemodynamics, not necessarily local neural activity.
- Scanner phantom/noise measurements can characterize components of measurement error, but not all in-vivo physiological variability. Target denoising choices change both `Y` and the relevant ceiling.
- An fMRI measurement ceiling can be high while EEG predictability is low: repeatable vascular or regional neural variation may still be absent from EEG. Conversely, EEG may predict some variability treated as “noise” by a stimulus-only repeatability analysis.

**Adding modalities.** For additional input `Z`, the oracle squared-error improvement equals:

```text
E[Var(Y | X)] - E[Var(Y | X,Z)]
  = E[Var(E[Y | X,Z] | X)] >= 0.
```

An independently validated gain establishes useful information in `Z` beyond that particular EEG model. It does not establish that a finite model already extracts everything from `X`, or that `Z` acts causally. No gain can reflect redundant sensing, noisy/poorly placed sensors, inadequate modeling, or low power, rather than fundamental sufficiency of EEG.

### Gaps

- No repeated-measurement model or target-specific reliability analysis accompanies the supplied project scores; no denominator for a claimed fraction of explainable variance has been established.
- No nonparametric estimate of `E[Var(Y|X)]` is available here. Exact repeated high-dimensional EEG histories are essentially unavailable; local-neighbor estimates require assumptions about smoothness, input noise and coverage.
- A convenient decomposition `Y = neural + vascular + noise` is not generally identifiable from these observations: the components interact and can covary. “Fraction neural” requires a stated causal/measurement model and additional validation.

## 5. What do the primary electrophysiology/fMRI and reconstruction studies actually demonstrate?

### Takeaway

Primary studies establish physiological links and valuable predictive signals, with substantial differences in species, simultaneity, output and validation. They do not collectively demonstrate a clinically validated personal replacement for regional fMRI.

### Cited Findings

| Study/status | People/animals, acquisition and overlap | Actual output/evaluation; permissible conclusion |
|---|---|---|
| **Logothetis et al., Nature 2001; peer reviewed** | **10 anesthetized macaques, 29 combined electrophysiological/fMRI sessions**, one laboratory. Simultaneous intracortical signals and visual-cortex BOLD. Figure-specific examples can involve only two animals and must not replace the total cohort count. | Local responses and fitted/validated impulse relationships. Reported figure fits and animal/site variation are not unseen-person/site reconstruction or a human scalp ceiling. [Publisher](https://www.nature.com/articles/35084005); [full original paper copy, Methods](https://mriquestions.com/uploads/3/4/5/7/34572113/logothetis_nature_review_541152.pdf) |
| **He et al., PNAS 2008; peer reviewed** | **Five epilepsy patients**, Washington University clinical setting. ECoG across wake, SWS and REM; resting fixation fMRI obtained in a **separate session**, before or after surgery. Same patients, different occasions. | Similarity of spatial correlation/network structure. Slow-potential correspondence persisted across states; gamma-power correspondence differed by state. No time-aligned personal reconstruction, held-out-person decoder, or held-out-site test. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC2564983/) |
| **Schölvinck et al., PNAS 2010; peer reviewed** | **Three awake resting macaques; 67 collected runs, 30 excluded**, leaving 37 by subtraction. Importantly, exclusions were based on lack of a consistent electrophysiology–fMRI relationship, with possible technical explanations; five excluded runs had no identified explanation. Simultaneous LFP and **MION-enhanced relative-CBV fMRI**, not ordinary BOLD. | Lagged temporal and spatial coupling; eye state affected coupling. Global association does not prove all regional trajectories are observed. Exclusion/selection makes the analyzed correlations unsuitable as an unbiased population ceiling. [Primary paper and methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC2890438/); [PubMed figures](https://pubmed.ncbi.nlm.nih.gov/20439733/) |
| **Murta et al., “Phase–amplitude coupling and the BOLD signal: A simultaneous intracranial EEG (icEEG)-fMRI study in humans performing a finger-tapping task,” NeuroImage 2017; peer reviewed** | **Seven drug-resistant epilepsy patients acquired; only three analyzed** after finding suitable significant motor BOLD clusters. One London clinical acquisition setting, simultaneous invasive EEG and **1.5 T fMRI**, five-minute motor-task run. | Local task-related BOLD amplitude and added variance from PAC/band-power regressors; not free-running regional reconstruction. No held-out-person/site prediction established. Selection, task structure and tiny analyzed sample limit extrapolation. [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5312786/) |
| **Winder et al., “Weak correlations between hemodynamic signals and ongoing neural activity during the resting state,” Nature Neuroscience 2017; peer reviewed** | Awake-mouse electrophysiology/hemodynamics; accessed publisher/abstract, total animal and per-assay counts not audited. | Useful counterweight to assuming fixed strong coupling in every state. This note quotes no numerical effect or human BOLD ceiling from it. [Primary publisher article](https://www.nature.com/articles/s41593-017-0007-y) |
| **NeuroBOLT, “Resting-state EEG-to-fMRI Synthesis with Multi-dimensional Feature Mapping,” NeurIPS 2024; peer-reviewed conference paper** | Rest: **22 people/29 simultaneous scans**. Within-scan chronological **80/10/10**, with reported 20 s split gaps; intersubject **18/5/6 scans**, keeping repeated scans from each person together. People per split not verified here. | Six selected regional time courses plus global signal; **Pearson temporal R**, not volumes or calibrated R². Reported intersubject seven-target mean `.473` is a particular split result; aggregation/seed details need the exact implementation before pooling with CV. Different target/task settings do not establish unseen-site clinical validity. [Official proceedings](https://papers.neurips.cc/paper_files/paper/2024/file/29c294ddc628c94cd2c636383ef106c1-Paper-Conference.pdf); [searchable author manuscript, split description](https://arxiv.org/html/2410.05341v1) |
| **“Bridging EEG to fMRI: Semi-Supervised Functional Connectivity Translation via Latent Alignment,” MICCAI 2026; official accepted-paper page** | Authors report Stage II **115 subjects/831 sessions from six dataset sources**, with **7:1:2 subject-level random split**. Sources are not verified unique sites, and aggregate-person deduplication was not independently established. | **Static FC translation**, not reconstruction of time courses or volumes. Dataset/split details partly come from explicitly labeled **author feedback**, alongside reviewer reproducibility concerns. No verified unseen-site or held-out-paradigm result should be inferred. [Official paper/review/response page](https://papers.miccai.org/miccai-2026/0130-Paper0924.html) |

The original NeuroBOLT data are in-scanner simultaneous EEG-fMRI; the published experiment does not establish performance from routine outside-scanner EEG. Acquisition context must accompany every transferable claim. [Author dataset description](https://huggingface.co/datasets/huxxxxi/NeuroBOLT)

### Inferences

- **State dependence is not evidence of no coupling.** A relationship can be useful within one state and shift when arousal, eye condition, anesthesia, pathology or vascular state changes. Pooling states can both create common-mode correlations and hide regional failures.
- **FC agreement is a weaker/different target than personal timepoint reconstruction.** Many different traces have the same static covariance. Good task maps or responses to a repeated stimulus can likewise coexist with poor spontaneous-event recovery.
- **Simultaneous invasive data are especially informative** because local electrical and hemodynamic events can be compared at the same time. They still have restricted coverage, selected clinical populations, and neural measures that do not directly enumerate every metabolically relevant process.
- **Two institutions are not automatically an unseen-site evaluation.** Hermes used different modality cohorts at two institutions; MICCAI's six dataset sources do not by themselves establish leave-one-acquisition-site-out testing.

### Gaps

- No clinical BOLD-substitution endpoint or prospective outside-scanner validation was identified in the studies tabulated here.
- The NeuroBOLT manuscript's exact subject counts in each scan-level split, full aggregation implementation, and correspondence of every published-version detail to the searchable v1 manuscript remain unaudited; these notes do not import its headline R into the internal CV comparison.
- Abstract-only and partially accessible sources cannot support unverified covariate adjustment, patient counts, site counts, or uncertainty estimates. Mark those fields unavailable instead of guessing.
- **Unverified quantities:** Winder's total and per-assay animal counts; NeuroBOLT's unique people per split and complete metric/seed aggregation; MICCAI 2026's deduplicated unique people, acquisition-site count, and held-out-site performance. The published/author-reported scan, session and subject totals above retain their stated provenance and must not fill these gaps.

## 6. Why is diffusion-generated plausible BOLD not verified personal BOLD, and what changes clinically?

### Takeaway

A generative model can represent a conditional distribution and produce realistic possibilities. Unless the conditioning measurements determine the clinically relevant residual, one generated possibility is not evidence that the patient's corresponding BOLD event occurred.

### Cited Findings

- **Blau and Michaeli, “The Perception-Distortion Tradeoff” (CVPR 2018; peer-reviewed theoretical/computational paper).** Distinguishes perceptual/distributional realism from reconstruction distortion in inverse problems. This is not a neuroscience clinical trial; its relevance here is methodological. [Official paper](https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html)
- **“Research on fMRI Image Generation from EEG Signals Based on Diffusion Models” (Electronics, 13 November 2025; published journal article, partial primary text accessible).** The indexed methods report **2,870 EEG-fMRI pairs** for “NODDI,” **4,828 pairs** for XP-2, and **8:1:1** and **13:2:2** partitions respectively. These are pair counts, not verified people. Participant/site counts, separation by person, and temporal-overlap protection were not verified. The data-availability text points “NODDI” to an AMICO/NODDI software wiki, making paired-data provenance insufficiently clear in the material inspected. No numerical accuracy claim from this paper is adopted. [Publisher article](https://www.mdpi.com/2079-9292/14/22/4432)
- Simultaneous in-scanner EEG contains gradient, cardiac and motion contamination, requiring correction. This establishes a measurement-domain difference to consider, not evidence that a particular trained model necessarily leaks artifacts. [Primary multiband EEG-fMRI study](https://doi.org/10.1371/journal.pone.0238485)

### Inferences

- Even if a diffusion model perfectly learns `p(Y|X)`, drawing from it does not reveal which conditionally possible outcome actually happened. Anatomical realism, spatial smoothness, power spectra, plausible networks, SSIM or a discriminator can be good while personal event timing, amplitudes or pathological deviations are wrong.
- **Illustrative mathematical deduction:** if the true `Y` and generated `Y'` are independent draws from the same exact conditional distribution given `X`, then `E[(Y-Y')^2 | X] = 2 Var(Y|X)`. The conditional mean has conditional error `Var(Y|X)`. Sampling can better preserve realism/distributional variability, but does not beat the conditional mean for squared error merely by adding plausible variation. A sampler using extra personal measurements changes the conditioning and is a different case.
- Ensembles of generated traces can describe uncertainty only if their distribution is calibrated. Multiple samples from one misspecified model need not capture epistemic uncertainty or a new disease mechanism. Evaluate proper probabilistic scores and interval/event coverage on independent people/sites; “looks diverse” is not calibration.
- **Clinical shift can affect `p(X)`, `p(Y|X)`, and the target definition.** Changes include cap/reference, channel loss, electrode contact, skull lesions, head motion, outside-scanner recording, eye/sleep state, drugs, CO2, vascular disease, tumors, scanner sequence and denoising. Some covariates can be recorded or adapted to; an unseen biological mapping cannot be repaired by reweighting EEG marginals alone.
- A normal-looking reconstruction may suppress the unusual event that matters clinically. Quantify regional/event false negatives, latency and amplitude errors, uncertainty and failure detection. A high global correlation is not evidence against a missed lesion-adjacent response or focal event.
- Predicting **observed BOLD** and inferring **neural function** are different clinical claims. A perfect imitation of a neurovascularly uncoupled BOLD map could reproduce a misleading negative; a prior-based “neural-looking” replacement could disagree with actual patient hemodynamics. Both require a stated endpoint and an independent reference.
- External-site frozen evaluation and realistic EEG acquisition are necessary tests for transfer claims, but one external dataset does not establish robustness across pathology, cap systems and prospective workflows. EEG-only could still be useful for validated narrow monitoring endpoints without claiming complete fMRI replacement.

### Gaps

- No audited diffusion study here establishes verified personal regional BOLD recovery across unseen clinical people and sites from outside-scanner EEG.
- The 2025 diffusion paper's incomplete sample/provenance audit prevents any conclusion about unseen-person/site performance or leakage. The concern is insufficiently verified design, not a demonstrated misconduct or leakage finding.
- No proof that a multimodal sensor combination fully identifies all clinically relevant BOLD components was found. “Multimodal may lift a ceiling” is supported as a hypothesis; “multimodal solves it” is not.

## 7. Which experiments distinguish data scarcity from observability limits, and what must the writer not overclaim?

### Takeaway

The strongest strategy is to vary **information available at inference**, measurement quality and independent training data separately. Improvement with an added modality is evidence of missing useful information; a small learning-curve plateau or a failed sensor addition is not proof of an absolute ceiling.

### Cited Findings

- The relevant measurement mechanisms motivate sensor and physiological perturbations: cancellation and deep-source sensitivity [Ahlfors](https://pmc.ncbi.nlm.nih.gov/articles/PMC2797557/), CO2/body coupling [Wise](https://pubmed.ncbi.nlm.nih.gov/15050588/), and disease-specific vascular effects [Pillai and Zacà](https://pmc.ncbi.nlm.nih.gov/articles/PMC3235658/).
- Target repeatability and EEG information limits must be estimated separately. [Lage-Castellanos](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006397)

### Inferences

**The following are proposed experiments, not work run in this task.** Select sample sizes by power/precision for a predeclared primary endpoint using person-level variability; no universal participant count is invented here.

| Experiment | Design and controls | Result that favors a reducible data/model limit | Result that favors missing information; remaining caveat |
|---|---|---|---|
| **1. Cross training people × EEG information** | Record high-density EEG with individual electrode locations/anatomy and simultaneous fMRI. Train matched models on genuinely independent increasing person counts; at inference compare nested channel subsets with the complete cap. Hold people/sessions/sites out and keep target quality constant. | Performance improves with independent people or model capacity at a fixed montage. | Stable gains from denser coverage at matched training size indicate an input limitation in the sparse cap. A dense-cap plateau still does not prove the complete EEG ceiling. |
| **2. Nested multimodal sensing** | EEG only; physiology only; EEG plus respiration/ETCO2/ECG/PPG; then pupil/video, blood pressure or other justified sensors. Match capacity, training data, timing and tuning. Use held-out-person/site predictions and conditional residual tests. | Extra data/model capacity closes the gap without extra sensors. | Reproducible gains beyond the best EEG baselines show useful additional information. Gains can also reflect easier feature extraction; no gain is not proof of EEG sufficiency. |
| **3. Within-person physiological dissociation** | Repeated, ethically appropriate free-breathing, paced/deep-breathing and controlled-CO2 conditions with EEG, end-tidal CO2, motion and fMRI. Prefer manipulations permitting respiratory and CO2 effects to be distinguished. Cross-condition prediction must be frozen. | Modeling observed physiology/HRF restores performance across conditions. | BOLD residuals differing with manipulated physiology after accounting for EEG support missing target drivers. “Same EEG” must be assessed with measurement-error uncertainty; breathing can itself alter neural state. |
| **4. Individual vascular calibration** | Compare a shared HRF with individual regional HRF/CVR and ASL-informed models, calibration collected independently of test responses. Repeat across days; include prespecified vascular/pathology groups. | Individual calibration materially improves held-out prediction. | Persistent EEG-unexplained but vascular-predictable variation implicates latent vascular state. Hypercapnia/CVR is not a complete assay of neurovascular coupling or metabolism. |
| **5. Local invasive triangulation where clinically available** | Pair permitted simultaneous intracranial EEG/scalp/fMRI or validated local hemodynamics, restricting analyses to covered regions. Compare scalp-only, invasive-only and combined models. Do not implant solely to satisfy this proposal. | Strong local relationships plus improved scalp processing suggest recoverable measurement/representation loss. | Invasive features predicting scalp residuals establish additional local information in that setting. Invasive residual error may still reflect limited electrode coverage, state or vascular measurement. |
| **6. Target-quality and repeatability study** | Repeated stimuli, simultaneous multi-echo or other redundant acquisitions with explicit noise covariance; validate model assumptions using held-out repeats. Estimate ceilings separately for event amplitudes, regional time courses and FC. | Low target reliability explains part of observed performance loss and improves with acquisition. | A high target ceiling with low EEG prediction leaves an EEG/model gap. Repeated resting runs alone do not quantify timepoint noise. |
| **7. Global versus regional specificity** | Report global prediction, full regional signals, and regional residual targets after a precisely specified global/physiological projection. Include a global-only spatial-template baseline and EEG/physiology controls; assess non-global spatial contrasts. | Better modeling increases regional residual accuracy beyond shared-mode baselines. | Good global/full-signal performance with weak regional residual recovery suggests limited demonstrated specificity. Target changes/GSR do not quantify a non-neural fraction. |
| **8. Feature sufficiency and history** | Compare raw signals, band-power envelopes, phase/PAC, broadband components and causal context lengths; include EMG/EOG and phase-randomization controls that preserve selected statistics. Fit all preprocessing within proper splits. | Added features/context improve independent prediction. | Physiological/invasive measurements still explain residuals after rich features, suggesting incomplete observability. Null phase results may reflect SNR or estimation difficulty. |
| **9. Scanner-to-deployment bridge and prospective validation** | Repeated same-person inside/outside-scanner EEG with matched state and equipment where possible; test acquisition-domain robustness. Subsequently freeze a fully causal pipeline for an actual prospective trial with simultaneous reference fMRI and monitored physiology. Audit buffering, timing, filtering and artifact correction. | Acquisition adaptation and calibration preserve performance. | In-scanner success disappearing after domain change implicates artifacts or context. Outside-scanner EEG has no simultaneous MRI ground truth, so bridge evidence alone cannot validate exact outside-scanner BOLD. |
| **10. Generative uncertainty and clinical endpoints** | Evaluate posterior means and samples on held-out real BOLD; use calibrated R², temporal r, proper scores, coverage, patient/event-level false negatives and prespecified clinical comparators. Include abnormal cases and OOD stress tests. | Calibrated gains on personal endpoints support useful modeling improvements. | Realism improving without matched personal accuracy illustrates prior-driven plausibility. Even well-calibrated uncertainty may be too wide for the clinical endpoint. |

**Evaluation contract for all experiments:**

1. Specify whether the output is a volume, regional continuous trace, task amplitude/map, static FC, or dynamic FC. Distinguish causal estimation of delayed hemodynamics from future forecasting.
2. Count unique people, scans/sessions and acquisition sites separately. Report within-person, unseen-person/same-site and unseen-site tests separately. Keep all repeats from a held-out person out of training/tuning; identify any permitted adaptation or calibration.
3. Split before data-dependent preprocessing, feature selection, HRF tuning, augmentation and model selection. Windows and subjects are different sampling units. Purge boundary overlap according to actual context, filtering and target construction; a nominal time gap alone is not a full leakage audit.
4. Report per-run/per-target temporal Pearson r and calibrated predictive R² with baseline, units, scaling and calibration specified. Include raw and Fisher-z summaries if useful, with weighting explicit. Report regional distributions and uncertainty, not only pooled points or a mean across targets.
5. Use person-level resampling and temporal block/surrogate controls that respect autocorrelation; compare models on the same held-out observations. A non-significant difference does not establish equivalence without a prespecified equivalence margin and adequate precision.
6. Log physiological covariates, state, medication, artifacts and missing sensors. Report actual adjustment; “physiology recorded” is not “all confounds removed.” Separate common arousal capture from evidence of region-specific neural reconstruction.
7. Use strong ridge/linear and global/physiology-only baselines. Add architecture only when it wins on the same split, context and endpoints. Enforce causal preprocessing when making streaming claims.

**What the writer must not overclaim:**

- No universal ceiling such as “EEG-to-fMRI tops out at r ≈ 0.3.” Neither current scores nor anatomical nonuniqueness quantify it.
- No claim that more parameters solve absent information, or that failure of a modest model proves absent information.
- No claim that deep sources are always invisible, that dense EEG identifies all sources, that all scalp gamma is neural, or that all signals above 20 Hz are muscle.
- No substitution of separate-session FC correspondence, task maps, animal optical signals, or contrast-enhanced CBV for simultaneous human resting BOLD reconstruction.
- No statement that global BOLD is wholly artifact or wholly local neural activity; no interpretation of a GSR-associated score drop as a measured vascular fraction.
- No conversion of mean temporal r into calibrated R², explainable-variance fraction, neural fraction, disease sensitivity, or clinical accuracy.
- No claim of cross-site equivalence from close point estimates; no inference that frozen transfer to one dataset establishes general clinical portability.
- No statement that replay is a prospective live scanner trial; no claim that generated plausible BOLD is the verified personal recording.
- No importing final-paper cohort totals from a preprint, treating paired windows as people, or treating multiple dataset sources as verified acquisition sites.

### Gaps

**Internal provenance U1 — supplied by the user in this assignment, not peer reviewed and not independently audited here. No public source URL was provided.** These observations are context, not part of the external evidence grade:

| Supplied internal observation | Permissible interpretation and limitation |
|---|---|
| **22 people / 29 VU resting scans; full ridge seven-target R `.381` versus shared 24 s NeuroBOLT `.336` in subject-grouped CV.** | Describes the supplied comparison under its CV/context. Does not establish an architecture-independent ceiling or superiority in every setting. Exact averaging, confidence intervals and implementation were not re-audited. |
| **Removing global signal changes 64-region mean R `.343` to `.144`.** | Evidence that the evaluated target/preprocessing choice materially affects reported accuracy. Does not establish what fraction of predicted signal is non-neural; global regression changes both target and variance structure. |
| **Frozen VU ridge on 28 ds006040 people: eyes-closed R `.227`, versus `.228` trained within site; eyes-open `.140`.** | A supplied external-dataset/state comparison. No demonstrated equivalence, no inference of pathology generalization, no invented site count or participant overlap. Acquisition and split details beyond those supplied remain unaudited. |
| **Arousal-monitor prototype global BOLD streaming replay r `.263`.** | Replay feasibility only. It is **not a prospective live scanner trial**; latency, online artifact correction and prospective clinical utility remain unestablished. |

The small VU learning curve cannot distinguish finite-sample/model limitations from `E[Var(Y|X)]`. Needed but unavailable quantities include per-target repeatability, causal versus offline preprocessing effects, physiology's conditional information gain, dense-cap gains, subject/site uncertainty, pathology effects, and prospective decision performance. These are the unmeasured ceilings and gaps that should frame the report's conclusions.
