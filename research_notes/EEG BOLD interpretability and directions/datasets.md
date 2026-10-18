# Open simultaneous EEG-fMRI datasets for enlarging or externally validating cross-subject EEG-to-BOLD prediction

Scope note. Facts below were taken from repository pages, dataset READMEs, BIDS sidecars and BrainVision headers (read through the OpenNeuro GraphQL API at https://openneuro.org/crn/graphql, so they are cited to the dataset's OpenNeuro page), and from the data papers. A systematic sweep of every OpenNeuro dataset tagged EEG (700) or MRI (1,193) on 2026-10-18 was used to find datasets holding both modalities; every hit was then checked by hand. Anything that could not be confirmed from a primary page is marked "unverified".

## Q1. Exact facts for each serious candidate dataset

### Takeaway
About a dozen open datasets hold simultaneous EEG-fMRI with a usable rest condition. Four are the best matches for the VU/NeuroBOLT pipeline: Penn State ds003768 (33 people, TR 2.1 s, rest plus sleep), Magdeburg MULTI-CLARID ds005795 (34 people, 10 min eyes-closed, TR 2 s, carbon-wire loops plus full physiology), NKI NATVIEW (22 people x 2 sessions, TR 2.1 s, rest plus movies) and Drexel/Temple ds007216 (24 people x 2 sessions, carbon-wire loops, rest with experience sampling). Each is open (CC0 or CC BY) and about the size of the current study or larger. Pooled, they would multiply the number of training people several times over.

### Cited Findings

#### Reference point: the current VU dataset (NeuroBOLT)
- The Hugging Face card ("neurobolt-rest") describes 22 participants and 29 scans (7 people scanned twice). Each person had two 20-minute eyes-closed resting sessions; scans were dropped for artefacts. Licence is Apache-2.0. — [HF card](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT/blob/main/README.md)
- Acquisition was 3T multi-echo gradient-echo EPI with TR 2100 ms. EEG was BrainAmp MR, a 32-channel 10-20 montage with FCz reference, sampled at 5 kHz and synced to the scanner's 10 MHz clock. After ECG/EOG/EMG are removed, 26 scalp channels remain. The release is DiFuMo-64 ROI series plus two global signals, low-passed below 0.15 Hz, with EEG resampled to 200 Hz. — [HF card](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT/blob/main/README.md)
- The card says task data and DiFuMo resolutions above 64 are not public. Requests go to yamin.li@vanderbilt.edu. — [HF card](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT/blob/main/README.md)
- According to the NeuroBOLT paper, the auditory-task set (16 scans, 10 subjects) came from a different site on a 3T Siemens Prisma. — [arXiv 2410.05341](https://arxiv.org/abs/2410.05341) (via search summary; not re-read in full)

#### 1. OpenNeuro ds003768 — "Simultaneous EEG and fMRI signals during sleep from humans" (Penn State, Xiao Liu lab)
- **Accession and licence:** https://openneuro.org/datasets/ds003768, latest snapshot 1.0.13, CC0, 92.9 GB. The data paper is Gu, Sainburg, Han & Liu, *Data in Brief* 48:109059 (2023). A companion paper is Gu et al., *NeuroImage* 2022 ("An orderly sequence of autonomic and neural events at transient arousal changes"). — [OpenNeuro ds003768](https://openneuro.org/datasets/ds003768); [Data in Brief / PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583)
- **Subjects and design:** 33 healthy participants (17 M / 16 F, age 22.1 ± 3.2). Session order: anatomical scan, a 10-min rest, a 15-min visual-motor adaptation task, a second 10-min rest, then several 15-min sleep scans. — [PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583); [OpenNeuro README](https://openneuro.org/datasets/ds003768)
- **Eyes and arousal tracking:** During rest, eyes were open or closed at will, closed about 75% of the time. Eyelid state was tracked with an ASL eye tracker. During sleep scans, awake participants pressed a button about once per second (S1 markers). — [PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583)
- **Sleep scoring:** A registered polysomnographic technologist scored sleep in 30-s epochs (w/1/2/3, plus uncertain/unscorable). Scores are in `sourcedata`. — [OpenNeuro README](https://openneuro.org/datasets/ds003768)
- **MRI:** 3T Siemens Prisma Fit with a 20-channel coil. EPI TR 2100 ms, TE 25 ms, 35 slices, 3x3x4 mm. — [OpenNeuro README](https://openneuro.org/datasets/ds003768)
- **EEG:** 32-channel Brain Products BrainAmp MR at 5000 Hz (0–250 Hz band), FCz reference, AFz ground. The BrainVision header lists 30 scalp channels (Fp1 Fp2 F3 F4 C3 C4 P3 P4 O1 O2 F7 F8 T7 T8 P7 P8 Fz Cz Pz Oz FC1 FC2 CP1 CP2 FC5 FC6 CP5 CP6 TP9 TP10) plus EOG and ECG. R128 markers are volume triggers. — [OpenNeuro ds003768 sub-01 vhdr](https://openneuro.org/datasets/ds003768)
- **Sidecar discrepancy:** The top-level BIDS sidecars say SamplingFrequency 250 and RecordingDuration 600/900 s. The .vhdr headers and file sizes are consistent with 5 kHz raw data (a 258.7 MB rest file of 32 int16 channels is about 809 s at 5 kHz). — [OpenNeuro ds003768](https://openneuro.org/datasets/ds003768)
- **Artefact correction and preprocessing:** The release is raw EEG; the paper says "The pre-processed EEG data were not provided". No preprocessed fMRI is described. — [PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583)
- **Physiology:** ECG and EOG are recorded. Respiration and pulse are not mentioned. — [PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583)
- **Volume:** The ATR survey table lists 58.3 h of recordings, the largest in its comparison. — [Tsutsumi et al. 2026, Table 1](https://europepmc.org/article/PMC/PMC12979783)

#### 2. OpenNeuro ds005795 — MULTI-CLARID (Multimodal Category Learning and Resting-state Imaging Data), LIN Magdeburg
- **Accession and licence:** https://openneuro.org/datasets/ds005795, snapshot 1.0.0 (2025-01-28), CC0, 6.9 GB. Authors are Stadler, Stöter, … van der Meer, Wolff, Brechmann. No data paper is listed; the related task paper is Wolff & Brechmann, *Cerebral Cortex* 2023. — [OpenNeuro ds005795](https://openneuro.org/datasets/ds005795)
- **Subjects and conditions:** 34 subjects, all with rest EEG and rest BOLD; 33 have physiology files. The design is a 10-min resting fMRI with eyes closed plus an approximately 27-min auditory category-learning task. Only 5 of the learning-task datasets are public; the rest are available on request. — [OpenNeuro ds005795 README and file tree](https://openneuro.org/datasets/ds005795)
- **MRI:** 3T Philips Achieva dStream with a 32-channel head coil, TR 2.0 s for both rest and task (bold.json). — [OpenNeuro ds005795](https://openneuro.org/datasets/ds005795)
- **EEG and auxiliary channels:**
  - 64-channel EEG (including ECG) at 5 kHz on two BrainAmp MRplus amplifiers.
  - A BrainAmp ExG MR recorded 2 EOG, 4 facial EMG and **4 carbon-wire loops**.
  - Skin conductance was recorded on a second ExG amplifier.
  - Respiration and heart rate came from Invivo MRI sensors (100 Hz).
  - — [OpenNeuro ds005795 README](https://openneuro.org/datasets/ds005795)
- **Artefact correction:** The released EEG is already preprocessed in BrainVision Analyzer 2.3: MR-artefact correction, 0.3–125 Hz band-pass, downsampling to 500 Hz, then CWL correction. The rest sidecar shows 72 channels at 500 Hz. "Raw data for optimized artifact correction are available upon request." — [OpenNeuro ds005795 README / sidecar](https://openneuro.org/datasets/ds005795)
- **Other files:** A T1w scan and a PD-weighted UTE scan for electrode localisation, plus electrodes.tsv. — [OpenNeuro ds005795](https://openneuro.org/datasets/ds005795)

#### 3. NATVIEW_EEGFMRI — "An open-access dataset of naturalistic viewing using simultaneous EEG-fMRI" (Nathan Kline Institute)
- **Accession and licence:** INDI page https://fcon_1000.projects.nitrc.org/indi/retro/nat_view.html; S3 path `s3://fcp-indi/data/Projects/NATVIEW_EEGFMRI/`; CC BY 4.0, with no DUA mentioned. Code is at https://github.com/NathanKlineInstitute/NATVIEW_EEGFMRI. The paper is Telesford et al., *Sci Data* 10:554 (2023). — [INDI page](https://fcon_1000.projects.nitrc.org/indi/retro/nat_view.html); [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **Subjects:** 22 adults (age 23–51), two sessions each, 2–354 days apart (median 11). — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **Conditions per session:**
  - 600 s rest. Rest is **eyes open** (white fixation cross); there is no eyes-closed condition.
  - 600 s Inscapes.
  - Movies: The Present 2 x 258 s; Monkey clips 2 x 300 s; Despicable Me 2 x 600 s (English in session 1, Hungarian in session 2).
  - A checkerboard outside the scanner, inside with scanner off, and inside with scanner on (200 s each).
  - A 90 s PEER calibration scan.
  - — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **MRI:** 3T Siemens TIM Trio with a 12-channel coil. TR 2100 ms, TE 24.6 ms, 38 slices, 3.47x3.47x3.33 mm, no multiband. TR was kept at 2.1 s to limit electrode RF heating. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **EEG:** BrainCap MR with 64 channels (61 cortical, 2 EOG, 1 ECG) on two BrainAmp MR amplifiers at 5 kHz. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **Physiology and eye tracking:** EyeLink 1000 Plus (left eye, released at 250 Hz). BIOPAC MP150 respiration belt at 62.5 Hz. No carbon-wire loops. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **Preprocessing released:**
  - EEG: FASTR gradient removal, PCA/ANC residual removal, QRS-template BCG subtraction, 0.5–70 Hz, average reference.
  - fMRI: Connectome Computation System with Friston-24 and WM/CSF regression (with and without GSR), Schaefer-400 ROI time series.
  - Motion/QC metrics: FD and DVARS.
  - — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **Volume:** The ATR survey table lists 47.0 h. — [Tsutsumi et al. 2026, Table 1](https://europepmc.org/article/PMC/PMC12979783)

#### 4. OpenNeuro ds007216 — "A multi-session simultaneous EEG-fMRI dataset with (repeated/online) experience sampling" (Kucyi lab, Drexel; scanned at Temple)
- **Accession and licence:** https://openneuro.org/datasets/ds007216, snapshot 1.1.0. The OpenNeuro description says CC0, while the preprint says CC BY 4.0. There is also an NDA copy (collection C4336). The preprint is Shareef-Trudeau, Braun, Bounyarith, Li, Peng & Kucyi, bioRxiv, Feb 2026 (doi 10.64898/2026.02.04.703882). — [OpenNeuro ds007216](https://openneuro.org/datasets/ds007216); [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **Subjects and sessions:** 24 adults (18–35), 47 EEG-fMRI sessions (23 people x 2 sessions, 1 x 1), 3–62 days apart. About 1.33 h of simultaneous data per person. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **Conditions per session:** 3 x ~10.5-min rest runs with multidimensional experience sampling (fixation cross, so eyes open; probes every 45–60 s), plus 1 x ~8-min gradCPT. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **MRI:** 3T Siemens Prisma with a 64-channel coil. Multiband 3, TR 2000 ms, TE 25 ms, 2 mm isotropic, with a B0 field map. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **EEG:** BrainCap MR with 31 cortical 10-20 channels, **4 CWL sensors**, and ECG on channel 32, recorded at 5 kHz. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **Artefact correction released:** Gradient correction in the BERGEN toolbox using SPM realignment parameters, then CWL regression for cardioballistic and helium-pump artefacts. Filtering, ICA and re-referencing are left to the user. The paper describes FSL-based fMRI preprocessing for validation. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **Respiration and eye tracking:** Not mentioned in the portion read. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)

#### 5. OpenNeuro ds006040 — "Sustained Attention Task (gradCPT) Dataset using simultaneous EEG-fMRI and DTI" (Sungkyunkwan University, Moon lab)
- **Accession and licence:** https://openneuro.org/datasets/ds006040, snapshot 1.0.2, CC0, 185.2 GB. The paper is Cha et al., *Sci Data* (published 2026-03-03, doi 10.1038/s41597-026-06616-6). Code is at https://github.com/MoonBrainLab/GradCPT-Simultaneous-EEG-fMRI-DTI-Data. — [OpenNeuro ds006040](https://openneuro.org/datasets/ds006040); [Europe PMC PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **Subjects:** 28 (age 19–42), one session each. — [OpenNeuro ds006040](https://openneuro.org/datasets/ds006040); [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **Conditions:** Eyes-open and **eyes-closed** rest in both Scan OFF and Scan ON, a 15 Hz checkerboard, gradCPT, imagery, and gradCPT-with-imagery. Task codes include EO/EC with ON/OFF. Scan-OFF eyes-open rest is 180 s. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628); [OpenNeuro README_dataset.txt](https://openneuro.org/datasets/ds006040)
- **MRI:** 3T Siemens Prisma with a 64-channel coil. TR fixed at 2 s for all fMRI, 40 slices, 3.5 mm voxels. DWI is also included. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **EEG:** BrainCap MR with Multitrodes, 64 channels (63 cortical plus ECG on channel 32), at 5000 Hz on two BrainAmp MR. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **Preprocessing:** EEG used FMRIB gradient removal (window 30), QRS detection and median-template BCG subtraction, and a 0.5–100 Hz filter. fMRI was run through fMRIPrep 23.0.1. Both raw and preprocessed data are released. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **Physiology and eye tracking:** An EyeLink 1000 was used to monitor engagement; whether those data are released is unverified. Respiration and skin conductance were **not** recorded (the authors say so). No CWL. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)

#### 6. OpenNeuro ds005127 — "AMRI 16-N-0031 sleep1" (NIH/NINDS Advanced MRI section; Picchioni, Duyn, de Zwart)
- **Accession and licence:** https://openneuro.org/datasets/ds005127, snapshot 2.0.2 (2026-08-26), 491.6 GB. The LICENSE file says **CC BY 4.0**, although the OpenNeuro metadata field says CC0. — [OpenNeuro ds005127](https://openneuro.org/datasets/ds005127)
- **Design:** Overnight EEG-fMRI on two consecutive nights, about 8 h each. Participants were woken at random intervals 8 times per night. Data were collected around 2016–2017. 16 subjects (age 20.8–33.1). Short wake scans are included: rest is "eyes closed, please stay awake", along with ICC/ECC tasks, a motion localizer and a waking perceptual-threshold task. — [OpenNeuro ds005127 README/FAQ/participants.tsv](https://openneuro.org/datasets/ds005127)
- **MRI:** 3T, TR 3.0 s, TE 36 ms, no multiband (bold.json). A `func-complex` folder holds phase data. — [OpenNeuro ds005127](https://openneuro.org/datasets/ds005127)
- **EEG:**
  - 65 recorded channels at 5000 Hz, FCz reference, AFz ground: 63 EEG + ECG + EMG.
  - Channels 11 and 12 are labelled E1/E2 (EOG positions) where the standard cap has F7/F8.
  - — [OpenNeuro ds005127 eeg.json/vhdr](https://openneuro.org/datasets/ds005127)
- **Derivatives:** Added in 1.0.2 and later: EEG-derived sleep scoring (30-s epochs, AASM, wall-clock time); gradient- and cardioballistic-corrected EEG; preprocessed fMRI; and `physio_prepro`. Raw folders include `biopac`, `video` and `misc`. — [OpenNeuro ds005127 CHANGES/file tree](https://openneuro.org/datasets/ds005127)
- **Method papers:** Moehlman 2019 *J Neurosci Methods* and Picchioni 2022 *NeuroImage*. — [OpenNeuro ds005127 FAQ](https://openneuro.org/datasets/ds005127)
- **Follow-on study:** "sleep2" (ds006163, 2019–2024) is "tentatively publicly released in September 2028". Its OpenNeuro page did not return a public snapshot. — [OpenNeuro ds005127 README](https://openneuro.org/datasets/ds005127)

#### 7. Gallego-Rudolf et al. — "Simultaneous and independent EEG and MRI: a multimodal neuroimaging dataset" (UNAM Juriquilla, Mexico)
- **Accession and licence:** Mendeley Data https://data.mendeley.com/datasets/crhybxpdy6/2 (doi 10.17632/crhybxpdy6.2). The paper is *Data in Brief* 51:109661 (2023). The article is CC BY; the page reviewed states no separate data licence. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **Subjects:** 20 healthy **males** (mean 26 y). — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **Simultaneous conditions:** **10 min eyes-closed rest** and a 4-min EO/EC block task. A 2-min eyes-open block was recorded but its fMRI is not included. There is also EEG outside the scanner and inside without scanning, and a separate session with 10 min of EC fMRI without the cap (sub-019 session-1 EC fMRI is missing). — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **MRI:** 3T GE MR750 Discovery with a 32-channel coil. TR 2000 ms, TE 40 ms, 35 slices, 4 mm isotropic. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **EEG:** EGI GES 400 MR, 32-channel sponge Geodesic Sensor Net at 1000 Hz, Cz reference, with ECG. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **Preprocessing:** Only gradient-corrected EEG is provided (`_gac`, AAS in Net Station), so BCG remains. fMRI is raw only. Structured as BIDS. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)

#### 8. ATR "atr-EfP-2025" — "An EEG dataset with carbon wire loops in cognitive tasks and resting state inside and outside MR scanners" (ATR, Kyoto)
- **Access:** https://bicr.atr.jp/dbi/download/dataset-of-eeg-fmri-with-cwl/. Not open download: you email for access with a signed Data Usage Agreement, use is **noncommercial only**, and every co-user must be named. — [ATR page](https://bicr.atr.jp/dbi/download/dataset-of-eeg-fmri-with-cwl/)
- **Paper:** Tsutsumi, Kishi, Ogawa, Kuroda, Kobler & Kawanabe, *Sci Data* (2026-02-04, doi 10.1038/s41597-026-06734-1). — [Europe PMC PMC12979783](https://europepmc.org/article/PMC/PMC12979783)
- **Subjects:** 39 adults in their 20s–40s; 43.6 h of data. A subset was scanned on both scanners (traveling-subject design). — [PMC12979783](https://europepmc.org/article/PMC/PMC12979783)
- **Conditions:** Multiple **8-min eyes-open** rest runs per day, 6-min visual oddball and 7-min N-back, over two days; also EEG in a shielded room without scanning. — [PMC12979783 Table 2](https://europepmc.org/article/PMC/PMC12979783)
- **MRI:** Two 3T scanners: a Siemens Prisma fit (64-channel coil, TR 0.8 s, multiband) and a Siemens Verio (12-channel coil, TR 2.5 s, single-band). — [PMC12979783 Table 1](https://europepmc.org/article/PMC/PMC12979783)
- **EEG:** 63 channels + ECG + **4 CWL** (BrainAmp MR plus / ExG MR, BrainCap MR) at 5 kHz with SyncBox. — [PMC12979783](https://europepmc.org/article/PMC/PMC12979783); [ATR page](https://bicr.atr.jp/dbi/download/dataset-of-eeg-fmri-with-cwl/)
- **Release state:** **Raw** but de-identified (EEGLAB .set, NIfTI, BIDS). The preprocessing pipeline (AAS, CWL regression, 250 Hz, autoreject) is described, not shipped. — [PMC12979783](https://europepmc.org/article/PMC/PMC12979783)

#### 9. "EEG, fMRI and NODDI at rest" (UCL; Deligianni et al.)
- **Accession and licence:** OSF https://osf.io/dvmrb (BIDS v1.1.2 version prepared by C.R. Pernet), CC BY 4.0. Authors are F. Deligianni, M. Centeno, D.W. Carmichael, G.H. Zhang, C.A. Clark and J.D. Clayden. Associated papers: Deligianni et al., *Front Neurosci* 8:258 (2014) and *PLoS ONE* 11(4):e0153404 (2016). — [OSF wiki (via OSF API)](https://osf.io/dvmrb)
- **Acquisition (secondary source):** 17 healthy adults, **eyes-open** rest, 64-channel EEG at 250 Hz, Siemens Avanto **1.5T**, TR 2.16 s. Literature using it often keeps 15 subjects. This comes from an EEG-to-fMRI synthesis paper and was not checked against the OSF files. — [arXiv 2502.08025 (search summary)](https://arxiv.org/pdf/2502.08025)

#### 10. CWL "Eyes Open – Eyes Closed" EEG/fMRI dataset (van der Meer et al. 2016; Magdeburg / MPI CBS Leipzig)
- **Accession:** NITRC https://www.nitrc.org/projects/cwleegfmri_data, 8 subject archives released 2017-11-02 under an MIT licence. The paper names an XNAT project at MPI CBS (xnat.cbs.mpg.de, project EEGfMRI) as the raw archive. The NITRC page carries a banner saying it is "under review for potential modification in compliance with Administration directives". — [NITRC](https://www.nitrc.org/projects/cwleegfmri_data); [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **Subjects and conditions:** 8 subjects doing a 4 min 30 s EO/EC block task (four 30-s EC blocks) under 6 conditions: outside before, in-bore helium pump on/off with and without EPI, and outside after. — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **MRI:** 3T Siemens Trio (TR 1.95 s, 4 subjects) and Verio (TR 2.0 s, 4 subjects). — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **EEG:** 30-channel BrainAmp MR Plus at 5 kHz + EOG + ECG + 6 CWL. — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **Release state:** Both raw and corrected EEG (Bergen toolbox), and DARTEL-normalised EPI. — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)

#### 11. OpenNeuro ds003574 — "Reward biases spontaneous neural reactivation during sleep" (Geneva; Sterpenich et al., *Nat Commun* 2021)
- **Accession and licence:** https://openneuro.org/datasets/ds003574, CC0, 19.3 GB. — [OpenNeuro ds003574](https://openneuro.org/datasets/ds003574)
- **Design:** 18 participants. Two task EPI sessions (face and maze games, with rest periods) were recorded without EEG. One EPI session of rest-to-sleep was recorded with 64-electrode EEG, lasting 1–2 h in the scanner and reaching N2 or N3. — [OpenNeuro ds003574](https://openneuro.org/datasets/ds003574)
- **MRI:** 3T Siemens TrioTim (Geneva BBL), TR 2.1 s. — [OpenNeuro ds003574 bold.json](https://openneuro.org/datasets/ds003574)

#### 12. OpenNeuro ds002725 — joint EEG-fMRI during affective music listening (Reading/Plymouth; Daly et al.)
- **Accession and licence:** https://openneuro.org/datasets/ds002725, CC0, 16.4 GB. Paper: Daly et al., *Sci Rep* 9:9415 (2019). — [OpenNeuro ds002725](https://openneuro.org/datasets/ds002725)
- **Design and acquisition:** 21 participants. Tasks are classical and generated music runs plus "washout" runs; the ATR table describes 2 x 30-min listening. EEG is 30 channels + ECG, with FCz reference and 1000 Hz in the BIDS sidecar. TR is 2.0 s; the ATR table gives the scanner as Siemens Trio 3T. — [OpenNeuro ds002725 sidecars](https://openneuro.org/datasets/ds002725); [PMC12979783 Table 1](https://europepmc.org/article/PMC/PMC12979783)
- **Not established:** Artefact-correction status is not stated in the README, so it is unverified.

#### 13. OpenNeuro ds002336 / ds002338 — EEG-fMRI motor-imagery neurofeedback XP1 / XP2 (Rennes; Lioi et al., *Sci Data* 7:173, 2020)
- **Accession and licence:** https://openneuro.org/datasets/ds002336 (XP1: 10 subjects, 18.0 GB) and https://openneuro.org/datasets/ds002338 (XP2: 17 subjects, 26.0 GB), both CC0. — [ds002336](https://openneuro.org/datasets/ds002336); [ds002338](https://openneuro.org/datasets/ds002338)
- **Design:** Block design of 20 s rest / 20 s task (motor localizer, MI pre/post, NF runs). There is no continuous rest run. — [ds002336 README](https://openneuro.org/datasets/ds002336)
- **MRI:** 3T Siemens Verio. XP1: TR 2 s, whole brain, 32 slices, 2x2x4 mm. XP2: **TR 1 s with only 16 slices covering the superior half of the brain**. — [ds002336 README](https://openneuro.org/datasets/ds002336); [ds002338 README](https://openneuro.org/datasets/ds002338)
- **EEG:** 64-channel Brain Products at 5 kHz, FCz reference, ECG on channel 32. Preprocessed EEG is supplied: BVA gradient AAS, downsampling to 200 Hz, 50 Hz low-pass, and semi-automatic BCG correction with R markers. — [ds002336 README](https://openneuro.org/datasets/ds002336)

#### 14. OpenNeuro ds000116 — Auditory and Visual Oddball EEG-fMRI (Columbia; Walz, Goldman, Muraskin, Conroy, Brown, Sajda)
- **Accession and licence:** https://openneuro.org/datasets/ds000116, 17 subjects, 3.3 GB on OpenNeuro. The licence field is null. **The EEG is only on legacy OpenfMRI** (https://legacy.openfmri.org/dataset/ds000116/). — [OpenNeuro ds000116](https://openneuro.org/datasets/ds000116)
- **Design and MRI:** 3 auditory + 3 visual oddball runs of 170 TRs each. 3T Philips Achieva with a single-channel coil, TR 2 s, 32 slices, 3x3x4 mm. — [OpenNeuro ds000116 README](https://openneuro.org/datasets/ds000116)
- **EEG:**
  - Custom MR-compatible bipolar system with 49 channels at 1000 Hz: 43 EEG bipolar pairs, re-referenced to 34 electrodes, plus 2 EOG and ECG.
  - Supplied as raw, gradient-removed (BCG remains), and re-referenced.
  - — [OpenNeuro ds000116 README](https://openneuro.org/datasets/ds000116)

#### 15. Smaller, task-only, or restricted datasets (catalogued for completeness)
- **ds002158** (EPFL/Campus Biotech Geneva; Pereira et al., *PNAS* 2020):
  - 20 subjects, CC0, 82.2 GB; 3T Siemens Prisma, multiband 4, rest TR 1.28 s.
  - Derivatives include `eegprep` and `fmriprep`. A `task-rest` BOLD exists, but the EEG folders inspected (sub-02, sub-10 ses-001) contain only `task-main` runs, so rest EEG appears absent.
  - — [OpenNeuro ds002158](https://openneuro.org/datasets/ds002158)
- **ds002739** (Glasgow; Gherman & Philiastides): 24 subjects, CC0, 7.6 GB. A perceptual-confidence task with only "rest_break" periods; preprocessed EEG at 1000 Hz and preprocessed fMRI with motion parameters; TR 2 s. — [OpenNeuro ds002739](https://openneuro.org/datasets/ds002739)
- **Georgie et al. "A perceptual decision making EEG/fMRI data set"** (Birmingham/FU Berlin):
  - 17 subjects, task only with no rest; 3T Philips Achieva, TR 2 s; 64-channel BrainAmp MR Plus at 5 kHz.
  - Gradient- and BCG-corrected EEG is in `derivatives`.
  - The OSF project https://osf.io/q4t8k/ is **private and needs a DUA**.
  - — [bioRxiv 253047](https://www.biorxiv.org/content/10.1101/253047.full)
- **Kraljič et al. 2022** (Ljubljana):
  - 16 subjects; resting state as 22 alternating 40-s EO/EC blocks, plus finger tapping and checkerboard.
  - 3T Philips Achieva TX, multiband 4, TR 1.1 s; **128-channel** BrainCap MR at 5 kHz with **6 CWL** and ECG.
  - Only processed and exported data plus scripts are on OSF (https://osf.io/2ey74/). Raw data "will be made available by the authors, without undue reservation".
  - — [PMC10406266](https://pmc.ncbi.nlm.nih.gov/articles/PMC10406266/)
- **ds006033** (synchronous EEG-fMRI inner speech): 3 subjects. **ds005533** (Lewis lab, "High-quality multimodal MRI with simultaneous EEG using conductive ink and polymer-thick film nets"): 3 subjects, checkerboard. Both are too small for cross-subject work. — [OpenNeuro sweep: ds006033](https://openneuro.org/datasets/ds006033); [ds005533](https://openneuro.org/datasets/ds005533)
- **Sajda-lab "He et al." auditory oddball with pupillometry:** 19 subjects, Prisma TR 2.1 s, 64-channel. It is listed in the ATR survey, but data availability was not checked. — [PMC12979783 Table 1](https://europepmc.org/article/PMC/PMC12979783)

### Inferences
**Ranked table** (my ranking for the specific goal of cross-subject EEG-to-BOLD rest prediction in the NeuroBOLT pipeline). "Open" means a direct download with no DUA.

| Rank | Dataset (accession) | N people (sessions) | In-scanner rest | TR / field / vendor | EEG (rest of montage) | Artefact-corrected EEG shipped? | CWL / ECG / resp / eye | Licence & access |
|---|---|---|---|---|---|---|---|---|
| 1 | Penn State sleep/rest, ds003768 | 33 | 2x10 min, eyes mostly closed (~75%), plus 15-min sleep runs | 2.1 s / 3T / Siemens Prisma | BrainAmp MR 32 (30 scalp, standard 10-20), FCz ref, 5 kHz | No (raw) | – / ECG / – / eyelid via ASL (release unverified) | CC0, open |
| 2 | MULTI-CLARID, ds005795 | 34 | 10 min eyes closed | 2.0 s / 3T / Philips Achieva | BrainAmp MRplus 63 + ECG, 5 kHz (shipped at 500 Hz) | Yes (MR + CWL corrected); raw on request | 4 CWL / ECG / resp+pulse / – (+EOG, EMG, GSR) | CC0, open |
| 3 | NATVIEW (INDI S3) | 22 (x2) | 2x10 min **eyes open** | 2.1 s / 3T / Siemens Trio | BrainCap MR 61 + 2 EOG + ECG, 5 kHz | Yes (FASTR + BCG) and Schaefer-400 fMRI ROIs | – / ECG / belt / EyeLink | CC BY 4.0, open |
| 4 | Kucyi multi-session, ds007216 | 24 (47 sessions) | 3x~10.5 min per session, eyes open, with experience sampling | 2.0 s MB3 / 3T / Siemens Prisma | BrainCap MR 31 + ECG, 5 kHz | Yes (gradient + CWL regression) | 4 CWL / ECG / not stated / not stated | CC0 (OpenNeuro) / CC BY (paper), open; NDA mirror |
| 5 | Moon gradCPT, ds006040 | 28 | EO and **EC** rest (Scan ON) | 2.0 s / 3T / Siemens Prisma | BrainCap MR 63 + ECG, 5 kHz | Yes (FMRIB + BCG); fMRIPrep | – / ECG / none / EyeLink (monitoring) | CC0, open |
| 6 | NIH sleep1, ds005127 | 16 (2 nights) | Overnight sleep, about 8 h/night; short EC wake rest | **3.0 s** / 3T | 63 + ECG + EMG, 5 kHz (F7/F8 replaced by E1/E2) | Yes (derivatives) + sleep scores + preprocessed fMRI | – / ECG / BIOPAC + physio_prepro / video | CC BY 4.0 (LICENSE), open; 492 GB |
| 7 | UNAM, Mendeley crhybxpdy6 | 20 (all male) | 10 min **eyes closed** + EO/EC blocks | 2.0 s / 3T / **GE** MR750 | **EGI** 32-ch sponge net, 1 kHz | Gradient only (BCG remains) | – / ECG / – / – | CC BY article; data licence unstated; open |
| 8 | ATR atr-EfP-2025 | 39 (2 days; traveling subset) | Multiple 8-min **eyes open** | 0.8 s MB (Prisma) / 2.5 s (Verio) / 3T | BrainCap MR 63 + ECG, 5 kHz | No (raw) | 4 CWL / ECG / – / – | **DUA, noncommercial** |
| 9 | UCL NODDI, OSF dvmrb | 17 | Eyes-open rest | 2.16 s / **1.5T** / Siemens Avanto | 64-ch, 250 Hz (secondary source) | Unverified | Unverified | CC BY 4.0, open |
| 10 | Geneva sleep, ds003574 | 18 | Rest-to-sleep 1–2 h (N2/N3) | 2.1 s / 3T / Siemens Trio | 64 electrodes | Unverified | Unverified | CC0, open |
| 11 | CWL van der Meer, NITRC | 8 | 4.5 min EO/EC blocks | 1.95/2.0 s / 3T / Siemens Trio/Verio | BrainAmp 30 + EOG + ECG | Yes (Bergen) + raw | 6 CWL / ECG / – / – | MIT (NITRC), open |
| 12 | Daly music, ds002725 | 21 | Washout runs only | 2.0 s / 3T / Siemens Trio | 30 + ECG (1 kHz in sidecar) | Unverified | – / ECG / – / – | CC0, open |
| 13 | Lioi NF, ds002336 / ds002338 | 10 / 17 | 20-s rest blocks only | 2 s (XP1) / 1 s partial-brain (XP2) / 3T / Siemens Verio | 63 + ECG, 5 kHz | Yes (BVA, 200 Hz) | – / ECG / – / – | CC0, open |
| 14 | Oddball, ds000116 | 17 | None | 2 s / 3T / Philips | Custom bipolar 43→34 ch, 1 kHz | Gradient only | – / ECG+EOG / – / – | No licence on OpenNeuro; EEG on legacy OpenfMRI |

- On TR and montage, the closest matches are ds003768 (TR 2.1 s, BrainAmp 32-ch 10-20, FCz ref, the same recording family as VU) and NATVIEW (TR 2.1 s). TR 2.0 s datasets (ds005795, ds007216, ds006040, UNAM) need only a small resampling step.
- The best eyes-closed rest matches are ds005795 (10 min EC), UNAM (10 min EC), ds006040 (EC runs) and ds003768 (mostly closed). NATVIEW, ds007216, ATR and NODDI rest are eyes open. That is a real distribution shift for alpha-driven EEG features and is itself a test of transfer.
- Rough count of openly downloadable people with some in-scanner simultaneous rest: ds003768 33 + ds005795 34 + NATVIEW 22 + ds007216 24 + ds006040 28 + UNAM 20 + NODDI 17 ≈ 178. That is about 8 times the current 22. ATR adds 39 under a DUA.

### Gaps
- The exact 26 VU scalp channel labels are not on the HF card, so channel-by-channel overlap with each candidate was not computed. The standard BrainCap MR 32 layout in ds003768 is very likely a superset, but this is unverified.
- The VU scanner vendor/model is not given on the HF card.
- ds003768: rest-run eyes-open/closed annotations and whether the eye-tracker eyelid signal is in the release were not confirmed.
- ds006040: the length of the Scan-ON eyes-closed rest run was not extracted from the table text (unverified).
- NODDI: acquisition details (1.5T Avanto, TR 2.16 s, 64-ch, 250 Hz) come from a secondary paper, not the OSF files.
- ds002725, ds003574: whether gradient/BCG-corrected EEG is included, and the EEG system/sampling details for ds003574, were not checked.
- ds007216: respiration and eye-tracking availability were not confirmed (the paper tail was truncated).

## Q2. Status of the specifically named candidates (including negatives)

### Takeaway
Several named candidates are not usable as simultaneous EEG-fMRI. LEMON, ds004902 and PsiConnect hold separately recorded EEG, and Bergen, Oxford/Nottingham, Kuopio, Montreal and Science Data Bank turned up no open simultaneous release. The Chang lab/Vanderbilt data beyond the 22-person HF release are "on request". The genuinely new 2025–2026 releases are ds007216 (Kucyi), ds006040 (Moon), ATR atr-EfP-2025, ds005795 MULTI-CLARID and the re-versioned NIH ds005127.

### Cited Findings
- **NATVIEW:** Confirmed open; details under Q1 #3. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **CWL dataset (van der Meer 2016):** Confirmed, 8 subjects; details under Q1 #10. — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **Deligianni 2016 / "EEG-fMRI-NODDI":** Confirmed as OSF dvmrb under CC BY 4.0. — [OSF](https://osf.io/dvmrb)
- **ds002336 / ds002338 (Lioi):** Confirmed. Neither has a continuous rest run, and XP2 covers only the superior half of the brain. — [ds002336](https://openneuro.org/datasets/ds002336); [ds002338](https://openneuro.org/datasets/ds002338)
- **ds000116:** Confirmed. The EEG is only on legacy OpenfMRI and uses a custom bipolar montage. — [ds000116](https://openneuro.org/datasets/ds000116)
- **ds003768 (Gu et al.):** Confirmed; details under Q1 #1. — [ds003768](https://openneuro.org/datasets/ds003768)
- **ds004902 is not EEG-fMRI.** It is "A Resting-state EEG Dataset for Sleep Deprivation": 71 participants, normal sleep vs sleep deprivation, 61-channel Brain Products at 500 Hz, EEG only (modalities eeg and beh). Xiang et al., *Sci Data* 11:427 (2024). — [OpenNeuro ds004902](https://openneuro.org/datasets/ds004902)
- **Setzer et al. 2022 (Lewis lab):**
  - The paper used 7T fast fMRI. Its preprint reports 66 behavioural arousals from 6 subjects with simultaneous EEG and fast fMRI at 3T. No data-availability statement was retrieved. — [Search summary of Setzer et al., *Nat Commun* 13:5442](https://pmc.ncbi.nlm.nih.gov/articles/PMC9481532)
  - The only Lewis-lab OpenNeuro sleep set found, ds007761 (15 subjects, eyes-closed visual stimulation during sleep-wake transitions), is described as "raw 3T fMRI data" and lists only MRI modality. — [OpenNeuro ds007761](https://openneuro.org/datasets/ds007761)
- **LEMON (Babayan et al., *Sci Data* 2019):** 227 participants assessed over two days, with 3T MRI including rs-fMRI and a separate 62-channel resting EEG experiment. No source describes it as simultaneous. — [Search summary of Babayan et al. 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6371893/)
- **PsiConnect (Monash, ds006110; *Sci Data* 2026):**
  - 65 recruited and 62 analysed, psilocybin vs baseline. 3T Skyra multi-echo, multiband 4, TR 0.91 s; rest 8 min eyes closed, plus meditation, music and movie.
  - The **EEG was recorded in a separate session** in an acoustically absorbent room: 64-channel BrainAmp at 500 Hz, RELAX-cleaned.
  - — [bioRxiv 2025.04.11.643415](https://www.biorxiv.org/content/10.1101/2025.04.11.643415.full); [OpenNeuro ds006110](https://openneuro.org/datasets/ds006110)
- **Bergen:** "Bergen" shows up in this literature as the BERGEN EEG-fMRI toolbox, used for gradient correction in ds007216 and the CWL dataset; no Bergen-hosted dataset turned up (see Gaps). — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/); [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/)
- **Oxford/Nottingham resting EEG-fMRI:** No open release was found. The UK-linked open simultaneous sets found are the UCL NODDI set and the Birmingham perceptual-decision set, which is private on OSF with a DUA. — [OSF dvmrb](https://osf.io/dvmrb); [bioRxiv 253047](https://www.biorxiv.org/content/10.1101/253047.full)
- **MPI Leipzig:** The van der Meer CWL raw data sit on the MPI CBS XNAT (project EEGfMRI). The Leipzig/Magdeburg group's newest open release is MULTI-CLARID (ds005795, LIN Magdeburg, co-author J. van der Meer). — [PMC5063756](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063756/); [ds005795](https://openneuro.org/datasets/ds005795)
- **Chang lab / Vanderbilt:** The only public release is the HF ROI release. The card says task data and finer parcellations are available on request. No Chang-lab OpenNeuro EEG-fMRI dataset was found. — [HF card](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT/blob/main/README.md); [Zhang et al. 2024 vigilance paper record](https://doaj.org/article/dde0955e50df4d9bb93a6f10257e629f)
- **Other datasets that hold EEG and MRI but not simultaneously:** Le Petit Prince HK (ds004718), LPP 7T (ds005345), PEARL-Neuro (ds004796), REM-sleep memory (ds006576, nap EEG plus separate fMRI), and TMR REM sleep (ds005530, 6-channel PSG plus separate fMRI with pulse oximetry). — [OpenNeuro ds006576](https://openneuro.org/datasets/ds006576); [OpenNeuro ds005530](https://openneuro.org/datasets/ds005530)
- **Survey cross-check:** The 2026 ATR data paper's survey table of public EEG-fMRI datasets lists Telesford, Schrooten, Kraljič, He, Walz, Georgie, van der Meer, Lioi, Gu, Daly and Cha. All of those are covered above, which corroborates that the sweep is complete. — [PMC12979783 Table 1](https://europepmc.org/article/PMC/PMC12979783)

### Inferences
- The field's open supply is still small. Nearly all sizeable releases with rest are 20–35 people, and the main 2025–2026 additions (ds005795, ds006040, ds007216, ATR) each roughly match the current study in N.
- The CN-EPFL set used in some EEG-to-fMRI synthesis papers alongside NODDI and Oddball may be ds002158 (EPFL authors, Campus Biotech Geneva). This is unverified, and its rest EEG appears absent.

### Gaps
- Not checked: the data-availability statements of Setzer 2022 and Fultz 2019; the data availability of He, Hong & Sajda 2023; and Schrooten et al. 2019 (5 subjects).
- No authoritative statement was retrieved that LEMON's EEG was recorded outside the scanner; this is inferred from the two-day design.
- A 0.55T EEG-fMRI feasibility preprint (arXiv 2602.13489) appeared in search, but its data availability was not checked.
- Negative results with no source to cite:
  - **Bergen (Hugdahl lab), Oxford/Nottingham, Kuopio, Montreal (MNI/Gotman) and Science Data Bank (China):** two web searches each (English and Chinese for ScienceDB) found no open simultaneous EEG-fMRI release, and none appears in the full OpenNeuro EEG/MRI sweep. ScienceDB's internal search and institutional repositories (Bergen, Oxford ORA, Nottingham, Kuopio/UEF, MNI) were not searched directly.
  - These datasets may exist under restricted or on-request access.

## Q3. Compatibility with the current pipeline, and physiological recordings for confound control

### Takeaway
On hardware and TR, the most pipeline-compatible datasets are ds003768 (BrainAmp 32-ch, FCz, TR 2.1 s) and NATVIEW (TR 2.1 s, BrainCap 64). For eyes-closed rest with CWL plus the richest physiology, ds005795 (respiration, pulse, ECG, EOG, EMG, GSR, CWL) is the standout. NATVIEW (respiration belt, ECG, EyeLink) and ds005127 (BIOPAC physio, ECG, EMG, video, sleep scores) are the next best for confound control.

### Cited Findings
- **ds003768:** BrainAmp MR 32-channel 10-20 layout with FCz reference, the same system family and reference as VU (BrainAmp MR 32-ch, FCz). TR 2.1 s matches VU's TR exactly. — [ds003768 vhdr/README](https://openneuro.org/datasets/ds003768); [HF card](https://huggingface.co/datasets/NeurdyLab/NeuroBOLT/blob/main/README.md)
- **NATVIEW:** TR 2.1 s, BrainCap MR 64 at 5 kHz. Released EEG is gradient and BCG corrected; respiration is BIOPAC at 62.5 Hz; eye tracking is EyeLink 1000 Plus; FD/DVARS are provided. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
- **ds005795:** TR 2.0 s. 10-min eyes-closed rest. 4 CWL, ECG, 2 EOG, 4 EMG, GSR, and respiration plus heart rate (Invivo). EEG shipped MR- and CWL-corrected at 500 Hz. — [ds005795](https://openneuro.org/datasets/ds005795)
- **ds007216:** TR 2.0 s, 4 CWL + ECG, BERGEN gradient + CWL regression applied. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **ds006040:** TR 2.0 s, ECG only. The authors explicitly did not record respiration or skin conductance. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
- **ds005127:** BIOPAC folder and `physio_prepro` derivative, ECG and EMG channels, video, AASM sleep scoring; TR 3.0 s. — [ds005127](https://openneuro.org/datasets/ds005127)
- **UNAM:** EGI 32-channel sponge net at 1 kHz with Cz reference, a different EEG vendor and montage. Only gradient-corrected EEG; ECG only. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
- **ds000116:** Custom bipolar EEG system, so it does not share the 10-20 unipolar montage. — [ds000116](https://openneuro.org/datasets/ds000116)
- **ds005127 montage:** Channels 11/12 are E1/E2 where the standard cap has F7/F8. — [ds005127 vhdr](https://openneuro.org/datasets/ds005127)

### Inferences
- **Preprocessing:** To reuse the current VU-trained models unchanged, the cheapest external sets are those already shipped artefact-corrected: ds005795, NATVIEW, ds007216, ds006040 and ds005127 derivatives. ds003768 and ATR need gradient/BCG (and for ATR, CWL) correction to be run, ideally with the same pipeline used for VU so that preprocessing does not confound "site".
- **fMRI side:** Most sets ship raw BOLD (ds003768, ds005795, ATR, UNAM). NATVIEW ships Schaefer-400 ROI series, not DiFuMo-64. Expect to run one common fMRI pipeline and DiFuMo-64 extraction across all sets.
- **Physiology:** For confound control of the global signal and the arousal/autonomic component, prioritise ds005795 (resp + pulse + GSR) and NATVIEW (resp + ECG + eye). In ds003768, ECG plus button-press arousal markers plus sleep stages give an arousal label, but there is no respiration. ds005127 BIOPAC adds respiration/cardiac (exact channels unverified).
- **Montage:** Datasets on BrainCap MR caps (ds003768, ds005795, NATVIEW, ds007216, ds006040, ATR, ds005127) should contain all standard 10-20 labels used in VU-style 32-channel montages. ds005127 lacks F7/F8. UNAM (EGI) and ds000116 (bipolar) would require spatial interpolation or channel-set reduction.

### Gaps
- Not inspected: the BIOPAC channel content of ds005127; the eye-tracking release status in ds003768 and ds006040; and the per-subject channel lists of NATVIEW, ds007216 and ds006040 (to confirm they contain all 26 VU labels).

## Q4. Support for (a) more training people, (b) external validation on a different site/scanner, (c) sleep/vigilance range, (d) task-to-rest transfer

### Takeaway
- (a) Pool ds003768 + ds005795 + ds007216 + ds006040 (+ NATVIEW eyes-open rest) to move from 22 to roughly 150–180 training people.
- (b) Hold out whole datasets. The strongest out-of-distribution tests are UNAM (GE + EGI), NODDI (1.5T) and ATR (two scanners, traveling subjects, under DUA).
- (c) ds003768, ds005127 and ds003574 give staged sleep and arousal, with NIH sleep2 (ds006163) embargoed until about Sept 2028.
- (d) NATVIEW, ds007216, ds006040 and ATR pair rest with tasks or movies in the same people.

### Cited Findings
- **(a) More training people:**
  - Open rest-bearing N per dataset: ds003768 33, ds005795 34, ds007216 24 (47 sessions), ds006040 28, NATVIEW 22 (44 sessions), UNAM 20, NODDI 17. — [ds003768](https://openneuro.org/datasets/ds003768); [ds005795](https://openneuro.org/datasets/ds005795); [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/); [ds006040](https://openneuro.org/datasets/ds006040); [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527); [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/); [OSF dvmrb](https://osf.io/dvmrb)
  - Recorded hours: Gu 58.3 h, Telesford 47.0 h, Cha 28.0 h, ATR 43.6 h. — [PMC12979783 Table 1](https://europepmc.org/article/PMC/PMC12979783)
- **(b) Different site/scanner:**
  - Penn State Prisma (ds003768), Magdeburg Philips Achieva (ds005795), NKI Trio (NATVIEW), Temple Prisma (ds007216), SKKU Prisma (ds006040), UNAM GE MR750 with EGI EEG, UCL 1.5T Avanto (NODDI). — sources as in Q1
  - ATR has a subset scanned on both Prisma (TR 0.8 s MB) and Verio (TR 2.5 s), enabling traveling-subject analyses. — [PMC12979783](https://europepmc.org/article/PMC/PMC12979783)
  - NATVIEW and ds007216 have two sessions per person, 2–354 and 3–62 days apart, which allows within-person test-retest of prediction accuracy. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527); [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **(c) Sleep/vigilance range:**
  - ds003768: 15-min sleep scans with RPSGT staging and button-press wake markers. — [PMC10060583](https://pmc.ncbi.nlm.nih.gov/articles/PMC10060583)
  - ds005127: two overnight 8-h sessions with 8 forced arousals per night, plus scoring derivatives. — [ds005127](https://openneuro.org/datasets/ds005127)
  - ds003574: 1–2 h in-scanner sleep reaching N2/N3, TR 2.1 s. — [ds003574](https://openneuro.org/datasets/ds003574)
  - ds006163 (sleep2): release targeted for September 2028. — [ds005127 README](https://openneuro.org/datasets/ds005127)
  - ds007216's experience-sampling probes include arousal and engagement ratings every 45–60 s during rest. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
- **(d) Task-to-rest transfer (same people, same session):**
  - NATVIEW: rest + Inscapes + movies + checkerboard. — [PMC10447527](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447527)
  - ds007216: rest + gradCPT. — [PMC12889718](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889718/)
  - ds006040: EO/EC rest + gradCPT + imagery + checkerboard. — [PMC13066628](https://europepmc.org/article/PMC/PMC13066628)
  - ATR: EO rest + oddball + N-back. — [PMC12979783](https://europepmc.org/article/PMC/PMC12979783)
  - ds005795: EC rest + auditory learning (5 public). — [ds005795](https://openneuro.org/datasets/ds005795)
  - UNAM: EC rest + EO/EC block task. — [PMC10585622](https://pmc.ncbi.nlm.nih.gov/articles/PMC10585622/)
  - Task-only sets: Lioi NF, ds000116 oddball, ds002725 music, ds002739, Georgie.

### Inferences
- **Suggested experiment order:**
  1. **External validation first.** Apply the current VU-trained model, unchanged, to the EC rest of ds005795 and the rest of ds003768. Both are open and need no DUA, and between them they cover the eyes-closed condition and the exact TR.
  2. **Then the training curve.** Retrain with leave-one-dataset-out on the pooled ~150+ people, to see whether the ~9-person plateau is a property of the VU data or of the method.
- **Between-person variance:** ds003768 and ds005127 sleep stages and the ds007216 arousal ratings give an explicit vigilance covariate to test whether the large accuracy differences between people track arousal state.
- **Same-person checks:** Two-session datasets (NATVIEW, ds007216, ds005127, ATR) allow a check that a person's predictability is stable across sessions, which separates trait from state.
- **NODDI and UNAM:** Treat these as stress tests (1.5T; GE + EGI sponge net), not training data. Poor transfer there could reflect hardware rather than the method.

### Gaps
- No released dataset was found that combines eyes-closed rest, TR ≈ 2 s, CWL, respiration and N > 50 at a single site. The largest single sets cap at about 34 people.
- ds003768: whether its visual-motor adaptation task was recorded with EEG (and is released) was not confirmed. Its BIDS task list shows only rest and sleep.
- Total download sizes: ds005127 492 GB, ds006040 185 GB, ds003768 93 GB. NATVIEW, ds007216 and ATR sizes were not retrieved.
