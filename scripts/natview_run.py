#!/usr/bin/env python3
"""Pilot QC or locked reserved panel evaluation; no fMRI-driven alignment."""
import argparse
import importlib.metadata
import json
import os
import time
import traceback
from pathlib import Path

import nibabel as nib
import numpy as np

from natview_data import (ATLAS,ATLAS_LABELS,COMMON,DERIV,OUT,ROOT,clock_audit,eeg_features,
                          extract_targets,finite_json,paths,read_set)
from natview_stage import digest,save_json


def process(sub):
    stem,pre,raw,func=paths(sub)
    e=read_set(pre/f'eeg/{stem}_eeg.set')
    bold=func/'func_preproc/func_pp_nofilt_sm0.mni152.3mm.nii.gz'
    qc,mask,eye,resp=clock_audit(sub,e,nib.load(bold).shape[-1])
    save_json(OUT/f'{sub}_clock.json',finite_json(qc))
    print('CLOCK',sub,'PASS',qc['processed_R128'],'/',qc['n_volumes'],'physical windows',qc['retained_target_frames'],flush=True)
    x,frame=eeg_features(e,qc,mask,sub)
    # AFNI 3dvolreg: roll,pitch,yaw in degrees, dS,dL,dP in mm.
    motion=np.loadtxt(func/'func_nuisance/func_mc.1D')
    if motion.shape!=(qc['n_volumes'],6):raise ValueError('Unexpected AFNI motion dimensions')
    delta=np.diff(motion,axis=0,prepend=motion[[0]])
    fd=(abs(delta[:,:3])*np.pi/180*50).sum(1)+abs(delta[:,3:]).sum(1)
    bad=fd>.5;bad=bad | np.r_[False,bad[:-1]]
    for f in frame[bad[frame]]:qc['excluded_volumes'].append({'volume':int(f),'reason':'FD>0.5mm or immediately following such frame'})
    keep=~bad[frame];x=x[keep];frame=frame[keep]
    qc['motion_QC']={'method':'AFNI six parameters degrees/mm; Power FD, 50mm radius',
                      'mean_FD_mm':float(fd.mean()),'max_FD_mm':float(fd.max()),
                      'frames_FD_gt_0p5_or_next':np.flatnonzero(bad).tolist()}
    qc['feature_frames']=frame.tolist();qc['n_feature_frames']=len(frame)
    qc['retained_target_seconds_after_all_QC']=len(frame)*2.1
    qc['retained_frame_gaps']=int(np.sum(np.diff(frame)!=1))
    qc['retained_target_acquisition_span_seconds']=float((frame[-1]-frame[0]+1)*2.1) if len(frame) else 0
    qc['inclusion_pass']=len(frame)>=60
    y,labels=extract_targets(sub,qc)
    DERIV.mkdir(parents=True,exist_ok=True)
    dest=DERIV/f'{sub}_derived.npz'
    np.savez_compressed(dest,x=x,y=y[frame],frame=frame,labels=np.array(labels),fd=fd[frame])
    qc['derivative_path']=str(dest);qc['derivative_sha256']=digest(dest)
    qc['slurm_job_id']=os.environ['SLURM_JOB_ID'];qc['code_sha256']=digest('scripts/natview_data.py')
    qc['causal_context']='24s feature history lies in one physical segment; zero-phase segment filtering, source artifact/ICA cleanup, full-run target filtering and normalization are retrospective; no online-causal claim'
    save_json(OUT/f'{sub}_qc.json',finite_json(qc))
    print('DERIVED',sub,'frames',len(frame),'inclusion',qc['inclusion_pass'],'DiFuMo65',y.shape,flush=True)
    return qc


def check_freeze():
    protocol=json.loads((OUT/'protocol.json').read_text())
    freeze=json.loads((OUT/'freeze.json').read_text())
    assert digest(OUT/'protocol.json')==freeze['protocol_sha256']
    assert digest(DERIV/'vu_common23_prime_geometry_frozen.npz')==freeze['model_sha256']
    assert digest(OUT/'bridge_geometry.json')==freeze['bridge_geometry_sha256']
    for p,h in freeze['code_hashes'].items():assert digest(p)==h, 'Frozen code changed '+p
    return protocol,freeze


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['pilot','panel'],required=True);a=p.parse_args()
    assert os.environ.get('SLURM_JOB_ID'),'Use SLURM'
    if a.mode=='panel':
        protocol,freeze=check_freeze();subjects=protocol['reserved_people']
        save_json(OUT/'reserved_outcomes_opened.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                  'slurm_job_id':os.environ['SLURM_JOB_ID'],'freeze_sha256':digest(OUT/'freeze.json')})
    else:subjects=['sub-01']
    results=[]
    for sub in subjects:
        try:results.append(process(sub))
        except Exception as ex:
            traceback.print_exc()
            clock_path=OUT/f'{sub}_clock.json'
            clock_pass=clock_path.exists() and json.loads(clock_path.read_text()).get('clock_resolved',False)
            row={'subject':sub,'clock_resolved':clock_pass,'inclusion_pass':False,'error':str(ex),
                 'slurm_job_id':os.environ['SLURM_JOB_ID'],'traceback':traceback.format_exc()}
            save_json(OUT/f'{sub}_failure.json',row);results.append(row)
    summary={'mode':a.mode,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
             'runs':[{'subject':r['subject'],'clock_resolved':r['clock_resolved'],'inclusion_pass':r['inclusion_pass'],
                      'frames':r.get('n_feature_frames',0),'error':r.get('error')} for r in results],
             'environment':{k:importlib.metadata.version(k) for k in ['numpy','scipy','mne','nibabel','nilearn','torch']}}
    save_json(OUT/f'{a.mode}_build_summary.json',summary)
    if a.mode=='panel':
        from natview_score import score_panel
        score_panel(results,protocol,freeze)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
