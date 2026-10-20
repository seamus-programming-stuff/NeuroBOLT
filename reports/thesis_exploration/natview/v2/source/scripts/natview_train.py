#!/usr/bin/env python3
"""Retrain VU ridge on the fixed common23 bridge, with existing all26 selector."""
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from eval_inter_per_scan import CH_NAMES
from ext_transfer import fit_fixed, vu_alphas
from natview_stage import digest, save_json

OUT = Path('reports/thesis_exploration/natview')
SCRATCH = Path('/scratch/hz18/stay0060/NeuroBOLT')
COMMON = [c for c in CH_NAMES if c not in ['F4', 'FT9', 'FT10']]


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Use SLURM'
    torch.set_num_threads(int(os.environ['SLURM_CPUS_PER_TASK']))
    eegpath = SCRATCH/'checkpoints/learning_curve/features_fine_w24_sub12.npz'
    auxpath = SCRATCH/'checkpoints/interp/interp_cache.npz'
    cvpath = SCRATCH/'checkpoints/interp/cv_A/scores.csv'
    eeg, aux = np.load(eegpath), np.load(auxpath)
    labels = list(aux['labels'].astype(str)); scans = list(aux['scans'].astype(str))
    idx = [CH_NAMES.index(c) for c in COMMON]
    x = np.concatenate([eeg['x_'+s].reshape(-1,26,44,12)[:,idx].reshape(-1,23*44*12) for s in scans])
    y = np.concatenate([aux['y_all_'+s] for s in scans])
    assert np.isfinite(x).all() and np.isfinite(y).all() and len(labels) == 65
    alphas = vu_alphas(cvpath, labels)[('full','all65')]
    mean, sd = x.mean(0), x.std(0)+1e-8
    gi=labels.index('global signal clean'); ri=[j for j in range(65) if j!=gi]
    beta=np.linalg.lstsq(np.c_[np.ones(len(y)),y[:,gi]],y[:,ri],rcond=None)[0]
    print('FIT common23',x.shape,y.shape,'all26 selector',alphas.tolist(),flush=True)
    weights, intercept = fit_fixed((x-mean)/sd,y,alphas)
    model=SCRATCH/'checkpoints/ext/natview/vu_common23_frozen.npz'
    np.savez_compressed(model,weights=weights,intercept=intercept,mean=mean,sd=sd,alphas=alphas,
                        labels=np.array(labels),channels=np.array(COMMON),global_beta=beta)
    save_json(OUT/'model_training.json',{'model_path':str(model),'model_sha256':digest(model),
              'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'slurm_job_id':os.environ['SLURM_JOB_ID'],
              'training_scans':scans,'training_people':sorted(set(s.split('-')[0] for s in scans)),
              'n_training_rows':len(y),'channels':COMMON,'dropped_vu_channels':['F4','FT9','FT10'],
              'selector':'existing all26 VU cv_A, geometric median selected alpha over five folds, per target; no NATVIEW selection',
              'alpha_per_target':alphas.tolist(),'labels':labels,'n_outputs':65,
              'feature_definition':'baseline_ridge.band_power_features: microvolts, 24s history, 44 one-Hz bins, 12 two-second lags',
              'residual_definition':'predicted regional minus VU fitted intercept/global coefficient times predicted global; measured targets use the identical VU coefficients',
              'source_hashes':{str(p):digest(p) for p in [eegpath,auxpath,cvpath,Path(__file__),
                                Path('scripts/baseline_ridge.py'),Path('scripts/ext_transfer.py'),Path('scripts/interp_build_cache.py')]}})
    print('FROZEN MODEL',digest(model),flush=True)


if __name__=='__main__':
    main()
