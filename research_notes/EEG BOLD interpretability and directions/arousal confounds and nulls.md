# Arousal, the global signal, physiological confounds and null models in EEG-to-BOLD prediction

Scope: what part of resting-state BOLD is predictable from scalp EEG, how much of it is global/arousal signal rather than region-specific, which physiological and motion confounds can look like EEG-BOLD coupling, and which null models apply. Written for the NeuroBOLT VU-dataset project: 22 people, 29 eyes-closed scans of about 20 min each, TR 2.1 s, 26 EEG channels, DiFuMo-64 plus the global signal, with EOG, EMG, ECG and four CWL channels also recorded.

Source-flag convention:
- Items marked **[verified]** were checked against an abstract, a full text or a bibliographic record during this session.
- Items marked **[prior knowledge, not re-fetched]** are classic papers cited from memory with their standard DOIs. Their details should be checked before they go into a manuscript.
- Preprints are flagged explicitly.

## (a) Vigilance/arousal and the BOLD global signal: how much of the global signal is arousal-related, and what is its spatial pattern?

### Takeaway
1. **The global signal moves with vigilance.** Under eyes-closed rest, both its amplitude and its moment-to-moment fluctuations track EEG vigilance. The index used in that work, alpha RMS over (delta+theta) RMS, is essentially the one this project uses.
2. **The arousal component has a characteristic spatial pattern.** Its largest-amplitude, mostly same-sign fluctuations are in sensory cortex: visual, auditory and sensorimotor. When vigilance is low these regions are high, and the thalamus, cingulo-insular cortex and basal forebrain move with the opposite sign.
3. **Drowsiness is the norm in long eyes-closed scans.** About a third of subjects lose wakefulness within 3 min and about half by 10 min.
4. **Much of this signal is autonomic.** Recent multimodal work shows that the arousal-linked global signal is tightly coupled to autonomic physiology: heart rate, respiration and finger vascular tone. Part of the "arousal" variance is therefore expressed through systemic or vascular channels rather than local neurovascular coupling.

