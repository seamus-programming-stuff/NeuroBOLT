#!/usr/bin/env python3
"""Versioned metadata-only clock amendment, then unchanged frozen-model secondary test."""
import argparse
import copy
import json
import os
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd

import natview_data as nd
import natview_score as ns
from natview_segment_audit import certify
from natview_stage import digest,save_json

BASE=Path('reports/thesis_exploration/natview')
OUT=BASE/'v2'
DERIV=nd.DERIV/'v2'
SUBJECTS=['sub-04','sub-05','sub-06','sub-08','sub-10','sub-11','sub-12','sub-13']


def stage_mask_diagnostic(d):
    mask=np.ones(d['mask_length'],bool)
    for a,b in d['mask_false_intervals']:mask[a:b]=False
    original=np.flatnonzero(mask);additional=[];masked_anchor=0;outside=0
    for row in d['anchors']:
        q=row['original_sample_0based'];i=int(np.floor(q))
        if not 0<=i<len(mask):outside+=1;continue
        if not mask[i]:masked_anchor+=1;continue
        intermediate=np.searchsorted(original,i)+q-i
        additional.append(intermediate-row['processed_sample_0based'])
    aa=np.array(additional)
    return {'mask_length':d['mask_length'],'mask_true':d['mask_true_samples'],'pnts':d['pnts'],
       'mask_true_minus_payload_samples':d['mask_true_samples']-d['pnts'],
       'surviving_anchors_inside_mask_false_regions':masked_anchor,'anchors_outside_mask':outside,
       'additional_stage_offset_min_samples':float(aa.min()) if len(aa) else None,
       'additional_stage_offset_max_samples':float(aa.max()) if len(aa) else None,
       'additional_stage_offset_decreases':int(np.sum(np.diff(aa)<-1.01)),
       'consistent_with_mask_of_one_stage_followed_by_more_excision':bool(len(aa) and masked_anchor==0 and outside==0 and aa.min()>=-1.01 and np.all(np.diff(aa)>=-1.01)),
       'qualification':'a consistency test, not proof of which internal ASR stage wrote clean_sample_mask; published step7 enables both burst rejection and window rejection'}


