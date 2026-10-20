#!/usr/bin/env python3
"""Locked transfer endpoints. Diagnostic lags never alter clock mapping or headline r."""
import csv
import json
import os
import time
import numpy as np
from natview_data import DERIV,OUT,finite_json
from natview_stage import digest,save_json


def correlations(p,y):
    a=p-p.mean(0);b=y-y.mean(0);den=np.sqrt((a*a).sum(0)*(b*b).sum(0))
    return np.divide((a*b).sum(0),den,out=np.full(y.shape[1],np.nan),where=den>1e-12)


def metrics(p,y):
    r=correlations(p,y);den=((y-y.mean(0))**2).sum(0)
    r2=1-np.divide(((p-y)**2).sum(0),den,out=np.full(y.shape[1],np.nan),where=den>1e-12)
    amp=np.divide(p.std(0),y.std(0),out=np.full(y.shape[1],np.nan),where=y.std(0)>1e-12)
    return r,r2,amp


def stationary_indices(frames,rng):
    n=len(frames);idx=np.empty(n,dtype=int);idx[0]=rng.integers(n)
    for j in range(1,n):
        prev=idx[j-1]
        idx[j]=prev+1 if prev<n-1 and frames[prev+1]==frames[prev]+1 and rng.random()>=.1 else rng.integers(n)
    return idx


def lag_profile(p,y,frames):
    lookup={int(f):i for i,f in enumerate(frames)};curves=[]
    for lag in range(-5,6):
        pair=np.array([(i,lookup[int(f-lag)]) for i,f in enumerate(frames) if int(f-lag) in lookup])
        curves.append(correlations(p[pair[:,0]],y[pair[:,1]]) if len(pair)>=20 else np.full(y.shape[1],np.nan))
    curves=np.array(curves);best=np.nanargmax(np.nan_to_num(curves,nan=-2),axis=0)-5
    best=np.where(np.isfinite(curves).any(0),best*2.1,np.nan)
    return curves,best


