#!/usr/bin/env python3
"""Can event identities alone certify uninterrupted physical histories? No outcomes."""
import json
import os
import numpy as np
from natview_data import OUT,finite_json
from natview_stage import save_json,digest


def certify(d):
    a=sorted(d['anchors'],key=lambda x:x['processed_sample_0based'])
    p=np.array([x['processed_sample_0based'] for x in a]);o=np.array([x['original_sample_0based'] for x in a]);offset=o-p
    # A valid excision-only timeline has nondecreasing offset. No fitted slope or
    # hand-selected intercept is permitted. Only existing integer sample gaps.
    decreasing=np.flatnonzero(np.diff(offset)<-.01)
    blocks=[];start=0
    for stop in list(np.flatnonzero(abs(np.diff(offset))>.01)+1)+[len(a)]:
        block=a[start:stop]
        if len(block)>=2:
            oo=np.array([x['offset_samples'] for x in block])
            blocks.append({'processed_start_sample':block[0]['processed_sample_0based'],
                 'processed_stop_sample':block[-1]['processed_sample_0based'],
                 'original_start_sample':block[0]['original_sample_0based'],
                 'original_stop_sample':block[-1]['original_sample_0based'],
                 'offset_samples':float(np.median(oo)),'max_offset_residual_samples':float(np.max(abs(oo-np.median(oo)))),
                 'anchors':len(block),'max_anchor_spacing_seconds':float(np.max(np.diff([x['processed_sample_0based'] for x in block]))/250)})
        start=stop
    tr=[x for x in a if x['type']=='R128'];valid=[]
    for x in tr:
        q=x['original_sample_0based']
        match=[b for b in blocks if b['original_start_sample']<=q-29*250 and q+5*250<=b['original_stop_sample']]
        if len(match)==1:valid.append(x)
    return {'subject':d['subject'],'anchor_count':len(a),'offset_decreases':len(decreasing),
            'event_time_map_certifiable':len(decreasing)==0,'constant_offset_blocks':blocks,
            'frames_with_24s_history_and_5s_margins_between_certified_anchors':len(valid),
            'certified_R128_anchors':valid,
            'proof':'original minus processed sample offsets are nondecreasing for excision-only cleaning; equal offsets bracketing a window rule out a hidden excision within it. Do not extrapolate beyond first/last anchor of a constant-offset block.',
            'no_source_mask_repair_performed':True,'no_BOLD_or_EEG_values_read':True}


def main():
    assert os.environ.get('SLURM_JOB_ID')
    rows=[]
    for path in sorted(OUT.glob('sub-*_independent_clock_diagnostic.json')):
        result=certify(json.loads(path.read_text()));save_json(OUT/(result['subject']+'_event_segment_QC.json'),finite_json(result))
        rows.append({k:v for k,v in result.items() if k not in ['constant_offset_blocks','certified_R128_anchors','proof']})
        print('SEGMENTS',result['subject'],'certifiable',result['event_time_map_certifiable'],'nondecreasing violations',result['offset_decreases'],
              'physical windows',result['frames_with_24s_history_and_5s_margins_between_certified_anchors'],flush=True)
    save_json(OUT/'event_segment_QC_summary.json',{'slurm_job_id':os.environ['SLURM_JOB_ID'],'runs':rows,'source_sha256':digest(__file__)})


if __name__=='__main__':main()
