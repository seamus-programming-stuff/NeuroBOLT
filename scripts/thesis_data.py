#!/usr/bin/env python3
"""Auditable ds006040 inventory and strictly past-context local feature extraction.

This only adds derivatives; original recordings and old caches are read-only.
The source EEG artifact removal and the cached fMRI targets remain retrospective.
"""
import argparse
import glob
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.signal import butter, find_peaks, lfilter, sosfilt, welch

CHANNELS = ['FP1','FP2','F3','F4','C3','C4','P3','P4','O1','O2','F7','F8','T7','T8','P7','P8','FPZ','FZ','CZ','PZ','POZ','OZ','FT9','FT10','TP9','TP10']
RENAME = {'Fp1':'FP1','Fp2':'FP2','Fpz':'FPZ','Fz':'FZ','Cz':'CZ','Pz':'PZ','POz':'POZ','Oz':'OZ'}
REGIONS = [['FP1','FP2','FPZ','F3','F4','F7','F8','FZ'],['C3','C4','CZ'],['T7','T8','FT9','FT10','TP9','TP10'],['P3','P4','P7','P8','PZ'],['O1','O2','OZ','POZ']]
BANDS = [(1,4),(4,8),(8,13),(13,30),(30,45)]


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False,
                                   default=lambda x:x.item() if isinstance(x,np.generic) else str(x)) + '\n', encoding='utf-8')


def causal_downsample(data, sfreq):
    """One-pass anti-alias filter followed by integer decimation; never zero phase."""
    factor = int(round(sfreq / 200))
    if abs(sfreq / factor - 200) > 1e-6:
        raise ValueError('Only integer conversion to 200 Hz is audited')
    low = butter(6, 70, fs=sfreq, btype='lowpass', output='sos')
    return sosfilt(low, data, axis=-1)[..., ::factor]


def causal_hr(ecg, fs=200):
    """Online-confirmable energy peaks. RR is available only after the second peak.

    Fixed algorithm, no whole-record threshold, interpolation, peak-distance
    optimization, backfill, or ECG spectral predictors. Confirm local peaks after
    100 ms, then accept sequentially with a 300 ms refractory period.
    """
    z = sosfilt(butter(3, [5,25], fs=fs, btype='bandpass', output='sos'), ecg)
    env = lfilter(np.ones(int(.08*fs))/(int(.08*fs)), [1], z*z)
    a = 1 - np.exp(-1 / (8*fs))
    avg = lfilter([a], [1, -(1-a)], env)
    var = np.maximum(lfilter([a], [1, -(1-a)], env*env) - avg*avg, 0)
    delay = int(.1*fs)
    candidates = np.flatnonzero((env[1:-1] > env[:-2]) & (env[1:-1] >= env[2:])) + 1
    peaks, last = [], -int(fs)
    for p in candidates:
        if p < fs or p+delay >= len(env) or p-last < .3*fs:
            continue
        # The rightmost sample accessed is p+delay, the availability time.
        if env[p] < avg[p] + 2*np.sqrt(var[p]) or env[p] < env[max(0,p-delay):p+delay+1].max():
            continue
        peaks.append(p)
        last = p
    hr = np.full(len(ecg), np.nan)
    updates = []
    for prev, p in zip(peaks[:-1], peaks[1:]):
        rate = 60*fs/(p-prev)
        updates.append((p+delay, rate if 35 <= rate <= 160 else np.nan))
    for i, (at, rate) in enumerate(updates):
        stop = min(updates[i+1][0] if i+1 < len(updates) else len(hr), at+int(3*fs))
        hr[at:stop] = rate
    return hr, {'confirmed_peaks': len(peaks), 'valid_fraction': float(np.isfinite(hr).mean()),
                'median_hr': float(np.nanmedian(hr)) if np.isfinite(hr).any() else None}


