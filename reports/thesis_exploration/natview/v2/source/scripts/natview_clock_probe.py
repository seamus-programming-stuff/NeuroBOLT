#!/usr/bin/env python3
"""Development-only detailed sample mask and boundary comparison."""
import os
import numpy as np
from natview_data import ROOT,OUT,read_set,runs_of_true,finite_json
from natview_stage import save_json


def main():
    assert os.environ.get('SLURM_JOB_ID')
    e=read_set(ROOT/'preproc_data/sub-01/ses-01/eeg/sub-01_ses-01_task-rest_eeg.set')
    mask=np.asarray(e['etc']['clean_sample_mask'],bool);orig=np.flatnonzero(mask)
    boundaries=[{'latency':float(x['latency']),'duration':float(x['duration'])} for x in e['event'] if str(x['type'])=='boundary']
    gaps=[]
    for a,b in runs_of_true(~mask):
        gaps.append({'original_start':a,'original_stop':b,'n_missing':b-a,'expected_boundary_latency':float(mask[:a].sum())+.5})
    anchors=[]
    for x in e['event']:
        u=x.get('urevent',[])
        if np.size(u)!=1 or not np.isfinite(u):continue
        ue=e['urevent'][int(u)-1];p=float(x['latency'])-1;o=float(ue['latency'])-1
        if 0<=int(np.floor(p))<len(orig):
            rec=orig[int(np.floor(p))]+p-np.floor(p)
            anchors.append({'type':str(x['type']),'processed_sample':p,'original_sample':o,'mask_error_samples':rec-o})
    result={'mask_samples':len(mask),'pnts':e['pnts'],'mask_sum':int(mask.sum()),'first_retained':int(orig[0]),
            'last_retained':int(orig[-1]),'boundaries':boundaries,'mask_gaps':gaps,
            'all_anchor_count':len(anchors),'max_all_anchor_error':max(abs(x['mask_error_samples']) for x in anchors),
            'mismatched_anchors':[x for x in anchors if abs(x['mask_error_samples'])>1.01],
            'tail_anchors':anchors[-10:]}
    print(finite_json(result),flush=True);save_json(OUT/'pilot_mask_boundary_probe.json',finite_json(result))


if __name__=='__main__':main()
