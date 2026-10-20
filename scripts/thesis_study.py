#!/usr/bin/env python3
"""Frozen bounded people x retained duration x information x capacity study.

All fitted preprocessing, residual definitions, model selection and calibration
exclude outer test people. A single inner grouped validation split is used, not
an exhaustive nested CV. No clinical or untouched-external claim is supported.
"""
import argparse
import copy
import csv
import itertools
import json
import os
try:
    import resource
except ImportError:
    resource=None
import time
from pathlib import Path

import numpy as np
import torch
from thesis_data import digest, save_json


def standardize(train, *others):
    """Training-only missing-value imputation and standardization."""
    with np.errstate(all='ignore'):
        med=np.nanmedian(train,axis=0)
    med=np.nan_to_num(med)
    clean=np.where(np.isfinite(train),train,med)
    mean=clean.mean(0); sd=clean.std(0);sd[sd<1e-7]=1
    transform=lambda a:((np.where(np.isfinite(a),a,med)-mean)/sd).astype('float32')
    return [transform(a) for a in (train,)+others], {'median':med,'mean':mean,'sd':sd}


def correlations(p,y):
    a=p-p.mean(0); b=y-y.mean(0)
    den=np.sqrt((a*a).sum(0)*(b*b).sum(0))
    return np.divide((a*b).sum(0),den,out=np.full(y.shape[1],np.nan),where=den>1e-12)


def r2(p,y):
    den=((y-y.mean(0))**2).sum(0)
    return 1-np.divide(((p-y)**2).sum(0),den,out=np.full(y.shape[1],np.nan),where=den>1e-12)


def affine_calibration(p,y,w):
    pm=(p*w[:,None]).sum(0); ym=(y*w[:,None]).sum(0)
    var=(((p-pm)**2)*w[:,None]).sum(0)
    slope=np.divide(((p-pm)*(y-ym)*w[:,None]).sum(0),var,out=np.zeros(y.shape[1]),where=var>1e-10)
    return slope,ym-slope*pm


def weighted_mse(p,y,w):
    return (((p-y)**2)*w[:,None]).sum(0)


def ridge_select(x,y,xv,yv,wv,alphas):
    # Double precision eigensolve is fast for this 300/324-dimensional design.
    xt=torch.as_tensor(x,dtype=torch.float64); yt=torch.as_tensor(y,dtype=torch.float64)
    ym=yt.mean(0); xm=xt.mean(0); xc=xt-xm
    ev,v=torch.linalg.eigh(xc.T@xc); ev=ev.clamp(min=0)
    vxy=v.T@xc.T@(yt-ym)
    best=np.full(y.shape[1],np.inf); bw=np.zeros((x.shape[1],y.shape[1]));ba=np.zeros(y.shape[1])
    path=[]
    for alpha in alphas:
        ww=(v@(vxy/(ev[:,None]+alpha))).numpy()
        pv=(xv-xm.numpy())@ww+ym.numpy()
        mse=weighted_mse(pv,yv,wv);better=mse<best
        bw[:,better]=ww[:,better];ba[better]=alpha;best[better]=mse[better]
        path.append({'alpha':alpha,'validation_mse':float(mse.mean())})
    intercept=ym.numpy()-xm.numpy()@bw
    return lambda a:a@bw+intercept, {'alpha_per_target':ba.tolist(),'validation_mse_per_target':best.tolist(),'path':path}