def certified_adapter(d,raw_times):
    cert=certify(d)
    if not cert['event_time_map_certifiable']:raise ValueError('Original/processed event offset decreases')
    if not d['raw_R128']==d['urevents_R128']==d['nvol']==len(raw_times):raise ValueError('Raw/original/BOLD count mismatch')
    if d['raw_urevent_origin_residual_seconds']>.0041:raise ValueError('Raw/urevent clocks disagree')
    if np.max(abs(np.diff(raw_times)-2.1))>.006:raise ValueError('Irregular raw TR')
    if d['eye_pulses']<.9*d['nvol'] or d['eye_unique_matched_volumes']!=d['eye_pulses'] or d['eye_max_abs_raw_match_error_seconds']>.05:
        raise ValueError('Original independent eye clock gate fails')
    if d['biopac_pulses']!=d['nvol'] or d['biopac_relative_first_residual_seconds']>.04:
        raise ValueError('Original independent BIOPAC gate fails')
    anchors=d['anchors'];segments=[]
    boundary=np.unique([int(np.floor(x['latency'])) for x in d['boundaries'] if x['duration'] is not None and np.isfinite(x['duration']) and 0<float(x['latency'])<d['pnts']])
    for block in cert['constant_offset_blocks']:
        offset=block['offset_samples']
        if abs(offset-round(offset))>1e-6 or block['max_offset_residual_samples']>1e-6:
            raise ValueError('Excision offset is not an exact integer sample count')
        lo,hi=block['processed_start_sample'],block['processed_stop_sample']
        cuts=[lo]+[float(b) for b in boundary if lo<b<hi]+[hi+1e-7]
        for left,right in zip(cuts[:-1],cuts[1:]):
            aa=[x for x in anchors if left<=x['processed_sample_0based']<right and abs(x['offset_samples']-offset)<1e-6]
            if len(aa)<2:continue
            # No extrapolation outside the first/last bracketing event anchors.
            a=int(np.ceil(aa[0]['processed_sample_0based']));b=int(np.floor(aa[-1]['processed_sample_0based']))+1
            if b>a:segments.append({'processed_start':a,'processed_stop_exclusive':b,'offset_samples':int(round(offset)),
                 'original_start':a+int(round(offset)),'original_stop_exclusive':b+int(round(offset)),
                 'anchor_count':len(aa)})
    original_trigger=(raw_times+d['raw_urevent_offset_seconds'])*250
    windows=[];mapping=[]
    for row in anchors:
        if row['type']!='R128':continue
        q=row['original_sample_0based'];p=row['processed_sample_0based']
        volume=int(np.argmin(abs(original_trigger-q)))
        if abs(original_trigger[volume]-q)>1.01:raise ValueError('Processed event does not identify a raw scanner volume')
        base={'volume':volume,'event_sample_1based':p+1,'urevent_sample_1based':q+1}
        mapping.append(base)
        hit=[s for s in segments if s['processed_start']<=p-29*250 and p+5*250<=s['processed_stop_exclusive']-1]
        if len(hit)==1:windows.append({**base,**hit[0],'task_seconds':float(raw_times[volume])})
    if len(set(r['volume'] for r in mapping))!=len(mapping):raise ValueError('Duplicate processed volume identity')
    offset=d['raw_urevent_offset_seconds'];intervals=[]
    ss=sorted(segments,key=lambda s:s['original_start'])
    for a,b in zip(ss[:-1],ss[1:]):
        if b['original_start']>a['original_stop_exclusive']:
            intervals.append([a['original_stop_exclusive']/250,b['original_start']/250])
    retained=set(r['volume'] for r in windows)
    return {'subject':d['subject'],'clock_resolved':True,'n_volumes':d['nvol'],'sfreq':250,
       'raw_R128':d['raw_R128'],'urevent_R128':d['urevents_R128'],'processed_R128':d['events_R128'],
       'original_to_task_offset_seconds':offset,'raw_scanner_onsets_task_seconds':raw_times.tolist(),
       'certified_segments':segments,'certified_physical_windows':windows,'event_volume_mapping':mapping,
       'retained_target_frames':len(windows),'retained_target_seconds':len(windows)*2.1,
       'excluded_volumes':[{'volume':i,'reason':'no fully bracketed24s physical history plus original5s margins in one event-certified boundary-free segment'} for i in range(d['nvol']) if i not in retained],
       'removed_intervals_recording_seconds':intervals,
       'interval_plot_qualification':'uncertified intervals between event-bracketed continuous segments; includes real excisions and unextrapolated edge samples, not all are proven removed samples',
       'removed_seconds':float((max(x['offset_samples'] for x in anchors)-min(x['offset_samples'] for x in anchors))/250),
       'removed_seconds_qualification':'known cumulative excision offset change between first/last retained anchors; source mask not repaired',
       'all_anchor_offsets_nondecreasing':True,'no_prediction_or_BOLD_clock_selection':True,
       'source_mask_diagnostic':stage_mask_diagnostic(d),
       'eye':{'scanner_pulse_count':d['eye_pulses'],'max_abs_match_error_seconds':d['eye_max_abs_raw_match_error_seconds'],'unmatched_volumes':d['eye_unmatched_volumes']},
       'biopac':{'pulse_count':d['biopac_pulses'],'max_relative_clock_residual_seconds':d['biopac_relative_first_residual_seconds'],
                 'respiration_span_seconds':d['respiration_time_span_seconds']}}


def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for sub in SUBJECTS:
        d=json.loads((BASE/f'{sub}_independent_clock_diagnostic.json').read_text())
        stem,pre,raw,func=nd.paths(sub)
        rt=pd.read_csv(raw/f'eeg/{stem}_events.tsv',sep='\t');times=rt.loc[rt['value'].astype(str).str.strip()=='R128','onset'].to_numpy(float)
        qc=certified_adapter(d,times)
        em=json.loads((pre/f'eeg/{stem}_recording-eyetracking_physio.json').read_text());eye=nd.table(pre/f'eeg/{stem}_recording-eyetracking_physio.tsv.gz',em)
        qc['eye']['interpolated_fraction']=float((eye['Interpolated_Samples']!=0).mean())
        save_json(OUT/f'{sub}_certified_metadata.json',nd.finite_json(qc))
        rows.append({'subject':sub,'frames_before_amplitude_motion_QC':qc['retained_target_frames'],
                     'min60_pass_before_additional_QC':qc['retained_target_frames']>=60,
                     **qc['source_mask_diagnostic']})
        print('V2 METADATA',sub,qc['retained_target_frames'],'frames; no BOLD values read',flush=True)
    save_json(OUT/'metadata_audit_summary.json',{'runs':rows,'slurm_job_id':os.environ['SLURM_JOB_ID'],
          'policy':'all surviving anchors must have monotonic, exact integer original-minus-processed offsets; same-offset bracketing anchors certify physical time; split at every source boundary; no extrapolation; original24s+5s margins and min60 retained',
          'no_BOLD_values_or_predictions_read':True,'source_sha256':digest(__file__)})