def window_features(eeg, hr, endpoint, fs=200):
    """24 seconds strictly before endpoint; five regions x bands x 12 lags."""
    end = int(np.floor(endpoint*fs))
    start = end-24*fs
    if start < 0 or end > eeg.shape[1]:
        raise ValueError('Incomplete context')
    pieces = eeg[:,start:end].reshape(len(CHANNELS),12,2*fs)
    freq, psd = welch(pieces, fs=fs, nperseg=fs, axis=-1)
    logs = np.stack([np.log(np.maximum(psd[..., (freq>=lo)&(freq<hi)].mean(-1),1e-24)) for lo,hi in BANDS], axis=1)
    x = np.stack([logs[[CHANNELS.index(c) for c in reg]].mean(0) for reg in REGIONS]).reshape(-1)
    hh = hr[start:end].reshape(12,-1)
    valid = np.isfinite(hh)
    counts = valid.sum(1)
    rates = np.divide(np.nansum(hh,1), counts, out=np.full(12,np.nan), where=counts>0)
    phys = np.concatenate([rates, valid.mean(1)])
    return x.astype('float32'), phys.astype('float32')


def raw_path(root, run):
    sub, condition = run.split('_')
    return root/f'derivatives/{sub}/eeg/{sub}_task-{condition}ON_run-1_desc-anc0qrsrm_eeg.set'


def inventory(root, cache, out):
    import mne
    mne.set_log_level('ERROR')
    rows, labels = [], None
    for cp in sorted(cache.glob('chunk*.npz')):
        z = np.load(cp)
        labels = z['labels'].tolist()
        for run in z['runs'].astype(str):
            p = raw_path(root,run)
            frame = z[f'frame_{run}']
            raw = mne.io.read_raw_eeglab(str(p),preload=False,verbose=False)
            rows.append({'run':run,'subject':run.split('_')[0],'condition':run.split('_')[1],
                         'cache':str(cp),'cache_frames':len(frame),'first_frame':int(frame.min()),'last_frame':int(frame.max()),
                         'raw_set':str(p),'channels':raw.ch_names,'sfreq':raw.info['sfreq'],
                         'raw_samples':int(raw.n_times),'raw_seconds':float(raw.n_times/raw.info['sfreq']),
                         'ecg_names':[c for c in raw.ch_names if 'ECG' in c.upper() or 'EKG' in c.upper()],
                         'marker_counts':{s:int(sum(raw.annotations.description==s)) for s in set(raw.annotations.description)},
                         'files':[{'path':str(f),'bytes':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns} for f in (p,p.with_suffix('.fdt'),p.with_suffix('.json')) if f.exists()]})
    manifest={'dataset':'ds006040','scope':'previously inspected development dataset; no final external test',
              'runs':rows,'n_people':len(set(r['subject'] for r in rows)),'n_runs':len(rows),
              'labels':labels,'history_seconds':24,'TR_seconds':2,
              'new_release_staged':False,'independent_arousal_labels_staged':False,
              'input_plan':'real ECG timing only; no ECG/EOG EEG-band power; no respiration/CO2 inferred',
              'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    save_json(out/'manifest_inventory.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('runs','labels')},indent=2),flush=True)
    print('CHANNELS',rows[0]['channels'],flush=True)