def fit_mlp(x,y,xv,yv,wv,candidates,protocol,device,profile=False):
    ym=y.mean(0);sd=y.std(0);sd[sd<1e-6]=1
    xt=torch.as_tensor(x,device=device);yt=torch.as_tensor((y-ym)/sd,device=device)
    vx=torch.as_tensor(xv,device=device);vy=torch.as_tensor((yv-ym)/sd,device=device)
    vw=torch.as_tensor(wv,dtype=torch.float32,device=device)
    # Equal weight for global / full regional / global residual / global+phys
    # residual groups, despite their unequal numbers of outputs.
    tw=np.r_[.25,np.full(192,.25/64)].astype('float32')
    target_weight=torch.as_tensor(tw,device=device)
    best_loss=np.inf;best_net=None;records=[]
    for cand in candidates:
        torch.manual_seed(protocol['seed']);np.random.seed(protocol['seed'])
        net=torch.nn.Sequential(torch.nn.Linear(x.shape[1],cand['width']),torch.nn.GELU(),
                                torch.nn.Linear(cand['width'],y.shape[1])).to(device)
        opt=torch.optim.AdamW(net.parameters(),lr=protocol['mlp_learning_rate'],weight_decay=cand['weight_decay'])
        best_state=None;localbest=np.inf;bestepoch=0;started=time.monotonic()
        g=torch.Generator(device=device).manual_seed(protocol['seed'])
        for epoch in range(protocol['mlp_max_epochs']):
            net.train();order=torch.randperm(len(x),generator=g,device=device)
            for idx in order.split(protocol['batch_size']):
                opt.zero_grad(set_to_none=True)
                loss=(((net(xt[idx])-yt[idx])**2)*target_weight).sum(1).mean();loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(),5)
                opt.step()
            net.eval()
            with torch.no_grad():vl=float(((((net(vx)-vy)**2)*vw[:,None]).sum(0)*target_weight).sum())
            if not np.isfinite(vl):raise ValueError('Nonfinite neural validation loss')
            if vl < localbest-1e-7:
                localbest=vl;bestepoch=epoch+1;best_state=copy.deepcopy(net.state_dict())
            if epoch+1-bestepoch>=protocol['mlp_patience']:break
        net.load_state_dict(best_state);net.eval()
        record={**cand,'epochs_run':epoch+1,'best_epoch':bestepoch,'validation_standardized_mse':localbest,
                'fit_seconds':time.monotonic()-started,'parameters':sum(p.numel() for p in net.parameters())}
        records.append(record)
        if localbest<best_loss:best_loss=localbest;best_net=net;chosen=record
    def predict(a):
        with torch.no_grad():
            return np.concatenate([best_net(torch.as_tensor(b,device=device)).cpu().numpy() for b in np.array_split(a,max(1,int(np.ceil(len(a)/1024))))])*sd+ym
    return predict,{'chosen':chosen,'candidates':records,'validation_standardized_mse':best_loss}


def input_array(z,run,info):
    if info=='eeg':return z[f'eeg_{run}']
    if info=='phys':return z[f'phys_{run}']
    if info=='availability':return z[f'phys_{run}'][:,12:]
    return np.concatenate([z[f'eeg_{run}'],z[f'phys_{run}']],axis=1)


def stack(z,people,state,info,seconds=None):
    runs=[p+'_'+c for p in people for c in (['EC'] if state=='EC' else ['EC','EO'])]
    xx=[];yy=[];pp=[];owners=[];rows=[]
    for run in runs:
        n=len(z[f'frame_{run}']) if seconds is None else seconds//2//(1 if state=='EC' else 2)
        idx=np.arange(n)
        xx.append(input_array(z,run,info)[idx]);yy.append(z[f'y_{run}'][idx]);pp.append(z[f'phys_{run}'][idx]);owners.extend([run.split('_')[0]]*n)
        on=z[f'onset_{run}'][idx];fr=z[f'frame_{run}'][idx]
        rows.append({'run':run,'subject':run.split('_')[0],'n_frames':n,'retained_target_seconds':2*n,
                     'target_acquisition_span_seconds':float(on[-1]-on[0]+2),
                     'input_acquisition_span_seconds':float(on[-1]-on[0]+24),
                     'first_frame':int(fr[0]),'last_frame':int(fr[-1]),'gaps':int(np.sum(np.diff(fr)!=1))})
    weights=np.array([1/owners.count(p)/len(people) for p in owners],dtype='float32')
    return np.concatenate(xx),np.concatenate(yy),np.concatenate(pp),weights,rows


def targets(y,phys,beta=None,betap=None,gi=64):
    ri=[j for j in range(y.shape[1]) if j!=gi]
    d=np.c_[np.ones(len(y)),y[:,gi]]
    dp=np.c_[d,phys]
    if beta is None:beta=np.linalg.lstsq(d,y[:,ri],rcond=None)[0]
    if betap is None:
        # A fixed ridge on standardized physiological nuisance avoids unstable
        # coefficients for rare RR-availability patterns. Intercept unpenalized.
        penalty=np.eye(dp.shape[1]);penalty[0,0]=0
        betap=np.linalg.solve(dp.T@dp+penalty,dp.T@y[:,ri])
    out=np.c_[y[:,gi],y[:,ri],y[:,ri]-d@beta,y[:,ri]-dp@betap].astype('float32')
    return out,beta,betap


def lag_scores(p,y,frames):
    # Positive lag means prediction occurs later than the target. Pair using
    # original volume numbers, never adjacent retained rows across a gap.
    lookup={int(f):i for i,f in enumerate(frames)}
    cor=[]
    for lag in range(-5,6):
        pairs=[(i,lookup[int(f-lag)]) for i,f in enumerate(frames) if int(f-lag) in lookup]
        if len(pairs)<20:cor.append(np.full(y.shape[1],np.nan));continue
        a,b=np.array(pairs).T;cor.append(correlations(p[a],y[b]))
    cc=np.stack(cor);safe=np.nan_to_num(cc,nan=-2)
    best=np.argmax(safe,axis=0)
    # Constant predictions have no identifiable lag.
    return np.where(np.all(~np.isfinite(cc),axis=0),np.nan,(best-5)*2)


