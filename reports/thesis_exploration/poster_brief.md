# Poster brief: when can EEG support individual BOLD inference?

**Final brief; results reviewed 21 October 2026.** Preserve the **exact example2 layout already built**, its geometry and reading order. Use original content; copy no reference-example copyright material.

**Opening message.** Development gains coexist with weak secondary external transfer, compressed amplitudes and limited coverage. Clinical accuracy remains unestablished. The CS question is supported information, transferable estimation and abstention.

**Reference architecture.** Redraw the [actual UnEBOLT schematic](https://raw.githubusercontent.com/mlresearch/v315/main/assets/li26g/li26g.pdf): encoder, ROI-conditioned adapters and prediction heads; attribute and verify arrows. Label it a published reference; the tested ridge/MLP are separate. **UnEBOLT ≠ UniEFS.**

**Model→use-case panel.** Published cards: UnEBOLT, 64-ROI temporal r **.418 ± .036**, VU 22 people/29 scans, healthy auditory transfer; UniEFS, 512-ROI **.367 ± .052**, paired **29 people/39 scans**, pretrained decoder/context; MARBLE, 64-ROI **.434 ± .047**, VU 22/29, Mamba/attention, no external cohort. These are SDs, **not a leaderboard**; targets differ and VU is reused. Mark feedback, state-estimation and representation application arrows as hypotheses. ([UnEBOLT](https://proceedings.mlr.press/v315/li26g.html), [UniEFS](https://proceedings.mlr.press/v306/li26gp.html), [MARBLE](https://papers.miccai.org/miccai-2026/0612-Paper4437.html))

UniEFS's PD probe validates an EEG representation without paired patient BOLD. Prism's narrow adjunctive PTSD clearance and rehabilitation evidence from actual EEG-fMRI/EEG feedback do not validate these models or diagnostic substitution. Trained-weight access remains incomplete. ([FDA](https://www.accessdata.fda.gov/cdrh_docs/pdf22/K222101.pdf), [stroke trial](https://doi.org/10.1186/s12984-025-01598-9))

**Methods.** ds006040: **27 people/54 runs**; nine completed jobs, ten synthetic tests and frame/group/hash checks. **96 outer cells reuse the cohort.** EEG arms consume **300 power features**, not waveforms. Cross 4/12 people ×120/240 seconds ×EEG/ECG/combined ×ridge/MLP; grouped tests, inner tuning/calibration, person CIs and preselected panels. Published models were not reproduced. ([Record](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Clinical EEG fMRI thesis exploration/M3 experiments.md>))

**Primary chart: EC→EC, 12 people/240 seconds, regional64.** Plot all fixed arms with 95% person CIs; label r separately from predictive R². Use the [prespecified CSV](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/poster_scores.csv>).

| Arm | r [95% CI] | Predictive R² |
|---|---:|---:|
| Ridge EEG | .1886 [.1488, .2265] | .02788 |
| ECG timing/availability | .0177 [−.0082, .0438] | −.00441 |
| Combined ridge | .1782 [.1388, .2163] | .02309 |
| MLP EEG | .1223 [.0803, .1647] | .00678 |

**Learning chart.** Ridge EEG r: 4/120=.0889; 4/240=.1445; 12/120=.1419; 12/240=.1886. More people at 240 seconds: **Δr +.0441 [.0237, .0628]**; more time at 12 people: **+.0467 [.0236, .0711]**. Retained time also changes state/content; one subset order/seed supplies no ceiling. Use the [fixed learning CSV](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/data/poster_learning.csv>).

**Regional/error panel.** Predicted-global template r=.1845; full-regional increment **+.00410 [−.00813, .01680]** is uncertain. Residual r=.0905 but R²=−.00047; regional-contrast R²=−.00789. EEG amplitude ratio=.1615; **5/27** EC people and **28.5%** of person-region pairs had negative R²; **15/27** EO people were negative. Include calibrated R² and zero undefined primary correlations in the supporting caption.

**Condition panel.** EC-trained EO r=.1190 versus EC .1886. Equal-budget mixed EC+EO training raised EO to .1412, **Δr +.0222 [.00518, .04054]**, while EC fell to .1421. This is a within-site condition tradeoff, not an arousal/site claim.

Past-only features inherit retrospective processing. Sparse unannotated ECG validity median **.3918** limits physiology inference. MLP objectives differ from ridge. Neural work: **1m48s**, 96 candidate fits, **73.9 MB** allocated GPU peak, no checkpoints; costs do not establish clinical requirements.

**NATVIEW: strict failure, secondary amendment.** V1 rejected **7/8**; sub-12 alone supplies no population accuracy. The pilot is excluded. V2's metadata-only adapter was frozen after v1 exposure, before new predictions; **it is not the original untouched confirmation**. Model/scalers/geometry/QC gates stayed fixed. All eight clocks resolve; six pass minimum60 frames, while 05/10 retain only 4/23. **740/2,304 frames scored, 32.12%**; 767/2,304=33.29% includes their unscored frames.

**External chart: conditional six-person means, 10,000 person resamples.** Regional **r .1038 [−.0002, .2071]**, predictive **R² −.0714 [−.1064, −.0301]**, amplitude=.1492. Global r=.1249 [−.0330, .2760], R²=−.0431; residual r=.0248 [−.0050, .0546], R²=−.0722. All mean-r intervals include zero; **5/6** people have negative regional R². Its benchmark is the retained target mean, not neural variance or clinical performance. Individual intervals use 2,000 stationary-bootstrap replicates with 21-second expected blocks, restarting at gaps. ([Verified summary](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/reports/thesis_exploration/natview/v2/machine_summary.json>))

VU-only training: **22 people/29 scans; 12,144 features, 23 target sites ×44×12**, old26-channel selector. These are not 23 measured sites: TP9′/TP10′ always require interpolation; three people need additional splines. Reference/cleaning/mask/MNI/feature differences prevent interpreting M3/NATVIEW score subtraction as a site effect. Physiology supports clocks/QC; pilot eyes are 76.4% interpolated, not arousal labels. QC losses establish no ceiling.

**Three work packages.** WP1: target-aware measurement design. WP2: time-aware missing-observation dynamics, operator/montage adaptation and counted calibration versus fixed-window ridge. First test raw shared-montage/reference harmonization: a future engineering baseline, not novelty alone; no extra arm ran. WP3: selective prediction under explicit shift assumptions and useful coverage. Each needs prior-art comparison and fails without supported added value.

**Next steps.** MR/EEG experts verify physical operators; clinicians define independent ground truth and tolerances. Conditional wakefulness support must beat direct EEG; no advisory prototype was validated. One-ROI feedback requires paired patient target engagement and intervention evidence. Cohort/model brackets are proposals, not thresholds. Completed jobs, immutable versions and [provenance](<C:/Users/Seamus/Documents/GitHub/NeuroBOLT/research_notes/Clinical EEG fMRI thesis exploration/NATVIEW experiments.md>) support the findings, not clinical deployment.
