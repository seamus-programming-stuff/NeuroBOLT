#!/usr/bin/env python3
"""Independent metadata-only diagnostics for frozen clock exclusions; never scores BOLD."""
import json
import os
from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd
from natview_data import OUT,paths,read_set,runs_of_true,sparse_pulses,table,finite_json
from natview_stage import save_json,digest


def main():
    assert os.environ.get('SLURM_JOB_ID')
    rows=[]
    for sub in ['sub-04','sub-05','sub-06','sub-08','sub-10','sub-11','sub-12','sub-13']:
        stem,pre,raw,func=paths(sub);e=read_set(pre/f'eeg/{stem}_eeg.set')
        ue=list(e['urevent']);ev=list(e['event']);mask=np.asarray(e['etc'].get('clean_sample_mask',[]),bool)
        nvol=nib.load(func/'func_preproc/func_pp_nofilt_sm0.mni152.3mm.nii.gz').shape[-1]
        rt=pd.read_csv(raw/f'eeg/{stem}_events.tsv',sep='\t');rt=rt.loc[rt['value'].astype(str).str.strip()=='R128','onset'].to_numpy(float)
        ut=np.array([(float(x['latency'])-1)/250 for x in ue if str(x['type']).strip()=='R128'])
        anchors=[];boundaries=[]
        for x in ev:
            if str(x['type']).strip()=='boundary':
                boundaries.append({'latency':float(x['latency']),'duration':float(x['duration'])})
            u=x.get('urevent',[])
            if np.size(u)!=1 or not np.isfinite(u):continue
            y=ue[int(u)-1]
            anchors.append({'type':str(x['type']),'processed_sample_0based':float(x['latency'])-1,
                            'original_sample_0based':float(y['latency'])-1,
                            'offset_samples':float(y['latency'])-float(x['latency'])})
        em=json.loads((pre/f'eeg/{stem}_recording-eyetracking_physio.json').read_text());eye=table(pre/f'eeg/{stem}_recording-eyetracking_physio.tsv.gz',em)
        hi=eye['fMRI_Volume_Trigger'].to_numpy(float)>0;ep=eye['Time'].to_numpy(float)[np.flatnonzero(hi&~np.r_[False,hi[:-1]])]
        nearest=np.argmin(abs(ep[:,None]-rt[None,:]),axis=1) if len(ep) else []
        bm=json.loads((raw/f'eeg/{stem}_recording-trigger_physio.json').read_text());bt=table(raw/f'eeg/{stem}_recording-trigger_physio.tsv.gz',bm)
        bp=sparse_pulses(bt.iloc[:,0],bt.iloc[:,1])
        rm=json.loads((raw/f'eeg/{stem}_recording-respiratory_physio.json').read_text());resp=table(raw/f'eeg/{stem}_recording-respiratory_physio.tsv.gz',rm)
        row={'subject':sub,'nvol':nvol,'srate':e['srate'],'pnts':e['pnts'],'mask_shape':list(mask.shape),'mask_length':mask.size,
             'mask_true_samples':int(mask.sum()),'mask_false_samples':int((~mask).sum()),
             'events_R128':sum(str(x['type']).strip()=='R128' for x in ev),'urevents_R128':len(ut),'raw_R128':len(rt),
             'event_urevent_anchor_count':len(anchors),'boundary_count':len(boundaries),
             'raw_urevent_origin_residual_seconds':float(np.ptp(ut-rt)) if len(ut)==len(rt) else None,
             'raw_urevent_offset_seconds':float(np.median(ut-rt)) if len(ut)==len(rt) else None,
             'eye_pulses':len(ep),'eye_unique_matched_volumes':len(np.unique(nearest)),
             'eye_max_abs_raw_match_error_seconds':float(np.max(abs(ep-rt[nearest]))) if len(ep) else None,
             'eye_unmatched_volumes':sorted(set(range(nvol))-set(nearest)),
             'biopac_pulses':len(bp),'biopac_relative_first_residual_seconds':float(np.max(abs((bp-bp[0])-(rt-rt[0])))) if len(bp)==len(rt) else None,
             'respiration_time_span_seconds':[float(resp.iloc[0,0]),float(resp.iloc[-1,0])],
             'source_SET_history':str(e.get('history')),'no_BOLD_outcome_values_read':True,
             'anchors':anchors,'boundaries':boundaries,'mask_false_intervals':[list(x) for x in runs_of_true(~mask)]}
        save_json(OUT/f'{sub}_independent_clock_diagnostic.json',finite_json(row))
        rows.append({k:v for k,v in row.items() if k not in ['anchors','boundaries','mask_false_intervals','source_SET_history']})
        print('DIAGNOSTIC',sub,'pnts',row['pnts'],'mask_true',row['mask_true_samples'],'raw/ue/eye/bio',len(rt),len(ut),len(ep),len(bp),flush=True)
    save_json(OUT/'independent_clock_diagnostic_summary.json',finite_json({'slurm_job_id':os.environ['SLURM_JOB_ID'],'runs':rows,
            'scope':'metadata/trigger diagnostics only; original frozen inclusion rules and scores are unchanged','source_sha256':digest(__file__)}))


if __name__=='__main__':main()