def shifted_pairs(frames,shift):
    start=int(np.min(frames));span=int(np.max(frames)-start+1)
    lookup={int(f):i for i,f in enumerate(frames)}
    pairs=[(lookup[q],i) for i,f in enumerate(frames) for q in [int((f-start-shift)%span+start)] if q in lookup]
    return np.asarray(pairs,dtype=int)


def metric_row(p,pc,y,frames,seed=0):
    rr=correlations(p,y);r2s=r2(p,y)
    den=y.std(0);amp=np.divide(p.std(0),den,out=np.full(y.shape[1],np.nan),where=den>1e-10)
    lag=lag_scores(p,y,frames)
    rng=np.random.default_rng(seed)
    span=int(frames.max()-frames.min()+1)
    shifts=rng.integers(30,max(31,span-29),size=30)
    null=[];coverage=[]
    for shift in shifts:
        pair=shifted_pairs(frames,int(shift))
        a,b=pair.T
        null.append(float(np.nanmean(correlations(p[a],y[b]))) if np.isfinite(rr).any() else 0)
        coverage.append(len(pair)/len(frames))
    mean=lambda a:float(np.nanmean(a)) if np.isfinite(a).any() else None
    return {'r_mean':mean(rr),'predictive_R2':mean(r2s),'validation_calibrated_R2':mean(r2(pc,y)),
            'rmse':float(np.sqrt(np.mean((p-y)**2))),'amplitude_ratio':mean(amp),
            'best_lag_seconds':mean(lag),'absolute_best_lag_seconds':mean(abs(lag)),
            'negative_R2_fraction':float(np.mean(r2s<0)),'undefined_r_fraction':float(np.mean(~np.isfinite(rr))),
            'circular_shift_r_mean':float(np.mean(null)),'circular_shift_matched_fraction':float(np.mean(coverage)),
            'n_targets':y.shape[1],'n_frames':len(y)}