### Cited Findings
**EEG vigilance and the global signal (Wong, Liu and colleagues)**
- Wong, Olafsson, Tal & Liu (2013, NeuroImage 83:983–990) **[verified]** — [PubMed 23899724](https://pubmed.ncbi.nlm.nih.gov/23899724/); [ISMRM abstract](https://archive.ismrm.org/2013/0033.html):
  - Across subjects in eyes-closed rest, global-signal amplitude (the SD of the GS) correlated significantly and negatively with EEG vigilance.
  - Caffeine (200 mg; about 10 subjects; 5-min eyes-closed scans before and after the dose) raised vigilance. That rise was associated with lower GS amplitude and stronger DMN–task-positive anticorrelation.
- The eyes-open relationship in that study was weaker and only nearly significant — [Liu & Falahpour 2020 review, Front Neurosci 14:321](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- Wong, DeYoung & Liu (2016, NeuroImage 124:24–31): the change in GS amplitude from eyes closed to eyes open correlated negatively with the change in EEG vigilance. The slope resembled the caffeine slope — [PubMed 26327245](https://pubmed.ncbi.nlm.nih.gov/26327245/); [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified via review]**.

**How EEG vigilance is defined**
- Most EEG-fMRI vigilance metrics divide mid-band (alpha, beta) by low-band (delta, theta) power.
  - Jobert 1994, Larson-Prior 2009 and Wong 2013 use alpha power over delta+theta power (some take the square root). Window lengths are 1.8 s in Wong 2013 and 3 s in Olbrich 2009.
  - Olbrich et al. (2009) use alpha / (delta+theta+alpha).
  - [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- In Falahpour et al. (2018), vigilance is the alpha (7–13 Hz) RMS amplitude divided by the delta+theta (1–7 Hz) RMS amplitude, convolved with an HRF — [Falahpour et al. 2018, NeuroImage 174:317–327, bioRxiv 10.1101/234179](https://www.biorxiv.org/content/10.1101/234179v2.full) **[verified]**.
- The project's alpha/(delta+theta) index is therefore the field-standard "EEG vigilance" measure, not a novel feature.

**Template-based (fMRI-only) vigilance estimates (Falahpour 2018, Chang 2016, Goodale 2021)**
- Falahpour, Chang, Wong & Liu (2018) **[verified]** — [bioRxiv full text](https://www.biorxiv.org/content/10.1101/234179v2.full):
  - Design: 9 analysed subjects, 54 five-minute runs, TR 1.8 s, eyes open and eyes closed, with and without caffeine.
  - The correlation between the fMRI-template vigilance estimate and EEG vigilance had mean 0.31, median 0.34 and IQR 0.15 across runs.
  - The template beat the global signal as a vigilance predictor (EC t(26)=3.4, p=0.002; EO t(26)=5.5).
  - Preprocessing included RETROICOR, RVHRCOR, WM/CSF and motion regressors.
- **Directly parallel to the project's rho=+0.66 finding:** across runs, how well the template predicted vigilance correlated with the amplitude of vigilance fluctuations (EC r=0.63, p=0.0004; EO r=0.47). The template also predicted each run's vigilance SD (EC r=0.63; EO r=0.54) — [Falahpour 2018](https://www.biorxiv.org/content/10.1101/234179v2.full) **[verified]**.
- The Liu & Falahpour review figure shows an example template-vs-EEG correlation of r=0.51, and r=−0.33 between vigilance and the inverted GS in one example scan — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- Chang et al. (2016, PNAS 113:4518–4523) **[verified]** — [doi:10.1073/pnas.1520613113](https://doi.org/10.1073/pnas.1520613113):
  - They derived an fMRI spatial "arousal template" in macaques from behavioural arousal (eyelid) measures.
  - The template's TR-by-TR expression closely approximated an independent intracranial LFP arousal measure.
  - Human scalp-EEG validation came later, from Falahpour et al. (2018) — [PMC4843437 context](https://pmc.ncbi.nlm.nih.gov/articles/PMC4843437).
- Goodale et al. (2021, eLife 10:e62376) is from the same Vanderbilt group. An fMRI-based alertness index derived from simultaneous EEG-fMRI predicted behavioural response variability — [eLife 62376](https://elifesciences.org/articles/62376) **[verified title; details prior knowledge]**.

**Prevalence of sleep in resting scans (Tagliazucchi & Laufs 2014)**
- Tagliazucchi & Laufs (2014, Neuron 82:695–708) analysed 1,147 resting-state datasets — [doi:10.1016/j.neuron.2014.03.020](https://doi.org/10.1016/j.neuron.2014.03.020) **[verified]**:
  - About one third of subjects lost wakefulness within the first 3 min.
  - About half had done so by 10 min — [as summarised in Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321).

**Spatial pattern of vigilance-related BOLD**
- In the simultaneous EEG-fMRI alpha/vigilance literature:
  - Positive correlations are reported in the thalamus, insula and anterior cingulate (Goldman 2002; Moosmann 2003; Feige 2005; Difrancesco 2008; Sadaghiani 2010).
  - Negative correlations are reported in visual and fronto-parietal cortex (Goldman 2002; Laufs 2003a,b; Moosmann 2003).
  - In the review's example, the top-10% vigilance frames show positive thalamus and negative sensory cortex; the bottom-10% frames show the reverse.
  - Source: [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- In Falahpour 2018, eyes-closed scans gave stronger negative vigilance correlations than eyes-open scans in DMN regions (PCC, temporal gyri, medial frontal). They also gave stronger positive correlations in the thalamus, cingulate and insula — [Falahpour 2018](https://www.biorxiv.org/content/10.1101/234179v2.full) **[verified]**.

**Physiological and autonomic coupling of the global signal (Bolt 2025)**
- Bolt et al. (2025, Nat Neurosci 28:1327–1335) **[verified abstract]** — [doi:10.1038/s41593-025-01945-y](https://doi.org/10.1038/s41593-025-01945-y):
  - A single low-frequency (0.01–0.1 Hz) spatiotemporal pattern links the global fMRI signal, EEG activity, and peripheral autonomic signals: cardiovascular, respiratory, exocrine (skin conductance) and smooth muscle (pupil).
  - The pattern appears at rest, with cued deep breaths, with sensory stimuli, and with spontaneous sleep EEG events.
  - It persists after controlling for end-tidal CO2.
- Details from the bioRxiv preprint, 10.1101/2023.01.19.524818 **[verified; preprint version of the published paper]** — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full):
  - **Size of the global component.** The first principal component (the global signal) explains about 25% of whole-brain low-frequency fMRI variance.
  - **Shared component.** A multiset CCA component shared across GS, EEG and physiology had a mean pairwise r of 0.31 (ME-REST).
  - **EEG timing.** Broadband EEG power (2–20 Hz) co-fluctuates with the GS at zero lag at rest. Broadband power rises around 4 s after arousal events, at about the same time as the GS peak.
  - **Arousal response.** Around arousal events, heart rate rises and PPG amplitude falls (vasoconstriction).
  - **Spatial sequence.** Early decreases appear in sensorimotor and visual cortex. Increases appear in WM, CSF and large arteries (around −0.8 s). Grey and white matter then decrease (around 2.3 s), followed by large veins (around 6.9 s).
  - **CO2 clamping.** PC1 spatial weights correlated r=0.95 between free-breathing and CO2-clamped conditions (variance explained 0.28 vs 0.25).
  - **Multi-echo.** ME-ICA denoising retains the global pattern.
  - **Interpretation.** The authors argue for a primarily sympathetic, autonomic upstream driver. They read EEG as a co-marker of a common subcortical arousal source, not as the direct cause.
- Özbay et al. (2019, Commun Biol 2:421) studied sleep fMRI with EEG and finger PPG **[verified abstract]** — [doi:10.1038/s42003-019-0659-0](https://doi.org/10.1038/s42003-019-0659-0):
  - Widespread fMRI decreases co-occurred with K-complexes and with episodic drops in finger-skin vascular tone, i.e., sympathetic vasoconstriction.
  - The group's earlier work (Özbay et al. 2018, NeuroImage) had found strong correlation between the whole-brain fMRI signal and finger-skin vascular tone during rest and light sleep.
- Gold et al. (2024, Imaging Neuroscience) used simultaneous fMRI, EEG and peripheral recordings. Covariation between fMRI and autonomic measures (pulse, respiration) became stronger as vigilance fell, and FC rose at low alertness, especially at rest — [doi:10.1162/imag_a_00287](https://doi.org/10.1162/imag_a_00287); [Vanderbilt summary](https://www.vanderbilt.edu/valiant/2025/06/20/functional-mri-signals-exhibit-stronger-covariation-with-peripheral-autonomic-measures-as-vigilance-decreases) **[verified abstract-level]**.

**Mechanistic and subcortical evidence (Turchi 2018, Raut 2021, Liu 2018, Gu)**
- Turchi et al. (2018, Neuron 97:940–952): reversible inactivation of the nucleus basalis of Meynert in macaques strongly suppressed the global component of cortical fMRI fluctuations ipsilateral to the injection. Resting-state network structure was left intact, implying that the NBM drives the global component but not network-specific correlations — [doi:10.1016/j.neuron.2018.01.032](https://doi.org/10.1016/j.neuron.2018.01.032); [PMC5823771](https://pmc.ncbi.nlm.nih.gov/articles/PMC5823771) **[verified]**.
- Raut et al. (2021, Sci Adv 7:eabf2709): arousal fluctuations are accompanied by infraslow global waves that propagate through neocortex, thalamus, striatum and cerebellum. These waves account for much of the topographically organised FC; macaque ECoG shows similar propagation — [doi:10.1126/sciadv.abf2709](https://doi.org/10.1126/sciadv.abf2709); [PubMed 34290088](https://pubmed.ncbi.nlm.nih.gov/34290088/) **[verified]**.
- Liu X et al. (2018, Nat Commun 9:395): fMRI global-signal peaks coincide with transient arousal drops seen as "sequential spectral transitions" in electrophysiology. They come with specific basal forebrain and thalamic signal changes — [doi:10.1038/s41467-017-02815-3](https://doi.org/10.1038/s41467-017-02815-3) **[follow-up verified via Chang 2016 citation context; details prior knowledge]**.
- Gu, Han & Liu:
  - Gu, Han & Liu (2019, Front Neurosci 13:1190) review arousal contributions to rs-fMRI connectivity and dynamics — [doi:10.3389/fnins.2019.01190](https://doi.org/10.3389/fnins.2019.01190) **[verified]**.
  - Gu, Han & Liu ("Transient arousal modulations contribute to resting-state functional connectivity changes associated with head motion parameters", published in Cerebral Cortex 2020 per citing literature) found that DVARS/motion metrics partly index arousal-linked global-signal events — [bioRxiv 10.1101/444463](https://www.biorxiv.org/content/10.1101/444463.full.pdf) **[verified preprint; journal version not verified]**.
  - In the ISMRM 2018 version, scrubbing arousal-related time points gave a similar but stronger FC change than motion scrubbing — [ISMRM 2018](https://archive.ismrm.org/2018/2307.html) **[verified abstract]**.

**Global signal and neural activity (Schölvinck 2010)**
- Schölvinck et al. (2010, PNAS 107:10238): LFP power at a single macaque cortical site correlated with fMRI fluctuations across nearly the whole cortex. This is the classic evidence that the GS has a neural component — [doi:10.1073/pnas.0913110107](https://doi.org/10.1073/pnas.0913110107) **[prior knowledge, not re-fetched]**.

**Drowsiness, light sleep and BOLD fluctuation amplitude (Horovitz 2008, Fukunaga 2006, Larson-Prior 2009)**
- BOLD fluctuation amplitude increases in light sleep and drowsiness:
  - Horovitz et al. 2008, HBM 29:671 — [doi:10.1002/hbm.20428](https://doi.org/10.1002/hbm.20428).
  - Fukunaga et al. 2006, MRI 24:979 — [doi:10.1016/j.mri.2006.04.018](https://doi.org/10.1016/j.mri.2006.04.018).
  - Larson-Prior et al. 2009, PNAS 106:4489 — [doi:10.1073/pnas.0900924106](https://doi.org/10.1073/pnas.0900924106).
  - **[prior knowledge, not re-fetched]**.

**VIGALL vigilance staging (Olbrich/Hegerl)**
- VIGALL (Hegerl, Olbrich, Sander) classifies short resting-EEG epochs into stages:
  - 0 / A1 / A2 / A3: wake with alpha that progressively "anteriorises".
  - B1: low-amplitude, non-alpha EEG.
  - B2/3: theta/delta.
  - C: sleep onset, with K-complexes and spindles.
  - Sources: Sander et al. 2015, Neuropsychobiology — [doi:10.1159/000439384](https://doi.org/10.1159/000439384); Olbrich et al. 2009, NeuroImage 45:319 (EEG-vigilance and BOLD) — [doi:10.1016/j.neuroimage.2008.11.014](https://doi.org/10.1016/j.neuroimage.2008.11.014). **[prior knowledge, not re-fetched]**
- Liu & Falahpour (2020) list Olbrich 2009's alpha/(delta+theta+alpha) metric with 3-s windows — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.

**Global signal regression (GSR) reviews**
- Murphy & Fox 2017, NeuroImage 154:169 — [doi:10.1016/j.neuroimage.2016.11.052](https://doi.org/10.1016/j.neuroimage.2016.11.052).
- Liu, Nalci & Falahpour 2017, NeuroImage 150:213, "The global signal in fMRI: nuisance or information?" — [doi:10.1016/j.neuroimage.2017.02.036](https://doi.org/10.1016/j.neuroimage.2017.02.036).
- Both conclude that the GS mixes neural, arousal, physiological and motion contributions and that GSR is a trade-off. **[prior knowledge, not re-fetched]**
- Murphy et al. (2009) showed that GSR can introduce negative correlations — [cited in Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.

### Inferences
- **The headline result is expected from the literature.** In NeuroBOLT the GS is the best-predicted target (cross-subject R 0.564), and a single alpha/(delta+theta) index carries more than half the ridge model's performance. That is what this literature predicts for 20-min eyes-closed scans, during which most subjects will drift through drowsiness and possibly N1/N2. The dominant shared variance between EEG and BOLD is then the vigilance axis.
- **The project's rho=+0.66 replicates Falahpour 2018.** The finding that scans with more variable alpha/theta are more predictable is a near-exact replication of Falahpour 2018 (r=0.63 between per-run predictivity and vigilance-fluctuation amplitude, eyes closed). Predictability is largely gated by how much arousal fluctuates in a scan.
- **No single number answers "how much of the GS is arousal".** Bounds from the cited studies:
  - Per run, template↔EEG vigilance r is about 0.3–0.5 (R² about 0.1–0.25).
  - GS↔autonomic shared component: mean r about 0.3 (Bolt).
  - The GS (PC1) is about 25% of low-frequency whole-brain variance.
  - NeuroBOLT's own cross-subject GS R of 0.56 (R² about 0.32) is at or above the upper end of these, which plausibly reflects 20-min scans with large vigilance excursions.
- **Spatial signature to look for in the model's per-ROI R map:** the biggest same-sign arousal component in visual (cuneus), auditory (Heschl's) and sensorimotor cortex, and opposite-signed or weaker effects in the thalamus, cingulo-insular cortex and basal forebrain. Heschl's gyrus and cuneus are among NeuroBOLT's best-predicted ROIs, which fits an arousal-dominated model.

### Gaps
- No published estimate of "% of GS variance explained by EEG vigilance" for 20-min eyes-closed scans was found. Most quantitative work uses 5-min scans (Wong, Falahpour) or sleep data (Özbay).
- Full-text numbers for Chang 2016 (template–LFP correlation), Liu 2018 and Raut 2021 (pupil coupling) were not retrieved: PMC was blocked by a CAPTCHA during this session.
- Özbay 2018 NeuroImage, Picchioni et al. 2022 (autonomic arousals and CSF pulsations) and Soon et al. 2021 (microsleeps: respiratory, cardiac, EEG and BOLD) were not re-fetched, so their quantitative results are not reported here.

## (b) Region-specific vs global EEG-BOLD coupling: thalamus vs cortex for alpha, and what is predictable beyond the global signal

### Takeaway
1. **There is genuinely region-specific alpha-BOLD coupling.** It comes with opposite signs in different structures: pulvinar and visual cortex negative, anterior and mediodorsal thalamus and cingulo-insular cortex positive, so it cannot be a single global factor. The global/arousal component sits on top of it and dominates variance in sensory cortex.
2. **GSR measurably shifts EEG-vigilance correlation maps** in the positive direction.
3. **Gap: no published EEG-to-BOLD *prediction* study after GSR was found.** Quantifying region-specific EEG-predictable variance beyond the GS appears to be an open, reportable analysis.

### Cited Findings
**Alpha-BOLD correlation maps: thalamus vs cortex**
- Liu Z, de Zwart, Yao, van Gelderen, Kuo & Duyn (2012, NeuroImage 63:1060–1069), eyes-closed rest **[verified abstract]** — [doi:10.1016/j.neuroimage.2012.08.025](https://doi.org/10.1016/j.neuroimage.2012.08.025); [PMC3472152](https://pmc.ncbi.nlm.nih.gov/articles/PMC3472152):
  - Posterior alpha correlated negatively with BOLD in the visual thalamus, mainly the pulvinar rather than the LGN, and positively in the anterior and mediodorsal nuclei.
  - The pulvinar was functionally connected to the same visual cortex that was negatively alpha-correlated.
  - The dorsal nuclei belonged to a separate network with brainstem, cingulate and cerebellum.
- Classic maps (Goldman 2002; Moosmann 2003; Laufs 2003; Feige 2005; Difrancesco 2008; Sadaghiani 2010): alpha correlates positively with thalamus, insula and ACC, and negatively with occipital and fronto-parietal cortex — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**. Primary papers **[prior knowledge, not re-fetched]**:
  - Goldman et al. 2002, NeuroReport 13:2487 — [doi:10.1097/00001756-200212200-00022](https://doi.org/10.1097/00001756-200212200-00022).
  - Moosmann et al. 2003, NeuroImage 20:145 — [doi:10.1016/S1053-8119(03)00344-6](https://doi.org/10.1016/S1053-8119(03)00344-6).
  - Laufs et al. 2003, NeuroImage 19:1463 — [doi:10.1016/S1053-8119(03)00286-6](https://doi.org/10.1016/S1053-8119(03)00286-6).
  - Sadaghiani et al. 2010, J Neurosci 30:10243 — [doi:10.1523/JNEUROSCI.1004-10.2010](https://doi.org/10.1523/JNEUROSCI.1004-10.2010).
- Large inter-subject variability: in a 7-subject simultaneous study, only 3 subjects showed the expected negative alpha-BOLD correlation in occipital, parietal and frontal cortex — Gonçalves et al. 2006, NeuroImage 30:203 — [Amsterdam UMC record](https://pure.amsterdamumc.nl/en/publications/correlating-the-alpha-rhythm-to-bold-using-simultaneous-eegfmri-i/) **[verified abstract-level]**.

**Network-specific EEG signatures (Mantini 2007, Laufs 2003 PNAS)**
- Different resting-state networks carry different combinations of EEG band-power signatures — Mantini et al. 2007, PNAS 104:13170 — [doi:10.1073/pnas.0700668104](https://doi.org/10.1073/pnas.0700668104).
- Beta2 (17–23 Hz) correlates positively with DMN-like regions — Laufs et al. 2003, PNAS 100:11053 — [doi:10.1073/pnas.1831638100](https://doi.org/10.1073/pnas.1831638100).
- **[prior knowledge, not re-fetched]**

**Effects of global signal regression on EEG-BOLD maps**
- Falahpour et al. (ISMRM 2017; cited as Falahpour 2018b in the review): GSR induced a positive shift in EEG vigilance–BOLD correlation maps — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
  - Studies without GSR report negative correlations in the lingual gyrus, PCC, cuneus and precuneus.
  - Sadaghiani 2010, which used GSR, found positive correlations in dACC, anterior insula and anterior PFC.
- Turchi 2018: inactivating the cholinergic basal forebrain removes the global component but spares RSN-specific correlation structure. This is causal evidence that global (arousal) and network-specific variance are separable — [doi:10.1016/j.neuron.2018.01.032](https://doi.org/10.1016/j.neuron.2018.01.032) **[verified]**.
- Bolt et al.: the global component (PC1) is about 25% of low-frequency fMRI variance, leaving most of the variance non-global — [bioRxiv 10.1101/2023.01.19.524818](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full) **[verified preprint]**.

**NeuroBOLT per-ROI results**
- Cross-subject Pearson R (NeuroBOLT) **[verified]** — [arXiv 2410.05341](https://arxiv.org/html/2410.05341v3):

  | ROI | Cross-subject R (mean ± SD) |
  |---|---|
  | Global signal | 0.564 ± 0.115 |
  | Heschl's gyrus | 0.561 ± 0.046 |
  | Anterior precuneus | 0.496 ± 0.136 |
  | Cuneus | 0.482 ± 0.100 |
  | Thalamus | 0.453 ± 0.106 |
  | Middle frontal gyrus | 0.423 ± 0.115 |
  | Putamen | 0.335 ± 0.144 |

- The authors stress that the thalamus is reconstructed from 26 scalp channels with accuracy comparable to cortical ROIs.
- Earlier ridge-on-EEG-time-frequency work predicted visual cortex and subcortical BOLD (cited in NeuroBOLT related work) — [arXiv 2410.05341](https://arxiv.org/abs/2410.05341v1) **[verified]**.

### Inferences
- **The ROI ranking matches arousal amplitude.** The ordering GS ≈ Heschl's > precuneus/cuneus > thalamus > MFG > putamen roughly tracks the expected amplitude of the arousal/global component, which is large in sensory cortex and smaller in striatum. Strong thalamus prediction is also consistent with the thalamus being a known vigilance-correlated structure (positive in anterior/mediodorsal nuclei). It does not need to be read as source-localised deep activity.
- **This explains why predicted FC collapses to the population average.** If one shared arousal factor drives most of the predicted variance across ROIs, the predicted time series are nearly rank-1. Their correlation matrix will then look like the population's global-dominated FC, not the individual's network-specific FC. Turchi 2018 implies the network-specific part is driven by different mechanisms.
- **Concrete tests (all straightforward with the existing pipeline):**
  1. Regress the GS, or the out-of-fold predicted GS, out of each ROI target and re-fit. Report the residual cross-subject R per ROI against a mismatched-subject null (see d).
  2. Fit a model whose only input is the vigilance index and compare per-ROI ΔR with the full model.
  3. Test whether residual (post-GSR) predictability concentrates where opposite-signed alpha coupling is expected (pulvinar/visual vs anterior/mediodorsal thalamus, dACC/insula).
- **Interpretation caveat.** GSR shifts correlations positive (Falahpour), so post-GSR maps should be read as "relative to the global mean". Negative post-GSR results are not evidence of anticorrelated neural coupling.

### Gaps
- No peer-reviewed EEG→BOLD prediction study reporting accuracy after global-signal regression (or partialling out a vigilance index) was found. Searching more specific terms such as "EEG-informed fMRI residual after GSR" or "vigilance-regressed EEG-fMRI prediction" might still find one.
- Feige 2005, Difrancesco 2008, Omata 2013 (deep-structure alpha correlates; [PLoS ONE](https://doaj.org/article/11ab95f20ac14d6c9832561f7055a80b)) and de Munck 2007/2009 were not re-fetched for effect sizes.

## (c) Physiological and motion confounds in simultaneous EEG-fMRI, how they are controlled, and whether heart rate or pulse amplitude is itself a vigilance marker

### Takeaway
1. **Every major confound is coupled to arousal.** Respiration (RVT, CO2), heart rate, sympathetic vasoconstriction (PPG amplitude), head motion, eye movements/closure and EMG all affect BOLD, scalp EEG, or both.
2. **"Regress out physiology" can therefore remove real arousal signal,** and "EEG predicts BOLD" can be a common-cause effect.
3. **Motion is the clearest true artefact.** Even sub-0.2 mm movements produce <20 Hz EEG power changes that, once convolved with an HRF, correlate with BOLD in neurally plausible regions, including superior temporal cortex.
4. **Heart rate and PPG amplitude are themselves vigilance/arousal markers.** HR rises and PPG amplitude falls at arousals, and brain–body coupling strengthens as vigilance falls.

### Cited Findings
**Head motion as an EEG-BOLD confound (Fellner 2016, Jansen 2012, Gu 2020)**
- Fellner et al. (2016, NeuroImage 133:354–366) **[verified abstract]** — [doi:10.1016/j.neuroimage.2016.03.031](https://doi.org/10.1016/j.neuroimage.2016.03.031); [Nottingham eprint](https://eprints.nottingham.ac.uk/32369/):
  - Low-frequency EEG (<20 Hz) was strongly tied to in-scanner movement, even for movements under 0.2 mm, after standard artefact correction.
  - EEG-BOLD correlations closely resembled motion-BOLD correlations.
  - The theta-BOLD effects in a memory task appeared to reflect motion.
- Jansen et al. (2012, NeuroImage 59:261–270) **[verified abstract]** — [doi:10.1016/j.neuroimage.2011.06.094](https://doi.org/10.1016/j.neuroimage.2011.06.094); [PMC3221044](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3221044/):
  - Theta, alpha and beta power and motion-artefact predictors were uncorrelated with BOLD before HRF convolution.
  - After convolution with the canonical HRF, all of them correlated strongly with BOLD in bilateral superior temporal cortex, SMA, medial parietal cortex and cerebellum.
- Arousal transients drive part of DVARS/motion-related FC change, so motion and arousal are partly confounded with each other — Gu, Han & Liu — [bioRxiv 10.1101/444463](https://www.biorxiv.org/content/10.1101/444463.full.pdf) **[verified preprint]**.
- The vigilance–global-signal relationship was reduced when motion was included as a covariate (Patanaik et al. 2018) — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.

**Ballistocardiogram and carbon-wire-loop (CWL) correction**
- Carbon-wire loops record artefact-only signals (motion, ballistocardiogram, helium-pump and ventilator noise) for regression-based removal. CWL correction outperformed post-processing-only EEG corrections — van der Meer et al. 2016, NeuroImage 125:880–894 — [doi:10.1016/j.neuroimage.2015.10.064](https://doi.org/10.1016/j.neuroimage.2015.10.064); [VU record](https://research.vu.nl/en/publications/carbon-wire-loop-based-artifact-correction-outperforms-post-proce/) **[verified bibliographic and abstract]**.
- Related papers **[prior knowledge, not re-fetched]**:
  - Masterton et al. 2007, NeuroImage 37:202, motion/BCG reference loops — [doi:10.1016/j.neuroimage.2007.02.060](https://doi.org/10.1016/j.neuroimage.2007.02.060).
  - Abbott et al., Front Neurol, constructing carbon-fibre motion loops — [doi:10.3389/fneur.2014.00260](https://doi.org/10.3389/fneur.2014.00260).
  - Mullinger et al. 2013, NeuroImage 71:75, sources of the pulse artefact including bulk head rotation — [doi:10.1016/j.neuroimage.2012.12.070](https://doi.org/10.1016/j.neuroimage.2012.12.070).

**NeuroBOLT preprocessing of the VU dataset**
- EEG: gradient and BCG artefacts were reduced in BrainVision Analyzer 2; ECG, EOG and EMG channels were dropped, leaving 26 channels.
- fMRI: multi-echo ICA (tedana), motion regression and low-pass filtering below 0.15 Hz.
- No physiological-noise regression and no GSR are described.
- Source: [NeuroBOLT arXiv 2410.05341](https://arxiv.org/html/2410.05341v3) **[verified]**.

**Respiration and CO2**
- Alpha EEG global field power correlated with respiration (respiratory volume), most strongly with eyes closed. BOLD maps for alpha and for respiration were spatially similar: negative in visual cortex and parts of the temporal and frontal lobes — Yuan, Zotev, Phillips & Bodurka 2013, NeuroImage 79:81–93 — [doi:10.1016/j.neuroimage.2013.04.068](https://doi.org/10.1016/j.neuroimage.2013.04.068); [PubMed 23631982](https://neuinfo.org/literature/pmid:23631982?rpKey=on) **[verified abstract]**.
- In the same study, the EEG alpha–BOLD correlation was reduced after respiratory and cardiac regressors were removed — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- Classic respiration and CO2 models **[prior knowledge, not re-fetched]**:
  - RVT regressors — Birn et al. 2006, NeuroImage 31:1536 — [doi:10.1016/j.neuroimage.2006.02.048](https://doi.org/10.1016/j.neuroimage.2006.02.048).
  - Respiration response function — Birn et al. 2008, NeuroImage 40:644 — [doi:10.1016/j.neuroimage.2007.11.059](https://doi.org/10.1016/j.neuroimage.2007.11.059).
  - End-tidal CO2 fluctuations drive low-frequency BOLD — Wise et al. 2004, NeuroImage 21:1652 — [doi:10.1016/j.neuroimage.2003.11.025](https://doi.org/10.1016/j.neuroimage.2003.11.025).
  - Respiration and PETCO2 vs BOLD — Chang & Glover 2009, NeuroImage 47:1381 — [doi:10.1016/j.neuroimage.2009.04.048](https://doi.org/10.1016/j.neuroimage.2009.04.048).
  - Whole-brain signals dominated by respiratory events and motion — Power et al. 2017, NeuroImage 146:609 — [doi:10.1016/j.neuroimage.2016.09.038](https://doi.org/10.1016/j.neuroimage.2016.09.038).
  - Multi-echo ICA does not remove respiration-related global signals — Power et al. 2018, PNAS 115:E2105 — [doi:10.1073/pnas.1720985115](https://doi.org/10.1073/pnas.1720985115).
- Bolt: the global spatiotemporal pattern survives end-tidal CO2 clamping (spatial r=0.95; variance 0.28 free vs 0.25 clamped) — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full) **[verified preprint]**.

**Heart rate and cardiac pulsation**
- Cardiac pulsation regressors (RETROICOR) — Glover, Li & Ress 2000, MRM 44:162 — [doi:10.1002/1522-2594(200007)44:1<162::AID-MRM23>3.0.CO;2-E](https://doi.org/10.1002/1522-2594(200007)44:1%3C162::AID-MRM23%3E3.0.CO;2-E) **[prior knowledge, not re-fetched]**.
- Low-frequency heart-rate fluctuations are a BOLD variance source — Shmueli et al. 2007, NeuroImage 38:306 — [doi:10.1016/j.neuroimage.2007.07.037](https://doi.org/10.1016/j.neuroimage.2007.07.037) **[prior knowledge, not re-fetched]**.
- The cardiac response function: HR convolved with a CRF that peaks at about 4 s and undershoots at about 12 s — Chang, Cunningham & Glover 2009, NeuroImage 44:857 — [doi:10.1016/j.neuroimage.2008.09.029](https://doi.org/10.1016/j.neuroimage.2008.09.029) **[prior knowledge, not re-fetched]**.
- Physiological response functions vary across subjects (partly with mean HR and its variance). Scan-specific PRFs can be estimated from more than 5 min of data and outperform canonical CRF/RRF — Kassinopoulos & Mitsis 2019, NeuroImage 202:116150 — [bioRxiv 10.1101/512855](https://www.biorxiv.org/content/10.1101/512855v3); [doi:10.1016/j.neuroimage.2019.116150](https://doi.org/10.1016/j.neuroimage.2019.116150) **[verified abstract; no variance-explained numbers in abstract]**.

**Heart rate and pulse amplitude as arousal markers**
- At arousals (deep breaths, cued responses, K-complexes), HR rises, EEG broadband power rises and PPG amplitude drops. These co-occur with the global fMRI peak at about 4 s, followed by an undershoot at about 14 s — Bolt et al. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full); [Nat Neurosci 2025](https://doi.org/10.1038/s41593-025-01945-y) **[verified]**.
- Finger vascular-tone drops (sympathetic) accompany K-complexes and widespread fMRI decreases — Özbay 2019 — [doi:10.1038/s42003-019-0659-0](https://doi.org/10.1038/s42003-019-0659-0) **[verified]**.
- Physio–fMRI coupling strengthens as vigilance decreases — Gold et al. 2024 — [doi:10.1162/imag_a_00287](https://doi.org/10.1162/imag_a_00287) **[verified]**.

**Eye movements and eye closure**
- Slow eyelid closures and microsleeps during drowsiness come with striking BOLD co-activation and deactivation patterns — Poudel et al. 2021, J Neural Eng — [PDF](https://www.nzbri.org/resources/publications/659/Poudel_Journal-of-Neural-Engineering_2021.pdf) **[verified abstract-level]**.
- Microsleeps show decreased thalamic and increased fronto-parietal activity — Poudel et al. 2014, HBM 35:257 — [doi:10.1002/hbm.22178](https://doi.org/10.1002/hbm.22178) **[prior knowledge, not re-fetched]**.
- Spontaneous eye movements in the dark or with eyes closed are coupled to resting-state fMRI fluctuations — Ramot et al. 2011, NeuroImage 58:213 — [doi:10.1016/j.neuroimage.2011.06.015](https://doi.org/10.1016/j.neuroimage.2011.06.015) **[prior knowledge, not re-fetched]**.

**Studies that combine EEG and physiology**
- Bolt's multiset CCA puts GS, EEG alpha/broadband power, HR, respiration, PPG, skin conductance and pupil into one shared component (mean pairwise r about 0.31) — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full) **[verified]**.
- Yuan 2013 showed partial overlap: alpha–BOLD correlation was reduced, not eliminated, by physiological regressors — [Liu & Falahpour 2020](https://doi.org/10.3389/fnins.2020.00321) **[verified]**.
- In Falahpour 2018, vigilance–fMRI relations were found after RETROICOR, RVHRCOR, WM/CSF and motion regression. The paper did not report with-vs-without comparisons — [Falahpour 2018](https://www.biorxiv.org/content/10.1101/234179v2.full) **[verified]**.

### Inferences
- **Why the confounds are not separable by regression alone.** The VU recordings include ECG (heart rate, HRV and, via ECG-derived respiration, a crude respiration proxy), EOG, EMG and four CWL channels. A belt or PPG is not mentioned in NeuroBOLT, so RVT and PPG amplitude may not be available. HR, respiration, PPG amplitude, motion and EOG are all arousal-coupled. Regressing them out of BOLD (or EEG) will remove some genuine arousal-linked neural variance along with artefact. The defensible design is **nested model comparison**, not "clean then predict":
  - Fit nuisance-only, EEG-only, and EEG+nuisance ridge models on the same cross-subject folds.
  - Report the unique ΔR of EEG over nuisance (and the reverse) per ROI.
  - The model families:
    - CWL band power and FD/realignment parameters (motion).
    - EOG power at 0.1–1 Hz (slow eye movements) and blink rate.
    - EMG power (muscle).
    - HR and HRV from ECG, convolved with a CRF or entered as lagged features.
  - If EEG keeps substantial unique R (especially in alpha/theta at posterior channels) over all of these, "artefact" is a weak explanation.
- **Motion risk in the project's best ROIs.** Jansen 2012 found motion-artefact EEG predictors mapped to superior temporal cortex, SMA, medial parietal cortex and cerebellum. NeuroBOLT's best cortical ROI is Heschl's gyrus (superior temporal) and the anterior precuneus is medial parietal. That is reason to run the CWL-only and motion-only models before claiming these as neural.
- **Channel and band diagnostics.** If ridge weights concentrate on frontal/temporal channels in delta and above about 20–30 Hz, suspect EOG and EMG respectively. Posterior alpha/theta weights are more consistent with genuine vigilance EEG.
- **Even a successful EEG prediction is ambiguous.** The arousal axis drives both EEG spectral shifts and sympathetic/vascular BOLD changes. "EEG predicts BOLD" is then compatible with a shared upstream cause, not EEG-indexed local neural activity driving local BOLD — the interpretation Bolt et al. adopt. To an advisor, the precise claim is: the model reads arousal state, a real brain state, and that state is expressed in BOLD through both neural and autonomic-vascular routes.
- **Open question for the project.** Whether NeuroBOLT's EEG preprocessing applied CWL regression is not stated; it describes only Analyzer-based gradient and BCG correction. If CWL regression was not applied, residual motion artefact in <20 Hz EEG is plausible (Fellner 2016).

### Gaps
- Not quantified: no paper found with cross-validated variance-explained numbers for an EEG-only vs a physiology-only vs a combined model of resting BOLD at the ROI level.
- Not retrieved:
  - Variance-explained figures for HR and RVT regressors on the global signal. Kassinopoulos & Mitsis 2019 and Chang 2009 full texts were not accessed.
  - Soon et al. 2021 (microsleeps; respiratory, cardiac, EEG and BOLD).
  - Abbott et al. (CWL construction): exact year and volume not verified.
- Not recorded in the VU dataset as described: EMG-specific EEG-fMRI confound studies with high-frequency (beta/gamma) muscle contamination of BOLD correlations. Not covered here.

## (d) Null models and significance testing for correlations between autocorrelated time series

### Takeaway
1. **Slow BOLD and HRF-convolved EEG features have few effective degrees of freedom.** For one 20-min scan, null |r| up to about 0.2 is ordinary, about 0.23 for 10 min, and about 0.35 for a 2-min test segment.
2. **Naive tests are badly miscalibrated.** Naive Fisher-z tests can give false-positive rates near 50%.
3. **The appropriate null depends on the claim:**
   - Effective-DOF correction (Bartlett, Pyper-Peterman, xDF) or circular-shift / IAAFT surrogates for single-scan significance.
   - A **mismatched-subject (session-permutation) null** for cross-subject prediction. It preserves any scan-time-locked structure shared across subjects, such as a drowsiness drift over the scan, onset transients or common filtering.

### Cited Findings
**Effective degrees of freedom: xDF, Bartlett, Pyper-Peterman**
- Afyouni, Smith & Nichols (2019, NeuroImage 199:609–625), "Effective degrees of freedom of the Pearson's correlation coefficient under autocorrelation" (xDF) **[verified]** — [doi:10.1016/j.neuroimage.2019.05.011](https://doi.org/10.1016/j.neuroimage.2019.05.011); [PMC6693558](https://pmc.ncbi.nlm.nih.gov/articles/PMC6693558):
  - Autocorrelation inflates Var(r) and breaks Fisher-z.
  - Naive false-positive rates "can approach 50%" when both series are highly autocorrelated.
  - In null data built by inter-subject scrambling, about 35% of regions were "significant" naively (expected 5%) against 2.6% with xDF.
  - Example edge: Z_naive=6.02 vs Z_xDF=2.08.
  - Bartlett-1935-type AR(1) corrections ignore cross-correlation and can be mis-calibrated (2% to over 7% FPR depending on AR order).
  - Global AR(1) corrections perform poorly.
  - Autocorrelation severity grows with ROI size.
  - They recommend per-pair ACF regularisation, truncating at N/5 lags following Pyper & Peterman, and no pre-whitening.
- Pyper & Peterman 1998, CJFAS 55:2127 — [doi:10.1139/f98-104](https://doi.org/10.1139/f98-104) **[prior knowledge, not re-fetched; formula cited by Afyouni 2019]**. Effective sample size:

  1/N* ≈ 1/N + (2/N) Σ_j [(N−j)/N] ρ_xx(j) ρ_yy(j), summed over lags j up to N/5.
- Bartlett 1946, J R Stat Soc Suppl 8:27 — [doi:10.2307/2983611](https://doi.org/10.2307/2983611) **[prior knowledge, not re-fetched]**. For two AR(1) series with coefficients a and b:

  Var(r) ≈ (1/N)(1+ab)/(1−ab).

  For a=b=0.8 that is N_eff ≈ N/4.6.

**Filtering and slow drift**
- Band-pass and low-pass filtering induces correlation between neighbouring samples and inflates connectivity estimates unless corrected — Davey, Grayden, Egan & Johnston 2013, NeuroImage 64:728–740 — [doi:10.1016/j.neuroimage.2012.08.022](https://doi.org/10.1016/j.neuroimage.2012.08.022); [manuscript](https://minerva-access.unimelb.edu.au/bitstream/handle/11343/44035/Filtering%20induces_NeuroImage.pdf?sequence=1) **[verified abstract-level]**.
- "Nonsense correlations" between slowly varying series (Yule 1926; Granger & Newbold 1974) and their modern neuroscience versions **[prior knowledge, not re-fetched]**:
  - Yule 1926 — [doi:10.2307/2341482](https://doi.org/10.2307/2341482).
  - Granger & Newbold 1974 — [doi:10.1016/0304-4076(74)90034-7](https://doi.org/10.1016/0304-4076(74)90034-7).
  - Slow drifts create spurious neuron–variable correlations, detectable with session-permutation nulls — Elber-Dorozko & Loewenstein 2018, eLife 7:e34248 — [doi:10.7554/eLife.34248](https://doi.org/10.7554/eLife.34248).
  - Session permutation, linear shift and other remedies — Harris, "Nonsense correlations in neuroscience", **preprint**, bioRxiv 10.1101/2020.11.29.402719 — [bioRxiv](https://doi.org/10.1101/2020.11.29.402719).
  - Functional networks largely reproduced by spatial and temporal autocorrelation alone — Shinn et al. 2023, Nat Neurosci 26:867 — [doi:10.1038/s41593-023-01299-3](https://doi.org/10.1038/s41593-023-01299-3).
  - Cross-correlation of autocorrelated series is unreliable without prewhitening or transfer-function models — Dean & Dunsmuir 2016, Behav Res Methods 48:783 — [doi:10.3758/s13428-015-0611-2](https://doi.org/10.3758/s13428-015-0611-2).

**Surrogate-data methods** **[prior knowledge, not re-fetched]**
- Phase randomisation (Fourier surrogates) preserves the power spectrum (the autocorrelation) and destroys cross-dependence — Theiler et al. 1992, Physica D 58:77 — [doi:10.1016/0167-2789(92)90102-S](https://doi.org/10.1016/0167-2789(92)90102-S).
- IAAFT additionally preserves the amplitude distribution — Schreiber & Schmitz 1996, PRL 77:635 — [doi:10.1103/PhysRevLett.77.635](https://doi.org/10.1103/PhysRevLett.77.635); Schreiber & Schmitz 2000, Physica D 142:346 — [doi:10.1016/S0167-2789(00)00043-9](https://doi.org/10.1016/S0167-2789(00)00043-9).
- Multivariate phase randomisation applies the same random phases to all channels, preserving within-set cross-spectra — Prichard & Theiler 1994, PRL 73:951 — [doi:10.1103/PhysRevLett.73.951](https://doi.org/10.1103/PhysRevLett.73.951).
- Review of surrogate methods, including cyclic shifts and their assumptions (stationarity; edge discontinuities for Fourier surrogates) — Lancaster et al. 2018, Phys Rep 748:1–60 — [doi:10.1016/j.physrep.2018.06.001](https://doi.org/10.1016/j.physrep.2018.06.001).

**Own simulation: chance-level r at this project's settings**
- Method (inference; script in session scratchpad, not in the repo):
  - Synthetic independent pairs at TR 2.1 s.
  - "BOLD": 1/f noise, 4th-order Butterworth low-pass below 0.15 Hz, 4th-order polynomial detrend, mirroring the NeuroBOLT fMRI preprocessing.
  - "EEG feature": an independent 1/f band-power series convolved with a canonical double-gamma HRF.
  - 4,000 pairs per length.
- Results:

  | Series length | Null SD(r) | 95th pct \|r\| | 99th pct \|r\| | Median Bartlett N_eff (nominal N) | White-noise SD |
  |---|---|---|---|---|---|
  | 20-min scan (N=575) | 0.10 | 0.20 | 0.25 | about 94 (575) | 0.042 |
  | 10 min (N=286) | 0.12 | 0.23 | 0.30 | about 69 (286) | — |
  | 2-min held-out segment (N=57; NeuroBOLT's intra-subject test window is the last 10% of the scan) | 0.18 | 0.35 | 0.44 | — | — |

- The mean of 22 *independent* null scans has a 95th-percentile |mean r| of about 0.04 (20-min).
- Steeper BOLD spectra (β>1) would widen all of these.

### Inferences
- **What the simulation does and does not settle.** Against an independence null, a cross-subject mean R of 0.38 across 22 people is far outside chance (null mean |r| at the 95th percentile is about 0.04). Individual scans or folds near R of about 0.2 are not individually distinguishable from chance by a naive test. The weakest fold (0.23) sits at the single-scan 95% bound if it is one subject's scan. The serious threat to the headline number is not sampling noise; it is **shared non-specific structure plus confounds**.
- **Recommended nulls, in order of relevance to the claims:**
  1. **Mismatched-subject null (session permutation).** Apply the trained cross-subject model to subject A's EEG and score it against subject B's time-aligned BOLD, over all A≠B (truncated to common length). This keeps everything scan-time-locked and shared: a monotonic drift toward drowsiness over a 20-min eyes-closed scan (cf. Tagliazucchi & Laufs), start-of-scan transients, filter edge effects and detrending. If mismatched pairs give mean r well above 0, part of the "prediction" is generic time-in-scan structure. The real effect is the matched-minus-mismatched gap.
  2. **Circular time-shift null within subject.** Rotate the EEG features relative to the BOLD by more than the model's lag window plus the HRF (say more than 30–60 s), avoiding the edges. This preserves both autocorrelations. It is valid only under approximate stationarity, which a drowsiness drift violates — another reason to pair it with (1).
  3. **Multivariate phase-randomised or IAAFT surrogates of the EEG feature matrix.** Use the same phases across features (Prichard-Theiler), then pass the surrogates through the frozen model. This tests whether the specific temporal alignment matters beyond spectral content.
  4. **Effective-DOF p-values (Pyper-Peterman/xDF) for per-scan or per-ROI correlations.** Pass the *predicted* and *observed* series. The prediction is a smoothed, HRF-like series, so its autocorrelation must enter the correction, not just the BOLD's.
- **Two traps specific to the evaluation:**
  - **Comparing intra- and cross-subject numbers.** NeuroBOLT's intra-subject numbers come from roughly 2-min test windows with a null 95% bound of about 0.35. They are noisier, and not directly comparable to cross-subject numbers on full 20-min scans.
  - **Group-level testing.** Treat subjects (not time points) as the unit, e.g., a one-sample test or permutation test on per-subject matched-minus-mismatched Fisher-z.

### Gaps
- No published EEG-fMRI paper was found that reports a mismatched-subject null for *cross-subject EEG→BOLD prediction* specifically. The approach is standard in hyperscanning and neural-encoding work, but no citable EEG-fMRI precedent was retrieved.
- Hindriks et al. 2016 (null distributions for sliding-window correlations; NeuroImage 127:242) was not re-fetched — [doi:10.1016/j.neuroimage.2015.11.055](https://doi.org/10.1016/j.neuroimage.2015.11.055) **[prior knowledge]**.
- The simulation assumes a 1/f spectrum and stationarity. It should be re-run with the project's actual BOLD and predicted-series ACFs (or replaced by the empirical mismatched-subject null).

## (e) Ceiling estimates: how much resting BOLD variance has been predicted from EEG, within-subject vs cross-subject

### Takeaway
1. **Best published resting-state numbers are around R² of 0.2–0.3.** The strongest are NeuroBOLT: mean R of about 0.53 within-subject on short held-out segments and about 0.47 cross-subject over 7 ROIs, with the GS at 0.56 cross-subject. That is roughly 20–30% of variance in the best ROIs and less elsewhere.
2. **Classic EEG-informed-fMRI and vigilance-template studies show lower per-run coupling,** around r 0.3–0.5.
3. **The project's ridge result sits in that range.** Mean cross-subject R of about 0.38 (R² about 0.14) across 64 ROIs is plausible for an arousal-dominated signal. The ceiling is probably set by how much arousal fluctuates in each scan, not by model capacity.

### Cited Findings
**NeuroBOLT (VU dataset)**
- Setup: 22 subjects, 29 eyes-closed scans of about 20 min, 26 channels — [arXiv 2410.05341](https://arxiv.org/html/2410.05341v3) **[verified]**.
- Intra-subject (train on the first 80% of a scan, test on the last 10%): NeuroBOLT mean R 0.531, against 0.341–0.484 for baselines.
- Cross-subject (18 train / 5 validation / 6 test scans): mean R 0.473, against 0.151–0.435 for baselines.
- No ridge baseline was run.
- The authors characterise moment-to-moment r of about 0.4–0.5 as strong given EEG/fMRI SNR — [arXiv 2410.05341](https://arxiv.org/pdf/2410.05341) **[verified]**.
- Other EEG→fMRI generative models exist (e.g., CATD, arXiv 2408.00777, **preprint**) — [arXiv 2408.00777](https://arxiv.org/pdf/2408.00777) **[verified existence only; numbers not retrieved]**.

**Reverse-direction and shared-variance benchmarks**
- fMRI-template ↔ EEG vigilance: mean r 0.31 per 5-min run (Falahpour 2018) — [bioRxiv](https://www.biorxiv.org/content/10.1101/234179v2.full) **[verified]**.
- GS / EEG / physiology shared component: mean r about 0.31 (Bolt) — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.01.19.524818v3.full) **[verified]**.
- The global component is about 25% of low-frequency whole-brain variance — same source **[verified]**.

**Earlier EEG-informed fMRI**
- Earlier resting-state EEG-informed fMRI studies report significant but variable band-power–BOLD correlations with marked inter-subject variability, e.g., only 3 of 7 subjects showing the canonical alpha pattern (Gonçalves 2006) — [Amsterdam UMC record](https://pure.amsterdamumc.nl/en/publications/correlating-the-alpha-rhythm-to-bold-using-simultaneous-eegfmri-i/) **[verified abstract-level]**.
- An "EEG fingerprint" approach predicted deep-region (amygdala) BOLD from EEG — Meir-Hasson et al. 2014, NeuroImage 102:128 — [doi:10.1016/j.neuroimage.2013.11.004](https://doi.org/10.1016/j.neuroimage.2013.11.004) **[prior knowledge, not re-fetched; effect size not verified]**.

### Inferences
- **The project's numbers are within the expected envelope.** Cross-subject R of about 0.38 for ridge on lagged band power (range 0.23–0.52 across folds) sits just below NeuroBOLT's transformer (0.47 cross-subject on 7 hand-picked, mostly high-arousal-amplitude ROIs). The vigilance-index-dominance finding suggests most of the gap between a one-feature model and a deep model is small. The ceiling is probably set by the arousal variance available in each scan (Falahpour's r=0.63 predictivity–amplitude relationship; the project's rho=+0.66).
- **Within- and cross-subject numbers are not comparable as reported.**
  - NeuroBOLT's within-subject advantage (0.53 vs 0.47) is measured on about 2-min test windows, whose null spread is much larger (95% |r| about 0.35 in the simulation above).
  - Within-subject models can also exploit subject-specific HRF and channel-impedance idiosyncrasies.
  - A fair comparison would use the same test segments, or leave-one-scan-out for subjects with two scans (7 of 22 in VU).
- **For the advisor:** a defensible statement is that about 10–30% of ROI BOLD variance is EEG-predictable across subjects. Most of it is the shared arousal/global axis, which reaches its highest amplitude in sensory cortex and thalamus. The region-specific remainder is not yet quantified; analyses (b) and (c) above would quantify it.

### Gaps
- No peer-reviewed study was found that reports cross-validated, cross-subject variance explained in resting BOLD from EEG across a whole-brain parcellation, other than NeuroBOLT (7 ROIs reported).
- No study was found that compares within- vs cross-subject prediction on identical test windows.
- Effect sizes for Meir-Hasson 2014, Kovalev et al. (EEG→subcortical fMRI, preprint) and 2025–2026 EEG→fMRI synthesis papers were not retrieved.
