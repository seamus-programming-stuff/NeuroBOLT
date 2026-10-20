#!/usr/bin/env python3
"""Report-only export of the poster panels specified before any outcomes.

Added after fitting began; it changes no fitted model, score, CI, or contrast.
Frozen analysis source hashes are checked before adding reporting metadata.
"""
import argparse
import csv
import json
from pathlib import Path

from thesis_data import digest,save_json

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out
s=json.loads((out/'summary.json').read_text());pr=json.loads((out/'protocol.json').read_text())
v=json.loads((out/'verification.json').read_text());assert s['complete'] and v['passed']
source_root=Path(__file__).parent
checks={name:digest(source_root/name)==sha for name,sha in pr['source_sha256'].items()}
assert all(checks.values()),checks
chosen=pr['poster_primary_prespecified'];arms={('ridge','eeg'):'Ridge EEG',('ridge','phys'):'Ridge ECG timing',
                                             ('ridge','combined'):'Ridge EEG + ECG timing',('mlp','eeg'):'MLP EEG'}
primary=[r for r in s['conditions'] if all(r[k]==chosen[k] for k in ['train_state','eval_condition','training_people','duration_seconds','target']) and (r['model'],r['input']) in arms]
learning=[r for r in s['conditions'] if r['model']=='ridge' and r['input']=='eeg' and r['train_state']=='EC' and r['eval_condition']=='EC' and r['target']=='regional64']
assert len(primary)==4 and len(learning)==4
def poster_row(r):
    return {'model':arms[(r['model'],r['input'])],'condition':'EC train / EC test','target':'regional64','metric':'temporal_r',
            'mean':r['r_mean'],'ci_low':r['r_mean_ci95'][0],'ci_high':r['r_mean_ci95'][1],'n_people':r['n_people'],
            'train_people':r['training_people'],'target_seconds_per_person':r['duration_seconds'],
            'predictive_R2':r['predictive_R2'],'validation_calibrated_R2':r['validation_calibrated_R2'],
            'dataset':'ds006040','scope':'previously inspected development dataset','estimator':r['model'],'input':r['input']}
for filename,records in [('poster_scores.csv',primary),('poster_learning.csv',learning)]:
    rows=[poster_row(r) for r in records]
    with open(out/filename,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
s['poster_primary']=primary;s['poster_learning']=learning
s['poster_exports']={'scores_csv':'reports/thesis_exploration/data/poster_scores.csv',
                     'learning_csv':'reports/thesis_exploration/data/poster_learning.csv'}
s['physiology_scope']='Only this fixed sparse unannotated causal ECG RR detector plus availability indicators was tested; this does not assess all useful physiology. Median valid-sample fraction 0.3918; no independent beat annotations, respiration, CO2 or arousal labels.'
s['frozen_source_checks']=checks;s['packaging_source_sha256']=digest(__file__)
s['reporting_enrichment']='After completed fits: labels, sensor limitation and exact prespecified poster subsets added; scores, CIs, contrasts and frozen analysis sources unchanged.'
save_json(out/'summary.json',s)
save_json(out/'package_verification.json',{'passed':True,'frozen_source_checks':checks,'poster_primary_rows':4,
          'poster_learning_rows':4,'source_sha256':digest(__file__),'protocol_sha256':digest(out/'protocol.json')})
print('PACKAGED: four prespecified primary rows and four learning rows; all frozen source hashes match.')
