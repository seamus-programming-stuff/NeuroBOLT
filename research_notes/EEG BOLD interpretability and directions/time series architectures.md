# Time-series architectures and training strategies for small-cohort cross-subject EEG-to-BOLD prediction

Scope note: this note covers literature from 2023 to October 2026, plus older foundational methods. Reproduction context: 22 people, 29 resting scans, 26 channels. Ridge on lagged log power (1 Hz x 24 s) reached mean R 0.381, against 0.336 for NeuroBOLT, in subject-grouped 5-fold CV. Preprints are flagged [PREPRINT]. Where a number came from automated extraction of a paper's HTML and not from reading the paper directly, it is flagged "(extracted)". Citations marked "(URL not re-fetched)" are standard references given from prior knowledge so the writer can locate them. They support descriptions of methods only, never numbers.

Previously covered items, one line each. I found nothing new about small-data overfitting for any of them in this pass:
- UnEBOLT (MIDL 2026): no indexed page found by my searches, so I have nothing new on it.
- MARBLE (MICCAI 2026): the only trace I found is a self-reported LinkedIn acceptance post. It describes a hybrid Mamba-Transformer with a cross-attention ROI decoder whose attention maps rank EEG channels per ROI. There is no paper text, so I can say nothing about overfitting. — [LinkedIn post](https://kr.linkedin.com/in/emeelkaa)
- REVE, CBraMod, TFM-Tokenizer, CATD, EEG-FM-Bench, NATVIEW: not re-summarised. See the small-data evidence on EEG foundation models in section 5.

---

## 1. New EEG-to-fMRI / EEG-to-BOLD papers (2024–2026) beyond those already covered

### Takeaway
The most important new paper is MEL [PREPRINT, Aug 2026]. It uses the same VU dataset (22 subjects, 29 scans, 26 channels) with leave-one-subject-out evaluation. It found that a ridge on a z-scored lag x channel x band log-bandpower cube beats a uniform-STFT lag-band ridge (0.439 vs 0.382 avg R). A small MLP ensemble on that cube beat both ridge and NeuroBOLT (0.499 vs 0.473). This is the only direct evidence in this exact dataset that a nonlinear readout on lagged band power beats ridge cross-subject, and it reports no significance tests. Elsewhere, the reported deep-vs-linear gains are mixed. Herzog 2026 has deep learning beating linear in leave-one-out (0.323 vs 0.213, n=19). R-EEGNet only matched Group Lasso. Several others report no linear baseline at all.

### Cited Findings

**MEL: Coordinate-Preserving EEG Tokenization for fMRI Translation** (Liu, Yan, Yin, Li, Zhang; arXiv 2608.29304, v1 29 Aug 2026) [PREPRINT]
- Data: the VU EEG-fMRI dataset used by NeuroBOLT, 29 scans from 22 subjects, with OpenNeuro ds000116 Oddball for transfer and NODDI as a stress test. Targets are 7 ROIs: cuneus, Heschl's, anterior middle frontal, anterior precuneus, putamen, thalamus, global signal. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Protocol: both intra-scan and strict leave-one-subject-out inter-subject splits. Normalization, checkpoint selection and ridge penalties use training/validation data only. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Representation: 16 s of pre-target EEG in 2 s lag bins (8 lags) x 26 channels x 5 canonical bands (delta to gamma), giving a 1,040-dim log-bandpower cube. It is z-scored with train-only statistics and flattened. Readouts are ridge (31 log-spaced penalties chosen per target) or a "compact" MLP trained with seeds 1–5 and ensembled. MLP width and depth are not reported. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Inter-subject avg R: NeuroBOLT 0.473, BIOT 0.435, uniform STFT lag-band + ridge 0.382, MEL-ridge 0.439, MEL-MLP 0.488, MEL-MLP 5-seed ensemble 0.499. Intra-scan avg R: NeuroBOLT 0.531, LaBraM 0.484, BIOT 0.473, uniform STFT + ridge 0.455, MEL-ridge 0.452, classical lagged bandpower + ridge 0.431, MEL-MLP 0.524, MEL-MLP ensemble 0.543. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Per-ROI, inter-subject: the MEL ensemble is below NeuroBOLT on cuneus (0.440 vs 0.482) and Heschl's gyrus (0.377 vs 0.561). Across-target SDs are about 0.2–0.3. No significance tests are reported. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Ablations (ridge, avg R): time-mean aggregation 0.292; canonical HRF-weighted aggregation 0.325; lag coordinates with 3 bands 0.407; lag coordinates with 5 bands 0.452. 2 s bins were best, and the 5–11 s lag range was the strongest restricted range. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- Validity controls (avg R): normal 0.452; channel permutation 0.395; band reversal 0.236; random lag 0.198; lag reversal 0.102; label or target shuffle about 0. With the same MLP protocol, classical lagged bandpower and STFT features "drop substantially". No numbers are given for this. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)

