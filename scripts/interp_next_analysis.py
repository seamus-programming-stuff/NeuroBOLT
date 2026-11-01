"""Frozen, prediction-first interpretability continuation; no model fitting.

All filesystem operations use pathlib. Audit reads metadata before new scoring.
Run is restricted to an isolated new output directory and verified input hashes.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import importlib.metadata as metadata
import itertools
import json
import math
import platform
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELS = ('eeg_full', 'phys_specific', 'eeg+phys_specific')
FOUR = ('Cuneus', 'Heschl’s gyrus', 'Thalamus', 'global signal clean')
SEVEN = ('Cuneus', 'Heschl’s gyrus', 'Middle frontal gyrus anterior',
         'Precuneus anterior', 'Putamen', 'Thalamus', 'global signal clean')
SOURCES = ('interp_next_analysis.py', 'interp_next_tests.py', 'interp_cv.py',
           'interp_maps.py', 'interp_report.py', 'interp_attribution.py',
           'interp_build_cache.py', 'ridge_learning_curve.py', 'baseline_ridge.py',
           'eval_inter_per_scan.py', 'm3_env.sh', 'interp_m3.sbatch')
TR = 2.1


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return clean(x.tolist())
    if isinstance(x, np.generic):
        return clean(x.item())
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def save(path, data, exclusive=False):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as f:
        json.dump(clean(data), f, indent=2, allow_nan=False)
        f.write('\n')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def person(scan):
    m = re.match(r'^(sub\d+)-scan\d+$', scan)
    if m is None:
        raise ValueError('Invalid scan identity: ' + str(scan))
    return m[1]


def schema_features(x, channels):
    """Accept the audited EEG-only cache representation, never a target matrix."""
    if len(channels) != 26 or len(set(channels)) != 26:
        raise AssertionError('Expected exactly the 26 documented EEG electrodes')
    forbidden = ('bold', 'fmri', 'global', 'ecg', 'eog', 'emg', 'cwl')
    if any(any(t in str(c).lower() for t in forbidden) for c in channels):
        raise AssertionError('Target or nuisance channel in EEG schema')
    if x.ndim != 2 or x.shape[1] != 26 * 44 * 12:
        raise AssertionError('Expected channel x frequency x lag EEG features')
    return x.reshape(len(x), 26, 44, 12)


def metric(p, y):
    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if p.shape != y.shape or p.ndim != 1 or not np.isfinite(p).all() or not np.isfinite(y).all():
        raise ValueError('Metrics require identical, finite one-dimensional arrays')
    pc, yc = p-p.mean(), y-y.mean()
    sy, sp = float(np.linalg.norm(yc)), float(np.linalg.norm(pc))
    constant = np.ptp(p) <= 1e-12 * max(1., float(np.max(np.abs(p))))
    r = float(pc @ yc / (sp*sy)) if not constant and sy > 1e-12 else float('nan')
    return {'r': r, 'R2': 1-float(np.sum((p-y)**2))/(sy**2) if sy > 1e-12 else float('nan'),
            'RMSE': float(np.sqrt(np.mean((p-y)**2))),
            'SD_ratio': (0. if constant else sp/sy) if sy > 1e-12 else float('nan')}


def fdr(p, method='bh'):
    p = np.asarray(p, dtype=float)
    answer = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    if np.any((p[ok] < 0) | (p[ok] > 1)):
        raise ValueError('p-values outside [0,1]')
    q = p[ok]
    n = len(q)
    if not n:
        return answer
    order = np.argsort(q)
    factor = np.sum(1/np.arange(1, n+1)) if method == 'by' else 1.
    ranked = np.minimum.accumulate((q[order]*n*factor/np.arange(1,n+1))[::-1])[::-1]
    corrected = np.empty(n)
    corrected[order] = np.clip(ranked, 0, 1)
    answer[ok] = corrected
    return answer


def bootstrap_means(a, b=10000, seed=20261102):
    a = np.asarray(a, dtype=float)
    if a.ndim == 1:
        a = a[:, None]
    if not np.isfinite(a).all():
        raise ValueError('Declare complete-panel exclusions before bootstrapping')
    rng = np.random.default_rng(seed)
    result = np.empty((b, a.shape[1]))
    for start in range(0,b,250):
        idx = rng.integers(len(a),size=(min(250,b-start),len(a)))
        result[start:start+len(idx)] = a[idx].mean(axis=1)
    return result


def signflip(a, b=9999, seed=20261103):
    a = np.asarray(a,dtype=float)
    if a.ndim == 1:
        a = a[:,None]
    if not np.isfinite(a).all():
        raise ValueError('Nonfinite paired contrast')
    observed = np.abs(a.mean(axis=0))
    if len(a) <= 12:
        signs = np.array(list(itertools.product((-1.,1.),repeat=len(a))))
        null = np.abs(signs @ a / len(a))
        return (null >= observed-1e-14).mean(axis=0), len(signs), 'exact'
    rng = np.random.default_rng(seed)
    count = np.zeros(a.shape[1],dtype=int)
    for start in range(0,b,500):
        signs = rng.choice((-1.,1.),size=(min(500,b-start),len(a)))
        count += (np.abs(signs @ a / len(a)) >= observed-1e-14).sum(axis=0)
    return (count+1)/(b+1), b, 'Monte Carlo'


def stat(a, b):
    a = np.asarray(a,dtype=float)
    ci = np.percentile(bootstrap_means(a,b)[:,0],[2.5,97.5])
    p,n,kind = signflip(a)
    sd = float(a.std(ddof=1))
    return {'mean':float(a.mean()),'SD':sd,'lo':ci[0],'hi':ci[1],
            'p':p[0],'dz':float(a.mean()/sd) if sd>1e-12 else np.nan,
            'n_people':len(a),'permutations':n,'permutation_type':kind}


def folds(path):
    result=[]
    for k in range(1,6):
        frame=pd.read_excel(path,sheet_name=f'fold{k}')
        groups={g:frame.loc[frame[g]==1,'scan_name'].astype(str).tolist() for g in ('train','val','test')}
        sets={g:set(map(person,v)) for g,v in groups.items()}
        if sets['train']&sets['val'] or sets['train']&sets['test'] or sets['val']&sets['test']:
            raise AssertionError('Person leakage in fold '+str(k))
        result.append({'fold':k,**groups})
    tests=[s for f in result for s in f['test']]
    if len(tests)!=29 or len(set(tests))!=29 or len(set(map(person,tests)))!=22:
        raise AssertionError('Expected each VU scan held out exactly once')
    return result


def headers(path):
    import zipfile
    answer={}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            with z.open(name) as f:
                version=np.lib.format.read_magic(f)
                shape,fortran,dtype=np.lib.format._read_array_header(f,version)
                answer[name[:-4]]={'shape':shape,'dtype':str(dtype)}
    return answer


def channels_from_source():
    tree=ast.parse((ROOT/'scripts/eval_inter_per_scan.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CH_NAMES' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('EEG electrode schema not found')


def audit(args):
    out=args.out
    out.mkdir(parents=True,exist_ok=False)
    interp=args.interp
    inputs={'features':args.features,'aux':interp/'interp_cache.npz',
            'eeg_full':interp/'cv_A/predictions_eeg_full.npz',
            'phys_specific':interp/'cv_D/predictions_phys_specific.npz',
            'eeg+phys_specific':interp/'cv_D/predictions_eeg+phys_specific.npz'}
    descriptions={k:{'path':str(v.resolve()),'bytes':v.stat().st_size,'sha256':sha(v),'arrays':headers(v)} for k,v in inputs.items()}
    attribution_inputs=[{'path':str(v.resolve()),'sha256':sha(v)} for v in sorted((interp/'attribution').glob('permutation_*.csv'))]
    if not attribution_inputs:raise ValueError('Historical matched perturbation CSV inputs missing')
    attr_schema=pd.concat([pd.read_csv(Path(v['path']),usecols=['model','kind','part']) for v in attribution_inputs]).drop_duplicates()
    assert len(attr_schema)==123
    cv=folds(ROOT/'scan_split_cv5.xlsx')
    ch=channels_from_source()
    for f in cv:
        for s in f['test']:
            shape=descriptions['features']['arrays']['x_'+s]['shape']
            assert len(shape)==2 and shape[1]==26*44*12
            assert descriptions['aux']['arrays']['frame_'+s]['shape']==(shape[0],)
            for model in MODELS:
                assert descriptions[model]['arrays']['pred_'+s]['shape']==(shape[0],129)
    cvroot=args.checkpoint_root/'cv'
    candidates=sorted(cvroot.rglob('*.pth')) if cvroot.exists() else []
    local=ROOT/'checkpoints'
    external=[p for p in sorted(local.rglob('*.pth')) if p.name!='labram-base.pth'] if local.exists() else []
    checkpoints=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in candidates+external]
    gate={'state':'BLOCKED','reason':'No verified shared cross-person checkpoints covering all five CV folds; no neural forward/backward passes authorized by the gate.',
          'cv_directory':str(cvroot),'cv_pth_count':len(candidates),'other_checkpoints_not_substitutes':checkpoints}
    if candidates:
        gate['reason']='Candidate files require fold/subject/output/validation provenance; none is automatically accepted from its name. P2 is conservatively blocked pending a complete verified manifest.'
    # Synthetic runtime choice is made before new outcome scoring.
    t=time.monotonic();bootstrap_means(np.random.default_rng(7).normal(size=(22,96)),1000)
    profile=time.monotonic()-t
    b=10000 if profile<5 else 1000
    env={'utc':utc(),'python':sys.version,'platform':platform.platform(),'packages':{}}
    for name in ('numpy','pandas','scipy','torch','mne','timm','linear-attention-transformer'):
        try:env['packages'][name]=metadata.version(name)
        except metadata.PackageNotFoundError:env['packages'][name]=None
    save(out/'environment.json',env,True)
    save(out/'inventory.json',{'inputs':descriptions,'attribution_inputs':attribution_inputs,'P2':gate,'features':{'source_keys':'x_<scan> only','shape':[None,26,44,12],'channels':ch,
        'proof_limit':'Schema and source audit cannot retroactively certify every historical execution; no target arrays enter this continuation feature function.'}},True)
    p={'created_utc':utc(),'scope':'Exploratory correction of already-inspected VU development outputs; no refitting or new models.',
       'base_commit':'c962c07','source_sha256':{s:sha(ROOT/'scripts'/s) for s in SOURCES},
       'split_sha256':sha(ROOT/'scan_split_cv5.xlsx'),'inventory_sha256':sha(out/'inventory.json'),
       'inputs':{k:{'path':v['path'],'sha256':v['sha256']} for k,v in descriptions.items()},
       'attribution_inputs':attribution_inputs,
       'folds':cv,'channels':ch,'primary':[('eeg_full','phys_specific'),('eeg+phys_specific','eeg_full')],
       'endpoint':'Mean raw predictive R2 over 64 regions, then scans within person; 22 equal-weight people.',
       'families':{'primary_raw_R2':2,'secondary_raw_R2_regional_contrasts':128,'secondary_gsr_R2_regional_contrasts':128,
                   'coupling_alpha_beta_4targets_12lags':96,'prediction_association_alpha_beta_4targets_12lags':96,
                   'raw7_circular_shift_scan_tests':29,'gsr64_circular_shift_scan_tests':29,'historical_attribution_all_models_parts':123},
       'bootstrap_B':b,'synthetic_profile_1000_seconds':profile,'signflip_B':9999,'seed':20261102,
       'FDR':'BH .05 plus BY sensitivity; missing tests remain missing; finite/tested counts reported.',
       'lag_contrasts':['Thalamus positive alpha/beta peak minus mean Cuneus/Heschl negative peak; 2-second bins.'],
       'temporal_null':'Enumerated cyclic shifts >=63s within each complete consecutive run; gaps block the scan null rather than join censored segments. 63s is primary; 126s is a separately reported sensitivity, not selected for significance. Stationarity assumed.',
       'acf':'Fold1 training-only alpha and global autocorrelation at 63/126s, descriptive warning if large; no test-tuned minimum shift.',
       'attribution':'Reweight existing waveform perturbations over repeats/ROIs, scans, then five people; exact sign flips for small n. No new neural pass.',
       'P2':gate,'limits':{'GPU_allocations':0,'GPU_hours':0,'CPU_hours_total_cap':8,'job_CPUs':4,'job_memory_GB':32,'job_wall_minutes':90},
       'inference_limits':['Repeatedly inspected data','Shared CV training sets','Sign symmetry/exchangeability assumptions','Spatially correlated features','Retrospective whole-run filtering/GSR'],
       'outputs':['metrics_per_scan.csv','metrics_per_person.csv','contrasts.csv','partitions_per_person.csv','partitions_summary.csv','lag_profiles.csv','lag_peaks.csv','nulls.csv','attribution_person.csv','attribution_summary.csv']}
    save(out/'protocol.json',p,True)
    (out/'protocol.sha256').write_text(sha(out/'protocol.json')+'  protocol.json\n',encoding='utf-8')
    save(out/'execution_log.json',{'state':'FROZEN','events':[{'utc':utc(),'event':'Audit complete before new scoring; P2 blocked; no fits planned.'}]},True)
    print('FROZEN',sha(out/'protocol.json'),'P2',gate['state'],'bootstrap',b,flush=True)


def save_csv(out,name,rows):
    frame=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(out/name,index=False,float_format='%.12g',lineterminator='\n')


def contrast_frame(person_metrics,p,b):
    result=[]
    regional=person_metrics[person_metrics['roi']!='global signal clean']
    for targetset in ('all65','gsr64'):
        subset=regional[regional.targets==targetset]
        for a,base in p['primary']:
            means=subset.groupby(['model','person']).R2.mean().unstack('model')
            diff=(means[a]-means[base]).to_numpy()
            if targetset=='all65':
                result.append({'family':'primary_raw_R2','contrast':a+' minus '+base,'roi':'REGIONAL_MEAN_64',**stat(diff,b)})
            for roi,g in subset.groupby('roi'):
                w=g.pivot(index='person',columns='model',values='R2').sort_index()
                result.append({'family':'secondary_'+('raw' if targetset=='all65' else 'gsr')+'_R2_regional_contrasts',
                               'contrast':a+' minus '+base,'roi':roi,**stat((w[a]-w[base]).to_numpy(),b)})
    frame=pd.DataFrame(result)
    for family,g in frame.groupby('family'):
        frame.loc[g.index,'q_BH']=fdr(g.p.to_numpy())
        frame.loc[g.index,'q_BY']=fdr(g.p.to_numpy(),'by')
        frame.loc[g.index,'family_planned']=p['families'][family]
        frame.loc[g.index,'family_tested']=g.p.notna().sum()
    return frame


def corr_columns(x,y):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    xc,yc=x-x.mean(0),y-y.mean(0)
    den=np.linalg.norm(xc,axis=0)[:,None]*np.linalg.norm(yc,axis=0)[None,:]
    return np.divide(xc.T@yc,den,out=np.full(den.shape,np.nan),where=den>1e-12)


def alpha_beta(x,channels):
    cube=schema_features(x,channels).astype(np.float64)
    freqs=np.arange(1,45)+.5
    values=[]
    for lo,hi in ((8,13),(13,30)):
        sel=cube[:,:,(freqs>=lo)&(freqs<hi),:]
        maximum=sel.max(axis=2,keepdims=True)
        values.append((maximum[:,:,0,:]+np.log(np.exp(sel-maximum).sum(axis=2))).mean(axis=1))
    return np.stack(values,axis=1).reshape(len(x),24)


def cyclic_null(pred,true,frames,min_seconds=63):
    if np.any(np.diff(frames)!=1):
        return None
    gap=int(math.ceil(min_seconds/TR))
    n=len(frames)
    shifts=np.arange(gap,n-gap+1,2)
    if not len(shifts):return None
    pc=pred-pred.mean(0);tc=true-true.mean(0)
    den=np.linalg.norm(pc,axis=0)*np.linalg.norm(tc,axis=0)
    keep=den>1e-12
    if not keep.any():return None
    # FFT cyclic cross-correlation; exactly the same shift applied to every ROI.
    cc=np.fft.irfft(np.fft.rfft(pc[:,keep],axis=0)*np.conj(np.fft.rfft(tc[:,keep],axis=0)),n=n,axis=0)/den[keep]
    null=cc[shifts].mean(1);real=float(cc[0].mean())
    return {'r':real,'p':float((1+(null>=real).sum())/(1+len(null))),
            'null_mean':float(null.mean()),'null_sd':float(null.std(ddof=1)),
            'shifts':len(shifts),'min_shift_seconds':gap*TR,'null_values':null}


def run(args):
    out=args.out;p=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    if sha(out/'protocol.json')!=(out/'protocol.sha256').read_text().split()[0]:raise ValueError('Protocol changed')
    for name,h in p['source_sha256'].items():
        if sha(ROOT/'scripts'/name)!=h:raise ValueError('Frozen source changed: '+name)
    for k,v in p['inputs'].items():
        if sha(Path(v['path']))!=v['sha256']:raise ValueError('Frozen input changed: '+k)
    for v in p['attribution_inputs']:
        if sha(Path(v['path']))!=v['sha256']:raise ValueError('Frozen perturbation CSV changed')
    t=time.monotonic();b=p['bootstrap_B']
    log={'state':'RUNNING','started_utc':utc(),'events':[],'P2':p['P2'],'fit_count':0}
    save(out/'execution_log.json',log)
    with np.load(Path(p['inputs']['aux']['path']),allow_pickle=False) as aux:
        scans=sorted(str(s) for s in aux['scans']);labels=[str(s) for s in aux['labels']]
        assert len(scans)==29 and len(set(map(person,scans)))==22 and len(labels)==65
        roi64=[x for x in labels if x!='global signal clean']
        target_names=['all65|'+x for x in labels]+['gsr64|'+x for x in roi64]
        truths={}
        frames={s:aux['frame_'+s].copy() for s in scans}
        for s in scans:
            y=np.asarray(aux['y_all_'+s],dtype=float)
            design=np.column_stack([np.ones(len(y)),y[:,labels.index('global signal clean')]])
            yy=y[:,[labels.index(x) for x in roi64]]
            residual=yy-design@np.linalg.lstsq(design,yy,rcond=None)[0]
            truths[s]=np.column_stack([y,residual])
        fold_lookup={s:f for f in p['folds'] for s in f['test']}
        predictions={};rows=[]
        for model in MODELS:
            with np.load(Path(p['inputs'][model]['path']),allow_pickle=False) as z:
                assert [str(x) for x in z['targets']]==target_names
                predictions[model]={}
                for s in scans:
                    yy=np.asarray(z['true_'+s],dtype=float);pp=np.asarray(z['pred_'+s],dtype=float)
                    if not np.allclose(yy,truths[s],atol=2e-5,rtol=2e-5):raise AssertionError('Target/frame mismatch '+s)
                    assert pp.shape==yy.shape and np.all(np.diff(frames[s])>0)
                    predictions[model][s]=pp
                    for j,name in enumerate(target_names):
                        targets,roi=name.split('|',1)
                        rows.append({'model':model,'targets':targets,'roi':roi,'scan':s,'person':person(s),
                                     'fold':fold_lookup[s]['fold'],'n_frames':len(yy),**metric(pp[:,j],yy[:,j])})
        for s in scans:
            f=fold_lookup[s];mean=np.concatenate([truths[a] for a in f['train']]).mean(0)
            for j,name in enumerate(target_names):
                targets,roi=name.split('|',1)
                rows.append({'model':'training_mean','targets':targets,'roi':roi,'scan':s,'person':person(s),
                    'fold':f['fold'],'n_frames':len(truths[s]),**metric(np.full(len(truths[s]),mean[j]),truths[s][:,j])})
        scan_metrics=pd.DataFrame(rows);save_csv(out,'metrics_per_scan.csv',scan_metrics)
        keys=['model','targets','roi','person']
        pm=scan_metrics.groupby(keys)[['r','R2','RMSE','SD_ratio']].mean().reset_index()
        pm['n_scans']=scan_metrics.groupby(keys).size().to_numpy()
        save_csv(out,'metrics_per_person.csv',pm)
        save_csv(out,'contrasts.csv',contrast_frame(pm,p,b))
        parts=[]
        raw=pm[pm.targets=='all65']
        for (who,roi),g in raw.groupby(['person','roi']):
            v=g.set_index('model').R2
            parts.append({'person':who,'roi':roi,'EEG':v['eeg_full'],'physiology':v['phys_specific'],'joint':v['eeg+phys_specific'],
                'unique_EEG':v['eeg+phys_specific']-v['phys_specific'],
                'unique_physiology':v['eeg+phys_specific']-v['eeg_full'],
                'shared':v['eeg_full']+v['phys_specific']-v['eeg+phys_specific']})
        part=pd.DataFrame(parts);save_csv(out,'partitions_per_person.csv',part)
        part['group']=part.roi
        aggregate=part[part.roi!='global signal clean'].groupby('person').mean(numeric_only=True).reset_index()
        aggregate['group']='REGIONAL_MEAN_64'
        both=pd.concat([part,aggregate],ignore_index=True)
        summary=[]
        for group,g in both.groupby('group'):
            for component in ('EEG','physiology','joint','unique_EEG','unique_physiology','shared'):
                ss=stat(g[component].to_numpy(),b)
                summary.append({'roi':group,'component':component,**{k:ss[k] for k in ('mean','SD','lo','hi','n_people')}})
        save_csv(out,'partitions_summary.csv',summary)
        print('P0 COMPLETE',len(scan_metrics),'scan-target-model rows',flush=True)
        # Lag associations use only the EEG cache to build features.
        coupling=[];association=[];acf=[]
        cols=[labels.index(x) for x in FOUR]
        training=set(p['folds'][0]['train'])
        with np.load(Path(p['inputs']['features']['path']),allow_pickle=False) as feature_cache:
            for s in scans:
                x=alpha_beta(feature_cache['x_'+s],p['channels'])
                y=truths[s][:,cols];pred=predictions['eeg_full'][s][:,cols]
                coupling.append(corr_columns(x,y).T.reshape(4,2,12))
                association.append(corr_columns(x,pred).T.reshape(4,2,12))
                assert np.allclose(feature_cache['y_'+s],truths[s][:,[labels.index(q) for q in SEVEN]],atol=2e-5,rtol=2e-5)
                if s in training:
                    for variable,a in (('alpha_power',x.reshape(len(x),2,12)[:,0,-1]),('global_BOLD',truths[s][:,labels.index('global signal clean')])):
                        for lag in (30,60):
                            acf.append({'scan':s,'person':person(s),'variable':variable,'lag_seconds':lag*TR,
                                        'acf':float(corr_columns(a[:-lag,None],a[lag:,None])[0,0]),'consecutive':bool(np.all(np.diff(frames[s])==1))})
        save_csv(out,'training_ACF.csv',acf)
        lagrows=[];lag_person={}
        people=sorted(set(map(person,scans)))
        for kind,array in (('coupling',coupling),('prediction_association',association)):
            scan_z=np.arctanh(np.clip(np.stack(array),-.999999,.999999))
            z=np.stack([scan_z[[i for i,s in enumerate(scans) if person(s)==who]].mean(0) for who in people])
            lag_person[kind]=z
            flat=z.reshape(22,-1);samples=bootstrap_means(flat,b);pv,nperm,ptype=signflip(flat)
            ci=np.percentile(samples,[2.5,97.5],axis=0)
            qbh,qby=fdr(pv),fdr(pv,'by')
            for i,(roi,band,lag) in enumerate(itertools.product(FOUR,('alpha','beta'),24-2*np.arange(12)-1)):
                rr=np.tanh(flat[:,i]);bounds=np.tanh(ci[:,i])
                lagrows.append({'kind':kind,'roi':roi,'band':band,'lag_seconds':int(lag),'mean_r':float(np.tanh(flat[:,i].mean())),
                    'SD_person_r':float(rr.std(ddof=1)),'lo':bounds[0],'hi':bounds[1],'p':pv[i],'q_BH':qbh[i],'q_BY':qby[i],
                    'n_people':22,'n_scans':29,'family_planned':96,'family_tested':int(np.isfinite(pv).sum()),'permutations':nperm})
            np.savez_compressed(out/(kind+'_person_profiles.npz'),z=z,people=np.array(people),rois=np.array(FOUR),lags=24-2*np.arange(12)-1)
        save_csv(out,'lag_profiles.csv',lagrows)
        peaks=[];z=lag_person['coupling'];lags=24-2*np.arange(12)-1
        samples=bootstrap_means(z.reshape(22,-1),b).reshape(b,4,2,12)
        mean=z.mean(0)
        for bi,band in enumerate(('alpha','beta')):
            cortex=mean[:2,bi].mean(0);thalamus=mean[2,bi]
            cp=lags[np.argmin(samples[:,:2,bi].mean(1),axis=1)]
            tp=lags[np.argmax(samples[:,2,bi],axis=1)]
            delta=tp-cp
            peaks.append({'band':band,'thalamus_peak_seconds':int(lags[np.argmax(thalamus)]),
                'cortex_peak_seconds':int(lags[np.argmin(cortex)]),'difference_seconds':int(lags[np.argmax(thalamus)]-lags[np.argmin(cortex)]),
                'lo':float(np.percentile(delta,2.5)),'hi':float(np.percentile(delta,97.5)),
                'thalamus_modal_fraction':float(max(np.mean(tp==v) for v in lags)),
                'cortex_modal_fraction':float(max(np.mean(cp==v) for v in lags)),
                'expected_sign_fraction':float(np.mean((samples[:,2,bi].max(1)>0)&(samples[:,:2,bi].mean(1).min(1)<0))),
                'bootstrap_B':b,'resolution_seconds':2,'n_people':22})
        save_csv(out,'lag_peaks.csv',peaks)
        # Temporal null is a diagnostic; no assumption of 798 independent people.
        nullrows=[];group_null={};rawcols=[labels.index(q) for q in SEVEN]
        gsrcols=list(range(65,129))
        for targetset,cc in (('raw7',rawcols),('gsr64',gsrcols)):
            for minsec in (63,126):
                scan_null={}
                for s in scans:
                    r=cyclic_null(predictions['eeg_full'][s][:,cc],truths[s][:,cc],frames[s],minsec)
                    if r is None:
                        nullrows.append({'targets':targetset,'min_requested_seconds':minsec,'scan':s,'person':person(s),'state':'BLOCKED_NONCONTIGUOUS_OR_SHORT'})
                    else:
                        scan_null[s]=r
                        nullrows.append({'targets':targetset,'min_requested_seconds':minsec,'scan':s,'person':person(s),'state':'SCORED','n_frames':len(frames[s]),**{k:v for k,v in r.items() if k!='null_values'}})
                rng=np.random.default_rng(20261104)
                draws=[];observed=[]
                for who in people:
                    group=[s for s in scans if person(s)==who and s in scan_null]
                    if not group:continue
                    observed.append(np.mean([scan_null[s]['r'] for s in group]))
                    draws.append(np.mean([rng.choice(scan_null[s]['null_values'],9999) for s in group],axis=0))
                sim=np.mean(draws,axis=0);real=float(np.mean(observed))
                group_null[targetset+'_'+str(minsec)]={'n_people':len(observed),'mean_r':real,'p':float((1+(sim>=real).sum())/10000),
                    'null_lo':float(np.percentile(sim,2.5)),'null_hi':float(np.percentile(sim,97.5)),'stationarity_assumed':True}
        nf=pd.DataFrame(nullrows)
        for _,g in nf.groupby(['targets','min_requested_seconds']):
            nf.loc[g.index,'q_BH']=fdr(g.p.to_numpy())
            nf.loc[g.index,'q_BY']=fdr(g.p.to_numpy(),'by')
            nf.loc[g.index,'family_planned']=29
            nf.loc[g.index,'family_tested']=g.p.notna().sum()
        save_csv(out,'nulls.csv',nf);save(out/'group_temporal_null.json',group_null)
        mismatch=[]
        for a in scans:
            for other in scans:
                if person(a)==person(other):continue
                n=min(len(truths[a]),len(truths[other]))
                rr=[metric(predictions['eeg_full'][a][:n,j],truths[other][:n,j])['r'] for j in rawcols]
                mismatch.append({'prediction_scan':a,'target_scan':other,'prediction_person':person(a),'target_person':person(other),'mean_r':np.mean(rr)})
        save_csv(out,'mismatched_pairs_descriptive.csv',mismatch)
        print('P1 LAGS/NULLS COMPLETE',flush=True)
    # Existing attribution results: repeats -> ROIs -> scans -> people.
    perm=pd.concat([pd.read_csv(Path(v['path'])) for v in p['attribution_inputs']],ignore_index=True)
    perm['person']=perm.scan.map(person);perm['drop']=perm.base_r-perm.perturbed_r
    attrs=perm.groupby(['model','kind','part','scan','person'])[['drop','shift']].mean().reset_index()
    attrs=attrs.groupby(['model','kind','part','person'])[['drop','shift']].mean().reset_index()
    save_csv(out,'attribution_person.csv',attrs)
    summaries=[]
    for (model,kind,part),g in attrs.groupby(['model','kind','part']):
        summaries.append({'model':model,'kind':kind,'part':part,**stat(g['drop'].to_numpy(),b),'mean_relative_prediction_change':g['shift'].mean()})
    attr=pd.DataFrame(summaries)
    attr['q_BH']=fdr(attr.p.to_numpy());attr['q_BY']=fdr(attr.p.to_numpy(),'by')
    attr['family_planned']=123;attr['family_tested']=attr.p.notna().sum()
    save_csv(out,'attribution_summary.csv',attr)
    # Historical donor algorithm is verified structurally, not rerun on new EEG.
    repeat=perm.groupby(['model','kind'])['repeat'].agg(['min','max','nunique']).reset_index()
    save_csv(out,'attribution_repeat_audit.csv',repeat)
    summary=[]
    for (model,targetset),g in pm[pm.roi!='global signal clean'].groupby(['model','targets']):
        per=g.groupby('person')[['r','R2','RMSE','SD_ratio']].mean()
        for key in ('r','R2','RMSE','SD_ratio'):
            vals=per[key].to_numpy();ss=stat(vals,b) if np.isfinite(vals).all() else {}
            summary.append({'model':model,'targets':targetset,'metric':key,**{k:ss.get(k,np.nan) for k in ('mean','SD','lo','hi','n_people')},
                'negative_R2_people':int((per.R2<0).sum()) if key=='R2' else np.nan})
    save_csv(out,'summary.csv',summary)
    log.update({'state':'COMPLETE','completed_utc':utc(),'elapsed_seconds':time.monotonic()-t,
                'n_people':22,'n_scans':29,'bootstrap_B':b,'neural_passes':0,'fit_count':0,
                'events':[{'utc':utc(),'event':'P0/P1 completed; P2 blocked by checkpoint gate; no fit/retry/scope search.'}]})
    save(out/'execution_log.json',log)
    save(out/'output_hashes.json',{f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file() and f.name!='output_hashes.json'})
    print('COMPLETE',json.dumps(log),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('audit','run'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--interp',type=Path)
    parser.add_argument('--features',type=Path)
    parser.add_argument('--checkpoint-root',type=Path)
    args=parser.parse_args();args.out=args.out.resolve()
    allowed=(ROOT/'reports/interpretability_next').resolve()
    if allowed not in args.out.parents:raise ValueError('Output must be an isolated continuation directory')
    if args.command=='audit':
        if any(getattr(args,k) is None for k in ('interp','features','checkpoint_root')):parser.error('audit requires all source paths')
        audit(args)
    else:
        try:run(args)
        except Exception as exc:
            save(args.out/'failure.json',{'state':'FAILED','utc':utc(),'error':repr(exc),'partial_outputs_not_complete':True})
            raise


if __name__=='__main__':main()
