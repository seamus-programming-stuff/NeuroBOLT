#!/usr/bin/env python3
"""NATVIEW clocks/identity/units/atlas. Never infer alignment from prediction skill."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.signal import butter, filtfilt, resample_poly, welch

from natview_stage import digest, save_json

ROOT=Path('/scratch/hz18/stay0060/NeuroBOLT/data/natview')
DERIV=Path('/scratch/hz18/stay0060/NeuroBOLT/checkpoints/ext/natview')
OUT=Path('reports/thesis_exploration/natview')
ATLAS=Path('/scratch/hz18/stay0060/nilearn_data/difumo_atlases/64/3mm/maps.nii.gz')
ATLAS_LABELS=ATLAS.parents[1]/'labels_64_dictionary.csv'
VU_AUX=Path('/scratch/hz18/stay0060/NeuroBOLT/checkpoints/interp/interp_cache.npz')
VU26=['FP1','FP2','F3','F4','C3','C4','P3','P4','O1','O2','F7','F8','T7','T8','P7','P8','FPZ','FZ','CZ','PZ','POZ','OZ','FT9','FT10','TP9','TP10']
COMMON=[c for c in VU26 if c not in ['F4','FT9','FT10']]


def finite_json(v):
    if isinstance(v,dict):return {str(k):finite_json(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [finite_json(x) for x in v]
    if isinstance(v,np.ndarray):return finite_json(v.tolist())
    if isinstance(v,np.generic):return finite_json(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v


def paths(sub):
    stem=f'{sub}_ses-01_task-rest'
    pre=ROOT/f'preproc_data/{sub}/ses-01'
    raw=ROOT/f'raw_data/{sub}/ses-01'
    func=pre/f'func/{stem}_bold'
    return stem,pre,raw,func


def read_set(path):
    m=loadmat(path,simplify_cells=True)
    return m.get('EEG',m)


def identity_indices(names, requested=COMMON):
    # Case formatting is the only canonicalization; never map electrode identities.
    canonical=[str(c).upper() for c in names]
    if len(set(canonical))!=len(canonical):raise ValueError('Duplicate channel identities')
    missing=[c for c in requested if c not in canonical]
    if missing:raise ValueError('Missing common23 channels: '+str(missing))
    return [canonical.index(c) for c in requested]


def to_microvolts(data, units):
    factors={'uV':1.0,'µV':1.0,'V':1e6}
    if units not in factors:raise ValueError('Unknown units: '+units)
    return np.asarray(data)*factors[units]


def common23_bridge(data,names,channel_coordinates=None,geometry=None):
    """Fixed metadata-only extension for up to three additional missing electrodes.

    All donors are measured scalp channels with source SET positions. No EEG
    outcome, BOLD outcome or channel substitution enters this interpolation.
    """
    import mne
    canonical=[str(c).upper() for c in names]
    if len(set(canonical))!=len(canonical):raise ValueError('Duplicate scalp channel identities')
    if geometry is None:geometry=json.loads((OUT/'bridge_geometry.json').read_text())
    literal=geometry['feature_channels_literal_VU'];always=geometry['always_interpolate']
    additional=[c for c in literal if c not in always and c not in canonical]
    if len(additional)>3:raise ValueError('More than 3 additional missing bridge electrodes; frozen exclusion')
    missing=additional+always
    positions={}
    if channel_coordinates is None:raise ValueError('Explicit donor electrode geometry required')
    for row in channel_coordinates:
        c=str(row['labels']).upper()
        p=np.array([row[k] for k in ['X','Y','Z']],float)
        if np.isfinite(p).all() and np.linalg.norm(p)>0:
            p=p/np.linalg.norm(p);positions[c]=np.array([-p[1],p[0],p[2]])*.095
    donor=[c for c in canonical if c in positions]
    if len(donor)<40:raise ValueError('Fewer than 40 measured scalp donors with finite source coordinates')
    use=donor+missing
    target=geometry['target_positions_head_m']
    montage=mne.channels.make_dig_montage(ch_pos={**{c:positions[c] for c in donor},**{c:target[c] for c in missing}},coord_frame='head')
    rr=mne.io.RawArray(np.r_[np.asarray(data)[[canonical.index(c) for c in donor]],np.zeros((len(missing),data.shape[1]))],
                       mne.create_info(use,250,'eeg'),verbose=False)
    rr.set_montage(montage);rr.info['bads']=missing
    rr.interpolate_bads(reset_bads=False,mode='accurate',origin=(0.,0.,0.),method={'eeg':'spline'},verbose=False)
    return rr.get_data(picks=literal),{'interpolated':missing,'always_interpolated_VU_prime_sites':always,
           'additional_missing_interpolated':additional,'measured_feature_channels':[c for c in literal if c not in missing],
           'n_measured_features':len(literal)-len(missing),'n_interpolated_features':len(missing),'donors':donor,
           'feature_channels_literal_VU':literal,'geometry_sha256':digest(OUT/'bridge_geometry.json') if (OUT/'bridge_geometry.json').exists() else None,
           'method':'MNE accurate spherical spline; source SET donor directions and VU target directions on95mm sphere, fixed origin0',
           'reason':'additional source-cleaned electrodes missing; policy specified from channel metadata before reserved outcome arrays',
           'reference':'original source reference retained; no reference harmonization'}


def runs_of_true(mask):
    edges=np.diff(np.r_[False,np.asarray(mask,dtype=bool),False].astype(int))
    return list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))


def physical_window_segment(segments,time_seconds,fs=250):
    return next(((a,b) for a,b in segments if a/fs<=time_seconds-29 and time_seconds+5<=b/fs),None)


def validate_sample_map(e):
    fs=float(e['srate'])
    if fs!=250:raise ValueError('Unfrozen EEG sample rate')
    mask=np.asarray(e['etc']['clean_sample_mask'],dtype=bool)
    if mask.sum()!=int(e['pnts']):raise ValueError('Sample mask does not reconstruct cleaned data')
    original=np.flatnonzero(mask)
    ev=list(e['event']);ue=list(e['urevent'])
    triggers=[(i,x) for i,x in enumerate(ue) if str(x['type']).strip()=='R128']
    ue_index={i:k for k,(i,x) in enumerate(triggers)}
    rows=[]
    for x in ev:
        if str(x['type']).strip()!='R128':continue
        u=int(x['urevent'])-1
        if u not in ue_index:raise ValueError('R128 event link is not R128 urevent')
        p=float(x['latency'])-1;orig=float(ue[u]['latency'])-1
        # Fractional event latencies must preserve the exact integer excision offset.
        i=int(np.floor(p))
        rec=original[i]+p-i
        if abs(rec-orig)>1.01:raise ValueError(f'urevent/mask mismatch {rec-orig} samples')
        rows.append({'volume':ue_index[u],'event_sample_1based':p+1,'urevent_sample_1based':orig+1,
                     'mask_reconstruction_error_samples':rec-orig,'urevent_index_1based':u+1})
    boundaries=[x for x in ev if str(x['type']).strip()=='boundary' and np.size(x.get('duration',[]))==1 and np.isfinite(x['duration'])]
    # Confirm the mask against ALL surviving event->urevent identities, not just
    # periodic scanner pulses. A source boundary can understate a merged excision:
    # pilot gap 732 samples has stored duration335. Never overwrite the source.
    anchor_count=0;max_anchor_error=0.
    for x in ev:
        u=x.get('urevent',[])
        if np.size(u)!=1 or not np.isfinite(u):continue
        ue0=ue[int(u)-1];p=float(x['latency'])-1;o=float(ue0['latency'])-1
        if not 0<=int(np.floor(p))<len(original):continue
        rec=original[int(np.floor(p))]+p-np.floor(p)
        err=abs(rec-o);max_anchor_error=max(max_anchor_error,err);anchor_count+=1
        if err>1.01:raise ValueError('Sample mask disagrees with surviving event/urevent anchor')
    # Every interior mask gap must have an actual boundary at its compressed
    # position. Duration discrepancies are retained verbatim in the clock audit.
    for a,b in runs_of_true(~mask):
        if a==0 or b==len(mask):continue
        latency=float(mask[:a].sum())+.5
        match=[x for x in boundaries if abs(float(x['latency'])-latency)<=1]
        if len(match)!=1:raise ValueError('Interior excision lacks matching boundary position')
    return mask,triggers,rows,boundaries


def table(path,meta):
    return pd.read_csv(path,sep='\t',header=None,names=meta['Columns'])


def sparse_pulses(times,codes):
    """BIOPAC release stores only high samples; adjacent high rows form one pulse."""
    times=np.asarray(times,float);codes=np.asarray(codes,float)
    if not (np.isfinite(times).all() and np.isfinite(codes).all()):raise ValueError('Nonfinite pulse list')
    if np.any(np.diff(times)<=0):raise ValueError('Pulse list time must increase')
    hi=codes>0
    if not hi.any():raise ValueError('No positive trigger codes')
    tt=times[hi]
    # At 62.5 Hz duplicate high samples are 16 ms apart. One TR is 2.1 s.
    return tt[np.r_[True,np.diff(tt)>.1]]


def clock_audit(sub,e,nvol):
    stem,pre,raw,func=paths(sub)
    mask,triggers,rows,boundaries=validate_sample_map(e)
    discrepancies=[]
    for a,b in runs_of_true(~mask):
        if a==0 or b==len(mask):continue
        lat=float(mask[:a].sum())+.5
        bd=next(x for x in boundaries if abs(float(x['latency'])-lat)<=1)
        if abs(float(bd['duration'])-(b-a))>1:
            discrepancies.append({'boundary_latency_1based':lat,'stored_duration_samples':float(bd['duration']),
                                  'mask_removed_samples':b-a,'physical_gap_start_sample':a,'physical_gap_stop_sample':b})
    rt=pd.read_csv(raw/f'eeg/{stem}_events.tsv',sep='\t')
    raw_tr=rt.loc[rt['value'].astype(str).str.strip()=='R128','onset'].to_numpy(float)
    uetime=np.array([(float(x['latency'])-1)/250 for i,x in triggers])
    if not len(raw_tr)==len(triggers)==nvol:raise ValueError('Raw events/urevents/BOLD count differs; no truncation')
    offsets=uetime-raw_tr;offset=float(np.median(offsets))
    if np.max(abs(offsets-offset))>.0041:raise ValueError('Raw and urevent clocks cannot be reconciled')
    trerr=np.diff(raw_tr)-2.1
    if np.max(abs(trerr))>.006:raise ValueError('Raw scanner gap/irregular TR')
    eye_meta=json.loads((pre/f'eeg/{stem}_recording-eyetracking_physio.json').read_text())
    eye=table(pre/f'eeg/{stem}_recording-eyetracking_physio.tsv.gz',eye_meta)
    # The Time column already contains its task-relative offset; do NOT add StartTime.
    et=eye['Time'].to_numpy(float);hi=eye['fMRI_Volume_Trigger'].to_numpy(float)>0
    epi=np.flatnonzero(hi & ~np.r_[False,hi[:-1]])
    ep=et[epi]
    nearest=np.argmin(abs(ep[:,None]-raw_tr[None,:]),axis=1)
    eyeerr=ep-raw_tr[nearest]
    if len(ep)<int(.9*nvol) or len(np.unique(nearest))!=len(ep) or np.max(abs(eyeerr))>.05:
        raise ValueError('Eye scanner pulse mapping fails predeclared 50ms/90% threshold')
    trig_meta=json.loads((raw/f'eeg/{stem}_recording-trigger_physio.json').read_text())
    bi=table(raw/f'eeg/{stem}_recording-trigger_physio.tsv.gz',trig_meta)
    bp=sparse_pulses(bi.iloc[:,0],bi.iloc[:,1])
    if len(bp)!=nvol:raise ValueError(f'BIOPAC pulse count {len(bp)} differs from {nvol}')
    bdiff=(bp-bp[0])-(raw_tr-raw_tr[0])
    if np.max(abs(bdiff))>.04:raise ValueError('BIOPAC scanner pulse differences exceed 40ms')
    resp_meta=json.loads((raw/f'eeg/{stem}_recording-respiratory_physio.json').read_text())
    resp=table(raw/f'eeg/{stem}_recording-respiratory_physio.tsv.gz',resp_meta)
    segments=runs_of_true(mask)
    # Every window must lie entirely in a retained physical segment, with 5 s on either
    # side for retrospective filtering/resampling. No compressed-time concatenation.
    kept=[]; exclusions=[]
    for r in rows:
        t=(r['urevent_sample_1based']-1)/250
        seg=physical_window_segment(segments,t)
        if seg:
            kept.append({**r,'segment_start_sample_0based':seg[0],'segment_stop_sample_exclusive':seg[1],
                         'task_seconds':float(raw_tr[r['volume']]),'original_recording_seconds':t})
        else:exclusions.append({'volume':r['volume'],'reason':'24s physical history plus 5s filter margins crosses removed interval or acquisition edge'})
    surviving={r['volume'] for r in rows}
    exclusions += [{'volume':v,'reason':'scanner event excised by source EEG cleaning'} for v in range(nvol) if v not in surviving]
    result={'subject':sub,'clock_resolved':True,'n_volumes':nvol,'sfreq':250,'raw_R128':len(raw_tr),
            'urevent_R128':len(triggers),'processed_R128':len(rows),'boundary_count_including_start':len(boundaries)+1,
            'original_samples':len(mask),'retained_samples':int(mask.sum()),'removed_samples':int((~mask).sum()),
            'removed_seconds':float((~mask).sum()/250),'original_to_task_offset_seconds':offset,
            'raw_urevent_offset_max_residual_seconds':float(np.max(abs(offsets-offset))),
            'raw_scanner_onsets_task_seconds':raw_tr.tolist(),'original_urevent_onsets_recording_seconds':uetime.tolist(),
            'raw_TR_max_error_seconds':float(np.max(abs(trerr))),
            'removed_intervals_recording_seconds':[[a/250,b/250] for a,b in runs_of_true(~mask)],
            'boundaries':[{'latency_1based':float(x['latency']),'removed_samples':float(x['duration'])} for x in boundaries],
            'boundary_duration_discrepancies':discrepancies,
            'boundary_discrepancy_policy':'preserve stored durations; use exact cumulative clean_sample_mask only if every surviving event/urevent anchor agrees within 1.01 samples and every interior mask gap has a matching boundary position',
            'all_surviving_anchor_count':sum(np.size(x.get('urevent',[]))==1 for x in e['event']),
            'event_volume_mapping':rows,'retained_windows':kept,'excluded_volumes':sorted(exclusions,key=lambda r:r['volume']),
            'retained_target_frames':len(kept),'retained_target_seconds':len(kept)*2.1,
            'eye':{'scanner_pulse_count':len(ep),'pulse_task_seconds':ep.tolist(),'matched_volumes':nearest.tolist(),
                   'unmatched_volumes':sorted(set(range(nvol))-set(nearest)),
                   'max_abs_match_error_seconds':float(np.max(abs(eyeerr))),
                   'first_time_column':float(et[0]),'last_time_column':float(et[-1]),'StartTime_sidecar':eye_meta['StartTime'],
                   'time_column_nonincreasing_steps':int(np.sum(np.diff(et)<=0)),
                   'pupil_nonzero_fraction':float((eye['Pupil_Area']>0).mean()),
                   'interpolated_fraction':float((eye['Interpolated_Samples']!=0).mean()),
                   'blink_code_values':np.unique(eye['Blinks']).tolist(),
                   'interpretation':'QC only; uncalibrated pupil area; missing or interpolated pupil is not sleep'},
            'biopac':{'file_rows':len(bi),'code_values':np.unique(bi.iloc[:,1]).tolist(),
                      'format':'sparse positive pulse sample list; group consecutive high timestamps within 100ms',
                      'pulse_count':len(bp),'pulse_seconds':bp.tolist(),'relative_to_first_trigger':True,
                      'max_relative_clock_residual_seconds':float(np.max(abs(bdiff))),
                      'respiration_first_seconds':float(resp.iloc[0,0]),'respiration_last_seconds':float(resp.iloc[-1,0]),
                      'respiration_finite_fraction':float(np.isfinite(resp.iloc[:,1]).mean()),'respiration_units':'V'},
            'no_outcome_based_clock_selection':True,'clock_rule':'raw ordered R128 = volume0..N-1; event urevent links + exact clean_sample_mask; eye task clock nearest <=50ms; BIOPAC ordered pulses relative to first <=40ms',
            'volume_drop_rule':'zero; pinned released CCS wrapper numDropping=0; raw and processed 288 volumes in pilot'}
    return result,mask,eye,resp


def eeg_features(e,qc,mask,sub):
    import mne
    from baseline_ridge import BAND_SETS,band_power_features
    names=[x['labels'] for x in e['chanlocs']]
    stem,pre,raw,func=paths(sub)
    channels=pd.read_csv(pre/f'eeg/{stem}_channels.tsv',sep='\t')
    if list(channels['name'].astype(str))!=names:raise ValueError('Channel sidecar differs from actual SET ordering')
    units=set(channels['units'].astype(str))
    if len(units)!=1:raise ValueError('Mixed channel units')
    all_data=to_microvolts(e['data'],units.pop())
    if not np.isfinite(all_data).all():raise ValueError('Nonfinite EEG: no filling authorized')
    data,bridge=common23_bridge(all_data,names,e['chanlocs'])
    check=mne.io.read_raw_eeglab(str(pre/f'eeg/{stem}_eeg.set'),preload=False,verbose=False)
    unit_error=float(np.max(abs(check.get_data(start=0,stop=100)*1e6-all_data[:,:100])))
    if unit_error>1e-4:raise ValueError('EEGLAB uV versus MNE volts conversion differs')
    cumulative=np.r_[0,np.cumsum(mask)]
    xx=[];frames=[];amp=[];segments={}
    for r in qc['retained_windows']:
        a,b=r['segment_start_sample_0based'],r['segment_stop_sample_exclusive']
        if (a,b) not in segments:
            arr=data[:,cumulative[a]:cumulative[b]]
            arr=resample_poly(arr,4,5,axis=1)  # antialiasing; each contiguous physical segment independently
            segments[a,b]=mne.filter.filter_data(arr.astype(float),200,l_freq=.5,h_freq=None,verbose=False)
        segment=segments[a,b]
        end=int(round(((r['urevent_sample_1based']-1)-a)*200/250))
        window=segment[:,end-4800:end+1]
        if window.shape!=(23,4801):raise ValueError('Incomplete physical window')
        if np.max(np.ptp(window,axis=1))>500:
            qc['excluded_volumes'].append({'volume':r['volume'],'reason':'common23 peak-to-peak >500 uV'})
            continue
        window=(window-window.mean(1,keepdims=True))[:,:4800]
        xx.append(band_power_features(window[None],BAND_SETS['fine'],12)[0]);frames.append(r['volume'])
        amp.append(float(np.max(np.ptp(window,axis=1))))
    qc['channels_actual']=names;qc['common23_channels']=bridge['feature_channels_literal_VU'];qc['channel_bridge']=bridge
    qc['reference_actual']=str(e.get('ref'));qc['units_input']='uV';qc['units_feature']='uV^2/Hz, natural log(power+1e-12)'
    qc['feature_frames']=frames;qc['n_feature_frames']=len(frames);qc['max_retained_peak_to_peak_uV']=max(amp) if amp else None
    qc['retained_target_seconds_after_amplitude_QC']=len(frames)*2.1
    qc['MNE_volts_to_microvolts_max_error_uV']=unit_error
    qc['source_SET_history']=str(e.get('history',''))
    f,power=welch(data,fs=250,nperseg=1000,axis=1)
    qc['EEG_spectral_QC']={'median_channel_RMS_uV':float(np.median(np.sqrt((data*data).mean(1)))),
       'median_channel_power_45_100_over_1_45':float(np.median(power[:,(f>=45)&(f<100)].sum(1)/power[:,(f>=1)&(f<45)].sum(1))),
       'interpretation':'descriptive corrected EEG amplitude/spectrum; does not prove absence of residual MR/BCG artifacts'}
    return np.asarray(xx,dtype='float32'),np.asarray(frames,dtype='int32')


def atlas_order(atlas_labels,vu_labels):
    if len(atlas_labels)!=64 or len(set(atlas_labels))!=64:raise ValueError('Atlas must have 64 unique regions')
    region=[x for x in vu_labels if x!='global signal clean']
    if set(region)!=set(atlas_labels) or len(vu_labels)!=65:raise ValueError('DiFuMo/VU target identities differ')
    return [atlas_labels.index(x) if x!='global signal clean' else 64 for x in vu_labels]


def extract_targets(sub,qc):
    import nibabel as nib
    from nilearn.maskers import NiftiMapsMasker
    from dataset_maker.preproc import normalize_data
    stem,pre,raw,func=paths(sub)
    path=func/'func_preproc/func_pp_nofilt_sm0.mni152.3mm.nii.gz'
    img=nib.load(path);atlas=nib.load(ATLAS)
    if len(atlas.shape)!=4 or atlas.shape[-1]!=64:raise ValueError('Atlas dimension mismatch')
    if len(img.shape)!=4 or img.shape[-1]!=qc['n_volumes']:raise ValueError('Target volume mismatch')
    if abs(float(img.header.get_zooms()[3])-2.1)>1e-4:raise ValueError('Unexpected TR')
    labels=pd.read_csv(ATLAS_LABELS)['Difumo_names'].tolist();vu=np.load(VU_AUX)['labels'].astype(str).tolist()
    order=atlas_order(labels,vu)
    data=img.get_fdata(dtype='float32')
    if not np.isfinite(data).all():raise ValueError('Nonfinite released volume')
    # Source brain mask is in native EPI coordinates. Do not misregister it by
    # merely resampling an affine. Define the released MNI nonzero support explicitly.
    support=np.any(data!=0,axis=3) & (data.std(axis=3)>1e-8)
    maskimg=nib.Nifti1Image(support.astype('uint8'),img.affine)
    masker=NiftiMapsMasker(str(ATLAS),mask_img=maskimg,detrend=False,standardize=False,
                          resampling_target='data',t_r=2.1,reports=False)
    regions=masker.fit_transform(img)
    if regions.shape!=(img.shape[3],64):raise ValueError('Lost atlas regions')
    global_signal=data[support].mean(0)
    y=np.c_[regions,global_signal][:,order].T
    b,a=butter(5,.15/(.5/2.1),btype='low')
    y=filtfilt(b,a,y,axis=1);y,_=normalize_data(y)
    qc['target_extraction']={'bold_shape':list(img.shape),'bold_affine':img.affine.tolist(),
        'atlas_shape':list(atlas.shape),'atlas_affine':atlas.affine.tolist(),'atlas_sha256':digest(ATLAS),
        'atlas_labels_sha256':digest(ATLAS_LABELS),'labels_in_model_order':vu,'atlas_column_order':order,
        'global_mask':'nonzero temporal support of released MNI no-GSR volume, temporal sd>1e-8',
        'global_voxels':int(support.sum()),'target_filter':'5th order 0.15Hz Butterworth filtfilt',
        'normalization':'full-run demean + absolute 95th percentile scaling; retrospective target definition',
        'released_processing':'CCS 24 motion parameters + WM/CSF; no GSR/no temporal filter/no smoothing; no extra nuisance regression',
        'native_mask_shape':list(nib.load(func/'func_reg/func_pp_mask.nii.gz').shape),
        'bold_sha256':digest(path),'output_shape':[img.shape[3],65]}
    return y.T.astype('float32'),vu