def freeze():
    import subprocess
    import sys
    assert (BASE/'v1/snapshot_receipt.json').exists(),'Preserve completed strict-v1 first'
    assert not (OUT/'freeze.json').exists(),'Never overwrite v2 lock'
    r=subprocess.run([sys.executable,'scripts/natview_v2_tests.py'],capture_output=True,text=True)
    (OUT/'tests.txt').write_text(r.stdout+r.stderr);r.check_returncode()
    protocol=json.loads((BASE/'protocol.json').read_text());original=json.loads((BASE/'freeze.json').read_text())
    protocol.update(version=2,scope='secondary exploratory amended metadata adapter; NOT original untouched confirmation',
          original_v1_protocol_sha256=original['protocol_sha256'],original_v1_freeze_sha256=digest(BASE/'freeze.json'),
          original_v1_result='7/8 excluded by source-mask contract; only sub12 eligible. Preserved under v1/.',
          amendment='use exact event/urevent sample-offset certificates rather than assuming source clean_sample_mask is cumulative; no source field overwritten',
          v2_clock_policy=json.loads((OUT/'metadata_audit_summary.json').read_text())['policy'],
          v2_numeric_thresholds='original thresholds unchanged:24s history,5s margins,500uV,FD0.5mm+following,min60,eye50ms/BIOPAC40ms',
          model_coefficients_scalers_and_bridge='unchanged from v1 final dd9b894b model and fixed VU/NATVIEW source coordinate bridge',
          frozen_v2_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    protocol['original_v1_clock_contract']=protocol['clock']
    protocol['clock']={'identity':'same ordered raw R128 and event->urevent physical volume identities',
          'certificate':json.loads((OUT/'metadata_audit_summary.json').read_text())['policy'],
          'source_mask':'retained unchanged as stage-specific/possibly noncumulative provenance; never silently expanded or used as cumulative timeline',
          'independent_clocks':'original numeric gates unchanged: raw TR6ms, raw/urevent4.1ms, eye unique>=90% within50ms, BIOPAC count and relative40ms',
          'no_outcome_alignment':'no BOLD values/predictions/correlations used in amendment or sample map'}
    protocol['exclusions']['window']='reject any24s physical history plus original5s margins not fully bracketed by equal-offset event anchors within one source-boundary-free segment; no extrapolation'
    save_json(OUT/'protocol.json',protocol)
    shutil.copy2(BASE/'bridge_geometry.json',OUT/'bridge_geometry.json')
    DERIV.mkdir(parents=True,exist_ok=True);shutil.copy2(nd.DERIV/'vu_common23_prime_geometry_frozen.npz',DERIV/'vu_common23_prime_geometry_frozen.npz')
    files=['scripts/natview_v2.py','scripts/natview_v2_tests.py','scripts/natview_data.py','scripts/natview_score.py','scripts/natview_segment_audit.py']
    metadata={str(p):digest(p) for p in OUT.glob('*_certified_metadata.json')}
    lock={'protocol_sha256':digest(OUT/'protocol.json'),'model_sha256':original['model_sha256'],
          'bridge_geometry_sha256':original['bridge_geometry_sha256'],'metadata_hashes':metadata,
          'code_hashes':{p:digest(p) for p in files},'v1_code_hashes':original['code_hashes'],
          'scope':'secondary exploratory; freeze before v2 predictions; v1 already evaluated one person',
          'frozen_utc':protocol['frozen_v2_utc'],'slurm_job_id':os.environ['SLURM_JOB_ID']}
    assert digest(DERIV/'vu_common23_prime_geometry_frozen.npz')==lock['model_sha256']
    save_json(OUT/'freeze.json',lock);print('V2 FROZEN',lock['protocol_sha256'],flush=True)


def run():
    lock=json.loads((OUT/'freeze.json').read_text());protocol=json.loads((OUT/'protocol.json').read_text())
    assert digest(OUT/'protocol.json')==lock['protocol_sha256']
    assert digest(DERIV/'vu_common23_prime_geometry_frozen.npz')==lock['model_sha256']
    assert digest(OUT/'bridge_geometry.json')==lock['bridge_geometry_sha256']
    for p,h in {**lock['v1_code_hashes'],**lock['code_hashes'],**lock['metadata_hashes']}.items():assert digest(p)==h,p
    nd.OUT=OUT;ns.OUT=OUT;ns.DERIV=DERIV
    save_json(OUT/'v2_outcomes_opened.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'freeze_sha256':digest(OUT/'freeze.json'),'slurm_job_id':os.environ['SLURM_JOB_ID']})
    results=[]
    for sub in SUBJECTS:
        qc=json.loads((OUT/f'{sub}_certified_metadata.json').read_text());stem,pre,raw,func=nd.paths(sub)
        e=nd.read_set(pre/f'eeg/{stem}_eeg.set')
        helper=copy.deepcopy(qc);helper['retained_windows']=[{'volume':w['volume'],
             'segment_start_sample_0based':w['processed_start'],'segment_stop_sample_exclusive':w['processed_stop_exclusive'],
             'urevent_sample_1based':w['event_sample_1based']} for w in qc['certified_physical_windows']]
        x,frame=nd.eeg_features(e,helper,np.ones(int(e['pnts']),bool),sub)
        # Identity computational index mask selects already-certified continuous
        # source excerpts; it is never used as the physical clock or source repair.
        for k in ['channel_bridge','channels_actual','common23_channels','MNE_volts_to_microvolts_max_error_uV','source_SET_history','EEG_spectral_QC','reference_actual','units_input','units_feature']:
            qc[k]=helper[k]
        qc['excluded_volumes']=helper['excluded_volumes']
        motion=np.loadtxt(func/'func_nuisance/func_mc.1D');delta=np.diff(motion,axis=0,prepend=motion[[0]])
        assert motion.shape==(qc['n_volumes'],6)
        fd=(abs(delta[:,:3])*np.pi/180*50).sum(1)+abs(delta[:,3:]).sum(1);bad=fd>.5;bad=bad|np.r_[False,bad[:-1]]
        for f in frame[bad[frame]]:qc['excluded_volumes'].append({'volume':int(f),'reason':'FD>0.5mm or immediately following such frame'})
        keep=~bad[frame];x=x[keep];frame=frame[keep]
        qc.update(feature_frames=frame.tolist(),n_feature_frames=len(frame),retained_target_seconds_after_all_QC=len(frame)*2.1,
                  retained_frame_gaps=int(np.sum(np.diff(frame)!=1)),inclusion_pass=len(frame)>=60,
                  slurm_job_id=os.environ['SLURM_JOB_ID'],scope='amended v2 secondary exploratory')
        qc['motion_QC']={'mean_FD_mm':float(fd.mean()),'max_FD_mm':float(fd.max()),'frames_FD_gt_0p5_or_next':np.flatnonzero(bad).tolist()}
        if qc['inclusion_pass']:
            y,labels=nd.extract_targets(sub,qc);path=DERIV/f'{sub}_derived.npz'
            np.savez_compressed(path,x=x,y=y[frame],frame=frame,labels=np.array(labels));qc['derivative_path']=str(path);qc['derivative_sha256']=digest(path)
        else:qc['exclusion_reason']='fewer than60 frames under unchanged physical-context/amplitude/motion gates; no accuracy metrics computed'
        save_json(OUT/f'{sub}_qc.json',nd.finite_json(qc));results.append(qc)
        print('V2 QC',sub,len(frame),'frames, included',qc['inclusion_pass'],flush=True)
    ns.score_panel(results,protocol,lock)
    s=json.loads((OUT/'machine_summary.json').read_text());s.update(branch='amended_v2_secondary_complete_eligible_panel',
         original_strict_8person_confirmation_achieved=False,scope='secondary exploratory after metadata-only clock amendment; not original untouched confirmation',
         original_v1_summary_sha256=digest(BASE/'v1/machine_summary.json'),original_v1_protocol_sha256=lock['v1_code_hashes'] and json.loads((BASE/'freeze.json').read_text())['protocol_sha256'],
         model_coefficients_scalers_unchanged=True,v2_metadata_freeze_sha256=digest(OUT/'freeze.json'))
    save_json(OUT/'machine_summary.json',s)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['audit','freeze','run'],required=True);a=p.parse_args()
    assert os.environ.get('SLURM_JOB_ID')
    {'audit':audit,'freeze':freeze,'run':run}[a.phase]()
