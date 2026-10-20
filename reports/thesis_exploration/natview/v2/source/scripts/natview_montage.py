#!/usr/bin/env python3
"""Read channel-identity metadata only; no reserved EEG or BOLD outcomes."""
import pandas as pd
from natview_data import COMMON,OUT,paths
from natview_stage import digest,save_json


rows=[]
for sub in ['sub-04','sub-05','sub-06','sub-08','sub-10','sub-11','sub-12','sub-13']:
    stem,pre,raw,func=paths(sub);path=pre/f'eeg/{stem}_channels.tsv'
    tab=pd.read_csv(path,sep='\t');names=tab['name'].str.upper().tolist()
    rows.append({'subject':sub,'n_channels':len(names),'missing_common23':[c for c in COMMON if c not in names],
                 'metadata_sha256':digest(path),'no_outcomes_read':True})
save_json(OUT/'reserved_montage_metadata_audit.json',rows)
print(rows,flush=True)