def build(root, cache, out):
    import mne
    mne.set_log_level('ERROR')
    inv=json.loads((out/'manifest_inventory.json').read_text())
    arrays, qc, failed = {}, [], []
    chunk = None
    for row in inv['runs']:
        run=row['run']; started=time.monotonic()
        try:
            if chunk != row['cache']:
                z=np.load(row['cache']); chunk=row['cache']
            raw=mne.io.read_raw_eeglab(row['raw_set'],preload=False,verbose=False)
            raw.rename_channels({k:v for k,v in RENAME.items() if k in raw.ch_names})
            if len(row['ecg_names']) != 1:
                raise ValueError('Exactly one independently named ECG channel required')
            picks=CHANNELS+row['ecg_names']
            data=raw.get_data(picks=picks)
            bad=~np.isfinite(data).all(0)
            data[:,bad]=0
            down=causal_downsample(data,raw.info['sfreq']); del data
            eeg=sosfilt(butter(3,.5,fs=200,btype='highpass',output='sos'),down[:-1],axis=-1)
            hr, hqc=causal_hr(down[-1])
            marker=raw.annotations.onset[raw.annotations.description=='TR']
            boundaries=raw.annotations.onset[np.array(['boundary' in s.lower() for s in raw.annotations.description])]
            frame=z[f'frame_{run}']; y=z[f'y_{run}']
            if len(marker) != 190:
                raise ValueError(f'Unexpected marker count {len(marker)}')
            xs, ps, ys, fs, ons, fds = [], [], [], [], [], []
            bad_prefix=np.r_[0,np.cumsum(bad)]
            for i,fr in enumerate(frame):
                endpoint=float(marker[fr])
                # 30-second startup + 24-second strict history; 6-second
                # past-only margin after missing samples for filter recovery.
                if endpoint < 30 or endpoint*200 > eeg.shape[1]:
                    continue
                if np.any((boundaries >= endpoint-30) & (boundaries < endpoint)):
                    continue
                lo=max(0,int((endpoint-30)*row['sfreq'])); hi=min(len(bad),int(endpoint*row['sfreq']))
                if bad_prefix[hi] != bad_prefix[lo] or not np.isfinite(y[i]).all():
                    continue
                x,p=window_features(eeg,hr,endpoint)
                xs.append(x);ps.append(p);ys.append(y[i]);fs.append(fr);ons.append(endpoint);fds.append(z[f'fd_{run}'][i])
            if len(xs)<120:
                raise ValueError(f'Fewer than 120 jointly eligible frames: {len(xs)}')
            for name,a in [('eeg',xs),('phys',ps),('y',ys),('frame',fs),('onset',ons),('fd',fds)]:
                arrays[f'{name}_{run}']=np.array(a,dtype='int32' if name=='frame' else 'float32')
            qc.append({**{k:row[k] for k in ('run','subject','condition','cache_frames')},'frames':len(xs),
                       'first_frame':int(fs[0]),'last_frame':int(fs[-1]),'first_onset':ons[0],'last_onset':ons[-1],
                       'missing_raw_fraction':float(bad.mean()),'boundary_events':int(len(boundaries)),'hr':hqc,'seconds':time.monotonic()-started,
                       'eeg_features':300,'phys_features':24,'mean_fd':float(np.mean(fds))})
            print('BUILT',run,len(xs),hqc,'seconds',round(time.monotonic()-started,2),flush=True)
        except Exception as e:
            failed.append({'run':run,'error':repr(e)})
            print('FAILED',run,repr(e),flush=True)
    # Complete EC/EO pairs only: same people and eligibility across all arms.
    people=sorted({r['subject'] for r in qc if all(any(q['run']==r['subject']+'_'+c for q in qc) for c in ('EC','EO'))})
    runs=[p+'_'+c for p in people for c in ('EC','EO')]
    arrays={k:v for k,v in arrays.items() if any(k.endswith('_'+r) for r in runs)}
    np.savez_compressed(out/'features_causal.npz',runs=np.array(runs),labels=np.array(inv['labels']),**arrays)
    save_json(out/'feature_qc.json',{'runs':qc,'failed':failed,'people_complete_pairs':people,
              'input_feature_causality':'one-pass anti-alias/highpass, strict preceding 24 s, confirmed RR forward-hold; no future normalization',
              'retrospective_limitations':['authors gradient/BCG correction causality not established','fMRI motion/trend regression, zero-phase lowpass and whole-run percentile normalization inherited from old cache','inherited cached frame QC includes a future gap margin; evaluation coverage is retrospective','target amplitude units are normalized, not percent BOLD'],
              'cache_sha256':{str(p):digest(p) for p in sorted(cache.glob('chunk*.npz'))}})
    print('COMPLETE',len(people),'people',len(runs),'runs',flush=True)


