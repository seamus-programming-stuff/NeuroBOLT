# Interpreting EEG-to-BOLD encoding models, and EEG-informed HRFs / transfer functions

Scope note: these notes are for a project predicting resting-state DiFuMo-64 ROI BOLD (TR 2.1 s) from 26-channel scalp EEG in 22 people (the VU dataset used by NeuroBOLT, [arXiv:2410.05341](https://arxiv.org/abs/2410.05341)). The best model is ridge on lagged log power (26 ch x 44 one-Hz bins x 12 two-second lags = 13,728 features). Its weights show alpha/beta power 5-12 s before a frame predicting lower BOLD, with an opposite-sign term at the shortest lags. The deep model (multi-scale STFT + LaBraM) is no better than ridge. Preprints are flagged **[preprint]**. Conference abstracts are flagged **[abstract]**. Claims I could check only through secondary summaries are flagged **[secondary]**.

---

## 1. Does Haufe et al. 2014 apply to an EEG→BOLD ridge model, and what do structure coefficients, PDP, permutation importance, drop-group refits and variance partitioning add with collinear lagged spectral features?

### Takeaway
Yes, Haufe applies, though the reason is easy to miss. With respect to the EEG features, an EEG→BOLD ridge is a multivariate *extraction filter*: a "backward model" in Haufe's sense, because many correlated measured channels are combined to read out one target. Its raw weights are therefore filters, not patterns. They can be large, or sign-flipped, on features that only cancel shared variance (suppressors). The fix is to report a pattern a ∝ Cov(X, ŷ) alongside the weights. For a single target this is the same as structure coefficients up to per-feature scaling. Then use group-level refits (drop-group or banded ridge) to measure *unique* contributions. Single-feature permutation importance and plain partial dependence are close to useless here, because they extrapolate off the data manifold.

### Cited Findings
**Haufe and the filter-vs-pattern distinction**
- Haufe et al. 2014 (NeuroImage 87:96-110, DOI 10.1016/j.neuroimage.2013.10.067) make the core point: forward-model parameters can be read neurophysiologically, but backward-model weights can be nonzero at channels whose activity is statistically independent of the process of interest. They give a procedure that turns a linear backward model into an "activation pattern", which can be interpreted. — [PubMed 24239590](https://pubmed.ncbi.nlm.nih.gov/24239590); [author PDF](https://doc.ml.tu-berlin.de/bbci/publications/HauMeiGoeDaeHayBlaBie13.pdf)
- The transform (A = Σ_x W Σ_ŝ⁻¹) is now standard. MNE-Python's `get_coef` returns both "filters" and "patterns" with this citation. — [MNE docs](https://mne.tools/0.21/generated/mne.decoding.get_coef.html)
- Kriegeskorte & Douglas 2019 (Curr Opin Neurobiol 55:167-179, DOI 10.1016/j.conb.2019.04.002) say reading weights as feature contributions in an encoding model "can be problematic when the predictor variables or their noise components are correlated and when priors (or penalties) are used to regularize the fit". They add that a single significant encoding model gives weak theoretical constraints, so many models must be compared inferentially. — [PMC6705607](https://pmc.ncbi.nlm.nih.gov/articles/PMC6705607/); [arXiv:1812.00278](https://arxiv.org/abs/1812.00278)
- Weichwald et al. 2015 (NeuroImage) give causal interpretation rules for encoding vs decoding models. Encoding-model weights support causal claims only when the predictor is experimentally manipulated, which spontaneous EEG power is not. — [arXiv:1511.04780](https://arxiv.org/abs/1511.04780)
- Wilming, Haufe et al. 2022 (Machine Learning 111) built linear ground-truth data containing suppressor variables. Most attribution methods (LRP, DTD, PatternNet, PatternAttribution, LIME, Anchors, SHAP, permutation-based) could not tell important features from suppressors. Haufe-style activation-pattern methods gave the best explanations. — [ar5iv 2111.07473](https://ar5iv.labs.arxiv.org/html/2111.07473); [MLJ record](https://mlanthology.org/mlj/2022/wilming2022mlj-scrutinizing)
- The same group's XAI-TRIS benchmark extends the suppressor problem to non-linear settings **[preprint]**. PatternLocal (2025) targets false-positive attributions in non-linear models **[preprint]**. — [arXiv:2306.12816](https://arxiv.org/abs/2306.12816); [arXiv:2505.11210](https://arxiv.org/html/2505.11210v3)

**Collinearity among EEG bands is real and changes maps**
- de Munck et al. 2009 (NeuroImage 47:69-76) used 15 subjects at rest for 30 min. When significant, the BOLD maps for other bands "looked much like the alpha map", especially beta, even with alpha harmonics discarded. Adding the other bands as confounders "has a large effect" on the SPM, especially when each band's HRF is estimated from the data. Their conclusion: band powers are strongly intercorrelated, so a multi-frequency model is required. — [UvA record](https://www.dare.uva.nl/id/b7151024-b98f-4d70-834e-984824ebb377)
- Rosa et al. 2010 found total-power and per-band regressors "highly collinear", so their individual contributions were hard to separate (see Q3). — [PMC2793371](https://pmc.ncbi.nlm.nih.gov/articles/PMC2793371/)

**Structure coefficients, commonality and variance partitioning**
- Kraha et al. 2012 (Front Psychol 3:44) review tools for interpreting regression under multicollinearity: beta weights, structure coefficients (r between each predictor and ŷ), commonality analysis, dominance and relative-weight analysis. Structure coefficients are not distorted by collinearity, but they say nothing about unique contribution. — [DOI 10.3389/fpsyg.2012.00044](https://doi.org/10.3389/fpsyg.2012.00044)
- Variance partitioning in fMRI encoding comes from Lescroart, Stansbury & Gallant 2015 (Front Comput Neurosci, [DOI 10.3389/fncom.2015.00135](https://doi.org/10.3389/fncom.2015.00135)) and de Heer et al. 2017 (J Neurosci, [DOI 10.1523/JNEUROSCI.3267-16.2017](https://doi.org/10.1523/JNEUROSCI.3267-16.2017)). Each fits models on every subset of feature groups and derives unique and shared variance from set arithmetic on held-out R².
- Dupré la Tour, Eickenberg, Nunez-Elizalde & Gallant 2022 (NeuroImage 264:119728) note that classic variance partitioning yields 2^m − 1 terms that are "hard to interpret". They propose **banded ridge**, with one regularization hyperparameter per feature space. It sets aside non-predictive or redundant spaces and improves both accuracy and interpretability. They also give a product-measure variance decomposition whose cost scales linearly with the number of spaces. Code is in the Himalaya package. — [PMC9807218](https://pmc.ncbi.nlm.nih.gov/articles/PMC9807218/); [Gallant lab](https://gallantlab.org/publications/2022-feature-space-selection-banded/)
- A 2025 CCN abstract compares variance partitioning with the "residual method" for interpreting encoding models **[abstract]**. — [Schultheiss 2025](https://2025.ccneuro.org/abstract_pdf/Schultheiss_2025_Comparing_Variance_Partitioning_Residual_Method_Interpreting.pdf)

**Permutation importance, conditional/grouped permutation, drop-group refits, PDP/ALE**
- Hooker, Mentch & Zhou 2021 (Stat Comput 31:82) show that permute-and-predict importance and partial dependence plots "can vastly over-emphasize correlated features". Breaking dependencies forces the model to extrapolate into sparse regions of feature space. They recommend measuring the loss in performance after *refitting* without the features ("at least one more model"). — [arXiv:1905.03151](https://arxiv.org/abs/1905.03151)
- Strobl et al. 2008 (BMC Bioinformatics 9:307) introduced conditional permutation, which permutes within strata of correlated covariates. It avoids extrapolation but tends to *underestimate* importance, and it gets computationally hard as n grows. — [DOI 10.1186/1471-2105-9-307](https://doi.org/10.1186/1471-2105-9-307); trade-offs as summarised in [Hooker et al.](https://arxiv.org/abs/1905.03151) and [arXiv:2411.02221](https://arxiv.org/pdf/2411.02221v2) **[secondary]**
- Gregorutti, Michel & Saint-Pierre 2017 (Stat Comput 27:659) show that permutation importance of each variable shrinks as the number of correlated copies grows, and propose *grouped* permutation importance. — [arXiv:1310.5726](https://arxiv.org/abs/1310.5726)
- Leave-one-covariate-out (LOCO) refits from Lei et al. 2018 (JASA) and the nonparametric VIM framework of Williamson et al. 2021 (Biometrics) both define importance as the drop in population R² when a feature group is removed and the model refit. They come with valid inference. — [arXiv:1604.04173](https://arxiv.org/abs/1604.04173); [DOI 10.1111/biom.13392](https://doi.org/10.1111/biom.13392)
- Accumulated Local Effects (ALE; Apley & Zhu 2020, JRSS-B) were designed to replace PDPs when features are correlated. — [arXiv:1612.08468](https://arxiv.org/abs/1612.08468)
- Molnar et al. 2022 catalogue model-agnostic interpretation pitfalls: extrapolation under dependence, confusing correlation with causation, and ignoring model uncertainty. — [arXiv:2007.04131](https://arxiv.org/abs/2007.04131)
- Grouped feature-importance and combined-feature-effect plots are developed in Au et al. 2022 (Data Min Knowl Disc). — [arXiv:2104.11688](https://arxiv.org/abs/2104.11688)

**Forward TRF analogy**
- The mTRF literature uses the same lagged-ridge design: Crosse et al. 2016 (Front Hum Neurosci 10:604) and Crosse et al. 2021 (Front Neurosci 15:705621), the latter on methodological considerations. Forward TRF weights are routinely read as response kernels. With several correlated stimulus features, however, regularization and collinearity bias the kernels. — [DOI 10.3389/fnhum.2016.00604](https://doi.org/10.3389/fnhum.2016.00604); [DOI 10.3389/fnins.2021.705621](https://doi.org/10.3389/fnins.2021.705621)

### Inferences
- **Which direction is "forward"?** In Haufe's framework, forward/backward is defined relative to the *multivariate measured data* (here the 13,728 EEG features), not relative to brain vs stimulus. A model ŷ = Xw that reads one BOLD ROI out of many correlated EEG features is formally an extraction filter. So the ridge weights in band x lag x channel are filters. A positive short-lag weight can be a suppressor that subtracts slow shared variance (e.g., broadband or arousal-related power) rather than a "positive coupling". (Inference from Haufe 2014 and Wilming 2022.)
- **Pattern for a single target.** For one target, the Haufe pattern is a = Cov(X, ŷ)/Var(ŷ). Each element equals SD(x_j)·corr(x_j, ŷ)/SD(ŷ), so it is the structure coefficient rescaled by feature SD. It is cheap: one matrix-vector product per ROI on held-out data. It should be shown as a channel x frequency x lag map next to the weights. Because log power is strongly autocorrelated across 2-s lags, the pattern will be much smoother over lags than the weights. If the short-lag opposite-sign lobe disappears in the pattern, it is a filter/suppressor feature, not a separate physiological response. (Derived from Haufe 2014 and Kraha 2012.)
- **What ridge does to adjacent lags.** Ridge shrinks most strongly along low-variance directions of X'X. For autocorrelated lags those directions are high-frequency contrasts *between* adjacent lags. So a surviving [+ short lag, − long lag] contrast is either real signal or a sign that λ is too small. Check it along the regularization path, and against a model with a lag-smoothness or rank constraint (see Q5). (Inference.)
- **Unique vs shared.** For "what does the model use", the defensible quantities are group-level: bands (delta/theta/alpha/beta/gamma), channel clusters, and lag windows (0-4 s vs 4-12 s vs 12-24 s). Measure (i) held-out ΔR² from drop-group refits (LOCO/VIM) and (ii) banded-ridge per-group λ or variance decomposition. Single-feature permutation importance on 13,728 near-duplicate features will be near zero everywhere and biased toward extrapolation artefacts. If a permutation approach is used, permute whole groups using circular time-shifts within a scan, so autocorrelation is preserved. (Inference from Hooker 2021, Gregorutti 2017, Dupré la Tour 2022.)
- **PDP adds nothing for ridge.** For a linear model, a PDP is a straight line with slope w_j. It only becomes informative (ALE preferred) for the deep model. (Inference.)
- **Expect redundancy.** Following de Munck 2009, alpha and beta maps should be expected to look alike, and unique beta variance may be small even if beta weights are large. (Inference.)

### Gaps
- I found no paper that applies the Haufe transform, or a structure-coefficient map, specifically to an EEG-spectrum → BOLD ridge model. The recommendation above is derived, not reported.
- No published study compares LOCO, conditional permutation and banded-ridge decompositions on lagged EEG spectral features. Their relative bias for this design is unknown.

---

## 2. Attribution for deep EEG models (IG, occlusion, band ablation, spectral attribution on EEG transformers), and known failure modes

### Takeaway
Gradient-family methods with a principled baseline (Integrated Gradients, DeepLIFT, gradient×input, LRP) behave best on EEG benchmarks. But every attribution method inherits the suppressor problem, and per-sample maps are unreliable. For a NeuroBOLT-type model, the most defensible "what does it use" analyses are:
- frequency-band ablation with *retraining*, or with in-distribution replacement;
- frequency-domain relevance (DFT-based "virtual inspection layers");
- comparison to the ridge's Haufe pattern.

LaBraM-specific interpretability work exists only as 2025-2026 preprints. Attention weights are not explanations.

### Cited Findings
- **Integrated Gradients** (Sundararajan, Taly & Yan, ICML 2017) satisfies sensitivity, implementation invariance and completeness: attributions sum to F(x) − F(baseline). The result depends entirely on the baseline. — [arXiv:1703.01365](https://arxiv.org/abs/1703.01365)
- **Sanity checks** (Adebayo et al., NeurIPS 2018): some saliency methods (e.g., Guided Backprop, Guided GradCAM) barely change when model weights are randomized, so they act like edge detectors rather than model explanations. Plain gradients and GradCAM pass. — [arXiv:1810.03292](https://arxiv.org/abs/1810.03292)
- **ROAR** (Hooker et al., NeurIPS 2019): removing "important" inputs without retraining confounds importance with distribution shift. Retraining after removal showed many methods no better than random, apart from some ensembling variants. — [arXiv:1806.10758](https://arxiv.org/abs/1806.10758)
- **Unreliability** (Kindermans et al. 2019): several attribution methods are not invariant to a constant input shift that the model ignores. — [arXiv:1711.00867](https://arxiv.org/abs/1711.00867)
- **PatternNet / PatternAttribution** (Kindermans et al., ICLR 2018) extend the Haufe filter-vs-pattern idea to deep nets by separating "signal" from "distractor" directions. — [arXiv:1705.05598](https://arxiv.org/abs/1705.05598)
- **Suppressor failure.** Wilming et al. 2022 showed that LRP, SHAP, LIME and permutation methods attribute importance to suppressor features in linear ground truth (see Q1). — [ar5iv 2111.07473](https://ar5iv.labs.arxiv.org/html/2111.07473)
- **EEG benchmark** (Cui et al. 2023, Front Comput Neurosci 17:1232925): seven methods were compared across models and datasets for EEG-BCI. Gradient×Input, DeepLIFT, Integrated Gradients and LRP performed similarly and better than saliency, deconvolution and guided backprop. Interpretation quality was inconsistent across individual samples even for good methods, and depended on architecture and dataset. — [PMC10470463](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10470463/); [arXiv:2202.06948](https://arxiv.org/abs/2202.06948)
- **Spectral perturbation on EEG CNNs** (Schirrmeister et al. 2017, HBM 38:5391): introduced amplitude-perturbation visualisation. Spectral amplitudes are perturbed and output changes are correlated with the perturbation, giving band x channel importance maps. — [arXiv:1703.05051](https://arxiv.org/abs/1703.05051)
- **Frequency-domain relevance for time-series models** (Vielhaben et al. 2024, Pattern Recognition): "virtual inspection layers" insert an invertible DFT/STFT so that LRP or other relevance can be read out per frequency (and time-frequency) for models that take raw time series. — [arXiv:2303.06365](https://arxiv.org/abs/2303.06365)
- **Attention ≠ explanation** (Jain & Wallace 2019): attention weights often do not correlate with gradient-based importance, and alternative attention distributions can yield the same prediction. — [arXiv:1902.10186](https://arxiv.org/abs/1902.10186)
- **Models in question.** LaBraM (Jiang et al., ICLR 2024) is a channel-patch transformer pretrained by masked prediction of neural-codebook tokens learned from Fourier amplitude and phase ([arXiv:2405.18765](https://arxiv.org/abs/2405.18765)). BIOT (Yang et al., NeurIPS 2023) is a biosignal transformer that tokenises each channel's STFT ([arXiv:2305.10351](https://arxiv.org/abs/2305.10351)).
- **LaBraM-specific interpretability (all recent preprints):**
  - Attention-aware LRP applied to LaBraM (12 layers x 10 heads), claimed to give finer input and intermediate-layer attributions than Attention Rollout or SHAP **[preprint, 2026]**. — [arXiv:2605.11885](https://arxiv.org/pdf/2605.11885)
  - A causal "feature audit" of LaBraM, CBraMod and CSBrain on five clinical tasks: 648/945 (68.6%) model-task-feature units were "representation-causal" and 199 (21.1%) "encoded-only". Frequency-domain features dominated, but other feature families carried substantial causal mass **[preprint; NeurIPS 2026 poster]**. — [arXiv:2605.11410](https://arxiv.org/pdf/2605.11410); [NeurIPS listing](https://neurips.cc/virtual/2026/poster/150770)
  - A LaBraM Alzheimer's-diagnosis study used occlusion of regions and frequency bands **[preprint]**. — [arXiv:2608.27719](https://arxiv.org/pdf/2608.27719)
  - A sparse-autoencoder study across SleepFM, REVE and LaBraM **[preprint]**. — via [emergentmind summary](https://www.emergentmind.com/topics/labram) **[secondary]**

### Inferences
- **Make deep-model attributions comparable to ridge.** Aggregate absolute (or signed) IG attributions into the same channel x 1-Hz-bin x 2-s-lag grid used by ridge. For the STFT branch this is direct. For the LaBraM branch it needs a DFT virtual-inspection layer (Vielhaben 2024). Then correlate the deep map with the ridge Haufe pattern, not with ridge weights. If they match, the deep model is using the same alpha/beta-history signal, which would be consistent with its lack of advantage. (Inference.)
- **Baseline choice for IG on spectral input.** A zero-power baseline is far off-manifold for log power. Better choices are the subject's mean log spectrum, or an expected-gradients-style average over random in-scan time points. (Inference from Sundararajan 2017 and Hooker 2021.)
- **Band ablation.** Zeroing a band of the input STFT is the deep analogue of unrestricted permutation: off-distribution and biased (Hooker 2019, Hooker 2021). Prefer (a) retraining with the band removed (ROAR/LOCO logic), or (b) replacing band power with a circularly time-shifted copy from the same scan, which keeps marginal statistics. (Inference.)
- **Attention maps.** Attention maps from LaBraM should not be presented as the explanation (Jain & Wallace 2019). Use LRP or IG through the attention layers instead. (Inference.)

### Gaps
- I found no peer-reviewed study that applies attribution to an EEG→fMRI *regression* model (NeuroBOLT or similar) and reports which bands and lags it uses. The NeuroBOLT paper itself is the primary model reference, and I did not verify whether it contains attribution analyses.
- The LaBraM interpretability findings are preprints, mostly from 2026, on classification tasks, so their relevance to BOLD regression is untested.

---

## 3. Classic EEG-informed fMRI: kernel latencies vs canonical HRF, and sign of coupling by band and region

### Takeaway
At eyes-closed rest, alpha power couples **negatively** with BOLD in occipital, parietal and lateral fronto-parietal (attention) cortex. It couples **positively** in the thalamus (anterior and mediodorsal) and insula/cingulo-opercular regions. The thalamic response peaks a few seconds earlier than the cortical one. Beta is also mostly negative in sensory cortex (Scheeringa), but beta-2 (17-23 Hz) was positive with DMN nodes in Laufs 2003. Gamma, and the relative high-vs-low-frequency balance, couple positively. Time-resolved estimates put BOLD peaks about 5-10 s after the EEG change (gamma-LFP lag 6-8 s in monkey). Low-frequency (2-15 Hz) LFP–BOLD coupling at rest was near zero-lag.

### Cited Findings
**Alpha: cortex negative, thalamus positive**
- Goldman et al. 2002 (NeuroReport 13:2487-2492, DOI 10.1097/01.wnr.0000047685.08940.d0) did simultaneous EEG-fMRI of alpha. Martinez-Montes et al. 2004 report that their data-driven alpha atom (parieto-occipital cortex, thalamus, insula) "matched closely" Goldman's conventional result. — [ModelDB citation](https://modeldb.science/citations/107473); [Martinez-Montes PubMed 15219575](https://pubmed.ncbi.nlm.nih.gov/15219575)
- A tensor-methods review describes the Martinez-Montes alpha atom's spatial signature as positive for thalamus and negative for visual cortex. — [arXiv:1506.06040](https://arxiv.org/pdf/1506.06040) **[secondary]**
- Moosmann et al. 2003 (NeuroImage; fMRI + NIRS; PMID 14527577) is cited for negative occipital alpha–BOLD and positive thalamic correlation. — [Neurosynth record](https://neurosynth.org/studies/14527577); summarised in [PMC3472152](https://pmc.ncbi.nlm.nih.gov/articles/PMC3472152) **[secondary]**
- **de Munck et al. 2007** (NeuroImage 35:1142-1151, DOI 10.1016/j.neuroimage.2007.01.022):
  - 16 subjects, eyes-closed rest. The alpha response function (ARF) was estimated with no a priori shape.
  - Thalamic ARF mainly positive, peaking "a few seconds earlier" than occipital/parietal cortex.
  - Occipital and parietal ARFs similar in amplitude and timing.
  - One subject had a positive cortical ARF.
  - No systematic BOLD *preceding* alpha, except in the two highest-alpha subjects.
  - Strong immediate positive correlation at the eyeball and negative at the back of the eye.
  - Cortical ARF peak times formed a pattern interpreted as a travelling wave.
  - The authors note the spatial ARF pattern mixes local alpha differences with local HRF differences.
  - — [UvA record](https://dare.uva.nl/id/2cb87dac-6040-4c67-b6fb-b4cf8a3eb6df)
- Liu et al. 2012 (NeuroImage 63:1060-1069) found that thalamic coupling is subdivided: negative alpha–BOLD correlations mostly in visual thalamus (pulvinar > LGN), positive at anterior and mediodorsal nuclei. — [PMC3472152](https://pmc.ncbi.nlm.nih.gov/articles/PMC3472152)
- Omata et al. 2013: the slow-fluctuation component of alpha power correlated positively with BOLD in brainstem, medial thalamus and ACC. — [PMC3688940](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3688940/)
- A review notes alpha–fMRI results are "generally consistent in cortical regions but notably variable in the thalamus". — via search summary of [PMC3688940](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3688940/) **[secondary]**
- Sadaghiani et al. 2010 (J Neurosci 30:10243): alpha power correlated positively with a cingulo-opercular/thalamic "tonic alertness" network and negatively with dorsal attention regions. — [DOI 10.1523/JNEUROSCI.1004-10.2010](https://doi.org/10.1523/JNEUROSCI.1004-10.2010)

**Laufs 2003 (PNAS 100:11053, DOI 10.1073/pnas.1831638100)**
- 10 analysed subjects, eyes closed, canonical-HRF-convolved band power.
- Alpha was negatively correlated with bilateral lateral frontal and parietal cortex. Peak was left lateral PFC (−44, 34, 16), Z = 5.8; parietal peaks at (−50, −52, 50) and (34, −72, 48).
- Positive alpha correlations were sparse (occipital, mid-cingulate).
- **Beta-2 (17-23 Hz) correlated positively** with PCC (Z = 4.3), precuneus (Z = 4.1), left TPJ (Z = 4.5) and dmPFC (Z = 3.7-3.8). The authors read this as an EEG signature of the default-mode network.
- Beta-3 (24-30 Hz) gave a positive ACC peak (Z = 5.6) and negative PCC/TPJ/PFC. Beta-1 and theta showed no effects. No thalamic results were reported.
- — [PMC196925](https://pmc.ncbi.nlm.nih.gov/articles/PMC196925)
- Laufs et al. 2006 reanalysed the 2003 datasets. They described two alpha patterns across studies: occipital/parietal BOLD increases with alpha decreases, vs frontal-parietal. — [Laufs 2006 PDF](https://www.unicog.org/publications/Laufs.Neuroimage.2006.pdf)

**Mantini 2007 (PNAS 104:13170)**
- ICA gave 6 RSNs. Each RSN's BOLD correlated with a *specific combination* of delta, theta, alpha, beta and gamma power, not a single band. — [PMC1941820](https://pmc.ncbi.nlm.nih.gov/articles/PMC1941820)

**Gamma vs alpha/beta independence**
- Scheeringa et al. 2011 (Neuron 69:572-583): during a visual attention task, trial-by-trial BOLD increased with high-gamma (60-80 Hz) power and decreased with alpha and beta power. The two contributions were *independent*. — [MPI record](https://forms.mpi.nl/node/46580); [PMID 21315266](https://neuinfo.org/literature/pmid:21315266?rpKey=on)
- Scheeringa et al. 2016 (PNAS), laminar: gamma correlated positively with superficial-layer BOLD; beta negatively with deep-layer BOLD; alpha negatively with both. — [PMC4914170](https://pmc.ncbi.nlm.nih.gov/articles/PMC4914170) (link as returned by search; verify) and [dataset](https://data.ru.nl/collections/di/dccn/DSC_3016026.03_440)

**Transfer-function / "heuristic" models**
- **Rosa et al. 2010** (NeuroImage 49:1496-1509, DOI 10.1016/j.neuroimage.2009.09.011):
  - Design: 3 subjects x 3 sessions, flicker at 2-30 Hz, TR 3.06 s, first EEG PC, Morlet power over 1-40 Hz. They did *not* estimate a free kernel: EEG regressors were convolved with canonical HRF + temporal + dispersion derivatives, and the temporal derivative explained significant variance.
  - Best model: the RMS-frequency "heuristic" (√Σ f²·P̃(f), relative power). It correlated positively with BOLD, while total power and 1-7 Hz power correlated negatively.
  - Three-way comparison within the activation mask (p < .001 uncorrected): Heuristic 620 voxels, F_max 13.3; total power 5 voxels, F_max 8.2; 3-band model 18 voxels, F_max 4.9. Only the Heuristic survived FWE.
  - Total-power and band regressors were highly collinear.
  - — [PMC2793371](https://pmc.ncbi.nlm.nih.gov/articles/PMC2793371/)
- Rosa, Kilner & Penny 2011 (PLoS Comput Biol 7:e1002070) did Bayesian comparison of neurovascular coupling models with EEG-fMRI. — cited in [SPM bibliography](https://www.fil.ion.ucl.ac.uk/spm/doc/biblio/Author/ROSA-MJ.html)
- Leite, Leal & Figueiredo 2013 (Front Neurol 4:1; single hypothalamic-hamartoma patient, ICA-EEG): frequency-weighted (RMSF) metrics outperformed power-weighted metrics, consistent with a prior healthy-subject visual study. This is the "Leite 2013" paper; it is in Frontiers in Neurology, not HBM. — [PMC3554836](https://pmc.ncbi.nlm.nih.gov/articles/PMC3554836)
- Sato et al. 2010 (NeuroImage 50:1416-1426, DOI 10.1016/j.neuroimage.2010.06.018), "From EEG to BOLD: brain mapping and estimating transfer functions in simultaneous EEG-fMRI acquisitions". Record found; methods and results not retrieved. — [USP repository](https://repositorio.usp.br/item/001965756)
- Murta, Leite, Carmichael, Figueiredo & Lemieux 2015 (HBM 36:391-414, DOI 10.1002/hbm.22623) review the electrophysiological correlates of BOLD for EEG-informed fMRI. — [ISR Lisboa listing](https://welcome.isr.tecnico.ulisboa.pt/?p=20255)

**Eyes-open rest, region-specific HRFs (closest to this project's setting)**
- Prokopiou, Xifra-Porxas, Kassinopoulos, Boudrias & Mitsis **[preprint, bioRxiv 2020; journal version not verified]**:
  - Source-reconstructed band power (< 100 Hz) predicted BOLD with block-structured models: HRF ⊛ (linear combination of band powers), i.e., a separable band x lag kernel.
  - Motor task: BOLD variance "mainly explained by" beta; the HRF was mainly negative, attributed to beta desynchronisation and post-movement rebound.
  - Eyes-open rest: all bands contributed significantly, with region-dependent weights.
  - HRF shapes were positive in sensorimotor cortex and *negative* in parietal/occipital cortex.
  - Resting-state band contributions and HRFs varied across subjects (7 subjects in the ISMRM version).
  - — [bioRxiv 10.1101/2020.06.29.178483](https://www.biorxiv.org/content/10.1101/2020.06.29.178483v2); [ISMRM 2019 abstract](https://archive.ismrm.org/2019/2673.html)
- Mann-Krzisnik & Mitsis 2022 (HBM 43:4045-4073), with region/component-specific Laguerre-basis HRFs:
  - Motor-imagery HRFs "peak around 5-10 s".
  - Resting state (Deligianni data, 11 subjects, TR 2.16 s): single-subject correlations between BOLD and its EEG-based estimate were only 0.19-0.28 with 1 component and 0.24-0.32 with 2. The null was rejected in 1/33 and 0/33 cases respectively.
  - — [PMC9374895](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374895/)
- Simões et al. 2020 (J Neural Eng 17(4)) ask "How much of the BOLD-fMRI signal can be approximated from simultaneous EEG data". In the companion ISMRM abstract, random forests on scalp + source features raised accuracy from 20% to 53% **[abstract]**. — [CISUC record](https://old.cisuc.uc.pt/publication/show/6254); [ISMRM 2020](https://archive.ismrm.org/2020/3937.html)
- Meir-Hasson et al. 2014 (NeuroImage 102:128-141): an "EEG finger-print" predicting amygdala BOLD from time-frequency features of one electrode, later used for neurofeedback (Keynan 2016). — [DBLP](https://dblp.dagstuhl.de/pid/74/10230.html)

**Arousal / global signal**
- Wong et al. 2013 (NeuroImage; 10 subjects, eyes-closed): resting global-signal amplitude was negatively correlated with an EEG vigilance measure. A later definition of the vigilance index is alpha / (delta+theta) power (Falahpour 2018). — [ISMRM abstract](https://archive.ismrm.org/2013/2245.html); [Frontiers opinion summarising](https://www.frontiersin.org/articles/10.3389/fnins.2019.00823/full) **[secondary for the index definition]**

**Invasive anchors for sign and lag**
- Schölvinck et al. 2010 (PNAS), monkey, rest:
  - LFP at one site correlated positively with fMRI across nearly the whole cortex.
  - Upper gamma (40-80 Hz) led BOLD by about **6-8 s**.
  - 2-15 Hz power also correlated strongly, but at **near-zero lag**.
  - Coupling was stronger and *anticipatory* with eyes closed.
  - The authors warned against global-signal regression.
  - — [PMC2890714](https://pmc.ncbi.nlm.nih.gov/articles/PMC2890714)
- Magri et al. 2012 (J Neurosci 32:1395-1407):
  - Gamma (40-100 Hz) was the most informative band for BOLD, and alpha (8-12) and beta (18-30) carried complementary information.
  - The alpha–gamma relation was reflected in BOLD *amplitude*.
  - The beta–gamma relation was reflected in BOLD *latency* relative to gamma changes.
  - — [PMC3240306](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3240306/)
- Goense & Logothetis 2008 (Curr Biol 18:631-640): in awake V1 the largest share of BOLD variance was explained by 20-60 Hz LFP. — [Glasgow eprint](https://eprints.gla.ac.uk/85078)
- Logothetis et al. 2001 (Nature 412:150) found LFP was the only signal significantly correlated with BOLD at transient-response sites. — [IDEAS record](https://ideas.repec.org/a/nat/nature/v412y2001i6843d10.1038_35084005.html)
- Mukamel et al. 2005 (Science 309:951-954): in 2 patients, BOLD predicted from auditory-cortex single-unit firing correlated with fMRI from 11 other subjects watching the same movie at **r = 0.75** (P < 10⁻⁴⁷). — [Hasson lab](https://hassonlab.princeton.edu/publications/coupling-between-neuronal-firing-field-potentials-and-fmri-human-auditory-cortex)

**Reviews**
- Huster et al. 2012 (J Neurosci 32:6053; [DOI 10.1523/JNEUROSCI.0447-12.2012](https://doi.org/10.1523/JNEUROSCI.0447-12.2012))
- Abreu et al. 2018, "EEG-informed fMRI: a review of data analysis methods" (Front Hum Neurosci 12:29; [DOI 10.3389/fnhum.2018.00029](https://doi.org/10.3389/fnhum.2018.00029))
- Warbrick 2022 (Sensors 22:2262; [DOI 10.3390/s22062262](https://doi.org/10.3390/s22062262))

### Inferences
- **The 5-12 s negative alpha/beta lobe** matches what the literature predicts. The sign agrees with the cortical alpha–BOLD and beta–BOLD negative coupling (Goldman, Laufs, Moosmann, de Munck, Scheeringa, Prokopiou's negative parieto-occipital HRFs). The timing agrees with a hemodynamic delay: a canonical-type HRF with a peak near 6 s and FWHM about 4 s covers roughly 4-8 s (see Q4), and EEG-derived HRFs peak around 5-10 s (Mann-Krzisnik). (Inference.)
- **Candidate explanations for the opposite-sign short-lag (0-4 s) term:**
  1. Filter/suppressor or "temporal-derivative" structure. A [+ early, − late] weight pair on an autocorrelated regressor acts like canonical HRF plus a temporal-derivative term, shifting the effective kernel's latency. Rosa 2010 found temporal derivatives significant, and Magri 2012 ties beta to BOLD *latency*. Check whether it vanishes in the Haufe pattern.
  2. Genuine near-zero-lag coupling of low-frequency power, as in Schölvinck 2010's 2-15 Hz band. Or arousal/eye-state dynamics: de Munck 2007's immediate eyeball correlation, and eyes-closed "anticipatory" coupling in Schölvinck. Both could leak through scalp EEG artefacts, such as eye movements or motion that co-occur with BOLD changes.
  3. A thalamic or cingulo-opercular-type positive coupling with an earlier peak (de Munck 2007; Sadaghiani 2010). This would show up mainly in specific DiFuMo components rather than uniformly.
  - These are hypotheses for testing, not established facts. (Inference.)
- **Region dependence of the sign is expected.** Thalamic/insular/cingulo-opercular ROIs may show positive alpha coupling while visual/parietal ROIs show negative. So a pooled "alpha → lower BOLD" summary averages heterogeneous ROI kernels. (Inference from Liu 2012, Sadaghiani 2010, Prokopiou 2020.)
- **Rosa/Leite "relative spectrum" idea.** It implies that log-power features (where relative power is a linear contrast of bins) suit linear models. The ridge can implement an RMSF-like "high minus low frequency" contrast. This should appear as opposite-sign weights between low and high bins at the *same* lag, not across lags. (Inference.)
- **Benchmark for the project.** Mann-Krzisnik & Mitsis's resting-state correlations (about 0.2-0.3, rarely significant per subject) are a realistic external benchmark for scalp-EEG → resting BOLD prediction. (Inference.)

### Gaps
- Exact peak latencies (in seconds) for de Munck 2007's thalamic vs cortical ARFs, Goldman 2002, Moosmann 2003 and Feige 2005 were not retrievable from abstracts. Full texts are needed.
- Sato 2010's method and results were not retrieved.
- I found no "Leite 2013" in Human Brain Mapping. The frequency-specific transfer-function paper by Leite is Front Neurol 2013, and the HBM paper is the Murta 2015 review.
- The Prokopiou study's journal version (possibly Brain Topography) could not be verified, so it is cited as a preprint.
- Mukamel 2005's DOI is listed inconsistently across databases (…1110913 vs …1110948).
- The LFP–fMRI correlation values in Mukamel 2005, and Goense & Logothetis 2008's MUA comparison, were not retrieved.

---

## 4. HRF variability across regions and people, and how much it matters for prediction

### Takeaway
HRF timing varies by a few seconds across people, with smaller (but significant) differences across regions within a person. Within-subject responses are more stable than between-subject ones. A substantial fraction of cortex can show negative responses. Ignoring this variability can distort resting-state connectivity by tens of percent. For a lagged-feature ridge with 12 free lags per feature, region-specific HRFs are absorbed automatically *per ROI*. Subject-specific HRFs are not absorbed when one model is pooled across 22 people.

### Cited Findings
- **Taylor, Kim & Ress 2018** (NeuroImage 173:322-331), 20 subjects aged 20-60 at 3T, brief multisensory stimulation:
  - Positive-HRF time-to-peak **6.1 ± 0.6 s**; FWHM **4.1 ± 0.5 s**; time-to-undershoot **10.8 ± 1.1 s**.
  - Peak amplitude 0.7 ± 0.2%; undershoot −0.15 ± 0.14%.
  - Timing was "relatively stable across the cortical surface" with small but significant regional differences.
  - Of strongly activated cortex, **27 ± 9% showed negative HRFs**.
  - Cross-subject spatial pattern correlation was 0.60 ± 0.06.
  - A double gamma still misses much temporal variability.
  - This is *not* a UK Biobank study; the assignment's "Taylor 2018 UK Biobank HRF" looks like a conflation.
  - — [PMC5911213](https://pmc.ncbi.nlm.nih.gov/articles/PMC5911213/)
- **Aguirre, Zarahn & D'Esposito 1998** (NeuroImage 8:360-369): time-to-peak ranged about **2.7-6.2 s across 32 subjects** and was unrelated to reaction time. Repeated scans of the same ROI in the same subject varied much less than across subjects. — [Frontiers 2009 summary](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/neuro.09.008.2009/pdf) **[secondary; check against original]**
- **Handwerker, Ollinger & D'Esposito 2004** (NeuroImage 21:1639-1651, DOI 10.1016/j.neuroimage.2003.11.029) showed that HRFs vary across subjects and across regions within subjects, and examined how this affects statistical analyses. — [PubMed 15050587](https://pubmed.ncbi.nlm.nih.gov/15050587/); [NIMH FIM listing](https://fim.nimh.nih.gov/publications/handwerker_et_al_2004_0)
- **Rangaprakash, Wu, Marinazzo, Hu & Deshpande 2018** (MRM 80:1697-1713, DOI 10.1002/mrm.27146):
  - In simulations, HRF variability changed functional connectivity by **up to 50%**.
  - In 7T resting data (n = 47), mean/median FC error from HRF confounds was **30.5% / 11.5%**, with false connections mostly between lobes.
  - They recommend deconvolution.
  - A 2023 follow-up reports a 15.4% median error in a sex-difference comparison.
  - — [NITRC PDF](https://www.nitrc.org/docman/view.php/1304/78941/Hemodynamic%20response%20function%20(HRF)%20variability%20confounds%20resting-state%20fMRI%20functional%20connectivity.); [Frontiers 2023, PMC10375034](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10375034/)
- **Wu et al. 2013** (Med Image Anal 17:365-374): blind deconvolution of resting fMRI. It detects spontaneous point-process "events", fits a voxel-wise HRF, and underlies the rsHRF toolbox. — [DOI 10.1016/j.media.2013.01.003](https://doi.org/10.1016/j.media.2013.01.003)
- **Polimeni & Lewis 2021** (Prog Neurobiol 207:102174) argue that fast fMRI needs updated HRF models.
- **Chen et al. 2021** (NeuroImage):
  - Lower-intensity stimuli produce faster, narrower HRFs.
  - Voxel-wise HRFs deviate more from canonical at higher spatial resolution.
  - Lewis et al. 2016 detected 0.75 Hz BOLD oscillations "an order of magnitude larger" than canonical linear models predict.
  - — [MGH listing](https://nmr.mgh.harvard.edu/publications/journal_articles/8129); [DOAJ NeuroImage Dec 2021](https://doaj.org/article/e3d68c6dfff74ac8bd3787b64e8f8612); [ISMRM 2016](https://cds.ismrm.org/protected/16MProceedings/PDFfiles/0760.html)
- **Epilepsy EEG-fMRI**:
  - IED-related BOLD typically peaks about 4-6 s after the spike, but HRFs vary across subjects, regions and spike types.
  - Negative responses are slower than positive ones (Bénar et al. 2002, NeuroImage 17:1182; Bagshaw et al. 2004).
  - Intracranial EEG-fMRI in 11 patients found patient- and location-specific HRFs deviating from canonical.
  - — [PMC6869833 and related summaries via search](https://pmc.ncbi.nlm.nih.gov/articles/PMC6869833) **[secondary]**; [Lemieux UCL](https://discovery-pp.ucl.ac.uk/19134/1/19134.pdf)
- **Regional HRF and prediction in EEG-fMRI**:
  - de Munck 2009: estimating each band's HRF from data has a "large effect" on the resulting maps. — [UvA record](https://www.dare.uva.nl/id/b7151024-b98f-4d70-834e-984824ebb377)
  - Prokopiou 2020: HRF shape "varied considerably across regions" **[preprint]**. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2020.06.29.178483v2)
  - Mann-Krzisnik & Mitsis 2022: region-specific HRFs gave "improved modelling capacity" over canonical in simulation. — [PMC9374895](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374895/)
  - Van Eyndhoven et al. 2021: regions with the most deviant HRFs carried clinical information (see Q5). — [arXiv:2004.14185](https://arxiv.org/abs/2004.14185)

### Inferences
- **What 12 lags of 2 s cover.** They span 0-24 s, which covers peak (about 4-8 s) and undershoot (about 10-16 s) for essentially all reported HRFs. So the ridge does not suffer from HRF-shape misspecification per ROI. This is one reason it is hard to beat. (Inference from Taylor 2018 and Aguirre 1998.)
- **Pooling across subjects.** It forces one kernel per ROI on all 22 people. With subject time-to-peak spread of about 2-3 s (Aguirre), the pooled kernel is a blurred average. This predicts smoother, wider weights than any individual and a cost to cross-subject prediction. A test: fit per-subject kernels, or a shared spectral/spatial profile with subject-specific lag profiles (Q5), and compare held-out R². (Inference.)
- **Vascular confound.** Region-to-region HRF differences mean that differences in *lag* of the alpha kernel across ROIs cannot be read as neural timing differences (de Munck 2007 makes this point themselves). (Inference.)

### Gaps
- Handwerker 2004's numeric ranges (time-to-peak spread across subjects and regions; false-negative rates under canonical HRF) were not retrieved.
- Aguirre 1998's 2.7-6.2 s figure is from a secondary summary.
- I found no UK Biobank HRF characterisation paper by "Taylor 2018". If the advisor meant a specific UKB HRF paper, it still needs to be identified.
- I found no study that directly quantifies how much held-out EEG→BOLD prediction accuracy is lost by ignoring subject-specific HRFs.

---

## 5. Low-rank / separable (channel x spectrum x lag) models in EEG-fMRI: interpretability and predictive performance

### Takeaway
Multiway/tensor models were adopted mainly for *interpretability*. They yield a small number of "atoms", each with one spatial, one spectral and one temporal/HRF signature. The classic results (Martinez-Montes 2004: an alpha atom with parieto-occipital, thalamic and insular loadings; Van Eyndhoven 2021: region-specific Toeplitz HRFs that localise epileptic onset) were interpretable and physiologically plausible. Reported predictive gains over conventional EEG-informed fMRI are modest or not quantified, and resting-state predictive accuracy has been low.

### Cited Findings
- **Martinez-Montes et al. 2004** (NeuroImage 22:1023-1034; corrigendum 2005):
  - N-PLS with EEG (space x frequency x time) as predictor and fMRI as response. Each EEG atom is an outer product of spatial, spectral and temporal signatures.
  - Three atoms emerged (theta, alpha, gamma peaks); **only the alpha atom's time course correlated significantly with fMRI**.
  - Its fMRI map (parieto-occipital, thalamus, insula) "matched closely" Goldman 2002.
  - — [PubMed 15219575](https://pubmed.ncbi.nlm.nih.gov/15219575); [PDF](https://web-mit-edu.ezproxyberklee.flo.org/swg/ImagingPubs/Multimodal%20Imaging/Martinez04.pdf)
  - A later review states the atom's spatial signature is positive in thalamus and negative in visual cortex. — [arXiv:1506.06040](https://arxiv.org/pdf/1506.06040) **[secondary]**
- **Van Eyndhoven, Dupont, Tousseyn, Vervliet, Van Paesschen, Van Huffel & Hunyadi 2021** (NeuroImage, DOI 10.1016/j.neuroimage.2020.117652):
  - Coupled matrix-tensor factorisation of an EEG spectrogram tensor (channel x frequency x time) and a BOLD matrix.
  - The shared temporal mode uses **Toeplitz-structured factors = region-specific HRFs** (a spatially specific "neurovascular bridge").
  - Results in 12 epilepsy patients: sensitive ictal-onset-zone localisation in 10/12. In 9/12, the regions with the most deviant HRF waveforms (two entropy-like metrics) revealed complementary parts of the onset zone.
  - — [arXiv:2004.14185](https://arxiv.org/abs/2004.14185); [KU Leuven thesis](https://theses.eurasip.org/document/tensor-based-blind-source-separation-for-structured-eeg-fmri-data-fusion/)
- **Mann-Krzisnik & Mitsis 2022** (HBM 43:4045-4073):
  - CPD of an impulse-response tensor (node x band x HRF-time in simulation; time x SOBI-component x frequency x subject in data), with Laguerre-basis HRFs per BOLD component.
  - Spectral profiles were mostly broadband and smooth. One component had a strong 16 Hz weighting; others were broadband in motor/somatosensory cortex.
  - Motor-imagery HRFs peaked at 5-10 s.
  - **Predictive accuracy was modest:** motor imagery r = 0.30-0.37 (up to 0.44 with 2 components); rest r = 0.19-0.32, with almost no single-subject significance (0-3%).
  - — [PMC9374895](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374895/)
- **Prokopiou et al. 2020** "block-structured" models, HRF ⊛ (Σ_b β_b · power_b), are an explicitly rank-1 band x lag model per region (see Q3 for findings) **[preprint]**. The same group also proposed HRF estimation by convolutional sparse coding with **rank-1 constraints** **[preprint]**. — [bioRxiv 2020.06.29.178483](https://www.biorxiv.org/content/10.1101/2020.06.29.178483v2); [bioRxiv 2020.09.09.290296](https://www.biorxiv.org/content/10.1101/2020.09.09.290296v1.full.pdf+html)
- **Deligianni et al. 2014** (Front Neurosci) related EEG and fMRI connectomes across bands. Their resting dataset (11 subjects, TR 2.16 s) is the one Mann-Krzisnik & Mitsis decomposed. — dataset description in [PMC9374895](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374895/)
- **Banded ridge** (Dupré la Tour 2022) is a different "structured" route: grouped penalties rather than low rank. It improved prediction and interpretability in voxelwise encoding by suppressing redundant feature spaces. — [PMC9807218](https://pmc.ncbi.nlm.nih.gov/articles/PMC9807218/)

### Inferences
- **Parameter count.** A rank-R CP (separable) version of the current ridge kernel W[channel, freq, lag] ≈ Σ_r a_r ∘ b_r ∘ c_r has R·(26 + 44 + 12) = 82R parameters per ROI, versus 13,728. A rank-1 model *is* the classic "spatial filter x spectral weighting x HRF" EEG-informed-fMRI model with a free HRF. (Inference.)
- **A direct test.** Compare held-out R² of the full ridge, rank-1, rank-2 and rank-3 CP regressions, or a partially separable "spectrum x lag" model with free channel weights. This tests whether the ridge's opposite-sign short-lag lobe is needed. If rank-1 or rank-2 matches ridge, the advisor-ready story is "one spectral profile (alpha/beta, negative) x one HRF-like lag profile x one scalp topography", which is directly comparable to Martinez-Montes 2004 and Prokopiou 2020. (Inference.)
- **Second component.** If a rank-2 model needs a second component with a short-lag, opposite-sign lag profile and a frontal/ocular topography, that would point to the artefact or arousal explanation in Q3. A posterior topography with an early peak would point toward thalamic-type coupling. (Inference.)
- **Pooling with subject-specific lags.** Coupled or shared-factor models (one spectral/spatial profile shared across subjects, subject-specific lag profiles) are the natural way to pool 22 subjects while allowing HRF variability (Q4). Van Eyndhoven's Toeplitz-HRF idea is the region-wise analogue. (Inference.)

### Gaps
- I did not retrieve quantitative predictive comparisons (separable vs unstructured, or vs canonical-HRF regressors) on real data from Martinez-Montes 2004 or Van Eyndhoven 2021. Their results are reported as localisation/interpretability outcomes rather than held-out BOLD prediction.
- I did not retrieve details of Deligianni et al.'s own tensor or fusion results, or any 2023-2026 paper benchmarking low-rank EEG→BOLD regression against deep models such as NeuroBOLT.