def score_panel(results,protocol,freeze):
    model=np.load(DERIV/'vu_common23_prime_geometry_frozen.npz');labels=model['labels'].astype(str).tolist()
    gi=labels.index('global signal clean');ri=[i for i in range(65) if i!=gi]
    beta=model['global_beta'];rows=[];regional=[];predictions={};failed=[]
    for qc in results:
        sub=qc['subject']
        if not qc.get('inclusion_pass',False):
            failed.append({'subject':sub,'reason':qc.get('error','fewer than 60 prespecified QC-passing frames')});continue
        z=np.load(qc['derivative_path']);x,y,frames=z['x'],z['y'],z['frame']
        assert z['labels'].astype(str).tolist()==labels
        assert qc['channel_bridge']['feature_channels_literal_VU']==model['channels'].astype(str).tolist()
        p=((x-model['mean'])/model['sd'])@model['weights']+model['intercept']
        residual_y=y[:,ri]-np.c_[np.ones(len(y)),y[:,gi]]@beta
        residual_p=p[:,ri]-np.c_[np.ones(len(p)),p[:,gi]]@beta
        allp=np.c_[p,residual_p];ally=np.c_[y,residual_y]
        groups={'global':[gi],'regional64':ri,'VU_global_adjusted_residual64':list(range(65,129))}
        # Same stationary resampling for all outcomes and metrics, no block crosses a physical gap.
        rng=np.random.default_rng(20261021+int(sub[-2:]));boot={k:[] for k in groups}
        for _ in range(2000):
            idx=stationary_indices(frames,rng);r,r2,amp=metrics(allp[idx],ally[idx])
            for name,cols in groups.items():boot[name].append([np.nanmean(r[cols]),np.nanmean(r2[cols]),np.nanmean(amp[cols])])
        for name,cols in groups.items():
            pp,yy=allp[:,cols],ally[:,cols];r,r2,amp=metrics(pp,yy);curve,lag=lag_profile(pp,yy,frames)
            ci=np.nanquantile(boot[name],[.025,.975],axis=0)
            row={'subject':sub,'target':name,'n_frames':len(frames),'retained_target_seconds':len(frames)*2.1,
                 'n_directly_measured_feature_sites':qc['channel_bridge']['n_measured_features'],
                 'n_interpolated_feature_sites':qc['channel_bridge']['n_interpolated_features'],
                 'r':float(np.nanmean(r)),'r_CI_low':float(ci[0,0]),'r_CI_high':float(ci[1,0]),
                 'normalized_target_predictive_R2':float(np.nanmean(r2)),'R2_CI_low':float(ci[0,1]),'R2_CI_high':float(ci[1,1]),
                 'amplitude_ratio':float(np.nanmean(amp)),'amplitude_CI_low':float(ci[0,2]),'amplitude_CI_high':float(ci[1,2]),
                 'diagnostic_best_lag_mean_seconds':float(np.nanmean(lag)),
                 'diagnostic_abs_best_lag_mean_seconds':float(np.nanmean(abs(lag))),
                 'negative_R2_fraction':float(np.mean(r2<0)),'undefined_r_fraction':float(np.mean(~np.isfinite(r)))}
            rows.append(row)
            labs=[labels[j] for j in cols] if name!='VU_global_adjusted_residual64' else [labels[j] for j in ri]
            for j,lab in enumerate(labs):
                regional.append({'subject':sub,'target':name,'region':lab,'r':r[j],'normalized_target_predictive_R2':r2[j],
                                 'amplitude_ratio':amp[j],'diagnostic_best_lag_seconds':lag[j],
                                 **{f'r_lag_{k}_TR':curve[k+5,j] for k in range(-5,6)}})
        predictions.update({f'{sub}_pred':p,f'{sub}_true':y,f'{sub}_frame':frames,
                            f'{sub}_residual_pred':residual_p,f'{sub}_residual_true':residual_y})
        print('SCORED',sub,'frames',len(frames),'global r',rows[-3]['r'],'regional r',rows[-2]['r'],flush=True)
    if rows:
        for name,data in [('per_person_metrics.csv',rows),('regional_metrics.csv',regional)]:
            with open(OUT/name,'w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
        np.savez_compressed(DERIV/'locked_predictions.npz',labels=np.array(labels),**predictions)
    pooled=[];rng=np.random.default_rng(20261021)
    for target in ['global','regional64','VU_global_adjusted_residual64']:
        rr=[r for r in rows if r['target']==target]
        if not rr:continue
        vals=np.array([[r['r'],r['normalized_target_predictive_R2'],r['amplitude_ratio']] for r in rr])
        bb=np.array([vals[rng.integers(len(rr),size=len(rr))].mean(0) for _ in range(10000)])
        ci=np.quantile(bb,[.025,.975],axis=0)
        pooled.append({'target':target,'n_people':len(rr),'person_mean_r':float(vals[:,0].mean()),'person_bootstrap_r_95CI':ci[:,0].tolist(),
                       'person_mean_normalized_target_predictive_R2':float(vals[:,1].mean()),'person_bootstrap_R2_95CI':ci[:,1].tolist(),
                       'person_mean_amplitude_ratio':float(vals[:,2].mean()),'person_bootstrap_amplitude_95CI':ci[:,2].tolist()})
    summary={'branch':'achieved_locked_8person_external_pilot' if len(results)==8 and len(failed)==0 else 'partial_or_not_achieved_locked_panel',
             'n_prespecified_people':8,'n_clock_resolved':sum(q.get('clock_resolved',False) for q in results),
             'n_evaluated_people':len(results)-len(failed),'excluded_people':failed,'pooled_metrics':pooled,
             'channel_contract':'21 nominal exact name-overlap sites +2 always interpolated VU prime targets; additional missing2or3 sites interpolated in3 prespecified people',
             'per_person_QC':[{'subject':q['subject'],'clock_resolved':q.get('clock_resolved',False),
                              'frames':q.get('n_feature_frames',0),'retained_seconds':q.get('retained_target_seconds_after_all_QC'),
                              'measured_feature_sites':q.get('channel_bridge',{}).get('n_measured_features'),
                              'interpolated_feature_sites':q.get('channel_bridge',{}).get('interpolated'),
                              'eye_interpolated_fraction':q.get('eye',{}).get('interpolated_fraction'),
                              'clock_eye_max_abs_error_seconds':q.get('eye',{}).get('max_abs_match_error_seconds'),
                              'clock_biopac_max_relative_error_seconds':q.get('biopac',{}).get('max_relative_clock_residual_seconds'),
                              'error':q.get('error')} for q in results],
             'protocol_sha256':freeze['protocol_sha256'],'model_sha256':freeze['model_sha256'],
             'freeze_sha256':digest(OUT/'freeze.json'),'slurm_job_id':os.environ['SLURM_JOB_ID'],
             'completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
             'primary_alignment':'unshifted; original scanner volume identities from raw events/urevents/mask and independent pulses',
             'bootstrap':'2000 within-person stationary replicates, expected 10TR block; restart at every gap; 10000 between-person iid replicates',
             'lag':'-5..5 original volume index lags, min20 pairs, positive prediction later; descriptive only; no re-alignment or model selection',
             'clinical_claim':False,'independent_sleep_or_arousal_labels':False,'new_site_accuracy_scope':'small external feasibility panel; resting instructed eye condition/site and preprocessing confounded',
             'pilot_used_for_ingestion_only':True,'test_outcome_tuning':False,'EEG_adaptation':'none; VU training means/scales only',
             'residual_endpoint':'VU-trained global coefficient used on measured and predicted global; measured BOLD defines label only, never a model input; residual algebra, not a separately tuned residual head'}
    save_json(OUT/'machine_summary.json',finite_json(summary))