def freeze(out):
    qc=json.loads((out/'feature_qc.json').read_text())
    people=qc['people_complete_pairs']
    if len(people)<24:
        raise ValueError('Prespecified 12-person arm requires at least 24 complete people')
    rng=np.random.default_rng(20261021)
    shuffled=np.array(people)[rng.permutation(len(people))]
    folds=[]
    for k, test in enumerate(np.array_split(shuffled,3)):
        pool=[p for p in shuffled if p not in test]
        val=pool[:4]; train=pool[4:]
        folds.append({'fold':k,'test_people':test.tolist(),'validation_people':val,'training_order':train,
                      'training_people_levels':{'4':train[:4],'12':train[:12]}})
    protocol={'study':'thesis_causal_factorial_v1','frozen_before_model_outcomes':True,
              'dataset':'ds006040','scope':'single-site previously inspected development data; EC within-condition and EO condition-shift evaluation',
              'folds':folds,'people_levels':[4,12],'duration_seconds':[120,240],
              'duration_definition':'first 60/120 eligible EC target frames (120/240 retained target-seconds), plus strictly prior 24 s input context; actual acquisition span and gaps reported per person; no inner validation frames counted as training',
              'inputs':['eeg','phys','combined'],'physiology':'ECG RR timing and availability fractions only; no ECG spectral power, no respiration, no CO2, no EOG',
              'availability_control':'highest resource condition only: availability fractions without RR; both ridge and MLP, EC training',
              'interpretation':'bounded development comparisons from one fixed nested subset order per fold, not a scaling law',
              'poster_primary_prespecified':{'train_state':'EC','eval_condition':'EC','training_people':12,'duration_seconds':240,'target':'regional64','arms':['ridge EEG','ridge ECG timing+availability','ridge EEG+ECG timing+availability','MLP EEG']},
              'poster_learning_prespecified':'ridge EEG, EC train/test, regional64; 4 vs12 training people crossed with120 vs240 retained target-seconds/person; full grid reported',
              'models':['ridge','mlp'],'ridge_alphas':[.1,1,10,100,1000,10000],
              'mlp_candidates':[{'width':32,'weight_decay':.01},{'width':128,'weight_decay':.01}],
              'mlp_max_epochs':60,'mlp_patience':10,'mlp_learning_rate':.001,'batch_size':128,'seed':41,
              'mlp_objective':'193 standardized outputs jointly fitted; each of global, regional64, global-residual64, global+phys-residual64 groups has weight 1/4. Shared MLP representation differs from independent per-output ridge; not an isolated parameter-count intervention.',
              'ridge_objective':'independent-output raw-target MSE; per-output alpha on equal-person validation MSE. Standardizing any one output would not change its selected alpha.',
              'selection':'one nested subject-disjoint inner validation holdout per outer fold, equal-person MSE; choose ridge alpha per target and neural width/epoch by average standardized-target MSE; no refit on validation',
              'calibration':'per-output affine fitted on inner validation predictions only; report both uncalibrated and validation-calibrated R2',
              'targets':['global','regional64','global_residual64','global_phys_residual64'],
              'residual_definition':'nuisance coefficients fitted only on selected training frames; apply to measured heldout global/physiology for retrospective target definition; residual models receive no measured BOLD input',
              'controls':['training_mean_R2','predicted_global_template','availability-only at n12/240s','30 deterministic within-run original-volume-grid circular shifts >=60s; score matched available frame pairs'],
              'metrics':['temporal_r','predictive_R2','validation_calibrated_R2','rmse','amplitude_ratio','best_lag_seconds_+-10','regional_contrast_r','negative_R2_fraction','undefined_r_fraction'],
              'aggregation':'per-run metrics averaged over ROIs, then EC/EO separately per person; all outer-test people once; 2000 person bootstrap draws, paired by person for differences',
              'mixed_state_extension':'only highest resource 12 people x240 total seconds/person, first60 EC and60 EO frames, same validation/test people; equal total labels',
              'profile_gate':'one GPU profile fit; then one serial GPU job, 4 CPU/12GB request; CPU ridge job 4 CPU/12GB; no checkpoint files',
              'feature_sha256':digest(out/'features_causal.npz'),
              'source_sha256':{p.name:digest(p) for p in sorted(Path(__file__).parent.glob('thesis_*')) if p.is_file()},
              'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    p=out/'protocol.json'
    if p.exists():
        raise FileExistsError('Protocol is immutable; retain it and document amendments separately')
    save_json(p,protocol)
    (out/'protocol.sha256').write_text(digest(p)+'  protocol.json\n')
    print('FROZEN',digest(p),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','build','freeze'])
    p.add_argument('--root',type=Path,default=Path('/scratch/hz18/stay0060/ext/ds006040'))
    p.add_argument('--cache',type=Path,default=Path('/scratch/hz18/stay0060/ext/cache'))
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.command=='audit':inventory(a.root,a.cache,a.out)
    elif a.command=='build':build(a.root,a.cache,a.out)
    else:freeze(a.out)


if __name__=='__main__':main()