**Herzog et al., "From surface to depth: Using deep learning to predict striatal fMRI reward signaling from EEG"** (Imaging Neuroscience 4, 2026, doi 10.1162/imag.a.1160; OSF preprint 2024)
- A convolutional autoencoder reconstructs ventral-striatum BOLD from EEG during a two-choice gambling task. It was trained on 19 healthy participants and validated leave-one-out. Mean r was 0.323 for deep learning vs 0.213 for a linear baseline. The authors call generalization "modest". Informative EEG features were theta to beta, at right centroparietal, temporal and frontal electrodes. — [Europe PMC record](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:41816006&resultType=core&format=json); [PubMed](https://pubmed.ncbi.nlm.nih.gov/41816006/)

**R-EEGNet** (EUSIPCO 2025, "Deep Learning prediction of BOLD-fMRI signals from ...")
- EEGNet adapted to regress one fMRI time point from a 15 s EEG window. It was subject-specific only: 15 healthy subjects doing motor imagery. Performance was similar to Group Lasso, and both beat a naive model. I could not parse the PDF, so I have no numbers. — [EUSIPCO 2025 PDF](https://eusipco2025.org/wp-content/uploads/pdfs/0001025.pdf)

**Mehta, Goncalves, ..., Grover, Figueiredo, "EEG-to-fMRI synthesis of task-evoked and spontaneous brain activity: addressing issues of statistical significance and generalizability"** (arXiv 2504.10752, v2 Jan 2026) [PREPRINT]
- Subject-specific distributed-lag linear models on multichannel EEG spectral power, fit with sparse group lasso, predicting the somatomotor network. They beat null models in most subjects and conditions, but less often for spontaneous activity. Prediction degrades when train and test come from different sessions. The authors argue that temporally separated train/test splits are needed to avoid leakage and optimistic bias. — [arXiv abs](https://arxiv.org/abs/2504.10752)

**Semenkov, Rudych, Ossadtchi, "Beyond the Surface: Revealing the Depths of Brain Activity by Predicting fMRI from EEG with Deep Learning"** (bioRxiv 2024.11.20.624528; an ECAI 2024 "digital twin" version exists) [PREPRINT]
- A lightweight, subject-specific network predicts BOLD in 7 bilateral subcortical structures. Targets are expressed relative to mean hemodynamic activity, explicitly to avoid inflated scores from common-mode, likely non-neuronal signal. Performance is reported as significantly above chance. Sensorimotor cortex contributed most, and the thalamus had the shortest hemodynamic delay. No linear baseline is mentioned in the abstract. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2024.11.20.624528v1)

**Donoso, "Neural networks and foundation models: two strategies for EEG-to-fMRI prediction"** (Frontiers in Systems Biology 5:1715692, Dec 2025; bioRxiv 2025.05.06.652346)
- OpenNeuro ds002336 (motor-imagery neurofeedback). 9 usable subjects x 49 Harvard-Oxford regions, within-subject cross-session. For regression, only RF (r = 0.145) and SVM (r = 0.175) beat a predict-zero baseline. Unregularised linear regression and all NNs (MLP, CNN, GRU, transformer) did not. LLMs (Gemma-2-2B, Llama-3.2-3B, PaliGemma2) did not beat baseline on the classification task. No ridge baseline was run. — [PMC12753390](https://pmc.ncbi.nlm.nih.gov/articles/PMC12753390/)

**E2fNet** (Roos, Fukuda, Cap; arXiv 2502.08025, Feb 2025) [PREPRINT]
- Spectrogram EEG encoder, then a U-Net, then an fMRI volume decoder. Evaluated on NODDI, Oddball and CN-EPFL with SSIM against volumes. It beats CNN baselines and the NT-ViT transformer on SSIM. This is volumetric image synthesis, not ROI time-course correlation, and there is no linear baseline. — [arXiv](https://arxiv.org/abs/2502.08025v2)

**SAMBA, "Latent Representation Learning for Multimodal Brain Activity Translation"** (Afrasiyabi, ..., Turk-Browne, Krishnaswamy; ICASSP 2025; arXiv 2409.18462)
- Attention-based wavelet decomposition of electrophysiology, graph attention over functional units, and recurrent layers into a shared latent space for EEG to fMRI. I did not obtain its numbers or baselines. — [arXiv PDF](https://arxiv.org/pdf/2409.18462)

**Calhas & Henriques line (INESC-ID / IST Lisbon)**
- 2020 [PREPRINT]: compared autoencoders, GANs and pairwise learning for EEG-to-fMRI synthesis and argued feasibility. — [alphaXiv 2009.14133](https://alphaxiv.org/abs/2009.14133)
- MLHC 2023 (PMLR 219): attention graphs over electrode relationships, Fourier features, a shared latent space and latent style. Reported to beat prior state of the art on resting-state and task data. I did not find a ridge baseline. — [PMLR](https://proceedings.mlr.press/v219/calhas23a.html)
- Calhas PhD thesis (2023), "EEG to fMRI Synthesis". — [IST record](https://scholar.tecnico.ulisboa.pt/records/ybSGXY8KpnLLL5Rg1xUl0JLbIq5n-rYA04v6)
- medRxiv 2023 [PREPRINT]: synthesis plus a contrastive loss to classify schizophrenia. — [medRxiv](https://www.medrxiv.org/content/10.1101/2023.08.07.23293748v1)

**Chang-lab (Vanderbilt) related items**
- Li, Lou, Xu, Wang, Chang (SPIE Medical Imaging 2024, vol. 12926, pp. 795–800): sinusoidal representation networks (SIREN) to predict fMRI from EEG. This is the NeuroBOLT precursor, cited in NeuroBOLT's reference list. — [NeuroBOLT arXiv](https://arxiv.org/pdf/2410.05341)
- NeuroBOLT arXiv v3 (Sept 2025) uses 20 s gaps between train, validation and test to limit autocorrelation leakage. Its resting-state inter-subject split randomly divides subjects. — [NeuroBOLT arXiv](https://arxiv.org/pdf/2410.05341)
- CBrain (MICCAI 2025, Chang co-author): cross-modal learning to detect vigilance states from resting-state fMRI. This is fMRI-side, not EEG-to-BOLD. — [MICCAI 2025 paper 4486](https://papers.miccai.org/miccai-2025/paper/4486_paper.pdf)
- I found no Kumar or Song EEG-to-BOLD follow-up from the Chang lab.

**Inverse direction (fMRI to EEG), with a direct linear vs nonlinear comparison**
- Jacob, Bailes, Williams, Stringer, Lewis (PLoS Comput Biol 21(9):e1013497, 2025). 32 subjects in two fast-TR datasets, leave-one-subject-out. Ridge predicted occipital EEG power from 60-TR parcel fMRI windows: brainwide alpha r = 0.30 and delta r = 0.41 on held-out subjects, rising to 0.46 and 0.45 after region selection. Recurrent and temporal-convolution networks were explored and "performance was not significantly better", so the linear model was kept. — [PMC12459787](https://pmc.ncbi.nlm.nih.gov/articles/PMC12459787/)

**Learned-HRF EEG-fMRI "transcoding"** (arXiv 2010.02167; arXiv 2212.02226; NeurIPS 2021 "Fusing simultaneously acquired EEG and fMRI via hierarchical deep transcoding")
- The fMRI encoder learns the HRF from data rather than fixing it. Impulse probes recover an initial dip, peak and undershoot that match the canonical HRF in timing but show clear between-subject differences. — [arXiv 2010.02167](https://arxiv.org/pdf/2010.02167); [arXiv 2212.02226](https://arxiv.org/pdf/2212.02226); [NeurIPS 2021](https://nips.cc/virtual/2021/36818)

**Diffusion-based EEG-to-fMRI image generation**
- "Research on fMRI Image Generation from EEG Signals Based on Diffusion Models" (Electronics 2025). Found but not inspected. — [doi 10.3390/electronics14224432](https://doi.org/10.3390/electronics14224432)

### Inferences
- MEL's "uniform STFT lag-band + ridge" inter-subject R (0.382) is almost identical to this reproduction's ridge (0.381). Its NeuroBOLT inter-subject figure (0.473) is much higher than the reproduced 0.336. That fits a protocol difference: LOSO vs grouped 5-fold, 16 s vs 24 s history, and possibly NeuroBOLT's own reported numbers reused instead of a re-run. The gap is worth checking before treating MEL's NeuroBOLT number as a target.
- MEL suggests two cheap, testable changes to the existing ridge:
  - Aggregate 1 Hz bins into canonical bands and 2 s lag bins. For ridge, MEL's cube beat the uniform STFT grid inter-subject (0.439 vs 0.382), though not intra-scan.
  - Put a small MLP ensemble on the same z-scored cube. This gave +0.05 to +0.06 R over ridge inter-subject.
  - Both need a paired per-subject test. MEL reports none, and its per-ROI SDs are large.
- MEL's ablation found that free lag coordinates beat canonical-HRF weighting (0.452 vs 0.325). Imposing a fixed double-gamma HRF on band power is therefore likely to hurt relative to the free FIR that the lagged ridge already learns.
- Channel permutation cost only about 0.06 R, while lag or band scrambling cost 0.2–0.35. Most usable signal is band x lag, not fine spatial topography. That is consistent with the pretrained spatial transformer branch (LaBraM) adding nothing in this reproduction.
- In the deep vs linear EEG-BOLD results, a deep model beat linear when the linear baseline was weak or unspecified (Herzog's linear model is not described in the abstract; Donoso used unregularised OLS). When a tuned regularised linear model was used, deep models matched rather than beat it (R-EEGNet vs Group Lasso; Jacob et al. ridge vs RNN/TCN).

### Gaps
- MEL: MLP size, the per-subject distribution of R, and any significance test. Also whether its NeuroBOLT numbers were re-run under LOSO. These need the full PDF.
- Herzog 2026: exactly what the linear baseline was (features, regularisation, lags). Not in the abstract.
- R-EEGNet: numeric results. The PDF did not parse.
- Mehta et al.: dataset name, n, and effect sizes. Abstract only.
- No paper found under the names "EEG2fMRI" or "BrainWave" doing EEG-to-BOLD. BrainWave appears to be an EEG foundation model for clinical tasks; not verified this session.
- UnEBOLT and MARBLE full texts were not locatable.

---

## 2. Linear vs nonlinear encoding/decoding models in neuroscience: when nonlinearity helped

### Takeaway
Nonlinear models reliably beat linear ones in two situations. The first is a large aggregate training set (tens of subjects, many hours), as in VLAAI speech-envelope decoding (+52% over linear). The second is a nonlinear readout on a good hand-built representation (MEL; Algonauts transformer fusions). In small cohorts, in noisy whole-brain phenotype prediction, and in fMRI-EEG coupling studies, regularised linear models are usually at parity. Recent large benchmarks (Algonauts 2025; Schulz et al. 2020) say architecture matters far less than features and ensembling. Banville et al. 2025 say the deep-learning gain over linear is largest for noisy modalities such as EEG, and that it scales with data per subject, not with the number of subjects.

### Cited Findings
- **VLAAI (Accou et al., Sci Rep 13:812, 2023).** Subject-independent EEG speech-envelope decoder, median Pearson r = 0.19, a 52% increase over the linear decoder. The nonlinear components and output-context module gave about a 10% relative gain in ablation. Performance rose along a tanh curve as training subjects increased from 1 to 80 (tested on 26 held-out subjects). Fine-tuning to an individual with 5 or more minutes of data gave up to +34% (median 0.18 to 0.25). — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41598-022-27332-2&resultType=core&format=json); [Nature](https://www.nature.com/articles/s41598-022-27332-2)
- **Keshishian et al. (eLife 2020).** DNN models of ECoG auditory responses to speech significantly improved prediction over linear STRFs, particularly in nonprimary areas. Recasting the DNN as stimulus-dependent linear functions (dSTRF) recovered interpretability. I did not retrieve the exact gain. — [eLife PDF](https://elifesciences.org/articles/53445.pdf)
- **Algonauts 2025 (multimodal movies, about 80 h of fMRI per subject).** The linear baseline scored r = 0.20 in-distribution and 0.09 out-of-distribution. — [Challenge paper, arXiv 2501.00504](https://arxiv.org/pdf/2501.00504)
- **Insights from the Algonauts 2025 winners** [PREPRINT]. 2nd place VIBE scored 0.2125 and 3rd place SDA 0.2094. 4th place MedARC used only 1D temporal convolution plus a linear projection, with no nonlinearities, and says one more hour would have given 0.2117 (second place). The authors conclude architecture "didn't really matter" and that ensembling (20 to hundreds of models, per-parcel weighting) decided the ranking. TRIBE (Meta, 1st) reports sub-linear, plateauing gains with data up to about 80 h per subject. — [arXiv 2508.10784](https://arxiv.org/html/2508.10784v1)
- **Schulz et al. (Nat Commun 11:4238, 2020).** On UK Biobank brain images, linear models matched kernel and deep models for age and sex prediction across sample sizes, and kept improving up to about 10,000 subjects. On MNIST-type benchmarks, deep models pulled ahead. — [PMC7447816](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7447816/)
- **Banville et al. (arXiv 2501.15322, 2025)** [PREPRINT]. Image decoding over 8 datasets, 84 volunteers and 498 h across EEG, MEG, 3T and 7T fMRI. "The gain enabled by deep learning - in comparison to linear models - is obtained with the noisiest devices". Scaling "primarily depends on the amount of data per subject", and "little decoding gain is observed by increasing the number of subjects". — [arXiv abs](https://arxiv.org/abs/2501.15322)
- **Jacob et al. (PLoS Comput Biol 2025), fMRI to EEG power, n = 32, LOSO.** RNN and TCN were no better than ridge (details in section 1). — [PMC12459787](https://pmc.ncbi.nlm.nih.gov/articles/PMC12459787/)
- **Herzog et al. (Imaging Neurosci 2026), EEG to VS BOLD, n = 19, LOSO.** Deep learning 0.323 vs linear 0.213. — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:41816006&resultType=core&format=json)
- **MEL (2026)** [PREPRINT]. Same tokens, VU data, LOSO: MLP ensemble 0.499 vs ridge 0.439. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- **Ivanova et al. (NBDT 2022).** Most cognitive-neuroscience studies use linear mapping models. The choice should follow the goal (predictive accuracy, interpretability, biological plausibility). Linear maps ease comparison of feature sets and per-feature interpretation. — [arXiv 2208.10668](https://arxiv.org/pdf/2208.10668)
- **Banded ridge (Dupré la Tour, Eickenberg, Nunez-Elizalde, Gallant; NeuroImage 264:119728, 2022).** Separate ridge penalties per feature space act as feature-space selection: uninformative or redundant spaces are shrunk out, improving prediction and interpretability. Implemented in the Python package Himalaya. — [PMC9807218](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9807218/); [Gallant lab tutorial](https://gallantlab.org/voxelwise_tutorials/notebooks/shortclips/09_fit_banded_ridge_model.html)
- **Foundational mTRF references:** the mTRF toolbox (Crosse et al., Front Hum Neurosci 2016) and the applied-methods review (Crosse et al., Front Neurosci 2021). — [doi 10.3389/fnhum.2016.00604](https://doi.org/10.3389/fnhum.2016.00604); [doi 10.3389/fnins.2021.705621](https://doi.org/10.3389/fnins.2021.705621) (URLs not re-fetched)

### Inferences
- The reproduction's ridge learning curve plateaus at about 9 training people. That matches Banville et al. (adding subjects helps little; per-subject data drives scaling) and the saturating tanh curve in VLAAI. Collecting more people is unlikely to unlock a deep model. Longer recordings per person, or more scans per person, would help more.
- The VLAAI-style +52% came with about 80 training subjects and a backward (EEG to stimulus) task with a much richer target. That regime is far from 22 people predicting a slow BOLD signal. The closer analogues (Jacob, R-EEGNet, Schulz) show parity.
- The best single bet for nonlinearity is a small, heavily regularised, seed-ensembled MLP on top of the same lagged band-power features (MEL, Algonauts MedARC-style simplicity plus ensembling). An end-to-end raw-EEG network is a worse bet. Banded ridge (per band or per lag-block penalties) is a zero-risk linear upgrade to try first.

### Gaps
- No study found that compares ridge, MLP and deep sequence models head-to-head on EEG-to-BOLD with paired per-subject statistics in a cohort of 30 or fewer people.
- Exact effect size for Keshishian et al. not retrieved.

---

## 3. Sample-efficient sequence models: SSMs, TCNs, learnable filterbanks, HRF layers, DLinear/RLinear

### Takeaway
For forecasting, single affine layers (DLinear, RLinear) match or beat transformers, which supports linear lag models as strong baselines. EEG Mamba and SSM papers (State Mamba, EEGM2, FEMBA) target long-sequence, cross-domain or foundation-model settings and report no small-cohort regression evidence. Learnable filterbanks (EEGNet, SincNet, FBCNet) are the most sample-efficient deep options, but in EEG-to-BOLD R-EEGNet only matched Group Lasso. Learned-HRF layers exist (transcoding models), but MEL's ablation shows that a free lag basis beats canonical-HRF weighting.

### Cited Findings
- **DLinear/LTSF-Linear (Zeng et al., "Are Transformers Effective for Time Series Forecasting?", AAAI 2023, arXiv 2205.13504).** One-layer linear models outperform the sophisticated transformer-based long-term forecasting models on all 9 real-world benchmarks. The abstract describes the margin as often large but does not quantify it. — [arXiv abs](https://arxiv.org/abs/2205.13504)
- **RLinear (Li, Qi, Li, Xu; arXiv 2305.10721; journal version in Academia AI and Applications 2(2), 2026).** A single linear (affine) layer is competitive, and affine mapping "dominates forecasting performance" on common benchmarks. Reversible normalization significantly helps trend forecasting. Affine maps struggle with channels whose periods differ. — [arXiv abs](https://arxiv.org/abs/2305.10721)
- **State Mamba (AAAI 2026).** Spatiotemporal EEG state-space model with self-supervised alignment of representations and transitions across subjects. Evaluated on FACED, DEAP and ISRUC classification. No small-data regression evidence. — [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/38843)
- **EEGM2 (arXiv 2502.17873, 2025)** [PREPRINT]: Mamba-2 self-supervised framework for long-sequence EEG with claimed SOTA cross-domain accuracy on 6 datasets. **FEMBA (arXiv 2502.06438)** [PREPRINT]: bidirectional Mamba foundation model for efficiency in long-term monitoring. — [EEGM2](https://arxiv.org/html/2502.17873v1); [FEMBA](https://arxiv.org/abs/2502.06438v2)
- A 2026 Mamba-2 EEG affect-decoding poster stresses subject-disjoint evaluation, because models otherwise memorise subject signatures. — [poster PDF](https://axion.pwr.edu.pl/uploads/oscillate-mcsb-2026-poster.pdf)
- **R-EEGNet (EUSIPCO 2025).** EEGNet's depthwise temporal and spatial filters adapted to BOLD regression: roughly equal to Group Lasso, within-subject, n = 15. — [EUSIPCO PDF](https://eusipco2025.org/wp-content/uploads/pdfs/0001025.pdf)
- **Learned HRF.** The transcoding models learn subject-specific HRFs from data, with a canonical-like shape and between-subject variation. — [arXiv 2212.02226](https://arxiv.org/pdf/2212.02226). In MEL, HRF-weighted aggregation scored 0.325 vs 0.452 for free 2 s lag coordinates (ridge, avg R). — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- A Lisbon master's thesis (5 epilepsy patients) found a linear combination of band powers without a predefined HRF was consistently the best EEG-to-BOLD predictor. — [IST thesis record](https://scholar.tecnico.ulisboa.pt/records/8eZN1sanyvnes1GgypOO76MCihkCizfJE48j)
- **Foundational architectures (methods only, URLs not re-fetched):**
  - EEGNet, compact depthwise or separable conv: [arXiv 1611.08024](https://arxiv.org/abs/1611.08024)
  - SincNet, parametrised band-pass first layer: [arXiv 1808.00158](https://arxiv.org/abs/1808.00158)
  - FBCNet, filter-bank plus variance layer: [arXiv 2104.01233](https://arxiv.org/abs/2104.01233)
  - TCN (Bai et al. 2018): [arXiv 1803.01271](https://arxiv.org/abs/1803.01271)
  - S4: [arXiv 2111.00396](https://arxiv.org/abs/2111.00396)
  - Mamba: [arXiv 2312.00752](https://arxiv.org/abs/2312.00752)

### Inferences
- The existing lagged ridge already is a DLinear/ARX-style model: a distributed-lag linear filter on log band power. The forecasting literature says such models are hard to beat without large data.
- The sensible "deep" variants are thin, structured extensions of that model:
  - (a) a FBCNet- or SincNet-style learnable band-pass front end feeding log-variance into the same lag-linear head, so the bands are learned instead of fixed at 1 Hz;
  - (b) a low-rank factorised lag x band x channel head with a shared temporal kernel per band, essentially a learned per-band HRF;
  - (c) a small MLP on the lag cube.
  - Note: low-rank tensor regression already underperformed ridge here, so (b) needs care. A softer prior (banded or smoothness penalties) may be better than a hard rank constraint.
- SSM/Mamba advantages (long context, linear-time) are not binding here. 24 s at 1 Hz bins is a short sequence.

### Gaps
- I found no EEG-to-BOLD paper using S4 or Mamba, apart from the unverifiable MARBLE post. I also found no small-cohort regression benchmark of EEG Mamba models.
- No published EEG-to-BOLD use of SincNet or FBCNet front ends was found.

---

## 4. Frontier-lab time-series foundation models (TimesFM, Chronos, Moirai, Lag-Llama) and OpenAI/Anthropic

### Takeaway
Current time-series foundation models (TSFMs) are poorly matched to EEG-to-BOLD, which is a lagged-covariate (system-identification) regression problem. TimesFM-2.5 handles covariates by linear regression of residuals (XReg), and that interface is "memoryless". Chronos-2 does learn input dynamics in context but attenuates them to 0.33–0.80 of the true effect. A 256-sample ARX beats it. The more relevant frontier tool is TabPFN-2.5, a tabular in-context regressor for up to 50k rows and 2k features, applicable to PCA-reduced lagged band power. I found no relevant OpenAI or Anthropic release.

### Cited Findings
- **Chronos-2 (Amazon, arXiv 2510.15821, Oct 2025)** [PREPRINT]. Group attention enables in-context learning across related series and covariates (past-only or known-future, real or categorical). It is trained on synthetic multivariate data. Self-reported SOTA on fev-bench, GIFT-Eval and Chronos Benchmark II, with large margins on covariate tasks. — [arXiv](https://arxiv.org/html/2510.15821v1); [Amazon Science blog](https://www.amazon.science/blog/introducing-chronos-2-from-univariate-to-universal-forecasting)
- **TimesFM 2.5 (Google Research).** 200M parameters, context up to 16k, LoRA fine-tunable. Covariates are supported through XReg, which regresses TimesFM residuals linearly on the covariates. In-context fine-tuning (TimesFM-ICF) claims up to 25% gains on benchmarks, but I could not confirm it ships in the public 2.5 checkpoint. — [TimesFM docs (Algolia mirror of google-research/timesfm)](https://docsearch.algolia.com/mcp/docs/repo/google-research/timesfm); [electricity-price paper describing XReg, arXiv 2609.00089](https://arxiv.org/pdf/2609.00089)
- **Won, "Attenuated in-context identification in time-series foundation models" (arXiv 2610.08118, 6 Oct 2026)** [PREPRINT, single author].
  - Through their default covariate interfaces, TimesFM-2.5 and TabPFN-TS are memoryless: the predicted effect of an input change depends only on the same-time change (R² = 1.000 for TimesFM-2.5).
  - Chronos-2 identifies dynamics but predicts 0.33–0.80 of the true effect with a wrong-shaped impulse response. On a 1-DOF oscillator its error plateaus at 0.57 even with 8,192 context samples, while an ARX fitted to 256 samples reaches 0.02.
  - Synthetic forced-system fine-tuning (26 min) restores sensitivity to 0.83–0.96. Classical system ID still wins on 3 of 4 measured plants.
  - [arXiv abs](https://arxiv.org/abs/2610.08118)
- **TabPFN-2.5 (Prior Labs, arXiv 2511.08667, Nov 2025)** [tech report]. Built for up to 50,000 rows and 2,000 features. Reports a 100% win rate vs default XGBoost on small/medium classification (≤10k rows, ≤500 features) and 85% for regression on larger datasets (up to 100k rows and 2k features). The model card says it is untested beyond 50k samples or 2k features. — [arXiv](https://arxiv.org/pdf/2511.08667); [HF model card](https://huggingface.co/Prior-Labs/tabpfn_2_5)
- **TSFMs on physiological data.** A 2026 preprint found TimesFM, Chronos and Moirai zero-shot beat simple baselines for HRV forecasting in 49 people (MASE 0.81–0.87; Moirai gained least). This is forecasting, not cross-modal regression. — [arXiv 2607.20027](https://arxiv.org/html/2607.20027) [PREPRINT]
- **MOMENT as a frozen EEG temporal extractor (arXiv 2606.30104, Jun 2026)** [PREPRINT]. Compared a linear baseline, a CNN and frozen MOMENT inside an EEG foundation model. Simple temporal representations were competitive on motor imagery. Emotion recognition benefited from richer temporal modelling. MOMENT was an effective frozen extractor. — [arXiv abs](https://arxiv.org/abs/2606.30104)
- **Benchmark of probabilistic forecasters on mouse widefield neural activity (arXiv 2510.18037; NeurIPS 2025 workshop)** [PREPRINT]. Several deep models, including 2 foundation models, "consistently outperformed classical approaches", with informative forecasts up to 1.5 s ahead. This is autoregressive forecasting, not cross-modal regression. — [arXiv abs](https://arxiv.org/abs/2510.18037)
- **Moirai and Lag-Llama.** No EEG or neural cross-modal regression evidence found in this pass. MIRA notes that Moirai, TimesFM and Chronos need interpolated, regular inputs. — [MIRA arXiv 2506.07584](https://arxiv.org/html/2506.07584v7)
- **OpenAI / Anthropic.** A search found no time-series or neural-data forecasting model released by either. They appear only as LLM back-ends in agentic forecasting frameworks such as TimeCopilot. — [arXiv 2509.00616](https://arxiv.org/html/2509.00616v1)

### Inferences
- EEG-to-BOLD is essentially exogenous-input system identification with an HRF-scale lag of about 4–10 s. The one direct diagnostic of TSFM covariate handling (Won 2026) says these models either ignore lags (TimesFM-2.5 XReg, TabPFN-TS) or under-estimate them (Chronos-2), while a small ARX wins. That is evidence against expecting zero-shot TSFMs to beat lagged ridge.
- TabPFN-2.5, used as a plain tabular regressor on explicitly lagged features rather than as a time-series model, is the frontier tool most likely to add nonlinear value at this data size. The VU data has roughly a few thousand TRs, within its 50k-row limit. Features would need reducing to 2,000 or fewer, for example 5 bands x 26 channels x 8 lags = 1,040 as in MEL, or PCA.
- Subject-grouped CV must be kept, and TabPFN's in-context set must exclude the test subject.

### Gaps
- No published test of Chronos-2 or TimesFM on EEG-to-fMRI or any EEG-to-continuous-physiology cross-modal regression.
- Won 2026 is a single-author preprint on synthetic and mechanical plants. Its applicability to neurovascular coupling is an inference.
- No Moirai 2.x or Lag-Llama neural regression evidence found.

---

## 5. Small-data strategies that measurably helped neural decoding/encoding

### Takeaway
The strategies with reported effect sizes are:
- subject-specific layers (removing Défossez's subject layer cut EEG top-10 accuracy from 17.7% to 8.1%);
- per-subject fine-tuning (VLAAI +34% with 5 min);
- Euclidean alignment (+4.33% accuracy, more than 70% faster convergence);
- augmentation (up to +45% accuracy in low-data regimes, task-dependent);
- seed or model ensembling (MEL +0.011 R inter-subject; decisive in Algonauts).

Self-supervised EEG foundation models often fail to beat compact or classical decoders when labels are scarce. Linear probing of frozen EEG-FM features is consistently weak. Most of this evidence is classification, not regression.

### Cited Findings
- **Subject layer (Défossez et al., Nat Mach Intell 2023; arXiv 2208.12266).** Removing the subject-specific layer cut top-10 segment accuracy:
  - Broderick EEG: 17.7 to 8.1
  - Brennan EEG: 25.7 to 20.2
  - Schoffelen MEG: 67.5 to 42.4
  - Gwilliams MEG: 70.7 to 47.0
  - Removing spatial attention cost less (Brennan 25.7 to 20.6; Gwilliams 70.7 to 65.5).
  - Accuracy rose with more training subjects on the MEG datasets.
  - [arXiv HTML](https://arxiv.org/html/2208.12266v2)
- **SuLoRA (Klein et al., arXiv 2510.08059, v2 Feb 2026)** [PREPRINT]. Subject-specific low-rank adapters as drop-in replacements for linear or conv layers. They beat both subject-agnostic and independently trained subject-specific models on EEG motor imagery, and beat the MEG speech baseline with half the parameters. No numbers in the abstract. — [arXiv abs](https://arxiv.org/abs/2510.08059)
- **Per-subject fine-tuning (VLAAI).** With 5 or more minutes of a new subject's data, up to +34% (r 0.18 to 0.25). — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41598-022-27332-2&resultType=core&format=json)
- **Euclidean alignment (Junqueira, Aristimunha, Chevallier, de Camargo; J Neural Eng 21:036038, 2024).** +4.33% target-subject accuracy and more than 70% shorter convergence with deep nets (BNCI2014, High-Gamma motor imagery). EA raised a 3-model per-subject ensemble by 3.71%, but the shared EA model was still 3.62% better than that ensemble. — [arXiv 2401.10746](https://arxiv.org/abs/2401.10746v4); [HAL](https://hal-lirmm.ccsd.cnrs.fr/LISN-AO/hal-04677699v1)
- **Augmentation (Rommel, Paillard, Moreau, Gramfort; arXiv 2206.14483, J Neural Eng 2022).** 13 augmentations, 2 tasks, 2 datasets, 2 models. Up to +45% accuracy in low-data regimes. The best augmentation differs by task (sleep staging vs motor imagery). CADDA (ICLR 2022) learns class-wise augmentation policies. — [arXiv 2206.14483](https://arxiv.org/abs/2206.14483v2); [CADDA arXiv 2106.13695](https://arxiv.org/abs/2106.13695v1)
- **Ensembling.**
  - MEL 5-seed MLP ensemble: inter-subject 0.488 to 0.499; intra-scan 0.524 to 0.543. — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
  - Algonauts 2025: top teams ensembled 20 to hundreds of models with per-parcel weights, and ensembling, not architecture, separated the ranks. — [arXiv 2508.10784](https://arxiv.org/html/2508.10784v1)
- **EEG foundation models / self-supervised pretraining in data-scarce settings.**
  - "Are EEG Foundation Models Worth It?" (ICLR 2026): fully fine-tuned FMs do well with plentiful labels. In data-scarce scenarios they often fail to significantly beat compact networks or classical non-neural decoders. Linear probing is consistently weak, and there is no clear scaling law. — [ICLR 2026 poster](https://iclr.cc/virtual/2026/poster/10011450); [MLAnthology](https://mlanthology.org/iclr/2026/yang2026iclr-eeg/)
  - OmniEEG-Bench (arXiv 2606.00815, May 2026) [PREPRINT]: frozen pretrained representations "remain substantially limited for direct transfer" under linear probing. Under linear probing only 5 FMs beat EEGConformer. — [arXiv HTML](https://arxiv.org/html/2606.00815v1)
  - EEG-FM-Compass (arXiv 2601.17883) [PREPRINT] reports similar conclusions over 12 FMs and 13 datasets: specialist models trained from scratch remain competitive, and larger FMs do not necessarily generalise better. — [arXiv](https://arxiv.org/abs/2601.17883v1)
- **Per-subject vs across-subject data.** Banville et al. 2025: little gain from more subjects; scaling depends on data per subject. — [arXiv abs](https://arxiv.org/abs/2501.15322) [PREPRINT]
- **Evaluation hygiene.**
  - Mehta et al.: cross-session degradation and leakage from temporally adjacent splits. — [arXiv 2504.10752](https://arxiv.org/abs/2504.10752)
  - NeuroBOLT: 20 s gaps between splits. — [arXiv 2410.05341](https://arxiv.org/pdf/2410.05341)
  - Semenkov et al.: targets relative to the mean signal, to avoid common-mode inflation. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2024.11.20.624528v1)
- **Mixup for regression.** C-Mixup (NeurIPS 2022) mixes only samples with close labels, for regression. — [arXiv 2210.05775](https://arxiv.org/abs/2210.05775) (URL not re-fetched)

### Inferences
- The cross-subject target subject has no fMRI, so supervised per-subject fine-tuning is unavailable at test time. The transferable pieces are:
  - (a) unsupervised per-subject alignment of EEG features: EA or per-subject re-centring of log-power covariance, or simply per-subject z-scoring of every lag-band-channel feature, which MEL does with train statistics;
  - (b) subject embeddings or SuLoRA-style adapters during training, so shared weights are not contaminated by subject idiosyncrasies;
  - (c) seed or bagging ensembles, which are cheap and gave consistent small gains.
- Given that the LaBraM branch contributed nothing, the ICLR 2026, OmniEEG and Compass findings (weak linear probing, no small-data advantage) make it unlikely that swapping in REVE or CBraMod embeddings will beat band-power ridge without substantial fine-tuning. Fine-tuning is exactly what overfits at n ≈ 22.
- Augmentation evidence is almost entirely classification. For a regression target with about 2 s TR and HRF lag, label-preserving augmentations are restricted. Channel dropout, small frequency shifts and amplitude scaling are plausible. Time masking or shifting breaks the EEG-BOLD lag relationship unless applied jointly to both.

### Gaps
- No EEG-to-BOLD study reporting the effect of EA, subject embeddings, augmentation or SSL pretraining.
- Effect sizes for SuLoRA not in the abstract.
- Augmentation evidence for continuous regression targets (rather than classification) is lacking.

---

## 6. Spectral feature extraction beyond STFT band power

### Takeaway
Several older simultaneous EEG-fMRI studies report features beating plain band power: spectral-shape metrics (RMSF, the Kilner heuristic), connectivity degree from imaginary coherency, synchronisation measures, and β-γ phase-amplitude coupling. All of these are small task or epilepsy cohorts, mostly with no cross-subject validation. MEL's ablation shows that within band power, lag and band structure carry most of the signal. Aperiodic (1/f) EEG components relate to specific BOLD networks (salience, prefrontal) but only minimally to the DMN. I found no EEG-to-fMRI work using Riemannian tangent-space features. Their regression track record is in M/EEG age prediction.

### Cited Findings
- **Rosa et al. (NeuroImage 2010).** BOLD changes in a visual task tracked shifts in the EEG spectral profile, the relative power of high vs low frequencies, rather than any single band. The Kilner heuristic (BOLD rises with RMS frequency) fit better than the Goense–Logothetis model, which assumes no spectral shift. — [PMC2793371](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2793371/)
- **Leite et al. (Frontiers in Neurology 2013), epilepsy.** "Clear superiority" of RMSF metrics over power-weighted metrics for predicting BOLD. — [Frontiers](https://frontiersin.org/journals/neurology/articles/10.3389/fneur.2013.00001/full)
- **Abreu, Leal, Lopes da Silva, Figueiredo (Clin Neurophysiol 129(3):618–635, 2018).** Title claim: EEG synchronisation measures predict epilepsy-related BOLD better than common univariate metrics. Only bibliographic metadata was retrieved. — [ISR record](https://welcome.isr.tecnico.ulisboa.pt/?p=23127)
- **Xavier, ..., Figueiredo (ISMRM 2021 #3384).** Elastic-net linear models predicting DMN BOLD from EEG. Compared RMSF, total power, linear combination of band powers, and the weighted degree of a band-specific imaginary-coherency network (WD-ICoh). WD-ICoh outperformed the others. No numbers in the abstract. — [ISMRM archive](https://archive.ismrm.org/2021/3384.html)
- **Murta et al. (NeuroImage 146:438–451, 2017), icEEG-fMRI finger tapping.** In 2 of 3 analysed patients, β-γ PAC strength explained BOLD variance beyond α, β and γ powers. — [PMC5312786](https://pmc.ncbi.nlm.nih.gov/articles/PMC5312786)
- **Aperiodic exponent (Jacob et al., bioRxiv 2021.01.30.427861; journal version indexed on DOAJ).** In eyes-open resting simultaneous EEG-fMRI, aperiodic and periodic power were "only minimally" associated with the DMN. Increases in aperiodic power correlated with an auditory-salience-cerebellar network, and decreases with prefrontal regions. The authors cite preliminary evidence that aperiodic activity may underlie the fMRI global signal. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2021.01.30.427861.full.pdf)
- **Frozen EEG-FM features vs aperiodic exponent (arXiv 2607.24834)** [PREPRINT, WITHDRAWN by author for a table error]. Withdrawn, so do not rely on its numbers. It reported that CBraMod and BIOT embeddings decode the aperiodic exponent (R² 0.46–0.76) more reliably across cohorts than alpha-envelope long-range temporal correlations. — [arXiv abs](https://arxiv.org/abs/2607.24834)
- **Riemannian / covariance features.** Sabbagh et al. (NeurIPS 2019): projecting M/EEG covariance matrices to tangent space and applying ridge outperformed sensor-space estimators for age regression and approached MRI-based source-localisation pipelines. — [arXiv 1906.02687](https://arxiv.org/pdf/1906.02687). Engemann et al. (NeuroImage 262:119521, 2022) benchmarked Riemannian, filter-bank and deep (Deep4Net) pipelines for brain age on more than 2,500 M/EEG recordings. Numbers were not retrieved. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2021.12.14.472691.full.pdf); [GitHub](https://github.com/meeg-ml-benchmarks/meeg-brain-age-benchmark-paper)
- **MEL feature ablations (VU data, ridge).** 5 canonical bands beat 3 (0.452 vs 0.407). Band reversal (0.236) and lag scrambling (0.10–0.20) devastate performance. Channel permutation is mild (0.395). — [arXiv HTML](https://arxiv.org/html/2608.29304v1) (extracted)
- **SAMBA** uses attention-weighted wavelet decomposition for electrophysiology, but no comparison with band power was obtained. — [arXiv 2409.18462](https://arxiv.org/pdf/2409.18462)

### Inferences
- Within a ridge framework, the cheapest additions with some EEG-fMRI support are:
  - per-channel RMSF or spectral-centroid time series and band ratios, which capture the spectral-shape effect that a log-power linear model represents only partially;
  - aperiodic exponent and offset per window (specparam), potentially useful for global signal and salience or prefrontal targets;
  - imaginary-coherency or envelope-correlation node degree per band, which was the best feature in the one DMN study, but it is multiplicative in channel pairs and so needs strong shrinkage or banded ridge.
- A small MLP on log band power can in principle learn ratio, RMSF-like and interaction terms. That may be part of why MEL-MLP beats MEL-ridge.
- Riemannian tangent-space features of sliding-window covariance are well founded for regression, but untested for EEG-to-BOLD. At 26 channels the tangent space per band is 351-dimensional, multiplied by lags, so feature count grows fast.
- Multitaper or continuous-wavelet estimators mainly reduce variance in the power estimates. No evidence was found that they change EEG-BOLD prediction accuracy relative to STFT.

### Gaps
- No head-to-head of multitaper vs STFT vs wavelet power for EEG-to-BOLD prediction was found.
- No EEG-to-BOLD study using Riemannian tangent-space features was found.
- The aperiodic-BOLD effect sizes, and whether they add predictive value beyond band power in a cross-validated model, were not retrieved.
- The Abreu 2018 and Xavier 2021 results are known only from title or abstract. All the feature-comparison studies are small (n ≤ ~20), task or epileptic, and within-subject.
