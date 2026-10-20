#!/usr/bin/env python3
"""Verify VU cache correspondence per scan against the original construction."""
import os
import gc
from pathlib import Path
import mne
import numpy as np
from natview_data import OUT,VU_AUX,finite_json
from natview_stage import digest,save_json
from baseline_ridge import BAND_SETS,band_power_features
from eval_inter_per_scan import ROIS,CH_NAMES,TR
from dataset_maker.get_datasets import download_vu_dataset
from dataset_maker.preproc import epoching_seq2one,normalize_data
from scipy.signal import butter,filtfilt


def main():
    assert os.environ.get('SLURM_JOB_ID')
    mne.set_log_level('ERROR')
    path=Path('/scratch/hz18/stay0060/NeuroBOLT/checkpoints/learning_curve/features_fine_w24_sub12.npz')
    root='/scratch/hz18/stay0060/NeuroBOLT/data'
    eeg=np.load(path);aux=np.load(VU_AUX);labels=aux['labels'].astype(str).tolist()
    cols=[labels.index(lab) for lab,_ in ROIS];rows=[]
    for scan in aux['scans'].astype(str):
        x=eeg['x_'+scan];y=eeg['y_'+scan];ya=aux['y_all_'+scan];fr=aux['frame_'+scan]
        assert len(x)==len(y)==len(ya)==len(fr),scan+' row count mismatch'
        gap=float(np.max(abs(y-ya[:,cols])))
        assert gap<1e-4,scan+' y7 versus aux y_all mismatch'
        sub,ss=(int(z) for z in scan.replace('sub','').replace('scan','').split('-'))
        raw,fmri,_=download_vu_dataset(sub,ss,root,output_eegmneraw=True)
        raw.load_data().filter(l_freq=.5,h_freq=None,verbose=False)
        source_names=[c.upper() for c in raw.ch_names]
        expected_source_names=CH_NAMES[:-2]+["TP9'","TP10'"]
        assert source_names==expected_source_names,scan+' source cache electrode order differs'
        # Run the actual original epoch selector, carrying source volume index as
        # an artificial target. All frame identities are checked, not inferred
        # from total lengths or from prediction correlation.
        data,epochs=epoching_seq2one(raw,np.arange(len(fmri))[None],-24,0,'R149',ifnorm=0,crop=4800)
        reconstructed=np.asarray(data['fmri']).reshape(-1).astype(int)
        assert np.array_equal(reconstructed,fr),scan+' source/aux frame indices differ'
        audit_idx=np.unique([0,len(fr)//2,len(fr)-1])
        xx=band_power_features(np.stack([data['eeg'][i] for i in audit_idx]),BAND_SETS['fine'],12)
        xgap=float(np.max(abs(xx-x[audit_idx])))
        assert xgap<2e-4,scan+f' source feature rows differ {xgap}'
        b,a=butter(5,.15/(.5/TR),btype='low')
        yt=filtfilt(b,a,fmri[labels].to_numpy().T,axis=1);yt,_=normalize_data(yt)
        ygap=float(np.max(abs(yt[:,fr].T-ya)))
        assert ygap<1e-4,scan+' reconstructed all65 targets differ'
        rows.append({'scan':scan,'rows':len(x),'first_frame':int(fr[0]),'last_frame':int(fr[-1]),
                     'literal_source_channel_names':raw.ch_names,
                     'source_prime_qualifier':'TP9 and TP10 cache positions are literally TP9-prime and TP10-prime in VU; spatial bridge audited separately',
                     'all_source_frame_indices_exact':True,'cache_carries_frame_keys':('frame_'+scan in eeg.files),
                     'y7_aux_max_abs_error':gap,'source_all65_max_abs_error':ygap,
                     'source_feature_audit_rows':audit_idx.tolist(),'source_feature_max_abs_error':xgap})
        print('CACHE PASS',scan,len(fr),'xgap',xgap,'ygap',ygap,flush=True)
        del raw,data,epochs,x,y,ya,yt,xx;gc.collect()
    save_json(OUT/'VU_per_scan_cache_audit.json',{'passed':True,'slurm_job_id':os.environ['SLURM_JOB_ID'],
              'scans':rows,'source_frame_reconstruction':'original download_vu_dataset + epoching_seq2one with source frame index target',
              'feature_values_checked':'first/middle/last original windows per scan, all26 x44x12; every target row and frame identity checked',
              'hashes':{str(p):digest(p) for p in [path,VU_AUX,Path(__file__),Path('dataset_maker/preproc.py'),
                        Path('scripts/ridge_learning_curve.py'),Path('scripts/interp_build_cache.py')]}})


if __name__=='__main__':main()
