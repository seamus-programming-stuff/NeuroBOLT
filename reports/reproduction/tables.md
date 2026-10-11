## Table 1, NeuroBOLT rows (mean ± SD of per-scan Pearson R)

| Setting | Source | Cuneus | Heschl's gyrus | Middle frontal | Precuneus anterior | Putamen | Thalamus | Global signal | Avg. R |
|---|---|---|---|---|---|---|---|---|---|
| Intra-scan | Paper | 0.588 ± 0.166 | 0.566 ± 0.183 | 0.502 ± 0.168 | 0.559 ± 0.141 | 0.437 ± 0.184 | 0.480 ± 0.213 | 0.587 ± 0.162 | 0.531 |
| Intra-scan | Ours (29 scans) | 0.480 ± 0.276 | 0.420 ± 0.331 | 0.290 ± 0.334 | 0.401 ± 0.323 | 0.253 ± 0.237 | 0.273 ± 0.268 | 0.521 ± 0.201 | 0.377 |
| Inter-subject | Paper | 0.482 ± 0.100 | 0.561 ± 0.046 | 0.423 ± 0.115 | 0.496 ± 0.136 | 0.335 ± 0.144 | 0.453 ± 0.106 | 0.564 ± 0.115 | 0.473 |
| Inter-subject | Ours (6 held-out scans) | 0.464 ± 0.113 | 0.524 ± 0.042 | 0.429 ± 0.103 | 0.489 ± 0.116 | 0.332 ± 0.144 | 0.464 ± 0.104 | 0.550 ± 0.110 | 0.465 |
| Inter-subject | Authors' checkpoints, EEG high-pass on | 0.404 ± 0.123 | 0.442 ± 0.060 | 0.412 ± 0.104 | 0.491 ± 0.126 | 0.334 ± 0.149 | 0.456 ± 0.106 | 0.516 ± 0.086 | 0.437 |
| Inter-subject | Authors' checkpoints, EEG high-pass off | 0.481 ± 0.100 | 0.561 ± 0.046 | 0.423 ± 0.115 | 0.496 ± 0.136 | 0.335 ± 0.144 | 0.453 ± 0.106 | 0.564 ± 0.115 | 0.473 |

## 95% confidence intervals for our means (t-interval across scans)

| Setting | Cuneus | Heschl's gyrus | Middle frontal | Precuneus anterior | Putamen | Thalamus | Global signal |
|---|---|---|---|---|---|---|---|
| Intra-scan | 0.375 to 0.585 ✱ | 0.294 to 0.546 ✱ | 0.163 to 0.417 ✱ | 0.278 to 0.524 ✱ | 0.162 to 0.343 ✱ | 0.171 to 0.375 ✱ | 0.445 to 0.598 |
| Inter-subject | 0.345 to 0.583 | 0.480 to 0.568 | 0.321 to 0.537 | 0.367 to 0.611 | 0.181 to 0.484 | 0.354 to 0.573 | 0.435 to 0.666 |

✱ the paper's mean lies outside our 95% CI.

## Intra-scan mean R by epoch-selection rule (29 scans)

| Rule | Cuneus | Heschl's gyrus | Middle frontal | Precuneus anterior | Putamen | Thalamus | Global signal | Avg. R | RMS gap to paper |
|---|---|---|---|---|---|---|---|---|---|
| Paper | 0.588 ± 0.166 | 0.566 ± 0.183 | 0.502 ± 0.168 | 0.559 ± 0.141 | 0.437 ± 0.184 | 0.480 ± 0.213 | 0.587 ± 0.162 | 0.531 | |
| min val MSE (main.py) | 0.480 ± 0.276 | 0.420 ± 0.331 | 0.290 ± 0.334 | 0.401 ± 0.323 | 0.253 ± 0.237 | 0.273 ± 0.268 | 0.521 ± 0.201 | 0.377 | 0.162 |
| max val R | 0.414 ± 0.254 | 0.457 ± 0.301 | 0.337 ± 0.315 | 0.319 ± 0.377 | 0.235 ± 0.278 | 0.294 ± 0.238 | 0.504 ± 0.259 | 0.366 | 0.173 |
| last epoch | 0.476 ± 0.303 | 0.477 ± 0.297 | 0.358 ± 0.268 | 0.405 ± 0.313 | 0.330 ± 0.217 | 0.324 ± 0.237 | 0.560 ± 0.185 | 0.419 | 0.120 |
| max test R (oracle) | 0.603 ± 0.186 | 0.581 ± 0.193 | 0.512 ± 0.184 | 0.549 ± 0.168 | 0.445 ± 0.167 | 0.483 ± 0.177 | 0.630 ± 0.124 | 0.543 | 0.019 |
| min val MSE, only the 6 inter-subject test scans | 0.631 ± 0.128 | 0.652 ± 0.143 | 0.455 ± 0.426 | 0.627 ± 0.159 | 0.298 ± 0.356 | 0.467 ± 0.310 | 0.594 ± 0.278 | 0.532 | 0.071 |

Share of intra-scan runs with negative test R (min val MSE): Cuneus 14%, Heschl's gyrus 14%, Middle frontal 24%, Precuneus anterior 10%, Putamen 17%, Thalamus 14%, Global signal 0%; overall 13%.
Median selected epoch (of 0-29): Cuneus 14, Heschl's gyrus 9, Middle frontal 13, Precuneus anterior 11, Putamen 10, Thalamus 10, Global signal 13.

## Figure 5 recreation: the paper's scans, our models

| ROI | Scan (as in paper) | Paper R | Our R (block-bootstrap 95% CI) | Interval half-width (model scale) | Coverage, this scan | Coverage, all 6 test scans (model scale) | MC-dropout band coverage |
|---|---|---|---|---|---|---|---|
| Cuneus | sub21-scan01 | 0.548 | 0.523 (0.42 to 0.62) | ±1.24 (±0.95) | 99% | 98% (97%) | 3% |
| Heschl's gyrus | sub07-scan01 | 0.570 | 0.491 (0.38 to 0.59) | ±1.10 (±0.91) | 97% | 97% (96%) | 2% |
| Middle frontal | sub16-scan01 | 0.465 | 0.451 (0.34 to 0.55) | ±1.20 (±0.94) | 99% | 98% (95%) | 1% |
| Precuneus anterior | sub07-scan02 | 0.529 | 0.527 (0.42 to 0.62) | ±1.20 (±0.96) | 98% | 98% (97%) | 2% |
| Putamen | sub07-scan02 | 0.427 | 0.397 (0.32 to 0.47) | ±1.26 (±0.96) | 98% | 97% (95%) | 2% |
| Thalamus | sub11-scan01 | 0.427 | 0.444 (0.34 to 0.55) | ±1.20 (±0.97) | 97% | 98% (97%) | 2% |
| Global signal | sub11-scan01 | 0.615 | 0.595 (0.50 to 0.67) | ±1.12 (±0.95) | 99% | 98% (97%) | 3% |