def write_csv(path,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def conditions(protocol):
    for fold,n,sec,info in itertools.product(protocol['folds'],protocol['people_levels'],protocol['duration_seconds'],protocol['inputs']):
        yield fold,n,sec,info,'EC'
    for fold,info in itertools.product(protocol['folds'],protocol['inputs']):
        yield fold,12,240,info,'EC_EO'
    for fold in protocol['folds']:yield fold,12,240,'availability','EC'


def run_cell(z,protocol,fold,n,sec,info,state,model,device,out,profile=False):
    start=time.monotonic();people=fold['training_order'][:n]
    train=stack(z,people,state,info,sec);val=stack(z,fold['validation_people'],state,info)
    (x,xv),sx=standardize(train[0],val[0]);(ph,phv),sp=standardize(train[2],val[2])
    labels=z['labels'].astype(str).tolist();gi=labels.index('global signal clean')
    y,b,bp=targets(train[1],ph,gi=gi);yv,_,_=targets(val[1],phv,b,bp,gi=gi)
    args={'dataset':'ds006040','scope':'development','fold':fold['fold'],'input':info,'model':model,
          'training_people':n,'duration_seconds':sec,'train_state':state}
    if model=='ridge':pred,selection=ridge_select(x,y,xv,yv,val[3],protocol['ridge_alphas'])
    else:pred,selection=fit_mlp(x,y,xv,yv,val[3],protocol['mlp_candidates'][:1] if profile else protocol['mlp_candidates'],protocol,device,profile)
    pv=pred(xv);ca,cb=affine_calibration(pv,yv,val[3])
    metadata={**args,'protocol_sha256':digest(out/'protocol.json'),'selection':selection,
              'validation_selection_only':True,'training_rows':train[4],'validation_rows':val[4],
              'peak_ram_MB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024 if resource else None,
              'device':str(device),'gpu':torch.cuda.get_device_name() if device=='cuda' else None,
              'gpu_peak_allocated_MB':torch.cuda.max_memory_allocated()/2**20 if device=='cuda' else None,
              'source_sha256':digest(__file__)}
    if profile:
        metadata['elapsed_seconds']=time.monotonic()-start
        save_json(out/'profile.json',metadata)
        print('PROFILE',metadata['elapsed_seconds'],selection,flush=True);return
    rows=[];preds={}
    for person in fold['test_people']:
        for condition in ['EC','EO']:
            run=person+'_'+condition
            xx=input_array(z,run,info);xx=(np.where(np.isfinite(xx),xx,sx['median'])-sx['mean'])/sx['sd']
            pp=z[f'phys_{run}'];pp=(np.where(np.isfinite(pp),pp,sp['median'])-sp['mean'])/sp['sd']
            yy,_,_=targets(z[f'y_{run}'],pp,b,bp,gi=gi)
            prediction=pred(xx.astype('float32'));cal=prediction*ca+cb
            frames=z[f'frame_{run}']
            for name,sl in [('global',slice(0,1)),('regional64',slice(1,65)),('global_residual64',slice(65,129)),('global_phys_residual64',slice(129,193))]:
                rows.append({**args,'subject':person,'eval_condition':condition,'target':name,
                             **metric_row(prediction[:,sl],cal[:,sl],yy[:,sl],frames),
                             'training_mean_R2':float(np.nanmean(r2(np.broadcast_to(y[:,sl].mean(0),yy[:,sl].shape),yy[:,sl])))})
            # Learned global template receives predicted global, never measured
            # test BOLD. This is a control for regional specificity.
            template=prediction[:,[0]]@b[[1]]+b[[0]]
            ct=cal[:,[0]]@b[[1]]+b[[0]]
            rows.append({**args,'subject':person,'eval_condition':condition,'target':'global_template_regional64',
                         **metric_row(template,ct,yy[:,1:65],frames),
                         'training_mean_R2':float(np.nanmean(r2(np.broadcast_to(y[:,1:65].mean(0),yy[:,1:65].shape),yy[:,1:65])))})
            # Fixed adjacent atlas-index pairs, defined before inspecting scores.
            contrast=prediction[:,1:65:2]-prediction[:,2:65:2]
            true_contrast=yy[:,1:65:2]-yy[:,2:65:2]
            cal_contrast=cal[:,1:65:2]-cal[:,2:65:2]
            rows.append({**args,'subject':person,'eval_condition':condition,'target':'regional_contrast32',
                         **metric_row(contrast,cal_contrast,true_contrast,frames),
                         'training_mean_R2':float(np.nanmean(r2(np.broadcast_to((y[:,1:65:2]-y[:,2:65:2]).mean(0),true_contrast.shape),true_contrast)))})
            # Small highest-resource prediction archive for audit, no weights.
            if n==12 and sec==240:
                preds['pred_'+run]=prediction.astype('float32');preds['true_'+run]=yy
                preds['frame_'+run]=frames;preds['calibrated_'+run]=cal.astype('float32')
    # A constant training-mean control is recorded separately for each condition.
    # It shares target definitions and rows with the fitted model.
    metadata['elapsed_seconds']=time.monotonic()-start
    name=f"{model}_f{fold['fold']}_n{n}_s{sec}_{info}_{state}"
    write_csv(out/'cells'/f'{name}.csv',rows)
    save_json(out/'cells'/f'{name}.json',metadata)
    if preds:np.savez_compressed(out/'predictions'/f'{name}.npz',**preds)
    print('DONE',name,'seconds',round(metadata['elapsed_seconds'],2),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model',choices=['ridge','mlp'],required=True);p.add_argument('--profile',action='store_true')
    a=p.parse_args();out=a.out
    protocol=json.loads((out/'protocol.json').read_text())
    expected=(out/'protocol.sha256').read_text().split()[0]
    if digest(out/'protocol.json')!=expected:raise ValueError('Protocol hash changed')
    if digest(out/'features_causal.npz')!=protocol['feature_sha256']:raise ValueError('Feature hash changed')
    z=np.load(out/'features_causal.npz')
    torch.set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK',4)))
    torch.use_deterministic_algorithms(True)
    device='cuda' if a.model=='mlp' and torch.cuda.is_available() else 'cpu'
    if a.model=='mlp' and device!='cuda':raise RuntimeError('Neural fits must use the profiled GPU')
    (out/'cells').mkdir(exist_ok=True);(out/'predictions').mkdir(exist_ok=True)
    if a.profile:
        run_cell(z,protocol,protocol['folds'][0],12,240,'combined','EC','mlp',device,out,True);return
    if a.model=='mlp' and not (out/'profile.json').exists():raise ValueError('Profile must finish before bounded neural study')
    for fold,n,sec,info,state in conditions(protocol):
        name=f"{a.model}_f{fold['fold']}_n{n}_s{sec}_{info}_{state}"
        if (out/'cells'/f'{name}.json').exists():
            print('RESUME_SKIP',name,flush=True);continue
        run_cell(z,protocol,fold,n,sec,info,state,a.model,device,out)
    print('STUDY_COMPLETE',a.model,flush=True)


if __name__=='__main__':main()
