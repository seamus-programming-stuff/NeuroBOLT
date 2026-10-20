#!/usr/bin/env python3
"""Payload inspection of the development pilot; compute-node only."""
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from natview_stage import save_json


def safe(v):
    if isinstance(v, dict):
        return {k: safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if isinstance(v, np.ndarray):
        return safe(v.tolist()) if v.size < 10000 else {'shape': list(v.shape), 'dtype': str(v.dtype)}
    if isinstance(v, np.generic):
        return safe(v.item())
    if isinstance(v, float) and not np.isfinite(v):
        return None
    return v


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Use SLURM'
    root = Path('/scratch/hz18/stay0060/NeuroBOLT/data/natview')
    stem = 'sub-01_ses-01_task-rest'
    d = root/'preproc_data/sub-01/ses-01/eeg'
    mat = loadmat(d/(stem+'_eeg.set'), simplify_cells=True)
    e = mat.get('EEG', mat)
    print('FIELDS', e.keys(), flush=True)
    events = e['event']; ue = e.get('urevent', [])
    result = {k: safe(e.get(k)) for k in ['srate','nbchan','pnts','xmin','xmax','ref','times','etc','history']}
    result.update(events=safe(events), urevents=safe(ue), channels=safe(e['chanlocs']),
                  event_counts=dict(Counter(str(x['type']) for x in events)),
                  urevent_counts=dict(Counter(str(x['type']) for x in ue)),
                  data_summary={'shape':list(e['data'].shape),'min':float(e['data'].min()),
                                'max':float(e['data'].max()),'std':float(e['data'].std())})
    print(json.dumps({k:v for k,v in result.items() if k not in ['events','urevents','channels','etc','history']},indent=2), flush=True)
    print('R128', [x for x in events if str(x['type']).strip() == 'R128'][:5], flush=True)
    print('UREVENT', ue[:5], flush=True)
    print('BOUNDARIES', [x for x in events if str(x['type']).strip() == 'boundary'][:5], flush=True)
    print('ETC', safe(e.get('etc')), flush=True)
    for branch, typ in [('preproc_data','eyetracking'),('raw_data','trigger'),('raw_data','respiratory')]:
        dd=root/branch/'sub-01/ses-01/eeg'
        meta=json.loads((dd/(stem+f'_recording-{typ}_physio.json')).read_text())
        table=pd.read_csv(dd/(stem+f'_recording-{typ}_physio.tsv.gz'),sep='\t',header=None,names=meta['Columns'])
        print(typ,meta, table.shape,table.head(3).to_dict('list'),table.tail(3).to_dict('list'),flush=True)
        result[typ]={'metadata':meta,'shape':list(table.shape),'head':safe(table.head(3).to_dict('list')),
                     'tail':safe(table.tail(3).to_dict('list')),
                     'finite_fraction':{c:float(np.isfinite(pd.to_numeric(table[c],errors='coerce')).mean()) for c in table}}
        if typ in ['eyetracking','trigger']:
            col='fMRI_Volume_Trigger' if typ=='eyetracking' else 'trigger'
            vals=pd.to_numeric(table[col],errors='coerce').to_numpy()
            hi=vals > (np.nanmin(vals)+np.nanmax(vals))/2
            idx=np.flatnonzero(hi & ~np.r_[False,hi[:-1]])
            timecol=meta['Columns'][0]
            pulse=pd.to_numeric(table[timecol],errors='coerce').to_numpy()[idx]
            result[typ]['pulses']=safe(pulse)
            print('PULSES',typ,len(pulse),pulse[:10],pulse[-10:],np.unique(np.round(np.diff(pulse),4),return_counts=True),flush=True)
    save_json('reports/thesis_exploration/natview/pilot_payload_inspection.json',safe(result))


if __name__=='__main__':
    main()
