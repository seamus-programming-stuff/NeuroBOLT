#!/usr/bin/env python3
"""Read-only VU reference/cache provenance audit on SLURM."""
import os
from pathlib import Path
import mne
import numpy as np
import pandas as pd
from scipy.io import loadmat
from natview_data import OUT,VU_AUX
from natview_stage import save_json,digest


def main():
    assert os.environ.get('SLURM_JOB_ID')
    aux=np.load(VU_AUX);scan=str(aux['scans'][0])
    path=Path('/scratch/hz18/stay0060/NeuroBOLT/data/EEG')/(scan+'_eeg.set')
    mat=loadmat(path,simplify_cells=True);e=mat.get('EEG',mat)
    raw=mne.io.read_raw_eeglab(str(path),preload=False,verbose=False)
    frame=aux['frame_'+scan]
    d={'scan':scan,'EEG_source':str(path),'srate':float(e['srate']),
       'set_reference_field':str(e.get('ref')),'SET_history':str(e.get('history')),
       'channels':[x['labels'] for x in e['chanlocs']],
       'channel_coordinates':[{'label':x['labels'],**{k:float(x[k]) for k in ['X','Y','Z','theta','radius'] if np.size(x.get(k,[]))==1}} for x in e['chanlocs']],
       'first_retained_frame':int(frame[0]),'last_retained_frame':int(frame[-1]),
       'cache_labels':aux['labels'].astype(str).tolist(),
       'cache_sha256':digest(VU_AUX),'MNE_custom_ref_applied':str(raw.info.get('custom_ref_applied')),
       'note':'Common23 feature selection retains original VU recording reference. NATVIEW average over its retained scalp montage is not harmonized by dropping channels.'}
    save_json(OUT/'VU_reference_audit.json',d)
    print(d['scan'],'reference',d['set_reference_field'],'sampling',d['srate'],flush=True)


if __name__=='__main__':main()
